# -*- coding: utf-8 -*-
"""导出：旁白稿.md（含引文出处）、sentences.json / sentences.txt（逐句旁白，含时间轴，供 box 上重配音）、字幕 srt。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import SCENES
import timeline

LAYER = {0: "经典", 1: "正史", 2: "裴注", 5: "演义"}
TITLES = {"A": "开场钩子", "E": "一 · 败走投曹", "J": "二 · 一张空头上将衔", "M": "三 · 煮酒论英雄", "Q": "四 · 名分跟着人走",
          "T": "五 · 两条起家路", "V": "收束"}


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def main(out):
    T = timeline.build()
    os.makedirs(out, exist_ok=True)
    md = ["# 左将军与煮酒论英雄 · 旁白稿", "", f"成片时长约 {T['total'] // 60:.0f} 分 {T['total'] % 60:.0f} 秒；旁白 {len(T['lines'])} 句。", ""]
    lines = {l["id"]: l for l in T["lines"]}
    for s in SCENES:
        if s["id"] in TITLES:
            md += [f"## {TITLES[s['id']]}", ""]
        for i, l in enumerate(s["lines"]):
            lid = f"{s['id']}{i + 1:02d}"; tl = lines[lid]
            m, sec = divmod(tl["t0"], 60)
            md.append(f"- `{int(m)}:{sec:04.1f}` {l['say']}")
            c = l.get("card")
            if c and c["kind"] == "quote":
                md.append(f"  - 【{LAYER.get(c.get('layer', 1), '')}】「{c['text']}」——{c['src']}；白话：{c['plain']}")
            elif c and c["kind"] in ("analogy", "bias"):
                md.append(f"  - 【{'现代类比' if c['kind'] == 'analogy' else '类比偏差'}】{c['text'].replace(chr(10), '')}")
            elif c and c["kind"] == "duibi":
                md.append(f"  - 【对照】{c['yanyi']} / {c['shishu']}")
        md.append("")
    open(f"{out}/旁白稿.md", "w").write("\n".join(md))
    sent = [dict(id=l["id"], text=l["say"], start=round(l["t0"], 3), end=round(l["t1"], 3)) for l in T["lines"]]
    from script_data import all_lines
    tt = {d["id"]: d["tts"] for d in all_lines()}
    for x in sent:
        x["tts_text"] = tt[x["id"]]
    json.dump(dict(voice="托克维尔（Qwen3-TTS 1.7B Base ICL 克隆）", tempo=json.load(open(f"{timeline.WORK}/tts/proc/durs.json")).get("_tempo"),
                   gap_s=timeline.GAP, sentences=sent), open(f"{out}/sentences.json", "w"), ensure_ascii=False, indent=1)
    open(f"{out}/sentences.txt", "w").write("\n".join(f"{x['id']}\t{x['tts_text']}" for x in sent) + "\n")
    srt = []
    for k, sb in enumerate(T["subs"]):
        srt += [str(k + 1), f"{ts(sb['t0'])} --> {ts(sb['t1'])}", sb["text"], ""]
    open(f"{out}/字幕.srt", "w").write("\n".join(srt))
    print("docs ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
