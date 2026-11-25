# -*- coding: utf-8 -*-
"""Ink-wash primitives for EP52: paper, mountains, bamboo, seated figure, brush bars, seals, text."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1080, 1920
FD = "/tmp/claude-0/work/fonts/"
INK = (32, 30, 28)
INK2 = (70, 66, 60)
GREY = (120, 114, 104)
RED = (176, 46, 34)
PAPER = (236, 229, 212)
GOLD = (196, 150, 80)
DAWN = (246, 214, 160)


@functools.lru_cache(maxsize=64)
def font(kind, size):
    f = {"kai": "LXGWWenKai-Medium.ttf", "kai_r": "LXGWWenKai-Regular.ttf", "serif": "NotoSerifSC-Bold.otf",
         "black": "NotoSerifSC-Black.otf", "serif_r": "NotoSerifSC-Regular.otf"}[kind]
    return ImageFont.truetype(FD + f, size)


def rng(seed):
    return np.random.default_rng(seed)


def smooth_noise(n, scale, seed):
    r = rng(seed)
    k = max(2, int(n / scale) + 3)
    pts = r.standard_normal(k)
    x = np.linspace(0, k - 3, n)
    i = np.floor(x).astype(int); f = x - i
    f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f) + pts[i + 1] * f


def fbm1(n, seed, octaves=5, base=400):
    out = np.zeros(n)
    amp = 1.0
    for o in range(octaves):
        out += amp * smooth_noise(n, base / (2 ** o), seed + o * 17)
        amp *= 0.5
    return out


@functools.lru_cache(maxsize=4)
def paper(tint=PAPER, seed=1, dark=False):
    r = rng(seed)
    base = np.ones((H, W, 3), np.float32) * np.array(tint, np.float32)
    n = r.standard_normal((H // 4, W // 4)).astype(np.float32)
    ni = Image.fromarray(((n * 20 + 128).clip(0, 255)).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    n2 = (np.asarray(ni, np.float32) - 128) / 128
    fib = r.standard_normal((H, W)).astype(np.float32)
    fibi = Image.fromarray(((fib * 30 + 128).clip(0, 255)).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    f2 = (np.asarray(fibi, np.float32) - 128) / 128
    base += (n2 * 7 + f2 * 3)[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    vig = 1 - 0.22 * np.clip(d, 0, 1.4) ** 2
    base *= vig[..., None]
    if dark:
        base = base * 0.16 + np.array([8, 9, 12], np.float32)
    return Image.fromarray(base.clip(0, 255).astype(np.uint8), "RGB")


def ink_layer(mask, color=INK, alpha=1.0):
    """mask: L image -> RGBA layer"""
    lay = Image.new("RGBA", mask.size, color + (0,))
    a = mask if alpha >= 0.999 else mask.point(lambda v: int(v * alpha))
    lay.putalpha(a)
    return lay


@functools.lru_cache(maxsize=16)
def mountains(seed=3, y0=900, layers=4, height=520, dark=False):
    """Layered misty ridges as RGBA."""
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k in range(layers):
        prof = fbm1(W, seed + k * 11, base=500 - k * 60)
        prof = (prof - prof.min()) / (np.ptp(prof) + 1e-6)
        top = y0 + k * 110 - prof * (height - k * 90)
        m = np.zeros((H, W), np.float32)
        yy = np.arange(H)[:, None]
        inside = yy >= top[None, :]
        depth = np.clip((yy - top[None, :]) / 260.0, 0, 1)
        val = inside * (1 - 0.85 * depth)  # mist fading downward
        a = (0.20 + 0.18 * k) * 255
        m = (val * a).astype(np.uint8)
        mi = Image.fromarray(m).filter(ImageFilter.GaussianBlur(2 + (layers - k) * 2))
        col = tuple(int(c) for c in (np.array(INK2) * (0.8 + 0.1 * k))) if not dark else (150, 160, 175)
        out = Image.alpha_composite(out, ink_layer(mi, col))
    return out


def rough_rect_mask(w, h, seed=0, edge=6):
    r = rng(seed)
    m = Image.new("L", (w + 2 * edge, h + 2 * edge), 0)
    d = ImageDraw.Draw(m)
    pts = []
    n = 24
    for i in range(n + 1):
        pts.append((edge + w * i / n, edge + r.uniform(-edge, edge) * 0.6))
    for i in range(n + 1):
        pts.append((edge + w + r.uniform(-edge, edge) * 0.6, edge + h * i / n))
    for i in range(n, -1, -1):
        pts.append((edge + w * i / n, edge + h + r.uniform(-edge, edge) * 0.6))
    for i in range(n, -1, -1):
        pts.append((edge + r.uniform(-edge, edge) * 0.6, edge + h * i / n))
    d.polygon(pts, fill=255)
    a = np.asarray(m, np.float32)
    streak = r.uniform(0.75, 1.0, (1, a.shape[1])) if w > h else r.uniform(0.75, 1.0, (a.shape[0], 1))
    tex = r.uniform(0.85, 1.0, a.shape)
    a = a * streak * tex
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


def brush_bar(img, x, y, w, h, color=INK, seed=0, alpha=1.0):
    if w < 2 or h < 2:
        return
    m = rough_rect_mask(int(w), int(h), seed)
    img.alpha_composite(ink_layer(m, color, alpha), (int(x) - 6, int(y) - 6))


def seal(text, size=150, color=RED, seed=0, rot=0.0, white=True):
    """Square vermilion seal with text; returns RGBA."""
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    base = rough_rect_mask(s - 16, s - 16, seed, edge=8)
    lay = ink_layer(base, color, 0.92)
    im.alpha_composite(lay, (0, 0))
    d = ImageDraw.Draw(im)
    n = len(text)
    if n <= 2:
        rows = [text]
    elif n == 3:
        rows = [text[:1], text[1:]] if False else [text[:2], text[2:]]
    elif n == 4:
        rows = [text[:2], text[2:]]
    else:
        h2 = (n + 1) // 2
        rows = [text[:h2], text[h2:]]
    ncols = max(len(r) for r in rows)
    fs = int((s - 44) / max(ncols, len(rows)) * 0.95)
    f = font("serif", fs)
    tc = (245, 232, 220, 255) if white else color + (255,)
    for ri, row in enumerate(rows):
        cy = s / 2 - (len(rows) - 1) * fs * 0.55 + ri * fs * 1.1
        for ci, ch in enumerate(row):
            cx = s / 2 - (len(row) - 1) * fs / 2 + ci * fs
            d.text((cx, cy), ch, font=f, fill=tc, anchor="mm")
    # erode texture
    a = np.asarray(im.getchannel("A"), np.float32)
    r = rng(seed + 5)
    holes = (r.random(a.shape) > 0.97).astype(np.float32)
    hi = Image.fromarray((holes * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    a = a * (1 - np.asarray(hi, np.float32) / 255 * 0.8)
    im.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im


def text_img(txt, kind="kai", size=60, color=INK, stroke=0, stroke_color=None, spacing=12, align="center"):
    f = font(kind, size)
    dummy = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = dummy.multiline_textbbox((0, 0), txt, font=f, spacing=spacing, align=align, stroke_width=stroke)
    w, h = int(math.ceil(bb[2] - bb[0])) + 8, int(math.ceil(bb[3] - bb[1])) + 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.multiline_text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=color + (255,), spacing=spacing, align=align,
                     stroke_width=stroke, stroke_fill=(stroke_color or color) + (255,))
    return im


def vtext_img(txt, kind="kai", size=90, color=INK, gap=1.08):
    """Vertical text, one column per segment separated by '|' (right to left)."""
    cols = txt.split("|")
    f = font(kind, size)
    hmax = max(len(c) for c in cols)
    cw = int(size * 1.35)
    im = Image.new("RGBA", (cw * len(cols) + 20, int(hmax * size * gap) + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for ci, col in enumerate(cols):
        x = im.width - 10 - cw * ci - cw / 2
        for ri, ch in enumerate(col):
            y = 15 + ri * size * gap + size / 2
            if ch in "，。、；：":
                d.text((x + size * 0.3, y - size * 0.25), ch, font=f, fill=color + (255,), anchor="mm")
            else:
                d.text((x, y), ch, font=f, fill=color + (255,), anchor="mm")
    return im


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    al = im.getchannel("A").point(lambda v: int(v * max(0.0, a)))
    im.putalpha(al)
    return im


def paste_c(dst, im, cx, cy, a=1.0):
    if a <= 0.003:
        return
    if a < 0.999:
        im = fade(im, a)
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def wipe(im, frac, direction="down"):
    """Reveal fraction of image (soft edge)."""
    frac = max(0.0, min(1.0, frac))
    if frac >= 0.999:
        return im
    w, h = im.size
    m = np.zeros((h, w), np.float32)
    if direction == "down":
        edge = frac * (h + 80) - 40
        y = np.arange(h)[:, None]
        m = np.clip((edge - y) / 40 + 0.5, 0, 1) * np.ones((1, w))
    elif direction == "left":  # reveal from right to left (vertical columns)
        edge = w - frac * (w + 80) + 40
        x = np.arange(w)[None, :]
        m = np.clip((x - edge) / 40 + 0.5, 0, 1) * np.ones((h, 1))
    else:  # right
        edge = frac * (w + 80) - 40
        x = np.arange(w)[None, :]
        m = np.clip((edge - x) / 40 + 0.5, 0, 1) * np.ones((h, 1))
    a = np.asarray(im.getchannel("A"), np.float32) * m
    out = im.copy()
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


@functools.lru_cache(maxsize=8)
def figure(scale=1.0, color=INK, seed=0):
    """Seated meditator silhouette (lotus posture), soft ink, RGBA."""
    s = scale
    w, h = int(420 * s), int(470 * s)
    big = 2
    m = Image.new("L", (w * big, h * big), 0)
    d = ImageDraw.Draw(m)
    P = lambda x, y: (x * s * big, y * s * big)
    # head + topknot
    d.ellipse([*P(166, 34), *P(254, 130)], fill=255)
    # robe/body outline
    body = [(196, 120), (224, 120), (236, 150), (292, 172), (318, 200), (332, 260), (350, 320), (372, 356),
            (408, 392), (414, 428), (396, 452), (24, 452), (6, 428), (12, 392), (48, 356), (70, 320),
            (88, 260), (102, 200), (128, 172), (184, 150)]
    d.polygon([P(x, y) for x, y in body], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(9 * s * big))
    m = m.point(lambda v: 0 if v < 70 else min(255, int((v - 70) * 2.2)))
    d = ImageDraw.Draw(m)
    # robe folds / hands (lighter strokes)
    d.ellipse([*P(170, 330), *P(250, 368)], fill=170)
    d.line([P(150, 200), P(196, 340)], fill=200, width=int(5 * s * big))
    d.line([P(270, 200), P(226, 340)], fill=200, width=int(5 * s * big))
    d.arc([*P(60, 360), *P(360, 470)], 190, 350, fill=190, width=int(5 * s * big))
    m = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2 * s))
    a = np.asarray(m, np.float32)
    r = rng(seed)
    tex = np.asarray(Image.fromarray((r.random((h // 3 + 1, w // 3 + 1)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    a = a * (0.86 + 0.14 * tex)
    return ink_layer(Image.fromarray(a.clip(0, 255).astype(np.uint8)), color)


@functools.lru_cache(maxsize=8)
def walker(scale=1.0, phase=0, color=INK):
    s = scale
    w, h = int(200 * s), int(460 * s)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    cx = w / 2
    d.ellipse([cx - 32 * s, 10 * s, cx + 32 * s, 80 * s], fill=250)
    d.polygon([(cx - 40 * s, 85 * s), (cx + 40 * s, 85 * s), (cx + 62 * s, 330 * s), (cx - 62 * s, 330 * s)], fill=245)
    sw = [(-1, 1), (0, 0), (1, -1), (0, 0)][phase % 4]
    d.line([(cx - 15 * s, 320 * s), (cx - 15 * s + sw[0] * 35 * s, h - 8 * s)], fill=245, width=int(26 * s))
    d.line([(cx + 15 * s, 320 * s), (cx + 15 * s + sw[1] * 35 * s, h - 8 * s)], fill=245, width=int(26 * s))
    m = m.filter(ImageFilter.GaussianBlur(2 * s))
    return ink_layer(m, color)


@functools.lru_cache(maxsize=4)
def bamboo(seed=7, n=5, height=1500, dark=False):
    """Bamboo cluster (RGBA, full canvas), from right edge."""
    r = rng(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for i in range(n):
        x = W - 60 - i * r.uniform(60, 110)
        lean = r.uniform(-0.08, 0.03)
        w0 = r.uniform(14, 24)
        y = H + 50
        top = H - height * r.uniform(0.75, 1.05)
        seg = r.uniform(130, 190)
        val = int(r.uniform(150, 235))
        while y > top:
            y2 = y - seg
            xa, xb = x + lean * (H - y), x + lean * (H - y2)
            d.polygon([(xa - w0 / 2, y), (xa + w0 / 2, y), (xb + w0 / 2 * 0.95, y2 + 6), (xb - w0 / 2 * 0.95, y2 + 6)], fill=val)
            d.line([(xb - w0 * 0.7, y2 + 4), (xb + w0 * 0.7, y2 + 4)], fill=min(255, val + 20), width=4)
            # leaves
            if y2 < H - 500 and r.random() < 0.7:
                for _ in range(r.integers(2, 5)):
                    ang = r.uniform(-2.6, -0.4) if r.random() < 0.5 else r.uniform(0.4 + math.pi, 2.6 + math.pi)
                    ang = r.uniform(0, 2 * math.pi)
                    L = r.uniform(90, 170)
                    ex, ey = xb + math.cos(ang) * L, y2 + abs(math.sin(ang)) * L * 0.6 + 10
                    px, py = -math.sin(ang) * 11, math.cos(ang) * 11
                    d.polygon([(xb, y2 + 6), (xb + (ex - xb) * 0.4 + px, y2 + (ey - y2) * 0.4 + py), (ex, ey),
                               (xb + (ex - xb) * 0.4 - px, y2 + (ey - y2) * 0.4 - py)], fill=int(val * 0.9))
            y = y2
    m = m.filter(ImageFilter.GaussianBlur(1.6))
    col = INK if not dark else (20, 24, 30)
    return ink_layer(m, col)


def sway(layer, t, amp=6.0, speed=0.7, pivot_y=H):
    """Shear sway of a full-canvas layer around bottom."""
    k = amp * math.sin(t * speed) / H
    return layer.transform(layer.size, Image.AFFINE, (1, k, -k * pivot_y, 0, 1, 0), resample=Image.BILINEAR)


def blur_shadow(layer, radius=14, alpha=0.35, offset=(-160, 40)):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(radius)).point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", layer.size, INK + (0,))
    sh.putalpha(a)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, offset if offset[0] >= 0 and offset[1] >= 0 else (0, 0))
    if offset[0] < 0 or offset[1] < 0:
        out = sh.transform(sh.size, Image.AFFINE, (1, 0, -offset[0], 0, 1, -offset[1]))
    return out


def light_glow(cx, cy, r, color=DAWN, alpha=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 1.8 * 255 * alpha
    lay = Image.new("RGBA", (W, H), color + (0,))
    lay.putalpha(Image.fromarray(a.astype(np.uint8)))
    return lay


def ink_circle(frac, r=300, width=46, seed=2, color=INK):
    """Enso brush circle drawn up to frac (0..1); RGBA square."""
    s = int(2 * r + width * 3)
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)
    rr = rng(seed)
    n = int(360 * frac)
    c = s / 2
    for i in range(n):
        a = math.radians(-90 + i)
        wv = width * (0.55 + 0.45 * math.sin(i / 360 * math.pi) ** 0.6) * (1 - 0.5 * (i / 360) ** 3)
        rad = r + 6 * math.sin(i / 23.0)
        x, y = c + rad * math.cos(a), c + rad * math.sin(a)
        d.ellipse([x - wv / 2, y - wv / 2, x + wv / 2, y + wv / 2], fill=int(220 + 30 * rr.random()))
    m = m.filter(ImageFilter.GaussianBlur(1.5))
    return ink_layer(m, color)


def arrow(d, x0, y0, x1, y1, color=INK, width=10, head=34):
    d.line([(x0, y0), (x1, y1)], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    p1 = (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45))
    p2 = (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))
    d.polygon([(x1, y1), p1, p2], fill=color)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return ease((t - a) / max(1e-6, b - a))
