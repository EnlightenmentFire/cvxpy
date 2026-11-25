# -*- coding: utf-8 -*-
"""Scene drawers. Each: f(t, T, ev) -> RGBA canvas (W x H). ev = list of (t0, t1, sub) local narration lines."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *

CY = 900  # visual centre (subtitle band lives ~1480-1700)


def base(dark=False):
    return paper(dark=dark).convert("RGBA")


def ev_t(ev, i, default=0.0):
    return ev[i][0] if i < len(ev) else default


# ---------------- hook: dawn courtyard + phone ----------------
@functools.lru_cache(maxsize=1)
def courtyard_static():
    im = base()
    im.alpha_composite(light_glow(300, 520, 700, DAWN, 0.55))
    im.alpha_composite(mountains(seed=5, y0=760, layers=3, height=300))
    # ground: soft stone floor gradient
    g = np.zeros((H, W), np.float32)
    yy = np.arange(H)[:, None]
    g = np.clip((yy - 1150) / 500.0, 0, 1) * 70 * np.ones((1, W))
    im.alpha_composite(ink_layer(Image.fromarray(g.astype(np.uint8)).filter(ImageFilter.GaussianBlur(8)), (120, 110, 94)))
    return im


def phone_card(lines_shown, t, title="你现在在想什么？"):
    w, h = 460, 520
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 46, fill=(28, 28, 30, 235))
    d.rounded_rectangle([14, 14, w - 15, h - 15], 36, fill=(246, 243, 236, 255))
    d.rounded_rectangle([w / 2 - 60, 26, w / 2 + 60, 40], 7, fill=(28, 28, 30, 255))
    # notification banner
    d.rounded_rectangle([34, 64, w - 34, 170], 22, fill=(255, 255, 255, 255), outline=(210, 205, 195, 255))
    d.text((58, 80), "随机提问 · 现在", font=font("serif_r", 24), fill=(130, 124, 114))
    d.text((58, 114), title, font=font("serif", 34), fill=INK)
    qs = ["你现在感觉怎么样？", "你在做什么？", "你在想别的事吗？"]
    for i in range(min(lines_shown, 3)):
        y = 200 + i * 98
        d.rounded_rectangle([34, y, w - 34, y + 80], 20, fill=(232, 226, 214, 255))
        d.text((56, y + 22), f"{i + 1}. {qs[i]}", font=font("serif", 30), fill=INK)
    return im


@functools.lru_cache(maxsize=1)
def head_band():
    band = Image.new("RGBA", (W, H), PAPER + (0,))
    al = np.zeros((H, W), np.float32); yy = np.arange(H)[:, None]
    al[:] = 220 * np.clip(np.minimum((yy - 200) / 50, (500 - yy) / 50), 0, 1)
    band.putalpha(Image.fromarray(al.astype(np.uint8)))
    return band


def s_hook(t, T, ev):
    im = courtyard_static().copy()
    bam = bamboo(seed=7, n=6)
    sh = sway(bam, t, amp=14, speed=0.9)
    # shadow of bamboo on wall/ground (soft, offset)
    a = sh.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.28))
    shadow = Image.new("RGBA", (W, H), (40, 36, 30, 0)); shadow.putalpha(a)
    shadow = shadow.transform((W, H), Image.AFFINE, (1, 0.35, -420, 0, 1, -60), resample=Image.BILINEAR)
    im.alpha_composite(shadow)
    im.alpha_composite(sway(bam, t, amp=8, speed=0.9))
    fig = figure(0.95)
    im.alpha_composite(fig, (int(W * 0.34 - fig.width / 2), 1330 - fig.height))
    im.alpha_composite(head_band())
    hl = text_img("你有将近一半的时间", "black", 74, INK)
    hl2 = text_img("心，不在这里", "black", 96, RED)
    paste_c(im, hl, 540, 300)
    paste_c(im, hl2, 540, 410)
    # phone: present from frame 0 (hook)
    nq = 0
    if len(ev) > 0:
        nq = 0
    pc = phone_card(nq, t)
    y = 330 + 10 * math.sin(t * 1.3)
    paste_c(im, pc, 800, y + 230 + pc.height / 2, 1.0)
    return im


def s_hook_q(t, T, ev):
    im = s_hook(t + 5, T, [])
    # questions appear with narration rhythm
    n = 1 + int(t > T * 0.33) + int(t > T * 0.62)
    pc = phone_card(n, t)
    y = 330 + 10 * math.sin((t + 5) * 1.3)
    paste_c(im, pc, 800, y + 230 + pc.height / 2)
    return im


def s_stat(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 820, 650, DAWN, 0.25))
    frac = 0.469 * ramp(t, 0.1, 1.6)
    c = ink_circle(1.0, r=300, width=10, color=GREY)
    paste_c(im, c, 540, 820, 0.35)
    c2 = ink_circle(frac, r=300, width=54)
    paste_c(im, c2, 540, 820)
    num = text_img(f"{frac * 100:.1f}%", "black", 150, INK)
    paste_c(im, num, 540, 800)
    paste_c(im, text_img("的时刻 · 心不在焉", "kai", 54, INK2), 540, 935, ramp(t, 0.8, 1.6))
    if len(ev) > 1:
        a = ramp(t, ev[1][0], ev[1][0] + 0.6)
        paste_c(im, text_img("走神时，更不快乐", "serif", 76, RED), 540, 1260, a)
    return im


def s_paper(t, T, ev):
    im = base()
    r = rng(11)
    # 2,250 dots pinging at random
    pts = r.random((2250, 2)) * np.array([900, 600]) + np.array([90, 520])
    phase = r.random(2250) * 6
    d = ImageDraw.Draw(im)
    for (x, y), ph in zip(pts, phase):
        k = (t * 0.9 + ph) % 6
        if k < 0.5:
            rr = 4 + 14 * k
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(176, 46, 34, int(220 * (1 - k / 0.5))), width=2)
        d.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=(60, 56, 50, 150))
    card = Image.new("RGBA", (860, 250), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, 859, 249], 18, fill=(246, 241, 230, 235), outline=(120, 110, 96, 255), width=2)
    cd.text((430, 70), "《科学》Science  2010", font=font("serif", 50), fill=INK, anchor="mm")
    cd.text((430, 150), "Killingsworth & Gilbert, 330: 932", font=font("serif_r", 34), fill=INK2, anchor="mm")
    cd.text((430, 205), "哈佛大学 · 手机经验抽样", font=font("kai", 32), fill=GREY, anchor="mm")
    paste_c(im, card, 540, 330, ramp(t, 0, 0.5))
    n = 2250 if len(ev) < 2 else int(2250 * ramp(t, ev[1][0], ev[1][0] + 2.0)) if t < ev[1][0] + 2.0 else 2250
    big = text_img(f"{n:,} 人", "black", 110, INK)
    paste_c(im, big, 540, 1240, ramp(t, ev_t(ev, 1), ev_t(ev, 1) + 0.4) if len(ev) > 1 else 1)
    if len(ev) > 2:
        paste_c(im, text_img("近 25 万条即时记录", "kai", 56, INK2), 540, 1355, ramp(t, ev[2][0], ev[2][0] + 0.5))
    if len(ev) > 3:
        a = ramp(t, ev[3][0], ev[3][0] + 0.5)
        lay = Image.new("RGBA", (W, H), PAPER + (0,))
        lay.putalpha(int(225 * a))
        im.alpha_composite(lay)
        paste_c(im, text_img("46.9%", "black", 190, INK), 540, 720, a)
        paste_c(im, text_img("走神时刻占比", "kai", 58, INK2), 540, 860, a)
        paste_c(im, text_img("做任何事 ≥ 30%\n（亲密时刻除外）", "kai", 52, RED, spacing=18), 540, 1120, ramp(t, ev[3][0] + 2.5, ev[3][0] + 3.2))
    return im


def s_bars(t, T, ev):
    im = base()
    paste_c(im, text_img("快乐的起伏，能被什么解释？", "serif", 60, INK), 540, 330)
    a = ramp(t, ev_t(ev, 1) - 0.3, ev_t(ev, 1) + 2.5) if len(ev) > 1 else ramp(t, 1, 3)
    maxh = 620
    for i, (lab, v, col) in enumerate([("在做什么", 4.6, GREY), ("走不走神", 10.8, INK)]):
        x = 300 + i * 480
        h = maxh * v / 12 * a
        brush_bar(im, x - 90, 1240 - h, 180, max(2, h), col, seed=20 + i)
        paste_c(im, text_img(f"{v * a:.1f}%", "black", 70, col), x, 1190 - h)
        paste_c(im, text_img(lab, "kai", 56, INK), x, 1310)
    if len(ev) > 2:
        b = ramp(t, ev[2][0], ev[2][0] + 0.6)
        paste_c(im, text_img("想愉快的事 ≠ 更快乐", "serif", 60, RED), 540, 470, b)
    return im


def s_causal(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    paste_c(im, text_img("走神", "black", 120, INK), 270, 760)
    paste_c(im, text_img("不快乐", "black", 120, INK), 810, 760)
    k = 0.5 + 0.5 * math.sin(t * 2.2)
    arrow(d, 400, 720, 640, 720, (32, 30, 28, int(120 + 135 * k)), 9, 32)
    arrow(d, 640, 810, 400, 810, (32, 30, 28, int(120 + 135 * (1 - k))), 9, 32)
    paste_c(im, text_img("？", "black", 110, RED), 540, 600, 0.9)
    s = seal("相关非因果", 230, seed=31, rot=-6)
    paste_c(im, s, 540, 1130, ramp(t, 0.4, 0.8))
    if len(ev) > 2:
        paste_c(im, text_img("时间先后分析：倾向走神在前\n但仍不等于证明因果", "kai", 50, INK2, spacing=16), 540, 1370, ramp(t, ev[2][0], ev[2][0] + 0.6))
    return im


def s_title(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 500, 800, DAWN, 0.4))
    im.alpha_composite(mountains(seed=9, y0=1000, layers=4, height=480))
    fig = figure(0.55)
    im.alpha_composite(fig, (540 - fig.width // 2, 1180 - fig.height))
    a = ramp(t, ev_t(ev, 1) - 0.2, ev_t(ev, 1) + 0.6) if len(ev) > 1 else ramp(t, 0, 1)
    paste_c(im, text_img("打坐让人幸福，", "black", 96, INK), 540, 380, a)
    paste_c(im, text_img("证据到底有多硬？", "black", 96, RED), 540, 510, ramp(t, ev_t(ev, 1) + 0.4, ev_t(ev, 1) + 1.0) if len(ev) > 1 else a)
    return im


def s_funnel(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    t1 = ev_t(ev, 1, 3); t2 = ev_t(ev, 2, 6)
    card = text_img("JAMA Internal Medicine 2014\nGoyal 等 · 系统综述与元分析", "serif", 40, INK2, spacing=14)
    paste_c(im, card, 540, 330, ramp(t, t1, t1 + 0.5))
    # funnel shape
    pts = [(150, 520), (930, 520), (640, 1060), (640, 1250), (440, 1250), (440, 1060)]
    d.polygon(pts, outline=(70, 66, 60, 200), width=4)
    r = rng(4)
    n = int(600 * ramp(t, 0, 1.5))
    for i in range(n):
        x = r.uniform(170, 910); y = r.uniform(530, 640)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(90, 84, 76, 150))
    paste_c(im, text_img("18,753 条文献", "serif", 64, INK), 540, 590, ramp(t, t2, t2 + 0.6))
    b = ramp(t, t2 + 1.5, t2 + 3.0)
    for i in range(int(47 * b)):
        x = 470 + (i % 8) * 20; y = 1090 + (i // 8) * 24
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(176, 46, 34, 230))
    paste_c(im, text_img("47 项随机对照试验", "black", 70, RED), 540, 900, b)
    paste_c(im, text_img("3,515 名参与者", "serif", 60, INK), 540, 1360, ramp(t, t2 + 3.0, t2 + 3.6))
    return im


def s_control(t, T, ev):
    im = base()
    paste_c(im, text_img("主动对照", "black", 92, INK), 540, 330)
    fig = figure(0.42)
    for g, (x, lab, sub) in enumerate([(290, "冥想组", "正念冥想"), (790, "对照组", "健康讲座 / 放松训练")]):
        for k in range(3):
            paste_c(im, fig, x - 120 + k * 120, 760, 1.0 if g == 0 else 0.75)
        paste_c(im, text_img(lab, "serif", 56, INK), x, 920)
        paste_c(im, text_img(sub, "kai", 40, INK2), x, 985)
        brush_bar(im, x - 170, 1060, int(340 * ramp(t, 0.5, 2.0)), 40, GREY, seed=40 + g)
    paste_c(im, text_img("同样花时间 · 同样被关注", "kai", 48, INK2), 540, 1150, ramp(t, 1.5, 2.2))
    if len(ev) > 2:
        a = ramp(t, ev[2][0], ev[2][0] + 0.6)
        for i, w in enumerate(["被关注", "花了时间", "相信会变好"]):
            s = seal(w, 150, seed=50 + i, rot=(-5, 3, -2)[i])
            paste_c(im, s, 250 + i * 290, 1300, a)
    return im


def scroll_img(hi_right=0.0, rows_left=3, rows_right=4, bottom=0.0):
    w, h = 960, 960
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 40, w - 20, h - 40], fill=(244, 236, 214, 250), outline=(140, 120, 90, 255), width=3)
    for y in (20, h - 60):
        d.rounded_rectangle([0, y, w, y + 40], 18, fill=(110, 78, 50, 255))
    d.line([(w / 2, 90), (w / 2, h - 200)], fill=(140, 120, 90, 200), width=2)
    d.text((w * 0.27, 130), "有证据", font=font("black", 58), fill=INK, anchor="mm")
    d.text((w * 0.27, 190), "（中等强度 · 小到中等改善）", font=font("kai", 30), fill=INK2, anchor="mm")
    d.text((w * 0.73, 130), "证据不足 / 无效", font=font("black", 52), fill=RED, anchor="mm")
    for i, s in enumerate(["焦虑", "抑郁", "疼痛"][:rows_left]):
        d.text((w * 0.27, 290 + i * 110), s, font=font("serif", 66), fill=INK, anchor="mm")
    for i, s in enumerate(["积极情绪", "注意力", "睡眠", "体重"][:rows_right]):
        d.text((w * 0.73, 290 + i * 110), s, font=font("serif", 58), fill=(176, 46, 34, int(140 + 115 * hi_right)), anchor="mm")
    if bottom > 0:
        d.text((w / 2, h - 135), "不优于药物、运动等积极疗法", font=font("black", 50), fill=(32, 30, 28, int(255 * bottom)), anchor="mm")
    return im


def s_scroll(t, T, ev):
    im = base()
    rl = 3 if len(ev) < 2 else int(1 + 2 * ramp(t, ev[1][0], ev[1][0] + 3)) + (1 if t > ev[1][0] + 3 else 0)
    sc = scroll_img(0.0, min(3, max(1, rl)), 0)
    sc = wipe(sc, ramp(t, 0, 1.2), "down")
    paste_c(im, sc, 540, 860)
    paste_c(im, text_img("Goyal 等 · JAMA Intern Med 2014", "serif_r", 34, GREY), 540, 330)
    return im


def s_scroll2(t, T, ev):
    im = base()
    nr = 4 if len(ev) < 2 else min(4, int(4 * ramp(t, ev[1][0], ev[1][0] + 3.2)) + 0)
    bot = ramp(t, ev_t(ev, 2, 99), ev_t(ev, 2, 99) + 0.7)
    sc = scroll_img(ramp(t, 0, 1), 3, nr, bot)
    paste_c(im, sc, 540, 860)
    paste_c(im, text_img("Goyal 等 · JAMA Intern Med 2014", "serif_r", 34, GREY), 540, 330)
    return im


def s_es(t, T, ev):
    im = base()
    paste_c(im, text_img("效应量（练习 8 周时）", "serif", 58, INK), 540, 330)
    d = ImageDraw.Draw(im)
    x0, x1, y = 160, 940, 1180
    sc = lambda v: x0 + (x1 - x0) * v / 0.8
    d.line([(x0, y), (x1, y)], fill=INK2, width=4)
    for v, lab in [(0.2, "小 0.2"), (0.5, "中 0.5"), (0.8, "大 0.8")]:
        d.line([(sc(v), y - 14), (sc(v), y + 14)], fill=INK2, width=4)
        d.text((sc(v), y + 50), lab, font=font("kai", 38), fill=INK2, anchor="mm")
    a = ramp(t, 0.2, 2.0)
    for i, (lab, v, v2) in enumerate([("焦虑", 0.38, 0.22), ("抑郁", 0.30, 0.23), ("疼痛", 0.33, None)]):
        yy = 520 + i * 180
        d.text((x0, yy - 88), lab, font=font("serif", 48), fill=INK)
        brush_bar(im, x0, yy - 20, int((sc(v) - x0) * a), 56, INK, seed=60 + i)
        d.text((sc(v * a) + 30, yy + 8), f"{v:.2f}", font=font("black", 46), fill=INK, anchor="lm")
        if v2 and len(ev) > 1:
            b = ramp(t, ev[1][0], ev[1][0] + 1.2)
            brush_bar(im, x0, yy + 46, int((sc(v2) - x0) * b), 30, GREY, seed=70 + i, alpha=0.8)
            if b > 0.1:
                d.text((sc(v2 * b) + 30, yy + 62), f"{v2:.2f}（3–6 个月）", font=font("kai", 34), fill=GREY, anchor="lm")
    if len(ev) > 3:
        paste_c(im, text_img("有帮助，但不是脱胎换骨", "black", 64, RED), 540, 1350, ramp(t, ev[3][0], ev[3][0] + 0.6))
    return im


def s_verdict(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 820, 600, DAWN, 0.25))
    txt = vtext_img("打坐|不是幸福的捷径", "kai", 120, INK)
    paste_c(im, wipe(txt, ramp(t, 0.3, 3.0), "left"), 540, 860)
    s = seal("诚实话", 170, seed=80, rot=-4)
    paste_c(im, s, 840, 1340, ramp(t, 2.5, 3.0))
    return im


def s_metta(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 860, 760, DAWN, 0.35))
    d = ImageDraw.Draw(im)
    rings = ["自己", "亲近的人", "陌生人", "一切众生"]
    t2 = ev_t(ev, 2, 4)
    for i, w in enumerate(rings):
        a = ramp(t, t2 + i * 1.3, t2 + i * 1.3 + 0.8)
        if a <= 0:
            continue
        r = 110 + i * 120 + 6 * math.sin(t * 1.2 + i)
        d.ellipse([540 - r, 860 - r, 540 + r, 860 + r], outline=(176, 46, 34, int(200 * a)), width=5)
        paste_c(im, text_img(w, "kai", 44, INK), 540, 860 - r - 34 if i else 860, a)
    fig = figure(0.38)
    paste_c(im, fig, 540, 900, 0.0 if t2 < 99 and t < t2 else 0)
    paste_c(im, text_img("慈心禅", "black", 92, INK), 540, 300, ramp(t, ev_t(ev, 1), ev_t(ev, 1) + 0.6) if len(ev) > 1 else 1)
    if len(ev) > 3:
        a = ramp(t, ev[3][0], ev[3][0] + 0.8)
        paste_c(im, text_img("愿你平安 · 愿你健康 · 愿你快乐", "kai", 56, RED), 540, 1440 - 60, a)
    return im


def s_fred(t, T, ev):
    im = base()
    paste_c(im, text_img("Fredrickson 等 · JPSP 2008", "serif_r", 36, GREY), 540, 300)
    d = ImageDraw.Draw(im)
    t1 = ev_t(ev, 1, 2)
    r = rng(5)
    split = ramp(t, t1 + 1.0, t1 + 2.5)
    for i in range(139):
        g = i % 2
        gx, gy = (i // 2) % 10, (i // 2) // 10
        x = 540 + (-1 if g == 0 else 1) * (60 + 260 * split) + (gx - 4.5) * 24 * (0.6 + 0.4 * split)
        y = 560 + gy * 30
        col = (176, 46, 34, 230) if g == 0 else (90, 84, 76, 200)
        d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=col)
    if split > 0.5:
        d.text((240, 820), "慈心禅组", font=font("serif", 44), fill=RED, anchor="mm")
        d.text((840, 820), "排队等候组", font=font("serif", 44), fill=INK2, anchor="mm")
    paste_c(im, text_img("139 名在职成年人 · 随机分组", "kai", 46, INK), 540, 400, ramp(t, t1, t1 + 0.5))
    # curves
    t2 = ev_t(ev, 2, 99)
    c = ramp(t, t2, t2 + 4.0)
    if c > 0:
        x0, x1, yb = 140, 940, 1330
        d.line([(x0, yb), (x1, yb)], fill=INK2, width=3); d.line([(x0, yb), (x0, 930)], fill=INK2, width=3)
        d.text((x1, yb + 36), "时间 →", font=font("kai", 36), fill=INK2, anchor="rm")
        d.text((x0 + 10, 920), "每日积极情绪", font=font("kai", 36), fill=INK2, anchor="lm")
        n = int(80 * c)
        pts1 = [(x0 + (x1 - x0) * k / 80, yb - 60 - 300 * (k / 80) ** 1.6 + 8 * math.sin(k * 0.7)) for k in range(n + 1)]
        pts2 = [(x0 + (x1 - x0) * k / 80, yb - 60 - 10 * math.sin(k * 0.5)) for k in range(n + 1)]
        if len(pts1) > 1:
            d.line(pts1, fill=RED, width=10, joint="curve")
            d.line(pts2, fill=(120, 114, 104), width=8, joint="curve")
    if len(ev) > 4:
        paste_c(im, text_img("跑赢「享乐跑步机」", "black", 60, INK), 540, 1440 - 40, ramp(t, ev[4][0], ev[4][0] + 0.6))
    return im


def s_build(t, T, ev):
    im = base()
    paste_c(im, text_img("拓展与建构", "black", 96, INK), 540, 300, ramp(t, ev_t(ev, 2, 0), ev_t(ev, 2, 0) + 0.6) if len(ev) > 2 else 1)
    d = ImageDraw.Draw(im)
    # trunk
    g = ramp(t, 0, 2.5)
    tx, ty = 540, 1380
    brush_bar(im, tx - 22, ty - int(520 * g), 44, int(520 * g) + 2, INK, seed=90)
    paste_c(im, text_img("积极情绪", "serif", 52, RED), 540, 1430 - 20)
    res = [("觉察当下", 250, 980), ("目标感", 830, 960), ("社会支持", 270, 760), ("身体不适↓", 820, 760)]
    for i, (w, x, y) in enumerate(res):
        a = ramp(t, 1.0 + i * 0.9, 1.6 + i * 0.9)
        if a > 0:
            d.line([(tx, y + 120), (x, y)], fill=(32, 30, 28, int(200 * a)), width=8)
            d.ellipse([x - 120, y - 52, x + 120, y + 52], fill=(244, 236, 214, int(240 * a)), outline=(32, 30, 28, int(220 * a)), width=3)
            paste_c(im, text_img(w, "kai", 44, INK), x, y, a)
    if len(ev) > 1:
        a = ramp(t, ev[1][0], ev[1][0] + 0.8)
        paste_c(im, text_img("生活满意度↑  抑郁症状↓", "black", 58, RED), 540, 530, a)
    return im


def stamped_page(title, stamps, t, t0, seed=0):
    im = base()
    pg = Image.new("RGBA", (760, 900), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, 759, 899], fill=(248, 244, 234, 255), outline=(150, 140, 122, 255), width=2)
    d.text((380, 80), title, font=font("serif", 44), fill=INK, anchor="mm")
    r = rng(seed)
    for k in range(16):
        y = 160 + k * 40
        d.line([(60, y), (60 + r.uniform(450, 640), y)], fill=(150, 144, 132, 255), width=6)
    paste_c(im, pg, 540, 860)
    for i, s in enumerate(stamps):
        a = ramp(t, t0 + i * 0.9, t0 + i * 0.9 + 0.25)
        if a <= 0:
            continue
        sc = 1.0 + 0.6 * (1 - a)
        sim = seal(s, int(190), seed=seed + 100 + i, rot=(-8, 5, -3, 7)[i % 4])
        sim = sim.resize((int(sim.width * sc), int(sim.height * sc)))
        paste_c(im, sim, (330, 750, 380, 720)[i % 4], (600, 760, 1020, 1180)[i % 4], a)
    return im


def s_fredlim(t, T, ev):
    t0 = ev_t(ev, 1, 1)
    return stamped_page("慈心禅研究（2008）", ["单项研究", "企业员工", "候补对照"], t, t0, seed=7)


def s_hype(t, T, ev):
    im = base()
    pg = Image.new("RGBA", (800, 1000), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, 799, 999], fill=(248, 244, 234, 255), outline=(150, 140, 122, 255), width=2)
    d.text((400, 110), "Mind the Hype", font=font("black", 74), fill=INK, anchor="mm")
    d.text((400, 190), "《当心炒作》", font=font("kai", 56), fill=RED, anchor="mm")
    d.text((400, 260), "Van Dam 等 · Perspectives on", font=font("serif_r", 32), fill=INK2, anchor="mm")
    d.text((400, 305), "Psychological Science 13(1), 2018", font=font("serif_r", 32), fill=INK2, anchor="mm")
    r = rng(3)
    for k in range(13):
        y = 380 + k * 42
        d.line([(80, y), (80 + r.uniform(450, 640), y)], fill=(160, 154, 142, 255), width=6)
    paste_c(im, wipe(pg, ramp(t, 0, 1.0)), 540, 880)
    if len(ev) > 1:
        paste_c(im, text_img("15 位研究者联名", "black", 60, INK), 540, 260, ramp(t, ev[1][0] + 1.5, ev[1][0] + 2.1))
    return im


def s_hype1(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    paste_c(im, text_img("正念", "black", 150, INK), 540, 560)
    t1 = ev_t(ev, 1, 2)
    for i, w in enumerate(["注意力训练", "性格特质", "一整套课程"]):
        a = ramp(t, t1 + i * 1.4, t1 + i * 1.4 + 0.5)
        x = 200 + i * 340
        if a > 0:
            d.line([(540, 660), (x, 960)], fill=(32, 30, 28, int(220 * a)), width=6)
            paste_c(im, text_img(w, "serif", 48, INK), x, 1010, a)
    paste_c(im, text_img("定义不一", "serif", 54, RED), 540, 330, ramp(t, 0.4, 1.0))
    paste_c(im, text_img("名字一样，测的未必是一回事", "kai", 52, INK2), 540, 1220, ramp(t, ev_t(ev, 1, 99) + 4.5, ev_t(ev, 1, 99) + 5.2))
    return im


def s_hype2(t, T, ev):
    t0 = 0.6
    stamps = ["小样本", "无主动对照", "依赖自评", "宣传过度"]
    im = stamped_page("某冥想研究（示意）", stamps, t, t0, seed=21)
    if len(ev) > 2:
        a = ramp(t, ev[2][0], ev[2][0] + 0.6)
        paste_c(im, text_img("脑成像：易被过度解读\n副作用：需认真记录", "kai", 50, RED, spacing=16), 540, 300, a)
    return im


def s_pubbias(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    paste_c(im, text_img("发表偏差", "black", 92, INK), 540, 300)
    t1 = ev_t(ev, 1, 1)
    cols = 12
    a = ramp(t, t1, t1 + 3.5)
    for i in range(124):
        x = 540 + ((i % cols) - (cols - 1) / 2) * 66
        y = 480 + (i // cols) * 66
        if i < int(124 * a):
            pos = i < 108
            d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(176, 46, 34, 230) if pos else (150, 144, 132, 230))
    paste_c(im, text_img("124 项试验中 108 项阳性（87%）", "serif", 48, RED), 540, 1230, ramp(t, t1 + 3.5, t1 + 4.2))
    t2 = ev_t(ev, 2, 99)
    b = ramp(t, t2, t2 + 0.8)
    if b > 0:
        # expected ~66 line: after 66 dots -> row 5, col 6
        i = 66
        y = 480 + (i // cols) * 66
        d.line([(120, y + 33), (960, y + 33)], fill=(32, 30, 28, int(255 * b)), width=6)
        paste_c(im, text_img("按试验规模推算：约 66 项", "kai", 48, INK), 540, 1320, b)
        paste_c(im, text_img("实际约为预期的 1.6 倍", "black", 52, INK), 540, 1395, ramp(t, t2 + 2, t2 + 2.6))
    return im


def s_placebo(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    paste_c(im, text_img("安慰剂与期待效应", "black", 80, INK), 540, 320)
    cx, cy, R = 540, 1000, 330
    d.arc([cx - R, cy - R, cx + R, cy + R], 200, 340, fill=INK2, width=10)
    for k in range(9):
        ang = math.radians(200 + k * 17.5)
        d.line([(cx + (R - 30) * math.cos(ang), cy + (R - 30) * math.sin(ang)), (cx + R * math.cos(ang), cy + R * math.sin(ang))], fill=INK2, width=5)
    v = 0.25 + 0.5 * ramp(t, 0.5, T - 1.0) + 0.02 * math.sin(t * 5)
    ang = math.radians(200 + 140 * v)
    d.line([(cx, cy), (cx + (R - 50) * math.cos(ang), cy + (R - 50) * math.sin(ang))], fill=RED, width=12)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=INK)
    d.text((cx, cy + 80), "量表分数", font=font("kai", 50), fill=INK, anchor="mm")
    for i, w in enumerate(["花了时间", "交了学费", "相信会变好"]):
        a = ramp(t, 0.8 + i * 1.6, 1.3 + i * 1.6)
        paste_c(im, text_img(w, "serif", 46, INK2), 220 + i * 320, 520, a)
    return im


def s_lindahl(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    paste_c(im, text_img("Lindahl 等 · PLoS ONE 2017", "serif_r", 36, GREY), 540, 290)
    t1 = ev_t(ev, 1, 1)
    a = ramp(t, t1, t1 + 2.5)
    for i in range(int(92 * a)):
        g = i < 60
        x = 150 + (i % 16) * 52; y = 380 + (i // 16) * 56
        col = INK if g else (176, 46, 34)
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=col + (220,))
    if a > 0.6:
        d.text((300, 750), "● 60 位禅修者", font=font("serif", 40), fill=INK, anchor="mm")
        d.text((780, 750), "● 32 位老师与临床专家", font=font("serif", 40), fill=RED, anchor="mm")
    t2 = ev_t(ev, 2, 99)
    b = ramp(t, t2, t2 + 1.0)
    if b > 0:
        doms = ["认知", "知觉", "情绪", "躯体", "意志", "自我感", "人际"]
        for i, w in enumerate(doms):
            ang = -math.pi / 2 + i * 2 * math.pi / 7
            x, y = 540 + 280 * math.cos(ang), 1110 + 230 * math.sin(ang)
            d.ellipse([x - 70, y - 70, x + 70, y + 70], outline=(32, 30, 28, int(220 * b)), width=4)
            paste_c(im, text_img(w, "kai", 40, INK), x, y, b)
        paste_c(im, text_img("59 类体验\n7 个领域", "black", 50, INK, spacing=10), 540, 1110, b)
    t3 = ev_t(ev, 3, 99)
    c = ramp(t, t3, t3 + 0.6)
    if c > 0:
        lay = Image.new("RGBA", (W, H), PAPER + (0,)); lay.putalpha(int(215 * c)); im.alpha_composite(lay)
        paste_c(im, text_img("72%", "black", 200, RED), 540, 800, c)
        paste_c(im, text_img("的困难出现在密集禅修期间\n或刚结束之后", "kai", 56, INK, spacing=16), 540, 1000, c)
    t4 = ev_t(ev, 4, 99)
    if t > t4:
        s = seal("非发生率", 200, seed=111, rot=-6)
        paste_c(im, s, 540, 1250, ramp(t, t4 + 0.5, t4 + 0.9))
    return im


def s_zhiyi(t, T, ev):
    im = base()
    pg = Image.new("RGBA", (720, 1000), (0, 0, 0, 0))
    d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, 719, 999], fill=(232, 218, 188, 255), outline=(120, 96, 60, 255), width=4)
    for k in range(1, 7):
        d.line([(k * 720 / 7, 30), (k * 720 / 7, 970)], fill=(150, 120, 80, 120), width=2)
    pg.alpha_composite(vtext_img("修習止觀坐禪法要|治病第九", "kai", 76, INK), (150, 90))
    paste_c(im, pg, 540, 860, ramp(t, 0, 0.8))
    paste_c(im, text_img("天台智者大师（隋）", "kai", 44, INK2), 540, 300, ramp(t, 0.4, 1.0))
    if len(ev) > 1:
        a = ramp(t, ev[1][0], ev[1][0] + 0.6)
        box = text_img("如练习中明显不适\n请停下，寻求专业帮助", "black", 54, (250, 246, 236), spacing=16)
        bg = Image.new("RGBA", (box.width + 80, box.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 24, fill=RED + (235,))
        bg.alpha_composite(box, (40, 30))
        paste_c(im, bg, 540, 1290, a)
    return im


@functools.lru_cache(maxsize=1)
def moon_static():
    im = base(dark=True)
    im.alpha_composite(light_glow(760, 420, 380, (210, 214, 225), 0.35))
    d = ImageDraw.Draw(im)
    d.ellipse([700, 360, 820, 480], fill=(236, 232, 220, 255))
    im.alpha_composite(mountains(seed=13, y0=1050, layers=4, height=420, dark=True))
    return im


def s_yz(t, T, ev):
    im = moon_static().copy()
    lay = Image.new("RGBA", (W, H), (236, 229, 212, 0))
    lay.putalpha(int(255 * (1 - ramp(t, 0, 1.2))))
    im.alpha_composite(lay)
    fig = figure(0.5, color=(14, 16, 20))
    im.alpha_composite(fig, (540 - fig.width // 2, 1300 - fig.height))
    paste_c(im, text_img("印照", "black", 130, (236, 229, 212)), 540, 760, ramp(t, 0.8, 1.8))
    paste_c(im, text_img("不是证明", "kai", 56, (200, 190, 170)), 540, 890, ramp(t, 1.6, 2.4))
    return im


def quote_scene(t, T, ev, vt, src, qi, dark=True, extra=None):
    im = moon_static().copy() if dark else base()
    col = (236, 229, 212) if dark else INK
    tq = ev_t(ev, qi, 0)
    if t < tq - 0.2:
        a = ramp(t, 0, 0.6)
        if extra:
            paste_c(im, text_img(extra, "kai", 54, col), 540, 700, a)
        return im
    txt = vtext_img(vt, "kai", 118, col, gap=1.12)
    paste_c(im, wipe(txt, ramp(t, tq, tq + 2.6), "down"), 540, 840)
    paste_c(im, text_img(src, "kai", 38, (200, 190, 170) if dark else INK2), 540, 1400, ramp(t, tq + 1.5, tq + 2.2))
    s = seal("印照", 120, seed=141, rot=-3)
    paste_c(im, s, 830, 1220, ramp(t, tq + 2.4, tq + 2.8))
    return im


def s_jgj(t, T, ev):
    im = quote_scene(t, T, ev, "應無所住|而生其心", "《金剛般若波羅蜜經》 鳩摩羅什 譯", 2,
                     extra="五祖夜讲《金刚经》\n惠能言下大悟")
    t4 = ev_t(ev, 4, 99)
    if t > t4:
        a = ramp(t, t4, t4 + 0.5)
        lay = Image.new("RGBA", (W, H), (10, 11, 14, 0)); lay.putalpha(int(200 * a)); im.alpha_composite(lay)
        paste_c(im, vtext_img("不應住色生心|不應住聲香味觸法生心|應無所住而生其心", "kai", 66, (236, 229, 212)), 540, 860, a)
    return im


def s_tj(t, T, ev):
    return quote_scene(t, T, ev, "無念者|於念而無念", "《六祖大師法寶壇經·定慧品第四》", 1)


def s_wander(t, T, ev):
    im = base()
    fig = figure(0.8)
    cx, cy = 540, 1150
    im.alpha_composite(fig, (cx - fig.width // 2, cy + 200 - fig.height))
    d = ImageDraw.Draw(im)
    if len(ev) > 0 and t < ev_t(ev, 2, 99) - 0.2:
        paste_c(im, text_img("「游荡的心，\n是不快乐的心。」", "black", 70, INK, spacing=20), 540, 420, ramp(t, 0, 0.6))
        paste_c(im, text_img("Killingsworth & Gilbert, Science 2010", "serif_r", 32, GREY), 540, 590, ramp(t, 0.5, 1))
        return im
    thoughts = ["明天的会", "昨天的争执", "手机", "晚饭"]
    t3 = ev_t(ev, 3, 99)
    for i, w in enumerate(thoughts):
        ph = (t * 0.35 + i * 0.25) % 1.0
        back = ramp(t, t3, t3 + 2.0)
        dist = (120 + 380 * ease(ph)) * (1 - back)
        ang = -math.pi / 2 + (i - 1.5) * 0.55
        x, y = cx + dist * math.cos(ang) * 1.3, cy - 290 + dist * math.sin(ang) * 0.9
        a = (1 - ph * 0.6) * (1 - back * 0.7)
        d.line([(cx, cy - 300), (x, y)], fill=(176, 46, 34, int(120 * a)), width=3)
        b = text_img(w, "kai", 46, INK)
        bub = Image.new("RGBA", (b.width + 50, b.height + 34), (0, 0, 0, 0))
        ImageDraw.Draw(bub).rounded_rectangle([0, 0, bub.width - 1, bub.height - 1], 30, fill=(248, 244, 234, 230), outline=(32, 30, 28, 200), width=3)
        bub.alpha_composite(b, (25, 17))
        paste_c(im, bub, x, y, a)
    if t > t3:
        paste_c(im, text_img("发现 → 带回来", "black", 76, RED), 540, 360, ramp(t, t3, t3 + 0.6))
    return im


def s_notproof(t, T, ev):
    im = base()
    d = ImageDraw.Draw(im)
    a = ramp(t, 0, 0.8)
    for x, title, sub in [(290, "佛法", "解脱\n看清烦恼"), (790, "研究", "情绪量表\n几个分数")]:
        d.rounded_rectangle([x - 210, 560, x + 210, 1120], 24, fill=(246, 240, 226, int(240 * a)), outline=(32, 30, 28, int(200 * a)), width=3)
        paste_c(im, text_img(title, "black", 84, INK), x, 680, a)
        paste_c(im, text_img(sub, "kai", 54, INK2, spacing=18), x, 900, a)
    paste_c(im, text_img("≠", "black", 120, RED), 540, 840, ramp(t, 1.0, 1.6))
    s = seal("印照非证明", 240, seed=151, rot=-5)
    paste_c(im, s, 540, 1300, ramp(t, ev_t(ev, 2, 3), ev_t(ev, 2, 3) + 0.4))
    paste_c(im, text_img("类比 · 相互印照", "serif", 56, INK), 540, 360, a)
    return im


def s_breath(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 860, 700, DAWN, 0.3))
    per = 8.0
    ph = (t % per) / per
    k = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
    r = 180 + 160 * k
    c = ink_circle(1.0, r=int(r), width=26, seed=3)
    paste_c(im, c, 540, 860, 0.85)
    lab = "吸" if ph < 0.5 else "呼"
    paste_c(im, text_img(lab, "kai", 120, INK), 540, 860, 0.5 + 0.5 * abs(math.cos(math.pi * ph * 2)))
    paste_c(im, text_img("回到呼吸", "black", 80, INK), 540, 330, ramp(t, ev_t(ev, 2, 1), ev_t(ev, 2, 1) + 0.6))
    if len(ev) > 6:
        paste_c(im, text_img("一呼一吸 · 数一 …… 数到十", "kai", 52, INK2), 540, 1330, ramp(t, ev[6][0], ev[6][0] + 0.6))
    return im


@functools.lru_cache(maxsize=1)
def street_static():
    im = base()
    im.alpha_composite(light_glow(540, 520, 900, DAWN, 0.5))
    d = ImageDraw.Draw(im)
    r = rng(17)
    # alley: rows of houses with tiled roofs on both sides converging
    for side in (-1, 1):
        for k in range(6):
            depth = k / 6
            x = 540 + side * (480 - 330 * depth)
            w = 240 * (1 - 0.65 * depth)
            top = 760 + 160 * depth
            bot = 1400 - 300 * depth
            xa, xb = (x - w, x) if side < 0 else (x, x + w)
            g = int(110 + 80 * depth)
            d.rectangle([xa, top, xb, bot], fill=(g, g - 6, g - 14, 200))
            d.polygon([(xa - 20, top + 10), (xb + 20, top + 10), ((xa + xb) / 2, top - 60 * (1 - 0.6 * depth))], fill=(g - 50, g - 54, g - 60, 230))
    d.polygon([(380, 1400), (700, 1400), (590, 980), (490, 980)], fill=(210, 200, 182, 160))
    return im


def s_street(t, T, ev):
    im = street_static().copy()
    p = ramp(t, 0.5, T)
    sc = 1.0 - 0.55 * p
    wk = walker(round(sc, 2), int(t * 3) % 4)
    paste_c(im, wk, 540 + 20 * p, 1330 - 340 * p - wk.height / 2 + 120)
    if t < 1.2:  # rising from seat
        fig = figure(0.6)
        paste_c(im, fig, 540, 1260, 1 - ramp(t, 0.2, 1.0))
    a = ramp(t, 0.6, 1.6)
    paste_c(im, text_img("把走散的心\n一次次带回来", "black", 84, INK, spacing=24), 540, 400, a)
    return im


def s_end(t, T, ev):
    im = base()
    im.alpha_composite(light_glow(540, 860, 700, DAWN, 0.3))
    tq = ev_t(ev, 1, 2)
    if t < tq - 0.2:
        paste_c(im, text_img("六祖 · 无相颂", "kai", 60, INK2), 540, 760, ramp(t, 0, 0.6))
        return im
    t4 = ev_t(ev, 3, 99)
    a_out = 1 - ramp(t, t4 - 0.4, t4 + 0.4)
    txt = vtext_img("心平何勞持戒|行直何用修禪", "kai", 118, INK, gap=1.1)
    paste_c(im, wipe(txt, ramp(t, tq, tq + 2.8), "left"), 540, 800, a_out)
    paste_c(im, text_img("《六祖大師法寶壇經·疑問品第三》", "kai", 40, INK2), 540, 1330, ramp(t, tq + 1.5, tq + 2.2) * a_out)
    if t > t4 - 0.4:
        b = ramp(t, t4, t4 + 0.8)
        paste_c(im, text_img("坐，只是方法", "black", 96, INK), 540, 700, b)
        paste_c(im, text_img("心，才是归处", "black", 96, RED), 540, 860, ramp(t, t4 + 1.0, t4 + 1.8))
        s = seal("静坐的科学", 180, seed=171, rot=-4)
        paste_c(im, s, 540, 1150, ramp(t, t4 + 2.0, t4 + 2.5))
    return im


SCENES = {
    "hook": s_hook, "hook_q": s_hook_q, "stat": s_stat, "paper": s_paper, "bars": s_bars, "causal": s_causal,
    "title": s_title, "funnel": s_funnel, "control": s_control, "scroll": s_scroll, "es": s_es,
    "scroll2": s_scroll2, "verdict": s_verdict, "metta": s_metta, "fred": s_fred, "build": s_build,
    "fredlim": s_fredlim, "hype": s_hype, "hype1": s_hype1, "hype2": s_hype2, "pubbias": s_pubbias,
    "placebo": s_placebo, "lindahl": s_lindahl, "zhiyi": s_zhiyi, "yz": s_yz, "jgj": s_jgj, "tj": s_tj,
    "wander": s_wander, "notproof": s_notproof, "breath": s_breath, "street": s_street, "end": s_end,
}

# section tag, evidence-type chip, source
META = {
    "hook": ("一 · 走神的心", None, None),
    "hook_q": ("一 · 走神的心", None, None),
    "stat": ("一 · 走神的心", "实证 · 相关研究", "Killingsworth & Gilbert, Science 2010"),
    "paper": ("一 · 走神的心", "实证 · 相关研究", "Killingsworth & Gilbert, Science 330:932 (2010)"),
    "bars": ("一 · 走神的心", "实证 · 相关研究", "Killingsworth & Gilbert, Science 2010"),
    "causal": ("一 · 走神的心", "相关研究 · 不能直接说明因果", "Killingsworth & Gilbert, Science 2010"),
    "title": ("静坐的科学", None, None),
    "funnel": ("二 · 证据有多硬", "实证 · 系统综述与元分析", "Goyal et al., JAMA Intern Med 174(3):357–368 (2014)"),
    "control": ("二 · 证据有多硬", "实证 · 系统综述与元分析", "Goyal et al., JAMA Intern Med 2014"),
    "scroll": ("二 · 证据有多硬", "实证 · 系统综述与元分析", "Goyal et al., JAMA Intern Med 2014"),
    "es": ("二 · 证据有多硬", "实证 · 系统综述与元分析", "Goyal et al., JAMA Intern Med 2014"),
    "scroll2": ("二 · 证据有多硬", "实证 · 系统综述与元分析", "Goyal et al., JAMA Intern Med 2014"),
    "verdict": ("二 · 证据有多硬", None, None),
    "metta": ("三 · 慈心与积极情绪", None, None),
    "fred": ("三 · 慈心与积极情绪", "实证 · 单项研究", "Fredrickson et al., JPSP 95(5):1045–1062 (2008)"),
    "build": ("三 · 慈心与积极情绪", "实证 · 单项研究", "Fredrickson et al., JPSP 2008"),
    "fredlim": ("三 · 慈心与积极情绪", "局限 · 单项研究、候补对照", "Fredrickson et al., JPSP 2008"),
    "hype": ("四 · 局限与提醒", "争议与局限", "Van Dam et al., Perspect Psychol Sci 13(1):36–61 (2018)"),
    "hype1": ("四 · 局限与提醒", "争议与局限", "Van Dam et al., 2018"),
    "hype2": ("四 · 局限与提醒", "争议与局限", "Van Dam et al., 2018（印章为示意）"),
    "pubbias": ("四 · 局限与提醒", "争议与局限", "Coronado-Montoya et al., PLoS ONE 11(4):e0153220 (2016)"),
    "placebo": ("四 · 局限与提醒", "争议与局限", "Van Dam et al., 2018"),
    "lindahl": ("四 · 局限与提醒", "质性研究 · 小样本", "Lindahl et al., PLoS ONE 12(5):e0176239 (2017)"),
    "zhiyi": ("四 · 局限与提醒", None, "智顗《修習止觀坐禪法要》（CBETA T46n1915）"),
    "yz": ("五 · 印照", None, None),
    "jgj": ("五 · 印照", "类比 · 印照", None),
    "tj": ("五 · 印照", "类比 · 印照", None),
    "wander": ("五 · 印照", "类比 · 印照，不是证明", None),
    "notproof": ("五 · 印照", None, None),
    "breath": ("六 · 带回生活", None, None),
    "street": ("六 · 带回生活", None, None),
    "end": ("六 · 带回生活", None, None),
}
HELP_SCENES = {"es", "verdict"}  # show "如有困扰请寻求专业帮助"
