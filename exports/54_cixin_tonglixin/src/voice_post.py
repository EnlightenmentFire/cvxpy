# -*- coding: utf-8 -*-
"""旁白后处理：裁头尾静音、句内停顿压到 ≤0.4 s、全片统一变速（rubberband，保共振峰）、
50 Hz 高通、每句 -18 dBFS RMS（语音部分）。输出 48 kHz 单声道。
python voice_post.py [--tempo X]   # 缺省按目标语速自动求全片统一倍率
"""
import sys, os, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WK = "/tmp/claude-0/work"
RAW, OUT = f"{WK}/tts/raw", f"{WK}/tts/proc"
SR = 48000
MAX_PAUSE = 0.40
TARGET_CPS = 4.75      # 语音段字速；加句间停顿后整体约 255 字/分
TEMPO_MIN, TEMPO_MAX = 1.0, 1.15


def nchar(s):
    return len(re.sub(r"[，。？！：；、“”《》·\s]", "", s))


def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    thr = max(db.max() - 40, -58)
    v = db > thr
    if not v.any(): return x
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
    y = np.concatenate(out)
    f = int(0.01 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3: return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"rubberband=tempo={factor}:formant=preserved:pitchq=quality",
                        "-ar", str(SR), b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def load_trim(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return trim_and_cap(x)


def main():
    lines = [d for d in all_lines() if os.path.exists(f"{RAW}/{d['id']}.wav")]
    trimmed = {d["id"]: load_trim(d) for d in lines}
    if "--tempo" in sys.argv:
        fac = float(sys.argv[sys.argv.index("--tempo") + 1])
    else:
        c = sum(nchar(d["say"]) for d in lines); s = sum(len(trimmed[d["id"]]) / SR for d in lines)
        fac = float(np.clip(TARGET_CPS / (c / s), TEMPO_MIN, TEMPO_MAX))
        print(f"trimmed speech {c} chars / {s:.1f}s = {c / s:.2f} cps -> tempo {fac:.3f}")
    os.makedirs(OUT, exist_ok=True)
    sos = butter(4, 50, "highpass", fs=SR, output="sos")
    tot = 0
    for d in lines:
        x = tempo(trimmed[d["id"]], fac)
        x = sosfiltfilt(sos, x).astype(np.float32)
        db, n = frame_db(x); v = db > db.max() - 35
        fr = x[:len(db) * n].reshape(len(db), n)[v]
        x = x * (10 ** (-18 / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
        pk = np.abs(x).max()
        if pk > 0.95: x *= 0.95 / pk
        sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
        tot += len(x) / SR
    json.dump(dict(tempo=fac), open(f"{OUT}/_tempo.json", "w"))
    print(len(lines), "lines, speech", round(tot, 1), "s")


if __name__ == "__main__":
    main()
