"""Narration: Qwen3-TTS-12Hz-1.7B-Base cloning the VoiceDesign reference (seed 11).
Per line: generate -> median F0 must be 85-105 Hz -> ASR pinyin read-back must be exact -> else new seed.
Keeps every take; writes the chosen take per line + a jsonl log.
Usage: python tts_lines.py lines.json ref.wav out_dir [ids]"""
import json, os, sys, time, zlib
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(__file__))
import asrcheck as A
from voice_design import median_f0, REF_TEXT

MAX_TRY = int(os.environ.get("MAX_TRY", "6"))


def main():
    lines = json.load(open(sys.argv[1]))
    ref, out = sys.argv[2], sys.argv[3]
    only = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else None
    os.makedirs(out + "/takes", exist_ok=True)
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.bfloat16)
    prompt = m.create_voice_clone_prompt(ref_audio=ref, ref_text=REF_TEXT)
    log = open(out + "/tts_log.jsonl", "a")
    for L in lines:
        if only and L["id"] not in only:
            continue
        best = None
        for att in range(MAX_TRY):
            seed = (zlib.crc32(L["id"].encode()) + att * 7919) % 100000
            torch.manual_seed(seed); np.random.seed(seed)
            t0 = time.time()
            wavs, sr = m.generate_voice_clone(text=L["tts"], language="Chinese", voice_clone_prompt=prompt)
            a = np.asarray(wavs[0], np.float32)
            f0 = median_f0(a, sr)
            hyp = A.transcribe(a, sr)
            err = A.per(L["tts"], hyp)
            nch = len(A.norm_py(L["tts"])[0])
            dur = len(a) / sr
            ok = 85 <= f0 <= 105 and err == 0.0
            rec = dict(id=L["id"], att=att, seed=seed, f0=round(f0, 1), err=round(err, 3), dur=round(dur, 2),
                       cps=round(nch / dur, 2), asr=hyp, ok=ok, gen_s=round(time.time() - t0, 1))
            print(json.dumps(rec, ensure_ascii=False), flush=True)
            log.write(json.dumps(rec, ensure_ascii=False) + "\n"); log.flush()
            sf.write(f"{out}/takes/{L['id']}_s{seed}.wav", a, sr)
            key = (0 if ok else 1, err, abs(f0 - 95))
            if best is None or key < best[0]:
                best = (key, a, sr, rec)
            if ok:
                break
        sf.write(f"{out}/{L['id']}.wav", best[1], best[2])
        print("CHOSEN", json.dumps(best[3], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
