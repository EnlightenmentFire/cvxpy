"""成片声音终检：从 MP4 里抽出音轨，整轨语音识别，与脚本按拼音逐字比对。

用法: python qc_audio.py <video.mp4> <work_dir>
"""
import re
import subprocess
import sys

import numpy as np
import whisper
from pypinyin import lazy_pinyin

from narration import BEATS

video, work = sys.argv[1], sys.argv[2]
wav = work + '/out/qc_audio.wav'
subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', video, '-vn', '-ac', '1', '-ar', '16000', wav],
               stdin=subprocess.DEVNULL, check=True)
m = whisper.load_model('medium')
r = m.transcribe(wav, language='zh', initial_prompt='以下是普通话的句子。', fp16=False, condition_on_previous_text=False)
hz = lambda s: re.sub(r'[^一-鿿]', '', s)
hyp = ''.join(s['text'] for s in r['segments'])
try:
    import cn2an
    hyp = cn2an.transform(hyp, 'an2cn')
except Exception:
    pass
ref = ''.join(t for _, t in BEATS)
canon = lambda seq: ['long' if x == 'nong' else x for x in seq]
R, Hh = hz(ref), hz(hyp)
a, b = canon(lazy_pinyin(R)), canon(lazy_pinyin(Hh))
n, mm = len(a), len(b)
dp = np.zeros((n + 1, mm + 1), np.int32)
dp[:, 0] = np.arange(n + 1)
dp[0, :] = np.arange(mm + 1)
for i in range(1, n + 1):
    sub = dp[i - 1, :-1] + (np.array(b) != a[i - 1])
    best = np.minimum(dp[i - 1, 1:] + 1, sub)
    row = dp[i]
    for j in range(1, mm + 1):
        row[j] = min(best[j - 1], row[j - 1] + 1)
print('ref syllables %d, hyp %d, edit distance %d = %.2f%%' % (n, mm, dp[n, mm], 100.0 * dp[n, mm] / n), flush=True)
i, j, ops = n, mm, []
while i > 0 or j > 0:
    if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (a[i - 1] != b[j - 1]):
        if a[i - 1] != b[j - 1]:
            ops.append(('sub', i - 1, j - 1))
        i, j = i - 1, j - 1
    elif i > 0 and dp[i, j] == dp[i - 1, j] + 1:
        ops.append(('del', i - 1, j))
        i -= 1
    else:
        ops.append(('ins', i, j - 1))
        j -= 1
for op, i, j in ops[::-1]:
    print('  %s  ref[%s] | hyp[%s]' % (op, R[max(i - 6, 0):i + 7], Hh[max(j - 6, 0):j + 7]))
segs = r['segments']
print('first speech %.2fs, last speech ends %.2fs' % (segs[0]['start'], segs[-1]['end']), flush=True)
