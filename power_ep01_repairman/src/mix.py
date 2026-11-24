"""Final soundtrack per 配乐规范 (四、混音):

  narration (processed lines on the timeline)
  + score (MusicGen layers laid out along the story arc, 3 s crossfades, 2 s fade-in, 3 s fade-out,
           a hard dropout at every machine stop, -4 dB EQ at 3 kHz, sidechain-ducked under the voice)
  + sound design (machine rhythm in the cold open, clack + half-second silence + low hum at each stop)
  -> two-pass loudnorm to -16 LUFS integrated, true peak <= -1.5 dBTP.

python mix.py OUT.wav [T_END] [--no-music] [--dry]
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

import music  # sound-design generators (clack, hum, big_clack)
from music import SR
from script_data import LINES
from timeline import build, load_durations
from tts import PROC, WORK

MG = os.path.join(WORK, "musicgen")
XF = 3.0  # crossfade between layers (规范: 2–4 s)


# loudness of each layer before the bus gain: 铺底 quiet, 推进 a little up, 高潮 fullest (规范 二)
LAYER_LUFS = {"L1_base": -24.0, "L2_drive": -22.5, "L3_peak": -20.0, "L4_release": -23.5, "L5_end": -24.5}


def layer_audio(name):
    import librosa
    import pyloudnorm as pyln
    rep = json.load(open(os.path.join(MG, "report.json")))
    a, sr = sf.read(rep[name]["chosen_full"], dtype="float32", always_2d=True)
    if sr != SR:
        a = np.stack([librosa.resample(ch, orig_sr=sr, target_sr=SR) for ch in a.T], axis=1)
    meter = pyln.Meter(SR)
    lufs = meter.integrated_loudness(a)
    a = a * (10 ** ((LAYER_LUFS[name] - lufs) / 20))
    return a.T.astype(np.float32)  # (2, n)


def score_plan(tl):
    """(layer, start, end, gain) along the story: 铺底 -> 推进 -> 高潮 -> release -> quiet -> ending."""
    L, S = tl["lines"], tl["sections"]
    title = [c for c in tl["cards"] if c["sec"] == "title"][0]
    plan = [
        ("L1_base", title["start"], S["s2"][1], 1.0),                  # 铺底: title, background, the only crack
        ("L2_drive", S["s2"][1], L["s3_14"][0], 1.0),                  # 推进: who guards the crack, the inversion
        ("L1_base", L["s3_14"][0], S["s4"][1], 0.9),                   # theory: back to a quiet bed
        ("L2_drive", S["s4"][1], S["s5"][1], 1.0),                     # why here
        ("L3_peak", S["s5"][1], L["s6_06"][0] + 1.0, 1.0),             # 高潮: the vicious circle (+ 1.8 s hold)
        ("L4_release", L["s6_06"][0] + 1.0, S["s6"][1], 1.0),          # the reversal: rules as a shield
        ("L1_base", S["s6"][1], S["s7"][1], 0.75),                     # three quiet questions
        ("L5_end", S["s7"][1], tl["total"], 1.0),                      # resolve to a single piano
    ]
    return plan


def build_score(tl, n):
    out = np.zeros((2, n), np.float32)
    cache = {}
    offsets = {}
    for (name, a, b, g) in score_plan(tl):
        if name not in cache:
            cache[name] = layer_audio(name)
            offsets[name] = 0
        src = cache[name]
        i0 = max(0, int((a - XF / 2) * SR))
        i1 = min(n, int((b + XF / 2) * SR))
        L = i1 - i0
        # read from where this layer left off last time (no restart from the top), looping with a long crossfade
        seg = np.zeros((2, L), np.float32)
        pos = offsets[name]
        k = 0
        while k < L:
            take = min(L - k, src.shape[1] - pos)
            seg[:, k:k + take] += src[:, pos:pos + take]
            k += take
            pos += take
            if pos >= src.shape[1] - 1:
                # loop: crossfade 6 s of the tail into a later point of the clip (not the very start)
                xf = int(6 * SR)
                restart = int(src.shape[1] * 0.25)
                if k > xf:
                    ramp = np.linspace(0, 1, xf, dtype=np.float32)
                    seg[:, k - xf:k] *= (1 - ramp)
                    seg[:, k - xf:k] += src[:, restart - xf:restart] * ramp if restart >= xf else 0
                pos = restart
        offsets[name] = pos
        env = np.ones(L, np.float32)
        f = int(XF * SR)
        if i0 > 0:
            env[:f] = np.linspace(0, 1, f)
        if i1 < n:
            env[-f:] = np.minimum(env[-f:], np.linspace(1, 0, f))
        out[:, i0:i1] += seg * env * g
    # 高潮: during the narration hold after s6_05 the music stands alone, lifted ~3 dB
    L = tl["lines"]
    h0, h1 = L["s6_05"][1], L["s6_06"][0]
    a, b = int((h0 - 1.0) * SR), int((h1 + 1.5) * SR)
    if 0 < a < b <= n:
        x = np.linspace(0, 1, b - a)
        bump = 1 + 0.41 * np.sin(np.pi * x) ** 2
        out[:, a:b] *= bump
    # 规范: fade in 2 s at the start of the music, fade out 3 s at the very end
    title = [c for c in tl["cards"] if c["sec"] == "title"][0]
    s0 = int(title["start"] * SR)
    out[:, :s0] = 0
    fi = int(2 * SR)
    out[:, s0:s0 + fi] *= np.linspace(0, 1, fi)
    fo = int(3 * SR)
    out[:, n - fo:] *= np.linspace(1, 0, fo)
    # the machine-stop sound mark: music drops out dead, comes back slowly after the hum
    for (t, k, p) in tl["events"]:
        if k == "stop":
            a = int((t - 0.03) * SR)
            b = int((t + 0.6) * SR)
            rec = int(2.0 * SR)
            if 0 < a < n:
                out[:, a:min(n, b)] = 0
                if b + rec < n:
                    out[:, b:b + rec] *= np.linspace(0, 1, rec) ** 2
    return out


def sound_design(tl, n):
    """Diegetic machine rhythm in the cold open; clack + silence + hum at every stop."""
    sfx = np.zeros(n, np.float32)
    stops = [t for (t, k, p) in tl["events"] if k == "stop"]
    cold_stop = stops[0]
    t, k = 0.0, 0
    while t < cold_stop - 0.05:
        acc = 1.0 if k % 4 == 0 else (0.7 if k % 2 == 0 else 0.45)
        music.add(sfx, music.clack(acc), t, 0.5 * min(1.0, t / 0.8 + 0.2))
        if k % 4 == 0:
            music.add(sfx, music.thunk(1.0), t, 0.5)
        t += 60.0 / 104 / 2
        k += 1
    music.add(sfx, music._bandnoise(int(cold_stop * SR), 300, 2500) * 0.04, 0.0)
    for st in stops:
        music.add(sfx, music.big_clack(), st - 0.02, 0.9)
        music.add(sfx, music.hum(6.0 if st == cold_stop else 4.5), st + 0.5, 1.0)
    music.add(sfx, music.clack(1.0), tl["end_main"] + 0.6, 0.6)
    return sfx


def narration_track(tl, n):
    import librosa
    v = np.zeros(n, np.float32)
    for ln in LINES:
        if not ln["tts"] or ln["id"] not in tl["lines"]:
            continue
        p = os.path.join(PROC, f"{ln['id']}.wav")
        if not os.path.exists(p):
            continue
        y, sr = sf.read(p, dtype="float32")
        if sr != SR:
            y = librosa.resample(y, orig_sr=sr, target_sr=SR)
        music.add(v, y, tl["lines"][ln["id"]][0])
    return v


def ffmpeg(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def loudnorm_two_pass(inp, out, I=-16.0, TP=-1.5, LRA=11.0):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", inp, "-af",
                        f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    js = json.loads(txt[txt.rindex("{"): txt.rindex("}") + 1])
    flt = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
           f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
           f"linear=true:print_format=summary")
    ffmpeg(["-i", inp, "-af", flt, "-ar", str(SR), out])
    return js


def make_mix(out_path, t_end=None, with_music=True, music_gain=0.5):
    durs = load_durations(os.path.join(WORK, "tts/durations.json"))
    tl = build(durs)
    total = t_end or tl["total"]
    n = int(total * SR)
    tmp = tempfile.mkdtemp(prefix="mix_", dir=WORK)
    voice = narration_track(tl, n)
    sfx = sound_design(tl, n)
    vpath, spath = os.path.join(tmp, "voice.wav"), os.path.join(tmp, "sfx.wav")
    sf.write(vpath, np.stack([voice, voice], 1), SR)
    sf.write(spath, np.stack([sfx, sfx], 1), SR)
    pre = os.path.join(tmp, "premix.wav")
    if with_music:
        mus = build_score(tl, int(tl["total"] * SR))[:, :n]
        mpath = os.path.join(tmp, "music.wav")
        sf.write(mpath, mus.T, SR)
        # 规范 四: music EQ -4 dB @ 3 kHz, sidechain ducking by the narration, amix without normalisation
        fc = (f"[0:a]asplit=2[v][sc];"
              f"[1:a]volume={music_gain},equalizer=f=3000:t=q:w=1:g=-4[m];"
              f"[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];"
              f"[duck]asplit=2[d1][d2];"
              f"[v][d1][2:a]amix=inputs=3:duration=first:normalize=0[out]")
        ffmpeg(["-i", vpath, "-i", mpath, "-i", spath, "-filter_complex", fc, "-map", "[out]", pre,
                "-map", "[d2]", os.path.join(tmp, "ducked_music.wav")])
    else:
        ffmpeg(["-i", vpath, "-i", spath, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[out]",
                "-map", "[out]", pre])
    js = loudnorm_two_pass(pre, out_path)
    # the same linear gain applied to the stems, so the self-check compares like with like
    gain_db = float(js["target_offset"]) + (-16.0 - float(js["input_i"])) - float(js["target_offset"])
    for stem in ("voice.wav", "ducked_music.wav"):
        p = os.path.join(tmp, stem)
        if os.path.exists(p):
            ffmpeg(["-i", p, "-af", f"volume={gain_db:.2f}dB", os.path.join(tmp, "n_" + stem)])
    print(f"wrote {out_path}: measured in I={js['input_i']} TP={js['input_tp']} LRA={js['input_lra']}; stems in {tmp}")
    return tl, tmp


if __name__ == "__main__":
    out = sys.argv[1]
    t_end = None
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    if args:
        t_end = float(args[0])
    gain = 0.5
    for a in sys.argv[2:]:
        if a.startswith("--music-gain="):
            gain = float(a.split("=")[1])
    make_mix(out, t_end, with_music="--no-music" not in sys.argv, music_gain=gain)
