# -*- coding: utf-8 -*-
"""Modern companies, flat style: the frozen portrait (Disney) and the classroom (Apple University).
No logos, no characters, no real faces."""
import math, random
import skia
from engine import *
from shapes import bull_paths, bull_lines

ICE = (176, 214, 232)
TEAL = (16, 40, 44)
BOARD = (28, 58, 46)
CHALK = (232, 236, 226)

def frozen_portrait(c, cx, cy, w, h, ice=0.0, alpha=1.0, label=True):
    # frame
    fr = skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h)
    c.drawRect(fr.makeOutset(18, 18), paint((0, 0, 0), 0.4 * alpha, blur=12))
    c.drawRect(fr.makeOutset(16, 16), paint((176, 140, 70), alpha))
    c.drawRect(fr, paint((226, 212, 180), alpha))
    # silhouette (front, head & shoulders)
    sil = (52, 46, 40)
    c.save(); c.clipRect(fr)
    c.drawOval(skia.Rect.MakeXYWH(cx - w * 0.17, cy - h * 0.30, w * 0.34, h * 0.36), paint(sil, alpha))
    c.drawOval(skia.Rect.MakeXYWH(cx - w * 0.19, cy - h * 0.34, w * 0.38, h * 0.18), paint(sil, alpha))
    sh = path_from([(cx - w * 0.45, cy + h * 0.55), (cx - w * 0.38, cy + h * 0.18), (cx - w * 0.12, cy + h * 0.06),
                    (cx, cy + h * 0.08), (cx + w * 0.12, cy + h * 0.06), (cx + w * 0.38, cy + h * 0.18),
                    (cx + w * 0.45, cy + h * 0.55)], closed=True, smooth=True)
    c.drawPath(sh, paint(sil, alpha))
    # ice
    if ice > 0:
        c.drawRect(fr, paint(ICE, 0.55 * ice * alpha))
        rnd = random.Random(2)
        for k in range(int(40 * ice)):
            x = fr.left() + rnd.random() * w; y = fr.top() + rnd.random() * h
            L = 20 + rnd.random() * 60
            a0 = rnd.random() * math.pi
            for j in range(3):
                a = a0 + j * math.pi / 3
                c.drawLine(x - L * math.cos(a), y - L * math.sin(a), x + L * math.cos(a), y + L * math.sin(a),
                           paint((240, 250, 255), 0.55 * alpha, stroke=1.6))
        # frost creeping from edges
        for side in range(4):
            for k in range(14):
                t = k / 13
                if side == 0: x, y = fr.left() + t * w, fr.top()
                elif side == 1: x, y = fr.right(), fr.top() + t * h
                elif side == 2: x, y = fr.left() + t * w, fr.bottom()
                else: x, y = fr.left(), fr.top() + t * h
                c.drawCircle(x, y, 40 * ice * (0.6 + 0.4 * math.sin(k * 2.3 + side)), paint((235, 246, 252), 0.7 * alpha, blur=6))
    c.restore()
    c.drawRect(fr.makeOutset(16, 16), paint((120, 90, 40), alpha, stroke=3))
    if ice > 0.3:
        c.drawRect(fr.makeOutset(16, 16), paint((235, 246, 252), (ice - 0.3) * alpha, stroke=6))

def blackboard_bulls(c, x0, y0, w, h, stage=4.0, alpha=1.0):
    bx = skia.Rect.MakeXYWH(x0, y0, w, h)
    c.drawRect(bx.makeOutset(14, 14), paint((110, 74, 40), alpha))
    c.drawRect(bx, paint(BOARD, alpha))
    # chalk smudge
    radial(c, x0 + w * 0.3, y0 + h * 0.4, w * 0.4, (255, 255, 255, 18), (255, 255, 255, 0), alpha=alpha)
    n = 4
    cw = w / n
    for i in range(n):
        a = clamp(stage - i) * alpha
        if a <= 0:
            continue
        cx = x0 + cw * (i + 0.5); cy = y0 + h * 0.48
        s = cw * 0.44
        if i == 0:
            body, tail, h1, h2 = bull_paths(cx, cy, s)
            pg = skia.Paint(AntiAlias=True)
            pg.setShader(skia.GradientShader.MakeLinear(points=[(cx, cy - 0.4 * s), (cx, cy + 0.8 * s)],
                         colors=[C(*CHALK, 235 * a), C(150, 160, 150, 200 * a)]))
            c.drawPath(body, pg)
            for k in range(6):
                pa = path_from([(cx + (-0.3 + k * 0.15) * s, cy - 0.25 * s), (cx + (-0.25 + k * 0.15) * s, cy + 0.05 * s),
                                (cx + (-0.3 + k * 0.15) * s, cy + 0.3 * s)], smooth=True)
                c.drawPath(pa, paint(BOARD, 0.35 * a, stroke=2))
            for pa in (tail, h1, h2):
                c.drawPath(pa, paint(CHALK, 0.85 * a, stroke=3))
        elif i == 1:
            body, tail, h1, h2 = bull_paths(cx, cy, s)
            c.drawPath(body, paint(CHALK, 0.85 * a, stroke=3))
            # planes
            for seg in [((-0.5, -0.3), (0.0, 0.3)), ((0.0, -0.3), (0.0, 0.36)), ((0.0, 0.0), (0.66, 0.0)),
                        ((-0.6, 0.06), (-0.2, -0.4)), ((0.36, -0.26), (0.5, 0.34))]:
                (a1, b1), (a2, b2) = seg
                c.drawLine(cx + a1 * s, cy + b1 * s, cx + a2 * s, cy + b2 * s, paint(CHALK, 0.7 * a, stroke=2.4))
            for pa in (tail, h1, h2):
                c.drawPath(pa, paint(CHALK, 0.85 * a, stroke=3))
        elif i == 2:
            body, tail, h1, h2 = bull_paths(cx, cy, s)
            c.drawPath(body, paint(CHALK, 0.85 * a, stroke=3))
            for pa in (tail, h1):
                c.drawPath(pa, paint(CHALK, 0.85 * a, stroke=3))
        else:
            for pa in bull_lines(cx, cy, s):
                c.drawPath(pa, paint(CHALK, 0.95 * a, stroke=3.4))
        if i < n - 1 and a > 0.5:
            ax = x0 + cw * (i + 1)
            c.drawLine(ax - 10, cy + s * 0.9, ax + 10, cy + s * 0.9, paint(CHALK, 0.5 * a, stroke=2))
            c.drawLine(ax + 4, cy + s * 0.9 - 6, ax + 10, cy + s * 0.9, paint(CHALK, 0.5 * a, stroke=2))
            c.drawLine(ax + 4, cy + s * 0.9 + 6, ax + 10, cy + s * 0.9, paint(CHALK, 0.5 * a, stroke=2))
    draw_text(c, "简化", x0 + w - 24, y0 + 56, "serif_sb", 38, CHALK, alpha * 0.9, align="right")

def classroom(c, y0, stage=4.0, alpha=1.0):
    # wall
    c.drawRect(skia.Rect.MakeLTRB(60, y0, W - 60, y0 + 462), paint((30, 52, 54), alpha))
    blackboard_bulls(c, 110, y0 + 40, 860, 250, stage, alpha)
    # desks + students (flat circles)
    for row in range(2):
        for k in range(5):
            x = 170 + k * 185 + row * 40
            y = y0 + 360 + row * 62
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 58, y + 20, 116, 30), 6, 6), paint((150, 120, 84), alpha))
            c.drawCircle(x, y, 26, paint((14, 24, 26), alpha))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 42, y + 16, 84, 40), 18, 18), paint((14, 24, 26), alpha))

def draw_companies(c, ice=1.0, stage=4.0, top_a=1.0, bot_a=1.0):
    draw_bg(c, tint=((8, 22, 24), (16, 40, 44)))
    # top: frozen portrait
    if top_a > 0:
        frozen_portrait(c, 540, 480, 240, 290, ice, top_a)
        draw_text(c, "把“他”变成一个问题", 540, 690, "serif_sb", 36, ICE, top_a, align="center")
        draw_text(c, "“What would Walt do?”", 540, 734, "garamond_i", 30, MUTED, top_a, align="center")
    if bot_a > 0:
        classroom(c, 772, stage, bot_a)
        draw_text(c, "把“他怎么想”，教下去", 540, 1300, "serif_sb", 34, GOLD_HI, bot_a, align="center")
