"""raw TTS -> proc: 裁头尾静音、句内停顿压到 0.35s、rubberband R3 变速（保共振峰）、50Hz 高通、-18 dBFS RMS、48k。
usage: python voice_post.py TEMPO [ids...]"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
RAW = "/tmp/claude-0/w74/tts/raw"; OUT = "/tmp/claude-0/w74/tts/proc"; SR = 48000
MAX_PAUSE = 0.35

def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9), n

def trim_and_cap(x):
    db, n = frame_db(x); thr = max(db.max() - 42, -60); voiced = db > thr
    i0 = max(0, np.argmax(voiced) - 2); i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 2)
    out = []; maxf = int(MAX_PAUSE / 0.02); k = i0
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]: j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out); f = int(0.01 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y

def tempo(x, factor):
    if abs(factor - 1) < 1e-3: return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)

def process(d, fac):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x); x = tempo(x, fac)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x); v = db > db.max() - 35
    rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
    x = x * (10 ** (-18 / 20) / (rms + 1e-9)); pk = np.abs(x).max()
    if pk > 0.95: x *= 0.95 / pk
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR

if __name__ == "__main__":
    fac = float(sys.argv[1]); pre = sys.argv[2:]
    tot = 0
    for d in all_lines():
        if (not pre or any(d["id"].startswith(p) for p in pre)) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            tot += process(d, fac)
    print("speech total %.1fs" % tot)
