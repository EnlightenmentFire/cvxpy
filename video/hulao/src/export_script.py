# -*- coding: utf-8 -*-
"""导出逐段旁白稿（供审稿 / 自行录音）。"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, SECTIONS, LEX
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f"{ROOT}/src/timeline.json"))
tot = sum(len(re.findall(r'[一-鿿〇]', l[2])) for l in L); q = sum(len(re.findall(r'[一-鿿〇]', l[2])) for l in L if l[1] == 'q')
T = TL['total']
out = ["# 《孤城》第一集 · 毛德祖守虎牢 —— 逐段旁白稿", "",
       f"> 全稿 {tot} 字，其中史书原文 {q} 字（{100*q/tot:.0f}%）；成片 {int(T//60)} 分 {int(T%60)} 秒。",
       "> 加粗引号内为史书原文（文言，照读），其后为白话解释。时间码为成片位置，行号用于自行录音。",
       "> 自行录音：按行录成 `audio/lines/000.wav … 122.wav`，再依次运行 `src/build_timeline.py`、`src/audio.py`、`render.sh`、`encode.sh`，画面会按新的时长自动重排。", ""]
cur = None; NAMES = {'cold': '冷开场', 's11': '尾声', 's12': '收尾'}
for i, l in enumerate(L):
    if l[0] != cur:
        cur = l[0]; m = [s for s in SECTIONS if s[0] == cur][0]
        out += ["", "## " + (f"{m[1]} · {m[2]}" if m[2] else NAMES[cur]), ""]
    t = TL['lines'][i]['start']; tc = "%d:%04.1f" % (t // 60, t % 60)
    if l[1] == 'q': out.append(f"- `{i:03d}` `{tc}` **“{l[2]}”** —— {l[3]}")
    else: out.append(f"- `{i:03d}` `{tc}` {l[2]}")
out += ["", "## 读音提示（录音时注意）", "",
        "被创、生创（chuāng，同“疮”）· 东还（huán）· 长史（zhǎng shǐ）· 卫瓘（guàn）· 遂（suì）· 刎（wěn）· 髑髅台（dú lóu）· 荥阳（xíng）· 蒲阪（bǎn）· 汜水（sì）· 成皋（gāo）· 拓跋嗣（tuò bá sì）· 乘丧、裕丧（sāng）· 遽（jù）· 变难（nàn）· 不足为美、何为不可（wéi）· 长于守城（cháng）· 奚斤（xī jīn）· 率步骑（shuài）· 阳瓒（zàn）· 不降（xiáng）· 穴地（xué）· 辄（zhé）· 汲河（jí）· 檀道济（tán）· 沈叔狸（lí）· 劲兵（jìng）· 殆尽（dài jìn）· 俱毙（bì）· 将涉期年（jiāng shè jī nián）· 淹缓（yān）· 魏将、守将、将士、将佐（jiàng）· 衣冠（yī guān）· 舍此（shě）"]
open(f"{ROOT}/旁白稿.md", "w").write("\n".join(out) + "\n")
print(len(out), tot, q)
