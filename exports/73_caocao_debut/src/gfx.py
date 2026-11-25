# -*- coding: utf-8 -*-
"""Drawing primitives: fonts, text, cards, backgrounds, glow. 1080x1920."""
import math, functools, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 25

SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
SANS_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANS_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
KAI = "/usr/share/fonts/truetype/arphic/ukai.ttc"

# colour tokens
GOLD = (222, 184, 104)
GOLD_L = (245, 222, 160)
IVORY = (242, 234, 214)
INK = (10, 10, 14)
CAO = (20, 18, 16)          # 玄黑
PURPLE = (112, 62, 140)     # 宦官暗紫
PURPLE_L = (170, 120, 200)
WHITE = (236, 238, 242)     # 清流素白
YUAN = (196, 160, 82)       # 袁绍土黄
LIU = (200, 52, 40)         # 刘氏朱红
COLD = (120, 140, 160)      # 冷蓝灰
RED = (196, 60, 48)
GREY = (160, 160, 168)

LV_COL = {"三國志正文": (222, 184, 104), "裴注引書": (214, 160, 110), "後漢書": (150, 180, 200),
          "資治通鑑": (170, 170, 200), "三國演義": (196, 70, 60)}
LV_NAME = {"三國志正文": "①《三国志》正文", "裴注引書": "②裴注引书", "後漢書": "③《后汉书》",
           "資治通鑑": "④《资治通鉴》", "三國演義": "⑤《三国演义》"}


@functools.lru_cache(maxsize=256)
def font(path, size, idx=None):
    if idx is None:
        idx = {SERIF_B: 3, SERIF_R: 3, SANS_B: 2, SANS_R: 2, KAI: 0}.get(path, 0)
    return ImageFont.truetype(path, size, index=idx)


def sc_font(path, size):   # simplified-Chinese face
    return font(path, size, 2 if "Noto" in path else 0)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def clamp01(x):
    return min(1.0, max(0.0, x))


def wrap(text, fnt, maxw):
    """CJK wrap; avoid line-start punctuation."""
    lines, cur = [], ""
    NOSTART = "，。、；：？！」』）》"
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        t = cur + ch
        if fnt.getlength(t) > maxw and cur:
            if ch in NOSTART:
                cur = t; continue
            lines.append(cur); cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def text_img(text, fnt, fill, maxw=None, spacing=1.35, stroke=0, stroke_fill=(0, 0, 0), align="left", shadow=None):
    lines = wrap(text, fnt, maxw) if maxw else text.split("\n")
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * spacing)
    wmax = int(max(fnt.getlength(l) for l in lines)) + 2 * stroke + 8
    h = lh * len(lines) + 2 * stroke + 8
    im = Image.new("RGBA", (wmax, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = fnt.getlength(l)
        x = stroke + 4 + (0 if align == "left" else (wmax - 2 * stroke - 8 - lw) / (2 if align == "center" else 1))
        d.text((x, stroke + 4 + i * lh), l, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        a = im.split()[3].filter(ImageFilter.GaussianBlur(shadow))
        sh.putalpha(a.point(lambda v: min(255, int(v * 1.4))))
        sh.alpha_composite(im)
        im = sh
    return im


def with_alpha(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    al = im.split()[3].point(lambda v: int(v * a))
    im.putalpha(al)
    return im


def paste(base, im, x, y, a=1.0):
    if a <= 0.003:
        return
    im = with_alpha(im, a)
    x, y = int(round(x)), int(round(y))
    base.alpha_composite(im, (max(0, x), max(0, y)),
                         (max(0, -x), max(0, -y)))


def paste_c(base, im, cx, cy, a=1.0):
    paste(base, im, cx - im.width / 2, cy - im.height / 2, a)


def glow(im, r=18, gain=1.6):
    g = im.filter(ImageFilter.GaussianBlur(r))
    a = g.split()[3].point(lambda v: min(255, int(v * gain)))
    g.putalpha(a)
    g.alpha_composite(im)
    return g


def rrect(size, r, fill, outline=None, width=2):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=fill, outline=outline, width=width)
    return im


def noise_tex(w, h, seed=0, scale=6, octaves=4):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale * 2 ** o))
        sm = rng.random((s * h // w + 2, s + 2)).astype(np.float32)
        im = Image.fromarray((sm * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(im, np.float32) / 255
        tot += amp; amp *= 0.5
    return acc / tot


@functools.lru_cache(maxsize=8)
def dark_bg(seed=1, top=(16, 16, 22), bot=(6, 6, 8), tint=(0, 0, 0)):
    y = np.linspace(0, 1, H)[:, None, None]
    base = np.array(top, np.float32) * (1 - y) + np.array(bot, np.float32) * y
    n = noise_tex(W // 4, H // 4, seed)[..., None]
    n = np.asarray(Image.fromarray((n[..., 0] * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
    base = base * (0.85 + 0.3 * n) + np.array(tint, np.float32) * n
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
    base *= np.clip(1.15 - 0.55 * v, 0.35, 1)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


def parchment_dark(seed=3):
    """dark map paper"""
    n = noise_tex(W // 3, H // 3, seed, scale=5)
    n2 = noise_tex(W // 3, H // 3, seed + 9, scale=24, octaves=2)
    n = 0.7 * n + 0.3 * n2
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
    c0 = np.array([30, 26, 20], np.float32); c1 = np.array([58, 48, 34], np.float32)
    img = c0 + (c1 - c0) * n[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    v = ((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.55)) ** 2
    img *= np.clip(1.2 - 0.6 * v, 0.3, 1)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


def pill(text, fg, bg=None, size=30, outline=None, pad=(18, 6), fnt=None):
    f = fnt or sc_font(SANS_B, size)
    tw = int(f.getlength(text)); asc, desc = f.getmetrics()
    w, h = tw + 2 * pad[0], asc + desc + 2 * pad[1]
    im = rrect((w, h), h // 2, bg or (0, 0, 0, 0), outline=outline, width=2)
    ImageDraw.Draw(im).text((pad[0], pad[1] - 2), text, font=f, fill=fg)
    return im
