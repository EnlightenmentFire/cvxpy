# -*- coding: utf-8 -*-
"""各分镜画面。每个函数 f(cv, t, T, L, P, C)：t 场内秒，T 场长，L 每句起始（场内秒），P 参数，C 场内缓存"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from eng import *

QY = 330      # 古文卡中心 y
SUBY = 1488   # 字幕中心 y


def Lt(L, k, default=1e9):
    return L[k] if 0 <= k < len(L) else default


def zoom_bg(cv, bg, t, T, z0=1.0, z1=1.08, cx=0.5, cy=0.5):
    z = z0 + (z1 - z0) * ease(t / max(T, 0.1))
    w, h = W / z, H / z
    x0 = (bg.width - w) * cx; y0 = (bg.height - h) * cy
    im = bg.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))
    cv.paste(im, (0, 0))


def embers(C, key='emb', n=60, seed=5, cols=(ORANGE, (255, 200, 120), RED2), box=(0, 0, W, H), vel=((-12, 12), (-70, -25)), size=(1.2, 3.6)):
    if key not in C: C[key] = Field(n, seed, box, vel, size, cols)
    return C[key]


def card_in(cv, im, t, t0, t1=1e9, y=QY, x=W / 2):
    a = window(t, t0, t1, 0.45, 0.4)
    if a <= 0: return
    put(cv, im, x, y + (1 - eout((t - t0) / 0.5)) * 30, a)


# ════════════ 0 钩子：咸阳车驾 ════════════
def _procession_bg(C):
    if 'bg' in C: return C['bg']
    w, h = int(W * 1.1), int(H * 1.1)
    arr = grad_bg((14, 18, 26), (20, 14, 10), w, h, mid=(150, 92, 46), midpos=0.42)
    n = fnoise(w, h, 21, 5, 3)
    arr *= (0.8 + 0.35 * n[..., None])
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    sun = np.exp(-(((x - w * 0.5) / 260) ** 2 + ((y - h * 0.40) / 120) ** 2))
    arr += sun[..., None] * np.array([255, 170, 80]) * 0.85
    im = to_img(arr); d = ImageDraw.Draw(im)
    hy = int(h * 0.42)
    # 咸阳宫阙剪影
    r = random.Random(3)
    for k in range(26):
        cx = r.uniform(0, w); bw = r.uniform(60, 180); bh = r.uniform(30, 120)
        col = (30, 22, 22, 255)
        d.rectangle((cx - bw / 2, hy - bh, cx + bw / 2, hy + 4), fill=col)
        d.polygon([(cx - bw / 2 - 26, hy - bh), (cx, hy - bh - 34), (cx + bw / 2 + 26, hy - bh)], fill=col)
    for cx, bh in [(w * 0.5, 230), (w * 0.33, 160), (w * 0.67, 170)]:
        col = (22, 16, 18, 255)
        for lv in range(3):
            ww = 220 - lv * 50; yy = hy - bh * (lv + 1) / 3
            d.rectangle((cx - ww / 2, yy, cx + ww / 2, yy + bh / 3 + 4), fill=col)
            d.polygon([(cx - ww / 2 - 50, yy + 6), (cx - ww / 2 + 10, yy - 26), (cx + ww / 2 - 10, yy - 26), (cx + ww / 2 + 50, yy + 6)], fill=col)
    # 大道（透视）
    d.polygon([(w * 0.47, hy), (w * 0.53, hy), (w * 1.05, h), (-w * 0.05, h)], fill=(58, 40, 28, 255))
    for k in range(14):
        f = (k / 14) ** 2
        yy = hy + (h - hy) * f
        d.line((w * 0.5 - (w * 0.55) * f, yy, w * 0.5 + (w * 0.55) * f, yy), fill=(70, 50, 34, 255), width=1 + int(3 * f))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    C['bg'] = im; C['hy'] = hy / 1.1
    return im


def procession(cv, t, T, L, P, C):
    bg = _procession_bg(C)
    zoom_bg(cv, bg, t, T, 1.0, 1.07, 0.5, 0.45)
    hy = 806
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # 车驾队列：从远处向近处行进（透视）
    for lane in (-1, 1):
        for k in range(16):
            f = ((k / 16 + t * 0.045) % 1.0)
            ff = f ** 2.2
            y = hy + (1340 - hy) * ff
            s = 0.08 + 1.1 * ff
            x = 540 + lane * (30 + 330 * ff)
            soldier(d, x, y, s, (10, 8, 8, int(255 * clamp(f * 4))), True, (28, 24, 26, 255) if k % 4 == 0 else None)
    # 中央车驾（伞盖）
    f = ((0.35 + t * 0.045) % 1.0); ff = f ** 2.2
    y = hy + (1340 - hy) * ff; s = 0.12 + 1.3 * ff; x = 540
    col = (10, 8, 8, 255)
    d.rectangle((x - 70 * s, y - 70 * s, x + 70 * s, y - 20 * s), fill=col)
    d.ellipse((x - 95 * s, y - 40 * s, x - 45 * s, y + 10 * s), outline=col, width=max(1, int(8 * s)))
    d.ellipse((x + 45 * s, y - 40 * s, x + 95 * s, y + 10 * s), outline=col, width=max(1, int(8 * s)))
    d.line((x, y - 70 * s, x, y - 200 * s), fill=col, width=max(1, int(6 * s)))
    d.chord((x - 110 * s, y - 250 * s, x + 110 * s, y - 160 * s), 180, 360, fill=col)
    d.polygon([(x - 110 * s, y - 205 * s), (x + 110 * s, y - 205 * s), (x + 90 * s, y - 190 * s), (x - 90 * s, y - 190 * s)], fill=(60, 40, 16, 255))
    for hk in (-1, 1):  # 马
        hx = x + hk * 40 * s; hyy = y + 40 * s
        d.ellipse((hx - 30 * s, hyy - 70 * s, hx + 30 * s, hyy - 30 * s), fill=col)
        d.line((hx, hyy - 50 * s, hx + 10 * s, hyy - 100 * s), fill=col, width=max(1, int(12 * s)))
    cv.alpha_composite(ov)
    # 尘土
    embers(C, 'dust', 70, 7, ((200, 150, 100), (160, 120, 90)), (0, 700, W, 1500), ((-30, 30), (-20, -5)), (2, 6)).draw(cv, t, 0.5)
    embers(C).draw(cv, t, 0.8)
    # 前景人群
    if 'crowd' not in C:
        cr = Image.new('RGBA', (W, 700), (0, 0, 0, 0)); dd = ImageDraw.Draw(cr)
        r = random.Random(9)
        for k in range(22):
            x = r.uniform(-40, W + 40); s = r.uniform(0.9, 1.4); y = r.uniform(380, 560)
            dd.ellipse((x - 55 * s, y - 60 * s, x + 55 * s, y + 55 * s), fill=(4, 4, 5, 255))
            dd.polygon([(x - 150 * s, 700), (x - 120 * s, y + 70 * s), (x + 120 * s, y + 70 * s), (x + 150 * s, 700)], fill=(4, 4, 5, 255))
        C['crowd'] = cr
        C['bang'] = bust('bang', 760, (5, 5, 6, 255), rim=(255, 170, 90))
    put(cv, C['crowd'], W / 2 + 20 * math.sin(t * 0.3), H - 350, 1.0)
    # 刘邦背影（金边）
    put(cv, C['bang'], 300, 1620 + 10 * math.sin(t * 0.5), 1.0, scale=0.85)
    # 文字：嗟乎
    a = window(t, 0.0, Lt(L, 1) - 0.2, 0.01, 0.4)
    if a > 0:
        q = qcard('嗟乎，大丈夫當如此也！', '《史記·高祖本紀》', '唉，大丈夫就该这样。', 900, 64)
        put(cv, q, W / 2, 330, a)
    # 闪切：刘邦/刘备 → 问号
    t1 = Lt(L, 1)
    if t1 - 0.2 < t < t1 + 3.4:
        _flash(cv, t - t1, C)
    t2 = Lt(L, 2)
    if t > t2 - 0.1:
        a = appear(t, t2, 0.5)
        put(cv, txt('刘季', 150, 'brush', RED2, glow=22, gcol=(200, 40, 20)), W / 2, 330, a)
        put(cv, txt('后来的汉高祖 · 刘邦', 46, 'serifsc', GOLD2, 2, glow=8, gcol=(0, 0, 0)), W / 2, 470, a)


def _flash(cv, u, C):
    if 'zhuo_mini' not in C:
        bg = Image.new('RGBA', (W, H), (40, 22, 12, 255))
        dd = ImageDraw.Draw(bg)
        for k in range(9):
            x = 80 + k * 120; dd.ellipse((x - 40, 300, x + 40, 380), fill=(255, 150, 60, 120))
        C['zhuo_mini'] = bg
        C['bei'] = bust('bei', 820, (6, 5, 5, 255), rim=(255, 120, 70))
        C['bang2'] = bust('bang', 820, (6, 5, 5, 255), rim=(255, 120, 70))
    # 0-0.5: 左右分屏闪切；0.5-1.6：两脸合拢；之后问号
    if u < 0.0: return
    if u < 1.7:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        k = eout((u - 0.7) / 0.9) if u > 0.7 else 0
        d.rectangle((0, 560, W, 1380), fill=(14, 6, 4, int(235 * min(1, u * 5))))
        cv.alpha_composite(ov)
        sw = (int(u * 6) % 2 == 0)
        lx = 270 + 270 * k; rx = 810 - 270 * k
        a_l = 1.0 if (sw or u > 0.7) else 0.35; a_r = 1.0 if (not sw or u > 0.7) else 0.35
        put(cv, C['bang2'], lx, 1000, a_l * (1 - k * 0.6), scale=0.62)
        put(cv, C['bei'], rx, 1000, a_r * (1 - k * 0.6), scale=0.62)
        put(cv, txt('刘邦 · 秦末', 40, 'black', RED2, 3), 270, 1310, (1 - k))
        put(cv, txt('刘备 · 东汉末', 40, 'black', RED2, 3), 810, 1310, (1 - k))
    a = window(u, 1.1, 3.4, 0.4, 0.5)
    if a > 0:
        put(cv, txt('？', 400, 'black', RED2, glow=40, gcol=(220, 40, 20)), W / 2, 960, a, scale=0.8 + 0.2 * eout((u - 1.1) / 0.6))
        put(cv, txt('父 ？  母 ？', 70, 'serifsc', GOLD2, 3), W / 2, 1270, a)


# ════════════ 名字 ════════════
def names(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(2))
    embers(C, n=40).draw(cv, t, 0.6)
    # 卷轴
    pw = int(760 * eout(t / 1.0)); top, bot = 470, 1250
    if pw > 10:
        tex = paper_tex()
        if 'scroll' not in C:
            arr = np.stack([200 + 30 * tex, 180 + 28 * tex, 140 + 24 * tex], -1)[top:bot, 160:920]
            C['scroll'] = to_img(arr)
        sc = C['scroll'].crop((380 - pw // 2, 0, 380 + pw // 2, bot - top))
        cv.alpha_composite(sc, (540 - pw // 2, top))
        d = ImageDraw.Draw(cv)
        for x in (540 - pw // 2, 540 + pw // 2):
            d.rectangle((x - 16, top - 30, x + 16, bot + 30), fill=(70, 36, 20, 255))
            d.rectangle((x - 22, top - 44, x + 22, top - 30), fill=(150, 110, 50, 255))
            d.rectangle((x - 22, bot + 30, x + 22, bot + 44), fill=(150, 110, 50, 255))
    a = appear(t, 0.7, 0.6)
    if a > 0:
        put(cv, vtxt('父曰太公', 110, 'serif', (40, 20, 14)), 680, 860, a)
        put(cv, vtxt('母曰劉媼', 110, 'serif', (40, 20, 14)), 400, 860, a)
        put(cv, txt('《史記·高祖本紀》', 34, 'serif', (110, 60, 30)), 540, 1205, a)
    # 翻译
    t1 = Lt(L, 1)
    a = appear(t, t1, 0.4)
    if a > 0:
        put(cv, txt('＝「刘老爷子」', 60, 'black', RED, 4, (250, 240, 220)), 680, 560 + 0 * (1 - a), a)
        put(cv, txt('＝「刘大娘」', 60, 'black', RED, 4, (250, 240, 220)), 400, 1150, a)
    t2 = Lt(L, 2)
    a = appear(t, t2, 0.5)
    if a > 0:
        ov = Image.new('RGBA', (W, H), (6, 4, 4, int(222 * a))); cv.alpha_composite(ov)
        put(cv, txt('开国皇帝的父母', 64, 'serifsc', GOLD2, 3), W / 2, 700, a)
        # 印章：无名
        s = 1.6 - 0.6 * eout((t - t2) / 0.35)
        seal = C.get('seal')
        if seal is None:
            seal = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(seal)
            d.rounded_rectangle((10, 10, 290, 290), 18, fill=(190, 30, 24, 235))
            d.rounded_rectangle((26, 26, 274, 274), 12, outline=(255, 220, 200, 200), width=4)
            tt = vtxt('无名', 110, 'brush', (255, 236, 220), 4)
            seal.alpha_composite(tt, ((300 - tt.width) // 2, (300 - tt.height) // 2))
            seal = seal.rotate(-8, Image.BICUBIC, expand=True); C['seal'] = seal
        put(cv, seal, W / 2, 980, a, scale=s)
        put(cv, txt('正史只留下称呼', 48, 'sans', WHITE, 2), W / 2, 1250, appear(t, t2 + 0.5, 0.5))


# ════════════ 亭长 ════════════
def _pavilion(d, x, y, s, col):
    d.rectangle((x - 60 * s, y - 120 * s, x + 60 * s, y), fill=col)
    d.polygon([(x - 120 * s, y - 115 * s), (x - 70 * s, y - 165 * s), (x + 70 * s, y - 165 * s), (x + 120 * s, y - 115 * s)], fill=col)
    d.rectangle((x - 40 * s, y - 250 * s, x + 40 * s, y - 165 * s), fill=col)
    d.polygon([(x - 95 * s, y - 245 * s), (x - 30 * s, y - 310 * s), (x + 30 * s, y - 310 * s), (x + 95 * s, y - 245 * s)], fill=col)
    d.line((x, y - 310 * s, x, y - 420 * s), fill=col, width=max(2, int(5 * s)))
    d.rectangle((x - 20 * s, y - 70 * s, x + 20 * s, y), fill=(255, 170, 80, 255))


def ting_intro(cv, t, T, L, P, C):
    if 'bg' not in C:
        w, h = int(W * 1.08), int(H * 1.08)
        arr = grad_bg((8, 12, 22), (18, 16, 16), w, h, mid=(40, 46, 66), midpos=0.55)
        n = fnoise(w, h, 31, 5, 3); arr *= (0.8 + 0.4 * n[..., None])
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        moon = np.exp(-(((x - w * 0.80) / 70) ** 2 + ((y - h * 0.40) / 70) ** 2) * 1.0)
        arr += moon[..., None] * np.array([240, 230, 200]) * 0.9
        halo = np.exp(-(((x - w * 0.80) / 300) ** 2 + ((y - h * 0.40) / 300) ** 2))
        arr += halo[..., None] * np.array([60, 70, 90]) * 0.6
        im = to_img(arr); d = ImageDraw.Draw(im)
        # 山丘与路
        pts = [(0, h * 0.70)] + [(x, h * 0.66 - 60 * math.sin(x / 210) - 30 * math.sin(x / 77)) for x in range(0, w + 20, 20)] + [(w, h), (0, h)]
        d.polygon(pts, fill=(10, 10, 14, 255))
        d.line([(w * 0.2, h), (w * 0.45, h * 0.75), (w * 0.62, h * 0.67)], fill=(48, 40, 34, 255), width=30, joint='curve')
        _pavilion(d, w * 0.58, h * 0.665, 1.25, (6, 6, 8, 255))
        C['bg'] = im
    zoom_bg(cv, C['bg'], t, T, 1.0, 1.06, 0.55, 0.6)
    embers(C, 'f', 30, 4, ((255, 200, 140),), (500, 900, 900, 1300), ((-5, 5), (-25, -8)), (1, 2.5)).draw(cv, t, 0.7)
    a = appear(t, 0.2, 0.6)
    put(cv, txt('白丁？', 120, 'brush', GREY, glow=10, gcol=(0, 0, 0)), W / 2, 360, window(t, 0.1, Lt(L, 1) + 0.2))
    t1 = Lt(L, 1)
    a = appear(t, t1, 0.5)
    if a > 0:
        fo = 1 - appear(t, Lt(L, 2) - 0.1, 0.35)
        put(cv, txt('泗水亭长', 150, 'brush', GOLD2, glow=20, gcol=(160, 90, 20)), W / 2, 330, a * fo, scale=1.15 - 0.15 * eout((t - t1) / 0.5))
        put(cv, tag('秦朝 · 正式在编的基层吏员', GOLD, 36), W / 2, 480, appear(t, t1 + 0.6, 0.5) * fo)
    t2 = Lt(L, 2)
    card_in(cv, qcard('及壯，試為吏，為泗水亭長，廷中吏無所不狎侮。', '《史記·高祖本紀》', '县衙里的吏员，没有他不敢开玩笑的。', 940, 48), t, t2, 1e9, y=QY)


# ════════════ 涿县草鞋摊 ════════════
def stall(cv, t, T, L, P, C):
    if 'bg' not in C:
        w, h = int(W * 1.08), int(H * 1.08)
        arr = grad_bg((10, 8, 10), (30, 18, 12), w, h, mid=(46, 28, 20), midpos=0.5)
        n = fnoise(w, h, 41, 5, 3); arr *= (0.75 + 0.45 * n[..., None])
        im = to_img(arr); d = ImageDraw.Draw(im)
        r = random.Random(4)
        # 街屋
        for k in range(8):
            x = k * 160 - 40; bh = r.uniform(380, 520)
            d.rectangle((x, h * 0.62 - bh, x + 150, h * 0.62), fill=(14, 10, 10, 255))
            d.polygon([(x - 30, h * 0.62 - bh), (x + 75, h * 0.62 - bh - 70), (x + 180, h * 0.62 - bh)], fill=(12, 9, 9, 255))
        d.rectangle((0, h * 0.62, w, h), fill=(26, 18, 14, 255))
        # 摊子
        sx, sy = w * 0.52, h * 0.78
        d.rectangle((sx - 300, sy - 40, sx + 300, sy), fill=(60, 36, 20, 255))
        d.rectangle((sx - 300, sy, sx - 280, sy + 160), fill=(40, 24, 14, 255)); d.rectangle((sx + 280, sy, sx + 300, sy + 160), fill=(40, 24, 14, 255))
        d.line((sx - 330, sy - 330, sx + 330, sy - 330), fill=(50, 30, 18, 255), width=10)
        for k in range(9):  # 挂着的草鞋
            x = sx - 280 + k * 70
            d.line((x, sy - 330, x, sy - 250), fill=(150, 120, 70, 255), width=2)
            d.ellipse((x - 18, sy - 250, x + 18, sy - 170), fill=(170, 136, 80, 255), outline=(110, 80, 40, 255), width=3)
            for j in range(4): d.line((x - 14, sy - 235 + j * 18, x + 14, sy - 235 + j * 18), fill=(120, 90, 50, 255), width=2)
        for k in range(6):  # 摊面草鞋
            x = sx - 230 + k * 90
            d.ellipse((x - 34, sy - 62, x + 34, sy - 36), fill=(180, 145, 85, 255))
        # 席子卷
        d.ellipse((sx + 180, sy - 120, sx + 260, sy - 40), fill=(150, 120, 70, 255), outline=(90, 66, 36, 255), width=6)
        im = im.filter(ImageFilter.GaussianBlur(0.8))
        C['bg'] = im
        C['bei'] = bust('bei', 640, (8, 6, 6, 255), rim=(255, 150, 80))
        C['lan'] = Field(14, 8, (0, 300, W, 900), ((-3, 3), (-2, 2)), (14, 26), ((255, 150, 60), (255, 110, 40)), True)
    zoom_bg(cv, C['bg'], t, T, 1.0, 1.07, 0.5, 0.5)
    C['lan'].draw(cv, t, 0.55, 4)
    put(cv, C['bei'], 340, 1260, 1.0)
    embers(C, n=30).draw(cv, t, 0.6)
    a = appear(t, 0.0, 0.5)
    put(cv, txt('四百年后', 120, 'brush', GOLD2, glow=18, gcol=(150, 80, 20)), W / 2, 300, a * (1 - appear(t, Lt(L, 1) - 0.2, 0.4)))
    put(cv, txt('东汉 · 幽州涿县', 44, 'serifsc', GREY, 2), W / 2, 420, a * (1 - appear(t, Lt(L, 1) - 0.2, 0.4)))
    t1 = Lt(L, 1)
    a = appear(t, t1, 0.5)
    if a > 0:
        put(cv, tag('自称', GOLD, 30), W / 2, 250, a)
        put(cv, txt('汉景帝之子 · 中山靖王之后', 58, 'serifsc', GOLD2, 3, glow=10, gcol=(120, 70, 10)), W / 2, 340, a)
    t2 = Lt(L, 2)
    a = appear(t, t2, 0.5)
    if a > 0:
        put(cv, tag('现实', RED2, 30), W / 2, 450, a)
        put(cv, txt('少孤 · 卖草鞋 · 织席子', 58, 'black', RED2, 3), W / 2, 540, a)


# ════════════ 网友两派 ════════════
def debate(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(3))
    if 'b1' not in C:
        C['b1'] = bust('bang', 560, (6, 6, 8, 255), rim=(255, 110, 70))
        C['b2'] = bust('bei', 560, (6, 6, 8, 255), rim=(255, 110, 70))
    put(cv, C['b1'], 290, 860, appear(t, 0, 0.5))
    put(cv, C['b2'], 790, 860, appear(t, 0.2, 0.5))
    put(cv, txt('刘邦', 54, 'black', RED2, 3), 290, 1130, appear(t, 0, 0.5))
    put(cv, txt('刘备', 54, 'black', RED2, 3), 790, 1130, appear(t, 0.2, 0.5))
    a = appear(t, 0.3, 0.5)
    put(cv, txt('谁才是草根？', 110, 'brush', GOLD2, glow=16, gcol=(140, 80, 10)), W / 2, 330, a, scale=1.1 - 0.1 * a)
    for k, (s, col, y) in enumerate([('一派：两个都是草根', (230, 200, 160), 1250), ('另一派：两个都不是', (160, 200, 230), 1360)]):
        tt = Lt(L, k + 1)
        a = appear(t, tt, 0.4)
        if a > 0:
            b = tag(s, col, 44, 50)
            put(cv, b, W / 2 + (1 - eout((t - tt) / 0.4)) * (-300 if k == 0 else 300), y, a)


# ════════════ 两把尺子 ════════════
RUL = [(250, '出身天花板', '家世最多能把他托到多高'), (620, '实际政治购买力', '起步那一刻手里能调动什么')]
RX0, RX1 = 110, 970


def ruler(cv, y, title, sub, a=1.0, prog=1.0, ticks=('低', '中', '高')):
    if a <= 0: return
    put(cv, txt(title, 60, 'brush', GOLD2, glow=10, gcol=(120, 70, 10)), RX0, y - 80, a, 'lm')
    put(cv, txt(sub, 32, 'sans', GREY), RX0, y - 22, a, 'lm')
    d = ImageDraw.Draw(cv)
    x1 = RX0 + (RX1 - RX0) * eout(prog)
    al = int(255 * a)
    d.rectangle((RX0, y + 30, x1, y + 44), fill=GOLD + (al,))
    for k in range(21):
        x = RX0 + (RX1 - RX0) * k / 20
        if x > x1: break
        hh = 36 if k % 5 == 0 else 18
        d.line((x, y + 44, x, y + 44 + hh), fill=GOLD + (al,), width=3 if k % 5 == 0 else 2)
    for k, s in enumerate(ticks):
        x = RX0 + (RX1 - RX0) * k / 2
        if x <= x1 + 1: put(cv, txt(s, 30, 'sans', GOLD), x, y + 110, a)


def rdot(cv, y, frac, label, a=1.0, col=RED2, below=False, t=0):
    x = RX0 + (RX1 - RX0) * frac
    put(cv, dot_sprite(16, col, 1.0), x, y + 37, a)
    ring(cv, x, y + 37, 26 + 4 * math.sin(t * 4), col, a * 0.8, 3)
    put(cv, txt(label, 40, 'black', WHITE, 3, (90, 10, 0)), x, y + (215 if below else 165), a)


def rulers_intro(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(4))
    embers(C, n=40).draw(cv, t, 0.5)
    oy = 560  # 画面中部
    t0, t1, t2, t3, t4 = [Lt(L, k) for k in range(5)]
    # 单把尺子：出身
    a = window(t, 0, t1 + 0.3, 0.4, 0.5)
    if a > 0:
        ruler(cv, 900, '出身', '大家只用这一把量', a, appear(t, 0.2, 1.0), ('寒门', '', '豪门'))
        if t > t1 - 0.3:
            k = appear(t, t1 - 0.3, 0.4)
            d = ImageDraw.Draw(cv)
            d.line((520, 820, 600, 1060), fill=RED2 + (int(255 * k),), width=10)
    ruler(cv, oy + RUL[0][0], RUL[0][1], RUL[0][2], appear(t, t2, 0.5), appear(t, t2, 1.0))
    ruler(cv, oy + RUL[1][0], RUL[1][1], RUL[1][2], appear(t, t3, 0.5), appear(t, t3, 1.0))
    a = appear(t, t1, 0.5) * (1 - appear(t, t2 - 0.2, 0.3))
    put(cv, txt('换两把尺子', 110, 'brush', GOLD2, glow=16, gcol=(140, 80, 10)), W / 2, 960, a)
    a = appear(t, t4, 0.5)
    if a > 0:
        put(cv, txt('答案出人意料', 80, 'brush', RED2, glow=16, gcol=(200, 40, 10)), W / 2, 380, a)
        put(cv, txt('?', 70, 'black', WHITE, 3), RX0 + 0.5 * (RX1 - RX0), oy + RUL[0][0] - 8, a * (0.6 + 0.4 * math.sin(t * 5)))
        put(cv, txt('?', 70, 'black', WHITE, 3), RX0 + 0.5 * (RX1 - RX0), oy + RUL[1][0] - 8, a * (0.6 + 0.4 * math.cos(t * 5)))


def rulers_score(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(4))
    embers(C, n=40).draw(cv, t, 0.5)
    oy = 520
    ruler(cv, oy + RUL[0][0], RUL[0][1], RUL[0][2], appear(t, 0, 0.4), 1)
    ruler(cv, oy + RUL[1][0], RUL[1][1], RUL[1][2], appear(t, 0.2, 0.4), 1)
    if P['who'] == 'liubang':
        t0, t1 = Lt(L, 0), Lt(L, 1)
        put(cv, txt('刘邦：县吏网络中的一员', 64, 'brush', GOLD2, glow=12, gcol=(140, 80, 10)), W / 2, 330, appear(t, t0, 0.5))
        a = appear(t, t1, 0.5)
        rdot(cv, oy + RUL[0][0], 0.04 + 0.12 * eout((t - t1) / 1.0), '刘邦 · 低', a, t=t)
        a2 = appear(t, t1 + 3.0, 0.5)
        rdot(cv, oy + RUL[1][0], 0.04 + 0.46 * eout((t - t1 - 3.0) / 1.0), '刘邦 · 中', a2, t=t)
        return
    t0, t1, t2, t3, t4 = [Lt(L, k) for k in range(5)]
    put(cv, txt('两把尺子打分', 64, 'brush', GOLD2, glow=12, gcol=(140, 80, 10)), W / 2, 330, appear(t, 0, 0.5))
    a = appear(t, t1, 0.5)
    rdot(cv, oy + RUL[0][0], 0.16, '刘邦', a, RED2, False, t)
    rdot(cv, oy + RUL[1][0], 0.50, '刘邦', a, RED2, False, t)
    a = appear(t, t2, 0.5)
    rdot(cv, oy + RUL[0][0], 0.04 + 0.46 * eout((t - t2) / 1.0), '刘备', a, (255, 150, 110), False, t)
    rdot(cv, oy + RUL[1][0], 0.08, '刘备', appear(t, t2 + 3.5, 0.5), (255, 150, 110), False, t)
    a = appear(t, t3, 0.5)
    if a > 0:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for y in (oy + RUL[0][0], oy + RUL[1][0]):
            d.rectangle((RX0 - 10, y - 140, RX0 + 60, y + 150), fill=(120, 120, 120, int(60 * a)))
            d.rectangle((RX1 - 60, y - 140, RX1 + 10, y + 150), fill=(200, 170, 60, int(60 * a)))
        cv.alpha_composite(ov)
        put(cv, txt('纯草根', 34, 'sans', GREY, 2), RX0 + 25, oy + RUL[1][0] + 235, a)
        put(cv, txt('豪门', 34, 'sans', GOLD, 2), RX1 - 25, oy + RUL[1][0] + 235, a)
        put(cv, txt('都不在两端', 64, 'black', WHITE, 3), W / 2, 450, a * (1 - appear(t, t4, 0.3)))
    a = appear(t, t4, 0.5)
    if a > 0:
        put(cv, txt('边角料，打成王炸', 90, 'brush', RED2, glow=24, gcol=(220, 60, 10)), W / 2, 460, a, scale=1.2 - 0.2 * eout((t - t4) / 0.4))


# ════════════ 章节标题 ════════════
def title(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(6, (30, 20, 16), (90, 40, 20)))
    embers(C, n=90, seed=12, vel=((-20, 20), (-120, -40))).draw(cv, t, 0.9)
    a = appear(t, 0.05, 0.5)
    put(cv, txt(P['num'], 520, 'brush', (90, 30, 20), glow=30, gcol=(120, 30, 10)), W / 2, 820, a * 0.6, scale=1.25 - 0.25 * eout(t / 1.2))
    # 墨痕
    if 'stroke' not in C:
        s = Image.new('RGBA', (1000, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
        r = random.Random(2)
        for k in range(160):
            x = 40 + k * 5.8; w = max(3, 60 * math.sin(math.pi * k / 160) + r.uniform(-6, 6))
            d.ellipse((x - 8, 100 - w / 2, x + 8, 100 + w / 2), fill=(150, 26, 18, 230))
        C['stroke'] = s.filter(ImageFilter.GaussianBlur(1.5))
    p = eout((t - 0.2) / 0.6)
    if p > 0:
        sw = C['stroke'].crop((0, 0, max(1, int(1000 * p)), 200))
        put(cv, sw, 40, 900, 1.0, 'lm')
    put(cv, txt(P['title'], 120, 'brush', (255, 236, 205), glow=18, gcol=(0, 0, 0)), W / 2, 900, appear(t, 0.3, 0.5), scale=1.08 - 0.08 * eout((t - 0.3) / 0.6))
    put(cv, txt(P['sub'], 40, 'serifsc', GOLD, 2), W / 2, 1050, appear(t, 0.6, 0.5))


# ════════════ 家乡 ════════════
def home(cv, t, T, L, P, C):
    if 'bg' not in C:
        w, h = int(W * 1.08), int(H * 1.08)
        arr = grad_bg((20, 22, 30), (22, 18, 12), w, h, mid=(120, 86, 52), midpos=0.47)
        n = fnoise(w, h, 51, 5, 3); arr *= (0.8 + 0.35 * n[..., None])
        im = to_img(arr); d = ImageDraw.Draw(im)
        hy = h * 0.5
        d.rectangle((0, hy, w, h), fill=(30, 26, 16, 255))
        for k in range(26):  # 田垄
            f = (k / 26) ** 1.8; y = hy + (h - hy) * f
            d.line((0, y, w, y), fill=(56, 48, 26, 255), width=1 + int(5 * f))
        for k in range(-10, 11):
            d.line((w / 2 + k * 18, hy, w / 2 + k * 260, h), fill=(36, 31, 19, 255), width=1)
        col = (12, 10, 10, 255)
        house(d, w * 0.66, hy + 10, 1.5, col); house(d, w * 0.80, hy + 6, 1.0, col); house(d, w * 0.30, hy + 4, 0.8, col)
        for k, x in enumerate([0.1, 0.18, 0.46, 0.9, 0.97]): tree_sil(d, w * x, hy + 8, 1.2 + 0.2 * (k % 2), col, k)
        C['bg'] = im.filter(ImageFilter.GaussianBlur(0.8))
    zoom_bg(cv, C['bg'], t, T, 1.0, 1.06, 0.5, 0.5)
    embers(C, 'f', 30, 6, ((255, 220, 160),), (0, 900, W, 1300), ((-8, 8), (-12, -4)), (1, 2.2)).draw(cv, t, 0.6)
    t0, t1, t2, t3, t4 = [Lt(L, k) for k in range(5)]
    card_in(cv, qcard('高祖，沛豐邑中陽里人，姓劉氏，字季。', '《史記·高祖本紀》', '刘邦是沛县丰邑中阳里人，姓刘，字季。', 940, 52), t, 0.1, t1 - 0.1)
    put(cv, txt('沛 · 丰邑 · 中阳里', 52, 'black', GOLD2, 3), W / 2, 1040, appear(t, 0.8, 0.5) * (1 - appear(t, t1 - 0.2, 0.3)))
    a = window(t, t1, t2, 0.4, 0.3)
    if a > 0:
        for k, c in enumerate('伯仲叔季'):
            hi = c == '季'
            put(cv, txt(c, 150 if hi else 110, 'serifsc', RED2 if hi else GREY, 3, glow=18 if hi else 0, gcol=(200, 40, 10)), 210 + k * 220, 400, a)
        put(cv, txt('排行最末 · 老幺', 48, 'sans', WHITE, 2), W / 2, 560, a)
    a = window(t, t2, t3, 0.4, 0.3)
    if a > 0:
        put(cv, tag('家中', GOLD, 32), W / 2, 250, a)
        put(cv, txt('太公 ─ 二哥刘仲：能治产业', 54, 'black', WHITE, 3), W / 2, 350, a)
        put(cv, txt('刘季：「不能治產業，不如仲力」', 46, 'serif', GOLD2, 3), W / 2, 450, a)
    card_in(cv, qcard('常有大度，不事家人生產作業。', '《史記·高祖本紀》', '他心胸大，但不干家里的营生。', 940, 56), t, t3)
    a = appear(t, t4, 0.5)
    if a > 0:
        put(cv, tag('有地的农户 · 不是赤贫', RED2, 44, 60), W / 2, 1080, a)


# ════════════ 亭的体系 ════════════
def ting_system(cv, t, T, L, P, C):
    if 'bg' not in C:
        n = map_tex(); im = to_img(n * 0.8)
        C['bg'] = im
        r = np.random.RandomState(3)
        pts = []
        for i in range(14):
            for j in range(16):
                x = 80 + i * 70 + r.uniform(-14, 14); y = 560 + j * 52 + r.uniform(-10, 10)
                pts.append((x, y, math.hypot(x - 540, y - 960)))
        pts.sort(key=lambda p: p[2]); C['pts'] = pts
    cv.alpha_composite(C['bg'])
    t0, t1, t2, t3, t4, t5 = [Lt(L, k) for k in range(6)]
    card_in(cv, qcard('試為吏，為泗水亭長。', '《史記·高祖本紀》', '他试着当了吏，做了泗水亭长。', 900, 60), t, 0.05, t2 - 0.1)
    # 亭网扩散
    if t > t1 - 0.3:
        prog = appear(t, t1 - 0.3, max(1.0, t3 + 2 - t1))
        nshow = int(len(C['pts']) * prog)
        d = ImageDraw.Draw(cv)
        for i, (x, y, _) in enumerate(C['pts'][:nshow]):
            if i < nshow - 1 and i > 0:
                pass
            d.polygon([(x - 9, y + 6), (x, y - 8), (x + 9, y + 6)], fill=GOLD + (220,))
            d.rectangle((x - 5, y + 6, x + 5, y + 14), fill=GOLD + (200,))
        a = window(t, t1, t4, 0.4, 0.4)
        put(cv, tag('治安 · 捉盗贼 · 驿传 · 接待公差', GOLD, 36, 60), W / 2, 1420 - 120, a * (1 - appear(t, t2 - 0.2, 0.3)))
        put(cv, txt('十里一亭', 90, 'brush', GOLD2, glow=14, gcol=(0, 0, 0)), W / 2, 960, window(t, t2, t3 + 0.2) * 0.95)
    card_in(cv, qcard('大率十里一亭，亭有長。', '《漢書·百官公卿表》', '大约十里设一亭，亭有亭长。', 900, 60), t, t2, t4 - 0.1)
    a = window(t, t3, t4 + 0.1, 0.3, 0.3)
    if a > 0:
        n = int(29635 * eout((t - t3) / 2.0))
        put(cv, txt(f'{n:,}', 150, 'black', WHITE, 4, (60, 30, 0), glow=20, gcol=(200, 140, 40)), W / 2, 1180, a)
        put(cv, txt('个亭 ·《汉书》所载', 44, 'sans', GOLD, 2), W / 2, 1290, a)
    # 层级阶梯
    a = appear(t, t4, 0.5)
    if a > 0:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, int(170 * a))); cv.alpha_composite(ov)
        levels = [('郡', '郡守 · 二千石'), ('县', '县令 · 千石至三百石'), ('乡', '有秩 · 三老'), ('亭', '亭长 · 少吏')]
        for k, (lv, s) in enumerate(levels):
            aa = appear(t, t4 + 0.25 * k, 0.4)
            y = 640 + k * 170
            w = 720 - k * 110
            hi = lv == '亭'
            put(cv, rrect((w, 130), 10, (RED + (200,)) if hi else (40, 34, 28, 220), GOLD2 + (255,) if hi else GOLD + (160,), 3), W / 2, y, aa)
            put(cv, txt(lv, 70, 'serifsc', WHITE if hi else GOLD2), W / 2 - w / 2 + 70, y, aa)
            put(cv, txt(s, 40, 'sans', WHITE if hi else GREY), W / 2 + 40, y, aa)
        card_in(cv, qcard('百石以下有斗食、佐史之秩，……是爲少吏。', '《漢書·百官公卿表》', '一百石以下的，叫少吏。', 940, 50), t, t4 + 0.4)
        a5 = appear(t, t5, 0.5)
        if a5 > 0:
            put(cv, tag('正式的吏 ≠ 村长', GOLD2, 44, 60), 300, 1330, a5)
            put(cv, tag('级别很低 ≠ 高官', QIN2, 44, 60), 790, 1330, appear(t, t5 + 1.6, 0.5))


# ════════════ 现代类比 ════════════
def analogy(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(7, (16, 22, 26), (30, 40, 50)))
    d = ImageDraw.Draw(cv)
    for k in range(12):  # 淡网格，区别于史料卡
        d.line((0, 400 + k * 90, W, 400 + k * 90), fill=(80, 110, 130, 18), width=1)
    put(cv, tag('现代类比', (150, 200, 230), 40, 40), W / 2, 260, appear(t, 0, 0.4))
    tb = Lt(L, P.get('body_line', 1)); y = 360
    for k, s in enumerate(P['body']):
        im = block(s, 56, 'black', WHITE, 960, 1.35)
        put(cv, im, W / 2, y, appear(t, tb + 0.6 * k, 0.4), 'mt'); y += im.height + 22
    bl = P['bias_line']; tbias = Lt(L, bl)
    a = appear(t, tbias, 0.4)
    if a > 0:
        y0 = y + 50
        items = [block('①②③④'[k] + ' ' + s, 40, 'sans', (250, 225, 215), 860, 1.35, 'l') for k, s in enumerate(P['bias'])]
        hh = 110 + sum(im.height + 26 for im in items)
        put(cv, rrect((960, hh), 6, (40, 14, 12, 220), (230, 120, 90, 255), 3), W / 2, y0 + hh / 2, a)
        put(cv, tag('类比偏差', (240, 140, 110), 38, 60), W / 2, y0 + 50, a)
        yy = y0 + 100
        nrest = len(L) - bl
        for k, im in enumerate(items):
            tk = Lt(L, bl + k) if nrest >= len(items) else tbias + 1.6 * k
            put(cv, im, 90, yy, appear(t, tk, 0.4), 'lt'); yy += im.height + 26


# ════════════ 关系网 ════════════
NODES = {
    'xiao': (230, 800, '萧何', '主吏掾 · 县吏', GOLD2),
    'cao': (850, 800, '曹参', '狱掾 · 县吏', GOLD2),
    'fan': (230, 1220, '樊哙', '屠狗 · 市井', ORANGE),
    'lv': (850, 1220, '吕公', '县令之友 · 士绅', PAPER),
    'zhang': (880, 590, '张耳', '魏地豪杰 · 游侠', (200, 160, 230)),
}


def node(cv, x, y, name, role, col, a, big=False, t=0):
    r = 92 if big else 72
    put(cv, dot_sprite(r * 0.9, col, 0.0), x, y, a * 0.5)
    ov = Image.new('RGBA', (2 * r + 10, 2 * r + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.ellipse((5, 5, 2 * r + 5, 2 * r + 5), fill=(16, 12, 10, 240), outline=col + (255,), width=5)
    put(cv, ov, x, y, a)
    put(cv, txt(name, 54 if big else 46, 'black', col), x, y - 2, a)
    put(cv, txt(role, 30, 'sans', WHITE, 2), x, y + r + 28, a)


def network(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(8))
    embers(C, n=40).draw(cv, t, 0.5)
    tl = [Lt(L, k) for k in range(12)]
    cx, cy = 540, 1010
    # 沛县圈
    a = appear(t, 0, 0.6)
    ring(cv, cx, cy, 410, (120, 90, 60), a * 0.5, 3)
    put(cv, txt('沛县', 40, 'serifsc', (160, 130, 90)), cx - 290, cy - 330, a)
    appear_t = {'xiao': tl[1], 'cao': tl[6], 'fan': tl[8], 'lv': tl[9], 'zhang': tl[10]}
    d = ImageDraw.Draw(cv)
    for k, (x, y, *_r) in NODES.items():
        aa = appear(t, appear_t[k], 0.5)
        if aa > 0:
            p = eout((t - appear_t[k]) / 0.6)
            ex, ey = cx + (x - cx) * p, cy + (y - cy) * p
            d.line((cx, cy, ex, ey), fill=GOLD + (int(170 * aa),), width=4)
    for k, (x, y, n, role, col) in NODES.items():
        aa = appear(t, appear_t[k], 0.5)
        if aa > 0: node(cv, x, y, n, role, col, aa)
    node(cv, cx, cy, '刘邦', '泗水亭长', RED2, appear(t, 0, 0.5), True)
    # 萧何的上行线：郡、朝廷
    a = window(t, tl[4], tl[6], 0.4, 0.4)
    if a > 0:
        put(cv, tag('泗水郡 · 卒史事 · 考核第一', GOLD2, 34, 70), 330, 560, a)
        put(cv, tag('秦御史欲征 → 固辞', QIN2, 34, 70), 330, 640, appear(t, tl[5] + 1.5, 0.4) * a)
    # 古文卡（底部区域：1280 上方不挡节点则放顶部）
    cards = [
        (tl[1], tl[2], ('以文無害為沛主吏掾。', '《史記·蕭相國世家》', '萧何精通律令文书，任沛县主吏掾。')),
        (tl[2], tl[3], ('數以吏事護高祖。', '《史記·蕭相國世家》', '多次在公事上回护刘邦。')),
        (tl[3], tl[4], ('高祖以吏繇咸陽，吏皆送奉錢三，何獨以五。', '《史記·蕭相國世家》', '同僚都凑了份子，萧何多送了一份。')),
        (tl[5], tl[6], ('何乃給泗水卒史事，第一。', '《史記·蕭相國世家》', '萧何兼办泗水郡卒史事务，考核第一。')),
        (tl[6], tl[8], ('秦時為沛獄掾，而蕭何為主吏，居縣為豪吏矣。', '《史記·曹相國世家》', '曹参是狱掾，萧何是主吏，两人都是县里的豪吏。')),
        (tl[8], tl[9], ('以屠狗為事，與高祖俱隱。', '《史記·樊酈滕灌列傳》', '樊哙以杀狗卖肉为业，曾和刘邦一起躲藏。')),
        (tl[9], tl[10], ('單父人呂公善沛令。', '《史記·高祖本紀》', '吕公是沛县县令的好友。')),
        (tl[10], tl[11], ('高祖為布衣時，嘗數從張耳游，客數月。', '《史記·張耳陳餘列傳》', '刘邦还是平民时，多次跟张耳交游，做过几个月门客。')),
    ]
    for t0, t1, (q, s, b) in cards:
        card_in(cv, qcard(q, s, b, 960, 44), t, t0 + 0.3, t1, y=300)
    a = appear(t, tl[11], 0.5)
    if a > 0:
        d = ImageDraw.Draw(cv)
        put(cv, txt('人脉早就出了沛县', 84, 'brush', (220, 190, 245), glow=14, gcol=(0, 0, 0)), W / 2, 320, a)


# ════════════ 神话叙事 ════════════
def myth(cv, t, T, L, P, C):
    if 'bg' not in C:
        n = fnoise(W, H, 61, 6, 3); n2 = fnoise(W, H, 62, 4, 2)
        arr = np.stack([10 + 40 * n * n2, 12 + 44 * n * n2, 18 + 52 * n * n2], -1)
        C['bg'] = to_img(arr); C['n'] = n
    cv.alpha_composite(C['bg'])
    tl = [Lt(L, k) for k in range(6)]
    # 闪电
    flash = 0
    for tk in (tl[1] + 0.2, tl[1] + 1.6, tl[1] + 3.4):
        u = t - tk
        if 0 < u < 0.35:
            flash = max(flash, 1 - u / 0.35)
            r = random.Random(int(tk * 10)); x = r.uniform(250, 850); y = 420
            pts = [(x, y)]
            while y < 1100:
                y += r.uniform(40, 90); x += r.uniform(-70, 70); pts.append((x, y))
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            d.line(pts, fill=(230, 235, 255, int(255 * (1 - u / 0.35))), width=6)
            cv.alpha_composite(ov.filter(ImageFilter.GaussianBlur(6))); cv.alpha_composite(ov)
    if flash > 0:
        cv.alpha_composite(Image.new('RGBA', (W, H), (200, 210, 255, int(70 * flash))))
    # 水墨蛟龙：行波游动，头在右，墨身金边
    a = appear(t, tl[1], 0.8) * (1 - appear(t, tl[4], 0.6) * 0.65)
    if a > 0:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        N = 90; pts = []
        for i in range(N):
            f = i / (N - 1)
            x = 960 - f * 1150
            y = 800 + 150 * math.sin(f * 6.0 - t * 2.2) * (0.3 + 0.7 * f) + 30 * math.sin(f * 15 - t * 3)
            pts.append((x, y, f))
        for k in range(N - 1, -1, -1):
            x, y, f = pts[k]
            r = 44 * (1 - f) ** 0.7 + 6
            d.ellipse((x - r, y - r, x + r, y + r), fill=(6, 6, 8, 245))
            if k % 4 == 0 and 0.05 < f < 0.92 and k + 1 < N:
                x2, y2, _ = pts[k + 1]; dx, dy = x2 - x, y2 - y; L_ = math.hypot(dx, dy) + 1e-6
                nx, ny = -dy / L_, dx / L_
                if ny > 0: nx, ny = -nx, -ny
                d.polygon([(x + nx * r * 0.8, y + ny * r * 0.8), (x + nx * (r + 34) + dx * 0.8, y + ny * (r + 34) + dy * 0.8), (x + dx * 1.6, y + dy * 1.6)], fill=(6, 6, 8, 245))
        hx, hy, _ = pts[0]
        d.ellipse((hx - 30, hy - 40, hx + 90, hy + 26), fill=(6, 6, 8, 250))          # 头
        d.polygon([(hx + 60, hy - 20), (hx + 140, hy - 4), (hx + 70, hy + 22)], fill=(6, 6, 8, 250))  # 吻
        d.line((hx + 10, hy - 36, hx - 40, hy - 110, hx - 70, hy - 120), fill=(6, 6, 8, 250), width=9)   # 角
        d.line((hx + 30, hy - 36, hx + 0, hy - 100, hx - 20, hy - 116), fill=(6, 6, 8, 250), width=7)
        for s_ in (-1, 1):  # 须
            d.line([(hx + 120, hy + 4), (hx + 190, hy + 30 * s_ + 10 * math.sin(t * 3)), (hx + 260, hy + 70 * s_)], fill=(6, 6, 8, 230), width=4, joint='curve')
        d.ellipse((hx + 40, hy - 20, hx + 56, hy - 6), fill=(255, 200, 90, 255))   # 眼
        bb = ov.getbbox()
        if bb:
            crop = ov.crop(bb).filter(ImageFilter.GaussianBlur(1.6))
            g = glowify(crop, 9, (235, 175, 80), 1.1)
            pad = (g.width - crop.width) // 2
            put(cv, g, bb[0] - pad, bb[1] - pad, a, 'lt')
        # 云气
        for k in range(7):
            cx = (k * 170 + t * 25) % 1300 - 100; cy = 560 + (k % 3) * 160
            put(cv, dot_sprite(60, (120, 130, 150), 0.0), cx, cy, 0.25 * a)
    put(cv, tag('史书所载神话叙事', (230, 170, 110), 34, 60), W - 30, 200, appear(t, 0, 0.4), 'rm')
    put(cv, txt('天命叙事', 110, 'brush', GOLD2, glow=16, gcol=(0, 0, 0)), W / 2, 320, window(t, 0, tl[1] + 0.2))
    items = [(tl[1], '夢與神遇 · 蛟龍於其上'), (tl[2], '隆準而龍顏 · 左股有七十二黑子'), (tl[3], '呂公相面 · 醉斬白蛇')]
    for k, (tk, s) in enumerate(items):
        aa = appear(t, tk, 0.5) * (1 - appear(t, tl[4] - 0.2, 0.4) * 0.6)
        put(cv, txt(s, 52, 'serif', (250, 230, 190), 3, glow=10, gcol=(0, 0, 0)), W / 2, 1110 + k * 84, aa)
    a = appear(t, tl[4], 0.5)
    if a > 0:
        put(cv, tag('司马迁照录的汉代叙事 · 不当史实讲', (230, 170, 110), 40, 60), W / 2, 330, a)
    a = appear(t, tl[5], 0.5)
    if a > 0:
        cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(120 * a))))
        put(cv, txt('越缺门第', 120, 'brush', GREY, glow=12, gcol=(0, 0, 0)), W / 2, 760, a)
        put(cv, txt('越需要天命补位', 120, 'brush', RED2, glow=20, gcol=(200, 40, 10)), W / 2, 930, appear(t, tl[5] + 1.0, 0.5))


# ════════════ 追补谱系 ════════════
def pedigree(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(9))
    tl = [Lt(L, k) for k in range(5)]
    card_in(cv, qcard('漢帝本系，出自唐帝。', '《漢書·高帝紀》贊', '汉朝皇帝的祖先，出自帝尧。', 900, 60), t, tl[1], tl[3])
    put(cv, txt('东汉 班固', 70, 'brush', GOLD2, glow=12, gcol=(0, 0, 0)), W / 2, 330, window(t, 0, tl[1]))
    chain = ['帝尧', '刘累', '范氏', '……', '丰公', '太公', '刘邦']
    a0 = appear(t, tl[2], 0.3)
    if a0 > 0:
        d = ImageDraw.Draw(cv)
        y0 = 580
        for k, s in enumerate(chain):
            tk = tl[2] + 0.45 * k
            aa = appear(t, tk, 0.4)
            y = y0 + k * 120
            if k > 0 and aa > 0:
                for yy in range(int(y - 92), int(y - 30), 14):  # 虚线
                    d.line((W / 2, yy, W / 2, yy + 7), fill=GOLD + (int(220 * aa),), width=4)
            col = RED2 if s == '刘邦' else GOLD2
            put(cv, txt(s, 64 if s != '……' else 50, 'serifsc', col, 3, glow=8, gcol=(0, 0, 0)), W / 2, y - 60 + 60, aa)
    a = appear(t, tl[3], 0.5)
    if a > 0:
        put(cv, tag('东汉人追补的谱系', (240, 140, 110), 44, 70), W / 2, 330, a)
    a = appear(t, tl[4], 0.5)
    if a > 0:
        cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(150 * a))))
        d = ImageDraw.Draw(cv)
        y = 1300; x0, x1 = 150, 930
        p = eout((t - tl[4]) / 1.2)
        d.line((x0, y, x0 + (x1 - x0) * p, y), fill=GOLD + (255,), width=6)
        put(cv, txt('刘邦去世', 40, 'black', RED2, 2), x0, y - 60, a)
        put(cv, txt('前195年', 32, 'sans', GREY), x0, y + 46, a)
        put(cv, txt('《汉书》成书', 40, 'black', GOLD2, 2), x1, y - 60, appear(t, tl[4] + 1.2, 0.4))
        put(cv, txt('东汉 · 一世纪', 32, 'sans', GREY), x1, y + 46, appear(t, tl[4] + 1.2, 0.4))
        put(cv, txt('两百多年后补的家谱', 64, 'brush', WHITE, glow=10, gcol=(0, 0, 0)), W / 2, 1140, appear(t, tl[4] + 1.6, 0.4))


# ════════════ 秦末大图 ════════════
P_BIG = Proj(106.0, 123.0, 34.6)
P_SISHUI = Proj(114.6, 119.0, 34.45)


def map_common(cv, C):
    if 'tex' not in C: C['tex'] = to_img(map_tex())
    cv.alpha_composite(C['tex'])


def map_qin(cv, t, T, L, P, C):
    map_common(cv, C)
    tl = [Lt(L, k) for k in range(6)]
    z = ease((t - tl[3] + 1.0) / 2.5)
    Pj = P_BIG.lerp(P_SISHUI, z)
    draw_map(cv, Pj)
    put(cv, tag('示意', GREY, 26, 30), 60, 1360, 1, 'lm')
    put(cv, txt('秦二世元年 前209年', 52, 'brush', GOLD2, glow=10, gcol=(0, 0, 0)), W / 2, 300, 1)
    # 咸阳
    city(cv, Pj, '咸阳', QIN, 1 - z, 14, 44, sub='秦都')
    # 大泽乡涟漪
    if t > tl[0] - 0.2:
        x, y = Pj(*PLACE['大泽乡'])
        for k in range(4):
            u = ((t - tl[0]) * 0.55 - k * 0.25)
            if u > 0:
                uu = u % 1.0
                ring(cv, x, y, 40 + 600 * uu * (1 - 0.6 * z), ORANGE, (1 - uu) * 0.9 * (1 - 0.75 * z), 6)
        city(cv, Pj, '大泽乡', ORANGE, appear(t, tl[0], 0.4), 13, 44, dx=110, dy=20, sub='陈胜吴广起事')
    # 陈：张楚
    if t > tl[1] - 0.2:
        a = appear(t, tl[1], 0.4) * (1 - z)
        x0, y0 = Pj(*PLACE['大泽乡']); x1, y1 = Pj(*PLACE['陈'])
        draw_arrow(cv, bez((x0, y0), ((x0 + x1) / 2, y0 + 60), (x1, y1)), eout((t - tl[1]) / 1.2), ORANGE, a * (1 - z), 34, 20, 60, 80)
        city(cv, Pj, '陈', ORANGE, a, 12, 44, dy=-50, sub='张楚')
    # 郡县响应：橙点
    if t > tl[2] - 0.2:
        r = random.Random(7)
        for k in range(28):
            lon = r.uniform(112, 120); lat = r.uniform(31.5, 37)
            tk = tl[2] + r.uniform(0, 2.5)
            aa = appear(t, tk, 0.3) * (1 - z * 0.7)
            if aa > 0:
                x, y = Pj(lon, lat); put(cv, dot_sprite(8, ORANGE, 0.8), x, y, aa)
        put(cv, tag('诸郡县皆多杀其长吏以应陈涉', ORANGE, 34, 60), W / 2, 420, window(t, tl[2], tl[3] - 0.3))
    # 泗水郡近景
    if z > 0:
        put(cv, txt('泗水郡（示意）', 40, 'serifsc', GREY, 2), *Pj(115.3, 35.05), a=z)
        city(cv, Pj, '沛', RED2, z, 16, 58, dx=0, dy=-60, pulse=1, t=t, sub='县令犹豫')
        city(cv, Pj, '丰', RED, z, 11, 44, dx=-60, dy=-30)
        city(cv, Pj, '相', GREY, z * 0.8, 9, 36, dx=50, dy=-30)
        city(cv, Pj, '彭城', GREY, z * 0.8, 9, 36, dx=60, dy=30)
        card_in(cv, qcard('君為秦吏，今欲背之，率沛子弟，恐不聽。願君召諸亡在外者……', '《史記·高祖本紀》', '萧何、曹参：您是秦吏，号召不动人；不如召回逃亡在外的人。', 960, 46), t, tl[2] + 0.4, tl[4] - 0.2, y=470)
    if t > tl[4] - 0.2:
        a = appear(t, tl[4], 0.5)
        x, y = Pj(*PLACE['芒砀山'])
        d = ImageDraw.Draw(cv)
        for k in range(5):  # 山形
            xx = x - 120 + k * 55; hh = 60 + 30 * (k % 2)
            d.polygon([(xx - 50, y + 30), (xx, y + 30 - hh), (xx + 50, y + 30)], fill=(60, 54, 44, int(220 * a)), outline=(120, 110, 90, int(200 * a)))
        if 'band' not in C: C['band'] = Field(60, 33, (0, 0, 140, 90), ((-6, 6), (-6, 6)), (2, 4), (RED2, RED), True)
        fx, fy = x - 70, y - 40
        f = C['band']
        xs = fx + (f.p[:, 0] * 140 + 6 * np.sin(t * 2 + f.ph)); ys = fy + (f.p[:, 1] * 90 + 6 * np.cos(t * 2 + f.ph))
        for i in range(f.n):
            put(cv, dot_sprite(f.s[i], RED2), xs[i], ys[i], a)
        put(cv, txt('芒砀山', 46, 'black', RED2, 3), x, y + 90, a)
        put(cv, tag('刘季之众已数十百人', RED2, 34, 60), x + 40, y + 160, a)


# ════════════ 夜城：帛书射城 ════════════
def night_city(cv, t, T, L, P, C):
    if 'bg' not in C:
        w, h = W, H
        arr = grad_bg((4, 6, 14), (20, 10, 8), w, h, mid=(26, 24, 40), midpos=0.5)
        n = fnoise(w, h, 71, 5, 3); arr *= (0.75 + 0.45 * n[..., None])
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        moon = np.exp(-(((x - 230) / 50) ** 2 + ((y - 520) / 50) ** 2))
        arr += moon[..., None] * np.array([230, 220, 190])
        C['bg'] = to_img(arr)
        wall = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(wall)
        wy = 890
        d.rectangle((0, wy, W, 1330), fill=(10, 9, 10, 255))
        for k in range(0, W, 46): d.rectangle((k, wy - 30, k + 26, wy), fill=(10, 9, 10, 255))
        for x in (300, 780):  # 城楼
            d.rectangle((x - 90, wy - 120, x + 90, wy), fill=(8, 7, 8, 255))
            d.polygon([(x - 150, wy - 110), (x - 80, wy - 180), (x + 80, wy - 180), (x + 150, wy - 110)], fill=(8, 7, 8, 255))
            d.rectangle((x - 50, wy - 250, x + 50, wy - 180), fill=(8, 7, 8, 255))
            d.polygon([(x - 100, wy - 245), (x - 40, wy - 300), (x + 40, wy - 300), (x + 100, wy - 245)], fill=(8, 7, 8, 255))
        d.text((540, 1000), '沛', font=font('serifsc', 70), fill=(70, 60, 50, 255), anchor='mm')
        C['wall'] = wall
        C['fire'] = Field(90, 77, (0, 720, W, 930), ((-8, 8), (-80, -30)), (1.5, 4), (ORANGE, (255, 210, 120), RED2), True)
    cv.alpha_composite(C['bg'])
    tl = [Lt(L, k) for k in range(4)]
    # 城内火光（父老起事后增强）
    fire = 0.25 + 0.75 * appear(t, tl[3], 1.0)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(glow)
    d.ellipse((140, 610, 940, 1030), fill=(255, 110, 30, int(90 * fire)))
    cv.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
    C['fire'].draw(cv, t, fire)
    cv.alpha_composite(C['wall'])
    # 城门
    gw = 150; open_ = appear(t, tl[3] + 1.0, 1.2)
    closed = appear(t, tl[1], 0.6)
    d = ImageDraw.Draw(cv)
    gx = 540
    d.rectangle((gx - gw / 2 - 10, 1080, gx + gw / 2 + 10, 1330), fill=(4, 4, 4, 255))
    if open_ > 0:
        d.rectangle((gx - gw / 2 * open_, 1090, gx + gw / 2 * open_, 1330), fill=(255, 140, 60, int(255 * open_)))
    lw = gw / 2 * (1 - open_)
    d.rectangle((gx - gw / 2, 1090, gx - gw / 2 + lw, 1330), fill=(40, 26, 18, 255))
    d.rectangle((gx + gw / 2 - lw, 1090, gx + gw / 2, 1330), fill=(40, 26, 18, 255))
    # 城外刘邦众
    if 'band' not in C: C['band'] = Field(80, 55, (0, 0, 380, 120), ((-6, 6), (-3, 3)), (2, 4.5), (RED2, RED), True)
    f = C['band']
    k = appear(t, tl[3] + 1.6, 2.0)
    xs = 40 + f.p[:, 0] * 380 + k * 330; ys = 1340 + f.p[:, 1] * 80 - k * 20 + 4 * np.sin(t * 3 + f.ph)
    for i in range(f.n): put(cv, dot_sprite(f.s[i], RED2), xs[i], ys[i], 1 - 0.0 * k)
    put(cv, txt('刘季', 48, 'black', RED2, 3), 230 + k * 330, 1310 - k * 20, 1)
    if closed > 0 and t < tl[3]:
        put(cv, tag('闭城城守', QIN2, 40, 70), 540, 1040, closed * (1 - appear(t, tl[2], 0.3)))
    # 萧曹踰城
    a = window(t, tl[1] + 1.5, tl[2] + 0.5)
    if a > 0:
        u = eout((t - tl[1] - 1.5) / 1.5)
        for k2 in range(2):
            x = 880 - u * 140 + k2 * 30; y = 880 + u * 480 - 260 * math.sin(math.pi * u)
            put(cv, dot_sprite(6, GOLD2), x, y, a)
        put(cv, txt('萧、曹踰城', 40, 'black', GOLD2, 3), 860, 800, a)
    # 帛书箭
    if tl[2] - 0.1 < t:
        u = eout((t - tl[2] - 0.2) / 1.1)
        if u > 0:
            pts = bez((200, 1380), (420, 560), (720, 960), 60)
            pp = partial(pts, u)
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
            dd.line([tuple(p) for p in pp[-25:]], fill=(255, 240, 210, 150), width=4)
            hx, hy = pp[-1]
            dd.ellipse((hx - 10, hy - 10, hx + 10, hy + 10), fill=(255, 250, 230, 255))
            dd.rectangle((hx - 26, hy + 6, hx + 2, hy + 36), fill=(245, 240, 225, 240))
            cv.alpha_composite(ov.filter(ImageFilter.GaussianBlur(4))); cv.alpha_composite(ov)
        card_in(cv, qcard('劉季乃書帛射城上，謂沛父老曰：「天下苦秦久矣。……」', '《史記·高祖本紀》', '刘季把信写在帛上射进城：天下被秦朝折磨太久了。', 960, 48), t, tl[2] + 0.6, tl[3] + 0.2)
    a = appear(t, tl[3], 0.5)
    if a > 0:
        card_in(cv, qcard('父老乃率子弟共殺沛令，開城門迎劉季，欲以為沛令。', '《史記·高祖本紀》', '父老带子弟杀了县令，开门迎刘季，要立他做沛令。', 960, 48), t, tl[3] + 0.2)
    put(cv, tag('情景示意', GREY, 24, 30), W - 30, 1400, 1, 'rm')


# ════════════ 大字古文 ════════════
def quote_big(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(10, (30, 22, 16), (80, 50, 20)))
    embers(C, n=70, seed=19).draw(cv, t, 0.7)
    a = appear(t, 0.1, 0.6)
    text = P['text']
    im = block(text, 82, 'serif', (250, 232, 190), 860, 1.55, 'c', glow=14, gcol=(140, 80, 10))
    put(cv, im, W / 2, 760, a, scale=1.04 - 0.04 * eout(t / 1.0))
    put(cv, txt('——' + P['src'], 40, 'serif', GOLD), W - 110, 760 + im.height / 2 + 60, appear(t, 0.5, 0.5), 'rm')
    put(cv, tag('史料原文', GOLD, 30, 50), W / 2, 330, a)
    if len(L) > 1:
        a = appear(t, L[1], 0.5)
        if a > 0:
            bai = {'rang': '萧何曹参都是文吏，爱惜身家，怕事不成被秦灭族，把头把交椅让给了刘季。',
                   'chenshou': '刘备坚毅宽厚，识人待士，有汉高祖的风度，是英雄的器量。'}.get(P.get('_id'), '')
            put(cv, block(bai, 44, 'sans', (225, 220, 210), 900, 1.45), W / 2, 1200, a)


# ════════════ 机制图 ════════════
def mechanism(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(11))
    tl = [Lt(L, k) for k in range(4)]
    put(cv, txt('第一责任人', 110, 'brush', GOLD2, glow=16, gcol=(0, 0, 0)), W / 2, 300, appear(t, 0, 0.5))
    # 左：萧曹
    a = appear(t, 0.3, 0.5)
    put(cv, rrect((440, 560), 10, (28, 26, 30, 220), QIN2 + (200,), 3), 270, 820, a)
    put(cv, txt('萧何 · 曹参', 54, 'black', GOLD2), 270, 600, a)
    put(cv, txt('体制内 · 能力最强', 34, 'sans', GREY), 270, 660, a)
    for k, s in enumerate(['有家', '有业', '有官身']):
        put(cv, tag(s, QIN2, 40, 60), 270, 760 + k * 100, appear(t, 0.6 + 0.3 * k, 0.4))
    put(cv, txt('牵挂最多', 44, 'black', QIN2), 270, 1060, appear(t, 1.6, 0.4))
    # 右：刘季
    put(cv, rrect((440, 560), 10, (40, 16, 12, 220), RED2 + (220,), 3), 810, 820, a)
    put(cv, txt('刘季', 54, 'black', RED2), 810, 600, a)
    put(cv, txt('亡命在外 · 网络最广', 34, 'sans', GREY), 810, 660, a)
    for k, s in enumerate(['县吏网络', '市井豪侠', '芒砀旧部']):
        put(cv, tag(s, RED2, 40, 60), 810, 760 + k * 100, appear(t, 0.9 + 0.3 * k, 0.4))
    put(cv, txt('牵挂最少', 44, 'black', RED2), 810, 1060, appear(t, 1.9, 0.4))
    # 交椅移动
    u = eout((t - tl[1]) / 1.3)
    x = 270 + 540 * u
    seat = C.get('seat')
    if seat is None:
        seat = Image.new('RGBA', (160, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(seat)
        d.rectangle((20, 0, 140, 20), fill=GOLD2 + (255,)); d.rectangle((30, 20, 46, 100), fill=GOLD + (255,)); d.rectangle((114, 20, 130, 100), fill=GOLD + (255,))
        d.rectangle((10, 96, 150, 116), fill=GOLD2 + (255,)); d.rectangle((20, 116, 36, 170), fill=GOLD + (255,)); d.rectangle((124, 116, 140, 170), fill=GOLD + (255,))
        seat = glowify(seat, 12, (255, 180, 60)); C['seat'] = seat
    put(cv, seat, x, 1250, appear(t, 0.2, 0.5))
    put(cv, txt('头把交椅', 40, 'black', GOLD2, 3), x, 1360, appear(t, 0.2, 0.5))
    # 连坐
    a = window(t, tl[2], 1e9, 0.4)
    if a > 0:
        cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(140 * a))))
        put(cv, txt('连坐', 150, 'brush', QIN2, glow=20, gcol=(40, 60, 90)), W / 2, 560, a)
        d = ImageDraw.Draw(cv)
        r = random.Random(1)
        cx, cy = 540, 900
        for k in range(18):
            ang = k / 18 * 6.283; rr = 150 + (k % 3) * 70
            x2, y2 = cx + rr * math.cos(ang), cy + rr * 0.7 * math.sin(ang)
            aa = appear(t, tl[2] + 0.4 + k * 0.08, 0.3)
            d.line((cx, cy, x2, y2), fill=QIN2 + (int(150 * aa),), width=3)
            put(cv, dot_sprite(10, QIN2), x2, y2, aa)
        put(cv, dot_sprite(18, WHITE), cx, cy, a)
        put(cv, tag('一人造反 · 全族搭进去', QIN2, 40, 70), W / 2, 1180, a)
    a = appear(t, tl[3], 0.5)
    if a > 0:
        put(cv, txt('输一次 = 灭门', 60, 'black', QIN2, 3), 300, 1300, a)
        put(cv, txt('没有退路 = 最敢往前站', 60, 'black', RED2, 3), 600, 1300 + 90, appear(t, tl[3] + 2.6, 0.5))


# ════════════ 起兵推演 ════════════
P_PEI = Proj(115.85, 117.75, 34.8, (0, 420, W, 1380))


def map_advance(cv, t, T, L, P, C):
    map_common(cv, C)
    Pj = P_PEI
    draw_map(cv, Pj, rivers=('si',))
    tl = [Lt(L, k) for k in range(3)]
    put(cv, tag('示意', GREY, 26, 30), 60, 1360, 1, 'lm')
    put(cv, txt('沛公起兵', 100, 'brush', RED2, glow=20, gcol=(200, 30, 10)), W / 2, 300, 1)
    x, y = city(cv, Pj, '沛', RED2, 1, 20, 64, dx=70, dy=-50, pulse=1.0, t=t, sub='沛公 · 旗帜皆赤')
    city(cv, Pj, '丰', RED, 1, 13, 48, dx=-80, dy=0)
    city(cv, Pj, '胡陵', QIN, 1, 12, 46, dy=-50)
    city(cv, Pj, '方与', QIN, 1, 12, 46, dy=-50)
    # 子弟汇聚
    if 'army' not in C: C['army'] = Field(220, 91, (0, 0, 1, 1), ((0, 0), (0, 0)), (1.5, 3.5), (RED2, RED, (255, 140, 100)), True)
    f = C['army']
    gather = appear(t, tl[1], 2.5)
    n = int(f.n * (0.2 + 0.8 * gather))
    ang = f.p[:, 0] * 6.283; rad = 30 + 110 * np.sqrt(f.p[:, 1])
    sx = x + np.cos(ang) * (rad + 500 * (1 - gather)); sy = y + np.sin(ang) * (rad * 0.7 + 400 * (1 - gather))
    # 出击：沿箭头方向位移
    mv = appear(t, tl[2], 2.0)
    hx, hy = Pj(*PLACE['胡陵'])
    sx = sx + (hx - x) * 0.55 * mv * (1 - appear(t, tl[2] + 3.4, 1.5)); sy = sy + (hy - y) * 0.55 * mv * (1 - appear(t, tl[2] + 3.4, 1.5))
    for i in range(n): put(cv, dot_sprite(f.s[i], f.cols[f.c[i]]), sx[i], sy[i], 0.95)
    a = appear(t, tl[1], 0.5)
    if a > 0:
        cnt = int(2000 + 1000 * eout((t - tl[1]) / 2.5))
        put(cv, txt(f'沛县子弟 二三千人', 56, 'black', WHITE, 3, (90, 10, 0)), W / 2, 1290, a)
    # 箭头
    if t > tl[2] - 0.1:
        for k, nm in enumerate(['胡陵', '方与']):
            tx, ty = Pj(*PLACE[nm])
            p = eout((t - tl[2] - 0.5 * k) / 1.4)
            draw_arrow(cv, bez((x, y - 20), ((x + tx) / 2 + (40 if k == 0 else -60), (y + ty) / 2), (tx, ty + 30)), p, RED, 1, 54, 34, 80, 110)
        # Qin 驻军溃散
        for k, nm in enumerate(['胡陵', '方与']):
            tx, ty = Pj(*PLACE[nm])
            u = appear(t, tl[2] + 1.4, 1.5)
            r = random.Random(k)
            for j in range(18):
                ang = r.uniform(0, 6.28); rr = 20 + 160 * u * r.uniform(0.5, 1)
                put(cv, dot_sprite(3, QIN2), tx + math.cos(ang) * rr, ty + math.sin(ang) * rr * 0.7, 1 - u * 0.8)
        fx, fy = Pj(*PLACE['丰'])
        p = eout((t - tl[2] - 3.0) / 1.4)
        if p > 0:
            hx, hy = Pj(*PLACE['胡陵'])
            draw_arrow(cv, bez((hx - 20, hy + 40), (fx + 40, (hy + fy) / 2), (fx + 10, fy - 20)), p, RED, 1, 40, 26, 70, 96)
            put(cv, tag('还守丰', RED2, 34, 70), fx - 60, fy + 70, appear(t, tl[2] + 3.6, 0.4))


# ════════════ 起家三问 ════════════
def three_q(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(12, (30, 20, 16), (70, 30, 20)))
    embers(C, n=50).draw(cv, t, 0.6)
    put(cv, rrect((980, 1080), 8, (14, 11, 9, 220), GOLD + (230,), 3), W / 2, 890, appear(t, 0, 0.5))
    put(cv, txt('起家三问卡', 92, 'brush', GOLD2, glow=14, gcol=(0, 0, 0)), W / 2, 250, appear(t, 0, 0.5))
    put(cv, txt('刘邦 · 沛县起兵 · 前209年', 38, 'serifsc', RED2, 2), W / 2, 380, appear(t, 0.2, 0.5))
    y = 460
    for k, (q, items) in enumerate(P['q']):
        tk = Lt(L, k + 1)
        a = appear(t, tk, 0.5)
        put(cv, tag(f'{"一二三"[k]}  {q}', GOLD2, 44, 60), 90, y + 50, a, 'lm')
        for j, s in enumerate(items):
            put(cv, txt('· ' + s, 44, 'sans', WHITE, 2), 120, y + 135 + j * 64, appear(t, tk + 0.5 + 0.6 * j, 0.4), 'lm')
        y += 120 + 64 * len(items) + 40


# ════════════ 东汉图 ════════════
P_HAN = Proj(109.5, 121.0, 36.9)


def map_han(cv, t, T, L, P, C):
    map_common(cv, C)
    Pj = P_HAN
    draw_map(cv, Pj)
    tl = [Lt(L, k) for k in range(3)]
    put(cv, tag('示意', GREY, 26, 30), 60, 1360, 1, 'lm')
    put(cv, txt('东汉末 幽州涿郡', 60, 'brush', GOLD2, glow=10, gcol=(0, 0, 0)), W / 2, 300, 1)
    lx, ly = city(cv, Pj, '洛阳', GOLD2, 1, 16, 54, dy=-60, sub='东汉都城')
    zx, zy = city(cv, Pj, '涿县', RED2, appear(t, 0, 0.5), 14, 54, dx=0, dy=-60, pulse=1.0, t=t, sub='刘备家乡')
    city(cv, Pj, '中山', GREY, appear(t, 0.5, 0.5), 10, 40, dx=-90, dy=-10, sub='中山国')
    card_in(cv, qcard('漢景帝子中山靖王勝之後也。', '《三國志·先主傳》', '刘备是汉景帝之子中山靖王刘胜的后代。', 940, 54), t, 0.2, tl[1] - 0.1, y=470)
    if t > tl[1]:
        p = eout((t - tl[1]) / 1.6)
        d = ImageDraw.Draw(cv)
        pts = partial([(zx, zy), (lx, ly)], p)
        x0, y0 = pts[0]; x1, y1 = pts[-1]
        L_ = math.hypot(x1 - x0, y1 - y0); nseg = int(L_ / 26)
        for k in range(nseg):
            f0, f1 = k / max(nseg, 1), (k + 0.55) / max(nseg, 1)
            d.line((x0 + (x1 - x0) * f0, y0 + (y1 - y0) * f0, x0 + (x1 - x0) * f1, y0 + (y1 - y0) * f1), fill=GOLD2 + (230,), width=6)
        a = appear(t, tl[1] + 1.2, 0.5)
        put(cv, tag('约两千里 · 路程月余（示意）', GOLD2, 38, 80), (zx + lx) / 2 + 40, (zy + ly) / 2 + 20, a)
    a = appear(t, tl[2], 0.5)
    if a > 0:
        put(cv, tag('宗室名号 ≠ 官职', RED2, 46, 70), W / 2, 470, a)


# ════════════ 宗室树 ════════════
def tree(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(13))
    tl = [Lt(L, k) for k in range(3)]
    if 'tree' not in C:
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        r = random.Random(5)
        segs = []

        def grow(x, y, ang, ln, depth, gen):
            if depth == 0 or ln < 6: return
            x2, y2 = x + ln * math.sin(ang), y + ln * math.cos(ang)
            segs.append((x, y, x2, y2, gen, depth))
            nb = 6 if gen == 0 else r.choice([2, 2, 3])
            for k in range(nb):
                spread = 2.7 if gen == 0 else 1.0
                a2 = ang + (k - (nb - 1) / 2) * spread / max(1, nb - 1) + r.uniform(-0.15, 0.15)
                grow(x2, y2, a2, ln * r.uniform(0.62, 0.78), depth - 1, gen + 1)
        grow(540, 580, 0.0, 165, 8, 0)
        C['segs'] = segs
        C['leaves'] = [(s[2], s[3]) for s in segs if s[5] == 1]
    segs = C['segs']
    prog = appear(t, 0.3, max(2.0, tl[1] + 1.5))
    maxgen = 1 + prog * 8
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for (x, y, x2, y2, g, dep) in segs:
        if g < maxgen:
            f = clamp(maxgen - g)
            d.line((x, y, x + (x2 - x) * f, y + (y2 - y) * f), fill=GOLD + (int(200 - g * 18),), width=max(1, 7 - g))
    cv.alpha_composite(ov)
    put(cv, txt('中山靖王 刘胜', 52, 'black', GOLD2, 3), 540, 500, appear(t, 0, 0.5))
    card_in(cv, qcard('有子枝屬百二十餘人。', '《史記·五宗世家》', '刘胜的子孙有一百二十多人。', 900, 60), t, 0.3, tl[1] - 0.1, y=270 + 0)
    a = appear(t, tl[1], 0.5)
    if a > 0:
        lv = C['leaves']
        k = len(lv) // 3
        x, y = lv[k]
        ring(cv, x, y, 30 + 6 * math.sin(t * 5), RED2, a, 4)
        put(cv, dot_sprite(10, RED2), x, y, a)
        put(cv, txt('刘备？', 46, 'black', RED2, 3), x + 20, y + 60, a)
        put(cv, txt('将近三百年', 80, 'brush', WHITE, glow=10, gcol=(0, 0, 0)), W / 2, 300, a)
        put(cv, txt('前113年 刘胜去世  →  161年 刘备出生', 36, 'sans', GREY, 2), W / 2, 400, a)
    a = appear(t, tl[2], 0.5)
    if a > 0:
        cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(160 * a))))
        if 'ticket' not in C:
            tk = Image.new('RGBA', (760, 380), (0, 0, 0, 0)); d = ImageDraw.Draw(tk)
            d.rounded_rectangle((0, 0, 759, 379), 20, fill=(214, 190, 140, 255), outline=(120, 80, 40, 255), width=6)
            d.line((560, 20, 560, 360), fill=(120, 80, 40, 255), width=3)
            tk.alpha_composite(txt('入场券', 64, 'brush', (90, 30, 20)), (60, 40))
            tk.alpha_composite(txt('中山靖王之后', 60, 'serifsc', (60, 30, 20)), (50, 170))
            tk.alpha_composite(vtxt('汉室', 56, 'serifsc', (90, 30, 20)), (620, 110))
            C['ticket'] = tk.rotate(4, Image.BICUBIC, expand=True)
            st = Image.new('RGBA', (300, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
            d.rounded_rectangle((4, 4, 296, 156), 12, outline=(200, 30, 24, 255), width=10)
            st.alpha_composite(txt('过 期', 90, 'black', (200, 30, 24)), (50, 20))
            C['stamp'] = st.rotate(-14, Image.BICUBIC, expand=True)
        put(cv, C['ticket'], W / 2, 900, a)
        s = 1.8 - 0.8 * eout((t - tl[2] - 0.8) / 0.3)
        put(cv, C['stamp'], W / 2 + 150, 960, appear(t, tl[2] + 0.8, 0.15), scale=s)
        put(cv, txt('名字还在，门已经不认', 56, 'black', WHITE, 3), W / 2, 1230, appear(t, tl[2] + 1.5, 0.5))


# ════════════ 刘备的网 ════════════
def liubei_net(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(14))
    embers(C, n=40).draw(cv, t, 0.5)
    tl = [Lt(L, k) for k in range(5)]
    cx, cy = 540, 930
    nodes = [
        (tl[0] + 0.5, 230, 730, '母亲', '贩履织席', GREY),
        (tl[1], 850, 730, '刘元起', '同宗 · 出钱资助', PAPER),
        (tl[1] + 2.5, 850, 1150, '卢植', '同郡名儒 · 老师', GOLD2),
        (tl[2], 540, 1270, '公孙瓒', '同学', QIN2),
        (tl[3], 230, 1150, '商人', '张世平 苏双 · 金财', ORANGE),
    ]
    d = ImageDraw.Draw(cv)
    for (tk, x, y, n, r, col) in nodes:
        aa = appear(t, tk, 0.5)
        if aa > 0:
            p = eout((t - tk) / 0.6)
            d.line((cx, cy, cx + (x - cx) * p, cy + (y - cy) * p), fill=GOLD + (int(170 * aa),), width=4)
    for (tk, x, y, n, r, col) in nodes:
        aa = appear(t, tk, 0.5)
        if aa > 0: node(cv, x, y, n, r, col, aa)
    node(cv, cx, cy, '刘备', '涿县 · 少孤', RED2, appear(t, 0, 0.5), True)
    cards = [
        (tl[0], tl[1], ('先主少孤，與母販履織蓆為業。', '《三國志·先主傳》', '刘备幼年丧父，和母亲靠卖鞋织席为生。')),
        (tl[1], tl[2], ('與同宗劉德然、遼西公孫瓚俱事故九江太守同郡盧植。', '《三國志·先主傳》', '与同宗刘德然、辽西公孙瓒一起师从同郡的卢植。')),
        (tl[3], tl[4], ('中山大商張世平、蘇雙等貲累千金……乃多與之金財。', '《三國志·先主傳》', '中山大商张世平、苏双家财千金，资助了他很多钱。')),
        (tl[4], 1e9, ('先主由是得用合徒眾。', '《三國志·先主傳》', '刘备靠这笔钱，聚集起了自己的队伍。')),
    ]
    for t0, t1, (q, s, b) in cards:
        card_in(cv, qcard(q, s, b, 960, 46), t, t0 + 0.2, t1, y=380)
    a = appear(t, tl[4] + 1.0, 0.5)
    if a > 0:
        put(cv, tag('第一支队伍', RED2, 40, 80), cx, cy + 165, a)


# ════════════ 研究观点 ════════════
def research(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(15, (16, 24, 24), (20, 50, 50)))
    tl = [Lt(L, k) for k in range(6)]
    put(cv, tag('研究观点', TEAL, 40, 50), W / 2, 230, 1)
    a = window(t, 0, tl[5] - 0.2)
    put(cv, txt('李开元', 70, 'black', TEAL, 2), W / 2, 340, a)
    put(cv, txt('《汉帝国的建立与刘邦集团——军功受益阶层研究》', 34, 'serifsc', (200, 225, 220), 2), W / 2, 420, a)
    a1 = window(t, tl[0] + 0.5, tl[5] - 0.2)
    put(cv, txt('军功受益阶层', 120, 'brush', (170, 235, 225), glow=16, gcol=(20, 80, 70)), W / 2, 600, a1)
    stages = ['群盗集团', '楚国郡县', '汉王国', '汉帝国']
    y = 900
    d = ImageDraw.Draw(cv)
    for k, s in enumerate(stages):
        tk = tl[1] + 1.2 * k
        aa = appear(t, tk, 0.4) * (1 - appear(t, tl[5] - 0.2, 0.3))
        x = 150 + k * 260
        if aa > 0:
            if k > 0: d.line((x - 200, y, x - 60, y), fill=TEAL + (int(220 * aa),), width=5); d.polygon([(x - 60, y - 12), (x - 40, y), (x - 60, y + 12)], fill=TEAL + (int(220 * aa),))
            put(cv, rrect((190, 110), 8, (16, 36, 36, 230), TEAL + (220,), 3), x, y, aa)
            put(cv, txt(s, 40, 'black', WHITE), x, y, aa)
    a = appear(t, tl[2], 0.5) * (1 - appear(t, tl[5] - 0.2, 0.3))
    if a > 0:
        put(cv, txt('权力 · 财富 · 身份  重新分配', 54, 'black', (200, 240, 230), 3), W / 2, 1080, a)
    a = appear(t, tl[3], 0.5) * (1 - appear(t, tl[5] - 0.2, 0.3))
    if a > 0:
        put(cv, txt('沛县小网  →  汉初统治阶层', 56, 'black', GOLD2, 3), W / 2, 1200, a)
    a = appear(t, tl[4], 0.5) * (1 - appear(t, tl[5] - 0.2, 0.3))
    if a > 0:
        put(cv, tag('萧规曹随 · 萧何、曹参先后为汉相国', GOLD2, 40, 60), W / 2, 1310, a)
    a = appear(t, tl[5], 0.5)
    if a > 0:
        put(cv, tag('各家推演 · 只作参考', TEAL, 36, 50), W / 2, 420 + 0, a)
        put(cv, txt('客數月', 200, 'serif', (250, 232, 190), glow=20, gcol=(140, 80, 10)), W / 2, 820, a)
        put(cv, txt('——《史記·張耳陳餘列傳》', 40, 'serif', GOLD), W / 2 + 120, 1000, a)
        put(cv, txt('史书能确定的，只有这三个字', 50, 'sans', WHITE, 2), W / 2, 1140, a)


# ════════════ 收束 ════════════
def ending(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(16, (30, 18, 14), (110, 40, 20)))
    embers(C, n=110, seed=21, vel=((-20, 20), (-110, -40))).draw(cv, t, 0.9)
    tl = [Lt(L, k) for k in range(7)]
    a = window(t, 0, tl[4] - 0.3)
    put(cv, txt('「草根」量的是什么？', 90, 'brush', GOLD2, glow=14, gcol=(0, 0, 0)), W / 2, 330, a)
    oy = 560
    for k in range(2):
        ruler(cv, oy + RUL[k][0], RUL[k][1], RUL[k][2], window(t, 0.2, tl[1] - 0.1), 1)
    a = window(t, tl[1], tl[4] - 0.3)
    if a > 0:
        put(cv, txt('不是族谱上有没有名字', 64, 'black', GREY, 3), W / 2, 700, a)
        put(cv, txt('而是关键时刻能调动谁', 72, 'black', RED2, 3, glow=10, gcol=(120, 20, 0)), W / 2, 820, appear(t, tl[1] + 1.6, 0.5) * a)
    a = window(t, tl[2], tl[4] - 0.3)
    if a > 0:
        put(cv, tag('秩序稳定：出身决定天花板', QIN2, 42, 60), W / 2, 1000, a)
        put(cv, tag('秩序崩塌：能调动的人和钱决定走多远', RED2, 42, 60), W / 2, 1100, appear(t, tl[2] + 2.5, 0.5) * a)
    a = window(t, tl[3], tl[4] - 0.3)
    if a > 0:
        put(cv, txt('刘邦：无家谱，有网', 54, 'black', WHITE, 3), W / 2, 1230, a)
        put(cv, txt('刘备：有家谱，从卖鞋开始', 54, 'black', WHITE, 3), W / 2, 1310, appear(t, tl[3] + 1.5, 0.4) * a)
    a = appear(t, tl[4], 0.5)
    if a > 0:
        put(cv, txt('大泽乡 · 陈胜', 50, 'serifsc', GOLD, 2), W / 2, 520, a)
    a = appear(t, tl[5] - 0.1, 0.6)
    if a > 0:
        put(cv, vtxt('王侯將相', 150, 'serif', (252, 236, 200), 10, glow=24, gcol=(200, 80, 10)), 700, 960, a)
        put(cv, vtxt('寧有種乎', 150, 'serif', (252, 236, 200), 10, glow=24, gcol=(200, 80, 10)), 420, 960 + 40, appear(t, tl[5] + 0.8, 0.6))
        put(cv, txt('——《史記·陳涉世家》', 40, 'serif', GOLD), W - 90, 1390, appear(t, tl[5] + 1.0, 0.5), 'rm')
    a = appear(t, tl[6], 0.5)
    if a > 0:
        put(cv, txt('王侯将相，难道是天生的吗？', 50, 'sans', WHITE, 2), W / 2, 380, a)


def outro(cv, t, T, L, P, C):
    cv.alpha_composite(ink_bg(17, (24, 18, 14), (80, 40, 20)))
    embers(C, n=70, seed=23).draw(cv, t, 0.8)
    tl = [Lt(L, k) for k in range(2)]
    a = window(t, 0, tl[1] - 0.1)
    put(cv, tag('可迁移的一句判断', GOLD, 36, 40), W / 2, 560, a)
    put(cv, block('看一个人的起点，别只看简历上的出身，要看他在关键时刻能调动什么。', 70, 'black', WHITE, 880, 1.5, glow=8, gcol=(0, 0, 0)), W / 2, 850, a)
    a = appear(t, tl[1], 0.5)
    if a > 0:
        put(cv, txt('下一集', 60, 'serifsc', GOLD, 2), W / 2, 520, a)
        put(cv, txt('过期的入场券', 120, 'brush', GOLD2, glow=16, gcol=(120, 60, 10)), W / 2, 700, a)
        put(cv, txt('怎样换成第一块招牌', 90, 'brush', RED2, glow=16, gcol=(160, 30, 10)), W / 2, 860, appear(t, tl[1] + 1.0, 0.5))
        put(cv, txt('乱世起家录 · 刘备篇', 46, 'serifsc', GREY, 2), W / 2, 1050, appear(t, tl[1] + 1.8, 0.5))


KINDS = dict(procession=procession, names=names, ting_intro=ting_intro, stall=stall, debate=debate, rulers_intro=rulers_intro,
             title=title, home=home, ting_system=ting_system, analogy=analogy, network=network, rulers_score=rulers_score,
             myth=myth, pedigree=pedigree, map_qin=map_qin, night_city=night_city, quote_big=quote_big, mechanism=mechanism,
             map_advance=map_advance, three_q=three_q, map_han=map_han, tree=tree, liubei_net=liubei_net, research=research,
             ending=ending, outro=outro)
