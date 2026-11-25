"""Procedural art toolkit: noise, gradients, ink silhouettes, glows, lanterns, architecture, text.
All images are 1080x1920 unless stated. Float arrays are HxWx3 in [0,1]."""
import os, math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1080, 1920
FONTS = os.environ.get("FONTS", "/tmp/claude-0/work/fonts")

# palette (Dunhuang mineral pigments + night ink)
INK = (0.055, 0.06, 0.08)
NIGHT_TOP = (0.03, 0.04, 0.08)
NIGHT_BOT = (0.10, 0.10, 0.15)
OCHRE = (0.72, 0.55, 0.33)
PAPER = (0.86, 0.80, 0.68)
CINNABAR = (0.72, 0.18, 0.12)
MALACHITE = (0.24, 0.52, 0.44)
LAPIS = (0.16, 0.26, 0.52)
GOLD = (1.0, 0.80, 0.45)
FIRE = (1.0, 0.45, 0.12)
WARM = (1.0, 0.72, 0.38)


def rng(seed):
    return np.random.default_rng(seed)


@functools.lru_cache(maxsize=64)
def _font(name, size):
    p = {"kai": "LXGWWenKai-Medium.ttf", "kai_r": "LXGWWenKai-Regular.ttf", "brush": "MaShanZheng-Regular.ttf",
         "serif": "NotoSerifCJKsc-Regular.otf", "serif_sb": "NotoSerifCJKsc-SemiBold.otf",
         "serif_b": "NotoSerifCJKsc-Bold.otf", "serif_k": "NotoSerifCJKsc-Black.otf"}[name]
    return ImageFont.truetype(os.path.join(FONTS, p), size)


def font(name, size):
    return _font(name, int(size))


# ---------------------------------------------------------------- noise & gradients
def vnoise(h, w, cell, seed):
    r = rng(seed)
    gh, gw = h // cell + 3, w // cell + 3
    g = (r.random((gh, gw)) * 255).astype(np.uint8)
    im = Image.fromarray(g).resize((gw * cell, gh * cell), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32)[cell:cell + h, cell:cell + w] / 255.0
    return a


def fbm(h, w, cell, octaves=4, seed=0, gain=0.5):
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        c = max(2, cell >> o)
        acc += amp * vnoise(h, w, c, seed + 31 * o); tot += amp; amp *= gain
    return acc / tot


def vgrad(h, w, top, bot, gamma=1.0):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** gamma
    a = np.array(top, np.float32)[None, None]; b = np.array(bot, np.float32)[None, None]
    return np.broadcast_to(a * (1 - t) + b * t, (h, w, 3)).copy()


def radial(h, w, cx, cy, r, power=2.0):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power


def gauss_blob(size, sigma_frac=0.165):
    y, x = np.mgrid[:size, :size].astype(np.float32)
    c = (size - 1) / 2
    d2 = ((x - c) ** 2 + (y - c) ** 2) / (size * sigma_frac) ** 2
    return np.exp(-d2 * 0.5).astype(np.float32)


@functools.lru_cache(maxsize=32)
def blob(size):
    return gauss_blob(size)


def add_glow(img, cx, cy, size, color, amount=1.0):
    """additive gaussian glow, in place"""
    size = int(size * 1.5)
    if size < 3:
        return
    b = blob(size)
    x0, y0 = int(cx - size / 2), int(cy - size / 2)
    x1, y1 = x0 + size, y0 + size
    h, w = img.shape[:2]
    bx0, by0 = max(0, -x0), max(0, -y0)
    bx1, by1 = size - max(0, x1 - w), size - max(0, y1 - h)
    if bx1 <= bx0 or by1 <= by0:
        return
    sub = b[by0:by1, bx0:bx1, None] * (np.array(color, np.float32) * amount)
    img[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] += sub


def screen(a, b):
    return 1 - (1 - a) * (1 - b)


def vignette(h=H, w=W, strength=0.55):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt(((x - w / 2) / (w * 0.75)) ** 2 + ((y - h / 2) / (h * 0.62)) ** 2)
    return (1 - strength * np.clip(d, 0, 1.3) ** 2.2).astype(np.float32)[..., None]


VIG = None


def finish(img, vig=0.55, grain_seed=None):
    global VIG
    if VIG is None:
        VIG = vignette()
    out = img * VIG if vig else img
    return out


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def to_pil(img):
    return Image.fromarray(to_u8(img))


def from_pil(im):
    return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0


def paper(h=H, w=W, base=PAPER, seed=3, dark=0.18):
    n = fbm(h, w, 256, 5, seed)
    fib = fbm(h, w, 8, 2, seed + 9)
    img = np.array(base, np.float32)[None, None] * (1 - dark * (n[..., None] - 0.5) * 2 - 0.06 * (fib[..., None] - 0.5))
    return np.clip(img, 0, 1)


def mist_layer(h, w, seed, cell=380):
    return fbm(h, w, cell, 4, seed)


# ---------------------------------------------------------------- masks / silhouettes (drawn at 2x)
class Mask:
    """draw at SS x supersampling into an L mask, return float mask at native res"""

    def __init__(self, w=W, h=H, ss=2):
        self.ss = ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def P(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def ell(self, cx, cy, rx, ry, fill=255):
        s = self.ss
        self.d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=fill)

    def poly(self, pts, fill=255):
        self.d.polygon(self.P(pts), fill=fill)

    def line(self, pts, width, fill=255):
        self.d.line(self.P(pts), fill=fill, width=int(width * self.ss), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.ell(x, y, width / 2, width / 2, fill)

    def rect(self, x0, y0, x1, y1, fill=255):
        s = self.ss
        self.d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=fill)

    def get(self, blur=0.0):
        im = self.im.resize((self.w, self.h), Image.LANCZOS)
        if blur:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        return np.asarray(im, dtype=np.float32) / 255.0


def bez(p0, p1, p2, n=16):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(np.array, (p0, p1, p2))
    pts = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
    return [tuple(p) for p in pts]


def monk_seated(m, cx, by, s):
    """front view meditation; s ~ height"""
    m.ell(cx, by - 0.12 * s, 0.55 * s, 0.13 * s)                       # crossed legs
    body = bez((cx - 0.50 * s, by - 0.10 * s), (cx - 0.44 * s, by - 0.62 * s), (cx - 0.20 * s, by - 0.74 * s), 14) + \
           bez((cx + 0.20 * s, by - 0.74 * s), (cx + 0.44 * s, by - 0.62 * s), (cx + 0.50 * s, by - 0.10 * s), 14)
    m.poly(body)
    m.ell(cx, by - 0.71 * s, 0.22 * s, 0.07 * s)                       # shoulders
    m.rect(cx - 0.055 * s, by - 0.84 * s, cx + 0.055 * s, by - 0.70 * s)  # neck
    m.ell(cx, by - 0.90 * s, 0.10 * s, 0.12 * s)                       # shaved head


def monk_standing(m, cx, by, s, lean=0.0):
    sh = by - 0.80 * s
    robe = bez((cx - 0.17 * s, sh), (cx - 0.26 * s, by - 0.4 * s), (cx - 0.24 * s, by), 12) + \
           [(cx + 0.24 * s, by)] + bez((cx + 0.24 * s, by), (cx + 0.26 * s, by - 0.4 * s), (cx + 0.17 * s, sh), 12)
    m.poly([(x + lean * (by - y), y) for x, y in robe])
    m.ell(cx + lean * 0.8 * s, sh + 0.01 * s, 0.18 * s, 0.05 * s)
    m.rect(cx - 0.04 * s + lean * 0.85 * s, sh - 0.07 * s, cx + 0.04 * s + lean * 0.85 * s, sh + 0.02 * s)
    m.ell(cx + lean * 0.9 * s, sh - 0.11 * s, 0.075 * s, 0.09 * s)


def monk_kneel_offer(m, cx, by, s, f=1, arm=1.0):
    """side view kneeling (seiza-like), torso upright, arms forward holding a bowl; returns bowl centre"""
    X = lambda dx: cx + f * dx * s
    Y = lambda dy: by - dy * s
    # folded legs: thigh + shin wedge on the ground
    m.ell(X(-0.06), Y(0.11), 0.30 * s, 0.115 * s)                               # folded legs
    m.ell(X(-0.26), Y(0.17), 0.12 * s, 0.13 * s)                                # seat on heels
    # robe torso, slightly bowed forward
    back = bez((X(-0.30), Y(0.20)), (X(-0.30), Y(0.50)), (X(-0.14), Y(0.64)), 14)
    front = bez((X(0.02), Y(0.62)), (X(0.06), Y(0.42)), (X(0.10), Y(0.20)), 10)
    m.poly(back + front)
    m.ell(X(-0.07), Y(0.635), 0.10 * s, 0.04 * s)                              # shoulder
    m.rect(min(X(-0.075), X(-0.015)), Y(0.72), max(X(-0.075), X(-0.015)), Y(0.62))  # neck
    m.ell(X(-0.02), Y(0.775), 0.075 * s, 0.085 * s)                             # shaved head
    bx, byy = X(0.30 + 0.12 * arm), Y(0.47)
    # sleeve + forearm
    m.poly([(X(-0.08), Y(0.60)), (X(0.06), Y(0.56)), (bx - f * 0.05 * s, byy + 0.035 * s),
            (bx - f * 0.06 * s, byy - 0.025 * s), (X(0.02), Y(0.47)), (X(-0.10), Y(0.50))])
    return bx, byy - 0.03 * s


def monk_walk(m, cx, by, s, ph, f=1):
    X = lambda dx: cx + f * dx * s
    Y = lambda dy: by - dy * s
    st = math.sin(ph) * 0.10
    robe = [(X(-0.10), Y(0.80)), (X(-0.18), Y(0.40)), (X(-0.22 - st), Y(0.0)), (X(0.20 + st), Y(0.0)),
            (X(0.16), Y(0.40)), (X(0.12), Y(0.78))]
    m.poly(robe)
    m.ell(X(0.01), Y(0.80), 0.13 * s, 0.05 * s)
    m.ell(X(0.04), Y(0.92), 0.075 * s, 0.09 * s)
    m.line([(X(0.05), Y(0.70)), (X(0.22), Y(0.58)), (X(0.30), Y(0.60))], 0.05 * s)
    return X(0.32), Y(0.62)


def hunched(m, cx, by, s, f=-1, reach=0.0):
    """thin stooped figure (only ever shown as a shadow)"""
    X = lambda dx: cx + f * dx * s
    Y = lambda dy: by - dy * s
    body = bez((X(-0.10), Y(0.0)), (X(-0.18), Y(0.45)), (X(0.05), Y(0.66)), 14) + \
           bez((X(0.16), Y(0.60)), (X(0.05), Y(0.30)), (X(0.08), Y(0.0)), 10)
    m.poly(body)
    m.ell(X(0.17), Y(0.66), 0.075 * s, 0.085 * s)
    m.line([(X(0.10), Y(0.52)), (X(0.26 + 0.1 * reach), Y(0.42 + 0.05 * reach)), (X(0.34 + 0.12 * reach), Y(0.44 + 0.08 * reach))], 0.025 * s)
    m.line([(X(-0.02), Y(0.02)), (X(0.02), Y(0.0))], 0.03 * s)


def bowl(m, cx, cy, r):
    m.poly(bez((cx - r, cy), (cx, cy + 1.25 * r), (cx + r, cy), 18))
    m.ell(cx, cy, r, 0.22 * r)


def roof(m, cx, y, w, h, curl=0.18):
    """Chinese roof with upturned eaves"""
    L = bez((cx - w / 2 - w * curl * 0.4, y - h * 0.35), (cx - w * 0.38, y + h * 0.05), (cx - w * 0.15, y - h * 0.55), 12)
    R = bez((cx + w * 0.15, y - h * 0.55), (cx + w * 0.38, y + h * 0.05), (cx + w / 2 + w * curl * 0.4, y - h * 0.35), 12)
    top = [(cx + w * 0.15, y - h), (cx - w * 0.15, y - h)]
    m.poly(L + [(cx - w * 0.15, y - h)] + [(cx + w * 0.15, y - h)] + R + [(cx + w / 2, y), (cx - w / 2, y)])


def hall(m, cx, by, w, h, tiers=1):
    y = by
    for t in range(tiers):
        bw = w * (1 - 0.18 * t)
        m.rect(cx - bw * 0.36, y - h * 0.55, cx + bw * 0.36, y)
        roof(m, cx, y - h * 0.5, bw, h * 0.5)
        y -= h * 0.85


def pagoda(m, cx, by, w, h, n=7):
    lev = h / (n + 1.2)
    y = by
    for i in range(n):
        bw = w * (1 - 0.07 * i)
        m.rect(cx - bw * 0.28, y - lev * 0.6, cx + bw * 0.28, y)
        roof(m, cx, y - lev * 0.55, bw * 0.95, lev * 0.55, curl=0.25)
        y -= lev
    m.rect(cx - w * 0.02, y - lev * 1.2, cx + w * 0.02, y)
    m.ell(cx, y - lev * 0.6, w * 0.05, w * 0.05)


def ridge(w, h, base, amp, seed, cell=180, octaves=5):
    """1D mountain profile -> mask array HxW (1 below ridge)"""
    n = fbm(1, w, cell, octaves, seed)[0]
    n2 = fbm(1, w, cell * 3, 2, seed + 5)[0]
    yline = base - amp * (0.65 * n + 0.35 * n2 - 0.3) * 2
    yy = np.arange(h, dtype=np.float32)[:, None]
    return np.clip((yy - yline[None, :]) / 3.0, 0, 1)


def ink_mountains(img, layers, seed=0, cols=None, mist=0.6):
    """layers: list of (base_y, amp, darkness 0..1). Painterly ink-wash ranges with mist at foot."""
    h, w = img.shape[:2]
    for i, (base, amp, dark) in enumerate(layers):
        m = ridge(w, h, base, amp, seed + 13 * i)
        yy = np.arange(h, dtype=np.float32)[:, None]
        fade = np.clip(1 - (yy - base) / (amp * 2.2 + 1) * mist, 0.12, 1)
        tex = 0.85 + 0.15 * fbm(h, w, 60, 3, seed + 100 + i)
        a = (m * fade * tex * dark)[..., None]
        col = np.array(cols[i] if cols else INK, np.float32)
        img[:] = img * (1 - a) + col * a
    return img


# ---------------------------------------------------------------- composites
def comp(img, mask, color, alpha=1.0):
    a = (mask * alpha)[..., None]
    img[:] = img * (1 - a) + np.array(color, np.float32) * a
    return img


def rim_light(mask, dx, dy, blur=3):
    """edge highlight on side facing (dx,dy) light"""
    sh = np.roll(np.roll(mask, int(dy), 0), int(dx), 1)
    e = np.clip(mask - sh, 0, 1)
    if blur:
        e = np.asarray(Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
    return e


def halo(img, cx, cy, r, color=GOLD, rays=True, amount=1.0, seed=1):
    h, w = img.shape[:2]
    y, x = np.ogrid[:h, :w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    ring = np.exp(-((d - r) / (r * 0.06)) ** 2) * 0.55 + np.clip(1 - d / r, 0, 1) ** 1.5 * 0.35
    glow = np.exp(-(d / (r * 1.6)) ** 2) * 0.45
    tot = ring + glow
    if rays:
        ang = np.arctan2(y - cy, x - cx)
        rr = 0.5 + 0.5 * np.cos(ang * 24 + 0.3)
        tot = tot + rr ** 6 * np.exp(-(d / (r * 2.6)) ** 2) * 0.35
    img += tot[..., None].astype(np.float32) * np.array(color, np.float32) * amount
    return img


def lotus_mask(m, cx, cy, s, petals=9):
    for i in range(petals):
        a = math.pi * (i / (petals - 1)) if petals > 1 else math.pi / 2
        a = math.pi - a
        px, py = cx + math.cos(a) * s * 0.55, cy - math.sin(a) * s * 0.35
        pts = []
        for k in range(24):
            t = k / 23 * 2 * math.pi
            lx = math.cos(t) * s * 0.16; ly = math.sin(t) * s * 0.42
            ly = ly - abs(ly) * 0.0
            rot = a - math.pi / 2
            pts.append((px + lx * math.cos(rot) - ly * math.sin(rot) * 0.6, py + lx * math.sin(rot) + ly * math.cos(rot) * 0.6))
        m.poly(pts)
    m.ell(cx, cy + s * 0.05, s * 0.75, s * 0.14)


def lantern(img, x, y, s, flick=1.0, refl=True, warm=WARM):
    """floating river lantern (lotus lamp) with glow & reflection; additive/painted in place"""
    h, w = img.shape[:2]
    if not (-80 < x < w + 80 and -80 < y < h + 80):
        return
    add_glow(img, x, y - s * 0.6, s * 7, warm, 0.35 * flick)
    add_glow(img, x, y - s * 0.5, s * 2.2, (1, 0.85, 0.55), 0.9 * flick)
    x0, x1 = int(x - s * 0.9), int(x + s * 0.9)
    y0, y1 = int(y - s * 0.15), int(y + s * 0.25)
    if 0 <= y0 < y1 < h and 0 <= x0 < x1 < w:
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * 0.4 + np.array((0.55, 0.22, 0.12), np.float32) * 0.6
    if refl:
        for k in range(1, 6):
            add_glow(img, x + math.sin(k * 1.7 + x) * s * 0.3, y + s * (0.6 + k * 0.9), s * (2.4 - k * 0.25),
                     warm, 0.16 * flick * (1 - k / 6.5))


def water(h, w, seed, base=(0.02, 0.035, 0.07), top_y=900):
    img = vgrad(h, w, (0.03, 0.04, 0.08), base)
    n = fbm(h, w, 40, 3, seed)
    yy = np.arange(h, dtype=np.float32)[:, None]
    streak = (np.sin(yy * 0.9 + n * 6) * 0.5 + 0.5) * np.clip((yy - top_y) / 400, 0, 1)
    img += (streak * 0.025)[..., None]
    return img


# ---------------------------------------------------------------- text
def text_img(txt, fnt, fill=(240, 232, 214), shadow=True, stroke=0, stroke_fill=(0, 0, 0), spacing=8, align="center"):
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bb = d.multiline_textbbox((0, 0), txt, font=fnt, spacing=spacing, align=align, stroke_width=stroke)
    pad = 24
    bb = [int(math.floor(bb[0])), int(math.floor(bb[1])), int(math.ceil(bb[2])), int(math.ceil(bb[3]))]
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).multiline_text((pad - bb[0] + 2, pad - bb[1] + 3), txt, font=fnt, fill=(0, 0, 0, 200),
                                          spacing=spacing, align=align, stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 200))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        im = Image.alpha_composite(im, sh)
        d = ImageDraw.Draw(im)
    d.multiline_text((pad - bb[0], pad - bb[1]), txt, font=fnt, fill=fill, spacing=spacing, align=align,
                     stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def vtext_img(cols, fnt, fill=(236, 226, 205), gap=1.12, colgap=1.45, shadow=True):
    """vertical text, columns right-to-left; cols: list of strings. Returns RGBA and per-char boxes (order of reading)."""
    size = fnt.size
    ncol = len(cols)
    maxlen = max(len(c) for c in cols)
    pad = 30
    w = int(size * colgap * (ncol - 1) + size + pad * 2)
    h = int(size * gap * maxlen + pad * 2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    boxes = []
    for ci, col in enumerate(cols):
        x = w - pad - size - ci * size * colgap
        for k, ch in enumerate(col):
            y = pad + k * size * gap
            if ch in "，。、；：":
                d.text((x + size * 0.55, y - size * 0.35), ch, font=fnt, fill=fill)
            else:
                d.text((x, y), ch, font=fnt, fill=fill)
            boxes.append((int(x), int(y), int(x + size), int(y + size * gap), ch))
    if shadow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(5))
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * 0.8)))
        im = Image.alpha_composite(sh, im)
    return im, boxes


def paste(base_pil, over, x, y, alpha=1.0):
    if alpha <= 0.003:
        return
    if alpha < 0.999:
        a = over.split()[3].point(lambda v: int(v * alpha))
        over = over.copy(); over.putalpha(a)
    base_pil.paste(over, (int(x), int(y)), over)


def seal(text, size=90, color=(178, 40, 30)):
    """vermilion seal stamp with 2-4 chars"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, size - 4, size - 4], radius=8, fill=color + (235,))
    f = font("kai", size * (0.36 if len(text) > 2 else 0.5))
    if len(text) == 4:
        pos = [(size * 0.52, size * 0.10), (size * 0.52, size * 0.50), (size * 0.12, size * 0.10), (size * 0.12, size * 0.50)]
        for (x, y), ch in zip(pos, text):
            d.text((x, y), ch, font=f, fill=(250, 235, 220, 255))
    else:
        d.text((size / 2, size / 2), text, font=f, fill=(250, 235, 220, 255), anchor="mm")
    n = (np.random.default_rng(len(text)).random((size, size)) > 0.12).astype(np.uint8)
    a = np.asarray(im.split()[3]) * n
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im
