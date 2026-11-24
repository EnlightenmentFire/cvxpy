"""Post-process raw TTS lines: 50 Hz high-pass, trim, tempo (rubberband R3, formant
preserving), cap internal pauses at 0.4 s, normalise speech RMS to -18 dBFS.

Usage: voice_post.py raw_dir out_dir [ids...]
Writes out_dir/<id>.wav (48 kHz mono) and out_dir/durations.json
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly

SR = 48000
TEMPO = {"N": 1.32, "T": 1.26, "Q": 1.16}
MAX_PAUSE = 0.38
TARGET_RMS_DB = -18.0


def highpass(x, sr, fc=50.0):
    sos = butter(4, fc, btype="highpass", fs=sr, output="sos")
    return sosfiltfilt(sos, x)


def frame_rms_db(x, sr, win=0.02):
    n = int(sr * win)
    m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    rms = np.sqrt(np.mean(fr ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms), n


def trim(x, sr, rel_db=-42.0, margin=0.06):
    db, n = frame_rms_db(x, sr)
    thr = db.max() + rel_db
    idx = np.where(db > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * n - int(margin * sr))
    b = min(len(x), (idx[-1] + 1) * n + int(margin * sr))
    return x[a:b]


def cap_pauses(x, sr, max_pause=MAX_PAUSE, rel_db=-38.0):
    db, n = frame_rms_db(x, sr)
    thr = db.max() + rel_db
    silent = db < thr
    out, i, m = [], 0, len(silent)
    keep = int(max_pause * sr)
    fade = int(0.012 * sr)
    pos = 0
    while i < m:
        if silent[i]:
            j = i
            while j < m and silent[j]:
                j += 1
            a, b = i * n, j * n
            if (b - a) > keep and i > 0 and j < m:
                half = keep // 2
                seg1 = x[pos:a + half]
                seg2 = x[b - half:b]
                if out:
                    pass
                out.append(seg1)
                tail = seg2.copy()
                ramp = np.linspace(0, 1, min(fade, len(tail)))
                tail[: len(ramp)] *= ramp
                out[-1] = out[-1].copy()
                r2 = np.linspace(1, 0, min(fade, len(out[-1])))
                out[-1][-len(r2):] *= r2
                out.append(tail)
                pos = b
            i = j
        else:
            i += 1
    out.append(x[pos:])
    return np.concatenate(out)


def stretch(x, sr, tempo):
    if abs(tempo - 1.0) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/in.wav", f"{d}/out.wav"
        sf.write(a, x.astype(np.float32), sr)
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{tempo}", a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, _ = sf.read(b)
    return y


def normalise(x, sr):
    db, n = frame_rms_db(x, sr)
    thr = db.max() - 30
    act = db > thr
    if act.sum() == 0:
        return x
    fr = x[: len(db) * n].reshape(len(db), n)[act]
    rms = np.sqrt(np.mean(fr ** 2))
    g = 10 ** (TARGET_RMS_DB / 20) / rms
    y = x * g
    pk = np.max(np.abs(y))
    lim = 10 ** (-1.5 / 20)
    if pk > lim:  # soft-knee limiter on the peaks only
        y = np.where(np.abs(y) > lim * 0.8,
                     np.sign(y) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(y) - lim * 0.8) / (lim * 0.2))),
                     y)
    return y


def process(path, kind):
    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = resample_poly(x, SR, sr) if sr != SR else x
    x = highpass(x, SR)
    x = trim(x, SR)
    x = stretch(x, SR, TEMPO.get(kind, 1.2))
    x = cap_pauses(x, SR)
    x = trim(x, SR, margin=0.04)
    x = normalise(x, SR)
    return x


if __name__ == "__main__":
    raw, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    ids = sys.argv[3:] or sorted(f[:-5] for f in os.listdir(raw) if f.endswith(".json"))
    durs_path = f"{out}/durations.json"
    durs = json.load(open(durs_path)) if os.path.exists(durs_path) else {}
    for i in ids:
        meta = json.load(open(f"{raw}/{i}.json", encoding="utf-8"))
        y = process(f"{raw}/{i}.wav", meta["kind"])
        sf.write(f"{out}/{i}.wav", y.astype(np.float32), SR)
        durs[i] = len(y) / SR
        print(f"{i} {meta['kind']} raw={meta['dur']:.2f}s -> {durs[i]:.2f}s", flush=True)
    json.dump(durs, open(durs_path, "w"), indent=1)
