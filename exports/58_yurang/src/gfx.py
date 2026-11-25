# -*- coding: utf-8 -*-
"""画面基础库：numpy float32 画布 (H, W, 3)，取值 0–1。全部程序生成，不用外部素材。"""
import math
from functools import lru_cache
import numpy as np
import cv2
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FD = "/usr/share/fonts/opentype/noto/"
SC, TC = 2, 3   # ttc 索引：简体 / 繁体


@lru_cache(maxsize=256)
def font(weight="Bold", size=48, idx=SC, sans=False):
    fam = "NotoSansCJK" if sans else "NotoSerifCJK"
    return ImageFont.truetype(f"{FD}{fam}-{weight}.ttc", size, index=idx)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


# 调色板：夜、月、金、朱
NIGHT = hexc("#070b12")
INDIGO = hexc("#101a2b")
MOON = hexc("#c9d6e8")
GOLD = hexc("#e2bd72")
GOLD_D = hexc("#9c7a3c")
RED = hexc("#c23b2a")
RED_D = hexc("#6e1a14")
FIRE = hexc("#ff9a3c")
PAPER = hexc("#e9dfc8")
INK = hexc("#151515")
BLUE = hexc("#4f86c6")


def clamp01(x):
    return np.clip(x, 0, 1)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = min(max(t, 0.0), 1.0)
    return t ** 3


def ramp(t, a, b):
    """t 在 [a, b] 间 0→1（平滑）。"""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return ease((t - a) / (b - a))


def fade_io(t, dur, fi=0.4, fo=0.4):
    return min(ramp(t, 0, fi), 1 - ramp(t, dur - fo, dur))


# ---------------------------------------------------------------- 噪声
def fbm(w, h, seed=0, octaves=6, base=4, persistence=0.55):
    """分形值噪声（双三次放大随机网格），返回 0–1。"""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw, gh = max(2, int(base * 2 ** o * w / max(w, h)) + 2), max(2, int(base * 2 ** o * h / max(w, h)) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(g, mode="F").resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(im)
        tot += amp
        amp *= persistence
    acc /= tot
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)
    return acc


def vgrad(h, w, top, bot, gamma=1.0):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** gamma
    return np.broadcast_to(top * (1 - t) + bot * t, (h, w, 3)).astype(np.float32).copy()


def radial(h, w, cx, cy, r, power=2.0):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
    return np.clip(1 - d, 0, 1).astype(np.float32) ** power


@lru_cache(maxsize=4)
def vignette(strength=0.65, w=W, h=H):
    y, x = np.ogrid[:h, :w]
    d = np.sqrt(((x - w / 2) / (w * 0.62)) ** 2 + ((y - h / 2) / (h * 0.60)) ** 2)
    v = 1 - strength * np.clip(d - 0.35, 0, 1) ** 1.4
    return v.astype(np.float32)[:, :, None]


_GRAIN = None


def grain(img, t, amt=0.035):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7)
        _GRAIN = (rng.random((H // 2 + 64, W // 2 + 64)).astype(np.float32) - 0.5)
    k = int(t * 25) % 17
    ox, oy = (k * 37) % 64, (k * 23) % 64
    g = _GRAIN[oy:oy + H // 2, ox:ox + W // 2]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:, :, None]
    return img + g * amt


# ---------------------------------------------------------------- 图层
def to_img(a):
    return Image.fromarray((clamp01(a) * 255 + 0.5).astype(np.uint8))


def from_img(im):
    return np.asarray(im.convert("RGB"), np.float32) / 255


def over(dst, rgb, alpha):
    """alpha: (H,W) 或 (H,W,1) 或标量。"""
    if np.ndim(alpha) == 2:
        alpha = alpha[:, :, None]
    return dst * (1 - alpha) + rgb * alpha


def add(dst, rgb, k=1.0):
    return dst + rgb * k


def screen(dst, rgb):
    return 1 - (1 - dst) * (1 - rgb)


def blur(a, r):
    """快速高斯模糊（cv2）：大半径先缩小。a 为 (H,W) 或 (H,W,3)。"""
    if r <= 0:
        return a
    h, w = a.shape[:2]
    s = 4 if r > 12 else 2 if r > 4 else 1
    a = np.ascontiguousarray(a, dtype=np.float32)
    if s > 1:
        b = cv2.resize(a, (w // s, h // s), interpolation=cv2.INTER_AREA)
        b = cv2.GaussianBlur(b, (0, 0), r / s)
        return cv2.resize(b, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(a, (0, 0), r)


def glow(a, r=30, k=0.8):
    return a + blur(a, r) * k


def mask_from_poly(polys, w=W, h=H, ss=2, blur_r=0):
    """多边形 → 抗锯齿 alpha (H,W)。只在包围盒内超采样，快。
    polys: [[(x,y),...], ('ellipse', box), ('line', pts, width)]"""
    xs, ys, pad = [], [], 4 + blur_r * 3
    for p in polys:
        if isinstance(p, tuple) and p and p[0] == "ellipse":
            xs += [p[1][0], p[1][2]]; ys += [p[1][1], p[1][3]]
        elif isinstance(p, tuple) and p and p[0] == "line":
            xs += [q[0] for q in p[1]]; ys += [q[1] for q in p[1]]; pad = max(pad, p[2] + 4 + blur_r * 3)
        else:
            xs += [q[0] for q in p]; ys += [q[1] for q in p]
    out = np.zeros((h, w), np.float32)
    if not xs:
        return out
    x0 = int(max(0, min(xs) - pad)); x1 = int(min(w, max(xs) + pad + 1))
    y0 = int(max(0, min(ys) - pad)); y1 = int(min(h, max(ys) + pad + 1))
    if x1 <= x0 or y1 <= y0:
        return out
    bw, bh = x1 - x0, y1 - y0
    im = Image.new("L", (bw * ss, bh * ss), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        if isinstance(p, tuple) and p and p[0] == "ellipse":
            e = p[1]
            d.ellipse([(e[0] - x0) * ss, (e[1] - y0) * ss, (e[2] - x0) * ss, (e[3] - y0) * ss], fill=255)
        elif isinstance(p, tuple) and p and p[0] == "line":
            d.line([((x - x0) * ss, (y - y0) * ss) for x, y in p[1]], fill=255, width=max(1, int(p[2] * ss)), joint="curve")
        else:
            d.polygon([((x - x0) * ss, (y - y0) * ss) for x, y in p], fill=255)
    if ss > 1:
        im = im.resize((bw, bh), Image.BOX)
    a = np.asarray(im, np.float32) / 255
    if blur_r:
        a = cv2.GaussianBlur(a, (0, 0), blur_r)
    out[y0:y1, x0:x1] = a
    return out


def bezier(pts, n=24):
    """二次/三次贝塞尔折线采样。pts 为控制点。"""
    pts = np.array(pts, np.float32)
    t = np.linspace(0, 1, n)[:, None]
    k = len(pts) - 1
    out = np.zeros((n, 2), np.float32)
    for i, p in enumerate(pts):
        out += math.comb(k, i) * (t ** i) * ((1 - t) ** (k - i)) * p
    return [tuple(map(float, q)) for q in out]


def path(*segs):
    out = []
    for s in segs:
        out += bezier(s) if len(s) > 2 else list(s)
    return out


# ---------------------------------------------------------------- 文字
def text_layer(lines, fnt, fill=(1, 1, 1), anchor_xy=(W // 2, H // 2), align="center", spacing=1.25,
               stroke=0, stroke_fill=(0, 0, 0), shadow=0, vertical=False, w=W, h=H, tracking=0):
    """返回 (rgb, alpha)。lines: list[str]。vertical=True 时竖排，从右到左列。"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = tuple(int(c * 255) for c in fill) + (255,)
    scol = tuple(int(c * 255) for c in stroke_fill) + (255,)
    size = fnt.size
    if vertical:
        colw = int(size * spacing)
        ncol = len(lines)
        x0 = anchor_xy[0] + (ncol - 1) * colw / 2
        for ci, ln in enumerate(lines):
            x = x0 - ci * colw
            y = anchor_xy[1] - len(ln) * (size + tracking) / 2
            for ch in ln:
                d.text((x, y), ch, font=fnt, fill=col, anchor="mt", stroke_width=stroke, stroke_fill=scol)
                y += size + tracking
    else:
        lh = size * spacing
        y0 = anchor_xy[1] - lh * (len(lines) - 1) / 2
        for i, ln in enumerate(lines):
            y = y0 + i * lh
            if align == "center":
                d.text((anchor_xy[0], y), ln, font=fnt, fill=col, anchor="mm", stroke_width=stroke, stroke_fill=scol)
            elif align == "left":
                d.text((anchor_xy[0], y), ln, font=fnt, fill=col, anchor="lm", stroke_width=stroke, stroke_fill=scol)
            else:
                d.text((anchor_xy[0], y), ln, font=fnt, fill=col, anchor="rm", stroke_width=stroke, stroke_fill=scol)
    a = np.asarray(im, np.float32) / 255
    rgb, al = a[:, :, :3], a[:, :, 3]
    if shadow:
        sh = blur(al, shadow)
        return rgb, al, sh
    return rgb, al


def put_text(img, lines, fnt, fill=(1, 1, 1), xy=(W // 2, H // 2), alpha=1.0, shadow=10, shadow_k=0.75,
             glow_col=None, glow_r=20, glow_k=0.6, **kw):
    if alpha <= 0.002:
        return img
    rgb, al, sh = text_layer(lines, fnt, fill, xy, shadow=shadow or 1, **kw)
    img = img * (1 - (sh * shadow_k * alpha)[:, :, None])
    if glow_col is not None:
        g = blur(al, glow_r)
        img = img + g[:, :, None] * np.asarray(glow_col, np.float32) * glow_k * alpha
    return over(img, rgb, al * alpha)


def wrap(s, n):
    """按标点优先断行，每行不超过 n 字。"""
    out, cur = [], ""
    for ch in s:
        cur += ch
        if len(cur) >= n:
            # 回退到最近的标点
            k = max(cur.rfind(c) for c in "，。；：、！？")
            if k >= n // 2 and k < len(cur) - 1:
                out.append(cur[:k + 1]); cur = cur[k + 1:]
            else:
                out.append(cur); cur = ""
    if cur:
        out.append(cur)
    # 行首标点挪回上一行
    for i in range(1, len(out)):
        while out[i] and out[i][0] in "，。；：、！？」』":
            out[i - 1] += out[i][0]; out[i] = out[i][1:]
    return [x for x in out if x]


# ---------------------------------------------------------------- 粒子
class Particles:
    """确定性粒子：由 seed 生成，按时间求位置。"""

    def __init__(self, n, seed, box, vel, life, size, color, wobble=0.0, gravity=0.0):
        rng = np.random.default_rng(seed)
        x0, y0, x1, y1 = box
        self.p0 = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)], 1)
        vx, vy, vj = vel
        self.v = np.stack([rng.normal(vx, vj, n), rng.normal(vy, vj, n)], 1)
        self.birth = rng.uniform(0, life, n)
        self.life = life
        self.size = rng.uniform(size[0], size[1], n)
        self.ph = rng.uniform(0, 6.28, n)
        self.color = np.asarray(color, np.float32)
        self.wob = wobble
        self.g = gravity

    def draw(self, img, t, k=1.0, flick=True):
        age = (t + self.birth) % self.life
        pos = self.p0 + self.v * age[:, None]
        pos[:, 1] += 0.5 * self.g * age ** 2
        pos[:, 0] += self.wob * np.sin(self.ph + age * 2.1)
        a = np.sin(np.pi * age / self.life) ** 1.5
        if flick:
            a = a * (0.65 + 0.35 * np.sin(self.ph * 3 + t * 9))
        lay = np.zeros((H // 2, W // 2), np.float32)
        xs, ys = (pos[:, 0] / 2).astype(int), (pos[:, 1] / 2).astype(int)
        ok = (xs >= 1) & (xs < W // 2 - 1) & (ys >= 1) & (ys < H // 2 - 1)
        np.add.at(lay, (ys[ok], xs[ok]), a[ok] * self.size[ok])
        lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.2), (W, H), interpolation=cv2.INTER_LINEAR)
        core = lay[:, :, None] * self.color * k
        return img + core + blur(lay, 10)[:, :, None] * self.color * k * 0.8


# ---------------------------------------------------------------- 镜头
def kenburns(src, t, dur, z0=1.0, z1=1.08, c0=(0.5, 0.5), c1=(0.5, 0.5)):
    """src: 大于等于画面的 numpy 图；按时间缩放平移。"""
    u = ease(t / max(dur, 1e-3))
    z = z0 + (z1 - z0) * u
    cx = c0[0] + (c1[0] - c0[0]) * u
    cy = c0[1] + (c1[1] - c0[1]) * u
    sh, sw = src.shape[:2]
    cw, ch = W / z * sw / W, H / z * sh / H
    cw, ch = min(cw, sw), min(ch, sh)
    x0 = np.clip(cx * sw - cw / 2, 0, sw - cw)
    y0 = np.clip(cy * sh - ch / 2, 0, sh - ch)
    im = to_img(src) if src.dtype != np.uint8 else Image.fromarray(src)
    im = im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255


def shake(img, t, amp):
    if amp < 0.5:
        return img
    dx = int(amp * math.sin(t * 53.0)); dy = int(amp * math.cos(t * 47.0))
    return np.roll(np.roll(img, dx, 1), dy, 0)
