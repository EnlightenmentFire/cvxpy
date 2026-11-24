# -*- coding: utf-8 -*-
"""把某一句的音频在句内停顿处切成两句，其后的编号整体顺延一位（用于在两句之间插入留白）。
用法：python tools/split_line.py 目录 行号 切点秒数（取该停顿的中点）"""
import sys, os, json, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from qwen_clone_utils import trim
d, i, cut = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
files = sorted(int(f[:3]) for f in os.listdir(d) if f.endswith('.wav') and f[:3].isdigit())
for k in reversed([k for k in files if k > i]): os.rename(f'{d}/{k:03d}.wav', f'{d}/{k + 1:03d}.wav')
w, sr = sf.read(f'{d}/{i:03d}.wav'); w = w.astype(np.float32); c = int(cut * sr)
a, b = trim(w[:c], sr), trim(w[c:], sr)
sf.write(f'{d}/{i:03d}.wav', a, sr, subtype='PCM_16'); sf.write(f'{d}/{i + 1:03d}.wav', b, sr, subtype='PCM_16')
lp = f'{d}/qwen_log.json'
if os.path.exists(lp):
    log = json.load(open(lp)); new = {}
    for k, v in log.items():
        k = int(k); new[str(k + 1 if k > i else k)] = v
    new[str(i)] = dict(log[str(i)], split='前半'); new[str(i + 1)] = dict(log[str(i)], split='后半（原句切开）')
    json.dump(new, open(lp, 'w'), ensure_ascii=False, indent=0)
print(d, i, 'split at', cut, '->', round(len(a) / sr, 2), round(len(b) / sr, 2))
