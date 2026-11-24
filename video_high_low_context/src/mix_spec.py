# -*- coding: utf-8 -*-
"""Final mix per 配乐规范.md §4, using the reference ffmpeg chain:

  [voice] asplit -> [v] + [sc]
  [music] volume=0.5, equalizer f=3000 q w=1 g=-4, afade in 2 s -> [m]
  [m][sc] sidechaincompress threshold=0.02 ratio=10 attack=15 release=500 -> [duck]
  [v][duck][sfx] amix normalize=0 -> loudnorm I=-16 TP=-1.5 LRA=11 (two-pass, linear)

usage: python mix_spec.py clips_dir durations.json music.wav out.wav [t_end] [--no-music]
Writes out.wav plus stems voice.wav / sfx.wav next to it.
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402
import mix  # noqa: E402  (SFX generators)

SR = 48000


def stems(clips_dir, dur_path, t_end=None):
    tl, _ = render.make(dur_path)
    total = tl["total"] if t_end is None else t_end
    n = int(total * SR)
    voice = np.zeros(n, np.float32)
    for c in tl["clips"]:
        p = os.path.join(clips_dir, c["cid"] + ".wav")
        if not os.path.exists(p) or c["t"] >= total:
            continue
        a, sr = sf.read(p, dtype="float32")
        i = int(c["t"] * SR)
        j = min(n, i + len(a))
        voice[i:j] += a[: j - i]
    sL = np.zeros(n, np.float32)
    sR = np.zeros(n, np.float32)
    lib = {"pop": (mix.sfx_pop(), -24), "ding": (mix.sfx_ding(), -21), "type": (mix.sfx_type(), -28),
           "whoosh": (mix.sfx_whoosh(), -26), "flip": (mix.sfx_flip(), -24), "thud": (mix.sfx_thud(), -20)}

    def put(name, t, pan=0.0):
        sig, lvl = lib[name]
        i = int(max(0, t) * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        s = sig[: j - i] / (np.abs(sig).max() + 1e-9) * mix.db(lvl)
        sL[i:j] += s * math.cos((pan + 1) * math.pi / 4)
        sR[i:j] += s * math.sin((pan + 1) * math.pi / 4)

    for (t, name) in tl["sfx"]:
        if name in lib:
            put(name, t)
    for seg in tl["segs"]:
        tr = seg["trig"]
        if "calendar" in tr:
            for k in range(3):
                put("flip", tr["calendar"] + k * 1.25, 0.4)
        for (st, sname) in seg["scenes"]:
            if sname == "contract":
                put("thud", st + 1.45)
            if sname in ("meeting_us", "meeting_cn"):
                end = min([x for x, _ in seg["scenes"] if x > st] + [seg["t1"]])
                rt = mix.room_tone(end - st) * mix.db(+2)
                i = int(st * SR)
                j = min(n, i + len(rt))
                sL[i:j] += rt[: j - i]
                sR[i:j] += rt[: j - i] * 0.9
    return tl, total, voice, np.stack([sL, sR], 1)


def ff(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


GRAPH = ("[0:a]asplit=2[v][sc];"
         "[1:a]volume=0.5,equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2[m];"
         "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];"
         "[v][duck][2:a]amix=inputs=3:duration=first:normalize=0")
GRAPH_NOMUSIC = "[0:a][2:a]amix=inputs=2:duration=first:normalize=0"


GAP_TARGET = 17.5


def run(clips_dir, dur_path, music_path, out, t_end=None, no_music=False):
    d = os.path.dirname(os.path.abspath(out))
    tl, total, voice, sfx = stems(clips_dir, dur_path, t_end)
    vp, sp = os.path.join(d, "voice.wav"), os.path.join(d, "sfx.wav")
    sf.write(vp, np.stack([voice, voice], 1), SR, subtype="FLOAT")
    sf.write(sp, sfx, SR, subtype="FLOAT")
    if no_music:
        # silent music input keeps the graph shape identical
        mp = os.path.join(d, "silence.wav")
        sf.write(mp, np.zeros((len(voice), 2), np.float32), SR, subtype="FLOAT")
    else:
        mp = music_path
    if not no_music:
        # calibrate: music under speech should sit GAP_TARGET dB below the voice (spec: 15-18 dB)
        g0 = measure_gap(None, vp, mp, sp, t_end, no_print=True)
        m, _ = sf.read(mp, dtype="float32")
        m = m * (10 ** ((g0 - GAP_TARGET) / 20))
        pk = np.abs(m).max()
        if pk > 0.89:
            m = np.tanh(m / 0.89) * 0.89
        mp = os.path.join(d, "music_cal.wav")
        sf.write(mp, m.astype(np.float32), SR, subtype="FLOAT")
        print(f"calibration: gap {g0:.1f} dB -> scaled music by {g0 - GAP_TARGET:+.1f} dB")
    graph = GRAPH_NOMUSIC if no_music else GRAPH
    graph += ",alimiter=limit=0.7:attack=5:release=60:level=false"
    ins = ["-i", vp, "-i", mp, "-i", sp]
    if t_end is not None:
        ins = ["-t", str(t_end), "-i", vp, "-t", str(t_end), "-i", mp, "-t", str(t_end), "-i", sp]
    # pass 1: measure
    err = ff(ins + ["-filter_complex", graph + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S).group(0))
    ln = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}:linear=true:print_format=json").format(**js)
    err2 = ff(ins + ["-filter_complex", graph + "," + ln + ",aresample=48000", "-c:a", "pcm_s16le", out])
    js2 = json.loads(re.search(r"\{[^{}]*\"output_i\"[^{}]*\}", err2, re.S).group(0))
    print("loudnorm pass1:", {k: js[k] for k in ("input_i", "input_tp", "input_lra")})
    print("loudnorm out  :", {k: js2[k] for k in ("output_i", "output_tp", "output_lra", "normalization_type")})
    return tl, vp, sp, mp


def measure_gap(out_mix, voice_path, music_path, sfx_path, t_end=None, no_print=False):
    """Re-run the music branch alone (ducked by voice) and compare against the voice level."""
    d = os.path.dirname(os.path.abspath(voice_path))
    duck = os.path.join(d, "duck_only.wav")
    ins = ["-i", voice_path, "-i", music_path]
    if t_end is not None:
        ins = ["-t", str(t_end), "-i", voice_path, "-t", str(t_end), "-i", music_path]
    ff(ins + ["-filter_complex", "[0:a]asplit=2[v][sc];[v]anullsink;[1:a]volume=0.5,equalizer=f=3000:t=q:w=1:g=-4,"
              "afade=t=in:d=2[m];[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500",
              "-c:a", "pcm_f32le", duck])
    v, _ = sf.read(voice_path, dtype="float32")
    m, _ = sf.read(duck, dtype="float32")
    v, m = v.mean(1), m.mean(1)
    n = min(len(v), len(m))
    w = int(0.1 * SR)
    k = n // w
    vr = np.sqrt((v[: k * w].reshape(k, w) ** 2).mean(1) + 1e-12)
    mr = np.sqrt((m[: k * w].reshape(k, w) ** 2).mean(1) + 1e-12)
    vdb, mdb = 20 * np.log10(vr), 20 * np.log10(mr)
    sp = vdb > -32
    gap = 10 * np.log10((vr[sp] ** 2).mean()) - 10 * np.log10((mr[sp] ** 2).mean())
    # long pauses (>= 1 s of no speech): where music comes up on its own
    quiet = ~sp
    runs, cur = [], 0
    for q in quiet:
        cur = cur + 1 if q else 0
        runs.append(cur)
    long_q = np.array(runs) >= 10
    up = 10 * np.log10((mr[long_q] ** 2).mean()) if long_q.any() else float("nan")
    if not no_print:
        print(f"voice under speech {10 * np.log10((vr[sp] ** 2).mean()):.1f} dB | music under speech "
              f"{10 * np.log10((mr[sp] ** 2).mean()):.1f} dB | gap {gap:.1f} dB | music in long pauses {up:.1f} dB")
        # pumping inside continuous speech: spread of music level across speech windows
        print(f"music level spread under speech (std of 100 ms windows): {np.std(mdb[sp]):.1f} dB")
    os.remove(duck)
    return gap


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_music = "--no-music" in sys.argv
    clips_dir, dur_path, music_path, out = args[:4]
    t_end = float(args[4]) if len(args) > 4 else None
    tl, vp, sp, mp = run(clips_dir, dur_path, music_path, out, t_end, no_music)
    if not no_music:
        measure_gap(out, vp, mp, sp, t_end)
