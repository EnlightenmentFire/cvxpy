"""Re-synthesise only the named lines (ep47 addition, same engine / reference / gates as narrate_batch.py).

Used for lines whose *processed* take (after postprocess.py) left the pitch band or failed the
ASR read-back. Each candidate is run through the exact postprocess.py chain in memory, and is
accepted only if
  raw:       median F0 (after 0.4 s pause cap) in --f0 and pinyin+tone error <= --max-per
  processed: median F0 in --f0 and pinyin+tone error == 0
Up to --tries new seeds per line; otherwise the best-scoring candidate is kept and flagged.
The winning raw take replaces raw/<id>.wav and takes.json; then rerun postprocess.py --ids ..."""
import argparse
import json
import os
import re
import sys
import time

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from audio_utils import cer, highpass, median_f0, normalize_rms, per, tempo, transcribe, trim_and_squeeze  # noqa: E402
from script_data import all_lines  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--ref", required=True)
ap.add_argument("--ref-text", required=True)
ap.add_argument("--ids", required=True)
ap.add_argument("--tries", type=int, default=5)
ap.add_argument("--f0", default="86.5,103.5")
ap.add_argument("--max-per", type=float, default=0.05)
ap.add_argument("--narr-rate", type=float, default=5.4)
ap.add_argument("--quote-rate", type=float, default=4.3)
ap.add_argument("--max-factor", type=float, default=1.32)
ap.add_argument("--seed-base", type=int, default=20000)
args = ap.parse_args()

torch.set_num_threads(4)
f_lo, f_hi = [float(x) for x in args.f0.split(",")]
meta_path = os.path.join(args.out, "takes.json")
meta = json.load(open(meta_path))
log_path = os.path.join(args.out, "takes_log.jsonl")
lines = {l["id"]: l for l in all_lines()}
ids = args.ids.split(",")


def spoken_chars(s):  # identical to postprocess.py
    return len(re.sub(r"[\s，。、；：！？“”‘’《》（）「」…—,.;:!?A-Za-z]", "", s)) + len(re.findall(r"[A-Za-z]+", s))


def process(ln, w, sr):  # identical chain to postprocess.py
    w = trim_and_squeeze(w, sr, max_pause=0.4)
    rate0 = spoken_chars(ln["say"]) / (len(w) / sr)
    target = args.quote_rate if ln["kind"] == "quote" else args.narr_rate
    factor = float(np.clip(target / rate0, 1.0, args.max_factor))
    y = tempo(w, sr, factor)
    y = trim_and_squeeze(y, sr, max_pause=0.4)
    y = highpass(y, sr, 50)
    y = normalize_rms(y, sr, -18.0)
    return y, factor


from qwen_tts import Qwen3TTSModel  # noqa: E402

model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                                      device_map=("cuda:0" if torch.cuda.is_available() else "cpu"),
                                      dtype=torch.bfloat16, attn_implementation="sdpa")
ref_wav, ref_sr = sf.read(args.ref, dtype="float32")
prompt = model.create_voice_clone_prompt(ref_audio=(ref_wav, ref_sr), ref_text=args.ref_text)

failing = []
for lid in ids:
    ln = lines[lid]
    best = None
    for k in range(args.tries):
        seed = args.seed_base + 1009 * k + int(lid[-4:])
        torch.manual_seed(seed)
        np.random.seed(seed)
        t0 = time.time()
        wavs, sr = model.generate_voice_clone(text=ln["say"], language="Chinese", voice_clone_prompt=prompt)
        w = np.asarray(wavs[0], np.float32)
        gen_s = time.time() - t0
        f50, f10, f90 = median_f0(trim_and_squeeze(w, sr, max_pause=0.4), sr)
        hyp = transcribe(w, sr)
        e = float(per(ln["say"], hyp))
        y, factor = process(ln, w, sr)
        pf, _, _ = median_f0(y, sr)
        phyp = transcribe(y, sr)
        pe = float(per(ln["say"], phyp))
        ok = bool(f_lo <= f50 <= f_hi and e <= args.max_per and f_lo <= pf <= f_hi and pe == 0)
        score = float(max(0, f_lo - f50, f50 - f_hi) + max(0, f_lo - pf, pf - f_hi) * 2
                      + abs(pf - 95) / 20 + e * 60 + pe * 60)
        take = dict(id=lid, round=f"redo{k}", seed=seed, f0=round(f50, 1), f0_p10=round(f10, 1), f0_p90=round(f90, 1),
                    dur=round(len(w) / sr, 2), per=round(e, 3), cer=round(float(cer(ln["say"], hyp)), 3), asr=hyp,
                    proc_f0=round(pf, 1), proc_per=round(pe, 3), proc_asr=phyp, factor=round(factor, 3),
                    ok=ok, gen_s=round(gen_s, 1), score=score)
        with open(log_path, "a") as fh:
            fh.write(json.dumps(take, ensure_ascii=False) + "\n")
        print(json.dumps(take, ensure_ascii=False), flush=True)
        if best is None or score < best[0]["score"]:
            best = (take, w, sr)
        if ok:
            break
    take, w, sr = best
    sf.write(os.path.join(args.out, "raw", f"{lid}.wav"), w, sr)
    meta[lid] = take
    json.dump(meta, open(meta_path, "w"), ensure_ascii=False, indent=1)
    if not take["ok"]:
        failing.append(lid)
print("DONE; failing:", failing, flush=True)
