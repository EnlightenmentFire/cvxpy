"""Qwen3-TTS-12Hz-1.7B-Base 克隆（ICL）托克维尔设计音色，逐句合成。
参考音频：托克维尔那期的设计音色参考（18 秒），参考文本见 REF_TEXT。
每句：最多 NSEEDS 个种子，取中位音高落在 [F0_LO, F0_HI] 的第一个，否则取最接近 95 Hz 的。
usage: python tts_clone.py [id 前缀 ...] [--force]
"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from qwen_tts import Qwen3TTSModel

W = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{W}/tts/raw"
MODEL = os.environ.get("TTS_MODEL", "/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base")
REF_WAV = f"{W}/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 85)), float(os.environ.get("F0_HI", 105))
torch.set_num_threads(int(os.environ.get("THREADS", 4)))


def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array["frequency"]; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or [""]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if any(d["id"].startswith(a) for a in args)]
    os.makedirs(OUT, exist_ok=True)
    m = Qwen3TTSModel.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="cpu")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    for d in lines:
        meta = f"{OUT}/{d['id']}.json"
        if os.path.exists(meta) and not force and json.load(open(meta)).get("tts") == d["tts"]:
            continue
        best = None
        for seed in [1000 + 7 * i for i in range(int(os.environ.get("NSEEDS", 4)))]:
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr2 = m.generate_voice_clone(text=d["tts"].replace("“", "").replace("”", ""), language="Chinese",
                                               voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8)
            x = wavs[0].astype(np.float32); f0 = f0_median(x, sr2); dur = len(x) / sr2
            # 防止明显的胡言/截断：时长须在 每字 0.12–0.45 秒
            nch = sum(1 for c in d["tts"] if "一" <= c <= "鿿")
            sane = 0.12 * nch <= dur <= 0.45 * nch + 1.0
            ok = F0_LO <= f0 <= F0_HI and sane
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s gen={time.time()-t:.0f}s ok={ok}", flush=True)
            c = dict(seed=seed, f0=f0, dur=dur, ok=ok, x=x, sr=sr2, sane=sane)
            if best is None or (sane, -abs(f0 - 95)) > (best["sane"], -abs(best["f0"] - 95)):
                best = c
            if ok:
                best = c; break
        sf.write(f"{OUT}/{d['id']}.wav", best["x"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], ok=best["ok"], tts=d["tts"]),
                  open(meta, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
