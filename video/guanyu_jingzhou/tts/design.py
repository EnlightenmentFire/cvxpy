import sys, time, torch, soundfile as sf, numpy as np, parselmouth, warnings
warnings.filterwarnings('ignore')
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
def f0(w,sr):
    s=parselmouth.Sound(w.astype(np.float64),sr); f=s.to_pitch_ac(time_step=0.01,pitch_floor=60,pitch_ceiling=400).selected_array['frequency']; f=f[f>0]
    return round(float(np.median(f)),1), round(float(np.percentile(f,10)),1), round(float(np.percentile(f,90)),1)
TXT="建安二十四年，冬。江陵的城门，从里面打开了。一个人的选择，改变了一个集团的命运。"
D={'C':"四十多岁的男中音，音色醇厚、偏低沉，吐字清晰。以历史纪录片旁白的方式娓娓道来，语气凝重、克制，略带惋惜，语速中等偏慢，有自然的抑扬和停顿，句尾下沉，不激昂，不兴奋。",
   'D':"成熟稳重的男声，中低音，温厚有磁性。讲述一段沉重的历史，庄重、冷静、有分量，带一点叹息感，节奏从容，语调自然不平板，绝不高亢。",
   'E':"男性纪录片解说，声音沉稳厚实，音调中等偏低，语气严肃而平静，像在复盘一场失败，娓娓道来，自然流畅。"}
for k,ins in D.items():
    for seed in (1,2):
        torch.manual_seed(seed); t=time.time()
        wavs,sr=model.generate_voice_design(text=TXT,language="Chinese",instruct=ins)
        sf.write(f'ref/{k}{seed}.wav',wavs[0],sr)
        print('REF',k,seed,f0(wavs[0],sr),round(len(wavs[0])/sr,2),round(time.time()-t),flush=True)
