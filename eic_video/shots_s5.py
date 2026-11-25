# -*- coding: utf-8 -*-
"""Scene 5: famine, the revenue letter, the money flows, crisis & Parliament, Clive/Smith/Mencius, the command lag."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *
from kit import *
from shots_s0 import _east_india_house


def _q(cue):
    from script_data import SCENES
    for s_ in SCENES:
        for d_ in s_["lines"]:
            if d_.get("cue") == cue:
                return d_
    return None


@functools.lru_cache(maxsize=1)
def _cracked_earth():
    rng = np.random.default_rng(8)
    h0, h1 = 300, 1340
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    arr = np.zeros((H, W, 4), np.uint8)
    n = np.asarray(noise_tex(41), np.float32) / 255
    base = np.array([96, 74, 50], np.float32)
    arr[..., :3] = np.clip(base * (0.75 + 0.4 * n[..., None]), 0, 255).astype(np.uint8)
    arr[..., 3] = 255
    img = Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(img)
    # crack network from random seeds (Voronoi-ish edges via nearest-seed boundaries)
    pts = rng.random((70, 2)) * [W, H]
    ys, xs = np.mgrid[0:H:6, 0:W:6]
    dd = ((xs[..., None] - pts[:, 0]) ** 2 + (ys[..., None] - pts[:, 1]) ** 2)
    srt = np.sort(dd, axis=-1)
    edge = (np.sqrt(srt[..., 1]) - np.sqrt(srt[..., 0])) < 7
    em = Image.fromarray((edge * 255).astype(np.uint8), "L").resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1))
    dark = Image.new("RGBA", (W, H), (30, 20, 14, 255)); dark.putalpha(em)
    img.alpha_composite(dark)
    v = Image.new("RGBA", (W, H), (0, 0, 0, 255)); v.putalpha(vignette_mask(1.0))
    img.alpha_composite(v)
    sky = new(); sd = ImageDraw.Draw(sky)
    sd.rectangle((0, 0, W, 520), fill=(150, 120, 80, 255))
    m = Image.linear_gradient("L").resize((W, 520)).transpose(Image.FLIP_TOP_BOTTOM)
    sk = Image.new("RGBA", (W, 520), (170, 140, 90, 255)); sk.putalpha(m.point(lambda v: int(v * 0.0 + 255 - v)))
    img.alpha_composite(sk, (0, 0))
    sun = new(); ImageDraw.Draw(sun).ellipse((W / 2 - 90, 330, W / 2 + 90, 510), fill=(250, 230, 190, 255))
    img.alpha_composite(sun.filter(ImageFilter.GaussianBlur(16)))
    return img


def famine(img, g):
    T = g.T
    img.alpha_composite(_cracked_earth())
    dark = g.r("toll", 0, 0.6) * 0.75
    if dark:
        img.alpha_composite(Image.new("RGBA", (W, H), (8, 8, 10, int(255 * dark))))
    if not g.seen("toll"):
        title_card(img, "1769", "孟加拉 · 比哈尔：雨季几乎无雨", a=g.r("drought", 0, 0.6), y=760, size=110, sub_size=40)
        label(img, (W / 2, 1150), "1770 · 大饥荒", size=50, color=WHITE, a=g.r("drought", 2.2, 0.6), fontspec=SERIF_B, box=(60, 20, 10, 200))
    if g.seen("toll") and not g.seen("remit"):
        c = g.ct("toll")
        title_card(img, "死亡人数：没有定论", None, a=ramp(c, 0, 0.5), y=480, size=60)
        lay = new(); d = ImageDraw.Draw(lay)
        x0, x1, y = 120, 960, 800
        grad = Image.linear_gradient("L").rotate(90, expand=True).resize((x1 - x0, 60))
        bar = Image.new("RGBA", (x1 - x0, 60), (200, 160, 110, 255)); bar.putalpha(grad.point(lambda v: 60 + int(v * 0.7)))
        lay.alpha_composite(bar, (x0, y - 30))
        comp(img, lay, ramp(c, 0.6, 0.8))
        for (fr, txt, sub) in [(0.0, "约100万+", "现代学者（如 Datta、Dyson）"), (1.0, "约1000万", "据“三分之一”推算（Hunter）")]:
            x = x0 + (x1 - x0) * fr
            label(img, (x, y - 90), txt, size=44, color=GOLD_L, a=ramp(c, 1.2 + fr, 0.5), fontspec=SERIF_B)
            label(img, (min(max(x, 260), 820), y + 90), sub, size=28, color=IVORY, a=ramp(c, 1.6 + fr, 0.5))
        label(img, (W / 2, 1080), "当时公司的说法：三分之一人口", size=36, a=ramp(c, 3.0, 0.5), box=(0, 0, 0, 170))
    if g.seen("remit"):
        c = g.ct("remit")
        title_card(img, "饥荒那一年", None, a=ramp(c, 0, 0.5), y=500, size=60)
        hbar(img, 120, 720, 840, 60, 0.05 * ramp(c, 0.8, 0.8), (120, 180, 120), label_l="田赋减免", label_r="不到 5%", lsize=40)
        hbar(img, 120, 920, 840, 60, 0.10 * ramp(c, 2.4, 0.8), RED, label_l="第二年 · 加征", label_r="+10%", lsize=40, a=ramp(c, 2.0, 0.4))
        label(img, (W / 2, 1120), "据 W. W. Hunter 整理的公司档案（1868）", size=28, color=(190, 180, 160), a=ramp(c, 1.0, 0.5))


def hastings_doc(img, g):
    img.alpha_composite(bg_copy(tint=(40, 30, 20)))
    T = g.T
    a_doc = 1 - g.r("q_hastings", 0, 0.5)
    p = parchment(700, 820, seed=19)
    if a_doc > 0:
        pl = p.copy(); d = ImageDraw.Draw(pl)
        d.text((350, 90), "Fort William", font=font(EN_SERIF_I, 46), fill=(70, 45, 30, 255), anchor="mm")
        d.text((350, 150), "3rd November 1772", font=font(EN_SERIF_I, 34), fill=(70, 45, 30, 255), anchor="mm")
        for k in range(12):
            d.line((80, 240 + k * 42, 620 - (k % 3) * 40, 240 + k * 42), fill=(120, 90, 60, 200), width=3)
        d.text((560, 760), "W. Hastings", font=font(EN_SERIF_I, 40), fill=(70, 45, 30, 255), anchor="mm")
        comp(img, pl, ramp(T, 0, 0.5) * a_doc, ((W - 700) / 2, 380))
        if g.seen("doc"):
            label(img, (W / 2, 1270), "加尔各答参事会 → 伦敦董事会", size=36, color=GOLD_L, a=g.r("doc", 0.5) * a_doc, box=(0, 0, 0, 180))
    if g.seen("q_hastings"):
        c = g.ct("q_hastings")
        q = _q("q_hastings")
        quote_card(img, q["q"], q["t"].strip("“”"), ramp(c, 0, 0.5), c / max(1, g.cue_len("q_hastings") * 0.95), a=1 - g.r("doc2", 0, 0.5))
    if g.seen("doc2"):
        c = g.ct("doc2")
        for i, (nm, arrow, col, val) in enumerate([("人口", "↓", (170, 170, 190), "至少 1/3"), ("净征收", "↑", RED_L, "超过1768年")]):
            x = 300 + i * 480
            a = ramp(c, 0.2 + i * 0.6, 0.4)
            label(img, (x, 600), nm, size=56, color=WHITE, a=a, fontspec=SERIF_B)
            label(img, (x, 790), arrow, size=200, color=col, a=a, fontspec=SANS_B)
            label(img, (x, 980), val, size=40, color=col, a=a, box=(0, 0, 0, 170))


def flows(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    a1 = 1 - g.r("nabob", 0, 0.5) * 0.85
    node(img, (W / 2, 420), "孟加拉税收", None, color=GOLD, a=ramp(T, 0, 0.4) * a1, w=420)
    outs = [("股东分红", (200, 1050), GOLD_L), ("军费", (W / 2, 1100), (170, 170, 190)), ("职员口袋", (880, 1050), RED_L)]
    for i, (nm, (x, y), col) in enumerate(outs):
        a = ramp(T, 1.0 + i * 1.2, 0.5) * a1
        w_ = [16, 24, 40][i]
        path = bezier((W / 2, 490), ((W / 2 + x) / 2, 700), (x, y - 80))
        comp(img, thick_arrow(path, w_, col, prog=ramp(T, 1.0 + i * 1.2, 0.8)), a1)
        flow_dots(img, path, col, T, speed=0.4 + 0.3 * i, n=4 + 3 * i, r=6 + 2 * i, a=a)
        node(img, (x, y), nm, None, color=col, a=a, w=280, h=110)
    label(img, (880, 1150), "很大一部分", size=30, color=RED_L, a=ramp(T, 4.0, 0.5) * a1)
    if g.seen("nabob"):
        c = g.ct("nabob")
        title_card(img, "“纳勃布” Nabob", "发了财回国的公司职员", a=ramp(c, 0, 0.5), y=520, size=72)
        lay = new(); d = ImageDraw.Draw(lay)
        # manor
        d.rectangle((140, 860, 520, 1100), fill=(150, 138, 118, 255))
        d.polygon([(120, 860), (330, 740), (540, 860)], fill=(90, 70, 60, 255))
        for k in range(4):
            d.rectangle((170 + k * 90, 900, 220 + k * 90, 980), fill=(230, 180, 90, 255))
        d.rectangle((300, 1010, 360, 1100), fill=(60, 44, 30, 255))
        # parliament seat
        d.rounded_rectangle((640, 900, 940, 1080), radius=20, fill=(40, 90, 60, 255))
        d.rectangle((640, 1060, 940, 1110), fill=(30, 70, 46, 255))
        comp(img, lay, ramp(c, 0.4, 0.5))
        label(img, (330, 1160), "买庄园", size=40, color=GOLD_L, a=ramp(c, 0.8, 0.4), fontspec=SERIF_B)
        label(img, (790, 1160), "买议席", size=40, color=GOLD_L, a=ramp(c, 1.4, 0.4), fontspec=SERIF_B)


def crisis(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    a1 = 1 - g.r("regulating", 0, 0.5)
    if a1 > 0:
        title_card(img, "1772 · 信用危机", None, a=ramp(T, 0, 0.5) * a1, y=420, size=64)
        pts = [(120, 820), (250, 760), (380, 700), (500, 640), (580, 610), (650, 700), (720, 880), (800, 1000), (900, 1060), (960, 1080)]
        lay = new(); d = ImageDraw.Draw(lay)
        d.line((110, 560, 110, 1120, 980, 1120), fill=(200, 200, 200, 160), width=3)
        d.line(cut_polyline(pts, ramp(T, 0.3, 2.5)), fill=RED_L + (255,), width=8, joint="curve")
        comp(img, lay, a1)
        label(img, (300, 1170), "公司股价（示意）", size=30, color=IVORY, a=a1 * ramp(T, 0.5, 0.4))
        label(img, (760, 620), "周转不灵 → 向政府求援", size=36, color=WHITE, a=a1 * ramp(T, 2.6, 0.5), box=(110, 20, 16, 210))
    if g.seen("regulating"):
        c = g.ct("regulating")
        a2 = 1 - g.r("tea", 0, 0.5)
        title_card(img, "1773", None, a=ramp(c, 0, 0.4) * a2, y=380, size=90)
        counter(img, (W / 2, 560), 1400000 * ramp(c, 0.3, 1.5), prefix="借款 £", size=72, a=a2 * ramp(c, 0.3, 0.3))
        stamp(img, "《管理法》", (W / 2, 740), ramp(c, 2.2, 0.6) * a2, color=GOLD, size=64, angle=0)
        node(img, (300, 960), "孟加拉总督", "首任：黑斯廷斯", color=GOLD, a=ramp(c, 3.2, 0.4) * a2, w=380)
        node(img, (780, 960), "最高法院", "设在加尔各答", color=GOLD, a=ramp(c, 4.0, 0.4) * a2, w=380)
    if g.seen("tea"):
        c = g.ct("tea")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 900, W, 1340), fill=(26, 46, 64, 255))
        for k in range(12):
            d.line((k * 95, 950 + (k % 3) * 60, k * 95 + 60, 950 + (k % 3) * 60), fill=(70, 100, 125, 255), width=3)
        d.rectangle((0, 820, 520, 900), fill=(80, 60, 40, 255))
        comp(img, lay, ramp(c, 0, 0.5))
        lay = new(); d = ImageDraw.Draw(lay)
        for k in range(5):
            p = clamp01((c - 1.2 - k * 0.5) / 1.2)
            if p <= 0:
                continue
            x = 360 + k * 70 + p * 160
            y = 780 + 260 * p * p - 120 * p
            d.rectangle((x - 34, y - 28, x + 34, y + 28), fill=(140, 100, 60, 255), outline=(60, 40, 20, 255), width=3)
            d.text((x, y), "TEA", font=font(EN_SERIF_B, 22), fill=(40, 26, 14, 255), anchor="mm")
            if p >= 1:
                d.ellipse((x - 60, 1010, x + 60, 1040), outline=(200, 220, 230, 200), width=3)
        comp(img, lay)
        title_card(img, "《茶叶法》1773", "几个月后 · 波士顿倾茶", a=ramp(c, 0.2, 0.5), y=520, size=66, sub_size=40)


def clive_q(img, g):
    img.alpha_composite(bg_copy(tint=(60, 45, 10)))
    T = g.T
    a1 = 1 - g.r("q_clive", 0, 0.5)
    lay = new(); d = ImageDraw.Draw(lay)
    # vault arches with gold piles
    for k in range(3):
        x = 200 + k * 340
        d.rectangle((x - 140, 640, x + 140, 1120), fill=(34, 30, 26, 255))
        d.pieslice((x - 140, 520, x + 140, 760), 180, 360, fill=(34, 30, 26, 255))
        for j in range(16):
            coin(d, x - 100 + (j % 6) * 40, 1090 - (j // 6) * 34 - (j % 2) * 8, 22)
        d.polygon([(x - 60, 1000), (x - 30, 960), (x, 1000)], fill=(80, 170, 120, 255))
        d.polygon([(x + 20, 990), (x + 45, 950), (x + 70, 990)], fill=(200, 50, 60, 255))
    comp(img, lay, ramp(T, 0, 0.5) * a1)
    if g.seen("clive_q0"):
        c = g.ct("clive_q0")
        items = ["一位君主 · 听凭发落", "银行家 · 争相讨好", "满库金银 · 只为他开"]
        for i, t_ in enumerate(items):
            label(img, (W / 2, 400 + i * 70), t_, size=36, color=GOLD_L, a=ramp(c, 3.0 + i * 1.0, 0.4) * a1, box=(0, 0, 0, 170))
        label(img, (W / 2, 1200), "议会质询 · 克莱武答辩", size=34, a=ramp(c, 0.3, 0.4) * a1, box=(0, 0, 0, 170))
    if g.seen("q_clive"):
        c = g.ct("q_clive")
        q = _q("q_clive")
        quote_card(img, q["q"], q["t"].strip("“”"), ramp(c, 0, 0.5), c / max(1, g.cue_len("q_clive") * 0.9))


def smith2(img, g):
    img.alpha_composite(bg_copy(tint=(40, 30, 20)))
    T = g.T
    q = _q("q_smith2")
    zh = "很奇特的政府：每个官员都想尽快离开；他带着财产走了，这个国家哪怕被地震吞没，也与他无关。"
    quote_card(img, q["q"], zh, ramp(T, 0, 0.5), T / max(1, g.cue_len("q_smith2") * 0.9), a=1 - 0.6 * g.r("system", 0, 0.5), y_center=760)
    if g.seen("system"):
        c = g.ct("system")
        lay = new(); d = ImageDraw.Draw(lay)
        d.rectangle((0, 1130, W, 1340), fill=(8, 10, 16, 230))
        comp(img, lay, ramp(c, 0, 0.4))
        label(img, (300, 1235), "不是个人品格", size=44, color=(180, 180, 180), a=ramp(c, 0.4, 0.4), fontspec=SERIF_B)
        label(img, (780, 1235), "而是位置与制度", size=44, color=GOLD_L, a=ramp(c, 1.6, 0.4), fontspec=SERIF_B)
        lay = new(); d = ImageDraw.Draw(lay)
        d.line((150, 1240, 450, 1232), fill=(220, 60, 50, 255), width=6)
        comp(img, lay, ramp(c, 1.2, 0.3))


def mencius(img, g):
    img.alpha_composite(bg_copy(tint=(50, 40, 20)))
    T = g.T
    q = _q("q_mencius")
    quote_card(img, q["q"], "上上下下都在争夺私利，国家就危险了。", ramp(T, 0, 0.5), g.r("mencius2", 0, 2.5), y_center=780)


def lag(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    L = (W / 2, 470); C = (W / 2, 1120)
    node(img, L, "伦敦董事会", "利德贺街", color=GOLD, a=ramp(T, 0, 0.4), w=400)
    node(img, C, "加尔各答", "总督 · 职员", color=RED_L, a=ramp(T, 0.3, 0.4), w=400)
    path = [(L[0] - 120, L[1] + 70), (L[0] - 180, (L[1] + C[1]) / 2), (C[0] - 120, C[1] - 70)]
    p = bezier(*path, 30)
    lay = new(); d = ImageDraw.Draw(lay)
    dashed_line(d, p, BLUE_L + (230,), width=5)
    comp(img, lay, ramp(T, 0.6, 0.4))
    # slow ship carrying orders
    sp = (T * 0.06) % 1.0
    x, y = point_at(p, sp)
    lay = new(); ship(ImageDraw.Draw(lay), x, y, 80); comp(img, lay, ramp(T, 0.8, 0.4))
    label(img, (230, 800), "命令", size=40, color=BLUE_L, a=ramp(T, 1.0, 0.4), fontspec=SERIF_B)
    label(img, (230, 860), "单程 5–6 个月", size=32, a=ramp(T, 1.4, 0.4), box=(0, 0, 0, 170))
    # money: fast to pockets
    pocket = (860, 820)
    mp = bezier((C[0] + 140, C[1] - 60), (C[0] + 300, 1000), pocket, 20)
    flow_dots(img, mp, GOLD, T, speed=1.8, n=6, r=10, a=ramp(T, 3.0, 0.4))
    node(img, pocket, "个人口袋", None, color=GOLD, a=ramp(T, 3.0, 0.4), w=260, h=100)
    label(img, (860, 720), "钱：当场到手", size=34, color=GOLD_L, a=ramp(T, 3.4, 0.4), box=(0, 0, 0, 170))
    if g.seen("india_act"):
        c = g.ct("india_act")
        node(img, (W / 2, 470), "伦敦董事会", "利德贺街", color=GOLD, a=0)
        node(img, (830, 330 + 0 * c), "监督委员会", "1784《印度法》", color=(150, 200, 255), a=ramp(c, 0.3, 0.5), w=380, glow_=True)
        comp(img, thick_arrow([(660, 360), (W / 2 + 150, 430)], 18, (150, 200, 255), prog=ramp(c, 0.8, 0.6)))
        label(img, (W / 2, 1270), "公司重大决策 · 受英国政府管束", size=36, color=WHITE, a=ramp(c, 1.4, 0.4), box=(20, 40, 90, 210))


GROUPS = {
    "famine": (famine, ["drought0", "drought", "toll", "remit"]),
    "hastings_doc": (hastings_doc, ["doc0", "doc", "q_hastings", "doc2"]),
    "flows": (flows, ["flows", "nabob"]),
    "crisis": (crisis, ["crisis", "regulating", "tea"]),
    "clive_q": (clive_q, ["clive_q0", "q_clive"]),
    "smith2": (smith2, ["q_smith2", "system"]),
    "mencius": (mencius, ["q_mencius", "mencius2"]),
    "lag": (lag, ["lag", "india_act"]),
}
