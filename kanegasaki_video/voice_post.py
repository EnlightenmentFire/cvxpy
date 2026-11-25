"""Raw TTS lines -> processed: trim, cap internal pauses, tempo (rubberband R3, formant-preserving), 50 Hz HPF, RMS norm.
usage: TEMPO=1.12 python voice_post.py
"""
import os, sys, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
RAW, OUT, SR = "/tmp/claude-0/work/tts/raw", "/tmp/claude-0/work/tts/proc", 48000
TEMPO = float(os.environ.get("TEMPO", "1.12")); MAX_PAUSE = 0.32; TARGET_RMS_DB = -18.0

def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n; fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n

def trim_and_cap(x):
    db, n = frame_db(x); thr = max(db.max() - 40, -58); v = db > thr
    i0 = max(0, int(np.argmax(v)) - 2); i1 = min(len(v), len(v) - int(np.argmax(v[::-1])) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not v[k]:
            j = k
            while j < i1 and not v[j]: j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out); f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y

def tempo(x, factor):
    if abs(factor - 1) < 1e-3: return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"; sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)

def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x); x = tempo(x, TEMPO)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x); v = db > db.max() - 35; fr = x[:len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max(); x = x * (0.95 / pk) if pk > 0.95 else x
    os.makedirs(OUT, exist_ok=True); sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR, len(re.sub(r"[，。？！：；、“”《》「」\s]", "", d["say"]))

if __name__ == "__main__":
    tot_t = tot_c = 0
    for d in all_lines():
        if os.path.exists(f"{RAW}/{d['id']}.wav"):
            dt, nc = process(d); tot_t += dt; tot_c += nc
    print(f"processed: {tot_c} chars in {tot_t:.1f}s speech -> {tot_c / tot_t * 60:.0f} chars/min (speech only)")
