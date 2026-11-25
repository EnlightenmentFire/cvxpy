"""Write sentences/sentences.json + sentences.txt (one line per sentence, TTS text) and 旁白稿.md (readable script)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import S, all_lines
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(f"{ROOT}/sentences", exist_ok=True)
L = all_lines()
json.dump([dict(id=l["id"], scene=l["scene"], kind=l["k"], tts=l["say"], subtitle=(l["say"] if l["k"] == "q" else l["sub"]),
                card=(l["sub"] if l["k"] == "q" else None), source=l.get("src"), pause_after=l["gap"]) for l in L],
          open(f"{ROOT}/sentences/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{ROOT}/sentences/sentences.txt", "w").write("".join(l["say"] + "\n" for l in L))
md = ["# 旁白稿：小田原征伐与刀狩（从无名小卒到天下人 · 终章）", "",
      "> 一行一句，与成片配音一致。引文行：旁白读白话，画面上屏原文（标出处）。", ""]
for s in S:
    md.append(f"## {s['title'] or '开场钩子'}"); md.append("")
    for l in s["lines"]:
        if l["k"] == "q":
            md.append(f"> **原文**：{l['sub']}  \n> **出处**：{l['src']}  \n> **旁白**：{l['say']}")
        else:
            t = l["say"]
            from script_data import SUBS
            for a, b in SUBS.items(): t = t.replace(a, b)
            md.append(t)
        md.append("")
open(f"{ROOT}/旁白稿.md", "w").write("\n".join(md))
print(len(L), "lines")
