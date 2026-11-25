# -*- coding: utf-8 -*-
"""Scene 4: Diwani — from trade to tax."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
import maps
from maps import P_INDIA, PLACES
from shots_s3 import _card
import shots_s0


def atm(img, g):
    img.alpha_composite(bg_copy(tint=(40, 30, 50)))
    T = g.T
    a1 = 1 - g.r("qasim", 0, 0.6)
    _card(img, W / 2, 560, "米尔·贾法尔", "扶起来的纳瓦布", "turban", (190, 190, 190), ramp(T, 0, 0.5) * a1, name_size=34)
    lay = new(); d = ImageDraw.Draw(lay)
    for k in range(10):
        ph = (T * 0.5 + k / 10) % 1
        x = W / 2 + (ph - 0.5) * 60 + math.sin(k * 2.1) * 120 * ph
        y = 760 + ph * 380
        coin(d, x, y, 22)
    comp(img, lay, ramp(T, 0.5, 0.5) * a1)
    label(img, (W / 2, 1220), "提款机", size=56, color=GOLD_L, a=ramp(T, 1.0, 0.5) * a1 * (1 - g.r("gifts", 0)), fontspec=SERIF_B)
    if g.seen("gifts"):
        c = g.ct("gifts")
        a = g.r("gifts") * a1
        lay = new(); d = ImageDraw.Draw(lay); d.rectangle((0, 1000, W, 1330), fill=(8, 10, 16, 200)); comp(img, lay, a)
        counter(img, (W / 2, 1120), 2500000 * ramp(c, 0.4, 2.0), prefix="约 £", size=90, a=a)
        label(img, (W / 2, 1230), "1757–1765 · “政治礼物” · 估计", size=32, a=a * ramp(c, 1.0, 0.5))
    if g.seen("qasim"):
        a = g.r("qasim", 0.3) * (1 - g.r("buxar", 0))
        _card(img, W / 2, 560, "米尔·卡西姆", "1760 换上 · 贾法尔的女婿", "turban", BLUE_L, a, name_size=34)
    if g.seen("duty"):
        c = g.ct("duty")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((300, 860, 780, 900), fill=(120, 90, 60, 255))
        d.rectangle((310, 900, 340, 1150), fill=(120, 90, 60, 255)); d.rectangle((740, 900, 770, 1150), fill=(120, 90, 60, 255))
        # barrier lifts
        ang = 90 * ramp(c, 0.5, 0.8)
        L = 380
        x0, y0 = 350, 1010
        d.line((x0, y0, x0 + L * math.cos(math.radians(ang)), y0 - L * math.sin(math.radians(ang))), fill=(220, 60, 50, 255), width=18)
        comp(img, lay, ramp(c, 0, 0.4))
        label(img, (W / 2, 830), "取消所有商人的关税", size=40, color=GOLD_L, a=ramp(c, 0.6, 0.4), fontspec=SERIF_B)
        label(img, (W / 2, 1220), "职员的免税特权 → 不再值钱", size=38, a=ramp(c, 1.6, 0.4), box=(110, 20, 16, 200))


def buxar(img, g):
    img.alpha_composite(maps.north_map())
    T = g.T
    P = maps.P_NORTH
    bx, by = P(*PLACES["Buxar"])
    lay = new(); maps.marker(ImageDraw.Draw(lay), (bx, by), 12, RED_L); comp(img, lay)
    label(img, (bx, by - 150), "布克萨尔 1764.10", size=40, color=WHITE, a=ramp(T, 0.2, 0.4), fontspec=SERIF_B, box=(0, 0, 0, 170))
    for k, (lo, la, nm) in enumerate([(87.0, 24.2, "米尔·卡西姆"), (81.2, 27.6, "奥德纳瓦布"), (80.6, 24.6, "沙·阿拉姆二世")]):
        x, y = P(lo, la)
        p = ramp(T, 0.8 + k * 0.5, 1.0)
        comp(img, thick_arrow(bezier((x, y), ((x + bx) / 2, (y + by) / 2 - 40), (bx + (x - bx) * 0.18, by + (y - by) * 0.18)), 26, BLUE, prog=p))
        label(img, (x, y + (60 if k != 1 else -60)), nm, size=30, color=BLUE_L, a=p, box=(0, 0, 0, 170))
    cx, cy = P(88.36, 22.57)
    comp(img, thick_arrow(bezier((cx, cy), (bx + 200, by + 120), (bx + 30, by + 14)), 38, RED, prog=ramp(T, 2.5, 1.2), glow_r=6))
    stamp(img, "公司胜", (W / 2, 1180), ramp(T, 4.0, 0.6), color=RED_L, size=64)
    schematic(img)


def diwani_tent(img, g):
    img.alpha_composite(bg_copy(tint=(80, 50, 10)))
    T = g.T
    m = shots_s0._miniature()
    zoom = 1.0 + 0.25 * g.r("chair", 0, 1.5) - 0.25 * g.r("grant", 0, 1.0)
    s = 1.0 * zoom
    mm = m.resize((int(m.size[0] * s), int(m.size[1] * s)), Image.BICUBIC)
    # focus point table/chair (450, 520 in miniature coords)
    ox, oy = W / 2 - 450 * s, 840 - 520 * s
    a_m = ramp(T, 0, 0.5) * (1 - 0.65 * g.r("grant", 0, 0.8))
    comp(img, mm, a_m, (ox, oy))
    if not g.seen("chair"):
        label(img, (W / 2, 1300), "1765.8.12 · 阿拉哈巴德 · 克莱武营帐", size=36, color=GOLD_L, a=ramp(T, 0.6, 0.4), box=(0, 0, 0, 180))
    if g.seen("chair") and not g.seen("grant"):
        c = g.ct("chair")
        label(img, (W / 2, 1290), "宝座 = 搭布的扶手椅 + 英国式餐桌", size=36, color=WHITE, a=ramp(c, 1.0, 0.4), box=(0, 0, 0, 200))
    if g.seen("grant"):
        c = g.ct("grant")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((90, 480, W - 90, 1180), radius=20, fill=(232, 216, 176, 245), outline=(150, 110, 50, 255), width=4)
        comp(img, lay, ramp(c, 0, 0.5))
        tl = TextLayer()
        tl.add((W / 2, 560), "迪瓦尼 Diwani", font(SERIF_B, 60), (110, 30, 24))
        tl.add((W / 2, 650), "财政与征税权", font(SANS_B, 40), (50, 40, 30))
        for i, t_ in enumerate(["孟加拉", "比哈尔", "奥里萨"]):
            tl.add((250 + i * 290, 780), t_, font(SERIF_B, 54), (40, 30, 22))
        comp(img, tl.render(shadow=0), ramp(c, 0.3, 0.5))
        if g.seen("forever"):
            c2 = g.ct("forever")
            tl = TextLayer()
            tl.add((W / 2, 920), "“from generation to generation,", font(EN_SERIF_I, 40), (80, 50, 30))
            tl.add((W / 2, 975), "for ever and ever”", font(EN_SERIF_I, 40), (80, 50, 30))
            tl.add((W / 2, 1060), "世世代代，永远不得撤换", font(SERIF_B, 46), (140, 30, 24))
            comp(img, tl.render(shadow=0), ramp(c2, 0.2, 0.6))
            label(img, (W / 2, 1230), "敕令英译文 · 1765年8月12日", size=28, color=(200, 190, 160), a=ramp(c2, 0.6, 0.5))
    if g.seen("tribute"):
        c = g.ct("tribute")
        lay = new(); d = ImageDraw.Draw(lay); d.rectangle((0, 0, W, H), fill=(8, 10, 16, 210)); comp(img, lay, ramp(c, 0, 0.4))
        lay = new(); d = ImageDraw.Draw(lay)
        for k in range(int(min(26, c * 10))):
            coin(d, 160 + (k % 13) * 60, 980 + (k // 13) * 70, 26)
        comp(img, lay)
        title_card(img, "回报：每年26拉克卢比", "给皇帝的贡金", a=ramp(c, 0.2, 0.5), y=720, size=64)


def _ledger_book():
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((60, 420, W - 60, 1200), radius=16, fill=(90, 50, 30, 255))
    d.rectangle((84, 440, W / 2 - 6, 1180), fill=(234, 222, 192, 255))
    d.rectangle((W / 2 + 6, 440, W - 84, 1180), fill=(234, 222, 192, 255))
    for k in range(16):
        y = 540 + k * 40
        d.line((104, y, W / 2 - 26, y), fill=(170, 150, 120, 255), width=1)
        d.line((W / 2 + 26, y, W - 104, y), fill=(170, 150, 120, 255), width=1)
    d.line((W / 2, 440, W / 2, 1180), fill=(60, 40, 24, 255), width=6)
    d.text((W / 4 + 10, 490), "贸易", font=font(SERIF_B, 48), fill=(60, 40, 24, 255), anchor="mm")
    d.text((3 * W / 4 - 10, 490), "税收", font=font(SERIF_B, 48), fill=(130, 30, 24, 255), anchor="mm")
    return lay


def ledger(img, g):
    img.alpha_composite(bg_copy(tint=(50, 40, 20)))
    T = g.T
    comp(img, _ledger_book(), ramp(T, 0, 0.5))
    rng = np.random.default_rng(3)
    tl = TextLayer()
    shift = g.r("ledger_tax", 0.5, 2.5)
    for k in range(12):
        v = int(rng.integers(1200, 9800))
        a = ramp(T, 0.3 + k * 0.08, 0.2)
        # entries migrate from left column to right column
        mk = clamp01(shift * 12 - k)
        x = lerp(W / 4 + 10, 3 * W / 4 - 10, ease(mk))
        y = 560 + k * 40
        col = lerp_c((60, 40, 24), (130, 30, 24), ease(mk))
        tl.add((x, y), f"{v:,}", font(EN_SERIF, 30), col)
    comp(img, tl.render(shadow=0), ramp(T, 0.2, 0.3))
    if g.seen("ledger_silver"):
        c = g.ct("ledger_silver")
        a = 1 - g.r("ledger_tax", 0, 0.5)
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 1220, W, 1330), fill=(8, 10, 16, 220))
        comp(img, lay, a)
        lay = new(); d = ImageDraw.Draw(lay)
        x = -100 + ease(c / 3.0) * 700
        ship(d, x, 1290, 120)
        for k in range(3):
            d.rectangle((x - 40 + k * 26, 1240, x - 20 + k * 26, 1252), fill=(220, 220, 230, 255))
        comp(img, lay, a)
        label(img, (800, 1275), "英国白银 → 买布", size=34, color=IVORY, a=a * ramp(c, 0.8, 0.4))
    if g.seen("ledger_tax"):
        c = g.ct("ledger_tax")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 1205, W, 1345), fill=(8, 10, 16, 230))
        comp(img, lay)
        items = ["孟加拉的税", "买孟加拉的布", "运到伦敦卖"]
        for i, t_ in enumerate(items):
            x = 190 + i * 350
            label(img, (x, 1275), t_, size=34, color=GOLD_L if i == 0 else WHITE, a=ramp(c, 0.6 + i * 0.9, 0.4), fontspec=SERIF_B)
            if i < 2:
                comp(img, thick_arrow([(x + 110, 1275), (x + 220, 1275)], 16, GOLD, prog=ramp(c, 1.0 + i * 0.9, 0.5)))


def mech2(img, g):
    img.alpha_composite(bg_copy(tint=(60, 40, 10)))
    T = g.T
    mech_card(img, "收入来源：市场竞争", "收入来源：行政垄断", ramp(T, 1.0, 2.5), a=ramp(T, 0, 0.5))
    label(img, (300, 1150), "做买卖：讨好客户", size=36, color=IVORY, a=ramp(T, 3.5, 0.5), box=(0, 0, 0, 170))
    label(img, (780, 1150), "收税：握住入口", size=36, color=GOLD_L, a=ramp(T, 4.5, 0.5), box=(0, 0, 0, 170))


def dual(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    sep = g.r("dual2", 0, 1.5)
    title_card(img, "双重政府", "克莱武的设计", a=ramp(T, 0, 0.5), y=420, size=76)
    for side, (x, nm, sub, col) in enumerate([(330, "收税权", "公司", RED), (750, "治理责任", "纳瓦布（名义上）", BLUE)]):
        dx = (-1 if side == 0 else 1) * 70 * sep
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((x - 170 + dx, 640, x + 170 + dx, 1100), radius=18, fill=tuple(col) + (230,), outline=GOLD + (255,), width=3)
        comp(img, lay, ramp(T, 0.6 + side * 0.6, 0.5))
        label(img, (x + dx, 800), nm, size=52, color=WHITE, a=ramp(T, 0.6 + side * 0.6, 0.5), fontspec=SERIF_B)
        label(img, (x + dx, 900), sub, size=34, color=IVORY, a=ramp(T, 0.8 + side * 0.6, 0.5))
    if sep > 0:
        lay = new(); d = ImageDraw.Draw(lay)
        pts = [(W / 2, 600), (W / 2 - 20, 700), (W / 2 + 15, 800), (W / 2 - 18, 900), (W / 2 + 12, 1000), (W / 2, 1140)]
        d.line(cut_polyline(pts, sep), fill=(250, 230, 190, 255), width=6)
        comp(img, glow(lay, 8))
        label(img, (W / 2, 1220), "权力与责任 · 被拆开", size=44, color=GOLD_L, a=g.r("dual2", 0.8), fontspec=SERIF_B)


def smith1(img, g):
    img.alpha_composite(bg_copy(tint=(60, 40, 10)))
    T = g.T
    a_bust = 1 - g.r("q_smith1", 0, 0.5)
    lay = new(); d = ImageDraw.Draw(lay)
    d.ellipse((W / 2 - 200, 420, W / 2 + 200, 820), fill=(30, 34, 44, 255), outline=GOLD + (230,), width=4)
    person_bust(d, W / 2, 680, 300, (12, 14, 20, 255), hat="wig")
    comp(img, lay, ramp(T, 0, 0.5) * a_bust)
    title_card(img, "亚当·斯密", "《国富论》1776", a=ramp(T, 0.3, 0.5) * a_bust, y=930, size=66)
    if g.seen("q_smith1"):
        c = g.ct("q_smith1")
        ln = g.cue_len("q_smith1")
        q = None
        from script_data import SCENES
        for s_ in SCENES:
            for d_ in s_["lines"]:
                if d_.get("cue") == "q_smith1":
                    q = d_
        zh = q["t"].strip("“”")
        quote_card(img, q["q"], zh, ramp(c, 0, 0.5), c / max(1, ln * 0.95), a=1 - 0.5 * g.r("smith1b", 0, 0.5))
    if g.seen("smith1b"):
        c = g.ct("smith1b")
        # balance: merchant vs sovereign
        lay = new(); d = ImageDraw.Draw(lay)
        ang = math.radians(-12 * ease(c / 1.5))
        cx, cy = W / 2, 1230
        L = 300
        x0, y0 = cx - L * math.cos(ang), cy + L * math.sin(ang)
        x1, y1 = cx + L * math.cos(ang), cy - L * math.sin(ang)
        d.line((x0, y0, x1, y1), fill=GOLD + (255,), width=8)
        d.polygon([(cx, cy), (cx - 30, cy + 60), (cx + 30, cy + 60)], fill=GOLD + (255,))
        comp(img, lay, ramp(c, 0, 0.4))
        label(img, (x0, y0 - 40), "商人：低买高卖", size=32, color=WHITE, a=ramp(c, 0.3, 0.4), box=(110, 20, 16, 210))
        label(img, (x1, y1 - 40), "君主：民富国强", size=32, color=WHITE, a=ramp(c, 0.6, 0.4), box=(20, 40, 90, 210))


GROUPS = {
    "atm": (atm, ["atm", "gifts", "qasim", "duty"]),
    "buxar": (buxar, ["buxar"]),
    "diwani_tent": (diwani_tent, ["tent", "chair", "grant", "forever", "tribute"]),
    "ledger": (ledger, ["ledger0", "ledger_silver", "ledger_tax"]),
    "mech2": (mech2, ["mech2"]),
    "dual": (dual, ["dual", "dual2"]),
    "smith1": (smith1, ["smith1", "q_smith1", "smith1b"]),
}
