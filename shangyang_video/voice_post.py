"""旁白后处理：去头尾静音、句内停顿压到 ≤0.4 s、rubberband R3 变速（保共振峰）、50 Hz 高通、统一响度。
整体语速按 VOICE_SPEC 约 255 字/分钟（含句间停顿）自动求 TEMPO。
python voice_post.py            -> $WORK/tts/proc/*.wav + $WORK/timeline.json + narration.wav/srt
"""
import os, sys, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, OUT = f"{WK}/tts/raw", f"{WK}/tts/proc"
SR = 48000
MAX_PAUSE = 0.40
TARGET_CPM = 255.0
TARGET_RMS_DB = -18.0


def nchar(s):
    return len(re.sub(r"[，。？！：；、“”《》\s·「」]", "", s))


def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
    voiced = db > max(db.max() - 42, -60)
    i0 = max(0, int(np.argmax(voiced)) - 2)
    i1 = min(len(voiced), len(voiced) - int(np.argmax(voiced[::-1])) + 3)
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
    f = int(0.01 * SR)
    y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    return y


def tempo(x, factor):
    if abs(factor - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, x, SR, subtype="FLOAT")
        subprocess.run(["rubberband", "-3", "-F", "-T", f"{factor}", a, b], check=True, capture_output=True)
        y, _ = sf.read(b)
    return y.astype(np.float32)


def load_trim(d):
    x, sr = sf.read(f"{RAW}/{d['id']}.wav")
    x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR); x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return trim_and_cap(x)


def finish(x):
    x = sosfiltfilt(butter(4, 50, "highpass", fs=SR, output="sos"), x).astype(np.float32)
    db, n = frame_db(x)
    v = db > db.max() - 35
    fr = x[: len(db) * n].reshape(len(db), n)[v]
    x = x * (10 ** (TARGET_RMS_DB / 20) / (np.sqrt((fr ** 2).mean()) + 1e-9))
    pk = np.abs(x).max()
    return x * (0.95 / pk) if pk > 0.95 else x


def main():
    lines = all_lines()
    trimmed = {d["id"]: load_trim(d) for d in lines}
    raw_speech = sum(len(v) / SR for v in trimmed.values())
    gaps = sum(d["gap"] for d in lines)
    chars = sum(nchar(d["say"]) for d in lines)
    target_total = chars / TARGET_CPM * 60
    T = float(os.environ.get("TEMPO", raw_speech / max(1.0, target_total - gaps)))
    T = min(max(T, 0.95), 1.25)
    print(f"raw speech {raw_speech:.1f}s gaps {gaps:.1f}s chars {chars} -> tempo {T:.3f}")
    os.makedirs(OUT, exist_ok=True)
    tl, t, segs = {}, 0.35, []
    for d in lines:
        y = finish(tempo(trimmed[d["id"]], T))
        sf.write(f"{OUT}/{d['id']}.wav", y, SR, subtype="PCM_24")
        tl[d["id"]] = dict(start=round(t, 3), dur=round(len(y) / SR, 3))
        segs.append((t, y)); t += len(y) / SR + d["gap"]
    json.dump(tl, open(f"{WK}/timeline.json", "w"), ensure_ascii=False, indent=0)
    total = t + 3.0
    buf = np.zeros(int(total * SR), np.float32)
    for s, y in segs:
        i = int(s * SR); buf[i:i + len(y)] += y
    sf.write(f"{WK}/narration_raw.wav", buf, SR, subtype="PCM_24")
    sp = sum(len(y) / SR for _, y in segs)
    print(f"total {total:.1f}s = {total/60:.2f} min; {chars / (t - 0.35) * 60:.0f} cpm incl. pauses; speech {sp:.1f}s")


if __name__ == "__main__":
    main()
