"""旁白后处理：裁头尾静音、句内停顿压到 ≤0.40 s、rubberband R3 变速（保共振峰）、50 Hz 高通、-18 dBFS RMS。48 kHz 单声道。
TEMPO 环境变量 = 全片统一变速倍数（由 timeline.py 按 255 字/分钟反算）。
"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines

W = "/tmp/claude-0/work"
RAW, OUT = f"{W}/tts/raw", f"{W}/tts/proc"
SR = 48000
MAX_PAUSE = 0.40


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    return 20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    v = db > max(db.max() - 42, -60)
    if not v.any():
        return x
    i0 = max(0, np.argmax(v) - 2); i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 2)
    out, k, maxf = [], i0, int(MAX_PAUSE / 0.02)
    while k < i1:
        if not v[k]:
            j = k
            while j < i1 and not v[j]:
                j += 1
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.01 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, sr, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d, factor):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, factor)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x, SR); v = db > db.max() - 35
    rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
    x = x * (10 ** (-18 / 20) / (rms + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    f = float(os.environ.get("TEMPO", 1.0))
    pre = sys.argv[1:] or [""]
    for d in all_lines():
        if any(d["id"].startswith(p) for p in pre) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            print(d["id"], round(process(d, f), 2))
