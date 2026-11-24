"""Generate a human-readable script (docs/讲稿.md) from the structured script."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from script_parser import parse, TTS_GLOBAL, spoken_len

src = Path(__file__).parent.parent / "script" / "wude.script"
out = Path(__file__).parent.parent / "docs" / "讲稿.md"
segs = parse(src)
STAGE_DESC = {
    "slip_open": "竹简从黑暗里浮出，墨字「代火者必將水」逐字显现；黑旗展开",
    "title_card": "片名卡「五德终始」，五色方印",
    "map_qi": "战国示意地图，齐国亮起；十几万字的竹简堆起",
    "wheel_stage": "五德轮盘（大）",
    "lscq_book": "《吕氏春秋》竹简册，「应同」篇朱色标出",
    "slip_prophecy": "三枚竹简写预言原文，画面自下而上变暗（水要来了）",
    "broom": "汉画像石拓片风格：燕昭王拥彗先驱，碣石宫（示意）",
    "zouyan_scroll": "帛书：必止乎仁义节俭；惧然顾化 → 其后不能行之（朱笔划线）",
    "zouyan_scroll2": "同一幅帛书（收回伏笔）",
    "qin_unify": "示意地图：秦的黑色由西向东铺满；公元前221年",
    "qin_list": "黑漆青铜框清单：正朔 · 服色 · 数 · 更名 · 或曰黑龙（逐条亮出，鼓声规整）",
    "qin_law": "律令竹简缓缓下落；「刻削毋仁恩和义」「然后合五德之数」；仁义节俭 vs 急法不赦",
    "han_question": "秦的黑衣挂在衣架上，右侧红光渐起，打一个问号",
    "snake": "白蛇被一剑斩开（墨迹散开，不见血）；老妇跪泣剪影；红旗升起",
    "snake_red": "红色重述：赤帝之符",
    "shrine": "白青黄赤四帝牌位 → 黑帝牌位落下（北畤）→ 红旗 vs 黑帝祠，中间问号",
    "zhangcang": "张苍剪影与历盘：十月岁首，朱印「照旧」",
    "memorial": "奏章竹简：贾谊方案；公孙臣上书；「驳」字朱印盖下",
    "dragon": "云气纹中，金色线条的黄龙一笔一笔显现（标「史书记载」）",
    "zhangcang_exit": "张苍剪影转身离开",
    "smoke": "五采之气升起，被一阵风吹散，红色「诈」字",
    "court": "汉代宫殿线描：今宜何以为正朔？服色何上？「明」字朱圈",
    "seal_five": "整体转黄；正月岁首竹简；五字官印盖下（示意，不仿真实印文）",
    "book_review": "水（秦）← 土（汉·太初）：土克水",
    "simaqian": "司马迁伏案剪影，大字「何哉？」",
    "chain": "相生链：伏羲木→神农火→…→周木→汉火，共工、秦是两条灰色的闰位",
    "run_slot": "轮盘上秦被挤成一条灰缝（闰位）",
    "ke_vs_sheng": "相克（打下来的天下）｜相生（传下来的天下）",
    "suihong": "竹简「漢家堯後 有傳國之運」，随后变灰",
    "wangmang": "尧（火）→舜（土）：让；汉（火）→新（土）：受禅",
    "altar": "洛阳城南三层圜丘（示意），红色铺满，「始正火德」",
    "three_virtues": "同一个汉朝：水（汉初）/ 土（太初）/ 火（建武）",
    "slip_wanshi": "竹简「二世三世至于萬世 傳之無窮」，旁边「終始」，終字朱圈",
    "end_card": "片尾：史料与参考",
}
NUM = {"S0": "", "S1": "一", "S2": "二", "S3": "三", "S4": "四", "S5": "五", "S6": "六", "S7": "七",
       "S8": "八", "S9": "九"}
total = sum(spoken_len(l["text"]) for s in segs for l in s["lines"])
L = ["# 命理与正统 · 第一期《五德终始》讲稿", "",
     f"全文约 {total} 字（不含标点），按旁白语速估计成片 19–20 分钟。", "",
     "排版说明：**引文**单独成行并标出处；每段最后一行是“这说明”；【画面】为主要画面提示。", ""]
for s in segs:
    head = f"{NUM[s['id']]} · {s['title']}" if NUM[s["id"]] else s["title"]
    L += [f"## {head}", ""]
    for ln in s["lines"]:
        stage = [c["_args"][0] for c in ln["cues"] if c["cmd"] == "stage"]
        notes = [c.get("text") for c in ln["cues"] if c["cmd"] == "note"]
        if stage:
            L.append(f"【画面：{STAGE_DESC.get(stage[0], stage[0])}】")
            L.append("")
        if ln["kind"] == "Q":
            L.append(f"> **「{ln['text']}」** —— {ln['src']}")
        elif ln["kind"] == "T":
            L.append(f"**{ln['text']}**")
        else:
            L.append(ln["text"])
        for n in notes:
            L.append(f"\n※ 画面注：{n}")
        L.append("")
L += ["## 附：TTS 读音替换（字幕仍用正字）", "", "| 字幕 | 送入 TTS |", "|---|---|"]
for a, b in TTS_GLOBAL:
    L.append(f"| {a} | {b} |")
L.append("")
out.write_text("\n".join(L), encoding="utf-8")
print("wrote", out)
