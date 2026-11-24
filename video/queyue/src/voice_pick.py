import sys, os, re, warnings, numpy as np, soundfile as sf; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text
from kokoro import KPipeline, KModel
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
REPO='hexgrad/Kokoro-82M-v1.1-zh'
model=KModel(repo_id=REPO).to('cpu').eval(); pipe=KPipeline(lang_code='z', repo_id=REPO, model=model)
asr=WhisperModel('small', device='cpu', compute_type='int8')
idx=[1,9,19,39,58]
han=lambda s: re.findall(r'[一-鿿]', s)
def ed(a,b):
    d=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        p=d[:]; d[0]=i
        for j,y in enumerate(b,1): d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(x!=y))
    return d[-1]
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for v in sys.argv[2:]:
    err=tot=0; dur=0
    for i in idx:
        t=tts_text(L[i][2]); a=np.concatenate([r.audio.numpy() for r in pipe(t, voice=v, speed=1.0)])
        p=f'{out}/{v}_{i}.wav'; sf.write(p,a,24000); dur+=len(a)/24000
        import librosa; segs,_=asr.transcribe(librosa.resample(a.astype(np.float32), orig_sr=24000, target_sr=16000), language='zh', beam_size=3); hyp=''.join(s.text for s in segs)
        r=lazy_pinyin(''.join(han(t))); h=lazy_pinyin(''.join(han(hyp))); err+=ed(r,h); tot+=len(r)
    print(v, 'PER=%.3f'%(err/tot), 'dur=%.1f'%dur, flush=True)
