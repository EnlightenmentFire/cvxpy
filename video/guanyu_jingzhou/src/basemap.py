import numpy as np, math, json
from PIL import Image
from scipy import ndimage as ndi
D='/home/user/work/dem/'
def ramp(h):
    stops=[(-50,(30,40,48)),(0,(44,54,50)),(60,(50,60,52)),(250,(66,72,58)),(700,(92,88,66)),(1500,(122,108,82)),(2600,(146,130,104)),(4000,(170,160,144)),(5500,(205,202,196))]
    xs=[s[0] for s in stops]; out=np.zeros(h.shape+(3,),np.float32)
    for c in range(3): out[...,c]=np.interp(h,xs,[s[1][c] for s in stops])
    return out
def shade(H,z,exag):
    # meters per pixel at ~31N
    mpp=156543.03*math.cos(math.radians(31))/2**z
    gy,gx=np.gradient(H*exag/mpp)
    def hs(az,alt=45):
        az=math.radians(az); alt=math.radians(alt)
        lx=math.sin(az)*math.cos(alt); ly=-math.cos(az)*math.cos(alt); lz=math.sin(alt)
        n=np.sqrt(gx*gx+gy*gy+1)
        return np.clip((-gx*lx- gy*ly*-1*-1+lz)/n,0,1) if False else np.clip((-gx*lx+gy*ly*-1+lz)/n,0,1)
    s=0.6*hs(315)+0.25*hs(270)+0.15*hs(0)
    return s
def build(z,exag,out,feather=0):
    d=np.load(D+f'dem{z}.npz'); H=d['H']
    H=np.where(H<-200,-200,H)
    Hs=ndi.gaussian_filter(H,0.8)
    s=shade(Hs,z,exag)
    flat=math.sin(math.radians(45))
    rel=(s-flat)
    col=ramp(Hs)
    rgb=col*(1+1.55*rel[...,None])
    # soft ambient occlusion-ish: darken valleys relative to blurred elevation
    loc=Hs-ndi.gaussian_filter(Hs,12)
    rgb*= (1+np.clip(loc/900,-0.22,0.25))[...,None]
    # sea
    sea=(H<=0.5)&(ndi.uniform_filter((H<=0.5).astype(np.float32),9)>0.95)
    rgb[sea]=(24,33,42)
    rng=np.random.default_rng(3)
    n=ndi.gaussian_filter(rng.normal(0,1,H.shape),1.2)*5+rng.normal(0,1,H.shape)*1.6
    rgb+=n[...,None]
    rgb=np.clip(rgb,0,255).astype(np.uint8)
    if feather:
        a=np.ones(H.shape,np.float32); 
        for k in range(feather):
            v=k/feather; a[k,:]=np.minimum(a[k,:],v); a[-1-k,:]=np.minimum(a[-1-k,:],v); a[:,k]=np.minimum(a[:,k],v); a[:,-1-k]=np.minimum(a[:,-1-k],v)
        rgb=np.dstack([rgb,(a*255).astype(np.uint8)])
    Image.fromarray(rgb).save(out)
    json.dump({'z':z,'x0':int(d['x0']),'y0':int(d['y0']),'w':H.shape[1],'h':H.shape[0]},open(out+'.json','w'))
    print(out,rgb.shape)
build(7,2.2,'base7.png'); build(9,1.5,'base9.png',feather=160)
