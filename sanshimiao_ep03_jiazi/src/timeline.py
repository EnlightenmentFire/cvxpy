# -*- coding: utf-8 -*-
"""Build timeline.json (gear clicks, tags, captions) from narration timing.

Input: voice_timing.json  {"lines": [{"id","start","end"}], "anchors": {name: seconds}}
  anchors (from ASR word timestamps when available): quan (圈 in L4), shen (申), wu (午),
  chou (丑), y2044 (2044 in L2), suoyi (所以 in L8).
If an anchor is missing it is estimated from the character position in the line.

Step schedule (step k moves the gears from pair k to pair k+1; step 60 returns to 甲子):
  steps 1..10  : even ticks through L3/L4, step 10 (-> 甲戌, 天干转满一圈) lands on 圈.
  steps 11..59 : one smooth accelerating spin from L5 to the end of L7 (rate ramps up),
                 tuned so 甲申/甲午 fall as close as possible to the words 申/午.
  hold          : counter sits on 60 (癸亥) through the end of L7 and the silent beat.
  step 60       : the final click, just before the answer line -> 甲子 again.
"""
import json
import sys

import numpy as np


def est_anchor(line, text, ch, nth=1):
    i = -1
    for _ in range(nth):
        i = text.index(ch, i + 1)
    return line["start"] + (line["end"] - line["start"]) * (i + 0.5) / len(text)


def build(vt, lines_txt):
    L = {l["id"]: l for l in vt["lines"]}
    T = {l["id"]: l["tts"] for l in lines_txt}
    an = dict(vt.get("anchors", {}))
    # anchors from ASR word timestamps (homophones accepted: ASR writes 深/五/虚 for 申/午/戌)
    words = vt.get("words", [])
    def word_anchor(line_id, cands):
        l = L[line_id]
        for w, a, b in words:
            if l["start"] - 0.3 <= a <= l["end"] + 0.1 and any(c in w for c in cands):
                return max(a, b - 0.22)
        return None
    for k, lid, cands in (("quan", "L4", ["圈"]), ("xu", "L5", ["戌", "虚", "需", "须"]), ("shen", "L5", ["申", "深", "身", "伸"]), ("wu", "L5", ["午", "五", "武"]),
                          ("chou", "L6", ["丑"]), ("y2044", "L2", ["20", "二零"]), ("suoyi", "L8", ["所"])):
        v = word_anchor(lid, cands)
        if v is not None and k not in an:
            an[k] = round(float(v), 3)
    an.setdefault("quan", est_anchor(L["L4"], T["L4"], "圈"))
    an.setdefault("shen", est_anchor(L["L5"], T["L5"], "申"))
    an.setdefault("wu", est_anchor(L["L5"], T["L5"], "午"))
    an.setdefault("chou", est_anchor(L["L6"], T["L6"], "丑"))
    an.setdefault("y2044", est_anchor(L["L2"], T["L2"], "二", 1))
    an.setdefault("suoyi", est_anchor(L["L8"], T["L8"], "所"))

    # musical grid: the final click (answer hit) must sit exactly on a beat; tempo ~120
    t_ans = L["L8"]["start"] - 0.10
    # the answer hit must be a downbeat (beat index divisible by 4) so the post-answer bars and the
    # loop back to t=0 share one 4/4 grid; tempo stays within 110-130
    kb = max([k for k in range(36, 64, 4) if 110 <= 60 * k / t_ans <= 130], key=lambda k: -abs(60 * k / t_ans - 120))
    bpm = 60 * kb / t_ans
    beat = 60 / bpm
    eighth = beat / 2
    q = lambda x: round(x / eighth) * eighth
    steps = []
    # 1..10: one click per beat; the 10th (-> 甲戌, 天干转满一圈) lands on 圈, so the
    # gears start turning around "用两套字配对"
    t10 = round((an["quan"] + 0.02) / beat) * beat        # clicks 1-10 exactly on beats
    steps += [t10 - (10 - k) * beat for k in range(1, 11)]
    # 11..59 accelerating spin
    Ta = L["L5"]["start"] + 0.05
    Tb = q(L["L7"]["end"] - 0.30)        # counter reaches 60 just before the question ends (eighth grid)
    D = Tb - Ta
    best = None
    for p in np.linspace(1.0, 3.0, 21):
        for r0 in np.linspace(2.5, 6.0, 36):
            # rate r(tau) = r0 + c*(tau/D)^p, integral over D = 49 steps
            c = (49 - r0 * D) * (p + 1) / D
            if c < 0:
                continue
            tau = np.linspace(0, D, 4001)
            S = r0 * tau + c * D / (p + 1) * (tau / D) ** (p + 1)
            def when(k):
                return Ta + np.interp(k, S, tau)
            r_end = r0 + c
            if r_end > 16:
                continue
            err = (when(10) - an["shen"]) ** 2 + (when(20) - an["wu"]) ** 2
            if best is None or err < best[0]:
                best = (err, p, r0, c, S, tau)
    _, p, r0, c, S, tau = best
    for k in range(1, 50):                # steps 11..59 begin at S = k-1 .. 48 ; step 11 at Ta
        steps.append(float(Ta + np.interp(k - 1, S, tau)))
    # final click
    steps.append(t_ans)
    assert len(steps) == 60, len(steps)

    # end on a bar line (4/4 from t=0) at least `tail` after the last word -> seamless musical loop
    nb = int(np.ceil((L["L8"]["end"] + float(vt.get("tail", 1.0))) / beat))
    while nb % 4:
        nb += 1
    dur = nb * beat

    def s_time(k):   # time the gears reach pair index k (k steps done) ~ start of step k + small
        return steps[k - 1] + 0.05

    ev = {
        "year_a": L["L2"]["start"] + 0.05,
        "year_b": an["y2044"] - 0.05,
        "year_off": L["L3"]["start"] + 0.2,
        "cha_on": steps[9] + 0.08,
        "cha_off": L["L5"]["start"] + 0.35,
        "tags_on": L["L5"]["start"],
        # a tag is a log entry: it appears once the gears have passed that pair AND (for 戌/申/午) the word is said
        "tag_times": [L["L5"]["start"] + 0.05, max(s_time(10), an.get("xu", L["L5"]["start"] + 0.3) - 0.05),
                      max(s_time(20), an["shen"] - 0.05), max(s_time(30), an["wu"] - 0.05), s_time(40), s_time(50)],
        "chou_on": L["L6"]["start"] - 0.05,
        "chou_x": an["chou"] - 0.05,
        "tags_off": s_time(54),
        "spin": {"p": round(float(p), 2), "r0": round(float(r0), 2), "r_end": round(float(r0 + c), 2)},
        "bpm": bpm, "beat": beat, "ans_beat": kb, "total_beats": nb, "stop": steps[58], "drop": Tb,
    }
    W = lambda segs: [[s, h] for s, h in segs]
    caps = [
        {"start": 0.0, "segs": W([("为什么", 0), ("六十年", 1), ("一个轮回？", 0)])},
        {"start": L["L2"]["start"], "segs": W([("1984 甲子 → ", 0), ("2044", 1), (" 甲子", 0)])},
        {"start": L["L3"]["start"], "segs": W([("天干 ", 0), ("10", 1), (" 个，地支 ", 0), ("12", 1), (" 个", 0)])},
        {"start": L["L5"]["start"], "segs": W([("每一轮错开 ", 0), ("2", 1), (" 格", 0)])},
        {"start": L["L6"]["start"], "segs": W([("永远没有「", 0), ("甲丑", 1), ("」年", 0)])},
        {"start": L["L7"]["start"], "segs": W([("什么时候", 0), ("同时", 1), ("回到起点？", 0)])},
        {"start": t_ans, "answer": True, "small_start": an["suoyi"] - 0.1, "segs": []},
    ]
    return {"duration": float(dur), "lines": vt["lines"], "anchors": an, "step_times": [float(x) for x in steps],
            "events": ev, "captions": caps}


if __name__ == "__main__":
    vt = json.load(open(sys.argv[1]))
    lines_txt = json.load(open(sys.argv[2]))
    tl = build(vt, lines_txt)
    json.dump(tl, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
    st = tl["step_times"]
    print("duration", tl["duration"], "spin", tl["events"]["spin"])
    print("step10", round(st[9], 2), "step20/30 vs shen/wu", round(st[19], 2), round(tl["anchors"]["shen"], 2),
          round(st[29], 2), round(tl["anchors"]["wu"], 2), "step59", round(st[58], 2), "ans", round(st[59], 2))
