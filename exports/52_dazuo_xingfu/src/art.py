# -*- coding: utf-8 -*-
"""水墨画面引擎：宣纸、远山、竹、坐禅剪影、朱印、文字。全部程序生成。"""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1080, 1920
PAPER = (238, 231, 216)
INK = (28, 27, 26)
INK2 = (70, 68, 64)
GREY = (120, 116, 108)
ZHU = (178, 52, 40)        # 朱红
ZHU_L = (196, 92, 74)
GOLD = (196, 150, 82)

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-{}.ttc"
KAI = "/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-{}.ttf"


@functools.lru_cache(None)
def font(size, kind="serif", weight="Bold"):
    if kind == "serif":
        return ImageFont.truetype(SERIF.format(weight), size, index=2)
    if kind == "serif_tc":
        return ImageFont.truetype(SERIF.format(weight), size, index=3)
    if kind == "kai":
        return ImageFont.truetype(KAI.format(weight), size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", size)


def rng(seed):
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- 底子
@functools.lru_cache(None)
def paper(seed=1, tone=PAPER):
    r = rng(seed)
    base = np.zeros((H, W, 3), np.float32) + np.array(tone, np.float32)
    # 大尺度不均匀
    low = r.normal(0, 1, (H // 64 + 2, W // 64 + 2)).astype(np.float32)
    low = np.array(Image.fromarray(low).resize((W, H), Image.BICUBIC))
    base += low[..., None] * 3.5
    # 纤维
    fib = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(2600):
        x, y = r.uniform(0, W), r.uniform(0, H)
        a = r.uniform(0, math.pi); L = r.uniform(8, 40)
        d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=int(r.uniform(20, 60)), width=1)
    fib = np.array(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    base -= fib[..., None] * 10
    base += r.normal(0, 2.2, (H, W, 1)).astype(np.float32)
    # 四角压暗
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2
    base *= (1 - 0.16 * np.clip(v, 0, 1.4))[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def paper_img(seed=1):
    return Image.fromarray(paper(seed))


def fbm1d(n, seed, octaves=5, base=6):
    r = rng(seed)
    out = np.zeros(n, np.float32)
    amp, tot = 1.0, 0
    for o in range(octaves):
        k = base * 2 ** o
        pts = r.normal(0, 1, k + 3)
        xs = np.linspace(0, k, n)
        out += amp * np.interp(xs, np.arange(k + 3), pts)
        tot += amp; amp *= 0.5
    return out / tot


@functools.lru_cache(None)
def mountains(seed=3, layers=4, top=520, bottom=1250, darkest=0.55):
    """返回 RGBA：多层淡墨远山，越远越淡，山脚化入雾中。"""
    img = np.zeros((H, W, 4), np.float32)
    for i in range(layers):
        f = i / max(1, layers - 1)
        ridge = fbm1d(W, seed + i * 11, base=3 + i) * (140 - 30 * i)
        y0 = top + (bottom - top) * (0.15 + 0.6 * f)
        ys = y0 + ridge - 90 * np.exp(-((np.arange(W) - W * (0.3 + 0.4 * ((seed + i) % 3) / 2)) / 260) ** 2)
        yy = np.arange(H)[:, None].astype(np.float32)
        inside = (yy > ys[None, :]).astype(np.float32)
        depth = np.clip((yy - ys[None, :]) / (180 + 60 * i), 0, 1)
        a = inside * (1 - depth) ** 1.6 * (0.18 + darkest * f * 0.8)
        # 山脊线更浓
        a += inside * np.exp(-np.clip(yy - ys[None, :], 0, None) / 6) * 0.10 * (0.5 + f)
        col = np.array(INK2 if i < layers - 1 else INK, np.float32)
        img[..., :3] = img[..., :3] * (1 - a[..., None]) + col * a[..., None]
        img[..., 3] = img[..., 3] * (1 - a) + a
    rgb = np.where(img[..., 3:4] > 1e-4, img[..., :3] / np.maximum(img[..., 3:4], 1e-4), 0)
    out = np.dstack([rgb, img[..., 3] * 255]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def mist(top, bottom, strength=0.85, color=PAPER):
    a = np.zeros((H, W), np.float32)
    yy = np.arange(H, dtype=np.float32)
    mid = (top + bottom) / 2
    prof = np.exp(-((yy - mid) / ((bottom - top) / 2.2)) ** 2) * strength
    a[:] = prof[:, None]
    img = np.dstack([np.full((H, W), c, np.float32) for c in color] + [a * 255]).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def glow(cx, cy, r, color=GOLD, alpha=0.35):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    a = np.exp(-d ** 2) * alpha
    img = np.dstack([np.full((H, W), c, np.float32) for c in color] + [a * 255]).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


# ---------------------------------------------------------------- 笔触
def brush_line(d, pts, w0, w1, color, alpha=255):
    """粗细渐变的笔画（用一串圆近似）。pts: [(x,y)...]"""
    pts = np.asarray(pts, np.float32)
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    L = seg.sum()
    if L < 1:
        return
    n = max(2, int(L / 1.5))
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, L, n)
    xs = np.interp(s, cum, pts[:, 0]); ys = np.interp(s, cum, pts[:, 1])
    for i in range(n):
        f = s[i] / L
        w = w0 + (w1 - w0) * f
        w *= 0.85 + 0.3 * math.sin(f * math.pi)
        d.ellipse([xs[i] - w / 2, ys[i] - w / 2, xs[i] + w / 2, ys[i] + w / 2], fill=color + (alpha,))


def leaf(d, x, y, ang, L, wid, color, alpha):
    """竹叶：两头尖的弧形。"""
    pts = []
    for s in np.linspace(0, 1, 14):
        w = wid * math.sin(math.pi * s) ** 0.8
        cx = x + math.cos(ang) * L * s
        cy = y + math.sin(ang) * L * s + 0.12 * L * s * s
        pts.append((cx - math.sin(ang) * w, cy + math.cos(ang) * w))
    for s in np.linspace(1, 0, 14):
        w = wid * math.sin(math.pi * s) ** 0.8 * 0.3
        cx = x + math.cos(ang) * L * s
        cy = y + math.sin(ang) * L * s + 0.12 * L * s * s
        pts.append((cx + math.sin(ang) * w, cy - math.cos(ang) * w))
    d.polygon(pts, fill=color + (alpha,))


@functools.lru_cache(None)
def bamboo_spec(seed=5, x0=860, n=4):
    r = rng(seed)
    stalks = []
    for i in range(n):
        x = x0 + r.uniform(-120, 160) + i * 40
        lean = r.uniform(-0.12, 0.05)
        top = r.uniform(250, 600)
        nodes = np.sort(r.uniform(top, 1400, 6))
        leaves = []
        for k in range(r.integers(4, 7)):
            y = r.uniform(top, top + 700)
            for j in range(r.integers(3, 6)):
                ang = r.uniform(-2.6, -0.3) if r.random() < 0.5 else r.uniform(0.3, 2.9)
                leaves.append((y, ang, r.uniform(70, 130), r.uniform(8, 15), r.uniform(0.6, 1.0)))
        stalks.append(dict(x=x, lean=lean, top=top, nodes=nodes, w=r.uniform(13, 22),
                           alpha=r.uniform(0.55, 1.0), leaves=leaves, ph=r.uniform(0, 6.28)))
    return stalks


def bamboo(t, seed=5, x0=860, n=4, color=INK, alpha=1.0, sway=1.0):
    """竹：随风轻摆。返回 RGBA 全幅图层。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for s in bamboo_spec(seed, x0, n):
        a = int(255 * s["alpha"] * alpha)
        bottom = 1480
        def X(y):
            h = (bottom - y) / (bottom - s["top"])
            return s["x"] + s["lean"] * (bottom - y) + sway * 18 * h * h * math.sin(t * 0.9 + s["ph"])
        ys = np.linspace(bottom, s["top"], 30)
        brush_line(d, [(X(y), y) for y in ys], s["w"], s["w"] * 0.55, color, a)
        for ny in s["nodes"]:
            d.line([(X(ny) - s["w"] * 0.7, ny), (X(ny) + s["w"] * 0.7, ny - 3)], fill=PAPER + (int(a * 0.8),), width=3)
        for (ly, ang, L, wd, la) in s["leaves"]:
            if ly < s["top"]:
                continue
            ang2 = ang + 0.10 * sway * math.sin(t * 1.3 + ly * 0.01 + s["ph"])
            leaf(d, X(ly), ly, ang2, L, wd, color, int(a * la))
    return img


def _catmull(pts, n=10):
    pts = list(pts)
    P = [pts[-1]] + pts + pts[:2]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    return out


# 坐禅轮廓（右半边，y 向上，底为 0）
_SEAT_R = [(0, 338), (17, 336), (22, 322), (62, 312), (95, 293), (110, 255), (118, 205), (128, 160),
           (150, 118), (196, 78), (222, 42), (214, 14), (170, 2)]


def seated_figure(cx, base_y, scale=1.0, color=INK, alpha=235):
    """坐禅剪影（正面，结跏趺坐，定印）。返回 RGBA 小图及左上角坐标。"""
    s = scale
    w, h = int(480 * s), int(470 * s)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = color + (alpha,)
    ox, by = w / 2, h - 8 * s
    right = [(ox + x * s, by - y * s) for x, y in _SEAT_R]
    left = [(ox - x * s, by - y * s) for x, y in reversed(_SEAT_R)]
    d.polygon(_catmull(right + left[1:-1], 8), fill=c)
    d.ellipse([ox - 40 * s, by - 432 * s, ox + 40 * s, by - 330 * s], fill=c)      # 头
    d.ellipse([ox - 17 * s, by - 458 * s, ox + 17 * s, by - 420 * s], fill=c)      # 发髻
    lt = PAPER + (45,)
    lw = max(2, int(3 * s))
    d.arc([ox - 62 * s, by - 150 * s, ox + 62 * s, by - 86 * s], 15, 165, fill=lt, width=lw)   # 定印
    d.line([(ox - 100 * s, by - 228 * s), (ox - 64 * s, by - 128 * s)], fill=lt, width=lw)     # 臂褶
    d.line([(ox + 100 * s, by - 228 * s), (ox + 64 * s, by - 128 * s)], fill=lt, width=lw)
    d.arc([ox - 200 * s, by - 70 * s, ox + 200 * s, by + 30 * s], 195, 345, fill=lt, width=lw)  # 腿
    img = img.filter(ImageFilter.GaussianBlur(0.9 * s))
    return img, (int(cx - w / 2), int(base_y - h))


def standing_figure(cx, base_y, scale=1.0, phase=0.0, color=INK, alpha=230):
    """行走剪影。phase: 步态相位。"""
    s = scale
    w, h = int(200 * s), int(470 * s)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = color + (alpha,)
    ox = w / 2
    sw = math.sin(phase) * 30 * s
    # 腿
    brush_line(d, [(ox, h - 190 * s), (ox + sw, h - 5 * s)], 26 * s, 20 * s, color, alpha)
    brush_line(d, [(ox, h - 190 * s), (ox - sw, h - 5 * s)], 26 * s, 20 * s, color, alpha)
    # 袍
    d.polygon([(ox - 45 * s, h - 150 * s), (ox - 35 * s, h - 340 * s), (ox + 35 * s, h - 340 * s),
               (ox + 50 * s, h - 150 * s)], fill=c)
    d.ellipse([ox - 52 * s, h - 365 * s, ox + 52 * s, h - 315 * s], fill=c)
    d.ellipse([ox - 36 * s, h - 450 * s, ox + 36 * s, h - 370 * s], fill=c)
    brush_line(d, [(ox - 40 * s, h - 330 * s), (ox - 50 * s - sw * 0.5, h - 200 * s)], 20 * s, 16 * s, color, alpha)
    brush_line(d, [(ox + 40 * s, h - 330 * s), (ox + 50 * s + sw * 0.5, h - 200 * s)], 20 * s, 16 * s, color, alpha)
    return img.filter(ImageFilter.GaussianBlur(0.8 * s)), (int(cx - w / 2), int(base_y - h))


@functools.lru_cache(None)
def seal(text, size=120, color=ZHU, seed=7, style="white"):
    """朱印：style='white' 白文（红底白字），'red' 朱文（红框红字）。"""
    r = rng(seed)
    n = len(text)
    cols = 1 if n <= 2 else 2
    rows = math.ceil(n / cols)
    cw = size * 0.9
    w = int(cw * cols + size * 0.35); h = int(cw * rows + size * 0.35)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(int(cw * 0.86), "serif", "Black")
    if style == "white":
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(size * 0.08), fill=color + (235,))
        tc = (0, 0, 0, 0)
    else:
        d.rounded_rectangle([3, 3, w - 4, h - 4], radius=int(size * 0.08), outline=color + (235,), width=max(4, size // 14))
        tc = color + (235,)
    # 竖排，右起
    for i, ch in enumerate(text):
        col = i // rows; row = i % rows
        x = w - size * 0.175 - cw * (col + 1) + cw * 0.07
        y = size * 0.175 + cw * row - cw * 0.08
        if style == "white":
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).text((x, y), ch, font=f, fill=255)
            img.putalpha(ImageChops.subtract(img.getchannel("A"), mask))
        else:
            d.text((x, y), ch, font=f, fill=tc)
    # 斑驳
    a = np.array(img.getchannel("A"), np.float32)
    noise = r.random(a.shape) < 0.035
    a[noise] *= 0.25
    blot = np.array(Image.fromarray((r.random((h // 8 + 1, w // 8 + 1)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    a *= np.clip(0.75 + blot * 0.5, 0, 1)
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img


# ---------------------------------------------------------------- 文字
def text_size(s, f):
    b = f.getbbox(s)
    return b[2] - b[0], b[3] - b[1]


@functools.lru_cache(maxsize=4096)
def text_sprite(s, size, kind="serif", weight="Bold", color=INK, stroke=0, stroke_color=PAPER, spacing=0):
    f = font(size, kind, weight)
    if spacing:
        ws = [f.getlength(c) for c in s]
        tw = int(sum(ws) + spacing * (len(s) - 1)) + 2 * stroke + 4
    else:
        tw = int(f.getlength(s)) + 2 * stroke + 4
    th = int(size * 1.35) + 2 * stroke
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if spacing:
        x = stroke + 2
        for c, cw in zip(s, ws):
            d.text((x, stroke), c, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
            x += cw + spacing
    else:
        d.text((stroke + 2, stroke), s, font=f, fill=color + (255,), stroke_width=stroke, stroke_fill=stroke_color + (255,))
    return img


@functools.lru_cache(maxsize=256)
def vtext_sprite(s, size, kind="kai", weight="Regular", color=INK, gap=0.12):
    """竖排文字（标点占位缩小）。"""
    f = font(size, kind, weight)
    step = size * (1 + gap)
    n = len(s)
    img = Image.new("RGBA", (int(size * 1.3), int(step * n + size * 0.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = 0
    for ch in s:
        if ch in "，。、；：！？":
            d.text((size * 0.55, y - size * 0.35), ch, font=f, fill=color + (255,))
            y += step * 0.5
        else:
            d.text((size * 0.1, y), ch, font=f, fill=color + (255,))
            y += step
    return img.crop((0, 0, img.width, int(y + size * 0.3)))


def put(base, sprite, xy, alpha=1.0, anchor="lt"):
    """把 RGBA sprite 以不透明度 alpha 叠到 base（RGBA）上。anchor: lt / mt / mm"""
    if alpha <= 0.003 or sprite is None:
        return
    x, y = xy
    if anchor == "mt":
        x -= sprite.width / 2
    elif anchor == "mm":
        x -= sprite.width / 2; y -= sprite.height / 2
    elif anchor == "rt":
        x -= sprite.width
    x, y = int(round(x)), int(round(y))
    if alpha < 0.997:
        a = sprite.getchannel("A").point(lambda v: int(v * alpha))
        sprite = sprite.copy(); sprite.putalpha(a)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sprite.width, base.width - x), min(sprite.height, base.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, sprite.width, sprite.height):
        sprite = sprite.crop((sx0, sy0, sx1, sy1))
    base.alpha_composite(sprite, (max(0, x), max(0, y)))


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def fade(t, t0, dur=0.6):
    return ease((t - t0) / dur)
