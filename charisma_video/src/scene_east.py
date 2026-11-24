# -*- coding: utf-8 -*-
"""Han (bamboo slips, cinnabar) and Ottoman (miniature-style geometry, 19 lamps)."""
import math, random
import numpy as np
import skia
from engine import *
from shapes import horse_paths, ogee_arch, star8

CINNABAR = (196, 52, 36)
BAMBOO = (206, 178, 120)
BAMBOO_DK = (150, 118, 70)
HAN_BG = ((20, 14, 10), (44, 32, 22))

@functools.lru_cache(None)
def slip_texture(w=64, h=560, seed=0):
    rng = np.random.default_rng(seed)
    base = np.array(BAMBOO, np.float32)
    x = np.arange(w)[None, :].astype(np.float32)
    stripes = 0.06 * np.sin(x * 0.9 + rng.uniform(0, 6)) + 0.04 * np.sin(x * 2.7)
    img = np.ones((h, w, 3), np.float32) * base
    img *= (1 + stripes[..., None])
    img *= (1 + rng.normal(0, 0.02, (h, w))[..., None])
    edge = np.minimum(x, w - 1 - x) / 6.0
    img *= np.clip(0.75 + 0.25 * np.minimum(edge, 1), 0, 1)[..., None]
    # age spots
    for _ in range(4):
        cy, cx = rng.integers(0, h), rng.integers(0, w)
        yy, xx = np.mgrid[0:h, 0:w]
        img *= (1 - 0.12 * np.exp(-((yy - cy) ** 2 / 900 + (xx - cx) ** 2 / 200)))[..., None]
    out = np.dstack([np.clip(img, 0, 255).astype(np.uint8), np.full((h, w), 255, np.uint8)])
    return to_image(out)

SLIPS = [
    # (text, colour) – vertical, read right to left
    ("高帝刑白马盟曰", "ink"),
    ("非刘氏而王", "red"),
    ("天下共击之", "red"),
    ("今王吕氏非约也", "ink"),
]

def draw_han(c, horse_a=1.0, slips_a=1.0, red_a=1.0, seal_a=1.0, extra=None):
    draw_bg(c, tint=HAN_BG)
    # faint ink-wash hills
    for k, (y, a) in enumerate(((720, 0.10), (780, 0.14))):
        pa = path_from([(0, y), (180, y - 70 - k * 20), (360, y - 20), (560, y - 110), (760, y - 40),
                        (920, y - 90), (1080, y - 30), (1080, y + 200), (0, y + 200)], closed=True, smooth=True)
        c.drawPath(pa, paint((80, 70, 56), a * horse_a, blur=6))
    # white horse
    if horse_a > 0:
        body, tail, mane = horse_paths(560, 520, 300, flip=True)
        glowp = paint((255, 250, 235), 0.25 * horse_a, blur=24)
        c.drawPath(body, glowp)
        for pa in (tail, body):
            c.drawPath(pa, paint((236, 230, 214), horse_a))
        c.drawPath(mane, paint((210, 204, 190), horse_a))
        # ground line
        c.drawLine(300, 780, 840, 780, paint((180, 160, 120), 0.35 * horse_a, stroke=2))
    # bamboo slips
    if slips_a > 0:
        n = len(SLIPS) + 3
        sw, gap = 70, 8
        total = n * sw + (n - 1) * gap
        x0 = (W - total) / 2
        top, h = 840, 400
        tex = slip_texture(64, 560, 1)
        for k in range(n):
            x = x0 + k * (sw + gap)
            a = clamp(slips_a * (n + 2) / 3 - (n - 1 - k) * 0.25)  # unroll from right
            if a <= 0:
                continue
            dst = skia.Rect.MakeXYWH(x, top, sw, h)
            pp = skia.Paint(AntiAlias=True); pp.setAlphaf(a)
            c.drawImageRect(tex, dst, skia.SamplingOptions(skia.FilterMode.kLinear), pp)
            c.drawRect(dst, paint(BAMBOO_DK, a * 0.8, stroke=1.5))
        # cords
        for cy in (top + 50, top + h - 50):
            c.drawLine(x0 - 14, cy, x0 + total + 14, cy, paint((120, 60, 40), slips_a, stroke=5))
            c.drawLine(x0 - 14, cy + 4, x0 + total + 14, cy + 4, paint((70, 34, 24), slips_a * 0.6, stroke=2))
        # text columns right to left, on slips 6,5,4,3 (from left index)
        for j, (txt, kind) in enumerate(SLIPS):
            k = n - 2 - j
            x = x0 + k * (sw + gap) + sw / 2
            col = CINNABAR if kind == "red" else (34, 24, 16)
            al = slips_a * (red_a if kind == "red" else 1.0)
            size = 46 if len(txt) <= 5 else 40
            step = (h - 120) / len(txt)
            for i, ch in enumerate(txt):
                draw_text(c, ch, x, top + 82 + i * step + size * 0.8, "serif_b", size, col, al, align="center")
        # source label
        draw_text(c, "《史记·吕太后本纪》", W / 2, top + h + 52, "serif", 28, IVORY, slips_a * 0.85, align="center")
    # seal
    if seal_a > 0:
        sx, sy = 852, 1150
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx, sy, 84, 84), 6, 6)
        c.drawRRect(rr, paint(CINNABAR, 0.9 * seal_a))
        for i, ch in enumerate(["白", "马", "之", "盟"]):
            draw_text(c, ch, sx + 62 - (i // 2) * 40, sy + 36 + (i % 2) * 38, "serif_b", 30, (250, 230, 210),
                      0.95 * seal_a, align="center")

# ---------------------------------------------------------------- Ottoman
LAPIS = (22, 44, 104)
TURQ = (40, 150, 150)
OT_GOLD = (222, 180, 80)
VERMIL = (186, 60, 40)

@functools.lru_cache(None)
def ottoman_pattern():
    surf = new_surface(); c = surf.getCanvas()
    c.clear(C(*LAPIS))
    # 8-point star lattice
    step = 120
    for row in range(-1, H // step + 2):
        for col in range(-1, W // step + 2):
            cx = col * step + (step / 2 if row % 2 else 0)
            cy = row * step
            c.drawPath(star8(cx, cy, 46, 0.55), paint((30, 62, 132)))
            c.drawPath(star8(cx, cy, 46, 0.55), paint(OT_GOLD, 0.55, stroke=2))
            c.drawCircle(cx, cy, 12, paint(TURQ, 0.8))
            # connecting lines
            c.drawLine(cx + 46, cy, cx + step - 46, cy, paint(OT_GOLD, 0.35, stroke=1.5))
    return surf.makeImageSnapshot()

LAMP_POS = []
for r, (n, y) in enumerate(((7, 650), (6, 830), (6, 1010))):
    for k in range(n):
        x = 540 + (k - (n - 1) / 2) * 128
        LAMP_POS.append((x, y))

def lamp(c, x, y, lit, smoke=0.0, alpha=1.0, swing=0.0):
    # chain from above
    c.drawLine(x, y - 150, x, y - 42, paint(OT_GOLD, 0.6 * alpha, stroke=2))
    for k in range(3):
        c.drawLine(x, y - 42, x + (k - 1) * 22, y - 18, paint(OT_GOLD, 0.6 * alpha, stroke=1.6))
    # glow
    if lit > 0:
        radial(c, x, y + 4, 90, (255, 200, 110, 150), (255, 170, 60, 0), alpha=lit * alpha)
    # glass body (mosque lamp shape)
    pa = path_from([(x - 22, y - 18), (x + 22, y - 18), (x + 14, y - 2), (x + 30, y + 16), (x + 24, y + 36),
                    (x + 8, y + 46), (x - 8, y + 46), (x - 24, y + 36), (x - 30, y + 16), (x - 14, y - 2)],
                   closed=True, smooth=True)
    body_col = mix((24, 54, 70), (250, 214, 140), lit)
    c.drawPath(pa, paint(body_col, alpha * 0.95))
    c.drawPath(pa, paint(OT_GOLD, alpha * (0.5 + 0.5 * lit), stroke=2))
    # band decoration
    c.drawLine(x - 28, y + 16, x + 28, y + 16, paint(VERMIL if lit > 0.5 else (90, 40, 36), alpha * 0.8, stroke=3))
    if lit > 0:
        flame = path_from([(x, y - 2), (x + 6, y + 12), (x, y + 20), (x - 6, y + 12)], closed=True, smooth=True)
        c.drawPath(flame, paint((255, 246, 200), lit * alpha))
    if smoke > 0:
        pa = path_from([(x, y - 6), (x + 6, y - 30), (x - 5, y - 52), (x + 4, y - 78)], smooth=True)
        draw_path_progress(c, pa, paint((200, 200, 210), 0.45 * (1 - smoke) * alpha, stroke=3, blur=2), smoke)

def draw_ottoman(c, lamps_on=19, fading=0.0, arches_a=1.0, smoke_i=None, main=0.0):
    c.drawImage(ottoman_pattern(), 0, 0)
    # darken
    c.drawRect(skia.Rect.MakeWH(W, H), paint((4, 8, 20), 0.55))
    vignette(c, W / 2, 820, 1100, 200)
    # arcade frame
    if arches_a > 0:
        for k in range(3):
            x = 70 + k * 320
            arch = ogee_arch(x, 520, 300, 680)
            c.drawPath(arch, paint((6, 14, 34), 0.55 * arches_a))
            c.drawPath(arch, paint(OT_GOLD, arches_a, stroke=5))
            inner = ogee_arch(x + 14, 534, 272, 652)
            c.drawPath(inner, paint(VERMIL, 0.7 * arches_a, stroke=2))
        # border band
        band = skia.Rect.MakeLTRB(40, 440, W - 40, 1240)
        c.drawRect(band, paint(OT_GOLD, arches_a, stroke=4))
        c.drawRect(band.makeInset(12, 12), paint(TURQ, 0.8 * arches_a, stroke=2))
        for k in range(14):
            x = 80 + k * 66
            c.drawPath(star8(x, 470, 14, 0.5), paint(OT_GOLD, 0.8 * arches_a))
    # lamps: those with index < lamps_on are lit; index lamps_on is fading
    for i, (x, y) in enumerate(LAMP_POS):
        if i < lamps_on:
            lit = 1.0
        elif i == lamps_on:
            lit = 1 - fading
        else:
            lit = 0.0
        sm = fading if i == lamps_on else (1.0 if i > lamps_on else 0.0)
        lamp(c, x, y, lit, smoke=sm if i == lamps_on else 0.0)
    if main > 0:
        c.drawLine(540, 300, 540, 470, paint(OT_GOLD, 0.6 * main, stroke=2))
        c.save(); c.translate(540, 560); c.scale(1.5, 1.5); c.translate(-540, -560)
        lamp(c, 540, 560, 1.0, alpha=main)
        c.restore()
