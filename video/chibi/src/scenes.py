# -*- coding: utf-8 -*-
"""赤壁 · 质感重做：深色晕渲动态地图 + 沙盘推演。时间全部挂在旧时码（句级）上。"""
import math, json, random, numpy as np, skia
from geo import W, H, Cam, Base, merc
from gfx import *

ROOT = '/tmp/claude-0/-home-user-cvxpy/9a4786ae-0518-5e11-ad24-b93d03b9d022/scratchpad/'
DEM = ROOT + 'chibi2/dem/'
TLJ = json.load(open(ROOT + 'chibi/timeline_edge.json'))
NSH = len(TLJ)
TAIL_EXTRA = 6.0                      # 片尾静音延长（不动任何句子时码）
TOTAL = TLJ[-1]['start'] + TLJ[-1]['dur'] + TAIL_EXTRA
def S(i): return TLJ[i]['start']
def E(i): return TLJ[i]['start'] + TLJ[i]['dur'] + (TAIL_EXTRA if i == NSH - 1 else 0)
def D(i): return E(i) - S(i)
def shot_at(t):
    lo, hi = 0, NSH - 1
    while lo < hi:
        m = (lo + hi + 1) // 2
        if TLJ[m]['start'] <= t: lo = m
        else: hi = m - 1
    return lo
def win(t, i0, i1=None, din=0.45, dout=0.45, o0=0.0, o1=0.0):
    """shot i0 开始 到 shot i1 结束 之间可见。"""
    i1 = i0 if i1 is None else i1
    return fade(t, S(i0) + o0, E(i1) + o1, din, dout)

B7 = Base(DEM + 'base7.png'); B9 = Base(DEM + 'base9.png'); B10 = Base(DEM + 'base10.png')

# ------------------------------------------------------------------ 地理
CITY = {'襄阳': (112.14, 32.00), '樊': (112.15, 32.07), '新野': (112.36, 32.52), '宛': (112.53, 33.00), '当阳': (111.79, 30.82),
        '江陵': (112.19, 30.35), '夏口': (114.28, 30.57), '柴桑': (115.98, 29.71), '鄱阳': (116.68, 29.00), '赤壁': (113.67, 29.87),
        '乌林': (113.57, 29.96), '华容': (112.80, 30.27), '巴丘': (113.10, 29.37), '合肥': (117.27, 31.86), '许': (113.82, 34.03)}
RIV = json.load(open(DEM + 'rivers.json')); LAK = json.load(open(DEM + 'lakes.json'))
def _part(name, lon0):
    for f in RIV:
        if f['name'] == name:
            for p in f['parts']:
                if abs(p[0][0] - lon0) < 0.03: return [tuple(q) for q in p]
    raise KeyError(name)
YZ = _part('Chang Jiang', 103.85) + _part('Chang Jiang', 113.13)[::-1][1:] + _part('Yangtze', 114.303)[::-1][1:] + _part('Yangtze', 114.296)[1:]
YZ = [q for q in YZ if 109.0 < q[0] < 119.0]
OTHER = [(f['name'], p) for f in RIV if f['name'] in ('Han', 'Xiang', 'Gan', 'Yuan', 'Huai') for p in f['parts']]
LAKES = [p for f in LAK if f['name'] in ('Dongting Hu', 'Poyang Hu', 'Hong Hu', 'Liangzi Hu', 'Chao Hu', 'Po Hu', 'Long Hu', 'Daguan Hu') for p in f['parts']]
# 沿长江的弧长参数
_L = [0.0]
for k in range(1, len(YZ)): _L.append(_L[-1] + math.hypot((YZ[k][0] - YZ[k - 1][0]) * 0.87, YZ[k][1] - YZ[k - 1][1]))
def yz_u(lon):
    best = min(range(len(YZ)), key=lambda k: abs(YZ[k][0] - lon) + (0 if True else 0))
    return _L[best] / _L[-1]
def yz_at(u):
    d = clamp(u) * _L[-1]
    for k in range(1, len(YZ)):
        if _L[k] >= d:
            r = (d - _L[k - 1]) / max(1e-9, _L[k] - _L[k - 1]); a, b = YZ[k - 1], YZ[k]
            return (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r), math.atan2(b[1] - a[1], (b[0] - a[0]) * 0.87)
    return YZ[-1], 0.0
def yz_seg(lon0, lon1, n=40):
    u0, u1 = yz_u(lon0), yz_u(lon1)
    return [yz_at(u0 + (u1 - u0) * k / n)[0] for k in range(n + 1)]
U_JL, U_WL, U_XK, U_CS = yz_u(112.19), yz_u(113.58), yz_u(114.29), yz_u(115.98)

# ------------------------------------------------------------------ 镜头
AY = 700
def CM(lon, lat, span, ay=AY): return Cam(lon, lat, span, ay=ay)
C_OPEN = CM(112.95, 30.05, 2.3)
C_OPEN2 = CM(114.3, 30.0, 3.9)
C_CS = CM(115.95, 29.8, 1.25)
C_MID = CM(114.0, 30.7, 7.2)
C_XY = CM(112.2, 31.95, 1.9)
C_JL = CM(112.35, 30.35, 1.6)
C_EAST = CM(115.1, 30.15, 3.4)
C_NORTH = CM(112.45, 32.3, 2.6)
C_CHASE = CM(112.05, 31.35, 2.3)
C_HXK = CM(113.1, 30.65, 3.6)
C_FRONT = CM(114.1, 30.25, 4.6)
C_NW = CM(111.3, 32.4, 9.5)
C_SAND = CM(113.6, 30.25, 3.9)
C_BMID = CM(113.45, 30.0, 1.5)
C_BAT = CM(113.62, 29.92, 0.62)
C_BAT2 = CM(113.60, 29.93, 0.46)
C_RET = CM(112.92, 30.15, 2.25)
C_HF = CM(115.4, 30.75, 6.6)
C_END = CM(114.1, 30.2, 5.2)

KEYS = []
def k(t0, t1, cam): KEYS.append((t0, t1, cam))
def build_keys():
    k(0, 0, C_OPEN)
    k(S(1), S(1) + 2.4, C_OPEN2)
    k(S(4) - 0.6, S(4) + 1.4, C_CS)
    k(S(8) - 0.4, S(8) + 1.6, C_OPEN)
    k(S(14) - 0.8, S(14) + 1.2, C_MID)
    k(S(16) - 0.4, S(16) + 1.4, C_XY)
    k(S(17) - 0.4, S(17) + 1.4, C_JL)
    k(S(18) - 0.4, S(18) + 1.6, C_EAST)
    k(S(19) - 0.4, S(19) + 1.6, C_NORTH)
    k(S(23) - 0.4, S(23) + 1.2, C_CHASE)
    k(S(24) - 0.3, S(24) + 1.6, C_HXK)
    k(S(25) - 0.3, S(25) + 1.4, C_JL)
    k(S(26) - 0.3, S(26) + 1.8, C_FRONT)
    k(S(29) - 0.4, S(29) + 1.4, C_CS)
    k(S(30) - 0.2, S(30) + 2.0, C_HXK)
    k(S(33) - 0.4, S(33) + 1.4, C_CS)
    k(S(41) - 0.4, S(41) + 1.6, C_OPEN)
    k(S(47) - 0.3, S(47) + 1.6, C_CS)
    k(S(49) - 0.3, S(49) + 1.4, C_JL)
    k(S(51) + 0.5, S(51) + 3.0, C_FRONT)
    k(S(54) - 0.3, S(54) + 1.4, C_CS)
    k(S(60) - 0.3, S(60) + 1.4, CM(116.2, 29.45, 1.6))
    k(S(61) - 0.3, S(61) + 1.2, C_CS)
    k(S(62) - 0.4, S(62) + 1.8, C_NW)
    k(S(63) - 0.4, S(63) + 1.6, C_JL)
    k(S(64) - 0.3, S(64) + 1.6, C_FRONT)
    k(S(67) - 0.3, S(67) + 1.4, C_EAST)
    k(S(72) - 0.3, S(72) + 1.6, C_CS)
    k(S(76) - 0.4, S(76) + 1.6, C_SAND)
    k(S(86) - 0.3, S(86) + 1.2, C_CS)
    k(S(87) - 0.3, S(87) + 1.4, C_SAND)
    k(S(89) - 0.3, S(89) + 1.4, C_CHASE)
    k(S(92) - 0.3, S(92) + 1.6, C_FRONT)
    k(S(95) - 0.3, S(95) + 2.0, C_EAST)
    k(S(97) - 0.3, S(97) + 2.4, C_BMID)
    k(S(100) - 0.3, S(100) + 1.6, C_BMID)
    k(S(101) - 0.2, S(101) + 2.0, C_BAT)
    k(S(108) - 0.2, S(108) + 1.6, C_BAT2)
    k(S(113) - 0.2, S(113) + 1.4, C_BAT)
    k(S(116) - 0.2, S(116) + 1.0, C_BAT2)
    k(S(124) - 0.3, S(124) + 1.4, C_BAT)
    k(S(129) - 0.3, S(129) + 1.2, C_BAT2)
    k(S(130) - 0.3, S(130) + 1.6, C_RET)
    k(S(131) - 0.3, S(131) + 1.4, C_BAT)
    k(S(140) - 0.3, S(140) + 1.4, C_BMID)
    k(S(142) - 0.4, S(142) + 1.6, C_RET)
    k(S(168) - 0.4, S(168) + 1.8, C_HF)
    k(S(174) - 0.4, S(174) + 1.6, C_RET)
    k(S(182) - 0.4, S(182) + 1.4, C_BMID)
    k(S(185) - 0.3, S(185) + 1.2, C_BAT)
    k(S(192) - 0.3, S(192) + 1.2, C_RET)
    k(S(194) - 0.3, S(194) + 1.4, C_END)
    k(S(201) - 0.3, S(201) + 1.4, C_CS)
    k(S(205) - 0.2, S(205) + 2.4, C_END)
build_keys()
def _drift(cam, d):
    return Cam(cam.lon, cam.lat, cam.span * max(0.86, 1.0 - 0.0040 * d), cam.ax, cam.ay)
def cam_at(t):
    cur = KEYS[0][2]; hold0 = 0.0
    for i, (t0, t1, cam) in enumerate(KEYS):
        if t >= t1: cur = cam; hold0 = t1
        elif t >= t0:
            a = _drift(cur, t0 - hold0)
            return Cam.lerp(a, cam, ease((t - t0) / max(1e-6, t1 - t0)))
        else: break
    return _drift(cur, t - hold0)

def P(cam, name): return cam.p(*CITY[name])
def PL(cam, pts): return [cam.p(lo, la) for lo, la in pts]

# ------------------------------------------------------------------ 底图
WATER = '#2B5C7C'; WATER_L = '#5FA7D3'
def draw_base(c, cam, t, night=0.0):
    c.clear(skia.Color(16, 18, 20))
    B7.draw(c, cam)
    k9 = cam.S / (256 * 2 ** 9)
    if k9 > 0.20: B9.draw(c, cam, clamp((k9 - 0.20) / 0.16))
    k10 = cam.S / (256 * 2 ** 10)
    if k10 > 0.45: B10.draw(c, cam, clamp((k10 - 0.45) / 0.3))
    # 湖
    for poly in LAKES:
        pts = PL(cam, poly)
        if max(p[0] for p in pts) < -50 or min(p[0] for p in pts) > W + 50: continue
        c.drawPath(mkpath(pts, True), skia.Paint(AntiAlias=True, Color=rgba(WATER, 0.88)))
        c.drawPath(mkpath(pts, True), skia.Paint(AntiAlias=True, Color=rgba(WATER_L, 0.35), Style=skia.Paint.kStroke_Style, StrokeWidth=1.4))
    zw = clamp(cam.S / 30000.0, 0.6, 3.2)
    for name, p in OTHER:
        line(c, PL(cam, p), WATER, 2.2 * zw, 0.85); line(c, PL(cam, p), WATER_L, 0.9 * zw, 0.35)
    yp = PL(cam, YZ)
    line(c, yp, WATER_L, 9 * zw, 0.18, blur=6 * zw)
    line(c, yp, WATER, 5.2 * zw, 0.95)
    line(c, yp, WATER_L, 1.6 * zw, 0.55)
    if night > 0: dim(c, 0.50 * night, '#050B18')

def flow(c, cam, t, a=1.0, u0=0.25, u1=0.85, n=46, col='#BFE6FF'):
    if a <= 0.003: return
    for i in range(n):
        u = u0 + (u1 - u0) * ((i / n + t * 0.012) % 1.0)
        (lo, la), ang = yz_at(u)
        x, y = cam.p(lo, la)
        if -40 < x < W + 40 and -40 < y < H + 40:
            (lo2, la2), _ = yz_at(u + 0.004); x2, y2 = cam.p(lo2, la2)
            line(c, [(x, y), (x2, y2)], col, 3.0, 0.55 * a)

# ------------------------------------------------------------------ 船
def boat(c, x, y, ang, s, col, a=1.0, sail=True, lt=None, burn=0.0):
    if a <= 0.003: return
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang))
    p = skia.Path(); p.moveTo(-11 * s, -3.4 * s); p.lineTo(9 * s, -3.4 * s); p.lineTo(13 * s, 0); p.lineTo(9 * s, 3.4 * s); p.lineTo(-11 * s, 3.4 * s); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.85 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.2 * s))
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(mix(col, '#1A1210', burn * 0.8), a)))
    if sail:
        c.drawRect(skia.Rect.MakeXYWH(-2.0 * s, -6.5 * s, 2.6 * s, 13 * s), skia.Paint(AntiAlias=True, Color=rgba(lt or PAPER, 0.9 * a * (1 - burn))))
    c.restore()

def fleet_pts(u0, u1, n, rows=3, seed=1, spread=0.010):
    rng = random.Random(seed); out = []
    for i in range(n):
        u = u0 + (u1 - u0) * (i + rng.random() * 0.6) / n
        (lo, la), ang = yz_at(u)
        r = (i % rows) - (rows - 1) / 2
        nx, ny = -math.sin(ang), math.cos(ang)
        out.append((lo + nx * spread * r / 0.87 + rng.uniform(-0.002, 0.002), la + ny * spread * r, ang, rng.random()))
    return out
F_CAO_BIG = fleet_pts(U_JL, U_WL, 420, rows=5, seed=3, spread=0.011)
F_CAO_JL = fleet_pts(U_JL - 0.004, U_JL + 0.012, 70, rows=4, seed=5, spread=0.010)
F_WU = fleet_pts(U_XK + 0.002, U_CS - 0.01, 90, rows=3, seed=7, spread=0.008)

def draw_fleet(c, cam, pts, col, lt, a, t, prog=1.0, s=None, shift=0.0, sail=True):
    if a <= 0.003: return
    s = s or clamp(cam.S / 40000.0, 0.6, 2.4)
    n = int(len(pts) * prog)
    for (lo, la, ang, r) in pts[:n]:
        x, y = cam.p(lo + shift, la)
        if -30 < x < W + 30 and -30 < y < H + 30:
            boat(c, x, y + math.sin(t * 1.6 + r * 9) * 0.8 * s, -ang, s, col, a, sail, lt)

# 赤壁近景：曹军连船（北岸，首尾相接）、黄盖火船（南来）、营落
def _bank_rows():
    rows = []
    for rr in range(3):
        row = []
        for i in range(16):
            u = yz_u(113.47) + (yz_u(113.70) - yz_u(113.47)) * i / 15
            (lo, la), ang = yz_at(u)
            nx, ny = -math.sin(ang), math.cos(ang)
            off = 0.0105 + rr * 0.0062
            row.append((lo + nx * off / 0.87, la + ny * off, ang))
        rows.append(row)
    return rows
CHAIN = _bank_rows()
CAMPS = []
for i in range(11):
    u = yz_u(113.46) + (yz_u(113.70) - yz_u(113.46)) * i / 10
    (lo, la), ang = yz_at(u); nx, ny = -math.sin(ang), math.cos(ang)
    for j in range(2):
        off = 0.040 + j * 0.016
        CAMPS.append((lo + nx * off / 0.87 + (j * 0.006), la + ny * off))
def _wu_line():
    out = []
    for i in range(12):
        u = yz_u(113.55) + (yz_u(113.76) - yz_u(113.55)) * i / 11
        (lo, la), ang = yz_at(u); nx, ny = -math.sin(ang), math.cos(ang)
        out.append((lo - nx * 0.016 / 0.87, la - ny * 0.016, ang))
    return out
WU_LINE = _wu_line()
FIRE_START = (113.60, 29.915)

def camp(c, x, y, s, a, burn=0.0):
    rrect(c, x - 9 * s, y - 6 * s, 18 * s, 12 * s, 2, mix('#6E7884', '#2A1A12', burn), a)
    line(c, [(x - 9 * s, y - 6 * s), (x, y - 12 * s), (x + 9 * s, y - 6 * s)], mix(CAO_L, '#3A2618', burn), 2.2 * s, a)

def flame(c, x, y, s, t, seed, a=1.0):
    if a <= 0.003: return
    fl = 0.75 + 0.25 * math.sin(t * 11 + seed * 7.1) + 0.12 * math.sin(t * 23 + seed)
    glow(c, x, y - 6 * s, 26 * s * fl, '#FF7A1A', 0.55 * a)
    p = skia.Path(); h = 20 * s * fl
    p.moveTo(x - 7 * s, y); p.quadTo(x - 6 * s, y - h * 0.6, x + math.sin(t * 7 + seed) * 2 * s, y - h); p.quadTo(x + 6 * s, y - h * 0.6, x + 7 * s, y); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba('#FF8A2A', 0.95 * a)))
    p2 = skia.Path(); h2 = h * 0.55
    p2.moveTo(x - 3.5 * s, y); p2.quadTo(x - 3 * s, y - h2 * 0.6, x, y - h2); p2.quadTo(x + 3 * s, y - h2 * 0.6, x + 3.5 * s, y); p2.close()
    c.drawPath(p2, skia.Paint(AntiAlias=True, Color=rgba('#FFE08A', a)))

def smoke(c, x, y, s, t, seed, a=1.0, wind=(-1.0, -0.8)):
    if a <= 0.003: return
    for k in range(4):
        age = ((t * 0.28 + k / 4 + seed * 0.37) % 1.0)
        px = x + wind[0] * age * 120 * s + math.sin(seed + k) * 8 * s; py = y + wind[1] * age * 120 * s - age * 30 * s
        circle(c, px, py, (10 + 34 * age) * s, '#3A3532', 0.42 * a * (1 - age) * min(1, age * 5), blur=10 * s)

def embers(c, x, y, s, t, seed, a=1.0):
    for k in range(5):
        age = ((t * 0.7 + k / 5 + seed * 0.53) % 1.0)
        px = x - age * 70 * s + math.sin(seed * 3 + k * 2 + t * 3) * 10 * s; py = y - age * 90 * s
        circle(c, px, py, 1.8 * s, '#FFC266', a * (1 - age))

def wind_field(c, cam, t, a, dirv=(-0.75, -0.66), n=70, col='#DDEBF5', speed=1.0, seed=11):
    if a <= 0.003: return
    rng = random.Random(seed)
    for i in range(n):
        x0 = rng.uniform(-200, W + 200); y0 = rng.uniform(150, 1450); ph = rng.random(); L = rng.uniform(60, 150)
        u = (t * 0.35 * speed + ph) % 1.0
        x = x0 + dirv[0] * (u - 0.5) * 700; y = y0 + dirv[1] * (u - 0.5) * 700
        aa = a * math.sin(math.pi * u) * 0.55
        line(c, [(x, y), (x - dirv[0] * L, y - dirv[1] * L)], col, 2.2, aa)

def haze(c, cam, pts, t, a, col='#9DBB52', r=60):
    if a <= 0.003: return
    for i, (lo, la) in enumerate(pts):
        x, y = cam.p(lo, la)
        rr = r * (0.8 + 0.25 * math.sin(t * 1.3 + i * 1.7))
        circle(c, x + math.sin(t * 0.5 + i) * 10, y + math.cos(t * 0.4 + i) * 6, rr, col, 0.20 * a, blur=rr * 0.5)

def snow(c, t, a, n=110, seed=5):
    if a <= 0.003: return
    rng = random.Random(seed)
    for i in range(n):
        x0 = rng.uniform(0, W); sp = rng.uniform(60, 140); ph = rng.uniform(0, 2000); r = rng.uniform(1.4, 3.6)
        y = (ph + t * sp) % (H + 40) - 20; x = x0 + math.sin(t * 0.8 + i) * 18
        circle(c, x, y, r, '#E8F1F8', 0.75 * a)

# ------------------------------------------------------------------ 标注小件
def label(c, x, y, s, a=1.0, size=30, col=PAPER, fname='serif', anchor='c'):
    text(c, s, x, y, size, col, fname, a, anchor, stroke=6, shadow=6)
def ribbon(c, x, y, s, col, a=1.0, size=30, anchor='l'):
    return tag(c, x, y, s, col, a, size, anchor)
def letter_icon(c, x, y, s, a, seal='曹'):
    if a <= 0.003: return
    rrect(c, x - 26 * s, y - 18 * s, 52 * s, 36 * s, 3, '#E9DFC6', a)
    line(c, [(x - 26 * s, y - 18 * s), (x, y + 2 * s), (x + 26 * s, y - 18 * s)], '#8A7A5A', 2 * s, a)
    rrect(c, x + 8 * s, y + 2 * s, 14 * s, 12 * s, 2, '#B23A2A', a)

def warletter(c, t0, t, lines, src, a=1.0, y=430, slam=True, seal='曹', w=900):
    """战书：深色绢面卡，宋体，朱印。"""
    if a <= 0.003: return
    u = ramp(t, t0, t0 + 0.35)
    sc = lerp(1.55, 1.0, eout(u)) if slam else 1.0
    c.save(); c.translate(W / 2, y + 150); c.scale(sc, sc); c.translate(-W / 2, -(y + 150))
    x = (W - w) / 2; h = 110 + len(lines) * 84
    panel(c, x, y, w, h, a, r=6, fill='#15110C', fa=0.90, edge=GOLD, ea=0.35)
    line(c, [(x + 24, y + 54), (x + w - 24, y + 54)], GOLD, 1.2, 0.35 * a)
    text(c, src, x + 30, y + 40, 25, GOLD, 'sansm', a * 0.9)
    yy = y + 124
    for l in lines:
        segs = re_hl(l); xx = x + 40
        for s_, hl in segs:
            text(c, s_, xx, yy, 60, '#FF7A55' if hl else '#F3E7C8', 'serifx', a); xx += tw(s_, 'serifx', 60)
        yy += 84
    # 朱印
    rrect(c, x + w - 120, y + h - 116, 86, 86, 6, '#B23A2A', 0.9 * a)
    text(c, seal, x + w - 77, y + h - 48, 56, '#F3E2C8', 'serifx', a, 'c')
    c.restore()
    if slam and 0.25 < (t - t0) < 1.2:
        k_ = (t - t0 - 0.25)
        for j in range(18):
            ang = j / 18 * 6.283; r = 120 + k_ * 420
            circle(c, W / 2 + math.cos(ang) * r * 1.6, y + 150 + math.sin(ang) * r * 0.5, 5, '#D8C8A0', 0.5 * (1 - k_ / 0.95))

def re_hl(s):
    out = []; cur = ''; hl = False
    for ch in s:
        if ch in '{}':
            if cur: out.append((cur, hl))
            cur = ''; hl = ch == '{'; continue
        cur += ch
    if cur: out.append((cur, hl))
    return out

def bigline(c, s, y, size, a, col=PAPER, hl=GOLD, fname='serifx'):
    if a <= 0.003: return
    segs = re_hl(s); w = sum(tw(x, fname, size) for x, _ in segs); xx = W / 2 - w / 2
    for x, h in segs:
        text(c, x, xx, y, size, hl if h else col, fname, a, stroke=8, shadow=14); xx += tw(x, fname, size)

def bigtext(c, t, i, lines, sub=None, y0=520, size=None, i1=None, dimk=0.35):
    a = win(t, i, i1, 0.35, 0.35)
    if a <= 0.003: return
    dim(c, dimk * a)
    for j, l in enumerate(lines):
        sz = size or min(150, int(900 / max(1, len(re_hl(''.join(x for x, _ in re_hl(l)))[0][0]) if False else 900 / max(1, len(l.replace('{', '').replace('}', ''))))))
        aj = a * ss(ramp(t, S(i) + 0.12 * j, S(i) + 0.12 * j + 0.5))
        yy = y0 + j * sz * 1.18 + (1 - aj) * 26
        bigline(c, l, yy, sz, aj)
    if sub:
        text(c, sub, W / 2, y0 + len(lines) * (size or 130) * 1.18 + 30, 40, '#D9D2C2', 'sansm', a * ss(ramp(t, S(i) + 0.5, S(i) + 1.0)), 'c', stroke=5, shadow=6)

# ------------------------------------------------------------------ 引文
CITES = {}
def cite(i, level, src, q, gloss=None, i1=None, note=None, y=None):
    CITES[i] = dict(level=level, src=src, q=q, gloss=gloss, i1=i1 or i, note=note, y=y)
cite(7, '裴注', '《三国志·吴主传》裴注引《江表传》', '权得书以示群臣，莫不响震失色。', '孙权把信给群臣看，没有不震动变色的')
cite(22, '正史', '《三国志·魏书·武帝纪》', '九月，公到新野，琮遂降，备走夏口。', '曹操到新野，刘琮投降，刘备逃往夏口')
cite(32, '正史', '《三国志·吴书·鲁肃传》', '到当阳长阪，与备会……劝备与权并力。', '鲁肃在长坂见到刘备，劝他与孙权合力')
cite(34, '注家', '《周瑜传》裴松之注（转述本传）', '本传直云，权延见群下，问以计策，瑜摆拨众人之议，独言抗拒之计。', '本传只写周瑜一人驳倒众议、主张抵抗')
cite(36, '注家', '《三国志·周瑜传》裴松之注', '臣松之以为建计拒曹公，实始鲁肃。', '第一个提出抵抗曹操的，其实是鲁肃')
cite(37, '注家', '《三国志·周瑜传》裴松之注', '了不云肃先有谋，殆为攘肃之善也。', '本传不提鲁肃在先，几乎是抢了鲁肃的功')
cite(50, '正史', '《三国志·吴书·周瑜传》', '此为长江之险，已与我共之矣。', '议者：长江天险，已经和曹操共有了')
cite(51, '正史', '《三国志·吴书·周瑜传》', '刘表治水军，蒙冲斗舰，乃以千数，操悉浮以沿江。', '刘表的战船数以千计，曹操全部沿江排开')
cite(52, '正史', '《三国志·吴书·周瑜传》', '兼有步兵，水陆俱下……而势力众寡，又不可论。愚谓大计不如迎之。', '水陆并进，兵力悬殊，不如迎降')
cite(55, '正史', '《三国志·吴书·鲁肃传》', '今肃可迎操耳，如将军，不可也。', '我可以迎曹操，将军不可以')
cite(56, '正史', '《三国志·吴书·鲁肃传》', '今肃迎操，操当以肃还付乡党，品其名位，犹不失下曹从事，', '我投降，曹操会把我交还乡里，照样有官做')
cite(57, '正史', '《三国志·吴书·鲁肃传》', '乘犊车，从吏卒，交游士林，累官故不失州郡也。', '出入有车有从，慢慢升到州郡长官')
cite(58, '正史', '《三国志·吴书·鲁肃传》', '将军迎操，欲安所归？', '将军迎降，又能归向何处')
cite(66, '正史', '《三国志·吴书·周瑜传》', '此数四者，用兵之患也，而操皆冒行之。', '这四条都是用兵之患，曹操全都冒险去做了')
cite(68, '裴注', '《周瑜传》裴注引《江表传》', '权拔刀斫前奏案曰：诸将吏敢复有言当迎操者，与此案同！', '孙权拔刀砍案：再有人说迎曹，下场如此案', i1=69)
cite(73, '裴注', '《周瑜传》裴注引《江表传》', '及会罢之夜，瑜请见。', '散会那天夜里，周瑜求见孙权')
cite(74, '裴注', '《周瑜传》裴注引《江表传》', '诸人徒见操书，言水步八十万，而各恐慑，不复料其虚实。', '众人只看到曹操的信，就被吓住，不再估量它的虚实', i1=75)
cite(80, '裴注', '《周瑜传》裴注引《江表传》', '夫以疲病之卒，御狐疑之众，众数虽多，甚未足畏。', '疲病之兵统驭狐疑之众，人多也不足畏')
cite(82, '裴注', '《周瑜传》裴注引《江表传》', '五万兵难卒合，已选三万人，船粮战具俱办。', '五万仓促难以集齐，已选好三万，船粮兵器都备齐了')
cite(83, '裴注', '《周瑜传》裴注引《江表传》', '卿与子敬、程公便在前发，孤当续发人众，多载资粮，为卿后援。', '你们先出发，我随后增兵运粮做后援')
cite(87, '正史', '《三国志·蜀书·诸葛亮传》', '今战士还者及关羽水军精甲万人，刘琦合江夏战士亦不下万人。', '刘备尚有精兵一万，刘琦江夏兵也不下一万', i1=88)
cite(90, '正史', '《三国志·蜀书·诸葛亮传》', '此所谓「彊弩之末，势不能穿鲁缟」者也。', '射到尽头的箭，连薄绸都穿不透', i1=91)
cite(92, '正史', '《三国志·蜀书·诸葛亮传》', '北方之人，不习水战；又荆州之民附操者，逼兵势耳，非心服也。', '荆州人附曹，是被兵势所逼，并不心服')
cite(102, '正史', '《三国志·吴书·周瑜传》', '遇于赤壁。时曹公军众已有疾病，', '两军在赤壁相遇，那时曹军中已经有了疾病', i1=103)
cite(105, '正史', '《三国志·吴书·周瑜传》', '初一交战，公军败退，引次江北。', '初次交战，曹军败退，退驻江北')
cite(111, '正史', '《三国志·吴书·周瑜传》', '今寇众我寡，难与持久。', '黄盖：敌众我寡，难以久持')
cite(112, '正史', '《三国志·吴书·周瑜传》', '然观操军船舰，首尾相接，可烧而走也。', '曹军船舰首尾相连，可以火攻击退')
cite(114, '正史', '《三国志·吴书·周瑜传》', '乃取蒙冲斗舰数十艘，实以薪草，膏油灌其中，裹以帷幕，上建牙旗。', '几十艘战船装满柴草、灌油，外裹帷幕，插上牙旗', i1=115)
cite(116, '正史', '《三国志·吴书·周瑜传》', '先书报曹公，欺以欲降。', '先写信给曹操，假称要投降')
cite(120, '裴注', '《周瑜传》裴注引《江表传》', '曹公特见行人，密问之，口敕曰：但恐汝诈耳。', '曹操私下召见送信人：只怕你是诈降')
cite(121, '裴注', '《周瑜传》裴注引《江表传》', '盖若信实，当授爵赏，超于前后也。', '若是真降，封赏超过以往所有人')
cite(124, '正史', '《三国志·吴书·周瑜传》', '盖放诸船，同时发火。时风盛猛，', '黄盖放出诸船，同时点火。当时风很大')
cite(125, '正史', '《三国志·吴书·周瑜传》', '又豫备走舸，各系大船后，因引次俱前。', '预备轻快小船，系在大船之后，依次前进')
cite(126, '正史', '《三国志·吴书·周瑜传》', '曹公军吏士皆延颈观望，指言盖降。', '曹军都伸着脖子看，说黄盖来降了')
cite(129, '正史', '《三国志·吴书·周瑜传》', '悉延烧岸上营落。顷之，烟炎张天，人马烧溺死者甚众，军遂败退，还保南郡。', '火烧到岸上营寨，烟焰满天，曹军败退，回守南郡', i1=130)
cite(132, '裴注', '《周瑜传》裴注引《江表传》', '时东南风急，因以十舰最著前，中江举帆。', '当时东南风正急，十艘船冲在最前，江心升帆', i1=133)
cite(134, '裴注', '《周瑜传》裴注引《江表传》', '盖举火白诸校，使众兵齐声大叫曰：降焉！', '黄盖举火示意，让士兵齐声高喊：投降了')
cite(135, '裴注', '《周瑜传》裴注引《江表传》', '操军人皆出营立观。去北军二里余，同时发火。', '曹军都出营站着看。离北岸二里多时同时点火')
cite(136, '裴注', '《周瑜传》裴注引《江表传》', '瑜等率轻锐寻继其后，雷鼓大进，北军大坏，曹公退走。', '周瑜率精锐随后擂鼓进攻，曹军大败')
cite(144, '正史', '《三国志·魏书·武帝纪》', '公至赤壁，与备战，不利。于是大疫，吏士多死者，乃引军还。', '曹操到赤壁与刘备交战不利，又遇大疫，官兵多死，于是退兵', i1=149)
cite(151, '正史', '《三国志·魏书·武帝纪》建安十四年令', '自顷已来，军数征行，或遇疫气，吏士死亡不归。', '近来军队屡次出征，有时遇上疫气，官兵死了回不了家', i1=152)
cite(153, '裴注', '曹操与孙权书 ·《周瑜传》裴注引《江表传》', '赤壁之役，值有疾病，孤烧船自退，横使周瑜虚获此名。', '赤壁那一仗赶上疾病，是我自己烧船撤的，倒让周瑜白得了名声', i1=155)
cite(159, '裴注', '《武帝纪》裴注引《山阳公载记》', '公船舰为备所烧，引军从华容道步归，遇泥泞，道不通，天又大风，', '曹操的船被刘备烧了，从华容道步行撤回，路上泥泞，又刮大风', i1=161)
cite(162, '裴注', '《武帝纪》裴注引《山阳公载记》', '悉使羸兵负草填之，骑乃得过。羸兵为人马所蹈藉，陷泥中，死者甚众。', '让体弱的士兵背草填路，骑兵才得以通过，填路的兵多被踩陷泥中', i1=163)
cite(164, '裴注', '《武帝纪》裴注引《山阳公载记》', '刘备，吾俦也。但得计少晚；向使早放火，吾徒无类矣。', '刘备是我的同类，只是计谋来得晚了点；若早放火，我们都活不成', i1=165)
cite(166, '裴注', '《武帝纪》裴注引《山阳公载记》', '备寻亦放火而无所及。', '刘备随后也放了火，但已经追不上了')
cite(171, '注家', '《武帝纪》裴注引孙盛《异同评》', '案吴志，刘备先破公军，然后权攻合肥，而此记云权先攻合肥，后有赤壁之事。二者不同，吴志为是。', '按吴书是先赤壁、后合肥；这里的记载顺序相反。孙盛认为吴书是对的', i1=172)
cite(174, '注家', '《三国志·鲁肃传》裴松之注', '若二国史官，各记所闻，竞欲称扬本国容美，各取其功。', '两国史官各记所闻，都想替本国争功')
cite(188, '裴注', '《周瑜传》裴注引《江表传》', '子翼良苦，远涉江湖为曹氏作说客邪？', '周瑜开口就点破蒋干的来意')
cite(189, '裴注', '《周瑜传》裴注引《江表传》', '干还，称瑜雅量高致，非言辞所间。', '蒋干回去说：周瑜气度高远，不是言语能离间的')
cite(193, '裴注', '《武帝纪》裴注引《山阳公载记》', '引军从华容道步归，遇泥泞，道不通。', '华容道在这份记载里，是一条泥路')

def draw_cite(c, t, i):
    ci = CITES[i]; a = fade(t, S(i) + 0.05, E(ci['i1']), 0.4, 0.35)
    if a <= 0.003: return
    hh = cite_card(c, ci, 0.0035, y=-3000)      # 量高度（画在屏外）
    y = ci['y'] or (1330 - hh)
    cite_card(c, ci, a, y=y, x=64, w=872)

# ------------------------------------------------------------------ 章节
CHAP = {13: '一 · 荆州换了主人', 43: '二 · 那一夜，有人在算账', 99: '三 · 先来的是病', 142: '四 · 同一场仗，两本账', 182: '五 · 那些情节出自哪本书'}
def chap_label(t):
    cur = '';
    for i in sorted(CHAP):
        if t >= S(i): cur = CHAP[i]
    if t >= S(197): cur = '收 · 回到那封信'
    return cur
def chapter_card(c, t, i):
    a = fade(t, S(i), E(i), 0.35, 0.45)
    if a <= 0.003: return
    dim(c, 0.55 * a)
    num, ttl = CHAP[i].split(' · ')
    u = eout(ramp(t, S(i), S(i) + 0.7))
    text(c, num, W / 2, 610, 150, GOLD, 'serifx', a, 'c', stroke=8, shadow=16)
    line(c, [(W / 2 - 260 * u, 680), (W / 2 + 260 * u, 680)], GOLD, 2.0, 0.8 * a)
    text(c, ttl, W / 2, 790 + (1 - u) * 20, fit(ttl, 'serifx', 900, 96), PAPER, 'serifx', a, 'c', stroke=8, shadow=14)
def fit(s, f, maxw, size):
    while size > 30 and tw(s, f, size) > maxw: size -= 3
    return size

# ------------------------------------------------------------------ 沙盘兵块
def block(c, x, y, s, fac, a=1.0, ghost=False, dimk=0.0, wob=0.0):
    if a <= 0.003: return
    col, dk, lt = FAC[fac]
    if ghost:
        p = skia.Paint(AntiAlias=True, Color=rgba(lt, 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6)
        p.setPathEffect(skia.DashPathEffect.Make([5, 4], 0))
        c.drawRect(skia.Rect.MakeXYWH(x - s / 2, y - s / 2, s, s), p); return
    rrect(c, x - s / 2 - 2, y - s / 2 - 2 + wob, s + 4, s + 4, 3, INK, 0.85 * a)
    rrect(c, x - s / 2, y - s / 2 + wob, s, s, 2, mix(col, '#2A2D30', dimk), a)
    rrect(c, x - s / 2, y - s / 2 + wob, s, s, 2, lt, 0.0, stroke=lt, sw=1.4) if False else None
def grid_pos(cx, cy, n, cols, s, gap):
    return [(cx + (k % cols - (cols - 1) / 2) * (s + gap), cy + (k // cols) * (s + gap)) for k in range(n)]

# ------------------------------------------------------------------ 主绘制
def draw_frame(c, t, fi):
    i = shot_at(min(t, TLJ[-1]['start'] + TLJ[-1]['dur'] - 0.01))
    cam = cam_at(t)
    night = max(fade(t, S(72), E(75), 0.8, 0.8), fade(t, S(201), E(202), 0.8, 0.8), 0.6 * fade(t, S(203), TOTAL + 1, 0.8, 0.5))
    draw_base(c, cam, t, night)
    world(c, cam, t, i)
    overlays(c, cam, t, i)
    vignette(c, 1.0); top_grad(c, 1.0)
    hud(c, t, i)
    for s0, s1, txt in TLJ[i]['subs']:
        if s0 <= t < s1:
            subtitle(c, txt, 1.0); break
    grain(c, fi, 0.022)

# 城与势力（随时间变化）
def fac_of(name, t):
    if name in ('襄阳', '樊', '新野'): return 'cao' if t >= S(22) + 1.0 else None
    if name == '宛' or name == '许': return 'cao'
    if name == '江陵': return 'cao' if t >= S(25) + 1.4 else None
    if name in ('柴桑', '鄱阳', '合肥' if False else '__'): return 'sun'
    if name == '夏口': return 'liu' if t >= S(24) + 1.0 else None
    return None

def cities(c, cam, t, show, a=1.0, hi=()):
    for name in show:
        x, y = P(cam, name)
        if not (-60 < x < W + 60 and -60 < y < H + 60): continue
        major = name in hi
        if major: pulse(c, x, y, t, GOLD, 14, 60, 1.8, 0.8 * a, 2, 2.5)
        anc = 'r' if name in ('当阳', '江陵', '华容', '巴丘', '乌林') else 'l'
        city(c, x, y, name, fac_of(name, t), a, size=34 if major else 28, major=major, anchor=anc, dx=16, dy=11)

def world(c, cam, t, i):
    # 长江流向
    flow(c, cam, t, win(t, 14, 15) + 0.5 * win(t, 0, 3))
    # ---------- 开场：满江船阵 ----------
    a_cao = max(win(t, 0, 12, 0.01, 0.6), win(t, 41, 42), win(t, 45, 52), win(t, 197, 200))
    if a_cao > 0.003:
        draw_fleet(c, cam, F_CAO_BIG, CAO, CAO_L, a_cao, t, prog=min(1.0, 0.25 + (t - 0) / 3.0) if t < 6 else 1.0)
    if t < S(13):
        sw = win(t, 1, 3)
        if sw > 0:
            p = PL(cam, yz_seg(113.7, 115.95))
            arrow(c, p, CAO_L, eout(ramp(t, S(1) + 0.1, S(1) + 2.0)), 16, sw, 46, dash=None)
        cities(c, cam, t, ['江陵', '夏口', '柴桑', '乌林'], win(t, 0, 12, 0.6, 0.5), hi=('柴桑',) if t > S(4) else ())
    # 孙权/江东
    if win(t, 4, 6) > 0:
        x, y = P(cam, '柴桑'); unit(c, x + 70, y - 70, 'sun', '孙权', win(t, 4, 6), 1.1, sub='二十六岁 · 坐镇柴桑')
    if win(t, 6, 6) > 0:   # 信抵柴桑，震动
        x, y = P(cam, '柴桑'); u = ramp(t, S(6), S(6) + 1.4)
        (lo0, la0) = CITY['江陵']; sx, sy = cam.p(lo0, la0)
        letter_icon(c, lerp(sx, x, eout(u)), lerp(sy, y, eout(u)) - math.sin(u * 3.14) * 160, 1.2, win(t, 6, 6))
        if t > S(6) + 1.4:
            for kk in range(3): pulse(c, x, y, t, '#FF7A55', 20, 260, 1.4, win(t, 6, 6), 3, 4)
    if win(t, 11, 12) > 0:
        a = win(t, 11, 12)
        for j, (nm, (lo, la), col) in enumerate((('信', (112.4, 30.3), GOLD), ('病', (113.45, 30.05), '#B9D46A'), ('火', CITY['赤壁'], '#FF8A3A'))):
            aj = a * ss(ramp(t, S(11) + 0.9 + j * 0.9, S(11) + 1.4 + j * 0.9))
            x, y = cam.p(lo, la)
            glow(c, x, y, 90, col, 0.6 * aj); text(c, nm, x, y + 26, 76, col, 'serifx', aj, 'c', stroke=8, shadow=10)
        b = win(t, 12, 12)
        if b > 0:
            x, y = P(cam, '赤壁'); tag(c, x + 10, y + 50, '吴书：火攻', SUN_L, b * ss(ramp(t, S(12) + 0.6, S(12) + 1.2)), 30)
            x, y = P(cam, '乌林'); tag(c, x - 20, y - 130, '魏书：不利 · 大疫', CAO_L, b * ss(ramp(t, S(12) + 1.4, S(12) + 2.0)), 30, 'r')

    # ---------- 第一章 ----------
    if S(13) <= t < S(43):
        a = win(t, 13, 42, 0.6, 0.6)
        show = ['襄阳', '樊', '新野', '宛', '当阳', '江陵', '夏口', '柴桑', '鄱阳']
        hi = []
        if S(16) <= t < E(16): hi = ['襄阳']
        if S(17) <= t < E(17): hi = ['江陵']
        if S(18) <= t < E(18): hi = ['夏口', '柴桑']
        if S(21) <= t < E(22): hi = ['新野', '襄阳']
        if S(23) <= t < E(23): hi = ['当阳']
        if S(24) <= t < E(24): hi = ['夏口']
        if S(25) <= t < E(27): hi = ['江陵']
        if S(29) <= t < E(29) or S(33) <= t < E(40): hi = ['柴桑']
        cities(c, cam, t, show, a, hi)
        # 中游舞台
        if win(t, 15, 15) > 0:
            line(c, PL(cam, yz_seg(112.2, 116.0)), GOLD, 16, 0.25 * win(t, 15, 15), blur=10)
        if win(t, 16, 16) > 0:
            x, y = P(cam, '襄阳'); tag(c, x + 40, y + 40, '荆州牧 刘表 · 大本营', GOLD, win(t, 16, 16), 30)
        if win(t, 17, 17) > 0:
            x, y = P(cam, '江陵'); tag(c, x + 30, y + 46, '江陵 · 囤船与粮', GOLD, win(t, 17, 17), 30)
            draw_fleet(c, cam, F_CAO_JL, '#9A8F78', PAPER, win(t, 17, 17), t)
        # 曹军南下
        if S(19) <= t < E(22):
            a1 = win(t, 19, 22)
            arrow(c, PL(cam, [CITY['宛'], (112.45, 32.75), CITY['新野']]), CAO, eout(ramp(t, S(19) + 0.6, S(21) + 1.0)), 13, a1, 38)
            x, y = cam.p(*CITY['宛']); unit(c, x + 0, y - 60, 'cao', '曹操', a1, 1.1)
            if t > S(21):
                x, y = P(cam, '新野'); unit(c, x + 60, y - 10, 'cao', '曹军', a1 * ss(ramp(t, S(21), S(21) + 0.6)), 1.0)
        # 刘备南走 + 曹军轻骑追击
        if S(23) <= t < E(24):
            a2 = win(t, 23, 24)
            lp = [CITY['樊'], CITY['襄阳'], (111.98, 31.4), CITY['当阳']]
            u = eout(ramp(t, S(23) + 0.2, S(23) + 2.6)); arrow(c, PL(cam, lp), LIU, u, 12, a2, 36)
            cp = [CITY['襄阳'], (112.05, 31.5), (111.86, 30.95)]
            arrow(c, PL(cam, cp), CAO_L, eout(ramp(t, S(23) + 0.9, S(23) + 3.2)), 11, a2, 34, dash=(18, 10))
            x, y, _ = along(PL(cam, lp), u); unit(c, x + 50, y, 'liu', '刘备', a2, 1.0, strength=1 - 0.55 * ss(ramp(t, S(23) + 3.0, S(23) + 3.8)))
            if t > S(23) + 3.0:
                x, y = P(cam, '当阳'); pulse(c, x, y, t, '#FF6A4A', 16, 110, 0.9, a2, 3, 4)
                tag(c, x + 40, y + 50, '长坂 · 被追及', LIU_L, a2, 28)
            if t >= S(24):
                hp = [CITY['当阳'], (112.4, 30.9), (113.0, 30.75), (113.7, 30.62), CITY['夏口']]
                arrow(c, PL(cam, hp), LIU, eout(ramp(t, S(24) + 0.1, S(24) + 2.0)), 11, a2, 34)
        if S(24) + 1.5 <= t < E(42):
            x, y = P(cam, '夏口'); unit(c, x - 70, y + 50, 'liu', '刘备', win(t, 24, 42), 0.9, label_side='l')
        # 曹操下江陵，接收水军
        if S(25) <= t < E(28):
            a3 = win(t, 25, 28)
            arrow(c, PL(cam, [CITY['襄阳'], (112.0, 31.2), CITY['江陵']]), CAO, eout(ramp(t, S(25) + 0.1, S(25) + 1.6)), 13, a3 * (1 - win(t, 27, 28) * 0.6), 38)
            k_ = ss(ramp(t, S(25) + 1.6, S(25) + 3.0))
            draw_fleet(c, cam, F_CAO_JL, mix('#9A8F78', CAO, k_), PAPER, a3, t)
            if t < E(25):
                x, y = P(cam, '江陵'); tag(c, x - 30, y + 60, '刘表水军 · 归曹', CAO_L, a3 * k_, 30, 'r')
        if S(26) <= t < E(27):
            a4 = win(t, 26, 27)
            terr_glow(c, cam, [(111.6, 32.8), (113.2, 32.8), (113.3, 30.9), (112.5, 30.0), (111.5, 30.2)], CAO, 0.20 * a4 * ss(ramp(t, S(26), S(26) + 1.6)))
        if S(27) <= t < E(28):
            a5 = win(t, 27, 28)
            arrow(c, PL(cam, yz_seg(112.3, 115.9)), CAO_L, eout(ramp(t, S(27) + 0.4, S(27) + 3.2)), 15, a5, 44, dash=(26, 14))
        if win(t, 28, 28) > 0:
            x, y = P(cam, '柴桑'); a6 = win(t, 28, 28)
            text(c, '迎？', x - 150, y - 120, 90, CAO_L, 'serifx', a6 * ss(ramp(t, S(28) + 1.4, S(28) + 1.9)), 'c', stroke=8, shadow=10)
            text(c, '打？', x + 120, y - 120, 90, SUN_L, 'serifx', a6 * ss(ramp(t, S(28) + 2.4, S(28) + 2.9)), 'c', stroke=8, shadow=10)
        # 鲁肃
        if S(29) <= t < E(32):
            a7 = win(t, 29, 32)
            rp = [CITY['柴桑'], (115.2, 30.05), CITY['夏口'], (113.3, 30.6), (112.4, 30.8), (111.86, 30.83)]
            u = eout(ramp(t, S(30) + 0.1, S(31) + 1.4)) if t >= S(30) else 0.0
            if t < S(30):
                x, y = P(cam, '柴桑'); unit(c, x + 60, y - 60, 'sun', '鲁肃', a7, 1.1, sub='最先动身')
            else:
                arrow(c, PL(cam, rp), SUN, u, 12, a7, 36)
                x, y, _ = along(PL(cam, rp), u); unit(c, x, y - 50, 'sun', '鲁肃', a7, 0.95, label_side='t')
                if t >= S(31):
                    x2, y2 = P(cam, '当阳'); unit(c, x2 - 40, y2 + 60, 'liu', '刘备', a7, 0.95, label_side='l')
                    if u > 0.97:
                        glow(c, x2, y2, 130, GOLD, 0.7 * a7); pulse(c, x2, y2, t, GOLD, 20, 120, 1.6, a7, 2, 3)
                        tag(c, x2 + 30, y2 - 120, '孙刘联盟的第一根线', GOLD, a7, 30)
        # 聚光灯：周瑜 / 鲁肃
        if S(33) <= t < E(40):
            a8 = win(t, 33, 40)
            x, y = P(cam, '柴桑')
            zx, zy = x - 170, y - 230; lx, ly = x + 170, y - 230
            sh = ss(ramp(t, S(37) + 1.0, S(38) + 1.2))
            spot(c, lerp(zx, lx, sh), lerp(zy, ly, sh), a8)
            unit(c, zx, zy, 'sun', '周瑜', a8 * (1 - 0.55 * sh), 1.15, label_side='b')
            unit(c, lx, ly, 'sun', '鲁肃', a8 * (0.45 + 0.55 * sh), 1.15, label_side='b')
    # ---------- 第二章 ----------
    if S(43) <= t < S(99):
        a = win(t, 43, 98, 0.6, 0.6)
        cities(c, cam, t, ['襄阳', '江陵', '夏口', '柴桑', '鄱阳', '当阳', '乌林', '赤壁', '许', '宛'], a,
               hi=['柴桑'] if (S(47) <= t < E(48) or S(54) <= t < E(61) or S(72) <= t < E(75) or S(86) <= t < E(86)) else ['江陵'] if S(49) <= t < E(50) else [])
        if win(t, 47, 47) > 0:     # 猎物：准星对准柴桑
            x, y = P(cam, '柴桑'); a1 = win(t, 47, 47) * ss(ramp(t, S(47) + 1.8, S(47) + 2.4))
            r = lerp(220, 70, eout(ramp(t, S(47) + 1.8, S(47) + 3.0)))
            circle(c, x, y, r, '#FF5A3A', a1, stroke=4); circle(c, x, y, r * 0.45, '#FF5A3A', a1, stroke=2.5)
            for ang in (0, 90, 180, 270):
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                line(c, [(x + ca * r * 0.6, y + sa * r * 0.6), (x + ca * r * 1.3, y + sa * r * 1.3)], '#FF5A3A', 4, a1)
        if win(t, 48, 48) > 0:     # 群议：迎
            x, y = P(cam, '柴桑'); a2 = win(t, 48, 48); rng = random.Random(4)
            for j in range(14):
                ang = rng.uniform(0, 6.28); r = rng.uniform(90, 230)
                aj = a2 * ss(ramp(t, S(48) + 0.15 * j, S(48) + 0.15 * j + 0.3))
                tag(c, x + math.cos(ang) * r, y + math.sin(ang) * r * 0.7 - 40, '迎', CAO_L, aj, 30, 'c')
        if win(t, 49, 53) > 0:
            a3 = win(t, 49, 53)
            draw_fleet(c, cam, F_CAO_JL, CAO, CAO_L, a3, t)
            if t >= S(51):
                draw_fleet(c, cam, F_CAO_BIG, CAO, CAO_L, a3, t, prog=eout(ramp(t, S(51), S(51) + 4.0)))
            if t >= S(52):
                for side in (-1, 1):
                    pts = [(lo, la + side * 0.12) for lo, la in yz_seg(112.3, 113.4, 12)]
                    arrow(c, PL(cam, pts), CAO, eout(ramp(t, S(52) + 0.3, S(52) + 2.6)), 10, a3, 32)
        if win(t, 54, 59) > 0:    # 更衣
            a4 = win(t, 54, 59); x, y = P(cam, '柴桑')
            u = eout(ramp(t, S(54) + 0.4, S(54) + 3.0))
            unit(c, x + lerp(-120, 120, u), y - 200, 'sun', '孙权', a4, 1.1, label_side='t')
            unit(c, x + lerp(-260, 10, eout(ramp(t, S(54) + 1.6, S(54) + 4.2))), y - 200, 'sun', '鲁肃', a4, 0.95, label_side='b')
        if win(t, 59, 59) > 0:
            a5 = win(t, 59, 59); x, y = P(cam, '柴桑')
            tag(c, 100, 330, '群臣迎曹  →  换个上司', CAO_L, a5 * ss(ramp(t, S(59) + 0.5, S(59) + 1.0)), 40)
            tag(c, 100, 420, '孙权迎曹  →  欲安所归', SUN_L, a5 * ss(ramp(t, S(59) + 1.6, S(59) + 2.1)), 40)
        if win(t, 60, 61) > 0:
            a6 = win(t, 60, 61)
            arrow(c, PL(cam, [CITY['鄱阳'], (116.3, 29.4), CITY['柴桑']]), SUN, eout(ramp(t, S(60) + 0.4, S(60) + 2.4)), 12, a6, 36)
            x, y = P(cam, '鄱阳'); tag(c, x + 20, y + 40, '周瑜 · 自鄱阳召回', SUN_L, a6, 30)
            if t >= S(61):
                x, y = P(cam, '柴桑'); unit(c, x + 80, y - 90, 'sun', '周瑜', a6, 1.2, sub='四笔账')
        # 四笔账
        if win(t, 62, 62) > 0:
            a7 = win(t, 62, 62)
            gx, gy = cam.p(108.6, 34.2); unit(c, gx, gy, 'liu' if False else 'cao', None, 0)  # 占位
            rrect(c, gx - 70, gy - 34, 140, 68, 6, '#6A4C8C', 0.85 * a7); text(c, '关西', gx, gy + 12, 34, PAPER, 'serifx', a7, 'c')
            tag(c, gx - 10, gy + 50, '马超 · 韩遂', '#B79CDB', a7, 30, 'c')
            for j, tgt in enumerate((CITY['许'], CITY['宛'])):
                arrow(c, PL(cam, [(108.9, 34.1), ((108.9 + tgt[0]) / 2, 34.4 - j * 0.3), tgt]), '#B79CDB', eout(ramp(t, S(62) + 1.0 + j * 0.6, S(62) + 3.4 + j * 0.6)), 10, a7, 32, dash=(20, 12))
            x, y = P(cam, '江陵'); unit(c, x, y - 50, 'cao', '曹军主力', a7, 1.0)
        if win(t, 63, 63) > 0:
            a8 = win(t, 63, 63); x, y = P(cam, '江陵'); m = ss(ramp(t, S(63) + 1.2, S(63) + 2.6))
            unit(c, x + 90, y - 120, 'cao', '骑' if m < 0.5 else '舟', a8, 1.4, kind='army' if m < 0.5 else 'fleet')
            text(c, '舍鞍马 · 仗舟楫', x + 90, y - 200, 44, PAPER, 'serifx', a8, 'c', stroke=7, shadow=8)
        if win(t, 64, 65) > 0:
            snow(c, t, win(t, 64, 64))
            if win(t, 64, 64) > 0: dim(c, 0.18 * win(t, 64, 64), '#9CC7E8')
            haze(c, cam, [yz_at(U_JL + (U_WL - U_JL) * k_ / 8)[0] for k_ in range(9)], t, win(t, 65, 66), r=90)
        if S(62) <= t < E(66):
            items = ['一 · 关西未安', '二 · 舍鞍马 仗舟楫', '三 · 盛寒 马无蒿草', '四 · 不习水土 必生疾病']
            for j, it in enumerate(items):
                if t >= S(62 + j):
                    aj = ss(ramp(t, S(62 + j), S(62 + j) + 0.5)) * fade(t, S(62), E(66) - 0.1, 0.3, 0.4)
                    cur = (S(62 + j) <= t < E(62 + j))
                    tag(c, 70, 300 + j * 66, it, GOLD if cur else '#8F8A7E', aj, 34 if cur else 30)
        if win(t, 67, 67) > 0:
            a9 = win(t, 67, 67)
            arrow(c, PL(cam, yz_seg(115.95, 114.35)), SUN, eout(ramp(t, S(67) + 0.2, S(67) + 2.2)), 13, a9, 38)
            x, y = P(cam, '夏口'); tag(c, x - 40, y - 110, '请精兵三万 · 进住夏口', SUN_L, a9, 32)
        if win(t, 68, 69) > 0 and S(68) + 0.6 < t < S(68) + 1.0:
            dim(c, 0.25, '#FFFFFF')   # 斫案一闪
        if win(t, 70, 71) > 0:
            a10 = win(t, 70, 71)
            for j, it in enumerate(['关西 · 后方', '舟楫 · 所短', '盛寒 · 无草', '水土 · 疾病']):
                tag(c, 70, 300 + j * 66, it, GOLD, a10, 32)
        # 夜：沙盘算账
        if S(72) <= t < E(75):
            x, y = P(cam, '柴桑'); a11 = win(t, 72, 75)
            glow(c, x, y - 10, 150, '#FFB45A', 0.85 * a11)
            mx, my = W - 200, 300; glow(c, mx, my, 160, '#E8EEF5', 0.5 * a11); circle(c, mx, my, 42, '#F2F0E6', 0.9 * a11)
            if t >= S(73):
                unit(c, x - 120, y - 120, 'sun', '周瑜', a11, 1.1, label_side='t'); unit(c, x + 120, y - 120, 'sun', '孙权', a11, 1.1, label_side='t')
        sand(c, cam, t)
        if win(t, 89, 89) > 0:
            a12 = win(t, 89, 89)
            arrow(c, PL(cam, [CITY['襄阳'], (112.05, 31.5), CITY['当阳']]), CAO_L, eout(ramp(t, S(89) + 0.2, S(89) + 2.6)), 12, a12, 36, dash=(18, 10))
            x, y = P(cam, '当阳'); tag(c, x + 30, y - 200, '轻骑一日一夜三百余里', CAO_L, a12, 34)
        if win(t, 90, 91) > 0:
            x, y = P(cam, '当阳'); a13 = win(t, 90, 91)
            p = [(x + 360, y - 300), (x + 120, y - 100), (x + 30, y - 25)]
            arrow(c, p, '#D8D2C4', ss(ramp(t, S(90) + 0.2, S(90) + 1.6)) * 0.85, 8, a13, 30, glow=False)
        if win(t, 92, 92) > 0:
            a14 = win(t, 92, 92)
            draw_fleet(c, cam, F_CAO_BIG, CAO, CAO_L, a14, t)
            for j in range(20):
                (lo, la), _ = yz_at(U_JL + (U_WL - U_JL) * j / 19); x, y = cam.p(lo, la + 0.08)
                circle(c, x, y, 7, '#C8B27A', a14 * (0.4 + 0.4 * math.sin(t * 6 + j)), stroke=2)
        if win(t, 93, 93) > 0:
            a15 = win(t, 93, 93); x, y = P(cam, '夏口')
            unit(c, 230, 360, 'sun', '周瑜', a15, 1.2, label_side='b'); unit(c, W - 230, 360, 'liu', '诸葛亮', a15, 1.2, label_side='b')
            arrow(c, [(260, 420), (W / 2 - 40, 560)], SUN_L, ss(ramp(t, S(93) + 0.5, S(93) + 1.6)), 8, a15, 26)
            arrow(c, [(W - 260, 420), (W / 2 + 40, 560)], LIU_L, ss(ramp(t, S(93) + 0.5, S(93) + 1.6)), 8, a15, 26)
            text(c, '曹军虽众 · 可破', W / 2, 640, 54, GOLD, 'serifx', a15 * ss(ramp(t, S(93) + 1.6, S(93) + 2.2)), 'c', stroke=7, shadow=10)
        if win(t, 95, 96) > 0:
            a16 = win(t, 95, 96); u = eout(ramp(t, S(95) + 0.3, S(95) + 4.0))
            pts = fleet_pts(lerp(U_CS - 0.035, U_XK, u), lerp(U_CS, U_XK + 0.035, u), 70, 3, 21, 0.008)
            draw_fleet(c, cam, pts, '#3FC6CC', PAPER, a16, t)
            x, y = P(cam, '夏口'); tag(c, x + 30, y + 60, '周瑜 · 程普 · 鲁肃  水军三万', SUN_L, a16, 30)
            if t >= S(96): unit(c, x - 80, y - 40, 'liu', '刘备', a16, 1.0, label_side='l'); glow(c, x, y, 120, GOLD, 0.6 * a16)
        if win(t, 97, 98) > 0:
            a17 = win(t, 97, 98)
            draw_fleet(c, cam, fleet_pts(U_WL - 0.004, U_WL + 0.006, 40, 3, 9), CAO, CAO_L, a17, t)
            haze(c, cam, [CITY['乌林'], (113.5, 30.02), (113.62, 30.0), (113.45, 29.95)], t, a17 * ss(ramp(t, S(98), S(98) + 1.6)), r=110)
    # ---------- 第三章：赤壁 ----------
    if S(99) <= t < S(142):
        battle(c, cam, t)
    # ---------- 第四章：退走与两本账 ----------
    if S(142) <= t < S(182):
        retreat(c, cam, t)
    # ---------- 第五章 ----------
    if S(182) <= t < S(197):
        myths(c, cam, t)
    # ---------- 收 ----------
    if t >= S(197):
        ending(c, cam, t)

def terr_glow(c, cam, poly, col, a):
    if a <= 0.003: return
    p = skia.Paint(AntiAlias=True, Color=rgba(col, a)); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30))
    c.drawPath(mkpath(PL(cam, poly), True), p)

def spot(c, x, y, a):
    dim(c, 0.35 * a)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((x, y + 40), 220, [rgba('#FFF2C8', 0.42 * a), rgba('#FFF2C8', 0.10 * a), rgba('#FFF2C8', 0.0)], [0.0, 0.6, 1.0]))
    p.setBlendMode(skia.BlendMode.kPlus)
    path = skia.Path(); path.moveTo(x - 30, 160); path.lineTo(x + 30, 160); path.lineTo(x + 200, y + 120); path.lineTo(x - 200, y + 120); path.close()
    c.drawPath(path, p)

def sand(c, cam, t):
    """周瑜核算：信上八十万 → 十五六万 + 最多七八万；江东三万；刘备 / 刘琦各约一万。每块 = 一万。"""
    if not (S(76) <= t < E(88)): return
    a = win(t, 76, 88)
    s = 40; gap = 8
    cx, cy = W / 2, 440
    pos = grid_pos(cx, cy, 80, 10, s, gap)
    bx0, by0 = pos[0][0] - s / 2 - 30, 330; bx1, by1 = pos[-1][0] + s / 2 + 30, pos[-1][1] + s / 2 + 90
    panel(c, bx0, by0, bx1 - bx0, by1 - by0, a, r=8, fa=0.62, edge=GOLD, ea=0.25)
    st = 76
    for st_ in range(76, 89):
        if t >= S(st_): st = st_
    for j, (x, y) in enumerate(pos):
        aj = a * ss(ramp(t, S(76) + 0.4 + j * 0.02, S(76) + 0.7 + j * 0.02))
        if st <= 76:
            block(c, x, y, s, 'cao', aj)
        else:
            if j < 16:
                block(c, x, y, s, 'cao', aj, dimk=0.35 if j < 15 else 0.6)
            elif j < 24 and st >= 78:
                block(c, x, y, s, 'cao', aj, dimk=0.15, wob=math.sin(t * 9 + j) * 2.5)
            else:
                k_ = ss(ramp(t, S(77) + 0.3, S(77) + 1.6))
                if k_ < 1: block(c, x, y, s, 'cao', aj * (1 - k_))
                block(c, x, y, s, 'cao', aj * k_ * 0.9, ghost=True)
    tx = bx0 + 24
    text(c, '周瑜的核算 · 每格一万人（据《江表传》）', tx, by0 + 46, 30, GOLD, 'serif', a)
    lab_y = by1 - 46
    if st == 76: text(c, '信上：水步八十万', tx, lab_y, 36, CAO_L, 'serifx', a, stroke=5)
    if st >= 77: text(c, '北方带来：不过十五六万 · 已久疲', tx, lab_y, 32, CAO_L, 'serifx', a * ss(ramp(t, S(77) + 0.4, S(77) + 1.0)) * (1 if st < 78 else 0), stroke=5)
    if st >= 78 and st < 79: text(c, '刘表降众：最多七八万 · 尚怀狐疑', tx, lab_y, 32, '#C8B27A', 'serifx', a * ss(ramp(t, S(78) + 0.3, S(78) + 0.9)), stroke=5)
    if st >= 79:
        text(c, '实格 ≈ 二十来万　　虚格：信上的水分', tx, lab_y, 32, GOLD, 'serifx', a * ss(ramp(t, S(79) + 0.4, S(79) + 1.0)), stroke=5)
    if st >= 82:
        sx, sy = 150, by1 + 50
        for j, (x, y) in enumerate(grid_pos(sx + 30, sy, 3, 3, s, gap)):
            block(c, x, y, s, 'sun', a * ss(ramp(t, S(82) + 1.0 + j * 0.25, S(82) + 1.4 + j * 0.25)))
        tag(c, sx - 40, sy + 30, '江东先发：三万', SUN_L, a * ss(ramp(t, S(82) + 1.0, S(82) + 1.6)), 30)
    if st >= 84:
        tex = '三万  对  二十几万'
        text(c, tex, W / 2, by1 + 200, 60, GOLD, 'serifx', a * ss(ramp(t, S(84) + 0.3, S(84) + 0.9)) * (1 - win(t, 85, 88)), 'c', stroke=8, shadow=10)
    if st >= 87:
        lx, ly = 470, by1 + 50
        block(c, lx, ly, s, 'liu', a * ss(ramp(t, S(87) + 1.0, S(87) + 1.6)))
        tag(c, lx + 26, ly - 18, '刘备：精甲万人（含关羽水军）', LIU_L, a * ss(ramp(t, S(87) + 1.0, S(87) + 1.6)), 28)
        if st >= 88:
            block(c, lx, ly + s + gap, s, 'liu', a * ss(ramp(t, S(88) + 0.2, S(88) + 0.8)))
            tag(c, lx + 26, ly + s + gap - 18, '刘琦：江夏战士不下万人', LIU_L, a * ss(ramp(t, S(88) + 0.2, S(88) + 0.8)), 28)

def battle(c, cam, t):
    a = fade(t, S(99), S(142), 0.6, 0.6)
    cities(c, cam, t, ['乌林', '赤壁', '江陵', '夏口', '巴丘', '华容'], a, hi=['赤壁'] if S(100) <= t < E(101) else [])
    s = clamp(cam.S / 52000.0, 0.45, 2.4) * 0.62
    t_meet = S(100)
    # 远景：两支舰队相向
    if S(99) <= t < S(101) + 1.5:
        a1 = fade(t, S(99), S(101) + 1.5, 0.5, 1.0)
        u = eout(ramp(t, S(100) - 0.5, S(100) + 3.0))
        draw_fleet(c, cam, fleet_pts(lerp(U_JL + 0.01, U_WL - 0.012, u), lerp(U_JL + 0.03, U_WL + 0.002, u), 60, 3, 13), CAO, CAO_L, a1, t)
        draw_fleet(c, cam, fleet_pts(lerp(U_XK - 0.03, U_WL + 0.006, u), lerp(U_XK - 0.005, U_WL + 0.02, u), 50, 3, 17), SUN, SUN_L, a1, t)
        if t > S(101):
            x, y = P(cam, '赤壁'); tag(c, x + 20, y + 70, '赤壁 · 今地有争议（示意）', GOLD, a1, 28)
    # 近景元素
    near = fade(t, S(101) + 1.0, S(141) + 1.0, 0.8, 1.0)
    if near > 0.003:
        t_fire = S(127) + 0.6        # 同时发火
        fire_on = t >= t_fire
        # 营落
        for j, (lo, la) in enumerate(CAMPS):
            x, y = cam.p(lo, la)
            tb = t_fire + 2.2 + math.hypot(lo - FIRE_START[0], la - FIRE_START[1]) * 60
            burn = ss(ramp(t, tb, tb + 2.0)) * (1 - 0.6 * ss(ramp(t, S(140), S(141))))
            camp(c, x, y, s * 1.3, near, burn)
            if burn > 0.05:
                flame(c, x, y - 4 * s, s * 1.2, t, j + 50, near * burn); smoke(c, x, y - 10, s * 1.2, t, j + 50, near * burn)
        # 曹军连船
        retreat_k = ss(ramp(t, S(105) + 0.2, S(105) + 2.2))     # 初战败退 → 北岸
        for r_, row in enumerate(CHAIN):
            pts = []
            for j, (lo, la, ang) in enumerate(row):
                dy = (1 - retreat_k) * -0.03 if t < S(106) else 0.0
                x, y = cam.p(lo, la + dy)
                pts.append((x, y))
            ch = fade(t, S(112), E(113) + 0.5, 0.5, 0.6) + 0.35 * (1 if t > S(113) else 0) * (1 - ss(ramp(t, S(140), S(141))))
            if ch > 0: line(c, pts, GOLD if t < S(127) else '#FF9A4A', 3.2, near * min(1, ch))
            for j, (lo, la, ang) in enumerate(row):
                x, y = pts[j]
                d = math.hypot(lo - FIRE_START[0], la - FIRE_START[1])
                tb = t_fire + 0.3 + d * 45 + r_ * 0.25
                burn = ss(ramp(t, tb, tb + 1.2)) * (1 - 0.7 * ss(ramp(t, S(140), S(141))))
                boat(c, x, y + math.sin(t * 1.4 + j) * 0.8 * s, -ang, s * 1.35, CAO, near, True, CAO_L, burn)
                if burn > 0.05:
                    flame(c, x, y - 2 * s, s * 1.3, t, j * 3 + r_, near * burn)
                    if (j + r_) % 2 == 0: smoke(c, x, y - 8, s * 1.4, t, j * 3 + r_, near * burn)
                    embers(c, x, y - 10, s * 1.2, t, j + r_ * 7, near * burn)
        # 疾病
        sick = near * (fade(t, S(102), E(104), 0.6, 0.6) + 0.5 * fade(t, S(108), E(109), 0.6, 0.6))
        if sick > 0.003:
            haze(c, cam, [(lo, la) for lo, la in CAMPS[::2]] + [(row[j][0], row[j][1]) for row in CHAIN[:1] for j in range(0, 16, 3)], t, sick, r=70)
            for j, (lo, la) in enumerate(CAMPS[::3]):
                x, y = cam.p(lo, la); text(c, '疫', x, y - 30, 30, '#C9DD7A', 'serifx', sick * (0.6 + 0.4 * math.sin(t * 3 + j)), 'c', stroke=5)
            x, y = P(cam, '乌林'); tag(c, x - 40, y - 150, '曹军 · 已有疾病', '#C9DD7A', sick, 32, 'r')
        # 初战
        if S(105) <= t < E(105):
            a2 = fade(t, S(105), E(105), 0.3, 0.4)
            for j in range(3):
                (lo, la), _ = yz_at(yz_u(113.52 + j * 0.07)); x, y = cam.p(lo, la - 0.03)
                arrow(c, [(x, y + 80), (x + 10, y - 10)], SUN, eout(ramp(t, S(105), S(105) + 1.0)), 10, a2, 30)
                arrow(c, [(x + 30, y - 20), (x + 20, y - 140)], CAO_L, eout(ramp(t, S(105) + 1.0, S(105) + 2.4)), 10, a2, 30)
        # 孙刘阵线（南岸）
        wu_a = near * (1 - ss(ramp(t, S(140), S(141))))
        for j, (lo, la, ang) in enumerate(WU_LINE):
            x, y = cam.p(lo, la); boat(c, x, y + math.sin(t * 1.2 + j) * 0.8 * s, -ang, s * 1.2, SUN if j % 4 else LIU, wu_a, True, SUN_L if j % 4 else LIU_L)
        if S(106) <= t < E(108):
            a3 = fade(t, S(106), E(108), 0.4, 0.4)
            x, y = P(cam, '乌林'); tag(c, x - 40, y - 90, '江北 · 曹军', CAO_L, a3, 30, 'r')
            x, y = P(cam, '赤壁'); tag(c, x + 30, y + 40, '江南 · 孙刘', SUN_L, a3, 30)
        if win(t, 108, 108) > 0: snow(c, t, 0.7 * win(t, 108, 108))
        if win(t, 110, 110) > 0:
            x, y = P(cam, '赤壁'); unit(c, x + 120, y + 40, 'sun', '黄盖', win(t, 110, 110), 1.25)
        if win(t, 112, 113) > 0:
            x, y = P(cam, '乌林'); tag(c, x - 40, y - 210, '首尾相接 · 火易蔓延，难以散开', GOLD, win(t, 112, 113), 32, 'r')
        # 火船
        fs_a = near * fade(t, S(114), S(129), 0.6, 0.8)
        if fs_a > 0.003:
            go = eout(ramp(t, S(127) - 0.4, t_fire + 0.4))
            if t >= S(133) and t < E(133): go = eout(ramp(t, S(133), E(133)))
            for j in range(10):
                (lo, la), ang = yz_at(yz_u(113.53) + (yz_u(113.68) - yz_u(113.53)) * j / 9)
                nx, ny = -math.sin(ang), math.cos(ang)
                off = lerp(-0.028, 0.006, go)
                x, y = cam.p(lo + nx * off / 0.87, la + ny * off)
                boat(c, x, y, -ang - 1.4, s * 1.5, '#3A2A1C', fs_a, sail=(t >= S(115) or (S(133) <= t < E(133))), lt=GOLD)
                if t < t_fire: glow(c, x, y, 18 * s, '#FFB050', 0.5 * fs_a)
                if t >= S(115): line(c, [(x, y), (x - 3 * s, y - 16 * s)], '#B23A2A', 2.4, fs_a)
                if t >= S(125):   # 走舸
                    x2, y2 = cam.p(lo + nx * (off - 0.006) / 0.87, la + ny * (off - 0.006))
                    boat(c, x2, y2, -ang - 1.4, s * 0.7, SUN, fs_a, False)
                    line(c, [(x, y), (x2, y2)], '#D8D2C4', 1.2, 0.6 * fs_a)
                if fire_on and t < S(131):
                    flame(c, x, y - 3 * s, s * 1.6, t, j + 90, fs_a); embers(c, x, y, s * 1.4, t, j + 90, fs_a)
            if win(t, 114, 115) > 0:
                x, y = P(cam, '赤壁'); tag(c, x + 30, y + 110, '蒙冲斗舰数十艘 · 薪草 · 膏油', '#FFB050', win(t, 114, 115), 30)
        # 信：八十万 / 百万
        if win(t, 116, 123) > 0:
            a4 = win(t, 116, 123)
            x0, y0 = P(cam, '赤壁'); x1, y1 = P(cam, '乌林')
            u = eout(ramp(t, S(116) + 0.2, S(116) + 2.0))
            letter_icon(c, lerp(x0, x1, u), lerp(y0, y1, u) - math.sin(u * 3.14) * 140, 1.4, a4, '盖')
            if t >= S(118):
                text(c, '百万之众', x1, y1 - 120, 70, '#FF7A55', 'serifx', a4 * ss(ramp(t, S(118) + 0.5, S(118) + 1.2)), 'c', stroke=8, shadow=10)
            if t >= S(122):
                tag(c, 70, 300, '第一封  曹操 → 孙权：「八十万」 · 吓', CAO_L, a4 * ss(ramp(t, S(122) + 0.3, S(122) + 0.9)), 32)
                tag(c, 70, 370, '第二封  黄盖 → 曹操：「百万」 · 骗', SUN_L, a4 * ss(ramp(t, S(123) + 1.6, S(123) + 2.2)), 32)
        # 风
        wa = near * max(fade(t, S(124), S(130), 0.8, 0.8), fade(t, S(131), S(139), 0.8, 0.8), fade(t, S(186), S(186), 0.1, 0.1))
        if wa > 0.003:
            wind_field(c, cam, t, wa, speed=1.5 if t > t_fire else 1.0)
            tagtxt = '时风盛猛（《周瑜传》）' if t < S(131) else '东南风急（《江表传》）'
            if S(131) <= t < E(131): tagtxt = '正文：只说风大 · 未言方向'
            tag(c, W - 70, 300, tagtxt, '#DDEBF5', wa, 32, 'r')
            if t >= S(131) + 2.4 and t < S(139):
                arrow(c, [(W - 140, 520), (W - 330, 360)], '#DDEBF5', ss(ramp(t, S(131) + 2.4, S(131) + 3.4)), 12, wa, 36)
                text(c, '东南 → 西北', W - 230, 590, 30, '#DDEBF5', 'sansm', wa, 'c', stroke=5)
        if win(t, 126, 126) > 0:
            for j, (lo, la, ang) in enumerate(CHAIN[0][::3]):
                x, y = cam.p(lo, la); text(c, '盖降！', x, y - 40 - (j % 2) * 26, 28, CAO_L, 'serifx', win(t, 126, 126) * ss(ramp(t, S(126) + 0.3 * j, S(126) + 0.3 * j + 0.4)), 'c', stroke=5)
        if win(t, 134, 135) > 0:
            x, y = P(cam, '赤壁'); text(c, '降焉！', x, y - 170, 72, GOLD, 'serifx', win(t, 134, 134), 'c', stroke=8, shadow=10)
        if win(t, 136, 136) > 0:
            a5 = win(t, 136, 136)
            for j in range(5):
                (lo, la), _ = yz_at(yz_u(113.5 + j * 0.05)); x, y = cam.p(lo, la - 0.035)
                arrow(c, [(x, y + 60), (x + 20, y - 200)], SUN, eout(ramp(t, S(136) + j * 0.15, S(136) + 1.4 + j * 0.15)), 12, a5, 34)
            tag(c, 70, 300, '雷鼓大进 · 北军大坏', SUN_L, a5, 34)
        # 撤往南郡
        if win(t, 130, 130) > 0:
            a6 = win(t, 130, 130)
            arrow(c, PL(cam, [CITY['乌林'], (113.2, 30.1), CITY['华容'], (112.45, 30.3), CITY['江陵']]), CAO_L, eout(ramp(t, S(130), S(130) + 2.0)), 14, a6, 40)
        # 顺序条
        for (i0, items) in ((104, ['病', '交战', '火']), (139, ['病', '一战', '诈降', '火', '风'])):
            ao = win(t, i0, i0)
            if ao > 0: order_strip(c, t, i0, items, ao)
        # 正史：无祭坛
        if win(t, 137, 137) > 0:
            tag(c, W / 2, 380, '正史与裴注：无登坛作法', '#D9776A', win(t, 137, 137), 36, 'c')
        if win(t, 140, 141) > 0:
            dim(c, 0.4 * win(t, 140, 141))

def order_strip(c, t, i0, items, a):
    n = len(items); w = 880; x0 = (W - w) / 2; y = 330
    for j, it in enumerate(items):
        aj = a * ss(ramp(t, S(i0) + 0.4 + j * 0.45, S(i0) + 0.8 + j * 0.45))
        x = x0 + w * (j + 0.5) / n
        circle(c, x, y, 50, '#0B0D10', 0.85 * aj); circle(c, x, y, 50, GOLD, aj, stroke=3)
        text(c, it, x, y + 17, 46 if len(it) == 1 else 32, PAPER, 'serifx', aj, 'c')
        text(c, '①②③④⑤'[j], x, y + 92, 30, GOLD, 'sans', aj, 'c')
        if j < n - 1: line(c, [(x + 56, y), (x + w / n - 56, y)], GOLD, 2, 0.7 * aj)

def retreat(c, cam, t):
    a = fade(t, S(142), S(182), 0.6, 0.6)
    in_hf = S(168) - 0.4 <= t < E(173) + 0.4
    show = ['乌林', '赤壁', '华容', '江陵', '巴丘', '夏口'] + (['合肥', '柴桑'] if in_hf else [])
    cities(c, cam, t, show, a, hi=['华容'] if S(160) <= t < E(166) else [])
    route = [CITY['乌林'], (113.25, 30.12), CITY['华容'], (112.5, 30.33), CITY['江陵']]
    # 退走的军团
    ra = a * (1 - (1 if in_hf else 0))
    if ra > 0.003:
        u = eout(ramp(t, S(144), S(145) + 3.0)) if t < S(160) else eout(ramp(t, S(160), S(162) + 3.0))
        arrow(c, PL(cam, route), CAO_L, max(0.02, u), 14, ra, 40, dash=(20, 12) if t >= S(160) else None)
        for j in range(6):
            uu = clamp(u - j * 0.06)
            if uu > 0.01:
                x, y, _ = along(PL(cam, route), uu); unit(c, x, y - 34, 'cao', None, ra * 0.95, 0.6, strength=0.7)
        # 两套解释：同一张图上分注
        x, y = P(cam, '乌林')
        if t >= S(146) - 0.2 and t < S(160):
            lbl = [('魏《武帝纪》：与备战，不利 · 大疫', CAO_L, S(144) + 0.8)]
            if t >= S(150): lbl.append(('吴书：黄盖火攻', SUN_L, S(150) + 0.4))
            if t >= S(153): lbl.append(('曹操书信：孤烧船自退', '#C9D3DE', S(153) + 0.6))
            for j, (s_, col, t0) in enumerate(lbl):
                tag(c, 70, 300 + j * 66, s_, col, ra * ss(ramp(t, t0, t0 + 0.5)), 32)
        if S(147) <= t < E(147):
            for j, nm in enumerate(('周瑜', '黄盖')):
                unit(c, x + 120 + j * 170, y + 120, 'sun', nm, 0.35 * win(t, 147, 147), 1.0, label_side='b')
                line(c, [(x + 80 + j * 170, y + 80), (x + 160 + j * 170, y + 160)], '#D9776A', 5, win(t, 147, 147))
            tag(c, x + 80, y + 230, '《武帝纪》正文未见', '#D9776A', win(t, 147, 147), 30)
        # 病：疫气沿退路
        haze(c, cam, [(lo, la) for lo, la in [CITY['乌林'], (113.25, 30.12), CITY['华容'], (112.5, 30.33)]], t, ra * max(win(t, 149, 152), 0.0), r=110)
        if t >= S(159) and t < S(168):
            fx, fy = P(cam, '乌林')
            fa = fade(t, S(159), S(168), 0.4, 0.6)
            for j in range(5): flame(c, fx - 40 + j * 22, fy + 10, 1.5, t, j + 200, fa * (0.4 if t > S(160) else 1.0))
            tag(c, 70, 300, '《山阳公载记》：船舰为备所烧', LIU_L, fa, 32)
        if S(161) <= t < E(163):
            ma = win(t, 161, 163); xh, yh = P(cam, '华容')
            road = PL(cam, [CITY['乌林'], (113.25, 30.12), CITY['华容']])
            line(c, road, '#6B5232', 34, 0.75 * ma); line(c, road, '#8A6A40', 18, 0.6 * ma)
            for j in range(40):
                rx = (j * 53 + t * 380) % (W + 200) - 100; ry = (j * 97 + t * 520) % 1200 + 200
                line(c, [(rx, ry), (rx - 30, ry + 60)], '#CFD8E0', 2, 0.35 * ma)
            if t >= S(162):
                for j in range(26):
                    u2 = j / 25; x2, y2, _ = along(road, u2)
                    circle(c, x2 + math.sin(j) * 8, y2 + math.cos(j * 1.3) * 6, 5, '#C9B27A', ma * ss(ramp(t, S(162) + j * 0.05, S(162) + j * 0.05 + 0.3)))
                tag(c, 70, 432, '羸兵负草填之，骑乃得过', '#C9B27A', ma, 32)
            tag(c, 70, 366, '泥泞 · 道不通 · 天又大风', '#CFD8E0', ma, 32)
        if win(t, 166, 167) > 0:
            fx, fy = P(cam, '乌林'); fa = win(t, 166, 167)
            for j in range(4): flame(c, fx + 40 + j * 24, fy - 20, 1.7, t, j + 300, fa)
            tag(c, 70, 366, '备寻亦放火 · 而无所及', LIU_L, fa, 32)
    # 合肥与赤壁的先后
    if in_hf:
        ha = fade(t, S(168) - 0.4, E(173) + 0.4, 0.5, 0.5)
        hp = [CITY['柴桑'], (116.5, 30.6), (117.0, 31.4), CITY['合肥']]
        u = eout(ramp(t, S(168) + 1.6, S(168) + 3.6))
        bounce = ss(ramp(t, S(173) + 0.8, S(173) + 2.4))
        arrow(c, PL(cam, hp), SUN, u * (1 - 0.35 * bounce), 13, ha, 38)
        if t >= S(169):
            arrow(c, PL(cam, [(113.6, 31.6), (115.5, 32.3), CITY['合肥']]), CAO_L, eout(ramp(t, S(169) + 0.2, S(169) + 2.0)), 11, ha, 34, dash=(18, 10))
            x, y = cam.p(114.6, 32.15); tag(c, x, y - 40, '张憙救合肥', CAO_L, ha, 28, 'c')
        xw, yw = P(cam, '乌林'); xh, yh = P(cam, '合肥')
        swap = ss(ramp(t, S(171) + 2.0, S(171) + 3.4))
        n1, n2 = ('①', '②')
        for (px, py, lab) in ((xh, yh, '合肥'), (xw, yw, '赤壁')):
            first = (lab == '合肥')
            order = lerp(1 if first else 2, 2 if first else 1, swap)
            col = GOLD
            text(c, '①' if order < 1.5 else '②', px, py - 60, 64, col, 'sans', ha, 'c', stroke=7, shadow=8)
        tag(c, 70, 300, '魏书这边：先合肥，后赤壁' if swap < 0.5 else '吴志（孙盛从之）：先赤壁，后合肥', CAO_L if swap < 0.5 else SUN_L, ha, 34)
        if t >= S(173):
            tag(c, xh - 20, yh + 60, '同年攻合肥 · 未下', SUN_L, ha, 30, 'r')
    # 四种说法摊在同一张退走图上
    if S(175) <= t < S(182):
        pa = fade(t, S(175), S(182), 0.4, 0.6); x, y = P(cam, '乌林')
        items = [('吴书：火攻', SUN_L, S(176)), ('魏书：不利 · 大疫', CAO_L, S(176) + 1.6), ('山阳公载记：刘备烧船', LIU_L, S(177)), ('曹操书信：孤烧船自退', '#C9D3DE', S(177) + 2.2)]
        for j, (s_, col, t0) in enumerate(items):
            tag(c, 70, 300 + j * 66, s_, col, pa * ss(ramp(t, t0, t0 + 0.5)), 34)
            line(c, [(560, 330 + j * 66), (x, y)], col, 1.6, 0.5 * pa * ss(ramp(t, t0, t0 + 0.5)))
        haze(c, cam, [(lo, la) for lo, la in [CITY['乌林'], CITY['华容']]], t, 0.6 * pa, r=90)
        for j in range(4): flame(c, x - 30 + j * 20, y + 10, 1.3, t, j + 400, 0.6 * pa)

def myths(c, cam, t):
    a = fade(t, S(182), S(197), 0.6, 0.6)
    cities(c, cam, t, ['乌林', '赤壁', '华容', '江陵'], a)
    s = clamp(cam.S / 52000.0, 0.45, 2.4) * 0.62
    for r_, row in enumerate(CHAIN):
        for j, (lo, la, ang) in enumerate(row):
            x, y = cam.p(lo, la); boat(c, x, y, -ang, s * 1.35, CAO, a * 0.8, True, CAO_L)
    if win(t, 183, 184) > 0:
        tag(c, W / 2, 330, '以下为《三国演义》情节 · 出处分开放', '#D9776A', win(t, 183, 184), 36, 'c')
    for i, name, verdict in ((185, '草船借箭', '本次所对《武帝纪》《周瑜传》《吴主传》《诸葛亮传》及裴注：未见'),
                             (186, '借东风', '正史：时风盛猛 · 《江表传》：东南风急 · 无祭坛'),
                             (187, '蒋干盗书', '《江表传》：蒋干来作说客 · 无盗书'),
                             (191, '连环计', '正文：船舰首尾相接 · 无庞统献计'),
                             (192, '舌战群儒 · 华容道义释', '本次所对正文：未见')):
        aa = win(t, i, i + (3 if i == 187 else 0))
        if aa <= 0.003: continue
        dim(c, 0.30 * aa)
        text(c, name, W / 2, 470, fit(name, 'serifx', 900, 110), PAPER, 'serifx', aa, 'c', stroke=8, shadow=14)
        rrect(c, W / 2 - 150, 520, 300, 62, 6, '#D9776A', 0.0, stroke='#D9776A', sw=4)
        p = skia.Paint(AntiAlias=True, Color=rgba('#D9776A', aa), Style=skia.Paint.kStroke_Style, StrokeWidth=4)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(W / 2 - 150, 520, 300, 62), 6, 6), p)
        text(c, '演义情节', W / 2, 565, 40, '#D9776A', 'serifx', aa, 'c')
        for j, l in enumerate(wrap(verdict, 'sansm', 36, 900)):
            text(c, l, W / 2, 660 + j * 52, 36, '#E4DDCF', 'sansm', aa * ss(ramp(t, S(i) + 0.6, S(i) + 1.2)), 'c', stroke=5)
        if i == 186: wind_field(c, cam, t, aa * 0.8)
        if i == 191:
            for row in CHAIN:
                line(c, [cam.p(lo, la) for lo, la, _ in row], GOLD, 3, aa)
    if win(t, 190, 190) > 0:
        tag(c, W / 2, 330, '没有盗书 · 没有反间', '#D9776A', win(t, 190, 190), 38, 'c')
    if win(t, 193, 193) > 0:
        road = PL(cam, [CITY['乌林'], (113.25, 30.12), CITY['华容']]); line(c, road, '#8A6A40', 18, 0.7 * win(t, 193, 193))
    if win(t, 195, 195) > 0:
        aa = win(t, 195, 195)
        for j, (nm, (lo, la), col) in enumerate((('信', (112.4, 30.3), GOLD), ('病', (113.45, 30.05), '#B9D46A'), ('火', CITY['赤壁'], '#FF8A3A'))):
            x, y = cam.p(lo, la); aj = aa * ss(ramp(t, S(195) + 0.6 + j * 0.8, S(195) + 1.1 + j * 0.8))
            glow(c, x, y, 90, col, 0.6 * aj); text(c, nm, x, y + 26, 76, col, 'serifx', aj, 'c', stroke=8, shadow=10)

def ending(c, cam, t):
    a = fade(t, S(197), TOTAL + 1, 0.5, 0.1)
    cities(c, cam, t, ['江陵', '柴桑', '乌林', '夏口'], a * (1 - fade(t, S(203), TOTAL + 1, 0.6, 0.1)))
    if t < S(201):
        draw_fleet(c, cam, F_CAO_BIG, CAO, CAO_L, a, t)
    if S(198) <= t < E(200):
        b = win(t, 198, 200)
        for j, (nm, val, city_, col) in enumerate((('对方自称的数字', '八十万', '江陵', '#FF7A55'), ('自己核算的数字', '十五六万 + 七八万', '柴桑', GOLD), ('事后解释撤退的说法', '火 · 病 · 自烧船', '乌林', SUN_L))):
            if t < S(198 + j): continue
            x, y = P(cam, city_); aj = b * ss(ramp(t, S(198 + j), S(198 + j) + 0.5))
            yy = y - 150 - (j == 2) * 60
            x = clamp(x, 240, W - 240)
            panel(c, x - 200, yy - 60, 400, 120, aj, r=6, fa=0.86)
            text(c, nm, x, yy - 18, 26, '#D9D2C2', 'sansm', aj, 'c'); text(c, val, x, yy + 36, fit(val, 'serifx', 370, 48), col, 'serifx', aj, 'c')
    if S(201) <= t < E(202):
        x, y = P(cam, '柴桑'); b = win(t, 201, 202)
        glow(c, x, y - 10, 140, '#FFB45A', 0.8 * b)
        mx, my = W - 200, 300; glow(c, mx, my, 160, '#E8EEF5', 0.5 * b); circle(c, mx, my, 42, '#F2F0E6', 0.9 * b)
        if t >= S(202):
            u = eout(ramp(t, S(202) + 0.2, S(202) + 2.6))
            unit(c, x - 260 + 200 * u, y - 140, 'sun', '周瑜', b, 1.1, label_side='t')
            rrect(c, x - 30, y - 200, 60, 110, 4, '#FFB45A', 0.85 * b * ss(ramp(t, S(202) + 1.8, S(202) + 2.6)))

def overlays(c, cam, t, i):
    # 引文卡
    for j in range(max(0, i - 3), i + 1):
        if j in CITES and S(j) <= t < E(CITES[j]['i1']) + 0.4: draw_cite(c, t, j)
    # 章节卡
    if i in CHAP: chapter_card(c, t, i)
    # 开场：战书砸下 + 八十万膨胀
    if t < S(3):
        a = fade(t, 0, S(3), 0.05, 0.4)
        warletter(c, 0.35, t, ['今治水军{八十万}众，', '方与将军会猎于吴。'], '曹操致孙权书 · 裴松之注引《江表传》', a, y=300)
        k_ = ramp(t, 1.6, 3.4)
        if k_ > 0:
            sc = lerp(0.3, 1.0, eout(k_)); aa = a * ss(ramp(t, 1.6, 2.1))
            glow(c, W / 2, 900, 380 * sc, '#FF7A30', 0.55 * aa)
            text(c, '八十万', W / 2, 960, 230 * sc, '#FFD48A', 'serifx', aa, 'c', stroke=10, shadow=24)
            for j in range(26):
                ang = j / 26 * 6.283 + t; r = 200 + 260 * eout(k_) + (j % 3) * 40
                circle(c, W / 2 + math.cos(ang) * r, 900 + math.sin(ang) * r * 0.55, 3 + (j % 3), '#FFC27A', aa * (1 - k_ * 0.6))
        if t >= S(2):
            bigline(c, '是{信}，还是{吓}一跳？', 1260, 82, ss(ramp(t, S(2) + 0.2, S(2) + 0.7)) * fade(t, S(2), S(3), 0.3, 0.3))
    for (i0, i1, ls, src, seal) in ((41, 42, ['今治水军{八十万}众，', '方与将军会猎于吴。'], '曹操致孙权书 · 裴注引《江表传》', '曹'),
                                    (45, 45, ['近者奉辞伐罪，旄麾南指，', '{刘琮束手}。'], '曹操致孙权书 · 裴松之注引《江表传》', '曹'),
                                    (46, 46, ['今治水军{八十万}众，', '方与将军{会猎于吴}。'], '曹操致孙权书 · 裴松之注引《江表传》', '曹'),
                                    (117, 117, ['用江东六郡山越之人，', '以当中国{百万之众}。'], '黄盖致曹操书 · 裴注引《江表传》', '盖'),
                                    (197, 197, ['今治水军{八十万}众，', '方与将军会猎于吴。'], '曹操致孙权书 · 裴注引《江表传》', '曹')):
        aw = win(t, i0, i1, 0.3, 0.4)
        if aw > 0.003: warletter(c, S(i0) + 0.05, t, ls, src, aw, y=330, seal=seal)
    if win(t, 3, 3) > 0:
        a = win(t, 3, 3)
        text(c, '公元208年', W / 2, 560, 150, GOLD, 'serifx', a, 'c', stroke=8, shadow=16)
        text(c, '建安十三年 · 长江中游', W / 2, 660, 50, PAPER, 'serif', a, 'c', stroke=6, shadow=8)
    if win(t, 8, 8) > 0:
        a = win(t, 8, 8); v = int(800000 * eout(ramp(t, S(8), S(8) + 1.8)))
        glow(c, W / 2, 520, 360, '#FF7A30', 0.35 * a)
        text(c, '{:,}'.format(v), W / 2, 580, 180, '#FFD48A', 'serifx', a, 'c', stroke=10, shadow=20)
        text(c, '水军八十万众 · 一千八百年', W / 2, 670, 44, PAPER, 'serif', a, 'c', stroke=6, shadow=8)
    if win(t, 9, 9) > 0:
        a = win(t, 9, 9); dim(c, 0.35 * a)
        tag(c, W / 2, 420, '历史的关键一局', GOLD, a, 34, 'c')
        bigline(c, '八十万水军', 620, 140, a * ss(ramp(t, S(9), S(9) + 0.5)))
        bigline(c, '是{信}还是{吓}？', 790, 140, a * ss(ramp(t, S(9) + 0.4, S(9) + 0.9)))
    if win(t, 10, 10) > 0:
        a = win(t, 10, 10)
        for j, s_ in enumerate(('借东风', '草船借箭')):
            aj = a * ss(ramp(t, S(10) + 0.4 + j * 1.0, S(10) + 0.8 + j * 1.0))
            text(c, s_, W / 2, 520 + j * 140, 96, '#9A948A', 'serifx', aj, 'c', stroke=7, shadow=8)
            ww = tw(s_, 'serifx', 96); u = ss(ramp(t, S(10) + 1.0 + j * 1.0, S(10) + 1.5 + j * 1.0))
            line(c, [(W / 2 - ww / 2 - 20, 490 + j * 140), (W / 2 - ww / 2 - 20 + (ww + 40) * u, 490 + j * 140)], '#D9776A', 7, aj)
        tag(c, W / 2, 820, '演义情节 · 本集不进主线', '#D9776A', a, 32, 'c')
    # 大字
    BIG = {26: (['两三个月', '荆州{换了主人}'], '几乎没有大战'), 38: (['攘{肃}之善'], '抢了鲁肃的功（裴松之语）'),
           40: (['谁站在{聚光灯}下', '本身就是写出来的'], None), 42: (['八十万', '有多少{水分}？'], None),
           47: (['会猎', '猎物是{谁}？'], None), 53: (['大计不如{迎}之'], '议者的结论'), 71: (['全是{后勤}', '和{季节}'], '没有一条是计谋'),
           81: (['精兵{五万}'], '自足制之'), 91: (['强弩之{末}'], '射到尽头的箭，连薄绸都穿不透'), 97: (['三万人', '{出发}了'], None),
           98: (['曹营里', '有东西在{蔓延}'], None), 103: (['已有{疾病}'], '写在火之前'), 109: (['不是{法术}', '是一个{冬天}'], '湿冷 · 远道 · 水土'),
           118: (['中国', '{百万}之众'], '众寡不敌 · 海内所共见'), 119: (['八十万 → {百万}'], '数字又一次被说大'),
           138: (['风 是天气', '{等风} 是人的事'], None), 141: (['这场{火}', '几乎找不到'], None),
           152: (['或遇{疫气}'], '令文没有点名赤壁'), 155: (['孤烧船{自退}'], '横使周瑜虚获此名'), 157: (['撤退怪谁', '当时就在{吵}'], None),
           178: (['谁说的', '是{真}的？'], '不替史书裁定'), 179: (['曹军{退}了'], '乃引军还'), 180: (['退兵的理由', '不止{一个}版本'], None),
           181: (['借东风', '草船借箭'], '从哪来的？'), 194: (['小说：法术 · 一个人', '史书：天气 · {一群人}'], None),
           196: (['一笔', '吵不完的{账}'], None)}
    if i in BIG:
        ls, sub = BIG[i]
        size = min(150, int(880 / max(len(l.replace('{', '').replace('}', '')) for l in ls)))
        bigtext(c, t, i, ls, sub, y0=520 if i not in (152, 155) else 470, size=size)
    # 解读 / 证据强度 小牌
    NOTE = {85: ('证据强度：中', '这套数字全出自《江表传》，是吴方一家之言，不是曹营军账'),
            94: ('读史提醒', '两段都是说给孙权听的游说之辞，算账的人也有立场'),
            156: ('证据强度：弱至中', '政敌之间的书信，自我开脱的成分很大'),
            167: ('证据强度：中偏弱', '《山阳公载记》细节生动，只能算一家之说'),
            35: ('裴松之', '南朝宋人 · 为《三国志》作注，引书二百余种'),
            44: ('《江表传》', '晋人虞溥撰 · 原书已佚，赖裴松之注引存'),
            140: ('《三国志·魏书·武帝纪》', '写曹操的那一卷'), 143: ('《三国志·魏书·武帝纪》', '建安十三年 · 十二月'),
            158: ('《山阳公载记》', '晋人乐资撰 · 原书已佚，裴注引存'), 170: ('孙盛《异同评》', '东晋史家，专挑诸书异同'),
            33: ('《三国志·吴书·周瑜传》', '我们熟悉的版本：周瑜力排众议')}
    if i in NOTE:
        h_, b_ = NOTE[i]; a = win(t, i, i, 0.35, 0.35)
        lines = wrap(b_, 'sansm', 32, 800); hh = 90 + len(lines) * 46
        y = 1330 - hh
        panel(c, 64, y, 872, hh, a, r=8, fa=0.86); rrect(c, 64, y, 7, hh, 3, '#F2A93B' if '强度' in h_ or '提醒' in h_ else '#C9B6E0', a)
        text(c, h_, 100, y + 52, 36, '#F2A93B' if '强度' in h_ or '提醒' in h_ else GOLD, 'serifx', a)
        for j, l in enumerate(lines): text(c, l, 100, y + 100 + j * 46, 32, '#E4DDCF', 'sansm', a)
    # 周瑜原话：大字
    if S(203) <= t < E(204):
        a = fade(t, S(203), E(204), 0.5, 0.4)
        dim(c, 0.35 * a)
        q = ['诸人徒见操书，', '言水步八十万，', '而各恐慑，', '{不复料其虚实}。']
        for j, l in enumerate(q):
            t0 = S(203) + 0.3 + j * 1.1 if j < 3 else S(204)
            bigline(c, l, 520 + j * 120, 86 if j < 3 else 100, a * ss(ramp(t, t0, t0 + 0.6)), col='#F6EBCB', hl=GOLD)
        text(c, '——《三国志·周瑜传》裴松之注引《江表传》', W / 2, 1050, 32, GOLD, 'serif', a, 'c', stroke=5)
        text(c, '白话｜众人只看到曹操的信，就被吓住，不再估量它的虚实', W / 2, 1110, 30, '#D9D2C2', 'sansm', a, 'c', stroke=5)
    # 片尾：经典 + 标题
    if t >= S(205):
        t_q = E(204) + 3.2 + 0.5           # 末句「史书没有记」之后
        tl = TLJ[205]; t_q = tl['subs'][-1][1] + 0.4
        a1 = fade(t, t_q, TOTAL - 3.0, 0.6, 0.5)
        if a1 > 0.003:
            dim(c, 0.55 * a1)
            q = ['夫未战而庙算胜者，得算多也；', '未战而庙算不胜者，得算少也。', '多算胜，少算不胜，', '而况于无算乎！']
            for j, l in enumerate(q):
                text(c, l, W / 2, 520 + j * 92, 58, '#F6EBCB', 'serifx', a1 * ss(ramp(t, t_q + j * 0.35, t_q + j * 0.35 + 0.6)), 'c', stroke=7, shadow=12)
            text(c, '——《孙子·计篇》', W / 2, 520 + 4 * 92 + 10, 40, GOLD, 'serif', a1, 'c', stroke=5)
            text(c, '白话｜开战之前算得多的胜，算得少的不胜，何况根本不算', W / 2, 520 + 4 * 92 + 80, 30, '#D9D2C2', 'sansm', a1, 'c', stroke=5)
        a2 = fade(t, TOTAL - 3.0, TOTAL + 1, 0.6, 0.1)
        if a2 > 0.003:
            dim(c, 0.6 * a2)
            tag(c, W / 2, 470, '历史的关键一局', GOLD, a2, 36, 'c')
            bigline(c, '八十万水军', 680, 140, a2); bigline(c, '是{信}还是{吓}？', 850, 140, a2)
            text(c, '地形：Mapzen Terrain Tiles（SRTM）· 河湖：Natural Earth · 配音：AI 合成 · 地图均为示意', W / 2, 1080, 22, '#9C978C', 'sansm', a2, 'c')

def hud(c, t, i):
    tag(c, 50, 92, '历史的关键一局', GOLD, 1.0, 28)
    lab = chap_label(t) if t >= S(13) else ''
    if lab: text(c, lab, W - 56, 128, 36, GOLD, 'serifx', 1.0, 'r', stroke=6, shadow=8)
    text(c, 'AI配音 · 示意图', W - 56, 176, 22, '#B7B0A2', 'sansm', 0.9, 'r', stroke=4)
