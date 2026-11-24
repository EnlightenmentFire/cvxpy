# -*- coding: utf-8 -*-
"""MusicGen (facebook/musicgen-stereo-medium) helpers: text-only clips and audio-prompted continuation."""
import os, sys, time, json
import numpy as np, torch, soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration

SR_MG = 32000
TOK_PER_S = 50

PROMPTS = {
    # 思想类：钢琴 + 柔和弦乐 pad，温暖、安静，像在书房里听人讲
    "L1": "soft warm strings pad with sustained long notes and a few sparse piano notes, reflective, calm, quiet, slow, intimate, D minor, no drums, no vocals",
    "L2": "warm piano with soft strings pad, gentle steady pulse, soft low percussion, thoughtful, slowly building, moving forward, D minor, 76 bpm, no vocals",
    "L3": "full warm orchestra, piano and lush strings, soft timpani, emotional swell, hopeful yet solemn, cinematic, no vocals",
    "COLD": "cold sparse quiet strings pad, still, suspended, sustained long notes, no melody, no drums, no vocals",
    "OUT": "solo piano, sparse, slow, gentle ending, long reverb, reflective, no drums, no vocals",
}

class MG:
    def __init__(self, path, threads=4):
        torch.set_num_threads(threads)
        self.proc = AutoProcessor.from_pretrained(path)
        self.model = MusicgenForConditionalGeneration.from_pretrained(path, torch_dtype=torch.bfloat16).eval()

    def gen(self, prompt, seconds, seed, audio_prompt=None, guidance=3.0):
        torch.manual_seed(seed)
        if audio_prompt is None:
            inp = self.proc(text=[prompt], padding=True, return_tensors="pt")
            n_prompt = 0
        else:
            ap = np.asarray(audio_prompt, np.float32)          # (2, n)
            inp = self.proc(audio=[ap], sampling_rate=SR_MG, text=[prompt], padding=True, return_tensors="pt")
            inp["input_values"] = inp["input_values"].to(torch.bfloat16)
            n_prompt = ap.shape[-1]
        with torch.inference_mode():
            out = self.model.generate(**inp, do_sample=True, guidance_scale=guidance,
                                      max_new_tokens=int(seconds * TOK_PER_S))
        a = out[0].float().numpy()
        if a.ndim == 1:
            a = np.stack([a, a])
        return a[:, n_prompt:] if n_prompt else a

def save(path, a):
    sf.write(path, a.T, SR_MG)

if __name__ == "__main__":
    # candidates: python mg.py cand <model> <out_dir> <layer> <seconds> <seed1,seed2,...>
    mode = sys.argv[1]
    if mode == "cand":
        model, out, layer, secs, seeds = sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6]
        os.makedirs(out, exist_ok=True)
        mg = MG(model, int(os.environ.get("MG_THREADS", "4")))
        for sd in [int(x) for x in seeds.split(",")]:
            t = time.time()
            a = mg.gen(PROMPTS[layer], secs, sd)
            save(os.path.join(out, f"{layer}_seed{sd}.wav"), a)
            print(f"{layer} seed{sd} {a.shape[-1]/SR_MG:.1f}s in {time.time()-t:.0f}s", flush=True)

def gen_batch(mg, prompts, audio_prompts, seconds, seed, guidance=3.0):
    """Batched continuation: all audio prompts must have equal length. Returns list of (2, n) new audio."""
    torch.manual_seed(seed)
    aps = [np.asarray(a, np.float32) for a in audio_prompts]
    n_prompt = aps[0].shape[-1]
    inp = mg.proc(audio=aps, sampling_rate=SR_MG, text=prompts, padding=True, return_tensors="pt")
    inp["input_values"] = inp["input_values"].to(torch.bfloat16)
    with torch.inference_mode():
        out = mg.model.generate(**inp, do_sample=True, guidance_scale=guidance, max_new_tokens=int(seconds * TOK_PER_S))
    res = []
    for i in range(len(prompts)):
        a = out[i].float().numpy()
        res.append(a[:, n_prompt:])
    return res
