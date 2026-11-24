# -*- coding: utf-8 -*-
"""用 Qwen3-TTS VoiceDesign 按文字描述设计参考音（不克隆任何真人）：出 3 个候选，量中位音高，选最接近 90 Hz 的。
用法：python tools/qwen_design.py out_dir"""
import sys, os, json, time, warnings, numpy as np, soundfile as sf, torch, parselmouth
warnings.filterwarnings('ignore'); torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
DESC = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
REF_TXT = "公元五四六年冬，山西南部的小城玉璧。高欢带着整个东方来打这座小城，五十天后回去，第二年就死了。"


def f0(w, sr):
    s = parselmouth.Sound(w.astype(np.float64), sr)
    f = s.to_pitch_ac(time_step=0.01, pitch_floor=55, pitch_ceiling=350).selected_array['frequency']; f = f[f > 0]
    return round(float(np.median(f)), 1), round(float(np.percentile(f, 10)), 1), round(float(np.percentile(f, 90)), 1)


model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
res = []
for seed in (11, 23, 37):
    torch.manual_seed(seed); t0 = time.time()
    wavs, sr = model.generate_voice_design(text=REF_TXT, language="Chinese", instruct=DESC)
    w = wavs[0]; p = f"{OUT}/cand_{seed}.wav"; sf.write(p, w, sr)
    med, p10, p90 = f0(w, sr); res.append(dict(seed=seed, path=p, med=med, p10=p10, p90=p90, dur=round(len(w) / sr, 2), sr=sr))
    print('CAND', seed, med, p10, p90, round(len(w) / sr, 2), 's', round(time.time() - t0), 'sec', flush=True)
best = min(res, key=lambda r: abs(r['med'] - 90))
json.dump(dict(desc=DESC, ref_text=REF_TXT, cands=res, chosen=best), open(f"{OUT}/design.json", "w"), ensure_ascii=False, indent=1)
print('CHOSEN', best)
