import torch, time, soundfile as sf, sys
from transformers import AutoProcessor, MusicgenForConditionalGeneration
torch.set_num_threads(4)
name="facebook/musicgen-stereo-medium"
proc=AutoProcessor.from_pretrained(name); m=MusicgenForConditionalGeneration.from_pretrained(name)
prompt="tense cinematic pulse, low synth drone, heartbeat kick on every beat, rising staccato strings, building suspense then bright resolving chord, 115 bpm, no vocals"
inp=proc(text=[prompt],padding=True,return_tensors="pt")
for i in range(3):
    torch.manual_seed(11+i); t=time.time()
    a=m.generate(**inp,do_sample=True,guidance_scale=3.0,max_new_tokens=1510)
    sr=m.config.audio_encoder.sampling_rate
    sf.write(f"/tmp/claude-0/-home-user-cvxpy/fe4a820e-e082-5cd9-87f9-b1a5df450d7b/scratchpad/w/music/mg_{i}.wav",a[0].T.numpy(),sr)
    print(i,a.shape,sr,"took",round(time.time()-t),flush=True)
