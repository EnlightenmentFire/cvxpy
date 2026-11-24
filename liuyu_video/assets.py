# -*- coding: utf-8 -*-
"""静态素材：地图几何、版画开场图层。"""
import functools
import json
import math

import cairo
import numpy as np

from engine import W, H, C, hexrgb, set_col, smooth_path

GEO = "/home/user/work/geo/region.json"

# ── 地名（经纬度，取今地近似位置） ───────────────────────
PLACES = {
    "建康": (118.78, 32.05), "京口": (119.45, 32.21), "广陵": (119.43, 32.40),
    "江乘": (118.98, 32.17), "罗落桥": (118.90, 32.10), "竹里": (119.17, 32.13),
    "覆舟山": (118.805, 32.068), "东陵": (118.83, 32.075), "石头城": (118.745, 32.06),
    "句章": (121.46, 29.97), "海盐": (120.93, 30.50), "山阴": (120.58, 30.00),
    "吴": (120.62, 31.30), "沪渎": (121.35, 31.25), "上虞": (120.87, 30.03),
    "寿春": (116.78, 32.58), "江陵": (112.19, 30.35), "寻阳": (115.99, 29.71), "历阳": (118.35, 31.70),
}
# 长江示意走向（江陵 → 建康），用于“桓玄东下”箭头
YANGTZE_PATH = [(112.19, 30.35), (112.40, 29.72), (112.90, 29.82), (113.15, 29.42), (113.90, 29.97), (114.30, 30.58),
                (115.10, 30.20), (116.00, 29.72), (116.22, 29.75), (117.05, 30.52), (117.80, 30.95), (118.38, 31.35),
                (118.50, 31.70), (118.78, 32.05)]
MODERN = {"建康": "今南京", "京口": "今镇江", "广陵": "今扬州", "句章": "今宁波", "海盐": "今海盐", "山阴": "今绍兴", "吴": "今苏州"}

LAT0 = 31.2
KX = math.cos(math.radians(LAT0))


class MapView:
    """经纬度 → 屏幕。view = (lon_c, lat_c, px_per_deg, sx, sy)"""

    def __init__(self, lon_c, lat_c, k, sx=W / 2, sy=H * 0.42):
        self.lon_c, self.lat_c, self.k, self.sx, self.sy = lon_c, lat_c, k, sx, sy

    def __call__(self, lon, lat):
        return (self.sx + (lon - self.lon_c) * KX * self.k, self.sy - (lat - self.lat_c) * self.k)

    @staticmethod
    def blend(a, b, x):
        lk = math.log(a.k) + (math.log(b.k) - math.log(a.k)) * x
        return MapView(a.lon_c + (b.lon_c - a.lon_c) * x, a.lat_c + (b.lat_c - a.lat_c) * x, math.exp(lk),
                       a.sx + (b.sx - a.sx) * x, a.sy + (b.sy - a.sy) * x)

    def place(self, name):
        return self(*PLACES[name])


@functools.lru_cache(maxsize=1)
def geo():
    d = json.load(open(GEO))
    out = {}
    for key, items in d.items():
        polys = []
        for name, g in items:
            t = g["type"]
            if t == "Polygon":
                polys.append((name, "poly", [g["coordinates"]]))
            elif t == "MultiPolygon":
                polys.append((name, "poly", g["coordinates"]))
            elif t == "LineString":
                polys.append((name, "line", [g["coordinates"]]))
            elif t == "MultiLineString":
                polys.append((name, "line", g["coordinates"]))
        out[key] = polys
    return out


def _poly_path(ctx, view, rings):
    for ring in rings:
        for i, (lon, lat) in enumerate(ring):
            x, y = view(lon, lat)
            if i == 0:
                ctx.move_to(x, y)
            else:
                ctx.line_to(x, y)
        ctx.close_path()


def draw_map(ctx, view, alpha=1.0, hatch=True, river_alpha=1.0, show_coast=True):
    g = geo()
    # 海
    set_col(ctx, C["water"], alpha)
    ctx.rectangle(0, 0, W, H); ctx.fill()
    # 海面横线（版画水纹）
    if hatch:
        ctx.set_line_width(1.0)
        set_col(ctx, "#2a3a48", 0.35 * alpha)
        for yy in range(0, H, 9):
            ctx.move_to(0, yy); ctx.line_to(W, yy)
        ctx.stroke()
    # 陆地
    ctx.save()
    for name, kind, parts in g["ne_10m_land"]:
        for rings in parts:
            _poly_path(ctx, view, rings)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    set_col(ctx, C["land"], alpha)
    ctx.fill_preserve()
    ctx.clip()
    if hatch:
        # 陆地斜纹
        set_col(ctx, "#3a3024", 0.55 * alpha)
        ctx.set_line_width(1.1)
        for k in range(-H, W + H, 14):
            ctx.move_to(k, 0); ctx.line_to(k + H * 0.35, H)
        ctx.stroke()
    ctx.restore()
    # 湖
    for name, kind, parts in g["ne_10m_lakes"]:
        for rings in parts:
            _poly_path(ctx, view, rings)
    set_col(ctx, C["water"], alpha); ctx.fill()
    # 海岸线
    if show_coast:
        ctx.set_line_width(1.6)
        set_col(ctx, "#8a7a62", 0.55 * alpha)
        for name, kind, parts in g["ne_10m_coastline"]:
            for line_ in parts:
                for i, (lon, lat) in enumerate(line_):
                    x, y = view(lon, lat)
                    (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.stroke()
    # 河流：长江画粗
    for name, kind, parts in g["ne_10m_rivers_lake_centerlines"]:
        big = name in ("Yangtze", "Chang Jiang")
        if not big and name not in ("Fuchun", "Han", "Huai", "Gan", "Qiantang"):
            continue
        wid = max(2.0, min(16.0, view.k / 90)) if big else max(1.0, min(4.0, view.k / 500))
        for line_ in parts:
            pts = [view(lon, lat) for lon, lat in line_]
            ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            set_col(ctx, C["water"], alpha * river_alpha)
            ctx.set_line_width(wid + 3)
            for i, (x, y) in enumerate(pts):
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            ctx.stroke()
            set_col(ctx, C["river"], 0.9 * alpha * river_alpha)
            ctx.set_line_width(wid * 0.55)
            for i, (x, y) in enumerate(pts):
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            ctx.stroke()


# ── 版画开场：分层生成 ────────────────────────────────────
PAPER = "#dccaa6"
INK = "#120d0a"


def _rng(seed):
    return np.random.default_rng(seed)


def _surface(w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(s)
    c.set_antialias(cairo.ANTIALIAS_BEST)
    return s, c


HORIZON = 820


@functools.lru_cache(maxsize=4)
def woodcut_layers(mood="dawn", figure=True):
    """返回 dict(sky, far, river, near)：各为全幅 ARGB 图层。mood: dawn / dusk"""
    rng = _rng(11 if mood == "dawn" else 23)
    warm = "#e0a35e" if mood == "dawn" else "#d0743f"
    layers = {}

    # 天空：底色 + 横向刻线（越近地平线越密越亮）+ 太阳
    s, c = _surface()
    set_col(c, "#17110c"); c.paint()
    sun_x, sun_y, sun_r = 300, HORIZON - 70, 120
    # 太阳光晕：同心细圈
    for i in range(18):
        r = sun_r + 14 + i * 16
        set_col(c, warm, 0.16 * (1 - i / 18))
        c.set_line_width(2.0)
        c.arc(sun_x, sun_y, r, 0, 2 * math.pi); c.stroke()
    set_col(c, warm, 0.95)
    c.arc(sun_x, sun_y, sun_r, 0, 2 * math.pi); c.fill()
    y = HORIZON
    k = 0
    while y > 60:
        gap = 5 + (HORIZON - y) * 0.028
        bright = max(0.0, 1 - (HORIZON - y) / 760)
        c.set_line_width(1.6 + bright * 1.6)
        pts = []
        amp = rng.uniform(0.5, 2.5)
        ph = rng.uniform(0, 6.28)
        x0 = rng.uniform(-40, 40)
        for x in range(-20, W + 40, 24):
            pts.append((x + x0, y + math.sin(x / 140 + ph) * amp))
        # 刻线断续
        segs = []
        cur = []
        for p in pts:
            if rng.random() < 0.035:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append(p)
        if len(cur) > 1:
            segs.append(cur)
        # 太阳处刻线变成暗色（像刻在亮面上）
        for seg in segs:
            set_col(c, PAPER, 0.10 + 0.42 * bright)
            c.move_to(*seg[0])
            for p in seg[1:]:
                c.line_to(*p)
            c.stroke()
        y -= gap
        k += 1
    # 太阳上压几道暗刻线
    c.save(); c.arc(sun_x, sun_y, sun_r, 0, 2 * math.pi); c.clip()
    for yy in range(int(sun_y - sun_r), int(sun_y + sun_r), 13):
        set_col(c, "#5a2e17", 0.55); c.set_line_width(3)
        c.move_to(sun_x - sun_r, yy); c.line_to(sun_x + sun_r, yy); c.stroke()
    c.restore()
    layers["sky"] = s

    # 远岸：低山剪影
    s, c = _surface()
    base = HORIZON
    xs = np.arange(-40, W + 60, 20)
    hts = np.zeros_like(xs, dtype=float)
    for f, a in ((1 / 420, 70), (1 / 160, 26), (1 / 60, 8)):
        hts += a * np.sin(xs * f * 2 * math.pi + rng.uniform(0, 6.28))
    hts = 40 + (hts - hts.min()) * 0.9
    hts[xs < 220] *= 0.4
    pts = [(x, base - h) for x, h in zip(xs, hts)]
    pts = smooth_path(pts, 4)
    set_col(c, "#0c0907")
    c.move_to(-40, base + 30)
    for p in pts:
        c.line_to(*p)
    c.line_to(W + 60, base + 30); c.close_path(); c.fill()
    # 山脊亮线
    set_col(c, PAPER, 0.35); c.set_line_width(1.6)
    c.move_to(*pts[0])
    for p in pts[1:]:
        c.line_to(*p)
    c.stroke()
    # 山体等高刻线
    for j in range(1, 6):
        set_col(c, PAPER, 0.10); c.set_line_width(1.2)
        c.move_to(pts[0][0], pts[0][1] + j * 9)
        for p in pts[1:]:
            c.line_to(p[0], min(base + 20, p[1] + j * 9 + rng.uniform(-1, 1)))
        c.stroke()
    layers["far"] = s

    # 江面：横向波纹，太阳倒影处亮
    s, c = _surface()
    set_col(c, "#0e0b09")
    c.rectangle(0, base + 10, W, 520); c.fill()
    y = base + 16
    while y < base + 520:
        d = (y - base) / 520
        gap = 6 + d * 16
        for x0 in np.arange(-60, W, rng.uniform(60, 140)):
            L = rng.uniform(40, 180) * (1 + d)
            refl = math.exp(-((x0 + L / 2 - sun_x) / (110 + d * 160)) ** 2)
            al = 0.12 + 0.75 * refl * (1 - d * 0.6)
            if rng.random() < 0.55 or refl > 0.3:
                set_col(c, warm if refl > 0.35 else PAPER, al)
                c.set_line_width(1.4 + d * 1.6)
                c.move_to(x0, y)
                c.curve_to(x0 + L * 0.3, y - 2 - d * 2, x0 + L * 0.6, y + 2 + d * 2, x0 + L, y)
                c.stroke()
        y += gap
    layers["river"] = s

    # 近岸 + 马桩 + 人 + 芦苇
    s, c = _surface()
    gy = 1330  # 近岸地面
    # 地面
    set_col(c, "#0b0806")
    c.move_to(-20, gy + 40)
    for x in range(-20, W + 40, 40):
        c.line_to(x, gy + 18 * math.sin(x / 210) + rng.uniform(-6, 6) - (40 if 450 < x < 900 else 0))
    c.line_to(W + 40, H + 40); c.line_to(-20, H + 40); c.close_path(); c.fill_preserve()
    c.save(); c.clip()
    set_col(c, PAPER, 0.13); c.set_line_width(1.5)
    for k in range(-H, W + H, 13):
        c.move_to(k, gy - 60); c.line_to(k - 420, gy + 560)
    c.stroke()
    c.restore()
    # 马桩（木桩），立在偏右
    px, pw, ptop = 712, 74, 520
    c.save()
    c.translate(px, gy - 10)
    c.rotate(0.035)
    set_col(c, "#0a0705")
    c.move_to(-pw / 2, 0); c.line_to(-pw / 2 + 4, -(gy - 10 - ptop)); c.line_to(pw / 2 - 2, -(gy - 10 - ptop) - 6)
    c.line_to(pw / 2, 0); c.close_path(); c.fill()
    # 木纹
    for i in range(7):
        xx = -pw / 2 + 8 + i * (pw - 16) / 6
        set_col(c, PAPER, 0.22 if i % 2 else 0.12); c.set_line_width(1.6)
        c.move_to(xx, -6)
        c.curve_to(xx + rng.uniform(-4, 4), -(gy - ptop) * 0.33, xx + rng.uniform(-5, 5), -(gy - ptop) * 0.66, xx + rng.uniform(-3, 3), -(gy - 10 - ptop) + 6)
        c.stroke()
    # 桩顶
    set_col(c, PAPER, 0.5); c.set_line_width(2.2)
    c.move_to(-pw / 2 + 4, -(gy - 10 - ptop)); c.line_to(pw / 2 - 2, -(gy - 10 - ptop) - 6); c.stroke()
    # 桩侧受光
    set_col(c, warm, 0.55); c.set_line_width(2.4)
    c.move_to(-pw / 2 + 1, -10); c.line_to(-pw / 2 + 4, -(gy - 10 - ptop) + 4); c.stroke()
    c.restore()

    if not figure:
        # 空桩：绳子散落在地上
        set_col(c, "#c99a5b", 0.9); c.set_line_width(5)
        c.move_to(700, 1296); c.curve_to(640, 1312, 560, 1300, 520, 1318); c.stroke()
        c.move_to(740, 1290); c.curve_to(800, 1306, 860, 1296, 900, 1322); c.stroke()
        c.arc(720, 1300, 16, 0, 2 * math.pi); c.stroke()
    # 人：背靠木桩坐在地上，双臂反绑在桩后，膝盖朝左
    if figure:
        def arm_path(cx):  # noqa
            cx.new_path()
            cx.move_to(668, 905); cx.curve_to(700, 930, 735, 975, 760, 1030)
            cx.curve_to(772, 1058, 776, 1082, 770, 1096)  # 手腕（桩后伸出）
            cx.curve_to(760, 1104, 748, 1098, 744, 1086)
            cx.curve_to(736, 1050, 712, 1000, 680, 960)
            cx.close_path()
        # 手臂在桩后：先画手臂，再画一次桩身遮住
        set_col(c, "#070504"); arm_path(c); c.fill()
        set_col(c, warm, 0.7); c.set_line_width(2.2)
        c.move_to(760, 1030); c.curve_to(772, 1058, 776, 1082, 770, 1096); c.stroke()
        c.save(); c.translate(px, gy - 10); c.rotate(0.035)
        set_col(c, "#0a0705")
        c.rectangle(-pw / 2 + 2, -(gy - 10 - 880), pw - 4, 300); c.fill()
        for i in range(7):
            xx = -pw / 2 + 8 + i * (pw - 16) / 6
            set_col(c, PAPER, 0.22 if i % 2 else 0.12); c.set_line_width(1.6)
            c.move_to(xx, -(gy - 10 - 880)); c.line_to(xx + 1, -(gy - 10 - 1180)); c.stroke()
        set_col(c, warm, 0.55); c.set_line_width(2.4)
        c.move_to(-pw / 2 + 2, -(gy - 10 - 880)); c.line_to(-pw / 2 + 2, -(gy - 10 - 1180)); c.stroke()
        c.restore()

        def fig_path(cx):
            cx.new_path()
            cx.move_to(690, 848)                                   # 后颈
            cx.curve_to(700, 868, 708, 884, 708, 904)              # 肩背贴桩
            cx.curve_to(712, 1000, 712, 1180, 708, 1290)           # 背
            cx.curve_to(708, 1300, 700, 1306, 690, 1306)           # 臀
            cx.line_to(600, 1304)                                  # 坐地
            cx.curve_to(560, 1262, 520, 1205, 494, 1160)           # 大腿下沿
            cx.curve_to(478, 1196, 460, 1246, 448, 1296)           # 小腿后
            cx.line_to(372, 1306)                                  # 脚底
            cx.curve_to(358, 1306, 356, 1290, 372, 1282)           # 脚尖
            cx.curve_to(392, 1274, 410, 1268, 418, 1260)           # 脚背
            cx.curve_to(424, 1220, 432, 1150, 444, 1112)           # 胫骨
            cx.curve_to(452, 1088, 470, 1078, 492, 1080)           # 膝盖
            cx.curve_to(540, 1088, 580, 1108, 604, 1126)           # 大腿上沿
            cx.curve_to(598, 1078, 590, 1020, 592, 975)            # 腹
            cx.curve_to(594, 938, 604, 904, 624, 886)              # 胸
            cx.curve_to(640, 876, 646, 864, 646, 852)              # 颈前
            cx.curve_to(636, 848, 626, 842, 622, 830)              # 下巴
            cx.curve_to(618, 818, 612, 806, 610, 798)              # 嘴
            cx.curve_to(604, 792, 606, 786, 612, 782)              # 鼻
            cx.curve_to(614, 772, 616, 764, 618, 756)              # 眉
            cx.curve_to(624, 742, 638, 734, 658, 732)              # 额
            cx.curve_to(684, 730, 704, 746, 708, 772)              # 头顶
            cx.curve_to(712, 800, 704, 826, 690, 848)              # 后脑
            cx.close_path()
        set_col(c, "#070504")
        fig_path(c); c.fill()
        # 发髻与簪
        c.arc(676, 724, 20, 0, 2 * math.pi); c.fill()
        c.set_line_width(4.5); c.move_to(650, 718); c.line_to(706, 714); c.stroke()
        # 受光轮廓（太阳在左）
        set_col(c, warm, 0.9); c.set_line_width(3)
        c.move_to(658, 732); c.curve_to(638, 734, 624, 742, 618, 756); c.curve_to(616, 764, 614, 772, 612, 782)
        c.curve_to(606, 786, 604, 792, 610, 798); c.curve_to(612, 806, 618, 818, 622, 830); c.stroke()
        c.set_line_width(2.6)
        c.move_to(624, 886); c.curve_to(604, 904, 594, 938, 592, 975); c.curve_to(590, 1020, 598, 1078, 604, 1126); c.stroke()
        c.move_to(492, 1080); c.curve_to(470, 1078, 452, 1088, 444, 1112); c.curve_to(432, 1150, 424, 1220, 418, 1260); c.stroke()
        # 衣褶刻线
        set_col(c, PAPER, 0.15); c.set_line_width(1.4)
        for i in range(8):
            yy = 930 + i * 44
            c.move_to(600, yy); c.curve_to(630, yy + 10, 670, yy + 6, 704, yy + 16); c.stroke()
        for i in range(5):
            c.move_to(500 + i * 22, 1096 + i * 6); c.curve_to(540 + i * 18, 1150, 570 + i * 12, 1230, 600 + i * 6, 1296); c.stroke()
        # 绳子：缠胸腹、绕过木桩
        for k, yy in enumerate((930, 985, 1040)):
            set_col(c, "#c99a5b", 0.95); c.set_line_width(5.5)
            c.move_to(592, yy + 4); c.curve_to(640, yy + 22, 712, yy + 22, 758, yy + 6); c.stroke()
            set_col(c, "#6b4a26", 0.9); c.set_line_width(2)
            for j in range(9):
                xx = 598 + j * 18
                c.move_to(xx, yy + 5 + j * 1.5); c.line_to(xx + 7, yy + 15 + j * 1.1); c.stroke()
        # 腕上绳结
        set_col(c, "#c99a5b", 0.95); c.set_line_width(5)
        c.arc(766, 1080, 13, 0, 2 * math.pi); c.stroke()
        c.move_to(770, 1092); c.curve_to(782, 1150, 772, 1230, 800, 1306); c.stroke()
    layers["near"] = s
    s, c = _surface()
    # 芦苇（左前景）
    for i in range(60):
        x0 = rng.uniform(-30, 300) if i < 48 else rng.uniform(880, 1110)
        h0 = rng.uniform(260, 620)
        bend = rng.uniform(-90, 40)
        y0 = gy + rng.uniform(20, 140)
        set_col(c, "#0a0806"); c.set_line_width(rng.uniform(2.5, 5))
        c.move_to(x0, y0); c.curve_to(x0 + bend * 0.2, y0 - h0 * 0.4, x0 + bend * 0.6, y0 - h0 * 0.75, x0 + bend, y0 - h0); c.stroke()
        set_col(c, PAPER, 0.18); c.set_line_width(1.0)
        c.move_to(x0 + 2, y0); c.curve_to(x0 + bend * 0.2 + 2, y0 - h0 * 0.4, x0 + bend * 0.6 + 2, y0 - h0 * 0.75, x0 + bend + 2, y0 - h0); c.stroke()
        if rng.random() < 0.5:  # 穗
            set_col(c, "#0a0806")
            c.save(); c.translate(x0 + bend, y0 - h0); c.rotate(math.atan2(-h0, bend) + math.pi / 2)
            c.scale(1, 3.2); c.arc(0, 0, 7, 0, 2 * math.pi); c.restore(); c.fill()
    layers["reeds"] = s
    return layers


def draw_woodcut(ctx, t_norm, alpha=1.0, mood="dawn", push=(1.0, 1.08), focus=(700, 1000), figure=True, t_abs=0.0):
    """t_norm 0..1：镜头缓推 + 视差；t_abs：芦苇随风、江面微光"""
    L = woodcut_layers(mood, figure)
    z = push[0] + (push[1] - push[0]) * t_norm
    for name, par in (("sky", 0.25), ("far", 0.45), ("river", 0.65), ("near", 1.0), ("reeds", 1.08)):
        zz = 1 + (z - 1) * par
        ctx.save()
        ctx.translate(focus[0], focus[1]); ctx.scale(zz, zz); ctx.translate(-focus[0], -focus[1])
        ctx.translate(-(t_norm * 18) * par, 0)
        if name == "reeds":
            k = 0.018 * math.sin(t_abs * 1.15) + 0.008 * math.sin(t_abs * 2.7 + 1.0)
            ctx.transform(cairo.Matrix(1, 0, k, 1, -k * 1450, 0))
        ctx.set_source_surface(L[name], 0, 0)
        if name == "river":
            ctx.paint_with_alpha(alpha * 0.82)
            ctx.translate(6 * math.sin(t_abs * 0.9), 0)
            ctx.set_source_surface(L[name], 0, 0)
            ctx.paint_with_alpha(alpha * (0.18 + 0.12 * math.sin(t_abs * 1.7)))
        else:
            ctx.paint_with_alpha(alpha)
        ctx.restore()
