# -*- coding: utf-8 -*-
"""Map base layers from Natural Earth (public domain). Equirectangular with cos(lat0) x-scaling."""
import json, math, os, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import (W, H, new, font, SANS, SANS_B, SERIF_B, GOLD, GOLD_L, IVORY, SEA, LAND, LAND_L, noise_tex, comp)

GEO = "/tmp/claude-0/geo"
CACHE = "/tmp/claude-0/work/cache"
os.makedirs(CACHE, exist_ok=True)


@functools.lru_cache(maxsize=4)
def _features(name):
    return json.load(open(f"{GEO}/{name}.geojson"))["features"]


class Proj:
    def __init__(self, lon0, lon1, lat0, lat1, box):
        self.lon0, self.lon1, self.lat0, self.lat1 = lon0, lon1, lat0, lat1
        self.box = box  # x0, y0, x1, y1 in frame px
        self.k = math.cos(math.radians((lat0 + lat1) / 2))
        sx = (box[2] - box[0]) / ((lon1 - lon0) * self.k)
        sy = (box[3] - box[1]) / (lat1 - lat0)
        self.s = min(sx, sy)
        self.cx = (box[0] + box[2]) / 2
        self.cy = (box[1] + box[3]) / 2
        self.mlon = (lon0 + lon1) / 2
        self.mlat = (lat0 + lat1) / 2

    def __call__(self, lon, lat):
        return (self.cx + (lon - self.mlon) * self.k * self.s, self.cy - (lat - self.mlat) * self.s)

    def pts(self, coords):
        return [self(c[0], c[1]) for c in coords]


def _rings(geom):
    if geom["type"] == "Polygon":
        yield geom["coordinates"][0]
    elif geom["type"] == "MultiPolygon":
        for p in geom["coordinates"]:
            yield p[0]


def _lines(geom):
    if geom["type"] == "LineString":
        yield geom["coordinates"]
    elif geom["type"] == "MultiLineString":
        for l in geom["coordinates"]:
            yield l


def base_map(key, proj, land="ne_50m_land", rivers=False, river_filter=None, grat=10, sea=SEA, land_col=LAND,
             coast=GOLD, extra_pad=2.0):
    """Full-frame RGBA map plate (transparent outside proj box is not needed: we draw full frame)."""
    path = f"{CACHE}/map_{key}.png"
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    img = Image.new("RGBA", (W, H), tuple(sea) + (255,))
    # sea gradient + texture
    arr = np.asarray(img, np.float32)
    n = np.asarray(noise_tex(21), np.float32)[..., None] / 255.0
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    arr[..., :3] = arr[..., :3] * (0.85 + 0.25 * n) * (1.1 - 0.25 * yy)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    # graticule
    if grat:
        gl = new(); gd = ImageDraw.Draw(gl)
        for lon in range(-180, 181, grat):
            if proj.lon0 - 20 < lon < proj.lon1 + 20:
                gd.line([proj(lon, la) for la in np.linspace(proj.lat0 - 30, proj.lat1 + 30, 30)], fill=(120, 150, 170, 40), width=1)
        for la in range(-80, 81, grat):
            if proj.lat0 - 20 < la < proj.lat1 + 20:
                gd.line([proj(lo, la) for lo in np.linspace(proj.lon0 - 40, proj.lon1 + 40, 30)], fill=(120, 150, 170, 40), width=1)
        img.alpha_composite(gl)
    # land
    lm = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(lm)
    lo0, lo1 = proj.lon0 - 40, proj.lon1 + 40
    la0, la1 = proj.lat0 - 30, proj.lat1 + 30
    rings = []
    for f in _features(land):
        for r in _rings(f["geometry"]):
            xs = [c[0] for c in r]; ys = [c[1] for c in r]
            if max(xs) < lo0 or min(xs) > lo1 or max(ys) < la0 or min(ys) > la1 or max(ys) < -58:
                continue
            p = proj.pts(r)
            if len(p) > 2:
                ld.polygon(p, fill=255)
                rings.append(p)
    tex = np.asarray(noise_tex(33), np.float32)[..., None] / 255.0
    land_arr = np.array(land_col, np.float32)[None, None] * (0.9 + 0.2 * tex)
    # inner shading: darker toward coast for relief feel
    inner = np.asarray(lm.filter(ImageFilter.GaussianBlur(18)), np.float32)[..., None] / 255.0
    land_arr = land_arr * (0.75 + 0.35 * inner)
    land_img = Image.fromarray(np.clip(land_arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    land_img.putalpha(lm)
    # soft coastal glow on sea
    cg = Image.new("RGBA", (W, H), tuple(GOLD) + (0,))
    cg.putalpha(lm.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.22)))
    img.alpha_composite(cg)
    img.alpha_composite(land_img)
    cl = new(); cd = ImageDraw.Draw(cl)
    for p in rings:
        cd.line(p + [p[0]], fill=tuple(coast) + (170,), width=2)
    img.alpha_composite(cl)
    if rivers:
        rl = new(); rd = ImageDraw.Draw(rl)
        for f in _features("ne_10m_rivers_lake_centerlines"):
            nm = f["properties"].get("name") or ""
            if river_filter and not river_filter(nm, f["properties"]):
                continue
            for l in _lines(f["geometry"]):
                xs = [c[0] for c in l]; ys = [c[1] for c in l]
                if not xs or max(xs) < lo0 or min(xs) > lo1 or max(ys) < la0 or min(ys) > la1:
                    continue
                sr = f["properties"].get("scalerank", 6) or 6
                rd.line(proj.pts(l), fill=(110, 160, 190, 200), width=max(2, int(6 - sr * 0.45)), joint="curve")
        img.alpha_composite(rl)
    img.save(path)
    return img


def marker(d, xy, r=10, color=GOLD, ring=True):
    x, y = xy
    if ring:
        d.ellipse((x - r * 2, y - r * 2, x + r * 2, y + r * 2), outline=tuple(color) + (150,), width=2)
    d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(color) + (255,), outline=(20, 16, 10, 255), width=2)


def fort_icon(d, x, y, s, color=GOLD):
    """Star-fort / bastion icon centred at (x,y)."""
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = s if i % 2 == 0 else s * 0.55
        pts.append((x + r * math.cos(a), y - r * math.sin(a)))
    d.polygon(pts, fill=tuple(color) + (235,), outline=(30, 22, 12, 255))
    d.rectangle((x - s * 0.22, y - s * 0.22, x + s * 0.22, y + s * 0.22), fill=(40, 30, 18, 255))


# --------------------------------------------------------------- standard projections used in the film
STAGE = (40, 300, 1040, 1290)

P_WORLD = Proj(-22, 98, -40, 58, (20, 330, 1060, 1290))
P_INDIA = Proj(66.5, 93.5, 6.5, 31.5, (60, 300, 1020, 1290))
P_BENGAL = Proj(85.6, 90.8, 21.4, 25.6, (40, 300, 1040, 1290))
P_NORTH = Proj(79.5, 90.5, 21.0, 29.0, (40, 300, 1040, 1290))
P_CARIB = Proj(-68, -60, 15, 21, (40, 300, 1040, 1290))

PLACES = {
    "London": (-0.12, 51.5), "Cape": (18.47, -34.36), "Madras": (80.29, 13.08), "Bombay": (72.84, 18.94),
    "Calcutta": (88.36, 22.57), "Murshidabad": (88.27, 24.18), "Plassey": (88.25, 23.80),
    "Chandernagore": (88.37, 22.87), "Delhi": (77.21, 28.65), "Patna": (85.14, 25.6), "Buxar": (83.98, 25.57),
    "Allahabad": (81.85, 25.43), "Amsterdam": (4.9, 52.37), "Lisbon": (-9.14, 38.72), "Goa": (73.83, 15.49),
    "Batavia": (106.8, -6.2), "Pondicherry": (79.83, 11.93), "Dhaka": (90.41, 23.81),
}

# Bhagirathi-Hooghly (hand traced, schematic)
HOOGHLY = [(87.93, 24.78), (88.07, 24.47), (88.25, 24.20), (88.27, 23.98), (88.24, 23.80), (88.13, 23.64),
           (88.37, 23.40), (88.40, 23.15), (88.37, 22.87), (88.35, 22.57), (88.22, 22.25), (88.05, 21.95), (88.0, 21.6)]
# a schematic main Ganges / Padma course
GANGES = [(84.0, 25.6), (85.14, 25.62), (86.5, 25.35), (87.6, 25.12), (87.93, 24.78), (88.6, 24.35), (89.3, 23.9),
          (89.8, 23.5), (90.3, 23.1), (90.6, 22.6), (90.8, 22.1)]


def world_map():
    return base_map("world", P_WORLD, land="ne_50m_land", grat=15)


def india_map():
    return base_map("india", P_INDIA, land="ne_50m_land", rivers=True,
                    river_filter=lambda n, p: (p.get("scalerank") or 9) <= 6, grat=5)


def bengal_map():
    img = base_map("bengal_raw", P_BENGAL, land="ne_10m_land", grat=1)
    path = f"{CACHE}/map_bengal.png"
    if os.path.exists(path):
        return Image.open(path).convert("RGBA")
    rl = new(); rd = ImageDraw.Draw(rl)
    for course, w in ((GANGES, 9), (HOOGHLY, 7)):
        p = P_BENGAL.pts(course)
        rd.line(p, fill=(90, 150, 190, 230), width=w, joint="curve")
    img.alpha_composite(rl.filter(ImageFilter.GaussianBlur(1.0)))
    img.save(path)
    return img


def carib_map():
    return base_map("carib", P_CARIB, land="ne_10m_land", grat=2)


def north_map():
    return base_map("north", P_NORTH, land="ne_10m_land", rivers=True,
                    river_filter=lambda n, p: (p.get("scalerank") or 9) <= 8, grat=2)
