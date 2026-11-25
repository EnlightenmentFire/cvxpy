"""Japanese-period silhouette art for ep.66 (skia): castles, ishigaki, trees, ridges, ashigaru, ships, rice bales,
swords, hoe, scroll/paper, ledger grid. All shapes are hand-coded vector drawings (no external images)."""
import math, functools
import numpy as np, skia
from engine import *

VERM = (214, 66, 44)        # Toyotomi vermilion
BLUE = (96, 160, 226)       # Hojo cold blue
PAPERL = (236, 226, 202); PAPERD = (196, 180, 146)
GOLDW = (236, 190, 96)

def P(*pts):
    pa = skia.Path(); pa.moveTo(*pts[0])
    for q in pts[1:]: pa.lineTo(*q)
    pa.close(); return pa

def lin(c, x0, y0, x1, y1, cols, stops=None):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(*k) if isinstance(k, tuple) and len(k) == 2 and isinstance(k[0], tuple) else col(k) for k in cols], stops))
    return p

def bg_grad(c, top, bot, y0=0, y1=H):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y1)], [col(top), col(bot)]))
    c.drawRect(skia.Rect(0, 0, W, H), p)

def sky3(c, top, mid, hor, hy):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, hy)], [col(top), col(mid), col(hor)], [0, 0.55, 1]))
    c.drawRect(skia.Rect(0, 0, W, hy + 2), p)

@functools.lru_cache(maxsize=64)
def ridge_pts(seed, y, amp, n=40, rough=0.5):
    rng = np.random.default_rng(seed)
    xs = np.linspace(-60, W + 60, n)
    v = np.cumsum(rng.normal(0, 1, n)); v = (v - v.mean()) / (v.std() + 1e-6)
    v2 = rng.normal(0, rough, n)
    ys = y - amp * (0.6 * v + 0.4 * v2)
    return tuple(zip(xs.tolist(), ys.tolist()))

def ridge(c, seed, y, amp, color, a=1.0, n=40, rough=0.5, blur=None):
    pts = ridge_pts(seed, y, amp, n, rough)
    pa = skia.Path(); pa.moveTo(-60, H + 10)
    sm = catmull(list(pts), 6)
    for q in sm: pa.lineTo(float(q[0]), float(q[1]))
    pa.lineTo(W + 60, H + 10); pa.close()
    c.drawPath(pa, paint(color, a, blur=blur))

def ridge_y(seed, y, amp, xq, n=40, rough=0.5):
    pts = ridge_pts(seed, y, amp, n, rough)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return float(np.interp(xq, xs, ys))

def conifer(c, x, y, h, color, a=1.0, ang=0.0):
    """tree with base at (x,y), height h; ang = fall rotation in degrees (about base)."""
    if a <= 0: return
    c.save(); c.translate(x, y); c.rotate(ang)
    w = h * 0.34; p = paint(color, a)
    c.drawRect(skia.Rect(-h * 0.025, -h * 0.18, h * 0.025, 0), p)
    for k in range(4):
        y0 = -h * (0.12 + k * 0.21); ww = w * (1 - k * 0.2)
        c.drawPath(P((-ww, y0), (ww, y0), (ww * 0.12, y0 - h * 0.36), (-ww * 0.12, y0 - h * 0.36)), p)
    c.drawPath(P((-w * 0.25, -h * 0.85), (w * 0.25, -h * 0.85), (0, -h)), p)
    c.restore()

def ishigaki(c, x0, x1, y_top, y_bot, a=1.0, lit=(150, 140, 124), dark=(70, 64, 58), stones=True, seed=3):
    """sloped stone wall (slight concave flare), stone pattern"""
    flare = (y_bot - y_top) * 0.22
    pa = skia.Path(); pa.moveTo(x0 + flare, y_top); pa.lineTo(x1 - flare, y_top)
    pa.quadTo(x1 - flare * 0.2, (y_top + y_bot) / 2 + flare * 0.3, x1, y_bot); pa.lineTo(x0, y_bot)
    pa.quadTo(x0 + flare * 0.2, (y_top + y_bot) / 2 + flare * 0.3, x0 + flare, y_top); pa.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y_top), skia.Point(0, y_bot)], [col(lit, a), col(dark, a)]))
    c.drawPath(pa, p)
    if stones:
        c.save(); c.clipPath(pa, skia.ClipOp.kIntersect, True)
        rng = np.random.default_rng(seed); hh = (y_bot - y_top)
        rows = max(3, int(hh / 26)); lp = paint((30, 26, 22), 0.55 * a, stroke=1.6)
        for r in range(rows + 1):
            yy = y_top + r * hh / rows
            c.drawLine(x0, yy, x1, yy + rng.normal(0, 1.5), lp)
            xx = x0 + rng.uniform(0, 40)
            while xx < x1:
                c.drawLine(xx, yy, xx + rng.normal(0, 3), yy + hh / rows, lp); xx += rng.uniform(30, 64)
        c.restore()

def roof(c, cx, y, w, h, color, a=1.0, flare=0.16):
    """curved Japanese hip roof, eave line at y, width w, height h"""
    pa = skia.Path()
    pa.moveTo(cx - w / 2 - w * flare, y - h * 0.15)
    pa.quadTo(cx - w / 2, y, cx - w * 0.42, y)
    pa.lineTo(cx + w * 0.42, y)
    pa.quadTo(cx + w / 2, y, cx + w / 2 + w * flare, y - h * 0.15)
    pa.quadTo(cx + w * 0.32, y - h * 0.4, cx + w * 0.22, y - h)
    pa.lineTo(cx - w * 0.22, y - h)
    pa.quadTo(cx - w * 0.32, y - h * 0.4, cx - w / 2 - w * flare, y - h * 0.15)
    pa.close()
    c.drawPath(pa, paint(color, a))

def tenshu(c, cx, base_y, s=1.0, wall=(228, 222, 206), roofc=(40, 44, 50), a=1.0, lit=1.0, windows=0.0):
    """multi-storey keep on a stone base; base_y = top of stone base. s=scale (1 -> ~300 px tall)."""
    if a <= 0: return
    levels = [(220, 64), (176, 56), (132, 50), (92, 46)]
    y = base_y
    for i, (w, hgt) in enumerate(levels):
        w *= s; hgt *= s
        wc = tuple(int(v * (0.55 + 0.45 * lit)) for v in wall)
        c.drawRect(skia.Rect(cx - w / 2, y - hgt, cx + w / 2, y), paint(wc, a))
        if windows > 0:
            for k in range(3):
                wx = cx - w / 3 + k * w / 3
                c.drawRect(skia.Rect(wx - 7 * s, y - hgt * 0.62, wx + 7 * s, y - hgt * 0.3), paint((255, 190, 110), a * windows))
        else:
            for k in range(3):
                wx = cx - w / 3 + k * w / 3
                c.drawRect(skia.Rect(wx - 6 * s, y - hgt * 0.62, wx + 6 * s, y - hgt * 0.3), paint((40, 36, 34), a * 0.8))
        y -= hgt
        roof(c, cx, y + 8 * s, w * 1.12, 34 * s if i < 3 else 52 * s, roofc, a)
        y -= 16 * s
    # shachi-ish finial nubs
    c.drawCircle(cx - 22 * s, y - 30 * s, 5 * s, paint(roofc, a)); c.drawCircle(cx + 22 * s, y - 30 * s, 5 * s, paint(roofc, a))
    return y

def castle(c, cx, ground_y, s=1.0, a=1.0, lit=1.0, windows=0.0, stone=(160, 150, 132), walls=True):
    """stone base + tenshu + flanking white walls. returns top y"""
    bw = 320 * s; bh = 120 * s
    if walls:
        for side in (-1, 1):
            x0 = cx + side * bw * 0.45; x1 = cx + side * bw * 1.35
            lo, hi = min(x0, x1), max(x0, x1)
            ishigaki(c, lo, hi, ground_y - bh * 0.55, ground_y, a, tuple(int(v * (0.6 + 0.4 * lit)) for v in stone), (60, 56, 50), seed=5 + side)
            c.drawRect(skia.Rect(lo + 10 * s, ground_y - bh * 0.55 - 34 * s, hi - 10 * s, ground_y - bh * 0.55), paint(tuple(int(v * (0.55 + 0.45 * lit)) for v in (226, 220, 204)), a))
            c.drawRect(skia.Rect(lo + 4 * s, ground_y - bh * 0.55 - 42 * s, hi - 4 * s, ground_y - bh * 0.55 - 30 * s), paint((44, 46, 52), a))
            # yagura
            yx = (lo + hi) / 2 + side * bw * 0.25
            c.drawRect(skia.Rect(yx - 40 * s, ground_y - bh * 0.55 - 86 * s, yx + 40 * s, ground_y - bh * 0.55 - 30 * s), paint(tuple(int(v * (0.55 + 0.45 * lit)) for v in (226, 220, 204)), a))
            roof(c, yx, ground_y - bh * 0.55 - 82 * s, 96 * s, 34 * s, (44, 46, 52), a)
    ishigaki(c, cx - bw / 2, cx + bw / 2, ground_y - bh, ground_y, a, tuple(int(v * (0.6 + 0.4 * lit)) for v in stone), (60, 56, 50))
    return tenshu(c, cx, ground_y - bh, s, a=a, lit=lit, windows=windows)

def ashigaru(c, x, y, s=1.0, color=INK, a=1.0, spear=True, banner=None, ph=0.0, walk=0.0):
    """foot soldier silhouette: jingasa hat, spear, optional sashimono banner (plain colour, no emblems)."""
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(s, s); p = paint(color, a)
    sw = math.sin(ph) * 10 * walk
    c.drawLine(-6, -40, -8 - sw, 0, paint(color, a, stroke=9)); c.drawLine(6, -40, 8 + sw, 0, paint(color, a, stroke=9))
    c.drawPath(P((-15, -40), (15, -40), (12, -92), (-12, -92)), p)
    c.drawCircle(0, -102, 11, p)
    c.drawPath(P((-26, -104), (26, -104), (0, -122)), p)  # jingasa
    if spear:
        c.drawLine(14, -70, 26, -230, paint(color, a, stroke=4))
        c.drawPath(P((24, -228), (30, -230), (29, -262)), p)
    if banner is not None:
        c.drawLine(-10, -92, -14, -200, paint(color, a, stroke=3))
        c.drawRect(skia.Rect(-46, -200, -14, -140), paint(banner, a))
    c.restore()

def boat(c, x, y, s=1.0, color=INK, a=1.0, sail=None, flip=False):
    """atakebune-like silhouette: hull + deck house + square sail"""
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s); p = paint(color, a)
    c.drawPath(P((-90, -6), (100, -6), (80, 18), (-70, 18)), p)
    c.drawRect(skia.Rect(-50, -34, 50, -6), p)
    c.drawRect(skia.Rect(-30, -50, 30, -34), p)
    c.drawLine(0, -50, 0, -150, paint(color, a, stroke=4))
    if sail is not None:
        c.drawRect(skia.Rect(-40, -146, 40, -66), paint(sail, a))
        for k in range(1, 4): c.drawLine(-40, -146 + k * 20, 40, -146 + k * 20, paint(color, a * 0.5, stroke=1.5))
    c.restore()

def bale(c, x, y, s=1.0, a=1.0, color=(206, 170, 96)):
    """rice bale (tawara) icon"""
    if a <= 0: return
    r = skia.RRect.MakeRectXY(skia.Rect(x - 46 * s, y - 26 * s, x + 46 * s, y + 26 * s), 24 * s, 24 * s)
    c.drawRRect(r, paint(color, a)); c.drawRRect(r, paint((90, 66, 30), a, stroke=2.5 * s))
    for k in (-26, 0, 26):
        c.drawLine(x + k * s, y - 26 * s, x + k * s, y + 26 * s, paint((110, 80, 36), a, stroke=3 * s))

def katana(c, x, y, L, ang, a=1.0, color=(200, 204, 210), tsuka=(40, 30, 24), glow=0.0):
    if a <= 0: return
    c.save(); c.translate(x, y); c.rotate(ang)
    blade = skia.Path(); blade.moveTo(0, -3); blade.quadTo(L * 0.5, -10, L, -14); blade.lineTo(L * 0.96, -6)
    blade.quadTo(L * 0.5, 2, 0, 4); blade.close()
    if glow > 0: c.drawPath(blade, paint((255, 150, 60), glow * a, blur=10))
    c.drawPath(blade, paint(color, a))
    c.drawRect(skia.Rect(-L * 0.28, -5, 0, 5), paint(tsuka, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-4, -12, 4, 12), 2, 2), paint((150, 120, 60), a))
    c.restore()

def hoe(c, x, y, s=1.0, a=1.0, ang=0.0):
    """kuwa (hoe): long handle + blade"""
    if a <= 0: return
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    c.drawLine(0, 0, 0, -420, paint((120, 86, 50), a, stroke=14))
    c.drawLine(-3, 0, -3, -420, paint((160, 120, 72), a * 0.6, stroke=3))
    c.drawPath(P((-8, -400), (-150, -380), (-160, -330), (-10, -360)), paint((120, 122, 126), a))
    c.drawPath(P((-8, -400), (-150, -380), (-152, -372), (-10, -392)), paint((190, 192, 196), a * 0.8))
    c.restore()

def paper_bg(c, warm=1.0, dark=0.0):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.45), 1250,
                                  [col(tuple(int(v * (1 - dark)) for v in (78, 66, 48))), col(tuple(int(v * (1 - dark)) for v in (22, 17, 12)))]))
    c.drawRect(skia.Rect(0, 0, W, H), p)

def scroll_doc(c, x0, y0, w, h, a=1.0, paper=PAPERL):
    if a <= 0: return
    c.drawRect(skia.Rect(x0 + 10, y0 + 18, x0 + w + 10, y0 + h + 18), paint(INK, 0.5 * a, blur=20))
    pp = skia.Paint(AntiAlias=True)
    pp.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x0 + w, y0 + h)], [col(paper, a), col(PAPERD, a)]))
    c.drawRect(skia.Rect(x0, y0, x0 + w, y0 + h), pp)
    c.drawRect(skia.Rect(x0 - 14, y0 - 6, x0 + 8, y0 + h + 6), paint((70, 46, 30), a))
    c.drawRect(skia.Rect(x0 + w - 8, y0 - 6, x0 + w + 14, y0 + h + 6), paint((70, 46, 30), a))

def ink_text(c, s, x, y, size, a=1.0, face="tcbk", color=(30, 24, 18)):
    text(c, s, x, y, size, face, color, a, "c")

def vcol(c, s, x, y, size, a=1.0, color=(30, 24, 18), face="tcbk", lh=1.12):
    for i, ch in enumerate(s):
        if ch in "、，。":
            text(c, ch, x + size * 0.34, y + i * size * lh + size * 0.40, size * 0.9, face, color, a, "c")
        else:
            text(c, ch, x, y + (i + 0.88) * size * lh, size, face, color, a, "c")

def grid_field(c, x0, y0, cols_, rows_, cw, ch, a=1.0, color=(120, 150, 90), line=(40, 34, 26), prog=1.0, persp=0.0):
    for r in range(rows_):
        for k in range(cols_):
            i = r * cols_ + k
            if i > prog * cols_ * rows_: continue
            sh = 0.85 + 0.15 * math.sin(i * 1.7)
            cc = tuple(int(v * sh) for v in color)
            c.drawRect(skia.Rect(x0 + k * cw + 3, y0 + r * ch + 3, x0 + (k + 1) * cw - 3, y0 + (r + 1) * ch - 3), paint(cc, a))
    c.drawRect(skia.Rect(x0, y0, x0 + cols_ * cw, y0 + rows_ * ch), paint(line, a * 0.8, stroke=3))

def stars(c, t, a=1.0, n=90, seed=4, ymax=900):
    rng = np.random.default_rng(seed)
    for i in range(n):
        x = rng.uniform(0, W); y = rng.uniform(0, ymax); r = rng.uniform(0.8, 2.2)
        tw = 0.6 + 0.4 * math.sin(t * rng.uniform(0.5, 2) + i)
        c.drawCircle(x, y, r, paint((230, 230, 240), a * tw * rng.uniform(0.3, 0.9)))

def fire(c, x, y, s, t, a=1.0, seed=0):
    """bonfire flicker"""
    if a <= 0: return
    c.drawCircle(x, y - 10 * s, 90 * s, paint((255, 140, 50), 0.22 * a, blur=40 * s))
    for k in range(5):
        ph = t * (7 + k) + seed * 2.3 + k
        hh = (40 + 18 * math.sin(ph)) * s; ww = (14 - k * 1.5) * s
        ox = math.sin(ph * 0.7) * 5 * s + (k - 2) * 6 * s
        col_ = [(255, 220, 140), (255, 170, 70), (240, 110, 40), (255, 190, 90), (230, 90, 30)][k]
        c.drawPath(P((x + ox - ww, y), (x + ox + ww, y), (x + ox + math.sin(ph) * 4 * s, y - hh)), paint(col_, a * 0.85))
