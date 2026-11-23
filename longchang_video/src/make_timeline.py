"""由配音文件的实际时长生成时间线。

用法: python make_timeline.py <work> <tempo> [out.json]
tempo: 后期整体变速倍率（1.0 不变）。还没合成出来的句子按字数估算，并在输出里标出。
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

import storyboard as sb
from narration import BEATS

work, tempo = sys.argv[1], float(sys.argv[2])
out = sys.argv[3] if len(sys.argv) > 3 else work + '/timeline.json'


def trim_bounds(y, sr, thr_db=-42.0, pad=0.04):
    """首尾静音裁掉，留一点气口。"""
    win = int(sr * 0.02)
    n = len(y) // win
    rms = np.sqrt((y[:n * win].reshape(n, win) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms / (np.abs(y).max() + 1e-9) + 1e-9)
    idx = np.where(db > thr_db)[0]
    if len(idx) == 0:
        return 0, len(y)
    a = max(int(idx[0] * win - pad * sr), 0)
    b = min(int((idx[-1] + 1) * win + pad * 2.5 * sr), len(y))
    return a, b


durs, missing, clips = {}, [], {}
for bid, text in BEATS:
    p = f'{work}/audio/narr/{bid}.wav'
    if os.path.exists(p):
        y, sr = sf.read(p, dtype='float32')
        a, b = trim_bounds(y, sr)
        durs[bid] = (b - a) / sr / tempo
        clips[bid] = dict(path=p, a=int(a), b=int(b), sr=sr)
    else:
        durs[bid] = len(sb.hanzi(text)) / 3.26 / tempo
        missing.append(bid)
tl = sb.build_timeline(durs)
tl['tempo'] = tempo
tl['clips'] = clips
tl['missing'] = missing
json.dump(tl, open(out, 'w'), ensure_ascii=False, indent=1)
speech = sum(durs.values())
print('beats %d (missing %d)  speech %.1fs  total %.1fs = %d:%04.1f' % (
    len(durs), len(missing), speech, tl['total'], tl['total'] // 60, tl['total'] % 60))
