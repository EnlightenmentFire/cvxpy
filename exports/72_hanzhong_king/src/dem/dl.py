import math, os, urllib.request, concurrent.futures as cf
def tile(lon,lat,z):
    n=2**z; x=int((lon+180)/360*n); y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n); return x,y
def fetch(a):
    z,x,y=a; p=f'{z}_{x}_{y}.png'
    if os.path.exists(p) and os.path.getsize(p)>500: return 0
    err=None
    for k in range(4):
        try:
            d=urllib.request.urlopen(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',timeout=40).read()
            open(p,'wb').write(d); return 1
        except Exception as e: err=e
    print('fail',a,err); return -1
jobs=[]
for z,(l0,l1,b0,b1) in {7:(95,122,22,40),9:(102,113,28,34.8),11:(105.4,107.6,32.6,33.6)}.items():
    x0,y0=tile(l0,b1,z); x1,y1=tile(l1,b0,z)
    jobs+=[(z,x,y) for x in range(x0,x1+1) for y in range(y0,y1+1)]
    print(z,(x1-x0+1)*(y1-y0+1))
with cf.ThreadPoolExecutor(16) as ex: r=list(ex.map(fetch,jobs))
print('done',len(r),r.count(-1))
