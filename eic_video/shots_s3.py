# -*- coding: utf-8 -*-
"""Scene 3: Plassey — conspiracy, battle wargame, spoils."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
import maps
import shots_s0


def _card(img, x, y, name, sub, hat, col, a, w=300, h=360, name_size=36):
    if a <= 0:
        return
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), radius=20, fill=(16, 20, 30, 240), outline=tuple(col) + (255,), width=3)
    d.ellipse((x - 95, y - h / 2 + 30, x + 95, y - h / 2 + 220), fill=(36, 42, 58, 255))
    person_bust(d, x, y - h / 2 + 175, 160, tuple(col) + (255,), hat=hat)
    comp(img, lay, a)
    label(img, (x, y + h / 2 - 95), name, size=name_size, color=WHITE, a=a, fontspec=SERIF_B)
    label(img, (x, y + h / 2 - 45), sub, size=26, color=tuple(col), a=a)


def conspiracy(img, g):
    img.alpha_composite(bg_copy(tint=(40, 30, 50)))
    T = g.T
    _card(img, W / 2, 520, "西拉杰", "纳瓦布", "turban", BLUE_L, ramp(T, 0, 0.5))
    if g.seen("court"):
        label(img, (W / 2, 760), "宫廷里，不少人想换掉他", size=36, a=g.r("court", 0.6) * (1 - g.r("pact", 0)), box=(0, 0, 0, 170))
    _card(img, 250, 1000, "米尔·贾法尔", "掌管军饷的统帅", "turban", (190, 190, 190), g.r("jafar"), name_size=32)
    _card(img, 830, 1000, "贾加特·塞特", "孟加拉最大的银行家族", None, GOLD, g.r("seth"), name_size=32)
    if g.seen("seth"):
        lay = new(); d = ImageDraw.Draw(lay)
        for k in range(4):
            coin(d, 760 + k * 46, 1210, 20)
        comp(img, lay, g.r("seth", 0.5))
    if g.seen("pact"):
        c = g.ct("pact")
        # company card enters, lines connect
        _card(img, W / 2, 1000, "公司", "克莱武", "tricorn", RED_L, ramp(c, 0, 0.5), w=240, name_size=34)
        lay = new(); d = ImageDraw.Draw(lay)
        for (x0, y0) in ((400, 1000), (680, 1000)):
            dashed_line(d, [(x0, y0), (W / 2 + (-120 if x0 < W / 2 else 120), 1000)], GOLD + (255,), width=5, prog=ramp(c, 0.6, 0.8))
        comp(img, lay)
        stamp(img, "密约 1757.6", (W / 2, 760), ramp(c, 1.6, 0.6), color=(200, 50, 40), size=54)
        label(img, (W / 2, 1270), "扶他上位 ⇄ 巨额补偿", size=40, color=GOLD_L, a=ramp(c, 2.6, 0.5) * (1 - g.r("pact2", 0, 0.3)), box=(0, 0, 0, 180))
    if g.seen("pact2"):
        stamp(img, "账已算好一半", (W / 2, 1270), g.r("pact2", 0.3, 0.6), color=GOLD, size=64, angle=6)


# ------------------------------------------------------------------ the battle map

RIVER = [(-20, 300), (150, 380), (230, 520), (150, 640), (90, 760), (150, 880), (120, 1060), (60, 1200), (-20, 1320)]
GROVE = (190, 850, 470, 1080)
LODGE = (205, 740)
TANK = (520, 650)
COMPANY = [(250, 800), (320, 800), (390, 800), (460, 800), (530, 800)]
LOYAL = [(330, 470), (450, 450), (570, 440), (690, 450), (800, 480), (500, 610), (560, 600), (880, 560), (920, 660)]
MADAN = [(500, 610), (560, 600)]
JAFAR = [(900, 790), (870, 900), (810, 1000), (730, 1080), (640, 1130)]
CAMP = [(260, 400), (480, 370), (720, 365), (930, 400)]


@functools.lru_cache(maxsize=1)
def _terrain():
    img = Image.new("RGBA", (W, H), (46, 52, 38, 255))
    arr = np.asarray(img, np.float32)
    n = np.asarray(noise_tex(17), np.float32)[..., None] / 255
    arr[..., :3] *= 0.8 + 0.35 * n
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    rp = bezier(RIVER[0], RIVER[1], RIVER[2], 20) + bezier(RIVER[2], RIVER[3], RIVER[4], 20)[1:] + \
        bezier(RIVER[4], RIVER[5], RIVER[6], 20)[1:] + bezier(RIVER[6], RIVER[7], RIVER[8], 20)[1:]
    d.line(rp, fill=(50, 90, 120, 255), width=90, joint="curve")
    d.line(rp, fill=(70, 115, 145, 255), width=56, joint="curve")
    rng = np.random.default_rng(4)
    # grove
    for i in range(140):
        x = GROVE[0] + rng.random() * (GROVE[2] - GROVE[0]); y = GROVE[1] + rng.random() * (GROVE[3] - GROVE[1])
        r = 12 + rng.random() * 10
        d.ellipse((x - r, y - r, x + r, y + r), fill=(28 + int(rng.random() * 20), 62 + int(rng.random() * 25), 34, 255))
    d.rectangle((LODGE[0] - 24, LODGE[1] - 20, LODGE[0] + 24, LODGE[1] + 20), fill=(150, 130, 100, 255), outline=(40, 30, 20, 255), width=3)
    # tank (pond)
    d.ellipse((TANK[0] - 60, TANK[1] - 36, TANK[0] + 60, TANK[1] + 36), fill=(70, 115, 145, 255), outline=(120, 100, 70, 255), width=6)
    # entrenchment of the camp
    d.line(CAMP, fill=(120, 96, 64, 255), width=14, joint="curve")
    for x, y in CAMP:
        d.rectangle((x - 14, y - 14, x + 14, y + 14), fill=(120, 96, 64, 255))
    tl = TextLayer()
    tl.add((330, 1110), "芒果林", font(SERIF_B, 36), (200, 230, 190))
    tl.add((LODGE[0] + 34, LODGE[1] - 30), "狩猎小屋", font(SANS, 24), IVORY, anchor="lm")
    tl.add((70, 520), "胡格利河", font(SERIF_B, 30), (170, 210, 235), anchor="mm")
    tl.add((600, 322), "纳瓦布营地 · 壕垒", font(SANS, 28), IVORY)
    img.alpha_composite(tl.render(shadow=0.6))
    v = Image.new("RGBA", (W, H), (0, 0, 0, 255)); v.putalpha(vignette_mask(0.9))
    img.alpha_composite(v)
    return img


def _blocks(d, pts, col, size=(80, 50), outline=None, wobble=0, t=0):
    for i, (x, y) in enumerate(pts):
        ox = math.sin(t * 6 + i) * wobble
        d.rounded_rectangle((x - size[0] / 2 + ox, y - size[1] / 2, x + size[0] / 2 + ox, y + size[1] / 2), radius=6,
                            fill=tuple(col) + (240,), outline=(tuple(outline) + (255,)) if outline else (20, 20, 20, 255), width=3 if outline else 2)


def battle_map(img, g):
    img.alpha_composite(_terrain())
    T = g.T
    rain = g.r("b_rain", 0, 0.8) * (1 - g.r("b_advance", 1, 1.5))
    adv = g.r("b_advance", 0.3, 3.0)
    lay = new(); d = ImageDraw.Draw(lay)
    # nawab loyal blocks
    arc_p = g.r("b_arc", 0, 2.0)
    n_show = int(round(arc_p * len(LOYAL)))
    retreat = adv
    pts = [(x + (x - 540) * 0.0, y - 120 * retreat) for (x, y) in LOYAL[:n_show]]
    madan_hit = g.r("b_charge", 2.5, 0.8)
    for i, (x, y) in enumerate(LOYAL[:n_show]):
        col = BLUE
        if (x, y) in MADAN and madan_hit > 0:
            col = lerp_c(BLUE, (90, 100, 130), madan_hit)
        _blocks(d, [(x, y - 120 * retreat)], col)
    # jafar blocks
    jn = int(round(g.r("b_arc", 1.0, 1.5) * len(JAFAR)))
    grey = max(g.r("b_left", 0.5, 1.2) * 0.35, g.r("b_grey", 0, 1.2))
    jcol = lerp_c(BLUE, (150, 150, 150), grey)
    wd = g.r("b_grey", 2.5, 2.5)
    jp = [(x + 160 * wd, y + 60 * wd) for (x, y) in JAFAR[:jn]]
    _blocks(d, jp, jcol, outline=(255, 255, 255) if g.seen("b_left") else None)
    # company blocks + advance
    cp = [(x + 150 * adv, y - 220 * adv) for (x, y) in COMPANY]
    if g.seen("b_grove") or True:
        _blocks(d, cp, RED, size=(64, 44))
    comp(img, lay, 1.0)
    # labels
    if g.seen("b_grove"):
        a = g.r("b_grove", 0.4) * (1 - g.r("b_arc", 0, 0.5))
        label(img, (cp[2][0], cp[2][1] + 58), "公司 约3000人", size=32, color=RED_L, a=g.r("b_grove", 0.4), box=(0, 0, 0, 170))
    if g.seen("b_arc"):
        label(img, (720, 530 - 120 * retreat), "纳瓦布 约5万人", size=34, color=BLUE_L, a=g.r("b_arc", 1.2) * (1 - adv), box=(0, 0, 0, 170))
    if g.seen("b_left"):
        label(img, (720, 1210), "米尔·贾法尔部（左翼）", size=34, color=WHITE, a=g.r("b_left", 0.3) * (1 - g.r("b_count", 0)), box=(70, 70, 70, 200))
    # cannonade
    if g.seen("b_cannon"):
        c = g.ct("b_cannon")
        lay = new(); d = ImageDraw.Draw(lay)
        fade_k = 1 - g.r("b_rain", 0.5, 1.0) * 0.7
        for k in range(6):
            ph = (c * 0.8 + k / 6) % 1.0
            src = LOYAL[(k * 2) % len(LOYAL)]
            dst = COMPANY[k % 5]
            p0 = (src[0], src[1] - 120 * retreat)
            pts_ = [p0, ((p0[0] + dst[0]) / 2, min(p0[1], dst[1]) - 60), dst]
            x, y = point_at(bezier(*pts_, 20), ph)
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 210, 140, int(230 * fade_k)))
        for k in range(3):
            ph = (c * 0.9 + k / 3) % 1.0
            src = COMPANY[k * 2]; dst = MADAN[k % 2]
            x, y = point_at(bezier(src, ((src[0] + dst[0]) / 2, dst[1] - 80), dst, 20), ph)
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 240, 200, 255))
        comp(img, glow(lay, 6), (1 - adv))
    if rain > 0:
        shots_s0._rain(img, T, rain * 0.55)
        lay = new()
        comp(img, Image.new("RGBA", (W, H), (60, 70, 90, 60)), rain)
        for (x, y) in LOYAL[:4]:
            label(img, (x, y - 44), "湿", size=26, color=(180, 220, 255), a=rain * g.r("b_rain", 1.0), box=(10, 30, 60, 210), pad=8)
        label(img, (cp[0][0] - 10, cp[0][1] + 58), "油布", size=26, color=WHITE, a=rain * g.r("b_rain", 1.5) * (1 - g.r("b_charge", 0)), box=(110, 20, 16, 210), pad=8)
    if g.seen("b_charge"):
        c = g.ct("b_charge")
        p = ramp(c, 0.2, 1.6)
        path = bezier((530, 580), (500, 690), (430, 760))
        comp(img, thick_arrow(path, 46, BLUE_L, prog=p * (1 - 0.0), glow_r=8), 1 - ramp(c, 3.2, 0.8))
        if c > 1.8:
            lay = new(); d = ImageDraw.Draw(lay)
            r = 30 + 60 * ease((c - 1.8) / 0.6)
            d.ellipse((430 - r, 760 - r, 430 + r, 760 + r), outline=(255, 230, 160, int(255 * (1 - ease((c - 1.8) / 1.2)))), width=8)
            comp(img, glow(lay, 8))
        label(img, (640, 700), "米尔·马丹 冲锋 → 致命伤", size=32, color=WHITE, a=ramp(c, 2.2, 0.4) * (1 - g.r("b_turban", 0)), box=(20, 40, 90, 220))
    if g.seen("b_turban") and not g.seen("b_letter"):
        c = g.ct("b_turban")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((560, 380, 1010, 700), radius=20, fill=(16, 20, 30, 240), outline=GOLD + (255,), width=3)
        d.polygon([(620, 600), (785, 440), (950, 600)], fill=(110, 40, 34, 255))
        d.rectangle((640, 600, 930, 640), fill=(80, 30, 26, 255))
        d.ellipse((740, 610, 830, 650), fill=(235, 230, 210, 255))
        comp(img, lay, ramp(c, 0, 0.4))
        label(img, (785, 670), "据说：头巾扔在贾法尔脚下", size=28, a=ramp(c, 0.6, 0.4))
    if g.seen("b_letter"):
        c = g.ct("b_letter")
        jx, jy = jp[1] if len(jp) > 1 else JAFAR[1]
        path = bezier((jx, jy), ((jx + 400) / 2, jy + 80), (cp[3][0], cp[3][1] + 20), 30)
        lay = new(); d = ImageDraw.Draw(lay)
        dashed_line(d, path, (240, 240, 240, 255), width=4, prog=ramp(c, 0.2, 1.5))
        if 0.2 < c:
            x, y = point_at(path, ramp(c, 0.2, 1.5))
            d.rectangle((x - 22, y - 15, x + 22, y + 15), fill=(240, 235, 220, 255), outline=(60, 50, 40, 255), width=2)
            d.line((x - 22, y - 15, x, y + 2, x + 22, y - 15), fill=(60, 50, 40, 255), width=2)
        comp(img, lay, 1 - g.r("b_flee", 1.0))
        label(img, (640, 1270), "密信：“快进攻”", size=34, a=ramp(c, 1.2, 0.4) * (1 - g.r("b_flee", 0)), box=(0, 0, 0, 190))
    if g.seen("b_flee"):
        c = g.ct("b_flee")
        lay = new(); d = ImageDraw.Draw(lay)
        camel(d, 690 + 20 * c, 330 - 60 * ease(c / 4), 46, (240, 235, 220, 255))
        comp(img, lay, 1 - ramp(c, 3.5, 1.0))
        comp(img, thick_arrow([(700, 300), (760, 160)], 20, (230, 230, 230), prog=ramp(c, 0.5, 1.0)), 1 - ramp(c, 3.5, 1.0))
        label(img, (790, 200), "西拉杰回首都", size=30, a=ramp(c, 0.8, 0.4) * (1 - ramp(c, 3.5, 1.0)), box=(0, 0, 0, 190))
    if g.seen("b_advance"):
        c = g.ct("b_advance")
        for k, (x, y) in enumerate(COMPANY[::2]):
            path = bezier((x, y - 30), (x + 80, y - 250), (x + 220, y - 420))
            comp(img, thick_arrow(path, 44, RED, prog=ramp(c, 0.2 + k * 0.2, 1.6), glow_r=6), 1 - g.r("b_count", 0, 0.6) * 0.7)
        label(img, (600, 260), "营地被攻破", size=36, color=WHITE, a=ramp(c, 2.0, 0.4) * (1 - g.r("b_grey", 0)), box=(120, 24, 20, 210))
    if g.seen("b_grey"):
        c = g.ct("b_grey")
        label(img, (760, 1230), "从头到尾 · 原地不动", size=38, color=WHITE, a=ramp(c, 0.5, 0.4) * (1 - g.r("b_count", 0)), fontspec=SERIF_B, box=(80, 80, 80, 220))
        jx, jy = JAFAR[2]
        comp(img, thick_arrow(bezier((jx + 140, jy + 60), (jx + 260, jy + 80), (jx + 300, jy + 220)), 34, (180, 180, 180), prog=ramp(c, 3.0, 1.5)), 1 - g.r("b_count", 0))
    if g.seen("b_count"):
        c = g.ct("b_count")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 0, W, H), fill=(6, 8, 12, int(180 * ramp(c, 0, 0.6))))
        comp(img, lay)
        hbar(img, 120, 520, 840, 60, ramp(c, 0.3, 1.0), BLUE, label_l="纳瓦布 · 账面兵力", label_r="约5万", lsize=36)
        hbar(img, 120, 700, 840, 60, 0.06 * ramp(c, 0.8, 1.0), RED, label_l="公司", label_r="约3000", lsize=36)
        hbar(img, 120, 880, 840, 60, 0.12 * ramp(c, 1.8, 1.0), BLUE_L, label_l="真正与公司交手的", label_r="一小部分", lsize=36, a=ramp(c, 1.6, 0.4))
        lay = new(); d = ImageDraw.Draw(lay)
        x1 = 120 + 840 * ramp(c, 0.3, 1.0)
        d.rounded_rectangle((120 + 840 * 0.12, 880, max(120 + 840 * 0.13, x1), 940), radius=30, outline=(170, 170, 170, 200), width=3)
        comp(img, lay, ramp(c, 2.6, 0.5))
        label(img, (640, 1010), "其余：按兵不动或随之撤退", size=32, color=(200, 200, 200), a=ramp(c, 2.8, 0.5))
    if g.seen("b_loss"):
        c = g.ct("b_loss")
        lay = new(); d = ImageDraw.Draw(lay); d.rectangle((0, 0, W, H), fill=(6, 8, 12, 200)); comp(img, lay, ramp(c, 0, 0.4) * (1 - g.r("b_count", 0)) if False else ramp(c, 0, 0.4))
        counter(img, (W / 2, 700), 22 * ramp(c, 0.2, 1.0), prefix="阵亡 ", suffix=" 人", size=120, color=RED_L)
        counter(img, (W / 2, 880), 50 * ramp(c, 0.6, 1.0), prefix="伤 ", suffix=" 人", size=90, color=IVORY)
        label(img, (W / 2, 1020), "公司一方 · 据克莱武1757年7月报告", size=30, color=(190, 180, 160), a=ramp(c, 1.0, 0.4))
    if g.seen("b_deal"):
        c = g.ct("b_deal")
        lay = new(); d = ImageDraw.Draw(lay); d.rectangle((0, 0, W, H), fill=(6, 8, 12, 200)); comp(img, lay)
        title_card(img, "与其说是战斗", None, a=ramp(c, 0, 0.5), y=600, size=60, color=IVORY)
        stamp(img, "不如说是交易", (W / 2, 820), ramp(c, 0.8, 0.6), color=GOLD, size=96, angle=-4)
        label(img, (W / 2, 1060), "战场 = 交割地点", size=44, color=GOLD_L, a=ramp(c, 2.2, 0.5), fontspec=SERIF_B)
    schematic(img, "推演示意")


# ------------------------------------------------------------------ spoils

def spoils(img, g):
    T = g.T
    img.alpha_composite(bg_copy(tint=(40, 40, 50)))
    if g.seen("pay"):
        a = 1 - g.r("boats", 0, 0.5)
        _card(img, W / 2, 640, "米尔·贾法尔", "新纳瓦布", "turban", (190, 190, 190), g.r("pay") * a, name_size=34)
        label(img, (W / 2, 950), "西拉杰被杀 · 开始兑现承诺", size=38, a=g.r("pay", 1.0) * a, box=(0, 0, 0, 170))
    if g.seen("boats"):
        c = g.ct("boats")
        lay = new(); d = ImageDraw.Draw(lay)
        # river band diagonal
        d.polygon([(0, 560), (W, 840), (W, 1120), (0, 840)], fill=(40, 80, 110, 255))
        comp(img, lay, ramp(c, 0, 0.5) * (1 - g.r("clive_money", 0, 0.5)))
        lay = new(); d = ImageDraw.Draw(lay)
        rng = np.random.default_rng(1)
        for k in range(46):
            u = (k / 46 + c * 0.03) % 1.0
            v = rng.random()
            x = u * (W + 200) - 100
            y = 700 + u * 280 + (v - 0.5) * 200
            s = 34 + v * 20
            d.polygon([(x - s, y), (x + s, y), (x + s * 0.7, y + s * 0.35), (x - s * 0.7, y + s * 0.35)], fill=(80, 56, 36, 255))
            d.rectangle((x - s * 0.4, y - s * 0.35, x + s * 0.3, y), fill=(215, 215, 225, 255))
        comp(img, lay, ramp(c, 0.3, 0.6) * (1 - g.r("clive_money", 0, 0.5)))
        label(img, (W / 2, 420), "75拉克卢比 · 将近100万英镑", size=46, color=GOLD_L, a=ramp(c, 0.8, 0.5) * (1 - g.r("clive_money", 0, 0.5)), fontspec=SERIF_B, box=(0, 0, 0, 170))
        label(img, (W / 2, 1220), "200条船 · 奏着乐 · 顺河而下", size=38, a=ramp(c, 1.6, 0.5) * (1 - g.r("clive_money", 0, 0.5)), box=(0, 0, 0, 170))
    if g.seen("clive_money"):
        c = g.ct("clive_money")
        a = 1 - g.r("loot", 0, 0.5)
        lay = new(); d = ImageDraw.Draw(lay)
        n = int(min(18, c * 8))
        for k in range(n):
            coin(d, 300 + (k % 3) * 10, 900 - k * 26, 70)
        comp(img, lay, a)
        counter(img, (680, 640), 234000 * ramp(c, 0.2, 1.6), prefix="£", size=96, a=a)
        label(img, (680, 730), "克莱武个人所得（约）", size=34, a=a * ramp(c, 0.5, 0.4))
        counter(img, (680, 920), 30000 * ramp(c, 1.6, 1.2), prefix="+£", suffix="/年", size=72, color=IVORY, a=a * ramp(c, 1.4, 0.3))
        label(img, (680, 1000), "封地年租（约）", size=32, a=a * ramp(c, 1.8, 0.4))
    if g.seen("loot"):
        c = g.ct("loot")
        a = ramp(c, 0, 0.5)
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((110, 460, W - 110, 1160), radius=24, fill=(232, 222, 198, 245))
        comp(img, lay, a)
        tl = TextLayer()
        tl.add((180, 600), "loot", font(EN_SERIF_B, 150), (40, 30, 22), anchor="lm")
        tl.add((190, 720), "/luːt/  noun & verb", font(EN_SERIF_I, 40), (90, 70, 50), anchor="lm")
        tl.add((190, 820), "from Hindi  lūṭ", font(EN_SERIF, 44), (120, 30, 24), anchor="lm")
        tl.add((190, 930), "源自印地语：劫掠、抢来的财物", font(SANS_B, 40), (40, 30, 22), anchor="lm")
        tl.add((190, 1030), "18世纪后期进入英语", font(SANS, 34), (90, 70, 50), anchor="lm")
        comp(img, tl.render(shadow=0), a)


GROUPS = {
    "conspiracy": (conspiracy, ["court", "jafar", "seth", "pact", "pact2"]),
    "battle_map": (battle_map, ["b_grove", "b_arc", "b_left", "b_cannon", "b_rain", "b_charge", "b_turban", "b_letter",
                                "b_flee", "b_advance", "b_grey", "b_count", "b_loss", "b_deal"]),
    "spoils": (spoils, ["pay", "boats", "clive_money", "loot"]),
}
