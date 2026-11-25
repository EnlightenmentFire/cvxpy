# -*- coding: utf-8 -*-
"""Post-process raw TTS lines: resample 48k, trim head/tail silence, cap inner pauses at 0.38 s,
tempo via ffmpeg rubberband (formant preserving), 60 Hz high-pass, normalize speech RMS to -18 dBFS.
usage: python voice_post.py [tempo]   (writes /tmp/claude-0/work/tts/proc/*.wav and proc/durs.json)"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

RAW = "/tmp/claude-0/work/tts/raw"
OUT = "/tmp/claude-0/work/tts/proc"
SR = 48000
MAX_PAUSE = 0.38


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    voiced = db > max(db.max() - 40, -58)
    if not voiced.any():
        return x
    i0 = max(0, np.argmax(voiced) - 2)
    i1 = min(len(voiced), len(voiced) - np.argmax(voiced[::-1]) + 3)
    out = []; maxf = int(MAX_PAUSE / 0.02); k = i0
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
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"rubberband=tempo={factor}:formant=preserved:pitchq=quality", b], check=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d, factor):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, factor)
    x = sosfiltfilt(butter(4, 60, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x, SR)
    fr = x[:len(db) * n].reshape(len(db), n)[db > db.max() - 35]
    x = x * (10 ** (-18 / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95:
        x *= 0.95 / pk
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    factor = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    os.makedirs(OUT, exist_ok=True)
    durs = {}
    for d in all_lines():
        if os.path.exists(f"{RAW}/{d['id']}.wav"):
            durs[d["id"]] = process(d, factor)
    json.dump(dict(tempo=factor, durs=durs), open(f"{OUT}/durs.json", "w"), indent=0)
    n = sum(len(re.sub(r"[，。？！：；、“”《》\s]", "", d["text"])) for d in all_lines() if d["id"] in durs)
    T = sum(durs.values())
    print(f"{len(durs)} lines, speech {T:.1f}s, {n/T*60:.0f} chars/min speech-only, {n/(T+0.5*len(durs))*60:.0f} incl 0.5s gaps")
