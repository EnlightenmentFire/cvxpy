# -*- coding: utf-8 -*-
"""旁白后期 + 对时：去头尾静音、句内长停顿压到 0.4 秒、统一变速（rubberband R3 保共振峰）到全片约 255 字/分、
60 Hz 高通、逐句响度对齐；拼接成 narration.wav（48k 单声道），输出 timeline.json / narration.srt / sentences.json / sentences.txt。"""
import os, sys, json, re, subprocess, tempfile
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, resample_poly
import pyloudnorm as pyln
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines, SCENES

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
RAW, PROC = f"{WORK}/tts/raw", f"{WORK}/tts/proc"
SR = 48000
LEAD = 0.5          # 开场：第一帧即画面 + 磬声，0.5 秒后开口
TARGET_CPM = 255.0
MAX_PAUSE = 0.40


def nchars(s):
    return len(re.sub(r"[^一-鿿0-9A-Za-z]", "", s))


def frame_db(x, win=0.02):
    n = int(SR * win); m = len(x) // n
    fr = x[: m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), n


def trim_and_cap(x):
    db, n = frame_db(x)
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
    f = int(0.008 * SR)
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


def srt_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    os.makedirs(PROC, exist_ok=True)
    L = all_lines()
    trimmed = []
    for d in L:
        x, sr = sf.read(f"{RAW}/{d['id']}.wav")
        x = x.astype(np.float32)
        if x.ndim > 1:
            x = x.mean(1)
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
        trimmed.append(trim_and_cap(x))
    speech = sum(len(x) for x in trimmed) / SR
    gaps = sum(d["gap"] for d in L)
    chars = sum(nchars(d["say"]) for d in L)
    target_total = chars / TARGET_CPM * 60
    # 引文句（slow）不变速；其余统一变速
    slow_s = sum(len(x) for x, d in zip(trimmed, L) if d.get("slow")) / SR
    norm_s = speech - slow_s
    need = target_total - gaps - slow_s
    factor = float(np.clip(norm_s / need, 1.0, 1.15))
    print(f"speech {speech:.1f}s gaps {gaps:.1f}s chars {chars} -> tempo {factor:.3f}")
    meter = pyln.Meter(SR)
    sos = butter(4, 60, "highpass", fs=SR, output="sos")
    out = []
    for x, d in zip(trimmed, L):
        y = x if d.get("slow") else tempo(x, factor)
        y = sosfiltfilt(sos, y).astype(np.float32)
        pad = np.zeros(int(0.4 * SR), np.float32)
        try:
            lu = meter.integrated_loudness(np.concatenate([y, pad]))
            y = y * 10 ** ((-18.0 - lu) / 20)
        except Exception:
            pass
        sf.write(f"{PROC}/{d['id']}.wav", y, SR)
        out.append(y)
    t = LEAD
    tl_lines = []
    for y, d in zip(out, L):
        tl_lines.append(dict(id=d["id"], start=round(t, 3), end=round(t + len(y) / SR, 3), text=d["say"]))
        t += len(y) / SR + d["gap"]
    last_end = tl_lines[-1]["end"]
    total = last_end + 3.0   # 片尾余音
    nar = np.zeros(int(total * SR) + SR, np.float32)
    for y, l in zip(out, tl_lines):
        i0 = int(round(l["start"] * SR)); nar[i0:i0 + len(y)] += y
    nar = nar[: int(round(total * SR))]
    lu = meter.integrated_loudness(nar)
    nar *= 10 ** ((-15.0 - lu) / 20)
    pk = np.abs(nar).max()
    if pk > 10 ** (-1.6 / 20):
        print("warn: narration peak", 20 * np.log10(pk))
    sf.write(f"{WORK}/narration.wav", nar, SR, subtype="FLOAT")
    # 场景边界（与 render.py 同算法）
    scenes = []
    for i, s in enumerate(SCENES):
        ls = [l for l in tl_lines if l["id"].startswith(s["id"] + "_")]
        scenes.append(dict(id=s["id"], first=ls[0]["start"]))
    for i, s in enumerate(scenes):
        s["t0"] = 0.0 if i == 0 else scenes[i - 1]["t1"]
        s["t1"] = scenes[i + 1]["first"] - 0.15 if i + 1 < len(scenes) else total
    json.dump(dict(lines=tl_lines, scenes=scenes, total=total, last_end=last_end, tempo=factor, lead=LEAD),
              open(f"{WORK}/timeline.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{WORK}/narration.srt", "w") as f:
        for i, l in enumerate(tl_lines, 1):
            f.write(f"{i}\n{srt_time(l['start'])} --> {srt_time(l['end'])}\n{l['text']}\n\n")
    json.dump([dict(id=l["id"], text=l["text"], start=l["start"], end=l["end"]) for l in tl_lines],
              open(f"{WORK}/sentences.json", "w"), ensure_ascii=False, indent=1)
    open(f"{WORK}/sentences.txt", "w").write("\n".join(l["text"] for l in tl_lines) + "\n")
    print(f"total {total:.1f}s = {total/60:.2f} min; {chars} chars -> {chars/(last_end-LEAD)*60:.0f} 字/分")


if __name__ == "__main__":
    main()
