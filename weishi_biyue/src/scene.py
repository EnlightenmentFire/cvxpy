# -*- coding: utf-8 -*-
"""《围师必阙》竖屏短片 —— 单画面场景渲染器。

整条只有一个画面：夜色中一座方城的俯视示意图，镜头极慢推近。
所有元素都按时间参数 t（秒）计算，事件时间点来自 timeline.json（由配音时长生成）。
"""
import json
import math
import os

import numpy as np
import skia

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(HERE, "..", "fonts"))

# ---------------------------------------------------------------- palette
YELLOW = (255, 212, 0)        # 关键词亮黄 #FFD400
WHITE = (255, 255, 255)
GOLD = (255, 200, 90)         # 缺口 / 光路
EMBER = (255, 150, 60)        # 守军暖橙
XUAN = (16, 11, 12)           # 玄黑
VERMILION = (196, 48, 36)     # 朱笔

# ---------------------------------------------------------------- geometry
CX, CY = 540.0, 960.0         # 城池中心（世界坐标）
HALF = 196.0                  # 城墙半边长
GATE_W = 52.0
RING_IN, RING_ROWS, RING_STEP = 246.0, 5, 19.0
TOP_SAFE, BOT_SAFE = int(H * 0.10), int(H * 0.80)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ramp(t, t0, dur):
    return smooth((t - t0) / dur) if dur > 0 else float(t >= t0)


def col(rgb, a=1.0):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, clamp(a))


# ---------------------------------------------------------------- fonts
_tf_cache = {}


def typeface(name):
    if name not in _tf_cache:
        _tf_cache[name] = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, name))
    return _tf_cache[name]


def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


SERIF_BLACK = "NotoSerifSC-Black.ttf"
SERIF_BOLD = "NotoSerifSC-Bold.ttf"
SANS_BLACK = "NotoSansSC-Black.ttf"
SANS_BOLD = "NotoSansSC-Bold.ttf"
SANS_MED = "NotoSansSC-Medium.ttf"
BRUSH = "MaShanZheng-Regular.ttf"
KAI = "LXGWWenKaiTC-Regular.ttf"


# ---------------------------------------------------------------- rich text
def parse_rich(s):
    """'普通**高亮**普通' -> [(text, highlighted)]"""
    out, hi = [], False
    for i, part in enumerate(s.split("**")):
        if part:
            out.append((part, i % 2 == 1))
    return out


def rich_width(segs, f, tracking=0.0):
    w = 0.0
    for txt, _ in segs:
        w += f.measureText(txt) + tracking * len(txt)
    return w


def draw_rich_line(c, s, x_center, y_base, f, alpha=1.0, stroke=8.0, base=WHITE,
                   hi=YELLOW, tracking=0.0, shadow=True, hi_font=None):
    segs = parse_rich(s)
    widths = []
    for txt, h in segs:
        ff = hi_font if (h and hi_font) else f
        widths.append(ff.measureText(txt) + tracking * len(txt))
    total = sum(widths)
    x = x_center - total / 2
    for (txt, h), w in zip(segs, widths):
        ff = hi_font if (h and hi_font) else f
        draw_text(c, txt, x, y_base, ff, hi if h else base, alpha, stroke, tracking, shadow)
        x += w
    return total


def draw_text(c, txt, x, y, f, rgb, alpha=1.0, stroke=8.0, tracking=0.0, shadow=True):
    if alpha <= 0.003:
        return
    blob = make_blob(txt, x, y, f, tracking)
    if shadow:
        p = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 0.55 * alpha))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9))
        c.drawTextBlob(blob, 0, 6, p)
    if stroke > 0:
        p = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 0.92 * alpha))
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawTextBlob(blob, 0, 0, p)
    p = skia.Paint(AntiAlias=True, Color4f=col(rgb, alpha))
    c.drawTextBlob(blob, 0, 0, p)


def make_blob(txt, x, y, f, tracking=0.0):
    if tracking == 0:
        return skia.TextBlob.MakeFromString(txt, f) if False else _blob_pos(txt, x, y, f, 0.0)
    return _blob_pos(txt, x, y, f, tracking)


def _blob_pos(txt, x, y, f, tracking):
    glyphs = f.textToGlyphs(txt)
    widths = f.getWidths(glyphs)
    pos, cx = [], x
    for w in widths:
        pos.append(skia.Point(cx, y))
        cx += w + tracking
    b = skia.TextBlobBuilder()
    b.allocRunPos(f, glyphs, pos)
    return b.make()


# ---------------------------------------------------------------- background
def make_background(seed=7, scale=1.0):
    """暗调地形底：fBm 高度场 + 山体阴影 + 极淡等高线 + 月光。返回 RGBA uint8 (H, W, 4)。"""
    from PIL import Image
    rng = np.random.default_rng(seed)
    bw, bh = int(W * scale), int(H * scale)
    h = np.zeros((bh, bw), np.float32)
    amp = 1.0
    for octave in range(7):
        n = 3 * 2 ** octave
        g = rng.standard_normal((max(2, int(n * bh / bw)), n)).astype(np.float32)
        img = Image.fromarray(g).resize((bw, bh), Image.BICUBIC)
        h += amp * np.asarray(img)
        amp *= 0.55
    h = (h - h.min()) / (h.max() - h.min())
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    # 像素 → 世界坐标（背景图按 1 像素 = 1 世界单位、以城池为中心铺设）
    wx = xx - (bw - W) / 2
    wy = yy - (bh - H) / 2
    # 城址所在是一块平地：在城池周围压平地形
    r = np.sqrt((wx - CX) ** 2 + (wy - CY) ** 2)
    flat = np.clip((r - 330) / 260, 0, 1)
    h = h * (0.25 + 0.75 * flat) + 0.45 * (1 - flat) * 0.6
    gy, gx = np.gradient(h * 60)
    shade = np.clip(0.5 + (-gx * 0.7 - gy * 0.7) * 1.05, 0, 1)
    # 等高线
    k = h * 22.0
    fr = np.abs(k - np.round(k))
    contour = np.clip(1 - fr / 0.05, 0, 1) * (0.35 + 0.65 * flat) * 0.9
    # 色彩：夜色石板 → 暗橄榄
    base = np.stack([
        24 + 14 * h + 20 * (shade - 0.5),
        29 + 14 * h + 20 * (shade - 0.5),
        33 + 12 * h + 22 * (shade - 0.5),
    ], -1)
    base += contour[..., None] * np.array([10, 12, 14], np.float32)
    # 古道：四门各一条，极淡（东门那条后面会亮成光路）
    for ang, wob in ((0, 0.10), (math.pi / 2, -0.07), (math.pi, 0.08), (-math.pi / 2, 0.05)):
        d = road_distance(wx, wy, ang, wob)
        road = np.clip(1 - d / 5.0, 0, 1) * 0.55
        base += road[..., None] * np.array([12, 11, 9], np.float32)
    # 月光：画面中上部偏亮，四周压暗
    m = np.exp(-(((wx - 560) / 700) ** 2 + ((wy - 900) / 900) ** 2))
    base *= (0.60 + 0.62 * m)[..., None]
    plain = np.exp(-(((wx - CX) / 520) ** 2 + ((wy - CY) / 520) ** 2))
    base += plain[..., None] * np.array([7, 8, 8], np.float32)
    # 城内平地略亮
    inside = (np.abs(wx - CX) < HALF) & (np.abs(wy - CY) < HALF)
    base[inside] *= 1.08
    out = np.clip(base, 0, 255).astype(np.uint8)
    a = np.full((bh, bw, 1), 255, np.uint8)
    return np.concatenate([out, a], -1)


def road_path_point(s, ang, wob):
    """从城门出发的古道，s 为离城中心距离。"""
    ca, sa = math.cos(ang), math.sin(ang)
    off = wob * (max(0.0, s - HALF - 40)) ** 1.25 * 0.08
    return CX + ca * s - sa * off, CY + sa * s + ca * off


def road_distance(x, y, ang, wob):
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = x - CX, y - CY
    s = dx * ca + dy * sa
    n = -dx * sa + dy * ca
    sp = np.maximum(0.0, s - HALF - 40)
    off = wob * sp ** 1.25 * 0.08
    d = np.abs(n - off)
    d = np.where(s < HALF, 1e3, d)
    return d


# ---------------------------------------------------------------- actors
class Actors:
    def __init__(self, seed=3):
        rng = np.random.default_rng(seed)
        self.rng = rng
        # 围城兵点：沿圆角方环排布
        pts, rows = [], []
        for k in range(RING_ROWS):
            d = RING_IN + k * RING_STEP
            per = 8 * d
            n = int(per / 15.5)
            off = rng.uniform(0, 1)
            for i in range(n):
                u = (i + off + rng.uniform(-0.18, 0.18)) / n
                x, y = rounded_square(u, d, 0.22 * d)
                x += rng.normal(0, 2.0)
                y += rng.normal(0, 2.0)
                pts.append((x, y))
                rows.append(k)
        self.siege = np.array(pts, np.float32)
        self.siege_row = np.array(rows)
        self.siege_phase = rng.uniform(0, 2 * math.pi, len(pts)).astype(np.float32)
        self.siege_r = rng.uniform(4.6, 6.0, len(pts)).astype(np.float32)
        # 东侧缺口：走廊里的兵点向外撤走并淡出，两侧的兵点向旁边让一让
        rel = self.siege - np.array([CX, CY], np.float32)
        ay = np.abs(rel[:, 1])
        east = rel[:, 0] > HALF
        corridor, soft = 78.0, 175.0
        self.siege_withdraw = east & (ay < corridor)
        dirn = np.sign(rel[:, 1]); dirn[dirn == 0] = 1
        side = east & (ay >= corridor) & (ay < soft)
        push = 26.0 * np.clip(1 - (ay - corridor) / (soft - corridor), 0, 1) ** 1.5 * side
        tgt = self.siege.copy()
        tgt[:, 1] += dirn * push
        tgt[:, 0] += np.where(side, 8.0, 0.0)
        out = rng.uniform(110, 190, len(pts)).astype(np.float32)
        tgt[:, 0] += np.where(self.siege_withdraw, out, 0.0)
        tgt[:, 1] += np.where(self.siege_withdraw, dirn * rng.uniform(10, 50, len(pts)), 0.0)
        self.siege_gap_target = tgt
        self.siege_gap_delay = ((1 - ay / soft).clip(0, 1) * 0.0 + (rel[:, 0] - HALF) / 200.0 * 0.5
                                + rng.uniform(0, 0.35, len(pts))).astype(np.float32)

        # 守军光点：城内散布 → 聚向城墙 → 散开变暗
        n_def = 118
        inner = HALF - 30
        calm = rng.uniform(-inner, inner, (n_def, 2)).astype(np.float32)
        # 避开主街
        wall = []
        for i in range(n_def):
            u = rng.uniform(0, 1)
            x, y = rounded_square(u, HALF - rng.uniform(14, 34), 2)
            wall.append((x - CX, y - CY))
        wall = np.array(wall, np.float32)
        loose = calm * 0.72 + rng.normal(0, 10, (n_def, 2)).astype(np.float32)
        self.def_calm = calm
        self.def_wall = wall
        self.def_loose = loose
        self.def_phase = rng.uniform(0, 2 * math.pi, n_def).astype(np.float32)
        self.def_delay = rng.uniform(0, 0.6, n_def).astype(np.float32)
        # 越撞越密：额外的城头光点
        n_extra = 90
        extra = []
        for i in range(n_extra):
            u = rng.uniform(0, 1)
            x, y = rounded_square(u, HALF - rng.uniform(10, 26), 2)
            extra.append((x - CX, y - CY))
        self.def_extra = np.array(extra, np.float32)
        self.def_extra_t = np.sort(rng.uniform(0, 1, n_extra)).astype(np.float32)
        self.def_extra_phase = rng.uniform(0, 2 * math.pi, n_extra).astype(np.float32)


def rounded_square(u, d, rad):
    """沿半边长 d、圆角半径 rad 的圆角方形走一圈，u∈[0,1)。返回世界坐标。"""
    s = d - rad
    straight = 2 * s
    arc = math.pi * rad / 2
    per = 4 * (straight + arc)
    L = (u % 1.0) * per
    seg = straight + arc
    side = int(L // seg)
    l = L - side * seg
    if l < straight:
        lx, ly = -s + l, -d
    else:
        a = (l - straight) / rad - math.pi / 2
        lx, ly = s + rad * math.cos(a), -s + rad * math.sin(a)
    # rotate by side*90deg
    for _ in range(side):
        lx, ly = -ly, lx
    return CX + lx, CY + ly


# ---------------------------------------------------------------- drawing helpers
def glow_circle(c, x, y, r, rgb, a, blur):
    p = skia.Paint(AntiAlias=True, Color4f=col(rgb, a))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawCircle(x, y, r, p)


def draw_city(c, wall_glow=0.0, gate_flash=0.0):
    # 护城河
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=9,
                   Color4f=col((20, 34, 44), 0.9))
    c.drawRect(skia.Rect.MakeLTRB(CX - HALF - 30, CY - HALF - 30, CX + HALF + 30, CY + HALF + 30), p)
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                   Color4f=col((90, 120, 140), 0.35))
    c.drawRect(skia.Rect.MakeLTRB(CX - HALF - 34, CY - HALF - 34, CX + HALF + 34, CY + HALF + 34), p)
    # 城内街巷
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2,
                   Color4f=col((120, 120, 112), 0.16))
    for i in range(1, 8):
        v = -HALF + i * (2 * HALF / 8)
        c.drawLine(CX + v, CY - HALF + 14, CX + v, CY + HALF - 14, p)
        c.drawLine(CX - HALF + 14, CY + v, CX + HALF - 14, CY + v, p)
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=5,
                   Color4f=col((150, 146, 132), 0.20))
    c.drawLine(CX, CY - HALF, CX, CY + HALF, p)
    c.drawLine(CX - HALF, CY, CX + HALF, CY, p)
    # 城墙（四门留口）
    if wall_glow > 0:
        g = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                       Color4f=col(EMBER, 0.55 * wall_glow))
        g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
        c.drawRect(skia.Rect.MakeLTRB(CX - HALF, CY - HALF, CX + HALF, CY + HALF), g)
    wallp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=15,
                       Color4f=col((168, 160, 144), 0.92), StrokeCap=skia.Paint.kButt_Cap)
    hl = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2,
                    Color4f=col((222, 216, 200), 0.55), StrokeCap=skia.Paint.kButt_Cap)
    g2 = GATE_W / 2
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for i in range(4):
        x0, y0 = corners[i]
        x1, y1 = corners[(i + 1) % 4]
        ax, ay = CX + x0 * HALF, CY + y0 * HALF
        bx, by = CX + x1 * HALF, CY + y1 * HALF
        mx, my = (ax + bx) / 2, (ay + by) / 2
        dx, dy = (bx - ax) / (2 * HALF), (by - ay) / (2 * HALF)
        for (sx, sy, ex, ey) in ((ax, ay, mx - dx * g2, my - dy * g2), (mx + dx * g2, my + dy * g2, bx, by)):
            c.drawLine(sx, sy, ex, ey, wallp)
            c.drawLine(sx, sy, ex, ey, hl)
        # 门楼
        for sgn in (-1, 1):
            tx, ty = mx + dx * sgn * (g2 + 9), my + dy * sgn * (g2 + 9)
            r = skia.Rect.MakeXYWH(tx - 12, ty - 12, 24, 24)
            c.drawRect(r, skia.Paint(AntiAlias=True, Color4f=col((150, 142, 126), 0.95)))
            c.drawRect(r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                     Color4f=col((225, 218, 200), 0.5)))
    # 角楼
    for (sx, sy) in corners:
        r = skia.Rect.MakeXYWH(CX + sx * HALF - 16, CY + sy * HALF - 16, 32, 32)
        c.drawRect(r, skia.Paint(AntiAlias=True, Color4f=col((150, 142, 126), 0.95)))
        c.drawRect(r, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5,
                                 Color4f=col((225, 218, 200), 0.5)))
    if gate_flash > 0:
        glow_circle(c, CX + HALF, CY, 40, GOLD, 0.65 * gate_flash, 22)


def draw_arrow(c, x, y, ang, length, alpha, scale=1.0):
    """军事态势图式的进攻箭头（玄黑，冷色描边）。尖端在 (x, y)。"""
    if alpha <= 0.01:
        return
    L = length * scale
    hw = 30 * scale
    tw = 13 * scale
    ca, sa = math.cos(ang), math.sin(ang)

    def P(a, b):  # a 沿箭头方向，b 横向
        return skia.Point(x + ca * a - sa * b, y + sa * a + ca * b)

    path = skia.Path()
    path.moveTo(P(0, 0))
    path.lineTo(P(-46 * scale, hw))
    path.lineTo(P(-40 * scale, tw))
    path.lineTo(P(-L, tw * 0.55))
    path.lineTo(P(-L - 8 * scale, 0))
    path.lineTo(P(-L, -tw * 0.55))
    path.lineTo(P(-40 * scale, -tw))
    path.lineTo(P(-46 * scale, -hw))
    path.close()
    sh = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 0.5 * alpha))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8))
    c.save(); c.translate(0, 6); c.drawPath(path, sh); c.restore()
    c.drawPath(path, skia.Paint(AntiAlias=True, Color4f=col(XUAN, 0.96 * alpha)))
    c.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=2.4,
                                Color4f=col((214, 222, 232), 0.85 * alpha)))


def draw_slips(c, t, T):
    """竹简：城拔，皆坑之。浮出 → 朱笔划掉 → 淡去。"""
    t_in, t_strike, t_out = T["slips_in"], T["slips_strike"], T["slips_out"]
    if t < t_in:
        return
    a_in = ease_out((t - t_in) / 0.7)
    a_out = 1 - smooth((t - t_out) / 0.9)
    alpha = a_in * a_out
    if alpha <= 0.003:
        return
    chars = ["城", "拔", "皆", "坑", "之"]
    sw, sh, gap = 84.0, 168.0, 5.0
    extra_gap = 18.0  # 「城拔」与「皆坑之」之间的停顿
    total = 5 * sw + 4 * gap + extra_gap
    cx, cy = CX, 496.0 - 26 * (1 - a_in) - 30 * smooth((t - t_out) / 0.9)
    x0 = cx - total / 2
    c.save()
    # 整体阴影
    sp = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 0.55 * alpha))
    sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    c.drawRect(skia.Rect.MakeXYWH(x0 - 6, cy - sh / 2 + 10, total + 12, sh + 6), sp)
    f = font(BRUSH, 82)
    rng = np.random.default_rng(5)
    xs = []
    x = x0
    for i, ch in enumerate(chars):
        sway = math.sin(t * 1.3 + i * 0.9) * 1.2
        r = skia.Rect.MakeXYWH(x, cy - sh / 2 + sway, sw, sh)
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(x, 0), skia.Point(x + sw, 0)],
            [skia.Color4f(0.62, 0.48, 0.27, alpha).toColor(), skia.Color4f(0.80, 0.66, 0.40, alpha).toColor(),
             skia.Color4f(0.74, 0.59, 0.34, alpha).toColor(), skia.Color4f(0.55, 0.41, 0.22, alpha).toColor()],
            [0.0, 0.35, 0.7, 1.0])
        c.drawRoundRect(r, 6, 6, skia.Paint(AntiAlias=True, Shader=shader))
        # 竹纤维
        fp = skia.Paint(AntiAlias=True, StrokeWidth=1.0, Color4f=col((90, 62, 30), 0.25 * alpha))
        for k in range(6):
            fx = x + 8 + rng.uniform(0, sw - 16)
            c.drawLine(fx, r.top() + 6, fx + rng.uniform(-1, 1), r.bottom() - 6, fp)
        c.drawRoundRect(r, 6, 6, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                                            Color4f=col((60, 40, 18), 0.7 * alpha)))
        # 墨字
        w = f.measureText(ch)
        tp = skia.Paint(AntiAlias=True, Color4f=col((34, 20, 10), 0.95 * alpha))
        c.drawTextBlob(_blob_pos(ch, x + sw / 2 - w / 2, cy + 28 + sway, f, 0), 0, 0, tp)
        xs.append(x)
        x += sw + gap + (extra_gap if i == 1 else 0)
    # 编绳
    cp = skia.Paint(AntiAlias=True, StrokeWidth=3.2, Color4f=col((52, 34, 18), 0.85 * alpha))
    for yy in (cy - sh * 0.34, cy + sh * 0.36):
        c.drawLine(x0 - 10, yy, x0 + total + 10, yy, cp)
    # 朱笔一划
    if t >= t_strike:
        k = ease_out((t - t_strike) / 0.32)
        sx0, sy0 = x0 - 26, cy + 18
        sx1, sy1 = x0 + total + 26, cy - 22
        ex = sx0 + (sx1 - sx0) * k
        ey = sy0 + (sy1 - sy0) * k
        path = skia.Path()
        path.moveTo(sx0, sy0)
        path.quadTo((sx0 + ex) / 2, (sy0 + ey) / 2 - 10 * k, ex, ey)
        bp = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=19,
                        StrokeCap=skia.Paint.kRound_Cap, Color4f=col(VERMILION, 0.95 * alpha))
        c.drawPath(path, bp)
        bp2 = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                         StrokeCap=skia.Paint.kRound_Cap, Color4f=col((235, 90, 70), 0.6 * alpha))
        c.drawPath(path, bp2)
    c.restore()


def bezier(p0, p1, p2, p3, u):
    a = (1 - u) ** 3
    b = 3 * (1 - u) ** 2 * u
    cc = 3 * (1 - u) * u * u
    d = u ** 3
    return (a * p0[0] + b * p1[0] + cc * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + cc * p2[1] + d * p3[1])


LIGHT_PATH = [(CX + HALF + 4, CY), (CX + HALF + 150, CY + 2), (CX + HALF + 250, CY + 40), (W + 160, CY + 120)]


def draw_light_path(c, t, T):
    t0 = T["path_in"]
    if t < t0:
        return
    k = ease_out((t - t0) / 1.1)
    n = 80
    pts = [bezier(*LIGHT_PATH, u * k) for u in np.linspace(0, 1, n)]
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    glow = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                      StrokeCap=skia.Paint.kRound_Cap, Color4f=col(GOLD, 0.35))
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    c.drawPath(path, glow)
    core = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=4.5,
                      StrokeCap=skia.Paint.kRound_Cap, Color4f=col((255, 232, 160), 0.95))
    c.drawPath(path, core)
    # 沿光路向外流动的细小光粒
    for i in range(14):
        u = ((t - t0) * 0.16 + i / 14.0) % 1.0
        if u > k:
            continue
        x, y = bezier(*LIGHT_PATH, u)
        glow_circle(c, x, y, 3.2, (255, 236, 170), 0.85 * math.sin(math.pi * u), 3)
    # 门口光晕
    glow_circle(c, CX + HALF + 6, CY, 34, GOLD, 0.5 * k, 20)


# ---------------------------------------------------------------- main frame
class Scene:
    def __init__(self, timeline, bg_scale=1.12):
        self.T = timeline
        self.bg = make_background(scale=bg_scale)
        self.bg_scale = bg_scale
        self.bg_img = skia.Image.fromarray(self.bg, colorType=skia.kRGBA_8888_ColorType)
        self.A = Actors()
        rng = np.random.default_rng(11)
        self.grain = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.48) / (H * 0.60)) ** 2)
        self.vign = np.clip(1.0 - 0.55 * np.clip(r - 0.45, 0, None) ** 1.6, 0.35, 1.0)[..., None]

    # -------------------------------------------------- camera
    def zoom(self, t):
        T = self.T
        return 1.0 + 0.085 * smooth(t / T["end"])

    def render(self, t):
        T = self.T
        surface = skia.Surface(W, H)
        c = surface.getCanvas()
        c.clear(skia.ColorBLACK)
        z = self.zoom(t)
        freeze = T["freeze"] <= t < T["answer"]
        # 世界层（随镜头推近）
        c.save()
        c.translate(W / 2, CY)
        c.scale(z, z)
        c.translate(-W / 2, -CY)
        # 撞墙时轻微震动
        shake = self.shake(t)
        c.translate(*shake)
        bw, bh = self.bg.shape[1], self.bg.shape[0]
        c.drawImageRect(self.bg_img, skia.Rect.MakeXYWH((W - bw) / 2, CY - bh * (CY / H), bw, bh),
                        skia.SamplingOptions(skia.FilterMode.kLinear))
        self.draw_world(c, t)
        c.restore()
        # 屏幕层（字幕、标签，不随镜头）
        self.draw_overlay(c, t)
        img = surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
        return self.post(img, t)

    def shake(self, t):
        sx = sy = 0.0
        for th in self.T["hits"]:
            dt = t - th
            if 0 <= dt < 0.35:
                e = (1 - dt / 0.35) ** 2
                sx += math.sin(dt * 90) * 3.5 * e
                sy += math.cos(dt * 77) * 2.5 * e
        return sx, sy

    def post(self, img, t):
        f = img.astype(np.float32)
        f *= self.vign
        g = self.grain[int(t * 30) % len(self.grain)]
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
        f += g * 4.2
        return np.clip(f, 0, 255).astype(np.uint8)

    # -------------------------------------------------- world
    def draw_world(self, c, t):
        T, A = self.T, self.A
        # 墙头火光：越撞越亮
        hits_done = sum(1 for th in T["hits"] if t >= th)
        rally = ramp(t, T["rally"], 1.4)
        loosen = ramp(t, T["loosen"], 1.8)
        wall_glow = (0.25 * rally + 0.14 * hits_done) * (1 - loosen)
        for th in T["hits"]:
            dt = t - th
            if 0 <= dt < 0.6:
                wall_glow += 0.5 * (1 - dt / 0.6)
        gate_flash = 0.0
        for tf in T["gate_flash"]:
            dt = t - tf
            if 0 <= dt < 0.7:
                gate_flash = max(gate_flash, math.sin(math.pi * dt / 0.7))
        draw_city(c, wall_glow=min(wall_glow, 1.3), gate_flash=gate_flash)
        self.draw_defenders(c, t)
        self.draw_siege(c, t)
        self.draw_attacks(c, t)
        draw_light_path(c, t, T)

    def draw_siege(self, c, t):
        T, A = self.T, self.A
        tt = min(t, T["freeze"]) if T["freeze"] <= t < T["answer"] else t
        breathe = 1.6 * np.sin(tt * 1.7 + A.siege_phase)
        rel = A.siege - np.array([CX, CY], np.float32)
        nrm = rel / (np.linalg.norm(rel, axis=1, keepdims=True) + 1e-6)
        # 攻城时整体微微压紧
        squeeze = 0.0
        if T["hits"]:
            squeeze = 6.0 * ramp(t, T["hits"][0] - 0.5, 0.8) * (1 - ramp(t, T["gap"], 1.0))
        pos = A.siege + nrm * (breathe[:, None] - squeeze)
        # 开口
        g = np.clip((t - T["gap"] - A.siege_gap_delay) / 1.9, 0, 1)
        g = g * g * (3 - 2 * g)
        pos = pos * (1 - g[:, None]) + (A.siege_gap_target + nrm * breathe[:, None]) * g[:, None]
        alpha = 1 - g * self.A.siege_withdraw.astype(np.float32)
        # 兵阵整体的暗影（让玄黑兵点成「一团」）
        mass = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=RING_ROWS * RING_STEP + 26,
                          Color4f=col((0, 0, 0), 0.38))
        mass.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
        dmid = RING_IN + (RING_ROWS - 1) * RING_STEP / 2
        c.saveLayer()
        c.drawRoundRect(skia.Rect.MakeLTRB(CX - dmid, CY - dmid, CX + dmid, CY + dmid), 0.22 * dmid, 0.22 * dmid, mass)
        kg = smooth((t - T["gap"]) / 2.2)
        if kg > 0:
            er = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 1.0), BlendMode=skia.BlendMode.kDstOut)
            er.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 22))
            c.drawRect(skia.Rect.MakeLTRB(CX + HALF + 30, CY - 70 * kg, W + 600, CY + 70 * kg), er)
        c.restore()
        shadow = skia.Paint(AntiAlias=True, Color4f=col((0, 0, 0), 0.55))
        shadow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3))
        for (x, y), r, a in zip(pos, A.siege_r, alpha):
            if a > 0.01:
                shadow.setAlphaf(0.55 * float(a))
                c.drawCircle(float(x) + 1.5, float(y) + 3.0, float(r) + 0.8, shadow)
        fill = skia.Paint(AntiAlias=True, Color4f=col(XUAN, 1.0))
        moon = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6,
                          Color4f=col((176, 188, 204), 0.55), StrokeCap=skia.Paint.kRound_Cap)
        for (x, y), r, a in zip(pos, A.siege_r, alpha):
            if a <= 0.01:
                continue
            x, y, r = float(x), float(y), float(r)
            fill.setAlphaf(float(a))
            c.drawCircle(x, y, r, fill)
            moon.setAlphaf(0.55 * float(a))
            c.drawArc(skia.Rect.MakeLTRB(x - r + 0.8, y - r + 0.8, x + r - 0.8, y + r - 0.8), 190, 100, False, moon)

    def draw_defenders(self, c, t):
        T, A = self.T, self.A
        tt = min(t, T["freeze"]) if T["freeze"] <= t < T["answer"] else t
        rally = np.clip((t - T["rally"] - A.def_delay) / 1.4, 0, 1)
        rally = rally * rally * (3 - 2 * rally)
        loose = np.clip((t - T["loosen"] - A.def_delay) / 1.8, 0, 1)
        loose = loose * loose * (3 - 2 * loose)
        jit = np.stack([np.sin(tt * 2.1 + A.def_phase), np.cos(tt * 1.7 + A.def_phase * 1.3)], -1) * 2.0
        p = A.def_calm * (1 - rally[:, None]) + A.def_wall * rally[:, None]
        p = p * (1 - loose[:, None]) + A.def_loose * loose[:, None]
        p = p + jit + np.array([CX, CY], np.float32)
        hits_done = sum(1 for th in T["hits"] if t >= th)
        inten = 0.42 + 0.48 * ramp(t, T["rally"], 1.4) + 0.08 * hits_done
        for th in T["hits"]:
            dt = t - th
            if 0 <= dt < 0.5:
                inten += 0.25 * (1 - dt / 0.5)
        inten *= 1 - 0.62 * ramp(t, T["loosen"], 1.8)
        flick = 0.85 + 0.15 * np.sin(tt * 7.0 + A.def_phase * 3)
        # 额外的城头光点（越撞越密）
        pts = list(zip(p, flick))
        if T["hits"]:
            span0, span1 = T["hits"][0] - 0.3, T["hits"][-1] + 0.3
            frac = clamp((t - span0) / (span1 - span0))
            fade = 1 - ramp(t, T["loosen"], 1.6)
            if frac > 0 and fade > 0:
                for e, te, ph in zip(A.def_extra, A.def_extra_t, A.def_extra_phase):
                    if te <= frac:
                        q = e * (1 - 0.25 * ramp(t, T["loosen"], 2.0)) + np.array([CX, CY], np.float32)
                        pts.append((q, fade * (0.85 + 0.15 * math.sin(tt * 7 + ph))))
        for (x, y), fl in pts:
            a = clamp(inten * fl, 0, 1.6)
            glow_circle(c, float(x), float(y), 9 + 4 * min(a, 1.2), EMBER, 0.38 * min(a, 1.3), 8)
        for (x, y), fl in pts:
            a = clamp(inten * fl, 0, 1.6)
            c.drawCircle(float(x), float(y), 3.4 + 1.2 * min(a, 1.0),
                         skia.Paint(AntiAlias=True, Color4f=col((255, 196, 120), min(1.0, 0.35 + 0.7 * a))))

    def draw_attacks(self, c, t):
        T = self.T
        # (方向角, 沿墙偏移) —— 箭头从外向城墙推进
        specs = [(0.0, -60), (math.pi / 2, 50), (math.pi, 40), (-math.pi / 2, -70), (math.pi, -80), (math.pi / 2, -40)]
        for i, th in enumerate(T["hits"]):
            ang, off = specs[i % len(specs)]
            # 箭头指向城心方向：从 ang 方向外侧来
            ca, sa = math.cos(ang), math.sin(ang)
            wx = CX + ca * (HALF + 12) - sa * off
            wy = CY + sa * (HALF + 12) + ca * off
            ox = CX + ca * (RING_IN + 120) - sa * off
            oy = CY + sa * (RING_IN + 120) + ca * off
            t_start = th - 0.42
            if t < t_start or t > th + 0.75:
                continue
            if t < th:
                k = (t - t_start) / 0.42
                k = k * k
                x, y = ox + (wx - ox) * k, oy + (wy - oy) * k
                a = min(1.0, (t - t_start) / 0.12)
            else:
                k = ease_out((t - th) / 0.75)
                x, y = wx + (ox - wx) * 0.45 * k, wy + (oy - wy) * 0.45 * k
                a = 1 - smooth((t - th) / 0.75)
            draw_arrow(c, x, y, ang + math.pi, 150, a, 1.35)
            if t >= th:
                dt = t - th
                glow_circle(c, wx, wy, 34 + 30 * dt, EMBER, 0.75 * max(0, 1 - dt / 0.5), 16)
                glow_circle(c, wx, wy, 10, (255, 236, 190), 0.9 * max(0, 1 - dt / 0.25), 5)

    # -------------------------------------------------- overlay (screen space)
    def draw_overlay(self, c, t):
        T = self.T
        # 顶部压暗带，托住大字
        top_dark = max(1 - ramp(t, T["q_out"], 0.3), ramp(t, T["answer"], 0.4))
        if top_dark > 0:
            sh = skia.GradientShader.MakeLinear(
                [skia.Point(0, 150), skia.Point(0, 760)],
                [skia.Color4f(0, 0, 0, 0.55 * top_dark).toColor(), skia.Color4f(0, 0, 0, 0).toColor()])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 800), skia.Paint(Shader=sh))
        self.draw_question(c, t)
        draw_slips(c, t, T)
        self.draw_hud(c, t)
        self.draw_subs(c, t)
        self.draw_answer(c, t)

    def draw_question(self, c, t):
        T = self.T
        a = 1 - smooth((t - T["q_out"]) / 0.25)
        if a <= 0:
            return
        f1 = font(SERIF_BLACK, 84)
        f2 = font(SERIF_BLACK, 138)
        draw_rich_line(c, "包围敌人", W / 2, 330, f1, a, stroke=9)
        draw_rich_line(c, "为什么要故意", W / 2, 440, f1, a, stroke=9)
        # 「留个口子」在 ~1.2s 有一道亮光扫过
        draw_rich_line(c, "**留个口子？**", W / 2, 600, f2, a, stroke=12)
        sweep = (t - T["q_glint"]) / 0.7
        if 0 < sweep < 1:
            gx = W / 2 - 300 + 600 * sweep
            sh = skia.GradientShader.MakeLinear(
                [skia.Point(gx - 70, 0), skia.Point(gx, 0), skia.Point(gx + 70, 0)],
                [skia.Color4f(1, 1, 1, 0).toColor(), skia.Color4f(1, 1, 0.9, 0.85 * a).toColor(), skia.Color4f(1, 1, 1, 0).toColor()])
            blob = _blob_pos("留个口子？", W / 2 - f2.measureText("留个口子？") / 2, 600, f2, 0)
            c.drawTextBlob(blob, 0, 0, skia.Paint(AntiAlias=True, Shader=sh))
        # 下划光
        u = ease_out((t - T["q_glint"]) / 0.5)
        if u > 0:
            w = 520 * u
            p = skia.Paint(AntiAlias=True, Color4f=col(YELLOW, 0.9 * a))
            c.drawRoundRect(skia.Rect.MakeXYWH(W / 2 - w / 2, 632, w, 7), 3.5, 3.5, p)

    def draw_hud(self, c, t):
        T = self.T
        a = ramp(t, T["hud_in"], 0.5) * (1 - ramp(t, T["hud_out"], 0.6))
        if a <= 0:
            return
        x, y = 64, 262
        f = font(SERIF_BOLD, 46)
        draw_text(c, "壶关", x, y, f, (236, 226, 204), a, stroke=6, tracking=10)
        lp = skia.Paint(AntiAlias=True, Color4f=col((236, 226, 204), 0.6 * a), StrokeWidth=2)
        c.drawLine(x, y + 18, x + 120, y + 18, lp)
        fk = font(KAI, 40)
        a1 = ramp(t, T["month1"], 0.4) * a
        a2 = ramp(t, T["month2"], 0.4) * a
        if a1 > 0:
            draw_text(c, "一个月……", x, y + 74, fk, (255, 214, 160), a1, stroke=5)
        if a2 > 0:
            draw_text(c, "又一个月", x, y + 128, fk, (255, 214, 160), a2, stroke=5)

    def draw_subs(self, c, t):
        for s in self.T["subs"]:
            t0, t1, text = s["t0"], s["t1"], s["text"]
            if t0 - 0.12 <= t <= t1 + 0.12:
                a = smooth((t - (t0 - 0.12)) / 0.12) * (1 - smooth((t - t1) / 0.12))
                self.draw_sub(c, text, a, s.get("size", 66))

    def draw_sub(self, c, text, a, size=66):
        f = font(SANS_BLACK, size)
        lines = text.split("|")
        base = 1440 - (len(lines) - 1) * (size * 1.32)
        for i, ln in enumerate(lines):
            draw_rich_line(c, ln, W / 2, base + i * size * 1.32, f, a, stroke=10)

    def draw_answer(self, c, t):
        T = self.T
        ta = T["answer"]
        if t < ta:
            return
        k1 = ease_out((t - ta) / 0.28)
        k2 = ease_out((t - ta - T["answer_l2"]) / 0.28)
        k3 = ramp(t, ta + T["answer_src"], 0.5)
        f1 = font(SERIF_BLACK, 84)
        fh = font(SERIF_BLACK, 104)
        # 大字一落下：略微从大到正常
        def scaled(k, fn):
            c.save()
            s = 1.0 + 0.10 * (1 - k)
            c.translate(W / 2, 0)
            c.scale(s, s)
            c.translate(-W / 2, 0)
            fn()
            c.restore()
        scaled(k1, lambda: draw_rich_line(c, "围死了，人人拼命", W / 2, 318, f1, k1, stroke=10))
        scaled(k2, lambda: draw_rich_line(c, "留条**活路**，就没人想死", W / 2, 452, f1, k2, stroke=10, hi_font=fh))
        fs = font(SERIF_BOLD, 38)
        draw_rich_line(c, "围城必示之活门 ——《三国志·曹仁传》", W / 2, 1404, fs, 0.92 * k3, stroke=6, base=(232, 226, 212))
        draw_rich_line(c, "围师必阙 ——《孙子兵法》", W / 2, 1468, fs, 0.92 * k3, stroke=6, base=(232, 226, 212))


def load_timeline(path):
    with open(path) as f:
        return json.load(f)
