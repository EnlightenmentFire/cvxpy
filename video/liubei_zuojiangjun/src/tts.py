# -*- coding: utf-8 -*-
"""托克维尔声音：Qwen3-TTS-12Hz-1.7B-Base 以设计参考音（18 秒）做 ICL 克隆，逐句合成。
每句试若干 seed，中位基频须在 [F0_LO, F0_HI]（参考音约 87 Hz），字速须在合理区间；否则取最接近的一版。
用法：python tts.py [id 前缀 ...] [--force]
输出：$WORK/tts/raw/<id>.wav + <id>.json
"""
import sys, os, json, time, re
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from qwen_tts import Qwen3TTSModel

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{WORK}/tts/raw"
MODEL = os.environ.get("TTS_MODEL", "/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base")
REF_WAV = f"{WORK}/ref/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 80)), float(os.environ.get("F0_HI", 108))
NSEEDS = int(os.environ.get("NSEEDS", 3))
torch.set_num_threads(int(os.environ.get("THREADS", 4)))


def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=70, pitch_ceiling=300)
    v = p.selected_array["frequency"]; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def nchars(s):
    return len([c for c in s if "一" <= c <= "鿿" or c.isdigit()])


def tts_text(s):
    return s.replace("“", "").replace("”", "").replace("《", "").replace("》", "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = [d for d in all_lines() if not args or any(d["id"].startswith(a) for a in args)]
    os.makedirs(OUT, exist_ok=True)
    todo = []
    for d in lines:
        mp = f"{OUT}/{d['id']}.json"
        if os.path.exists(mp) and not force:
            try:
                if json.load(open(mp)).get("text") == d["tts"]:
                    continue
            except Exception:
                pass
        todo.append(d)
    print("todo:", len(todo), flush=True)
    if not todo:
        return
    m = Qwen3TTSModel.from_pretrained(MODEL, dtype=torch.float32, device_map="cpu")
    rw, rsr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(rw.astype(np.float32), rsr), ref_text=REF_TEXT)
    for d in todo:
        best = None
        n = nchars(d["tts"])
        for k in range(NSEEDS):
            seed = 1000 + 7 * k
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=tts_text(d["tts"]), language="Chinese", voice_clone_prompt=prompt,
                                              temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32)
            f0 = f0_median(w, sr); dur = len(w) / sr; cps = n / max(dur, 0.1)
            ok = F0_LO <= f0 <= F0_HI and 2.8 <= cps <= 6.5
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s cps={cps:.2f} gen={time.time()-t:.0f}s ok={ok}", flush=True)
            score = abs(f0 - 92) + (0 if 2.8 <= cps <= 6.5 else 50)
            if best is None or score < best["score"]:
                best = dict(seed=seed, f0=f0, dur=dur, cps=cps, ok=ok, w=w, sr=sr, score=score)
            if ok:
                break
        sf.write(f"{OUT}/{d['id']}.wav", best["w"], best["sr"])
        json.dump(dict(id=d["id"], seed=best["seed"], f0=best["f0"], dur=best["dur"], cps=best["cps"], ok=best["ok"], text=d["tts"]),
                  open(f"{OUT}/{d['id']}.json", "w"), ensure_ascii=False)
    print("ALLDONE", flush=True)


if __name__ == "__main__":
    main()
