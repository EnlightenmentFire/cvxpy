"""Fetch Terrarium elevation tiles (AWS open data 'elevation-tiles-prod', Mapzen/Tilezen sources incl. SRTM, ETOPO1, GMTED)
and render dark cinematic shaded-relief textures (web mercator) for three map levels.
usage: python build_maps.py
"""
import os, math, io, json, concurrent.futures as cf, urllib.request
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom as ndzoom

TILE = "/tmp/claude-0/work/tiles"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "maps")
MAPS = {
    "A": dict(z=8, lon0=19.0, lon1=31.5, lat0=34.6, lat1=42.4, ex=7.0),   # Aegean
    "B": dict(z=11, lon0=22.55, lon1=24.25, lat0=37.30, lat1=38.30, ex=2.2),  # Saronic gulf
    "C": dict(z=14, lon0=23.40, lon1=23.73, lat0=37.885, lat1=38.025, ex=1.4),  # strait
}

def tx(lon, z): return (lon + 180) / 360 * 2 ** z
def ty(lat, z):
    r = math.radians(lat); return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z

def fetch(z, x, y):
    p = f"{TILE}/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(4):
            try:
                data = urllib.request.urlopen(url, timeout=30).read(); open(p, "wb").write(data); break
            except Exception as e:
                if k == 3: raise
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float64)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

def mosaic(m):
    z = m["z"]
    fx0, fx1 = tx(m["lon0"], z), tx(m["lon1"], z)
    fy0, fy1 = ty(m["lat1"], z), ty(m["lat0"], z)
    X = range(int(fx0), int(fx1) + 1); Y = range(int(fy0), int(fy1) + 1)
    with cf.ThreadPoolExecutor(8) as ex:
        tiles = {(x, y): ex.submit(fetch, z, x, y) for x in X for y in Y}
    big = np.vstack([np.hstack([tiles[(x, y)].result() for x in X]) for y in Y])
    px0 = int((fx0 - X[0]) * 256); px1 = int((fx1 - X[0]) * 256)
    py0 = int((fy0 - Y[0]) * 256); py1 = int((fy1 - Y[0]) * 256)
    return big[py0:py1, px0:px1]

def lerpc(a, b, t):
    a = np.array(a, float); b = np.array(b, float); return a + (b - a) * t[..., None]

def render(k, m):
    e = mosaic(m)
    e = gaussian_filter(e, 0.6)
    h, w = e.shape
    # pixel size in metres (mercator, approx at centre lat)
    lat_c = (m["lat0"] + m["lat1"]) / 2
    mpp = 40075016.686 * math.cos(math.radians(lat_c)) / (256 * 2 ** m["z"])
    land = e > 0.5
    dz_dy, dz_dx = np.gradient(np.where(land, e, 0) * m["ex"], mpp)
    az, alt = math.radians(315), math.radians(38)
    slope = np.arctan(np.hypot(dz_dx, dz_dy)); aspect = np.arctan2(-dz_dx, dz_dy)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)
    # land: dark bronze -> warm ochre by hillshade, slight brightening with height
    hn = np.clip(e / (1400 if k == "A" else 900), 0, 1)
    lc = lerpc((34, 30, 24), (150, 128, 92), np.clip(hs * 0.85 + hn * 0.25, 0, 1))
    # sea: depth tint
    d = np.clip(-e / (2500 if k == "A" else 120), 0, 1)
    sc = lerpc((40, 74, 88), (10, 22, 32), d ** 0.6)
    img = np.where(land[..., None], lc, sc)
    # coastline glow
    edge = gaussian_filter(land.astype(float), 1.2 if k != "A" else 0.9)
    rim = np.clip(1 - np.abs(edge - 0.5) * 2, 0, 1) * (~land)
    img = img + rim[..., None] * np.array([60, 70, 66]) * 0.55
    rng = np.random.default_rng(3)
    img = img * (1 + rng.normal(0, 0.012, (h, w))[..., None])
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f"{OUT}/{k}.jpg", quality=92)
    Image.fromarray((land * 255).astype(np.uint8)).save(f"/tmp/claude-0/work/land_{k}.png")
    print(k, w, h, "mpp", round(mpp, 1))
    return dict(lon0=m["lon0"], lon1=m["lon1"], lat0=m["lat0"], lat1=m["lat1"], w=w, h=h)

if __name__ == "__main__":
    meta = {k: render(k, m) for k, m in MAPS.items()}
    json.dump(meta, open(f"{OUT}/maps.json", "w"), indent=1)
