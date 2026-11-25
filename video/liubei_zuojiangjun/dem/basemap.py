import numpy as np, math, json, glob
from PIL import Image
from scipy import ndimage as ndi
def mosaic(z):
    fs=glob.glob(f'{z}_*.png'); xs=sorted({int(f.split('_')[1]) for f in fs}); ys=sorted({int(f.split('_')[2][:-4]) for f in fs})
    H=np.zeros((len(ys)*256,len(xs)*256),np.float32)
    for f in fs:
        x=int(f.split('_')[1]); y=int(f.split('_')[2][:-4])
        a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        h=a[...,0]*256+a[...,1]+a[...,2]/256-32768
        H[(y-ys[0])*256:(y-ys[0]+1)*256,(x-xs[0])*256:(x-xs[0]+1)*256]=h
    return H,xs[0],ys[0]
def ramp(h):
    stops=[(-60,(20,30,38)),(0,(46,52,44)),(50,(58,62,48)),(200,(72,72,54)),(600,(92,84,62)),(1200,(112,98,74)),(2200,(128,114,92)),(3500,(150,140,124)),(5000,(186,182,176))]
    xs=[s[0] for s in stops]; out=np.zeros(h.shape+(3,),np.float32)
    for c in range(3): out[...,c]=np.interp(h,xs,[s[1][c] for s in stops])
    return out
def build(z,exag,out):
    H,x0,y0=mosaic(z); H=np.maximum(H,-200)
    Hs=ndi.gaussian_filter(H,0.9)
    mpp=156543.03*math.cos(math.radians(34))/2**z
    gy,gx=np.gradient(Hs*exag/mpp)
    def hs(az,alt=40):
        az=math.radians(az); alt=math.radians(alt)
        lx=math.sin(az)*math.cos(alt); ly=-math.cos(az)*math.cos(alt); lz=math.sin(alt)
        n=np.sqrt(gx*gx+gy*gy+1); return np.clip((-gx*lx+gy*ly*-1*-1*-1+lz)/n,0,1)
    s=0.65*hs(315)+0.35*hs(260)
    rel=s-math.sin(math.radians(40))
    rgb=ramp(Hs)*(1+1.5*rel[...,None])
    loc=Hs-ndi.gaussian_filter(Hs,14); rgb*=(1+np.clip(loc/1000,-0.2,0.22))[...,None]
    sea=(H<=0.5)&(ndi.uniform_filter((H<=0.5).astype(np.float32),9)>0.95)
    rgb[sea]=(18,26,34)
    rng=np.random.default_rng(3)
    rgb+= (ndi.gaussian_filter(rng.normal(0,1,H.shape),1.3)*5+rng.normal(0,1,H.shape)*1.5)[...,None]
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(out)
    json.dump({'z':z,'x0':x0,'y0':y0,'w':H.shape[1],'h':H.shape[0]},open(out+'.json','w'))
    print(out,H.shape)
build(7,2.4,'base7.png'); build(9,1.6,'base9.png')
