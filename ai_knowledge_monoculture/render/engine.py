"""Core drawing helpers for the vertical video (1080x1920).

Shapes and curves are drawn with pycairo (anti-aliased vectors); text is rendered
with Pillow/FreeType into alpha masks (cached) and painted through cairo, so CJK
fonts, weights and colours are fully controllable.
"""
import math
import os
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

# ---------------------------------------------------------------- palette
def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

BG0 = "#05080F"      # deep blue-black
BG1 = "#0B1424"
CYAN = "#3FD3E8"     # "one voice"  -> the new tyrant
ORANGE = "#FF9A3C"   # "many voices" -> the new mob
WHITE = "#EEF3F8"
GREY = "#8C98A8"
DIM = "#4A5568"
RED = "#E5484D"

# ---------------------------------------------------------------- fonts
NOTO = "/usr/share/fonts/opentype/noto"
FONTS = {
    "sans": (f"{NOTO}/NotoSansCJK-Regular.ttc", 2),
    "sans_light": (f"{NOTO}/NotoSansCJK-Light.ttc", 2),
    "sans_medium": (f"{NOTO}/NotoSansCJK-Medium.ttc", 2),
    "sans_bold": (f"{NOTO}/NotoSansCJK-Bold.ttc", 2),
    "sans_black": (f"{NOTO}/NotoSansCJK-Black.ttc", 2),
    "serif": (f"{NOTO}/NotoSerifCJK-Regular.ttc", 2),
    "serif_medium": (f"{NOTO}/NotoSerifCJK-Medium.ttc", 2),
    "serif_bold": (f"{NOTO}/NotoSerifCJK-Bold.ttc", 2),
    "serif_black": (f"{NOTO}/NotoSerifCJK-Black.ttc", 2),
    "mono": (f"{FONT_DIR}/JetBrainsMono-Regular.ttf", 0),
    "mono_bold": (f"{FONT_DIR}/JetBrainsMono-Bold.ttf", 0),
    "mono_cjk": (f"{NOTO}/NotoSansCJK-Regular.ttc", 7),
    "fell": (f"{FONT_DIR}/IMFellEnglish-Regular.ttf", 0),
    "fell_italic": (f"{FONT_DIR}/IMFellEnglish-Italic.ttf", 0),
    "fell_sc": (f"{FONT_DIR}/IMFellEnglishSC-Regular.ttf", 0),
}


@lru_cache(maxsize=256)
def font(name, size):
    path, idx = FONTS[name]
    return ImageFont.truetype(path, int(size), index=idx)


# ---------------------------------------------------------------- text masks
class TextMask:
    """An A8-like alpha mask of a text string plus its metrics."""

    def __init__(self, arr, ox, oy, adv, asc, desc):
        self.arr = arr            # uint8 HxW alpha
        self.ox, self.oy = ox, oy  # offset of mask relative to pen origin (baseline-left)
        self.adv = adv            # advance width
        self.asc, self.desc = asc, desc
        h, w = arr.shape
        # cairo ARGB32 white text, premultiplied: (a,a,a,a)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
        buf = np.zeros((h, stride // 4, 4), np.uint8)
        buf[:, :w, 0] = arr
        buf[:, :w, 1] = arr
        buf[:, :w, 2] = arr
        buf[:, :w, 3] = arr
        self._buf = buf
        self.surface = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)
        self.w, self.h = w, h


@lru_cache(maxsize=4096)
def text_mask(text, fname, size, tracking=0.0, blur=0.0):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    if tracking == 0:
        adv = f.getlength(text)
    else:
        adv = sum(f.getlength(c) for c in text) + tracking * size * max(0, len(text) - 1)
    pad = int(size * 0.5 + blur * 3) + 4
    wpx = int(math.ceil(adv)) + 2 * pad
    hpx = asc + desc + 2 * pad
    im = Image.new("L", (max(1, wpx), max(1, hpx)), 0)
    d = ImageDraw.Draw(im)
    if tracking == 0:
        d.text((pad, pad), text, font=f, fill=255)
    else:
        x = pad
        for c in text:
            d.text((x, pad), c, font=f, fill=255)
            x += f.getlength(c) + tracking * size
    if blur > 0:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(im, dtype=np.uint8).copy()
    return TextMask(arr, -pad, -pad - asc, adv, asc, desc)


def text_width(text, fname, size, tracking=0.0):
    return text_mask(text, fname, size, tracking).adv


def draw_text(ctx, text, x, y, fname="sans", size=40, color=WHITE, alpha=1.0,
              anchor="ls", tracking=0.0, glow=0.0, glow_color=None, glow_alpha=0.6,
              shadow=0.0, shadow_alpha=0.75):
    """Draw text. anchor: first char l/m/r (horizontal), second s/m/t (baseline / middle / top)."""
    if not text or alpha <= 0.002:
        return 0
    tm = text_mask(text, fname, size, tracking)
    hx = {"l": 0, "m": -tm.adv / 2, "r": -tm.adv}[anchor[0]]
    vy = {"s": 0, "m": (tm.asc - tm.desc) / 2 * 0.86, "t": tm.asc * 0.88}[anchor[1]]
    px, py = x + hx, y + vy
    if shadow > 0:
        sm = text_mask(text, fname, size, tracking, blur=shadow)
        ctx.save()
        ctx.set_source_rgba(0, 0, 0, shadow_alpha * alpha)
        ctx.mask_surface(sm.surface, px + sm.ox + 2, py + sm.oy + 3)
        ctx.restore()
    if glow > 0:
        gm = text_mask(text, fname, size, tracking, blur=glow)
        r, g, b, _ = hexrgb(glow_color or color)
        ctx.save()
        ctx.set_source_rgba(r, g, b, glow_alpha * alpha)
        ctx.mask_surface(gm.surface, px + gm.ox, py + gm.oy)
        ctx.restore()
    r, g, b, a0 = hexrgb(color) if isinstance(color, str) else color
    ctx.save()
    ctx.set_source_rgba(r, g, b, a0 * alpha)
    ctx.mask_surface(tm.surface, px + tm.ox, py + tm.oy)
    ctx.restore()
    return tm.adv


# CJK-aware line wrapping -------------------------------------------------
NO_START = set("，。、；：！？）》」』”’…—,.;:!?)]%")
NO_END = set("（《「『“‘([")


def wrap(text, fname, size, max_w, tracking=0.0):
    """Greedy wrap that treats CJK chars individually and keeps Latin words whole."""
    tokens = []
    buf = ""
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch in "'’-@$.,%:/&"):
            buf += ch
        else:
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
    if buf:
        tokens.append(buf)
    lines, cur = [], ""
    for tok in tokens:
        if tok == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + tok
        if text_width(trial.strip(), fname, size, tracking) <= max_w or not cur.strip():
            cur = trial
        else:
            # keep punctuation off the start of a line
            if tok in NO_START or (tok[0] in NO_START):
                cur = trial
                continue
            if cur and cur[-1] in NO_END:
                carry = cur[-1]
                lines.append(cur[:-1].rstrip())
                cur = carry + tok.lstrip()
            else:
                lines.append(cur.rstrip())
                cur = tok.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def draw_paragraph(ctx, text, x, y, max_w, fname="sans", size=40, color=WHITE, alpha=1.0,
                   line_h=1.45, align="l", tracking=0.0, **kw):
    lines = wrap(text, fname, size, max_w, tracking)
    for i, ln in enumerate(lines):
        if align == "l":
            draw_text(ctx, ln, x, y + i * size * line_h, fname, size, color, alpha, "ls", tracking, **kw)
        elif align == "m":
            draw_text(ctx, ln, x + max_w / 2, y + i * size * line_h, fname, size, color, alpha, "ms", tracking, **kw)
        else:
            draw_text(ctx, ln, x + max_w, y + i * size * line_h, fname, size, color, alpha, "rs", tracking, **kw)
    return len(lines) * size * line_h


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def fade(t, t0, dur=0.4):
    return ease_out((t - t0) / dur) if dur > 0 else float(t >= t0)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    a = hexrgb(c1) if isinstance(c1, str) else c1
    b = hexrgb(c2) if isinstance(c2, str) else c2
    return tuple(lerp(a[i], b[i], t) for i in range(4))


# ---------------------------------------------------------------- canvas
def new_canvas():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    return surf, ctx


def set_color(ctx, c, alpha=1.0):
    r, g, b, a = hexrgb(c) if isinstance(c, str) else c
    ctx.set_source_rgba(r, g, b, a * alpha)


def fill_bg(ctx, top=BG0, bottom=BG1):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, *hexrgb(top))
    g.add_color_stop_rgba(1, *hexrgb(bottom))
    ctx.set_source(g)
    ctx.paint()


def rounded_rect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


_KEEP = {}


def np_to_surface(arr_rgba):
    """uint8 RGBA (straight alpha) -> cairo ARGB32 surface (premultiplied BGRA)."""
    h, w, _ = arr_rgba.shape
    a = arr_rgba[..., 3:4].astype(np.uint16)
    rgb = (arr_rgba[..., :3].astype(np.uint16) * a // 255).astype(np.uint8)
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    buf = np.zeros((h, stride // 4, 4), np.uint8)
    buf[:, :w, 0] = rgb[..., 2]
    buf[:, :w, 1] = rgb[..., 1]
    buf[:, :w, 2] = rgb[..., 0]
    buf[:, :w, 3] = arr_rgba[..., 3]
    s = cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, stride)
    _KEEP[id(s)] = buf  # keep the pixel buffer alive as long as the surface is used
    return s


def pil_to_surface(im):
    return np_to_surface(np.asarray(im.convert("RGBA")))


def surface_to_np(surf):
    """cairo surface -> uint8 RGB array."""
    surf.flush()
    buf = np.ndarray((surf.get_height(), surf.get_stride() // 4, 4), np.uint8, surf.get_data())
    return buf[:, : surf.get_width(), [2, 1, 0]].copy()


def save_png(surf, path):
    Image.fromarray(surface_to_np(surf)).save(path)


# ---------------------------------------------------------------- textures
@lru_cache(maxsize=8)
def grain_surface(seed=0, strength=26, mono=True, size=(W, H)):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (size[1], size[0]))
    v = np.clip(128 + n * strength, 0, 255).astype(np.uint8)
    rgba = np.dstack([v, v, v, np.full_like(v, 255)])
    return np_to_surface(rgba)


def overlay_grain(ctx, seed, alpha=0.06, op=cairo.OPERATOR_OVERLAY):
    ctx.save()
    ctx.set_operator(op)
    ctx.set_source_surface(grain_surface(seed % 6), 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def vignette(ctx, strength=0.55, color=(0, 0, 0)):
    g = cairo.RadialGradient(W / 2, H * 0.45, H * 0.25, W / 2, H * 0.45, H * 0.75)
    g.add_color_stop_rgba(0, *color, 0)
    g.add_color_stop_rgba(1, *color, strength)
    ctx.set_source(g)
    ctx.paint()


# ---------------------------------------------------------------- chrome
SUB_Y = 1440          # subtitle block centre (keeps clear of 视频号 top/bottom overlays)
SAFE_TOP = 230


def draw_subtitle(ctx, text, alpha=1.0, size=52, y=SUB_Y, max_w=900, color=WHITE, band=False):
    if not text:
        return
    lines = wrap(text, "sans_medium", size, max_w)
    lh = size * 1.38
    y0 = y - (len(lines) - 1) * lh / 2
    if band:  # dark pill behind the text for light backgrounds (paper / parchment)
        wmax = max(text_width(ln, "sans_medium", size) for ln in lines)
        rounded_rect(ctx, W / 2 - wmax / 2 - 30, y0 - size * 0.95, wmax + 60, lh * (len(lines) - 1) + size * 1.9, 22)
        ctx.set_source_rgba(0.05, 0.04, 0.03, 0.62 * alpha)
        ctx.fill()
    for i, ln in enumerate(lines):
        draw_text(ctx, ln, W / 2, y0 + i * lh, "sans_medium", size, color, alpha, "mm",
                  shadow=6, shadow_alpha=0.9)


def draw_chapter_tag(ctx, label, alpha=1.0, color=GREY, accent=CYAN, dark=True):
    x, y = 72, SAFE_TOP + 40
    set_color(ctx, accent, alpha)
    ctx.rectangle(x, y - 26, 6, 32)
    ctx.fill()
    draw_text(ctx, label, x + 22, y, "sans_medium", 30, color, alpha, "ls")


def draw_series_tag(ctx, alpha=1.0, color=GREY):
    draw_text(ctx, "AI 知识", W - 72, SAFE_TOP + 40, "sans_bold", 28, color, alpha * 0.8, "rs",
              tracking=0.08)
