"""Regenerate specific lines with fresh seeds; keep the take with the best ASR read-back within 85-105 Hz."""
import os, sys, json, shutil, time
import numpy as np, torch, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); sys.path.insert(0, os.path.dirname(__file__))
torch.set_num_threads(int(os.environ.get("TTS_THREADS", "2")))
from qwen_tts import Qwen3TTSModel
from pitch import med_f0
from tts import to_tts, REF_TEXT
from asr_check import load16, cer
import script
base, ref, fw = sys.argv[1:4]; keys = sys.argv[4:]
segs = {s["id"]: s for s in script.SEGMENTS}
m = Qwen3TTSModel.from_pretrained(base, dtype=torch.bfloat16, device_map="cpu", attn_implementation="sdpa")
prompt = m.create_voice_clone_prompt(ref_audio=ref, ref_text=REF_TEXT, x_vector_only_mode=False)
from faster_whisper import WhisperModel
asr = WhisperModel(fw, device="cpu", compute_type="int8", cpu_threads=2)
meta = json.load(open("lines/meta.json"))
os.makedirs("lines/alt", exist_ok=True)
for key in keys:
    sid, idx = key.rsplit("_", 1); ln = segs[sid]["lines"][int(idx)]
    text = to_tts(ln)
    takes = []
    if os.path.exists(f"lines/{key}.wav") and meta.get(key, {}).get("text") == text:
        takes.append((f"lines/{key}.wav", meta[key]["seed"]))
    for seed in (51, 52, 53):
        torch.manual_seed(seed)
        w, sr = m.generate_voice_clone(text=text, language="Chinese", voice_clone_prompt=prompt)
        fn = f"lines/alt/{key}_{seed}.wav"; sf.write(fn, w[0], sr); takes.append((fn, seed))
    best = None
    for fn, seed in takes:
        f0 = med_f0(fn)
        segs_, _ = asr.transcribe(load16(fn), language="zh", beam_size=5)
        hyp = "".join(s.text for s in segs_)
        e = cer(text, hyp)
        ok = 85 <= f0 <= 105
        print(f"{key} seed{seed} f0={f0:.1f} CER={e:.3f} {'' if ok else '(pitch out)'} | {hyp}", flush=True)
        score = e + (1 if not ok else 0)
        if best is None or score < best[0]:
            best = (score, fn, seed, f0)
    if best[1] != f"lines/{key}.wav":
        shutil.copy(best[1], f"lines/{key}.wav")
    meta[key] = dict(text=text, f0=best[3], dur=sf.info(f"lines/{key}.wav").duration, seed=best[2])
    json.dump(meta, open("lines/meta.json", "w"), ensure_ascii=False, indent=1)
    print("KEEP", key, best[1], flush=True)
