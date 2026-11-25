import json, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from script import SCENES, all_lines, tts_text
D = "/home/user/work/deliver"
L = all_lines()
json.dump([dict(id=d["id"], kind=("quote" if d["k"] == "q" else "narration"), text=d["say"], tts_text=tts_text(d["say"]))
           for d in L], open(f"{D}/sentences.json", "w"), ensure_ascii=False, indent=1)
open(f"{D}/sentences.txt", "w").write("\n".join(tts_text(d["say"]) for d in L) + "\n")
SEC = {"hook": "开场钩子", "c1": "第一笔：族叔刘元起", "c2": "第二笔：名师卢植", "c3": "第三笔：同学公孙瓒", "c4": "第四笔：马贩子张世平、苏双", "c5": "兑现：黄巾之乱", "end": "收束"}
out = ["# 68 刘备的第一笔起家资本 · 旁白稿", "", "合集：乱世起家录｜刘备篇。配音：托克维尔音色（Qwen3-TTS-12Hz-1.7B-Base 克隆，Apache-2.0）。", "",
       "「引文」行慢读并上古文卡（原文＋出处＋白话）；「类比」「偏差」行对应画面的「现代类比」「类比偏差」标签。", ""]
cur = None
n = 0
for sc in SCENES:
    if sc["sec"] != cur:
        cur = sc["sec"]; out += ["", f"## {SEC[cur]}", ""]
    for ln in sc["lines"]:
        n += len(re.findall(r"[一-鿿]", ln["say"]))
        if ln["k"] == "q":
            card = ln["card"]
            if card == "same":
                out.append(f"> 引文（续）：{ln['say']}")
            else:
                out.append(f"> 引文：{card[0]} ——{card[1]}  \n> 白话：{card[2]}")
        else:
            tg = {"analog": "【类比】", "bias": "【偏差】", "novel": "【演义/史书】", "lone": "【孤证】"}.get(ln.get("tag"), "")
            out.append(f"{tg}{ln['say']}")
        out.append("")
out.insert(2, f"全文 {n} 个汉字（不含标点），{len(L)} 句。")
open(f"{D}/旁白稿.md", "w").write("\n".join(out))
print(n)
