# 逐句合成配音（Kokoro-82M v1.1-zh，Apache-2.0）。用法: python tts_kokoro.py <voice> <speed> [ids]
import sys, os, numpy as np, soundfile as sf
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from script import S
from kokoro import KPipeline, KModel
REPO='hexgrad/Kokoro-82M-v1.1-zh'
voice=sys.argv[1]; speed=float(sys.argv[2]); only=set(sys.argv[3].split(',')) if len(sys.argv)>3 else None
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'audio','seg_B'); os.makedirs(OUT,exist_ok=True)
model=KModel(repo_id=REPO).to('cpu').eval(); pipe=KPipeline(lang_code='z',repo_id=REPO,model=model)
for i,c,k,t,tts in S:
    if only and i not in only: continue
    parts=[]
    sp=speed*(0.91 if k=='q' else 1.0)   # 原话句放慢
    for r in pipe(tts or t, voice=voice, speed=sp):
        print(i,'|',r.graphemes,'|',r.phonemes,flush=True); parts.append(r.audio.numpy())
    sf.write(f'{OUT}/{i}.wav',np.concatenate(parts),24000)
print('ALLDONE')
