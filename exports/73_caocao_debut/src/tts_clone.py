"""Qwen3-TTS Base ICL clone of the designed 'Tocqueville' narrator voice; per-line synthesis.
Per line: try seeds until median F0 in [F0_LO, F0_HI]; keep the closest otherwise.
usage: python tts_clone.py [id ...] [--force]"""
import sys, os, json, time, re
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(__file__))
from script import all_lines
from qwen_tts import Qwen3TTSModel
W = "/tmp/claude-0/w73"
OUT = f"{W}/tts/raw"
REF_WAV = f"{W}/ref.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 82)), float(os.environ.get("F0_HI", 108))
torch.set_num_threads(int(os.environ.get("NT", 4)))

def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0

def tts_text(s):
    return re.sub(r"[《》「」“”]", "", s)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if not args or d["id"] in args]
    m = Qwen3TTSModel.from_pretrained(f"{W}/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    for d in lines:
        mp = f"{OUT}/{d['id']}.json"
        if os.path.exists(mp) and not force and json.load(open(mp)).get("text") == d["say"]:
            continue
        best = None
        for seed in [1000 + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]:
            torch.manual_seed(seed); np.random.seed(seed); t = time.time()
            wavs, sr2 = m.generate_voice_clone(text=tts_text(d["say"]), language="Chinese", voice_clone_prompt=prompt,
                                               temperature=0.8, subtalker_temperature=0.8)
            x = wavs[0].astype(np.float32); f0 = f0_median(x, sr2); dur = len(x) / sr2
            nch = len(re.sub(r"[，。？！：；、“”《》「」\s·]", "", d["say"]))
            cps = nch / max(dur, 0.1)
            ok = F0_LO <= f0 <= F0_HI and 2.8 <= cps <= 7.5   # cps guard catches truncation / runaway
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s cps={cps:.2f} gen={time.time()-t:.0f}s ok={ok}", flush=True)
            c = dict(seed=seed, f0=f0, dur=dur, cps=cps, ok=ok, x=x, sr=sr2)
            if best is None or (ok and not best["ok"]) or (ok == best["ok"] and abs(f0 - 95) < abs(best["f0"] - 95)):
                best = c
            if ok: break
        sf.write(f"{OUT}/{d['id']}.wav", best["x"], best["sr"])
        json.dump({k: best[k] for k in ("seed", "f0", "dur", "cps", "ok")} | dict(id=d["id"], text=d["say"]), open(mp, "w"), ensure_ascii=False)

if __name__ == "__main__":
    main()
