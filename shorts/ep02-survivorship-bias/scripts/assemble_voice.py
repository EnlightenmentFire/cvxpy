import json, subprocess, numpy as np, soundfile as sf, librosa, scipy.signal as ss, parselmouth
PICK={"s1":"raw_s1_2","s2":"raw_s2_2","s3a":"raw_s3a_3","s3b":"raw_s3b_6","s4":"raw_s4_3","s5a":"raw_s5a_3","s5b":"raw_s5b_3"}
STRETCH={"s5a":1.12}   # 答案句放慢一点、重一点
GAP={"s1":0.20,"s2":0.22,"s3a":0.14,"s3b":0.22,"s4":0.70,"s5a":0.24}
SR=48000; V="voice/"
out=[]; tl={}; t=0.0
for k in ["s1","s2","s3a","s3b","s4","s5a","s5b"]:
    f=V+PICK[k]+".wav"
    if k in STRETCH:
        subprocess.run(["rubberband","-q","-F","--fine","-t",str(STRETCH[k]),f,V+f"st_{k}.wav"],check=True); f=V+f"st_{k}.wav"
    y,sr=sf.read(f); y=y if y.ndim==1 else y.mean(1)
    y=librosa.resample(y,orig_sr=sr,target_sr=SR)
    _,(a,b)=librosa.effects.trim(y,top_db=40,frame_length=1024,hop_length=128)
    a=max(0,a-int(0.012*SR)); b=min(len(y),b+int(0.06*SR)); y=y[a:b]
    fi=int(0.004*SR); fo=int(0.03*SR); y[:fi]*=np.linspace(0,1,fi); y[-fo:]*=np.linspace(1,0,fo)
    tl[k]=[round(t,3),round(t+len(y)/SR,3)]
    out.append(y); t+=len(y)/SR
    if k in GAP: out.append(np.zeros(int(GAP[k]*SR))); t+=GAP[k]
v=np.concatenate(out)
b,a=ss.butter(2,50/(SR/2),'high'); v=ss.lfilter(b,a,v)
# 人声统一到约 -18 dBFS RMS（只算有声段）
act=v[np.abs(v)>1e-3]; rms=np.sqrt(np.mean(act**2)); v*=10**(-18/20)/rms
pk=np.max(np.abs(v)); 
if pk>0.97: v*=0.97/pk
sf.write(V+"voice.wav",v.astype(np.float32),SR,subtype="FLOAT")
tl["voice_end"]=round(t,3)
json.dump(tl,open(V+"timeline.json","w"),indent=1)
print(tl, "peak", round(20*np.log10(np.max(np.abs(v))),1))
for k,(s,e) in tl.items() if False else []: pass
for k in PICK:
    s,e=tl[k]; seg=v[int(s*SR):int(e*SR)]
    p=parselmouth.Sound(seg,SR).to_pitch(pitch_floor=60,pitch_ceiling=300).selected_array['frequency']; p=p[p>0]
    print(k, "F0 median", round(float(np.median(p)),1), "dur", round(e-s,2))
