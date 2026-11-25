# -*- coding: utf-8 -*-
"""Drawing helpers on top of pycairo. Frame 1080x1920, ARGB32 (memory order BGRA)."""
import math
import numpy as np
import cairo

W, H = 1080, 1920
SANS = "Noto Sans CJK SC"
SERIF = "Noto Serif CJK SC"
LATIN_I = "DejaVu Serif"

# palette
BG = (0.075, 0.078, 0.085)
IVORY = (0.93, 0.89, 0.80)
GOLD = (0.86, 0.70, 0.40)
DIM = (0.62, 0.60, 0.55)
FR = (0.36, 0.58, 0.90)       # 法军 冷蓝
FR_D = (0.20, 0.36, 0.62)
AL = (0.74, 0.20, 0.18)       # 英荷联军 暗红
AL_D = (0.48, 0.12, 0.11)
PR = (0.36, 0.58, 0.40)       # 普军 墨绿
PR_D = (0.20, 0.36, 0.25)
FIRE = (1.0, 0.62, 0.25)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def surface_from_rgb(arr):
    """numpy HxWx3 float(0..1) or uint8 -> cairo ImageSurface"""
    if arr.dtype != np.uint8:
        arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    h, w = arr.shape[:2]
    buf = np.empty((h, w, 4), np.uint8)
    buf[..., 0] = arr[..., 2]; buf[..., 1] = arr[..., 1]; buf[..., 2] = arr[..., 0]; buf[..., 3] = 255
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :w] = buf
    s.mark_dirty()
    return s


def surface_from_rgba(arr):
    """premultiplies"""
    if arr.dtype != np.float32:
        arr = arr.astype(np.float32) / (255.0 if arr.dtype == np.uint8 else 1.0)
    h, w = arr.shape[:2]
    a = np.clip(arr[..., 3:4], 0, 1)
    rgb = np.clip(arr[..., :3], 0, 1) * a
    buf = np.empty((h, w, 4), np.uint8)
    buf[..., 0] = (rgb[..., 2] * 255); buf[..., 1] = (rgb[..., 1] * 255); buf[..., 2] = (rgb[..., 0] * 255)
    buf[..., 3] = (a[..., 0] * 255)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    np.ndarray((h, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :w] = buf
    s.mark_dirty()
    return s


def new_surface(w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def blur(a, sigma):
    """separable gaussian on 2D float array"""
    if sigma <= 0:
        return a
    r = int(sigma * 3)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    pad = np.pad(a, ((r, r), (0, 0)), mode="edge")
    a = sum(k[i] * pad[i:i + a.shape[0]] for i in range(2 * r + 1))
    pad = np.pad(a, ((0, 0), (r, r)), mode="edge")
    return sum(k[i] * pad[:, i:i + a.shape[1]] for i in range(2 * r + 1))


def noise2d(h, w, scale, rng, octaves=4):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1, int(scale * 2 ** o))
        g = rng.random((h // s + 3, w // s + 3)).astype(np.float32)
        yi = np.linspace(0, h / s, h); xi = np.linspace(0, w / s, w)
        y0 = yi.astype(int); x0 = xi.astype(int); fy = (yi - y0)[:, None]; fx = (xi - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp; amp *= 0.5
    return out / tot


# ---------------------------------------------------------------- text
def font(ctx, size, bold=False, serif=False, family=None, italic=False):
    fam = family or (SERIF if serif else SANS)
    ctx.select_font_face(fam, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_w(ctx, s):
    return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, color=IVORY, alpha=1.0, anchor="mm", bold=False, serif=False, halo=0, halo_col=(0, 0, 0),
         halo_a=0.75, family=None, italic=False):
    """anchor: [lmr][tmb] ; y is baseline-ish center for 'm'"""
    font(ctx, size, bold, serif, family, italic)
    wv = text_w(ctx, s)
    fe = ctx.font_extents()
    if anchor[0] == "m":
        x0 = x - wv / 2
    elif anchor[0] == "r":
        x0 = x - wv
    else:
        x0 = x
    if anchor[1] == "m":
        y0 = y + size * 0.36
    elif anchor[1] == "t":
        y0 = y + size * 0.88
    else:
        y0 = y
    if halo > 0 and alpha > 0:
        ctx.move_to(x0, y0); ctx.text_path(s)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*halo_col, halo_a * alpha); ctx.set_line_width(halo); ctx.stroke()
    ctx.move_to(x0, y0)
    ctx.set_source_rgba(*color, alpha)
    ctx.show_text(s)
    return wv


def wrap_cjk(ctx, s, maxw, size, bold=False, serif=False):
    font(ctx, size, bold, serif)
    lines, cur = [], ""
    for ch in s:
        if text_w(ctx, cur + ch) > maxw and cur:
            # avoid line-start punctuation
            if ch in "，。！？；：、”）》":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def wrap_words(ctx, s, maxw, size, family=LATIN_I, italic=True):
    font(ctx, size, family=family, italic=italic)
    lines, cur = [], ""
    for w_ in s.split(" "):
        t = (cur + " " + w_).strip()
        if text_w(ctx, t) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- shapes
def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def polyline_len(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def smooth(pts, n=12):
    """Catmull-Rom through control points"""
    if len(pts) < 3:
        return [tuple(p) for p in pts]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for k in range(n):
            t = k / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append(tuple(q))
    out.append(tuple(pts[-1]))
    return out


def cut(pts, frac):
    """first frac of polyline"""
    if frac >= 1:
        return list(pts)
    L = polyline_len(pts) * max(frac, 0)
    out = [pts[0]]
    acc = 0
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if acc + d >= L:
            t = (L - acc) / d if d else 0
            out.append((lerp(pts[i][0], pts[i + 1][0], t), lerp(pts[i][1], pts[i + 1][1], t)))
            return out
        acc += d
        out.append(pts[i + 1])
    return out


def path(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)


def arrow(ctx, pts, prog, color, width=34, alpha=1.0, head=1.9, glow=True, dark=None, smooth_n=12, outline=True):
    """Thick tapered campaign arrow along control points, drawn up to prog (0..1)."""
    if prog <= 0.001 or alpha <= 0:
        return
    sp = smooth(pts, smooth_n)
    seg = cut(sp, prog)
    if len(seg) < 2:
        return
    hx, hy = seg[-1]
    # direction at tip
    k = len(seg) - 2
    while k > 0 and math.dist(seg[k], seg[-1]) < width * 0.8:
        k -= 1
    dx, dy = hx - seg[k][0], hy - seg[k][1]
    dl = math.hypot(dx, dy) or 1
    dx, dy = dx / dl, dy / dl
    hl = width * head
    body_end = (hx - dx * hl * 0.85, hy - dy * hl * 0.85)
    body = cut(seg, max(0, (polyline_len(seg) - hl * 0.85) / max(polyline_len(seg), 1)))
    if len(body) < 2:
        body = [seg[0], body_end]
    # tapered body as polygon
    n = len(body)
    left, right = [], []
    for i, p in enumerate(body):
        a = body[max(i - 1, 0)]; b = body[min(i + 1, n - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = -ty / tl, tx / tl
        wv = width * (0.45 + 0.55 * (i / max(n - 1, 1))) / 2
        left.append((p[0] + nx * wv, p[1] + ny * wv)); right.append((p[0] - nx * wv, p[1] - ny * wv))
    nx, ny = -dy, dx
    hw = width * 1.05
    tip = [(body[-1][0] + nx * hw, body[-1][1] + ny * hw), (hx + dx * hl * 0.15, hy + dy * hl * 0.15),
           (body[-1][0] - nx * hw, body[-1][1] - ny * hw)]
    poly = left + tip + right[::-1]

    def fill_poly():
        ctx.move_to(*poly[0])
        for p in poly[1:]:
            ctx.line_to(*p)
        ctx.close_path()

    if glow:
        for gw, ga in ((26, 0.06), (14, 0.10), (6, 0.16)):
            fill_poly(); ctx.set_source_rgba(*color, ga * alpha); ctx.set_line_width(gw)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    fill_poly()
    g = cairo.LinearGradient(body[0][0], body[0][1], hx, hy)
    d = dark or tuple(c * 0.6 for c in color)
    g.add_color_stop_rgba(0, *d, 0.55 * alpha)
    g.add_color_stop_rgba(1, *color, 0.95 * alpha)
    ctx.set_source(g)
    ctx.fill_preserve()
    if outline:
        ctx.set_source_rgba(1, 1, 1, 0.35 * alpha); ctx.set_line_width(2); ctx.stroke()
    else:
        ctx.new_path()


def dashed(ctx, pts, prog, color, width=8, alpha=1.0, dash=(22, 16), smooth_n=12, offset=0):
    if prog <= 0:
        return
    seg = cut(smooth(pts, smooth_n), prog)
    if len(seg) < 2:
        return
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    path(ctx, seg); ctx.set_source_rgba(*color, 0.18 * alpha); ctx.set_line_width(width * 3); ctx.stroke()
    ctx.set_dash(dash, offset)
    path(ctx, seg); ctx.set_source_rgba(*color, alpha); ctx.set_line_width(width); ctx.stroke()
    ctx.restore()
    # small head
    if prog > 0.02:
        hx, hy = seg[-1]; px, py = seg[max(0, len(seg) - 4)]
        a = math.atan2(hy - py, hx - px)
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(a)
        ctx.move_to(width * 2.2, 0); ctx.line_to(-width * 1.2, width * 1.6); ctx.line_to(-width * 1.2, -width * 1.6); ctx.close_path()
        ctx.set_source_rgba(*color, alpha); ctx.fill(); ctx.restore()


def label(ctx, s, x, y, size=30, color=IVORY, alpha=1.0, anchor="mm", bold=False, dot=None, dot_r=9):
    if alpha <= 0:
        return
    if dot is not None:
        ctx.arc(x, y, dot_r + 3, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.6 * alpha); ctx.fill()
        ctx.arc(x, y, dot_r, 0, 2 * math.pi); ctx.set_source_rgba(*dot, alpha); ctx.fill()
    text(ctx, s, x, y, size, color, alpha, anchor, bold=bold, halo=size * 0.28, halo_a=0.85)


def unit_block(ctx, x, y, w, h, color, alpha=1.0, angle=0.0, kind="inf"):
    """NATO-ish block: rectangle; inf = X cross, cav = single diagonal, art = dot"""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.rotate(angle)
    ctx.rectangle(-w / 2 - 3, -h / 2 - 3, w + 6, h + 6); ctx.set_source_rgba(0, 0, 0, 0.45 * alpha); ctx.fill()
    ctx.rectangle(-w / 2, -h / 2, w, h); ctx.set_source_rgba(*color, 0.92 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.75 * alpha); ctx.set_line_width(2); ctx.stroke()
    ctx.set_line_width(2.2)
    if kind == "inf":
        ctx.move_to(-w / 2, -h / 2); ctx.line_to(w / 2, h / 2); ctx.move_to(-w / 2, h / 2); ctx.line_to(w / 2, -h / 2); ctx.stroke()
    elif kind == "cav":
        ctx.move_to(-w / 2, h / 2); ctx.line_to(w / 2, -h / 2); ctx.stroke()
    elif kind == "art":
        ctx.arc(0, 0, min(w, h) * 0.22, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.85 * alpha); ctx.fill()
    ctx.restore()


def vignette_surface(strength=0.75):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.58)) ** 2)
    a = np.clip((d - 0.55) / 0.6, 0, 1) ** 1.6 * strength
    arr = np.zeros((H, W, 4), np.float32); arr[..., 3] = a
    return surface_from_rgba(arr)


def paint_surface(ctx, surf, x=0, y=0, alpha=1.0, scale=1.0):
    if alpha <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    if scale != 1.0:
        ctx.scale(scale, scale)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


def fill_bg(ctx, color=BG, alpha=1.0):
    ctx.set_source_rgba(*color, alpha); ctx.paint()
