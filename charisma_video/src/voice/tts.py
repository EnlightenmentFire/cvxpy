# -*- coding: utf-8 -*-
"""Clone the designed narrator voice with Qwen3-TTS Base and synthesize lines.
usage: python tts.py <base_model_dir> <ref_wav> <out_dir> <seg_id>[:<line_idx>,...] ...
"""
import sys, os, re, json, time
import numpy as np, torch, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
torch.set_num_threads(int(os.environ.get("TTS_THREADS", "4")))
from qwen_tts import Qwen3TTSModel
from pitch import med_f0
import script

REF_TEXT = "一九一九年一月，德国刚刚战败。慕尼黑，一位五十四岁的教授站在一群大学生面前，问了一个很老的问题：人，为什么会服从别人？"
DIG = "零一二三四五六七八九"

def num2zh(n):
    n = int(n)
    if n < 10: return DIG[n]
    if n < 20: return "十" + (DIG[n % 10] if n % 10 else "")
    if n < 100: return DIG[n // 10] + "十" + (DIG[n % 10] if n % 10 else "")
    if n < 1000:
        h, r = divmod(n, 100)
        s = DIG[h] + "百"
        if r == 0: return s
        if r < 10: return s + "零" + DIG[r]
        return s + (DIG[r // 10] + "十" + (DIG[r % 10] if r % 10 else ""))
    return "".join(DIG[int(d)] for d in str(n))

def to_tts(line):
    s = line.get("s") or line["t"]
    s = re.sub(r"(\d{4})\s*年", lambda m: "".join(DIG[int(d)] for d in m.group(1)) + "年", s)
    s = re.sub(r"\d+", lambda m: num2zh(m.group(0)), s)
    s = s.replace("——", "，").replace("……", "，").replace("·", "")
    s = s.replace(" ", "")
    return s

def main():
    base, ref, out = sys.argv[1:4]
    sel = sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    m = Qwen3TTSModel.from_pretrained(base, dtype=torch.bfloat16, device_map="cpu", attn_implementation="sdpa")
    prompt = m.create_voice_clone_prompt(ref_audio=ref, ref_text=REF_TEXT, x_vector_only_mode=False)
    segs = {s["id"]: s for s in script.SEGMENTS}
    meta_path = os.path.join(out, "meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for item in sel:
        sid, _, idxs = item.partition(":")
        lines = segs[sid]["lines"]
        idx = [int(i) for i in idxs.split(",")] if idxs else range(len(lines))
        for i in idx:
            ln = lines[i]
            if ln.get("k") == "en":
                continue
            text = to_tts(ln)
            best = None
            for attempt, seed in enumerate([1234, 777, 4242, 9001, 31337, 2024, 8888]):
                torch.manual_seed(seed)
                t0 = time.time()
                wavs, sr = m.generate_voice_clone(text=text, language="Chinese", voice_clone_prompt=prompt)
                fn = os.path.join(out, f"{sid}_{i:02d}.wav")
                tmp = fn + f".try{attempt}.wav"
                sf.write(tmp, wavs[0], sr)
                f0 = med_f0(tmp)
                dur = len(wavs[0]) / sr
                cps = len(text) / max(dur, 0.1)
                ok = 86.5 <= f0 <= 104 and 2.2 < cps < 7.5
                print(f"{sid}_{i:02d} try{attempt} seed{seed} f0={f0:.1f} dur={dur:.2f} cps={cps:.2f} {'OK' if ok else 'RETRY'} ({time.time()-t0:.0f}s)", flush=True)
                score = abs(f0 - 95) + (0 if 2.2 < cps < 7.5 else 100)
                if best is None or score < best[0]:
                    best = (score, tmp, f0, dur, seed)
                if ok:
                    break
            os.replace(best[1], fn)
            for f in os.listdir(out):
                if f.startswith(f"{sid}_{i:02d}.wav.try"):
                    os.remove(os.path.join(out, f))
            meta[f"{sid}_{i:02d}"] = dict(text=text, f0=best[2], dur=best[3], seed=best[4])
            json.dump(meta, open(meta_path, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
