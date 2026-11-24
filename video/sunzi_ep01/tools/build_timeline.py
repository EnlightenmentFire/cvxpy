# -*- coding: utf-8 -*-
"""由逐行旁白 wav 生成 timeline.json（行起止、分段、字幕块）和整条 vo.wav。

用法：python tools/build_timeline.py --vo build/vo_zm_010
任何 TTS / 真人录音只要按行 id 提供 wav（任意采样率，单声道），都能重建时间轴。
"""
import argparse, json, re, sys, pathlib, wave
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import script as S

SR = 48000
# 各段开场留白（秒）：章节卡 / 画面先入
LEAD = {"s1": 1.1, "s2": 0.5, "s3": 2.2, "s4": 0.5, "s5": 2.2, "s6": 0.6, "s7": 0.5, "s8": 2.1, "s9": 0.6, "s10": 0.6}
TITLE_CARD = 3.1      # s1 之后的片名卡
TAIL = 3.4            # 片尾卡
PUNC_GAP = {"：": 0.13, "，": 0.10, "。": 0.22, "？": 0.26, "！": 0.26, "；": 0.18}
Q_GAP = 0.26
MAXC = 17             # 字幕每块最多汉字数（单行 ≤ 17；超过则两行）


def read_wav(p):
    import soundfile as sf
    w, sr = sf.read(str(p), dtype="float32")
    if w.ndim > 1:
        w = w.mean(1)
    if sr != SR:
        n = int(round(len(w) * SR / sr))
        w = np.interp(np.linspace(0, len(w) - 1, n), np.arange(len(w)), w).astype("float32")
    return w


def han(s):
    return len(re.findall(r"[一-鿿]", s))


def split_chunks(sub, kind):
    """把一行切成字幕块：先按句（。？！；：）分，句内再按逗号凑到 MAXC 字以内。保留原标点。"""
    sents = re.findall(r"[^。？！；：]+[。？！；：」』]*|[。？！；：」』]+", sub)
    merged = []
    for p in sents:
        if merged and han(p) == 0:
            merged[-1] += p
        else:
            merged.append(p)
    # 很短的句子（≤4 字）并入相邻句，避免一闪而过
    sents = []
    for p in merged:
        if sents and (han(p) <= 4 or han(sents[-1]) <= 4) and han(sents[-1]) + han(p) <= MAXC:
            sents[-1] += p
        else:
            sents.append(p)
    chunks = []
    for sent in sents:
        parts = re.findall(r"[^，、]+[，、」』]*|[，、」』]+", sent)
        mp = []
        for p in parts:
            if mp and han(p) == 0:
                mp[-1] += p
            else:
                mp.append(p)
        cur = ""
        loc = []
        for p in mp:
            if cur and han(cur) + han(p) > MAXC:
                loc.append(cur); cur = p
            else:
                cur += p
        if cur:
            loc.append(cur)
        if len(loc) > 1 and han(loc[-1]) <= 3 and han(loc[-2]) + han(loc[-1]) <= 2 * MAXC - 6:
            last = loc.pop(); loc[-1] += last
        chunks += loc
    return chunks


def display_lines(txt):
    """字幕显示文本：去掉行尾标点；过长则拆成两行（尽量在标点处、且两行均衡）。"""
    t = txt.strip()
    t = re.sub(r"[，。；：、]+$", "", t)
    t = re.sub(r"[，。；：、]+(?=[」』]$)", "", t)
    if han(t) <= MAXC:
        return [t]
    best, bi = 1e9, None
    for m in re.finditer(r"[，；：、。？！]", t):
        i = m.end()
        d = abs(han(t[:i]) - han(t[i:]))
        if d < best and han(t[:i]) <= MAXC + 1 and han(t[i:]) <= MAXC + 1:
            best, bi = d, i
    if bi is None:
        bi = len(t) // 2
    a, b = t[:bi], t[bi:]
    a = re.sub(r"[，；：、]+$", "", a)
    return [a, b]


def silences(w, min_len=0.07):
    """返回静音段 [(start,end)]（秒）。"""
    hop = int(0.01 * SR)
    n = len(w) // hop
    if n == 0:
        return []
    rms = np.sqrt(np.mean(w[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    thr = max(0.006, np.percentile(rms, 90) * 0.06)
    q = rms < thr
    out, i = [], 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]:
                j += 1
            if (j - i) * 0.01 >= min_len:
                out.append((i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo", required=True)
    ap.add_argument("--out", default=str(ROOT / "build"))
    a = ap.parse_args()
    vo = pathlib.Path(a.vo)
    lines, chunks, segs = [], [], {}
    audio = []
    t = 0.0
    seg_ids = [s[0] for s in S.SEGMENTS]
    for seg_id, title, ls in S.SEGMENTS:
        seg_start = t
        t += LEAD[seg_id]
        for ln in ls:
            lid, kind, sub = ln[0], ln[1], ln[2]
            opt = ln[3] if len(ln) > 3 else {}
            w = read_wav(vo / f"{lid}.wav")
            dur = len(w) / SR
            start, end = t, t + dur
            audio.append((start, w))
            lines.append({"id": lid, "seg": seg_id, "kind": kind, "sub": sub, "start": round(start, 3), "end": round(end, 3)})
            # 字幕块
            cs = split_chunks(sub, kind)
            if len(cs) == 1:
                bounds = [0.0, dur]
            else:
                wts = [han(x) + 0.6 * len(re.findall(r"[，。；：？！、]", x)) for x in cs]
                cum = np.cumsum(wts) / sum(wts) * dur
                sil = silences(w)
                bounds = [0.0]
                for b in cum[:-1]:
                    cand = [(abs((s0 + s1) / 2 - b), (s0 + s1) / 2) for s0, s1 in sil if abs((s0 + s1) / 2 - b) < 0.7 and (s0 + s1) / 2 > bounds[-1] + 0.5]
                    bounds.append(min(cand)[1] if cand else float(b))
                bounds.append(dur)
            for i, cx in enumerate(cs):
                chunks.append({"line": lid, "kind": kind, "text": cx, "lines": display_lines(cx),
                               "start": round(start + bounds[i], 3), "end": round(start + bounds[i + 1], 3)})
            gap = opt.get("gap")
            if gap is None:
                gap = Q_GAP if kind == "q" else PUNC_GAP.get(sub.rstrip("」』")[-1], 0.28)
            t = end + gap
        segs[seg_id] = {"start": round(seg_start, 3), "end": round(t, 3)}
        if seg_id == "s1":
            segs["title"] = {"start": round(t, 3), "end": round(t + TITLE_CARD, 3)}
            t += TITLE_CARD
    segs["end"] = {"start": round(t, 3), "end": round(t + TAIL, 3)}
    total = t + TAIL
    # 字幕块之间不留空隙闪烁：同一行相邻块首尾相接；块尾延长到下一块前或 +0.25s
    for i, ch in enumerate(chunks):
        nxt = chunks[i + 1]["start"] if i + 1 < len(chunks) else total
        ch["end"] = round(min(max(ch["end"], ch["start"] + 0.6) + 0.18, nxt - 0.04), 3)
    mix = np.zeros(int(total * SR) + SR, dtype="float32")
    for st, w in audio:
        i = int(st * SR)
        mix[i:i + len(w)] += w
    import soundfile as sf
    out = pathlib.Path(a.out)
    sf.write(str(out / "vo.wav"), mix, SR)
    json.dump({"fps": 30, "total": round(total, 3), "vo": str(vo.name), "lines": lines, "segs": segs, "chunks": chunks},
              open(out / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    speech = sum(l["end"] - l["start"] for l in lines)
    nh = sum(han(l["sub"]) for l in lines)
    print(f"总时长 {total:.1f}s = {int(total//60)}:{total%60:04.1f}；纯人声 {speech:.1f}s；{nh} 字；{nh/speech:.2f} 字/秒")
    for k in seg_ids[:1] + ["title"] + seg_ids[1:] + ["end"]:
        print(f"  {k:6s} {segs[k]['start']:7.2f} → {segs[k]['end']:7.2f}  ({segs[k]['end']-segs[k]['start']:5.1f}s)")
    over = [ch for ch in chunks if max(han(l) for l in ch["lines"]) > MAXC + 1 or len(ch["lines"]) > 2]
    print("字幕块", len(chunks), "超长", [c["text"] for c in over])


if __name__ == "__main__":
    main()
