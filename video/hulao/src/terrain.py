# -*- coding: utf-8 -*-
"""生成地形底图（真实 DEM 晕渲）。DEM: Mapzen/AWS Terrain Tiles (terrarium)，数据源 SRTM 等开放高程数据。
用法：python terrain.py [macro gz hl hulao]"""
import os, io, math, sys, json, urllib.request
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATES = {   # name: lon0, lon1, lat0, lat1, zoom, upsample, 垂直夸张, 色调高程上限
    'macro': (103.0, 123.0, 22.5, 46.0, 8, 2, 5.0, 3500),
    'gz':    (106.8, 111.8, 33.1, 35.9, 10, 1, 3.2, 3200),
    'hl':    (111.3, 115.6, 33.7, 36.2, 10, 1, 3.6, 2400),
    'hulao': (112.72, 113.72, 34.52, 35.16, 12, 1, 3.0, 1300),
}

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n

def fetch(z, x, y):
    os.makedirs(f"{ROOT}/cache/tiles", exist_ok=True)
    p = f"{ROOT}/cache/tiles/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(5):
            try:
                data = urllib.request.urlopen(url, timeout=30).read(); break
            except Exception as e:
                if k == 4: raise
        open(p, "wb").write(data)
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)

def fbm(shape, beta=2.0, seed=0):
    rng = np.random.default_rng(seed); h, w = shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    spec = (rng.normal(size=(h, w // 2 + 1)) + 1j * rng.normal(size=(h, w // 2 + 1))) / f ** (beta / 2); spec[0, 0] = 0
    a = np.fft.irfft2(spec, s=shape); a -= a.min(); a /= a.max()
    return a.astype(np.float32)

def hillshade(h, cell, az=315, alt=42, zf=1.0):
    gy, gx = np.gradient(h * zf, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
    azr, altr = np.radians(360 - az + 90), np.radians(alt)
    return np.sin(altr) * np.sin(slope) + np.cos(altr) * np.cos(slope) * np.cos(azr - aspect)

def ramp(v, stops):
    xs = np.array([s[0] for s in stops], np.float32); cs = np.array([s[1] for s in stops], np.float32)
    out = np.empty(v.shape + (3,), np.float32)
    for k in range(3): out[..., k] = np.interp(v, xs, cs[:, k])
    return out

def plate(name):
    LON0, LON1, LAT0, LAT1, Z, S, ZF, HMAX = PLATES[name]
    x0, y1 = lonlat_to_tile(LON0, LAT0, Z); x1, y0 = lonlat_to_tile(LON1, LAT1, Z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    H = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]
    with ThreadPoolExecutor(12) as ex: tiles = list(ex.map(lambda j: fetch(Z, j[0], j[1]), jobs))
    for (tx, ty), t in zip(jobs, tiles):
        H[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = t[..., 0] * 256 + t[..., 1] + t[..., 2] / 256 - 32768
    px0, px1 = int((x0 - tx0) * 256), int((x1 - tx0) * 256); py0, py1 = int((y0 - ty0) * 256), int((y1 - ty0) * 256)
    H = H[py0:py1, px0:px1]
    Hi = np.asarray(Image.fromarray(H).resize((H.shape[1] * S, H.shape[0] * S), Image.BICUBIC)) if S > 1 else H
    sea0 = Image.fromarray(((Hi <= 0.5) * 255).astype(np.uint8))
    small = sea0.resize((max(8, sea0.size[0] // 4), max(8, sea0.size[1] // 4)), Image.BILINEAR).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.5))
    sea = np.asarray(small.resize(sea0.size, Image.BILINEAR)) > 127
    cell = 40075000 * math.cos(math.radians((LAT0 + LAT1) / 2)) / (2 ** Z * 256 * S)
    hs = 0.7 * hillshade(Hi, cell, 315, 40, ZF) + 0.3 * hillshade(Hi, cell, 270, 55, ZF)
    hs = hs - np.sin(np.radians(40)) * 0.95
    k = HMAX / 3500.0
    # 暗调：比上一集底图整体压暗、偏冷褐
    col = ramp(np.clip(Hi, 0, HMAX), [
        (0, (46, 50, 40)), (60 * k, (54, 56, 42)), (300 * k, (66, 63, 46)), (800 * k, (82, 74, 54)),
        (1400 * k, (100, 89, 68)), (2200 * k, (120, 108, 88)), (HMAX, (148, 140, 124))])
    n = fbm(Hi.shape, 1.6, 3)
    col *= (0.93 + 0.14 * n)[..., None]
    col = col * np.clip(1.0 + hs * 1.25, 0.35, 1.9)[..., None] * 1.12
    seacol = np.array((20, 32, 40), np.float32) * (0.9 + 0.2 * fbm(Hi.shape, 2.2, 5))[..., None]
    m = (np.asarray(Image.fromarray((sea * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255)[..., None]
    col = col * (1 - m) + seacol * m
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    os.makedirs(f"{ROOT}/assets", exist_ok=True)
    img.save(f"{ROOT}/assets/{name}.jpg", quality=92)
    meta = dict(lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1, w=img.size[0], h=img.size[1], mx0=x0 / 2 ** Z, my0=y0 / 2 ** Z, scale=2 ** Z * 256 * S)
    json.dump(meta, open(f"{ROOT}/assets/{name}.json", "w"))
    print(name, img.size, "elev", float(Hi.min()), float(Hi.max()), flush=True)

if __name__ == "__main__":
    for nm in (sys.argv[1:] or list(PLATES)): plate(nm)
