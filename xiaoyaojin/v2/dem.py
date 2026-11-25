# 下载 AWS Terrain Tiles（terrarium 编码，SRTM 等来源）并拼成高程网格；下载 Natural Earth 河湖矢量
import math, os, sys, urllib.request, concurrent.futures as cf
import numpy as np
from PIL import Image
D = sys.argv[1]; os.makedirs(D, exist_ok=True); os.chdir(D)
LEVELS = {7: (102.5, 123.5, 25.5, 38.5), 10: (116.4, 118.6, 30.7, 32.45), 12: (117.05, 117.62, 31.66, 32.02)}
def tile(lon, lat, z):
    n = 2 ** z; return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
def fetch(a):
    z, x, y = a; p = f'{z}_{x}_{y}.png'
    if os.path.exists(p) and os.path.getsize(p) > 500: return 0
    for k in range(4):
        try:
            open(p, 'wb').write(urllib.request.urlopen(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png', timeout=40).read()); return 1
        except Exception as e: err = e
    print('fail', a, err); return -1
for z, (l0, l1, b0, b1) in LEVELS.items():
    x0, y0 = tile(l0, b1, z); x1, y1 = tile(l1, b0, z)
    jobs = [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    with cf.ThreadPoolExecutor(8) as ex: r = list(ex.map(fetch, jobs))
    H = np.zeros(((y1 - y0 + 1) * 256, (x1 - x0 + 1) * 256), np.float32)
    for (_, x, y) in jobs:
        a = np.asarray(Image.open(f'{z}_{x}_{y}.png').convert('RGB')).astype(np.float32)
        H[(y - y0) * 256:(y - y0 + 1) * 256, (x - x0) * 256:(x - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    np.savez_compressed(f'dem{z}.npz', H=H, z=z, x0=x0, y0=y0)
    print(z, len(jobs), H.shape, float(H.min()), float(H.max()), r.count(-1))
for n in ('ne_10m_rivers_lake_centerlines', 'ne_10m_lakes', 'ne_10m_rivers_asia'):
    if not os.path.exists(n + '.geojson'):
        try:
            open(n + '.geojson', 'wb').write(urllib.request.urlopen(f'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{n}.geojson', timeout=120).read())
        except Exception as e: print('ne fail', n, e)
print('ok')
