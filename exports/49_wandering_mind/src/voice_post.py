# -*- coding: utf-8 -*-
"""Post-process raw TTS lines: trim, cap internal pauses, tempo (rubberband, formant-preserving),
60 Hz high-pass, normalise speech RMS. Writes 48 kHz mono 24-bit wavs to WORK/tts/proc.
usage: python voice_post.py [ids...]
"""
import os, sys, json, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{WORK}/tts/raw", f"{WORK}/tts/proc"
SR = 48000
TEMPO = float(os.environ.get("TEMPO", 1.10))
MAX_PAUSE = 0.45
TARGET_RMS_DB = -18.0


def frame_db(x, win=0.02):
    n = int(SR * win)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    voiced = db > max(db.max() - 42, -60)
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2)
    i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]:
                j += 1
            L = j - k
            keep = min(L, maxf)
            a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n])
            k = j
        else:
            out.append(x[k * n:(k + 1) * n])
            k += 1
    y = np.concatenate(out)
    f = int(0.01 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={factor}:pitchq=quality:formant=preserved:transients=smooth:window=standard",
                        "-c:a", "pcm_f32le", b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, TEMPO)
    x = sosfiltfilt(butter(4, 60, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.9:
        x *= 0.9 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    ids = sys.argv[1:]
    for d in all_lines():
        if (not ids or d["id"] in ids) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            src = f"{RAW}/{d['id']}.wav"
            dst = f"{OUT}/{d['id']}.wav"
            if not ids and os.path.exists(dst) and os.path.getmtime(dst) > os.path.getmtime(src):
                continue
            print(d["id"], round(process(d), 2), flush=True)
