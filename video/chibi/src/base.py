import numpy as np, math, glob, json
from PIL import Image
from scipy import ndimage as ndi
Image.MAX_IMAGE_PIXELS = None
def mosaic(z):
    fs=glob.glob(f'{z}_*_*.png'); xs=sorted({int(f.split('_')[1]) for f in fs}); ys=sorted({int(f.split('_')[2].split('.')[0]) for f in fs})
    H=np.zeros(((ys[-1]-ys[0]+1)*256,(xs[-1]-xs[0]+1)*256),np.float32)
    for f in fs:
        _,x,y=f[:-4].split('_'); x=int(x); y=int(y)
        a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        H[(y-ys[0])*256:(y-ys[0]+1)*256,(x-xs[0])*256:(x-xs[0]+1)*256]=a[...,0]*256+a[...,1]+a[...,2]/256-32768
    return H,xs[0],ys[0]
def ramp(h):
    stops=[(-50,(26,36,44)),(0,(34,44,44)),(30,(40,50,46)),(120,(50,58,50)),(400,(70,72,58)),(900,(96,90,70)),(1600,(122,110,86)),(2600,(146,132,106)),(4000,(172,162,146))]
    xs=[s[0] for s in stops]; out=np.zeros(h.shape+(3,),np.float32)
    for c in range(3): out[...,c]=np.interp(h,xs,[s[1][c] for s in stops])
    return out
def build(z,exag,out,feather=0):
    H,x0,y0=mosaic(z); H=np.where(H<-100,-100,H)
    Hs=ndi.gaussian_filter(H,0.9)
    mpp=156543.03*math.cos(math.radians(30.5))/2**z
    gy,gx=np.gradient(Hs*exag/mpp)
    def hs(az,alt=40):
        az=math.radians(az); alt=math.radians(alt)
        lx=math.sin(az)*math.cos(alt); ly=-math.cos(az)*math.cos(alt); lz=math.sin(alt)
        n=np.sqrt(gx*gx+gy*gy+1); return np.clip((-gx*lx-gy*ly+lz)/n,0,1)
    s=0.6*hs(315)+0.25*hs(270)+0.15*hs(0)
    rel=s-math.sin(math.radians(40))
    rgb=ramp(Hs)*(1+1.6*rel[...,None])
    loc=Hs-ndi.gaussian_filter(Hs,12); rgb*=(1+np.clip(loc/700,-0.25,0.25))[...,None]
    rng=np.random.default_rng(3)
    rgb+=(ndi.gaussian_filter(rng.normal(0,1,H.shape),1.2)*4+rng.normal(0,1,H.shape)*1.4)[...,None]
    rgb=np.clip(rgb,0,255).astype(np.uint8)
    if feather:
        a=np.ones(H.shape,np.float32)
        for k in range(feather):
            v=(k/feather)**1.5; a[k,:]=np.minimum(a[k,:],v); a[-1-k,:]=np.minimum(a[-1-k,:],v); a[:,k]=np.minimum(a[:,k],v); a[:,-1-k]=np.minimum(a[:,-1-k],v)
        rgb=np.dstack([rgb,(a*255).astype(np.uint8)])
    Image.fromarray(rgb).save(out)
    json.dump({'z':z,'x0':x0,'y0':y0,'w':H.shape[1],'h':H.shape[0]},open(out+'.json','w'))
    print(out,rgb.shape)
build(7,2.4,'base7.png'); build(9,1.7,'base9.png',feather=200); build(10,1.5,'base10.png',feather=180)
