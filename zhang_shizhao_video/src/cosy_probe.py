import sys, time
sys.path.insert(0,'/opt/CosyVoice'); sys.path.insert(0,'/opt/CosyVoice/third_party/Matcha-TTS')
import torch, torchaudio
from cosyvoice.cli.cosyvoice import CosyVoice
cv = CosyVoice('/opt/models/CosyVoice-300M-SFT', load_jit=False, load_trt=False, fp16=False)
print(cv.list_available_spks())
text = "一九二六年三月，北京。平政院的一份裁决书上，写着这样一行字：教育部之处分取消之。"
t=time.time()
outs=[o['tts_speech'] for o in cv.inference_sft(text, '中文男', stream=False, speed=1.0)]
w=torch.cat(outs,dim=1)
torchaudio.save('/home/user/cvxpy/zhang_shizhao_video/build/cosy/probe_m.wav', w, cv.sample_rate)
print('dur', w.shape[1]/cv.sample_rate, 'rt', time.time()-t, 'sr', cv.sample_rate)
