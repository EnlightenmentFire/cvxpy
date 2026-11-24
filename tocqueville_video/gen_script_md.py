"""Render script_data.py into SCRIPT.md (human-readable)."""
import re
from script_data import SCENES

out = ["# 《一个法国年轻人看美国小镇》脚本（v1 草稿）", "",
       "> 旁白 = 中文口播；【法文】只出字幕卡，旁白念紧随其后的白话译文。出处按通行分法：上卷 = 1835 年卷，下卷 = 1840 年卷。", ""]
total = 0
for s in SCENES:
    out.append(f"## {s['chapter'] or s['title']}")
    out.append("")
    for d in s["lines"]:
        n = len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"]))
        total += n
        if d["k"] == "q":
            out.append(f"> 【法文】*{d['fr']}*  ")
            out.append(f"> 【白话】{d.get('sub', d['say'])}  ")
            out.append(f"> —— {d['src']}")
        else:
            out.append(f"- {d.get('sub', d['say'])}")
        out.append("")
out.append(f"---\n口播约 {total} 字。")
open("SCRIPT.md", "w").write("\n".join(out))
print("chars", total)
