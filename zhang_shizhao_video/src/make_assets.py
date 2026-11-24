# 生成自制纹理与地图路径（无第三方版权素材；地图轮廓来自 Natural Earth，公有领域）
import numpy as np, json, math
from PIL import Image, ImageFilter
rng=np.random.default_rng(7)
W,H=1080,1920
def fbm(w,h,octs=6,seed=0):
    r=np.random.default_rng(seed); out=np.zeros((h,w),np.float32); amp=1; tot=0
    for o in range(octs):
        s=2**(o+2)
        g=r.random((h//s+2,w//s+2)).astype(np.float32)
        im=Image.fromarray((g*255).astype(np.uint8)).resize((w,h),Image.BICUBIC)
        out+=np.asarray(im,np.float32)/255*amp; tot+=amp; amp*=0.55
    return out/tot
def paper(base,name,dark=False,seed=1):
    n1=fbm(W,H,6,seed); n2=rng.normal(0,1,(H,W)).astype(np.float32)
    fine=np.asarray(Image.fromarray(((n2*0.5+0.5).clip(0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)),np.float32)/255
    # 纤维
    fib=np.zeros((H,W),np.float32)
    for _ in range(900):
        x=rng.integers(0,W); y=rng.integers(0,H); L=rng.integers(15,70); a=rng.uniform(0,math.pi)
        for k in range(L):
            xx=int(x+k*math.cos(a)); yy=int(y+k*math.sin(a))
            if 0<=xx<W and 0<=yy<H: fib[yy,xx]+=rng.uniform(.3,1)
    fib=np.asarray(Image.fromarray((fib.clip(0,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)),np.float32)/255
    yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
    edge=np.clip((d-0.75)/0.7,0,1)**1.6
    v=(n1-0.5)*(0.16 if not dark else 0.10)+(fine-0.5)*(0.07 if not dark else 0.05)-fib*(0.05 if not dark else -0.03)-edge*(0.16 if not dark else 0.25)
    # 污渍
    st=fbm(W,H,3,seed+9); v-=np.clip(st-0.62,0,1)*(0.35 if not dark else 0.1)
    b=np.array(base,np.float32)/255
    img=np.clip(b[None,None,:]*(1+v[...,None]*(1.0 if not dark else 1.6)),0,1)
    # 暖色偏移
    img[...,2]*=(1-edge*0.08)
    Image.fromarray((img*255).astype(np.uint8)).save(f'assets/{name}.jpg',quality=90)
paper((232,221,197),'paper_light',seed=1)
paper((218,203,172),'paper_old',seed=3)
paper((30,26,22),'paper_dark',dark=True,seed=5)
# 拓片纹理：黑底白点（可平铺的透明 PNG）
s=512; a=rng.random((s,s)); sp=(a>0.985).astype(np.float32)
sp=np.asarray(Image.fromarray((sp*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)),np.float32)/255
cl=fbm(s,s,4,11); alpha=np.clip(sp*2.2+np.clip(cl-0.6,0,1)*1.2,0,1)
rub=np.zeros((s,s,4),np.uint8); rub[...,:3]=20; rub[...,3]=(alpha*255).astype(np.uint8)
Image.fromarray(rub).save('assets/rub_specks.png')
# 印泥缺损蒙版
a=fbm(s,s,5,21); m=np.clip((a-0.33)*6,0,1); n=rng.random((s,s)); m*= (n>0.06)
Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5)).save('assets/seal_mask.png')
# 颗粒（视频级别，在浏览器里不加，ffmpeg 加）
# ── 地图 ──
gj=json.load(open('assets/geo/ne_50m_land.geojson'))
def proj(lon,lat,box,w):
    lon0,lon1,lat0,lat1=box
    mx=lambda la: math.log(math.tan(math.pi/4+math.radians(la)/2))
    x=(lon-lon0)/(lon1-lon0)*w
    sc=w/math.radians(lon1-lon0)
    y=(mx(lat1)-mx(lat))*sc
    return x,y
def build(box,w,simp=0.6):
    lon0,lon1,lat0,lat1=box; paths=[]
    for f in gj['features']:
        g=f['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:
            ring=poly[0]
            xs=[p[0] for p in ring]; ys=[p[1] for p in ring]
            if max(xs)<lon0-5 or min(xs)>lon1+5 or max(ys)<lat0-5 or min(ys)>lat1+5: continue
            pts=[]; last=None
            for lon,lat in ring:
                lat=max(min(lat,84),-60)
                x,y=proj(lon,lat,box,w)
                if last is None or abs(x-last[0])+abs(y-last[1])>simp: pts.append((x,y)); last=(x,y)
            if len(pts)>3: paths.append('M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)+'Z')
    h=proj(lon0,lat0,box,w)[1]
    return {'d':' '.join(paths),'w':w,'h':h,'box':box}
cities={'上海':(121.47,31.23),'南京':(118.78,32.06),'东京':(139.69,35.69),'北京':(116.40,39.90),'伦敦':(-0.12,51.5)}
out={}
for name,box,w in [('eurasia',(-14,152,12,64),1500),('eastasia',(104,146,22,46),1080)]:
    m=build(box,w); m['cities']={k:proj(v[0],v[1],box,w) for k,v in cities.items()}; out[name]=m
open('src/mapdata.js','w').write('window.MAPDATA='+json.dumps(out,ensure_ascii=False)+';')
print({k:(v['w'],round(v['h']),len(v['d'])) for k,v in out.items()})
