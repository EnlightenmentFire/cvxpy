# -*- coding: utf-8 -*-
"""图元：字体、文字排版、卡片、字幕、颜色、缓动、粒子、地图镜头。全部用 skia 绘制。"""
import math, json, os
import numpy as np
import skia

W, H = 1080, 1920
FPS = 25
WORK = os.environ.get("WORK", "/tmp/claude-0/work")

# ───────── 颜色（系列规定） ─────────
RED = (200, 44, 36)        # 刘备朱红
RED_HI = (236, 84, 62)
BLACK = (22, 20, 20)       # 曹操玄黑
GOLD = (214, 176, 98)      # 描金
GOLD_HI = (246, 214, 140)
BLUE = (88, 140, 196)      # 吕布冷蓝
BLUE_HI = (140, 188, 236)
YELLOW = (196, 156, 72)    # 袁绍土黄
GREEN = (120, 160, 120)    # 刘表浅绿
GREY = (130, 134, 140)
PAPER = (236, 226, 204)
WHITE = (246, 244, 238)


def col(c, a=1.0):
    return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, max(0.0, min(1.0, a)))


def paint(c, a=1.0, stroke=None, aa=True, cap=None, blur=None):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(col(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ───────── 缓动 ─────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x); return x ** 3


def ramp(t, t0, dur):
    return ease((t - t0) / dur) if dur > 0 else float(t >= t0)


def lerp(a, b, t):
    return a + (b - a) * t


def fade_win(t, t0, t1, fi=0.4, fo=0.4):
    """t0..t1 窗口内为 1，两端淡入淡出。"""
    return ease((t - t0) / fi) * ease((t1 - t) / fo)


# ───────── 字体 ─────────
_TF = {}


def tf(name="sans", bold=False):
    key = (name, bold)
    if key not in _TF:
        fam = {"sans": "Noto Sans CJK SC", "serif": "Noto Serif CJK SC", "tc": "Noto Serif CJK TC"}[name]
        st = skia.FontStyle.Bold() if bold else skia.FontStyle.Normal()
        if name == "sans" and bold == "black":
            st = skia.FontStyle(900, 5, skia.FontStyle.kUpright_Slant)
        _TF[key] = skia.Typeface.MakeFromName(fam, st)
    return _TF[key]


def font(size, name="sans", bold=False):
    f = skia.Font(tf(name, bold), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def text_w(s, size, name="sans", bold=False):
    return font(size, name, bold).measureText(s)


def draw_text(c, s, x, y, size, color=WHITE, a=1.0, name="sans", bold=False, align="left",
              stroke=0, stroke_col=(0, 0, 0), stroke_a=0.85, shadow=0, spacing=0.0):
    if a <= 0.003 or not s:
        return
    f = font(size, name, bold)
    if spacing:
        # 逐字绘制（字距）
        ws = [f.measureText(ch) for ch in s]
        tot = sum(ws) + spacing * (len(s) - 1)
        x0 = x - tot / 2 if align == "center" else x - tot if align == "right" else x
        for ch, w in zip(s, ws):
            draw_text(c, ch, x0, y, size, color, a, name, bold, "left", stroke, stroke_col, stroke_a, shadow)
            x0 += w + spacing
        return
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    blob = skia.TextBlob.MakeFromString(s, f)
    if blob is None:
        return
    if shadow:
        c.drawTextBlob(blob, x, y + shadow * 0.4, paint((0, 0, 0), 0.55 * a, blur=shadow))
    if stroke:
        p = paint(stroke_col, stroke_a * a, stroke=stroke)
        c.drawTextBlob(blob, x, y, p)
    c.drawTextBlob(blob, x, y, paint(color, a))


NOSTART = set("，。、；：？！」』”）》〉,.;:?!）")


def wrap(s, size, maxw, name="sans", bold=False):
    """按字宽折行；标点不放行首。支持 \\n 强制换行。"""
    out = []
    for para in s.split("\n"):
        f = font(size, name, bold)
        line = ""
        for ch in para:
            if f.measureText(line + ch) > maxw and line:
                if ch in NOSTART:
                    # 把标点挂在本行尾
                    line += ch; out.append(line); line = ""; continue
                out.append(line); line = ch
            else:
                line += ch
        if line:
            out.append(line)
    return out


def rrect(c, x, y, w, h, r, p):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)


# ───────── 背景纹理（预渲染） ─────────
_CACHE = {}


def noise_img(w, h, seed=1, scale=1.0, alpha=0.08):
    key = ("noise", w, h, seed, scale, alpha)
    if key not in _CACHE:
        from scipy import ndimage as ndi
        rng = np.random.default_rng(seed)
        n = ndi.gaussian_filter(rng.normal(0, 1, (h, w)), 1.0 * scale) + rng.normal(0, 0.6, (h, w))
        n = (n - n.min()) / (n.max() - n.min())
        a = np.zeros((h, w, 4), np.uint8)
        v = (n * 255).astype(np.uint8)
        a[..., 0] = v; a[..., 1] = v; a[..., 2] = v; a[..., 3] = int(255 * alpha)
        a[..., :3] = (a[..., :3].astype(np.float32) * alpha).astype(np.uint8)
        _CACHE[key] = skia.Image.fromarray(a, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    return _CACHE[key]


def vignette(c, strength=0.75, inner=0.35):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.46), H * 0.72,
                                               [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, strength)],
                                               [0.0, inner, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def grad_rect(c, x, y, w, h, c0, a0, c1, a1, vertical=True):
    p = skia.Paint()
    pts = [skia.Point(x, y), skia.Point(x, y + h)] if vertical else [skia.Point(x, y), skia.Point(x + w, y)]
    p.setShader(skia.GradientShader.MakeLinear(pts, [col(c0, a0), col(c1, a1)]))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


# ───────── 卡片 ─────────
LAYER_TAG = {0: "经典", 1: "正史", 2: "裴注", 3: "范晔《后汉书》", 5: "演义"}
CARD_X, CARD_W = 60, 960


def quote_card_layout(card):
    tsize = 58 if len(card["text"]) <= 24 else 50 if len(card["text"]) <= 40 else 44
    lines = wrap(card["text"], tsize, CARD_W - 110, "tc", True)
    plines = wrap(card.get("plain", ""), 36, CARD_W - 110) if card.get("plain") else []
    h = 92 + len(lines) * tsize * 1.42 + 64 + (len(plines) * 50 + 30 if plines else 0) + 20
    return tsize, lines, plines, h


def draw_quote_card(c, card, y, t, a=1.0):
    """y：卡片顶部；t：卡片出现后的秒数（用于逐字显影）。"""
    if a <= 0.003:
        return 0
    tsize, lines, plines, h = quote_card_layout(card)
    x = CARD_X
    rise = (1 - ease_out(t / 0.5)) * 24
    y = y + rise
    # 底板
    rrect(c, x + 6, y + 10, CARD_W, h, 10, paint((0, 0, 0), 0.45 * a, blur=18))
    rrect(c, x, y, CARD_W, h, 10, paint((14, 11, 9), 0.86 * a))
    rrect(c, x, y, CARD_W, h, 10, paint(GOLD, 0.9 * a, stroke=2.2))
    rrect(c, x + 9, y + 9, CARD_W - 18, h - 18, 6, paint(GOLD, 0.35 * a, stroke=1))
    # 层级标签
    tag = LAYER_TAG.get(card.get("layer", 1), "")
    lay = card.get("layer", 1)
    tagc = GOLD if lay in (0, 1) else (170, 190, 210) if lay == 2 else (160, 160, 160)
    if tag:
        tw = text_w(tag, 26, "sans", True) + 28
        rrect(c, x + 40, y + 30, tw, 40, 4, paint(tagc, 0.95 * a, stroke=1.6))
        draw_text(c, tag, x + 40 + tw / 2, y + 59, 26, tagc, a, "sans", True, "center")
    # 原文（逐字显影）
    total = sum(len(l) for l in lines)
    shown = total * clamp(t / max(0.6, 0.045 * total))
    yy = y + 100 + tsize
    k = 0
    for ln in lines:
        xx = x + 55
        f = font(tsize, "tc", True)
        for ch in ln:
            ca = clamp(shown - k) * a
            if ca > 0:
                draw_text(c, ch, xx, yy, tsize, (246, 230, 190), ca, "tc", True, shadow=4)
            xx += f.measureText(ch); k += 1
        yy += tsize * 1.42
    # 出处
    yy += 4
    draw_text(c, "—— " + card["src"], x + CARD_W - 48, yy, 30, GOLD, a * ramp(t, 0.5, 0.5), "serif", False, "right")
    if plines:
        yy += 34
        c.drawLine(x + 55, yy, x + CARD_W - 55, yy, paint(GOLD, 0.35 * a, stroke=1))
        yy += 52
        pa = a * ramp(t, 0.8, 0.5)
        for ln in plines:
            draw_text(c, ln, x + 55, yy, 36, (226, 226, 222), pa, "sans")
            yy += 50
    return h


def draw_tag(c, s, x, y, color, a, size=30):
    tw = text_w(s, size, "sans", True) + 30
    rrect(c, x, y, tw, size + 20, 4, paint(color, 0.95 * a, stroke=2))
    draw_text(c, s, x + tw / 2, y + size + 4, size, color, a, "sans", True, "center")
    return tw


def draw_text_card(c, kind, text, y, t, a=1.0):
    """analogy / bias 卡。"""
    if a <= 0.003:
        return 0
    size = 50 if kind == "analogy" else 34
    lines = wrap(text, size, CARD_W - 110, "sans", kind == "analogy")
    lh = size * 1.45
    h = 110 + len(lines) * lh + 40
    x = CARD_X
    y = y + (1 - ease_out(t / 0.5)) * 24
    colr = (150, 200, 230) if kind == "analogy" else (232, 170, 90)
    rrect(c, x + 6, y + 10, CARD_W, h, 10, paint((0, 0, 0), 0.45 * a, blur=18))
    rrect(c, x, y, CARD_W, h, 10, paint((10, 14, 20) if kind == "analogy" else (20, 14, 8), 0.86 * a))
    rrect(c, x, y, CARD_W, h, 10, paint(colr, 0.7 * a, stroke=2))
    draw_tag(c, "现代类比" if kind == "analogy" else "类比偏差", x + 40, y + 30, colr, a)
    yy = y + 110 + size
    for i, ln in enumerate(lines):
        la = a * ramp(t, 0.15 + 0.12 * i, 0.4)
        draw_text(c, ln, x + 55, yy, size, WHITE, la, "sans", kind == "analogy")
        yy += lh
    return h


def draw_duibi(c, card, y, t, a=1.0):
    x = CARD_X
    y = y + (1 - ease_out(t / 0.5)) * 24
    l1 = wrap(card["yanyi"], 38, CARD_W - 100)
    l2 = wrap(card["shishu"], 40, CARD_W - 100, "sans", True)
    h1 = 40 + len(l1) * 56
    h2 = 50 + len(l2) * 60
    # 演义（淡）
    a1 = a * ramp(t, 0, 0.5)
    rrect(c, x, y, CARD_W, h1, 8, paint((20, 20, 20), 0.55 * a1))
    yy = y + 52
    for ln in l1:
        draw_text(c, ln, x + 50, yy, 38, (200, 196, 188), 0.62 * a1, "sans"); yy += 56
    # 史书（金描边）
    y2 = y + h1 + 22
    a2 = a * ramp(t, 0.9, 0.5)
    rrect(c, x, y2, CARD_W, h2, 8, paint((14, 11, 9), 0.88 * a2))
    rrect(c, x, y2, CARD_W, h2, 8, paint(GOLD, 0.95 * a2, stroke=2.4))
    yy = y2 + 62
    for ln in l2:
        draw_text(c, ln, x + 50, yy, 40, (248, 232, 196), a2, "sans", True); yy += 60
    return h1 + 22 + h2


# ───────── 字幕 ─────────
SUB_Y = 1588


def draw_subtitle(c, s, a=1.0, y=SUB_Y):
    if not s or a <= 0.01:
        return
    lines = wrap(s, 50, 940, "sans", True)
    yy = y - (len(lines) - 1) * 66
    for ln in lines:
        draw_text(c, ln, W / 2, yy, 50, WHITE, a, "sans", True, "center", stroke=7, stroke_a=0.9, shadow=8)
        yy += 66


def sub_chunks(s, maxlen=17):
    """把一句旁白切成字幕块：先按标点断，太长再按字数切。"""
    s = s.replace("“", "「").replace("”", "」")
    parts, cur = [], ""
    for ch in s:
        cur += ch
        if ch in "，。？！；：":
            parts.append(cur); cur = ""
    if cur:
        parts.append(cur)
    out, buf = [], ""
    for p in parts:
        if len(buf) + len(p) <= maxlen:
            buf += p
        else:
            if buf:
                out.append(buf)
            while len(p) > maxlen + 4:
                cut = maxlen
                out.append(p[:cut]); p = p[cut:]
            buf = p
    if buf:
        out.append(buf)
    # 去掉块末的逗号句号（字幕不显示行尾标点）
    return [o.rstrip("，。；：") for o in out]


# ───────── 地图镜头 ─────────
def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2


class Cam:
    def __init__(s, lon, lat, span, ax=540, ay=860):
        s.lon, s.lat, s.span, s.ax, s.ay = lon, lat, span, ax, ay

    @property
    def S(s):
        return W / (s.span / 360)

    def p(s, lon, lat):
        mx, my = merc(lon, lat); m0 = merc(s.lon, s.lat)
        return s.ax + (mx - m0[0]) * s.S, s.ay + (my - m0[1]) * s.S

    def px_per_deg(s):
        return W / s.span

    @staticmethod
    def lerp(a, b, t):
        sp = math.exp(math.log(a.span) * (1 - t) + math.log(b.span) * t)
        return Cam(a.lon + (b.lon - a.lon) * t, a.lat + (b.lat - a.lat) * t, sp, a.ax + (b.ax - a.ax) * t, a.ay + (b.ay - a.ay) * t)


class Base:
    def __init__(s, path):
        from PIL import Image
        s.m = json.load(open(path + ".json")); im = Image.open(path).convert("RGBA"); s.lv = []
        for L in range(4):
            a = np.asarray(im if L == 0 else im.resize((im.width >> L, im.height >> L), Image.LANCZOS))
            if a.shape[2] == 4:
                a = a.copy(); a[..., :3] = (a[..., :3].astype(np.float32) * (a[..., 3:4] / 255.0)).astype(np.uint8)
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


# ───────── 箭头、虚线、粒子 ─────────
def bezier(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def curve_pts(pts, n=60, bend=0.18):
    """两点或多点 → 平滑折线（每段二次贝塞尔，向一侧弯）。"""
    out = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        dx, dy = b[0] - a[0], b[1] - a[1]
        ctrl = (mx - dy * bend, my + dx * bend)
        for k in range(n):
            out.append(bezier(a, ctrl, b, k / n))
    out.append(pts[-1])
    return out


def poly_len(pts):
    return [0.0] + list(np.cumsum([math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]))


def poly_at(pts, cum, d):
    if d <= 0:
        return pts[0], 0.0
    if d >= cum[-1]:
        a, b = pts[-2], pts[-1]
        return pts[-1], math.atan2(b[1] - a[1], b[0] - a[0])
    i = int(np.searchsorted(cum, d)) - 1
    i = max(0, min(i, len(pts) - 2))
    f = (d - cum[i]) / max(1e-6, cum[i + 1] - cum[i])
    a, b = pts[i], pts[i + 1]
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), math.atan2(b[1] - a[1], b[0] - a[0])


def draw_arrow(c, pts, prog, color, width=34, a=1.0, head=1.0, glow=True):
    """粗大推进箭头：pts 屏幕坐标折线，prog 0..1 生长进度。"""
    if prog <= 0.001 or a <= 0.003:
        return
    cum = poly_len(pts); L = cum[-1] * prog
    hl = width * 1.7 * head
    body_end = max(0.0, L - hl * 0.6)
    path = skia.Path()
    n = max(2, int(60 * prog))
    for k in range(n + 1):
        (x, y), _ = poly_at(pts, cum, body_end * k / n)
        if k == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    if glow:
        c.drawPath(path, paint(color, 0.35 * a, stroke=width * 1.9, blur=width * 0.6))
    # 渐变：尾淡头实
    p0, _ = poly_at(pts, cum, 0); p1, ang = poly_at(pts, cum, L)
    pp = paint(color, a, stroke=width, cap=skia.Paint.kButt_Cap)
    pp.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [col(color, 0.25 * a), col(color, a)]))
    c.drawPath(path, pp)
    c.drawPath(path, paint((255, 255, 255), 0.18 * a, stroke=width * 0.25, cap=skia.Paint.kButt_Cap))
    # 箭头
    tip = p1
    hw = width * 1.25 * head
    bx, by = tip[0] - math.cos(ang) * hl, tip[1] - math.sin(ang) * hl
    nx, ny = -math.sin(ang), math.cos(ang)
    hp = skia.Path()
    hp.moveTo(*tip); hp.lineTo(bx + nx * hw, by + ny * hw); hp.lineTo(bx + nx * width * 0.5 * 0.9, by + ny * width * 0.5 * 0.9)
    hp.lineTo(bx - nx * width * 0.5 * 0.9, by - ny * width * 0.5 * 0.9); hp.lineTo(bx - nx * hw, by - ny * hw); hp.close()
    c.drawPath(hp, paint(color, a))
    c.drawPath(hp, paint((255, 255, 255), 0.35 * a, stroke=2))


def draw_dashed(c, pts, prog, color, width=7, a=1.0, dash=(22, 16), phase=0.0, glow=True):
    if prog <= 0.001 or a <= 0.003:
        return
    cum = poly_len(pts); L = cum[-1] * prog
    path = skia.Path()
    n = max(2, int(80 * prog))
    for k in range(n + 1):
        (x, y), _ = poly_at(pts, cum, L * k / n)
        path.moveTo(x, y) if k == 0 else path.lineTo(x, y)
    if glow:
        c.drawPath(path, paint(color, 0.3 * a, stroke=width * 2.6, blur=width))
    p = paint(color, a, stroke=width)
    p.setPathEffect(skia.DashPathEffect.Make(list(dash), phase))
    c.drawPath(path, p)
    return poly_at(pts, cum, L)


class Swarm:
    """兵团粒子：每个粒子在 起点散布 → 终点散布 之间移动，带抖动与拖尾。"""

    def __init__(s, n, seed, spread0=40, spread1=40):
        r = np.random.default_rng(seed)
        s.n = n
        s.o0 = r.normal(0, 1, (n, 2)) * spread0
        s.o1 = r.normal(0, 1, (n, 2)) * spread1
        s.delay = r.uniform(0, 0.35, n)
        s.ph = r.uniform(0, 6.28, n)
        s.sz = r.uniform(0.7, 1.3, n)

    def pos(s, p0, p1, prog, t, ctrl=None, jitter=3.0):
        f = np.clip((prog - s.delay) / (1 - s.delay.max() + 1e-6), 0, 1)
        f = f * f * (3 - 2 * f)
        if ctrl is None:
            bx = p0[0] + (p1[0] - p0[0]) * f; by = p0[1] + (p1[1] - p0[1]) * f
        else:
            bx = (1 - f) ** 2 * p0[0] + 2 * (1 - f) * f * ctrl[0] + f * f * p1[0]
            by = (1 - f) ** 2 * p0[1] + 2 * (1 - f) * f * ctrl[1] + f * f * p1[1]
        ox = s.o0[:, 0] * (1 - f) + s.o1[:, 0] * f
        oy = s.o0[:, 1] * (1 - f) + s.o1[:, 1] * f
        jx = np.sin(t * 3.1 + s.ph) * jitter; jy = np.cos(t * 2.7 + s.ph * 1.3) * jitter
        return np.stack([bx + ox + jx, by + oy + jy], 1), f

    @staticmethod
    def draw(c, xy, color, a=1.0, r=3.2, sz=None, glow=True):
        if a <= 0.003:
            return
        pts = [skia.Point(float(x), float(y)) for x, y in xy]
        if glow:
            pg = paint(color, 0.22 * a, stroke=r * 4.2); pg.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 1.5))
            c.drawPoints(skia.Canvas.kPoints_PointMode, pts, pg)
        c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(color, a, stroke=r * 2))
        c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint((255, 255, 255), 0.35 * a, stroke=r * 0.8))


def smoke(c, x, y, t, seed, n=10, size=60, a=0.35, color=(90, 86, 80)):
    r = np.random.default_rng(seed)
    for i in range(n):
        ph = r.uniform(0, 1); sp = r.uniform(0.15, 0.35)
        f = (t * sp + ph) % 1.0
        xx = x + r.normal(0, size * 0.6) + f * size * 0.8 * r.uniform(-1, 1)
        yy = y - f * size * 2.0 + r.normal(0, size * 0.3)
        rr = size * (0.4 + f * 0.9)
        c.drawCircle(xx, yy, rr, paint(color, a * math.sin(math.pi * f), blur=rr * 0.5))


def city(c, x, y, name, a=1.0, color=PAPER, size=40, r=9, side="right", major=False, ring=None):
    if a <= 0.003:
        return
    if ring is not None:
        c.drawCircle(x, y, r + 8 + ring * 30, paint(color, a * (1 - ring) * 0.8, stroke=3))
    if major:
        c.drawRect(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), paint((10, 10, 10), 0.8 * a))
        c.drawRect(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), paint(color, a, stroke=3))
    else:
        c.drawCircle(x, y, r, paint((10, 10, 10), 0.8 * a))
        c.drawCircle(x, y, r, paint(color, a, stroke=3))
    if name:
        if side == "right":
            draw_text(c, name, x + r + 12, y + size * 0.36, size, color, a, "serif", True, stroke=5, stroke_a=0.8)
        elif side == "left":
            draw_text(c, name, x - r - 12, y + size * 0.36, size, color, a, "serif", True, "right", stroke=5, stroke_a=0.8)
        elif side == "up":
            draw_text(c, name, x, y - r - 14, size, color, a, "serif", True, "center", stroke=5, stroke_a=0.8)
        else:
            draw_text(c, name, x, y + r + size + 6, size, color, a, "serif", True, "center", stroke=5, stroke_a=0.8)


def banner(c, x, y, s, color, a=1.0, size=40):
    """势力名牌：竖条旗。"""
    if a <= 0.003:
        return
    w = size + 26; h = len(s) * (size + 6) + 30
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2 + 4, y + 6, w, h), paint((0, 0, 0), 0.4 * a, blur=8))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, y, w, h), paint(color, 0.92 * a))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2 + 5, y + 5, w - 10, h - 10), paint(GOLD_HI, 0.7 * a, stroke=1.5))
    yy = y + 18 + size
    for ch in s:
        draw_text(c, ch, x, yy, size, (250, 244, 230), a, "serif", True, "center")
        yy += size + 6


def seal(c, x, y, s=1.0, a=1.0, glow=0.0, rot=0.0, text="左將軍"):
    """金印：俯视斜角的印台 + 印钮 + 印面朱文。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if glow > 0:
        c.drawCircle(0, 0, 150, paint(GOLD_HI, 0.45 * glow * a, blur=60))
    # 阴影
    rrect(c, -78, -60, 156, 156, 10, paint((0, 0, 0), 0.5 * a, blur=14))
    # 印台（金）
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(-80, -80), skia.Point(80, 80)],
                                               [col((255, 226, 150), a), col((196, 146, 60), a), col((120, 82, 30), a)]))
    rrect(c, -80, -80, 160, 160, 12, p)
    rrect(c, -80, -80, 160, 160, 12, paint((255, 240, 200), 0.6 * a, stroke=2))
    # 印面
    rrect(c, -62, -62, 124, 124, 6, paint((150, 28, 22), 0.95 * a))
    rrect(c, -56, -56, 112, 112, 4, paint((250, 220, 200), 0.85 * a, stroke=3))
    for k, ch in enumerate(text):
        draw_text(c, ch, 0, -22 + (k - (len(text) - 1) / 2) * 36 + 34, 34, (250, 226, 210), a, "tc", True, "center")
    c.restore()


def scroll_icon(c, x, y, s=1.0, a=1.0):
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    rrect(c, -36, -16, 72, 32, 4, paint((236, 214, 160), a))
    rrect(c, -42, -20, 10, 40, 3, paint((150, 30, 24), a))
    rrect(c, 32, -20, 10, 40, 3, paint((150, 30, 24), a))
    c.drawLine(-24, -6, 24, -6, paint((120, 90, 50), a, stroke=2)); c.drawLine(-24, 4, 18, 4, paint((120, 90, 50), a, stroke=2))
    c.restore()


def lightning(c, x0, y0, y1, seed, a=1.0, width=4):
    r = np.random.default_rng(seed)
    pts = [(x0, y0)]
    y = y0; x = x0
    while y < y1:
        y += r.uniform(30, 70); x += r.normal(0, 28); pts.append((x, y))
    path = skia.Path(); path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    c.drawPath(path, paint((200, 220, 255), 0.6 * a, stroke=width * 4, blur=width * 3))
    c.drawPath(path, paint((240, 246, 255), a, stroke=width))
    # 分叉
    for k in range(2):
        i = r.integers(1, max(2, len(pts) - 1))
        bx, by = pts[i]; bp = skia.Path(); bp.moveTo(bx, by)
        for j in range(4):
            bx += r.normal(30 * (1 if k else -1), 15); by += r.uniform(20, 50); bp.lineTo(bx, by)
        c.drawPath(bp, paint((230, 240, 255), 0.7 * a, stroke=width * 0.6))
