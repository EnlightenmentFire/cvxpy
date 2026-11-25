"""画面引擎：cv2 画图形（半分辨率发光层 + 全分辨率清晰层），PIL 渲染文字（缓存）。"""
import os, re, math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 25
FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/work/fonts")
FONTS = {
    "sans": "NotoSansSC-400.ttf", "sans5": "NotoSansSC-500.ttf", "sansb": "NotoSansSC-700.ttf", "sansh": "NotoSansSC-900.ttf",
    "serif": "NotoSerifSC-400.ttf", "serifb": "NotoSerifSC-600.ttf", "serifh": "NotoSerifSC-900.ttf",
}
# palette (RGB 0-255)
BG = (3, 6, 14)
CYAN = (94, 231, 255)
BLUE = (70, 130, 255)
VIOLET = (150, 125, 255)
AMBER = (255, 184, 92)
RED = (255, 96, 96)
GREEN = (120, 240, 170)
WHITE = (240, 244, 255)
GREY = (150, 160, 180)
DIM = (80, 90, 110)

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x
def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x):
    x = clamp(x); return x ** 3
def fade(t, t0, t1, d=0.4):
    """0→1 over [t0,t0+d], 1→0 over [t1-d,t1]"""
    return clamp((t - t0) / d) * clamp((t1 - t) / d)
def lerp(a, b, k):
    return a + (b - a) * k
def mix(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))
def scale(c, k):
    return tuple(int(clamp(float(v) * float(k), 0, 255)) for v in c)

@functools.lru_cache(maxsize=64)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name]), size)

@functools.lru_cache(maxsize=4096)
def text_rgba(s, size, fname="sans5", color=WHITE, stroke=0, stroke_color=(0, 0, 0), spacing=0):
    f = font(fname, size)
    x0, y0, x1, y1 = f.getbbox(s, stroke_width=stroke) if s else (0, 0, 1, 1)
    asc, desc = f.getmetrics()
    w = max(1, x1 - min(0, x0) + stroke * 2 + 2 + spacing * len(s))
    h = asc + desc + stroke * 2 + 4
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if spacing:
        x = stroke
        for ch in s:
            d.text((x, stroke), ch, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
            x += f.getlength(ch) + spacing
    else:
        d.text((stroke - min(0, x0), stroke), s, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
    a = np.asarray(im)
    return a

def text_size(s, size, fname="sans5", spacing=0):
    a = text_rgba(s, size, fname, WHITE, 0, (0, 0, 0), spacing)
    return a.shape[1], a.shape[0]

def blit_rgba(img, rgba, x, y, alpha=1.0):
    """alpha-composite rgba (h,w,4 uint8) onto img (uint8) at top-left x,y."""
    if alpha <= 0.003:
        return
    h, w = rgba.shape[:2]
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(img.shape[1], x + w), min(img.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    src = rgba[Y0 - y:Y1 - y, X0 - x:X1 - x]
    a = src[..., 3:4].astype(np.float32) * (alpha / 255.0)
    dst = img[Y0:Y1, X0:X1]
    dst[:] = (dst * (1 - a) + src[..., :3] * a).astype(np.uint8)

def text(img, s, x, y, size=48, fname="sans5", color=WHITE, anchor="mm", alpha=1.0, stroke=0, stroke_color=(0, 0, 0), spacing=0):
    if not s or alpha <= 0.003:
        return (0, 0)
    a = text_rgba(s, size, fname, tuple(color), stroke, tuple(stroke_color), spacing)
    h, w = a.shape[:2]
    ax = {"l": 0, "m": w // 2, "r": w}[anchor[0]]
    ay = {"t": 0, "m": h // 2, "b": h}[anchor[1]]
    blit_rgba(img, a, int(x - ax), int(y - ay), alpha)
    return (w, h)

def wrap(s, size, fname, maxw):
    """greedy wrap for CJK text; keeps closing punctuation off line starts"""
    lines, cur = [], ""
    toks = re.findall(r"[A-Za-z0-9'’\-.,;:!?“”\"()…§/&]+ ?|.", s, flags=re.S)
    for ch in toks:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if text_size(cur + ch, size, fname)[0] > maxw and cur:
            if ch in "，。、；：！？」』）》,.":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur.rstrip()); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur.rstrip())
    return lines

def paragraph(img, s, x, y, size, fname="serif", color=WHITE, maxw=900, lh=1.5, anchor="m", alpha=1.0, stroke=0, reveal=1.0):
    """multi-line text; anchor 'l' or 'm' horizontally; y is top. reveal: fraction of chars shown (typewriter-free fade by line)"""
    ls = wrap(s, size, fname, maxw)
    n = len(ls)
    for i, ln in enumerate(ls):
        k = clamp(reveal * n - i) if reveal < 1 else 1.0
        text(img, ln, x, y + i * size * lh, size, fname, color, anchor + "t", alpha * ease(k), stroke)
    return y + n * size * lh

# ---------- glow layer ----------
GW, GH = W // 2, H // 2

class Frame:
    def __init__(self, base=None):
        self.img = np.empty((H, W, 3), np.uint8)
        if base is None:
            self.img[:] = BG
        else:
            self.img[:] = base
        self.g = np.zeros((GH, GW, 3), np.float32)   # additive glow buffer, half-res, 0..1+
    def finish_glow(self, strength=1.0, sharp=0.9):
        if strength <= 0 or not self.g.any():
            return
        g = self.g
        b1 = cv2.GaussianBlur(g, (0, 0), 3)
        b2 = cv2.GaussianBlur(cv2.resize(g, (GW // 4, GH // 4), interpolation=cv2.INTER_AREA), (0, 0), 4)
        b2 = cv2.resize(b2, (GW, GH), interpolation=cv2.INTER_LINEAR)
        tot = g * sharp + b1 * 1.2 + b2 * 2.2
        up = cv2.resize(tot, (W, H), interpolation=cv2.INTER_LINEAR)
        out = self.img.astype(np.float32) + up * (255.0 * strength)
        np.clip(out, 0, 255, out=out)
        self.img[:] = out.astype(np.uint8)
        self.g[:] = 0

def gcol(c, k=1.0):
    k = float(k); return (float(c[0]) / 255.0 * k, float(c[1]) / 255.0 * k, float(c[2]) / 255.0 * k)

def gline(fr, p, q, c, k=1.0, th=1):
    cv2.line(fr.g, (int(p[0] / 2), int(p[1] / 2)), (int(q[0] / 2), int(q[1] / 2)), gcol(c, k), th, cv2.LINE_AA)
def gdot(fr, p, r, c, k=1.0):
    cv2.circle(fr.g, (int(p[0] / 2), int(p[1] / 2)), max(1, int(r / 2)), gcol(c, k), -1, cv2.LINE_AA)
def gring(fr, p, r, c, k=1.0, th=1):
    cv2.circle(fr.g, (int(p[0] / 2), int(p[1] / 2)), max(1, int(r / 2)), gcol(c, k), th, cv2.LINE_AA)

def line(img, p, q, c, th=2):
    cv2.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), c, th, cv2.LINE_AA)
def circle(img, p, r, c, th=-1):
    cv2.circle(img, (int(p[0]), int(p[1])), max(1, int(r)), c, th, cv2.LINE_AA)
def rect_alpha(img, x0, y0, x1, y1, c, a):
    x0, y0, x1, y1 = [int(v) for v in (max(0, x0), max(0, y0), min(W, x1), min(H, y1))]
    if x1 <= x0 or y1 <= y0 or a <= 0:
        return
    sub = img[y0:y1, x0:x1].astype(np.float32)
    sub = sub * (1 - a) + np.array(c, np.float32) * a
    img[y0:y1, x0:x1] = sub.astype(np.uint8)
def rounded(img, x0, y0, x1, y1, r, c, th=2):
    x0, y0, x1, y1, r = int(x0), int(y0), int(x1), int(y1), int(r)
    for (cx, cy, a0) in ((x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90)):
        cv2.ellipse(img, (cx, cy), (r, r), a0, 0, 90, c, th, cv2.LINE_AA)
    line(img, (x0 + r, y0), (x1 - r, y0), c, th); line(img, (x0 + r, y1), (x1 - r, y1), c, th)
    line(img, (x0, y0 + r), (x0, y1 - r), c, th); line(img, (x1, y0 + r), (x1, y1 - r), c, th)

# ---------- static backgrounds ----------
def _vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2)
    return np.clip(1.05 - 0.55 * d ** 2, 0.25, 1.0)[..., None]
VIG = None
def vignette(img, k=1.0):
    global VIG
    if VIG is None:
        VIG = _vignette().astype(np.float32)
    v = VIG if k == 1.0 else 1 - (1 - VIG) * k
    img[:] = (img * v).astype(np.uint8)

@functools.lru_cache(maxsize=8)
def nebula(seed=1, hue=(20, 40, 90), hue2=(60, 20, 80), k=1.0):
    """soft space nebula background (uint8)"""
    rng = np.random.default_rng(seed)
    small = np.zeros((48, 27, 3), np.float32)
    for _ in range(9):
        cx, cy = rng.uniform(0, 27), rng.uniform(0, 48)
        r = rng.uniform(4, 14)
        yy, xx = np.mgrid[0:48, 0:27]
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None]
        c = np.array(hue if rng.random() < 0.6 else hue2, np.float32)
        small += g * c * rng.uniform(0.3, 0.8)
    big = cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), 30) * k * 0.75
    img = np.clip(big + np.array(BG, np.float32), 0, 255)
    # stars
    n = 900
    xs, ys = rng.integers(0, W, n), rng.integers(0, H, n)
    br = rng.power(4, n) * 200
    for x, y, b in zip(xs, ys, br):
        img[y, x] = np.minimum(255, img[y, x] + b)
    img = cv2.GaussianBlur(img, (0, 0), 0.6)
    return img.astype(np.uint8)

@functools.lru_cache(maxsize=4)
def grid_bg(seed=3):
    img = nebula(seed, (10, 30, 60), (30, 15, 60), 0.8).copy()
    for x in range(0, W, 60):
        cv2.line(img, (x, 0), (x, H), (18, 26, 40), 1)
    for y in range(0, H, 60):
        cv2.line(img, (0, y), (W, y), (18, 26, 40), 1)
    return img
