# 深色晕渲底图：参照关羽工程 src/basemap.py 的 ramp + shade，调暗、去饱和；湖泊（Natural Earth）烤进底图
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
D = sys.argv[1]

def ramp(h):
    stops = [(-50, (26, 34, 40)), (0, (38, 44, 42)), (40, (46, 50, 46)), (150, (58, 60, 52)), (500, (80, 76, 60)),
             (1200, (108, 98, 78)), (2500, (134, 122, 100)), (4000, (160, 152, 138)), (5500, (196, 194, 188))]
    xs = [s[0] for s in stops]; out = np.zeros(h.shape + (3,), np.float32)
    for c in range(3): out[..., c] = np.interp(h, xs, [s[1][c] for s in stops])
    return out

def shade(H, z, exag, lat=31.8):
    mpp = 156543.03 * math.cos(math.radians(lat)) / 2 ** z
    gy, gx = np.gradient(H * exag / mpp)
    def hs(az, alt=40):
        az = math.radians(az); alt = math.radians(alt)
        lx, ly, lz = math.sin(az) * math.cos(alt), -math.cos(az) * math.cos(alt), math.sin(alt)
        return np.clip((-gx * lx - gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1), 0, 1)
    return 0.6 * hs(315) + 0.25 * hs(270) + 0.15 * hs(0)

def merc_px(lon, lat, z, x0, y0):
    n = 2 ** z
    return ((lon + 180) / 360 * n - x0) * 256, ((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n - y0) * 256

def lakes_mask(shape, z, x0, y0):
    im = Image.new('L', (shape[1], shape[0]), 0); dr = ImageDraw.Draw(im)
    d = json.load(open(D + '/ne_10m_lakes.geojson'))
    for f in d['features']:
        nm = f['properties'].get('name') or ''
        if 'Shuiku' in nm: continue          # 现代水库不画
        g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        for poly in polys:
            ring = [merc_px(x, y, z, x0, y0) for x, y in poly[0]]
            if len(ring) > 2: dr.polygon(ring, fill=255)
    return np.asarray(im) > 127

def build(z, exag, out, blur=0.8, gain=1.0):
    d = np.load(f'{D}/dem{z}.npz'); H = d['H']; x0, y0 = int(d['x0']), int(d['y0'])
    H = np.where(H < -100, -100, H); Hs = ndi.gaussian_filter(H, blur)
    s = shade(Hs, z, exag); rel = s - math.sin(math.radians(40))
    rgb = ramp(Hs) * (1 + 1.45 * rel[..., None])
    loc = Hs - ndi.gaussian_filter(Hs, 14)
    rgb *= (1 + np.clip(loc / 700, -0.2, 0.22))[..., None]
    water = lakes_mask(H.shape, z, x0, y0) | ((H <= 0.5) & (ndi.uniform_filter((H <= 0.5).astype(np.float32), 9) > 0.95))
    w = ndi.gaussian_filter(water.astype(np.float32), 1.2)[..., None]
    rgb = rgb * gain
    rgb = rgb * (1 - w) + np.array([22, 36, 44], np.float32) * w
    rng = np.random.default_rng(3)
    rgb += (ndi.gaussian_filter(rng.normal(0, 1, H.shape), 1.2) * 4 + rng.normal(0, 1, H.shape) * 1.2)[..., None]
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f'{D}/base{z}.png')
    json.dump({'z': z, 'x0': x0, 'y0': y0, 'w': H.shape[1], 'h': H.shape[0]}, open(f'{D}/base{z}.png.json', 'w'))
    print(z, H.shape)

build(7, 1.1, 'base7', 1.0, 0.62); build(10, 6.0, 'base10', 1.0); build(12, 9.0, 'base12', 1.4)
