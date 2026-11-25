# -*- coding: utf-8 -*-
"""底图：真实高程晕渲（AWS Terrain Tiles / terrarium，SRTM 等公有领域数据）＋ Natural Earth 河流（公有领域）。
输出 assets/macro.jpg（东亚大图）、assets/region.jpg（淮河—淝水局部）、assets/geo.json（投影参数与河流折线）。"""
import os, io, math, json, urllib.request
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = f"{ROOT}/cache/tiles"; os.makedirs(CACHE, exist_ok=True)
PLATES = {
    "macro": dict(z=6, lon=(97.0, 125.0), lat=(19.5, 43.0), S=3, zf=6.0),
    "region": dict(z=10, lon=(115.9, 117.75), lat=(32.15, 33.25), S=2, zf=9.0),
}


def tile_xy(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def fetch(z, x, y):
    p = f"{CACHE}/{z}_{x}_{y}.png"
    if not os.path.exists(p):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(4):
            try:
                data = urllib.request.urlopen(url, timeout=30).read(); break
            except Exception:
                if k == 3: raise
        open(p, "wb").write(data)
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def hillshade(h, cell, az=315, alt=40, zf=1.0):
    gy, gx = np.gradient(h * zf, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    azr, altr = np.radians(360 - az + 90), np.radians(alt)
    return np.sin(altr) * np.sin(slope) + np.cos(altr) * np.cos(slope) * np.cos(azr - aspect)


def ramp(v, stops):
    xs = np.array([s[0] for s in stops], np.float32); cs = np.array([s[1] for s in stops], np.float32)
    return np.stack([np.interp(v, xs, cs[:, k]) for k in range(3)], -1)


def plate(name, z, lon, lat, S, zf):
    x0, y1 = tile_xy(lon[0], lat[0], z); x1, y0 = tile_xy(lon[1], lat[1], z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    H = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            t = fetch(z, tx, ty)
            H[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = t[..., 0] * 256 + t[..., 1] + t[..., 2] / 256 - 32768
    px0, px1 = int((x0 - tx0) * 256), int((x1 - tx0) * 256)
    py0, py1 = int((y0 - ty0) * 256), int((y1 - ty0) * 256)
    H = H[py0:py1, px0:px1]
    Hi = np.asarray(Image.fromarray(H).resize((H.shape[1] * S, H.shape[0] * S), Image.BICUBIC))
    sea = Hi <= 0.5
    if name == "macro":
        m = Image.fromarray((sea * 255).astype(np.uint8))
        sm = m.resize((m.size[0] // 4, m.size[1] // 4), Image.BILINEAR).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
        sea = np.asarray(sm.resize(m.size, Image.BILINEAR)) > 127
    else:
        sea[:] = False
    cell = 40075000 * math.cos(math.radians(np.mean(lat))) / (2 ** z * 256 * S)
    hs = 0.65 * hillshade(Hi, cell, 315, 38, zf) + 0.35 * hillshade(Hi, cell, 250, 50, zf)
    hs = np.clip(hs, 0, 1)
    e = np.clip(Hi, 0, 5000)
    if name == "macro":
        v = np.log1p(e / 60) / np.log1p(5000 / 60)
        base = ramp(v, [(0, (58, 62, 52)), (0.25, (70, 72, 58)), (0.5, (96, 88, 68)), (0.75, (124, 112, 90)), (1, (170, 164, 150))])
    else:
        v = np.clip(e / 450, 0, 1)
        base = ramp(v, [(0, (60, 66, 54)), (0.08, (66, 70, 56)), (0.3, (92, 86, 66)), (1, (140, 128, 104))])
    img = base * (0.42 + 0.85 * hs[..., None])
    water = np.array([18, 30, 40], np.float32)
    img[sea] = water
    # vignette-free; keep neutral, scenes darken as needed
    img = np.clip(img, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(f"{ROOT}/assets/{name}.jpg", quality=90)
    if name == "macro":
        Image.fromarray(((~sea) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)).save(f"{ROOT}/assets/macro_land.png")
    # mercator params: pixel = (X - mx0) * scale, X in [0,1] web-mercator units
    n = 2 ** z * 256 * S
    return dict(mx0=(tx0 * 256 + px0) / (2 ** z * 256), my0=(ty0 * 256 + py0) / (2 ** z * 256), scale=n, w=img.shape[1], h=img.shape[0])


def rivers(bbox):
    p = f"{ROOT}/cache/ne_rivers.geojson"
    if not os.path.exists(p):
        url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_lake_centerlines.geojson"
        open(p, "wb").write(urllib.request.urlopen(url, timeout=60).read())
    g = json.load(open(p))
    out = []
    keep = {"Chang Jiang", "Yangtze", "Huang", "Huang He", "Huai", "Huai He", "Han", "Han Shui", "Wei", "Wei He", "Ying", "Ying He", "Jialing", "Fen", "Fen He", "Luo", "Yalong", "Min", "Wu", "Xiang", "Gan"}
    for f in g["features"]:
        nm = (f["properties"].get("name") or "")
        sr = f["properties"].get("scalerank", 9)
        geo = f["geometry"]
        lines = geo["coordinates"] if geo["type"] == "MultiLineString" else [geo["coordinates"]]
        for ln in lines:
            pts = [(round(x, 3), round(y, 3)) for x, y in ln if bbox[0] <= x <= bbox[1] and bbox[2] <= y <= bbox[3]]
            if len(pts) > 1 and (sr <= 6 or nm in keep):
                out.append(dict(name=nm, rank=sr, pts=pts))
    return out


if __name__ == "__main__":
    geo = {}
    for k, v in PLATES.items():
        geo[k] = plate(k, **v)
        print(k, geo[k])
    geo["rivers"] = rivers((97, 125, 19.5, 43))
    print("rivers", len(geo["rivers"]), sorted({r["name"] for r in geo["rivers"]})[:60])
    json.dump(geo, open(f"{ROOT}/assets/geo.json", "w"), ensure_ascii=False)
