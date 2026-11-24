# -*- coding: utf-8 -*-
"""Per-scene animation: each scene maps a context (local time + cue times) to
(cache_key, builder) for the illustration, plus a camera (zoom, focus) and optional overlays."""
import math, json, os
import numpy as np
from PIL import Image, ImageDraw
from art import (W, H, paper, Ink, INK, INK_SOFT, RED, hexc, wash, hatch, mask_from_poly, person, dog, horse, limb,
                 noise2d, cnoise, blur, font, FONT_CJK, FONT_CJK_B, FONT_CJK_SB, FONT_FR_I, FONT_FR, draw_text_rgba, over,
                 balance_cjk)
from layout import PX0, PY0, PX1, PY1
import scenes as S
from scenes import ease, crown, scallop_outline, engr_tree, speech_bubble, red_ellipse, lighten, NIGHT

HERE = os.path.dirname(os.path.abspath(__file__))
PCX, PCY = (PX0 + PX1) / 2, (PY0 + PY1) / 2

SCENE_TONE = {"s00": "sea", "s01": "france", "s02": "america", "s03": "america", "s04": "america", "s05": "forest",
              "s06": "america", "s07": "oldfrance", "s08": "gray", "s09": "ice", "s10": "dawn"}

from collections import OrderedDict
_STATIC = OrderedDict()
_STATIC_MAX = 48


def static(key, fn):
    """memoize full-frame canvases as uint8 (memory) and hand back float32 copies"""
    if key in _STATIC:
        _STATIC.move_to_end(key)
    else:
        v = fn()
        _STATIC[key] = (np.clip(v, 0, 1) * 255 + 0.5).astype(np.uint8) if isinstance(v, np.ndarray) else v
        if len(_STATIC) > _STATIC_MAX:
            _STATIC.popitem(last=False)
    v = _STATIC[key]
    return v.astype(np.float32) / 255 if isinstance(v, np.ndarray) else v


def q(x, n=40):
    """quantize a 0..1 parameter for caching"""
    return round(float(x) * n) / n


def blend(a, b, x):
    return a * (1 - x) + b * x


def text_items(items):
    return draw_text_rgba((W, H), items)


def label(ill, x, y, txt, size=30, color=(46, 33, 24, 255), anchor="mm", bold=False, op=1.0):
    f = font(FONT_CJK_SB if bold else FONT_CJK, size)
    over(ill, text_items([(x, y, txt, f, color, anchor)]), op)


def big_text(ill, lines, y0, size=64, color=(40, 28, 20, 255), lh=1.45, op=1.0, halo="#ece3cb"):
    f = font(FONT_CJK_B, size)
    items = [(W / 2, y0 + i * size * lh, ln, f, color, "mm") for i, ln in enumerate(lines)]
    rgba = text_items(items)
    if halo:
        a = rgba[..., 3]
        hm = blur(a, 12) * 0.65 * op
        ill[:] = ill * (1 - hm[..., None]) + hexc(halo) * hm[..., None]
    over(ill, rgba, op)


def plate_fill(tone, color, op, seed=1):
    ill = paper(tone, 30 + seed)
    m = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]])
    wash(ill, m, hexc(color), op, seed=seed, gran=0.3, edge=0.05, bleed=10)
    return ill


def medallion(ill, cx, cy, rx, ry, draw_fn, caption=None, tone_col="#d9cdb0"):
    """oval portrait frame with a silhouette drawn by draw_fn(ink)"""
    m = np.zeros((H, W), np.float32)
    yy, xx = np.ogrid[:H, :W]
    m[((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1] = 1
    m = blur(m, 1.2)
    ill[:] = ill * (1 - m[..., None] * 0.85) + hexc(tone_col) * m[..., None] * 0.85
    ink = Ink()
    draw_fn(ink)
    a = ink.alpha() * m
    ill[:] = ill * (1 - a[..., None]) + INK * a[..., None]
    fr = Ink()
    fr.ellipse(cx, cy, rx, ry, None, 255, 4)
    fr.ellipse(cx, cy, rx + 14, ry + 14, None, 255, 1.6)
    fr.apply(ill, INK, 0.9)
    if caption:
        label(ill, cx, cy + ry + 52, caption, 32)


def profile_head(ink, cx, cy, s, queue=False, hat=False):
    """large profile bust silhouette facing right; (cx,cy) head centre; s = head radius"""
    ink.ellipse(cx, cy, s * 0.95, s * 1.1)
    ink.poly([(cx + s * 0.75, cy - s * 0.3), (cx + s * 1.22, cy + s * 0.25), (cx + s * 0.8, cy + s * 0.45)])
    ink.ellipse(cx + s * 0.55, cy + s * 0.78, s * 0.42, s * 0.35)
    ink.poly([(cx - s * 0.5, cy + s * 0.6), (cx + s * 0.45, cy + s * 0.9), (cx + s * 0.5, cy + s * 1.7), (cx - s * 0.7, cy + s * 1.7)])
    ink.poly([(cx - s * 2.2, cy + s * 3.4), (cx - s * 1.6, cy + s * 1.9), (cx - s * 0.6, cy + s * 1.5), (cx + s * 0.6, cy + s * 1.55),
              (cx + s * 1.5, cy + s * 1.95), (cx + s * 2.1, cy + s * 3.4)])
    ink.poly([(cx - s * 0.95, cy - s * 0.2), (cx - s * 0.6, cy - s * 1.15), (cx + s * 0.3, cy - s * 1.25), (cx + s * 0.85, cy - s * 0.75),
              (cx + s * 0.2, cy - s * 0.75), (cx - s * 0.5, cy - s * 0.3), (cx - s * 0.75, cy + s * 0.55)])
    if queue:
        ink.poly([(cx - s * 0.95, cy + s * 0.1), (cx - s * 1.35, cy + s * 0.65), (cx - s * 1.2, cy + s * 0.8), (cx - s * 0.8, cy + s * 0.45)])
        ink.ellipse(cx - s * 1.0, cy + s * 0.25, s * 0.18, s * 0.12, 0)
    if hat:
        ink.poly([(cx - s * 1.5, cy - s * 0.85), (cx + s * 1.5, cy - s * 0.85), (cx + s * 1.45, cy - s * 1.05), (cx - s * 1.45, cy - s * 1.05)])
        ink.poly([(cx - s * 0.95, cy - s * 1.0), (cx + s * 0.95, cy - s * 1.0), (cx + s * 1.05, cy - s * 2.6), (cx - s * 1.05, cy - s * 2.6)])


# ====================================================================== map

_GEO = None
LON0, LON1, LAT0, LAT1 = -97.0, -63.0, 24.0, 50.0


def geo():
    global _GEO
    if _GEO is None:
        _GEO = json.load(open(os.path.join(HERE, "assets", "geo_east_na.json")))
    return _GEO


def proj(lon, lat):
    k = min((PX1 - PX0 - 30) / ((LON1 - LON0) * math.cos(math.radians(37))), (PY1 - PY0 - 30) / (LAT1 - LAT0))
    x = PX0 + 15 + (lon - LON0) * math.cos(math.radians(37)) * k
    y = PY0 + 15 + (LAT1 - lat) * k
    return x, y


CITIES = {  # name: (lon, lat, label or None)
    "newport": (-71.31, 41.49, "纽波特"), "ny": (-74.0, 40.71, "纽约"), "singsing": (-73.86, 41.16, None),
    "albany": (-73.75, 42.65, None), "auburn": (-76.57, 42.93, None), "buffalo": (-78.88, 42.89, None),
    "detroit": (-83.05, 42.33, None), "saginaw": (-83.95, 43.42, "密歇根荒野"), "mackinac": (-84.6, 45.85, None),
    "greenbay": (-88.0, 44.5, None), "montreal": (-73.57, 45.5, None), "quebec": (-71.21, 46.81, "魁北克"),
    "boston": (-71.06, 42.36, "波士顿"), "hartford": (-72.67, 41.76, None), "phila": (-75.17, 39.95, "费城"),
    "baltimore": (-76.61, 39.29, None), "pittsburgh": (-80.0, 40.44, None), "cincinnati": (-84.51, 39.1, None),
    "louisville": (-85.76, 38.25, None), "nashville": (-86.78, 36.16, None), "memphis": (-90.05, 35.15, "孟菲斯"),
    "neworleans": (-90.07, 29.95, "新奥尔良"), "mobile": (-88.04, 30.69, None), "montgomery": (-86.3, 32.38, None),
    "norfolk": (-76.29, 36.85, None), "washington": (-77.04, 38.9, "华盛顿"),
}
ROUTE = ["newport", "ny", "singsing", "albany", "auburn", "buffalo", "detroit", "saginaw", "detroit", "mackinac", "greenbay",
         "mackinac", "detroit", "buffalo", "montreal", "quebec", "montreal", "boston", "hartford", "ny", "phila", "baltimore",
         "phila", "pittsburgh", "cincinnati", "louisville", "nashville", "memphis", "neworleans", "mobile", "montgomery",
         "norfolk", "washington", "ny"]


def map_static():
    ill = paper("sea", 61)
    g = geo()
    sea = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]])
    wash(ill, sea, hexc("#8fa7aa"), 0.42, seed=2, gran=0.3, edge=0.05, bleed=6)
    land = [[proj(x, y) for x, y in poly] for poly in g["land"]]
    lm = mask_from_poly(land)
    # land back to paper colour, then a warm wash
    pap = paper("america", 62)
    ill[:] = ill * (1 - lm[..., None]) + pap * lm[..., None]
    wash(ill, lm, hexc("#cdb88a"), 0.35, seed=3, gran=0.35, edge=0.25, bleed=1.5)
    lakes = [[proj(x, y) for x, y in poly] for poly in g["lakes"]]
    lk = mask_from_poly(lakes)
    wash(ill, lk, hexc("#7f9aa0"), 0.55, seed=4, gran=0.2, edge=0.3, bleed=0.8)
    ink = Ink()
    for p in land:
        if len(p) > 2:
            ink.line(p, 1.3, closed=True)
    for p in lakes:
        if len(p) > 2:
            ink.line(p, 1.0, closed=True)
    # coastal ripple lines (sea side)
    rng = np.random.default_rng(5)
    ripple = Ink()
    for k, off in enumerate((7, 14, 22)):
        for p in land:
            if len(p) > 40:
                pts = [(x + off * 0.0, y) for x, y in p[::3]]
        # approximate: dilate land mask instead
    dil = [blur(lm, r) for r in (6, 12, 20)]
    for r, dm in zip((6, 12, 20), dil):
        band = ((dm > 0.08) & (dm < 0.2) & (lm < 0.1)).astype(np.float32)
        a = band * (0.45 - r * 0.012)
        ill[:] = ill * (1 - a[..., None]) + INK * a[..., None]
    rv = Ink()
    for r in g["rivers"]:
        pts = [proj(x, y) for x, y in r["pts"]]
        rv.line(pts, 1.6 if r["name"] in ("Mississippi", "Ohio") else 1.0)
    ink.apply(ill, INK, 0.85)
    rv.apply(ill, hexc("#3f5b66"), 0.85)
    # cartouche + compass
    f = font(FONT_CJK_SB, 34)
    over(ill, text_items([(PX1 - 170, PY1 - 120, "1831—1832", font(FONT_FR_I, 36), (70, 48, 32, 255), "mm"),
                          (PX1 - 170, PY1 - 78, "九个多月的路线", f, (70, 48, 32, 255), "mm"),
                          (proj(-95, 31)[0], proj(-95, 31)[1], "美 国", font(FONT_CJK_SB, 40), (90, 70, 50, 200), "mm"),
                          (proj(-74.5, 33)[0], proj(-74.5, 33)[1], "大 西 洋", font(FONT_CJK, 34), (60, 80, 85, 200), "mm")]))
    c = Ink()
    cx, cy = PX0 + 110, PY1 - 140
    for a in range(8):
        ang = a * math.pi / 4
        L = 60 if a % 2 == 0 else 32
        c.poly([(cx, cy), (cx + L * math.cos(ang - 0.18) * 0.35, cy + L * math.sin(ang - 0.18) * 0.35), (cx + L * math.cos(ang), cy + L * math.sin(ang))])
    c.ellipse(cx, cy, 70, 70, None, 255, 1.2)
    c.apply(ill, INK, 0.75)
    over(ill, text_items([(cx, cy - 86, "N", font(FONT_FR, 28), (46, 33, 24, 255), "mm")]))
    return ill


def route_points():
    pts = [proj(*CITIES[c][:2]) for c in ROUTE]
    # densify
    out, cum = [pts[0]], [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 6))
        for i in range(1, n + 1):
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            cum.append(cum[-1] + math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]))
            out.append(p)
    return out, cum


def draw_map(prog=1.0, dim=0.0):
    ill = static("map", map_static).copy()
    pts, cum = route_points()
    L = cum[-1] * prog
    r = Ink()
    seg = []
    for i in range(1, len(pts)):
        if cum[i] > L:
            break
        if int(cum[i] / 10) % 2 == 0:
            r.line([pts[i - 1], pts[i]], 3.2)
    r.apply(ill, RED, 0.9, grain=0.06)
    dots = Ink()
    items = []
    seen = set()
    for i, c in enumerate(ROUTE):
        x, y = proj(*CITIES[c][:2])
        idx = min(range(len(pts)), key=lambda j: (pts[j][0] - x) ** 2 + (pts[j][1] - y) ** 2)
        if cum[idx] <= L + 1 and c not in seen:
            seen.add(c)
            dots.ellipse(x, y, 6, 6)
            lab = CITIES[c][2]
            if lab:
                dx = -14 if c in ("newport", "boston", "quebec", "ny", "phila", "washington") else 14
                anc = "rm" if dx > 0 and False else ("lm" if dx > 0 else "rm")
                if c in ("newport", "boston", "quebec"):
                    anc, dx = "lm", 14
                items.append((x + dx, y - 2, lab, font(FONT_CJK_SB, 30), (46, 33, 24, 255), anc))
    dots.apply(ill, INK, 0.95, grain=0.05)
    if items:
        rgba = text_items(items)
        hm = blur(rgba[..., 3], 5) * 0.7
        ill[:] = ill * (1 - hm[..., None]) + hexc("#eadfc3") * hm[..., None]
        over(ill, rgba)
    if dim:
        ill[:] = ill * (1 - dim) + hexc("#e8dfc8") * dim
    return ill


# ====================================================================== s00 opening

def sea_static():
    return S.draw_sea(t=0.0, ship_x=-5.0)  # ship drawn off-plate -> static sea


_SHIP = None


def ship_overlay():
    """ship as an affine layer (k, d) captured once, then translated per frame"""
    global _SHIP
    if _SHIP is None:
        def drawer(cv):
            rng = np.random.default_rng(0)
            ink = Ink()
            sail = S.ship(ink, cv, 400, 1025, 400, rng)
            ink.apply(cv, INK, 0.92)
            sail.apply(cv, INK, 0.75)
        z = np.zeros((H, W, 3), np.float32); o = np.ones((H, W, 3), np.float32)
        drawer(z); drawer(o)
        k, d = o - z, z
        y0, y1, x0, x1 = 600, 1100, 150, 760
        _SHIP = (k[y0:y1, x0:x1].copy(), d[y0:y1, x0:x1].copy(), (y0, x0))
    return _SHIP


def put_ship(ill, dx, dy):
    k, d, (y0, x0) = ship_overlay()
    h, w = k.shape[:2]
    yy, xx = int(y0 + dy), int(x0 + dx)
    ya, yb = max(PY0, yy), min(PY1, yy + h)
    xa, xb = max(PX0, xx), min(PX1, xx + w)
    if ya >= yb or xa >= xb:
        return ill
    ks, ds = k[ya - yy:yb - yy, xa - xx:xb - xx], d[ya - yy:yb - yy, xa - xx:xb - xx]
    ill[ya:yb, xa:xb] = ill[ya:yb, xa:xb] * ks + ds
    return ill


def s00(c):
    cur, prev, x = c.phase([(None, "sea"), ("map_route", "map"), ("s00_07", "road")])

    def draw_phase(name):
        if name == "sea":
            ill = static("sea", sea_static).copy()
            pr = min(1.0, c.tq / max(1.0, (c.at("title_card") or 20)))
            dx = -330 + 330 * ease(pr) + 6 * math.sin(c.tq * 0.6)
            dy = 4 * math.sin(c.tq * 1.3)
            put_ship(ill, dx, dy)
            to = c.p("title_card", 1.2)
            if to > 0:
                S.title_overlay(ill, to)
            return ill
        if name == "map":
            a, b = c.at("map_route"), c.at("s00_07") or (c.at("map_route") + 10)
            return draw_map(min(1.0, max(0.0, (c.tq - a) / max(1.0, (b - a) * 0.9))))
        if name == "road":
            return static("road_bare", lambda: S.road_dynamic(S.road_static(office=False), fallen=0.0, gather=0.0, circled=0.0, bubble=0.0, cleared=1.0)).copy()

    if cur == "sea":
        key = ("sea", round(c.tq, 2), q(c.p("title_card", 1.2), 20))
    elif cur == "map":
        key = ("map", round(c.tq, 1), prev, q(x, 15))
    else:
        key = ("road", prev, q(x, 15))

    def fn():
        a = draw_phase(cur)
        if prev and x < 1:
            return blend(draw_phase(prev), a, x)
        return a
    return key, fn


def cam_s00(c):
    cur, prev, x = c.phase([(None, "sea"), ("map_route", "map"), ("s00_07", "road")])
    if cur == "road":
        z = 1.0 + 0.12 * c.p("s00_07", 6.0, smooth=True)
        return z, 520, 980
    return 1.0 + 0.03 * min(1, c.t / 30), PCX, PCY


# ====================================================================== s01 who he was

def prison_door():
    ill = plate_fill("france", "#7d8894", 0.35, 2)
    ink = Ink()
    # stone wall
    rng = np.random.default_rng(3)
    for row in range(16):
        y = PY0 + row * 60
        off = 0 if row % 2 else 55
        ink.line([(PX0, y), (PX1, y)], 1.2)
        for k in range(-1, 10):
            x = PX0 + off + k * 110
            ink.line([(x, y), (x, y + 60)], 1.2)
    hatch(ink, [[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]], 30, 9, 0.7, rng)
    door = [(330, 470), (750, 470), (750, 1200), (330, 1200)]
    dm = mask_from_poly([door, [(330, 470), (540, 360), (750, 470)]])
    pap = paper("forest", 63)
    ill[:] = ill * (1 - dm[..., None]) + pap * dm[..., None]
    wash(ill, dm, S.WOOD, 0.75, seed=5, gran=0.5, edge=0.4, bleed=1)
    d2 = Ink()
    d2.line(door + [door[0]], 4)
    d2.arc(540, 470, 210, 110, 180, 360, 4)
    for k in range(1, 6):
        d2.line([(330 + 70 * k, 420 - (25 if 1 < k < 5 else 0)), (330 + 70 * k, 1200)], 1.4)
    for yb in (560, 860, 1120):
        d2.poly([(325, yb), (755, yb), (755, yb + 26), (325, yb + 26)])
        for k in range(8):
            d2.ellipse(350 + k * 55, yb + 13, 6, 6, 0)
    # barred window
    d2.poly([(470, 640), (610, 640), (610, 760), (470, 760)], 255)
    for k in range(1, 5):
        d2.line([(470 + 28 * k, 640), (470 + 28 * k, 760)], 4, 0)
    d2.ellipse(690, 860, 18, 18)
    d2.poly([(684, 860), (696, 860), (694, 900), (686, 900)])
    ink.apply(ill, INK, 0.6)
    d2.apply(ill, NIGHT, 0.95, grain=0.08)
    # tally marks
    t = Ink()
    for g in range(3):
        for k in range(5):
            x = 800 + g * 70 + k * 11
            if k < 4:
                t.line([(x, 1000), (x + 3, 1060)], 2.2)
        t.line([(800 + g * 70 - 6, 1050), (800 + g * 70 + 46, 1008)], 2.2)
    t.apply(ill, hexc("#efeee8"), 0.8)
    label(ill, 860, 960, "1793", 38, (240, 238, 230, 230))
    return ill


def guillotine():
    ill = plate_fill("france", "#6c7783", 0.45, 3)
    ink = Ink()
    rng = np.random.default_rng(4)
    # dusk sky hatch
    hatch(ink, [[(PX0, PY0), (PX1, PY0), (PX1, 780), (PX0, 780)]], 0, 8, 0.8, rng)
    # square: distant buildings
    for k in range(9):
        x = PX0 + k * 110
        h_ = 140 + 40 * (k % 3)
        ink.poly([(x, 900), (x + 104, 900), (x + 104, 900 - h_), (x, 900 - h_)], 140)
        for w_ in range(3):
            ink.poly([(x + 18 + w_ * 28, 900 - h_ + 30), (x + 30 + w_ * 28, 900 - h_ + 30), (x + 30 + w_ * 28, 900 - h_ + 55), (x + 18 + w_ * 28, 900 - h_ + 55)], 0)
    sil = Ink()
    # scaffold + frame, far and small, no blade detail
    sil.poly([(450, 900), (630, 900), (630, 870), (450, 870)])
    sil.poly([(520, 870), (532, 870), (532, 700), (520, 700)])
    sil.poly([(548, 870), (560, 870), (560, 700), (548, 700)])
    sil.poly([(512, 700), (568, 700), (568, 688), (512, 688)])
    for k in range(40):
        x = PX0 + 30 + k * 23 + rng.uniform(-6, 6)
        person(sil, x, 1000 + rng.uniform(0, 30), rng.uniform(40, 55), "stand", 1 if k % 2 else -1, ["top", "cap", "bonnet", None][k % 4], k % 4 == 2)
    ink.apply(ill, INK, 0.5)
    sil.apply(ill, NIGHT, 0.9, grain=0.05)
    label(ill, PCX, 1150, "1794 年春 · 巴黎", 34, (36, 40, 48, 255))
    return ill


def father():
    ill = plate_fill("france", "#8a94a0", 0.25, 4)
    medallion(ill, PCX, 740, 250, 320, lambda ink: profile_head(ink, PCX - 10, 690, 95, queue=True), "他的父亲 · 1794 年 · 二十二岁")
    return ill


def alexis():
    ill = plate_fill("france", "#8a94a0", 0.2, 5)
    medallion(ill, PCX, 740, 250, 320, lambda ink: profile_head(ink, PCX - 10, 690, 95), "托克维尔 · 1805 年生")
    return ill


def two_judges():
    ill = plate_fill("sea", "#9fb0b0", 0.3, 6)
    ink = Ink()
    rng = np.random.default_rng(7)
    # quay and ship masts behind
    ink.line([(PX0, 1080), (PX1, 1080)], 2.4)
    hatch(ink, [[(PX0, 1080), (PX1, 1080), (PX1, PY1), (PX0, PY1)]], 10, 7, 0.9, rng)
    for mx in (640, 760, 880):
        ink.line([(mx, 1080), (mx, 560)], 3)
        for k in range(3):
            ink.line([(mx - 60 + k * 8, 640 + k * 120), (mx + 60 - k * 8, 640 + k * 120)], 2)
    ink.poly([(560, 1080), (1000, 1080), (970, 1000), (590, 1000)], 255)
    sil = Ink()
    person(sil, 300, 1078, 330, "stand", 1, "top")
    person(sil, 430, 1078, 345, "point", 1, "top")
    sil.poly([(160, 1078), (260, 1078), (260, 1010), (160, 1010)])  # trunk
    ink.apply(ill, INK, 0.8)
    sil.apply(ill, INK, 0.97, grain=0.05)
    # the commission letter
    lx, ly = 690, 520
    lm = mask_from_poly([[(lx - 150, ly - 110), (lx + 150, ly - 110), (lx + 150, ly + 110), (lx - 150, ly + 110)]])
    ill[:] = ill * (1 - lm[..., None] * 0.95) + hexc("#f4ecd6") * lm[..., None] * 0.95
    li = Ink()
    li.line([(lx - 150, ly - 110), (lx + 150, ly - 110), (lx + 150, ly + 110), (lx - 150, ly + 110), (lx - 150, ly - 110)], 1.6)
    for k in range(5):
        li.line([(lx - 120, ly - 20 + k * 24), (lx + 120 - (60 if k == 4 else 0), ly - 20 + k * 24)], 1.0, val=140)
    li.apply(ill, INK, 0.85)
    label(ill, lx, ly - 62, "公 函", 38, bold=True)
    r = Ink(); r.ellipse(lx + 105, ly + 75, 24, 24); r.apply(ill, RED, 0.9)
    label(ill, lx, ly + 150, "差事：考察美国的新式监狱", 30)
    return ill


def prison_plan(walk=0.0):
    ill = plate_fill("france", "#9aa4ad", 0.2, 7)
    ink = Ink()
    cx, cy = PCX, 760
    ink.line([(cx + 300 * math.cos(a), cy + 300 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)], 2.0)  # outer wall approx
    ang0 = [math.radians(a) for a in (-90, -38, 14, 66, 118, 170, 222)]
    for a in ang0:
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        L = 290
        pts = [(cx + ux * 40 + nx * 22, cy + uy * 40 + ny * 22), (cx + ux * L + nx * 22, cy + uy * L + ny * 22),
               (cx + ux * L - nx * 22, cy + uy * L - ny * 22), (cx + ux * 40 - nx * 22, cy + uy * 40 - ny * 22)]
        ink.line(pts + [pts[0]], 2.2)
        for k in range(14):
            s_ = 50 + k * 17
            for sgn in (1, -1):
                ink.line([(cx + ux * s_ + nx * 22 * sgn, cy + uy * s_ + ny * 22 * sgn), (cx + ux * s_ + nx * 38 * sgn, cy + uy * s_ + ny * 38 * sgn)], 1.0)
        ink.line([(cx + ux * 40 + nx * 38, cy + uy * 40 + ny * 38), (cx + ux * L + nx * 38, cy + uy * L + ny * 38)], 1.0)
        ink.line([(cx + ux * 40 - nx * 38, cy + uy * 40 - ny * 38), (cx + ux * L - nx * 38, cy + uy * L - ny * 38)], 1.0)
    ink.ellipse(cx, cy, 42, 42, None, 255, 2.4)
    ink.apply(ill, INK, 0.85)
    # two visitors walking down one corridor, pausing at cell doors
    a = ang0[2]
    s_ = 60 + 210 * walk
    v = Ink()
    for j in (0, 1):
        sx = cx + math.cos(a) * (s_ - 18 * j)
        sy = cy + math.sin(a) * (s_ - 18 * j)
        v.ellipse(sx, sy, 7, 7)
    v.apply(ill, RED, 0.95)
    label(ill, PCX, 1135, "费城东州监狱（平面示意）", 30)
    return ill


def question_map():
    ill = draw_map(1.0, dim=0.35)
    return ill


S01_ORDER = [(None, "door"), ("guillotine_shadow", "guillo"), ("s01_03", "father"), ("s01_04", "alexis"),
             ("two_judges", "judges"), ("prison_corridor", "plan"), ("s01_10", "map")]


def s01(c):
    cur, prev, x = c.phase(S01_ORDER)
    walk = c.p("prison_corridor", 9.0, smooth=False)
    builders = {"door": prison_door, "guillo": guillotine, "father": father, "alexis": alexis, "judges": two_judges,
                "plan": lambda: prison_plan(0.0), "map": question_map}

    def get(name):
        if name == "plan":
            return prison_plan(walk)
        return static(("s01", name), builders[name]).copy()
    key = (cur, prev, q(x, 15), q(walk, 30) if cur == "plan" or prev == "plan" else 0)

    def fn():
        a = get(cur)
        return blend(get(prev), a, x) if prev and x < 1 else a
    return key, fn


def cam_s01(c):
    cur, prev, x = c.phase(S01_ORDER)
    if cur == "door":
        return 1.0 + 0.08 * min(1, c.t / 8), PCX, 700
    if cur in ("father", "alexis"):
        return 1.0 + 0.05 * c.p("s01_03" if cur == "father" else "s01_04", 8), PCX, 740
    return 1.0 + 0.03 * min(1, c.t / 60), PCX, PCY


def ov_s01(c, fr, overlay):
    a = c.at("s01_11")
    if a is not None and c.t >= a - 0.2:
        op = c.p("s01_11", 0.8)
        ov = overlay(("s01q",), lambda cv: big_text(cv, ["一个没有国王、没有贵族的国家，", "凭什么不乱？"], 690, 52))
        ov.apply(fr, op)


# ====================================================================== s02 the blocked road

def playground():
    ill = paper("america", 71)
    sky = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 760), (PX0, 760)]])
    wash(ill, sky, hexc("#c3cdc6"), 0.35, seed=3, gran=0.2, edge=0.1, bleed=10)
    gm = mask_from_poly([[(PX0, 760), (PX1, 760), (PX1, PY1), (PX0, PY1)]])
    wash(ill, gm, hexc("#a9ae72"), 0.45, seed=4, gran=0.45, edge=0.1, bleed=4)
    ink = Ink()
    rng = np.random.default_rng(8)
    # one-room schoolhouse
    sx, sy = 640, 760
    hm = mask_from_poly([[(sx, sy), (sx + 300, sy), (sx + 300, sy - 170), (sx, sy - 170)]])
    wash(ill, hm, hexc("#b0563c"), 0.55, seed=6, gran=0.3, edge=0.3, bleed=0.6)
    ink.line([(sx, sy), (sx + 300, sy), (sx + 300, sy - 170), (sx, sy - 170), (sx, sy)], 2)
    roof = [(sx - 20, sy - 168), (sx + 150, sy - 270), (sx + 320, sy - 168)]
    ink.line(roof + [roof[0]], 2)
    hatch(ink, [roof], 20, 5, 0.9, rng)
    ink.poly([(sx + 135, sy - 290), (sx + 165, sy - 290), (sx + 165, sy - 250), (sx + 135, sy - 250)], 255)
    ink.line([(sx + 150, sy - 290), (sx + 150, sy - 320)], 2)
    for wx in (sx + 30, sx + 210):
        ink.line([(wx, sy - 120), (wx + 55, sy - 120), (wx + 55, sy - 50), (wx, sy - 50), (wx, sy - 120)], 1.5)
    ink.poly([(sx + 125, sy), (sx + 175, sy), (sx + 175, sy - 90), (sx + 125, sy - 90)], 255)
    for i in range(6):
        engr_tree(ill, ink, PX0 + 40 + i * 95, 760, 140 + 20 * (i % 2), rng, color=S.GREEN_D, seed=50 + i, wash_op=0.4)
    S.grass(ink, rng, 800, PY1 - 5, 200)
    # slate with rules
    bx, by = 140, 860
    bm = mask_from_poly([[(bx, by), (bx + 260, by), (bx + 260, by + 170), (bx, by + 170)]])
    ill[:] = ill * (1 - bm[..., None] * 0.9) + hexc("#2f3a2f") * bm[..., None] * 0.9
    ink.line([(bx + 130, by + 170), (bx + 130, by + 240)], 4)
    ink.apply(ill, INK, 0.9)
    over(ill, text_items([(bx + 130, by + 30, "我们的规矩", font(FONT_CJK_SB, 30), (235, 230, 215, 255), "mm"),
                          (bx + 22, by + 78, "一、轮流当头", font(FONT_CJK, 25), (225, 222, 210, 255), "lm"),
                          (bx + 22, by + 114, "二、不许耍赖", font(FONT_CJK, 25), (225, 222, 210, 255), "lm"),
                          (bx + 22, by + 150, "三、犯规的罚站", font(FONT_CJK, 25), (225, 222, 210, 255), "lm")]))
    return ill


def playground_kids(ill, t):
    sil = Ink()
    cx, cy, R = 600, 1060, 200
    for i in range(9):
        a = 2 * math.pi * i / 9 + t * 0.35
        x, y = cx + R * math.cos(a), cy + R * 0.35 * math.sin(a)
        person(sil, x, y + 60, 120 + 10 * math.sin(a), "walk", 1 if math.sin(a) > 0 else -1, None, i % 3 == 0, arm_t=t * 1.3 + i, child=True)
    # the one standing out for breaking a rule
    person(sil, 900, 1150, 118, "stand", -1, None, False, child=True)
    sil.apply(ill, INK, 0.96, grain=0.05)
    return ill


def s02(c):
    cur, prev, x = c.phase([(None, "road"), ("playground", "play")])
    fallen = c.p("tree_falls", 1.4, delay=3.2)
    gather = c.p("neighbors_gather", 3.2, smooth=False)
    circled = c.p("neighbors_gather", 1.2, delay=3.6)
    bubble = c.p("neighbors_gather", 0.5, delay=1.0)
    saw = c.p("saw_clear", 3.0, smooth=False)
    cleared = c.p("saw_clear", 1.0, delay=2.6)
    if c.past("saw_clear", 3.0):
        bubble = 0.0
        circled = max(0.0, 1 - c.p("saw_clear", 0.6, delay=3.0))
    carts = c.p("saw_clear", 4.0, delay=3.4)
    moving = (0.0 < gather < 1.0) or (0.0 < saw < 1.0) or (0.0 < fallen < 1.0) or (0.0 < carts < 1.0) or (c.past("saw_clear") and not c.past("saw_clear", 3.2))
    tt = round(c.tq, 2) if (moving or cur == "play" or prev == "play") else 0

    def road():
        st = static("road_static", lambda: S.road_static())
        return S.road_dynamic(st.copy(), t=tt, fallen=fallen, gather=gather, circled=circled, saw=saw, cleared=cleared,
                              bubble=bubble, carts_go=carts)

    def play():
        return playground_kids(static("playground", playground).copy(), c.tq)
    key = (cur, prev, q(x, 15), q(fallen), q(gather), q(circled), q(bubble, 10), q(saw), q(cleared, 10), q(carts), tt)

    def fn():
        a = road() if cur == "road" else play()
        if prev and x < 1:
            b = road() if prev == "road" else play()
            return blend(b, a, x)
        return a
    return key, fn


def cam_s02(c):
    if c.past("playground", -0.3):
        return 1.04, PCX, PCY
    if c.past("office_dark", -0.2):
        k = c.p("office_dark", 1.6)
        return 1.0 + 0.9 * k, PCX + (900 - PCX) * k, PCY + (425 - PCY) * k
    if c.past("neighbors_gather"):
        k = c.p("neighbors_gather", 3.0)
        return 1.0 + 0.18 * k, PCX + (760 - PCX) * k, PCY + (960 - PCY) * k
    return 1.0 + 0.04 * min(1, c.t / 10), PCX, PCY


# ====================================================================== s03 school of liberty

def meeting_house(ink, ill, x, base, s, rng):
    """white New England meeting house with steeple; (x, base) bottom-left"""
    w, h = s, s * 0.55
    body = [(x, base), (x + w, base), (x + w, base - h), (x, base - h)]
    m = mask_from_poly([body, [(x - 10, base - h), (x + w / 2, base - h - s * 0.28), (x + w + 10, base - h)]])
    pap = paper("dawn", 64)
    ill[:] = ill * (1 - m[..., None] * 0.9) + pap * m[..., None] * 0.9
    ink.line(body + [body[0]], 2)
    ink.line([(x - 10, base - h), (x + w / 2, base - h - s * 0.28), (x + w + 10, base - h)], 2)
    for k in range(1, 12):
        ink.line([(x, base - h + k * h / 12), (x + w, base - h + k * h / 12)], 0.7, val=130)
    tx = x + w / 2
    tw = s * 0.16
    ink.line([(tx - tw / 2, base - h - s * 0.2), (tx - tw / 2, base - h - s * 0.55), (tx + tw / 2, base - h - s * 0.55), (tx + tw / 2, base - h - s * 0.2)], 2)
    ink.line([(tx - tw / 2 - 6, base - h - s * 0.55), (tx, base - h - s * 0.85), (tx + tw / 2 + 6, base - h - s * 0.55)], 2)
    ink.arc(tx, base - h - s * 0.45, tw * 0.25, tw * 0.3, 180, 360, 1.6)
    for k in range(3):
        wx = x + w * (0.15 + 0.3 * k)
        ink.line([(wx, base - h * 0.75), (wx + w * 0.1, base - h * 0.75), (wx + w * 0.1, base - h * 0.25), (wx, base - h * 0.25), (wx, base - h * 0.75)], 1.4)
    ink.line([(tx - w * 0.06, base), (tx - w * 0.06, base - h * 0.4), (tx + w * 0.06, base - h * 0.4), (tx + w * 0.06, base)], 1.6)


def town_wide():
    ill = paper("america", 72)
    rng = np.random.default_rng(9)
    sky = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 820), (PX0, 820)]])
    wash(ill, sky, hexc("#c3cdc6"), 0.35, seed=3, gran=0.2, edge=0.1, bleed=10)
    gm = mask_from_poly([[(PX0, 820), (PX1, 820), (PX1, PY1), (PX0, PY1)]])
    wash(ill, gm, hexc("#a9ae72"), 0.48, seed=4, gran=0.45, edge=0.1, bleed=4)
    ink = Ink()
    S.clouds(ink, rng, [(420, 300, 170, 30), (500, 760, 150, 24)])
    hills = [(PX0, 820)] + [(PX0 + (PX1 - PX0) * i / 20, 760 - 30 * math.sin(i * 0.5) - 8 * rng.random()) for i in range(21)] + [(PX1, 820)]
    hatch(ink, [hills], -15, 6, 0.8, rng)
    meeting_house(ink, ill, 380, 860, 320, rng)
    for hx, hb, hs in [(130, 880, 150), (790, 875, 160), (930, 900, 110)]:
        m = mask_from_poly([[(hx, hb), (hx + hs, hb), (hx + hs, hb - hs * 0.55), (hx, hb - hs * 0.55)]])
        wash(ill, m, hexc("#e8e1cc"), 0.5, seed=7, gran=0.1, edge=0.1, bleed=0.5)
        ink.line([(hx, hb), (hx + hs, hb), (hx + hs, hb - hs * 0.55), (hx, hb - hs * 0.55), (hx, hb)], 1.5)
        roof = [(hx - 8, hb - hs * 0.55), (hx + hs / 2, hb - hs * 0.85), (hx + hs + 8, hb - hs * 0.55)]
        ink.line(roof + [roof[0]], 1.5)
        hatch(ink, [roof], 25, 4.5, 0.8, rng)
    for i, (tx, th) in enumerate([(300, 260), (740, 280), (90, 200), (990, 230)]):
        engr_tree(ill, ink, tx, 900 + (i % 2) * 20, th, rng, color=S.GREEN, seed=60 + i, wash_op=0.5)
    # the green with fence
    for i in range(20):
        x = PX0 + i * 50
        ink.line([(x, 1010), (x, 975)], 1.8)
    ink.line([(PX0, 985), (PX1, 985)], 1.4); ink.line([(PX0, 1000), (PX1, 1000)], 1.4)
    S.grass(ink, rng, 1030, PY1 - 5, 160)
    ink.apply(ill, INK, 0.9)
    sil = Ink()
    for i, x in enumerate([470, 530, 590, 650, 700, 840]):
        person(sil, x, 940 + (i % 2) * 10, 95, "walk" if i % 3 else "stand", -1 if x > 600 else 1, ["top", "wide", "cap"][i % 3])
    sil.apply(ill, INK, 0.95, grain=0.05)
    label(ill, PCX, 1180, "新英格兰的一个乡镇 · 两三千人", 30)
    return ill


def hall(hands, ledger, rot):
    return S.draw_meeting(t=0.6, hands=hands, ledger=ledger, rot=rot)


def chalk_words(n):
    ill = static(("hall", 1.0, 0.0, 0), lambda: hall(1.0, 0.0, 0)) * 0.55 + hexc("#2f3a2f") * 0.45
    words = ["商量", "让步", "选人", "盯着选上的人"]
    items = []
    for i, w in enumerate(words[:n]):
        items.append((PCX, 520 + i * 150, w, font(FONT_CJK_B, 72), (238, 234, 220, 255), "mm"))
    if items:
        over(ill, text_items(items))
    return ill


def excluded(k):
    ill = paper("america", 73)
    rng = np.random.default_rng(10)
    wall = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 1020), (PX0, 1020)]])
    wash(ill, wall, hexc("#e9e1cb"), 0.5, seed=2, gran=0.2, edge=0.05, bleed=2)
    ink = Ink()
    for j in range(1, 30):
        ink.line([(PX0, PY0 + j * 25), (PX1, PY0 + j * 25)], 0.7, val=120)
    # doorway with warm light
    dx0, dx1, dy0, dy1 = 360, 720, 420, 1020
    dm = mask_from_poly([[(dx0, dy1), (dx1, dy1), (dx1, dy0), (dx0, dy0)]])
    wash(ill, dm, hexc("#e0b25f"), 0.55, seed=11, gran=0.35, edge=0.2, bleed=1.0)
    yy, xx = np.ogrid[:H, :W]
    glow = np.exp(-(((xx - (dx0 + dx1) / 2) / 260.0) ** 2 + ((yy - 760) / 420.0) ** 2)).astype(np.float32) * dm
    ill[:] = ill * (1 - glow[..., None] * 0.35) + hexc("#fbe7b3") * glow[..., None] * 0.35
    ink.line([(dx0, dy1), (dx0, dy0), (dx1, dy0), (dx1, dy1)], 4)
    ink.poly([(PX0, 1020), (PX1, 1020), (PX1, PY1), (PX0, PY1)], 60)
    ink.apply(ill, INK, 0.85)
    inside = Ink()
    for i, x in enumerate(np.linspace(dx0 + 40, dx1 - 40, 6)):
        S.bust_back(inside, x, 1020, 100, raise_=1.0 if i % 2 == 0 else 0.6)
    inside.apply(ill, INK, 0.95, grain=0.05)
    out_l = Ink(); out_r = Ink()
    groups = [(150, [("bonnet", True), ("bonnet", True), ("shawl", True)], "女人"),
              (860, [(None, False), ("cap", False)], "黑人"),
              (980, [(None, False)], "印第安人")]
    for gi, (gx, members, lab) in enumerate(groups):
        for j, (hat, dress) in enumerate(members):
            person(out_l, gx + j * 60 - (len(members) - 1) * 30, 1180, 170, "stand", 1 if gx < 500 else -1, hat, dress)
    out_l.apply(ill, hexc("#77726a"), 0.75, grain=0.05)
    for gi, (gx, members, lab) in enumerate(groups):
        op = ease((k - gi * 0.25) / 0.2)
        if op > 0:
            label(ill, gx, 960 if gx < 500 else 940 + gi * 0, lab, 34, (70, 60, 50, 255), op=op, bold=True)
    label(ill, (dx0 + dx1) / 2, 380, "能在镇民大会上举手的人", 32, bold=True)
    return ill


S03_ORDER = [(None, "town"), ("meeting_hall", "hall"), ("s03_13", "chalk"), ("s03_14", "town"), ("excluded", "excl"), ("s03_18", "town")]


def s03(c):
    cur, prev, x = c.phase(S03_ORDER)
    hands = c.p("hands_up", 2.2)
    ledger = c.p("offices_list", 0.8)
    rot = int(max(0.0, c.since("rotate")) / 0.7) % 12 if c.past("rotate") else 0
    if c.past("s03_10"):
        rot = 0
    nchalk = int(min(4, max(0, c.since("s03_13")) / 1.6 + 1)) if c.past("s03_13") else 0
    ka = c.at("excluded"); kb = c.end("excluded")
    kex = 0.0 if ka is None else min(1.0, max(0.0, (c.tq - ka) / max(1, kb - ka)))

    def get(name):
        if name == "town":
            return static("town", town_wide)
        if name == "hall":
            return static(("hall", q(hands, 12), q(ledger, 8), rot), lambda: hall(q(hands, 12), q(ledger, 8), rot))
        if name == "chalk":
            return static(("chalk", nchalk), lambda: chalk_words(nchalk))
        if name == "excl":
            return static(("excl", q(kex, 20)), lambda: excluded(q(kex, 20)))
    key = (cur, prev, q(x, 15), q(hands, 12), q(ledger, 8), rot, nchalk, q(kex, 20))

    def fn():
        a = get(cur)
        return blend(get(prev), a, x) if prev and x < 1 else a
    return key, fn


def cam_s03(c):
    cur, _, _ = c.phase(S03_ORDER)
    if cur == "town":
        return 1.0 + 0.06 * min(1, c.t / 20), 540, 860
    if cur == "hall" and c.past("offices_list") and not c.past("s03_10"):
        return 1.0, PCX, PCY
    return 1.0 + 0.04 * min(1, c.t / 40), PCX, 900


# ====================================================================== s04 temperance

def icon_box(ill, ink, x, y, w, h, lab, draw):
    m = mask_from_poly([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]])
    ill[:] = ill * (1 - m[..., None] * 0.5) + hexc("#f2e9d2") * m[..., None] * 0.5
    ink.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], 1.6)
    draw(ink, x + w / 2, y + h * 0.42, min(w, h) * 0.5)
    label(ill, x + w / 2, y + h - 34, lab, 32, bold=True)


def ic_flags(ink, cx, cy, s):
    ink.line([(cx - s, cy - s * 0.4), (cx, cy - s * 0.1), (cx + s, cy - s * 0.4)], 1.6)
    for k in range(7):
        t = k / 6
        x = cx - s + 2 * s * t
        y = cy - s * 0.4 + s * 0.3 * math.sin(math.pi * t)
        ink.poly([(x - 10, y), (x + 10, y), (x, y + 26)])
    ink.line([(cx - s, cy - s * 0.6), (cx - s, cy + s * 0.6)], 3); ink.line([(cx + s, cy - s * 0.6), (cx + s, cy + s * 0.6)], 3)


def ic_church(ink, cx, cy, s):
    ink.line([(cx - s * 0.6, cy + s * 0.6), (cx - s * 0.6, cy), (cx + s * 0.6, cy), (cx + s * 0.6, cy + s * 0.6), (cx - s * 0.6, cy + s * 0.6)], 2)
    ink.line([(cx - s * 0.7, cy), (cx, cy - s * 0.45), (cx + s * 0.7, cy)], 2)
    ink.line([(cx, cy - s * 0.45), (cx, cy - s * 0.95)], 2); ink.line([(cx - s * 0.15, cy - s * 0.8), (cx + s * 0.15, cy - s * 0.8)], 2)


def ic_inn(ink, cx, cy, s):
    ink.line([(cx - s * 0.7, cy + s * 0.6), (cx - s * 0.7, cy - s * 0.2), (cx + s * 0.3, cy - s * 0.2), (cx + s * 0.3, cy + s * 0.6)], 2)
    ink.line([(cx - s * 0.8, cy - s * 0.2), (cx - s * 0.2, cy - s * 0.7), (cx + s * 0.4, cy - s * 0.2)], 2)
    ink.line([(cx + s * 0.3, cy - s * 0.05), (cx + s * 0.85, cy - s * 0.05)], 2.4)
    ink.line([(cx + s * 0.5, cy - s * 0.05), (cx + s * 0.5, cy + s * 0.08)], 1.4); ink.line([(cx + s * 0.8, cy - s * 0.05), (cx + s * 0.8, cy + s * 0.08)], 1.4)
    ink.poly([(cx + s * 0.45, cy + s * 0.08), (cx + s * 0.85, cy + s * 0.08), (cx + s * 0.85, cy + s * 0.4), (cx + s * 0.45, cy + s * 0.4)], 200)


def ic_book(ink, cx, cy, s):
    ink.line([(cx, cy + s * 0.5), (cx - s * 0.8, cy + s * 0.35), (cx - s * 0.8, cy - s * 0.45), (cx, cy - s * 0.3), (cx + s * 0.8, cy - s * 0.45), (cx + s * 0.8, cy + s * 0.35), (cx, cy + s * 0.5), (cx, cy - s * 0.3)], 2)
    for k in range(4):
        ink.line([(cx - s * 0.65, cy - s * 0.25 + k * s * 0.15), (cx - s * 0.12, cy - s * 0.15 + k * s * 0.15)], 1)
        ink.line([(cx + s * 0.12, cy - s * 0.15 + k * s * 0.15), (cx + s * 0.65, cy - s * 0.25 + k * s * 0.15)], 1)


def ic_hospital(ink, cx, cy, s):
    ink.line([(cx - s * 0.85, cy + s * 0.6), (cx - s * 0.85, cy - s * 0.3), (cx + s * 0.85, cy - s * 0.3), (cx + s * 0.85, cy + s * 0.6), (cx - s * 0.85, cy + s * 0.6)], 2)
    for r in range(2):
        for k in range(5):
            x = cx - s * 0.7 + k * s * 0.35
            ink.line([(x, cy - s * 0.15 + r * s * 0.35), (x + s * 0.15, cy - s * 0.15 + r * s * 0.35), (x + s * 0.15, cy + r * s * 0.35 + s * 0.05), (x, cy + r * s * 0.35 + s * 0.05), (x, cy - s * 0.15 + r * s * 0.35)], 1.2)
    ink.line([(cx - s * 0.9, cy - s * 0.3), (cx, cy - s * 0.62), (cx + s * 0.9, cy - s * 0.3)], 2)


def ic_school(ink, cx, cy, s):
    ink.line([(cx - s * 0.7, cy + s * 0.6), (cx - s * 0.7, cy - s * 0.1), (cx + s * 0.7, cy - s * 0.1), (cx + s * 0.7, cy + s * 0.6), (cx - s * 0.7, cy + s * 0.6)], 2)
    ink.line([(cx - s * 0.8, cy - s * 0.1), (cx, cy - s * 0.55), (cx + s * 0.8, cy - s * 0.1)], 2)
    ink.poly([(cx - s * 0.08, cy - s * 0.72), (cx + s * 0.08, cy - s * 0.72), (cx + s * 0.08, cy - s * 0.52), (cx - s * 0.08, cy - s * 0.52)])
    ink.line([(cx - s * 0.12, cy + s * 0.6), (cx - s * 0.12, cy + s * 0.15), (cx + s * 0.12, cy + s * 0.15), (cx + s * 0.12, cy + s * 0.6)], 1.6)


ICONS = [("办节庆", ic_flags), ("盖教堂", ic_church), ("开客栈", ic_inn), ("印书", ic_book), ("建医院", ic_hospital), ("办学校", ic_school)]


def icons_grid(n):
    ill = paper("america", 74)
    ink = Ink()
    bw, bh = 400, 270
    for i, (lab, fn) in enumerate(ICONS[:n]):
        x = PX0 + 60 + (i % 2) * (bw + 48)
        y = PY0 + 40 + (i // 2) * (bh + 30)
        icon_box(ill, ink, x, y, bw, bh, lab, fn)
    ink.apply(ill, INK, 0.9)
    return ill


def split_static():
    ill = paper("america", 34)
    right = paper("france", 35)
    rng = np.random.default_rng(0)
    edge = [(540 + 8 * math.sin(y * 0.05) + rng.normal(0, 2), y) for y in range(PY0, PY1 + 10, 10)]
    rm = mask_from_poly([edge + [(PX1 + 20, PY1 + 10), (PX1 + 20, PY0)]])
    ill[:] = ill * (1 - rm[..., None]) + right * rm[..., None]
    wash(ill, rm, hexc("#8794a0"), 0.28, seed=3, gran=0.3, edge=0.1, bleed=2)
    ink = Ink()
    ink.line(edge, 2.2)
    ink.apply(ill, INK, 0.9)
    f = font(FONT_CJK_SB, 44); fs = font(FONT_CJK, 28)
    over(ill, text_items([(298, 380, "美 国", f, (46, 33, 24, 255), "mm"), (298, 432, "“我们自己凑起来”", fs, (90, 66, 45, 255), "mm"),
                          (782, 380, "法 国", f, (36, 40, 48, 255), "mm"), (782, 432, "“请上面来管”", fs, (60, 66, 76, 255), "mm")]))
    pal = Ink()
    S.palace(pal, 782, 640, 330)
    pal.apply(ill, hexc("#232a33"), 0.95, grain=0.04)
    over(ill, text_items([(782, 668, "政府", font(FONT_CJK_SB, 30), (36, 40, 48, 255), "mm")]))
    return ill


_DOTS = None


def dot_data():
    global _DOTS
    if _DOTS is None:
        rng = np.random.default_rng(21)
        N = 700
        sx, sy = rng.uniform(PX0 + 10, 530, N), rng.uniform(500, PY1 - 10, N)
        ring = 1 + (np.arange(N) % 6)
        a = rng.uniform(0, 2 * math.pi, N)
        rr = 110 + ring * 17 + rng.normal(0, 3, N)
        tx, ty = 298 + rr * np.cos(a), 850 + rr * np.sin(a) * 0.9
        delay = rng.random(N) * 0.4
        _DOTS = (sx, sy, tx, ty, delay)
    return _DOTS


def split_dynamic(gather, fly_t, flying):
    ill = static("split_static", split_static)
    sx, sy, tx, ty, delay = dot_data()
    g = np.clip(gather * 1.4 - delay, 0, 1); g = g * g * (3 - 2 * g)
    xs, ys = sx + (tx - sx) * g, sy + (ty - sy) * g
    dots = Ink()
    for x, y in zip(xs, ys):
        dots.ellipse(x, y, 2.6, 2.6)
    dots.apply(ill, INK, 0.9, grain=0.05)
    if gather > 0.6:
        op = ease((gather - 0.6) / 0.4)
        over(ill, text_items([(298, 832, "十万人", font(FONT_CJK_B, 40), (46, 33, 24, int(255 * op)), "mm"),
                              (298, 882, "戒酒会", font(FONT_CJK, 30), (90, 66, 45, int(255 * op)), "mm")]))
    if flying > 0:
        let = Ink()
        rng = np.random.default_rng(22)
        for i in range(130):
            sx_, sy_ = rng.uniform(570, PX1 - 20), rng.uniform(PY1 - 40, PY1 + 220)
            k = (fly_t * 0.22 + rng.random()) % 1.0
            if fly_t * 0.22 < 1 and k > fly_t * 0.22 + 0.05 and rng.random() > 0:
                pass
            tx_, ty_ = 782 + rng.normal(0, 60), 600 + rng.normal(0, 20)
            x = sx_ + (tx_ - sx_) * k + 30 * math.sin(k * 6 + i)
            y = sy_ + (ty_ - sy_) * k
            if y > PY1 - 5 or y < 560:
                continue
            S.envelope(let, x, y, 13 - 5 * k, math.sin(fly_t * 2 + i) * 0.6)
        let.apply(ill, hexc("#232a33"), 0.85 * flying, grain=0.05)
    return ill


def alone_together(k, t):
    ill = paper("america", 75)
    sil = Ink()
    rng = np.random.default_rng(31)
    n = 12
    for i in range(n):
        sx, sy = rng.uniform(PX0 + 70, PX1 - 70), rng.uniform(560, 1180)
        a = 2 * math.pi * i / n
        tx, ty = PCX + 230 * math.cos(a), 900 + 110 * math.sin(a)
        g = ease(k * 1.3 - i * 0.025)
        x, y = sx + (tx - sx) * g, sy + (ty - sy) * g
        moving = 0.02 < g < 0.98
        person(sil, x, y, 120 + 20 * (y - 560) / 620, "walk" if moving else ("talk" if g > 0.98 else "stand"), 1 if tx > sx else -1,
               ["top", "wide", "cap", None, "bonnet"][i % 5], i % 5 == 4, arm_t=t + i)
    sil.apply(ill, INK, 0.95, grain=0.05)
    if k > 0.9:
        label(ill, PCX, 900, "一起", 44, bold=True, op=ease((k - 0.9) / 0.1))
    return ill


def loop_diagram(rot):
    ill = paper("america", 76)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]]), hexc("#b7a789"), 0.2, seed=8, bleed=10)
    ink = Ink()
    cx, cy, R = PCX, 800, 290
    nodes = ["政府替人们包办", "人们忘了怎么凑起来", "更离不开政府"]
    for i in range(3):
        a0 = -math.pi / 2 + i * 2 * math.pi / 3 + 0.42
        a1 = a0 + 2 * math.pi / 3 - 0.84
        pts = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in np.linspace(a0, a1, 30)]
        ink.line(pts, 4)
        ex, ey = pts[-1]; px_, py_ = pts[-3]
        ang = math.atan2(ey - py_, ex - px_)
        ink.poly([(ex + 18 * math.cos(ang), ey + 18 * math.sin(ang)), (ex + 16 * math.cos(ang + 2.4), ey + 16 * math.sin(ang + 2.4)), (ex + 16 * math.cos(ang - 2.4), ey + 16 * math.sin(ang - 2.4))])
    # a token travelling around the loop
    a = -math.pi / 2 + rot
    ink.ellipse(cx + R * math.cos(a), cy + R * math.sin(a), 12, 12)
    ink.apply(ill, INK, 0.9)
    items = []
    for i, n_ in enumerate(nodes):
        a = -math.pi / 2 + i * 2 * math.pi / 3
        items.append((cx + (R + 10) * math.cos(a), cy + (R + 10) * math.sin(a) + (-30 if i == 0 else 40), n_, font(FONT_CJK_SB, 36), (46, 33, 24, 255), "mm"))
    items.append((cx, cy, "停不下来的循环", font(FONT_CJK, 32), (110, 80, 55, 255), "mm"))
    rgba = text_items(items)
    hm = blur(rgba[..., 3], 8) * 0.8
    ill[:] = ill * (1 - hm[..., None]) + hexc("#ece3cb") * hm[..., None]
    over(ill, rgba)
    return ill


S04_ORDER = [(None, "icons"), ("dots_gather", "split"), ("s04_12", "alone"), ("loop", "loop")]


def s04(c):
    cur, prev, x = c.phase(S04_ORDER)
    a3, b3 = c.at("s04_03"), c.end("s04_03")
    n_icons = 2 if a3 is None or c.tq < a3 else min(6, 2 + int((c.tq - a3) / max(0.5, (b3 - a3) / 4.2)))
    gather = c.p("dots_gather", 6.0, smooth=False)
    flying = c.p("letters_fly", 0.6)
    fly_t = max(0.0, c.since("letters_fly"))
    ka = c.at("s04_13")
    k_al = c.p("s04_13", 7.0, smooth=False)
    rot = (c.tq * 0.8) % (2 * math.pi)

    def get(name):
        if name == "icons":
            return static(("icons", n_icons), lambda: icons_grid(n_icons))
        if name == "split":
            if flying > 0 or 0 < gather < 1:
                return split_dynamic(gather, round(fly_t, 2), flying)
            return static(("split", q(gather), 0), lambda: split_dynamic(gather, 0, 0))
        if name == "alone":
            if 0 < k_al < 1:
                return alone_together(k_al, c.tq)
            return static(("alone", q(k_al, 2)), lambda: alone_together(q(k_al, 2), 0.0))
        if name == "loop":
            return loop_diagram(rot)
    dyn = (cur == "split" and (flying > 0 or 0 < gather < 1)) or (cur == "alone" and 0 < k_al < 1) or cur == "loop" or prev == "loop"
    key = (cur, prev, q(x, 15), n_icons, q(gather), q(flying, 10), round(c.tq, 2) if dyn else 0, q(k_al))

    def fn():
        a = get(cur)
        return blend(get(prev), a, x) if prev and x < 1 else a
    return key, fn


def cam_s04(c):
    cur, _, _ = c.phase(S04_ORDER)
    if cur == "split" and not c.past("letters_fly", -0.5):
        k = c.p("dots_gather", 2.0)
        return 1.0 + 0.35 * k, PCX + (300 - PCX) * k, PCY + (850 - PCY) * k
    if cur == "split" and c.past("letters_fly", -0.5) and not c.past("split_both", -0.5):
        k = c.p("letters_fly", 1.5)
        return 1.35 - 0.0 * k, 300 + (782 - 300) * k, 850 + (760 - 850) * k
    return 1.0 + 0.03 * min(1, c.t / 30), PCX, PCY


# ====================================================================== s05 books in the cabin

def forest_static():
    ill = paper("forest", 77)
    rng = np.random.default_rng(12)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]]), hexc("#7e8c5c"), 0.35, seed=3, bleed=10)
    ink = Ink()
    for layer, (n, wmin, wmax, op) in enumerate([(14, 10, 18, 120), (9, 20, 34, 200), (6, 36, 56, 255)]):
        for i in range(n):
            x = rng.uniform(PX0, PX1)
            w_ = rng.uniform(wmin, wmax)
            ink.poly([(x - w_ / 2, PY1), (x + w_ / 2, PY1), (x + w_ * 0.35, PY0), (x - w_ * 0.35, PY0)], op)
    hatch(ink, [[(PX0, 1050), (PX1, 1050), (PX1, PY1), (PX0, PY1)]], 8, 6, 0.8, rng)
    ink.apply(ill, INK, 0.85)
    for i in range(10):
        m = mask_from_poly([crown(rng.uniform(PX0, PX1), rng.uniform(PY0 - 40, 560), rng.uniform(80, 160), rng)])
        wash(ill, m, S.GREEN_D, 0.5, seed=20 + i, bleed=2)
    return ill


def forest_ride(t, k):
    ill = static("forest", forest_static)
    sil = Ink()
    for j in range(2):
        x = PX0 - 160 + (PX1 - PX0 + 320) * k - j * 210
        horse(sil, x, 1120 - j * 6, 230, 1, t=t + j, walking=True)
        person(sil, x + 10, 1120 - 230 * 0.5 - j * 6, 150, "sit", 1, "top")
    sil.apply(ill, NIGHT, 0.95, grain=0.05)
    return ill


def cabin_ext():
    ill = paper("forest", 78)
    rng = np.random.default_rng(13)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 760), (PX0, 760)]]), hexc("#b8c2b0"), 0.35, seed=2, bleed=10)
    wash(ill, mask_from_poly([[(PX0, 760), (PX1, 760), (PX1, PY1), (PX0, PY1)]]), hexc("#9a9a62"), 0.45, seed=3, bleed=4)
    ink = Ink()
    for i in range(16):
        x = PX0 + i * 64 + rng.uniform(-10, 10)
        ink.poly([(x - 9, 790), (x + 9, 790), (x + 6, PY0), (x - 6, PY0)], 230)
    for i in range(8):
        m = mask_from_poly([crown(PX0 + i * 130 + 50, rng.uniform(PY0, 520), rng.uniform(100, 160), rng)])
        wash(ill, m, S.GREEN_D, 0.55, seed=30 + i, bleed=2)
    # log cabin
    x0, x1, base, top = 330, 760, 1030, 840
    cm = mask_from_poly([[(x0, base), (x1, base), (x1, top), (x0, top)]])
    wash(ill, cm, S.WOOD, 0.7, seed=5, gran=0.5, edge=0.3, bleed=0.6)
    for k in range(9):
        y = top + k * (base - top) / 9
        ink.line([(x0 - 14, y), (x1 + 14, y)], 2.2)
        ink.ellipse(x0 - 10, y + 10, 10, 10, None, 255, 1.4); ink.ellipse(x1 + 10, y + 10, 10, 10, None, 255, 1.4)
    roof = [(x0 - 40, top + 4), ((x0 + x1) / 2, top - 150), (x1 + 40, top + 4)]
    ink.poly(roof, 200)
    ink.poly([(x0 + 90, top - 60), (x0 + 130, top - 60), (x0 + 130, top - 160), (x0 + 90, top - 160)], 255)
    ink.poly([(560, 915), (620, 915), (620, 985), (560, 985)], 0)
    ink.line([(560, 915), (620, 915), (620, 985), (560, 985), (560, 915)], 2.4)
    ink.poly([(420, base), (480, base), (480, 920), (420, 920)], 255)
    # stumps
    for sx in (180, 260, 860, 950):
        ink.poly([(sx - 22, 1110), (sx + 22, 1110), (sx + 20, 1080), (sx - 20, 1080)], 230)
        ink.ellipse(sx, 1080, 21, 7, None, 255, 1.4)
    S.grass(ink, rng, 1060, PY1 - 5, 150)
    ink.apply(ill, INK, 0.9)
    label(ill, PCX, 1185, "密歇根荒野里的一间圆木屋", 30)
    return ill


def cabin_smoke(t):
    ill = static("cabin_ext", cabin_ext)
    for k in range(7):
        ph = (t * 0.25 + k / 7) % 1.0
        sx, sy = 440 + 60 * ph, 680 - 260 * ph
        m = mask_from_poly([crown(sx, sy, 12 + 40 * ph, np.random.default_rng(k), n=12)])
        wash(ill, m, hexc("#8a8a84"), 0.35 * (1 - ph), seed=k, bleed=4 + 6 * ph)
    return ill


def cabin_int(shake=0.0):
    ill = paper("forest", 79)
    rng = np.random.default_rng(14)
    wall = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 900), (PX0, 900)]])
    wash(ill, wall, S.WOOD, 0.55, seed=2, gran=0.5, edge=0.1, bleed=2)
    ink = Ink()
    for k in range(13):
        y = PY0 + k * 46
        ink.line([(PX0, y), (PX1, y)], 2.0)
    # window with forest light
    wm = mask_from_poly([[(640, 380), (900, 380), (900, 620), (640, 620)]])
    ill[:] = ill * (1 - wm[..., None]) + hexc("#e8ecd9") * wm[..., None]
    ink.line([(640, 380), (900, 380), (900, 620), (640, 620), (640, 380)], 3)
    ink.line([(770, 380), (770, 620)], 2); ink.line([(640, 500), (900, 500)], 2)
    for i in range(5):
        ink.poly([(660 + i * 50, 620), (672 + i * 50, 620), (670 + i * 50, 400), (662 + i * 50, 400)], 150)
    # table
    tm = mask_from_poly([[(PX0, 900), (PX1, 900), (PX1, PY1), (PX0, PY1)]])
    wash(ill, tm, hexc("#7a4f2e"), 0.6, seed=3, gran=0.5, bleed=1)
    for k in range(6):
        ink.line([(PX0, 930 + k * 55), (PX1, 930 + k * 55 + rng.normal(0, 3))], 1.0)
    # axe leaning on the wall
    ink.line([(170, 1050), (300, 650)], 7)
    ink.poly([(292, 640), (345, 625), (350, 690), (300, 680)])
    # Bible (thick, dark)
    bm = mask_from_poly([[(340, 1000), (600, 1000), (590, 1060), (330, 1060)]])
    wash(ill, bm, hexc("#3b2a20"), 0.9, seed=6, bleed=0.5)
    ink.line([(340, 1000), (600, 1000), (590, 1060), (330, 1060), (340, 1000)], 2)
    ink.line([(345, 1010), (595, 1010)], 1.0)
    # newspapers
    for j in range(3):
        pts = [(600 + j * 18, 1080 - j * 8), (900 + j * 10, 1060 - j * 12), (930 + j * 10, 1150 - j * 10), (620 + j * 18, 1170 - j * 6)]
        pm = mask_from_poly([pts])
        ill[:] = ill * (1 - pm[..., None] * 0.95) + hexc("#ece3c9") * pm[..., None] * 0.95
        ink.line(pts + [pts[0]], 1.4)
    for k in range(9):
        ink.line([(650, 1090 + k * 7 + 18), (900, 1075 + k * 7 + 18)], 0.8, val=140)
    # Shakespeare volumes
    for j in range(3):
        x = 120 + j * 62
        vm = mask_from_poly([[(x, 1180), (x + 54, 1180), (x + 54, 1000), (x, 1000)]])
        wash(ill, vm, hexc(["#5d2b22", "#2f3f2c", "#4a3424"][j]), 0.85, seed=7 + j, bleed=0.4)
        ink.line([(x, 1180), (x + 54, 1180), (x + 54, 1000), (x, 1000), (x, 1180)], 1.4)
    ink.apply(ill, INK, 0.9)
    over(ill, text_items([(465, 1030, "HOLY BIBLE", font(FONT_FR, 26), (210, 190, 140, 255), "mm"),
                          (780, 1100, "NEWS", font(FONT_FR, 40), (60, 50, 40, 255), "mm")]))
    vt = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
    ImageDraw.Draw(vt).text((100, 30), "SHAKESPEARE", font=font(FONT_FR, 24), fill=(215, 190, 130, 255), anchor="mm")
    vt = np.asarray(vt.rotate(90, expand=True)).astype(np.float32) / 255
    for j in range(3):
        x = 120 + j * 62 + 27 - vt.shape[1] // 2
        y = 1090 - vt.shape[0] // 2
        reg = ill[y:y + vt.shape[0], x:x + vt.shape[1]]
        a = vt[..., 3:4]
        ill[y:y + vt.shape[0], x:x + vt.shape[1]] = reg * (1 - a) + vt[..., :3] * a
    return ill


def henry_v():
    ill = paper("forest", 80)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]]), hexc("#7a4f2e"), 0.55, seed=4, bleed=6)
    pm = mask_from_poly([[(170, 420), (540, 440), (540, 1150), (170, 1130)], [(540, 440), (910, 420), (910, 1130), (540, 1150)]])
    ill[:] = ill * (1 - pm[..., None] * 0.96) + hexc("#efe5c9") * pm[..., None] * 0.96
    ink = Ink()
    ink.line([(170, 420), (540, 440), (910, 420), (910, 1130), (540, 1150), (170, 1130), (170, 420)], 2)
    ink.line([(540, 440), (540, 1150)], 2)
    for k in range(20):
        y = 720 + k * 20
        if y < 1100:
            ink.line([(590, y), (870, y - 2)], 0.8, val=130)
    ink.apply(ill, INK, 0.85)
    over(ill, text_items([(355, 600, "THE LIFE OF", font(FONT_FR, 30), (46, 33, 24, 255), "mm"),
                          (355, 660, "KING HENRY", font(FONT_FR, 40), (46, 33, 24, 255), "mm"),
                          (355, 715, "THE FIFTH", font(FONT_FR, 40), (46, 33, 24, 255), "mm"),
                          (355, 830, "SHAKESPEARE", font(FONT_FR_I, 30), (90, 66, 45, 255), "mm"),
                          (725, 650, "ACT I", font(FONT_FR, 30), (46, 33, 24, 255), "mm")]))
    label(ill, PCX, 1210, "他第一次读《亨利五世》，是在一间圆木屋里", 30)
    return ill


S05_ORDER = [(None, "ride"), ("cabin_ext", "ext"), ("cabin_int", "int"), ("shakespeare", "henry"), ("s05_07", "int")]


def s05(c):
    cur, prev, x = c.phase(S05_ORDER)
    a, b = c.at("forest_ride") or 0.0, c.at("cabin_ext") or 12.0
    k = min(1.0, max(0.0, (c.tq - a + 0.6) / max(1.0, b - a)))

    def get(name):
        if name == "ride":
            return forest_ride(c.tq, k)
        if name == "ext":
            return cabin_smoke(c.tq)
        if name == "int":
            return static("cabin_int", cabin_int)
        if name == "henry":
            return static("henry", henry_v)
    dyn = cur in ("ride", "ext") or prev in ("ride", "ext")
    key = (cur, prev, q(x, 15), round(c.tq, 2) if dyn else 0)

    def fn():
        a_ = get(cur)
        return blend(get(prev), a_, x) if prev and x < 1 else a_
    return key, fn


def cam_s05(c):
    cur, _, _ = c.phase(S05_ORDER)
    if cur == "int":
        if c.past("bible_axe_paper", -0.3) and not c.past("shakespeare", -0.3):
            k = c.p("bible_axe_paper", 2.5)
            return 1.0 + 0.3 * k, PCX + (560 - PCX) * k, PCY + (1000 - PCY) * k
        return 1.0 + 0.05 * min(1, c.t / 20), PCX, 900
    return 1.0 + 0.04 * min(1, c.t / 20), PCX, PCY


# ====================================================================== s06 why here

def compact(nsig):
    ill = S.draw_sea(t=0.0, ship_x=0.08)
    m = mask_from_poly([[(560, 380), (960, 400), (950, 860), (570, 850)]])
    ill[:] = ill * (1 - m[..., None] * 0.95) + hexc("#f1e7cc") * m[..., None] * 0.95
    ink = Ink()
    ink.line([(560, 380), (960, 400), (950, 860), (570, 850), (560, 380)], 2)
    for k in range(5):
        ink.line([(600, 470 + k * 30), (910, 480 + k * 30)], 0.9, val=150)
    rng = np.random.default_rng(15)
    for i in range(nsig):
        x = 600 + (i % 3) * 110 + rng.uniform(-6, 6)
        y = 660 + (i // 3) * 48
        pts = [(x + j * 9, y + 6 * math.sin(j * 1.7 + i)) for j in range(10)]
        ink.line(pts, 1.6)
    ink.apply(ill, INK, 0.9)
    label(ill, 760, 425, "1620 年 · 船上的约定", 30, bold=True)
    return ill


def pyramid(k):
    ill = paper("america", 81)
    ink = Ink()
    levels = ["乡镇", "县", "州", "联邦"]
    items = []
    for i, lab in enumerate(levels):
        g = ease(k * 4 - i)
        if g <= 0:
            continue
        w = 560 - i * 110
        y = 1130 - i * 150
        yy = y - 400 * (1 - g)
        ink.line([(PCX - w / 2, yy), (PCX + w / 2, yy), (PCX + w / 2, yy - 120), (PCX - w / 2, yy - 120), (PCX - w / 2, yy)], 2.4)
        items.append((PCX, yy - 60, lab, font(FONT_CJK_B, 46), (46, 33, 24, int(255 * g)), "mm"))
    # arrow up
    if k > 0.9:
        ink.line([(PCX + 360, 1100), (PCX + 360, 560)], 4)
        ink.poly([(PCX + 340, 570), (PCX + 380, 570), (PCX + 360, 520)])
        items.append((PCX + 360, 1160, "从下往上", font(FONT_CJK_SB, 30), (46, 33, 24, 255), "mm"))
    ink.apply(ill, INK, 0.9)
    if items:
        over(ill, text_items(items))
    label(ill, PCX, 380, "在美国：先有乡镇，再有县、州、联邦", 32, bold=True)
    return ill


def no_lords():
    ill = paper("america", 82)
    ink = Ink()
    cx, cy = 330, 720
    pts = [(cx - 120, cy + 60), (cx - 130, cy - 50), (cx - 60, cy + 10), (cx, cy - 80), (cx + 60, cy + 10), (cx + 130, cy - 50), (cx + 120, cy + 60)]
    ink.line(pts + [pts[0]], 3)
    for x in (cx - 130, cx, cx + 130):
        ink.ellipse(x, cy - 60 if x != cx else cy - 92, 10, 10)
    ink.apply(ill, hexc("#8a857c"), 0.8)
    r = Ink()
    r.line([(cx - 160, cy + 110), (cx + 160, cy - 130)], 6)
    r.apply(ill, RED, 0.8)
    label(ill, cx, 900, "没有世袭贵族", 36, bold=True)
    S.office_icon(ill)
    label(ill, 900, 580, "远在天边的衙门", 28, (110, 108, 100, 255))
    return ill


def gears(t):
    ill = paper("america", 83)
    ink = Ink()
    specs = [(330, 700, 120, 12, 1), (520, 820, 80, 8, -1.5), (690, 700, 110, 11, 1.09), (480, 560, 70, 7, -1.7)]
    for gx, gy, r, n, sp in specs:
        a0 = t * 0.6 * sp
        pts = []
        for i in range(n * 4):
            a = a0 + 2 * math.pi * i / (n * 4)
            rr = r * (1.12 if (i % 4) in (1, 2) else 0.95)
            pts.append((gx + rr * math.cos(a), gy + rr * math.sin(a)))
        ink.line(pts + [pts[0]], 2.4)
        ink.ellipse(gx, gy, r * 0.25, r * 0.25, None, 255, 2)
        for k in range(4):
            a = a0 + k * math.pi / 2
            ink.line([(gx + r * 0.25 * math.cos(a), gy + r * 0.25 * math.sin(a)), (gx + r * 0.85 * math.cos(a), gy + r * 0.85 * math.sin(a))], 2)
    # empty motor slot
    dsh = [(820, 900), (980, 900), (980, 1060), (820, 1060)]
    for a, b in zip(dsh, dsh[1:] + dsh[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L / 12)
        for i in range(0, n, 2):
            ink.line([(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n), (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)], 1.8)
    ink.apply(ill, INK, 0.9)
    label(ill, 900, 980, "发动机？", 34, (110, 100, 90, 255), bold=True)
    return ill


def broken_bridge(k, t):
    ill = paper("america", 84)
    rng = np.random.default_rng(16)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 760), (PX0, 760)]]), hexc("#c3cdc6"), 0.35, seed=3, bleed=10)
    wash(ill, mask_from_poly([[(PX0, 760), (PX1, 760), (PX1, PY1), (PX0, PY1)]]), hexc("#a9ae72"), 0.45, seed=4, bleed=4)
    wash(ill, mask_from_poly([[(PX0, 960), (PX1, 940), (PX1, 1060), (PX0, 1080)]]), hexc("#6f8f8f"), 0.6, seed=5, bleed=2)
    ink = Ink()
    hills = [(PX0, 760)] + [(PX0 + (PX1 - PX0) * i / 20, 720 - 40 * math.sin(i * 0.4) - 10 * rng.random()) for i in range(21)] + [(PX1, 760)]
    hatch(ink, [hills], -15, 6, 0.8, rng)
    ink.ellipse(900, 800, 40, 22, None, 255, 1.6)  # a lone farm far away
    for i in range(30):
        x = PX0 + i * 33
        ink.line([(x, 1000 + rng.normal(0, 2)), (x + 18, 1000 + rng.normal(0, 2))], 1.0, val=150)
    # bridge: left half intact, right half planks being replaced
    ink.line([(250, 950), (540, 950)], 5)
    n_planks = int(k * 8)
    for i in range(8):
        x = 540 + i * 36
        if i < n_planks:
            ink.line([(x, 950), (x + 34, 950)], 5)
    for px in (250, 400, 540, 700, 830):
        ink.line([(px, 950), (px, 1050)], 4)
    ink.apply(ill, INK, 0.9)
    sil = Ink()
    person(sil, 520, 945, 150, "carry", 1, "wide", arm_t=t)
    person(sil, 470, 945, 160, "talk", 1, "cap", arm_t=t)
    person(sil, 880, 1100, 150, "carry", -1, "wide", arm_t=t)
    sil.apply(ill, INK, 0.95, grain=0.05)
    return ill


S06_ORDER = [(None, "town"), ("mayflower", "compact"), ("pyramid_up", "pyramid"), ("layer2", "lords"), ("s06_07", "gears"),
             ("layer3", "bridge"), ("s06_09", "three")]


def three_words():
    ill = paper("america", 85)
    big_text(ill, ["历史", "信仰", "土地"], 620, 84, lh=1.7)
    return ill


def s06(c):
    cur, prev, x = c.phase(S06_ORDER)
    nsig = int(min(9, max(0, c.since("mayflower")) / 0.6)) if c.past("mayflower") else 0
    kp = c.p("pyramid_up", 5.0, smooth=False)
    kb = c.p("layer3", 6.0, smooth=False)

    def get(name):
        if name == "town":
            return static("town", town_wide)
        if name == "compact":
            return static(("compact", nsig), lambda: compact(nsig))
        if name == "pyramid":
            return static(("pyr", q(kp)), lambda: pyramid(q(kp)))
        if name == "lords":
            return static("lords", no_lords)
        if name == "gears":
            return gears(c.tq)
        if name == "bridge":
            return broken_bridge(kb, c.tq)
        if name == "three":
            return static("three", three_words)
    dyn = cur in ("gears", "bridge") or prev in ("gears", "bridge")
    key = (cur, prev, q(x, 15), nsig, q(kp), round(c.tq, 2) if dyn else 0)

    def fn():
        a = get(cur)
        return blend(get(prev), a, x) if prev and x < 1 else a
    return key, fn


def ov_s06(c, fr, overlay):
    pass


# ====================================================================== s07 a bell tower

def archives():
    ill = paper("oldfrance", 86)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]]), hexc("#5d6873"), 0.45, seed=2, bleed=10)
    ink = Ink()
    rng = np.random.default_rng(17)
    # shelves of bundled files
    for r in range(4):
        y = 420 + r * 150
        ink.line([(PX0, y + 120), (PX1, y + 120)], 3)
        x = PX0 + 10
        while x < PX1 - 40:
            w_ = rng.uniform(30, 70)
            ink.line([(x, y + 120), (x, y + rng.uniform(20, 50)), (x + w_, y + rng.uniform(20, 50)), (x + w_, y + 120)], 1.4)
            ink.line([(x, y + 80), (x + w_, y + 80)], 1.0, val=150)
            x += w_ + 4
    ink.apply(ill, INK, 0.7)
    # desk + reading figure + candle glow
    glow = np.zeros((H, W), np.float32)
    yy, xx = np.ogrid[:H, :W]
    glow = np.exp(-(((xx - 700) ** 2 + (yy - 1000) ** 2) / (2 * 180 ** 2))).astype(np.float32)
    ill[:] = ill * (1 - glow[..., None] * 0.6) + hexc("#f4d999") * glow[..., None] * 0.6
    sil = Ink()
    sil.poly([(PX0, 1080), (PX1, 1080), (PX1, 1110), (PX0, 1110)])
    person(sil, 460, 1240, 300, "sit", 1, None)
    for k in range(5):
        sil.poly([(560 + k * 4, 1080 - k * 14), (680 + k * 4, 1080 - k * 14), (680 + k * 4, 1068 - k * 14), (560 + k * 4, 1068 - k * 14)], 200)
    sil.poly([(694, 1080), (706, 1080), (706, 1020), (694, 1020)])
    sil.apply(ill, NIGHT, 0.95, grain=0.05)
    f = Ink(); f.ellipse(700, 1008, 6, 12); f.apply(ill, hexc("#fff1c4"), 0.95, grain=0)
    label(ill, PCX, 380, "法国各省的旧档案", 32, (235, 230, 220, 255), bold=True)
    return ill


def same_origin(k):
    ill = paper("oldfrance", 87)
    ink = Ink()
    rng = np.random.default_rng(18)
    S.church(ink, PCX - 30, 560, 150)
    items = [(PCX, 610, "中世纪的乡村教区", font(FONT_CJK_SB, 32), (46, 33, 24, 255), "mm")]
    # left branch across the sea -> New England town
    g1 = ease(k * 2)
    pts = [(PCX - 40, 650), (PCX - 180, 760), (300, 900)]
    if g1 > 0:
        n = int(30 * g1)
        path = [(pts[0][0] + (pts[2][0] - pts[0][0]) * i / 29, pts[0][1] + (pts[2][1] - pts[0][1]) * i / 29 + 40 * math.sin(math.pi * i / 29)) for i in range(n)]
        if len(path) > 1:
            ink.line(path, 3)
        for wv in range(4):
            y = 800 + wv * 14
            ink.line([(330 + i * 12, y + 4 * math.sin(i)) for i in range(14)], 1.2)
    g2 = ease(k * 2 - 1)
    if g2 > 0:
        n = int(30 * g2)
        path = [(PCX + 40 + (780 - PCX - 40) * i / 29, 650 + (900 - 650) * i / 29) for i in range(n)]
        if len(path) > 1:
            ink.line(path, 3)
    ink.apply(ill, INK, 0.9)
    if g1 > 0.95:
        tmp = Ink()
        meeting_house(tmp, ill, 160, 1120, 250, rng)
        tmp.apply(ill, INK, 0.9)
        items.append((285, 1170, "新英格兰的乡镇：自己当家", font(FONT_CJK_SB, 30), (46, 33, 24, 255), "mm"))
    if g2 > 0.95:
        tmp = Ink()
        S.church(tmp, 760, 1120, 150)
        tmp.apply(ill, INK, 0.9)
        # the state's big hand above
        hand = Ink()
        hx, hy = 790, 860
        hand.poly([(hx - 130, hy), (hx + 130, hy), (hx + 120, hy + 40), (hx - 120, hy + 40)], 200)
        for f_ in range(4):
            hand.poly([(hx - 110 + f_ * 62, hy + 30), (hx - 70 + f_ * 62, hy + 30), (hx - 75 + f_ * 62, hy + 120), (hx - 105 + f_ * 62, hy + 120)], 200)
        hand.apply(ill, hexc("#38404a"), 0.7, grain=0.05)
        items.append((780, 1170, "法国的教区：攥在国家手里", font(FONT_CJK_SB, 30), (46, 33, 24, 255), "mm"))
    over(ill, text_items(items))
    return ill


def windy_village():
    ill = S.draw_paper_route(t=0, doc=0.0, cal=1)
    return ill


def crown_falls(k):
    ill = S.draw_paper_route(t=0, doc=0.99, cal=3)
    cr = Ink()
    cx, cy = 420, 360 + 300 * ease(k)
    pts = [(cx - 60, cy + 30), (cx - 65, cy - 25), (cx - 30, cy + 5), (cx, cy - 40), (cx + 30, cy + 5), (cx + 65, cy - 25), (cx + 60, cy + 30)]
    cr.poly(pts)
    cr.apply(ill, hexc("#b08a3a"), 0.9 * (1 - 0.8 * ease(k)), grain=0.1)
    if k > 0.5:
        label(ill, PCX, 1220, "国王倒了，公文的路还在", 32, (60, 66, 76, 255), bold=True, op=ease((k - 0.5) / 0.4))
    return ill


S07_ORDER = [(None, "arch"), ("s07_02", "origin"), ("village", "village"), ("paper_route", "route"), ("s07_12", "crown"), ("s07_14", "two")]


def s07(c):
    cur, prev, x = c.phase(S07_ORDER)
    ko = c.p("s07_03", 4.0, smooth=False) if c.past("s07_03") else 0.0
    a, b = c.at("paper_route"), c.at("s07_09")
    doc = 0.0 if a is None else min(0.99, max(0.0, (c.tq - a) / max(1.0, (b or a + 10) - a)))
    cal = 1
    if c.past("calendar"):
        cal = 1 + min(2, int(c.since("calendar") / 1.6))
    kc = c.p("s07_12", 3.0, smooth=False)

    def get(name):
        if name == "arch":
            return static("arch", archives)
        if name == "origin":
            return static(("origin", q(ko, 20)), lambda: same_origin(q(ko, 20)))
        if name == "village":
            return static("village", windy_village)
        if name == "route":
            return static(("route", q(doc, 40), cal), lambda: S.draw_paper_route(t=0, doc=q(doc, 40), cal=cal))
        if name == "crown":
            return static(("crown", q(kc, 20)), lambda: crown_falls(q(kc, 20)))
        if name == "two":
            return static(("split", 1.0, 0), lambda: split_dynamic(1.0, 0, 0))
    key = (cur, prev, q(x, 15), q(ko, 20), q(doc, 40), cal, q(kc, 20))

    def fn():
        a_ = get(cur)
        return blend(get(prev), a_, x) if prev and x < 1 else a_
    return key, fn


def cam_s07(c):
    cur, _, _ = c.phase(S07_ORDER)
    if cur == "village":
        k = c.p("village", 3)
        return 1.0 + 0.5 * k, PCX + (260 - PCX) * k, PCY + (1000 - PCY) * k
    if cur == "route" and c.past("calendar", -0.3):
        k = c.p("calendar", 1.2)
        return 1.0 + 0.6 * k, PCX + (895 - PCX) * k, PCY + (1095 - PCY) * k
    return 1.0 + 0.03 * min(1, c.t / 20), PCX, PCY


# ====================================================================== s08 the circle

def s08(c):
    drawn = c.p("circle_draw", 2.5)
    out = c.p("step_out", 2.5, smooth=False)
    turned = c.p("turn_backs", 2.5, smooth=False)
    shrink = 0.0
    if c.past("bubble_shrink"):
        shrink = 0.3 + 0.7 * c.p("bubble_shrink", 4.0)
    elif c.past("step_out"):
        shrink = 0.0
    else:
        shrink = 1.0
    gray = 0.25 * c.p("turn_backs", 2.0) + 0.6 * c.p("bubble_shrink", 4.0)
    moving = 0 < out < 1
    tt = round(c.tq, 2) if moving else 0.5
    key = (q(drawn), q(out), q(turned, 20), q(shrink, 20), q(gray, 20), tt)

    def fn():
        return S.draw_circle(t=tt, drawn=q(drawn), out=q(out) if out < 1 else 1.0, turned=q(turned, 20), shrink=q(shrink, 20), gray=q(gray, 20))
    return key, fn


def cam_s08(c):
    if c.past("bubble_shrink", -0.3):
        k = c.p("bubble_shrink", 3)
        return 1.0 + 0.45 * k, PCX + (900 - PCX) * k, PCY + (860 - PCY) * k
    return 1.0 + 0.03 * min(1, c.t / 20), PCX, PCY


# ====================================================================== s09 Memphis

def memphis_static():
    ill = paper("ice", 51)
    rng = np.random.default_rng(0)
    hor = 690
    for k, (y0, op) in enumerate([(PY0, 0.55), (PY0 + 120, 0.35), (PY0 + 240, 0.25)]):
        m = mask_from_poly([[(PX0, y0), (PX1, y0), (PX1, hor), (PX0, hor)]])
        wash(ill, m, hexc("#5b7088"), op, seed=60 + k, gran=0.2, edge=0.05, bleed=40)
    river = mask_from_poly([[(PX0, hor), (PX1, hor), (PX1, 1090), (PX0, 1110)]])
    wash(ill, river, hexc("#3a5068"), 0.8, seed=63, gran=0.3, edge=0.1, bleed=2)
    ink = Ink()
    fb = [(PX0, hor + 4)] + [(PX0 + (PX1 - PX0) * i / 119, hor - 20 - 9 * abs(math.sin(i * 0.9)) - 6 * abs(math.sin(i * 2.3)) - 4 * rng.random()) for i in range(120)] + [(PX1, hor + 4)]
    ink.poly(fb, 210)
    floes = []
    rngf = np.random.default_rng(70)
    for i in range(46):
        yy = hor + 12 + (rngf.random() ** 1.6) * (1080 - hor - 20)
        sc = 0.25 + 1.2 * (yy - hor) / (1080 - hor)
        xx = rngf.uniform(PX0 - 40, PX1 + 40)
        w_, h_ = rngf.uniform(30, 75) * sc, rngf.uniform(7, 15) * sc
        pts = [(xx + w_ * math.cos(2 * math.pi * v / 7 + rngf.uniform(-0.2, 0.2)) * rngf.uniform(0.7, 1.1),
                yy + h_ * math.sin(2 * math.pi * v / 7) * rngf.uniform(0.7, 1.1)) for v in range(7)]
        floes.append(pts)
    fm = mask_from_poly(floes)
    lighten(ill, blur(fm, 0.8), hexc("#e8eef3"), 0.92)
    sidem = mask_from_poly([[(px, py + 4) for px, py in f] for f in floes]) * (1 - fm)
    lighten(ill, sidem, hexc("#8fa3b6"), 0.6)
    for f in floes:
        ink.line(f, 1.0, closed=True, val=150)
    for k in range(40):
        yy = hor + 10 + (k / 40) ** 1.5 * (1080 - hor)
        x0 = rng.uniform(PX0, PX1 - 100)
        ink.line([(x0 + i * 14, yy + rng.normal(0, 0.8)) for i in range(8)], 0.7, val=120)
    ink.apply(ill, NIGHT, 0.85)
    bank = [(PX0, 1085), (250, 1072), (360, 1058), (560, 1075), (PX1, 1095), (PX1, PY1), (PX0, PY1)]
    bm = mask_from_poly([bank])
    lighten(ill, bm, hexc("#e3e9ee"), 0.9)
    wash(ill, bm, hexc("#9fb0c0"), 0.25, seed=82, gran=0.6, edge=0.05, bleed=3)
    gi = Ink()
    for _ in range(140):
        x = rng.uniform(PX0, PX1); y = rng.uniform(1110, PY1 - 5)
        gi.line([(x, y), (x + rng.uniform(-4, 4), y - rng.uniform(4, 12))], 1.0)
    gi.line(bank[:5], 1.6)
    # forest edge on the near-left (where the column comes from)
    for i in range(7):
        x = PX0 + i * 22
        gi.poly([(x - 8, 1090), (x + 8, 1090), (x + 5, 780 + 30 * (i % 3)), (x - 5, 780 + 30 * (i % 3))], 255)
    gi.apply(ill, NIGHT, 0.75)
    return ill


_SNOW = None


def snow_layer(t, amount):
    global _SNOW
    if _SNOW is None:
        rs = np.random.default_rng(99)
        _SNOW = (rs.uniform(PX0, PX1, 520), rs.uniform(PY0, PY1, 520), rs.uniform(18, 45, 520), rs.uniform(1.0, 2.6, 520), rs.uniform(150, 255, 520))
    x0, y0, v, r, val = _SNOW
    sn = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(sn)
    ys = (y0 - PY0 + v * t) % (PY1 - PY0) + PY0
    xs = x0 + 10 * np.sin(t * 0.8 + np.arange(len(x0)))
    for x, y, rr, vv in zip(xs, ys, r, val):
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(vv))
    return np.asarray(sn).astype(np.float32) / 255 * amount


def memphis(t, boat_x, column, boarding, dogs_in, howl, snow=1.0, people=True, dogs=True):
    ill = static("memphis_static", memphis_static)
    rng = np.random.default_rng(1)
    boat = Ink(); light = Ink()
    bx = 500 + boat_x * 650
    chim = S.steamboat(boat, bx, 905, 560, rng, light=light)
    plank_a, plank_b = (330, 1060), (bx + 30, 880)
    if boat_x < 0.02 and boarding < 0.999:
        boat.line([plank_a, plank_b], 7)
    boat.apply(ill, NIGHT, 0.96, grain=0.04)
    light.apply(ill, hexc("#7d8fa3"), 0.8, grain=0.05)
    for j, cpos in enumerate(chim):
        for k in range(8):
            ph = (t * 0.35 + k / 8.0) % 1.0
            sx, sy = cpos[0] + 140 * ph ** 1.3, cpos[1] - 260 * ph
            pm = mask_from_poly([crown(sx, sy, 10 + 46 * ph, np.random.default_rng(80 + k + 10 * j), n=12)])
            wash(ill, pm, hexc("#3e4a58"), 0.42 * (1 - ph) ** 1.2, seed=81 + k, gran=0.3, edge=0.1, bleed=3 + 6 * ph)
    sil = Ink()
    if people:
        N = 16
        for i in range(N):
            # walk along the bank to a queue position, then board
            u_bank = min(1.0 - i * 0.055, column * 1.6 - i * 0.09)
            u = u_bank + boarding * (1.0 + i * 0.055 + 1.0) * 1.0
            if u < 0 or u > 2.0:
                continue
            if u <= 1.0:
                x = PX0 - 20 + (plank_a[0] - PX0 + 20) * u
                y = 1100 - 40 * u
            else:
                k = u - 1.0
                x = plank_a[0] + (plank_b[0] - plank_a[0]) * k
                y = plank_a[1] + (plank_b[1] - plank_a[1]) * k
            sc = 1.0 - 0.25 * max(0, u - 1)
            hh = (95 + 30 * ((i * 37) % 10) / 10) * sc
            kind = i % 5
            walking = 0 < column < 1 or 0 < boarding < 1
            if kind == 0:
                person(sil, x, y, hh, "huddle", 1, "shawl", True)
            elif kind == 1:
                person(sil, x, y, hh, "walk" if walking else "stand", 1, None, False, arm_t=t + i)
            elif kind == 2:
                person(sil, x, y, hh * 0.92, "bow", 1, "shawl", True)
            elif kind == 3:
                person(sil, x, y, hh, "carry", 1, "shawl", True)
                sil.ellipse(x + hh * 0.12, y - hh * 0.8, hh * 0.09, hh * 0.08)
            else:
                person(sil, x, y, hh * 0.7, "walk" if walking else "stand", 1, None, False, arm_t=t + i, child=True)
    if dogs:
        dpos = [(470, 1175, 150), (650, 1160, 128), (300, 1200, 136)]
        for j, (x, y, s) in enumerate(dpos):
            hw = min(1.0, howl * (1.0 if j == 0 else 0.8))
            if howl > 0:
                hw = hw * (0.85 + 0.15 * math.sin(t * 3 + j))
            k = min(1.0, max(0.0, dogs_in * 1.2 - j * 0.12))
            arrive = ease(min(1.0, max(0.0, column * 1.3 - 0.15 - j * 0.1)))
            if arrive < 1.0:
                if arrive <= 0:
                    continue
                x = x - (1 - arrive) * (x - PX0 + 160)
            if k > 0:
                tx, ty = 520 + 110 * j + 260 * k, 1030 - 70 * k
                kk = min(1, k * 1.5)
                dog(sil, x + (tx - x) * kk, y + (ty - y) * kk, s * (1 - 0.45 * k), 1, 0.1, swim=k > 0.6)
            else:
                dog(sil, x, y, s, 1, hw)
    sil.apply(ill, NIGHT, 0.97, grain=0.04)
    if snow > 0:
        lighten(ill, snow_layer(t, 1.0), hexc("#f4f7fa"), 0.85 * snow)
    return ill


def s09(c):
    t = c.tq
    boat_x = 1.0 - c.p("s09_02", 7.0) if not c.past("s09_03") else 0.0
    if c.past("dogs_howl"):
        boat_x = 0.75 * c.p("dogs_howl", 12.0, delay=1.5, smooth=False)
    if c.past("question", -0.3):
        boat_x = 0.75
    column = c.p("column_arrives", 9.0, smooth=False)
    boarding = c.p("boarding", max(4.0, (c.at("dogs_shore") or 30) - (c.at("boarding") or 0) - 1.0), smooth=False) if c.past("boarding") else 0.0
    if c.past("dogs_shore"):
        boarding = 1.0
    dogs_in = c.p("dogs_howl", 4.0, delay=3.0, smooth=False)
    howl = c.p("dogs_howl", 0.8) if c.past("dogs_howl") else 0.0
    if c.past("dogs_howl", 3.0):
        howl = max(0.0, 1 - c.p("dogs_howl", 1.0, delay=3.0))
    people = not c.past("dogs_shore")
    dogs = not c.past("question", -0.3)
    key = (round(t, 2), q(boat_x, 200), q(column, 60), q(boarding, 60), q(dogs_in, 60), q(howl, 20), people, dogs)

    def fn():
        return memphis(t, boat_x, column, boarding, dogs_in, howl, 1.0, people, dogs)
    return key, fn


def cam_s09(c):
    if c.past("dogs_shore", -0.3) and not c.past("question", -0.3):
        k = c.p("dogs_shore", 3.0)
        return 1.0 + 0.35 * k, PCX + (520 - PCX) * k, PCY + (1040 - PCY) * k
    return 1.0 + 0.04 * min(1, c.t / 30), PCX, PCY


def black_s09(c):
    e = c.end("dogs_howl")
    if e is None:
        return 0.0
    tt = c.t - e
    if tt < 0.3:
        return 0.0
    if tt < 0.9:
        return ease((tt - 0.3) / 0.6)
    if tt < 2.6:
        return 1.0
    a = c.at("question")
    if a is not None and c.t < a:
        return 1.0 - ease((c.t - (e + 2.6)) / max(0.2, a - (e + 2.6)))
    return 0.0


# ====================================================================== s10 a craft

def books():
    ill = paper("dawn", 88)
    wash(ill, mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]]), hexc("#b89a6a"), 0.25, seed=3, bleed=10)
    for j, (x, yr, col) in enumerate([(330, "1835", "#5a2a22"), (600, "1840", "#2f3d33")]):
        m = mask_from_poly([[(x, 1120), (x + 200, 1120), (x + 200, 500), (x, 500)]])
        wash(ill, m, hexc(col), 0.9, seed=5 + j, bleed=0.5)
        ink = Ink()
        ink.line([(x, 1120), (x + 200, 1120), (x + 200, 500), (x, 500), (x, 1120)], 2)
        for yy in (560, 1060):
            ink.line([(x + 15, yy), (x + 185, yy)], 1.6)
        ink.apply(ill, INK, 0.9)
        tl_ = Image.new("RGBA", (520, 120), (0, 0, 0, 0))
        dd = ImageDraw.Draw(tl_)
        dd.text((260, 40), "DE LA DÉMOCRATIE", font=font(FONT_FR, 40), fill=(225, 200, 140, 255), anchor="mm")
        dd.text((260, 88), "EN AMÉRIQUE", font=font(FONT_FR, 40), fill=(225, 200, 140, 255), anchor="mm")
        arr = np.asarray(tl_.rotate(90, expand=True)).astype(np.float32) / 255
        y0 = 800 - arr.shape[0] // 2; x0 = x + 100 - arr.shape[1] // 2
        reg = ill[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]]
        ill[y0:y0 + arr.shape[0], x0:x0 + arr.shape[1]] = reg * (1 - arr[..., 3:4]) + arr[..., :3] * arr[..., 3:4]
        over(ill, text_items([(x + 100, 1090, ["I", "II"][j], font(FONT_FR, 34), (225, 200, 140, 255), "mm"),
                              (x + 100, 1170, yr, font(FONT_FR, 40), (46, 33, 24, 255), "mm")]))
    label(ill, PCX, 1225, "《论美国的民主》上卷、下卷", 32, bold=True)
    return ill


def sea_dawn():
    ill = S.draw_sea(t=0.0, ship_x=-5.0)
    m = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, 900), (PX0, 900)]])
    wash(ill, m, hexc("#e0b27a"), 0.35, seed=9, bleed=30)
    return ill


def final_card(lines, vign=None):
    ill = paper("dawn", 89)
    if vign is not None:
        for i, img in enumerate(vign):
            # small framed vignettes from earlier scenes
            sm = Image.fromarray((np.clip(img[PY0:PY1, PX0:PX1], 0, 1) * 255).astype(np.uint8)).resize((270, 264), Image.BILINEAR)
            a = np.asarray(sm).astype(np.float32) / 255
            x0 = PX0 + 40 + i * 305; y0 = 900
            ill[y0:y0 + 264, x0:x0 + 270] = a
            ink = Ink(); ink.line([(x0, y0), (x0 + 270, y0), (x0 + 270, y0 + 264), (x0, y0 + 264), (x0, y0)], 2); ink.apply(ill, INK, 0.9)
    big_text(ill, lines, 560 if vign is None else 520, 66)
    return ill


S10_ORDER = [(None, "sea"), ("books", "books"), ("s10_03", "alexis"), ("s10_06", "play"), ("s10_07", "road"),
             ("final1", "f1"), ("final2", "f2"), ("final3", "f3")]


def s10(c):
    cur, prev, x = c.phase(S10_ORDER)
    k = c.p("ship_leave", 8.0, smooth=False)

    def get(name):
        if name == "sea":
            ill = static("sea_dawn", sea_dawn)
            put_ship(ill, 60 + 520 * k, 0)
            return ill
        if name == "books":
            return static("books", books)
        if name == "alexis":
            return static(("s01", "alexis"), alexis)
        if name == "play":
            return playground_kids(static("playground", playground), c.tq)
        if name == "road":
            return static("road_final", lambda: S.road_dynamic(S.road_static(), fallen=1.0, gather=1.0, circled=1.0, bubble=1.0, cleared=0.0))
        if name == "f1":
            return static("f1", lambda: final_card(["自由不是一句口号，", "是一门手艺。"]))
        if name == "f2":
            return static("f2", lambda: final_card(["手艺是在修路、办学、开会", "这种小事里练出来的。"],
                                                   [static("road_final", lambda: S.road_dynamic(S.road_static(), fallen=1.0, gather=1.0, circled=1.0, bubble=1.0, cleared=0.0)),
                                                    static("playground", playground), static(("hall", 1.0, 0.0, 0), lambda: hall(1.0, 0.0, 0))]))
        if name == "f3":
            return static("f3", lambda: final_card(["什么都等别人来管，", "人就会慢慢忘了，", "怎么自己管自己。"]))
    dyn = cur in ("sea", "play") or prev in ("sea", "play")
    key = (cur, prev, q(x, 15), round(c.tq, 2) if dyn else 0)

    def fn():
        a = get(cur)
        return blend(get(prev), a, x) if prev and x < 1 else a
    return key, fn


def cam_s10(c):
    cur, _, _ = c.phase(S10_ORDER)
    if cur in ("f1", "f2", "f3"):
        return 1.0, PCX, PCY
    return 1.0 + 0.04 * min(1, c.t / 20), PCX, PCY


def black_s10(c):
    e = c.end("final3")
    if e is None:
        return 0.0
    return ease((c.t - e - 2.4) / 1.2) if c.t > e + 2.4 else 0.0


# ====================================================================== dispatch

SCENE_FN = {"s00": s00, "s01": s01, "s02": s02, "s03": s03, "s04": s04, "s05": s05, "s06": s06, "s07": s07, "s08": s08,
            "s09": s09, "s10": s10}
CAM_FN = {"s00": cam_s00, "s01": cam_s01, "s02": cam_s02, "s03": cam_s03, "s04": cam_s04, "s05": cam_s05, "s07": cam_s07,
          "s08": cam_s08, "s09": cam_s09, "s10": cam_s10}
OV_FN = {"s01": ov_s01}
BLACK_FN = {"s09": black_s09, "s10": black_s10}


def scene_illustration(sid, c):
    return SCENE_FN[sid](c)


def scene_camera(sid, c):
    f = CAM_FN.get(sid)
    if f is None:
        return 1.0 + 0.03 * min(1, c.t / 30), PCX, PCY
    return f(c)


def scene_overlay(sid, c, fr, overlay):
    f = OV_FN.get(sid)
    if f:
        f(c, fr, overlay)


def scene_black(sid, c):
    f = BLACK_FN.get(sid)
    return f(c) if f else 0.0


TEASER = "下一期 · 敬请关注"


def tail_frame(t, dur, overlay):
    fr = np.zeros((H, W, 3), np.float32)
    op = min(ease(t / 0.8), ease((dur - t) / 0.8))
    ov = overlay(("tail", TEASER), lambda cv: over(cv, text_items([(W / 2, 900, TEASER, font(FONT_CJK, 36), (215, 205, 185, 255), "mm")])))
    ov.apply(fr, op)
    return fr
