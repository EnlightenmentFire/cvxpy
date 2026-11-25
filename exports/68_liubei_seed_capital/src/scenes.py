# -*- coding: utf-8 -*-
"""Per-scene visuals. Each scene fn(c, S) draws the main visual (no subtitles/cards/header)."""
import math, functools
import numpy as np
import skia
import gfx
from gfx import (W, H, paint, draw_text, font, ease, ease_out, ramp, fade_win, INK, WHITE, GOLD, GOLD_L, RED, RED_L,
                 BLUEGRAY, BLUE_L, OCHRE, DARK_OCHRE, PAPER, figure, horse, coin, glow_dot, big_arrow, tag, seal,
                 rrect, np_to_image, to_u8)
import geo
from geo import MapView


class Ctx:
    def __init__(self, t, dur, L, lines, gt=0.0):
        self.t, self.dur, self.L, self.lines, self.gt = t, dur, L, lines, gt

    def s(self, i):  # line start
        i = min(i, len(self.L) - 1)
        return self.L[i][0]

    def e(self, i):
        i = min(i, len(self.L) - 1)
        return self.L[i][1]

    def k(self, i, d=0.6, off=0.0):
        return ramp(self.t, self.s(i) + off, self.s(i) + off + d)

    def cur(self):
        for i, (a, b) in enumerate(self.L):
            if self.t < b + 0.2:
                return i
        return len(self.L) - 1


def draw_img(c, img, x=0, y=0, sc=1.0, a=1.0, cx=None, cy=None):
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(max(0.0, min(1.0, a)))
    c.save()
    if cx is not None:
        c.translate(cx, cy); c.scale(sc, sc); c.translate(-img.width() / 2, -img.height() / 2)
    else:
        c.translate(x, y); c.scale(sc, sc)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


# ───────────────── backgrounds (cached) ─────────────────
@functools.lru_cache(None)
def bg_dusk(seed=3, wh=2600):
    img = gfx.sky((wh, W), (16, 18, 38), (156, 84, 46), (40, 26, 22), seed=seed, clouds=0.35, cloud_col=(210, 120, 70), horizon=0.40)
    # sun glow
    yy, xx = np.mgrid[0:wh, 0:W].astype(np.float32)
    d = np.hypot(xx - 700, (yy - wh * 0.40) * 1.2)
    img += (np.exp(-d / 260) * 120)[..., None] * np.array([1.0, 0.65, 0.3])
    gfx.mountains_layer(img, seed + 1, wh * 0.40, 60, (60, 40, 46), haze_col=(150, 84, 50), haze=0.55)
    gfx.mountains_layer(img, seed + 2, wh * 0.44, 40, (38, 26, 30), haze_col=(120, 64, 40), haze=0.35)
    gfx.mountains_layer(img, seed + 3, wh * 0.47, 14, (22, 16, 18))
    img[int(wh * 0.62):] *= 0.85
    img = gfx.vignette(img, 0.35)
    img = gfx.grain(img, seed, 3)
    return np_to_image(to_u8(img))


@functools.lru_cache(None)
def bg_day(seed=5):
    img = gfx.sky((H, W), (64, 70, 82), (196, 170, 128), (92, 76, 54), seed=seed, clouds=0.3, cloud_col=(230, 214, 180), horizon=0.52)
    gfx.mountains_layer(img, seed + 1, H * 0.50, 50, (120, 110, 100), haze_col=(196, 170, 128), haze=0.6)
    gfx.mountains_layer(img, seed + 2, H * 0.55, 20, (88, 74, 56), haze_col=(170, 140, 100), haze=0.3)
    img[int(H * 0.62):] = img[int(H * 0.62):] * 0.9
    img = gfx.vignette(img, 0.45)
    img = gfx.grain(img, seed, 3)
    return np_to_image(to_u8(img))


@functools.lru_cache(None)
def bg_ink(seed=9, tone=(26, 22, 20), tone2=(52, 40, 30)):
    img = gfx.sky((H, W), tone, tone2, tone, seed=seed, clouds=0.25, cloud_col=(90, 70, 50), horizon=0.5)
    n = gfx.fbm((H // 4, W // 4), seed + 3, base=40)
    from scipy import ndimage as ndi
    n = ndi.zoom(n, 4, order=1)[:H, :W]
    img *= (0.85 + 0.3 * n)[..., None]
    img = gfx.vignette(img, 0.6)
    img = gfx.grain(img, seed, 4)
    return np_to_image(to_u8(img))


@functools.lru_cache(None)
def bg_night(seed=11):
    img = gfx.sky((H, W), (8, 10, 20), (34, 36, 52), (14, 12, 16), seed=seed, clouds=0.25, cloud_col=(60, 64, 84), horizon=0.55)
    gfx.mountains_layer(img, seed + 1, H * 0.56, 40, (24, 26, 36), haze_col=(40, 42, 60), haze=0.4)
    gfx.mountains_layer(img, seed + 2, H * 0.6, 16, (12, 12, 16))
    img = gfx.vignette(img, 0.5)
    img = gfx.grain(img, seed, 3)
    return np_to_image(to_u8(img))


@functools.lru_cache(None)
def bg_epic(seed=21):
    img = gfx.sky((H, W), (30, 16, 18), (214, 96, 40), (40, 18, 14), seed=seed, clouds=0.45, cloud_col=(250, 150, 80), horizon=0.5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - 540, (yy - H * 0.5) * 1.4)
    img += (np.exp(-d / 300) * 140)[..., None] * np.array([1.0, 0.6, 0.25])
    gfx.mountains_layer(img, seed + 1, H * 0.50, 50, (70, 34, 30), haze_col=(200, 90, 40), haze=0.6)
    gfx.mountains_layer(img, seed + 2, H * 0.555, 26, (36, 18, 16), haze_col=(150, 60, 30), haze=0.3)
    img[int(H * 0.6):] *= 0.75
    img = gfx.vignette(img, 0.4)
    img = gfx.grain(img, seed, 3)
    return np_to_image(to_u8(img))


@functools.lru_cache(None)
def tree_geo():
    return gfx.mulberry_tree(11)


def dust(c, t, x0, x1, y, n=60, seed=1, col=(200, 150, 100), a=0.5, drift=-120, size=40):
    rng = np.random.default_rng(seed)
    for i in range(n):
        px = rng.uniform(x0, x1)
        ph = rng.random()
        life = 3.0
        u = ((t / life) + ph) % 1.0
        xx = px + drift * u * life
        yy = y - u * rng.uniform(40, 160) + rng.normal(0, 14)
        r = size * (0.4 + u * 1.2)
        c.drawCircle(xx, yy, r, paint(col, a * (1 - u) * 0.6, blur=r * 0.6))


def embers(c, t, n=40, seed=2, col=(255, 180, 90), a=0.8, area=(0, 300, W, 1400)):
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        px = rng.uniform(x0, x1); ph = rng.random(); sp = rng.uniform(30, 90)
        yy = y1 - ((t * sp + ph * (y1 - y0)) % (y1 - y0))
        xx = px + math.sin(t * 0.8 + i) * 20
        r = rng.uniform(1.5, 3.5)
        c.drawCircle(xx, yy, r * 3, paint(col, a * 0.25, blur=r * 2))
        c.drawCircle(xx, yy, r, paint(col, a))


def scene_fade(c, S, fin=0.5, fout=0.5):
    a = 1 - min(ramp(S.t, 0, fin), 1 - ramp(S.t, S.dur - fout, S.dur))
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, a))


def label_chip(c, x, y, text, color, a=1.0, size=40, sub=None):
    f = font("serif_blk", size)
    w = gfx.text_w(text, f) + 40
    rrect(c, x - w / 2, y - size * 1.05, w, size * 1.5, 8, fill=(14, 12, 12), fill_a=0.75 * a, border=color, border_a=a, bw=2.5)
    draw_text(c, text, x, y, f, color, a)
    if sub:
        draw_text(c, sub, x, y + size * 1.1, font("sans_m", size * 0.6), (230, 220, 200), a, stroke=4)


# ───────────────── scenes ─────────────────
def v_open(c, S):
    t = S.t
    cam = 640 * (1 - ease(ramp(t, 0.6, 4.2)))   # tilt up
    c.save(); c.translate(0, -cam)
    draw_img(c, bg_dusk(), 0, -330)
    # ridge with caravan (world y ~ 760)
    ry = 760
    for i in range(9):
        spd = 70 * (1 - ease(ramp(t, 4.0, 6.0)))
        x = 1250 - i * 120 - t * 55 + (1 - ease(ramp(t, 4.0, 6.0))) * 0
        x = 1200 - i * 118 - min(t, 4.5) * 60 - max(0, t - 4.5) * 12
        ph = t * 1.1 + i * 0.37
        g = 0.55 if i else 0.55 * (1 - ease(ramp(t, 4.3, 5.4)))
        horse(c, x, ry + (i % 2) * 8, 0.62, phase=ph, color=(18, 12, 14), facing=-1, gallop=g, rider=(i % 3 == 0),
              rim=(255, 170, 90), rim_a=0.5, head_up=(1.0 if i == 0 and t > 4.8 else 0.0))
    dust(c, t, 100, 1200, ry + 6, n=40, seed=3, col=(220, 150, 90), a=0.45, drift=60, size=30)
    # town wall silhouette
    wall = [(0, 980), (220, 980), (220, 950), (260, 950), (260, 980), (680, 980), (680, 940), (740, 930), (800, 940), (800, 980), (W, 980), (W, 1150), (0, 1150)]
    c.drawPath(gfx.path_from(wall), paint((20, 14, 14), 0.92))
    # market ground
    c.drawRect(skia.Rect.MakeXYWH(0, 1140, W, 1400), paint((26, 18, 16)))
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1140), skia.Point(0, 1500)],
                                                [gfx.col((90, 50, 30), 0.6), gfx.col((26, 18, 16), 0.0)]))
    c.drawRect(skia.Rect.MakeXYWH(0, 1140, W, 360), g)
    # stall + boy weaving (world y ~ 1700)
    by = 1760
    c.drawRect(skia.Rect.MakeXYWH(140, by - 18, 800, 22), paint((50, 32, 22)))
    for k in range(9):  # sandals
        sx = 600 + k * 38
        c.drawOval(skia.Rect.MakeXYWH(sx, by - 34, 30, 14), paint((150, 112, 62), 0.9))
        c.drawOval(skia.Rect.MakeXYWH(sx + 4, by - 31, 22, 8), paint((90, 62, 34), 0.9))
    c.drawCircle(700, by - 120, 300, paint((255, 140, 60), 0.28 + 0.04 * math.sin(t * 7), blur=140))
    figure(c, 380, by - 18, 460, color=(14, 10, 10), pose="sit", phase=t * 1.8, rim=(255, 150, 80), rim_a=0.8, facing=1)
    # straw strands
    for k in range(14):
        a0 = k * 0.45 + math.sin(t * 2 + k) * 0.08
        c.drawLine(540, by - 120, 540 + math.cos(a0) * 140, by - 90 + math.sin(a0) * 50, paint((220, 170, 90), 0.6, stroke=2.5))
    # leader looking down marker
    c.restore()
    embers(c, t, n=24, seed=4, a=0.5)


def draw_carriage(c, x, y, s, a, col=GOLD_L):
    c.save(); c.translate(x, y); c.scale(s, s)
    pp = paint(col, a, stroke=3.2)
    gl = paint(col, a * 0.45, stroke=8, blur=6)
    # canopy dome
    dome = skia.Path(); dome.moveTo(-120, -150); dome.cubicTo(-90, -230, 90, -230, 120, -150); dome.close()
    for p_ in (gl, pp):
        c.drawPath(dome, p_)
    # feather tufts (羽葆)
    for k in range(-4, 5):
        bx = k * 28; by = -150 - (1 - (k / 4.5) ** 2) * 62
        for j in range(3):
            c.drawLine(bx, by, bx + (j - 1) * 9, by - 26, pp)
    c.drawLine(0, -150, 0, 10, pp); c.drawLine(0, -150, 0, 10, gl)
    # box
    c.drawRect(skia.Rect.MakeXYWH(-90, -40, 180, 70), pp)
    # wheel
    c.drawCircle(0, 60, 62, pp); c.drawCircle(0, 60, 62, gl)
    for k in range(12):
        th = k / 12 * math.pi * 2
        c.drawLine(0, 60, math.cos(th) * 60, 60 + math.sin(th) * 60, paint(col, a * 0.8, stroke=1.6))
    c.drawLine(90, 0, 250, -30, pp)
    c.restore()


def v_tree(c, S):
    t = S.t
    z = 1.0 + 0.06 * ease(t / max(S.dur, 1))
    c.save(); c.translate(W / 2, 1000); c.scale(z, z); c.translate(-W / 2, -1000)
    draw_img(c, bg_day(), 0, 0)
    segs, leaves = tree_geo()
    # fence (篱笆)
    for k in range(-2, 30):
        x = k * 40 - 20
        c.drawLine(x, 1290, x + 6, 1170, paint((40, 30, 22), 0.95, stroke=7))
    c.drawLine(-20, 1200, W + 20, 1190, paint((40, 30, 22), 0.95, stroke=6))
    c.drawLine(-20, 1250, W + 20, 1244, paint((40, 30, 22), 0.95, stroke=6))
    # house corner
    c.drawPath(gfx.path_from([(800, 1300), (800, 1020), (760, 1020), (900, 930), (1100, 930), (1100, 1300)]), paint((36, 28, 22)))
    a_tree = 1.0
    gfx.draw_tree(c, 470, 1300, 900, segs, leaves, color=(30, 24, 18), a=a_tree, t=t, rim=(255, 226, 160), leaf_col=(28, 34, 24))
    c.drawRect(skia.Rect.MakeXYWH(0, 1300, W, 700), paint((40, 32, 24)))
    # kids
    kids = [(300, 1340, 0.9, (26, 20, 16)), (410, 1346, 0.85, (26, 20, 16)), (560, 1344, 1.0, (20, 12, 10)), (680, 1342, 0.82, (26, 20, 16))]
    for i, (x, y, s, cc) in enumerate(kids):
        ph = t * 0.9 + i * 0.4
        figure(c, x + math.sin(ph * 2) * 10 * (i != 2), y, 175 * s, color=cc, pose="walk" if i != 2 else "stand", phase=ph,
               rim=(RED_L if i == 2 else (255, 220, 160)), rim_a=0.9 if i == 2 else 0.4, sleeve=0.8 if (i == 2 and t > S.s(2)) else 0)
    # uncle appears
    ua = S.k(3, 0.6)
    if ua > 0:
        figure(c, 760 + (1 - ua) * 60, 1340, 230, color=(16, 12, 10), a=ua, pose="stand", hat="guan", sleeve=0.6 * S.k(4, 0.3), facing=-1,
               rim=(255, 200, 150), rim_a=0.5)
    c.restore()
    # carriage ghost
    ca = fade_win(t, S.s(2) - 0.2, S.e(3) + 0.5, 0.8, 0.8)
    if ca > 0:
        draw_carriage(c, 520, 700, 1.25, ca)
        draw_text(c, "羽葆蓋車", 520, 980, font("serif_blk_tc", 54), GOLD_L, ca * S.k(3, 0.6), stroke=5, shadow=8, spacing=10)
        draw_text(c, "天子車駕", 520, 1040, font("serif_tc", 34), (235, 220, 190), ca * S.k(3, 0.6), stroke=4, spacing=6)
    # red flash on 滅吾門
    fl = fade_win(t, S.s(4), S.e(4) + 0.4, 0.15, 0.8)
    if fl > 0:
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1100, [gfx.col(RED, 0.0), gfx.col(RED, 0.55)]))
        g.setAlphaf(fl)
        c.drawRect(skia.Rect.MakeWH(W, H), g)


def v_teaser_study(c, S):
    t = S.t
    draw_img(c, bg_ink(9, (30, 24, 20), (80, 58, 36)), 0, 0)
    # road
    path = gfx.path_from([(380, 1360), (700, 1360), (580, 760), (520, 760)])
    c.drawPath(path, paint((90, 70, 46), 0.6))
    # boy walking up road
    u = ease(ramp(t, 0.2, S.dur))
    figure(c, 540 + 40 * (1 - u), 1300 - 380 * u, 220 - 120 * u, color=INK, pose="walk", phase=t * 1.4, rim=RED_L, rim_a=0.9)
    # uncle on left with coins flowing
    figure(c, 230, 1300, 260, color=(14, 12, 10), hat="guan", rim=GOLD, rim_a=0.6)
    draw_text(c, "族叔 劉元起", 230, 1380, font("serif_tc", 40), GOLD_L, ramp(t, 0.3, 0.9), stroke=4)
    bx, by = 540 + 40 * (1 - u), 1300 - 380 * u - (220 - 120 * u) * 0.6
    for i in range(16):
        ph = ((t * 0.9) + i / 16) % 1
        x = 260 + (bx - 260) * ph
        y = 1150 + (by - 1150) * ph - math.sin(ph * math.pi) * 160
        coin(c, x, y, 14, a=math.sin(ph * math.pi), spin=t * 3 + i)
    # equal bars: 德然 = 刘备
    ka = S.k(0, 0.5, 2.5)
    if ka > 0:
        for j, (nm, cc) in enumerate((("劉德然", GOLD), ("劉備", RED_L))):
            x = 760 + j * 160
            hh = 260 * ease(ramp(t, S.s(0) + 2.6, S.s(0) + 4))
            c.drawRect(skia.Rect.MakeXYWH(x - 40, 1100 - hh, 80, hh), paint(cc, 0.85 * ka))
            draw_text(c, nm, x, 1150, font("serif_tc", 36), WHITE, ka, stroke=4)
        draw_text(c, "＝", 840, 1000, font("serif_blk", 70), WHITE, ka, stroke=4)
    # 婶婶抱怨 chip
    ka2 = S.k(1, 0.4)
    if ka2 > 0:
        label_chip(c, 540, 560, "婶婶：哪能总这样？", (230, 210, 180), ka2, 44)
        label_chip(c, 540, 680, "叔叔：这孩子不是一般人", GOLD_L, S.k(1, 0.4, 2.0), 44)


def v_teaser_classmate(c, S):
    t = S.t
    draw_img(c, bg_ink(13, (18, 22, 30), (40, 50, 64)), 0, 0)
    k = ease(ramp(t, 0, 1.2))
    figure(c, 380, 1300, 300, color=INK, rim=RED_L, rim_a=0.8)
    s2 = 300 + 260 * ease(ramp(t, 1.5, 4.0))
    figure(c, 700, 1300, s2, color=(18, 22, 30), rim=BLUE_L, rim_a=0.9, hat="guan")
    draw_text(c, "公孫瓚", 700, 1390, font("serif_blk_tc", 64), BLUE_L, k, stroke=6, shadow=8, spacing=8)
    draw_text(c, "遼西人 · 劉備的師兄", 700, 1450, font("sans_m", 34), (220, 230, 240), k, stroke=4)
    ka = ramp(t, 2.5, 3.3)
    if ka > 0:
        label_chip(c, 540, 520, "十几年后：雄踞北方的军阀", BLUE_L, ka, 46)
    # cold riders silhouettes
    for i in range(6):
        horse(c, 1200 - ((t * 120 + i * 180) % 1500), 760 + (i % 2) * 20, 0.45, phase=t * 1.3 + i * 0.3,
              color=(30, 40, 56), facing=-1, gallop=1, rider=True, a=0.7 * ramp(t, 1.5, 2.5))


def herd(c, t, y0, n=24, scale=0.9, seed=5, speed=520, facing=-1, col=(14, 10, 10), rim=(255, 160, 80), x_span=2600, a=1.0, riders=0.3):
    rng = np.random.default_rng(seed)
    items = []
    for i in range(n):
        lane = rng.random()
        s = scale * (0.6 + 0.6 * lane)
        x = (rng.uniform(0, x_span) - t * speed * (0.8 + 0.4 * lane)) % x_span - 400
        if facing > 0:
            x = W - x
        y = y0 + lane * 260
        items.append((y, x, s, rng.random(), rng.random() < riders))
    items.sort()
    for y, x, s, ph, rd in items:
        horse(c, x, y, s, phase=t * 1.6 + ph, color=col, facing=facing, gallop=1.0, rider=rd, rim=rim, rim_a=0.55, a=a)


def v_teaser_horses(c, S):
    t = S.t
    draw_img(c, bg_epic(21), 0, 0)
    herd(c, t + 3, 940, n=22, scale=1.5, speed=480)
    dust(c, t, -100, 1200, 1250, n=50, seed=7, col=(230, 150, 90), a=0.55, drift=200, size=50)
    for i in range(22):
        ph = ((t * 0.7) + i / 22) % 1
        x = 900 - 600 * ph
        y = 700 + math.sin(ph * 6 + i) * 60 + i * 6
        coin(c, x, y, 16, a=min(1, ramp(t, 0.5, 1.2)) * math.sin(ph * math.pi), spin=t * 4 + i)
    ka = ramp(t, 0.8, 1.6)
    label_chip(c, 540, 520, "中山大商 · 张世平、苏双", GOLD_L, ka, 46)


SEAL_TXT = ["宗族", "名師", "同門", "商賈"]
SEAL_LAB = ["族叔 · 劉元起", "名師 · 盧植", "同學 · 公孫瓚", "馬販 · 張世平 蘇雙"]


def ledger(c, cx, cy, a, open_k, slots_a, seals_prog, labels=SEAL_LAB, big=True, notes=None, note_a=None, hi=None):
    w, h = (920, 760) if big else (600, 480)
    xs = gfx.bamboo_ledger(c, cx, cy, w, h, n=12, a=a, open_k=open_k)
    if len(xs) < 12:
        return
    cols = [xs[10], xs[7], xs[4], xs[1]]  # right-to-left reading order
    for i, x in enumerate(cols):
        sa = slots_a[i]
        if sa <= 0:
            continue
        lab = labels[i]
        f = font("serif_blk_tc", 40 if big else 28)
        gfx.draw_vtext(c, lab.replace(" · ", "").replace(" ", ""), x, cy - h / 2 + 30, f, (40, 24, 12), a * sa, lead=1.02)
        # seal slot
        sy = cy + h / 2 - (110 if big else 80)
        ss = 120 if big else 80
        dash = paint((120, 40, 30), a * sa * 0.7, stroke=2.5)
        dash.setPathEffect(skia.DashPathEffect.Make([8, 6], 0))
        c.drawRect(skia.Rect.MakeXYWH(x - ss / 2, sy - ss / 2, ss, ss), dash)
        if seals_prog[i] > 0:
            seal(c, x, sy, ss * 0.95, SEAL_TXT[i], a=a, prog=seals_prog[i])
        if hi is not None and hi == i:
            c.drawRect(skia.Rect.MakeXYWH(x - (w / 12) * 1.3, cy - h / 2 - 10, (w / 12) * 2.6, h + 20), paint(GOLD_L, a * 0.9, stroke=4, blur=0))
        if notes and note_a and note_a[i] > 0:
            draw_text(c, notes[i], x, cy + h / 2 + 70, font("sans_b", 34), WHITE, a * note_a[i], stroke=5)


def v_ledger_intro(c, S):
    t = S.t
    draw_img(c, bg_ink(9, (28, 22, 18), (70, 50, 30)), 0, 0)
    ok = ease(ramp(t, 0.1, 1.6))
    slots = [ease(ramp(t, 0.5 + i * 0.6, 1.0 + i * 0.6)) for i in range(4)]
    ledger(c, W / 2, 900, 1.0, ok, slots, [0, 0, 0, 0])
    qa = S.k(1, 0.5)
    if qa > 0:
        draw_text(c, "哪一笔真正值钱？", W / 2, 1420, font("serif_blk", 70), GOLD_L, qa, stroke=6, shadow=10, spacing=4)
    ta = S.k(2, 0.5)
    if ta > 0:
        draw_text(c, "起家资本账本", W / 2, 440, font("serif_blk", 60), WHITE, ta, stroke=5, shadow=8, spacing=14)


def map_markers(c, v, names, a=1.0, size=34, **kw):
    for n in names:
        v.label(c, n, a, size=size, **kw)


def v_hand(c, S):
    t = S.t
    # line0: map ① 幽州涿郡、中山国、洛阳
    m_a = 1 - ramp(t, S.e(0) + 0.2, S.e(0) + 1.0)
    if m_a > 0:
        v0 = MapView((114.8, 37.6), 0.64)
        v1 = MapView((115.4, 38.1), 0.80)
        v = MapView.lerp(v0, v1, ease(ramp(t, 0, S.e(0))))
        v.draw_base(c, m_a)
        geo.region(c, geo.YOU, v, BLUE_L, m_a * S.k(0, 0.8, 0.5), label="幽州", label_ll=(116.3, 40.7), size=50, t=t)
        for nm, kk, dy in (("涿郡", 0.3, -28), ("中山國", 3.0, 52), ("洛陽", 5.0, -28)):
            ka = m_a * ramp(t, kk, kk + 0.6)
            v.label(c, nm, ka, size=40, dy=dy, dot_col=RED if nm == "涿郡" else GOLD)
        x, y = v.pt("涿郡")
        glow_dot(c, x, y, 10, RED, m_a)
        # north barbarians
        nx, ny = v.pt(117.0, 41.9)
        draw_text(c, "烏桓 · 鮮卑", nx, ny, font("serif_tc", 36), (210, 200, 180), m_a * ramp(t, 1.8, 2.4), stroke=4, spacing=4)
        dashed = [v.pt(lo, la) for lo, la in ((112.5, 40.9), (115, 41.2), (117.5, 40.6), (119.6, 40.1))]
        gfx.dashed_line(c, dashed, (200, 190, 160), m_a * ramp(t, 1.8, 2.4), w=4, prog=ramp(t, 1.8, 3.5))
        geo.map_frame(c, m_a)
    if t < S.e(0) + 0.3:
        return
    a = ramp(t, S.e(0) + 0.3, S.e(0) + 1.0)
    draw_img(c, bg_ink(17, (24, 20, 18), (60, 44, 30)), 0, 0, a=a)
    draw_text(c, "劉備的起手牌", W / 2, 470, font("serif_blk", 64), GOLD_L, a, stroke=5, shadow=8, spacing=10)
    cards = [("祖父", "劉雄 · 做過縣令"), ("父親", "劉弘 · 早亡"), ("家業", "賣鞋 · 織席"), ("名號", "中山靖王之後")]
    for i, (h1, h2) in enumerate(cards):
        k = ease_out(ramp(t, S.s(1) + i * 0.5, S.s(1) + i * 0.5 + 0.6))
        if k <= 0:
            continue
        cx = 300 + (i % 2) * 480
        cy = 720 + (i // 2) * 400
        c.save(); c.translate(cx, cy); c.scale(max(0.02, abs(math.cos((1 - k) * math.pi / 2))), 1)
        rrect(c, -200, -170, 400, 340, 18, fill=(36, 28, 24), fill_a=0.95 * a, border=GOLD, border_a=0.9 * a, bw=3, shadow=20)
        rrect(c, -184, -154, 368, 308, 12, border=GOLD, border_a=0.35 * a, bw=1.5)
        draw_text(c, h1, 0, -50, font("serif_blk_tc", 64), GOLD_L, a, spacing=10)
        draw_text(c, h2, 0, 60, font("serif_tc", 38), WHITE, a)
        c.restore()
    # stamp 兌不出 on 名號 card
    ka = S.k(4, 0.3)
    if ka > 0:
        c.save(); c.translate(780, 1120); c.rotate(-12)
        s = 1.6 - 0.6 * ease_out(ka)
        c.scale(s, s)
        rrect(c, -150, -50, 300, 100, 8, border=RED, border_a=ka * 0.95, bw=6)
        draw_text(c, "兌不出", 0, 24, font("serif_blk_tc", 64), RED, ka * 0.95, spacing=10)
        c.restore()
    # 120 descendants dots on line 2
    ka = fade_win(t, S.s(3), S.e(3) + 0.3, 0.4, 0.4)
    if ka > 0:
        rrect(c, 90, 1230, 900, 190, 14, fill=INK, fill_a=0.85 * ka)
        for j in range(120):
            x = 120 + (j % 30) * 28.5
            y = 1270 + (j // 30) * 30
            c.drawCircle(x, y, 8, paint(GOLD if j else RED_L, ka * min(1, ramp(t, S.s(3) + j * 0.02, S.s(3) + j * 0.02 + 0.2))))
        draw_text(c, "子枝屬百二十餘人 · 三百餘年", W / 2, 1398, font("serif_tc", 32), WHITE, ka, stroke=3)


def coins_stack(c, x, base, n, a, color=GOLD):
    for j in range(int(n)):
        y = base - j * 14
        c.drawOval(skia.Rect.MakeXYWH(x - 60, y - 10, 120, 26), paint((120, 86, 30), a))
        c.drawOval(skia.Rect.MakeXYWH(x - 60, y - 16, 120, 26), paint(color, a))
        c.drawOval(skia.Rect.MakeXYWH(x - 12, y - 8, 24, 10), paint((120, 86, 30), a * 0.8))


def v_uncle(c, S):
    t = S.t
    draw_img(c, bg_ink(19, (30, 24, 18), (74, 54, 32)), 0, 0)
    # two stacks: 德然 / 劉備, grow over the years
    yrs = min(8, t * 1.2)
    for j, (nm, cc) in enumerate((("劉德然", GOLD), ("劉備", (240, 170, 120)))):
        x = 330 + j * 420
        coins_stack(c, x, 1180, 1 + yrs * 2.2, 1.0, cc)
        draw_text(c, nm, x, 1260, font("serif_blk_tc", 46), RED_L if j else GOLD_L, 1, stroke=4, spacing=6)
    ka = S.k(2, 0.4, 0.2)
    if ka > 0:
        draw_text(c, "常", 300, 640, font("serif_blk_tc", 170), GOLD_L, ka, stroke=6, glow=20, glow_col=GOLD)
        draw_text(c, "年年給", 300, 730, font("sans_b", 40), WHITE, ka, stroke=4)
    kb = S.k(2, 0.4, 2.2)
    if kb > 0:
        draw_text(c, "等", 780, 640, font("serif_blk_tc", 170), GOLD_L, kb, stroke=6, glow=20, glow_col=GOLD)
        draw_text(c, "和親兒子一個標準", 780, 730, font("sans_b", 40), WHITE, kb, stroke=4)
        draw_text(c, "＝", W / 2, 1080, font("serif_blk", 90), WHITE, kb, stroke=4)
    # aunt / uncle figures
    fa = S.k(3, 0.5)
    if fa > 0:
        figure(c, 150, 1500, 190, color=(16, 12, 10), a=fa, rim=(230, 200, 170), rim_a=0.5, sleeve=0.5)
        draw_text(c, "元起妻", 150, 1540, font("sans_m", 30), (230, 220, 200), fa, stroke=3)
    fb = S.k(5, 0.5)
    if fb > 0:
        figure(c, 930, 1500, 220, color=(16, 12, 10), a=fb, hat="guan", rim=GOLD, rim_a=0.6, facing=-1)
        draw_text(c, "劉元起", 930, 1540, font("sans_m", 30), GOLD_L, fb, stroke=3)


# ── analogy panel scenes ──
ANALOG = {
    "analog_uncle": dict(
        an="乡镇大老板，把没了父亲的族侄\n和亲儿子一起送出去留学，生活费一样多",
        icon="shops",
        bias=["不是随手掏一笔学费：常年的食宿、衣服、书简、交游", "卢植就在涿郡本地讲学：钱主要不是路费", "伤筋不动骨：婶婶抱怨，没闹大，家里拿得出"],
        bias_line=[3, 3, 4], an_line=1),
    "analog_lu": dict(
        an="名教授挂名的高级研修班\n大班授课，结业可写「师从某某」", icon="cert",
        bias=["≠ 院士亲自带研究生", "非嫡传弟子，史书无任何学问记载"], bias_line=[1, 2], an_line=0),
    "analog_gsz": dict(
        an="研修班里的大师兄成了一方诸侯\n落难投奔，让你去一座中等城市当一把手", icon="city",
        bias=["汉代郡国长官：民政＋兵＋刑狱，权力更集中", "不是同学情白送：「以拒冀州牧袁紹」"], bias_line=[2, 3], an_line=0),
    "analog_horse": dict(
        an="跑边贸的大商人，看中本地青年领袖\n直接出资，让他拉起一支队伍", icon="caravan",
        bias=["不是商业投资：是乱世里的保护与押注", "马和武装本身就是暴力资源", "史书没写回报条件：不编「对赌协议」"], bias_line=[2, 3, 3], an_line=0),
}


def draw_icon(c, kind, cx, cy, a, t):
    if kind == "shops":
        for i in range(4):
            x = cx - 270 + i * 180
            c.drawPath(gfx.path_from([(x - 70, cy + 70), (x - 70, cy - 20), (x - 85, cy - 20), (x, cy - 80), (x + 85, cy - 20), (x + 70, cy - 20), (x + 70, cy + 70)]),
                       paint(GOLD, a * 0.9, stroke=3))
            c.drawRect(skia.Rect.MakeXYWH(x - 25, cy + 10, 50, 60), paint(GOLD, a * 0.6, stroke=2.5))
        for i in range(6):
            ph = ((t * 0.5) + i / 6) % 1
            coin(c, cx - 300 + 600 * ph, cy - 140 - math.sin(ph * math.pi) * 60, 12, a * math.sin(ph * math.pi), spin=t * 3 + i)
    elif kind == "cert":
        rrect(c, cx - 230, cy - 120, 460, 240, 10, fill=PAPER, fill_a=0.9 * a, border=GOLD, border_a=a, bw=4)
        draw_text(c, "结业证书", cx, cy - 50, font("serif_blk", 44), (60, 40, 24), a, spacing=8)
        draw_text(c, "师从　卢植", cx, cy + 30, font("serif_sc", 40), (90, 50, 30), a, spacing=4)
        seal(c, cx + 170, cy + 80, 60, "盧植", a=a, prog=1)
    elif kind == "city":
        for i in range(9):
            x = cx - 320 + i * 80; hh = 60 + (i * 37 % 5) * 30
            c.drawRect(skia.Rect.MakeXYWH(x, cy + 80 - hh, 60, hh), paint(BLUE_L, a * 0.75, stroke=3))
        c.drawLine(cx - 360, cy + 80, cx + 360, cy + 80, paint(BLUE_L, a, stroke=3))
        glow_dot(c, cx, cy - 100, 12, RED, a)
    elif kind == "caravan":
        c.save(); c.clipRect(skia.Rect.MakeXYWH(cx - 380, cy - 160, 760, 280))
        for i in range(5):
            horse(c, cx + 400 - ((t * 90 + i * 170) % 900), cy + 90, 0.55, phase=t + i * 0.3, color=GOLD, facing=-1, gallop=0.35, a=a * 0.8, rider=(i == 0))
        c.restore()


def v_analog(c, S, key):
    t = S.t
    cfg = ANALOG[key]
    draw_img(c, bg_ink(23, (22, 20, 22), (44, 40, 44)), 0, 0)
    a1 = ramp(t, 0.1, 0.6)
    # analogy block
    tag(c, 70, 330, "现代类比", GOLD, a1, size=38)
    rrect(c, 60, 410, 960, 560, 16, fill=(30, 26, 22), fill_a=0.85 * a1, border=GOLD, border_a=0.6 * a1, bw=2, shadow=20)
    draw_icon(c, cfg["icon"], W / 2, 600, a1, t)
    for j, ln in enumerate(cfg["an"].split("\n")):
        draw_text(c, ln, W / 2, 850 + j * 62, font("serif_sc", 44), WHITE, a1, stroke=3)
    # bias block
    b0 = min(cfg["bias_line"])
    a2 = S.k(b0, 0.5, -0.2)
    if a2 > 0:
        tag(c, 70, 1010, "类比偏差", (236, 110, 80), a2, size=38)
        y = 1110
        for j, (txt, li) in enumerate(zip(cfg["bias"], cfg["bias_line"])):
            kk = S.k(li, 0.5, 0.0 + 0.6 * (j - cfg["bias_line"].index(li)))
            if kk <= 0:
                continue
            f = font("sans_b", 40)
            lines = gfx.wrap(txt, f, 860)
            c.drawCircle(96, y - 13, 9, paint((236, 110, 80), kk))
            for ln in lines:
                draw_text(c, ln, 125, y, f, (240, 232, 220), kk, align="l", stroke=3)
                y += 58
            y += 22


def v_analog_uncle(c, S): v_analog(c, S, "analog_uncle")
def v_analog_lu(c, S): v_analog(c, S, "analog_lu")
def v_analog_gsz(c, S): v_analog(c, S, "analog_gsz")
def v_analog_horse(c, S): v_analog(c, S, "analog_horse")


def seal_moment(c, S, i, li, label, st=None):
    """stamp seal i near end of line li"""
    st = S.e(li) - 1.6 if st is None else st
    p = ramp(S.t, st, st + 0.45)
    if p > 0:
        a = 1.0
        rrect(c, W / 2 - 330, 1020, 660, 330, 18, fill=(236, 224, 196), fill_a=0.95 * ramp(S.t, st - 0.4, st), border=GOLD, border_a=ramp(S.t, st - 0.4, st), bw=3, shadow=24)
        seal(c, W / 2 - 160, 1185, 200, SEAL_TXT[i], a=a, prog=p)
        draw_text(c, ["第一笔", "第二笔", "第三笔", "第四笔"][i], W / 2 + 120, 1150, font("serif_blk", 52), (60, 36, 20), ramp(S.t, st + 0.3, st + 0.7), spacing=6)
        draw_text(c, label, W / 2 + 120, 1230, font("serif_sc", 40), (120, 40, 30), ramp(S.t, st + 0.4, st + 0.8))


def v_mech_clan(c, S):
    t = S.t
    draw_img(c, bg_ink(29, (26, 20, 18), (62, 44, 30)), 0, 0)
    cx, cy = W / 2, 760
    draw_text(c, "宗族网络", cx, 420, font("serif_blk", 60), GOLD_L, ramp(t, 0.2, 0.8), stroke=5, spacing=12)
    nodes = [("元起", 0), ("子敬", 1), ("德然", 2), ("族人", 3), ("族人", 4), ("族人", 5), ("族人", 6), ("族人", 7)]
    k = ease(ramp(t, 0.3, 1.5))
    pts = []
    for nm, i in nodes:
        th = i / len(nodes) * 2 * math.pi - math.pi / 2
        x, y = cx + math.cos(th) * 330 * k, cy + math.sin(th) * 260 * k
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        for j in range(i + 1, len(pts)):
            if (j - i) in (1, 3):
                c.drawLine(x, y, *pts[j], paint(GOLD, 0.25 * k, stroke=2))
        c.drawLine(x, y, cx, cy, paint(GOLD, 0.35 * k, stroke=2.5))
    for i, (nm, _) in enumerate(nodes):
        x, y = pts[i]
        hi = i == 0
        c.drawCircle(x, y, 46 if hi else 36, paint((40, 30, 22), k))
        c.drawCircle(x, y, 46 if hi else 36, paint(GOLD_L if hi else GOLD, k, stroke=3))
        draw_text(c, nm, x, y + 13, font("serif_tc", 34 if hi else 28), GOLD_L if hi else (220, 200, 170), k)
    # credit flow particles
    fl = S.k(1, 1.0)
    for i in range(len(pts)):
        for j in range(3):
            ph = ((t * 0.6) + j / 3 + i * 0.13) % 1
            x = pts[i][0] + (cx - pts[i][0]) * ph
            y = pts[i][1] + (cy - pts[i][1]) * ph
            c.drawCircle(x, y, 7, paint(GOLD_L, fl * math.sin(ph * math.pi), blur=2))
    glow_dot(c, cx, cy, 26, RED, k)
    draw_text(c, "劉備", cx, cy + 82, font("serif_blk_tc", 44), RED_L, k, stroke=5)
    ka = S.k(1, 0.5, 1.0)
    if ka > 0:
        for j, s_ in enumerate(("没有银行", "没有助学贷款")):
            label_chip(c, 300 + j * 480, 1160, s_, (220, 200, 170), ka, 40)
    seal_moment(c, S, 0, 2, "宗族信用")


def v_luzhi(c, S):
    t = S.t
    draw_img(c, bg_night(11), 0, 0)
    # hall
    c.drawRect(skia.Rect.MakeXYWH(140, 600, 800, 640), paint((28, 22, 22), 0.95))
    c.drawPath(gfx.path_from([(60, 640), (540, 430), (1020, 640)]), paint((20, 16, 16)))
    for k in range(5):
        c.drawRect(skia.Rect.MakeXYWH(190 + k * 175, 660, 26, 580), paint((14, 10, 10)))
    # lamp light
    c.drawCircle(540, 900, 260, paint((255, 170, 80), 0.25 + 0.03 * math.sin(t * 5), blur=120))
    # 卢植 back view, tall
    figure(c, 540, 1180, 360, color=(10, 8, 8), hat="guan", rim=(255, 190, 110), rim_a=0.8, sleeve=0.2)
    c.drawRect(skia.Rect.MakeXYWH(0, 1235, W, 700), paint((18, 14, 14)))
    draw_text(c, "盧植", 540, 1330, font("serif_blk_tc", 70), GOLD_L, ramp(t, 0.5, 1.2), stroke=6, shadow=10, spacing=20)
    # CV chips
    cv = [("涿郡涿人", 2), ("与郑玄同师马融", 2), ("熹平四年 · 九江太守", 3), ("因病去职", 3)]
    for j, (s_, li) in enumerate(cv):
        kk = S.k(li, 0.5, (j % 2) * 1.4)
        if kk > 0:
            draw_text(c, s_, 540, 420 + j * 64, font("serif_sc", 42), (240, 225, 200), kk * (1 - S.k(4, 0.5)), stroke=4, shadow=6)


def v_lecture(c, S):
    t = S.t
    draw_img(c, bg_ink(31, (30, 24, 20), (70, 52, 34)), 0, 0)
    z = 1.0 + 0.08 * ease(ramp(t, 0, S.dur))
    liu_xy = (W / 2, 1400)
    c.save(); c.translate(W / 2, 900); c.scale(z, z); c.translate(-W / 2, -900)
    # floor perspective
    c.drawPath(gfx.path_from([(0, 1500), (W, 1500), (720, 700), (360, 700)]), paint((52, 38, 26), 0.9))
    for k in range(6):
        c.drawLine(360 - k * 70, 700 + k * 160, 720 + k * 70, 700 + k * 160, paint((70, 52, 34), 0.5, stroke=2))
    # window right with horses outside
    wx, wy, ww, wh = 830, 560, 220, 300
    c.save(); c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), paint((210, 170, 110)))
    for i in range(3):
        horse(c, wx + ww + 80 - ((t * 60 + i * 140) % 420), wy + 250, 0.5, phase=t + i * 0.4, color=(60, 40, 26), facing=-1, gallop=0.4)
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), paint((30, 22, 16), stroke=10))
    c.drawLine(wx + ww / 2, wy, wx + ww / 2, wy + wh, paint((30, 22, 16), stroke=6))
    # teacher distant
    figure(c, 540, 740, 110, color=(14, 10, 10), hat="guan", rim=(255, 190, 110), rim_a=0.6)
    # rows of students (backs)
    for r in range(5):
        y = 820 + r * 140
        n = 5 + r // 2
        s = 70 + r * 24
        for k in range(n):
            x = W / 2 + (k - (n - 1) / 2) * (100 + r * 16)
            liu = (r == 4 and k == n - 1)
            if liu:
                liu_xy = (x, y)
            figure(c, x, y, s, color=(16, 12, 10), pose="sit", rim=(RED_L if liu else (255, 200, 140)), rim_a=0.9 if liu else 0.35,
                   facing=1 if liu else -1, phase=0)
    c.restore()
    ka = S.k(2, 0.5)
    if ka > 0:
        lx, ly = liu_xy
        lx = W / 2 + (lx - W / 2) * z; ly = 900 + (ly - 900) * z
        c.drawCircle(lx, ly - 80 * z, 110, paint(RED_L, ka * 0.9, stroke=5))
        draw_text(c, "刘备在这儿", lx - 40, ly - 220 * z, font("sans_b", 40), RED_L, ka, stroke=5)


def v_mech_name(c, S):
    t = S.t
    draw_img(c, bg_ink(37, (24, 22, 26), (50, 44, 48)), 0, 0)
    draw_text(c, "汉代选官 · 察举", W / 2, 420, font("serif_blk", 58), GOLD_L, S.k(1, 0.5), stroke=5, spacing=8)
    ins = ["名声", "门第", "师承"]
    for j, s_ in enumerate(ins):
        kk = S.k(1, 0.4, 0.5 + j * 0.4)
        x = 220 + j * 320
        rrect(c, x - 120, 520, 240, 110, 12, fill=(40, 34, 30), fill_a=0.9 * kk, border=RED_L if j == 2 else GOLD, border_a=kk, bw=3 if j == 2 else 2)
        draw_text(c, s_, x, 595, font("serif_blk", 52), RED_L if j == 2 else WHITE, kk, spacing=8)
        if kk > 0:
            big_arrow(c, [(x, 640), (W / 2, 790)], ease(kk), 22, GOLD, kk * 0.8, glow=False)
    kk = S.k(1, 0.4, 2.0)
    rrect(c, W / 2 - 260, 800, 520, 120, 14, fill=(50, 40, 30), fill_a=0.9 * kk, border=GOLD_L, border_a=kk)
    draw_text(c, "举荐 · 孝廉 / 茂才", W / 2, 880, font("serif_blk", 46), GOLD_L, kk)
    big_arrow(c, [(W / 2, 930), (W / 2, 1040)], ease(S.k(1, 0.5, 2.5)), 26, GOLD, kk * 0.9, glow=False)
    draw_text(c, "官", W / 2, 1140, font("serif_blk", 90), WHITE, S.k(1, 0.5, 2.8), stroke=5, glow=14, glow_col=GOLD)
    kc = S.k(2, 0.5)
    if kc > 0:
        label_chip(c, 220, 720 - 40, "师从卢植", RED_L, kc, 38)
        # meter
        draw_text(c, "入场券 · 最低一档", W / 2, 1290, font("sans_b", 44), (240, 220, 200), kc, stroke=4)
    kd = S.k(4, 0.5)
    if kd > 0:
        figure(c, 360, 1480, 160, color=INK, rim=RED_L, rim_a=0.9)
        figure(c, 640, 1480, 180, color=(18, 22, 30), rim=BLUE_L, rim_a=0.9 * kd, a=kd, hat="guan")
        draw_text(c, "？", 640, 1250, font("serif_blk", 80), BLUE_L, kd, stroke=4)
    if S.t > S.e(4) - 1.8:
        seal_moment(c, S, 1, 4, "名师背书")


def v_gsz(c, S):
    t = S.t
    draw_img(c, bg_ink(41, (18, 22, 30), (40, 50, 66)), 0, 0)
    a0 = 1 - S.k(5, 0.6)
    af = a0 * (1 - S.k(4, 0.5))
    if a0 > 0:
        # two figures bowing
        figure(c, 360, 1200, 330, color=INK, rim=RED_L, rim_a=0.9, a=af, sleeve=0.4 * S.k(1, 0.5))
        figure(c, 720, 1200, 360, color=(16, 20, 28), rim=BLUE_L, rim_a=0.9, a=af, hat="guan", facing=-1)
        draw_text(c, "劉備", 360, 1280, font("serif_blk_tc", 46), RED_L, af, stroke=4)
        draw_text(c, "公孫瓚 · 年長", 720, 1280, font("serif_blk_tc", 46), BLUE_L, af, stroke=4)
        kk = S.k(1, 0.5, 1.5)
        draw_text(c, "以兄事之", W / 2, 640, font("serif_blk_tc", 80), GOLD_L, kk * a0 * (1 - S.k(3, 0.4)), stroke=5, spacing=14, glow=12, glow_col=GOLD)
        # backers comparison
        kb = S.k(4, 0.5)
        if kb > 0:
            for j, (nm, sub, hgt, cc) in enumerate((("公孫瓚背後", "太守岳父", 420, BLUE_L), ("劉備背後", "一個族叔", 150, RED_L))):
                x = 360 + j * 360
                hh = hgt * ease(kb)
                c.drawRect(skia.Rect.MakeXYWH(x - 70, 1180 - hh, 140, hh), paint(cc, 0.85 * kb * a0))
                draw_text(c, nm, x, 1240, font("serif_tc", 40), WHITE, kb * a0, stroke=4)
                draw_text(c, sub, x, 1150 - hh, font("serif_blk", 50), cc, kb * a0, stroke=4)
    k5 = S.k(5, 0.6)
    if k5 > 0:
        # cavalry clash: few blue riders vs many
        c.save()
        for i in range(30):
            x = 1150 - ((t * 140 + i * 47) % 900)
            horse(c, x + (i % 5) * 20, 960 + (i % 6) * 50, 0.6, phase=t * 1.4 + i * 0.3, color=(60, 50, 40), facing=-1, gallop=1, rider=True, a=k5 * 0.8)
        for i in range(5):
            horse(c, -150 + ((t * 220 + i * 70) % 1400), 1200 + i * 34, 1.0, phase=t * 1.8 + i * 0.4, color=(16, 20, 28), facing=1, gallop=1, rider=True, rim=BLUE_L, rim_a=0.9, a=k5)
        c.restore()
        draw_text(c, "數十騎 vs 數百鮮卑騎", W / 2, 640, font("serif_blk_tc", 56), BLUE_L, k5, stroke=5, shadow=8)
        draw_text(c, "→ 一路升到中郎將", W / 2, 720, font("serif_tc", 44), WHITE, S.k(5, 0.5, 2.5), stroke=4)


def v_map_pingyuan(c, S):
    t = S.t
    v0 = MapView((116.0, 37.3), 0.66)
    v1 = MapView((116.2, 38.0), 0.85)
    v = MapView.lerp(v0, v1, ease(ramp(t, S.s(3), S.e(5))))
    v.draw_base(c)
    geo.map_frame(c)
    # 履历 route (line 1)
    k1 = S.k(1, 3.0)
    if k1 > 0:
        route = [v.pt("涿縣"), v.pt(117.0, 37.0), v.pt("下邳"), v.pt("下密"), v.pt("高唐")]
        gfx.dashed_line(c, route, RED_L, 0.9, w=6, on=20, off=10, prog=k1, phase=-t * 30)
        for nm, kk in (("下邳", 0.4), ("下密", 0.7), ("高唐", 0.9)):
            if k1 > kk:
                v.label(c, nm, 1, size=34, dot_col=RED)
    v.label(c, "涿縣", 1, size=34, dot_col=RED)
    # 孤证 line 2
    k2 = fade_win(t, S.s(2), S.e(2) + 0.8, 0.5, 0.8)
    if k2 > 0:
        gfx.dashed_line(c, [v.pt("洛陽"), v.pt(115.0, 35.2), v.pt("沛")], (230, 220, 200), k2, w=4, on=8, off=12, prog=S.k(2, 2.0))
        v.label(c, "洛陽", k2, size=34)
        v.label(c, "沛", k2, size=34)
        tag(c, 70, 1180, "孤证 · 裴注引《英雄记》", (210, 200, 180), k2, size=34)
    # line 3+: regions
    k3 = S.k(3, 0.8)
    if k3 > 0:
        geo.region(c, geo.YOU, v, BLUE_L, k3, label="公孫瓚", label_ll=(116.8, 40.3), size=48, t=t)
        geo.region(c, geo.JI, v, DARK_OCHRE, S.k(4, 0.8), label="袁紹", label_ll=(114.9, 37.3), size=48, t=t)
        geo.region(c, geo.QING, v, BLUE_L, S.k(4, 0.8, 1.5) * 0.8, label="田楷", label_ll=(118.6, 36.8), size=40, t=t)
        big_arrow(c, [v.pt(116.5, 39.8), v.pt(117.2, 38.6), v.pt(116.6, 37.4)], ease(S.k(4, 1.6, 0.3)), 34, BLUE_L, 0.9, t=t, dash_flow=60)
        v.label(c, "鄴", S.k(4, 0.5), size=32, dot_col=DARK_OCHRE)
    k5 = S.k(5, 0.6)
    if k5 > 0:
        x, y = v.pt("平原")
        pulse = 1 + 0.3 * math.sin(t * 5)
        glow_dot(c, x, y, 14 * pulse, RED, k5)
        v.label(c, "平原", k5, size=44, dy=-34, color=RED_L, dot=False)
        draw_text(c, "釘子", x + 120, y + 70, font("serif_blk_tc", 40), RED_L, k5, stroke=5)
    k6 = S.k(6, 0.5)
    if k6 > 0:
        rrect(c, 60, 1110, 960, 230, 16, fill=INK, fill_a=0.75 * k6, border=GOLD, border_a=0.6 * k6)
        draw_text(c, "别部司马：能单独带一支人马的军官", 90, 1195, font("sans_b", 40), WHITE, k6, align="l")
        draw_text(c, "平原相：一个郡国的长官，秩二千石", 90, 1285, font("sans_b", 40), GOLD_L, S.k(6, 0.5, 2.5), align="l")


def v_mech_option(c, S):
    t = S.t
    draw_img(c, bg_ink(43, (20, 22, 28), (44, 48, 60)), 0, 0)
    draw_text(c, "同学关系 ＝ 一张期权", W / 2, 440, font("serif_blk", 60), GOLD_L, ramp(t, 0.2, 0.8), stroke=5, spacing=6)
    x0, x1, yb = 140, 960, 1180
    c.drawLine(x0, yb, x1, yb, paint(WHITE, 0.7, stroke=3))
    c.drawLine(x0, yb, x0, 600, paint(WHITE, 0.7, stroke=3))
    draw_text(c, "价值", x0 + 10, 590, font("sans_m", 32), WHITE, 0.8, align="l")
    draw_text(c, "年份", x1, yb + 50, font("sans_m", 32), WHITE, 0.8, align="r")
    for yr, xx in (("同窗", x0 + 60), ("黄巾", x0 + 330), ("投奔", x0 + 700)):
        draw_text(c, yr, xx, yb + 50, font("sans_m", 32), (220, 210, 190), 0.9)
    k = ease(ramp(t, 0.5, S.e(0)))
    pts = [(x0, yb - 10), (x0 + 400, yb - 14), (x0 + 660, yb - 20), (x0 + 700, yb - 400), (x1, yb - 430)]
    S_ = gfx.sample_curve(pts, 200)
    n = int(len(S_) * k)
    if n > 2:
        p = gfx.path_from(S_[:n], close=False)
        c.drawPath(p, paint(GOLD, 0.5, stroke=14, blur=8))
        c.drawPath(p, paint(GOLD_L, 1, stroke=6))
    if k > 0.85:
        glow_dot(c, x0 + 700, yb - 400, 14, RED, ramp(t, S.e(0) - 0.5, S.e(0)))
        draw_text(c, "平原相", x0 + 700, yb - 450, font("serif_blk", 44), RED_L, ramp(t, S.e(0) - 0.5, S.e(0)), stroke=4)
    kb = S.k(1, 0.5)
    if kb > 0 and t < S.e(1) - 1.7:
        label_chip(c, W / 2, 1360, "兑现前提：你对他也有用", (236, 140, 100), kb, 44)
    seal_moment(c, S, 2, 1, "同门期权")


def v_youxia(c, S):
    t = S.t
    draw_img(c, bg_dusk(7), 0, -560)
    c.drawRect(skia.Rect.MakeXYWH(0, 1350, W, 600), paint((24, 16, 14)))
    figure(c, 540, 1360, 300, color=(12, 8, 8), rim=RED_L, rim_a=0.95)
    n = int(2 + 14 * ease(ramp(t, S.s(2), S.e(2))))
    rng = np.random.default_rng(3)
    for i in range(16):
        if i >= n:
            break
        side = -1 if i % 2 else 1
        x = 540 + side * (130 + (i // 2) * 52) + rng.normal(0, 8)
        y = 1370 + (i // 2) * 6
        figure(c, x, y, 190 - (i // 2) * 6, color=(18, 12, 12), rim=(255, 170, 110), rim_a=0.5, facing=-side, a=min(1, ramp(t, S.s(2) + i * 0.15, S.s(2) + i * 0.15 + 0.4)))
    ka = S.k(2, 0.5, 1.0)
    if ka > 0:
        draw_text(c, "年少争附之", W / 2, 560, font("serif_blk_tc", 70), GOLD_L, ka * (1 - S.k(3, 0.4)), stroke=5, spacing=12, glow=12, glow_col=GOLD)
    # inset map: 河東解縣 → 涿郡
    km = fade_win(t, S.s(3), S.e(3) + 0.3, 0.5, 0.5)
    if km > 0:
        rrect(c, 140, 380, 800, 520, 16, fill=INK, fill_a=0.8 * km, border=GOLD, border_a=km)
        v = MapView((113.4, 37.2), 0.30, cy=640)
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(140, 380, 800, 520), 16, 16), doAntiAlias=True)
        v.draw_base(c, km)
        big_arrow(c, [v.pt("解縣"), v.pt(113.5, 37.6), v.pt("涿郡")], ease(S.k(3, 2.0, 0.4)), 26, (220, 200, 170), km, t=t)
        v.label(c, "解縣", km, size=32, disp="河東解縣")
        v.label(c, "涿郡", km, size=32, dot_col=RED)
        c.restore()
        draw_text(c, "關羽 · 亡命奔涿郡", 540, 860, font("serif_blk_tc", 40), GOLD_L, km, stroke=4)
    kg = S.k(4, 0.6)
    if kg > 0:
        figure(c, 260, 1400, 420, color=(10, 8, 8), rim=(255, 120, 90), rim_a=0.9, a=kg, sleeve=0.2)
        figure(c, 820, 1400, 410, color=(10, 8, 8), rim=(255, 140, 90), rim_a=0.9, a=kg, facing=-1)
        draw_text(c, "關羽", 260, 1480, font("serif_blk_tc", 50), GOLD_L, kg, stroke=5)
        draw_text(c, "張飛", 820, 1480, font("serif_blk_tc", 50), GOLD_L, kg, stroke=5)
        draw_text(c, "為之禦侮", W / 2, 560, font("serif_blk_tc", 70), GOLD_L, kg, stroke=5, spacing=12, glow=12, glow_col=GOLD)


def v_horses(c, S):
    t = S.t
    shake = (math.sin(t * 37) * 3 + math.sin(t * 23) * 2) * ramp(t, S.s(1), S.s(1) + 0.5) * (1 - ramp(t, S.e(2), S.e(2) + 1))
    c.save(); c.translate(shake, shake * 0.6)
    draw_img(c, bg_epic(21), 0, 0)
    # herd thunders in during quote
    ha = ramp(t, 0.2, 1.4)
    herd(c, t, 860, n=30, scale=1.6, speed=600, a=ha, seed=9)
    dust(c, t, -200, 1300, 1260, n=80, seed=7, col=(230, 150, 90), a=0.6 * ha, drift=260, size=60)
    # banner on left grows
    kb = ease(ramp(t, S.s(2), S.e(4)))
    bx, by = 190, 1380
    pole = 200 + 520 * kb
    c.drawLine(bx, by, bx, by - pole, paint(INK, 1, stroke=10))
    flag = skia.Path()
    fw, fh = 140 + 140 * kb, 100 + 90 * kb
    flag.moveTo(bx, by - pole)
    for k in range(13):
        u = k / 12
        flag.lineTo(bx + fw * u, by - pole + math.sin(t * 5 + u * 6) * 12 * u)
    for k in range(12, -1, -1):
        u = k / 12
        flag.lineTo(bx + fw * u, by - pole + fh + math.sin(t * 5 + u * 6) * 12 * u)
    flag.close()
    c.drawPath(flag, paint(RED, 0.5, blur=20))
    c.drawPath(flag, paint(RED, 0.95))
    draw_text(c, "劉", bx + fw * 0.45, by - pole + fh * 0.72, font("serif_blk_tc", fh * 0.62), (250, 232, 200), 0.95)
    # coins stream into banner
    kc = fade_win(t, S.s(2) - 0.5, S.e(4), 0.6, 1.0)
    for i in range(40):
        ph = ((t * 0.55) + i / 40) % 1
        x = 1050 - (1050 - bx - fw / 2) * ph
        y = 620 + i % 7 * 30 + (by - pole + fh / 2 - 650) * ph + math.sin(ph * 8 + i) * 30
        coin(c, x, y, 15, a=kc * math.sin(ph * math.pi), spin=t * 5 + i)
    # formation of troops
    kf = ramp(t, S.s(4), S.e(4))
    if kf > 0:
        for r in range(4):
            for k in range(14):
                idx = r * 14 + k
                if idx / 56 > kf:
                    continue
                x = 330 + k * 52 + r * 14
                y = 1390 + r * 46
                figure(c, x, y, 86, color=(14, 8, 8), rim=RED_L, rim_a=0.5)
                c.drawLine(x + 10, y - 90, x + 16, y - 150, paint(INK, 1, stroke=3))
    c.restore()
    embers(c, t, n=40, seed=8, a=0.7)
    km = fade_win(t, S.s(1) - 0.3, S.e(2) + 0.3, 0.5, 0.5)
    if km > 0:
        bx0, by0, bw, bh = 150, 250, 780, 420
        rrect(c, bx0, by0, bw, bh, 14, fill=INK, fill_a=0.85 * km, border=GOLD, border_a=km, shadow=20)
        v = MapView((115.6, 39.0), 0.55, cy=by0 + bh / 2)
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx0, by0, bw, bh), 14, 14), doAntiAlias=True)
        v.draw_base(c, km)
        pts = [v.pt("中山國"), v.pt(115.3, 39.0), v.pt("涿郡")]
        gfx.dashed_line(c, pts, GOLD_L, km, w=5, on=1000, off=1, prog=ease(ramp(t, S.s(1), S.s(1) + 3.0)))
        q = gfx.sample_curve(pts, 60)[int(59 * ease(ramp(t, S.s(1), S.s(1) + 3.0)))]
        glow_dot(c, q[0], q[1], 8, GOLD, km)
        v.label(c, "中山國", km, size=32, dy=44)
        v.label(c, "涿郡", km, size=32, dot_col=RED)
        c.restore()
        draw_text(c, "販馬周旋於涿郡", W / 2, by0 + bh - 24, font("serif_blk_tc", 34), GOLD_L, km, stroke=4)
    ka = S.k(4, 0.4)
    if ka > 0:
        draw_text(c, "钱 → 刀 · 马 · 弟兄", W / 2, 520, font("serif_blk", 64), GOLD_L, ka, stroke=6, shadow=10, glow=14, glow_col=GOLD)


def v_mech_army(c, S):
    t = S.t
    draw_img(c, bg_ink(47, (30, 18, 16), (70, 34, 26)), 0, 0)
    a0 = 1 - S.k(1, 0.5)
    if a0 > 0:
        items = [("豪侠号召力", (240, 210, 170)), ("商人资本", GOLD_L), ("私人武装", RED_L)]
        for j, (s_, cc) in enumerate(items):
            kk = ease_out(ramp(t, 0.3 + j * 1.1, 0.9 + j * 1.1))
            y = 560 + j * 300
            rrect(c, W / 2 - 300, y - 90, 600, 160, 16, fill=(40, 26, 22), fill_a=0.92 * kk * a0, border=cc, border_a=kk * a0, bw=3, shadow=20)
            draw_text(c, s_, W / 2, y + 18, font("serif_blk", 64), cc, kk * a0, spacing=8)
            if j < 2:
                draw_text(c, "＋" if j == 0 else "＝", W / 2, y + 170, font("serif_blk", 70), WHITE, ramp(t, 0.9 + j * 1.1, 1.3 + j * 1.1) * a0)
    k1 = S.k(1, 0.5)
    if k1 > 0 and t < S.e(2) - 1.6:
        tag(c, 80, 420, "演义说", (200, 190, 170), k1, size=40)
        draw_text(c, "桃园三结义，焚香结拜", 80, 560, font("serif_sc", 50), (220, 210, 190), k1, align="l", stroke=3)
        c.drawLine(80, 540, 80 + 500 * ease(S.k(1, 0.6, 2.0)), 540, paint((236, 110, 80), k1, stroke=5))
        tag(c, 80, 640, "史书说", GOLD, S.k(1, 0.5, 2.6), size=40)
        draw_text(c, "只有一句：寢則同床，恩若兄弟", 80, 780, font("serif_tc", 50), GOLD_L, S.k(1, 0.5, 2.6), align="l", stroke=3)
    seal_moment(c, S, 3, 2, "商人资本", st=S.e(2) + 0.45)


def v_map_yellow(c, S):
    t = S.t
    v0 = MapView((115.3, 37.5), 0.68)
    v1 = MapView((115.2, 38.3), 1.0)
    zoom_k = ease(ramp(t, S.s(4) + 0.5, S.e(4)))
    v = MapView.lerp(v0, v1, zoom_k)
    v.draw_base(c)
    geo.map_frame(c)
    geo.region(c, geo.JI, v, (200, 190, 170), 0.5, label=None, t=t)
    x, y = v.pt(114.3, 38.9)
    draw_text(c, "冀州", x, y, font("serif_blk_tc", 46), (220, 210, 190), 0.6 * (1 - S.k(4, 0.3, 0.6)), stroke=5, spacing=8)
    shrink = 1 - 0.6 * ease(ramp(t, S.s(3), S.e(4)))
    ka = ramp(t, 0.3, 1.5)
    blobs = [((115.1, 37.15), 120, 1), ((114.6, 37.7), 70, 2), ((116.2, 37.8), 60, 3), ((114.4, 36.6), 60, 4), ((116.8, 36.5), 55, 5), ((113.9, 35.4), 55, 6)]
    for (ll, r, sd) in blobs:
        bx, by = v.pt(*ll)
        gfx.blob(c, bx, by, r * shrink * v.s / 0.55, OCHRE, ka * 0.85, t, seed=sd)
    v.label(c, "鉅鹿", ka, size=34, dy=-30, dot_col=OCHRE)
    v.label(c, "廣宗", ka, size=34, dy=50, dot_col=OCHRE)
    draw_text(c, "黃巾", *v.pt(115.9, 37.0), font("serif_blk_tc", 56), OCHRE, ka, stroke=6, shadow=8, spacing=10)
    # 卢植 big arrow from 洛阳 (line 3)
    k3 = S.k(3, 2.2)
    if k3 > 0:
        big_arrow(c, [v.pt(112.6, 34.9), v.pt(113.8, 36.0), v.pt(114.9, 36.9)], ease(k3), 56, BLUE_L, 0.92, t=t, dash_flow=70)
        x, y = v.pt(113.0, 35.7)
        draw_text(c, "盧植 · 北軍五校", x, y, font("serif_blk_tc", 40), BLUE_L, k3, stroke=5, shadow=6)
    # 邹靖 arrow from 涿 south + red dot merging (line 1-2)
    k1 = S.k(1, 1.5)
    if k1 > 0:
        merge = ease(S.k(2, 1.5))
        zx, zy = v.pt("涿縣")
        rx = zx + (v.pt(116.0, 39.1)[0] - zx) * merge
        ry = zy + (v.pt(116.0, 39.1)[1] - zy) * merge
        glow_dot(c, rx, ry, 11, RED, k1 * (1 - 0.6 * ramp(t, S.e(2), S.e(2) + 1)))
        big_arrow(c, [v.pt(116.3, 39.4), v.pt(116.0, 38.6), v.pt(115.6, 37.8)], ease(S.k(2, 2.4, 1.0)), 38, BLUE_L, 0.9, t=t, dash_flow=60)
        draw_text(c, "校尉鄒靖", *v.pt(117.3, 38.9), font("serif_blk_tc", 38), BLUE_L, S.k(2, 0.6, 0.8), stroke=5)
        v.label(c, "涿縣", k1, size=32, dot=False, color=RED_L, dy=-24)
        # red stripe inside merged arrow
        if merge > 0.9:
            big_arrow(c, [v.pt(116.3, 39.4), v.pt(116.0, 38.6), v.pt(115.6, 37.8)], ease(S.k(2, 2.4, 1.0)), 12, RED, 0.9, glow=False)
    # 安喜 marker at end
    k5 = S.k(4, 0.6, 1.0)
    if k5 > 0:
        x, y = v.pt("安喜")
        glow_dot(c, x, y, 14, RED, k5)
        label_chip(c, x, y - 70, "中山 安喜尉", RED_L, k5, 40)


def v_dianlue(c, S):
    t = S.t
    draw_img(c, bg_night(51), 0, 0)
    tag(c, 70, 330, "另一说 · 裴注引《典略》", (210, 200, 180), ramp(t, 0.2, 0.7), size=36)
    c.drawRect(skia.Rect.MakeXYWH(0, 1250, W, 700), paint((14, 12, 14)))
    # 刘子平 recommends
    k0 = 1 - S.k(1, 0.5)
    if k0 > 0:
        figure(c, 320, 1250, 260, color=INK, rim=(220, 210, 190), rim_a=0.6, a=k0, sleeve=0.4)
        figure(c, 720, 1250, 280, color=INK, rim=BLUE_L, rim_a=0.6, a=k0, hat="guan", facing=-1)
        draw_text(c, "平原 劉子平", 320, 1320, font("serif_tc", 36), WHITE, k0, stroke=3)
        draw_text(c, "討張純的從事", 720, 1320, font("serif_tc", 36), BLUE_L, k0, stroke=3)
        big_arrow(c, [(420, 1000), (620, 1000)], ease(S.k(0, 0.8, 2.0)), 22, GOLD, k0, glow=False)
        draw_text(c, "薦", 520, 960, font("serif_blk_tc", 54), GOLD_L, S.k(0, 0.5, 2.4) * k0, stroke=4)
    k1 = S.k(1, 0.6)
    if k1 > 0:
        # lying figure
        c.save(); c.translate(540, 1240); c.rotate(-90)
        figure(c, 0, 0, 260, color=(30, 20, 20), a=k1, rim=RED_L, rim_a=1.0)
        c.restore()
        for i in range(6):
            horse(c, 1200 - ((t - S.s(1)) * 160 + i * 150), 1180 + (i % 2) * 20, 0.5, phase=t * 1.3 + i * 0.3, color=(30, 28, 34), facing=-1, gallop=1, rider=True, a=k1 * (1 - S.k(3, 0.6)))
    k3 = S.k(3, 0.6)
    if k3 > 0:
        # cart carrying away
        x = 540 - 300 * ease(S.k(3, 4.0, 0.5))
        c.drawRect(skia.Rect.MakeXYWH(x - 120, 1150, 240, 60), paint((50, 40, 34), k3))
        c.drawCircle(x - 70, 1220, 36, paint((80, 64, 50), k3, stroke=6))
        c.drawCircle(x + 70, 1220, 36, paint((80, 64, 50), k3, stroke=6))
        draw_text(c, "→ 以軍功為安喜尉", W / 2, 620, font("serif_blk_tc", 50), GOLD_L, S.k(3, 0.5, 2.5), stroke=5)


def v_three_q(c, S):
    t = S.t
    draw_img(c, bg_ink(53, (28, 22, 18), (60, 44, 30)), 0, 0)
    a = ramp(t, 0.1, 0.6)
    x0, y0, w, h = 60, 330, 960, 900
    rrect(c, x0, y0, w, h, 22, fill=(236, 224, 196), fill_a=0.96 * a, border=GOLD, border_a=a, bw=4, shadow=30)
    rrect(c, x0 + 16, y0 + 16, w - 32, h - 32, 14, border=(150, 110, 60), border_a=0.6 * a, bw=1.5)
    draw_text(c, "起家三問", W / 2, y0 + 110, font("serif_blk_tc", 66), (90, 30, 20), a, spacing=18)
    draw_text(c, "劉備 · 公元184年 · 安喜尉", W / 2, y0 + 170, font("serif_tc", 34), (110, 80, 50), a)
    rows = [("手里有什么", "私人部曲（人数史书无载）\n关羽、张飞 · 商人的钱"), ("借了谁的势", "州郡募义兵的口子\n校尉邹靖的旗号"), ("做对了哪一步", "私人武装挂到官军名下\n换来第一张正式身份")]
    for j, (q, ans) in enumerate(rows):
        kk = S.k(j + 1, 0.5)
        y = y0 + 240 + j * 215
        c.drawLine(x0 + 50, y - 20, x0 + w - 50, y - 20, paint((150, 110, 60), a * 0.5, stroke=1.5))
        draw_text(c, f"{'一二三'[j]}　{q}", x0 + 60, y + 50, font("serif_blk", 46), (150, 40, 28), a, align="l")
        for m, ln in enumerate(ans.split("\n")):
            draw_text(c, ln, x0 + 120, y + 120 + m * 56, font("sans_b", 40), (50, 36, 24), kk, align="l")
    k4 = S.k(4, 0.5)
    if k4 > 0:
        rrect(c, x0, 1255, w, 170, 14, fill=INK, fill_a=0.9 * k4, border=RED_L, border_a=k4)
        draw_text(c, "没有旗号＝地方武装", W / 2, 1325, font("serif_blk", 44), (220, 210, 190), k4)
        draw_text(c, "挂上官军旗号＝义兵，能论功受官", W / 2, 1395, font("serif_blk", 44), GOLD_L, S.k(4, 0.5, 2.0))


def v_duyou(c, S):
    t = S.t
    draw_img(c, bg_ink(57, (26, 18, 16), (66, 40, 30)), 0, 0)
    k0 = ramp(t, 0.1, 0.6) * (1 - S.k(2, 0.5))
    if k0 > 0:
        seal(c, W / 2, 820, 260, "安喜", a=k0, prog=1.0)
        draw_text(c, "第一块招牌", W / 2, 1060, font("serif_blk", 56), GOLD_L, k0, stroke=5, spacing=8)
        # crack
        ck = S.k(0, 0.4, 1.4)
        if ck > 0:
            crack = [(W / 2 - 150, 690), (W / 2 - 40, 790), (W / 2 + 10, 760), (W / 2 + 60, 880), (W / 2 + 150, 950)]
            c.drawPath(gfx.path_from(crack[:2 + int(3 * ck)], close=False), paint(INK, k0, stroke=8))
    k1 = S.k(1, 0.5)
    if k1 > 0 and t < S.s(2):
        tag(c, 80, 1150, "演义说", (200, 190, 170), k1, size=38)
        draw_text(c, "张飞怒鞭督邮", 290, 1200, font("serif_sc", 48), (220, 210, 190), k1, align="l")
        c.drawLine(290, 1186, 290 + 300 * ease(S.k(1, 0.5, 1.2)), 1186, paint((236, 110, 80), k1, stroke=5))
        tag(c, 80, 1260, "史书说", GOLD, S.k(1, 0.5, 1.8), size=38)
        draw_text(c, "动手的是刘备本人", 290, 1310, font("serif_sc", 48), GOLD_L, S.k(1, 0.5, 1.8), align="l")
    k2 = S.k(2, 0.5)
    if k2 > 0:
        # horse post with tied official
        c.drawRect(skia.Rect.MakeXYWH(700, 700, 26, 560), paint((60, 44, 30), k2))
        figure(c, 640, 1250, 280, color=INK, a=k2, hat="guan", rim=(220, 200, 170), rim_a=0.4)
        # 绶带 ribbon
        rib = skia.Path(); rib.moveTo(640, 1000); rib.cubicTo(680, 960 + math.sin(t * 3) * 10, 700, 1000, 713, 980)
        c.drawPath(rib, paint(RED, k2, stroke=10))
        lv = ease(S.k(4, 3.0))
        figure(c, 350 - 300 * lv, 1260, 300, color=INK, a=k2 * (1 - lv * 0.7), pose="walk", phase=t * 1.2, rim=RED_L, rim_a=0.8, facing=-1)
        c.drawRect(skia.Rect.MakeXYWH(0, 1255, W, 700), paint((20, 14, 12)))
        if S.k(2, 0.4, 2.0) > 0:
            draw_text(c, "杖二百", 760, 560, font("serif_blk_tc", 90), RED_L, S.k(2, 0.4, 2.0) * (1 - S.k(3, 0.4)), stroke=6, glow=14, glow_col=RED)
    k3 = fade_win(t, S.s(3), S.e(3) + 0.2, 0.5, 0.5)
    if k3 > 0:
        label_chip(c, W / 2, 520, "诏书：裁汰军功出身的长吏", (220, 210, 190), k3, 42)
    k5 = S.k(5, 0.6)
    if k5 > 0:
        draw_text(c, "敢做", W / 2, 640, font("serif_blk", 140), GOLD_L, k5, stroke=6, glow=24, glow_col=GOLD, spacing=30)


def v_ledger_sum(c, S):
    t = S.t
    draw_img(c, bg_ink(59, (28, 22, 18), (70, 50, 30)), 0, 0)
    notes = ["钱＋宗族信用", "名头", "期权", "真金白银"]
    nk = [S.k(1, 0.4, 0.0), S.k(1, 0.4, 2.3), S.k(1, 0.4, 3.6), S.k(1, 0.4, 6.2)]
    hi = 3 if S.t > S.s(2) else None
    ledger(c, W / 2, 820, 1.0, 1.0, [1, 1, 1, 1], [1, 1, 1, 1], notes=None)
    cols_x = [W / 2 + 920 / 2 - (12 - i) * (920 / 12) + 920 / 24 for i in (10, 7, 4, 1)]
    for i, x in enumerate(cols_x):
        if nk[i] > 0:
            label_chip(c, x, 1300 + (i % 2) * 90, notes[i], RED_L if i == 3 else GOLD_L, nk[i], 34)
    if hi is not None:
        x = cols_x[3]
        c.drawRect(skia.Rect.MakeXYWH(x - 90, 420, 180, 800), paint(GOLD_L, S.k(2, 0.4) * (0.6 + 0.4 * math.sin(t * 4)), stroke=5))
        for i in range(3):
            big_arrow(c, [(cols_x[i], 430), ((cols_x[i] + x) / 2, 330), (x, 420)], ease(S.k(2, 0.8, 3.5)), 14, GOLD, S.k(2, 0.4, 3.5) * (1 - S.k(3, 0.4)), glow=False)
    k3 = S.k(3, 0.6)
    if k3 > 0:
        rrect(c, 40, 380, 1000, 1000, 20, fill=INK, fill_a=0.94 * k3)
        f = font("serif_blk", 64)
        for j, ln in enumerate(["第一笔资源", "往往不来自能力", "而来自", "别人愿意押你一把"]):
            draw_text(c, ln, W / 2, 560 + j * 100, f, GOLD_L if j == 3 else WHITE, S.k(3, 0.5, j * 0.6), stroke=4, spacing=6)
        draw_text(c, "分清：哪张牌是名头，哪张牌能兑现", W / 2, 1060, font("sans_b", 46), RED_L, S.k(3, 0.5, 4.5), stroke=4)


def v_finale(c, S):
    t = S.t
    draw_img(c, bg_epic(61), 0, 0)
    # rider with red banner on ridge
    x = 540
    horse(c, x, 1010, 1.1, phase=t * 0.3, color=(16, 8, 8), facing=1, gallop=0.1, rider=True, rim=(255, 180, 90), rim_a=0.8)
    c.drawLine(x - 10, 880, x - 10, 560, paint(INK, 1, stroke=7))
    flag = skia.Path(); flag.moveTo(x - 10, 560)
    for k in range(13):
        u = k / 12; flag.lineTo(x - 10 + 200 * u, 560 + math.sin(t * 3 + u * 5) * 10 * u)
    for k in range(12, -1, -1):
        u = k / 12; flag.lineTo(x - 10 + 200 * u, 680 + math.sin(t * 3 + u * 5) * 10 * u)
    flag.close()
    c.drawPath(flag, paint(RED, 0.95))
    c.drawRect(skia.Rect.MakeXYWH(0, 1010, W, 900), paint((22, 12, 10)))
    embers(c, t, n=40, seed=12, a=0.6)
    k2 = S.k(2, 0.6)
    if k2 > 0 and t < S.s(3):
        f = font("serif_blk", 54)
        for j, ln in enumerate(["起家的本钱", "是一次又一次", "有人愿意押在他身上的信任"]):
            draw_text(c, ln, W / 2, 1180 + j * 82, f, GOLD_L if j == 2 else WHITE, S.k(2, 0.5, j * 0.8), stroke=5, shadow=8)
    k3 = S.k(3, 0.6)
    if k3 > 0:
        rrect(c, 90, 1120, 900, 260, 18, fill=INK, fill_a=0.85 * k3, border=GOLD, border_a=k3, bw=3)
        draw_text(c, "下一集", W / 2, 1200, font("sans_b", 40), (220, 210, 190), k3)
        draw_text(c, "从客将到徐州之主", W / 2, 1310, font("serif_blk", 72), GOLD_L, k3, spacing=8, glow=12, glow_col=GOLD)
    # end fade
    fo = ramp(t, S.dur - 1.2, S.dur)
    if fo > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, fo))


VIS = {k[2:]: v for k, v in globals().items() if k.startswith("v_")}
