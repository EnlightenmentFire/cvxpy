# 用 whisper 逐句回听，按拼音比对找读错的字（标点、同音字不算错）
import sys, os, re, warnings, numpy as np, soundfile as sf, librosa; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from script import L, tts_text
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
asr = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=2)
han = lambda s: re.findall(r'[一-鿿]', s)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
E = T = 0
for i, l in enumerate(L):
    a, sr = sf.read(f"{ROOT}/audio/lines/{i:03d}.wav"); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    segs, _ = asr.transcribe(a, language='zh', beam_size=5, initial_prompt='以下是普通话的句子。'); hyp = ''.join(s.text for s in segs)
    r = lazy_pinyin(''.join(han(tts_text(l[2])))); h = lazy_pinyin(''.join(han(hyp))); e = ed(r, h); E += e; T += len(r)
    if e / max(1, len(r)) > 0.08 or abs(len(h) - len(r)) > 1: print(i, l[1], '%.2f' % (e / len(r)), '|', l[2], '=>', hyp, flush=True)
print('overall PER %.3f' % (E / T))
