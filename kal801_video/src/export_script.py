# -*- coding: utf-8 -*-
"""把 script_data 导出为可读的旁白稿 docs/script.md。"""
import os
from script_data import B, SECTION_TITLES, LANG_TAG

SCENE_NOTE = {
    "cold": "全黑；字幕一行行打出；近地警告红字", "title": "片名卡", "night": "夜航，747 剪影穿过云层",
    "cockpit": "从背后看三个座位的剪影（机长左、副驾驶右、工程师后侧）", "map": "关岛俯视示意图",
    "timeline": "20 分钟竖向时间轴", "profile": "侧视剖面：真实航迹 / 程序最低高度 / 地形",
    "impact": "黑屏 + 一声闷响 + 静音两秒", "memorial": "黑底白字", "report": "调查报告摘要（中译）",
    "cheese": "瑞士奶酪（注明是比喻）", "ua173": "1978 暖黄胶片：起落架灯 vs 油量表", "stat": "统计条",
    "nasa": "1979 NASA 研讨会", "sim": "模拟器实验对比", "ladder": "六级梯子", "rules": "三条规矩卡",
    "pdi": "权力距离：问卷与刻度尺", "debate": "左右分屏 → 核对附录 → 规矩卡", "after": "安全记录时间线",
    "end": "黑底三句", "credits": "片尾",
}

out = ["# 《不敢说的那句话》旁白稿（自动导出自 src/script_data.py）", "",
       "> 英文原话只出字幕卡，旁白念中文意思；近地警告为自行合成的机械人声。", ""]
cur = None
for x in B:
    if x["sec"] != cur:
        cur = x["sec"]
        title = SECTION_TITLES.get(cur, {0: "冷启动", 11: "收尾", 12: "片尾"}.get(cur, ""))
        out += ["", f"## {cur:02d} {title}", ""]
    line = []
    if x["q"]:
        q = x["q"]
        note = f"；{q['note']}" if q.get("note") else ""
        line.append(f"〔字幕卡 {q['t']} {q['who']}〕`{q['en']}`（{LANG_TAG[q['lang']]}{note}）")
    if x["gpws"]:
        line.append(f"〔近地警告〕`{x['gpws'].upper()}`")
    if x["say"]:
        txt = x["sub"] or x["say"]
        line.append(("**" + txt + "**") if x["key"] else txt)
    if not line:
        line.append(f"〔{SCENE_NOTE.get(x['scene'], x['scene'])}〕")
    out.append(f"- {' '.join(line)}  <sub>[{x['id']} · {SCENE_NOTE.get(x['scene'], x['scene'])}]</sub>")
os.makedirs("../docs", exist_ok=True)
open("../docs/script.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("wrote docs/script.md", len(out), "lines")
