# -*- coding: utf-8 -*-
"""Saul chosen by lot (1 Samuel 10): tribes -> clan -> man; hiding among the baggage; taller by a head."""
import math, random
import skia
from engine import *
from shapes import xf

SAND = (196, 160, 104)
SAND_DK = (120, 92, 56)
CLAY = (150, 92, 60)
SAUL_BG = ((22, 18, 12), (48, 38, 24))

def stone(c, x, y, r, lit, alpha=1.0, label=None):
    col = mix(SAND_DK, (250, 220, 150), lit)
    if lit > 0:
        radial(c, x, y, r * 3, (250, 214, 140, 120), (250, 200, 120, 0), alpha=lit * alpha)
    pa = path_from([(x - r, y + r * 0.2), (x - r * 0.6, y - r * 0.8), (x + r * 0.5, y - r * 0.9), (x + r, y),
                    (x + r * 0.6, y + r * 0.8), (x - r * 0.5, y + r * 0.9)], closed=True, smooth=True)
    c.drawPath(pa, paint(col, alpha))
    c.drawPath(pa, paint((40, 30, 18), alpha * 0.8, stroke=2))
    if label:
        draw_text(c, label, x, y + r + 34, "serif", 24, IVORY, alpha * (0.5 + 0.5 * lit), align="center")

def figure(c, x, y, h, col, alpha=1.0, outline=None, dashed=False):
    """simple robed figure silhouette, feet at y, height h"""
    r = h * 0.11
    body = path_from([(x - h * 0.17, y), (x - h * 0.13, y - h * 0.55), (x - h * 0.09, y - h * 0.74),
                      (x + h * 0.09, y - h * 0.74), (x + h * 0.13, y - h * 0.55), (x + h * 0.17, y)], closed=True, smooth=True)
    head = skia.Path(); head.addCircle(x, y - h * 0.86, r)
    if dashed:
        p = paint(outline or IVORY, alpha, stroke=2.5)
        p.setPathEffect(skia.DashPathEffect.Make([9, 8], 0))
        c.drawPath(body, p); c.drawPath(head, p)
        return
    c.drawPath(body, paint(col, alpha)); c.drawPath(head, paint(col, alpha))
    if outline:
        c.drawPath(body, paint(outline, alpha, stroke=2.5)); c.drawPath(head, paint(outline, alpha, stroke=2.5))

def jar(c, x, y, s, alpha=1.0):
    pa = path_from([(x - 14 * s, y - 60 * s), (x + 14 * s, y - 60 * s), (x + 12 * s, y - 52 * s), (x + 30 * s, y - 34 * s),
                    (x + 26 * s, y - 6 * s), (x + 12 * s, y), (x - 12 * s, y), (x - 26 * s, y - 6 * s), (x - 30 * s, y - 34 * s),
                    (x - 12 * s, y - 52 * s)], closed=True, smooth=True)
    c.drawPath(pa, paint(CLAY, alpha)); c.drawPath(pa, paint((60, 34, 20), alpha, stroke=2))
    c.drawLine(x - 24 * s, y - 34 * s, x + 24 * s, y - 34 * s, paint((90, 50, 30), alpha, stroke=3))

def sack(c, x, y, w, h, alpha=1.0):
    pa = path_from([(x - w / 2, y), (x - w / 2 + 6, y - h * 0.8), (x - w * 0.15, y - h), (x + w * 0.15, y - h),
                    (x + w / 2 - 6, y - h * 0.8), (x + w / 2, y)], closed=True, smooth=True)
    c.drawPath(pa, paint((140, 116, 80), alpha)); c.drawPath(pa, paint((60, 46, 28), alpha, stroke=2))

TRIBES = ["流便", "西缅", "利未", "犹大", "以萨迦", "西布伦", "但", "拿弗他利", "迦得", "亚设", "以法莲", "便雅悯"]

def draw_saul(c, tribes=0.0, pick=0.0, clans=0.0, pick2=0.0, men=0.0, pick3=0.0, hide=0.0, tall=0.0, doubt=0.0):
    draw_bg(c, tint=SAUL_BG)
    # stage 1: twelve tribe stones in an arc
    a1 = tribes * (1 - ease(clans))
    if a1 > 0:
        for i in range(12):
            ang = math.radians(200 + i * (140 / 11))
            x = 540 + 400 * math.cos(ang); y = 860 + 400 * math.sin(ang)
            ai = clamp(tribes * 14 - i) * a1
            lit = pick if i == 11 else 0.0
            dim = (1 - 0.6 * pick) if i != 11 else 1
            stone(c, x, y, 34, lit, ai * dim, "便雅悯" if (i == 11 and pick > 0.3) else None)
        draw_text(c, "十二支派", 540, 820, "serif_sb", 40, GOLD, a1 * (1 - pick), align="center")
        draw_text(c, "便雅悯支派", 540, 820, "serif_sb", 44, GOLD_HI, a1 * pick, align="center")
    # stage 2: clans of Benjamin
    a2 = clans * (1 - ease(men))
    if a2 > 0:
        for i in range(6):
            x = 540 + (i - 2.5) * 150; y = 700
            lit = pick2 if i == 3 else 0.0
            stone(c, x, y, 30, lit, a2 * ((1 - 0.6 * pick2) if i != 3 else 1), "玛特利族" if i == 3 else None)
        draw_text(c, "按宗族抽", 540, 560, "serif_sb", 40, GOLD, a2, align="center")
    # stage 3: men of the clan; the lot falls on one, who is missing
    a3 = men * (1 - ease(tall) * 0.0)
    if a3 > 0 and tall < 1:
        aa = a3 * (1 - ease(tall))
        draw_text(c, "签落在基士的儿子扫罗身上", 540, 470, "serif_sb", 40, GOLD_HI, aa * pick3, align="center")
        for i in range(7):
            x = 540 + (i - 3) * 130; y = 900
            if i == 3:
                if pick3 > 0:
                    radial(c, x, y - 120, 200, (250, 214, 140, 90), (250, 200, 120, 0), alpha=aa * pick3)
                if hide > 0:
                    figure(c, x, y, 250, None, aa * hide, outline=GOLD_HI, dashed=True)
                    draw_text(c, "？", x, y - 120, "serif_b", 72, GOLD_HI, aa * hide, align="center")
                figure(c, x, y, 250, (70, 56, 36), aa * (1 - hide), outline=GOLD_HI if pick3 > 0 else None)
            else:
                figure(c, x, y, 230, (52, 42, 28), aa * (1 - 0.4 * pick3))
        # baggage pile with a figure peeking
        if hide > 0:
            bx = 540; by = 1180
            ah = aa * hide
            draw_text(c, "“他藏在器具中了。”", 540, 1262, "serif", 34, IVORY, ah, align="center")
            figure(c, bx + 10, by - 10, 170, (70, 56, 36), ah, outline=GOLD_HI)
            for k, (dx, s) in enumerate(((-150, 1.2), (-60, 1.5), (60, 1.3), (150, 1.1))):
                jar(c, bx + dx, by, s, ah)
            sack(c, bx - 20, by + 4, 150, 70, ah); sack(c, bx + 90, by + 4, 110, 60, ah)
    # stage 4: standing among the people, taller by a head
    if tall > 0:
        at = ease(tall)
        rnd = random.Random(3)
        for i in range(11):
            x = 80 + i * 92
            if i == 5:
                continue
            h = 300 + rnd.uniform(-14, 14)
            figure(c, x, 1180, h, (46, 38, 26), at * (1 - 0.35 * doubt))
        figure(c, 540, 1180, 380, (86, 68, 40), at, outline=GOLD_HI)
        radial(c, 540, 840, 220, (250, 214, 140, 70), (250, 200, 120, 0), alpha=at)
        c.drawLine(470, 840 + 6, 610, 840 + 6, paint(GOLD, at * 0.6, stroke=2))
        draw_text(c, "身体比众民高过一头", 540, 640, "serif_sb", 38, GOLD_HI, at * (1 - doubt), align="center")
        if doubt > 0:
            draw_text(c, "“这人怎能救我们呢？”", 540, 600, "serif_b", 52, RED, doubt, align="center")
            draw_text(c, "——《撒母耳记上》10:27（和合本）", 540, 660, "serif", 28, IVORY, doubt * 0.85, align="center")
