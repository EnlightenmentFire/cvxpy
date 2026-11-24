"""Post-process raw TTS lines: trim, cap pauses at 0.4 s, tempo (rubberband R3, formant-preserving),
50 Hz high-pass, normalize to -18 dBFS RMS (speech portions). Writes 48 kHz mono wavs.
usage: python voice_post.py <id prefixes...>
"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines

RAW = "/tmp/claude-0/work/tts/raw"
OUT = "/tmp/claude-0/work/tts/proc"
SR = 48000
TEMPO = {"n": 1.15, "q": 1.03}
MAX_PAUSE = 0.40
TARGET_RMS_DB = -18.0


def frame_db(x, sr, win=0.02):
    n = int(sr * win)
    m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 42, -60)
    voiced = db > thr
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2)
    i1 = len(voiced) - np.argmax(voiced[::-1]) + 2
    segs, cur, run = [], [], 0
    out = []
    maxf = int(MAX_PAUSE / 0.02)
    k = i0
    while k < i1:
        if not voiced[k]:
            j = k
            while j < i1 and not voiced[j]:
                j += 1
            L = j - k
            keep = min(L, maxf)
            # keep the middle of the pause (fade edges preserved by neighbours)
            a = k + (L - keep) // 2
            out.append(x[a * n:(a + keep) * n])
            k = j
        else:
            out.append(x[k * n:(k + 1) * n])
            k += 1
    y = np.concatenate(out) if out else x
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


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, TEMPO[d["k"]])
    sos = butter(4, 50, "highpass", fs=SR, output="sos")
    x = sosfiltfilt(sos, x).astype(np.float32)
    db, n = frame_db(x, SR)
    v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    rms = np.sqrt((fr ** 2).mean())
    x = x * (10 ** (TARGET_RMS_DB / 20) / (rms + 1e-9))
    peak = np.abs(x).max()
    if peak > 0.95:
        x = x * 0.95 / peak
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    n_ch = len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"]))
    return dict(id=d["id"], dur=len(x) / SR, cps=n_ch / (len(x) / SR))


if __name__ == "__main__":
    pre = sys.argv[1:]
    res = []
    for d in all_lines():
        if any(d["id"].startswith(p) for p in pre) and os.path.exists(f"{RAW}/{d['id']}.wav"):
            r = process(d); res.append(r)
            print(f"{r['id']} {r['dur']:.2f}s {r['cps']:.2f} cps")
