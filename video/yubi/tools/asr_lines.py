# 逐句语音识别回读（任意逐句音频目录、任意行号），按拼音比对原文
import sys, os, re, warnings, numpy as np, soundfile as sf, librosa; warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
from script import L
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
LD = sys.argv[1]; idx = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else range(len(L))
asr = WhisperModel('small', device='cpu', compute_type='int8')
han = lambda s: re.findall(r'[一-鿿]', s)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
E = T = 0
for i in idx:
    a, sr = sf.read(os.path.join(LD, f'{i:03d}.wav')); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    segs, _ = asr.transcribe(a, language='zh', beam_size=5, initial_prompt='以下是普通话的句子。'); hyp = ''.join(s.text for s in segs)
    r = lazy_pinyin(''.join(han(L[i][2]))); h = lazy_pinyin(''.join(han(hyp))); e = ed(r, h); E += e; T += len(r)
    print(i, L[i][1], '%.2f' % (e / max(1, len(r))), '|', L[i][2], '=>', hyp, flush=True)
print('PER %.3f' % (E / max(1, T)))
