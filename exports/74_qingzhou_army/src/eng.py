# -*- coding: utf-8 -*-
"""画面引擎（skia）：字体、文字、地图、箭头、粒子、旗帜、火光、箭雨、卡片、字幕。"""
import math, json, functools
import numpy as np
import skia

W, H = 1080, 1920
FPS = 25

# ---------------------------------------------------------------- 颜色
def C(r, g, b, a=255):
    return skia.Color(int(r), int(g), int(b), int(a))

GOLD = (222, 180, 92)
GOLD_L = (246, 214, 140)
INK = (14, 13, 12)
CAO = (22, 20, 18)          # 玄黑
DONG = (118, 142, 166)      # 冷蓝灰
DONG_D = (70, 88, 108)
HJ = (156, 96, 42)          # 黄巾暗赭
HJ_L = (196, 128, 60)
YAN = (236, 232, 220)       # 兖州精英浅白
YUAN = (196, 164, 82)       # 袁绍土黄
RED = (196, 52, 40)
WHITE = (244, 240, 230)
PAPER = (232, 222, 200)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def eout(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ein(t):
    t = clamp(t)
    return t ** 3


def mixc(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))


def fade(t, a, d=0.4):
    """t 秒数；a 起点；返回淡入系数"""
    return ease((t - a) / d)


def win(t, a, b, d=0.4):
    """在 [a,b] 区间可见，两头各 d 秒淡入淡出"""
    return ease((t - a) / d) * ease((b - t) / d)


# ---------------------------------------------------------------- 字体
FAM = {
    "serif": ("Noto Serif CJK SC", 700), "serifB": ("Noto Serif CJK SC", 900), "serifM": ("Noto Serif CJK SC", 500),
    "tc": ("Noto Serif CJK TC", 700), "tcB": ("Noto Serif CJK TC", 900), "tcM": ("Noto Serif CJK TC", 500),
    "sans": ("Noto Sans CJK SC", 500), "sansB": ("Noto Sans CJK SC", 700), "sansH": ("Noto Sans CJK SC", 900),
}


@functools.lru_cache(None)
def tface(key):
    fam, w = FAM[key]
    return skia.Typeface(fam, skia.FontStyle(w, 5, skia.FontStyle.kUpright_Slant))


@functools.lru_cache(4096)
def font(key, size):
    f = skia.Font(tface(key), float(size))
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def tw(s, key, size):
    return font(key, size).measureText(s)


NO_START = set("，。、；：？！）」』”’》…·")


def wrap(s, key, size, maxw):
    f = font(key, size)
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if f.measureText(cur + ch) > maxw and cur:
            if ch in NO_START:
                # 标点不放行首：把它挂在行尾
                cur += ch; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def paint(col, a=1.0, stroke=None, aa=True, blur=None, blend=None):
    p = skia.Paint(AntiAlias=aa)
    if len(col) == 4:
        p.setColor(C(*col[:3], col[3] * a))
    else:
        p.setColor(C(*col, 255 * clamp(a)))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend:
        p.setBlendMode(blend)
    return p


def text(c, s, x, y, key, size, col=WHITE, a=1.0, align="c", shadow=0.7, stroke=0, stroke_col=(0, 0, 0), glow=None, spacing=0):
    """y 是基线"""
    if a <= 0.003 or not s:
        return
    f = font(key, size)
    if spacing:
        widths = [f.measureText(ch) for ch in s]
        tot = sum(widths) + spacing * (len(s) - 1)
    else:
        tot = f.measureText(s)
    x0 = x - tot / 2 if align == "c" else (x - tot if align == "r" else x)

    def draw(p, dx=0, dy=0):
        if spacing:
            xx = x0
            for ch, w_ in zip(s, widths):
                c.drawString(ch, xx + dx, y + dy, f, p); xx += w_ + spacing
        else:
            c.drawString(s, x0 + dx, y + dy, f, p)
    if glow:
        draw(paint(glow[0], a * glow[2], blur=glow[1]))
    if shadow:
        draw(paint((0, 0, 0), a * shadow, blur=max(2, size * 0.08)), 0, size * 0.04)
    if stroke:
        draw(paint(stroke_col, a, stroke=stroke))
    draw(paint(col, a))
    return tot


def text_lines(c, lines, x, y, key, size, lh=1.45, **kw):
    for i, s in enumerate(lines):
        text(c, s, x, y + i * size * lh, key, size, **kw)
    return y + len(lines) * size * lh


def rrect(c, x0, y0, x1, y1, r, p):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r), p)


# ---------------------------------------------------------------- 地图
def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2


class Cam:
    def __init__(s, lon, lat, span, ax=540, ay=820):
        s.lon, s.lat, s.span, s.ax, s.ay = lon, lat, span, ax, ay

    @property
    def S(s):
        return W / (s.span / 360)

    def p(s, lon, lat):
        mx, my = merc(lon, lat); m0 = merc(s.lon, s.lat)
        return s.ax + (mx - m0[0]) * s.S, s.ay + (my - m0[1]) * s.S

    def pp(s, ll):
        return [s.p(*q) for q in ll]

    @staticmethod
    def lerp(a, b, t):
        t = ease(t)
        sp = math.exp(math.log(a.span) * (1 - t) + math.log(b.span) * t)
        return Cam(lerp(a.lon, b.lon, t), lerp(a.lat, b.lat, t), sp, lerp(a.ax, b.ax, t), lerp(a.ay, b.ay, t))

    def pxdeg(s):
        return W / s.span


class Base:
    def __init__(s, path):
        from PIL import Image
        s.m = json.load(open(path + ".json"))
        im = Image.open(path).convert("RGBA")
        s.lv = []
        for L in range(4):
            a = np.asarray(im if L == 0 else im.resize((im.width >> L, im.height >> L), Image.LANCZOS))
            s.lv.append(skia.Image.fromarray(np.ascontiguousarray(a), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))

    def draw(s, c, cam, alpha=1.0):
        z = s.m["z"]; n = 256 * 2 ** z; k = cam.S / n; m0 = merc(cam.lon, cam.lat)
        tx = cam.ax + (s.m["x0"] * 256 / n - m0[0]) * cam.S; ty = cam.ay + (s.m["y0"] * 256 / n - m0[1]) * cam.S
        L = 0
        while L < 3 and k * 2 ** (L + 1) <= 1.0:
            L += 1
        img = s.lv[L]; kk = k * 2 ** L
        x0 = max(0.0, (0 - tx) / kk - 2); y0 = max(0.0, (0 - ty) / kk - 2)
        x1 = min(img.width(), (W - tx) / kk + 2); y1 = min(img.height(), (H - ty) / kk + 2)
        if x1 <= x0 or y1 <= y0:
            return
        p = skia.Paint(); p.setAlphaf(alpha)
        samp = skia.SamplingOptions(skia.CubicResampler.Mitchell()) if kk > 1.05 else skia.SamplingOptions(skia.FilterMode.kLinear)
        c.drawImageRect(img, skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.Rect.MakeLTRB(tx + x0 * kk, ty + y0 * kk, tx + x1 * kk, ty + y1 * kk), samp, p)


_BASES = {}


def base(z):
    if z not in _BASES:
        _BASES[z] = Base(f"/tmp/claude-0/w74/dem/base{z}.png")
    return _BASES[z]


PL = {  # 地名 -> (lon, lat)  东汉治所，示意
    "洛阳": (112.62, 34.72), "长安": (108.88, 34.30), "荥阳": (113.45, 34.84), "成皋": (113.22, 34.86), "敖仓": (113.36, 34.93),
    "孟津": (112.62, 34.88), "武关": (110.75, 33.70), "酸枣": (114.22, 35.18), "陈留": (114.55, 34.70), "河内": (113.30, 35.06),
    "邺": (114.35, 36.30), "宛": (112.53, 33.00), "阳翟": (113.47, 34.15), "濮阳": (115.03, 35.70), "东武阳": (115.55, 36.12),
    "寿张": (115.98, 35.80), "卢": (116.72, 36.42), "济北": (116.72, 36.42), "昌邑": (116.25, 35.12), "任城": (116.58, 35.40),
    "东平": (116.40, 35.95), "鄄城": (115.52, 35.56), "范": (115.48, 35.86), "东阿": (116.18, 36.27), "临淄": (118.35, 36.85),
    "许": (113.85, 34.05), "历阳": (118.35, 31.72), "丹杨": (118.75, 30.95), "龙亢": (116.95, 33.08), "谯": (115.78, 33.85),
    "蓟": (116.40, 39.90), "代": (114.60, 39.85), "黑山": (113.95, 36.15), "汴水": (113.62, 34.82), "平原": (116.43, 37.18),
}

RIVER_HE = [(110.3, 34.62), (111.2, 34.82), (112.0, 34.86), (112.62, 34.92), (113.4, 34.97), (113.95, 35.12), (114.3, 35.32),
            (114.65, 35.6), (115.1, 35.86), (115.55, 36.02), (116.2, 36.42), (116.45, 36.8), (116.65, 37.15), (117.4, 37.45), (118.4, 37.65)]
RIVER_JI = [(113.42, 34.88), (113.9, 34.98), (114.45, 35.05), (115.1, 35.2), (115.75, 35.35), (116.05, 35.6), (116.25, 35.9),
            (116.75, 36.42), (117.05, 36.68), (117.6, 37.0), (118.3, 37.3)]
RIVER_BIAN = [(113.42, 34.84), (113.85, 34.8), (114.35, 34.79), (114.9, 34.62), (115.6, 34.45), (116.4, 34.35), (117.2, 34.25)]
YAN_POLY = [(114.55, 35.78), (115.3, 36.38), (116.0, 36.62), (116.95, 36.6), (117.45, 36.05), (117.35, 35.3), (116.65, 34.92),
            (115.6, 34.52), (114.6, 34.52), (114.15, 34.98), (114.3, 35.45)]
QING_POLY = [(116.95, 36.6), (117.6, 37.5), (118.9, 37.55), (119.6, 37.0), (119.4, 36.2), (118.6, 35.8), (117.45, 36.05)]


def smooth(pts, n=8):
    """Catmull-Rom 平滑"""
    if len(pts) < 3:
        return pts
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                  + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


def path_from(pts, close=False):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def polyline_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def cut(pts, frac):
    """截取折线前 frac 部分"""
    if frac >= 1:
        return list(pts)
    L = polyline_len(pts) * max(frac, 0); out = [pts[0]]; acc = 0
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if acc + d >= L:
            t = (L - acc) / d if d else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], t), lerp(pts[i][1], pts[i + 1][1], t)))
            return out
        out.append(pts[i + 1]); acc += d
    return out


def point_at(pts, frac):
    q = cut(pts, frac)
    return q[-1]


def draw_river(c, cam, pts, width, a=1.0, col=(96, 132, 150)):
    sp = smooth(cam.pp(pts), 6)
    pa = path_from(sp)
    c.drawPath(pa, paint(col, 0.35 * a, stroke=width * 3.2, blur=width * 1.5))
    c.drawPath(pa, paint(col, 0.9 * a, stroke=width))
    c.drawPath(pa, paint((170, 200, 210), 0.5 * a, stroke=max(1, width * 0.35)))


def draw_rivers(c, cam, a=1.0, bian=0.0):
    s = cam.pxdeg() / 120
    draw_river(c, cam, RIVER_HE, 5.5 * s ** 0.5, a)
    draw_river(c, cam, RIVER_JI, 3.0 * s ** 0.5, a * 0.85)
    if bian > 0:
        draw_river(c, cam, RIVER_BIAN, 3.0 * s ** 0.5, a * bian, col=(110, 150, 170))


def region(c, cam, poly, fill, a=1.0, edge=None, dash=True, width=3):
    sp = smooth(cam.pp(poly + [poly[0]]), 6)
    pa = path_from(sp, True)
    if fill and a > 0:
        c.drawPath(pa, paint(fill[:3], a * (fill[3] if len(fill) > 3 else 0.3)))
    if edge:
        p = paint(edge[:3], (edge[3] if len(edge) > 3 else 0.9) * (a if fill else 1), stroke=width)
        if dash:
            p.setPathEffect(skia.DashPathEffect.Make([14, 9], 0))
        c.drawPath(pa, p)


def city(c, cam, name, a=1.0, size=34, col=PAPER, dx=0, dy=0, dot=True, align="c", key="serif"):
    if a <= 0:
        return
    x, y = cam.p(*PL[name])
    if dot:
        c.drawCircle(x, y, 7, paint((0, 0, 0), 0.6 * a, blur=3))
        c.drawCircle(x, y, 5.5, paint(col, a))
        c.drawCircle(x, y, 5.5, paint((0, 0, 0), a * 0.8, stroke=1.6))
    text(c, name, x + dx, y - 16 + dy, key, size, col, a, align=align, shadow=0.9, stroke=4, stroke_col=(10, 9, 8))


def vignette(c, strength=0.75):
    sh = skia.GradientShader.MakeRadial((W / 2, H * 0.46), H * 0.72, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, int(255 * strength))], [0, 0.55, 1.0])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)


def topbot_shade(c, top=0.75, bot=0.85):
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, 330)], [C(0, 0, 0, int(255 * top)), C(0, 0, 0, 0)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 330), p)
    sh = skia.GradientShader.MakeLinear([(0, 1250), (0, H)], [C(0, 0, 0, 0), C(0, 0, 0, int(255 * bot))])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeLTRB(0, 1250, W, H), p)


# ---------------------------------------------------------------- 箭头
def arrow(c, pts, prog, col=CAO, edge=GOLD, width=46, a=1.0, glow=True, head=1.0, t=0.0, dashed=False):
    """粗箭头：pts 屏幕坐标（已平滑），prog 0..1 生长；边宽 width"""
    if prog <= 0.001 or a <= 0:
        return
    sp = cut(pts, prog)
    if len(sp) < 2:
        return
    L = polyline_len(sp)
    hl = min(width * 1.6, L * 0.6) * head
    body = cut(sp, max(0.0, (L - hl * 0.8) / max(L, 1e-6)))
    tip = sp[-1]
    # 方向
    k = len(sp) - 2
    while k > 0 and math.dist(sp[k], tip) < 4:
        k -= 1
    dx, dy = tip[0] - sp[k][0], tip[1] - sp[k][1]
    dl = math.hypot(dx, dy) or 1; ux, uy = dx / dl, dy / dl; nx, ny = -uy, ux
    base_ = (tip[0] - ux * hl, tip[1] - uy * hl)
    hw = width * 1.05
    headp = skia.Path(); headp.moveTo(*tip)
    headp.lineTo(base_[0] + nx * hw, base_[1] + ny * hw)
    headp.lineTo(base_[0] + ux * hl * 0.18, base_[1] + uy * hl * 0.18)
    headp.lineTo(base_[0] - nx * hw, base_[1] - ny * hw); headp.close()
    bp = path_from(body) if len(body) > 1 else None
    if glow:
        if bp:
            c.drawPath(bp, paint(edge, 0.35 * a, stroke=width * 1.25, blur=width * 0.5))
        c.drawPath(headp, paint(edge, 0.35 * a, blur=width * 0.4))
    if bp:
        p = paint(edge, a, stroke=width * 0.62 + 6)
        p.setStrokeCap(skia.Paint.kButt_Cap)
        if dashed:
            p.setPathEffect(skia.DashPathEffect.Make([width * 0.9, width * 0.6], -t * 80))
        c.drawPath(bp, p)
        p2 = paint(col, a, stroke=width * 0.62)
        p2.setStrokeCap(skia.Paint.kButt_Cap)
        if dashed:
            p2.setPathEffect(skia.DashPathEffect.Make([width * 0.9, width * 0.6], -t * 80))
        c.drawPath(bp, p2)
        # 流动高光
        if not dashed:
            p3 = paint(edge, 0.55 * a, stroke=width * 0.14)
            p3.setPathEffect(skia.DashPathEffect.Make([width * 0.5, width * 1.4], -t * 140))
            c.drawPath(bp, p3)
    c.drawPath(headp, paint(edge, a, stroke=6))
    c.drawPath(headp, paint(col, a))


def map_arrow(c, cam, lls, prog, **kw):
    pts = smooth(cam.pp(lls), 10)
    arrow(c, pts, prog, **kw)


# ---------------------------------------------------------------- 旗帜
def flag(c, x, y, ch, col=CAO, edge=GOLD, size=1.0, a=1.0, t=0.0, tilt=0.0, txt=None):
    """立旗：x,y 为旗杆底部；tilt 弧度（倒下）"""
    if a <= 0.003:
        return
    c.save()
    c.translate(x, y); c.rotate(math.degrees(tilt))
    s = size
    pole = 130 * s
    c.drawLine(0, 0, 0, -pole, paint((40, 30, 20), a, stroke=5 * s))
    c.drawLine(0, 0, 0, -pole, paint(edge, a * 0.6, stroke=1.5 * s))
    fw, fh = 84 * s, 92 * s
    pa = skia.Path()
    n = 10
    top = []
    bot = []
    for i in range(n + 1):
        u = i / n
        wv = math.sin(t * 5 + u * 4) * 6 * s * u
        top.append((u * fw, -pole + wv))
        bot.append((u * fw, -pole + fh + wv * 1.1))
    pa.moveTo(*top[0])
    for q in top[1:]:
        pa.lineTo(*q)
    for q in reversed(bot):
        pa.lineTo(*q)
    pa.close()
    c.drawPath(pa, paint((0, 0, 0), 0.5 * a, blur=6 * s))
    c.drawPath(pa, paint(col, a))
    c.drawPath(pa, paint(edge, a, stroke=3 * s))
    cx = fw * 0.5; cy = -pole + fh * 0.5 + math.sin(t * 5 + 2) * 3 * s
    tc = (20, 18, 16) if sum(col) > 500 else edge
    text(c, ch, cx, cy + 26 * s * 0.5 + 8 * s, "serifB", 52 * s, tc, a, shadow=0)
    c.restore()
    if txt:
        text(c, txt, x + 42 * size, y + 38 * size, "sansB", 28 * max(size, 0.8), WHITE, a, shadow=0.9, stroke=4, stroke_col=(0, 0, 0))


# ---------------------------------------------------------------- 粒子
class Army:
    """一团兵：屏幕坐标中心 + 形状；返回点阵"""
    def __init__(s, n, seed=1, shape="blob", w=200, h=120):
        r = np.random.default_rng(seed)
        s.n = n
        if shape == "blob":
            ang = r.uniform(0, 2 * np.pi, n); rad = np.sqrt(r.uniform(0, 1, n))
            s.ox = np.cos(ang) * rad * w / 2; s.oy = np.sin(ang) * rad * h / 2
        elif shape == "rect":
            cols = int(math.sqrt(n * w / h)) or 1; rows = int(math.ceil(n / cols))
            i = np.arange(n); s.ox = (i % cols / max(cols - 1, 1) - 0.5) * w; s.oy = (i // cols / max(rows - 1, 1) - 0.5) * h
        s.jx = r.normal(0, 1, n); s.jy = r.normal(0, 1, n); s.ph = r.uniform(0, 2 * np.pi, n); s.r = r.uniform(0, 1, n)

    def pts(s, cx, cy, t=0, jit=2.0, scale=1.0, march=(0, 0)):
        x = cx + s.ox * scale + np.sin(t * 3 + s.ph) * jit + s.jx * 0.5
        y = cy + s.oy * scale + np.cos(t * 2.6 + s.ph) * jit + s.jy * 0.5
        return x, y


def draw_pts(c, x, y, col, a=1.0, size=3.0, glow=False):
    if a <= 0.003 or len(x) == 0:
        return
    pts = [skia.Point(float(px), float(py)) for px, py in zip(x, y)]
    if col == GOLD and not glow:
        # 金色层一律做成柔光（避免空心圈）
        c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(col, a, stroke=size * 1.2, blur=size * 0.5))
        return
    if glow:
        c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(col, a * 0.35, stroke=size * 3.2, blur=size * 1.6))
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(col, a, stroke=size))


def draw_pts_multi(c, x, y, cols, a, size=3.0, nb=6):
    """按颜色分桶画点（cols: Nx3 float）"""
    if len(x) == 0:
        return
    key = np.clip((cols[:, 0] / 255 * nb).astype(int), 0, nb - 1) * 100 + np.clip((cols[:, 2] / 255 * nb).astype(int), 0, nb - 1)
    for k in np.unique(key):
        m = key == k
        col = cols[m].mean(0)
        draw_pts(c, x[m], y[m], tuple(col), a, size)


# ---------------------------------------------------------------- 火、烟、箭雨
def fire_glow(c, x, y, r, t, a=1.0, seed=0):
    fl = 0.75 + 0.25 * math.sin(t * 9 + seed) * math.sin(t * 5.3 + seed * 2)
    sh = skia.GradientShader.MakeRadial((x, y), r * (0.9 + 0.1 * fl), [C(255, 170, 70, int(200 * a * fl)), C(220, 90, 30, int(110 * a)), C(120, 30, 10, 0)], [0, 0.35, 1])
    p = skia.Paint(); p.setShader(sh); p.setBlendMode(skia.BlendMode.kScreen)
    c.drawCircle(x, y, r, p)


def embers(c, x, y, w, t, a=1.0, n=40, seed=0, rise=180):
    r = np.random.default_rng(seed)
    ox = r.uniform(-w / 2, w / 2, n); sp = r.uniform(0.4, 1.0, n); ph = r.uniform(0, 1, n)
    u = (t * 0.25 * sp + ph) % 1.0
    px = x + ox + np.sin(u * 8 + ph * 6) * 14
    py = y - u * rise * (1 + sp)
    al = (1 - u) * a
    for i in range(n):
        c.drawCircle(float(px[i]), float(py[i]), 2.2 * sp[i] + 0.6, paint((255, 190, 90), al[i]))


def smoke(c, x, y, w, t, a=1.0, n=10, seed=0, col=(30, 26, 24)):
    r = np.random.default_rng(seed)
    for i in range(n):
        ph = r.uniform(0, 1); sp = r.uniform(0.3, 1)
        u = (t * 0.05 * sp + ph) % 1
        cx = x + r.uniform(-w / 2, w / 2) + u * 120
        cy = y - u * 220
        rad = 60 + u * 160
        c.drawCircle(cx, cy, rad, paint(col, a * 0.35 * math.sin(u * math.pi), blur=rad * 0.6))


def arrow_rain(c, t, a=1.0, n=70, seed=5, ang=-0.55, area=(0, 0, W, 1300), speed=1400, length=70, col=(220, 200, 160)):
    if a <= 0:
        return
    r = np.random.default_rng(seed)
    x0, y0, x1, y1 = area
    ph = r.uniform(0, 1, n); xs = r.uniform(x0 - 300, x1 + 300, n); sp = r.uniform(0.8, 1.2, n)
    dx, dy = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
    span = (y1 - y0) + 400
    for i in range(n):
        u = (t * speed * sp[i] / span + ph[i]) % 1
        d = u * span
        px = xs[i] - dy * 0 + (d * math.tan(-ang)) * 0.6
        py = y0 - 200 + d
        c.drawLine(px, py, px - length * 0.55, py - length, paint(col, a * 0.75, stroke=2.2))
        c.drawLine(px, py, px - 6, py - 10, paint((240, 230, 200), a, stroke=3))


def flash(c, a, col=(255, 240, 210)):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(col, a, blend=skia.BlendMode.kScreen))


def stamp(c, ch, x, y, size, a, t, col=RED):
    """印章式大字：从大到小砸下"""
    if a <= 0:
        return
    k = 1 + 1.2 * (1 - eout(t / 0.35))
    c.save(); c.translate(x, y); c.scale(k, k); c.rotate(-8)
    s = size
    rrect(c, -s * 0.62, -s * 0.62, s * 0.62, s * 0.62, s * 0.08, paint(col, a * 0.9, stroke=s * 0.06))
    text(c, ch, 0, s * 0.36, "serifB", s * 0.95, col, a * 0.95, shadow=0)
    c.restore()


# ---------------------------------------------------------------- 卡片
TIER = {1: ("《三国志》正文", (222, 180, 92)), 2: ("裴注引书", (150, 190, 186)), 5: ("《三国演义》", (190, 120, 110)), 0: ("分析", (180, 180, 180))}


def quote_card(c, card, a, y=1080, tt=0.0):
    """古文卡：深色半透明底 + 金描边 + 繁体原文 + 出处 + 白话"""
    if a <= 0.003:
        return 0
    x0, x1 = 70, W - 70
    yuan = card["yuan"]
    size = 54 if len(yuan) <= 16 else 48 if len(yuan) <= 30 else 42
    lines = wrap(yuan, "tc", size, x1 - x0 - 100)
    bl = wrap(card["bai"], "sans", 34, x1 - x0 - 100)
    hgt = 70 + len(lines) * size * 1.5 + 40 + 44 + len(bl) * 34 * 1.45 + 30
    y0 = y - hgt
    dy = (1 - eout(clamp(tt / 0.5))) * 30
    y0 += dy
    p = paint((10, 10, 12), 0.80 * a)
    rrect(c, x0, y0, x1, y0 + hgt, 18, paint((0, 0, 0), 0.5 * a, blur=18))
    rrect(c, x0, y0, x1, y0 + hgt, 18, p)
    tlab, tcol = TIER[card.get("tier", 1)]
    rrect(c, x0 + 6, y0 + 6, x1 - 6, y0 + hgt - 6, 14, paint(tcol, 0.85 * a, stroke=2.2))
    # 层级角标
    tag_w = tw(tlab, "sansB", 24) + 28
    rrect(c, x0 + 34, y0 - 18, x0 + 34 + tag_w, y0 + 18, 8, paint((16, 14, 12), a))
    rrect(c, x0 + 34, y0 - 18, x0 + 34 + tag_w, y0 + 18, 8, paint(tcol, a, stroke=2))
    text(c, tlab, x0 + 34 + tag_w / 2, y0 + 9, "sansB", 24, tcol, a, shadow=0)
    yy = y0 + 62 + size * 0.75
    # 逐行显现
    for i, s in enumerate(lines):
        la = a * ease((tt - 0.15 - i * 0.18) / 0.45)
        text(c, s, W / 2, yy, "tc", size, GOLD_L, la, shadow=0.6, glow=(GOLD, 10, 0.25))
        yy += size * 1.5
    yy += 4
    text(c, card["src"], x1 - 46, yy, "tcM", 28, tcol, a, align="r", shadow=0)
    yy += 26
    c.drawLine(x0 + 46, yy, x1 - 46, yy, paint(tcol, 0.35 * a, stroke=1.5))
    yy += 34 + 12
    ba = a * ease((tt - 0.5) / 0.5)
    for s in bl:
        text(c, s, W / 2, yy, "sans", 34, (225, 220, 210), ba, shadow=0)
        yy += 34 * 1.45
    return hgt


def analogy_card(c, card, a, y=1100, tt=0.0, bias_a=None):
    if a <= 0.003:
        return
    x0, x1 = 64, W - 64
    bl = wrap(card["body"], "sansB", 40, x1 - x0 - 90)
    bs = wrap(card["bias"], "sans", 33, x1 - x0 - 90)
    h1 = 84 + len(bl) * 40 * 1.45 + 26
    h2 = 74 + len(bs) * 33 * 1.45 + 22
    hgt = h1 + h2
    y0 = y - hgt + (1 - eout(clamp(tt / 0.5))) * 30
    rrect(c, x0, y0, x1, y0 + hgt, 18, paint((0, 0, 0), 0.5 * a, blur=18))
    rrect(c, x0, y0, x1, y0 + h1, 18, paint((18, 26, 34), 0.9 * a))
    rrect(c, x0, y0, x1, y0 + h1, 18, paint((120, 170, 200), 0.8 * a, stroke=2.2))
    # 标签
    lab = "现代类比"
    lw = tw(lab, "sansB", 28) + 32
    rrect(c, x0 + 32, y0 + 24, x0 + 32 + lw, y0 + 66, 21, paint((120, 170, 200), a))
    text(c, lab, x0 + 32 + lw / 2, y0 + 56, "sansB", 28, (12, 20, 28), a, shadow=0)
    yy = y0 + 84 + 40 * 0.95
    for s in bl:
        text(c, s, x0 + 46, yy, "sansB", 40, (236, 240, 244), a, align="l", shadow=0)
        yy += 40 * 1.45
    ba = a if bias_a is None else a * bias_a
    yb = y0 + h1 + 10
    rrect(c, x0, yb, x1, yb + h2 - 10, 16, paint((34, 16, 14), 0.9 * ba))
    rrect(c, x0, yb, x1, yb + h2 - 10, 16, paint((200, 90, 70), 0.85 * ba, stroke=2))
    lab2 = "类比偏差"
    lw2 = tw(lab2, "sansB", 26) + 30
    rrect(c, x0 + 32, yb + 18, x0 + 32 + lw2, yb + 56, 19, paint((200, 90, 70), ba, stroke=2.2))
    text(c, lab2, x0 + 32 + lw2 / 2, yb + 47, "sansB", 26, (230, 130, 110), ba, shadow=0)
    yy = yb + 74 + 33 * 0.9
    for s in bs:
        text(c, s, x0 + 46, yy, "sans", 33, (236, 220, 214), ba, align="l", shadow=0)
        yy += 33 * 1.45


def duizhao_card(c, rows, a, y=1150, tt=0.0):
    x0, x1 = 64, W - 64
    blocks = []
    for lab, body, src in rows:
        bl = wrap(body, "serif", 38, x1 - x0 - 230)
        blocks.append((lab, bl, src, 50 + len(bl) * 38 * 1.5 + 40))
    hgt = sum(b[3] for b in blocks) + 30
    y0 = y - hgt
    rrect(c, x0, y0, x1, y0 + hgt, 18, paint((10, 10, 12), 0.82 * a))
    rrect(c, x0, y0, x1, y0 + hgt, 18, paint(GOLD, 0.7 * a, stroke=2))
    yy = y0 + 20
    for i, (lab, bl, src, h) in enumerate(blocks):
        ra = a * ease((tt - i * 0.9) / 0.5)
        col = (200, 130, 120) if i == 0 else GOLD_L
        text(c, lab, x0 + 40, yy + 58, "serifB", 42, col, ra, align="l", shadow=0)
        y2 = yy + 58
        for s in bl:
            text(c, s, x0 + 180, y2, "serif", 38, (236, 230, 216), ra, align="l", shadow=0)
            y2 += 38 * 1.5
        text(c, src, x1 - 40, y2 - 6, "sans", 24, (170, 160, 140), ra, align="r", shadow=0)
        yy += h
        if i == 0:
            c.drawLine(x0 + 40, yy - 6, x1 - 40, yy - 6, paint(GOLD, 0.3 * a, stroke=1.5))


def chip(c, s, x, y, a, col=GOLD, size=30, fill=(12, 11, 10), align="l"):
    w_ = tw(s, "sansB", size) + size * 1.1
    x0 = x if align == "l" else x - w_ / 2
    rrect(c, x0, y - size * 0.95, x0 + w_, y + size * 0.45, size * 0.6, paint(fill, 0.85 * a))
    rrect(c, x0, y - size * 0.95, x0 + w_, y + size * 0.45, size * 0.6, paint(col, a, stroke=2))
    text(c, s, x0 + w_ / 2, y + size * 0.06, "sansB", size, col, a, shadow=0)
    return w_


# ---------------------------------------------------------------- 字幕与角标
def subtitle(c, s, a):
    if a <= 0.003 or not s:
        return
    lines = wrap(s, "sansB", 50, W - 140)
    y = 1585 - (len(lines) - 1) * 50 * 1.32
    for ln in lines:
        text(c, ln, W / 2, y, "sansB", 50, (255, 255, 255), a, shadow=0.85, stroke=7, stroke_col=(8, 8, 8))
        y += 50 * 1.32


def corner(c, section, map_on=0.0):
    text(c, "乱世起家录｜曹操篇", 46, 92, "sansB", 30, (230, 210, 160), 0.85, align="l", shadow=0.9)
    if section:
        text(c, section, 46, 136, "sans", 26, (210, 200, 180), 0.75, align="l", shadow=0.9)
    rrect(c, W - 168, 64, W - 42, 102, 10, paint((0, 0, 0), 0.45))
    text(c, "AI 配音", W - 105, 93, "sans", 24, (230, 230, 230), 0.85, shadow=0)
    if map_on > 0.01:
        text(c, "地图示意", W - 46, 1290, "sans", 24, (220, 210, 190), 0.7 * map_on, align="r", shadow=0.9)


def grain(c, t, a=0.05):
    r = np.random.default_rng(int(t * FPS) % 97)
    xs = r.uniform(0, W, 500); ys = r.uniform(0, H, 500)
    pts = [skia.Point(float(x), float(y)) for x, y in zip(xs, ys)]
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint((255, 255, 255), a, stroke=1.5))
