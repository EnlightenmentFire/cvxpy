"""Post-process raw TTS lines: trim head/tail silence, cap internal pauses, optional tempo (rubberband R3,
formant-preserving), 60 Hz high-pass, speech RMS to -18 dBFS. 48 kHz mono. Writes durations.json.
usage: python voice_post.py [ids...]"""
import sys, os, json, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{WORK}/tts/raw", f"{WORK}/tts/proc"
SR = 48000
TEMPO = {"n": float(os.environ.get("TEMPO_N", 1.0)), "q": float(os.environ.get("TEMPO_Q", 1.0))}
MAX_PAUSE = 0.38


def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    thr = max(db.max() - 40, -58)
    v = db > thr
    if not v.any():
        return x
    i0 = max(0, int(np.argmax(v)) - 2)
    i1 = min(len(v), len(v) - int(np.argmax(v[::-1])) + 3)
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
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def process(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x)
    x = tempo(x, TEMPO[d["k"]])
    x = sosfiltfilt(butter(4, 60, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    vv = db > db.max() - 32
    fr = x[:len(db) * n].reshape(len(db), n)[vv]
    x = x * (10 ** (-18 / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.89: x *= 0.89 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    pre = sys.argv[1:]
    dp = f"{OUT}/durations.json"
    durs = json.load(open(dp)) if os.path.exists(dp) else {}
    for d in all_lines():
        if (not pre or any(d["id"].startswith(p) for p in pre)) and os.path.exists(f"{RAW}/{d['id']}.json"):
            durs[d["id"]] = round(process(d), 3)
    json.dump(durs, open(dp, "w"), indent=0)
    ls = [d for d in all_lines() if d["id"] in durs]
    import re
    ch = sum(len(re.sub(r"[，。？！：；、“”《》·…\s—]", "", d["t"])) for d in ls)
    sp = sum(durs[d["id"]] for d in ls); gp = sum(d["gap"] for d in ls)
    print(f"{len(ls)} lines, {ch} chars, speech {sp:.1f}s, +gaps {sp+gp:.1f}s -> {ch/(sp+gp)*60:.0f} chars/min")
