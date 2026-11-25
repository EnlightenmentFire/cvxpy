# -*- coding: utf-8 -*-
"""Drawing primitives for the vertical 1080x1920 frame (PIL RGBA)."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
NOTO = "/usr/share/fonts/opentype/noto/"
SERIF_B = (NOTO + "NotoSerifCJK-Bold.ttc", 2)
SERIF = (NOTO + "NotoSerifCJK-Regular.ttc", 2)
SANS = (NOTO + "NotoSansCJK-Regular.ttc", 2)
SANS_B = (NOTO + "NotoSansCJK-Bold.ttc", 2)
EN_SERIF_I = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 0)
EN_SERIF = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", 0)
EN_SERIF_B = ("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 0)

# palette
NAVY = (12, 18, 30)
NAVY2 = (22, 32, 50)
GOLD = (214, 172, 88)
GOLD_L = (240, 210, 140)
IVORY = (238, 228, 205)
WHITE = (248, 246, 240)
RED = (200, 52, 42)          # company (warm)
RED_L = (236, 98, 70)
BLUE = (64, 120, 196)        # nawab (cool)
BLUE_L = (120, 170, 235)
GREY = (140, 140, 140)
GREEN = (70, 110, 70)
SEA = (14, 34, 52)
LAND = (64, 58, 44)
LAND_L = (92, 82, 60)
INK = (30, 24, 18)
PARCH = (226, 206, 164)


@functools.lru_cache(maxsize=256)
def font(spec, size):
    path, idx = spec
    return ImageFont.truetype(path, int(size), index=idx)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def clamp01(x):
    return min(1.0, max(0.0, x))


def ramp(t, t0, dur):
    """0 before t0, eases to 1 over dur."""
    if t is None or t < t0:
        return 0.0
    return ease((t - t0) / max(dur, 1e-6))


def lerp(a, b, x):
    return a + (b - a) * x


def lerp_c(c1, c2, x):
    return tuple(int(round(a + (b - a) * x)) for a, b in zip(c1, c2))


def new(color=(0, 0, 0, 0), size=(W, H)):
    return Image.new("RGBA", size, color)


def fade(layer, a):
    """Return layer with alpha multiplied by a (0..1)."""
    if a >= 0.999:
        return layer
    if a <= 0.001:
        return None
    r, g, b, al = layer.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))


def comp(base, layer, a=1.0, xy=(0, 0)):
    """alpha-composite layer onto base in place (layer may be smaller, placed at xy)."""
    if layer is None:
        return base
    l = fade(layer, a)
    if l is None:
        return base
    if l.size == base.size and xy == (0, 0):
        base.alpha_composite(l)
    else:
        x, y = int(round(xy[0])), int(round(xy[1]))
        base.alpha_composite(l, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    return base


def glow(layer, radius=8, strength=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = fade(g, strength) if strength < 1 else g
    out = new(size=layer.size)
    out.alpha_composite(g)
    if strength > 1:
        out.alpha_composite(g)
    out.alpha_composite(layer)
    return out


# ------------------------------------------------------------------ backgrounds

@functools.lru_cache(maxsize=8)
def noise_tex(seed=0, size=(W, H), scale=1.0):
    rng = np.random.default_rng(seed)
    small = rng.random((size[1] // 8 + 1, size[0] // 8 + 1)).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8), "L").resize(size, Image.BICUBIC)
    fine = Image.fromarray((rng.random((size[1], size[0])) * 255).astype(np.uint8), "L")
    return Image.blend(im, fine, 0.35)


def vignette_mask(strength=0.75, size=(W, H)):
    w, h = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = (x - w / 2) / (w / 2)
    dy = (y - h / 2) / (h / 2)
    d = np.sqrt(dx * dx * 1.0 + dy * dy * 0.8)
    v = np.clip((d - 0.55) / 0.8, 0, 1) ** 1.6 * strength
    return Image.fromarray((v * 255).astype(np.uint8), "L")


@functools.lru_cache(maxsize=16)
def bg(top=NAVY2, bottom=NAVY, tint=None, vig=0.8, seed=0):
    """Dark gradient with soft paper noise and vignette."""
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    c1 = np.array(top, np.float32)[None, None]
    c2 = np.array(bottom, np.float32)[None, None]
    arr = c1 * (1 - y) + c2 * y
    arr = np.repeat(arr, W, axis=1)
    n = np.asarray(noise_tex(seed), np.float32)[..., None] / 255.0
    arr = arr * (0.92 + 0.16 * n)
    if tint is not None:
        # soft radial glow in tint colour near the upper third
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / 700) ** 2 + ((yy - 760) / 760) ** 2)
        g = np.clip(1 - d, 0, 1)[..., None] ** 2
        arr = arr + np.array(tint, np.float32)[None, None] * g * 0.35
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    if vig:
        black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        black.putalpha(vignette_mask(vig))
        img.alpha_composite(black)
    return img


def bg_copy(*a, **k):
    return bg(*a, **k).copy()


# ------------------------------------------------------------------ text

def text_size(s, f):
    b = f.getbbox(s)
    return b[2] - b[0], b[3] - b[1]


def _tokens(s):
    import re
    return re.findall(r"[A-Za-z0-9.,%+–\-·:']+(?:\s[A-Za-z][A-Za-z.]*)*[年月日万人]?|\n|.", s)


def wrap_cjk(s, f, maxw):
    lines, cur = [], ""
    for tok in _tokens(s):
        if tok == "\n":
            lines.append(cur); cur = ""; continue
        if f.getlength(cur + tok) > maxw and cur:
            if tok in "，。、；：？！”』）》,.;:?!)":
                cur += tok; continue
            lines.append(cur); cur = tok.lstrip()
        else:
            cur += tok
    if cur:
        lines.append(cur)
    return lines


def balance_cjk(s, f, maxw):
    lines = wrap_cjk(s, f, maxw)
    if len(lines) <= 1:
        return lines
    n = len(lines)
    lo, hi = maxw * 0.5, maxw
    best = lines
    for _ in range(14):
        mid = (lo + hi) / 2
        l2 = wrap_cjk(s, f, mid)
        if len(l2) <= n:
            best, hi = l2, mid
        else:
            lo = mid
    return best


def wrap_words(s, f, maxw):
    words, lines, cur = s.split(" "), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getlength(t) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def draw_text(img, xy, s, f, fill=WHITE, anchor="mm", shadow=0.6, stroke=0, stroke_fill=(0, 0, 0), alpha=1.0, spacing=0):
    """Draw text with soft shadow onto img (RGBA) in place."""
    if alpha <= 0.01 or not s:
        return img
    layer = new(size=img.size)
    d = ImageDraw.Draw(layer)
    if shadow:
        sh = new(size=img.size)
        ds = ImageDraw.Draw(sh)
        ds.text((xy[0] + 3, xy[1] + 4), s, font=f, fill=(0, 0, 0, int(255 * shadow)), anchor=anchor,
                stroke_width=stroke + 3, stroke_fill=(0, 0, 0, int(255 * shadow)))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        layer.alpha_composite(sh)
    col = fill if len(fill) == 4 else fill + (255,)
    d.text(xy, s, font=f, fill=col, anchor=anchor, stroke_width=stroke,
           stroke_fill=stroke_fill if stroke else None)
    return comp(img, layer, alpha)


class TextLayer:
    """Accumulate text items on one layer (one shadow blur for all)."""
    def __init__(self, size=(W, H)):
        self.size = size
        self.items = []

    def add(self, xy, s, f, fill=WHITE, anchor="mm", stroke=0, stroke_fill=(0, 0, 0)):
        self.items.append((xy, s, f, fill, anchor, stroke, stroke_fill))
        return self

    def render(self, shadow=0.6, blur=5):
        layer = new(size=self.size)
        if shadow:
            sh = new(size=self.size)
            ds = ImageDraw.Draw(sh)
            for (xy, s, f, fill, anchor, stroke, sf) in self.items:
                ds.text((xy[0] + 3, xy[1] + 4), s, font=f, fill=(0, 0, 0, int(255 * shadow)), anchor=anchor,
                        stroke_width=stroke + 3, stroke_fill=(0, 0, 0, int(255 * shadow)))
            layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
        d = ImageDraw.Draw(layer)
        for (xy, s, f, fill, anchor, stroke, sf) in self.items:
            col = fill if len(fill) == 4 else tuple(fill) + (255,)
            d.text(xy, s, font=f, fill=col, anchor=anchor, stroke_width=stroke, stroke_fill=sf if stroke else None)
        return layer


# ------------------------------------------------------------------ geometry

def bezier(p0, p1, p2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def polyline_len(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def cut_polyline(pts, frac):
    if frac >= 1:
        return pts
    total = polyline_len(pts) * max(frac, 0)
    out = [pts[0]]
    acc = 0
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + L >= total:
            r = (total - acc) / max(L, 1e-6)
            out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r))
            return out
        out.append(b)
        acc += L
    return out


def point_at(pts, frac):
    c = cut_polyline(pts, frac)
    return c[-1]


def thick_arrow(pts, width, color, head=2.4, prog=1.0, taper=True, outline=None, glow_r=0):
    """Return an RGBA layer with a fat curved arrow along pts drawn to fraction prog."""
    layer = new()
    if prog <= 0.01 or len(pts) < 2:
        return layer
    p = cut_polyline(pts, prog)
    if len(p) < 2:
        return layer
    hl = width * head
    # shorten shaft for head
    total = polyline_len(p)
    shaft = cut_polyline(p, max(0.0, (total - hl * 0.8) / max(total, 1)))
    left, right = [], []
    n = len(shaft)
    for i, (x, y) in enumerate(shaft):
        a = shaft[max(0, i - 1)]; b = shaft[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = width / 2 * ((0.55 + 0.45 * i / max(n - 1, 1)) if taper else 1)
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    tip = p[-1]
    base = shaft[-1]
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    hw = width * 1.25
    headpoly = [(base[0] + nx * hw, base[1] + ny * hw), (tip[0] + ux * 4, tip[1] + uy * 4), (base[0] - nx * hw, base[1] - ny * hw)]
    poly = left + headpoly + right[::-1]
    d = ImageDraw.Draw(layer)
    col = color if len(color) == 4 else tuple(color) + (235,)
    if outline:
        d.polygon(poly, fill=col, outline=outline)
        d.line(poly + [poly[0]], fill=outline, width=3)
    else:
        d.polygon(poly, fill=col)
    if glow_r:
        layer = glow(layer, glow_r)
    return layer


def dashed_line(d, pts, color, width=3, dash=14, gap=10, prog=1.0):
    p = cut_polyline(pts, prog)
    acc = 0
    on = True
    seg = [p[0]]
    for a, b in zip(p, p[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        pos = 0
        while pos < L:
            lim = dash if on else gap
            step = min(lim - acc, L - pos)
            pos += step; acc += step
            pt = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
            if on:
                seg.append(pt)
            if acc >= lim:
                if on and len(seg) > 1:
                    d.line(seg, fill=color, width=width)
                on = not on; acc = 0; seg = [pt]
    if on and len(seg) > 1:
        d.line(seg, fill=color, width=width)


def rounded_panel(size, radius=24, fill=(10, 14, 22, 215), outline=GOLD, width=2):
    im = new(size=size)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((1, 1, size[0] - 2, size[1] - 2), radius=radius, fill=fill,
                        outline=(tuple(outline) + (200,)) if outline else None, width=width)
    return im


def gold_rule(d, cx, y, half, color=GOLD, dots=True, width=2):
    d.line((cx - half, y, cx - 18, y), fill=color, width=width)
    d.line((cx + 18, y, cx + half, y), fill=color, width=width)
    if dots:
        d.regular_polygon((cx, y, 7), 4, rotation=45, fill=color)


# ------------------------------------------------------------------ parchment

@functools.lru_cache(maxsize=8)
def parchment(w, h, seed=3, tone=PARCH):
    rng = np.random.default_rng(seed)
    n = np.asarray(noise_tex(seed, (w, h)), np.float32) / 255.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]) / 60.0
    edge = np.clip(edge, 0, 1)
    base = np.array(tone, np.float32)[None, None] * (0.86 + 0.18 * n[..., None])
    base = base * (0.62 + 0.38 * edge[..., None])
    stains = np.asarray(noise_tex(seed + 7, (w, h)), np.float32) / 255.0
    base *= (0.95 + 0.08 * (stains[..., None] - 0.5))
    a = (np.clip(edge * 3, 0, 1) * 255).astype(np.uint8)
    rough = (np.asarray(noise_tex(seed + 11, (w, h)), np.float32) / 255.0)
    a = np.where(edge * 60 < 6 + rough * 10, 0, 255).astype(np.uint8)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    img.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(1.2)))
    return img


def wax_seal(r=70, color=(150, 28, 24)):
    s = int(r * 2.6)
    im = new(size=(s, s))
    d = ImageDraw.Draw(im)
    c = s / 2
    rng = np.random.default_rng(4)
    pts = []
    for i in range(48):
        a = i / 48 * 2 * math.pi
        rr = r * (1.08 + 0.08 * rng.random())
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    d.polygon(pts, fill=color + (255,))
    d.ellipse((c - r * 0.78, c - r * 0.78, c + r * 0.78, c + r * 0.78), outline=(110, 16, 14, 255), width=5)
    d.ellipse((c - r * 0.62, c - r * 0.62, c + r * 0.62, c + r * 0.62), fill=(170, 40, 32, 255))
    f = font(EN_SERIF_B, r * 0.7)
    d.text((c, c + 2), "ER", font=f, fill=(105, 14, 12, 255), anchor="mm")
    hl = new(size=(s, s))
    ImageDraw.Draw(hl).ellipse((c - r * 0.7, c - r * 0.85, c + r * 0.1, c - r * 0.1), fill=(255, 200, 180, 50))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(10)))
    sh = new(size=(s + 30, s + 30))
    sh.alpha_composite(Image.new("RGBA", (s, s), (0, 0, 0, 0)), (15, 20))
    return im


# ------------------------------------------------------------------ icons / silhouettes

def soldier(d, x, y, h, color, gun=True):
    """Simple standing soldier silhouette at feet position (x, y) with height h."""
    w = h * 0.28
    hd = h * 0.13
    d.ellipse((x - hd, y - h, x + hd, y - h + 2 * hd), fill=color)          # head
    d.polygon([(x - w / 2, y - h + 2 * hd), (x + w / 2, y - h + 2 * hd), (x + w * 0.4, y - h * 0.42),
               (x - w * 0.4, y - h * 0.42)], fill=color)                     # torso
    d.line((x - w * 0.2, y - h * 0.45, x - w * 0.25, y), fill=color, width=max(2, int(w * 0.32)))
    d.line((x + w * 0.2, y - h * 0.45, x + w * 0.25, y), fill=color, width=max(2, int(w * 0.32)))
    if gun:
        d.line((x + w * 0.45, y - h * 0.55, x + w * 0.6, y - h * 1.25), fill=color, width=max(2, int(w * 0.14)))


def elephant(d, x, y, s, color, howdah=None):
    """Elephant silhouette facing left, feet at y, s ~ body length."""
    c = color
    bw, bh = s, s * 0.6
    top = y - bh * 1.45
    d.ellipse((x - bw * 0.5, top, x + bw * 0.5, top + bh * 1.0), fill=c)                       # body
    d.ellipse((x - bw * 0.72, top + bh * 0.02, x - bw * 0.3, top + bh * 0.62), fill=c)         # head
    d.ellipse((x - bw * 0.5, top + bh * 0.05, x - bw * 0.16, top + bh * 0.7), fill=c)          # ear
    trunk = [(x - bw * 0.66, top + bh * 0.45), (x - bw * 0.8, top + bh * 0.75), (x - bw * 0.82, top + bh * 1.1),
             (x - bw * 0.76, top + bh * 1.35)]
    d.line(trunk, fill=c, width=max(3, int(s * 0.09)), joint="curve")
    d.line([(x - bw * 0.64, top + bh * 0.62), (x - bw * 0.78, top + bh * 0.78)], fill=(200, 190, 165, 255), width=max(2, int(s * 0.025)))
    for lx in (-0.36, -0.18, 0.16, 0.34):
        d.rounded_rectangle((x + bw * lx - bw * 0.075, top + bh * 0.7, x + bw * lx + bw * 0.075, y), radius=int(s * 0.03), fill=c)
    d.line((x + bw * 0.48, top + bh * 0.35, x + bw * 0.56, top + bh * 0.85), fill=c, width=max(2, int(s * 0.025)))
    if howdah:
        hx0, hx1 = x - bw * 0.2, x + bw * 0.24
        hy = top - bh * 0.05
        d.rectangle((hx0, hy - bh * 0.28, hx1, hy + bh * 0.05), fill=howdah)
        d.pieslice((hx0 - bw * 0.02, hy - bh * 0.62, hx1 + bw * 0.02, hy - bh * 0.02), 180, 360, fill=howdah)
        d.line((x + bw * 0.02, hy - bh * 0.62, x + bw * 0.02, hy - bh * 0.78), fill=howdah, width=max(2, int(s * 0.02)))
        d.rectangle((x - bw * 0.42, top + bh * 0.08, x + bw * 0.36, top + bh * 0.3), fill=tuple(min(255, int(v * 1.6)) for v in howdah[:3]) + (255,))


def cannon(d, x, y, s, color, facing=1):
    """Field gun, wheel at (x,y)."""
    r = s * 0.28
    d.ellipse((x - r, y - r, x + r, y + r), outline=color, width=max(2, int(s * 0.06)))
    d.line((x - facing * s * 0.6, y + r * 0.6, x + facing * s * 0.1, y), fill=color, width=max(2, int(s * 0.08)))
    d.line((x - facing * s * 0.1, y - s * 0.05, x + facing * s * 0.75, y - s * 0.3), fill=color, width=max(3, int(s * 0.17)))


def tree(d, x, y, s, color, rng):
    """Rounded mango-tree silhouette with trunk; base at (x,y)."""
    d.rectangle((x - s * 0.05, y - s * 0.45, x + s * 0.05, y), fill=color)
    for _ in range(7):
        ox = (rng.random() - 0.5) * s * 0.8
        oy = -s * 0.55 - rng.random() * s * 0.45
        r = s * (0.25 + rng.random() * 0.18)
        d.ellipse((x + ox - r, y + oy - r * 0.85, x + ox + r, y + oy + r * 0.85), fill=color)


def camel(d, x, y, s, color):
    d.ellipse((x - s * 0.45, y - s * 0.95, x + s * 0.35, y - s * 0.5), fill=color)
    d.ellipse((x - s * 0.2, y - s * 1.15, x + s * 0.12, y - s * 0.75), fill=color)    # hump
    d.line((x + s * 0.3, y - s * 0.75, x + s * 0.55, y - s * 1.25), fill=color, width=max(3, int(s * 0.12)))
    d.ellipse((x + s * 0.48, y - s * 1.36, x + s * 0.75, y - s * 1.18), fill=color)
    for lx in (-0.35, -0.2, 0.15, 0.28):
        d.line((x + s * lx, y - s * 0.6, x + s * lx * 1.1, y), fill=color, width=max(2, int(s * 0.07)))
    # rider
    d.ellipse((x - s * 0.14, y - s * 1.55, x + s * 0.04, y - s * 1.37), fill=color)
    d.polygon([(x - s * 0.18, y - s * 1.38), (x + s * 0.08, y - s * 1.38), (x + s * 0.05, y - s * 1.08), (x - s * 0.15, y - s * 1.08)], fill=color)


def ship(d, x, y, s, hull=(40, 30, 22, 255), sail=(230, 220, 195, 255)):
    """East Indiaman silhouette, waterline centre (x,y), length s."""
    d.polygon([(x - s * 0.5, y - s * 0.12), (x + s * 0.5, y - s * 0.16), (x + s * 0.38, y + s * 0.04), (x - s * 0.4, y + s * 0.04)], fill=hull)
    for mx, mh in ((-0.22, 0.62), (0.05, 0.75), (0.3, 0.55)):
        d.line((x + s * mx, y - s * 0.12, x + s * mx, y - s * mh), fill=hull, width=max(2, int(s * 0.02)))
        for k, wv in ((0.0, 0.2), (0.22, 0.17)):
            top = y - s * mh + s * k * mh * 0.9 + s * 0.04
            hh = s * mh * 0.3
            d.polygon([(x + s * mx - s * wv / 2, top), (x + s * mx + s * wv / 2, top),
                       (x + s * mx + s * wv / 2 * 1.1, top + hh), (x + s * mx - s * wv / 2 * 1.1, top + hh)], fill=sail)
    d.line((x + s * 0.5, y - s * 0.16, x + s * 0.72, y - s * 0.34), fill=hull, width=max(2, int(s * 0.015)))
    d.polygon([(x - s * 0.22, y - s * 0.72), (x - s * 0.22, y - s * 0.66), (x - s * 0.1, y - s * 0.69)], fill=(200, 40, 40, 255))


def coin(d, x, y, r, color=GOLD, edge=(120, 90, 40)):
    d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(color) + (255,), outline=tuple(edge) + (255,), width=max(1, int(r * 0.12)))
    d.ellipse((x - r * 0.68, y - r * 0.68, x + r * 0.68, y + r * 0.68), outline=tuple(edge) + (200,), width=max(1, int(r * 0.07)))


def person_bust(d, cx, cy, s, color, hat=None):
    """Simple bust silhouette (head + shoulders) centred at (cx, cy)."""
    d.ellipse((cx - s * 0.22, cy - s * 0.62, cx + s * 0.22, cy - s * 0.1), fill=color)
    d.chord((cx - s * 0.5, cy - s * 0.05, cx + s * 0.5, cy + s * 0.75), 180, 360, fill=color)
    if hat == "turban":
        d.ellipse((cx - s * 0.27, cy - s * 0.78, cx + s * 0.27, cy - s * 0.42), fill=color)
        d.ellipse((cx - s * 0.05, cy - s * 0.9, cx + s * 0.07, cy - s * 0.74), fill=color)
    elif hat == "tricorn":
        d.polygon([(cx - s * 0.34, cy - s * 0.5), (cx, cy - s * 0.78), (cx + s * 0.34, cy - s * 0.5), (cx, cy - s * 0.56)], fill=color)
    elif hat == "wig":
        d.ellipse((cx - s * 0.3, cy - s * 0.6, cx - s * 0.12, cy - s * 0.2), fill=color)
        d.ellipse((cx + s * 0.12, cy - s * 0.6, cx + s * 0.3, cy - s * 0.2), fill=color)


def to_rgb(img):
    return img.convert("RGB")
