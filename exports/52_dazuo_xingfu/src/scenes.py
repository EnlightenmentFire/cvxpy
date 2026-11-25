# -*- coding: utf-8 -*-
"""各场景画面。每个场景: bg() 返回静态底图（RGBA, 缓存）；draw(img, t, L, dur) 在其上画动态层。
L: 本场景各句 (start, end)，场景内时间（秒）。"""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *

SUB_Y = 1440          # 字幕区上沿
HEAD_Y = 190          # 标题区


# ================================================================ 通用部件
def at(L, i, off=0.0):
    i = min(i, len(L) - 1)
    return L[i][0] + off


def ap(t, L, i, off=0.0, d=0.6):
    return fade(t, at(L, i, off), d)


def headline(img, text, a, y=HEAD_Y, size=76, color=INK, kind="serif"):
    if a <= 0:
        return
    sp = text_sprite(text, size, kind, "Bold", color)
    put(img, sp, (W / 2, y + (1 - a) * 14), a, "mt")


def tag(img, text, a, y, x=None, size=34, color=ZHU, fill=None):
    """朱框标签：如【实证 · 相关研究】"""
    if a <= 0:
        return
    sp = _tag_sprite(text, size, color, fill)
    put(img, sp, (W / 2 if x is None else x, y), a, "mt" if x is None else "lt")


@functools.lru_cache(None)
def _tag_sprite(text, size, color, fill):
    f = font(size, "serif", "SemiBold")
    tw = int(f.getlength(text))
    w, h = tw + size * 1.4, int(size * 1.75)
    img = Image.new("RGBA", (int(w), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if fill:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=8, fill=fill + (235,))
        d.text((size * 0.7, size * 0.22), text, font=f, fill=PAPER + (255,))
    else:
        d.rounded_rectangle([1, 1, w - 2, h - 2], radius=8, outline=color + (230,), width=3)
        d.text((size * 0.7, size * 0.22), text, font=f, fill=color + (255,))
    return img


@functools.lru_cache(None)
def card_sprite(w, h, shade=0.0, radius=18, tone=(246, 241, 230)):
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([24, 28, w + 24, h + 28], radius=radius, fill=(0, 0, 0, 60))
    img = img.filter(ImageFilter.GaussianBlur(9))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=radius, fill=tone + (250,), outline=(200, 190, 170, 255), width=2)
    return img


def card(img, x, y, w, h, a=1.0, tone=(246, 241, 230)):
    put(img, card_sprite(int(w), int(h), tone=tone), (x - 20, y - 20), a)


def text(img, s, x, y, size=44, a=1.0, color=INK, anchor="lt", kind="serif", weight="Bold"):
    if a <= 0:
        return
    put(img, text_sprite(s, size, kind, weight, color), (x, y), a, anchor)


def ink_bar(img, x, y, w, h, a=1.0, color=INK, seed=0):
    """水墨笔触的横条（干笔边缘）。"""
    if a <= 0 or w < 2:
        return
    sp = _bar_sprite(int(w), int(h), color, seed)
    put(img, sp, (x, y), a)


@functools.lru_cache(maxsize=512)
def _bar_sprite(w, h, color, seed):
    r = rng(seed + w)
    m = np.zeros((h, w), np.float32)
    yy = np.linspace(-1, 1, h)[:, None]
    edge = 1 - np.abs(yy) ** 6
    m[:] = edge
    # 干笔：横向丝纹
    streak = r.random((h, 1)) * 0.5 + 0.55
    m *= np.clip(streak + r.normal(0, 0.08, (h, w)), 0, 1)
    # 起收笔
    xs = np.arange(w)[None, :]
    m *= np.clip(xs / max(4, h * 0.6), 0, 1) ** 0.6
    m *= np.clip((w - xs) / max(4, h * 0.3), 0, 1) ** 0.4
    img = np.dstack([np.full((h, w), c, np.uint8) for c in color] + [(m * 235).astype(np.uint8)])
    return Image.fromarray(img, "RGBA").filter(ImageFilter.GaussianBlur(0.7))


def ink_dot(d, x, y, r, color, alpha):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (int(alpha),))


def arrow(d, x0, y0, x1, y1, color=INK, width=6, alpha=230, head=22, dashed=False):
    c = color + (int(alpha),)
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 2:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    ex, ey = x1 - ux * head * 0.8, y1 - uy * head * 0.8
    if dashed:
        n = int(L / 26)
        for k in range(n):
            if k % 2 == 0:
                a0, a1 = k / n, min((k + 1) / n, 1)
                d.line([(x0 + (ex - x0) * a0, y0 + (ey - y0) * a0), (x0 + (ex - x0) * a1, y0 + (ey - y0) * a1)], fill=c, width=width)
    else:
        d.line([(x0, y0), (ex, ey)], fill=c, width=width)
    px, py = -uy, ux
    d.polygon([(x1, y1), (ex - ux * head * 0.4 + px * head * 0.55, ey - uy * head * 0.4 + py * head * 0.55),
               (ex - ux * head * 0.4 - px * head * 0.55, ey - uy * head * 0.4 - py * head * 0.55)], fill=c)


def soft_cover(img, y0, y1, a, feather=50):
    if a <= 0:
        return
    m = np.zeros((H, 1), np.float32)
    yy = np.arange(H)[:, None]
    m = np.clip(np.minimum((yy - (y0 - feather)) / feather, ((y1 + feather) - yy) / feather), 0, 1)
    al = (np.repeat(m, W, 1) * 250 * a).astype(np.uint8)
    c = np.zeros((H, W, 4), np.uint8); c[..., :3] = paper(1); c[..., 3] = al
    img.alpha_composite(Image.fromarray(c, "RGBA"))


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def stamp(img, s, x, y, t, t0, size=40, rot=-6, color=ZHU):
    """朱印盖下：先大后小、略旋转。"""
    if t < t0:
        return
    k = ease((t - t0) / 0.22)
    sc = 1.6 - 0.6 * k
    sp = _tag_sprite(s, size, color, None)
    sp2 = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR).rotate(rot, expand=True, resample=Image.BICUBIC)
    put(img, sp2, (x, y), min(1, k * 1.4), "mm")


# ================================================================ 背景
@functools.lru_cache(None)
def bg_courtyard():
    b = paper_img(1).convert("RGBA")
    b.alpha_composite(glow(330, 640, 430, GOLD, 0.38))
    b.alpha_composite(mountains(3, 4, 560, 1150))
    b.alpha_composite(mist(980, 1260, 0.92))
    # 石台
    st = layer(); d = ImageDraw.Draw(st)
    d.ellipse([170, 1290, 700, 1360], fill=INK2 + (60,))
    b.alpha_composite(st.filter(ImageFilter.GaussianBlur(10)))
    return b


@functools.lru_cache(None)
def bg_plain(seed=2, mtn=True, glow_y=None):
    b = paper_img(seed).convert("RGBA")
    if glow_y:
        b.alpha_composite(glow(540, glow_y, 520, GOLD, 0.22))
    if mtn:
        m = mountains(seed + 10, 3, 1050, 1500, 0.35)
        a = m.getchannel("A").point(lambda v: int(v * 0.45)); m = m.copy(); m.putalpha(a)
        b.alpha_composite(m)
        b.alpha_composite(mist(1330, 1700, 0.9))
    return b


@functools.lru_cache(None)
def bg_scroll(top=430, bottom=1360, seed=4):
    """卷轴：浅色绢面 + 上下木轴。"""
    b = bg_plain(seed, True).copy()
    l = layer(); d = ImageDraw.Draw(l)
    d.rectangle([70, top, W - 70, bottom], fill=(244, 238, 224, 255))
    d.rectangle([70, top, W - 70, bottom], outline=(170, 150, 120, 255), width=2)
    d.rectangle([84, top + 14, W - 84, bottom - 14], outline=(200, 180, 150, 255), width=1)
    for yy in (top - 18, bottom - 4):
        d.rounded_rectangle([40, yy, W - 40, yy + 22], radius=10, fill=(96, 64, 40, 255))
        d.ellipse([22, yy - 4, 52, yy + 26], fill=(70, 46, 30, 255)); d.ellipse([W - 52, yy - 4, W - 22, yy + 26], fill=(70, 46, 30, 255))
    sh = layer(); ImageDraw.Draw(sh).rectangle([80, top + 12, W - 60, bottom + 16], fill=(0, 0, 0, 70))
    b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    b.alpha_composite(l)
    return b


@functools.lru_cache(None)
def bg_alley():
    """收束：街巷屋檐剪影。"""
    b = paper_img(9).convert("RGBA")
    b.alpha_composite(glow(540, 760, 600, GOLD, 0.30))
    b.alpha_composite(mountains(21, 2, 650, 950, 0.3))
    l = layer(); d = ImageDraw.Draw(l)
    r = rng(11)
    # 左右两排屋舍（近大远小，透视收向中间）
    for side in (-1, 1):
        for k in range(6):
            f = k / 5
            x_out = 540 + side * (540 - 380 * f) * 1.05
            x_in = 540 + side * (300 - 210 * f)
            top = 760 + 160 * f
            roof = top - 120 * (1 - f) - 40
            bot = 1330 - 360 * f
            a = int(220 - 150 * f)
            xa, xb = sorted([x_in, x_out])
            d.rectangle([xa, top, xb, bot], fill=INK2 + (int(a * 0.55),))
            d.polygon([(xa - 30, top + 6), (xb + 30, top + 6), (xb + 8, roof), (xa - 8, roof)], fill=INK + (a,))
            # 檐角上翘
            d.line([(xa - 30, top + 6), (xa - 46, top - 10)], fill=INK + (a,), width=4)
            d.line([(xb + 30, top + 6), (xb + 46, top - 10)], fill=INK + (a,), width=4)
            # 门窗留白
            d.rectangle([(xa + xb) / 2 - 20 * (1 - f * 0.6), bot - 120 * (1 - f * 0.6), (xa + xb) / 2 + 20 * (1 - f * 0.6), bot], fill=PAPER + (int(a * 0.5),))
    # 石板路
    for k in range(14):
        y = 1000 + k ** 1.55 * 9
        w = 150 + k * 40
        d.line([(540 - w, y), (540 + w, y)], fill=INK2 + (35,), width=2)
    b.alpha_composite(l.filter(ImageFilter.GaussianBlur(1.2)))
    b.alpha_composite(mist(1200, 1500, 0.6))
    return b


# ================================================================ S1 钩子
def notif(img, x, y, msg, a=1.0, sub="此刻"):
    if a <= 0:
        return
    w, h = 470, 150
    card(img, x, y, w, h, a, tone=(250, 248, 243))
    l = layer(); d = ImageDraw.Draw(l)
    d.rounded_rectangle([x + 24, y + 26, x + 74, y + 76], radius=12, fill=ZHU + (int(230 * a),))
    d.ellipse([x + 38, y + 40, x + 60, y + 62], outline=PAPER + (int(255 * a),), width=4)
    img.alpha_composite(l)
    text(img, sub, x + 92, y + 22, 28, a, GREY, weight="Medium")
    text(img, "刚刚", x + w - 80, y + 22, 26, a, GREY, weight="Regular")
    text(img, msg, x + 92, y + 70, 42, a, INK)


@functools.lru_cache(None)
def _hook_static():
    b = bg_courtyard().copy()
    fig, xy = seated_figure(410, 1330, 0.74)
    b.alpha_composite(fig, xy)
    return b


def draw_hook(img, t, L, dur):
    img.alpha_composite(bamboo(t, 5, 960, 3, INK, 0.85))
    # 标题从第一帧起就在
    headline(img, "人有将近一半的时间", 1.0, 170, 74)
    k = ease(t / 0.5)
    headline(img, "心不在焉", 1.0, 270, 118, ZHU)
    # 手机提问：第一帧就在
    pop = 1 + 0.06 * math.sin(min(t, 0.5) / 0.5 * math.pi)
    notif(img, 560, 470, "你现在在想什么？", 1.0)
    # 三个问题
    qs = ["① 你现在感觉怎么样？", "② 你在做什么？", "③ 你在想眼前这件事吗？"]
    if len(L) > 1:
        s0, e0 = L[1]
        card(img, 560, 650, 470, 215, fade(t, s0, 0.4), tone=(250, 248, 243))
        for i, q in enumerate(qs):
            tq = s0 + (e0 - s0) * (0.02 + i * 0.3)
            a = fade(t, tq, 0.4)
            text(img, q, 585, 668 + i * 64, 34, a, INK2, weight="SemiBold")
    # 第三句：念头飘走（墨点从头顶飘向右上）
    if len(L) > 2 and t > L[2][0]:
        l = layer(); d = ImageDraw.Draw(l)
        r = rng(3)
        for k2 in range(26):
            ph = (t - L[2][0]) * 0.35 + k2 / 26
            ph = ph % 1.0
            x = 430 + ph * 420 + 40 * math.sin(k2 * 1.7 + t)
            y = 930 - ph * 360 + 30 * math.cos(k2 * 2.3 + t * 0.7)
            rr = 6 + 14 * ph * (0.6 + 0.4 * math.sin(k2))
            ink_dot(d, x, y, rr, INK2, 150 * (1 - ph) * fade(t, L[2][0], 0.8))
        img.alpha_composite(l.filter(ImageFilter.GaussianBlur(2)))
        text(img, "46.9%", 760, 960, 92, fade(t, L[2][0] + 0.4, 0.6), ZHU, "mt", weight="Black")
        text(img, "的时刻在想别的事", 760, 1070, 34, fade(t, L[2][0] + 0.6, 0.6), INK2, "mt")
    if len(L) > 3:
        tag(img, "走神时，人普遍更不快乐", ap(t, L, 3), 1240, size=44, fill=ZHU)


# ================================================================ S1b 结论先行
def draw_verdict(img, t, L, dur):
    headline(img, "每天打坐，会更快乐吗？", ap(t, L, 0, -0.2), 190, 70)
    a = ap(t, L, 1)
    if a > 0:
        text(img, "打坐", 540, 360, 120, a, INK, "mt", weight="Black")
        text(img, "不是幸福的捷径", 540, 520, 96, a, ZHU, "mt", weight="Black")
    # 两栏预告
    a3, a4 = ap(t, L, 2), ap(t, L, 3)
    if a3 > 0:
        card(img, 90, 720, 430, 470, a3)
        text(img, "有帮助", 305, 750, 50, a3, INK, "mt")
        text(img, "小到中等", 305, 820, 32, a3, GREY, "mt", weight="Medium")
        for i, s in enumerate(["焦虑", "抑郁", "疼痛"]):
            text(img, s, 305, 900 + i * 86, 56, ease((t - at(L, 2) - 0.3 - 0.25 * i) / 0.5), INK, "mt")
    if a4 > 0:
        card(img, 560, 720, 430, 470, a4)
        text(img, "证据不足", 775, 750, 50, a4, ZHU, "mt")
        text(img, "让人更开心", 775, 900, 52, a4, INK, "mt")
        text(img, "（积极情绪）", 775, 975, 34, a4, GREY, "mt", weight="Medium")
    tag(img, "Goyal 等，JAMA Internal Medicine，2014", min(a3, 1), 1230, size=28, color=GREY)
    # 本期路线
    a5 = ap(t, L, 4)
    if a5 > 0:
        soft_cover(img, 700, 1290, a5)
        for i, (s, c) in enumerate([("宣传", GREY), ("证据", INK), ("印照", ZHU)]):
            x = 230 + i * 310
            ai = ease((t - at(L, 4) - 0.6 * i) / 0.5)
            l = layer(); d = ImageDraw.Draw(l)
            d.ellipse([x - 120, 860, x + 120, 1100], outline=c + (int(220 * ai),), width=6)
            img.alpha_composite(l)
            text(img, s, x, 925, 76, ai, c, "mt")
            if s == "宣传":
                l = layer(); ImageDraw.Draw(l).line([(x - 100, 1060), (x + 100, 900)], fill=ZHU + (int(200 * ai),), width=8)
                img.alpha_composite(l)


# ================================================================ S2 经验抽样
@functools.lru_cache(None)
def phone_sprite():
    w, h = 470, 860
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([26, 30, w + 26, h + 30], radius=60, fill=(0, 0, 0, 70))
    img = img.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([20, 20, w + 20, h + 20], radius=60, fill=INK + (255,))
    d.rounded_rectangle([36, 36, w + 4, h + 4], radius=48, fill=(247, 243, 234, 255))
    d.rounded_rectangle([w / 2 - 40, 50, w / 2 + 80, 70], radius=10, fill=INK + (255,))
    return img


def draw_sampling(img, t, L, dur):
    headline(img, "经验抽样：在当下就问", ap(t, L, 0, -0.3), 170, 66)
    tag(img, "实证 · 相关研究", ap(t, L, 0), 275, size=32)
    phase2 = at(L, 4)          # 46.9% 起换成点阵
    a_ph = ap(t, L, 0) * (1 - fade(t, phase2 - 0.2, 0.5))
    if a_ph > 0:
        put(img, phone_sprite(), (300, 390), a_ph)
        text(img, "随机提问", 535, 480, 34, a_ph, GREY, "mt", weight="Medium")
        a1 = min(a_ph, ap(t, L, 1))
        text(img, "不靠事后回忆", 535, 560, 44, a1, ZHU, "mt")
        qs = [("你现在感觉怎么样？", "0 ———— 100"), ("你在做什么？", "22 项活动任选"),
              ("你在想眼前以外的事吗？", "否 / 愉快 / 中性 / 不愉快")]
        for i, (q, sub) in enumerate(qs):
            ai = min(a_ph, fade(t, at(L, 3, 0.6 + 0.9 * i), 0.5))
            text(img, q, 535, 680 + i * 160, 36, ai, INK, "mt")
            text(img, sub, 535, 735 + i * 160, 28, ai, GREY, "mt", weight="Medium")
        tag(img, "Killingsworth & Gilbert，Science，2010", min(a_ph, ap(t, L, 2)), 1290, size=28, color=GREY)
        text(img, "2,250 名成年人", 540, 1350, 40, min(a_ph, ap(t, L, 3)), INK, "mt")
    if t > phase2 - 0.2:
        a = fade(t, phase2 - 0.2, 0.5)
        l = layer(); d = ImageDraw.Draw(l)
        k_on = int(min(47, max(0, (t - phase2) / 1.6 * 47)))
        for i in range(100):
            r_, c_ = divmod(i, 10)
            x = 220 + c_ * 71; y = 420 + r_ * 71
            if i < k_on:
                ink_dot(d, x, y, 25, ZHU, 220 * a)
            else:
                ink_dot(d, x, y, 25, INK2, 70 * a)
        img.alpha_composite(l)
        text(img, "46.9%", 540, 1135, 110, a, ZHU, "mt", weight="Black")
        text(img, "的时刻，心在别处", 540, 1265, 40, a, INK, "mt")
        a6 = ap(t, L, 5) * (1 - ap(t, L, 6))
        tag(img, "任何活动中，走神都不低于三成", a6, 1350, size=34)
        if ap(t, L, 6) > 0:
            acts = ["洗碗", "通勤", "工作", "看电视", "聊天"]
            for i, s in enumerate(acts):
                ai = ease((t - at(L, 6) - 0.45 * i) / 0.4) * (1 - ap(t, L, 7))
                text(img, s, 140 + i * 200, 1350, 40, ai, INK2, "mt", weight="SemiBold")
        a8 = ap(t, L, 7)
        if a8 > 0:
            l = layer(); d = ImageDraw.Draw(l)
            arrow(d, 470, 1375, 130, 1375, INK2, 6, 220 * a8)
            arrow(d, 610, 1375, 950, 1375, INK2, 6, 220 * a8)
            img.alpha_composite(l)
            text(img, "昨天", 200, 1320, 40, a8, INK2, "mt")
            text(img, "明天", 880, 1320, 40, a8, INK2, "mt")
            text(img, "此刻", 540, 1345, 46, a8, ZHU, "mt")


# ================================================================ S2b 情绪
def draw_sampling2(img, t, L, dur):
    headline(img, "走神时，心情怎样？", ap(t, L, 0, -0.3), 170, 66)
    phase2 = at(L, 3)
    a_bars = ap(t, L, 0) * (1 - fade(t, phase2 - 0.2, 0.5))
    if a_bars > 0:
        x0 = 860
        text(img, "与“专心眼前”相比的幸福感差值", 540, 330, 34, a_bars, GREY, "mt", weight="Medium")
        l = layer(); d = ImageDraw.Draw(l)
        d.line([(x0, 420), (x0, 1180)], fill=INK + (int(200 * a_bars),), width=4)
        img.alpha_composite(l)
        text(img, "专心眼前 = 0", x0, 1195, 30, a_bars, INK2, "mt", weight="Medium")
        rows = [("想愉快的事", -0.52, 2, "≈ 0（不显著）"), ("想中性的事", -7.2, 1, "−7"), ("想不愉快的事", -23.9, 1, "−24")]
        for i, (lab, v, li, num) in enumerate(rows):
            y = 470 + i * 240
            ai = min(a_bars, fade(t, at(L, li, 0.3 + (0.9 if i == 2 else 0)), 0.5))
            if li == 2:
                ai = min(a_bars, ap(t, L, 2, 0.3))
            grow = ease((t - at(L, li, 0.3 + (0.9 if i == 2 else 0))) / 1.0) if li == 1 else ease((t - at(L, 2, 0.3)) / 1.0)
            wpx = max(6, abs(v) * 26 * grow)
            text(img, lab, 120, y, 44, ai, INK, "lt")
            ink_bar(img, x0 - wpx, y + 70, wpx, 56, ai, ZHU if v < -5 else INK2, seed=i)
            text(img, num, x0 - wpx - 20, y + 74, 40, ai, ZHU if v < -5 else INK2, "rt")
        text(img, "幸福感 0–100 分 · 回归系数 · Science 2010", 540, 1270, 28, a_bars, GREY, "mt", weight="Medium")
    if t > phase2 - 0.2:
        a = fade(t, phase2 - 0.2, 0.6)
        card(img, 110, 380, 860, 360, a)
        text(img, "A Wandering Mind", 540, 430, 66, a, INK, "mt", kind="latin")
        text(img, "Is an Unhappy Mind", 540, 515, 66, a, INK, "mt", kind="latin")
        text(img, "一颗游荡的心，是一颗不快乐的心", 540, 630, 40, a, ZHU, "mt")
        a5 = ap(t, L, 4)
        tag(img, "观察研究，不是实验", a5, 800, size=40)
        a6 = ap(t, L, 5)
        if a6 > 0:
            l = layer(); d = ImageDraw.Draw(l)
            arrow(d, 330, 1010, 750, 1010, INK, 8, 230 * a6)
            arrow(d, 750, 1110, 330, 1110, GREY, 6, 200 * ease((t - at(L, 5) - 1.5) / 0.6), dashed=True)
            img.alpha_composite(l)
            text(img, "走神", 200, 1030, 56, a6, INK, "mm")
            text(img, "不快乐", 890, 1030, 56, a6, INK, "mm")
            text(img, "时间先后提示：多在前", 540, 945, 30, a6, INK2, "mt", weight="Medium")
            text(img, "反过来也可能？", 540, 1135, 30, ease((t - at(L, 5) - 1.5) / 0.6), GREY, "mt", weight="Medium")
        stamp(img, "相关 ≠ 因果", 540, 1300, t, at(L, 6, 0.3), size=54)


# ================================================================ S3 Goyal
def draw_goyal(img, t, L, dur):
    headline(img, "打坐能让人更快乐吗？", ap(t, L, 0, -0.3), 170, 66)
    a2 = ap(t, L, 1)
    if a2 > 0:
        card(img, 120, 320, 840, 200, a2)
        text(img, "JAMA Internal Medicine · 2014", 540, 350, 40, a2, INK, "mt", kind="latin")
        text(img, "系统综述与元分析 · Goyal 等", 540, 425, 38, a2, INK2, "mt")
    tag(img, "实证 · 系统综述", a2, 570, size=32)
    # 漏斗
    a3 = ap(t, L, 2) * (1 - ap(t, L, 3, -0.2))
    if a3 > 0:
        t3 = at(L, 2)
        rows = [("18,753", "篇文献", 860, 0.0), ("47", "项随机对照试验", 600, 1.3), ("3,515", "名参与者", 420, 2.6)]
        for i, (n, lab, w, dt) in enumerate(rows):
            ai = min(a3, ease((t - t3 - dt) / 0.5))
            y = 690 + i * 210
            ink_bar(img, 540 - w / 2, y, w, 150, ai * 0.18, INK, seed=10 + i)
            text(img, n, 540, y + 12, 76, ai, ZHU if i else INK, "mt", weight="Black")
            text(img, lab, 540, y + 105, 32, ai, INK2, "mt", weight="Medium")
    # 主动对照
    a4 = ap(t, L, 3)
    if a4 > 0:
        text(img, "主动对照", 540, 680, 84, a4, ZHU, "mt", weight="Black")
        a5 = ap(t, L, 4)
        for side, lab, sub in ((-1, "冥想组", "正念冥想课程"), (1, "对照组", "健康教育 / 放松训练")):
            x = 540 + side * 245
            ai = a5 if side > 0 else a4
            fig, xy = seated_figure(x, 1150, 0.42, INK if side < 0 else INK2)
            put(img, fig, xy, ai)
            text(img, lab, x, 1180, 48, ai, INK, "mt")
            text(img, sub, x, 1245, 32, ai, GREY, "mt", weight="Medium")
        text(img, "≈", 540, 960, 90, a5, INK2, "mt")
        tag(img, "扣除“被关照”“有期待”的那部分", ap(t, L, 5), 1320, size=36, fill=ZHU)


# ================================================================ S3b 两栏卷轴
def draw_goyal2(img, t, L, dur):
    phaseB = at(L, 8)
    aA = fade(t, -1, 0.1) * (1 - fade(t, phaseB - 0.3, 0.6))
    if aA > 0:
        headline(img, "四十七项严格试验的结论", aA, 170, 62)
        # 左栏
        a1 = min(aA, ap(t, L, 0))
        text(img, "有证据（中等强度）", 305, 470, 40, a1, INK, "mt")
        text(img, "证据不足 / 未见效果", 775, 470, 40, a1, ZHU, "mt")
        l = layer(); ImageDraw.Draw(l).line([(540, 470), (540, 1320)], fill=(170, 150, 120, int(220 * a1)), width=2)
        img.alpha_composite(l)
        rows = [("焦虑", 0.38, 0.22), ("抑郁", 0.30, 0.23), ("疼痛", 0.33, None)]
        for i, (lab, es, es2) in enumerate(rows):
            y = 560 + i * 150
            ai = min(aA, ap(t, L, 1, 0.3 + 0.4 * i))
            text(img, lab, 120, y + 8, 46, ai, INK)
            g = ease((t - at(L, 2, 0.4 * i)) / 0.8)
            wpx = es * 700 * g
            if g > 0:
                ink_bar(img, 240, y + 10, wpx, 48, aA, INK, seed=20 + i)
                text(img, f"{es:.2f}", 250 + wpx, y + 10, 38, aA * g, INK, weight="Black")
            if es2:
                g2 = ease((t - at(L, 3, 0.4 * i)) / 0.8)
                if g2 > 0:
                    ink_bar(img, 240, y + 72, es2 * 700 * g2, 30, aA * 0.75, INK2, seed=30 + i)
                    text(img, f"{es2:.2f}", 250 + es2 * 700 * g2, y + 66, 30, aA * g2, INK2, weight="SemiBold")
        text(img, "深：8 周时效应量   浅：3–6 个月后", 120, 1000, 26, min(aA, ap(t, L, 3)), GREY, weight="Medium")
        # U3 示意
        a5 = min(aA, ap(t, L, 4))
        if a5 > 0:
            l = layer(); d = ImageDraw.Draw(l)
            xs = np.linspace(-3.2, 3.6, 120)
            for mu, c, al in ((0, INK2, 120), (0.3, ZHU, 210)):
                pts = [(110 + (x + 3.2) / 6.8 * 400, 1215 - 160 * math.exp(-(x - mu) ** 2 / 2)) for x in xs]
                d.line(pts, fill=c + (int(al * a5),), width=5)
            d.line([(110 + 3.5 / 6.8 * 400, 1055), (110 + 3.5 / 6.8 * 400, 1215)], fill=ZHU + (int(150 * a5),), width=2)
            img.alpha_composite(l)
            text(img, "灰：对照组   红：练习组", 310, 1222, 22, a5, GREY, "mt", weight="Medium")
            text(img, "≈ 62%", 420, 1060, 34, a5, ZHU, "mt", weight="Black")
        tag(img, "有，但不神奇", min(aA, ap(t, L, 5)), 1275, x=170, size=34, fill=INK)
        # 右栏
        for i, s in enumerate(["积极情绪", "注意力", "睡眠", "体重", "……"]):
            ai = min(aA, ap(t, L, 6, 0.6 + 0.35 * i))
            text(img, s, 775, 570 + i * 105, 46, ai, INK2, "mt")
        a8 = min(aA, ap(t, L, 7))
        if a8 > 0:
            card(img, 580, 1100, 390, 220, a8)
            text(img, "不优于", 775, 1120, 44, a8, ZHU, "mt")
            text(img, "药物 · 运动", 775, 1185, 36, a8, INK, "mt")
            text(img, "其他行为疗法", 775, 1240, 36, a8, INK, "mt")
    if t > phaseB - 0.3:
        a = fade(t, phaseB - 0.3, 0.7)
        text(img, "打坐", 540, 420, 130, a, INK, "mt", weight="Black")
        text(img, "不是幸福的捷径", 540, 600, 104, a, ZHU, "mt", weight="Black")
        l = layer(); d = ImageDraw.Draw(l)
        g = ease((t - phaseB - 0.5) / 0.8)
        brush_line(d, [(170, 760), (170 + 740 * g, 752)], 14, 6, ZHU, int(200 * a))
        img.alpha_composite(l)
        text(img, "越严格的研究，效果越朴素", 540, 840, 44, ap(t, L, 9), INK2, "mt")
        text(img, "温和的练习  ≠  特效药", 540, 960, 56, ap(t, L, 10), INK, "mt")
    a12 = ap(t, L, 11)
    if a12 > 0:
        card(img, 110, 1110, 860, 210, a12, tone=(250, 240, 232))
        text(img, "如有焦虑、抑郁等困扰", 540, 1140, 44, a12, ZHU, "mt")
        text(img, "请寻求专业帮助 · 冥想不能替代治疗", 540, 1215, 38, a12, INK, "mt")


# ================================================================ S4 慈心禅
def draw_metta(img, t, L, dur):
    headline(img, "积极情绪，能练出来吗？", ap(t, L, 0, -0.3), 170, 66)
    a2 = ap(t, L, 1)
    tag(img, "Fredrickson 等 · JPSP 2008 · 实证 · 单项研究", a2, 280, size=28, color=GREY)
    phase2 = at(L, 4)
    aA = ap(t, L, 1) * (1 - fade(t, phase2 - 0.2, 0.5))
    if aA > 0:
        # 坐者与涟漪
        l = layer(); d = ImageDraw.Draw(l)
        for k in range(5):
            ph = ((t * 0.18) + k / 5) % 1
            r = 120 + ph * 420
            d.ellipse([540 - r, 900 - r * 0.62, 540 + r, 900 + r * 0.62], outline=ZHU + (int(150 * (1 - ph) * aA),), width=4)
        img.alpha_composite(l.filter(ImageFilter.GaussianBlur(1.5)))
        fig, xy = seated_figure(540, 1080, 0.7)
        put(img, fig, xy, aA)
        wishes = ["愿我平安", "愿你平安", "愿众生离苦得乐"]
        for i, s in enumerate(wishes):
            ai = min(aA, ap(t, L, 2, 1.2 + 1.0 * i))
            text(img, s, 540, 1150 + i * 70, 46 if i < 2 else 50, ai, INK if i < 2 else ZHU, "mt", kind="kai", weight="Bold")
        a4 = min(aA, ap(t, L, 3))
        if a4 > 0:
            soft_cover(img, 1140, 1390, a4, 30)
            text(img, "四无量心", 540, 1150, 36, a4, GREY, "mt", weight="Medium")
            for i, ch in enumerate("慈悲喜舍"):
                sp = seal(ch, 92, ZHU if i == 0 else INK2, seed=40 + i)
                put(img, sp, (240 + i * 200, 1215), a4 * (1 if i == 0 else 0.55), "mt")
    if t > phase2 - 0.2:
        a = fade(t, phase2 - 0.2, 0.5)
        text(img, "139", 540, 420, 150, a, INK, "mt", weight="Black")
        text(img, "名员工 · 同一家软件公司", 540, 610, 40, a, INK2, "mt")
        a6 = ap(t, L, 5)
        if a6 > 0:
            l = layer(); d = ImageDraw.Draw(l)
            for i in range(139):
                grp = 0 if i < 67 else 1
                j = i if grp == 0 else i - 67
                cols = 8
                x = (130 if grp == 0 else 600) + (j % cols) * 46
                y = 780 + (j // cols) * 46
                ai = a6 * ease((t - at(L, 5) - j * 0.012) / 0.3)
                ink_dot(d, x + 20, y, 15, ZHU if grp == 0 else INK2, 220 * ai)
            img.alpha_composite(l)
            text(img, "67 人 慈心禅", 300, 1230, 40, a6, ZHU, "mt")
            text(img, "72 人 排队等候", 770, 1230, 40, a6, INK2, "mt")
            text(img, "7 周 · 6 次课 · 回家自练", 540, 700, 34, a6, GREY, "mt", weight="Medium")


def draw_spiral(img, t, L, dur):
    headline(img, "慈心禅七周之后", ap(t, L, 0, -0.3) * (1 - ap(t, L, 3, -0.2)), 170, 66)
    phase2 = at(L, 3)
    aA = ap(t, L, 0) * (1 - fade(t, phase2 - 0.2, 0.5))
    if aA > 0:
        # 每日积极情绪（示意）
        l = layer(); d = ImageDraw.Draw(l)
        d.line([(130, 760), (950, 760)], fill=INK2 + (int(180 * aA),), width=3)
        g = ease((t - at(L, 0)) / 2.5)
        pts = []
        for k in range(int(60 * g) + 1):
            x = k / 60
            pts.append((130 + x * 820, 740 - 300 * (x ** 1.6) + 18 * math.sin(k * 1.3)))
        if len(pts) > 1:
            d.line(pts, fill=ZHU + (int(230 * aA),), width=6)
        img.alpha_composite(l)
        text(img, "练习组每日积极情绪（示意）", 540, 790, 30, aA, GREY, "mt", weight="Medium")
        # 剂量反应
        a3 = min(aA, ap(t, L, 2))
        if a3 > 0:
            text(img, "每练习 1 小时带来的积极情绪增量", 540, 900, 36, a3, INK, "mt")
            for i, (lab, v, dt) in enumerate((("第 2 周", 0.06, 0.0), ("第 7 周", 0.17, 3.0))):
                g = ease((t - at(L, 2) - dt) / 0.8)
                h = v * 1500 * g
                x = 330 + i * 420
                ink_bar_v(img, x - 60, 1290 - h, 120, h, a3, ZHU if i else INK2)
                text(img, f"{v:.2f}", x, 1290 - h - 60, 44, a3 * g, ZHU if i else INK2, "mt", weight="Black")
                text(img, lab, x, 1305, 36, a3 * g, INK, "mt")
            text(img, "≈ 3 倍", 540, 1000, 60, ap(t, L, 2, 3.6) * aA, ZHU, "mt", weight="Black")
    if t > phase2 - 0.2:
        a = fade(t, phase2 - 0.2, 0.5)
        headline(img, "拓展与建构", a, 170, 76, ZHU)
        # 积极情绪 → 资源 → 结果
        text(img, "积极情绪", 540, 330, 56, a, ZHU, "mt")
        res = ["觉察当下", "人生目标", "社会支持", "身体不适↓"]
        l = layer(); d = ImageDraw.Draw(l)
        for i, s in enumerate(res):
            ai = ap(t, L, 3, 1.0 + 0.6 * i)
            x = 180 + i * 240
            arrow(d, 540, 410, x, 560, INK2, 4, 200 * ai, 18)
        img.alpha_composite(l)
        for i, s in enumerate(res):
            ai = ap(t, L, 3, 1.0 + 0.6 * i)
            x = 180 + i * 240
            card(img, x - 105, 575, 210, 90, ai)
            text(img, s, x, 595, 36, ai, INK, "mt")
        a5 = ap(t, L, 4)
        l = layer(); d = ImageDraw.Draw(l)
        for i in range(4):
            arrow(d, 180 + i * 240, 690, 540, 800, INK2, 4, 180 * a5, 18)
        img.alpha_composite(l)
        text(img, "生活满意度↑   抑郁症状↓", 540, 815, 48, a5, INK, "mt")
        # 上升螺旋
        a6 = ap(t, L, 5)
        if a6 > 0:
            l = layer(); d = ImageDraw.Draw(l)
            g = ease((t - at(L, 5)) / 3.0)
            pts = []
            for k in range(int(220 * g) + 2):
                u = k / 220 * 3.2 * math.pi
                r = 60 + 34 * u
                pts.append((540 + r * math.cos(u) * 1.25, 1210 - 26 * u + r * 0.35 * math.sin(u)))
            d.line(pts, fill=ZHU + (int(190 * a6),), width=5)
            img.alpha_composite(l.filter(ImageFilter.GaussianBlur(0.8)))
            text(img, "拓宽 → 建构 → 再拓宽", 540, 1300, 34, a6 * (1 - ap(t, L, 6)), GREY, "mt", weight="Medium")
        a7 = ap(t, L, 6)
        if a7 > 0:
            soft_cover(img, 960, 1400, a7)
            for i, s in enumerate(["单项研究", "对照只是等待", "同一家公司"]):
                stamp(img, s, 200 + i * 340, 1060, t, at(L, 6, 0.4 + 0.9 * i), size=38)
            tag(img, "需要独立的重复研究", ap(t, L, 7), 1180, size=42, fill=INK)


def ink_bar_v(img, x, y, w, h, a, color):
    if h < 2:
        return
    sp = _bar_sprite(int(h), int(w), color, 7).rotate(90, expand=True)
    put(img, sp, (x, y), a)


# ================================================================ S5 小心炒作
@functools.lru_cache(None)
def page_sprite(seed):
    r = rng(seed)
    w, h = 300, 400
    img = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([18, 20, w + 18, h + 20], fill=(0, 0, 0, 60))
    img = img.filter(ImageFilter.GaussianBlur(7)); d = ImageDraw.Draw(img)
    d.rectangle([10, 10, w + 10, h + 10], fill=(248, 245, 236, 255), outline=(190, 180, 160, 255))
    d.rectangle([40, 40, w - 40, 62], fill=INK2 + (200,))
    y = 90
    while y < h - 20:
        L = r.uniform(0.6, 1.0) * (w - 60)
        d.line([(40, y), (40 + L, y)], fill=(150, 145, 135, 255), width=4)
        y += 22
    return img


def draw_hype(img, t, L, dur):
    a1 = ap(t, L, 0, -0.2)
    headline(img, "泼一点冷水", a1, 170, 70)
    a2 = ap(t, L, 1)
    if a2 > 0:
        card(img, 120, 300, 840, 330, a2)
        text(img, "Mind the Hype", 540, 330, 76, a2, ZHU, "mt", kind="latin")
        text(img, "《小心炒作》", 540, 430, 50, a2, INK, "mt")
        text(img, "Van Dam 等 15 位学者 · 2018", 540, 505, 34, a2, INK2, "mt")
        text(img, "Perspectives on Psychological Science", 540, 560, 28, a2, GREY, "mt", kind="latin")
    tag(img, "批评来自研究冥想的人自己", ap(t, L, 3) * (1 - ap(t, L, 4)), 690, size=36, fill=INK)
    # 三点
    a5 = ap(t, L, 4)
    if a5 > 0:
        text(img, "一 · 定义五花八门", 120, 690, 46, a5, INK)
        text(img, "正念", 540, 830, 80, a5 * (1 - ap(t, L, 6)), ZHU, "mt", weight="Black")
        l = layer(); d = ImageDraw.Draw(l)
        for i, s in enumerate(["注意状态", "八周课程", "修行传统"]):
            ai = ap(t, L, 4, 1.0 + 0.9 * i) * (1 - ap(t, L, 6))
            x = 200 + i * 340
            arrow(d, 540, 930, x, 1010, INK2, 4, 200 * ai, 16)
        img.alpha_composite(l)
        for i, s in enumerate(["注意状态", "八周课程", "修行传统"]):
            ai = ap(t, L, 4, 1.0 + 0.9 * i) * (1 - ap(t, L, 6))
            text(img, s, 200 + i * 340, 1025, 42, ai, INK, "mt")
        text(img, "名字一样，量的未必一样", 540, 1120, 40, ap(t, L, 5) * (1 - ap(t, L, 6)), INK2, "mt")
    a7 = ap(t, L, 6)
    if a7 > 0:
        text(img, "二 · 样本小 · 缺主动对照 · 靠自填问卷", 120, 790, 40, a7, INK)
    a8 = ap(t, L, 7)
    if a8 > 0:
        text(img, "三 · 宣传跑在证据前面", 120, 880, 40, a8, INK)
        g = ease((t - at(L, 7, 0.5)) / 1.0)
        ink_bar_v(img, 330, 1300 - 330 * g, 110, 330 * g, a8, ZHU)
        ink_bar_v(img, 640, 1300 - 120 * g, 110, 120 * g, a8, INK2)
        text(img, "宣传", 385, 1310, 38, a8, ZHU, "mt")
        text(img, "证据", 695, 1310, 38, a8, INK2, "mt")
    a9 = ap(t, L, 8)
    if a9 > 0:
        soft_cover(img, 670, 1400, a9)
        text(img, "“harmed, misled,", 540, 860, 60, a9, INK, "mt", kind="latin")
        text(img, "and disappointed”", 540, 945, 60, a9, INK, "mt", kind="latin")
        text(img, "受到伤害 · 被误导 · 最后失望", 540, 1060, 44, a9, ZHU, "mt")


def draw_bias(img, t, L, dur):
    headline(img, "三个容易被忽略的因素", ap(t, L, 0, -0.2), 170, 64)
    a = ap(t, L, 0)
    for i in range(3):
        put(img, page_sprite(60 + i), (110 + i * 300, 360 + (i % 2) * 40), a)
    stamp(img, "小样本", 230, 450, t, at(L, 0, 1.0), 40, -8)
    stamp(img, "靠自评", 880, 480, t, at(L, 0, 1.6), 40, 7)
    rows = [("发表偏差", "有效的更容易发表，无效的锁进抽屉"),
            ("期待效应", "相信有用，分数就可能高一点"),
            ("缺主动对照", "和“什么都不做”比，几乎都有效")]
    for i, (s, sub) in enumerate(rows):
        t0 = at(L, i + 1)
        stamp(img, s, (330, 720, 430)[i], (610, 650, 770)[i], t, t0 + 0.2, 50, (-7, 6, -4)[i])
        ai = fade(t, t0 + 0.5, 0.5)
        card(img, 100, 860 + i * 165, 880, 140, ai)
        text(img, s, 140, 880 + i * 165, 46, ai, ZHU)
        text(img, sub, 140, 940 + i * 165, 34, ai, INK2, weight="Medium")


def draw_adverse(img, t, L, dur):
    headline(img, "打坐也有“副作用”吗？", ap(t, L, 0, -0.2), 170, 66)
    a2 = ap(t, L, 1)
    tag(img, "Lindahl 等 · PLoS ONE 2017 · 访谈研究", a2, 280, size=30, color=GREY)
    phaseB = at(L, 5)
    aA = a2 * (1 - fade(t, phaseB - 0.2, 0.5))
    if aA > 0:
        l = layer(); d = ImageDraw.Draw(l)
        for i in range(60):
            x = 190 + (i % 10) * 78; y = 400 + (i // 10) * 70
            ai = aA * ease((t - at(L, 1) - 0.02 * i) / 0.3)
            ink_dot(d, x, y, 13, INK2, 220 * ai)
            d.ellipse([x - 20, y + 16, x + 20, y + 46], fill=INK2 + (int(180 * ai),))
        img.alpha_composite(l)
        text(img, "60 位禅修者与禅修老师", 540, 830, 40, aA, INK, "mt")
        a3 = min(aA, ap(t, L, 2))
        if a3 > 0:
            text(img, "59 类体验 · 7 个领域", 540, 910, 48, a3, ZHU, "mt")
            doms = ["认知", "知觉", "情绪", "身体", "意志", "自我感", "人际"]
            for i, s in enumerate(doms):
                ai = min(aA, ap(t, L, 2, 1.0 + 0.3 * i))
                x = 160 + (i % 4) * 253 + (0 if i < 4 else 126)
                y = 1000 + (i // 4) * 90
                text(img, s, x, y, 40, ai, INK2, "mt")
        tag(img, "访谈研究：说明不了有多常见", min(aA, ap(t, L, 3)), 1200, size=38)
        tag(img, "密集禅修需要有经验的指导", min(aA, ap(t, L, 4)), 1290, size=38, fill=INK)
    if t > phaseB - 0.2:
        a = fade(t, phaseB - 0.2, 0.6)
        text(img, "打坐有用", 540, 560, 110, a, INK, "mt", weight="Black")
        text(img, "但没有宣传的那么神", 540, 740, 80, a, ZHU, "mt", weight="Black")


# ================================================================ S6 印照
def quote_card(img, t, t0, s_cols, src, gloss, gloss_t, x_center=540, top=360, size=104):
    """竖排经文：逐字显影。s_cols: 列表，右起。"""
    ncol = len(s_cols)
    colw = size * 1.45
    x_right = x_center + (ncol - 1) * colw / 2
    k = 0
    for c, col in enumerate(s_cols):
        x = x_right - c * colw
        y = top
        for ch in col:
            if ch in "，。":
                y += size * 0.5
                continue
            ai = fade(t, t0 + 0.16 * k, 0.5)
            put(img, text_sprite(ch, size, "kai", "Bold", INK), (x, y), ai, "mt")
            y += size * 1.12
            k += 1
    a = fade(t, t0 + 0.16 * k, 0.6)
    sp = seal("原典", 64, ZHU, seed=91)
    put(img, sp, (x_right + size * 0.55, top + size * 0.1), a)
    text(img, src, 540, 1180, 32, a, INK2, "mt", weight="Medium")
    ag = fade(t, gloss_t, 0.6)
    text(img, gloss, 540, 1250, 38, ag, ZHU, "mt")


def draw_jingang(img, t, L, dur):
    headline(img, "佛法讲的“安住当下”", ap(t, L, 0, -0.2) * (1 - ap(t, L, 2, -0.5)), 170, 66)
    text(img, "《金刚经》", 540, 300, 56, ap(t, L, 1) * (1 - ap(t, L, 4)), INK2, "mt")
    t3 = at(L, 2, -0.3)
    if t > t3:
        a_out = 1 - ap(t, L, 4, -0.2)
        sub = img if a_out >= 1 else layer()
        quote_card(sub, t, t3, ["應無所住", "而生其心"], "《金剛般若波羅蜜經》 鳩摩羅什 譯",
                   "心不执着于任何一处，而清明地生起作用", at(L, 3), size=112)
        if sub is not img:
            a = sub.getchannel("A").point(lambda v: int(v * max(0, a_out))); sub.putalpha(a)
            img.alpha_composite(sub)
    a5 = ap(t, L, 4)
    if a5 > 0:
        cols = ["不應住色生心", "不應住聲香味觸法生心", "應無所住而生其心"]
        for i, s in enumerate(cols):
            sp = vtext_sprite(s, 54, "kai", "Bold", ZHU if i == 2 else INK)
            put(img, sp, (700 - i * 150, 360), ease((t - at(L, 4) - 0.8 * i) / 0.6) * (1 - ap(t, L, 5, 1.5) * 0.6))
        text(img, "经文原句 · CBETA T08 No.235", 540, 1210, 28, a5, GREY, "mt", weight="Medium")
    a6 = ap(t, L, 5)
    if a6 > 0:
        card(img, 130, 1040, 820, 150, a6)
        text(img, "据《坛经·行由品》：", 540, 1060, 34, a6, INK2, "mt", weight="Medium")
        text(img, "“至應無所住而生其心，惠能言下大悟”", 540, 1110, 38, a6, INK, "mt", kind="kai")
        tag(img, "传统记载 · 当故事听", a6, 1270, size=32)


def draw_tanjing(img, t, L, dur):
    text(img, "《六祖坛经》", 540, 200, 56, ap(t, L, 0, -0.2), INK2, "mt")
    t2 = at(L, 1, -0.3)
    a_out = 1 - ap(t, L, 3, -0.3)
    if t > t2 and a_out > 0:
        sub = layer()
        quote_card(sub, t, t2, ["無念者，", "於念而無念"], "《六祖大師法寶壇經·定慧品》 宗寶本",
                   "无念，不是没有念头，而是不被念头带走", at(L, 2), top=330, size=112)
        a = sub.getchannel("A").point(lambda v: int(v * a_out)); sub.putalpha(a)
        img.alpha_composite(sub)
    a4 = ap(t, L, 3)
    if a4 > 0:
        # 念头如云飘过，心如明月不动
        l = layer(); d = ImageDraw.Draw(l)
        d.ellipse([440, 640, 640, 840], outline=ZHU + (int(230 * a4),), width=6)
        img.alpha_composite(l)
        text(img, "此心", 540, 708, 52, a4, ZHU, "mt", kind="kai", weight="Bold")
        words = ["明天的会", "昨天那句话", "手机", "要是……", "早知道……"]
        for i, s in enumerate(words):
            ph = ((t - at(L, 3)) * 0.09 + i / 5) % 1
            x = -150 + ph * 1400
            y = 470 + (i % 3) * 330 + 20 * math.sin(t * 0.8 + i)
            text(img, s, x, y, 40, a4 * 0.7 * math.sin(ph * math.pi), GREY, "mt", kind="kai")
        tag(img, "类比 · 或许相通", a4, 1000, size=36)
        text(img, "让人不快乐的，未必是念头本身", 540, 1110, 40, ap(t, L, 3, 2.0), INK, "mt")
        text(img, "而是心被念头带走", 540, 1175, 46, ap(t, L, 3, 4.0), ZHU, "mt")


def draw_mirror(img, t, L, dur):
    a1 = ap(t, L, 0, -0.2)
    headline(img, "这是印照，不是证明", a1, 170, 70, ZHU)
    a2 = ap(t, L, 1)
    if a2 > 0:
        l = layer(); d = ImageDraw.Draw(l)
        sep = 200 - 40 * ease((t - at(L, 4)) / 2.0)
        for side, c in ((-1, INK), (1, INK2)):
            x = 540 + side * sep
            d.ellipse([x - 270, 480, x + 270, 1020], outline=c + (int(200 * a2),), width=6)
        img.alpha_composite(l)
        text(img, "佛法", 330, 600, 64, a2, INK, "mt", weight="Black")
        text(img, "解脱", 330, 700, 44, a2, INK2, "mt")
        text(img, "苦的根本", 330, 765, 40, a2, INK2, "mt")
        text(img, "研究", 750, 600, 64, a2, INK2, "mt", weight="Black")
        text(img, "情绪量表", 750, 700, 44, a2, INK2, "mt")
        text(img, "问卷分数", 750, 765, 40, a2, INK2, "mt")
        text(img, "二者不是一回事", 540, 1060, 44, a2, INK, "mt")
    a3 = ap(t, L, 2)
    tag(img, "科学不替佛法背书 · 佛法不靠量表证明", a3 * (1 - ap(t, L, 3)), 1150, size=34)
    a4 = ap(t, L, 3)
    if a4 > 0:
        text(img, "安住当下，是为了看清烦恼", 540, 1140, 42, a4, INK, "mt")
        text(img, "从哪里生起，又从哪里熄灭", 540, 1200, 42, a4, INK, "mt")
    a5 = ap(t, L, 4)
    if a5 > 0:
        sp = seal("照見", 84, ZHU, seed=95)
        put(img, sp, (540, 720), a5, "mt")
        text(img, "心不要被带走", 540, 1290, 46, a5, ZHU, "mt")


# ================================================================ S7 收束
def draw_breath(img, t, L, dur):
    img.alpha_composite(bamboo(t, 6, 880, 3, INK, 0.55))
    headline(img, "能带回生活的一件小事", ap(t, L, 0, -0.2), 170, 64)
    fig, xy = seated_figure(540, 1180, 0.8)
    put(img, fig, xy, 1.0)
    a2 = ap(t, L, 1)
    if a2 > 0:
        br = 0.5 - 0.5 * math.cos((t - at(L, 1)) * 2 * math.pi / 8.0)   # 8 秒一呼一吸
        l = layer(); d = ImageDraw.Draw(l)
        r = 260 + 90 * br
        d.ellipse([540 - r, 900 - r, 540 + r, 900 + r], outline=GOLD + (int(170 * a2),), width=5)
        img.alpha_composite(l.filter(ImageFilter.GaussianBlur(2)))
        lab = "吸" if math.sin((t - at(L, 1)) * 2 * math.pi / 8.0) > 0 else "呼"
        text(img, lab, 540, 470, 56, a2 * 0.8, GOLD, "mt", kind="kai", weight="Bold")
        text(img, "每天几分钟 · 回到呼吸", 540, 300, 42, a2, INK2, "mt")
    a3 = ap(t, L, 2)
    if a3 > 0:
        n = int(min(10, max(1, (t - at(L, 2) - 2.0) / 0.9 + 1)))
        text(img, f"{n}", 540, 1230, 70, a3 * (1 - ap(t, L, 3)), ZHU, "mt", kind="kai", weight="Bold")
        text(img, "坐椅子也可以 · 默数一到十", 540, 1330, 34, a3 * (1 - ap(t, L, 3)), GREY, "mt", weight="Medium")
    a4 = ap(t, L, 3)
    if a4 > 0:
        # 念头飘出又回来
        l = layer(); d = ImageDraw.Draw(l)
        for k in range(10):
            ph = ((t - at(L, 3)) * 0.25 + k / 10) % 1
            ang = k * 0.63
            rr = 180 + 240 * math.sin(ph * math.pi)
            x = 540 + rr * math.cos(ang); y = 820 + rr * 0.6 * math.sin(ang)
            ink_dot(d, x, y, 10, INK2, 160 * a4 * (1 - ap(t, L, 4)))
        img.alpha_composite(l.filter(ImageFilter.GaussianBlur(1.5)))
        cnt = ["一次", "两次", "一百次"]
        for i, s in enumerate(cnt):
            text(img, s, 260 + i * 280, 1230, 52, ap(t, L, 3, 2.6 + 0.7 * i) * (1 - ap(t, L, 4)), ZHU, "mt", kind="kai", weight="Bold")
    a6 = ap(t, L, 5)
    if a6 > 0:
        card(img, 130, 1210, 820, 150, a6 * (1 - ap(t, L, 6)), tone=(250, 240, 232))
        text(img, "练习中明显不适：停下来", 540, 1228, 38, a6 * (1 - ap(t, L, 6)), ZHU, "mt")
        text(img, "必要时寻求专业帮助", 540, 1285, 36, a6 * (1 - ap(t, L, 6)), INK, "mt")
    a7 = ap(t, L, 6)
    text(img, "多一次察觉", 540, 1240, 60, a7, INK, "mt", kind="kai", weight="Bold")
    text(img, "就是一次回家", 540, 1320, 46, ap(t, L, 7), ZHU, "mt", kind="kai", weight="Bold")


def draw_ending(img, t, L, dur):
    # 前半：経文；后半：走入街巷
    walk_t = at(L, 3, -0.6)
    a_q = 1 - fade(t, walk_t, 0.8)
    if a_q > 0:
        sub = layer()
        text(sub, "六祖慧能 · 无相颂", 540, 200, 50, ap(t, L, 0, -0.2), INK2, "mt")
        if t > at(L, 1, -0.3):
            quote_card(sub, t, at(L, 1, -0.3), ["心平何勞持戒", "行直何用修禪"],
                       "《六祖大師法寶壇經·疑問品》 無相頌", "心若平正，何必刻意持戒；行为正直，何须执着坐禅", at(L, 2), top=320, size=96)
        text(sub, "打坐是方法，不是目的", 540, 1320, 46, ap(t, L, 2, 3.0), INK, "mt")
        a = sub.getchannel("A").point(lambda v: int(v * a_q)); sub.putalpha(a)
        img.alpha_composite(sub)
    if t > walk_t:
        a = fade(t, walk_t, 0.8)
        al = bg_alley().copy()
        u = max(0, t - walk_t)
        # 人从近处走向巷子深处
        p = min(1, u / 9.0)
        sc = 0.9 - 0.65 * p
        y = 1420 - 420 * p
        fig, xy = standing_figure(540 + 30 * math.sin(u * 0.4), y, sc, u * 3.2)
        al.alpha_composite(fig, xy)
        al.putalpha(al.getchannel("A").point(lambda v: int(v * a)))
        img.alpha_composite(al)
        text(img, "打坐不是幸福的捷径", 540, 200, 62, fade(t, walk_t + 0.6, 0.8), INK, "mt", weight="Black")
        text(img, "把走散的心一次次带回来", 540, 300, 50, fade(t, walk_t + 3.0, 0.8), ZHU, "mt")
        text(img, "就少了许多无谓的苦", 540, 375, 50, fade(t, walk_t + 4.5, 0.8), ZHU, "mt")


SCENE_FUNCS = {
    "hook": (_hook_static, draw_hook),
    "verdict": (lambda: bg_plain(2, True, 600), draw_verdict),
    "sampling": (lambda: bg_plain(3, True), draw_sampling),
    "sampling2": (lambda: bg_plain(4, True), draw_sampling2),
    "goyal": (lambda: bg_plain(5, True), draw_goyal),
    "goyal2": (lambda: bg_scroll(430, 1400, 6), draw_goyal2),
    "metta": (lambda: bg_plain(7, True, 900), draw_metta),
    "spiral": (lambda: bg_plain(8, True), draw_spiral),
    "hype": (lambda: bg_plain(12, True), draw_hype),
    "bias": (lambda: bg_plain(13, True), draw_bias),
    "adverse": (lambda: bg_plain(14, True), draw_adverse),
    "jingang": (lambda: bg_plain(15, True, 700), draw_jingang),
    "tanjing": (lambda: bg_plain(16, True, 700), draw_tanjing),
    "mirror": (lambda: bg_plain(17, True), draw_mirror),
    "breath": (lambda: bg_courtyard(), draw_breath),
    "ending": (lambda: bg_plain(18, True, 700), draw_ending),
}
