"""插画元素：夜河、木筏、栅栏、高橹、人物剪影、森林、土藏、书签卡、天守。"""
import math
import numpy as np
import skia
from gfx import *


# ---------- 夜河全景（开场与《武功夜话》段） ----------
def sky(cv, dawn=0.0, fire=0.0):
    top = mix((6, 9, 18), (38, 52, 84), dawn)
    mid = mix((14, 20, 34), (150, 120, 110), dawn)
    bot = mix((20, 26, 38), (214, 160, 120), dawn)
    vgrad(cv, top, mid, 0, 520); vgrad(cv, mid, bot, 520, 760)
    if fire > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 400, W, 360), paint((180, 70, 30), 0.25 * fire, blur=80))


def hills(cv, dawn=0.0, y=760):
    r = np.random.default_rng(11)
    for layer, (h, col) in enumerate([(170, (24, 30, 44)), (110, (16, 20, 30))]):
        c = mix(col, mix(col, (90, 80, 90), 0.6), dawn * (0.6 - 0.25 * layer))
        pts = [(0, y)]
        xs = np.linspace(0, W, 28)
        ph = r.uniform(0, 6, 3)
        for x in xs:
            hh = h * (0.55 + 0.25 * math.sin(x / 140 + ph[0]) + 0.15 * math.sin(x / 57 + ph[1]) + 0.05 * math.sin(x / 23 + ph[2]))
            pts.append((x, y - hh + layer * 40))
        pts.append((W, y))
        cv.drawPath(poly_path(pts, True), paint(c))


def river(cv, t, dawn=0.0, y0=760, y1=H, flow=1.0):
    """透视河面：远窄近宽，带水纹和天光倒影。"""
    col_far = mix((18, 30, 44), (150, 130, 130), dawn * 0.8)
    col_near = mix((8, 14, 22), (60, 66, 80), dawn * 0.6)
    vgrad(cv, col_far, col_near, y0, y1)
    p = paint((170, 200, 230), 0.12 + 0.1 * dawn, stroke=2)
    r = np.random.default_rng(5)
    for i in range(140):
        u = r.uniform(0, 1)
        z = ((u + t * 0.06 * flow * r.uniform(0.6, 1.4)) % 1.0)
        y = y0 + (y1 - y0) * z ** 1.8
        x = r.uniform(-0.2, 1.2) * W
        L = 20 + 120 * z ** 1.5
        p.setStrokeWidth(1 + 3 * z)
        p.setAlphaf((0.06 + 0.16 * z) * (0.6 + 0.4 * dawn + 0.2))
        cv.drawLine(x - L, y, x + L, y, p)


def raft(cv, x, y, s, a=1.0, logs=7, lit=0.0):
    """木筏（俯视透视的一排原木）。"""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for i in range(logs):
        yy = (i - logs / 2) * 16
        rrect(cv, -150, yy, 300, 14, 7, paint(mix((58, 40, 26), (150, 100, 60), lit), a))
        cv.drawLine(-150, yy + 3, 150, yy + 3, paint((120, 90, 60), 0.4 * a, stroke=2))
    for xx in (-110, 0, 110):
        cv.drawLine(xx, -logs * 8 - 4, xx, logs * 8 + 2, paint((30, 22, 14), a, stroke=6))
    # 筏上捆好的预制构件
    for k in range(3):
        rrect(cv, -100 + k * 70, -logs * 8 - 30, 54, 26, 3, paint((84, 60, 38), a))
    cv.restore()


def stake_row(cv, pts, prog, a=1.0, h=90, col=(46, 34, 24), hi=(120, 84, 52), lit=0.0):
    """沿折线立栅栏，prog 控制立起的数量（每根有生长动画）。"""
    n = len(pts)
    shown = prog * n
    for i, (x, y, s) in enumerate(pts):
        k = clamp(shown - i)
        if k <= 0:
            continue
        hh = h * s * eout(k)
        w = 13 * s
        path = poly_path([(x - w / 2, y), (x - w / 2, y - hh), (x, y - hh - 14 * s), (x + w / 2, y - hh), (x + w / 2, y)], True)
        cv.drawPath(path, paint(mix(col, hi, lit), a))
        cv.drawLine(x - w / 2 + 2, y - hh + 4, x - w / 2 + 2, y, paint(hi, 0.35 * a, stroke=2))
    # 横档
    if prog > 0.15:
        vis = [p for i, p in enumerate(pts) if i < shown - 0.5]
        if len(vis) > 1:
            for frac in (0.35, 0.75):
                cv.drawPath(poly_path([(x, y - h * s * frac) for x, y, s in vis]), paint(mix(col, hi, lit * 0.6), a, stroke=6 * vis[0][2]))


def yagura(cv, x, y, s, prog, a=1.0, lit=0.0):
    """高橹：四柱、斜撑、平台、小屋顶。prog 0..1 自下而上搭起。"""
    if prog <= 0:
        return
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    col = mix((40, 30, 22), (150, 104, 64), lit)
    hgt = 300
    hp = hgt * clamp(prog / 0.7)
    for xx in (-70, 70):
        cv.drawLine(xx, 0, xx * 0.82, -hp, paint(col, a, stroke=14))
    for xx in (-30, 30):
        cv.drawLine(xx, 0, xx * 0.9, -hp, paint(col, a * 0.8, stroke=9))
    for k in range(3):
        yy = -hgt * (0.25 + 0.27 * k)
        if -yy < hp:
            cv.drawLine(-66, yy + 40, 62, yy - 30, paint(col, a, stroke=7))
            cv.drawLine(-62, yy, 62, yy, paint(col, a, stroke=7))
    pr = clamp((prog - 0.7) / 0.3)
    if pr > 0:
        cv.save(); cv.translate(0, -hgt); cv.scale(1, eout(pr))
        rrect(cv, -90, -20, 180, 24, 3, paint(col, a))
        for xx in range(-80, 90, 32):
            cv.drawLine(xx, -20, xx, -70, paint(col, a, stroke=6))
        cv.drawPath(poly_path([(-120, -70), (0, -120), (120, -70)], True), paint(mix((26, 22, 20), (90, 70, 50), lit), a))
        cv.restore()
    cv.restore()


def figure(cv, x, y, s, a=1.0, col=(10, 10, 14), pose=0, t=0.0, weapon="spear", seed=0):
    """人物剪影。pose 0 站立 1 挥锤 2 持枪前刺 3 扛木。"""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    p = paint(col, a)
    sw = math.sin(t * 6 + seed)
    # 腿
    cv.drawLine(-8, -50, -16 - 6 * sw * (pose == 2), 0, paint(col, a, stroke=11))
    cv.drawLine(8, -50, 14 + 6 * sw * (pose == 2), 0, paint(col, a, stroke=11))
    # 躯干
    cv.drawPath(poly_path([(-17, -52), (17, -52), (13, -105), (-13, -105)], True), p)
    # 头与笠
    cv.drawCircle(0, -118, 11, p)
    cv.drawPath(poly_path([(-26, -118), (0, -136), (26, -118)], True), p)
    if pose == 1:   # 挥木槌
        ang = -0.4 + 1.3 * (0.5 + 0.5 * math.sin(t * 7 + seed))
        hx, hy = 14 + 46 * math.cos(-ang - 1.2), -98 + 46 * math.sin(-ang - 1.2)
        cv.drawLine(10, -98, hx, hy, paint(col, a, stroke=8))
        cv.save(); cv.translate(hx, hy); cv.rotate(math.degrees(-ang))
        rrect(cv, -14, -10, 28, 20, 4, p); cv.restore()
    elif pose == 2:  # 持枪
        cv.drawLine(-10, -92, 36 + 10 * sw, -100, paint(col, a, stroke=8))
        cv.drawLine(-60, -84, 120 + 12 * sw, -108, paint(col, a, stroke=4))
        cv.drawPath(poly_path([(120 + 12 * sw, -114), (142 + 12 * sw, -110), (120 + 12 * sw, -102)], True), p)
    elif pose == 3:  # 扛木
        cv.drawLine(-12, -96, 18, -112, paint(col, a, stroke=8))
        cv.drawLine(-90, -118, 110, -136, paint(col, a, stroke=13))
    else:
        if weapon == "spear":
            cv.drawLine(24, 0, 30, -190, paint(col, a, stroke=4))
            cv.drawPath(poly_path([(26, -190), (30, -214), (34, -190)], True), p)
        cv.drawLine(14, -96, 26, -60, paint(col, a, stroke=8))
    cv.restore()


def fire_arrow(cv, x0, y0, x1, y1, k, a=1.0, h=160):
    """火箭：抛物线飞行，k 0..1。"""
    if k <= 0 or k >= 1:
        return
    def P(u):
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - h * 4 * u * (1 - u)
    x, y = P(k)
    for j in range(8):
        u = k - j * 0.012
        if u < 0:
            break
        xx, yy = P(u)
        cv.drawCircle(xx, yy, 6 - j * 0.6, paint((255, 150 - j * 10, 60), a * (1 - j / 8) * 0.8, blur=3))
    cv.drawCircle(x, y, 16, paint((255, 160, 70), 0.4 * a, blur=10))
    cv.drawCircle(x, y, 4, paint((255, 240, 200), a))


def forest(cv, t, y, a=1.0, seed=2, n=40, sc=1.0, col=(12, 18, 16)):
    r = np.random.default_rng(seed)
    for i in range(n):
        x = r.uniform(-50, W + 50); h = r.uniform(180, 380) * sc; w = h * r.uniform(0.28, 0.36)
        yy = y + r.uniform(-30, 60) * sc
        c = mix(col, (40, 50, 44), r.uniform(0, 0.5))
        for k in range(3):
            hh = h * (1 - k * 0.28)
            cv.drawPath(poly_path([(x - w * (1 - k * 0.2) / 2, yy - h * k * 0.25), (x, yy - hh - h * 0.05 * k), (x + w * (1 - k * 0.2) / 2, yy - h * k * 0.25)], True), paint(c, a))
        cv.drawLine(x, yy, x, yy + 24 * sc, paint(c, a, stroke=6 * sc))


def kura(cv, x, y, s, a=1.0, wet=0.0):
    """土藏（白墙、海鼠壁、瓦顶）。"""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    wall = mix((196, 190, 176), (120, 126, 130), wet)
    cv.drawRect(skia.Rect.MakeXYWH(-200, -300, 400, 300), paint(wall, a))
    for i in range(5):
        for j in range(8):
            cx = -190 + j * 50 + (25 if i % 2 else 0)
            cy = -100 + i * 20
            if -200 < cx < 190:
                cv.save(); cv.translate(cx, cy); cv.rotate(45)
                cv.drawRect(skia.Rect.MakeXYWH(-8, -8, 16, 16), paint((60, 62, 66), a * 0.75)); cv.restore()
    cv.drawPath(poly_path([(-250, -300), (-180, -400), (180, -400), (250, -300)], True), paint((40, 42, 48), a))
    cv.drawRect(skia.Rect.MakeXYWH(-60, -190, 120, 190), paint((40, 34, 30), a))
    cv.drawRect(skia.Rect.MakeXYWH(-60, -190, 120, 190), paint((20, 16, 14), a, stroke=6))
    cv.restore()


def slip(cv, x, y, w, h, title, sub="", a=1.0, accent=GOLD, year=None, tag=None):
    """暗色题签卡（代替书影）：深色底、竖排金字题签。"""
    if a <= 0:
        return
    rrect(cv, x + 8, y + 14, w, h, 10, paint((0, 0, 0), 0.6 * a, blur=16))
    rrect(cv, x, y, w, h, 10, paint((26, 24, 30), 0.95 * a))
    rrect(cv, x + 10, y + 10, w - 20, h - 20, 6, paint(accent, 0.5 * a, stroke=1.6))
    # 题签条
    sw = 92
    sx = x + w - sw - 30
    rrect(cv, sx, y + 30, sw, h - 60, 4, paint((236, 226, 200), 0.95 * a))
    chars = list(title)
    fs = min(62, (h - 110) / max(1, len(chars)))
    for i, ch in enumerate(chars):
        text(cv, ch, sx + sw / 2, y + 60 + fs * 0.9 + i * fs * 1.04, "serif_k", fs, INK, a, "c")
    tx = x + 34
    if year:
        text(cv, year, tx, y + 110, "serif_k", 84, accent, a)
    if sub:
        para(cv, sub, tx, y + (190 if year else 80), w - sw - 90, "sans", 34, (220, 214, 200), a, 1.45)
    if tag:
        text(cv, tag, tx, y + h - 40, "sans_b", 30, (240, 150, 120), a)


def doc_card(cv, x, y, w, lines_jp, a=1.0, title=None, hl=None, f="jp", size=44, lh=1.6):
    """和纸原文卡：竖向排列不便，用横排原文，hl=要高亮的子串列表。"""
    if a <= 0:
        return 0
    allines = []
    for l in lines_jp:
        allines += wrap(l, f, size, w - 80)
    h = 60 + (70 if title else 0) + len(allines) * size * lh + 30
    rrect(cv, x + 6, y + 12, w, h, 6, paint((0, 0, 0), 0.6 * a, blur=18))
    rrect(cv, x, y, w, h, 6, paint(PAPER, a))
    r = np.random.default_rng(4)
    for i in range(60):
        xx = x + r.uniform(0, w); yy = y + r.uniform(0, h)
        cv.drawLine(xx, yy, xx + r.uniform(-30, 30), yy + r.uniform(-4, 4), paint((180, 168, 140), 0.25 * a, stroke=1))
    yy = y + 64
    if title:
        text(cv, title, x + 40, yy, "sans_b", 32, (120, 40, 30), a)
        yy += 70
    for l in allines:
        if hl:
            for hs, col in hl:
                k = l.find(hs)
                if k >= 0:
                    x0 = x + 40 + tw(l[:k], f, size)
                    cv.drawRect(skia.Rect.MakeXYWH(x0 - 4, yy - size * 0.95, tw(hs, f, size) + 8, size * 1.25), paint(col[0], col[1] * a))
        text(cv, l, x + 40, yy, f, size, INK, a)
        yy += size * lh
    return h


def tenshu(cv, x, y, s, a=1.0, col=(232, 230, 222), roof=(54, 60, 68)):
    """现代仿天守建筑远景（白墙三重）。"""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawRect(skia.Rect.MakeXYWH(-230, -70, 460, 70), paint((90, 92, 96), a))
    for i, (w, h) in enumerate([(380, 120), (290, 100), (200, 90), (130, 70)]):
        yb = -70 - sum(hh + 30 for _, hh in [(380, 120), (290, 100), (200, 90), (130, 70)][:i])
        cv.drawRect(skia.Rect.MakeXYWH(-w / 2, yb - h, w, h), paint(col, a))
        for k in range(-w // 2 + 30, w // 2 - 20, 50):
            cv.drawRect(skia.Rect.MakeXYWH(k, yb - h * 0.62, 22, h * 0.3), paint((70, 70, 76), a))
        cv.drawPath(poly_path([(-w / 2 - 44, yb - h), (-w / 2 + 10, yb - h - 30), (w / 2 - 10, yb - h - 30), (w / 2 + 44, yb - h)], True), paint(roof, a))
    cv.restore()
