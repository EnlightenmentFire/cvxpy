"""Re-synthesize specific lines: try seeds, post-process, ASR each, keep the best (lowest pinyin error, F0 in range).
usage: python regen.py id [id...]   env NTRY (default 6), SEED0"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
import tts_clone as T
import voice_post as VP
import asr_check as A
from qwen_tts import Qwen3TTSModel
from faster_whisper import WhisperModel
from scipy.signal import resample_poly

ids = sys.argv[1:]
lines = {d["id"]: d for d in all_lines()}
m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
ref_w, ref_sr = sf.read(T.REF_WAV)
prompt = m.create_voice_clone_prompt(ref_audio=(ref_w.astype(np.float32), ref_sr), ref_text=T.REF_TEXT)
asr = WhisperModel("/tmp/claude-0/models/faster-whisper-small", device="cpu", compute_type="int8", cpu_threads=2)
dp = f"{VP.OUT}/durations.json"
for lid in ids:
    d = lines[lid]
    best = None
    for k in range(int(os.environ.get("NTRY", 6))):
        seed = int(os.environ.get("SEED0", 2000)) + 13 * k
        torch.manual_seed(seed); np.random.seed(seed)
        wavs, sr = m.generate_voice_clone(text=T.tts_text(d["say"]), language="Chinese", voice_clone_prompt=prompt,
                                          temperature=0.8, subtalker_temperature=0.8)
        w = wavs[0].astype(np.float32)
        f0 = T.f0_median(w, sr)
        sf.write(f"{T.OUT}/{lid}.wav", w, sr)
        json.dump(dict(id=lid, seed=seed, f0=f0, dur=len(w) / sr, ok=True, text=d["say"]), open(f"{T.OUT}/{lid}.json", "w"), ensure_ascii=False)
        dur = VP.process(d)
        x, psr = sf.read(f"{VP.OUT}/{lid}.wav")
        segs, _ = asr.transcribe(resample_poly(x, 1, 3).astype(np.float32), language="zh", beam_size=5,
                                 initial_prompt="以下是普通话的句子，关于北宋王安石变法。")
        hyp = "".join(s.text for s in segs)
        e = A.per(A.py(d["say"]), A.py(hyp))
        score = e + (0 if T.F0_LO <= f0 <= T.F0_HI else 0.5)
        print(f"{lid} seed={seed} f0={f0:.1f} err={e:.3f} {hyp}", flush=True)
        if best is None or score < best[0]:
            best = (score, seed, w, sr, f0, hyp)
        if e == 0 and T.F0_LO <= f0 <= T.F0_HI:
            break
    score, seed, w, sr, f0, hyp = best
    sf.write(f"{T.OUT}/{lid}.wav", w, sr)
    json.dump(dict(id=lid, seed=seed, f0=f0, dur=len(w) / sr, ok=True, text=d["say"], asr=hyp), open(f"{T.OUT}/{lid}.json", "w"), ensure_ascii=False)
    durs = json.load(open(dp)) if os.path.exists(dp) else {}
    durs[lid] = round(VP.process(d), 3)
    json.dump(durs, open(dp, "w"), indent=0)
    print("KEEP", lid, seed, round(score, 3), hyp, flush=True)
