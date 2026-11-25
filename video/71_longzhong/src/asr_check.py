# -*- coding: utf-8 -*-
"""ASR 回读（faster-whisper large-v3-turbo）：逐句按无调拼音比对稿子，并用词级时间戳对齐字幕分块。
输出 tts/asr.json（每句识别结果与拼音错误率）、tts/align.json（每句各字幕块起点，相对句首秒）。
usage: python asr_check.py [ids...]
"""
import sys, os, re, json, difflib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from timeline import chunks, PROC, W
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import opencc

_cc = opencc.OpenCC('t2s')
NUM = dict(zip('0123456789', '零一二三四五六七八九'))
def norm(s): return re.sub(r'[^一-鿿]', '', ''.join(NUM.get(c, c) for c in _cc.convert(s)))


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]; dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
    return dp[-1]


def main():
    ids = sys.argv[1:]
    m = WhisperModel(f'{W}/models/fw-large-v3-turbo', device='cpu', compute_type='int8', cpu_threads=4)
    asr = json.load(open(f'{W}/tts/asr.json')) if os.path.exists(f'{W}/tts/asr.json') else {}
    al = json.load(open(f'{W}/tts/align.json')) if os.path.exists(f'{W}/tts/align.json') else {}
    for d in all_lines():
        if ids and d['id'] not in ids: continue
        p = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(p): continue
        x, sr = sf.read(p); x = resample_poly(x, 1, 3).astype(np.float32)
        segs, _ = m.transcribe(x, language='zh', beam_size=5, word_timestamps=True, vad_filter=False,
                               initial_prompt='以下是普通话的句子。刘备，诸葛亮，隆中对，裴松之，魏略，出师表，荆州，益州。')
        chars = []      # (字, 起点秒)
        for s in segs:
            for w in s.words:
                cs = norm(w.word)
                for k, ch in enumerate(cs):
                    chars.append((ch, w.start + (w.end - w.start) * k / max(1, len(cs))))
        hyp = ''.join(c for c, _ in chars)
        ref = norm(d['say'])
        a, b = lazy_pinyin(ref), lazy_pinyin(hyp)
        per = edit(a, b) / max(1, len(a))
        asr[d['id']] = dict(hyp=hyp, per=round(per, 3))
        flag = 'OK ' if per <= 0.08 else 'BAD'
        print(f"{flag} {d['id']} PER={per:.2f}" + ('' if per <= 0.08 else f"\n   want {ref}\n   got  {hyp}"), flush=True)
        # 字幕块对齐（按拼音序列匹配）
        if not d['nosub'] and chars:
            ch = chunks(d['sub'])
            sub_norm = norm(d['sub']); sp = lazy_pinyin(sub_norm)
            sm = difflib.SequenceMatcher(None, sp, b, autojunk=False)
            mp = {}
            for blk in sm.get_matching_blocks():
                for k in range(blk.size): mp[blk.a + k] = blk.b + k
            starts = []; pos = 0
            for c_ in ch:
                n = len(norm(c_))
                j = next((mp[i] for i in range(pos, pos + max(1, n)) if i in mp), None)
                starts.append(None if j is None else max(0.0, chars[j][1] - 0.08))
                pos += n
            starts[0] = 0.0
            # 缺失的按前后插值；保证单调
            for i in range(1, len(starts)):
                if starts[i] is None or starts[i] <= starts[i - 1]:
                    starts[i] = None
            known = [(i, v) for i, v in enumerate(starts) if v is not None]
            dur = sf.info(p).duration
            for i in range(len(starts)):
                if starts[i] is None:
                    lo = max([k for k in known if k[0] < i], default=(0, 0.0)); hi = min([k for k in known if k[0] > i], default=(len(starts), dur))
                    starts[i] = lo[1] + (hi[1] - lo[1]) * (i - lo[0]) / (hi[0] - lo[0])
            al[d['id']] = [round(v, 3) for v in starts]
    json.dump(asr, open(f'{W}/tts/asr.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(al, open(f'{W}/tts/align.json', 'w'), ensure_ascii=False, indent=1)
    bad = [k for k, v in asr.items() if v['per'] > 0.08]
    print('BAD:', ' '.join(bad))


if __name__ == '__main__':
    main()
