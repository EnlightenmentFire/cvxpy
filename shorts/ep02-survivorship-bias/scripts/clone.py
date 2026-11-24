import torch, soundfile as sf, time, sys, json
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
O="/tmp/claude-0/-home-user-cvxpy/fe4a820e-e082-5cd9-87f9-b1a5df450d7b/scratchpad/w/voice/"
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32, attn_implementation="sdpa")
ref_text = "二战的时候，军方统计飞回来的轰炸机，打算在弹孔多的地方加装甲。统计学家的思路正好反过来。"
prompt = m.create_voice_clone_prompt(ref_audio=O+"design_5.wav", ref_text=ref_text)
S = json.load(open(O+"../scripts/lines.json"))
which = sys.argv[1].split(",") if len(sys.argv)>1 else list(S)
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv)>2 else [1,2,3]
for k in which:
    for sd in seeds:
        torch.manual_seed(sd)
        t=time.time()
        w, sr = m.generate_voice_clone(text=S[k], language="Chinese", voice_clone_prompt=prompt, do_sample=True)
        sf.write(f"{O}raw_{k}_{sd}.wav", w[0], sr)
        print(k, sd, round(len(w[0])/sr,2), "s took", round(time.time()-t,1), flush=True)
