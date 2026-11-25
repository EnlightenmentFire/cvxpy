import math, json, numpy as np, skia
W,H=1080,1920
def merc(lon,lat):
    return (lon+180)/360, (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2
class Cam:
    def __init__(s,lon,lat,span,ax=540,ay=880): s.lon,s.lat,s.span,s.ax,s.ay=lon,lat,span,ax,ay
    @property
    def S(s): return W/(s.span/360)
    def p(s,lon,lat):
        mx,my=merc(lon,lat); m0=merc(s.lon,s.lat)
        return s.ax+(mx-m0[0])*s.S, s.ay+(my-m0[1])*s.S
    @staticmethod
    def lerp(a,b,t):
        # zoom-aware interpolation (log span)
        sp=math.exp(math.log(a.span)*(1-t)+math.log(b.span)*t)
        return Cam(a.lon+(b.lon-a.lon)*t,a.lat+(b.lat-a.lat)*t,sp,a.ax+(b.ax-a.ax)*t,a.ay+(b.ay-a.ay)*t)
class Base:
    """底图：预建多级缩小版，按镜头比例选级，只画可见区域。"""
    def __init__(s,path):
        from PIL import Image
        s.m=json.load(open(path+'.json')); im=Image.open(path); s.lv=[]
        for L in range(4):
            a=np.asarray(im if L==0 else im.resize((im.width>>L,im.height>>L),Image.LANCZOS))
            if a.shape[2]==3: a=np.dstack([a,np.full(a.shape[:2],255,np.uint8)])
            else:
                a=a.copy(); a[...,:3]=(a[...,:3].astype(np.float32)*(a[...,3:4]/255.0)).astype(np.uint8)
            s.lv.append(skia.Image.fromarray(np.ascontiguousarray(a),skia.kRGBA_8888_ColorType,skia.kPremul_AlphaType))
    def draw(s,c,cam,alpha=1.0):
        z=s.m['z']; n=256*2**z; k=cam.S/n; m0=merc(cam.lon,cam.lat)
        tx=cam.ax+(s.m['x0']*256/n-m0[0])*cam.S; ty=cam.ay+(s.m['y0']*256/n-m0[1])*cam.S
        L=0
        while L<3 and k*2**(L+1)<=1.0: L+=1
        img=s.lv[L]; kk=k*2**L
        # 可见源矩形
        x0=max(0.0,(0-tx)/kk-2); y0=max(0.0,(0-ty)/kk-2); x1=min(img.width(),(W-tx)/kk+2); y1=min(img.height(),(H-ty)/kk+2)
        if x1<=x0 or y1<=y0: return k
        p=skia.Paint(); p.setAlphaf(alpha)
        samp=skia.SamplingOptions(skia.CubicResampler.Mitchell()) if kk>1.05 else skia.SamplingOptions(skia.FilterMode.kLinear)
        c.drawImageRect(img,skia.Rect.MakeLTRB(x0,y0,x1,y1),skia.Rect.MakeLTRB(tx+x0*kk,ty+y0*kk,tx+x1*kk,ty+y1*kk),samp,p)
        return k
def load_rivers(path='/tmp/claude-0/work/dem/rivers.geojson',bbox=(96,19,124,41)):
    d=json.load(open(path)); out=[]
    for f in d['features']:
        g=f['geometry']
        if not g: continue
        ls=[g['coordinates']] if g['type']=='LineString' else g['coordinates']
        for l in ls:
            if any(bbox[0]<c[0]<bbox[2] and bbox[1]<c[1]<bbox[3] for c in l):
                out.append((f['properties'].get('name'),f['properties'].get('scalerank',9),[(c[0],c[1]) for c in l]))
    return out
