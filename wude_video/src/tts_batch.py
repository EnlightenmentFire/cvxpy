"""Batched version of tts_worker: same checks (F0 range, ASR pinyin read-back, speaking rate),
4 lines per forward pass (~2.4x faster on CPU). Cache is keyed by the TTS text, so editing a
line in the script only re-synthesises that line.

Usage: tts_batch.py script.json out_dir [line_id ...]
"""
import json
import os
import sys
import time
import zlib

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(__file__))
import tts_worker as T

BATCH = int(os.environ.get("BATCH", "4"))


def main():
    script_json, out_dir = sys.argv[1], sys.argv[2]
    ids = set(sys.argv[3:])
    os.makedirs(out_dir, exist_ok=True)
    segs = json.load(open(script_json, encoding="utf-8"))
    lines = [l for s in segs for l in s["lines"]]
    if ids:
        lines = [l for l in lines if l["id"] in ids]
    todo = []
    for ln in lines:
        mp = f"{out_dir}/{ln['id']}.json"
        if os.path.exists(mp):
            meta = json.load(open(mp, encoding="utf-8"))
            if meta.get("tts") == ln["tts"]:
                continue
        todo.append(ln)
    print(f"{len(todo)} lines to synthesise", flush=True)
    if not todo:
        return
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(T.BASE_MODEL, device_map="cpu", dtype=torch.bfloat16,
                                          attn_implementation="sdpa")
    ref, rsr = sf.read(T.REF_WAV)
    prompt = model.create_voice_clone_prompt(ref_audio=(ref.astype(np.float32), rsr), ref_text=T.REF_TEXT)
    asr = T.ASR()
    best = {}
    queue = sorted(todo, key=lambda l: len(T.han_only(l["tts"])))
    for attempt in range(T.MAX_TRIES):
        if not queue:
            break
        retry = []
        for b in range(0, len(queue), BATCH):
            batch = queue[b:b + BATCH]
            texts = [l["tts"] for l in batch]
            nmax = max(len(T.han_only(t)) for t in texts)
            seed = 1000 + 37 * attempt + zlib.crc32(batch[0]["id"].encode()) % 997 * (1 if attempt else 0)
            torch.manual_seed(seed)
            t1 = time.time()
            wavs, sr = model.generate_voice_clone(text=texts, language=["Chinese"] * len(batch),
                                                  voice_clone_prompt=prompt * len(batch),
                                                  max_new_tokens=int(12.5 * (nmax / 2.0 + 6)))
            gen = time.time() - t1
            for ln, w in zip(batch, wavs):
                w = np.asarray(w, dtype=np.float32)
                text = ln["tts"]
                dur = len(w) / sr
                f0, f0span = T.f0_stats(w, sr)
                got_txt = asr(w, sr)
                exp, got = T.pinyin_seq(text), T.pinyin_seq(got_txt)
                ser = T.edit_distance(exp, got) / max(1, len(exp))
                n_han = len(T.han_only(text))
                rate = n_han / max(dur, 0.1)
                ok_f0 = T.F0_LO <= f0 <= T.F0_HI
                ok_rate = 1.6 <= rate <= 6.5
                score = ser * 3 + (0 if ok_f0 else min(abs(f0 - 95) / 40, 1.0)) + (0 if ok_rate else 1.0)
                take = dict(seed=seed, attempt=attempt, dur=dur, f0=f0, f0span=f0span, ser=ser, asr=got_txt,
                            rate=rate, score=score, diffs=T.diff_report(exp, got)[:20])
                prev = best.get(ln["id"])
                if prev is None or score < prev[0]["score"]:
                    best[ln["id"]] = (take, w, sr)
                status = "ok" if (ok_f0 and ok_rate and ser <= T.SER_OK) else "RETRY"
                print(f"{ln['id']} a{attempt} f0={f0:.1f} ser={ser:.3f} rate={rate:.2f} {status} | {got_txt[:36]}",
                      flush=True)
                if status == "RETRY":
                    retry.append(ln)
                else:
                    _save(out_dir, ln, best[ln["id"]])
            print(f"  batch of {len(batch)} in {gen:.0f}s", flush=True)
        queue = retry
    for ln in queue:  # keep best take for lines that never passed
        _save(out_dir, ln, best[ln["id"]], flagged=True)
    print("ALL DONE", flush=True)


def _save(out_dir, ln, rec, flagged=False):
    take, w, sr = rec
    sf.write(f"{out_dir}/{ln['id']}.wav", w, sr)
    take.update(id=ln["id"], kind=ln["kind"], text=ln["text"], tts=ln["tts"], flagged=flagged)
    json.dump(take, open(f"{out_dir}/{ln['id']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
