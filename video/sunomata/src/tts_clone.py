"""Qwen3-TTS Base (ICL) 克隆托克维尔设计音色，逐句合成。中位音高不在 [85,105] Hz 就换 seed（最多 NSEEDS 次），取最接近 95 Hz 的。
参考音频与参考文本沿用 claude/tocqueville-america-video-a250yg（voice_design_reference，18 秒）。
usage: python tts_clone.py [id 前缀...]  （缺省全部）
"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
from qwen_tts import Qwen3TTSModel

W = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{W}/tts/raw"
REF_WAV = f"{W}/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
torch.set_num_threads(int(os.environ.get("THREADS", 4)))


def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def main():
    pre = [a for a in sys.argv[1:] if not a.startswith("--")] or [""]
    os.makedirs(OUT, exist_ok=True)
    lines = [d for d in all_lines() if any(d["id"].startswith(a) for a in pre)]
    m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.float32, device_map="cpu")
    rw, rsr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(rw.astype(np.float32), rsr), ref_text=REF_TEXT)
    for d in lines:
        mp = f"{OUT}/{d['id']}.json"
        if os.path.exists(mp) and "--force" not in sys.argv:
            try:
                if json.load(open(mp)).get("text") == d["say"]:
                    continue
            except Exception:
                pass
        best = None
        seeds = [int(x) for x in os.environ["SEEDS"].split(",")] if os.environ.get("SEEDS") else [1000 + 7 * i for i in range(int(os.environ.get("NSEEDS", 3)))]
        for seed in seeds:
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=tts_text(d["say"]), language="Chinese", voice_clone_prompt=prompt,
                                              temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32)
            f0 = f0_median(w, sr); dur = len(w) / sr
            ok = 85 <= f0 <= 105 and dur < 0.45 * len(d["say"]) + 2
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s gen={time.time()-t:.0f}s ok={ok}", flush=True)
            c = dict(seed=seed, f0=f0, dur=dur, ok=ok, w=w, sr=sr)
            if best is None or (ok and not best["ok"]) or (ok == best["ok"] and abs(f0 - 95) < abs(best["f0"] - 95)):
                best = c
            if ok:
                break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], ok=best["ok"], text=d["say"]),
                  open(mp, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
