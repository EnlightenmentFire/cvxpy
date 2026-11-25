import numpy as np, math, json, glob
from PIL import Image
from scipy import ndimage as ndi
D='/home/user/work/dem/'
z=8
fs=glob.glob(D+f'{z}_*.png')
xs=sorted({int(f.split('_')[1]) for f in fs}); ys=sorted({int(f.split('_')[2].split('.')[0]) for f in fs})
x0,y0=xs[0],ys[0]; W=(xs[-1]-x0+1)*256; Hh=(ys[-1]-y0+1)*256
H=np.zeros((Hh,W),np.float32)
for f in fs:
    x=int(f.split('_')[1]); y=int(f.split('_')[2].split('.')[0])
    a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
    H[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=a[...,0]*256+a[...,1]+a[...,2]/256-32768
H=np.where(H<-100,-100,H)
Hs=ndi.gaussian_filter(H,1.0)
mpp=156543.03*math.cos(math.radians(37))/2**z
gy,gx=np.gradient(Hs*2.0/mpp)
def hs(az,alt=40):
    az=math.radians(az); alt=math.radians(alt)
    lx=math.sin(az)*math.cos(alt); ly=math.cos(az)*math.cos(alt); lz=math.sin(alt)
    n=np.sqrt(gx*gx+gy*gy+1)
    return np.clip((-gx*lx+gy*ly+lz)/n,0,1)
s=0.65*hs(315)+0.35*hs(270)
stops=[(-100,(14,22,30)),(0,(34,38,36)),(80,(42,45,40)),(300,(56,56,46)),(800,(78,72,56)),(1500,(104,94,74)),(2500,(128,118,98))]
xsx=[a for a,_ in stops]; col=np.zeros(H.shape+(3,),np.float32)
for c in range(3): col[...,c]=np.interp(Hs,xsx,[b[c] for _,b in stops])
rel=s-math.sin(math.radians(40))
rgb=col*(1+1.7*rel[...,None])
sea=(H<=0.5)&(ndi.uniform_filter((H<=0.5).astype(np.float32),7)>0.9)
seacol=np.array((16,26,36),np.float32)
rgb[sea]=seacol
# coastline glow
edge=ndi.binary_dilation(sea,iterations=2)&~sea
rgb[edge]=rgb[edge]*0.5+np.array((150,140,110))*0.5
rng=np.random.default_rng(3)
rgb+=(ndi.gaussian_filter(rng.normal(0,1,H.shape),1.5)*4)[...,None]
rgb=np.clip(rgb,0,255).astype(np.uint8)
Image.fromarray(rgb).save('/home/user/work/proj/assets/base8.png')
np.save('/home/user/work/proj/assets/sea8.npy',sea)
json.dump({'z':z,'x0':x0,'y0':y0,'w':W,'h':Hh},open('/home/user/work/proj/assets/base8.json','w'))
print(W,Hh)
