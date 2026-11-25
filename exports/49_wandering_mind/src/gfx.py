# -*- coding: utf-8 -*-
"""Small raster toolkit: cropped RGBA layers (premultiplied float32), supersampled drawing, text, blur, compositing."""
import os, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 25
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/work/fonts")

# palette (RGB 0..1)
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

BG_TOP = hexc("#0d1216")
BG_BOT = hexc("#1a2228")
PAPER = hexc("#ede5d3")
PAPER_D = hexc("#d9cdb4")
INK = hexc("#1c1b19")
INK_S = hexc("#4a4741")
MIST = hexc("#c9d2d6")
GOLD = hexc("#d4ae6a")
GOLD_D = hexc("#a8823f")
CINNABAR = hexc("#b8432f")
TEAL = hexc("#5f9e95")
INDIGO = hexc("#7d8fc4")
WHITE = hexc("#f4f1ea")
GREY = hexc("#9aa3a8")

# ----------------------------------------------------------------------------- fonts
FONTS = {
    "serif": ("NotoSerifSC.ttf", None),
    "sans": ("NotoSansSC.ttf", None),
    "kai": ("LXGWWenKai.ttf", None),
    "kaim": ("LXGWWenKaiMedium.ttf", None),
    "brush": ("MaShanZheng.ttf", None),
}


@functools.lru_cache(maxsize=256)
def font(name, size, weight=None):
    f = ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name][0]), int(size))
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


# ----------------------------------------------------------------------------- layers
class Layer:
    """Premultiplied RGB + alpha, cropped at (x, y)."""
    __slots__ = ("x", "y", "rgb", "a")

    def __init__(self, x, y, rgb, a):
        self.x, self.y, self.rgb, self.a = int(x), int(y), rgb, a

    @property
    def w(self):
        return self.a.shape[1]

    @property
    def h(self):
        return self.a.shape[0]


def layer_from_pil(img, x=0, y=0, trim=True):
    arr = np.asarray(img.convert("RGBA"), dtype=np.float32) / 255.0
    a = arr[..., 3]
    if trim:
        ys, xs = np.nonzero(a > 1 / 512)
        if len(ys) == 0:
            return None
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        arr = arr[y0:y1, x0:x1]
        a = a[y0:y1, x0:x1]
        x, y = x + x0, y + y0
    rgb = arr[..., :3] * a[..., None]
    return Layer(x, y, np.ascontiguousarray(rgb), np.ascontiguousarray(a))


def comp(frame, L, opacity=1.0, dx=0, dy=0):
    """Composite layer onto frame (H,W,3 float32) in place."""
    if L is None or opacity <= 0.003:
        return
    x, y = L.x + int(round(dx)), L.y + int(round(dy))
    fx0, fy0 = max(x, 0), max(y, 0)
    fx1, fy1 = min(x + L.w, W), min(y + L.h, H)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    lx0, ly0 = fx0 - x, fy0 - y
    lx1, ly1 = lx0 + (fx1 - fx0), ly0 + (fy1 - fy0)
    a = L.a[ly0:ly1, lx0:lx1]
    rgb = L.rgb[ly0:ly1, lx0:lx1]
    dst = frame[fy0:fy1, fx0:fx1]
    if opacity >= 0.999:
        dst *= (1 - a)[..., None]
        dst += rgb
    else:
        dst *= (1 - a * opacity)[..., None]
        dst += rgb * opacity


def comp_add(frame, L, opacity=1.0, dx=0, dy=0):
    """Additive (glow) composite."""
    if L is None or opacity <= 0.003:
        return
    x, y = L.x + int(dx), L.y + int(dy)
    fx0, fy0 = max(x, 0), max(y, 0)
    fx1, fy1 = min(x + L.w, W), min(y + L.h, H)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    lx0, ly0 = fx0 - x, fy0 - y
    frame[fy0:fy1, fx0:fx1] += L.rgb[ly0:ly0 + fy1 - fy0, lx0:lx0 + fx1 - fx0] * opacity


def scaled(L, s, cx=None, cy=None):
    """Return a scaled copy of a layer around (cx, cy) (defaults to its centre)."""
    if abs(s - 1) < 1e-3:
        return L
    cx = L.x + L.w / 2 if cx is None else cx
    cy = L.y + L.h / 2 if cy is None else cy
    nw, nh = max(1, int(L.w * s)), max(1, int(L.h * s))
    rgb = cv2.resize(L.rgb, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    a = cv2.resize(L.a, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
    nx = cx + (L.x - cx) * s
    ny = cy + (L.y - cy) * s
    return Layer(nx, ny, rgb, a)


def blur_layer(L, sigma, pad=None):
    pad = int(sigma * 3) if pad is None else pad
    rgb = cv2.copyMakeBorder(L.rgb, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    a = cv2.copyMakeBorder(L.a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    rgb = cv2.GaussianBlur(rgb, (0, 0), sigma)
    a = cv2.GaussianBlur(a, (0, 0), sigma)
    return Layer(L.x - pad, L.y - pad, rgb, a)


# ----------------------------------------------------------------------------- supersampled canvas
class Canvas:
    """Draw at SS x resolution on a region; .layer() downsamples to a Layer."""

    def __init__(self, x, y, w, h, ss=2):
        self.x, self.y, self.w, self.h, self.ss = x, y, w, h, ss
        self.img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def P(self, px, py):
        return ((px - self.x) * self.ss, (py - self.y) * self.ss)

    def pts(self, ps):
        return [self.P(*p) for p in ps]

    @staticmethod
    def col(c, a=1.0):
        return tuple(int(v * 255) for v in c[:3]) + (int(a * 255),)

    def line(self, ps, c, width, a=1.0, joint="curve"):
        self.d.line(self.pts(ps), fill=self.col(c, a), width=max(1, int(width * self.ss)), joint=joint)
        r = width * self.ss / 2
        for p in (ps[0], ps[-1]):
            q = self.P(*p)
            self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=self.col(c, a))

    def poly(self, ps, c, a=1.0, outline=None, width=1):
        self.d.polygon(self.pts(ps), fill=self.col(c, a) if c is not None else None,
                       outline=self.col(outline, a) if outline else None, width=int(width * self.ss))

    def circle(self, cx, cy, r, c=None, a=1.0, outline=None, width=1):
        p = self.P(cx, cy)
        R = r * self.ss
        self.d.ellipse([p[0] - R, p[1] - R, p[0] + R, p[1] + R], fill=self.col(c, a) if c is not None else None,
                       outline=self.col(outline, a) if outline is not None else None, width=max(1, int(width * self.ss)))

    def ellipse(self, cx, cy, rx, ry, c=None, a=1.0, outline=None, width=1):
        p = self.P(cx, cy)
        self.d.ellipse([p[0] - rx * self.ss, p[1] - ry * self.ss, p[0] + rx * self.ss, p[1] + ry * self.ss],
                       fill=self.col(c, a) if c is not None else None,
                       outline=self.col(outline, a) if outline is not None else None, width=max(1, int(width * self.ss)))

    def rrect(self, x0, y0, x1, y1, r, c=None, a=1.0, outline=None, width=1):
        p0, p1 = self.P(x0, y0), self.P(x1, y1)
        self.d.rounded_rectangle([p0, p1], radius=r * self.ss, fill=self.col(c, a) if c is not None else None,
                                 outline=self.col(outline, a) if outline is not None else None,
                                 width=max(1, int(width * self.ss)))

    def text(self, x, y, s, fnt, c, a=1.0, anchor="mm", spacing=0):
        f = font(fnt[0], fnt[1] * self.ss, fnt[2] if len(fnt) > 2 else None)
        self.d.text(self.P(x, y), s, font=f, fill=self.col(c, a), anchor=anchor)

    def layer(self):
        img = self.img.resize((self.w, self.h), Image.LANCZOS) if self.ss != 1 else self.img
        return layer_from_pil(img, self.x, self.y)


def full_canvas(ss=2):
    return Canvas(0, 0, W, H, ss)


# ----------------------------------------------------------------------------- text
def text_layer(s, fnt, c, x, y, anchor="mm", a=1.0, shadow=None, glow=None, track=0):
    """Render text (single or multi-line with \n) to a Layer positioned with anchor at (x, y)."""
    f = font(*fnt)
    lines = s.split("\n")
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.25)
    widths = [int(f.getlength(l)) + track * max(0, len(l) - 1) for l in lines]
    tw, th = max(widths) + 40, lh * len(lines) + 40
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = tuple(int(v * 255) for v in c[:3]) + (int(a * 255),)
    for i, l in enumerate(lines):
        lx = 20 + (max(widths) - widths[i]) / 2 if anchor[0] == "m" else (20 if anchor[0] == "l" else 20 + max(widths) - widths[i])
        ly = 20 + i * lh
        if track:
            for ch in l:
                d.text((lx, ly), ch, font=f, fill=col)
                lx += f.getlength(ch) + track
        else:
            d.text((lx, ly), l, font=f, fill=col)
    ox = {"l": 20, "m": 20 + max(widths) / 2, "r": 20 + max(widths)}[anchor[0]]
    oy = {"t": 20, "m": 20 + lh * len(lines) / 2 - (lh - (asc + desc)) / 2, "b": th - 20}[anchor[1]]
    L = layer_from_pil(img, x - ox, y - oy, trim=False)
    if shadow or glow:
        out = []
        if shadow:
            sc, ss_, sa = shadow
            S = blur_layer(L, ss_)
            S.rgb = S.a[..., None] * np.array(sc, np.float32) * sa
            S.a = S.a * sa
            out.append(S)
        if glow:
            gc, gs, ga = glow
            G = blur_layer(L, gs)
            G.rgb = G.a[..., None] * np.array(gc, np.float32) * ga
            G.a = G.a * 0
            out.append(("add", G))
        out.append(L)
        return out
    return L


def comp_any(frame, item, opacity=1.0, dx=0, dy=0):
    if item is None:
        return
    if isinstance(item, list):
        for it in item:
            comp_any(frame, it, opacity, dx, dy)
    elif isinstance(item, tuple) and item[0] == "add":
        comp_add(frame, item[1], opacity, dx, dy)
    else:
        comp(frame, item, opacity, dx, dy)


def wrap_cjk(s, maxch):
    """Greedy wrap at punctuation when possible; returns list of lines."""
    out, cur = [], ""
    for ch in s:
        cur += ch
        if len(cur) >= maxch:
            # try to break after the last punctuation in the latter half
            k = max(cur.rfind(p) for p in "，。、：；？！」")
            if k >= maxch // 2 and k < len(cur) - 1:
                out.append(cur[:k + 1]); cur = cur[k + 1:]
            else:
                out.append(cur); cur = ""
    if cur:
        if out and len(cur) <= 2 and all(c in "，。、：；？！」』" for c in cur):
            out[-1] += cur
        else:
            out.append(cur)
    return out


# ----------------------------------------------------------------------------- easing / noise
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def fade(t, t0, d=0.6):
    return ease((t - t0) / d)


def value_noise(h, w, scale, seed=0, octaves=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sh, sw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
        g = rng.random((sh, sw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= 0.5
        scale /= 2
    return out / tot
