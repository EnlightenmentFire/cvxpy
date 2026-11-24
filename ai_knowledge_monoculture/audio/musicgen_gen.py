"""Generate music beds with MusicGen (facebook/musicgen-stereo-medium, transformers).

Per the music spec: each layer is generated as 20-30 s pieces in 2-3 versions, the best one is
picked (least competing with the voice), and long sections are extended by continuation
(the last seconds of the chosen take are fed back as an audio prompt), so key and tempo stay put.

NOTE: the MusicGen weights are licensed CC-BY-NC-4.0 (non-commercial)."""
import argparse
import json
import os
import time

import numpy as np
import soundfile as sf
import torch
from transformers import AutoProcessor, MusicgenForConditionalGeneration

MODEL = "facebook/musicgen-stereo-medium"
SR = 32000
FRAME_RATE = 50


class Gen:
    def __init__(self, threads=4):
        torch.set_num_threads(threads)
        self.proc = AutoProcessor.from_pretrained(MODEL)
        self.model = MusicgenForConditionalGeneration.from_pretrained(MODEL, torch_dtype=torch.bfloat16)
        self.model.audio_encoder.float()      # EnCodec in fp32 for clean decoding
        self.model.eval()

    @torch.no_grad()
    def text(self, prompt, seconds, n=1, seed=0, guidance=3.0, temperature=1.0):
        torch.manual_seed(seed)
        inp = self.proc(text=[prompt] * n, padding=True, return_tensors="pt")
        out = self.model.generate(**inp, do_sample=True, guidance_scale=guidance, temperature=temperature,
                                  top_k=250, max_new_tokens=int(seconds * FRAME_RATE))
        return [o.float().numpy() for o in out]        # each (2, samples)

    @torch.no_grad()
    def continue_(self, prompt, prev, extra_seconds, context_seconds=10.0, seed=0, guidance=3.0):
        """prev: (2, samples) float. Returns prev extended by extra_seconds (crossfade-free, same stream)."""
        torch.manual_seed(seed)
        ctx = prev[:, -int(context_seconds * SR):]
        inp = self.proc(audio=[ctx], sampling_rate=SR, text=[prompt], padding=True, return_tensors="pt")
        out = self.model.generate(**inp, do_sample=True, guidance_scale=guidance, top_k=250,
                                  max_new_tokens=int((context_seconds + extra_seconds) * FRAME_RATE))
        new = out[0].float().numpy()
        new = new[:, ctx.shape[1]:]                       # drop the re-decoded context
        return np.concatenate([prev, new], axis=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="json: [{key, prompt, seconds, versions}]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    plan = json.load(open(a.plan))
    g = Gen(a.threads)
    for item in plan:
        if a.only and item["key"] not in a.only.split(","):
            continue
        nv = item.get("versions", 3)
        paths = [os.path.join(a.out, f"{item['key']}_v{v}.wav") for v in range(nv)]
        if all(os.path.exists(p) for p in paths):
            continue
        t0 = time.time()
        seed = 1000 + sum(map(ord, item["key"]))
        wavs = g.text(item["prompt"], item.get("seconds", 27), nv, seed=seed)    # all versions in one batch
        for p, wav in zip(paths, wavs):
            sf.write(p, wav.T, SR)
        print(json.dumps(dict(key=item["key"], versions=nv, secs=round(wavs[0].shape[1] / SR, 1),
                              gen_s=round(time.time() - t0, 1))), flush=True)
