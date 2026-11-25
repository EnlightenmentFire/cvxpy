# -*- coding: utf-8 -*-
"""地图：DEM 晕渲底图（Web 墨卡托瓦片拼接）＋ Natural Earth 河流/海岸 ＋ 手绘古河道、州界（示意）。"""
import functools
import json
import math

import cairo
import numpy as np
from PIL import Image

import engine as E
from engine import W, H, C

GEO = "/tmp/claude-0/work/geo"

PLACES = {
    "郯": (118.36, 34.61), "下邳": (117.96, 34.32), "小沛": (116.93, 34.73), "彭城": (117.18, 34.27),
    "平原": (116.43, 37.17), "临淄": (118.31, 36.85), "寿春": (116.78, 32.58), "陈留": (114.47, 34.78),
    "鄄城": (115.51, 35.56), "范": (115.50, 36.05), "东阿": (116.25, 36.33), "濮阳": (115.03, 35.76),
    "琅邪": (118.35, 35.10), "盱眙": (118.53, 33.00), "淮阴": (118.98, 33.58), "广陵": (119.43, 32.39),
    "海西": (119.42, 34.10), "朐": (119.20, 34.58), "宛陵": (118.75, 30.95), "襄贲": (118.05, 34.85),
    "邺": (114.38, 36.33), "北海": (119.10, 36.70), "昌邑": (116.35, 35.10), "许": (113.85, 34.05),
    "东海": (119.0, 34.9),
}
MODERN = {"郯": "今郯城", "下邳": "今睢宁古邳", "小沛": "今沛县", "彭城": "今徐州", "平原": "今德州平原", "寿春": "今寿县",
          "临淄": "今淄博", "陈留": "今开封东南", "鄄城": "今鄄城", "盱眙": "今盱眙", "淮阴": "今淮安", "广陵": "今扬州"}

# 古河道（示意）：泗水、沂水、淮水下游（今洪泽湖、南四湖当时尚未形成）
SI = [(117.35, 35.62), (117.0, 35.58), (116.78, 35.45), (116.70, 35.12), (116.82, 34.90), (116.93, 34.73),
      (117.03, 34.50), (117.18, 34.27), (117.45, 34.20), (117.75, 34.25), (117.96, 34.32), (118.20, 34.10),
      (118.35, 33.92), (118.65, 33.72), (118.98, 33.58)]
YI = [(118.15, 36.15), (118.55, 35.80), (118.45, 35.45), (118.35, 35.10), (118.25, 34.80), (118.10, 34.55),
      (117.96, 34.32)]
HUAI_LOW = [(116.20, 32.50), (116.78, 32.62), (117.40, 32.90), (118.10, 33.00), (118.53, 33.02), (118.75, 33.35),
            (118.98, 33.58), (119.40, 33.78), (119.95, 34.0), (120.30, 34.10)]
# 州界（示意）
BORDERS = [
    [(118.6, 36.1), (118.0, 35.75), (117.55, 35.35), (117.10, 35.0), (117.05, 34.6), (117.2, 34.1),
     (117.6, 33.85), (118.0, 33.5), (118.3, 33.1), (118.6, 32.6), (118.9, 32.25)],           # 徐｜兖、豫、扬
    [(118.6, 36.1), (119.3, 36.15), (119.9, 36.0), (120.4, 35.9)],                             # 徐｜青
    [(116.2, 36.9), (117.0, 36.6), (117.8, 36.4), (118.6, 36.1)],                              # 兖｜青
    [(117.10, 35.0), (116.5, 34.8), (115.8, 34.6), (115.0, 34.4), (114.3, 34.5)],              # 兖｜豫
    [(114.3, 34.5), (114.2, 35.1), (114.35, 35.6), (115.3, 36.05), (116.2, 36.9), (116.6, 37.6), (117.6, 38.2)],  # 兖/青｜冀
    [(113.6, 32.3), (114.8, 32.45), (115.9, 32.6), (116.6, 32.85), (117.3, 33.2), (117.6, 33.85)],  # 豫｜扬
]
PROV = {"徐州": (118.75, 34.0), "兖州": (115.9, 35.55), "豫州": (115.4, 33.55), "青州": (119.4, 36.6),
        "冀州": (115.2, 37.6), "扬州": (117.2, 31.9)}


def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2


@functools.lru_cache(maxsize=4)
def plate(name):
    meta = json.load(open(f"{GEO}/assets/{name}.json"))
    img = Image.open(f"{GEO}/assets/{name}.jpg").convert("RGB")
    return img, meta


@functools.lru_cache(maxsize=1)
def geo():
    d = json.load(open(f"{GEO}/region.json"))
    out = {}
    for key, items in d.items():
        lst = []
        for name, g in items:
            t, c = g["type"], g["coordinates"]
            if t == "Polygon":
                lst.append((name, [c]))
            elif t == "MultiPolygon":
                lst.append((name, c))
            elif t == "LineString":
                lst.append((name, [[c]]))
            elif t == "MultiLineString":
                lst.append((name, [[x] for x in c]))
        out[key] = lst
    return out


class Cam:
    """lon,lat 为画面中心（落在屏幕 (sx,sy)），k = 屏幕像素 / 经度 1 度（赤道方向，墨卡托）"""

    def __init__(self, lon, lat, k, sx=W / 2, sy=H * 0.44):
        self.lon, self.lat, self.k, self.sx, self.sy = lon, lat, k, sx, sy
        self.mx, self.my = merc(lon, lat)

    def __call__(self, lon, lat):
        mx, my = merc(lon, lat)
        s = self.k * 360
        return self.sx + (mx - self.mx) * s, self.sy + (my - self.my) * s

    def p(self, name):
        return self(*PLACES[name])

    @staticmethod
    def blend(a, b, x):
        lk = math.log(a.k) + (math.log(b.k) - math.log(a.k)) * x
        return Cam(a.lon + (b.lon - a.lon) * x, a.lat + (b.lat - a.lat) * x, math.exp(lk),
                   a.sx + (b.sx - a.sx) * x, a.sy + (b.sy - a.sy) * x)


_BG = {}


def background(cam, name=None, dim=1.0):
    """返回 H×W×3 uint8 的底图（缓存相同相机）。"""
    if name is None:
        name = "xz" if cam.k > 900 else "macro"
    key = (name, round(cam.lon, 5), round(cam.lat, 5), round(cam.k, 3), round(cam.sx, 1), round(cam.sy, 1), dim)
    if key in _BG:
        return _BG[key]
    img, m = plate(name)
    s = cam.k * 360
    # 屏幕 (X,Y) → 墨卡托 → 底图像素
    # mx = cam.mx + (X - sx)/s ; px = (mx - mx0)*scale
    a = m["scale"] / s
    c0 = (cam.mx - cam.sx / s - m["mx0"]) * m["scale"]
    f0 = (cam.my - cam.sy / s - m["my0"]) * m["scale"]
    out = img.transform((W, H), Image.AFFINE, (a, 0, c0, 0, a, f0), resample=Image.BILINEAR, fillcolor=(18, 30, 38))
    arr = np.asarray(out)
    if dim != 1.0:
        arr = (arr.astype(np.float32) * dim).astype(np.uint8)
    if len(_BG) > 6:
        _BG.clear()
    _BG[key] = arr
    return arr


def paint_bg(ctx, cam, dim=1.0, name=None):
    arr = background(cam, name, dim)
    rgba = np.dstack([arr[..., 2], arr[..., 1], arr[..., 0], np.full((H, W), 255, np.uint8)])
    rgba = np.ascontiguousarray(rgba)
    surf = cairo.ImageSurface.create_for_data(memoryview(rgba), cairo.FORMAT_ARGB32, W, H, W * 4)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()
    E._KEEP["bg"] = rgba


def _path(ctx, cam, pts):
    for i, (lon, lat) in enumerate(pts):
        x, y = cam(lon, lat)
        (ctx.move_to if i == 0 else ctx.line_to)(x, y)


def draw_rivers(ctx, cam, alpha=1.0, hi=None):
    """hi: 需要高亮的古河道名集合 {'泗水','沂水'}"""
    g = geo()
    w0 = max(1.5, min(7.0, cam.k / 140))
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for name, parts in g["ne_10m_rivers_lake_centerlines"]:
        if name not in ("Huang", "Yangtze", "Chang Jiang", "Huai"):
            continue
        wid = w0 * (1.3 if name in ("Huang", "Yangtze", "Chang Jiang") else 0.8)
        for ring in parts:
            for line_ in ring:
                _path(ctx, cam, [(p[0], p[1]) for p in line_])
                E.set_col(ctx, C["river"], 0.75 * alpha); ctx.set_line_width(wid); ctx.stroke()
    for nm, pts in (("泗水", SI), ("沂水", YI), ("淮水", HUAI_LOW)):
        h = hi and nm in hi
        pp = E.smooth_path([cam(*p) for p in pts], 8)
        if h:
            E.polyline(ctx, pp, "#9cc6e6", w0 * 2.6, 0.35 * alpha)
        E.polyline(ctx, pp, "#8fb4cf" if h else C["river"], w0 * (1.6 if h else 0.9), (0.95 if h else 0.7) * alpha)


def draw_borders(ctx, cam, alpha=1.0, labels=True, hi=None):
    ctx.set_dash([10, 8])
    for b in BORDERS:
        _path(ctx, cam, b)
        E.set_col(ctx, "#e8d9b8", 0.32 * alpha); ctx.set_line_width(2.2); ctx.stroke()
    ctx.set_dash([])
    if labels:
        for nm, (lon, lat) in PROV.items():
            x, y = cam(lon, lat)
            if -100 < x < W + 100 and -100 < y < H + 100:
                big = hi and nm in hi
                E.draw_text(ctx, nm, x, y, "serif", "Bold", 64 if big else 50, "#f1e4c4" if big else "#e8d9b8",
                            alpha * (0.85 if big else 0.42), "cm", tracking=0.35, shadow=4)


def draw_coast(ctx, cam, alpha=1.0):
    g = geo()
    for name, parts in g["ne_10m_coastline"]:
        for ring in parts:
            for line_ in ring:
                _path(ctx, cam, [(p[0], p[1]) for p in line_])
                E.set_col(ctx, "#a89877", 0.35 * alpha); ctx.set_line_width(1.6); ctx.stroke()


def city(ctx, cam, name, alpha=1.0, col="#efe6d2", size=34, dot=7, side="r", label=None, modern=False, ring=None):
    x, y = cam.p(name)
    if alpha <= 0.01:
        return x, y
    if ring:
        E.circle(ctx, x, y, dot * 2.4, ring, 0.9 * alpha, stroke=True, width=3)
    E.circle(ctx, x, y, dot + 3, "#0c0a08", 0.8 * alpha)
    E.circle(ctx, x, y, dot, col, alpha)
    txt = label or name
    dx = {"r": dot + 14, "l": -dot - 14, "c": 0}[side[0]]
    dy = -dot - 26 if side == "c" else (dot + 30 if side == "cb" else 0)
    anc = {"r": "lm", "l": "rm", "c": "cb"}[side[0]]
    if side == "cb":
        anc = "ct"
    E.draw_text(ctx, txt, x + dx, y + dy, "serif", "Bold", size, col, alpha, anc, shadow=5, stroke=0)
    if modern and name in MODERN:
        yy = y + dy + (size * 0.75 if anc[1] == "m" else (size * 0.2 if anc[1] == "b" else size * 1.3))
        E.draw_text(ctx, MODERN[name], x + dx, yy, "sans", "Regular", int(size * 0.58), "#c9bda4", 0.8 * alpha,
                    anc[0] + "t", shadow=4)
    return x, y


def base(ctx, cam, t=0.0, dim=0.92, rivers=True, borders=True, hi_rivers=None, hi_prov=None, prov_labels=True):
    paint_bg(ctx, cam, dim)
    # 冷暖统一的色调罩
    E.set_col(ctx, "#140f0a", 0.18); ctx.rectangle(0, 0, W, H); ctx.fill()
    draw_coast(ctx, cam)
    if rivers:
        draw_rivers(ctx, cam, hi=hi_rivers)
    if borders:
        draw_borders(ctx, cam, labels=prov_labels, hi=hi_prov)
