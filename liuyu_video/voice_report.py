# -*- coding: utf-8 -*-
"""把 qnarr 的 report.json 汇总成表：逐段音高、两套 ASR 相似度、重试次数。"""
import json, sys, statistics
rep = json.load(open(sys.argv[1]))
rows, f0s, ok, tot, retry, first = [], [], 0, 0, 0, 0
for lid, segs in rep.items():
    for s in segs:
        tot += 1; ok += s["ok"]; retry += len(s["tries"]) - 1; f0s.append(s["f0"]); first += len(s["tries"]) == 1 and s["ok"]
        rows.append(f"| {lid} | {'引' if s['quote'] else ''}{s['text'][:22]} | {s['f0']:.0f} | {s['sim_w']:.2f} | {s['sim_p']:.2f} | {len(s['tries'])} | {'✓' if s['ok'] else '✗ ' + ','.join(s.get('bad_keys', []))} |")
print(f"段数 {tot}，一次通过 {first}，最终通过 {ok}/{tot}，重试 {retry} 次；"
      f"音高中位 {statistics.median(f0s):.1f} Hz（范围 {min(f0s):.0f}–{max(f0s):.0f}）\n")
print("| 行 | 片段 | 中位音高 Hz | Whisper | Paraformer | 尝试 | 结果 |\n|---|---|---|---|---|---|---|")
print("\n".join(rows))
