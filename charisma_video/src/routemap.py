# -*- coding: utf-8 -*-
"""The recurring 'six roads' map: a glowing circle (charisma) that goes dark and
splits into six gold roads (Weber §11 a–f)."""
import math
import skia
from engine import *
from shapes import drop_path

O = (540.0, 745.0)
R0 = 78.0

ROADS = [
    # name, weber letter, angle of departure, waypoints, endpoint, label side, cost text
    dict(name="寻找", sub="按标志找下一个", letter="a", ang=-125,
         pts=[(420, 640), (372, 566), (292, 522), (215, 470)], side="up", cost="（本期不展开）"),
    dict(name="抽签·神谕", sub="交给天意", letter="b", ang=-55,
         pts=[(660, 640), (708, 566), (788, 522), (865, 470)], side="up", cost="选中的人，未必人人服"),
    dict(name="前任指定", sub="他亲自点名", letter="c", ang=-4,
         pts=[(700, 772), (778, 736), (850, 774), (905, 800)], side="down", cost="挑人的那一眼，\n会被亲情蒙住"),
    dict(name="推选＋认可", sub="班底推出，众人认可", letter="d", ang=52,
         pts=[(628, 880), (690, 950), (760, 1050), (850, 1110)], side="down", cost="吵起来，三年选不出"),
    dict(name="血统", sub="魅力在血里", letter="e", ang=128,
         pts=[(452, 880), (390, 950), (320, 1050), (230, 1110)], side="down", cost="谁算这个血统？\n说不清，就骨肉相残"),
    dict(name="职位", sub="魅力在位子上", letter="f", ang=184,
         pts=[(380, 772), (302, 736), (230, 774), (175, 800)], side="down", cost="位子一直发光，\n坐上去的人未必"),
]

def road_path(i):
    r = ROADS[i]
    a = math.radians(r["ang"])
    start = (O[0] + R0 * math.cos(a), O[1] + R0 * math.sin(a))
    dy = O[1] - 760.0
    return path_from([start] + [(x, y + dy) for x, y in r["pts"]], smooth=True)

_PATHS = None
def paths():
    global _PATHS
    if _PATHS is None:
        _PATHS = [road_path(i) for i in range(6)]
    return _PATHS

# ------------------------------------------------------------------ icons
def icon(c, i, x, y, s, col, alpha):
    p = paint(col, alpha, stroke=2.6 * s)
    f = paint(col, alpha)
    if i == 0:  # eye
        pa = skia.Path(); pa.moveTo(x - 17 * s, y); pa.quadTo(x, y - 15 * s, x + 17 * s, y)
        pa.quadTo(x, y + 15 * s, x - 17 * s, y); pa.close()
        c.drawPath(pa, p); c.drawCircle(x, y, 5 * s, f)
    elif i == 1:  # lot tube with sticks
        for k, dx in enumerate((-6, -2, 3, 7)):
            c.drawLine(x + dx * s, y - 2 * s, x + (dx + (k - 1.5) * 2.5) * s, y - 20 * s, p)
        rr = skia.Rect.MakeXYWH(x - 11 * s, y - 4 * s, 22 * s, 22 * s)
        c.drawRect(rr, paint(INK, alpha)); c.drawRect(rr, p)
        c.drawLine(x - 11 * s, y + 4 * s, x + 11 * s, y + 4 * s, paint(col, alpha, stroke=1.4 * s))
    elif i == 2:  # pointing hand
        pa = skia.Path()
        pts = [(-14, -2), (-14, 10), (-4, 14), (6, 12), (8, 6), (4, 4), (8, 2), (6, -3), (22, -3),
               (22, -8), (4, -8), (-2, -12), (-8, -8)]
        pa = path_from([(x + a * s, y + b * s) for a, b in pts], closed=True)
        c.drawPath(pa, p)
    elif i == 3:  # ballot box + raised hands
        rr = skia.Rect.MakeXYWH(x - 13 * s, y - 2 * s, 26 * s, 18 * s)
        c.drawRect(rr, p)
        c.drawLine(x - 6 * s, y - 2 * s, x + 6 * s, y - 2 * s, paint(INK, alpha, stroke=3 * s))
        c.drawRect(skia.Rect.MakeXYWH(x - 4 * s, y - 16 * s, 9 * s, 12 * s), f)
        for dx in (-19, 19):
            c.drawLine(x + dx * s, y + 4 * s, x + dx * s * 1.1, y - 12 * s, p)
    elif i == 4:  # blood drop
        c.drawPath(drop_path(x, y + 3 * s, 11 * s), f)
    elif i == 5:  # crown over vestment
        pa = path_from([(x - 14 * s, y - 2 * s), (x - 14 * s, y - 16 * s), (x - 7 * s, y - 8 * s),
                        (x, y - 19 * s), (x + 7 * s, y - 8 * s), (x + 14 * s, y - 16 * s),
                        (x + 14 * s, y - 2 * s)], closed=True)
        c.drawPath(pa, f)
        pa2 = path_from([(x - 12 * s, y + 18 * s), (x - 8 * s, y + 2 * s), (x + 8 * s, y + 2 * s),
                         (x + 12 * s, y + 18 * s)], closed=True)
        c.drawPath(pa2, p)
        c.drawLine(x, y + 4 * s, x, y + 17 * s, paint(col, alpha, stroke=1.6 * s))

# ------------------------------------------------------------------ main draw
def draw_map(c, glow=1.0, extinguish=0.0, split=0.0, icons=0.0, labels=None, costs=None,
             active=None, travel=0.0, dim_others=0.0, show_center_label=0.0, final=0.0,
             faded=None):
    """glow: brightness of the circle; extinguish 0..1 (goes dark); split 0..1 roads grow;
    labels/costs: list of 6 alphas; active: index of highlighted road; travel 0..1 dot."""
    labels = labels or [0] * 6
    costs = costs or [0] * 6
    faded = faded or [0] * 6
    ox, oy = O
    # faint cartographic rings
    for k, rr in enumerate((150, 260, 380, 500)):
        c.drawCircle(ox, oy, rr, paint(GOLD_DIM, 0.10 + 0.05 * (k == 0), stroke=1.0))
    for k in range(72):
        a = math.radians(k * 5)
        r1, r2 = (500, 512) if k % 6 else (494, 518)
        c.drawLine(ox + r1 * math.cos(a), oy + r1 * math.sin(a), ox + r2 * math.cos(a), oy + r2 * math.sin(a),
                   paint(GOLD_DIM, 0.22, stroke=1.2))
    # --- roads
    P = paths()
    for i in range(6):
        g = clamp(split * 1.25 - i * 0.05)
        if g <= 0:
            continue
        is_act = active == i
        dimk = 1.0 - (dim_others if (active is not None and not is_act) else 0.0)
        dimk *= (1 - 0.55 * faded[i])
        base_col = GOLD if not is_act else GOLD_HI
        width = 5.0 if i != 0 else 4.0
        p = paint(base_col, 0.95 * dimk, stroke=width)
        if i == 0:
            p.setPathEffect(skia.DashPathEffect.Make([14, 12], 0))
        # glow under road
        pg = paint(GOLD, 0.35 * dimk * (1.6 if is_act else 1.0), stroke=width * 3.2, blur=7)
        draw_path_progress(c, P[i], pg, g)
        if i == 0 and g < 1:
            # dashed + trim: draw dashed fully but mask by trim → approximate via progress segments
            pp = skia.Paint(p); pp.setPathEffect(dash_trim(14, 12, g))
            c.drawPath(P[i], pp)
        else:
            draw_path_progress(c, P[i], p, g)
        # endpoint marker
        if g >= 0.999:
            (ex, ey), _, _ = path_point(P[i], 1.0)
            c.drawCircle(ex, ey, 11, paint(INK, dimk))
            c.drawCircle(ex, ey, 11, paint(base_col, dimk, stroke=3))
            c.drawCircle(ex, ey, 4.5, paint(base_col, dimk))
        if is_act and travel > 0:
            (tx, ty), _, _ = path_point(P[i], travel)
            glow_circle(c, tx, ty, 16, GOLD_HI, 1.0)
            c.drawCircle(tx, ty, 6, paint(IVORY))
    # --- center circle
    ex = ease(extinguish)
    lum = glow * (1 - ex)
    if lum > 0.01:
        radial(c, ox, oy, R0 * 3.2, (*GOLD_HI, 120), (*GOLD, 0), alpha=lum)
        radial(c, ox, oy, R0 * 1.6, (*GOLD_HI, 255), (*GOLD, 0), alpha=lum)
        # rays
        for k in range(24):
            a = math.radians(k * 15 + 7)
            ln = R0 * (1.5 + 0.35 * ((k * 7) % 5) / 4)
            c.drawLine(ox + R0 * 1.05 * math.cos(a), oy + R0 * 1.05 * math.sin(a),
                       ox + ln * math.cos(a), oy + ln * math.sin(a), paint(GOLD_HI, 0.25 * lum, stroke=2))
    # disc
    disc_col = mix((40, 34, 20), GOLD_HI, lum)
    c.drawCircle(ox, oy, R0, paint(disc_col))
    c.drawCircle(ox, oy, R0, paint(mix(GOLD_DIM, GOLD_HI, lum), 1.0, stroke=3))
    c.drawCircle(ox, oy, R0 - 10, paint(mix(GOLD_DIM, (255, 240, 200), lum), 0.6, stroke=1.2))
    # cracks after extinguish
    if split > 0:
        for i in range(6):
            a = math.radians(ROADS[i]["ang"])
            g = clamp(split * 3)
            c.drawLine(ox + (R0 - 4) * math.cos(a), oy + (R0 - 4) * math.sin(a),
                       ox + (R0 - 4 - 40 * g) * math.cos(a + 0.25), oy + (R0 - 4 - 40 * g) * math.sin(a + 0.25),
                       paint(GOLD_DIM, 0.9, stroke=2))
    # centre label
    lab_a = max(show_center_label, 0)
    if lab_a > 0:
        col = mix(GOLD_HI, INK, lum)
        draw_text(c, "他", ox, oy + 22, "serif_b", 62, mix(GOLD, (60, 40, 10), lum), lab_a, align="center")
    # --- icons at forks
    if icons > 0:
        for i in range(6):
            (ix, iy), _, _ = path_point(P[i], 0.30)
            a = clamp(icons * 1.4 - i * 0.08)
            if a <= 0:
                continue
            dimk = 1.0 - (dim_others if (active is not None and active != i) else 0.0)
            dimk *= (1 - 0.55 * faded[i])
            c.drawCircle(ix, iy, 33, paint(INK, a * 0.92 * dimk))
            c.drawCircle(ix, iy, 33, paint(GOLD, a * dimk, stroke=2.2))
            icon(c, i, ix, iy, 1.0, GOLD_HI if active == i else GOLD, a * dimk)
    # --- labels
    for i in range(6):
        la = labels[i]
        if la <= 0 and costs[i] <= 0:
            continue
        dimk = 1.0 - (dim_others if (active is not None and active != i) else 0.0)
        r = ROADS[i]
        (ex, ey), _, _ = path_point(P[i], 1.0)
        lx = clamp(ex, 135, W - 135)
        if r["side"] == "up":
            ny = ey - 120
        else:
            ny = ey + 58
        if la > 0:
            col = GOLD_HI if active == i else IVORY
            draw_text(c, r["name"], lx, ny, "serif_sb", 36, col, la * dimk, align="center")
            nw = text_width(r["name"], "serif_sb", 36)
            draw_text(c, r["letter"] + ")", lx - nw / 2 - 10, ny, "garamond_i", 28, GOLD, la * dimk * 0.9, align="right")
            draw_text(c, r["sub"], lx, ny + 36, "sans", 23, MUTED, la * dimk, align="center")
        if costs[i] > 0:
            ca = costs[i] * (1.0 - 0.3 * (dim_others if (active is not None and active != i) else 0))
            col = MUTED if i == 0 else RED
            lines = r["cost"].split("\n")
            for k, ln in enumerate(lines):
                draw_text(c, ln, lx, ny + 72 + k * 31, "sans_m", 23, col, ca, align="center")
