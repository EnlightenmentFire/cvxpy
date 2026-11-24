import glob, json, re, sys, numpy as np, soundfile as sf, librosa, parselmouth
from faster_whisper import WhisperModel
L=json.load(open('scripts/lines.json'))
m=WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=4)
from opencc import OpenCC
cc=OpenCC('t2s')
def norm(s): s=cc.convert(s); return re.sub(r'[^一-鿿]','',s)
def cer(a,b):
    d=np.arange(len(b)+1)
    for i,ca in enumerate(a,1):
        p=d.copy(); d[0]=i
        for j,cb in enumerate(b,1): d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(ca!=cb))
    return d[-1]/max(1,len(a))
res={}
files=sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else 'voice/raw_*.wav'))
for f in files:
    k=f.split('raw_')[1].rsplit('_',1)[0]
    y,sr=sf.read(f); yt,_=librosa.effects.trim(y,top_db=38)
    dur=len(yt)/sr
    p=parselmouth.Sound(yt,sr).to_pitch(pitch_floor=60,pitch_ceiling=300).selected_array['frequency']; p=p[p>0]
    segs,_=m.transcribe(librosa.resample(np.asarray(y if y.ndim==1 else y.mean(1),dtype=np.float32),orig_sr=sr,target_sr=16000),language='zh',beam_size=5,initial_prompt='以下是普通话的句子。')
    txt=''.join(s.text for s in segs)
    c=cer(norm(L[k]),norm(txt))
    res[f]=dict(k=k,dur=round(dur,2),cps=round(len(norm(L[k]))/dur,2),f0=round(float(np.median(p)),1),cer=round(c,3),asr=txt)
    print(f, res[f], flush=True)
json.dump(res,open('voice/check.json','w'),ensure_ascii=False,indent=1)
