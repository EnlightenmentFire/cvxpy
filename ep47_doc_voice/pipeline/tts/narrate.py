"""Step 2 of the voice pipeline: clone the designed narrator voice with Qwen3-TTS Base
(Apache-2.0) and synthesise the script sentence by sentence.

For every sentence: try seeds until the median pitch is inside 85-105 Hz and an ASR
read-back (faster-whisper large-v3) matches the text; keep the best attempt otherwise.
Raw takes go to <out>/raw/<id>.wav and metadata to <out>/takes.json.
"""
import argparse
import json
import os
import sys
import time
import zlib

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from audio_utils import cer, median_f0, per, transcribe, trim_and_squeeze  # noqa: E402
from script_data import all_lines  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ref", required=True, help="reference wav (designed voice)")
ap.add_argument("--ref-text", required=True)
ap.add_argument("--ids", default="", help="comma separated line ids (default: all non-robot lines)")
ap.add_argument("--tries", type=int, default=4)
ap.add_argument("--f0", default="86.5,103.5")   # small margin inside 85-105 for post-processing drift
ap.add_argument("--max-cer", type=float, default=0.06)
ap.add_argument("--redo", action="store_true")
args = ap.parse_args()

torch.set_num_threads(4)
os.makedirs(os.path.join(args.out, "raw"), exist_ok=True)
meta_path = os.path.join(args.out, "takes.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

lines = [l for l in all_lines() if l["kind"] != "robot"]
if args.ids:
    want = args.ids.split(",")
    lines = [l for l in lines if l["id"] in want]
f_lo, f_hi = [float(x) for x in args.f0.split(",")]

from qwen_tts import Qwen3TTSModel  # noqa: E402

model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map=("cuda:0" if torch.cuda.is_available() else "cpu"),
                                      dtype=torch.bfloat16, attn_implementation="sdpa")
ref_wav, ref_sr = sf.read(args.ref, dtype="float32")
prompt = model.create_voice_clone_prompt(ref_audio=(ref_wav, ref_sr), ref_text=args.ref_text)

for ln in lines:
    lid = ln["id"]
    if lid in meta and meta[lid].get("ok") and not args.redo:
        print("skip", lid, flush=True)
        continue
    best = None
    for k in range(args.tries):
        seed = 1000 + 17 * k + (zlib.crc32(lid.encode()) % 97)
        torch.manual_seed(seed)
        np.random.seed(seed)
        t0 = time.time()
        wavs, sr = model.generate_voice_clone(text=ln["say"], language="Chinese", voice_clone_prompt=prompt)
        w = np.asarray(wavs[0], np.float32)
        gen_s = time.time() - t0
        f50, f10, f90 = median_f0(trim_and_squeeze(w, sr, max_pause=0.4), sr)   # measured as it will be used
        hyp = transcribe(w, sr)
        e = float(per(ln["say"], hyp))   # pinyin+tone syllable error rate
        c = float(cer(ln["say"], hyp))
        ok = bool((f_lo <= f50 <= f_hi) and e <= args.max_cer)
        # score: pitch distance from 95 Hz + heavy penalty for ASR errors
        score = float(abs(f50 - 95) / 10 + e * 40)
        take = dict(id=lid, seed=seed, f0=round(f50, 1), f0_p10=round(f10, 1), f0_p90=round(f90, 1),
                    dur=round(len(w) / sr, 2), per=round(e, 3), cer=round(c, 3), asr=hyp, ok=ok, gen_s=round(gen_s, 1), score=score)
        print(json.dumps(take, ensure_ascii=False), flush=True)
        if best is None or score < best[0]["score"]:
            best = (take, w, sr)
        if ok:
            break
    take, w, sr = best
    sf.write(os.path.join(args.out, "raw", f"{lid}.wav"), w, sr)
    meta[lid] = take
    json.dump(meta, open(meta_path, "w"), ensure_ascii=False, indent=1)
print("DONE", flush=True)
