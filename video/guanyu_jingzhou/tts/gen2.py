# -*- coding: utf-8 -*-
"""以设计出的参考音（ref/C2.wav）为基准，用 Base 模型克隆合成全部旁白；逐段量基频，偏高则换种子重试。"""
import sys, os, time, json, torch, soundfile as sf, numpy as np, parselmouth, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/user/work/vid')
from script import BEATS, say_text
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
REF_TXT="建安二十四年，冬。江陵的城门，从里面打开了。一个人的选择，改变了一个集团的命运。"
prompt = model.create_voice_clone_prompt(ref_audio='ref/C2.wav', ref_text=REF_TXT, x_vector_only_mode=False)
def f0(w,sr):
    s=parselmouth.Sound(w.astype(np.float64),sr); f=s.to_pitch_ac(time_step=0.01,pitch_floor=60,pitch_ceiling=400).selected_array['frequency']; f=f[f>0]
    if len(f)<10: return 999.0, 999.0
    return round(float(np.median(f)),1), round(float(np.percentile(f,90)),1)
only=sys.argv[1:]
st=json.load(open('f0_v2.json')) if os.path.exists('f0_v2.json') else {}
for b in BEATS:
    bid=b['id']; out=f'wav2/{bid}.wav'
    if only and bid not in only: continue
    if os.path.exists(out) and not only: continue
    best=None; t=time.time(); nchar=len([c for c in say_text(b) if '一'<=c<='鿿'])
    for k,seed in enumerate((7,19,31)):
        torch.manual_seed(seed + (int(time.time())%1000 if only else 0))
        wavs,sr=model.generate_voice_clone(text=say_text(b),language="Chinese",voice_clone_prompt=prompt)
        w=wavs[0]; med,p90=f0(w,sr); dur=len(w)/sr; cps=nchar/max(0.1,dur)
        ok = med<=118 and p90<=175 and 2.6<=cps<=6.0
        if best is None or (med+0.3*p90)<(best[1]+0.3*best[2]): best=(w,med,p90,dur,seed)
        if ok: break
    w,med,p90,dur,seed=best
    sf.write(out,w,sr); st[bid]=dict(med=med,p90=p90,dur=round(dur,2),tries=k+1,seed=seed)
    json.dump(st,open('f0_v2.json','w'))
    print('GEN',bid,med,p90,round(dur,2),'cps',round(nchar/dur,2),'tries',k+1,round(time.time()-t),flush=True)
print('ALLDONE2',flush=True)
