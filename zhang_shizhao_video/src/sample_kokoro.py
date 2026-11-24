import sys, numpy as np, soundfile as sf
sys.path.insert(0,'/home/user/cvxpy/zhang_shizhao_video/src')
from script import S
from kokoro import KPipeline, KModel
REPO='hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval()
pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)
ids = sys.argv[1].split(','); voice=sys.argv[2]; speed=float(sys.argv[3]); out=sys.argv[4]
D={s[0]:s for s in S}
parts=[]
for i in ids:
    t = D[i][4] or D[i][3]
    for r in pipe(t, voice=voice, speed=speed):
        print(i, r.phonemes)
        parts.append(r.audio.numpy())
    parts.append(np.zeros(int(24000*0.45),dtype=np.float32))
w=np.concatenate(parts); sf.write(out,w,24000); print('ok',len(w)/24000)
