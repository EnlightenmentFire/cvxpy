"""Visual beats for ep.66. Each beat fn(c, x) where x is a Ctx (t, T, fi, lines{id:(t0,t1)}, gt)."""
import math
import numpy as np, skia
from engine import *
from art import *
from sil import person, dust_layer
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
SCENIC = set()   # 情景示意 beats
def scenic(f): SCENIC.add(f.__name__[2:]); return f

# ------------------------------------------------------------------ shared map helpers
HOJO = [(138.95, 34.60), (138.78, 34.95), (138.92, 35.20), (138.97, 35.45), (138.75, 35.75), (138.55, 36.10), (138.62, 36.45),
        (138.95, 36.80), (139.35, 36.62), (139.75, 36.40), (140.15, 36.10), (140.45, 35.80), (140.35, 35.45), (140.05, 35.30),
        (139.80, 35.33), (139.65, 35.18), (139.45, 35.30), (139.20, 35.26), (139.12, 35.05), (139.10, 34.85)]
TOKAIDO = [(135.77, 35.01), (136.40, 35.05), (136.90, 35.18), (137.70, 34.75), (138.38, 34.98), (138.86, 35.10), (139.02, 35.18), (139.15, 35.25)]
SEAWAY = [(135.40, 34.60), (135.15, 34.05), (135.75, 33.45), (136.75, 34.20), (137.40, 34.50), (138.30, 34.55), (138.80, 34.45), (139.15, 34.70), (139.30, 35.00), (139.20, 35.20)]
NORTHWAY = [(136.65, 36.56), (137.60, 36.75), (138.20, 36.55), (138.70, 36.36), (138.79, 36.32)]

def poly_path(cam, pts):
    pa = skia.Path(); Pp = [cam.P(*q) for q in pts]
    sm = catmull(Pp + [Pp[0]], 8)
    pa.moveTo(*sm[0])
    for q in sm[1:]: pa.lineTo(*q)
    pa.close(); return pa

def territory(c, cam, pts, color, a=1.0, fill=0.16, prog=1.0):
    if a <= 0: return
    pa = poly_path(cam, pts)
    c.drawPath(pa, paint(color, fill * a))
    st = paint(color, 0.85 * a, stroke=4)
    if prog < 1:
        Lm = skia.PathMeasure(pa, False).getLength()
        st.setPathEffect(skia.DashPathEffect.Make([Lm * prog, Lm * 2], 0))
    c.drawPath(pa, paint(color, 0.35 * a, stroke=14, blur=8)); c.drawPath(pa, st)

def mapframe(c, cam, x, dim=0.0, riv=0.8):
    draw_map(c, cam, dim=dim)
    draw_rivers(c, cam, riv)

def castles(c, cam, x, spec, size=1.0, lsize=38):
    for it in spec:
        nm, st, a = it[0], it[1], it[2]; side = it[3] if len(it) > 3 else "r"
        X, Y = cam.city(nm); city_marker(c, X, Y, nm, st, a, x.t, size, side, lsize)

def red_marker(c, X, Y, a, t, size=1.0, name=None, side="r", lsize=38):
    if a <= 0: return
    r = 11 * size; pul = 0.5 + 0.5 * math.sin(t * 3)
    c.drawCircle(X, Y, r * (2.4 + 0.6 * pul), paint(RED, 0.25 * a, blur=10))
    c.drawCircle(X, Y, r, paint(RED, a)); c.drawCircle(X, Y, r, paint(INK, 0.8 * a, stroke=2.5))
    c.drawCircle(X, Y, r * 0.42, paint(WHITE, 0.9 * a))
    if name:
        if side == "r": text(c, name, X + r + 14, Y + lsize * 0.36, lsize, "sans", WHITE, a, "l", stroke=6)
        elif side == "l": text(c, name, X - r - 14, Y + lsize * 0.36, lsize, "sans", WHITE, a, "r", stroke=6)
        elif side == "u": text(c, name, X, Y - r - 16, lsize, "sans", WHITE, a, "c", stroke=6)
        else: text(c, name, X, Y + r + lsize + 6, lsize, "sans", WHITE, a, "c", stroke=6)

def route(c, cam, pts, prog, w=34, color=RED, a=1.0, flow_t=None):
    arrow(c, [cam.P(*q) for q in pts], prog, w, color, a, flow_t=flow_t)

def along(cam, pts, u):
    poly = catmull([cam.P(*q) for q in pts], 20)
    part, _ = partial(poly, clamp(u))
    q = part[-1]; qq = part[-2] if len(part) > 1 else part[-1]
    return float(q[0]), float(q[1]), math.degrees(math.atan2(q[1] - qq[1], q[0] - qq[0]))

def big_title(c, s, y, size=96, color=WHITE, a=1.0, face="serifbk", spacing=8):
    text(c, s, W / 2, y, size, face, color, a, "c", shadow=14, spacing=spacing)

def chip(c, s, x, y, a=1.0, color=GOLD, size=38, fill=(18, 14, 10)):
    if a <= 0: return
    f = font("sansm", size); tw = f.measureText(s)
    rr = skia.RRect.MakeRectXY(skia.Rect(x - tw / 2 - 22, y - size * 1.05, x + tw / 2 + 22, y + size * 0.45), 10, 10)
    c.drawRRect(rr, paint(fill, 0.78 * a)); c.drawRRect(rr, paint(color, 0.85 * a, stroke=2.5))
    text(c, s, x, y, size, "sansm", color, a, "c")

def dark_bg(c, x, vname="kanto", lon=139.4, lat=35.7, s=0.55, dim=0.66):
    cam = Cam(vname, lon + 0.01 * math.sin(x.gt * 0.05), lat, s * (1 + 0.006 * x.t))
    draw_map(c, cam, dim=dim)

def mech_tag(c, n, s, a, y=410):
    text(c, f"机制{n}", W / 2, y - 66, 40, "sansm", GOLD, a * 0.9, "c", spacing=10)
    text(c, s, W / 2, y + 10, 66, "serifbk", WHITE, a, "c", shadow=10)

def counter(c, val, x, y, size, a, color=GOLD, suffix="", face="serifbk"):
    text(c, f"{int(val):,}{suffix}", x, y, size, face, color, a, "c", shadow=12)

def quote_vertical(c, s, src, a, x0=None, size=84, top=430, reveal=1.0, maxcol=9, face="tcbk", srcsize=38):
    cols = [seg for seg in s.replace("，", "，|").replace("。", "。|").replace("、", "、|").replace("　", "|").split("|") if seg]
    out = []
    for seg in cols:
        if out and len(out[-1]) + len(seg) <= maxcol: out[-1] += seg
        else: out.append(seg)
    cols = out
    n = len(cols); colw = size * 1.45
    mh = max(len(q) for q in cols) * size * 1.08
    cw = n * colw + 120; ch = mh + 120
    cx = W / 2 if x0 is None else x0
    card(c, cx - cw / 2, top - 60, cw, ch + 70, a, fa=0.8)
    tot = sum(len(q) for q in cols); k = 0
    for i, q in enumerate(cols):
        xx = cx + cw / 2 - 60 - colw * (i + 0.5)
        for j, ch_ in enumerate(q):
            ca = a * clamp((tot * reveal - k) * 1.5) if reveal < 1 else a
            if ca > 0: vtext(c, ch_, xx, top + j * size * 1.08, size, face, PAPER, ca)
            k += 1
    text(c, "—— " + src, cx + cw / 2 - 40, top + ch + 40, srcsize, "tc", GOLD, a, "r")
    return top + ch + 40

# =================================================================== s0 hook
def dawn_scene(c, x, prog, show_castle=True, defenders=True, legend=False):
    t = x.t
    sky3(c, (26, 32, 46), (86, 92, 108), (206, 176, 138), 1060)
    # mist
    for k in range(3):
        c.drawRect(skia.Rect(0, 820 + k * 70, W, 900 + k * 70), paint((220, 200, 170), 0.06, blur=30))
    ridge(c, 11, 900, 40, (70, 78, 92), 0.9, rough=0.3)
    # Ishigakiyama ridge with castle
    ry = 1020
    ridge(c, 12, ry, 55, (44, 52, 56), 1.0, rough=0.25)
    cx = 600
    gy = ridge_y(12, ry, 55, cx, rough=0.25) + 6
    mound = skia.Path(); mound.moveTo(cx - 640, gy + 160); mound.quadTo(cx - 520, gy - 4, cx - 360, gy - 4)
    mound.lineTo(cx + 360, gy - 4); mound.quadTo(cx + 520, gy - 4, cx + 640, gy + 160); mound.close()
    c.drawPath(mound, paint((44, 52, 56)))
    if show_castle:
        c.save(); c.translate(cx, gy); c.scale(0.9, 0.9); c.translate(-cx, -gy)
        lit = 0.75 + 0.25 * clamp(prog * 1.5)
        c.drawCircle(cx, gy - 160, 300, paint((255, 214, 160), 0.10 * clamp(prog * 1.5), blur=80))
        castle(c, cx, gy, 1.0, 1.0, lit)
        c.restore()
    # trees on the ridge: each falls when prog passes its threshold
    rng = np.random.default_rng(5)
    xs = np.linspace(280, 930, 22)
    for i, tx in enumerate(xs):
        th = 0.06 + 0.9 * (i / len(xs)) + rng.uniform(-0.04, 0.04)
        fall = clamp((prog - th) / 0.08)
        ang = 92 * ein(fall) * (1 if i % 2 else -1) * rng.uniform(0.85, 1.0)
        ty = ridge_y(12, ry, 55, tx, rough=0.25) + 4
        hh = rng.uniform(190, 260)
        conifer(c, tx, ty + 30 * ein(fall), hh, (22, 30, 30), 1.0 - clamp((fall - 0.7) / 0.3), ang)
        if 0 < fall < 1:
            c.drawCircle(tx, ty - 20, 40 + 60 * fall, paint((200, 190, 170), 0.12 * (1 - fall), blur=18))
    # foreground: Odawara wall parapet + defenders looking up
    fy = 1500
    c.drawRect(skia.Rect(0, fy, W, H), paint((14, 14, 16)))
    for i in range(0, W + 60, 60):
        c.drawRect(skia.Rect(i, fy - 40, i + 34, fy), paint((14, 14, 16)))
    if defenders:
        for i, (dx, s) in enumerate([(140, 1.6), (300, 1.4), (820, 1.7), (960, 1.3)]):
            ashigaru(c, dx, fy + 10, s, (10, 10, 12), 1.0, spear=(i % 2 == 0))
    vignette(c, 0.55)

@scenic
def v_ichiya(c, x):
    t = x.t
    prog = 0.25 + 0.75 * eout(t / 6.5)
    dawn_scene(c, x, prog)
    a = 1.0
    big_title(c, "一夜城", 430, 150, PAPERL, a, spacing=26)
    text(c, "小田原 · 1590", W / 2, 520, 44, "sansm", GOLD, a * 0.95, "c", spacing=8)
    if x.on("a02"):
        pa = x.p("a02", 0.4)
        chip(c, "传说 ×   真实 √", W / 2, 640, pa, GOLD, 40)

def v_compare(c, x):
    paper_bg(c, dark=0.25)
    a = clamp(x.t / 0.4)
    # left: Sunomata legend (faded sketch)
    card(c, 60, 400, 460, 860, a, fa=0.6, border=(120, 110, 96))
    text(c, "墨俣一夜城", 290, 480, 52, "serifbk", (200, 190, 170), a, "c")
    text(c, "第一集 · 传说", 290, 540, 34, "sansm", (170, 160, 140), a, "c")
    c.save(); c.translate(290, 980); c.scale(0.55, 0.55)
    castle(c, 0, 0, 0.8, a * 0.35, 0.4, walls=False)
    c.restore()
    text(c, "？", 290, 900, 220, "serifbk", (200, 180, 140), a * 0.55, "c")
    text(c, "同时代可靠史料", 290, 1110, 36, "sans", (210, 200, 180), a, "c")
    text(c, "找不到记载", 290, 1160, 40, "sansm", (230, 140, 110), a, "c")
    # right: Ishigakiyama, real
    b = clamp((x.t - 1.0) / 0.5)
    card(c, 560, 400, 460, 860, b, fa=0.72, border=GOLD)
    text(c, "石垣山城", 790, 480, 52, "serifbk", PAPERL, b, "c")
    text(c, "本集 · 1590", 790, 540, 34, "sansm", GOLD, b, "c")
    ishigaki(c, 610, 970, 760, 980, b, (176, 166, 148), (74, 68, 60))
    text(c, "石垣遗址至今尚存", 790, 1060, 36, "sans", WHITE, b, "c")
    text(c, "国家史迹 · 发掘出土瓦片", 790, 1110, 34, "sans", WHITE, b, "c")
    text(c, "真的", 790, 1190, 56, "serifbk", GOLD, b, "c")

@mapbeat
def v_mobilize(c, x):
    cam = cam_lerp("japan", (136.6, 35.2, 0.50), (137.6, 35.3, 0.56), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    k = eout(x.t / 2.2)
    route(c, cam, TOKAIDO, k, 40, RED, flow_t=x.t)
    route(c, cam, NORTHWAY, eout((x.t - 0.6) / 2.2), 30, RED, 0.9, flow_t=x.t)
    territory(c, cam, HOJO, CYAN, clamp(x.t / 0.6), 0.22)
    X, Y = cam.city("京都"); red_marker(c, X, Y, 1, x.t, 1.0, "京都", "d")
    X, Y = cam.city("小田原城"); city_marker(c, X, Y, "小田原", "lit", 1, x.t, 1.1, "r", 40)
    X, Y = cam.P(139.6, 36.2); region_label(c, "北条", X, Y, 60, 1, CYAN)
    v = 210000 * eout(x.t / 2.0)
    counter(c, v, W / 2, 470, 128, 1.0, RED)
    text(c, "约 21 万人 · 推定总数", W / 2, 540, 40, "sansm", WHITE, 1, "c", stroke=6)

@mapbeat
def v_fleet(c, x):
    cam = cam_lerp("japan", (137.4, 34.7, 0.56), (138.2, 34.8, 0.62), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.2)
    k = eout(x.t / 2.5)
    route(c, cam, SEAWAY, k, 30, RED, 0.9, flow_t=x.t)
    for i in range(9):
        u = (k * 0.95 - i * 0.075)
        if u <= 0: continue
        bx, by, ang = along(cam, SEAWAY, u)
        boat(c, bx + 18 * math.sin(i * 2.3), by + 30 + 14 * math.cos(i * 1.7), 0.42, (24, 18, 16), 0.95, sail=(230, 214, 186), flip=False)
    text(c, "海路 · 上千艘船", W / 2, 470, 76, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "运兵 · 运粮", W / 2, 545, 44, "sansm", GOLD, clamp((x.t - 1.2) / 0.5), "c", stroke=6)

@mapbeat
def v_grain(c, x):
    cam = Cam("japan", 137.7, 34.9, 0.6)
    mapframe(c, cam, x, dim=0.15)
    territory(c, cam, HOJO, CYAN, 1, 0.2)
    # gold particle flows along both lines
    for pts, n in ((TOKAIDO, 40), (SEAWAY, 46)):
        for i in range(n):
            u = ((x.t * 0.18 + i / n) % 1.0)
            px, py, _ = along(cam, pts, u)
            c.drawCircle(px, py, 7, paint(GOLDW, 0.85, blur=2)); c.drawCircle(px, py, 16, paint(GOLDW, 0.18, blur=8))
    X, Y = cam.city("骏府")
    nb = int(1 + 14 * eout(x.t / 3))
    for i in range(nb):
        bale(c, 330 + (i % 5) * 100, 1300 - (i // 5) * 56, 1.0, 1.0)
    counter(c, 200000 * eout(x.t / 2.4), W / 2, 470, 120, 1, GOLD, " 石+")
    text(c, "开战之前 · 军粮先行", W / 2, 545, 42, "sansm", WHITE, 1, "c", stroke=6)

def odawara_scene(c, x, gates=0.0, siege=None, lit=0.8, dusk=False):
    """Odawara castle front view, siege camps optional"""
    if dusk: sky3(c, (20, 22, 34), (70, 56, 62), (170, 110, 70), 1150)
    else: sky3(c, (24, 30, 44), (70, 80, 96), (150, 144, 130), 1150)
    ridge(c, 21, 1000, 60, (52, 60, 70), 1.0)
    ridge(c, 22, 1140, 30, (34, 40, 44), 1.0, rough=0.2)
    castle(c, W / 2, 1220, 1.0, 1.0, lit)
    c.drawRect(skia.Rect(0, 1220, W, H), paint((26, 26, 24)))
    # sogamae earthwork line
    c.drawRect(skia.Rect(0, 1290, W, 1310), paint((60, 54, 44)))

@scenic
def v_oldway(c, x):
    odawara_scene(c, x)
    t = x.t
    # besieging camps arrive then leave (two cycles)
    t8 = x.L("a08")[0]
    for k, (yr, nm, t0) in enumerate([("1561", "上杉谦信", t8 - 0.3), ("1569", "武田信玄", t8 + 1.3)]):
        u = clamp((t - t0) / 1.2); leave = clamp((t - t0 - 1.4) / 1.2)
        a = u * (1 - leave)
        if a <= 0: continue
        for i in range(9):
            xx = 80 + i * 110 + (-1 if k else 1) * 300 * leave
            ashigaru(c, xx, 1460 + (i % 2) * 30, 0.9, (30, 22, 18), a, banner=(110, 100, 80))
        text(c, f"{yr} {nm}", W / 2, 1380, 52, "serifbk", WHITE, a, "c", stroke=7)
        if leave > 0.1: text(c, "撤兵", W / 2 + (-1 if k else 1) * 260, 1300, 46, "sansm", GOLD, leave * (1 - leave) * 4, "c", stroke=6)
    big_title(c, "关门 · 死守 · 等对方粮尽", 430, 64, PAPERL, clamp(t / 0.5), spacing=4)

def v_oldway2(c, x):
    paper_bg(c, dark=0.35)
    a = clamp(x.t / 0.3)
    big_title(c, "这一次", 520, 80, WHITE, a)
    big_title(c, "对方的粮，比你多", 650, 92, GOLD, clamp((x.t - 0.5) / 0.4))
    # two granaries as bars
    k = eout((x.t - 0.6) / 1.2)
    c.drawRect(skia.Rect(240, 1300 - 220, 420, 1300), paint(CYAN, 0.9 * a))
    text(c, "北条", 330, 1360, 46, "serifbk", CYAN, a, "c")
    hh = 220 + 300 * k
    c.drawRect(skia.Rect(660, 1300 - hh, 840, 1300), paint(RED, 0.95 * a))
    text(c, "丰臣", 750, 1360, 46, "serifbk", RED, a, "c")
    text(c, "（示意）", W / 2, 1420, 30, "sans", (200, 190, 170), a, "c")

def v_question(c, x):
    paper_bg(c, dark=0.45)
    t10, t11, t12 = x.L("a10")[0], x.L("a11")[0], x.L("a12")[0]
    if x.t < t11:
        for i, (s, colr) in enumerate([("21 万大军", WHITE), ("围城 3 个月", WHITE), ("几乎没打", GOLD), ("北条开城", CYAN)]):
            big_title(c, s, 640 + i * 150, 96, colr, clamp((x.t - i * 0.9) / 0.4))
    else:
        big_title(c, "两个问题", 560, 72, GOLD, x.p("a11", 0.4))
        card(c, 90, 680, W - 180, 220, x.p("a11", 0.4), fa=0.7)
        text(c, "① 一场仗，怎样不打就赢？", W / 2, 810, 58, "serifbk", WHITE, x.p("a11", 0.4), "c")
        card(c, 90, 960, W - 180, 220, x.p("a12", 0.4), fa=0.7)
        text(c, "② 赢了，怎样不再回到战国？", W / 2, 1090, 56, "serifbk", WHITE, x.p("a12", 0.4), "c")

def v_katana_tease(c, x):
    bg_grad(c, (14, 12, 12), (4, 4, 6))
    k = eout(x.t / 1.5)
    katana(c, 160, 1040, 820, -8, 1.0, glow=0.0)
    # glint sweep
    gx = 160 + 900 * clamp((x.t - 0.5) / 1.2)
    c.drawCircle(gx, 1040 - (gx - 160) * 0.14, 60, paint((255, 250, 230), 0.5 * (1 - abs(clamp((x.t - 0.5) / 1.2) - 0.5) * 2), blur=24))
    big_title(c, "后半段的答案", 620, 64, WHITE, k)
    big_title(c, "一把刀", 760, 128, GOLD, clamp((x.t - 0.8) / 0.5), spacing=30)

# =================================================================== s1 background
@mapbeat
def v_japan_west(c, x):
    cam = cam_lerp("japan", (134.5, 34.2, 0.46), (136.0, 34.8, 0.5), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    t2 = x.L("b02")[0]
    for (lon, lat, nm, yr, dt) in [(133.5, 33.6, "四国", "1585", 0.0), (130.8, 32.5, "九州", "1587", 1.8)]:
        a = clamp((x.t - t2 - dt) / 0.6)
        X, Y = cam.P(lon, lat)
        c.drawCircle(X, Y, 150, paint(RED, 0.30 * a, blur=50))
        text(c, nm, X, Y, 62, "serifbk", WHITE, a, "c", stroke=7)
        text(c, yr, X, Y + 62, 44, "sansm", GOLD, a, "c", stroke=6)
    X, Y = cam.city("大坂"); red_marker(c, X, Y, 1, x.t, 1.2, "大坂", "d")
    if x.on("b01b"):
        text(c, "尾张小卒 → 关白", W / 2, 470, 66, "serifbk", WHITE, x.p("b01b", 0.5), "c", shadow=10)
        text(c, "三十多年", W / 2, 545, 44, "sansm", GOLD, x.p("b01b", 0.5), "c", stroke=6)
    if x.on("b02"):
        a = clamp((x.t - t2 - 3.0) / 0.6)
        text(c, "西日本 · 尽在掌握", W / 2, 1380, 60, "serifbk", RED, a, "c", shadow=10)

@mapbeat
def v_kanto(c, x):
    cam = cam_lerp("kanto", (139.3, 35.6, 0.45), (139.4, 35.75, 0.5), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    k = eout(x.t / 2.0)
    territory(c, cam, HOJO, CYAN, 1, 0.22, prog=k)
    X, Y = cam.P(139.45, 36.0); region_label(c, "北条领国", X, Y, 70, k, CYAN)
    X, Y = cam.city("小田原城"); city_marker(c, X, Y, "小田原", "lit", 1, x.t, 1.3, "r", 44)
    if x.on("b04"):
        a = x.p("b04", 0.5)
        names = ["早云", "氏纲", "氏康", "氏政", "氏直"]
        for i, nm in enumerate(names):
            chip(c, nm, 170 + i * 185, 1360, clamp((x.t - x.L("b04")[0] - i * 0.25) / 0.4), CYAN, 42)
        text(c, "五代 · 近百年", W / 2, 1460, 54, "serifbk", WHITE, a, "c", stroke=7)
    text(c, "关东", W / 2, 470, 90, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=12, spacing=20)

@mapbeat
def v_sogamae(c, x):
    cam = cam_lerp("odawara", (139.15, 35.255, 0.42), (139.155, 35.255, 0.5), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    # sogamae ring (schematic ~9 km)
    X, Y = cam.city("小田原城")
    k = eout(x.t / 2.5)
    pts = [(139.128, 35.262), (139.140, 35.272), (139.158, 35.275), (139.172, 35.268), (139.176, 35.255), (139.170, 35.244), (139.150, 35.240), (139.135, 35.246)]
    territory(c, cam, pts, CYAN, 1, 0.16, prog=k)
    city_marker(c, X, Y, "小田原城", "lit", 1, x.t, 1.3, "u", 44)
    text(c, "总构 · 约 9 公里", W / 2, 470, 70, "serifbk", WHITE, k, "c", shadow=10)
    if x.on("b06"):
        t6 = x.L("b06")[0]
        for i, (nm, ang, dt) in enumerate([("1561 上杉谦信", -2.4, 0.0), ("1569 武田信玄", 2.6, 2.8)]):
            u = clamp((x.t - t6 - dt) / 1.4); back = clamp((x.t - t6 - dt - 1.8) / 1.2)
            a = u * (1 - 0.7 * back)
            if a <= 0: continue
            sx, sy = X + math.cos(ang) * 720, Y + math.sin(ang) * 520 - 200
            ex, ey = X + math.cos(ang) * 260, Y + math.sin(ang) * 200 - 60
            arrow(c, [(sx, sy), ((sx + ex) / 2, (sy + ey) / 2 - 40), (ex, ey)], eout(u), 34, (190, 150, 120), a)
            if back > 0:
                arrow(c, [(ex, ey + 50), ((sx + ex) / 2, (sy + ey) / 2 + 30), (sx, sy + 60)], eout(back), 22, (150, 150, 150), back * 0.8)
            text(c, nm, min(max(sx, 200), W - 200), max(sy - 40, 600), 42, "sansm", WHITE, a, "c", stroke=6)
        text(c, "两次闭门 · 两次退兵", W / 2, 1380, 58, "serifbk", CYAN, clamp((x.t - t6 - 5) / 0.6), "c", shadow=8)

def v_bujirei(c, x):
    paper_bg(c, dark=0.3)
    a = clamp(x.t / 0.4)
    scroll_doc(c, 230, 420, 620, 640, a)
    vcol(c, "惣無事", W / 2, 470, 120, a, (40, 28, 20))
    c.drawRect(skia.Rect(640, 900, 720, 980), paint((180, 40, 30), 0.85 * a))
    text(c, "停止私战", 290, 1180, 50, "serifbk", WHITE, a, "c", stroke=6)
    text(c, "纠纷 → 中央裁决", 760, 1180, 50, "serifbk", WHITE, clamp((x.t - 1.0) / 0.5), "c", stroke=6)
    if x.on("b08"):
        b = x.p("b08", 0.5)
        card(c, 90, 1240, W - 180, 200, b, fa=0.85, border=GOLD)
        seal(c, 130, 1300, "学界争论", b, 32)
        text(c, "统一法令？还是一封封书信？", W / 2, 1390, 50, "serifbk", GOLD, b, "c")

@mapbeat
def v_nagurumi(c, x):
    cam = cam_lerp("kanto", (139.0, 36.4, 0.62), (139.02, 36.6, 0.9), clamp(x.t / 4))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.18)
    X, Y = cam.city("沼田城"); city_marker(c, X, Y, "沼田城", "lit", 1, x.t, 1.0, "r", 38)
    Xn, Yn = cam.city("名胡桃城")
    took = x.p("b09", 0.8, 3.0) if x.on("b09") else 0
    if took < 1:
        red_marker(c, Xn, Yn, 1 - took, x.t, 1.1, "名胡桃城（真田）", "l", 38)
    if took > 0:
        arrow(c, [(X + 10, Y + 30), ((X + Xn) / 2 + 30, (Y + Yn) / 2 + 60), (Xn + 14, Yn + 10)], eout(took), 26, CYAN)
        flash(c, Xn, Yn, took, CYAN, 140)
        city_marker(c, Xn, Yn, "名胡桃城", "lit", took, x.t, 1.1, "l", 38)
    text(c, "1589 · 秋", W / 2, 470, 70, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)
    if x.on("b10"):
        text(c, "秀吉刚刚裁定的归属", W / 2, 1360, 54, "serifbk", WHITE, x.p("b10", 0.5), "c", stroke=7)
    if x.on("b11"):
        chip(c, "宣战朱印状", W / 2, 1460, x.p("b11", 0.5), RED, 48)
    if x.on("b12"):
        seal(c, 90, 1250, "另一种观点：早有准备", x.p("b12", 0.5), 32)

# =================================================================== s2 logistics
@mapbeat
def v_march(c, x):
    cam = cam_lerp("japan", (136.6, 35.1, 0.52), (138.0, 35.1, 0.6), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.2)
    k = eout(x.t / 3.0)
    route(c, cam, TOKAIDO, k, 46, RED, flow_t=x.t)
    for nm, side in (("京都", "d"), ("骏府", "d")):
        X, Y = cam.city(nm); red_marker(c, X, Y, 1, x.t, 0.9, nm, side)
    X, Y = cam.city("小田原城"); city_marker(c, X, Y, "小田原", "lit", 1, x.t, 1.1, "r", 40)
    text(c, "1590 · 3 月", W / 2, 470, 80, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "东海道 · 大军东进", W / 2, 545, 44, "sansm", RED, 1, "c", stroke=6)

def v_ledger(c, x):
    paper_bg(c, dark=0.3)
    a = clamp(x.t / 0.4)
    big_title(c, "先算一笔账", 450, 72, WHITE, a)
    t3, t4 = x.L("c03")[0], x.L("c03")[0]
    if x.on("c03"):
        b = x.p("c03", 0.5)
        card(c, 80, 540, W - 160, 300, b, fa=0.85)
        text(c, "米 · 杂粮", 260, 650, 46, "sansm", PAPER, b, "c")
        counter(c, 200000 * eout(x.p("c03", 2.0)), 640, 670, 96, b, GOLD, " 石+")
        text(c, "天正大判", 260, 790, 46, "sansm", PAPER, clamp((x.t - t3 - 3.5) / 0.5), "c")
        counter(c, 10000 * eout(clamp((x.t - t3 - 3.5) / 1.5)), 640, 800, 84, clamp((x.t - t3 - 3.5) / 0.5), GOLDW, " 枚")
        seal(c, 110, 900, "据记载 · 长束正家经办", b, 30)
        n = int(1 + 23 * eout(x.p("c03", 3.0)))
        for i in range(n):
            bale(c, 170 + (i % 8) * 106, 1260 - (i // 8) * 58, 1.0, 1.0)
    if x.on("c04"):
        b = x.p("c04", 0.5)
        card(c, 80, 1290, W - 160, 140, b, fa=0.85, border=GOLD)
        text(c, "1 石 ≈ 1 人 1 年口粮", W / 2, 1380, 58, "serifbk", GOLD, b, "c")

@mapbeat
def v_navy(c, x):
    cam = cam_lerp("japan", (137.2, 34.6, 0.6), (138.9, 34.95, 0.9), clamp(x.t / max(x.T, 1)))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.2)
    k = eout(x.t / 3.5)
    route(c, cam, SEAWAY, k, 32, RED, 0.9, flow_t=x.t)
    for i in range(11):
        u = (k * 0.97 - i * 0.065)
        if u <= 0: continue
        bx, by, ang = along(cam, SEAWAY, u)
        boat(c, bx + 22 * math.sin(i * 2.3), by + 30 + 18 * math.cos(i * 1.7), 0.45, (24, 18, 16), 0.95, sail=(230, 214, 186))
    text(c, "水军 · 千艘 · 两万余人", W / 2, 470, 66, "serifbk", WHITE, 1, "c", shadow=10)
    if x.on("c06"):
        nm = ["九鬼", "长宗我部", "胁坂", "加藤", "毛利"]
        for i, s in enumerate(nm):
            chip(c, s, 150 + i * 195, 560, clamp((x.t - x.L("c06")[0] - i * 0.3) / 0.4), RED, 36)
    if x.on("c07"):
        b = x.p("c07", 0.6)
        X, Y = cam.city("小田原城")
        p = paint(RED, 0.9 * b, stroke=6); p.setPathEffect(skia.DashPathEffect.Make([18, 14], x.t * 40))
        c.drawArc(skia.Rect(X - 260, Y - 160, X + 260, Y + 360), 200, 150 * b, False, p)
        text(c, "① 运粮   ② 封锁海面", W / 2, 1380, 58, "serifbk", GOLD, b, "c", stroke=7)

def v_mech1(c, x):
    dark_bg(c, x, "japan", 137.5, 35.0, 0.5, 0.72)
    a = clamp(x.t / 0.4)
    mech_tag(c, "一", "补给：守城的算术", a)
    # chart: x = months, two supply lines
    x0, y0, w, h = 140, 620, 800, 520
    c.drawLine(x0, y0 + h, x0 + w, y0 + h, paint(WHITE, a * 0.8, stroke=3))
    c.drawLine(x0, y0, x0, y0 + h, paint(WHITE, a * 0.8, stroke=3))
    text(c, "围城时间 →", x0 + w, y0 + h + 60, 36, "sans", WHITE, a, "r")
    text(c, "围城方存粮", x0 + 10, y0 - 20, 36, "sans", WHITE, a, "l")
    # old assumption: drops fast
    kk = eout(x.t / 2.5)
    pts = [(x0 + w * u, y0 + h * (0.15 + 0.85 * min(1, u * 2.2))) for u in np.linspace(0, kk, 30)]
    if len(pts) > 1:
        pa = skia.Path(); pa.moveTo(*pts[0])
        for q in pts[1:]: pa.lineTo(*q)
        c.drawPath(pa, paint(CYAN, a, stroke=7))
    text(c, "过去的对手：几个月就见底", x0 + w * 0.47, y0 + h * 0.86, 38, "sansm", CYAN, a * kk, "l", stroke=5)
    if x.on("c10"):
        k2 = eout(x.p("c10", 2.5))
        pts = [(x0 + w * u, y0 + h * (0.12 + 0.12 * u)) for u in np.linspace(0, k2, 30)]
        pa = skia.Path(); pa.moveTo(*pts[0])
        for q in pts[1:]: pa.lineTo(*q)
        c.drawPath(pa, paint(RED, 0.4, stroke=22, blur=10)); c.drawPath(pa, paint(RED, 1, stroke=8))
        text(c, "丰臣：背后是统一的财政", x0 + w * 0.08, y0 + h * 0.05, 40, "sansm", RED, k2, "l", stroke=5)
    if x.on("c11"):
        b = x.p("c11", 0.5)
        text(c, "比谁耗得久 —— 这道题从一开始就算错了", W / 2, 1300, 42, "serifbk", GOLD, b, "c", stroke=6)
    text(c, "示意", x0 + w - 10, y0 + 40, 28, "sans", (200, 190, 170), a * 0.8, "r")

HOJO_CASTLES = ["小田原城", "山中城", "韭山城", "下田城", "八王子城", "钵形城", "松井田城", "忍城", "玉绳城", "江户", "岩槻城", "沼田城"]

def kanto_net(c, cam, x, states, line_a=1.0, cut=0.0):
    X0, Y0 = cam.city("小田原城")
    for nm in HOJO_CASTLES[1:]:
        X, Y = cam.city(nm)
        st = states.get(nm, "lit")
        la = line_a * (0.55 if st == "lit" else 0.15) * (1 - cut)
        c.drawLine(X0, Y0, X, Y, paint(CYAN, la, stroke=2.5))
    for nm in HOJO_CASTLES:
        st = states.get(nm, "lit")
        if st == "hide": continue
        X, Y = cam.city(nm)
        side = {"山中城": "l", "韭山城": "l", "下田城": "r", "松井田城": "l", "沼田城": "r", "忍城": "r", "钵形城": "l", "江户": "r", "岩槻城": "r", "玉绳城": "r", "八王子城": "l"}.get(nm, "r")
        city_marker(c, X, Y, nm, st if st != "red" else "fallen", 1, x.t, 1.2 if nm == "小田原城" else 0.85, side, 34)

@mapbeat
def v_network(c, x):
    cam = cam_lerp("kanto", (139.3, 35.7, 0.46), (139.3, 35.7, 0.5), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.16)
    k = eout(x.t / 2.0)
    kanto_net(c, cam, x, {}, k)
    text(c, "支城网", W / 2, 470, 84, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10, spacing=16)
    if x.on("c14"):
        # garrison dots stream into Odawara
        X0, Y0 = cam.city("小田原城")
        u = x.p("c14", 3.0)
        for i, nm in enumerate(HOJO_CASTLES[1:]):
            X, Y = cam.city(nm)
            for j in range(4):
                v = clamp(u * 1.3 - j * 0.1)
                c.drawCircle(lerp(X, X0, eout(v)), lerp(Y, Y0, eout(v)), 7, paint(CYAN, 0.9 * (1 - v * 0.6)))
        text(c, "主力 · 城主 → 全部调进本城", W / 2, 1320, 52, "serifbk", CYAN, x.p("c14", 0.6), "c", stroke=7)
        text(c, "支城只剩临时征来的老弱", W / 2, 1395, 44, "sansm", WHITE, x.p("c14", 0.6, 2.0), "c", stroke=6)
    if x.on("c14b"):
        b = x.p("c14b", 0.5)
        card(c, 90, 520, W - 180, 170, b, fa=0.85, border=CYAN)
        text(c, "征召 15–70 岁男子 · 收寺钟铸炮", W / 2, 615, 46, "serifbk", WHITE, b, "c")
        text(c, "家底：只有关东这一块", W / 2, 670, 36, "sansm", CYAN, b, "c")

@mapbeat
def v_yamanaka(c, x):
    cam = cam_lerp("kanto", (139.05, 35.2, 0.9), (139.03, 35.19, 1.5), clamp(x.t / 4))
    mapframe(c, cam, x)
    X, Y = cam.city("山中城")
    k = eout(clamp((x.t - 0.8) / 2.0))
    arrow(c, [(X - 520, Y + 160), (X - 260, Y + 60), (X - 30, Y + 6)], k, 50, RED, flow_t=x.t)
    fallen = x.t > 0.8 + 2.4
    if fallen: flash(c, X, Y, (x.t - 3.2) / 1.0, RED, 200)
    city_marker(c, X, Y, "山中城", "fallen" if fallen else "lit", 1, x.t, 1.4, "u", 46)
    Xo, Yo = cam.city("小田原城"); city_marker(c, Xo, Yo, "小田原", "lit", 1, x.t, 1.2, "r", 40)
    text(c, "3 月 29 日 · 箱根", W / 2, 470, 70, "serifbk", WHITE, 1, "c", shadow=10)
    if fallen: big_title(c, "不到一天 · 城破", 1360, 72, RED, clamp((x.t - 3.2) / 0.5))

@mapbeat
def v_north(c, x):
    cam = cam_lerp("kanto", (138.95, 36.15, 0.62), (139.1, 36.05, 0.66), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.16)
    k = eout(x.t / 2.5)
    route(c, cam, [(138.05, 36.6), (138.45, 36.45), (138.70, 36.36), (138.78, 36.33)], k, 40, RED, flow_t=x.t)
    Xu, Yu = cam.city("碓冰岭"); text(c, "碓冰岭", Xu - 30, Yu - 50, 38, "sansm", WHITE, k, "c", stroke=6)
    opened = x.t > x.L("c16")[0] + 3.5
    castles(c, cam, x, [("松井田城", "fallen" if opened else "siege", 1, "d"), ("钵形城", "lit", 1, "r"), ("忍城", "lit", 1, "r"), ("八王子城", "lit", 1, "r")], 1.0, 36)
    text(c, "北方军 · 前田利家 / 上杉景胜", W / 2, 470, 54, "serifbk", WHITE, 1, "c", shadow=10)
    if opened:
        u = clamp((x.t - x.L("c16")[0] - 3.8) / 2.0)
        Xm, Ym = cam.city("松井田城"); Xh, Yh = cam.city("钵形城")
        p = paint(GOLD, 0.95 * u, stroke=5); p.setPathEffect(skia.DashPathEffect.Make([16, 12], -x.t * 40))
        pa = skia.Path(); pa.moveTo(Xm, Ym); pa.quadTo((Xm + Xh) / 2, min(Ym, Yh) - 120, Xh, Yh); c.drawPath(pa, p)
        text(c, "降将带路 · 劝降", W / 2, 1380, 56, "serifbk", GOLD, u, "c", stroke=7)

@mapbeat
def v_dominoes(c, x):
    cam = Cam("kanto", 139.3, 35.75, 0.5)
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.14)
    t18 = x.L("c18")[0]
    seq = [("松井田城", -99), ("玉绳城", -2.0), ("江户", -1.5), ("岩槻城", -1.0), ("下田城", -0.6), ("沼田城", -0.3),
           ("钵形城", 0.3), ("八王子城", 2.6), ("韭山城", 5.0)]
    st = {"山中城": "fallen"}
    for nm, dt in seq:
        if x.t >= t18 + dt: st[nm] = "fallen"
    kanto_net(c, cam, x, st)
    for nm, dt, lab in [("钵形城", 0.3, "6.14 开城"), ("八王子城", 2.6, "6.23 攻破"), ("韭山城", 5.0, "6.24 开城")]:
        u = clamp((x.t - t18 - dt) / 0.4)
        if u > 0:
            X, Y = cam.city(nm); flash(c, X, Y, (x.t - t18 - dt) / 0.9, RED, 120)
            text(c, lab, X, Y + 70, 36, "sansm", GOLD, u, "c", stroke=6)
    text(c, "一座座支城", W / 2, 470, 72, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "开城 / 攻破", W / 2, 545, 44, "sansm", GOLD, 1, "c", stroke=6)

@mapbeat
def v_oshi(c, x):
    cam = cam_lerp("kanto", (139.4, 36.15, 0.9), (139.45, 36.14, 1.6), clamp(x.t / 4))
    mapframe(c, cam, x)
    X, Y = cam.city("忍城")
    k = eout(x.t / 2.5)
    # flood ring
    c.drawCircle(X, Y, 200 * k + 1, paint((70, 130, 170), 0.35, blur=20))
    p = paint((120, 180, 210), 0.8 * k, stroke=6); p.setPathEffect(skia.DashPathEffect.Make([22, 14], x.t * 20))
    c.drawCircle(X, Y, 230 * k + 1, p)
    city_marker(c, X, Y, "忍城", "lit", 1, x.t, 1.5, "u", 50)
    text(c, "石田三成 · 筑堤水攻", W / 2, 470, 60, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "撑到了小田原投降之后", W / 2, 1380, 56, "serifbk", CYAN, clamp((x.t - 3) / 0.6), "c", stroke=7)

@mapbeat
def v_isolated(c, x):
    cam = cam_lerp("kanto", (139.3, 35.75, 0.5), (139.2, 35.4, 0.62), clamp(x.t / max(x.T, 1)))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.1)
    st = {nm: "fallen" for nm in HOJO_CASTLES[1:]}; st["忍城"] = "lit"
    cut = eout(x.t / 3.0)
    kanto_net(c, cam, x, st, 1.0, cut)
    X, Y = cam.city("小田原城")
    ring = paint(RED, 0.9, stroke=8); ring.setPathEffect(skia.DashPathEffect.Make([20, 12], x.t * 30))
    c.drawCircle(X, Y, 120 - 20 * cut, ring)
    text(c, "网，被一根一根剪断", W / 2, 470, 66, "serifbk", WHITE, 1, "c", shadow=10)
    big_title(c, "孤城", 1380, 110, CYAN, clamp((x.t - 2) / 0.6), spacing=40)
