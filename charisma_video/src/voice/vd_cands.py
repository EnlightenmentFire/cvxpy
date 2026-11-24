import time, torch, soundfile as sf, sys
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
from pitch import med_f0
m=Qwen3TTSModel.from_pretrained(sys.argv[1], dtype=torch.bfloat16, device_map="cpu", attn_implementation="sdpa")
ins="四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
ref="一九一九年一月，德国刚刚战败。慕尼黑，一位五十四岁的教授站在一群大学生面前，问了一个很老的问题：人，为什么会服从别人？"
for seed in [11,23,37,41,59,73]:
    torch.manual_seed(seed)
    wavs,sr=m.generate_voice_design(text=ref, instruct=ins, language="Chinese", do_sample=True)
    fn=f"cand_{seed}.wav"; sf.write(fn,wavs[0],sr)
    print(seed, round(len(wavs[0])/sr,2), "f0", round(med_f0(fn),1), flush=True)
