"""以 MusicGen 第 0 版为底，按画面节点剪辑并叠加层次；输出 music.wav 与节拍表。"""
import json, subprocess, numpy as np, soundfile as sf, librosa, scipy.signal as ss
SR=48000; V='voice/'; M='music/'
tl=json.load(open(V+'timeline.json'))
HIT=tl['s5a'][0]                      # 答案落下的重拍
y,sr=sf.read(M+'mg_0.wav'); m=y.mean(1)
_,bf=librosa.beat.beat_track(y=m,sr=sr,start_bpm=115); bt=librosa.frames_to_time(bf,sr=sr)
# 节拍线性拟合 → 精确拍长
k=np.arange(len(bt)); per,ph=np.polyfit(k,bt,1)
NB=32                                  # 开头到重拍 = 32 拍（8 小节）
r=HIT/(NB*per)                         # 轻微拉伸，使 32 拍正好等于 HIT
subprocess.run(['rubberband','-q','--fine','-t',f'{r:.6f}',M+'mg_0.wav',M+'mg_0_st.wav'],check=True)
y,sr=sf.read(M+'mg_0_st.wav'); y=librosa.resample(y.T,orig_sr=sr,target_sr=SR).T
P=per*r                                # 输出中的拍长
# 起点：原曲 5.5s 附近、落在拍点上
starts=ph*r+P*np.arange(-30,60); starts=starts[starts>0.5]; O=starts[np.argmin(abs(starts-5.6))]
NTOT=int(np.ceil((tl['voice_end']+1.75)/P)); END=NTOT*P   # 总长取整拍，循环时拍子接得上
n=int(round(END*SR)); t=np.arange(n)/SR
bed=y[int(O*SR):int(O*SR)+n]
if len(bed)<n: bed=np.pad(bed,((0,n-len(bed)),(0,0)))
beats=np.arange(NTOT)*P
print('bpm',60/P,'stretch',r,'offset',O,'END',END,'beats',NTOT)
F=lambda midi:440*2**((midi-69)/12)
def saw(f,tt,det=(0,-7,7)):
    out=0
    for c in det:
        ff=f*2**(c/1200); out=out+2*((tt*ff+np.random.rand())%1)-1
    return out/len(det)
def lp(x,fc,o=2): b,a=ss.butter(o,fc/(SR/2)); return ss.lfilter(b,a,x)
def hp(x,fc,o=2): b,a=ss.butter(o,fc/(SR/2),'high'); return ss.lfilter(b,a,x)
rng=np.random.default_rng(0)
# --- 弦乐短音型：9 秒起（s3a），八分音符，F 小调主和弦；13 秒起加高八度
strings=np.zeros(n)
pat=[53,60,56,60, 53,60,56,63]      # F3 C4 Ab3 C4 F3 C4 Ab3 Eb4
t0=tl['s3a'][0]
for i in range(int(NB*2)):
    st=i*P/2
    if st<t0-0.01 or st>=HIT-0.02: continue
    prog=(st-t0)/(HIT-t0)
    for oct_,thr in ((0,0),(12,0.45)):
        if prog<thr: continue
        note=pat[i%8]+oct_; L=int(0.22*SR); s=int(st*SR); e=min(n,s+L); tt=np.arange(e-s)/SR
        env=np.minimum(1,tt/0.006)*np.exp(-tt/0.075)
        g=(0.10+0.16*prog)*(0.7 if oct_ else 1.0)
        strings[s:e]+=g*env*saw(F(note),tt)
strings=lp(hp(strings,120),2600)
# --- 冲刺 riser：HIT 前 1.6 秒，噪声 + 上行
ris=np.zeros(n); s=int((HIT-1.6)*SR); e=int(HIT*SR); tt=np.arange(e-s)/SR
noise=rng.standard_normal(e-s); u=tt/1.6
sweep=np.zeros(e-s)
for j in range(e-s): pass
bnoise=hp(noise,800)*(u**2.2)*0.22
tone=np.sin(2*np.pi*np.cumsum(F(65)*(1+u*1.0))/SR)*(u**2)*0.12
ris[s:e]=bnoise+tone
# --- 重拍：低频轰 + 噪声击打
hit=np.zeros(n); s=int(HIT*SR); L=int(2.2*SR); tt=np.arange(L)/SR
f_sw=40+80*np.exp(-tt/0.06); boom=np.sin(2*np.pi*np.cumsum(f_sw)/SR)*np.exp(-tt/0.55)*0.9
crack=lp(hp(rng.standard_normal(L),300),5000)*np.exp(-tt/0.09)*0.35
hit[s:s+L]=(boom+crack)[:n-s]
# --- 长和弦：F 大调加九（明亮的「原来如此」），托到最后一帧
pad=np.zeros(n); s=int(HIT*SR); tt=np.arange(n-s)/SR
chord=[41,53,60,65,69,67,72]          # F2 F3 C4 F4 A4 G4 C5
amps=[0.30,0.24,0.18,0.15,0.13,0.08,0.08]
sig=sum(a*saw(F(c),tt,det=(0,-9,9,-4)) for c,a in zip(chord,amps))
env=np.minimum(1,tt/0.03)*(0.75+0.25*np.exp(-tt/0.6))
pad[s:]=lp(sig,1700,3)*env*(1+0.05*np.sin(2*np.pi*0.5*tt))*1.05
# --- 尾段心跳鼓：保持拍子，接回开头
kick=np.zeros(n)
for b in beats:
    if b<HIT+P-0.01: continue
    s=int(b*SR); L=int(0.35*SR); tt=np.arange(min(L,n-s))/SR
    kick[s:s+len(tt)]+=np.sin(2*np.pi*np.cumsum(50+60*np.exp(-tt/0.03))/SR)*np.exp(-tt/0.16)*0.6
# --- 底：答案后底曲淡出（让长和弦接手）
g=np.ones(n); s=int((HIT+0.05)*SR); L=int(1.4*SR); g[s:s+L]=np.linspace(1,0.3,L); g[s+L:]=0.3
# 答案前空拍底曲上推 +3dB
s0=int(tl['s4'][1]*SR); g[s0:int(HIT*SR)]*=np.linspace(1,1.4,int(HIT*SR)-s0)
out=bed*g[:,None]
mono=strings+ris+hit+pad+kick
out[:,0]+=mono*1.0; out[:,1]+=mono*1.0
# 防咔：开头 0.12s 淡入（≤0.3s），结尾 25ms 微淡出
fi=int(0.12*SR); out[:fi]*=np.linspace(0,1,fi)[:,None]; fo=int(0.025*SR); out[-fo:]*=np.linspace(1,0,fo)[:,None]
out/=np.max(np.abs(out))/0.9
sf.write(M+'music.wav',out.astype(np.float32),SR,subtype='FLOAT')
tl['end']=round(END,4); tl['beats']=[round(b,4) for b in beats]; tl['music']=dict(src='mg_0',offset=round(O,3),stretch=round(r,5),bpm=round(60/P,2))
json.dump(tl,open(V+'timeline_final.json','w'),indent=1)
# 首尾电平对比
a=out[:int(1.0*SR)]; z=out[-int(1.0*SR):]
print('first 1s RMS dB',20*np.log10(np.sqrt((a**2).mean())),'last 1s',20*np.log10(np.sqrt((z**2).mean())))
