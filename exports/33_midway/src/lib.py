# -*- coding: utf-8 -*-
"""Drawing helpers (pycairo) for the Midway video. 1080x1920 portrait."""
import math, json, os, functools
import numpy as np
import cairo

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = "Noto Serif CJK SC"
SANS = "Noto Sans CJK SC"

# palette
BG0 = (0.035, 0.055, 0.085)
BG1 = (0.06, 0.10, 0.15)
SEA = (0.05, 0.11, 0.17)
LAND = (0.16, 0.18, 0.17)
LAND_EDGE = (0.42, 0.46, 0.44)
US = (0.30, 0.66, 1.00)      # cold blue
US_D = (0.12, 0.35, 0.62)
JP = (0.72, 0.20, 0.17)      # dark red
JP_D = (0.42, 0.12, 0.10)
GOLD = (0.93, 0.78, 0.45)
WHITE = (0.95, 0.95, 0.93)
GREY = (0.62, 0.64, 0.66)
RED = (0.92, 0.18, 0.14)
FIRE = (1.0, 0.55, 0.12)
PAPER = (0.90, 0.85, 0.74)
INK = (0.13, 0.11, 0.09)


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ease(x):
    x = clamp(x); return x * x * (3 - 2 * x)

def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_in(x):
    x = clamp(x); return x ** 3

def ramp(t, t0, dur):
    return ease((t - t0) / dur) if dur > 0 else float(t >= t0)

def lerp(a, b, u):
    return a + (b - a) * u

def mix(c1, c2, u):
    return tuple(lerp(a, b, u) for a, b in zip(c1, c2))

def rgba(ctx, c, a=1.0):
    if len(c) == 4:
        ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)
    else:
        ctx.set_source_rgba(c[0], c[1], c[2], a)


# ---------------------------------------------------------------- text
_measure_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)

def set_font(ctx, size, font=SERIF, bold=True):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)

def text_w(s, size, font=SERIF, bold=True):
    c = cairo.Context(_measure_surf); set_font(c, size, font, bold)
    return c.text_extents(s).x_advance

def text(ctx, s, x, y, size, color=WHITE, a=1.0, font=SERIF, bold=True, align="c", stroke=0, stroke_c=(0, 0, 0), spacing=0.0, glow=0):
    """y is the baseline. align c/l/r."""
    if a <= 0.003 or not s:
        return 0
    set_font(ctx, size, font, bold)
    if spacing:
        widths = [ctx.text_extents(ch).x_advance for ch in s]
        tw = sum(widths) + spacing * size * (len(s) - 1)
    else:
        tw = ctx.text_extents(s).x_advance
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
    def path():
        ctx.new_path()
        if spacing:
            xx = x0
            for ch, wd in zip(s, widths):
                ctx.move_to(xx, y); ctx.text_path(ch); xx += wd + spacing * size
        else:
            ctx.move_to(x0, y); ctx.text_path(s)
    if glow:
        for r, ga in ((glow, 0.10), (glow * 0.55, 0.16)):
            path(); rgba(ctx, color, a * ga); ctx.set_line_width(r); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    if stroke:
        path(); rgba(ctx, stroke_c, a * 0.9); ctx.set_line_width(stroke); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    path(); rgba(ctx, color, a); ctx.fill()
    return tw


def wrap_cn(s, maxw, size, font=SERIF, bold=True):
    """Greedy wrap for Chinese text; avoid line-start punctuation."""
    lines, cur = [], ""
    for ch in s:
        if text_w(cur + ch, size, font, bold) > maxw and cur:
            if ch in "，。！？、：；」』）》,.!?" :
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def para(ctx, s, x, y, maxw, size, color=WHITE, a=1.0, font=SERIF, bold=True, lh=1.45, align="c", **kw):
    ls = wrap_cn(s, maxw, size, font, bold)
    for i, l in enumerate(ls):
        text(ctx, l, x, y + i * size * lh, size, color, a, font, bold, align, **kw)
    return len(ls) * size * lh


# ---------------------------------------------------------------- shapes
def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def panel(ctx, x, y, w, h, a=1.0, fill=(0.03, 0.05, 0.08), alpha=0.78, edge=GOLD, ea=0.55, r=14):
    rrect(ctx, x, y, w, h, r); rgba(ctx, fill, alpha * a); ctx.fill_preserve()
    rgba(ctx, edge, ea * a); ctx.set_line_width(2); ctx.stroke()


def bezier_pts(p0, p1, p2, n=80):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = map(np.array, (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def poly_pts(pts, n=120):
    """Resample a polyline to n points along length."""
    pts = np.asarray(pts, float)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    s = np.linspace(0, d[-1], n)
    return np.c_[np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])]


def arrow(ctx, pts, prog, color, width=46, a=1.0, head=1.9, tail_w=0.45, outline=True, glow=True):
    """Thick tapered campaign arrow along pts (Nx2), drawn up to prog in [0,1]."""
    if prog <= 0.01 or a <= 0:
        return
    pts = np.asarray(pts, float)
    n = max(2, int(len(pts) * clamp(prog)))
    P = pts[:n]
    seg = np.diff(P, axis=0); L = np.hypot(seg[:, 0], seg[:, 1]); L[L == 0] = 1e-6
    tang = np.vstack([seg / L[:, None], seg[-1:] / L[-1]])
    nrm = np.c_[-tang[:, 1], tang[:, 0]]
    cum = np.r_[0, np.cumsum(L)]; tot = cum[-1] if cum[-1] > 0 else 1
    hl = min(width * head * 1.1, tot * 0.45)
    body_end = cum <= tot - hl
    if body_end.sum() < 2:
        body_end[:2] = True
    wd = width * (tail_w + (1 - tail_w) * (cum / tot)) / 2
    B = P[body_end]; Wd = wd[body_end]; N = nrm[body_end]
    left = B + N * Wd[:, None]; right = B - N * Wd[:, None]
    tip = P[-1]; t_dir = tang[-1]; tn = np.array([-t_dir[1], t_dir[0]])
    base = tip - t_dir * hl
    hw = width * head / 2
    def path():
        ctx.new_path()
        ctx.move_to(*left[0])
        for p in left[1:]:
            ctx.line_to(*p)
        ctx.line_to(*(base + tn * wd[-1]))
        ctx.line_to(*(base + tn * hw)); ctx.line_to(*tip); ctx.line_to(*(base - tn * hw))
        ctx.line_to(*(base - tn * wd[-1]))
        for p in right[::-1]:
            ctx.line_to(*p)
        ctx.close_path()
    if glow:
        path(); rgba(ctx, color, 0.22 * a); ctx.set_line_width(18); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    path()
    g = cairo.LinearGradient(*P[0], *tip)
    g.add_color_stop_rgba(0, *color[:3], 0.25 * a); g.add_color_stop_rgba(0.5, *color[:3], 0.8 * a); g.add_color_stop_rgba(1, *color[:3], 0.98 * a)
    ctx.set_source(g); ctx.fill_preserve()
    if outline:
        rgba(ctx, (1, 1, 1), 0.55 * a); ctx.set_line_width(2.2); ctx.stroke()
    else:
        ctx.new_path()


def dashed_line(ctx, pts, color, a=1.0, w=3, dash=(14, 10), prog=1.0):
    pts = np.asarray(pts, float); n = max(2, int(len(pts) * clamp(prog)))
    ctx.new_path(); ctx.move_to(*pts[0])
    for p in pts[1:n]:
        ctx.line_to(*p)
    ctx.set_dash(dash); rgba(ctx, color, a); ctx.set_line_width(w); ctx.stroke(); ctx.set_dash([])


def carrier_top(ctx, x, y, ang, s=1.0, color=JP, a=1.0, fire=0.0, t=0.0, dim=0.0):
    """Top-down flat-top: hull in faction color, wooden flight deck, island. Length ~130*s px."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s)
    L, Wd = 64, 15
    c = mix(color, (0.15, 0.15, 0.15), dim)
    ctx.new_path()
    ctx.move_to(-L, -Wd * 0.75); ctx.line_to(L * 0.7, -Wd * 0.85); ctx.curve_to(L * 0.95, -Wd * 0.7, L * 1.05, -4, L * 1.08, 0)
    ctx.curve_to(L * 1.05, 4, L * 0.95, Wd * 0.7, L * 0.7, Wd * 0.85); ctx.line_to(-L, Wd * 0.75); ctx.close_path()
    rgba(ctx, mix(c, (0, 0, 0), 0.25), 0.97 * a); ctx.fill()
    # flight deck
    ctx.rectangle(-L * 1.02, -Wd * 0.95, L * 1.9, Wd * 1.9)
    deck = mix((0.50, 0.40, 0.30), c, 0.25)
    deck = mix(deck, (0.12, 0.12, 0.12), dim)
    rgba(ctx, deck, a); ctx.fill_preserve(); rgba(ctx, c, a); ctx.set_line_width(3.0 / max(s, 0.3)); ctx.stroke()
    # deck markings
    for xx in (-L * 0.55, L * 0.45):
        ctx.rectangle(xx - 6, -6, 12, 12); rgba(ctx, (0.25, 0.2, 0.15), 0.8 * a); ctx.fill()
    ctx.move_to(-L * 0.95, 0); ctx.line_to(L * 0.85, 0); rgba(ctx, (1, 1, 1), 0.35 * a); ctx.set_line_width(1.2 / max(s, 0.3)); ctx.set_dash([6, 5]); ctx.stroke(); ctx.set_dash([])
    # island
    ctx.rectangle(0, -Wd * 0.95 - 7, 16, 7); rgba(ctx, (0.22, 0.22, 0.24), a); ctx.fill()
    ctx.restore()
    if fire > 0:
        fire_blob(ctx, x, y, 38 * s * (0.6 + 0.4 * fire), fire * a, t)


def fire_blob(ctx, x, y, r, a, t, seed=0):
    rng = np.random.default_rng(seed + int(x * 7 + y * 13))
    for k in range(7):
        ph = rng.uniform(0, 6.28); dx = rng.uniform(-0.8, 0.8) * r; dy = rng.uniform(-0.3, 0.3) * r
        rr = r * (0.45 + 0.35 * math.sin(t * rng.uniform(4, 9) + ph) ** 2)
        g = cairo.RadialGradient(x + dx, y + dy, 0, x + dx, y + dy, rr)
        g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.9 * a); g.add_color_stop_rgba(0.35, 1, 0.55, 0.12, 0.7 * a); g.add_color_stop_rgba(1, 0.6, 0.1, 0.0, 0)
        ctx.set_source(g); ctx.arc(x + dx, y + dy, rr, 0, 6.29); ctx.fill()
    # smoke
    for k in range(5):
        ph = (t * 0.25 + k / 5) % 1
        sx = x + 0.6 * r * math.sin(k * 2.1) + ph * r * 1.6; sy = y - ph * r * 2.4
        rr = r * (0.4 + ph * 1.1)
        g = cairo.RadialGradient(sx, sy, 0, sx, sy, rr)
        g.add_color_stop_rgba(0, 0.12, 0.11, 0.10, 0.45 * a * (1 - ph)); g.add_color_stop_rgba(1, 0.1, 0.1, 0.1, 0)
        ctx.set_source(g); ctx.arc(sx, sy, rr, 0, 6.29); ctx.fill()


def plane_top(ctx, x, y, ang, s=1.0, color=US, a=1.0):
    """Simple single-engine plane silhouette (top view), pointing at ang."""
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s)
    ctx.new_path()
    ctx.move_to(14, 0); ctx.curve_to(12, -2, 6, -2.4, 2, -2.4); ctx.line_to(1, -17); ctx.line_to(-3, -17); ctx.line_to(-4, -2.4)
    ctx.line_to(-11, -2); ctx.line_to(-13, -7); ctx.line_to(-15, -7); ctx.line_to(-15, 7); ctx.line_to(-13, 7); ctx.line_to(-11, 2)
    ctx.line_to(-4, 2.4); ctx.line_to(-3, 17); ctx.line_to(1, 17); ctx.line_to(2, 2.4); ctx.curve_to(6, 2.4, 12, 2, 14, 0); ctx.close_path()
    rgba(ctx, color, a); ctx.fill_preserve(); rgba(ctx, (0, 0, 0), 0.5 * a); ctx.set_line_width(0.8); ctx.stroke()
    ctx.restore()


def plane_side(ctx, x, y, s=1.0, color=US, a=1.0, flip=False, pitch=0.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(pitch)
    if flip:
        ctx.scale(-s, s)
    else:
        ctx.scale(s, s)
    ctx.new_path()
    ctx.move_to(22, 0); ctx.curve_to(20, -4, 10, -5, 0, -4.5); ctx.line_to(-16, -3); ctx.line_to(-22, -11); ctx.line_to(-25, -11)
    ctx.line_to(-24, 2); ctx.line_to(-10, 3); ctx.line_to(8, 4); ctx.curve_to(16, 4, 21, 3, 22, 0); ctx.close_path()
    rgba(ctx, color, a); ctx.fill()
    ctx.rectangle(-3, -0.5, 10, 3); rgba(ctx, mix(color, (0, 0, 0), 0.4), a); ctx.fill()
    ctx.restore()


def wake(ctx, pts, a=1.0, w=10):
    """White wake behind a ship path (pts oldest→newest)."""
    pts = np.asarray(pts, float)
    if len(pts) < 2:
        return
    n = len(pts)
    for i in range(1, n):
        u = i / n
        ctx.move_to(*pts[i - 1]); ctx.line_to(*pts[i])
        rgba(ctx, (0.92, 0.96, 1.0), a * 0.55 * u); ctx.set_line_width(w * (0.4 + 0.9 * u)); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def xmark(ctx, x, y, r, a, color=RED, w=7):
    ctx.move_to(x - r, y - r); ctx.line_to(x + r, y + r); ctx.move_to(x + r, y - r); ctx.line_to(x - r, y + r)
    rgba(ctx, color, a); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def vignette(ctx, strength=0.65):
    g = cairo.RadialGradient(W / 2, H * 0.45, H * 0.25, W / 2, H * 0.45, H * 0.75)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, strength)
    ctx.set_source(g); ctx.paint()


# ---------------------------------------------------------------- textures
def _fbm(h, w, seed, octaves=6, base=4):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        f = base * 2 ** o
        g = rng.random((f + 1, int(f * w / h) + 2)).astype(np.float32)
        ys = np.linspace(0, f, h); xs = np.linspace(0, int(f * w / h) + 1 - 1e-3, w)
        y0 = ys.astype(int); x0 = xs.astype(int); fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        y1 = np.minimum(y0 + 1, g.shape[0] - 1); x1 = np.minimum(x0 + 1, g.shape[1] - 1)
        v = (g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx) * (1 - fy) + (g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx) * fy
        out += amp * v; tot += amp; amp *= 0.5
    return out / tot


def surf_from_rgba(arr):
    """arr HxWx4 float 0..1 straight alpha -> cairo surface (premultiplied BGRA)."""
    h, w = arr.shape[:2]
    a = arr[..., 3:4]
    pm = np.concatenate([arr[..., 2:3] * a, arr[..., 1:2] * a, arr[..., 0:1] * a, a], axis=2)
    buf = np.ascontiguousarray((pm * 255).clip(0, 255).astype(np.uint8))
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    st = s.get_stride()
    dst = np.ndarray((h, st), np.uint8, s.get_data())
    dst[:, :w * 4] = buf.reshape(h, w * 4)
    s.mark_dirty()
    return s


@functools.lru_cache(maxsize=None)
def cloud_tex(seed, w=1400, h=1400, cover=0.5):
    n = _fbm(h // 2, w // 2, seed, 7, 3)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    d = np.clip((n - (1 - cover) * 0.75 - 0.18) * 3.2, 0, 1)
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    d = d * np.clip((1 - rr) * 2.2, 0, 1) ** 1.2
    shade = 0.78 + 0.22 * np.clip((n - 0.4) * 2, 0, 1)
    arr = np.dstack([shade * 0.92, shade * 0.95, shade, d * 0.95]).astype(np.float32)
    return surf_from_rgba(arr)


@functools.lru_cache(maxsize=None)
def sea_tex(seed=3, w=1300, h=2200):
    n = _fbm(h // 2, w // 2, seed, 6, 6)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)
    v = (n - 0.5)
    arr = np.dstack([0.05 + v * 0.05, 0.12 + v * 0.08, 0.18 + v * 0.10, np.ones_like(v)]).astype(np.float32)
    return surf_from_rgba(arr)


@functools.lru_cache(maxsize=None)
def paper_tex(w=900, h=1100, seed=7, tint=PAPER):
    n = _fbm(h, w, seed, 6, 5)
    rng = np.random.default_rng(seed); fine = rng.random((h, w)).astype(np.float32)
    v = 0.86 + 0.14 * n + 0.04 * (fine - 0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy]).astype(np.float32)
    burn = np.clip(edge / 40, 0, 1) ** 0.6
    v = v * (0.75 + 0.25 * burn)
    arr = np.dstack([tint[0] * v, tint[1] * v, tint[2] * v, np.ones_like(v)]).astype(np.float32)
    return surf_from_rgba(arr)


@functools.lru_cache(maxsize=None)
def grain_tex(seed):
    rng = np.random.default_rng(seed)
    g = rng.random((H // 2, W // 2)).astype(np.float32)
    arr = np.dstack([g, g, g, np.full_like(g, 0.05)])
    return surf_from_rgba(arr)


def paint_surface(ctx, s, x, y, scale=1.0, a=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(scale, scale); ctx.set_source_surface(s, 0, 0)
    ctx.paint_with_alpha(a); ctx.restore()


def grain(ctx, fi):
    ctx.save(); ctx.scale(2, 2); ctx.set_source_surface(grain_tex(fi % 6), 0, 0)
    ctx.set_operator(cairo.OPERATOR_OVERLAY); ctx.paint(); ctx.restore()


# ---------------------------------------------------------------- map
_LAND = None

def land():
    global _LAND
    if _LAND is None:
        _LAND = [np.array(r, float) for r in json.load(open(os.path.join(HERE, "..", "geo", "pacific.json")))]
    return _LAND


class Cam:
    """Equirectangular w/ cos(lat0) scaling. center lon/lat, k = px per degree lat."""
    def __init__(self, lon, lat, k, cx=W / 2, cy=860, lat0=30):
        self.lon, self.lat, self.k, self.cx, self.cy = lon, lat, k, cx, cy
        self.c = math.cos(math.radians(lat0))

    def p(self, lon, lat):
        return (self.cx + (lon - self.lon) * self.k * self.c, self.cy - (lat - self.lat) * self.k)

    def pa(self, arr):
        arr = np.asarray(arr, float)
        return np.c_[self.cx + (arr[:, 0] - self.lon) * self.k * self.c, self.cy - (arr[:, 1] - self.lat) * self.k]


def cam_lerp(a, b, u):
    u = ease(u)
    # interpolate zoom in log space
    k = math.exp(lerp(math.log(a.k), math.log(b.k), u))
    return Cam(lerp(a.lon, b.lon, u), lerp(a.lat, b.lat, u), k, lerp(a.cx, b.cx, u), lerp(a.cy, b.cy, u))


def draw_map(ctx, cam, a=1.0, grid=True, top=250, bottom=1480, t=0.0):
    ctx.save()
    ctx.rectangle(0, top, W, bottom - top); ctx.clip()
    # sea
    paint_surface(ctx, sea_tex(), -100 - (t * 3) % 50, top - 100, 1.0, a)
    rgba(ctx, (0.02, 0.06, 0.11), 0.35 * a); ctx.paint()
    if grid:
        ctx.set_line_width(1)
        step = 5 if cam.k > 30 else 10
        lon0 = math.floor((cam.lon - W / (cam.k * cam.c) / 2) / step) * step
        for lon in np.arange(lon0, lon0 + W / (cam.k * cam.c) + 2 * step, step):
            x, _ = cam.p(lon, 0); ctx.move_to(x, top); ctx.line_to(x, bottom)
        lat0 = math.floor((cam.lat - (bottom - top) / cam.k) / step) * step
        for lat in np.arange(lat0, lat0 + 2 * (bottom - top) / cam.k + step, step):
            _, y = cam.p(0, lat); ctx.move_to(0, y); ctx.line_to(W, y)
        rgba(ctx, (0.55, 0.7, 0.85), 0.10 * a); ctx.stroke()
    # land
    lonmin = cam.lon - W / (cam.k * cam.c) / 2 - 2; lonmax = cam.lon + W / (cam.k * cam.c) / 2 + 2
    latmin = cam.lat - (bottom - cam.cy) / cam.k - 2; latmax = cam.lat + (cam.cy - top) / cam.k + 2
    ctx.new_path()
    for r in land():
        if r[:, 0].max() < lonmin or r[:, 0].min() > lonmax or r[:, 1].max() < latmin or r[:, 1].min() > latmax:
            continue
        P = cam.pa(r)
        if np.ptp(P[:, 0]) < 1.2 and np.ptp(P[:, 1]) < 1.2:
            ctx.rectangle(P[0, 0] - 1, P[0, 1] - 1, 2.4, 2.4); continue
        step = max(1, int(len(P) / 1500))
        ctx.move_to(*P[0])
        for q in P[1::step]:
            ctx.line_to(*q)
        ctx.close_path()
    rgba(ctx, LAND, 0.96 * a); ctx.fill_preserve(); rgba(ctx, LAND_EDGE, 0.8 * a); ctx.set_line_width(1.3); ctx.stroke()
    ctx.restore()


def map_frame(ctx, top=250, bottom=1480, a=1.0, label="示意"):
    ctx.rectangle(18, top + 2, W - 36, bottom - top - 4); rgba(ctx, GOLD, 0.35 * a); ctx.set_line_width(1.5); ctx.stroke()
    # fade edges
    for y0, y1 in ((top, top + 60), (bottom, bottom - 60)):
        g = cairo.LinearGradient(0, y0, 0, y1); g.add_color_stop_rgba(0, *BG0, a); g.add_color_stop_rgba(1, *BG0, 0)
        ctx.set_source(g); ctx.rectangle(0, min(y0, y1), W, abs(y1 - y0)); ctx.fill()
    if label:
        text(ctx, label, W - 40, bottom - 22, 24, GREY, 0.85 * a, SANS, False, "r")


def pin(ctx, x, y, label, a=1.0, color=GOLD, size=34, dx=18, dy=-14, align="l", r=7):
    if a <= 0:
        return
    ctx.arc(x, y, r + 5, 0, 6.29); rgba(ctx, color, 0.25 * a); ctx.fill()
    ctx.arc(x, y, r, 0, 6.29); rgba(ctx, color, a); ctx.fill()
    text(ctx, label, x + dx, y + dy, size, WHITE, a, SERIF, True, align, stroke=6, stroke_c=(0, 0, 0))
