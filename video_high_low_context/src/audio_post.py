# -*- coding: utf-8 -*-
"""Post-process raw TTS clips: trim, tempo (rubberband, formant-preserving), cap pauses at
0.4 s, 50 Hz high-pass, RMS-normalise to about -18 dBFS. Writes durations.json.

usage: python audio_post.py raw_dir out_dir clips.json [narr_tempo] [quote_tempo]
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly

SR = 48000
TARGET_RMS_DB = -18.0
MAX_PAUSE = 0.38


def frame_db(a, sr, win=0.01):
    n = int(sr * win)
    m = len(a) // n
    if m == 0:
        return np.array([-120.0]), n
    fr = a[: m * n].reshape(m, n)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms + 1e-12), n


def trim(a, sr, pre=0.03, post=0.08):
    db, n = frame_db(a, sr)
    thr = max(-48.0, db.max() - 42)
    idx = np.where(db > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] * n - int(pre * sr))
    e = min(len(a), (idx[-1] + 1) * n + int(post * sr))
    return a[s:e]


def cap_pauses(a, sr, max_pause=MAX_PAUSE):
    db, n = frame_db(a, sr)
    thr = max(-50.0, db.max() - 38)
    silent = db < thr
    out = []
    i = 0
    m = len(silent)
    keep = int(max_pause / 0.01)
    while i < m:
        j = i
        while j < m and silent[j] == silent[i]:
            j += 1
        seg = a[i * n: j * n]
        if silent[i] and (j - i) > keep and i > 0 and j < m:
            half = keep // 2
            seg = np.concatenate([a[i * n: (i + half) * n], a[(j - (keep - half)) * n: j * n]])
            # short crossfade at the joint
        out.append(seg)
        i = j
    out.append(a[m * n:])
    return np.concatenate(out)


def tempo(a, sr, ratio):
    if abs(ratio - 1.0) < 1e-3:
        return a
    with tempfile.TemporaryDirectory() as td:
        i, o = os.path.join(td, "i.wav"), os.path.join(td, "o.wav")
        sf.write(i, a, sr, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{ratio:.4f}", "-q", i, o], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        b, _ = sf.read(o, dtype="float32")
    return b


def hp(a, sr, f=50.0):
    sos = butter(4, f, btype="highpass", fs=sr, output="sos")
    return sosfiltfilt(sos, a).astype(np.float32)


def active_rms_db(a, sr):
    db, n = frame_db(a, sr, 0.02)
    act = db[db > db.max() - 30]
    if len(act) == 0:
        return -60.0
    lin = np.mean(10 ** (act / 10))
    return 10 * np.log10(lin + 1e-12)


def normalise(a, sr, target=TARGET_RMS_DB):
    g = 10 ** ((target - active_rms_db(a, sr)) / 20)
    b = a * g
    pk = np.abs(b).max()
    lim = 10 ** (-1.5 / 20)
    if pk > lim:  # gentle soft clip on rare peaks
        b = np.tanh(b / lim) * lim
    return b.astype(np.float32)


def to48k(a, sr):
    if sr == SR:
        return a
    from math import gcd
    g = gcd(sr, SR)
    return resample_poly(a, SR // g, sr // g).astype(np.float32)


def nchars(s):
    return len(re.sub(r"[^一-鿿A-Za-z぀-ヿ]", "", s))


def main():
    raw, out, clips_path = sys.argv[1], sys.argv[2], sys.argv[3]
    narr_t = float(sys.argv[4]) if len(sys.argv) > 4 else None
    quote_t = float(sys.argv[5]) if len(sys.argv) > 5 else None
    os.makedirs(out, exist_ok=True)
    clips = {c["cid"]: c for c in json.load(open(clips_path))}
    durp = os.path.join(out, "durations.json")
    durs = json.load(open(durp)) if os.path.exists(durp) else {}
    files = sorted(f for f in os.listdir(raw) if f.endswith(".wav"))
    # measure natural rate to choose tempo
    rates = []
    for f in files:
        cid = f[:-4]
        c = clips.get(cid)
        if not c or c["kind"] != "narr":
            continue
        a, sr = sf.read(os.path.join(raw, f), dtype="float32")
        a = trim(a, sr)
        rates.append(nchars(c["tts"]) / (len(a) / sr))
    med = float(np.median(rates)) if rates else 4.4
    if narr_t is None:
        narr_t = float(np.clip(5.3 / med, 1.0, 1.3))
    if quote_t is None:
        quote_t = float(np.clip(narr_t * 0.9, 1.0, 1.2))
    print(f"median raw rate {med:.2f} cps -> narration tempo {narr_t:.3f}, quote tempo {quote_t:.3f}")
    for f in files:
        cid = f[:-4]
        c = clips.get(cid)
        if not c:
            continue
        a, sr = sf.read(os.path.join(raw, f), dtype="float32")
        if a.ndim > 1:
            a = a.mean(1)
        a = to48k(a, sr)
        a = trim(a, SR)
        k = c["kind"]
        r = narr_t if k == "narr" else quote_t if k in ("quote", "jp") else 1.0
        a = tempo(a, SR, r)
        a = cap_pauses(a, SR)
        a = trim(a, SR, 0.02, 0.06)
        a = hp(a, SR)
        a = normalise(a, SR)
        sf.write(os.path.join(out, cid + ".wav"), a, SR, subtype="PCM_16")
        durs[cid] = round(len(a) / SR, 3)
    json.dump(durs, open(durp, "w"), indent=1, ensure_ascii=False)
    print("clips", len(durs))


if __name__ == "__main__":
    main()
