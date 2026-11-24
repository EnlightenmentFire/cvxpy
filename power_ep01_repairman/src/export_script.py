"""Export the narration script to a reviewable Markdown file (讲稿)."""
import os
import sys

from script_data import LINES, SECTIONS, spoken_chars

NOTES = {
    "c01": "【示意】冷启动场景为示意，不是书中记载的某一天。",
    "i02": "克罗齐耶的研究以实地访谈和观察为基础。",
    "s1_04": "“巴黎地区的几家”：二手文献常说三家，未能对原书核实，旁白只说“几家”。",
    "s1_05": "每车间维修工人数二手文献说法不一（6–8 / 12），旁白只说“几个到十来个”。",
    "s3_16": "【转述】说明书“不见了”：多部教材转述；原书没有说是谁拿走的，旁白不说“藏”。",
    "s3_17": "人物心理只用“也许”。",
    "s4_02": "【英文原话】Crozier 1964，第 6 章 Power and Uncertainty。",
    "s4_06": "【法文】只上屏，不让中文 TTS 念。",
    "s4_08": "【法文原话】只上屏；措辞以 1977 年原书为准，核不实则只讲意思。",
    "s4_17": "【英文原话】Hickson et al. 1971, ASQ 16(2)。",
    "s6_10": "【二手概括】研究者对 Friedberg 导言的概括。",
    "s7_05": "【推论】由理论推出，不是对这家厂后来情况的记载。",
    "s7_06": "【推论】同上，用“可以想见”。",
}


def main(out):
    lines = ["# 「组织里的权力」第一期《维修工》讲稿", "",
             "> 每一行 = 一句配音（括号里是只上屏、不念的内容）。【示意】【转述】【推论】标记对应画面上的标注。", ""]
    total = 0
    for sec, label in SECTIONS:
        if label:
            lines += [f"## {label[0]} · {label[1]}", ""]
        elif sec == "cold":
            lines += ["## 冷启动", ""]
        elif sec == "intro":
            lines += ["## 片头 · 引子", ""]
        elif sec == "end":
            lines += ["## 尾声", ""]
        for d in [x for x in LINES if x["sec"] == sec]:
            txt = d["text"]
            if d["tts"] is None:
                s = f"- （上屏）*{txt}*"
            elif d["lang"] != "Chinese":
                s = f"- *{txt}*"
                if d.get("sub"):
                    s += f"  \n  字幕：{d['sub']}"
            else:
                s = f"- {txt}"
                total += spoken_chars(d["tts"])
            if d["id"] in NOTES:
                s += f"  \n  > {NOTES[d['id']]}"
            lines.append(s)
        lines.append("")
    lines += ["---", "", "片尾小字：下一期 · 罗伯特·摩西", "",
              f"中文配音约 {total} 字。"]
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out, total, "chars")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "../script/讲稿_v1.md"))
