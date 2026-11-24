# 把逐句配音排上时间轴 → timings.js；合成配乐与音效（全部自制，numpy 合成）；混音输出 build/mix.wav
import sys, os, re, json, math
import numpy as np, soundfile as sf
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)
from script import S
SR=48000
SEG=os.path.join(ROOT,'audio',os.environ.get('VOICE','seg_A'))
START=0.9; GAP=0.27; GAP_Q=0.40; CH_GAP=2.6
EXTRA={'c0_2':1.3,'c6_6':.5,'c6_13':1.3,'c7_1':.9,'c7_2':.9,'c7_3':1.6}
TAIL=5.5

def load(i,est):
    f=f'{SEG}/{i}.wav'
    if not os.path.exists(f):
        print('MISSING',i); return np.zeros(int(est*SR),np.float32)
    w,sr=sf.read(f,dtype='float32')
    if w.ndim>1: w=w.mean(1)
    w=resample_poly(w,SR,sr).astype(np.float32)
    env=np.abs(w); th=max(0.012,env.max()*0.03)
    idx=np.where(env>th)[0]
    a=max(0,idx[0]-int(.04*SR)); b=min(len(w),idx[-1]+int(.09*SR))
    w=w[a:b]; n=int(.01*SR); w[:n]*=np.linspace(0,1,n); w[-n:]*=np.linspace(1,0,n)
    return w

# ── 1. 旁白时间轴 ──
t=START; tim={}; segs=[]; prev=None
for i,c,k,txt,tts in S:
    if prev is not None and c!=prev: t+= (CH_GAP if c!='c7' else 0.6)
    if k=='s' and prev==c: t+=0.15
    est=len(re.findall(r'[一-鿿〇]',txt))/4.8
    w=load(i,est); d=len(w)/SR
    tim[i]=[round(t,3),round(t+d,3)]; segs.append((t,w,c))
    t+=d+(GAP_Q if k=='q' else GAP)+EXTRA.get(i,0); prev=c
total=t+TAIL; tim['_end']=[round(total,3),round(total,3)]
open(os.path.join(HERE,'timings.js'),'w').write('window.TIM='+json.dumps(tim)+';')
json.dump(tim,open(os.path.join(ROOT,'build','timings.json'),'w'))
N=int(total*SR)+SR
narr=np.zeros(N,np.float32)
for t0,w,c in segs:
    a=int(t0*SR); narr[a:a+len(w)]+=w
# 旁白：轻度压缩 + 归一
def rms(x): return float(np.sqrt(np.mean(x**2)+1e-12))
act=np.abs(narr)>0.01
narr/= (rms(narr[act])/0.11)
narr=np.tanh(narr*1.15)/1.15
print('total %.1fs  (%d:%04.1f)'%(total,total//60,total%60))

# ── 2. 配乐 ──
rng=np.random.default_rng(1881)
def pluck(freq,dur,bright=1.0):
    n=int(dur*SR); tt=np.arange(n)/SR; out=np.zeros(n)
    for h_ in range(1,13):
        f=freq*h_*(1+0.0004*h_*h_)
        if f>9000: break
        amp=(1/h_**1.25)*(0.6+0.4*math.sin(h_*1.7)**2)*bright**(h_-1)
        out+=amp*np.exp(-tt*(0.9+0.55*h_))*np.sin(2*np.pi*f*tt+rng.uniform(0,6.28))
    att=np.minimum(1,tt/0.004); out*=att
    out[:int(.012*SR)]+=rng.normal(0,.25,int(.012*SR))*np.linspace(1,0,int(.012*SR))
    return out
def bell(freq,dur):
    n=int(dur*SR); tt=np.arange(n)/SR; out=np.zeros(n)
    for r,a,dc in [(1,1,.7),(2.0,.5,1.0),(2.76,.35,1.4),(5.4,.2,2.2),(0.5,.5,.5)]:
        out+=a*np.exp(-tt*dc)*np.sin(2*np.pi*freq*r*tt)
    return out*np.minimum(1,tt/0.01)
def thud():
    n=int(.35*SR); tt=np.arange(n)/SR
    f=np.linspace(95,42,n); ph=2*np.pi*np.cumsum(f)/SR
    o=np.sin(ph)*np.exp(-tt*13)
    nz=rng.normal(0,1,n)*np.exp(-tt*60)*.35
    sos=butter(2,1800,'low',fs=SR,output='sos'); return o+sosfilt(sos,nz)
P={'D2':73.42,'A2':110.0,'D3':146.83,'F3':174.61,'G3':196.0,'A3':220.0,'C4':261.63,'D4':293.66,'F4':349.23,'G4':392.0,'A4':440.0,'C5':523.25,'D5':587.33}
SCALE=['D3','F3','G3','A3','C4','D4','F4','G4','A4','C5','D5']
L=np.zeros(N); R=np.zeros(N)
def add(buf,t0,pan=0.5,g=1.0):
    a=int(t0*SR)
    if a>=N or a<0: return
    b=min(N,a+len(buf)); L[a:b]+=buf[:b-a]*g*math.cos(pan*math.pi/2); R[a:b]+=buf[:b-a]*g*math.sin(pan*math.pi/2)
# 每章的起止时间
chs=['c0','c1','c2','c3','c4','c5','c6','c7']
first={c:min(tim[s[0]][0] for s in S if s[1]==c) for c in chs}
last={c:max(tim[s[0]][1] for s in S if s[1]==c) for c in chs}
# 各章性格：(每小节音符数范围, 音区下标范围, 步长秒, 低音脉冲)
MOOD={'c0':((1,2),(0,4),4.0,False),'c1':((2,3),(1,7),4.0,False),'c2':((3,4),(4,10),3.2,False),'c3':((2,3),(1,7),3.6,True),
      'c4':((1,3),(2,8),4.4,False),'c5':((3,4),(4,10),3.0,False),'c6':((2,3),(0,6),3.6,True),'c7':((1,2),(1,6),4.8,False)}
for ci,c in enumerate(chs):
    t0=first[c]-(2.4 if c not in('c0','c7') else 0.5); t1=(first[chs[ci+1]]-2.6) if ci+1<len(chs) else total-1.5
    (n0,n1),(lo,hi),bar,pulse=MOOD[c]; idx=rng.integers(lo,hi); tb=t0
    while tb<t1-1:
        k=rng.integers(n0,n1+1); slots=sorted(rng.choice(8,size=k,replace=False))
        for sl in slots:
            idx=int(np.clip(idx+rng.choice([-2,-1,-1,1,1,2,3,-3]),lo,hi))
            f=P[SCALE[idx]]; add(pluck(f,3.2,0.9),tb+sl*bar/8+rng.uniform(-.015,.015),pan=rng.uniform(.3,.7),g=rng.uniform(.5,.85))
            if rng.random()<.18: add(pluck(f*1.5 if SCALE[idx][0] in 'DGA' else f*2,2.6,0.85),tb+sl*bar/8+bar/16,pan=rng.uniform(.2,.8),g=.35)
        add(pluck(P['D2']*(1 if rng.random()<.7 else 1.5),4.5,0.8),tb,pan=.5,g=.75)
        if pulse:
            for q in range(2): add(thud()*0.5,tb+q*bar/2,pan=.5,g=.5)
        tb+=bar
    if c not in('c0','c7'): add(bell(P['D3'],5.0),first[c]-2.4,pan=.5,g=.55)
add(bell(P['D2']*2,6.0),0.15,pan=.5,g=.5)
add(pluck(P['D3'],6,0.9),total-5.5,g=.9); add(pluck(P['A3'],6,0.9),total-5.4,g=.6); add(pluck(P['D4'],6,0.9),total-5.3,g=.5)
# 持续低音
tt=np.arange(N)/SR
dr=np.zeros(N)
for f,a,lf in [(73.42,.5,.07),(110.0,.3,.05),(146.83,.22,.09),(220.3,.08,.11)]:
    dr+=a*np.sin(2*np.pi*f*tt)*(0.6+0.4*np.sin(2*np.pi*lf*tt+f))
dr*=0.16
L+=dr; R+=dr*0.97
# 混响
irn=int(2.8*SR); ti=np.arange(irn)/SR
sos=butter(2,3500,'low',fs=SR,output='sos')
irL=sosfilt(sos,rng.normal(0,1,irn))*np.exp(-ti*2.3); irR=sosfilt(sos,rng.normal(0,1,irn))*np.exp(-ti*2.3)
irL/=np.sqrt((irL**2).sum()); irR/=np.sqrt((irR**2).sum())
L=L+0.55*fftconvolve(L,irL)[:N]; R=R+0.55*fftconvolve(R,irR)[:N]
mus=np.stack([L,R],1).astype(np.float32)
sos=butter(2,[45,7000],'band',fs=SR,output='sos'); mus=sosfilt(sos,mus,axis=0)
mus/= rms(mus)/0.05
# 闪避：旁白时压低
env=np.zeros(N);
for t0,w,c in segs: env[max(0,int((t0-.25)*SR)):int((t0+len(w)/SR+.3)*SR)]=1
k=int(.5*SR); ker=np.hanning(k); ker/=ker.sum(); env=fftconvolve(env,ker,mode='same')
gain=0.62-0.40*env        # 间隙 0.62，旁白下 0.22
fade=np.minimum(1,tt/1.5)*np.clip((total-tt)/2.5,0,1)
mus*= (gain*fade)[:,None]

# ── 3. 音效：盖章 ──
sfx=np.zeros((N,2),np.float32)
def C(i): return tim[i][0]
def CE(i): return tim[i][1]
def hit(t0,g=1.0):
    b=thud(); a=int(t0*SR)
    if a+len(b)<N: sfx[a:a+len(b),0]+=b*g; sfx[a:a+len(b),1]+=b*g
hit(C('c0_2')+.55+.2,1.0)
for c in ['c1','c2','c3','c4','c5','c6']: hit(first[c]-2.5+.15+.2,.7)
d=CE('c0_4')-C('c0_4')
for i in range(3): hit(C('c0_4')+d*.42+i*.18+.2,.5)
hit(C('c1_2')+.25+.2,.8)
cd=CE('c2_6')-C('c2_6'); hit(C('c2_6')+cd*.2+.2,.7)
pd=CE('c3_5')-C('c3_5'); hit(C('c3_5')+pd*.84+.2,.7)
pd=CE('c6_5')-C('c6_5'); hit(C('c6_5')+pd*.74+.2,.9)
dd=CE('c6_10')-C('c6_10'); hit(C('c6_10')+dd*.36+.2,.9)
hit(C('c7_3')-.1+1.3+.2,1.1)
sfx*=0.16

mix=np.stack([narr,narr],1)+mus+sfx
pk=np.abs(mix).max();
if pk>0.97: mix*=0.97/pk
os.makedirs(os.path.join(ROOT,'build'),exist_ok=True)
sf.write(os.path.join(ROOT,'build','mix.wav'),mix[:int(total*SR)],SR,subtype='PCM_16')
sf.write(os.path.join(ROOT,'build','music_only.wav'),(mus+sfx)[:int(total*SR)],SR,subtype='PCM_16')
print('narr rms %.3f  music rms under speech %.4f  in gaps %.4f'%(rms(narr[act]),rms(mus[env>.9]),rms(mus[(env<.1)&(tt>2)&(tt<total-3)])))
