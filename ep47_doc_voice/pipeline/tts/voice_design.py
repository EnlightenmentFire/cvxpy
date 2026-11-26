"""Step 1 of the voice pipeline: design a narrator voice from a text description
(Qwen3-TTS VoiceDesign, Apache-2.0), make several candidates with different seeds,
and measure each candidate's median pitch with Praat (parselmouth)."""
import sys, json, time, torch, numpy as np, soundfile as sf, parselmouth
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
out_dir = sys.argv[1]
seeds = [int(s) for s in sys.argv[2].split(",")]
INSTRUCT = "四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"
REF_TEXT = ("一九零六年，英国普利茅斯的一个牲畜展览会上，有人办了一场猜牛重量的比赛。"
            "将近八百个人，各自写下自己的答案，谁也看不见别人写了什么。")
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu",
                                  dtype=torch.bfloat16, attn_implementation="sdpa")
def median_f0(wav, sr):
    snd = parselmouth.Sound(wav.astype(np.float64), sampling_frequency=sr)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=300)
    f = pitch.selected_array["frequency"]; f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0
res = []
for s in seeds:
    torch.manual_seed(s); np.random.seed(s)
    t0 = time.time()
    wavs, sr = m.generate_voice_design(text=REF_TEXT, instruct=INSTRUCT, language="Chinese")
    w = wavs[0]
    f0 = median_f0(w, sr)
    path = f"{out_dir}/cand_seed{s}.wav"
    sf.write(path, w, sr)
    r = dict(seed=s, path=path, median_f0=round(f0, 1), dur=round(len(w)/sr, 2), gen_s=round(time.time()-t0, 1))
    print(json.dumps(r, ensure_ascii=False), flush=True)
    res.append(r)
json.dump(dict(instruct=INSTRUCT, ref_text=REF_TEXT, candidates=res), open(f"{out_dir}/candidates.json", "w"), ensure_ascii=False, indent=1)
