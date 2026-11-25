# -*- coding: utf-8 -*-
"""Scene 2: from trading post to fortress."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
import maps
from maps import P_INDIA, P_BENGAL, PLACES

FORTS = [("madras", "Madras", "马德拉斯", "圣乔治堡 · 约1640", (30, 40)),
         ("bombay", "Bombay", "孟买", "1668 · 年租10英镑", (-200, -10)),
         ("calcutta", "Calcutta", "加尔各答", "1690 · 威廉堡", (-300, 70))]


def india_forts(img, g):
    img.alpha_composite(maps.india_map())
    T = g.T
    title_card(img, "三个据点", None, a=ramp(T, 0, 0.5) * (1 - g.r("madras", 1.5)), y=420, size=64)
    for cue, key, zh, sub, (dx, dy) in FORTS:
        if not g.seen(cue):
            continue
        a = g.r(cue, 0, 0.5)
        x, y = P_INDIA(*PLACES[key])
        lay = new(); d = ImageDraw.Draw(lay)
        sc = 1 + 0.8 * (1 - ease_out(min(1, g.ct(cue) / 0.4)))
        maps.fort_icon(d, x, y, 26 * sc)
        comp(img, glow(lay, 8), a)
        ax = x + dx if dx > 0 else x + dx
        anchor = "lm" if dx > 0 else "lm"
        label(img, (ax, y + dy - 30), zh, size=46, color=GOLD_L, a=a, anchor=anchor, fontspec=SERIF_B)
        label(img, (ax, y + dy + 26), sub, size=30, color=IVORY, a=a, anchor=anchor, box=(0, 0, 0, 170))
    schematic(img)


def factory(img, g):
    img.alpha_composite(bg_copy(tint=(40, 40, 30)))
    T = g.T
    lay = new(); d = ImageDraw.Draw(lay)
    # river/sea band
    d.rectangle((0, 1050, W, 1300), fill=(30, 52, 70, 255))
    for k in range(12):
        d.line((k * 100, 1100 + (k % 3) * 40, k * 100 + 60, 1100 + (k % 3) * 40), fill=(80, 110, 130, 255), width=3)
    # warehouses
    for i, (x, w_, h_) in enumerate([(100, 260, 220), (380, 300, 260), (700, 280, 200)]):
        d.rectangle((x, 1040 - h_, x + w_, 1040), fill=(160, 140, 110, 255))
        d.polygon([(x - 10, 1040 - h_), (x + w_ / 2, 1040 - h_ - 70), (x + w_ + 10, 1040 - h_)], fill=(110, 60, 40, 255))
        for k in range(3):
            d.rectangle((x + 30 + k * (w_ - 60) / 3, 1040 - h_ + 50, x + 60 + k * (w_ - 60) / 3, 1040 - h_ + 100), fill=(50, 40, 30, 255))
        d.rectangle((x + w_ / 2 - 30, 1040 - 90, x + w_ / 2 + 30, 1040), fill=(60, 44, 30, 255))
    d.rectangle((0, 1040, W, 1060), fill=(90, 80, 60, 255))
    ship(d, 820, 1180, 300)
    # bales
    for k in range(5):
        d.rounded_rectangle((420 + k * 46, 1000 - (k % 2) * 30, 460 + k * 46, 1040 - (k % 2) * 30), radius=6, fill=(210, 200, 170, 255))
    comp(img, lay, ramp(T, 0, 0.5))
    lay = new(); d = ImageDraw.Draw(lay)
    cannon(d, 120, 1030, 70, (30, 26, 22, 255), facing=1)
    cannon(d, 980, 1030, 70, (30, 26, 22, 255), facing=-1)
    comp(img, lay, ramp(T, 2.0, 0.5))
    for i, t_ in enumerate(["仓库", "码头", "账房", "几门炮"]):
        label(img, (180 + i * 240, 520), t_, size=44, color=GOLD_L, a=ramp(T, 0.4 + i * 0.5, 0.4), fontspec=SERIF_B, box=(0, 0, 0, 150))
    title_card(img, "商栈", "factory", a=ramp(T, 0, 0.5), y=400, size=72, sub_size=34)


MUGHAL_1707 = [(67.5, 24.5), (69, 29), (71.5, 34.5), (74.5, 35), (78, 31.5), (80.5, 29), (84, 27.5), (88, 26.8), (92, 25.5),
               (91.8, 22.5), (89, 21.8), (86.8, 21.2), (84, 18.5), (81, 15.5), (79.8, 13.5), (77.5, 12.5), (75.5, 13.5),
               (74, 16), (73, 19), (72.6, 21.5), (70, 22.5)]
REGIONS = [("孟加拉", (88.5, 23.6), (60, 140, 200)), ("奥德", (81.5, 27.0), (120, 170, 110)),
           ("马拉塔", (75.0, 19.5), (220, 130, 60)), ("海德拉巴", (78.6, 17.0), (170, 120, 200)),
           ("卡纳蒂克", (79.2, 12.6), (200, 90, 90))]


def mughal_break(img, g):
    img.alpha_composite(maps.india_map())
    T = g.T
    P = P_INDIA
    poly = P.pts(MUGHAL_1707)
    brk = g.r("mughal", 1.0, 2.0)
    lay = new(); d = ImageDraw.Draw(lay)
    d.polygon(poly, fill=GOLD + (int(80 * (1 - brk) + 20),), outline=GOLD + (230,))
    comp(img, lay, ramp(T, 0, 0.5))
    label(img, (P(78, 24)[0], P(78, 24)[1]), "莫卧儿帝国", size=54, color=GOLD_L, a=ramp(T, 0.2, 0.5) * (1 - brk), fontspec=SERIF_B)
    label(img, (W / 2, 1220), "1707 · 奥朗则布去世", size=40, color=IVORY, a=ramp(T, 0.4, 0.5) * (1 - g.r("chaos", 0)), box=(0, 0, 0, 170))
    if brk > 0:
        lay = new(); d = ImageDraw.Draw(lay)
        rng = np.random.default_rng(3)
        # crack lines
        for (a_, b_) in [((72, 25), (80, 21)), ((80, 21), (86.5, 22.5)), ((80, 21), (78, 15)), ((80, 21), (82, 27))]:
            pts = [P(a_[0] + (b_[0] - a_[0]) * k / 8 + rng.normal(0, 0.3), a_[1] + (b_[1] - a_[1]) * k / 8 + rng.normal(0, 0.3)) for k in range(9)]
            d.line(cut_polyline(pts, brk), fill=(240, 220, 180, 230), width=4)
        comp(img, lay)
        for i, (nm, ll, col) in enumerate(REGIONS):
            a = ramp(brk, 0.2 + i * 0.12, 0.3)
            x, y = P(*ll)
            l2 = new(); dd = ImageDraw.Draw(l2)
            dd.ellipse((x - 70, y - 70, x + 70, y + 70), fill=col + (90,))
            comp(img, l2.filter(ImageFilter.GaussianBlur(14)), a)
            label(img, (x, y), nm, size=38, color=WHITE, a=a, fontspec=SERIF_B)
    if g.seen("chaos"):
        c = g.ct("chaos")
        x0, y0 = P(64.5, 33.5); x1, y1 = P(*PLACES["Delhi"])
        comp(img, thick_arrow(bezier((x0, y0), (x0 + 120, y0 - 60), (x1, y1)), 30, RED_L, prog=ramp(c, 1.5, 1.2), glow_r=6))
        lay = new(); maps.marker(ImageDraw.Draw(lay), (x1, y1), 10, RED_L); comp(img, lay, ramp(c, 1.5, 0.4))
        label(img, (x1 - 10, y1 - 70), "1739 纳迪尔沙攻破德里", size=34, color=WHITE, a=ramp(c, 2.4, 0.5), box=(110, 20, 16, 210))
        mx, my = P(75.5, 20.5)
        for k, (dx, dy) in enumerate([(160, -140), (200, 60), (-20, 170)]):
            comp(img, thick_arrow(bezier((mx, my), (mx + dx * 0.4, my + dy * 0.2), (mx + dx, my + dy)), 18, (230, 150, 70), prog=ramp(c, 0.3 + k * 0.3, 0.8)))
    if g.seen("cost"):
        c = g.ct("cost")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 0, W, H), fill=(8, 10, 16, int(170 * ramp(c, 0, 0.5))))
        comp(img, lay)
        lay = new(); d = ImageDraw.Draw(lay)
        maps.fort_icon(d, 330, 760, 150)
        comp(img, lay, ramp(c, 0.2, 0.4))
        for k in range(int(min(8, c * 3))):
            lay = new(); coin(ImageDraw.Draw(lay), 650 + (k % 4) * 70, 860 - (k // 4) * 70 - (k % 2) * 10, 30); comp(img, lay)
        label(img, (W / 2, 1050), "保护生意，要花钱", size=56, color=GOLD_L, a=ramp(c, 0.5, 0.5), fontspec=SERIF_B)
        label(img, (W / 2, 1130), "加固要塞 · 多招兵", size=38, a=ramp(c, 1.0, 0.5), box=(0, 0, 0, 160))
    schematic(img)


def dupleix(img, g):
    img.alpha_composite(bg_copy(tint=(30, 30, 50)))
    T = g.T
    label(img, (W / 2, 360), "法国东印度公司 · 杜布雷", size=44, color=GOLD_L, a=ramp(T, 0, 0.5), fontspec=SERIF_B)
    # drilled sepoy block
    lay = new(); d = ImageDraw.Draw(lay)
    n = int(min(24, T * 8))
    for i in range(n):
        r, c = divmod(i, 6)
        soldier(d, 110 + c * 62 + r * 10, 640 + r * 70, 80, (200, 190, 170, 255))
    comp(img, lay)
    label(img, (300, 960), "招募印度士兵", size=36, a=ramp(T, 0.5, 0.4), box=(0, 0, 0, 160))
    label(img, (300, 1020), "欧式操练", size=36, a=ramp(T, 1.2, 0.4), box=(0, 0, 0, 160))
    # prince
    lay = new(); d = ImageDraw.Draw(lay)
    d.ellipse((650, 520, 970, 840), fill=(30, 36, 52, 255), outline=GOLD + (255,), width=3)
    person_bust(d, 810, 720, 220, (150, 120, 90, 255), hat="turban")
    comp(img, lay, ramp(T, 2.0, 0.5))
    label(img, (810, 900), "地方王公", size=40, color=GOLD_L, a=ramp(T, 2.0, 0.5), fontspec=SERIF_B)
    comp(img, thick_arrow(bezier((470, 700), (560, 620), (640, 680)), 28, GOLD, prog=ramp(T, 2.6, 0.8)))
    label(img, (560, 590), "出租", size=36, color=GOLD_L, a=ramp(T, 3.0, 0.4), fontspec=SERIF_B)
    if g.seen("land"):
        c = g.ct("land")
        comp(img, thick_arrow(bezier((700, 980), (560, 1100), (400, 1130)), 26, (120, 200, 120), prog=ramp(c, 0.2, 0.8)))
        lay = new(); d = ImageDraw.Draw(lay)
        # land parcel: fields
        for k in range(4):
            d.polygon([(180 + k * 60, 1110), (230 + k * 60, 1110), (210 + k * 60, 1190), (160 + k * 60, 1190)], fill=(90, 140, 70, 255) if k % 2 else (130, 160, 80, 255))
        comp(img, lay, ramp(c, 0.8, 0.4))
        label(img, (W / 2, 1260), "付不起现钱 → 划一片土地的税收抵账", size=36, color=WHITE, a=ramp(c, 1.0, 0.5), box=(20, 50, 20, 200))


def mech1(img, g):
    img.alpha_composite(bg_copy(tint=(60, 40, 10)))
    T = g.T
    mech_card(img, "保护贸易的武力成本", "出租武力的生意", ramp(T, 1.5, 2.5), a=ramp(T, 0, 0.5))
    label(img, (W / 2, 1150), "英国人很快学会了这一套", size=34, color=IVORY, a=ramp(T, 0, 0.5))


@functools.lru_cache(maxsize=1)
def _pass_doc():
    w, h = 520, 640
    im = parchment(w, h, seed=13).copy(); d = ImageDraw.Draw(im)
    d.text((w / 2, 90), "通行证", font=font(SERIF_B, 64), fill=(70, 40, 24, 255), anchor="mm")
    d.text((w / 2, 160), "dastak", font=font(EN_SERIF_I, 40), fill=(90, 60, 40, 255), anchor="mm")
    for k in range(6):
        d.line((70, 240 + k * 50, w - 70, 240 + k * 50), fill=(130, 100, 70, 200), width=3)
    d.text((w / 2, 560), "免缴关税", font=font(SERIF_B, 48), fill=(150, 30, 24, 255), anchor="mm")
    return im


def dastak(img, g):
    img.alpha_composite(bg_copy(tint=(50, 40, 20)))
    T = g.T
    doc = _pass_doc()
    x0 = (W - doc.size[0]) / 2 - 180 * g.r("private", 0, 0.8)
    comp(img, doc, ramp(T, 0, 0.5), (x0, 360 + 30 * (1 - ease_out(min(1, T / 0.6)))))
    if g.seen("dastak") and not g.seen("private"):
        stamp(img, "1717 敕令", (W / 2 + 160, 960), g.r("dastak", 1.0, 0.6), color=(170, 30, 24), size=56)
        label(img, (W / 2, 1180), "公司货物在孟加拉免税", size=40, color=GOLD_L, a=g.r("dastak", 1.6), box=(0, 0, 0, 170))
    if g.seen("private"):
        c = g.ct("private")
        # customs gate + flows
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((700, 420, 960, 470), fill=(120, 90, 60, 255))
        d.rectangle((715, 470, 745, 820), fill=(120, 90, 60, 255)); d.rectangle((915, 470, 945, 820), fill=(120, 90, 60, 255))
        d.text((830, 445), "孟加拉关卡", font=font(SANS_B, 30), fill=(250, 240, 220, 255), anchor="mm")
        comp(img, lay, ramp(c, 0, 0.4))
        # private goods bypass the gate
        comp(img, thick_arrow(bezier((560, 900), (830, 1000), (1000, 880)), 26, GOLD, prog=ramp(c, 0.6, 1.0)))
        label(img, (800, 1060), "职员私货 · 照样免税", size=34, color=GOLD_L, a=ramp(c, 1.2, 0.5), box=(0, 0, 0, 170))
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((720, 560, 940, 760), radius=14, outline=(150, 150, 150, 255), width=3)
        d.text((830, 660), "国库 ↓", font=font(SANS_B, 38), fill=(200, 200, 200, 255), anchor="mm")
        comp(img, lay, ramp(c, 2.0, 0.5))
        label(img, (W / 2, 1220), "薪水不高 · 私人生意 · 逃掉孟加拉的税", size=34, a=ramp(c, 2.5, 0.5), box=(0, 0, 0, 170))


def bengal_1756(img, g):
    img.alpha_composite(maps.bengal_map())
    T = g.T
    P = P_BENGAL
    lay = new(); d = ImageDraw.Draw(lay)
    for key in ("Calcutta", "Murshidabad"):
        maps.marker(d, P(*PLACES[key]), 11)
    comp(img, lay)
    cx, cy = P(*PLACES["Calcutta"]); mx, my = P(*PLACES["Murshidabad"])
    label(img, (cx + 24, cy + 4), "加尔各答", size=40, anchor="lm", fontspec=SERIF_B)
    label(img, (mx + 24, my), "穆尔希达巴德", size=36, anchor="lm")
    # portrait cards
    def card(x, y, name, sub, hat, col, a):
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((x - 170, y - 190, x + 170, y + 190), radius=20, fill=(16, 20, 30, 235), outline=tuple(col) + (255,), width=3)
        d.ellipse((x - 100, y - 160, x + 100, y + 40), fill=(36, 42, 58, 255))
        person_bust(d, x, y - 10, 170, tuple(col) + (255,), hat=hat)
        comp(img, lay, a)
        label(img, (x, y + 90), name, size=30 if len(name) > 7 else 38, color=WHITE, a=a, fontspec=SERIF_B)
        label(img, (x, y + 145), sub, size=28, color=tuple(col), a=a)
    if g.seen("siraj"):
        a = g.r("siraj") * (1 - 0.3 * g.r("clive"))
        card(260, 560, "西拉杰·乌德-达乌拉", "1756 继位 · 孟加拉纳瓦布", "turban", BLUE_L, a)
    if g.seen("fall"):
        c = g.ct("fall")
        comp(img, thick_arrow(bezier((mx, my + 20), (mx - 60, (my + cy) / 2), (cx - 10, cy - 24)), 34, BLUE, prog=ramp(c, 0.3, 1.4), glow_r=6))
        label(img, (cx - 40, cy + 80), "1756.6 攻下加尔各答", size=34, a=ramp(c, 1.6, 0.4), box=(20, 40, 90, 210))
    if g.seen("clive"):
        c = g.ct("clive")
        sx, sy = P(88.0, 21.5)
        comp(img, thick_arrow(bezier((sx, sy + 120), (sx + 80, sy), (cx + 6, cy + 30)), 34, RED, prog=ramp(c, 0.2, 1.4), glow_r=6))
        label(img, (cx + 70, cy + 170), "1757.1 克莱武夺回", size=34, a=ramp(c, 1.4, 0.4), anchor="lm", box=(110, 20, 16, 210))
    if g.seen("clive2"):
        a = g.r("clive2")
        card(800, 560, "罗伯特·克莱武", "公司文书 → 军官", "tricorn", RED_L, a)
    schematic(img)


GROUPS = {
    "india_forts": (india_forts, ["forts0", "madras", "bombay", "calcutta"]),
    "factory": (factory, ["factory"]),
    "mughal_break": (mughal_break, ["mughal", "chaos", "cost"]),
    "dupleix": (dupleix, ["dupleix", "land"]),
    "mech1": (mech1, ["mech1"]),
    "dastak": (dastak, ["dastak", "private"]),
    "bengal_1756": (bengal_1756, ["siraj", "fall", "clive", "clive2"]),
}
