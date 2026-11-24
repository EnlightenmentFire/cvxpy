import time, sys, torch, numpy as np, soundfile as sf
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
dtype = torch.bfloat16 if sys.argv[1] == "bf16" else torch.float32
t0 = time.time()
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=dtype, attn_implementation="sdpa")
print("load", round(time.time()-t0,1), flush=True)
instr = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
text = "一九零六年秋天，英国普利茅斯，一个牲畜展览会上，有一个猜牛重量的小比赛。"
torch.manual_seed(1)
t0 = time.time()
wavs, sr = m.generate_voice_design(text=text, instruct=instr, language="Chinese")
el = time.time()-t0
dur = len(wavs[0])/sr
print(f"gen {el:.1f}s audio {dur:.1f}s rtf {el/dur:.2f} sr {sr}", flush=True)
sf.write(sys.argv[2], wavs[0], sr)
