# -*- coding: utf-8 -*-
"""重做一句里的任意一段，新段时长与旧段完全相同（整句、整片时间轴都不动）。

python fix_seg2.py NARR_DIR LINE_ID 段内关键字 "TTS写法1|TTS写法2" 种子1,种子2,... [归一字表]

- 段的位置：按 split_line_q 切段，再用句中插入的“纯零静音”找精确边界。
- 候选：每种写法 × 每个种子；拉伸到旧段的语速后做两路 ASR（Whisper + Paraformer）。
  归一字表形如 "还:环缓换寰桓,中:众重"——ASR 写成这些同音字时视为读对（字幕用原字）。
- 选择：两路 ASR 都 ≥0.95 → 音高在 85–105 Hz → 两路最低相似度 → 时长最接近。
  全部候选都不过就不改，旧段保留。
- 选中后用一次 rubberband（保共振峰）直接拉到旧段的精确时长，拼回整句；该段的逐字时间按新音频重算。
"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qtts  # noqa: E402
import qnarr  # noqa: E402
import script  # noqa: E402

SR = qtts.SR
HAN = re.compile(r"[一-鿿0-9]")


def zero_runs(w, min_len):
    z = np.concatenate([[False], w == 0.0, [False]])
    d = np.diff(z.astype(np.int8))
    starts, ends = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
    return [(a, b) for a, b in zip(starts, ends) if b - a >= min_len]


def seg_bounds(line, pieces, infos):
    """返回每段的 [起, 止) 样本位置"""
    n = len(pieces)
    pred, t = [], 0
    for k in range(n):
        d = int(round(infos[k]["dur"] * SR))
        pred.append([t, t + d])
        p = min(qnarr.PAUSE_CAP, pieces[k][2])
        t += d + (int(p * SR) if (p and k < n - 1) else 0)
    bounds = [list(x) for x in pred]
    for k in range(n - 1):
        p = min(qnarr.PAUSE_CAP, pieces[k][2])
        if not p:
            continue
        need = int(p * SR)
        runs = zero_runs(line, int(need * 0.9))
        if not runs:
            continue
        # 离预测的段尾最近、且长度不短于插入静音的零段
        a, b = min(runs, key=lambda r: abs(r[0] - pred[k][1]) + abs((r[1] - r[0]) - need) * 0.1)
        if abs(a - pred[k][1]) < int(0.15 * SR):
            bounds[k][1] = a
            bounds[k + 1][0] = b
    bounds[0][0] = 0
    bounds[-1][1] = len(line)
    return bounds


def normalize(text, table):
    for good, alts in table.items():
        for ch in alts:
            text = text.replace(ch, good)
    return text


def main(narr, lid, key, variants, seeds, table):
    rep = json.load(open(os.path.join(narr, "report.json")))
    metas = json.load(open(os.path.join(narr, "meta.json")))
    meta = {m["id"]: m for m in metas}
    d = script.BY_ID[lid] if hasattr(script, "BY_ID") else next(x for x in script.LINES if x["id"] == lid)
    pieces = qnarr.split_line_q(d["text"])
    infos = rep[lid]
    assert len(infos) == len(pieces), (len(infos), len(pieces))
    k = next(i for i, p in enumerate(pieces) if key in p[0])
    display, is_q, _ = pieces[k]
    line, sr = sf.read(os.path.join(narr, lid + ".wav"), dtype="float32")
    assert sr == SR
    bounds = seg_bounds(line, pieces, infos)
    A, B = bounds[k]
    D = (B - A) / SR
    tempo = infos[k]["tempo"]
    print(f"[{lid}] 第 {k+1}/{len(pieces)} 段：{display}  旧段 {D:.3f}s（{A}–{B}），语速 ×{tempo}", flush=True)
    want = qtts.syllables(display)
    nhan = len(HAN.findall(display))
    cands = []
    for v in variants:
        for s in seeds:
            raw = qtts.trim_and_cap(qtts.gen(v, s), cap=qnarr.PAUSE_CAP)
            w2 = qtts.trim_and_cap(qtts.stretch(raw, tempo), cap=qnarr.PAUSE_CAP)
            f0 = qtts.median_f0(w2)
            c = qnarr.check(display, w2)
            sw = qtts.similarity(want, qtts.syllables(normalize(c["whisper"], table)))
            sp = qtts.similarity(want, qtts.syllables(normalize(c["paraformer"], table)))
            ratio = D / (len(w2) / SR)
            ok_f0 = (qtts.F0_LO <= f0 <= qtts.F0_HI) if nhan >= 8 else (75 <= f0 <= 115)
            ok = min(sw, sp) >= 0.95 and not c["bad_keys"] and 0.9 <= ratio <= 1.1
            print(f"  [{v}] seed {s}: f0={f0:.1f} W={sw:.3f} P={sp:.3f} 时长比={ratio:.3f} {'OK' if ok and ok_f0 else ''}"
                  f"\n      W:{c['whisper']}\n      P:{c['paraformer']}", flush=True)
            cands.append(dict(score=(ok, ok_f0, round(min(sw, sp), 3), -abs(1 - ratio)), raw=raw, v=v, s=s, f0=f0,
                              sw=sw, sp=sp, c=c))
    best = max(cands, key=lambda x: x["score"])
    if not (best["score"][0] and best["score"][1]):
        print("没有候选同时通过 ASR、音高、时长三项，保留旧段", flush=True)
        return False
    raw = best["raw"]
    # 一次拉伸到旧段精确时长
    tempo2 = (len(raw) / SR) / D
    w3 = qtts.stretch(raw, tempo2)
    n = B - A
    if len(w3) >= n:
        w3 = w3[:n]
    else:
        w3 = np.concatenate([w3, np.zeros(n - len(w3), np.float32)])
    fade = int(0.004 * SR)              # 拼接处 4 ms 渐变，避免爆音
    w3[:fade] *= np.linspace(0, 1, fade); w3[-fade:] *= np.linspace(1, 0, fade)
    new_line = np.concatenate([line[:A], w3.astype(np.float32), line[B:]])
    assert len(new_line) == len(line)
    c3 = qnarr.check(display, w3)
    print(f"选中 [{best['v']}] seed {best['s']}，终版 W:{c3['whisper']} | P:{c3['paraformer']}", flush=True)
    sf.write(os.path.join(narr, lid + ".wav"), new_line, SR)
    # 逐字时间：只替换这一段的字
    m = meta[lid]
    i0 = sum(len(HAN.findall(p[0])) for p in pieces[:k])
    newt = qnarr.char_times(display, c3["words"], D, A / SR)
    assert len(newt) == nhan
    m["words"][i0:i0 + nhan] = [[ch, a, b, is_q] for ch, a, b in newt]
    m["f0"] = round(qtts.median_f0(new_line), 1)
    json.dump(metas, open(os.path.join(narr, "meta.json"), "w"), ensure_ascii=False, indent=1)
    infos[k].update(seed=best["s"], tts_text=best["v"], f0=round(best["f0"], 1), whisper=c3["whisper"],
                    paraformer=c3["paraformer"], sim=round(min(best["sw"], best["sp"]), 3),
                    sim_w=round(best["sw"], 3), sim_p=round(best["sp"], 3), ok=True,
                    tries=infos[k].get("tries", []) + [dict(seed=c["s"], f0=round(c["f0"], 1), sim_w=round(c["sw"], 3),
                                                            sim_p=round(c["sp"], 3)) for c in cands],
                    fixed=True, fixed_note="同音字替换后重做，时长对齐旧段")
    json.dump(rep, open(os.path.join(narr, "report.json"), "w"), ensure_ascii=False, indent=1)
    print(f"已替换：整句中位音高 {m['f0']} Hz，时长不变 {len(new_line)/SR:.3f}s", flush=True)
    return True


if __name__ == "__main__":
    tbl = {}
    if len(sys.argv) > 6 and sys.argv[6]:
        for item in sys.argv[6].split(","):
            g, alts = item.split(":")
            tbl[g] = alts
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split("|"), [int(x) for x in sys.argv[5].split(",")], tbl)
