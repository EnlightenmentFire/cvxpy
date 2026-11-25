"""Post-process raw TTS lines: trim, cap internal pauses, rubberband tempo (formant-preserving),
50 Hz HPF, RMS normalize. Writes 48k mono to tts/proc. usage: python voice_post.py [tempo]"""
import sys, os, json, subprocess, tempfile, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script import all_lines

W = "/tmp/claude-0/w73"
RAW, OUT = f"{W}/tts/raw", f"{W}/tts/proc"
SR = 48000
MAX_PAUSE = 0.38


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 42, -60)
    v = db > thr
    if not v.any():
        return x
    i0 = max(0, np.argmax(v) - 2); i1 = min(len(v), len(v) - np.argmax(v[::-1]) + 3)
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
    f = int(0.012 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
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


def nch(s):
    return len(re.sub(r"[，。？！：；、“”《》「」\s·]", "", s))


def process(d, fac):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav"); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    x = trim_and_cap(x, SR)
    x = tempo(x, SR, fac)
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x, SR); v = db > db.max() - 35
    rms = np.sqrt((x[:len(db) * n].reshape(len(db), n)[v] ** 2).mean())
    x = x * (10 ** (-18 / 20) / (rms + 1e-9))
    pk = np.abs(x).max()
    if pk > 0.95: x *= 0.95 / pk
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
    return len(x) / SR


if __name__ == "__main__":
    lines = [d for d in all_lines() if os.path.exists(f"{RAW}/{d['id']}.wav")]
    # choose tempo so that (chars) / (speech + 0.5 s gaps) ~= 255 /min
    target = float(sys.argv[1]) if len(sys.argv) > 1 else 255.0
    raw = []
    for d in lines:
        x, sr = sf.read(f"{RAW}/{d['id']}.wav")
        x = x.mean(1) if x.ndim > 1 else x
        raw.append(len(trim_and_cap(x.astype(np.float32), sr)) / sr)
    chars = sum(nch(d["sub"]) for d in lines)
    need = chars / (target / 60) - 0.5 * len(lines)
    fac = sum(raw) / need
    fac = min(max(fac, 1.0), 1.25)
    print(f"lines={len(lines)} chars={chars} raw={sum(raw):.1f}s tempo={fac:.3f}")
    meta = {}
    for d in lines:
        meta[d["id"]] = process(d, fac)
    json.dump(dict(tempo=fac, dur=meta), open(f"{OUT}/meta.json", "w"))
    tot = sum(meta.values()) + 0.5 * len(lines)
    print(f"speech={sum(meta.values()):.1f}s with gaps={tot:.1f}s rate={chars / tot * 60:.0f} chars/min")
