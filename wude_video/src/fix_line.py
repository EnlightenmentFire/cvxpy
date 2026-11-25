"""Re-record one line with alternative homophone substitutions, keep the take whose ASR read-back
matches, post-process it, and stretch it to the exact length of the current take so the picture
timeline (already rendered) stays valid.

usage: fix_line.py <line_id> "<tts text variant 1>" ["<variant 2>" ...]
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, os.path.dirname(__file__))
import tts_worker as T
import voice_post as V

BUILD = "/home/user/wude_build"


def main():
    lid, variants = sys.argv[1], sys.argv[2:]
    segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
    ln = next(l for s in segs for l in s["lines"] if l["id"] == lid)
    exp = T.pinyin_seq(ln["text"])  # expected reading of the real text
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(T.BASE_MODEL, device_map="cpu", dtype=torch.bfloat16,
                                          attn_implementation="sdpa")
    ref, rsr = sf.read(T.REF_WAV)
    prompt = model.create_voice_clone_prompt(ref_audio=(ref.astype(np.float32), rsr), ref_text=T.REF_TEXT)
    asr = T.ASR()
    best = None
    for vi, text in enumerate(variants):
        texts = [text] * 4
        torch.manual_seed(3000 + vi)
        wavs, sr = model.generate_voice_clone(text=texts, language=["Chinese"] * 4, voice_clone_prompt=prompt * 4,
                                              max_new_tokens=400)
        for k, w in enumerate(wavs):
            w = np.asarray(w, dtype=np.float32)
            f0, _ = T.f0_stats(w, sr)
            got_txt = asr(w, sr)
            ser = T.edit_distance(T.pinyin_seq(text), T.pinyin_seq(got_txt)) / max(1, len(T.pinyin_seq(text)))
            ok_f0 = T.F0_LO <= f0 <= T.F0_HI
            score = ser * 3 + (0 if ok_f0 else 1)
            print(f"variant {vi} take {k}: f0={f0:.1f} ser={ser:.3f} | {got_txt}", flush=True)
            if best is None or score < best[0]:
                best = (score, w, sr, text, got_txt, f0, ser)
    score, w, sr, text, got_txt, f0, ser = best
    print(f"chosen: '{text}' -> '{got_txt}' f0={f0:.1f} ser={ser:.3f}", flush=True)
    old = f"{BUILD}/voice_post/{lid}.wav"
    old_len = len(sf.read(old)[0]) / V.SR
    with tempfile.TemporaryDirectory() as d:
        raw = f"{d}/raw.wav"
        sf.write(raw, w, sr)
        y = V.process(raw, ln["kind"])
        cur = len(y) / V.SR
        a, b = f"{d}/a.wav", f"{d}/b.wav"
        sf.write(a, y.astype(np.float32), V.SR)
        subprocess.run(["rubberband", "-3", "-F", "-t", f"{old_len / cur:.6f}", a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        z, _ = sf.read(b)
    n = int(round(old_len * V.SR))
    z = np.pad(z, (0, max(0, n - len(z))))[:n]
    z = V.normalise(z, V.SR)
    os.replace(old, old + ".bak")
    sf.write(old, z.astype(np.float32), V.SR)
    json.dump(dict(id=lid, text=text, asr=got_txt, f0=f0, ser=ser, length=old_len),
              open(f"{BUILD}/voice_post/{lid}.fix.json", "w"), ensure_ascii=False, indent=1)
    print(f"replaced {old} ({old_len:.2f}s kept)", flush=True)


if __name__ == "__main__":
    main()
