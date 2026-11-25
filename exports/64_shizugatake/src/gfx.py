# -*- coding: utf-8 -*-
"""skia drawing helpers: fonts, text, arrows, markers, particles, map camera."""
import math, json, random
import numpy as np
import skia

W, H = 1080, 1920
FD = "/tmp/claude-0/work/fonts"
BASE = "/tmp/claude-0/work/base"

TF = {
    "serif": skia.Typeface.MakeFromFile(f"{FD}/OTF/SimplifiedChinese/SourceHanSerifSC-Bold.otf"),
    "heavy": skia.Typeface.MakeFromFile(f"{FD}/OTF/SimplifiedChinese/SourceHanSerifSC-Heavy.otf"),
    "semi": skia.Typeface.MakeFromFile(f"{FD}/OTF/SimplifiedChinese/SourceHanSerifSC-SemiBold.otf"),
    "brush": skia.Typeface.MakeFromFile(f"{FD}/MaShanZheng-Regular.ttf"),
    "sans": skia.Typeface.MakeFromFile(f"{FD}/NotoSansCJKsc-Bold.otf"),
    "sansm": skia.Typeface.MakeFromFile(f"{FD}/NotoSansCJKsc-Medium.otf"),
}
_fonts = {}


def font(name, size):
    k = (name, int(size))
    if k not in _fonts:
        f = skia.Font(TF[name], int(size)); f.setSubpixel(True); f.setEdging(skia.Font.Edging.kAntiAlias)
        _fonts[k] = f
    return _fonts[k]


# palette
RED = (214, 58, 38)        # 羽柴 朱红
RED_HI = (255, 120, 80)
BLUE = (70, 120, 210)      # 柴田 冷蓝
BLUE_HI = (140, 185, 255)
LBLUE = (150, 210, 240)    # 前田 浅蓝
GOLD = (232, 196, 120)
INK = (16, 14, 12)
PAPER = (236, 226, 204)
WHITE = (250, 246, 238)


def col(c, a=1.0):
    return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, max(0.0, min(1.0, a)))


def paint(c, a=1.0, stroke=None, blur=None, aa=True, cap=None, join=None, blend=None):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(col(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap); p.setStrokeJoin(join or skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend:
        p.setBlendMode(blend)
    return p


# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x); return x ** 3


def ev(t, t0, d=0.6, f=ease):
    return f((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def fio(t, t0, t1, d=0.5):
    """fade in at t0, out at t1"""
    return min(ev(t, t0, d), 1 - ev(t, t1 - d, d))


def lerp(a, b, x):
    return a + (b - a) * x


def mix(c1, c2, x):
    return tuple(lerp(c1[i], c2[i], x) for i in range(3))


# ---------------- text ----------------
def text(c, s, x, y, size, face="serif", color=WHITE, a=1.0, align="c", stroke=0, scolor=INK, sa=0.85,
         shadow=0, spacing=0.0):
    if a <= 0.003 or not s:
        return 0
    f = font(face, size)
    if face == "brush":
        s = s.replace("·", "  ")
        g = f.textToGlyphs(s)
        if any(int(x) == 0 and ch != " " for x, ch in zip(g, s)):
            # per-char fallback to a heavy serif for glyphs missing in the brush font
            fb = font("heavy", size * 0.92)
            ws = [(f if int(x) else fb).measureText(ch) for x, ch in zip(g, s)]
            tw = sum(ws); xx = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
            for (x_, ch), w_ in zip(zip(g, s), ws):
                text(c, ch, xx + w_ / 2, y, size if int(x_) else size * 0.92, face if int(x_) else "heavy", color, a, "c", stroke, scolor, sa, shadow)
                xx += w_
            return tw
    if spacing:
        widths = [f.measureText(ch) + spacing * size for ch in s]
        tw = sum(widths) - spacing * size
    else:
        tw = f.measureText(s)
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)

    def draw(p):
        if spacing:
            xx = x0
            for ch, w_ in zip(s, widths):
                c.drawString(ch, xx, y, f, p); xx += w_
        else:
            c.drawString(s, x0, y, f, p)
    if shadow:
        draw(paint(INK, a * 0.7, blur=shadow))
    if stroke:
        draw(paint(scolor, a * sa, stroke=stroke))
    draw(paint(color, a))
    return tw


def measure(s, size, face="serif"):
    return font(face, size).measureText(s)


def vtext(c, s, x, y, size, face="brush", color=WHITE, a=1.0, gap=1.05, stroke=0, shadow=0):
    """vertical text, top at y, centered on x"""
    for i, ch in enumerate(s):
        text(c, ch, x, y + size * (i + 0.88) * gap, size, face, color, a, "c", stroke=stroke, shadow=shadow)


def wrap(s, size, maxw, face="serif"):
    out, cur = [], ""
    for ch in s:
        if measure(cur + ch, size, face) > maxw and cur:
            out.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


# ---------------- shapes ----------------
def rrect(c, x, y, w, h, r, color, a=1.0, stroke=None, blur=None):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint(color, a, stroke=stroke, blur=blur))


def vgrad(c, y0, y1, c0, a0, c1, a1, x0=0, x1=W):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [col(c0, a0), col(c1, a1)]))
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y1), p)


def radial(c, x, y, r, color, a=1.0, a1=0.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((x, y), max(r, 1), [col(color, a), col(color, a1)]))
    c.drawCircle(x, y, r, p)


def vignette(c, strength=0.75):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), H * 0.62, [col(INK, 0), col(INK, 0), col(INK, strength)], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def catmull(pts, n=16):
    if len(pts) < 3:
        out = []
        for i in range(n * (len(pts) - 1) + 1):
            u = i / n; k = min(int(u), len(pts) - 2); f = u - k
            out.append((lerp(pts[k][0], pts[k + 1][0], f), lerp(pts[k][1], pts[k + 1][1], f)))
        return out
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                    (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in range(2)))
    out.append(pts[-1])
    return out


def cut(poly, frac):
    """sub-polyline from start up to fraction of length"""
    if frac <= 0:
        return [poly[0]]
    L = [0.0]
    for i in range(1, len(poly)):
        L.append(L[-1] + math.dist(poly[i - 1], poly[i]))
    tgt = L[-1] * clamp(frac)
    out = [poly[0]]
    for i in range(1, len(poly)):
        if L[i] >= tgt:
            f = (tgt - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
            out.append((lerp(poly[i - 1][0], poly[i][0], f), lerp(poly[i - 1][1], poly[i][1], f)))
            return out
        out.append(poly[i])
    return out


def plen(poly):
    return sum(math.dist(poly[i - 1], poly[i]) for i in range(1, len(poly)))


def at(poly, frac):
    s = cut(poly, frac)
    p = s[-1]
    q = s[-2] if len(s) > 1 else poly[1]
    if len(s) == 1:
        q = poly[0]; p = poly[1]
        return poly[0], math.atan2(p[1] - q[1], p[0] - q[0])
    return p, math.atan2(p[1] - q[1], p[0] - q[0])


def arrow(c, pts, prog, width, color, a=1.0, glow=True, head=2.3, smooth=True, dash=None, hi=None, taper=True):
    """thick campaign arrow growing along pts (screen coords)"""
    if prog <= 0.001 or a <= 0.003:
        return
    poly = catmull(pts) if smooth else pts
    seg = cut(poly, prog)
    if len(seg) < 2:
        return
    end, ang = seg[-1], math.atan2(seg[-1][1] - seg[-2][1], seg[-1][0] - seg[-2][0])
    hl = width * head
    # stop body before head
    tot = plen(seg)
    body = cut(seg, max(0.0, (tot - hl * 0.6) / max(tot, 1e-6)))
    path = skia.Path()
    path.moveTo(*body[0])
    for p in body[1:]:
        path.lineTo(*p)
    hpath = skia.Path()
    hx, hy = end
    ca, sa_ = math.cos(ang), math.sin(ang)
    hpath.moveTo(hx + ca * hl * 0.25, hy + sa_ * hl * 0.25)
    hpath.lineTo(hx - ca * hl + -sa_ * hl * 0.62, hy - sa_ * hl + ca * hl * 0.62)
    hpath.lineTo(hx - ca * hl * 0.72, hy - sa_ * hl * 0.72)
    hpath.lineTo(hx - ca * hl - -sa_ * hl * 0.62, hy - sa_ * hl - ca * hl * 0.62)
    hpath.close()
    if glow:
        c.drawPath(path, paint(color, a * 0.55, stroke=width * 1.9, blur=width * 0.9))
        c.drawPath(hpath, paint(color, a * 0.55, blur=width * 0.7))
    c.drawPath(path, paint(INK, a * 0.5, stroke=width + 6))
    p = paint(color, a, stroke=width)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    c.drawPath(path, p)
    if hi:
        c.drawPath(path, paint(hi, a * 0.7, stroke=max(2, width * 0.22)))
    c.drawPath(hpath, paint(INK, a * 0.5, stroke=6))
    c.drawPath(hpath, paint(color, a))


def dashed(c, pts, prog, width, color, a=1.0, on=18, off=12, smooth=True):
    if prog <= 0.001 or a <= 0.003:
        return
    poly = catmull(pts) if smooth else pts
    seg = cut(poly, prog)
    path = skia.Path(); path.moveTo(*seg[0])
    for p in seg[1:]:
        path.lineTo(*p)
    p = paint(color, a, stroke=width); p.setPathEffect(skia.DashPathEffect.Make([on, off], 0))
    c.drawPath(path, p)


def fort(c, x, y, color, a=1.0, size=30, label=None, lsize=34, lpos="r", lcolor=WHITE, state=1.0, pulse=0.0, flag=True):
    """砦 marker: square keep with flag. state<1 shrinks/greys (fallen)."""
    if a <= 0.003:
        return
    s = size
    if pulse > 0:
        c.drawCircle(x, y, s * (1.2 + 1.6 * pulse), paint(color, a * (1 - pulse) * 0.8, stroke=4))
    radial(c, x, y, s * 2.2, color, a * 0.35)
    r = skia.Rect.MakeXYWH(x - s / 2, y - s / 2, s, s)
    c.save(); c.rotate(45, x, y)
    c.drawRect(r.makeOutset(4, 4), paint(INK, a * 0.8))
    c.drawRect(r, paint(color, a))
    c.drawRect(r.makeInset(s * 0.28, s * 0.28), paint(mix(color, WHITE, 0.45), a * 0.9))
    c.restore()
    if flag:
        c.drawLine(x, y - s * 0.6, x, y - s * 1.8, paint(INK, a, stroke=4))
        fp = skia.Path(); fp.moveTo(x, y - s * 1.8); fp.lineTo(x + s * 0.9, y - s * 1.55); fp.lineTo(x, y - s * 1.3); fp.close()
        c.drawPath(fp, paint(color, a))
    if label:
        if lpos == "r":
            text(c, label, x + s * 1.1, y + lsize * 0.36, lsize, "serif", lcolor, a, "l", stroke=6)
        elif lpos == "l":
            text(c, label, x - s * 1.1, y + lsize * 0.36, lsize, "serif", lcolor, a, "r", stroke=6)
        elif lpos == "b":
            text(c, label, x, y + s + lsize, lsize, "serif", lcolor, a, "c", stroke=6)
        else:
            text(c, label, x, y - s * 2.0, lsize, "serif", lcolor, a, "c", stroke=6)


def xmark(c, x, y, s, a=1.0, color=(255, 70, 50)):
    if a <= 0:
        return
    c.drawLine(x - s, y - s, x + s, y + s, paint(INK, a, stroke=16)); c.drawLine(x - s, y + s, x + s, y - s, paint(INK, a, stroke=16))
    c.drawLine(x - s, y - s, x + s, y + s, paint(color, a, stroke=9)); c.drawLine(x - s, y + s, x + s, y - s, paint(color, a, stroke=9))


def city(c, x, y, label, a=1.0, size=12, lsize=34, lpos="r", color=PAPER):
    if a <= 0.003:
        return
    c.drawCircle(x, y, size + 4, paint(INK, a * 0.8))
    c.drawCircle(x, y, size, paint(color, a))
    c.drawCircle(x, y, size * 0.45, paint(INK, a))
    if label:
        dx = {"r": size + 10, "l": -(size + 10), "c": 0, "b": 0, "t": 0}[lpos]
        dy = {"r": lsize * 0.35, "l": lsize * 0.35, "c": lsize * 0.35, "b": size + lsize, "t": -size - 12}[lpos]
        text(c, label, x + dx, y + dy, lsize, "serif", color, a, {"r": "l", "l": "r"}.get(lpos, "c"), stroke=7)


def unit(c, x, y, color, a=1.0, w=120, h=56, label=None, lsize=32, ang=0.0):
    """army block (NATO-ish box)"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang))
    radial(c, 0, 0, w * 0.9, color, a * 0.35)
    r = skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h)
    c.drawRect(r.makeOutset(4, 4), paint(INK, a * 0.85))
    c.drawRect(r, paint(color, a))
    c.drawLine(-w / 2, -h / 2, w / 2, h / 2, paint(mix(color, WHITE, 0.6), a, stroke=3))
    c.drawLine(-w / 2, h / 2, w / 2, -h / 2, paint(mix(color, WHITE, 0.6), a, stroke=3))
    c.restore()
    if label:
        text(c, label, x, y + h / 2 + lsize + 4, lsize, "serif", WHITE, a, "c", stroke=7)


def tag(c, s, x, y, size=34, color=RED, a=1.0, fg=WHITE, face="serif", pad=16, align="c"):
    if a <= 0.003:
        return
    tw = measure(s, size, face)
    x0 = x - tw / 2 - pad if align == "c" else (x if align == "l" else x - tw - 2 * pad)
    rrect(c, x0 + 4, y - size * 0.95 + 6, tw + 2 * pad, size * 1.45, 8, INK, a * 0.6, blur=6)
    rrect(c, x0, y - size * 0.95, tw + 2 * pad, size * 1.45, 8, color, a * 0.92)
    text(c, s, x0 + pad + tw / 2, y + size * 0.05, size, face, fg, a)


def stamp(c, s, x, y, size=60, color=(200, 40, 30), a=1.0, rot=-8):
    if a <= 0.003:
        return
    c.save(); c.rotate(rot, x, y)
    tw = measure(s, size, "heavy")
    r = skia.Rect.MakeXYWH(x - tw / 2 - 18, y - size * 0.95, tw + 36, size * 1.35)
    c.drawRect(r, paint(color, a * 0.9, stroke=7))
    text(c, s, x, y + size * 0.1, size, "heavy", color, a * 0.95)
    c.restore()


# ---------------- particles ----------------
class Rng:
    def __init__(self, seed):
        self.r = random.Random(seed)

    def __call__(self, a=0.0, b=1.0):
        return self.r.uniform(a, b)


def embers(c, t, n=60, seed=1, a=1.0, area=(0, 0, W, H), color=(255, 150, 60), rise=60, size=3.0):
    R = Rng(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        px, py, sp, ph, sz = R(x0, x1), R(y0, y1), R(0.5, 1.5), R(0, 10), R(0.5, 1.5)
        life = (t * sp * 0.25 + ph) % 1.0
        y = py - life * rise * sp * 4
        x = px + math.sin(t * 1.3 + ph * 6) * 14
        if y < y0 - 50:
            continue
        al = a * math.sin(life * math.pi)
        c.drawCircle(x, y, size * sz, paint(color, al * 0.9))
        c.drawCircle(x, y, size * sz * 3, paint(color, al * 0.25, blur=size * 2))


def smoke(c, t, x, y, a=1.0, n=10, seed=2, spread=80, color=(200, 196, 186), size=40, rise=30):
    if a <= 0.003:
        return
    R = Rng(seed)
    for i in range(n):
        ph = R(0, 1); sp = R(0.6, 1.4)
        life = (t * 0.18 * sp + ph) % 1.0
        xx = x + R(-spread, spread) + life * 40 * sp
        yy = y + R(-spread * 0.4, spread * 0.4) - life * rise * 3
        r = size * (0.6 + life * 1.8) * 1.5
        radial(c, xx, yy, r, color, a * 0.30 * math.sin(life * math.pi))


def flashes(c, t, pts, a=1.0, seed=3, rate=6.0, color=(255, 220, 140), size=10):
    if a <= 0.003:
        return
    R = Rng(seed)
    for i, (x, y) in enumerate(pts):
        ph = R(0, 1); f = R(0.7, 1.3)
        v = (t * rate * f + ph) % 1.0
        if v < 0.18:
            k = 1 - v / 0.18
            c.drawCircle(x, y, size * (1 + k), paint(color, a * k))
            c.drawCircle(x, y, size * 4 * k, paint(color, a * 0.4 * k, blur=size * 2))


def fog(c, t, a=0.5, seed=4, y0=0, y1=H, color=(200, 205, 210)):
    if a <= 0.003:
        return
    R = Rng(seed)
    for i in range(14):
        x = (R(0, W * 1.6) + t * R(8, 22)) % (W * 1.6) - W * 0.3
        y = R(y0, y1)
        r = R(160, 360)
        al = a * R(0.10, 0.22)
        c.save(); c.translate(x, y); c.scale(1.8, 0.5)
        radial(c, 0, 0, r * 1.3, color, al * 1.4)
        c.restore()


def snow(c, t, a=1.0, n=140, seed=5, area=(0, 0, W, H)):
    if a <= 0.003:
        return
    R = Rng(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        px, sp, ph, sz = R(x0, x1), R(40, 110), R(0, 2000), R(1.5, 4.5)
        y = y0 + (ph + t * sp) % (y1 - y0)
        x = px + math.sin(t * 0.9 + ph) * 20
        c.drawCircle(x, y, sz, paint(WHITE, a * 0.75))


def rain(c, t, a=1.0, n=160, seed=6):
    if a <= 0.003:
        return
    R = Rng(seed)
    p = paint((170, 190, 210), a * 0.35, stroke=2)
    for i in range(n):
        px, sp, ph = R(-200, W), R(1400, 2200), R(0, 3000)
        y = (ph + t * sp) % (H + 200) - 100
        x = px + y * 0.18
        c.drawLine(x, y, x + 10, y + 46, p)


def torch(c, x, y, t, a=1.0, seed=0, s=1.0):
    if a <= 0.003:
        return
    fl = 0.75 + 0.25 * math.sin(t * 17 + seed * 3.1) * math.sin(t * 7.3 + seed)
    radial(c, x, y, 46 * s * fl, (255, 140, 40), a * 0.45)
    c.drawCircle(x, y, 7 * s * fl, paint((255, 200, 110), a))
    c.drawCircle(x, y, 3.2 * s, paint((255, 250, 220), a))


# ---------------- maps ----------------
class Basemap:
    def __init__(self, name):
        self.meta = json.load(open(f"{BASE}/{name}.json"))
        from geo import MapGeo
        self.geo = MapGeo(self.meta["z"], self.meta["x0"], self.meta["y0"], self.meta["s"])
        self.img = {}
        self.name = name

    def image(self, mode):
        if mode not in self.img:
            im = skia.Image.open(f"{BASE}/{self.name}_{mode}.png").makeRasterImage()
            self.img[mode] = im.withDefaultMipmaps()
        return self.img[mode]


class Cam:
    """world (basemap px) -> screen. cx,cy world center; z = screen px per world px; sy = screen y of center"""
    def __init__(self, cx, cy, z, sy=880):
        self.cx, self.cy, self.z, self.sy = cx, cy, z, sy

    def __call__(self, x, y):
        return (x - self.cx) * self.z + W / 2, (y - self.cy) * self.z + self.sy

    @staticmethod
    def blend(a, b, x):
        # zoom interpolated in log space
        z = math.exp(lerp(math.log(a.z), math.log(b.z), x))
        return Cam(lerp(a.cx, b.cx, x), lerp(a.cy, b.cy, x), z, lerp(a.sy, b.sy, x))


def draw_map(c, bm, cam, mode="day", a=1.0, mode2=None, k2=0.0):
    c.save()
    c.translate(W / 2 - cam.cx * cam.z, cam.sy - cam.cy * cam.z)
    c.scale(cam.z, cam.z)
    samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
    p = skia.Paint(); p.setAlphaf(a)
    c.drawImage(bm.image(mode), 0, 0, samp, p)
    if mode2 and k2 > 0.003:
        p2 = skia.Paint(); p2.setAlphaf(a * k2)
        c.drawImage(bm.image(mode2), 0, 0, samp, p2)
    c.restore()


def fit_cam(bm, names_or_pts, pad=1.25, sy=880, maxw=W * 0.84, maxh=1150):
    pts = [bm.geo.p(n) if isinstance(n, str) else bm.geo(*n) for n in names_or_pts]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    z = min(maxw / (w * pad), maxh / (h * pad))
    return Cam(cx, cy, z, sy)
