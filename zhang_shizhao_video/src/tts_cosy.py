# 逐句合成配音（CosyVoice-300M-SFT 内置“中文男”，Apache-2.0）。已存在的句子跳过。
import sys, os
sys.path.insert(0,'/home/user/cvxpy/zhang_shizhao_video/src'); sys.path.insert(0,'/opt/CosyVoice'); sys.path.insert(0,'/opt/CosyVoice/third_party/Matcha-TTS')
import torch, torchaudio
from script import S
from cosyvoice.cli.cosyvoice import CosyVoice
OUT='/home/user/cvxpy/zhang_shizhao_video/audio/seg_A'; os.makedirs(OUT,exist_ok=True)
SPEED=float(os.environ.get('SPEED','1.1'))
only=set(sys.argv[1].split(',')) if len(sys.argv)>1 else None
cv = CosyVoice('/opt/models/CosyVoice-300M-SFT', load_jit=False, load_trt=False, fp16=False)
for i,c,k,t,tts in S:
    f=f'{OUT}/{i}.wav'
    if only is None and os.path.exists(f): continue
    if only is not None and i not in only: continue
    torch.manual_seed(1234+hash(i)%1000 if only is None else int.from_bytes(os.urandom(2),'big'))
    w=torch.cat([o['tts_speech'] for o in cv.inference_sft(tts or t, '中文男', stream=False, speed=SPEED)],dim=1)
    torchaudio.save(f, w, cv.sample_rate); print('DONE',i,round(w.shape[1]/cv.sample_rate,2),flush=True)
print('ALLDONE')
