"""画面引擎基础：字体、颜色、渐变、光晕、剪影、竹简、文字、颗粒。全部程序绘制，无外部图片素材。"""
import math, os, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 25
FD = "/usr/share/fonts/opentype/noto/"

# 调色：深色纪录片质感，青铜金 + 朱砂红 + 竹简黄
INK = (10, 9, 8)
GOLD = (214, 172, 92)
GOLD2 = (240, 206, 132)
BRONZE = (150, 108, 58)
RED = (178, 42, 32)
RED2 = (226, 74, 52)
PAPER = (236, 224, 198)
SLIP = (196, 164, 104)
GREY = (120, 116, 108)
BLUE = (72, 98, 128)
NIGHT = (14, 20, 34)
WARM = (255, 176, 82)


@functools.lru_cache(None)
def font(kind="serif", size=40, weight="Bold", tc=False):
    idx = 3 if tc else 2
    f = {"serif": f"NotoSerifCJK-{weight}.ttc", "sans": f"NotoSansCJK-{weight}.ttc"}[kind]
    return ImageFont.truetype(FD + f, size, index=idx)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ramp(t, t0, dur):
    return ease((t - t0) / max(dur, 1e-6))


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


def scale_c(c, k):
    return tuple(int(clamp(v * k, 0, 255)) for v in c)


# ── 背景 ──
@functools.lru_cache(None)
def vgrad(top, bot, w=W, h=H, gamma=1.0):
    y = np.linspace(0, 1, h)[:, None] ** gamma
    a = np.array(top, float)[None, None, :]
    b = np.array(bot, float)[None, None, :]
    arr = a + (b - a) * y[..., None]
    arr = np.broadcast_to(arr, (h, w, 3))
    return Image.fromarray(arr.astype(np.uint8), "RGB")


@functools.lru_cache(None)
def radial_mask(w, h, cx, cy, r, power=2.0):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    m = np.clip(1 - d, 0, 1) ** power
    return Image.fromarray((m * 255).astype(np.uint8), "L")


def glow(img, cx, cy, r, color, strength=1.0, power=2.0):
    """在 img 上加一团径向光（screen-ish 叠加）。"""
    r = int(r)
    x0, y0 = int(cx - r), int(cy - r)
    m = radial_mask(2 * r, 2 * r, r, r, r, power)
    if strength != 1.0:
        m = m.point(lambda v: int(clamp(v * strength / 255) * 255))
    layer = Image.new("RGB", (2 * r, 2 * r), color)
    box = (x0, y0)
    region = img.crop((x0, y0, x0 + 2 * r, y0 + 2 * r))
    added = ImageChops.add(region, Image.composite(layer, Image.new("RGB", layer.size), m))
    img.paste(added, box)
    return img


@functools.lru_cache(None)
def vignette_mask(strength=0.75):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.62)) ** 2)
    m = 1 - strength * np.clip(d - 0.35, 0, 1) ** 1.6
    return m.astype(np.float32)[..., None]


_GRAIN = None


def grain_frames():
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7)
        _GRAIN = [rng.normal(0, 2.8, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]
    return _GRAIN


def finish(img, fi, vig=0.75, grain=True):
    a = np.asarray(img).astype(np.float32)
    a *= vignette_mask(vig)
    if grain:
        g = grain_frames()[fi % 6]
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)
        a += g
    return np.clip(a, 0, 255).astype(np.uint8)


# ── 文字 ──
def text_size(s, f):
    b = f.getbbox(s)
    return b[2] - b[0], b[3] - b[1]


def draw_text(img, xy, s, f, fill=PAPER, anchor="mm", shadow=6, alpha=1.0, stroke=0, stroke_fill=(0, 0, 0)):
    if alpha <= 0.01:
        return img
    base = img.convert("RGBA") if img.mode != "RGBA" else img
    lay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 2, xy[1] + 3), s, font=f, fill=(0, 0, 0, int(200 * alpha)), anchor=anchor,
                                stroke_width=stroke + 2, stroke_fill=(0, 0, 0, int(200 * alpha)))
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        lay = Image.alpha_composite(lay, sh)
        d = ImageDraw.Draw(lay)
    d.text(xy, s, font=f, fill=fill + (int(255 * alpha),), anchor=anchor, stroke_width=stroke,
           stroke_fill=stroke_fill + (int(255 * alpha),))
    out = Image.alpha_composite(base, lay)
    return out.convert(img.mode) if img.mode != "RGBA" else out


def wrap(s, f, maxw):
    """按像素宽度断行（中文逐字），尽量不让标点落在行首。"""
    lines, cur = [], ""
    for ch in s:
        if text_size(cur + ch, f)[0] > maxw and cur:
            if ch in "，。！？；：、」』）”":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(s, f, maxw):
    """两行时尽量等长。"""
    ls = wrap(s, f, maxw)
    if len(ls) == 2:
        n = len(s)
        best = None
        for k in range(max(1, n // 2 - 6), min(n - 1, n // 2 + 7)):
            a, b = s[:k], s[k:]
            if b and b[0] in "，。！？；：、」』）”":
                continue
            wa, wb = text_size(a, f)[0], text_size(b, f)[0]
            if max(wa, wb) <= maxw:
                score = abs(wa - wb) - (30 if a[-1] in "，。；：！？" else 0)
                if best is None or score < best[0]:
                    best = (score, [a, b])
        if best:
            return best[1]
    return ls


def vtext(img, x, y, s, f, fill=INK, alpha=1.0, gap=1.08):
    """竖排文字，(x,y) 为第一个字中心。"""
    d = ImageDraw.Draw(img, "RGBA")
    step = f.size * gap
    for i, ch in enumerate(s):
        d.text((x, y + i * step), ch, font=f, fill=fill + (int(255 * alpha),), anchor="mm")
    return img


# ── 形状 ──
def poly(d, pts, fill):
    d.polygon([(float(x), float(y)) for x, y in pts], fill=fill)


def mountains(w, h, base_y, amp, seed, color, rough=0.5, n=9):
    """返回一条山脊剪影（RGBA 图）。"""
    rng = np.random.default_rng(seed)
    xs = np.linspace(-50, w + 50, 240)
    y = np.zeros_like(xs)
    for k in range(1, n + 1):
        y += rng.uniform(0.3, 1.0) * (rough ** (k - 1)) * np.sin(xs / w * math.pi * (k * 1.3) + rng.uniform(0, 6.28))
    y = base_y - amp * (y - y.min()) / (y.max() - y.min() + 1e-9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = list(zip(xs, y)) + [(w + 50, h), (-50, h)]
    d.polygon(pts, fill=color)
    return im


def figure(d, x, y, s, color, kind="robe", facing=1):
    """古装人物剪影（背影/侧影）。(x,y) 为脚底中心，s 为身高像素。"""
    h = s
    head = h * 0.075
    # 冠
    d.ellipse([x - head, y - h + head * 0.4, x + head, y - h + head * 2.4], fill=color)
    d.rectangle([x - head * 0.35, y - h - head * 0.2, x + head * 0.35, y - h + head * 0.8], fill=color)
    # 长袍：梯形 + 袖
    sh = y - h + head * 2.3
    poly(d, [(x - h * 0.10, sh), (x + h * 0.10, sh), (x + h * 0.20, y), (x - h * 0.20, y)], color)
    poly(d, [(x - h * 0.10, sh + h * 0.02), (x - h * 0.19, sh + h * 0.30), (x - h * 0.15, sh + h * 0.45),
             (x - h * 0.06, sh + h * 0.12)], color)
    poly(d, [(x + h * 0.10, sh + h * 0.02), (x + h * 0.19, sh + h * 0.30), (x + h * 0.15, sh + h * 0.45),
             (x + h * 0.06, sh + h * 0.12)], color)
    if kind == "crown":
        d.rectangle([x - head * 1.4, y - h - head * 0.1, x + head * 1.4, y - h + head * 0.3], fill=color)


def horse(d, x, y, s, color, ang=0.0, phase=0.0):
    """马的剪影（侧面奔跑），朝 ang 方向（弧度，0=向右）。(x,y) 为躯干中心。"""
    ca, sa = math.cos(ang), math.sin(ang)
    flip = -1 if ca < 0 else 1

    def T(px, py):
        px *= flip
        # 只做水平翻转 + 轻微倾斜，保持剪影直立
        tilt = sa * 0.25 * flip
        return (x + px * s - py * s * tilt, y + py * s + px * s * tilt)

    body = [(-0.55, -0.12), (-0.2, -0.22), (0.3, -0.22), (0.5, -0.32), (0.62, -0.58), (0.74, -0.66), (0.86, -0.6),
            (0.8, -0.5), (0.68, -0.42), (0.62, -0.18), (0.5, 0.05), (-0.45, 0.08), (-0.62, -0.02)]
    poly(d, [T(*p) for p in body], color)
    # 鬃、尾
    poly(d, [T(0.52, -0.36), T(0.6, -0.66), T(0.42, -0.4)], color)
    poly(d, [T(-0.55, -0.1), T(-0.85, 0.05 + 0.1 * math.sin(phase * 3)), T(-0.78, 0.25), T(-0.58, 0.02)], color)
    # 腿（奔跑相位）
    for lx, ph in [(-0.38, 0), (-0.28, 1.6), (0.36, 3.1), (0.46, 4.7)]:
        a = 0.55 * math.sin(phase + ph)
        kx, ky = lx + 0.18 * math.sin(a), 0.05 + 0.22 * math.cos(a)
        fx, fy = kx + 0.16 * math.sin(a * 1.6 - 0.3), ky + 0.22
        for (p, q) in [((lx, 0.02), (kx, ky)), ((kx, ky), (fx, fy))]:
            P, Q = T(*p), T(*q)
            d.line([P, Q], fill=color, width=max(2, int(s * 0.055)))


def slip(w, h, seed=0, tone=1.0, dark=False):
    """一根竹简（RGBA）。"""
    rng = np.random.default_rng(seed)
    c0 = np.array(SLIP if not dark else (96, 78, 52), float) * tone
    x = np.linspace(-1, 1, w)[None, :]
    shade = 0.82 + 0.18 * (1 - x ** 2)
    yy = np.linspace(0, 1, h)[:, None]
    fib = 1 + 0.04 * np.sin(np.linspace(0, 40, w) + rng.uniform(0, 6))[None, :] + rng.normal(0, 0.015, (h, w))
    blot = 1 - 0.08 * np.exp(-((yy - rng.uniform(0.2, 0.8)) ** 2) / 0.02)
    a = c0[None, None, :] * (shade * fib * blot)[..., None]
    a = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB").convert("RGBA")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=max(2, w // 6), fill=255)
    im.putalpha(m)
    return im


def slip_card(lines_text, f, w_slip=86, h=760, n=None, seed=1, fill=(40, 26, 14)):
    """一排竹简，每根竖写一列（从右到左）。lines_text: 每根竹简的文字列表。返回 RGBA。"""
    n = n or len(lines_text)
    gap = 6
    W2 = n * (w_slip + gap) + 40
    im = Image.new("RGBA", (W2, h + 40), (0, 0, 0, 0))
    for i in range(n):
        s = slip(w_slip, h, seed=seed + i)
        x = W2 - 20 - (i + 1) * (w_slip + gap)
        im.alpha_composite(s, (x, 20))
        if i < len(lines_text):
            vtext(im, x + w_slip // 2, 20 + f.size * 1.0, lines_text[i], f, fill=fill)
    d = ImageDraw.Draw(im)
    for yy in (int(h * 0.18), int(h * 0.82)):
        d.line([(10, 20 + yy), (W2 - 10, 20 + yy)], fill=(70, 44, 24, 255), width=5)
    return im


def paste_center(img, im, cx, cy, alpha=1.0, scale=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if img.mode == "RGBA":
        img.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else img.paste(im, (x, y), im)
    else:
        img.paste(im, (x, y), im)
    return img


def kenburns(img, t, D, z0=1.0, z1=1.08, cx0=0.5, cy0=0.5, cx1=0.5, cy1=0.5):
    """对整幅图做缓慢推拉（输出 W×H）。img 可以比画面大。"""
    k = ease(t / max(D, 1e-6))
    z = lerp(z0, z1, k)
    cx, cy = lerp(cx0, cx1, k) * img.width, lerp(cy0, cy1, k) * img.height
    w, h = W / z * img.width / W, H / z * img.height / H
    w, h = img.width / z, img.height / z
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    box = (max(0, box[0]), max(0, box[1]), min(img.width, box[2]), min(img.height, box[3]))
    return img.transform((W, H), Image.EXTENT, box, Image.BILINEAR)


def dust(img, t, n=60, seed=3, color=(220, 200, 160), speed=18, size=2.2, alpha=110, region=None):
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = region or (0, 0, W, H)
    for i in range(n):
        px = rng.uniform(x0, x1); py = rng.uniform(y0, y1)
        vx, vy = rng.uniform(-0.4, 0.4) * speed, rng.uniform(-1, -0.2) * speed
        ph = rng.uniform(0, 6.28)
        x = x0 + (px - x0 + vx * t + 12 * math.sin(t * 0.5 + ph)) % (x1 - x0)
        y = y0 + (py - y0 + vy * t) % (y1 - y0)
        a = int(alpha * (0.5 + 0.5 * math.sin(t * 1.3 + ph)))
        r = size * rng.uniform(0.6, 1.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (a,))
    return img


def arrow(d, p0, p1, color, width=10, head=34, k=1.0):
    """粗箭头，k∈[0,1] 为生长进度。"""
    if k <= 0:
        return
    x0, y0 = p0; x1, y1 = p1
    x1, y1 = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    ang = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - head * 0.8 * math.cos(ang), y1 - head * 0.8 * math.sin(ang)
    d.line([(x0, y0), (bx, by)], fill=color, width=width)
    poly(d, [(x1, y1), (x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45)),
             (x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))], color)


def path_arrow(d, pts, color, width=10, head=34, k=1.0):
    """沿折线生长的箭头。"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = sum(seg) * clamp(k)
    if L <= 0:
        return
    out = [pts[0]]
    for i, s in enumerate(seg):
        if L >= s:
            out.append(pts[i + 1]); L -= s
        else:
            a, b = pts[i], pts[i + 1]
            out.append((a[0] + (b[0] - a[0]) * L / s, a[1] + (b[1] - a[1]) * L / s)); break
    if len(out) >= 2:
        if len(out) > 2:
            d.line(out[:-1], fill=color, width=width, joint="curve")
        arrow(d, out[-2], out[-1], color, width, head)


def seal(text, size=150, color=RED):
    """朱文方印（RGBA）。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, size - 4, size - 4], radius=10, outline=color + (255,), width=8)
    n = len(text)
    if n == 4:
        f = font("serif", int(size * 0.36), "Black", tc=True)
        for i, ch in enumerate(text):
            cx = size * (0.70 if i < 2 else 0.30); cy = size * (0.30 if i % 2 == 0 else 0.70)
            d.text((cx, cy), ch, font=f, fill=color + (255,), anchor="mm")
    else:
        f = font("serif", int(size * 0.5 / max(1, n) * 1.6), "Black", tc=True)
        d.text((size / 2, size / 2), text, font=f, fill=color + (255,), anchor="mm")
    return im
