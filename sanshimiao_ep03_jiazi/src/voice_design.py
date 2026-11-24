"""Design a reference narrator voice with Qwen3-TTS VoiceDesign (no real person cloned).
Generates N candidates, measures median F0 (parselmouth), keeps the one nearest the target."""
import json, os, sys, time
import numpy as np, soundfile as sf, torch, parselmouth

INSTRUCT = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏快"
REF_TEXT = "为什么六十年，一个甲子？一九八四年是甲子年，下一个甲子年，要等到二零四四年。十和十二，最小公倍数是六十。"


def median_f0(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = p.selected_array["frequency"]; f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


def main(out, seeds, target=90.0):
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.bfloat16)
    rows = []
    for s in seeds:
        torch.manual_seed(s); np.random.seed(s)
        t0 = time.time()
        wavs, sr = m.generate_voice_design(text=REF_TEXT, instruct=INSTRUCT, language="Chinese")
        w = np.asarray(wavs[0], np.float32)
        p = os.path.join(out, f"design_seed{s}.wav"); sf.write(p, w, sr)
        rows.append(dict(seed=s, path=p, f0=round(median_f0(w, sr), 1), dur=round(len(w) / sr, 2), sr=sr, gen_s=round(time.time() - t0, 1)))
        print(rows[-1], flush=True)
    best = min(rows, key=lambda r: abs(r["f0"] - target))
    json.dump(dict(instruct=INSTRUCT, ref_text=REF_TEXT, candidates=rows, chosen=best), open(os.path.join(out, "design.json"), "w"), ensure_ascii=False, indent=1)
    print("chosen", best)


if __name__ == "__main__":
    main(sys.argv[1], [int(x) for x in sys.argv[2].split(",")])
