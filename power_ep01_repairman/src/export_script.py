"""Export the narration script to a reviewable Markdown file (讲稿)."""
import os
import sys

from script_data import LINES, SECTIONS, spoken_chars

NOTES = {
    "c01": "【示意】冷启动场景为示意，不是书中记载的某一天。",
    "s1_03": "Crozier 1964, pp. 58, 62, 68。",
    "s1_04": "Crozier 1964, pp. 59, 61, 117。",
    "s1_05": "Crozier 1964, pp. 62, 89–90。",
    "s1_06": "Crozier 1964, pp. 89–90（约一打维修工，每人专管三台机器，既调机器也修机器）。",
    "s1_07": "Crozier 1964, p. 68（底薪以定额的 85% 为准，超出部分为计件奖金）。",
    "s1_08": "Crozier 1964, pp. 63, 70。",
    "s1_09": "Crozier 1964, pp. 89, 157。",
    "s2_04": "原书没有“机器一停女工就少挣钱”的说法，已改。",
    "s2_05": "Crozier 1964, p. 109（第 4 章）；pp. 131, 154。",
    "s3_03": "Crozier 1964, pp. 90, 126。",
    "s3_05": "Crozier 1964, p. 90。",
    "s3_06": "Crozier 1964, p. 97。",
    "s3_07": "Crozier 1964, p. 97（tolerant paternalism）。",
    "s3_08": "Crozier 1964, pp. 98–99, 154。",
    "s3_13": "Crozier 1964, p. 126（they are the real bosses）。",
    "s3_14": "Crozier 1964, p. 153（rule-of-thumb skill）。",
    "s3_15": "Crozier 1964, p. 153：原书措辞即“设法让它们从车间里消失”。",
    "s3_16": "Crozier 1964, p. 153 脚注。教材里“预防性维护推不下去、有人搞破坏”的说法原书查不到，不用。",
    "s3_16c": "Crozier 1964, p. 153。",
    "s3_17": "人物心理只用“也许”。",
    "s4_02": "【英文原话】Crozier 1964, p. 158。",
    "s4_06": "【法文】只上屏，不让中文 TTS 念。",
    "s4_07b": "Crozier & Friedberg 1977（约 p. 21），法文只上屏。",
    "s4_08": "【法文原话】只上屏，1977 年初版 pp. 59–60。",
    "s4_11": "Crozier & Friedberg 1977, p. 71。",
    "s4_17": "【英文原话】Hickson et al. 1971, ASQ 16(2), p. 219。",
    "s4_19": "Hickson 等 1971, p. 221 原意。",
    "s4_22": "第三条依据 Hickson 等 1971, p. 225：维修一停，产出很快就停。",
    "s4_22b": "Hickson 等 1971, p. 225：“很可能”有工会协议；“得三条一起解释”。",
    "s5_05": "Crozier 1964, p. 192。",
    "s6_04": "Crozier 1964, pp. 193–194；Friedberg 2010 导言 p. xi。",
    "s6_07": "Crozier 1964, pp. 160–161（下属施压要求新规章限制上级权力）。原书没有“女工最想要更多规章”的说法。",
    "s6_08b": "Crozier, Sociologie du travail, 1960, pp. 61–75，按原文结构翻译。",
    "s6_09": "Friedberg 2010 年导言 p. xii。",
    "s6_10": "Crozier 1964, pp. 153, 156。“阴影地带”的说法不用。",
    "s7_05": "【推论】由理论推出，不是对这家厂后来情况的记载。",
    "s7_05b": "Crozier & Friedberg 1977, p. 67（作者自称“推到极端”的说法）。",
    "s7_06": "【推论】用“可以想见”。",
    "s7_06a": "Hickson 等 1971, p. 224（作者的推断）。",
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
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "../script/讲稿_v3.md"))
