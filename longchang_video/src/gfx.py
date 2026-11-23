"""绘图基础：文字精灵、合成、缓动、噪声。全片 1920x1080，线性叠加在 float32 sRGB 画布上。"""
import functools
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
FONT_DIR = os.environ.get('LC_FONTS', '')

# ── 颜色（sRGB 0..1）──
def rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return np.array([int(hexstr[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


INK = rgb('#06080b')        # 底色
PAPER = rgb('#e9e3d6')      # 正文
BRIGHT = rgb('#f6f1e6')     # 引文
GREY = rgb('#8e949d')       # 白话字幕 / 次要
DIM = rgb('#5d636c')        # 角标
EMBER = rgb('#d98f4e')      # 解读
COOL = rgb('#86a9bd')       # 理论
FACT = rgb('#b8b2a2')       # 史实

FONTS = {
    'serif-xl': 'SourceHanSerifSC-ExtraLight.otf',
    'serif-l': 'SourceHanSerifSC-Light.otf',
    'serif': 'SourceHanSerifSC-Regular.otf',
    'serif-m': 'SourceHanSerifSC-Medium.otf',
    'serif-sb': 'SourceHanSerifSC-SemiBold.otf',
    'serif-b': 'SourceHanSerifSC-Bold.otf',
    'sans-xl': 'SourceHanSansSC-ExtraLight.otf',
    'sans-l': 'SourceHanSansSC-Light.otf',
    'sans': 'SourceHanSansSC-Normal.otf',
    'sans-r': 'SourceHanSansSC-Regular.otf',
}


@functools.lru_cache(maxsize=None)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, FONTS[name]), size)


# ── 缓动 ──
def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease(x):
    x = clamp01(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ramp(t, t0, t1):
    """t0 -> t1 之间从 0 平滑升到 1。"""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return float(smooth((t - t0) / (t1 - t0)))


def window(t, t_in, t_out, fin=0.6, fout=0.5):
    """淡入淡出包络：t_in 开始淡入，t_out 淡出结束。"""
    return float(smooth((t - t_in) / fin) * smooth((t_out - t) / fout))


# ── 文字 ──
PUNCT_NARROW = set('，。、；：？！”’）》」』')
PUNCT_OPEN = set('“‘（《「『')


def _line_width(line, f, spacing):
    w = 0.0
    for ch in line:
        w += f.getlength(ch) + spacing
    return w - spacing if line else 0.0


@functools.lru_cache(maxsize=4096)
def text_sprite(text, fontname='serif', size=54, color=(0.91, 0.89, 0.84), spacing=0.0, line_gap=1.6,
                align='center', shadow=0.0):
    """渲染（可多行）文字为预乘 alpha 的 RGBA float32 精灵。返回 (rgba, w, h)。

    shadow>0 时在字后加一层柔和暗影，压在地图上时保证可读。
    """
    f = font(fontname, size)
    lines = text.split('\n')
    widths = [_line_width(l, f, spacing) for l in lines]
    lh = int(round(size * line_gap))
    pad = int(size * 0.6) + (int(shadow * 3) if shadow else 0)
    w = int(max(widths) + 2 * pad) + 2
    h = int(lh * (len(lines) - 1) + size * 1.3 + 2 * pad)
    img = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        if align == 'center':
            x = (w - widths[i]) / 2
        elif align == 'right':
            x = w - pad - widths[i]
        else:
            x = pad
        y = pad + i * lh
        for ch in line:
            d.text((x, y), ch, font=f, fill=255)
            x += f.getlength(ch) + spacing
    a = np.asarray(img, np.float32) / 255.0
    out = np.zeros((h, w, 4), np.float32)
    col = np.asarray(color, np.float32)
    if shadow:
        sh = cv2.GaussianBlur(a, (0, 0), shadow)
        sh = np.clip(sh * 2.2, 0, 1) * 0.85
        # 暗影在下（预乘，颜色为黑），文字在上
        out[..., 3] = sh
        out[..., :3] = 0
        out[..., :3] = out[..., :3] * (1 - a[..., None]) + col * a[..., None]
        out[..., 3] = sh * (1 - a) + a
    else:
        out[..., :3] = col * a[..., None]
        out[..., 3] = a
    return out, w, h


def blit(canvas, sprite, cx, cy, alpha=1.0, anchor='c'):
    """把预乘 RGBA 精灵贴到画布上。anchor: 'c' 中心, 'l' 左中, 'r' 右中, 'tl' 左上。整数像素对位。"""
    if alpha <= 0.003:
        return
    sh, sw = sprite.shape[:2]
    if anchor == 'c':
        x0, y0 = int(round(cx - sw / 2)), int(round(cy - sh / 2))
    elif anchor == 'l':
        x0, y0 = int(round(cx)), int(round(cy - sh / 2))
    elif anchor == 'r':
        x0, y0 = int(round(cx - sw)), int(round(cy - sh / 2))
    else:
        x0, y0 = int(round(cx)), int(round(cy))
    Hc, Wc = canvas.shape[:2]
    xa, ya = max(x0, 0), max(y0, 0)
    xb, yb = min(x0 + sw, Wc), min(y0 + sh, Hc)
    if xa >= xb or ya >= yb:
        return
    s = sprite[ya - y0:yb - y0, xa - x0:xb - x0]
    a = s[..., 3:4] * alpha
    region = canvas[ya:yb, xa:xb]
    region *= (1 - a)
    region += s[..., :3] * alpha


def blit_blur(canvas, sprite, cx, cy, alpha, blur, anchor='c'):
    """淡入时带一点由虚到实。"""
    if blur > 0.4:
        sprite = cv2.GaussianBlur(sprite, (0, 0), blur)
    blit(canvas, sprite, cx, cy, alpha, anchor)


def add_glow(canvas, x, y, radius, color, intensity):
    """加性光点（高斯）。"""
    if intensity <= 0.002:
        return
    r = int(radius * 3)
    x0, y0 = int(round(x)) - r, int(round(y)) - r
    Hc, Wc = canvas.shape[:2]
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + 2 * r + 1, Wc), min(y0 + 2 * r + 1, Hc)
    if xa >= xb or ya >= yb:
        return
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radius * radius))
    canvas[ya:yb, xa:xb] += g[..., None] * (np.asarray(color, np.float32) * intensity)


# ── 噪声 ──
def value_noise(h, w, cell, rng, octaves=4, persistence=0.5):
    """平滑分形噪声，输出 0..1。cell 是最粗一层的格子尺寸（像素）。"""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        gh, gw = h // c + 3, w // c + 3
        g = rng.random((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (gw * c, gh * c), interpolation=cv2.INTER_CUBIC)[c:c + h, c:c + w]
        out += up * amp
        tot += amp
        amp *= persistence
    out /= tot
    return out


def noise1d(n, cell, rng, octaves=5, persistence=0.5):
    out = np.zeros(n, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        g = rng.random(n // c + 4).astype(np.float32)
        x = np.arange(n) / c + 1
        i = x.astype(int)
        f = x - i
        f = f * f * (3 - 2 * f)
        out += (g[i] * (1 - f) + g[i + 1] * f) * amp
        tot += amp
        amp *= persistence
    return out / tot


def flicker(t, seed=0.0):
    """火光闪烁：几支不同周期正弦叠加，0.75..1.15 左右。"""
    return float(0.95 + 0.10 * np.sin(t * 7.3 + seed) + 0.06 * np.sin(t * 13.1 + seed * 2.1)
                 + 0.05 * np.sin(t * 2.9 + seed * 0.7) + 0.03 * np.sin(t * 23.7 + seed * 1.3))
