"""由整理好的配音（audio/narr48）的实际时长生成时间线。

用法: python make_timeline.py <work> [out.json]
还没合成出来的句子按字数估算，并在输出里标出。
"""
import json
import os
import sys

import soundfile as sf

import storyboard as sb
from narration import BEATS

work = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else work + '/timeline.json'
EST_CPS = 3.45

durs, missing = {}, []
for bid, text in BEATS:
    p = f'{work}/audio/narr48/{bid}.wav'
    if os.path.exists(p):
        info = sf.info(p)
        durs[bid] = info.frames / info.samplerate
    else:
        durs[bid] = len(sb.hanzi(text)) / EST_CPS
        missing.append(bid)
tl = sb.build_timeline(durs)
tl['missing'] = missing
json.dump(tl, open(out, 'w'), ensure_ascii=False, indent=1)
speech = sum(durs.values())
print('beats %d (missing %d)  speech %.1fs  total %.1fs = %d:%04.1f' % (
    len(durs), len(missing), speech, tl['total'], tl['total'] // 60, tl['total'] % 60))
