"""MusicGen (facebook/musicgen-stereo-medium) clips per layer, per 配乐规范 (cold war / suspense).
Jobs are batched 3 at a time across layers (memory-safe, full batches); every clip is saved
immediately, so re-running resumes where it stopped."""
import json, os, sys, time, torch, numpy as np, soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.set_num_threads(4)
# run from the scratchpad musicgen/ folder (clips are not kept in the repo)
OUT = os.path.dirname(os.path.abspath(__file__)) + "/clips"
os.makedirs(OUT, exist_ok=True)
LAYERS = [
 # 高潮: full orchestra for the hypothetical segment
 ("climax", 3, "epic tragic cinematic orchestral climax, low cellos and double basses, slow heavy taiko drums, dark swelling brass, solemn, building to a huge crescendo, D minor, 70 bpm, no vocals"),
 # 铺底: long tones / pads only
 ("bed", 5, "dark ambient cinematic underscore, deep low drone and sustained low strings, cold war suspense, very sparse and quiet, slow, no drums, no melody, no vocals, D minor, 60 bpm"),
 # 推进 (part 1, dive -> sonar): tension, still no drums
 # (4 clips first; 3 more once the drum prompts were dropped: tension now runs dive -> launch)
 ("tension", 7, "tense cold war submarine thriller underscore, deep low drone, slow tremolo low strings, ominous and restrained, slowly rising tension, no drums, no percussion, no melody, no vocals, D minor, 70 bpm"),
 # 推进 (part 2, sonar -> launch): the sparse heartbeat-like low drum comes in
 ("build", 3, "tense cold war submarine thriller underscore, deep low drone with a sparse slow heartbeat-like low kick drum pulse, minimal, restrained, ominous, no melody, no vocals, D minor, 60 bpm"),
 # the first build prompt gave drones without an audible drum: ask for the drum explicitly
 ("drum", 6, "dark cinematic suspense underscore, steady slow pulsing heartbeat rhythm played on deep low drums, thumping sub bass hits, ominous low drone underneath, minimal, no melody, no vocals, D minor, 60 bpm"),
 # 收尾: a single instrument
 ("ending", 3, "solo cello, slow mournful melody, sparse and quiet, intimate, gentle hall reverb, D minor, 60 bpm, no other instruments, no drums, no vocals"),
 # 变稀: after the climax, thinner low strings
 ("post", 8, "sparse melancholic low strings, slow sustained cello and double bass over a soft dark ambient drone, quiet aftermath at sea, solemn, D minor, 60 bpm, no drums, no vocals"),
]
BS = 3
jobs = [(name, i, prompt) for name, n, prompt in LAYERS for i in range(n)
        if not os.path.exists(f"{OUT}/{name}_{i}.wav")]
print("todo", len(jobs), flush=True)
if not jobs:
    print("ALL DONE", flush=True); sys.exit(0)
proc = AutoProcessor.from_pretrained("facebook/musicgen-stereo-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-stereo-medium", dtype=torch.bfloat16).eval()
metap = f"{OUT}/../gen_meta.json"
meta = json.load(open(metap)) if os.path.exists(metap) else {}
for b0 in range(0, len(jobs), BS):
    batch = jobs[b0:b0 + BS]
    name0, i0, _ = batch[0]
    torch.manual_seed(1000 + 97 * i0 + sum(map(ord, name0)))
    t = time.time()
    inputs = proc(text=[p for _, _, p in batch], padding=True, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=1503)
    a = out.float().numpy()
    for j, (name, i, prompt) in enumerate(batch):
        sf.write(f"{OUT}/{name}_{i}.wav", a[j].T, 32000)
        m = meta.setdefault(name, {"prompt": prompt, "clips": {}})
        m["prompt"] = prompt
        m.setdefault("clips", {})[str(i)] = {"seconds": round(a.shape[-1] / 32000, 2), "batch": [f"{n}_{k}" for n, k, _ in batch],
                                             "seed": 1000 + 97 * i0 + sum(map(ord, name0)), "gen_s": round(time.time() - t, 1)}
    json.dump(meta, open(metap, "w"), indent=1)
    print([f"{n}_{k}" for n, k, _ in batch], round(time.time() - t, 1), "s", flush=True)
print("ALL DONE", flush=True)
