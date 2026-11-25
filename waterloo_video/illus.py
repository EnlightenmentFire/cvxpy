# -*- coding: utf-8 -*-
"""Painted-style illustration layers: dusk hillside with the Guard, rain & mud, courier, empty hill at sunset."""
import math
import numpy as np
import cairo
from gfx import *

_C = {}
CREST_X0, CREST_Y = 700, 830      # crest of the hill (right part of the frame)


def ground_y(x):
    """slope rising from lower-left to the crest at right"""
    if x >= CREST_X0:
        return CREST_Y + (x - CREST_X0) * 0.05
    return CREST_Y + (CREST_X0 - x) * 0.50


def dusk_bg(variant="battle"):
    key = "dusk_" + variant
    if key in _C:
        return _C[key]
    rng = np.random.default_rng(21)
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([0.05, 0.05, 0.07]); mid = np.array([0.42, 0.17, 0.08]); low = np.array([0.85, 0.45, 0.16])
    if variant == "calm":
        mid = np.array([0.40, 0.22, 0.14]); low = np.array([0.95, 0.62, 0.30])
    t = np.clip((y - 0.12) / 0.38, 0, 1)
    sky = top * (1 - t) + mid * t
    t2 = np.clip((y - 0.36) / 0.10, 0, 1)
    sky = sky * (1 - t2) + low * t2
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    # sun glow
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sx, sy = (300, 720) if variant != "calm" else (560, 740)
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    sky += (np.exp(-d / 260)[..., None] * np.array([0.6, 0.35, 0.12]) + (d < 46)[..., None] * np.array([0.5, 0.45, 0.3]))
    cl = noise2d(H, W, 120, rng, 4)
    sky *= (0.82 + 0.3 * cl[..., None])
    _C[key] = surface_from_rgb(np.clip(sky, 0, 1).astype(np.float32))
    return _C[key]


def smoke_layer(seed, alpha=0.55, color=(0.55, 0.45, 0.38)):
    key = f"smoke{seed}"
    if key in _C:
        return _C[key]
    rng = np.random.default_rng(seed)
    w = W * 2
    n = noise2d(900, w, 110, rng, 5)
    n = blur(n, 16)
    a = np.clip((n - 0.42) * 2.6, 0, 1) * alpha
    yy = np.linspace(0, 1, 900)[:, None]
    a *= np.clip(np.sin(yy * math.pi) * 1.4, 0, 1)
    arr = np.zeros((900, w, 4), np.float32)
    arr[..., 0] = color[0] * (0.8 + 0.4 * n); arr[..., 1] = color[1] * (0.8 + 0.4 * n); arr[..., 2] = color[2] * (0.8 + 0.4 * n)
    arr[..., 3] = a
    _C[key] = surface_from_rgba(arr)
    return _C[key]


def hill(ctx, color=(0.07, 0.055, 0.05), wheat=True, t=0.0):
    ctx.move_to(-10, ground_y(-10))
    for x in range(0, W + 20, 20):
        ctx.line_to(x, ground_y(x) + 6 * math.sin(x * 0.013))
    ctx.line_to(W + 10, H); ctx.line_to(-10, H); ctx.close_path()
    g = cairo.LinearGradient(0, CREST_Y, 0, H)
    g.add_color_stop_rgb(0, *[c * 1.6 for c in color]); g.add_color_stop_rgb(1, *[c * 0.4 for c in color])
    ctx.set_source(g); ctx.fill()
    if wheat:
        rng = np.random.default_rng(4)
        ctx.set_line_width(1.6)
        for i in range(520):
            x = rng.uniform(560, W + 10)
            y0 = ground_y(x) + rng.uniform(-2, 40)
            hgt = rng.uniform(14, 34)
            sway = 4 * math.sin(t * 1.7 + x * 0.05)
            ctx.move_to(x, y0); ctx.line_to(x + sway, y0 - hgt)
            ctx.set_source_rgba(0.55, 0.40, 0.20, 0.55); ctx.stroke()


def soldier(ctx, x, y, s, phase, color=(0.03, 0.03, 0.04), bearskin=True, musket=True, alpha=1.0, lean=0.0, facing=1):
    """silhouette with feet at (x,y), height ~ 150*s"""
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s * facing, s); ctx.rotate(lean)
    ctx.set_source_rgba(*color, alpha)
    sw = math.sin(phase) * 14
    # legs
    ctx.set_line_width(11); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-3, -62); ctx.line_to(-3 + sw, -2); ctx.stroke()
    ctx.move_to(3, -62); ctx.line_to(3 - sw, -2); ctx.stroke()
    # coat
    ctx.move_to(-16, -112); ctx.line_to(16, -112); ctx.line_to(20, -58); ctx.line_to(-22, -54); ctx.close_path(); ctx.fill()
    # pack
    rrect(ctx, -30, -108, 16, 34, 4); ctx.fill()
    # head + bearskin
    ctx.arc(0, -122, 10, 0, 2 * math.pi); ctx.fill()
    if bearskin:
        ctx.move_to(-13, -126)
        ctx.curve_to(-16, -165, 16, -170, 14, -126); ctx.close_path(); ctx.fill()
    else:
        ctx.rectangle(-11, -142, 22, 18); ctx.fill()
    if musket:
        ctx.set_line_width(4)
        ctx.move_to(-6, -66); ctx.line_to(26, -178); ctx.stroke()
        ctx.set_line_width(2); ctx.move_to(26, -178); ctx.line_to(30, -196); ctx.stroke()
    ctx.restore()


def guard_column(ctx, t, advance, retreat=0.0, scatter=0.0, alpha=1.0, beat=0.0):
    """three ranks-groups climbing towards the crest; advance 0..1 ; retreat pulls back"""
    rng = np.random.default_rng(7)
    groups = [(0.62, 0.0, -160), (0.78, 0.25, -60), (1.0, 0.5, 60)]
    for scale, off, dy in groups:
        n_files = 12
        for rank in range(3):
            for f in range(n_files):
                base_x = -560 + f * 92 * scale + rank * 34 * scale - off * 260
                prog = advance * 900 - retreat * 640
                x = base_x + prog
                jitter = rng.uniform(-6, 6)
                if scatter > 0:
                    x -= scatter * rng.uniform(150, 700)
                gy = ground_y(min(max(x, -50), W)) + dy * 0.0 + rank * 10 * scale + 30 * scale
                bob = -abs(math.sin(t * 5.2 + f * 0.4)) * 4 * scale
                ph = t * 5.2 + f * 0.7 + rank
                face = -1 if (retreat > 0.15 and rng.random() < 0.6 + 0.4 * scatter) else 1
                lean = -0.08 if face > 0 else 0.1
                shade = 0.03 + 0.03 * (1 - scale)
                soldier(ctx, x + jitter, gy + bob, 1.45 * scale, ph, (shade, shade, shade + 0.01), True,
                        True, alpha, lean=lean, facing=face)


def redcoat_line(ctx, rise, t, alpha=1.0, fire=0.0):
    """British line rising from the wheat behind the crest"""
    if rise <= 0:
        return
    for i in range(11):
        x = 730 + i * 34
        gy = ground_y(x) + 18 - rise * 4
        hide = (1 - rise) * 120
        ctx.save()
        ctx.rectangle(0, 0, W, gy + 20); ctx.clip()
        soldier(ctx, x, gy + hide, 0.85, 0.3, (0.30, 0.05, 0.04), bearskin=False, alpha=alpha, facing=-1)
        ctx.restore()
        if fire > 0:
            fl = fire * (0.6 + 0.4 * math.sin(t * 40 + i * 2.1))
            mx, my = x - 26, gy - 0.85 * 175 + hide
            g = cairo.RadialGradient(mx, my, 0, mx, my, 60 * fl + 1)
            g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.95 * fl); g.add_color_stop_rgba(1, 1, 0.5, 0.1, 0)
            ctx.set_source(g); ctx.arc(mx, my, 60 * fl + 1, 0, 6.3); ctx.fill()


def draw_dusk(ctx, t, advance, rise=0.0, fire=0.0, retreat=0.0, scatter=0.0, red=0.0, shake=0.0):
    ctx.save()
    if shake > 0:
        ctx.translate(math.sin(t * 37) * 8 * shake, math.cos(t * 29) * 6 * shake)
    paint_surface(ctx, dusk_bg(), 0, 0)
    sm = smoke_layer(31, 0.55)
    paint_surface(ctx, sm, -((t * 18) % W), 380, 0.9)
    # far ridge
    ctx.move_to(0, 800); ctx.curve_to(300, 740, 700, 780, W, 730); ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path()
    ctx.set_source_rgba(0.10, 0.06, 0.05, 0.85); ctx.fill()
    hill(ctx, t=t)
    redcoat_line(ctx, rise, t, 1.0, fire)
    guard_column(ctx, t, advance, retreat, scatter)
    sm2 = smoke_layer(47, 0.45, (0.45, 0.38, 0.33))
    paint_surface(ctx, sm2, -((t * 30 + 400) % W), 900, 0.5)
    # drifting embers
    rng = np.random.default_rng(77)
    for i in range(70):
        x0, y0, sp = rng.uniform(0, W), rng.uniform(500, 1400), rng.uniform(20, 70)
        x = (x0 + t * sp * 0.6) % W; y = (y0 - t * sp) % 1000 + 450
        fl = 0.5 + 0.5 * math.sin(t * 3 + i)
        ctx.arc(x, y, 1.5 + 2 * fl, 0, 6.3); ctx.set_source_rgba(1, 0.6, 0.2, 0.25 + 0.5 * fl); ctx.fill()
    if red > 0:
        ctx.set_source_rgba(0.5, 0.02, 0.0, 0.35 * red); ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------- rain / mud
def rain(ctx, t, density=1.0, alpha=0.5, seed=3, slant=0.18):
    rng = np.random.default_rng(seed)
    n = int(380 * density)
    xs = rng.uniform(-200, W + 200, n); ys0 = rng.uniform(0, H, n); sp = rng.uniform(1400, 2200, n); ln = rng.uniform(30, 70, n)
    ctx.set_line_width(1.6)
    ctx.set_source_rgba(0.75, 0.80, 0.88, alpha)
    for x, y0, v, l in zip(xs, ys0, sp, ln):
        y = (y0 + t * v) % (H + 100) - 50
        xx = x + y * slant
        ctx.move_to(xx, y); ctx.line_to(xx + l * slant, y + l)
    ctx.stroke()


def mud_bg():
    if "mud" in _C:
        return _C["mud"]
    rng = np.random.default_rng(8)
    n = noise2d(H, W, 30, rng, 5)
    n2 = noise2d(H, W, 6, rng, 3)
    y = np.linspace(0, 1, H)[:, None]
    base = np.array([0.34, 0.26, 0.17])
    col = base * (0.5 + 0.8 * n[..., None]) * (0.7 + 0.5 * y[..., None])
    wet = np.clip((n2 - 0.62) * 5, 0, 1)[..., None]
    col = col * (1 - wet) + np.array([0.45, 0.46, 0.50]) * wet * (0.5 + 0.5 * y[..., None])
    sky = np.clip(1 - y / 0.33, 0, 1)[..., None]
    col = col * (1 - sky) + np.array([0.07, 0.08, 0.10]) * sky
    _C["mud"] = surface_from_rgb(np.clip(col, 0, 1).astype(np.float32))
    return _C["mud"]


def gun_wheel(ctx, x, y, r, sink, rot=0.0, alpha=1.0):
    """field-gun wheel sunk into mud by `sink` (px)"""
    ctx.save()
    ctx.rectangle(0, 0, W, y + r - sink); ctx.clip()
    ctx.translate(x, y + sink * 0.0); ctx.rotate(rot)
    ctx.set_source_rgba(0.08, 0.06, 0.05, alpha)
    ctx.set_line_width(r * 0.13); ctx.arc(0, 0, r * 0.93, 0, 6.3); ctx.stroke()
    ctx.set_line_width(r * 0.05)
    for k in range(12):
        a = k * math.pi / 6
        ctx.move_to(math.cos(a) * r * 0.16, math.sin(a) * r * 0.16); ctx.line_to(math.cos(a) * r * 0.88, math.sin(a) * r * 0.88)
    ctx.stroke()
    ctx.arc(0, 0, r * 0.17, 0, 6.3); ctx.fill()
    ctx.set_source_rgba(0.55, 0.5, 0.45, 0.4 * alpha); ctx.set_line_width(3); ctx.arc(0, 0, r, math.pi * 1.05, math.pi * 1.6); ctx.stroke()
    ctx.restore()


def cannon_side(ctx, x, y, s, alpha=1.0, sink=0.0):
    ctx.save(); ctx.translate(x, y + sink); ctx.scale(s, s)
    ctx.set_source_rgba(0.04, 0.035, 0.03, alpha)
    ctx.move_to(-160, 10); ctx.line_to(40, -40); ctx.line_to(46, -26); ctx.line_to(-150, 30); ctx.close_path(); ctx.fill()   # trail
    rrect(ctx, -30, -78, 210, 34, 14); ctx.fill()  # barrel
    ctx.restore()
    gun_wheel(ctx, x, y - 20 * s + sink, 72 * s, sink, 0.2, alpha)


# ---------------------------------------------------------------- courier
def horse_rider(ctx, x, y, s, t, alpha=1.0, color=(0.03, 0.03, 0.04)):
    """galloping horse + courier silhouette, facing right; feet near (x, y)"""
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.set_source_rgba(*color, alpha)
    g = t * 9.0
    pitch = 0.06 * math.sin(g)
    ctx.save(); ctx.rotate(pitch)
    # barrel / body
    ctx.move_to(-78, -92)
    ctx.curve_to(-70, -122, 40, -128, 62, -108)
    ctx.curve_to(74, -98, 70, -70, 52, -64)
    ctx.curve_to(10, -56, -40, -58, -70, -66)
    ctx.curve_to(-90, -72, -92, -86, -78, -92); ctx.fill()
    # neck stretched forward, head low (gallop)
    ctx.move_to(44, -112); ctx.curve_to(70, -140, 96, -150, 112, -142)
    ctx.line_to(140, -118); ctx.curve_to(146, -110, 138, -102, 128, -106)
    ctx.line_to(104, -116); ctx.curve_to(90, -104, 72, -86, 58, -78); ctx.close_path(); ctx.fill()
    # ears & mane
    ctx.move_to(104, -146); ctx.line_to(108, -162); ctx.line_to(114, -146); ctx.fill()
    ctx.set_line_width(5)
    for k in range(5):
        mx = 60 + k * 10; my = -124 - k * 5
        ctx.move_to(mx, my); ctx.line_to(mx - 14, my - 8 + 4 * math.sin(g + k)); ctx.stroke()
    # tail streaming
    ctx.set_line_width(9); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-80, -96); ctx.curve_to(-110, -100, -130, -92, -150, -84 + 8 * math.sin(g * 1.2)); ctx.stroke()
    # rider: leaning forward
    ctx.move_to(-14, -116); ctx.line_to(16, -116); ctx.line_to(30, -168); ctx.line_to(4, -176); ctx.close_path(); ctx.fill()
    ctx.arc(30, -186, 12, 0, 6.3); ctx.fill()
    ctx.move_to(14, -194); ctx.curve_to(26, -206, 40, -206, 50, -194); ctx.close_path(); ctx.fill()   # bicorne
    ctx.set_line_width(7); ctx.move_to(22, -160); ctx.line_to(58, -136); ctx.line_to(92, -132); ctx.stroke()  # arm + reins
    ctx.move_to(4, -170); ctx.curve_to(-34, -164 + 10 * math.sin(g * 1.3), -56, -140, -60, -122); ctx.line_to(-10, -124); ctx.fill()  # cloak
    ctx.move_to(-4, -118); ctx.line_to(-12, -84); ctx.line_to(4, -80); ctx.stroke()  # boot
    # satchel
    rrect(ctx, -30, -112, 22, 18, 3); ctx.fill()
    ctx.restore()
    # legs: gallop cycle, two-segment with hooves
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    legs = [(-58, 0.0, -1), (-44, 0.5, -1), (40, 2.4, 1), (54, 2.9, 1)]
    for hx, ph, side in legs:
        a = math.sin(g + ph); lift = max(0.0, math.cos(g + ph))
        kx = hx + a * 26 * side * (1 if side > 0 else 1)
        ky = -36 - lift * 12
        fx = hx + a * 52
        fy = -4 - lift * 26
        ctx.set_line_width(13); ctx.move_to(hx, -70); ctx.line_to(kx, ky); ctx.stroke()
        ctx.set_line_width(8); ctx.move_to(kx, ky); ctx.line_to(fx, fy); ctx.stroke()
        ctx.arc(fx, fy, 6, 0, 6.3); ctx.fill()
    ctx.restore()


def field_far_bg():
    if "far" in _C:
        return _C["far"]
    rng = np.random.default_rng(12)
    y = np.linspace(0, 1, H)[:, None, None]
    sky = np.array([0.20, 0.22, 0.25]) * (1 - y) + np.array([0.42, 0.40, 0.36]) * y
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    sky *= (0.85 + 0.25 * noise2d(H, W, 140, rng, 4)[..., None])
    _C["far"] = surface_from_rgb(np.clip(sky, 0, 1).astype(np.float32))
    return _C["far"]


def draw_courier(ctx, t, alpha=1.0):
    paint_surface(ctx, field_far_bg(), 0, 0)
    # distant hills (parallax)
    for k, (yb, amp, col, sp) in enumerate([(820, 40, (0.30, 0.30, 0.29), 10), (900, 55, (0.22, 0.22, 0.19), 30), (1010, 30, (0.13, 0.12, 0.09), 80)]):
        off = (t * sp) % 600
        ctx.move_to(-10, H)
        for x in range(-10, W + 40, 20):
            xx = x + off
            ctx.line_to(x, yb - amp * (0.5 + 0.5 * math.sin(xx * 0.006 + k)) - 12 * math.sin(xx * 0.021 + k * 2))
        ctx.line_to(W + 40, H); ctx.close_path(); ctx.set_source_rgb(*col); ctx.fill()
    # posts / trees whipping past
    for i in range(6):
        x = W + 200 - ((t * 420 + i * 260) % (W + 400))
        ctx.set_source_rgba(0.06, 0.06, 0.05, 0.9)
        ctx.rectangle(x, 860, 10, 200); ctx.fill()
        ctx.arc(x + 5, 850, 46, 0, 6.3); ctx.fill()
    ctx.rectangle(0, 1040, W, H - 1040); ctx.set_source_rgb(0.10, 0.09, 0.07); ctx.fill()
    bob = math.sin(t * 9) * 6
    horse_rider(ctx, 520, 1060 + bob, 1.6, t, alpha)
    # mud spray
    rng = np.random.default_rng(int(t * 25) % 100)
    for _ in range(14):
        ctx.arc(380 + rng.uniform(-60, 30), 1040 + rng.uniform(-40, 10), rng.uniform(2, 5), 0, 6.3)
    ctx.set_source_rgba(0.12, 0.1, 0.08, 0.9); ctx.fill()
    rain(ctx, t, 0.6, 0.30, seed=5, slant=0.35)
