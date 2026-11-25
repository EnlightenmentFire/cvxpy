# -*- coding: utf-8 -*-
"""TTS 原始句 → 处理后旁白：去首尾静音、句内停顿压到 ≤0.4 s、rubberband R3 变速（保共振峰）、50 Hz 高通、-18 dBFS RMS。
usage: python voice_post.py [id_prefix ...]"""
import sys, os, re, json, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines

W = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{W}/tts/raw", f"{W}/tts/proc"
SR = 48000
TEMPO = {"n": float(os.environ.get("TEMPO_N", 1.12)), "q": float(os.environ.get("TEMPO_Q", 1.02))}
MAX_PAUSE = 0.40
TARGET_RMS_DB = -18.0


def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    voiced = db > max(db.max() - 42, -60)
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2); i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]: j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3: return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, TEMPO[d["k"]])
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 35
    rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
    x = x * (10 ** (TARGET_RMS_DB / 20) / (rms + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95: x *= 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    nch = len(re.sub(r"[，。？！：；、“”《》（）·\s]", "", d["say"]))
    return d["id"], len(x) / SR, nch


if __name__ == "__main__":
    pre = sys.argv[1:]
    tot_d = tot_c = 0
    for d in all_lines():
        if (not pre or any(d["id"].startswith(p) for p in pre)) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            i, dur, c = process(d); tot_d += dur; tot_c += c
    print(f"processed: {tot_c} chars, {tot_d:.1f}s speech, {tot_c / tot_d * 60:.0f} chars/min (speech only)")
