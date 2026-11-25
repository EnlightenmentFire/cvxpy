"""MusicGen (facebook/musicgen-stereo-medium) clips per layer, per 配乐规范 (cold war / suspense).
Batches of 3 (memory-safe), every clip saved immediately; re-running resumes where it stopped."""
import json, os, sys, time, torch, numpy as np, soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.set_num_threads(4)
OUT = os.path.dirname(os.path.abspath(__file__)) + "/clips"
os.makedirs(OUT, exist_ok=True)
LAYERS = [
 ("climax", 3, "epic tragic cinematic orchestral climax, low cellos and double basses, slow heavy taiko drums, dark swelling brass, solemn, building to a huge crescendo, D minor, 70 bpm, no vocals"),
 ("bed", 5, "dark ambient cinematic underscore, deep low drone and sustained low strings, cold war suspense, very sparse and quiet, slow, no drums, no melody, no vocals, D minor, 60 bpm"),
 ("build", 7, "tense cold war submarine thriller underscore, deep low drone with a sparse slow heartbeat-like low kick drum pulse, minimal, restrained, ominous, D minor, 70 bpm, no melody, no vocals"),
 ("ending", 3, "solo cello, slow mournful melody, sparse and quiet, intimate, gentle hall reverb, D minor, 60 bpm, no other instruments, no drums, no vocals"),
 ("post", 8, "sparse melancholic low strings, slow sustained cello and double bass over a soft dark ambient drone, quiet aftermath at sea, solemn, D minor, 60 bpm, no drums, no vocals"),
]
BS = 3
proc = AutoProcessor.from_pretrained("facebook/musicgen-stereo-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-stereo-medium", dtype=torch.bfloat16).eval()
metap = f"{OUT}/../gen_meta.json"
meta = json.load(open(metap)) if os.path.exists(metap) else {}
for name, n, prompt in LAYERS:
    todo = [i for i in range(n) if not os.path.exists(f"{OUT}/{name}_{i}.wav")]
    for b0 in range(0, len(todo), BS):
        idx = todo[b0:b0 + BS]
        torch.manual_seed(1000 + 97 * idx[0] + sum(map(ord, name)))
        t = time.time()
        inputs = proc(text=[prompt] * len(idx), padding=True, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=1503)
        a = out.float().numpy()
        for j, i in enumerate(idx):
            sf.write(f"{OUT}/{name}_{i}.wav", a[j].T, 32000)
        meta.setdefault(name, {"prompt": prompt, "n": n, "batches": []})["batches"].append(
            {"idx": idx, "seconds": round(a.shape[-1] / 32000, 2), "gen_s": round(time.time() - t, 1)})
        json.dump(meta, open(metap, "w"), indent=1)
        print(name, idx, round(time.time() - t, 1), "s", flush=True)
print("ALL DONE", flush=True)
