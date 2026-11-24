"""Shared helpers: canvas, easing, colour, glow, grain, text sprites."""
import os, math, functools
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SCRATCH = os.environ.get(
    "SKY_SCRATCH",
    "/tmp/claude-0/-home-user-cvxpy/f0c8e50d-dc80-5fad-820f-299cfe1179c7/scratchpad")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- layout
# WeChat Channels overlays: keep the top ~200px and the bottom ~460px clear.
SAFE_TOP = 210
SUB_Y = 1395          # centre line of the subtitle block
SAFE_BOTTOM = 1460

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def remap(t, t0, t1):
    """0..1 progress of t inside [t0, t1] (clamped)."""
    if t1 == t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))

def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)

def smoother(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)

def ease_out(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p

def ease_in(x, p=3):
    x = clamp(x)
    return x ** p

def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def pulse(t, t0, rise, hold, fall):
    """trapezoid envelope: 0 -> 1 over rise, hold, 1 -> 0 over fall."""
    if t < t0 or t > t0 + rise + hold + fall:
        return 0.0
    if t < t0 + rise:
        return smooth((t - t0) / max(rise, 1e-6))
    if t < t0 + rise + hold:
        return 1.0
    return 1 - smooth((t - t0 - rise - hold) / max(fall, 1e-6))

def fade_window(t, t0, t1, fin=0.4, fout=0.4):
    if t < t0 or t > t1:
        return 0.0
    a = smooth((t - t0) / fin) if fin > 0 else 1.0
    b = smooth((t1 - t) / fout) if fout > 0 else 1.0
    return min(a, b)

# ---------------------------------------------------------------- colour
def hexc(h, scale=1.0):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32) * scale

PAL = {
    'bg': hexc('05070c'),
    'us': hexc('7fb6ff'),        # cold blue (US)
    'us_hi': hexc('cfe4ff'),
    'su': hexc('ffb25a'),        # amber (Soviet)
    'su_hi': hexc('ffe0b0'),
    'white': hexc('f2f4f7'),
    'grey': hexc('9aa3ad'),
    'dim': hexc('5c6670'),
    'red': hexc('ff4a3d'),
    'mag': hexc('ff4fd8'),       # 80s magenta (hypothetical)
    'cyan': hexc('46f0ff'),
    'paper': hexc('e9e4d8'),
}

def new_canvas(color=None):
    c = np.empty((H, W, 3), np.float32)
    c[:] = PAL['bg'] if color is None else color
    return c

def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

def tonemap(img, knee=0.82):
    """soft shoulder so additive glows don't hard-clip."""
    x = np.maximum(img - knee, 0)
    return np.minimum(img, knee) + (1 - knee) * (1 - np.exp(-x / (1 - knee)))

# ---------------------------------------------------------------- glow
def blur(img, sigma):
    if sigma <= 0:
        return img
    k = int(sigma * 3) * 2 + 1
    return cv2.GaussianBlur(img, (k, k), sigma, borderType=cv2.BORDER_CONSTANT)

def bloom(layer, strength=1.0, radii=(4, 12, 32, 80), weights=(0.9, 0.6, 0.45, 0.35)):
    """multi-scale gaussian glow computed on downsampled copies (fast)."""
    h, w = layer.shape[:2]
    acc = np.zeros_like(layer)
    for r, wt in zip(radii, weights):
        f = max(1, int(r // 4))
        small = cv2.resize(layer, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
        small = blur(small, r / f)
        acc += cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR) * wt
    return acc * strength

_VIG = {}
def vignette(img, strength=0.5):
    key = (img.shape[0], img.shape[1], strength)
    if key not in _VIG:
        h, w = img.shape[:2]
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (x - w / 2) / (w / 2)
        ny = (y - h / 2) / (h / 2)
        r = np.sqrt((nx * nx + ny * ny) / 2)
        t = np.clip((r - 0.35) / 0.7, 0, 1)
        t = t * t * (3 - 2 * t)
        _VIG[key] = (1 - strength * t)[..., None].astype(np.float32)
    return img * _VIG[key]

_GRAIN = None
def grain(img, frame_idx, amount=0.018):
    """filmic grain generated at half resolution (cheaper to encode)."""
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7)
        _GRAIN = []
        for _ in range(12):
            g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
            _GRAIN.append(g[..., None])
    g = _GRAIN[frame_idx % len(_GRAIN)]
    lum = img.mean(axis=2, keepdims=True)
    # grain mostly in the mid-tones, very little in pure black
    wgt = np.clip(lum * 3.0, 0, 1) * (1 - np.clip(lum - 0.7, 0, 1))
    return img + g * amount * (0.35 + 0.65 * wgt)

def chroma_shift(img, px=2):
    if px <= 0:
        return img
    out = img.copy()
    out[:, px:, 0] = img[:, :-px, 0]
    out[:, :-px, 2] = img[:, px:, 2]
    return out

# grades --------------------------------------------------------
def grade_reality(img):
    """cold blue / grey-white."""
    lum = img @ np.array([0.3, 0.55, 0.15], np.float32)
    out = img * 0.82 + lum[..., None] * 0.18
    out = out * np.array([0.94, 0.99, 1.06], np.float32)
    return out

def grade_hypo(img, amt=1.0):
    """80s concept-art look: magenta shadows, teal-cyan mids, warm highlights."""
    lum = (img @ np.array([0.3, 0.55, 0.15], np.float32))[..., None]
    shadows = np.array([0.10, 0.015, 0.11], np.float32)       # violet-magenta lift
    mids = np.array([0.80, 1.02, 1.08], np.float32)
    highs = np.array([1.10, 0.98, 0.92], np.float32)
    s = np.clip(1 - lum * 4, 0, 1)
    hgt = np.clip((lum - 0.45) * 2.2, 0, 1)
    out = img * (mids * (1 - hgt) + highs * hgt) + shadows * s * 0.55
    return img * (1 - amt) + out * amt

# ---------------------------------------------------------------- fonts / text
FONT_DIR = '/usr/share/fonts/opentype/noto'
FONTS = {
    'black': (f'{FONT_DIR}/NotoSansCJK-Black.ttc', 2),
    'bold': (f'{FONT_DIR}/NotoSansCJK-Bold.ttc', 2),
    'medium': (f'{FONT_DIR}/NotoSansCJK-Medium.ttc', 2),
    'regular': (f'{FONT_DIR}/NotoSansCJK-Regular.ttc', 2),
    'light': (f'{FONT_DIR}/NotoSansCJK-Light.ttc', 2),
    'mono': (f'{FONT_DIR}/NotoSansCJK-Bold.ttc', 7),
    'type': ('/usr/share/fonts/opentype/courier-prime/Courier Prime.otf', 0),
    'typeb': ('/usr/share/fonts/opentype/courier-prime/Courier Prime Bold.otf', 0),
}

@functools.lru_cache(maxsize=256)
def font(kind, size):
    path, idx = FONTS[kind]
    return ImageFont.truetype(path, int(size), index=idx)

@functools.lru_cache(maxsize=2048)
def text_sprite(text, kind='bold', size=48, color=(1, 1, 1), tracking=0, shadow=0.0,
                stroke=0, stroke_color=(0, 0, 0), line_gap=1.35, align='center'):
    """RGBA float32 sprite (premultiplied off; alpha separate)."""
    f = font(kind, size)
    lines = text.split('\n')
    def line_w(s):
        if tracking == 0:
            return f.getlength(s)
        return sum(f.getlength(ch) for ch in s) + tracking * max(0, len(s) - 1)
    widths = [line_w(s) for s in lines]
    asc, desc = f.getmetrics()
    lh = int(size * line_gap)
    pad = int(size * 0.35) + stroke + 4
    w = int(max(widths) + pad * 2)
    h = int(lh * (len(lines) - 1) + asc + desc + pad * 2)
    img = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(img)
    for i, s in enumerate(lines):
        if align == 'center':
            x = pad + (max(widths) - widths[i]) / 2
        elif align == 'right':
            x = pad + (max(widths) - widths[i])
        else:
            x = pad
        y = pad + i * lh
        if tracking == 0:
            d.text((x, y), s, font=f, fill=255, stroke_width=0)
        else:
            for ch in s:
                d.text((x, y), ch, font=f, fill=255)
                x += f.getlength(ch) + tracking
    a = np.asarray(img, np.float32) / 255.0
    rgb = np.empty((h, w, 3), np.float32)
    rgb[:] = color
    if stroke > 0:
        k = stroke * 2 + 1
        sa = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        sa = blur(sa, stroke * 0.5)
        rgb = rgb * a[..., None] + np.array(stroke_color, np.float32) * (1 - a[..., None])
        a = np.maximum(a, sa * 0.9)
    if shadow > 0:
        sh = blur(a, size * 0.12) * shadow
        rgb = rgb * a[..., None] / np.maximum(np.maximum(a, sh)[..., None], 1e-6)
        a = np.maximum(a, sh)
    return rgb, a

def blit(canvas, sprite, x, y, alpha=1.0, anchor='center', add=False, scale=1.0):
    """composite an (rgb, a) sprite. anchor: center | lt | lc | rc | ct | cb."""
    if alpha <= 0.002:
        return
    rgb, a = sprite
    if scale != 1.0:
        nh, nw = max(1, int(rgb.shape[0] * scale)), max(1, int(rgb.shape[1] * scale))
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        rgb = cv2.resize(rgb, (nw, nh), interpolation=interp)
        a = cv2.resize(a, (nw, nh), interpolation=interp)
    h, w = a.shape
    if anchor == 'center':
        x0, y0 = x - w / 2, y - h / 2
    elif anchor == 'lt':
        x0, y0 = x, y
    elif anchor == 'lc':
        x0, y0 = x, y - h / 2
    elif anchor == 'rc':
        x0, y0 = x - w, y - h / 2
    elif anchor == 'ct':
        x0, y0 = x - w / 2, y
    elif anchor == 'cb':
        x0, y0 = x - w / 2, y - h
    else:
        raise ValueError(anchor)
    x0, y0 = int(round(x0)), int(round(y0))
    H_, W_ = canvas.shape[:2]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W_, x0 + w), min(H_, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    sub_a = a[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0][..., None] * alpha
    sub_rgb = rgb[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
    region = canvas[dy0:dy1, dx0:dx1]
    if add:
        region += sub_rgb * sub_a
    else:
        region *= (1 - sub_a)
        region += sub_rgb * sub_a

def text(canvas, s, x, y, kind='bold', size=48, color=(1, 1, 1), alpha=1.0, anchor='center',
         tracking=0, shadow=0.0, stroke=0, line_gap=1.35, align='center', add=False, scale=1.0):
    color = tuple(float(c) for c in color)
    spr = text_sprite(s, kind, int(size), color, tracking, shadow, stroke, (0.0, 0.0, 0.0), line_gap, align)
    blit(canvas, spr, x, y, alpha, anchor, add=add, scale=scale)
    return spr[1].shape[1], spr[1].shape[0]

# ---------------------------------------------------------------- primitive drawing (float canvas)
def _bbox(pts, pad, shape):
    pts = np.asarray(pts, np.float32).reshape(-1, 2)
    x0 = int(np.floor(pts[:, 0].min() - pad)); x1 = int(np.ceil(pts[:, 0].max() + pad)) + 1
    y0 = int(np.floor(pts[:, 1].min() - pad)); y1 = int(np.ceil(pts[:, 1].max() + pad)) + 1
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, shape[1]), min(y1, shape[0])
    return x0, y0, x1, y1

def _apply(layer, box, a, color, add):
    x0, y0, x1, y1 = box
    reg = layer[y0:y1, x0:x1]
    col = np.asarray(color, np.float32)
    if a.ndim == 2:
        a = a[..., None]
    if add:
        reg += col * a
    else:
        reg *= (1 - a)
        reg += col * a

def draw_line(layer, p0, p1, color, width=2, alpha=1.0, add=False):
    draw_polyline(layer, [p0, p1], color, width, alpha, add=add)

def draw_polyline(layer, pts, color, width=2, alpha=1.0, closed=False, add=False):
    pts = np.asarray(pts, np.float32)
    if len(pts) < 2 or alpha <= 0:
        return
    box = _bbox(pts, width * 2 + 3, layer.shape)
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.polylines(m, [np.round((pts - [x0, y0]) * 16).astype(np.int32)], closed, 255,
                  max(1, int(round(width))), cv2.LINE_AA, shift=4)
    _apply(layer, box, m.astype(np.float32) / 255.0 * alpha, color, add)

def draw_graded(layer, segs, color, add=True):
    """many segments with individual intensity/width into one local mask.
    segs: list of (p0, p1, intensity 0..1, width)."""
    if not segs:
        return
    allp = np.array([[s[0], s[1]] for s in segs], np.float32).reshape(-1, 2)
    wmax = max(s[3] for s in segs)
    box = _bbox(allp, wmax * 2 + 3, layer.shape)
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return
    m = np.zeros((y1 - y0, x1 - x0), np.float32)
    for p0, p1, inten, wd in segs:
        q0 = (int(round((p0[0] - x0) * 16)), int(round((p0[1] - y0) * 16)))
        q1 = (int(round((p1[0] - x0) * 16)), int(round((p1[1] - y0) * 16)))
        tmp = np.zeros_like(m, dtype=np.uint8) if False else None
        cv2.line(m, q0, q1, float(inten), max(1, int(round(wd))), cv2.LINE_8, shift=4)
    m = cv2.GaussianBlur(m, (3, 3), 0.6)
    _apply(layer, box, m, color, add)

def mask_poly(shape, pts_list, ss=1):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.round(np.asarray(p) * 16).astype(np.int32) for p in pts_list], 255, cv2.LINE_AA, shift=4)
    return m.astype(np.float32) / 255.0

def fill_poly(layer, pts, color, alpha=1.0, add=False):
    pts = np.asarray(pts, np.float32)
    box = _bbox(pts, 3, layer.shape)
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.round((pts - [x0, y0]) * 16).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    _apply(layer, box, m.astype(np.float32) / 255.0 * alpha, color, add)

def ring(layer, x, y, r, color, width=2, alpha=1.0, add=True):
    box = _bbox([[x - r, y - r], [x + r, y + r]], width + 3, layer.shape)
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.circle(m, (int((x - x0) * 16), int((y - y0) * 16)), int(r * 16), 255, max(1, int(width)), cv2.LINE_AA, shift=4)
    _apply(layer, box, m.astype(np.float32) / 255.0 * alpha, color, add)

def splat(layer, x, y, radius, color, intensity=1.0):
    """additive gaussian dot."""
    r = max(radius, 0.6)
    R = int(r * 3.5) + 2
    xi, yi = int(x), int(y)
    Hh, Ww = layer.shape[:2]
    xa, xb, ya, yb = max(0, xi - R), min(Ww, xi + R + 1), max(0, yi - R), min(Hh, yi + R + 1)
    if xb <= xa or yb <= ya:
        return
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)) * intensity
    layer[ya:yb, xa:xb] += g[..., None] * np.asarray(color, np.float32)

def rect(layer, x0, y0, x1, y1, color, alpha=1.0):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(layer.shape[1], x1), min(layer.shape[0], y1)
    if x1 <= x0 or y1 <= y0:
        return
    reg = layer[y0:y1, x0:x1]
    reg *= (1 - alpha)
    reg += np.asarray(color, np.float32) * alpha

def frame_rect(layer, x0, y0, x1, y1, color, width=2, alpha=1.0):
    draw_polyline(layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], color, width, alpha, closed=True)
