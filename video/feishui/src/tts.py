"""Clone the Tocqueville narrator voice (Qwen3-TTS-12Hz-1.7B-Base, ICL) and synthesize each line.
Seeds are retried until the median F0 lands inside [F0_LO, F0_HI]; best candidate kept.
usage: python tts.py [id_prefix ...] [--force]
"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
from qwen_tts import Qwen3TTSModel

W = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{W}/tts/raw"
REF_WAV = f"{W}/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
MODEL = os.environ.get("TTS_MODEL", "/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base")
F0_LO, F0_HI = float(os.environ.get("F0_LO", 82)), float(os.environ.get("F0_HI", 108))
torch.set_num_threads(int(os.environ.get("THREADS", 4)))


def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if not args or any(d["id"].startswith(a) for a in args)]
    os.makedirs(OUT, exist_ok=True)
    m = Qwen3TTSModel.from_pretrained(MODEL, dtype=torch.float32, device_map="cpu")
    rw, rsr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(rw.astype(np.float32), rsr), ref_text=REF_TEXT)
    for d in lines:
        mp = f"{OUT}/{d['id']}.json"
        if os.path.exists(mp) and not force and json.load(open(mp)).get("text") == d["say"]:
            continue
        best = None
        for seed in [1000 + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]:
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=d["say"].replace("“", "").replace("”", ""), language="Chinese",
                                              voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32); f0 = f0_median(w, sr); dur = len(w) / sr
            ok = F0_LO <= f0 <= F0_HI and dur < 1.2 * len(d["say"]) / 2.5 + 3
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s gen={time.time()-t:.0f}s ok={ok}", flush=True)
            c = dict(seed=seed, f0=f0, dur=dur, ok=ok, w=w, sr=sr)
            if best is None or (ok and not best["ok"]) or (ok == best["ok"] and abs(f0 - 94) < abs(best["f0"] - 94)):
                best = c
            if ok:
                break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump({k: best[k] for k in ("seed", "f0", "dur", "ok")} | dict(id=d["id"], text=d["say"]),
                  open(mp, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
