import numpy as np, math, glob, os
from PIL import Image
def build(z, out):
    fs=glob.glob(f'{z}_*_*.png'); xs=sorted({int(f.split('_')[1]) for f in fs}); ys=sorted({int(f.split('_')[2].split('.')[0]) for f in fs})
    H=np.zeros(((ys[-1]-ys[0]+1)*256,(xs[-1]-xs[0]+1)*256),np.float32)
    for f in fs:
        _,x,y=f[:-4].split('_'); x=int(x); y=int(y)
        a=np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        h=a[...,0]*256+a[...,1]+a[...,2]/256-32768
        H[(y-ys[0])*256:(y-ys[0]+1)*256,(x-xs[0])*256:(x-xs[0]+1)*256]=h
    np.savez_compressed(out,H=H.astype(np.float32),z=z,x0=xs[0],y0=ys[0])
    print(z,H.shape,H.min(),H.max(),xs[0],ys[0])
build(7,'dem7.npz'); build(9,'dem9.npz')
