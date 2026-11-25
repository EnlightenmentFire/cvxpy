# -*- coding: utf-8 -*-
"""分镜：每个 vis 一个绘制函数 f(c, S, t)，t 为场景内秒数，S 为 timeline 场景字典（含 cues）。"""
import math, os, sys, json
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import geo

P = geo.PLACES
_B = {}


def bases():
    if not _B:
        _B["b7"] = Base(f"{WORK}/dem/base7_r.png")
        _B["b9"] = Base(f"{WORK}/dem/base9_r.png")
        img, meta = geo.terr_layer()
        _B["terr"] = (img, meta)
        for nm in ("袁绍", "曹操", "刘表"):
            _B["t_" + nm] = geo.terr_layer([nm])[0]
    return _B


def cue(S, name, default=1e9):
    return S["cues"][name] - S["t0"] if name in S["cues"] else default


def lt(S, i):
    """第 i 句（0 起）的场景内起始时间。"""
    ls = S["lines"]
    return ls[min(i, len(ls) - 1)]["t0"] - S["t0"]


def dur(S):
    return S["t1"] - S["t0"]


# ───────────────────────── 地图通用 ─────────────────────────
def draw_terr(c, cam, img, a):
    if a <= 0.003:
        return
    meta = bases()["terr"][1]
    z = meta["z"]; n = 256 * 2 ** z; k = cam.S / n; m0 = merc(cam.lon, cam.lat)
    tx = cam.ax + (meta["x0"] * 256 / n - m0[0]) * cam.S; ty = cam.ay + (meta["y0"] * 256 / n - m0[1]) * cam.S
    p = skia.Paint(); p.setAlphaf(a)
    c.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), skia.Rect.MakeXYWH(tx, ty, img.width() * k, img.height() * k),
                    skia.SamplingOptions(skia.FilterMode.kLinear), p)


def draw_map(c, cam, terr=None, terr_a=1.0, grade=0.0):
    B = bases()
    c.clear(skia.Color4f(0.06, 0.07, 0.07, 1))
    a9 = clamp((6.8 - cam.span) / 2.0)
    if a9 < 1:
        B["b7"].draw(c, cam)
    if a9 > 0:
        B["b9"].draw(c, cam, a9)
    if terr:
        for nm in terr:
            draw_terr(c, cam, B["t_" + nm] if nm != "all" else B["terr"][0], terr_a)
    # 色调：压暗、偏暖
    c.drawRect(skia.Rect.MakeWH(W, H), paint((18, 14, 10), 0.12 + grade))
    grad_rect(c, 0, 0, W, 330, (8, 8, 8), 0.85, (8, 8, 8), 0.0)
    grad_rect(c, 0, 1250, W, 670, (8, 8, 8), 0.0, (8, 8, 8), 0.9)
    vignette(c, 0.55, 0.42)


def map_note(c, a=1.0):
    draw_text(c, "地图示意 · 今地名位置近似", 40, 300, 24, (200, 196, 186), 0.75 * a, "sans")


def pl(cam, name):
    return cam.p(*P[name])


def year_tag(c, s, a=1.0, sub=None):
    if a <= 0.003:
        return
    draw_text(c, s, W - 50, 250, 64, GOLD_HI, a, "serif", True, "right", stroke=4, stroke_a=0.6)
    if sub:
        draw_text(c, sub, W - 52, 296, 28, (220, 210, 190), a, "sans", False, "right")


def flag(c, x, y, color, a=1.0, s=1.0, wave=0.0, label=None):
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    c.drawLine(0, 0, 0, -70, paint((30, 26, 22), a, stroke=4))
    path = skia.Path(); path.moveTo(0, -70)
    for k in range(9):
        xx = k * 6; yy = -70 + math.sin(wave * 4 + k * 0.7) * 3
        path.lineTo(xx, yy)
    for k in range(8, -1, -1):
        xx = k * 6; yy = -38 + math.sin(wave * 4 + k * 0.7) * 3
        path.lineTo(xx, yy)
    path.close()
    c.drawPath(path, paint(color, a)); c.drawPath(path, paint((255, 255, 255), 0.4 * a, stroke=1.5))
    if label:
        draw_text(c, label, 27, -44, 26, (255, 250, 240), a, "serif", True, "center")
    c.restore()


def xmark(c, x, y, a=1.0, s=1.0):
    if a <= 0.003:
        return
    d = 22 * s
    c.drawLine(x - d, y - d, x + d, y + d, paint((230, 60, 50), a, stroke=8))
    c.drawLine(x - d, y + d, x + d, y - d, paint((230, 60, 50), a, stroke=8))


def big_text(c, s, y, size, color=GOLD_HI, a=1.0, name="serif", bold=True, spacing=0, stroke=6):
    draw_text(c, s, W / 2, y, size, color, a, name, bold, "center", stroke=stroke, stroke_a=0.7, shadow=14, spacing=spacing)


# ───────────────────────── 人物剪影 ─────────────────────────
def figure(c, x, y, s, facing=1, robe=(30, 28, 30), trim=GOLD, rim=0.4, pose="rest", hand=0.0, label=None, la=1.0, hat=True):
    """跽坐的人物剪影（侧面）。pose: rest / cup / drop。"""
    c.save(); c.translate(x, y); c.scale(s * facing, s)
    # 身体（袍）
    body = skia.Path()
    body.moveTo(-120, 0); body.cubicTo(-140, -90, -95, -200, -55, -250)
    body.cubicTo(-35, -272, -5, -280, 15, -270); body.cubicTo(48, -250, 60, -200, 70, -150)
    body.cubicTo(95, -90, 140, -50, 150, 0); body.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -280), skia.Point(0, 0)],
                                               [col(tuple(min(255, v + 26) for v in robe)), col(robe), col(tuple(max(0, v - 14) for v in robe))]))
    c.drawPath(body, p)
    # 衣领、襟（描边）
    lap = skia.Path(); lap.moveTo(8, -268); lap.cubicTo(30, -230, 24, -190, 52, -150)
    c.drawPath(lap, paint(trim, 0.85, stroke=6))
    c.drawPath(body, paint(trim, 0.35, stroke=2.5))
    # 轮廓光
    if rim > 0:
        c.drawPath(body, paint((210, 220, 255), 0.35 * rim, stroke=5, blur=3))
    # 头
    c.drawCircle(18, -312, 40, paint(tuple(max(0, v - 4) for v in (44, 36, 32))))
    c.drawCircle(18, -312, 40, paint((210, 220, 255), 0.3 * rim, stroke=3, blur=2))
    nose = skia.Path(); nose.moveTo(54, -322); nose.lineTo(66, -304); nose.lineTo(54, -298); nose.close()
    c.drawPath(nose, paint((40, 33, 30)))
    # 胡须
    beard = skia.Path(); beard.moveTo(30, -286); beard.cubicTo(44, -262, 40, -246, 30, -236); beard.cubicTo(22, -252, 18, -270, 22, -286); beard.close()
    c.drawPath(beard, paint((20, 18, 18), 0.9))
    if hat:
        cap = skia.Path(); cap.moveTo(-28, -334); cap.lineTo(-44, -398); cap.lineTo(-8, -392); cap.lineTo(44, -340); cap.close()
        c.drawPath(cap, paint((18, 16, 16)))
        c.drawPath(cap, paint(trim, 0.6, stroke=2))
        c.drawLine(-30, -336, 52, -336, paint(trim, 0.8, stroke=5))
        c.drawLine(-60, -352, 40, -360, paint(trim, 0.7, stroke=3))
    # 手臂与袖
    if pose == "cup":
        ex, ey = 150, -250 - 20 * hand
    elif pose == "drop":
        ex, ey = 165, -150
    else:
        ex, ey = 150, -150
    sl = skia.Path(); sl.moveTo(-10, -235); sl.cubicTo(40, -250, 100, ey - 10, ex - 10, ey)
    sl.lineTo(ex - 30, ey + 50); sl.cubicTo(60, -120, 10, -130, -20, -160); sl.close()
    p2 = skia.Paint(AntiAlias=True)
    p2.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -250), skia.Point(0, -100)], [col(tuple(min(255, v + 30) for v in robe)), col(robe)]))
    c.drawPath(sl, p2)
    c.drawPath(sl, paint(trim, 0.5, stroke=2.5))
    c.drawCircle(ex + 4, ey + 6, 13, paint((70, 56, 48)))
    if pose == "cup":
        cup = skia.Path(); cup.moveTo(ex - 4, ey - 6); cup.lineTo(ex + 28, ey - 6); cup.lineTo(ex + 22, ey + 14); cup.lineTo(ex + 2, ey + 14); cup.close()
        c.drawPath(cup, paint((150, 40, 30))); c.drawPath(cup, paint(GOLD, 0.8, stroke=2))
    c.restore()
    if label:
        draw_text(c, label, x, y + 60 * s, 40, trim, la, "serif", True, "center", stroke=5, stroke_a=0.8)


def room(c, t, flash=0.0, rain=0.0, brightness=1.0, seed=3):
    """许都府邸内景：后墙、窗棂、窗外雷雨天、柱、席。"""
    c.clear(skia.Color4f(0.05, 0.04, 0.035, 1))
    grad_rect(c, 0, 0, W, H, (34, 24, 18), brightness, (12, 9, 7), brightness)
    # 窗外
    wx, wy, ww, wh = 210, 330, 660, 520
    c.save(); c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
    sky = (26, 32, 44)
    grad_rect(c, wx, wy, ww, wh, (40, 46, 60), 1, (16, 18, 24), 1)
    r = np.random.default_rng(seed)
    for k in range(14):
        cx = wx + ((r.uniform(0, 1) * ww + t * r.uniform(6, 20)) % (ww + 300)) - 150
        cy = wy + r.uniform(20, 260)
        rr = r.uniform(70, 150)
        c.drawCircle(cx, cy, rr, paint((64 + 40 * flash, 70 + 40 * flash, 86 + 50 * flash), 0.55, blur=rr * 0.45))
    if flash > 0.02:
        c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), paint((200, 214, 255), 0.65 * flash))
        lightning(c, wx + ww * 0.62, wy - 10, wy + wh * 0.8, seed + int(t * 0), a=min(1, flash * 1.4), width=4)
    if rain > 0:
        rr2 = np.random.default_rng(11)
        p = paint((170, 186, 210), 0.35 * rain, stroke=1.6)
        for k in range(160):
            x0 = wx + rr2.uniform(0, ww + 120); sp = rr2.uniform(700, 1100)
            y0 = wy + ((rr2.uniform(0, 1) * wh + t * sp) % (wh + 60)) - 30
            c.drawLine(x0, y0, x0 - 10, y0 + 34, p)
    # 远处许都屋脊剪影
    roof = skia.Path(); roof.moveTo(wx, wy + wh)
    for k, (dx, hh) in enumerate([(0, 60), (90, 90), (160, 70), (250, 120), (330, 80), (420, 105), (520, 66), (600, 92), (660, 60)]):
        roof.lineTo(wx + dx, wy + wh - hh); roof.lineTo(wx + dx + 40, wy + wh - hh - 14); roof.lineTo(wx + dx + 80, wy + wh - hh)
    roof.lineTo(wx + ww, wy + wh); roof.close()
    c.drawPath(roof, paint((10, 10, 14), 0.95))
    c.restore()
    # 窗棂
    lat = paint((26, 16, 10), 1, stroke=14)
    c.drawRect(skia.Rect.MakeXYWH(wx, wy, ww, wh), paint((40, 22, 12), 1, stroke=26))
    for k in range(1, 6):
        c.drawLine(wx + ww * k / 6, wy, wx + ww * k / 6, wy + wh, lat)
    for k in range(1, 4):
        c.drawLine(wx, wy + wh * k / 4, wx + ww, wy + wh * k / 4, lat)
    # 光斑落地
    if flash > 0.02:
        lp = skia.Path(); lp.moveTo(wx, wy + wh); lp.lineTo(wx + ww, wy + wh); lp.lineTo(W + 100, 1500); lp.lineTo(-100, 1500); lp.close()
        c.drawPath(lp, paint((190, 205, 255), 0.18 * flash, blur=30))
    # 柱
    for px in (70, 1010):
        grad_rect(c, px - 45, 0, 90, H, (90, 26, 18), 1, (40, 12, 8), 1, vertical=False)
        c.drawRect(skia.Rect.MakeXYWH(px - 45, 0, 90, H), paint((0, 0, 0), 0.25))
    # 横梁
    grad_rect(c, 0, 200, W, 60, (70, 30, 18), 1, (30, 14, 8), 1)
    # 地面、席
    grad_rect(c, 0, 1230, W, 690, (40, 30, 22), 1, (16, 12, 9), 1)
    mat = skia.Path(); mat.moveTo(120, 1250); mat.lineTo(960, 1250); mat.lineTo(1060, 1500); mat.lineTo(20, 1500); mat.close()
    c.drawPath(mat, paint((92, 74, 44), 0.75))
    for k in range(18):
        y = 1250 + k * 14
        c.drawLine(120 - (y - 1250) * 0.4, y, 960 + (y - 1250) * 0.4, y, paint((60, 46, 26), 0.6, stroke=1.5))
    c.drawPath(mat, paint((140, 40, 30), 0.8, stroke=5))


def stage_begin(c, z=1.0):
    """宴饮场景统一放大：以 (540,900) 为轴放大 1.25 并下移。"""
    c.save(); c.translate(540, 960); c.scale(1.25 * z, 1.25 * z); c.translate(-540, -900)


def table(c, y=1180, x0=360, x1=720):
    c.drawRect(skia.Rect.MakeXYWH(x0, y, x1 - x0, 18), paint((70, 22, 14)))
    c.drawRect(skia.Rect.MakeXYWH(x0, y, x1 - x0, 4), paint((160, 60, 40), 0.8))
    for lx in (x0 + 20, x1 - 40):
        c.drawRect(skia.Rect.MakeXYWH(lx, y + 18, 20, 60), paint((50, 16, 10)))
    # 器皿：耳杯、豆、樽
    for bx in (430, 520, 640):
        c.drawOval(skia.Rect.MakeXYWH(bx - 32, y - 18, 64, 20), paint((120, 34, 24)))
        c.drawOval(skia.Rect.MakeXYWH(bx - 26, y - 16, 52, 10), paint((30, 10, 8)))
    rrect(c, 565, y - 70, 50, 70, 8, paint((120, 92, 50)))
    c.drawLine(565, y - 52, 615, y - 52, paint(GOLD, 0.8, stroke=3))


def utensils(c, t, t0, x0=700, y0=1090, ytab=1176, slow=1.0):
    """匕箸下落：t0 开始，重力 + 旋转 + 落案弹跳。返回落案时刻。"""
    g = 1800 * slow
    T_land = math.sqrt(2 * (ytab - y0) / g)
    items = [(0, -40, 0.3, 180, 8), (22, -30, -0.5, 180, 8), (44, -10, 0.9, 120, 0)]
    for i, (dx, vx, w, L, kind) in enumerate(items):
        tt = t - t0 - i * 0.04
        if tt < 0:
            x, y, ang = x0 + dx, y0, -0.9 + i * 0.1
        elif tt < T_land:
            x = x0 + dx + vx * tt; y = y0 + 0.5 * g * tt * tt; ang = -0.9 + i * 0.1 + w * tt * 4
        else:
            tb = tt - T_land
            bounce = abs(math.sin(tb * 18)) * 22 * math.exp(-tb * 6)
            x = x0 + dx + vx * T_land + vx * 0.3 * min(tb, 0.3); y = ytab - bounce
            ang = (0.05 + i * 0.04) * (1 - math.exp(-tb * 8)) + (-0.9 + i * 0.1 + w * T_land * 4) * math.exp(-tb * 8)
        c.save(); c.translate(x, y); c.rotate(math.degrees(ang))
        if kind:
            rrect(c, -L / 2, -kind / 2, L, kind, 3, paint((250, 236, 200)))
            rrect(c, -L / 2, -kind / 2, L, kind, 3, paint((40, 20, 10), 0.8, stroke=1.5))
            c.drawRect(skia.Rect.MakeXYWH(-L / 2, -kind / 2, 36, kind), paint((170, 40, 30)))
        else:
            c.drawOval(skia.Rect.MakeXYWH(-L / 2, -15, 46, 30), paint((236, 220, 180)))
            c.drawOval(skia.Rect.MakeXYWH(-L / 2, -15, 46, 30), paint((40, 20, 10), 0.8, stroke=1.5))
            rrect(c, -L / 2 + 40, -4, L - 40, 8, 3, paint((236, 220, 180)))
        c.restore()
    return t0 + T_land


def stamp(c, s, x, y, size=120, a=1.0, scale=1.0):
    """朱文竖排印章字。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(scale, scale)
    n = len(s); w = size * 1.25; h = n * size * 1.08 + size * 0.35
    rrect(c, -w / 2, -h / 2, w, h, 10, paint((170, 30, 24), 0.92 * a))
    rrect(c, -w / 2 + 8, -h / 2 + 8, w - 16, h - 16, 6, paint((250, 220, 200), 0.8 * a, stroke=4))
    yy = -h / 2 + size * 0.17 + size * 0.88
    for ch in s:
        draw_text(c, ch, 0, yy, size, (252, 236, 222), a, "tc", True, "center")
        yy += size * 1.08
    c.restore()


# ───────────────────────── 0 钩子 ─────────────────────────
def v_hook(c, S, t):
    fl = max(math.exp(-t * 5.0) * (1 if t < 0.12 or 0.2 < t < 0.5 else 0.5), 0)
    fl += 0.9 * math.exp(-max(0, t - 6.2) * 6) if t > 6.2 else 0
    stage_begin(c, 1.0 + 0.05 * ease(t / 14))
    room(c, t, flash=min(1, fl), rain=clamp((t - 4) / 3) * 0.7)
    figure(c, 230, 1300, 1.18, 1, robe=(26, 24, 26), trim=GOLD, rim=0.4 + fl, pose="cup", hand=ease(t / 1.2))
    figure(c, 850, 1300, 1.18, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.4 + fl, pose="drop")
    table(c)
    land = utensils(c, t, -0.05, slow=0.45)
    c.restore()
    vignette(c, 0.7, 0.35)
    # 名牌
    a = ramp(t, 0.5, 0.6)
    draw_text(c, "曹操", 250, 1530, 40, GOLD, a * (1 - ramp(t, lt(S, 3) - 0.3, 0.3)), "serif", True, "center", stroke=5)
    draw_text(c, "刘备", 830, 1530, 40, RED_HI, a * (1 - ramp(t, lt(S, 3) - 0.3, 0.3)), "serif", True, "center", stroke=5)
    # 失匕箸 印章（首帧即在）
    stamp(c, "失匕箸", 900, 640, 116, 1.0, 1.0 + 0.06 * math.exp(-max(0, t - land) * 8) * (t > land))
    # 天下英雄 大字
    big_text(c, "天下英雄", 300, 104, GOLD_HI, 1 - ramp(t, lt(S, 3) - 0.3, 0.4), "tc", True, spacing=14)
    big_text(c, "唯使君與操耳", 410, 72, (240, 226, 196), 1 - ramp(t, lt(S, 3) - 0.3, 0.4), "tc", True, spacing=8)
    # A03 比一支军队还值钱：远景兵阵虚影
    t3 = lt(S, 2)
    if t > t3 - 0.2:
        aa = fade_win(t, t3, lt(S, 3), 0.4, 0.4)
        r = np.random.default_rng(5)
        xy = np.stack([r.uniform(60, 1020, 500), 1490 + r.uniform(0, 80, 500) + np.sin(r.uniform(0, 6, 500) + t * 2) * 3], 1)
        Swarm.draw(c, xy, (150, 150, 150), 0.45 * aa, r=2.6)
        draw_text(c, "一句话  >  一支军队", W / 2, 1460, 56, GOLD_HI, aa, "serif", True, "center", stroke=6, shadow=10)


# ───────────────────────── B 反差：丢徐州 ─────────────────────────
def v_lostxuzhou(c, S, t):
    cam = Cam.lerp(Cam(117.4, 34.2, 4.2, ay=820), Cam(116.0, 34.15, 6.2, ay=820), ease((t - cue(S, "flee")) / 3.0))
    draw_map(c, cam)
    map_note(c, ramp(t, 0, 0.6))
    year_tag(c, "196–198", ramp(t, 0.2, 0.5), "建安元年至三年")
    xp = pl(cam, "下邳"); xs = pl(cam, "小沛"); xu = pl(cam, "许")
    tl = cue(S, "lost")
    flip = ramp(t, tl + 0.6, 0.4)
    city(c, *xp, "下邳", 1, PAPER, major=True)
    city(c, *xs, "小沛", 1, PAPER, side="up")
    city(c, *xu, "许", ramp(t, cue(S, "flee"), 0.5), GOLD_HI, major=True, side="left")
    flag(c, xp[0] + 6, xp[1] - 14, RED, 1 - flip, 1.3, t)
    flag(c, xp[0] + 6, xp[1] - 14, BLUE, flip, 1.3, t, "呂")
    if t > tl:
        c.drawCircle(*xp, 30 + 160 * ease_out((t - tl) / 1.2), paint(BLUE_HI, 0.8 * (1 - ramp(t, tl, 1.2)), stroke=6))
        draw_text(c, "徐州失守", xp[0], xp[1] + 120, 54, BLUE_HI, fade_win(t, tl + 0.3, dur(S), 0.4, 0.4), "serif", True, "center", stroke=6)
        # 妻儿两次被俘
        for k, yr in enumerate(["196 妻儿被俘", "198 妻儿再被俘"]):
            draw_text(c, yr, 80, 1180 + k * 62, 40, (230, 200, 190), ramp(t, tl + 1.0 + k * 0.8, 0.4), "sans", True, stroke=5)
    tf_ = cue(S, "flee")
    if t > tf_:
        pts = curve_pts([xp, xs, xu], 40, 0.12)
        draw_dashed(c, pts, ease((t - tf_) / 2.0), RED_HI, 8, 1, phase=-t * 40)
        draw_text(c, "带着残兵投奔曹操", W / 2, 470, 46, RED_HI, ramp(t, tf_ + 0.8, 0.5), "serif", True, "center", stroke=6)


# ───────────────────────── C 礼遇：同舆同席 ─────────────────────────
def v_honor(c, S, t):
    c.clear(skia.Color4f(0.05, 0.04, 0.035, 1))
    grad_rect(c, 0, 0, W, H, (40, 30, 20), 1, (10, 8, 6), 1)
    c.drawImage(noise_img(W // 4, H // 4, 2, alpha=0.06), 0, 0)
    # 车盖（羽葆盖车示意）
    cx, cy = W / 2, 760
    z = 1 + 0.05 * ease(t / 9)
    c.save(); c.translate(cx, cy); c.scale(z, z); c.translate(-cx, -cy)
    canopy = skia.Path(); canopy.moveTo(cx - 330, cy - 150); canopy.quadTo(cx, cy - 330, cx + 330, cy - 150); canopy.close()
    c.drawPath(canopy, paint((60, 20, 14))); c.drawPath(canopy, paint(GOLD, 0.8, stroke=4))
    for k in range(-3, 4):
        c.drawLine(cx + k * 95, cy - 150, cx + k * 95 + 4, cy - 132, paint(GOLD, 0.7, stroke=3))
    c.drawLine(cx, cy - 300, cx, cy + 120, paint((50, 30, 18), 1, stroke=10))
    # 车厢
    rrect(c, cx - 300, cy + 120, 600, 120, 8, paint((70, 24, 16)))
    c.drawRect(skia.Rect.MakeXYWH(cx - 300, cy + 120, 600, 10), paint(GOLD, 0.7))
    # 两人同车
    figure(c, cx - 140, cy + 130, 0.78, 1, robe=(26, 24, 26), trim=GOLD, rim=0.5, label=None)
    figure(c, cx + 140, cy + 130, 0.78, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.5)
    # 车轮
    for wx in (cx - 220, cx + 220):
        c.drawCircle(wx, cy + 300, 110, paint((40, 26, 16), 1, stroke=14))
        for k in range(12):
            a_ = k * math.pi / 6 + t * 0.6
            c.drawLine(wx, cy + 300, wx + math.cos(a_) * 104, cy + 300 + math.sin(a_) * 104, paint((60, 40, 24), 1, stroke=4))
        c.drawCircle(wx, cy + 300, 16, paint(GOLD, 0.9))
    c.restore()
    vignette(c, 0.65, 0.4)
    a1 = ramp(t, lt(S, 1) + 0.6, 0.5)
    draw_text(c, "出则同舆", W / 2 - 200, 300, 64, GOLD_HI, a1, "serif", True, "center", stroke=5, shadow=10)
    draw_text(c, "坐则同席", W / 2 + 200, 300, 64, GOLD_HI, ramp(t, lt(S, 1) + 1.6, 0.5), "serif", True, "center", stroke=5, shadow=10)
    draw_text(c, "曹操", cx - 140, cy + 280, 36, GOLD, ramp(t, 0.3, 0.5), "serif", True, "center", stroke=5)
    draw_text(c, "刘备", cx + 140, cy + 280, 36, RED_HI, ramp(t, 0.3, 0.5), "serif", True, "center", stroke=5)


# ───────────────────────── D 金印 ─────────────────────────
def v_seal(c, S, t):
    c.clear(skia.Color4f(0.04, 0.035, 0.03, 1))
    grad_rect(c, 0, 0, W, H, (30, 22, 14), 1, (6, 5, 4), 1)
    r = np.random.default_rng(9)
    # 金尘
    xy = np.stack([r.uniform(0, W, 140), (r.uniform(0, H, 140) - t * r.uniform(10, 40, 140)) % H], 1)
    Swarm.draw(c, xy, GOLD, 0.35, r=1.6)
    drop = ease_out(t / 1.0)
    sy = lerp(260, 640, drop)
    te = cue(S, "empty")
    shrink = ramp(t, te, 0.8)
    sx = lerp(W / 2, W / 2, shrink); s_ = lerp(1.7, 1.15, shrink)
    seal(c, sx, sy - 90 * shrink, s_, 1, glow=0.8 + 0.2 * math.sin(t * 2))
    draw_text(c, "左将军", W / 2, 960 - 90 * shrink, 70, GOLD_HI, ramp(t, 0.6, 0.5), "serif", True, "center", stroke=5, shadow=12, spacing=18)
    draw_text(c, "以天子名义授予 · 有印有绶", W / 2, 1030 - 90 * shrink, 36, (230, 220, 200), ramp(t, 1.4, 0.5) * (1 - shrink), "sans", False, "center")
    # 二十年时间轴
    tw = cue(S, "twenty")
    if t > tw - 0.1:
        a = ramp(t, tw, 0.5) * (1 - ramp(t, te, 0.5))
        y = 1150; x0, x1 = 140, 940
        c.drawLine(x0, y, x0 + (x1 - x0) * ease((t - tw) / 2.0), y, paint(GOLD, a, stroke=6))
        draw_text(c, "199", x0, y + 60, 44, GOLD_HI, a, "serif", True, "center")
        draw_text(c, "219", x1, y + 60, 44, GOLD_HI, a * ramp(t, tw + 1.8, 0.4), "serif", True, "center")
        draw_text(c, "二十年", W / 2, y - 30, 56, WHITE, a * ramp(t, tw + 1.0, 0.4), "serif", True, "center", stroke=5)
    # 空：没有地盘、没有自己的军队
    if t > te - 0.1:
        a = ramp(t, te + 0.3, 0.5) * (1 - ramp(t, cue(S, "ask") - 0.2, 0.5))
        for k, (lab, val) in enumerate([("地盘", "无"), ("自己的军队", "无")]):
            y = 1040 + k * 100
            rrect(c, 200, y - 56, 680, 80, 8, paint((255, 255, 255), 0.06 * a))
            draw_text(c, lab, 240, y, 46, (220, 214, 200), a, "sans", True)
            draw_text(c, val, 840, y, 54, (230, 90, 70), a * ramp(t, te + 0.8 + k * 0.5, 0.3), "serif", True, "right")
    ta = cue(S, "ask")
    if t > ta - 0.1:
        a = ramp(t, ta, 0.4)
        big_text(c, "空头上将衔，", 1120, 74, WHITE, a)
        big_text(c, "有什么用？", 1220, 74, GOLD_HI, a)
    vignette(c, 0.6, 0.4)


# ───────────────────────── E 196 年徐州 ─────────────────────────
YS = (160, 136, 176)  # 袁术：冷紫灰


def v_map196(c, S, t):
    k0 = Cam(117.9, 33.9, 4.6, ay=840)
    k1 = Cam(118.1, 33.7, 3.6, ay=840)
    k2 = Cam(116.4, 34.1, 6.0, ay=840)
    tx = cue(S, "toxu")
    cam = Cam.lerp(Cam.lerp(k0, k1, ease(t / 14)), k2, ease((t - tx) / 2.5))
    draw_map(c, cam)
    map_note(c)
    year_tag(c, "196", ramp(t, 0, 0.5), "建安元年")
    P_ = lambda n: pl(cam, n)
    city(c, *P_("下邳"), "下邳", 1, PAPER, major=True)
    city(c, *P_("小沛"), "小沛", 1, PAPER, side="up")
    city(c, *P_("彭城"), "彭城", 0.8, PAPER, side="left", r=7, size=28)
    city(c, *P_("盱眙"), "盱眙", ramp(t, cue(S, "yuanshu"), 0.5), PAPER, side="left")
    city(c, *P_("淮阴"), "淮阴", ramp(t, cue(S, "yuanshu"), 0.5), PAPER)
    city(c, *P_("寿春"), "寿春", ramp(t, cue(S, "yuanshu"), 0.5), YS, side="left")
    city(c, *P_("许"), "许", ramp(t, tx, 0.5), GOLD_HI, major=True, side="up")
    # 徐州范围光晕
    txz = cue(S, "xuzhou")
    xp = P_("下邳")
    ga = fade_win(t, txz, cue(S, "lvbu") + 1.5, 0.5, 0.8)
    c.drawCircle(*xp, 210 * (cam.px_per_deg() / 235), paint(RED, 0.28 * ga, blur=60))
    draw_text(c, "徐州", xp[0] + 60, xp[1] - 120, 60, RED_HI, ga, "serif", True, stroke=6)
    # 袁术北上 vs 刘备南下
    ty = cue(S, "yuanshu")
    if t > ty:
        pr = ease((t - ty) / 1.8)
        a_r = 1 - ramp(t, cue(S, "lvbu") + 2.5, 0.8)
        draw_arrow(c, curve_pts([xp, P_("盱眙")], 30, 0.1), pr, RED, 30, a_r)
        draw_arrow(c, curve_pts([P_("寿春"), (P_("盱眙")[0] - 30, P_("盱眙")[1] + 30)], 30, -0.1), pr, YS, 30, a_r)
        sw = Swarm(160, 3, 30, 22)
        xy, _ = sw.pos(xp, (P_("盱眙")[0] + 30, P_("盱眙")[1] - 20), pr, t)
        Swarm.draw(c, xy, RED_HI, 0.8 * a_r, 3)
        sw2 = Swarm(160, 4, 30, 22)
        xy2, _ = sw2.pos(P_("寿春"), (P_("盱眙")[0] - 50, P_("盱眙")[1] + 30), pr, t)
        Swarm.draw(c, xy2, YS, 0.8 * a_r, 3)
        draw_text(c, "袁术", P_("寿春")[0], P_("寿春")[1] + 60, 40, YS, a_r * ramp(t, ty, 0.4), "serif", True, "center", stroke=5)
        draw_text(c, "相持经月", P_("盱眙")[0], P_("盱眙")[1] + 90, 36, WHITE, fade_win(t, ty + 1.8, cue(S, "lvbu") + 1, 0.4, 0.4), "sans", True, "center", stroke=5)
    # 吕布袭下邳
    tl = cue(S, "lvbu")
    flip = ramp(t, tl + 1.2, 0.3)
    flag(c, xp[0] + 6, xp[1] - 14, RED, 1 - flip, 1.4, t)
    flag(c, xp[0] + 6, xp[1] - 14, BLUE, flip, 1.4, t, "呂")
    if t > tl:
        sp = P_("小沛")
        draw_arrow(c, curve_pts([sp, xp], 30, -0.2), ease((t - tl) / 1.2), BLUE, 34, 1 - ramp(t, cue(S, "xiaopei"), 0.6))
        if t > tl + 1.2:
            c.drawCircle(*xp, 26 + 120 * ease_out((t - tl - 1.2) / 1.0), paint(BLUE_HI, 0.8 * (1 - ramp(t, tl + 1.2, 1.0)), stroke=6))
            draw_text(c, "曹豹倒戈", xp[0] + 40, xp[1] + 80, 42, BLUE_HI, fade_win(t, tl + 1.3, cue(S, "xiaopei"), 0.3, 0.4), "serif", True, stroke=5)
    # 刘备去小沛
    tp = cue(S, "xiaopei")
    if t > tp:
        sp = P_("小沛")
        pr = ease((t - tp) / 1.6)
        rx = lerp(P_("盱眙")[0], sp[0], pr); ry = lerp(P_("盱眙")[1], sp[1], pr)
        c.drawCircle(rx, ry, 16, paint(RED_HI, 0.9)); c.drawCircle(rx, ry, 30, paint(RED, 0.4, blur=10))
    ta = cue(S, "attack")
    if t > ta:
        sp = P_("小沛")
        sw = Swarm(220, 8, 26, 34)
        xy, _ = sw.pos(sp, sp, 1, t, jitter=4)
        Swarm.draw(c, xy, RED_HI, 0.8 * (1 - ramp(t, tx + 0.6, 0.8)), 2.6)
        draw_text(c, "又聚万余人", sp[0], sp[1] - 70, 38, RED_HI, fade_win(t, ta + 0.2, tx, 0.3, 0.3), "serif", True, "center", stroke=5)
        draw_arrow(c, curve_pts([xp, (sp[0] + 20, sp[1] + 10)], 30, 0.25), ease((t - ta - 1.4) / 1.4), BLUE, 36, 1)
    if t > tx:
        pts = curve_pts([P_("小沛"), P_("许")], 50, -0.12)
        draw_dashed(c, pts, ease((t - tx) / 2.2), RED_HI, 8, 1, phase=-t * 40)


# ───────────────────────── F 程昱进言 ─────────────────────────
def ink_ring(c, x, y, rad, a, seed=1, color=(6, 6, 6)):
    r = np.random.default_rng(seed)
    for k in range(40):
        ang = k / 40 * 6.283 + r.uniform(-0.1, 0.1)
        rr = rad * r.uniform(0.85, 1.2)
        c.drawCircle(x + math.cos(ang) * rr, y + math.sin(ang) * rr, r.uniform(40, 90), paint(color, 0.55 * a, blur=30))


def v_chengyu(c, S, t):
    c.clear(skia.Color4f(0.83, 0.79, 0.70, 1))
    grad_rect(c, 0, 0, W, H, (214, 200, 172), 1, (150, 132, 104), 1)
    c.drawImage(noise_img(W // 3, H // 3, 4, alpha=0.12), 0, 0)
    cx, cy = W / 2, 820
    t3 = lt(S, 2)
    threat = ramp(t, 0.3, 1.5) * (1 - ramp(t, t3 + 0.5, 1.5))
    ink_ring(c, cx, cy, lerp(520, 250, threat), threat, 3)
    # 金色护身光环
    halo = ramp(t, lt(S, 3), 1.0)
    if halo > 0:
        c.drawCircle(cx, cy - 40, 260, paint(GOLD_HI, 0.5 * halo, stroke=10, blur=6))
        c.drawCircle(cx, cy - 40, 300 + 10 * math.sin(t * 2), paint(GOLD, 0.35 * halo, blur=40))
    figure(c, cx - 10, cy + 200, 0.95, 1, robe=(110, 30, 24), trim=(240, 170, 120), rim=0.2)
    draw_text(c, "刘备", cx, cy + 290, 44, (120, 30, 20), 1, "serif", True, "center")
    # 两个关键词
    draw_text(c, "早图之", cx, 330, 96, (20, 18, 16), threat, "tc", True, "center", spacing=20)
    draw_text(c, "收英雄", cx, 330, 96, (150, 40, 28), ramp(t, t3 + 0.6, 0.6) * (1 - ramp(t, lt(S, 3) - 0.3, 0.5)), "tc", True, "center", spacing=20)
    big_text(c, "名望 = 护身符", 330, 78, (140, 96, 30), halo, "serif", True, stroke=0)
    draw_text(c, "程昱 进言", 80, 230, 36, (40, 34, 28), ramp(t, 0.2, 0.4) * (1 - ramp(t, t3, 0.4)), "sans", True)
    draw_text(c, "曹操 答", 80, 230, 36, (40, 34, 28), ramp(t, t3, 0.4), "sans", True)


# ───────────────────────── G 天子在许 ─────────────────────────
def v_emperor(c, S, t):
    cam = Cam.lerp(Cam(111.0, 34.4, 9.0, ay=820), Cam(113.0, 34.6, 12.0, ay=840), ease((t - cue(S, "decrees")) / 3))
    draw_map(c, cam)
    map_note(c)
    year_tag(c, "196", 1, "建安元年 · 天子都许")
    xu = pl(cam, "许"); ly = pl(cam, "洛阳"); ca = pl(cam, "长安")
    city(c, *ly, "洛阳", 1, PAPER, side="up")
    city(c, *ca, "长安", 1, PAPER, side="up")
    pts = curve_pts([ly, xu], 40, 0.2)
    pe = draw_dashed(c, pts, ease((t - 0.3) / 2.5), (240, 200, 90), 7, 1, phase=-t * 30)
    if pe:
        (px, py), _ = pe
        c.drawCircle(px, py, 22, paint(GOLD_HI, 0.9)); c.drawCircle(px, py, 40, paint(GOLD_HI, 0.4, blur=14))
    glow = ramp(t, 2.6, 0.8)
    c.drawCircle(*xu, 70 + 6 * math.sin(t * 2), paint(GOLD_HI, 0.45 * glow, blur=30))
    city(c, *xu, "许", 1, GOLD_HI, major=True, size=44, side="right")
    draw_text(c, "天子", xu[0], xu[1] + 70, 38, GOLD_HI, glow, "serif", True, "center", stroke=5)
    # 诏书四出
    td = cue(S, "decrees")
    if t > td:
        targets = [(-1, -0.6), (1, -0.5), (1, 0.4), (-0.4, 0.9), (0.4, 1), (-1, 0.3), (0, -1)]
        for k, (dx, dy) in enumerate(targets):
            f = ((t - td) * 0.45 + k * 0.13) % 1.0
            x = xu[0] + dx * 380 * f; y = xu[1] + dy * 380 * f
            scroll_icon(c, x, y, 0.9, (1 - f) * ramp(t, td, 0.5) * (1 - ramp(t, cue(S, "biao") - 0.3, 0.5)))
    # 表/诏 循环示意
    tb = cue(S, "biao")
    if t > tb:
        a = ramp(t, tb, 0.5)
        rx = [(xu[0] - 330, xu[1] - 260), (xu[0] + 300, xu[1] - 300), (xu[0] + 320, xu[1] + 260)]
        for k, p in enumerate(rx):
            pr = ease((t - tb - k * 0.25) / 1.2)
            draw_arrow(c, curve_pts([p, (xu[0] + (p[0] - xu[0]) * 0.18, xu[1] + (p[1] - xu[1]) * 0.18)], 20, 0.15), pr, (200, 200, 200), 14, a, glow=False)
            draw_arrow(c, curve_pts([(xu[0] + (p[0] - xu[0]) * 0.18, xu[1] + (p[1] - xu[1]) * 0.18 + 30), (p[0], p[1] + 30)], 20, 0.15), ease((t - tb - 1.2 - k * 0.25) / 1.2), GOLD_HI, 14, a, glow=False)
        draw_text(c, "上表 →", W / 2, 1210, 46, (220, 220, 220), a, "serif", True, "center", stroke=5)
        draw_text(c, "← 下诏", W / 2, 1280, 46, GOLD_HI, ramp(t, tb + 1.2, 0.5), "serif", True, "center", stroke=5)
        tbl = tb + (S["lines"][-2]["t0"] - S["lines"][-3]["t0"])
        draw_text(c, "李傕、郭汜", ca[0], ca[1] + 70, 36, (200, 120, 110), fade_win(t, tbl, tbl + 6, 0.4, 0.6), "serif", True, "center", stroke=5)


# ───────────────────────── H 下邳之围 ─────────────────────────
SISHUI = [(116.9, 35.1), (117.05, 34.75), (117.18, 34.26), (117.6, 34.22), (117.95, 34.27), (118.3, 33.9), (118.6, 33.6), (118.95, 33.45)]
YISHUI = [(118.65, 35.6), (118.45, 35.1), (118.25, 34.7), (117.98, 34.32)]


def river_path(cam, pts, c, a=1.0, w=6):
    sp = curve_pts([cam.p(*p) for p in pts], 12, 0.05)
    path = skia.Path(); path.moveTo(*sp[0])
    for p in sp[1:]:
        path.lineTo(*p)
    c.drawPath(path, paint((70, 120, 160), 0.5 * a, stroke=w * 2.5, blur=w))
    c.drawPath(path, paint((120, 170, 210), a, stroke=w))
    return sp


def v_xiapi(c, S, t):
    tm, tsg, tfl, tcl, tcap = cue(S, "march"), cue(S, "siege"), cue(S, "flood"), cue(S, "collapse"), cue(S, "capture")
    k0 = Cam(117.3, 34.4, 3.4, ay=840)
    k1 = Cam(117.75, 34.3, 2.2, ay=840)
    k2 = Cam(117.9, 34.25, 1.9, ay=800)
    cam = Cam.lerp(Cam.lerp(k0, k1, ease((t - tm) / 4)), k2, ease((t - tsg) / 4))
    shake = 0
    if tfl < t < tcl + 3:
        shake = 2.5 * math.sin(t * 40) * math.exp(-((t - tfl) % 4))
    c.save(); c.translate(shake, 0)
    draw_map(c, cam)
    c.restore()
    map_note(c)
    year_tag(c, "198", 1, "建安三年 · 下邳之围")
    xp = pl(cam, "下邳"); xs = pl(cam, "小沛"); pc = pl(cam, "彭城"); lg = pl(cam, "梁国")
    # 泗水、沂水
    ra = ramp(t, tsg - 1, 1.0)
    if ra > 0:
        sp1 = river_path(cam, SISHUI, c, ra)
        river_path(cam, YISHUI, c, ra)
        draw_text(c, "泗水", *pl(cam, "彭城"), 0, "serif") if False else None
        p1 = cam.p(117.6, 34.15); p2 = cam.p(118.3, 34.75)
        draw_text(c, "泗水", p1[0], p1[1] + 40, 34, (150, 200, 235), ra, "serif", True, "center", stroke=4)
        if p2[1] > 360:
            draw_text(c, "沂水", p2[0] + 40, p2[1], 34, (150, 200, 235), ra, "serif", True, stroke=4)
    # 水淹
    if t > tfl:
        fr = ease((t - tfl) / 5.0)
        rr = np.random.default_rng(2)
        R = cam.px_per_deg() * 0.3 * fr
        for k in range(26):
            ang = k / 26 * 6.283
            rad = R * rr.uniform(0.6, 1.3)
            x = xp[0] + math.cos(ang) * rad * 0.8; y = xp[1] + math.sin(ang) * rad * 0.6
            c.drawCircle(x, y, R * 0.55, paint((60, 110, 150), 0.38 * fr, blur=R * 0.25))
        for k in range(5):
            f = ((t - tfl) * 0.4 + k / 5) % 1.0
            c.drawOval(skia.Rect.MakeXYWH(xp[0] - R * f * 1.2, xp[1] - R * f * 0.8, R * f * 2.4, R * f * 1.6), paint((180, 220, 250), 0.35 * (1 - f) * fr, stroke=3))
        draw_text(c, "决泗、沂水灌城", W / 2, 420, 58, (160, 210, 245), fade_win(t, tfl + 0.6, tfl + 9, 0.5, 0.6), "serif", True, "center", stroke=6, shadow=10)
    city(c, *xp, "下邳", 1, PAPER, major=True, size=44)
    city(c, *xs, "小沛", ramp(t, 0, 0.5) * (1 - ramp(t, tsg, 1)), PAPER, side="up")
    city(c, *pc, "彭城", 1 - ramp(t, tsg, 1), PAPER, side="left", r=7, size=28)
    # 高顺攻小沛
    tg = 0.3
    if t < tsg + 1:
        pr = ease((t - tg) / 1.6)
        draw_arrow(c, curve_pts([xp, xs], 30, -0.2), pr, BLUE, 32, 1 - ramp(t, tm, 0.6))
        if t > 2.0:
            sw = Swarm(120, 21, 20, 70)
            xy, _ = sw.pos(xs, (xs[0] - 120, xs[1] - 40), ease((t - 2.0) / 2), t)
            Swarm.draw(c, xy, RED_HI, 0.8 * (1 - ramp(t, tm, 0.8)), 2.6)
    # 曹军 + 刘备 东征
    n_b, n_r, n_bl = 520, 160, 280
    swB = Swarm(n_b, 31, 60, 20); swR = Swarm(n_r, 32, 40, 20); swL = Swarm(n_bl, 33, 14, 14)
    ring_r = cam.px_per_deg() * 0.2
    # 敌军（蓝）：城内外
    blue_a = 1.0
    if t < tcl:
        xyL, _ = swL.pos(xp, xp, 1, t, jitter=2 + 3 * ramp(t, tfl + 3, 2) * abs(math.sin(t * 3)))
        # 城内收缩
        xyL = xp + (xyL - xp) * lerp(2.2, 0.9, ramp(t, tsg, 2))
        Swarm.draw(c, xyL, BLUE_HI, blue_a * (0.9 - 0.35 * ramp(t, tfl + 4, 6) * (0.5 + 0.5 * math.sin(t * 9))), 2.6)
    else:
        # 溃散：向四周散开、变暗
        xyL, _ = swL.pos(xp, xp, 1, t, jitter=2)
        f = ease_out((t - tcl) / 2.5)
        d = (xyL - xp)
        nrm = np.linalg.norm(d, axis=1, keepdims=True) + 1e-3
        xyL = xp + d / nrm * (nrm * 0.9 + f * cam.px_per_deg() * 0.25 * (0.5 + np.random.default_rng(4).uniform(0, 1, (n_bl, 1))))
        Swarm.draw(c, xyL, BLUE_HI, 0.9 * (1 - f * 0.85), 2.4)
    if t > tm:
        pr = ease((t - tm) / 5.0)
        ang = np.linspace(0, 6.283, n_b, endpoint=False)
        ringB = np.stack([xp[0] + np.cos(ang) * ring_r * 1.6, xp[1] + np.sin(ang) * ring_r * 1.2], 1)
        start = np.array(lg) if lg[0] > -2000 else np.array([xp[0] - 800, xp[1]])
        f = np.clip((pr - swB.delay) / 0.65, 0, 1); f = f * f * (3 - 2 * f)
        pre = ramp(t, tsg, 3.0)
        mid = np.array([(start[0] + xp[0]) / 2, (start[1] + xp[1]) / 2])
        tgtB = mid + swB.o0 * 1.6
        tgtB = tgtB * (1 - pre) + (ringB + swB.o0 * 0.35) * pre
        xyB = start + swB.o0 + (tgtB - start - swB.o0) * f[:, None]
        xyB += np.stack([np.sin(t * 3 + swB.ph), np.cos(t * 2.6 + swB.ph)], 1) * 2.5
        if t > tcl + 0.5:
            xyB = xyB + (np.array(xp) - xyB) * ease((t - tcl - 0.5) / 3) * 0.55
        Swarm.draw(c, xyB, (14, 12, 12), 1, 4.4, glow=False)
        Swarm.draw(c, xyB, GOLD, 0.55, 2.0, glow=False)
        angR = np.linspace(0.6, 2.4, n_r)
        ringR = np.stack([xp[0] + np.cos(angR + 2.2) * ring_r * 1.75, xp[1] + np.sin(angR + 2.2) * ring_r * 1.3], 1)
        fR = np.clip((pr - swR.delay) / 0.65, 0, 1); fR = fR * fR * (3 - 2 * fR)
        tgtR = (mid + swR.o0) * (1 - pre) + (ringR + swR.o0 * 0.4) * pre
        xyR = start + np.array([0, 40]) + swR.o0 + (tgtR - start - swR.o0) * fR[:, None]
        Swarm.draw(c, xyR, RED_HI, 1, 3.0)
        # 粗箭头
        aa = 1 - ramp(t, tsg + 2, 1.0)
        draw_arrow(c, curve_pts([(start[0], start[1] - 30), (xp[0] - ring_r * 2.2, xp[1] - 20)], 30, -0.1), ease((t - tm) / 2.2), (40, 38, 40), 46, aa)
        draw_arrow(c, curve_pts([(start[0], start[1] + 60), (xp[0] - ring_r * 2.0, xp[1] + 70)], 30, 0.12), ease((t - tm - 0.3) / 2.2), RED, 30, aa)
        banner(c, start[0] + 70, start[1] - 260, "曹", (30, 28, 30), ramp(t, tm, 0.5) * aa, 44)
        banner(c, start[0] + 150, start[1] - 200, "劉", RED, ramp(t, tm + 0.3, 0.5) * aa, 38)
    # 围城：箭雨 + 烟
    if tsg < t < tcl + 1:
        a = ramp(t, tsg + 1, 1) * (1 - ramp(t, tcl, 1))
        r = np.random.default_rng(int(t * 6))
        for k in range(28):
            ang = r.uniform(0, 6.283)
            f = (t * 1.4 + k * 0.137) % 1.0
            sx = xp[0] + math.cos(ang) * ring_r * 1.6; sy = xp[1] + math.sin(ang) * ring_r * 1.2
            x = lerp(sx, xp[0], f); y = lerp(sy, xp[1], f) - math.sin(f * math.pi) * 40
            c.drawLine(x, y, x + (xp[0] - sx) * 0.04, y + (xp[1] - sy) * 0.04, paint((230, 220, 200), 0.6 * a, stroke=2))
        smoke(c, xp[0], xp[1] - 20, t, 5, 8, 50, 0.3 * a)
    # 援军不至
    tcu = cue(S, "cutoff")
    if t > tcu:
        ss = pl(cam, "寿春")
        p_end = (xp[0] + (ss[0] - xp[0]) * 0.45, xp[1] + (ss[1] - xp[1]) * 0.45)
        sp = (min(max(ss[0], xp[0] - 100), W + 100), min(ss[1], H + 200))
        draw_dashed(c, curve_pts([(W + 40, xp[1] + 120), (xp[0] + 260, xp[1] + 90)], 20, 0.1), ease((t - tcu) / 1.5), YS, 7, 1 - ramp(t, tcl, 0.5))
        xmark(c, xp[0] + 250, xp[1] + 90, ramp(t, tcu + 1.3, 0.3) * (1 - ramp(t, tcl, 0.5)), 1.3)
        draw_text(c, "袁术援兵不至", xp[0] + 250, xp[1] + 20, 38, YS, fade_win(t, tcu + 1.0, tcl, 0.3, 0.4), "serif", True, "center", stroke=5)
    tmr = cue(S, "morale")
    if t > tmr:
        draw_text(c, "看不到解围的希望", W / 2, 420, 54, BLUE_HI, fade_win(t, tmr + 0.4, tcl, 0.4, 0.4), "serif", True, "center", stroke=6, shadow=10)
    # 城破易帜
    flip = ramp(t, tcl + 1.2, 0.3)
    flag(c, xp[0] + 8, xp[1] - 18, BLUE, 1 - flip, 1.5, t, "呂")
    flag(c, xp[0] + 8, xp[1] - 18, (30, 28, 30), flip, 1.5, t, "曹")
    if t > tcl:
        draw_text(c, "宋宪、魏续缚陈宫 · 举城降", W / 2, 420, 48, WHITE, fade_win(t, tcl + 0.3, tcap, 0.4, 0.4), "serif", True, "center", stroke=6, shadow=10)
    if t > tcap:
        big_text(c, "生擒吕布", 430, 84, GOLD_HI, ramp(t, tcap, 0.4))


# ───────────────────────── I 起家三问卡 ─────────────────────────
def sanwen_card(c, S, t, y0=360):
    q = [("手里有什么", "关羽、张飞，收拢的散兵（人数史书无载）\n名号：豫州牧、左将军"),
         ("借了谁的势", "曹操手里的天子：名号由曹操「表」请，\n盖的是汉朝廷的印"),
         ("做对了哪一步", "寄人篱下，不争兵、不争地，\n先把朝廷正式授予的名号拿到手")]
    a = ramp(t, 0, 0.5)
    x = 60; w = 960; h = 1100
    rrect(c, x + 6, y0 + 10, w, h, 12, paint((0, 0, 0), 0.5 * a, blur=20))
    rrect(c, x, y0, w, h, 12, paint((16, 12, 10), 0.92 * a))
    rrect(c, x, y0, w, h, 12, paint(GOLD, 0.9 * a, stroke=2.5))
    draw_text(c, "起家三问", x + 50, y0 + 100, 66, GOLD_HI, a, "serif", True, spacing=10)
    draw_text(c, "公元 199 年 · 许都", x + w - 50, y0 + 96, 34, (220, 206, 180), a, "sans", False, "right")
    c.drawLine(x + 50, y0 + 140, x + w - 50, y0 + 140, paint(GOLD, 0.5 * a, stroke=1.5))
    keys = ["q1", "q2", "q3"]
    for k, (qq, ans) in enumerate(q):
        tk = cue(S, keys[k])
        on = ramp(t, tk, 0.5)
        yy = y0 + 200 + k * 300
        act = on * (1 - (ramp(t, cue(S, keys[k + 1]), 0.5) * 0.45 if k < 2 else 0))
        rrect(c, x + 36, yy - 30, w - 72, 270, 10, paint(RED if k == 0 else GOLD if k == 1 else (200, 120, 60), 0.12 * act))
        c.drawCircle(x + 90, yy + 30, 34, paint(GOLD, 0.9 * a, stroke=3))
        draw_text(c, "一二三"[k], x + 90, yy + 46, 40, GOLD_HI, a, "serif", True, "center")
        draw_text(c, qq, x + 150, yy + 46, 52, WHITE, a * (0.5 + 0.5 * on), "serif", True)
        for j, ln in enumerate(ans.split("\n")):
            draw_text(c, ln, x + 150, yy + 120 + j * 56, 38, (236, 226, 206), on, "sans")


def v_sanwen(c, S, t):
    cam = Cam(115.5, 34.2, 7.0, ay=900)
    draw_map(c, cam, grade=0.25)
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.35))
    seal(c, 880, 260, 0.6, ramp(t, 0.3, 0.5), glow=0.5)
    sanwen_card(c, S, t)


# ───────────────────────── J 类比 ─────────────────────────
def v_analogy(c, S, t):
    c.clear(skia.Color4f(0.04, 0.05, 0.06, 1))
    grad_rect(c, 0, 0, W, H, (18, 24, 32), 1, (6, 7, 9), 1)
    # 空的指挥沙盘：网格 + 无兵
    gp = paint((120, 150, 180), 0.18, stroke=1.2)
    for k in range(0, W + 1, 60):
        c.drawLine(k, 300, k, 960, gp)
    for k in range(300, 961, 60):
        c.drawLine(0, k, W, k, gp)
    seal(c, W / 2, 560, 1.25, 1, glow=0.6 + 0.2 * math.sin(t * 2))
    a = ramp(t, lt(S, 1), 0.5)
    for k, s in enumerate(["防区：无", "部队：无", "指挥部：无"]):
        draw_text(c, s, W / 2 + (k - 1) * 320, 860, 40, (180, 200, 220), a * ramp(t, lt(S, 1) + 0.4 + k * 0.4, 0.3), "sans", True, "center")
    vignette(c, 0.6, 0.4)


# ───────────────────────── K 名号满天飞 ─────────────────────────
def v_titles(c, S, t):
    c.clear(skia.Color4f(0.05, 0.04, 0.035, 1))
    grad_rect(c, 0, 0, W, H, (36, 26, 18), 1, (8, 6, 5), 1)
    tags = ["自领州牧", "互相表奏", "某某将军", "某州刺史", "称帝", "某郡太守", "自号将军", "表某为牧", "领某州", "中郎将"]
    r = np.random.default_rng(12)
    tg, tgold, tys = cue(S, "gold"), cue(S, "gold"), cue(S, "yuanshao")
    chaos_a = ramp(t, 0.2, 0.6) * (1 - ramp(t, tys, 0.6))
    for k in range(26):
        s = tags[k % len(tags)]
        x = r.uniform(80, 1000) + math.sin(t * r.uniform(0.3, 0.8) + k) * 40
        y = r.uniform(300, 1000) + math.cos(t * r.uniform(0.3, 0.8) + k) * 30
        dim = 1 - 0.7 * ramp(t, tgold, 0.8)
        draw_text(c, s, x, y, r.uniform(30, 52), (200, 190, 170), chaos_a * dim * r.uniform(0.4, 0.9), "serif", False, "center")
    ts = cue(S, "selfmade")
    if ts < t < tys:
        draw_text(c, "袁术 · 自己称帝", W / 2, 1120, 52, YS, fade_win(t, ts + 2.5, tgold, 0.4, 0.4), "serif", True, "center", stroke=5)
    if t > tgold:
        ga = ramp(t, tgold, 0.6) * (1 - ramp(t, tys, 0.6))
        seal(c, W / 2, 650, 1.3, ga, glow=1.0)
        draw_text(c, "天子正授 · 各方不得不认", W / 2, 900, 46, GOLD_HI, ga, "serif", True, "center", stroke=5)
        draw_text(c, "= 稀缺的硬通货", W / 2, 970, 46, GOLD_HI, ga * ramp(t, tgold + 1, 0.4), "serif", True, "center", stroke=5)
    tq = lt(S, 3) - 0.0
    if t > tys - 0.1:
        a = ramp(t, tys, 0.6)
        # 座次梯：大将军 > 太尉
        x0 = 240
        for k, (rank, who, colr) in enumerate([("大将军", "曹操", GOLD), ("太尉", "袁绍", YELLOW)]):
            y = 420 + k * 190
            rrect(c, x0, y, 600, 140, 10, paint((255, 255, 255), 0.06 * a))
            rrect(c, x0, y, 600, 140, 10, paint(colr, 0.8 * a, stroke=2))
            draw_text(c, rank, x0 + 40, y + 90, 56, WHITE, a, "serif", True)
        sw = ease((t - lt(S, 4)) / 1.2)
        for k, (who, colr) in enumerate([("曹操", GOLD), ("袁绍", YELLOW)]):
            y0 = 420 + k * 190; y1 = 420 + (1 - k) * 190
            y = lerp(y0, y1, sw)
            draw_text(c, who, x0 + 560, y + 90, 54, colr, a, "serif", True, "right", stroke=4)
        draw_text(c, "「耻班在公下」", W / 2, 860, 58, YELLOW, ramp(t, tys + 2.5, 0.5), "tc", True, "center", stroke=5)
        draw_text(c, "→ 大将军让给袁绍", W / 2, 940, 44, WHITE, ramp(t, lt(S, 4), 0.5), "serif", True, "center", stroke=5)
    vignette(c, 0.6, 0.4)


# ───────────────────────── L 二十年 ─────────────────────────
def v_seal219(c, S, t):
    c.clear(skia.Color4f(0.04, 0.035, 0.03, 1))
    grad_rect(c, 0, 0, W, H, (30, 22, 14), 1, (6, 5, 4), 1)
    x0, x1, y = 110, 970, 360
    yrs = [(199, "拜左将军"), (211, "入益州"), (219, "汉中王")]
    pr = ease(t / 3.5)
    c.drawLine(x0, y, x0 + (x1 - x0) * pr, y, paint(GOLD, 0.9, stroke=5))
    for k, (yr, lab) in enumerate(yrs):
        f = (yr - 199) / 20
        x = x0 + (x1 - x0) * f
        a = ramp(t, f * 3.5, 0.4)
        c.drawCircle(x, y, 10, paint(GOLD_HI, a))
        draw_text(c, str(yr), x, y - 30, 32, GOLD_HI, a, "serif", True, "center")
        draw_text(c, lab, x, y + 56, 30, WHITE, a, "sans", True, "center")
    sx = x0 + (x1 - x0) * pr
    seal(c, sx, y + 150, 0.55, 1, glow=0.6)
    # 头衔清单
    tl = cue(S, "list")
    items = ["左将军", "领司隶校尉", "豫州牧", "荆州牧", "益州牧", "宜城亭侯"]
    for k, it in enumerate(items):
        a = ramp(t, tl + 1.0 + k * 0.5, 0.4) * (1 - ramp(t, lt(S, 1) - 0.4, 0.5))
        hl = k == 0
        draw_text(c, it, W / 2, 700 + k * 70, 52 if hl else 42, GOLD_HI if hl else (220, 214, 200), a, "serif", True, "center", stroke=4)
    ts = cue(S, "span")
    if t > ts:
        big_text(c, "199 → 219", 760, 96, GOLD_HI, ramp(t, ts, 0.5))
        big_text(c, "整整二十年", 870, 66, WHITE, ramp(t, ts + 0.6, 0.5))
    vignette(c, 0.6, 0.4)


# ───────────────────────── M 衣带诏 ─────────────────────────
def v_plot(c, S, t):
    c.clear(skia.Color4f(0.03, 0.025, 0.02, 1))
    grad_rect(c, 0, 0, W, H, (24, 14, 10), 1, (4, 3, 2), 1)
    # 宫门剪影
    for k in range(2):
        x = 160 + k * 560
        c.drawRect(skia.Rect.MakeXYWH(x, 260, 200, 900), paint((50, 16, 10)))
        for j in range(5):
            for i in range(3):
                c.drawCircle(x + 45 + i * 55, 340 + j * 90, 10, paint(GOLD, 0.6))
    # 衣带展开
    t1 = lt(S, 1)
    pr = ease((t - t1) / 2.2)
    cx, cy = W / 2, 720
    band = skia.Path()
    L = 760 * pr
    band.moveTo(cx - 380, cy)
    for k in range(40):
        x = cx - 380 + L * k / 39
        band.lineTo(x, cy + math.sin(k * 0.4 + t * 1.5) * 14)
    for k in range(39, -1, -1):
        x = cx - 380 + L * k / 39
        band.lineTo(x, cy + 70 + math.sin(k * 0.4 + t * 1.5) * 14)
    band.close()
    c.drawPath(band, paint((120, 30, 22), 0.95))
    c.drawPath(band, paint(GOLD, 0.7, stroke=2))
    if pr > 0.6:
        g = ramp(t, t1 + 1.6, 0.8)
        c.drawCircle(cx, cy + 35, 120, paint(GOLD_HI, 0.35 * g, blur=40))
        scroll_icon(c, cx, cy + 35, 1.8, g)
        draw_text(c, "密诏：诛曹", cx, cy + 210, 62, GOLD_HI, g, "serif", True, "center", stroke=6, shadow=12)
    draw_text(c, "董承", cx, 420, 56, (220, 200, 180), ramp(t, t1, 0.5), "serif", True, "center", stroke=5)
    t2 = lt(S, 2)
    if t > t2:
        figure(c, cx, 1330, 0.8, 1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.3)
        c.drawCircle(cx, 1180, 220, paint(RED, 0.18 * ramp(t, t2, 0.6), blur=60))
        draw_text(c, "刘备 卷入", cx, 1420, 46, RED_HI, ramp(t, t2, 0.5), "serif", True, "center", stroke=5)
    vignette(c, 0.7, 0.35)


# ───────────────────────── N 煮酒（史书版） ─────────────────────────
def v_banquet(c, S, t):
    tw, td = cue(S, "words"), cue(S, "drop")
    fl = 0.0
    stage_begin(c, 1.0 + 0.06 * ease(t / 20))
    room(c, t + 30, flash=0, rain=0, brightness=1)
    figure(c, 230, 1300, 1.18, 1, robe=(26, 24, 26), trim=GOLD, rim=0.4, pose="cup", hand=ease((t - tw) / 1.0))
    figure(c, 850, 1300, 1.18, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.4, pose="drop" if t > td else "rest")
    table(c)
    if t > td - 0.1:
        utensils(c, t, td + 0.2, slow=0.5)
    else:
        utensils(c, -1, 0)
    c.restore()
    vignette(c, 0.7, 0.35)
    draw_text(c, "曹操", 250, 1530, 40, GOLD, 1 - ramp(t, tw, 0.3), "serif", True, "center", stroke=5)
    draw_text(c, "刘备", 830, 1530, 40, RED_HI, 1 - ramp(t, tw, 0.3), "serif", True, "center", stroke=5)
    if t > tw - 0.2:
        a = ramp(t, tw, 0.5) * (1 - ramp(t, td - 0.3, 0.5))
        big_text(c, "今天下英雄", 300, 90, GOLD_HI, a, "tc", True, spacing=10)
        big_text(c, "唯使君與操耳", 410, 78, (240, 226, 196), a * ramp(t, tw + 0.6, 0.5), "tc", True, spacing=8)
    if t > td:
        stamp(c, "失匕箸", 900, 640, 110, ramp(t, td + 1.0, 0.12), 1 + 0.35 * (1 - ease_out((t - td - 1.0) / 0.35)))


# ───────────────────────── O 雷声与演义 ─────────────────────────
def v_thunder(c, S, t):
    th = cue(S, "thunder")
    fl = math.exp(-max(0, t - th - 0.3) * 4) if t > th + 0.3 else 0
    fl += math.exp(-max(0, t - th - 0.75) * 5) * 0.7 if t > th + 0.75 else 0
    stage_begin(c)
    room(c, t + 40, flash=min(1, fl), rain=0.8, brightness=0.9, seed=5)
    figure(c, 230, 1300, 1.18, 1, robe=(26, 24, 26), trim=GOLD, rim=0.4 + fl)
    figure(c, 850, 1300, 1.18, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.4 + fl, pose="drop")
    table(c)
    utensils(c, 100, 0)
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.25))
    vignette(c, 0.7, 0.35)
    tag_a = ramp(t, 0.3, 0.5) * (1 - ramp(t, lt(S, 2) - 0.3, 0.4))
    draw_text(c, "雷声出处：裴注引《华阳国志》", W / 2, 250, 44, (180, 200, 230), tag_a, "serif", True, "center", stroke=5)
    tY = lt(S, 2)
    if t > tY - 0.2:
        # 青梅、酒（演义元素，淡入后被划掉）
        a = ramp(t, tY, 0.5)
        x = 540
        c.drawCircle(x - 120, 330, 34, paint((120, 170, 90), 0.8 * a)); c.drawCircle(x - 80, 340, 30, paint((130, 180, 100), 0.8 * a))
        rrect(c, x + 60, 280, 60, 90, 10, paint((140, 110, 60), 0.8 * a))
        draw_text(c, "青梅  煮酒  龙", W / 2, 460, 46, (200, 200, 190), a * 0.8, "serif", True, "center")
        cross = ramp(t, lt(S, 3), 0.6)
        c.drawLine(300, 445, 300 + 480 * cross, 445, paint((230, 70, 60), 0.9, stroke=7))
        draw_text(c, "演义所加", W / 2, 530, 36, (230, 120, 100), cross, "sans", True, "center")


# ───────────────────────── P 评语的分量 ─────────────────────────
def v_rating(c, S, t):
    cam = Cam(113.5, 33.6, 14.0, ay=820)
    draw_map(c, cam, ["all"], 0.6 * ramp(t, cue(S, "spread"), 1.0))
    map_note(c)
    xu = pl(cam, "许")
    tp, tt_, tsp, tb = cue(S, "pingping"), cue(S, "top"), cue(S, "spread"), cue(S, "blade")
    # 品评：名士 → 人物 层级
    if t > tp - 0.2 and t < tsp:
        a = ramp(t, tp, 0.5) * (1 - ramp(t, tsp - 0.3, 0.5))
        rrect(c, 140, 420, 800, 330, 12, paint((10, 8, 6), 0.75 * a))
        draw_text(c, "东汉：人的分量 ≈ 名士的品评", W / 2, 500, 44, GOLD_HI, a, "serif", True, "center")
        draw_text(c, "乡里名士", 300, 640, 44, (200, 200, 190), a, "serif", True, "center")
        draw_text(c, "→", W / 2, 640, 50, WHITE, a * ramp(t, tt_, 0.4), "sans", True, "center")
        draw_text(c, "当朝第一权臣", 770, 640, 48, GOLD_HI, a * ramp(t, tt_, 0.4), "serif", True, "center", stroke=4)
        draw_text(c, "（手握天子）", 770, 700, 32, (220, 210, 190), a * ramp(t, tt_ + 0.5, 0.4), "sans", False, "center")
    if t > tsp:
        city(c, *xu, "许", 1, GOLD_HI, major=True, size=40)
        for k in range(5):
            f = ((t - tsp) * 0.35 + k / 5) % 1.0
            rr = 40 + f * 900
            c.drawCircle(*xu, rr, paint(GOLD_HI, 0.55 * (1 - f) * ramp(t, tsp, 0.5) * (1 - ramp(t, tb, 0.8)), stroke=4))
        draw_text(c, "「英雄」", xu[0], xu[1] - 70, 66, GOLD_HI, ramp(t, tsp, 0.5) * (1 - ramp(t, tb, 0.5)), "tc", True, "center", stroke=6)
    if t > tb:
        a = ramp(t, tb, 0.5)
        x, y = W / 2, 760
        R = 180 - 60 * ease((t - tb) / 1.5)
        c.drawCircle(x, y, R, paint((230, 60, 50), 0.9 * a, stroke=5))
        c.drawLine(x - R - 60, y, x - 30, y, paint((230, 60, 50), 0.9 * a, stroke=5)); c.drawLine(x + 30, y, x + R + 60, y, paint((230, 60, 50), 0.9 * a, stroke=5))
        c.drawLine(x, y - R - 60, x, y - 30, paint((230, 60, 50), 0.9 * a, stroke=5)); c.drawLine(x, y + 30, x, y + R + 60, paint((230, 60, 50), 0.9 * a, stroke=5))
        c.drawCircle(x, y, 18, paint(RED_HI, a))
        draw_text(c, "评语 = 靶子", x, 480, 66, (240, 100, 80), a, "serif", True, "center", stroke=6, shadow=10)
    tl = lt(S, len(S["lines"]) - 2)
    if t > tl:
        draw_text(c, "心里装着密诏", W / 2, 1110, 50, RED_HI, ramp(t, tl, 0.5), "serif", True, "center", stroke=6)
    vignette(c, 0.5, 0.45)


# ───────────────────────── Q 出走 ─────────────────────────
def v_escape(c, S, t):
    ty, tdd, tch, tcz, trl = cue(S, "yuanshu"), cue(S, "dead"), cue(S, "chase"), cue(S, "chezhou"), cue(S, "rally")
    cam = Cam.lerp(Cam(115.6, 33.9, 6.6, ay=820), Cam(117.2, 34.2, 4.6, ay=820), ease((t - tcz) / 3))
    draw_map(c, cam)
    map_note(c)
    year_tag(c, "199", 1, "建安四年")
    xu, xp, ss, xs = pl(cam, "许"), pl(cam, "下邳"), pl(cam, "寿春"), pl(cam, "小沛")
    city(c, *xu, "许", 1, GOLD_HI, major=True, side="left")
    city(c, *xp, "下邳", 1, PAPER, major=True)
    city(c, *xs, "小沛", 1, PAPER, side="up")
    city(c, *ss, "寿春", ramp(t, ty, 0.5), YS, side="left")
    pts = curve_pts([xu, xp], 50, -0.12)
    pe = draw_dashed(c, pts, ease((t - ty - 0.5) / 4.0), RED_HI, 8, 1, phase=-t * 40)
    if pe and t > ty + 0.5:
        (px, py), _ = pe
        seal(c, px, py - 70, 0.42, 1, glow=0.6)
    if t > ty:
        pr = ease((t - ty) / 2.5)
        a = 1 - ramp(t, tdd + 1.0, 0.6)
        draw_arrow(c, curve_pts([ss, (lerp(ss[0], xp[0], 0.55), lerp(ss[1], xp[1], 0.55))], 30, 0.1), pr, YS, 28, a)
        draw_text(c, "袁术北上投袁绍", ss[0] + 20, ss[1] + 80, 36, YS, a * ramp(t, ty, 0.5), "serif", True, "center", stroke=5)
        if t > tdd:
            pp = (lerp(ss[0], xp[0], 0.55), lerp(ss[1], xp[1], 0.55))
            xmark(c, *pp, ramp(t, tdd, 0.3) * a, 1.4)
            draw_text(c, "病死", pp[0] + 50, pp[1] + 10, 40, (230, 90, 80), ramp(t, tdd, 0.3) * a, "serif", True, stroke=5)
    if t > tch:
        pts2 = curve_pts([xu, (lerp(xu[0], xp[0], 0.42), lerp(xu[1], xp[1], 0.42) - 30)], 40, -0.12)
        draw_dashed(c, pts2, ease((t - tch - 1.5) / 2.0), (40, 38, 40), 9, 1 - ramp(t, tcz, 0.5), phase=-t * 50)
        draw_dashed(c, pts2, ease((t - tch - 1.5) / 2.0), GOLD, 3, 1 - ramp(t, tcz, 0.5), phase=-t * 50, glow=False)
        draw_text(c, "追之不及", W / 2, 1180, 56, GOLD_HI, fade_win(t, tch + 3.2, tcz, 0.4, 0.4), "serif", True, "center", stroke=6)
    flip = ramp(t, tcz + 0.8, 0.3)
    flag(c, xp[0] + 6, xp[1] - 14, (30, 28, 30), 1 - flip, 1.3, t, "曹")
    flag(c, xp[0] + 6, xp[1] - 14, RED, flip, 1.3, t, "劉")
    if t > tcz:
        draw_text(c, "杀车胄", xp[0] - 20, xp[1] + 90, 44, RED_HI, fade_win(t, tcz + 0.6, trl, 0.3, 0.4), "serif", True, "center", stroke=5)
    if t > trl:
        sw = Swarm(700, 41, 260, 45)
        dh = pl(cam, "东海")
        xy, f = sw.pos((dh[0] + 40, dh[1] - 120), xp, ease((t - trl) / 3.5), t, jitter=3)
        Swarm.draw(c, xy, RED_HI, 0.85, 2.6)
        draw_text(c, "众数万人", xp[0] + 20, xp[1] - 120, 60, RED_HI, ramp(t, trl + 2, 0.5), "serif", True, "center", stroke=6, shadow=10)
    tc = cue(S, "cash")
    if t > tc:
        big_text(c, "名分 → 兑现", 420, 80, GOLD_HI, ramp(t, tc, 0.5))


# ───────────────────────── R 曹操回头 ─────────────────────────
def v_target(c, S, t):
    tf_, ta, tcr, tdf = cue(S, "front"), cue(S, "aim"), cue(S, "crosshair"), cue(S, "defeat")
    cam = Cam(115.8, 35.2, 7.6, ay=860)
    draw_map(c, cam, ["袁绍", "曹操"], 0.8)
    map_note(c)
    year_tag(c, "200", 1, "建安五年")
    xu, gd, ye, xs = pl(cam, "许"), pl(cam, "官渡"), pl(cam, "邺"), pl(cam, "小沛")
    city(c, *xu, "许", 1, GOLD_HI, major=True, side="left")
    city(c, *gd, "官渡", 1, PAPER, side="up")
    city(c, *ye, "邺", 1, YELLOW, major=True)
    city(c, *xs, "小沛", 1, RED_HI)
    tp = cue(S, "purge")
    draw_text(c, "董承等伏诛", W / 2, 420, 54, (230, 120, 110), fade_win(t, tp + 0.3, tf_, 0.4, 0.4), "serif", True, "center", stroke=6)
    if t > tf_:
        for k in range(3):
            st = (ye[0] - 60 + k * 70, ye[1] + 40)
            draw_arrow(c, curve_pts([st, (gd[0] - 40 + k * 40, gd[1] - 50)], 30, 0.1), ease((t - tf_ - k * 0.2) / 2), YELLOW, 30, 1)
        banner(c, ye[0] + 90, ye[1] - 40, "袁", YELLOW, ramp(t, tf_, 0.5), 40)
    if t > ta:
        draw_arrow(c, curve_pts([(xu[0] + 30, xu[1] - 20), (xs[0] - 50, xs[1] + 10)], 40, -0.15), ease((t - ta) / 2.2), (40, 38, 40), 48, 1)
        banner(c, xu[0] - 60, xu[1] - 260, "曹", (30, 28, 30), ramp(t, ta, 0.5), 44)
    if t > tcr:
        a = ramp(t, tcr, 0.4)
        R = 120 - 50 * ease((t - tcr) / 1.2)
        x, y = xs
        c.drawCircle(x, y, R, paint((230, 60, 50), a, stroke=5))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.drawLine(x + dx * (R + 40), y + dy * (R + 40), x + dx * 20, y + dy * 20, paint((230, 60, 50), a, stroke=5))
        draw_text(c, "天下英雄 → 准星", W / 2, 1180, 52, (240, 110, 90), a, "serif", True, "center", stroke=6)
    if t > tdf:
        sw = Swarm(260, 51, 20, 120)
        xy, _ = sw.pos(xs, (xs[0] + 20, xs[1] - 80), ease((t - tdf) / 2.5), t)
        Swarm.draw(c, xy, RED_HI, 0.8 * (1 - 0.6 * ramp(t, tdf + 1, 2)), 2.6)
        draw_text(c, "妻儿第三次被俘 · 关羽被擒", W / 2, 1250, 42, WHITE, ramp(t, tdf + 0.8, 0.4), "sans", True, "center", stroke=5)


# ───────────────────────── S 流亡：印跟着人走 ─────────────────────────
EXILE = ["小沛", "平原", "邺", "汝南", "新野"]


def v_exile(c, S, t):
    tn, tye, tg, tso, txy, tac, tbr, tlz = (cue(S, k) for k in ("north", "ye", "glow", "south", "xinye", "account", "biroulight", "longzhong"))
    cam0 = Cam(115.5, 34.5, 9.5, ay=840)
    cam1 = Cam(114.2, 33.6, 9.0, ay=900)
    cam = Cam.lerp(cam0, cam1, ease((t - tso) / 3))
    draw_map(c, cam, ["袁绍", "曹操", "刘表"], 0.85)
    map_note(c)
    year_tag(c, "200–201", 1, "流亡")
    pts_s = [pl(cam, n) for n in EXILE]
    for n in ("许", "官渡"):
        city(c, *pl(cam, n), n, 0.8, GOLD, side="left", r=7, size=28)
    for k, n in enumerate(EXILE):
        city(c, *pts_s[k], n, 1, PAPER, side="right" if n != "新野" else "left", major=n in ("邺",))
    banner(c, pl(cam, "邺")[0] - 110, pl(cam, "邺")[1] - 150, "袁紹", YELLOW, 0.9, 34)
    banner(c, pl(cam, "新野")[0] - 150, pl(cam, "新野")[1] - 40, "劉表", (90, 130, 90), 0.9 * ramp(t, tso, 0.5), 34)
    seg1 = curve_pts(pts_s[:3], 40, 0.12)
    seg2 = curve_pts(pts_s[2:], 40, -0.1)
    p1 = ease((t - tn) / 3.0)
    p2 = ease((t - tso) / 4.0)
    e1 = draw_dashed(c, seg1, p1, RED_HI, 7, 1, phase=-t * 40)
    e2 = draw_dashed(c, seg2, p2, RED_HI, 7, 1, phase=-t * 40) if t > tso else None
    e = e2 if e2 else e1
    if e:
        (px, py), _ = e
        stops = [(tye, "邺"), (txy, "新野")]
        gl = 0.5
        for ts_, nm in stops:
            if t > ts_:
                gl = max(gl, 1.2 * math.exp(-(t - ts_ - 1.0) * 0.8) if t > ts_ + 1 else ramp(t, ts_, 1.0) * 1.2)
        if t > tg:
            gl = max(gl, fade_win(t, tg, tso, 0.4, 0.8) * 1.3)
        dimf = 1 - 0.55 * ramp(t, tbr, 0.8) * (1 - ramp(t, tlz, 0.8))
        seal(c, px, py - 90, 0.5, 1, glow=gl * dimf)
    if t > tye:
        draw_text(c, "出邺城二百里相迎", pl(cam, "邺")[0], pl(cam, "邺")[1] + 80, 40, YELLOW, fade_win(t, tye + 0.5, tso, 0.4, 0.4), "serif", True, "center", stroke=5)
    if t > tg:
        draw_text(c, "左将军 + 「英雄」", W / 2, 400, 56, GOLD_HI, fade_win(t, tg + 0.3, tso, 0.4, 0.5), "serif", True, "center", stroke=6, shadow=10)
    if t > txy:
        nx = pl(cam, "新野")
        draw_text(c, "郊迎 · 上宾 · 增兵", nx[0], nx[1] + 90, 40, (150, 200, 150), fade_win(t, txy + 0.5, tac, 0.4, 0.4), "serif", True, "center", stroke=5)
    if t > tac:
        draw_text(c, "名分账户：从未清零", W / 2, 400, 56, GOLD_HI, fade_win(t, tac + 0.2, tbr, 0.4, 0.5), "serif", True, "center", stroke=6, shadow=10)
    if t > tbr:
        draw_text(c, "髀肉复生", W / 2, 400, 70, (220, 200, 180), fade_win(t, tbr + 0.3, tlz, 0.4, 0.5), "tc", True, "center", stroke=6, shadow=10)
    if t > tlz:
        lz = pl(cam, "隆中")
        city(c, *lz, "隆中", ramp(t, tlz, 0.5), GOLD_HI, side="left", ring=((t - tlz) * 0.7) % 1.0)


# ───────────────────────── T 校正：早年相识 ─────────────────────────
def v_correction(c, S, t):
    cam = Cam(114.6, 34.1, 6.4, ay=820)
    draw_map(c, cam)
    map_note(c)
    ly, pg, cl = pl(cam, "洛阳"), pl(cam, "沛国"), pl(cam, "陈留")
    city(c, *ly, "洛阳", 1, PAPER, side="up")
    city(c, *pg, "沛国", 1, PAPER, side="up")
    t1, t2, t3 = lt(S, 1), lt(S, 2), lt(S, 3)
    big_text(c, "早年就认识？", 400, 72, WHITE, ramp(t, 0.2, 0.5) * (1 - ramp(t, t1, 0.4)))
    if t > t1:
        pts = curve_pts([ly, pg], 40, -0.15)
        draw_dashed(c, pts, ease((t - t1) / 2.5), (210, 200, 190), 5, 0.9, dash=(10, 12), phase=-t * 20)
        mid = pts[len(pts) // 2]
        rrect(c, mid[0] - 60, mid[1] - 90, 120, 50, 6, paint((10, 10, 10), 0.8 * ramp(t, t1 + 1, 0.4)))
        draw_text(c, "孤证", mid[0], mid[1] - 52, 34, (240, 200, 120), ramp(t, t1 + 1, 0.4), "sans", True, "center")
    if t > t2:
        city(c, *cl, "陈留", ramp(t, t2, 0.4), GOLD_HI, side="right")
        draw_text(c, "《武帝纪》：至陈留，散家财起兵", cl[0] + 10, cl[1] + 70, 34, GOLD_HI, ramp(t, t2 + 0.6, 0.4), "sans", True, "center", stroke=5)
        draw_text(c, "两说不合", W / 2, 400, 60, (240, 160, 120), fade_win(t, t2 + 1.5, t3, 0.4, 0.4), "serif", True, "center", stroke=6)
    if t > t3:
        a = ramp(t, t3, 0.5)
        rrect(c, 140, 330, 800, 120, 10, paint((10, 8, 6), 0.8 * a))
        draw_text(c, "少年同学？ 无史料", W / 2, 410, 54, (240, 110, 90), a, "serif", True, "center")


# ───────────────────────── U 两条路 ─────────────────────────
def v_compare(c, S, t):
    tca, tli, ttw, tth = cue(S, "cao"), cue(S, "liu"), cue(S, "two"), cue(S, "three")
    c.clear(skia.Color4f(0.04, 0.035, 0.03, 1))
    if t < tth:
        # 上：曹操版图
        cam = Cam(114.0, 34.2, 9.0, ax=540, ay=520)
        c.save(); c.clipRect(skia.Rect.MakeXYWH(0, 220, W, 620))
        draw_map(c, cam, ["曹操"], 1.0)
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(0, 220, W, 620), paint(GOLD, 0.6, stroke=2))
        a = ramp(t, tca, 0.5)
        for k, s in enumerate(["天子", "中原", "屯田积粮", "越打越大的军队"]):
            rrect(c, 60 + k * 245, 760, 225, 64, 6, paint((10, 10, 10), 0.85 * ramp(t, tca + 0.4 * k, 0.4)))
            draw_text(c, s, 60 + k * 245 + 112, 805, 34, GOLD_HI, ramp(t, tca + 0.4 * k, 0.4), "sans", True, "center")
        draw_text(c, "曹操：攒地盘", 60, 300, 50, GOLD_HI, ramp(t, ttw, 0.5), "serif", True, stroke=5)
        # 下：刘备只有名号
        grad_rect(c, 0, 860, W, 600, (40, 16, 12), 1, (10, 6, 5), 1)
        a2 = ramp(t, tli, 0.5)
        seal(c, 270, 1120, 0.9, max(0.35, a2), glow=0.6 * a2)
        for k, s in enumerate(["一个名号", "一句评语", "关、张几人"]):
            draw_text(c, s, 560, 1040 + k * 80, 44, (240, 200, 180), ramp(t, tli + 0.5 * k, 0.4), "serif", True)
        draw_text(c, "刘备：攒名分", 60, 940, 50, RED_HI, ramp(t, ttw, 0.5), "serif", True, stroke=5)
    else:
        grad_rect(c, 0, 0, W, H, (30, 22, 14), 1, (6, 5, 4), 1)
        seal(c, W / 2, 420, 1.0, 1, glow=0.7)
        for k, (cu, s, sub) in enumerate([("u1", "护身", "杀一人而失天下之心"), ("u2", "招人", "振臂一呼，众数万人"), ("u3", "换席位", "出城二百里 · 郊迎上宾")]):
            tk = cue(S, cu); a = ramp(t, tk, 0.5)
            y = 680 + k * 210
            rrect(c, 120, y, 840, 170, 10, paint((255, 255, 255), 0.05 * a))
            rrect(c, 120, y, 840, 170, 10, paint(GOLD, 0.7 * a, stroke=2))
            draw_text(c, "一二三"[k], 180, y + 105, 56, GOLD_HI, a, "serif", True, "center")
            draw_text(c, s, 250, y + 80, 52, WHITE, a, "serif", True)
            draw_text(c, sub, 250, y + 138, 34, (220, 206, 180), a, "sans")
        tl = lt(S, len(S["lines"]) - 2)
        if t > tl:
            a = ramp(t, tl, 0.5)
            c.drawRect(skia.Rect.MakeWH(W, H), paint((6, 5, 4), 0.9 * a))
            big_text(c, "地盘：实，一仗可光", 700, 58, (220, 220, 210), a)
            big_text(c, "名分：虚，跟着人走", 800, 58, GOLD_HI, a * ramp(t, tl + 1.5, 0.5))
            tlast = lt(S, len(S["lines"]) - 1)
            big_text(c, "但名分只是种子", 980, 70, RED_HI, ramp(t, tlast, 0.5))


# ───────────────────────── V 收束 ─────────────────────────
def v_ending(c, S, t):
    tz, tn, tl_ = cue(S, "zhouyi"), cue(S, "next"), cue(S, "lesson")
    if t < tz:
        stage_begin(c)
        room(c, t + 60, flash=0, rain=0.4, brightness=0.8)
        figure(c, 230, 1300, 1.18, 1, robe=(26, 24, 26), trim=GOLD, rim=0.3, pose="cup", hand=1)
        figure(c, 850, 1300, 1.18, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=0.3)
        table(c)
        utensils(c, 100, 0)
        c.restore()
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.3 + 0.3 * ramp(t, tl_, 1)))
        vignette(c, 0.7, 0.35)
        if t > tl_:
            a = ramp(t, tl_, 0.6)
            rrect(c, 80, 330, 920, 360, 12, paint((10, 8, 6), 0.8 * a))
            rrect(c, 80, 330, 920, 360, 12, paint(GOLD, 0.7 * a, stroke=2))
            draw_text(c, "落魄时攒下的头衔和评价，", W / 2, 440, 48, WHITE, a, "serif", True, "center")
            draw_text(c, "可能比一时的地盘更耐用；", W / 2, 510, 48, WHITE, a, "serif", True, "center")
            draw_text(c, "但别人给你的高评价，", W / 2, 590, 48, GOLD_HI, ramp(t, tl_ + 2.5, 0.5), "serif", True, "center")
            draw_text(c, "也会让你成为靶子。", W / 2, 660, 48, GOLD_HI, ramp(t, tl_ + 2.5, 0.5), "serif", True, "center")
    elif t < tn:
        c.clear(skia.Color4f(0.03, 0.025, 0.02, 1))
        grad_rect(c, 0, 0, W, H, (26, 18, 12), 1, (4, 3, 2), 1)
        c.drawImage(noise_img(W // 3, H // 3, 6, alpha=0.06), 0, 0)
        seal(c, W / 2, 1080, 0.8, ramp(t, tz + 1.5, 1.0), glow=0.4)
        # 竖排大字
        a = ramp(t, tz, 0.8)
        for col_i, s in enumerate(["君子藏器於身", "待時而動"]):
            x = W / 2 + 90 - col_i * 180
            for k, ch in enumerate(s):
                draw_text(c, ch, x, 300 + k * 96, 86, GOLD_HI, a * ramp(t, tz + 0.15 * (k + col_i * 6), 0.4), "tc", True, "center", shadow=12)
        draw_text(c, "——《周易·繫辭下》", W / 2 + 300, 900, 32, GOLD, a, "serif", False, "center")
    else:
        # 下一集：山中草庐
        c.clear(skia.Color4f(0.05, 0.06, 0.07, 1))
        grad_rect(c, 0, 0, W, H, (40, 48, 56), 1, (10, 12, 14), 1)
        a = ramp(t, tn, 1.0)
        for k, (yy, colr) in enumerate([(820, (40, 50, 58)), (930, (30, 38, 44)), (1050, (20, 26, 30))]):
            path = skia.Path(); path.moveTo(0, H)
            for i in range(0, W + 60, 60):
                path.lineTo(i, yy - 120 * math.sin(i / 260 + k * 1.7) - 60 * math.sin(i / 90 + k))
            path.lineTo(W, H); path.close()
            c.drawPath(path, paint(colr, a))
        # 草庐
        hx, hy = 640, 1020
        roof = skia.Path(); roof.moveTo(hx - 120, hy); roof.lineTo(hx, hy - 90); roof.lineTo(hx + 120, hy); roof.close()
        c.drawPath(roof, paint((90, 80, 50), a)); c.drawRect(skia.Rect.MakeXYWH(hx - 90, hy, 180, 90), paint((60, 50, 36), a))
        c.drawRect(skia.Rect.MakeXYWH(hx - 20, hy + 30, 40, 60), paint((240, 200, 120), 0.8 * a))
        # 三行脚印
        for k in range(3):
            pp = ramp(t, tn + 1 + k * 0.8, 0.6)
            draw_dashed(c, curve_pts([(120 + k * 30, 1500 - k * 40), (hx - 60, hy + 90)], 30, 0.2), pp, RED_HI, 5, a, dash=(8, 14))
        big_text(c, "下一集", 420, 56, (200, 210, 220), a)
        big_text(c, "四十七岁那年", 560, 76, WHITE, ramp(t, tn + 0.5, 0.6))
        big_text(c, "他三次去了一个山里的草庐", 680, 60, GOLD_HI, ramp(t, tn + 1.2, 0.6))
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), ramp(t, dur(S) - 1.2, 1.2)))


VIS = dict(hook=v_hook, lostxuzhou=v_lostxuzhou, honor=v_honor, seal=v_seal, map196=v_map196, chengyu=v_chengyu,
           emperor=v_emperor, xiapi=v_xiapi, sanwen=v_sanwen, analogy=v_analogy, titles=v_titles, seal219=v_seal219,
           plot=v_plot, banquet=v_banquet, thunder=v_thunder, rating=v_rating, escape=v_escape, target=v_target,
           exile=v_exile, correction=v_correction, compare=v_compare, ending=v_ending)
