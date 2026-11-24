# -*- coding: utf-8 -*-
"""导出逐段旁白稿（供审稿 / 自行录音）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, SECTIONS, tts_text
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f"{ROOT}/src/timeline.json"))
out = ["# 《却月阵》逐段旁白稿", "", "> 加粗引号内为史书原文（文言），其后为白话解释。时间码为成片位置。",
       "> 自行录音：按行录成 `audio/lines/000.wav … 0NN.wav`（行号见每行开头），运行 `src/build_timeline.py`、`src/audio.py`、`render.sh`、`encode.sh` 即可按新时长重排全片。", ""]
cur = None
for i, l in enumerate(L):
    if l[0] != cur:
        cur = l[0]; m = [s for s in SECTIONS if s[0] == cur][0]
        out += ["", "## " + (f"{m[1]} · {m[2]}" if m[2] else ("冷开场" if cur == 'cold' else "收尾")), ""]
    t = TL['lines'][i]['start']; tc = "%d:%04.1f" % (t // 60, t % 60)
    if l[1] == 'q': out.append(f"- `{i:03d}` `{tc}` **“{l[2]}”** —— {l[3]}")
    else: out.append(f"- `{i:03d}` `{tc}` {l[2]}")
    tt = tts_text(l[2])
    if tt.replace('。', '').replace('，', '') != l[2].replace('《', '').replace('》', '').replace('……', '').replace('——', '').replace('。', '').replace('，', ''):
        pass
out += ["", "## 读音提示（录音时注意）", "",
        "丁旿（wǔ）· 白毦（ěr）· 车百乘（shèng）· 矟/槊（shuò）· 率（shuài）· 为却月阵/为虏所杀/终为我物（wéi）· 长孙嵩（zhǎng）· 拉纤、纤绳（qiàn）· 中箭（zhòng）· 覆没（mò）· 九锡（xī）· 辄（zhé）· 魏将、宋将（jiàng）· 阿薄干（ā bó gān）· 一杆（gǎn）"]
open(f"{ROOT}/旁白稿.md", "w").write("\n".join(out) + "\n")
print(len(out))
