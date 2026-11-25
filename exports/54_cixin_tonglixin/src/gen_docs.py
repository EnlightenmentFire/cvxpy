# -*- coding: utf-8 -*-
"""生成 SCRIPT.md（带时间码的旁白稿）与 sentences.json / sentences.txt（逐句旁白稿，供盒子上重配）。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
import scenes as SC

WK = "/tmp/claude-0/work"
OUTD = sys.argv[1] if len(sys.argv) > 1 else f"{WK}/docs"
os.makedirs(OUTD, exist_ok=True)
J = json.load(open(f"{WK}/timeline.json"))
lines = all_lines()
tl = {x["id"]: x for x in J["lines"]}


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


n = sum(len(re.sub(r"[，。？！：；、“”《》·\s]", "", d["say"])) for d in lines)
md = [f"# 太能共情的人，为什么最容易累垮？——旁白稿\n",
      f"共 {len(lines)} 句，{n} 字（不计标点），成片 {mmss(J['total'])}，约 {n / (J['total'] / 60):.0f} 字/分钟。\n",
      "格式：`时间码` 〔场景 / 证据标签〕 旁白\n"]
cur = None
for d in lines:
    x = tl[d["id"]]
    if d["scene"] != cur:
        cur = d["scene"]
        tag = SC.TAG.get(cur, ("", None))[0]
        md.append(f"\n**〔{cur}{' / ' + tag if tag else ''}〕**\n")
    md.append(f"- `{mmss(x['start'])}` {d['sub']}" + (f"  （配音读作：{d['say']}）" if d['sub'] != d['say'] else ""))
open(f"{OUTD}/SCRIPT.md", "w").write("\n".join(md) + "\n")
json.dump([dict(id=d["id"], scene=d["scene"], text=d["say"], pause_after=d["pause"], start=tl[d["id"]]["start"], end=tl[d["id"]]["end"])
           for d in lines], open(f"{OUTD}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{OUTD}/sentences.txt", "w").write("\n".join(d["say"] for d in lines) + "\n")
print("docs ->", OUTD)
