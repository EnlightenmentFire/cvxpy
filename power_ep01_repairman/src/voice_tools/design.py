import time, sys, torch, soundfile as sf
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
t0 = time.time()
m = Qwen3TTSModel.from_pretrained("models/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.bfloat16)
print("load", time.time()-t0, flush=True)
instruct = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
text = "上世纪五十年代，法国一家国营烟草厂里，组织图上最不起眼的一群人，成了车间里真正说了算的人。"
seeds = [int(s) for s in sys.argv[1:]] or [1]
for seed in seeds:
    torch.manual_seed(seed)
    t1 = time.time()
    wavs, sr = m.generate_voice_design(text=text, language="Chinese", instruct=instruct)
    dur = len(wavs[0])/sr
    print(f"seed {seed}: gen {time.time()-t1:.1f}s for {dur:.1f}s audio", flush=True)
    sf.write(f"voice/design_seed{seed}.wav", wavs[0], sr)
