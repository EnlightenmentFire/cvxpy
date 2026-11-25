"""Tocqueville voice (Qwen3-TTS Base ICL clone) per-line synthesis with F0 gate.
usage: python tts_run.py [ids...] [--force]"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
from qwen_tts import Qwen3TTSModel
OUT = "/home/user/work/tts/raw"
REF_WAV = "/home/user/work/ref/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = 82.0, 108.0
torch.set_num_threads(int(os.environ.get("THREADS", 4)))

def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    seed0 = int(os.environ.get("SEED0", 1000))
    lines = [d for d in all_lines() if not args or any(d["id"].startswith(a) for a in args)]
    m = Qwen3TTSModel.from_pretrained("/home/user/work/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
    ref_w, ref_sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(ref_w.astype(np.float32), ref_sr), ref_text=REF_TEXT)
    for d in lines:
        txt = tts_text(d["say"])
        meta_p = f"{OUT}/{d['id']}.json"
        if os.path.exists(meta_p) and not force:
            try:
                if json.load(open(meta_p)).get("tts") == txt: continue
            except Exception: pass
        best = None
        for seed in [seed0 + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]:
            torch.manual_seed(seed); np.random.seed(seed); t = time.time()
            wavs, sr = m.generate_voice_clone(text=txt, language="Chinese", voice_clone_prompt=prompt,
                                              temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32); f0 = f0_median(w, sr); dur = len(w) / sr
            ok = F0_LO <= f0 <= F0_HI and dur < len(txt) * 0.45 + 2
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s gen={time.time()-t:.0f}s ok={ok} | {txt}", flush=True)
            cand = dict(seed=seed, f0=f0, dur=dur, ok=ok, w=w, sr=sr)
            if best is None or (ok and not best["ok"]) or (ok == best["ok"] and abs(f0 - 92) < abs(best["f0"] - 92)):
                best = cand
            if ok: break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], ok=best["ok"], say=d["say"], tts=txt),
                  open(meta_p, "w"), ensure_ascii=False)

if __name__ == "__main__":
    main()
