# -*- coding: utf-8 -*-
"""Export sentences.json / sentences.txt / 旁白稿.md / narration.srt for box re-voicing and review."""
import json, sys, os
sys.path.insert(0, "/tmp/claude-0/w73/proj")
import timeline
from script import SCENES

DEL = "/tmp/claude-0/w73/deliver"
TL = timeline.build()


def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}".replace(",1000", ",999")


os.makedirs(DEL, exist_ok=True)
sent = [dict(id=r["id"], scene=r["scene"], tts_text=r["say"], subtitle=r["sub"], start=round(r["t0"], 3), end=round(r["t1"], 3)) for r in TL["lines"]]
json.dump(dict(episode="73_caocao_debut", voice="托克维尔（Qwen3-TTS 1.7B Base ICL 克隆，参考 voice_design_reference 18 秒）",
               rate_target="约255字/分（含0.5秒句间停顿）", gap_s=0.5, sentences=sent), open(f"{DEL}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{DEL}/sentences.txt", "w").write("".join(f"{s['id']}\t{s['tts_text']}\n" for s in sent))
with open(f"{DEL}/narration.srt", "w") as f:
    for i, s in enumerate(TL["subs"], 1):
        f.write(f"{i}\n{ts(s['t0'])} --> {ts(s['t1'])}\n{s['text'].replace(chr(10), '')}\n\n")
# readable script
md = ["# 第73期 曹操篇1 旁白稿（含画面卡片）\n"]
k = 0
for sc in SCENES:
    md.append(f"\n## {sc.get('title') or sc['id']}\n")
    for it in sc["items"]:
        if it[0] == "n":
            r = TL["lines"][k]; k += 1
            m, s = divmod(r["t0"], 60)
            md.append(f"- `{int(m):02d}:{s:04.1f}` {r['sub']}")
        elif it[0] == "card":
            d = it[1]; md.append(f"  - 〔古文卡〕{d['text']} —— {d['src']}｜白话：{d['bh']}")
        elif it[0] == "ana":
            md.append(f"  - 〔现代类比〕{it[1]['ana']}\n  - 〔类比偏差〕{it[1]['bias']}")
        elif it[0] == "q3":
            d = it[1]; md.append(f"  - 〔起家三问〕手里有什么：{d['have']}／借了谁的势：{d['lean']}／做对了哪一步：{d['step']}")
        elif it[0] == "yy":
            md.append(f"  - 〔演义说〕{it[1]['yy']}\n  - 〔史书说〕{it[1]['sx']}")
open(f"{DEL}/旁白稿_73.md", "w").write("\n".join(md) + "\n")
print(len(sent), "sentences; total", round(TL["total"], 1), "s")
