# -*- coding: utf-8 -*-
"""逐句挑选配音候选 → 校验（音高 / ASR / 语速）→ 剪静音、拼接、50Hz 高通、统一响度。

用法: python voice_build.py <workdir>
  读 <workdir>/sentences.json 与 <workdir>/voice/sent/*.wav
  写 <workdir>/voice/voice.wav、voice_report.json、voice_timing.json
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
import parselmouth
import soundfile as sf
import soxr

SR = 48000
GAP = 0.20          # 句间停顿（≤0.25s）
PRE_ANSWER = 0.70   # 答案前空拍（0.6–0.8s）
MAX_INNER = 0.22    # 句内逗号停顿上限
F0_LO, F0_HI = 85.0, 105.0


def load(path):
    a, sr = sf.read(path, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    return soxr.resample(a, sr, SR) if sr != SR else a


def frames_db(a, win=0.02):
    n = int(SR * win)
    m = len(a) // n
    fr = a[: m * n].reshape(m, n)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    return 20 * np.log10(rms + 1e-9), n


def trim_and_tighten(a, max_inner=MAX_INNER, thr_rel=-38.0):
    """切掉首尾静音；句内超过 max_inner 的停顿压到 max_inner（保留两端各 40ms 的自然尾音）。"""
    db, n = frames_db(a)
    thr = db.max() + thr_rel
    voiced = db > thr
    idx = np.where(voiced)[0]
    if len(idx) == 0:
        return a
    s, e = idx[0], idx[-1] + 1
    s = max(0, s - 1)                       # 20ms 预留辅音起始
    e = min(len(voiced), e + 4)             # 80ms 尾音
    a = a[s * n: e * n]
    voiced = voiced[s:e]
    # 句内长停顿
    out, i, L = [], 0, len(voiced)
    keep = int(max_inner / 0.02)
    while i < L:
        if not voiced[i]:
            j = i
            while j < L and not voiced[j]:
                j += 1
            run = j - i
            if run > keep:
                half = keep // 2
                out.append(a[i * n: (i + half) * n])
                out.append(a[(j - (keep - half)) * n: j * n])
            else:
                out.append(a[i * n: j * n])
            i = j
        else:
            j = i
            while j < L and voiced[j]:
                j += 1
            out.append(a[i * n: j * n])
            i = j
    out.append(a[L * n:])
    b = np.concatenate(out)
    # 5ms 淡入淡出防咔哒
    f = int(0.005 * SR)
    b[:f] *= np.linspace(0, 1, f)
    b[-f:] *= np.linspace(1, 0, f)
    return b


def median_f0(a):
    s = parselmouth.Sound(a.astype(np.float64), SR)
    p = s.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=300)
    v = p.selected_array["frequency"]
    v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def norm_text(s):
    s = re.sub(r"[，。？！：；、,.?!:;\s《》“”\"']", "", s)
    return s.replace("翔", "降")


def pinyin_seq(s):
    """带声调拼音序列，用来判断「读音」是否正确（ASR 选错同音字不算读错）。"""
    from pypinyin import lazy_pinyin, Style
    s = norm_text(s)
    return lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True)


def pinyin_ok(hyp, ref):
    a, b = pinyin_seq(hyp), pinyin_seq(ref)
    # 「降」在本句读 xiáng（TTS 输入用同音字「翔」），ASR 回写成「降」时 pypinyin 会给 jiang4
    a = ["xiang2" if x == "jiang4" else x for x in a]
    b = ["xiang2" if x == "jiang4" else x for x in b]
    return a == b, a, b


def hanzi_count(s):
    return len(re.findall(r"[一-鿿]", s))


def main(work):
    sys.path.insert(0, work)
    from asr import transcribe  # faster-whisper medium wrapper (work/asr.py)

    S = json.load(open(os.path.join(work, "sentences.json")))
    report, chosen = [], {}
    tmpdir = os.path.join(work, "voice", "tmp")
    os.makedirs(tmpdir, exist_ok=True)
    for s in S:
        cands = sorted(glob.glob(os.path.join(work, "voice", "sent", f"{s['id']}_s*.wav")))
        rows = []
        for c in cands:
            a = trim_and_tighten(load(c))
            tp = os.path.join(tmpdir, os.path.basename(c))
            sf.write(tp, a, SR)
            f0 = median_f0(a)
            cache = tp + ".asr.txt"
            if os.path.exists(cache):
                hyp = open(cache).read()
            else:
                hyp = "".join(x.text for x in transcribe(tp))
                open(cache, "w").write(hyp)
            exact = norm_text(hyp) == norm_text(s["text"])
            ok, pa, pb = pinyin_ok(hyp, s["text"])
            diff = [f"{x}->{y}" for x, y in zip(pb, pa) if x != y]
            dur = len(a) / SR
            rate = hanzi_count(s["text"]) / dur
            rows.append(dict(file=c, f0=round(f0, 1), asr=hyp, asr_exact=exact, asr_ok=ok, pinyin_diff=diff,
                             dur=round(dur, 2), rate=round(rate, 2)))
            print(s["id"], os.path.basename(c), rows[-1], flush=True)

        def score(r):
            pen = 0.0
            if not r["asr_ok"]:
                pen += 100
            if not (F0_LO <= r["f0"] <= F0_HI):
                pen += 10 + min(abs(r["f0"] - F0_LO), abs(r["f0"] - F0_HI))
            pen += abs(r["f0"] - 92) * 0.05
            return pen
        force = json.loads(os.environ.get("VOICE_FORCE", "{}"))
        best = min(rows, key=score)
        if s["id"] in force:  # 人工复核后指定（例如拉速后 ASR 回读出现声调偏差）
            best = [r for r in rows if r["file"].endswith(force[s["id"]])][0]
        chosen[s["id"]] = best
        report.append(dict(id=s["id"], text=s["text"], tts=s["tts"], candidates=rows, chosen=os.path.basename(best["file"])))
    json.dump(report, open(os.path.join(work, "voice", "voice_report.json"), "w"), ensure_ascii=False, indent=1)
    return report, chosen


def assemble(work, chosen, tempo=None):
    """拼接。tempo: {id: 倍速}，用 rubberband（保留共振峰）拉速。"""
    S = json.load(open(os.path.join(work, "sentences.json")))
    tmpdir = os.path.join(work, "voice", "tmp")
    parts, timing, t = [], [], 0.0
    for i, s in enumerate(S):
        src = os.path.join(tmpdir, os.path.basename(chosen[s["id"]]["file"]))
        k = (tempo or {}).get(s["id"], 1.0)
        if abs(k - 1.0) > 1e-3:
            dst = src.replace(".wav", f"_x{k:.2f}.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af",
                            f"rubberband=tempo={k}:formant=preserved:pitchq=quality:transients=crisp", dst], check=True)
            a = load(dst)
        else:
            a = load(src)
        if i > 0:
            gap = PRE_ANSWER if s["id"] == "S6" else GAP
            parts.append(np.zeros(int(gap * SR), np.float32))
            t += gap
        timing.append(dict(id=s["id"], text=s["text"], t0=round(t, 3), t1=round(t + len(a) / SR, 3)))
        parts.append(a)
        t += len(a) / SR
    v = np.concatenate(parts)
    raw = os.path.join(work, "voice", "voice_raw.wav")
    sf.write(raw, v, SR)
    # 50Hz 高通 + 统一到约 -18 dBFS RMS（只算有声部分）
    hp = os.path.join(work, "voice", "voice_hp.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", "highpass=f=50:poles=2", hp], check=True)
    v = load(hp)
    db, n = frames_db(v)
    m = db > db.max() - 35
    fr = v[: len(db) * n].reshape(len(db), n)[m]
    rms_db = 10 * np.log10((fr ** 2).mean() + 1e-12)
    gain = 10 ** ((-18.0 - rms_db) / 20)
    v = v * gain
    peak = np.abs(v).max()
    if peak > 0.89:  # 约 -1 dBFS 余量
        v = v * (0.89 / peak)
    out = os.path.join(work, "voice", "voice.wav")
    sf.write(out, v, SR, subtype="PCM_24")
    json.dump(dict(total=round(len(v) / SR, 3), sentences=timing, tempo=tempo or {}),
              open(os.path.join(work, "voice", "voice_timing.json"), "w"), ensure_ascii=False, indent=1)
    return out, timing, len(v) / SR


if __name__ == "__main__":
    work = sys.argv[1]
    report, chosen = main(work)
    tempo = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    out, timing, total = assemble(work, chosen, tempo)
    print(json.dumps(timing, ensure_ascii=False, indent=1))
    print("total", total)
