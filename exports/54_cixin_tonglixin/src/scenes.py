# -*- coding: utf-8 -*-
"""各场景。每个场景：make(ctx) -> (theme, frame_fn)；frame_fn(t) 返回 RGBA 全幅图。
ctx: dur（秒）, lt（本场景各句开始的本地时间列表）。theme: 'dark' | 'light'（决定字幕配色）。"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *

ART_TOP, ART_BOT = 330, 1330   # 主画面区


def L_at(ctx, i, default=0.0):
    lt = ctx["lt"]
    return lt[i] if i < len(lt) else default


def push(img, t, dur, z0=1.0, z1=1.06, cx=0.5, cy=0.5):
    """缓慢推镜：对整幅 RGBA 图做缩放裁切。"""
    z = z0 + (z1 - z0) * (t / max(dur, 1e-3))
    if abs(z - 1) < 1e-3:
        return img
    w, h = int(W * z), int(H * z)
    im = img.resize((w, h), Image.BILINEAR)
    x0 = int((w - W) * cx); y0 = int((h - H) * cy)
    return im.crop((x0, y0, x0 + W, y0 + H))


def card_title(lay, s, y, size=58, color=INK, kind="serif", wght=700, maxw=900):
    t, h = text_layer(s, font(kind, size, wght), color, maxw=maxw, y=y)
    return Image.alpha_composite(lay, t), h


# =============== 钩子：夜医院走廊 ===============
def corridor_static():
    img = night_bg(5, (8, 12, 20), (18, 24, 34)).convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    vx, vy = W * 0.5, H * 0.40   # 消失点
    # 墙、地、天花板（透视）
    d.polygon([(0, 260), (vx - 90, vy - 70), (vx - 90, vy + 90), (0, 1560)], fill=(30, 38, 52, 255))
    d.polygon([(W, 260), (vx + 90, vy - 70), (vx + 90, vy + 90), (W, 1560)], fill=(26, 33, 46, 255))
    d.polygon([(0, 1560), (vx - 90, vy + 90), (vx + 90, vy + 90), (W, 1560)], fill=(36, 44, 56, 255))
    d.polygon([(0, 260), (vx - 90, vy - 70), (vx + 90, vy - 70), (W, 260)], fill=(20, 26, 36, 255))
    d.rectangle((vx - 90, vy - 70, vx + 90, vy + 90), fill=(60, 74, 88, 255))
    # 尽头门缝光
    d.rectangle((vx - 22, vy - 40, vx + 22, vy + 90), fill=(170, 190, 196, 255))
    # 地面反光线
    for k in range(9):
        u = k / 9
        y = vy + 90 + (1560 - vy - 90) * (u ** 1.8)
        x0 = vx - 90 - (vx - 90) * (u ** 1.8)
        d.line([(x0, y), (W - x0, y)], fill=(255, 255, 255, 10), width=2)
    # 两侧门框
    for k in range(4):
        u = 0.15 + k * 0.2
        def P(side, yy):
            x = (vx - 90) * (u ** 1.3) if side < 0 else W - (W - vx - 90) * (u ** 1.3)
            return x
        for side in (-1, 1):
            x = P(side, 0)
            top = 260 + (vy - 70 - 260) * (u ** 1.3) + 40
            bot = 1560 + (vy + 90 - 1560) * (u ** 1.3)
            w = 70 * (1 - u ** 1.3) + 10
            xs = x + (w if side < 0 else -w)
            d.polygon([(x, top), (xs, top + 8), (xs, bot - 6), (x, bot)], fill=(18, 24, 34, 255))
    # 天花板灯（发光）
    glowl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k in range(6):
        u = (k / 6) ** 1.6
        y = 260 + (vy - 70 - 260) * u + 10
        w = 300 * (1 - u) + 20
        g = glow(int(w * 1.6) + 2, (190, 215, 225), w * 0.5, 0.55)
        glowl.alpha_composite(g, (int(vx - g.size[0] / 2), int(y - g.size[1] / 2)))
        ImageDraw.Draw(glowl).rectangle((vx - w / 2, y - 5 * (1 - u) - 2, vx + w / 2, y + 5 * (1 - u) + 2), fill=(225, 238, 240, 230))
    img = Image.alpha_composite(img, glowl)
    return img


def nurse_layer():
    """靠墙闭眼的护士剪影（右侧墙前，侧身）。"""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    x, y = 700, 760   # 头部位置
    # 头：侧脸，下巴微抬，头靠墙
    d.ellipse((x - 62, y - 76, x + 62, y + 70), fill=255)
    d.polygon([(x - 58, y - 10), (x - 82, y + 18), (x - 66, y + 30), (x - 60, y + 52), (x - 40, y + 70)], fill=255)   # 鼻、唇、下巴
    d.ellipse((x + 20, y - 70, x + 98, y + 6), fill=255)   # 发髻
    # 颈
    d.polygon([(x - 30, y + 50), (x + 30, y + 40), (x + 40, y + 120), (x - 20, y + 130)], fill=255)
    # 身体：微微后靠
    body = [(x - 120, y + 140), (x + 80, y + 110), (x + 120, y + 260), (x + 135, y + 560), (x + 150, y + 820),
            (x - 120, y + 830), (x - 110, y + 560), (x - 150, y + 300)]
    d.polygon(body, fill=255)
    d.ellipse((x - 160, y + 110, x + 0, y + 240), fill=255)   # 肩
    # 手臂垂下
    d.polygon([(x - 150, y + 200), (x - 110, y + 190), (x - 80, y + 520), (x - 120, y + 530)], fill=255)
    # 腿
    d.polygon([(x - 100, y + 820), (x - 10, y + 820), (x - 20, y + 1080), (x - 80, y + 1080)], fill=255)
    d.polygon([(x + 10, y + 820), (x + 130, y + 820), (x + 120, y + 1070), (x + 50, y + 1075)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(1.6))
    lay = Image.new("RGBA", (W, H), (9, 12, 18, 0))
    lay.putalpha(m)
    # 轮廓光（来自走廊尽头）
    rim = m.filter(ImageFilter.GaussianBlur(5))
    edge = Image.fromarray(np.clip(np.array(rim, np.int16) - np.array(m.filter(ImageFilter.GaussianBlur(0.5)), np.int16) * 0.0, 0, 255).astype(np.uint8))
    rl = Image.new("RGBA", (W, H), (120, 150, 170, 0))
    sh = np.array(m, np.float32)
    shifted = np.roll(sh, -4, axis=1)
    edge = np.clip(sh - shifted, 0, 255) * 0.9
    rl.putalpha(Image.fromarray(edge.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)))
    return Image.alpha_composite(lay, rl)


def make_hook(ctx):
    base = corridor_static()
    nurse = nurse_layer()
    base = Image.alpha_composite(base, nurse)
    # 题目（首帧即有）
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle((0, 330, W, 640), fill=(6, 9, 14, 150))
    base = Image.alpha_composite(base, band.filter(ImageFilter.GaussianBlur(40)))
    title, _ = text_layer("太能共情的人，\n为什么最容易累垮？", font("serif", 84, 800), (244, 240, 230), maxw=980, y=380, spacing=1.32, shadow=(0, 0, 0, 200))
    dur = ctx["dur"]

    def fr(t):
        im = push(base, t, dur + 2, 1.0, 1.05, 0.62, 0.45)
        # 灯光轻微闪烁
        fl = 0.04 * math.sin(t * 13) * math.sin(t * 3.1)
        if fl > 0.02:
            im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)), fl)
        return Image.alpha_composite(im, title)
    return "dark", fr


# =============== 两套网络（交替亮） ===============
REG = {  # 内侧面示意坐标（相对 cx, cy, s）
    "aMCC": (-0.12, -0.33, 0.20, 0.10, -0.15),
    "AI": (-0.40, 0.10, 0.14, 0.09, 0.0),
    "pgACC": (-0.55, -0.02, 0.12, 0.10, 0.5),
    "mOFC": (-0.66, 0.28, 0.18, 0.09, 0.2),
    "VS": (-0.30, 0.22, 0.11, 0.08, 0.0),
}


def region_layer(cx, cy, s, keys, color, strength=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k in keys:
        dx, dy, rx, ry, rot = REG[k]
        lay = Image.alpha_composite(lay, blob(cx + dx * s, cy + dy * s, rx * s, ry * s, color, strength, rot))
    return lay


def make_brain2(ctx):
    cx, cy, s = 560, 820, 400
    bg = night_bg(7).convert("RGBA")
    br = brain_base(cx, cy, s, "medial", True)
    base = Image.alpha_composite(bg, br)
    warm = region_layer(cx, cy, s, ["aMCC", "AI"], WARM, 1.0)
    cool = region_layer(cx, cy, s, ["pgACC", "mOFC", "VS"], COOL, 1.0)
    f = font("sans", 40, 600)
    lw = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lw.alpha_composite(text_layer("难受 · 退缩", f, WARM + (255,), y=1170, x=300)[0])
    lc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lc.alpha_composite(text_layer("温暖 · 伸手", f, COOL + (255,), y=1170, x=780)[0])
    note = text_layer("脑区位置为示意", font("sans", 28, 400), (170, 176, 190, 255), y=1250)[0]
    t1 = L_at(ctx, 1, ctx["dur"] / 2)

    def fr(t):
        im = base.copy()
        # 0~t1：交替；t1 之后：左右各自对应文字
        ph = 0.5 + 0.5 * math.sin(t * 2.4)
        im = over(im, warm, 0.25 + 0.75 * ph)
        im = over(im, cool, 0.25 + 0.75 * (1 - ph))
        im = over(im, lw, ramp(t, t1, .5))
        im = over(im, lc, ramp(t, t1 + 1.2, .5))
        im = over(im, note, 0.9)
        return im
    return "dark", fr


# =============== 助人职业与倦怠 ===============
def make_burnout(ctx):
    bg = night_bg(9, (12, 16, 24), (24, 30, 40)).convert("RGBA")
    roles = ["医生", "护士", "心理咨询师"]
    lays = []
    for i, r in enumerate(roles):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        x = 220 + i * 320
        # 简化人物：头 + 肩
        d.ellipse((x - 55, 560, x + 55, 670), fill=(196, 204, 214, 255))
        d.pieslice((x - 120, 690, x + 120, 930), 180, 360, fill=(196, 204, 214, 255))
        d.rectangle((x - 120, 810, x + 120, 900), fill=(196, 204, 214, 255))
        f = font("sans", 44, 600)
        tw, _ = text_size(r, f)
        d.text((x - tw / 2, 940), r, font=f, fill=(236, 232, 222, 255))
        lays.append(lay)
    # 电量/疲惫条
    t2 = L_at(ctx, 1, 4); t3 = L_at(ctx, 2, 8)
    quote = text_layer("“Physicians … have a high prevalence rate of burnout.”", font("serif", 36, 500), (214, 206, 190, 255), maxw=900, y=1060)[0]
    src = text_layer("Klimecki, Leiberg, Ricard & Singer, 2014", font("sans", 28, 400), (160, 166, 178, 255), y=1180)[0]
    word, _ = text_layer("同情疲劳", font("serif", 120, 800), (236, 232, 222, 255), y=1030)
    word_en = text_layer("compassion fatigue", font("serif", 40, 400), (170, 176, 190, 255), y=1200)[0]

    def fr(t):
        im = bg.copy()
        for i, l in enumerate(lays):
            a = ramp(t, i * 0.45, .5)
            # 逐渐暗淡（疲惫）
            dim = 1 - 0.45 * ramp(t, t2, 2.0)
            im = over(im, l, a * dim)
        if t < t3:
            im = over(im, quote, ramp(t, t2, .5) * (1 - ramp(t, t3 - .4, .4)))
            im = over(im, src, ramp(t, t2 + .3, .5) * (1 - ramp(t, t3 - .4, .4)))
        else:
            im = over(im, word, ramp(t, t3, .5))
            im = over(im, word_en, ramp(t, t3 + .3, .5))
        return im
    return "dark", fr


# =============== 名字叫错了 + 三件事 ===============
def make_rename(ctx):
    bg = paper(11).convert("RGBA")
    t1 = L_at(ctx, 1, 4); t2 = L_at(ctx, 2, 8)
    old, _ = text_layer("同情疲劳", font("serif", 110, 800), INK + (255,), y=560)
    old_en = text_layer("compassion fatigue", font("serif", 38, 400), INK_SOFT + (255,), y=700)[0]
    new, _ = text_layer("共情痛苦疲劳", font("serif", 110, 800), WARM + (255,), y=820)
    new_en = text_layer("empathic distress fatigue", font("serif", 38, 400), INK_SOFT + (255,), y=960)[0]
    src = text_layer("Klimecki & Singer (2012). Empathic Distress Fatigue Rather Than Compassion Fatigue? 载于 Pathological Altruism, 牛津大学出版社", font("sans", 26, 400), INK_SOFT + (255,), y=1040, maxw=900)[0]
    strike = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    items = ["一  两条路，有什么不同", "二  能不能练", "三  证据到哪里为止"]
    lst = []
    for i, s in enumerate(items):
        lst.append(text_layer(s, font("serif", 62, 700), INK + (255,), y=560 + i * 160, x=200, align="left")[0])

    def fr(t):
        im = bg.copy()
        if t < t2:
            im = over(im, old, ramp(t, 0, .4))
            im = over(im, old_en, ramp(t, .2, .4))
            p = ramp(t, 1.4, .6)
            if p > 0:
                s2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(s2).line([(290, 625), (290 + 500 * p, 615)], fill=SEAL + (230,), width=10)
                im = Image.alpha_composite(im, s2)
            im = over(im, new, ramp(t, t1, .5))
            im = over(im, new_en, ramp(t, t1 + .3, .5))
            im = over(im, src, ramp(t, t1 + .6, .5))
            if t > t2 - .4:
                im = Image.blend(im, bg, ramp(t, t2 - .4, .4))
        else:
            for i, l in enumerate(lst):
                im = over(im, l, ramp(t, t2 + 0.6 + i * 1.6, .5))
        return im
    return "light", fr


# =============== 论文卡片 ===============
def paper_card(title_cn, cite_lines, tag=None, y0=470, bg_seed=13):
    bg = paper(bg_seed).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((90, y0, W - 90, y0 + 700), 18, fill=(250, 247, 240, 235), outline=(150, 140, 125, 255), width=2)
    d.line([(130, y0 + 120), (W - 130, y0 + 120)], fill=(180, 170, 150, 255), width=2)
    lay.alpha_composite(text_layer(title_cn, font("serif", 54, 700), INK + (255,), y=y0 + 38, maxw=840)[0])
    y = y0 + 160
    for s, kind, sz, col in cite_lines:
        tl, h = text_layer(s, font(kind, sz, 500 if kind == "serif" else 400), col + (255,), maxw=820, y=y)
        lay.alpha_composite(tl); y += h + 18
    return bg, lay


def make_exp_intro(ctx):
    bg, card = paper_card("一项对照训练实验", [
        ("Differential pattern of functional brain plasticity after compassion and empathy training", "serif", 40, INK),
        ("O. M. Klimecki, S. Leiberg, M. Ricard & T. Singer", "sans", 34, INK_SOFT),
        ("Social Cognitive and Affective Neuroscience 9(6): 873–879 (2014)", "sans", 32, INK_SOFT),
        ("《社会认知与情感神经科学》", "serif", 40, INK),
    ])
    t1 = L_at(ctx, 1, 1.5)

    def fr(t):
        im = bg.copy()
        k = ramp(t, max(0, t1 - .6), .7)
        card2 = card.transform(card.size, Image.AFFINE, (1, 0, 0, 0, 1, -30 * (1 - k)))
        return over(im, card2, k)
    return "light", fr


def make_exp_design(ctx):
    bg = paper(15).convert("RGBA")
    t1 = L_at(ctx, 1, 2)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fT = font("serif", 46, 700); f = font("sans", 36, 500); fs = font("sans", 30, 400)
    # 时间轴标签
    xs = [170, 400, 620, 860]
    for x, s in zip([300, 520, 760], ["训练前", "第一轮后", "第二轮后"]):
        pass
    rows = [("同理心-慈悲组", "完成 25 人", [("同理心", WARM), ("慈悲", COOL)], 560),
            ("记忆训练对照组", "完成 28 人", [("记忆", (150, 150, 150)), ("记忆", (150, 150, 150))], 900)]
    row_lays = []
    for name, n, blocks, y in rows:
        l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(l)
        dd.text((110, y - 90), name, font=fT, fill=INK)
        dd.text((W - 110 - text_size(n, f)[0], y - 80), n, font=f, fill=INK_SOFT)
        # 扫描点 Pre / Post1 / Post2
        pts = [150, 540, 930]
        for i, x in enumerate(pts):
            dd.ellipse((x - 26, y + 34, x + 26, y + 86), outline=INK, width=4, fill=(250, 246, 238))
            dd.text((x - 14, y + 40), "扫", font=font("sans", 26, 600), fill=INK)
        for i, (lbl, col) in enumerate(blocks):
            x0, x1 = pts[i] + 36, pts[i + 1] - 36
            dd.rounded_rectangle((x0, y + 30, x1, y + 90), 12, fill=col + (235,))
            tw, _ = text_size(lbl, f)
            dd.text(((x0 + x1) / 2 - tw / 2, y + 36), lbl, font=f, fill=(255, 252, 245))
        row_lays.append(l)
    foot = text_layer("全部为女性参与者 · 两组先后招募", font("sans", 34, 500), INK_SOFT + (255,), y=1170)[0]
    legend = text_layer("“扫” = 核磁共振扫描 + 情绪自评", font("sans", 28, 400), INK_SOFT + (255,), y=1240)[0]

    def fr(t):
        im = bg.copy()
        im = over(im, row_lays[0], ramp(t, 0.3, .6))
        im = over(im, row_lays[1], ramp(t, min(t1 + 1.4, 1.6), .6))
        im = over(im, foot, ramp(t, 0.3, .6))
        im = over(im, legend, ramp(t, t1 + 2.5, .6))
        return im
    return "light", fr


def make_exp_video(ctx):
    bg = night_bg(17, (14, 18, 26), (26, 32, 42)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # 扫描仪（侧视）：环形机架 + 检查床 + 平躺的人
    d.rounded_rectangle((330, 640, 690, 960), 60, fill=(44, 52, 66, 255), outline=(190, 198, 210, 255), width=8)
    d.ellipse((410, 700, 610, 900), fill=(14, 18, 26, 255), outline=(150, 160, 176, 255), width=4)
    d.rectangle((120, 860, 960, 884), fill=(150, 158, 170, 255))
    d.rectangle((200, 884, 240, 980), fill=(110, 118, 130, 255)); d.rectangle((840, 884, 880, 980), fill=(110, 118, 130, 255))
    d.ellipse((470, 800, 524, 852), fill=(196, 204, 214, 255))   # 头（在孔内）
    d.rounded_rectangle((520, 812, 900, 852), 18, fill=(196, 204, 214, 255))
    # 屏幕（上方）
    scr = (360, 440, 720, 620)
    d.rounded_rectangle(scr, 14, fill=(28, 34, 44, 255), outline=(150, 160, 176, 255), width=3)
    d.line([(540, 620), (540, 700)], fill=(110, 118, 130, 255), width=3)
    lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(lay2)
    f = font("sans", 34, 500)
    d2.text((740, 510), "短片\n10–18 秒", font=f, fill=(214, 220, 228))
    t1 = L_at(ctx, 1, 3); t2 = L_at(ctx, 2, 6)
    sub = text_layer("新闻 / 纪录片：受伤、天灾", font("sans", 34, 500), (214, 220, 228, 255), y=1000)[0]
    sliders = []
    for i, (lbl, col) in enumerate([("感同身受", (200, 200, 210)), ("积极情绪", COOL), ("消极情绪", WARM)]):
        l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(l)
        y = 1080 + i * 80
        dd.text((130, y - 4), lbl, font=f, fill=(226, 230, 236))
        dd.rounded_rectangle((340, y + 10, 940, y + 26), 8, fill=(70, 78, 92))
        sliders.append((l, y, col))

    def fr(t):
        im = Image.alpha_composite(bg, lay)
        im = over(im, lay2, 1)
        # 屏幕里闪动的画面（抽象色块）
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ds = ImageDraw.Draw(s)
        ph = int(t / 2.2)
        r = np.random.default_rng(ph)
        for k in range(5):
            x = r.uniform(380, 640); y = r.uniform(455, 560); w = r.uniform(30, 100)
            c = tuple(int(v) for v in r.uniform(60, 150, 3))
            ds.ellipse((x, y, x + w, y + w * 0.6), fill=c + (160,))
        im = Image.alpha_composite(im, s.filter(ImageFilter.GaussianBlur(6)))
        im = over(im, sub, ramp(t, t1, .5))
        for i, (l, y, col) in enumerate(sliders):
            a = ramp(t, t2 + i * 0.5, .5)
            if a <= 0: continue
            im = over(im, l, a)
            v = 0.3 + 0.4 * abs(math.sin(t * 0.9 + i))
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle((340, y + 10, 340 + 600 * v * a, y + 26), 8, fill=col)
            dd.ellipse((340 + 600 * v * a - 16, y + 2, 340 + 600 * v * a + 16, y + 34), fill=(240, 240, 240))
        return im
    return "dark", fr


def make_exp_emp(ctx):
    """同理心训练：自他两圆逐渐重叠，变暖变暗；消极情绪箭头上升。"""
    bg = paper(19).convert("RGBA")
    t1 = L_at(ctx, 1, 3); t2 = L_at(ctx, 2, 5)
    head = text_layer("第一步 · 同理心训练", font("serif", 60, 800), INK + (255,), y=420)[0]
    sub = text_layer("练“共鸣”：真切感受对方的痛苦", font("sans", 38, 500), INK_SOFT + (255,), y=510)[0]
    lab_s = text_layer("我", font("serif", 48, 700), INK + (255,), x=380, y=1150)[0]
    lab_o = text_layer("他人", font("serif", 48, 700), INK + (255,), x=700, y=1150)[0]
    arrow_txt = text_layer("消极情绪 ↑", font("sans", 44, 700), WARM + (255,), y=1240)[0]

    def fr(t):
        im = bg.copy()
        im = over(im, head, ramp(t, 0, .5)); im = over(im, sub, ramp(t, .3, .5))
        k = ramp(t, t1, 3.0)
        sep = 170 - 110 * k
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cy = 850
        col_o = (int(WARM[0]), int(WARM[1]), int(WARM[2]), 120)
        d.ellipse((540 + sep - 200, cy - 200, 540 + sep + 200, cy + 200), fill=col_o, outline=WARM + (255,), width=5)
        col_s = (int(70 + 130 * k), int(70 - 10 * k), int(80 - 20 * k), int(40 + 80 * k))
        d.ellipse((540 - sep - 200, cy - 200, 540 - sep + 200, cy + 200), fill=col_s, outline=INK + (255,), width=5)
        im = Image.alpha_composite(im, lay)
        im = over(im, lab_s, 1); im = over(im, lab_o, 1)
        im = over(im, arrow_txt, ramp(t, t2, .5))
        return im
    return "light", fr


def make_brain_hi(ctx, keys, color, title, labels, tag):
    cx, cy, s = 560, 860, 400
    bg = night_bg(21).convert("RGBA")
    base = Image.alpha_composite(bg, brain_base(cx, cy, s, "medial", True))
    hi = region_layer(cx, cy, s, keys, color, 1.0)
    head = text_layer(title, font("serif", 56, 800), (240, 236, 226, 255), y=420)[0]
    lab = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lab)
    f = font("sans", 36, 600)
    for (k, txt, (lx, ly), left) in labels:
        dx, dy, rx, ry, rot = REG[k]
        label_line(d, (cx + dx * s, cy + dy * s), (lx, ly), txt, f, color, left)
    note = text_layer("脑区位置为示意 · 前脑岛实际位于大脑外侧深部", font("sans", 26, 400), (170, 176, 190, 255), y=1260)[0]

    def fr(t):
        im = base.copy()
        pulse = 0.75 + 0.25 * math.sin(t * 2.2)
        im = over(im, hi, ramp(t, .2, .8) * pulse)
        im = over(im, head, ramp(t, 0, .5))
        im = over(im, lab, ramp(t, .9, .6))
        im = over(im, note, 0.9)
        return im
    return "dark", fr


def make_brain_emp(ctx):
    return make_brain_hi(ctx, ["aMCC", "AI"], WARM, "同理心训练后：增强的区域",
                         [("aMCC", "前扣带中部", (700, 560), True), ("AI", "前脑岛", (150, 1130), True)], "实证")


def make_brain_comp(ctx):
    return make_brain_hi(ctx, ["pgACC", "mOFC", "VS"], COOL, "慈悲训练后：另一组网络",
                         [("pgACC", "膝前扣带回", (110, 600), True), ("mOFC", "内侧眶额皮层", (120, 1160), True),
                          ("VS", "腹侧纹状体", (640, 1140), True)], "实证")


def make_exp_comp(ctx):
    """慈心观：善意由近及远扩展的同心光环。"""
    bg = night_bg(23, (16, 18, 26), (34, 30, 30)).convert("RGBA")
    t1 = L_at(ctx, 1, 2); t2 = L_at(ctx, 2, 8)
    head = text_layer("第二步 · 慈悲训练", font("serif", 60, 800), (244, 238, 226, 255), y=420)[0]
    rings = [("亲近的人", 120), ("陌生人", 230), ("关系不好的人", 330)]
    f = font("sans", 36, 600)
    note = text_layer("短片同样令人难过", font("serif", 44, 700), (244, 238, 226, 255), y=1260)[0]

    def fr(t):
        im = bg.copy()
        im = over(im, head, ramp(t, 0, .5))
        cx, cy = 540, 930
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # 中心光
        core = glow(360, COOL, 90, 0.9 * ramp(t, t1, 1.0))
        g.alpha_composite(core, (cx - 180, cy - 180))
        d = ImageDraw.Draw(g)
        span = max(1.5, (t2 - t1) * 0.9)
        for i, (lbl, r) in enumerate(rings):
            a = ramp(t, t1 + 0.8 + i * span / 3, 0.9)
            if a <= 0: continue
            rr = r * (0.85 + 0.15 * a)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=COOL + (int(200 * a),), width=4)
            tw, _ = text_size(lbl, f)
            d.text((cx - tw / 2, cy - rr - 52), lbl, font=f, fill=(244, 230, 200, int(255 * a)))
        im = Image.alpha_composite(im, g)
        im = over(im, note, ramp(t, t2, .6))
        return im
    return "dark", fr


def make_chart(ctx):
    bg = paper(25).convert("RGBA")
    head = text_layer("看同样的受苦短片 · 情绪自评变化", font("serif", 48, 800), INK + (255,), y=420)[0]
    x0, x1, y0, y1 = 170, 930, 620, 1120
    ax = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ax)
    d.line([(x0, y1), (x1, y1)], fill=INK, width=3)
    d.line([(x0, y0 - 20), (x0, y1)], fill=INK, width=3)
    f = font("sans", 32, 500)
    xs = [x0 + 60, (x0 + x1) / 2, x1 - 60]
    for x, s in zip(xs, ["训练前", "同理心后", "慈悲后"]):
        tw, _ = text_size(s, f); d.text((x - tw / 2, y1 + 18), s, font=f, fill=INK)
    neg = [0.55, 0.30, 0.55]   # y 比例（越小越高）
    pos = [0.62, 0.62, 0.32]
    note = text_layer("示意：只画变化方向（依据论文摘要），非原始数据", font("sans", 26, 400), INK_SOFT + (255,), y=1220)[0]
    lg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lg)
    dl.line([(220, 560), (290, 560)], fill=WARM, width=8); dl.text((305, 538), "消极情绪", font=f, fill=WARM)
    dl.line([(560, 560), (630, 560)], fill=(176, 130, 40), width=8); dl.text((645, 538), "积极情绪", font=f, fill=(176, 130, 40))

    def series(p, vals, col):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        pts = [(x, y0 + (y1 - y0) * v) for x, v in zip(xs, vals)]
        seg = p * 2
        for i in range(2):
            u = max(0, min(1, seg - i))
            if u <= 0: break
            a, b = pts[i], pts[i + 1]
            e = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            dd.line([a, e], fill=col, width=8)
        for i, pt in enumerate(pts):
            if p * 2 >= i - 0.01:
                dd.ellipse((pt[0] - 12, pt[1] - 12, pt[0] + 12, pt[1] + 12), fill=col)
        return lay

    def fr(t):
        im = bg.copy()
        im = over(im, head, ramp(t, 0, .5)); im = over(im, ax, ramp(t, 0, .5)); im = over(im, lg, ramp(t, .2, .5))
        p = ramp(t, 0.4, max(1.0, ctx["dur"] * 0.6))
        im = Image.alpha_composite(im, series(p, neg, WARM))
        im = Image.alpha_composite(im, series(p, pos, (176, 130, 40)))
        im = over(im, note, 1)
        return im
    return "light", fr


def make_k13(ctx):
    bg, card = paper_card("更早的一项研究", [
        ("Functional neural plasticity and associated changes in positive affect after compassion training", "serif", 40, INK),
        ("O. M. Klimecki, S. Leiberg, C. Lamm & T. Singer", "sans", 34, INK_SOFT),
        ("Cerebral Cortex 23(7): 1552–1561 (2013)", "sans", 32, INK_SOFT),
        ("只练慈悲 → 面对他人受苦，积极情绪增加", "serif", 40, (150, 100, 20)),
    ], bg_seed=27)

    def fr(t):
        k = ramp(t, 0, .6)
        return over(bg.copy(), card, k)
    return "light", fr


def quote_card(en, cn, src, dark=False, seed=29):
    bg = (night_bg(seed) if dark else paper(seed)).convert("RGBA")
    fg = (240, 236, 226) if dark else INK
    sub = (170, 176, 190) if dark else INK_SOFT
    q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(q)
    d.text((110, 400), "“", font=font("serif", 200, 700), fill=(SEAL if not dark else COOL) + (200,))
    t_en, h = text_layer(en, font("serif", 46, 500), fg + (255,), maxw=840, y=620, spacing=1.4)
    t_cn, h2 = text_layer(cn, font("serif", 52, 700), fg + (255,), maxw=860, y=640 + h + 60, spacing=1.45)
    t_src = text_layer(src, font("sans", 30, 400), sub + (255,), y=640 + h + 60 + h2 + 40, maxw=900)[0]
    return bg, t_en, t_cn, t_src


def make_quote(ctx, en, cn, src, dark=False, seed=29):
    bg, a, b, c = quote_card(en, cn, src, dark, seed)
    t1 = L_at(ctx, 1, 1.0)

    def fr(t):
        im = bg.copy()
        im = over(im, a, ramp(t, 0.1, .7))
        im = over(im, b, ramp(t, t1 - 0.2, .7))
        im = over(im, c, ramp(t, t1 + 0.3, .7))
        return im
    return ("dark" if dark else "light"), fr


def make_quote_k14(ctx):
    return make_quote(ctx, "We conclude that training compassion may reflect a new coping strategy to overcome empathic distress and strengthen resilience.",
                      "训练慈悲，可能是一种新的应对方式，帮助人克服共情痛苦、增强韧性。",
                      "Klimecki et al., Soc Cogn Affect Neurosci, 2014 · 摘要", False, 31)


def make_quote_sk(ctx):
    return make_quote(ctx, "Compassion is feeling for and not feeling with the other.",
                      "慈悲，是为对方而感受，而不是跟着对方一起感受。",
                      "Singer & Klimecki, “Empathy and compassion”, Current Biology 24(18): R875–R878, 2014", True, 33)


def bullet_card(ctx, head, items, tag=None, dark=False, seed=35, y0=560, gap=None, size=44, timing=None):
    bg = (night_bg(seed) if dark else paper(seed)).convert("RGBA")
    fg = (240, 236, 226) if dark else INK
    h = text_layer(head, font("serif", 58, 800), fg + (255,), y=420, maxw=940)[0]
    lays = []
    y = y0
    for it in items:
        tl, hh = text_layer(it, font("sans", size, 500), fg + (255,), maxw=860, y=y, x=110, align="left", spacing=1.38)
        lays.append(tl); y += hh + (gap if gap is not None else 40)
    tm = timing or [0.6 + i * 1.0 for i in range(len(items))]

    def fr(t):
        im = bg.copy()
        im = over(im, h, ramp(t, 0, .5))
        for l, t0 in zip(lays, tm):
            im = over(im, l, ramp(t, t0, .5))
        return im
    return ("dark" if dark else "light"), fr


def make_caveat1(ctx):
    lt = ctx["lt"]
    return bullet_card(ctx, "这是一项小研究", [
        "· 完成者：同理心-慈悲组 25 人，记忆对照组 28 人",
        "· 全部为女性，平均年龄二十多岁",
        "· 两组先后招募，不是同时随机分组",
        "· 两种训练按固定顺序进行",
        "→ 一个值得重视的模式，还不是定论"],
        timing=[L_at(ctx, 1, 1), L_at(ctx, 1, 1) + 3.5, L_at(ctx, 2, 6), L_at(ctx, 2, 6) + 2.8, L_at(ctx, 3, 9)], seed=37, size=42)


# =============== 区分：自他界线 ===============
def make_define(ctx):
    bg = paper(39).convert("RGBA")
    t = ctx["lt"]
    tA = L_at(ctx, 2, 4); tB = L_at(ctx, 3, 7); tC = L_at(ctx, 4, 10); tD = L_at(ctx, 5, 13)
    head = text_layer("同理心 empathy：分享他人的感受", font("serif", 50, 800), INK + (255,), y=420, maxw=960)[0]
    src = text_layer("Singer & Klimecki, Current Biology, 2014", font("sans", 28, 400), INK_SOFT + (255,), y=500)[0]
    f = font("serif", 44, 700)
    lbl_boundary = text_layer("自他分明", font("serif", 46, 700), (60, 120, 100, 255), y=1180)[0]
    lbl_blur = text_layer("界线模糊 → 苦压到自己身上", font("serif", 46, 700), WARM + (255,), y=1180)[0]
    lbl_cont = text_layer("分不清是谁的疼 = 情绪传染", font("serif", 46, 700), INK_SOFT + (255,), y=1180)[0]

    def fr(tt):
        im = bg.copy()
        im = over(im, head, ramp(tt, 0, .5)); im = over(im, src, ramp(tt, .3, .5))
        # 两圆：我 / 他人
        if tt < tC:
            k = 0.0
        else:
            k = ramp(tt, tC, 2.0)
        if tt >= tD - 0.01 and False:
            pass
        sep = 190 - 120 * k
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cy = 840
        d.ellipse((540 + sep - 190, cy - 190, 540 + sep + 190, cy + 190), fill=WARM + (110,), outline=WARM + (255,), width=5)
        d.ellipse((540 - sep - 190, cy - 190, 540 - sep + 190, cy + 190), fill=(255, 255, 255, 60), outline=INK + (255,), width=5)
        # 中间界线（虚线）
        bl = 1 - k
        if tt >= tB and bl > 0.05:
            for yy in range(cy - 220, cy + 220, 26):
                d.line([(540, yy), (540, yy + 14)], fill=(60, 120, 100, int(255 * bl * ramp(tt, tB, .5))), width=6)
        im = Image.alpha_composite(im, lay)
        d = ImageDraw.Draw(im)
        d.text((540 - sep - 40, cy - 30), "我", font=f, fill=INK)
        d.text((540 + sep - 40, cy - 30), "他人", font=f, fill=INK)
        if tt < tC:
            im = over(im, lbl_boundary, ramp(tt, tB, .5))
        elif tt < tD:
            im = over(im, lbl_cont, ramp(tt, tC, .5))
        else:
            im = over(im, lbl_blur, ramp(tt, tD, .5))
        return im
    return "light", fr


def make_twopath(ctx):
    bg = paper(41).convert("RGBA")
    t1 = L_at(ctx, 1, 2); t2 = L_at(ctx, 2, 6); t3 = L_at(ctx, 3, 9); t4 = L_at(ctx, 4, 13)
    lay0 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay0)
    fb = font("serif", 50, 800); f = font("sans", 36, 500)

    def box(dd, cx, cy, txt, col, w=360):
        tw, th = text_size(txt, fb)
        dd.rounded_rectangle((cx - w / 2, cy - 55, cx + w / 2, cy + 55), 18, fill=col + (235,))
        dd.text((cx - tw / 2, cy - 34), txt, font=fb, fill=(252, 248, 240))
    box(d, 540, 480, "他人之苦", (90, 86, 82))
    d.line([(540, 535), (540, 610)], fill=INK, width=4)
    box(d, 540, 665, "同理心", (120, 112, 104))
    left = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(left)
    dl.line([(470, 720), (280, 860)], fill=INK, width=4)
    box(dl, 270, 915, "共情痛苦", WARM, 380)
    for i, s in enumerate(["以自我为中心的难受", "想退开、自保", "长期 → 损害身心"]):
        tw, _ = text_size(s, f); dl.text((270 - tw / 2, 1000 + i * 58), s, font=f, fill=INK)
    right = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(right)
    dr.line([(610, 720), (800, 860)], fill=INK, width=4)
    box(dr, 810, 915, "慈悲", (176, 130, 40), 380)
    for i, s in enumerate(["温暖、关切", "想让对方好起来", "靠近 · 助人"]):
        tw, _ = text_size(s, f); dr.text((810 - tw / 2, 1000 + i * 58), s, font=f, fill=INK)
    src = text_layer("据 Singer & Klimecki (2014) 图 1 重绘（示意）", font("sans", 26, 400), INK_SOFT + (255,), y=1240)[0]

    def fr(t):
        im = bg.copy()
        im = over(im, lay0, ramp(t, 0, .6))
        im = over(im, left, ramp(t, t1, .6))
        im = over(im, right, ramp(t, t3, .6))
        im = over(im, src, ramp(t, t1, .6))
        return im
    return "light", fr


# =============== 水墨：落水者与长竿 ===============
def ink_scene_layers():
    bgp = paper(43).convert("RGBA")
    # 远山
    def mountains(d):
        r = np.random.default_rng(4)
        pts = [(0, 700)]
        for x in range(0, W + 40, 40):
            pts.append((x, 640 - 120 * math.sin(x / 260) - 60 * math.sin(x / 90 + 1) + r.uniform(-8, 8)))
        pts += [(W, 900), (0, 900)]
        d.polygon(pts, fill=60)
    mt = ink_layer(mountains, blur=8, bleed=30, seed=5, color=(90, 96, 100))
    # 水面横纹
    def water(d):
        r = np.random.default_rng(6)
        for i in range(34):
            y = 950 + i * 9 + r.uniform(-4, 4)
            x0 = r.uniform(200, 1000); L = r.uniform(150, 500)
            d.line([(x0, y), (x0 + L, y + r.uniform(-3, 3))], fill=int(r.uniform(60, 140)), width=int(r.uniform(2, 5)))
    wt = ink_layer(water, blur=1.5, bleed=4, seed=7)
    # 岸（左侧巨石）
    def bank(d):
        d.polygon([(0, 1000), (90, 930), (220, 915), (330, 950), (400, 1010), (430, 1110), (380, 1170), (0, 1200)], fill=235)
        d.polygon([(40, 1060), (160, 1030), (260, 1060), (200, 1100)], fill=120)
    bk = ink_layer(bank, blur=3, bleed=12, seed=8)
    # 落水者（右侧水中，单手高举）
    def drowning(d):
        x, y = 800, 1000
        d.ellipse((x - 34, y - 40, x + 34, y + 28), fill=255)
        d.line([(x + 18, y - 6), (x + 64, y - 110), (x + 74, y - 160)], fill=255, width=18, joint="curve")
        d.ellipse((x + 62, y - 186, x + 92, y - 152), fill=255)
        d.line([(x - 26, y + 4), (x - 74, y - 40)], fill=255, width=14)
        d.ellipse((x - 100, y + 18, x + 100, y + 44), outline=200, width=5)
        d.ellipse((x - 150, y + 30, x + 150, y + 62), outline=120, width=3)
    dw = ink_layer(drowning, blur=1.8, bleed=6, seed=9)
    # 跳下去的人（在落水者旁，一起挣扎）
    def jumper(d):
        x, y = 610, 1020
        d.ellipse((x - 32, y - 38, x + 32, y + 26), fill=255)
        d.line([(x - 14, y - 6), (x - 82, y - 96)], fill=255, width=16)
        d.line([(x + 16, y - 4), (x + 60, y - 74)], fill=255, width=15)
        d.ellipse((x - 110, y + 16, x + 110, y + 44), outline=180, width=5)
        r = np.random.default_rng(10)
        for k in range(9):
            a = r.uniform(math.pi * 1.15, math.pi * 1.85); L = r.uniform(25, 60)
            d.ellipse((x + L * math.cos(a) * 1.6 - 5, y + 10 + L * math.sin(a) - 5, x + L * math.cos(a) * 1.6 + 5, y + 10 + L * math.sin(a) + 5), fill=140)
    jp = ink_layer(jumper, blur=1.8, bleed=6, seed=11)
    # 站稳的人：弓步立于石上，双手握竿
    def stander(d):
        x, y = 200, 640            # 头心
        d.ellipse((x - 36, y - 40, x + 36, y + 34), fill=255)
        d.polygon([(x - 72, y + 4), (x + 72, y + 4), (x, y - 26)], fill=255)          # 斗笠
        d.polygon([(x - 46, y + 46), (x + 40, y + 46), (x + 62, y + 190), (x - 58, y + 190)], fill=255)   # 上身
        d.polygon([(x - 58, y + 186), (x + 62, y + 186), (x + 96, y + 270), (x - 92, y + 270)], fill=255)  # 衣摆
        d.line([(x - 40, y + 260), (x - 96, y + 330)], fill=255, width=26)   # 后腿
        d.line([(x + 40, y + 260), (x + 110, y + 320)], fill=255, width=26)  # 前腿（弓）
        d.line([(x + 110, y + 320), (x + 110, y + 345)], fill=255, width=24)
        d.line([(x + 20, y + 80), (x + 110, y + 150)], fill=255, width=20)   # 臂
        d.line([(x - 10, y + 96), (x + 60, y + 170)], fill=255, width=18)
    st = ink_layer(stander, blur=1.8, bleed=6, seed=12)

    def pole_fn(p):
        def f(d):
            d.line([(240, 770), (840, 870)], fill=255, width=11)
        return f
    pole_full = ink_layer(pole_fn(1.0), blur=1.2, bleed=4, seed=13)
    return bgp, mt, wt, bk, dw, jp, st, pole_full


def make_ink(ctx):
    bgp, mt, wt, bk, dw, jp, st, pole = ink_scene_layers()
    base = Image.alpha_composite(Image.alpha_composite(bgp, mt), wt)
    t1 = L_at(ctx, 1, 3); t2 = L_at(ctx, 2, 7); t3 = L_at(ctx, 3, 11); t4 = L_at(ctx, 4, 15)
    lblA = text_layer("共情痛苦：跳下去一起挣扎", font("serif", 42, 700), WARM + (255,), y=1180)[0]
    lblB = text_layer("慈悲：站稳，伸出长竿", font("serif", 42, 700), (150, 100, 20, 255), y=1250)[0]
    note = text_layer("类比示意 · 非实验结果", font("sans", 28, 500), INK_SOFT + (255,), y=420)[0]
    sl = seal("慈悲", 900, 1120, 76)
    # 竿子分段显示用 mask
    def fr(t):
        im = base.copy()
        im = over(im, bk, ramp(t, 0, .8))
        bob = math.sin(t * 2.2) * 4
        im = over(im, dw.transform(dw.size, Image.AFFINE, (1, 0, 0, 0, 1, -bob)), ramp(t, 0.3, .8))
        im = over(im, jp.transform(jp.size, Image.AFFINE, (1, 0, 0, 0, 1, bob)), ramp(t, t1, .6))
        im = over(im, lblA, ramp(t, t1 + .5, .6))
        if t >= t2:
            im = over(im, st, ramp(t, t2, .6))
            p = ramp(t, t2 + 0.8, 1.6)
            if p > 0:
                m = Image.new("L", (W, H), 0)
                ImageDraw.Draw(m).rectangle((0, 0, 250 + 600 * p, H), fill=255)
                pl = pole.copy(); pl.putalpha(ImageChops.multiply(pl.getchannel("A"), m))
                im = Image.alpha_composite(im, pl)
            im = over(im, lblB, ramp(t, t2 + 1.6, .6))
        im = over(im, sl, ramp(t, t3, .6))
        im = over(im, note, ramp(t, t4 - 0.3, .5) if t4 < ctx["dur"] else 0)
        return im
    return "light", fr


def make_helping(ctx):
    return bullet_card(ctx, "行为上的证据", [
        "· 生起慈悲的人，比陷入共情痛苦的人更常出手相助（巴特森、艾森伯格等的社会心理学研究）",
        "· 练过慈悲的人，在电脑游戏里更愿意帮助陌生人（辛格团队）",
        "· 坚持几周慈心练习，日常积极情绪增加（弗雷德里克森等）"],
        timing=[L_at(ctx, 1, 1), L_at(ctx, 2, 5), L_at(ctx, 3, 9)], seed=45, size=40, gap=50)


# =============== ReSource ===============
def make_resource(ctx):
    bg = night_bg(47).convert("RGBA")
    t1 = L_at(ctx, 1, 3); t2 = L_at(ctx, 2, 6)
    h1 = text_layer("ReSource 项目", font("serif", 64, 800), (244, 238, 226, 255), y=430)[0]
    big = text_layer("332", font("serif", 240, 800), (244, 238, 226, 255), y=560)[0]
    cap = text_layer("名 20–55 岁健康成年人", font("sans", 44, 500), (200, 206, 216, 255), y=870)[0]
    row = text_layer("9 个月  ·  3 个模块  ·  每个 3 个月", font("sans", 48, 600), COOL + (255,), y=1000)[0]
    src = text_layer("Valk et al., Science Advances 3(10): e1700489 (2017)", font("sans", 28, 400), (160, 166, 178, 255), y=1240)[0]

    def fr(t):
        im = bg.copy()
        im = over(im, h1, ramp(t, 0, .5)); im = over(im, src, ramp(t, .3, .5))
        im = over(im, big, ramp(t, t2, .6)); im = over(im, cap, ramp(t, t2 + .3, .6))
        im = over(im, row, ramp(t, t2 + 2.0, .6))
        return im
    return "dark", fr


MOD = [("当下 Presence", "专注呼吸、觉察身体（类似正念）", BLUE),
       ("情感 Affect", "慈悲、面对困难情绪、助人动机", (200, 120, 70)),
       ("视角 Perspective", "理解他人所想、反观自己的念头", JADE)]


def make_modules(ctx):
    bg = night_bg(49).convert("RGBA")
    lays = []
    for i, (n, dsc, col) in enumerate(MOD):
        l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(l)
        y = 440 + i * 230
        d.rounded_rectangle((90, y, W - 90, y + 190), 20, fill=col + (60,), outline=col + (255,), width=4)
        d.text((130, y + 26), f"{i + 1}  {n}", font=font("serif", 50, 800), fill=(244, 238, 226))
        d.text((130, y + 108), dsc, font=font("sans", 38, 500), fill=(214, 220, 228))
        lays.append(l)
    ctl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ctl)
    y = 440 + 3 * 230
    d.rounded_rectangle((90, y, W - 90, y + 140), 20, outline=(150, 156, 168, 255), width=3)
    d.text((130, y + 40), "对照组：不训练，同期做同样测量", font=font("sans", 40, 500), fill=(200, 206, 216))
    tm = [L_at(ctx, i, i * 3) for i in range(4)]

    def fr(t):
        im = bg.copy()
        for l, t0 in zip(lays, tm[:3]):
            im = over(im, l, ramp(t, t0, .5))
        im = over(im, ctl, ramp(t, tm[3], .5))
        return im
    return "dark", fr


LAT = {"pfc": (-0.62, -0.30, 0.26, 0.20, 0.3), "fi": (-0.30, 0.12, 0.17, 0.11, 0.2),
       "ifg": (-0.52, 0.08, 0.14, 0.10, 0.0), "temp": (0.05, 0.30, 0.30, 0.10, -0.1)}


def make_cortex(ctx):
    cx, cy, s = 560, 870, 400
    bg = night_bg(51).convert("RGBA")
    base = Image.alpha_composite(bg, brain_base(cx, cy, s, "lateral", True, 8))
    def reg(keys, col):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for k in keys:
            dx, dy, rx, ry, rot = LAT[k]
            lay = Image.alpha_composite(lay, blob(cx + dx * s, cy + dy * s, rx * s, ry * s, col, 0.95, rot))
        return lay
    regs = [reg(["pfc"], BLUE), reg(["fi"], (220, 120, 70)), reg(["ifg", "temp"], JADE)]
    head = text_layer("三种练法 · 三处不同的皮层变化", font("serif", 52, 800), (244, 238, 226, 255), y=420)[0]
    f = font("sans", 34, 600)
    labs = []
    for txt, col, y in [("当下 → 前额叶", BLUE, 1130), ("情感 → 额叶-脑岛", (220, 120, 70), 1180), ("视角 → 额下回、颞叶外侧", JADE, 1230)]:
        labs.append(text_layer(txt, f, col + (255,), y=y)[0])
    note = text_layer("外侧面示意 · 位置为大致范围", font("sans", 26, 400), (170, 176, 190, 255), y=1290)[0]
    t1 = L_at(ctx, 1, 4); t2 = L_at(ctx, 2, 10); t3 = L_at(ctx, 3, 13)
    big = text_layer("练什么，就长什么", font("serif", 70, 800), (244, 238, 226, 255), y=520)[0]

    def fr(t):
        im = base.copy()
        im = over(im, head, ramp(t, 0, .5) * (1 - ramp(t, t3 - .3, .4)))
        for i, (r, l) in enumerate(zip(regs, labs)):
            a = ramp(t, t1 + i * 2.2, .7)
            im = over(im, r, a * (0.8 + 0.2 * math.sin(t * 2 + i)))
            im = over(im, l, a)
        im = over(im, note, 0.9)
        im = over(im, big, ramp(t, t3, .6))
        return im
    return "dark", fr


def make_cortex_cav(ctx):
    return bullet_card(ctx, "同样要说清楚", [
        "· 参与者 95% 以上为白人，都是健康成年人",
        "· 皮层厚度是间接指标",
        "· 不等于“一个人变得更善良了”"], dark=True, seed=53,
        timing=[0.5, L_at(ctx, 0, 0) + 3.6, L_at(ctx, 0, 0) + 6.0])


def make_limits(ctx):
    bg, card = paper_card("《警惕炒作》", [
        ("Mind the Hype: A Critical Evaluation and Prescriptive Agenda for Research on Mindfulness and Meditation", "serif", 38, INK),
        ("N. T. Van Dam 等 15 位作者", "sans", 34, INK_SOFT),
        ("Perspectives on Psychological Science 13(1): 36–61 (2018)", "sans", 32, INK_SOFT),
        ("方法粗糙 · 对照不足 · 媒体夸大 · 不良反应被低估", "serif", 38, SEAL),
    ], bg_seed=55)
    t2 = L_at(ctx, 2, 6)

    def fr(t):
        im = bg.copy()
        return over(im, card, ramp(t, 0.2, .6))
    return "light", fr


def make_limits3(ctx):
    return bullet_card(ctx, "放到本期题目上：三点要记住", [
        "一  情绪多是自评，可能有期待效应",
        "二  脑区亮了，不等于找到“慈悲中枢”",
        "三  慈悲训练不能替代休息、制度支持与专业帮助",
        "长期失眠、麻木、提不起劲 → 先找专业的人聊聊"],
        timing=[L_at(ctx, 1, 2), L_at(ctx, 2, 7), L_at(ctx, 3, 12), L_at(ctx, 4, 18)], seed=57, size=44, gap=60)


def make_practice(ctx):
    bg = paper(59).convert("RGBA")
    head = text_layer("一个很小的转向", font("serif", 60, 800), INK + (255,), y=420)[0]
    steps = ["停一下：双脚踩地，慢慢呼吸", "提醒自己：这是他的苦，我在这里陪他", "转向：我能为他做点什么？"]
    lays = [text_layer(f"{i + 1}  {s}", font("sans", 44, 600), INK + (255,), maxw=880, x=110, y=640 + i * 170, align="left")[0] for i, s in enumerate(steps)]
    small = text_layer("哪怕只是递一杯热水，听他把话说完", font("serif", 44, 600), (150, 100, 20, 255), y=1150)[0]
    note = text_layer("生活建议，并非经过检验的疗法", font("sans", 30, 500), INK_SOFT + (255,), y=1250)[0]
    tm = [L_at(ctx, 2, 3), L_at(ctx, 3, 7), L_at(ctx, 4, 10)]

    def fr(t):
        im = bg.copy()
        im = over(im, head, ramp(t, 0, .5))
        # 呼吸圆
        r = 60 + 20 * math.sin(t * 1.3)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((540 - r, 560 - r * 0 - 40, 540 + r, 560 + 2 * r - 40 - r), outline=JADE + (0,), width=1)
        for l, t0 in zip(lays, tm):
            im = over(im, l, ramp(t, t0, .5))
        im = over(im, small, ramp(t, L_at(ctx, 5, 13), .5))
        im = over(im, note, ramp(t, L_at(ctx, 6, 16), .5))
        return im
    return "light", fr


# =============== 经卷 ===============
def scroll_bg(seed=61):
    bg = paper(seed, (230, 222, 204)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # 卷轴上下木轴
    for y in (360, 1340):
        d.rounded_rectangle((70, y - 18, W - 70, y + 18), 16, fill=(92, 62, 40, 255))
        d.ellipse((40, y - 26, 96, y + 26), fill=(70, 46, 30, 255)); d.ellipse((W - 96, y - 26, W - 40, y + 26), fill=(70, 46, 30, 255))
    # 乌丝栏
    for x in range(140, W - 120, 92):
        d.line([(x, 390), (x, 1310)], fill=(150, 110, 80, 90), width=2)
    return bg


def make_scroll(ctx):
    bg = scroll_bg()
    t1 = L_at(ctx, 1, 2)
    title = vtext_layer("大智度論\n卷第二十七", font("tc", 76, 800), INK + (255,), x=830, y=470, col_gap=1.5)
    by = vtext_layer("龍樹造\n鳩摩羅什譯", font("tc", 44, 600), INK_SOFT + (255,), x=520, y=500, col_gap=1.6)
    sub = vtext_layer("釋初品大慈大悲義第四十二", font("tc", 40, 600), INK_SOFT + (255,), x=330, y=470)
    sl = seal("慈悲", 200, 1180, 80)

    def fr(t):
        im = bg.copy()
        p = ramp(t, 0, 1.4)   # 展开
        im = over(im, title, ramp(t, 0.4, .8))
        im = over(im, by, ramp(t, t1, .8))
        im = over(im, sub, ramp(t, t1 + .8, .8))
        im = over(im, sl, ramp(t, t1 + 1.6, .5))
        if p < 1:
            cover = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(cover).rectangle((0, 380 + int(940 * p), W, 1322), fill=(230, 222, 204, 255))
            im = Image.alpha_composite(im, cover)
        return im
    return "light", fr


def classic(ctx, cols, size, white, src, white_y=1150, seed=63, x=None, t_white=None, extra=None):
    bg = scroll_bg(seed)
    xr = x or (540 + (len(cols) - 1) * size * 1.6 / 2)
    v = vtext_layer("\n".join(cols), font("tc", size, 700), INK + (255,), x=int(xr), y=420, col_gap=1.6, line_gap=1.1)
    w_ = text_layer(white, font("serif", 42, 600), (120, 70, 30, 255), maxw=880, y=white_y)[0]
    s_ = text_layer(src, font("sans", 26, 400), INK_SOFT + (255,), y=1360, maxw=960)[0]
    tw = t_white if t_white is not None else L_at(ctx, 1, 2)

    def fr(t):
        im = bg.copy()
        # 逐列显现
        n = len(cols)
        for i in range(n):
            pass
        im = over(im, v, ramp(t, 0.1, 1.2))
        im = over(im, w_, ramp(t, tw, .6))
        im = over(im, s_, ramp(t, 0.6, .6))
        if extra:
            im = extra(im, t)
        return im
    return "light", fr


def make_quote_dz1(ctx):
    # 两段：先大慈大悲句，后父亲譬喻
    tF = L_at(ctx, 2, 9)
    st1, f1 = classic(ctx, ["大慈與一切眾生樂，", "大悲拔一切眾生苦。"], 80, "大慈，是给一切众生快乐；大悲，是拔除一切众生的痛苦。",
                      "《大智度論》卷二十七 · 龍樹造，鳩摩羅什譯", white_y=1180)
    ctx2 = dict(ctx); ctx2["lt"] = [l - tF for l in ctx["lt"]]
    st2, f2 = classic(ctx2, ["其父慈惻，", "以若干方便，", "令得免苦，", "是大悲。"], 72,
                      "父亲心疼孩子，想尽种种办法让他们免于受苦，这就是大悲。", "《大智度論》卷二十七（譬喻：諸子繫在牢獄）",
                      white_y=1180, seed=65, t_white=0.8)

    def fr(t):
        if t < tF - 0.4:
            return f1(t)
        if t < tF:
            return Image.blend(f1(t), f2(0), ramp(t, tF - 0.4, 0.4))
        return f2(t - tF)
    return "light", fr


def make_quote_dz2(ctx):
    bg = scroll_bg(67)
    f = font("tc", 50, 700)
    left = vtext_layer("小悲，名觀眾生\n種種身苦心苦，\n憐愍而已，\n不能令脫。", f, INK_SOFT + (255,), x=980, y=430, col_gap=1.5, line_gap=1.08)
    right = vtext_layer("大悲，憐愍眾生苦，\n亦能令脫苦。", f, INK + (255,), x=340, y=430, col_gap=1.5, line_gap=1.08)
    tl = text_layer("小悲：怜悯而已", font("serif", 40, 700), INK_SOFT + (255,), x=800, y=1180)[0]
    tr = text_layer("大悲：还能帮他脱苦", font("serif", 40, 700), (150, 90, 30, 255), x=300, y=1180)[0]
    src = text_layer("《大智度論》卷二十七 · 釋初品大慈大悲義第四十二", font("sans", 26, 400), INK_SOFT + (255,), y=1360)[0]
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(line).line([(560, 430), (560, 1140)], fill=(150, 110, 80, 160), width=2)
    big = text_layer("只陪着难过是不够的\n要有力气，把人拉上来", font("serif", 52, 800), (150, 90, 30, 255), y=1170, spacing=1.35)[0]
    t1 = L_at(ctx, 1, 2); t2 = L_at(ctx, 2, 6); t3 = L_at(ctx, 3, 9)

    def fr(t):
        im = bg.copy()
        im = over(im, src, ramp(t, 0, .6)); im = over(im, line, ramp(t, 0, .6))
        im = over(im, left, ramp(t, t1, .8))
        im = over(im, right, ramp(t, t2, .8))
        if t < t3:
            im = over(im, tl, ramp(t, t1 + 1.0, .6)); im = over(im, tr, ramp(t, t2 + 1.0, .6))
        else:
            im = over(im, big, ramp(t, t3, .6))
        return im
    return "light", fr


def make_yinzhao(ctx):
    bg = paper(69).convert("RGBA")
    head = text_layer("印照，不是证明", font("serif", 76, 800), SEAL + (255,), y=440)[0]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (h1, b1, col) in enumerate([("经论", "讲修行的境界\n此心、此生的体验", (120, 80, 40)), ("实验", "量看短片时的\n情绪自评与脑血流", (60, 90, 120))]):
        x = 110 + i * 450
        d.rounded_rectangle((x, 620, x + 410, 1000), 22, fill=(250, 246, 238, 230), outline=col + (255,), width=3)
        tw, _ = text_size(h1, font("serif", 54, 800)); d.text((x + 205 - tw / 2, 650), h1, font=font("serif", 54, 800), fill=col)
        for j, ln in enumerate(b1.split("\n")):
            tw, _ = text_size(ln, font("sans", 38, 500)); d.text((x + 205 - tw / 2, 780 + j * 62), ln, font=font("sans", 38, 500), fill=INK)
    mid = text_layer("相通之处，不是同一件事", font("serif", 46, 700), INK + (255,), y=1060)[0]
    last = text_layer("或许佛学的讲法，也有科学基础\n——算是一种印照。", font("serif", 42, 600), (120, 80, 40, 255), y=1150, maxw=900)[0]
    t1 = L_at(ctx, 1, 2); t2 = L_at(ctx, 2, 5); t3 = L_at(ctx, 3, 10)

    def fr(t):
        im = bg.copy()
        im = over(im, head, ramp(t, t1, .6))
        im = over(im, lay, ramp(t, t2, .6))
        im = over(im, mid, ramp(t, t2 + 2.5, .6))
        im = over(im, last, ramp(t, t3, .6))
        return im
    return "light", fr


def make_quote_dz3(ctx):
    return classic(ctx, ["以大慈悲力故，", "於無量阿僧祇世", "生死中，", "心不厭沒。"], 76,
                   "因为大慈悲的力量，在无量的生死之中，心不厌倦，也不沉没。", "《大智度論》卷二十七 · 龍樹造，鳩摩羅什譯",
                   white_y=1180, seed=71, t_white=L_at(ctx, 1, 4) - 0.5)


# =============== 晨光：递出一杯热水 ===============
def dawn_static():
    t = np.linspace(0, 1, H)[:, None, None]
    top = np.array((250, 226, 186), np.float32); bot = np.array((214, 176, 140), np.float32)
    a = top * (1 - t) + bot * t
    a = np.repeat(a, W, axis=1)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # 窗格光
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(rays)
    for i in range(4):
        x = 80 + i * 150
        d.polygon([(x, 300), (x + 90, 300), (x + 520, 1400), (x + 330, 1400)], fill=(255, 246, 220, 46))
    img = Image.alpha_composite(img, rays.filter(ImageFilter.GaussianBlur(24)))
    # 桌面
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1180, W, H), fill=(150, 108, 76, 255))
    d.line([(0, 1180), (W, 1180)], fill=(120, 84, 58, 255), width=6)
    return img


def hand_cup():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    skin = (230, 186, 154, 255); skin_d = (206, 158, 126, 255); sleeve = (238, 234, 226, 255)
    # 前臂从右下伸入
    d.polygon([(W + 60, 1010), (W + 60, 1200), (760, 1080), (740, 980)], fill=skin)
    d.polygon([(W + 60, 990), (W + 60, 1230), (930, 1150), (900, 1000)], fill=sleeve)
    # 手掌托住杯底
    d.ellipse((470, 990, 800, 1110), fill=skin)
    # 杯
    cx, top, bot = 600, 720, 1040
    d.polygon([(cx - 150, top), (cx + 150, top), (cx + 122, bot), (cx - 122, bot)], fill=(248, 246, 240, 255))
    d.polygon([(cx + 60, top + 10), (cx + 150, top), (cx + 122, bot), (cx + 50, bot)], fill=(230, 226, 218, 255))
    d.ellipse((cx - 122, bot - 18, cx + 122, bot + 18), fill=(236, 232, 224, 255))
    d.ellipse((cx - 150, top - 32, cx + 150, top + 32), fill=(232, 228, 220, 255))
    d.ellipse((cx - 132, top - 22, cx + 132, top + 22), fill=(205, 165, 112, 255))
    # 托杯的手：掌心在下，拇指压在杯身前侧
    d.rounded_rectangle((cx - 40, 960, cx + 140, 1008), 24, fill=skin)
    lay = lay.filter(ImageFilter.GaussianBlur(0.8))
    return lay


def make_dawn(ctx):
    base = Image.alpha_composite(dawn_static(), hand_cup())
    t1 = L_at(ctx, 1, 3)
    end1 = text_layer("先让自己站稳。", font("serif", 64, 800), (90, 54, 30, 255), y=420)[0]
    end2 = text_layer("慈悲不是一起沉下去，\n而是有力气伸出手。", font("serif", 64, 800), (90, 54, 30, 255), y=420, spacing=1.35)[0]

    def fr(t):
        im = push(base, t, ctx["dur"] + 1, 1.0, 1.04, 0.45, 0.6)
        # 蒸汽
        st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(st)
        for k in range(3):
            pts = []
            for j in range(40):
                u = j / 39
                y = 720 - u * 300
                x = 500 + k * 60 + 26 * math.sin(u * 7 + t * 1.6 + k * 2) * u
                pts.append((x, y))
            a = int(110 * (0.6 + 0.4 * math.sin(t * 1.2 + k)))
            d.line(pts, fill=(255, 255, 255, a), width=10, joint="curve")
        im = Image.alpha_composite(im, st.filter(ImageFilter.GaussianBlur(6)))
        if t < t1:
            im = over(im, end1, ramp(t, .2, .6) * (1 - ramp(t, t1 - .3, .3)))
        else:
            im = over(im, end2, ramp(t, t1, .6))
        return im
    return "light", fr


SCENES = {
    "hook": make_hook, "brain2": make_brain2, "burnout": make_burnout, "rename": make_rename,
    "exp_intro": make_exp_intro, "exp_design": make_exp_design, "exp_video": make_exp_video, "exp_emp": make_exp_emp,
    "brain_emp": make_brain_emp, "exp_comp": make_exp_comp, "chart": make_chart, "brain_comp": make_brain_comp,
    "k13": make_k13, "quote_k14": make_quote_k14, "caveat1": make_caveat1, "define": make_define, "twopath": make_twopath,
    "quote_sk": make_quote_sk, "ink": make_ink, "helping": make_helping, "resource": make_resource, "modules": make_modules,
    "cortex": make_cortex, "cortex_cav": make_cortex_cav, "limits": make_limits, "limits3": make_limits3,
    "practice": make_practice, "scroll": make_scroll, "quote_dz1": make_quote_dz1, "quote_dz2": make_quote_dz2,
    "yinzhao": make_yinzhao, "quote_dz3": make_quote_dz3, "dawn": make_dawn,
}

# 区段标题与证据标签
SECTION = {
    "hook": None, "brain2": None, "burnout": None, "rename": None,
    "exp_intro": "一 · 一个实验", "k13": "一 · 一个实验", "caveat1": "一 · 一个实验",
    "define": "二 · 两条路", "helping": "二 · 两条路",
    "resource": "三 · 更大的样本",
    "limits": "四 · 证据的边界", "practice": "五 · 带回生活",
    "scroll": "六 · 印照", "dawn": None,
}
TAG = {
    "brain2": ("示意", (110, 120, 136)),
    "exp_intro": ("实证 · 小样本", (160, 90, 40)), "exp_design": ("实证 · 小样本", (160, 90, 40)),
    "exp_video": ("实证 · 小样本", (160, 90, 40)), "exp_emp": ("实证 · 小样本", (160, 90, 40)),
    "brain_emp": ("实证 · 小样本", (160, 90, 40)), "exp_comp": ("实证 · 小样本", (160, 90, 40)),
    "chart": ("实证 · 小样本", (160, 90, 40)), "brain_comp": ("实证 · 小样本", (160, 90, 40)),
    "k13": ("实证 · 小样本", (160, 90, 40)), "quote_k14": ("实证 · 小样本", (160, 90, 40)), "caveat1": ("小样本", SEAL),
    "define": ("综述", (60, 100, 130)), "twopath": ("综述", (60, 100, 130)), "quote_sk": ("综述", (60, 100, 130)),
    "ink": ("类比", (110, 110, 110)), "helping": ("实证", (60, 120, 90)),
    "resource": ("实证 · 大样本", (60, 120, 90)), "modules": ("实证 · 大样本", (60, 120, 90)),
    "cortex": ("实证 · 大样本", (60, 120, 90)), "cortex_cav": ("局限", SEAL),
    "limits": ("方法论综述", (60, 100, 130)), "limits3": ("局限", SEAL), "practice": ("生活建议", (110, 110, 110)),
    "quote_dz1": ("经典", (120, 80, 40)), "quote_dz2": ("经典", (120, 80, 40)), "yinzhao": ("印照 · 非证明", SEAL),
    "quote_dz3": ("经典", (120, 80, 40)),
}
