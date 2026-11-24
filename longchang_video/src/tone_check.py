"""多音字的声调核对：用 Whisper 的逐字时间戳定位，再量这个字的基频走向。

升调（二声）/ 降调（四声）/ 高平（一声）/ 低（三声）一看便知，
可以分辨 重 chóng/zhòng、朝 cháo/zhāo、长 zhǎng/cháng、着 zháo/zhe、教 jiāo/jiào。
用法: python tone_check.py <work> id:字[:第几次出现] ...
"""
import sys

import librosa
import numpy as np
import whisper

work = sys.argv[1]
asr = whisper.load_model('medium')
for spec in sys.argv[2:]:
    parts = spec.split(':')
    bid, ch = parts[0], parts[1]
    nth = int(parts[2]) if len(parts) > 2 else 0
    path = f'{work}/audio/narr/{bid}.wav'
    r = asr.transcribe(path, language='zh', initial_prompt='以下是普通话的句子。', fp16=False, word_timestamps=True)
    words = [w for s in r['segments'] for w in s['words']]
    y, sr = librosa.load(path, sr=16000)
    f0, vf, _ = librosa.pyin(y, fmin=55, fmax=320, sr=sr, frame_length=1024, hop_length=160)
    med = np.nanmedian(f0)
    # 逐字展开（一个 word 可能含多个字，按字数均分时间）
    chars = []
    for w in words:
        txt = ''.join(c for c in w['word'] if '一' <= c <= '鿿')
        for i, c in enumerate(txt):
            d = (w['end'] - w['start']) / max(len(txt), 1)
            chars.append((c, w['start'] + i * d, w['start'] + (i + 1) * d))
    hits = [x for x in chars if x[0] == ch]
    if len(hits) <= nth:
        print(spec, 'NOT FOUND in', ''.join(c for c, _, _ in chars))
        continue
    c, a, b = hits[nth]
    i0, i1 = int(a * 100), int(b * 100) + 1
    seg = f0[i0:i1]
    v = seg[~np.isnan(seg)]
    if len(v) < 4:
        print(spec, 'too few voiced frames', len(v))
        continue
    st = 12 * np.log2(v / med)
    k = max(len(st) // 3, 1)
    head, mid, tail = st[:k].mean(), st[k:-k].mean() if len(st) > 2 * k else st.mean(), st[-k:].mean()
    shape = 'rising' if tail - head > 1.5 else ('falling' if tail - head < -1.5 else ('high-level' if st.mean() > 1.0 else 'low/level'))
    ctx = ''.join(x[0] for x in chars)
    print('%-10s %s  %.2f-%.2fs  head %+.1f mid %+.1f tail %+.1f st (rel. median)  -> %s   | %s' % (spec, c, a, b, head, mid, tail, shape, ctx))
