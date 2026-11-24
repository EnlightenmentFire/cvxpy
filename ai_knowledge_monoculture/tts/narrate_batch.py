"""Batched version of narrate.py for the full script (same acceptance rules, higher throughput on CPU).

Round r: every still-failing sentence is synthesised again with a new seed, `--batch` sentences per
model call. A take is accepted when its median pitch (measured after the 0.4 s pause cap) is inside
--f0 and the ASR read-back matches by pinyin+tone. After the last round the best take is kept and
flagged so it can be fixed by hand."""
import argparse
import json
import os
import sys
import time

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from audio_utils import cer, median_f0, per, transcribe, trim_and_squeeze  # noqa: E402
from script_data import all_lines  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ref", required=True)
ap.add_argument("--ref-text", required=True)
ap.add_argument("--ids", default="")
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--batch", type=int, default=4)
ap.add_argument("--f0", default="86.5,103.5")
ap.add_argument("--max-per", type=float, default=0.05)
ap.add_argument("--redo", action="store_true")
ap.add_argument("--seed-base", type=int, default=5000)
args = ap.parse_args()

torch.set_num_threads(4)
os.makedirs(os.path.join(args.out, "raw"), exist_ok=True)
meta_path = os.path.join(args.out, "takes.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
log_path = os.path.join(args.out, "takes_log.jsonl")

lines = [l for l in all_lines() if l["kind"] != "robot"]
if args.ids:
    want = set(args.ids.split(","))
    lines = [l for l in lines if l["id"] in want]
if not args.redo:
    lines = [l for l in lines if not (l["id"] in meta and meta[l["id"]].get("ok"))]
f_lo, f_hi = [float(x) for x in args.f0.split(",")]
print(f"{len(lines)} sentences to synthesise", flush=True)

from qwen_tts import Qwen3TTSModel  # noqa: E402

model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu",
                                      dtype=torch.bfloat16, attn_implementation="sdpa")
ref_wav, ref_sr = sf.read(args.ref, dtype="float32")
prompt = model.create_voice_clone_prompt(ref_audio=(ref_wav, ref_sr), ref_text=args.ref_text)

best = {}
pending = list(lines)
for r in range(args.rounds):
    if not pending:
        break
    # sort by length so a batch has similar lengths (less padding waste)
    pending.sort(key=lambda l: len(l["say"]))
    nxt = []
    for g in range(0, len(pending), args.batch):
        group = pending[g:g + args.batch]
        seed = args.seed_base + r * 1009 + g
        torch.manual_seed(seed)
        np.random.seed(seed)
        t0 = time.time()
        wavs, sr = model.generate_voice_clone(text=[l["say"] for l in group], language=["Chinese"] * len(group),
                                              voice_clone_prompt=prompt)
        gen_s = time.time() - t0
        for ln, w in zip(group, wavs):
            w = np.asarray(w, np.float32)
            f50, f10, f90 = median_f0(trim_and_squeeze(w, sr, max_pause=0.4), sr)
            hyp = transcribe(w, sr)
            e = float(per(ln["say"], hyp))
            c = float(cer(ln["say"], hyp))
            ok = bool((f_lo <= f50 <= f_hi) and e <= args.max_per)
            score = float(max(0, f_lo - f50, f50 - f_hi) + abs(f50 - 95) / 20 + e * 60)
            take = dict(id=ln["id"], round=r, seed=seed, f0=round(f50, 1), f0_p10=round(f10, 1), f0_p90=round(f90, 1),
                        dur=round(len(w) / sr, 2), per=round(e, 3), cer=round(c, 3), asr=hyp, ok=ok,
                        gen_s=round(gen_s / len(group), 1), score=score)
            with open(log_path, "a") as fh:
                fh.write(json.dumps(take, ensure_ascii=False) + "\n")
            print(json.dumps(take, ensure_ascii=False), flush=True)
            if ln["id"] not in best or score < best[ln["id"]][0]["score"]:
                best[ln["id"]] = (take, w, sr)
                sf.write(os.path.join(args.out, "raw", f"{ln['id']}.wav"), w, sr)
                meta[ln["id"]] = take
                json.dump(meta, open(meta_path, "w"), ensure_ascii=False, indent=1)
            if not ok:
                nxt.append(ln)
    pending = nxt
    print(f"round {r}: {len(pending)} still failing", flush=True)
print("DONE; failing:", [l["id"] for l in pending], flush=True)
