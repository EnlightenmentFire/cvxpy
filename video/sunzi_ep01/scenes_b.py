# -*- coding: utf-8 -*-
"""场景 中：章节卡、s3 七国形势图、s4 等（断粮·夜惊·声东击西）、s5 巨鹿。"""
import math
import numpy as np
import skia
from engine import *
from scenes_a import header, caption, quote, ring_motif, camp


# ============ 章节卡 ============
def chapter(c, t, s0, num, name, sub, legend, dur=2.0):
    a = pulse(t, s0 - 0.05, s0 + dur, 0.3, 0.45)
    if a <= 0.003:
        return
    c.drawRect(skia.Rect.MakeWH(W, H), P("#050506", a * 0.96))
    lt = t - s0
    text(c, num, W / 2, 610, font("serif", 900, 96), "gold", a * ease(ramp(lt, 0.0, 0.4)), align="c")
    c.drawLine(W / 2 - 70, 652, W / 2 + 70, 652, P("gold2", a, 2))
    text(c, name, W / 2, 830, font("serif", 900, 150), "bone", a * ease(ramp(lt, 0.1, 0.6)), align="c", track=14, glow=24, glow_a=0.2)
    text(c, sub, W / 2, 930, font("serif", 600, 50), "dim", a * ease(ramp(lt, 0.3, 0.8)), align="c", track=6)
    la = a * ease(ramp(lt, 0.5, 1.0))
    if legend:
        (n1, n2) = legend
        y = 1070
        block(c, 300, y - 12, 34, 34, "han", la); tag(c, n1, 330, y, 34, "bone", la, kind="serif", weight=700)
        block(c, 640, y - 12, 34, 34, "enemy", la); tag(c, n2, 670, y, 34, "red", la, kind="serif", weight=700)


# ============ 形势图（示意） ============
GX0, GX1, GY0, GY1 = 50, 1030, 440, 1220
LON0, LON1, LAT0, LAT1 = 112.55, 120.2, 31.7, 36.3


def geo(lon, lat):
    return (GX0 + (lon - LON0) / (LON1 - LON0) * (GX1 - GX0), GY1 - (lat - LAT0) / (LAT1 - LAT0) * (GY1 - GY0))


CITY = {k: geo(*v) for k, v in {
    "荥阳": (113.4, 34.8), "睢阳": (115.65, 34.4), "昌邑": (116.2, 35.2), "下邑": (116.35, 34.42),
    "彭城": (117.2, 34.26), "淮泗口": (118.9, 33.55), "广陵": (119.4, 32.4), "丹徒": (119.45, 32.2),
}.items()}
RIVERS = {
    "黄河": ([(112.55, 34.9), (113.6, 34.98), (114.3, 35.2), (114.9, 35.6), (115.5, 36.0), (115.9, 36.3)], 7, (115.6, 35.78)),
    "淮水": ([(112.55, 32.4), (114.2, 32.3), (115.3, 32.45), (116.3, 32.6), (117.2, 32.9), (118.2, 33.0), (118.9, 33.5), (119.5, 33.75), (120.2, 33.9)], 6, (115.6, 32.22)),
    "泗水": ([(117.0, 36.3), (116.95, 35.6), (116.8, 35.0), (117.15, 34.3), (117.9, 34.1), (118.5, 33.8), (118.9, 33.5)], 4.5, (117.3, 35.35)),
    "长江": ([(117.3, 31.7), (118.0, 31.8), (118.7, 32.1), (119.3, 32.25), (119.9, 32.1), (120.2, 32.0)], 8, (118.25, 31.82)),
    "睢水": ([(114.3, 34.7), (115.0, 34.5), (115.65, 34.34), (116.5, 34.0), (117.3, 33.75), (118.0, 33.75), (118.5, 33.8)], 2.6, None),
}
WEST = (GX0 + 4, 610)          # “← 长安” 在图外西侧
WU_PATH = [CITY["广陵"], geo(118.9, 32.9), geo(118.2, 33.3), CITY["彭城"], geo(116.5, 34.25), (CITY["睢阳"][0] + 52, CITY["睢阳"][1] + 6)]
SUPPLY = [CITY["昌邑"], geo(117.2, 34.75), geo(118.1, 34.1), CITY["淮泗口"]]


def shield(c, x, y, s=1.0, a=1.0, hot=0.0, hit=0.0):
    """梁（睢阳）：盾形城标。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    p = skia.Path()
    p.moveTo(-26, -30); p.lineTo(26, -30); p.lineTo(26, 2); p.quadTo(24, 26, 0, 38); p.quadTo(-24, 26, -26, 2); p.close()
    if hot > 0:
        c.drawPath(p, P("gold", a * 0.5 * hot, 14, blur=14))
    if hit > 0:
        c.drawPath(p, P("red", a * 0.7 * hit, 16, blur=12))
    c.drawPath(p, P("black", a))
    c.drawPath(p, P(mix("bone", "gold", hot), a, 4))
    text(c, "梁", 0, 14, font("serif", 900, 34), mix("bone", "gold", hot), a, align="c")
    c.restore()


def han_camp_icon(c, x, y, a=1.0, thick=0.0, glow=0.0, s=1.0):
    if a <= 0.003:
        return
    r = 25 * s
    if glow > 0:
        rrect(c, x - r - 8, y - r - 8, 2 * r + 16, 2 * r + 16, 6, "bone", a * 0.35 * glow, blur=14)
    rrect(c, x - r, y - r, 2 * r, 2 * r, 4, "black", a)
    rrect(c, x - r, y - r, 2 * r, 2 * r, 4, "bone", a, sw=3.5 + 4.5 * thick)
    rrect(c, x - r * 0.52, y - r * 0.52, r * 1.04, r * 1.04, 2, "bone", a * 0.75, sw=1.8)
    if thick > 0:
        rrect(c, x - r - 11, y - r - 11, 2 * r + 22, 2 * r + 22, 7, "bone", a * 0.8 * thick, sw=2.2, dash=(9, 6))


def army(c, x, y, side, a=1.0, n=5, s=1.0, lit=1.0, ang=0.0, seed=0):
    """一簇兵力方块。"""
    if a <= 0.003:
        return
    lay = [(0, 0), (-24, 16), (24, 16), (-12, -18), (14, -20), (0, 34), (-34, -6), (36, -4)][:n]
    c.save(); c.translate(x, y); c.rotate(ang); c.scale(s, s)
    for i, (dx, dy) in enumerate(lay):
        block(c, dx, dy, 20, 20, side, a, r=3, lit=lit)
    c.restore()


def runner(c, pts, prog, col="gold", r=6, a=1.0, trail=0.16, smooth=True):
    """沿路径奔走的小点（信使/轻骑），带拖尾。"""
    if a <= 0.003 or prog <= 0 or prog >= 1:
        return
    path = spline(pts) if smooth and len(pts) > 2 else poly(pts)
    c.drawPath(path, P(col, a * 0.55, r * 0.9, trim=(max(0, prog - trail), prog)))
    (x, y), _ = path_point(path, prog)
    glow_dot(c, x, y, r, col, a)


def map_base(c, a=1.0, lab=1.0):
    if a <= 0.003:
        return
    panel = skia.Rect.MakeLTRB(GX0 - 14, GY0 - 14, GX1 + 14, GY1 + 14)
    c.drawRoundRect(panel, 10, 10, P("#0e1016", a * 0.72))
    c.save(); c.clipRect(panel)
    # 经纬网（淡）
    for lon in range(113, 121):
        x, _ = geo(lon, 34)
        c.drawLine(x, GY0 - 14, x, GY1 + 14, P("#ffffff", a * 0.03, 1))
    for lat in range(32, 37):
        _, y = geo(116, lat)
        c.drawLine(GX0 - 14, y, GX1 + 14, y, P("#ffffff", a * 0.03, 1))
    for name, (pts, w, lp) in RIVERS.items():
        path = spline([geo(*p) for p in pts])
        c.drawPath(path, P("water", a * 0.95, w + 3))
        c.drawPath(path, P("water2", a * 0.95, w * 0.55))
        if lp:
            x, y = geo(*lp)
            tag(c, name, x, y, 26, "water2", a * lab * 1.0, kind="serif", weight=600, align="c")
    c.restore()
    c.drawRoundRect(panel, 10, 10, P("ink2", a * 0.9, 1.5))
    # 长安方向
    tag(c, "← 长安", GX0 + 6, WEST[1] - 22, 28, "bone", a * lab, kind="serif", weight=700, plate=True)
    tag(c, "形势示意 · 今地系后世考证", GX1 + 8, GY1 + 46, 22, "dim2", a * lab, align="r")
    # 北向标
    nx, ny = GX1 - 34, GY0 + 44
    c.drawPath(poly([(nx, ny - 22), (nx - 9, ny + 6), (nx, ny), (nx + 9, ny + 6)], True), P("dim", a * lab))
    tag(c, "北", nx, ny + 34, 22, "dim", a * lab, align="c")


def city(c, name, a=1.0, lab=None, dx=16, dy=10, col="bone", size=28, mark=True, align="l"):
    x, y = CITY[name]
    if mark:
        rrect(c, x - 7, y - 7, 14, 14, 2, "black", a)
        rrect(c, x - 7, y - 7, 14, 14, 2, col, a, sw=2.4)
    tag(c, lab or name, x + dx, y + dy, size, col, a, kind="serif", weight=700, plate=True, align=align)


def campaign_map(c, ctx):
    """s3 全段 + s4 首句共用的形势图。"""
    t = ctx.t
    T = ctx.st
    s3a, _ = ctx.tl.S("s3")
    t_end = T("s4_03") - 0.25
    a = pulse(t, s3a + 1.6, t_end, 0.7, 0.5)
    if a <= 0.003:
        return
    dimk = 1 - 0.72 * pulse(t, T("s3_08") - 0.2, ctx.en("s3_08") + 0.1, 0.4, 0.4)   # 讲“两种来历”时压暗
    a *= dimk
    map_base(c, a)
    SY = CITY["睢阳"]; CY = CITY["昌邑"]; XY = CITY["荥阳"]
    # ---- 城 ----
    ca = a * ease(ramp(t, s3a + 2.0, s3a + 2.8))
    city(c, "广陵", ca, "广陵（吴）", dx=-16, dy=40, col="red", align="r")
    city(c, "彭城", ca, "彭城（楚）", dx=-30, dy=56, col="red", align="c")
    city(c, "荥阳", a * ctx.fin("s3_02", 0.5), "荥阳", dx=0, dy=52, align="c")
    # ---- 吴楚西进 ----
    wp = ease(ramp(t, T("s3_01") + 0.8, T("s3_01") + 5.0))
    starve = ease(ramp(t, T("s4_01") + 2.2, T("s4_01") + 4.2))        # 粮道被断后变暗
    wcol = mix("red", "red2", starve * 0.8)
    if wp > 0:
        arrow(c, WU_PATH, wcol, 13, wp, a * 0.92, head=30, glow=10 * (1 - starve))
        (hx, hy), _ = path_point(spline(WU_PATH), wp)
        tag(c, "吴楚西进", *geo(117.75, 33.05), 28, "red", a * ease(ramp(wp, 0.5, 0.8)) * (1 - ctx.fin("s4_01", 0.4)), kind="serif", weight=700, plate=True)
        tag(c, "吴王“发二十余万人”（卷106）", CITY["广陵"][0] - 16, CITY["广陵"][1] + 78, 23, "dim", a * pulse(t, T("s3_01") + 2.5, T("s3_04"), 0.5, 0.5), align="r", plate=True)
    # 围攻睢阳的红色兵团（s4_01 后转向汉营）
    siege = ease(ramp(t, T("s3_01") + 4.6, T("s3_01") + 5.6))
    to_han = ease(ramp(t, T("s4_01") + 3.6, T("s4_01") + 5.6))
    ax = lerp(SY[0] + 74, CY[0] + 30, to_han); ay = lerp(SY[1] + 10, CY[1] + 78, to_han)
    hitk = pulse(t, T("s3_10"), ctx.en("s3_11") + 1.0, 0.3, 0.6)
    jit = math.sin(t * 9.0) * 5 * hitk
    army(c, ax - jit, ay, "enemy", a * siege, n=7, s=1.05, lit=1 - 0.7 * starve)
    # ---- 梁 ----
    hot = max(pulse(t, T("s3_06") + 1.6, T("s3_07") + 0.6, 0.4, 0.5), pulse(t, T("s3_09"), ctx.en("s3_09"), 0.4, 0.6))
    hit = hitk * (0.55 + 0.45 * math.sin(t * 9.0))
    shield(c, SY[0], SY[1], 1.0, a, hot=hot, hit=max(0, hit))
    tag(c, "睢阳", SY[0], SY[1] + 70, 28, "bone", a, kind="serif", weight=700, plate=True, align="c")
    tag(c, "今河南商丘", SY[0], SY[1] + 104, 22, "dim", a * pulse(t, T("s3_09") + 0.5, ctx.en("s3_09") + 0.6, 0.4, 0.5), align="c", plate=True)
    tag(c, "「以梁委之」", SY[0] - 40, SY[1] - 50, 30, "gold", a * pulse(t, T("s3_06") + 1.6, ctx.en("s3_07") + 0.4, 0.4, 0.5), kind="serif", weight=700, plate=True, align="c")
    # ---- 汉军：荥阳 → 昌邑 ----
    mv = ease(ramp(t, T("s3_10") + 0.0, T("s3_10") + 1.5))
    plan = pulse(t, T("s3_06") + 0.2, T("s3_10") + 0.5, 0.5, 0.4)
    route = [XY, geo(114.6, 35.25), CY]
    if plan > 0:
        arrow(c, route, "bone", 4, ease(ramp(t, T("s3_06") + 0.2, T("s3_06") + 1.6)), a * plan * 0.8, head=16, dash=(12, 9))
    ha = a * ctx.fin("s3_02", 0.6, 0.2)
    (hx, hy), _ = path_point(spline(route), mv)
    thick = ease(ramp(t, T("s3_12"), T("s3_13") + 1.2))
    backing = ease(ramp(t, T("s3_15") + 0.3, T("s3_15") + 1.5))
    han_camp_icon(c, hx, hy, ha, thick=thick * mv, glow=backing, s=lerp(0.85, 1.0, mv))
    lab_a = ha * (1 - pulse(t, T("s3_10") - 0.1, T("s3_10") + 1.6, 0.3, 0.3))
    if mv < 0.5:
        tag(c, "太尉 周亚夫", XY[0] + 42, XY[1] - 6, 28, "bone", lab_a, kind="serif", weight=700, plate=True)
        tag(c, "“将三十六将军”（卷106）", XY[0] + 42, XY[1] + 30, 22, "dim", lab_a * pulse(t, T("s3_02") + 0.6, T("s3_05"), 0.4, 0.5), plate=True)
    else:
        tag(c, "昌邑 · 周亚夫", CY[0] - 4, CY[1] - 46, 28, "bone", lab_a, kind="serif", weight=700, plate=True, align="c")
        tag(c, "今山东巨野、金乡一带", CY[0] - 4, CY[1] - 80, 22, "dim", lab_a * pulse(t, T("s3_10") + 1.6, ctx.en("s3_11"), 0.4, 0.5), align="c", plate=True)
        tag(c, "驻地：卷57作“昌邑”；卷106作“昌邑南”，后记吴军“走条侯军，会下邑”", GX0 + 4, GY0 + 16, 21, "dim", a * pulse(t, T("s3_10") + 1.8, ctx.en("s3_11") + 0.4, 0.5, 0.5), plate=True)
        tag(c, "「堅壁」", CY[0] + 44, CY[1] + 12, 30, "gold", a * pulse(t, T("s3_12") + 0.8, ctx.en("s3_13") + 0.3, 0.4, 0.5), kind="serif", weight=700, plate=True)
    # ---- 绝其粮道：计划（虚线）→ 执行（轻骑） ----
    sp = pulse(t, T("s3_06") + 2.6, T("s4_01") + 0.3, 0.5, 0.4)
    if sp > 0:
        c.drawPath(spline(SUPPLY), P("gold", a * sp * 0.75, 3, dash=(10, 9), trim=(0, ease(ramp(t, T("s3_06") + 2.6, T("s3_06") + 3.8)))))
        tag(c, "「絕其糧道」", *geo(117.85, 34.62), 28, "gold", a * sp * ease(ramp(t, T("s3_06") + 3.4, T("s3_06") + 4.0)) * (1 - ctx.fin("s3_08", 0.3)), kind="serif", weight=700, plate=True)
    city(c, "淮泗口", a * ease(ramp(t, T("s3_06") + 3.0, T("s3_06") + 3.8)), "淮泗口（卷106）", dx=18, dy=-14, col="bone", size=26)
    ex = ease(ramp(t, T("s4_01") + 0.4, T("s4_01") + 2.4))
    if t >= T("s4_01"):
        c.drawPath(spline(SUPPLY), P("gold", a * 0.9, 4, trim=(0, ex)))
        for k in range(3):
            runner(c, SUPPLY, clamp(ex * 1.05 - k * 0.07), "gold", 5.5, a)
        cut = ease(ramp(t, T("s4_01") + 2.2, T("s4_01") + 2.8))
        if cut > 0:
            x, y = CITY["淮泗口"]
            c.drawLine(x - 20, y - 20, x + 20, y + 20, P("gold", a * cut, 6)); c.drawLine(x + 20, y - 20, x - 20, y + 20, P("gold", a * cut, 6))
            circle(c, x, y, 20 + 46 * cut, "gold", a * (1 - cut) * 0.8, sw=3)
            tag(c, "轻骑绝吴楚“兵后食道”（卷57；地点据卷106）", x - 40, y + 62, 23, "gold", a * cut, align="c", plate=True)
        tag(c, "吴军“数欲挑战，终不出”", CY[0] - 300, CY[1] + 70, 24, "bone", a * to_han * (1 - ramp(t, t_end - 0.6, t_end)), plate=True)
    # ---- 求救的信使：睢阳 → 昌邑（三拨，都被挡回） ----
    for k in range(3):
        st = T("s3_10") + 1.7 + k * 0.75
        pr = ramp(t, st, st + 0.8)
        runner(c, [SY, CY], pr, "bone", 5, a, smooth=False)
        back = ramp(t, st + 0.8, st + 1.3)
        if 0 < back < 1:
            circle(c, CY[0] - 22, CY[1] + 40, 6 + 16 * back, "bone", a * (1 - back), sw=2)
    tag(c, "梁“日使使请太尉”", (SY[0] + CY[0]) / 2 - 150, (SY[1] + CY[1]) / 2 - 6, 23, "bone", a * pulse(t, T("s3_10") + 1.7, ctx.en("s3_10") + 0.8, 0.3, 0.4), plate=True, align="c")
    # ---- 梁王上书 → 长安；诏书（光）自西来，到营门前熄灭 ----
    up = ramp(t, T("s3_11") + 0.1, T("s3_11") + 1.3)
    runner(c, [SY, geo(114.3, 34.35), WEST], up, "bone", 5.5, a)
    tag(c, "梁王上书", *geo(113.9, 34.12), 23, "bone", a * pulse(t, T("s3_11") + 0.2, T("s3_11") + 2.2, 0.3, 0.4), plate=True)
    ed = [WEST, geo(114.2, 34.95), (CY[0] - 34, CY[1] + 4)]
    ep = ease(ramp(t, T("s3_11") + 1.6, T("s3_12") + 0.5))
    die = ease(ramp(t, T("s3_12") + 0.6, T("s3_12") + 1.5))
    if ep > 0 and die < 1:
        pth = spline(ed)
        c.drawPath(pth, P("gold", a * 0.7 * (1 - die), 22, blur=14, trim=(max(0, ep - 0.5), ep)))
        c.drawPath(pth, P("#fff3d0", a * (1 - die), 6, trim=(max(0, ep - 0.5), ep)))
        (x, y), _ = path_point(pth, ep)
        glow_dot(c, x, y, 8 * (1 - die * 0.6), "#fff3d0", a * (1 - die), spread=4)
        tag(c, "诏：救梁", *geo(114.35, 35.5), 28, "gold", a * (1 - die) * ease(ramp(ep, 0.2, 0.5)), kind="serif", weight=700, plate=True)
    if 0 < die < 1:
        circle(c, CY[0] - 34, CY[1] + 4, 10 + 40 * die, "gold", a * (1 - die) * 0.8, sw=3)
    # ---- 背后：梁王—景帝—周亚夫 ----
    bk = pulse(t, T("s3_14") + 0.3, t_end if t < T("s4_01") else T("s4_01") + 0.5, 0.6, 0.5) if t < T("s4_01") + 0.5 else 0
    if bk > 0:
        l1 = [SY, geo(114.3, 34.35), WEST]
        c.drawPath(spline(l1), P("red", a * bk * 0.8, 3, dash=(8, 7), trim=(0, ease(ramp(t, T("s3_14") + 0.3, T("s3_14") + 1.5)))))
        tag(c, "求救 · 告状", *geo(114.15, 34.02), 24, "red", a * bk * ease(ramp(t, T("s3_14") + 1.0, T("s3_14") + 1.6)), plate=True, kind="serif", weight=700)
        l2 = [WEST, geo(114.2, 34.95), (CY[0] - 34, CY[1] + 4)]
        bp = ease(ramp(t, T("s3_15") + 0.2, T("s3_15") + 1.6))
        c.drawPath(spline(l2), P("gold", a * bk * 0.35, 12, blur=8, trim=(0, bp)))
        c.drawPath(spline(l2), P("gold", a * bk, 3.5, trim=(0, bp)))
        tag(c, "景帝没有撤他", *geo(114.05, 35.72), 30, "gold", a * bk * ease(ramp(bp, 0.5, 1.0)), plate=True, kind="serif", weight=700)


def scene_s3(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s3")
    header(c, 0.5 * ease(ramp(t, s0 + 1.6, s0 + 2.4)), src="《史记》卷五十七 · 卷一百六")
    campaign_map(c, ctx)
    a_all = ease(ramp(t, s0 + 1.7, s0 + 2.4))
    # ---- 顶部题记区 ----
    ca = pulse(t, s0 + 1.8, T("s3_09") - 0.2, 0.5, 0.4)
    caption(c, "汉景帝三年（前154年）· 七国之乱", ca * a_all, y=354)
    tag(c, "太尉：汉朝最高军事长官", W / 2, 404, 28, "dim", a_all * pulse(t, T("s3_02") + 1.6, T("s3_02") + 4.2, 0.4, 0.4) * ca, align="c")
    # 文帝遗言（画面补注，图下一行）
    wa = pulse(t, T("s3_02") + 1.2, ctx.en("s3_09") - 0.2, 0.5, 0.4)
    tag(c, "文帝临终嘱太子：「即有緩急，周亞夫真可任將兵」（卷57）", 64, GY1 + 46, 23, "gold2", wa * a_all, kind="serif", weight=700)
    tag(c, "真有急事，周亚夫可以带兵", 64, GY1 + 80, 22, "dim", wa * a_all)
    # 请示原文
    qa = pulse(t, T("s3_05") - 0.2, ctx.en("s3_07") + 0.2, 0.4, 0.4)
    quote(c, ["楚兵剽輕，難與爭鋒", "願以梁委之，絕其糧道，乃可制"], W / 2, 346, 46, ctx.prog("s3_05", 0, 0.4), qa, lh=1.42, weight=800, track=2)
    st7 = ease(ramp(t, T("s3_07") + 0.1, T("s3_07") + 0.5)) * (1 - ease(ramp(t, ctx.en("s3_07") + 0.2, ctx.en("s3_07") + 0.6)))
    stamp(c, "上許之", 160, 560, 46, "red", st7, rot=-6)
    # 两种来历
    sa = pulse(t, T("s3_08") - 0.1, ctx.en("s3_08") + 0.15, 0.4, 0.4)
    if sa > 0:
        lt = t - T("s3_08")
        text(c, "同一条计策，两种来历", W / 2, 400, font("serif", 800, 50), "bone", sa, align="c", track=4)
        for i, (vol, name, q, plain) in enumerate([
                ("卷五十七", "绛侯周勃世家", "「因自請上」", "周亚夫自己向景帝提出"),
                ("卷一百六", "吴王濞列传", "「至淮陽，問……鄧都尉」", "路上问父亲周勃的老门客，门客献策")]):
            ai = sa * ease(ramp(lt, 1.8 + i * 2.4, 2.4 + i * 2.4))
            y = 560 + i * 300
            rrect(c, 110, y, 860, 240, 12, "#101218", ai * 0.92)
            rrect(c, 110, y, 860, 240, 12, "gold2", ai * 0.8, sw=1.8)
            tag(c, "《史记》" + vol, 150, y + 62, 30, "gold", ai, kind="serif", weight=700)
            tag(c, name, 930, y + 62, 28, "dim", ai, kind="serif", weight=600, align="r")
            text(c, q, 150, y + 136, font("serif", 800, 48), "bone", ai)
            tag(c, plain, 150, y + 196, 30, "dim", ai)
        tag(c, "史书两说并存，这里不替它统一", W / 2, 1190, 28, "dim", sa * ease(ramp(lt, 5.0, 5.6)), align="c")
    # 梁孝王身份
    la = pulse(t, T("s3_09") - 0.1, T("s3_04") - 0.05, 0.5, 0.4)
    tag(c, "梁城守坚：吴楚“以梁为限，不敢过而西”（卷58）", 64, GY1 + 46, 23, "dim", a_all * pulse(t, T("s3_13"), s1 - 0.3, 0.5, 0.5))
    caption(c, "梁孝王 · 景帝同母弟（卷58）", la, y=354)
    tag(c, "梁国正挡在吴楚西进的路上", W / 2, 404, 28, "dim", la, align="c")
    caption(c, "吴楚攻梁 · 梁日日求救", pulse(t, T("s3_10") - 0.1, ctx.en("s3_11") - 0.5, 0.5, 0.4), y=354)
    # 不奉诏
    q2 = pulse(t, T("s3_12") - 0.15, ctx.en("s3_13") + 0.2, 0.3, 0.5)
    quote(c, ["太尉不奉詔，堅壁不出"], W / 2, 384, 76, ctx.prog("s3_12", 0, 0.4), q2, track=3)
    # 兄弟
    ba = pulse(t, T("s3_14") + 0.2, s1 - 0.2, 0.5, 0.5)
    if ba > 0:
        f = font("serif", 900, 56)
        text(c, "景帝", 330, 376, f, "bone", ba, align="c", track=6)
        text(c, "梁孝王", 760, 376, f, "bone", ba, align="c", track=6)
        c.drawLine(420, 350, 640, 350, P("gold", ba, 3)); c.drawLine(420, 364, 640, 364, P("gold", ba, 3))
        tag(c, "同母兄弟", 530, 334, 26, "gold", ba, align="c", kind="serif", weight=700)
        tag(c, "求救的、告状的，都是他", 760, 420, 26, "red", ba * ease(ramp(t, T("s3_14") + 1.4, T("s3_14") + 2.0)), align="c")
    chapter(c, t, s0, "壹", "周亚夫", "把梁国扔出去", ("汉军 · 玄黑", "吴楚 · 暖红"))


# ============ s4 等 ============
def cross_section(c, x0, x1, y, a=1.0):
    """深沟高垒剖面示意。"""
    if a <= 0.003:
        return
    g = P("dim", a, 2.5)
    xd0, xd1 = x0 + 150, x0 + 330           # 沟
    xr0, xr1 = x0 + 400, x0 + 640           # 垒
    depth, height = 62, 76
    ground = skia.Path()
    ground.moveTo(x0, y); ground.lineTo(xd0, y); ground.lineTo(xd0 + 34, y + depth); ground.lineTo(xd1 - 34, y + depth); ground.lineTo(xd1, y)
    ground.lineTo(xr0, y); ground.lineTo(xr0 + 62, y - height); ground.lineTo(xr1 - 62, y - height); ground.lineTo(xr1, y); ground.lineTo(x1, y)
    fill = skia.Path(ground); fill.lineTo(x1, y + depth + 40); fill.lineTo(x0, y + depth + 40); fill.close()
    c.drawPath(fill, P("#14161b", a))
    water = poly([(xd0 + 14, y + 32), (xd1 - 14, y + 32), (xd1 - 34, y + depth), (xd0 + 34, y + depth)], True)
    c.drawPath(water, P("water", a * 0.9))
    c.drawPath(ground, P("bone", a * 0.9, 3.5))
    # 垒上木栅
    for k in range(9):
        xx = xr0 + 70 + k * 12.5
        c.drawLine(xx, y - height, xx, y - height - 26, P("bone", a * 0.8, 3))
    # 守军
    for xx in (xr1 - 150, xr1 - 118):
        c.drawCircle(xx, y - height - 40, 6, P("bone", a * 0.8)); c.drawLine(xx, y - height - 34, xx, y - height - 4, P("bone", a * 0.8, 5))
    tag(c, "深沟", (xd0 + xd1) / 2, y - 16, 30, "gold", a, align="c", kind="serif", weight=700)
    tag(c, "高垒", (xr0 + xr1) / 2, y + 44, 30, "gold", a, align="c", kind="serif", weight=700)
    tag(c, "营外", x0 + 58, y - 16, 24, "dim", a, align="c"); tag(c, "营内", x1 - 80, y - 16, 24, "dim", a, align="c")
    tag(c, "剖面示意", x1, y + depth + 30, 22, "dim2", a, align="r")


_RNG = np.random.default_rng(42)
_TORCH = [(_RNG.random(), _RNG.random(), _RNG.random() * 6.28, 0.6 + _RNG.random() * 1.2) for _ in range(70)]
_RING = [(_RNG.random() * 6.28, 0.85 + _RNG.random() * 0.4, _RNG.random()) for _ in range(40)]


def scene_s4(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s4")
    tcamp = T("s4_03") - 0.25
    if t < tcamp + 0.3:
        header(c, 0.5, src="《史记》卷五十七 · 卷一百六")
        campaign_map(c, ctx)
        caption(c, "他也不是光等", pulse(t, s0 + 0.2, tcamp, 0.4, 0.4) * 0.0, y=354)
    a = pulse(t, tcamp, s1, 0.7, 0.6)
    if a <= 0.003:
        return
    header(c, 0.5 * a, src="《史记·绛侯周勃世家》")
    endk = ease(ramp(t, T("s4_11") - 0.2, T("s4_11") + 0.8))        # 收束：营图退后
    cx, cy, cw, ch = 540, 770, 620, 440
    camp_a = a * lerp(1.0, 0.0, ease(ramp(t, T("s4_12") - 0.3, T("s4_12") + 0.5)))
    night = pulse(t, tcamp, T("s4_07") - 0.2, 0.6, 0.8)
    # 夜色
    if night > 0:
        circle(c, cx, cy, 520, "#05060a", a * night * 0.55, blur=120)
    # 营外吴军（饿 → 暗 → 少 → 溃散）
    siege_in = ease(ramp(t, T("s4_07") - 0.6, T("s4_07") + 0.4))
    starve = ease(ramp(t, T("s4_09") - 0.2, ctx.en("s4_09") + 1.0))
    flee = ease(ramp(t, T("s4_10") + 0.6, T("s4_10") + 3.0))
    for i, (ang, rr, ph) in enumerate(_RING):
        gone = clamp(starve * 1.7 - ph * 1.1)                       # 一圈圈减少
        if gone >= 1:
            continue
        ang = i / len(_RING) * 6.2832 + (ph - 0.5) * 0.1
        r0 = 400 * (1.0 + (rr - 1.05) * 0.35 + (i % 2) * 0.09)
        x = cx + math.cos(ang) * r0 * 1.06 + flee * (260 + 240 * ph)
        y = cy + math.sin(ang) * r0 * 0.84 + flee * (300 + 200 * ph)
        if GY0 - 120 < y < 1250 and 20 < x < 1060:
            block(c, x, y, 17, 17, "enemy", camp_a * siege_in * (1 - gone) * (1 - flee * 0.9), r=2, lit=1 - 0.8 * starve)
    gx, gy = camp(c, cx, cy, cw, ch, camp_a, gate=ease(ramp(t, T("s4_10") + 1.2, T("s4_10") + 2.0)), lit=lerp(1.0, 0.75, night),
                  hq_glow=0.5 + 0.5 * night, seed=11, tent_alpha=lerp(0.55, 0.3, night))
    # 夜惊：营内火点乱闪，中军帐不动
    chaos = pulse(t, T("s4_03") + 0.5, T("s4_05") + 1.2, 0.8, 1.6)
    calm = ease(ramp(t, T("s4_05") + 1.0, T("s4_05") + 2.6))
    if night > 0:
        for i, (u, v, ph, sp) in enumerate(_TORCH):
            bx = cx - cw / 2 + 50 + u * (cw - 100); by = cy - ch / 2 + 50 + v * (ch - 100)
            if abs(bx - cx) < 60 and abs(by - cy) < 60:
                continue
            reach = 1 - math.hypot(bx - cx, by - cy) / 330             # 乱势由外向中军蔓延
            k = chaos * clamp((ctx.since("s4_03") - 0.5) * 0.55 + (1 - reach) * 1.2 - 0.5)
            jx = math.sin(t * (5 + sp * 4) + ph) * 16 * k; jy = math.cos(t * (4 + sp * 5) + ph * 2) * 14 * k
            fl = 0.45 + 0.55 * abs(math.sin(t * (6 + sp * 7) + ph))
            aa = camp_a * night * (0.25 + 0.75 * k * fl + 0.25 * (1 - chaos))
            glow_dot(c, bx + jx, by + jy, 3.2 + 2.2 * k, mix("gold", "ember", k), aa, spread=2.6 + 1.6 * k)
        tag(c, "中军帐：不动", cx, cy + 74, 26, "gold", camp_a * pulse(t, T("s4_04"), T("s4_06") + 0.6, 0.4, 0.5), align="c", kind="serif", weight=700, plate=True)
    qa = pulse(t, T("s4_04") - 0.15, ctx.en("s4_05") + 0.2, 0.3, 0.5)
    quote(c, ["太尉終臥不起"], W / 2, 440, 92, ctx.prog("s4_04", 0, 0.3), qa * a)
    cap_a = pulse(t, tcamp + 0.3, T("s4_04") - 0.3, 0.5, 0.3) * a
    caption(c, "夜 · 军中惊", cap_a, y=380)
    # 剖面
    xs = pulse(t, tcamp + 0.4, T("s4_07") - 0.4, 0.6, 0.5) * a
    cross_section(c, 150, 930, 1180, xs)
    # 声东击西
    pa = pulse(t, T("s4_07") - 0.3, T("s4_09") - 0.1, 0.4, 0.5) * a
    if pa > 0:
        nx, ny = cx + cw / 2 + 70, cy - ch / 2 - 30
        c.drawPath(poly([(nx, ny - 24), (nx - 10, ny + 6), (nx, ny), (nx + 10, ny + 6)], True), P("dim", pa)); tag(c, "北", nx, ny + 34, 22, "dim", pa, align="c")
        se = (cx + cw / 2, cy + ch / 2); nw = (cx - cw / 2, cy - ch / 2)
        # 东南：虚箭
        fp = ease(ramp(t, T("s4_07") + 0.2, T("s4_07") + 1.6))
        arrow(c, [(se[0] + 230, se[1] + 200), (se[0] + 30, se[1] + 26)], "red", 9, fp, pa * 0.85, head=26, dash=(16, 12), smooth=False)
        tag(c, "东南陬 · 虚", se[0] + 60, se[1] + 178, 30, "red", pa * ease(ramp(fp, 0.4, 0.9)), kind="serif", weight=700, align="c", plate=True)
        # 营内守军调往西北
        mvp = ease(ramp(t, T("s4_07") + 2.0, T("s4_07") + 3.4))
        for k in range(6):
            sx0, sy0 = cx + 150 - (k % 3) * 34, cy + 110 + (k // 3) * 34
            tx, ty = nw[0] + 44 + (k % 3) * 30, nw[1] + 44 + (k // 3) * 30
            block(c, lerp(sx0, tx, mvp), lerp(sy0, ty, mvp), 22, 22, "han", pa)
        tag(c, "「使備西北」", nw[0] + 150, nw[1] + 130, 32, "gold", pa * ease(ramp(mvp, 0.3, 0.9)), kind="serif", weight=700, plate=True)
        # 西北：实箭，撞墙弹回
        hp_ = ramp(t, T("s4_08") + 0.5, T("s4_08") + 1.5)
        bounce = ramp(t, T("s4_08") + 1.5, T("s4_08") + 2.4)
        tip = eout(hp_) - 0.34 * eout(bounce)
        if hp_ > 0:
            arrow(c, [(nw[0] - 215, nw[1] - 150), (nw[0] - 28, nw[1] - 22)], "red", 14, clamp(tip), pa, head=34, smooth=False, glow=8)
            tag(c, "精兵 · 实", nw[0] - 100, nw[1] - 170, 30, "red", pa * ease(ramp(hp_, 0.2, 0.6)), kind="serif", weight=700, align="c", plate=True)
        if 0 < bounce < 1:
            circle(c, nw[0], nw[1], 20 + 70 * bounce, "bone", pa * (1 - bounce), sw=4)
        tag(c, "「不得入」", nw[0] + 60, nw[1] - 62, 36, "gold", pa * ease(ramp(bounce, 0.2, 0.7)), kind="serif", weight=900, plate=True)
    tag(c, "卷106只记一次夜袭：“夜奔条侯壁，惊东南……果从西北入。吴大败”，与卷57不同", W / 2, 1296, 22, "dim", pa, align="c")
    # 饿而退
    q9 = pulse(t, T("s4_09") - 0.15, ctx.en("s4_10") - 0.4, 0.3, 0.5)
    quote(c, ["吳兵既餓，乃引而去"], W / 2, 400, 76, ctx.prog("s4_09", 0, 0.3), q9 * a, track=3)
    # 追击
    pu = ease(ramp(t, T("s4_10") + 1.8, T("s4_10") + 3.4))
    if pu > 0 and camp_a > 0:
        arrow(c, [(gx, gy + 20), (gx + 120, gy + 130), (gx + 330, gy + 230)], "bone", 10, pu, camp_a * (1 - endk * 0.6), head=28)
        tag(c, "出精兵追击 · 大破之", gx - 120, gy + 190, 28, "bone", camp_a * pu * (1 - endk), kind="serif", weight=700, plate=True, align="c")
    # 三个月
    ma = pulse(t, T("s4_11") - 0.1, T("s4_12") - 0.1, 0.5, 0.4) * a
    if ma > 0:
        rrect(c, 60, 300, 960, 170, 10, "bg", ma * 0.82, blur=14)
        text(c, "三个月", W / 2, 420, font("serif", 900, 112), "bone", ma, align="c", track=10, glow=20, glow_a=0.25)
        tag(c, "“凡相攻守三月，而吴楚破平”（卷57）", W / 2, 474, 30, "gold", ma, align="c", kind="serif", weight=700)
        tag(c, "卷106：正月起兵，“三月皆破，独赵后下”", W / 2, 1290, 24, "dim", ma, align="c")
    # 形篇第二句
    fa = pulse(t, T("s4_12") + 0.1, s1, 0.5, 0.6)
    if fa > 0:
        caption(c, "《孙子兵法 · 形篇》", fa, y=470)
        quote(c, ["勝兵先勝", "而後求戰"], W / 2, 640, 132, ctx.prog("s4_13", 0, 0.3), fa, lh=1.3)
        g = ctx.fin("s4_14", 0.5, 0.2) * fa
        y = 1010
        f = font("serif", 800, 54)
        text(c, "先有胜算", 300, y, f, "bone", g, align="c")
        arrow(c, [(450, y - 18), (630, y - 18)], "gold", 5, ease(ramp(t, T("s4_14") + 0.8, T("s4_14") + 1.6)), g, head=18, smooth=False)
        text(c, "再去开战", 790, y, f, "bone", g * ease(ramp(t, T("s4_14") + 1.4, T("s4_14") + 2.0)), align="c")
        tag(c, "坚壁 · 断粮", 300, y + 58, 30, "dim", g, align="c")
        tag(c, "饿了再追", 790, y + 58, 30, "dim", g * ease(ramp(t, T("s4_14") + 1.4, T("s4_14") + 2.0)), align="c")
        tag(c, "他的胜算，有一半在背后", W / 2, y + 190, 40, "gold", fa * ease(ramp(t, T("s4_14") + 3.0, T("s4_14") + 3.7)), align="c", kind="serif", weight=800)


# ============ s5 巨鹿（示意） ============
JL = (580, 610)       # 巨鹿城
ZH = (580, 1050)      # 章邯军（其南）
RIVER5 = [(700, 1330), (800, 1240), (930, 1180), (1090, 1150)]


def yongdao(c, x, y0, y1, a, prog=1.0, cut=0.0, flow_t=0.0, cut_y=None, w=44):
    """甬道：两侧筑墙，中间运粮。自 y0（南）向 y1（北）修筑。"""
    if a <= 0.003 or prog <= 0:
        return
    yt = lerp(y0, y1, prog)
    for sx in (-1, 1):
        xx = x + sx * w / 2
        if cut > 0 and cut_y is not None:
            gap = 60 * cut
            c.drawLine(xx, y0, xx, min(y0, cut_y + gap / 2), P("bone", a * 0.9, 6, cap=False))
            if yt < cut_y - gap / 2:
                c.drawLine(xx, cut_y - gap / 2, xx, yt, P("bone", a * 0.9 * (1 - 0.6 * cut), 6, cap=False))
        else:
            c.drawLine(xx, y0, xx, yt, P("bone", a * 0.9, 6, cap=False))
        # 墙垛
        yy = y0 - 14
        while yy > yt:
            if not (cut > 0 and cut_y is not None and abs(yy - cut_y) < 36 * cut):
                c.drawLine(xx - sx * 0, yy, xx + sx * 9, yy, P("bone", a * 0.6, 2, cap=False))
            yy -= 22
    # 粮车（小点）北运
    if cut < 1:
        n = 9
        for k in range(n):
            ph = ((flow_t * 0.22 + k / n) % 1.0)
            yy = lerp(y0, y1, ph)
            if yy < yt:
                continue
            if cut > 0 and cut_y is not None and yy < cut_y + 30:
                continue
            circle(c, x, yy, 5, "gold", a * 0.95 * (1 - cut * 0.3))


def boat(c, x, y, a=1.0, sink=0.0, s=1.0):
    if a <= 0.003:
        return
    c.save(); c.translate(x, y + sink * 26); c.rotate(-18 + sink * 34); c.scale(s, s)
    hull = skia.Path(); hull.moveTo(-34, -6); hull.quadTo(0, 16, 34, -6); hull.lineTo(26, 6); hull.quadTo(0, 20, -26, 6); hull.close()
    c.drawPath(hull, P("bone", a * (1 - sink * 0.85)))
    c.restore()
    if sink > 0:
        for k in range(2):
            r = (sink * 1.3 - k * 0.3)
            if 0 < r < 1:
                c.drawOval(skia.Rect.MakeXYWH(x - 50 * r, y + 10 - 12 * r, 100 * r, 24 * r), P("water2", a * (1 - r), 2.5))


def scene_s5(c, ctx):
    t = ctx.t
    T = ctx.st
    s0, s1 = ctx.tl.S("s5")
    a = pulse(t, s0 + 1.6, s1, 0.7, 0.6)
    header(c, 0.5 * a, src="《史记·项羽本纪》")
    if a > 0.003:
        caption(c, "秦二世三年（前207年）· 巨鹿", a * pulse(t, s0 + 1.8, T("s5_04") - 0.3, 0.5, 0.4), y=354)
        tag(c, "示意图：方位据《史记》，位置无确考者不标今地", 72, 1304, 22, "dim2", a)
        # 河（项羽所渡）
        ra = a * ease(ramp(t, T("s5_07") - 0.8, T("s5_07") + 0.2))
        if ra > 0:
            rp = spline(RIVER5)
            c.drawPath(rp, P("water", ra, 30)); c.drawPath(rp, P("water2", ra * 0.8, 10))
            tag(c, "河", 1010, 1126, 30, "water2", ra, kind="serif", weight=700)
        # 巨鹿城
        x, y = JL
        rrect(c, x - 74, y - 74, 148, 148, 6, "black", a); rrect(c, x - 74, y - 74, 148, 148, 6, "dim", a, sw=5)
        rrect(c, x - 58, y - 58, 116, 116, 4, "dim", a * 0.5, sw=1.5)
        text(c, "巨鹿", x, y + 6, font("serif", 900, 40), "bone", a, align="c")
        tag(c, "赵王歇 · 张耳", x, y + 44, 22, "dim", a, align="c")
        # 诸侯军（壁上观）
        za = a * ease(ramp(t, s0 + 2.2, s0 + 3.0))
        for k in range(4):
            block(c, x - 82 + k * 55, 416, 26, 26, "gray", za * 0.9)
        tag(c, "陈馀军 · 巨鹿之北", x - 120, 426, 24, "dim", za, align="r")
        for k in range(6):
            block(c, 120 + (k % 2) * 50, 560 + (k // 2) * 50, 26, 26, "gray", za * 0.9)
        tag(c, "诸侯军十余壁", 145, 726, 24, "dim", za, align="c")
        tag(c, "“莫敢纵兵”", 145, 758, 24, "dim", za, align="c")
        # 王离、涉间围城
        wl_in = ease(ramp(t, s0 + 2.0, s0 + 3.2))
        dead = ease(ramp(t, T("s5_07") + 4.0, T("s5_08") + 0.6))
        hl = pulse(t, T("s5_03"), T("s5_04"), 0.3, 0.5)
        n = 16
        for k in range(n):
            ang = k / n * 2 * math.pi + 0.2
            bx, by = x + math.cos(ang) * 150, y + math.sin(ang) * 150
            if abs(bx - x) < 30 and by > y:        # 留出甬道口
                continue
            gone = clamp(dead * 1.6 - (k * 7 % n) / n * 0.6)
            if gone < 1:
                block(c, bx, by, 28, 28, "qin", a * wl_in * (1 - gone), lit=0.6 + 0.4 * hl)
            elif gone >= 1 and dead > 0:
                rrect(c, bx - 14, by - 14, 28, 28, 3, "dim2", a * 0.35, sw=1.5, dash=(4, 4))
        tag(c, "王离、涉间", x + 270, y - 20, 30, "bone", a * wl_in * (1 - dead), kind="serif", weight=700, align="c", plate=True)
        tag(c, "围巨鹿", x + 270, y + 18, 26, "dim", a * wl_in * (1 - dead), align="c", plate=True)
        tag(c, "杀苏角 · 虏王离", x + 280, y + 2, 30, "red", a * ease(ramp(dead, 0.5, 1.0)), kind="serif", weight=700, align="c", plate=True)
        # 章邯军其南
        zin = ease(ramp(t, T("s5_02") + 0.2, T("s5_02") + 1.6))
        zy = lerp(1230, ZH[1], zin)
        keep = pulse(t, T("s5_08") + 2.2, s1, 0.5, 0.4)
        if keep > 0:
            rrect(c, ZH[0] - 118, zy - 62, 236, 124, 12, "bone", a * 0.45 * keep, blur=18)
        rrect(c, ZH[0] - 100, zy - 46, 200, 92, 6, "black", a * zin); rrect(c, ZH[0] - 100, zy - 46, 200, 92, 6, "bone", a * zin, sw=5)
        rrect(c, ZH[0] - 84, zy - 30, 168, 60, 3, "bone", a * zin * 0.5, sw=1.5)
        text(c, "章邯", ZH[0], zy + 15, font("serif", 900, 44), "bone", a * zin, align="c", track=6)
        tag(c, "「章邯軍其南」", ZH[0] - 250, zy + 12, 28, "gold", a * pulse(t, T("s5_04"), T("s5_06"), 0.4, 0.5), kind="serif", weight=700, align="c", plate=True)
        tag(c, "主力仍在", ZH[0] - 230, zy + 6, 40, "gold", a * keep, kind="serif", weight=900, align="c")
        tag(c, "后随章邯降楚的秦卒“二十余万”（卷7）", ZH[0], zy + 96, 23, "dim", a * keep, align="c", plate=True)
        # 甬道
        yp = ease(ramp(t, T("s5_04") + 0.6, T("s5_04") + 2.8))
        cutk = ease(ramp(t, T("s5_07") + 3.0, T("s5_07") + 3.8))
        yongdao(c, ZH[0], ZH[1] - 50, JL[1] + 172, a, yp, cut=cutk, flow_t=t, cut_y=880)
        ya = a * pulse(t, T("s5_04") + 1.8, T("s5_07") - 0.2, 0.5, 0.5)
        tag(c, "甬道", ZH[0] + 60, 880, 38, "gold", ya, kind="serif", weight=900)
        tag(c, "两侧筑墙，中间运粮", ZH[0] + 60, 924, 28, "dim", ya * ctx.fin("s5_05", 0.4, 1.2))
        tag(c, "输之粟 ↑", ZH[0] - 60, 880, 28, "gold", ya, align="r")
        # 原文
        qa = pulse(t, T("s5_04") - 0.15, ctx.en("s5_04") + 0.4, 0.3, 0.5)
        quote(c, ["章邯軍其南，築甬道而輸之粟"], W / 2, 356, 52, ctx.prog("s5_04", 0, 0.3), qa * a, weight=800, track=2)
        # 同一套
        sm = pulse(t, T("s5_06") + 0.2, T("s5_07") - 0.2, 0.5, 0.4) * a
        if sm > 0:
            rrect(c, 70, 1160, 940, 120, 10, "bg", sm * 0.9, blur=10)
            tag(c, "周亚夫：坚壁 · 断敌粮道", 290, 1206, 32, "bone", sm, align="c", kind="serif", weight=700)
            tag(c, "章邯：居后 · 护己粮道", 790, 1206, 32, "bone", sm, align="c", kind="serif", weight=700)
            tag(c, "两个人盯的，都是粮道", W / 2, 1256, 30, "gold", sm * ctx.fin("s5_06", 0.4, 2.0), align="c")
        # 项羽：渡河、沉船、九战、绝甬道
        xa = a * ease(ramp(t, T("s5_07") - 0.1, T("s5_07") + 0.5))
        cross = ease(ramp(t, T("s5_07") + 0.2, T("s5_07") + 1.6))
        adv = ease(ramp(t, T("s5_07") + 1.8, T("s5_07") + 3.4))
        px = lerp(1000, 860, cross); py = lerp(1280, 1090, cross)
        path = [(860, 1090), (800, 960), (ZH[0] + 40, 880)]
        if adv > 0:
            arrow(c, path, "red", 13, adv, xa, head=32, glow=10)
            sw2 = ease(ramp(t, T("s5_07") + 3.6, T("s5_08") + 0.4))
            arrow(c, [(ZH[0] + 20, 870), (ZH[0] + 140, 800), (JL[0] + 150, JL[1] + 150)], "red", 11, sw2, xa, head=28)
        (ax_, ay_), _ = path_point(spline(path), adv)
        if adv <= 0:
            ax_, ay_ = px, py
        army(c, ax_ + 46 * (1 - adv), ay_ + 30 * (1 - adv), "enemy", xa, n=6, s=1.1)
        tag(c, "项羽", ax_ + 96, ay_ + 60, 34, "red", xa, kind="serif", weight=900, plate=True)
        sink = ease(ramp(t, T("s5_07") + 1.4, T("s5_07") + 3.0))
        for k, (bx, by) in enumerate([(850, 1214), (930, 1184), (790, 1252)]):
            boat(c, bx, by, xa * ease(ramp(cross, 0.2, 0.7)), sink=clamp(sink * 1.3 - k * 0.12))
        tag(c, "皆沉船 · 破釜甑 · 持三日粮", 500, 1250, 26, "red", xa * pulse(t, T("s5_07") + 1.2, T("s5_08") + 1.0, 0.4, 0.5), align="c", plate=True)
        tag(c, "九战 · 绝其甬道", ZH[0] - 190, 850, 30, "red", a * ease(ramp(cutk, 0.3, 1.0)), kind="serif", weight=700, plate=True, align="c")
        if 0 < cutk < 1:
            circle(c, ZH[0], 880, 16 + 70 * cutk, "red", a * (1 - cutk), sw=4)
    chapter(c, t, s0, "贰", "章邯", "同一套打法", ("秦军 · 玄黑", "楚军 · 暖红"))
