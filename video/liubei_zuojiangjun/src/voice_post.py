# -*- coding: utf-8 -*-
"""旁白后处理：去头尾静音、句内停顿压到 ≤MAX_PAUSE、rubberband R3 保共振峰变速、50 Hz 高通、按语音段 RMS 归一。
输出 48 kHz 单声道 $WORK/tts/proc/<id>.wav，并写 $WORK/tts/proc/durs.json。
用法：python voice_post.py [id 前缀 ...]
"""
import sys, os, json, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{WORK}/tts/raw", f"{WORK}/tts/proc"
SR = 48000
TEMPO = float(os.environ.get("TEMPO", 1.18))
MAX_PAUSE = 0.32
TARGET_RMS_DB = -19.0


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 40, -58)
    v = db > thr
    if not v.any():
        return x
    i0 = max(0, np.argmax(v) - 2); i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 3)
    out = []; k = i0; maxf = int(MAX_PAUSE / 0.02)
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
    f = int(0.008 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
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


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, TEMPO)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x, SR); v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.9:
        x *= 0.9 / pk
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pre = sys.argv[1:] or [""]
    dp = f"{OUT}/durs.json"
    durs = json.load(open(dp)) if os.path.exists(dp) else {}
    for d in all_lines():
        if any(d["id"].startswith(p) for p in pre) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            durs[d["id"]] = round(process(d), 3)
    durs["_tempo"] = TEMPO
    json.dump(durs, open(dp, "w"), indent=0)
    print(len(durs) - 1, "lines", round(sum(v for k, v in durs.items() if not k.startswith("_")), 1), "s")
