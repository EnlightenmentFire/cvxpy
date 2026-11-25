# -*- coding: utf-8 -*-
"""Visual panels. Each visual: static(params)->RGBA full frame (cached) + dyn(base, tl, dur, p, ev).
ev: dict(strikes=[t...] relative to visual start, lines=[(s,e)...] relative to visual start)."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

VIS = {}


def visual(name, tag=None):
    def deco(cls):
        VIS[name] = cls(); VIS[name].tag = tag
        return cls
    return deco


def line_idx(tl, ev):
    k = -1
    for i, (s, e) in enumerate(ev.get("lines", [])):
        if tl >= s - 0.05:
            k = i
    return k


def line_t(i, ev, default=0.0):
    L = ev.get("lines", [])
    return L[i][0] if 0 <= i < len(L) else default


# ------------------------------------------------------------------ particles
def dust(base, t, n=60, seed=1, col=(230, 200, 140), area=(0, 0, W, H), speed=18, size=(2, 5), amax=150):
    rng = np.random.default_rng(seed)
    x0 = rng.uniform(area[0], area[2], n); y0 = rng.uniform(area[1], area[3], n)
    vx = rng.uniform(-0.3, 0.3, n) * speed; vy = rng.uniform(-1, -0.2, n) * speed
    ph = rng.uniform(0, 6.28, n); sz = rng.uniform(size[0], size[1], n)
    d = ImageDraw.Draw(base)
    h = area[3] - area[1]
    for i in range(n):
        x = x0[i] + vx[i] * t + 14 * math.sin(t * 0.6 + ph[i])
        y = area[1] + (y0[i] - area[1] + vy[i] * t) % h
        a = int(amax * (0.5 + 0.5 * math.sin(t * 1.3 + ph[i])))
        r = sz[i]
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))


# ------------------------------------------------------------------ gate (衙门夜景)
STICK_COLS = [(46, 104, 140), (178, 46, 36), (206, 164, 58), (226, 224, 214), (34, 32, 30)]


@functools.lru_cache(maxsize=2)
def gate_static(moon=True):
    y = np.linspace(0, 1, H)[:, None, None]
    sky = np.array([10, 14, 30], np.float32) * (1 - y) + np.array([4, 4, 8], np.float32) * y
    img = Image.fromarray(sky.repeat(W, 1).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(7)
    for _ in range(140):
        x, yy = rng.uniform(0, W), rng.uniform(0, 700)
        a = int(rng.uniform(40, 160)); r = rng.uniform(0.8, 2.0)
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=(220, 220, 255, a))
    # moon
    if moon:
        m = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dm = ImageDraw.Draw(m)
        dm.ellipse([780, 210, 900, 330], fill=(230, 222, 196, 230))
        img.alpha_composite(m.filter(ImageFilter.GaussianBlur(28))); img.alpha_composite(m)
    # distant city roofs
    for k in range(9):
        x = -60 + k * 140; hh = 40 + (k * 37) % 50
        d.polygon([(x, 900), (x + 70, 900 - hh), (x + 140, 900)], fill=(16, 18, 28, 255))
    d.rectangle([0, 900, W, 960], fill=(16, 18, 28, 255))
    # main wall
    wall_top, wall_bot = 1000, 1390
    d.rectangle([0, wall_top, W, wall_bot], fill=(34, 32, 36, 255))
    for row in range(wall_top, wall_bot, 26):      # bricks
        off = 0 if (row // 26) % 2 else 34
        d.line([(0, row), (W, row)], fill=(24, 22, 26, 255), width=2)
        for x in range(off, W, 68):
            d.line([(x, row), (x, row + 26)], fill=(24, 22, 26, 255), width=2)
    # roof
    rt = 800
    roof = [(-40, 1010), (60, 960), (180, 900), (300, rt + 40), (540, rt), (780, rt + 40), (900, 900), (1020, 960), (1120, 1010)]
    d.polygon(roof + [(1120, 1030), (-40, 1030)], fill=(14, 14, 18, 255))
    d.line(roof, fill=GOLD + (200,), width=4)
    for x in range(-20, 1100, 28):
        d.line([(x, 1012), (x, 1030)], fill=(30, 28, 30, 255), width=6)
    # gate opening
    d.rectangle([380, 1110, 700, 1390], fill=(6, 6, 8, 255))
    d.pieslice([380, 1030, 700, 1190], 180, 360, fill=(6, 6, 8, 255))
    d.rectangle([386, 1150, 536, 1390], outline=(70, 40, 28, 255), width=3, fill=(40, 22, 16, 255))
    d.rectangle([544, 1150, 694, 1390], outline=(70, 40, 28, 255), width=3, fill=(40, 22, 16, 255))
    for yy in range(1180, 1380, 46):
        for xx in (420, 470, 510, 580, 620, 660):
            d.ellipse([xx - 5, yy - 5, xx + 5, yy + 5], fill=(150, 116, 60, 255))
    # plaque
    d.rectangle([420, 1040, 660, 1100], fill=(12, 10, 10, 255), outline=GOLD + (255,), width=3)
    pt = text_img("北部尉", sc_font(KAI, 46), GOLD_L)
    img.alpha_composite(pt, (540 - pt.width // 2, 1043))
    # stick racks
    for side, x0 in (("L", 70), ("R", 760)):
        d.rectangle([x0 - 10, 1120, x0 + 260, 1134], fill=(60, 40, 26, 255))
        d.rectangle([x0 - 10, 1360, x0 + 260, 1372], fill=(60, 40, 26, 255))
        for i in range(12):
            c = STICK_COLS[i % 5]; x = x0 + 6 + i * 21
            d.rounded_rectangle([x, 1100, x + 13, 1380], 6, fill=c + (255,), outline=(0, 0, 0, 255))
            d.line([(x + 3, 1108), (x + 3, 1370)], fill=tuple(min(255, v + 50) for v in c) + (200,), width=2)
            d.rectangle([x - 1, 1100, x + 14, 1112], fill=GOLD + (255,))
    # road
    for k in range(14):
        yy = 1390 + int(530 * (k / 14) ** 1.6)
        d.line([(0, yy), (W, yy)], fill=(22, 20, 24, 255), width=2)
    d.rectangle([0, 1390, W, H], fill=None)
    road = Image.new("RGBA", (W, H - 1390), (18, 17, 20, 255))
    img.alpha_composite(road, (0, 1390))
    d = ImageDraw.Draw(img)
    for k in range(1, 16):
        yy = 1390 + int(530 * (k / 16) ** 1.7)
        d.line([(0, yy), (W, yy)], fill=(30, 28, 32, 255), width=2)
    for k in range(-10, 11):
        d.line([(540 + k * 30, 1390), (540 + k * 220, H)], fill=(30, 28, 32, 255), width=2)
    return img


@functools.lru_cache(maxsize=2)
def lantern_img():
    im = Image.new("RGBA", (220, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([(110, 0), (110, 60)], fill=(40, 30, 20, 255), width=4)
    d.ellipse([60, 60, 160, 200], fill=(214, 70, 40, 255))
    d.rectangle([80, 56, 140, 68], fill=(30, 24, 20, 255)); d.rectangle([80, 194, 140, 206], fill=(30, 24, 20, 255))
    for k in (80, 110, 140):
        d.arc([k - 50 + (110 - k) // 2, 60, k + 50 - (110 - k) // 2, 200], 270, 90, fill=(160, 40, 24, 255), width=2)
    t = text_img("尉", sc_font(KAI, 44), (40, 10, 6))
    im.alpha_composite(t, (110 - t.width // 2, 104))
    return im


@functools.lru_cache(maxsize=2)
def lantern_glow():
    g = Image.new("RGBA", (700, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([250, 250, 450, 450], fill=(255, 150, 70, 200))
    return g.filter(ImageFilter.GaussianBlur(90))


@functools.lru_cache(maxsize=2)
def figure_img():
    im = Image.new("RGBA", (200, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([78, 10, 122, 58], fill=(8, 8, 10, 255))
    d.polygon([(70, 6), (130, 6), (124, 22), (76, 22)], fill=(8, 8, 10, 255))
    d.polygon([(64, 60), (136, 60), (170, 400), (30, 400)], fill=(8, 8, 10, 255))
    d.line([(136, 90), (186, 200)], fill=(8, 8, 10, 255), width=16)
    return im


@functools.lru_cache(maxsize=2)
def swoosh_img():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k in range(18):
        a = 200 - k * 10
        d.arc([120 - k * 6, 760 - k * 6, 1100 + k * 6, 1740 + k * 6], 200, 265, fill=(255, 230, 170, max(a, 20)), width=10)
    return im.filter(ImageFilter.GaussianBlur(5))


@functools.lru_cache(maxsize=4)
def big_title(t, size=170):
    f = sc_font(KAI, size)
    if f.getlength(t) > 960:
        size = int(size * 960 / f.getlength(t))
    return glow(text_img(t, sc_font(KAI, size), GOLD_L, stroke=2, stroke_fill=(60, 40, 10)), 26, 1.7)


def strike_fx(base, tl, ev):
    """flash + swoosh near strike times; returns shake offset."""
    sh = 0.0
    for s in ev.get("strikes", []):
        dt = tl - s
        if -0.12 <= dt < 0:
            paste(base, swoosh_img(), 0, 0, (dt + 0.12) / 0.12)
        if 0 <= dt < 0.6:
            a = (1 - dt / 0.6) ** 2
            fl = Image.new("RGBA", (W, H), (255, 236, 200, int(120 * a)))
            base.alpha_composite(fl)
            sh = max(sh, 16 * a)
    return sh


@visual("gate", tag="情景示意")
class Gate:
    def static(self, p):
        return gate_static()

    def dyn(self, base, tl, dur, p, ev):
        t = tl
        for x in (300, 780):
            fl = 0.75 + 0.18 * math.sin(t * 7.1 + x) + 0.07 * math.sin(t * 13.3 + x * 0.3)
            paste(base, lantern_glow(), x - 350, 1050 - 350, fl)
            paste(base, lantern_img(), x - 110, 920)
        if p.get("figure"):
            a = clamp01((tl - p.get("fig_t", 0)) / 0.6)
            paste(base, figure_img(), 440, 1420, a)
        dust(base, t, n=50, seed=3, col=(200, 200, 220), area=(0, 300, W, 1900), speed=14, amax=90)
        if p.get("title"):
            a = (1.0 if p.get("title_now") else clamp01(tl / 0.5)) * (1 - clamp01((tl - p.get("title_dur", 99)) / 0.5))
            bt = big_title(p["title"])
            paste_c(base, bt, 540, 520 + 10 * (1 - ease_out(tl / 0.8)), a)
        return strike_fx(base, tl, ev)


# ------------------------------------------------------------------ name card
@visual("name")
class Name:
    def static(self, p):
        return dark_bg(11).copy()

    def dyn(self, base, tl, dur, p, ev):
        dust(base, tl, n=40, seed=5)
        a = ease(tl / 0.7)
        paste_c(base, big_title(p.get("text", "曹操"), 230), 540, 700, a)
        sub = text_img(p.get("sub", "字孟德 · 沛国谯县人"), sc_font(SERIF_R, 46), IVORY)
        paste_c(base, sub, 540, 900, ease((tl - 0.5) / 0.6))
        if p.get("tag"):
            tg = pill(p["tag"], (240, 220, 255), PURPLE + (255,), size=44, pad=(26, 10))
            k = ease_out((tl - p.get("tag_t", 1.6)) / 0.5)
            paste_c(base, tg, 540, 1040 + 30 * (1 - k), k)


# ------------------------------------------------------------------ family tree
def node(d, base, cx, cy, r, fill, ring, name, sub, a=1.0, namecol=IVORY):
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    dl.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill + (255,), outline=ring + (255,), width=5)
    lay = glow(lay, 16, 1.0) if ring == GOLD else lay
    nm = text_img(name, sc_font(KAI, 64), namecol)
    lay.alpha_composite(nm, (int(cx - nm.width / 2), int(cy - nm.height / 2)))
    if sub:
        s = text_img(sub, sc_font(SANS_R, 32), (215, 210, 200), maxw=560, align="center")
        lay.alpha_composite(s, (int(cx - s.width / 2), int(cy + r + 12)))
    paste(base, lay, 0, 0, a)


@functools.lru_cache(maxsize=4)
def tree_layer(doubt, stage):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    return lay


@visual("tree")
class Tree:
    def static(self, p):
        return dark_bg(12, top=(18, 12, 24)).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        a1, a2, a3 = ease(tl / 0.5), ease((tl - 0.6) / 0.5), ease((tl - 1.2) / 0.5)
        if a2 > 0:
            d.line([(540, 520), (540, 760)], fill=PURPLE_L + (int(200 * a2),), width=6)
            lab = text_img("养子", sc_font(SANS_B, 34), PURPLE_L); paste(base, lab, 560, 610, a2)
        if a3 > 0:
            d.line([(540, 900), (540, 1130)], fill=GOLD + (int(200 * a3),), width=6)
        node(d, base, 540, 440, 86, (60, 30, 80), PURPLE, "曹腾", None, a1)
        st = text_img("中常侍 · 大长秋 · 费亭侯", sc_font(SANS_R, 34), (220, 200, 235))
        paste_c(base, st, 540, 560 - 20, a1 * 0)
        paste_c(base, st, 820 if False else 540, 330, a1)
        node(d, base, 540, 830, 76, (50, 50, 56), (150, 150, 160), "曹嵩", None, a2)
        q = text_img("生出本末不详", sc_font(SANS_R, 32), (200, 200, 205)); paste(base, q, 640, 805, a2)
        node(d, base, 540, 1220, 92, CAO, GOLD, "曹操", None, a3, namecol=GOLD_L)
        if p.get("money"):
            m = text_img("后官至太尉（据《后汉书》：输西园钱一亿）", sc_font(SANS_R, 32), GOLD)
            paste_c(base, m, 540, 932, a3)
        if p.get("doubt"):
            k = ease((tl - 0.3) / 0.6)
            for yy in range(0, 200, 22):
                d.line([(250, 700 + yy * 0.6), (262, 706 + yy * 0.6)], fill=(170, 170, 180, int(200 * k)), width=3)
            d.line([(200, 830), (440, 830)], fill=(170, 170, 180, int(160 * k)), width=3)
            nd = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dn = ImageDraw.Draw(nd)
            for x in range(80, 330, 24):
                dn.line([(x, 830), (x + 12, 830)], fill=(200, 200, 210, 255), width=4)
            paste(base, nd, 0, 0, k)
            xh = text_img("夏侯氏？", sc_font(KAI, 52), (200, 200, 210)); paste_c(base, xh, 150, 760, k)
            src = text_img("《曹瞒传》《世语》说，敌国之说，存疑", sc_font(SANS_R, 28), (190, 190, 196), maxw=300, align="center")
            paste_c(base, src, 160, 930, k)


# ------------------------------------------------------------------ big text
@visual("bigtext")
class BigText:
    def static(self, p):
        return dark_bg(13).copy()

    def dyn(self, base, tl, dur, p, ev):
        txt = p["text"]; size = p.get("size", 170)
        f = sc_font(KAI, size)
        n = len(txt)
        widths = [f.getlength(c) for c in txt]
        total = sum(widths)
        if total > 980:
            size = int(size * 980 / total); f = sc_font(KAI, size); widths = [f.getlength(c) for c in txt]; total = sum(widths)
        x = 540 - total / 2; y = p.get("y", 760)
        for i, c in enumerate(txt):
            a = ease((tl - 0.15 * i) / 0.45)
            if a > 0:
                ci = big_title(c, size)
                paste_c(base, ci, x + widths[i] / 2, y + 12 * (1 - a), a)
            x += widths[i]
        if p.get("cap"):
            cap = text_img(p["cap"], sc_font(SANS_R, 38), (215, 210, 200), maxw=900, align="center")
            paste_c(base, cap, 540, y + size * 0.5 + 90, ease((tl - 0.15 * n - 0.2) / 0.5))
        dust(base, tl, n=36, seed=9)


# ------------------------------------------------------------------ 钱 官 名
@visual("lack")
class Lack:
    def static(self, p):
        return dark_bg(14).copy()

    def dyn(self, base, tl, dur, p, ev):
        items = [("钱", True), ("官", True), ("名", False)]
        for i, (c, ok) in enumerate(items):
            a = ease_out((tl - 0.45 * i) / 0.45)
            if a <= 0: continue
            cx = 220 + i * 320; cy = 760
            box = rrect((260, 300), 20, (12, 12, 14, 230), outline=(GOLD if not ok else (120, 120, 126)) + (255,), width=4)
            paste_c(base, box, cx, cy + 20 * (1 - a), a)
            col = (170, 170, 176) if ok else GOLD_L
            g = text_img(c, sc_font(KAI, 170), col)
            if not ok:
                pulse = 0.8 + 0.2 * math.sin(tl * 4)
                g = glow(g, 24, 1.2 + pulse)
            paste_c(base, g, cx, cy - 20 + 20 * (1 - a), a)
            mk = text_img("有" if ok else "缺", sc_font(SANS_B, 48), (150, 200, 150) if ok else (240, 120, 100))
            paste_c(base, mk, cx, cy + 210, a)
        cap = p.get("cap")
        if cap:
            ci = text_img(cap, sc_font(SERIF_B, 48), IVORY, maxw=900, align="center")
            paste_c(base, ci, 540, 1120, ease((tl - 1.6) / 0.5))


# ------------------------------------------------------------------ bamboo slips (评语卡)
def slip_board(ncol=4):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 140, 390, 940, 1250
    nsl = 8; sw = (x1 - x0) / nsl
    for i in range(nsl):
        xa = x0 + i * sw + 4; xb = x0 + (i + 1) * sw - 4
        base_c = np.array([176, 146, 92]) * (0.92 + 0.08 * math.sin(i * 2.3))
        d.rounded_rectangle([xa, y0, xb, y1], 10, fill=tuple(int(v) for v in base_c) + (255,), outline=(110, 84, 46, 255), width=2)
        for k in range(0, 860, 37):
            d.line([(xa + 6, y0 + k + (i * 13) % 30), (xb - 6, y0 + k + (i * 13) % 30 + 2)], fill=(150, 120, 74, 90), width=1)
    for yy in (y0 + 120, y1 - 120):
        d.line([(x0 - 20, yy), (x1 + 20, yy)], fill=(90, 60, 30, 255), width=6)
    return im


@functools.lru_cache(maxsize=2)
def slip_static():
    b = dark_bg(15, top=(20, 16, 12)).copy()
    b.alpha_composite(slip_board())
    return b


def vcol(text, size, col):
    f = font(SERIF_B, size)
    im = Image.new("RGBA", (size + 20, int(len(text) * size * 1.12) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, c in enumerate(text):
        d.text((10, 10 + i * size * 1.12), c, font=f, fill=col)
    return im


@visual("slips")
class Slips:
    def static(self, p):
        return slip_static()

    def dyn(self, base, tl, dur, p, ev):
        mode = p.get("mode", "blank")
        ink = (30, 18, 10, 255)
        if mode == "blank":
            g = 0.5 + 0.5 * math.sin(tl * 2)
            hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(hl).rectangle([140, 390, 940, 1250], outline=GOLD + (int(120 + 100 * g),), width=6)
            base.alpha_composite(hl.filter(ImageFilter.GaussianBlur(6)))
            q = text_img("评", sc_font(KAI, 260), (90, 60, 30, 110))
            paste_c(base, q, 540, 820, 0.6)
            return
        # columns: v1 at slips 6,7 (right side, read right->left), v2 at slips 1,2
        cols1 = ["子治世之能臣", "亂世之姦雄"]
        cols2 = ["君清平之姦賊", "亂世之英雄"]
        sw = 100
        def put(cols, xs, a, slide):
            for j, ctext in enumerate(cols):
                im = vcol(ctext, 74, ink)
                paste(base, im, xs[j] - im.width / 2 + slide, 470, a)
        if mode in ("v1", "both", "cross"):
            a = ease((tl - 0.2) / 0.8) if mode == "v1" else 1.0
            slide = -160 * (1 - ease_out((tl - 0.2) / 0.8)) if mode == "v1" else 0
            put(cols1, [140 + 7.5 * sw, 140 + 6.5 * sw] if mode != "v1" else [140 + 4.5 * sw, 140 + 3.5 * sw], a, slide)
            if mode != "v1":
                tg = pill("《异同杂语》", (30, 18, 10), GOLD + (255,), size=30); paste_c(base, tg, 140 + 7 * sw, 1310)
            else:
                tg = pill("裴注引孙盛《异同杂语》", (30, 18, 10), GOLD + (255,), size=30); paste_c(base, tg, 540, 1310, a)
        if mode in ("both", "cross"):
            a = ease((tl - 0.2) / 0.8) if mode == "both" else 1.0
            slide = 160 * (1 - ease_out((tl - 0.2) / 0.8)) if mode == "both" else 0
            put(cols2, [140 + 1.5 * sw, 140 + 0.5 * sw], a, slide)
            tg = pill("《后汉书》", (20, 20, 24), (170, 196, 214, 255), size=30); paste_c(base, tg, 140 + 1 * sw, 1310, a)
        if mode == "cross":
            k = ease((tl - 0.3) / 0.8)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            ys = lambda i: 470 + 10 + i * 74 * 1.12
            # highlight 能臣 (v1 col0 idx4-5) vs 姦賊 (v2 col0 idx4-5); 姦雄 vs 英雄 (col1 idx3-4)
            boxes = [((140 + 7.5 * sw), 4, 2, (210, 70, 60)), ((140 + 1.5 * sw), 4, 2, (210, 70, 60)),
                     ((140 + 6.5 * sw), 3, 2, (60, 120, 200)), ((140 + 0.5 * sw), 3, 2, (60, 120, 200))]
            for (cx, i0, n, c) in boxes:
                d.rounded_rectangle([cx - 52, ys(i0) - 6, cx + 52, ys(i0 + n) - 4], 10, outline=c + (int(255 * k),), width=6)
            d.line([(140 + 7.5 * sw - 52, ys(5)), (140 + 1.5 * sw + 52, ys(5))], fill=(210, 70, 60, int(200 * k)), width=4)
            d.line([(140 + 6.5 * sw - 52, ys(4)), (140 + 0.5 * sw + 52, ys(4))], fill=(60, 120, 200, int(200 * k)), width=4)
            base.alpha_composite(lay)
            lab = text_img("太平：能臣 ↔ 奸贼　　乱世：奸雄 ↔ 英雄", sc_font(SANS_B, 40), IVORY)
            paste_c(base, lab, 540, 1390, k)


# ------------------------------------------------------------------ two rivers
def river_y(x, cy, t, ph):
    return cy + 46 * math.sin(x / 170 + ph) + 14 * math.sin(x / 61 + t * 0.4 + ph)


@functools.lru_cache(maxsize=2)
def rivers_static():
    b = dark_bg(16, top=(14, 14, 22)).copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for cy, col, ph in ((620, (200, 206, 220), 0.0), (1100, (110, 60, 140), 1.7)):
        pts = [(x, river_y(x, cy, 0, ph)) for x in range(-20, W + 40, 20)]
        d.line(pts, fill=col + (90,), width=170, joint="curve")
        d.line(pts, fill=col + (60,), width=110, joint="curve")
    b.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))
    t1 = glow(text_img("清流 · 士大夫", sc_font(KAI, 62), WHITE), 12, 1.0)
    t2 = glow(text_img("浊流 · 宦官", sc_font(KAI, 62), PURPLE_L), 12, 1.0)
    b.alpha_composite(t1, (540 - t1.width // 2, 430))
    b.alpha_composite(t2, (540 - t2.width // 2, 1240))
    return b


@visual("rivers")
class Rivers:
    def static(self, p):
        return rivers_static()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        rng = np.random.default_rng(4)
        for cy, col, ph, sp in ((620, (236, 238, 245), 0.0, 60), (1100, (170, 110, 210), 1.7, 46)):
            n = 110
            x0 = rng.uniform(0, W, n); off = rng.uniform(-55, 55, n); sz = rng.uniform(2, 5, n); v = rng.uniform(0.7, 1.3, n)
            for i in range(n):
                x = (x0[i] + sp * v[i] * tl) % (W + 40) - 20
                y = river_y(x, cy, tl, ph) + off[i]
                r = sz[i]
                d.line([(x - 10 * v[i], y), (x, y)], fill=col + (150,), width=int(r))
        mode = p.get("cao", "none")
        if mode == "none":
            return
        if mode == "in":
            x = 540 + 30 * math.sin(tl * 0.7); y = river_y(x, 1100, tl, 1.7)
        elif mode == "out":
            x = 540 + 30 * math.sin(tl * 0.7); y = river_y(x, 620, tl, 0.0)
        else:  # cross
            k = ease((tl - p.get("t0", 0.4)) / p.get("dur", 3.0))
            x = 540 + 120 * math.sin(k * math.pi)
            y = (1 - k) * river_y(x, 1100, tl, 1.7) + k * river_y(x, 620, tl, 0.0)
            for j in range(1, 14):          # trail
                kk = max(0, k - j * 0.025)
                xx = 540 + 120 * math.sin(kk * math.pi)
                yy = (1 - kk) * river_y(xx, 1100, tl, 1.7) + kk * river_y(xx, 620, tl, 0.0)
                rr = 16 - j
                d.ellipse([xx - rr, yy - rr, xx + rr, yy + rr], fill=GOLD + (int(150 - 10 * j),))
        dot = cao_dot()
        paste_c(base, dot, x, y)
        lab = text_img("曹操", sc_font(KAI, 46), GOLD_L, stroke=3, stroke_fill=(0, 0, 0))
        paste_c(base, lab, x + 90, y - 10)


@functools.lru_cache(maxsize=1)
def cao_dot():
    im = Image.new("RGBA", (120, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([38, 38, 82, 82], fill=CAO + (255,), outline=GOLD + (255,), width=6)
    return glow(im, 14, 2.0)


# ------------------------------------------------------------------ 党锢 prison
@visual("prison")
class Prison:
    def static(self, p):
        b = dark_bg(17, top=(14, 12, 16)).copy()
        return b

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        rng = np.random.default_rng(11)
        n = 104; cols = 13
        order = rng.permutation(n)
        k = clamp01((tl - 0.6) / max(1.0, dur - 1.6))
        gone = int(k * n)
        for i in range(n):
            r_, c_ = divmod(i, cols)
            x = 150 + c_ * 65; y = 520 + r_ * 85
            dead = np.where(order == i)[0][0] < gone
            col = (90, 86, 84, 255) if dead else (236, 232, 222, 255)
            d.ellipse([x - 12, y - 30, x + 12, y - 6], fill=col)
            d.rounded_rectangle([x - 18, y - 4, x + 18, y + 34], 8, fill=col)
        for x in range(110, 1000, 74):     # bars
            d.rectangle([x, 420, x + 14, 1260], fill=(46, 44, 50, 255), outline=(90, 86, 96, 255))
        d.rectangle([90, 410, 1000, 432], fill=(60, 56, 62, 255)); d.rectangle([90, 1250, 1000, 1272], fill=(60, 56, 62, 255))
        y1 = text_img("公元169年 · 第二次党锢之祸", sc_font(SERIF_B, 46), IVORY); paste_c(base, y1, 540, 340, ease(tl / 0.5))
        c = text_img(f"死于狱中：{gone} / 百余人", sc_font(SANS_B, 44), (230, 150, 130)); paste_c(base, c, 540, 1340, ease((tl - 0.6) / 0.4))


# ------------------------------------------------------------------ 察举 pyramid
@visual("pyramid")
class Pyramid:
    def static(self, p):
        return dark_bg(18).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        cols, rows = 20, 10
        k = ease((tl - 0.2) / 1.2)
        for i in range(int(cols * rows * k)):
            r_, c_ = divmod(i, cols)
            x = 120 + c_ * 44; y = 820 + r_ * 44
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(150, 150, 160, 220))
        t1 = text_img("每个点 = 一千人　共二十万口", sc_font(SANS_R, 36), (200, 200, 206)); paste_c(base, t1, 540, 1310, k)
        k2 = ease_out((tl - 1.6) / 1.0)
        if k2 > 0:
            x = 120 + 9 * 44; y0 = 820 + 4 * 44
            y = y0 + (520 - y0) * k2
            g = cao_dot(); paste_c(base, g, x + (540 - x) * k2, y)
            lab = text_img("孝廉 × 1 / 年", sc_font(KAI, 64), GOLD_L); paste_c(base, lab, 540, 420, k2)
        t0 = text_img("察举：郡国按人口荐举", sc_font(SERIF_B, 50), IVORY); paste_c(base, t0, 540, 300, ease(tl / 0.5))


# ------------------------------------------------------------------ chain: 名士品评→名声→察举→做官
@visual("chain")
class Chain:
    def static(self, p):
        return dark_bg(19).copy()

    def dyn(self, base, tl, dur, p, ev):
        items = ["名士品评", "名声", "察举（孝廉）", "做官"]
        d = ImageDraw.Draw(base)
        hl = p.get("hl", -1)
        for i, s in enumerate(items):
            a = ease_out((tl - 0.35 * i) / 0.4)
            if a <= 0: continue
            y = 400 + i * 240
            on = (i == hl) or (hl == -1)
            col = GOLD if on else (110, 110, 116)
            box = rrect((560, 150), 20, (12, 12, 14, 235), outline=col + (255,), width=4)
            paste_c(base, box, 540, y, a)
            tx = text_img(s, sc_font(KAI, 66), GOLD_L if on else (170, 170, 176))
            if i == hl:
                tx = glow(tx, 16, 1.0 + 0.5 * math.sin(tl * 4) ** 2)
            paste_c(base, tx, 540, y, a)
            if i < 3:
                d.line([(540, y + 80), (540, y + 160)], fill=col + (int(220 * a),), width=6)
                d.polygon([(524, y + 150), (556, y + 150), (540, y + 170)], fill=col + (int(220 * a),))
        if p.get("stamp"):
            k = clamp01((tl - 1.6) / 0.25)
            if k > 0:
                st = stamp_img(p["stamp"])
                s = 1.6 - 0.6 * k
                im = st.resize((int(st.width * s), int(st.height * s)))
                paste_c(base, im, 860, 400, k)


@functools.lru_cache(maxsize=4)
def stamp_img(t):
    im = Image.new("RGBA", (220, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 210, 210], 18, outline=(200, 40, 30, 255), width=10)
    f = sc_font(KAI, 80)
    for i, c in enumerate(t[:4]):
        r_, c_ = divmod(i, 2)
        d.text((118 - c_ * 92, 22 + r_ * 92), c, font=f, fill=(200, 40, 30, 255))
    return im.rotate(-8, expand=True, resample=Image.BICUBIC)


# ------------------------------------------------------------------ 桥玄 seal
@visual("seal")
class Seal:
    def static(self, p):
        b = dark_bg(20, top=(20, 16, 12)).copy()
        pap = rrect((760, 900), 10, (196, 178, 140, 255))
        b.alpha_composite(pap, (160, 380))
        return b

    def dyn(self, base, tl, dur, p, ev):
        t = text_img(p.get("text", "命世之才"), font(KAI, 120), (30, 20, 12))
        # vertical layout
        txt = p.get("text", "命世之才")
        for i, c in enumerate(txt):
            ci = text_img(c, sc_font(KAI, 130), (30, 20, 12))
            paste_c(base, ci, 600, 520 + i * 150, ease((tl - 0.2 * i) / 0.4))
        k = clamp01((tl - 1.2) / 0.22)
        if k > 0:
            st = stamp_img(p.get("who", "桥玄之印"))
            s = 1.8 - 0.8 * k
            im = st.resize((int(st.width * s), int(st.height * s)))
            paste_c(base, im, 330, 1060, k)
        lab = text_img(p.get("cap", "桥玄：前太尉，「世名知人」"), sc_font(SANS_R, 36), IVORY, maxw=900, align="center")
        paste_c(base, lab, 540, 1340, ease((tl - 0.4) / 0.5))


# ------------------------------------------------------------------ authors timeline
@visual("authors")
class Authors:
    def static(self, p):
        return dark_bg(21).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        Y0, Y1 = 150, 470
        X = lambda yr: 120 + (yr - Y0) / (Y1 - Y0) * 840
        k = ease(tl / 0.8)
        d.line([(X(Y0), 900), (X(Y0) + (X(Y1) - X(Y0)) * k, 900)], fill=(170, 170, 176, 255), width=4)
        for yr in range(150, 471, 50):
            if X(yr) <= X(Y0) + (X(Y1) - X(Y0)) * k:
                d.line([(X(yr), 890), (X(yr), 910)], fill=(170, 170, 176, 255), width=3)
                ty = text_img(f"{yr}", sc_font(SANS_R, 28), (170, 170, 176)); paste_c(base, ty, X(yr), 940)
        ev_ = [(170, 175, "求评", "曹操见许劭\n约170年代", GOLD, 0.6),
               (302, 373, "孙盛", "东晋\n《异同杂语》", (214, 160, 110), 1.2),
               (398, 445, "范晔", "南朝宋\n《后汉书》", (150, 180, 200), 1.8)]
        for (a_, b_, nm, sub, col, t0) in ev_:
            a = ease_out((tl - t0) / 0.5)
            if a <= 0: continue
            up = nm == "求评"
            y = 760 if not up else 1040
            d.rounded_rectangle([X(a_) - 4, 880, X(b_) + 4, 920], 8, fill=col + (int(255 * a),))
            box = text_img(nm, sc_font(KAI, 56), col); paste_c(base, box, (X(a_) + X(b_)) / 2, y - 40, a)
            sb = text_img(sub, sc_font(SANS_R, 30), (210, 210, 214), align="center"); paste_c(base, sb, (X(a_) + X(b_)) / 2, y + 40, a)
        cap = text_img("记录者都比事件晚一百多年，材料来源不同", sc_font(SERIF_B, 42), IVORY, maxw=900, align="center")
        paste_c(base, cap, 540, 1260, ease((tl - 2.4) / 0.5))


# ------------------------------------------------------------------ balance (costly signal)
@visual("balance")
class Balance:
    def static(self, p):
        return dark_bg(22).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        cx, cy = 540, 640
        L = ev.get("lines", [])
        # tilt: starts left-heavy (cost), then right side lifts into balance as credibility accrues
        k = ease((tl - (L[3][0] if len(L) > 3 else dur * 0.6)) / 2.0)
        ang = math.radians(-14 + 14 * k)
        dx, dy = 380 * math.cos(ang), 380 * math.sin(ang)
        d.polygon([(cx - 70, 1340), (cx + 70, 1340), (cx + 14, cy), (cx - 14, cy)], fill=(120, 100, 60, 255))
        d.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=GOLD + (255,), width=14)
        d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=GOLD_L + (255,))
        for side, (px, py), col, items in ((-1, (cx - dx, cy - dy), PURPLE_L, ["蹇硕叔父的命", "宦官集团的报复", "丢官、丢命的风险"]),
                                         (1, (cx + dx, cy + dy), WHITE, ["清流的认可", "「不避豪强」的名声"])):
            d.line([(px, py), (px - 120, py + 260)], fill=(180, 160, 110, 255), width=3)
            d.line([(px, py), (px + 120, py + 260)], fill=(180, 160, 110, 255), width=3)
            d.chord([px - 170, py + 200, px + 170, py + 330], 0, 180, fill=(70, 60, 40, 255), outline=GOLD + (255,), width=3)
            for j, it in enumerate(items):
                a = ease_out((tl - 0.4 - 0.5 * j - (0 if side < 0 else 1.6)) / 0.4)
                ti = pill(it, col, (14, 14, 18, 230), size=30, outline=col + (200,))
                paste_c(base, ti, px, py + 180 - j * 64, a)
        cap = text_img("昂贵信号（costly signal）", sc_font(SERIF_B, 50), GOLD_L); paste_c(base, cap, 540, 330, ease(tl / 0.5))
        c2 = text_img("Spence, 1973 · 只借用机制", sc_font(SANS_R, 30), (180, 180, 186)); paste_c(base, c2, 540, 400, ease(tl / 0.5))
        c3 = text_img("代价越高，信号越可信", sc_font(KAI, 56), IVORY); paste_c(base, c3, 540, 1420 - 60, ease((tl - 3.0) / 0.5))


# ------------------------------------------------------------------ map
LON0, LON1, LAT0, LAT1 = 110.6, 120.2, 31.6, 38.3
MX0, MY0, PXD, PYD = 60, 330, 100.0, 122.0


def P(lon, lat):
    return (MX0 + (lon - LON0) * PXD, MY0 + (LAT1 - lat) * PYD)


PLACES = {"洛阳": (112.62, 34.72), "谯县": (115.78, 33.85), "汝南": (114.62, 32.96), "颍川": (113.47, 34.15),
          "顿丘": (115.0, 35.85), "济南": (117.35, 36.72), "陈留": (114.55, 34.72), "沛国": (116.8, 33.95)}
RIVERS = {
    "黄河": [(110.6, 34.62), (111.3, 34.75), (112.0, 34.85), (112.8, 34.92), (113.6, 34.95), (114.2, 35.25), (114.9, 35.75),
           (115.6, 36.3), (116.3, 36.9), (117.0, 37.35), (117.8, 37.65), (118.6, 37.85), (119.0, 37.92)],
    "淮河": [(113.2, 32.4), (114.0, 32.45), (114.8, 32.4), (115.6, 32.55), (116.4, 32.75), (117.2, 32.95), (118.0, 33.1),
           (118.7, 33.35), (119.4, 33.75), (120.2, 34.05)],
    "洛水": [(111.3, 34.38), (111.9, 34.55), (112.62, 34.67), (113.05, 34.78)],
    "颍水": [(113.0, 34.42), (113.6, 34.02), (114.3, 33.6), (115.3, 33.12), (116.3, 32.75)],
    "济水": [(113.6, 35.0), (114.6, 35.1), (115.5, 35.45), (116.4, 36.2), (117.2, 36.8), (118.2, 37.35)],
}
REGIONS = {"司隶": (111.6, 35.4), "豫州": (114.6, 33.4), "兖州": (115.9, 35.2), "冀州": (115.6, 37.7), "青州": (118.4, 36.4), "徐州": (118.4, 34.3)}


@functools.lru_cache(maxsize=2)
def map_static():
    b = parchment_dark(5)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sea = [P(117.9, 38.3), P(118.6, 37.95), P(119.2, 37.3), P(120.2, 37.05), P(120.2, 38.3)]
    d.polygon(sea, fill=(28, 40, 52, 255))
    d.polygon([P(120.2, 34.8), P(119.9, 34.5), P(120.0, 33.9), P(120.2, 33.4)], fill=(28, 40, 52, 255))
    for nm, pts in RIVERS.items():
        w = 9 if nm in ("黄河", "淮河") else 4
        d.line([P(*q) for q in pts], fill=(70, 100, 120, 255), width=w, joint="curve")
    for nm, (lo, la) in REGIONS.items():
        t = text_img(nm, sc_font(SERIF_B, 52), (120, 104, 78))
        x, y = P(lo, la); lay.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))
    for nm in ("黄河", "淮河"):
        q = RIVERS[nm][len(RIVERS[nm]) // 2 + (2 if nm == "黄河" else 0)]
        t = text_img(nm, sc_font(KAI, 36), (110, 140, 160)); x, y = P(*q); lay.alpha_composite(t, (int(x + 10), int(y + 8)))
    b.alpha_composite(lay)
    d = ImageDraw.Draw(b)
    d.rectangle([MX0 - 10, MY0 - 10, W - MX0 + 10, P(0, LAT0)[1] + 10], outline=(140, 120, 84, 255), width=3)
    tt = text_img("东汉中原（示意）", sc_font(SERIF_R, 30), (170, 150, 110)); b.alpha_composite(tt, (MX0 + 10, MY0 + 6))
    return b


@functools.lru_cache(maxsize=32)
def place_lbl(nm, col):
    return text_img(nm, sc_font(KAI, 50), col, stroke=4, stroke_fill=(20, 16, 10))


def route(d, a, b, k, col, width=8, dashed=False, bend=0.18):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2 - (y1 - y0) * bend, (y0 + y1) / 2 + (x1 - x0) * bend
    pts = []
    N = 60
    for i in range(int(N * k) + 1):
        u = i / N
        pts.append(((1 - u) ** 2 * x0 + 2 * u * (1 - u) * mx + u * u * x1, (1 - u) ** 2 * y0 + 2 * u * (1 - u) * my + u * u * y1))
    if len(pts) < 2: return
    if dashed:
        for i in range(0, len(pts) - 1, 2):
            d.line(pts[i:i + 2], fill=col, width=width)
    else:
        d.line(pts, fill=col, width=width, joint="curve")
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    if k > 0.98:
        s = width * 3.2
        d.polygon([(xb + s * math.cos(ang), yb + s * math.sin(ang)),
                   (xb + s * 0.8 * math.cos(ang + 2.4), yb + s * 0.8 * math.sin(ang + 2.4)),
                   (xb + s * 0.8 * math.cos(ang - 2.4), yb + s * 0.8 * math.sin(ang - 2.4))], fill=col)


@visual("map", tag="地图示意")
class Map:
    def static(self, p):
        return map_static()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        for (a, b, col, lab, dashed, t0) in p.get("routes", []):
            k = ease((tl - t0) / 1.6)
            if k <= 0: continue
            pa, pb = P(*PLACES[a]), P(*PLACES[b])
            route(d, pa, pb, k, col + (255,), width=12, dashed=dashed)
            if lab and k > 0.6:
                mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
                li = pill(lab, col, (10, 10, 10, 220), size=32, outline=col + (255,))
                paste_c(base, li, mx + p.get("lab_dx", 0), my + p.get("lab_dy", -70), ease((k - 0.6) / 0.4))
        for nm in p.get("places", []):
            col = p.get("cols", {}).get(nm, IVORY)
            x, y = P(*PLACES[nm])
            pulse = 0.5 + 0.5 * math.sin(tl * 3)
            hot = nm in p.get("hot", [])
            r = 12 + (8 * pulse if hot else 0)
            d.ellipse([x - r - 10, y - r - 10, x + r + 10, y + r + 10], outline=col + (int(120 * (1 - pulse)) if hot else 0,), width=4)
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=col + (255,), outline=(20, 16, 10, 255), width=3)
            lb = place_lbl(nm if nm != "沛国" else "沛国", col)
            dx, dy = p.get("off", {}).get(nm, (0, -58))
            paste_c(base, lb, x + dx, y + dy)
        for (txt, lo, la, col, t0) in p.get("notes", []):
            x, y = P(lo, la)
            ni = text_img(txt, sc_font(SANS_B, 32), col, maxw=520, stroke=3, stroke_fill=(10, 10, 10), align="center")
            paste_c(base, ni, x, y, ease((tl - t0) / 0.5))


# ------------------------------------------------------------------ Luoyang city plan
@functools.lru_cache(maxsize=1)
def luoyang_static():
    b = parchment_dark(8)
    d = ImageDraw.Draw(b)
    x0, y0, x1, y1 = 290, 380, 790, 1240       # 城垣（南北长、东西窄，示意）
    d.rectangle([x0, y0, x1, y1], outline=(200, 180, 130, 255), width=8)
    d.rectangle([380, 450, 700, 700], outline=(170, 150, 110, 255), width=4)   # 北宫
    d.rectangle([400, 900, 680, 1120], outline=(170, 150, 110, 255), width=4)  # 南宫
    for (t, x, y) in (("北宫", 540, 575), ("南宫", 540, 1010)):
        im = text_img(t, sc_font(KAI, 54), (190, 170, 124)); b.alpha_composite(im, (x - im.width // 2, y - im.height // 2))
    d.line([(150, 1320), (400, 1300), (700, 1310), (940, 1290)], fill=(70, 100, 120, 255), width=10)
    lo = text_img("洛水", sc_font(KAI, 40), (110, 140, 160)); b.alpha_composite(lo, (820, 1320))
    for (gx, gy) in ((x0, 560), (x0, 900), (x1, 560), (x1, 900), (450, y0), (630, y0), (420, y1), (660, y1)):
        d.rectangle([gx - 14, gy - 14, gx + 14, gy + 14], fill=(200, 180, 130, 255))
    tt = text_img("东汉洛阳城（示意）", sc_font(SERIF_B, 46), (210, 190, 140)); b.alpha_composite(tt, (540 - tt.width // 2, 290))
    return b


@visual("luoyang", tag="地图示意")
class Luoyang:
    def static(self, p):
        return luoyang_static()

    def dyn(self, base, tl, dur, p, ev):
        k = ease((tl - 0.5) / 0.8)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        pulse = 0.6 + 0.4 * math.sin(tl * 3)
        d.rectangle([296, 386, 784, 760], fill=GOLD + (int(60 * k * pulse),), outline=GOLD + (int(230 * k),), width=5)
        for x in range(296, 784, 28):
            d.line([(x, 386), (x + 60, 446)], fill=GOLD + (int(50 * k),), width=2)
        base.alpha_composite(lay)
        lb = pill("北部尉辖区（示意）", (20, 16, 10), GOLD + (255,), size=34); paste_c(base, lb, 540, 790, k)
        # night patrol lantern dot
        if k > 0.5:
            u = (tl * 0.08) % 1.0
            per = [(300, 400), (780, 400), (780, 750), (300, 750)]
            seg = u * 4; i = int(seg) % 4; f = seg - int(seg)
            (ax, ay), (bx, by) = per[i], per[(i + 1) % 4]
            x, y = ax + (bx - ax) * f, ay + (by - ay) * f
            paste(base, lantern_glow().resize((240, 240)), x - 120, y - 120, 0.9)


# ------------------------------------------------------------------ career timeline
CAREER = [("约174年", "洛阳北部尉", "五色棒"), ("", "顿丘令", "明升暗调"), ("", "议郎", ""), ("184年", "骑都尉", "讨颍川黄巾"),
          ("", "济南相", "奏免其八"), ("", "称病还乡", "谯东五十里精舍"), ("188年", "典军校尉", "西园八校尉之一")]


@visual("career")
class Career:
    def static(self, p):
        return dark_bg(23).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        hl = p.get("hl", 0)
        L = ev.get("lines", [])
        # progress through nodes as lines advance
        li = line_idx(tl, ev)
        upto = p.get("upto", [0, 3, 4, 4, 5, 5, 6])
        reach = upto[min(max(li, 0), len(upto) - 1)] if upto else 6
        top, step = 350, 150
        d.line([(300, top), (300, top + step * 6)], fill=(90, 90, 96, 255), width=6)
        for i, (yr, post, note) in enumerate(CAREER):
            y = top + i * step
            on = i <= reach
            a = ease((tl - 0.12 * i) / 0.4)
            col = GOLD if on else (100, 100, 106)
            d.ellipse([300 - 20, y - 20, 300 + 20, y + 20], fill=(CAO if on else (40, 40, 44)) + (255,), outline=col + (int(255 * a),), width=5)
            if yr:
                ty = text_img(yr, sc_font(SANS_B, 32), col); paste(base, ty, 250 - ty.width, y - 22, a)
            pi = text_img(post, sc_font(KAI, 56), GOLD_L if on else (140, 140, 146)); paste(base, pi, 345, y - 40, a)
            if note:
                ni = text_img(note, sc_font(SANS_R, 30), (210, 200, 180) if on else (120, 120, 126)); paste(base, ni, 360 + pi.width, y - 18, a)
        if reach >= 0:
            y = top + reach * step
            paste_c(base, cao_dot(), 300, y)


# ------------------------------------------------------------------ 西园八校尉
@visual("org")
class Org:
    def static(self, p):
        return dark_bg(24).copy()

    def dyn(self, base, tl, dur, p, ev):
        d = ImageDraw.Draw(base)
        hl = p.get("hl", "cao")
        t0 = text_img("公元188年 · 西园八校尉", sc_font(SERIF_B, 50), IVORY); paste_c(base, t0, 540, 330, ease(tl / 0.5))
        k = ease_out((tl - 0.3) / 0.5)
        box = rrect((560, 190), 20, (40, 20, 54, 240), outline=PURPLE_L + (255,), width=4); paste_c(base, box, 540, 530, k)
        n = text_img("蹇硕", sc_font(KAI, 76), (236, 220, 250)); paste_c(base, n, 540, 500, k)
        s = text_img("上军校尉 · 统领八校", sc_font(SANS_R, 32), (210, 190, 225)); paste_c(base, s, 540, 580, k)
        s2 = text_img("「雖大將軍亦領屬焉」", sc_font(SERIF_R, 30), (200, 180, 215)); paste_c(base, s2, 540, 660, k)
        others = [("袁绍", "中军", YUAN), ("鲍鸿", "下军", GREY), ("曹操", "典军", GOLD), ("赵融", "助军左", GREY),
                  ("冯芳", "助军右", GREY), ("夏牟", "左", GREY), ("淳于琼", "右", GREY)]
        for i, (nm, pos, col) in enumerate(others):
            r_, c_ = divmod(i, 4)
            x = 180 + c_ * 240 + (120 if r_ else 0); y = 900 + r_ * 260
            a = ease_out((tl - 0.8 - 0.12 * i) / 0.4)
            d.line([(540, 625), (x, y - 90)], fill=(110, 90, 130, int(150 * a)), width=3)
            on = (nm == "曹操" and hl in ("cao", "both")) or (nm == "袁绍" and hl in ("yuan", "both"))
            bx = rrect((200, 170), 16, (14, 14, 16, 240), outline=(col if on else (90, 90, 96)) + (255,), width=5 if on else 2)
            paste_c(base, bx, x, y, a)
            ni = text_img(nm, sc_font(KAI, 56 if len(nm) < 3 else 46), col if on else (170, 170, 176))
            if on: ni = glow(ni, 12, 1.0 + 0.5 * math.sin(tl * 4) ** 2)
            paste_c(base, ni, x, y - 20, a)
            pi = text_img(pos + "校尉", sc_font(SANS_R, 28), (200, 200, 204)); paste_c(base, pi, x, y + 48, a)
        src = text_img("据《后汉书·何进传》《灵帝纪》注引《山阳公载记》", sc_font(SANS_R, 28), (170, 170, 176)); paste_c(base, src, 540, 1330, ease((tl - 1.5) / 0.5))


# ------------------------------------------------------------------ stele
@functools.lru_cache(maxsize=1)
def stele_static():
    b = dark_bg(25, top=(16, 18, 22)).copy()
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([330, 330, 750, 1300], 60, fill=(84, 84, 88, 255), outline=(120, 120, 126, 255), width=6)
    n = noise_tex(420, 970, 3, scale=10)
    tex = Image.fromarray((n * 60).astype(np.uint8)).convert("L")
    lay = Image.new("RGBA", (420, 970), (40, 40, 44, 0)); lay.putalpha(tex)
    b.alpha_composite(lay, (330, 330))
    d.rectangle([280, 1300, 800, 1380], fill=(60, 60, 64, 255))
    return b


@visual("stele")
class Stele:
    def static(self, p):
        return stele_static()

    def dyn(self, base, tl, dur, p, ev):
        txt = "漢故征西將軍曹侯之墓"
        for i, c in enumerate(txt):
            a = ease((tl - 0.3 - 0.18 * i) / 0.4)
            ci = text_img(c, font(SERIF_B, 78), (26, 26, 28))
            hi = text_img(c, font(SERIF_B, 78), (150, 150, 156))
            paste_c(base, hi, 541, 420 + i * 86 + 2, a)
            paste_c(base, ci, 540, 420 + i * 86, a)
        dust(base, tl, n=40, seed=12, col=(200, 200, 210), amax=80)


# ------------------------------------------------------------------ book (演义)
@functools.lru_cache(maxsize=1)
def book_static():
    b = dark_bg(26, top=(22, 14, 12)).copy()
    d = ImageDraw.Draw(b)
    for side in (0, 1):
        x0 = 110 if side == 0 else 545
        d.rectangle([x0, 330, x0 + 425, 1300], fill=(70, 58, 42, 255), outline=(110, 90, 60, 255), width=3)
        for k in range(10):
            x = x0 + 30 + k * 40
            d.line([(x, 380), (x, 1250)], fill=(90, 74, 52, 255), width=2)
    t = text_img("三國演義", sc_font(KAI, 96), (120, 96, 66)); b.alpha_composite(t, (540 - t.width // 2, 360))
    return b


@visual("book")
class Book:
    def static(self, p):
        return book_static()

    def dyn(self, base, tl, dur, p, ev):
        dust(base, tl, n=30, seed=14, amax=90)


# ------------------------------------------------------------------ teaser
@visual("teaser", tag="地图示意")
class Teaser(Map):
    def dyn(self, base, tl, dur, p, ev):
        p = dict(places=["洛阳", "陈留", "谯县"], hot=["陈留"], cols={"陈留": GOLD, "洛阳": COLD},
                 routes=[("洛阳", "陈留", GOLD, "散家财，起兵", False, 0.4)],
                 off={"陈留": (0, 60)})
        super().dyn(base, tl, dur, p, ev)
        t = text_img("下一集", sc_font(KAI, 80), GOLD_L); paste_c(base, glow(t, 14, 1.2), 540, 1260, ease((tl - 0.3) / 0.5))
