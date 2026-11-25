"""Qwen3-TTS Base ICL clone of the Tocqueville designed voice, batched on CPU.
Per line: median F0 must be in [F0_LO, F0_HI]; lines failing are retried with new seeds (single).
usage: python tts_clone.py [ids...]   (env FORCE=1 to redo)
"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from qwen_tts import Qwen3TTSModel

OUT = "/tmp/claude-0/work/tts/raw"; os.makedirs(OUT, exist_ok=True)
REF_WAV = "/tmp/claude-0/work/voice/ref.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = 82.0, 108.0
BATCH = int(os.environ.get("BATCH", 4))
torch.set_num_threads(4)

def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0

def clean(s):
    return s.replace("「", "").replace("」", "").replace("“", "").replace("”", "").replace("《", "").replace("》", "")

def done(d):
    mp = f"{OUT}/{d['id']}.json"
    if os.environ.get("FORCE") or not os.path.exists(mp): return False
    j = json.load(open(mp)); return j.get("text") == d["say"] and j.get("ok", False)

def main():
    args = sys.argv[1:]
    lines = [d for d in all_lines() if (not args or any(d["id"].startswith(a) for a in args))]
    todo = [d for d in lines if not done(d)]
    print("todo", len(todo), flush=True)
    m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.bfloat16, device_map="cpu", attn_implementation="sdpa")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    def save(d, x, sr, seed, f0, ok):
        sf.write(f"{OUT}/{d['id']}.wav", x, sr)
        json.dump(dict(id=d["id"], seed=seed, f0=f0, dur=len(x)/sr, ok=ok, text=d["say"]), open(f"{OUT}/{d['id']}.json", "w"), ensure_ascii=False)
    retry = []
    # sort by length so batches are similar length
    todo.sort(key=lambda d: len(d["say"]))
    for i in range(0, len(todo), BATCH):
        b = todo[i:i+BATCH]; seed = 1000
        torch.manual_seed(seed); t = time.time()
        wavs, sr2 = m.generate_voice_clone(text=[clean(d["say"]) for d in b], language=["Chinese"]*len(b),
                                           voice_clone_prompt=prompt * len(b) if isinstance(prompt, list) else [prompt]*len(b),
                                           temperature=0.8, subtalker_temperature=0.8)
        for d, x in zip(b, wavs):
            x = np.asarray(x, np.float32); f0 = f0_median(x, sr2); ok = F0_LO <= f0 <= F0_HI and len(x)/sr2 < 1.2*len(d["say"])/2.5 + 3
            save(d, x, sr2, seed, f0, ok)
            print(f"{d['id']} f0={f0:.1f} dur={len(x)/sr2:.1f} ok={ok}", flush=True)
            if not ok: retry.append(d)
        print(f"batch {i//BATCH} {time.time()-t:.0f}s", flush=True)
    for d in retry:
        best = None
        for seed in [1007, 1014, 1021, 1028]:
            torch.manual_seed(seed)
            wavs, sr2 = m.generate_voice_clone(text=clean(d["say"]), language="Chinese", voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8)
            x = np.asarray(wavs[0], np.float32); f0 = f0_median(x, sr2); ok = F0_LO <= f0 <= F0_HI
            print(f"retry {d['id']} seed={seed} f0={f0:.1f} ok={ok}", flush=True)
            if best is None or abs(f0-95) < abs(best[2]-95): best = (x, seed, f0, ok)
            if ok: break
        save(d, best[0], sr2, best[1], best[2], best[3])

if __name__ == "__main__":
    main()
