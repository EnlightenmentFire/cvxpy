"""Qwen3-TTS Base ICL clone of the 托克维尔 designed voice. usage: python tts_run.py WORKER NWORKERS [ids...] [--force]"""
import sys, os, json, time
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
from qwen_tts import Qwen3TTSModel
OUT = "/tmp/claude-0/w74/tts/raw"
REF_WAV = "/tmp/claude-0/w74/voice/ref.wav"
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
torch.set_num_threads(int(os.environ.get("NT", 2)))

def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0

def main():
    wk, nw = int(sys.argv[1]), int(sys.argv[2])
    ids = [a for a in sys.argv[3:] if not a.startswith("--")]
    force = "--force" in sys.argv
    lines = all_lines()
    if ids: lines = [d for d in lines if any(d["id"].startswith(a) for a in ids)]
    lines = [d for i, d in enumerate(lines) if i % nw == wk]
    m = Qwen3TTSModel.from_pretrained("/tmp/claude-0/models/Qwen3-TTS-12Hz-1.7B-Base", dtype=torch.bfloat16, device_map="cpu")
    w, sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(w.astype(np.float32), sr), ref_text=REF_TEXT)
    for d in lines:
        meta = f"{OUT}/{d['id']}.json"
        text = tts_text(d["say"])
        if os.path.exists(meta) and not force and json.load(open(meta)).get("text") == text:
            continue
        seed = int(os.environ.get("SEED", 1000)) + (7 if force and "SEED" not in os.environ else 0)
        torch.manual_seed(seed); np.random.seed(seed)
        t = time.time()
        wavs, sr2 = m.generate_voice_clone(text=text, language="Chinese", voice_clone_prompt=prompt, temperature=0.8, subtalker_temperature=0.8)
        x = wavs[0].astype(np.float32)
        f0 = f0_median(x, sr2)
        sf.write(f"{OUT}/{d['id']}.wav", x, sr2)
        json.dump(dict(id=d["id"], seed=seed, f0=f0, dur=len(x) / sr2, text=text, gen=time.time() - t), open(meta, "w"), ensure_ascii=False)
        print(f"{d['id']} f0={f0:.1f} dur={len(x)/sr2:.1f} gen={time.time()-t:.0f}s", flush=True)

if __name__ == "__main__":
    main()
