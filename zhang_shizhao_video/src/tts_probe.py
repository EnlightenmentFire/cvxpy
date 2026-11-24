import sys, numpy as np, soundfile as sf, torch, time, glob, os
from kokoro import KPipeline, KModel
from huggingface_hub import list_repo_files
REPO='hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval()
pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)
text = "一九二六年三月，北京。平政院的一份裁决书上，写着这样一行字：教育部之处分取消之。"
voices = sorted(f[7:-3] for f in list_repo_files(REPO) if f.startswith('voices/zm'))
os.makedirs('build/probe', exist_ok=True)
import librosa
for v in voices:
    t=time.time()
    wavs=[r.audio.numpy() for r in pipe(text, voice=v, speed=1.0)]
    w=np.concatenate(wavs)
    sf.write(f'build/probe/{v}.wav', w, 24000)
    f0,_,_ = librosa.pyin(w, fmin=60, fmax=300, sr=24000)
    f0=f0[~np.isnan(f0)]
    print(v, f"dur={len(w)/24000:.2f}s f0med={np.median(f0):.0f} f0std={np.std(f0):.0f} rt={time.time()-t:.1f}s", flush=True)
