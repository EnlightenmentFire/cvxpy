# -*- coding: utf-8 -*-
"""生成两张底图：macro.jpg（真实 DEM 晕渲，大尺度地图）与 tactical.jpg（程序生成的河岸战术底图）。
DEM: Mapzen/AWS Terrain Tiles (terrarium)，数据源 SRTM 等公有领域数据。"""
import os, io, math, sys, json, urllib.request
import numpy as np
from PIL import Image, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 8
LON0, LON1, LAT0, LAT1 = 104.0, 123.0, 22.5, 45.5

def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y

def fetch(z, x, y):
    p = f"{ROOT}/cache/tiles/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(4):
            try:
                data = urllib.request.urlopen(url, timeout=30).read(); break
            except Exception as e:
                if k == 3: raise
        open(p, "wb").write(data)
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)

def fbm(shape, beta=2.0, seed=0):
    rng = np.random.default_rng(seed)
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy); f[0, 0] = 1
    spec = (rng.normal(size=(h, w // 2 + 1)) + 1j * rng.normal(size=(h, w // 2 + 1))) / f ** (beta / 2)
    spec[0, 0] = 0
    a = np.fft.irfft2(spec, s=shape)
    a -= a.min(); a /= a.max()
    return a.astype(np.float32)

def blur(a, sigma):
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    return np.fft.irfft2(np.fft.rfft2(a) * g, s=a.shape).astype(np.float32)

def hillshade(h, cell, az=315, alt=42, zf=1.0):
    gy, gx = np.gradient(h * zf, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = np.radians(360 - az + 90), np.radians(alt)
    return np.sin(altr) * np.sin(slope) + np.cos(altr) * np.cos(slope) * np.cos(azr - aspect)

def ramp(v, stops):
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    out = np.empty(v.shape + (3,), np.float32)
    for k in range(3):
        out[..., k] = np.interp(v, xs, cs[:, k])
    return out

def macro():
    x0, y1 = lonlat_to_tile(LON0, LAT0, Z); x1, y0 = lonlat_to_tile(LON1, LAT1, Z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    H = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            t = fetch(Z, tx, ty)
            H[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = t[..., 0] * 256 + t[..., 1] + t[..., 2] / 256 - 32768
    # crop to bbox
    px0, px1 = int((x0 - tx0) * 256), int((x1 - tx0) * 256)
    py0, py1 = int((y0 - ty0) * 256), int((y1 - ty0) * 256)
    H = H[py0:py1, px0:px1]
    # upsample x2 for crisper plate
    S = 2
    Hi = np.asarray(Image.fromarray(H).resize((H.shape[1] * S, H.shape[0] * S), Image.BICUBIC))
    sea0 = Image.fromarray(((Hi <= 0.5) * 255).astype(np.uint8))
    small = sea0.resize((sea0.size[0] // 4, sea0.size[1] // 4), Image.BILINEAR).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.5))
    sea = np.asarray(small.resize(sea0.size, Image.BILINEAR)) > 127
    cell = 40075000 * math.cos(math.radians(36)) / (2 ** Z * 256 * S)
    hs1 = hillshade(Hi, cell, 315, 40, 5.0)
    hs2 = hillshade(Hi, cell, 270, 55, 5.0)
    hs = 0.7 * hs1 + 0.3 * hs2
    hs = (hs - np.sin(np.radians(40)) * 0.95)
    col = ramp(np.clip(Hi, 0, 3500), [
        (0,   (58, 62, 48)), (60,  (66, 68, 50)), (300, (80, 76, 54)), (800, (98, 88, 64)),
        (1400, (118, 104, 80)), (2200, (140, 126, 102)), (3500, (170, 160, 142))])
    n = fbm(Hi.shape, 1.6, 3)
    col *= (0.93 + 0.14 * n)[..., None]
    shade = np.clip(1.0 + hs * 1.25, 0.35, 1.9)[..., None]
    col = col * shade * 1.2
    # 海
    seacol = np.array((24, 38, 46), np.float32) * (0.9 + 0.2 * fbm(Hi.shape, 2.2, 5))[..., None]
    # 海岸柔边
    m = Image.fromarray((sea * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    m = (np.asarray(m).astype(np.float32) / 255)[..., None]
    col = col * (1 - m) + seacol * m
    # 海岸亮边
    edge = np.asarray(Image.fromarray((sea * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    col += (np.where(sea, edge - 1, 0) * -1 * 30)[..., None] * np.array((0.5, 0.8, 0.9), np.float32)
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    img.save(f"{ROOT}/assets/macro.jpg", quality=93)
    meta = dict(lon0=LON0, lon1=LON1, lat0=LAT0, lat1=LAT1, w=img.size[0], h=img.size[1],
                mx0=x0 / 2 ** Z, my0=y0 / 2 ** Z, scale=2 ** Z * 256 * S)
    json.dump(meta, open(f"{ROOT}/assets/macro.json", "w"))
    print("macro", img.size, meta)

def tactical():
    """战术底图：1 px = 0.6 m；北在上；河在下方，自西向东流。"""
    from PIL import ImageDraw
    W, Hh = 4096, 5120
    y = np.arange(Hh, dtype=np.float32)[:, None]; x = np.arange(W, dtype=np.float32)[None, :]
    n0 = fbm((Hh, W), 3.4, 10); n1 = fbm((Hh, W), 2.7, 11); n2 = fbm((Hh, W), 2.0, 12); n4 = fbm((Hh, W), 2.4, 14)
    rng = np.random.default_rng(7)
    bankN = 3150 + 70 * np.sin(x / 1300.0 + 0.6) + 40 * np.sin(x / 520.0 + 2.0)
    bankS = bankN + 680 + 45 * np.sin(x / 900.0 + 1.5)
    dN = bankN - y + (n1 - 0.5) * 60
    dS = y - bankS + (n4 - 0.5) * 50
    land = np.where(dN > 0, dN, np.where(dS > 0, dS, 0))
    water = (dN <= 0) & (dS <= 0)
    # 低缓起伏 + 旧河槽
    old = np.exp(-((dN - 900 - 260 * np.sin(x / 700.0) - 300 * (n0 - 0.5)) / 60.0) ** 2)
    elev = np.clip(land / 200.0, 0, 1) ** 0.6 * 2.5 + (n1 - 0.5) * 16 + (n2 - 0.5) * 2.2 - old * 1.6
    micro = blur(fbm((Hh, W), 1.2, 21) - 0.5, 1.6) * 1.1
    elev = blur(elev, 5.0) + micro
    hs = hillshade(elev, 0.6, 315, 38, 1.6); hs = hs - np.sin(np.radians(38)) * 0.97
    tone = n0 * 0.55 + n1 * 0.3 + n2 * 0.15
    base = ramp(tone, [(0.0, (52, 58, 40)), (0.3, (68, 70, 46)), (0.5, (84, 80, 52)), (0.7, (100, 90, 60)), (1.0, (122, 108, 74))])
    # 田块：低分辨率随机格 -> 旋转拉伸
    cells = rng.random((Hh // 160 + 2, W // 220 + 2)).astype(np.float32)
    cellimg = np.asarray(Image.fromarray(cells, mode="F").resize((W, Hh), Image.NEAREST))
    cellimg = np.roll(cellimg, 37, axis=1)
    fieldmask = np.clip((n0 - 0.45) * 6, 0, 1) * np.clip((dN - 260) / 200.0, 0, 1)
    fieldmask = np.asarray(Image.fromarray((fieldmask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))).astype(np.float32) / 255
    furrow = np.sin((x * 0.5 + y * 1.0) / 2.6) * 0.5 + 0.5
    cellimg = blur(cellimg, 3.0)
    base *= (1 + fieldmask * ((cellimg - 0.5) * 0.10 - 0.03 * furrow))[..., None]
    base *= (0.86 + 0.28 * n0)[..., None]
    sand = np.array((172, 152, 112), np.float32)
    sw = 70 + 120 * np.clip(n0 * 1.6 - 0.3, 0, 1)
    ks = np.clip(1 - land / sw, 0, 1)[..., None] ** 1.4
    wet = np.clip(1 - land / 22.0, 0, 1)[..., None]
    col = base * (1 - ks) + sand * (0.9 + 0.2 * n2[..., None]) * ks
    col = col * (1 - 0.3 * wet)
    col *= np.clip(1 + hs * 1.9, 0.55, 1.55)[..., None]
    col *= (1 - 0.18 * old)[..., None]
    # 水
    streak = rng.normal(size=(Hh // 3, W // 96)).astype(np.float32)
    streak = np.asarray(Image.fromarray(streak, mode="F").resize((W, Hh), Image.BICUBIC))
    depth = np.clip(np.minimum(-dN, -dS) / 260.0, 0, 1)
    wcol = ramp(depth, [(0, (148, 130, 94)), (0.12, (126, 116, 88)), (0.45, (100, 102, 86)), (1, (80, 90, 84))])
    wcol *= (1 + 0.035 * streak + 0.10 * (n1 - 0.5) + 0.08 * (n0 - 0.5))[..., None]
    bar = (n1 * 0.6 + n4 * 0.4) > 0.72
    barm = np.asarray(Image.fromarray((bar & water).astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(9))).astype(np.float32)[..., None] / 255
    wcol = wcol * (1 - 0.75 * barm) + sand * 0.9 * 0.75 * barm
    wm = np.asarray(Image.fromarray(water.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32)[..., None] / 255
    col = col * (1 - wm) + wcol * wm
    foam = np.exp(-(np.minimum(np.abs(dN), np.abs(dS)) / 4.0) ** 2)[..., None]
    col += foam * 16
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA")
    # 灌丛/树丛（带投影）
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); tr = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(sh), ImageDraw.Draw(tr)
    dens = np.clip((n2 - 0.5) * 4 + (n0 - 0.5) * 2, 0, 1)
    pts = rng.random((60000, 2)) * (W, Hh)
    cnt = 0
    for px, py in pts:
        ix, iy = int(px), int(py)
        if water[iy, ix] or land[iy, ix] < 90: continue
        if rng.random() > dens[iy, ix] * 0.35 + old[iy, ix] * 0.5: continue
        # 阵地中心区域少树，便于看清
        if abs(px - 2048) < 700 and 0 < bankN[0, ix] - py < 900 and rng.random() < 0.85: continue
        r = rng.uniform(2.5, 7.5)
        ds.ellipse((px - r + r * 0.9, py - r + r * 0.9, px + r + r * 0.9, py + r + r * 0.9), fill=(10, 14, 8, 110))
        g = rng.integers(-8, 8)
        dt.ellipse((px - r, py - r, px + r, py + r), fill=(44 + g, 58 + g, 34 + g, 235))
        dt.ellipse((px - r * 0.6 - r * 0.2, py - r * 0.6 - r * 0.2, px + r * 0.3, py + r * 0.3), fill=(70 + g, 84 + g, 48 + g, 200))
        cnt += 1
    sh = sh.filter(ImageFilter.GaussianBlur(2)); tr = tr.filter(ImageFilter.GaussianBlur(0.7))
    img = Image.alpha_composite(Image.alpha_composite(img, sh), tr).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    a += rng.normal(0, 2.2, a.shape[:2])[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img.save(f"{ROOT}/assets/tactical.jpg", quality=92)
    bn = np.argmax(water, axis=0)[::16].tolist()
    bs = (Hh - np.argmax(water[::-1], axis=0))[::16].tolist()
    json.dump(dict(w=W, h=Hh, mpp=0.6, step=16, bankN=bn, bankS=bs), open(f"{ROOT}/assets/tactical.json", "w"))
    print("tactical", img.size, "trees", cnt)

if __name__ == "__main__":
    which = sys.argv[1:] or ["macro", "tactical"]
    if "macro" in which: macro()
    if "tactical" in which: tactical()
