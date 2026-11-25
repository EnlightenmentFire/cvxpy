# -*- coding: utf-8 -*-
"""Higher-level widgets: cards, clocks, documents, hangar cross-section, carriers at sea."""
import math
import numpy as np
import cairo
from lib import *

# ---------------------------------------------------------------- geography (lon in 0..360)
MIDWAY = (182.63, 28.21)
PEARL = (202.05, 21.35)
TOKYO = (139.7, 35.7)
HASHIRA = (132.4, 33.9)          # 柱岛泊地 (approx, Inland Sea)
ALEUT = (186.5, 52.0)            # Dutch Harbor approx 166.5W
KIDO_0430 = (180.6, 30.4)        # 机动部队 approx 04:30 (示意)
KIDO_1020 = (181.3, 30.8)
TF16 = (184.0, 31.3)             # 示意
TF17 = (184.6, 31.7)
POINT_LUCK = (187.0, 32.0)        # ~32N 173W

CAM_PAC = Cam(170, 36.0, 13.5)
CAM_OPS = Cam(183.0, 30.0, 118)
CAM_ZOOM = Cam(181.4, 30.85, 330)

JP_CARRIERS = ["赤城", "加贺", "苍龙", "飞龙"]


def header(ctx, sec, a=1.0):
    text(ctx, "历史的关键一局 · 中途岛", 54, 196, 30, GOLD, 0.9 * a, SERIF, True, "l", spacing=0.05)
    if sec:
        text(ctx, sec, 54, 252, 44, WHITE, a, SERIF, True, "l", stroke=4)
    ctx.move_to(54, 270); ctx.line_to(54 + 160 * a, 270); rgba(ctx, GOLD, 0.7 * a); ctx.set_line_width(3); ctx.stroke()


def ai_badge(ctx):
    rrect(ctx, W - 176, 168, 124, 40, 8); rgba(ctx, (0, 0, 0), 0.45); ctx.fill_preserve(); rgba(ctx, GREY, 0.7); ctx.set_line_width(1.2); ctx.stroke()
    text(ctx, "AI 配音", W - 114, 197, 24, (0.85, 0.85, 0.85), 0.9, SANS, False)


def bg(ctx, t, tint=BG0):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *tint); g.add_color_stop_rgb(0.5, *BG1); g.add_color_stop_rgb(1, *tint)
    ctx.set_source(g); ctx.paint()


def clock(ctx, hhmm, x=W - 60, y=360, a=1.0, date="6月4日", size=78, color=GOLD):
    """Digital battle clock (top right of visual area)."""
    if a <= 0:
        return
    w = 330
    panel(ctx, x - w, y - 92, w, 122, a, alpha=0.72, edge=color, ea=0.6, r=10)
    text(ctx, date, x - w + 22, y - 50, 28, GREY, a, SANS, False, "l")
    text(ctx, hhmm, x - 24, y + 8, size, color, a, SANS, True, "r", glow=10)


def hhmm_lerp(t0, t1, u):
    """t0, t1 minutes since midnight."""
    m = int(lerp(t0, t1, clamp(u)))
    return f"{m // 60:02d}:{m % 60:02d}"


def card(ctx, x, y, w, h, title=None, a=1.0, edge=GOLD, fill=(0.03, 0.05, 0.08), alpha=0.86):
    if a <= 0:
        return
    panel(ctx, x, y, w, h, a, fill=fill, alpha=alpha, edge=edge, ea=0.7)
    if title:
        text(ctx, title, x + 28, y + 50, 32, edge, a, SANS, True, "l")


def stamp(ctx, s, x, y, size, a, color=RED, rot=-0.12, sc=1.0):
    if a <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc)
    tw = text_w(s, size, SERIF, True)
    rrect(ctx, -tw / 2 - 22, -size * 0.95, tw + 44, size * 1.35, 8)
    rgba(ctx, (0.06, 0.05, 0.05), 0.82 * a); ctx.fill_preserve()
    rgba(ctx, color, 0.9 * a); ctx.set_line_width(6); ctx.stroke()
    text(ctx, s, 0, size * 0.1, size, color, a, SERIF, True)
    ctx.restore()


def strike(ctx, x0, y, x1, prog, a=1.0, color=RED, w=10):
    if prog <= 0:
        return
    xe = lerp(x0, x1, ease_out(prog))
    ctx.move_to(x0, y + 4); ctx.line_to(xe, y - 6)
    rgba(ctx, color, a); ctx.set_line_width(w); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()


def big_title(ctx, s, y, a, size=96, color=WHITE, sub=None, sub_c=GOLD, glow=14):
    text(ctx, s, W / 2, y, size, color, a, SERIF, True, glow=glow, stroke=6)
    if sub:
        text(ctx, sub, W / 2, y + size * 0.85, size * 0.42, sub_c, a, SERIF, True)


def quote_card(ctx, lines, src, y, a, size=66, color=GOLD, plain=None, h=None):
    """Classical quote: big gold text lines, source line, optional plain Chinese."""
    if a <= 0:
        return
    n = len(lines)
    hh = h or (n * size * 1.5 + 200 + (90 if plain else 0))
    card(ctx, 70, y, W - 140, hh, None, a, edge=GOLD, alpha=0.82)
    yy = y + 80 + size * 0.6
    for l in lines:
        text(ctx, l, W / 2, yy, size, color, a, SERIF, True, glow=10); yy += size * 1.5
    text(ctx, src, W / 2, yy + 10, 30, GREY, a, SERIF, False)
    if plain:
        para(ctx, plain, W / 2, yy + 80, W - 240, 36, WHITE, a, SANS, False)


def doc_page(ctx, x, y, w, h, a, title=None, lines=(), size=30, hl=None, rot=0.0, font="DejaVu Serif"):
    """Paper document with typewriter-ish English lines. hl: (line_index, alpha) highlight."""
    if a <= 0:
        return
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate(rot); ctx.translate(-w / 2, -h / 2)
    # shadow
    rrect(ctx, 10, 14, w, h, 4); rgba(ctx, (0, 0, 0), 0.45 * a); ctx.fill()
    ctx.save(); rrect(ctx, 0, 0, w, h, 4); ctx.clip()
    s = paper_tex(); ctx.scale(w / s.get_width(), h / s.get_height()); ctx.set_source_surface(s, 0, 0); ctx.paint_with_alpha(a); ctx.restore()
    yy = 70
    if title:
        text(ctx, title, w / 2, yy, size * 1.05, INK, a, font, True); yy += size * 2.0
    for i, l in enumerate(lines):
        if hl and hl[0] == i and hl[1] > 0:
            tw = text_w(l, size, font, False)
            ctx.rectangle(40, yy - size * 0.95, min(tw, w - 80) * clamp(hl[1]) + 8, size * 1.25); rgba(ctx, (1.0, 0.85, 0.2), 0.55 * a); ctx.fill()
        text(ctx, l, 44, yy, size, INK, a, font, False, "l"); yy += size * 1.45
    ctx.restore()


def record_table(ctx, x, y, w, rows, a, title="赤城号 航空队行动记录（摘要·示意）", reveal=1.0, hi=None, size=34):
    if a <= 0:
        return
    rh = size * 1.75
    h = 90 + rh * len(rows) + 20
    card(ctx, x, y, w, h, title, a, edge=(0.75, 0.8, 0.85), alpha=0.9)
    for i, (tm, ev) in enumerate(rows):
        ra = a * clamp(reveal * len(rows) - i)
        yy = y + 90 + rh * (i + 0.7)
        if hi is not None and i == hi:
            ctx.rectangle(x + 12, yy - size * 1.05, w - 24, rh * 0.95); rgba(ctx, RED, 0.25 * ra); ctx.fill()
        text(ctx, tm, x + 34, yy, size, GOLD, ra, SANS, True, "l")
        text(ctx, ev, x + 34 + size * 3.6, yy, size, WHITE, ra, SANS, False, "l")
        ctx.move_to(x + 20, yy + rh * 0.3); ctx.line_to(x + w - 20, yy + rh * 0.3); rgba(ctx, GREY, 0.2 * ra); ctx.set_line_width(1); ctx.stroke()
    return h


# ---------------------------------------------------------------- carriers & fleet on map
def fleet_jp(ctx, cam, center, t, a=1.0, names=True, fires=(0, 0, 0, 0), zig=0.0, s=None, dim=(0, 0, 0, 0), wake_len=40, hide=()):
    """Four Japanese carriers in box formation around center (lon,lat). zig: snake-wake amplitude."""
    cx, cy = cam.p(*center)
    sc = s or clamp(cam.k / 260, 0.35, 1.15)
    sp = 190 * sc
    offs = [(-0.75, -0.6), (-0.75, 0.6), (0.75, -0.6), (0.75, 0.6)]  # 赤城 加贺 苍龙 飞龙
    pos = []
    A = zig * 40 * sc; om = 0.55; vx = 36 * sc
    for i, (ox, oy) in enumerate(offs):
        if i in hide:
            pos.append(None); continue
        bx, by = cx + ox * sp, cy + oy * sp
        ph = i * 0.9
        if zig:
            hist = [(bx - k * 0.12 * vx, by + A * (math.sin(om * (t - k * 0.12) + ph) - math.sin(om * t + ph))) for k in range(wake_len, 0, -1)]
            wake(ctx, hist + [(bx, by)], a, 7 * sc + 2)
            ang = math.atan2(A * om * math.cos(om * t + ph), vx)
        else:
            wake(ctx, [(bx - 90 * sc, by), (bx - 30 * sc, by)], a * 0.8, 6 * sc + 2)
            ang = 0
        carrier_top(ctx, bx, by, ang, sc, JP, a, fire=fires[i], t=t + i, dim=dim[i])
        if names:
            text(ctx, JP_CARRIERS[i], bx, by + 30 * sc + 30, 30, (1, 0.85, 0.8), a, SERIF, True, stroke=5)
        pos.append((bx, by))
    return pos


def fleet_us(ctx, cam, center, a=1.0, names=(), s=None, fire=None, t=0.0, label=None):
    cx, cy = cam.p(*center)
    sc = s or clamp(cam.k / 260, 0.3, 1.0)
    n = max(1, len(names))
    for i in range(n):
        bx, by = cx + (i - (n - 1) / 2) * 160 * sc, cy + (i % 2) * 36 * sc
        carrier_top(ctx, bx, by, -0.04, sc, US, a, fire=(fire[i] if fire else 0), t=t + i)
    nm = "·".join(x for x in names if x)
    if nm:
        text(ctx, nm, cx, cy + 40 * sc + 34, 28, (0.8, 0.9, 1), a, SERIF, True, stroke=5)
    if label:
        text(ctx, label, cx, cy - 40 * sc - 18, 30, US, a, SANS, True, stroke=5)


# ---------------------------------------------------------------- hangar cross-section
def hangar_view(ctx, x0, y0, w, t, a=1.0, planes=None, piles=0, deck_planes=None, fire=0.0, boom=None,
                elevator=None, fuel=0.0, labels=True, bomb_drop=None):
    """Side cross-section of a carrier: flight deck at y0, hangar below.
    planes: list of weapon codes per hangar slot: 'T' torpedo, 'B' bomb, '-' none, 'x' being swapped.
    deck_planes: list of 'F' fighters on deck (x fractions).
    elevator: (frac_x, lift 0..1) moving plane up.
    """
    if a <= 0:
        return
    hgt = 300
    # hull
    ctx.new_path()
    ctx.move_to(x0, y0); ctx.line_to(x0 + w, y0); ctx.line_to(x0 + w - 30, y0 + hgt + 60); ctx.curve_to(x0 + w * 0.6, y0 + hgt + 110, x0 + w * 0.3, y0 + hgt + 110, x0 + 50, y0 + hgt + 70); ctx.close_path()
    rgba(ctx, (0.20, 0.21, 0.23), a); ctx.fill_preserve(); rgba(ctx, (0.7, 0.72, 0.75), 0.7 * a); ctx.set_line_width(2.5); ctx.stroke()
    # waterline
    ctx.rectangle(x0 - 60, y0 + hgt + 40, w + 120, 140)
    g = cairo.LinearGradient(0, y0 + hgt + 40, 0, y0 + hgt + 180); g.add_color_stop_rgba(0, 0.08, 0.2, 0.3, 0.85 * a); g.add_color_stop_rgba(1, 0.02, 0.06, 0.1, 0)
    ctx.set_source(g); ctx.fill()
    # flight deck
    ctx.rectangle(x0 - 20, y0 - 12, w + 40, 14); rgba(ctx, (0.55, 0.45, 0.32), a); ctx.fill()
    # island
    ctx.rectangle(x0 + w * 0.62, y0 - 70, 46, 58); rgba(ctx, (0.3, 0.31, 0.33), a); ctx.fill()
    # hangar interior
    hy0, hy1 = y0 + 18, y0 + 160
    ctx.rectangle(x0 + 40, hy0, w - 80, hy1 - hy0)
    hg = mix((0.09, 0.09, 0.1), (0.5, 0.15, 0.05), fire)
    rgba(ctx, hg, a); ctx.fill()
    ctx.rectangle(x0 + 60, hy1 + 18, w - 130, 110); rgba(ctx, (0.08, 0.08, 0.09), a); ctx.fill()
    if labels:
        text(ctx, "飞行甲板", x0 + 10, y0 - 26, 28, GOLD, a, SANS, True, "l")
        text(ctx, "机库（封闭）", x0 + 56, hy0 + 34, 26, GREY, a, SANS, False, "l")
        text(ctx, "下层机库", x0 + 76, hy1 + 52, 24, GREY, 0.8 * a, SANS, False, "l")
    # elevators
    for ex in (0.22, 0.78):
        ctx.rectangle(x0 + w * ex - 46, y0 - 13, 92, 4); rgba(ctx, GOLD, 0.6 * a); ctx.fill()
    # planes in hangar
    planes = planes or []
    n = len(planes)
    for i, wcode in enumerate(planes):
        px = x0 + 110 + i * (w - 220) / max(1, n - 1)
        py = hy1 - 38
        plane_side(ctx, px, py - 6, 2.3, (0.62, 0.6, 0.55), a)
        if wcode in "TBx":
            oy = py + 20
            if wcode == "T" or (wcode == "x" and math.sin(t * 2 + i) > 0):
                torpedo(ctx, px - 6, oy, 1.4, a)
            else:
                bomb(ctx, px, oy, 1.6, a)
        if wcode == "x":
            text(ctx, "⇅", px, py - 34, 30, GOLD, a * (0.6 + 0.4 * math.sin(t * 6)), "DejaVu Sans", True)
    # piles of ordnance on hangar floor
    for k in range(piles):
        px = x0 + 140 + (k * 97) % (w - 280); py = hy1 - 6 - (k // 8) * 12
        if k % 2:
            torpedo(ctx, px, py, 0.7, a)
        else:
            bomb(ctx, px, py, 0.7, a)
    if fuel > 0:
        ctx.set_dash([10, 6])
        ctx.move_to(x0 + 60, hy0 + 14); ctx.line_to(x0 + w - 60, hy0 + 14)
        rgba(ctx, FIRE, 0.75 * a * fuel); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
        if labels:
            text(ctx, "输油管", x0 + w - 70, hy0 + 44, 24, FIRE, a * fuel, SANS, True, "r")
    # deck planes
    for fx in (deck_planes or []):
        plane_side(ctx, x0 + w * fx, y0 - 22, 1.3, (0.75, 0.75, 0.72), a, flip=True)
    if elevator:
        fx, lift = elevator
        ex = x0 + w * fx
        ey = lerp(hy1 - 20, y0 - 20, ease(lift))
        ctx.rectangle(ex - 46, ey + 14, 92, 6); rgba(ctx, GOLD, 0.8 * a); ctx.fill()
        plane_side(ctx, ex, ey, 1.6, (0.8, 0.78, 0.7), a)
        ctx.move_to(ex - 50, hy1); ctx.line_to(ex - 50, y0); ctx.move_to(ex + 50, hy1); ctx.line_to(ex + 50, y0)
        rgba(ctx, GOLD, 0.3 * a); ctx.set_line_width(2); ctx.set_dash([6, 6]); ctx.stroke(); ctx.set_dash([])
    if bomb_drop is not None and bomb_drop < 1.2:
        bx = x0 + w * 0.5
        by = lerp(y0 - 420, hy0 + 60, clamp(bomb_drop))
        bomb(ctx, bx, by, 1.4, a, vertical=True)
    if fire > 0:
        for k in range(6):
            fire_blob(ctx, x0 + 120 + k * (w - 240) / 5, hy0 + 90, 70 * fire, a * fire, t, seed=k)
    if boom is not None and 0 <= boom < 1:
        for k, (bx, d) in enumerate(((0.5, 0), (0.35, 0.15), (0.65, 0.3), (0.2, 0.45), (0.8, 0.55))):
            u = (boom - d) / 0.4
            if 0 < u < 1:
                cx, cy = x0 + w * bx, hy0 + 70
                r = 40 + 160 * ease_out(u)
                g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
                g.add_color_stop_rgba(0, 1, 1, 0.85, a * (1 - u)); g.add_color_stop_rgba(0.4, 1, 0.6, 0.1, 0.8 * a * (1 - u)); g.add_color_stop_rgba(1, 0.5, 0.1, 0, 0)
                ctx.set_source(g); ctx.arc(cx, cy, r, 0, 6.29); ctx.fill()


def torpedo(ctx, x, y, s, a):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -26, -4, 52, 8, 4); rgba(ctx, (0.72, 0.74, 0.76), a); ctx.fill()
    ctx.move_to(-26, -6); ctx.line_to(-32, 0); ctx.line_to(-26, 6); rgba(ctx, (0.5, 0.5, 0.5), a); ctx.fill()
    ctx.restore()


def bomb(ctx, x, y, s, a, vertical=False):
    ctx.save(); ctx.translate(x, y)
    if vertical:
        ctx.rotate(math.pi / 2)
    ctx.scale(s, s)
    ctx.save(); ctx.scale(1.7, 1); ctx.arc(0, 0, 7, 0, 6.29); ctx.restore()
    rgba(ctx, (0.35, 0.33, 0.3) if not vertical else (0.15, 0.15, 0.15), a); ctx.fill()
    ctx.move_to(-11, 0); ctx.line_to(-18, -6); ctx.line_to(-18, 6); ctx.close_path(); ctx.fill()
    ctx.restore()


def stat_grid(ctx, x, y, n, cols, alive, a, t, cell=56, color=US, lost_u=1.0):
    """n plane icons; first `alive` survive, others turn red-X progressively by lost_u."""
    for i in range(n):
        r, c = divmod(i, cols)
        px, py = x + c * cell, y + r * cell
        lost = i >= alive
        u = clamp(lost_u * (n - alive) - (i - alive)) if lost else 0
        col = mix(color, (0.35, 0.12, 0.1), u)
        plane_top(ctx, px, py, -math.pi / 2, 1.25, col, a * (1 - 0.5 * u))
        if u > 0:
            xmark(ctx, px, py, 13, a * u, RED, 4)


def chain_node(ctx, x, y, w, h, s, a, lit=1.0, color=GOLD, size=34):
    if a <= 0:
        return
    rrect(ctx, x, y, w, h, 12)
    rgba(ctx, mix((0.05, 0.07, 0.1), (0.25, 0.08, 0.05), lit * 0.6), 0.9 * a); ctx.fill_preserve()
    rgba(ctx, mix(GREY, color, lit), a); ctx.set_line_width(3); ctx.stroke()
    para(ctx, s, x + w / 2, y + h / 2 + size * 0.35 - (len(wrap_cn(s, w - 50, size, SANS, True)) - 1) * size * 0.72, w - 50, size, mix(GREY, WHITE, lit), a, SANS, True)
