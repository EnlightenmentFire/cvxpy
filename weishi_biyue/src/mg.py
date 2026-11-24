import torch, numpy as np, soundfile as sf, time, sys
torch.set_num_threads(4)
from transformers import AutoProcessor, MusicgenForConditionalGeneration
proc = AutoProcessor.from_pretrained("models/musicgen-stereo-medium")
model = MusicgenForConditionalGeneration.from_pretrained("models/musicgen-stereo-medium", torch_dtype=torch.float32)
sr = model.config.audio_encoder.sampling_rate
jobs = [
  ("main", "driving cinematic war percussion, taiko drums, staccato low strings ostinato, chinese xun flute accent, tense, building, D minor, 120 bpm, no vocals", 30.0, [7, 19, 42]),
  ("xun", "solo chinese xun flute, slow mournful phrase, D minor, sparse, ancient, reverb, no drums, no vocals", 8.0, [5]),
  ("end", "huge taiko drum hit then sustained cinematic low strings and brass chord, D minor, epic resolution, no melody, no vocals", 10.0, [3]),
]
which = sys.argv[1:] or [j[0] for j in jobs]
for name, prompt, dur, seeds in jobs:
    if name not in which: continue
    for seed in seeds:
        torch.manual_seed(seed)
        t0 = time.time()
        inp = proc(text=[prompt], padding=True, return_tensors="pt")
        with torch.inference_mode():
            audio = model.generate(**inp, do_sample=True, guidance_scale=3.0, max_new_tokens=int(dur * 50) + 4)
        a = audio[0].cpu().numpy().T
        sf.write(f"music/{name}_s{seed}.wav", a, sr)
        print(name, seed, a.shape, "%.0fs" % (time.time() - t0), flush=True)
