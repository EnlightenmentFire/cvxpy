# -*- coding: utf-8 -*-
"""逐镜头画面。每句旁白有 v 标记；v -> 镜头(shot)；同一镜头的连续句子共享一个画面，内部按事件时间推进。"""
import math
import numpy as np
import skia
from eng import *

# ---------------------------------------------------------------- 镜头分配
SHOT = {}
for v in ["bian_night", "caohong", "river_escape"]:
    SHOT[v] = "night"
SHOT["bian_flash"] = "phalanx"
for v in ["suanzao_feast", "suanzao_feast2", "rebuke"]:
    SHOT[v] = "feast"
for v in ["west_arrow", "yangzhou", "map_east", "map_cao", "map_luoyang_fire", "map_cao_speech", "map_plan", "map_west",
          "map_xurong", "defeat_stamp", "xurong_think", "xurong_retreat", "fame", "chenliu",
          "yan_invite", "dongjun_map", "dongjun_win", "yuan_shi", "tide_in", "baoxin_warn", "baoxin_eye", "baoxin_plan",
          "liudai_fall", "no_master", "chengong", "chengong_q", "chengong_lobby", "welcome",
          "shouzhang_map", "scout_fail", "fear", "armor_up", "ambush", "baoxin_die", "chase_jibei", "baoxin_right",
          "yuan_geo", "yuan_geo2", "revolt", "mech_title", "mech1", "mech2", "mech3", "analogy2", "analogy2b", "thesis2"]:
    SHOT[v] = "map"
SHOT["battle_bian"] = "battle"
for v in ["tide_flash", "transform", "transform2", "identity"]:
    SHOT[v] = "tide"
for v in ["ledger", "num_jump"]:
    SHOT[v] = "ledger"
for v in ["question", "thesis"]:
    SHOT[v] = "question"
for v in ["title_bian"]:
    SHOT[v] = "title"
for v in ["capital", "analogy1", "analogy1b", "wait"]:
    SHOT[v] = "network"
for v in ["zhoumu"]:
    SHOT[v] = "zhoumu"
for v in ["why3", "why_a", "why_b", "why_c", "why_c2", "analogy3", "analogy3b"]:
    SHOT[v] = "why"
for v in ["card3_intro", "card3_a", "card3_b", "card3_c"]:
    SHOT[v] = "card3"
SHOT["wood_statue"] = "statue"
for v in ["view_title", "dialog1", "dialog2", "cao_ans", "cao_quote", "fuzi"]:
    SHOT[v] = "dialog"
for v in ["practice", "borrow"]:
    SHOT[v] = "borrow"
for v in ["qing_leave", "qing_leave2"]:
    SHOT[v] = "leave"
for v in ["novel_title", "novel_vs", "novel_chengong", "novel_base"]:
    SHOT[v] = "novel"
for v in ["end_q", "end_a", "end_b", "end_c", "end_quote", "next"]:
    SHOT[v] = "end"

SECTION = {"hook": "", "bian": "一 · 汴水：输了仗，赢了名声", "yan": "二 · 兖州：地盘是被请来的", "qing": "三 · 青州兵：军队是收编来的",
           "view": "四 · 押地理，还是押人", "novel": "五 · 演义与史书", "end": ""}


class Ctx:
    def __init__(s, lines, T):
        s.L = lines; s.T = T
        s.ev = {d["v"]: d for d in lines}
        s.cur = lines[0]
        for d in lines:
            if d["start"] <= T + 1e-6:
                s.cur = d
        s.i = lines.index(s.cur)

    def since(s, v):
        return s.T - s.ev[v]["start"] if v in s.ev else -1e9

    def dur(s, v):
        return s.ev[v]["dur"]

    def until(s, v):
        """距离 v 开始还有多久（负数表示已开始）"""
        return s.ev[v]["start"] - s.T

    def win(s, v0, v1=None, d=0.5, lag=0.0):
        """从 v0 开始（+lag 秒）到 v1 开始可见；v1 为 None 则到 v0 所在镜头结束"""
        a = s.since(v0) - lag
        if a < -d:
            return 0.0
        if v1 is None:
            d0 = s.ev[v0]; i0 = s.L.index(d0)
            b = (s.L[i0 + 1]["start"] if i0 + 1 < len(s.L) else 1e9) - s.T
        else:
            b = s.until(v1)
        return ease(a / d + 1) * ease(b / d) if a < 0 else ease(min(1.0, a / d + 1)) * ease(b / d)

    def shot_end(s, v):
        d = s.ev[v]; i = s.L.index(d); sh = SHOT.get(v)
        while i + 1 < len(s.L) and SHOT.get(s.L[i + 1]["v"]) == sh:
            i += 1
        return s.L[i + 1]["start"] if i + 1 < len(s.L) else 1e9


def shot_start(ctx, line):
    i = ctx.L.index(line); sh = SHOT.get(line["v"])
    while i > 0 and SHOT.get(ctx.L[i - 1]["v"]) == sh:
        i -= 1
    return ctx.L[i]["start"]


# ================================================================ 夜战汴水
_horse = None


def horse_path():
    """侧面奔马剪影（手绘关键点）"""
    p = skia.Path()
    pts = [(0, 0), (30, -10), (70, -14), (120, -12), (150, -20), (170, -45), (182, -70), (192, -78), (205, -74), (214, -60),
           (210, -52), (196, -50), (188, -36), (180, -14), (176, 6), (190, 30), (205, 62), (198, 66), (180, 36), (160, 18),
           (140, 22), (126, 50), (138, 78), (130, 80), (112, 50), (100, 26), (60, 26), (40, 40), (20, 70), (12, 72), (22, 40),
           (10, 24), (-10, 40), (-40, 64), (-46, 60), (-22, 34), (-14, 14), (-30, 10), (-48, 22), (-60, 20), (-38, 4), (-14, -2)]
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def draw_horse(c, x, y, s, a, t, col=(8, 8, 8), rim=GOLD, flip=False, bob=True):
    global _horse
    if _horse is None:
        _horse = horse_path()
    c.save(); c.translate(x, y + (math.sin(t * 9) * 4 if bob else 0)); c.scale(-s if flip else s, s)
    c.drawPath(_horse, paint(rim, 0.55 * a, blur=6))
    c.drawPath(_horse, paint(col, a))
    c.restore()


def sh_night(c, ctx, ts):
    T = ctx.T
    # 夜空
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(6, 8, 14), C(22, 18, 22), C(48, 26, 16), C(10, 10, 12)], [0, 0.34, 0.5, 0.75])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    c.save(); c.translate(0, -190)
    # 远处火光
    for i, (x, y, r) in enumerate([(160, 980, 300), (520, 1010, 380), (900, 970, 320)]):
        fire_glow(c, x, y, r, T, 0.9, seed=i)
    smoke(c, 540, 960, 1000, T, 0.8, n=12, seed=3)
    # 对岸山影
    pa = skia.Path(); pa.moveTo(0, 1040)
    for i in range(0, 1100, 60):
        pa.lineTo(i, 1010 - 40 * math.sin(i * 0.011) - 25 * math.sin(i * 0.031))
    pa.lineTo(W, 1100); pa.lineTo(0, 1100); pa.close()
    c.drawPath(pa, paint((10, 9, 10), 1))
    # 河
    sh = skia.GradientShader.MakeLinear([(0, 1090), (0, 1330)], [C(30, 26, 30), C(60, 40, 28), C(16, 16, 22)], [0, 0.4, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeLTRB(0, 1090, W, 1330), p)
    for k in range(14):
        yy = 1100 + k * 17
        off = (T * (20 + k * 3)) % 140
        pe = paint((255, 170, 90), 0.20 * (1 - k / 14), stroke=2)
        pe.setPathEffect(skia.DashPathEffect.Make([60 + k * 4, 80], off))
        c.drawLine(0, yy, W, yy, pe)
    c.drawRect(skia.Rect.MakeLTRB(0, 1330, W, H + 200), paint((8, 8, 10)))
    embers(c, 540, 1060, 1000, T, 0.9, n=60, seed=1, rise=420)
    # 近处兵：董卓军冷蓝灰从右压来，曹军黑金在左
    a_cl = 1.0
    r = np.random.default_rng(7)
    n = 260
    bx = r.uniform(560, 1150, n); by = r.uniform(1020, 1090, n)
    bx = bx - (ts * 18) % 60
    draw_pts(c, bx, by - np.abs(np.sin(T * 6 + bx)) * 3, DONG, a_cl * 0.9, size=4)
    for i in range(0, n, 3):
        c.drawLine(float(bx[i]), float(by[i]), float(bx[i]) - 12, float(by[i]) - 40, paint(DONG, 0.6, stroke=1.6))
    cx = r.uniform(-60, 420, 140); cy = r.uniform(1030, 1095, 140)
    draw_pts(c, cx, cy, (40, 34, 26), 1, size=4.5)
    draw_pts(c, cx, cy, GOLD, 0.25, size=7)
    v = ctx.cur["v"]
    # 箭雨
    arrow_rain(c, T, 0.85 if v != "river_escape" else 0.35, n=80, seed=5, area=(0, 120, W, 1150))
    # 旗
    s0 = ctx.since("bian_night")
    hit = 1.6
    tilt = -0.0 if s0 < hit else -0.35 * eout((s0 - hit) / 0.5)
    if v == "bian_night":
        flag(c, 300, 1040, "曹", CAO, GOLD, 1.25, 1, T, tilt=tilt)
        flag(c, 780, 1030, "徐", DONG_D, DONG, 1.15, 1, T + 1)
        if s0 > hit - 0.25:
            flash(c, 0.35 * (1 - clamp((s0 - hit) / 0.35)), (255, 120, 80))
        draw_horse(c, 470, 1075, 1.5, 1, T, bob=False)
    elif v == "caohong":
        s = ctx.since("caohong")
        flag(c, 260, 1040, "曹", CAO, GOLD, 1.1, 1, T, tilt=-0.35)
        hx = lerp(880, 520, eout(s / 3.0))
        draw_horse(c, hx, 1075, 1.6, 1, T, flip=True)
        text(c, "曹洪 让马", hx - 120, 930, "serifB", 46, GOLD_L, ease(s / 0.6), shadow=0.9, stroke=4)
    elif v == "river_escape":
        s = ctx.since("river_escape")
        bx_ = lerp(120, 900, ease(s / max(ctx.dur("river_escape"), 1)))
        pa = skia.Path(); pa.moveTo(bx_ - 70, 1190); pa.lineTo(bx_ + 70, 1190); pa.lineTo(bx_ + 50, 1215); pa.lineTo(bx_ - 50, 1215); pa.close()
        c.drawPath(pa, paint((6, 6, 6))); c.drawPath(pa, paint(GOLD, 0.5, stroke=2))
        for dx in (-18, 18):
            c.drawLine(bx_ + dx, 1190, bx_ + dx, 1150, paint((6, 6, 6), 1, stroke=10))
            c.drawCircle(bx_ + dx, 1140, 9, paint((6, 6, 6)))
        text(c, "夜渡汴水", 540, 610, "serifB", 64, GOLD_L, ease(s / 0.6), glow=(GOLD, 14, 0.4))
    c.restore()
    # 大标题
    if v == "bian_night":
        a = 1.0
        text(c, "汴水", 540, 470, "serifB", 210, GOLD_L, a, glow=(GOLD, 26, 0.55), shadow=0.8, spacing=30)
        text(c, "公元190年 · 荥阳", 540, 570, "serif", 44, (230, 210, 170), a * 0.95, shadow=0.9)


# ================================================================ 方阵闪回
def sh_phalanx(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(8, 8, 10))
    sh = skia.GradientShader.MakeRadial((540, 900), 900, [C(60, 44, 20), C(8, 8, 10)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    rows, cols = 34, 26
    k = eout(ts / 1.6)
    for rr in range(rows):
        yy = 700 + rr * 18 * (0.55 + rr / rows)
        sc = 0.5 + rr / rows
        n = cols
        xs = np.linspace(540 - 300 * sc, 540 + 300 * sc, n)
        ys = np.full(n, yy) + np.sin(T * 4 + xs * 0.05) * 2
        draw_pts(c, xs, ys, GOLD, 0.35 * k, size=8 * sc)
        draw_pts(c, xs, ys, (16, 14, 12), k, size=5 * sc)
    for i in range(7):
        x = 540 + (i - 3) * 130
        flag(c, x, 700, "青" if i == 3 else "曹", CAO, GOLD, 0.8, k, T + i)
    text(c, "三年后", 540, 420, "serifB", 120, GOLD_L, ease(ts / 0.5), glow=(GOLD, 20, 0.5), spacing=14)
    text(c, "从几十万人里挑出来的军队", 540, 520, "serif", 48, WHITE, ease((ts - 0.4) / 0.5), shadow=0.9)


# ================================================================ 酸枣酒宴
def sh_feast(c, ctx, ts):
    T = ctx.T
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(8, 10, 18), C(20, 16, 22), C(12, 10, 10)], [0, 0.6, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    cam = ts * 40
    # 帐篷三层视差
    for layer, (yb, sz, a_, n) in enumerate([(820, 0.6, 0.55, 9), (980, 0.85, 0.8, 7), (1180, 1.2, 1.0, 5)]):
        for i in range(n + 2):
            x = (i * (1200 / n) - cam * (0.4 + layer * 0.4)) % 1400 - 160
            w_ = 230 * sz; h_ = 170 * sz
            pa = skia.Path(); pa.moveTo(x - w_ / 2, yb); pa.lineTo(x, yb - h_); pa.lineTo(x + w_ / 2, yb); pa.close()
            c.drawPath(pa, paint((24, 20, 18), a_))
            # 帐内灯火
            fl = 0.8 + 0.2 * math.sin(T * 7 + i * 3 + layer)
            sh2 = skia.GradientShader.MakeRadial((x, yb - h_ * 0.25), w_ * 0.5, [C(255, 190, 100, int(220 * fl * a_)), C(255, 140, 60, 0)])
            p2 = skia.Paint(); p2.setShader(sh2); p2.setBlendMode(skia.BlendMode.kScreen)
            c.drawCircle(x, yb - h_ * 0.25, w_ * 0.5, p2)
            pd = skia.Path(); pd.moveTo(x - w_ * 0.12, yb); pd.lineTo(x, yb - h_ * 0.42); pd.lineTo(x + w_ * 0.12, yb); pd.close()
            c.drawPath(pd, paint((255, 200, 120), 0.85 * a_ * fl))
            # 杯影
            if layer == 2:
                for k in range(3):
                    cx_ = x - 50 + k * 50
                    c.drawCircle(cx_, yb + 26 + math.sin(T * 3 + k + i) * 4, 9, paint((255, 200, 120), 0.6))
    c.drawRect(skia.Rect.MakeLTRB(0, 1180, W, H), paint((10, 9, 9)))
    text(c, "酸枣大营", 540, 430, "serifB", 96, GOLD_L, ease(ts / 0.5), glow=(GOLD, 16, 0.4), spacing=10)
    text(c, "关东联军 · 十余万", 540, 520, "serif", 42, (230, 215, 190), ease((ts - 0.3) / 0.5), shadow=0.9)
    v = ctx.cur["v"]
    if v == "rebuke":
        s = ctx.since("rebuke")
        # 一处整兵的黑金营帐被点亮
        sh3 = skia.GradientShader.MakeRadial((540, 980), 260, [C(222, 180, 92, 120), C(0, 0, 0, 0)])
        p3 = skia.Paint(); p3.setShader(sh3); c.drawCircle(540, 980, 260, p3)
        flag(c, 540, 1020, "曹", CAO, GOLD, 1.0, ease(s / 0.5), T)


# ================================================================ 地图（主推演）
CAM = {
    "west_arrow": (113.85, 35.0, 2.9, 9), "yangzhou": (115.6, 33.2, 9.0, 7),
    "yan_invite": (116.0, 35.6, 4.6, 9),
    "chenliu": (114.4, 34.9, 3.6, 9), "map_east": (113.2, 34.6, 7.6, 7), "map_cao": (113.9, 34.9, 4.2, 9),
    "map_luoyang_fire": (111.4, 34.5, 6.0, 7), "map_cao_speech": (113.6, 34.9, 4.6, 9), "map_plan": (112.6, 34.4, 6.4, 7),
    "map_west": (113.8, 35.0, 3.4, 9), "map_xurong": (113.6, 34.9, 2.4, 9), "defeat_stamp": (113.6, 34.9, 2.6, 9),
    "xurong_think": (113.8, 34.95, 2.8, 9), "xurong_retreat": (113.3, 34.85, 3.4, 9), "fame": (115.2, 35.2, 7.4, 7),
    "dongjun_map": (115.0, 35.9, 3.6, 9), "dongjun_win": (115.1, 35.85, 3.0, 9), "yuan_shi": (114.9, 36.1, 3.6, 9),
    "tide_in": (116.6, 35.9, 4.4, 9), "baoxin_warn": (116.3, 35.85, 3.6, 9), "baoxin_eye": (116.75, 35.75, 2.4, 9),
    "baoxin_plan": (116.4, 35.7, 3.4, 9), "liudai_fall": (116.4, 35.5, 3.2, 9), "no_master": (113.5, 35.2, 9.0, 7),
    "chengong": (115.4, 35.9, 3.2, 9), "chengong_q": (115.6, 35.7, 3.6, 9), "chengong_lobby": (115.8, 35.5, 3.6, 9),
    "welcome": (115.8, 35.7, 3.8, 9), "mech_title": (115.8, 35.7, 4.2, 9),
    "shouzhang_map": (116.0, 35.8, 3.0, 9), "scout_fail": (116.25, 35.85, 2.0, 9), "fear": (116.15, 35.82, 1.7, 9),
    "armor_up": (116.15, 35.82, 1.8, 9), "ambush": (116.3, 35.95, 2.6, 9), "baoxin_die": (116.3, 35.95, 2.4, 9),
    "chase_jibei": (116.45, 36.15, 2.8, 9), "baoxin_right": (116.5, 36.2, 3.0, 9),
    "yuan_geo": (115.6, 37.6, 10.5, 7), "yuan_geo2": (115.6, 37.6, 10.0, 7), "revolt": (115.9, 35.7, 4.0, 9),
}


def cam_for(ctx):
    """当前镜头：从上一个有 CAM 的地图句插值到本句"""
    cur = ctx.cur
    i = ctx.L.index(cur)
    j = i
    while j >= 0 and ctx.L[j]["v"] not in CAM:
        j -= 1
    if j < 0:
        return Cam(115, 35.5, 6), 7
    key = ctx.L[j]["v"]
    lon, lat, span, z = CAM[key]
    tgt = Cam(lon, lat, span)
    k = j - 1
    while k >= 0 and ctx.L[k]["v"] not in CAM:
        k -= 1
    if k >= 0 and SHOT.get(ctx.L[k]["v"]) == "map" and shot_start(ctx, ctx.L[k]) == shot_start(ctx, ctx.L[j]):
        lon0, lat0, sp0, z0 = CAM[ctx.L[k]["v"]]
        u = (ctx.T - ctx.L[j]["start"]) / 1.6
        cam = Cam.lerp(Cam(lon0, lat0, sp0), tgt, clamp(u))
    else:
        # 新镜头：缓慢推近
        u = ctx.T - ctx.L[j]["start"]
        cam = Cam(lon, lat, span * (1.06 - 0.06 * ease(u / 4)))
    zz = 9 if cam.span < 5.0 else 7
    return cam, zz


def tide_particles(n, seed):
    r = np.random.default_rng(seed)
    return dict(u=r.uniform(0, 1, n), off=r.normal(0, 1, n), ph=r.uniform(0, 6.28, n), sp=r.uniform(0.7, 1.3, n), fam=r.uniform(0, 1, n) < 0.55)


_TP = tide_particles(5200, 11)
TIDE_PATH = [(118.6, 36.6), (117.9, 36.2), (117.2, 35.8), (116.7, 35.55), (116.45, 35.75), (116.2, 35.9)]


def draw_tide(c, cam, T, a, prog, front=None, col=HJ, spread=0.55, n=None, compress=1.0, center=None):
    """黄巾潮：沿 TIDE_PATH 推进，prog 为前锋位置 0..1"""
    if a <= 0.01:
        return
    P = _TP; m = len(P["u"]) if n is None else n
    pts = smooth(TIDE_PATH, 8)
    L = len(pts) - 1
    u = np.clip(P["u"][:m] * prog, 0, 1)
    idx = np.clip((u * L).astype(int), 0, L - 1); fr = u * L - idx
    pa = np.array(pts)
    lon = pa[idx, 0] * (1 - fr) + pa[idx + 1, 0] * fr
    lat = pa[idx, 1] * (1 - fr) + pa[idx + 1, 1] * fr
    lon = lon + P["off"][:m] * spread * 0.6 * compress + np.sin(T * 0.8 + P["ph"][:m]) * 0.02
    lat = lat + np.roll(P["off"][:m], 7) * spread * 0.45 * compress + np.cos(T * 0.7 + P["ph"][:m]) * 0.02
    if center is not None:
        k = center[2]
        lon = lon * (1 - k) + (center[0] + P["off"][:m] * 0.18) * k
        lat = lat * (1 - k) + (center[1] + np.roll(P["off"][:m], 7) * 0.12) * k
    xs = np.empty(m); ys = np.empty(m)
    S = cam.S; m0 = merc(cam.lon, cam.lat)
    mx = (lon + 180) / 360
    my = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2
    xs = cam.ax + (mx - m0[0]) * S; ys = cam.ay + (my - m0[1]) * S
    fam = P["fam"][:m]
    draw_pts(c, xs[~fam], ys[~fam], col, a * 0.25, size=9, glow=False) if False else None
    c.drawPoints(skia.Canvas.kPoints_PointMode, [skia.Point(float(px_), float(py_)) for px_, py_ in zip(xs[~fam][::2], ys[~fam][::2])], paint(HJ_L, a * 0.35, stroke=10, blur=6))
    draw_pts(c, xs[~fam], ys[~fam], col, a * 0.95, size=4.2)
    draw_pts(c, xs[fam], ys[fam], mixc(col, (230, 200, 150), 0.35), a * 0.6, size=2.2)
    return xs, ys


def sh_map(c, ctx, ts):
    T = ctx.T
    cam, z = cam_for(ctx)
    c.drawColor(C(10, 10, 10))
    base(7).draw(c, cam)
    if z == 9:
        b9a = clamp((5.0 - cam.span) / 0.6)
        base(9).draw(c, cam, b9a)
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.18))
    draw_rivers(c, cam, 0.9, bian=1.0 if ctx.cur["scene"] in ("hook", "bian") else 0.0)
    w, sn = ctx.win, ctx.since
    S = cam.pxdeg() / 120
    # 兖州州界
    ya = max(w("yan_invite"), w("dongjun_map", "mech_title"), w("shouzhang_map", "baoxin_right"), w("revolt"), w("mech_title", "thesis2"), w("analogy2", "thesis2") * 0, w("thesis2"))
    if ya > 0:
        own = 0.0
        if ctx.cur["scene"] == "qing" or ctx.cur["v"] in ("mech_title", "mech1", "mech2", "mech3", "analogy2", "analogy2b", "thesis2"):
            own = 1.0
        elif sn("welcome") > 0:
            own = ease((sn("welcome") - 2.5) / 1.5)
        dark = 0.0
        if sn("tide_in") > 0 and sn("welcome") < 2.5:
            dark = ease(sn("tide_in") / 2)
        fillc = mixc(mixc((120, 40, 30), (60, 30, 20), dark), (40, 34, 22), own)
        region(c, cam, YAN_POLY, fillc + (0.22 + 0.1 * own,), ya, edge=mixc(GOLD, GOLD_L, own) + (0.9,), width=3 + 2 * own)
        cx, cy = cam.p(116.4, 34.82)
        text(c, "兖州", cx, cy, "serifB", 54, GOLD_L, ya * 0.8, shadow=0.9, stroke=5, stroke_col=(10, 8, 6))
    qa = max(w("tide_in", "liudai_fall"), w("yan_invite"))
    if qa > 0:
        region(c, cam, QING_POLY, (120, 80, 40, 0.18), qa, edge=(196, 128, 60, 0.7))
        cx, cy = cam.p(118.5, 36.9)
        text(c, "青州", cx, cy, "serifB", 50, HJ_L, qa * 0.9, shadow=0.9, stroke=5, stroke_col=(10, 8, 6))
    # ---- 城名：按需要
    def cities(names, a, size=32):
        for nm in names:
            city(c, cam, nm, a, size=size)
    big = ctx.cur["scene"] in ("hook", "bian") or ctx.cur["v"] in ("no_master", "yuan_geo", "yuan_geo2")
    if big:
        cities(["洛阳", "长安", "荥阳", "酸枣"], 0.9)
    else:
        cities(["濮阳", "寿张", "济北", "昌邑", "鄄城"], 0.85, 30)

    # ================= 钩子：西进一线 / 扬州募兵 / 兖州来请
    a = w("west_arrow")
    if a > 0:
        s = sn("west_arrow")
        for i in range(12):
            ang = i / 12 * 6.28
            x, y = cam.p(114.3 + 0.26 * math.cos(ang), 35.22 + 0.16 * math.sin(ang))
            flag(c, x, y, "张刘桥袁　　　　　　　　"[i], (150, 140, 120), (200, 190, 170), 0.5, a, T + i)
        lls = [PL["酸枣"], (113.9, 35.05), PL["荥阳"]]
        map_arrow(c, cam, lls, eout(s / 1.6), width=24 * S ** 0.5, a=a, t=T)
        if s > 1.6:
            map_arrow(c, cam, [(112.5, 35.3), (113.0, 34.95), (113.5, 34.82)], eout((s - 1.6) / 0.8), col=DONG_D, edge=DONG, width=38 * S ** 0.5, a=a, t=T)
        if s > 2.4:
            x, y = cam.p(*PL["荥阳"])
            stamp(c, "败", x + 40, y - 120, 120, a, s - 2.4)
        x, y = cam.p(*PL["酸枣"])
        text(c, "十余万 · 按兵不动", x + 30, y + 120, "sansB", 34, WHITE, a, shadow=0.9, stroke=4)
    a = w("yangzhou")
    if a > 0:
        s = sn("yangzhou")
        cities(["历阳", "龙亢", "谯"], a)
        r = np.random.default_rng(3)
        n = 400
        x0, y0 = cam.p(*PL["龙亢"])
        ox = r.normal(0, 60, n); oy = r.normal(0, 40, n)
        keep = r.uniform(0, 1, n) < 0.125
        k = eout((s - 1.5) / 2.0)
        dx = ox * (1 + 4 * k * ~keep); dy = oy * (1 + 4 * k * ~keep) + 300 * k * ~keep
        al = np.where(keep, 1.0, 1 - k)
        draw_pts(c, x0 + dx[keep], y0 + dy[keep], GOLD, a, size=5)
        draw_pts(c, x0 + dx[~keep], y0 + dy[~keep], (150, 140, 120), a * (1 - k), size=4)
        num = int(lerp(4000, 500, k))
        text(c, f"{num}+", x0, y0 - 140, "serifB", 92, GOLD_L if k > 0.9 else WHITE, a, glow=(GOLD, 14, 0.4), stroke=5)
        text(c, "扬州募兵 → 龙亢兵变", x0, y0 - 60, "sansB", 34, WHITE, a, stroke=4)
    a = w("yan_invite")
    if a > 0:
        s = sn("yan_invite")
        x, y = cam.p(*PL["昌邑"])
        flag(c, x, y, "刘", (150, 60, 50), (220, 160, 140), 0.9, a, T, tilt=-1.4 * eout((s - 0.6) / 0.8))
        tide_a = a
        draw_tide(c, cam, T, tide_a, 0.9)
        for i in range(3):
            p0 = cam.p(116.3 + i * 0.2, 35.3 + i * 0.12); p1 = cam.p(*PL["濮阳"])
            k = eout((s - 1.5 - i * 0.2) / 2.2)
            flag(c, lerp(p0[0], p1[0] + 60 + i * 40, k), lerp(p0[1], p1[1] + 40, k), "迎", YAN, (120, 110, 90), 0.6, a * clamp((s - 1.5) / 0.4), T + i)
        x, y = cam.p(*PL["濮阳"])
        flag(c, x, y, "曹", CAO, GOLD, 1.0, a, T)
    # ================= 汴水之败
    a = w("chenliu", "map_east")
    if a > 0:
        s = sn("chenliu")
        x, y = cam.p(*PL["陈留"])
        city(c, cam, "陈留", a, size=40)
        flag(c, x, y - 10, "曹", CAO, GOLD, 1.2 * eout(s / 0.8), a, T)
        ar = Army(500, 5, "blob", 220, 120)
        px, py = ar.pts(x + 40, y + 70, T, 1.5, eout(s / 1.5))
        draw_pts(c, px, py, GOLD, a * 0.5, 6); draw_pts(c, px, py, (20, 18, 14), a, 3.5)
        text(c, "散家财 · 合义兵", x, y + 190, "serifB", 46, GOLD_L, a * ease((s - 0.6) / 0.5), stroke=5)
    a = max(w("map_east", "map_west"), 0)
    if a > 0:
        s = sn("map_east")
        cities(["河内", "邺", "宛", "阳翟", "陈留"], a, 28)
        flags = [("河内", "袁", YUAN), ("邺", "韩", (150, 140, 120)), ("宛", "术", YUAN), ("阳翟", "孔", (150, 140, 120))]
        for i, (nm, ch, col) in enumerate(flags):
            x, y = cam.p(*PL[nm]); flag(c, x, y, ch, col, (230, 220, 190), 0.6, a * ease((s - i * 0.25) / 0.4), T + i)
        for i in range(8):
            ang = i / 8 * 6.28
            x, y = cam.p(114.22 + 0.32 * math.cos(ang), 35.18 + 0.2 * math.sin(ang))
            flag(c, x, y, "张刘桥袁　　　　"[i], (150, 140, 120), (200, 190, 170), 0.5, a * ease((s - 1 - i * 0.1) / 0.4), T + i)
        x, y = cam.p(*PL["洛阳"])
        flag(c, x, y, "董", DONG_D, DONG, 1.0, a, T)
        if sn("map_east") > 0:
            x, y = cam.p(*PL["河内"])
            text(c, "盟主 袁绍", x, y + 60, "sansB", 30, YUAN, a, stroke=4)
    a = w("map_cao", "map_xurong")
    if a > 0:
        x, y = cam.p(114.0, 35.12)
        flag(c, x, y, "曹", CAO, GOLD, 0.85, a, T, txt="行奋武将军 · 数千人")
        c.drawCircle(x, y - 60, 90 + 8 * math.sin(T * 4), paint(GOLD, 0.6 * a, stroke=3))
    a = w("map_luoyang_fire", "map_west")
    if a > 0:
        s = sn("map_luoyang_fire")
        x, y = cam.p(*PL["洛阳"])
        fire_glow(c, x, y, 160, T, a); embers(c, x, y, 120, T, a, 30, 2)
        map_arrow(c, cam, [PL["洛阳"], (110.8, 34.7), PL["长安"]], eout(s / 2.0), col=DONG_D, edge=DONG, width=34 * S ** 0.5, a=a, t=T)
        text(c, "迁都长安 · 焚洛阳", x, y + 80, "sansB", 34, WHITE, a * ease((s - 0.8) / 0.5), stroke=4)
    a = w("map_plan", "map_west")
    if a > 0:
        s = sn("map_plan")
        plans = [[PL["河内"], PL["孟津"]], [PL["酸枣"], (113.8, 35.0), PL["敖仓"], PL["成皋"]], [PL["宛"], (111.6, 33.5), PL["武关"]]]
        for i, pl in enumerate(plans):
            map_arrow(c, cam, pl, eout((s - i * 0.7) / 1.2), col=(60, 50, 30), edge=GOLD_L, width=20 * S ** 0.5, a=a * 0.85, t=T, dashed=True)
        cities(["孟津", "成皋", "武关"], a, 26)
        if s > ctx.dur("map_plan") - 2.0:
            x, y = cam.p(113.0, 34.2)
            stamp(c, "弃", x, y, 120, a, s - (ctx.dur("map_plan") - 2.0), col=(170, 160, 150))
    a = w("map_west", "map_xurong")
    if a > 0:
        s = sn("map_west")
        map_arrow(c, cam, [PL["酸枣"], (113.9, 35.02), PL["荥阳"]], eout(s / 2.2), width=30 * S ** 0.5, a=a, t=T)
        x, y = cam.p(*PL["酸枣"])
        for i in range(6):
            flag(c, x + (i - 3) * 50, y + 20, "　", (150, 140, 120), (200, 190, 170), 0.45, a, T + i)
        text(c, "只有他西进", x, y + 110, "serifB", 40, GOLD_L, a, stroke=5)
    a = max(w("map_xurong", "xurong_think"), 0)
    if a > 0:
        s = sn("map_xurong")
        x, y = cam.p(113.3, 34.8)
        flag(c, x, y, "徐", DONG_D, DONG, 1.0, a, T, txt="董卓部将 徐荣")
        x2, y2 = cam.p(113.62, 34.84)
        flag(c, x2, y2, "曹", CAO, GOLD, 0.9, a, T)
        text(c, "汴水", *cam.p(113.7, 34.72), "serifB", 40, (170, 210, 220), a, stroke=4)
        if ctx.cur["v"] == "defeat_stamp":
            stamp(c, "败", 540, 760, 260, 1, sn("defeat_stamp"))
    a = w("xurong_think", "fame")
    if a > 0:
        s = sn("xurong_think")
        x, y = cam.p(113.3, 34.8)
        flag(c, x, y, "徐", DONG_D, DONG, 1.0, a, T)
        xs, ys = cam.p(*PL["酸枣"])
        pe = paint(DONG, 0.8 * a, stroke=3); pe.setPathEffect(skia.DashPathEffect.Make([12, 10], -T * 30))
        c.drawLine(x, y - 60, xs, ys, pe)
        text(c, "？", (x + xs) / 2, (y + ys) / 2 - 20, "serifB", 90, DONG, a * (0.6 + 0.4 * math.sin(T * 5)), stroke=4)
        if sn("xurong_retreat") > 0:
            s2 = sn("xurong_retreat")
            map_arrow(c, cam, [(113.25, 34.82), (112.9, 34.78), (112.62, 34.74)], eout(s2 / 1.5), col=DONG_D, edge=DONG, width=34 * S ** 0.5, a=a, t=T)
            text(c, "徐荣 引兵还", *cam.p(112.9, 34.55), "sansB", 34, WHITE, a * ease(s2 / 0.5), stroke=4)
    a = w("fame")
    if a > 0:
        s = sn("fame")
        x, y = cam.p(*PL["荥阳"])
        for k in range(4):
            u = ((s * 0.35 + k * 0.25) % 1.0)
            c.drawCircle(x, y, 40 + u * 900, paint(GOLD, a * 0.55 * (1 - u), stroke=5))
        nodes = ["陈留", "濮阳", "昌邑", "鄄城", "邺", "阳翟", "谯", "许", "任城", "济北"]
        for i, nm in enumerate(nodes):
            xx, yy = cam.p(*PL[nm])
            dd = math.dist((x, y), (xx, yy))
            on = ease((s * 0.35 * 900 + 40 - dd) / 80)
            c.drawCircle(xx, yy, 16, paint(GOLD_L, a * on * 0.6, blur=8)); c.drawCircle(xx, yy, 7, paint(GOLD_L, a * on))
        text(c, "名声", 540, 420, "serifB", 150, GOLD_L, a, glow=(GOLD, 24, 0.5), spacing=20)
    # ================= 兖州
    a = w("dongjun_map", "tide_in")
    if a > 0:
        s = sn("dongjun_map")
        city(c, cam, "东武阳", a, 28)
        x, y = cam.p(*PL["黑山"])
        for i in range(3):
            map_arrow(c, cam, [(113.9 + i * 0.05, 36.3 - i * 0.18), (114.5, 36.0 - i * 0.12), (114.95, 35.8 - i * 0.05)], eout((s - i * 0.3) / 1.8), col=DONG_D, edge=DONG, width=26 * S ** 0.5, a=a * (1 - ease(sn("dongjun_win") / 1.5)), t=T)
        text(c, "黑山军 十余万", x - 20, y - 20, "sansB", 34, DONG, a * (1 - ease(sn("dongjun_win") / 1.5)), stroke=4)
        if sn("dongjun_win") > 0:
            s2 = sn("dongjun_win")
            map_arrow(c, cam, [(114.2, 35.3), (114.6, 35.55), PL["濮阳"]], eout(s2 / 1.4), width=34 * S ** 0.5, a=a, t=T)
            xx, yy = cam.p(*PL["濮阳"])
            flag(c, xx + 70, yy, "白", DONG_D, DONG, 0.8, a, T, tilt=-1.3 * eout((s2 - 1.4) / 0.6))
            flag(c, xx, yy, "曹", CAO, GOLD, 1.0, a * ease((s2 - 1.5) / 0.5), T, txt="东郡太守")
        if sn("yuan_shi") > 0:
            s3 = sn("yuan_shi")
            xa, ya_ = cam.p(*PL["邺"]); xb, yb = cam.p(*PL["濮阳"])
            city(c, cam, "邺", a, 30)
            flag(c, xa, ya_, "袁", YUAN, (240, 220, 160), 1.0, a, T)
            pe = paint(YUAN, a, stroke=6); pe.setPathEffect(skia.DashPathEffect.Make([18, 12], -T * 40))
            pp = cut([(xa, ya_ - 60), (xb + 10, yb - 60)], eout(s3 / 1.2))
            c.drawPath(path_from(pp), pe)
            text(c, "表荐", (xa + xb) / 2 + 40, (ya_ + yb) / 2 - 70, "serifB", 46, YUAN, a * ease((s3 - 0.8) / 0.4), stroke=5)
            text(c, "少年好友", xa, ya_ + 50, "sansB", 30, YUAN, a * ease((s3 - 1.2) / 0.4), stroke=4)
    a = w("tide_in", "chengong")
    if a > 0:
        s = sn("tide_in")
        prog = eout(s / 3.5)
        cities(["任城", "东平"], a, 28)
        draw_tide(c, cam, T, a, prog)
        if sn("baoxin_eye") > 0 and sn("liudai_fall") < 0:
            s2 = sn("baoxin_eye")
            k = ease(s2 / 0.6)
            # 放大：兵与家属
            c.drawCircle(540, 640, 230, paint((0, 0, 0), 0.6 * k))
            c.drawCircle(540, 640, 230, paint(HJ_L, 0.9 * k, stroke=3))
            r = np.random.default_rng(9)
            for i in range(40):
                ang = r.uniform(0, 6.28); rad = r.uniform(0, 190)
                xx = 540 + math.cos(ang) * rad; yy = 640 + math.sin(ang) * rad * 0.8
                if i % 3 == 0:
                    c.drawCircle(xx, yy, 9, paint(HJ_L, k)); c.drawLine(xx, yy + 8, xx, yy + 30, paint(HJ_L, k, stroke=5))
                    c.drawLine(xx + 10, yy - 20, xx + 10, yy + 34, paint((200, 190, 170), k, stroke=2))
                else:
                    c.drawCircle(xx, yy, 6, paint((230, 200, 150), 0.8 * k)); c.drawLine(xx, yy + 5, xx, yy + 18, paint((230, 200, 150), 0.8 * k, stroke=4))
            text(c, "兵 + 家属", 540, 330, "serifB", 64, HJ_L, k, stroke=5)
            text(c, "无辎重 · 靠抄掠", 540, 960, "sansB", 36, WHITE, k * ease((s2 - 1.2) / 0.5), stroke=4)
        if sn("baoxin_warn") > 0:
            xb, yb = cam.p(*PL["济北"])
            flag(c, xb, yb, "鲍", YAN, (110, 100, 80), 0.9, a, T, txt="济北相 鲍信")
        xl, yl = cam.p(*PL["昌邑"])
        fall = eout((sn("liudai_fall") - 0.4) / 0.7) if sn("liudai_fall") > 0 else 0
        flag(c, xl, yl, "刘", (150, 60, 50), (220, 160, 140), 0.9, a, T, tilt=-1.45 * fall, txt="兖州刺史 刘岱" if fall < 0.1 else None)
        if sn("baoxin_plan") > 0 and sn("liudai_fall") < 0:
            s3 = sn("baoxin_plan")
            for nm in ["昌邑", "鄄城", "济北", "濮阳"]:
                xx, yy = cam.p(*PL[nm])
                c.drawCircle(xx, yy, 46, paint(YAN, 0.9 * a * ease(s3 / 0.5), stroke=6))
            text(c, "固守 · 待其离散", 540, 420, "serifB", 64, YAN, a * ease(s3 / 0.5), stroke=5)
        if sn("liudai_fall") > 0:
            flash(c, 0.35 * (1 - clamp((sn("liudai_fall") - 0.8) / 0.4)) * (sn("liudai_fall") > 0.8), (255, 90, 60))
    a = w("no_master", "chengong")
    if a > 0:
        s = sn("no_master")
        xa, ya_ = cam.p(*PL["长安"]); xb, yb = cam.p(116.3, 35.6)
        pe = paint((200, 200, 200), 0.8 * a, stroke=4); pe.setPathEffect(skia.DashPathEffect.Make([16, 12], -T * 30))
        mid = ((xa + xb) / 2, (ya_ + yb) / 2 - 80)
        c.drawLine(xa, ya_, mid[0] - 40, mid[1] + 15, pe)
        c.drawLine(mid[0] + 40, mid[1] - 5, xb, yb, pe)
        text(c, "✕", mid[0], mid[1] + 30, "sansH", 90, RED, a * ease((s - 1) / 0.3), stroke=4)
        text(c, "王命断绝", mid[0], mid[1] - 70, "serifB", 56, WHITE, a * ease((s - 1.2) / 0.4), stroke=5)
        flag(c, xa, ya_, "李", DONG_D, DONG, 0.7, a, T, txt="董卓余党控制长安")
        text(c, "无主", xb, yb + 20, "serifB", 64, (220, 120, 100), a * ease((s - 0.4) / 0.4), stroke=5)
    a = w("chengong", "mech_title")
    if a > 0:
        s = sn("chengong")
        xd, yd = cam.p(*PL["濮阳"]); xz, yz = cam.p(*PL["昌邑"])
        draw_tide(c, cam, T, a * 0.7, 1.0)
        flag(c, xd, yd, "曹", CAO, GOLD, 1.0, a, T, txt="东郡太守" if sn("welcome") < 0 else None)
        # 陈宫白旗
        if sn("chengong_lobby") > 0:
            k = eout(sn("chengong_lobby") / 2.5)
            gx, gy = lerp(xd + 70, xz, k), lerp(yd + 20, yz, k)
        else:
            gx, gy = xd + 80, yd + 20
        if sn("welcome") > 0:
            gx, gy = xz, yz
        flag(c, gx, gy, "陈", YAN, (110, 100, 80), 0.75, a * ease(s / 0.5), T, txt="陈宫（东郡人）" if sn("chengong_lobby") < 0 else None)
        if sn("chengong_lobby") > 0:
            for i, nm in enumerate(["别驾", "治中"]):
                flag(c, xz + 60 + i * 60, yz + 30, nm[0], YAN, (110, 100, 80), 0.55, a * ease((sn("chengong_lobby") - 2.2 - i * 0.3) / 0.4), T + i)
        if sn("welcome") > 0:
            s2 = sn("welcome")
            xb, yb = cam.p(*PL["济北"])
            flag(c, xb, yb, "鲍", YAN, (110, 100, 80), 0.8, a, T)
            # 白旗走向东郡，再迎黑旗回来
            k1 = eout(s2 / 1.8); k2 = eout((s2 - 2.2) / 2.0)
            for i, (sx, sy) in enumerate([(xz, yz), (xb, yb), (xz + 60, yz + 30)]):
                px = lerp(sx, xd + 50 + i * 40, k1); py = lerp(sy, yd + 40, k1)
                px = lerp(px, xz - 60 + i * 50, k2); py = lerp(py, yz + 40, k2)
                flag(c, px, py, "迎", YAN, (110, 100, 80), 0.6, a, T + i)
            cx_ = lerp(xd, xz, k2); cy_ = lerp(yd, yz, k2)
            flag(c, cx_, cy_, "曹", CAO, GOLD, 1.15, a, T, txt="兖州牧" if k2 > 0.95 else None)
    a = max(w("mech_title", "analogy2"), 0)
    if a > 0:
        items = [("mech1", "①", "精英缺一个能打的人"), ("mech2", "②", "只有他在汴水真打过"), ("mech3", "③", "就在身边 · 有兵 · 有袁绍")]
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.45 * a))
        text(c, "被请来的三个环节", 540, 400, "serifB", 64, GOLD_L, a, glow=(GOLD, 14, 0.35))
        for i, (v, n_, s_) in enumerate(items):
            k = ease(sn(v) / 0.5) if sn(v) > -0.4 else 0
            y = 560 + i * 150
            rrect(c, 90, y - 70, W - 90, y + 50, 16, paint((12, 11, 10), 0.85 * a * k))
            rrect(c, 90, y - 70, W - 90, y + 50, 16, paint(GOLD, a * k * (0.9 if ctx.cur["v"] == v else 0.45), stroke=2.5))
            text(c, n_, 150, y + 10, "serifB", 60, GOLD_L, a * k, shadow=0)
            text(c, s_, 210, y + 4, "serifB", 46, WHITE, a * k, align="l", shadow=0)
    a = max(w("analogy2", "thesis2"), 0)
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.4 * a))
    a = w("thesis2")
    if a > 0:
        s = sn("thesis2")
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.4 * a))
        x, y = cam.p(116.2, 35.4)
        flag(c, x, y + 120, "曹", CAO, GOLD, 1.4, a, T)
        text(c, "地盘", 540, 430, "serifB", 90, WHITE, a, shadow=0.9)
        text(c, "是被请来的", 540, 560, "serifB", 110, GOLD_L, a * ease((s - 0.5) / 0.5), glow=(GOLD, 20, 0.5))
    # ================= 寿张之战
    a = w("shouzhang_map", "transform")
    if a > 0 and ctx.cur["scene"] == "qing":
        s = sn("shouzhang_map")
        cities(["东平"], a, 28)
        prog = 1.0
        center = None
        if sn("chase_jibei") > 0:
            k = eout(sn("chase_jibei") / 3.5)
            center = (PL["济北"][0] + 0.1, PL["济北"][1] + 0.05, k)
        tide = draw_tide(c, cam, T, a, prog, center=center, compress=1.0)
        xs_, ys_ = cam.p(*PL["寿张"])
        # 曹军
        ar = Army(420, 21, "blob", 170, 110)
        jit = 1.5
        if ctx.cur["v"] == "fear":
            jit = 7.0
        if ctx.cur["v"] == "armor_up":
            jit = lerp(7.0, 0.5, ease(sn("armor_up") / 2.5))
        cx_, cy_ = xs_ + 120, ys_ + 40
        if sn("chase_jibei") > 0:
            xj, yj = cam.p(*PL["济北"])
            k = eout(sn("chase_jibei") / 3.5)
            cx_, cy_ = lerp(cx_, xj - 120, k), lerp(cy_, yj + 120, k)
        px, py = ar.pts(cx_, cy_, T, jit)
        glow_a = 0.45
        if ctx.cur["v"] == "armor_up":
            glow_a = 0.45 + 0.5 * math.sin(clamp(sn("armor_up") / 2.5) * math.pi)
        draw_pts(c, px, py, GOLD, a * glow_a, 7); draw_pts(c, px, py, (22, 20, 16), a, 4)
        flag(c, cx_, cy_ - 40, "曹", CAO, GOLD, 0.9, a, T, txt="兖州牧" if ctx.cur["v"] == "shouzhang_map" else None)
        if sn("shouzhang_map") > 0 and sn("scout_fail") < 0:
            map_arrow(c, cam, [PL["昌邑"], (116.0, 35.45), (116.1, 35.75)], eout(s / 1.6), width=30, a=a, t=T)
        if ctx.cur["v"] == "scout_fail":
            s2 = sn("scout_fail")
            map_arrow(c, cam, [(116.15, 35.82), (116.35, 35.88), (116.5, 35.85)], eout(s2 / 1.2), width=24, a=a, t=T)
            if s2 > 1.4:
                xx, yy = cam.p(116.5, 35.85)
                flash(c, 0.25 * (1 - clamp((s2 - 1.4) / 0.4)), (255, 90, 60))
                text(c, "死者数百", xx, yy - 80, "serifB", 54, (230, 120, 100), ease((s2 - 1.6) / 0.4), stroke=5)
        if ctx.cur["v"] == "fear":
            text(c, "旧兵少 · 新兵不习练", 540, 420, "serifB", 58, (220, 200, 180), ease(sn("fear") / 0.5), stroke=5)
        if ctx.cur["v"] == "armor_up":
            text(c, "被甲婴胄 · 亲巡将士", 540, 420, "serifB", 58, GOLD_L, ease(sn("armor_up") / 0.5), glow=(GOLD, 14, 0.4), stroke=5)
        if ctx.cur["v"] == "ambush" or (sn("ambush") > 0 and sn("baoxin_die") < 0):
            s2 = sn("ambush")
            for i, (lo, la) in enumerate([(116.1, 36.15), (116.65, 36.1), (116.45, 35.6)]):
                xx, yy = cam.p(lo, la)
                k = ease((s2 - i * 0.4) / 0.5)
                ar2 = Army(120, 30 + i, "blob", 90, 60)
                qx, qy = ar2.pts(xx, yy, T, 1)
                draw_pts(c, qx, qy, GOLD, a * k * 0.5, 6); draw_pts(c, qx, qy, (20, 18, 14), a * k, 3.5)
                text(c, "伏", xx, yy - 50, "serifB", 44, GOLD_L, a * k, stroke=4)
            # 降路
            pe = paint(YAN, a * ease((s2 - 1.5) / 0.6), stroke=8); pe.setPathEffect(skia.DashPathEffect.Make([20, 14], -T * 60))
            p0 = cam.p(116.6, 35.95); p1 = cam.p(116.9, 36.4)
            c.drawLine(*p0, *p1, pe)
            text(c, "降路", p1[0] + 20, p1[1] - 10, "serifB", 46, YAN, a * ease((s2 - 1.8) / 0.5), stroke=5)
            # 日夜
            dn = (math.sin(T * 1.2) + 1) / 2
            c.drawRect(skia.Rect.MakeWH(W, H), paint((10, 20, 50), 0.18 * dn * a))
            text(c, "昼夜会战", 540, 420, "serifB", 58, WHITE, ease(s2 / 0.5) * a, stroke=5)
        if sn("baoxin_die") > 0 and sn("chase_jibei") < 0:
            s2 = sn("baoxin_die")
            xb, yb = cam.p(116.45, 35.95)
            flag(c, xb, yb, "鲍", YAN, (110, 100, 80), 0.9, a, T, tilt=-1.45 * eout((s2 - 0.5) / 0.9))
            text(c, "鲍信战死", xb, yb - 170, "serifB", 54, YAN, a * ease((s2 - 0.9) / 0.5), stroke=5)
        if sn("chase_jibei") > 0:
            s2 = sn("chase_jibei")
            map_arrow(c, cam, [(116.15, 35.85), (116.4, 36.05), (116.62, 36.32)], eout(s2 / 2.5), width=40, a=a, t=T)
            if s2 > 3.0:
                xx, yy = cam.p(*PL["济北"])
                text(c, "乞降", xx, yy - 160, "serifB", 96, YAN, a * ease((s2 - 3.0) / 0.5), glow=(YAN, 16, 0.4), stroke=5)
        if sn("baoxin_right") > 0:
            s2 = sn("baoxin_right")
            text(c, "「彼欲戰不得，攻又不能，", 540, 400, "tc", 48, YAN, a * ease(s2 / 0.6), stroke=4)
            text(c, "其勢必離散」", 540, 470, "tc", 48, YAN, a * ease((s2 - 0.3) / 0.6), stroke=4)
            text(c, "— 鲍信 ·《三国志·武帝纪》", 540, 530, "sans", 28, (200, 195, 185), a * ease((s2 - 0.6) / 0.6), stroke=3)
    # ================= 袁绍地理
    a = w("yuan_geo", "cao_ans")
    if a > 0:
        s = sn("yuan_geo")
        cities(["邺", "蓟", "代", "平原"], a, 30)
        region(c, cam, [(113.6, 35.4), (114.2, 38.0), (114.0, 40.5), (117.8, 41.0), (119.0, 39.5), (117.8, 38.0), (117.0, 37.0), (115.6, 35.95)], (190, 160, 80, 0.20), a, edge=(196, 164, 82, 0.9))
        x, y = cam.p(*PL["邺"])
        flag(c, x, y, "袁", YUAN, (240, 220, 160), 1.1, a, T)
        draw_river(c, cam, RIVER_HE, 12, a * (0.6 + 0.4 * math.sin(T * 3)), col=(120, 170, 200))
        lab = [((114.8, 35.25), "黄河 · 护城河"), ((115.3, 40.3), "燕代 · 后院"), ((117.0, 41.6), "戎狄 · 兵源")]
        for i, (ll, s_) in enumerate(lab):
            xx, yy = cam.p(*ll)
            k = ease((sn("yuan_geo2") - i * 0.8) / 0.5) if sn("yuan_geo2") > 0 else 0
            text(c, s_, xx, yy, "serifB", 44, (240, 215, 140), a * k, stroke=5)
        xx, yy = cam.p(116.5, 42.0)
        for i in range(5):
            map_arrow(c, cam, [(112.5 + i * 1.6, 42.3), (113.5 + i * 1.2, 41.2)], ease((sn("yuan_geo2") - 2.4) / 1.0), col=(90, 70, 40), edge=YUAN, width=18, a=a * 0.8, t=T)
    # ================= 兖州叛变
    a = w("revolt")
    if a > 0:
        s = sn("revolt")
        k = ease((s - 0.8) / 1.5)
        region(c, cam, YAN_POLY, (70, 88, 108, 0.45 * k), a, edge=(118, 142, 166, 0.9))
        x, y = cam.p(115.0, 35.7)
        flag(c, x, y, "吕", DONG_D, DONG, 1.1, a * ease(s / 0.6), T)
        flag(c, x - 70, y + 20, "张", DONG_D, DONG, 0.8, a * ease((s - 0.4) / 0.6), T + 1)
        flag(c, x + 70, y + 20, "陈", DONG_D, DONG, 0.8, a * ease((s - 0.6) / 0.6), T + 2)
        for nm in ["鄄城", "范", "东阿"]:
            xx, yy = cam.p(*PL[nm])
            c.drawCircle(xx, yy, 36 + 4 * math.sin(T * 4), paint(GOLD, a * k, stroke=6))
            c.drawCircle(xx, yy, 14, paint(GOLD_L, a * k))
            city(c, cam, nm, a * k, size=36, col=GOLD_L)
        text(c, "只剩三城", 540, 420, "serifB", 72, GOLD_L, a * ease((s - 2.5) / 0.5), glow=(GOLD, 14, 0.4), stroke=5)


# ================================================================ 汴水会战（粒子对冲）
def sh_battle(c, ctx, ts):
    T = ctx.T
    cam = Cam(113.5, 34.83, 1.3 * (1.0 - 0.08 * ease(ts / 6)))
    c.drawColor(C(10, 10, 10))
    base(9).draw(c, cam)
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.25))
    draw_rivers(c, cam, 1.0, bian=1.0)
    text(c, "汴水", *cam.p(113.75, 34.76), "serifB", 48, (170, 210, 220), 1, stroke=4)
    city(c, cam, "荥阳", 1, 40)
    r = np.random.default_rng(2)
    nC, nD = 1100, 2600
    cx = r.normal(0, 120, nC); cy = r.normal(0, 80, nC)
    dxx = r.normal(0, 230, nD); dyy = r.normal(0, 150, nD)
    k = eout(ts / 2.5)
    x0, y0 = 760, 880
    x1, y1 = 260, 820
    # 曹军向西冲，董军包抄
    cxx = lerp(x0, x0 - 180, k) + cx + np.sin(T * 6 + cx) * 2
    cyy = y0 + cy
    lost = r.uniform(0, 1, nC) < ease((ts - 2.0) / 4.0) * 0.6
    dax = lerp(x1, x1 + 220, k) + dxx * (1 - 0.3 * k) + np.sin(T * 5 + dyy) * 2
    day = y1 + dyy * (1 - 0.4 * k)
    wrap_ = ease((ts - 1.5) / 3.0)
    ang = np.arctan2(dyy, dxx)
    dax = dax + np.cos(ang) * 120 * wrap_; day = day + np.sin(ang) * 90 * wrap_
    draw_pts(c, dax, day, DONG, 0.85, 3.5)
    draw_pts(c, cxx[~lost], cyy[~lost], GOLD, 0.45, 7); draw_pts(c, cxx[~lost], cyy[~lost], (22, 20, 16), 1, 4)
    draw_pts(c, cxx[lost] + 20, cyy[lost] + 30, (90, 40, 30), 0.6, 3)
    smoke(c, (x0 + x1) / 2, (y0 + y1) / 2, 500, T, 0.9, n=10, seed=4)
    arrow_rain(c, T, 0.7, n=60, seed=8, area=(0, 300, W, 1250))
    for i in range(3):
        fire_glow(c, (x0 + x1) / 2 + (i - 1) * 160, (y0 + y1) / 2 + 60, 160, T, 0.6, seed=i)
    flag(c, cxx.mean(), y0 - 30, "曹", CAO, GOLD, 1.0, 1, T, tilt=-0.2 * ease((ts - 3) / 1))
    flag(c, x1 + 220 * k, y1 - 40, "徐", DONG_D, DONG, 1.1, 1, T)
    text(c, "力战尽日", 540, 420, "serifB", 80, (240, 200, 160), ease((ts - 0.5) / 0.5), glow=(RED, 16, 0.5), stroke=5)


# ================================================================ 黄巾转色（高燃）
def sh_tide(c, ctx, ts):
    T = ctx.T
    v = ctx.cur["v"]
    flash_mode = v == "tide_flash"
    st = ctx.since("transform") if not flash_mode else ts
    cam = Cam(116.6, 36.25, 2.1 * (1.0 - 0.05 * ease(ts / 8)))
    c.drawColor(C(10, 10, 10))
    base(9).draw(c, cam)
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.30))
    draw_rivers(c, cam, 0.9)
    city(c, cam, "济北", 1, 36)
    n = 9000
    r = np.random.default_rng(42)
    ox = r.normal(0, 1, n); oy = r.normal(0, 1, n); ph = r.uniform(0, 6.28, n); fam = r.uniform(0, 1, n) < 0.6
    cx, cy = 540, 700
    # 初始：散乱潮水
    sx = cx + ox * 300 + np.sin(T * 0.7 + ph) * 8
    sy = cy + oy * 200 + np.cos(T * 0.6 + ph) * 8
    # 转色波：从前锋（左下）推进到后方
    front = (ox * 0.6 - oy * 0.4)
    wave = (st - 0.8) / 2.6 * 6 - 3
    turned = np.clip((wave - front) * 1.5, 0, 1)
    # 目标：精锐 -> 大方阵；家属 -> 后方营地
    soldiers = ~fam
    idx_s = np.cumsum(soldiers) - 1
    ns = soldiers.sum()
    cols_ = int(math.sqrt(ns * 1.6)); rows_ = int(math.ceil(ns / cols_))
    tx = np.where(soldiers, cx - 280 + (idx_s % cols_) / max(cols_ - 1, 1) * 560, cx + ox * 300)
    ty = np.where(soldiers, cy - 230 + (idx_s // cols_) / max(rows_ - 1, 1) * 330, cy + 230 + np.abs(oy) * 70)
    m = ease((st - 3.4) / 3.0) if not flash_mode else 0.0
    px = lerp(sx, tx, m); py = lerp(sy, ty, m)
    if flash_mode:
        turned = np.clip(((ts - 1.2) / 1.6 * 6 - 3 - front) * 1.5, 0, 1)
    colA = np.array(HJ, float); colB = np.array((30, 26, 20), float); colF = np.array(GOLD_L, float)
    flashk = np.clip(1 - np.abs((wave - front) * 1.5 - 0.5) * 2, 0, 1) if not flash_mode else np.zeros(n)
    cols = colA[None] * (1 - turned[:, None]) + colB[None] * turned[:, None]
    cols = cols * (1 - flashk[:, None] * 0.8) + colF[None] * flashk[:, None] * 0.8
    # 金色辉光（已转色者）
    tm = turned > 0.5
    draw_pts(c, px[tm & soldiers], py[tm & soldiers], GOLD, 0.55, 7.5)
    fl = flashk > 0.35
    if fl.any():
        draw_pts(c, px[fl], py[fl], GOLD_L, 0.9, 9.0)
    draw_pts_multi(c, px[soldiers], py[soldiers], cols[soldiers], 1.0, 4.4)
    draw_pts_multi(c, px[fam], py[fam], cols[fam] * 0.6 + np.array((200, 180, 150)) * 0.4, 0.7, 2.4)
    # 家属营炊烟与灯火
    camp = ease((st - 5.5) / 2.0) if not flash_mode else 0
    if camp > 0:
        for i in range(7):
            x = cx - 300 + i * 100; y = cy + 270
            fire_glow(c, x, y, 70, T, camp * 0.9, seed=i)
            for k in range(4):
                u = ((T * 0.12 + k * 0.25 + i * 0.13) % 1)
                c.drawCircle(x + u * 40 + math.sin(u * 6 + i) * 10, y - 20 - u * 200, 14 + u * 40, paint((170, 160, 150), camp * 0.25 * (1 - u), blur=12 + u * 20))
        text(c, "家属营 · 炊烟", cx, cy + 390, "serifB", 44, (240, 220, 190), camp, stroke=5)
    phal = ease((st - 5.2) / 1.0) if not flash_mode else 0
    if phal > 0:
        rrect(c, cx - 300, cy - 250, cx + 300, cy + 120, 8, paint(GOLD, phal * 0.8, stroke=4))
        c.drawRect(skia.Rect.MakeLTRB(cx - 300, cy - 250, cx + 300, cy + 120), paint(GOLD, phal * 0.10, blur=30))
        for i in range(5):
            flag(c, cx - 250 + i * 125, cy - 250, "青" if i == 2 else "曹", CAO, GOLD, 0.7, phal, T + i)
        ta = phal * (1 - ease((ctx.since("transform2") - 3) / 0.5)) if v != "transform" else phal
        if v == "identity":
            ta = 0
        text(c, "青州兵", 540, 330, "serifB", 150, GOLD_L, ta, glow=(GOLD, 28, 0.6), spacing=24)
    if flash_mode:
        k = ease((ts - 0.3) / 0.5)
        text(c, "降卒 30万+", 540, 330, "serifB", 96, WHITE, k, stroke=6, glow=(HJ_L, 16, 0.4))
        text(c, "男女 100万+", 540, 450, "serifB", 80, (240, 215, 170), ease((ts - 1.0) / 0.5), stroke=6)
        chip(c, "史书数字", 540, 530, ease((ts - 1.4) / 0.5), col=(220, 200, 160), size=30, align="c")
    if v == "transform2":
        s = ctx.since("transform2")
        chip(c, "史书数字 · 可能有夸大", 540, 420, ease(s / 0.5) * (1 - ease((s - 3) / 0.4)), col=(220, 200, 160), size=30, align="c")
        text(c, "一座会走路的城", 540, 320, "serifB", 96, WHITE, ease((s - 3.3) / 0.6), stroke=6, glow=(GOLD, 18, 0.4))
    if v == "identity":
        s = ctx.since("identity")
        text(c, "整体收编 · 自成一军", 540, 320, "serifB", 80, GOLD_L, ease(s / 0.6), stroke=6, glow=(GOLD, 18, 0.4))


# ================================================================ 曹操自述（账本）
def sh_ledger(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(12, 11, 10))
    sh = skia.GradientShader.MakeRadial((540, 800), 900, [C(48, 38, 24), C(10, 9, 8)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    # 竹简
    n = 11
    for i in range(n):
        x = 540 + (i - n / 2 + 0.5) * 78
        k = ease((ts - i * 0.05) / 0.5)
        rrect(c, x - 32, 230, x + 32, 1000, 8, paint((170, 140, 90), 0.85 * k))
        rrect(c, x - 32, 230, x + 32, 1000, 8, paint((90, 70, 40), k, stroke=2))
    txt = "汴水之戰數千後領兖州破降黃巾三十萬衆"
    cols = [txt[0:6], txt[6:10], txt[10:14], txt[14:]]
    for j, col in enumerate(cols):
        x = 540 + (1.5 - j) * 156
        for i, ch in enumerate(col):
            k = ease((ts - 0.4 - (j * 6 + i) * 0.07) / 0.3)
            text(c, ch, x, 320 + i * 108, "tcB", 84, (40, 26, 14), k, shadow=0)
    text(c, "曹操自述", 540, 1100, "serifB", 54, GOLD_L, ease((ts - 0.5) / 0.5), shadow=0.9)
    if ctx.cur["v"] == "num_jump":
        s = ctx.since("num_jump")
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.75 * ease(s / 0.4)))
        k = eout((s - 0.3) / 1.4)
        val = int(lerp(3000, 300000, k ** 2))
        text(c, "几千", 300, 760, "serifB", 110, (200, 190, 170), ease(s / 0.4), stroke=5)
        text(c, "→", 540, 760, "serifB", 110, GOLD, ease((s - 0.2) / 0.4), stroke=5)
        text(c, f"{val // 10000}万" if val >= 10000 else f"{val}", 800, 760, "serifB", 120, GOLD_L, ease((s - 0.3) / 0.4), glow=(GOLD, 20, 0.5), stroke=5)
        text(c, "两年多", 540, 920, "serif", 56, WHITE, ease((s - 1.2) / 0.5), stroke=5)


# ================================================================ 问题与命题
def sh_question(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(8, 8, 10))
    sh = skia.GradientShader.MakeRadial((540, 760), 800, [C(40, 30, 18), C(8, 8, 10)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    embers(c, 540, 1300, 1000, T, 0.6, n=50, seed=9, rise=900)
    v = ctx.cur["v"]
    if v == "question":
        s = ctx.since("question")
        text(c, "败军之将", 540, 520, "serifB", 110, WHITE, ease(s / 0.5), stroke=5)
        text(c, "凭什么被请？", 540, 660, "serifB", 110, GOLD_L, ease((s - 0.4) / 0.5), glow=(GOLD, 18, 0.45))
        text(c, "三十万敌人", 540, 860, "serifB", 96, WHITE, ease((s - 2.2) / 0.5), stroke=5)
        text(c, "怎么变成自己的兵？", 540, 990, "serifB", 96, GOLD_L, ease((s - 2.6) / 0.5), glow=(GOLD, 18, 0.45))
    else:
        s = ctx.since("thesis")
        text(c, "地盘", 300, 620, "serifB", 120, WHITE, ease((s - 0.6) / 0.5), stroke=5)
        text(c, "被请来的", 720, 620, "serifB", 100, GOLD_L, ease((s - 1.4) / 0.5), glow=(GOLD, 18, 0.45))
        text(c, "军队", 300, 820, "serifB", 120, WHITE, ease((s - 2.4) / 0.5), stroke=5)
        text(c, "收编来的", 720, 820, "serifB", 100, GOLD_L, ease((s - 3.0) / 0.5), glow=(GOLD, 18, 0.45))
        c.drawLine(140, 700, 940 * ease((s - 0.5) / 1.0) + 140 * (1 - ease((s - 0.5) / 1.0)), 700, paint(GOLD, 0.6, stroke=2))


def sh_title(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(8, 8, 10))
    sh = skia.GradientShader.MakeRadial((540, 800), 800, [C(36, 28, 18), C(8, 8, 10)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    sec = SECTION.get(ctx.cur["scene"], "")
    n_, rest = sec.split(" · ") if " · " in sec else ("", sec)
    head, tail = rest.split("：") if "：" in rest else (rest, "")
    text(c, n_, 540, 560, "serifB", 100, GOLD, ease(ts / 0.5), shadow=0.8)
    text(c, head, 540, 760, "serifB", 150, GOLD_L, ease((ts - 0.2) / 0.5), glow=(GOLD, 24, 0.5), spacing=16)
    text(c, tail, 540, 900, "serif", 64, WHITE, ease((ts - 0.6) / 0.5), shadow=0.9)


# ================================================================ 名声网络
def sh_network(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(10, 10, 12))
    r = np.random.default_rng(17)
    n = 46
    xs = r.uniform(120, 960, n); ys = r.uniform(300, 1200, n)
    xs[0], ys[0] = 540, 760
    k = ease(ts / 3)
    for i in range(n):
        for j in range(i + 1, n):
            d = math.dist((xs[i], ys[i]), (xs[j], ys[j]))
            if d < 230:
                on = ease((k * 900 - math.dist((540, 760), (xs[i], ys[i]))) / 200)
                c.drawLine(xs[i], ys[i], xs[j], ys[j], paint(GOLD, 0.35 * on, stroke=1.6))
    for i in range(n):
        on = ease((k * 900 - math.dist((540, 760), (xs[i], ys[i]))) / 200)
        c.drawCircle(xs[i], ys[i], 10, paint(GOLD_L, 0.25 + 0.75 * on))
        c.drawCircle(xs[i], ys[i], 26, paint(GOLD, 0.3 * on, blur=10))
    flag(c, 540, 800, "曹", CAO, GOLD, 1.1, 1, T)
    text(c, "士人圈的口碑", 540, 300, "serifB", 64, GOLD_L, ease(ts / 0.5), shadow=0.9)
    text(c, "政治资本", 540, 390, "serifB", 52, WHITE, ease((ts - 1) / 0.5), shadow=0.9)
    v = ctx.cur["v"]
    if v in ("analogy1", "analogy1b"):
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.4))
    if v == "wait":
        s = ctx.since("wait")
        yr = 190 + int(clamp(s / 1.6) * 2)
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.5 * ease(s / 0.4)))
        text(c, f"公元{yr}年", 540, 760, "serifB", 120, GOLD_L, ease(s / 0.4), glow=(GOLD, 18, 0.45))


def sh_zhoumu(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(10, 10, 12))
    sh = skia.GradientShader.MakeRadial((540, 800), 800, [C(40, 32, 20), C(10, 10, 12)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    text(c, "东郡太守", 540, 470, "serifB", 80, (200, 190, 170), ease(ts / 0.4), stroke=4)
    text(c, "↓", 540, 600, "serifB", 90, GOLD, ease((ts - 0.5) / 0.4))
    text(c, "兖州牧", 540, 770, "serifB", 150, GOLD_L, ease((ts - 0.8) / 0.4), glow=(GOLD, 24, 0.55), spacing=14)
    for i, s_ in enumerate(["管兵", "管民", "管钱粮"]):
        chip(c, s_, 270 + i * 270, 920, ease((ts - 1.6 - i * 0.4) / 0.4), col=GOLD_L, size=40, align="c")
    text(c, "一郡之守 → 一方诸侯", 540, 1060, "serif", 50, WHITE, ease((ts - 3.0) / 0.5), shadow=0.9)


# ================================================================ 三层机制
def sh_why(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(12, 11, 10))
    sh = skia.GradientShader.MakeRadial((540, 760), 900, [C(36, 28, 18), C(10, 9, 8)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    v = ctx.cur["v"]
    text(c, "为什么收，而不是杀或散？", 540, 300, "serifB", 60, GOLD_L, 1, glow=(GOLD, 12, 0.3))
    tabs = [("why_a", "① 流动人群"), ("why_b", "② 家属在营"), ("why_c", "③ 精兵＋劳力")]
    for i, (vv, lab) in enumerate(tabs):
        act = (v == vv) or (vv == "why_c" and v in ("why_c2",))
        on = ctx.since(vv) > 0
        chip(c, lab, 200 + i * 340, 400, 1 if on else 0.35, col=GOLD_L if act else (170, 160, 140), size=34, align="c")
    if v in ("why3",):
        s = ctx.since("why3")
        for i, (s_, col) in enumerate([("杀？", (200, 90, 70)), ("散？", (150, 150, 150)), ("收！", GOLD_L)]):
            text(c, s_, 540, 640 + i * 170, "serifB", 120, col, ease((s - i * 0.5) / 0.4), stroke=5)
    if v == "why_a":
        s = ctx.since("why_a")
        r = np.random.default_rng(3)
        n = 300
        ox = r.normal(0, 70, n); oy = r.normal(0, 50, n)
        k = ease((s - 1.0) / 2.0)
        # 打散 -> 换个地方重新聚集
        x0, y0 = 300, 760
        x1, y1 = 800, 760
        px = np.where(np.arange(n) % 2 == 0, lerp(x0 + ox, x1 + ox * 0.8, k), x0 + ox)
        py = lerp(y0 + oy, y1 + oy, k) + np.sin(np.arange(n) + T * 3) * 3
        draw_pts(c, px, py, HJ_L, 1, 4)
        text(c, "打散 → 换个地方接着抢", 540, 980, "serifB", 52, WHITE, ease((s - 1.5) / 0.5), stroke=5)
        text(c, "杀光 → 做不到，逼出死战", 540, 1070, "serifB", 52, (230, 140, 120), ease((s - 4.0) / 0.5), stroke=5)
    if v == "why_b":
        s = ctx.since("why_b")
        r = np.random.default_rng(4)
        sx = r.uniform(240, 840, 220); sy = r.uniform(560, 700, 220)
        fx = r.uniform(240, 840, 260); fy = r.uniform(840, 960, 260)
        k = ease((s - 0.6) / 1.5)
        cs = mixc(HJ, (26, 22, 18), k)
        draw_pts(c, sx, sy, GOLD, 0.45 * k, 7); draw_pts(c, sx, sy, cs, 1, 4)
        draw_pts(c, fx, fy, (230, 200, 160), 0.8, 3)
        text(c, "前方：兵", 540, 520, "serifB", 46, GOLD_L, 1, stroke=4)
        text(c, "后方：家小", 540, 1030, "serifB", 46, (230, 200, 160), 1, stroke=4)
        for i in range(7):
            x = 280 + i * 85
            pe = paint(GOLD, 0.7 * ease((s - 1.5) / 0.6), stroke=3); pe.setPathEffect(skia.DashPathEffect.Make([10, 8], -T * 30))
            c.drawLine(x, 710, x + 10, 830, pe)
        chip(c, "人质", 220, 790, ease((s - 2.5) / 0.4), col=(230, 140, 120), size=34)
        chip(c, "后勤", 760, 790, ease((s - 3.0) / 0.4), col=GOLD_L, size=34)
        text(c, "流寇 → 依附曹操的武装集团", 540, 1130, "serifB", 48, WHITE, ease((s - 5.5) / 0.5), stroke=5)
    if v in ("why_c", "why_c2", "analogy3", "analogy3b"):
        s = ctx.since("why_c")
        boxes = [(540, 560, "百万人口"), (300, 760, "精锐 → 青州兵"), (780, 760, "其余 → 劳力"), (780, 960, "196年 许下屯田")]
        for i, (x, y, s_) in enumerate(boxes):
            k = ease((s - i * 0.9) / 0.5)
            w_ = tw(s_, "serifB", 44) + 60
            rrect(c, x - w_ / 2, y - 60, x + w_ / 2, y + 26, 14, paint((16, 14, 12), 0.9 * k))
            rrect(c, x - w_ / 2, y - 60, x + w_ / 2, y + 26, 14, paint(GOLD if i < 3 else (150, 190, 186), k, stroke=2.5))
            text(c, s_, x, y, "serifB", 44, WHITE, k, shadow=0)
        for (a_, b_) in [((540, 590), (300, 700)), ((540, 590), (780, 700))]:
            c.drawLine(*a_, *b_, paint(GOLD, 0.7 * ease((s - 1) / 0.5), stroke=3))
        pe = paint((150, 190, 186), 0.8 * ease((s - 3.0) / 0.5), stroke=3); pe.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
        c.drawLine(780, 790, 780, 900, pe)
        text(c, "得穀百萬斛", 780, 1050, "tc", 40, (150, 190, 186), ease((s - 3.4) / 0.5), shadow=0)
        if ctx.since("why_c2") > 0:
            chip(c, "推测 · 史书未明载二者关系", 540, 1160, ease(ctx.since("why_c2") / 0.4), col=(200, 200, 200), size=30, align="c")
        if v in ("analogy3", "analogy3b"):
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55))


# ================================================================ 起家三问卡
def sh_card3(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(10, 10, 10))
    sh = skia.GradientShader.MakeRadial((540, 760), 900, [C(40, 32, 20), C(10, 10, 10)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    x0, x1, y0 = 70, W - 70, 250
    rrect(c, x0, y0, x1, 1330, 22, paint((14, 12, 10), 0.92))
    rrect(c, x0, y0, x1, 1330, 22, paint(GOLD, 1, stroke=3))
    rrect(c, x0 + 10, y0 + 10, x1 - 10, 1320, 16, paint(GOLD, 0.4, stroke=1.2))
    text(c, "起家三问", 540, y0 + 110, "serifB", 80, GOLD_L, 1, glow=(GOLD, 14, 0.35), spacing=12)
    text(c, "曹操 · 公元192年 · 兖州", 540, y0 + 170, "sans", 32, (200, 190, 170), 1, shadow=0)
    rows = [("card3_a", "手里有什么", ["袁绍表来的东郡太守", "汴水后只剩一千多人的旧部", "陈宫、鲍信等兖州人望"]),
            ("card3_b", "借了谁的势", ["袁绍的表荐", "兖州精英的推举", "黄巾压境的威胁本身"]),
            ("card3_c", "做对了哪一步", ["不屠降，收编为己有", "把敌人变成自己的主力"])]
    y = y0 + 260
    for vv, lab, items in rows:
        s = ctx.since(vv)
        k = ease(s / 0.5) if s > -1e8 else 0
        act = ctx.cur["v"] == vv
        text(c, lab, x0 + 60, y + 10, "serifB", 50, GOLD_L if act else GOLD, k, align="l", shadow=0)
        for i, it in enumerate(items):
            kk = ease((s - 0.5 - i * 0.6) / 0.4)
            c.drawCircle(x0 + 80, y + 70 + i * 62 - 12, 6, paint(GOLD, kk))
            text(c, it, x0 + 104, y + 70 + i * 62, "sans", 38, WHITE, kk, align="l", shadow=0)
        y += 90 + len(items) * 62 + 30
        c.drawLine(x0 + 50, y - 40, x1 - 50, y - 40, paint(GOLD, 0.25, stroke=1.2))


# ================================================================ 刻木
def sh_statue(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(6, 6, 8))
    fire_glow(c, 540, 1060, 520, T, 0.9)
    # 木像剪影
    pa = skia.Path()
    pa.addCircle(540, 640, 58)
    pa.moveTo(470, 720); pa.lineTo(610, 720); pa.lineTo(650, 1050); pa.lineTo(430, 1050); pa.close()
    c.drawPath(pa, paint((60, 40, 24), 1))
    c.drawPath(pa, paint(GOLD, 0.5, stroke=2))
    for k in range(12):
        c.drawLine(470 + k * 6, 740 + k * 25, 610 - k * 5, 745 + k * 25, paint((40, 26, 14), 0.6, stroke=2))
    # 烛
    for x in (330, 750):
        c.drawRect(skia.Rect.MakeLTRB(x - 12, 1000, x + 12, 1100), paint((220, 210, 190)))
        fl = 1 + 0.15 * math.sin(T * 12 + x)
        pf = skia.Path(); pf.moveTo(x, 1000 - 50 * fl); pf.quadTo(x + 14, 985, x, 998); pf.quadTo(x - 14, 985, x, 1000 - 50 * fl)
        c.drawPath(pf, paint((255, 200, 110))); fire_glow(c, x, 975, 120, T, 0.8, seed=x)
    text(c, "衆乃刻木如信形狀，祭而哭焉", 540, 380, "tc", 54, GOLD_L, ease(ts / 0.8), shadow=0.9)
    text(c, "《三國志·武帝紀》", 540, 450, "tcM", 30, (200, 190, 170), ease((ts - 0.5) / 0.6), shadow=0)


# ================================================================ 对话 / 名言
def seal(c, x, y, ch, col, a, size=150):
    rrect(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2, 16, paint(col if sum(col) > 200 else (20, 18, 16), a))
    rrect(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2, 16, paint(GOLD, a, stroke=4))
    text(c, ch, x, y + size * 0.3, "serifB", size * 0.78, (20, 18, 16) if sum(col) > 400 else GOLD_L, a, shadow=0)


def sh_dialog(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(10, 10, 12))
    sh = skia.GradientShader.MakeRadial((540, 760), 900, [C(36, 30, 20), C(10, 10, 12)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    v = ctx.cur["v"]
    if v == "view_title":
        text(c, "四", 540, 560, "serifB", 100, GOLD, ease(ts / 0.5))
        text(c, "押地理，还是押人", 540, 760, "serifB", 110, GOLD_L, ease((ts - 0.2) / 0.5), glow=(GOLD, 24, 0.5))
        return
    if v in ("cao_quote", "fuzi"):
        # 曹操一句，单独定格
        r = np.random.default_rng(5)
        xs = r.uniform(100, 980, 60); ys = r.uniform(300, 1250, 60)
        for i in range(60):
            c.drawCircle(xs[i], ys[i], 6, paint(GOLD_L, 0.4 + 0.3 * math.sin(T * 2 + i)))
            if i > 0:
                c.drawLine(xs[i], ys[i], xs[i - 1], ys[i - 1], paint(GOLD, 0.15, stroke=1))
        seal(c, 540, 560, "曹", CAO, 1, 170)
        return
    seal(c, 260, 640, "袁", YUAN, 1, 170)
    seal(c, 820, 640, "曹", CAO, 1, 170)
    text(c, "袁绍", 260, 790, "serifB", 46, YUAN, 1)
    text(c, "曹操", 820, 790, "serifB", 46, GOLD_L, 1)
    if v == "dialog1":
        s = ctx.since("dialog1")
        text(c, "「若事不輯，", 300, 960, "tc", 52, (240, 225, 180), ease((s - 2.0) / 0.5), align="l", shadow=0.8)
        text(c, "則方面何所可據？」", 340, 1040, "tc", 52, (240, 225, 180), ease((s - 2.4) / 0.5), align="l", shadow=0.8)
        text(c, "如果大事不成，该占据哪一方？", 540, 1130, "sans", 36, WHITE, ease((s - 3) / 0.5), shadow=0.8)
    if v == "dialog2":
        s = ctx.since("dialog2")
        text(c, "「足下意以爲何如？」", 540, 1000, "tc", 56, GOLD_L, ease(s / 0.5), shadow=0.8)
        text(c, "你怎么看？", 540, 1090, "sans", 38, WHITE, ease((s - 0.4) / 0.5), shadow=0.8)
    if v == "cao_ans":
        s = ctx.since("cao_ans")
        text(c, "不谈山河", 540, 1000, "serifB", 72, (200, 190, 170), ease(s / 0.5), stroke=4)
        text(c, "只谈人", 540, 1110, "serifB", 96, GOLD_L, ease((s - 1.5) / 0.5), glow=(GOLD, 18, 0.45))


def sh_borrow(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(10, 10, 12))
    sh = skia.GradientShader.MakeRadial((540, 760), 900, [C(36, 30, 20), C(10, 10, 12)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    text(c, "任天下之智力", 540, 330, "tcB", 84, GOLD_L, ease(ts / 0.5), glow=(GOLD, 16, 0.4))
    text(c, "第一次实践", 540, 420, "serif", 48, WHITE, ease((ts - 0.4) / 0.5), shadow=0.9)
    s = ctx.since("borrow")
    items = [("地", "兖州", "别人的地盘"), ("人", "陈宫 · 鲍信", "别人的人"), ("兵", "青州兵", "原本是敌人")]
    for i, (ch, a_, b_) in enumerate(items):
        k = ease((s - 1.0 - i * 1.6) / 0.5) if s > -1e8 else 0
        y = 620 + i * 210
        seal(c, 230, y, ch, CAO, k, 140)
        text(c, a_, 340, y - 10, "serifB", 56, WHITE, k, align="l", shadow=0.8)
        text(c, b_, 340, y + 60, "sans", 40, GOLD_L, k, align="l", shadow=0.8)


def sh_leave(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(8, 8, 10))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(10, 12, 18), C(30, 24, 20), C(8, 8, 10)], [0, 0.6, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    text(c, "公元220年 · 洛阳", 540, 360, "serifB", 64, GOLD_L, ease(ts / 0.5), glow=(GOLD, 14, 0.35))
    text(c, "曹操去世", 540, 450, "serif", 48, WHITE, ease((ts - 0.4) / 0.5))
    # 方阵向远方行进
    k = ease((ts - 4.0) / 6.0)
    for rr in range(18):
        sc = 0.4 + rr / 18 * 0.8
        y = 640 + rr * 26 * sc - k * 120
        xs = np.linspace(540 - 260 * sc, 540 + 260 * sc, 20)
        ys = np.full(20, y) + np.abs(np.sin(T * 6 + xs * 0.1 + rr)) * 3
        a = 1 - k * 0.6
        draw_pts(c, xs, ys, GOLD, 0.75 * a, 9 * sc); draw_pts(c, xs, ys, (18, 16, 14), a, 5 * sc)
    # 鼓
    beat = (T * 1.6) % 1
    c.drawCircle(860, 560, 70, paint((60, 30, 20), 1)); c.drawCircle(860, 560, 70, paint(GOLD, 0.8, stroke=4))
    c.drawCircle(860, 560, 70 + beat * 100, paint(GOLD, 0.5 * (1 - beat), stroke=3))
    text(c, "擊鼓", 860, 575, "tcB", 40, GOLD_L, 1, shadow=0)
    flag(c, 540, 640 - k * 120, "青", CAO, GOLD, 1.1 - 0.4 * k, 1 - k * 0.5, T)


def sh_novel(c, ctx, ts):
    T = ctx.T
    c.drawColor(C(12, 11, 10))
    sh = skia.GradientShader.MakeRadial((540, 760), 900, [C(40, 30, 22), C(12, 11, 10)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(W, H), p)
    v = ctx.cur["v"]
    if v == "novel_title":
        for i, (ch, t2, col) in enumerate([("演", "明代小说《三国演义》", (190, 120, 110)), ("史", "西晋陈寿《三国志》", GOLD)]):
            x = 300 + i * 480; k = ease((ts - 0.3 - i * 0.4) / 0.5)
            c.drawCircle(x, 740, 150, paint(col, 0.18 * k, blur=30))
            c.drawCircle(x, 740, 130, paint(col, k, stroke=4))
            text(c, ch, x, 790, "serifB", 150, col, k, shadow=0)
            text(c, t2, x, 950, "serifB", 38, col, k)
    text(c, "演义  vs  史书", 540, 360, "serifB", 96, GOLD_L, ease(ts / 0.5), glow=(GOLD, 18, 0.4))
    if v == "novel_chengong":
        s = ctx.since("novel_chengong")
        duizhao_card(c, [("演义说", "陈宫在吕伯奢事件后，弃曹操而去。", "《三國演義》第四、五回"),
                         ("史书说", "陈宫说动兖州，替曹操迎来一州。", "《武帝紀》裴注引《世語》")], 1, y=1180, tt=s)
    if v == "novel_base":
        s = ctx.since("novel_base")
        text(c, "领旨升官", 300, 700, "serifB", 80, (200, 140, 130), ease(s / 0.5), stroke=4)
        text(c, "地方推举", 780, 700, "serifB", 80, GOLD_L, ease((s - 1.5) / 0.5), glow=(GOLD, 16, 0.4))
        text(c, "≠", 540, 700, "serifB", 90, WHITE, ease((s - 1.0) / 0.5))
        text(c, "霸业的底盘", 540, 940, "serifB", 100, GOLD_L, ease((s - 5.0) / 0.5), glow=(GOLD, 20, 0.5))


def sh_end(c, ctx, ts):
    T = ctx.T
    v = ctx.cur["v"]
    cam = Cam(116.0, 35.6, 4.2 * (1 - 0.1 * ease(ts / 20)))
    c.drawColor(C(10, 10, 10))
    base(9).draw(c, cam)
    c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.45))
    draw_rivers(c, cam, 0.8)
    region(c, cam, YAN_POLY, (40, 34, 22, 0.35), 1, edge=GOLD_L + (0.9,), width=4)
    x, y = cam.p(116.2, 35.5)
    ar = Army(1400, 77, "rect", 420, 200)
    px, py = ar.pts(x, y + 170, T, 1.2)
    draw_pts(c, px, py, GOLD, 0.5, 7); draw_pts(c, px, py, (22, 20, 16), 1, 4)
    flag(c, x, y + 60, "曹", CAO, GOLD, 1.3, 1, T)
    if v == "end_q":
        s = ctx.since("end_q")
        text(c, "凭什么被请？", 540, 460, "serifB", 100, WHITE, ease((s - 1) / 0.5), stroke=5)
    if v == "end_a":
        s = ctx.since("end_a")
        text(c, "别人观望", 540, 420, "serifB", 90, (200, 190, 170), ease(s / 0.5), stroke=5)
        text(c, "他真上场", 540, 540, "serifB", 110, GOLD_L, ease((s - 1.0) / 0.5), glow=(GOLD, 20, 0.5))
    if v == "end_b":
        s = ctx.since("end_b")
        text(c, "不是消灭", 540, 420, "serifB", 90, (200, 190, 170), ease(s / 0.5), stroke=5)
        text(c, "而是收编", 540, 540, "serifB", 110, GOLD_L, ease((s - 2.5) / 0.5), glow=(GOLD, 20, 0.5))
    if v == "end_c":
        s = ctx.since("end_c")
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.4 * ease(s / 0.5)))
        for i, ln in enumerate(["别人观望时真上场，", "哪怕输了，也会被记住；", "对手的队伍，", "有时可以变成你的队伍。"]):
            text(c, ln, 540, 520 + i * 110, "serifB", 64, GOLD_L if i % 2 else WHITE, ease((s - i * 1.2) / 0.5), stroke=5)
    if v == "end_quote":
        s = ctx.since("end_quote")
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.5 * ease(s / 0.5)))
    if v == "next":
        s = ctx.since("next")
        k = ease(s / 0.8)
        c.drawRect(skia.Rect.MakeWH(W, H), paint((6, 6, 8), 0.85 * k))
        # 洛阳废墟剪影
        pa = skia.Path(); pa.moveTo(0, 1150)
        xs = [0, 80, 80, 160, 160, 230, 260, 260, 340, 340, 420, 470, 470, 560, 600, 600, 700, 700, 790, 820, 900, 900, 1000, 1080]
        ys = [1150, 1150, 1040, 1040, 1100, 1100, 990, 1080, 1080, 1010, 1060, 1060, 960, 1040, 1040, 1080, 1080, 1000, 1020, 1100, 1100, 1050, 1120, 1120]
        for xx, yy in zip(xs, ys):
            pa.lineTo(xx, yy)
        pa.lineTo(W, 1300); pa.lineTo(0, 1300); pa.close()
        c.drawPath(pa, paint((22, 20, 22), k))
        fire_glow(c, 300, 1100, 300, T, 0.6 * k, seed=1)
        smoke(c, 540, 1050, 900, T, 0.8 * k, n=10, seed=6)
        text(c, "下一集", 540, 480, "serifB", 64, GOLD, ease((s - 0.5) / 0.5))
        text(c, "洛阳废墟里的皇帝", 540, 640, "serifB", 100, GOLD_L, ease((s - 1.0) / 0.6), glow=(GOLD, 20, 0.5))
        text(c, "谁去接他，谁就拿到最值钱的一张牌", 540, 760, "serif", 46, WHITE, ease((s - 4) / 0.6), shadow=0.9)


SHOT_FN = {"night": sh_night, "phalanx": sh_phalanx, "feast": sh_feast, "map": sh_map, "battle": sh_battle, "tide": sh_tide,
           "ledger": sh_ledger, "question": sh_question, "title": sh_title, "network": sh_network, "zhoumu": sh_zhoumu,
           "why": sh_why, "card3": sh_card3, "statue": sh_statue, "dialog": sh_dialog, "borrow": sh_borrow, "leave": sh_leave,
           "novel": sh_novel, "end": sh_end}
