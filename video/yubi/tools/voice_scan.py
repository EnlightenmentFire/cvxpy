# 用同一句话试全部男声：量基频（中位数/90分位）与语速，并用 whisper 回检读音错误率
import sys, os, re, warnings, numpy as np, soundfile as sf, json; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from script import L, tts_text
import torch; torch.set_num_threads(4)
from kokoro import KPipeline, KModel
import parselmouth, librosa
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)
asr = WhisperModel('small', device='cpu', compute_type='int8')
han = lambda s: re.findall(r'[一-鿿]', s)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
out = sys.argv[1]; os.makedirs(out, exist_ok=True); voices = sys.argv[2].split(','); idx = [int(x) for x in sys.argv[3].split(',')]
res = {}
for v in voices:
    f0s = []; err = tot = 0; dur = 0; nch = 0
    for i in idx:
        t = tts_text(L[i][2]); a = np.concatenate([r.audio.numpy() for r in pipe(t, voice=v, speed=1.3)])
        sf.write(f'{out}/{v}_{i}.wav', a, 24000); dur += len(a) / 24000; nch += len(han(t))
        snd = parselmouth.Sound(a.astype(np.float64), 24000); f = snd.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=400).selected_array['frequency']; f0s += list(f[f > 0])
        segs, _ = asr.transcribe(librosa.resample(a.astype(np.float32), orig_sr=24000, target_sr=16000), language='zh', beam_size=3, initial_prompt='以下是普通话的句子。')
        hyp = ''.join(s.text for s in segs); r = lazy_pinyin(''.join(han(t))); h = lazy_pinyin(''.join(han(hyp))); err += ed(r, h); tot += len(r)
    f0s = np.array(f0s); res[v] = dict(med=round(float(np.median(f0s)), 1), p90=round(float(np.percentile(f0s, 90)), 1), p10=round(float(np.percentile(f0s, 10)), 1), per=round(err / tot, 3), cps=round(nch / dur, 2))
    print(v, res[v], flush=True)
json.dump(res, open(f'{out}/scan.json', 'w'), indent=1)
