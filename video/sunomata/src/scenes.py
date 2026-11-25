"""各镜头。每个镜头函数 fn(cv, t, dur, X)：t 为镜头内时间，X.s(id)/X.e(id) 给出该句在镜头内的起止秒。"""
import math
import numpy as np
import skia
from gfx import *
from illustr import *

# ---------- 地名与河道（经纬度；河道为示意） ----------
PL = dict(kiyosu=(136.842, 35.215), inaba=(136.782, 35.434), suno=(136.688, 35.366), ogaki=(136.612, 35.360),
          inuyama=(136.944, 35.388), owari=(137.12, 35.02), mino=(136.80, 35.63), bay=(136.76, 34.93))
KISO = [(137.06, 35.43), (136.97, 35.40), (136.94, 35.385), (136.88, 35.383), (136.82, 35.376), (136.775, 35.365),
        (136.748, 35.33), (136.736, 35.27), (136.726, 35.20), (136.718, 35.12), (136.71, 35.04)]
OLDKISO = [(136.775, 35.365), (136.745, 35.372), (136.715, 35.369), (136.688, 35.366)]
NAGARA = [(136.87, 35.56), (136.81, 35.47), (136.785, 35.44), (136.752, 35.418), (136.72, 35.398), (136.698, 35.378),
          (136.688, 35.366), (136.676, 35.33), (136.68, 35.25), (136.69, 35.15), (136.696, 35.04)]
IBI = [(136.56, 35.60), (136.60, 35.48), (136.624, 35.40), (136.636, 35.33), (136.66, 35.25), (136.676, 35.15), (136.686, 35.04)]
RIVERS = [(KISO, "木曾川", (136.90, 35.395), 1.0), (NAGARA, "长良川", (136.745, 35.445), 0.9),
          (IBI, "揖斐川", (136.585, 35.47), 0.8), (OLDKISO, "", None, 0.8)]


def hdr(cv, t, title, sub=None, a=1.0, col=GOLD):
    k = ramp(t, 0.05, 0.5) * a
    if k <= 0:
        return
    text(cv, title, W / 2, 262, "serif_k", 64, col, k, "c", ls=4, shadow=10)
    w = tw(title, "serif_k", 64, 4)
    cv.drawLine(W / 2 - w / 2 * ramp(t, 0.2, 0.6), 292, W / 2 + w / 2 * ramp(t, 0.2, 0.6), 292, paint(col, 0.6 * k, stroke=2))
    if sub:
        text(cv, sub, W / 2, 350, "sans", 36, (215, 210, 200), k * ramp(t, 0.3, 0.5), "c", shadow=6)


def partial(pts, prog):
    if prog >= 1:
        return pts
    d = [0]
    for i in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    L = d[-1] * prog
    out = [pts[0]]
    for i in range(1, len(pts)):
        if d[i] <= L:
            out.append(pts[i])
        else:
            f = (L - d[i - 1]) / max(1e-6, d[i] - d[i - 1])
            out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f))
            break
    return out


def draw_rivers(cv, mv, prog=1.0, a=1.0, width=1.0, label=True):
    for pts, name, lp, wv in RIVERS:
        sp = [mv.P(*q) for q in pts]
        sp = partial(sp, prog)
        if len(sp) < 2:
            continue
        path = smooth_path(sp)
        cv.drawPath(path, paint((60, 120, 170), 0.45 * a, stroke=16 * width * wv, blur=6))
        cv.drawPath(path, paint((96, 160, 205), 0.95 * a, stroke=6 * width * wv))
        if label and name and prog > 0.7:
            x, y = mv.P(*lp)
            text(cv, name, x, y, "serif_b", 34, (160, 205, 235), a * ease((prog - 0.7) / 0.3), "c", shadow=6)


def place(cv, mv, key, name, a=1.0, col=WHITE, side="r", size=40, dot=True, ring=None):
    if a <= 0:
        return
    x, y = mv.P(*PL[key])
    if dot:
        cv.drawCircle(x, y, 11, paint((0, 0, 0), 0.6 * a, blur=4))
        cv.drawCircle(x, y, 8, paint(col, a))
    if ring:
        cv.drawCircle(x, y, ring, paint(col, 0.8 * a, stroke=3))
    dx = 22 if side == "r" else -22
    text(cv, name, x + dx, y + 13, "serif_b", size, col, a, "l" if side == "r" else "r", shadow=8)


def check_row(cv, x, y, label, ok, a, size=46):
    if a <= 0:
        return
    col = (120, 200, 130) if ok else ODA_HI
    s = 30
    cv.save(); cv.translate(x + s, y - size * 0.35)
    cv.scale(0.6 + 0.4 * eout(a), 0.6 + 0.4 * eout(a))
    if ok:
        cv.drawPath(poly_path([(-s * 0.7, 0), (-s * 0.15, s * 0.55), (s * 0.8, -s * 0.6)]), paint(col, a, stroke=9))
    else:
        cv.drawLine(-s * 0.6, -s * 0.6, s * 0.6, s * 0.6, paint(col, a, stroke=9))
        cv.drawLine(-s * 0.6, s * 0.6, s * 0.6, -s * 0.6, paint(col, a, stroke=9))
    cv.restore()
    text(cv, label, x + 90, y, "serif_b", size, WHITE, a, shadow=6)


def stamp(cv, s, x, y, k, size=96, col=ODA, rot=-8):
    if k <= 0:
        return
    sc = 1.6 - 0.6 * eout(k)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc, sc)
    w = tw(s, "serif_k", size) + 50
    a = clamp(k * 2)
    rrect(cv, -w / 2, -size * 0.85, w, size * 1.2, 8, paint(col, 0.9 * a, stroke=7))
    text(cv, s, 0, size * 0.18, "serif_k", size, col, a, "c")
    cv.restore()


def quote_card(cv, t, X, lid, orig, src, gloss=None, y=640, size=74, jp=False, maxw=900, out=None):
    """古文/名言引文卡：原文大字 + 出处 + 白话。out=淡出时刻（镜头内秒）。"""
    k = ramp(t, X.s(lid) - 0.4, 0.6) * (1 - (ramp(t, out, 0.4) if out else 0))
    if k <= 0:
        return
    cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.45 * k))
    f = "jp" if jp else "serif_k"
    ls = [l for part in orig.split("\n") for l in wrap(part, f, size, maxw)]
    hh = len(ls) * size * 1.45
    cv.drawLine(W / 2 - 60, y - 70, W / 2 + 60, y - 70, paint(GOLD, k, stroke=3))
    for i, l in enumerate(ls):
        kk = ramp(t, X.s(lid) - 0.3 + i * 0.35, 0.6)
        text(cv, l, W / 2, y + size + i * size * 1.45, f, size, (246, 238, 218), kk, "c", shadow=14, glow=(GOLD, 22, 0.25))
    yy = y + hh + 70
    text(cv, "——" + src, W / 2, yy + 10, "sans", 34, GOLD, ramp(t, X.s(lid) + 0.4, 0.6), "c")
    if gloss:
        para(cv, gloss, W / 2, yy + 100, maxw, "serif", 40, (215, 210, 200), ramp(t, X.s(lid) + 0.9, 0.6), 1.5, "c")


# ============ A 钩子 ============
def isle_pts(n=22, x0=110, x1=980, y=1130, s=1.0):
    return [(x0 + (x1 - x0) * i / (n - 1), y + 26 * math.sin(i * 0.6), s * (0.85 + 0.15 * math.sin(i * 1.7))) for i in range(n)]


def river_scene(cv, t, build, dawn, cam=0.0, fight=0.0, rafts=1.0, legend=None, fire=0.0, hammer=True, fg=False):
    """夜河建城全景。build 0..1，dawn 0..1，cam 镜头上移量（0..1）。"""
    cv.drawRect(skia.Rect.MakeWH(W, 400), paint(mix((6, 9, 18), (38, 52, 84), dawn)))
    cv.save()
    cv.translate(0, 260 * cam)
    sky(cv, dawn, fire)
    hills(cv, dawn)
    river(cv, t, dawn, flow=1.2)
    # 对岸火把（斋藤方）
    for i in range(9):
        x = 80 + i * 118 + 20 * math.sin(i * 2.3)
        torch(cv, x, 742 + 6 * math.sin(i), t, 0.45, 0.9 * (1 - 0.7 * dawn), seed=i)
    # 木筏顺流而下（自远而近）
    if rafts > 0:
        for i in range(4):
            z = ((t * 0.07 + i * 0.25) % 1.0)
            y = 790 + 520 * z ** 1.7
            s = 0.25 + 0.9 * z ** 1.5
            x = W / 2 + (i - 1.5) * 160 * (0.4 + z) + 60 * math.sin(i * 1.3)
            raft(cv, x, y, s, rafts * clamp(z * 6) * clamp((1 - z) * 5), lit=0.15 * dawn)
    # 河洲
    cv.drawPath(smooth_path([(-40, 1250), (120, 1120), (420, 1090), (760, 1100), (1120, 1150), (1120, 1400), (-40, 1400)]), paint(mix((20, 22, 20), (70, 64, 52), dawn)))
    cv.drawRect(skia.Rect.MakeXYWH(-40, 1250, W + 80, 700), paint(mix((20, 22, 20), (70, 64, 52), dawn)))
    lit = 0.25 * (1 - dawn) + 0.45 * dawn
    yagura(cv, 300, 1110, 0.95, clamp(build * 1.25 - 0.1), lit=lit)
    yagura(cv, 820, 1120, 0.75, clamp(build * 1.3 - 0.3), lit=lit)
    stake_row(cv, isle_pts(), build, h=120, lit=lit)
    # 工人与兵
    if hammer:
        for i in range(6):
            x = 150 + i * 160
            figure(cv, x, 1215 + (i % 2) * 30, 0.95, pose=1 if i % 3 else 3, t=t, seed=i * 1.7, col=(8, 8, 10))
    if fight > 0:
        for i in range(4):
            figure(cv, 120 + i * 260, 1330, 1.15, a=fight, pose=2, t=t, seed=i)
        for i in range(7):
            ph = (t * 0.6 + i / 7) % 1
            x0 = 100 + i * 140
            fire_arrow(cv, x0, 760, x0 + 120 + i * 13, 1180, ph, fight)
    for i, x in enumerate((210, 560, 900)):
        torch(cv, x, 1150, t, 0.8, 1 - dawn, seed=10 + i)
        embers(cv, t, x, 1150, 1 - dawn, seed=i)
    if fg:
        # 地面火光与近景：大号人物打桩
        sh_ = skia.GradientShader.MakeRadial((W / 2, 1300), 700, [C((255, 130, 50), 0.32 * (1 - dawn)), C((255, 110, 40), 0.0)])
        pp = skia.Paint(); pp.setShader(sh_); cv.drawRect(skia.Rect.MakeXYWH(0, 1100, W, 900), pp)
        for k, (x, sc) in enumerate(((140, 2.9), (930, 2.6))):
            cv.drawRect(skia.Rect.MakeXYWH(x + (90 if k == 0 else -150), 1520, 46, 420), paint((26, 18, 12)))
            cv.drawPath(poly_path([(x + (90 if k == 0 else -150), 1520), (x + (113 if k == 0 else -127), 1480), (x + (136 if k == 0 else -104), 1520)], True), paint((26, 18, 12)))
            figure(cv, x, 1960, sc, pose=1, t=t * 1.3, seed=k * 2.1, col=(4, 4, 6))
        torch(cv, 560, 1500, t, 1.4, 1 - dawn, seed=21)
        embers(cv, t, 560, 1500, 1 - dawn, n=24, seed=5, spread=120)
    cv.restore()
    rain(cv, t, a=0.28 * (1 - 0.6 * dawn))


def sh_hook(cv, t, dur, X):
    e2 = X.s("A02")
    build = ease(lin(t, 0.0, e2 - 0.4)) * 0.55 + 0.45
    dawn = ease(lin(t, e2 - 1.6, e2 + 0.2))
    cam = ease(lin(t, e2 - 1.6, e2 + 0.6))
    river_scene(cv, t, build, dawn, cam, fg=True)
    # 大字「一夜」
    k = 1 - ramp(t, e2 + 0.2, 0.6) * 0.0
    sc = 1.0 + 0.04 * t / dur
    cv.save(); cv.translate(W / 2, 520); cv.scale(sc, sc)
    text(cv, "一夜", 0, 0, "serif_k", 280, (250, 244, 228), k, "c", ls=30, shadow=30, glow=(ODA, 60, 0.75))
    cv.restore()
    text(cv, "墨俣一夜城", W / 2, 640, "serif_b", 64, GOLD, 1.0, "c", ls=16, shadow=12)
    corner_tag(cv, "传说场景 · 情景演绎", 1.0)
    # 反转：史书一字未写
    k2 = ramp(t, e2 + 0.3, 0.5)
    if k2 > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * k2))
        text(cv, "最可靠的史书", W / 2, 860, "serif_k", 92, WHITE, k2, "c", shadow=16)
        stamp(cv, "一字未写", W / 2, 1050, lin(t, e2 + 1.6, e2 + 2.0), 120)


def sh_koki(cv, t, dur, X):
    vgrad(cv, (14, 14, 22), (6, 8, 12))
    hdr(cv, t, "《信长公记》", "太田牛一 · 织田信长近臣 · 同时代人")
    slip(cv, 90, 420, 360, 520, "信長公記", "", ramp(t, 0.1, 0.5), year="首卷")
    a = ramp(t, 0.8, 0.6)
    doc_card(cv, 480, 430, 520, ["永禄四年辛酉五月上旬……", "洲股御要害丈夫に仰せ付けられ、御居陣候"], a,
             title="首卷 · 十四条合战之事", hl=[("洲股御要害", ((230, 120, 90), 0.45))], size=40)
    s4 = X.s("A04")
    check_row(cv, 170, 1080, "修筑墨俣（洲股）工事", True, ramp(t, s4 + 0.2, 0.4))
    check_row(cv, 170, 1170, "秀吉", False, ramp(t, s4 + 1.8, 0.4))
    check_row(cv, 170, 1260, "一夜", False, ramp(t, s4 + 3.2, 0.4))
    corner_tag(cv, "据日文原文", ramp(t, 0.8, 0.4))


STRATA = [("1626", "小濑甫庵《太阁记》", "离事件约60年", (118, 96, 70)), ("1797", "《绘本太阁记》（读本小说）", "约230年", (96, 80, 66)),
          ("1959", "前野家文书「被发现」", "据收藏者说", (78, 70, 64)), ("1987", "《武功夜话》出版", "约420年", (62, 58, 58))]


def strata(cv, t, starts, y0=1240, hh=150, hl=None, a=1.0):
    """四层地层自下而上叠起。starts=每层出现时刻。"""
    for i, (yr, book, gap, col) in enumerate(STRATA):
        k = ramp(t, starts[i], 0.5) * a
        if k <= 0:
            continue
        y = y0 - i * (hh + 14) - 40 * (1 - eout(k))
        pts = [(60, y)] + [(60 + 960 * j / 12, y - 10 * math.sin(j * 1.3 + i)) for j in range(13)] + [(1020, y + hh), (60, y + hh)]
        cv.drawPath(poly_path(pts, True), paint(col, 0.95 * k))
        cv.drawPath(poly_path(pts, True), paint(mix(col, (255, 255, 255), 0.3), 0.6 * k, stroke=2))
        hk = 1.0 if hl is None else (1.0 if hl == i else 0.35)
        text(cv, yr, 100, y + hh * 0.62, "serif_k", 76, GOLD, k * hk, shadow=8)
        text(cv, book, 330, y + hh * 0.48, "serif_b", 40, WHITE, k * hk, shadow=6)
        text(cv, gap, 330, y + hh * 0.48 + 52, "sans", 32, (220, 200, 170), k * hk)


def sh_strata(cv, t, dur, X):
    vgrad(cv, (16, 16, 24), (8, 8, 12))
    hdr(cv, t, "一个故事，四个年份")
    s6 = X.s("A06")
    starts = [s6 - 0.2 + i * 0.75 for i in range(4)]
    s7 = X.s("A07")
    hl = None
    if "A07b" in X.ids:
        sb = X.s("A07b"); eb = X.e("A07b")
        if t > sb:
            q = (t - sb) / max(1, eb - sb)
            hl = 0 if q < 0.33 else 1 if q < 0.62 else 3
    strata(cv, t, starts, hl=hl)
    # 右侧：完整度箭头
    k = ramp(t, s7, 0.6)
    if k > 0:
        arrow(cv, [(980, 1330), (980, 540)], k, ODA, 30)
        text(cv, "越晚", 940, 1380, "serif_b", 38, ODA_HI, k, "r")
        text(cv, "越完整", 940, 590, "serif_b", 44, ODA_HI, k, "r", shadow=6)


def sh_typhoon(cv, t, dur, X):
    vgrad(cv, (14, 18, 26), (6, 8, 12))
    s9, s10 = X.s("A09"), X.s("A10")
    zoom = 1 + 0.05 * t / dur
    cv.save(); cv.translate(W / 2, 1000); cv.scale(zoom, zoom); cv.translate(-W / 2, -1000)
    forest(cv, t, 820, 0.8, seed=5, n=16, sc=0.8, col=(10, 14, 16))
    kura(cv, W / 2, 1180, 1.3, wet=0.6)
    wl = 1180 - 60 * ease(lin(t, 0.5, 4))
    cv.drawRect(skia.Rect.MakeXYWH(0, wl, W, H - wl), paint((40, 62, 80), 0.75))
    for i in range(20):
        x = (i * 97 + t * 40) % (W + 100) - 50
        cv.drawLine(x - 30, wl + 8 + (i % 4) * 12, x + 30, wl + 8 + (i % 4) * 12, paint((150, 180, 200), 0.3, stroke=2))
    cv.restore()
    rain(cv, t, n=380, a=0.4, wind=0.35, speed=3000)
    if t < s9 + 0.3:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((210, 220, 255), 0.5 * max(0, math.sin(t * 2.3) ** 30)))
    # 旧箱与模糊文书
    k = ramp(t, s9, 0.6)
    if k > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * k))
        rrect(cv, 190, 560, 700, 520, 10, paint((70, 50, 34), k))
        rrect(cv, 190, 560, 700, 520, 10, paint((30, 20, 14), k, stroke=8))
        r = np.random.default_rng(9)
        for j in range(3):
            x0, y0 = 240 + j * 30, 600 + j * 26
            rrect(cv, x0, y0, 560, 400, 4, paint(mix(PAPER, (160, 150, 130), j * 0.3), k))
            for c in range(9):
                for rr in range(int(r.integers(5, 10))):
                    cv.drawRect(skia.Rect.MakeXYWH(x0 + 520 - c * 58, y0 + 30 + rr * 38, 26, 26), paint((40, 34, 30), 0.5 * k, blur=5))
        text(cv, "谁运木料 · 怎么放排 · 夜里怎么打桩", W / 2, 1180, "serif_b", 46, WHITE, ramp(t, s9 + 2, 0.5), "c", shadow=8)
    stamp(cv, "伪书？", 760, 760, lin(t, s10 + 0.4, s10 + 0.8), 110)
    ka = ramp(t, s10 + 2.6, 0.5)
    if ka > 0:
        text(cv, "原本至今未公开", W / 2, 1290, "serif_k", 60, ODA_HI, ka, "c", shadow=10)
    corner_tag(cv, "情景演绎 · 非原物", 1.0)
    text(cv, "1959 · 伊势湾台风", W / 2, 300, "serif_k", 62, GOLD, ramp(t, 0.1, 0.5), "c", shadow=10)


def sh_question(cv, t, dur, X):
    vgrad(cv, (20, 14, 14), (6, 6, 10))
    cv.drawCircle(W / 2, 820, 520, paint(ODA, 0.10, blur=160))
    s12, s13 = X.s("A12"), X.s("A13")
    k = ramp(t, 0.1, 0.5) * (1 - ramp(t, s13 - 0.3, 0.4))
    text(cv, "墨俣一夜城", W / 2, 700, "serif_k", 120, WHITE, k, "c", ls=10, shadow=20)
    text(cv, "到底发生过没有？", W / 2, 860, "serif_k", 86, ODA_HI, k, "c", shadow=14)
    k2 = ramp(t, s12, 0.5) * (1 - ramp(t, s13 - 0.3, 0.4))
    text(cv, "证据这么弱，为什么越传越完整？", W / 2, 1040, "serif_b", 52, (225, 218, 205), k2, "c", shadow=8)
    k3 = ramp(t, s13, 0.6)
    if k3 > 0:
        text(cv, "从无名小卒到天下人", W / 2, 640, "serif_b", 56, GOLD, k3, "c", ls=8, shadow=10)
        text(cv, "第一集", W / 2, 740, "sans", 40, (210, 200, 190), k3, "c", ls=10)
        text(cv, "一座查无实据的城", W / 2, 900, "serif_k", 104, WHITE, ramp(t, s13 + 0.4, 0.6), "c", ls=6, shadow=20, glow=(ODA, 40, 0.35))
        text(cv, "传说是怎样一层层长出来的", W / 2, 1020, "serif", 44, (220, 212, 200), ramp(t, s13 + 1.0, 0.6), "c")


# ============ B 战略背景 ============
def sh_bigmap(cv, t, dur, X):
    bm = basemap("big")
    z = 1.55 + 0.25 * ease(t / dur)
    mv = MapView(bm, 136.80, 35.33, z, cy=900)
    mv.draw(cv, bright=0.9)
    vgrad(cv, (8, 10, 16), (8, 10, 16), 0, 420, 0.7)
    hdr(cv, t, "织田攻美浓", "十六世纪中叶")
    draw_rivers(cv, mv, ramp(t, 0.5, 2.0), 0.8, 0.7, label=False)
    ka = ramp(t, 0.6, 0.6)
    for key, nm in (("owari", "尾 张"), ("mino", "美 浓")):
        x, y = mv.P(*PL[key])
        text(cv, nm, x, y, "serif_k", 86, (235, 225, 205), 0.6 * ka, "c", ls=20, shadow=10)
    x, y = mv.P(*PL["bay"]); text(cv, "伊势湾", x, y, "serif", 40, (140, 170, 200), ka * 0.8, "c")
    s2 = X.s("B02")
    place(cv, mv, "kiyosu", "清洲（织田）", ramp(t, s2, 0.5), ODA_HI)
    place(cv, mv, "inaba", "稻叶山（斋藤）", ramp(t, s2 + 2.0, 0.5), (170, 200, 230), ring=34)
    k = ramp(t, s2 + 3.4, 0.5)
    if k > 0:
        x, y = mv.P(*PL["inaba"])
        text(cv, "＝后来的岐阜", x + 22, y + 66, "sans", 34, (200, 215, 230), k)
    arrow(cv, [mv.P(*PL["kiyosu"]), mv.P(136.83, 35.33), mv.P(136.795, 35.41)], lin(t, s2 + 1.0, s2 + 3.0), ODA, 40)
    corner_tag(cv, "地图示意", 1.0)


def plain_view(t, dur, lon=136.76, lat=35.33, z0=1.05, z1=1.15):
    return MapView(basemap("plain"), lon, lat, z0 + (z1 - z0) * ease(t / max(1, dur)), cy=880)


def sh_rivers(cv, t, dur, X):
    mv = plain_view(t, dur)
    mv.draw(cv, bright=0.85)
    vgrad(cv, (8, 10, 16), (8, 10, 16), 0, 400, 0.75)
    hdr(cv, t, "浓尾平原：河网", "路少，水多")
    draw_rivers(cv, mv, ease(lin(t, 0.3, 5.0)), 1.0, 1.0)
    place(cv, mv, "kiyosu", "清洲", ramp(t, 0.5, 0.4), ODA_HI)
    place(cv, mv, "inaba", "稻叶山", ramp(t, 0.5, 0.4), (170, 200, 230))
    corner_tag(cv, "战国时河道示意，与今不同", 1.0)


def sh_cross(cv, t, dur, X):
    mv = plain_view(t, dur, z0=1.15, z1=1.2)
    mv.draw(cv, bright=0.75)
    vgrad(cv, (8, 10, 16), (8, 10, 16), 0, 400, 0.75)
    hdr(cv, t, "每一条河，都是一道墙")
    draw_rivers(cv, mv, 1.0, 1.0, 1.0)
    place(cv, mv, "kiyosu", "清洲", 1.0, ODA_HI)
    place(cv, mv, "inaba", "稻叶山", 1.0, (170, 200, 230))
    attempts = [[(136.86, 35.25), (136.82, 35.33), (136.80, 35.40)], [(136.80, 35.24), (136.74, 35.30), (136.70, 35.36)],
                [(136.90, 35.28), (136.86, 35.35), (136.83, 35.42)]]
    for i, pts in enumerate(attempts):
        t0 = 0.4 + i * 1.4
        grow = lin(t, t0, t0 + 0.9)
        back = lin(t, t0 + 1.1, t0 + 1.9)
        sp = [mv.P(*q) for q in pts]
        if back <= 0:
            arrow(cv, sp, grow * 0.62, ODA, 36)
        else:
            arrow(cv, sp, 0.62 * (1 - 0.5 * back), ODA, 36, a=1 - 0.7 * back)
        hit = partial(sp, 0.62)[-1]
        blocked_mark(cv, hit[0], hit[1] - 20, 46, ramp(t, t0 + 0.8, 0.2) * (1 - 0.5 * back))
    corner_tag(cv, "调动示意", 1.0)
    quote_card(cv, t, X, "B05c", "客绝水而来，勿迎之于水内，令半济而击之，利。", "《孙子·行军》", "敌人渡河而来，不要在水里迎击；等他渡过一半再打，最有利。", y=560, size=66,
               out=X.s("B05d") - 0.3 if "B05d" in X.ids else None)
    # 半渡示意
    if "B05d" in X.ids:
        k = ramp(t, X.s("B05d"), 0.5)
        if k > 0:
            cv.drawRect(skia.Rect.MakeWH(W, H), paint((6, 8, 12), 0.88 * k))
            cv.drawRect(skia.Rect.MakeXYWH(0, 760, W, 260), paint(WATER, 0.9 * k))
            cv.drawRect(skia.Rect.MakeXYWH(0, 760, W, 300), paint(WATER, 0.9 * k))
            for i in range(14):
                x = 120 + (i % 7) * 120 + (0 if i < 7 else 60); y = 700 if i < 7 else 910
                cv.drawCircle(x, y, 26, paint(ODA, k))
            for i in range(7):
                cv.drawCircle(1150 - (i * 70 + t * 20) % 1300, 1180, 20, paint(ODA, 0.5 * k))
            for i in range(9):
                cv.drawCircle(80 + i * 115, 500, 26, paint(SAITO, k))
            for i in range(5):
                arrow(cv, [(140 + i * 200, 530), (150 + i * 200, 660)], lin(t, X.s("B05d") + 0.8, X.s("B05d") + 1.6), SAITO, 26, a=k)
            text(cv, "已上岸的一半", 1000, 780 - 20, "serif_b", 40, ODA_HI, k, "r", shadow=6)
            text(cv, "还在水里的一半", 1000, 1010, "serif_b", 40, ODA_HI, k, "r", shadow=6)
            text(cv, "后队隔着河，帮不上", W / 2, 1260, "serif_b", 40, (220, 200, 190), k, "c")
            text(cv, "守河一方", 60, 440, "serif_b", 40, (180, 205, 230), k)
            text(cv, "首尾不能相顾", W / 2, 1380, "serif_k", 64, GOLD, ramp(t, X.s("B05d") + 1.8, 0.5), "c", shadow=8)


def sh_supply(cv, t, dur, X):
    mv = plain_view(t, dur, z0=1.2, z1=1.3)
    mv.draw(cv, bright=0.75)
    vgrad(cv, (8, 10, 16), (8, 10, 16), 0, 400, 0.75)
    hdr(cv, t, "补给线：前锋悬在半空")
    draw_rivers(cv, mv, 1.0, 1.0, 1.0)
    place(cv, mv, "kiyosu", "清洲", 1.0, ODA_HI)
    place(cv, mv, "inaba", "稻叶山", 1.0, (170, 200, 230), ring=30)
    src = mv.P(*PL["kiyosu"]); front = mv.P(136.75, 35.405)
    grow = ease(lin(t, 0.4, 3.0))
    pts = partial([src, mv.P(136.80, 35.30), mv.P(136.77, 35.37), front], grow)
    # 补给车队点列
    sp = smooth_path(pts) if len(pts) > 2 else poly_path(pts)
    smp, L = sample_path(sp, 120)
    for i in range(0, len(smp), 4):
        ph = (i / len(smp) + t * 0.15) % 1
        x, y = smp[i][0], smp[i][1]
        cv.drawCircle(x, y, 6, paint(GOLD, 0.8))
    cv.drawPath(sp, paint(GOLD, 0.35, stroke=3))
    if grow > 0.95:
        fx, fy = front
        pulse = 0.5 + 0.5 * math.sin(t * 5)
        cv.drawCircle(fx, fy, 40 + 10 * pulse, paint(ODA, 0.4, blur=14))
        cv.drawCircle(fx, fy, 26, paint(ODA, 1))
        text(cv, "前锋", fx + 40, fy - 30, "serif_b", 42, ODA_HI, 1, shadow=8)
        s7 = X.s("B07")
        k = ramp(t, s7 + 0.8, 0.5)
        for i in range(4):
            a0 = i * math.pi / 2 + 0.4
            arrow(cv, [(fx + 200 * math.cos(a0), fy + 200 * math.sin(a0)), (fx + 60 * math.cos(a0), fy + 60 * math.sin(a0))], k, SAITO, 30)
    text(cv, "粮食 · 箭矢 · 伤兵：全靠身后那条河", W / 2, 1310, "serif_b", 44, WHITE, ramp(t, 1.0, 0.5), "c", shadow=8)
    corner_tag(cv, "机制示意", 1.0)


def sh_suno(cv, t, dur, X):
    z = 1.5 + 1.2 * ease(lin(t, 0, 3.5))
    mv = MapView(basemap("plain"), 136.70 + 0.03 * ease(lin(t, 4, 10)), 35.38, z, cy=860)
    mv.draw(cv, bright=0.8)
    vgrad(cv, (8, 10, 16), (8, 10, 16), 0, 400, 0.75)
    hdr(cv, t, "墨俣（洲股）", "渡口，也是咽喉")
    draw_rivers(cv, mv, 1.0, 1.0, 1.3)
    x, y = mv.P(*PL["suno"])
    s9, s10, s11 = X.s("B09"), X.s("B10"), X.s("B11")
    k = ramp(t, s9, 0.5)
    pulse = 0.5 + 0.5 * math.sin(t * 4)
    cv.drawCircle(x, y, 60 + 30 * pulse * k, paint(ODA, 0.35 * k, blur=20))
    cv.drawCircle(x, y, 22, paint(ODA if k > 0 else WHITE, 1))
    text(cv, "墨俣", x - 30, y + 14, "serif_k", 52, ODA_HI if k > 0 else WHITE, 1, "r", shadow=10)
    place(cv, mv, "inaba", "稻叶山", 1.0, (170, 200, 230), ring=32)
    place(cv, mv, "ogaki", "大垣", 0.8, (200, 200, 200), side="l", size=34)
    # 补给线缩短
    if t > s10:
        q = ease(lin(t, s10, s10 + 2.5))
        far = (x + 520, y + 900)
        mid = (far[0] + (x - far[0]) * q, far[1] + (y - far[1]) * q)
        cv.drawLine(far[0], far[1], x, y, paint(GOLD, 0.25 * (1 - q), stroke=4))
        cv.drawLine(mid[0], mid[1], x, y, paint(GOLD, 0.9, stroke=6))
        text(cv, "补给线缩到河对岸", W / 2, 1300, "serif_b", 46, GOLD, ramp(t, s10 + 1.5, 0.5), "c", shadow=8)
    ka = lin(t, s11 - 0.5, s11 + 1.5)
    ix, iy = mv.P(*PL["inaba"])
    arrow(cv, [(x + 20, y - 20), ((x + ix) / 2 + 30, (y + iy) / 2 + 40), (ix - 30, iy + 30)], ka, ODA, 44)
    corner_tag(cv, "战国时河道示意，与今不同", 1.0)


def sh_koki1561(cv, t, dur, X):
    vgrad(cv, (16, 14, 18), (6, 6, 10))
    hdr(cv, t, "一五六一 · 《信长公记》首卷", "十四条合战之事")
    s13 = X.s("B13")
    a = ramp(t, 0.6, 0.6)
    doc_card(cv, 80, 440, 920, ["永禄四年辛酉五月上旬、木曾川、飛騨川大河打ち越え、西美濃へ御乱入……", "其の後、洲股御要害丈夫に仰せ付けられ、御居陣候", "……洲股御引払ひなさる。"],
             a, title="太田牛一《信长公记》首卷（日文原文节录）",
             hl=[("洲股御要害丈夫に仰せ付けられ", ((230, 120, 90), 0.4 * ramp(t, s13 + 1.5, 0.5))),
                 ("洲股御引払ひなさる", ((120, 150, 230), 0.45 * ramp(t, X.s("B13b"), 0.5)))], size=42)
    if "B12b" in X.ids:
        k = ramp(t, X.s("B12b"), 0.5) * (1 - ramp(t, s13, 0.4))
        text(cv, "斋藤义龙病死 → 龙兴继位", W / 2, 1180, "serif_b", 50, (190, 210, 235), k, "c", shadow=8)
    s15 = X.s("B15")
    k = ramp(t, s15, 0.5)
    if k > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 1050, W, 400), paint((6, 6, 10), 0.85 * k))
        text(cv, "由谁修筑？", 140, 1200, "serif_k", 72, WHITE, k, shadow=8)
        bw = 360
        rrect(cv, 560, 1120, bw, 110, 8, paint(GOLD, k, stroke=4))
        if (t * 2) % 2 < 1.3:
            cv.drawLine(590, 1140, 590, 1210, paint(GOLD, k, stroke=4))
        text(cv, "书上没写", 740, 1330, "serif_b", 46, ODA_HI, ramp(t, s15 + 1.2, 0.4), "c")
    s16 = X.s("B16")
    if t > s16:
        text(cv, "记住这个空白", W / 2, 1420, "serif_k", 56, GOLD, ramp(t, s16, 0.5), "c", shadow=10)
    corner_tag(cv, "原文据日文版本", 1.0)


# ============ C 传说第一、二层 ============
def layer_bar(cv, t, idx, a=1.0):
    """顶部小时间尺：四层中当前层高亮。"""
    y = 410
    cv.drawLine(120, y, 960, y, paint((120, 120, 120), 0.6 * a, stroke=3))
    for i, (yr, *_r) in enumerate(STRATA):
        x = 120 + i * 280
        on = i == idx
        cv.drawCircle(x, y, 16 if on else 10, paint(ODA if on else (130, 130, 130), a))
        text(cv, yr, x, y + 58, "serif_b", 36 if on else 30, ODA_HI if on else (160, 160, 160), a, "c")
    text(cv, "1566", 50, y - 26, "sans", 26, (150, 150, 150), 0.0)


def sh_layer1(cv, t, dur, X):
    vgrad(cv, (20, 17, 14), (8, 7, 6))
    hdr(cv, t, "传说第一层 · 1626")
    layer_bar(cv, t, 0, ramp(t, 0.2, 0.5))
    slip(cv, 80, 520, 420, 560, "太閤記", "小濑甫庵著\n离事件约60年", ramp(t, 0.4, 0.5), tag="后世 · 偏颂扬")
    s3, s4, s5, s6 = X.s("C03"), X.s("C04"), X.s("C05"), X.s("C06")
    rows = [("1566 · 美浓敌境的一座要害", True, s3 + 0.5), ("木料先备好，扎筏顺流放下", True, s4 + 0.3), ("七八天大体建成", True, s4 + 3.0),
            ("守将中已有蜂须贺小六", True, s4 + 5.0), ("城在墨俣", False, s5 + 0.8), ("一夜", False, s5 + 2.2)]
    for i, (lb, ok, ts) in enumerate(rows):
        check_row(cv, 520, 600 + i * 96, lb, ok, ramp(t, ts, 0.4), size=36)
    k = ramp(t, s6, 0.5)
    if k > 0:
        rrect(cv, 80, 1190, 920, 150, 12, paint((60, 20, 14), 0.7 * k))
        para(cv, "以颂扬秀吉著称，不少场面和对话是作者补写", W / 2, 1255, 860, "serif_b", 42, (255, 200, 180), k, 1.4, "c")
    text(cv, "原书章名：秀吉卿轻一命于敌国成要害之主事", W / 2, 1160, "sans", 30, (200, 185, 150), ramp(t, s3, 0.4) * (1 - ramp(t, s6, 0.3)), "c")


def sh_layer2(cv, t, dur, X):
    vgrad(cv, (22, 16, 14), (8, 6, 6))
    hdr(cv, t, "传说第二层 · 1797")
    layer_bar(cv, t, 1, ramp(t, 0.2, 0.5))
    s8, s10, s11, s12, s13 = X.s("C08"), X.s("C10"), X.s("C11"), X.s("C12"), X.s("C13")
    k0 = ramp(t, 0.3, 0.5) * (1 - ramp(t, s10 - 0.2, 0.4))
    slip(cv, 300, 520, 480, 640, "絵本太閤記", "读本小说\n离事件约230年", k0, accent=(220, 150, 110), tag="通俗小说，不是史书")
    # 三格分镜
    panels = [("佐久间信盛", False, s10 + 0.4), ("柴田胜家", False, s10 + 2.6), ("秀吉", True, s11 + 0.2)]
    for i, (nm, ok, ts) in enumerate(panels):
        k = ramp(t, ts, 0.4) * (1 - ramp(t, s13 - 0.3, 0.4))
        if k <= 0:
            continue
        x = 70 + i * 320
        rrect(cv, x, 520, 300, 560, 10, paint((30, 26, 24), 0.95 * k))
        rrect(cv, x, 520, 300, 560, 10, paint(GOLD if ok else (120, 110, 100), k, stroke=3))
        figure(cv, x + 150, 960, 2.0, a=k, col=(200, 186, 160) if ok else (110, 100, 92), pose=0, t=0)
        text(cv, nm, x + 150, 1040, "serif_b", 40, WHITE, k, "c")
        if not ok:
            stamp(cv, "失败", x + 150, 680, lin(t, ts + 0.5, ts + 0.9), 64, rot=-12)
        else:
            kk = ramp(t, s11 + 1.8, 0.4)
            text(cv, "「七天！」", x + 150, 640, "serif_k", 56, GOLD, kk, "c")
            if t > s12:
                stamp(cv, "一夜", x + 150, 760, lin(t, s12 + 0.5, s12 + 0.9), 80, col=ODA)
    # C13 对照
    k = ramp(t, s13, 0.5)
    if k > 0:
        cols = [("", "1626 甫庵", "1797 绘本"), ("城名", "—", "洲股"), ("一夜", "—", "有"), ("失败的前辈", "—", "两位"), ("年份", "1566", "1562")]
        for r, row in enumerate(cols):
            y = 640 + r * 110
            for c, cell in enumerate(row):
                x = 140 + c * 300
                col = GOLD if r == 0 else (ODA_HI if c == 2 else WHITE)
                text(cv, cell, x, y, "serif_b", 44, col, ramp(t, s13 + r * 0.35, 0.4), "l")
            cv.drawLine(120, y + 32, 980, y + 32, paint((120, 110, 100), 0.5 * k, stroke=1.5))
    corner_tag(cv, "剧情据《绘本太阁记》", ramp(t, s10, 0.4))


def sh_structure(cv, t, dur, X):
    vgrad(cv, (18, 14, 18), (6, 6, 8))
    hdr(cv, t, "说书的结构")
    beats = ["两位重臣失败", "小人物出头", "立下期限", "一夜逆转"]
    for i, b in enumerate(beats):
        k = ramp(t, 0.6 + i * 0.9, 0.4)
        y = 560 + i * 190
        rrect(cv, 200, y, 680, 130, 65, paint(mix((60, 50, 60), ODA, i / 3), 0.9 * k))
        text(cv, b, W / 2, y + 84, "serif_k", 56, WHITE, k, "c")
        if i < 3:
            arrow(cv, [(W / 2, y + 136), (W / 2, y + 184)], ramp(t, 1.0 + i * 0.9, 0.3), GOLD, 16, glow=False)
    s15 = X.s("C15")
    k = ramp(t, s15 + 2.2, 0.5)
    text(cv, "与观众的期待严丝合缝", W / 2, 1380, "serif_b", 50, GOLD, k, "c", shadow=8)


# ============ D 《武功夜话》 ============
BK_TAG = "据《武功夜话》，真伪有争议"


def sh_bk_intro(cv, t, dur, X):
    river_scene(cv, t * 0.6, 0.0, 0.0, 0.0, rafts=1.0, hammer=False)
    cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.45))
    hdr(cv, t, "传说第三层 · 1987", "最燃的一层")
    layer_bar(cv, t, 3, ramp(t, 0.2, 0.5))
    s2, s3, s4 = X.s("D02"), X.s("D03"), X.s("D04")
    slip(cv, 300, 520, 480, 620, "武功夜話", "前野家文书\n1987 年刊行", ramp(t, s2, 0.5) * (1 - ramp(t, s3 + 0.5, 0.4)), accent=(230, 130, 100))
    k = ramp(t, s3 + 0.6, 0.5)
    if k > 0:
        text(cv, "蜂须贺小六", W / 2, 720, "serif_k", 100, WHITE, k, "c", shadow=18, glow=(ODA, 30, 0.4))
        text(cv, "川并众的头领 · 建城主力", W / 2, 820, "serif_b", 46, GOLD, k, "c", shadow=8)
        text(cv, "（1626 年的甫庵书里，他只是守将之一）", W / 2, 890, "sans", 34, (200, 190, 180), ramp(t, s3 + 2.0, 0.5), "c")
    k = ramp(t, s4, 0.5)
    for i, (lb, x) in enumerate([("熟悉水路", 200), ("伐木放排", 540), ("也会打仗", 880)]):
        kk = ramp(t, s4 + 1.2 + i * 0.7, 0.4)
        rrect(cv, x - 150, 1010, 300, 100, 50, paint(ODA, 0.85 * kk))
        text(cv, lb, x, 1078, "serif_k", 46, WHITE, kk, "c")
    corner_tag(cv, BK_TAG, 1.0, col=(255, 190, 160))


def sh_bk_forest(cv, t, dur, X):
    vgrad(cv, (10, 16, 18), (20, 26, 22))
    cv.save(); cv.translate(-40 * t / dur, 0)
    forest(cv, t, 900, 1, seed=3, n=30, sc=1.0)
    forest(cv, t, 1200, 1, seed=8, n=18, sc=1.5, col=(6, 10, 8))
    cv.restore()
    cv.drawRect(skia.Rect.MakeXYWH(0, 1250, W, 700), paint((14, 16, 12)))
    for i in range(4):
        figure(cv, 160 + i * 250, 1380, 1.4, pose=1 if i % 2 == 0 else 3, t=t * 1.2, seed=i, col=(4, 4, 6))
        if i % 2 == 0 and (math.sin(t * 7 + i) > 0.95):
            cv.drawCircle(220 + i * 250, 1260, 30, paint((255, 230, 180), 0.5, blur=12))
    # 堆好的构件
    k = ramp(t, 2.0, 1.0)
    for j in range(6):
        rrect(cv, 120 + j * 140, 1470 - 0, 120, 26, 6, paint((110, 80, 50), k))
        rrect(cv, 140 + j * 140, 1440, 100, 26, 6, paint((96, 70, 44), k))
    text(cv, "上游 · 预制", W / 2, 300, "serif_k", 70, GOLD, ramp(t, 0.2, 0.5), "c", shadow=12)
    text(cv, "栅栏 · 木板 · 橹的构件", W / 2, 390, "serif_b", 46, WHITE, ramp(t, 1.5, 0.5), "c", shadow=8)
    corner_tag(cv, BK_TAG, 1.0, col=(255, 190, 160))


def sh_bk_map(cv, t, dur, X):
    mv = plain_view(t, dur, lon=136.78, lat=35.40, z0=1.25, z1=1.35)
    mv.draw(cv, bright=0.6)
    vgrad(cv, (6, 8, 14), (6, 8, 14), 0, 400, 0.8)
    draw_rivers(cv, mv, 1.0, 1.0, 1.2)
    place(cv, mv, "inaba", "稻叶山", 1.0, (170, 200, 230), ring=30)
    sx, sy = mv.P(*PL["suno"])
    path = [mv.P(137.02, 35.43), mv.P(136.94, 35.39), mv.P(136.85, 35.38), mv.P(136.775, 35.366), mv.P(136.73, 35.37), (sx + 10, sy)]
    g = ease(lin(t, 0.3, dur - 0.8))
    arrow(cv, path, g, ODA, 34, dashed=True)
    pp = partial(path, g)[-1]
    raft(cv, pp[0], pp[1] - 40, 0.22)
    cv.drawCircle(sx, sy, 20, paint(ODA, 1))
    text(cv, "墨俣", sx - 30, sy + 14, "serif_k", 50, ODA_HI, 1, "r", shadow=10)
    text(cv, "顺流而下", W / 2, 300, "serif_k", 70, GOLD, ramp(t, 0.2, 0.5), "c", shadow=12)
    # 图例
    rrect(cv, 60, 1240, 520, 80, 12, paint((0, 0, 0), 0.6))
    arrow(cv, [(90, 1280), (250, 1280)], 1.0, ODA, 22, dashed=True, glow=False)
    text(cv, "虚线 = 传说路线", 280, 1294, "sans", 34, WHITE, 1)
    corner_tag(cv, BK_TAG, 1.0, col=(255, 190, 160))


def sh_bk_build(cv, t, dur, X):
    s8, s9, s10, s11 = X.s("D08"), X.s("D09"), X.s("D10"), X.s("D11")
    build = 0.05 + 0.8 * ease(lin(t, 0.5, s11)) + 0.15 * ease(lin(t, s11, s11 + 1.5))
    dawn = ease(lin(t, s11 - 0.3, s11 + 2.5))
    fight = ramp(t, s8, 0.5) * (1 - ramp(t, s11, 1.0))
    shake = 6 * fight * math.sin(t * 40) * (0.5 + 0.5 * math.sin(t * 3))
    cv.save(); cv.translate(shake, 0)
    river_scene(cv, t, build, dawn, cam=0.35 * ease(lin(t, s11, s11 + 2.5)), fight=fight, rafts=1 - dawn, fire=fight)
    cv.restore()
    if t < s8:
        text(cv, "夜 · 上岸 · 组装", W / 2, 300, "serif_k", 70, GOLD, ramp(t, 0.2, 0.5) * (1 - ramp(t, s8 - 0.3, 0.3)), "c", shadow=12)
    k = ramp(t, s10, 0.25) * (1 - ramp(t, s11 + 0.2, 0.4))
    if k > 0:
        sc = 1.25 - 0.25 * eout(lin(t, s10, s10 + 0.4))
        cv.save(); cv.translate(W / 2, 520); cv.scale(sc, sc)
        text(cv, "一边打 · 一边建", 0, 0, "serif_k", 104, WHITE, k, "c", shadow=20, glow=(ODA, 40, 0.6))
        cv.restore()
    k = ramp(t, s11 + 1.2, 0.6)
    text(cv, "天亮 · 城已立起", W / 2, 470, "serif_k", 96, (255, 246, 226), k, "c", shadow=20, glow=(ODA, 40, 0.45))
    corner_tag(cv, BK_TAG, 1.0, col=(255, 190, 160))
    text(cv, "情景演绎", W - 50, 180, "sans", 28, (210, 200, 190), 0.8, "r")


def sh_bk_too_good(cv, t, dur, X):
    vgrad(cv, (14, 12, 16), (6, 6, 8))
    hdr(cv, t, "好到回答了所有问题")
    s12, s13, s14 = X.s("D12"), X.s("D13"), X.s("D14")
    rows = ["木料哪来", "怎么运", "为什么快", "敌人为什么没拦住"]
    for i, r in enumerate(rows):
        check_row(cv, 260, 560 + i * 110, r, True, ramp(t, s12 + 2.0 + i * 0.7, 0.3))
    k = ramp(t, s13, 0.5) * (1 - ramp(t, s14, 0.4))
    text(cv, "预制 · 水运 · 夜间组装", W / 2, 1080, "serif_k", 60, GOLD, k, "c", shadow=8)
    k = ramp(t, s14, 0.5)
    if k > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.6 * k))
        text(cv, "最晚出现的文书", W / 2, 820, "serif_k", 84, WHITE, k, "c", shadow=14)
        text(cv, "为什么讲得最完整？", W / 2, 960, "serif_k", 84, ODA_HI, ramp(t, s14 + 1.5, 0.5), "c", shadow=14)


# ============ E 证据审查 ============
def sh_ev_doc(cv, t, dur, X):
    vgrad(cv, (12, 14, 18), (6, 6, 8))
    hdr(cv, t, "证据审查")
    kura(cv, W / 2, 1150, 1.2, a=0.8, wet=0.3)
    s2, s3 = X.s("E02"), X.s("E03")
    cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.35))
    tl = [("1959", "据称在仓库被发现", s2 + 0.3), ("1977", "地方上开始介绍", s2 + 1.4), ("1987", "整理出版", s2 + 3.2)]
    for i, (y, lb, ts) in enumerate(tl):
        k = ramp(t, ts, 0.4)
        text(cv, y, 200, 520 + i * 110, "serif_k", 60, GOLD, k, shadow=8)
        text(cv, lb, 380, 520 + i * 110, "serif_b", 46, WHITE, k, shadow=8)
    k = ramp(t, s3, 0.5)
    if k > 0:
        cx, cy = W / 2, 1060
        rrect(cv, cx - 90, cy - 40, 180, 150, 18, paint(ODA, k))
        cv.drawPath(smooth_path([(cx - 55, cy - 40), (cx - 55, cy - 110), (cx, cy - 150), (cx + 55, cy - 110), (cx + 55, cy - 40)]), paint(ODA, k, stroke=20))
        cv.drawCircle(cx, cy + 30, 18, paint((30, 10, 10), k))
        text(cv, "原本未向公众公开", W / 2, 1270, "serif_k", 64, WHITE, k, "c", shadow=10)
        text(cv, "纸张 · 墨迹 · 笔迹，外人无从检验", W / 2, 1350, "serif_b", 40, (220, 200, 190), ramp(t, s3 + 1.5, 0.5), "c")
    corner_tag(cv, "情景演绎", 1.0)


def sh_ev_book(cv, t, dur, X):
    vgrad(cv, (14, 14, 20), (6, 6, 8))
    s4, s5, s5b, s6, s7, s8 = (X.s(i) for i in ("E04", "E05", "E05b", "E06", "E07", "E08"))
    k0 = 1 - ramp(t, s7 - 0.3, 0.4)
    hdr(cv, t, "2002 ·《伪书〈武功夜话〉的研究》", "藤本正行 · 铃木真哉（洋泉社）", a=k0)
    slip(cv, 80, 440, 340, 520, "偽書武功夜話の研究", "", ramp(t, s4, 0.5) * k0, accent=(200, 200, 220))
    items = [("「铁炮队」等带「队」的叫法", "后世用法", s5 + 1.5), ("江户中期以后才写成", "两人的结论", s5b + 0.3),
             ("「八百津」", "1889 年才有的地名", s6 + 1.6), ("「富加」", "1954 年合并时才起", s6 + 2.6)]
    for i, (a_, b_, ts) in enumerate(items):
        k = ramp(t, ts, 0.4) * k0
        if k <= 0:
            continue
        y = 470 + i * 130
        rrect(cv, 450, y, 560, 112, 10, paint((40, 30, 30), 0.9 * k))
        text(cv, a_, 476, y + 50, "serif_b", 38, WHITE, k)
        text(cv, b_, 476, y + 96, "sans", 30, ODA_HI, k)
    k = ramp(t, s6, 0.4) * k0
    text(cv, "地名一条，出自其他研究者", 450, 1040, "sans", 28, (170, 170, 170), k)
    # 天平
    k = ramp(t, s7, 0.5)
    if k > 0:
        tilt = 0.12 * math.sin(t * 1.2)
        cx, cy = W / 2, 760
        cv.drawLine(cx, cy, cx, cy + 440, paint(GOLD, k, stroke=10))
        cv.save(); cv.translate(cx, cy); cv.rotate(math.degrees(tilt))
        cv.drawLine(-360, 0, 360, 0, paint(GOLD, k, stroke=10))
        for sx_, lb, col in ((-360, "伪书说", ODA_HI), (360, "辩护说", (170, 200, 230))):
            cv.drawLine(sx_, 0, sx_ - 90, 220, paint(GOLD, k * 0.7, stroke=3)); cv.drawLine(sx_, 0, sx_ + 90, 220, paint(GOLD, k * 0.7, stroke=3))
            cv.drawPath(smooth_path([(sx_ - 130, 220), (sx_, 280), (sx_ + 130, 220)]), paint(GOLD, k, stroke=8))
            text(cv, lb, sx_, 200, "serif_k", 52, col, k, "c", shadow=8)
        cv.restore()
        text(cv, "看过原件的学者：经后人改动，仍有价值", W / 2, 1310, "serif_b", 40, (200, 215, 235), ramp(t, s7 + 1.5, 0.5) * (1 - ramp(t, s8, 0.3)), "c")
        k8 = ramp(t, s8 + 1.8, 0.5)
        text(cv, "拿它证明一夜城：靠不住", W / 2, 1310, "serif_k", 60, ODA_HI, k8, "c", shadow=10)
        text(cv, "争论仍在继续", W / 2, 520, "serif_k", 64, GOLD, ramp(t, s8, 0.5), "c", shadow=10)


def sh_bartlett(cv, t, dur, X):
    vgrad(cv, (12, 14, 20), (6, 6, 10))
    hdr(cv, t, "系列再现实验", "巴特利特《记忆》（1932）")
    s10, s11, s12 = X.s("E10"), X.s("E11"), X.s("E12")
    n = 5
    for i in range(n):
        k = ramp(t, s10 + 1.0 + i * 0.8, 0.4)
        x = 140 + i * 200; y = 820
        cv.drawCircle(x, y, 58, paint((70, 80, 100), k))
        cv.drawCircle(x, y - 10, 24, paint((180, 190, 210), k))
        cv.drawPath(smooth_path([(x - 40, y + 40), (x, y + 18), (x + 40, y + 40)]), paint((180, 190, 210), k, stroke=10))
        if i < n - 1:
            arrow(cv, [(x + 66, y), (x + 134, y)], ramp(t, s10 + 1.4 + i * 0.8, 0.3), GOLD, 14, glow=False)
        # 故事条：越传越短、越整齐
        q = i / (n - 1)
        bars = int(9 - 5 * q)
        for b in range(bars):
            r = np.random.default_rng(i * 10 + b)
            bw = 150 * (r.uniform(0.4, 1.0) * (1 - q) + 0.8 * q)
            col = mix((200, 120, 90) if r.uniform() < 0.35 * (1 - q) else (180, 180, 180), (220, 200, 150), q)
            rrect(cv, x - 75, 940 + b * 26, bw, 16, 8, paint(col, k * 0.9))
    k = ramp(t, s11, 0.5)
    if k > 0:
        for i, (lb, ts) in enumerate([("变短", s11 + 0.8), ("陌生细节被丢掉", s11 + 2.0), ("说不通的被改得说得通", s11 + 3.6)]):
            text(cv, lb, W / 2, 1240 + i * 70, "serif_b", 46, WHITE, ramp(t, ts, 0.4), "c", shadow=6)
    k = ramp(t, s12 + 1.5, 0.5)
    if k > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 520, W, 160), paint((0, 0, 0), 0.6 * k))
        text(cv, "记忆不是录像，是重建", W / 2, 630, "serif_k", 72, GOLD, k, "c", shadow=12)


def sh_gu(cv, t, dur, X):
    vgrad(cv, (18, 14, 12), (6, 6, 6))
    s13, s14, s16 = X.s("E13"), X.s("E14"), X.s("E16")
    k0 = 1 - ramp(t, s16 - 0.2, 0.4)
    if t < s14:
        text(cv, "越传越顺，可细节为什么越来越多？", W / 2, 900, "serif_k", 58, WHITE, ramp(t, s13, 0.5), "c", shadow=10)
    else:
        k = ramp(t, s14, 0.5) * k0
        text(cv, "顾颉刚 · 1923", W / 2, 420, "serif_k", 62, GOLD, k, "c", shadow=10)
        text(cv, "「层累地造成的中国古史」", W / 2, 510, "serif_b", 48, WHITE, k, "c", shadow=8)
        if k0 > 0:
            cv.save()
            quote_card(cv, t, X, "E15", "时代愈后，传说中的中心人物愈放愈大。", "顾颉刚《与钱玄同先生论古史书》（1923）", "越往后，故事的中心人物被放得越大。", y=700, size=64)
            cv.restore()
    if "E16" in X.ids and t > s16 - 0.2:
        k = ramp(t, s16 - 0.2, 0.5)
        hdr(cv, t - s16, "层层往上加", a=k)
        sb = X.s("E16b") if "E16b" in X.ids else s16 + 3
        rows = [("1626", "敌境的一座要害", s16 + 0.6), ("1797", "＋城名 ＋一夜 ＋失败的前辈", sb + 2.8), ("1987", "＋川并众 ＋木料来路 ＋上岸时辰", sb + 5.6)]
        for i, (y, lb, ts) in enumerate(rows):
            kk = ramp(t, ts, 0.4)
            yy = 1180 - i * 220
            w = 420 + i * 250
            rrect(cv, W / 2 - w / 2, yy - 90, w, 150, 12, paint(mix((90, 70, 50), ODA, i / 2), 0.9 * kk))
            text(cv, y, W / 2, yy - 20, "serif_k", 52, GOLD, kk, "c")
            text(cv, lb, W / 2, yy + 40, "serif_b", 36, WHITE, kk, "c")


def sh_hindsight(cv, t, dur, X):
    vgrad(cv, (14, 12, 18), (6, 6, 8))
    hdr(cv, t, "后见之明")
    s18, s19 = X.s("E18"), X.s("E19")
    y = 900
    cv.drawLine(100, y, 980, y, paint((140, 140, 140), 0.8, stroke=4))
    for x, lb in ((180, "早年"), (900, "天下人")):
        cv.drawCircle(x, y, 14, paint(WHITE, 1))
        text(cv, lb, x, y + 70, "serif_b", 44, WHITE, 1, "c")
    k = ramp(t, 0.8, 0.5)
    cv.drawCircle(900, y, 50 + 6 * math.sin(t * 3), paint(GOLD, 0.4 * k, blur=20))
    arrow(cv, [(880, y - 60), (540, y - 220), (220, y - 70)], lin(t, 1.5, 3.5), GOLD, 30)
    text(cv, "回头找「天才的证据」", W / 2, y - 260, "serif_b", 46, GOLD, ramp(t, 3.0, 0.5), "c")
    k = ramp(t, s18, 0.5)
    text(cv, "凭什么爬到顶？", W / 2, 1180, "serif_k", 64, WHITE, k, "c", shadow=10)
    k = ramp(t, s19, 0.5)
    if k > 0:
        rrect(cv, 140, y - 50, 120, 100, 8, paint(ODA, k, stroke=5))
        f = ease(lin(t, s19 + 0.8, s19 + 1.8))
        rrect(cv, 140, y - 50, 120, 100, 8, paint(ODA, 0.8 * f))
        text(cv, "墨俣", 200, y + 18, "serif_k", 44, WHITE, f, "c")
        text(cv, "恰好填进这个空白", W / 2, 1300, "serif_k", 60, ODA_HI, ramp(t, s19 + 1.2, 0.5), "c", shadow=10)


# ============ F 可信的秀吉 ============
def sh_docs(cv, t, dur, X):
    vgrad(cv, (16, 16, 14), (6, 6, 6))
    hdr(cv, t, "真正能确定的秀吉")
    s2, s3, s3b = X.s("F02"), X.s("F03"), X.s("F03b")
    k = ramp(t, s2, 0.5) * (1 - ramp(t, s3 - 0.2, 0.3))
    if k > 0:
        check_row(cv, 200, 640, "出身低微：没有争议", True, ramp(t, s2, 0.4))
        check_row(cv, 200, 760, "父亲是足轻：只是通说", False, ramp(t, s2 + 2.2, 0.4))
        check_row(cv, 200, 880, "早年故事：多出自后世", False, ramp(t, s2 + 4.0, 0.4))
    k = ramp(t, s3, 0.5)
    if k > 0:
        y = 900
        x0, x1 = 100, 980
        def X_(yr):
            return x0 + (yr - 1558) / (1572 - 1558) * (x1 - x0)
        cv.drawLine(x0, y, x1, y, paint((150, 150, 150), k, stroke=4))
        for yr in range(1560, 1572, 2):
            text(cv, str(yr), X_(yr), y + 56, "sans", 28, (160, 160, 160), k, "c")
        kz = ramp(t, s3b, 0.5)
        cv.drawRect(skia.Rect.MakeXYWH(X_(1561), y - 170, X_(1566) - X_(1561), 170), paint(ODA, 0.25 * kz))
        text(cv, "传说发生的年份：几乎没有同时代记录", (X_(1561) + X_(1566)) / 2, y - 196, "serif_b", 34, ODA_HI, kz, "c")
        for yr, lb, sub, ts in ((1565, "1565", "最早署名「木下藤吉郎秀吉」（抄本）", s3 + 0.8), (1568, "1568", "现存最早原件", s3 + 4.0)):
            kk = ramp(t, ts, 0.4)
            x = X_(yr)
            cv.drawCircle(x, y, 16, paint(GOLD, kk))
            cv.drawLine(x, y + 80, x, y + 180 + (yr - 1565) * 50, paint(GOLD, kk * 0.6, stroke=2))
            text(cv, lb, x, y + 230 + (yr - 1565) * 50, "serif_k", 48, GOLD, kk, "c")
            text(cv, sub, min(max(x, 330), 750), y + 290 + (yr - 1565) * 50, "serif_b", 36, WHITE, kk, "c")


def sh_frois(cv, t, dur, X):
    vgrad(cv, (16, 14, 12), (6, 6, 6))
    hdr(cv, t, "弗洛伊斯《日本史》", "葡萄牙传教士 · 记秀吉对其一行所言")
    s5, s6 = X.s("F05"), X.s("F06")
    a = ramp(t, 0.8, 0.6)
    doc_card(cv, 70, 470, 940, ["皆が見るとおり、予は醜い顔をしており、五体も貧弱だが、予の日本における成功を忘れるでないぞ"], a,
             title="松田毅一、川崎桃太译《日本史》第4卷（日译本）", size=46, hl=[("予の日本における成功", ((230, 150, 90), 0.4 * ramp(t, s5 + 2, 0.5)))])
    k = ramp(t, s5 - 0.2, 0.5)
    para(cv, "「你们都看到了，我长得丑，身子也弱。但别忘了，我在日本的成功。」", W / 2, 1020, 880, "serif_b", 50, WHITE, k, 1.5, "c", shadow=8)
    k = ramp(t, s6 + 0.5, 0.5)
    text(cv, "他要人记住的，是做成的事", W / 2, 1300, "serif_k", 58, GOLD, k, "c", shadow=10)


def sh_battles(cv, t, dur, X):
    bm = basemap("big")
    mv = MapView(bm, 136.6, 35.4, 1.25 + 0.1 * t / dur, cy=880)
    mv.draw(cv, bright=0.7)
    vgrad(cv, (8, 8, 12), (8, 8, 12), 0, 420, 0.8)
    hdr(cv, t, "撑起他的，是有据可查的硬仗")
    arrows = [[(136.84, 35.21), (136.6, 35.5), (136.25, 35.62)], [(136.84, 35.21), (136.5, 35.15), (136.1, 35.05)], [(136.7, 35.4), (136.3, 35.9), (136.05, 35.95)]]
    for i, a_ in enumerate(arrows):
        arrow(cv, [mv.P(*q) for q in a_], lin(t, 0.5 + i * 0.8, 2.5 + i * 0.8), ODA, 40)
    corner_tag(cv, "示意", 1.0)


# ============ G 收束 ============
def sh_museum(cv, t, dur, X):
    s3, s4 = X.s("G03"), X.s("G04")
    k3 = ramp(t, s3, 0.6)
    vgrad(cv, (44, 54, 78), (190, 150, 130), 0, 1100)
    vgrad(cv, (40, 44, 50), (14, 14, 18), 1100, H)
    cv.save(); s = 1.0 + 0.05 * t / dur
    cv.translate(W / 2, 1100); cv.scale(s, s); cv.translate(-W / 2, -1100)
    forest(cv, t, 1120, 0.9, seed=12, n=26, sc=0.5, col=(20, 24, 26))
    tenshu(cv, W / 2, 1110, 1.0, a=1 - 0.6 * k3)
    cv.restore()
    text(cv, "今天的「墨俣一夜城」", W / 2, 300, "serif_k", 66, WHITE, ramp(t, 0.2, 0.5), "c", shadow=12)
    k = ramp(t, X.s("G02"), 0.5) * (1 - k3)
    text(cv, "大垣市墨俣历史资料馆 · 1991", W / 2, 1300, "serif_b", 44, WHITE, k, "c", shadow=8)
    text(cv, "外观仿大垣城天守", W / 2, 1370, "serif_b", 44, GOLD, k, "c", shadow=8)
    if k3 > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 1150, W, 400), paint((10, 10, 12), 0.85 * k3))
        stake_row(cv, [(120 + i * 38, 1380, 0.8) for i in range(10)], 1.0, a=k3, h=110)
        yagura(cv, 300, 1380, 0.55, 1.0, a=k3)
        text(cv, "战国时：栅栏 · 土垒 · 木橹", 330, 1470, "serif_b", 36, WHITE, k3, "c")
        text(cv, "≠", 600, 1330, "serif_k", 90, ODA_HI, k3, "c")
        tenshu(cv, 830, 1380, 0.4, a=k3)
        text(cv, "今天：仿天守", 830, 1470, "serif_b", 36, WHITE, k3, "c")
    k = ramp(t, s4 + 0.5, 0.5)
    if k > 0:
        cv.drawRect(skia.Rect.MakeXYWH(0, 380, W, 170), paint((0, 0, 0), 0.55 * k))
        text(cv, "按传说盖的楼，纪念查无实据的城", W / 2, 490, "serif_k", 54, GOLD, k, "c", shadow=10)
    corner_tag(cv, "建筑示意，非实景", 1.0)


def sh_mencius(cv, t, dur, X):
    vgrad(cv, (14, 12, 10), (4, 4, 4))
    cv.drawCircle(W / 2, 800, 500, paint(GOLD, 0.06, blur=180))
    k = ramp(t, 0.2, 0.6)
    text(cv, "孟 子", W / 2, 520, "serif_k", 64, GOLD, k * (1 - ramp(t, X.s("G06") - 0.6, 0.3)), "c", ls=10)
    quote_card(cv, t, X, "G06", "尽信《书》，\n则不如无《书》。", "《孟子·尽心下》", "完全相信书上写的，还不如没有书。", y=640, size=96)


def sh_takeaway(cv, t, dur, X):
    vgrad(cv, (16, 12, 12), (4, 4, 6))
    k = ramp(t, 0.2, 0.6)
    text(cv, "越是成功者的起家故事", W / 2, 640, "serif_k", 70, WHITE, k, "c", shadow=12)
    text(cv, "越要问一句", W / 2, 760, "serif_k", 70, WHITE, ramp(t, 1.2, 0.5), "c", shadow=12)
    text(cv, "哪一年？谁写的？", W / 2, 930, "serif_k", 110, ODA_HI, ramp(t, 2.4, 0.5), "c", shadow=20, glow=(ODA, 40, 0.4))
    if "G08b" in X.ids:
        sb, sc = X.s("G08b"), X.s("G08c")
        for i, (lb, ts) in enumerate([("离事件多近", sb + 3.0), ("经过几道手", sb + 4.3)]):
            text(cv, lb, W / 2, 1110 + i * 80, "serif_b", 50, GOLD, ramp(t, ts, 0.4), "c")
        text(cv, "越远 · 越多手 · 越漂亮 → 越要多问", W / 2, 1330, "serif_b", 44, (225, 215, 200), ramp(t, sc + 0.5, 0.5), "c")


def sh_next(cv, t, dur, X):
    vgrad(cv, (10, 12, 14), (18, 20, 18))
    # 山道
    for i, (col, yb, amp) in enumerate([((22, 28, 30), 900, 220), ((14, 18, 18), 1100, 180), ((8, 10, 10), 1300, 140)]):
        pts = [(0, H)] + [(x, yb - amp * (0.5 + 0.5 * math.sin(x / 180 + i * 2))) for x in range(0, W + 60, 60)] + [(W, H)]
        cv.drawPath(poly_path(pts, True), paint(col))
    road = smooth_path([(200, H), (420, 1500), (640, 1300), (520, 1150), (700, 1000)])
    cv.drawPath(road, paint((60, 56, 48), 0.9, stroke=40))
    for i in range(5):
        ph = (t * 0.08 + i / 5) % 1
        smp, L = sample_path(road, 100)
        p = smp[int((1 - ph) * 99)]
        figure(cv, p[0], p[1], 0.3 + 0.5 * ph, col=(4, 4, 6), pose=0, t=t)
    k = ramp(t, 0.6, 0.6)
    doc_card(cv, 90, 420, 900, ["金ケ崎の城には木下藤吉郎残しをかせられ"], k, title="《信长公记》卷三（日文原文节录）", size=44,
             hl=[("木下藤吉郎", ((230, 120, 90), 0.45))])
    k = ramp(t, 2.5, 0.6)
    text(cv, "下一集", W / 2, 800, "sans", 40, (210, 200, 190), k, "c", ls=10)
    text(cv, "金崎撤退", W / 2, 930, "serif_k", 130, WHITE, k, "c", ls=12, shadow=20, glow=(ODA, 40, 0.45))
    text(cv, "1570 · 断后的人", W / 2, 1030, "serif_b", 48, GOLD, ramp(t, 3.2, 0.5), "c")


# 镜头表：(起始句 id, 函数)
SHOTS = [("A01", sh_hook), ("A03", sh_koki), ("A05", sh_strata), ("A08", sh_typhoon), ("A11", sh_question),
         ("B01", sh_bigmap), ("B03", sh_rivers), ("B05", sh_cross), ("B06", sh_supply), ("B08", sh_suno), ("B12", sh_koki1561),
         ("C01", sh_layer1), ("C07", sh_layer2), ("C14", sh_structure),
         ("D01", sh_bk_intro), ("D05", sh_bk_forest), ("D06", sh_bk_map), ("D07", sh_bk_build), ("D12", sh_bk_too_good),
         ("E01", sh_ev_doc), ("E04", sh_ev_book), ("E09", sh_bartlett), ("E13", sh_gu), ("E17", sh_hindsight),
         ("F01", sh_docs), ("F04", sh_frois), ("F07", sh_battles),
         ("G01", sh_museum), ("G05", sh_mencius), ("G08", sh_takeaway), ("G09", sh_next)]
