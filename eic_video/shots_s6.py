# -*- coding: utf-8 -*-
"""Scene 6: Burke & Hastings, the long unwinding, synthesis, the takeaway, Smith's verdict."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
import maps
from maps import P_CARIB
from shots_s0 import _east_india_house
from shots_s1 import _book
from shots_s5 import _q


@functools.lru_cache(maxsize=1)
def _westminster():
    img = bg_copy(top=(20, 22, 30), bottom=(10, 10, 14))
    d = ImageDraw.Draw(img)
    # hall interior: hammerbeam roof silhouette and tall end window
    stone = (44, 40, 36, 255)
    d.rectangle((0, 900, W, 1400), fill=(30, 26, 22, 255))
    for k in range(7):
        x = -60 + k * 200
        d.polygon([(x, 900), (x + 40, 900), (x + 140, 520), (x + 100, 520)], fill=stone)
        d.polygon([(x + 200, 900), (x + 160, 900), (x + 60, 520), (x + 100, 520)], fill=stone)
    d.polygon([(0, 520), (W / 2, 260), (W, 520)], fill=(36, 32, 28, 255))
    # great window glow
    win = new(); wd = ImageDraw.Draw(win)
    wd.rectangle((W / 2 - 150, 560, W / 2 + 150, 880), fill=(200, 180, 130, 255))
    wd.pieslice((W / 2 - 150, 410, W / 2 + 150, 710), 180, 360, fill=(200, 180, 130, 255))
    img.alpha_composite(win.filter(ImageFilter.GaussianBlur(6)))
    for k in range(5):
        d.line((W / 2 - 150 + k * 75, 470, W / 2 - 150 + k * 75, 880), fill=stone, width=8)
    for k in range(4):
        d.line((W / 2 - 150, 600 + k * 80, W / 2 + 150, 600 + k * 80), fill=stone, width=6)
    rays = new(); rd = ImageDraw.Draw(rays)
    rd.polygon([(W / 2 - 150, 880), (W / 2 + 150, 880), (W / 2 + 420, 1400), (W / 2 - 420, 1400)], fill=(220, 200, 150, 40))
    img.alpha_composite(rays.filter(ImageFilter.GaussianBlur(30)))
    # benches with tiny figures
    for row in range(3):
        y = 1080 + row * 90
        d.rectangle((60, y, W - 60, y + 26), fill=(60, 44, 30, 255))
        for k in range(22):
            x = 90 + k * 42 + (row % 2) * 20
            d.ellipse((x - 10, y - 46, x + 10, y - 26), fill=(16, 14, 12, 255))
            d.rectangle((x - 13, y - 28, x + 13, y), fill=(16, 14, 12, 255))
    return img


def westminster(img, g):
    T = g.T
    z = 1 + 0.05 * min(1, T / 12)
    base = _westminster()
    vw, vh = W / z, H / z
    img.alpha_composite(base.transform((W, H), Image.EXTENT, ((W - vw) / 2, (H - vh) / 2, (W + vw) / 2, (H + vh) / 2), Image.BILINEAR))
    a1 = 1 - g.r("q_burke", 0, 0.5)
    if not g.seen("burke0"):
        title_card(img, "1788年2月", "威斯敏斯特大厅 · 弹劾黑斯廷斯", a=ramp(T, 0.2, 0.6), y=380, size=80, sub_size=40)
    if g.seen("burke0"):
        c = g.ct("burke0")
        lay = new(); d = ImageDraw.Draw(lay)
        d.ellipse((W / 2 - 170, 330, W / 2 + 170, 670), fill=(30, 34, 44, 245), outline=GOLD + (230,), width=4)
        person_bust(d, W / 2, 550, 260, (12, 14, 20, 255), hat="wig")
        comp(img, lay, ramp(c, 0, 0.5) * a1)
        title_card(img, "埃德蒙·伯克", "主控官 · 开场演说连讲四天", a=ramp(c, 0.3, 0.5) * a1, y=760, size=60, sub_size=36)
    if g.seen("q_burke"):
        c = g.ct("q_burke")
        q = _q("q_burke")
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(120 * ramp(c, 0, 0.5)))))
        quote_card(img, q["q"], q["t"].strip("“”"), ramp(c, 0, 0.5), c / max(1, g.cue_len("q_burke") * 0.92), y_center=800)


def unwinding(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    marks = []
    if g.seen("acquit"):
        marks.append((1795, "无罪", (190, 190, 190)))
    if g.seen("t1813"):
        marks.append((1813, "失去贸易垄断", GOLD_L))
        marks.append((1833, "停止商业", GOLD))
    if g.seen("t1857"):
        marks.append((1857, "大起义", RED_L))
    if g.seen("t1874"):
        marks.append((1858, "移交王室", BLUE_L))
        marks.append((1874, "解散", WHITE))
    marks = [(1788, "弹劾", (190, 190, 190))] + marks
    timeline_bar(img, (1780, 1880), sorted(marks), ramp(T, 0, 1.5),
                 y=820, x0=90, x1=990)
    cap = None
    if g.seen("acquit") and not g.seen("tide"):
        cap = ("审判拖了七年", g.r("acquit"))
    elif g.seen("tide") and not g.seen("t1813"):
        cap = ("议会一点点收回权力", g.r("tide"))
    elif g.seen("t1833") and not g.seen("t1857"):
        cap = ("不做生意，只剩统治", g.r("t1833"))
    elif g.seen("t1874"):
        cap = ("1874 · 东印度公司解散", g.r("t1874", 2.0))
    if cap:
        title_card(img, cap[0], None, a=cap[1], y=1180, size=64)
    if g.seen("t1857") and not g.seen("t1874"):
        lay = new(); d = ImageDraw.Draw(lay)
        for k in range(14):
            x = 120 + k * 62
            soldier(d, x, 1260, 100, (150, 40, 34, 255))
        comp(img, lay, g.r("t1857", 0.5))
        label(img, (W / 2, 1100), "1857 · 战火烧遍北印度", size=40, color=RED_L, a=g.r("t1857", 0.8), fontspec=SERIF_B)


def synth(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    sp = g.r("synth", 0, 1.2)
    lay = new(); d = ImageDraw.Draw(lay)
    _book(d, 110 + 60 * sp, 380, 320, 420, "The Company-State", "Stern", (40, 60, 90))
    _book(d, 650 - 60 * sp, 380, 320, 420, "The Anarchy", "Dalrymple", (90, 40, 34))
    comp(img, lay, ramp(T, 0, 0.5) * (1 - sp))
    if not g.seen("synth"):
        label(img, (W / 2, 900), "意外滑成帝国？", size=46, color=RED_L, a=ramp(T, 0.5, 0.5), fontspec=SERIF_B)
        label(img, (W / 2, 990), "还是一开始就是政治体？", size=46, color=BLUE_L, a=ramp(T, 1.5, 0.5), fontspec=SERIF_B)
    else:
        c = g.ct("synth")
        items = [("工具", "特许状给的权力", GOLD_L), ("机会", "莫卧儿的崩塌", BLUE_L), ("推力", "股东·董事·职员的算盘", RED_L)]
        for i, (h_, t_, col) in enumerate(items):
            a = ramp(c, 0.8 + i * 2.2, 0.5)
            y = 640 + i * 190
            label(img, (230, y), h_, size=56, color=col, a=a, fontspec=SERIF_B)
            label(img, (620, y), t_, size=40, color=WHITE, a=a, box=(0, 0, 0, 160))
        title_card(img, "各对一半", None, a=ramp(c, 0, 0.5), y=440, size=72)


def lesson(img, g):
    img.alpha_composite(bg_copy(tint=(60, 40, 10)))
    T = g.T
    title_card(img, "带走一个判断", None, a=ramp(T, 0, 0.5) * (1 - g.r("lesson2", 0, 0.5)), y=420, size=64)
    if g.seen("lesson1") and not g.seen("lesson2"):
        c = g.ct("lesson1")
        mech_card(img, "收入：赢得客户", "收入：掌握垄断入口", ramp(c, 0.5, 2.5), a=ramp(c, 0, 0.5), y=800, tag="当")
        label(img, (300, 1160), "服务", size=56, color=IVORY, a=ramp(c, 3.5, 0.4), fontspec=SERIF_B)
        comp(img, thick_arrow([(420, 1160), (640, 1160)], 24, GOLD, prog=ramp(c, 4.0, 0.5)))
        label(img, (780, 1160), "征收", size=56, color=RED_L, a=ramp(c, 4.5, 0.4), fontspec=SERIF_B)
    if g.seen("lesson2"):
        c = g.ct("lesson2")
        node(img, (W / 2, 480), "谁在做决定？", None, color=GOLD, a=ramp(c, 0, 0.4), w=520)
        for i, (nm, col, x) in enumerate([("命令链", BLUE_L, 300), ("钱的流向", GOLD, 780)]):
            a = ramp(c, 0.4 + i * 0.8, 0.4)
            p = [(x, 1150), (x + (W / 2 - x) * 0.4, 850), (W / 2 + (x - W / 2) * 0.2, 560)]
            comp(img, thick_arrow(bezier(*p), 30, col, prog=ramp(c, 0.4 + i * 0.8, 1.0)), a)
            label(img, (x, 1210), nm, size=48, color=col, a=a, fontspec=SERIF_B)


def final(img, g):
    T = g.T
    if not g.seen("q_smith_final"):
        img.alpha_composite(maps.carib_map())
        P = P_CARIB
        lay = new(); d = ImageDraw.Draw(lay)
        for (lo, la) in ((-64.93, 18.34), (-64.75, 17.73)):
            maps.marker(d, P(lo, la), 12)
        comp(img, lay, ramp(T, 0.3, 0.4))
        x, y = P(-64.93, 18.34)
        label(img, (x + 30, y - 40), "圣托马斯", size=36, anchor="lm", a=ramp(T, 0.5, 0.4))
        x, y = P(-64.75, 17.73)
        label(img, (x + 30, y + 40), "圣克罗伊", size=36, anchor="lm", a=ramp(T, 0.7, 0.4))
        title_card(img, "斯密原句的语境", "丹麦专营公司治理的加勒比小岛", a=ramp(T, 0, 0.5), y=420, size=56, sub_size=36)
        label(img, (W / 2, 1180), "同一章：大量篇幅批评英国东印度公司", size=34, color=GOLD_L, a=ramp(T, 4.0, 0.5), box=(0, 0, 0, 190))
        schematic(img)
    else:
        c = g.ct("q_smith_final")
        img.alpha_composite(bg_copy(top=(40, 30, 40), bottom=(10, 10, 16), tint=(120, 70, 20)))
        h = _east_india_house()
        hh = h.resize((int(h.size[0] * 1.2), int(h.size[1] * 1.2)), Image.BICUBIC)
        comp(img, hh, 0.35, ((W - hh.size[0]) / 2, 300))
        q = _q("q_smith_final")
        quote_card(img, q["q"], q["t"].strip("“”"), ramp(c, 0, 0.6), c / max(1, g.cue_len("q_smith_final") * 0.9), y_center=820)


GROUPS = {
    "westminster": (westminster, ["westminster", "burke0", "q_burke"]),
    "unwinding": (unwinding, ["acquit", "tide", "t1813", "t1833", "t1857", "t1874"]),
    "synth": (synth, ["debate2", "synth"]),
    "lesson": (lesson, ["lesson0", "lesson1", "lesson2"]),
    "final": (final, ["smith_ctx", "q_smith_final"]),
}
