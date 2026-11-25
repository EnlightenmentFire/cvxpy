"""Visual beats. Each beat fn(c, x) where x is a Ctx (t, T, fi, lines{id:(t0,t1)})."""
import math, random
import numpy as np, skia
from engine import *
from sil import *
from geo import CITY

class Ctx:
    def __init__(self, t, T, fi, lines, gt=0.0):
        self.t, self.T, self.fi, self.lines, self.gt = t, T, fi, lines, gt
    def L(self, lid):
        return self.lines.get(lid, (1e9, 1e9))
    def p(self, lid, d=1.0, off=0.0):
        t0, _ = self.L(lid); return clamp((self.t - t0 - off) / d)
    def on(self, lid, off=0.0):
        return self.t >= self.L(lid)[0] + off

MAPBEATS = set()
def mapbeat(f): MAPBEATS.add(f.__name__[2:]); return f

KHW_POLY = [(47.5,34.0),(48.5,37.0),(50.0,37.3),(53.5,36.9),(53.3,40.5),(55.0,43.5),(58.5,45.0),(61.0,46.0),(64.5,45.0),(66.9,44.0),(68.6,43.0),(70.5,42.0),(72.5,41.0),(73.0,39.5),(71.5,37.5),(70.5,35.5),(69.5,33.0),(66.0,31.0),(62.0,29.5),(58.0,27.5),(54.0,27.8),(51.0,29.5),(48.5,31.5)]
MON_POLY = [(73.0,43.0),(75,47),(80,49),(87,51),(95,52),(105,52),(115,51),(122,48),(124,44),(120,41),(116,40.5),(112,39.5),(106,40.5),(98,41.5),(93,39),(88,37.5),(80,37),(75,38.5),(72.8,41.5)]
MON_CORE = [(87,51),(95,52),(105,52),(115,51),(120,48),(118,44),(112,42),(104,41.8),(96,42.5),(90,45),(86,48)]

def poly_path(cam, pts):
    pa = skia.Path(); P = [cam.P(*q) for q in pts]
    sm = catmull(P + [P[0]], 8)
    pa.moveTo(*sm[0])
    for q in sm[1:]: pa.lineTo(*q)
    pa.close(); return pa

def territory(c, cam, pts, color, a=1.0, fill=0.16, prog=1.0):
    if a <= 0: return
    pa = poly_path(cam, pts)
    c.drawPath(pa, paint(color, fill * a))
    st = paint(color, 0.85 * a, stroke=4)
    if prog < 1:
        L = skia.PathMeasure(pa, False).getLength()
        st.setPathEffect(skia.DashPathEffect.Make([L * prog, L * 2], 0))
    c.drawPath(pa, paint(color, 0.35 * a, stroke=14, blur=8)); c.drawPath(pa, st)

def mapframe(c, cam, x, dim=0.0, riv=1.0):
    draw_map(c, cam, dim=dim)
    draw_rivers(c, cam, riv)

def cities(c, cam, x, spec, size=1.0, lsize=40):
    """spec: list of (name, state, alpha, side) """
    for it in spec:
        nm, st, a = it[0], it[1], it[2]; side = it[3] if len(it) > 3 else "r"
        X, Y = cam.city(nm); city_marker(c, X, Y, nm, st, a, x.t, size, side, lsize)

def quote_vertical(c, s, src, a, t, x0=None, size=84, top=430, reveal=1.0):
    """Classical quote as vertical columns (right to left) on a dark card, source under it."""
    cols = [seg for seg in s.replace("，", "，|").replace("。", "。|").replace("；", "；|").split("|") if seg]
    # merge very short columns
    out = []
    for seg in cols:
        if out and len(out[-1]) + len(seg) <= 9: out[-1] += seg
        else: out.append(seg)
    cols = out
    n = len(cols); colw = size * 1.45
    mh = max(len(q) for q in cols) * size * 1.08
    cw = n * colw + 120; ch = mh + 120
    cx = W / 2 if x0 is None else x0
    card(c, cx - cw / 2, top - 60, cw, ch + 70, a, fa=0.78)
    tot = sum(len(q) for q in cols); shown = int(tot * clamp(reveal) + 0.999); k = 0
    for i, q in enumerate(cols):
        xx = cx + cw / 2 - 60 - colw * (i + 0.5)
        for j, ch_ in enumerate(q):
            if k >= shown: break
            ca = a * clamp((tot * reveal - k) * 1.5) if reveal < 1 else a
            vtext(c, ch_, xx, top + j * size * 1.08, size, "tcbk", PAPER, ca)
            k += 1
    text(c, "—— " + src, cx + cw / 2 - 40, top + ch + 40, 40, "tc", GOLD, a, "r")
    return top + ch + 40

def quote_horizontal(c, s, src, a, top=520, size=58, width=15, reveal=1.0):
    lines = wrap(s, width)
    lh = size * 1.55; ch = len(lines) * lh + 150
    card(c, 70, top - 90, W - 140, ch + 40, a, fa=0.8)
    text(c, "「", 110, top - 10, 90, "tc", GOLD, a * 0.9, "l")
    tot = sum(len(l) for l in lines); k = 0
    for i, ln in enumerate(lines):
        la = a * clamp(tot * reveal - k + 1) if reveal < 1 else a
        text(c, ln, W / 2, top + 60 + i * lh, size, "tc", PAPER, la, "c"); k += len(ln)
    text(c, src, W - 110, top + 60 + len(lines) * lh + 20, 32, "tc", GOLD, a, "r")

# =================================================================== s0 hook
def v_storm(c, x):
    t = x.t
    hy = 1080
    sky(c, top=(36, 26, 20), mid=(120, 78, 42), hor=(196, 140, 78), hy=hy, sun=(760, 760, 70, 0.9))
    ground(c, hy, top=(92, 62, 36), bot=(22, 16, 12))
    # far dust
    dust_layer(c, 11, t, 40, 700, 520, 0.55)
    # columns of horsemen emerging from the horizon (perspective)
    cols = [(-0.55, 0.0), (-0.22, 0.6), (0.12, 0.25), (0.45, 0.9), (0.78, 0.4)]
    for ci, (cxn, d0) in enumerate(cols):
        for k in range(14):
            u = ((t * 0.055 + d0 * 0.3 + k * 0.075) % 1.05)
            if u > 1.0: continue
            depth = u ** 1.6
            yy = hy + 6 + depth * 760
            s = 0.12 + depth * 1.7
            xx = W / 2 + cxn * (180 + depth * 1300) + math.sin(k * 3.1 + ci) * 14 * s
            a = clamp(u * 6) * (1.0 - 0.3 * (1 - depth))
            dust = (160, 110, 64)
            c.drawCircle(xx - 30 * s, yy - 20 * s, 60 * s, paint(dust, 0.22 * a, blur=20 * s + 2))
            horse_rider(c, xx, yy, s, ph=t * 9 + k * 1.7 + ci, color=(16, 11, 8), a=a, flip=(cxn > 0.3), banner=(k % 5 == 0))
    dust_layer(c, 12, t, 120, 1000, 500, 0.3)
    dust_layer(c, 13, t, 220, 1400, 600, 0.2)
    c.drawRect(skia.Rect(0, 0, W, H), paint((120, 70, 30), 0.12))
    vignette(c, 0.6)
    # titles
    t1 = x.L("a01")[0]; t2 = x.L("a02")[0]
    a1 = 1.0 * (1 - clamp((t - t2 + 0.2) / 0.4) * 0.65)
    text(c, "1218", W / 2, 520, 220, "serifbk", GOLD, a1, "c", shadow=18, spacing=8)
    text(c, "一支商队被杀", W / 2, 640, 70, "serif", WHITE, a1, "c", shadow=10, spacing=10)
    a2 = clamp((t - t2) / 0.4)
    text(c, "三年后", W / 2, 790, 64, "serif", WHITE, a2, "c", shadow=10, spacing=10)
    text(c, "中亚最强帝国 土崩瓦解", W / 2, 900, 78, "serifbk", GOLD, a2, "c", shadow=12, spacing=6)

# =================================================================== s1 montage
@mapbeat
def v_empire(c, x):
    cam = cam_lerp("eurasia", (100, 44, 0.85), (68, 39, 1.0), clamp(x.t / max(4.0, x.T * 0.55)))
    mapframe(c, cam, x)
    territory(c, cam, MON_POLY, GOLD, clamp(x.t / 0.8), 0.14)
    territory(c, cam, KHW_POLY, CYAN, clamp((x.t - 1.0) / 1.0), 0.18, prog=eout((x.t - 1.0) / 2.5))
    X, Y = cam.P(100, 46.5); region_label(c, "蒙古", X, Y, 64, clamp(x.t / 0.8), GOLD)
    X, Y = cam.P(80, 41.5); region_label(c, "西辽故地", X, Y, 44, clamp(x.t / 0.8), (230, 200, 140))
    X, Y = cam.P(60.5, 35.0); region_label(c, "花剌子模", X, Y, 72, clamp((x.t - 1.5) / 1.0), CYAN)
    pb = x.p("b02", 0.8)
    cities(c, cam, x, [("撒马尔罕", "lit", pb, "r"), ("布哈拉", "lit", pb, "l"), ("玉龙杰赤", "lit", pb, "l")], 0.9, 36)
    X, Y = cam.P(66, 30.5)
    text(c, "锡尔河 → 伊朗高原", X, Y, 40, "sansm", (220, 220, 210), pb * 0.9, "c", stroke=6)

def blob(c, x0, y0, r, color, a, t, n=90, seed=1):
    rng = np.random.default_rng(seed)
    c.drawCircle(x0, y0, r * 1.25, paint(color, 0.18 * a, blur=40))
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(rng.uniform(0, 1))
        xx = x0 + math.cos(ang + t * 0.2) * rr; yy = y0 + math.sin(ang + t * 0.2) * rr * 0.8
        c.drawCircle(xx, yy, 5, paint(color, 0.9 * a))

GARR = ["讹答剌", "布哈拉", "撒马尔罕", "玉龙杰赤", "忽毡", "别纳客忒", "毡的", "养吉干", "昔格纳黑", "讷儿", "匝儿讷黑", "忒耳迷", "巴里黑", "马鲁"]
def garrison_pts(cam, n=34, seed=5):
    rng = np.random.default_rng(seed); out = []
    for nm in GARR: out.append(cam.city(nm))
    while len(out) < n:
        lon = rng.uniform(58, 72); lat = rng.uniform(37, 44.5)
        out.append(cam.P(lon, lat))
    return out

@mapbeat
def v_armyblob(c, x):
    cam = Cam("theater", 64.5, 40.6, 0.66)
    mapframe(c, cam, x, dim=0.15)
    a = clamp(x.t / 0.6)
    X, Y = cam.P(63.5, 40.0); blob(c, X, Y, 170, CYAN, a, x.t, 140, 2)
    text(c, "花剌子模", X, Y - 210, 56, "serifbk", CYAN, a, "c", stroke=6)
    X2, Y2 = cam.P(73.5, 44.5); blob(c, X2, Y2, 110, GOLD, a, x.t, 70, 3)
    text(c, "蒙古", X2, Y2 - 150, 56, "serifbk", GOLD, a, "c", stroke=6)
    pb = x.p("b03", 0.6)
    card(c, 120, 1180, W - 240, 120, pb, fa=0.7)
    text(c, "兵力总数：并不处下风", W / 2, 1238, 46, "sans", WHITE, pb, "c")
    text(c, "（史书给出的数字悬殊，不可尽信）", W / 2, 1284, 30, "sansm", (200, 190, 170), pb, "c")
    pc = x.p("b04", 0.6)
    if pc > 0:
        text(c, "野战决战：几乎没有", W / 2, 420, 60, "serifbk", WHITE, pc, "c", shadow=10)

@mapbeat
def v_shatter(c, x):
    cam = Cam("theater", 64.5, 40.6, 0.66)
    mapframe(c, cam, x, dim=0.15)
    X0, Y0 = cam.P(63.5, 40.0)
    pts = garrison_pts(cam)
    k = eout((x.t - 0.6) / 2.2)
    rng = np.random.default_rng(2)
    if k < 1: blob(c, X0, Y0, 170 * (1 - k), CYAN, 1 - k, x.t, 140, 2)
    for i, (px, py) in enumerate(pts):
        d = clamp(k * 1.3 - i * 0.008)
        xx, yy = lerp(X0, px, eout(d)), lerp(Y0, py, eout(d))
        if d > 0:
            city_marker(c, xx, yy, None, "lit", clamp(d * 3), x.t + i, 0.75)
        if d >= 1:
            ra = clamp((x.t - 3.0 - i * 0.03) / 0.6)
            p = paint(GOLD, 0.7 * ra, stroke=2.5); p.setPathEffect(skia.DashPathEffect.Make([6, 7], x.t * 20))
            c.drawCircle(xx, yy, 30, p)
    for nm in ["讹答剌", "布哈拉", "撒马尔罕", "玉龙杰赤"]:
        X, Y = cam.city(nm); text(c, nm, X + 22, Y + 12, 34, "sans", WHITE, clamp((x.t - 2.0) / 0.6), "l", stroke=6)
    pb = x.p("b06", 0.6)
    text(c, "一支大军 → 几十座孤岛", W / 2, 420, 62, "serifbk", WHITE, pb, "c", shadow=10)

def theater_routes(c, cam, x, which, prog, flow=True):
    R = {
        "otrar": [(71.5, 44.2), (69.6, 43.6), (68.6, 43.1)],
        "jochi": [(68.9, 43.4), (67.3, 44.0), (65.6, 44.3), (64.0, 44.5), (62.2, 45.4)],
        "upper": [(69.4, 42.7), (69.6, 41.8), (69.3, 41.1), (69.6, 40.4)],
        "main": [(69.2, 43.4), (67.6, 42.6), (66.4, 42.0), (65.7, 40.7), (64.6, 39.9)],
    }
    out = {}
    for k in which:
        pts = [cam.P(*q) for q in R[k]]
        out[k] = arrow(c, pts, prog.get(k, 1.0), w=34 if k == "main" else 26, flow_t=(x.t if flow else None))
    return out

@mapbeat
def v_desertflash(c, x):
    cam = cam_lerp("theater", (66.5, 41.5, 0.9), (65.5, 41.0, 1.0), x.t / x.T)
    mapframe(c, cam, x, dim=0.1)
    X, Y = cam.P(64.8, 42.4); region_label(c, "克孜勒库姆沙漠", X, Y, 44, 0.9)
    cities(c, cam, x, [("讹答剌", "siege", 1.0, "r"), ("布哈拉", "lit" if x.t < 3.2 else "fallen", 1.0, "l"), ("撒马尔罕", "lit", 1.0, "r")], 1.0, 40)
    tip = theater_routes(c, cam, x, ["main"], {"main": eout((x.t - 0.6) / 2.6)})
    X, Y = cam.city("布哈拉"); flash(c, X, Y, (x.t - 3.2) / 1.0, GOLD, 160)
    text(c, "从沙漠里冒出来", W / 2, 420, 60, "serifbk", WHITE, clamp((x.t - 1.0) / 0.5), "c", shadow=10)

@mapbeat
def v_chaseflash(c, x):
    cam = Cam("theater", 57.0, 38.0, 0.55)
    mapframe(c, cam, x, dim=0.1)
    k = eout(x.t / (x.T * 0.9))
    path = [(66.9, 37.5), (62.0, 36.8), (58.8, 36.2), (54.5, 36.4), (54.0, 36.95)]
    P = [cam.P(*q) for q in path]
    poly = catmull(P, 20); part, _ = partial(poly, k); sx, sy = part[-1]
    arrow(c, [(px + 0, py + 40) for px, py in P], clamp(k - 0.06), 22, flow_t=x.t)
    arrow(c, [(px + 0, py - 40) for px, py in P], clamp(k - 0.1), 22, flow_t=x.t)
    c.drawCircle(sx, sy, 34, paint(CYAN, 0.3, blur=12)); c.drawCircle(sx, sy, 14, paint(CYAN)); c.drawCircle(sx, sy, 14, paint(INK, 0.8, stroke=3))
    text(c, "苏丹", sx, sy - 34, 40, "sans", CYAN, 1, "c", stroke=6)
    X, Y = cam.P(51, 40.5); region_label(c, "里海", X, Y, 52, 0.9, (160, 200, 215))

def v_indusflash(c, x):
    indus_scene(c, x.t, x.T, quick=True)

def v_question(c, x):
    c.drawRect(skia.Rect(0, 0, W, H), paint((16, 13, 10)))
    sky(c, top=(14, 12, 10), mid=(30, 24, 18), hor=(60, 44, 28), hy=1920)
    a = clamp(x.t / 0.5)
    text(c, "兵并不少", W / 2, 700, 96, "serifbk", WHITE, a, "c", shadow=12, spacing=8)
    text(c, "为什么被", W / 2, 860, 72, "serif", (220, 210, 190), clamp((x.t - 0.8) / 0.5), "c", spacing=8)
    text(c, "一座城一座城", W / 2, 1000, 100, "serifbk", GOLD, clamp((x.t - 1.3) / 0.5), "c", shadow=14, spacing=6)
    text(c, "地吃掉？", W / 2, 1140, 72, "serif", (220, 210, 190), clamp((x.t - 1.8) / 0.5), "c", spacing=8)
    vignette(c, 0.6)

def sunzi_diagram(c, x, t0, a):
    # one big gold group vs ten small cyan groups
    k = eout((x.t - t0) / 1.2)
    c.drawCircle(W / 2, 1250, 120, paint(GOLD, 0.25 * a * k, blur=30))
    c.drawCircle(W / 2, 1250, 90 * k + 1, paint(GOLD, 0.9 * a))
    text(c, "专", W / 2, 1272, 70, "serifbk", INK, a * k, "c")
    for i in range(10):
        ang = i / 10 * 2 * math.pi - math.pi / 2
        R = 300
        xx = W / 2 + math.cos(ang) * R; yy = 1250 + math.sin(ang) * R * 0.62
        c.drawCircle(xx, yy, 30 * k + 1, paint(CYAN, 0.9 * a)); c.drawCircle(xx, yy, 30 * k + 1, paint(INK, 0.6 * a, stroke=2))
    text(c, "分", W / 2 + 300 + 70, 1272, 50, "serifbk", CYAN, a * k, "c")

def dark_map_bg(c, x, vname="theater", lon=64.5, lat=40.5, s=0.7, dim=0.62):
    cam = Cam(vname, lon + 0.15 * math.sin(x.gt * 0.05), lat, s * (1 + 0.01 * x.t))
    draw_map(c, cam, dim=dim)

def v_sunzi1(c, x):
    dark_map_bg(c, x)
    q0 = x.L("b12")[0]
    a = clamp((x.t - q0 + 0.3) / 0.5)
    if x.t < q0:
        text(c, "两千多年前", W / 2, 700, 64, "serif", (220, 210, 190), clamp(x.t / 0.5), "c", shadow=8, spacing=10)
        text(c, "孙子", W / 2, 860, 120, "serifbk", GOLD, clamp((x.t - 0.4) / 0.5), "c", shadow=12, spacing=20)
    else:
        bot = quote_vertical(c, "我專為一，敵分為十，是以十攻其一也。", "《孫子·虛實》", a, x.t, size=78, top=380,
                             reveal=clamp((x.t - q0) / (x.L("b12")[1] - q0 + 0.01) * 1.15))
        if x.on("b13"): sunzi_diagram(c, x, x.L("b13")[0], 1.0)
        if x.on("b14"):
            pa = x.p("b14", 0.5)
            text(c, "为什么要把自己拆成十份？", W / 2, 1520, 52, "serifbk", WHITE, pa, "c", shadow=10)
    vignette(c, 0.5)

# =================================================================== s2 Otrar
@mapbeat
def v_eurasia(c, x):
    cam = cam_lerp("eurasia", (90, 44, 0.85), (77, 42, 0.8), x.t / x.T)
    mapframe(c, cam, x)
    k = eout(x.t / 2.5)
    territory(c, cam, MON_CORE, GOLD, 1.0, 0.16)
    territory(c, cam, MON_POLY, GOLD, k, 0.12, prog=k)
    territory(c, cam, KHW_POLY, CYAN, 1.0, 0.16)
    X, Y = cam.P(102, 47); region_label(c, "蒙古", X, Y, 60, 1.0, GOLD)
    X, Y = cam.P(80, 42); region_label(c, "西辽故地", X, Y, 46, k, (235, 205, 140))
    X, Y = cam.P(62, 38); region_label(c, "花剌子模", X, Y, 60, 1.0, CYAN)
    X, Y = cam.P(72.8, 42.3)
    if k > 0.8:
        flash(c, X, Y, (x.t - 2.2) / 1.2, WHITE, 140)
        text(c, "1218 · 第一次直接接壤", X, Y + 120, 42, "sans", WHITE, clamp((x.t - 2.2) / 0.6), "c", stroke=6)

def dusk(c, x, hy=1250):
    sky(c, top=(22, 18, 24), mid=(92, 56, 40), hor=(188, 112, 58), hy=hy, sun=(300, hy - 60, 60, 0.8))
    ground(c, hy, top=(70, 44, 26), bot=(14, 10, 8))

def wall(c, x0, hy, a=1.0, gate_x=None, gate_open=1.0, glow=1.0):
    p = paint((20, 14, 12), a)
    c.drawRect(skia.Rect(x0, hy - 260, W + 50, hy + 4), p)
    for i in range(int((W + 50 - x0) / 46) + 1):
        c.drawRect(skia.Rect(x0 + i * 46, hy - 290, x0 + i * 46 + 26, hy - 258), p)
    for tx in [x0 - 10, x0 + 330, W - 120]:
        c.drawRect(skia.Rect(tx, hy - 360, tx + 110, hy + 4), p)
        for j in range(3): c.drawRect(skia.Rect(tx + j * 42, hy - 390, tx + j * 42 + 26, hy - 358), p)
    if gate_x is not None:
        gw, gh = 150, 200
        r = skia.Rect(gate_x - gw / 2, hy - gh, gate_x + gw / 2, hy)
        arch = skia.Path(); arch.moveTo(r.left(), hy); arch.lineTo(r.left(), hy - gh + gw / 2)
        arch.arcTo(skia.Rect(r.left(), hy - gh, r.right(), hy - gh + gw), 180, 180, False); arch.lineTo(r.right(), hy); arch.close()
        c.drawPath(arch, paint((255, 190, 110), 0.75 * glow * a)); c.drawPath(arch, paint((255, 170, 90), 0.4 * glow * a, blur=30))
        # doors closing
        dw = gw / 2 * (1 - gate_open)
        c.save(); c.clipPath(arch, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect(r.left(), hy - gh, r.left() + dw, hy), paint((30, 20, 14), a))
        c.drawRect(skia.Rect(r.right() - dw, hy - gh, r.right(), hy), paint((30, 20, 14), a))
        c.restore()

def v_caravan(c, x):
    hy = 1250; dusk(c, x, hy)
    dust_layer(c, 21, x.t, 25, 900, 450, 0.35)
    for i in range(9):
        xx = W + 120 - ((x.t * 70 + i * 150) % (W + 500))
        camel(c, xx, hy + 30 + (i % 2) * 18, 1.05 + (i % 3) * 0.05, ph=x.t * 4 + i, color=(24, 16, 12), a=1.0, flip=True)
    for i in range(3):
        xx = W + 120 - ((x.t * 70 + i * 450 + 75) % (W + 500))
        person(c, xx, hy + 60, 1.0, (24, 16, 12))
    vignette(c, 0.6)
    pa = x.p("c03", 0.6)
    if pa > 0:
        card(c, 90, 400, W - 180, 300, pa, fa=0.78)
        seal(c, 130, 470, "史料分歧", pa, 32)
        text(c, "志费尼《世界征服者史》", 130, 550, 40, "sans", WHITE, pa, "l"); text(c, "约 450 人", W - 130, 550, 46, "serifbk", GOLD, pa, "r")
        text(c, "奈萨维", 130, 640, 40, "sans", WHITE, pa, "l"); text(c, "只记下 4 个商人的名字", W - 130, 640, 40, "serif", GOLD, pa, "r")
    else:
        text(c, "1218 · 蒙古商队西行", W / 2, 520, 58, "serif", PAPER, clamp(x.t / 0.6), "c", shadow=10, spacing=6)

def v_gate(c, x):
    hy = 1250; dusk(c, x, hy)
    t4b = x.L("c04b")[0]
    close = ease((x.t - t4b - 0.3) / 2.0)
    gx = 640
    wall(c, 380, hy, 1.0, gx, 1 - close, glow=1 - 0.85 * close)
    for i in range(5):
        xx = gx - 40 - 150 * (i + 1) + min(x.t, t4b) * 55
        if xx < gx - 60 or close < 0.1:
            a = 1.0 if xx < gx - 60 else clamp((gx + 20 - xx) / 80)
            camel(c, min(xx, gx), hy + 10, 0.9, ph=(min(x.t, t4b + 1)) * 4 + i, color=(18, 12, 10), a=a)
    text(c, "讹答剌", gx, hy - 420, 60, "serifbk", PAPER, clamp(x.t / 0.6), "c", shadow=8, spacing=10)
    vignette(c, 0.55)
    pk = x.p("c05", 0.6)
    if pk > 0:
        card(c, 110, 380, W - 220, 230, pk, fa=0.78)
        text(c, "守将 亦纳勒术", 190, 470, 44, "sans", CYAN, pk, "l")
        text(c, "苏丹之母 秃儿罕可敦", W - 190, 570, 44, "sans", CYAN, pk, "r")
        c.drawLine(300, 490, W - 330, 530, paint(GOLD, 0.9 * pk, stroke=3))
        text(c, "亲族", W / 2, 500, 36, "serif", GOLD, pk, "c")
    if x.on("c04b"): seal(c, 90, 1420, "据志费尼记载", clamp((x.t - t4b) / 0.4), 30)

def v_envoy(c, x):
    hy = 1250
    sky(c, top=(14, 14, 20), mid=(40, 34, 40), hor=(90, 64, 52), hy=hy)
    ground(c, hy, top=(40, 30, 22), bot=(10, 8, 6))
    xx = -100 + x.t * 85
    horse_rider(c, xx, hy + 120, 1.6, ph=x.t * 5, color=(12, 10, 8), gallop=False, banner=True)
    vignette(c, 0.6)
    t7 = x.L("c07")[0]
    if x.t >= t7 and not x.on("c08"):
        pa = x.p("c07", 0.5)
        card(c, 80, 420, W / 2 - 100, 220, pa); card(c, W / 2 + 20, 420, W / 2 - 100, 220, pa, border=CYAN)
        text(c, "交人", W / 4 + 10, 505, 56, "serifbk", WHITE, pa, "c"); text(c, "向母族开刀", W / 4 + 10, 585, 40, "sans", GOLD, pa, "c")
        text(c, "不交", 3 * W / 4 - 10, 505, 56, "serifbk", WHITE, pa, "c"); text(c, "向草原宣战", 3 * W / 4 - 10, 585, 40, "sans", CYAN, pa, "c")
    if x.on("c08"):
        pa = x.p("c08", 0.5)
        card(c, 70, 360, W - 140, 470, pa, fa=0.8)
        seal(c, 110, 430, "史料分歧", pa, 32)
        rows = [("志费尼", "使者被杀"), ("伊本·艾西尔", "使者被杀，随从剃须放回"), ("奈萨维", "三人皆被杀")]
        for i, (a_, b_) in enumerate(rows):
            ra = clamp((x.t - x.L("c08")[0] - 0.5 - i * 1.2) / 0.5) * pa
            text(c, a_, 110, 530 + i * 95, 40, "sans", WHITE, ra, "l"); text(c, b_, W - 110, 530 + i * 95, 40, "serif", GOLD, ra, "r")
        text(c, "（据巴托尔德《突厥斯坦》整理）", W - 110, 800, 28, "sansm", (190, 180, 160), pa, "r")

def v_yuanshi(c, x):
    dark_map_bg(c, x, "eurasia", 75, 42, 1.5, 0.66)
    q0, q1 = x.L("c10")
    a = clamp((x.t + 0.2) / 0.5)
    if x.t < q0:
        text(c, "《元史·太祖本纪》", W / 2, 800, 72, "serifbk", PAPER, a, "c", shadow=10)
        text(c, "明初官修 · 中华书局点校本", W / 2, 900, 38, "sansm", GOLD, a, "c")
    else:
        bot = quote_vertical(c, "夏六月，西域殺使者，帝率師親征，取訛答剌城，擒其酋哈只兒只蘭禿。", "《元史·太祖本紀》", 1.0, x.t, size=70, top=330,
                             reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
        if x.on("c11"):
            text(c, "哈只兒 ≈ 守将称号 Ghayir", W / 2, 1450, 36, "sansm", (210, 200, 180), x.p("c11", 0.5), "c")
    vignette(c, 0.5)

def v_yuanshi2b(c, x):
    dark_map_bg(c, x, "eurasia", 75, 42, 1.5, 0.7)
    a = clamp(x.t / 0.5)
    card(c, 70, 380, W - 140, 620, a, fa=0.82)
    text(c, "《元史·太祖本纪》", W / 2, 470, 48, "tcbk", PAPER, a, "c")
    text(c, "十五年", 130, 580, 44, "tc", GOLD, a, "l"); text(c, "克蒲華城 · 克尋思干城", W - 130, 580, 44, "tc", WHITE, a, "r")
    text(c, "十六年", 130, 680, 44, "tc", GOLD, a, "l"); text(c, "攻卜哈兒、薛迷思干等城", W - 130, 680, 44, "tc", WHITE, a, "r")
    pb = clamp((x.t - 2.0) / 0.6)
    c.drawLine(130, 720, W - 130, 720, paint(RED, 0.8 * pb, stroke=3))
    text(c, "蒲華 = 卜哈兒 = 布哈拉", W / 2, 800, 42, "sans", CYAN, pb, "c")
    text(c, "尋思干 = 薛迷思干 = 撒马尔罕", W / 2, 870, 42, "sans", CYAN, pb, "c")
    pc = x.p("c12b", 0.6)
    text(c, "那珂通世：「此襲本書之誤也」", W / 2, 960, 36, "tc", GOLD, pc, "c")
    text(c, "——《校正增注元親征錄》", W - 130, 1060, 30, "tc", (200, 190, 170), pc, "r")
    vignette(c, 0.5)

@mapbeat
def v_crack(c, x):
    cam = Cam("eurasia", 61, 37, 1.2 * (1 + 0.01 * x.t))
    mapframe(c, cam, x, dim=0.1)
    territory(c, cam, KHW_POLY, CYAN, 1.0, 0.18)
    k = eout((x.t - 0.6) / 2.4)
    crack = [(67.5, 43.5), (66.0, 41.0), (63.6, 39.6), (61.0, 38.6), (58.0, 36.6), (54.5, 35.0), (51.0, 33.0)]
    P = [cam.P(*q) for q in crack]
    rnd = random.Random(4); Pj = [(px + rnd.uniform(-14, 14), py + rnd.uniform(-14, 14)) for px, py in P]
    poly = catmull(Pj, 4); part, _ = partial(poly, k)
    pa = skia.Path(); pa.moveTo(*part[0])
    for q in part[1:]: pa.lineTo(*q)
    c.drawPath(pa, paint((255, 240, 200), 0.6, stroke=14, blur=10)); c.drawPath(pa, paint((255, 250, 235), 1.0, stroke=4))
    text(c, "帝国内部的裂缝", W / 2, 420, 64, "serifbk", WHITE, clamp((x.t - 1.2) / 0.5), "c", shadow=10)

# =================================================================== s3 structure
EXPAND = [  # (year label, polygon) rough schematic stages
    ("约1200 · 花剌子模绿洲", [(58.0,43.8),(61.5,43.5),(62.0,41.5),(60.5,40.5),(58.0,41.0),(56.8,42.5)]),
    ("1210前后 · 河中、呼罗珊", [(56.0,44.0),(61.5,45.0),(66.0,43.5),(68.6,43.0),(70.5,41.8),(68.5,39.0),(66.5,37.0),(61.5,35.0),(57.0,35.5),(54.0,37.0),(53.5,40.5)]),
    ("1215 · 哥疾宁", [(55.0,43.5),(61.0,46.0),(66.9,44.0),(68.6,43.0),(72.5,41.0),(73.0,39.5),(71.5,37.5),(70.5,35.5),(69.5,33.0),(66.0,31.0),(62.0,29.5),(58.5,31.0),(55.0,33.5),(53.5,36.9),(53.3,40.5)]),
    ("1217 · 伊朗高原西部", KHW_POLY),
]
@mapbeat
def v_expand(c, x):
    cam = cam_lerp("eurasia", (61, 38, 1.3), (59, 36, 1.15), x.t / x.T)
    mapframe(c, cam, x)
    t1 = x.L("d02")[0]
    k = (x.t - t1) / max(1.0, x.L("d02")[1] - t1)
    if x.t < t1:
        territory(c, cam, EXPAND[0][1], CYAN, 1.0, 0.2)
        territory(c, cam, MON_POLY, GOLD, 0.0)
        X, Y = cam.P(70, 46); text(c, "西辽（宗主）", X, Y, 44, "serif", (230, 200, 140), clamp(x.t / 0.5), "c", stroke=6)
        X2, Y2 = cam.P(59.5, 42.5); c.drawLine(X2, Y2 - 30, X - 20, Y + 20, paint(GOLD, 0.7 * clamp(x.t / 0.5), stroke=3))
        text(c, "年年纳贡", (X + X2) / 2 + 30, (Y + Y2) / 2, 36, "sans", GOLD, clamp(x.t / 0.5), "l", stroke=5)
    else:
        n = min(3, int(k * 4.2))
        for i in range(n + 1):
            aa = 1.0 if i < n else clamp((k * 4.2 - n) * 2)
            territory(c, cam, EXPAND[i][1], CYAN, aa * (0.5 if i < n else 1.0), 0.10)
        text(c, EXPAND[n][0], W / 2, 420, 52, "serifbk", CYAN, 1.0, "c", shadow=10)
    if x.on("d03"):
        X, Y = cam.city("撒马尔罕"); flash(c, X, Y, ((x.t - x.L("d03")[0] - 2.5) % 2.0) / 1.2, RED, 90)
        city_marker(c, X, Y, "撒马尔罕 · 曾起兵反抗", "lit", x.p("d03", 0.5), x.t, 0.9, "r", 34)
    if x.on("d03b"):
        pb = x.p("d03b", 2.5)
        P = [cam.P(*q) for q in [(51.4, 35.7), (48.5, 34.8), (46.5, 34.2), (45.0, 33.6)]]
        arrow(c, P, eout(pb), 24, CYAN)
        if pb > 0.9:
            X, Y = P[2]; text(c, "大雪 · 折返", X, Y - 40, 40, "sans", WHITE, clamp((pb - 0.9) * 8), "c", stroke=6)
        X, Y = cam.city("巴格达"); city_marker(c, X, Y, "巴格达", "lit", x.p("d03b", 0.5), x.t, 0.8, "d", 34)
    if x.on("d03c"):
        text(c, "四面扩张 · 四面树敌", W / 2, 1300, 54, "serifbk", WHITE, x.p("d03c", 0.5), "c", shadow=10)

def node(c, x0, y0, label, color, a, w=360, h=110, sub=None):
    card(c, x0 - w / 2, y0 - h / 2, w, h, a, fa=0.82, border=color)
    text(c, label, x0, y0 + (0 if sub else 16), 44, "serifbk", color, a, "c")
    if sub: text(c, sub, x0, y0 + 40, 30, "sansm", (210, 200, 180), a, "c")

def v_org(c, x):
    dark_map_bg(c, x, "theater", 60, 41, 0.9, 0.72)
    a = clamp(x.t / 0.5)
    node(c, 300, 560, "苏丹 摩诃末", CYAN, a)
    node(c, 780, 560, "太后 秃儿罕可敦", CYAN, clamp((x.t - x.L("d05")[0]) / 0.5), w=400)
    # army cluster
    for i in range(36):
        xx = 260 + (i % 9) * 70; yy = 1000 + (i // 9) * 70
        c.drawCircle(xx, yy, 20, paint(CYAN, 0.9 * a)); c.drawCircle(xx, yy, 20, paint(INK, 0.6 * a, stroke=2))
    text(c, "主力：康里、钦察等突厥部族骑兵", W / 2, 920, 42, "sans", WHITE, a, "c", stroke=5)
    pk = x.p("d05", 0.8)
    if pk > 0:
        c.drawLine(780, 620, 780, 960, paint(GOLD, 0.9 * pk, stroke=5))
        text(c, "同出一部（康里）", 800, 800, 40, "sans", GOLD, pk, "l", stroke=5)
        p = paint(CYAN, 0.55 * pk, stroke=3); p.setPathEffect(skia.DashPathEffect.Make([10, 10], 0))
        c.drawLine(300, 620, 380, 960, p)
        text(c, "名义统帅", 250, 800, 36, "sansm", (200, 200, 200), pk, "c", stroke=5)
        seal(c, 90, 1380, "据志费尼记载", pk, 30)
    vignette(c, 0.4)

def scroll(c, x0, y0, w, h, title, body, a, color):
    card(c, x0, y0, w, h, a, fill=(52, 44, 34), fa=0.92, border=color, r=10)
    text(c, title, x0 + w / 2, y0 + 70, 46, "serifbk", color, a, "c")
    for i, ln in enumerate(body): text(c, ln, x0 + w / 2, y0 + 140 + i * 56, 38, "serif", PAPER, a, "c")

def v_decree(c, x):
    dark_map_bg(c, x, "theater", 59, 42.3, 1.3, 0.7)
    a = clamp(x.t / 0.5)
    scroll(c, 90, 430, 420, 330, "太后令", ["同一件事", "日期：先"], a, CYAN)
    scroll(c, 570, 430, 420, 330, "苏丹令", ["同一件事", "日期：后"], clamp((x.t - 1.2) / 0.5), CYAN)
    pk = clamp((x.t - 3.0) / 0.6)
    if pk > 0:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(570 - 10, 420, 1000, 770), 14, 14), paint(GOLD, pk, stroke=6))
        text(c, "执行日期更晚的那一道", W / 2, 880, 56, "serifbk", GOLD, pk, "c", shadow=8)
        text(c, "不论出自谁", W / 2, 950, 40, "sans", WHITE, pk, "c")
        seal(c, 90, 1380, "据奈萨维记载", pk, 30)
    if x.on("d07"):
        pa = x.p("d07", 0.5)
        text(c, "一个国家 · 两套命令", W / 2, 1110, 64, "serifbk", WHITE, pa, "c", shadow=10)
    vignette(c, 0.4)

def v_mech1(c, x):
    dark_map_bg(c, x, "theater", 64, 40.5, 0.8, 0.7)
    a = clamp(x.t / 0.5)
    text(c, "机制①：不敢授权", W / 2, 420, 60, "serifbk", GOLD, a, "c", shadow=10)
    t9, t10 = x.L("d09")[0], x.L("d10")[0]
    sx, sy = W / 2, 620
    c.drawCircle(sx, sy, 46, paint(CYAN, a)); text(c, "苏丹", sx, sy + 14, 38, "serifbk", INK, a, "c")
    if x.t < t10:
        # one big army under one general
        bx, by = W / 2, 1050
        blob(c, bx, by, 160, CYAN, a, x.t, 120, 7)
        c.drawCircle(bx, by, 40, paint(WHITE, a)); text(c, "将", bx, by + 14, 40, "serifbk", INK, a, "c")
        if x.t >= t9:
            pk = clamp((x.t - t9) / 0.8)
            arrow(c, [(bx + 40, by - 180), (bx + 160, by - 330), (sx + 60, sy + 70)], eout(pk), 30, RED)
            text(c, "打赢：功高震主", 150, 1340, 44, "sans", WHITE, pk, "l", stroke=5)
            text(c, "倒戈：苏丹完了", W - 150, 1340, 44, "sans", RED, pk, "r", stroke=5)
    else:
        k = eout((x.t - t10) / 1.2)
        rng = np.random.default_rng(3)
        for i in range(16):
            ang = i / 16 * 2 * math.pi; R = 380 * k
            xx = W / 2 + math.cos(ang) * R; yy = 1060 + math.sin(ang) * R * 0.55
            c.drawCircle(xx, yy, 26, paint(CYAN, 0.95 * a)); c.drawCircle(xx, yy, 26, paint(INK, 0.6, stroke=2))
            c.drawLine(sx, sy + 46, xx, yy - 26, paint(CYAN, 0.25 * a * k, stroke=1.5))
        text(c, "每城一将 · 谁也坐不大", W / 2, 1420, 52, "serifbk", WHITE, k, "c", shadow=8)
        text(c, "对内：安全", W / 2, 1080, 46, "sans", CYAN, k, "c", stroke=6)
    vignette(c, 0.4)

@mapbeat
def v_muqali(c, x):
    cam = cam_lerp("eurasia", (87, 41.5, 0.74), (86, 41, 0.7), x.t / x.T)
    mapframe(c, cam, x)
    territory(c, cam, MON_POLY, GOLD, 1, 0.12); territory(c, cam, KHW_POLY, CYAN, 1, 0.12)
    pk = eout(x.t / 2.0)
    P = [cam.P(*q) for q in [(104, 46.5), (110, 43.5), (114.5, 40.5)]]
    arrow(c, P, pk, 40, GOLD, flow_t=x.t)
    X, Y = P[-1]; text(c, "木华黎：华北全权", X + 10, Y + 90, 44, "sans", GOLD, pk, "r", stroke=6)
    X, Y = cam.P(102.8, 47.2); city_marker(c, X, Y, None, "gold", 1, x.t, 1.0)
    for i, (lon, lat) in enumerate([(68.3, 42.85), (64.42, 39.77), (66.98, 39.65), (59.15, 42.32), (69.6, 40.3), (66.9, 36.8), (61.8, 37.6), (58.8, 36.2)]):
        X, Y = cam.P(lon, lat); city_marker(c, X, Y, None, "lit", 1, x.t + i, 0.6)
    X, Y = cam.P(62, 34); text(c, "一支军队都不敢交", X, Y, 42, "sans", CYAN, x.p("d10c", 0.5), "c", stroke=6)
    X, Y = cam.P(108, 37.0); text(c, "半个战场交出去", X, Y, 42, "sans", GOLD, x.p("d10c", 0.5), "c", stroke=6)

@mapbeat
def v_irgiz(c, x):
    cam = Cam("eurasia", 62, 45, 2.0 * (1 + 0.02 * x.t))
    mapframe(c, cam, x)
    X, Y = cam.P(61.5, 48.3)
    k = clamp((x.t - 0.5) / 0.6)
    arrow(c, [(X + 260, Y - 120), (X + 120, Y - 40), (X + 30, Y)], eout(k), 28, GOLD)
    arrow(c, [(X - 120, Y + 300), (X - 70, Y + 140), (X - 20, Y + 20)], eout(k), 28, CYAN)
    for j in range(3): flash(c, X, Y, ((x.t - 1.2 - j * 0.5) % 1.5) / 1.2, WHITE, 110)
    text(c, "交锋（年份各书不同）", X, Y + 120, 40, "sans", WHITE, k, "c", stroke=6)
    X, Y = cam.P(59.8, 45.2); region_label(c, "咸海", X, Y, 44, 1, (160, 200, 215))
    seal(c, 90, 1380, "据记载", k, 30)
    text(c, "苏丹从此畏惧蒙古骑兵的野战", W / 2, 420, 52, "serifbk", WHITE, clamp((x.t - 2.0) / 0.5), "c", shadow=10)

def v_council(c, x):
    dark_map_bg(c, x, "theater", 64, 40, 0.8, 0.72)
    a = clamp(x.t / 0.5)
    text(c, "战前的三个选项", W / 2, 420, 58, "serifbk", WHITE, a, "c", shadow=10)
    opts = [("撤回各城驻军", "以阿姆河为护城河", CYAN), ("扎兰丁：领兵", "到边境迎战", CYAN), ("分兵守城", "苏丹的选择", GOLD)]
    for i, (h1, h2, colr) in enumerate(opts):
        pa = clamp((x.t - 0.6 - i * 0.9) / 0.5)
        y = 520 + i * 210
        card(c, 110, y, W - 220, 170, pa, border=colr)
        text(c, h1, 160, y + 72, 48, "serifbk", colr, pa, "l"); text(c, h2, 160, y + 132, 36, "sans", PAPER, pa, "l")
        if i < 2 and x.t > 3.6:
            pk = clamp((x.t - 3.6 - i * 0.3) / 0.4)
            text(c, "×", W - 170, y + 110, 90, "sansbk", RED, pk, "c")
    seal(c, 110, 1200, "据志费尼记载", clamp((x.t - 1.0) / 0.5), 30)
    if x.on("d12b"):
        pb = x.p("d12b", 0.6)
        card(c, 70, 1230, W - 140, 300, pb, fa=0.88)
        lines = ["只有军队像蒙古军服从成吉思汗那样", "服从苏丹，他才能把兵集中到一处。"]
        for i, ln in enumerate(lines): text(c, ln, W / 2, 1320 + i * 64, 42, "serif", PAPER, pb, "c")
        text(c, "—— 巴托尔德《蒙古入侵时期的突厥斯坦》（大意）", W - 110, 1480, 28, "sansm", GOLD, pb, "r")
    vignette(c, 0.35)

def v_forged(c, x):
    dark_map_bg(c, x, "theater", 64, 40, 0.8, 0.75)
    a = clamp(x.t / 0.5)
    # letter
    lx, ly = 150 + eout((x.t - 1.0) / 2.0) * 420, 560
    card(c, lx, ly, 360, 440, a, fill=(214, 198, 160), fa=0.95, border=GOLD_D, r=6)
    for i in range(7): c.drawLine(lx + 40, ly + 90 + i * 44, lx + 320 - (i % 3) * 30, ly + 90 + i * 44, paint((90, 70, 50), 0.7 * a, stroke=3))
    text(c, "将领 → 成吉思汗", lx + 180, ly + 60, 34, "serifbk", (70, 40, 20), a, "c")
    c.drawCircle(lx + 290, ly + 390, 34, paint((160, 40, 30), 0.9 * a))
    text(c, "伪", lx + 290, ly + 404, 36, "serifbk", WHITE, a, "c")
    text(c, "暗中送到苏丹手里", W / 2, 1150, 52, "serifbk", WHITE, clamp((x.t - 2.5) / 0.5), "c", shadow=8)
    text(c, "猜疑 +1", W / 2, 1250, 64, "serifbk", RED, clamp((x.t - 4.0) / 0.5), "c", shadow=8)
    seal(c, 90, 1380, "据巴托尔德", a, 30)
    vignette(c, 0.4)

@mapbeat
def v_garrison(c, x):
    cam = cam_lerp("theater", (64.6, 40.6, 0.7), (64.6, 40.6, 0.76), x.t / x.T)
    mapframe(c, cam, x, dim=0.08)
    pts = garrison_pts(cam)
    for i, (px, py) in enumerate(pts):
        city_marker(c, px, py, None, "lit", 1, x.t + i, 0.75)
        p = paint(GOLD, 0.0, stroke=2)
    for nm, side in [("讹答剌", "r"), ("布哈拉", "l"), ("撒马尔罕", "r"), ("玉龙杰赤", "l"), ("忽毡", "r"), ("巴里黑", "r")]:
        X, Y = cam.city(nm); text(c, nm, X + (22 if side == "r" else -22), Y + 12, 34, "sans", WHITE, 1, "l" if side == "r" else "r", stroke=6)
    if x.on("d17"):
        pk = x.p("d17", 1.5)
        # links try to appear then break
        rng = np.random.default_rng(9)
        for i in range(18):
            a_, b_ = rng.integers(0, len(pts), 2)
            (x1, y1), (x2, y2) = pts[a_], pts[b_]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            al = clamp(pk * 2) * (1 - clamp((pk - 0.6) * 3))
            p = paint(CYAN, 0.6 * al, stroke=2); p.setPathEffect(skia.DashPathEffect.Make([8, 8], 0))
            c.drawLine(x1, y1, mx - (x2 - x1) * 0.08, my - (y2 - y1) * 0.08, p)
            c.drawLine(mx + (x2 - x1) * 0.08, my + (y2 - y1) * 0.08, x2, y2, p)
        text(c, "缺一个能调兵互救的中枢", W / 2, 420, 54, "serifbk", WHITE, clamp(pk * 1.5), "c", shadow=10)
    elif x.on("d14"):
        text(c, "对内最安全 = 对外最危险", W / 2, 420, 54, "serifbk", WHITE, x.p("d14", 0.5), "c", shadow=10)
    else:
        text(c, "分兵守城", W / 2, 420, 64, "serifbk", CYAN, clamp(x.t / 0.5), "c", shadow=10)

def v_sunzi2(c, x):
    dark_map_bg(c, x, "theater", 64.6, 40.6, 0.75, 0.66)
    q0, q1 = x.L("d15")
    quote_vertical(c, "無所不備，則無所不寡。", "《孫子·虛實》", clamp((x.t + 0.3) / 0.5), x.t, size=96, top=380,
                   reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
    vignette(c, 0.5)

# =================================================================== s4 routes
def theater_base(c, x, cam, extra_states=None):
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.P(64.6, 42.6); region_label(c, "克孜勒库姆沙漠", X, Y, 40, 0.85)
    X, Y = cam.P(67.6, 44.6); text(c, "锡尔河", X, Y, 34, "serif", (150, 205, 225), 0.9, "c", stroke=5)
    X, Y = cam.P(61.5, 40.4); text(c, "阿姆河", X, Y, 34, "serif", (150, 205, 225), 0.9, "c", stroke=5)
    X, Y = cam.P(59.8, 45.2); region_label(c, "咸海", X, Y, 40, 0.9, (160, 200, 215))
    st = {"讹答剌": "lit", "布哈拉": "lit", "撒马尔罕": "lit", "玉龙杰赤": "lit", "忽毡": "lit", "别纳客忒": "lit", "毡的": "lit", "养吉干": "lit", "昔格纳黑": "lit"}
    if extra_states: st.update(extra_states)
    side = {"布哈拉": "l", "玉龙杰赤": "l", "毡的": "l", "养吉干": "l", "别纳客忒": "l"}
    for nm, s in st.items():
        X, Y = cam.city(nm); city_marker(c, X, Y, nm, s, 1, x.t, 0.85, side.get(nm, "r"), 32)

ROUTE_LABEL = {"otrar": ("察合台·窝阔台", -40, -60), "jochi": ("术赤", 0, -50), "upper": ("偏师", 70, 0), "main": ("成吉思汗·拖雷", -60, 0)}
def route_scene(c, x, cam, prog, states=None, labels=True):
    theater_base(c, x, cam, states)
    theater_routes(c, cam, x, [k for k in prog if prog[k] > 0], prog)
    R0 = {"otrar": (71.0, 44.4), "jochi": (66.0, 44.3), "upper": (69.8, 41.8), "main": (66.4, 41.6)}
    if labels:
        for k, v in prog.items():
            if v > 0.2:
                X, Y = cam.P(*R0[k]); lb, dx, dy = ROUTE_LABEL[k]
                text(c, lb, X + dx, Y + dy, 34, "sans", GOLD, clamp((v - 0.2) * 3), "c", stroke=6)

THEATER_CAM = (66.4, 41.8, 0.80)
@mapbeat
def v_routes0(c, x):
    cam = cam_lerp("theater", (66.5, 42.0, 0.62), THEATER_CAM, x.t / x.T)
    theater_base(c, x, cam)
    P = [cam.P(*q) for q in [(76.0, 45.5), (73.5, 44.6), (71.5, 44.0)]]
    arrow(c, P, eout(x.t / 2.0), 46, GOLD, flow_t=x.t)
    text(c, "1219 秋 · 兵临锡尔河", W / 2, 420, 58, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)

def _rp(x):
    if x.on("e04"): return {"otrar": 1, "jochi": 1, "upper": x.p("e04", 2.0)}
    if x.on("e03"): return {"otrar": 1, "jochi": x.p("e03", 2.2)}
    return {"otrar": x.p("e02", 1.6)}
@mapbeat
def v_route1(c, x):
    cam = Cam("theater", *THEATER_CAM); route_scene(c, x, cam, _rp(x), {"讹答剌": "siege" if x.p("e02", 1.6) > 0.9 else "lit"})
    text(c, "第一路 · 围讹答剌", W / 2, 420, 54, "serifbk", GOLD, 1, "c", shadow=10)
@mapbeat
def v_route2(c, x):
    cam = Cam("theater", *THEATER_CAM); route_scene(c, x, cam, _rp(x), {"讹答剌": "siege"})
    text(c, "第二路 · 顺锡尔河而下", W / 2, 420, 54, "serifbk", GOLD, 1, "c", shadow=10)
@mapbeat
def v_route3(c, x):
    cam = Cam("theater", *THEATER_CAM); route_scene(c, x, cam, _rp(x), {"讹答剌": "siege", "毡的": "siege", "养吉干": "siege"})
    text(c, "第三路 · 溯河而上", W / 2, 420, 54, "serifbk", GOLD, 1, "c", shadow=10)
BASE3 = {"otrar": 1, "jochi": 1, "upper": 1}
SIEGE3 = {"讹答剌": "siege", "毡的": "siege", "养吉干": "siege", "别纳客忒": "siege", "忽毡": "siege"}
@mapbeat
def v_route4a(c, x):
    cam = cam_lerp("theater", THEATER_CAM, (67.6, 42.8, 1.1), x.t / x.T)
    route_scene(c, x, cam, dict(BASE3), SIEGE3)
    X, Y = cam.P(69.2, 43.4)
    c.drawCircle(X, Y, 60, paint(GOLD, 0.3, blur=20)); city_marker(c, X, Y, None, "gold", 1, x.t, 1.6)
    text(c, "第四路：成吉思汗 · 拖雷 · 主力", W / 2, 420, 52, "serifbk", GOLD, clamp(x.t / 0.5), "c", shadow=10)
@mapbeat
def v_route4b(c, x):
    t6 = x.L("e06")[0]; T = x.T
    cam = cam_lerp("theater", (67.6, 42.8, 1.1), (65.8, 41.3, 1.0), clamp(x.t / 4.0))
    pr = dict(BASE3); pr["main"] = 0.08 + 0.62 * eout(x.t / 6.0)
    route_scene(c, x, cam, pr, SIEGE3)
    # desert shading pulse
    X, Y = cam.P(64.6, 42.3)
    c.drawCircle(X, Y, 260, paint((230, 180, 100), 0.08 + 0.04 * math.sin(x.t * 2), blur=80))
    if x.on("e07"):
        X, Y = cam.P(65.5, 42.9); text(c, "井在哪？路在哪？", X, Y - 70, 40, "sans", WHITE, x.p("e07", 0.5), "c", stroke=6)
    if x.on("e08"):
        pk = x.p("e08", 0.6)
        for nm in ["匝儿讷黑", "讷儿"]:
            Xc, Yc = cam.city(nm); city_marker(c, Xc, Yc, nm, "gold", pk, x.t, 0.7, "l", 30)
        X, Y = cam.P(66.0, 41.3); text(c, "「汗之路」", X + 30, Y, 40, "serifbk", GOLD, pk, "l", stroke=6)
        seal(c, 90, 1380, "据志费尼记载", pk, 30)
    if x.on("e08b"):
        text(c, "一月 · 穿越荒原", W / 2, 420, 58, "serifbk", WHITE, x.p("e08b", 0.5), "c", shadow=10)
    else:
        text(c, "主力扎进沙漠", W / 2, 420, 58, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
@mapbeat
def v_route4c(c, x):
    cam = cam_lerp("theater", (65.8, 41.3, 1.0), (66.0, 41.2, 0.9), clamp(x.t / 5.0))
    pr = dict(BASE3); pr["main"] = 0.7 + 0.3 * eout(x.t / 1.6)
    route_scene(c, x, cam, pr, dict(SIEGE3, **{"布哈拉": "siege" if x.t > 1.6 else "lit"}))
    X, Y = cam.city("布哈拉"); flash(c, X, Y, (x.t - 1.6) / 1.2, GOLD, 200)
    text(c, "1220 · 2月 · 布哈拉城下", W / 2, 420, 56, "serifbk", GOLD, clamp((x.t - 1.4) / 0.5), "c", shadow=10)
    if x.on("e09b"):
        pk = x.p("e09b", 1.0)
        X1, Y1 = cam.city("讹答剌"); X2, Y2 = cam.city("布哈拉")
        p = paint(WHITE, 0.85 * pk, stroke=3); p.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
        c.drawLine(X1, Y1, lerp(X1, X2, eout(pk)), lerp(Y1, Y2, eout(pk)), p)
        text(c, "直线约470公里", (X1 + X2) / 2 + 40, (Y1 + Y2) / 2 + 60, 40, "sans", WHITE, pk, "l", stroke=6)
        text(c, "本该最安全的后方", W / 2, 1300, 52, "serifbk", CYAN, clamp((x.t - x.L("e09b")[0] - 1.5) / 0.5), "c", shadow=8)

@mapbeat
def v_mech2(c, x):
    cam = Cam("theater", *THEATER_CAM)
    route_scene(c, x, cam, {"otrar": 1, "jochi": 1, "upper": 1, "main": 1}, dict(SIEGE3, **{"布哈拉": "siege"}), labels=False)
    text(c, "机制②：分进合击", W / 2, 420, 60, "serifbk", GOLD, clamp(x.t / 0.5), "c", shadow=10)
    # synchronized clock
    cx, cy = W / 2, 1270; a = clamp((x.t - 0.8) / 0.5)
    c.drawCircle(cx, cy, 80, paint(INK, 0.7 * a)); c.drawCircle(cx, cy, 80, paint(GOLD, a, stroke=4))
    ang = x.t * 1.5
    c.drawLine(cx, cy, cx + 60 * math.sin(ang), cy - 60 * math.cos(ang), paint(GOLD, a, stroke=5))
    text(c, "关键不在分，而在合", W / 2, 1420, 50, "serifbk", WHITE, a, "c", shadow=8)
    if x.on("e11"): text(c, "同一张时间表", W / 2, 1150, 42, "sans", GOLD, x.p("e11", 0.5), "c", stroke=6)

def v_decimal(c, x):
    dark_map_bg(c, x, "theater", 66, 42, 0.8, 0.75)
    a = clamp(x.t / 0.5)
    labels = [("十户", 10), ("百户", 100), ("千户", 1000), ("万户", 10000)]
    for i, (lb, n) in enumerate(labels):
        pa = clamp((x.t - i * 0.8) / 0.5)
        y = 560 + i * 190
        text(c, lb, 140, y + 20, 52, "serifbk", GOLD, pa, "l")
        k = min(n, 10) if i == 0 else 10
        for j in range(k):
            xx = 360 + j * 62
            if i == 0: c.drawCircle(xx, y, 16, paint(GOLD, pa))
            else:
                c.drawRect(skia.Rect(xx - 22, y - 22, xx + 22, y + 22), paint(GOLD, pa * 0.9, stroke=3))
                text(c, labels[i - 1][0][0], xx, y + 12, 26, "sans", GOLD, pa, "c")
    if x.on("e11c"):
        pk = x.p("e11c", 0.6)
        card(c, 90, 1300, W - 180, 190, pk, fa=0.85)
        text(c, "统帅：目标 + 会合时间", W / 2, 1375, 46, "serifbk", WHITE, pk, "c")
        text(c, "各路：怎么走、怎么打，自己定", W / 2, 1450, 40, "sans", GOLD, pk, "c")
    text(c, "层层对应 · 各对上级负责", W / 2, 420, 54, "serifbk", WHITE, a, "c", shadow=10)
    vignette(c, 0.35)

@mapbeat
def v_fog(c, x):
    cam = cam_lerp("theater", (65.5, 41.0, 0.82), (65.5, 41.0, 0.88), x.t / x.T)
    theater_base(c, x, cam, dict(SIEGE3, **{"布哈拉": "siege"}))
    # fog with holes
    c.saveLayer(skia.Rect(0, 0, W, H), None)
    c.drawRect(skia.Rect(0, 0, W, H), paint((10, 10, 12), 0.86))
    clear = skia.Paint(AntiAlias=True); clear.setBlendMode(skia.BlendMode.kDstOut)
    for nm in ["讹答剌", "布哈拉", "撒马尔罕", "玉龙杰赤", "忽毡", "别纳客忒", "毡的", "养吉干", "昔格纳黑"]:
        X, Y = cam.city(nm)
        clear.setShader(skia.GradientShader.MakeRadial(skia.Point(X, Y), 120, [col(WHITE, 1), col(WHITE, 0)]))
        c.drawCircle(X, Y, 120, clear)
    c.restore()
    for nm in ["讹答剌", "布哈拉", "撒马尔罕", "玉龙杰赤", "忽毡"]:
        X, Y = cam.city(nm)
        for j, q in enumerate(["?", "?"]):
            text(c, "?", X + 70 + j * 36, Y - 50 - j * 26, 46, "serifbk", WHITE, 0.6 + 0.3 * math.sin(x.t * 2 + j), "c")
    msg = "每座城只看得见自己的城外"
    if x.on("e16"): msg = "信息差 → 兵力差"
    if x.on("e18b"): msg = "再坚固的城，也只是孤岛"
    text(c, msg, W / 2, 420, 56, "serifbk", WHITE, 1, "c", shadow=10)

def v_sunzi3(c, x):
    dark_map_bg(c, x, "theater", 65.5, 41.0, 0.85, 0.7)
    q0, q1 = x.L("e14")
    if x.t < q0:
        text(c, "孙子", W / 2, 860, 110, "serifbk", GOLD, clamp(x.t / 0.3), "c", shadow=12, spacing=20)
    else:
        quote_vertical(c, "不知戰之地，不知戰之日，則左不能救右，右不能救左。", "《孫子·虛實》", clamp((x.t - q0 + 0.3) / 0.5), x.t, size=70, top=360,
                       reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
    vignette(c, 0.5)

@mapbeat
def v_khujand(c, x):
    cam = cam_lerp("theater", (69.4, 40.6, 1.6), (68.6, 41.3, 1.3), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("忽毡")
    city_marker(c, X, Y, "忽毡", "siege", 1, x.t, 1.0, "d", 36)
    ix, iy = X + 40, Y - 30
    c.drawOval(skia.Rect(ix - 26, iy - 12, ix + 26, iy + 12), paint((90, 80, 60), 1)); c.drawCircle(ix, iy, 30, paint(CYAN, 0.4, stroke=3))
    text(c, "江心岛", ix + 40, iy - 30, 34, "sans", CYAN, 1, "l", stroke=6)
    pk = eout((x.t - 3.5) / 4.0)
    P = [cam.P(*q) for q in [(69.75, 40.3), (69.0, 40.9), (68.6, 41.5), (68.3, 42.6)]]
    if pk > 0: arrow(c, P, pk, 22, CYAN)
    text(c, "帖木儿灭里 · 乘船突围", W / 2, 420, 54, "serifbk", CYAN, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("e18"): text(c, "救得了自己 · 救不了战局", W / 2, 1320, 50, "serifbk", WHITE, x.p("e18", 0.5), "c", shadow=8)

# =================================================================== s5
@mapbeat
def v_bukhara(c, x):
    cam = cam_lerp("theater", (64.0, 39.4, 1.7), (64.2, 39.5, 1.85), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("布哈拉")
    t2, t3, t3b = x.L("f02")[0], x.L("f03")[0], x.L("f03b")[0]
    st = "siege" if x.t < t3 else "fallen"
    # ring of gold around
    for i in range(10):
        ang = i / 10 * 2 * math.pi + x.t * 0.1
        c.drawCircle(X + math.cos(ang) * 150, Y + math.sin(ang) * 110, 9, paint(GOLD, 0.9))
    city_marker(c, X, Y, "布哈拉", st, 1, x.t, 1.4, "u", 44)
    if x.on("f01"):
        pk = eout((x.t - x.L("f01")[0] - 2.5) / 3.0)
        P = [cam.P(*q) for q in [(64.35, 39.7), (64.0, 39.4), (63.6, 39.15), (63.3, 39.05)]]
        if pk > 0: tip = arrow(c, P, pk, 26, CYAN)
        text(c, "夜间突围", W / 2, 420, 58, "serifbk", CYAN, clamp(pk * 3), "c", shadow=10)
    if x.t >= t2:
        pk = eout((x.t - t2) / 1.5)
        P = [cam.P(*q) for q in [(64.9, 39.5), (64.2, 39.0), (63.45, 38.95)]]
        arrow(c, P, pk, 30, GOLD)
        Xa, Ya = cam.P(63.3, 39.05); flash(c, Xa, Ya, (x.t - t2 - 1.4) / 1.2, WHITE, 140)
        X2, Y2 = cam.P(63.25, 38.9); text(c, "阿姆河边", X2, Y2 + 70, 38, "sans", WHITE, pk, "c", stroke=6)
    if x.t >= t3:
        pk = clamp((x.t - t3) / 0.5)
        text(c, "城门打开 · 内城坚持十二天", W / 2, 1300, 50, "serifbk", WHITE, pk, "c", shadow=8)
    if x.t >= t3b:
        for i in range(4):
            q = ((x.t - t3b) * 0.5 + i * 0.25) % 1
            c.drawCircle(X, Y, 60 + q * 600, paint(GOLD, 0.6 * (1 - q), stroke=3))

def v_yuanshi2(c, x):
    dark_map_bg(c, x, "theater", 64.4, 39.8, 1.4, 0.7)
    q0, q1 = x.L("f05")
    if x.t < q0: text(c, "《元史》", W / 2, 860, 90, "serifbk", PAPER, clamp(x.t / 0.3), "c", shadow=10)
    else:
        quote_vertical(c, "十五年庚辰春三月，帝克蒲華城。", "《元史·太祖本紀》", clamp((x.t - q0 + 0.3) / 0.5), x.t, size=86, top=380,
                       reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
    if x.on("f06"):
        text(c, "蒲华 = 布哈拉", W / 2, 1420, 56, "serifbk", CYAN, x.p("f06", 0.5), "c", shadow=8)
        text(c, "（史家考订：实为1220年2月）", W / 2, 1490, 32, "sansm", (200, 190, 170), x.p("f06", 0.5), "c")
    vignette(c, 0.5)

@mapbeat
def v_samarkand(c, x):
    cam = cam_lerp("theater", (66.6, 39.7, 1.6), (66.9, 39.65, 1.85), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("撒马尔罕")
    t8, t9 = x.L("f08")[0], x.L("f09")[0]
    st = "lit" if x.t < t8 else ("siege" if x.t < t9 + 4 else "fallen")
    city_marker(c, X, Y, "撒马尔罕", st, 1, x.t, 1.5, "u", 46)
    if x.t >= t8:
        pk = clamp((x.t - t8) / 1.0)
        rng = np.random.default_rng(4)
        for i in range(70):
            ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(170, 260)
            xx = X + math.cos(ang) * r; yy = Y + math.sin(ang) * r * 0.75
            colr = GOLD if i % 5 == 0 else (150, 140, 120)
            c.drawCircle(xx, yy, 7, paint(colr, 0.9 * pk))
        text(c, "俘虏被驱赶在阵前", W / 2, 420, 54, "serifbk", WHITE, pk, "c", shadow=10)
        seal(c, 90, 1380, "据记载", pk, 30)
    if x.t >= t9:
        pk = clamp((x.t - t9 - 2.5) / 2.0)
        for i in range(12):
            ang = -0.4 + i * 0.07
            r = 30 + pk * 220
            c.drawCircle(X + math.cos(ang) * r, Y + math.sin(ang) * r, 10, paint(CYAN, 0.9 * (1 - clamp((x.t - t9 - 6.5) / 1.5))))
        text(c, "1220 · 3月 · 康里守军出城投降", W / 2, 1300, 46, "serifbk", WHITE, clamp((x.t - t9) / 0.5), "c", shadow=8)

def tower_night(c, x):
    sky(c, top=(8, 10, 18), mid=(20, 24, 36), hor=(46, 44, 52), hy=1400)
    ground(c, 1400, top=(24, 20, 18), bot=(6, 6, 6))
    for i in range(40):
        rr = random.Random(i); sx, sy = rr.uniform(0, W), rr.uniform(0, 900)
        c.drawCircle(sx, sy, rr.uniform(1, 2.4), paint(WHITE, 0.4 + 0.3 * math.sin(x.gt * 2 + i)))
    p = paint((6, 6, 8))
    c.drawRect(skia.Rect(0, 1100, W, 1420), p)
    for i in range(24): c.drawRect(skia.Rect(i * 46, 1070, i * 46 + 26, 1102), p)
    person(c, 540, 1100, 1.6, (6, 6, 8))
    for k in range(3):
        fx = 200 + k * 340; fl = 0.6 + 0.4 * math.sin(x.gt * 3 + k)
        c.drawCircle(fx, 1330, 120, paint((255, 150, 60), 0.12 * fl, blur=60))

def v_dilemma(c, x):
    tower_night(c, x)
    if x.t < x.L("f11")[0]:
        text(c, "如果你是守将", W / 2, 520, 72, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
    else:
        qs = ["援军会不会来？", "苏丹在哪？", "隔壁的城还在吗？"]
        for i, qq in enumerate(qs):
            pa = clamp((x.t - x.L("f11")[0] - i * 1.6) / 0.4)
            card(c, 150 + (i % 2) * 120, 380 + i * 170, 660, 120, pa, border=CYAN)
            text(c, qq, 190 + (i % 2) * 120, 460 + i * 170, 50, "serifbk", WHITE, pa, "l")
            text(c, "不知道", 770 + (i % 2) * 120, 460 + i * 170, 36, "sans", CYAN, clamp(pa * 2 - 1), "r")
    if x.on("f12"):
        text(c, "死守的意义，取决于别人", W / 2, 1000, 52, "serifbk", GOLD, x.p("f12", 0.5), "c", shadow=8)
    vignette(c, 0.4)

def v_staghunt(c, x):
    tower_night(c, x)
    a = clamp(x.t / 0.5)
    text(c, "猎鹿博弈", W / 2, 420, 66, "serifbk", GOLD, a, "c", shadow=10)
    x0, y0, cw, chh = 160, 520, 380, 220
    hdr = ["别人坚守", "别人先跑"]; row = ["我坚守", "我先跑"]
    cells = [["城守住了", "白白送死"], ["保住性命", "保住性命"]]
    colr = [[GOLD, RED], [CYAN, CYAN]]
    for j, h in enumerate(hdr): text(c, h, x0 + 120 + cw * (j + 0.5), y0 - 20, 40, "sans", WHITE, a, "c")
    for i, r in enumerate(row):
        text(c, r, x0 + 50, y0 + chh * (i + 0.5) + 14, 40, "sans", WHITE, a, "c")
        for j in range(2):
            pa = clamp((x.t - 0.6 - (i * 2 + j) * 0.5) / 0.4)
            card(c, x0 + 120 + cw * j + 8, y0 + chh * i + 8, cw - 16, chh - 16, pa, border=colr[i][j])
            text(c, cells[i][j], x0 + 120 + cw * (j + 0.5), y0 + chh * (i + 0.5) + 16, 48, "serifbk", colr[i][j], pa, "c")
    if x.on("f12c"):
        text(c, "看不见别人时：先跑最稳妥", W / 2, 1100, 52, "serifbk", WHITE, x.p("f12c", 0.5), "c", shadow=8)
    vignette(c, 0.4)

def v_cohesion(c, x):
    dark_map_bg(c, x, "theater", 64, 40, 0.9, 0.78)
    a = clamp(x.t / 0.5)
    hx, hy = W / 2, 560
    cut = clamp((x.t - x.L("f14")[0]) / 1.2) if x.on("f14") else 0
    c.drawCircle(hx, hy, 50, paint(GOLD, a)); text(c, "组织", hx, hy + 14, 36, "serifbk", INK, a, "c")
    rng = np.random.default_rng(2)
    for g in range(6):
        ang = math.pi * (0.15 + g * 0.14); gx = W / 2 + math.cos(ang) * 380 * (1 if g % 2 else -1) * 0.9; gy = 900 + (g // 2) * 170
        gx = 180 + g * 145; gy = 1050 + (g % 2) * 120
        if cut < 1:
            p = paint(GOLD, 0.6 * a * (1 - cut), stroke=3)
            c.drawLine(hx, hy + 50, lerp(hx, gx, 1 - cut * 0.5), lerp(hy + 50, gy - 40, 1 - cut * 0.5), p)
        for m in range(5):
            ang2 = m / 5 * 2 * math.pi
            spread = 26 + cut * (60 + rng.uniform(0, 80))
            mx = gx + math.cos(ang2 + g) * spread; my = gy + math.sin(ang2 + g) * spread + cut * 40
            c.drawCircle(mx, my, 12, paint(CYAN, a * (1 - 0.6 * cut)))
    text(c, "希尔斯 & 贾诺维茨（1948）", W / 2, 420, 46, "serifbk", GOLD, a, "c", shadow=8)
    text(c, "身边的小群体 + 运转的组织", W / 2, 1400, 46, "sans", WHITE, a * (1 - cut), "c")
    text(c, "被切断、被打散 → 成片瓦解", W / 2, 1400, 46, "sans", RED, cut, "c")
    vignette(c, 0.35)

@mapbeat
def v_dominoes(c, x):
    cam = Cam("theater", *THEATER_CAM)
    order = ["布哈拉", "撒马尔罕", "讹答剌", "毡的", "养吉干", "别纳客忒", "忽毡", "昔格纳黑"]
    st = {}
    for i, nm in enumerate(order):
        tt = 0.5 + i * 0.9
        st[nm] = "fallen" if x.t > tt else "siege"
    theater_base(c, x, cam, st)
    for i, nm in enumerate(order):
        X, Y = cam.city(nm); flash(c, X, Y, (x.t - 0.5 - i * 0.9) / 1.0, GOLD, 120)
    text(c, "崩溃会传染", W / 2, 420, 64, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("f16"):
        pk = x.p("f16", 0.5)
        card(c, 90, 1240, W - 180, 170, pk, fa=0.85)
        text(c, "史书伤亡数字：大到难以置信", W / 2, 1310, 42, "sans", WHITE, pk, "c")
        text(c, "学者普遍认为有夸大 · 破坏惨重属实", W / 2, 1375, 36, "sansm", GOLD, pk, "c")

# =================================================================== s6
FLIGHT = [(66.98, 39.65), (67.2, 37.4), (66.9, 36.8), (62.5, 36.5), (58.8, 36.2), (54.5, 36.0), (51.4, 35.6), (50.0, 36.3), (52.5, 36.7), (54.0, 36.95)]
def sultan_pos(cam, k):
    P = [cam.P(*q) for q in FLIGHT]; poly = catmull(P, 20); part, _ = partial(poly, k); return part[-1], P

@mapbeat
def v_flight0(c, x):
    cam = cam_lerp("theater", (66.5, 38.6, 1.1), (64.5, 37.8, 0.9), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    cities(c, cam, x, [("撒马尔罕", "siege", 1, "r"), ("布哈拉", "fallen", 1, "l"), ("巴里黑", "lit", 1, "r"), ("忒耳迷", "lit", 1, "l")], 0.9, 34)
    k = 0.18 * eout(x.t / x.T)
    (sx, sy), P = sultan_pos(cam, k)
    poly = catmull(P, 20); part, _ = partial(poly, k)
    pa = skia.Path(); pa.moveTo(*part[0]); [pa.lineTo(*q) for q in part[1:]]
    pp = paint(CYAN, 0.8, stroke=4); pp.setPathEffect(skia.DashPathEffect.Make([12, 10], -x.t * 30)); c.drawPath(pa, pp)
    c.drawCircle(sx, sy, 36, paint(CYAN, 0.3, blur=12)); c.drawCircle(sx, sy, 15, paint(CYAN)); c.drawCircle(sx, sy, 15, paint(INK, 0.8, stroke=3))
    text(c, "苏丹", sx + 30, sy + 12, 40, "sans", CYAN, 1, "l", stroke=6)
    text(c, "苏丹南渡阿姆河", W / 2, 420, 58, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)

def flight_scene(c, x, k, cam, chase_lag=0.06, labels=True, chase=True):
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.P(51, 40.5); region_label(c, "里海", X, Y, 56, 0.9, (160, 200, 215))
    (sx, sy), P = sultan_pos(cam, k)
    passed = [("巴里黑", 0.25), ("你沙不儿", 0.45), ("剌夷", 0.68), ("可疾云", 0.76)]
    for nm, kk in passed:
        X, Y = cam.city(nm); city_marker(c, X, Y, nm, "lit" if k < kk else "fallen", 1, x.t, 0.8, "d", 32)
    poly = catmull(P, 20); part, _ = partial(poly, k)
    pa = skia.Path(); pa.moveTo(*part[0]); [pa.lineTo(*q) for q in part[1:]]
    pp = paint(CYAN, 0.8, stroke=4); pp.setPathEffect(skia.DashPathEffect.Make([12, 10], -x.t * 30)); c.drawPath(pa, pp)
    if chase and k > chase_lag:
        for off, nm in [(30, "哲别"), (-30, "速不台")]:
            Q = [(px, py + off) for px, py in P[1:]]
            kk = clamp((k - chase_lag) / (1 - 0.1))
            tip = arrow(c, [(P[0][0], P[0][1] + off)] + Q, clamp(k - chase_lag), 22, GOLD, flow_t=x.t)
            if tip is not None and labels: text(c, nm, tip[0], tip[1] + off * 1.6, 36, "sans", GOLD, 1, "c", stroke=6)
    c.drawCircle(sx, sy, 36, paint(CYAN, 0.3, blur=12)); c.drawCircle(sx, sy, 15, paint(CYAN)); c.drawCircle(sx, sy, 15, paint(INK, 0.8, stroke=3))
    if labels: text(c, "苏丹", sx, sy - 34, 40, "sans", CYAN, 1, "c", stroke=6)

@mapbeat
def v_flight1(c, x):
    cam = cam_lerp("theater", (64.5, 37.8, 0.9), (61.0, 37.3, 0.75), x.t / x.T)
    k = 0.18 + 0.12 * eout(x.t / x.T)
    flight_scene(c, x, k, cam, chase_lag=0.12)
    msg = "哲别 · 速不台：专追苏丹本人"
    if x.on("g03"): msg = "机制③：打的不是兵，是中枢"
    text(c, msg, W / 2, 420, 52, "serifbk", GOLD, 1, "c", shadow=10)

@mapbeat
def v_flight2(c, x):
    cam = cam_lerp("theater", (61.0, 37.3, 0.75), (55.5, 37.0, 0.72), x.t / x.T)
    k = 0.30 + 0.60 * (x.t / x.T)
    flight_scene(c, x, k, cam, chase_lag=0.07)
    msg = "经呼罗珊一路西逃"
    if x.on("g05"): msg = "他走一城，一城就明白：没人来救了"
    if x.on("g05b"): msg = "没有大脑的身体"
    text(c, msg, W / 2, 420, 50, "serifbk", WHITE, 1, "c", shadow=10)

@mapbeat
def v_island(c, x):
    cam = cam_lerp("theater", (54.5, 37.4, 1.2), (54.0, 37.0, 1.9), x.t / x.T)
    k = 0.9 + 0.1 * eout(x.t / 4.0)
    flight_scene(c, x, k, cam, chase_lag=0.1, labels=False, chase=False)
    X, Y = cam.city("阿必思衮岛")
    fadea = 1 - clamp((x.t - x.L("g07")[0]) / 2.0) if x.on("g07") else 1
    c.drawCircle(X, Y, 50, paint(INK, 0.7 * (1 - fadea)))
    text(c, "里海小岛（阿必思衮附近）", X, Y + 90, 38, "sans", WHITE, 1, "c", stroke=6)
    if x.on("g06"):
        pk = x.p("g06", 0.6)
        card(c, 90, 1240, W - 180, 160, pk, fa=0.85)
        text(c, "病死岛上：1220年12月？1221年1月？", W / 2, 1305, 40, "sans", WHITE, pk, "c")
        text(c, "原始史料无确切日期（巴托尔德）", W / 2, 1365, 32, "sansm", GOLD, pk, "c")
    text(c, "苏丹之死", W / 2, 420, 60, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)

@mapbeat
def v_terken(c, x):
    cam = Cam("theater", 55.5, 39.5, 0.78)
    mapframe(c, cam, x, dim=0.05)
    k = eout(x.t / (x.T * 0.8))
    P = [cam.P(*q) for q in [(59.15, 42.32), (57.5, 40.0), (55.0, 37.8), (53.0, 36.4)]]
    arrow(c, P, k, 22, CYAN)
    X, Y = cam.city("玉龙杰赤"); city_marker(c, X, Y, "玉龙杰赤", "lit", 1, x.t, 1.0, "r", 36)
    X, Y = P[-1]
    if k > 0.95:
        c.drawCircle(X, Y, 40, paint(GOLD, 0.9, stroke=6)); flash(c, X, Y, (x.t - x.T * 0.8) / 1.0, GOLD, 120)
        text(c, "山中城堡 · 被俘", X, Y + 90, 40, "sans", GOLD, 1, "c", stroke=6)
    text(c, "太后秃儿罕可敦出走", W / 2, 420, 56, "serifbk", CYAN, clamp(x.t / 0.5), "c", shadow=10)

@mapbeat
def v_urgench(c, x):
    cam = cam_lerp("theater", (59.4, 42.2, 1.6), (59.15, 42.3, 1.9), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("玉龙杰赤")
    t10, t11 = x.L("g10")[0], x.L("g11")[0]
    st = "siege" if x.t < t11 + 3.5 else "fallen"
    city_marker(c, X, Y, "玉龙杰赤", st, 1, x.t, 1.5, "u", 46)
    if x.t < t10:
        for i in range(5):
            ang = i / 5 * 2 * math.pi + x.t * 0.4
            xx = X + math.cos(ang) * 50; yy = Y + math.sin(ang) * 40
            arrow(c, [(xx, yy), (xx + math.cos(ang) * 60, yy + math.sin(ang) * 50)], 1, 14, CYAN, glow=False)
        text(c, "城内：各行其是", W / 2, 420, 56, "serifbk", CYAN, clamp(x.t / 0.5), "c", shadow=10)
    elif x.t < t11:
        for side, nm in [(-1, "术赤"), (1, "察合台")]:
            ax = X + side * 260
            arrow(c, [(ax, Y + 220), (ax + side * -60, Y + 60), (X + side * 70, Y)], 1, 26, GOLD)
            text(c, nm, ax, Y + 280, 40, "sans", GOLD, 1, "c", stroke=6)
        sp = (math.sin(x.t * 8) + 1) / 2
        text(c, "冲突", X, Y + 210, 56, "serifbk", RED, 0.5 + 0.5 * sp, "c", stroke=6)
        text(c, "城外：蒙古人也不和", W / 2, 420, 56, "serifbk", GOLD, 1, "c", shadow=10)
    else:
        k = eout((x.t - t11) / 1.2)
        p = paint(GOLD, 0.95, stroke=8); c.drawArc(skia.Rect(X - 170, Y - 140, X + 170, Y + 140), -90, 360 * k, False, p)
        text(c, "窝阔台 · 统一指挥", X, Y + 210, 44, "sans", GOLD, k, "c", stroke=6)
        text(c, "1221 春 · 玉龙杰赤陷落", W / 2, 420, 56, "serifbk", WHITE, clamp((x.t - t11 - 3.5) / 0.5), "c", shadow=10)

def tree(c, cx, top, color, a, missing=False, t=0.0):
    rx, ry = cx, top
    if missing:
        p = paint(color, 0.6 * a, stroke=3); p.setPathEffect(skia.DashPathEffect.Make([8, 8], 0))
        c.drawCircle(rx, ry, 44, p); text(c, "?", rx, ry + 18, 54, "serifbk", color, a, "c")
    else:
        c.drawCircle(rx, ry, 44, paint(color, a)); text(c, "裁", rx, ry + 16, 44, "serifbk", INK, a, "c")
    for i in range(3):
        nx = cx - 150 + i * 150; ny = top + 220
        if not missing: c.drawLine(rx, ry + 44, nx, ny - 30, paint(color, 0.7 * a, stroke=3))
        c.drawCircle(nx, ny, 30, paint(color, 0.9 * a))
        for j in range(2):
            mx = nx - 40 + j * 80; my = ny + 160
            c.drawLine(nx, ny + 30, mx, my - 20, paint(color, 0.5 * a, stroke=2))
            c.drawCircle(mx, my, 20, paint(color, 0.8 * a))
    if missing:
        text(c, "×", cx - 75, top + 240, 56, "sansbk", RED, 0.5 + 0.5 * math.sin(t * 6), "c")
        text(c, "×", cx + 75, top + 240, 56, "sansbk", RED, 0.5 + 0.5 * math.sin(t * 6 + 1), "c")

def v_center(c, x):
    dark_map_bg(c, x, "theater", 62, 40, 0.8, 0.78)
    a = clamp(x.t / 0.5)
    tree(c, 280, 640, GOLD, a, False, x.t); tree(c, 800, 640, CYAN, a, True, x.t)
    text(c, "蒙古", 280, 1180, 52, "serifbk", GOLD, a, "c"); text(c, "花剌子模", 800, 1180, 52, "serifbk", CYAN, a, "c")
    text(c, "两边都有内讧", W / 2, 420, 60, "serifbk", WHITE, a, "c", shadow=10)
    text(c, "区别：有没有能拍板的中枢", W / 2, 1350, 50, "serifbk", GOLD, clamp((x.t - 1.5) / 0.5), "c", shadow=8)
    vignette(c, 0.35)

@mapbeat
def v_caucasus(c, x):
    cam = cam_lerp("eurasia", (48, 41, 1.2), (46, 42.5, 1.12), x.t / x.T)
    mapframe(c, cam, x)
    P = [cam.P(*q) for q in [(54.0, 36.9), (49.5, 36.6), (47.0, 39.0), (46.0, 41.8), (45.5, 44.0), (41.5, 46.2), (37.8, 47.2)]]
    arrow(c, P, eout(x.t / (x.T * 0.85)), 34, GOLD, flow_t=x.t)
    X, Y = cam.P(44.5, 42.8); region_label(c, "高加索", X, Y, 44, 0.9)
    X, Y = cam.P(35.0, 43.5); region_label(c, "黑海", X, Y, 50, 0.9, (160, 200, 215))
    X, Y = cam.P(51, 41); region_label(c, "里海", X, Y, 50, 0.9, (160, 200, 215))
    text(c, "一次追击 → 一场远征", W / 2, 420, 56, "serifbk", GOLD, clamp(x.t / 0.5), "c", shadow=10)

# =================================================================== s7
@mapbeat
def v_jalal0(c, x):
    cam = cam_lerp("indus", (66.5, 34.5, 0.75), (68.5, 34.0, 0.9), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    cities(c, cam, x, [("哥疾宁", "lit", 1, "r"), ("八鲁湾", "lit", 1, "r")], 1.0, 38)
    X, Y = cam.P(66.0, 36.0)
    a = clamp(x.t / 0.5)
    text(c, "临终改立继承人", W / 2, 420, 56, "serifbk", WHITE, a, "c", shadow=10)
    # sword
    c.save(); c.translate(W / 2, 1250); c.rotate(-30)
    c.drawRect(skia.Rect(-220, -8, 160, 8), paint((210, 210, 220), a)); c.drawRect(skia.Rect(160, -26, 176, 26), paint(GOLD, a))
    c.drawRect(skia.Rect(176, -8, 250, 8), paint(GOLD_D, a)); c.restore()
    seal(c, 90, 1380, "据奈萨维记载", a, 30)
    if x.on("h02"):
        Xg, Yg = cam.city("哥疾宁"); flash(c, Xg, Yg, (x.t - x.L("h02")[0] - 1) / 1.2, CYAN, 140)
        text(c, "扎兰丁 · 哥疾宁重整", Xg, Yg + 110, 42, "sans", CYAN, x.p("h02", 0.5), "c", stroke=6)

@mapbeat
def v_parwan(c, x):
    cam = Cam("indus", 68.8, 34.4, 1.05)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("八鲁湾")
    t4, t4b, t5 = x.L("h04")[0], x.L("h04b")[0], x.L("h05")[0]
    cities(c, cam, x, [("哥疾宁", "lit", 1, "r")], 1.0, 36)
    if x.t < t4:
        arrow(c, [(X + 300, Y - 300), (X + 150, Y - 120), (X + 30, Y - 20)], eout(x.t / 1.5), 30, GOLD)
        arrow(c, [(X - 120, Y + 380), (X - 60, Y + 200), (X - 10, Y + 30)], eout(x.t / 1.5), 34, CYAN)
        flash(c, X, Y, (x.t - 1.5) / 1.2, CYAN, 180)
        text(c, "八鲁湾：蒙古军少有的大败", W / 2, 420, 52, "serifbk", CYAN, clamp((x.t - 1.6) / 0.5), "c", shadow=10)
        city_marker(c, X, Y, "八鲁湾", "lit", 1, x.t, 1.2, "r", 40)
    else:
        city_marker(c, X, Y, "八鲁湾", "lit", 1, x.t, 1.2, "r", 40)
        blob(c, X, Y + 140, 110, CYAN, 1, x.t, 80, 5)
        text(c, "马", X, Y + 165, 64, "serifbk", WHITE, 1, "c", stroke=6)
        text(c, "为一匹马争吵", W / 2, 420, 56, "serifbk", WHITE, clamp((x.t - t4) / 0.5), "c", shadow=10)
        seal(c, 90, 1380, "据志费尼记载", 1, 30)
        if x.t >= t4b:
            pk = eout((x.t - t4b - 2.5) / 3.0)
            arrow(c, [(X + 60, Y + 160), (X + 260, Y + 260), (X + 420, Y + 420)], pk, 26, CYAN)
            text(c, "不敢罚：怕康里兵不服", W / 2, 1300, 48, "serifbk", WHITE, clamp((x.t - t4b) / 0.5), "c", shadow=8)
        if x.t >= t5:
            text(c, "一场胜仗 ≠ 一个体系", W / 2, 1180, 54, "serifbk", GOLD, x.p("h05", 0.5), "c", shadow=8)

@mapbeat
def v_indus0(c, x):
    cam = cam_lerp("indus", (70.2, 34.3, 0.85), (71.0, 34.0, 1.0), x.t / x.T)
    mapframe(c, cam, x, dim=0.05)
    X, Y = cam.city("印度河渡口")
    P = [cam.P(*q) for q in [(68.6, 34.9), (69.8, 34.4), (71.0, 34.1), (72.0, 33.95)]]
    arrow(c, P, eout(x.t / 3.5), 44, GOLD, flow_t=x.t)
    k = clamp(x.t / 3.5)
    for i in range(30):
        ang = i * 2.4; r = 30 + (i % 6) * 9 * (1.2 - 0.6 * k)
        c.drawCircle(X + 30 + math.cos(ang) * r * 0.6, Y + math.sin(ang) * r, 7, paint(CYAN, 0.9))
    X2, Y2 = cam.P(72.9, 33.6); region_label(c, "印度河", X2, Y2, 46, 0.9, (150, 205, 225))
    text(c, "1221 · 11月 · 印度河畔", W / 2, 420, 54, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("h06b"): text(c, "背水 · 退无可退", W / 2, 1300, 54, "serifbk", CYAN, x.p("h06b", 0.5), "c", shadow=8)

def indus_scene(c, t, T, quick=False, lt=None):
    """Cliff, river, rider leaping. quick: compressed timing for the montage."""
    hy = 1000
    sky(c, top=(20, 18, 26), mid=(70, 50, 48), hor=(170, 110, 70), hy=hy, sun=(820, 760, 70, 0.7))
    # far bank
    fb = skia.Path(); fb.moveTo(0, hy); 
    for i in range(12): fb.lineTo(i * 100, hy - 40 - 30 * math.sin(i * 1.3))
    fb.lineTo(W, hy); fb.lineTo(W, hy + 40); fb.lineTo(0, hy + 40); fb.close()
    c.drawPath(fb, paint((40, 30, 26)))
    # river
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, hy + 30), skia.Point(0, H)], [col((90, 80, 76)), col((16, 22, 28))]))
    c.drawRect(skia.Rect(0, hy + 30, W, H), p)
    for i in range(60):
        rr = random.Random(i); yy = hy + 50 + rr.uniform(0, 860); ww = rr.uniform(40, 160) * (0.5 + (yy - hy) / 900)
        xx = (rr.uniform(0, W) + t * (40 + (yy - hy) * 0.12)) % (W + 200) - 100
        c.drawLine(xx, yy, xx + ww, yy, paint((220, 180, 140), 0.12 + 0.1 * rr.random(), stroke=2))
    # cliff (left)
    cl = skia.Path(); cl.moveTo(0, 820); cl.lineTo(380, 830); cl.lineTo(430, 860); cl.lineTo(450, 960); cl.lineTo(420, 1120)
    cl.lineTo(470, 1300); cl.lineTo(430, 1500); cl.lineTo(0, 1500); cl.close()
    c.drawPath(cl, paint((14, 10, 10)))
    # watchers on cliff
    for i in range(6):
        person(c, 60 + i * 50, 830, 0.55, (14, 10, 10), 1, arm=(1.2 if i == 2 else 0.2))
    s = 0.85
    if quick:
        u = clamp(t / max(T, 0.1) * 1.3)
        u = clamp(t / max(T, 0.1) * 1.05); run_end, leap_end = 0.3, 0.9
    else:
        u = clamp(t / max(4.5, 0.1)) if lt is None else clamp((t - lt) / 4.5)
        run_end, leap_end = 0.35, 0.75
    if u < run_end:
        q = u / run_end; rx = lerp(60, 390, q); ry = 828
        horse_rider(c, rx, ry, s, ph=t * 10, color=(10, 8, 8))
    elif u < leap_end:
        q = (u - run_end) / (leap_end - run_end)
        rx = lerp(390, 700, q); ry = 828 - 140 * math.sin(math.pi * q * 0.7) + q * q * 380
        c.save(); c.translate(rx, ry); c.rotate(-10 + 40 * q); c.translate(-rx, -ry)
        horse_rider(c, rx, ry, s, ph=0, color=(10, 8, 8), pose="leap", gallop=False)
        c.restore()
    else:
        q = (u - leap_end) / (1 - leap_end)
        sx, sy = 700, 1210
        for k in range(3):
            rq = clamp(q * 1.5 - k * 0.2)
            c.drawOval(skia.Rect(sx - 60 - rq * 260, sy - 12 - rq * 40, sx + 60 + rq * 260, sy + 12 + rq * 40), paint((230, 210, 190), 0.6 * (1 - rq), stroke=3))
        if q < 0.25:
            for k in range(14):
                ang = -math.pi * k / 13; r = q * 900
                c.drawCircle(sx + math.cos(ang) * r * 0.6, sy + math.sin(ang) * r, 8, paint((230, 220, 210), 0.7 * (1 - q * 4)))
        hx = sx + q * 280; hy2 = sy - 30 * q
        c.drawCircle(hx, hy2, 12, paint((10, 8, 8), clamp(q * 4)))
        c.drawOval(skia.Rect(hx - 50, hy2 - 6, hx + 30, hy2 + 10), paint((10, 8, 8), 0.8 * clamp(q * 4)))
    dust_layer(c, 31, t, 30, 700, 500, 0.15)
    vignette(c, 0.55)

def v_indusleap(c, x):
    t7, t8, t9 = x.L("h07")[0], x.L("h08")[0], x.L("h09")[0]
    indus_scene(c, x.t, x.T, quick=False, lt=t7 + 2.5)
    seal(c, 90, 400, "据志费尼记载", clamp(x.t / 0.5), 30)
    if x.on("h09"):
        q0, q1 = x.L("h09")
        quote_horizontal(c, "為父者，當有此子！", "—— 志費尼《世界征服者史》（據Boyle英譯轉述）", clamp((x.t - q0 + 0.2) / 0.4), top=560, size=80, width=12)
    elif x.on("h08"):
        text(c, "不许放箭", W / 2, 560, 64, "serifbk", WHITE, x.p("h08", 0.5), "c", shadow=10)

def v_sunzi4(c, x):
    indus_scene(c, x.gt, 100, quick=False, lt=-100)
    c.drawRect(skia.Rect(0, 0, W, H), paint(INK, 0.55))
    q0, q1 = x.L("h11")
    if x.t < q0:
        text(c, "孙子", W / 2, 860, 110, "serifbk", GOLD, clamp(x.t / 0.3), "c", shadow=12, spacing=20)
    else:
        quote_vertical(c, "投之亡地然後存，陷之死地然後生。", "《孫子·九地》", clamp((x.t - q0 + 0.3) / 0.5), x.t, size=82, top=380,
                       reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
    if x.on("h13"):
        text(c, "死地救得了一个人", W / 2, 1350, 50, "serifbk", WHITE, x.p("h13", 0.5), "c", shadow=8)
        text(c, "救不了一个国家", W / 2, 1430, 50, "serifbk", GOLD, x.p("h13", 0.5, 1.5), "c", shadow=8)
    if x.on("h14"):
        c.drawRect(skia.Rect(0, 1280, W, 1480), paint(INK, 0.7 * x.p("h14", 0.4)))
        text(c, "个人的勇武，补不上体系的失序", W / 2, 1400, 50, "serifbk", WHITE, x.p("h14", 0.5), "c", shadow=8)

# =================================================================== s8
@mapbeat
def v_recap(c, x):
    cam = Cam("theater", 64.6, 40.6, 0.7)
    mapframe(c, cam, x, dim=0.12)
    pts = garrison_pts(cam)
    t2 = x.L("i02")[0]
    k = eout((x.t - t2 - 1.5) / 2.5) if x.on("i02") else 0
    X0, Y0 = cam.P(63.5, 40.0)
    for i, (px, py) in enumerate(pts):
        xx, yy = lerp(px, X0, k), lerp(py, Y0, k)
        city_marker(c, xx, yy, None, "lit", 1 - 0.7 * k, x.t + i, 0.75)
    if k > 0.3: blob(c, X0, Y0, 170 * k, CYAN, k, x.t, 140, 2)
    if x.on("i02"): text(c, "同一时间 · 同一地点", W / 2, 420, 60, "serifbk", GOLD, x.p("i02", 0.5), "c", shadow=10)
    else: text(c, "兵并不少", W / 2, 420, 60, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("i03"):
        text(c, "缺的是：敢授权、能协调的中枢", W / 2, 1320, 48, "serifbk", WHITE, x.p("i03", 0.5), "c", shadow=8)

@mapbeat
def v_recap2(c, x):
    cam = Cam("eurasia", 78, 42, 0.64)
    mapframe(c, cam, x)
    k = eout(x.t / 3.0)
    arrow(c, [cam.P(*q) for q in [(66, 39), (58, 37), (50, 38), (46, 42), (40, 46)]], k, 30, GOLD, flow_t=x.t)
    arrow(c, [cam.P(*q) for q in [(103, 46.5), (110, 43), (115, 40)]], k, 30, GOLD, flow_t=x.t)
    X, Y = cam.P(45, 45.5); text(c, "哲别 · 速不台", X, Y - 40, 38, "sans", GOLD, k, "c", stroke=6)
    X, Y = cam.P(113, 38.5); text(c, "木华黎", X, Y + 60, 38, "sans", GOLD, k, "c", stroke=6)
    X, Y = cam.P(102.8, 47.2); city_marker(c, X, Y, None, "gold", 1, x.t, 1.4)
    for i, (lon, lat) in enumerate([(68.3, 42.85), (64.42, 39.77), (66.98, 39.65), (59.15, 42.32), (69.6, 40.3), (66.9, 36.8), (61.8, 37.6)]):
        X, Y = cam.P(lon, lat); city_marker(c, X, Y, None, "fallen" if x.on("i03c") else "lit", 1, x.t + i, 0.6)
    text(c, "把兵交给别人", W / 2, 420, 58, "serifbk", GOLD, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("i03c"): text(c, "攥在手里 → 谁也救不了谁", W / 2, 1300, 50, "serifbk", CYAN, x.p("i03c", 0.5), "c", shadow=8)

def v_lesson(c, x):
    dark_map_bg(c, x, "theater", 64.6, 40.6, 0.7, 0.8)
    a = clamp(x.t / 0.5)
    card(c, 80, 520, W - 160, 640, a, fa=0.85)
    lines = [("领导者不敢授权", WHITE), ("资源就会被拆成", WHITE), ("互不支援的碎片", CYAN), ("", WHITE), ("对手不需要比你大", WHITE), ("只需要比你集中", GOLD)]
    for i, (ln, colr) in enumerate(lines):
        pa = clamp((x.t - i * 0.7) / 0.5)
        text(c, ln, W / 2, 640 + i * 92, 62, "serifbk", colr, pa, "c")
    vignette(c, 0.4)

def parchment(c, x):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), 1200, [col((70, 58, 42)), col((24, 18, 12))]))
    c.drawRect(skia.Rect(0, 0, W, H), p)
    dust_layer(c, 41, 0, 0, 0, H, 0.15)

def v_athir(c, x):
    parchment(c, x)
    q0, q1 = x.L("i06")
    if x.t < q0:
        text(c, "伊本·艾西尔", W / 2, 760, 84, "serifbk", PAPER, clamp(x.t / 0.5), "c", shadow=10)
        text(c, "《全史》 · 同时代阿拉伯史家", W / 2, 860, 40, "sansm", GOLD, clamp(x.t / 0.5), "c")
        # pen hesitating
        px = W / 2 + 80 * math.sin(x.t * 1.2); py = 1080
        c.drawLine(px, py, px + 120, py - 160, paint(PAPER, 0.7, stroke=4))
    else:
        quote_horizontal(c, "多年來，我一直不願提起這件事。它太可怕了，我不忍落筆；一隻腳剛邁出去，另一隻腳又縮了回來。",
                         "—— 伊本·艾西爾《全史》伊曆617年條（據E. G. Browne英譯轉述）", clamp((x.t - q0 + 0.3) / 0.5), top=520, size=58, width=14,
                         reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.1))
    vignette(c, 0.5)

def v_end(c, x):
    parchment(c, x)
    t8 = x.L("i08")[0]
    if x.t < t8:
        text(c, "朋友们一再劝他", W / 2, 760, 60, "serif", PAPER, clamp(x.t / 0.5), "c")
        text(c, "略过不写，于事无补", W / 2, 880, 60, "serifbk", GOLD, clamp((x.t - 2.0) / 0.5), "c")
        seal(c, 90, 1380, "据Browne英译", clamp(x.t / 0.5), 30)
    else:
        a = clamp((x.t - t8) / 0.8)
        text(c, "有些事", W / 2, 760, 70, "serif", PAPER, a, "c", spacing=10)
        text(c, "正因为可怕", W / 2, 880, 80, "serifbk", WHITE, a, "c", spacing=10)
        text(c, "才必须被记住", W / 2, 1000, 80, "serifbk", GOLD, clamp((x.t - t8 - 1.0) / 0.8), "c", spacing=10)
        text(c, "历史的关键一局", W / 2, 1240, 40, "sansm", GOLD, clamp((x.t - t8 - 3.0) / 0.8), "c", spacing=8)
    vignette(c, 0.6)
