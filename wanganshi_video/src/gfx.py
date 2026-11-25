# -*- coding: utf-8 -*-
"""Drawing primitives: rice-paper texture, ink washes, sprites (coins, figures, buildings, seals, ledgers),
text helpers. Everything procedural (numpy / OpenCV / PIL)."""
import math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FD = "/usr/share/fonts/opentype/noto/"
CAL = "/tmp/claude-0/fonts/"

INK = (28, 26, 24)
PAPER = (234, 224, 200)
RED = (178, 34, 30)
VERM = (196, 58, 36)
GOLD = (196, 150, 70)
BRONZE = (150, 110, 60)
GREEN = (92, 128, 70)
NIGHT = (16, 20, 30)


@functools.lru_cache(maxsize=None)
def font(kind, size):
    if kind == "serif":
        return ImageFont.truetype(FD + "NotoSerifCJK-Bold.ttc", size, index=2)
    if kind == "serif_tc":
        return ImageFont.truetype(FD + "NotoSerifCJK-Bold.ttc", size, index=3)
    if kind == "serif_black":
        return ImageFont.truetype(FD + "NotoSerifCJK-Black.ttc", size, index=2)
    if kind == "serif_black_tc":
        return ImageFont.truetype(FD + "NotoSerifCJK-Black.ttc", size, index=3)
    if kind == "serif_reg":
        return ImageFont.truetype(FD + "NotoSerifCJK-Regular.ttc", size, index=2)
    if kind == "sans":
        return ImageFont.truetype(FD + "NotoSansCJK-Bold.ttc", size, index=2)
    if kind == "sans_med":
        return ImageFont.truetype(FD + "NotoSansCJK-Medium.ttc", size, index=2)
    if kind == "brush":
        return ImageFont.truetype(CAL + "MaShanZheng.ttf", size)
    if kind == "cao":
        return ImageFont.truetype(CAL + "ZhiMangXing.ttf", size)
    raise KeyError(kind)


# ───────────────────────── easing ─────────────────────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ramp(t, t0, d=0.6):
    return ease((t - t0) / d) if d > 0 else float(t >= t0)


# ───────────────────────── noise / textures ─────────────────────────
def smooth_noise(h, w, scale, seed, octaves=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gh, gw = max(2, int(h / s) + 2), max(2, int(w / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp; amp *= 0.5; s /= 2
    return out / tot


@functools.lru_cache(maxsize=None)
def paper(seed=1, tone=PAPER, dark=False):
    rng = np.random.default_rng(seed)
    base = np.ones((H, W, 3), np.float32) * np.array(tone, np.float32)
    blot = smooth_noise(H, W, 380, seed) - 0.5
    base += blot[..., None] * (26 if not dark else 14)
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    fine = cv2.GaussianBlur(fine, (0, 0), 0.8)
    base += fine[..., None] * (5 if not dark else 3)
    # fibres
    fib = np.zeros((H, W), np.float32)
    for _ in range(900):
        x, y = rng.integers(0, W), rng.integers(0, H)
        a = rng.uniform(0, math.pi); L = rng.uniform(8, 40)
        cv2.line(fib, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))), 1.0, 1, cv2.LINE_AA)
    fib = cv2.GaussianBlur(fib, (0, 0), 0.6)
    base -= fib[..., None] * (14 if not dark else -6)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2
    base *= (1 - 0.28 * np.clip(v, 0, 1.5))[..., None]
    return np.clip(base, 0, 255).astype(np.uint8)


def night_bg(seed=3):
    p = paper(seed, tone=(30, 34, 46), dark=True).astype(np.float32)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    p = p * (0.75 + 0.35 * yy)
    return np.clip(p, 0, 255).astype(np.uint8)


def ridge_layer(y0, amp, seed, color=INK, alpha=0.6, blur=3, fade=420, w=W, h=H, rough=1.0):
    """Ink-wash mountain ridge: RGBA float layer."""
    rng = np.random.default_rng(seed)
    xs = np.arange(w)
    n = smooth_noise(1, w, 260, seed, 5)[0] - 0.5
    n2 = smooth_noise(1, w, 70, seed + 9, 3)[0] - 0.5
    top = y0 - amp * (n * 2.0 + rough * 0.35 * n2)
    yy = np.arange(h)[:, None].astype(np.float32)
    d = yy - top[None, :]
    a = np.clip(d / 6.0, 0, 1) * np.clip(1 - d / fade, 0, 1) ** 1.3
    a = a + 0.25 * np.clip(1 - np.abs(d) / 5, 0, 1)
    tex = smooth_noise(h, w, 60, seed + 3, 3)
    a = a * (0.75 + 0.5 * tex) * alpha
    if blur:
        a = cv2.GaussianBlur(a, (0, 0), blur)
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = color
    rgba[..., 3] = np.clip(a, 0, 1)
    return rgba


def over(base, rgba, x=0, y=0):
    """alpha-composite float RGBA (0..1 alpha) onto uint8/float RGB base in place (returns float)."""
    b = base.astype(np.float32) if base.dtype != np.float32 else base
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(b.shape[1], x + w), min(b.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return b
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4]
    b[y0:y1, x0:x1] = b[y0:y1, x0:x1] * (1 - a) + src[..., :3] * a
    return b


# ───────────────────────── PIL helpers ─────────────────────────
def pil_rgba(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def text_size(txt, f):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1]


try:
    import opencc
    _T2S = opencc.OpenCC("t2s")
except Exception:  # pragma: no cover
    _T2S = None


@functools.lru_cache(maxsize=None)
def _cmap(path):
    from fontTools.ttLib import TTFont
    return set(TTFont(path, fontNumber=0)["cmap"].getBestCmap().keys())


def t2s(txt):
    return _T2S.convert(txt) if _T2S else txt


def draw_text(img, xy, txt, f, fill, anchor="mm", stroke=0, stroke_fill=None, alpha=1.0, trad=False):
    if alpha <= 0.01:
        return
    if not trad:
        txt = t2s(txt)
    if alpha < 0.999:
        # draw on a temp layer and composite so the fade really blends
        probe = ImageDraw.Draw(img)
        fp0 = getattr(f, "path", "")
        if isinstance(fp0, str) and fp0.startswith(CAL):
            cm = _cmap(fp0)
            if any(ord(ch) not in cm for ch in txt if not ch.isspace()):
                f = font("serif_black", f.size)
        x0, y0, x1, y1 = probe.textbbox(xy, txt, font=f, anchor=anchor, stroke_width=stroke)
        x0, y0 = int(x0) - 4, int(y0) - 4
        lay = Image.new("RGBA", (int(x1) - x0 + 8, int(y1) - y0 + 8), (0, 0, 0, 0))
        draw_text(lay, (xy[0] - x0, xy[1] - y0), txt, f, fill, anchor, stroke, stroke_fill, 1.0, trad=True)
        if alpha > 0.0:
            a = lay.getchannel("A").point(lambda v: int(v * alpha))
            lay.putalpha(a)
            img.alpha_composite(lay, (max(0, x0), max(0, y0)), (max(0, -x0), max(0, -y0)))
        return
    fp = getattr(f, "path", "")
    if isinstance(fp, str) and fp.startswith(CAL):
        cm = _cmap(fp)
        if any(ord(ch) not in cm for ch in txt if not ch.isspace()):
            f = font("serif_black", f.size)
    d = ImageDraw.Draw(img)
    col = tuple(fill[:3]) + (int(255 * (fill[3] / 255 if len(fill) > 3 else 1)),)
    sf = None
    if stroke:
        sc = stroke_fill or (0, 0, 0)
        sf = tuple(sc[:3]) + (int(255 * (sc[3] / 255 if len(sc) > 3 else 1)),)
    d.text(xy, txt, font=f, fill=col, anchor=anchor, stroke_width=stroke, stroke_fill=sf)


def wrap(txt, f, maxw):
    """Greedy wrap for CJK (break anywhere, avoid line-initial punctuation); word-wrap for Latin."""
    if all(ord(ch) < 0x2E80 for ch in txt):
        lines, cur = [], ""
        for wd in txt.split(" "):
            cand = (cur + " " + wd).strip()
            if text_size(cand, f)[0] > maxw and cur:
                lines.append(cur); cur = wd
            else:
                cur = cand
        return lines + ([cur] if cur else [])
    lines, cur = [], ""
    for ch in txt:
        if text_size(cur + ch, f)[0] > maxw and cur:
            if ch in "，。、；：？！”」）》":
                cur += ch; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(txt, f, maxw):
    lines = wrap(txt, f, maxw)
    if len(lines) <= 1 or all(ord(ch) < 0x2E80 for ch in txt):
        return lines
    n = len(lines)
    # rebalance: try making lines equal length
    per = math.ceil(len(txt) / n)
    out, i = [], 0
    while i < len(txt):
        j = min(len(txt), i + per)
        while j < len(txt) and txt[j] in "，。、；：？！”」）》":
            j += 1
        out.append(txt[i:j]); i = j
    if all(text_size(l, f)[0] <= maxw * 1.04 for l in out):
        return out
    return lines


def to_np(img):
    a = np.asarray(img).astype(np.float32)
    a[..., 3] /= 255.0
    return a


# ───────────────────────── sprites ─────────────────────────
@functools.lru_cache(maxsize=None)
def coin(r, legend=True, tone=0):
    s = 3
    R = r * s
    im = pil_rgba(2 * R + 4, 2 * R + 4)
    d = ImageDraw.Draw(im)
    c = R + 2
    base = [(168, 124, 64), (140, 104, 58), (120, 96, 60)][tone]
    d.ellipse([c - R, c - R, c + R, c + R], fill=base + (255,), outline=(70, 50, 28, 255), width=max(2, R // 14))
    d.ellipse([c - R * 0.86, c - R * 0.86, c + R * 0.86, c + R * 0.86], outline=(96, 70, 38, 255), width=max(1, R // 22))
    hsz = R * 0.26
    d.rectangle([c - hsz, c - hsz, c + hsz, c + hsz], fill=(0, 0, 0, 0), outline=(80, 58, 30, 255), width=max(2, R // 18))
    d.rectangle([c - hsz + 2, c - hsz + 2, c + hsz - 2, c + hsz - 2], fill=(0, 0, 0, 0))
    if legend and r >= 18:
        f = font("serif_tc", int(R * 0.36))
        for ch, (dx, dy) in zip("熙寧元寶", [(0, -1), (0, 1), (1, 0), (-1, 0)]):
            draw_text(im, (c + dx * R * 0.56, c + dy * R * 0.56), ch, f, (80, 56, 28, 255), trad=True)
    # sheen
    arr = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]]
    sheen = np.clip(1 - ((xx - c * 0.7) ** 2 + (yy - c * 0.6) ** 2) / (R * R * 0.9), 0, 1) * 40
    arr[..., :3] += sheen[..., None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im = im.resize((im.width // s, im.height // s), Image.LANCZOS)
    return im


@functools.lru_cache(maxsize=None)
def coin_stack(n, r=30):
    """Side-view stack of n coins (a 'string' of cash) as RGBA image."""
    s = 2
    R = r * s
    hh = int(R * 0.34)
    step = int(R * 0.16)
    im = pil_rgba(2 * R + 8, n * step + hh + 8)
    d = ImageDraw.Draw(im)
    for i in range(n):
        y = im.height - hh - 4 - i * step
        col = (150 + (i * 7) % 20, 110 + (i * 5) % 16, 58, 255)
        d.ellipse([4, y, 4 + 2 * R, y + hh], fill=col, outline=(70, 50, 28, 255), width=2)
    y = im.height - hh - 4 - (n - 1) * step
    d.rectangle([R + 4 - hh * 0.3, y + hh * 0.3, R + 4 + hh * 0.3, y + hh * 0.7], fill=(60, 44, 24, 255))
    return im.resize((im.width // s, im.height // s), Image.LANCZOS)


@functools.lru_cache(maxsize=None)
def money_bag(size, label="青苗錢", tone=(150, 120, 80)):
    s = 2
    S = size * s
    im = pil_rgba(S, int(S * 1.15))
    d = ImageDraw.Draw(im)
    w = S
    d.ellipse([w * 0.08, S * 0.28, w * 0.92, S * 1.1], fill=tone + (255,), outline=INK + (255,), width=3 * s)
    d.polygon([(w * 0.32, S * 0.32), (w * 0.5, S * 0.16), (w * 0.68, S * 0.32)], fill=tone + (255,), outline=INK + (255,))
    d.ellipse([w * 0.36, S * 0.04, w * 0.64, S * 0.22], fill=tone + (255,), outline=INK + (255,), width=2 * s)
    d.line([(w * 0.33, S * 0.31), (w * 0.67, S * 0.31)], fill=(120, 30, 24, 255), width=5 * s)
    if label:
        f = font("serif_tc", int(S * 0.15))
        draw_text(im, (w * 0.5, S * 0.72), label, f, (60, 36, 20, 255), trad=True)
    return im.resize((im.width // s, im.height // s), Image.LANCZOS)


@functools.lru_cache(maxsize=None)
def seal(text, size, color=RED, rot=-4, cols=None):
    """Red square seal with white characters (2x2 or single row)."""
    s = 2
    S = size * s
    im = pil_rgba(S, S)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, S - 4, S - 4], radius=S // 14, fill=color + (255,))
    n = len(text)
    if n == 4:
        f = font("serif_black_tc", int(S * 0.38))
        pos = [(0.72, 0.29), (0.72, 0.71), (0.28, 0.29), (0.28, 0.71)]  # right column first, top-down
        for ch, (px, py) in zip(text, pos):
            draw_text(im, (S * px, S * py), ch, f, (248, 236, 220, 255), trad=True)
    elif n == 2:
        f = font("serif_black_tc", int(S * 0.42))
        draw_text(im, (S * 0.5, S * 0.29), text[0], f, (248, 236, 220, 255), trad=True)
        draw_text(im, (S * 0.5, S * 0.71), text[1], f, (248, 236, 220, 255), trad=True)
    else:
        f = font("serif_black_tc", int(S * 0.7 / max(1, n) * (1.6 if n == 1 else 1)))
        draw_text(im, (S * 0.5, S * 0.5), text, f, (248, 236, 220, 255), trad=True)
    arr = np.asarray(im).astype(np.float32)
    rng = np.random.default_rng(len(text) * 31 + size)
    holes = smooth_noise(S, S, 10, int(rng.integers(1e6)), 2)
    arr[..., 3] *= np.clip((holes - 0.18) * 4, 0, 1)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).rotate(rot, resample=Image.BICUBIC, expand=True)
    return im.resize((im.width // s, im.height // s), Image.LANCZOS)


@functools.lru_cache(maxsize=None)
def official(scale=1.0, color=INK, robe=(70, 60, 92), hold="book", facing=1):
    """Song official silhouette with long-winged futou hat; RGBA PIL."""
    s = 2
    k = scale * s
    w, h = int(300 * k), int(520 * k)
    im = pil_rgba(w, h)
    d = ImageDraw.Draw(im)
    cx = w / 2
    # robe
    d.polygon([(cx - 70 * k, 150 * k), (cx + 70 * k, 150 * k), (cx + 110 * k, 500 * k), (cx - 110 * k, 500 * k)], fill=robe + (255,))
    d.line([(cx, 160 * k), (cx, 500 * k)], fill=(40, 34, 52, 255), width=int(3 * k))
    d.rectangle([cx - 75 * k, 250 * k, cx + 75 * k, 268 * k], fill=(150, 120, 60, 255))  # belt
    # sleeves
    d.polygon([(cx - 70 * k, 160 * k), (cx - 120 * k, 330 * k), (cx - 60 * k, 340 * k), (cx - 40 * k, 200 * k)], fill=tuple(max(0, c - 12) for c in robe) + (255,))
    d.polygon([(cx + 70 * k, 160 * k), (cx + 120 * k, 330 * k), (cx + 60 * k, 340 * k), (cx + 40 * k, 200 * k)], fill=tuple(max(0, c - 12) for c in robe) + (255,))
    # head
    d.ellipse([cx - 38 * k, 70 * k, cx + 38 * k, 150 * k], fill=(214, 186, 150, 255))
    # futou hat with long wings
    d.rounded_rectangle([cx - 42 * k, 46 * k, cx + 42 * k, 98 * k], radius=int(16 * k), fill=color + (255,))
    d.rectangle([cx - 140 * k, 80 * k, cx + 140 * k, 88 * k], fill=color + (255,))
    if hold == "book":
        d.rectangle([cx - 50 * k, 270 * k, cx + 50 * k, 340 * k], fill=(230, 214, 176, 255), outline=INK + (255,), width=int(3 * k))
        d.line([(cx, 270 * k), (cx, 340 * k)], fill=INK + (255,), width=int(2 * k))
    elif hold == "hu":
        d.polygon([(cx - 10 * k, 330 * k), (cx + 10 * k, 330 * k), (cx + 14 * k, 180 * k), (cx - 14 * k, 180 * k)], fill=(230, 220, 200, 255))
    im = im.resize((w // s, h // s), Image.LANCZOS)
    if facing < 0:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


@functools.lru_cache(maxsize=None)
def farmer(scale=1.0, head_dx=0, tone=(120, 100, 72), poor=False):
    s = 2
    k = scale * s
    w, h = int(300 * k), int(460 * k)
    im = pil_rgba(w, h)
    d = ImageDraw.Draw(im)
    cx = w / 2
    body = tone
    d.polygon([(cx - 60 * k, 170 * k), (cx + 60 * k, 170 * k), (cx + 75 * k, 330 * k), (cx - 75 * k, 330 * k)], fill=body + (255,))
    d.rectangle([cx - 55 * k, 330 * k, cx - 15 * k, 440 * k], fill=(90, 76, 56, 255))
    d.rectangle([cx + 15 * k, 330 * k, cx + 55 * k, 440 * k], fill=(90, 76, 56, 255))
    d.rectangle([cx - 80 * k, 180 * k, cx - 55 * k, 300 * k], fill=body + (255,))
    d.rectangle([cx + 55 * k, 180 * k, cx + 80 * k, 300 * k], fill=body + (255,))
    hx = cx + head_dx * k
    d.ellipse([hx - 36 * k, 95 * k, hx + 36 * k, 170 * k], fill=(196, 160, 118, 255))
    # straw hat (douli)
    d.polygon([(hx - 110 * k, 120 * k), (hx, 40 * k), (hx + 110 * k, 120 * k)], fill=(196, 168, 100, 255), outline=(110, 88, 50, 255))
    for i in range(-3, 4):
        d.line([(hx, 44 * k), (hx + i * 30 * k, 118 * k)], fill=(150, 124, 70, 255), width=max(1, int(1.5 * k)))
    if poor:
        d.line([(cx - 40 * k, 220 * k), (cx + 20 * k, 260 * k)], fill=(70, 58, 40, 255), width=int(3 * k))
    return im.resize((w // s, h // s), Image.LANCZOS)


@functools.lru_cache(maxsize=None)
def building(kind="hall", scale=1.0, lit=False, label=None):
    """Song-style hall / granary / gate silhouette (side elevation)."""
    s = 2
    k = scale * s
    w, h = int(520 * k), int(380 * k)
    im = pil_rgba(w, h)
    d = ImageDraw.Draw(im)
    cx = w / 2
    roof = (44, 46, 56) if not lit else (40, 36, 40)
    wall = (150, 70, 50) if kind != "granary" else (170, 150, 116)
    # platform
    d.rectangle([cx - 240 * k, 330 * k, cx + 240 * k, 370 * k], fill=(120, 110, 96, 255))
    # walls / columns
    d.rectangle([cx - 200 * k, 170 * k, cx + 200 * k, 330 * k], fill=wall + (255,))
    for i in range(-4, 5):
        d.rectangle([cx + i * 46 * k - 6 * k, 170 * k, cx + i * 46 * k + 6 * k, 330 * k], fill=(90, 40, 30, 255) if kind != "granary" else (120, 100, 70, 255))
    if lit:
        for i in range(-3, 4):
            d.rectangle([cx + i * 46 * k + 10 * k, 200 * k, cx + i * 46 * k + 36 * k, 300 * k], fill=(255, 196, 110, 255))
    if kind == "gate":
        d.rectangle([cx - 50 * k, 210 * k, cx + 50 * k, 330 * k], fill=(60, 24, 20, 255))
    # roof: curved hip roof
    pts = []
    for i in range(41):
        x = -1 + i / 20
        y = 0.12 * x ** 6
        pts.append((cx + x * 270 * k, (172 - 60 * y * 3) * k))
    top = [(cx + 150 * k, 70 * k), (cx - 150 * k, 70 * k)]
    d.polygon(pts + top, fill=roof + (255,))
    d.line([(cx - 160 * k, 68 * k), (cx + 160 * k, 68 * k)], fill=roof + (255,), width=int(12 * k))
    d.polygon([(cx - 168 * k, 74 * k), (cx - 180 * k, 40 * k), (cx - 150 * k, 64 * k)], fill=roof + (255,))
    d.polygon([(cx + 168 * k, 74 * k), (cx + 180 * k, 40 * k), (cx + 150 * k, 64 * k)], fill=roof + (255,))
    if label:
        f = font("serif_black_tc", int(34 * k))
        tw = text_size(label, f)[0]
        d.rectangle([cx - tw / 2 - 16 * k, 120 * k, cx + tw / 2 + 16 * k, 166 * k], fill=(30, 30, 40, 255), outline=GOLD + (255,), width=int(3 * k))
        draw_text(im, (cx, 143 * k), label, f, (230, 190, 100, 255), trad=True)
    return im.resize((w // s, h // s), Image.LANCZOS)


@functools.lru_cache(maxsize=None)
def ledger(w, h, cols=10, title=None, rows_text=None):
    """Open account book (two pages) with vertical ruled columns. Returns RGBA PIL."""
    im = pil_rgba(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h], fill=(96, 60, 40, 255))
    m = 14
    d.rectangle([m, m, w - m, h - m], fill=(240, 228, 196, 255))
    d.line([(w / 2, m), (w / 2, h - m)], fill=(150, 120, 90, 255), width=4)
    for side in (0, 1):
        x0 = m + 30 + side * (w / 2 - m)
        x1 = x0 + w / 2 - m - 60
        d.rectangle([x0, m + 30, x1, h - m - 30], outline=(170, 50, 40, 255), width=3)
        for i in range(1, cols):
            x = x0 + (x1 - x0) * i / cols
            d.line([(x, m + 30), (x, h - m - 30)], fill=(190, 90, 70, 200), width=1)
    return im


def paste(base_img, sprite, cx, cy, alpha=1.0, scale=1.0, anchor="c", rot=0.0):
    """Paste PIL RGBA sprite onto PIL RGBA base; anchor c=center, b=bottom-center."""
    if alpha <= 0.01:
        return
    sp = sprite
    if scale != 1.0:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if rot:
        sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = sp.getchannel("A").point(lambda v: int(v * alpha))
        sp = sp.copy(); sp.putalpha(a)
    if anchor == "b":
        x, y = int(cx - sp.width / 2), int(cy - sp.height)
    else:
        x, y = int(cx - sp.width / 2), int(cy - sp.height / 2)
    base_img.alpha_composite(sp, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))


def ink_stroke(d, pts, width, color=INK, alpha=1.0):
    col = tuple(color[:3]) + (int(255 * alpha),)
    d.line(pts, fill=col, width=int(width), joint="curve")


def tick(d, x, y, s, prog, color=RED, width=9):
    """Brush tick mark ✓ drawn progressively (prog 0..1)."""
    p1, p2, p3 = (x - s * 0.5, y), (x - s * 0.12, y + s * 0.42), (x + s * 0.6, y - s * 0.55)
    if prog <= 0:
        return
    a = clamp(prog / 0.35)
    q = (p1[0] + (p2[0] - p1[0]) * a, p1[1] + (p2[1] - p1[1]) * a)
    d.line([p1, q], fill=color + (255,), width=width)
    if prog > 0.35:
        b = clamp((prog - 0.35) / 0.65)
        r = (p2[0] + (p3[0] - p2[0]) * b, p2[1] + (p3[1] - p2[1]) * b)
        d.line([p2, r], fill=color + (255,), width=width)


def arrow(d, a, b, color, width=10, head=30, prog=1.0):
    if prog <= 0:
        return
    bx, by = a[0] + (b[0] - a[0]) * prog, a[1] + (b[1] - a[1]) * prog
    d.line([a, (bx, by)], fill=color, width=width)
    ang = math.atan2(by - a[1], bx - a[0])
    p1 = (bx + head * math.cos(ang), by + head * math.sin(ang))
    p2 = (bx + head * 0.7 * math.cos(ang + 2.4), by + head * 0.7 * math.sin(ang + 2.4))
    p3 = (bx + head * 0.7 * math.cos(ang - 2.4), by + head * 0.7 * math.sin(ang - 2.4))
    d.polygon([p1, p2, p3], fill=color)


class ODraw:
    """ImageDraw wrapper: opaque primitives draw directly; semi-transparent ones are drawn on a
    bbox-sized temp layer and alpha-composited, so fades blend correctly."""

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)

    @staticmethod
    def _alpha(kw, args):
        for key in ("fill", "outline"):
            v = kw.get(key)
            if isinstance(v, tuple) and len(v) == 4 and v[3] < 255:
                return True
        return False

    @staticmethod
    def _pts(xy):
        if isinstance(xy, (list, tuple)) and xy and isinstance(xy[0], (list, tuple)):
            return [(float(p[0]), float(p[1])) for p in xy]
        flat = list(xy)
        return [(float(flat[i]), float(flat[i + 1])) for i in range(0, len(flat) - 1, 2)]

    def __getattr__(self, name):
        fn = getattr(self.d, name)
        if name not in ("line", "rectangle", "rounded_rectangle", "ellipse", "polygon", "chord", "pieslice", "arc"):
            return fn

        def wrapped(xy, *args, **kw):
            if not self._alpha(kw, args):
                return fn(xy, *args, **kw)
            pts = self._pts(xy)
            pad = int(kw.get("width", 1) or 1) + 4
            x0 = int(min(p[0] for p in pts)) - pad; y0 = int(min(p[1] for p in pts)) - pad
            x1 = int(max(p[0] for p in pts)) + pad; y1 = int(max(p[1] for p in pts)) + pad
            x0, y0 = max(0, x0), max(0, y0)
            x1, y1 = min(self.img.width, x1), min(self.img.height, y1)
            if x1 <= x0 or y1 <= y0:
                return
            lay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            sh = [(p[0] - x0, p[1] - y0) for p in pts]
            if name in ("rectangle", "rounded_rectangle", "ellipse", "chord", "pieslice", "arc"):
                sh = [sh[0][0], sh[0][1], sh[1][0], sh[1][1]]
            getattr(ld, name)(sh, *args, **kw)
            self.img.alpha_composite(lay, (x0, y0))
        return wrapped
