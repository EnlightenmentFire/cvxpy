# -*- coding: utf-8 -*-
"""Assemble the narration track from per-line takes.

trim silence -> rubberband time-stretch (R3 / --fine, formants preserved) -> join with short gaps
(<= 0.22 s; 0.7 s beat before the answer line) -> 50 Hz high-pass -> RMS to about -18 dBFS
-> ASR read-back with word timestamps (anchors for the picture) -> voice_timing.json

Usage: python assemble_voice.py lines.json lines_dir out_dir
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import asrcheck as A
from voice_design import median_f0

SR = 48000
GAP = 0.20
ANSWER_GAP = 0.70
TARGET_CPS = 5.3          # narration speed after stretch (syllables / s, pinyin count)
ANSWER_SLOWER = 0.93      # answer line a touch slower / heavier
TARGET_RMS_DB = -18.0


def sh(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def trim(a, sr, thr_db=-42, pad=0.03):
    fr = int(0.01 * sr)
    n = len(a) // fr
    e = np.array([np.sqrt(np.mean(a[i * fr:(i + 1) * fr] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(e + 1e-12)
    on = np.where(db > thr_db)[0]
    if not len(on):
        return a
    s = max(0, on[0] * fr - int(pad * sr))
    t = min(len(a), (on[-1] + 1) * fr + int(pad * sr))
    return a[s:t]


def active_rms_db(a, sr):
    fr = int(0.02 * sr)
    n = len(a) // fr
    e = np.array([np.mean(a[i * fr:(i + 1) * fr] ** 2) for i in range(n)])
    thr = np.max(e) * 10 ** (-40 / 10)
    act = e[e > thr]
    return 10 * np.log10(np.mean(act) + 1e-12)


def main():
    lines = json.load(open(sys.argv[1]))
    src, out = sys.argv[2], sys.argv[3]
    os.makedirs(out + "/tmp", exist_ok=True)
    segs, info = [], []
    for L in lines:
        a, sr = sf.read(f"{src}/{L['id']}.wav", dtype="float32")
        a = trim(a, sr)
        nsyl = len(A.norm_py(L["tts"])[0])
        cps0 = nsyl / (len(a) / sr)
        tgt = TARGET_CPS * (ANSWER_SLOWER if L.get("answer") else 1.0)
        ratio = max(0.85, min(1.30, tgt / cps0))           # tempo factor (>1 = faster)
        p_in, p_out = f"{out}/tmp/{L['id']}_in.wav", f"{out}/tmp/{L['id']}_rb.wav"
        sf.write(p_in, a, sr)
        sh(["rubberband", "--fine", "--formant", "-q", "-T", f"{ratio:.4f}", p_in, p_out])
        sh(["ffmpeg", "-y", "-i", p_out, "-ar", str(SR), "-ac", "1", f"{out}/tmp/{L['id']}_48k.wav"])
        b, _ = sf.read(f"{out}/tmp/{L['id']}_48k.wav", dtype="float32")
        b = trim(b, SR, pad=0.02)
        segs.append(b)
        info.append(dict(id=L["id"], cps_raw=round(cps0, 2), tempo=round(ratio, 3), dur=round(len(b) / SR, 3),
                         cps=round(nsyl / (len(b) / SR), 2), f0=round(float(median_f0(b, SR)), 1)))
    # join
    parts, timing, t = [], [], 0.0
    for i, (L, b) in enumerate(zip(lines, segs)):
        if i > 0:
            g = ANSWER_GAP if L.get("answer") else GAP
            parts.append(np.zeros(int(g * SR), np.float32))
            t += g
        timing.append(dict(id=L["id"], start=round(t, 3), end=round(t + len(b) / SR, 3)))
        parts.append(b)
        t += len(b) / SR
    v = np.concatenate(parts)
    raw = f"{out}/tmp/voice_raw.wav"
    sf.write(raw, v, SR)
    # 50 Hz high-pass, then RMS normalise (speech-active) to -18 dBFS, peak-safe
    hp = f"{out}/tmp/voice_hp.wav"
    sh(["ffmpeg", "-y", "-i", raw, "-af", "highpass=f=50:poles=2", "-c:a", "pcm_f32le", hp])
    v, _ = sf.read(hp, dtype="float32")
    g = 10 ** ((TARGET_RMS_DB - active_rms_db(v, SR)) / 20)
    v = v * g
    pk = np.max(np.abs(v))
    if pk > 0.89:
        v = np.tanh(v / 0.89 * 1.0) * 0.89 if pk > 1.2 else v * (0.89 / pk)
    sf.write(f"{out}/voice.wav", v, SR, subtype="PCM_24")
    # ASR read-back with word timestamps
    text, words = A.transcribe(v, SR, words=True)
    ref = "".join(L["tts"] for L in lines)
    err = A.per(ref, text)
    json.dump(dict(lines=timing, info=info, asr=text, per=round(err, 4), words=[(w, round(float(a), 3), round(float(b), 3)) for w, a, b in words],
                   rms_db=round(float(active_rms_db(v, SR)), 2), duration=round(len(v) / SR, 3)),
              open(f"{out}/voice_timing.json", "w"), ensure_ascii=False, indent=1)
    for r in info:
        print(r)
    print("total", round(len(v) / SR, 2), "s  PER", round(err, 4))
    print(text)


if __name__ == "__main__":
    main()
