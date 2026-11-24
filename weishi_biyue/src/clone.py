import torch, soundfile as sf, numpy as np, json, sys, os
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
m = Qwen3TTSModel.from_pretrained("models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
ref_audio = "voice/design_3_s101.wav"
ref_text = "兵法里有一句老话。一座孤城，被围了几个月，守住它的，往往不是城墙，而是人心。"
prompt = m.create_voice_clone_prompt(ref_audio=ref_audio, ref_text=ref_text)
S = json.load(open("sentences.json"))
seeds = [int(s) for s in sys.argv[1].split(",")] if len(sys.argv) > 1 else [1, 2, 3]
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
os.makedirs("voice/sent", exist_ok=True)
for s in S:
    if only and s["id"] not in only: continue
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        wavs, sr = m.generate_voice_clone(text=s["tts"], language="Chinese", voice_clone_prompt=prompt)
        sf.write(f"voice/sent/{s['id']}_s{seed}.wav", wavs[0], sr)
        print(s["id"], seed, len(wavs[0]) / sr, flush=True)
