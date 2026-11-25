# -*- coding: utf-8 -*-
"""Download Terrarium elevation tiles (AWS open data, Mapzen terrain tiles) and stitch DEM arrays
for the three map extents. Output: WORK/cache/dem_<name>.npy (+ .json with bounds).
Coastline mask: Natural Earth 10 m land (public domain) rasterised with cairo, combined with elevation.
usage: python fetch_dem.py
"""
import os, math, json, io, urllib.request
import numpy as np
from PIL import Image
import cairo

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
TILES = "/tmp/claude-0/geo/tiles"
CACHE = f"{WORK}/cache"
os.makedirs(TILES, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
NE = "/tmp/claude-0/geo/ne.json"

EXTENTS = {
    # name: (lon0, lon1, lat0, lat1, zoom)
    "nation": (129.6, 142.2, 30.9, 41.4, 7),
    "region": (135.2, 138.1, 33.9, 35.9, 10),
    "owari": (136.70, 137.26, 34.90, 35.46, 12),
}


def deg2num(lon, lat, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def tile(z, x, y):
    fn = f"{TILES}/{z}_{x}_{y}.png"
    if not os.path.exists(fn):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        for k in range(4):
            try:
                data = urllib.request.urlopen(url, timeout=30).read(); break
            except Exception:
                if k == 3:
                    raise
        open(fn, "wb").write(data)
    a = np.asarray(Image.open(fn).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def build(name):
    lon0, lon1, lat0, lat1, z = EXTENTS[name]
    x0, y0 = deg2num(lon0, lat1, z)
    x1, y1 = deg2num(lon1, lat0, z)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    rows = []
    for ty in range(ty0, ty1 + 1):
        rows.append(np.concatenate([tile(z, tx, ty) for tx in range(tx0, tx1 + 1)], 1))
    M = np.concatenate(rows, 0)
    # crop to exact bounds in mercator pixel space, then resample to equirectangular grid (lat-linear)
    out_w = int((x1 - x0) * 256)
    c = math.cos(math.radians((lat0 + lat1) / 2))
    out_h = int(out_w * (lat1 - lat0) / ((lon1 - lon0) * c))
    lons = np.linspace(lon0, lon1, out_w)
    lats = np.linspace(lat1, lat0, out_h)
    px = (np.array([deg2num(l, lat0, z)[0] for l in lons]) - tx0) * 256
    py = (np.array([deg2num(lon0, l, z)[1] for l in lats]) - ty0) * 256
    xi = np.clip(px.astype(int), 0, M.shape[1] - 1)
    yi = np.clip(py.astype(int), 0, M.shape[0] - 1)
    D = M[yi][:, xi]
    # land mask from Natural Earth polygons
    s = cairo.ImageSurface(cairo.FORMAT_A8, out_w, out_h)
    ctx = cairo.Context(s)
    gj = json.load(open(NE))
    kx = out_w / (lon1 - lon0); ky = out_h / (lat1 - lat0)
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
                if max(xs) < lon0 or min(xs) > lon1 or max(ys) < lat0 or min(ys) > lat1:
                    continue
                ctx.move_to((ring[0][0] - lon0) * kx, (lat1 - ring[0][1]) * ky)
                for p in ring[1:]:
                    ctx.line_to((p[0] - lon0) * kx, (lat1 - p[1]) * ky)
                ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(0, 0, 0, 1); ctx.fill()
    s.flush()
    st = s.get_stride()
    mask = np.ndarray((out_h, st), np.uint8, s.get_data())[:, :out_w].astype(np.float32) / 255
    np.save(f"{CACHE}/dem_{name}.npy", D.astype(np.float32))
    np.save(f"{CACHE}/land_{name}.npy", mask.astype(np.float32))
    json.dump(dict(lon0=lon0, lon1=lon1, lat0=lat0, lat1=lat1, w=out_w, h=out_h), open(f"{CACHE}/dem_{name}.json", "w"))
    print(name, D.shape, float(D.min()), float(D.max()))


if __name__ == "__main__":
    for n in EXTENTS:
        build(n)
