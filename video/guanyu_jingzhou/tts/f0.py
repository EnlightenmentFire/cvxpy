import librosa, numpy as np, json, sys, os, warnings
warnings.filterwarnings('ignore')
def f0stat(p):
    y,sr=librosa.load(p,sr=16000); f,v,_=librosa.pyin(y,fmin=60,fmax=380,sr=sr,frame_length=1024); f=f[v]
    if len(f)==0: return None
    return dict(med=round(float(np.median(f)),1), p90=round(float(np.percentile(f,90)),1), dur=round(len(y)/sr,2))
if __name__=='__main__':
    sys.path.insert(0,'/home/user/work/vid')
    from script import BEATS
    out={}
    for b in BEATS:
        out[b['id']]=f0stat(f"wav/{b['id']}.wav")
    json.dump(out,open('f0_v1.json','w'))
    meds=[v['med'] for v in out.values()]
    print('median of medians',np.median(meds),'min',min(meds),'max',max(meds))
    print(' '.join(f"{k}:{int(v['med'])}" for k,v in out.items()))
    print('<=140:',sum(m<=140 for m in meds),' 140-170:',sum(140<m<=170 for m in meds),' >170:',sum(m>170 for m in meds))
