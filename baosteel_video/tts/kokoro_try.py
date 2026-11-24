import sys, os, numpy as np, soundfile as sf, torch, time
from kokoro import KPipeline, KModel
REPO='hexgrad/Kokoro-82M-v1.1-zh'
model=KModel(repo_id=REPO).eval()
pipe=KPipeline(lang_code='z', repo_id=REPO, model=model)
text=sys.argv[1]; out=sys.argv[2]; voices=sys.argv[3].split(','); speed=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
os.makedirs(out,exist_ok=True)
for v in voices:
    t=time.time(); wavs=[]
    for r in pipe(text, voice=v, speed=speed, split_pattern=r'\n+'):
        wavs.append(r.audio.numpy()); wavs.append(np.zeros(int(24000*0.35),dtype=np.float32))
    w=np.concatenate(wavs); sf.write(f'{out}/{v}.wav', w, 24000)
    print(v, f'{len(w)/24000:.1f}s', f'gen {time.time()-t:.1f}s', flush=True)
