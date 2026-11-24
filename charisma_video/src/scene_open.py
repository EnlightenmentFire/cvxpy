# -*- coding: utf-8 -*-
"""Cold open (1970s meeting room, illustrative), title card, Weber 1919."""
import math
import skia
from engine import *
from shapes import profile_path, beard_path, xf

# 1970s muted palette
WALL = (58, 44, 30)
WALL_LINE = (44, 32, 22)
TABLE = (96, 64, 38)
TABLE_HI = (128, 88, 52)
SUIT = [(52, 46, 36), (40, 44, 40), (62, 50, 40), (36, 38, 46), (58, 52, 34), (48, 40, 34)]
SKIN = (150, 112, 86)
HAIR = [(30, 22, 16), (60, 42, 26), (24, 22, 20), (88, 70, 46), (36, 28, 22), (70, 58, 50)]

TABLE_FAR_Y, TABLE_NEAR_Y = 760, 1190
TABLE_FAR_W, TABLE_NEAR_W = 400, 760

def table_x(y, side):
    k = (y - TABLE_FAR_Y) / (TABLE_NEAR_Y - TABLE_FAR_Y)
    w = lerp(TABLE_FAR_W, TABLE_NEAR_W, k)
    return W / 2 + side * w / 2

def person(c, x, y, scale, facing, look_up, suit, hair, alpha=1.0, lit=0.0):
    """top-down-ish seated figure: shoulders + head. facing: angle (rad) toward table;
    look_up: 0..1 turns head toward the portrait (up)."""
    sh = skia.Rect.MakeXYWH(x - 46 * scale, y - 22 * scale, 92 * scale, 52 * scale)
    c.drawRRect(skia.RRect.MakeRectXY(sh, 26 * scale, 26 * scale), paint(suit, alpha))
    # shirt/tie hint
    c.drawCircle(x + math.cos(facing) * 10 * scale, y + math.sin(facing) * 10 * scale - 6 * scale, 9 * scale,
                 paint((150, 140, 120), alpha * 0.5))
    # head position moves slightly toward wall when looking up
    hx = x + math.cos(facing) * 6 * scale
    hy = y - 10 * scale - look_up * 8 * scale
    r = 25 * scale
    c.drawCircle(hx, hy, r, paint(hair, alpha))
    # face visible on the side we look toward
    gaze = lerp(facing, -math.pi / 2, look_up) if abs(facing + math.pi / 2) > 1e-3 else facing
    fx, fy = hx + math.cos(gaze) * r * 0.42, hy + math.sin(gaze) * r * 0.42
    c.save()
    c.clipPath(path_from([(hx + r * math.cos(a), hy + r * math.sin(a)) for a in
                          [2 * math.pi * k / 30 for k in range(30)]], closed=True), doAntiAlias=True)
    face_col = mix(SKIN, (230, 190, 140), lit * look_up * 0.6)
    c.drawCircle(fx, fy, r * 0.72, paint(face_col, alpha * (0.55 + 0.45 * look_up)))
    c.restore()

PEOPLE = [  # (y, side, suit idx)
    (840, -1, 0), (960, -1, 1), (1080, -1, 2),
    (840, 1, 3), (960, 1, 4), (1080, 1, 5),
]

def draw_meeting(c, look_up=0.0, line_a=0.0, zh_a=0.0, portrait_glow=0.5, chair_a=1.0, cam=0.0):
    # background wall
    c.save()
    c.translate(0, -cam * 40)
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, 740), paint(WALL))
    for k in range(0, W, 54):
        c.drawLine(k, 0, k, 740, paint(WALL_LINE, 0.8, stroke=3))
    # floor
    c.drawRect(skia.Rect.MakeLTRB(0, 740, W, H), paint((34, 40, 36)))
    for k in range(-20, 30):  # carpet lines in perspective
        x0 = W / 2 + k * 40
        x1 = W / 2 + k * 150
        c.drawLine(x0, 740, x1, H, paint((28, 34, 30), 0.8, stroke=2))
    c.drawLine(0, 740, W, 740, paint((20, 16, 12), stroke=6))
    # light pool from portrait / lamp
    radial(c, W / 2, 520, 520, (255, 220, 150, 90), (255, 200, 120, 0), alpha=0.6 + 0.4 * portrait_glow)
    # portrait frame (oval, gilt)
    px, py, pw, ph = W / 2, 470, 230, 290
    oval = skia.Rect.MakeXYWH(px - pw / 2, py - ph / 2, pw, ph)
    c.drawOval(oval.makeOutset(26, 26), paint((0, 0, 0), 0.5, blur=14))
    c.drawOval(oval.makeOutset(22, 22), paint((150, 112, 40)))
    c.drawOval(oval.makeOutset(22, 22), paint(GOLD_HI, 0.7, stroke=3))
    c.drawOval(oval.makeOutset(8, 8), paint((110, 80, 30)))
    inner = skia.Paint(AntiAlias=True)
    inner.setShader(skia.GradientShader.MakeRadial(center=(px, py - 30), radius=ph * 0.7,
                    colors=[C(236, 214, 170), C(176, 146, 100)]))
    c.drawOval(oval, inner)
    # silhouette in portrait: head & shoulders, front-facing, smiling hint via cheek line
    c.save(); c.clipPath(path_from([(px + pw / 2 * math.cos(a), py + ph / 2 * math.sin(a)) for a in
                                    [2 * math.pi * k / 48 for k in range(48)]], closed=True), doAntiAlias=True)
    sil = (46, 36, 28)
    c.drawOval(skia.Rect.MakeXYWH(px - 52, py - 92, 104, 128), paint(sil))
    c.drawOval(skia.Rect.MakeXYWH(px - 60, py - 104, 120, 70), paint(sil))  # hair
    sh = path_from([(px - 120, py + 150), (px - 104, py + 72), (px - 40, py + 40), (px, py + 46),
                    (px + 40, py + 40), (px + 104, py + 72), (px + 120, py + 150)], closed=True, smooth=True)
    c.drawPath(sh, paint(sil))
    c.drawRect(skia.Rect.MakeXYWH(px - 22, py + 20, 44, 34), paint(sil))
    c.restore()
    # table
    tp = path_from([(table_x(TABLE_FAR_Y, -1), TABLE_FAR_Y), (table_x(TABLE_FAR_Y, 1), TABLE_FAR_Y),
                    (table_x(TABLE_NEAR_Y, 1), TABLE_NEAR_Y), (table_x(TABLE_NEAR_Y, -1), TABLE_NEAR_Y)], closed=True)
    c.drawPath(tp, paint(TABLE))
    pg = skia.Paint(AntiAlias=True)
    pg.setShader(skia.GradientShader.MakeLinear(points=[(0, TABLE_FAR_Y), (0, TABLE_NEAR_Y)],
                 colors=[C(*TABLE_HI, 200), C(*TABLE, 0)]))
    c.drawPath(tp, pg)
    c.drawPath(tp, paint((60, 40, 24), stroke=4))
    # empty chair at the head of the table (under the portrait)
    cx, cy = W / 2, TABLE_FAR_Y - 36
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 62, cy - 34, 124, 56), 18, 18), paint((70, 34, 26), chair_a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - 62, cy - 34, 124, 56), 18, 18), paint((110, 60, 44), chair_a, stroke=3))
    # papers, cups
    import random
    rnd = random.Random(4)
    for (y, side, _) in PEOPLE:
        xx = table_x(y, side) - side * 70
        c.save(); c.translate(xx, y + 6); c.rotate(rnd.uniform(-14, 14))
        c.drawRect(skia.Rect.MakeXYWH(-34, -24, 68, 48), paint((214, 206, 186), 0.85))
        for k in range(4):
            c.drawLine(-26, -14 + k * 9, 22, -14 + k * 9, paint((120, 110, 100), 0.5, stroke=1.5))
        c.restore()
        c.drawCircle(xx - side * 60, y - 30, 13, paint((226, 220, 206)))
        c.drawCircle(xx - side * 60, y - 30, 8, paint((70, 44, 26)))
    # ashtray + pitcher
    c.drawCircle(W / 2 + 30, 1010, 22, paint((90, 110, 100)))
    c.drawCircle(W / 2 + 30, 1010, 12, paint((50, 60, 56)))
    # people
    for k, (y, side, si) in enumerate(PEOPLE):
        x = table_x(y, side) + side * 52
        facing = math.pi if side > 0 else 0.0
        person(c, x, y, 1.22 + (y - 840) / 1400, facing, look_up, SUIT[si], HAIR[si], lit=portrait_glow)
    # near-end person (back to camera)
    person(c, W / 2, TABLE_NEAR_Y + 52, 1.25, -math.pi / 2, 0.0, (44, 40, 34), (28, 22, 18))
    c.restore()
    # darken lower part for text legibility
    pg = skia.Paint(AntiAlias=True)
    pg.setShader(skia.GradientShader.MakeLinear(points=[(0, 1150), (0, 1500)],
                 colors=[C(*BG0, 0), C(*BG0, 255)]))
    c.drawRect(skia.Rect.MakeLTRB(0, 1150, W, H), pg)
    # floating line
    if line_a > 0:
        y = 1040 - 30 * ease_out(line_a)
        bx = skia.Rect.MakeXYWH(90, y - 92, 900, 190 if zh_a > 0 else 130)
        c.drawRRect(skia.RRect.MakeRectXY(bx, 18, 18), paint(INK, 0.5 * line_a, blur=10))
        draw_text(c, "“What would Walt do?”", W / 2, y, "garamond_i", 76, GOLD_HI, line_a, align="center",
                  glow=8, glow_color=GOLD)
        draw_text(c, "沃尔特会怎么做？", W / 2, y + 70, "serif_sb", 44, IVORY, zh_a, align="center")

# ---------------------------------------------------------------- title card
def draw_title(c, a=1.0, sub_a=1.0, glow=0.6):
    draw_bg(c)
    radial(c, W / 2, 700, 420, (*GOLD_HI, 110), (*GOLD, 0), alpha=glow)
    c.drawCircle(W / 2, 700, 92, paint(mix((40, 34, 20), GOLD_HI, glow)))
    c.drawCircle(W / 2, 700, 92, paint(GOLD, 1, stroke=3))
    draw_text(c, "他走了以后", W / 2, 1000, "serif_b", 118, GOLD_HI, a, align="center", tracking=0.08,
              glow=14 * a, glow_color=GOLD)
    draw_text(c, "魅力的日常化", W / 2, 1090, "serif_sb", 44, IVORY, sub_a, align="center", tracking=0.3)
    draw_text(c, "Die Veralltäglichung des Charisma", W / 2, 1150, "garamond_i", 36, GOLD, sub_a * 0.9, align="center")

# ---------------------------------------------------------------- Weber 1919
CARDS = [
    dict(n="一", big="一直如此", lab="传统", de="die Autorität des „ewig Gestrigen“", zh="“永远的昨天”的权威"),
    dict(n="二", big="这个人不一般", lab="卡里斯玛", de="die Autorität der außeralltäglichen persönlichen Gnadengabe (Charisma)",
         zh="一个人身上超乎寻常的、天赐恩典的权威"),
    dict(n="三", big="规则这么写", lab="法理", de="Herrschaft kraft „Legalität“", zh="凭“合法性”的支配"),
]

def draw_lecture(c, a=1.0, y0=330):
    """silhouette lecture hall, 1919"""
    if a <= 0:
        return
    # warm lamp
    radial(c, 720, y0 + 120, 380, (255, 210, 140, 110), (255, 200, 120, 0), alpha=a)
    # window panes behind (winter light)
    for k in range(3):
        r = skia.Rect.MakeXYWH(150 + k * 120, y0 + 20, 90, 200)
        c.drawRect(r, paint((70, 96, 110), 0.25 * a))
        c.drawLine(r.centerX(), r.top(), r.centerX(), r.bottom(), paint(INK, 0.5 * a, stroke=4))
        c.drawLine(r.left(), r.centerY(), r.right(), r.centerY(), paint(INK, 0.5 * a, stroke=4))
    sil = (8, 14, 12)
    # lecturer (profile facing left) behind lectern
    hx, hy = 760, y0 + 140
    head = profile_path(hx, hy, 80, flip=True)
    c.drawPath(head, paint(sil, a))
    c.drawPath(beard_path(hx, hy, 80, flip=True), paint(sil, a))
    body = path_from([(hx - 30, hy + 50), (hx + 30, hy + 50), (hx + 84, hy + 82), (hx + 96, hy + 260),
                      (hx - 76, hy + 260), (hx - 70, hy + 90)], closed=True, smooth=True)
    c.drawPath(body, paint(sil, a))
    lect = path_from([(hx - 150, hy + 120), (hx - 10, hy + 100), (hx - 30, hy + 290), (hx - 130, hy + 290)], closed=True)
    c.drawPath(lect, paint((20, 26, 22), a))
    c.drawPath(lect, paint(GOLD_DIM, 0.5 * a, stroke=2))
    # audience heads (backs)
    for row in range(2):
        for k in range(7):
            x = 90 + k * 125 + (row * 60)
            y = y0 + 330 + row * 46
            c.drawCircle(x, y, 34, paint(sil, a))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 56, y + 20, 112, 80), 30, 30), paint(sil, a))
    # caption
    draw_text(c, "1919.1.28  慕尼黑", 70, y0 + 60, "serif_sb", 36, GOLD_HI, a)
    draw_text(c, "Politik als Beruf · 以政治为业", 70, y0 + 106, "garamond_i", 30, IVORY, a * 0.9)

def draw_cards(c, appear=(1, 1, 1), highlight=1.0, y=800):
    w, gap = 318, 18
    x0 = (W - (3 * w + 2 * gap)) / 2
    for i, cd in enumerate(CARDS):
        a = appear[i]
        if a <= 0:
            continue
        x = x0 + i * (w + gap)
        yy = y + (1 - ease_out(a)) * 30
        hl = highlight if i == 1 else 0.0
        rect = skia.Rect.MakeXYWH(x, yy, w, 470)
        rr = skia.RRect.MakeRectXY(rect, 14, 14)
        if hl > 0:
            c.drawRRect(rr, paint(GOLD, 0.35 * hl * a, blur=22))
        c.drawRRect(rr, paint(mix((14, 30, 27), (44, 38, 20), hl), 0.95 * a))
        c.drawRRect(rr, paint(mix(GOLD_DIM, GOLD_HI, hl), a, stroke=2.4))
        draw_text(c, "第" + cd["n"] + "种", x + w / 2, yy + 50, "sans", 24, MUTED, a, align="center")
        draw_text(c, cd["big"], x + w / 2, yy + 118, "serif_b", 40 if len(cd["big"]) < 6 else 36,
                  GOLD_HI if hl > 0.5 else IVORY, a, align="center")
        c.drawLine(x + 40, yy + 150, x + w - 40, yy + 150, paint(GOLD_DIM, 0.8 * a, stroke=1.4))
        draw_text(c, cd["lab"], x + w / 2, yy + 200, "serif_sb", 32, GOLD if hl < 0.5 else GOLD_HI, a, align="center")
        n = draw_paragraph(c, cd["de"], x + w / 2, yy + 250, "garamond_i", 24, mix(MUTED, GOLD_HI, hl), w - 30, a,
                           line_h=1.25)
        draw_paragraph(c, cd["zh"], x + w / 2, yy + 262 + n * 31 + 8, "serif", 23, IVORY, w - 40, a * 0.9, line_h=1.4)
