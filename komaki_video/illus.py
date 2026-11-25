# -*- coding: utf-8 -*-
"""Sengoku-style silhouette illustration kit (情景示意): skies, earthworks, banners, ashigaru, riders,
forest, smoke & muzzle flashes, golden-fan standard, castle silhouette. Banners are plain colour fields —
no crests, no sun discs, no radiating patterns."""
import math
import numpy as np
import cairo
from gfx import *

_C = {}
SIL = (0.035, 0.035, 0.045)


def _grad_sky(stops, key, seed=3, cloud=0.25, glow=None):
    if key in _C:
        return _C[key]
    rng = np.random.default_rng(seed)
    y = np.linspace(0, 1, H)
    col = np.zeros((H, 3), np.float32)
    for i in range(len(stops) - 1):
        (p0, c0), (p1, c1) = stops[i], stops[i + 1]
        m = (y >= p0) & (y <= p1)
        t = ((y[m] - p0) / (p1 - p0))[:, None]
        col[m] = np.array(c0) * (1 - t) + np.array(c1) * t
    sky = np.broadcast_to(col[:, None, :], (H, W, 3)).copy()
    if cloud:
        cl = noise2d(H, W, 140, rng, 4)
        sky *= (1 - cloud / 2 + cloud * cl[..., None])
    if glow:
        gx, gy, gr, gc = glow
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt((xx - gx) ** 2 + (yy - gy) ** 2)
        sky += np.exp(-d / gr)[..., None] * np.array(gc)
    _C[key] = surface_from_rgb(np.clip(sky, 0, 1).astype(np.float32))
    return _C[key]


def sky(kind):
    if kind == "plain":     # overcast plain, cold dawn
        return _grad_sky([(0, (0.05, 0.06, 0.08)), (0.30, (0.20, 0.23, 0.27)), (0.48, (0.42, 0.42, 0.40)), (1, (0.10, 0.10, 0.10))],
                         "plain", glow=(760, 760, 340, (0.22, 0.18, 0.12)))
    if kind == "forest":    # misty morning in the woods
        return _grad_sky([(0, (0.06, 0.08, 0.09)), (0.35, (0.24, 0.29, 0.30)), (0.55, (0.36, 0.40, 0.38)), (1, (0.08, 0.09, 0.08))],
                         "forest", seed=5, glow=(300, 600, 420, (0.30, 0.27, 0.18)))
    if kind == "hill":      # hazy late morning, hill top
        return _grad_sky([(0, (0.07, 0.07, 0.09)), (0.32, (0.30, 0.27, 0.24)), (0.50, (0.62, 0.52, 0.38)), (1, (0.10, 0.08, 0.06))],
                         "hill", seed=8, glow=(700, 700, 360, (0.40, 0.30, 0.12)))
    if kind == "dusk":      # Osaka silhouette
        return _grad_sky([(0, (0.03, 0.03, 0.05)), (0.30, (0.14, 0.09, 0.08)), (0.50, (0.55, 0.30, 0.12)), (0.56, (0.70, 0.42, 0.16)), (1, (0.05, 0.04, 0.04))],
                         "dusk", seed=9, cloud=0.18, glow=(540, 1000, 300, (0.45, 0.25, 0.08)))
    raise KeyError(kind)


# ---------------------------------------------------------------- figures
def ashigaru(ctx, x, y, s, phase=0.0, flag=RED, weapon="yari", facing=1, alpha=1.0, run=0.0, lean=0.0, aim=False, col=SIL):
    """foot soldier silhouette, feet at (x,y), height ~150*s; conical jingasa hat, small back banner."""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s * facing, s); ctx.rotate(lean + run * 0.18)
    ctx.set_source_rgba(*col, alpha)
    sw = math.sin(phase) * (8 + 16 * run)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(10)
    ctx.move_to(-3, -60); ctx.line_to(-4 + sw, -2); ctx.stroke()
    ctx.move_to(3, -60); ctx.line_to(4 - sw, -2); ctx.stroke()
    # body (do armour skirt flares)
    ctx.move_to(-13, -110); ctx.line_to(13, -110); ctx.line_to(22, -56); ctx.line_to(-22, -56); ctx.close_path(); ctx.fill()
    # head + jingasa
    ctx.arc(0, -119, 9, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(-24, -121); ctx.line_to(0, -138); ctx.line_to(24, -121); ctx.close_path(); ctx.fill()
    # sashimono: pole + small flag on the back
    ctx.set_line_width(2.5); ctx.move_to(-10, -100); ctx.line_to(-12, -178); ctx.stroke()
    fl = 1.0 + 0.08 * math.sin(phase * 1.7)
    ctx.move_to(-12, -178); ctx.line_to(-12 - 26 * fl, -176); ctx.line_to(-12 - 25 * fl, -140); ctx.line_to(-12, -142); ctx.close_path()
    ctx.set_source_rgba(*flag, alpha); ctx.fill()
    ctx.set_source_rgba(*col, alpha)
    ctx.set_line_width(4)
    if weapon == "yari":
        ctx.move_to(6, -40); ctx.line_to(30, -230); ctx.stroke()
        ctx.move_to(30, -230); ctx.line_to(33, -252); ctx.set_line_width(3); ctx.stroke()
    elif weapon == "teppo":
        if aim:
            ctx.move_to(-4, -100); ctx.line_to(70, -104); ctx.stroke()
        else:
            ctx.move_to(-4, -60); ctx.line_to(26, -170); ctx.stroke()
    ctx.restore()


def rider(ctx, x, y, s, phase=0.0, flag=BLU, facing=1, alpha=1.0, col=SIL, gallop=1.0):
    """mounted samurai silhouette at ground (x,y), ~ 230*s tall"""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s * facing, s)
    ctx.set_source_rgba(*col, alpha)
    b = math.sin(phase) * 6 * gallop
    ctx.translate(0, -b)
    # horse body
    ctx.save(); ctx.translate(0, -95); ctx.scale(1.0, 0.55); ctx.arc(0, 0, 62, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    # neck + head
    ctx.move_to(40, -120); ctx.line_to(78, -175); ctx.line_to(108, -160); ctx.line_to(100, -146); ctx.line_to(70, -140); ctx.line_to(52, -95); ctx.close_path(); ctx.fill()
    # legs
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_width(10)
    for i, (lx, ph) in enumerate(((-40, 0), (-28, 2.2), (32, 1.1), (44, 3.3))):
        a = math.sin(phase + ph) * 0.6 * gallop
        ctx.move_to(lx, -80); ctx.line_to(lx + math.sin(a) * 50, -80 + math.cos(a) * 78 + b); ctx.stroke()
    # tail
    ctx.set_line_width(7); ctx.move_to(-58, -110); ctx.curve_to(-85, -100, -92, -70, -96, -50 + 8 * math.sin(phase)); ctx.stroke()
    # rider
    ctx.move_to(-16, -130); ctx.line_to(16, -130); ctx.line_to(12, -190); ctx.line_to(-12, -190); ctx.close_path(); ctx.fill()
    ctx.arc(0, -200, 11, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(-15, -204); ctx.line_to(0, -222); ctx.line_to(15, -204); ctx.close_path(); ctx.fill()     # kabuto
    ctx.set_line_width(4); ctx.move_to(8, -175); ctx.line_to(80, -250); ctx.stroke()                        # spear
    ctx.set_line_width(2.5); ctx.move_to(-10, -180); ctx.line_to(-12, -268); ctx.stroke()
    ctx.move_to(-12, -268); ctx.line_to(-44, -266); ctx.line_to(-43, -226); ctx.line_to(-12, -228); ctx.close_path()
    ctx.set_source_rgba(*flag, alpha); ctx.fill()
    ctx.restore()


def nobori(ctx, x, y, h, color, t, seed=0, alpha=1.0, wind=1.0):
    """tall vertical banner (nobori) on a pole; plain colour, flutters at the free edge"""
    if alpha <= 0:
        return
    w = h * 0.22
    ctx.save()
    ctx.set_source_rgba(*SIL, alpha); ctx.set_line_width(max(2, h * 0.018))
    ctx.move_to(x, y); ctx.line_to(x, y - h * 1.05); ctx.stroke()
    ctx.move_to(x, y - h * 1.02); ctx.line_to(x + w * 1.05, y - h * 1.02); ctx.stroke()
    top, bot = y - h * 1.0, y - h * 0.22
    n = 14
    pts = []
    for i in range(n + 1):
        u = i / n
        yy = lerp(top, bot, u)
        off = wind * w * 0.22 * math.sin(t * 5.2 + u * 5 + seed) * u
        pts.append((x + w + off, yy))
    ctx.move_to(x, top)
    for p in pts:
        ctx.line_to(*p)
    ctx.line_to(x, bot); ctx.close_path()
    g = cairo.LinearGradient(x, top, x + w, top)
    g.add_color_stop_rgba(0, *[c * 0.6 for c in color], alpha); g.add_color_stop_rgba(1, *color, alpha)
    ctx.set_source(g); ctx.fill()
    ctx.restore()


def earthwork(ctx, y, scale, color_flag, t, alpha=1.0, n_flags=9, seed=0, dark=0.0, x0=-40, x1=W + 40):
    """an earthen rampart (dorui) running across the frame with palisade and banners."""
    if alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    h = 46 * scale
    ctx.save()
    ctx.move_to(x0, y + h)
    xs = np.linspace(x0, x1, 40)
    for xv in xs:
        ctx.line_to(xv, y - h * 0.5 + math.sin(xv * 0.01 + seed) * h * 0.12)
    ctx.line_to(x1, y + h); ctx.close_path()
    c = 0.10 + 0.05 * (1 - dark)
    ctx.set_source_rgba(c, c * 0.9, c * 0.75, alpha); ctx.fill()
    # palisade
    ctx.set_source_rgba(*SIL, alpha); ctx.set_line_width(max(1.5, 4 * scale))
    for xv in np.arange(x0, x1, 22 * scale):
        yy = y - h * 0.5 + math.sin(xv * 0.01 + seed) * h * 0.12
        ctx.move_to(xv, yy); ctx.line_to(xv + rng.uniform(-2, 2), yy - 38 * scale);
    ctx.stroke()
    ctx.move_to(x0, y - h * 0.5 - 30 * scale); ctx.line_to(x1, y - h * 0.5 - 30 * scale); ctx.set_line_width(max(1, 3 * scale)); ctx.stroke()
    for i in range(n_flags):
        xv = lerp(x0 + 60, x1 - 60, (i + 0.5) / n_flags) + rng.uniform(-20, 20)
        yy = y - h * 0.5
        nobori(ctx, xv, yy, 200 * scale * rng.uniform(0.85, 1.1), color_flag, t, seed=i * 1.3 + seed, alpha=alpha)
    ctx.restore()


def pine(ctx, x, yb, h, seed=0, col=SIL, alpha=1.0, sway=0.0):
    """conical cedar (sugi) silhouette with ragged tiers"""
    rng = np.random.default_rng(seed)
    ctx.save(); ctx.set_source_rgba(*col, alpha)
    tw = max(3, h * 0.03)
    ctx.move_to(x - tw, yb); ctx.line_to(x - tw * 0.4 + sway, yb - h); ctx.line_to(x + tw * 0.4 + sway, yb - h); ctx.line_to(x + tw, yb); ctx.close_path(); ctx.fill()
    n = 9
    for k in range(n):
        u0 = 0.22 + k * 0.085
        cy = yb - h * u0
        half = h * 0.16 * (1 - k / n) + h * 0.02
        cx = x + sway * u0
        ctx.move_to(cx - half, cy + h * 0.02)
        steps = 6
        for i in range(steps + 1):
            px = cx - half + 2 * half * i / steps
            py = cy + h * 0.02 + rng.uniform(-h * 0.012, h * 0.012)
            ctx.line_to(px, py)
        ctx.line_to(cx + sway * 0.1, cy - h * 0.13)
        ctx.close_path(); ctx.fill()
    ctx.restore()


def fog(seed, alpha=0.5, color=(0.70, 0.72, 0.70), hh=700):
    key = f"fog{seed}"
    if key in _C:
        return _C[key]
    rng = np.random.default_rng(seed)
    w = W * 2
    n = blur(noise2d(hh, w, 120, rng, 5), 10)
    a = np.clip((n - 0.38) * 2.2, 0, 1) * alpha
    yy = np.linspace(0, 1, hh)[:, None]
    a *= np.clip(np.sin(yy * math.pi) * 1.5, 0, 1)
    arr = np.zeros((hh, w, 4), np.float32)
    arr[..., :3] = np.array(color)[None, None] * (0.85 + 0.3 * n[..., None])
    arr[..., 3] = a
    _C[key] = surface_from_rgba(arr)
    return _C[key]


def drift(ctx, surf, y, t, speed=12, alpha=1.0):
    if alpha <= 0:
        return
    w = surf.get_width()
    x = -((t * speed) % (w - W))
    ctx.set_source_surface(surf, x, y); ctx.paint_with_alpha(alpha)


def muzzle(ctx, x, y, age, facing=1, size=1.0):
    """flash at age 0..0.15, then fades"""
    if age < 0 or age > 0.35:
        return
    a = clamp(1 - age / 0.25)
    r = 46 * size * (0.6 + age * 3)
    g = cairo.RadialGradient(x + 20 * facing * size, y, 0, x + 20 * facing * size, y, r)
    g.add_color_stop_rgba(0, 1, 0.97, 0.80, a); g.add_color_stop_rgba(0.35, 1, 0.62, 0.22, 0.75 * a); g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
    ctx.set_source(g); ctx.arc(x + 20 * facing * size, y, r, 0, 2 * math.pi); ctx.fill()


def smoke_puffs(ctx, x, y, age, seed=0, size=1.0, facing=1, col=(0.78, 0.76, 0.72), dur=6.0):
    """white powder smoke expanding & drifting from a muzzle"""
    if age < 0 or age > dur:
        return
    rng = np.random.default_rng(seed)
    for k in range(6):
        a0 = rng.uniform(0, 0.15)
        aa = age - a0
        if aa < 0:
            continue
        u = 1 - math.exp(-aa * 1.6)
        px = x + facing * size * (30 + 110 * u * rng.uniform(0.6, 1.4)) + aa * 10 * size
        py = y - size * (10 + 40 * u * rng.uniform(0.2, 1.0))
        r = size * (14 + 70 * u * rng.uniform(0.7, 1.2))
        al = 0.55 * clamp(aa / 0.1) * clamp(1 - aa / dur) ** 1.3
        g = cairo.RadialGradient(px, py, 0, px, py, r)
        g.add_color_stop_rgba(0, *col, al); g.add_color_stop_rgba(1, *col, 0)
        ctx.set_source(g); ctx.arc(px, py, r, 0, 2 * math.pi); ctx.fill()


def golden_fan(ctx, x, y, s, t, alpha=1.0, glow=1.0):
    """Ieyasu's golden-fan standard (金扇の馬印): plain gold folding fan on a tall pole. No disc, no rays."""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if glow > 0:
        g = cairo.RadialGradient(0, -330, 0, 0, -330, 260)
        g.add_color_stop_rgba(0, 1, 0.85, 0.45, 0.45 * alpha * glow); g.add_color_stop_rgba(1, 1, 0.7, 0.3, 0)
        ctx.set_source(g); ctx.arc(0, -330, 260, 0, 2 * math.pi); ctx.fill()
    ctx.set_source_rgba(*SIL, alpha); ctx.set_line_width(7)
    ctx.move_to(0, 0); ctx.line_to(0, -300); ctx.stroke()
    sway = 0.04 * math.sin(t * 1.3)
    ctx.translate(0, -300); ctx.rotate(sway)
    a0, a1 = math.radians(-160), math.radians(-20)
    R, r = 170, 40
    ctx.move_to(math.cos(a0) * r, math.sin(a0) * r)
    ctx.arc(0, 0, R, a0, a1)
    ctx.arc_negative(0, 0, r, a1, a0)
    ctx.close_path()
    g = cairo.LinearGradient(-R, -R, R, 0)
    g.add_color_stop_rgba(0, 0.78, 0.56, 0.16, alpha); g.add_color_stop_rgba(0.5, 1.0, 0.86, 0.45, alpha); g.add_color_stop_rgba(1, 0.70, 0.48, 0.12, alpha)
    ctx.set_source(g); ctx.fill_preserve()
    ctx.set_source_rgba(0.35, 0.22, 0.05, 0.9 * alpha); ctx.set_line_width(3); ctx.stroke()
    ctx.set_line_width(2)
    for k in range(11):
        a = lerp(a0, a1, k / 10)
        ctx.move_to(math.cos(a) * r, math.sin(a) * r); ctx.line_to(math.cos(a) * R, math.sin(a) * R)
    ctx.set_source_rgba(0.45, 0.30, 0.08, 0.55 * alpha); ctx.stroke()
    ctx.arc(0, 0, 10, 0, 2 * math.pi); ctx.set_source_rgba(*SIL, alpha); ctx.fill()
    ctx.restore()


def castle(ctx, x, y, s, alpha=1.0, col=SIL, lit=0.0):
    """tenshu silhouette on stone base, base centre at (x,y)"""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.set_source_rgba(*col, alpha)
    ctx.move_to(-260, 0); ctx.curve_to(-230, -60, -210, -120, -200, -170); ctx.line_to(200, -170)
    ctx.curve_to(210, -120, 230, -60, 260, 0); ctx.close_path(); ctx.fill()
    yb = -170
    widths = [190, 160, 128, 96, 70]
    for i, w in enumerate(widths):
        hh = 62 if i < 4 else 70
        ctx.rectangle(-w * 0.82, yb - hh, w * 1.64, hh); ctx.fill()
        # curved eave
        ey = yb - hh + 6
        ctx.move_to(-w * 1.08, ey + 4); ctx.curve_to(-w * 0.7, ey - 10, w * 0.7, ey - 10, w * 1.08, ey + 4)
        ctx.line_to(w * 0.95, ey - 18); ctx.line_to(-w * 0.95, ey - 18); ctx.close_path(); ctx.fill()
        if lit > 0:
            for k in range(-2, 3):
                ctx.rectangle(k * w * 0.3 - 6, yb - hh * 0.6, 12, 16)
            ctx.set_source_rgba(1, 0.75, 0.35, lit * alpha * (0.5 + 0.1 * i)); ctx.fill(); ctx.set_source_rgba(*col, alpha)
        yb = ey - 18
    # roof cap
    ctx.move_to(-60, yb); ctx.curve_to(-30, yb - 30, 30, yb - 30, 60, yb); ctx.close_path(); ctx.fill()
    ctx.restore()


def hills(ctx, base_y, amp, col, seed=0, alpha=1.0, freq=0.006):
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6, 3)
    ctx.move_to(-10, H + 10)
    for x in range(-10, W + 30, 15):
        y = base_y - amp * (0.5 + 0.3 * math.sin(x * freq + ph[0]) + 0.15 * math.sin(x * freq * 2.7 + ph[1]) + 0.07 * math.sin(x * freq * 7 + ph[2]))
        ctx.line_to(x, y)
    ctx.line_to(W + 30, H + 10); ctx.close_path()
    ctx.set_source_rgba(*col, alpha); ctx.fill()


def particles(ctx, cx, cy, t, n, spread, color, seed=0, alpha=1.0, drift=(30, -20), r=5):
    """dissolving particles (units breaking up)"""
    if alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(0.3, 1.0)
        life = rng.uniform(0.6, 1.0)
        u = clamp(t / life)
        x = cx + math.cos(ang) * spread * sp * u + drift[0] * u
        y = cy + math.sin(ang) * spread * sp * u * 0.6 + drift[1] * u
        a = alpha * (1 - u) ** 0.8
        if a <= 0.01:
            continue
        ctx.rectangle(x - r / 2, y - r / 2, r, r); ctx.set_source_rgba(*color, a); ctx.fill()
