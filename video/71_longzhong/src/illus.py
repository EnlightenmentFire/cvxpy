# -*- coding: utf-8 -*-
"""开场插画：隆中雪后，竹林、草庐、门推开；门外将军，门内青年铺开发光的地图。全部矢量绘制（示意，非写实）。"""
import math, numpy as np, skia
from gfx import *
from geo import W, H

_static = {}
RNG = np.random.default_rng(11)


def _grad_rect(c, x, y, w, h, cols, pos, vertical=True, a=1.0):
    p = skia.Paint()
    pts = [(x, y), (x, y + h)] if vertical else [(x, y), (x + w, y)]
    p.setShader(skia.GradientShader.MakeLinear(pts, [rgba(cc, a) for cc in cols], pos))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def _ridge(c, y0, amp, seed, col, a=1.0, blur=0.0, step=6):
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28, 4); fr = [1.3, 2.9, 6.1, 13.0]; am = [1.0, 0.45, 0.22, 0.1]
    p = skia.Path(); p.moveTo(-20, H)
    for x in range(-20, W + 30, step):
        u = x / W
        yy = y0 - amp * sum(m * (0.5 + 0.5 * math.sin(f * u * 6.28 + q)) for m, f, q in zip(am, fr, ph))
        p.lineTo(x, yy)
    p.lineTo(W + 30, H); p.close()
    pt = skia.Paint(AntiAlias=True, Color=rgba(col, a))
    if blur: pt.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(p, pt)


def _bamboo(c, x, y0, y1, wdt, col, a, sway=0.0, seed=0, leaves=True, snow=True, lean=0.0):
    """一根竹：分节，顶部微弯，带叶簇与积雪。"""
    r = np.random.default_rng(seed)
    n = 14
    pts = []
    for i in range(n + 1):
        u = i / n
        dx = lean * u * u * 120 + sway * u ** 2.2 * 60
        pts.append((x + dx, y0 + (y1 - y0) * u))
    p = skia.Paint(AntiAlias=True, Color=rgba(col, a), Style=skia.Paint.kStroke_Style, StrokeWidth=wdt)
    p.setStrokeCap(skia.Paint.kButt_Cap)
    c.drawPath(mkpath(pts), p)
    # 节
    seg = r.uniform(70, 110)
    yy = y0 - seg
    while yy > y1:
        u = (yy - y0) / (y1 - y0)
        xx = x + lean * u * u * 120 + sway * u ** 2.2 * 60
        line(c, [(xx - wdt * 0.62, yy), (xx + wdt * 0.62, yy)], mix(col, '#000000', 0.35), max(1.5, wdt * 0.22), a)
        if snow and r.random() < 0.35:
            rrect(c, xx - wdt * 0.5, yy - wdt * 0.28, wdt, wdt * 0.32, wdt * 0.15, '#E9EEF2', a * 0.85)
        # 叶簇
        if leaves and u > 0.35 and r.random() < 0.55:
            side = r.choice([-1, 1])
            for k in range(r.integers(2, 5)):
                L = r.uniform(40, 85) * (wdt / 14 + 0.4)
                ang = side * r.uniform(0.25, 0.9) + math.pi / 2 * 0 + sway * 0.3
                lx = xx + side * L * math.cos(ang * 0.6); ly = yy + 8 + L * 0.45 * (k + 1) / 3
                lp = skia.Path(); lp.moveTo(xx, yy + 4)
                lp.quadTo((xx + lx) / 2, yy - 6 + k * 6, lx, ly)
                lp.quadTo((xx + lx) / 2 + 4, yy + 12 + k * 6, xx, yy + 4)
                c.drawPath(lp, skia.Paint(AntiAlias=True, Color=rgba(mix(col, '#1B2A22', 0.3), a * 0.95)))
                if snow and r.random() < 0.5:
                    line(c, [((xx + lx) / 2, yy - 2 + k * 6), (lx * 0.7 + xx * 0.3, ly - 6)], '#EEF2F4', 2.0, a * 0.7)
        yy -= seg


def _build_static():
    """远景：天空、远山、雾、远竹（缓存）。"""
    s = skia.Surface(W, H); c = s.getCanvas()
    _grad_rect(c, 0, 0, W, H, ['#1B2533', '#3A4A5A', '#7C8C98', '#A9B4BC'], [0.0, 0.35, 0.62, 0.78])
    # 远山（雪顶）
    _ridge(c, 720, 260, 3, '#5E6F7E', 0.9, blur=1.5)
    _ridge(c, 760, 150, 5, '#7E8E9A', 0.85)
    _ridge(c, 820, 120, 7, '#9AA8B1', 0.9)
    # 雾
    _grad_rect(c, 0, 640, W, 360, ['#B8C2C9', '#B8C2C9'], [0, 1], a=0.0)
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 640), (0, 980)], [rgba('#C9D2D8', 0.0), rgba('#C9D2D8', 0.75), rgba('#C9D2D8', 0.0)], [0, 0.6, 1]))
    c.drawRect(skia.Rect.MakeXYWH(0, 640, W, 360), p)
    # 远竹（灰、虚）
    r = np.random.default_rng(2)
    for i in range(46):
        x = r.uniform(-40, W + 40); w_ = r.uniform(5, 9)
        _bamboo(c, x, 1100, r.uniform(80, 420), w_, mix('#6E8078', '#A9B6B4', r.uniform(0.2, 0.7)), 0.55, seed=int(r.integers(1e6)), snow=True, lean=r.uniform(-0.3, 0.3))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 700), (0, 1150)], [rgba('#C4CDD3', 0.0), rgba('#C4CDD3', 0.55)]))
    c.drawRect(skia.Rect.MakeXYWH(0, 700, W, 450), p)
    # 雪地
    gp = skia.Path(); gp.moveTo(0, 1180); gp.cubicTo(300, 1130, 700, 1160, W, 1120); gp.lineTo(W, H); gp.lineTo(0, H); gp.close()
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([(0, 1120), (0, H)], [rgba('#DCE3E8'), rgba('#9FAAB4'), rgba('#5B6672')], [0, 0.45, 1]))
    c.drawPath(gp, p)
    # 雪地起伏阴影
    for k in range(9):
        y = r.uniform(1230, 1800); x = r.uniform(-200, W)
        rrect(c, x, y, r.uniform(300, 700), r.uniform(18, 40), 30, '#7F8A96', 0.18, blur=16)
    _static['bg'] = s.makeImageSnapshot()


HUT = dict(x=150, y=760, w=560, h=440)       # 草庐墙体（左上角 x,y）
DOOR = dict(x=300, y=900, w=250, h=300)


def _hut(c, a, door, light, t):
    hx, hy, hw, hh = HUT['x'], HUT['y'], HUT['w'], HUT['h']
    # 墙
    rrect(c, hx - 10, hy + hh - 10, hw + 20, 30, 10, '#000000', 0.35 * a, blur=16)
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([(hx, hy), (hx + hw, hy)], [rgba('#5B4A3A', a), rgba('#3F3328', a)]))
    c.drawRect(skia.Rect.MakeXYWH(hx, hy + 70, hw, hh - 70), p)
    # 木柱
    for xx in (hx + 8, hx + hw - 28, hx + 160, hx + hw - 180):
        rrect(c, xx, hy + 70, 20, hh - 70, 3, '#2C231B', a)
    # 屋顶（茅草）：梯形 + 草纹 + 积雪
    rp = skia.Path(); rp.moveTo(hx - 70, hy + 110); rp.lineTo(hx + 80, hy - 70); rp.lineTo(hx + hw - 80, hy - 70); rp.lineTo(hx + hw + 70, hy + 110); rp.close()
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([(0, hy - 70), (0, hy + 110)], [rgba('#6E5B40', a), rgba('#4A3B28', a)]))
    c.drawPath(rp, p)
    r = np.random.default_rng(5)
    for i in range(160):
        u = r.uniform(0, 1); v = r.uniform(0.15, 1)
        x0 = lerp(hx + 80, hx - 70, v) + (lerp(hx + hw - 80, hx + hw + 70, v) - lerp(hx + 80, hx - 70, v)) * u
        y0 = lerp(hy - 70, hy + 110, v)
        line(c, [(x0, y0), (x0 + r.uniform(-6, 6), y0 + r.uniform(16, 34))], '#2E2418', 1.4, 0.5 * a)
    # 积雪
    sp = skia.Path(); sp.moveTo(hx - 74, hy + 104)
    sp.lineTo(hx + 76, hy - 76); sp.lineTo(hx + hw - 76, hy - 76); sp.lineTo(hx + hw + 74, hy + 104)
    for k in range(14, -1, -1):
        u = k / 14
        xx = lerp(hx + 80, hx + hw - 80, u); yy = hy - 30 + 10 * math.sin(k * 1.7)
        if k in (0, 14): continue
    sp.lineTo(hx + hw + 30, hy + 98); sp.cubicTo(hx + hw - 120, hy - 20, hx + 120, hy - 26, hx - 30, hy + 98); sp.close()
    c.drawPath(sp, skia.Paint(AntiAlias=True, Color=rgba('#EEF2F5', 0.96 * a)))
    line(c, [(hx - 74, hy + 104), (hx + hw + 74, hy + 104)], '#2B2218', 6, a)
    # 门洞内部：暖光
    dx, dy, dw, dh = DOOR['x'], DOOR['y'], DOOR['w'], DOOR['h']
    inside = mix('#1E130B', '#8A5428', light)
    p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeRadial((dx + dw * 0.35, dy + dh * 0.72), dh * 0.85,
                                                                               [rgba(mix('#2A1A10', '#E8A458', light), a), rgba(inside, a), rgba('#140C06', a)], [0, 0.5, 1]))
    c.drawRect(skia.Rect.MakeXYWH(dx, dy, dw, dh), p)
    return dx, dy, dw, dh


def _youth(c, x, y, a, s=1.0, mapu=0.0, mglow=0.0, lit=(0, 0), t=0.0):
    """门内青年：跪坐，头戴纶巾，正在铺开一张地图（剪影＋暖色轮廓光）。"""
    if a <= 0.003: return
    col = '#22150D'
    # 案几上的地图
    mw = 165 * s * (0.25 + 0.75 * ease(mapu)); mh = 50 * s
    mx = x - 185 * s; my = y + 74 * s - mh - 4 * s
    # 矮几
    rrect(c, x - 190 * s, y + 74 * s, 200 * s, 16 * s, 3, '#3A2414', a)
    rrect(c, x - 180 * s, y + 88 * s, 12 * s, 28 * s, 2, '#3A2414', a); rrect(c, x - 10 * s, y + 88 * s, 12 * s, 28 * s, 2, '#3A2414', a)
    if mapu > 0.01:
        glow(c, mx + mw / 2, my + mh / 2, 120 * s * (0.6 + 0.4 * mglow), '#FFC870', 0.55 * mglow * a)
        mp = skia.Path(); mp.moveTo(mx, my); mp.lineTo(mx + mw, my - 6 * s); mp.lineTo(mx + mw + 14 * s, my + mh); mp.lineTo(mx - 10 * s, my + mh + 6 * s); mp.close()
        c.drawPath(mp, skia.Paint(AntiAlias=True, Color=rgba(mix('#B9A27A', '#F1DDB0', mglow), a)))
        c.drawPath(mp, skia.Paint(AntiAlias=True, Color=rgba('#5A3E24', a), Style=skia.Paint.kStroke_Style, StrokeWidth=2))
        # 地图上的两块红（荆、益）
        if lit[0] > 0.01: circle(c, mx + mw * 0.58, my + mh * 0.55, 13 * s * lit[0], LIU, a * lit[0]); glow(c, mx + mw * 0.58, my + mh * 0.55, 30 * s, '#FF5A3C', 0.8 * lit[0] * a)
        if lit[1] > 0.01: circle(c, mx + mw * 0.30, my + mh * 0.50, 15 * s * lit[1], LIU, a * lit[1]); glow(c, mx + mw * 0.30, my + mh * 0.50, 32 * s, '#FF5A3C', 0.8 * lit[1] * a)
        for k in range(5):
            line(c, [(mx + 10 * s, my + (12 + k * 10) * s), (mx + mw - 6 * s, my + (10 + k * 10) * s)], '#7A6440', 1, 0.35 * a)
        # 卷轴两端
        rrect(c, mx + mw + 4 * s, my - 10 * s, 12 * s, mh + 22 * s, 5 * s, '#5A3A20', a)
    # 身体
    p = skia.Path()
    p.moveTo(x - 40 * s, y + 40 * s); p.cubicTo(x - 50 * s, y - 20 * s, x - 30 * s, y - 70 * s, x - 5 * s, y - 78 * s)
    p.lineTo(x + 18 * s, y - 72 * s); p.cubicTo(x + 40 * s, y - 40 * s, x + 50 * s, y + 0 * s, x + 70 * s, y + 40 * s); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
    # 手臂伸向地图
    line(c, [(x - 5 * s, y - 50 * s), (x - 40 * s, y + 0 * s), (mx + mw * 0.85, my + 14 * s)], col, 14 * s, a)
    # 头 + 纶巾
    circle(c, x + 4 * s, y - 98 * s, 22 * s, col, a)
    hp = skia.Path(); hp.moveTo(x - 18 * s, y - 104 * s); hp.lineTo(x - 8 * s, y - 136 * s); hp.lineTo(x + 18 * s, y - 132 * s); hp.lineTo(x + 26 * s, y - 104 * s); hp.close()
    c.drawPath(hp, skia.Paint(AntiAlias=True, Color=rgba('#3A2B20', a)))
    line(c, [(x + 22 * s, y - 112 * s), (x + 40 * s, y - 86 * s)], '#3A2B20', 4 * s, a)
    # 轮廓光
    line(c, [(x - 5 * s, y - 78 * s), (x - 30 * s, y - 70 * s), (x - 50 * s, y - 20 * s)], '#FFB35C', 2.5 * s, 0.6 * a * (0.4 + mglow))


def _general(c, x, y, a, s=1.0, rim=0.0):
    """门外将军：背身略侧，披风、肩甲、发髻，腰悬剑。y 为脚底。"""
    if a <= 0.003: return
    col = '#0E1116'
    # 影子
    rrect(c, x - 140 * s, y - 14 * s, 300 * s, 34 * s, 20 * s, '#2A3440', 0.45 * a, blur=10)
    # 披风
    p = skia.Path()
    p.moveTo(x - 60 * s, y - 380 * s); p.cubicTo(x - 110 * s, y - 250 * s, x - 130 * s, y - 80 * s, x - 150 * s, y)
    p.lineTo(x + 120 * s, y); p.cubicTo(x + 100 * s, y - 120 * s, x + 90 * s, y - 260 * s, x + 62 * s, y - 380 * s); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
    # 衣褶
    for k in range(5):
        xx = x - 90 * s + k * 42 * s
        line(c, [(xx + 20 * s, y - 330 * s), (xx - 6 * s, y - 20 * s)], '#1E242C', 3 * s, 0.7 * a)
    # 肩甲
    for sx in (-1, 1):
        ep = skia.Path(); ep.moveTo(x + sx * 20 * s, y - 392 * s); ep.cubicTo(x + sx * 80 * s, y - 400 * s, x + sx * 96 * s, y - 360 * s, x + sx * 92 * s, y - 330 * s)
        ep.lineTo(x + sx * 40 * s, y - 340 * s); ep.close()
        c.drawPath(ep, skia.Paint(AntiAlias=True, Color=rgba('#1A1F26', a)))
        for k in range(3):
            line(c, [(x + sx * (48 + k * 12) * s, y - (385 - k * 6) * s), (x + sx * (60 + k * 10) * s, y - (345 - k * 4) * s)], '#39424D', 2 * s, a)
    # 头、发髻、冠
    rrect(c, x - 12 * s, y - 412 * s, 30 * s, 30 * s, 6 * s, col, a)
    circle(c, x + 3 * s, y - 436 * s, 27 * s, col, a)
    rrect(c, x - 8 * s, y - 480 * s, 22 * s, 22 * s, 6 * s, col, a)
    line(c, [(x - 18 * s, y - 470 * s), (x + 26 * s, y - 470 * s)], '#3A4048', 3.5 * s, a)
    # 剑
    line(c, [(x + 70 * s, y - 220 * s), (x + 108 * s, y - 70 * s)], '#2B3036', 7 * s, a)
    line(c, [(x + 60 * s, y - 230 * s), (x + 80 * s, y - 214 * s)], '#6B5A3A', 5 * s, a)
    # 轮廓光（门内暖光，从左侧）
    if rim > 0.01:
        line(c, [(x - 60 * s, y - 380 * s), (x - 110 * s, y - 250 * s), (x - 130 * s, y - 80 * s), (x - 150 * s, y)], '#FFB35C', 3.5 * s, 0.7 * rim * a, blur=1.5)
        p = skia.Paint(AntiAlias=True, Color=rgba('#FFB35C', 0.6 * rim * a), Style=skia.Paint.kStroke_Style, StrokeWidth=3 * s)
        c.drawArc(skia.Rect.MakeLTRB(x - 24 * s, y - 463 * s, x + 30 * s, y - 409 * s), 150, 110, False, p)


_flakes = None


def snow(c, t, a=1.0, n=260, wind=0.0, speed=1.0):
    global _flakes
    if _flakes is None:
        r = np.random.default_rng(9)
        N = 400; _flakes = np.stack([r.uniform(0, W, N), r.uniform(0, H, N), r.uniform(1.2, 5.0, N), r.uniform(0, 6.28, N), r.uniform(0.5, 1.3, N)], 1)
    if a <= 0.003: return
    pb = skia.Paint(AntiAlias=True); pb.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 1.4))
    pn = skia.Paint(AntiAlias=True)
    for i, (x0, y0, sz, ph, sp) in enumerate(_flakes[:n]):
        y = (y0 + t * (40 + sz * 22) * sp * speed) % (H + 40) - 20
        x = (x0 + t * wind * (30 + sz * 10) + 18 * math.sin(t * 0.8 * sp + ph)) % (W + 40) - 20
        p = pb if sz > 3.6 else pn
        p.setColor(rgba('#FFFFFF', a * (0.35 + 0.13 * sz)))
        c.drawCircle(x, y, sz * 0.8, p)


def door_leaf(c, dx, dy, dw, dh, op, a):
    """门扇：绕左边铰链转开（透视压缩宽度）。op 0 关，1 开。"""
    ww = dw * math.cos(op * math.pi * 0.46)
    # 门扇朝内开，向左侧收
    p = skia.Path(); p.moveTo(dx, dy); p.lineTo(dx + ww, dy + 10 * op); p.lineTo(dx + ww, dy + dh - 8 * op); p.lineTo(dx, dy + dh); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba('#3B2A1C', a)))
    for k in range(1, 5):
        xx = dx + ww * k / 5
        line(c, [(xx, dy + 6 * op * k / 5), (xx, dy + dh - 5 * op * k / 5)], '#24180F', 2.5, a)
    line(c, [(dx, dy + dh * 0.3), (dx + ww, dy + dh * 0.3 + 3 * op)], '#24180F', 4, a)
    line(c, [(dx, dy + dh * 0.72), (dx + ww, dy + dh * 0.72 - 3 * op)], '#24180F', 4, a)
    # 门框
    rrect(c, dx - 12, dy - 14, dw + 24, 16, 3, '#2C2118', a)
    rrect(c, dx - 12, dy - 14, 14, dh + 14, 3, '#2C2118', a)
    rrect(c, dx + dw - 2, dy - 14, 14, dh + 14, 3, '#2C2118', a)


def draw(c, t, door=1.0, light=1.0, mapu=1.0, mglow=1.0, lit=(0, 0), a=1.0, zoom=1.0, zx=420, zy=1060, sway=0.0, snow_a=1.0, gen_a=1.0):
    if 'bg' not in _static: _build_static()
    c.save()
    if zoom != 1.0:
        c.translate(zx, zy); c.scale(zoom, zoom); c.translate(-zx, -zy)
    pa = skia.Paint(); pa.setAlphaf(a)
    c.drawImage(_static['bg'], 0, 0, skia.SamplingOptions(), pa)
    # 中景竹（左右两丛，随风摆）
    r = np.random.default_rng(4)
    for i in range(16):
        side = -1 if i < 8 else 1
        x = (r.uniform(-30, 140) if side < 0 else r.uniform(850, 1110))
        sw = math.sin(t * 0.9 + i * 0.7) * 0.25 + sway
        _bamboo(c, x, 1300, r.uniform(-60, 120), r.uniform(12, 20), mix('#24392D', '#3C5544', r.uniform(0, 1)), a, sway=sw, seed=100 + i, lean=side * -0.15)
    dx, dy, dw, dh = _hut(c, a, door, light * ease(door), t)
    # 光溢出到雪地
    if door > 0.01:
        k = ease(door) * light
        lp = skia.Path(); lp.moveTo(dx, dy + dh); lp.lineTo(dx + dw, dy + dh); lp.lineTo(dx + dw + 330, 1520); lp.lineTo(dx - 120, 1520); lp.close()
        p = skia.Paint(AntiAlias=True); p.setShader(skia.GradientShader.MakeLinear([(0, dy + dh), (0, 1520)], [rgba('#FFC27A', 0.55 * k * a), rgba('#FFC27A', 0.0)]))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14)); c.drawPath(lp, p)
        glow(c, dx + dw / 2, dy + dh * 0.6, 260, '#FFB565', 0.35 * k * a)
    c.save(); c.clipRect(skia.Rect.MakeXYWH(dx, dy, dw, dh))
    # 室内：书架、竹简
    for k in range(4):
        rrect(c, dx + dw - 70, dy + 40 + k * 34, 60, 6, 2, '#3A2414', a * 0.8)
        for j in range(5): rrect(c, dx + dw - 66 + j * 11, dy + 18 + k * 34, 8, 22, 2, '#5A3E24', a * 0.7)
    _youth(c, dx + dw * 0.70, dy + dh - 92, a * ease(door), 0.9, mapu, mglow * light, lit, t)
    c.restore()
    if mapu > 0.01:
        glow(c, dx + dw * 0.70 - 110, dy + dh - 50, 170, '#FFC870', 0.30 * mglow * light * a)
    door_leaf(c, dx, dy, dw, dh, door, a)
    _general(c, 760, 1500, a * gen_a, 1.05, rim=ease(door) * light)
    c.restore()
    snow(c, t, a * snow_a, wind=0.6)
