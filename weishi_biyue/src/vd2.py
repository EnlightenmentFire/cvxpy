import torch, time, soundfile as sf, numpy as np
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
m = Qwen3TTSModel.from_pretrained("models/Qwen3-TTS-12Hz-1.7B-VoiceDesign", dtype=torch.float32, device_map="cpu")
ref = "兵法里有一句老话。一座孤城，被围了几个月，守住它的，往往不是城墙，而是人心。"
jobs = [("四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏快", s) for s in (101, 202)] + \
       [("四十多岁男中音，声音醇厚饱满，音高适中不过低，历史纪录片旁白，凝重克制，语速中等偏快", s) for s in (303, 404, 505)]
for i,(ins,seed) in enumerate(jobs):
    torch.manual_seed(seed); np.random.seed(seed)
    wavs, sr = m.generate_voice_design(text=ref, instruct=ins, language="Chinese")
    sf.write(f"voice/design_{i+3}_s{seed}.wav", wavs[0], sr)
    print("cand", i+3, seed, flush=True)
