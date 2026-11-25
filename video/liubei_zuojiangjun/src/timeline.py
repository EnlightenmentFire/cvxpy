# -*- coding: utf-8 -*-
"""时间轴：按处理后旁白时长排出每句起止、场景起止、卡片窗口、字幕块。没有音频的句子按 4.3 字/秒估算。"""
import os, json, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import SCENES, all_lines
from gfx import sub_chunks, WORK

GAP = 0.45          # 句间停顿
SCENE_GAP = 0.75    # 场景切换额外停顿
CARD_HOLD = 0.6     # 带古文卡的句子后多留一点读卡时间
LEAD = 0.35         # 片头第一句前（雷声先响）
TAIL = 3.0


def est(s):
    return len(re.sub(r"[，。？！：；、“”《》\s]", "", s)) / 4.3


def build():
    dp = f"{WORK}/tts/proc/durs.json"
    durs = json.load(open(dp)) if os.path.exists(dp) else {}
    L = all_lines()
    t = LEAD
    scenes = []
    lines = []
    for si, s in enumerate(SCENES):
        if si:
            t += SCENE_GAP
        st = dict(id=s["id"], vis=s["vis"], t0=t - (0 if si == 0 else SCENE_GAP * 0.5), lines=[], cues={})
        for i, l in enumerate(s["lines"]):
            lid = f"{s['id']}{i + 1:02d}"
            d = durs.get(lid) or est(l["say"])
            ln = dict(id=lid, say=l["say"], t0=t, t1=t + d, card=l.get("card"), cue=l.get("cue"), has_audio=lid in durs)
            if ln["cue"]:
                st["cues"][ln["cue"]] = t
            lines.append(ln); st["lines"].append(ln)
            t += d + GAP + (CARD_HOLD if l.get("card") and l["card"]["kind"] == "quote" else 0) + l.get("pause", 0)
        st["t1"] = t + SCENE_GAP * 0.5
        scenes.append(st)
    scenes[0]["t0"] = 0.0
    total = t + TAIL
    scenes[-1]["t1"] = total
    for a, b in zip(scenes, scenes[1:]):
        a["t1"] = b["t0"]
    # 卡片窗口：从该句开始，到下一张卡出现或场景结束（至少 4 秒）
    cards = []
    for s in scenes:
        cs = [l for l in s["lines"] if l["card"]]
        for k, l in enumerate(cs):
            end = cs[k + 1]["t0"] if k + 1 < len(cs) else s["t1"] - 0.15
            if "next" in s["cues"] and l["t0"] < s["cues"]["next"]:
                end = min(end, s["cues"]["next"] - 0.2)
            cards.append(dict(t0=l["t0"], t1=max(end, l["t0"] + 4.0) if k + 1 == len(cs) and "next" not in s["cues"] else end, card=l["card"], scene=s["id"]))
    # 字幕块
    subs = []
    for l in lines:
        ch = sub_chunks(l["say"])
        n = [max(1, len(c)) for c in ch]; tot = sum(n)
        tt = l["t0"]
        for c, k in zip(ch, n):
            d = (l["t1"] - l["t0"]) * k / tot
            subs.append(dict(t0=tt, t1=tt + d, text=c)); tt += d
    return dict(scenes=scenes, lines=lines, cards=cards, subs=subs, total=total)


if __name__ == "__main__":
    T = build()
    print("total %.1fs (%d:%02d)" % (T["total"], T["total"] // 60, T["total"] % 60))
    for s in T["scenes"]:
        print(s["id"], s["vis"], "%.1f-%.1f" % (s["t0"], s["t1"]))
    json.dump(T, open(f"{WORK}/timeline.json", "w"), ensure_ascii=False, indent=0)
