# -*- coding: utf-8 -*-
"""Scene illustrations. Each draw_* returns a full-frame canvas (illustration only, before plate/layout).
Parameters are animation progress values so the same code serves stills and the full render.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from art import (W, H, paper, Ink, INK, INK_SOFT, RED, hexc, wash, hatch, mask_from_poly, person, dog, horse,
                 noise2d, blur, font, FONT_CJK, FONT_CJK_B, FONT_CJK_SB, FONT_FR_I, draw_text_rgba, over)
from layout import PX0, PY0, PX1, PY1

GREEN = hexc("#7d8a55")
GREEN_D = hexc("#5c6b3e")
EARTH = hexc("#b89464")
WOOD = hexc("#9a6a43")
SKY = hexc("#b9c3bd")
SEA = hexc("#6f8f8f")


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def crown(cx, cy, r, rng, n=30, sx=1.0, sy=0.9):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.8 + 0.28 * rng.random())
        pts.append((cx + rr * math.cos(a) * sx, cy + rr * math.sin(a) * sy))
    return pts


def scallop_outline(ink, pts, width=1.6, rng=None):
    # bumpy outline: small arcs between points
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        cx = sum(p[0] for p in pts) / n; cy = sum(p[1] for p in pts) / n
        dx, dy = mx - cx, my - cy
        L = math.hypot(dx, dy) + 1e-6
        bx, by = mx + dx / L * 6, my + dy / L * 6
        ink.line([(x0, y0), (bx, by), (x1, y1)], width)


def engr_tree(ill, ink, x, y, h, rng, color=GREEN, shade_angle=60, seed=0, wash_op=0.55):
    tw = h * 0.045
    trunk = [(x - tw, y), (x + tw, y), (x + tw * 0.55, y - h * 0.5), (x - tw * 0.55, y - h * 0.5)]
    ink.poly(trunk, 255)
    blobs = []
    for k in range(4):
        cx = x + rng.uniform(-0.18, 0.18) * h
        cy = y - h * (0.62 + 0.1 * rng.uniform(-1, 1))
        blobs.append(crown(cx, cy, h * rng.uniform(0.2, 0.3), rng))
    m = mask_from_poly(blobs)
    wash(ill, m, color, wash_op, seed=seed, bleed=1.5)
    for b in blobs:
        scallop_outline(ink, b, 1.3)
    # shade lower-right with hatching
    sh = [[(px + h * 0.05, py + h * 0.05) for (px, py) in b] for b in blobs[:2]]
    hatch(ink, sh, angle=shade_angle, spacing=5.5, width=1.0, rng=rng)


# ====================================================================== s00 sea / ship

def ship(ink, ill, x, y, s, rng, sail_op=1.0):
    """Three-masted packet ship, bow to the right. (x,y)=waterline center, s=hull length."""
    hull = [(x - s * 0.5, y - s * 0.07), (x + s * 0.42, y - s * 0.07), (x + s * 0.56, y - s * 0.12),
            (x + s * 0.45, y + s * 0.02), (x - s * 0.42, y + s * 0.03), (x - s * 0.52, y - s * 0.03)]
    ink.poly(hull, 255)
    # bowsprit
    ink.line([(x + s * 0.5, y - s * 0.1), (x + s * 0.78, y - s * 0.22)], 3)
    masts = [(-0.28, 0.62), (0.02, 0.72), (0.3, 0.6)]
    sails_m = []
    for mx, mh in masts:
        bx = x + mx * s
        top = y - s * 0.07 - mh * s
        ink.line([(bx, y - s * 0.07), (bx, top)], 3.2)
        nsail = 3
        for k in range(nsail):
            yt = top + s * 0.06 + k * mh * s * 0.28
            yb = yt + mh * s * 0.25
            wt = s * (0.11 + 0.025 * k)
            wb = s * (0.13 + 0.03 * k)
            belly = s * 0.03
            pts = [(bx - wt, yt), (bx + wt, yt)]
            for i in range(9):
                t = i / 8
                xx = bx + wb - 2 * wb * t
                pts.append((xx + belly * math.sin(math.pi * t) * 0.6, yb + belly * math.sin(math.pi * t)))
            sails_m.append(pts)
            ink.line([(bx - wt - 6, yt), (bx + wt + 6, yt)], 2.2)
    # jibs
    for k in range(2):
        sails_m.append([(x + s * (0.33 + 0.02 * k), y - s * (0.58 - 0.1 * k)), (x + s * (0.7 - 0.08 * k), y - s * (0.19 + 0.02 * k)),
                        (x + s * (0.38 + 0.02 * k), y - s * 0.15)])
    m = mask_from_poly(sails_m)
    wash(ill, m, hexc("#efe4c8"), 0.0 + 0.9 * sail_op, seed=11, gran=0.2, edge=0.2, bleed=0.5)
    sail_ink = Ink()
    for p in sails_m:
        sail_ink.line(p, 1.6, closed=True)
    sh = [[(px, py) for (px, py) in p] for p in sails_m]
    for p in sh:
        xs = [q[0] for q in p]
        cx = sum(xs) / len(xs)
        half = [(px, py) for (px, py) in p]
        hatch(sail_ink, [[(min(px, cx + 0), py) for (px, py) in half]], angle=80, spacing=6, width=0.9, rng=rng)
    # rigging
    for mx, mh in masts:
        bx = x + mx * s
        top = y - s * 0.07 - mh * s
        ink.line([(bx, top), (x - s * 0.5, y - s * 0.08)], 0.9)
        ink.line([(bx, top), (x + s * 0.5, y - s * 0.1)], 0.9)
    ink.line([(x + 0.02 * s, y - s * 0.79), (x + s * 0.78, y - s * 0.22)], 0.9)
    # flag
    ink.poly([(x + 0.3 * s, y - s * 0.69), (x + 0.36 * s, y - s * 0.675), (x + 0.3 * s, y - s * 0.66)], 255)
    return sail_ink


def draw_sea(t=0.0, ship_x=0.5, title=1.0, seed=0):
    ill = paper("sea", 21)
    rng = np.random.default_rng(seed)
    hor = 900
    sky = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, hor), (PX0, hor)]])
    wash(ill, sky, hexc("#a9bcc0"), 0.42, seed=1, gran=0.25, edge=0.15, bleed=8)
    sea = mask_from_poly([[(PX0, hor), (PX1, hor), (PX1, PY1), (PX0, PY1)]])
    wash(ill, sea, SEA, 0.55, seed=2, gran=0.35, edge=0.1, bleed=3)
    ink = Ink()
    # clouds: horizontal hatch bands
    for cy, cx, cw in [(690, 300, 230), (760, 780, 260), (830, 450, 300)]:
        pts = []
        for i in range(20):
            a = 2 * math.pi * i / 20
            pts.append((cx + cw * math.cos(a) * (0.9 + 0.15 * rng.random()), cy + 38 * math.sin(a) * (0.8 + 0.3 * rng.random())))
        hatch(ink, [pts], angle=0, spacing=6, width=0.9, rng=rng)
    # coast & lighthouse (Newport, far right)
    coast = [(700, hor + 2), (760, hor - 18), (850, hor - 30), (930, hor - 22), (PX1, hor - 26), (PX1, hor + 4)]
    ink.poly(coast, 200)
    ink.poly([(880, hor - 30), (892, hor - 30), (889, hor - 78), (883, hor - 78)], 255)
    ink.poly([(878, hor - 78), (894, hor - 78), (886, hor - 90)], 255)
    # waves
    for k in range(70):
        yy = hor + 6 + (k / 70) ** 1.7 * (PY1 - hor)
        span = 30 + 140 * (yy - hor) / (PY1 - hor)
        for j in range(int(9 + 8 * rng.random())):
            xx = rng.uniform(PX0 - 40, PX1)
            ph = t * 0.8 + k
            dx = 18 * math.sin(ph + j)
            amp = 1.5 + 4 * (yy - hor) / (PY1 - hor)
            pts = [(xx + dx + i * span / 8, yy + amp * math.sin(i * 0.9 + ph)) for i in range(9)]
            ink.line(pts, 0.8 + 1.4 * (yy - hor) / (PY1 - hor))
    sx = PX0 + (PX1 - PX0) * ship_x
    sail_ink = ship(ink, ill, sx, hor + 125 + 4 * math.sin(t * 1.3), 400, rng)
    ink.apply(ill, INK, 0.92)
    sail_ink.apply(ill, INK, 0.75)
    return ill


# ====================================================================== s02 road

ROAD_Y0, ROAD_Y1 = 905, 1075
OFFICE_BOX = (800, 330, 1004, 515)


def clouds(ink, rng, specs, spacing=6):
    for cy, cx, cw, chh in specs:
        pts = []
        for i in range(24):
            a = 2 * math.pi * i / 24
            pts.append((cx + cw * math.cos(a) * (0.9 + 0.15 * rng.random()),
                        cy + chh * math.sin(a) * (0.75 + 0.35 * rng.random()) - (chh * 0.5 if math.sin(a) < 0 else 0) * rng.random()))
        hatch(ink, [pts], angle=0, spacing=spacing, width=0.8, rng=rng)


def grass(ink, rng, y0, y1, n=260, x0=PX0, x1=PX1):
    for _ in range(n):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
        hh = 6 + 18 * (y - y0) / max(1, (y1 - y0))
        for k in range(3):
            a = math.radians(-90 + rng.uniform(-25, 25))
            ink.line([(x + k * 3, y), (x + k * 3 + hh * math.cos(a), y + hh * math.sin(a))], 0.9)


def fallen_tree(ill, ink, rx, ry, ang, L, cleared, rng, sev=0.0):
    """Trunk from roots (rx,ry) along angle ang (radians, screen coords). Returns nothing."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    w0, w1 = 30, 11
    keep = 1.0 - cleared
    side1 = [(rx + ux * L * s + nx * (w0 + (w1 - w0) * s), ry + uy * L * s + ny * (w0 + (w1 - w0) * s)) for s in np.linspace(0, 1, 12)]
    side2 = [(rx + ux * L * s - nx * (w0 + (w1 - w0) * s), ry + uy * L * s - ny * (w0 + (w1 - w0) * s)) for s in np.linspace(0, 1, 12)]
    poly = side1 + side2[::-1]
    # branches + clumps
    clumps, branches = [], []
    rngb = np.random.default_rng(12)
    for k in range(7):
        s = 0.42 + 0.085 * k
        bx, by = rx + ux * L * s, ry + uy * L * s
        sgn = 1 if k % 2 else -1
        a2 = ang + sgn * rngb.uniform(0.45, 0.85)
        bl = rngb.uniform(70, 110)
        ex, ey = bx + bl * math.cos(a2), by + bl * math.sin(a2)
        branches.append([(bx, by), ((bx + ex) / 2 + rngb.normal(0, 4), (by + ey) / 2 + rngb.normal(0, 4)), (ex, ey)])
        clumps.append(crown(ex, ey, rngb.uniform(42, 58), rngb))
    clumps.append(crown(rx + ux * L * 1.03, ry + uy * L * 1.03, 72, rngb))
    if keep <= 0:
        return
    cm = mask_from_poly(clumps)
    wash(ill, cm, GREEN, 0.6 * keep, seed=10, bleed=1.5)
    tm = mask_from_poly([poly])
    wash(ill, tm, WOOD, 0.8 * keep, seed=9, gran=0.4, edge=0.4, bleed=0.8)
    for b in branches:
        ink.line(b, 3.4)
    ink.line(poly, 2.3, closed=True)
    for k in (-14, -6, 3, 11):
        pts = [(rx + ux * L * s + nx * k * (1 - 0.6 * s), ry + uy * L * s + ny * k * (1 - 0.6 * s)) for s in np.linspace(0.04, 0.96, 14)]
        ink.line([(px + rng.normal(0, 0.8), py + rng.normal(0, 0.8)) for px, py in pts], 1.0)
    hatch(ink, [side1[:8] + [(rx + ux * L * s, ry + uy * L * s) for s in np.linspace(0.6, 0, 8)]], math.degrees(ang) + 80, 4.2, 0.9, rng)
    for c in clumps:
        scallop_outline(ink, c, 1.25)
    hatch(ink, [[(px + 10, py + 12) for px, py in c] for c in clumps], 60, 5, 0.9, rng)
    # roots fan (on the far side)
    for k in range(9):
        a = ang + math.pi + rng.uniform(-1.2, 1.2)
        r1, r2 = rng.uniform(28, 40), rng.uniform(50, 75)
        ink.line([(rx, ry), (rx + r1 * math.cos(a), ry + r1 * math.sin(a)), (rx + r2 * math.cos(a + 0.25), ry + r2 * math.sin(a + 0.25))], 2.4)
    # torn earth
    ink.ellipse(rx - 10, ry + 6, 46, 14, 160)


def office_icon(ill, lit=0.0):
    ox0, oy0, ox1, oy1 = OFFICE_BOX
    o = Ink()
    def dashed(p0, p1):
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = int(L / 12)
        for i in range(0, n, 2):
            t0, t1 = i / n, min(1, (i + 1) / n)
            o.line([(p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0), (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)], 1.6)
    dashed((ox0, oy0), (ox1, oy0)); dashed((ox1, oy0), (ox1, oy1)); dashed((ox1, oy1), (ox0, oy1)); dashed((ox0, oy1), (ox0, oy0))
    bx0, bx1, base = ox0 + 38, ox1 - 38, oy1 - 62
    o.line([(bx0 - 10, base), (bx1 + 10, base)], 2.2)
    o.line([(bx0 - 6, base - 72), (bx1 + 6, base - 72)], 2.2)
    o.line([(bx0 - 10, base - 72), ((bx0 + bx1) / 2, base - 102), (bx1 + 10, base - 72), (bx0 - 10, base - 72)], 2.0)
    for k in range(5):
        x = bx0 + 6 + k * (bx1 - bx0 - 12) / 4
        o.line([(x, base - 68), (x, base - 3)], 3.2)
    o.apply(ill, hexc("#77766f"), 0.5, grain=0.05)
    f = font(FONT_CJK, 28)
    over(ill, draw_text_rgba((W, H), [((ox0 + ox1) / 2, oy1 - 36, "官府", f, (110, 108, 100, 190), "mm")]), 1.0)


def speech_bubble(ill, bx, by, bw, bh, text, tail, op=1.0, size=38):
    b = Ink()
    pts = []
    for i in range(48):
        a = 2 * math.pi * i / 48
        pts.append((bx + bw / 2 * math.cos(a) * (1 + 0.025 * math.sin(5 * a)), by + bh / 2 * math.sin(a)))
    tx, ty = tail
    # find two bubble points nearest the tail direction
    ang = math.atan2(ty - by, tx - bx)
    i0 = int(((ang % (2 * math.pi)) / (2 * math.pi)) * 48)
    a, c = pts[(i0 - 2) % 48], pts[(i0 + 2) % 48]
    bm = mask_from_poly([pts, [a, (tx, ty), c, (bx, by)]])
    ill[:] = ill * (1 - bm[..., None] * 0.93 * op) + hexc("#f6efdc") * bm[..., None] * 0.93 * op
    seq = [pts[(i0 + 2 + k) % 48] for k in range(45)]
    b.line(seq, 2.0)
    b.line([a, (tx, ty), c], 2.0)
    b.apply(ill, INK, 0.9 * op, grain=0.05)
    if text:
        f = font(FONT_CJK_SB, size)
        over(ill, draw_text_rgba((W, H), [(bx, by - 2, text, f, (46, 33, 24, 255), "mm")]), op)


def red_ellipse(ill, cx, cy, rx_, ry_, prog, op=0.85, dashed=True, width=3.4):
    r = Ink()
    n = 48
    for i in range(n):
        if i / n > prog:
            break
        if (not dashed) or i % 2 == 0:
            a0 = 2 * math.pi * i / n - math.pi / 2; a1 = 2 * math.pi * (i + 1) / n - math.pi / 2
            r.line([(cx + rx_ * math.cos(a0), cy + ry_ * math.sin(a0)), (cx + rx_ * math.cos(a1), cy + ry_ * math.sin(a1))], width)
    r.apply(ill, RED, op, grain=0.08)


def draw_road(t=0.0, fallen=1.0, gather=1.0, circled=1.0, saw=0.0, cleared=0.0, bubble=1.0, seed=0, carts_go=0.0):
    ill = paper("america", 31)
    rng = np.random.default_rng(seed)
    hor = 655
    sky = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, hor), (PX0, hor)]])
    wash(ill, sky, hexc("#c3cdc6"), 0.38, seed=3, gran=0.2, edge=0.1, bleed=10)
    fields = mask_from_poly([[(PX0, hor), (PX1, hor - 10), (PX1, PY1), (PX0, PY1)]])
    wash(ill, fields, hexc("#a9ae72"), 0.45, seed=4, gran=0.45, edge=0.1, bleed=4)
    road = [(PX0, ROAD_Y0 + 25), (PX1, ROAD_Y0 - 25), (PX1, ROAD_Y1 - 15), (PX0, ROAD_Y1 + 35)]
    wash(ill, mask_from_poly([road]), EARTH, 0.58, seed=5, gran=0.5, edge=0.3, bleed=2)
    ink = Ink()
    clouds(ink, rng, [(400, 260, 170, 34), (470, 620, 150, 26), (560, 380, 220, 22)])
    # birds
    for bx, by in [(560, 420), (590, 405), (612, 430)]:
        ink.line([(bx - 9, by - 3), (bx, by + 2), (bx + 9, by - 3)], 1.4)
    hills = [(PX0, hor)]
    for i in range(21):
        x = PX0 + (PX1 - PX0) * i / 20
        hills.append((x, hor - 28 - 26 * math.sin(i * 0.7 + 1) - 10 * rng.random()))
    hills.append((PX1, hor))
    hatch(ink, [hills], angle=-18, spacing=6, width=0.85, rng=rng)
    ink.line(hills[1:-1], 1.4)
    rng2 = np.random.default_rng(7)
    for i in range(12):
        x = PX0 + 30 + i * 82 + rng2.uniform(-18, 18)
        if 210 < x < 360:
            continue
        engr_tree(ill, ink, x, hor - 22 + rng2.uniform(-6, 6), rng2.uniform(70, 105), rng2, color=GREEN_D, seed=40 + i, wash_op=0.38)
    # farmhouse
    fx, fy = 230, hor + 20
    hm = mask_from_poly([[(fx, fy), (fx + 115, fy), (fx + 115, fy - 62), (fx, fy - 62)]])
    wash(ill, hm, hexc("#e9e2cf"), 0.6, seed=8, gran=0.1, edge=0.1, bleed=0.5)
    ink.line([(fx, fy), (fx + 115, fy), (fx + 115, fy - 62), (fx, fy - 62), (fx, fy)], 1.6)
    roof = [(fx - 10, fy - 60), (fx + 57, fy - 104), (fx + 125, fy - 60)]
    ink.line(roof + [roof[0]], 1.6)
    hatch(ink, [roof], 25, 4.2, 0.9, rng)
    ink.poly([(fx + 80, fy - 106), (fx + 91, fy - 106), (fx + 91, fy - 82), (fx + 80, fy - 82)])
    for wx in (fx + 16, fx + 74):
        ink.line([(wx, fy - 44), (wx + 20, fy - 44), (wx + 20, fy - 24), (wx, fy - 24), (wx, fy - 44)], 1.2)
    ink.line([(fx + 50, fy), (fx + 50, fy - 34), (fx + 66, fy - 34), (fx + 66, fy)], 1.2)
    # split-rail fence along far road edge
    for i in range(18):
        x0 = PX0 + i * 56
        ya = ROAD_Y0 + 25 - (x0 - PX0) * 50 / (PX1 - PX0) - 8
        for k in range(3):
            ink.line([(x0, ya - 12 - k * 12), (x0 + 56, ya - 20 - k * 12 + (7 if i % 2 else -3))], 1.8)
        ink.line([(x0, ya + 2), (x0, ya - 50)], 2.2)
    for off in (45, 80, 120):
        pts = [(PX0 + (PX1 - PX0) * i / 29, ROAD_Y0 + 25 + off - 50 * i / 29 + rng.normal(0, 1.2)) for i in range(30)]
        ink.line(pts, 1.0)
    hatch(ink, [road], angle=3, spacing=12, width=0.7, rng=rng)
    grass(ink, rng, ROAD_Y1 + 40, PY1 - 5, 240)
    for k in range(14):
        yy = hor + 22 + k * 13
        ink.line([(PX0 + rng.uniform(0, 40) + i * 48, yy + rng.normal(0, 0.6) - i * 0.3) for i in range(21)], 0.7)
    # ---- the fallen tree: roots on the far edge, crown in the near verge
    rx, ry = 430, ROAD_Y0 - 2
    ang = math.radians(-92 + (92 + 52) * ease(fallen))
    fallen_tree(ill, ink, rx, ry, ang, 360, cleared, rng)
    # cart + horse on the left, stopped
    sil = Ink()
    cx0 = 60 + 380 * carts_go
    horse(sil, cx0 + 250, ROAD_Y0 + 112, 170, facing=1)
    sil.poly([(cx0, ROAD_Y0 + 52), (cx0 + 125, ROAD_Y0 + 52), (cx0 + 116, ROAD_Y0 + 88), (cx0 + 8, ROAD_Y0 + 88)], 255)
    sil.ellipse(cx0 + 30, ROAD_Y0 + 100, 24, 24, None, 255, 2.6)
    sil.ellipse(cx0 + 98, ROAD_Y0 + 100, 24, 24, None, 255, 2.6)
    for k in range(6):
        a = k * math.pi / 3
        for wx in (cx0 + 30, cx0 + 98):
            sil.line([(wx, ROAD_Y0 + 100), (wx + 22 * math.cos(a), ROAD_Y0 + 100 + 22 * math.sin(a))], 1.2)
    sil.line([(cx0 + 125, ROAD_Y0 + 72), (cx0 + 190, ROAD_Y0 + 66)], 2.4)
    person(sil, cx0 + 92, ROAD_Y0 + 60, 92, "sit", 1, "wide")
    # neighbors gather to the right of the tree
    people = [(650, ROAD_Y0 + 120, 178, "talk", -1, "top", False),
              (722, ROAD_Y0 + 112, 168, "point", -1, "wide", False),
              (790, ROAD_Y0 + 124, 150, "stand", -1, "bonnet", True),
              (850, ROAD_Y0 + 116, 172, "talk", -1, "cap", False),
              (915, ROAD_Y0 + 126, 158, "stand", -1, "wide", False),
              (975, ROAD_Y0 + 132, 118, "stand", -1, "cap", False)]
    for i, (x, y, h, pose, f, hat, dress) in enumerate(people):
        g = ease(gather * 1.35 - i * 0.07)
        sx = 1150 + 60 * i
        xx = sx + (x - sx) * g
        p = pose if g >= 0.999 else "walk"
        ff = f
        if saw > 0 and i in (0, 1, 3):
            tx = [520, 600, 560][[0, 1, 3].index(i)]
            ty = [ROAD_Y0 + 60, ROAD_Y0 + 105, ROAD_Y0 + 150][[0, 1, 3].index(i)]
            k = ease(saw * 3)
            xx = x + (tx - x) * k
            y = y + (ty - y) * k
            p = "saw" if saw * 3 >= 1 else "walk"
        sil.ellipse(xx, y + 2, h * 0.16, h * 0.025, 90)
        person(sil, xx, y, h, p, ff, hat, dress, arm_t=t + i)
    ink.apply(ill, INK, 0.92)
    sil.apply(ill, INK, 0.97, grain=0.05)
    if bubble > 0:
        speech_bubble(ill, 790, 760, 300, 104, "咱们自己来！", (720, 875), bubble)
    if circled > 0:
        red_ellipse(ill, 718, ROAD_Y0 + 35, 118, 150, circled)
    office_icon(ill)
    return ill


# ====================================================================== s09 Memphis

NIGHT = hexc("#18202c")


def lighten(canvas, mask, color, op):
    a = np.clip(mask * op, 0, 1)[..., None]
    canvas[:] = canvas * (1 - a) + np.asarray(color)[None, None, :] * a


def steamboat(ink, x, y, s, rng, smoke_t=0.0, light=None):
    """Side-wheel river steamboat, bow to the left. (x,y)=waterline at the bow; s=length.
    light: optional Ink layer for pale railing/window lines."""
    hull = [(x - s * 0.03, y - s * 0.045), (x + s * 0.05, y - s * 0.03), (x + s, y - s * 0.035), (x + s * 0.99, y + s * 0.012), (x + s * 0.07, y + s * 0.016)]
    ink.poly(hull, 255)
    ink.poly([(x + s * 0.04, y - s * 0.03), (x + s * 0.97, y - s * 0.03), (x + s * 0.97, y - s * 0.045), (x + s * 0.04, y - s * 0.045)], 255)
    # boiler deck cabin
    ink.poly([(x + s * 0.12, y - s * 0.045), (x + s * 0.93, y - s * 0.045), (x + s * 0.93, y - s * 0.105), (x + s * 0.12, y - s * 0.105)], 255)
    ink.poly([(x + s * 0.09, y - s * 0.105), (x + s * 0.95, y - s * 0.105), (x + s * 0.95, y - s * 0.115), (x + s * 0.09, y - s * 0.115)], 255)
    # texas deck + pilothouse
    ink.poly([(x + s * 0.3, y - s * 0.115), (x + s * 0.78, y - s * 0.115), (x + s * 0.78, y - s * 0.15), (x + s * 0.3, y - s * 0.15)], 255)
    ink.poly([(x + s * 0.36, y - s * 0.15), (x + s * 0.44, y - s * 0.15), (x + s * 0.44, y - s * 0.19), (x + s * 0.36, y - s * 0.19)], 255)
    ink.poly([(x + s * 0.35, y - s * 0.19), (x + s * 0.45, y - s * 0.19), (x + s * 0.40, y - s * 0.205)], 255)
    # paddle box
    ink.ellipse(x + s * 0.62, y - s * 0.05, s * 0.085, s * 0.085, 255)
    # chimneys
    tops = []
    for cx in (x + s * 0.2, x + s * 0.27):
        ink.poly([(cx - s * 0.011, y - s * 0.105), (cx + s * 0.011, y - s * 0.105), (cx + s * 0.013, y - s * 0.44), (cx - s * 0.013, y - s * 0.44)], 255)
        ink.poly([(cx - s * 0.024, y - s * 0.455), (cx + s * 0.024, y - s * 0.455), (cx + s * 0.015, y - s * 0.43), (cx - s * 0.015, y - s * 0.43)], 255)
        tops.append((cx, y - s * 0.46))
    # flagstaff at the bow
    ink.line([(x + s * 0.02, y - s * 0.045), (x + s * 0.02, y - s * 0.16)], 2)
    if light is not None:
        for k in range(26):
            px = x + s * (0.13 + 0.031 * k)
            light.line([(px, y - s * 0.05), (px, y - s * 0.1)], 1.2)
        light.line([(x + s * 0.12, y - s * 0.075), (x + s * 0.93, y - s * 0.075)], 1.0)
        for k in range(12):
            px = x + s * (0.32 + 0.038 * k)
            light.line([(px, y - s * 0.12), (px, y - s * 0.145)], 1.0)
        for k in range(8):
            a_ = k * math.pi / 8
            cx_, cy_ = x + s * 0.62, y - s * 0.05
            light.line([(cx_ - s * 0.08 * math.cos(a_), cy_ - s * 0.08 * math.sin(a_)), (cx_, cy_)], 1.0)
    return tops


def draw_memphis(t=0.0, boarding=0.7, dogs_in=0.0, howl=0.0, snow=1.0, boat_x=0.0, seed=0, column=1.0):
    ill = paper("ice", 51)
    rng = np.random.default_rng(seed)
    hor = 690
    # sky: layered cold washes, darker at top
    for k, (y0, op) in enumerate([(PY0, 0.55), (PY0 + 120, 0.35), (PY0 + 240, 0.25)]):
        m = mask_from_poly([[(PX0, y0), (PX1, y0), (PX1, hor), (PX0, hor)]])
        wash(ill, m, hexc("#5b7088"), op, seed=60 + k, gran=0.2, edge=0.05, bleed=40)
    river = mask_from_poly([[(PX0, hor), (PX1, hor), (PX1, 1090), (PX0, 1110)]])
    wash(ill, river, hexc("#3a5068"), 0.8, seed=63, gran=0.3, edge=0.1, bleed=2)
    ink = Ink()
    # far bank forest (west bank)
    fb = [(PX0, hor + 4)]
    for i in range(120):
        x = PX0 + (PX1 - PX0) * i / 119
        fb.append((x, hor - 20 - 9 * abs(math.sin(i * 0.9)) - 6 * abs(math.sin(i * 2.3)) - 4 * rng.random()))
    fb.append((PX1, hor + 4))
    ink.poly(fb, 210)
    # ice floes in perspective
    floes = []
    rngf = np.random.default_rng(70)
    for i in range(46):
        yy = hor + 12 + (rngf.random() ** 1.6) * (1080 - hor - 20)
        sc = 0.25 + 1.2 * (yy - hor) / (1080 - hor)
        xx = rngf.uniform(PX0 - 40, PX1 + 40) + (t * 9 * sc) % 60
        w_, h_ = rngf.uniform(30, 75) * sc, rngf.uniform(7, 15) * sc
        pts = []
        nv = 7
        for v in range(nv):
            a = 2 * math.pi * v / nv + rngf.uniform(-0.2, 0.2)
            pts.append((xx + w_ * math.cos(a) * rngf.uniform(0.7, 1.1), yy + h_ * math.sin(a) * rngf.uniform(0.7, 1.1)))
        floes.append(pts)
    fm = mask_from_poly(floes)
    lighten(ill, blur(fm, 0.8), hexc("#e8eef3"), 0.92)
    sidem = mask_from_poly([[(px, py + 4) for px, py in f] for f in floes]) * (1 - fm)
    lighten(ill, sidem, hexc("#8fa3b6"), 0.6)
    for f in floes:
        ink.line(f, 1.0, closed=True, val=150)
    # current lines
    for k in range(40):
        yy = hor + 10 + (k / 40) ** 1.5 * (1080 - hor)
        x0 = rng.uniform(PX0, PX1 - 100)
        ink.line([(x0 + i * 14, yy + rng.normal(0, 0.8)) for i in range(8)], 0.7, val=120)
    ink.apply(ill, NIGHT, 0.85)
    # steamboat
    boat = Ink()
    light = Ink()
    bx = 500 + boat_x * 650
    chim = steamboat(boat, bx, 905, 560, rng, light=light)
    # gangplank
    plank_a, plank_b = (330, 1060), (bx + 30, 880)
    if boat_x < 0.05:
        boat.line([plank_a, plank_b], 7)
    boat.apply(ill, NIGHT, 0.96, grain=0.04)
    light.apply(ill, hexc("#7d8fa3"), 0.8, grain=0.05)
    # smoke: puffs rising from the chimneys, drifting right
    for j, c in enumerate(chim):
        for k in range(10):
            ph = (t * 0.35 + k / 10.0) % 1.0
            sx = c[0] + 140 * ph ** 1.3 + 6 * math.sin(t + k)
            sy = c[1] - 260 * ph
            r_ = 10 + 46 * ph
            pm = mask_from_poly([crown(sx, sy, r_, np.random.default_rng(80 + k + 10 * j), n=14)])
            wash(ill, pm, hexc("#3e4a58"), 0.42 * (1 - ph) ** 1.2, seed=81 + k, gran=0.3, edge=0.1, bleed=3 + 6 * ph)
    # near bank (snow)
    bank = [(PX0, 1085), (250, 1072), (360, 1058), (560, 1075), (PX1, 1095), (PX1, PY1), (PX0, PY1)]
    bm = mask_from_poly([bank])
    lighten(ill, bm, hexc("#e3e9ee"), 0.9)
    wash(ill, bm, hexc("#9fb0c0"), 0.25, seed=82, gran=0.6, edge=0.05, bleed=3)
    gi = Ink()
    for _ in range(140):
        x = rng.uniform(PX0, PX1); y = rng.uniform(1110, PY1 - 5)
        gi.line([(x, y), (x + rng.uniform(-4, 4), y - rng.uniform(4, 12))], 1.0)
    gi.line(bank[:4], 1.6)
    gi.apply(ill, NIGHT, 0.7)
    # the column of people: walk along the bank, then up the plank, then vanish into the boat
    sil = Ink()
    N = 16
    rngp = np.random.default_rng(90)
    for i in range(N):
        # position along path parameter: 0 = left edge of bank, 1 = bank end of plank, 2 = boat deck
        u = column * 2.2 - i * 0.13 + boarding * 1.6
        if u < 0 or u > 2.0:
            continue
        if u <= 1.0:
            x = PX0 - 20 + (plank_a[0] - PX0 + 20) * u
            y = 1104 - 30 * u
        else:
            k = u - 1.0
            x = plank_a[0] + (plank_b[0] - plank_a[0]) * k
            y = plank_a[1] + (plank_b[1] - plank_a[1]) * k
        sc = 1.0 - 0.25 * max(0, u - 1)
        hh = rngp.uniform(95, 125) * sc
        kind = i % 5
        if kind == 0:
            person(sil, x, y, hh, "huddle", 1, "shawl", True, arm_t=t)
        elif kind == 1:
            person(sil, x, y, hh, "walk", 1, None, False, arm_t=t + i)
        elif kind == 2:
            person(sil, x, y, hh * 0.92, "bow", 1, "shawl", True)
        elif kind == 3:
            person(sil, x, y, hh, "carry", 1, "shawl", True)
            sil.ellipse(x + hh * 0.12, y - hh * 0.8, hh * 0.09, hh * 0.08)
        else:
            person(sil, x, y, hh * 0.7, "walk", 1, None, False, arm_t=t + i, child=True)
    # dogs on the bank
    dpos = [(470, 1175, 150, 0.0), (650, 1160, 128, 0.2), (300, 1200, 136, 0.0)]
    for j, (x, y, s, hb) in enumerate(dpos):
        h_ = min(1.0, howl * (1.0 if j == 0 else 0.7) + hb)
        if dogs_in > 0:
            # leap into the water and swim toward the boat
            k = min(1.0, dogs_in * 1.2 - j * 0.12)
            if k > 0:
                tx, ty = 520 + 110 * j + 140 * k, 1030 - 70 * k
                x = x + (tx - x) * min(1, k * 1.5)
                y = y + (ty - y) * min(1, k * 1.5)
                dog(sil, x, y, s * (1 - 0.45 * k), 1, 0.1, swim=k > 0.6)
                continue
        dog(sil, x, y, s, 1, h_)
    sil.apply(ill, NIGHT, 0.97, grain=0.04)
    # snow
    if snow > 0:
        sn = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(sn)
        rs = np.random.default_rng(99)
        for i in range(520):
            x0 = rs.uniform(PX0, PX1)
            v = rs.uniform(18, 45)
            y0 = (rs.uniform(PY0, PY1) + v * t) % (PY1 - PY0) + PY0
            x = x0 + 10 * math.sin(t * 0.8 + i)
            r_ = rs.uniform(1.0, 2.6)
            d.ellipse([x - r_, y0 - r_, x + r_, y0 + r_], fill=int(rs.uniform(150, 255)))
        snm = np.asarray(sn).astype(np.float32) / 255
        lighten(ill, snm, hexc("#f4f7fa"), 0.85 * snow)
    return ill


# ====================================================================== title overlay for s00

def title_overlay(ill, op=1.0):
    fb = font(FONT_CJK_B, 96)
    fs = font(FONT_CJK, 30)
    items = [(W / 2, 410, "一个法国年轻人", fb, (40, 28, 20, 255), "mm"),
             (W / 2, 525, "看美国小镇", fb, (40, 28, 20, 255), "mm"),
             (W / 2, 612, "1831—1832 · 托克维尔的美国笔记", fs, (80, 60, 45, 255), "mm")]
    rgba = draw_text_rgba((W, H), items)
    a = rgba[..., 3]
    halo = blur(a, 14) * 0.6
    ill[:] = ill * (1 - halo[..., None] * op) + hexc("#ece3cb") * halo[..., None] * op
    over(ill, rgba, op)
    # red seal
    s = Ink()
    s.poly([(860, 470), (930, 470), (930, 540), (860, 540)])
    s.apply(ill, RED, 0.85 * op, grain=0.25)
    f2 = font(FONT_CJK_B, 26)
    over(ill, draw_text_rgba((W, H), [(895, 491, "托克", f2, (240, 225, 200, 255), "mm"), (895, 521, "维尔", f2, (240, 225, 200, 255), "mm")]), op)


# ====================================================================== s03 meeting hall

def bust_back(ink, x, y, s, raise_=0.0, val=255, hat=None):
    """Person seen from behind, head and shoulders; (x,y)=bottom center, s=shoulder width."""
    ink.poly([(x - s * 0.5, y), (x - s * 0.48, y - s * 0.3), (x - s * 0.3, y - s * 0.45), (x + s * 0.3, y - s * 0.45), (x + s * 0.48, y - s * 0.3), (x + s * 0.5, y)], val)
    ink.line([(x, y - s * 0.4), (x, y - s * 0.55)], s * 0.18, val)
    ink.ellipse(x, y - s * 0.7, s * 0.17, s * 0.2, val)
    if raise_ > 0:
        sx = x + s * 0.38
        ex, ey = sx + s * 0.08, y - s * 0.45 - s * 0.45 * raise_
        hx, hy = sx + s * 0.06, y - s * 0.45 - s * 0.95 * raise_
        ink.line([(sx, y - s * 0.38), (ex, ey), (hx, hy)], s * 0.12, val)
        ink.ellipse(hx, hy, s * 0.07, s * 0.08, val)


OFFICES = ["行政委员", "估税员", "收税员", "治安员", "书记员", "司库", "济贫监督", "学校委员", "道路监督"]


def draw_meeting(t=0.0, hands=1.0, ledger=1.0, rot=0.0, seed=0):
    ill = paper("america", 33)
    rng = np.random.default_rng(seed)
    hall_x1 = 700 if ledger > 0 else PX1
    wall = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]])
    wash(ill, wall, hexc("#cdb48a"), 0.35, seed=1, gran=0.3, edge=0.05, bleed=4)
    floor = mask_from_poly([[(PX0, 860), (PX1, 860), (PX1, PY1), (PX0, PY1)]])
    wash(ill, floor, WOOD, 0.35, seed=2, gran=0.5, edge=0.1, bleed=3)
    ink = Ink()
    # plank walls
    for k in range(0, 40):
        x = PX0 + k * 26
        ink.line([(x, PY0), (x, 860)], 0.7, val=150)
    # windows with light
    for wx in (150, 520):
        wm = mask_from_poly([[(wx, 380), (wx + 150, 380), (wx + 150, 640), (wx, 640)]])
        lighten = wm
        ill[:] = ill * (1 - wm[..., None] * 0.6) + hexc("#f7f0dc") * wm[..., None] * 0.6
        ink.line([(wx, 380), (wx + 150, 380), (wx + 150, 640), (wx, 640), (wx, 380)], 2.4)
        for c in (1, 2):
            ink.line([(wx + 50 * c, 380), (wx + 50 * c, 640)], 1.4)
        for r in (1, 2, 3):
            ink.line([(wx, 380 + 65 * r), (wx + 150, 380 + 65 * r)], 1.4)
    # moderator's desk + board
    ink.poly([(330, 760), (430, 760), (425, 860), (335, 860)], 230)
    bm = mask_from_poly([[(270, 330), (490, 330), (490, 440), (270, 440)]])
    ill[:] = ill * (1 - bm[..., None] * 0.85) + hexc("#2f3a2f") * bm[..., None] * 0.85
    f = font(FONT_CJK_SB, 26)
    over(ill, draw_text_rgba((W, H), [(380, 358, "本年议程", f, (235, 230, 215, 255), "mm"),
                                      (380, 402, "修路 · 办学 · 定税", font(FONT_CJK, 22), (235, 230, 215, 255), "mm")]))
    sil = Ink()
    person(sil, 380, 770, 120, "talk", 1, None, arm_t=t)
    # rows of townsmen from behind, hands rising
    rows = [(890, 52, 11), (960, 64, 9), (1040, 80, 8), (1130, 98, 7), (1235, 118, 6)]
    rngr = np.random.default_rng(5)
    for ri, (yy, s, n) in enumerate(rows):
        x0, x1 = PX0 + 20, PX1 - 20
        for k in range(n):
            x = x0 + (x1 - x0) * (k + 0.5) / n + rngr.uniform(-8, 8)
            r_ = rngr.random()
            up = ease(hands * 1.6 - r_ * 0.6) if r_ < 0.8 else 0.0
            bust_back(sil, x, yy, s * 1.05, up)
    ink.apply(ill, INK, 0.8)
    sil.apply(ill, INK, 0.96, grain=0.05)
    # the ledger slip on the right
    if ledger > 0:
        lx0, lx1, ly0, ly1 = 700, 1000, 330, 1220
        lm = np.zeros((H, W), np.float32); lm[ly0:ly1, lx0:lx1] = 1; lm = blur(lm, 1.5)
        sh = blur(np.roll(np.roll(lm, 8, 0), -6, 1), 10) * 0.35
        ill[:] = ill * (1 - sh[..., None] * ledger)
        ill[:] = ill * (1 - lm[..., None] * 0.95 * ledger) + hexc("#f0e6cc") * lm[..., None] * 0.95 * ledger
        li = Ink()
        li.line([(lx0 + 12, ly0 + 12), (lx1 - 12, ly0 + 12), (lx1 - 12, ly1 - 12), (lx0 + 12, ly1 - 12), (lx0 + 12, ly0 + 12)], 1.0)
        items = [((lx0 + lx1) / 2, ly0 + 52, "镇上的差事", font(FONT_CJK_SB, 34), (46, 33, 24, 255), "mm"),
                 ((lx0 + lx1) / 2, ly0 + 92, "主要的就有十九种", font(FONT_CJK, 22), (110, 80, 55, 255), "mm")]
        hats = ["top", "wide", "cap", None, "top", "wide", None, "cap", "top"]
        for i, name in enumerate(OFFICES):
            yy = ly0 + 150 + i * 80
            items.append((lx0 + 125, yy, name, font(FONT_CJK, 30), (46, 33, 24, 255), "lm"))
            li.line([(lx0 + 30, yy + 34), (lx1 - 30, yy + 34)], 0.6, val=120)
            # rotating portraits: a different little person each time
            k = int(rot + i * 0.37) % 4
            hx = lx0 + 70
            person(li, hx, yy + 30, 62, "stand", 1 if (k % 2) else -1, [hats[i], "wide", "cap", None][k])
        items.append(((lx0 + lx1) / 2, ly1 - 40, "……", font(FONT_CJK, 30), (46, 33, 24, 255), "mm"))
        li.apply(ill, INK, 0.9 * ledger, grain=0.05)
        over(ill, draw_text_rgba((W, H), items), ledger)
    return ill


# ====================================================================== s04 split screen

def envelope(ink, x, y, s, ang, val=255):
    ca, sa = math.cos(ang), math.sin(ang)
    def R(dx, dy):
        return (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    pts = [R(-s, -s * 0.65), R(s, -s * 0.65), R(s, s * 0.65), R(-s, s * 0.65)]
    ink.line(pts, 1.3, closed=True, val=val)
    ink.line([R(-s, -s * 0.65), R(0, s * 0.1), R(s, -s * 0.65)], 1.1, val=val)


def palace(ink, cx, base, w, val=255):
    h = w * 0.22
    ink.poly([(cx - w / 2, base), (cx + w / 2, base), (cx + w / 2, base - h), (cx - w / 2, base - h)], val)
    ink.poly([(cx - w * 0.14, base - h), (cx + w * 0.14, base - h), (cx + w * 0.14, base - h * 1.5), (cx - w * 0.14, base - h * 1.5)], val)
    ink.ellipse(cx, base - h * 1.5, w * 0.1, w * 0.12, val)
    ink.poly([(cx - 3, base - h * 1.5 - w * 0.12), (cx + 3, base - h * 1.5 - w * 0.12), (cx, base - h * 1.5 - w * 0.2)], val)
    for k in range(-2, 3):
        ink.poly([(cx + k * w * 0.2 - w * 0.06, base - h), (cx + k * w * 0.2 + w * 0.06, base - h), (cx + k * w * 0.2, base - h - w * 0.06)], val)


def draw_split(t=0.0, gather=1.0, fly=1.0, seed=0):
    ill = paper("america", 34)
    right = paper("france", 35)
    m = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(seed)
    edge = [(540 + 8 * math.sin(y * 0.05) + rng.normal(0, 2), y) for y in range(PY0, PY1 + 10, 10)]
    rm = mask_from_poly([edge + [(PX1 + 20, PY1 + 10), (PX1 + 20, PY0)]])
    ill[:] = ill * (1 - rm[..., None]) + right * rm[..., None]
    wash(ill, rm, hexc("#8794a0"), 0.28, seed=3, gran=0.3, edge=0.1, bleed=2)
    ink = Ink()
    ink.line(edge, 2.2)
    f = font(FONT_CJK_SB, 44)
    fs = font(FONT_CJK, 28)
    over(ill, draw_text_rgba((W, H), [(298, 380, "美 国", f, (46, 33, 24, 255), "mm"), (298, 432, "“我们自己凑起来”", fs, (90, 66, 45, 255), "mm"),
                                      (782, 380, "法 国", f, (36, 40, 48, 255), "mm"), (782, 432, "“请上面来管”", fs, (60, 66, 76, 255), "mm")]))
    # left: 100,000 people as dots converging into a ring
    dots = Ink()
    rngd = np.random.default_rng(21)
    cx, cy = 298, 850
    N = 700
    for i in range(N):
        sx, sy = rngd.uniform(PX0 + 10, 530), rngd.uniform(500, PY1 - 10)
        ring = 1 + (i % 6)
        a = rngd.uniform(0, 2 * math.pi)
        rr = 110 + ring * 17 + rngd.normal(0, 3)
        tx, ty = cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.9
        g = ease(gather * 1.4 - rngd.random() * 0.4)
        x = sx + (tx - sx) * g; y = sy + (ty - sy) * g
        dots.ellipse(x, y, 2.6, 2.6)
    dots.apply(ill, INK, 0.9, grain=0.05)
    over(ill, draw_text_rgba((W, H), [(cx, cy - 18, "十万人", font(FONT_CJK_B, 40), (46, 33, 24, int(255 * ease(gather))), "mm"),
                                      (cx, cy + 32, "戒酒会", font(FONT_CJK, 30), (90, 66, 45, int(255 * ease(gather))), "mm")]))
    # right: letters flying up to the palace
    pal = Ink()
    palace(pal, 782, 640, 330)
    pal.apply(ill, hexc("#232a33"), 0.95, grain=0.04)
    over(ill, draw_text_rgba((W, H), [(782, 668, "政府", font(FONT_CJK_SB, 30), (36, 40, 48, 255), "mm")]))
    let = Ink()
    rngl = np.random.default_rng(22)
    for i in range(130):
        sx, sy = rngl.uniform(570, PX1 - 20), rngl.uniform(PY1 - 40, PY1 + 220)
        ph = (fly * 1.2 + rngl.random()) % 1.0 if fly > 0 else 0
        k = ph
        tx, ty = 782 + rngl.normal(0, 60), 600 + rngl.normal(0, 20)
        x = sx + (tx - sx) * k + 30 * math.sin(k * 6 + i)
        y = sy + (ty - sy) * k
        if y > PY1 - 5 or y < 560:
            continue
        envelope(let, x, y, 13 - 5 * k, math.sin(t * 2 + i) * 0.6)
    let.apply(ill, hexc("#232a33"), 0.85, grain=0.05)
    ink.apply(ill, INK, 0.9)
    return ill


# ====================================================================== s07 bell tower / paper route

def church(ink, x, base, s, broken=1.0, val=255):
    ink.poly([(x - s * 0.5, base), (x + s * 0.3, base), (x + s * 0.3, base - s * 0.4), (x - s * 0.5, base - s * 0.4)], 0)
    ink.line([(x - s * 0.5, base), (x + s * 0.3, base), (x + s * 0.3, base - s * 0.4), (x - s * 0.5, base - s * 0.4), (x - s * 0.5, base)], 2.0)
    ink.line([(x - s * 0.55, base - s * 0.38), (x - s * 0.1, base - s * 0.62), (x + s * 0.35, base - s * 0.38)], 2.0)
    # tower
    ink.line([(x + s * 0.3, base), (x + s * 0.3, base - s * 0.85), (x + s * 0.55, base - s * 0.85), (x + s * 0.55, base)], 2.0)
    ink.line([(x + s * 0.36, base - s * 0.72), (x + s * 0.36, base - s * 0.6), (x + s * 0.49, base - s * 0.6), (x + s * 0.49, base - s * 0.72)], 1.4)
    if broken < 1:
        ink.line([(x + s * 0.28, base - s * 0.85), (x + s * 0.425, base - s * 1.25), (x + s * 0.57, base - s * 0.85)], 2.0)
    else:
        ink.line([(x + s * 0.28, base - s * 0.85), (x + s * 0.36, base - s * 1.0), (x + s * 0.42, base - s * 0.93)], 2.0)
        ink.line([(x + s * 0.5, base - s * 0.97), (x + s * 0.57, base - s * 0.85)], 2.0)
        for k in range(4):
            ink.line([(x + s * (0.42 + 0.05 * k), base - s * (1.02 - 0.02 * k)), (x + s * (0.47 + 0.05 * k), base - s * (1.08 + 0.03 * k))], 1.6)
    ink.line([(x - s * 0.15, base), (x - s * 0.15, base - s * 0.2), (x - s * 0.02, base - s * 0.2), (x - s * 0.02, base)], 1.4)


def scroll_doc(ink, x, y, s, val=255):
    ink.line([(x - s, y - s * 0.7), (x + s, y - s * 0.7), (x + s, y + s * 0.7), (x - s, y + s * 0.7), (x - s, y - s * 0.7)], 1.6)
    for k in range(3):
        ink.line([(x - s * 0.7, y - s * 0.3 + k * s * 0.3), (x + s * 0.7, y - s * 0.3 + k * s * 0.3)], 1.0)
    ink.ellipse(x + s * 0.55, y + s * 0.55, s * 0.22, s * 0.22)


def draw_paper_route(t=0.0, doc=0.5, cal=2, seed=0):
    ill = paper("oldfrance", 36)
    rng = np.random.default_rng(seed)
    full = mask_from_poly([[(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]])
    wash(ill, full, hexc("#9aa6b0"), 0.22, seed=1, gran=0.3, edge=0.05, bleed=10)
    ink = Ink()
    # nodes
    village = (250, 1110)
    intend = (760, 830)
    paris = (420, 520)
    church(ink, village[0] - 40, village[1], 170, broken=1.0)
    for i, hx in enumerate((100, 140, 330, 380)):
        ink.line([(hx, village[1]), (hx, village[1] - 40), (hx + 30, village[1] - 40), (hx + 30, village[1]), (hx, village[1])], 1.4)
        ink.line([(hx - 4, village[1] - 38), (hx + 15, village[1] - 58), (hx + 34, village[1] - 38)], 1.4)
    # wind strokes near the tower
    for k in range(4):
        y = village[1] - 200 + 18 * k
        ink.line([(80 + 20 * k, y), (180 + 20 * k, y - 6), (230 + 20 * k, y + 2)], 1.0)
    # intendant's hôtel
    ix, ib = intend
    ink.poly([(ix - 110, ib), (ix + 110, ib), (ix + 110, ib - 90), (ix - 110, ib - 90)], 0)
    ink.line([(ix - 110, ib), (ix + 110, ib), (ix + 110, ib - 90), (ix - 110, ib - 90), (ix - 110, ib)], 2.0)
    ink.line([(ix - 120, ib - 90), (ix, ib - 130), (ix + 120, ib - 90)], 2.0)
    for k in range(6):
        ink.line([(ix - 85 + k * 34, ib - 70), (ix - 85 + k * 34, ib - 30)], 1.2)
    pal = Ink()
    palace(pal, paris[0], paris[1], 300)
    pal.apply(ill, hexc("#2a313b"), 0.9, grain=0.04)
    labels = [(village[0] - 40, village[1] + 40, "村子"), (ix, ib + 34, "省里的总督"), (paris[0], paris[1] + 32, "巴黎 · 御前会议")]
    # dotted route village -> intendant -> paris and back
    route = [(village[0] + 60, village[1] - 120), (560, 1000), (ix - 60, ib - 40), (ix - 20, ib - 150), (640, 650), (paris[0] + 120, paris[1] - 40)]
    pts = []
    for a, b in zip(route[:-1], route[1:]):
        for s_ in np.linspace(0, 1, 30, endpoint=False):
            pts.append((a[0] + (b[0] - a[0]) * s_, a[1] + (b[1] - a[1]) * s_))
    pts.append(route[-1])
    for i in range(0, len(pts) - 1, 2):
        ink.line([pts[i], pts[i + 1]], 2.2)
    for (ax, ay), (bx, by) in [(route[1], route[2]), (route[4], route[5])]:
        a = math.atan2(by - ay, bx - ax)
        ink.line([(bx - 18 * math.cos(a - 0.4), by - 18 * math.sin(a - 0.4)), (bx, by), (bx - 18 * math.cos(a + 0.4), by - 18 * math.sin(a + 0.4))], 2.2)
    # moving document
    k = int(doc * (len(pts) - 1))
    dx, dy = pts[k]
    doc_ink = Ink()
    dm = mask_from_poly([[(dx - 26, dy - 19), (dx + 26, dy - 19), (dx + 26, dy + 19), (dx - 26, dy + 19)]])
    ill[:] = ill * (1 - dm[..., None]) + hexc("#f3ead2") * dm[..., None]
    scroll_doc(doc_ink, dx, dy, 26)
    ink.apply(ill, INK, 0.88)
    doc_ink.apply(ill, INK, 0.95, grain=0.04)
    r = Ink(); r.ellipse(dx + 14, dy + 14, 6, 6); r.apply(ill, RED, 0.9)
    f = font(FONT_CJK_SB, 30)
    items = [(x, y, s, f, (36, 40, 48, 255), "mm") for x, y, s in labels]
    items += [(600, 945, "等待……", font(FONT_CJK, 26), (80, 70, 60, 255), "mm"), (680, 700, "等待……", font(FONT_CJK, 26), (80, 70, 60, 255), "mm")]
    over(ill, draw_text_rgba((W, H), items))
    # calendar
    cx0, cy0 = 820, 1010
    cm = mask_from_poly([[(cx0, cy0), (cx0 + 150, cy0), (cx0 + 150, cy0 + 170), (cx0, cy0 + 170)]])
    ill[:] = ill * (1 - cm[..., None] * 0.95) + hexc("#f3ead2") * cm[..., None] * 0.95
    ci = Ink()
    ci.line([(cx0, cy0), (cx0 + 150, cy0), (cx0 + 150, cy0 + 170), (cx0, cy0 + 170), (cx0, cy0)], 2.0)
    for k in range(5):
        ci.ellipse(cx0 + 20 + k * 27, cy0, 5, 5, None, 255, 1.6)
    ci.apply(ill, INK, 0.9)
    rb = Ink(); rb.poly([(cx0 + 2, cy0 + 2), (cx0 + 148, cy0 + 2), (cx0 + 148, cy0 + 44), (cx0 + 2, cy0 + 44)]); rb.apply(ill, RED, 0.85)
    over(ill, draw_text_rgba((W, H), [(cx0 + 75, cy0 + 23, "等了", font(FONT_CJK_SB, 26), (245, 235, 220, 255), "mm"),
                                      (cx0 + 75, cy0 + 108, f"{['一','两','三'][min(2, cal - 1)]}年", font(FONT_CJK_B, 54), (40, 30, 24, 255), "mm")]))
    return ill


# ====================================================================== s08 circle

def draw_circle(t=0.0, drawn=1.0, out=1.0, turned=1.0, shrink=0.6, gray=0.6, seed=0):
    ill = paper("gray", 37)
    rng = np.random.default_rng(seed)
    cx, cy, R = 470, 800, 330
    ink = Ink()
    n = 120
    pts = [(cx + R * math.cos(2 * math.pi * i / n - math.pi / 2), cy + R * 0.92 * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(int(n * drawn) + 1)]
    if len(pts) > 1:
        ink.line(pts, 6.0)
    ink.apply(ill, INK, 0.9)
    sil = Ink()
    rngc = np.random.default_rng(8)
    spots = []
    while len(spots) < 11:
        a = rngc.uniform(0, 2 * math.pi); r = R * 0.75 * math.sqrt(rngc.random())
        x, y = cx + r * math.cos(a), cy + 60 + r * 0.8 * math.sin(a)
        if all(abs(x - sx) > 75 or abs(y - sy) > 55 for sx, sy in spots):
            spots.append((x, y))
    spots.sort(key=lambda p: p[1])
    ox = cx + (R + 150) * out if out < 1 else cx + R + 160
    oy = cy + 170
    for i, (x, y) in enumerate(spots):
        face_out = 1 if x < ox else -1
        f = face_out if turned < (0.3 + 0.04 * i) else -face_out
        person(sil, x, y, 135, "talk" if i % 3 == 0 else "stand", f, ["top", "wide", None, "cap"][i % 4], i % 5 == 2, arm_t=t + i)
    sil.apply(ill, INK, 0.95, grain=0.05)
    # the one who stepped out
    o = Ink()
    person(o, ox, oy, 140, "talk" if shrink < 0.5 else "stand", -1, "top", arm_t=t)
    o.apply(ill, hexc("#3b3632"), 0.9, grain=0.05)
    if shrink < 1:
        k = 1 - shrink
        speech_bubble(ill, ox - 40, oy - 210 + 40 * shrink, 140 * k + 30, 70 * k + 18, "我觉得……" if k > 0.6 else "", (ox - 10, oy - 140), op=0.95, size=int(30 * max(0.4, k)))
    if gray > 0:
        g = ill.mean(axis=2, keepdims=True)
        m = np.zeros((H, W, 1), np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.clip((np.hypot(xx - ox, (yy - oy + 60) * 0.7) - 90) / 260, 0, 1)
        m[..., 0] = (1 - d) * gray
        ill[:] = ill * (1 - m) + (g * 0.85 + 0.06) * m
    return ill
