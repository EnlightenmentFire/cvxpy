import torch, time, soundfile as sf, numpy as np, sys
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
t0=time.time()
m = Qwen3TTSModel.from_pretrained("models/Qwen3-TTS-12Hz-1.7B-VoiceDesign", dtype=torch.float32, device_map="cpu")
print("load", time.time()-t0, flush=True)
instruct = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏快"
ref = "兵法里有一句老话。一座孤城，被围了几个月，守住它的，往往不是城墙，而是人心。"
for i, seed in enumerate([11, 23, 37]):
    torch.manual_seed(seed); np.random.seed(seed)
    t0=time.time()
    wavs, sr = m.generate_voice_design(text=ref, instruct=instruct, language="Chinese")
    sf.write(f"voice/design_{i}_s{seed}.wav", wavs[0], sr)
    print("cand", i, seed, len(wavs[0])/sr, "sec, took", time.time()-t0, flush=True)
