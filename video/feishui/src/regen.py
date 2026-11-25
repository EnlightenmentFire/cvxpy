"""Regenerate given lines with several seeds; keep the take whose ASR contains the required text and has lowest pinyin error.
usage: python regen.py id:required [id:required ...]"""
import sys, os, json, re, time, difflib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
from tts import REF_WAV, REF_TEXT, MODEL, OUT, f0_median
from qwen_tts import Qwen3TTSModel
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
from scipy.signal import resample_poly
torch.set_num_threads(4)
D = {d["id"]: d for d in all_lines()}
m = Qwen3TTSModel.from_pretrained(MODEL, dtype=torch.float32, device_map="cpu")
rw, rsr = sf.read(REF_WAV); prompt = m.create_voice_clone_prompt(ref_audio=(rw.astype(np.float32), rsr), ref_text=REF_TEXT)
asr = WhisperModel("small", device="cpu", compute_type="int8")
py = lambda s: lazy_pinyin(re.sub(r"[，。？！：；、“”《》（）·\s,.?!]", "", s))
for arg in sys.argv[1:]:
    lid, _, req = arg.partition(":"); d = D[lid]; best = None
    for seed in [2000 + 13 * i for i in range(int(os.environ.get("NSEEDS", 6)))]:
        torch.manual_seed(seed); np.random.seed(seed)
        wavs, sr = m.generate_voice_clone(text=d["say"], language="Chinese", voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8)
        w = wavs[0].astype(np.float32); f0 = f0_median(w, sr)
        x16 = resample_poly(w, 16000 // np.gcd(sr, 16000), sr // np.gcd(sr, 16000)).astype(np.float32)
        hyp = "".join(s.text for s in asr.transcribe(x16, language="zh", beam_size=5, initial_prompt="以下是普通话的句子，关于淝水之战、东晋、苻坚、秦兵。")[0])
        err = 1 - difflib.SequenceMatcher(a=py(d["say"]), b=py(hyp)).ratio()
        ok = (req in hyp) and 82 <= f0 <= 108
        print(lid, seed, f"f0={f0:.0f} err={err:.3f} ok={ok}", hyp, flush=True)
        score = (0 if ok else 1, err)
        if best is None or score < best[0]: best = (score, w, sr, seed, f0, hyp)
        if ok and err < 0.05: break
    _, w, sr, seed, f0, hyp = best
    sf.write(f"{OUT}/{lid}.wav", w, sr)
    json.dump(dict(id=lid, seed=seed, f0=f0, dur=len(w) / sr, ok=True, text=d["say"], asr=hyp), open(f"{OUT}/{lid}.json", "w"), ensure_ascii=False)
    print("KEEP", lid, seed, hyp, flush=True)
