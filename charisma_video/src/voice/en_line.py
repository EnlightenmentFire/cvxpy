import torch, soundfile as sf, sys
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
from pitch import med_f0
m=Qwen3TTSModel.from_pretrained(sys.argv[1], dtype=torch.bfloat16, device_map="cpu", attn_implementation="sdpa")
ins="A tired American businessman in his fifties, low and slightly husky voice, speaking slowly and quietly with a hesitant pause, in a hushed 1970s boardroom."
for seed in [5, 17, 29]:
    torch.manual_seed(seed)
    wavs,sr=m.generate_voice_design(text="What would Walt do?", instruct=ins, language="English", do_sample=True)
    fn=f"en_{seed}.wav"; sf.write(fn,wavs[0],sr); print(seed, round(len(wavs[0])/sr,2), round(med_f0(fn),1), flush=True)
