"""Clone the Tocqueville narrator voice (Qwen3-TTS 1.7B Base, ICL mode) line by line.
Reference: A0b 托克维尔设计音色参考 18 s (= tocqueville branch preview/voice_design_reference.m4a). bf16 on CPU (AMX), ~4x realtime.
Each line: try seeds until median F0 within [F0_LO, F0_HI] Hz; keep closest to 95 Hz otherwise.
usage: python tts_clone.py [id prefixes...] [--force]
"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from qwen_tts import Qwen3TTSModel

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{WORK}/tts/raw"
REF_WAV = f"{WORK}/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 85.0)), float(os.environ.get("F0_HI", 105.0))
torch.set_num_threads(int(os.environ.get("THREADS", 4)))


def f0_median(w, sr):
    snd = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr)
    v = snd.to_pitch(pitch_floor=75, pitch_ceiling=300).selected_array['frequency']
    v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def tts_text(s):
    return s.replace("“", "").replace("”", "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if not args or any(d["id"] == a or d["id"].startswith(a) for a in args)]
    os.makedirs(OUT, exist_ok=True)
    m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=getattr(torch, os.environ.get("TTS_DTYPE", "bfloat16")), device_map="cpu")
    ref_w, ref_sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(ref_w.astype(np.float32), ref_sr), ref_text=REF_TEXT)
    for d in lines:
        meta_p = f"{OUT}/{d['id']}.json"
        if os.path.exists(meta_p) and not force:
            try:
                if json.load(open(meta_p)).get("text") == d["say"]:
                    continue
            except Exception:
                pass
        best = None
        base = int(os.environ.get("SEED0", 1000))
        for seed in [base + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]:
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=tts_text(d["say"]), language="Chinese", voice_clone_prompt=prompt,
                                              temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32)
            f0, dur = f0_median(w, sr), len(w) / sr
            ok = F0_LO <= f0 <= F0_HI and dur < len(d["say"]) * 0.5 + 2
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s gen={time.time()-t:.0f}s ok={ok}", flush=True)
            cand = dict(seed=seed, f0=f0, dur=dur, ok=ok, w=w, sr=sr)
            if best is None or (cand["ok"] and not best["ok"]) or (cand["ok"] == best["ok"] and abs(f0 - 95) < abs(best["f0"] - 95)):
                best = cand
            if ok:
                break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], ok=best["ok"], text=d["say"]),
                  open(meta_p, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
