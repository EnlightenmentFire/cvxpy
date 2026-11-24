import sys, os, time, torch, soundfile as sf
sys.path.insert(0,'/home/user/work/vid')
from script import BEATS, say_text
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", device_map="cpu", dtype=torch.float32)
INS="像新闻联播男主播一样，严肃、干练、语速较快地播报。"
only=sys.argv[1:]
for b in BEATS:
    if only and b['id'] not in only: continue
    out=f"wav/{b['id']}.wav"
    if os.path.exists(out) and not only: continue
    t=time.time(); torch.manual_seed(1234 if not only else int(time.time())%100000)
    wavs, sr = model.generate_custom_voice(text=say_text(b), language="Chinese", speaker="Uncle_Fu", instruct=INS)
    sf.write(out, wavs[0], sr)
    print(b['id'], round(len(wavs[0])/sr,2), round(time.time()-t,1), flush=True)
print('ALLDONE', flush=True)
