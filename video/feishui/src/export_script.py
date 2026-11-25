# -*- coding: utf-8 -*-
"""导出逐句旁白稿：sentences.json / sentences.txt / 旁白稿.md（含时间码），供 box 上重配或审稿。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines, SECTIONS

HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
tl = json.load(open(f"{HERE}/timeline.json")); T = {l["id"]: l for l in tl["lines"]}
fmt = lambda s: f"{int(s // 60):02d}:{s % 60:05.2f}"
rows = []
for d in all_lines():
    t = T.get(d["id"], {})
    rows.append(dict(id=d["id"], section=d["sec_title"], kind="quote" if d["k"] == "q" else "narration", text=d["text"], tts_text=d["say"],
                     source=d["src"], start=t.get("start"), end=t.get("end"), pause_after=d["gap"]))
json.dump(dict(voice="托克维尔（Qwen3-TTS-12Hz-1.7B-Base ICL 克隆，参考 A0b 18 秒）", tempo={"narration": 1.12, "quote": 1.02}, lines=rows),
          open(f"{out}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{out}/sentences.txt", "w").write("\n".join(r["tts_text"] for r in rows) + "\n")
md = ["# 淝水之战 · 旁白稿", "", f"全片 {fmt(tl['total'])}，{len(rows)} 句。引文行为朗读的古文原句（字幕卡片显示繁体原文与出处）。", ""]
for sid, title, _ in SECTIONS:
    md += [f"## {title}", ""]
    for r in rows:
        if r["id"].startswith(sid + "_"):
            tc = fmt(r["start"]) if r["start"] is not None else "--"
            md.append(f"- `{tc}` " + (f"**「{r['text']}」** —— {r['source']}" if r["kind"] == "quote" else r["text"]))
    md.append("")
open(f"{out}/旁白稿.md", "w").write("\n".join(md))
print("exported", len(rows))
