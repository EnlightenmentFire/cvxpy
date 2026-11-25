# -*- coding: utf-8 -*-
"""画面基础：字体、文字图、光晕、纸纹、圆相、剪影等（全部程序绘制）。"""
import math, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920

INK = (13, 14, 18)
GOLD = (216, 180, 106)
VERM = (184, 67, 47)
JADE = (111, 163, 146)
MIST = (233, 228, 216)
GREY = (150, 146, 138)

FONT_FILES = {
    "sans": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 2),
    "sansb": ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2),
    "serif": ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 2),
    "serifr": ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 2),
    "kai": ("/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Regular.ttf", 0),
    "kaib": ("/usr/share/fonts/truetype/lxgw-wenkai/LXGWWenKai-Bold.ttf", 0),
    "ukai": ("/usr/share/fonts/truetype/arphic/ukai.ttc", 0),
}


@functools.lru_cache(maxsize=None)
def font(name, size):
    path, idx = FONT_FILES[name]
    try:
        return ImageFont.truetype(path, size, index=idx)
    except OSError:
        import glob
        if name.startswith("kai"):
            c = glob.glob("/usr/share/fonts/truetype/lxgw/*WenKai*Regular*") + glob.glob("/usr/share/fonts/**/LXGW*", recursive=True)
            return ImageFont.truetype(sorted(c)[0], size)
        raise


def lerp(a, b, t):
    return a + (b - a) * t


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def mixc(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


@functools.lru_cache(maxsize=4096)
def text_img(text, fname, size, color=MIST, stroke=0, stroke_color=(0, 0, 0), spacing=None, align="center", shadow=0):
    """多行文字 -> RGBA Image（已裁边）。"""
    f = font(fname, size)
    lines = text.split("\n")
    sp = spacing if spacing is not None else int(size * 0.42)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    boxes = [d.textbbox((0, 0), ln or " ", font=f, stroke_width=stroke) for ln in lines]
    widths = [b[2] - b[0] for b in boxes]
    lh = int(size * 1.18)
    w = max(widths) + 4 * stroke + 8 + 2 * shadow
    h = lh * len(lines) + sp * (len(lines) - 1) + 4 * stroke + 12 + 2 * shadow
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 2 * stroke + 4
    for ln, wd, b in zip(lines, widths, boxes):
        if align == "center":
            x = (w - wd) // 2 - b[0]
        else:
            x = 2 * stroke + 4 - b[0]
        if shadow:
            d.text((x + shadow, y + shadow), ln, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        d.text((x, y), ln, font=f, fill=color + (255,) if len(color) == 3 else color,
               stroke_width=stroke, stroke_fill=stroke_color)
        y += lh + sp
    if shadow:
        sh = im.filter(ImageFilter.GaussianBlur(shadow))
        im = Image.alpha_composite(sh, im)
    return im


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    al = im.getchannel("A").point(lambda v: int(v * a))
    im.putalpha(al)
    return im


def over(dst, im, xy, a=1.0, anchor="mm"):
    """把 RGBA im 合成到 dst（RGBA，原地），anchor: mm 居中 / lt 左上。"""
    if a <= 0.003 or im is None:
        return
    x, y = xy
    if anchor == "mm":
        x -= im.width // 2; y -= im.height // 2
    elif anchor == "mt":
        x -= im.width // 2
    elif anchor == "rt":
        x -= im.width
    elif anchor == "lm":
        y -= im.height // 2
    dst.alpha_composite(with_alpha(im, a), (int(x), int(y))) if 0 <= x and 0 <= y and x + im.width <= dst.width and y + im.height <= dst.height \
        else _over_clip(dst, with_alpha(im, a), int(x), int(y))


def _over_clip(dst, im, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.width, x + im.width), min(dst.height, y + im.height)
    if x1 <= x0 or y1 <= y0:
        return
    crop = im.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    dst.alpha_composite(crop, (x0, y0))


@functools.lru_cache(maxsize=256)
def glow(r, color, power=2.0, alpha=1.0):
    """径向光晕精灵，半径 r。"""
    s = 2 * r + 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = np.clip(1 - d, 0, 1) ** power * alpha
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def smooth_noise(w, h, scale, seed=0):
    rng = np.random.default_rng(seed)
    sw, sh = max(2, int(w / scale)), max(2, int(h / scale))
    n = rng.random((sh, sw)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0


@functools.lru_cache(maxsize=8)
def ink_bg(seed=0, base=INK, warm=0.0):
    """深墨底 + 细微纸纹 + 云气。返回 RGBA Image。"""
    n1 = smooth_noise(W, H, 240, seed)
    n2 = smooth_noise(W, H, 60, seed + 1)
    g = np.random.default_rng(seed + 2).normal(0, 1, (H, W)).astype(np.float32)
    v = 0.55 * n1 + 0.3 * n2
    arr = np.zeros((H, W, 3), np.float32)
    b = np.array(base, np.float32)
    tint = np.array([1.0 + 0.10 * warm, 1.0 + 0.05 * warm, 1.0], np.float32)
    arr[:] = b
    arr += (v[..., None] - 0.4) * 14 * tint + g[..., None] * 2.2
    # 柔和暗角
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2)
    arr *= np.clip(1.15 - 0.45 * d, 0.55, 1.1)[..., None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


@functools.lru_cache(maxsize=8)
def paper_tex(w, h, seed=3):
    n1 = smooth_noise(w, h, 120, seed)
    n2 = smooth_noise(w, h, 18, seed + 1)
    g = np.random.default_rng(seed).normal(0, 1, (h, w)).astype(np.float32)
    base = np.array([232, 222, 199], np.float32)
    arr = base + ((n1 - 0.5) * 18 + (n2 - 0.5) * 8 + g * 3)[..., None] * np.array([1, 1, 1.1])
    # 纤维
    rng = np.random.default_rng(seed + 9)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    for _ in range(int(w * h / 900)):
        x, y = rng.random() * w, rng.random() * h
        a = rng.random() * math.pi
        L = 6 + rng.random() * 22
        d.line((x, y, x + L * math.cos(a), y + L * math.sin(a)), fill=(205, 192, 165, 70), width=1)
    # 边缘做旧
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy])
    edge = np.clip(e / 40.0, 0, 1)
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] *= (0.86 + 0.14 * edge)[..., None]
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


@functools.lru_cache(maxsize=16)
def enso(r, thick, color=GOLD, gap_deg=28, start_deg=-60, seed=1, alpha=1.0):
    """禅宗圆相：笔触粗细变化 + 飞白。返回 RGBA。"""
    s = int(2 * (r + thick * 1.5) + 4)
    c = s / 2
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    dx, dy = xx - c, yy - c
    rad = np.sqrt(dx * dx + dy * dy)
    ang = (np.degrees(np.arctan2(dy, dx)) - start_deg) % 360  # 0..360 沿笔势
    u = ang / (360 - gap_deg)  # 0..1 笔程
    valid = u <= 1.0
    # 起笔重、收笔轻，中途起伏
    width = thick * (0.55 + 0.6 * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.6) * (1 - 0.55 * np.clip(u - 0.75, 0, 1) / 0.25)
    rr = r + thick * 0.18 * np.sin(u * 7.0 + seed)
    dist = np.abs(rad - rr)
    core = np.clip(1 - dist / (width * 0.5 + 1e-3), 0, 1)
    core = np.clip(core * 2.2, 0, 1)
    rng = np.random.default_rng(seed)
    # 飞白：沿径向的条纹，随笔程加强
    k = 60
    streak_phase = rng.random(k) * 2 * np.pi
    rel = (rad - rr) / (width + 1e-3)
    st = np.zeros_like(rad)
    for i in range(6):
        st += np.sin(rel * (9 + i * 7) + streak_phase[i]) * (0.5 ** i)
    dry = np.clip(0.75 + 0.6 * st, 0, 1)
    dryness = np.clip((u - 0.35) / 0.65, 0, 1)
    a = core * (1 - dryness * (1 - dry)) * valid
    nz = smooth_noise(s, s, 6, seed + 5)
    a *= (0.8 + 0.25 * nz)
    a = np.clip(a * alpha, 0, 1)
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# 侧脸剪影（单位坐标，面朝右；原点在头顶附近）
_PROFILE = [(-0.42, -0.05), (-0.40, -0.32), (-0.25, -0.52), (0.0, -0.58), (0.22, -0.52), (0.34, -0.36),
            (0.38, -0.18), (0.40, -0.06), (0.50, 0.06), (0.43, 0.10), (0.42, 0.16), (0.46, 0.21),
            (0.42, 0.25), (0.43, 0.30), (0.38, 0.38), (0.25, 0.43), (0.16, 0.44), (0.12, 0.62),
            (0.30, 0.80), (0.55, 0.92), (0.60, 1.10), (-0.70, 1.10), (-0.62, 0.90), (-0.34, 0.78),
            (-0.24, 0.55), (-0.30, 0.38), (-0.40, 0.22)]


def profile_poly(cx, cy, s, flip=False):
    return [(cx + (-x if flip else x) * s, cy + y * s) for x, y in _PROFILE]


def figure_poly(cx, base_y, h, pose="stand", flip=False):
    """极简人形：返回 (头圆心, 头半径, 身体多边形)。pose: stand / sit / curl / reach。"""
    s = h
    f = -1 if flip else 1
    if pose == "stand":
        head = (cx, base_y - 0.88 * s, 0.075 * s)
        body = [(cx - 0.11 * s, base_y - 0.78 * s), (cx + 0.11 * s, base_y - 0.78 * s), (cx + 0.13 * s, base_y - 0.42 * s),
                (cx + 0.08 * s, base_y), (cx + 0.02 * s, base_y), (cx, base_y - 0.38 * s), (cx - 0.02 * s, base_y),
                (cx - 0.08 * s, base_y), (cx - 0.13 * s, base_y - 0.42 * s)]
    elif pose == "curl":
        head = (cx + f * 0.10 * s, base_y - 0.36 * s, 0.075 * s)
        body = [(cx - f * 0.16 * s, base_y), (cx - f * 0.18 * s, base_y - 0.22 * s), (cx - f * 0.05 * s, base_y - 0.38 * s),
                (cx + f * 0.12 * s, base_y - 0.30 * s), (cx + f * 0.20 * s, base_y - 0.14 * s), (cx + f * 0.18 * s, base_y)]
    elif pose == "sit":
        head = (cx, base_y - 0.62 * s, 0.075 * s)
        body = [(cx - 0.11 * s, base_y - 0.52 * s), (cx + 0.10 * s, base_y - 0.52 * s), (cx + 0.12 * s, base_y - 0.22 * s),
                (cx + f * 0.30 * s, base_y - 0.18 * s), (cx + f * 0.30 * s, base_y), (cx - 0.12 * s, base_y)]
    else:
        raise ValueError(pose)
    return head, body


def draw_figure(d, cx, base_y, h, color, pose="stand", flip=False):
    (hx, hy, hr), body = figure_poly(cx, base_y, h, pose, flip)
    d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=color)
    d.polygon(body, fill=color)
