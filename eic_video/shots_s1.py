# -*- coding: utf-8 -*-
"""Scene 1: the 1600 charter, the sea route, joint stock, VOC, the political powers, the scholarly debate."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
import maps
from maps import P_WORLD, PLACES


@functools.lru_cache(maxsize=1)
def _charter_doc():
    w, h = 860, 1000
    im = parchment(w, h, seed=5).copy()
    d = ImageDraw.Draw(im)
    fb = font(EN_SERIF_B, 64)
    d.text((w / 2, 120), "ELIZABETH", font=fb, fill=(60, 30, 20, 255), anchor="mm")
    fi = font(EN_SERIF_I, 30)
    body = ("by the Grace of God, Queen of England, France and Ireland, Defender of the Faith... "
            "Whereas our most dear and loving Subjects ... have of our certain Knowledge been Petitioners unto Us, "
            "for our Royal Assent and Licence to be granted unto them, that they ... might adventure and set forth "
            "one or more Voyages ... to the East-Indies ...")
    y = 200
    for l in wrap_words(body, fi, w - 160):
        d.text((80, y), l, font=fi, fill=(70, 45, 30, 255), anchor="lm"); y += 44
    y += 20
    nm = ["The Governor and Company of", "Merchants of London trading", "into the East-Indies"]
    for l in nm:
        d.text((w / 2, y), l, font=font(EN_SERIF_B, 40), fill=(120, 30, 24, 255), anchor="mm"); y += 54
    y += 20
    for l in wrap_words("... the whole, entire and only Trade and Traffick ... for the Term of Fifteen Years ...", fi, w - 160):
        d.text((80, y), l, font=fi, fill=(70, 45, 30, 255), anchor="lm"); y += 44
    d.text((w - 90, h - 90), "31 Dec. 1600", font=font(EN_SERIF_I, 34), fill=(70, 45, 30, 255), anchor="rm")
    return im, (y - 54 * 3 - 20 - 44 * 2)


def charter(img, g):
    img.alpha_composite(bg_copy(tint=(70, 50, 20)))
    T = g.T
    doc, ny = _charter_doc()
    # unroll: reveal from top
    rev = ease_out(T / 1.6)
    hh = max(2, int(doc.size[1] * rev))
    part = doc.crop((0, 0, doc.size[0], hh))
    x0, y0 = (W - doc.size[0]) / 2, 300
    sh = new(); ImageDraw.Draw(sh).rectangle((x0 + 10, y0 + 16, x0 + doc.size[0] + 10, y0 + hh + 16), fill=(0, 0, 0, 160))
    comp(img, sh.filter(ImageFilter.GaussianBlur(16)))
    comp(img, part, 1.0, (x0, y0))
    # roller at the bottom edge while unrolling
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0 - 20, y0 + hh - 18, x0 + doc.size[0] + 20, y0 + hh + 18), radius=18, fill=(150, 120, 80, 255))
    comp(img, lay, 1 - ramp(T, 1.6, 0.4))
    if g.seen("seal"):
        c = g.ct("seal")
        s = wax_seal(78)
        sc = 1 + 1.2 * (1 - ease_out(min(1, c / 0.35)))
        ss = s.resize((int(s.size[0] * sc), int(s.size[1] * sc)), Image.BICUBIC)
        comp(img, ss, min(1, c / 0.2), (x0 + 170 - ss.size[0] / 2, y0 + 900 - ss.size[1] / 2))
        label(img, (W / 2, 1360 - 60), "伊丽莎白一世特许状 · 1600年12月31日", size=36, color=GOLD_L, a=ramp(c, 0.5, 0.5), box=(0, 0, 0, 170))
    if g.seen("name"):
        a = g.r("name", 0.2)
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((x0 + 60, y0 + ny - 40, x0 + doc.size[0] - 60, y0 + ny + 140), radius=12, outline=GOLD + (255,), width=4)
        comp(img, glow(lay, 6), a)
        label(img, (W / 2, y0 + ny + 200), "“伦敦商人对东印度贸易的总督与公司”", size=38, color=WHITE, a=a, box=(0, 0, 0, 200))


def _route_pts():
    P = P_WORLD
    pts = [(-0.12, 51.5), (-7, 45), (-13, 30), (-15, 14), (-11, -2), (-2, -22), (18.5, -36.5), (35, -33), (50, -20),
           (62, -2), (70, 10), (72.8, 18.9)]
    return [P(*p) for p in pts]


def world_route(img, g):
    img.alpha_composite(maps.world_map())
    T = g.T
    P = P_WORLD
    d0 = ImageDraw.Draw(img)
    # monopoly zone east of the Cape meridian (~20E)
    a = g.r("monopoly", 0.1, 1.0)
    if a > 0:
        lay = new(); d = ImageDraw.Draw(lay)
        x = P(20, 0)[0]
        d.rectangle((x, 0, W, H), fill=GOLD + (40,))
        d.line((x, 0, x, H), fill=GOLD + (230,), width=4)
        comp(img, lay, a * (1 - 0.6 * g.r("route", 0)))
        label(img, (x + 20, 420), "好望角以东", size=50, color=GOLD_L, a=a, anchor="lm", fontspec=SERIF_B)
        label(img, (x + 20, 486), "独家贸易 · 期限15年", size=34, color=IVORY, a=a, anchor="lm", box=(0, 0, 0, 160))
    lay = new(); d = ImageDraw.Draw(lay)
    for nm, zh in (("London", "伦敦"), ("Cape", "好望角"), ("Bombay", "印度")):
        xy = P(*PLACES[nm])
        maps.marker(d, xy, 9)
    comp(img, lay)
    label(img, (P(*PLACES["London"])[0] + 18, P(*PLACES["London"])[1] - 30), "伦敦", size=34, anchor="lm")
    label(img, (P(*PLACES["Cape"])[0], P(*PLACES["Cape"])[1] + 46), "好望角", size=34)
    label(img, (P(*PLACES["Bombay"])[0] - 10, P(*PLACES["Bombay"])[1] - 36), "印度", size=34)
    if g.seen("route0") or g.seen("route"):
        c = g.ct("route0") if g.seen("route0") else g.ct("route")
        rp = _route_pts()
        prog = clamp01(c / 9.0)
        lay = new(); d = ImageDraw.Draw(lay)
        dashed_line(d, rp, GOLD_L + (230,), width=5, prog=prog)
        comp(img, lay)
        x, y = point_at(rp, prog)
        sl = new(); ship(ImageDraw.Draw(sl), x, y, 70)
        comp(img, sl)
        if g.seen("route"):
            months = 5.5 * prog / 1.0
            label(img, (W / 2, 1230), f"单程约 5–6 个月 · 往返常常一年半以上", size=36, color=GOLD_L, a=g.r("route", 0.5), box=(0, 0, 0, 180))
    if g.seen("risk"):
        items = [((-11, 38), "风暴"), ((-6, 2), "海盗"), ((48, -18), "葡萄牙"), ((80, 0), "荷兰")]
        for i, ((lo, la), t_) in enumerate(items):
            a = g.r("risk", 0.3 + i * 0.4, 0.4)
            x, y = P(lo, la)
            lay = new(); d = ImageDraw.Draw(lay)
            d.ellipse((x - 44, y - 44, x + 44, y + 44), fill=(120, 24, 20, 220), outline=(255, 200, 180, 255), width=3)
            d.line((x - 18, y - 18, x + 18, y + 18), fill=(255, 230, 220, 255), width=6)
            d.line((x - 18, y + 18, x + 18, y - 18), fill=(255, 230, 220, 255), width=6)
            comp(img, lay, a)
            label(img, (x, y + 72), t_, size=32, a=a, box=(0, 0, 0, 170))
    schematic(img)


def shares(img, g):
    img.alpha_composite(bg_copy(tint=(60, 45, 15)))
    T = g.T
    # merchants on top dropping coins into a ship ("the venture"), then split back
    lay = new(); d = ImageDraw.Draw(lay)
    xs = [180, 360, 540, 720, 900]
    for i, x in enumerate(xs):
        person_bust(d, x, 470, 150, (190, 175, 140, 255), hat="tricorn")
    comp(img, lay, ramp(T, 0, 0.4))
    ship_l = new(); ship(ImageDraw.Draw(ship_l), W / 2, 1000, 420)
    comp(img, ship_l, ramp(T, 0.3, 0.5))
    lay = new(); d = ImageDraw.Draw(lay)
    for i, x in enumerate(xs):
        p = clamp01((T - 0.8 - i * 0.15) / 1.0)
        if 0 < p < 1:
            yy = 560 + p * 300
            xx = x + (W / 2 - x) * ease(p)
            coin(d, xx, yy, 22)
    comp(img, lay)
    label(img, (W / 2, 1110), "入股 · 共担风险", size=44, color=GOLD_L, a=ramp(T, 1.2, 0.5), fontspec=SERIF_B)
    p2 = ramp(T, 3.2, 1.0)
    if p2 > 0:
        lay = new(); d = ImageDraw.Draw(lay)
        for i, x in enumerate(xs):
            q = clamp01((T - 3.2 - i * 0.12) / 1.0)
            xx = W / 2 + (x - W / 2) * ease(q); yy = 1000 - 360 * ease(q) + 120 * (1 - ease(q))
            if q > 0:
                coin(d, xx, yy, 22); coin(d, xx + 14, yy - 12, 22)
        comp(img, lay)
        label(img, (W / 2, 1210), "赚了按股分，亏了一起扛", size=40, a=p2, box=(0, 0, 0, 170))


def voc(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    a1 = 1 - g.r("voyages", 0, 0.5)
    if a1 > 0:
        title_card(img, "资本规模（约）", None, a=a1 * ramp(T, 0, 0.4), y=380, size=56)
        p = ease((T - 0.4) / 1.5)
        hbar(img, 120, 600, 840, 80, 0.1 * p, RED, label_l="英国东印度公司 1600", label_r="1", a=a1)
        hbar(img, 120, 820, 840, 80, 1.0 * p, (220, 140, 50), label_l="荷兰联合东印度公司 VOC 1602", label_r="≈10", a=a1)
        for i, t_ in enumerate(["长期资本", "宣战 · 缔约 · 建要塞"]):
            label(img, (W / 2, 1020 + i * 80), t_, size=40, color=GOLD_L, a=a1 * ramp(T, 1.8 + i * 0.6, 0.4), box=(40, 25, 5, 180))
        label(img, (W / 2, 1240), "荷兰公司另有一期专讲", size=28, color=(180, 170, 150), a=a1 * ramp(T, 2.6, 0.4))
    if g.seen("voyages"):
        c = g.ct("voyages")
        a = g.r("voyages", 0.2)
        title_card(img, "英国公司：一次航行，一次凑钱", None, a=a, y=380, size=50)
        lay = new(); d = ImageDraw.Draw(lay)
        for i in range(4):
            x = 170 + i * 250
            q = ramp(c, 0.3 + i * 0.35, 0.4)
            if q > 0:
                ship(d, x, 700, 150)
                for k in range(3):
                    coin(d, x - 30 + k * 30, 790, 18)
        comp(img, lay, a)
        label(img, (W / 2, 900), "回港 → 分账 → 散伙", size=40, a=ramp(c, 1.6, 0.4), box=(0, 0, 0, 170))
        p = ramp(c, 3.2, 0.6)
        if p > 0:
            lay = new(); d = ImageDraw.Draw(lay)
            d.rounded_rectangle((260, 1020, 820, 1220), radius=24, fill=(30, 26, 18, 230), outline=GOLD + (255,), width=3)
            for k in range(7):
                coin(d, 380 + k * 55, 1120, 26)
            comp(img, lay, p)
            label(img, (W / 2, 1270), "1657年 · 长期股本", size=44, color=GOLD_L, a=p, fontspec=SERIF_B)


def powers(img, g):
    img.alpha_composite(bg_copy(tint=(70, 50, 20)))
    T = g.T
    doc, _ = _charter_doc()
    small = doc.resize((int(doc.size[0] * 0.8), int(doc.size[1] * 0.8)), Image.BICUBIC)
    comp(img, small, 0.55 - 0.35 * g.r("powers"), ((W - small.size[0]) / 2, 330))
    if g.seen("seed") and not g.seen("powers"):
        title_card(img, "另一颗种子", None, a=g.r("seed", 0.2), y=760, size=80)
    if g.seen("powers"):
        c = g.ct("powers")
        title_card(img, "1660年代以后 · 王室陆续授权", None, a=ramp(c, 0, 0.4), y=430, size=46)
        items = ["宣战媾和", "铸币", "驻军 · 建要塞", "审判"]
        for i, t_ in enumerate(items):
            p = ramp(c, 1.0 + i * 1.3, 0.35)
            x = 300 if i % 2 == 0 else 780
            y = 700 + (i // 2) * 280
            stamp(img, t_, (x, y), p, color=(190, 40, 34), size=60, angle=-8 + i * 5)
        label(img, (W / 2, 1270), "对非基督教的君主", size=30, color=IVORY, a=ramp(c, 1.0, 0.4), box=(0, 0, 0, 160))


def _book(d, x, y, w, h, title, year, col):
    d.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=tuple(col) + (255,), outline=GOLD + (255,), width=3)
    d.rectangle((x + 14, y, x + 30, y + h), fill=tuple(max(0, v - 40) for v in col) + (255,))
    f = font(EN_SERIF_B, 40)
    yy = y + 90
    for l in wrap_words(title, f, w - 80):
        d.text((x + w / 2 + 10, yy), l, font=f, fill=GOLD_L + (255,), anchor="mm"); yy += 50
    d.text((x + w / 2 + 10, y + h - 60), year, font=font(EN_SERIF_I, 32), fill=IVORY + (255,), anchor="mm")


def debate(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    left_a = ramp(T, 0, 0.5)
    right_a = g.r("dalrymple", 0, 0.5)
    lay = new(); d = ImageDraw.Draw(lay)
    _book(d, 90, 380, 400, 520, "The Company-State", "Stern · 2011", (40, 60, 90))
    comp(img, lay, left_a)
    label(img, (290, 960), "菲利普·斯特恩", size=40, color=GOLD_L, a=left_a, fontspec=SERIF_B)
    label(img, (290, 1030), "“公司国家”", size=36, a=left_a)
    label(img, (290, 1100), "17世纪起就是政治体", size=32, color=BLUE_L, a=g.r("stern2", 0.3), box=(0, 0, 0, 170))
    lay = new(); d = ImageDraw.Draw(lay)
    _book(d, 590, 380, 400, 520, "The Anarchy", "Dalrymple · 2019", (90, 40, 34))
    comp(img, lay, right_a)
    label(img, (790, 960), "威廉·达尔林普尔", size=40, color=GOLD_L, a=right_a, fontspec=SERIF_B)
    label(img, (790, 1030), "《无政府》", size=36, a=right_a)
    label(img, (790, 1100), "商业公司滑向帝国", size=32, color=RED_L, a=g.r("dalrymple", 1.0), box=(0, 0, 0, 170))
    if g.seen("debate"):
        title_card(img, "？", None, a=g.r("debate"), y=650, size=160, color=WHITE)
        label(img, (W / 2, 1230), "先记住这个问题", size=40, color=GOLD_L, a=g.r("debate", 0.5), box=(0, 0, 0, 170))


GROUPS = {
    "charter": (charter, ["charter", "seal", "name"]),
    "world_route": (world_route, ["monopoly", "route0", "route", "risk"]),
    "shares": (shares, ["shares"]),
    "voc": (voc, ["voc", "voyages"]),
    "powers": (powers, ["seed", "powers"]),
    "debate": (debate, ["stern", "stern2", "dalrymple", "debate"]),
}
