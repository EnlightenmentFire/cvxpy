# -*- coding: utf-8 -*-
"""Post-process raw TTS lines: trim lead/tail silence, cap inner pauses, tempo (rubberband, formant preserved),
50 Hz high-pass, normalise speech RMS. Writes 48 kHz mono wavs to tts/proc/.
usage: python voice_post.py [tempo_n] [tempo_q]
"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

RAW = "/tmp/claude-0/work/tts/raw"
OUT = "/tmp/claude-0/work/tts/proc"
SR = 48000
MAX_PAUSE = 0.42
TARGET_RMS_DB = -18.0


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
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
    f = int(0.012 * sr)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, sr, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-af",
                        f"rubberband=tempo={factor}:formant=preserved:pitchq=quality:window=standard", b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d, tempos):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, tempos[d["k"]])
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x, SR)
    v = db > db.max() - 35
    fr = x[:len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    tn = float(sys.argv[1]) if len(sys.argv) > 1 else 1.1
    tq = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    durs = {}
    for d in all_lines():
        if os.path.exists(f"{RAW}/{d['id']}.wav"):
            durs[d["id"]] = process(d, {"n": tn, "q": tq})
    json.dump(durs, open("/tmp/claude-0/work/tts/proc_durs.json", "w"), indent=1)
    print(len(durs), "lines", sum(durs.values()), "s")
