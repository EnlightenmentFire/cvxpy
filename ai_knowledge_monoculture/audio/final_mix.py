"""Final mix per the music spec (配乐规范 §四):

  voice  : narration (+ machine-voice line), sidechain key
  music  : volume -> 3 kHz cut (-4 dB, q 1) -> fade in 2 s -> sidechaincompress(thr 0.02, ratio 10,
           attack 15 ms, release 500 ms) keyed by the voice
  sfx    : not ducked
  master : amix (no normalisation) -> two-pass loudnorm I=-16 LUFS, TP=-1.5 dBTP, LRA=11 (linear)

Also reports: music level under the voice (target 15-18 dB below), loudness/true peak,
and writes the ducked-music-only stem for checks."""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "render"))
import mix as M  # noqa: E402
import plan  # noqa: E402
import timeline  # noqa: E402

SR = 48000


def build_stems(voice_dir, robot, out_dir):
    segs, total = timeline.build(voice_dir, robot, None, allow_missing=False)
    n = int((total + 0.5) * SR)
    voice = np.zeros(n, np.float32)
    for s in segs:
        for e in s.events:
            M.place(voice, M.load48(e.audio), e.start, 0.9 if e.kind == "robot" else 1.0)
    sfx = np.zeros((n, 2), np.float32)
    events = []
    for s in segs:
        fn = plan.PLANS.get(s.key)
        if fn:
            events += fn(s, {e.id: e for e in s.events})
    events += plan.transitions(segs)
    for t, arr, g, pan in events:
        lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        tmp = np.zeros(n, np.float32)
        M.place(tmp, arr.astype(np.float32), t, g)
        sfx[:, 0] += tmp * lg * 1.41
        sfx[:, 1] += tmp * rg * 1.41
    os.makedirs(out_dir, exist_ok=True)
    vp, sp = os.path.join(out_dir, "voice.wav"), os.path.join(out_dir, "sfx.wav")
    sf.write(vp, voice, SR, subtype="FLOAT")
    sf.write(sp, sfx, SR, subtype="FLOAT")
    # sidechain key: steady noise at the narration's level for the whole of each sentence, silence between
    # sentences -> the music stays put under a sentence (no 'breathing' in tiny pauses) and comes back up
    # between sentences, paragraphs and chapters.
    rng = np.random.default_rng(0)
    key = np.zeros(n, np.float32)
    for s in segs:
        for e in s.events:
            a, b = int(max(0, e.start - 0.08) * SR), int(min(total, e.end + 0.12) * SR)
            key[a:b] = rng.normal(0, 10 ** (-18 / 20), b - a)
    kp = os.path.join(out_dir, "key.wav")
    sf.write(kp, key, SR, subtype="FLOAT")
    return segs, total, vp, sp


def ff(args):
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-nostats"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


GRAPH = ("[0:a]aformat=channel_layouts=stereo[v];[3:a]aformat=channel_layouts=stereo[sc];"
         "[1:a]volume={vol},acompressor=threshold=0.1:ratio=3:attack=20:release=300:knee=4,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2[m];"
         "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];")


def mix(vp, mp, sp, out, vol=0.5, no_music=False):
    if no_music:
        g = "[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=first:normalize=0[pre]"
        inputs = ["-i", vp, "-i", sp]
    else:
        g = GRAPH.format(vol=vol) + "[v][duck][2:a]amix=inputs=3:duration=first:normalize=0[pre]"
        inputs = ["-i", vp, "-i", mp, "-i", sp, "-i", os.path.join(os.path.dirname(vp), "key.wav")]
    # pass 1: measure
    err = ff(inputs + ["-filter_complex", g + ";[pre]loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[o]",
                       "-map", "[o]", "-f", "null", "-"])
    js = json.loads(err[err.rindex("{"): err.rindex("}") + 1])
    ln = ("loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    # pass 2: apply (+ a true-peak safety limiter after the linear gain)
    ff(inputs + ["-filter_complex", g + f";[pre]{ln},aresample=48000,aresample=192000,alimiter=limit=0.79:attack=1:release=50:level=false,aresample=48000[o]",
                 "-map", "[o]", "-ar", str(SR), "-c:a", "pcm_s16le", out])
    return js


def ducked_music_stem(vp, mp, out, vol=0.5):
    g = GRAPH.format(vol=vol) + "[v]anullsink"
    kp = os.path.join(os.path.dirname(vp), "key.wav")
    ff(["-i", vp, "-i", mp, "-i", vp, "-i", kp, "-filter_complex", g, "-map", "[duck]", "-c:a", "pcm_f32le", out])


def measure(path):
    err = ff(["-i", path, "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"])
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])
    LRA = float(re.findall(r"LRA:\s+(-?[\d.]+) LU", err)[-1])
    TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
    return dict(I=I, LRA=LRA, TP=TP)


def under_voice_db(vp, duck_path, segs):
    """Median (voice RMS - ducked music RMS) over 400 ms windows where the narration is speaking,
    and the music rise in pauses (music RMS in gaps minus music RMS under speech)."""
    v, _ = sf.read(vp, dtype="float32")
    m, _ = sf.read(duck_path, dtype="float32")
    m = m.mean(axis=1) if m.ndim > 1 else m
    hop = int(0.4 * SR)
    diffs, gap_lv, sp_lv = [], [], []
    speech = np.zeros(len(v), bool)
    for s in segs:
        for e in s.events:
            speech[int(e.start * SR): int(e.end * SR)] = True
    for i in range(0, min(len(v), len(m)) - hop, hop):
        vv = v[i:i + hop]
        mm = m[i:i + hop]
        vr = 20 * np.log10(np.sqrt(np.mean(vv ** 2)) + 1e-9)
        mr = 20 * np.log10(np.sqrt(np.mean(mm ** 2)) + 1e-9)
        if speech[i:i + hop].all() and vr > -40:
            diffs.append(vr - mr)
            sp_lv.append(mr)
        elif not speech[i:i + hop].any():
            gap_lv.append(mr)
    return dict(voice_minus_music_db=round(float(np.median(diffs)), 1),
                p10=round(float(np.percentile(diffs, 10)), 1), p90=round(float(np.percentile(diffs, 90)), 1),
                music_rise_in_pauses_db=round(float(np.median(gap_lv) - np.median(sp_lv)), 1) if gap_lv else None)


if __name__ == "__main__":
    voice_dir, robot, music_path, out_dir = sys.argv[1:5]
    vol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
    segs, total, vp, sp = build_stems(voice_dir, robot, out_dir)
    print("stems ok", round(total, 2))
    ducked = os.path.join(out_dir, "music_ducked.wav")
    # pick the music pre-gain so the music sits ~16.5 dB under the voice while it speaks (spec: 15-18 dB)
    for it in range(4):
        ducked_music_stem(vp, music_path, ducked, vol)
        under = under_voice_db(vp, ducked, segs)
        print("vol", round(vol, 3), "under voice:", under, flush=True)
        err = under["voice_minus_music_db"] - 16.5
        if abs(err) <= 0.6 or it == 3:
            break          # keep the last measured volume so the report matches the mix
        vol = vol * (10 ** (err / 20))
    mix(vp, music_path, sp, os.path.join(out_dir, "mix.wav"), vol)
    m1 = measure(os.path.join(out_dir, "mix.wav"))
    print("mix:", m1)
    mix(vp, music_path, sp, os.path.join(out_dir, "mix_nomusic.wav"), vol, no_music=True)
    m2 = measure(os.path.join(out_dir, "mix_nomusic.wav"))
    print("no-music mix:", m2)
    json.dump(dict(vol=vol, under=under, mix=m1, nomusic=m2), open(os.path.join(out_dir, "mix_measure.json"), "w"),
              indent=1)
