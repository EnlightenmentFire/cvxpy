"""Generate 讲稿.md (with timestamps from timeline), sentences.json / sentences.txt (one line per sentence).
usage: python gen_docs.py <timeline.json> <docs_dir> <sentences_dir>"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from script_data import SCENES, all_lines
from render import chapter_of

tl = json.load(open(sys.argv[1])); dd = sys.argv[2]; sd = sys.argv[3]
os.makedirs(dd, exist_ok=True); os.makedirs(sd, exist_ok=True)
st = {l["id"]: l for l in tl["lines"]}
fmt = lambda t: f"{int(t // 60):02d}:{t % 60:04.1f}"
out = ["# 《王安石变法为什么失败》讲稿（成片对时版）", "",
       f"成片总长 {fmt(tl['total'])}；旁白 {len(tl['lines'])} 句；时间码取自成片时间线。引文出处与核对见《史料核对.md》。", ""]
cur = None
for l in all_lines():
    ch = chapter_of(l["scene"])
    if ch != cur:
        out += ["", f"## {ch}", ""]; cur = ch
    t = st[l["id"]]
    if l["k"] == "q":
        c = l["card"]
        out.append(f"- `{fmt(t['start'])}` **引文**　{c['orig']}　——{c['src']}  \n  白话：{c['plain']}")
    else:
        out.append(f"- `{fmt(t['start'])}` {l['t']}")
n = sum(len(re.sub(r"[，。？！：；、“”《》·…\s—]", "", l["t"])) for l in all_lines())
out += ["", f"（正文约 {n} 字，不计标点。）"]
open(f"{dd}/讲稿.md", "w").write("\n".join(out) + "\n")
sents = [dict(id=l["id"], kind="quote" if l["k"] == "q" else "narration", subtitle=l["t"], tts_text=l["say"], pause_after=l["gap"],
              start=st[l["id"]]["start"], end=st[l["id"]]["end"]) for l in all_lines()]
json.dump(sents, open(f"{sd}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{sd}/sentences.txt", "w").write("\n".join(f"{s['id']}\t{s['tts_text']}" for s in sents) + "\n")
print("docs ok")
