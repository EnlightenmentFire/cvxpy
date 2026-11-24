# -*- coding: utf-8 -*-
"""场景 下：s6 后方先塌（分屏）、s7 那句「粮少」、s8 回到周亚夫（静物）。"""
import math
import numpy as np
import skia
from engine import *
from scenes_a import header, caption, quote, ring_motif
from scenes_b import chapter, army, runner


def person(c, x, y, h=46, col="bone", a=1.0):
    """小人剪影：y 为脚底。"""
    if a <= 0.003:
        return
    k = h / 46
    c.drawCircle(x, y - 39 * k, 6.5 * k, P(col, a))
    c.drawPath(poly([(x - 7 * k, y - 31 * k), (x + 7 * k, y - 31 * k), (x + 11 * k, y), (x - 11 * k, y)], True), P(col, a))


def qin_block(c, x, y, w, h, name, a=1.0, glow=0.0, size=44):
    if a <= 0.003:
        return
    if glow > 0:
        rrect(c, x - w / 2 - 16, y - h / 2 - 16, w + 32, h + 32, 12, "bone", a * 0.4 * glow, blur=18)
    rrect(c, x - w / 2, y - h / 2, w, h, 6, "black", a); rrect(c, x - w / 2, y - h / 2, w, h, 6, "bone", a, sw=5)
    rrect(c, x - w / 2 + 14, y - h / 2 + 14, w - 28, h - 28, 3, "bone", a * 0.45, sw=1.5)
    text(c, name, x, y + size * 0.36, font("serif", 900, size), "bone", a, align="c", track=6)


def chu_block(c, x, y, w, h, name, a=1.0, size=44):
    if a <= 0.003:
        return
    rrect(c, x - w / 2 - 8, y - h / 2 - 8, w + 16, h + 16, 10, "red", a * 0.3, blur=14)
    rrect(c, x - w / 2, y - h / 2, w, h, 6, "red", a)
    rrect(c, x - w / 2 + 12, y - h / 2 + 12, w - 24, h - 24, 3, "#f0c9b0", a * 0.35, sw=1.5)
    text(c, name, x, y + size * 0.36, font("serif", 900, size), "#1a0b08", a, align="c", track=6)


def palace(c, cx, gy, a=1.0, lit=1.0, red=0.0):
    """咸阳宫门（司马门）剪影：双阙、门楼、紧闭的门。gy 为地面。"""
    if a <= 0.003:
        return
    edge = mix(mix("dim", "bone", lit), "red2", red)
    fill = P("#08080a", a)
    ln = lambda w=3: P(edge, a * (0.55 + 0.4 * lit), w)
    # 宫墙
    wall = skia.Rect.MakeLTRB(cx - 330, gy - 120, cx + 330, gy)
    c.drawRect(wall, fill); c.drawRect(wall, ln(2.5))
    for k in range(-5, 6):
        c.drawLine(cx + k * 60, gy - 120, cx + k * 60, gy - 132, ln(2))
    # 双阙
    for sx in (-1, 1):
        x = cx + sx * 250
        tw_ = skia.Rect.MakeLTRB(x - 36, gy - 250, x + 36, gy)
        c.drawRect(tw_, fill); c.drawRect(tw_, ln(3))
        for (yy, hw) in ((gy - 250, 62), (gy - 196, 52)):
            roof = poly([(x - hw, yy), (x + hw, yy), (x + hw * 0.62, yy - 30), (x - hw * 0.62, yy - 30)], True)
            c.drawPath(roof, fill); c.drawPath(roof, ln(3))
        c.drawLine(x - 22, gy - 150, x + 22, gy - 150, ln(1.5))
    # 门楼
    body = skia.Rect.MakeLTRB(cx - 120, gy - 200, cx + 120, gy)
    c.drawRect(body, fill); c.drawRect(body, ln(3))
    roof = poly([(cx - 170, gy - 200), (cx + 170, gy - 200), (cx + 112, gy - 248), (cx - 112, gy - 248)], True)
    c.drawPath(roof, fill); c.drawPath(roof, ln(3.5))
    c.drawLine(cx - 96, gy - 262, cx + 96, gy - 262, ln(4))
    # 两扇门（紧闭）
    for sx in (-1, 1):
        d = skia.Rect.MakeLTRB(cx + (sx - 1) * 39, gy - 150, cx + (sx + 1) * 39, gy)
        c.drawRect(d, P("#0d0b0a", a)); c.drawRect(d, P(mix("gold2", "red2", red), a * (0.7 + 0.3 * lit), 2.5))
        for r in range(4):
            for q in range(3):
                c.drawCircle(d.left() + 18 + q * 21, gy - 128 + r * 32, 3.2, P(mix("gold", "red2", red), a * (0.45 + 0.4 * lit)))
    c.drawLine(cx, gy - 150, cx, gy, P("#000000", a, 3))
    c.drawLine(cx - 400, gy, cx + 400, gy, ln(2.5))


def fork(c, y, rows, a, t, t0, x0=210, x1=870, size=44):
    """两行“无论……都……”的分叉示意。rows: [(左, 右)]。"""
    if a <= 0.003:
        return
    f = font("serif", 800, size)
    for i, (l, r) in enumerate(rows):
        yy = y + i * (size * 1.62)
        ai = a * ease(ramp(t, t0 + i * 1.0, t0 + i * 1.0 + 0.5))
        text(c, l, x0, yy, f, "bone", ai, align="c")
        arrow(c, [(x0 + 130, yy - size * 0.34), (x1 - 150, yy - size * 0.34)], "dim", 4, ease(ramp(t, t0 + i * 1.0 + 0.3, t0 + i * 1.0 + 1.0)), ai, head=16, smooth=False)
        text(c, r, x1, yy, f, "red", a * ease(ramp(t, t0 + i * 1.0 + 0.8, t0 + i * 1.0 + 1.3)), align="c")


# ============ s6 后方先塌 ============
GATE_X, GATE_Y = 560, 742
CAMP6 = (300, 1010)
CHU6 = (770, 1236)
ROAD = [(300, 962), (170, 918), (104, 840), (120, 770), (250, 742), (440, 742), (505, 742)]
ESC = [(620, 742), (900, 760), (990, 850), (930, 930), (640, 990), (408, 1004)]
ZHANG = [(30, 1140), (300, 1158), (560, 1118), (820, 1150), (1050, 1124)]


def scene_s6(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s6")
    a = pulse(t, s0, s1, 0.6, 0.6)
    if a <= 0.003:
        return
    header(c, 0.5 * a, src="《史记·项羽本纪》")
    p2 = ctx.prog("s6_02")
    # ---------- 分屏线 ----------
    top_on = ease(ramp(t, T("s6_03") + 0.6, T("s6_03") + 1.6))
    c.drawLine(60, 846, 1020, 846, P("ink2", a * 0.9, 1.5))
    tag(c, "咸阳 · 朝廷", 1010, 830, 27, "dim", a * top_on, align="r", kind="serif", weight=700)
    tag(c, "前线 · 棘原", 1010, 886, 27, "dim", a, align="r", kind="serif", weight=700)

    # ---------- 背后那条线（营垒 → 咸阳） ----------
    road = spline(ROAD)
    road_in = ease(ramp(p2, 0.52, 0.72))
    broken = ease(ramp(t, T("s6_14") - 0.6, T("s6_14") + 2.4))
    if road_in > 0:
        segs = 30
        for i in range(segs):
            f0, f1 = i / segs, (i + 1) / segs
            if f1 > road_in and t < T("s6_03"):
                continue
            # 自咸阳一端（末段）向营垒一端变红、断开
            k = clamp(broken * 1.9 - (1 - f1) * 0.9)
            colr = mix("bone", "red", clamp(k * 2))
            vis = 1.0 if (i % 2 == 0 or k < 0.45) else 1 - ease(ramp(k, 0.45, 0.9))
            c.drawPath(road, P(colr, a * 0.85 * vis * (1 - 0.45 * k), 4.5, trim=(f0 + 0.003, f1 - 0.003)))
    tag(c, "营垒背后：通向朝廷的线", 150, 940, 23, "dim", a * pulse(t, T("s6_03"), T("s6_04"), 0.5, 0.5), plate=True)
    
    # ---------- 下半：棘原相持 ----------
    c.drawPath(spline(ZHANG), P("water", a, 24)); c.drawPath(spline(ZHANG), P("water2", a * 0.8, 8))
    tag(c, "漳水", 960, 1102, 26, "water2", a, kind="serif", weight=600)
    # 秦军数却：营垒后挪，留残影
    steps = ease(ramp(p2, 0.26, 0.36)) + ease(ramp(p2, 0.38, 0.48))
    shake = pulse(t, T("s6_15") + 3.0, s1, 0.2, 0.4) * math.sin(t * 22) * 4
    cx6 = CAMP6[0] - steps * 9 + shake; cy6 = CAMP6[1] - steps * 11
    for g in range(int(steps + 0.5)):
        rrect(c, CAMP6[0] - 100 - (g) * 9, CAMP6[1] - 42 - g * 11 + 22, 200, 84, 6, "dim2", a * 0.5 * pulse(t, T("s6_02"), T("s6_04"), 0.4, 1.0), sw=1.5, dash=(6, 6))
    still_here = pulse(t, T("s6_13"), T("s6_15"), 0.5, 0.5)
    qin_block(c, cx6, cy6, 200, 84, "章邯", a, glow=still_here)
    tag(c, "「秦軍數卻」", cx6 + 122, cy6 - 26, 30, "gold", a * pulse(t, T("s6_02") + 2.0, ctx.en("s6_02") - 2.4, 0.4, 0.5), kind="serif", weight=700, plate=True)
    tag(c, "秦军几次后退", cx6 + 136, cy6 + 12, 24, "dim", a * pulse(t, T("s6_02") + 2.0, ctx.en("s6_02") - 2.4, 0.4, 0.5), plate=True)
    tag(c, "营垒还在 · 主力还在", cx6 + 20, cy6 + 84, 28, "bone", a * still_here, kind="serif", weight=700, align="c", plate=True)
    chu_block(c, CHU6[0], CHU6[1], 190, 76, "项羽", a, size=40)
    tag(c, "漳南", CHU6[0] + 118, CHU6[1] + 12, 26, "red", a, kind="serif", weight=700)
    tag(c, "棘原", cx6 - 120, cy6 + 12, 26, "bone", a * (1 - pulse(t, T("s6_02") + 1.8, T("s6_04"), 0.3, 0.5)), kind="serif", weight=700, align="r")
    tag(c, "相持未战", 560, 1090, 28, "dim", a * pulse(t, T("s6_01") + 1.0, T("s6_02") + 2.0, 0.5, 0.5), kind="serif", weight=700, align="c", plate=True)

    # 二世使人让章邯：自咸阳而下的责问
    blame = ramp(p2, 0.66, 0.92)
    runner(c, list(reversed(ROAD)), blame, "red", 7, a)
    tag(c, "「二世使人讓章邯」", 160, 800, 28, "gold", a * pulse(t, T("s6_02") + 5.0, T("s6_03") + 0.6, 0.4, 0.5), kind="serif", weight=700, plate=True)
    tag(c, "让：责备", 174, 838, 23, "dim", a * pulse(t, T("s6_02") + 5.4, T("s6_03") + 0.6, 0.4, 0.5), plate=True)
    # 长史欣上咸阳
    up = ease(ramp(t, T("s6_03") + 0.8, T("s6_03") + 3.6))
    runner(c, ROAD, up * 0.999, "bone", 7, a * (1 - ease(ramp(up, 0.96, 1.0))))
    tag(c, "长史 司马欣 · 请事", 190, 882, 26, "bone", a * pulse(t, T("s6_03") + 0.6, T("s6_04") + 0.4, 0.4, 0.5), kind="serif", weight=700, plate=True)

    # ---------- 上半：咸阳司马门 ----------
    q_on = pulse(t, T("s6_06") - 0.3, T("s6_12") - 0.1, 0.5, 0.6)          # 两段原文占用上半屏
    q1 = pulse(t, s0 + 0.3, T("s6_02") + 2.0, 0.5, 0.5)
    pal_a = a * top_on * (1 - 0.86 * q_on)
    if pal_a > 0.003:
        day_t = ctx.prog("s6_04", 0.2, 1.2)
        # 日夜轮转的天光
        sky = 0.5 + 0.5 * math.sin(day_t * 3 * 2 * math.pi - math.pi / 2) if 0 < day_t < 1 else 0.5
        circle(c, GATE_X, GATE_Y - 150, 330, "gold", pal_a * 0.06 * sky * pulse(t, T("s6_04"), T("s6_05"), 0.4, 0.4), blur=90)
        c.save(); c.translate(GATE_X, GATE_Y); c.scale(0.86, 0.86); c.translate(-GATE_X, -GATE_Y)
        palace(c, GATE_X, GATE_Y, pal_a, lit=0.75, red=ease(ramp(broken, 0.0, 0.5)))
        c.restore()
        tag(c, "咸阳宫 · 司马门", GATE_X, GATE_Y - 252, 28, "bone", pal_a * (1 - broken), kind="serif", weight=700, align="c")
        # 等候的人
        wait = pulse(t, T("s6_03") + 3.6, T("s6_05") + 0.5, 0.4, 0.3)
        person(c, GATE_X - 6, GATE_Y, 44, "bone", pal_a * wait)
        tag(c, "司马欣 · 留司马门三日", GATE_X + 24, GATE_Y + 44, 24, "bone", pal_a * wait, plate=True)
        # 第一天 / 第二天 / 第三天
        da = pal_a * pulse(t, T("s6_04") - 0.1, T("s6_05") + 0.8, 0.4, 0.5)
        for i, lab in enumerate(["第一天", "第二天", "第三天"]):
            on = ease(ramp(day_t, i / 3 + 0.02, i / 3 + 0.12))
            x = 330 + i * 230
            rrect(c, x - 84, 336, 168, 60, 8, "#0d0e12", da * 0.9)
            rrect(c, x - 84, 336, 168, 60, 8, mix("dim2", "gold", on), da, sw=2)
            text(c, lab, x, 380, font("serif", 800, 36), mix("dim2", "bone", on), da, align="c")
        tag(c, "「趙高不見，有不信之心」", GATE_X, 444, 32, "red", pal_a * pulse(t, T("s6_04") + 2.6, T("s6_05") + 1.0, 0.4, 0.5), kind="serif", weight=700, align="c", plate=True)
    tag(c, "背后 · 已断", 300, 812, 36, "red", a * ease(ramp(broken, 0.55, 0.95)), kind="serif", weight=900, plate=True)
    # 逃回：不走原路；追兵沿原路，追不上
    esc = ease(ramp(t, T("s6_05") + 0.2, T("s6_05") + 2.4))
    if 0 < esc and t < T("s6_06") + 0.5:
        ea = a * (1 - ease(ramp(t, T("s6_06") - 0.2, T("s6_06") + 0.5)))
        c.drawPath(spline(ESC), P("bone", ea * 0.55, 3, dash=(9, 9), trim=(0, esc)))
        runner(c, ESC, esc * 0.999, "bone", 7, ea)
        tag(c, "「不敢出故道」", 800, 812, 28, "gold", ea * ease(ramp(esc, 0.2, 0.5)), kind="serif", weight=700, plate=True, align="c")
        tag(c, "不敢走来时的原路", 800, 884 + 28, 23, "dim", ea * ease(ramp(esc, 0.3, 0.6)), plate=True, align="c")
        chase = ease(ramp(t, T("s6_05") + 2.4, T("s6_05") + 4.4)) * 0.62
        rroad = spline(list(reversed(ROAD)))
        c.drawPath(rroad, P("red", ea * 0.9, 5, dash=(4, 12), trim=(0, chase)))
        tag(c, "趙高“使人追之，不及”", 250, 700, 24, "red", ea * ease(ramp(chase, 0.3, 0.6)), plate=True)

    # ---------- 上半屏的原文 ----------
    quote(c, ["章邯軍棘原，項羽軍漳南", "相持未戰"], W / 2, 500, 60, ctx.prog("s6_01", 0, 0.3), q1 * a, lh=1.5, weight=800, track=2)
    qa = pulse(t, T("s6_06") - 0.1, ctx.en("s6_08") + 0.2, 0.4, 0.4) * a
    if qa > 0:
        tag(c, "司马欣逃回军中，对章邯说", W / 2, 372, 28, "dim", qa, align="c")
        quote(c, ["今戰能勝，高必疾妒吾功", "戰不能勝，不免於死"], W / 2, 462, 60, ctx.prog("s6_07", 0, 0.3), qa, lh=1.42, weight=800, track=2)
        fork(c, 634, [("打赢", "赵高妒功"), ("打输", "难逃一死")], qa, t, T("s6_08") - 0.1, size=40)
    qb = pulse(t, T("s6_09") - 0.1, T("s6_12") - 0.15, 0.4, 0.4) * a
    if qb > 0:
        tag(c, "陈馀遗章邯书", W / 2, 372, 28, "dim", qb, align="c")
        text(c, "夫將軍居外久，多內卻", W / 2, 452, font("serif", 800, 50), "gold2", qb * ease(ramp(t, T("s6_09") + 1.4, T("s6_09") + 2.0)), align="c", track=2)
        quote(c, ["有功亦誅，無功亦誅"], W / 2, 552, 80, ctx.prog("s6_10", 0, 0.2), qb, track=2)
        tag(c, "卻，同“隙”：嫌隙", W / 2, 600, 23, "dim", qb * ease(ramp(t, T("s6_09") + 1.8, T("s6_09") + 2.4)), align="c")
        fork(c, 660, [("有功", "诛"), ("无功", "诛")], qb, t, T("s6_11") + 0.8, size=40)
    # 敌人的信：自楚赵一侧飞来
    lp = ease(ramp(t, T("s6_09") + 0.1, T("s6_09") + 1.8))
    if 0 < lp and t < T("s6_12"):
        la = a * (1 - ease(ramp(t, T("s6_11"), T("s6_11") + 0.8)))
        pth = spline([(1040, 960), (800, 930), (560, 1010), (cx6 + 112, cy6)])
        (lx, ly), _ = path_point(pth, lp)
        c.drawPath(pth, P("red", la * 0.5, 2.5, dash=(6, 8), trim=(0, lp)))
        c.save(); c.translate(lx, ly); c.rotate(-10)
        rrect(c, -22, -15, 44, 30, 3, "#e9e2d0", la); c.drawPath(poly([(-22, -15), (0, 3), (22, -15)]), P("red2", la, 2))
        c.restore()
    # 不攻营垒，攻其背后
    bk = pulse(t, T("s6_12") + 0.2, T("s6_13") + 0.2, 0.5, 0.6) * a
    if bk > 0:
        fp = ease(ramp(t, T("s6_12") + 0.4, T("s6_12") + 1.4))
        arrow(c, [(CHU6[0] - 110, CHU6[1] - 30), (cx6 + 150, cy6 + 60)], "red2", 7, fp * 0.8, bk * 0.7, head=20, smooth=False, dash=(10, 8))
        bp = ease(ramp(t, T("s6_12") + 2.0, T("s6_12") + 3.6))
        arrow(c, [(CHU6[0] - 120, CHU6[1] + 10), (360, 1250), (60, 1120), (70, 900), (112, 800)], "red", 9, bp, bk, head=26, glow=8)
        tag(c, "不攻营垒", 600, 1050, 26, "dim", bk * fp, plate=True, align="c")
        tag(c, "攻他的背后", 190, 1230, 30, "red", bk * ease(ramp(bp, 0.4, 0.8)), kind="serif", weight=700, plate=True, align="c")
    # 约未成，再破之、大破之
    if t > T("s6_15"):
        la = a
        tk = ease(ramp(t, T("s6_15") + 0.6, T("s6_15") + 1.8))
        c.drawPath(poly([(cx6 + 96, cy6 + 30), (CHU6[0] - 100, CHU6[1] - 20)]), P("gold", la * 0.8 * (1 - ease(ramp(t, T("s6_15") + 2.6, T("s6_15") + 3.2))), 3, dash=(8, 8), trim=(0, tk)))
        tag(c, "暗中遣使 · 欲约", 560, 1196, 24, "gold", la * pulse(t, T("s6_15") + 0.8, T("s6_15") + 3.0, 0.4, 0.4), plate=True, align="c")
        for i, (lab, st, sx) in enumerate([("再破之", 3.0, 0), ("大破之", 3.9, 70)]):
            hp = ease(ramp(t, T("s6_15") + st, T("s6_15") + st + 0.7))
            arrow(c, [(CHU6[0] - 60 + sx, CHU6[1] - 40), (cx6 + 130 + sx, cy6 + 58)], "red", 11, hp, la, head=28, smooth=False, glow=8)
            tag(c, lab, 640 + i * 150, 1070 - i * 4, 30, "red", la * ease(ramp(hp, 0.5, 1.0)), kind="serif", weight=900, plate=True, align="c")


# ============ s7 那句「粮少」 ============
def scene_s7(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s7")
    a = pulse(t, s0, s1, 0.6, 0.7)
    if a <= 0.003:
        return
    header(c, 0.5 * a, src="《史记·项羽本纪》")
    river = spline([(30, 800), (300, 840), (560, 780), (830, 830), (1050, 790)])
    c.drawPath(river, P("water", a, 28)); c.drawPath(river, P("water2", a * 0.8, 9))
    QX, QY = 300, 640
    CX, CY = 760, 1010
    meet = ease(ramp(t, T("s7_07") + 0.3, T("s7_07") + 2.6))
    # 章邯：背后那条线已断
    for i in range(7):
        x0, y0 = QX - 60 - i * 34, QY - 60 - i * 26
        if i % 2 == 0:
            fl = 0.5 + 0.5 * math.sin(t * 3 + i)
            c.drawLine(x0, y0, x0 - 22, y0 - 17, P("red", a * (0.35 + 0.4 * fl * pulse(t, T("s7_06"), T("s7_07"), 0.3, 0.5)) * (1 - meet), 4.5))
    tag(c, "背后 · 已断", QX - 150, QY - 190, 30, "red", a * pulse(t, T("s7_05") + 1.6, T("s7_07") + 0.3, 0.5, 0.5), kind="serif", weight=900, plate=True, align="c")
    qx = lerp(QX, CX - 250, meet); qy = lerp(QY, CY - 20, meet)
    qin_block(c, qx, qy, lerp(210, 160, meet), lerp(88, 70, meet), "章邯", a, size=lerp(46, 36, meet))
    chu_block(c, CX, CY, 230, 92, "项羽", a, size=48)
    # 「粮少」：楚营上方的一行小字
    la = ease(ramp(t, T("s7_02") + 0.1, T("s7_02") + 0.7)) * a
    if la > 0:
        text(c, "糧少", CX, CY - 92, font("serif", 800, 50), "gold", la, align="c", track=10, glow=14, glow_a=0.5)
        # 粮仓刻度
        for i in range(5):
            x = CX - 80 + i * 40
            rrect(c, x - 14, CY + 70, 28, 40, 3, "red2" if i > 0 else "gold", la * (0.5 if i > 0 else 1.0), sw=None if i == 0 else 2)
        tag(c, "楚军存粮", CX + 130, CY + 100, 24, "dim", la)
    q = pulse(t, T("s7_01") + 0.6, T("s7_04") + 0.4, 0.5, 0.5) * a
    if q > 0:
        tag(c, "项羽召军吏谋曰", W / 2, 352, 28, "dim", q, align="c")
        quote(c, ["糧少，欲聽其約"], W / 2, 470, 100, ctx.prog("s7_02", 0, 0.2), q, track=4)
    # 敌之可胜？也许
    ma = pulse(t, T("s7_05") - 0.1, T("s7_07") + 0.2, 0.5, 0.6) * a
    if ma > 0:
        pth = skia.Path(); pth.addOval(skia.Rect.MakeXYWH(CX - 190, CY - 150, 380, 300))
        c.drawPath(pth, P("gold", ma * 0.9, 3.5, dash=(14, 12), trim=(0, ease(ramp(t, T("s7_05"), T("s7_05") + 1.4)))))
        tag(c, "敌之可胜？", CX - 10, CY - 176, 38, "gold", ma * ease(ramp(t, T("s7_05") + 0.6, T("s7_05") + 1.2)), kind="serif", weight=900, align="c", plate=True)
        tag(c, "也许", CX + 150, CY - 176, 30, "dim", ma * ease(ramp(t, T("s7_05") + 1.4, T("s7_05") + 2.0)), kind="serif", weight=700, plate=True)
        text(c, "等不起了", W / 2, 440, font("serif", 900, 110), "bone", pulse(t, T("s7_06") + 0.2, T("s7_07") - 0.1, 0.4, 0.4) * a, align="c", track=10, glow=20, glow_a=0.25)
    ca = pulse(t, T("s7_07") + 0.1, s1, 0.5, 0.6) * a
    caption(c, "洹水南 · 殷虚 —— 已盟", ca, y=380, size=40)
    tag(c, "殷虚：今河南安阳一带（后世考证）", W / 2, 430, 24, "dim", ca, align="c")
    tag(c, "“章邯见项羽而流涕，为言赵高”", W / 2, 1250, 32, "gold", ca * ease(ramp(t, T("s7_07") + 2.0, T("s7_07") + 2.8)), kind="serif", weight=700, align="c")


# ============ s8 回到周亚夫 ============
def node(c, name, x, y, a=1.0, col="bone", size=54, w=None):
    if a <= 0.003:
        return
    f = font("serif", 900, size)
    ww = (w or tw(name, f, 4) + 56)
    rrect(c, x - ww / 2, y - size * 0.86, ww, size * 1.62, 8, "#0d0e12", a * 0.95)
    rrect(c, x - ww / 2, y - size * 0.86, ww, size * 1.62, 8, col, a * 0.85, sw=2.5)
    text(c, name, x, y + size * 0.3, f, col, a, align="c", track=4)


def meat_still(c, a, t, T, ctx):
    """静物：一案、一盘、一大块肉、空着的筷位。"""
    if a <= 0.003:
        return
    # 漆案
    rrect(c, 150, 610, 780, 520, 26, "#120d0d", a)
    rrect(c, 150, 610, 780, 520, 26, "red2", a * 0.9, sw=4)
    rrect(c, 174, 634, 732, 472, 16, "#3a1a16", a * 0.8, sw=1.6)
    # 盘
    c.drawOval(skia.Rect.MakeXYWH(250, 700, 440, 340), P("#0a0909", a))
    c.drawOval(skia.Rect.MakeXYWH(250, 700, 440, 340), P("dim", a * 0.8, 3))
    c.drawOval(skia.Rect.MakeXYWH(284, 728, 372, 284), P("dim2", a * 0.7, 1.5))
    # 大胾
    pts = [(350, 800), (430, 772), (520, 780), (590, 820), (606, 884), (572, 944), (490, 968), (400, 958), (340, 916), (326, 850)]
    m = spline(pts, closed=True)
    sh = skia.GradientShader.MakeLinear([(330, 770), (600, 970)], [C("#7a3a2c", a), C("#5a281f", a), C("#35160f", a)], [0, 0.5, 1])
    c.drawPath(m, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawPath(m, P("#1a0a07", a * 0.9, 3))
    for (p0, p1, p2) in (((372, 836), (450, 810), (540, 826)), ((366, 890), (460, 872), (566, 892)), ((410, 936), (480, 926), (540, 938))):
        fat = skia.Path(); fat.moveTo(*p0); fat.quadTo(p1[0], p1[1], p2[0], p2[1])
        c.drawPath(fat, P("#c9a48c", a * 0.38, 5))
    tag(c, "大胾 · 一整块肉，没有切", 470, 1084, 26, "dim", a, align="c")
    # 空着的筷位
    ea = a * ctx.fin("s8_04", 0.5, 4.6)
    for dx in (0, 26):
        c.save(); c.translate(770 + dx, 870); c.rotate(4)
        rrect(c, -6, -150, 12, 300, 6, "gold", ea * (0.55 + 0.25 * math.sin(t * 2.4)), sw=2.2, dash=(9, 8))
        c.restore()
    tag(c, "不置櫡", 782, 1072, 30, "gold", ea, kind="serif", weight=700, align="c")
    tag(c, "（没放筷子）", 782, 1104, 22, "dim", ea, align="c")


def shield_sil(c, x, y, s=1.0, a=1.0):
    """汉式双弧盾剪影。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    p = skia.Path()
    p.moveTo(-44, -84); p.quadTo(-22, -100, 0, -84); p.quadTo(22, -100, 44, -84)
    p.lineTo(50, 70); p.quadTo(24, 92, 0, 78); p.quadTo(-24, 92, -50, 70); p.close()
    c.drawPath(p, P("#0c0c0e", a)); c.drawPath(p, P("dim", a, 3))
    c.drawLine(0, -82, 0, 76, P("dim", a * 0.8, 2))
    c.drawOval(skia.Rect.MakeXYWH(-10, -18, 20, 30), P("dim", a * 0.8, 2))
    c.restore()


def armor_sil(c, x, y, s=1.0, a=1.0):
    """札甲剪影。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    p = poly([(-52, -92), (-22, -100), (0, -86), (22, -100), (52, -92), (76, -40), (52, -26), (50, 88), (-50, 88), (-52, -26), (-76, -40)], True)
    c.drawPath(p, P("#0c0c0e", a)); c.drawPath(p, P("dim", a, 3))
    for r in range(7):
        yy = -62 + r * 22
        c.drawLine(-48, yy, 48, yy, P("dim", a * 0.5, 1.4))
        for q in range(-3, 4):
            c.drawLine(q * 14 + (7 if r % 2 else 0), yy, q * 14 + (7 if r % 2 else 0), yy + 22, P("dim", a * 0.35, 1.2))
    c.restore()


def scene_s8(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s8")
    a = pulse(t, s0 + 1.6, s1, 0.6, 0.7)
    header(c, 0.5 * a, src="《史记·绛侯周勃世家》")
    if a > 0.003:
        # ---- A：有卻 ----
        aA = pulse(t, s0 + 1.7, T("s8_04") - 0.05, 0.6, 0.5) * a
        if aA > 0:
            quote(c, ["由此梁孝王與太尉有卻"], W / 2, 400, 70, ctx.prog("s8_02", 0, 0.3), aA * ctx.fin("s8_01", 0.4, 1.8), track=2)
            tag(c, "卻，同“隙”：嫌隙、结怨", W / 2, 452, 26, "dim", aA * ctx.fin("s8_02", 0.4, 1.0), align="c")
            TH, JD, LW, ZY = (540, 620), (280, 850), (800, 850), (540, 1130)
            la = aA * ease(ramp(t, s0 + 1.9, s0 + 2.7))
            for (p, q) in ((TH, JD), (TH, LW)):
                c.drawLine(p[0], p[1] + 40, q[0], q[1] - 54, P("dim", la, 2.5))
            c.drawLine(JD[0], JD[1] + 40, ZY[0] - 80, ZY[1] - 54, P("dim", la, 2.5))
            tag(c, "母子", 372, 716, 24, "dim", la, align="c"); tag(c, "母子 · 最疼的小儿子", 800, 716, 24, "gold", la * ctx.fin("s8_03", 0.4, 1.4), align="c")
            tag(c, "君臣", 360, 1004, 24, "dim", la, align="c")
            # 有卻：裂纹
            ck = ease(ramp(t, T("s8_02") + 0.4, T("s8_02") + 1.6))
            crack = poly([(LW[0] - 10, LW[1] + 40), (742, 930), (764, 968), (694, 1010), (716, 1046), (ZY[0] + 96, ZY[1] - 54)])
            c.drawPath(crack, P("red", la * 0.6, 12, blur=8, trim=(0, ck)))
            c.drawPath(crack, P("red", la, 4, trim=(0, ck)))
            tag(c, "有卻", 800, 1004, 34, "red", la * ease(ramp(ck, 0.5, 1.0)), kind="serif", weight=900, align="c")
            # 每朝，常与太后言条侯之短
            wk = ease(ramp(t, T("s8_03") + 2.6, T("s8_03") + 3.8))
            arrow(c, [(LW[0] + 60, LW[1] - 60), (860, 700), (TH[0] + 120, TH[1] - 6)], "red", 4, wk, la, head=16, dash=(8, 7))
            tag(c, "“每朝，常与太后言条侯之短”", 760, 560, 24, "red", la * ease(ramp(wk, 0.5, 1.0)), align="c", plate=True)
            node(c, "窦太后", *TH, la, "bone"); node(c, "景帝", *JD, la, "bone"); node(c, "梁孝王", *LW, la, mix("bone", "red", ck * 0.7)); node(c, "周亚夫", *ZY, la, "gold")
        # ---- B：赐食 ----
        aB = pulse(t, T("s8_04") + 0.1, T("s8_07") - 0.05, 0.6, 0.5) * a
        if aB > 0:
            la = aB * (1 - ctx.fin("s8_05", 0.3, -0.3))
            tag(c, "为丞相：争废栗太子，“景帝由此疏之”", W / 2, 372, 28, "dim", la * ctx.fin("s8_04", 0.4, 0.4), align="c")
            tag(c, "议封皇后兄王信：“非有功不得侯”", W / 2, 416, 28, "dim", la * ctx.fin("s8_04", 0.4, 1.4), align="c")
            tag(c, "景帝中三年（前147年）以病免相；其后，禁中赐食", W / 2, 520, 26, "bone", aB * ctx.fin("s8_04", 0.4, 3.4), align="c")
            meat_still(c, aB * ctx.fin("s8_04", 0.6, 3.0), t, T, ctx)
            qa = pulse(t, T("s8_05") - 0.15, ctx.en("s8_06") + 0.2, 0.3, 0.4) * aB
            quote(c, ["此怏怏者，非少主臣也"], W / 2, 420, 72, ctx.prog("s8_05", 0, 0.3), qa, track=2)
        # ---- C：葬器 ----
        aC = pulse(t, T("s8_07") + 0.1, T("s8_11") - 0.1, 0.6, 0.7) * a
        if aC > 0:
            dark = ease(ramp(t, T("s8_10") - 0.2, T("s8_10") + 0.8))
            gy = 940
            sink = ease(ramp(t, T("s8_08") + 1.6, T("s8_09") + 1.6))
            sa = aC * (1 - dark)
            armor_sil(c, 210, gy - 150 + sink * 250, 1.25, sa * lerp(1.0, 0.45, sink))
            for i in range(3):
                shield_sil(c, 420 + i * 150, gy - 130 + sink * 250, 1.1, sa * (1 - i * 0.22) * lerp(1.0, 0.45, sink) * ease(ramp(t, T("s8_07") + 0.6 + i * 0.25, T("s8_07") + 1.2 + i * 0.25)))
            tag(c, "× 五百", 900, gy - 120 + sink * 250, 46, "dim", sa * ctx.fin("s8_07", 0.5, 1.8) * lerp(1.0, 0.45, sink), kind="serif", weight=900, align="c")
            c.drawLine(80, gy, 1000, gy, P("bone", sa * 0.8, 3))
            tag(c, "地上", 990, gy - 18, 32, "bone", sa * ctx.fin("s8_08", 0.4, 0.3), kind="serif", weight=700, align="r")
            tag(c, "地下", 990, gy + 50, 32, "red", sa * ctx.fin("s8_08", 0.4, 2.0), kind="serif", weight=700, align="r")
            tag(c, "“工官尚方甲楯五百被，可以葬者” —— 陪葬用的器物", W / 2, 560, 26, "dim", sa * ctx.fin("s8_07", 0.5, 1.4) * (1 - ctx.fin("s8_08", 0.3)), align="c")
            qa = pulse(t, T("s8_08") - 0.15, ctx.en("s8_09") + 0.2, 0.3, 0.5) * aC
            quote(c, ["君侯縱不反地上", "即欲反地下耳"], W / 2, 392, 74, ctx.prog("s8_08", 0, 0.3), qa, lh=1.36, track=2)
            # 五日
            if dark > 0:
                da = aC * dark
                p10 = ctx.prog("s8_10", 0.1, 0.0)
                for i in range(5):
                    off = ease(ramp(t, T("s8_10") + 0.5 + i * 0.5, T("s8_10") + 1.0 + i * 0.5))
                    x = 380 + i * 80
                    c.drawLine(x, 760, x, 840, P(mix("bone", "dim2", off), da * (1 - 0.6 * off), 7))
                tag(c, "不食五日", W / 2, 920, 34, "bone", da, kind="serif", weight=800, align="c")
                tag(c, "景帝后元元年（前143年）· 距平定七国十一年", W / 2, 1010, 28, "dim", da * ctx.fin("s8_10", 0.5, 1.4), align="c")
                tag(c, "《汉书·景帝纪》：“条侯周亚夫下狱死”", W / 2, 1054, 24, "dim2", da * ctx.fin("s8_10", 0.5, 1.8), align="c")
        # ---- D：父与子 ----
        aD = pulse(t, T("s8_11") + 0.05, T("s8_15") - 0.05, 0.6, 0.5) * a
        if aD > 0:
            qa = pulse(t, T("s8_11") + 0.6, ctx.en("s8_13") + 0.3, 0.4, 0.5) * aD
            quote(c, ["吾嘗將百萬軍", "然安知獄吏之貴乎"], W / 2, 384, 66, clamp(ctx.prog("s8_12", 0, 0.2) * 0.6 + 0.42) if t > T("s8_12") else 0.4 * ctx.fin("s8_11", 0.8, 0.8), qa, lh=1.4, track=2)
            for i, (who, mid, mid2, end, col, tk) in enumerate([
                    ("父 · 周勃", "千金与狱吏", "薄昭为言薄太后", "出", "gold", T("s8_11") + 0.3),
                    ("子 · 周亚夫", "梁孝王数言其短", "太后不悦 · 景帝疏之", "死", "red", T("s8_14") + 2.6)]):
                y = 690 + i * 300
                ai = aD * ease(ramp(t, tk, tk + 0.6))
                node(c, who, 210, y, ai, "bone", size=40, w=270)
                tag(c, "下狱", 210, y + 80, 28, "dim", ai, align="c", kind="serif", weight=700)
                pr = ease(ramp(t, tk + 0.6, tk + 1.8))
                arrow(c, [(360, y - 6), (810, y - 6)], col, 4, pr, ai, head=16, smooth=False)
                tag(c, mid, 585, y - 30, 27, "bone", ai * ease(ramp(pr, 0.2, 0.6)), align="c", plate=True)
                tag(c, mid2, 585, y + 34, 27, "bone", ai * ease(ramp(pr, 0.4, 0.8)), align="c", plate=True)
                node(c, end, 900, y, ai * ease(ramp(pr, 0.7, 1.0)), col, size=58, w=120)
            tag(c, "宫里有人替他说话", 585, 600, 26, "gold", aD * ctx.fin("s8_14", 0.5, 0.4), align="c")
            tag(c, "宫里的人，站在对面", 585, 1100, 26, "red", aD * ctx.fin("s8_14", 0.5, 4.6), align="c")
        # ---- E：那根线 ----
        aE = pulse(t, T("s8_15") + 0.05, s1, 0.6, 0.7) * a
        if aE > 0:
            st = T("s8_15")
            items = [("以梁委之", "前154年 · 赢下这一仗的决定", "gold", 500), ("梁孝王有卻", "“由此”结怨", "bone", 700),
                     ("太后前言其短", "景帝渐疏之", "bone", 900), ("下狱 · 不食五日而死", "前143年", "red", 1100)]
            lp = ease(ramp(t, st + 0.4, st + 5.2))
            c.drawPath(poly([(200, 500), (200, 1100)]), P("red", aE * 0.5, 9, blur=7, trim=(0, lp)))
            c.drawPath(poly([(200, 500), (200, 1100)]), P("red", aE, 3.5, trim=(0, lp)))
            for i, (h, sub, col, y) in enumerate(items):
                ai = aE * ease(ramp(lp, i / 3 - 0.08, i / 3 + 0.06)) if i else aE * ease(ramp(t, st + 0.1, st + 0.6))
                circle(c, 200, y, 13, "bg", ai); circle(c, 200, y, 13, col, ai, sw=4); circle(c, 200, y, 5, col, ai)
                text(c, h, 250, y + 16, font("serif", 900, 50), col, ai)
                tag(c, sub, 252, y + 58, 26, "dim", ai)
            text(c, "那根线", W / 2, 396, font("serif", 900, 72), "bone", aE * ease(ramp(t, st + 2.4, st + 3.2)), align="c", track=12)
    chapter(c, t, s0, "叁", "周亚夫", "赢了之后", None)
