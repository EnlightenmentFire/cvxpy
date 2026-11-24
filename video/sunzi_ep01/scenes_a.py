# -*- coding: utf-8 -*-
"""场景 上：公共部件、s1 细柳营、片名卡、s2 竹简、s9 断点、s10 收尾。"""
import math
import numpy as np
import skia
from engine import *

STAGE_T, STAGE_B = 250, 1290


# ============ 公共部件 ============
def header(c, a=0.5, src=None, series=True):
    """左上角系列标记、右上角出处（都在顶部安全区之下）。"""
    if series:
        f = font("serif", 700, 28)
        text(c, "兵法", 72, 286, f, "gold", a * 0.9, track=6)
        c.drawLine(150, 277, 186, 277, P("dim", a * 0.7, 1.5))
        text(c, "第一期  先为不可胜", 200, 286, font("sans", 500, 26), "dim", a, track=2)
    if src:
        text(c, src, W - 72, 286, font("sans", 500, 26), "dim", a * 1.15, align="r")


def source(c, s, a=1.0, y=1296):
    tag(c, s, W / 2, y, 26, "dim2", a, align="c", weight=500)


def caption(c, s, a=1.0, y=352, size=34):
    """时间/地点题记。"""
    if a <= 0.003:
        return
    f = font("serif", 600, size)
    w = tw(s, f, 3)
    c.drawLine(W / 2 - w / 2 - 46, y - size * 0.34, W / 2 - w / 2 - 14, y - size * 0.34, P("gold2", a, 2))
    c.drawLine(W / 2 + w / 2 + 14, y - size * 0.34, W / 2 + w / 2 + 46, y - size * 0.34, P("gold2", a, 2))
    text(c, s, W / 2, y, f, "bone", a * 0.92, align="c", track=3)


def quote(c, lines, cx, y, size, prog=1.0, a=1.0, col="gold", lh=1.34, weight=900, dim=0.10, track=4):
    """原文大字（横排、居中），逐字亮起。prog: 0→1 贯穿全部字。"""
    if a <= 0.003:
        return
    f = font("serif", weight, size)
    n = sum(len(l) for l in lines)
    k = 0
    for i, l in enumerate(lines):
        w = tw(l, f, track)
        x = cx - w / 2
        yy = y + i * size * lh
        for ch in l:
            lit = ease(ramp(prog * n, k - 0.2, k + 0.9))
            cw = f.measureText(ch)
            aa = a * (dim + (1 - dim) * lit)
            if lit > 0.02 and lit < 0.999:
                text(c, ch, x, yy, f, col, a * lit * (1 - lit) * 2.2, glow=size * 0.22, glow_a=0.9)
            text(c, ch, x, yy, f, col if lit > 0.5 else "gold2", aa)
            x += cw + track
            k += 1


def ring_motif(c, cx, cy, a, inner=1.0, outer=0.0, r1=150, r2=300, outer_broken=0.0, q=0.0,
               in_label="营垒", out_label="朝廷", char="己", char_size=120, outer_col="bone", lab_a=1.0):
    """「己」的两层：内圈=营垒（实线），外圈=朝廷/背后（虚线）。全片复用的母题。"""
    if a <= 0.003:
        return
    f = font("serif", 900, char_size)
    text(c, char, cx, cy + char_size * 0.36, f, "gold", a, align="c", glow=18, glow_a=0.35)
    if inner > 0:
        pth = skia.Path(); pth.addCircle(cx, cy, r1)
        c.save(); c.rotate(-90, cx, cy)
        c.drawPath(pth, P("bone", a * 0.9, 4, trim=(0, inner)))
        c.restore()
        tag(c, in_label, cx, cy - r1 - 18, 38, "bone", a * ease(ramp(inner, 0.6, 1)) * lab_a, align="c", kind="serif", weight=700, plate=True)
    if outer > 0:
        pth = skia.Path(); pth.addCircle(cx, cy, r2)
        c.save(); c.rotate(-90, cx, cy)
        if outer_broken > 0:
            # 外圈断裂：分段消失、变红
            segs = 24
            for i in range(segs):
                gone = ramp(outer_broken * segs, i * 0.8, i * 0.8 + 3)
                if i % 3 == 1:
                    gone = ramp(outer_broken, 0.1, 0.5)
                colr = mix("bone", "red", ease(ramp(outer_broken, 0, 0.5)))
                if gone < 1:
                    c.drawPath(pth, P(colr, a * 0.8 * (1 - gone), 3.2, trim=(i / segs + 0.006, (i + 1) / segs - 0.006)))
        else:
            c.drawPath(pth, P(outer_col, a * 0.75, 3.2, dash=(16, 13), trim=(0, outer)))
        c.restore()
        la = a * ease(ramp(outer, 0.6, 1)) * lab_a * (1 - outer_broken)
        tag(c, out_label + ("？" if q > 0.5 else ""), cx, cy - r2 - 18, 38, "gold" if q > 0.5 else outer_col, la, align="c", kind="serif", weight=700, plate=True)


# ============ 营寨俯视 ============
def camp(c, cx, cy, w, h, a=1.0, gate=0.0, lit=1.0, tents=True, moat=True, gate_side="s",
         tent_alpha=None, hq_glow=0.0, seed=3, thick=7.0, towers=True, gate_w=96):
    """营寨俯视示意。gate: 0 关 →1 开。返回营门中心坐标。"""
    if a <= 0.003:
        return (cx, cy + h / 2)
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    la = a * (0.45 + 0.5 * lit)
    if moat:
        m = 30
        pth = skia.Path(); pth.addRoundRect(skia.Rect.MakeLTRB(x0 - m, y0 - m, x1 + m, y1 + m), 18, 18)
        c.drawPath(pth, P("water2", a * 0.55, 10))
        c.drawPath(pth, P("water", a * 0.9, 5, dash=(22, 10)))
    gx, gy = cx, y1
    # 垒墙（南墙留门）
    wall = skia.Path()
    wall.moveTo(gx - gate_w / 2, y1); wall.lineTo(x0, y1); wall.lineTo(x0, y0); wall.lineTo(x1, y0); wall.lineTo(x1, y1); wall.lineTo(gx + gate_w / 2, y1)
    c.drawPath(wall, P("black", a, thick + 8, cap=False))
    c.drawPath(wall, P("bone", la, thick, cap=False))
    inner = skia.Path()
    k = 16
    inner.moveTo(gx - gate_w / 2, y1 - k); inner.lineTo(x0 + k, y1 - k); inner.lineTo(x0 + k, y0 + k); inner.lineTo(x1 - k, y0 + k); inner.lineTo(x1 - k, y1 - k); inner.lineTo(gx + gate_w / 2, y1 - k)
    c.drawPath(inner, P("dim", a * 0.5, 1.6))
    # 墙上的栅齿
    tick = P("bone", la * 0.55, 2, cap=False)
    step = 26
    xx = x0 + step
    while xx < x1 - 4:
        if abs(xx - gx) > gate_w / 2 + 6:
            c.drawLine(xx, y1 - 5, xx, y1 + 9, tick)
        c.drawLine(xx, y0 - 9, xx, y0 + 5, tick)
        xx += step
    yy = y0 + step
    while yy < y1 - 4:
        c.drawLine(x0 - 9, yy, x0 + 5, yy, tick); c.drawLine(x1 - 5, yy, x1 + 9, yy, tick)
        yy += step
    if towers:
        for tx, ty in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            rrect(c, tx - 17, ty - 17, 34, 34, 3, "black", a)
            rrect(c, tx - 17, ty - 17, 34, 34, 3, "bone", la, sw=3.2)
    # 门阙与门扇
    for sx in (-1, 1):
        px = gx + sx * gate_w / 2
        rrect(c, px - 11, y1 - 22, 22, 44, 3, "black", a)
        rrect(c, px - 11, y1 - 22, 22, 44, 3, "bone", la, sw=3.2)
        ang = sx * gate * 78
        c.save(); c.translate(px - sx * 9, y1); c.rotate(ang)
        c.drawLine(0, 0, -sx * (gate_w / 2 - 12), 0, P("gold", a * (0.95 - 0.25 * gate), 6.5, cap=False))
        c.restore()
    # 帐幕
    if tents:
        rng = np.random.default_rng(seed)
        ta = a * (tent_alpha if tent_alpha is not None else 0.55)
        cols = max(4, int((w - 150) // 62)); rows = max(4, int((h - 150) // 58))
        gx0 = cx - (cols - 1) * 31; gy0 = cy - (rows - 1) * 29
        for r in range(rows):
            for q in range(cols):
                px, py = gx0 + q * 62, gy0 + r * 58
                if abs(px - cx) < 70 and abs(py - cy) < 64:
                    continue
                if abs(px - cx) < 34 and py > cy:     # 中轴甬路
                    continue
                pth = poly([(px - 13, py + 9), (px, py - 11), (px + 13, py + 9)], True)
                c.drawPath(pth, P("ink2", ta))
                c.drawPath(pth, P("dim", ta * 0.9, 1.4))
        # 中军大帐
        if hq_glow > 0:
            circle(c, cx, cy, 70, "gold", a * 0.28 * hq_glow, blur=36)
        pth = poly([(cx - 34, cy + 24), (cx, cy - 30), (cx + 34, cy + 24)], True)
        c.drawPath(pth, P("black", a))
        c.drawPath(pth, P("gold", a * (0.55 + 0.45 * hq_glow), 3))
        c.drawLine(cx, cy - 30, cx, cy - 58, P("gold", a * 0.8, 2.2))
        c.drawPath(poly([(cx, cy - 58), (cx + 22, cy - 51), (cx, cy - 44)], True), P("gold", a * 0.8))
    return (gx, gy)


def archer(c, x, y, s=1.0, a=1.0, flip=1, col="bone"):
    """弓弩手剪影（持满）。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s * flip, s)
    p = P(col, a)
    c.drawCircle(0, -30, 6.5, p)
    c.drawPath(poly([(-8, -22), (8, -22), (11, 12), (-11, 12)], True), p)
    c.drawPath(poly([(-9, -24), (9, -24), (0, -40)], True), P(col, a * 0.9))  # 盔
    bow = skia.Path(); bow.moveTo(14, -34); bow.quadTo(32, -10, 14, 14)
    c.drawPath(bow, P(col, a, 2.6))
    c.drawLine(14, -34, 14, 14, P(col, a * 0.7, 1.2))
    c.drawLine(-2, -10, 30, -10, P(col, a, 2))
    c.restore()


def carriage(c, x, y, a=1.0, s=1.0):
    """天子车驾（俯视示意）：伞盖、车舆、两马、前导骑。朝上行进。"""
    if a <= 0.003:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    g = P("gold", a); gs = P("gold", a, 2.4); dk = P("black", a)
    # 两匹马
    for dx in (-15, 15):
        c.drawOval(skia.Rect.MakeXYWH(dx - 8, -86, 16, 44), g)
        c.drawOval(skia.Rect.MakeXYWH(dx - 5, -100, 10, 20), g)
    c.drawLine(-15, -46, -15, -22, gs); c.drawLine(15, -46, 15, -22, gs)
    # 车轮、车舆、伞盖
    rrect(c, -40, -18, 9, 50, 3, "gold", a); rrect(c, 31, -18, 9, 50, 3, "gold", a)
    rrect(c, -28, -26, 56, 62, 5, "black", a); rrect(c, -28, -26, 56, 62, 5, "gold", a, sw=3)
    c.drawCircle(0, 4, 26, dk); c.drawCircle(0, 4, 26, gs); c.drawCircle(0, 4, 5, g)
    for k in range(8):
        an = k * math.pi / 4
        c.drawLine(0, 4, 26 * math.cos(an), 4 + 26 * math.sin(an), P("gold", a * 0.55, 1.3))
    # 属车骑从
    for i, (dx, dy) in enumerate([(-58, -60), (58, -60), (-58, 0), (58, 0), (-58, 60), (58, 60), (-22, 86), (22, 86)]):
        c.drawOval(skia.Rect.MakeXYWH(dx - 6, dy - 15, 12, 30), P("gold", a * 0.7))
    c.restore()


# ============ s1 冷启动：细柳营 ============
def scene_s1(c, ctx):
    t = ctx.t
    s0, s1 = ctx.tl.S("s1")
    lt = t - s0
    a_all = pulse(t, s0, s1, 0.9, 0.5)
    late = ctx.fin("s1_07", 0.8)                 # 后半：营寨退暗
    c.save()
    z = lerp(1.0, 1.07, ease(ramp(t, s0, ctx.st("s1_07"))))   # 缓推
    c.translate(W / 2, 850); c.scale(z, z); c.translate(-W / 2, -850)
    cx, cy, cw, chh = 540, 850, 700, 430
    gate = ease(ramp(t, ctx.st("s1_05") + 0.2, ctx.st("s1_05") + 1.6))
    camp_a = a_all * lerp(1.0, 0.34, late)
    gx, gy = camp(c, cx, cy, cw, chh, camp_a, gate=gate, lit=1.0, hq_glow=ease(ramp(t, ctx.st("s1_06"), ctx.st("s1_07") + 0.6)), seed=5)
    # 弓弩手：营门两侧墙内一线
    al = camp_a * ease(ramp(lt, 0.4, 1.4))
    hot = pulse(t, ctx.st("s1_01") + 1.2, ctx.en("s1_04"), 0.5, 0.8)
    for i in range(5):
        for sx in (-1, 1):
            archer(c, gx + sx * (92 + i * 54), gy - 44, 0.82, al * (0.6 + 0.4 * hot), flip=1, col=mix("bone", "gold", 0.35 * hot))
    # 车驾：自下而上，至营门外停住；开门后按辔徐行
    y_stop = gy + 128
    y_in = lerp(y_stop, gy + 16, ease(ramp(t, ctx.st("s1_05") + 1.2, ctx.en("s1_06") + 0.8)) ** 1.0)
    y_car = lerp(1500, y_stop, eout(ramp(t, s0 + 0.2, ctx.en("s1_01") - 0.1))) if t < ctx.st("s1_05") + 1.2 else y_in
    carriage(c, gx, y_car, a_all * (1 - late), 0.86)
    # 被拦：门前一道横线闪动
    blk = pulse(t, ctx.en("s1_01") - 0.5, ctx.st("s1_05") + 0.3, 0.3, 0.5)
    if blk > 0:
        fl = 0.65 + 0.35 * math.sin(t * 7)
        c.drawLine(gx - 120, gy + 34, gx + 120, gy + 34, P("red", blk * fl * a_all, 4, dash=(14, 10)))
        tag(c, "不得入", gx + 150, gy + 46, 32, "red", blk * a_all, kind="serif", weight=700)
    # 「按辔徐行」小注
    sl = pulse(t, ctx.st("s1_05") + 1.4, ctx.st("s1_07") + 0.2, 0.5, 0.5) * a_all
    tag(c, "「軍中不得驅馳」", gx + 96, gy + 84, 32, "gold", sl, kind="serif", weight=700)
    tag(c, "天子的车，也只能按辔徐行", gx + 110, gy + 128, 26, "dim", sl)
    tag(c, "文帝遣使持节，壁门乃开", gx - 110, gy + 128, 26, "dim", pulse(t, ctx.st("s1_05") + 0.1, ctx.st("s1_07") + 0.2, 0.5, 0.5) * a_all, align="r")
    c.restore()

    # 题记与出处
    caption(c, "汉文帝后六年（前158年）· 细柳", a_all * (1 - late) * ease(ramp(lt, 0.3, 1.3)), y=342)
    header(c, a_all * 0.5, src="《史记·绛侯周勃世家》", series=False)
    # 原文大字
    qa = ctx.span("s1_03", "s1_04", 0.3, 0.5, pre=0.15)
    quote(c, ["軍中聞將軍令", "不聞天子之詔"], W / 2, 462, 78, ctx.prog("s1_03", 0, 0.5), qa * a_all)
    qb = ctx.span("s1_06", "s1_06", 0.25, 0.5, pre=0.1, post=0.5)
    quote(c, ["此真將軍矣"], W / 2, 520, 124, ctx.prog("s1_06", 0, 0.3), qb * a_all)
    # 人名
    na = ctx.fin("s1_07", 0.7, 0.5) * a_all
    if na > 0:
        text(c, "周亚夫", W / 2, 500, font("serif", 900, 136), "bone", na, align="c", track=18, glow=22, glow_a=0.25)
        tag(c, "条侯 · 绛侯周勃之子", W / 2, 562, 32, "dim", na, align="c", kind="serif", weight=600)
        w1 = ctx.fin("s1_08", 0.6, 0.6) * a_all
        tag(c, "前154年", 300, 1196, 34, "gold", w1, align="c", kind="serif", weight=700)
        tag(c, "三个月破吴楚", 300, 1244, 32, "bone", w1, align="c")
        w2 = ctx.fin("s1_09", 0.6, 0.5) * a_all
        tag(c, "前143年", 780, 1196, 34, "red", w2, align="c", kind="serif", weight=700)
        tag(c, "下狱，绝食五日而死", 780, 1244, 32, "bone", w2, align="c")
        pr = ease(ramp(t, ctx.st("s1_09") + 0.4, ctx.st("s1_09") + 1.6))
        if pr > 0:
            arrow(c, [(470, 1214), (610, 1214)], "dim", 2.5, pr, a_all * 0.9, head=12, smooth=False)


# ============ 片名卡 ============
def scene_title(c, ctx):
    t = ctx.t
    s0, s1 = ctx.tl.S("title")
    a = pulse(t, s0, s1, 0.5, 0.5)
    lt = t - s0
    text(c, "兵 法", W / 2, 560, font("serif", 700, 54), "gold", a * ease(ramp(lt, 0.0, 0.6)), align="c", track=30)
    c.drawLine(W / 2 - 90, 600, W / 2 + 90, 600, P("gold2", a * ease(ramp(lt, 0.2, 0.8)), 2))
    tag(c, "第 一 期", W / 2, 656, 34, "dim", a * ease(ramp(lt, 0.2, 0.8)), align="c", kind="serif", weight=600)
    f = font("serif", 900, 168)
    s = "先為不可勝"
    w = tw(s, f, 10)
    x = W / 2 - w / 2
    for i, ch in enumerate(s):
        ai = ease(ramp(lt, 0.35 + i * 0.13, 0.9 + i * 0.13))
        text(c, ch, x, 900 + (1 - ai) * 16, f, "bone", a * ai, glow=26, glow_a=0.22)
        x += f.measureText(ch) + 10
    b = a * ease(ramp(lt, 1.2, 1.9))
    text(c, "同一句兵法", W / 2, 1040, font("serif", 600, 46), "dim", b, align="c", track=8)
    text(c, "周亚夫赢了", W / 2 - 150, 1136, font("serif", 800, 54), "bone", b, align="c", track=4)
    text(c, "章邯输了", W / 2 + 170, 1136, font("serif", 800, 54), "red", b, align="c", track=4)


# ============ 竹简 ============
def slips(c, cols, cx, cy, size, lit, a=1.0, seed=1, gap=18, hot=None, dark=None):
    """竹简：cols 自右向左的列文本；lit(i_col, i_char)->0..1 点亮度。
    hot/dark: {(col,char): 强度} 个别字高亮/压暗。"""
    if a <= 0.003:
        return {}
    rng = np.random.default_rng(seed)
    sw = size * 1.36
    step = size * 1.15
    n = len(cols)
    maxlen = max(len(s) for s in cols)
    hh = maxlen * step + size * 0.9
    total = n * sw + (n - 1) * gap
    pos = {}
    xs = [cx + total / 2 - sw / 2 - i * (sw + gap) for i in range(n)]
    for i, s in enumerate(cols):
        x = xs[i]
        dy = rng.normal() * 9
        top = cy - hh / 2 + dy
        r = skia.Rect.MakeXYWH(x - sw / 2, top, sw, hh)
        sh = skia.GradientShader.MakeLinear([(x - sw / 2, 0), (x + sw / 2, 0)],
                                            [C("#1c170f", a), C("bamboo2", a), C("bamboo3", a), C("bamboo", a), C("#17130c", a)],
                                            [0, 0.18, 0.5, 0.86, 1])
        c.drawRoundRect(r, 5, 5, skia.Paint(AntiAlias=True, Shader=sh))
        # 竹纹
        for k in range(9):
            lx = x - sw / 2 + 6 + rng.random() * (sw - 12)
            c.drawLine(lx, top + 8, lx + rng.normal() * 2, top + hh - 8, P("#000000" if k % 2 else "#8a7650", a * (0.10 + 0.08 * rng.random()), 1.2))
        # 竹节
        for ny in (0.31, 0.71):
            yy = top + hh * (ny + rng.normal() * 0.02)
            c.drawLine(x - sw / 2 + 2, yy, x + sw / 2 - 2, yy, P("#0d0a06", a * 0.55, 2))
            c.drawLine(x - sw / 2 + 2, yy + 2.5, x + sw / 2 - 2, yy + 2.5, P("#8a7650", a * 0.16, 1))
        c.drawRoundRect(r, 5, 5, P("#8a7650", a * 0.22, 1.5))
        pos[i] = (x, top)
    # 编绳
    for ny in (0.085, 0.915):
        yy = cy - hh / 2 + hh * ny
        c.drawLine(xs[-1] - sw / 2 - 12, yy, xs[0] + sw / 2 + 12, yy, P("#0c0a07", a * 0.9, 7))
        c.drawLine(xs[-1] - sw / 2 - 12, yy - 1.5, xs[0] + sw / 2 + 12, yy - 1.5, P("#6b5a3c", a * 0.55, 2.2, dash=(7, 5)))
    f = font("serif", 900, size)
    out = {}
    for i, s in enumerate(cols):
        x, top = pos[i]
        y0 = top + size * 1.22
        for j, ch in enumerate(s):
            l = clamp(lit(i, j))
            y = y0 + j * step
            hk = (hot or {}).get((i, j), 0.0)
            dk = (dark or {}).get((i, j), 0.0)
            # 未亮：刻痕般的暗字
            text(c, ch, x, y, f, "#110d08", a * 0.85 * (1 - l), align="c")
            text(c, ch, x + 1, y + 1.5, f, "#6a5a3d", a * 0.42 * (1 - l), align="c")
            if l > 0.01:
                colr = mix(mix("gold", "bone", 0.25 + 0.5 * hk), "#3a3020", dk * 0.85)
                text(c, ch, x, y, f, colr, a * l, align="c", glow=size * (0.10 + 0.14 * hk) * (1 - dk), glow_a=(0.5 + 0.3 * hk) * (1 - dk))
            out[(i, j)] = (x, y - size * 0.36)
    return out


def scene_s2(c, ctx):
    t = ctx.t
    s0, s1 = ctx.tl.S("s2")
    a_all = pulse(t, s0, s1, 0.6, 0.5)
    header(c, a_all * 0.5, src="《孙子兵法 · 形篇》")
    # A：昔之善戰者…
    aA = ctx.span("s2_01", "s2_03", 0.6, 0.5, pre=0.4) * a_all
    if aA > 0:
        cols = ["昔之善戰者", "先為不可勝", "以待敵之可勝"]
        p = ctx.prog("s2_02", 0.1, 0.5) * 16
        base = [0, 5, 10]
        slips(c, cols, W / 2, 800, 112, lambda i, j: ease(ramp(p, base[i] + j - 0.3, base[i] + j + 0.8)), aA, seed=2, gap=26)
    # B：不可勝在己，可勝在敵
    tB0 = ctx.st("s2_04")
    tZ = ctx.st("s2_08")
    aB = pulse(t, tB0 - 0.1, ctx.st("s2_09") + 0.45, 0.5, 0.5) * a_all
    if aB > 0:
        cols = ["不可勝在己", "可勝在敵"]
        p = ctx.prog("s2_05", 0.05, 0.3) * 9.6
        base = [0, 5]
        z = ease(ramp(t, tZ - 0.1, tZ + 1.2))
        dark = {}
        if z > 0:
            for i, s in enumerate(cols):
                for j in range(len(s)):
                    if (i, j) != (0, 4):
                        dark[(i, j)] = z
        c.save()
        # 推近「己」：以「己」为锚点放大并移向画面中部
        zc = lerp(1.0, 1.08, z)
        c.translate(W / 2, 800); c.scale(zc, zc); c.translate(-W / 2, -800)
        pos = slips(c, cols, W / 2, 800, 124, lambda i, j: ease(ramp(p, base[i] + j - 0.3, base[i] + j + 0.8)), aB, seed=4, gap=40,
                    hot={(0, 4): z}, dark=dark)
        if z > 0.2 and pos:
            x, y = pos[(0, 4)]
            qa = ease(ramp(t, tZ + 0.8, tZ + 1.4)) * aB
            text(c, "？", x + 150, y + 50, font("serif", 900, 136), "bone", qa, align="c", glow=20, glow_a=0.4)
        c.restore()
        # 两句白话对照
        ga = pulse(t, ctx.st("s2_06"), ctx.st("s2_08") - 0.2, 0.5, 0.4) * a_all
        if ga > 0:
            f1 = font("serif", 800, 52)
            text(c, "不败", 880, 700, f1, "bone", ga, align="c"); tag(c, "靠自己", 880, 756, 36, "dim", ga, align="c")
            g2 = ga * ctx.fin("s2_06", 0.4, 1.1)
            text(c, "能不能赢", 200, 700, f1, "red", g2, align="c"); tag(c, "看对手", 200, 756, 36, "dim", g2, align="c")
    # C：「己」有多大 —— 两层圈
    aC = pulse(t, ctx.st("s2_09") + 0.05, ctx.en("s2_10") + 0.3, 0.6, 0.5) * a_all
    if aC > 0:
        inner = ease(ramp(t, ctx.st("s2_09") + 0.2, ctx.st("s2_09") + 1.2))
        outer = ease(ramp(t, ctx.st("s2_09") + 1.6, ctx.st("s2_09") + 2.8))
        mv = ease(ramp(t, ctx.st("s2_10") - 0.2, ctx.st("s2_10") + 0.8))
        cyy = lerp(760, 640, mv)
        sc = lerp(1.0, 0.82, mv)
        c.save(); c.translate(W / 2, cyy); c.scale(sc, sc); c.translate(-W / 2, -cyy)
        ring_motif(c, W / 2, cyy, aC, inner, outer, r1=170, r2=330, q=1.0, char_size=150)
        c.restore()
        # 两个人
        pa = ctx.fin("s2_10", 0.6, 0.4) * aC
        if pa > 0:
            f = font("serif", 900, 84)
            text(c, "周亚夫", 300, 1120, f, "bone", pa, align="c", track=6)
            text(c, "章邯", 790, 1120, f, "bone", pa * ctx.fin("s2_10", 0.5, 0.9), align="c", track=6)
            c.drawLine(540, 1040, 540, 1150, P("dim2", pa, 2))
            tag(c, "同一件事", W / 2, 1216, 34, "gold", pa * ctx.fin("s2_10", 0.5, 1.3), align="c", kind="serif", weight=700)
            tag(c, "赢", 300, 1216, 40, "bone", pa * ctx.fin("s2_10", 0.5, 2.1), align="c", kind="serif", weight=900)
            tag(c, "降", 790, 1216, 40, "red", pa * ctx.fin("s2_10", 0.5, 2.3), align="c", kind="serif", weight=900)


# ============ s9 断点 ============
def scene_s9(c, ctx):
    t = ctx.t
    s0, s1 = ctx.tl.S("s9")
    a_all = pulse(t, s0, s1, 0.6, 0.6)
    header(c, a_all * 0.5, src="《孙子兵法 · 谋攻篇》")
    aA = pulse(t, s0, ctx.en("s9_05") + 0.2, 0.6, 0.6) * a_all
    if aA > 0:
        cols = ["將能而君", "不御者勝"]
        p = ctx.prog("s9_02", 0.05, 0.3) * 8.6
        base = [0, 4]
        # 「君不御」= (0,3) (1,0) (1,1)：先亮，后暗
        hl = ease(ramp(t, ctx.st("s9_03") + 0.6, ctx.st("s9_03") + 1.4))
        dk = ease(ramp(t, ctx.st("s9_04") + 2.2, ctx.st("s9_04") + 3.6))
        keys = [(0, 3), (1, 0), (1, 1)]
        hot = {k: hl * (1 - dk) for k in keys}
        dark = {k: dk for k in keys}
        cy = 770
        slips(c, cols, W / 2, cy, 132, lambda i, j: ease(ramp(p, base[i] + j - 0.3, base[i] + j + 0.8)), aA, seed=9, gap=44, hot=hot, dark=dark)
        caption(c, "知胜有五 · 其五", aA, y=350)
        # 前半句 / 后半句
        h1 = ctx.fin("s9_04", 0.5, 0.1) * aA
        h2 = ease(ramp(t, ctx.st("s9_04") + 2.0, ctx.st("s9_04") + 2.6)) * aA
        f = font("serif", 900, 56)
        if h1 > 0:
            text(c, "將能", 290, 1150, f, "gold", h1, align="c", track=8)
            tag(c, "前半句：将军自己练得出", 290, 1202, 28, "bone", h1, align="c")
        if h2 > 0:
            text(c, "君不御", 790, 1150, f, mix("gold", "dim", dk), h2, align="c", track=8)
            tag(c, "后半句：将军自己做不出", 790, 1202, 28, "red", h2, align="c")
        h3 = ctx.fin("s9_05", 0.5, 0.1) * aA
        if h3 > 0:
            tag(c, "周亚夫：景帝下诏，却未换将", 290, 1262, 28, "bone", h3, align="c", kind="serif", weight=700)
            tag(c, "章邯：背后没有这样的人", 790, 1262, 28, "red", h3 * ctx.fin("s9_05", 0.4, 2.0), align="c", kind="serif", weight=700)
    aC = ctx.fin("s9_06", 0.7, -0.2) * a_all
    if aC > 0:
        st = ctx.st("s9_06")
        inner = ease(ramp(t, st, st + 0.9))
        outer = ease(ramp(t, st + 1.0, st + 2.4))
        ring_motif(c, W / 2, 760, aC, inner, outer, r1=150, r2=390, q=0.0, char_size=150, out_label="朝廷 · 背后", outer_col="gold")
        tag(c, "不可勝在己", W / 2, 1262, 58, "gold", aC * ease(ramp(t, st + 0.2, st + 1.0)), align="c", kind="serif", weight=900)


# ============ s10 收尾 + 片尾 ============
def scene_s10(c, ctx):
    t = ctx.t
    s0, _ = ctx.tl.S("s10")
    e0, e1 = ctx.tl.S("end")
    a_all = pulse(t, s0, e1, 0.7, 0.9)
    header(c, a_all * 0.5)
    # 回到最初的营垒俯视，缓慢拉远；外圈（背后）随拉远显形
    zp = ease(ramp(t, s0, e0 + 0.8))
    z = lerp(1.0, 0.5, zp)
    cyc = lerp(850, 880, zp)
    c.save(); c.translate(W / 2, cyc); c.scale(z, z); c.translate(-W / 2, -850)
    camp(c, 540, 850, 700, 430, a_all * 0.85, gate=0.0, lit=0.9, hq_glow=0.7, seed=5)
    ra = ease(ramp(zp, 0.45, 0.8))
    pth = skia.Path(); pth.addCircle(540, 850, 700)
    c.save(); c.rotate(-90, 540, 850)
    c.drawPath(pth, P("gold", a_all * 0.6 * ra, 3.2 / z, dash=(30, 24), trim=(0, ease(ramp(zp, 0.45, 1.0)))))
    c.restore()
    c.restore()
    # 两句映射（轻点）
    m1 = ctx.span("s10_01", "s10_01", 0.5, 0.5) * a_all
    if m1 > 0:
        tag(c, "做生意", W / 2, 372, 36, "gold", m1, align="c", kind="serif", weight=700)
        text(c, "先有现金和退路，再谈出击", W / 2, 444, font("serif", 700, 50), "bone", m1, align="c")
    m2 = ctx.span("s10_02", "s10_02", 0.5, 0.5) * a_all
    if m2 > 0:
        tag(c, "在职场", W / 2, 372, 36, "gold", m2, align="c", kind="serif", weight=700)
        text(c, "手艺 · 口碑 · 不只靠一个人", W / 2, 444, font("serif", 700, 50), "bone", m2, align="c")
    q = pulse(t, ctx.st("s10_03") + 0.3, e1 - 0.3, 0.6, 0.8)
    if q > 0:
        quote(c, ["勝可知", "而不可為"], W / 2, 372, 96, ctx.prog("s10_04", 0, 0.2), q * a_all, lh=1.28)
    ea = ease(ramp(t, e0 + 0.5, e0 + 1.4)) * a_all
    if ea > 0:
        tag(c, "引文据《史记》卷七、五十七、五十八、一百六，《汉书》卷五，《孙子兵法》", W / 2, 1268, 23, "dim", ea, align="c")
        tag(c, "地图为示意 · 今地系后世考证", W / 2, 1302, 23, "dim", ea, align="c")
