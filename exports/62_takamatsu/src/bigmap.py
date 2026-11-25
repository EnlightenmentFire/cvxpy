# -*- coding: utf-8 -*-
"""日本西部大图（Natural Earth 10m 海岸线，经 world-atlas 2.0.2；公有领域）。地名位置为近似，示意。"""
import os, json, math
import numpy as np
import cairo
from gfx import *

HERE = os.path.dirname(os.path.abspath(__file__))
POLYS = json.load(open(os.path.join(HERE, "assets", "japan_west.json")))
COSL = math.cos(math.radians(34.8))

PLACES = {
    "京都": (135.77, 35.01), "安土": (136.14, 35.15), "姬路": (134.69, 34.83), "冈山": (133.92, 34.66),
    "备中高松": (133.82, 34.69), "猿挂城": (133.62, 34.63), "吉田郡山": (132.71, 34.67), "鸟取": (134.23, 35.50),
    "三木": (135.00, 34.80), "来岛": (132.98, 34.12), "盐饱": (133.75, 34.36),
}
PROV = {"备中": (133.62, 34.86), "备后": (133.15, 34.72), "美作": (134.02, 35.08), "伯耆": (133.55, 35.36),
        "出云": (132.85, 35.32)}
# 毛利势力范围（示意多边形，粗略）与织田—宇喜多一方
MORI = [(130.75, 34.2), (131.0, 34.7), (132.0, 35.3), (133.0, 35.7), (133.95, 35.7), (133.95, 35.05), (133.85, 34.85),
        (133.95, 34.50), (133.4, 34.40), (132.8, 34.25), (132.2, 34.12), (131.5, 33.88), (130.75, 33.85)]
ODA = [(133.95, 35.7), (134.6, 35.8), (136.0, 36.0), (137.6, 36.5), (137.6, 34.0), (136.5, 33.6), (135.6, 33.9), (135.3, 34.3),
       (135.0, 34.62), (134.5, 34.62), (133.95, 34.50), (133.85, 34.85), (133.95, 35.05)]


class BCam:
    def __init__(self, lon, lat, ppd, cy=900):
        self.lon, self.lat, self.ppd, self.cy = lon, lat, ppd, cy

    def __call__(self, lon, lat):
        return W / 2 + (lon - self.lon) * self.ppd * COSL, self.cy - (lat - self.lat) * self.ppd


def lerp_cam(a, b, k):
    k = ease(k)
    # interpolate zoom in log space
    ppd = math.exp(lerp(math.log(a.ppd), math.log(b.ppd), k))
    return BCam(lerp(a.lon, b.lon, k), lerp(a.lat, b.lat, k), ppd, lerp(a.cy, b.cy, k))


_sea = {}


def sea_surface():
    if "s" not in _sea:
        rng = np.random.default_rng(11)
        n = noise2d(H, W, 60, rng, 4)
        yy = np.linspace(0, 1, H)[:, None]
        base = np.stack([0.055 + 0.02 * n, 0.075 + 0.025 * n, 0.10 + 0.035 * n], -1) * (0.9 + 0.2 * yy[..., None])
        _sea["s"] = surface_from_rgb(base)
        land = noise2d(H, W, 30, rng, 4)
        lc = np.stack([0.20 + 0.06 * land, 0.19 + 0.05 * land, 0.15 + 0.04 * land], -1)
        _sea["l"] = surface_from_rgb(lc)
    return _sea["s"], _sea["l"]


def land_path(ctx, cam):
    for poly in POLYS:
        pts = [cam(x, y) for x, y in poly]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < -50 or min(xs) > W + 50 or max(ys) < -50 or min(ys) > H + 50:
            continue
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.close_path()


def draw_map(ctx, cam, mori=0.0, oda=0.0, dim=0.0):
    sea, land = sea_surface()
    ctx.set_source_surface(sea, 0, 0); ctx.paint()
    # coast glow
    land_path(ctx, cam)
    ctx.set_source_rgba(0.55, 0.62, 0.70, 0.10); ctx.set_line_width(14); ctx.stroke()
    land_path(ctx, cam)
    ctx.save(); ctx.clip()
    ctx.set_source_surface(land, 0, 0); ctx.paint()
    for poly, col, a in ((MORI, BLUE, mori), (ODA, RED, oda)):
        if a > 0:
            pts = [cam(x, y) for x, y in poly]
            path(ctx, pts); ctx.close_path(); ctx.set_source_rgba(*col, 0.30 * a); ctx.fill()
    ctx.restore()
    land_path(ctx, cam)
    ctx.set_source_rgba(0.80, 0.74, 0.60, 0.75); ctx.set_line_width(2.2); ctx.stroke()
    if dim > 0:
        ctx.set_source_rgba(0, 0, 0, dim); ctx.paint()


def place(ctx, cam, name, alpha=1.0, size=32, color=IVORY, dot=GOLD, anchor="lm", dx=18, dy=0, bold=False, castle=False):
    x, y = cam(*PLACES[name]) if name in PLACES else cam(*PROV[name])
    if alpha <= 0:
        return x, y
    if castle:
        ctx.rectangle(x - 9, y - 9, 18, 18); ctx.set_source_rgba(0, 0, 0, 0.6 * alpha); ctx.fill()
        ctx.rectangle(x - 6, y - 6, 12, 12); ctx.set_source_rgba(*dot, alpha); ctx.fill()
    elif dot:
        ctx.arc(x, y, 10, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.6 * alpha); ctx.fill()
        ctx.arc(x, y, 7, 0, 2 * math.pi); ctx.set_source_rgba(*dot, alpha); ctx.fill()
    if anchor[0] == "l":
        tx = x + dx
    elif anchor[0] == "r":
        tx = x - dx
    else:
        tx = x
    text(ctx, name, tx, y + dy, size, color, alpha, anchor, bold=bold, halo=size * 0.28, halo_a=0.85)
    return x, y
