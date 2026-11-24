import sys, os, warnings; warnings.filterwarnings("ignore")
import numpy as np, soundfile as sf
sys.argv=[sys.argv[0]]
from kokoro import KModel, KPipeline
from script import LINES, tts_text
REPO='hexgrad/Kokoro-82M-v1.1-zh'; SR=24000
_en=KPipeline(lang_code='a', repo_id=REPO, model=False)
model=KModel(repo_id=REPO).eval()
zh=KPipeline(lang_code='z', repo_id=REPO, model=model, en_callable=lambda t: next(_en(t)).phonemes)
def trim(w,thr=0.012,pad=0.05):
    idx=np.where(np.abs(w)>thr)[0]; return w[max(0,idx[0]-int(pad*SR)):idx[-1]+int(pad*SR)]
pick=[0,1,2,3,18,30,32,91]
for v in ['zm_011','zm_033','zm_098']:
    out=[]
    for i in pick:
        t=tts_text(LINES[i][1],LINES[i][2])
        w=trim(np.concatenate([r.audio.numpy() for r in zh(t,voice=v,speed=1.08)]))
        out+= [w, np.zeros(int((0.7 if i in (3,18) else 0.32)*SR),dtype=np.float32)]
    w=np.concatenate(out); w=w/np.abs(w).max()*0.89
    sf.write(f'../samples/voice_{v}.wav', w, SR); print(v, round(len(w)/SR,1))
