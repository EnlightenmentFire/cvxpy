"""绘图基础：字体、文字、箭头、地图投影、粒子、叠加层。skia-python。"""
import math, json, os, functools
import numpy as np
import skia

W, H = 1080, 1920
FPS = 25
FD = "/usr/share/fonts/opentype/noto/"
DEM = "/tmp/claude-0/work/dem/"

# 颜色
BG = (9, 12, 20)
ODA = (214, 58, 40)        # 织田朱红
ODA_HI = (255, 112, 80)
SAITO = (112, 140, 168)    # 斋藤冷蓝灰
GOLD = (222, 184, 98)
PAPER = (226, 214, 186)
INK = (28, 24, 20)
WHITE = (240, 236, 226)
DIM = (150, 150, 150)
WATER = (40, 78, 104)


def C(rgb, a=1.0):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, max(0.0, min(1.0, a)))


def paint(rgb, a=1.0, stroke=None, blur=0, cap=skia.Paint.kRound_Cap, aa=True):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(C(rgb, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lin(t, t0, t1):
    return clamp((t - t0) / max(1e-6, t1 - t0))


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x); return x ** 3


def ramp(t, t0, d=0.5):
    return ease(lin(t, t0, t0 + d))


def fadeio(t, dur, a=0.4, b=0.4):
    return ease(lin(t, 0, a)) * (1 - ease(lin(t, dur - b, dur)))


def mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(len(a)))


# ---------- fonts ----------
_tf = {}
FONTS = {
    "serif": ("NotoSerifCJK-Regular.ttc", 2), "serif_sb": ("NotoSerifCJK-SemiBold.ttc", 2),
    "serif_b": ("NotoSerifCJK-Bold.ttc", 2), "serif_k": ("NotoSerifCJK-Black.ttc", 2),
    "sans": ("NotoSansCJK-Medium.ttc", 2), "sans_b": ("NotoSansCJK-Bold.ttc", 2),
    "sans_k": ("NotoSansCJK-Black.ttc", 2),
    "jp": ("NotoSerifCJK-SemiBold.ttc", 0), "jp_r": ("NotoSerifCJK-Regular.ttc", 0),
}


@functools.lru_cache(None)
def font(name, size):
    if name not in _tf:
        f, i = FONTS[name]
        _tf[name] = skia.Typeface.MakeFromFile(FD + f, i)
    ft = skia.Font(_tf[name], size)
    ft.setSubpixel(True); ft.setEdging(skia.Font.Edging.kAntiAlias)
    return ft


def tw(s, f="serif_b", size=40, ls=0):
    return font(f, size).measureText(s) + ls * max(0, len(s) - 1)


def text(cv, s, x, y, f="serif_b", size=40, col=WHITE, a=1.0, align="l", ls=0, shadow=0, glow=None, stroke=None):
    """y 为基线。align: l/c/r。ls 字距。shadow: 阴影模糊半径。stroke: (宽, 颜色)。"""
    if a <= 0.003 or not s:
        return
    ft = font(f, size)
    w = tw(s, f, size, ls)
    x0 = x - w / 2 if align == "c" else x - w if align == "r" else x

    def draw(p, dx=0, dy=0):
        if ls == 0:
            cv.drawString(s, x0 + dx, y + dy, ft, p)
        else:
            xx = x0
            for ch in s:
                cv.drawString(ch, xx + dx, y + dy, ft, p)
                xx += ft.measureText(ch) + ls
    if shadow:
        draw(paint((0, 0, 0), 0.75 * a, blur=shadow), 0, shadow * 0.4)
    if glow:
        draw(paint(glow[0], glow[2] * a, blur=glow[1]))
    if stroke:
        p = paint(stroke[1], a, stroke=stroke[0]); draw(p)
    draw(paint(col, a))
    return w


def wrap(s, f, size, maxw):
    lines, cur = [], ""
    for ch in s:
        if tw(cur + ch, f, size) > maxw and cur:
            if ch in "，。、？！：；”》）":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def para(cv, s, x, y, maxw, f="serif", size=40, col=WHITE, a=1.0, lh=1.5, align="l", shadow=0):
    ls = [l for part in s.split("\n") for l in wrap(part, f, size, maxw)]
    for i, l in enumerate(ls):
        text(cv, l, x, y + i * size * lh, f, size, col, a, align, shadow=shadow)
    return len(ls) * size * lh


# ---------- shapes ----------
def rrect(cv, x, y, w, h, r, p):
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)


def poly_path(pts, close=False):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_path(pts):
    """Catmull-Rom → cubic。"""
    p = skia.Path(); p.moveTo(*pts[0])
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    return p


def sample_path(path, n=200):
    m = skia.PathMeasure(path, False)
    L = m.getLength()
    out = []
    for i in range(n + 1):
        pos, tan = m.getPosTan(L * i / n)
        out.append((pos.x(), pos.y(), tan.x(), tan.y()))
    return out, L


def arrow(cv, pts, prog, col, width=34, a=1.0, head=2.1, glow=True, dashed=False, smooth=True):
    """粗箭头：沿路径生长到 prog（0..1），尾细头粗，带发光。"""
    if prog <= 0.01 or a <= 0:
        return
    path = smooth_path(pts) if smooth and len(pts) > 2 else poly_path(pts)
    smp, L = sample_path(path, 160)
    k = max(2, int(len(smp) * clamp(prog)))
    seg = smp[:k]
    hl = width * head * 1.15
    # 截掉箭头长度
    acc, cut = 0, len(seg) - 1
    for i in range(len(seg) - 1, 0, -1):
        acc += math.hypot(seg[i][0] - seg[i - 1][0], seg[i][1] - seg[i - 1][1])
        if acc >= hl * 0.75:
            cut = i; break
    body = seg[:cut + 1]
    tipx, tipy, tx, ty = seg[-1]
    nx, ny = -ty, tx
    if len(body) >= 2:
        left, right = [], []
        nb = len(body)
        for i, (x, y, dx, dy) in enumerate(body):
            wv = width * (0.45 + 0.55 * i / max(1, nb - 1)) / 2
            left.append((x - dy * wv, y + dx * wv)); right.append((x + dy * wv, y - dx * wv))
        shape = poly_path(left + right[::-1], True)
        if dashed:
            pp = skia.Paint(AntiAlias=True); pp.setColor4f(C(col, a)); pp.setStyle(skia.Paint.kStroke_Style)
            pp.setStrokeWidth(width * 0.55); pp.setStrokeCap(skia.Paint.kButt_Cap)
            pp.setPathEffect(skia.DashPathEffect.Make([width * 0.9, width * 0.7], 0))
            bp = poly_path([(x, y) for x, y, _, _ in body])
            if glow:
                g = skia.Paint(pp); g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, width * 0.5)); g.setColor4f(C(col, 0.5 * a))
                cv.drawPath(bp, g)
            cv.drawPath(bp, pp)
        else:
            if glow:
                cv.drawPath(shape, paint(col, 0.55 * a, blur=width * 0.6))
            cv.drawPath(shape, paint(col, a))
            hi = mix(col, (255, 255, 255), 0.35)
            cv.drawPath(poly_path([(x, y) for x, y, _, _ in body]), paint(hi, 0.35 * a, stroke=width * 0.18))
    bx, by = body[-1][0], body[-1][1]
    hw = width * head / 2
    hp = poly_path([(tipx, tipy), (bx + nx * hw, by + ny * hw), (bx - nx * hw, by - ny * hw)], True)
    if glow:
        cv.drawPath(hp, paint(col, 0.55 * a, blur=width * 0.6))
    cv.drawPath(hp, paint(col, a))


def blocked_mark(cv, x, y, s, a, col=SAITO):
    """蓝色挡板（盾形横条）。"""
    if a <= 0:
        return
    cv.save(); cv.translate(x, y)
    cv.drawRect(skia.Rect.MakeXYWH(-s, -s * 0.18, 2 * s, s * 0.36), paint(col, 0.5 * a, blur=s * 0.3))
    rrect(cv, -s, -s * 0.16, 2 * s, s * 0.32, s * 0.08, paint(col, a))
    cv.restore()


# ---------- map ----------
class Basemap:
    def __init__(self, name):
        self.meta = json.load(open(f"{DEM}{name}.json"))
        self.img = skia.Image.open(f"{DEM}{name}.png")
        self.z = self.meta["z"]

    def px(self, lon, lat):
        n = 2 ** self.z * 256
        x = (lon + 180) / 360 * n - self.meta["x0"] * 256
        y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n - self.meta["y0"] * 256
        return x, y


class MapView:
    """以 (lon,lat) 为屏幕中心点 (cx,cy)，scale = 屏幕像素 / 底图像素。"""
    def __init__(self, bm, lon, lat, scale, cx=W / 2, cy=860, rot=0):
        self.bm, self.scale, self.cx, self.cy = bm, scale, cx, cy
        self.ox, self.oy = bm.px(lon, lat)

    def P(self, lon, lat):
        x, y = self.bm.px(lon, lat)
        return (self.cx + (x - self.ox) * self.scale, self.cy + (y - self.oy) * self.scale)

    def draw(self, cv, a=1.0, bright=1.0):
        cv.save()
        cv.translate(self.cx, self.cy); cv.scale(self.scale, self.scale); cv.translate(-self.ox, -self.oy)
        p = skia.Paint(AntiAlias=True); p.setAlphaf(a)
        if bright != 1.0:
            b = bright
            p.setColorFilter(skia.ColorFilters.Matrix([b, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, 1, 0]))
        cv.drawImage(self.bm.img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
        cv.restore()


@functools.lru_cache(None)
def basemap(name):
    return Basemap(name)


# ---------- 质感 ----------
_rng = np.random.default_rng(7)
_grain = []


def grain_images():
    if not _grain:
        for i in range(6):
            g = (_rng.normal(0, 1, (480, 270)) * 18 + 128).clip(0, 255).astype(np.uint8)
            rgba = np.dstack([g, g, g, np.full_like(g, 22)])
            _grain.append(skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType))
    return _grain


def vignette(cv, strength=0.75):
    sh = skia.GradientShader.MakeRadial((W / 2, H * 0.45), H * 0.72, [C((0, 0, 0), 0), C((0, 0, 0), 0), C((0, 0, 0), strength)], [0, 0.55, 1.0])
    p = skia.Paint(); p.setShader(sh); cv.drawRect(skia.Rect.MakeWH(W, H), p)


def grain(cv, fi):
    img = grain_images()[fi % 6]
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kOverlay)
    cv.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kNearest), p)


def vgrad(cv, top, bot, y0=0, y1=H, a=1.0):
    sh = skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [C(top, a), C(bot, a)])
    p = skia.Paint(); p.setShader(sh); cv.drawRect(skia.Rect.MakeXYWH(0, y0, W, y1 - y0), p)


def rain(cv, t, n=260, a=0.35, seed=3, wind=0.18, speed=2600, y0=0, y1=H):
    r = np.random.default_rng(seed)
    xs = r.uniform(-200, W + 200, n); ys = r.uniform(0, 1, n); sp = r.uniform(0.7, 1.3, n); ln = r.uniform(30, 70, n)
    p = paint((200, 215, 235), a, stroke=1.6)
    span = y1 - y0
    for i in range(n):
        y = y0 + ((ys[i] * span + t * speed * sp[i]) % span)
        x = xs[i] + (y - y0) * wind
        cv.drawLine(x, y, x - ln[i] * wind, y - ln[i], p)


def embers(cv, t, x, y, a=1.0, n=14, seed=1, spread=60):
    r = np.random.default_rng(seed)
    for i in range(n):
        ph = (t * r.uniform(0.3, 0.7) + r.uniform(0, 1)) % 1
        ex = x + r.uniform(-spread, spread) * 0.4 + math.sin(t * 3 + i) * 10 * ph
        ey = y - ph * r.uniform(80, 220)
        cv.drawCircle(ex, ey, 2.2 * (1 - ph) + 0.6, paint((255, 170, 80), a * (1 - ph)))


def torch(cv, x, y, t, s=1.0, a=1.0, seed=0):
    fl = 0.8 + 0.2 * math.sin(t * 17 + seed * 3.1) + 0.1 * math.sin(t * 31 + seed)
    cv.drawCircle(x, y, 70 * s * fl, paint((255, 140, 50), 0.22 * a, blur=40 * s))
    cv.drawCircle(x, y, 22 * s * fl, paint((255, 190, 90), 0.8 * a, blur=8 * s))
    cv.drawCircle(x, y, 7 * s, paint((255, 240, 200), a))


def corner_tag(cv, s, a=1.0, y=118, x=None, col=(230, 220, 200)):
    """右上角说明小字（示意/情景演绎/据某书）。"""
    if a <= 0:
        return
    f, sz = "sans", 30
    w = tw(s, f, sz)
    x = W - 48 - w if x is None else x
    rrect(cv, x - 18, y - 36, w + 36, 50, 10, paint((0, 0, 0), 0.55 * a))
    rrect(cv, x - 18, y - 36, w + 36, 50, 10, paint(col, 0.35 * a, stroke=1.5))
    text(cv, s, x, y, f, sz, col, a)


def ai_badge(cv, a=1.0):
    rrect(cv, 44, 82, 150, 50, 10, paint((0, 0, 0), 0.45 * a))
    text(cv, "AI配音", 119, 117, "sans", 28, (225, 225, 225), 0.85 * a, "c")


def source_bar(cv, s, a=1.0, y=1360):
    """画面下部的出处条（细线+小字）。"""
    if a <= 0:
        return
    w = tw(s, "sans", 30)
    rrect(cv, W / 2 - w / 2 - 26, y - 38, w + 52, 54, 27, paint((0, 0, 0), 0.6 * a))
    text(cv, s, W / 2, y, "sans", 30, GOLD, a, "c")


def to_array(surface):
    return surface.toarray(colorType=skia.kRGBA_8888_ColorType)
