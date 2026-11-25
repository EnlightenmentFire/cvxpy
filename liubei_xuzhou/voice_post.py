# -*- coding: utf-8 -*-
"""旁白后期：每段去首尾静音、句内停顿压到 ≤0.35 s、rubberband R3 变速（保共振峰）、50 Hz 高通、
统一到 -18 dBFS RMS；同一句的各段之间留 0.22 s，拼成整句 wav（48 kHz 单声道）。
输出 /tmp/claude-0/work/tts/lines/<id>.wav 与 lines.json（每句时长）。
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import L

RAW = "/tmp/claude-0/work/tts/raw"
OUT = "/tmp/claude-0/work/tts/lines"
SR = 48000
TEMPO = {"n": float(os.environ.get("TEMPO_N", 1.18)), "q": float(os.environ.get("TEMPO_Q", 1.04))}
MAX_PAUSE = 0.35
SEG_GAP = 0.22
TARGET_RMS_DB = -18.0


def frame_db(x, win=0.02):
    n = int(SR * win)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    thr = max(db.max() - 40, -58)
    voiced = db > thr
    if not voiced.any():
        return x
    i0 = max(0, int(np.argmax(voiced)) - 2)
    i1 = min(len(voiced), len(voiced) - int(np.argmax(voiced[::-1])) + 3)
    out = []
    maxf = int(MAX_PAUSE / 0.02)
    k = i0
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]:
                j += 1
            L_ = j - k
            keep = min(L_, maxf)
            a = k + (L_ - keep) // 2
            out.append(x[a * n:(a + keep) * n])
            k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def load_seg(path):
    x, sr = sf.read(path)
    x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return x


def process_line(d):
    segs = sorted(glob.glob(f"{RAW}/{d['id']}_*.wav"), key=lambda p: int(p.rsplit("_", 1)[1][:-4]))
    if not segs:
        return None
    k = "q" if d["k"] == "q" else "n"
    parts = []
    for p in segs:
        x = trim_and_cap(load_seg(p))
        parts.append(x)
        parts.append(np.zeros(int(SEG_GAP / TEMPO[k] * SR), np.float32))
    x = np.concatenate(parts[:-1])
    x = tempo(x, TEMPO[k])
    sos = butter(4, 50, "highpass", fs=SR, output="sos")
    x = sosfiltfilt(sos, x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    rms = np.sqrt((fr ** 2).mean())
    x = x * (10 ** (TARGET_RMS_DB / 20) / (rms + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    nh = len(re.findall(r"[一-鿿]", d["t"]))
    return dict(id=d["id"], dur=len(x) / SR, chars=nh, cps=nh / (len(x) / SR))


if __name__ == "__main__":
    want = set(sys.argv[1:])
    res = {}
    if os.path.exists(f"{OUT}/lines.json"):
        res = json.load(open(f"{OUT}/lines.json"))
    for d in L:
        if want and d["id"] not in want:
            continue
        r = process_line(d)
        if r:
            res[d["id"]] = r
            print(f"{r['id']} {r['dur']:.2f}s {r['cps']:.2f} cps", flush=True)
    json.dump(res, open(f"{OUT}/lines.json", "w"), ensure_ascii=False, indent=0)
    tot = sum(v["dur"] for v in res.values()); ch = sum(v["chars"] for v in res.values())
    print(f"total {tot:.1f}s speech, {ch} chars, {ch / tot * 60:.0f} chars/min (speech only)")
