# -*- coding: utf-8 -*-
"""导出逐段旁白稿（审稿 / 自行录音用）。"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, SECTIONS
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f"{ROOT}/src/timeline.json"))
han = lambda s: len(re.findall(r'[一-鿿]', s))
tot = sum(han(l[2]) for l in L); q = sum(han(l[2]) for l in L if l[1] == 'q')
out = ["# 孤城 · 第二集《玉璧》逐段旁白稿", "",
       f"> 加粗引号内为史书原文（文言），其后为白话。时间码为成片位置；全片 {int(TL['total'] // 60)} 分 {int(TL['total'] % 60)} 秒，旁白 {tot} 字，其中文言 {q} 字（{100 * q / tot:.0f}%）。",
       "> 自行录音：按行号录成 `audio/lines/000.wav … 0NN.wav`，再跑 `src/build_timeline.py`、`src/audio.py`、`render.sh`、`encode.sh`，画面会按新时长自动重排。", ""]
cur = None
for i, l in enumerate(L):
    if l[0] != cur:
        cur = l[0]; m = [s for s in SECTIONS if s[0] == cur][0]
        out += ["", "## " + (f"{m[1]} · {m[2]}" if m[2] else ("冷启动" if cur == 'cold' else "收尾")), ""]
    t = TL['lines'][i]['start']; tc = "%d:%04.1f" % (t // 60, t % 60)
    out.append(f"- `{i:03d}` `{tc}` **“{l[2]}”** —— {l[3]}" if l[1] == 'q' else f"- `{i:03d}` `{tc}` {l[2]}")
out += ["", "## 读音提示（自己录音时注意）", "",
        "韦孝宽（kuān）· 世为三辅著姓（wéi，zhù）· 守将（jiàng）· 一行字（háng）· 缚楼（fù）· 长沟、长柄（cháng）· 木栅（zhà）· 以扞之（hàn）· 必不为降将军（wéi xiáng jiāng）· 不降（xiáng）· 共为一冢（wéi，zhǒng）· 劲弩（jìng）· 凶身自陨（yǔn）· 众将（jiàng）· 斛律（hú lǜ）· 敕勒（chì lè）· 天似穹庐（sì）· 笼盖（lǒng）· 见牛羊（xiàn）· 槲树（hú）· 邺（yè）· 祖珽（tǐng）· 勒死（lēi）· 冲着（chòng）· 死难（nàn）· 旬朔（xún shuò）"]
open(f"{ROOT}/旁白稿.md", "w").write("\n".join(out) + "\n")
print('ok', tot, q)
