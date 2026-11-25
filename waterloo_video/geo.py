# -*- coding: utf-8 -*-
"""Map data (approximate lat/lon, 示意) and map background renderers (hillshade)."""
import os, math
import numpy as np
import cairo
from gfx import *

CACHE = os.environ.get("WORK", "/tmp/claude-0/work") + "/cache"
os.makedirs(CACHE, exist_ok=True)


class Proj:
    def __init__(self, lon0, lon1, lat0, lat1, width):
        self.lon0, self.lat1 = lon0, lat1
        self.c = math.cos(math.radians((lat0 + lat1) / 2))
        self.k = width / ((lon1 - lon0) * self.c)
        self.w = int(width)
        self.h = int((lat1 - lat0) * self.k)

    def __call__(self, lon, lat):
        return ((lon - self.lon0) * self.c * self.k, (self.lat1 - lat) * self.k)

    def pts(self, ll):
        return [self(a, b) for a, b in ll]


# ---------------------------------------------------------------- big map (campaign)
BIG = Proj(4.18, 5.00, 50.36, 50.92, 1800)
TOWNS = {  # name: (lon, lat, size)
    "布鲁塞尔": (4.3525, 50.8467, 2), "滑铁卢": (4.3990, 50.7146, 1), "圣让山": (4.4080, 50.6870, 1),
    "瓦弗尔": (4.6010, 50.7170, 2), "圣朗贝尔": (4.4920, 50.7000, 0), "四臂村": (4.4530, 50.5710, 1),
    "利尼": (4.5790, 50.5130, 1), "让布卢": (4.6990, 50.5610, 1), "瓦尔安": (4.6990, 50.6250, 0),
    "沙勒罗瓦": (4.4446, 50.4108, 2), "那慕尔": (4.8720, 50.4674, 2), "尼韦勒": (4.3280, 50.5980, 0),
    "热纳普": (4.4520, 50.6110, 0),
}
RIVERS_BIG = {
    "代勒河": [(4.565, 50.56), (4.575, 50.62), (4.585, 50.67), (4.592, 50.70), (4.603, 50.718), (4.625, 50.76), (4.66, 50.84), (4.69, 50.90)],
    "桑布尔河": [(4.20, 50.42), (4.33, 50.405), (4.445, 50.412), (4.56, 50.43), (4.68, 50.455), (4.80, 50.462), (4.872, 50.467)],
    "默兹河": [(4.80, 50.36), (4.86, 50.43), (4.872, 50.467), (4.93, 50.50), (5.00, 50.53)],
    "拉斯讷溪": [(4.45, 50.62), (4.47, 50.66), (4.485, 50.69), (4.52, 50.71), (4.56, 50.725), (4.60, 50.74)],
}
ROADS_BIG = [
    [(4.3525, 50.8467), (4.380, 50.78), (4.399, 50.7146), (4.408, 50.687), (4.416, 50.670), (4.452, 50.611), (4.453, 50.571), (4.444, 50.4108)],
    [(4.328, 50.598), (4.453, 50.571), (4.600, 50.528), (4.75, 50.50), (4.872, 50.4674)],
    [(4.601, 50.717), (4.65, 50.64), (4.699, 50.561), (4.76, 50.51), (4.872, 50.4674)],
    [(4.408, 50.687), (4.47, 50.695), (4.492, 50.700), (4.55, 50.712), (4.601, 50.717)],
    [(4.3525, 50.8467), (4.46, 50.80), (4.601, 50.717)],
]
FOREST_BIG = [(4.36, 50.80), (4.44, 50.81), (4.49, 50.78), (4.47, 50.74), (4.42, 50.73), (4.37, 50.75)]


def _terrain_shade(h, light=(-1, -1.4), z=1.0):
    gy, gx = np.gradient(h * z)
    lx, ly = light
    n = np.sqrt(gx ** 2 + gy ** 2 + 1)
    l = np.sqrt(lx ** 2 + ly ** 2 + 1)
    return (-gx * lx - gy * ly + 1) / (n * l)


def build_bigmap():
    fn = f"{CACHE}/bigmap.png"
    if os.path.exists(fn):
        return cairo.ImageSurface.create_from_png(fn)
    w, h = BIG.w, BIG.h
    rng = np.random.default_rng(11)
    hm = noise2d(h, w, 90, rng, 5) * 60 + noise2d(h, w, 22, rng, 3) * 10
    # river valleys
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for nm, ll in RIVERS_BIG.items():
        pts = smooth(BIG.pts(ll), 10)
        d = np.full((h, w), 1e9, np.float32)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            vx, vy = x1 - x0, y1 - y0
            L = vx * vx + vy * vy + 1e-6
            t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L, 0, 1)
            d = np.minimum(d, (xx - x0 - t * vx) ** 2 + (yy - y0 - t * vy) ** 2)
        hm -= 22 * np.exp(-d / (2 * 45 ** 2))
    sh = _terrain_shade(hm, z=1.2)
    base = np.array([0.16, 0.15, 0.12])
    tint = (hm - hm.min()) / (hm.max() - hm.min())
    col = base[None, None] * (0.75 + 0.5 * sh[..., None]) + np.array([0.03, 0.035, 0.01])[None, None] * tint[..., None]
    grain = noise2d(h, w, 2, rng, 2)[..., None] * 0.04
    col = np.clip(col + grain - 0.02, 0, 1)
    s = surface_from_rgb(col.astype(np.float32))
    ctx = cairo.Context(s)
    # forest
    fp = smooth(BIG.pts(FOREST_BIG + [FOREST_BIG[0]]), 8)
    path(ctx, fp); ctx.close_path(); ctx.set_source_rgba(0.10, 0.17, 0.10, 0.55); ctx.fill()
    # rivers
    for nm, ll in RIVERS_BIG.items():
        pts = smooth(BIG.pts(ll), 10)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        path(ctx, pts); ctx.set_source_rgba(0.35, 0.42, 0.42, 0.30); ctx.set_line_width(10); ctx.stroke()
        path(ctx, pts); ctx.set_source_rgba(0.50, 0.58, 0.58, 0.55); ctx.set_line_width(3); ctx.stroke()
    # roads
    for r in ROADS_BIG:
        pts = smooth(BIG.pts(r), 8)
        path(ctx, pts); ctx.set_source_rgba(0.75, 0.66, 0.50, 0.30); ctx.set_line_width(5); ctx.stroke()
        ctx.set_dash([2, 9]); path(ctx, pts); ctx.set_source_rgba(0.9, 0.82, 0.65, 0.35); ctx.set_line_width(2); ctx.stroke(); ctx.set_dash([])
    s.write_to_png(fn)
    return s


def draw_big_labels(ctx, alpha=1.0, scale=1.0, skip=()):
    for nm, (lo, la, sz) in TOWNS.items():
        if nm in skip:
            continue
        x, y = BIG(lo, la)
        fs = (34, 40, 48)[sz] / scale ** 0.5
        r = (6, 8, 11)[sz] / scale ** 0.5
        ctx.arc(x, y, r + 3, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.7 * alpha); ctx.fill()
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(*IVORY, alpha); ctx.fill()
        dx = {"瓦尔安": 1, "圣朗贝尔": 1, "滑铁卢": -1, "圣让山": -1, "四臂村": -1, "热纳普": -1, "尼韦勒": -1, "沙勒罗瓦": 1}.get(nm, 1)
        text(ctx, nm, x + dx * (r + 12), y, fs, IVORY, alpha, "lm" if dx > 0 else "rm", bold=sz == 2, halo=fs * 0.3, halo_a=0.9)


# ---------------------------------------------------------------- battlefield
FIELD = Proj(4.366, 4.506, 50.648, 50.706, 2000)
PLACES = {
    "乌古蒙": (4.3929, 50.6703), "拉艾圣": (4.4110, 50.6780), "帕普洛特": (4.4340, 50.6775),
    "普朗斯努瓦": (4.4335, 50.6625), "美丽联盟": (4.4166, 50.6697), "圣让山": (4.4080, 50.6870),
    "罗松": (4.4190, 50.6610),
}
ROADS_F = {
    "char": [(4.4045, 50.705), (4.4080, 50.6870), (4.4110, 50.6780), (4.4166, 50.6697), (4.4190, 50.6610), (4.422, 50.648)],
    "niv": [(4.4080, 50.6870), (4.398, 50.680), (4.385, 50.672), (4.370, 50.662)],
    "ohain": [(4.380, 50.6835), (4.400, 50.6833), (4.4110, 50.6830), (4.425, 50.6825), (4.440, 50.6815), (4.455, 50.684), (4.475, 50.690), (4.492, 50.700)],
    "planc": [(4.4166, 50.6697), (4.425, 50.666), (4.4335, 50.6625), (4.450, 50.660), (4.47, 50.667)],
}
WOOD_F = {
    "巴黎林": [(4.452, 50.672), (4.470, 50.674), (4.478, 50.666), (4.468, 50.660), (4.455, 50.662)],
    "hougo": [(4.3895, 50.6715), (4.3965, 50.6712), (4.3965, 50.6683), (4.3895, 50.6686)],
}


def field_height(w, h):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lat = FIELD.lat1 - yy / FIELD.k
    lon = FIELD.lon0 + xx / (FIELD.k * FIELD.c)
    hm = 22 * np.exp(-((lat - 50.6840) / 0.0040) ** 2)          # Mont-St-Jean ridge
    hm += 16 * np.exp(-((lat - 50.6690) / 0.0045) ** 2)         # Belle-Alliance ridge
    hm += 10 * np.clip((lat - 50.690) / 0.01, 0, 1)
    hm -= 26 * np.exp(-((lon - 4.470 - (lat - 50.66) * 0.6) / 0.010) ** 2)   # Lasne valley east
    hm -= 10 * np.clip((lon - 4.445) / 0.03, 0, 1)
    rng = np.random.default_rng(3)
    hm += noise2d(h, w, 60, rng, 4) * 6
    return hm, lat, lon


def build_field():
    fn = f"{CACHE}/field.png"
    if os.path.exists(fn):
        return cairo.ImageSurface.create_from_png(fn)
    w, h = FIELD.w, FIELD.h
    hm, lat, lon = field_height(w, h)
    sh = _terrain_shade(hm, light=(-1, -1.2), z=5.0)
    rng = np.random.default_rng(5)
    e = (hm - hm.min()) / (hm.max() - hm.min())
    low = np.array([0.16, 0.19, 0.12]); high = np.array([0.42, 0.36, 0.22])
    col = low * (1 - e[..., None]) + high * e[..., None]
    # field parcels: rotated grid with random tint
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = (xx * 0.94 + yy * 0.34) / 150.0; v = (-xx * 0.34 + yy * 0.94) / 95.0
    cell = (np.floor(u).astype(np.int64) * 7349 + np.floor(v).astype(np.int64) * 1931) % 997 / 997.0
    tint = np.stack([0.035 * (cell - 0.5), 0.03 * (np.sin(cell * 20) * 0.5), -0.02 * (cell - 0.5)], -1)
    edge = (np.minimum(u % 1, 1 - u % 1) < 0.02) | (np.minimum(v % 1, 1 - v % 1) < 0.03)
    col = col + tint
    col[edge] *= 0.9
    col = col * (0.35 + 0.95 * np.clip(sh, 0, 1.4)[..., None])
    col = np.clip(col + (noise2d(h, w, 3, rng, 2)[..., None] - 0.5) * 0.05, 0, 1)
    s = surface_from_rgb(col.astype(np.float32))
    ctx = cairo.Context(s)
    # contours
    lv = np.arange(-30, 40, 6)
    ctx.set_line_width(1.2)
    for L in lv:
        m = (hm[:-1, :] < L) != (hm[1:, :] < L)
        ys, xs = np.nonzero(m[::3, ::3])
        ctx.set_source_rgba(0.95, 0.85, 0.6, 0.10)
        for y, x in zip(ys, xs):
            ctx.rectangle(x * 3, y * 3, 2, 2)
        ctx.fill()
    for nm, ll in WOOD_F.items():
        pts = smooth(FIELD.pts(ll + [ll[0]]), 6)
        path(ctx, pts); ctx.close_path(); ctx.set_source_rgba(0.08, 0.15, 0.08, 0.75); ctx.fill()
        rng2 = np.random.default_rng(len(nm))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for _ in range(120 if nm != "hougo" else 25):
            x = rng2.uniform(min(xs), max(xs)); y = rng2.uniform(min(ys), max(ys))
            ctx.arc(x, y, rng2.uniform(5, 11), 0, 6.3); ctx.set_source_rgba(0.12, 0.22, 0.11, 0.35); ctx.fill()
    for k, ll in ROADS_F.items():
        pts = smooth(FIELD.pts(ll), 8)
        path(ctx, pts); ctx.set_source_rgba(0.12, 0.1, 0.07, 0.6); ctx.set_line_width(12 if k == "char" else 8); ctx.stroke()
        path(ctx, pts); ctx.set_source_rgba(0.78, 0.70, 0.52, 0.55); ctx.set_line_width(6 if k == "char" else 4); ctx.stroke()
    # farm compounds
    for nm in ("乌古蒙", "拉艾圣", "帕普洛特", "美丽联盟", "圣让山"):
        x, y = FIELD(*PLACES[nm])
        ctx.rectangle(x - 16, y - 12, 32, 24); ctx.set_source_rgba(0.55, 0.45, 0.35, 0.95); ctx.fill_preserve()
        ctx.set_source_rgba(0, 0, 0, 0.7); ctx.set_line_width(2); ctx.stroke()
    x, y = FIELD(*PLACES["普朗斯努瓦"])
    rng3 = np.random.default_rng(9)
    for _ in range(22):
        ctx.rectangle(x + rng3.uniform(-50, 50), y + rng3.uniform(-35, 35), 12, 10)
    ctx.set_source_rgba(0.55, 0.45, 0.35, 0.95); ctx.fill()
    s.write_to_png(fn)
    return s


def build_field_height_cache():
    return field_height(FIELD.w, FIELD.h)[0]
