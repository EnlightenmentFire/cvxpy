# -*- coding: utf-8 -*-
"""Build hillshaded basemaps (day/night) for the regional (z11) and battlefield (z13) maps.
DEM: Mapzen/AWS terrarium tiles. Water: extracted from OSM raster tiles (© OpenStreetMap contributors)."""
import glob, json, numpy as np
from PIL import Image
from scipy import ndimage as ndi

D = "/tmp/claude-0/work/dem"
OUT = "/tmp/claude-0/work/base"


def mosaic(z, pat):
    fs = [f for f in glob.glob(f"{pat}/{z}_*.png")]
    xs = sorted({int(f.split("_")[-2]) for f in fs}); ys = sorted({int(f.split("_")[-1][:-4]) for f in fs})
    return xs, ys


def load(z):
    xs, ys = mosaic(z, D)
    H = np.zeros((256 * len(ys), 256 * len(xs)), np.float32)
    Wm = np.zeros_like(H, dtype=bool)
    for x in xs:
        for y in ys:
            a = np.asarray(Image.open(f"{D}/{z}_{x}_{y}.png").convert("RGB")).astype(np.float32)
            H[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
            o = np.asarray(Image.open(f"{D}/osm/{z}_{x}_{y}.png").convert("RGB")).astype(int)
            w = (abs(o[..., 0] - 170) < 8) & (abs(o[..., 1] - 211) < 8) & (abs(o[..., 2] - 223) < 8)
            Wm[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = w
    return H, Wm, xs[0], ys[0]


def clean_water(Wm, min_lake):
    m = ndi.binary_closing(Wm, iterations=3)
    lab, n = ndi.label(m)
    sz = ndi.sum(m, lab, range(1, n + 1))
    lakes = np.isin(lab, 1 + np.nonzero(sz >= min_lake)[0])
    lakes = ndi.binary_fill_holes(lakes)
    lakes = ndi.binary_opening(lakes, iterations=2)
    # rivers: thin water lines that are long
    rv = Wm & ~lakes
    lab, n = ndi.label(ndi.binary_dilation(rv))
    sz = ndi.sum(rv, lab, range(1, n + 1))
    rivers = np.isin(lab, 1 + np.nonzero(sz >= min_lake * 0.05)[0]) & rv
    return lakes, rivers


def shade(H, cell):
    gy, gx = np.gradient(H, cell)
    out = 0
    for az, w in ((315, 0.55), (270, 0.2), (0, 0.25)):
        a = np.radians(az); alt = np.radians(40)
        sl = np.arctan(np.hypot(gx, gy) * 1.6)
        asp = np.arctan2(-gx, gy)
        hs = np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(a - asp - np.pi / 2)
        out = out + w * hs
    return np.clip(out, 0, 1)


def lerp_pal(v, stops):
    v = np.clip(v, 0, 1); out = np.zeros(v.shape + (3,), np.float32)
    ks = [s[0] for s in stops]
    for i in range(len(stops) - 1):
        a, ca = stops[i]; b, cb = stops[i + 1]
        m = (v >= a) & (v <= b)
        t = ((v - a) / (b - a))[m][:, None]
        out[m] = np.array(ca) * (1 - t) + np.array(cb) * t
    return out


def build(z, name, scale, min_lake, emax, cell):
    H, Wm, x0, y0 = load(z)
    lakes, rivers = clean_water(Wm, min_lake)
    if scale != 1:
        Hi = Image.fromarray(H).resize((int(H.shape[1] * scale), int(H.shape[0] * scale)), Image.BICUBIC)
        H = np.asarray(Hi).astype(np.float32)
        lakes = np.asarray(Image.fromarray(lakes.astype(np.uint8) * 255).resize(Hi.size, Image.BILINEAR).filter(__import__("PIL.ImageFilter").ImageFilter.GaussianBlur(1.2))) > 127
        rivers = np.asarray(Image.fromarray(rivers.astype(np.uint8) * 255).resize(Hi.size, Image.BILINEAR)) > 90
    Hs = ndi.gaussian_filter(H, 0.6)
    hs = shade(Hs, cell / scale)
    e = np.clip(H, 0, None) / emax
    for mode in ("day", "night"):
        if mode == "day":
            pal = [(0, (74, 72, 52)), (0.12, (92, 86, 60)), (0.35, (112, 98, 70)), (0.7, (128, 112, 86)), (1, (150, 140, 120))]
            water = np.array((22, 38, 52)); riv = np.array((44, 70, 88))
        else:
            pal = [(0, (24, 30, 40)), (0.2, (30, 36, 48)), (0.5, (38, 42, 56)), (1, (52, 56, 70))]
            water = np.array((6, 12, 22)); riv = np.array((16, 28, 42))
        base = lerp_pal(e, pal)
        lit = 0.35 + 0.95 * hs[..., None]
        img = np.clip(base * lit, 0, 255)
        # water with shore glow
        dist = ndi.distance_transform_edt(lakes)
        shore = np.exp(-dist / (6 * scale))[..., None]
        wcol = water * (1 - 0.0) + (np.array((70, 92, 100)) if mode == "day" else np.array((30, 44, 60))) * 0.6 * shore
        img = np.where(lakes[..., None], wcol, img)
        img = np.where(rivers[..., None] & ~lakes[..., None], img * 0.4 + riv * 0.6, img)
        # vignette-ish contrast curve
        img = 255 * (img / 255) ** 1.08
        Image.fromarray(img.astype(np.uint8)).save(f"{OUT}/{name}_{mode}.png")
    np.save(f"{OUT}/{name}_lakes.npy", lakes)
    json.dump(dict(z=z, x0=x0, y0=y0, s=scale, w=H.shape[1], h=H.shape[0]), open(f"{OUT}/{name}.json", "w"))
    print(name, H.shape)


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    build(11, "region", 1.0, 3000, 1600, 76.0 * 0.82)
    build(13, "local", 2.0, 1500, 900, 19.1 * 0.82)
