"""Remix with the hold-sidechain (no pumping on commas), keeping the spec's other settings.

Uses the already-built voice.wav / music.wav / sfx.wav in <dir>:
  music: 3 kHz -4 dB (Q=1), fade in 2 s / out 3 s, volume, sidechain (ratio 10, attack 15 ms,
         release 500 ms, hold 350 ms, look-ahead 40 ms), threshold+volume calibrated so the
         narration sits 16.5 dB above the music while speaking
  sfx  : same EQ, lighter sidechain
  master: amix (normalize=0) -> limiter -> loudnorm I=-16 TP=-1.5 LRA=11 (two pass, linear)
usage: remix_hold.py <dir>
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from timeline import Timeline
import final_mix as F

BUILD = "/home/user/wude_build"
SR = 48000


def ff(args):
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r


def db(x):
    return 10 * np.log10(np.mean(x ** 2) + 1e-12)


def measure(tl, v, m):
    diffs = []
    for ln in tl.lines:
        a, b = int((ln["t0"] + 0.3) * SR), int((ln["t1"] - 0.2) * SR)
        if b - a >= SR:
            diffs.append(db(v[a:b]) - db(m[a:b]))
    gaps = []
    for x, y in zip(tl.lines[:-1], tl.lines[1:]):
        if y["t0"] - x["t1"] >= 1.2:
            a, b = int((x["t1"] + 0.6) * SR), int((y["t0"] - 0.1) * SR)
            gaps.append(db(m[a:b]))
    speech = float(np.median([db(v[int((l['t0'] + .3) * SR):int((l['t1'] - .2) * SR)])
                              for l in tl.lines if l['dur'] > 1.5]))
    return float(np.median(diffs)), float(np.percentile(diffs, 10)), float(np.percentile(diffs, 90)), \
        float(np.median(gaps)), speech


def jumps(tl, v, m, thr=6.0):
    hop, w = int(0.1 * SR), int(0.4 * SR)
    ev = 0
    for ln in tl.lines:
        a, b = int((ln["t0"] + 0.4) * SR), int((ln["t1"] - 0.4) * SR)
        if b - a < SR:
            continue
        lv = np.array([db(m[i:i + w]) for i in range(a, b - w, hop)])
        vv = np.array([db(v[i:i + w]) for i in range(a, b - w, hop)])
        med = np.median(lv)
        if np.any((vv > -30) & (lv - med > thr)):
            ev += 1
    return ev


def main():
    d = sys.argv[1]
    segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
    tl = Timeline(segs, json.load(open(f"{BUILD}/voice_post/durations.json")))
    end = max(0.0, tl.total - 3.0)
    ff(["-i", f"{d}/music.wav", "-af", f"equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2,afade=t=out:st={end:.3f}:d=3",
        "-c:a", "pcm_f32le", f"{d}/music_eq.wav"])
    ff(["-i", f"{d}/sfx.wav", "-af", "equalizer=f=3000:t=q:w=1:g=-4", "-c:a", "pcm_f32le", f"{d}/sfx_eq.wav"])
    v, _ = sf.read(f"{d}/voice.wav", dtype="float32")
    me, _ = sf.read(f"{d}/music_eq.wav", dtype="float32")
    se, _ = sf.read(f"{d}/sfx_eq.wav", dtype="float32")
    n = min(len(v), len(me), len(se))
    v, me, se = v[:n], me[:n], se[:n]
    vm = v.mean(1)
    mm = me.mean(1)
    best = None
    for th_db in (-34.0, -30.0, -27.0, -24.0):
        g = F.duck_gain(vm, th_db).astype(np.float32)
        d1, p10, p90, gap1, speech = measure(tl, vm, mm * g)
        vol_db = d1 - 16.5                     # make speech_diff exactly 16.5 dB
        gap = speech - (gap1 + vol_db)
        rec = dict(th_db=th_db, vol_db=vol_db, speech_diff=16.5, p10=p10 - d1 + 16.5, p90=p90 - d1 + 16.5,
                   pause_gap=gap)
        print(json.dumps({k: round(x, 2) for k, x in rec.items()}), flush=True)
        if best is None or abs(gap - 8) < abs(best[0]["pause_gap"] - 8):
            best = (rec, g)
    rec, g = best
    vol = 10 ** (rec["vol_db"] / 20)
    md = me * (vol * g)[:, None]
    jm_old = None
    if os.path.exists(f"{d}/duck.wav"):
        old, _ = sf.read(f"{d}/duck.wav", dtype="float32")
        jm_old = jumps(tl, vm, old[:n].mean(1))
    jm_new = jumps(tl, vm, md.mean(1))
    rec.update(lines_with_midline_jumps_before=jm_old, lines_with_midline_jumps_after=jm_new)
    print("chosen", json.dumps(rec), flush=True)
    gs = F.duck_gain(vm, rec["th_db"] + 8, ratio=4.0, attack_ms=10, release_ms=300, hold_ms=200).astype(np.float32)
    sd = se * gs[:, None]
    sf.write(f"{d}/duck.wav", md, SR, subtype="FLOAT")
    sf.write(f"{d}/sfx_duck.wav", sd, SR, subtype="FLOAT")
    json.dump(rec, open(f"{d}/ducking_hold.json", "w"), indent=1)
    # master: amix -> limiter -> loudnorm (two pass, linear)
    base = ["-i", f"{d}/voice.wav", "-i", f"{d}/duck.wav", "-i", f"{d}/sfx_duck.wav", "-filter_complex"]
    g1 = ("[0:a][1:a][2:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.78:attack=2:release=60:level=0,"
          "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[out]")
    r = ff(base + [g1, "-map", "[out]", "-f", "null", "-"])
    js = json.loads(re.findall(r"\{[^{}]+\}", r.stderr)[-1])
    g2 = ("[0:a][1:a][2:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.78:attack=2:release=60:level=0,"
          f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
          "linear=true:print_format=json[out]")
    r2 = ff(base + [g2, "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_f32le", f"{d}/mix.wav"])
    js2 = json.loads(re.findall(r"\{[^{}]+\}", r2.stderr)[-1])
    print("loudnorm out", js2["output_i"], "TP", js2["output_tp"], js2["normalization_type"], flush=True)


if __name__ == "__main__":
    main()
