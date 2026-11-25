# -*- coding: utf-8 -*-
"""Shared drawing utilities: fonts, cached text sprites, compositing, paper texture, easing."""
import os, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 25
FD = "/tmp/claude-0/work/fonts"
SERIF_SC = f"{FD}/NotoSerifSC[wght].ttf"
SERIF_TC = f"{FD}/NotoSerifTC[wght].ttf"
SANS_SC = f"{FD}/NotoSansSC[wght].ttf"
BRUSH = f"{FD}/MaShanZheng-Regular.ttf"

INK = (28, 26, 24)
PAPER = (236, 228, 210)
CINNABAR = (178, 48, 36)
GOLD = (222, 186, 120)
MIST = (200, 214, 228)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


@functools.lru_cache(maxsize=64)
def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def _wrap(text, f, maxw):
    """Greedy wrap for CJK text; avoids putting closing punctuation at line start."""
    lines, cur = [], ""
    no_start = set("，。、；：？！」』）》”’,.;:?!%")
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        t = cur + ch
        if f.getlength(t) > maxw and cur:
            if ch in no_start:
                cur = t; continue
            lines.append(cur); cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(text, f, maxw):
    """Wrap into the minimal number of lines, then balance line lengths."""
    lines = _wrap(text, f, maxw)
    n = len(lines)
    if n <= 1:
        return lines
    lo, hi = maxw * 0.5, maxw
    best = lines
    for _ in range(14):
        mid = (lo + hi) / 2
        L = _wrap(text, f, mid)
        if len(L) <= n:
            best, hi = L, mid
        else:
            lo = mid
    return best


@functools.lru_cache(maxsize=512)
def text_sprite(text, path, size, color=(255, 255, 255), weight=None, maxw=980, align="center",
                spacing=1.35, shadow=0, stroke=0, stroke_color=(0, 0, 0), balance=True, tracking=0):
    """Render text to an RGBA float32 sprite (premultiplied not used). Returns np array HxWx4 (0..1)."""
    f = font(path, size, weight)
    lines = balanced_wrap(text, f, maxw) if balance else _wrap(text, f, maxw)
    lh = int(size * spacing)
    widths = [f.getlength(l) + tracking * max(0, len(l) - 1) for l in lines]
    w = int(max(widths) + 2 * (stroke + shadow) + 8)
    h = int(lh * len(lines) + size * 0.4 + 2 * (stroke + shadow) + 8)
    pad = shadow * 3 + 4
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def draw_lines(dd, fill, sw=0, sc=None, off=(0, 0)):
        for i, l in enumerate(lines):
            lw = widths[i]
            x = pad + stroke + shadow + 4 + (0 if align == "left" else (max(widths) - lw) / (2 if align == "center" else 1))
            y = pad + stroke + shadow + 4 + i * lh
            if tracking:
                for ch in l:
                    dd.text((x + off[0], y + off[1]), ch, font=f, fill=fill, stroke_width=sw, stroke_fill=sc)
                    x += f.getlength(ch) + tracking
            else:
                dd.text((x + off[0], y + off[1]), l, font=f, fill=fill, stroke_width=sw, stroke_fill=sc)

    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_lines(ImageDraw.Draw(sh), (0, 0, 0, 200), sw=stroke + 2, sc=(0, 0, 0, 200), off=(0, 2))
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        img = Image.alpha_composite(img, sh)
        d = ImageDraw.Draw(img)
    draw_lines(d, tuple(color) + (255,), sw=stroke, sc=tuple(stroke_color) + (255,) if stroke else None)
    a = np.asarray(img).astype(np.float32) / 255.0
    return a


@functools.lru_cache(maxsize=256)
def vtext_sprite(text, path, size, color=INK, weight=None, col_len=12, col_gap=1.5, char_gap=1.12):
    """Vertical (竖排) text, columns right-to-left. Punctuation is kept small/offset."""
    f = font(path, size, weight)
    cols, cur = [], ""
    for ch in text:
        if ch == "\n":
            cols.append(cur); cur = ""; continue
        cur += ch
        if len(cur) >= col_len and ch in "，。；：、":
            cols.append(cur); cur = ""
    if cur:
        cols.append(cur)
    step = int(size * char_gap)
    cw = int(size * col_gap)
    hmax = max(len(c) for c in cols) * step + size
    w = cw * len(cols) + size
    img = Image.new("RGBA", (w, hmax), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for ci, c in enumerate(cols):
        x = w - size // 2 - (ci + 1) * cw + (cw - size) // 2
        y = size // 4
        for ch in c:
            if ch in "，。、；：":
                d.text((x + size * 0.55, y - size * 0.45), ch, font=f, fill=tuple(color) + (255,))
                y += int(step * 0.45)
            else:
                d.text((x, y), ch, font=f, fill=tuple(color) + (255,))
                y += step
    return np.asarray(img).astype(np.float32) / 255.0


def blit(dst, spr, x, y, alpha=1.0, anchor="center", tint=None):
    """Alpha-composite float sprite (HxWx4 0..1) onto float32 dst (HxWx3 0..1) at (x,y)."""
    if alpha <= 0.002:
        return
    sh, sw = spr.shape[:2]
    if anchor == "center":
        x0, y0 = int(round(x - sw / 2)), int(round(y - sh / 2))
    elif anchor == "top":
        x0, y0 = int(round(x - sw / 2)), int(round(y))
    elif anchor == "topleft":
        x0, y0 = int(round(x)), int(round(y))
    elif anchor == "bottom":
        x0, y0 = int(round(x - sw / 2)), int(round(y - sh))
    else:
        raise ValueError(anchor)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(dst.shape[1], x0 + sw), min(dst.shape[0], y0 + sh)
    if X1 <= X0 or Y1 <= Y0:
        return
    s = spr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    a = s[..., 3:4] * alpha
    rgb = s[..., :3] if tint is None else np.array(tint, np.float32) / 255.0
    d = dst[Y0:Y1, X0:X1]
    d *= (1 - a)
    d += rgb * a


def scale_sprite(spr, k):
    if abs(k - 1) < 1e-3:
        return spr
    h, w = spr.shape[:2]
    return cv2.resize(spr, (max(1, int(w * k)), max(1, int(h * k))), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)


def rgb(c):
    return np.array(c, np.float32) / 255.0


@functools.lru_cache(maxsize=4)
def paper_texture(w=W, h=H, seed=3, tone=PAPER):
    """宣纸: warm base, low-frequency mottling, fibres, soft vignette."""
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * rgb(tone)
    low = cv2.resize(rng.normal(0, 1, (h // 60, w // 60)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    mid = cv2.GaussianBlur(rng.normal(0, 1, (h // 4, w // 4)).astype(np.float32), (0, 0), 2)
    mid = cv2.resize(mid, (w, h), interpolation=cv2.INTER_LINEAR)
    fib = np.zeros((h, w), np.float32)
    for _ in range(900):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, np.pi); L = rng.uniform(10, 60)
        x2, y2 = x + L * np.cos(ang), y + L * np.sin(ang)
        cv2.line(fib, (int(x), int(y)), (int(x2), int(y2)), float(rng.uniform(0.3, 1)), 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.7)
    n = 0.014 * low + 0.010 * mid - 0.05 * fib
    p = base * (1 + n[..., None]) + rng.normal(0, 0.006, (h, w, 1)).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx - w / 2) / (w * 0.75)) ** 2 + ((yy - h / 2) / (h * 0.7)) ** 2
    p *= (1 - 0.22 * np.clip(v, 0, 1.5))[..., None]
    return np.clip(p, 0, 1).astype(np.float32)


def vignette(img, k=0.45):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx - w / 2) / (w * 0.7)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2
    return img * (1 - k * np.clip(v, 0, 1.3))[..., None]


@functools.lru_cache(maxsize=8)
def vignette_mask(k=0.45, w=W, h=H):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = ((xx - w / 2) / (w * 0.7)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2
    return (1 - k * np.clip(v, 0, 1.3))[..., None].astype(np.float32)


def grain(img, t, amt=0.012):
    rng = np.random.default_rng(int(t * 1000) % 100000)
    g = rng.normal(0, amt, (H // 2, W // 2, 1)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return img + g


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
