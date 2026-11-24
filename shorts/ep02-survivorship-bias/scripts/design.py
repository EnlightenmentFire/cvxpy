import torch, soundfile as sf, time, sys
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32, attn_implementation="sdpa")
ins = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏快"
ref = "二战的时候，军方统计飞回来的轰炸机，打算在弹孔多的地方加装甲。统计学家的思路正好反过来。"
for i in range(3,6):
    torch.manual_seed(100+i)
    t=time.time()
    w, sr = m.generate_voice_design(text=ref, instruct=ins, language="Chinese", do_sample=True)
    sf.write(f"/tmp/claude-0/-home-user-cvxpy/fe4a820e-e082-5cd9-87f9-b1a5df450d7b/scratchpad/w/voice/design_{i}.wav", w[0], sr)
    print(i, sr, len(w[0])/sr, "s, took", time.time()-t, flush=True)
