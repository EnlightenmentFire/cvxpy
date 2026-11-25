import sys, glob, numpy as np, librosa, warnings; warnings.filterwarnings("ignore")
from transformers import pipeline
asr = pipeline("automatic-speech-recognition", model="openai/whisper-small.en", device="cpu")
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=16000)
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    st = 12*np.log2(f0/np.median(f0)) if len(f0) else np.array([0])
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=256)[0]; rdb = 20*np.log10(rms[rms>rms.max()*0.05]+1e-9)
    txt = asr(y.copy())["text"].strip()
    print(f"{f.split('/')[-2]:>10} {f.split('/')[-1]:<16} dur={len(y)/sr:5.2f} medF0={np.median(f0) if len(f0) else 0:5.0f} pitchRange(st p10-p90)={np.percentile(st,90)-np.percentile(st,10):4.1f} loudVar(dB sd)={rdb.std():4.1f} | {txt}")
