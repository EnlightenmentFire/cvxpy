# -*- coding: utf-8 -*-
"""Scene painters. Each scene: object with render(t, lt) -> float32 HxWx3 image (0..1).
t = seconds since scene start; lt = list of line start times (scene-relative); dur = scene duration."""
import functools
import numpy as np, cv2
from engine import (W, H, FPS, SERIF_SC, SERIF_TC, SANS_SC, BRUSH, INK, PAPER, CINNABAR, GOLD, MIST,
                    text_sprite, vtext_sprite, blit, rgb, clamp, ease, ease_out, paper_texture, vignette_mask, scale_sprite)
from rain import RainWindow

WHITE = (244, 240, 232)
DIM = (150, 150, 150)
INKG = (92, 86, 80)
TEAL = (56, 96, 104)


def fade(t, t0, d=0.6):
    return ease((t - t0) / d)


def T(img, s, x, y, size=54, color=INK, path=SERIF_SC, alpha=1.0, anchor="center", weight=None, maxw=900,
      align="center", spacing=1.35, shadow=0, tracking=0):
    if alpha <= 0.002:
        return
    spr = text_sprite(s, path, size, tuple(color), weight, maxw, align, spacing, shadow, 0, (0, 0, 0), True, tracking)
    blit(img, spr, x, y, alpha, anchor)


def chip(img, s, x, y, alpha=1.0, color=CINNABAR, size=34, fill=False):
    """Bordered (or filled) tag such as 实证·较强."""
    if alpha <= 0.002:
        return
    tc = (250, 244, 232) if fill else tuple(color)
    spr = text_sprite(s, SANS_SC, size, tc, 500, 1000, "center", 1.2, 0)
    h, w = spr.shape[:2]
    bw, bh = w + 30, int(size * 1.55)
    x0, y0 = int(x - bw / 2), int(y - bh / 2)
    ov = img[y0:y0 + bh, x0:x0 + bw].copy()
    if fill:
        cv2.rectangle(ov, (0, 0), (bw - 1, bh - 1), rgb(color).tolist(), -1)
    else:
        cv2.rectangle(ov, (1, 1), (bw - 2, bh - 2), rgb(color).tolist(), 3, cv2.LINE_AA)
    img[y0:y0 + bh, x0:x0 + bw] = img[y0:y0 + bh, x0:x0 + bw] * (1 - alpha) + ov * alpha
    blit(img, spr, x, y + 1, alpha)


# ------------------------------------------------------------------ backgrounds
@functools.lru_cache(maxsize=2)
def ink_night(seed=11):
    """Deep ink background with faint mist bands and distant mountains (for the scroll scenes)."""
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    base = rgb((14, 16, 20)) * (1 - yy[..., None] * 0.35) + rgb((22, 28, 34)) * (yy[..., None] * 0.35)
    img = np.broadcast_to(base, (H, W, 3)).copy()
    xs = np.arange(W, dtype=np.float32)
    for k, (y0, amp, c) in enumerate([(1180, 120, (26, 32, 38)), (1300, 90, (20, 24, 28)), (1420, 70, (15, 17, 20))]):
        ph = rng.uniform(0, 6, 4)
        ridge = y0 - amp * (0.5 * np.sin(xs / 260 + ph[0]) + 0.3 * np.sin(xs / 113 + ph[1]) + 0.2 * np.sin(xs / 47 + ph[2]))
        mask = (np.arange(H)[:, None] > ridge[None, :]).astype(np.float32)
        mask = cv2.GaussianBlur(mask, (0, 0), 3 + k * 2)
        img = img * (1 - mask[..., None]) + rgb(c) * mask[..., None]
    mist = cv2.GaussianBlur(rng.normal(0, 1, (H // 16, W // 16)).astype(np.float32), (0, 0), 3)
    mist = cv2.resize(mist, (W, H), interpolation=cv2.INTER_CUBIC)
    img += (mist * 0.012)[..., None]
    return np.clip(img, 0, 1).astype(np.float32)


SC_X0, SC_X1, SC_Y0, SC_Y1 = 70, 1010, 150, 1430   # scroll paper area


@functools.lru_cache(maxsize=2)
def scroll_paper():
    p = paper_texture(SC_X1 - SC_X0, SC_Y1 - SC_Y0, seed=5)
    return p


def draw_scroll(img, t, open_t=0.0, dur=0.9):
    """Hanging scroll unrolling downward; returns visible bottom y."""
    k = ease_out((t - open_t) / dur)
    y1 = int(SC_Y0 + (SC_Y1 - SC_Y0) * k)
    # silk mounting border
    bx0, bx1 = SC_X0 - 26, SC_X1 + 26
    cv2.rectangle(img, (bx0, SC_Y0 - 50), (bx1, y1 + 30), rgb((52, 62, 64)).tolist(), -1)
    cv2.rectangle(img, (bx0 + 8, SC_Y0 - 42), (bx1 - 8, y1 + 22), rgb((72, 84, 84)).tolist(), 2, cv2.LINE_AA)
    if y1 > SC_Y0:
        img[SC_Y0:y1, SC_X0:SC_X1] = scroll_paper()[:y1 - SC_Y0]
    # rods
    for yr in (SC_Y0 - 58, y1 + 30):
        cv2.rectangle(img, (bx0 - 34, yr), (bx1 + 34, yr + 18), rgb((40, 26, 18)).tolist(), -1, cv2.LINE_AA)
        cv2.line(img, (bx0 - 34, yr + 3), (bx1 + 34, yr + 3), rgb((96, 66, 42)).tolist(), 2, cv2.LINE_AA)
        for xe in (bx0 - 44, bx1 + 34):
            cv2.rectangle(img, (xe, yr - 4), (xe + 10, yr + 22), rgb((150, 118, 64)).tolist(), -1)
    return y1


class Base:
    def __init__(self, dur, lt):
        self.dur, self.lt = dur, lt

    def L(self, i):
        """start time of line i (clamped)."""
        return self.lt[min(i, len(self.lt) - 1)]


class ScrollScene(Base):
    """Ink night + hanging scroll; subclasses draw content in `content(img, t)` (paper coordinates are absolute)."""
    label = ""

    def render(self, t):
        img = ink_night().copy()
        y1 = draw_scroll(img, t)
        if self.label:
            T(img, self.label, W / 2, 78, 34, GOLD, SERIF_SC, alpha=fade(t, 0.2), weight=500, tracking=6)
        if y1 > SC_Y0 + 40:
            sub = img[SC_Y0:y1]
            canvas = img.copy()
            self.content(canvas, t)
            img[SC_Y0:y1] = canvas[SC_Y0:y1]
            img[:SC_Y0] = canvas[:SC_Y0] if getattr(self, "draws_outside", False) else img[:SC_Y0]
        return img

    def content(self, img, t):
        pass


# ------------------------------------------------------------------ brush strokes
def brush_path(pts, w0, w1, seed=0, n=260):
    """Sample a polyline into stamps (x, y, radius) with taper and slight noise."""
    pts = np.array(pts, np.float32)
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], n)
    x = np.interp(u, s, pts[:, 0]); y = np.interp(u, s, pts[:, 1])
    rng = np.random.default_rng(seed)
    f = u / s[-1]
    r = (w0 + (w1 - w0) * f) * (0.85 + 0.15 * np.sin(f * 9 + seed)) * (1 + rng.normal(0, 0.04, n))
    r *= np.clip(f / 0.04, 0.3, 1)
    return np.stack([x, y, r], 1)


def draw_stamps(alpha_img, stamps, p, dry=0.0, seed=0):
    k = int(len(stamps) * clamp(p))
    rng = np.random.default_rng(seed)
    for i in range(k):
        x, y, r = stamps[i]
        cv2.circle(alpha_img, (int(x * 4), int(y * 4)), max(1, int(r * 4)), 1.0, -1, cv2.LINE_AA, 2)
    return k


def ink_layer(shape_wh, strokes, t, seed=0):
    """strokes: list of (stamps, t0, t1). Draw at 1/2 res then upsample; returns alpha HxW."""
    w, h = shape_wh
    a = np.zeros((h // 2, w // 2), np.float32)
    for (st, t0, t1) in strokes:
        p = clamp((t - t0) / max(1e-3, t1 - t0))
        k = int(len(st) * p)
        for x, y, r in st[:k]:
            cv2.circle(a, (int(x * 8), int(y * 8)), max(4, int(r * 8)), 1.0, -1, cv2.LINE_AA, 4)
    a = cv2.resize(a, (w, h), interpolation=cv2.INTER_LINEAR)
    # dry-brush texture
    rng = np.random.default_rng(seed)
    tex = cv2.resize(rng.random((h // 3, w // 3)).astype(np.float32), (w, h))
    a = a * (0.82 + 0.18 * tex)
    return a


def arrow_strokes(x0, y0, x1, y1, w=9, head=46, seed=0):
    ang = np.arctan2(y1 - y0, x1 - x0)
    shaft = brush_path([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + 6), (x1, y1)], w * 0.7, w, seed)
    hl = [(x1, y1), (x1 - head * np.cos(ang - 0.42), y1 - head * np.sin(ang - 0.42))]
    hr = [(x1, y1), (x1 - head * np.cos(ang + 0.42), y1 - head * np.sin(ang + 0.42))]
    fl = [(x0 + 30 * np.cos(ang), y0 + 30 * np.sin(ang)), (x0 - 10 * np.cos(ang - 0.5), y0 - 10 * np.sin(ang - 0.5) - 26)]
    fr = [(x0 + 30 * np.cos(ang), y0 + 30 * np.sin(ang)), (x0 - 10 * np.cos(ang + 0.5), y0 - 10 * np.sin(ang + 0.5) + 26)]
    return [shaft, brush_path(hl, w * 1.1, w * 0.4, seed + 1, 60), brush_path(hr, w * 1.1, w * 0.4, seed + 2, 60),
            brush_path(fl, w * 0.6, w * 0.3, seed + 3, 40), brush_path(fr, w * 0.6, w * 0.3, seed + 4, 40)]


def seal(img, s, x, y, size=40, alpha=1.0, color=CINNABAR):
    """Square red seal with white characters (2x2 or 1 column)."""
    if alpha <= 0.002:
        return
    n = len(s)
    cols = 2 if n == 4 else 1
    rows = (n + cols - 1) // cols
    bw, bh = cols * size + 24, rows * size + 24
    box = np.zeros((bh, bw, 4), np.float32)
    box[..., :3] = rgb(color); box[..., 3] = 0.94
    rng = np.random.default_rng(len(s))
    box[..., 3] *= (0.85 + 0.15 * rng.random((bh, bw)))
    order = [s[i] for i in range(n)]
    for i, ch in enumerate(order):
        c = cols - 1 - i // rows; r = i % rows
        spr = text_sprite(ch, SERIF_TC, size, (250, 240, 228), 700, 400, "center", 1.0, 0)
        hh, ww = spr.shape[:2]
        cx, cy = 12 + c * size + size / 2, 12 + r * size + size / 2
        x0, y0 = int(cx - ww / 2), int(cy - hh / 2 + size * 0.12)
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(bw, x0 + ww), min(bh, y0 + hh)
        sa = spr[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, 3]
        box[Y0:Y1, X0:X1, :3] = box[Y0:Y1, X0:X1, :3] * (1 - sa[..., None]) + rgb((250, 240, 228)) * sa[..., None]
    blit(img, box, x, y, alpha, "center")
