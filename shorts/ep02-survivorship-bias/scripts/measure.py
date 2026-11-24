import json, numpy as np, soundfile as sf, pyloudnorm as pyln
tl=json.load(open('voice/timeline_final.json'))
v,sr=sf.read('voice/voice_st.wav'); m,_=sf.read('music/ducked.wav'); meter=pyln.Meter(sr,block_size=0.4)
def L(x): return meter.integrated_loudness(x)
d=[]
for k in ['s1','s2','s3a','s3b','s5a','s5b']:
    a,b=(int(x*sr) for x in tl[k]); d.append(L(v[a:b])-L(m[a:b])); print(k,round(d[-1],1),end='; ')
a,b=int(tl['s4'][1]*sr),int(tl['s5a'][0]*sr)
print('\nmean voice-music LU',round(np.mean(d),1),'| music in gap',round(L(m[a-int(.3*sr):b]),1),'LUFS, music under s2',round(L(m[int(tl['s2'][0]*sr):int(tl['s2'][1]*sr)]),1))
