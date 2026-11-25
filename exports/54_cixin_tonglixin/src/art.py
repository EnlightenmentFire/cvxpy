# -*- coding: utf-8 -*-
"""画面基础：字体、宣纸、墨、发光、脑示意、文字排版。"""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1080, 1920
FONT_DIR = "/tmp/claude-0/work/fonts"

PAPER = (238, 232, 218)
INK = (30, 29, 31)
INK_SOFT = (78, 74, 70)
NIGHT = (14, 20, 30)
WARM = (214, 96, 72)      # 共情痛苦网络
COOL = (226, 182, 92)     # 慈悲网络（暖金，强调温暖）
JADE = (96, 160, 140)
BLUE = (92, 128, 186)
SEAL = (170, 46, 38)


@functools.lru_cache(maxsize=256)
def font(kind="sans", size=48, wght=500):
    path = {"sans": "notosanssc.ttf", "serif": "notoserifsc.ttf", "tc": "notoseriftc.ttf"}[kind]
    f = ImageFont.truetype(f"{FONT_DIR}/{path}", size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f


def rng(seed):
    return np.random.default_rng(seed)


@functools.lru_cache(maxsize=8)
def paper(seed=1, base=PAPER, w=W, h=H):
    r = rng(seed)
    a = np.zeros((h, w, 3), np.float32) + np.array(base, np.float32)
    # 低频云纹 + 纤维
    lo = r.normal(0, 1, (h // 40 + 2, w // 40 + 2)).astype(np.float32)
    lo = np.array(Image.fromarray(((lo - lo.min()) / (np.ptp(lo) + 1e-6) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 - .5
    hi = r.normal(0, 1, (h, w)).astype(np.float32)
    a += lo[..., None] * 14 + hi[..., None] * 3.0
    # 暗角
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt(((xx - w / 2) / (w * .75)) ** 2 + ((yy - h / 2) / (h * .7)) ** 2)
    a *= (1 - 0.16 * np.clip(d, 0, 1.4) ** 2)[..., None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # 纤维
    dr = ImageDraw.Draw(img, "RGBA")
    for _ in range(900):
        x, y = r.uniform(0, w), r.uniform(0, h)
        L, ang = r.uniform(6, 30), r.uniform(0, math.pi)
        dr.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=(120, 105, 85, int(r.uniform(8, 22))), width=1)
    return img


@functools.lru_cache(maxsize=8)
def night_bg(seed=2, top=(10, 16, 26), bot=(20, 28, 42)):
    r = rng(seed)
    t = np.linspace(0, 1, H)[:, None, None]
    a = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    a = np.repeat(a, W, axis=1)
    a += r.normal(0, 2.0, (H, W, 1)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * .7)) ** 2 + ((yy - H * .45) / (H * .6)) ** 2)
    a *= (1 - 0.35 * np.clip(d, 0, 1.3) ** 2)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def ink_layer(draw_fn, blur=2.0, bleed=6, seed=0, alpha=1.0, color=INK):
    """draw_fn(ImageDraw L-mode) 画墨形状；返回 RGBA 墨层（带晕染边）。"""
    m = Image.new("L", (W, H), 0)
    draw_fn(ImageDraw.Draw(m))
    core = m.filter(ImageFilter.GaussianBlur(blur))
    halo = m.filter(ImageFilter.GaussianBlur(bleed))
    r = rng(seed)
    noise = Image.fromarray((r.uniform(0.75, 1.0, (H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    a = ImageChops.multiply(ImageChops.lighter(core, halo.point(lambda v: int(v * 0.45))), noise)
    if alpha < 1:
        a = a.point(lambda v: int(v * alpha))
    lay = Image.new("RGBA", (W, H), color + (0,))
    lay.putalpha(a)
    return lay


def glow(size, color, radius, strength=1.0):
    """返回 RGBA 圆形柔光（size 方形）。"""
    s = size
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx - s / 2) ** 2 + (yy - s / 2) ** 2) / radius
    a = np.exp(-d ** 2 * 2.2) * 255 * strength
    img = np.zeros((s, s, 4), np.uint8)
    img[..., :3] = color
    img[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(img)


def blob(cx, cy, rx, ry, color, strength=1.0, rot=0):
    """在全幅 RGBA 上画一个椭圆形柔光斑。"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    c, s = math.cos(rot), math.sin(rot)
    X, Y = (xx - cx) * c + (yy - cy) * s, -(xx - cx) * s + (yy - cy) * c
    d = (X / rx) ** 2 + (Y / ry) ** 2
    a = np.exp(-d * 1.6) * 255 * strength
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = color
    img[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(img)


def fade(img, a):
    """RGBA 整体乘透明度。"""
    if a >= 0.999:
        return img
    im = img.copy()
    al = im.getchannel("A").point(lambda v: int(v * max(0, a)))
    im.putalpha(al)
    return im


def over(base, lay, a=1.0, xy=(0, 0)):
    if a <= 0.001:
        return base
    lay = fade(lay, a)
    if lay.size == base.size and xy == (0, 0):
        return Image.alpha_composite(base, lay)
    base.alpha_composite(lay, dest=(int(xy[0]), int(xy[1])))
    return base


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, t0, d=0.6):
    return ease((t - t0) / d) if d > 0 else float(t >= t0)


# ---------- 文字 ----------
def text_size(s, f):
    b = f.getbbox(s)
    return b[2] - b[0], b[3] - b[1]


def _tokens(s):
    import re as _re
    return _re.findall(r"[A-Za-z0-9’'\-–.,:;()“”\"/]+ ?|\n|.", s)


def wrap(s, f, maxw):
    lines, cur = [], ""
    for tok in _tokens(s):
        if tok == "\n":
            lines.append(cur.rstrip()); cur = ""; continue
        if text_size((cur + tok).rstrip(), f)[0] > maxw and cur:
            if tok in "，。、；：！？”》）":
                cur += tok; lines.append(cur.rstrip()); cur = ""; continue
            lines.append(cur.rstrip()); cur = tok.lstrip()
        else:
            cur += tok
    if cur:
        lines.append(cur.rstrip())
    return lines


def text_layer(s, f, fill, maxw=900, align="center", x=W // 2, y=0, spacing=1.45, shadow=None, stroke=0, stroke_fill=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lines = wrap(s, f, maxw)
    lh = int(f.size * spacing)
    for i, ln in enumerate(lines):
        tw, _ = text_size(ln, f)
        xx = x - tw // 2 if align == "center" else x
        yy = y + i * lh
        if shadow:
            d.text((xx + 2, yy + 3), ln, font=f, fill=shadow)
        d.text((xx, yy), ln, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if shadow:
        pass
    return lay, len(lines) * lh


def vtext_layer(s, f, fill, x, y, col_gap=1.5, line_gap=1.12, cols_max=None):
    """竖排：s 中 '\n' 分列，从右往左。x 为最右列中心。"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cols = s.split("\n")
    for ci, col in enumerate(cols):
        cx = x - ci * int(f.size * col_gap)
        for ri, ch in enumerate(col):
            tw, th = text_size(ch, f)
            b = f.getbbox(ch)
            if ch in "，。、；：":
                d.text((cx + f.size * 0.08 - b[0], y + ri * int(f.size * line_gap) - f.size * 0.35 - b[1] + f.size * 0.1), ch, font=f, fill=fill)
            else:
                d.text((cx - tw / 2 - b[0], y + ri * int(f.size * line_gap)), ch, font=f, fill=fill)
    return lay


def rounded(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def chip(text, x, y, color=(170, 46, 38), fg=(250, 246, 238), size=30):
    f = font("sans", size, 600)
    tw, th = text_size(text, f)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pad = 16
    d.rounded_rectangle((x, y, x + tw + pad * 2, y + size + 22), 10, fill=color + (230,))
    d.text((x + pad, y + 8 - f.getbbox(text)[1] + 2), text, font=f, fill=fg)
    return lay


def seal(text, x, y, size=70):
    """朱印（方章，白文）。"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x, y, x + size, y + size), 6, fill=SEAL + (220,))
    f = font("serif", int(size * 0.38), 800)
    n = len(text)
    if n == 4:
        pos = [(1, 0), (1, 1), (0, 0), (0, 1)]
        for ch, (c, r) in zip(text, pos):
            cx = x + size * (0.27 + 0.46 * c); cy = y + size * (0.27 + 0.46 * r)
            tw, th = text_size(ch, f); b = f.getbbox(ch)
            d.text((cx - tw / 2 - b[0], cy - th / 2 - b[1]), ch, font=f, fill=(250, 240, 230))
    else:
        tw, th = text_size(text, f); b = f.getbbox(text)
        d.text((x + size / 2 - tw / 2 - b[0], y + size / 2 - th / 2 - b[1]), text, font=f, fill=(250, 240, 230))
    return lay


# ---------- 脑示意 ----------
def brain_outline(cx, cy, s, view="medial"):
    """返回脑外轮廓点（大脑）+ 小脑 + 脑干，单位像素。s ~ 半宽。"""
    pts = []
    for i in range(240):
        a = 2 * math.pi * i / 240
        # 基本：前圆后略尖、底部较平
        rx = s * (1.0 + 0.05 * math.cos(a))
        ry = s * 0.72 * (1 + 0.08 * math.sin(2 * a))
        x = cx + rx * math.cos(a)
        y = cy - ry * math.sin(a) * (0.86 if math.sin(a) < 0 else 1.0)
        # 颞叶下垂（偏前下）
        if view == "lateral":
            k = math.exp(-((a - 3.75) ** 2) / 0.12)
            y += s * 0.16 * k
        pts.append((x, y))
    # 注意：x 轴正向为后（枕叶在右）→ 翻转使额叶在左
    pts = [(2 * cx - x, y) for x, y in pts]
    cereb = (cx + s * 0.42, cy + s * 0.38, s * 0.36, s * 0.22)  # 中心、半径
    stem = [(cx + s * 0.08, cy + s * 0.45), (cx + s * 0.26, cy + s * 0.45), (cx + s * 0.30, cy + s * 0.95), (cx + s * 0.14, cy + s * 0.95)]
    return pts, cereb, stem


@functools.lru_cache(maxsize=8)
def brain_base(cx, cy, s, view="medial", dark=True, seed=3):
    """返回 RGBA 脑示意底图（线描 + 半透明填充 + 沟回）。"""
    pts, (ccx, ccy, crx, cry), stem = brain_outline(cx, cy, s, view)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    line = (205, 210, 222, 200) if dark else (60, 56, 52, 210)
    fill = (40, 50, 68, 150) if dark else (225, 216, 198, 160)
    d.polygon(stem, fill=fill, outline=line)
    d.ellipse((ccx - crx, ccy - cry, ccx + crx, ccy + cry), fill=fill, outline=line, width=3)
    for k in range(5):
        yy = ccy - cry * 0.6 + k * cry * 0.3
        d.arc((ccx - crx * 0.9, yy - cry * 0.4, ccx + crx * 0.9, yy + cry * 0.4), 200, 340, fill=line[:3] + (90,), width=2)
    d.polygon(pts, fill=fill)
    # 沟回：脑内随机波纹（裁剪在轮廓内）
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    r = rng(seed)
    for _ in range(46):
        x0, y0 = r.uniform(cx - s, cx + s), r.uniform(cy - s * .7, cy + s * .7)
        ang = r.uniform(0, math.pi)
        seg = []
        L = r.uniform(s * 0.25, s * 0.6)
        for j in range(30):
            u = j / 29
            px = x0 + (u - .5) * L * math.cos(ang) + math.sin(u * 9 + x0) * 10 * math.sin(ang)
            py = y0 + (u - .5) * L * math.sin(ang) + math.sin(u * 9 + y0) * 10 * math.cos(ang)
            seg.append((px, py))
        gd.line(seg, fill=line[:3] + (70,), width=2, joint="curve")
    if view == "medial":
        # 胼胝体（弧形带）
        cc = []
        for j in range(60):
            a = math.pi * (0.1 + 0.8 * j / 59)
            cc.append((cx - s * 0.05 - s * 0.42 * math.cos(a), cy + s * 0.05 - s * 0.18 * math.sin(a)))
        gd.line(cc, fill=line[:3] + (150,), width=14, joint="curve")
    g.putalpha(ImageChops.multiply(g.getchannel("A"), mask))
    lay = Image.alpha_composite(lay, g)
    d = ImageDraw.Draw(lay)
    d.line(pts + [pts[0]], fill=line, width=4, joint="curve")
    return lay


def label_line(d, p0, p1, text, f, color, anchor_left=True):
    d.line([p0, p1], fill=color, width=2)
    d.ellipse((p0[0] - 6, p0[1] - 6, p0[0] + 6, p0[1] + 6), fill=color)
    tw, th = text_size(text, f)
    x = p1[0] + 10 if anchor_left else p1[0] - tw - 10
    d.text((x, p1[1] - f.size * 0.62), text, font=f, fill=color)
