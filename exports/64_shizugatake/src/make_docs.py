# -*- coding: utf-8 -*-
"""Write 旁白稿.md (lines with timecodes) and narration.srt from timeline.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import CHAPTERS

WK = "/tmp/claude-0/work"
OUT = sys.argv[1]
tl = json.load(open(f"{WK}/timeline.json"))


def tc(t, srt=False):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",") if srt else f"{int(m):02d}:{s:04.1f}"


md = ["# 贱岳之战 · 旁白稿", "", f"总长 {tl['total']/60:.2f} 分钟，{len(tl['lines'])} 句。时间码为成片时间。", ""]
cur = None
for L in tl["lines"]:
    if L["scene"] in CHAPTERS and L["scene"] != cur:
        n, name = CHAPTERS[L["scene"]]
        md += ["", f"## {n} · {name}", ""]
    if L["scene"] == "h0" and cur is None:
        md += ["## 开场", ""]
    cur = L["scene"]
    q = f"  〔引文卡：{L['q'][0]} {L['q'][1]}〕" if L["q"] else ""
    md.append(f"- `{tc(L['start'])}` {L['text']}{q}")
open(f"{OUT}/旁白稿.md", "w").write("\n".join(md) + "\n")

srt, k = [], 1
for L in tl["lines"]:
    for s in L["sub"]:
        srt += [str(k), f"{tc(s['s'], True)} --> {tc(s['e'], True)}", s["text"], ""]
        k += 1
open(f"{OUT}/narration.srt", "w").write("\n".join(srt))
print("docs ok", k - 1, "subs")
