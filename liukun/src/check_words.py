# -*- coding: utf-8 -*-
"""出片前自查：旁白稿 + 画面文字 + 字幕文件 里是否有敏感人名/敏感词/族群对立用语/现代类比。"""
import re, os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from script import L
HERE = os.path.dirname(os.path.abspath(__file__))
texts = {"旁白(白话)": "".join(l["text"] for l in L if l["kind"] == "p"),
         "旁白(原文)": "".join(l["text"] + l.get("show", "") for l in L) ,
         "画面文字": "".join(re.findall(r"'([^']*[一-鿿][^']*)'", open(os.path.join(HERE, "scenes_a.js"), encoding="utf8").read() + open(os.path.join(HERE, "scenes_b.js"), encoding="utf8").read())),
         "字幕srt": open(os.path.join(HERE, "..", "out", "liukun.srt"), encoding="utf8").read()}
MODERN = "习近平 毛泽东 邓小平 江泽民 胡锦涛 温家宝 李克强 周恩来 蒋介石 共产党 国民党 中共 政府 总书记 主席 总统 总理 台湾 香港 新疆 西藏 六四 天安门 法轮 文革 革命 民主 独裁 专制 维权 抗议 游行 示威 政变 颠覆 今天的中国 当今 现在的 如今的 当代 现代 告诉我们 启示 教训 时至今日 美国 日本 俄罗斯 乌克兰".split()
ETHNIC = "胡人 汉人 汉族 异族 蛮夷 蛮族 夷狄 胡虏 鞑 民族 种族 五胡乱华 乱华 汉奸 外族 入侵 侵略 野蛮 非我族类 犬羊 屠杀 屠城 灭族 胡 虏 夷 寇 贼".split()
GORE = "血腥 砍头 斩首 尸体 强奸 奸淫 自杀 虐杀 吃人 人相食".split()
ok = True
for name, t in texts.items():
    for grp, ws in (("现代/影射", MODERN), ("族群用语", ETHNIC), ("血腥", GORE)):
        hits = sorted({w for w in ws if w in t})
        if hits: print("[%s] %s: %s" % (name, grp, " ".join(hits)))
print("——白话旁白中出现的单字 胡/虏/夷/寇/贼：", [w for w in "胡虏夷寇贼" if w in texts["旁白(白话)"].replace("胡笳", "")])
