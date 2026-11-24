# -*- coding: utf-8 -*-
"""成片混音后整体回读：按时间轴把每句的时间窗从混音里切出来，用 faster-whisper 识别，按拼音比对原文，算误读率（PER）。
可加 phone 参数模拟手机外放（单声道，300 Hz 以下和 7 kHz 以上滤掉）。
用法：python tools/asr_mix.py 混音.wav [phone]  → 打印总 PER 和读错的句子"""
import sys, os, re, json, warnings, numpy as np, soundfile as sf, librosa; warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(ROOT, 'src'))
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
TL = json.load(open(os.path.join(ROOT, 'src', 'timeline.json')))
han = lambda s: re.findall(r'[一-鿿]', s)
D = '零一二三四五六七八九'


def num2cn(n):
    if n < 10: return D[n]
    if n < 20: return '十' + (D[n % 10] if n % 10 else '')
    if n < 100: return D[n // 10] + '十' + (D[n % 10] if n % 10 else '')
    if n < 1000: return D[n // 100] + '百' + ('' if n % 100 == 0 else ('零' + D[n % 10] if n % 100 < 10 else (num2cn(n % 100) if n % 100 >= 20 else '一' + num2cn(n % 100))))
    return ''.join(D[int(c)] for c in str(n))


def cn_digits(s):
    """识别结果里的阿拉伯数字按读法换回汉字（“公元572年”→“公元五七二年”，“50天”→“五十天”），只为公平比对。"""
    s = re.sub(r'(?<=公元)(\d+)', lambda m: ''.join(D[int(c)] for c in m.group(1)), s)
    return re.sub(r'\d+', lambda m: num2cn(int(m.group(0))), s)


def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]


w, sr = sf.read(sys.argv[1]); w = w.mean(1) if w.ndim == 2 else w
if 'phone' in sys.argv:
    X = np.fft.rfft(w); f = np.fft.rfftfreq(len(w), 1 / sr)
    X *= 1 / np.sqrt(1 + (300 / np.maximum(f, 1e-3)) ** 8) / np.sqrt(1 + (f / 7000) ** 8); w = np.fft.irfft(X, len(w))
w16 = librosa.resample(w.astype(np.float32), orig_sr=sr, target_sr=16000)
asr = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=int(os.environ.get('ASR_THREADS', '4')))
E = T = 0; bad = []
for l in TL['lines']:
    a = w16[int((l['start'] - 0.1) * 16000): int((l['end'] + 0.15) * 16000)]
    segs, _ = asr.transcribe(a, language='zh', beam_size=5, initial_prompt='以下是普通话的句子。', condition_on_previous_text=False)
    hyp = cn_digits(''.join(s.text for s in segs)); r = lazy_pinyin(''.join(han(l['text']))); h = lazy_pinyin(''.join(han(hyp))); e = ed(r, h); E += e; T += len(r)
    if e: bad.append((l['i'], e, l['text'], hyp))
for b in bad: print(b[0], b[1], '|', b[2], '=>', b[3])
print(os.path.basename(sys.argv[1]), 'phone' if 'phone' in sys.argv else '', 'PER %.4f  (%d/%d)' % (E / T, E, T))
