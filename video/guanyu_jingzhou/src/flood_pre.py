import numpy as np, math, json
from scipy import ndimage as ndi
from geo import merc, load_rivers
d=np.load('/home/user/work/dem/dem9.npz'); Hh=d['H']; z=9; x0=int(d['x0']); y0=int(d['y0']); n=256*2**z
def px(lon,lat):
    mx,my=merc(lon,lat); return mx*n-x0*256, my*n-y0*256
L,T_=px(111.45,32.65); R,B=px(112.85,31.45); L,T_,R,B=int(L),int(T_),int(R),int(B)
H=ndi.gaussian_filter(Hh[T_:B,L:R],1.0)
mask=np.zeros(H.shape,bool)
for name,rank,l in load_rivers():
    if name!='Han': continue
    for i in range(len(l)-1):
        a=px(*l[i]); b=px(*l[i+1]); k=int(max(abs(a[0]-b[0]),abs(a[1]-b[1]))*2)+1
        for j in range(k+1):
            x=a[0]+(b[0]-a[0])*j/k-L; y=a[1]+(b[1]-a[1])*j/k-T_
            if 0<=int(y)<H.shape[0] and 0<=int(x)<H.shape[1]: mask[int(y),int(x)]=True
# river surface elevation = local min near river pixel
Hmin=ndi.minimum_filter(H,5)
dist,(iy,ix)=ndi.distance_transform_edt(~mask,return_indices=True)
base=Hmin[iy,ix]
base=ndi.gaussian_filter(base,6)
e=H-base   # height above local river level (m)
e=np.where(dist>75,99,e)   # limit to ~20km from river
e=ndi.gaussian_filter(e,1.2)
np.save('flood_e.npy',e.astype(np.float32))
json.dump({'z':z,'L':L+x0*256,'T':T_+y0*256,'w':e.shape[1],'h':e.shape[0]},open('flood_e.json','w'))
print(e.shape,np.percentile(e,[1,10,30,50,70]), (e<10).mean())
