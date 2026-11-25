# -*- coding: utf-8 -*-
"""渲染引擎：cairo 画矢量，PIL 排字，numpy 做后期（颗粒、暗角）。"""
import math
import os
import functools
import numpy as np
import cairo
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 25
FONT_DIR = "/usr/share/fonts/opentype/noto"

# ── 配色 ──────────────────────────────────────────────────
def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)

C = dict(
    bg="#0f0d0b", bg2="#1a1611", ink="#efe6d2", dim="#a99d86", faint="#6b6152",
    gold="#c9a45c", gold2="#e6c886",
    red="#d23a2c", red2="#f2604a", redk="#7d1e16",          # 刘备 朱红
    black="#0b0b0c", blackg="#c9a45c",                      # 曹操 玄黑描金
    green="#93c08a", green2="#b9dcb0", greenk="#3f5e3a",   # 陶谦 浅绿（中立）
    blue="#5b8fc7", blue2="#8fb8e6", bluek="#26405e",      # 吕布 冷蓝
    yellow="#c79f4c", yellow2="#e3c278", yellowk="#5e4a22", # 袁氏 土黄
    gray="#8b93a0", grayk="#3c434d",                        # 公孙瓒/田楷 冷蓝灰
    river="#6f8ea6", water="#13202a",
)


# ── 缓动 ──────────────────────────────────────────────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def prog(t, t0, dur):
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return clamp((t - t0) / dur)

def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_in(x):
    x = clamp(x); return x ** 3

def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_back(x, s=1.4):
    x = clamp(x) - 1
    return 1 + x * x * ((s + 1) * x + s)

def smooth(x):
    x = clamp(x); return x * x * (3 - 2 * x)

def lerp(a, b, x):
    return a + (b - a) * x

def fade(t, t_in, t_out=None, d_in=0.4, d_out=0.4):
    """t_in 起淡入，t_out 起淡出"""
    a = ease_out(prog(t, t_in, d_in))
    if t_out is not None:
        a *= 1 - ease_in(prog(t, t_out, d_out))
    return a

# ── 字体与文字精灵 ────────────────────────────────────────
FONT_FILES = {"serif": "NotoSerifCJK-{w}.ttc", "sans": "NotoSansCJK-{w}.ttc", "tc": "NotoSerifCJK-{w}.ttc"}
FONT_INDEX = {"serif": 2, "sans": 2, "tc": 3}


@functools.lru_cache(maxsize=256)
def font(family, weight, size):
    w = {"Regular": "Regular", "Medium": "Medium", "SemiBold": "SemiBold", "Bold": "Bold", "Black": "Black",
         "Light": "Light"}.get(weight, "Regular")
    if family == "sans" and w == "SemiBold":
        w = "Medium"
    return ImageFont.truetype(os.path.join(FONT_DIR, FONT_FILES[family].format(w=w)), int(size), index=FONT_INDEX[family])


_KEEP = {}


def _pil_to_surface(img):
    """PIL RGBA → cairo ARGB32（预乘）"""
    arr = np.asarray(img, dtype=np.uint8)
    h, w = arr.shape[:2]
    a = arr[..., 3:4].astype(np.float32) / 255.0
    out = np.empty((h, w, 4), np.uint8)
    out[..., 0] = (arr[..., 2] * a[..., 0] + 0.5).astype(np.uint8)
    out[..., 1] = (arr[..., 1] * a[..., 0] + 0.5).astype(np.uint8)
    out[..., 2] = (arr[..., 0] * a[..., 0] + 0.5).astype(np.uint8)
    out[..., 3] = arr[..., 3]
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    if stride != w * 4:
        pad = np.zeros((h, stride), np.uint8)
        pad[:, : w * 4] = out.reshape(h, w * 4)
        out = pad
    out = np.ascontiguousarray(out)
    surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, w, h, stride)
    _KEEP[id(surf)] = out  # 防止底层内存被回收
    return surf


@functools.lru_cache(maxsize=4096)
def text_sprite(text, family="sans", weight="Medium", size=48, color="#efe4cc",
                tracking=0.0, shadow=0, stroke=0, stroke_color="#000000", vertical=False, line_gap=0.18):
    """返回 (surface, w, h, (ox, oy))。ox/oy 为文字左上相对精灵左上的偏移（含阴影边距）。"""
    f = font(family, weight, size)
    col = hexrgb(color)
    rgba = tuple(int(c * 255) for c in col[:3]) + (255,)
    pad = int(max(shadow * 2.5, stroke * 2) + 4)
    if not vertical:
        # 逐字排，支持字距
        adv = []
        for ch in text:
            bb = f.getbbox(ch)
            adv.append(f.getlength(ch))
        tw = sum(adv) + tracking * size * max(0, len(text) - 1)
        asc, desc = f.getmetrics()
        th = asc + desc
        img = Image.new("RGBA", (int(tw + 2 * pad + 2), int(th + 2 * pad + 2)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = pad
        for ch, a in zip(text, adv):
            d.text((x, pad), ch, font=f, fill=rgba, stroke_width=stroke,
                   stroke_fill=tuple(int(c * 255) for c in hexrgb(stroke_color)[:3]) + (255,))
            x += a + tracking * size
    else:
        step = size * (1 + line_gap)
        th = step * len(text)
        tw = size * 1.1
        img = Image.new("RGBA", (int(tw + 2 * pad), int(th + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, ch in enumerate(text):
            if ch in "，。、；：！？":
                # 竖排标点放右上
                d.text((pad + size * 0.55, pad + i * step - size * 0.35), ch, font=f, fill=rgba)
            else:
                cw = f.getlength(ch)
                d.text((pad + (tw - cw) / 2, pad + i * step), ch, font=f, fill=rgba, stroke_width=stroke,
                       stroke_fill=tuple(int(c * 255) for c in hexrgb(stroke_color)[:3]) + (255,))
    if shadow:
        a = img.split()[3]
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.putalpha(a.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: int(v * 0.85)))
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.alpha_composite(sh, (0, int(shadow * 0.4)))
        base.alpha_composite(img)
        img = base
    surf = _pil_to_surface(img)
    return surf, img.size[0], img.size[1], pad


def text_size(text, family="sans", weight="Medium", size=48, tracking=0.0):
    f = font(family, weight, size)
    w = sum(f.getlength(ch) for ch in text) + tracking * size * max(0, len(text) - 1)
    asc, desc = f.getmetrics()
    return w, asc + desc


def draw_text(ctx, text, x, y, family="sans", weight="Medium", size=48, color="#efe4cc",
              alpha=1.0, anchor="lt", tracking=0.0, shadow=0, stroke=0, stroke_color="#000000",
              scale=1.0, vertical=False, line_gap=0.18):
    """anchor: 两个字母，水平 l/c/r，垂直 t/m/b（以文字框而非精灵框计）"""
    if alpha <= 0.003 or not text:
        return
    surf, sw, sh, pad = text_sprite(text, family, weight, int(size), color, tracking, shadow, stroke,
                                    stroke_color, vertical, line_gap)
    bw, bh = sw - 2 * pad, sh - 2 * pad
    ax = {"l": 0, "c": 0.5, "r": 1}[anchor[0]]
    ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
    ctx.save()
    ctx.translate(x, y)
    if scale != 1.0:
        ctx.scale(scale, scale)
    ctx.translate(-ax * bw - pad, -ay * bh - pad)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return bw, bh


def wrap_cjk(text, family, weight, size, maxw, tracking=0.0):
    """按宽度折行，避免行首标点。"""
    lines, cur = [], ""
    for ch in text:
        if text_size(cur + ch, family, weight, size, tracking)[0] <= maxw or not cur:
            cur += ch
        else:
            if ch in "，。、；：！？」』）——…":
                cur += ch
                lines.append(cur); cur = ""
            else:
                lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


# ── 基础矢量 ──────────────────────────────────────────────
def set_col(ctx, col, alpha=1.0):
    r, g, b, a = hexrgb(col) if isinstance(col, str) else col
    ctx.set_source_rgba(r, g, b, a * alpha)


def rect(ctx, x, y, w, h, col, alpha=1.0):
    set_col(ctx, col, alpha); ctx.rectangle(x, y, w, h); ctx.fill()


def rrect_path(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def line(ctx, x0, y0, x1, y1, col, width=2, alpha=1.0, dash=None, cap=cairo.LINE_CAP_ROUND):
    set_col(ctx, col, alpha)
    ctx.set_line_width(width)
    ctx.set_line_cap(cap)
    if dash:
        ctx.set_dash(dash)
    ctx.move_to(x0, y0); ctx.line_to(x1, y1); ctx.stroke()
    if dash:
        ctx.set_dash([])


def circle(ctx, x, y, r, col, alpha=1.0, stroke=None, width=2):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    if stroke:
        set_col(ctx, col, alpha); ctx.set_line_width(width); ctx.stroke()
    else:
        set_col(ctx, col, alpha); ctx.fill()


def polyline(ctx, pts, col, width=2, alpha=1.0, frac=1.0, close=False):
    """frac: 只画到总长度的一部分（路线生长动画）"""
    if len(pts) < 2 or frac <= 0:
        return
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) * clamp(frac)
    set_col(ctx, col, alpha)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    acc = 0
    for i, s in enumerate(seg):
        if acc + s >= total:
            r = (total - acc) / s if s else 0
            ctx.line_to(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r)
            break
        ctx.line_to(*pts[i + 1])
        acc += s
    if close and frac >= 1:
        ctx.close_path()
    ctx.stroke()


def point_along(pts, frac):
    seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(seg) * clamp(frac)
    acc = 0
    for i, s in enumerate(seg):
        if acc + s >= total:
            r = (total - acc) / s if s else 0
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * r
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * r
            ang = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
            return x, y, ang
        acc += s
    ang = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    return pts[-1][0], pts[-1][1], ang


def arrow_head(ctx, x, y, ang, size, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.move_to(x + math.cos(ang) * size, y + math.sin(ang) * size)
    ctx.line_to(x + math.cos(ang + 2.5) * size * 0.8, y + math.sin(ang + 2.5) * size * 0.8)
    ctx.line_to(x + math.cos(ang - 2.5) * size * 0.8, y + math.sin(ang - 2.5) * size * 0.8)
    ctx.close_path(); ctx.fill()


def arrow(ctx, pts, col, width=4, alpha=1.0, frac=1.0, head=16):
    polyline(ctx, pts, col, width, alpha, frac)
    if frac > 0.02:
        x, y, a = point_along(pts, frac)
        arrow_head(ctx, x, y, a, head, col, alpha)


def smooth_path(pts, n=12):
    """Catmull-Rom 平滑"""
    if len(pts) < 3:
        return pts
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


# ── 印章 ──────────────────────────────────────────────────
@functools.lru_cache(maxsize=64)
def seal_sprite(text, size=120, color="#b8352a", style="square"):
    """朱文印：方框 + 篆意（用宋体粗体代替），边缘做旧"""
    s = int(size)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = tuple(int(c * 255) for c in hexrgb(color)[:3])
    m = max(3, s // 14)
    d.rounded_rectangle([m, m, s - m, s - m], radius=s // 12, fill=col + (255,))
    n = len(text)
    f = font("serif", "Black", int(s * (0.36 if n > 2 else 0.42)))
    if n <= 2:
        cells = [(s / 2, s / 2)] if n == 1 else [(s / 2, s * 0.33), (s / 2, s * 0.67)]
        if n == 1:
            f = font("serif", "Black", int(s * 0.6))
    elif n == 3:
        cells = [(s * 0.68, s * 0.33), (s * 0.68, s * 0.67), (s * 0.32, s * 0.5)]
    else:
        cells = [(s * 0.68, s * 0.31), (s * 0.68, s * 0.69), (s * 0.32, s * 0.31), (s * 0.32, s * 0.69)]
    for ch, (cx, cy) in zip(text, cells):
        bb = f.getbbox(ch)
        d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), ch, font=f, fill=(0, 0, 0, 0))
    # 用文字镂空：重新画一遍为透明
    arr = np.array(img)
    txt = Image.new("L", (s, s), 0)
    dt = ImageDraw.Draw(txt)
    for ch, (cx, cy) in zip(text, cells):
        bb = f.getbbox(ch)
        dt.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), ch, font=f, fill=255)
    t = np.array(txt).astype(np.float32) / 255
    arr[..., 3] = (arr[..., 3] * (1 - t)).astype(np.uint8)
    # 做旧：随机斑驳
    rng = np.random.default_rng(len(text) * 7 + s)
    noise = rng.random((s, s))
    blot = (noise > 0.93) & (arr[..., 3] > 0)
    arr[..., 3][blot] = (arr[..., 3][blot] * 0.25).astype(np.uint8)
    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(0.6))
    return _pil_to_surface(img), s


def draw_seal(ctx, text, x, y, size=120, alpha=1.0, color="#b8352a", rot=0.0, scale=1.0):
    surf, s = seal_sprite(text, int(size), color)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(scale, scale)
    ctx.translate(-s / 2, -s / 2)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


# ── 背景纹理、颗粒、暗角 ──────────────────────────────────
@functools.lru_cache(maxsize=4)
def paper_texture(seed=1, tone="#14100c", tone2="#1f1913", w=W, h=H):
    rng = np.random.default_rng(seed)
    base = np.array(hexrgb(tone)[:3]) * 255
    base2 = np.array(hexrgb(tone2)[:3]) * 255
    # 大尺度明暗
    small = rng.random((h // 64 + 2, w // 64 + 2)).astype(np.float32)
    big = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    # 纤维
    fib = rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32)
    fib = np.array(Image.fromarray(np.clip(fib * 40 + 128, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
                   .filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 255 - 0.5
    # 横向纤维条纹
    streak = rng.normal(0, 1, (h // 3, 8)).astype(np.float32)
    streak = np.array(Image.fromarray(np.clip(streak * 50 + 128, 0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255 - 0.5
    img = base[None, None, :] * (1 - big[..., None] * 0.6) + base2[None, None, :] * (big[..., None] * 0.6)
    img = img + fib[..., None] * 10 + streak[..., None] * 5
    img = np.clip(img, 0, 255).astype(np.uint8)
    rgba = np.dstack([img, np.full((h, w), 255, np.uint8)])
    return _pil_to_surface(Image.fromarray(rgba, "RGBA"))


@functools.lru_cache(maxsize=1)
def vignette_map(strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W / 2) / (W / 2)
    ny = (yy - H * 0.46) / (H / 2)
    d = np.sqrt(nx ** 2 * 1.15 + ny ** 2 * 0.85)
    v = 1 - strength * np.clip(d - 0.35, 0, 1.2) ** 1.6
    return np.clip(v, 0.25, 1).astype(np.float32)[..., None]


@functools.lru_cache(maxsize=1)
def grain_bank(n=12, amp=3.5, seed=3):
    rng = np.random.default_rng(seed)
    bank = []
    for _ in range(n):
        g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        g = np.array(Image.fromarray(np.clip(g * 40 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32)
        bank.append(((g - 128) / 40 * amp)[..., None])
    return bank


def postprocess(surface, frame_idx, grain=True, vig=True):
    buf = np.ndarray((H, W, 4), np.uint8, surface.get_data())
    rgb = buf[..., :3].astype(np.float32)
    if vig:
        rgb *= vignette_map()
    if grain:
        g = grain_bank()[(frame_idx // 2) % len(grain_bank())]
        # 颗粒在中间调最明显
        lum = rgb.mean(axis=2, keepdims=True) / 255
        rgb += g * (0.35 + 0.65 * (1 - np.abs(lum - 0.45) * 1.6).clip(0, 1))
    buf[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return buf


def new_frame():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    return surf, ctx


def paint_surface(ctx, surf, x=0, y=0, alpha=1.0, scale=1.0, cx=None, cy=None):
    ctx.save()
    if scale != 1.0:
        cx = W / 2 if cx is None else cx
        cy = H / 2 if cy is None else cy
        ctx.translate(cx, cy); ctx.scale(scale, scale); ctx.translate(-cx, -cy)
    ctx.set_source_surface(surf, x, y)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
