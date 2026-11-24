# -*- coding: utf-8 -*-
"""Procedural 19th-century travel-notebook look: parchment, ink, hatching, watercolor, silhouettes.
All canvases are float32 HxWx3 in [0,1]. Ink is drawn supersampled (SS) with PIL, then downsampled.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SS = 2

FONT_CJK = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
FONT_CJK_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_CJK_SB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc"
FONT_FR_I = "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Italic.otf"
FONT_FR = "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Regular.otf"
_fcache = {}


def font(path, size, index=None):
    key = (path, size)
    if key not in _fcache:
        if path.endswith(".ttc"):
            _fcache[key] = ImageFont.truetype(path, size, index=2)  # SC
        else:
            _fcache[key] = ImageFont.truetype(path, size)
    return _fcache[key]


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


INK = hexc("#2e2118")
INK_SOFT = hexc("#5a4632")
RED = hexc("#9c2f22")

# ------------------------------------------------------------------ noise / paper

_NCACHE = {}


def cnoise(h, w, scale, key):
    """cached smooth noise field (deterministic per key)"""
    k = (h, w, scale, key)
    if k not in _NCACHE:
        _NCACHE[k] = noise2d(h, w, scale, np.random.default_rng(hash(key) % (2 ** 32)))
    return _NCACHE[k]


def noise2d(h, w, scale, rng):
    sh, sw = max(2, h // scale), max(2, w // scale)
    a = rng.random((sh, sw)).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0


def fbm(h, w, rng, octaves=((420, .45), (140, .25), (40, .18), (9, .12))):
    tot = sum(a for _, a in octaves)
    return sum(noise2d(h, w, s, rng) * a for s, a in octaves) / tot


def blur(a, r):
    if r <= 0:
        return a
    if a.ndim == 2:
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255
    return np.stack([blur(a[..., i], r) for i in range(a.shape[2])], -1)


def blur_f(a, r):
    """float-precision blur via PIL 'F' mode not supported for Gaussian; use box-ish separable numpy."""
    if r <= 0:
        return a
    k = int(max(1, r * 2.5))
    x = np.arange(-k, k + 1, dtype=np.float32)
    g = np.exp(-0.5 * (x / r) ** 2); g /= g.sum()
    out = np.apply_along_axis(lambda v: np.convolve(v, g, mode="same"), 0, a)
    out = np.apply_along_axis(lambda v: np.convolve(v, g, mode="same"), 1, out)
    return out


PAPER_TONES = {
    "warm": ("#ecdfc4", "#d9c39b"),
    "america": ("#ecdfc2", "#d6bf93"),
    "france": ("#e4e2da", "#c3c6c4"),
    "oldfrance": ("#e2e1da", "#bfc3c3"),
    "gray": ("#e2ded6", "#c4c0b8"),
    "ice": ("#d6dde4", "#9fb0c0"),
    "sea": ("#e8e0c8", "#cbbd98"),
    "forest": ("#e8dcbf", "#cdb68a"),
    "dawn": ("#eee2c6", "#d8c29a"),
}


_PAPER = {}


def paper(tone="warm", seed=1, w=W, h=H):
    k = (tone, seed, w, h)
    if k not in _PAPER:
        _PAPER[k] = _paper(tone, seed, w, h)
    return _PAPER[k].copy()


def _paper(tone="warm", seed=1, w=W, h=H):
    rng = np.random.default_rng(seed)
    light, dark = (hexc(c) for c in PAPER_TONES.get(tone, PAPER_TONES["warm"]))
    n = fbm(h, w, rng)
    n2 = fbm(h, w, rng, ((60, .5), (6, .5)))
    t = np.clip((n - 0.5) * 1.6 + 0.35 + (n2 - 0.5) * 0.25, 0, 1)
    img = light[None, None, :] * (1 - t[..., None] * 0.45) + dark[None, None, :] * (t[..., None] * 0.45)
    # fibers
    fib = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(900):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(6, 30)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=int(rng.uniform(40, 110)), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    img = img * (1 - fib[..., None] * 0.07)
    # foxing stains
    st = np.zeros((h, w), np.float32)
    for _ in range(7):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(25, 110)
        yy, xx = np.ogrid[:h, :w]
        st += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))) * rng.uniform(0.2, 0.6)
    st *= (0.6 + 0.8 * noise2d(h, w, 30, rng))
    img = img * (1 - np.clip(st, 0, 1)[..., None] * np.array([0.05, 0.09, 0.15]))
    # vignette
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vx = (xx / w - 0.5) * 2; vy = (yy / h - 0.5) * 2
    v = np.clip(1 - 0.22 * (vx ** 2) ** 1.5 - 0.14 * (vy ** 2) ** 2, 0, 1)
    img = img * v[..., None]
    return np.clip(img, 0, 1).astype(np.float32)


# ------------------------------------------------------------------ ink layer

class Ink:
    """Supersampled alpha layer for ink drawing; composite with .apply()."""

    def __init__(self, w=W, h=H, ss=SS):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new("L", (w * ss, h * ss), 0)
        self.d = ImageDraw.Draw(self.im)

    def P(self, pts):
        s = self.ss
        return [(x * s, y * s) for x, y in pts]

    def line(self, pts, width=2.0, val=255, jitter=0.0, rng=None, closed=False):
        pts = list(pts)
        if closed:
            pts = pts + [pts[0]]
        if jitter and rng is not None:
            pts = [(x + rng.normal(0, jitter), y + rng.normal(0, jitter)) for x, y in pts]
        self.d.line(self.P(pts), fill=val, width=max(1, int(round(width * self.ss))), joint="curve")

    def wobble_line(self, p0, p1, width=2.0, amp=1.2, rng=None, n=None, val=255, taper=False):
        x0, y0 = p0; x1, y1 = p1
        L = math.hypot(x1 - x0, y1 - y0)
        n = n or max(2, int(L / 14))
        rng = rng or np.random.default_rng(0)
        ph = rng.uniform(0, 6.28)
        nx, ny = (-(y1 - y0) / (L + 1e-6), (x1 - x0) / (L + 1e-6))
        pts = []
        for i in range(n + 1):
            t = i / n
            off = amp * math.sin(ph + t * 7.0) + rng.normal(0, amp * 0.25)
            pts.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
        if taper:
            for i in range(n):
                t = i / n
                wdt = width * (0.35 + 0.65 * math.sin(math.pi * (t + 0.5 / n)))
                self.d.line(self.P([pts[i], pts[i + 1]]), fill=val, width=max(1, int(round(wdt * self.ss))))
        else:
            self.line(pts, width, val)

    def poly(self, pts, val=255, outline=None, width=1.5):
        self.d.polygon(self.P(pts), fill=val)
        if outline is not None:
            self.line(pts, width, outline, closed=True)

    def ellipse(self, cx, cy, rx, ry, val=255, outline=None, width=2.0):
        s = self.ss
        box = [(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s]
        if outline is None:
            self.d.ellipse(box, fill=val)
        else:
            self.d.ellipse(box, outline=outline, width=max(1, int(width * s)))

    def arc(self, cx, cy, rx, ry, a0, a1, width=2.0, val=255):
        s = self.ss
        self.d.arc([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], a0, a1, fill=val,
                   width=max(1, int(width * s)))

    def text(self, xy, txt, fnt, val=255, anchor="la"):
        s = self.ss
        f2 = ImageFont.truetype(fnt.path, int(fnt.size * s), index=getattr(fnt, "index", 0)) \
            if not fnt.path.endswith(".ttc") else ImageFont.truetype(fnt.path, int(fnt.size * s), index=2)
        self.d.text((xy[0] * s, xy[1] * s), txt, font=f2, fill=val, anchor=anchor)

    def alpha(self):
        a = self.im.reduce(self.ss) if self.ss > 1 else self.im
        return np.asarray(a).astype(np.float32) / 255.0

    def apply(self, canvas, color=INK, opacity=1.0, grain=0.18, seed=3):
        a = self.alpha() * opacity
        if grain:
            rng = np.random.default_rng(seed)
            g = cnoise(self.h, self.w, 3, ("grain", seed % 4))
            a = a * (1 - grain + grain * 1.6 * g)
            a = np.clip(a, 0, 1)
        canvas[:] = canvas * (1 - a[..., None]) + color[None, None, :] * a[..., None]
        return canvas


def mask_from_poly(polys, w=W, h=H, blur_r=0.0):
    m = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([(x * SS, y * SS) for x, y in p], fill=255)
    m = m.reduce(SS)
    if blur_r:
        m = m.filter(ImageFilter.GaussianBlur(blur_r))
    return np.asarray(m).astype(np.float32) / 255


def wash(canvas, mask, color, opacity=0.6, seed=0, gran=0.35, edge=0.6, bleed=2.5):
    """Watercolor multiply-wash inside mask with granulation and darker edges (cropped to the mask bbox)."""
    ys, xs = np.nonzero(mask > 0.002)
    if len(ys) == 0:
        return canvas
    h, w = mask.shape
    mg = int(bleed * 3 + 24)
    y0, y1 = max(0, ys.min() - mg), min(h, ys.max() + mg + 1)
    x0, x1 = max(0, xs.min() - mg), min(w, xs.max() + mg + 1)
    m = mask[y0:y1, x0:x1]
    m = blur(m, bleed) if bleed else m
    n = cnoise(h, w, 18, ("wn", seed % 8))[y0:y1, x0:x1]
    m = np.clip(m * (0.75 + 0.5 * n) - 0.08, 0, 1)
    m = np.clip(m * 1.25, 0, 1)
    e = np.clip(m - blur(m, 6), 0, 1)
    g = (cnoise(h, w, 2, ("wg2", seed % 4))[y0:y1, x0:x1] * 0.5 + cnoise(h, w, 7, ("wg7", seed % 4))[y0:y1, x0:x1] * 0.5)
    al = m * opacity * (1 - gran + gran * 1.4 * g) + e * edge
    al = np.clip(al, 0, 1)[..., None]
    col = np.asarray(color, np.float32)[None, None, :]
    sub = canvas[y0:y1, x0:x1]
    canvas[y0:y1, x0:x1] = sub * (1 - al + al * col)
    return canvas


def hatch(ink, poly_or_mask, angle=45, spacing=7, width=1.1, rng=None, val=255, wob=0.6, bbox=None):
    """Parallel hatch lines clipped to polygon(s). Draws into a temp layer then merges into ink."""
    rng = rng or np.random.default_rng(1)
    tmp = Image.new("L", ink.im.size, 0)
    d = ImageDraw.Draw(tmp)
    if bbox is None:
        if isinstance(poly_or_mask, list) and poly_or_mask and isinstance(poly_or_mask[0][0], (int, float, np.floating)):
            polys = [poly_or_mask]
        else:
            polys = poly_or_mask
        xs = [p[0] for pl in polys for p in pl]; ys = [p[1] for pl in polys for p in pl]
        bbox = (min(xs), min(ys), max(xs), max(ys))
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 5
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    k = -R
    s = SS
    while k <= R:
        px, py = cx + nx * k, cy + ny * k
        pts = []
        steps = 12
        for i in range(steps + 1):
            t = -R + 2 * R * i / steps
            off = rng.normal(0, wob)
            pts.append(((px + ux * t + nx * off) * s, (py + uy * t + ny * off) * s))
        d.line(pts, fill=val, width=max(1, int(width * s)))
        k += spacing * rng.uniform(0.85, 1.15)
    m = Image.new("L", ink.im.size, 0)
    md = ImageDraw.Draw(m)
    polys = poly_or_mask if not (poly_or_mask and isinstance(poly_or_mask[0][0], (int, float, np.floating))) else [poly_or_mask]
    for pl in polys:
        md.polygon([(x * s, y * s) for x, y in pl], fill=255)
    arr = np.minimum(np.asarray(tmp), np.asarray(m))
    cur = np.asarray(ink.im)
    ink.im = Image.fromarray(np.maximum(cur, arr))
    ink.d = ImageDraw.Draw(ink.im)


# ------------------------------------------------------------------ silhouettes

def limb(ink, p0, p1, w0, w1, val=255):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) + 1e-6
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ink.poly([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
              (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], val)
    ink.ellipse(x1, y1, w1 / 2, w1 / 2, val)
    ink.ellipse(x0, y0, w0 / 2, w0 / 2, val)


def arm(ink, sh, el, hd, h, val=255):
    limb(ink, sh, el, h * 0.062, h * 0.05, val)
    limb(ink, el, hd, h * 0.05, h * 0.038, val)
    ink.ellipse(hd[0], hd[1], h * 0.026, h * 0.03, val)


def person(ink, x, y, h, pose="stand", facing=1, hat="top", dress=False, val=255, arm_t=0.0, child=False):
    """19th-c silhouette standing with feet at (x, y); h = height to top of head (hat extra).
    pose: stand | raise | walk | saw | point | talk | carry | bow | sit | huddle
    """
    f = facing
    if child:
        h = h * 1.0
    hr = h * (0.062 if not child else 0.085)
    lean = {"bow": 0.07, "saw": 0.06, "carry": 0.03, "huddle": 0.05}.get(pose, 0.0) * h * f
    head_c = (x + lean * 1.25, y - h + hr * 1.15)
    sh_y = y - h * (0.80 if not child else 0.74)
    waist_y = y - h * 0.54
    hip_y = y - h * 0.47
    sw = h * 0.095
    ww = h * 0.07
    # ---- legs / skirt
    if dress:
        pts = [(x - ww + lean * 0.4, waist_y)]
        for i in range(9):
            t = i / 8
            pts.append((x - ww - (h * 0.17 - ww) * t ** 0.8 + lean * 0.4 * (1 - t), waist_y + (y - waist_y) * t))
        pts += [(x + h * 0.17, y)]
        for i in range(8, -1, -1):
            t = i / 8
            pts.append((x + ww + (h * 0.17 - ww) * t ** 0.8 + lean * 0.4 * (1 - t), waist_y + (y - waist_y) * t))
        ink.poly(pts, val)
    else:
        if pose == "walk":
            ph = math.sin(arm_t * 6.0)
            lx = h * 0.14 * ph
            for s_ in (1, -1):
                kx = x + s_ * lx * f * 0.5
                limb(ink, (x, hip_y), (kx + h * 0.02 * f, y - h * 0.25), h * 0.07, h * 0.055, val)
                limb(ink, (kx + h * 0.02 * f, y - h * 0.25), (x + s_ * lx * f, y - h * 0.03), h * 0.055, h * 0.042, val)
                ink.ellipse(x + s_ * lx * f + f * h * 0.03, y - h * 0.018, h * 0.045, h * 0.02, val)
        elif pose == "sit":
            limb(ink, (x, hip_y), (x + f * h * 0.2, hip_y + h * 0.02), h * 0.075, h * 0.06, val)
            limb(ink, (x + f * h * 0.2, hip_y + h * 0.02), (x + f * h * 0.21, y - h * 0.03), h * 0.06, h * 0.045, val)
        else:
            for s_ in (-1, 1):
                limb(ink, (x + s_ * h * 0.035, hip_y), (x + s_ * h * 0.045, y - h * 0.03), h * 0.068, h * 0.044, val)
                ink.ellipse(x + s_ * h * 0.045 + f * h * 0.025, y - h * 0.018, h * 0.045, h * 0.02, val)
        # frock-coat skirt with tails
        tail = h * 0.05 * (-f)
        ink.poly([(x - ww + lean * 0.5, waist_y - h * 0.02), (x + ww + lean * 0.5, waist_y - h * 0.02),
                  (x + ww * 1.25 + (tail if f < 0 else 0), y - h * 0.3), (x - ww * 1.25 + (tail if f > 0 else 0), y - h * 0.3)], val)
    # ---- torso (curved)
    tors = [(x - sw * 0.92 + lean, sh_y + h * 0.015), (x - sw + lean, sh_y + h * 0.04), (x - ww * 1.02 + lean * 0.5, waist_y),
            (x + ww * 1.02 + lean * 0.5, waist_y), (x + sw + lean, sh_y + h * 0.04), (x + sw * 0.92 + lean, sh_y + h * 0.015),
            (x + sw * 0.5 + lean, sh_y - h * 0.008), (x - sw * 0.5 + lean, sh_y - h * 0.008)]
    ink.poly(tors, val)
    # neck + head
    hx, hy = head_c
    limb(ink, (hx - f * hr * 0.1, hy + hr * 0.6), (x + lean, sh_y + h * 0.01), hr * 0.7, hr * 0.85, val)
    ink.ellipse(hx, hy, hr * 0.92, hr * 1.08, val)
    ink.poly([(hx + f * hr * 0.7, hy - hr * 0.2), (hx + f * hr * 1.18, hy + hr * 0.28), (hx + f * hr * 0.75, hy + hr * 0.42)], val)
    ink.ellipse(hx + f * hr * 0.55, hy + hr * 0.72, hr * 0.38, hr * 0.32, val)  # chin
    # ---- hats
    if hat == "top":
        bw = hr * 1.5
        ink.poly([(hx - bw, hy - hr * 0.62), (hx + bw, hy - hr * 0.62), (hx + bw * 0.95, hy - hr * 0.86), (hx - bw * 0.95, hy - hr * 0.86)], val)
        ink.poly([(hx - hr * 0.86, hy - hr * 0.8), (hx + hr * 0.86, hy - hr * 0.8), (hx + hr * 1.0, hy - hr * 2.5), (hx - hr * 1.0, hy - hr * 2.5)], val)
    elif hat == "wide":
        bw = hr * 2.0
        ink.poly([(hx - bw, hy - hr * 0.5), (hx - bw * 0.6, hy - hr * 0.68), (hx + bw * 0.6, hy - hr * 0.68), (hx + bw, hy - hr * 0.5), (hx + bw * 0.6, hy - hr * 0.6), (hx - bw * 0.6, hy - hr * 0.6)], val)
        ink.ellipse(hx, hy - hr * 0.9, hr * 0.95, hr * 0.6, val)
    elif hat == "bonnet":
        ink.ellipse(hx - f * hr * 0.35, hy - hr * 0.15, hr * 1.25, hr * 1.25, val)
        ink.poly([(hx - f * hr * 0.2, hy - hr * 1.35), (hx + f * hr * 1.55, hy - hr * 0.75), (hx + f * hr * 1.2, hy + hr * 0.1), (hx + f * hr * 0.2, hy - hr * 0.2)], val)
    elif hat == "cap":
        ink.ellipse(hx - f * hr * 0.1, hy - hr * 0.65, hr * 1.02, hr * 0.62, val)
        ink.poly([(hx, hy - hr * 0.62), (hx + f * hr * 1.75, hy - hr * 0.45), (hx + f * hr * 0.2, hy - hr * 0.32)], val)
    elif hat == "shawl":
        ink.poly([(hx - hr * 1.3, hy + hr * 0.5), (hx - hr * 0.9, hy - hr * 1.1), (hx, hy - hr * 1.45), (hx + hr * 0.9, hy - hr * 1.1),
                  (hx + hr * 1.3, hy + hr * 0.5), (x + sw * 1.45 + lean, sh_y + h * 0.3), (x - sw * 1.45 + lean, sh_y + h * 0.3)], val)
    # ---- arms
    shf = (x + f * sw * 0.8 + lean, sh_y + h * 0.04)
    shb = (x - f * sw * 0.7 + lean, sh_y + h * 0.04)
    down_f = ((shf[0] + f * h * 0.02, sh_y + h * 0.17), (shf[0] + f * h * 0.03, sh_y + h * 0.31))
    down_b = ((shb[0] - f * h * 0.015, sh_y + h * 0.17), (shb[0] - f * h * 0.02, sh_y + h * 0.31))
    if pose == "raise":
        up = min(1.0, max(0.0, arm_t))
        el = (shf[0] + f * h * (0.02 + 0.06 * up), sh_y + h * (0.17 - 0.24 * up))
        hd = (shf[0] + f * h * (0.03 + 0.07 * up), sh_y + h * (0.31 - 0.52 * up))
        arm(ink, shf, el, hd, h, val); arm(ink, shb, *down_b, h, val)
    elif pose == "point":
        arm(ink, shf, (shf[0] + f * h * 0.13, sh_y + h * 0.04), (shf[0] + f * h * 0.27, sh_y - h * 0.0), h, val)
        arm(ink, shb, *down_b, h, val)
    elif pose == "talk":
        g = 0.5 + 0.5 * math.sin(arm_t * 4.5)
        arm(ink, shf, (shf[0] + f * h * 0.06, sh_y + h * 0.16), (shf[0] + f * h * (0.18 + 0.04 * g), sh_y + h * (0.08 + 0.05 * g)), h, val)
        arm(ink, shb, *down_b, h, val)
    elif pose == "saw":
        s_ = math.sin(arm_t * 9.0)
        hd = (shf[0] + f * h * (0.24 + 0.07 * s_), sh_y + h * 0.25)
        arm(ink, shf, (shf[0] + f * h * 0.1, sh_y + h * 0.16), hd, h, val)
        arm(ink, shb, (shb[0] + f * h * 0.12, sh_y + h * 0.18), (hd[0] - f * h * 0.03, hd[1] + h * 0.02), h, val)
    elif pose == "carry":
        arm(ink, shf, (shf[0] + f * h * 0.12, sh_y + h * 0.12), (shf[0] + f * h * 0.18, sh_y - h * 0.0), h, val)
        arm(ink, shb, (shb[0] + f * h * 0.14, sh_y + h * 0.12), (shb[0] + f * h * 0.22, sh_y + h * 0.0), h, val)
    elif pose == "walk":
        ph = math.sin(arm_t * 6.0)
        arm(ink, shf, (shf[0] + f * h * 0.04 * ph, sh_y + h * 0.17), (shf[0] + f * h * 0.1 * ph, sh_y + h * 0.3), h, val)
        arm(ink, shb, (shb[0] - f * h * 0.04 * ph, sh_y + h * 0.17), (shb[0] - f * h * 0.1 * ph, sh_y + h * 0.3), h, val)
    elif pose == "huddle":
        arm(ink, shf, (shf[0] + f * h * 0.05, sh_y + h * 0.15), (x + lean + f * h * 0.02, sh_y + h * 0.2), h, val)
        arm(ink, shb, (shb[0] + f * h * 0.08, sh_y + h * 0.16), (x + lean, sh_y + h * 0.22), h, val)
    elif pose == "bow":
        arm(ink, shf, (shf[0] + f * h * 0.04, sh_y + h * 0.17), (shf[0] + f * h * 0.05, sh_y + h * 0.3), h, val)
        arm(ink, shb, *down_b, h, val)
    else:
        arm(ink, shf, *down_f, h, val); arm(ink, shb, *down_b, h, val)


def dog(ink, x, y, s, facing=1, howl=0.0, val=255, swim=False, t=0.0):
    """Dog silhouette; (x,y) = ground under body; s = nose-to-tail-base length. howl 0..1 raises the head."""
    f = facing
    def P(u, v):
        return (x + f * (u - 0.5) * s, y + v * s)
    if swim:
        # only head + back line above water
        ink.poly([P(0.25, -0.02), P(0.45, -0.07), P(0.68, -0.05), P(0.72, 0.0), P(0.25, 0.01)], val)
        hx, hy = P(0.78, -0.16)
        ink.ellipse(hx, hy, s * 0.09, s * 0.075, val)
        ink.poly([(hx + f * s * 0.04, hy - s * 0.03), (hx + f * s * 0.19, hy + s * 0.0), (hx + f * s * 0.05, hy + s * 0.05)], val)
        ink.poly([(hx - f * s * 0.03, hy - s * 0.05), (hx - f * s * 0.01, hy - s * 0.15), (hx + f * s * 0.03, hy - s * 0.05)], val)
        ink.line([P(0.62, -0.04), (hx, hy)], s * 0.08, val)
        return
    body = [P(0.16, -0.56), P(0.30, -0.60), P(0.50, -0.60), P(0.66, -0.62), P(0.76, -0.58), P(0.81, -0.46), P(0.78, -0.33),
            P(0.68, -0.29), P(0.56, -0.32), P(0.44, -0.35), P(0.30, -0.34), P(0.18, -0.38), P(0.12, -0.47)]
    ink.poly(body, val)
    # legs (short, sturdy)
    for u0, u1, w in ((0.72, 0.74, 0.085), (0.63, 0.62, 0.08), (0.26, 0.22, 0.10), (0.18, 0.20, 0.085)):
        limb(ink, P(u0, -0.38), P(u1, -0.17), s * w, s * 0.06, val)
        limb(ink, P(u1, -0.17), P(u1 + 0.01, -0.02), s * 0.06, s * 0.052, val)
        ink.ellipse(P(u1 + 0.035, -0.02)[0], P(u1 + 0.035, -0.02)[1], s * 0.05, s * 0.024, val)
    # bushy tail, hanging low
    ink.poly([P(0.15, -0.54), P(0.06, -0.48), P(0.01, -0.36), P(0.02, -0.26), P(0.07, -0.30), P(0.10, -0.40), P(0.16, -0.46)], val)
    # neck + head
    ang = math.radians(40 + 45 * howl)  # elevation of neck
    nb = P(0.72, -0.50)
    L = s * 0.2
    hx, hy = nb[0] + f * L * math.cos(ang), nb[1] - L * math.sin(ang)
    limb(ink, nb, (hx, hy), s * 0.22, s * 0.13, val)
    ink.ellipse(hx, hy, s * 0.1, s * 0.09, val)
    sa = math.radians(-12 + 72 * howl)  # snout elevation
    sl = s * 0.15
    sx, sy = hx + f * sl * math.cos(sa), hy - sl * math.sin(sa)
    limb(ink, (hx, hy + s * 0.015), (sx, sy), s * 0.11, s * 0.055, val)
    if howl > 0.5:
        # open mouth: small notch drawn as gap is not possible -> slight jaw drop
        jx, jy = hx + f * sl * 0.85 * math.cos(sa - 0.35), hy - sl * 0.85 * math.sin(sa - 0.35)
        limb(ink, (hx, hy + s * 0.03), (jx, jy), s * 0.05, s * 0.03, val)
    # drooping ear
    ex, ey = hx - f * s * 0.02, hy - s * 0.06
    ink.poly([(ex - f * s * 0.05, ey + s * 0.01), (ex - f * s * 0.1, ey + s * 0.09), (ex - f * s * 0.06, ey + s * 0.1), (ex + f * s * 0.03, ey + s * 0.02)], val)


def horse(ink, x, y, s, facing=1, val=255, t=0.0, walking=False):
    """Horse silhouette, (x,y) ground under body center, s = nose-to-tail length."""
    f = facing
    def P(u, v):
        return (x + f * (u - 0.5) * s, y + v * s)
    body = [P(0.80, -0.56), P(0.86, -0.78), P(0.92, -0.88), P(0.96, -0.90), P(1.04, -0.74), P(1.03, -0.70),
            P(0.95, -0.70), P(0.88, -0.66), P(0.82, -0.50), P(0.70, -0.42), P(0.45, -0.40), P(0.26, -0.43),
            P(0.16, -0.50), P(0.13, -0.60), P(0.20, -0.67), P(0.42, -0.65), P(0.66, -0.67), P(0.74, -0.70)]
    ink.poly(body, val)
    ink.poly([P(0.93, -0.90), P(0.95, -0.97), P(0.97, -0.89)], val)  # ear
    ink.poly([P(0.14, -0.60), P(0.07, -0.50), P(0.06, -0.33), P(0.10, -0.35), P(0.15, -0.52)], val)  # tail
    ph = math.sin(t * 5) if walking else 0.0
    for u, d in ((0.74, 1), (0.66, -1), (0.27, 1), (0.19, -1)):
        k = 0.04 * ph * d
        top = P(u, -0.45)
        knee = P(u + k * 0.6, -0.22)
        foot = P(u + k, -0.01)
        limb(ink, top, knee, s * 0.075, s * 0.045, val)
        limb(ink, knee, foot, s * 0.045, s * 0.04, val)


def tree(ink, x, y, h, rng, val=255, kind="leaf", hatch_ink=None):
    """Engraving-ish tree: trunk + scalloped crown outline."""
    tw = h * 0.05
    ink.poly([(x - tw, y), (x + tw, y), (x + tw * 0.5, y - h * 0.55), (x - tw * 0.5, y - h * 0.55)], val)
    cx, cy = x, y - h * 0.68
    r = h * 0.33
    pts = []
    n = 26
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.82 + 0.25 * rng.random())
        pts.append((cx + rr * math.cos(a) * 1.0, cy + rr * math.sin(a) * 0.9))
    return pts


# ------------------------------------------------------------------ text

def wrap_cjk(txt, fnt, maxw):
    lines, cur = [], ""
    no_start = set("，。？！：；、”》）…")
    for ch in txt:
        test = cur + ch
        if fnt.getlength(test) > maxw and cur:
            if ch in no_start:
                lines.append(cur[:-1]); cur = cur[-1] + ch
            else:
                lines.append(cur); cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def balance_cjk(txt, fnt, maxw):
    """Wrap into the fewest lines that fit maxw, with lines as even as possible (no 1-2 char orphans)."""
    lines = wrap_cjk(txt, fnt, maxw)
    n = len(lines)
    if n <= 1:
        return lines
    total = fnt.getlength(txt)
    w = total / n
    while w <= maxw:
        out = wrap_cjk(txt, fnt, w + fnt.size * 0.3)
        if len(out) == n:
            return out
        w += fnt.size * 0.5
    return lines


def wrap_words(txt, fnt, maxw):
    words, lines, cur = txt.split(" "), [], ""
    for w_ in words:
        test = (cur + " " + w_).strip()
        if fnt.getlength(test) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def draw_text_rgba(size, items):
    """items: list of (x, y, text, font, rgba, anchor). Returns RGBA float array (H,W,4)."""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x, y, t, f, c, anc in items:
        d.text((x, y), t, font=f, fill=c, anchor=anc)
    return np.asarray(im).astype(np.float32) / 255


def over(canvas, rgba, opacity=1.0):
    a = rgba[..., 3:4] * opacity
    canvas[:] = canvas * (1 - a) + rgba[..., :3] * a
    return canvas


def to_u8(canvas):
    return (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
