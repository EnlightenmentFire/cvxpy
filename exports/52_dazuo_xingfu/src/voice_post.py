"""旁白后期：去头尾静音、句内停顿压到 ≤0.4 s、统一变速（rubberband R3，保共振峰）、50 Hz 高通、
-18 dBFS RMS（语音段）。变速倍数按全片目标语速自动算：TARGET_CPM（含句间停顿）。
经文句（k=q）不加速，读得更慢更稳。
usage: python voice_post.py            -> WORK/tts/proc/*.wav, 打印语速
"""
import sys, os, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW = os.environ.get("TTS_RAW", f"{WORK}/tts/raw")
OUT = f"{WORK}/tts/proc"
SR = 48000
MAX_PAUSE = 0.40
TARGET_RMS_DB = -18.0
TARGET_CPM = float(os.environ.get("TARGET_CPM", 245))
OVERHEAD = 0.50 * 101 + 0.70 * 15 + 1.9 * 3     # 与 render.py 的 GAP/SCENE_GAP/Q_PRE+Q_POST 一致


def nchars(s):
    return len(re.sub(r"[，。？！：；、“”《》·\s]", "", s))


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 42, -60)
    voiced = db > thr
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
    f = int(0.01 * sr)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
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


def load_trim(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return trim_and_cap(x, SR)


def main():
    lines = all_lines()
    trimmed = {d["id"]: load_trim(d) for d in lines}
    n_all = sum(nchars(d["say"]) for d in lines)
    target_total = n_all / TARGET_CPM * 60
    speech_q = sum(len(trimmed[d["id"]]) / SR for d in lines if d["k"] == "q")
    speech_n = sum(len(trimmed[d["id"]]) / SR for d in lines if d["k"] != "q")
    fac = speech_n / max(1, target_total - OVERHEAD - speech_q)
    fac = float(np.clip(fac, 0.95, 1.25))
    print(f"chars {n_all}; raw speech {speech_n + speech_q:.1f}s; tempo factor {fac:.3f}")
    os.makedirs(OUT, exist_ok=True)
    sos = butter(4, 50, "highpass", fs=SR, output="sos")
    total = 0
    for d in lines:
        x = tempo(trimmed[d["id"]], SR, 1.0 if d["k"] == "q" else fac)
        x = sosfiltfilt(sos, x).astype(np.float32)
        db, n = frame_db(x, SR)
        v = db > db.max() - 35
        fr = x[:len(db) * n].reshape(len(db), n)[v]
        x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
        pk = np.abs(x).max()
        if pk > 0.95:
            x *= 0.95 / pk
        sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
        total += len(x) / SR
    print(f"processed speech {total:.1f}s; expected narration span {total + OVERHEAD:.1f}s "
          f"= {n_all / (total + OVERHEAD) * 60:.0f} chars/min")


if __name__ == "__main__":
    main()
