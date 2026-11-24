import sys, time, os
sys.path.insert(0, '/home/user/.venvs/cosyvoice_src'); sys.path.insert(0, '/home/user/.venvs/cosyvoice_src/third_party/Matcha-TTS')
import torch, torchaudio
from cosyvoice.cli.cosyvoice import CosyVoice
cv = CosyVoice('/home/user/.venvs/models/CosyVoice-300M-SFT', load_jit=False, load_trt=False, fp16=False)
print(cv.list_available_spks())
text = sys.argv[1]; out = sys.argv[2]; speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
t = time.time(); chunks = []
for line in text.split('\n'):
    if not line.strip(): continue
    for r in cv.inference_sft(line, '中文男', stream=False, speed=speed):
        chunks.append(r['tts_speech']); chunks.append(torch.zeros(1, int(cv.sample_rate * 0.35)))
w = torch.cat(chunks, dim=1); torchaudio.save(out, w, cv.sample_rate)
print('dur', w.shape[1] / cv.sample_rate, 'gen', time.time() - t)
