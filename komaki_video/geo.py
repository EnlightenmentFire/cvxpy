# -*- coding: utf-8 -*-
"""Map data (approximate lat/lon, 示意) and hillshaded sand-table base maps built from Terrarium DEM
(fetch_dem.py) + Natural Earth 10 m land mask."""
import os, math, json
import numpy as np
import cairo
from gfx import *

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
CACHE = f"{WORK}/cache"


class Proj:
    def __init__(self, lon0, lon1, lat0, lat1, width):
        self.lon0, self.lon1, self.lat0, self.lat1 = lon0, lon1, lat0, lat1
        self.c = math.cos(math.radians((lat0 + lat1) / 2))
        self.k = width / ((lon1 - lon0) * self.c)
        self.w = int(width)
        self.h = int(round((lat1 - lat0) * self.k))

    def __call__(self, lon, lat):
        return ((lon - self.lon0) * self.c * self.k, (self.lat1 - lat) * self.k)

    def pts(self, ll):
        return [self(a, b) for a, b in ll]


def _meta(name):
    return json.load(open(f"{CACHE}/dem_{name}.json"))


SCALE = {"nation": 2.0, "region": 1.0, "owari": 1.15}


def proj(name):
    m = _meta(name)
    return Proj(m["lon0"], m["lon1"], m["lat0"], m["lat1"], m["w"] * SCALE[name])


# ---------------------------------------------------------------- places
# 全国（大名据点，示意）
NATION = {
    "大坂": (135.526, 34.687), "尾张·小牧": (136.912, 35.292), "滨松": (137.727, 34.711),
    "春日山": (138.21, 37.15), "常陆": (140.45, 36.40), "小田原": (139.153, 35.251),
    "土佐": (133.60, 33.60), "纪州": (135.33, 34.25), "越中": (137.21, 36.69), "加贺": (136.66, 36.56),
}
# 尾张—三河（示意）
OWARI = {
    "小牧山": (136.9122, 35.2925), "犬山城": (136.9394, 35.3884), "乐田": (136.9570, 35.3215),
    "羽黑": (136.950, 35.355), "清洲城": (136.8406, 35.2153), "小幡城": (136.9640, 35.2049),
    "岩崎城": (137.0418, 35.1595), "白山林": (137.0280, 35.2060), "长久手": (137.0600, 35.1790),
    "冈崎城": (137.1590, 34.9563), "色金山": (137.0640, 35.1880),
}
REGION = {
    "大坂": (135.526, 34.687), "长岛城": (136.700, 35.100), "伊贺": (136.130, 34.770),
    "伊势": (136.540, 34.620), "竹鼻城": (136.740, 35.335), "小牧山": (136.9122, 35.2925),
    "冈崎": (137.159, 34.956), "滨松": (137.727, 34.711), "清洲": (136.8406, 35.2153),
}


# ---------------------------------------------------------------- base maps
def _shade(h, light=(-1.0, -1.3), z=1.0):
    gy, gx = np.gradient(h * z)
    lx, ly = light
    n = np.sqrt(gx ** 2 + gy ** 2 + 1)
    l = math.sqrt(lx ** 2 + ly ** 2 + 1)
    return (-gx * lx - gy * ly + 1) / (n * l)


def _resize(a, w, h):
    """bilinear resize of 2D float array"""
    H0, W0 = a.shape
    ys = np.linspace(0, H0 - 1, h); xs = np.linspace(0, W0 - 1, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, H0 - 1); x1 = np.minimum(x0 + 1, W0 - 1)
    fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    return (a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx) * (1 - fy) + (a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx) * fy


ZEX = {"nation": 0.004, "region": 0.02, "owari": 0.09}


def build_base(name):
    fn = f"{CACHE}/base_{name}.png"
    if os.path.exists(fn):
        return cairo.ImageSurface.create_from_png(fn)
    P = proj(name)
    D = np.load(f"{CACHE}/dem_{name}.npy"); L = np.load(f"{CACHE}/land_{name}.npy")
    D = _resize(D, P.w, P.h); L = _resize(L, P.w, P.h)
    land = np.clip(np.maximum(L, (D > 2).astype(np.float32) * (L > 0.02)), 0, 1)
    land = blur(land, 0.8)
    Dl = np.maximum(D, 0)
    sh = np.clip(_shade(blur(Dl, 1.0), z=ZEX[name]), 0, 1.6)
    rng = np.random.default_rng(7)
    e = np.clip(Dl / {"nation": 2200, "region": 1300, "owari": 450}[name], 0, 1) ** 0.6
    low = np.array([0.15, 0.135, 0.105]); high = np.array([0.33, 0.29, 0.22])
    col = low * (1 - e[..., None]) + high * e[..., None]
    col = col * (0.42 + 0.78 * sh[..., None])
    grain = (noise2d(P.h, P.w, 3, rng, 2)[..., None] - 0.5) * 0.035
    col = col + grain
    # sea: dark, deeper further from coast
    dist = blur(land, 18 if name != "nation" else 10)
    sea = np.array([0.035, 0.055, 0.075])[None, None] * (0.75 + 0.6 * dist[..., None])
    col = col * land[..., None] + sea * (1 - land[..., None])
    # coastline glow
    edge = np.clip(np.abs(np.gradient(land)[0]) + np.abs(np.gradient(land)[1]), 0, 1)
    edge = blur(edge, 1.2) * 2.2
    col = col + np.array([0.30, 0.36, 0.40])[None, None] * np.clip(edge, 0, 1)[..., None] * 0.35
    s = surface_from_rgb(np.clip(col, 0, 1).astype(np.float32))
    ctx = cairo.Context(s)
    # graticule (sand-table grid)
    step = {"nation": 1.0, "region": 0.25, "owari": 0.05}[name]
    ctx.set_line_width(1.2)
    ctx.set_source_rgba(0.85, 0.75, 0.55, 0.06)
    lo = math.ceil(P.lon0 / step) * step
    while lo < P.lon1:
        x, _ = P(lo, P.lat0); ctx.move_to(x, 0); ctx.line_to(x, P.h); lo += step
    la = math.ceil(P.lat0 / step) * step
    while la < P.lat1:
        _, y = P(P.lon0, la); ctx.move_to(0, y); ctx.line_to(P.w, y); la += step
    ctx.stroke()
    if name == "owari":
        _owari_details(ctx, P)
    s.write_to_png(fn)
    return s


# rivers (approximate, 示意)
RIVERS_OWARI = {
    "庄内川": [(137.02, 35.33), (136.99, 35.27), (136.965, 35.235), (136.93, 35.215), (136.89, 35.19), (136.86, 35.14), (136.85, 35.08)],
    "矢田川": [(137.04, 35.215), (137.0, 35.205), (136.96, 35.195), (136.925, 35.19)],
    "木曾川": [(137.02, 35.42), (136.95, 35.395), (136.90, 35.385), (136.83, 35.37), (136.77, 35.33), (136.72, 35.25)],
    "矢作川": [(137.20, 35.12), (137.17, 35.05), (137.16, 34.97), (137.12, 34.92)],
}
ROADS_OWARI = [
    [(136.957, 35.3215), (136.99, 35.27), (137.00, 35.23), (137.028, 35.206), (137.0418, 35.1595), (137.08, 35.10), (137.12, 35.02), (137.159, 34.9563)],
]


def _owari_details(ctx, P):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for nm, ll in RIVERS_OWARI.items():
        pts = smooth(P.pts(ll), 10)
        path(ctx, pts); ctx.set_source_rgba(0.25, 0.36, 0.42, 0.35); ctx.set_line_width(12); ctx.stroke()
        path(ctx, pts); ctx.set_source_rgba(0.42, 0.55, 0.62, 0.55); ctx.set_line_width(4); ctx.stroke()


def draw_place(ctx, name, x, y, alpha=1.0, size=34, dot=IVORY, side=1, bold=False, castle=False):
    alpha *= clamp((1340 - y) / 60) * clamp((y - 350) / 40) * clamp((x + 20) / 40) * clamp((W + 20 - x) / 40)
    if alpha <= 0:
        return
    r = 9 if castle else 7
    ctx.new_path()
    if castle:
        ctx.rectangle(x - r - 3, y - r - 3, 2 * r + 6, 2 * r + 6); ctx.set_source_rgba(0, 0, 0, 0.7 * alpha); ctx.fill()
        ctx.rectangle(x - r, y - r, 2 * r, 2 * r); ctx.set_source_rgba(*dot, alpha); ctx.fill()
    else:
        ctx.arc(x, y, r + 3, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.7 * alpha); ctx.fill()
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(*dot, alpha); ctx.fill()
    if side > 0:
        text(ctx, name, x + r + 12, y, size, IVORY, alpha, "lm", bold=bold, halo=size * 0.3, halo_a=0.9)
    elif side < 0:
        text(ctx, name, x - r - 12, y, size, IVORY, alpha, "rm", bold=bold, halo=size * 0.3, halo_a=0.9)
    else:
        text(ctx, name, x, y - r - 26, size, IVORY, alpha, "mm", bold=bold, halo=size * 0.3, halo_a=0.9)


if __name__ == "__main__":
    for n in ("nation", "region", "owari"):
        s = build_base(n); print(n, s.get_width(), s.get_height())
