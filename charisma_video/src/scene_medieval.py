# -*- coding: utf-8 -*-
"""Medieval church scenes in a stained-glass idiom: Viterbo 1268–71 (roof, key),
and the 'office charisma' window (empty figure, glowing seat)."""
import math, random
import skia
from engine import *
from shapes import gothic_arch

LEAD = (14, 14, 16)
RUBY = (150, 26, 34)
SAPPHIRE = (28, 54, 120)
AMBER = (196, 128, 36)
EMERALD = (24, 96, 64)
VIOLET = (78, 40, 96)
STONE = (92, 84, 74)
NIGHT0 = (6, 10, 24)
NIGHT1 = (18, 28, 58)

def glass(c, pa, col, alpha=1.0, lead=4.0, light=0.35, cx=None, cy=None, r=None):
    b = pa.computeTightBounds()
    cx = b.centerX() if cx is None else cx
    cy = b.centerY() if cy is None else cy
    r = max(b.width(), b.height()) * 0.8 if r is None else r
    p = skia.Paint(AntiAlias=True)
    hi = mix(col, (255, 245, 220), light)
    p.setShader(skia.GradientShader.MakeRadial(center=(cx, cy), radius=max(r, 1),
                colors=[C(*hi, 255 * alpha), C(*col, 255 * alpha), C(*mix(col, (0, 0, 0), 0.45), 255 * alpha)],
                positions=[0, 0.55, 1]))
    c.drawPath(pa, p)
    if lead > 0:
        c.drawPath(pa, paint(LEAD, alpha, stroke=lead))

def night_sky(c, rect, alpha=1.0, seed=3):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(points=[(0, rect.top()), (0, rect.bottom())],
                colors=[C(*NIGHT0, 255 * alpha), C(*NIGHT1, 255 * alpha)]))
    c.drawRect(rect, p)
    rnd = random.Random(seed)
    for _ in range(70):
        x = rnd.uniform(rect.left(), rect.right()); y = rnd.uniform(rect.top(), rect.bottom())
        c.drawCircle(x, y, rnd.uniform(0.8, 2.2), paint((230, 230, 250), alpha * rnd.uniform(0.3, 0.9)))

# roof tiles: rows on two slopes
APEX = (540, 430)
EAVE_Y = 650
LEFT, RIGHT = 130, 950

def tiles():
    out = []
    rows = 7
    for side in (-1, 1):
        for r in range(rows):
            t0 = r / rows; t1 = (r + 1) / rows
            n = 5 + r
            for k in range(n):
                u0 = k / n; u1 = (k + 1) / n
                # corners along slope: interpolate between apex and eave line
                def P(t, u):
                    ex = APEX[0] + side * (u * (APEX[0] - LEFT) * t)
                    ey = APEX[1] + (EAVE_Y - APEX[1]) * t
                    return (ex, ey)
                quad = [P(t0, u0), P(t0, u1), P(t1, u1), P(t1, u0)]
                out.append(dict(quad=quad, row=r, side=side, k=k, seed=r * 31 + k * 7 + (side > 0) * 3))
    return out

TILES = tiles()

def draw_viterbo(c, roof_off=0.0, bread=4, key=0.0, letter=0.0, moon=0.0, cardinals=1.0, inner_a=1.0):
    draw_bg(c, tint=((6, 12, 22), (14, 26, 46)))
    sky = skia.Rect.MakeLTRB(0, 0, W, H)
    night_sky(c, sky, 0.9)
    pg = skia.Paint(AntiAlias=True)
    pg.setShader(skia.GradientShader.MakeLinear(points=[(0, 1150), (0, 1500)], colors=[C(*NIGHT0, 0), C(*NIGHT0, 255)]))
    c.drawRect(skia.Rect.MakeLTRB(0, 1150, W, H), pg)
    # moon
    c.drawCircle(905, 520, 38, paint((236, 232, 210), 0.9))
    radial(c, 905, 520, 170, (236, 232, 210, 60), (236, 232, 210, 0))
    # hall walls (stone glass panels)
    hall = skia.Rect.MakeLTRB(LEFT, EAVE_Y, RIGHT, 1190)
    # interior back wall
    inner = path_from([(LEFT + 40, EAVE_Y + 10), (RIGHT - 40, EAVE_Y + 10), (RIGHT - 40, 1150), (LEFT + 40, 1150)], closed=True)
    glass(c, inner, (54, 44, 40), inner_a, lead=0, light=0.15)
    # interior windows
    for k in range(3):
        x = 250 + k * 220
        win = gothic_arch(x, 700, 130, 200)
        glass(c, win, [RUBY, SAPPHIRE, EMERALD][k], inner_a, lead=5, light=0.5)
        c.drawLine(x + 65, 712, x + 65, 900, paint(LEAD, inner_a, stroke=4))
        c.drawLine(x, 790, x + 130, 790, paint(LEAD, inner_a, stroke=3))
    # floor
    floor = path_from([(LEFT + 40, 1060), (RIGHT - 40, 1060), (RIGHT - 40, 1150), (LEFT + 40, 1150)], closed=True)
    glass(c, floor, (70, 50, 36), inner_a, lead=3, light=0.2)
    # moonlight shaft when roof is open
    if roof_off > 0.2:
        a = clamp((roof_off - 0.2) * 1.4) * 0.5
        shaft = path_from([(470, 600), (700, 600), (760, 1150), (380, 1150)], closed=True)
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear(points=[(0, 600), (0, 1150)],
                    colors=[C(220, 230, 255, 120 * a), C(220, 230, 255, 0)]))
        c.drawPath(shaft, p)
    # table
    table = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(300, 990, 780, 1040), 10, 10)
    c.drawRRect(table, paint((96, 62, 34), inner_a)); c.drawRRect(table, paint(LEAD, inner_a, stroke=3))
    # bread loaves
    for k in range(4):
        if k < bread:
            x = 380 + k * 100
            c.drawOval(skia.Rect.MakeXYWH(x - 26, 975, 52, 26), paint(AMBER, inner_a))
            c.drawOval(skia.Rect.MakeXYWH(x - 26, 975, 52, 26), paint(LEAD, inner_a, stroke=2.5))
    # cardinals (red cloaks + red caps), silhouettes from behind/side
    if cardinals > 0:
        for k in range(6):
            x = 300 + k * 96
            y = 1000 if k % 2 == 0 else 1012
            al = cardinals * inner_a
            body = path_from([(x - 40, 1110), (x - 38, y - 10), (x - 30, y - 50), (x + 30, y - 50), (x + 38, y - 10),
                              (x + 40, 1110)], closed=True)
            glass(c, body, RUBY, al, lead=3.5, light=0.3)
            cape = path_from([(x - 40, y - 2), (x - 32, y - 52), (x + 32, y - 52), (x + 40, y - 2)], closed=True)
            glass(c, cape, (120, 18, 26), al, lead=3, light=0.25)
            c.drawRect(skia.Rect.MakeXYWH(x - 9, y - 60, 18, 12), paint((230, 226, 214), al))
            c.drawCircle(x, y - 80, 21, paint((60, 44, 36), al))
            c.drawCircle(x, y - 80, 21, paint(LEAD, al, stroke=3))
            cap = skia.Path(); cap.addArc(skia.Rect.MakeXYWH(x - 19, y - 101, 38, 30), 180, 180); cap.close()
            c.drawPath(cap, paint((210, 30, 40), al))
    # outer walls (stone frame) drawn as glass panels
    for (x0, x1) in ((LEFT, LEFT + 40), (RIGHT - 40, RIGHT)):
        for k in range(6):
            y0 = EAVE_Y + k * 90
            pa = path_from([(x0, y0), (x1, y0), (x1, min(y0 + 90, 1190)), (x0, min(y0 + 90, 1190))], closed=True)
            glass(c, pa, mix(STONE, (120, 110, 96), (k % 2) * 0.4), 1.0, lead=3, light=0.2)
    base = path_from([(LEFT - 20, 1150), (RIGHT + 20, 1150), (RIGHT + 20, 1200), (LEFT - 20, 1200)], closed=True)
    glass(c, base, STONE, 1.0, lead=3, light=0.15)
    # gable wall triangle (behind tiles) – interior visible when tiles go
    # roof tiles
    rnd = random.Random(1)
    for tdef in TILES:
        # removal order: from apex row downward, randomised
        order = (tdef["row"] / 7) * 0.7 + (tdef["seed"] % 10) / 10 * 0.3
        gone = clamp((roof_off - order) / 0.12)
        if gone >= 1:
            continue
        q = tdef["quad"]
        dx = tdef["side"] * 120 * ease_in(gone)
        dy = -260 * ease_in(gone)
        rot = tdef["side"] * 40 * gone
        cx = sum(p[0] for p in q) / 4; cy = sum(p[1] for p in q) / 4
        c.save(); c.translate(cx + dx, cy + dy); c.rotate(rot); c.translate(-cx, -cy)
        pa = path_from(q, closed=True)
        col = mix((150, 70, 44), (176, 92, 56), (tdef["seed"] % 5) / 5)
        glass(c, pa, col, 1 - gone, lead=3, light=0.25)
        c.restore()
    # roof beams (remain)
    c.drawLine(APEX[0], APEX[1], LEFT - 10, EAVE_Y + 6, paint(LEAD, 1, stroke=9))
    c.drawLine(APEX[0], APEX[1], RIGHT + 10, EAVE_Y + 6, paint(LEAD, 1, stroke=9))
    c.drawLine(LEFT - 10, EAVE_Y + 6, RIGHT + 10, EAVE_Y + 6, paint(LEAD, 1, stroke=7))
    # letter caption
    if letter > 0:
        draw_text(c, "in discooperto palatio", 540, 335, "garamond_i", 46, GOLD_HI, letter, align="center")
        draw_text(c, "“在没有屋顶的宫殿里”——枢机主教们 1270 年 6 月的信", 540, 380, "serif", 26, IVORY, letter * 0.9, align="center")
    # key
    if key > 0:
        dim = 0.72 * ease(key)
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), dim))
        y = lerp(-200, 700, ease_out(key))
        radial(c, 540, y, 320, (*GOLD_HI, 70), (*GOLD, 0), alpha=ease(key))
        draw_key(c, 540, y, 1.15, rot=lerp(-25, 0, ease_out(key)))
        ta = clamp((key - 0.55) / 0.45)
        draw_text(c, "cum clave", 540, 1110, "garamond_i", 104, GOLD_HI, ta, align="center", glow=10, glow_color=GOLD)
        draw_text(c, "“带着钥匙”  →  conclave", 540, 1182, "serif_sb", 38, IVORY, ta, align="center")

def draw_key(c, x, y, s, rot=0.0, alpha=1.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    iron = (96, 80, 56)
    hi = (240, 210, 140)
    # bow (ring)
    c.drawCircle(0, -150, 70, paint(iron, alpha, stroke=26))
    c.drawCircle(0, -150, 70, paint(hi, alpha * 0.5, stroke=4))
    # quatrefoil in bow
    for a in range(4):
        aa = math.radians(a * 90 + 45)
        c.drawCircle(30 * math.cos(aa), -150 + 30 * math.sin(aa), 18, paint(iron, alpha, stroke=7))
    # shaft
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-13, -82, 26, 280), 8, 8), paint(iron, alpha))
    c.drawLine(-6, -80, -6, 190, paint(hi, alpha * 0.4, stroke=3))
    # bit
    bit = path_from([(13, 120), (78, 120), (78, 150), (58, 150), (58, 170), (78, 170), (78, 198), (13, 198)], closed=True)
    c.drawPath(bit, paint(iron, alpha))
    c.drawPath(bit, paint(hi, alpha * 0.4, stroke=2.5))
    c.restore()

# ---------------------------------------------------------------- office charisma window
def draw_window(c, seat_glow=1.0, figure=1.0, text_a=0.0):
    draw_bg(c, tint=((8, 10, 20), (20, 24, 44)))
    ox, oy, ow, oh = 250, 360, 580, 860
    outer = gothic_arch(ox, oy, ow, oh, 0.62)
    # stone surround
    c.drawPath(outer, paint((60, 56, 50), stroke=40))
    c.save(); c.clipPath(outer, doAntiAlias=True)
    # mosaic background panes
    rnd = random.Random(5)
    cols = [SAPPHIRE, SAPPHIRE, VIOLET, (34, 74, 140), EMERALD]
    step = 58
    for yy in range(int(oy - 60), int(oy + oh), step):
        for xx in range(ox, ox + ow, step):
            jit = lambda: rnd.uniform(-8, 8)
            pa = path_from([(xx + jit(), yy + jit()), (xx + step + jit(), yy + jit()),
                            (xx + step + jit(), yy + step + jit()), (xx + jit(), yy + step + jit())], closed=True)
            glass(c, pa, rnd.choice(cols), 1.0, lead=3.5, light=0.35)
    # border ruby
    c.restore()
    c.drawPath(outer, paint(RUBY, 1, stroke=18))
    c.drawPath(outer, paint(LEAD, 1, stroke=5))
    # seat (cathedra) glowing
    sx, sy = 540, 1000
    if seat_glow > 0:
        radial(c, sx, sy - 120, 360, (*GOLD_HI, 170), (*GOLD, 0), alpha=seat_glow)
    back = path_from([(sx - 90, sy), (sx - 90, sy - 220), (sx - 60, sy - 280), (sx, sy - 310), (sx + 60, sy - 280),
                      (sx + 90, sy - 220), (sx + 90, sy)], closed=True)
    glass(c, back, AMBER, 1.0, lead=5, light=0.6 * seat_glow + 0.2)
    seat = path_from([(sx - 120, sy - 10), (sx + 120, sy - 10), (sx + 120, sy + 30), (sx - 120, sy + 30)], closed=True)
    glass(c, seat, (170, 110, 40), 1.0, lead=5, light=0.4)
    for dx in (-110, 100):
        leg = path_from([(sx + dx, sy + 30), (sx + dx + 10, sy + 30), (sx + dx + 10, sy + 130), (sx + dx, sy + 130)], closed=True)
        glass(c, leg, (150, 96, 34), 1.0, lead=4, light=0.3)
    # vestment (chasuble) floating, glowing, with nobody inside
    vx, vy = 540, 640
    ch = path_from([(vx - 120, vy + 280), (vx - 150, vy + 60), (vx - 60, vy - 10), (vx, vy + 20), (vx + 60, vy - 10),
                    (vx + 150, vy + 60), (vx + 120, vy + 280)], closed=True, smooth=False)
    glass(c, ch, (196, 170, 90), 1.0, lead=5, light=0.55 * seat_glow + 0.25)
    c.drawLine(vx, vy + 30, vx, vy + 270, paint(RUBY, 1, stroke=18))
    c.drawLine(vx - 70, vy + 110, vx + 70, vy + 110, paint(RUBY, 1, stroke=18))
    # empty head: dashed outline only
    if figure > 0:
        p = paint(IVORY, 0.65 * figure, stroke=3)
        p.setPathEffect(skia.DashPathEffect.Make([10, 9], 0))
        c.drawCircle(vx, vy - 70, 52, p)
    if text_a > 0:
        draw_text(c, "character indelebilis", 540, 1300, "garamond_i", 54, GOLD_HI, text_a, align="center")
