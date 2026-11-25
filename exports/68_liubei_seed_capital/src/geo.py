# -*- coding: utf-8 -*-
"""Map projection + basemap view for the North China theatre (示意)."""
import json, math, functools
import numpy as np
import skia
from PIL import Image
import gfx
from gfx import paint, draw_text, font, INK, WHITE, GOLD, GOLD_L

A = "/home/user/work/proj/assets/"
META = json.load(open(A + "base8.json"))
Z = META["z"]

# 地名（近似今址，示意）
PLACES = {
    "涿縣": (115.97, 39.49), "涿郡": (115.97, 39.49), "薊": (116.38, 39.90), "中山國": (115.0, 38.52),
    "安喜": (115.10, 38.55), "洛陽": (112.45, 34.68), "鉅鹿": (115.02, 37.22), "廣宗": (115.15, 37.07),
    "鄴": (114.38, 36.32), "平原": (116.43, 37.17), "高唐": (116.23, 36.86), "下邳": (117.95, 34.32),
    "下密": (119.40, 36.80), "沛": (116.93, 34.73), "解縣": (110.85, 34.92), "令支": (118.70, 40.0),
    "臨淄": (118.30, 36.85), "南皮": (116.70, 38.04), "易京": (116.1, 39.03),
}


def lonlat_to_px(lon, lat):
    n = 256 * 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x - META["x0"] * 256, y - META["y0"] * 256


@functools.lru_cache(None)
def base_image():
    im = np.asarray(Image.open(A + "base8.png").convert("RGB")).astype(np.float32)
    # grade: lift plains a bit, warm tint
    im = im * np.array([1.08, 1.02, 0.92]) + 6
    return gfx.np_to_image(gfx.to_u8(im))


class MapView:
    """center (lon,lat) & scale (screen px per base px)."""

    def __init__(self, center, scale, cy=860):
        self.cx_px, self.cy_px = lonlat_to_px(*center)
        self.s = scale
        self.cy = cy
        self.clamp()

    def clamp(self):
        """full-screen views: keep the basemap covering the whole frame (no black edges)"""
        if self.cy != 860:
            return
        img = base_image(); bw, bh = img.width(), img.height()
        hx = gfx.W / 2 / self.s
        top, bot = self.cy / self.s, (gfx.H - self.cy) / self.s
        self.cx_px = min(max(self.cx_px, hx), bw - hx)
        self.cy_px = min(max(self.cy_px, top), bh - bot)

    @staticmethod
    def lerp(a, b, k):
        v = MapView((0, 0), 1)
        v.cx_px = a.cx_px + (b.cx_px - a.cx_px) * k
        v.cy_px = a.cy_px + (b.cy_px - a.cy_px) * k
        v.s = math.exp(math.log(a.s) + (math.log(b.s) - math.log(a.s)) * k)
        v.cy = a.cy + (b.cy - a.cy) * k
        v.clamp()
        return v

    def pt(self, lon, lat=None):
        if lat is None:
            lon, lat = PLACES[lon]
        x, y = lonlat_to_px(lon, lat)
        return (gfx.W / 2 + (x - self.cx_px) * self.s, self.cy + (y - self.cy_px) * self.s)

    def draw_base(self, c, a=1.0, dim=0.0):
        img = base_image()
        c.save()
        c.translate(gfx.W / 2, self.cy)
        c.scale(self.s, self.s)
        c.translate(-self.cx_px, -self.cy_px)
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(a)
        c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
        c.restore()
        if dim:
            c.drawRect(skia.Rect.MakeWH(gfx.W, gfx.H), paint(INK, dim))

    def label(self, c, name, a=1.0, dx=0, dy=-26, size=34, color=WHITE, dot=True, dot_col=GOLD, disp=None):
        x, y = self.pt(name)
        if dot:
            c.drawCircle(x, y, 9, paint(INK, a * 0.6, blur=4))
            c.drawCircle(x, y, 6, paint(dot_col, a))
            c.drawCircle(x, y, 6, paint(INK, a * 0.8, stroke=2))
        draw_text(c, disp or name, x + dx, y + dy, font("serif_tc", size), color, a, stroke=5, stroke_a=0.85, shadow=6)


def map_frame(c, a=1.0, note="東漢州郡示意"):
    """'示意' badge + thin frame"""
    draw_text(c, note, gfx.W - 40, 1340, font("sans_m", 24), (200, 190, 170), a * 0.85, align="r", stroke=3)


def region(c, pts_ll, view, color, a=1.0, label=None, label_ll=None, size=46, dashed=True, t=0.0):
    pts = [view.pt(lo, la) for lo, la in pts_ll]
    p = gfx.smooth_path(pts, close=True)
    c.drawPath(p, paint(color, a * 0.16))
    c.drawPath(p, paint(color, a * 0.35, blur=18))
    pp = paint(color, a * 0.9, stroke=3)
    if dashed:
        pp.setPathEffect(skia.DashPathEffect.Make([16, 10], t * 20))
    c.drawPath(p, pp)
    if label:
        x, y = view.pt(*label_ll) if label_ll else (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
        draw_text(c, label, x, y, font("serif_blk_tc", size), color, a * 0.95, stroke=6, stroke_a=0.8, shadow=8, spacing=6)


# 示意州界（粗略）
YOU = [(113.6, 41.4), (117.6, 41.6), (119.8, 40.6), (119.3, 39.4), (117.6, 38.9), (115.3, 38.9), (114.0, 39.6), (113.6, 40.6)]
JI = [(114.0, 39.4), (115.3, 38.85), (117.6, 38.85), (117.2, 37.6), (116.2, 36.6), (115.2, 35.9), (114.0, 36.0), (113.7, 37.2)]
QING = [(116.3, 37.9), (117.6, 38.3), (119.2, 37.6), (120.8, 37.2), (120.2, 36.0), (118.0, 35.6), (116.6, 36.2)]
