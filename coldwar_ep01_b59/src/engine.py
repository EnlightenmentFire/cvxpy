"""Core 2D compositing engine: float32 RGB canvases, glow, text, noise, film finish.

Everything is display-referred float32 in [0, 1+]; additive light is soft-clipped at
the end. Canvas is portrait 1080x1920.
"""
import functools
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# ----------------------------------------------------------------------------
# palette (sRGB 0..1)
# ----------------------------------------------------------------------------


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


BG = hexc("#04070c")
BG2 = hexc("#0b1422")
US = hexc("#6ec1ff")        # US / American side: cold blue
US_DIM = hexc("#2b6fb8")
SU = hexc("#ffb547")        # Soviet side: amber
SU_DIM = hexc("#b8741c")
NEU = hexc("#d9dee5")       # neutral gray-white
NEU_DIM = hexc("#7d8794")
ALERT = hexc("#e8484c")     # "red light" alert dots only (not a side colour)
SONAR = hexc("#5dff9e")
HYPO = hexc("#ff2e9a")      # hypothetical magenta

# ----------------------------------------------------------------------------
# fonts
# ----------------------------------------------------------------------------
FONT_DIR = "/usr/share/fonts/opentype/noto"
_WEIGHTS = {
    "black": "NotoSansCJK-Black.ttc",
    "bold": "NotoSansCJK-Bold.ttc",
    "medium": "NotoSansCJK-Medium.ttc",
    "regular": "NotoSansCJK-Regular.ttc",
    "light": "NotoSansCJK-Light.ttc",
    "thin": "NotoSansCJK-Thin.ttc",
}
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"


@functools.lru_cache(maxsize=64)
def font(weight="bold", size=48):
    if weight == "mono":
        p = MONO if os.path.exists(MONO) else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        return ImageFont.truetype(p, size)
    if weight == "monobold":
        p = MONO_BOLD if os.path.exists(MONO_BOLD) else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        return ImageFont.truetype(p, size)
    return ImageFont.truetype(os.path.join(FONT_DIR, _WEIGHTS[weight]), size, index=2)  # 2 = SC


def has_cjk(s):
    return any("⺀" <= ch <= "鿿" or "＀" <= ch <= "￯" or "　" <= ch <= "〿" for ch in s)


@functools.lru_cache(maxsize=512)
def text_mask(text, weight="bold", size=48, tracking=0.0, stroke=0):
    """Render text to a float32 alpha mask (h, w). tracking in em units."""
    if weight in ("mono", "monobold") and has_cjk(text):
        weight = "medium" if weight == "mono" else "bold"
    f = font(weight, size)
    if tracking == 0:
        bbox = f.getbbox(text, stroke_width=stroke)
        w = bbox[2] - min(0, bbox[0]) + 4 + 2 * stroke
        h = int(size * 1.45) + 2 * stroke
        img = Image.new("L", (max(1, w), h), 0)
        d = ImageDraw.Draw(img)
        d.text((2 + stroke - min(0, bbox[0]), int(size * 0.12) + stroke), text, font=f, fill=255,
               stroke_width=stroke, stroke_fill=255)
    else:
        adv = [f.getlength(ch) + tracking * size for ch in text]
        w = int(sum(adv) + 6 + 2 * stroke)
        h = int(size * 1.45) + 2 * stroke
        img = Image.new("L", (max(1, w), h), 0)
        d = ImageDraw.Draw(img)
        x = 2 + stroke
        for ch, a in zip(text, adv):
            d.text((x, int(size * 0.12) + stroke), ch, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
            x += a
    m = np.asarray(img, np.float32) / 255.0
    # trim empty columns on the right
    cols = np.where(m.max(0) > 0)[0]
    if len(cols):
        m = m[:, : cols[-1] + 3]
    return m


def text_size(text, weight="bold", size=48, tracking=0.0):
    m = text_mask(text, weight, size, tracking)
    return m.shape[1], m.shape[0]


def blit_mask(canvas, mask, x, y, color, alpha=1.0, mode="over"):
    """Composite a single-channel mask at (x, y) top-left with color."""
    h, w = mask.shape
    x0, y0 = int(round(x)), int(round(y))
    x1, y1 = x0 + w, y0 + h
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(canvas.shape[1], x1), min(canvas.shape[0], y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return canvas
    m = mask[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0][..., None] * alpha
    region = canvas[cy0:cy1, cx0:cx1]
    col = np.asarray(color, np.float32)
    if mode == "add":
        region += m * col
    else:
        region *= (1 - m)
        region += m * col
    return canvas


def draw_text(canvas, text, x, y, size=48, weight="bold", color=NEU, alpha=1.0, anchor="lt",
              tracking=0.0, mode="over", glow=0.0, shadow=0.0):
    """anchor: two letters, horizontal l/m/r + vertical t/m/b."""
    m = text_mask(text, weight, size, tracking)
    h, w = m.shape
    ax, ay = anchor[0], anchor[1]
    if ax == "m":
        x -= w / 2
    elif ax == "r":
        x -= w
    if ay == "m":
        y -= h / 2
    elif ay == "b":
        y -= h
    if shadow > 0:
        sm = cv2.GaussianBlur(np.pad(m, 12), (0, 0), 5)
        blit_mask(canvas, sm, x - 12 + 2, y - 12 + 3, (0, 0, 0), alpha * shadow)
    if glow > 0:
        gm = cv2.GaussianBlur(np.pad(m, 24), (0, 0), 9)
        blit_mask(canvas, gm, x - 24, y - 24, color, alpha * glow, mode="add")
    blit_mask(canvas, m, x, y, color, alpha, mode)
    return w, h


# ----------------------------------------------------------------------------
# canvases, blur, glow
# ----------------------------------------------------------------------------

def canvas(color=BG):
    c = np.empty((H, W, 3), np.float32)
    c[:] = color
    return c


def vgrad(c0, c1, h=H, w=W, power=1.0):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** power
    return np.broadcast_to(c0 * (1 - t) + c1 * t, (h, w, 3)).copy()


def radial(cx, cy, r, h=H, w=W, power=2.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(r, 1e-6)
    return np.clip(1 - d, 0, 1) ** power


_grid_cache = {}


def grid(h=H, w=W):
    key = (h, w)
    if key not in _grid_cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        _grid_cache[key] = (xx, yy)
    return _grid_cache[key]


def blur(img, sigma):
    if sigma <= 0:
        return img
    if sigma > 6:
        f = int(min(8, max(2, sigma // 3)))
        h, w = img.shape[:2]
        small = cv2.resize(img, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sigma / f)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(img, (0, 0), sigma)


def glow(layer, sigmas=(3, 10, 28, 70), weights=(0.9, 0.6, 0.45, 0.35)):
    out = np.zeros_like(layer)
    for s, wgt in zip(sigmas, weights):
        out += blur(layer, s) * wgt
    return out


def softclip(x, knee=0.82):
    y = np.where(x < knee, x, knee + (1 - knee) * np.tanh((x - knee) / (1 - knee)))
    return np.clip(y, 0, 1)


# ----------------------------------------------------------------------------
# noise
# ----------------------------------------------------------------------------

def value_noise(h, w, scale, seed=0, octaves=4, persistence=0.55):
    """fbm made of upsampled random grids. scale = feature size in px of first octave."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 3), max(2, int(w / s) + 3)
        g = rng.random((gh, gw), dtype=np.float32)
        up = cv2.resize(g, (int(gw * s), int(gh * s)), interpolation=cv2.INTER_CUBIC)
        oy, ox = rng.integers(0, max(1, up.shape[0] - h)), rng.integers(0, max(1, up.shape[1] - w))
        up = up[oy:oy + h, ox:ox + w]
        if up.shape != (h, w):
            up = cv2.resize(up, (w, h))
        out += amp * up
        tot += amp
        amp *= persistence
        s = max(1.5, s / 2)
    return out / tot


@functools.lru_cache(maxsize=8)
def noise_tile(size=512, scale=64, seed=0, octaves=4):
    """Periodic-ish noise tile for scrolling textures."""
    n = value_noise(size * 2, size * 2, scale, seed, octaves)
    # make it tileable by blending with shifted copy
    a = n[:size, :size]
    b = n[size:, size:]
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) / size
    wgt = np.sin(np.pi * xx) * np.sin(np.pi * yy)
    return (a * wgt + b * (1 - wgt)).astype(np.float32)


def scroll_noise(h, w, tile, ox, oy, zoom=1.0):
    th, tw = tile.shape
    xx, yy = grid(h, w)
    mx = ((xx / zoom + ox) % tw).astype(np.float32)
    my = ((yy / zoom + oy) % th).astype(np.float32)
    return cv2.remap(tile, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


# ----------------------------------------------------------------------------
# film finish
# ----------------------------------------------------------------------------
_vig = None


def vignette(img, strength=0.32):
    global _vig
    if _vig is None:
        xx, yy = grid()
        d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        _vig = (1 - np.clip(d, 0, 1.4) ** 2.2 * 0.5).astype(np.float32)[..., None]
    v = 1 - (1 - _vig) * (strength / 0.32)
    return img * v


def grain(img, amount=0.012, seed=None):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((H // 2, W // 2), dtype=np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = img.mean(2, keepdims=True)
    # more grain in mid-tones, less in black (keeps blacks clean for the encoder)
    wgt = np.clip(lum * 3.0, 0.15, 1.0)
    return img + n[..., None] * amount * wgt


def finish(img, vig=0.32, grain_amt=0.010, seed=None):
    img = vignette(img, vig)
    img = softclip(img)
    if grain_amt > 0:
        img = grain(img, grain_amt, seed)
    return np.clip(img, 0, 1)


def to_u8(img):
    # ordered dither to avoid banding in dark gradients
    return np.clip(img * 255.0 + (_bayer() - 0.5), 0, 255).astype(np.uint8)


@functools.lru_cache(maxsize=1)
def _bayer():
    b = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0
    t = np.tile(b, (H // 4 + 1, W // 4 + 1))[:H, :W]
    return t[..., None]


def save_png(img, path):
    Image.fromarray(to_u8(img)).save(path)


# ----------------------------------------------------------------------------
# shapes (anti-aliased via cv2 on uint8 masks, optional supersampling)
# ----------------------------------------------------------------------------

def mask_polyline(pts_list, thickness=1.5, h=H, w=W, closed=False, ss=2):
    m = np.zeros((h * ss, w * ss), np.uint8)
    shift = 4
    k = (1 << shift) * ss
    for pts in pts_list:
        if len(pts) < 2:
            continue
        p = np.round(np.asarray(pts, np.float64) * k).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(m, [p], closed, 255, max(1, int(round(thickness * ss))), cv2.LINE_AA, shift)
    if ss > 1:
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255.0


def mask_poly(pts_list, h=H, w=W, ss=2):
    m = np.zeros((h * ss, w * ss), np.uint8)
    shift = 4
    k = (1 << shift) * ss
    polys = [np.round(np.asarray(p, np.float64) * k).astype(np.int32).reshape(-1, 1, 2) for p in pts_list if len(p) >= 3]
    if polys:
        cv2.fillPoly(m, polys, 255, cv2.LINE_AA, shift)
    if ss > 1:
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255.0


def mask_circle(cx, cy, r, h=H, w=W, fill=True, thickness=2.0, ss=2):
    m = np.zeros((h * ss, w * ss), np.uint8)
    shift = 4
    k = (1 << shift) * ss
    cv2.circle(m, (int(round(cx * k)), int(round(cy * k))), int(round(r * k)), 255,
               -1 if fill else max(1, int(round(thickness * ss))), cv2.LINE_AA, shift)
    if ss > 1:
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255.0


def mask_ellipse(cx, cy, rx, ry, angle=0.0, h=H, w=W, fill=True, thickness=2.0, ss=2, a0=0, a1=360):
    m = np.zeros((h * ss, w * ss), np.uint8)
    shift = 4
    k = (1 << shift) * ss
    cv2.ellipse(m, (int(round(cx * k)), int(round(cy * k))), (int(round(rx * k)), int(round(ry * k))),
                angle, a0, a1, 255, -1 if fill else max(1, int(round(thickness * ss))), cv2.LINE_AA, shift)
    if ss > 1:
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255.0


def paint(canvas, mask, color, alpha=1.0, mode="over"):
    m = mask[..., None] * alpha
    col = np.asarray(color, np.float32)
    if mode == "add":
        canvas += m * col
    else:
        canvas *= (1 - m)
        canvas += m * col
    return canvas


def dashed(pts, dash=14, gap=10):
    """Split a polyline into dash segments."""
    pts = np.asarray(pts, np.float32)
    seg = np.diff(pts, axis=0)
    L = np.r_[0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    out = []
    s = 0.0
    while s < L[-1]:
        e = min(L[-1], s + dash)
        ts = np.linspace(s, e, max(2, int((e - s) / 3) + 2))
        xs = np.interp(ts, L, pts[:, 0])
        ys = np.interp(ts, L, pts[:, 1])
        out.append(np.stack([xs, ys], 1))
        s = e + gap
    return out


# ----------------------------------------------------------------------------
# easing
# ----------------------------------------------------------------------------

def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp01(x)
    return x ** 3


def ramp(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp01((t - a) / (b - a))


def lerp(a, b, t):
    return a + (b - a) * t


# ----------------------------------------------------------------------------
# HUD elements shared by scenes
# ----------------------------------------------------------------------------
SAFE_TOP = 220       # 视频号顶部遮挡（标题栏/状态栏）
SAFE_BOTTOM = 1920 - 470  # 底部遮挡（文案、按钮）
SUB_Y = 1335         # 字幕基线区（在安全区内）


def subtitle(canvas, text, alpha=1.0, y=SUB_Y, size=50, color=NEU):
    """Narration subtitle: up to two lines, centered, with soft shadow plate."""
    lines = text.split("\n")
    lh = int(size * 1.42)
    total = lh * len(lines)
    y0 = y - total / 2
    # soft dark plate behind
    maxw = max(text_size(l, "bold", size)[0] for l in lines)
    plate = np.zeros((int(total + 70), int(maxw + 150)), np.float32)
    plate[35:-35, 75:-75] = 1
    plate = cv2.GaussianBlur(plate, (0, 0), 22)
    blit_mask(canvas, plate, W / 2 - plate.shape[1] / 2, y0 - 35, (0, 0, 0), 0.55 * alpha)
    for i, l in enumerate(lines):
        draw_text(canvas, l, W / 2, y0 + i * lh, size=size, weight="bold", color=color, alpha=alpha,
                  anchor="mt", shadow=0.8)
    return canvas


def corner_tag(canvas, text, x=64, y=SAFE_TOP + 12, color=NEU_DIM, size=26, alpha=1.0, anchor="lt"):
    return draw_text(canvas, text, x, y, size=size, weight="mono", color=color, alpha=alpha,
                     anchor=anchor, tracking=0.05)


def hypo_frame(canvas, t=0.0, alpha=1.0, scale=1.0):
    """「假想」marker: thin border box with the word, top-left, plus thin frame line."""
    a = alpha
    pad = 46
    # thin full-frame border
    m = np.zeros((H, W), np.float32)
    cv2.rectangle(m, (pad, SAFE_TOP - 40), (W - pad, SAFE_BOTTOM + 60), 1.0, 2, cv2.LINE_AA)
    paint(canvas, m, HYPO * 1.0 + 0.15, 0.55 * a)
    size = int(46 * scale)
    tw, th = text_size("假想", "black", size, 0.25)
    x, y = 70, SAFE_TOP + 4
    box = np.zeros((H, W), np.float32)
    cv2.rectangle(box, (x - 16, int(y - 6)), (int(x + tw + 14), int(y + th + 2)), 1.0, 2, cv2.LINE_AA)
    paint(canvas, box, (1.0, 0.85, 0.95), 0.95 * a)
    draw_text(canvas, "假想", x, y, size=size, weight="black", color=(1.0, 0.9, 0.97), alpha=a, tracking=0.25)
    draw_text(canvas, "HYPOTHETICAL · 以下画面并未发生", x + tw + 30, y + th / 2 - 2, size=22, weight="mono",
              color=(1.0, 0.75, 0.9), alpha=0.85 * a, anchor="lm")
    return canvas


def chroma_shift(img, px=3):
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], px, axis=1)
    out[..., 2] = np.roll(img[..., 2], -px, axis=1)
    return out


THERMAL = np.array([
    [0.00, 0.00, 0.00, 0.00],
    [0.10, 0.06, 0.01, 0.16],
    [0.25, 0.30, 0.02, 0.42],
    [0.42, 0.75, 0.05, 0.50],
    [0.58, 1.00, 0.18, 0.40],
    [0.72, 1.00, 0.45, 0.12],
    [0.86, 1.00, 0.80, 0.30],
    [1.00, 1.00, 1.00, 0.92],
], np.float32)


def thermal_map(x):
    """Map intensity (0..1+) to false-colour thermal palette."""
    x = np.clip(x, 0, 1)
    xs = THERMAL[:, 0]
    out = np.empty(x.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(x, xs, THERMAL[:, c + 1])
    return out
