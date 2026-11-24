# -*- coding: utf-8 -*-
import re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from script import L, SEGS
cnt = lambda s: len(re.sub(r"[^一-鿿]", "", s))
NUM = "一二三四五六七八九十"
out = ["# 刘琨——一座没有后方的孤城 · 旁白稿", "",
       "- 旁白共 %d 字，其中朗读的史书原文 %d 字（%.1f%%）。" % (sum(cnt(l["text"]) for l in L), sum(cnt(l["text"]) for l in L if l["kind"] == "q"), 100 * sum(cnt(l["text"]) for l in L if l["kind"] == "q") / sum(cnt(l["text"]) for l in L)),
       "- **粗体「」** = 朗读的原文；〔画面〕= 只上画面、不朗读的原文。出处标在句后。", ""]
for i, (sid, name) in enumerate(SEGS):
    out.append("## %s　%s" % (NUM[i] if i < 10 else "十" + NUM[i - 10], name)); out.append("")
    for l in [x for x in L if x["seg"] == sid]:
        if l["kind"] == "q": out.append("> **「%s」**　——%s" % (l.get("disp") or l["text"], l["src"]))
        else:
            out.append(l["text"])
            if l.get("show"): out.append("　　〔画面：「%s」——%s〕" % (l["show"], l["show_src"]))
        out.append("")
open(os.path.join(os.path.dirname(__file__), "..", "旁白稿.md"), "w", encoding="utf8").write("\n".join(out))
print("ok")
