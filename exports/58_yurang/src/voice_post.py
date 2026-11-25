"""配音后期：去头尾静音、句内停顿压到 ≤0.35 s、rubberband R3 变速（保共振峰）、60 Hz 高通、统一响度。
usage: python voice_post.py [--tempo X]   （默认按目标语速自动算一个全片统一的倍率）
"""
import sys, os, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines

W = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{W}/tts/raw", f"{W}/tts/proc"
SR = 48000
MAX_PAUSE = 0.35
TARGET_CPS = float(os.environ.get("TARGET_CPS", 4.55))   # 句内语速（字/秒），加上句间停顿后约 255 字/分钟


def frame_db(x, sr, win=0.02):
    n = int(sr * win); m = len(x) // n
    fr = x[:m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x, sr):
    db, n = frame_db(x, sr)
    thr = max(db.max() - 40, -60)
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
    f = int(0.008 * sr)
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


def nch(s):
    return len(re.sub(r"[^一-鿿]", "", s))


def load_trim(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    g = np.gcd(sr, SR)
    x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return trim_and_cap(x, SR)


def main():
    lines = all_lines()
    tr = {d["id"]: load_trim(d) for d in lines}
    if "--tempo" in sys.argv:
        f = float(sys.argv[sys.argv.index("--tempo") + 1])
    else:
        c = sum(nch(d["say"]) for d in lines); s = sum(len(tr[d["id"]]) for d in lines) / SR
        f = min(1.25, max(1.0, TARGET_CPS / (c / s)))
        print(f"trimmed speech {s:.1f}s, {c / s:.2f} cps -> tempo {f:.3f}")
    os.makedirs(OUT, exist_ok=True)
    sos = butter(4, 60, "highpass", fs=SR, output="sos")
    meta = {}
    for d in lines:
        k = f * (1.0 if d["k"] == "n" else 0.94)   # 原文句子略慢
        x = tempo(tr[d["id"]], SR, k)
        x = sosfiltfilt(sos, x).astype(np.float32)
        db, n = frame_db(x, SR)
        vv = db > db.max() - 35
        fr = x[:len(db) * n].reshape(len(db), n)[vv]
        x = x * (10 ** (-18 / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
        pk = np.abs(x).max()
        if pk > 0.95:
            x *= 0.95 / pk
        sf.write(f"{OUT}/{d['id']}.wav", x, SR, subtype="PCM_24")
        meta[d["id"]] = dict(dur=len(x) / SR, cps=nch(d["say"]) / (len(x) / SR))
    json.dump(dict(tempo=f, lines=meta), open(f"{OUT}/meta.json", "w"), ensure_ascii=False, indent=1)
    print("done", len(meta))


if __name__ == "__main__":
    main()
