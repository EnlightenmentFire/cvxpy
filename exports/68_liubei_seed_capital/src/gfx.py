# -*- coding: utf-8 -*-
"""Drawing primitives (skia) for the 68 Liu Bei video."""
import math, functools
import numpy as np
import skia
from scipy import ndimage as ndi

W, H = 1080, 1920
NOTO = "/usr/share/fonts/opentype/noto/"


def _face(fname, want):
    for i in range(10):
        try:
            tf = skia.Typeface.MakeFromFile(NOTO + fname, i)
        except Exception:
            tf = None
        if tf is None:
            break
        if tf.getFamilyName().endswith(want):
            return tf
    return skia.Typeface.MakeFromFile(NOTO + fname, 0)


@functools.lru_cache(None)
def face(kind):
    return {
        "serif_tc": lambda: _face("NotoSerifCJK-Bold.ttc", "TC"),
        "serif_sc": lambda: _face("NotoSerifCJK-Bold.ttc", "SC"),
        "serif_blk": lambda: _face("NotoSerifCJK-Black.ttc", "SC"),
        "serif_blk_tc": lambda: _face("NotoSerifCJK-Black.ttc", "TC"),
        "serif_reg": lambda: _face("NotoSerifCJK-Regular.ttc", "SC"),
        "sans_b": lambda: _face("NotoSansCJK-Bold.ttc", "SC"),
        "sans_m": lambda: _face("NotoSansCJK-Medium.ttc", "SC"),
        "sans_blk": lambda: _face("NotoSansCJK-Black.ttc", "SC"),
    }[kind]()


@functools.lru_cache(None)
def font(kind, size):
    f = skia.Font(face(kind), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def col(c, a=1.0):
    r, g, b = c[:3]
    return skia.Color4f(r / 255, g / 255, b / 255, a * (c[3] / 255 if len(c) > 3 else 1))


def paint(c, a=1.0, stroke=None, blur=0, aa=True, cap=None, join=None):
    p = skia.Paint(AntiAlias=aa, Color4f=col(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap)
        p.setStrokeJoin(join or skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# palette
GOLD = (222, 184, 110)
GOLD_L = (246, 222, 168)
INK = (14, 12, 12)
RED = (206, 46, 36)          # 刘备 朱红
RED_L = (240, 96, 70)
BLUEGRAY = (122, 146, 170)   # 官军 / 公孙瓒 冷蓝灰
BLUE_L = (170, 196, 222)
OCHRE = (214, 168, 64)       # 黄巾 土黄
DARK_OCHRE = (150, 104, 48)  # 袁绍（与黄巾区分）暗赭
PAPER = (236, 224, 196)
WHITE = (250, 248, 242)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ramp(t, a, b):
    if b <= a:
        return 1.0 if t >= a else 0.0
    return min(max((t - a) / (b - a), 0.0), 1.0)


def fade_win(t, a, b, fi=0.4, fo=0.4):
    """1 inside [a,b] with fades."""
    return min(ramp(t, a, a + fi), 1 - ramp(t, b - fo, b))


# ───────── text ─────────
def text_w(s, f):
    return f.measureText(s)


NO_START = "，。！？、；：」』”）》,.!?;:"


def wrap(s, f, maxw):
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if text_w(cur + ch, f) > maxw and cur:
            if ch in NO_START:
                cur += ch; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(s, f, maxw):
    """wrap into minimal number of lines with roughly equal length"""
    lines = wrap(s, f, maxw)
    n = len(lines)
    if n <= 1:
        return lines
    lo, hi = maxw * 0.5, maxw
    best = lines
    for _ in range(14):
        mid = (lo + hi) / 2
        L = wrap(s, f, mid)
        if len(L) <= n:
            best = L; hi = mid
        else:
            lo = mid
    return best


def draw_text(c, s, x, y, f, color, a=1.0, align="c", stroke=0, stroke_col=INK, stroke_a=0.9,
              shadow=0, shadow_a=0.6, spacing=0.0, glow=0, glow_col=None):
    if a <= 0.002 or not s:
        return
    w = text_w(s, f) + spacing * max(len(s) - 1, 0)
    x0 = x - w / 2 if align == "c" else (x - w if align == "r" else x)

    def _draw(p, dx=0, dy=0):
        if spacing == 0:
            c.drawString(s, x0 + dx, y + dy, f, p)
        else:
            xx = x0
            for ch in s:
                c.drawString(ch, xx + dx, y + dy, f, p)
                xx += text_w(ch, f) + spacing
    if glow:
        _draw(paint(glow_col or color, a * 0.55, blur=glow))
    if shadow:
        _draw(paint(INK, a * shadow_a, blur=shadow), 0, shadow * 0.5)
    if stroke:
        _draw(paint(stroke_col, a * stroke_a, stroke=stroke))
    _draw(paint(color, a))
    return w


def draw_vtext(c, s, x, y, f, color, a=1.0, lead=1.08):
    """vertical text, top-down, centered on x"""
    size = f.getSize()
    for i, ch in enumerate(s):
        w = text_w(ch, f)
        c.drawString(ch, x - w / 2, y + size * (i + 0.88) * lead, f, paint(color, a))


# ───────── raster helpers ─────────
def np_to_image(arr):
    arr = np.ascontiguousarray(arr)
    if arr.shape[2] == 3:
        arr = np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)


def fbm(shape, seed, octaves=5, base=64.0, persist=0.55):
    rng = np.random.default_rng(seed)
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    s = base
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        up = ndi.zoom(g, (h / (gh - 1) * 1.0001, w / (gw - 1) * 1.0001), order=3)[:h, :w]
        if up.shape != shape:
            up = np.pad(up, ((0, h - up.shape[0]), (0, w - up.shape[1])), mode="edge")
        out += amp * up
        tot += amp
        amp *= persist
        s /= 2
    return out / tot


def sky(shape, top, mid, bot, seed=1, clouds=0.25, cloud_col=None, horizon=0.62):
    h, w = shape
    y = np.linspace(0, 1, h)[:, None]
    top, mid, bot = [np.array(c, np.float32) for c in (top, mid, bot)]
    t1 = np.clip(y / horizon, 0, 1)
    t2 = np.clip((y - horizon) / (1 - horizon), 0, 1)
    g = np.where((y < horizon)[..., None], top * (1 - t1[..., None]) + mid * t1[..., None],
                 mid * (1 - t2[..., None]) + bot * t2[..., None])
    g = np.broadcast_to(g, (h, w, 3)).copy()
    if clouds:
        n = fbm((h // 4, w // 4), seed, base=60)
        n = ndi.zoom(n, 4, order=1)[:h, :w]
        n = np.clip((n - 0.45) * 2.2, 0, 1) * (1 - y) ** 0.7
        cc = np.array(cloud_col or mid, np.float32)
        g = g * (1 - clouds * n[..., None]) + cc * clouds * n[..., None]
    return g


def vignette(img, strength=0.55, power=2.2):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 1.414
    v = 1 - strength * d ** power
    return img * v[..., None]


def grain(img, seed, amt=5.0):
    rng = np.random.default_rng(seed)
    return img + rng.normal(0, amt, img.shape[:2])[..., None]


def to_u8(img):
    return np.clip(img, 0, 255).astype(np.uint8)


def ridge_pts(seed, w, y0, amp, rough=0.55, n=9, x0=0):
    rng = np.random.default_rng(seed)
    N = 2 ** n + 1
    ys = np.zeros(N)
    ys[0], ys[-1] = rng.normal(0, amp * 0.5), rng.normal(0, amp * 0.5)
    step, sc = N - 1, amp
    while step > 1:
        half = step // 2
        for i in range(half, N - 1, step):
            ys[i] = (ys[i - half] + ys[i + half]) / 2 + rng.normal(0, sc)
        sc *= rough
        step = half
    xs = np.linspace(x0, x0 + w, N)
    return list(zip(xs, y0 + ys))


def fill_poly_np(img, pts, color, alpha=1.0, blur=0.0):
    """rasterize polygon with skia into an RGBA layer and composite onto float img"""
    h, w = img.shape[:2]
    surf = skia.Surface(w, h)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    cv.drawPath(p, paint(color, 1.0, blur=blur))
    a = surf.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255 * alpha
    img[:] = img * (1 - a[..., None]) + np.array(color[:3], np.float32) * a[..., None]


def mountains_layer(img, seed, y0, amp, color, alpha=1.0, haze_col=None, haze=0.0):
    h, w = img.shape[:2]
    pts = ridge_pts(seed, w + 200, y0, amp, x0=-100)
    poly = pts + [(w + 100, h + 10), (-100, h + 10)]
    c = np.array(color, np.float32)
    if haze_col is not None:
        c = c * (1 - haze) + np.array(haze_col, np.float32) * haze
    fill_poly_np(img, poly, tuple(c), alpha)


# ───────── shapes ─────────
def path_from(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def smooth_path(pts, close=False):
    """Catmull-Rom -> cubic"""
    p = skia.Path()
    n = len(pts)
    if n < 2:
        return p
    P = list(pts)
    if close:
        P = [pts[-1]] + list(pts) + [pts[0], pts[1]]
    else:
        P = [pts[0]] + list(pts) + [pts[-1]]
    p.moveTo(*P[1])
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    if close:
        p.close()
    return p


class PathSet:
    """separately drawn sub-paths (avoids winding holes where parts overlap)"""
    def __init__(self):
        self.ps = []
    def addPath(self, q):
        self.ps.append(q)
    def addOval(self, r):
        q = skia.Path(); q.addOval(r); self.ps.append(q)
    def draw(self, c, pt):
        for q in self.ps:
            c.drawPath(q, pt)


def figure(c, x, y, h, color=INK, a=1.0, pose="stand", phase=0.0, rim=None, rim_a=0.5, facing=1, hat="bun",
           sleeve=0.0):
    """Han-robe silhouette. (x,y) = feet center. h = height in px."""
    s = h / 100.0
    f = facing
    p = PathSet()
    if pose == "sit":
        # seated (kneeling) figure, h = seated height
        p.addOval(skia.Rect.MakeXYWH(x - 9 * s, y - 100 * s, 18 * s, 21 * s))
        body = [(x - 13 * s, y - 80 * s), (x + 13 * s, y - 80 * s), (x + 20 * s, y - 50 * s),
                (x + 34 * s * f if f > 0 else x + 30 * s, y - 4 * s), (x + 30 * s, y), (x - 30 * s, y),
                (x - 30 * s, y - 4 * s), (x - 20 * s, y - 50 * s)]
        p.addPath(smooth_path(body, close=True))
        # arms forward (working)
        sw = math.sin(phase * 2 * math.pi) * 3 * s
        arm = [(x + 8 * s * f, y - 72 * s), (x + 30 * s * f, y - 40 * s + sw), (x + 40 * s * f, y - 34 * s + sw),
               (x + 38 * s * f, y - 28 * s + sw), (x + 22 * s * f, y - 34 * s), (x + 2 * s * f, y - 56 * s)]
        p.addPath(smooth_path(arm, close=True))
    else:
        walk = pose == "walk"
        sw = math.sin(phase * 2 * math.pi) if walk else 0.0
        bob = abs(math.cos(phase * 2 * math.pi)) * 1.5 * s if walk else 0
        yy = y - bob
        p.addOval(skia.Rect.MakeXYWH(x - 7 * s, yy - 100 * s, 14 * s, 16 * s))
        body = [(x - 8 * s, yy - 84 * s), (x + 8 * s, yy - 84 * s), (x + 17 * s, yy - 76 * s), (x + 15 * s, yy - 50 * s),
                (x + 19 * s + 3 * s * sw, yy - 2 * s), (x + 3 * s * sw, yy + 1 * s), (x - 19 * s + 3 * s * sw, yy - 2 * s),
                (x - 15 * s, yy - 50 * s), (x - 17 * s, yy - 76 * s)]
        p.addPath(smooth_path(body, close=True))
        # sleeves
        sl = sleeve
        for side in (-1, 1):
            arm = [(x + side * 15 * s, yy - 76 * s), (x + side * (22 + 10 * sl) * s, yy - (48 + 20 * sl) * s),
                   (x + side * (26 + 14 * sl) * s, yy - (30 + 26 * sl) * s), (x + side * (14 + 6 * sl) * s, yy - (34 + 18 * sl) * s),
                   (x + side * 12 * s, yy - 56 * s)]
            p.addPath(smooth_path(arm, close=True))
        if walk:
            for side in (-1, 1):
                k = sw * side
                p.addPath(path_from([(x + 5 * s * k - 3 * s, yy - 4 * s), (x + 9 * s * k + 3 * s, yy - 4 * s),
                                     (x + 12 * s * k + 4 * s, yy + 2 * s), (x + 12 * s * k - 4 * s, yy + 2 * s)]))
        y = yy
    # topknot / hat
    if hat == "bun":
        p.addOval(skia.Rect.MakeXYWH(x - 4 * s, y - 108 * s, 8 * s, 9 * s))
    elif hat == "guan":   # official cap
        p.addPath(path_from([(x - 8 * s, y - 97 * s), (x + 8 * s, y - 97 * s), (x + 11 * s, y - 112 * s), (x - 6 * s, y - 110 * s)]))
    elif hat == "jin":    # yellow turban knot
        p.addOval(skia.Rect.MakeXYWH(x - 9 * s, y - 106 * s, 18 * s, 10 * s))
    if rim is not None:
        c.save()
        c.translate(-2.5 * s * f, -1.5 * s)
        p.draw(c, paint(rim, a * rim_a, blur=2.2 * s))
        c.restore()
    p.draw(c, paint(color, a))
    return p


def horse(c, x, y, s, phase=0.0, color=INK, a=1.0, facing=1, gallop=1.0, rider=False, rim=None, rim_a=0.45, head_up=0.0):
    """side-view horse silhouette. (x,y)=hoof line center, s=scale (~1 => 100px tall withers)."""
    c.save()
    c.translate(x, y)
    c.scale(s * facing, s)
    ph = phase * 2 * math.pi
    bob = math.sin(ph * 2) * 3 * gallop
    p = PathSet()
    # body
    body = [(-50, -64 + bob), (-30, -78 + bob), (10, -78 + bob), (38, -78 + bob), (50, -66 + bob),
            (46, -44 + bob), (30, -34 + bob), (-30, -36 + bob), (-50, -44 + bob), (-56, -56 + bob)]
    p.addPath(smooth_path(body, close=True))
    # neck + head
    hu = head_up * 10
    neck = [(24, -74 + bob), (42, -100 + bob - hu), (56, -114 + bob - hu), (66, -113 + bob - hu), (84, -94 + bob - hu * 0.6),
            (86, -86 + bob - hu * 0.6), (76, -82 + bob - hu * 0.6), (64, -90 + bob - hu), (52, -58 + bob)]
    p.addPath(smooth_path(neck, close=True))
    # ears
    p.addPath(path_from([(58, -112 + bob - hu), (60, -122 + bob - hu), (63, -111 + bob - hu)]))
    # mane flutter
    mane = [(46, -98 + bob - hu), (40, -90 + bob - hu * 0.7 + math.sin(ph * 3) * 2), (34, -78 + bob), (44, -80 + bob)]
    p.addPath(smooth_path(mane, close=True))
    # tail
    tw = math.sin(ph * 2 + 1) * 5 * gallop
    tail = [(-50, -64 + bob), (-66, -60 + bob + tw), (-78, -44 + bob + tw * 1.5), (-70, -46 + bob + tw), (-54, -54 + bob)]
    p.addPath(smooth_path(tail, close=True))
    # legs (4) two-segment, gallop swing
    legs = [(30, 0.0), (22, 0.18), (-34, 0.5), (-42, 0.68)]
    lp = paint(color, a, stroke=9.5, cap=skia.Paint.kRound_Cap)
    lp2 = paint(color, a, stroke=6.5, cap=skia.Paint.kRound_Cap)
    for lx, off in legs:
        ang = math.sin(ph + off * 2 * math.pi) * 0.55 * gallop
        knee = math.cos(ph + off * 2 * math.pi) * 0.5 * gallop
        hx, hy = lx, -40 + bob
        kx, ky = hx + math.sin(ang) * 22, hy + math.cos(ang) * 20
        fa = ang + (abs(knee) if lx > 0 else -abs(knee)) * 0.9
        fx, fy = kx + math.sin(fa) * 20, ky + math.cos(fa) * 20
        fy = min(fy, 0)
        lpath = skia.Path(); lpath.moveTo(hx, hy); lpath.lineTo(kx, ky)
        c.drawPath(lpath, lp)
        l2 = skia.Path(); l2.moveTo(kx, ky); l2.lineTo(fx, fy)
        c.drawPath(l2, lp2)
    if rider:
        p.addOval(skia.Rect.MakeXYWH(-6, -122 + bob, 12, 13))
        p.addPath(smooth_path([(-12, -108 + bob), (8, -108 + bob), (12, -80 + bob), (4, -62 + bob), (-16, -62 + bob), (-14, -86 + bob)], close=True))
    if rim is not None:
        c.save(); c.translate(-2, -1.5)
        p.draw(c, paint(rim, a * rim_a, blur=2.5))
        c.restore()
    p.draw(c, paint(color, a))
    c.restore()


def coin(c, x, y, r, a=1.0, spin=0.0, color=GOLD):
    """五铢钱: round with square hole; spin squashes x."""
    sx = max(abs(math.cos(spin)), 0.12)
    c.save(); c.translate(x, y); c.scale(sx, 1)
    c.drawCircle(0, 0, r * 1.5, paint(color, a * 0.25, blur=r * 0.8))
    p = skia.Path()
    p.addCircle(0, 0, r)
    p.addRect(skia.Rect.MakeXYWH(-r * 0.32, -r * 0.32, r * 0.64, r * 0.64))
    p.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(p, paint(color, a))
    c.drawCircle(0, 0, r * 0.82, paint(GOLD_L, a * 0.5, stroke=max(1.0, r * 0.08)))
    c.restore()


def glow_dot(c, x, y, r, color, a=1.0):
    c.drawCircle(x, y, r * 3.2, paint(color, a * 0.25, blur=r * 2.2))
    c.drawCircle(x, y, r * 1.4, paint(color, a * 0.6, blur=r * 0.7))
    c.drawCircle(x, y, r * 0.75, paint(WHITE, a * 0.9))


def polyline_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def sample_curve(pts, n=80):
    """Catmull-rom sampled points"""
    if len(pts) == 2:
        return [(pts[0][0] + (pts[1][0] - pts[0][0]) * i / n, pts[0][1] + (pts[1][1] - pts[0][1]) * i / n) for i in range(n + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    seg = len(P) - 3
    for i in range(seg):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        m = max(2, n // seg)
        for k in range(m):
            t = k / m
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


def big_arrow(c, pts, prog, width, color, a=1.0, glow=True, head=2.3, dash_flow=None, t=0.0, taper=0.45):
    """Thick tapered arrow along curve, drawn up to prog (0..1)."""
    if prog <= 0.001:
        return
    S = sample_curve(pts, 120)
    L = [0.0]
    for i in range(1, len(S)):
        L.append(L[-1] + math.dist(S[i - 1], S[i]))
    tot = L[-1]
    end = tot * prog
    hl = width * head * 1.1
    body_end = max(0.0, end - hl * 0.6)
    left, right = [], []
    k_end = 0
    for i in range(len(S)):
        if L[i] > body_end:
            break
        k_end = i
        i0, i1 = max(i - 1, 0), min(i + 1, len(S) - 1)
        dx, dy = S[i1][0] - S[i0][0], S[i1][1] - S[i0][1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        u = L[i] / max(end, 1)
        wv = width * (taper + (1 - taper) * u) / 2
        left.append((S[i][0] + nx * wv, S[i][1] + ny * wv))
        right.append((S[i][0] - nx * wv, S[i][1] - ny * wv))
    # tip position
    def at(dist):
        for i in range(1, len(S)):
            if L[i] >= dist:
                f = (dist - L[i - 1]) / max(L[i] - L[i - 1], 1e-6)
                return (S[i - 1][0] + (S[i][0] - S[i - 1][0]) * f, S[i - 1][1] + (S[i][1] - S[i - 1][1]) * f)
        return S[-1]
    tip = at(end)
    base = at(max(end - hl, 0))
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    d = math.hypot(dx, dy) or 1
    nx, ny = -dy / d, dx / d
    hw = width * head / 2
    headp = [(base[0] + nx * hw, base[1] + ny * hw), tip, (base[0] - nx * hw, base[1] - ny * hw)]
    poly = left + [(base[0] + nx * width / 2, base[1] + ny * width / 2)] + headp + [(base[0] - nx * width / 2, base[1] - ny * width / 2)] + right[::-1]
    if len(poly) < 3:
        return
    p = path_from(poly)
    if glow:
        c.drawPath(p, paint(color, a * 0.45, blur=width * 0.6))
    c.drawPath(p, paint(color, a * 0.92))
    c.drawPath(p, paint(WHITE, a * 0.35, stroke=2.0))
    # flowing highlight stripes
    if dash_flow:
        c.save(); c.clipPath(p, doAntiAlias=True)
        for j in range(int(end / dash_flow) + 2):
            dd = (j * dash_flow + t * dash_flow * 1.2) % (end + dash_flow)
            q = at(min(dd, end))
            c.drawCircle(q[0], q[1], width * 0.35, paint(WHITE, a * 0.22, blur=width * 0.25))
        c.restore()


def dashed_line(c, pts, color, a=1.0, w=4, on=14, off=10, prog=1.0, phase=0.0):
    S = sample_curve(pts, 100)
    L = polyline_len(S)
    p = skia.Path()
    p.moveTo(*S[0])
    acc = 0
    for i in range(1, len(S)):
        acc += math.dist(S[i - 1], S[i])
        if acc > L * prog:
            break
        p.lineTo(*S[i])
    pp = paint(color, a, stroke=w)
    pp.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    c.drawPath(p, pp)


def blob(c, cx, cy, r, color, a, t, seed=0, wob=0.18, blur=0):
    pts = []
    rng = np.random.default_rng(seed)
    ph = rng.random(4) * 6.28
    for k in range(28):
        th = k / 28 * 2 * math.pi
        rr = r * (1 + wob * (0.6 * math.sin(3 * th + ph[0] + t * 0.7) + 0.4 * math.sin(5 * th + ph[1] - t * 0.5)))
        pts.append((cx + rr * math.cos(th), cy + rr * math.sin(th) * 0.85))
    p = smooth_path(pts, close=True)
    c.drawPath(p, paint(color, a * 0.35, blur=r * 0.35))
    c.drawPath(p, paint(color, a * 0.55, blur=blur))
    c.drawPath(p, paint(color, a * 0.9, stroke=2.0))


# ───────── panels ─────────
def rrect(c, x, y, w, h, r, fill=None, fill_a=0.0, border=None, border_a=0.0, bw=2.0, shadow=0):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if shadow:
        c.drawRRect(rr, paint(INK, 0.5 * max(fill_a, border_a), blur=shadow))
    if fill is not None and fill_a > 0:
        c.drawRRect(rr, paint(fill, fill_a))
    if border is not None and border_a > 0:
        c.drawRRect(rr, paint(border, border_a, stroke=bw))


def tag(c, x, y, label, color, a=1.0, size=34, align="l", fill=(20, 16, 14)):
    f = font("sans_b", size)
    w = text_w(label, f) + size * 1.0
    hh = size * 1.55
    x0 = x if align == "l" else x - w / 2
    rrect(c, x0, y, w, hh, 6, fill=fill, fill_a=0.82 * a, border=color, border_a=a, bw=2.5)
    c.drawRect(skia.Rect.MakeXYWH(x0, y, 7, hh), paint(color, a))
    draw_text(c, label, x0 + w / 2 + 3, y + hh * 0.72, f, color, a)
    return w, hh


def seal(c, cx, cy, size, chars, a=1.0, prog=1.0, color=RED, rot=-4):
    """red square seal (阴文, white chars) with stamp animation; chars = 2 or 4 chars"""
    if a <= 0 or prog <= 0:
        return
    k = ease_out(prog)
    sc = 1.6 - 0.6 * k
    al = a * min(1.0, prog * 3)
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.scale(sc, sc)
    s = size
    # ink spread halo at impact
    if 0.25 < prog < 1:
        c.drawRect(skia.Rect.MakeXYWH(-s / 2 - 6, -s / 2 - 6, s + 12, s + 12), paint(color, al * 0.3 * (1 - prog), blur=10))
    rng = np.random.default_rng(len(chars) * 7 + int(cx))
    edge = []
    for i in range(40):
        t = i / 40
        side = int(t * 4); u = (t * 4) % 1
        jit = rng.normal(0, s * 0.008)
        if side == 0: edge.append((-s / 2 + u * s, -s / 2 + jit))
        elif side == 1: edge.append((s / 2 + jit, -s / 2 + u * s))
        elif side == 2: edge.append((s / 2 - u * s, s / 2 + jit))
        else: edge.append((-s / 2 + jit, s / 2 - u * s))
    c.drawPath(path_from(edge), paint(color, al * 0.95))
    f = font("serif_blk_tc", s * (0.38 if len(chars) == 4 else 0.62))
    if len(chars) == 4:
        pos = [(s * 0.22, -s * 0.22), (s * 0.22, s * 0.22), (-s * 0.22, -s * 0.22), (-s * 0.22, s * 0.22)]
    elif len(chars) == 2:
        pos = [(0, -s * 0.2), (0, s * 0.24)]
        f = font("serif_blk_tc", s * 0.4)
    else:
        pos = [(0, 0)]
    for ch, (px, py) in zip(chars, pos):
        w = text_w(ch, f)
        c.drawString(ch, px - w / 2, py + f.getSize() * 0.36, f, paint((250, 240, 228), al * 0.95))
    # texture speckles (paper showing through)
    for i in range(60):
        px, py = rng.uniform(-s / 2, s / 2, 2)
        c.drawCircle(px, py, rng.uniform(0.6, 2.0), paint((240, 220, 200), al * 0.35))
    c.restore()


def bamboo_ledger(c, cx, cy, w, h, n=13, a=1.0, open_k=1.0):
    """bamboo-slip ledger (竹简) unrolled; returns slip x centers"""
    sw = w / n
    xs = []
    vis = open_k
    for i in range(n):
        # unroll from right to left
        fi = (n - 1 - i) / max(n - 1, 1)
        if fi > vis + 1e-6:
            continue
        x = cx + w / 2 - (n - i) * sw
        xs.append(x + sw / 2)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 2, cy - h / 2, sw - 4, h), 6, 6)
        c.drawRRect(r, paint((86, 62, 34), a))
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear(
            [skia.Point(x, 0), skia.Point(x + sw, 0)],
            [col((188, 150, 96), a), col((222, 188, 128), a), col((170, 130, 80), a)]))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 4, cy - h / 2 + 2, sw - 8, h - 4), 5, 5), g)
        c.drawLine(x + sw * 0.3, cy - h / 2 + 6, x + sw * 0.3, cy + h / 2 - 6, paint((150, 112, 66), a * 0.4, stroke=1.2))
    # binding cords
    if xs:
        for yy in (cy - h * 0.36, cy + h * 0.36):
            c.drawLine(xs[0] - sw / 2, yy, xs[-1] + sw / 2, yy, paint((60, 40, 24), a * 0.9, stroke=4))
    return xs


def mulberry_tree(seed=7):
    """returns (branch segments list [(x0,y0,x1,y1,w)], leaf clusters [(x,y,r)]) normalized: base at (0,0), height ~1"""
    rng = np.random.default_rng(seed)
    segs, leaves = [], []

    def grow(x, y, ang, length, w, depth):
        x2 = x + math.sin(ang) * length
        y2 = y - math.cos(ang) * length
        segs.append((x, y, x2, y2, w))
        if depth == 0 or length < 0.03:
            leaves.append((x2, y2, rng.uniform(0.05, 0.09)))
            return
        n = 2 if depth > 1 else 3
        for k in range(n):
            da = (k - (n - 1) / 2) * rng.uniform(0.45, 0.75) + rng.normal(0, 0.12)
            grow(x2, y2, ang * 0.85 + da * 1.25, length * rng.uniform(0.68, 0.8), w * 0.66, depth - 1)
    grow(0, 0, 0.0, 0.30, 0.07, 6)
    return segs, leaves


def draw_tree(c, x, y, scale, segs, leaves, color=INK, a=1.0, t=0.0, rim=None, leaf_col=None):
    c.save(); c.translate(x, y); c.scale(scale, scale)
    for (x0, y0, x1, y1, w) in segs:
        c.drawLine(x0, y0, x1, y1, paint(color, a, stroke=w))
    crown = skia.Path()
    for i, (lx, ly, r) in enumerate(leaves):
        sway = math.sin(t * 1.3 + i * 0.7) * 0.004
        crown.addCircle(lx + sway, ly, r)
    crown.setFillType(skia.PathFillType.kWinding)
    if rim is not None:
        c.save(); c.translate(-0.008, -0.012)
        c.drawPath(crown, paint(rim, a * 0.55, blur=0.01))
        c.restore()
    c.drawPath(crown, paint(leaf_col or color, a))
    # inner texture: darker blobs
    rng = np.random.default_rng(5)
    for (lx, ly, r) in leaves[::3]:
        c.drawCircle(lx + rng.normal(0, 0.01), ly + 0.01, r * 0.6, paint(INK, a * 0.25, blur=0.012))
    c.restore()
