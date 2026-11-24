import sys
sys.path.insert(0,'/home/user/cvxpy/zhang_shizhao_video/src'); sys.path.insert(0,'/opt/CosyVoice'); sys.path.insert(0,'/opt/CosyVoice/third_party/Matcha-TTS')
import torch, torchaudio
from script import S
from cosyvoice.cli.cosyvoice import CosyVoice
cv = CosyVoice('/opt/models/CosyVoice-300M-SFT', load_jit=False, load_trt=False, fp16=False)
ids = sys.argv[1].split(','); out=sys.argv[2]
D={s[0]:s for s in S}
parts=[]
for i in ids:
    t = D[i][4] or D[i][3]
    w=torch.cat([o['tts_speech'] for o in cv.inference_sft(t, '中文男', stream=False, speed=1.0)],dim=1)
    parts += [w, torch.zeros(1,int(cv.sample_rate*0.45))]
torchaudio.save(out, torch.cat(parts,dim=1), cv.sample_rate)
print('ok', sum(p.shape[1] for p in parts)/cv.sample_rate)
