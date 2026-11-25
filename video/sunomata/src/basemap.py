"""下载 Terrarium 高程瓦片并做暗色晕渲底图（两级：尾张美浓大图 z9、浓尾河网 z11）。"""
import math, os, json, urllib.request, concurrent.futures as cf, io
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
D = "/tmp/claude-0/work/dem/"
os.makedirs(D, exist_ok=True)

def tile(lon, lat, z):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)

def fetch(a):
    z, x, y = a; p = f"{D}{z}_{x}_{y}.png"
    if not (os.path.exists(p) and os.path.getsize(p) > 500):
        for _ in range(4):
            try:
                open(p, "wb").write(urllib.request.urlopen(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", timeout=40).read()); break
            except Exception as e:
                print("retry", a, e)
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

def mosaic(z, l0, l1, b0, b1):
    x0, y0 = tile(l0, b1, z); x1, y1 = tile(l1, b0, z)
    jobs = [(z, x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
    with cf.ThreadPoolExecutor(12) as ex:
        ts = list(ex.map(fetch, jobs))
    nx = x1 - x0 + 1
    rows = [np.hstack(ts[i * nx:(i + 1) * nx]) for i in range(y1 - y0 + 1)]
    return np.vstack(rows), x0, y0

def ramp(h):
    st = [(-20, (12, 22, 30)), (0, (22, 32, 34)), (15, (30, 40, 36)), (80, (38, 46, 38)), (300, (52, 56, 44)), (800, (74, 72, 58)), (1500, (100, 94, 80)), (2500, (130, 124, 112))]
    xs = [s[0] for s in st]
    return np.stack([np.interp(h, xs, [s[1][c] for s in st]) for c in range(3)], -1)

def build(z, box, exag, name):
    H, x0, y0 = mosaic(z, *box)
    H = np.maximum(H, -50)
    Hs = ndi.gaussian_filter(H, 0.9)
    mpp = 156543.03 * math.cos(math.radians(35.3)) / 2 ** z
    gy, gx = np.gradient(Hs * exag / mpp)
    def hs(az, alt=40):
        az, alt = math.radians(az), math.radians(alt)
        lx, ly, lz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
        return np.clip((-gx * lx + gy * ly + lz) / np.sqrt(gx * gx + gy * gy + 1), 0, 1)
    s = 0.65 * hs(315) + 0.35 * hs(260)
    rgb = ramp(Hs) * (0.55 + 1.1 * s[..., None])
    loc = Hs - ndi.gaussian_filter(Hs, 10)
    rgb *= (1 + np.clip(loc / 700, -0.2, 0.2))[..., None]
    low = ndi.binary_opening(H <= 0.3, iterations=6)
    lab, _ = ndi.label(low)
    edge = set(np.unique(np.concatenate([lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sea = np.isin(lab, list(edge)) & (H <= 0.3)
    sea = ndi.binary_closing(sea, iterations=2) & (H <= 1.0)
    rgb[sea] = (14, 24, 34)
    rng = np.random.default_rng(1)
    rgb += (ndi.gaussian_filter(rng.normal(0, 1, H.shape), 1.0) * 4)[..., None]
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(f"{D}{name}.png")
    json.dump(dict(z=z, x0=x0, y0=y0, w=H.shape[1], h=H.shape[0]), open(f"{D}{name}.json", "w"))
    print(name, H.shape)

if __name__ == "__main__":
    build(9, (135.9, 137.7, 34.75, 36.1), 3.0, "big")
    build(11, (136.4, 137.05, 35.0, 35.6), 2.0, "plain")
