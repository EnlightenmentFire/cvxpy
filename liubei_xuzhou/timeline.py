# -*- coding: utf-8 -*-
"""时间线：按每句实测时长排布旁白、章节卡、场景区间、字幕屏。输出 timeline.json。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import L, CH
import widgets as Wd

LINES = "/tmp/claude-0/work/tts/lines/lines.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.json")
LEAD = 0.55          # 片头：鼓点与城门铁闩先响
CH_CARD = 2.0        # 章节卡（无旁白）
GAP = {"n": 0.42, "q": 0.62, "a": 0.5, "b": 0.5}
TAIL = 1.6


def build(durs=None):
    if durs is None:
        durs = {k: v["dur"] for k, v in json.load(open(LINES)).items()}
    chname = dict(CH)
    t = LEAD
    lines, cards = [], []
    prev_ch = None
    for d in L:
        if d["ch"] != prev_ch and d["ch"] not in ("open",):
            cards.append(dict(ch=d["ch"], title=chname[d["ch"]], t0=t, t1=t + CH_CARD))
            t += CH_CARD
        prev_ch = d["ch"]
        dur = durs.get(d["id"], len(d["t"]) / 4.3)
        lines.append(dict(id=d["id"], ch=d["ch"], sc=d["sc"], k=d["k"], t=d["t"], q=d.get("q"), t0=t, t1=t + dur))
        t += dur + d.get("gap", GAP[d["k"]])
    end = t + TAIL
    # 场景区间：连续同 sc 的句子合为一场；章节卡归入下一场
    scenes = []
    for i, ln in enumerate(lines):
        if scenes and scenes[-1]["sc"] == ln["sc"]:
            scenes[-1]["ids"].append(ln["id"])
        else:
            scenes.append(dict(sc=ln["sc"], ids=[ln["id"]], t0=ln["t0"]))
    for c in cards:
        for s in scenes:
            if abs(s["t0"] - c["t1"]) < 1e-6:
                s["t0"] = c["t0"]
    scenes[0]["t0"] = 0.0
    for i, s in enumerate(scenes):
        s["t1"] = scenes[i + 1]["t0"] if i + 1 < len(scenes) else end
    # 字幕屏
    subs = []
    for ln in lines:
        if ln["k"] == "q":
            continue
        screens = Wd.split_sub(ln["t"])
        tot = sum(len(s) for s in screens)
        a = ln["t0"]
        for s in screens:
            b = a + (ln["t1"] - ln["t0"]) * len(s) / tot
            subs.append(dict(text=s, t0=a, t1=b, id=ln["id"]))
            a = b
    tl = dict(end=end, lines=lines, cards=cards, scenes=scenes, subs=subs)
    json.dump(tl, open(OUT, "w"), ensure_ascii=False, indent=0)
    return tl


if __name__ == "__main__":
    tl = build()
    print("end", round(tl["end"], 1), "s;", len(tl["scenes"]), "scenes;", len(tl["subs"]), "subs")
    for s in tl["scenes"]:
        print(f"{s['t0']:7.1f} {s['t1']:7.1f} {s['sc']}")
