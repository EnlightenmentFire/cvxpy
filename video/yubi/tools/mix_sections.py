# -*- coding: utf-8 -*-
"""分段核对：每段有旁白时音乐（含音效）比人声低多少 dB、旁白停顿处音乐比人声低多少 dB（按 0.4 秒块，K 加权）。
用法：python tools/mix_sections.py [mix 名=mix]"""
import sys, os, json, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from loud import lufs, blocks
name = sys.argv[1] if len(sys.argv) > 1 else 'mix'
TL = json.load(open(f'{ROOT}/src/timeline.json')); S = TL['secs']; rep = json.load(open(f'{ROOT}/cache/mix_report.json'))[name]
k = 10 ** (rep['loudnorm']['gain_db'] / 20)
v, _ = sf.read(f'{ROOT}/audio/narration.wav'); b, _ = sf.read(f'{ROOT}/audio/{name}_bed.wav'); v *= k; b *= k
vI = lufs(v); t, mv = blocks(v); _, mb = blocks(b); t = t + 0.2
Lv = -0.691 + 10 * np.log10(mv + 1e-12); Lb = -0.691 + 10 * np.log10(mb + 1e-12)
act = Lv > vI - 8; quiet = Lv < vI - 30
print(f'voice {vI:.1f} LUFS   （有旁白时：音乐-人声 中位 / 10%–90%；停顿≥0.4s 处：音乐-人声整体响度 中位）')
for s in ('cold', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'):
    m = (t >= S[s]['start']) & (t < S[s]['end']); d = (Lb - Lv)[m & act]; p = (Lb - vI)[m & quiet & (Lb > -70)]
    print(f'{s:5s} under {np.median(d):6.1f}  ({np.percentile(d, 10):6.1f} … {np.percentile(d, 90):6.1f})   pauses {np.median(p) if len(p) else float("nan"):6.1f}  n={len(p)}')
d = (Lb - Lv)[act]; print(f'ALL   under {np.median(d):6.1f}  ({np.percentile(d, 10):6.1f} … {np.percentile(d, 90):6.1f})')
