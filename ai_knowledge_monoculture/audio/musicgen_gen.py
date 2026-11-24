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
    def continue_(self, prompt, prev, extra_seconds, context_seconds=8.0, seed=0, guidance=3.0, overlap=0.5):
        """prev: (2, samples). Feed the last context_seconds back as an audio prompt and append
        extra_seconds of new music in the same key/tempo. The model returns the re-decoded context
        followed by the new audio; the seam is crossfaded over `overlap` seconds."""
        torch.manual_seed(seed)
        n_ctx = int(context_seconds * SR)
        ctx = prev[:, -n_ctx:]
        inp = self.proc(audio=[ctx], sampling_rate=SR, text=[prompt], padding=True, return_tensors="pt")
        out = self.model.generate(**inp, do_sample=True, guidance_scale=guidance, top_k=250,
                                  max_new_tokens=int(extra_seconds * FRAME_RATE))
        full = out[0].float().numpy()            # re-decoded context + continuation
        n_ov = int(overlap * SR)
        a = prev[:, -n_ov:]
        b = full[:, n_ctx - n_ov:n_ctx]
        t = np.linspace(0, np.pi / 2, n_ov)[None, :]
        seam = a * np.cos(t) + b * np.sin(t)
        return np.concatenate([prev[:, :-n_ov], seam, full[:, n_ctx:]], axis=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True, help="json: [{key, prompt, seconds, versions}]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--extend", default="", help="comma list of piece keys to extend by continuation")
    ap.add_argument("--extend-seconds", type=float, default=20.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    plan = json.load(open(a.plan))
    g = Gen(a.threads)
    if a.extend:
        # extend the chosen take of each piece in its own key/tempo (continuation), update choices.json
        cpath = os.path.join(a.out, "choices.json")
        choices = json.load(open(cpath))
        prompts = {p["key"]: p["prompt"] for p in plan}
        for spec in a.extend.split(","):
            key, times = (spec.split(":") + ["1"])[:2]
            files = choices[key] if isinstance(choices[key], list) else [choices[key]]
            src = files[0]
            dst = f"{key}_ext.wav"
            if os.path.exists(os.path.join(a.out, dst)):
                continue
            t0 = time.time()
            w, sr = sf.read(os.path.join(a.out, src), dtype="float32")
            ext = w.T
            for k in range(int(times)):
                ext = g.continue_(prompts[key], ext, a.extend_seconds, context_seconds=8.0, seed=77 + k)
            sf.write(os.path.join(a.out, dst), ext.T, SR)
            choices[key] = [dst]
            json.dump(choices, open(cpath, "w"), indent=1)
            print(json.dumps(dict(key=key, extended=dst, secs=round(ext.shape[1] / SR, 1), gen_s=round(time.time() - t0, 1))), flush=True)
        raise SystemExit(0)
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
