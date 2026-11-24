# -*- coding: utf-8 -*-
"""底图：
  macro.jpg  东西魏形势图用的大尺度晕渲（AWS Terrain Tiles / terrarium，SRTM 等公有领域高程，z8）
  local.jpg  玉璧一带的真实地形晕渲（z13，约 15 m 原始分辨率，放大 2 倍），并输出 local_dem.npy 供提取汾河河道
  snow.png   局部地形的积雪遮罩（平缓处与北坡多）"""
import os, io, math, sys, json, urllib.request
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YUBI = (110.9418, 35.5631)      # OSM：玉壁城遗址（稷山县太阳乡白家庄村）


def tile_xy(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def fetch(z, x, y):
    os.makedirs(f"{ROOT}/cache/tiles", exist_ok=True)
    p = f"{ROOT}/cache/tiles/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(5):
            try:
                data = urllib.request.urlopen(url, timeout=40).read(); break
            except Exception:
                if k == 4: raise
        open(p, "wb").write(data)
    t = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    return t[..., 0] * 256 + t[..., 1] + t[..., 2] / 256 - 32768


def mosaic(z, lon0, lon1, lat0, lat1):
    x0, y1 = tile_xy(lon0, lat0, z); x1, y0 = tile_xy(lon1, lat1, z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    H = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            H[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = fetch(z, tx, ty)
    px0, px1 = int((x0 - tx0) * 256), int((x1 - tx0) * 256); py0, py1 = int((y0 - ty0) * 256), int((y1 - ty0) * 256)
    return H[py0:py1, px0:px1], dict(mx0=x0 / 2 ** z, my0=y0 / 2 ** z, mx1=x1 / 2 ** z, my1=y1 / 2 ** z)


def fbm(shape, beta=2.0, seed=0):
    rng = np.random.default_rng(seed); h, w = shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    spec = (rng.normal(size=(h, w // 2 + 1)) + 1j * rng.normal(size=(h, w // 2 + 1))) / f ** (beta / 2); spec[0, 0] = 0
    a = np.fft.irfft2(spec, s=shape); a -= a.min(); a /= a.max(); return a.astype(np.float32)


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


def blur(a, sigma):
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(a) * g, s=a.shape).astype(np.float32)


def up(a, s):
    return np.asarray(Image.fromarray(a).resize((a.shape[1] * s, a.shape[0] * s), Image.BICUBIC))


def macro():
    Z = 8; LON0, LON1, LAT0, LAT1 = 103.5, 119.5, 30.5, 42.2
    H, m = mosaic(Z, LON0, LON1, LAT0, LAT1); S = 2; Hi = up(H, S)
    sea = Hi <= 0.5
    cell = 40075000 * math.cos(math.radians(36)) / (2 ** Z * 256 * S)
    hs = 0.7 * hillshade(Hi, cell, 315, 40, 5.0) + 0.3 * hillshade(Hi, cell, 270, 55, 5.0); hs = hs - np.sin(np.radians(40)) * 0.95
    col = ramp(np.clip(Hi, 0, 3500), [(0, (52, 55, 46)), (80, (60, 61, 50)), (400, (74, 70, 55)), (900, (90, 82, 64)),
                                       (1500, (108, 98, 80)), (2300, (128, 118, 100)), (3500, (152, 146, 134))])
    col *= (0.92 + 0.16 * fbm(Hi.shape, 1.6, 3))[..., None]
    col = col * np.clip(1.0 + hs * 1.3, 0.32, 1.9)[..., None] * 1.12
    seacol = np.array((22, 32, 40), np.float32)
    mm = (np.asarray(Image.fromarray((sea * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255)[..., None]
    col = col * (1 - mm) + seacol * mm
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)); img.save(f"{ROOT}/assets/macro.jpg", quality=92)
    meta = dict(m, scale=2 ** Z * 256 * S, w=img.size[0], h=img.size[1], lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1)
    json.dump(meta, open(f"{ROOT}/assets/macro.json", "w")); print("macro", img.size)


def local():
    Z = 13; LON0, LON1, LAT0, LAT1 = 110.70, 111.20, 35.40, 35.72
    H, m = mosaic(Z, LON0, LON1, LAT0, LAT1)
    np.save(f"{ROOT}/cache/local_dem.npy", H)
    S = 2; Hi = up(H, S).astype(np.float32)
    Hs = blur(Hi, 1.2)
    cell = 40075000 * math.cos(math.radians(35.56)) / (2 ** Z * 256 * S)
    micro = (fbm(Hi.shape, 1.25, 21) - 0.5) * 2.2
    hs = 0.72 * hillshade(Hs + micro, cell, 315, 38, 1.7) + 0.28 * hillshade(Hs, cell, 250, 50, 1.7)
    hs = hs - np.sin(np.radians(38)) * 0.95
    lo, hi = np.percentile(Hi, 2), np.percentile(Hi, 99.5)
    # 按真实高程着色：汾河谷地（约 370–400 m）暗绿褐，二级台塬（约 450–470 m）浅黄土，山地更浅、偏石色
    col = ramp(Hi, [(360, (58, 64, 46)), (385, (66, 70, 50)), (405, (82, 80, 58)), (440, (112, 102, 74)), (470, (128, 114, 82)),
                    (600, (138, 124, 92)), (900, (150, 138, 112)), (1300, (164, 156, 140))])
    n1 = fbm(Hi.shape, 2.2, 5); n2 = fbm(Hi.shape, 1.5, 9)
    col *= (0.88 + 0.22 * n1)[..., None]
    # 田块纹理（只在平缓处）
    gy, gx = np.gradient(Hs, cell); slope = np.hypot(gx, gy)
    flat = np.clip(1 - slope / 0.08, 0, 1)
    rng = np.random.default_rng(3)
    cells = rng.random((Hi.shape[0] // 18 + 2, Hi.shape[1] // 26 + 2)).astype(np.float32)
    cellimg = np.asarray(Image.fromarray(cells, mode="F").resize((Hi.shape[1] + 26, Hi.shape[0] + 18), Image.NEAREST))[:Hi.shape[0], :Hi.shape[1]]
    col *= (1 + flat * (cellimg - 0.5) * 0.10)[..., None]
    col = col * np.clip(1.0 + hs * 2.2, 0.28, 1.8)[..., None]
    col += (n2[..., None] - 0.5) * 6
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)); img.save(f"{ROOT}/assets/local.jpg", quality=90)
    # 积雪遮罩：平缓处 + 北向坡多，陡坡少
    aspect_n = np.clip(-gy / (slope + 1e-6), -1, 1)
    snow = np.clip(0.55 * flat + 0.35 * (0.5 + 0.5 * aspect_n) * (1 - np.clip(slope / 0.6, 0, 1)) + (n1 - 0.5) * 0.5, 0, 1)
    Image.fromarray((snow * 255).astype(np.uint8)).save(f"{ROOT}/assets/snow.png")
    meta = dict(m, z=Z, S=S, scale=2 ** Z * 256 * S, w=img.size[0], h=img.size[1], lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1,
                elev=[float(lo), float(hi)], yubi=YUBI)
    json.dump(meta, open(f"{ROOT}/assets/local.json", "w")); print("local", img.size, "elev p2/p99.5", lo, hi)


if __name__ == "__main__":
    which = sys.argv[1:] or ["macro", "local"]
    if "macro" in which: macro()
    if "local" in which: local()
