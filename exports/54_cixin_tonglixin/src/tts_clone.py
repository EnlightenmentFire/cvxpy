"""Clone the Tocqueville narrator voice (Qwen3-TTS Base ICL) and synthesize each script line.
Each line: try seeds until median F0 in [F0_LO, F0_HI]; keep best. usage: python tts_clone.py [ids...] [--force]"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from qwen_tts import Qwen3TTSModel
W = "/tmp/claude-0/work"
OUT = f"{W}/tts/raw"; os.makedirs(OUT, exist_ok=True)
REF_WAV = f"{W}/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 85)), float(os.environ.get("F0_HI", 105))
torch.set_num_threads(int(os.environ.get("NT", 4)))

def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0

def tts_text(s):
    return s.replace("“", "").replace("”", "").replace("·", "")

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if not args or d["id"] in args]
    m = Qwen3TTSModel.from_pretrained(f"/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    seed0 = int(os.environ.get("SEED0", 1000))
    for d in lines:
        mp = f"{OUT}/{d['id']}.json"
        if os.path.exists(mp) and not force and json.load(open(mp)).get("text") == d["say"]:
            continue
        best = None
        for seed in [seed0 + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]:
            torch.manual_seed(seed); np.random.seed(seed); t = time.time()
            wavs, sr2 = m.generate_voice_clone(text=tts_text(d["say"]), language="Chinese", voice_clone_prompt=prompt,
                                               temperature=0.8, subtalker_temperature=0.8)
            x = wavs[0].astype(np.float32); f0 = f0_median(x, sr2); ok = F0_LO <= f0 <= F0_HI
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={len(x)/sr2:.1f}s gen={time.time()-t:.0f}s ok={ok}", flush=True)
            c = dict(seed=seed, f0=f0, dur=len(x)/sr2, ok=ok, w=x, sr=sr2)
            if best is None or abs(f0 - 95) < abs(best["f0"] - 95): best = c
            if ok: best = c; break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], ok=best["ok"], text=d["say"]),
                  open(mp, "w"), ensure_ascii=False)

if __name__ == "__main__":
    main()
