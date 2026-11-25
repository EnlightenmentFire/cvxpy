# -*- coding: utf-8 -*-
"""各场景画面。每个函数 f(ctx) -> RGBA 1080x1920（不含标题、角标、字幕）。
ctx: t 场景内时间, dur 场景时长, li 当前句序号, lt 当前句已过时间, ld 当前句时长, lines 句列表(含 start/end), scene。"""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from art import *

CY = 830  # 插图区中心
REALMS = ["地狱", "饿鬼", "畜生", "阿修罗", "人", "天", "声闻", "缘觉", "菩萨", "佛"]
FACE_COL = {"饿鬼": (150, 170, 140), "阿修罗": (200, 70, 50), "畜生": (90, 140, 210),
            "地狱": (130, 40, 36), "天": (232, 196, 110), "人": (226, 170, 110)}
FACE_TIME = {"饿鬼": "07:30", "阿修罗": "10:00", "畜生": "15:00", "地狱": "18:00", "天": "20:00", "人": "23:30"}


def line_start(ctx, i):
    return ctx["lines"][i]["start"] if 0 <= i < len(ctx["lines"]) else ctx["dur"]


def since(ctx, i):
    """距第 i 句开始的秒数（可为负）。"""
    return ctx["t"] - line_start(ctx, i)


def fade_in(ctx, i, d=0.6):
    return ease(since(ctx, i) / d)


# ---------------------------------------------------------------- 城市街道
SKY = [  # tod 关键帧: (tod, top, bottom)
    (0.00, (40, 48, 78), (214, 150, 110)),   # 黎明
    (0.25, (86, 120, 160), (200, 196, 180)),  # 白天
    (0.55, (70, 70, 110), (220, 128, 80)),    # 黄昏
    (0.75, (22, 24, 50), (70, 50, 70)),       # 入夜
    (1.00, (8, 9, 20), (26, 24, 40)),         # 深夜
]


def sky_cols(tod):
    for (t0, a0, b0), (t1, a1, b1) in zip(SKY, SKY[1:]):
        if tod <= t1:
            k = (tod - t0) / (t1 - t0)
            return mixc(a0, a1, k), mixc(b0, b1, k)
    return SKY[-1][1], SKY[-1][2]


@functools.lru_cache(maxsize=4)
def skyline_layers(seed=7):
    rng = np.random.default_rng(seed)
    layers = []
    for li, (hmin, hmax, wmin, wmax) in enumerate([(380, 760, 60, 150), (260, 560, 70, 170), (160, 380, 90, 210)]):
        mask = Image.new("L", (W, H), 0)
        win = []
        d = ImageDraw.Draw(mask)
        x = -40
        ground = 1330 + li * 30
        while x < W + 40:
            bw = rng.integers(wmin, wmax); bh = rng.integers(hmin, hmax)
            d.rectangle((x, ground - bh, x + bw, H), fill=255)
            if rng.random() < 0.3:
                d.rectangle((x + bw * 0.4, ground - bh - 40, x + bw * 0.46, ground - bh), fill=255)
            for wy in range(int(ground - bh + 20), ground - 20, 34):
                for wx in range(int(x + 12), int(x + bw - 16), 26):
                    if rng.random() < 0.42:
                        win.append((wx, wy, rng.random()))
            x += bw + rng.integers(-10, 18)
        layers.append((mask, win))
    return layers


def street(tod, t, dim=0.0, walkers=True):
    top, bot = sky_cols(tod)
    g = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    sky = np.array(top, np.float32) * (1 - g) + np.array(bot, np.float32) * g
    sky = np.broadcast_to(sky, (H, W, 3)).copy()
    im = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    night = clamp01((tod - 0.55) / 0.3)
    # 太阳/月
    if tod < 0.6:
        sx, sy = lerp(260, 820, tod / 0.6), lerp(820, 420, math.sin(math.pi * min(tod / 0.6, 1)))
        over(im, glow(260, (255, 214, 160), 2.2, 0.55), (sx, sy))
        over(im, glow(46, (255, 236, 200), 0.7, 0.95), (sx, sy))
    else:
        over(im, glow(150, (200, 210, 255), 2.5, 0.25 * night), (800, 420))
        over(im, glow(26, (236, 236, 250), 0.6, 0.9 * night), (800, 420))
    layers = skyline_layers()
    tones = [mixc(bot, top, 0.55), mixc(top, INK, 0.55), (14, 15, 20)]
    for k, ((mask, win), tone) in enumerate(zip(layers, tones)):
        par = (k + 1) * 6 * math.sin(t * 0.05)
        col = Image.new("RGBA", (W, H), tone + (255,))
        m = mask if abs(par) < 0.5 else mask.transform(mask.size, Image.AFFINE, (1, 0, -par, 0, 1, 0))
        im.paste(col, (0, 0), m)
        if night > 0.02 and k < 2:
            d = ImageDraw.Draw(im)
            for (wx, wy, r) in win:
                on = r < 0.2 + 0.6 * night
                if on:
                    flick = 0.85 + 0.15 * math.sin(t * 0.7 + r * 50)
                    c = mixc(tone, (255, 205, 130), (0.55 if k == 0 else 0.4) * night * flick)
                    d.rectangle((wx - par, wy, wx - par + 9, wy + 13), fill=c)
    # 街面
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1395, W, H), fill=(10, 11, 14))
    d.line((0, 1395, W, 1395), fill=mixc((10, 11, 14), GOLD, 0.25), width=2)
    # 路灯
    for lx in (140, 560, 980):
        d.line((lx, 1395, lx, 1150), fill=(24, 24, 28), width=6)
        d.line((lx, 1150, lx + 40, 1140), fill=(24, 24, 28), width=6)
        if night > 0.05:
            over(im, glow(120, (255, 200, 120), 2.0, 0.5 * night), (lx + 42, 1150))
    # 行人
    if walkers:
        d = ImageDraw.Draw(im)
        for i, (sp, x0, hh) in enumerate([(38, 100, 170), (-30, 900, 160), (55, -300, 180), (-46, 1300, 150), (26, 500, 165)]):
            x = (x0 + sp * t) % (W + 400) - 200
            bob = 3 * abs(math.sin(t * 4 + i))
            draw_figure(d, x, 1398 - bob, hh, (6, 6, 8), "stand")
    # 雾带
    mist = glow(520, MIST, 3.0, 0.10)
    over(im, mist, ((t * 18) % (W + 1000) - 500, 1300))
    if dim > 0:
        im = Image.blend(im, Image.new("RGBA", (W, H), INK + (255,)), dim)
    return im


def headline(im, a):
    if a <= 0:
        return
    t1 = text_img("一天之内", "serif", 96, MIST, shadow=6)
    t2 = text_img("你可能走过六道", "serif", 120, GOLD, shadow=6)
    over(im, t1, (W // 2, 470), a)
    over(im, t2, (W // 2, 610), a)


def v_street_open(ctx):
    t = ctx["t"]
    im = street(0.02 + 0.10 * t / max(ctx["dur"], 1), t)
    headline(im, 1.0 if t < ctx["dur"] - 0.8 else ease((ctx["dur"] - t) / 0.8))
    return im


def face_medallion(im, name, k, t):
    """k: 出现进度 0..1。"""
    if k <= 0:
        return
    col = FACE_COL[name]
    cx, cy, R = W // 2, 790, 330
    s = 0.92 + 0.08 * ease(k)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    over(lay, glow(int(R * 1.35), col, 1.8, 0.55), (cx, cy))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - R * s, cy - R * s, cx + R * s, cy + R * s), fill=(12, 12, 16, 235), outline=col + (255,), width=4)
    # 气氛
    rng = np.random.default_rng(hash(name) % 1000)
    if name == "饿鬼":
        for i in range(14):
            bx = cx - R * 0.8 + rng.random() * R * 1.6
            by = cy - R + ((t * 60 + rng.random() * 600) % (2 * R))
            if (bx - cx) ** 2 + (by - cy) ** 2 < (R * 0.92) ** 2:
                d.rectangle((bx - 26, by - 16, bx + 26, by + 16), outline=col + (160,), width=2)
                d.line((bx - 18, by - 4, bx + 14, by - 4), fill=col + (120,), width=2)
                d.line((bx - 18, by + 6, bx + 6, by + 6), fill=col + (120,), width=2)
    elif name == "阿修罗":
        for i in range(9):
            a0 = rng.random() * 2 * math.pi + 0.4 * math.sin(t * 3 + i)
            pts = []
            r0 = R * 0.55
            for j in range(5):
                rr = r0 + j * R * 0.09
                aa = a0 + (0.08 if j % 2 else -0.08)
                pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
            if (int(t * 6) + i) % 3:
                d.line(pts, fill=(255, 120, 80, 200), width=4)
    elif name == "畜生":
        for i in range(3):
            ph = (t * 0.6 + i / 3) % 1
            rr = R * (0.3 + 0.6 * ph)
            d.arc((cx - rr, cy - rr, cx + rr, cy + rr), int(t * 120 + i * 120) % 360, int(t * 120 + i * 120 + 260) % 360,
                  fill=col + (int(150 * (1 - ph)),), width=3)
        over(lay, glow(150, (120, 180, 255), 1.5, 0.8), (cx + 70, cy + 150))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((cx + 40, cy + 110, cx + 100, cy + 210), 10, fill=(170, 210, 255, 255))
    elif name == "地狱":
        sh = R * (0.95 - 0.25 * ease(min(t / 4, 1)))
        for i in range(3):
            q = sh - i * 22
            d.rectangle((cx - q * 0.7, cy - q * 0.7, cx + q * 0.7, cy + q * 0.7), outline=(150, 50, 40, 200 - i * 50), width=5)
    elif name == "天":
        for i in range(24):
            a = i / 24 * 2 * math.pi + t * 0.15
            d.line((cx + R * 0.35 * math.cos(a), cy + R * 0.35 * math.sin(a), cx + R * 0.9 * math.cos(a), cy + R * 0.9 * math.sin(a)),
                   fill=col + (90,), width=3)
    elif name == "人":
        for i in range(3):
            ph = (t * 0.25 + i / 3) % 1
            rr = R * (0.35 + 0.55 * ph)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=col + (int(170 * (1 - ph)),), width=3)
    # 侧脸
    face_c = mixc(col, (240, 236, 228), 0.35) if name != "地狱" else (70, 28, 26)
    shake = 4 * math.sin(t * 40) if name == "阿修罗" else 0
    d.polygon(profile_poly(cx - 30 + shake, cy - 60, 240 * s), fill=face_c + (255,))
    if name == "饿鬼":  # 细颈
        d.polygon([(cx - 8, cy + 40), (cx + 6, cy + 40), (cx + 2, cy + 170), (cx - 4, cy + 170)], fill=(12, 12, 16, 255))
    # 圆形遮罩外淡出
    over(im, lay, (0, 0), ease(k), anchor="lt")
    nm = text_img(name + ("道" if name not in ("地狱",) else ""), "ukai", 150, col, shadow=5)
    over(im, nm, (W // 2, 1235), ease(k))
    tm = text_img(FACE_TIME[name], "sans", 44, GREY)
    over(im, tm, (W // 2, 1345), ease(k))


def v_day_six(ctx):
    t, li = ctx["t"], ctx["li"]
    faces = [l.get("face") for l in ctx["lines"]]
    name = faces[li] if 0 <= li < len(faces) else None
    tods = {"饿鬼": 0.12, "阿修罗": 0.3, "畜生": 0.45, "地狱": 0.6, "天": 0.8, "人": 0.98}
    if name:
        tod = tods[name]
        prev = faces[li - 1] if li > 0 else None
        if prev:
            tod = lerp(tods[prev], tod, ease(since(ctx, li) / 1.2))
    else:
        tod = 0.98
    im = street(tod, t + 12, dim=0.45 if name else 0.15)
    if name:
        face_medallion(im, name, since(ctx, li) / 0.7, since(ctx, li))
    else:  # 六道一天走完：六个小圆环一排
        k = since(ctx, li)
        for i, n in enumerate(["饿鬼", "阿修罗", "畜生", "地狱", "天", "人"]):
            x = 150 + i * 156
            a = ease((k - i * 0.15) / 0.5)
            over(im, glow(80, FACE_COL[n], 1.6, 0.6), (x, 820), a)
            over(im, text_img(n, "ukai", 54, FACE_COL[n], shadow=3), (x, 820), a)
        over(im, text_img("六道，一天就走完了", "serif", 70, MIST, shadow=5), (W // 2, 1040), ease((k - 1.0) / 0.6))
    return im


# ---------------------------------------------------------------- 十法界
def dial(im, t, lit, web=0.0, pointer=None, center="一念", rot=0.0, enso_a=1.0, counters=0.0):
    cx, cy, R = W // 2, CY - 10, 360
    over(im, enso(470, 62, GOLD, seed=3, alpha=0.85), (cx, cy), enso_a)
    over(im, glow(300, GOLD, 2.4, 0.18 + 0.08 * math.sin(t * 1.3)), (cx, cy))
    pos = []
    for i in range(10):
        a = -math.pi / 2 + math.pi + (i + 0.5) / 10 * 2 * math.pi + rot
        pos.append((cx + R * math.cos(a), cy + R * math.sin(a)))
    if web > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        for i in range(10):
            for j in range(i + 1, 10):
                d.line((pos[i], pos[j]), fill=GOLD + (int(70 * web),), width=2)
        over(im, lay, (0, 0), 1.0, anchor="lt")
    for i, (x, y) in enumerate(pos):
        a = clamp01(lit[i])
        sage = i >= 6
        col = GOLD if sage else [(150, 50, 40), (140, 160, 130), (100, 140, 200), (200, 80, 60), (226, 170, 110), (232, 196, 110)][i]
        over(im, glow(95, col, 1.8, 0.75 * a), (x, y))
        dd = ImageDraw.Draw(im)
        r = 64
        dd.ellipse((x - r, y - r, x + r, y + r), fill=(14, 14, 18, 230), outline=mixc((60, 58, 54), col, a) + (255,), width=3)
        over(im, text_img(REALMS[i], "ukai", 44 if len(REALMS[i]) < 3 else 36, mixc((90, 88, 84), col, a)), (x, y))
    if pointer is not None:
        px, py = pointer
        dd = ImageDraw.Draw(im)
        dd.line((cx, cy, px, py), fill=MIST + (220,), width=4)
        over(im, glow(40, MIST, 1.2, 0.9), (px, py))
    over(im, glow(110, (255, 230, 170), 2.0, 0.6), (cx, cy))
    over(im, text_img(center, "ukai", 76, (250, 240, 215), shadow=4), (cx, cy))
    if counters > 0:
        rows = ["十界×十界＝百界", "×十如是＝千如", "×三种世间＝三千"]
        for k, r in enumerate(rows):
            over(im, text_img(r, "serif", 40, GOLD if k == 2 else MIST, shadow=3), (cx - 330 + k * 330, 1375), ease(counters * 3 - k))
    return pos


def v_ten_realms(ctx):
    t, li = ctx["t"], ctx["li"]
    im = ink_bg(1).copy()
    lit = [0.0] * 10
    lines = ctx["lines"]
    # 各句点亮
    for i, l in enumerate(lines):
        if l.get("ring") == 6 and ctx["t"] >= l["start"]:
            k = (t - l["start"]) / max(l["end"] - l["start"], 0.1)
            for j in range(6):
                lit[j] = max(lit[j], ease(k * 6 - j))
        if l.get("ring") == 10 and ctx["t"] >= l["start"]:
            k = (t - l["start"]) / max(l["end"] - l["start"], 0.1)
            for j in range(6, 10):
                lit[j] = max(lit[j], ease(k * 4 - (j - 6)))
    if li >= 3:
        lit = [1.0] * 10
    webk = 0.0
    cnt = 0.0
    for i, l in enumerate(lines):
        if l.get("ring") == -1 and t >= l["start"]:
            webk = max(webk, ease((t - l["start"]) / 2.0))
            if "百界" in l["say"]:
                cnt = clamp01((t - l["start"]) / max(l["end"] - l["start"], 0.1))
            elif cnt == 0 and webk > 0 and i > 0 and "百界" in lines[i - 1]["say"]:
                cnt = 1
    if li == 3:  # 前六个 = 六道
        k = since(ctx, 3)
        lit = [1.0] * 6 + [0.25] * 4
    if li == 4:  # 不是十层楼
        k = since(ctx, 4)
    if li >= 6 and "地狱里" in lines[li]["say"]:
        lit = [1.0] * 10
        webk = 1.0
    if li == 7 and "百界" not in lines[li]["say"]:
        pass
    dial(im, t, lit, web=webk, counters=cnt if li == 6 or (li >= 5 and cnt) else 0.0)
    if li == 4:
        k = since(ctx, 4)
        # 十层楼划掉
        d = ImageDraw.Draw(im)
        a = ease(k / 0.5)
        for j in range(10):
            y = 420 + j * 24
        over(im, text_img("✕ 十层楼", "serif", 56, VERM, shadow=3), (W // 2, 1330), a)
    return im


def v_ten_realms_turn(ctx):
    t, li = ctx["t"], ctx["li"]
    im = ink_bg(1).copy()
    lit = [0.35] * 10
    # 指针在各界间跳动
    seq = [0, 5, 2, 9, 3, 7, 1, 4, 8, 6]
    step = int(t / 0.9)
    target = seq[step % 10]
    if "地狱到佛" in ctx["lines"][li]["say"]:
        k = ease(since(ctx, li) / 2.2)
        target = None
        ang_from, ang_to = 0, 9
    cx, cy, R = W // 2, CY - 10, 360

    def ang(i):
        return -math.pi / 2 + math.pi + (i + 0.5) / 10 * 2 * math.pi
    if target is None:
        a = lerp(ang(0), ang(9) - 2 * math.pi if False else ang(9), k)
        pidx = 0 if k < 0.5 else 9
        lit[0] = 1.0 - k * 0.6
        lit[9] = 0.4 + k * 0.6
        p = (cx + (R - 70) * math.cos(a), cy + (R - 70) * math.sin(a))
    else:
        f = (t / 0.9) % 1
        prev = seq[(step - 1) % 10]
        a0, a1 = ang(prev), ang(target)
        if a1 - a0 > math.pi: a1 -= 2 * math.pi
        if a0 - a1 > math.pi: a1 += 2 * math.pi
        a = lerp(a0, a1, ease(f / 0.4))
        lit[target] = 1.0
        p = (cx + (R - 70) * math.cos(a), cy + (R - 70) * math.sin(a))
    dial(im, t, lit, pointer=p, center="心")
    if li == 0:
        over(im, text_img("界 ＝ 状态，不是地址", "serif", 58, MIST, shadow=4), (W // 2, 1340), fade_in(ctx, 0))
    return im


# ---------------------------------------------------------------- 引文卡
QUOTE_LINES = {}


def quote_card(qid, reveal, plain_a, t, wide=False):
    from script_data import QUOTES
    q = QUOTES[qid]
    lines = q["text"].split("\n")
    size = 58 if max(len(x) for x in lines) <= 14 else 50
    body = [text_img(x, "kai", size, (34, 28, 24)) for x in lines]
    srcim = text_img(q["src"], "kai", 30, (120, 96, 70))
    plain = text_img(q["plain"], "sans", 40, (70, 60, 50))
    bh = sum(b.height for b in body) + 14 * len(body)
    cw = 980
    ch = 120 + bh + 30 + srcim.height + 40 + plain.height + 90
    card = paper_tex(cw, ch).copy()
    y = 80
    n = len(body)
    for i, b in enumerate(body):
        a = ease(reveal * n - i)
        over(card, b, (cw // 2, y + b.height // 2), a)
        y += b.height + 14
    y += 20
    over(card, srcim, (cw // 2, y + srcim.height // 2), ease(reveal * n - (n - 1)))
    y += srcim.height + 30
    d = ImageDraw.Draw(card)
    d.line((cw * 0.3, y, cw * 0.7, y), fill=(160, 130, 100, int(200 * plain_a)), width=2)
    y += 30
    over(card, plain, (cw // 2, y + plain.height // 2), plain_a)
    # 印章
    seal = Image.new("RGBA", (86, 86), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    sd.rounded_rectangle((2, 2, 84, 84), 8, fill=VERM + (230,))
    over(seal, text_img("印\n照", "ukai", 30, (245, 230, 210), spacing=0), (43, 43))
    over(card, seal, (cw - 70, ch - 70), 0.9)
    return card


def v_quote(ctx, end=False):
    t, li = ctx["t"], ctx["li"]
    im = ink_bg(2, warm=0.6).copy()
    over(im, enso(520, 50, GOLD, seed=8, alpha=0.30), (W // 2, CY))
    over(im, glow(int(380 + 20 * math.sin(t)), GOLD, 2.6, 0.18), (W // 2, CY))
    qid = ctx["scene"]["quote"]
    lines = ctx["lines"]
    rd = [i for i, l in enumerate(lines) if l.get("slow")]
    r0, r1 = lines[rd[0]]["start"], lines[rd[-1]]["end"]
    reveal = clamp01((t - r0 + 0.3) / max(r1 - r0, 0.5))
    plain_line = rd[-1] + 1
    plain_a = ease(since(ctx, plain_line) / 0.8) if plain_line < len(lines) else 0
    card = quote_card(qid, reveal, plain_a, t)
    a = ease(t / 0.8)
    if end and t > ctx["dur"] - 2.0:
        a *= 1.0
    over(im, card, (W // 2, CY + 10 + 10 * (1 - a)), a)
    return im


def v_quote_end(ctx):
    im = v_quote(ctx, end=True)
    t, dur = ctx["t"], ctx["dur"]
    k = ease((t - (dur - 2.2)) / 1.6)
    if k > 0:
        over(im, text_img("一切唯心造", "ukai", 92, GOLD, shadow=6), (W // 2, 1420), k)
    return im


# ---------------------------------------------------------------- 地狱
def room(t, door_open=0.0, figure="curl", light=0.0, hue=(120, 40, 34)):
    im = ink_bg(4).copy()
    d = ImageDraw.Draw(im)
    # 一点透视
    bx0, by0, bx1, by1 = 330, 520, 750, 1080
    lc = mixc(INK, GOLD, 0.22) + (255,)
    for (x, y) in [(0, 300), (W, 300), (0, 1400), (W, 1400)]:
        tx = bx0 if x == 0 else bx1
        ty = by0 if y == 300 else by1
        d.line((x, y, tx, ty), fill=lc, width=2)
    d.rectangle((bx0, by0, bx1, by1), outline=lc, width=2)
    # 门
    dx0, dy0, dx1, dy1 = 480, 700, 610, 1080
    d.rectangle((dx0, dy0, dx1, dy1), fill=(8, 8, 10), outline=mixc(INK, GOLD, 0.35), width=3)
    crack = 2 + door_open * 120
    if door_open < 0.01:
        d.line((dx1 - 2, dy0 + 4, dx1 - 2, dy1 - 2), fill=(255, 220, 160, 200), width=2)
        over(im, glow(60, (255, 210, 150), 2.0, 0.35 + 0.1 * math.sin(t * 2)), (dx1, (dy0 + dy1) // 2))
    else:
        # 门洞亮
        op = door_open
        d.rectangle((dx0, dy0, dx1, dy1), fill=mixc((8, 8, 10), (255, 236, 200), min(1, 0.3 + op)))
        # 门扇向内转
        pw = (dx1 - dx0) * (1 - op)
        d.polygon([(dx0, dy0), (dx0 + pw, dy0 + 20 * op), (dx0 + pw, dy1 - 10 * op), (dx0, dy1)], fill=(30, 26, 24))
        # 地面光楔
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.polygon([(dx0 + pw, dy1), (dx1, dy1), (dx1 + 420 * op, 1400), (dx0 + pw - 200 * op, 1400)],
                   fill=(255, 226, 170, int(110 * op)))
        lay = lay.filter(ImageFilter.GaussianBlur(10))
        over(im, lay, (0, 0), 1, anchor="lt")
        over(im, glow(380, (255, 220, 160), 2.0, 0.55 * op), ((dx0 + dx1) // 2, (dy0 + dy1) // 2))
    over(im, glow(420, hue, 2.0, 0.35), (W // 2, 1250))
    d = ImageDraw.Draw(im)
    col = (6, 6, 8)
    if figure == "curl":
        draw_figure(d, 420, 1300, 380, col, "curl")
    elif figure == "stand":
        draw_figure(d, 470, 1310, 420, col, "stand")
    return im


def shuttle_box(im, k, cross=None):
    """两格箱示意（不画动物）：左格有电，右格安全；cross: 0..1 一个圆点越过矮栏。"""
    if k <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 170, 1180, 910, 1380
    d.rounded_rectangle((x0, y0, x1, y1), 14, fill=(16, 16, 20, 220), outline=MIST + (200,), width=3)
    mx = (x0 + x1) // 2
    d.rectangle((mx - 8, y1 - 70, mx + 8, y1), fill=GOLD + (255,))
    # 电
    for i in range(3):
        zx = x0 + 60 + i * 90
        d.line([(zx, y1 - 20), (zx + 20, y1 - 60), (zx + 5, y1 - 60), (zx + 28, y1 - 110)], fill=(240, 120, 80, 230), width=4)
    over(lay, text_img("有电击", "sans", 34, (240, 140, 110)), ((x0 + mx) // 2, y0 + 36))
    over(lay, text_img("安全", "sans", 34, JADE), ((mx + x1) // 2, y0 + 36))
    if cross is not None:
        p = clamp01(cross)
        cx_ = lerp(x0 + 300, x1 - 120, ease(p))
        cy_ = y1 - 40 - 90 * math.sin(math.pi * clamp01((p - 0.35) / 0.3))
        d.ellipse((cx_ - 18, cy_ - 18, cx_ + 18, cy_ + 18), fill=MIST + (255,))
    over(im, lay, (0, 0), k, anchor="lt")


def v_hell_room(ctx):
    t, li = ctx["t"], ctx["li"]
    im = room(t)
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li] if li >= 0 else ""
    if "无间" in cur:
        over(im, text_img("无 间", "ukai", 180, (150, 50, 40), shadow=8), (W // 2, 420), 0.85 * fade_in(ctx, li, 1.0))
    if li >= 3:
        box_a = ease(since(ctx, 3) / 0.8)
        cross = None
        if "跨过去" in cur:
            cross = since(ctx, li) / 2.5
        shuttle_box(im, box_a * (1 if li < 9 else 0.6), cross)
        over(im, text_img("示意图 · 不展示动物实验", "sans", 28, GREY), (W // 2, 1415), box_a)
    if "习得性无助" in cur:
        over(im, text_img("习得性无助", "serif", 92, MIST, shadow=6), (W // 2, 420), fade_in(ctx, li))
    if "伦理" in cur:
        over(im, text_img("动物实验 · 有伦理争议", "serif", 56, (220, 160, 120), shadow=4), (W // 2, 420), fade_in(ctx, li))
    return im


@functools.lru_cache(maxsize=2)
def brain_base():
    im = ink_bg(5).copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = W // 2 - 20, 780
    # 大脑（侧视，面朝右）
    pts = []
    for i in range(120):
        a = i / 120 * 2 * math.pi
        rx, ry = 380, 280
        r = 1 + 0.05 * math.sin(a * 9) + (0.08 if math.sin(a) > 0.2 and math.cos(a) < 0 else 0)
        pts.append((cx + rx * r * math.cos(a), cy - 40 + ry * r * math.sin(a) * (0.85 if math.sin(a) > 0 else 1)))
    d.polygon(pts, outline=MIST + (200,), fill=(30, 30, 36, 200))
    # 小脑
    d.ellipse((cx - 330, cy + 80, cx - 120, cy + 230), outline=MIST + (170,), fill=(26, 26, 30, 220))
    # 脑干
    d.polygon([(cx - 70, cy + 120), (cx + 10, cy + 120), (cx - 10, cy + 420), (cx - 80, cy + 420)], outline=MIST + (170,), fill=(26, 26, 30, 230))
    # 沟回
    rng = np.random.default_rng(3)
    for i in range(16):
        x = cx - 300 + rng.random() * 560
        y = cy - 230 + rng.random() * 330
        L = 60 + rng.random() * 90
        a = rng.random() * math.pi
        d.arc((x - L / 2, y - L / 4, x + L / 2, y + L / 4), int(math.degrees(a)), int(math.degrees(a)) + 140, fill=MIST + (70,), width=3)
    over(im, lay, (0, 0), 1, anchor="lt")
    return im


def v_hell_brain(ctx):
    t, li = ctx["t"], ctx["li"]
    im = brain_base().copy()
    cx, cy = W // 2 - 20, 780
    drn = (cx - 40, cy + 230)
    mpfc = (cx + 300, cy - 20)
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    red_a = 0.0 if li < 2 else (0.8 + 0.2 * math.sin(t * 5))
    gold_a = 0.0
    if any(k in "".join(says[:li + 1]) for k in ["控制感"]):
        gold_a = ease(since(ctx, next(i for i, s in enumerate(says) if "控制感" in s)) / 0.8)
    if li >= 2:
        over(im, glow(110, (230, 70, 50), 1.6, red_a), drn)
        over(im, text_img("中缝背核\n默认：退缩、被动", "sans", 34, (240, 150, 130), shadow=3), (drn[0] - 250, drn[1] + 40))
    if gold_a > 0:
        over(im, glow(120, GOLD, 1.6, gold_a), mpfc)
        over(im, text_img("内侧前额叶\n察觉：我能控制", "sans", 34, GOLD, shadow=3), (mpfc[0] - 40, mpfc[1] - 360 + 200), gold_a)
        # 抑制箭头
        if any("压住" in s for s in says[:li + 1]):
            k = ease(since(ctx, next(i for i, s in enumerate(says) if "压住" in s)) / 1.2)
            d = ImageDraw.Draw(im)
            ex, ey = lerp(mpfc[0], drn[0] + 60, k), lerp(mpfc[1], drn[1] - 40, k)
            d.line((mpfc, (ex, ey)), fill=GOLD + (255,), width=6)
            if k > 0.95:
                d.line((drn[0] + 30, drn[1] - 70, drn[0] + 90, drn[1] - 10), fill=GOLD + (255,), width=8)
                over(im, text_img("抑制", "serif", 44, GOLD, shadow=3), (drn[0] + 200, drn[1] - 120))
            # 红光减弱
    if "预防针" in cur or "可以逃脱" in cur:
        over(im, text_img("先有掌控的经验 → 不易垮掉", "serif", 50, JADE, shadow=4), (W // 2, 1330), fade_in(ctx, li))
    if "学会希望" in cur:
        over(im, text_img("不是学会了绝望\n是太久没有机会学会希望", "serif", 56, MIST, shadow=5), (W // 2, 1330), fade_in(ctx, li))
    if li == 1:
        over(im, text_img("被动，不是学来的", "serif", 64, MIST, shadow=5), (W // 2, 1330), fade_in(ctx, 1, 1.0) * 0 + 0)
    if li in (2, 3):
        over(im, text_img("被动，不是学来的", "serif", 64, MIST, shadow=5), (W // 2, 1330), fade_in(ctx, 2))
    return im


def v_hell_door(ctx):
    t, li, dur = ctx["t"], ctx["li"], ctx["dur"]
    says = [l["say"] for l in ctx["lines"]]
    op = 0.0
    if li >= 3:
        s = line_start(ctx, 3)
        op = ease((t - s) / 3.0)
    if li == len(says) - 1:
        op = max(op, ease(since(ctx, li) / 2.5))
    fig = "curl" if op < 0.35 else "stand"
    im = room(t, door_open=op, figure=fig)
    cur = says[li]
    if "起床" in cur:
        k = since(ctx, li)
        steps = ["起床", "叠被", "出门走十分钟"]
        for i, s_ in enumerate(steps):
            over(im, text_img(s_, "serif", 54, MIST, shadow=4), (W // 2, 360 + i * 90), ease((k - 0.9 - i * 1.0) / 0.5))
    if "门不一定锁着" in cur:
        over(im, text_img("门，没有锁", "serif", 72, (255, 220, 160), shadow=5), (W // 2, 400), fade_in(ctx, li))
    if "真的有用" in cur:
        over(im, text_img("我做的事，真的有用", "serif", 66, (255, 226, 170), shadow=5), (W // 2, 400), fade_in(ctx, li))
    return im


# ---------------------------------------------------------------- 饿鬼：隧道
def tunnel(t, narrow=1.0, warm=0.0, bill=True):
    im = ink_bg(6).copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = W // 2, CY
    n = 14
    for i in range(n):
        ph = ((i / n) + t * 0.12) % 1
        s = 0.06 + ph ** 2.2 * 1.6
        hw, hh = 520 * s, 640 * s
        a = int(200 * clamp01(ph * 2) * clamp01((1 - ph) * 3))
        col = mixc((90, 110, 90), (230, 190, 120), warm)
        d.rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), int(60 * s), outline=col + (a,), width=max(2, int(5 * s)))
    over(im, lay, (0, 0), 1, anchor="lt")
    if bill:
        b = Image.new("RGBA", (220, 140), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.rectangle((0, 0, 219, 139), fill=(236, 228, 210, 255), outline=(120, 110, 90, 255), width=3)
        for k in range(4):
            bd.line((20, 30 + k * 26, 150 - (k % 2) * 40, 30 + k * 26), fill=(110, 100, 90, 255), width=4)
        over(b, text_img("¥", "sansb", 60, VERM), (180, 70))
        sc = 1.0 + 0.04 * math.sin(t * 2)
        b = b.resize((int(220 * sc), int(140 * sc)))
        over(im, glow(200, (240, 230, 200), 2, 0.4), (cx, cy))
        over(im, b, (cx, cy))
    # 隧道视野：外围变暗
    yy, xx = np.ogrid[0:H, 0:W]
    return im, narrow


@functools.lru_cache(maxsize=32)
def vignette(r_q):
    r = r_q
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - W / 2) ** 2 + ((yy - CY) * 0.8) ** 2)
    a = np.clip((d - r) / 260.0, 0, 1) * 0.94
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = INK
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def chips(im, items, y0, k_list, size=46, col=MIST):
    for i, (txt, k) in enumerate(zip(items, k_list)):
        over(im, text_img(txt, "serif", size, col, shadow=4), (W // 2, y0 + i * int(size * 1.6)), k)


def v_tunnel(ctx, soft=False):
    t, li = ctx["t"], ctx["li"]
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    if not soft:
        # 越往后越窄
        tn = ease(t / max(ctx["dur"], 1))
        r = int(lerp(700, 260, tn) / 20) * 20
        warm = 0.0
    else:
        tn = ease(t / max(ctx["dur"] * 0.8, 1))
        r = int(lerp(260, 900, tn) / 20) * 20
        warm = tn
    im, _ = tunnel(t, warm=warm)
    over(im, vignette(r), (0, 0), 1, anchor="lt")
    if soft:
        over(im, glow(520, (255, 214, 150), 2.2, 0.3 * tn), (W // 2, CY))
    if "腹大如山" in cur:
        over(im, text_img("腹大如山 · 咽如针孔", "ukai", 84, (170, 190, 160), shadow=5), (W // 2, 420), fade_in(ctx, li))
        over(im, text_img("《阿毘達磨大毘婆沙論》卷一七二", "kai", 32, GREY), (W // 2, 500), fade_in(ctx, li))
    if "怎么吃" in cur:
        over(im, text_img("怎么吃，都不够", "serif", 70, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
    if "隧道视野" in cur:
        over(im, text_img("隧道视野", "serif", 96, MIST, shadow=6), (W // 2, 420), fade_in(ctx, li))
    if "稀缺" in cur and "书" in cur:
        over(im, text_img("《稀缺》 Scarcity", "serif", 70, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
        over(im, text_img("Mullainathan & Shafir, 2013", "serif", 34, GREY), (W // 2, 500), fade_in(ctx, li))
    if "带宽" in cur or "内存" in cur:
        k = fade_in(ctx, li)
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 190, 1260, 890, 1330
        d.rounded_rectangle((x0, y0, x1, y1), 12, outline=MIST + (int(220 * k),), width=3)
        fill = lerp(0, 0.72, ease(since(ctx, li) / 1.5))
        d.rounded_rectangle((x0 + 6, y0 + 6, x0 + 6 + (x1 - x0 - 12) * fill, y1 - 6), 8, fill=VERM + (int(230 * k),))
        over(im, text_img("脑子的带宽：被「缺」占掉一大块", "sans", 38, MIST, shadow=3), (W // 2, 1380), k)
    if "专注红利" in cur:
        over(im, text_img("专注红利", "serif", 80, GOLD, shadow=5), (W // 2, 420), fade_in(ctx, li))
    if "越缺越忙" in cur:
        k = since(ctx, li)
        chips(im, ["借明天的", "↓", "明天更缺", "↓", "越缺越忙，越忙越缺"], 1150 - 120, [ease((k - i * 0.7) / 0.5) for i in range(5)], 42)
    if soft:
        if "时间" in cur and "认可" in cur:
            k = since(ctx, li)
            chips(im, ["时间", "认可", "爱"], 1180, [ease((k - 1.2 - i * 0.8) / 0.5) for i in range(3)], 56, (220, 200, 170))
        if "填不满" in cur:
            over(im, text_img("永远填不满", "serif", 80, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
    return im


def v_tunnel_soft(ctx):
    return v_tunnel(ctx, soft=True)


# ---------------------------------------------------------------- 甘蔗农
@functools.lru_cache(maxsize=2)
def cane_bg():
    im = ink_bg(7, warm=0.4).copy()
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(11)
    for i in range(90):
        x = rng.random() * W
        h = 300 + rng.random() * 320
        base = 1420
        col = mixc((40, 52, 36), (120, 130, 80), rng.random() * 0.5)
        d.line((x, base, x + 10 * rng.standard_normal(), base - h), fill=col, width=int(5 + rng.random() * 5))
        for k in range(int(h / 60)):
            yk = base - k * 60 - rng.random() * 20
            d.line((x - 4, yk, x + 4, yk), fill=(20, 24, 18), width=2)
        lx = x + 10 * rng.standard_normal()
        ly = base - h
        for s in (-1, 1):
            d.line((lx, ly, lx + s * (60 + rng.random() * 60), ly + 50 + rng.random() * 60), fill=col, width=4)
    over(im, Image.new("RGBA", (W, 1100), INK + (150,)), (0, 0), 1, anchor="lt")
    return im


def bars(im, x0, y0, title, items, k, vmax, fmt="{:.2f}", unit="", h=300, bw=150, note=None):
    """items: [(label, value, color)]"""
    d = ImageDraw.Draw(im)
    over(im, text_img(title, "sans", 36, MIST, shadow=3), (x0 + len(items) * (bw + 70) // 2, y0 - 40), k)
    for i, (lab, v, c) in enumerate(items):
        x = x0 + i * (bw + 70)
        hh = h * v / vmax * ease(k * 1.4 - i * 0.2)
        d.rectangle((x, y0 + h - hh, x + bw, y0 + h), fill=c + (int(235 * k),))
        over(im, text_img(fmt.format(v) + unit, "sansb", 40, MIST), (x + bw // 2, y0 + h - hh - 34), ease(k * 1.4 - i * 0.2))
        over(im, text_img(lab, "sans", 34, GREY), (x + bw // 2, y0 + h + 34), k)
    if note:
        over(im, text_img(note, "sans", 28, GREY), (x0 + len(items) * (bw + 70) // 2 - 35, y0 + h + 90), k)


def v_cane(ctx):
    t, li = ctx["t"], ctx["li"]
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    im = cane_bg().copy()
    i_test = next(i for i, s in enumerate(says) if "收获前手头紧" in s)
    i_rep = next(i for i, s in enumerate(says) if "老实说" in s)
    if li <= 1:
        over(im, text_img("Mani, Mullainathan, Shafir & Zhao\nScience 341 (2013)", "serif", 40, MIST, shadow=4), (W // 2, 520), fade_in(ctx, 0))
        if li == 1:
            over(im, text_img("印度泰米尔纳德邦 · 甘蔗农", "serif", 52, GOLD, shadow=4), (W // 2, 680), fade_in(ctx, 1))
    elif li < i_test:
        over(im, text_img("464 位甘蔗农 · 同一批人\n收获前（手头紧）   vs   收获后（手头宽）", "serif", 44, MIST, shadow=4), (W // 2, 560), fade_in(ctx, 2))
        if li >= 3:
            over(im, text_img("瑞文推理题  ·  数字版斯特鲁普测验", "serif", 44, GOLD, shadow=4), (W // 2, 760), fade_in(ctx, 3))
    elif li < i_rep:
        k = ease(since(ctx, i_test) / 1.5)
        bars(im, 110, 420, "瑞文推理题 · 平均答对题数", [("收获前", 4.35, (150, 120, 90)), ("收获后", 5.45, GOLD)], k, 6.0, h=320, bw=120)
        bars(im, 610, 420, "斯特鲁普 · 用时（秒，越少越好）", [("收获前", 146, (150, 120, 90)), ("收获后", 131, GOLD)], k, 170, fmt="{:.0f}", h=320, bw=120)
        over(im, text_img("数据：Mani et al., Science 2013 田野研究", "sans", 28, GREY), (W // 2, 905), k)
        if "人还是那个人" in cur:
            over(im, text_img("人还是那个人，变的只是缺不缺", "serif", 54, MIST, shadow=4), (W // 2, 1040), fade_in(ctx, li))
    else:
        k = fade_in(ctx, i_rep)
        over(im, text_img("复现结果不一", "serif", 92, (230, 160, 90), shadow=6), (W // 2, 470), k)
        items = []
        if li >= i_rep + 1:
            items.append(("Carvalho, Meier & Wang, AER 2016\n发薪日前后：认知测验无差别", fade_in(ctx, i_rep + 1)))
        if li >= i_rep + 2:
            items.append(("O'Donnell 等 24 位作者, PNAS 2021\n重做 20 项网上稀缺实验：仅 4 项显著", fade_in(ctx, i_rep + 2)))
        for j, (s_, a) in enumerate(items):
            over(im, text_img(s_, "sans", 38, MIST, shadow=3), (W // 2, 680 + j * 170), a)
        if li >= i_rep + 3:
            over(im, text_img("有实证  ·  有复现争议", "serif", 64, GOLD, shadow=5), (W // 2, 1050), fade_in(ctx, i_rep + 3))
    return im


# ---------------------------------------------------------------- 天道：宴席
@functools.lru_cache(maxsize=4)
def feast_base(q):
    """q: 0 华美 .. 1 褪色（量化缓存）。"""
    fade = q / 10
    im = ink_bg(8, warm=1.0).copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx = W // 2
    # 长桌透视
    d.polygon([(cx - 70, 700), (cx + 70, 700), (cx + 470, 1420), (cx - 470, 1420)], fill=mixc((90, 40, 30), (50, 46, 44), fade) + (255,))
    d.polygon([(cx - 70, 700), (cx + 70, 700), (cx + 470, 1420), (cx - 470, 1420)], outline=mixc(GOLD, GREY, fade) + (255,), width=3)
    # 盘盏
    for k in range(7):
        z = k / 6
        y = lerp(730, 1360, z ** 1.3)
        sp = lerp(60, 360, z ** 1.3)
        for s in (-1, 1):
            r = lerp(8, 34, z)
            d.ellipse((cx + s * sp * 0.6 - r, y - r * 0.5, cx + s * sp * 0.6 + r, y + r * 0.5), fill=mixc((240, 220, 170), (150, 146, 140), fade) + (255,))
            # 宾客剪影
            draw_figure(d, cx + s * (sp + lerp(30, 120, z)), y + lerp(10, 60, z), lerp(70, 360, z), (10, 9, 10, 255), "sit", flip=(s < 0))
    over(im, lay, (0, 0), 1, anchor="lt")
    return im


def v_feast(ctx, fading=False):
    t, li = ctx["t"], ctx["li"]
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    fade = 0.0 if not fading else ease(t / max(ctx["dur"], 1))
    im = feast_base(int(round(fade * 10))).copy()
    # 灯笼
    for k in range(9):
        x = 120 + k * 105
        y = 470 + 30 * math.sin(k * 1.3)
        on = 1.0 if not fading else clamp01((1 - fade) * 9 - (8 - k) * 0.6 + 0.4)
        on *= 0.9 + 0.1 * math.sin(t * 3 + k)
        over(im, glow(110, (255, 170, 90), 1.8, 0.7 * on), (x, y))
        d = ImageDraw.Draw(im)
        d.ellipse((x - 22, y - 30, x + 22, y + 30), fill=mixc((60, 40, 36), (230, 90, 50), on))
        d.line((x, y - 30, x, 300), fill=(40, 34, 30), width=2)
    if fading:
        g = ImageEnhance.Color(im.convert("RGB")).enhance(1 - 0.85 * fade)
        im = g.convert("RGBA")
    if "五衰" in cur:
        over(im, text_img("天人五衰", "ukai", 120, (232, 196, 110), shadow=6), (W // 2, 380), fade_in(ctx, li))
    i_b = next((i for i, s in enumerate(says) if "二十二位" in s), None)
    if not fading and i_b is not None and li >= i_b:
        k = ease(since(ctx, i_b) / 1.2)
        panel = Image.new("RGBA", (W, 1040), (10, 10, 14, 205))
        im.alpha_composite(with_alpha(panel, k), (0, 300))
        over(im, text_img("Brickman, Coates & Janoff-Bulman, JPSP 1978\n中奖者 22 人 · 对照 22 人（0–5 分）", "sans", 30, GREY), (W // 2, 360), k)
        bars(im, 110, 480, "现在有多快乐", [("中奖者", 4.00, GOLD), ("对照组", 3.82, (150, 140, 120))], ease(since(ctx, i_b + 1) / 1.2) if li > i_b else 0, 5.0, h=280, bw=120)
        if li >= i_b + 2:
            bars(im, 610, 480, "日常小事的乐趣", [("中奖者", 3.33, GOLD), ("对照组", 3.82, (150, 140, 120))], ease(since(ctx, i_b + 2) / 1.2), 5.0, h=280, bw=120)
        if li >= i_b + 3:
            over(im, text_img("享乐适应", "serif", 84, MIST, shadow=6), (W // 2, 1060), fade_in(ctx, i_b + 3))
        if li >= i_b + 4:
            over(im, text_img("一 · 对比：见过大喜，小乐就淡了", "serif", 46, MIST, shadow=4), (W // 2, 1180), fade_in(ctx, i_b + 4))
        if li >= i_b + 5:
            over(im, text_img("二 · 习惯：新的快乐，成了新的平常", "serif", 46, MIST, shadow=4), (W // 2, 1260), fade_in(ctx, i_b + 5))
    if fading:
        i_s = next((i for i, s in enumerate(says) if "瑞典" in s), None)
        if i_s is not None and i_s <= li <= i_s + 2:
            k = fade_in(ctx, i_s)
            panel = Image.new("RGBA", (W, 560), (10, 10, 14, 210))
            im.alpha_composite(with_alpha(panel, k), (0, 330))
            over(im, text_img("Lindqvist, Östling & Cesarini\nReview of Economic Studies 2020 · 预先登记", "sans", 32, GREY), (W // 2, 410), k)
            over(im, text_img("瑞典 3,362 位彩票玩家 · 中奖后 5–22 年", "serif", 44, MIST, shadow=3), (W // 2, 520), k)
            if li >= i_s + 1:
                over(im, text_img("生活满意度：长期更高 ✓", "serif", 52, GOLD, shadow=3), (W // 2, 650), fade_in(ctx, i_s + 1))
            if li >= i_s + 2:
                over(im, text_img("日常快乐 · 心理健康：无显著差别", "serif", 48, (190, 180, 170), shadow=3), (W // 2, 760), fade_in(ctx, i_s + 2))
        if "小样本" in cur:
            over(im, text_img("小样本：22 人", "serif", 70, (230, 160, 90), shadow=5), (W // 2, 420), fade_in(ctx, li))
        if "不过如此" in cur:
            over(im, text_img("有了之后，也不过如此", "serif", 64, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
    return im


def v_feast_fade(ctx):
    return v_feast(ctx, fading=True)


# ---------------------------------------------------------------- 阿修罗
def v_asura(ctx):
    t, li = ctx["t"], ctx["li"]
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    im = ink_bg(9).copy()
    over(im, glow(560, (170, 50, 36), 2.0, 0.45 + 0.08 * math.sin(t * 2.2)), (W // 2, 1100))
    d = ImageDraw.Draw(im)
    lean = 10 * math.sin(t * 1.7)
    draw_figure(d, 250 + lean, 1400, 520, (6, 6, 8), "stand")
    draw_figure(d, 830 - lean, 1400, 540, (6, 6, 8), "stand")
    # 尺子
    y = 1060
    d.rectangle((330, y - 16, 750, y + 16), fill=(200, 170, 110))
    for k in range(22):
        x = 340 + k * 19
        d.line((x, y - 16, x, y - 16 + (14 if k % 5 else 26)), fill=(60, 40, 20), width=2)
    i_c = next(i for i, s in enumerate(says) if "工资" in s and "加州" in s)
    if "费斯廷格" in cur:
        over(im, text_img("社会比较理论", "serif", 80, MIST, shadow=5), (W // 2, 430), fade_in(ctx, li))
        over(im, text_img("Festinger, Human Relations, 1954", "serif", 34, GREY), (W // 2, 520), fade_in(ctx, li))
    if "类比" in cur:
        over(im, text_img("类 比", "serif", 96, (150, 170, 200), shadow=5), (W // 2, 430), fade_in(ctx, li))
    if i_c <= li <= i_c + 2:
        k = fade_in(ctx, i_c)
        over(im, text_img("Card, Mas, Moretti & Saez, AER 2012\n加州大学员工 · 可查同事工资之后", "sans", 32, GREY), (W // 2, 390), k)
        if li >= i_c + 1:
            k2 = fade_in(ctx, i_c + 1)
            over(im, text_img("低于中位数：满意度 ↓  想换工作 ↑", "serif", 52, (240, 140, 110), shadow=4), (W // 2, 560), k2)
            over(im, text_img("高于中位数：没有变化", "serif", 52, MIST, shadow=4), (W // 2, 650), ease(since(ctx, i_c + 1) / 0.6 - 2.5))
        if li >= i_c + 2:
            over(im, text_img("只带来失去，不带来得到", "serif", 56, GOLD, shadow=4), (W // 2, 780), fade_in(ctx, i_c + 2))
    if "跑步机" in cur:
        cx, cy, r = W // 2, 640, 170
        a0 = (t * 160) % 360
        d = ImageDraw.Draw(im)
        d.arc((cx - r, cy - r, cx + r, cy + r), a0, a0 + 300, fill=(230, 120, 90), width=10)
        over(im, text_img("越比越要比", "serif", 50, MIST, shadow=3), (cx, cy), fade_in(ctx, li))
    if "赢了不安心" in cur:
        over(im, text_img("赢了不安心\n输了不甘心", "ukai", 92, (230, 150, 120), shadow=6), (W // 2, 560), fade_in(ctx, li))
    return im


# ---------------------------------------------------------------- 畜生 / 人
def lamp(im, t, a=1.0):
    cx, cy = W // 2, 900
    fl = 1 + 0.06 * math.sin(t * 9) + 0.04 * math.sin(t * 13.7)
    over(im, glow(int(480 * fl), (255, 190, 110), 2.0, 0.55 * a), (cx, cy - 80))
    d = ImageDraw.Draw(im)
    d.polygon([(cx - 110, cy + 20), (cx + 110, cy + 20), (cx + 60, cy + 80), (cx - 60, cy + 80)], fill=(70, 50, 34))
    d.rectangle((cx - 16, cy + 80, cx + 16, cy + 240), fill=(60, 44, 30))
    d.ellipse((cx - 90, cy + 230, cx + 90, cy + 270), fill=(60, 44, 30))
    fh = 110 * fl
    d.polygon([(cx, cy - fh), (cx + 26, cy - 20), (cx, cy + 10), (cx - 26, cy - 20)], fill=(255, 220, 150))
    d.polygon([(cx, cy - fh * 0.55), (cx + 11, cy - 16), (cx, cy + 2), (cx - 11, cy - 16)], fill=(255, 250, 225))


def v_human(ctx):
    t, li = ctx["t"], ctx["li"]
    l = ctx["lines"][li]
    cur = l["say"]
    im = ink_bg(10).copy()
    if l.get("beat") == "auto":
        cx, cy = W // 2, 900
        over(im, glow(220, (110, 160, 240), 1.6, 0.6), (cx + 60, cy - 40))
        d = ImageDraw.Draw(im)
        draw_figure(d, cx, 1330, 620, (8, 8, 10), "sit")
        d.rounded_rectangle((cx + 40, cy - 110, cx + 100, cy - 10), 10, fill=(170, 210, 255))
        for i in range(3):
            r = 230 + i * 70
            a0 = (t * (90 - i * 20) + i * 100) % 360
            d.arc((cx - r, cy - 150 - r * 0.5, cx + r, cy - 150 + r * 0.5), a0, a0 + 250, fill=(110, 150, 220), width=5)
        over(im, text_img("自动驾驶", "serif", 80, (150, 190, 240), shadow=5), (W // 2, 400), 1.0)
        if "替我们做完" in cur:
            over(im, text_img("没有被觉察的习惯，替我们做决定", "serif", 46, MIST, shadow=4), (W // 2, 500), fade_in(ctx, li))
    else:
        lamp(im, t)
        k = since(ctx, li)
        if "苦乐参半" in cur:
            d = ImageDraw.Draw(im)
            tilt = 0.08 * math.sin(t * 1.2)
            cx, cy = W // 2, 470
            d.line((cx - 300 * math.cos(tilt), cy - 300 * math.sin(tilt), cx + 300 * math.cos(tilt), cy + 300 * math.sin(tilt)), fill=GOLD, width=5)
            for s, lab in ((-1, "苦"), (1, "乐")):
                px, py = cx + s * 300 * math.cos(tilt), cy + s * 300 * math.sin(tilt)
                d.line((px, py, px, py + 90), fill=GOLD, width=3)
                d.arc((px - 80, py + 50, px + 80, py + 130), 0, 180, fill=GOLD, width=5)
                over(im, text_img(lab, "ukai", 64, MIST), (px, py + 60))
        if "最后是人道" in cur:
            over(im, text_img("人道", "ukai", 150, (226, 170, 110), shadow=6), (W // 2, 430), fade_in(ctx, li))
        if "最适合修行" in cur:
            over(im, text_img("人道 · 最适合修行", "serif", 66, MIST, shadow=5), (W // 2, 430), fade_in(ctx, li))
        if "余力" in cur:
            chips(im, ["有苦，所以想出离", "有乐，所以有余力"], 380, [ease(k / 0.5), ease((k - 1.4) / 0.5)], 54)
    return im


# ---------------------------------------------------------------- 边界
def v_bounds(ctx):
    t, li = ctx["t"], ctx["li"]
    im = ink_bg(11).copy()
    over(im, enso(480, 40, GOLD, seed=12, alpha=0.18), (W // 2, CY))
    items = [("一", "印照 · 类比", "不是证明，也不是否证"), ("二", "研究各有局限", "动物实验 · 小样本 · 复现争议"),
             ("三", "境由心造", "≠ 苦都是自己想出来的")]
    beats = [l.get("beat") for l in ctx["lines"]]
    for j, (n, a, b) in enumerate(items):
        first = next((i for i, x in enumerate(beats) if x == j + 1), None)
        if first is None or li < first:
            continue
        k = ease(since(ctx, first) / 0.7)
        y = 440 + j * 290
        active = beats[li] == j + 1
        panel = Image.new("RGBA", (900, 230), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle((0, 0, 899, 229), 18, fill=(20, 20, 26, 230), outline=(GOLD if active else (80, 76, 70)) + (255,), width=3)
        over(panel, text_img(n, "ukai", 110, VERM if active else (120, 70, 60)), (100, 115))
        over(panel, text_img(a, "serif", 58, MIST if active else GREY), (180, 70), anchor="lm")
        over(panel, text_img(b, "sans", 40, (210, 200, 180) if active else (120, 116, 110)), (182, 155), anchor="lm")
        over(im, panel, (W // 2, y + 20 * (1 - k)), k)
    cur = ctx["lines"][li]["say"]
    if "一只手" in cur or "可以练" in cur:
        k = ease(since(ctx, li) / 2.0) if "一只手" in cur else 1.0
        d = ImageDraw.Draw(im)
        x = lerp(W + 40, 700, k)
        y = 1340
        d.rounded_rectangle((x, y - 34, x + 420, y + 34), 30, fill=(210, 180, 150))
        for i in range(4):
            d.rounded_rectangle((x - 70 + i * 6, y - 34 + i * 17, x + 20, y - 18 + i * 17), 8, fill=(210, 180, 150))
        over(im, glow(150, (255, 220, 170), 2, 0.5 * k), (x - 40, y))
    if "冷漠" in cur:
        over(im, text_img("「想开就好」", "serif", 60, (200, 120, 100), shadow=4), (W // 2, 1340), fade_in(ctx, li))
    return im


# ---------------------------------------------------------------- 收束：深夜街头伸手
DOORS = [("地狱", "一点控制感"), ("饿鬼", "一点带宽"), ("天", "珍惜已有"), ("阿修罗", "放下尺子"), ("畜生", "看见习惯"), ("人", "看见所有门")]


def v_night_hand(ctx):
    t, li, dur = ctx["t"], ctx["li"], ctx["dur"]
    says = [l["say"] for l in ctx["lines"]]
    cur = says[li]
    im = street(1.0, t + 40, dim=0.25, walkers=False)
    d = ImageDraw.Draw(im)
    i_hand = next(i for i, s in enumerate(says) if "伸过来的一只手" in s)
    i_doors = next(i for i, s in enumerate(says) if "各有一扇门" in s)
    i_last = next(i for i, s in enumerate(says) if "不必先问" in s)
    # 两个人
    sitter_x = 380
    draw_figure(d, sitter_x, 1398, 300, (4, 4, 6), "curl")
    k = ease((t - line_start(ctx, i_hand) + 0.5) / 3.0) if li >= i_hand else 0.0
    wx = lerp(W + 120, 640, ease((t - line_start(ctx, max(0, i_hand - 1))) / 4.0)) if li >= i_hand - 1 else W + 200
    draw_figure(d, wx, 1398, 420, (4, 4, 6), "stand")
    if li >= i_hand:
        hx0, hy0 = wx - 30, 1398 - 0.70 * 420
        tx, ty = sitter_x + 70, 1398 - 0.30 * 300
        hx, hy = lerp(hx0, tx + 30, k), lerp(hy0, ty, k)
        d.line((hx0, hy0, hx, hy), fill=(4, 4, 6), width=22)
        over(im, glow(140, (255, 214, 150), 1.8, 0.75 * k), (hx, hy))
    if "回到开头" in cur or (li in (1, 2)):
        over(im, text_img("孤苦无告、陷入绝望的人\n难道活得比畜生幸福吗？", "serif", 60, MIST, shadow=5), (W // 2, 520), fade_in(ctx, li) if li == 0 else 1.0)
    if "不在地下" in cur:
        over(im, text_img("地狱不在地下\n可能就在一个人的心里", "serif", 66, (230, 160, 130), shadow=5), (W // 2, 520), fade_in(ctx, li))
    if "此时此地" in cur:
        over(im, text_img("不是来世的故事\n是此时此地的提醒", "serif", 64, MIST, shadow=5), (W // 2, 520), fade_in(ctx, li))
    if "出路，也可以在心里" in cur:
        over(im, text_img("出路，也在心里", "serif", 72, GOLD, shadow=5), (W // 2, 520), fade_in(ctx, li))
    if "第一次" in cur:
        over(im, text_img("你伸出的手\n也许是别人的第一次", "serif", 66, GOLD, shadow=5), (W // 2, 520), fade_in(ctx, li))
    if i_doors <= li < i_last:
        panel = Image.new("RGBA", (W, 760), (8, 8, 12, 215))
        kk = fade_in(ctx, i_doors)
        im.alpha_composite(with_alpha(panel, kk), (0, 300))
        for j, (n, ex) in enumerate(DOORS):
            col = FACE_COL[n]
            x = 200 + (j % 3) * 340
            y = 470 + (j // 3) * 330
            show = clamp01((li - i_doors) / 1.0)
            idx_line = i_doors + 1 + (j // 2) if j < 4 else i_doors + 3
            a = kk if li < i_doors + 1 else (1.0 if li >= idx_line else 0.45)
            dd = ImageDraw.Draw(im)
            open_k = ease(since(ctx, idx_line) / 1.0) if li >= idx_line else 0
            dd.rectangle((x - 70, y - 120, x + 70, y + 80), fill=mixc((20, 20, 24), (255, 230, 180), 0.75 * open_k), outline=col, width=4)
            dd.polygon([(x - 70, y - 120), (x - 70 + 140 * (1 - open_k * 0.8), y - 110), (x - 70 + 140 * (1 - open_k * 0.8), y + 75), (x - 70, y + 80)], fill=(30, 28, 26))
            over(im, text_img(n, "ukai", 48, col), (x, y + 125), a * kk)
            over(im, text_img(ex, "sans", 32, MIST), (x, y + 180), open_k)
    if li >= i_last:
        over(im, text_img("能走进去\n也就能走出来", "ukai", 96, GOLD, shadow=6), (W // 2, 560), fade_in(ctx, i_last + 1) if li > i_last else 0)
        if li == i_last:
            over(im, text_img("先看看自己此刻的心\n落在哪一道", "serif", 64, MIST, shadow=5), (W // 2, 560), fade_in(ctx, li))
    return im


# ---------------------------------------------------------------- 钩子之后的预告
def v_tease(ctx):
    t, li = ctx["t"], ctx["li"]
    l = ctx["lines"][li]
    beat = l.get("beat")
    k = since(ctx, li)
    if beat == "door":
        im = room(t + 5, door_open=0.0)
        over(im, text_img("门没锁，却不再去推", "serif", 66, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
    elif beat == "tunnel":
        sub = dict(ctx, t=k, dur=6, lines=[dict(say="", start=0, end=6)], li=0)
        im = v_tunnel(sub)
        over(im, text_img("越缺什么，眼里越只剩什么", "serif", 62, MIST, shadow=5), (W // 2, 420), fade_in(ctx, li))
    elif beat == "feast":
        im = feast_base(int(round(clamp01(k / 5) * 6))).copy()
        for j in range(9):
            x = 120 + j * 105
            over(im, glow(110, (255, 170, 90), 1.8, 0.6 * (1 - clamp01(k / 5) * 0.6)), (x, 470))
        over(im, text_img("中了大奖，快乐没多出多少", "serif", 62, MIST, shadow=5), (W // 2, 380), fade_in(ctx, li))
    elif beat == "mirror":
        im = ink_bg(12).copy()
        off = 250
        over(im, enso(220, 30, GOLD, seed=4, alpha=0.9), (W // 2 - off, CY))
        over(im, enso(220, 30, (160, 190, 220), seed=6, alpha=0.9), (W // 2 + off, CY))
        over(im, text_img("佛学", "ukai", 80, GOLD), (W // 2 - off, CY))
        over(im, text_img("心理学", "serif", 64, (170, 200, 230)), (W // 2 + off, CY))
        ph = (t * 0.6) % 1
        over(im, glow(60, MIST, 1.2, 0.8), (lerp(W // 2 - off + 140, W // 2 + off - 140, ph), CY))
        over(im, text_img("印照，不是证明", "serif", 84, MIST, shadow=6), (W // 2, 1180), 1.0)
    elif beat == "q":
        im = street(0.97, t + 30, dim=0.6, walkers=False)
        d = ImageDraw.Draw(im)
        draw_figure(d, W // 2, 1398, 330, (4, 4, 6), "curl")
        if "最后回答" in l["say"]:
            over(im, text_img("最后，回答一个问题", "serif", 60, GREY, shadow=4), (W // 2, 520), fade_in(ctx, li))
        else:
            over(im, text_img("就算没有真的畜生道", "serif", 64, MIST, shadow=5), (W // 2, 480), 1.0 if "孤苦" in l["say"] else fade_in(ctx, li))
            if "孤苦" in l["say"]:
                over(im, text_img("孤苦无告、陷入绝望的人\n难道就活得比畜生幸福吗？", "ukai", 70, GOLD, shadow=6), (W // 2, 700), fade_in(ctx, li))
    else:
        im = ink_bg(1).copy()
        over(im, enso(420, 56, GOLD, seed=3, alpha=0.9), (W // 2, CY))
        over(im, glow(300, GOLD, 2.4, 0.25), (W // 2, CY))
        if li == 0:
            over(im, text_img("一念\n三千", "ukai", 150, (250, 236, 200), shadow=6), (W // 2, CY), fade_in(ctx, li, 1.0))
            over(im, text_img("天台宗 · 智者大师（538–597）", "serif", 40, GREY), (W // 2, 1390), fade_in(ctx, li))
        else:
            over(im, text_img("心理学实验室里\n相似的风景", "serif", 72, MIST, shadow=5), (W // 2, CY), fade_in(ctx, li))
    return im


VISUALS = {
    "street_open": v_street_open, "day_six": v_day_six, "tease": v_tease, "ten_realms": v_ten_realms,
    "quote": v_quote, "ten_realms_turn": v_ten_realms_turn, "hell_room": v_hell_room, "hell_brain": v_hell_brain,
    "hell_door": v_hell_door, "tunnel": v_tunnel, "cane": v_cane, "tunnel_soft": v_tunnel_soft, "feast": v_feast,
    "feast_fade": v_feast_fade, "asura": v_asura, "human": v_human, "bounds": v_bounds, "night_hand": v_night_hand,
    "quote_end": v_quote_end,
}
