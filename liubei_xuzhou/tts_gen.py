# -*- coding: utf-8 -*-
"""Qwen3-TTS-12Hz-1.7B-Base 克隆托克维尔设计音色，逐段合成（CPU，分批）。
每段：中位音高须在 85–105 Hz，否则换 seed 重来（最多 NTRY 次，保留最接近 95 Hz 的）。
usage: python tts_gen.py [ids...]   （缺省全部；已存在且文本一致的跳过）
"""
import os, sys, re, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import L, tts_text

OUT = "/tmp/claude-0/work/tts/raw"
REF_WAV = "/tmp/claude-0/work/voice/ref_voice.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
MODEL = "/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base"
F0_LO, F0_HI = float(os.environ.get("F0_LO", 85.0)), 105.0
NTRY = int(os.environ.get("NTRY", 4))
BATCH = int(os.environ.get("BATCH", 6))
torch.set_num_threads(4)


def segments():
    segs = []
    for d in L:
        txt = tts_text(d.get("say", d["t"]))
        parts = [p for p in re.split(r"(?<=[。？！；：])", txt) if p.strip()]
        merged = []
        for p in parts:
            if merged and len(re.findall(r"[一-鿿]", p)) < 7:
                merged[-1] += p
            elif merged and len(re.findall(r"[一-鿿]", merged[-1])) < 5:
                merged[-1] += p
            else:
                merged.append(p)
        for k, p in enumerate(merged):
            segs.append(dict(id=f"{d['id']}_{k}", line=d["id"], text=p.replace("“", "").replace("”", "")))
    return segs


def f0_median(w, sr):
    snd = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr)
    f = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300).selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    want = set(sys.argv[1:])
    todo = []
    for s in segments():
        if want and s["line"] not in want and s["id"] not in want:
            continue
        mp = f"{OUT}/{s['id']}.json"
        if os.environ.get("RETRY"):
            if os.path.exists(mp):
                j = json.load(open(mp))
                ok = F0_LO <= j["f0"] <= F0_HI and 2.6 <= j["cps"] <= 6.5 and j.get("text") == s["text"]
                if ok and s["id"] not in want and s["line"] not in want:
                    continue
            todo.append(s)
            continue
        if os.path.exists(mp) and json.load(open(mp)).get("text") == s["text"] and not os.environ.get("FORCE"):
            continue
        todo.append(s)
    print("segments to do:", len(todo), flush=True)
    from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained(MODEL, dtype=getattr(torch, os.environ.get("TTS_DTYPE", "bfloat16")), device_map="cpu")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    best = {}
    if os.environ.get("RETRY"):
        for s in todo:
            mp = f"{OUT}/{s['id']}.json"
            if os.path.exists(mp) and not (want and (s["id"] in want or s["line"] in want)):
                j = json.load(open(mp))
                if j.get("text") == s["text"]:
                    best[s["id"]] = dict(seed=j["seed"], f0=j["f0"], dur=j["dur"], cps=j["cps"], ok=False)
    seed0 = int(os.environ.get("SEED0", 0))
    pool = sorted(todo, key=lambda s: len(s["text"]))
    for attempt in range(NTRY):
        if not pool:
            break
        nxt = []
        for i in range(0, len(pool), BATCH):
            b = pool[i:i + BATCH]
            seed = 1000 + 7 * attempt + i + seed0
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, osr = m.generate_voice_clone(text=[s["text"] for s in b], language=["Chinese"] * len(b),
                                               voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8,
                                               max_new_tokens=int(36 + 5.0 * max(len(s["text"]) for s in b)))
            el = time.time() - t
            for s, x in zip(b, wavs):
                x = np.asarray(x, np.float32)
                f0 = f0_median(x, osr); dur = len(x) / osr
                nhan = len(re.findall(r"[一-鿿]", s["text"]))
                cps = nhan / max(dur, 0.1)
                ok = F0_LO <= f0 <= F0_HI and 2.6 <= cps <= 6.5
                cand = dict(seed=seed, f0=f0, dur=dur, cps=cps, ok=ok)
                old = best.get(s["id"])
                score = lambda c: (c["ok"], -abs(c["f0"] - 95))
                if old is None or score(cand) > score(old):
                    best[s["id"]] = cand
                    sf.write(f"{OUT}/{s['id']}.wav", x, osr)
                    json.dump(dict(id=s["id"], text=s["text"], **cand), open(f"{OUT}/{s['id']}.json", "w"), ensure_ascii=False)
                if not best[s["id"]]["ok"]:
                    nxt.append(s)
                print(f"try{attempt} {s['id']} f0={f0:.1f} dur={dur:.1f} cps={cps:.2f} ok={ok}", flush=True)
            print(f"  batch {len(b)} in {el:.0f}s", flush=True)
        pool = nxt
    print("DONE; still failing:", [s["id"] for s in pool], flush=True)


if __name__ == "__main__":
    main()
