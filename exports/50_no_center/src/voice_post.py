"""逐句后处理：去头尾静音、句内停顿压到 ≤0.4 s、可选整体变速（rubberband，保共振峰）、50 Hz 高通、语音段 RMS 归一到 −18 dBFS；48 kHz。
usage: python voice_post.py   （处理 raw 目录下全部句子；TEMPO 环境变量，默认 1.0）"""
import os, sys, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

W = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{W}/tts/raw", f"{W}/tts/proc"
SR = 48000
TEMPO = float(os.environ.get("TEMPO", "1.0"))
MAX_PAUSE = 0.40

def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
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
            L = j - k; keep = min(L, maxf); a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n]); k = j
        else:
            out.append(x[k * n:(k + 1) * n]); k += 1
    y = np.concatenate(out)
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f * 2:] *= np.linspace(1, 0, f * 2)
    return y

def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"rubberband=tempo={factor}:formant=preserved:pitchq=quality", b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)

def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, TEMPO)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 35
    rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
    x = x * (10 ** (-18 / 20) / (rms + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95: x *= 0.95 / pk
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    nc = len(re.sub(r"[，。？！：；、「」《》“”\s]", "", d["say"]))
    return len(x) / SR, nc

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tot_d = tot_c = 0
    for d in all_lines():
        if os.path.exists(f"{RAW}/{d['id']}.wav"):
            du, nc = process(d); tot_d += du; tot_c += nc
    print(f"speech {tot_d:.1f}s, {tot_c} chars, {tot_c / tot_d * 60:.0f} chars/min of speech")
