# -*- coding: utf-8 -*-
"""渲染引擎：文字精灵、古文卡、粒子、地图、剪影等通用件。全部程序化绘制，无外部图片。"""
import math, random, os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 25
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, '..', 'fonts')
NOTO = '/usr/share/fonts/opentype/noto/'
FONTS = {
    'sans': (NOTO + 'NotoSansCJK-Bold.ttc', 2),
    'black': (NOTO + 'NotoSansCJK-Black.ttc', 2),
    'serif': (NOTO + 'NotoSerifCJK-Bold.ttc', 3),      # TC 字形，古文原句
    'serifsc': (NOTO + 'NotoSerifCJK-Bold.ttc', 2),
    'brush': (os.path.join(FD, 'MaShanZheng-full.ttf'), 0),  # 仅简体
}

# 颜色
INK = (11, 10, 12)
GOLD = (222, 184, 108)
GOLD2 = (245, 214, 150)
PAPER = (236, 224, 198)
RED = (214, 52, 38)        # 刘氏朱红
RED2 = (255, 96, 64)
QIN = (104, 124, 148)      # 秦军冷蓝灰
QIN2 = (150, 170, 195)
ORANGE = (255, 150, 40)
WHITE = (245, 242, 235)
GREY = (170, 166, 160)
TEAL = (120, 190, 185)     # 研究观点角标


@lru_cache(64)
def font(name, size):
    p, i = FONTS[name]
    return ImageFont.truetype(p, size, index=i)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)


def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def appear(t, t0, d=0.5):
    return ease((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def window(t, t0, t1, fi=0.4, fo=0.4):
    """t0 渐入, t1 渐出"""
    return min(appear(t, t0, fi), 1 - appear(t, t1 - fo, fo))


_LUT = {}


def _alpha_mask(im, a):
    m = im.getchannel('A')
    if a >= 0.999: return m
    q = int(a * 100)
    if q not in _LUT: _LUT[q] = [int(v * q / 100) for v in range(256)]
    return m.point(_LUT[q])


def put(cv, im, x, y, a=1.0, anchor='mm', scale=1.0):
    """把 RGBA 精灵贴到 cv（RGBA）上。anchor: 'mm' 中心, 'lt' 左上, 'mt' 顶中, 'lm' 左中, 'rb' 右下"""
    if a <= 0.004 or im is None: return
    if abs(scale - 1) > 0.003:
        w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((w, h), Image.BILINEAR)
    w, h = im.size
    ax = {'l': 0, 'm': w / 2, 'r': w}[anchor[0]]
    ay = {'t': 0, 'm': h / 2, 'b': h}[anchor[1]]
    cv.paste(im, (int(round(x - ax)), int(round(y - ay))), _alpha_mask(im, a))


def glowify(im, radius=10, color=None, strength=1.0):
    a = im.getchannel('A')
    pad = radius * 3
    big = Image.new('L', (im.width + 2 * pad, im.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    g = big.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1: g = g.point(lambda v: min(255, int(v * strength)))
    col = color or (255, 200, 120)
    out = Image.new('RGBA', big.size, col + (0,))
    out.putalpha(g)
    out.alpha_composite(im, (pad, pad))
    return out


@lru_cache(2048)
def txt(s, size=48, f='sans', fill=WHITE, stroke=0, sfill=(0, 0, 0), glow=0, gcol=None, gstr=1.0, spacing=0):
    fo = font(f, size)
    if spacing:
        # 手动字距
        ws = [fo.getbbox(c)[2] - fo.getbbox(c)[0] if c.strip() else size // 2 for c in s]
        tw = sum(fo.getlength(c) for c in s) + spacing * (len(s) - 1)
        asc, desc = fo.getmetrics()
        im = Image.new('RGBA', (int(tw + 2 * stroke + 8), asc + desc + 2 * stroke + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im); x = stroke + 4
        for c in s:
            d.text((x, stroke + 4), c, font=fo, fill=fill + (255,), stroke_width=stroke, stroke_fill=sfill + (255,))
            x += fo.getlength(c) + spacing
    else:
        bb = fo.getbbox(s, stroke_width=stroke)
        asc, desc = fo.getmetrics()
        im = Image.new('RGBA', (bb[2] - min(0, bb[0]) + 8, asc + desc + 2 * stroke + 8), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((4 - min(0, bb[0]), 4 + stroke), s, font=fo, fill=fill + (255,), stroke_width=stroke, stroke_fill=sfill + (255,))
    im = im.crop(im.getbbox() or (0, 0, 1, 1))
    if glow:
        im = glowify(im, glow, gcol or fill, gstr)
    return im


def vtxt(s, size, f='serif', fill=WHITE, gap=6, glow=0, gcol=None):
    """竖排一列"""
    ims = [txt(c, size, f, fill) for c in s]
    h = sum(size + gap for _ in ims)
    out = Image.new('RGBA', (int(size * 1.2), h), (0, 0, 0, 0))
    y = 0
    for im in ims:
        out.alpha_composite(im, (int((out.width - im.width) / 2), y + int((size - im.height) / 2)))
        y += size + gap
    if glow: out = glowify(out, glow, gcol or fill)
    return out


def wrap(s, size, f, maxw):
    fo = font(f, size)
    lines, cur = [], ''
    no_start = '，。、；：！？」』）》…'
    for c in s:
        if fo.getlength(cur + c) > maxw and cur:
            if c in no_start:  # 标点不放行首
                cur += c; continue
            lines.append(cur); cur = c
        else:
            cur += c
    if cur: lines.append(cur)
    return lines


@lru_cache(512)
def block(s, size=48, f='sans', fill=WHITE, maxw=900, lh=1.45, align='c', stroke=0, glow=0, gcol=None):
    ls = wrap(s, size, f, maxw)
    ims = [txt(l, size, f, fill, stroke) for l in ls]
    w = max(i.width for i in ims); hh = int(size * lh)
    out = Image.new('RGBA', (w + 4, hh * (len(ims) - 1) + max(i.height for i in ims) + 4), (0, 0, 0, 0))
    for k, im in enumerate(ims):
        x = {'c': (w - im.width) // 2, 'l': 0, 'r': w - im.width}[align]
        out.alpha_composite(im, (x + 2, k * hh + 2))
    if glow: out = glowify(out, glow, gcol or fill)
    return out


def rrect(size, r, fill, outline=None, width=2):
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=fill, outline=outline, width=width)
    return im


@lru_cache(128)
def tag(s, col=GOLD, size=30, fill_a=40, f='sans'):
    t = txt(s, size, f, col)
    im = Image.new('RGBA', (t.width + 34, t.height + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width - 1, im.height - 1), fill=col + (fill_a,), outline=col + (230,), width=2)
    d.rectangle((4, 4, im.width - 5, im.height - 5), outline=col + (90,), width=1)
    im.alpha_composite(t, (17, 10))
    return im


@lru_cache(128)
def qcard(text, src, bai=None, width=960, size=54, label='史料原文', lcol=GOLD):
    """古文卡：深色半透明底、金描边、宋体原文、右下出处；下接一行白话"""
    pad = 48
    body = block(text, size, 'serif', (246, 232, 196), width - 2 * pad, 1.5, 'l')
    srcim = txt('——' + src, 30, 'serif', GOLD)
    baim = block(bai, 36, 'sans', (215, 210, 200), width - 2 * pad, 1.45, 'l') if bai else None
    h = pad + 26 + body.height + 22 + srcim.height + (30 + baim.height if baim else 0) + pad - 8
    im = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, width - 1, h - 1), fill=(14, 11, 9, 214), outline=GOLD + (235,), width=3)
    d.rectangle((9, 9, width - 10, h - 10), outline=GOLD + (80,), width=1)
    for (cx, cy) in [(0, 0), (width - 1, 0), (0, h - 1), (width - 1, h - 1)]:  # 角饰
        sx = 1 if cx == 0 else -1; sy = 1 if cy == 0 else -1
        d.line((cx, cy + sy * 2, cx + sx * 34, cy + sy * 2), fill=GOLD2 + (255,), width=5)
        d.line((cx + sx * 2, cy, cx + sx * 2, cy + sy * 34), fill=GOLD2 + (255,), width=5)
    lab = tag(label, lcol, 24, 50)
    im.alpha_composite(lab, (pad - 6, 22))
    y = pad + 30
    im.alpha_composite(body, (pad, y)); y += body.height + 22
    im.alpha_composite(srcim, (width - pad - srcim.width, y)); y += srcim.height
    if baim:
        y += 16
        d.line((pad, y, width - pad, y), fill=GOLD + (90,), width=1)
        y += 14
        im.alpha_composite(baim, (pad, y))
    return im


# ───────── 噪声 / 背景 ─────────
def fnoise(w, h, seed=0, octaves=5, base=4):
    rng = np.random.RandomState(seed)
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        sm = rng.rand(max(2, int(n * h / w)) + 1, n + 1).astype(np.float32)
        im = Image.fromarray((sm * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= 0.5
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min() + 1e-6)


def grad_bg(top, bottom, w=W, h=H, mid=None, midpos=0.5):
    y = np.linspace(0, 1, h)[:, None]
    top = np.array(top, np.float32); bottom = np.array(bottom, np.float32)
    if mid is None:
        c = top * (1 - y) + bottom * y
    else:
        mid = np.array(mid, np.float32)
        a = np.clip(y / midpos, 0, 1); b = np.clip((y - midpos) / (1 - midpos), 0, 1)
        c = np.where(y < midpos, top * (1 - a) + mid * a, mid * (1 - b) + bottom * b)
    return np.repeat(c[:, None, :], w, 1).reshape(h, w, 3)


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')


@lru_cache(8)
def vignette(strength=0.75):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.58)) ** 2)
    a = np.clip((d - 0.55) / 0.75, 0, 1) ** 1.6 * strength
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return im


@lru_cache(4)
def ink_bg(seed=1, tint=(26, 22, 20), warm=(60, 40, 26)):
    n = fnoise(W, H, seed, 6, 3)
    base = grad_bg((8, 8, 10), (16, 13, 12))
    t = np.array(tint, np.float32); wm = np.array(warm, np.float32)
    arr = base + n[..., None] * t * 0.9
    # 中央暖光
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((x - W / 2) / 700) ** 2 + ((y - H * 0.45) / 900) ** 2))
    arr += g[..., None] * wm * 0.55
    return to_img(arr)


@lru_cache(4)
def paper_tex(seed=3):
    n = fnoise(W, H, seed, 6, 6)
    return n


# ───────── 粒子 ─────────
@lru_cache(64)
def dot_sprite(r, col, core=1.0):
    s = int(r * 4) + 2
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) - (s - 1) / 2
    d = np.sqrt(x * x + y * y) / r
    a = np.exp(-d * d * 1.6) * 0.75 + np.clip(1 - d * 1.8, 0, 1) * core
    a = np.clip(a, 0, 1)
    im = Image.new('RGBA', (s, s), col + (0,))
    im.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return im


class Field:
    """确定性粒子场：位置由 t 解析计算，可分块并行渲染"""

    def __init__(self, n, seed, box=(0, 0, W, H), vel=((-10, 10), (-60, -20)), size=(1.5, 4), cols=(ORANGE,), flicker=True):
        r = np.random.RandomState(seed)
        self.n = n; self.box = box
        self.p = r.rand(n, 2); self.v = np.c_[r.uniform(*vel[0], n), r.uniform(*vel[1], n)]
        self.s = r.uniform(*size, n); self.ph = r.rand(n) * 6.28; self.c = r.randint(0, len(cols), n)
        self.cols = cols; self.fl = flicker

    def draw(self, cv, t, a=1.0, sway=12):
        x0, y0, x1, y1 = self.box; bw, bh = x1 - x0, y1 - y0
        xs = x0 + ((self.p[:, 0] * bw + self.v[:, 0] * t + sway * np.sin(t * 0.7 + self.ph)) % bw)
        ys = y0 + ((self.p[:, 1] * bh + self.v[:, 1] * t) % bh)
        al = (0.55 + 0.45 * np.sin(t * 3 + self.ph * 3)) if self.fl else np.ones(self.n)
        for i in range(self.n):
            aa = a * al[i]
            if aa < 0.05: continue
            sp = dot_sprite(round(self.s[i] * 2) / 2, self.cols[self.c[i]])
            put(cv, sp, xs[i], ys[i], aa)


# ───────── 几何 ─────────
def bez(p0, p1, p2, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(lambda p: np.array(p, np.float32), (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def arrow_poly(pts, w0=46, w1=30, head=90, headw=110):
    """沿折线的粗箭头多边形（含箭头）"""
    pts = np.asarray(pts, np.float32)
    if len(pts) < 2: return None
    seg = np.diff(pts, axis=0); L = np.sqrt((seg ** 2).sum(1)); tot = L.sum()
    if tot < 4: return None
    # 截掉箭头长度
    cum = np.r_[0, np.cumsum(L)]
    hl = min(head, tot * 0.45)
    keep = cum <= tot - hl
    body = pts[keep]
    # 箭头底点
    k = np.searchsorted(cum, tot - hl) - 1; k = max(0, min(k, len(seg) - 1))
    f = (tot - hl - cum[k]) / max(L[k], 1e-3)
    base = pts[k] + seg[k] * f
    body = np.vstack([body, base])
    n = len(body)
    left, right = [], []
    for i in range(n):
        if i == 0: dv = body[1] - body[0]
        elif i == n - 1: dv = body[-1] - body[-2]
        else: dv = body[i + 1] - body[i - 1]
        dv = dv / (np.linalg.norm(dv) + 1e-6); nv = np.array([-dv[1], dv[0]])
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        left.append(body[i] + nv * w); right.append(body[i] - nv * w)
    tip = pts[-1]; dv = tip - base; dv = dv / (np.linalg.norm(dv) + 1e-6); nv = np.array([-dv[1], dv[0]])
    poly = left + [base + nv * headw / 2, tip, base - nv * headw / 2] + right[::-1]
    return [tuple(map(float, p)) for p in poly]


def partial(pts, p):
    pts = np.asarray(pts, np.float32)
    seg = np.diff(pts, axis=0); L = np.sqrt((seg ** 2).sum(1)); cum = np.r_[0, np.cumsum(L)]
    tgt = cum[-1] * clamp(p)
    k = np.searchsorted(cum, tgt) - 1; k = max(0, min(k, len(seg) - 1))
    f = (tgt - cum[k]) / max(L[k], 1e-3)
    return np.vstack([pts[:k + 1], pts[k] + seg[k] * f])


def draw_arrow(cv, pts, p, col=RED, a=1.0, w0=46, w1=30, head=90, headw=110):
    if p <= 0.01: return
    pp = partial(pts, p)
    poly = arrow_poly(pp, w0, w1, head * min(1, p * 2), headw * min(1, p * 2))
    if not poly: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.polygon(poly, fill=col + (int(200 * a),))
    g = ov.filter(ImageFilter.GaussianBlur(14))
    cv.alpha_composite(g); cv.alpha_composite(ov)
    d2 = ImageDraw.Draw(cv)
    d2.line(poly + [poly[0]], fill=(255, 200, 170, int(220 * a)), width=3)


def ring(cv, x, y, r, col, a=1.0, w=4):
    ov = Image.new('RGBA', (int(2 * r + 40), int(2 * r + 40)), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov); c = r + 20
    d.ellipse((c - r, c - r, c + r, c + r), outline=col + (255,), width=w)
    ov = glowify(ov, 6, col)
    put(cv, ov, x, y, a)


# ───────── 剪影 ─────────
def soldier(d, x, y, s, col=(8, 8, 10, 255), spear=True, flag=None):
    """简化兵卒剪影：脚在 (x,y)，高约 120*s"""
    h = 120 * s
    d.ellipse((x - 9 * s, y - h, x + 9 * s, y - h + 18 * s), fill=col)
    d.polygon([(x - 16 * s, y - h + 18 * s), (x + 16 * s, y - h + 18 * s), (x + 20 * s, y - h * 0.38), (x - 20 * s, y - h * 0.38)], fill=col)
    d.polygon([(x - 18 * s, y - h * 0.4), (x + 18 * s, y - h * 0.4), (x + 13 * s, y), (x + 4 * s, y), (x, y - h * 0.22), (x - 4 * s, y), (x - 13 * s, y)], fill=col)
    if spear:
        d.line((x + 22 * s, y + 2 * s, x + 30 * s, y - h * 1.55), fill=col, width=max(1, int(3 * s)))
        d.polygon([(x + 30 * s, y - h * 1.55), (x + 26 * s, y - h * 1.45), (x + 34 * s, y - h * 1.45)], fill=col)
    if flag:
        d.line((x - 22 * s, y, x - 22 * s, y - h * 1.9), fill=col, width=max(1, int(3 * s)))
        d.polygon([(x - 22 * s, y - h * 1.9), (x + 30 * s, y - h * 1.82), (x + 22 * s, y - h * 1.55), (x - 22 * s, y - h * 1.5)], fill=flag)


def bust(kind='bang', size=600, col=(6, 6, 8, 255), rim=None):
    """头肩剪影。bang=戴竹皮冠的中年人；bei=束发少年"""
    S = size
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = S / 2
    hr = S * (0.15 if kind == 'bang' else 0.14)
    hy = S * 0.42
    # 肩
    d.polygon([(cx - S * 0.47, S), (cx - S * 0.40, S * 0.74), (cx - S * 0.12, S * 0.62), (cx + S * 0.12, S * 0.62), (cx + S * 0.40, S * 0.74), (cx + S * 0.47, S)], fill=col)
    d.rectangle((cx - hr * 0.45, hy + hr * 0.6, cx + hr * 0.45, S * 0.66), fill=col)  # 颈
    d.ellipse((cx - hr * 0.92, hy - hr * 1.1, cx + hr * 0.92, hy + hr * 1.05), fill=col)
    if kind == 'bang':
        # 长冠（竹皮冠）+ 胡须
        d.polygon([(cx - hr * 0.35, hy - hr * 0.95), (cx + hr * 0.35, hy - hr * 0.95), (cx + hr * 0.55, hy - hr * 2.0), (cx - hr * 0.15, hy - hr * 2.05)], fill=col)
        d.line((cx - hr * 0.9, hy - hr * 0.2, cx - hr * 0.55, hy + hr * 1.0), fill=col, width=int(S * 0.008))
        d.polygon([(cx - hr * 0.5, hy + hr * 0.7), (cx + hr * 0.5, hy + hr * 0.7), (cx, hy + hr * 1.6)], fill=col)
        # 交领
        d.polygon([(cx - S * 0.3, S * 0.72), (cx, S * 0.9), (cx + S * 0.3, S * 0.72), (cx + S * 0.27, S * 0.78), (cx, S * 0.95), (cx - S * 0.27, S * 0.78)], fill=(30, 18, 14, 255))
    else:
        d.ellipse((cx - hr * 0.38, hy - hr * 1.65, cx + hr * 0.38, hy - hr * 0.9), fill=col)  # 发髻
        d.polygon([(cx - S * 0.3, S * 0.72), (cx, S * 0.88), (cx + S * 0.3, S * 0.72), (cx + S * 0.27, S * 0.78), (cx, S * 0.93), (cx - S * 0.27, S * 0.78)], fill=(26, 20, 14, 255))
    if rim:
        a = im.getchannel('A')
        sh = ImageChops.offset(a, -int(S * 0.012), int(S * 0.006))
        edge = ImageChops.subtract(a, sh).filter(ImageFilter.GaussianBlur(S * 0.004))
        rl = Image.new('RGBA', (S, S), rim + (0,)); rl.putalpha(edge.point(lambda v: min(255, v * 3)))
        im = glowify(im, int(S * 0.02), rim, 0.5)
        pad = (im.width - S) // 2
        im.alpha_composite(rl, (pad, pad))
    return im


def house(d, x, y, s, col):
    d.rectangle((x - 70 * s, y - 60 * s, x + 70 * s, y), fill=col)
    d.polygon([(x - 100 * s, y - 55 * s), (x, y - 120 * s), (x + 100 * s, y - 55 * s)], fill=col)


def tree_sil(d, x, y, s, col, seed=0):
    r = random.Random(seed)
    d.line((x, y, x, y - 80 * s), fill=col, width=max(2, int(8 * s)))
    for k in range(7):
        rx = x + r.uniform(-50, 50) * s; ry = y - (80 + r.uniform(10, 90)) * s; rr = r.uniform(28, 48) * s
        d.ellipse((rx - rr, ry - rr, rx + rr, ry + rr), fill=col)


# ───────── 地图 ─────────
GEO = {
    'coast': [(117.6, 39.6), (118.6, 39.2), (119.3, 39.4), (120.5, 40.3), (121.8, 40.8), (121.2, 39.4), (122.2, 39.0), (121.6, 38.8),
              (120.8, 38.0), (119.0, 37.3), (118.9, 37.9), (118.0, 38.2), (117.6, 38.6), (117.6, 39.6)],
    'shandong': [(118.9, 37.25), (119.6, 37.15), (120.7, 37.8), (122.5, 37.4), (122.2, 36.9), (120.7, 36.4), (119.5, 35.6), (119.2, 34.8),
                 (120.3, 34.3), (120.9, 32.6), (121.9, 31.7), (121.9, 30.9), (122.6, 30.0), (121.5, 28.5)],
    'hehuang': [(104.0, 35.9), (105.5, 36.2), (106.5, 37.5), (107.0, 39.5), (109.8, 40.6), (111.0, 40.3), (110.6, 38.5), (110.4, 36.0), (110.3, 34.65), (111.5, 34.8),
                (112.5, 34.85), (113.5, 34.95), (114.5, 35.4), (115.3, 36.0), (116.0, 37.0), (116.8, 38.0), (117.6, 38.7)],
    'huai': [(113.3, 32.4), (114.4, 32.4), (115.4, 32.45), (116.4, 32.6), (117.4, 32.95), (118.5, 33.05), (119.2, 33.6), (120.2, 33.9)],
    'si': [(117.3, 35.6), (117.0, 35.4), (116.95, 35.0), (117.05, 34.7), (117.2, 34.27), (117.7, 34.0), (118.2, 33.7), (118.6, 33.3)],
    'wei': [(105.5, 34.6), (107.2, 34.35), (108.7, 34.3), (109.6, 34.5), (110.3, 34.62)],
    'han': [(106.5, 33.1), (108.0, 32.8), (109.5, 32.7), (111.0, 32.5), (112.1, 32.0), (113.3, 31.0), (114.2, 30.6)],
    'jiang': [(105.0, 29.5), (108.0, 30.5), (110.5, 30.8), (111.5, 30.4), (112.5, 29.6), (113.5, 29.9), (114.3, 30.6), (116.0, 29.8), (117.5, 30.8), (118.6, 31.7), (119.9, 32.2), (121.0, 31.8)],
    'qinling': [(106.5, 33.9), (107.8, 33.85), (109.0, 33.9), (110.2, 34.1), (111.3, 34.0)],
    'taihang': [(113.5, 35.3), (113.8, 36.3), (114.0, 37.3), (114.4, 38.3), (114.9, 39.3)],
    'tai': [(116.6, 36.0), (117.3, 36.3), (118.0, 36.2)],
    'sang': [(113.2, 39.0), (114.5, 39.8), (115.5, 40.0), (116.3, 39.6), (117.0, 39.3), (117.6, 39.0)],
}
PLACE = {
    '咸阳': (108.71, 34.33), '沛': (116.93, 34.72), '丰': (116.60, 34.69), '芒砀山': (116.35, 34.20), '大泽乡': (117.15, 33.55),
    '陈': (114.88, 33.73), '胡陵': (116.75, 35.00), '方与': (116.35, 35.05), '彭城': (117.19, 34.26), '相': (116.80, 33.90),
    '洛阳': (112.45, 34.68), '涿县': (115.97, 39.48), '中山': (114.99, 38.52), '长安': (108.94, 34.27), '蕲': (117.05, 33.45),
}


class Proj:
    def __init__(self, lon0, lon1, lat_c, rect=(0, 420, W, 1380)):
        self.lon0, self.lon1 = lon0, lon1; self.rect = rect
        x0, y0, x1, y1 = rect
        self.sx = (x1 - x0) / (lon1 - lon0)
        self.sy = self.sx / math.cos(math.radians(35)) * 0.98
        self.lat_c = lat_c; self.yc = (y0 + y1) / 2

    def __call__(self, lon, lat):
        return (self.rect[0] + (lon - self.lon0) * self.sx, self.yc - (lat - self.lat_c) * self.sy)

    def lerp(self, o, k):
        p = Proj.__new__(Proj)
        p.lon0 = self.lon0 + (o.lon0 - self.lon0) * k; p.lon1 = self.lon1 + (o.lon1 - self.lon1) * k
        p.lat_c = self.lat_c + (o.lat_c - self.lat_c) * k; p.rect = self.rect
        p.sx = (p.rect[2] - p.rect[0]) / (p.lon1 - p.lon0); p.sy = p.sx / math.cos(math.radians(35)) * 0.98; p.yc = self.yc
        return p


@lru_cache(4)
def map_tex():
    n = fnoise(W, H, 11, 6, 4)
    n2 = fnoise(W, H, 12, 3, 2)
    base = np.stack([30 + 26 * n + 10 * n2, 26 + 20 * n + 8 * n2, 20 + 14 * n + 6 * n2], -1)
    return base.astype(np.float32)


def draw_map(cv, P, a=1.0, rivers=('hehuang', 'huai', 'si', 'wei', 'jiang', 'han', 'sang'), river_a=1.0):
    """地图底：海、海岸、河流。P 为投影"""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # 海：海岸线以东
    sea = [P(*p) for p in GEO['shandong']]
    poly = sea + [(W + 400, H + 400), (W + 400, -400)]
    d.polygon(poly, fill=(10, 20, 30, int(235 * a)))
    bo = [P(*p) for p in GEO['coast']]
    d.polygon(bo, fill=(10, 20, 30, int(235 * a)))
    d.line(sea, fill=(120, 140, 150, int(150 * a)), width=3, joint='curve')
    d.line(bo, fill=(120, 140, 150, int(150 * a)), width=3, joint='curve')
    for r in rivers:
        pts = [P(*p) for p in GEO[r]]
        w = 7 if r in ('hehuang', 'jiang') else 4
        d.line(pts, fill=(70, 120, 140, int(70 * a * river_a)), width=w + 8, joint='curve')
        d.line(pts, fill=(120, 170, 190, int(170 * a * river_a)), width=max(2, w - 2), joint='curve')
    for rg in ('qinling', 'taihang', 'tai'):
        pts = [P(*p) for p in GEO[rg]]
        for k in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            for j in range(6):
                f = j / 6; x = x0 + (x1 - x0) * f; y = y0 + (y1 - y0) * f; s = 13
                d.polygon([(x - s, y + s * 0.6), (x, y - s), (x + s, y + s * 0.6)], outline=(140, 120, 90, int(120 * a)), fill=(70, 58, 42, int(110 * a)))
    cv.alpha_composite(ov)


def city(cv, P, name, col=GOLD, a=1.0, r=11, size=40, dx=0, dy=-46, pulse=0.0, t=0.0, lab=True, sub=None):
    x, y = P(*PLACE[name])
    if pulse:
        k = (t * 0.8) % 1
        ring(cv, x, y, r + 50 * k, col, a * (1 - k) * pulse, 3)
    put(cv, dot_sprite(r, col, 1.0), x, y, a)
    d = ImageDraw.Draw(cv)
    d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=(255, 250, 240, int(255 * a)))
    if lab:
        put(cv, txt(name, size, 'black', col if col != QIN else QIN2, 3, (0, 0, 0), glow=6, gcol=(0, 0, 0)), x + dx, y + dy, a)
    if sub:
        put(cv, txt(sub, int(size * 0.62), 'sans', GREY, 2), x + dx, y + dy + size * 0.95, a)
    return x, y
