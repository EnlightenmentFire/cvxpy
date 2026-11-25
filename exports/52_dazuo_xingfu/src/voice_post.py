"""raw TTS -> trimmed, pause-capped, tempo-adjusted (rubberband, formant preserved), 50 Hz HPF, RMS-normalized 48 kHz mono.
usage: python voice_post.py [--tempo X] [ids...]"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
D = os.path.dirname(os.path.abspath(__file__))
RAW, OUT, SR = f"{D}/tts/raw", f"{D}/tts/proc", 48000
MAX_PAUSE = 0.38

def frame_db(x, n):
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)

def trim_and_cap(x):
    n = int(0.02 * SR)
    db = frame_db(x, n)
    voiced = db > max(db.max() - 40, -60)
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2); i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]:
                j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.008 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"rubberband=tempo={factor}:formant=preserved:pitchq=quality:window=standard", b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)

def process(d, factor):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, factor)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db = frame_db(x, int(0.02 * SR)); v = db > db.max() - 30
    n = int(0.02 * SR); fr = x[:len(db) * n].reshape(len(db), n)[v]
    rms = np.sqrt((fr ** 2).mean()) + 1e-9
    x = x * (10 ** (-20 / 20) / rms)
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR

if __name__ == "__main__":
    args = sys.argv[1:]
    factor = 1.0
    if "--tempo" in args:
        i = args.index("--tempo"); factor = float(args[i + 1]); del args[i:i + 2]
    for d in all_lines():
        if (not args or d["id"] in args) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            print(d["id"], round(process(d, factor), 2))
