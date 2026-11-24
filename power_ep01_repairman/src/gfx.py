"""Core drawing toolkit: palette, paper, fonts, hand-drawn primitives, figures, machines.

Everything is drawn with skia-python on a 1080x1920 RGBA surface.
Visual rules: warm paper, brown inks, ONE accent (orange-red) reserved for
machine stoppage / uncertainty.
"""
import math
import os
from functools import lru_cache

import numpy as np
import skia

W, H = 1080, 1920
FPS = 30

FONT_DIR = os.environ.get(
    "EP_FONT_DIR",
    "/tmp/claude-0/-home-user-cvxpy/23149d0a-3dd1-5cf6-8dec-2980a0f4c270/scratchpad/work/fonts",
)
CACHE_DIR = os.environ.get(
    "EP_CACHE_DIR",
    "/tmp/claude-0/-home-user-cvxpy/23149d0a-3dd1-5cf6-8dec-2980a0f4c270/scratchpad/work/cache",
)
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------------------------------------------------------- layout
SAFE_TOP = 250          # WeChat Channels top UI
STAGE_TOP = 330
STAGE_BOT = 1225
STAGE_CY = (STAGE_TOP + STAGE_BOT) / 2
SUB_TOP = 1268          # subtitle zone
SUB_BOT = 1470
# below ~1500 the platform UI (name, caption, buttons) covers the frame

# ---------------------------------------------------------------- palette
PAPER = (236, 225, 200)
PAPER_DEEP = (226, 211, 180)
CARD = (246, 239, 222)
INK = (50, 37, 28)
INK2 = (88, 67, 50)
INK3 = (134, 112, 88)
INK4 = (176, 158, 132)
RULEC = (168, 156, 134)
OCHRE = (192, 152, 92)       # production workers' smocks
OCHRE_D = (158, 120, 70)
UMBER = (96, 70, 52)         # maintenance overalls
UMBER_D = (70, 50, 38)
SLATE = (128, 124, 116)      # shop director's grey coat
SLATE_D = (100, 96, 90)
SUIT = (74, 66, 60)
SKIN = (214, 190, 160)       # faceless heads, warm neutral
HAIR = (78, 58, 44)
METAL = (150, 138, 120)
METAL_D = (112, 102, 88)
ACCENT = (214, 74, 36)       # the ONLY warning colour


def col(rgb, a=1.0):
    r, g, b = rgb
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), int(r), int(g), int(b))


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))


def paint(rgb=INK, a=1.0, stroke=None, cap="round", join="round", blur=None):
    p = skia.Paint(AntiAlias=True, Color=col(rgb, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin({"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join}[join])
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, t0, t1):
    """0..1 progress of t inside [t0, t1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease(x):  # smoothstep-like cubic in-out
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ease_back(x, s=1.4):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


# ---------------------------------------------------------------- noise
def _hash(i, seed=0):
    x = math.sin(i * 12.9898 + seed * 78.233) * 43758.5453
    return x - math.floor(x)


def vnoise(x, seed=0):
    """Smooth 1-D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    a = _hash(i, seed) * 2 - 1
    b = _hash(i + 1, seed) * 2 - 1
    u = f * f * (3 - 2 * f)
    return a + (b - a) * u


def boil_seed(frame, every=5):
    """Hand-drawn 'line boil': the jitter seed changes every few frames."""
    return frame // every


# ---------------------------------------------------------------- fonts
@lru_cache(maxsize=None)
def typeface(name):
    files = {
        "serif_heavy": "SourceHanSerifCN-Heavy.otf",
        "serif_bold": "SourceHanSerifCN-Bold.otf",
        "serif_semi": "SourceHanSerifCN-SemiBold.otf",
        "serif": "SourceHanSerifCN-Medium.otf",
        "serif_reg": "SourceHanSerifCN-Regular.otf",
        "sans_heavy": "SourceHanSansCN-Heavy.otf",
        "sans_bold": "SourceHanSansCN-Bold.otf",
        "sans": "SourceHanSansCN-Medium.otf",
        "sans_reg": "SourceHanSansCN-Regular.otf",
        "garamond": "EBGaramond.ttf",
        "garamond_it": "EBGaramond-Italic.ttf",
        "hand": "Caveat.ttf",
        "script": "Parisienne.ttf",
        "type": "SpecialElite.ttf",
        "courier": "CourierPrime.ttf",
        "courier_bold": "CourierPrime-Bold.ttf",
    }
    tf = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, files[name]))
    if tf is None:
        raise FileNotFoundError(name)
    return tf


@lru_cache(maxsize=None)
def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_width(s, fname, size, spacing=0.0):
    f = font(fname, size)
    if spacing == 0:
        return f.measureText(s)
    return sum(f.measureText(ch) for ch in s) + spacing * max(0, len(s) - 1)


def draw_text(c, s, x, y, fname="serif_bold", size=48, rgb=INK, a=1.0, align="left",
              spacing=0.0, baseline="middle", stroke=None, stroke_rgb=PAPER):
    """Draw single-line text. baseline='middle' centres on y vertically."""
    if a <= 0.003 or not s:
        return 0
    f = font(fname, size)
    w = text_width(s, fname, size, spacing)
    if align == "center":
        x0 = x - w / 2
    elif align == "right":
        x0 = x - w
    else:
        x0 = x
    if baseline == "middle":
        m = f.getMetrics()
        yb = y - (m.fAscent + m.fDescent) / 2
    else:
        yb = y
    pnts = []
    if stroke:
        pnts.append(paint(stroke_rgb, a, stroke=stroke))
    pnts.append(paint(rgb, a))
    for p in pnts:
        if spacing == 0:
            c.drawString(s, x0, yb, f, p)
        else:
            xx = x0
            for ch in s:
                c.drawString(ch, xx, yb, f, p)
                xx += f.measureText(ch) + spacing
    return w


# ---------------------------------------------------------------- paper
def _fbm(w, h, rng, cells, weights):
    from PIL import Image
    acc = np.zeros((h, w), np.float32)
    for cell, wt in zip(cells, weights):
        gw, gh = max(2, w // cell + 2), max(2, h // cell + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w + cell * 2, h + cell * 2), Image.BICUBIC)
        a = np.asarray(im, np.float32)[cell:cell + h, cell:cell + w] / 255.0
        acc += (a - 0.5) * wt
    return acc


def make_paper(seed=11):
    """Static paper background + multiply overlay (texture, fibres, vignette)."""
    path_bg = os.path.join(CACHE_DIR, f"paper_bg_{seed}.npy")
    path_ov = os.path.join(CACHE_DIR, f"paper_ov_{seed}.npy")
    if os.path.exists(path_bg) and os.path.exists(path_ov):
        return np.load(path_bg), np.load(path_ov)
    from PIL import Image, ImageDraw, ImageFilter
    rng = np.random.default_rng(seed)
    blot = _fbm(W, H, rng, [420, 180, 70, 24], [0.9, 0.55, 0.35, 0.18])
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    fine = np.asarray(Image.fromarray(((fine * 18) + 128).clip(0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.6)), np.float32) / 255.0 - 0.5
    # fibres
    fib = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(2600):
        x, y = rng.random() * W, rng.random() * H
        ang = rng.random() * math.pi
        ln = 6 + rng.random() * 26
        d.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=int(40 + rng.random() * 60), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255.0
    # foxing spots
    spots = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(9):
        cx, cy, r = rng.random() * W, rng.random() * H, 20 + rng.random() * 90
        spots += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))) * (0.2 + 0.5 * rng.random())
    base = np.array(PAPER, np.float32)
    deep = np.array(PAPER_DEEP, np.float32)
    t = (blot * 0.9 + 0.5).clip(0, 1)[..., None]
    bg = base * (1 - t * 0.55) + deep * (t * 0.55)
    bg = bg + fine[..., None] * 10 - fib[..., None] * 9 - spots[..., None] * np.array([10, 14, 22], np.float32)
    # vignette
    nx = (xx / W - 0.5) * 2
    ny = (yy / H - 0.5) * 2
    r2 = nx ** 2 * 0.9 + ny ** 2 * 0.6
    vig = 1 - 0.20 * np.clip(r2 - 0.15, 0, None) ** 1.3
    bg = (bg * vig[..., None]).clip(0, 255).astype(np.uint8)
    # overlay: multiply texture applied on top of all content (keeps paper feel through ink)
    lum = (blot * 0.6 + fine * 0.7 - fib * 0.35 - spots * 0.25)
    ov = 1 + lum * 0.10
    ov = ov * (0.9 + 0.1 * vig)
    ov = (ov.clip(0.6, 1.0) * 255).astype(np.uint8)
    ov = np.dstack([ov, ov, ov, np.full_like(ov, 255)])
    bg = np.dstack([bg, np.full((H, W), 255, np.uint8)])
    np.save(path_bg, bg)
    np.save(path_ov, ov)
    return bg, ov


_PAPER = {}


def paper_images():
    if "bg" not in _PAPER:
        bg, ov = make_paper()
        _PAPER["bg"] = skia.Image.fromarray(bg, colorType=skia.kRGBA_8888_ColorType)
        _PAPER["ov"] = skia.Image.fromarray(ov, colorType=skia.kRGBA_8888_ColorType)
    return _PAPER["bg"], _PAPER["ov"]


def new_surface():
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    return skia.Surface.MakeRaster(info)


def draw_paper(c):
    bg, _ = paper_images()
    c.drawImage(bg, 0, 0)


def apply_overlay(c):
    _, ov = paper_images()
    p = skia.Paint()
    p.setBlendMode(skia.BlendMode.kMultiply)
    c.drawImage(ov, 0, 0, skia.SamplingOptions(), p)


# ---------------------------------------------------------------- hand-drawn primitives
def wobble_path(pts, seed=0, amp=1.2, closed=False, step=26):
    """Polyline through pts with gentle hand-drawn wobble (resampled + jittered)."""
    out = []
    n = len(pts)
    segs = n if closed else n - 1
    k = 0
    for i in range(segs):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        m = max(1, int(L / step))
        nx, ny = (-(y1 - y0) / (L + 1e-9), (x1 - x0) / (L + 1e-9))
        for j in range(m):
            t = j / m
            off = vnoise(k * 0.7, seed) * amp
            k += 1
            out.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
    if not closed:
        out.append(pts[-1])
    p = skia.Path()
    p.moveTo(*out[0])
    for q in out[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def wline(c, x0, y0, x1, y1, rgb=INK, w=3.0, a=1.0, seed=0, amp=1.0):
    c.drawPath(wobble_path([(x0, y0), (x1, y1)], seed, amp), paint(rgb, a, stroke=w))


def wrect(c, x, y, w, h, fill=None, stroke=INK, sw=3.0, a=1.0, seed=0, amp=1.0, r=0):
    if r > 0:
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
        if fill is not None:
            c.drawRRect(rr, paint(fill, a))
        if stroke is not None:
            c.drawRRect(rr, paint(stroke, a, stroke=sw))
        return
    pth = wobble_path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], seed, amp, closed=True)
    if fill is not None:
        c.drawPath(pth, paint(fill, a))
    if stroke is not None:
        c.drawPath(pth, paint(stroke, a, stroke=sw))


def stroke_reveal(c, path, prog, rgb=INK, w=4.0, a=1.0):
    """Draw only the first `prog` fraction of a path (draw-on animation)."""
    if prog <= 0:
        return
    pm = skia.PathMeasure(path, False)
    total = 0.0
    contours = []
    while True:
        L = pm.getLength()
        contours.append(L)
        total += L
        if not pm.nextContour():
            break
    target = total * clamp(prog)
    pm = skia.PathMeasure(path, False)
    acc = 0.0
    p = paint(rgb, a, stroke=w)
    for L in contours:
        if acc >= target:
            break
        dst = skia.Path()
        pm.getSegment(0, min(L, target - acc), dst, True)
        c.drawPath(dst, p)
        acc += L
        if not pm.nextContour():
            break


def arrow(c, x0, y0, x1, y1, rgb=INK, w=4.0, a=1.0, head=18, prog=1.0, seed=0, amp=0.8):
    if prog <= 0:
        return
    xe, ye = lerp(x0, x1, prog), lerp(y0, y1, prog)
    c.drawPath(wobble_path([(x0, y0), (xe, ye)], seed, amp), paint(rgb, a, stroke=w))
    ang = math.atan2(ye - y0, xe - x0)
    hp = skia.Path()
    hl = head + w * 0.8
    hp.moveTo(xe + math.cos(ang) * w * 0.6, ye + math.sin(ang) * w * 0.6)
    hp.lineTo(xe - math.cos(ang - 0.42) * hl, ye - math.sin(ang - 0.42) * hl)
    hp.lineTo(xe - math.cos(ang) * hl * 0.62, ye - math.sin(ang) * hl * 0.62)
    hp.lineTo(xe - math.cos(ang + 0.42) * hl, ye - math.sin(ang + 0.42) * hl)
    hp.close()
    c.drawPath(hp, paint(rgb, a))


def curved_arrow(c, pts, rgb=INK, w=4.0, a=1.0, head=18, prog=1.0):
    """Quadratic bezier arrow through (p0, ctrl, p1)."""
    (x0, y0), (cx, cy), (x1, y1) = pts
    n = 40
    m = max(2, int(n * clamp(prog)))
    P = []
    for i in range(m + 1):
        t = i / n
        if t > prog:
            t = prog
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        P.append((x, y))
    path = skia.Path()
    path.moveTo(*P[0])
    for q in P[1:]:
        path.lineTo(*q)
    c.drawPath(path, paint(rgb, a, stroke=w))
    if len(P) >= 2:
        (xa, ya), (xe, ye) = P[-2], P[-1]
        ang = math.atan2(ye - ya, xe - xa)
        hl = head + w * 0.8
        hp = skia.Path()
        hp.moveTo(xe + math.cos(ang) * w * 0.6, ye + math.sin(ang) * w * 0.6)
        hp.lineTo(xe - math.cos(ang - 0.42) * hl, ye - math.sin(ang - 0.42) * hl)
        hp.lineTo(xe - math.cos(ang) * hl * 0.62, ye - math.sin(ang) * hl * 0.62)
        hp.lineTo(xe - math.cos(ang + 0.42) * hl, ye - math.sin(ang + 0.42) * hl)
        hp.close()
        c.drawPath(hp, paint(rgb, a))


def gear_path(cx, cy, r, teeth=12, depth=0.18, rot=0.0, hole=0.32):
    p = skia.Path()
    n = teeth * 4
    for i in range(n + 1):
        ang = rot + 2 * math.pi * i / n
        k = i % 4
        rr = r if k in (0, 1) else r * (1 - depth)
        x, y = cx + math.cos(ang) * rr, cy + math.sin(ang) * rr
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    if hole > 0:
        p.addCircle(cx, cy, r * hole, skia.PathDirection.kCCW)
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p


def draw_gear(c, cx, cy, r, rot=0.0, rgb=METAL_D, a=1.0, teeth=12, outline=INK, sw=2.5):
    gp = gear_path(cx, cy, r, teeth, rot=rot)
    c.drawPath(gp, paint(rgb, a))
    c.drawPath(gp, paint(outline, a * 0.9, stroke=sw))


def ring_pulse(c, cx, cy, t, rmax=160, rgb=ACCENT, a=1.0, w=6):
    """Expanding warning ring(s); t in seconds since stop."""
    for k in range(3):
        tt = t - k * 0.45
        if tt <= 0:
            continue
        ph = (tt % 1.6) / 1.6 if k > 0 or tt > 1.6 else tt / 1.6
        r = 20 + ph * rmax
        al = a * (1 - ph) ** 1.2
        c.drawCircle(cx, cy, r, paint(rgb, al, stroke=w * (1 - ph * 0.5)))


def stamp(c, s, x, y, size=30, rgb=INK2, a=0.85, angle=-4):
    """Small rubber-stamp label, e.g. 「示意」."""
    c.save()
    c.translate(x, y)
    c.rotate(angle)
    w = text_width(s, "serif_heavy", size, spacing=size * 0.12) + size * 0.9
    h = size * 1.55
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), 6, 6), paint(rgb, a, stroke=3))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 5, -h / 2 + 5, w - 10, h - 10), 4, 4), paint(rgb, a * 0.6, stroke=1.2))
    draw_text(c, s, 0, 1, "serif_heavy", size, rgb, a, align="center", spacing=size * 0.12)
    c.restore()


# ---------------------------------------------------------------- figures (faceless)
def _rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def figure_side(c, x, y, h, kind="worker", face=1, a=1.0, look=0.0, arm=0.0, dim=0.0, tool=True):
    """Faceless side-view figure standing on (x, y=feet). face=+1 right, -1 left.
    look: head turn amount (0 = same as body, 1 = fully turned to the other side).
    arm: 0..1 arm raised forward. dim: 0..1 fade to grey."""
    if a <= 0.003:
        return
    body = {"worker": OCHRE, "maint": UMBER, "chief": SLATE, "engineer": SUIT, "director": SUIT}[kind]
    body = mix(body, (170, 162, 150), dim)
    skin = mix(SKIN, (190, 184, 174), dim)
    hair = mix(HAIR, (150, 144, 136), dim)
    ink = mix(INK, (140, 134, 126), dim)
    s = h / 100.0
    c.save()
    c.translate(x, y)
    c.scale(face * s, s)
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    pk = paint(ink, 1, stroke=2.2 / s)
    # legs
    legc = mix((70, 58, 50), (150, 144, 136), dim)
    if kind == "worker":
        c.drawRRect(_rrect(-9, -30, 7, 30, 3), paint(legc))
        c.drawRRect(_rrect(2, -30, 7, 30, 3), paint(legc))
        # smock (A-line, to the knee)
        p = skia.Path()
        p.moveTo(-12, -74); p.lineTo(12, -74); p.lineTo(19, -26); p.lineTo(-19, -26); p.close()
        c.drawPath(p, paint(body)); c.drawPath(p, pk)
        c.drawLine(-15, -46, 15, -46, paint(mix(body, ink, 0.25), 1, stroke=1.6 / s))  # apron tie
    else:
        legs_c = body if kind == "maint" else mix(body, ink, 0.25)
        c.drawRRect(_rrect(-11, -42, 9, 42, 3), paint(legs_c)); c.drawRRect(_rrect(-11, -42, 9, 42, 3), pk)
        c.drawRRect(_rrect(2, -42, 9, 42, 3), paint(legs_c)); c.drawRRect(_rrect(2, -42, 9, 42, 3), pk)
        if kind == "chief":  # long grey work coat
            p = skia.Path()
            p.moveTo(-14, -76); p.lineTo(14, -76); p.lineTo(18, -22); p.lineTo(-18, -22); p.close()
        else:
            p = skia.Path()
            p.moveTo(-14, -76); p.lineTo(14, -76); p.lineTo(15, -38); p.lineTo(-15, -38); p.close()
        c.drawPath(p, paint(body)); c.drawPath(p, pk)
        if kind == "maint":  # bib straps
            c.drawLine(-6, -76, -4, -52, paint(mix(body, ink, 0.4), 1, stroke=1.6 / s))
            c.drawLine(6, -76, 4, -52, paint(mix(body, ink, 0.4), 1, stroke=1.6 / s))
        if kind in ("engineer", "director"):
            c.drawPath(skia.Path().moveTo(-3, -76).lineTo(0, -60).lineTo(3, -76).close(), paint(CARD))
    # arm (forward)
    ang = lerp(80, 10, arm)  # degrees from horizontal-forward
    c.save()
    c.translate(4, -70)
    c.rotate(ang)
    c.drawRRect(_rrect(0, -4, 30, 8, 4), paint(mix(body, ink, 0.12)))
    c.drawRRect(_rrect(0, -4, 30, 8, 4), pk)
    c.drawCircle(31, 0, 4.5, paint(skin))
    if kind == "maint" and tool:
        # wrench
        c.drawRRect(_rrect(30, -2, 18, 4, 2), paint(METAL_D))
        c.drawCircle(49, 0, 5, paint(METAL_D))
        c.drawCircle(51, 0, 2.2, paint(body))
    if kind == "chief" and tool:
        c.drawRect(skia.Rect.MakeXYWH(26, -14, 14, 18), paint(CARD))
        c.drawRect(skia.Rect.MakeXYWH(26, -14, 14, 18), pk)
    c.restore()
    # neck + head
    c.drawRect(skia.Rect.MakeXYWH(-3, -82, 6, 8), paint(skin))
    hx = lerp(0, -1.5, look)
    c.drawCircle(hx, -92, 11, paint(skin))
    c.drawCircle(hx, -92, 11, pk)
    # head direction marker: bun (worker) / cap peak (maint) / hair (others)
    side = lerp(1.0, -1.0, look)  # +1 = facing forward(right in local coords)
    if kind == "worker":
        c.drawCircle(hx - 11 * side, -95, 5.5, paint(hair))
        c.drawArc(skia.Rect.MakeXYWH(hx - 11.5, -104, 23, 18), 180, 180, False, paint(hair))
    elif kind == "maint":
        c.drawArc(skia.Rect.MakeXYWH(hx - 12, -106, 24, 18), 180, 180, True, paint(UMBER_D if dim < 0.5 else ink))
        c.drawRRect(_rrect(hx + (2 if side > 0 else -16), -97, 14, 3.5, 1.5), paint(UMBER_D if dim < 0.5 else ink))
    else:
        c.drawArc(skia.Rect.MakeXYWH(hx - 11.5, -104, 23, 16), 180, 180, False, paint(hair))
        c.drawRect(skia.Rect.MakeXYWH(hx - 11 * side - 2, -97, 4, 6), paint(hair))
    if lay is not None:
        c.restore()
    c.restore()


def figure_top(c, x, y, r, kind="worker", heading=0.0, a=1.0, arm=1.0):
    """Faceless top-down figure. heading in degrees (0 = facing +x). r = shoulder half-width."""
    if a <= 0.003:
        return
    body = {"worker": OCHRE, "maint": UMBER, "chief": SLATE}[kind]
    c.save()
    c.translate(x, y)
    c.rotate(heading)
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    pk = paint(INK, 1, stroke=2.0)
    # arms reaching forward
    if arm > 0.01:
        for sy in (-1, 1):
            c.drawRRect(_rrect(0, sy * r * 0.62 - r * 0.17, r * 0.95 * arm + 2, r * 0.34, r * 0.16), paint(mix(body, INK, 0.12)))
            c.drawCircle(r * 0.95 * arm + 2, sy * r * 0.62, r * 0.17, paint(SKIN))
    c.drawOval(skia.Rect.MakeXYWH(-r * 0.45, -r, r * 0.9, r * 2), paint(body))
    c.drawOval(skia.Rect.MakeXYWH(-r * 0.45, -r, r * 0.9, r * 2), pk)
    hr = r * 0.40
    if kind == "worker":
        c.drawCircle(0, 0, hr, paint(HAIR))
        c.drawCircle(-hr * 0.95, 0, hr * 0.42, paint(mix(HAIR, INK, 0.3)))  # bun at the back
        c.drawCircle(hr * 0.3, 0, hr * 0.55, paint(SKIN))  # forehead hint, faceless
    elif kind == "maint":
        c.drawCircle(0, 0, hr * 1.05, paint(UMBER_D))
        c.drawRRect(_rrect(hr * 0.5, -hr * 0.6, hr * 0.9, hr * 1.2, hr * 0.3), paint(UMBER_D))  # cap peak
    else:
        c.drawCircle(0, 0, hr, paint(HAIR))
        c.drawCircle(hr * 0.3, 0, hr * 0.6, paint(SKIN))
    c.drawCircle(0, 0, hr * (1.05 if kind == "maint" else 1.0), pk)
    if lay is not None:
        c.restore()
    c.restore()


def bust(c, x, y, s, kind="worker", a=1.0, dim=0.0):
    """Faceless front-view bust icon (for org charts). (x, y) = centre of head; s = head radius."""
    if a <= 0.003:
        return
    body = {"worker": OCHRE, "maint": UMBER, "chief": SLATE, "engineer": SUIT, "director": SUIT}[kind]
    body = mix(body, (178, 170, 158), dim)
    skin = mix(SKIN, (196, 190, 180), dim)
    hair = mix(HAIR, (160, 154, 146), dim)
    ink = mix(INK, (150, 144, 136), dim)
    pk = paint(ink, a, stroke=max(1.5, s * 0.09))
    p = skia.Path()
    p.moveTo(x - s * 1.55, y + s * 2.55)
    p.cubicTo(x - s * 1.55, y + s * 1.35, x - s * 0.9, y + s * 1.05, x, y + s * 1.05)
    p.cubicTo(x + s * 0.9, y + s * 1.05, x + s * 1.55, y + s * 1.35, x + s * 1.55, y + s * 2.55)
    p.close()
    c.drawPath(p, paint(body, a)); c.drawPath(p, pk)
    if kind in ("engineer", "director"):
        tp = skia.Path().moveTo(x - s * 0.28, y + s * 1.06).lineTo(x, y + s * 1.7).lineTo(x + s * 0.28, y + s * 1.06).close()
        c.drawPath(tp, paint(CARD, a))
    if kind == "maint":
        c.drawLine(x - s * 0.55, y + s * 1.1, x - s * 0.45, y + s * 2.5, paint(mix(body, ink, 0.4), a, stroke=s * 0.1))
        c.drawLine(x + s * 0.55, y + s * 1.1, x + s * 0.45, y + s * 2.5, paint(mix(body, ink, 0.4), a, stroke=s * 0.1))
    c.drawCircle(x, y, s, paint(skin, a)); c.drawCircle(x, y, s, pk)
    if kind == "worker":
        c.drawArc(skia.Rect.MakeXYWH(x - s * 1.05, y - s * 1.08, s * 2.1, s * 1.5), 180, 180, False, paint(hair, a))
        c.drawCircle(x, y - s * 1.12, s * 0.38, paint(hair, a))
    elif kind == "maint":
        c.drawArc(skia.Rect.MakeXYWH(x - s * 1.08, y - s * 1.12, s * 2.16, s * 1.5), 180, 180, True, paint(UMBER_D if dim < 0.5 else ink, a))
        c.drawRRect(_rrect(x - s * 1.25, y - s * 0.5, s * 2.5, s * 0.3, s * 0.12), paint(UMBER_D if dim < 0.5 else ink, a))
    else:
        c.drawArc(skia.Rect.MakeXYWH(x - s * 1.02, y - s * 1.05, s * 2.04, s * 1.3), 180, 180, False, paint(hair, a))


def wrench_icon(c, x, y, s, rgb=INK2, a=1.0, ang=-40):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.drawRRect(_rrect(-s * 0.9, -s * 0.13, s * 1.5, s * 0.26, s * 0.12), paint(rgb, a))
    jaw = skia.Path()
    jaw.addCircle(s * 0.75, 0, s * 0.34)
    jaw.addRect(skia.Rect.MakeXYWH(s * 0.78, -s * 0.12, s * 0.4, s * 0.24))
    jaw.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(jaw, paint(rgb, a))
    c.restore()


# ---------------------------------------------------------------- machines
def machine_top(c, x, y, w, h, t, running=1.0, stop_t=None, seed=0, a=1.0):
    """Top-down cigarette-making machine. running: 0..1 speed factor."""
    c.save()
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    wrect(c, x, y, w, h, fill=METAL, stroke=INK, sw=3, seed=seed, amp=0.8)
    wrect(c, x + 8, y + 8, w - 16, h * 0.34, fill=mix(METAL, CARD, 0.35), stroke=INK2, sw=2, seed=seed + 1, amp=0.6)
    # conveyor with moving dashes (the cigarette rod)
    cy = y + h * 0.72
    c.drawLine(x + 10, cy, x + w - 10, cy, paint(INK2, 1, stroke=10, cap="butt"))
    ph = (t * 90 * running) % 28
    dp = paint(CARD, 1, stroke=6, cap="butt")
    dp.setPathEffect(skia.DashPathEffect.Make([16, 12], -ph))
    c.drawLine(x + 10, cy, x + w - 10, cy, dp)
    # gears
    rot = t * 2.2 * running
    draw_gear(c, x + w * 0.22, y + h * 0.25, h * 0.2, rot, METAL_D, teeth=10)
    draw_gear(c, x + w * 0.22 + h * 0.36, y + h * 0.25, h * 0.14, -rot * 1.4 + 0.2, METAL_D, teeth=8)
    if lay is not None:
        c.restore()
    c.restore()
    return (x + w * 0.22, y + h * 0.25)


def machine_side(c, x, y, w, h, t, running=1.0, a=1.0, seed=0, jam=False):
    """Side view machine standing on y (floor). Returns gear centre."""
    c.save()
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    # legs
    for lx in (x + w * 0.1, x + w * 0.85):
        c.drawRect(skia.Rect.MakeXYWH(lx, y - h * 0.25, w * 0.05, h * 0.25), paint(METAL_D))
    # body
    wrect(c, x, y - h, w, h * 0.75, fill=METAL, stroke=INK, sw=3, seed=seed, amp=0.7)
    # hopper
    hp = skia.Path()
    hp.moveTo(x + w * 0.55, y - h); hp.lineTo(x + w * 0.9, y - h * 1.25); hp.lineTo(x + w * 0.98, y - h * 1.25); hp.lineTo(x + w * 0.75, y - h); hp.close()
    c.drawPath(hp, paint(METAL_D)); c.drawPath(hp, paint(INK, 1, stroke=2.5))
    rot = t * 2.0 * running
    gx, gy = x + w * 0.28, y - h * 0.62
    draw_gear(c, gx, gy, h * 0.22, rot, METAL_D, teeth=12)
    draw_gear(c, gx + h * 0.34, gy + h * 0.1, h * 0.14, -rot * 1.55, METAL_D, teeth=9)
    # output tray with cigarettes
    c.drawRect(skia.Rect.MakeXYWH(x + w * 0.6, y - h * 0.45, w * 0.32, h * 0.08), paint(INK2))
    ph = (t * 40 * running) % 16
    for k in range(6):
        cx_ = x + w * 0.62 + ((k * 16 + ph) % (w * 0.3))
        c.drawRect(skia.Rect.MakeXYWH(cx_, y - h * 0.47, 10, 4), paint(CARD))
    if lay is not None:
        c.restore()
    c.restore()
    return gx, gy


def factory_front(c, x, y, w, h, a=1.0, windows_lit=True, seed=3):
    """Front view of a factory building with sawtooth roof and chimney; (x, y) = bottom-left."""
    c.save()
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    # chimney
    wrect(c, x + w * 0.82, y - h * 1.32, w * 0.07, h * 0.6, fill=mix(UMBER, PAPER, 0.25), stroke=INK, sw=3, seed=seed)
    # sawtooth roof
    n = 5
    p = skia.Path()
    p.moveTo(x, y - h * 0.72)
    for i in range(n):
        x0 = x + w * i / n
        p.lineTo(x0 + w / n * 0.78, y - h)
        p.lineTo(x0 + w / n * 0.78, y - h * 0.72)
        p.lineTo(x0 + w / n, y - h * 0.72)
    p.lineTo(x + w, y)
    p.lineTo(x, y)
    p.close()
    c.drawPath(p, paint(mix(OCHRE, PAPER, 0.45)))
    c.drawPath(p, paint(INK, 1, stroke=3.5))
    # windows
    for i in range(n):
        for j in range(2):
            wx = x + w * (i + 0.18) / n
            wy = y - h * (0.62 - j * 0.28)
            wrect(c, wx, wy, w / n * 0.64, h * 0.2, fill=mix(CARD, PAPER, 0.3), stroke=INK2, sw=2.5, seed=seed + i * 3 + j)
            c.drawLine(wx + w / n * 0.32, wy, wx + w / n * 0.32, wy + h * 0.2, paint(INK2, 1, stroke=2))
    # door
    wrect(c, x + w * 0.44, y - h * 0.2, w * 0.12, h * 0.2, fill=UMBER, stroke=INK, sw=3, seed=seed + 9)
    if lay is not None:
        c.restore()
    c.restore()


def card(c, x, y, w, h, title, lines=3, a=1.0, ang=0.0, seed=0, title_size=40, sub=None, body_fn=None,
         fill=CARD, title_font="serif_heavy"):
    """A rule / glossary card centred at (x, y)."""
    if a <= 0.003:
        return
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    lay = c.saveLayerAlpha(None, int(255 * a)) if a < 0.999 else None
    # shadow
    c.drawRRect(_rrect(-w / 2 + 6, -h / 2 + 8, w, h, 8), paint(INK, 0.16, blur=6))
    c.drawRRect(_rrect(-w / 2, -h / 2, w, h, 8), paint(fill))
    c.drawRRect(_rrect(-w / 2, -h / 2, w, h, 8), paint(INK2, 1, stroke=2.5))
    ty = -h / 2 + title_size * 0.95
    draw_text(c, title, 0, ty, title_font, title_size, INK, 1, align="center")
    if sub:
        draw_text(c, sub, 0, ty + title_size * 0.95, "courier", int(title_size * 0.5), INK3, 1, align="center")
    if body_fn is not None:
        body_fn(c, w, h)
    else:
        y0 = ty + title_size * (1.6 if sub else 1.0)
        for k in range(lines):
            ln = w * (0.72 - 0.18 * _hash(k + seed * 7))
            yy = y0 + k * 22
            if yy > h / 2 - 18:
                break
            c.drawRRect(_rrect(-w / 2 + 26, yy, ln, 7, 3.5), paint(INK4, 0.8))
    if lay is not None:
        c.restore()
    c.restore()


def check_mark(c, x, y, s, prog, rgb=INK, w=9):
    p = skia.Path()
    p.moveTo(x - s * 0.45, y)
    p.lineTo(x - s * 0.1, y + s * 0.38)
    p.lineTo(x + s * 0.55, y - s * 0.48)
    stroke_reveal(c, p, prog, rgb, w)


def qmark(c, x, y, size, rgb=INK, a=1.0):
    draw_text(c, "?", x, y, "garamond", size, rgb, a, align="center")
