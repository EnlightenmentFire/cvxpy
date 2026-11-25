# -*- coding: utf-8 -*-
"""分镜：按旁白时间轴调度各场景，叠加古文卡、类比卡、字幕与角标。"""
import math, numpy as np, skia
from geo import W, H, Cam, Base, merc
from gfx import *
from ui import *
from timeline import TL, FPS
from script import BEATS, SECTIONS, BYID
import data as D
from cards import QUOTES, ANALOGY, Q3, YANYI

T = TL(); S, E = T.S, T.E
VD = '/tmp/claude-0/work/vid/'
_B = {}
def base(k):
    if k not in _B: _B[k] = Base(VD + f'base{k}.png')
    return _B[k]
RNG = np.random.default_rng(11)

def vis(t, t0, t1, din=0.5, dout=0.5): return fade(t, t0, t1, din, dout)
def BV(t, b0, b1=None, din=0.5, dout=0.5, o0=0.0, o1=0.0):
    return fade(t, S(b0) + o0, E(b1 or b0) + o1, din, dout)
def P(c, cam, ll): return cam.p(*ll)
def PP(cam, pts): return [cam.p(*q) for q in pts]

# ---------------- 镜头 ----------------
class Track:
    def __init__(s, keys): s.k = sorted(keys, key=lambda x: x[0])
    def __call__(s, t):
        k = s.k
        if t <= k[0][0]: return k[0][1]
        for i in range(len(k) - 1):
            t0, c0 = k[i][0], k[i][1]; t1, c1 = k[i + 1][0], k[i + 1][1]
            if t0 <= t < t1:
                hold = k[i][2] if len(k[i]) > 2 else 0.0
                u = ease(ramp(t, t0 + hold, t1))
                return Cam.lerp(c0, c1, u)
        return k[-1][1]
def C(lon, lat, span, ay=800): return Cam(lon, lat, span, 540, ay)

# ---------------- 底图 ----------------
_cf_sepia = skia.ColorFilters.Matrix([0.42, 0.62, 0.16, 0, 18 / 255, 0.36, 0.56, 0.14, 0, 10 / 255, 0.26, 0.42, 0.11, 0, 0, 0, 0, 0, 1, 0])
def draw_base(c, cam, grade=None):
    c.clear(rgba('#121417'))
    base(7).draw(c, cam)
    if cam.span < 9.5: base(9).draw(c, cam, alpha=ss(ramp(9.5 - cam.span, 0, 3)))
    if cam.span < 1.9: base(11).draw(c, cam, alpha=ss(ramp(1.9 - cam.span, 0, 0.7)))
    if grade: dim(c, grade[1], grade[0])

def draw_rivers(c, cam, a=1.0, glow_names=(), ga=0.0, extra=()):
    k = cam.S / 1e4
    for pts, cls, name in D.RIVERS:
        if cls < 0.9 and cam.span > 6: continue
        q = PP(cam, pts)
        xs = [x for x, y in q]; ys = [y for x, y in q]
        if max(xs) < -50 or min(xs) > W + 50 or max(ys) < -50 or min(ys) > H + 50: continue
        w = max(1.2, min(9.0, cls * (1.4 + 220 / max(cam.span * 60, 1)) ))
        line(c, q, '#2E5E73', w + 2.5, 0.55 * a)
        line(c, q, '#6FA9C2', w, 0.85 * a)
        if name in glow_names and ga > 0:
            line(c, q, '#9FE0FF', w * 2.6, 0.35 * ga * a, blur=w * 1.5)
            line(c, q, '#CFF3FF', w * 0.9, 0.9 * ga * a)

def terr(c, cam, poly, col, a=1.0, edge=True, blur=18):
    if a <= 0.003: return
    pts = PP(cam, poly); path = mkpath(pts, True)
    fa = 0.30 if cam.span > 8 else 0.12 + 0.18 * clamp((cam.span - 2) / 6)
    p = skia.Paint(AntiAlias=True, Color=rgba(col, fa * a)); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(path, p)
    if edge:
        line(c, pts + [pts[0]], col, 3.2, 0.75 * a, dash=(14, 9))

def region_label(c, cam, ll, s, a=1.0, size=40, col='#F2E7D0', sub=None):
    x, y = cam.p(*ll)
    text(c, s, x, y, size, col, 'serifx', a, 'c', stroke=6, shadow=10, spacing=size * 0.25)
    if sub: text(c, sub, x, y + size * 0.85, size * 0.5, '#E0D6C4', 'sansm', a, 'c', stroke=4, shadow=4)

def cities(c, cam, names, a=1.0, fac=None, size=30, major=(), facs=None, subs=None, anchors=None):
    for n in names:
        x, y = cam.p(*D.CITY[n])
        f = (facs or {}).get(n, fac)
        anc = (anchors or {}).get(n, 'l')
        city(c, x, y, n, f, a, size=size, major=n in major, sub=(subs or {}).get(n), anchor=anc, dx=14 if anc != 'r' else 14)

def mountain_label(c, cam, ll, s, a=1.0, size=34):
    x, y = cam.p(*ll)
    text(c, s, x, y, size, '#E8DCC0', 'serifm', a * 0.9, 'c', stroke=5, shadow=8, spacing=14)

# ---------------- 粒子兵潮 ----------------
class Tide:
    """一群兵：从起点区域沿路径流向终点区域。经纬度坐标，带延迟、侧向抖动、拖尾。"""
    def __init__(s, n, src, dst, r0, r1, seed=1, delay=0.35, via=None):
        g = np.random.default_rng(seed); s.n = n
        ang = g.uniform(0, 2 * np.pi, n); rad = np.sqrt(g.uniform(0, 1, n))
        s.a = np.stack([src[0] + np.cos(ang) * rad * r0[0], src[1] + np.sin(ang) * rad * r0[1]], 1)
        ang = g.uniform(0, 2 * np.pi, n); rad = np.sqrt(g.uniform(0, 1, n))
        s.b = np.stack([dst[0] + np.cos(ang) * rad * r1[0], dst[1] + np.sin(ang) * rad * r1[1]], 1)
        s.d = g.uniform(0, delay, n); s.ph = g.uniform(0, 6.28, n); s.sp = g.uniform(0.85, 1.15, n)
        s.via = via
    def pos(s, u):
        k = np.clip((u - s.d) / (1 - s.d.max() + 1e-6) * s.sp, 0, 1)
        e = k * k * (3 - 2 * k)
        p = s.a + (s.b - s.a) * e[:, None]
        if s.via is not None:   # 二次贝塞尔弯曲
            mid = np.array(s.via)
            p = (1 - e)[:, None] ** 2 * s.a + 2 * ((1 - e) * e)[:, None] * (mid + (s.a + s.b) / 2 - (s.a.mean(0) + s.b.mean(0)) / 2) + (e ** 2)[:, None] * s.b
        return p, k
def draw_tide(c, cam, tide, u, col, head, a=1.0, size=3.2, trail=0.035, jitter=0.0, t=0.0):
    if a <= 0.003: return
    p1, k = tide.pos(u); p0, _ = tide.pos(max(0, u - trail))
    S_ = cam.S; m0 = merc(cam.lon, cam.lat)
    def proj(p):
        x = (p[:, 0] + 180) / 360; lat = np.radians(p[:, 1])
        y = (1 - np.arcsinh(np.tan(lat)) / np.pi) / 2
        return np.stack([cam.ax + (x - m0[0]) * S_, cam.ay + (y - m0[1]) * S_], 1)
    q1 = proj(p1); q0 = proj(p0)
    if jitter:
        q1 = q1 + np.stack([np.sin(t * 7 + tide.ph), np.cos(t * 6 + tide.ph * 1.3)], 1) * jitter
    pt = skia.Paint(AntiAlias=True, Color=rgba(col, 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=size)
    pt.setStrokeCap(skia.Paint.kRound_Cap)
    pth = skia.Path()
    moving = (k > 0.001) & (k < 0.999)
    for i in np.nonzero(moving)[0]:
        pth.moveTo(*q0[i]); pth.lineTo(*q1[i])
    c.drawPath(pth, pt)
    ph = skia.Paint(AntiAlias=True, Color=rgba(head, a), Style=skia.Paint.kStroke_Style, StrokeWidth=size * 1.25)
    ph.setStrokeCap(skia.Paint.kRound_Cap)
    pts = [skia.Point(float(x), float(y)) for x, y in q1]
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, ph)

class Crowd:
    """驻守/溃散的兵团：静止时轻微抖动，溃散时向外逃散并淡出。"""
    def __init__(s, n, ctr, r, seed=3, flee=(0.0, 0.02)):
        g = np.random.default_rng(seed); s.n = n
        ang = g.uniform(0, 2 * np.pi, n); rad = np.sqrt(g.uniform(0, 1, n))
        s.p = np.stack([ctr[0] + np.cos(ang) * rad * r[0], ctr[1] + np.sin(ang) * rad * r[1]], 1)
        dirv = g.normal(0, 1, (n, 2)) * 0.6 + np.array(flee) / (np.hypot(*flee) + 1e-9)
        s.v = dirv * g.uniform(0.02, 0.06, (n, 1)) * np.array([1, 0.8]); s.ph = g.uniform(0, 6.28, n)
        s.die = g.uniform(0, 1, n)
def draw_crowd(c, cam, cr, rout, col, edge, a=1.0, size=3.6, t=0.0, kill=0.0):
    if a <= 0.003: return
    r = ease(rout)
    p = cr.p + cr.v * r
    alive = cr.die >= kill
    al = np.clip(1.2 - r * 1.1, 0, 1)
    S_ = cam.S; m0 = merc(cam.lon, cam.lat)
    x = (p[:, 0] + 180) / 360; y = (1 - np.arcsinh(np.tan(np.radians(p[:, 1]))) / np.pi) / 2
    q = np.stack([cam.ax + (x - m0[0]) * S_, cam.ay + (y - m0[1]) * S_], 1)
    q += np.stack([np.sin(t * 3 + cr.ph), np.cos(t * 2.6 + cr.ph)], 1) * (0.8 + 3.5 * r)
    pe = skia.Paint(AntiAlias=True, Color=rgba(edge, 0.85 * a * al), Style=skia.Paint.kStroke_Style, StrokeWidth=size + 2.2)
    pe.setStrokeCap(skia.Paint.kSquare_Cap)
    pc = skia.Paint(AntiAlias=True, Color=rgba(col, a * al), Style=skia.Paint.kStroke_Style, StrokeWidth=size)
    pc.setStrokeCap(skia.Paint.kSquare_Cap)
    pts = [skia.Point(float(a_), float(b_)) for (a_, b_), ok in zip(q, alive) if ok]
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, pe); c.drawPoints(skia.Canvas.kPoints_PointMode, pts, pc)

def dust(c, cam, ll, t, a=1.0, r=120, n=14, seed=5, col='#B89A72'):
    if a <= 0.003: return
    g = np.random.default_rng(seed); x0, y0 = cam.p(*ll)
    for i in range(n):
        ph = g.uniform(0, 6.28); sp = g.uniform(0.15, 0.4); rr = g.uniform(0.4, 1.0) * r
        u = (t * sp + g.uniform(0, 1)) % 1.0
        x = x0 + math.cos(ph) * rr * (0.4 + u) ; y = y0 + math.sin(ph) * rr * 0.5 * (0.4 + u) - u * 40
        circle(c, x, y, rr * (0.35 + 0.6 * u), col, 0.16 * a * (1 - u), blur=rr * 0.3)

def arrows_rain(c, cam, src, dst, t, a=1.0, n=26, seed=9, spread=(0.01, 0.006), col='#F7E6C4'):
    """箭雨：自高处向低处的弧线短划。"""
    if a <= 0.003: return
    g = np.random.default_rng(seed)
    for i in range(n):
        off = g.uniform(0, 1); per = g.uniform(0.9, 1.4)
        u = ((t / per) + off) % 1.0
        sx = src[0] + g.normal(0, spread[0]); sy = src[1] + g.normal(0, spread[1])
        dx = dst[0] + g.normal(0, spread[0] * 1.5); dy = dst[1] + g.normal(0, spread[1] * 1.5)
        x0, y0 = cam.p(sx, sy); x1, y1 = cam.p(dx, dy)
        def at(v):
            return x0 + (x1 - x0) * v, y0 + (y1 - y0) * v - math.sin(math.pi * v) * 90
        pa = at(u); pb = at(max(0, u - 0.06))
        line(c, [pb, pa], col, 1.8, 0.75 * a * math.sin(math.pi * u))

def fire(c, x, y, t, a=1.0, s=1.0, seed=0):
    if a <= 0.003: return
    fl = 0.8 + 0.2 * math.sin(t * 13 + seed) * math.sin(t * 7.3 + seed * 2)
    glow(c, x, y, 70 * s * fl, '#FF7A1E', 0.55 * a)
    for k in range(5):
        u = ((t * 1.6 + k / 5 + seed * 0.17) % 1.0)
        circle(c, x + math.sin(seed + k * 2.1 + t * 3) * 8 * s, y - u * 46 * s, (9 - 6 * u) * s, '#FFC25A', 0.8 * a * (1 - u))
    circle(c, x, y - 4 * s, 7 * s, '#FFE3A0', 0.9 * a * fl)

def camp(c, cam, ll, r, a=1.0, label=None, fac='cao', burn=0.0, t=0.0, sub=None, side='r'):
    """营围：鹿角栅栏环 + 营帐。r 为经纬度半径。"""
    if a <= 0.003: return
    col, dk, lt = FAC[fac]
    x, y = cam.p(*ll); x1, _ = cam.p(ll[0] + r, ll[1]); R = abs(x1 - x)
    pts = [(x + math.cos(k / 24 * 6.283) * R, y + math.sin(k / 24 * 6.283) * R * 0.62) for k in range(25)]
    line(c, pts, INK, 7, 0.7 * a)
    line(c, pts, lt, 3, 0.95 * a, dash=(9, 6))
    for k in range(24):
        px, py = pts[k]; ang = k / 24 * 6.283
        line(c, [(px, py), (px + math.cos(ang) * 10, py + math.sin(ang) * 7 - 6)], lt, 2, 0.8 * a)
    for i in range(5):
        tx = x + (i - 2) * R * 0.28; ty = y + ((i % 2) - 0.5) * R * 0.2
        pth = skia.Path(); pth.moveTo(tx - 13, ty + 9); pth.lineTo(tx, ty - 11); pth.lineTo(tx + 13, ty + 9); pth.close()
        c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
        c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba(lt, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6))
    if burn > 0:
        for k in range(0, 24, 3):
            px, py = pts[k]; fire(c, px, py, t, a * burn, 0.7, seed=k)
    if label:
        lx = x + R + 18 if side == 'r' else x - R - 18
        text(c, label, lx, y + 10, 30, lt, 'sans', a, 'l' if side == 'r' else 'r', stroke=5, shadow=5)
        if sub: text(c, sub, lx, y + 44, 22, '#E7DEC8', 'sansm', a, 'l' if side == 'r' else 'r', stroke=4)

def hill_glow(c, cam, ll, a, t, col=LIU, r=120):
    if a <= 0.003: return
    x, y = cam.p(*ll)
    glow(c, x, y, r * (1 + 0.05 * math.sin(t * 3)), col, 0.75 * a)
    pulse(c, x, y, t, col, 20, r * 1.1, 2.0, a, 2, 3)

def banner(c, x, y, h, t, a=1.0, col=LIU, ch='漢', s=1.0, wind=1.0):
    """旗：旗杆 + 波动旗面。"""
    if a <= 0.003: return
    line(c, [(x, y), (x, y - h)], '#2A1D14', 6 * s, a); line(c, [(x, y), (x, y - h)], '#8A6A44', 3 * s, a)
    fw, fh = 150 * s, 104 * s; top = y - h + 8 * s
    def pt(u, v):
        wv = math.sin(u * 5.2 - t * 5.5) * 10 * s * u * wind
        return x + u * fw, top + v * fh + wv
    pth = skia.Path(); N = 16
    pth.moveTo(*pt(0, 0))
    for i in range(1, N + 1): pth.lineTo(*pt(i / N, 0))
    for i in range(N, -1, -1): pth.lineTo(*pt(i / N, 1))
    pth.close()
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#000000', 0.45 * a), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#FFD9A8', 0.6 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2 * s))
    cx, cy = pt(0.48, 0.5)
    text(c, ch, cx, cy + 22 * s, 64 * s, '#FFF0D8', 'serifx', a, 'c')

# ================= 场景 =================
SC = []
def scene(b0, b1, pre=0.0, post=0.0):
    def deco(fn):
        SC.append([S(b0) - pre if b0 else 0.0, (E(b1) + post) if b1 else T.total, fn]); return fn
    return deco
def seam(): # 连续场景首尾相接：下一场起点 = 本场终点
    SC.sort(key=lambda x: x[0])
    for i in range(len(SC) - 1): SC[i][1] = SC[i + 1][0]

DJS = (106.585, 33.088)        # 定军山（示意位置）
NANWEI = (106.640, 33.128)     # 南围（夏侯渊）
DONGWEI = (106.735, 33.140)    # 东围（张郃）
YPG = (106.560, 33.168)        # 阳平关

# ---------- 片头：定军山冲锋 ----------
TIDE_OPEN = Tide(1700, DJS, NANWEI, (0.035, 0.016), (0.022, 0.009), seed=2, delay=0.45)
CROWD_OPEN = Crowd(900, NANWEI, (0.026, 0.011), seed=4, flee=(0.05, 0.06))
@scene(None, 'h04')
def sc_open(c, t):
    tr = Track([(0.0, C(106.612, 33.114, 0.13, 900)), (S('h03') + 1.0, C(106.618, 33.116, 0.22, 860)), (S('h04'), C(106.66, 33.12, 0.95, 820)), (E('h04') + 0.4, C(106.75, 33.13, 1.6, 820))])
    cam = tr(t); draw_base(c, cam, ('#2A0E08', 0.18))
    draw_rivers(c, cam, 0.9)
    u = ramp(t, -4.5, S('h03') + 4.0)              # 第一帧已在冲锋途中
    rout = ramp(t, S('h03') + 2.0, S('h04') + 2)
    camp(c, cam, NANWEI, 0.03, 1.0 - 0.6 * ramp(t, S('h03') + 3, S('h04')), '夏侯渊 · 南围', burn=ss(ramp(t, 1.2, 3.0)), t=t)
    draw_crowd(c, cam, CROWD_OPEN, rout, CAO, CAO_L, 1.0, 4.0, t, kill=0.5 * rout)
    dust(c, cam, (DJS[0] * 0.5 + NANWEI[0] * 0.5, DJS[1] * 0.5 + NANWEI[1] * 0.5), t, 0.9, 160, 18)
    draw_tide(c, cam, TIDE_OPEN, u, LIU, '#FF6E52', 1.0, 4.6, 0.07, t=t)
    arrows_rain(c, cam, DJS, NANWEI, t, 0.9 * (1 - ramp(t, S('h03'), S('h04'))), 34)
    hill_glow(c, cam, DJS, 0.7, t, LIU, 90)
    x, y = cam.p(*DJS); text(c, '定军山', x - 20, y + 70, 40, '#FFE3CF', 'serifx', 1, 'c', stroke=6, shadow=10, spacing=10)
    ga = fade(t, -1.0, S('h03') + 1.5, 0.01, 0.8)   # 首帧即满显
    big_caption(c, '金鼓振天', ga, 560, 168, sub='《三国志·黄忠传》')
    a2 = vis(t, S('h04') - 0.4, 99999, 0.8)
    region_label(c, cam, (106.95, 33.30), '汉 中 盆 地', a2, 46)
    mountain_label(c, cam, (106.9, 33.62), '秦 岭', a2, 40); mountain_label(c, cam, (106.9, 32.75), '大 巴 山', a2, 40)

# ---------- 曹操：不信 ----------
@scene('h05', 'h06')
def sc_cao(c, t):
    cam = Track([(S('h05') - 0.5, C(107.6, 33.6, 3.6, 760)), (E('h06'), C(108.0, 33.8, 3.0, 760))])(t)
    draw_base(c, cam, ('#05050A', 0.45))
    draw_rivers(c, cam, 0.6)
    x, y = cam.p(*D.CITY['长安'])
    glow(c, x, y, 160, '#D9B65A', 0.35)
    unit(c, x, y, 'cao', '曹操', 1.0, 1.3, sub='长安')
    ax, ay = cam.p(*NANWEI)
    pulse(c, ax, ay, t, LIU, 10, 90, 1.6, 0.9)
    text(c, '汉中 · 夏侯渊战死', ax, ay + 70, 30, '#FFCDBE', 'sans', 1, 'c', stroke=5)
    line(c, [(ax, ay), (x, y)], '#D9B65A', 2, 0.6, dash=(10, 10), phase=-t * 40)

# ---------- 一张地图（情景演绎） ----------
def parchment(c, t, cam_ll, span, a=1.0, prog=1.0, notes=(), top=260, hgt=760, label=True):
    """羊皮/绢本地图：深棕框内的褐色益州地形，墨线河道逐步画出。"""
    if a <= 0.003: return
    x0, y0, w, h = 70, top, 940, hgt
    rrect(c, x0 - 10, y0 + 14, w + 20, h, 10, '#000000', 0.6 * a, blur=30)
    rrect(c, x0 - 14, y0 - 14, w + 28, h + 28, 8, '#4A2F18', a)
    c.save(); c.clipRect(skia.Rect.MakeXYWH(x0, y0, w, h))
    cam = Cam(cam_ll[0], cam_ll[1], span, x0 + w / 2, y0 + h / 2)
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, h), skia.Paint(Color=rgba('#C9AE80', a)))
    c.saveLayer(None, skia.Paint(ColorFilter=_cf_sepia, Alphaf=0.75 * a))
    base(9).draw(c, cam); c.restore()
    # 墨线河道
    for pts, cls, name in D.RIVERS:
        if cls < 0.9: continue
        q = PP(cam, pts); q = trim(q, 0, prog)
        line(c, q, '#3A230F', 1.5 + cls * 1.2, 0.85 * a)
    for n in ('成都', '雒城', '涪城', '葭萌', '江州', '白帝', '阆中'):
        x, y = cam.p(*D.CITY[n])
        circle(c, x, y, 7, '#7A1E12', a * ss(ramp(prog, 0.3, 0.6))); text(c, n, x + 12, y + 9, 26, '#2B1A0C', 'serif', a * ss(ramp(prog, 0.3, 0.6)))
    for i, (s, ll, ap) in enumerate(notes):
        if ap <= 0.003: continue
        x, y = cam.p(*ll)
        rrect(c, x - 6, y - 30, tw(s, 'serif', 26) + 16, 38, 3, '#7A1E12', 0.88 * a * ap)
        text(c, s, x + 2, y - 3, 26, '#F8E9D0', 'serif', a * ap)
    # 纸纹
    g = np.random.default_rng(3)
    for k in range(40):
        yy = y0 + g.uniform(0, h); line(c, [(x0, yy), (x0 + w, yy + g.normal(0, 3))], '#6B4A26', 1, 0.05 * a)
    c.restore()
    p = skia.Paint(AntiAlias=True, Color=rgba('#D8B66A', 0.7 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2)
    c.drawRect(skia.Rect.MakeXYWH(x0 - 4, y0 - 4, w + 8, h + 8), p)
    if label: tag(c, x0 + w - 6, y0 + h + 26, '情景演绎', '#D8B66A', a * 0.9, 22, 'r', fa=0.7, fname='sansm')

@scene('h07', 'h07')
def sc_scroll(c, t):
    c.clear(rgba('#0D0B09'))
    u = ramp(t, S('h07') + 1.0, E('h07'))
    parchment(c, t, (105.4, 30.9), 6.2 + 0.4 * (1 - u), vis(t, S('h07') - 0.3, E('h07') + 0.5, 0.6, 0.1), ss(u))
    text(c, '益州 · 山川地图', W / 2, 1110, 44, '#E8D6B0', 'serifx', vis(t, S('h07') + 2, 9e9), 'c', spacing=8)

# ---------- 入蜀概览 ----------
@scene('h08', 'h11')
def sc_enter(c, t):
    cam = Track([(S('h08') - 0.4, C(108.6, 31.2, 11.5, 760)), (S('h09') + 0.3, C(106.0, 31.6, 5.5, 760)), (E('h11'), C(105.7, 32.2, 3.2, 760))])(t)
    draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    terr(c, cam, D.T_YI, ZHANG, 0.9); terr(c, cam, D.T_HZ, ZL, 0.8); terr(c, cam, D.T_JING, LIU, 0.9)
    region_label(c, cam, (104.3, 29.9), '益州 · 刘璋', vis(t, S('h08'), 9e9), 40, ZHANG_L)
    region_label(c, cam, (106.9, 33.25), '汉中 · 张鲁', vis(t, S('h08') + 2.5, 9e9), 34, ZL_L)
    region_label(c, cam, (111.4, 28.5), '荆州 · 刘备', vis(t, S('h08'), E('h08')), 38, LIU_L)
    u = ramp(t, S('h08') + 1.5, E('h08') - 0.5)
    route = PP(cam, D.R_ENTER + D.R_FU_JIAMENG[1:])
    arrow(c, route, LIU, u, 7, 1.0, 24, dash=(18, 12))
    cities(c, cam, ['江陵', '成都', '涪城', '葭萌'], 1.0, None, 28, major=('成都',), facs={'江陵': 'liu', '成都': 'zhang', '涪城': 'zhang', '葭萌': 'zhang'})
    x, y = cam.p(*D.CITY['葭萌'])
    a = vis(t, S('h09'), 9e9)
    unit(c, x + 4, y - 50, 'liu', '刘备', a, 1.0, sub='客军', label_side='r')
    hb = vis(t, S('h10'), 9e9, 0.8)
    if hb > 0:
        for k in range(3):
            uu = ((t - S('h10')) / 2.4 + k / 3) % 1.0
            circle(c, x, y, 30 + uu * 260, '#FFB26B', 0.55 * hb * (1 - uu), stroke=3)
        glow(c, x, y, 140, '#FF9A50', 0.4 * hb)
        text(c, '收人心', x, y + 110, 40, '#FFE2C2', 'serifx', hb, 'c', stroke=6, shadow=8, spacing=8)

@scene('h12', 'h12')
def sc_flash(c, t):
    k = ramp(t, S('h12'), E('h12'))
    cam = Track([(S('h12') - 0.3, C(104.4, 31.0, 2.8, 760)), (S('h12') + 3.4, C(104.4, 31.0, 2.5, 760)), (S('h12') + 4.4, C(106.6, 33.0, 2.2, 760))])(t)
    draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    turn = ss(ramp(t, S('h12') + 1.0, S('h12') + 2.6))
    terr(c, cam, D.T_YI, mix(ZHANG, LIU, turn), 1.0)
    terr(c, cam, D.T_HZ, mix(ZL, LIU, ss(ramp(t, S('h12') + 5.0, S('h12') + 6.5))), 0.9)
    x, y = cam.p(*D.CITY['成都'])
    city(c, x, y, '成都', 'liu' if turn > 0.5 else 'zhang', 1, 34, major=True)
    pulse(c, x, y, t, LIU, 14, 120, 1.4, turn)
    tag(c, x + 30, y + 40, '214 · 刘璋出降', LIU, vis(t, S('h12') + 1.2, S('h12') + 4.2), 26)
    x2, y2 = cam.p(106.9, 33.1)
    banner(c, x2, y2 + 40, 190, t, vis(t, S('h12') + 4.6, 9e9), LIU, '漢', 0.9)
    tag(c, x2 + 40, y2 + 80, '219 · 汉中王', LIU, vis(t, S('h12') + 5.0, 9e9), 26)

@scene('h13', 'h14')
def sc_question(c, t):
    cam = C(106.0, 31.5, 7.5 + 0.3 * ramp(t, S('h13'), E('h14')), 760)
    draw_base(c, cam, ('#050507', 0.66))
    a1 = vis(t, S('h13') - 0.1, 9e9, 0.5); a2 = vis(t, S('h14') - 0.1, 9e9, 0.5)
    text(c, '客人', 300, 610, 120, ZHANG_L, 'serifx', a1, 'c', shadow=12); text(c, '主人', 780, 610, 120, LIU_L, 'serifx', a1 * ss(ramp(t, S('h13') + 1.2, S('h13') + 2.0)), 'c', shadow=12)
    arrow(c, [(420, 570), (650, 570)], '#E8D6B0', ss(ramp(t, S('h13') + 0.5, S('h13') + 1.3)), 6, a1, 22, glow=False)
    text(c, '？', 540, 760, 110, '#F4E6C2', 'serifx', a1, 'c')
    text(c, '屡战屡败', 300, 990, 92, '#B9C0C8', 'serifx', a2, 'c', shadow=12); text(c, '赢曹操', 790, 990, 92, LIU_L, 'serifx', a2 * ss(ramp(t, S('h14') + 1.4, S('h14') + 2.2)), 'c', shadow=12)
    arrow(c, [(490, 955), (660, 955)], '#E8D6B0', ss(ramp(t, S('h14') + 0.8, S('h14') + 1.5)), 6, a2, 22, glow=False)

# ---------- 壹 入蜀 ----------
@scene('r01', 'r10', pre=T.chap[1][1] - T.chap[1][0] + 0.3)
def sc_r_big(c, t):
    tr = Track([(T.chap[1][0], C(108.2, 30.9, 15.5, 780)), (S('r04'), C(108.0, 31.0, 13.5, 780)), (S('r10'), C(108.4, 31.0, 12.5, 780))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.8)
    aj = vis(t, -1, 9e9)
    terr(c, cam, D.T_JING, LIU, aj); terr(c, cam, D.T_SUN, SUN, 0.6); terr(c, cam, D.T_CAO, CAO, 0.9)
    terr(c, cam, D.T_YI, ZHANG, vis(t, S('r03'), 9e9)); terr(c, cam, D.T_HZ, ZL, vis(t, S('r05'), 9e9))
    region_label(c, cam, (111.3, 28.3), '荆州', aj, 44, LIU_L, sub='刘备 · 赤壁之后')
    region_label(c, cam, (104.2, 29.8), '益州', vis(t, S('r03'), 9e9), 50, ZHANG_L, sub='刘璋')
    region_label(c, cam, (107.0, 33.25), '汉中', vis(t, S('r05'), 9e9), 34, ZL_L, sub='张鲁')
    region_label(c, cam, (110.5, 35.4), '曹操', 0.9, 44, CAO_L)
    region_label(c, cam, (117.0, 29.5), '孙权', 0.8, 40, SUN_L)
    # 隆中对两步
    a2 = vis(t, S('r02'), E('r03') + 0.3)
    arrow(c, PP(cam, [(112.0, 29.6), (108.8, 30.2), (105.8, 30.6)]), '#F4E6C2', ss(ramp(t, S('r02') + 1.5, S('r02') + 3.0)), 6, a2, 22, dash=(12, 10))
    arrow(c, PP(cam, [(112.1, 30.6), (112.4, 32.4), (112.6, 33.8)]), '#F4E6C2', ss(ramp(t, S('r02') + 3.2, S('r02') + 4.4)), 5, a2 * 0.8, 20, dash=(10, 10))
    arrow(c, PP(cam, [(104.8, 31.5), (106.0, 33.0), (107.6, 34.0)]), '#F4E6C2', ss(ramp(t, S('r02') + 3.4, S('r02') + 4.6)), 5, a2 * 0.8, 20, dash=(10, 10))
    tag(c, 70, 300, '隆中对：跨有荆、益，两路北伐', '#E2C27A', a2, 28)
    cities(c, cam, ['江陵', '成都', '长安', '许'], 1, None, 26, facs={'江陵': 'liu', '成都': 'zhang', '长安': 'cao', '许': 'cao'})
    # 曹操欲讨张鲁
    a5 = vis(t, S('r05') + 2.5, E('r06') + 0.4)
    arrow(c, PP(cam, [D.CITY['长安'], (108.2, 34.0), (107.4, 33.4)]), '#D9B65A', ss(ramp(t, S('r05') + 3, S('r05') + 4.5)), 8, a5, 26)
    arrow(c, PP(cam, [(107.0, 32.9), (105.8, 31.6), (104.6, 30.9)]), '#D9B65A', ss(ramp(t, S('r06'), S('r06') + 1.6)), 6, a5 * 0.8, 22, dash=(10, 9))
    # 张松之计：请刘备
    a7 = vis(t, S('r07'), 9e9)
    x, y = cam.p(*D.CITY['成都'])
    if a7 > 0: unit(c, x - 60, y + 150, 'zhang', '张松', a7, 0.8, sub='别驾', label_side='l')
    a10 = vis(t, S('r10'), 9e9)
    arrow(c, PP(cam, D.R_FAZHENG), ZHANG_L, ss(ramp(t, S('r10') + 1.0, S('r10') + 4.0)), 5, a10, 20, dash=(10, 8))
    if a10 > 0:
        xe, ye = cam.p(*D.CITY['江陵'])
        tag(c, xe - 20, ye + 40, '法正 · 四千人来迎', ZHANG, a10 * ss(ramp(t, S('r10') + 3, S('r10') + 3.6)), 24, 'r')

@scene('r11', 'r12c')
def sc_r_insider(c, t):
    cam = C(105.0, 30.9, 6.5, 760)
    draw_base(c, cam, ('#050507', 0.55))
    # 两枚人物牌：张松、法正，从刘璋阵营（紫）转向刘备（红）
    for i, (nm, sub, cx) in enumerate((('张松', '益州别驾', 330), ('法正', '军议校尉', 750))):
        a = vis(t, S('r11') + 0.2 * i, 9e9)
        k = ss(ramp(t, S('r11') + 1.0 + 0.6 * i, S('r11') + 2.6 + 0.6 * i))
        col = mix(ZHANG, LIU, k)
        circle(c, cx, 560, 118, '#000000', 0.5 * a, blur=20)
        circle(c, cx, 560, 112, col, a); circle(c, cx, 560, 112, '#F4E6C2', 0.8 * a, stroke=3)
        text(c, nm, cx, 588, 78, '#FFF5E6', 'serifx', a, 'c')
        text(c, sub, cx, 720, 32, '#E2D6C2', 'sansm', a, 'c')
    a2 = vis(t, S('r11b'), E('r11c') + 0.2)
    tag(c, 330, 790, '忖「璋不足與有為」', ZHANG, a2, 30, 'c'); tag(c, 750, 790, '「志意不得」', ZHANG, a2, 30, 'c')
    a3 = vis(t, S('r11c'), E('r11c'))
    text(c, '不得志的能人＝最好的内应', W / 2, 940, 50, '#F4E6C2', 'serifx', a3, 'c', shadow=10)
    text(c, '《三国志·法正传》', W / 2, 990, 26, '#CDBF9C', 'serifm', a2, 'c')

@scene('r13', 'r17')
def sc_r_scroll(c, t):
    c.clear(rgba('#0D0B09'))
    u = ramp(t, S('r13'), E('r15'))
    notes = [('府库', (104.2, 30.4), ss(ramp(t, S('r14') + 1.2, S('r14') + 1.8))), ('兵器', (104.7, 31.3), ss(ramp(t, S('r14') + 1.8, S('r14') + 2.4))),
             ('人马', (105.6, 30.2), ss(ramp(t, S('r14') + 2.4, S('r14') + 3.0))), ('要害', (105.6, 32.0), ss(ramp(t, S('r14') + 3.4, S('r14') + 4.0))),
             ('道里', (106.6, 31.2), ss(ramp(t, S('r14') + 4.2, S('r14') + 4.8)))]
    parchment(c, t, (105.6, 30.9), 6.0, vis(t, S('r13') - 0.4, 9e9, 0.5), ss(u), notes, top=200, hgt=740)
    a = vis(t, S('r17'), 9e9)
    text(c, '仗还没打，情报战已经赢了', W / 2, 1020 if not QA(t) else 160, 46, '#FFE2C2', 'serifx', a * (0 if QA(t) else 1), 'c', shadow=10)

@scene('r18', 'r26')
def sc_r_route(c, t):
    tr = Track([(S('r18') - 0.4, C(108.4, 30.9, 9.5, 760)), (S('r19'), C(105.6, 31.0, 5.2, 760)), (S('r22'), C(105.2, 31.6, 4.0, 740)), (S('r24'), C(105.5, 32.0, 3.0, 740))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.85, ('Fu', 'Jialing'), vis(t, S('r18') + 2, E('r19')))
    terr(c, cam, D.T_YI, ZHANG, 0.9); terr(c, cam, D.T_HZ, ZL, 0.8)
    u = ramp(t, S('r18') + 1.0, E('r18') + 2.0)
    arrow(c, PP(cam, D.R_ENTER), LIU, u, 7, 1.0, 24, dash=(18, 12))
    u2 = ramp(t, S('r22') + 0.5, E('r22'))
    arrow(c, PP(cam, D.R_FU_JIAMENG), LIU, u2, 7, vis(t, S('r22'), 9e9), 24, dash=(18, 12))
    cities(c, cam, ['成都', '涪城', '葭萌', '江州', '白帝', '江陵', '阆中'], 1, 'zhang', 27, major=('成都',), facs={'江陵': 'liu'})
    tag(c, 70, 300, '刘备 · 步卒数万 · 溯江西进', LIU, vis(t, S('r18'), E('r18') + 1.5), 28)
    x, y = cam.p(*D.CITY['涪城'])
    am = vis(t, S('r19'), E('r21') + 0.3)
    unit(c, x - 60, y - 52, 'zhang', '刘璋', am, 0.9, label_side='l'); unit(c, x + 60, y - 52, 'liu', '刘备', am, 0.9, label_side='r')
    if am > 0:
        glow(c, x, y - 52, 90, '#FFD48A', 0.35 * am)
        tag(c, x, y + 36, '涪城相会 · 相见甚欢', '#E2C27A', am, 26, 'c')
    a20 = vis(t, S('r20'), E('r21'))
    if a20 > 0:
        text(c, '会上袭璋？', x, y - 140, 40, '#FF9C86', 'serifx', a20 * (1 - ss(ramp(t, S('r21'), S('r21') + 1))), 'c', stroke=5, shadow=6)
        text(c, '「此大事也，不可倉卒。」', x, y - 140, 38, '#F4E6C2', 'serifx', a20 * ss(ramp(t, S('r21'), S('r21') + 0.8)), 'c', stroke=5, shadow=6)
    xg, yg = cam.p(*D.CITY['葭萌'])
    ag = vis(t, S('r23'), 9e9)
    unit(c, xg + 6, yg - 56, 'liu', '三万余人', ag, 1.15, sub='车甲器械资货甚盛', label_side='r')
    hb = vis(t, S('r24') + 1.0, 9e9, 0.8)
    if hb > 0:
        for k in range(3):
            uu = ((t - S('r24')) / 2.6 + k / 3) % 1.0
            circle(c, xg, yg, 30 + uu * 300, '#FFB26B', 0.5 * hb * (1 - uu), stroke=3)
        xz, yz = cam.p(106.9, 33.15)
        line(c, [(xg, yg - 30), (xz, yz)], '#C3C8CE', 3, 0.6 * hb, dash=(6, 10))
        text(c, '不打张鲁', (xg + xz) / 2 + 30, (yg + yz) / 2, 34, '#E6E1D8', 'sans', hb, 'l', stroke=5)

def QA(t):
    """当前是否有古文卡/类比卡（用于避让）。"""
    for k, (b0, b1, q) in QUOTES.items():
        if S(b0) - 0.2 <= t <= E(b1) + 0.6: return True
    return False

@scene('r27', 'r30')
def sc_r_q3(c, t):
    cam = C(105.5, 32.0, 3.6, 760)
    draw_base(c, cam, ('#050507', 0.55))
    prog = [ramp(t, S('r28'), S('r28') + 1), ramp(t, S('r29'), S('r29') + 1), ramp(t, S('r30'), S('r30') + 1)]
    q3_card(c, Q3, vis(t, S('r27'), 9e9), 470, prog)

@scene('r31', 'r33')
def sc_r_analogy(c, t):
    cam = C(105.0, 31.2, 6.0, 700)
    draw_base(c, cam, ('#050507', 0.40))
    terr(c, cam, D.T_YI, ZHANG, 0.9)
    x, y = cam.p(*D.CITY['葭萌'])
    unit(c, x, y - 40, 'liu', '受邀的客军', 1, 1.0, label_side='r')
    xc, yc = cam.p(*D.CITY['成都']); city(c, xc, yc, '成都', 'zhang', 1, 30, major=True)
    a3 = vis(t, S('r33'), 9e9)
    if a3 > 0:
        text(c, '背 盟', W / 2, 620, 110, '#FF8C72', 'serifx', a3, 'c', stroke=8, shadow=14, spacing=30)
        text(c, '照实讲，不洗白', W / 2, 690, 34, '#F1E6E2', 'sansm', a3, 'c', stroke=5)

# ---------- 贰 取成都 ----------
@scene('c01', 'c06', pre=T.chap[2][1] - T.chap[2][0] + 0.3)
def sc_c_turn(c, t):
    tr = Track([(T.chap[2][0], C(105.1, 31.75, 4.0, 820)), (S('c04'), C(105.0, 31.7, 3.7, 820)), (S('c06'), C(104.7, 31.2, 2.8, 760))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    terr(c, cam, D.T_YI, ZHANG, 0.9); terr(c, cam, D.T_HZ, ZL, 0.8)
    cities(c, cam, ['成都', '雒城', '绵竹', '涪城', '葭萌', '白水关', '梓潼', '剑阁'], 1, 'zhang', 26, major=('成都',))
    xg, yg = cam.p(*D.CITY['葭萌'])
    solid = ss(ramp(t, S('c04') + 1.0, S('c04') + 1.6))
    # 客军虚线 → 实线
    if solid < 1: arrow(c, PP(cam, D.R_FU_JIAMENG), LIU, 1.0, 6, 0.8 * (1 - solid), 22, dash=(18, 12), glow=False)
    a2 = vis(t, S('c02'), E('c03') + 0.5)
    tag(c, 70, 300, '刘备求兵一万 · 刘璋只给四千', ZHANG, a2, 28)
    xc, yc = cam.p(*D.CITY['成都'])
    a3 = vis(t, S('c03'), E('c04'))
    if a3 > 0:
        unit(c, xc + 70, yc - 10, 'zhang', '张松', a3 * (1 - 0.6 * ss(ramp(t, S('c03') + 1.5, S('c03') + 2.2))), 0.8, label_side='r')
        k = ss(ramp(t, S('c03') + 1.5, S('c03') + 2.0)); line(c, [(xc + 40, yc - 40), (xc + 100, yc + 20)], '#FF5A3C', 6, a3 * k); line(c, [(xc + 100, yc - 40), (xc + 40, yc + 20)], '#FF5A3C', 6, a3 * k)
        for nm in ('白水关', '剑阁', '梓潼'):
            x, y = cam.p(*D.CITY[nm]); kk = ss(ramp(t, S('c03') + 3.0, S('c03') + 3.8))
            rrect(c, x - 26, y - 8, 52, 16, 3, ZHANG, a3 * kk); rrect(c, x - 26, y - 8, 52, 16, 3, '#FFFFFF', 0, stroke='#FFFFFF', sw=1.5)
    unit(c, xg + 6, yg - 56, 'liu', '刘备', 1.0, 1.0, label_side='r')
    if solid > 0:
        u = ramp(t, S('c04') + 1.2, E('c04') + 1.0)
        arrow(c, PP(cam, D.R_TURN), LIU, u, 11, solid, 34)
        x1, y1 = cam.p(*D.CITY['白水关'])
        k = ss(ramp(t, S('c04') + 0.4, S('c04') + 1.0)); tag(c, x1 - 40, y1 - 50, '斩杨怀', '#FF5A3C', vis(t, S('c04') + 0.3, E('c05')), 26, 'r')
        flash = math.exp(-max(0, t - (S('c04') + 1.1)) * 3.0) * (t > S('c04') + 1.0)
        glow(c, xg, yg, 260, '#FF6040', 0.7 * flash)
    a5 = vis(t, S('c05'), E('c05') + 0.3)
    big_caption(c, '客军 → 攻城之军', a5, 430, 72, spacing=6)
    a6 = vis(t, S('c06'), 9e9)
    if a6 > 0:
        xf, yf = cam.p(*D.CITY['涪城']); xm, ym = cam.p(*D.CITY['绵竹'])
        unit(c, xf, yf - 50, 'liu', None, a6, 0.9)
        u = ss(ramp(t, S('c06'), S('c06') + 2.0))
        unit(c, xf + (xm - xf) * u - 40, yf - 10 + (ym - yf) * u, 'zhang', '刘璝、张任等', a6, 0.85, label_side='l', strength=1 - 0.5 * u)
        k = ss(ramp(t, S('c06') + 3.2, S('c06') + 4.2))
        unit(c, xm + 50, ym + 30, 'liu' if k > 0.5 else 'zhang', '李严', a6 * ss(ramp(t, S('c06') + 2.5, S('c06') + 3.0)), 0.8, sub='率众来降' if k > 0.5 else None, label_side='r')
        if k > 0: pulse(c, xm + 50, ym + 30, t, LIU, 10, 60, 1.2, k)

@scene('c06b', 'c06g')
def sc_c_zhengdu(c, t):
    cam = Track([(S('c06b') - 0.4, C(104.9, 31.0, 3.0, 720)), (E('c06g'), C(104.9, 31.0, 2.7, 720))])(t)
    draw_base(c, cam, ('#0A0705', 0.25))
    draw_rivers(c, cam, 0.85, ('Fu',), vis(t, S('c06d'), E('c06d') + 1))
    terr(c, cam, D.T_YI, ZHANG, 0.8)
    cities(c, cam, ['成都', '雒城', '绵竹', '涪城'], 1, 'zhang', 26, major=('成都',), facs={'涪城': 'liu'})
    xf, yf = cam.p(*D.CITY['涪城'])
    unit(c, xf + 40, yf - 50, 'liu', '刘备', 1.0, 0.95, label_side='r')
    a = vis(t, S('c06c'), E('c06c') + 0.6)
    if a > 0:
        rows = ['兵不满万', '士众未附', '军无辎重', '野谷是资']
        for i, r in enumerate(rows):
            aa = a * ss(ramp(t, S('c06c') + 0.8 + i * 0.9, S('c06c') + 1.2 + i * 0.9))
            tag(c, 640, 250 + i * 66, r, '#FF8C72', aa, 32, fname='serif')
        text(c, '郑度看穿的软肋', 640, 220, 26, '#E6D9C4', 'sansm', a)
    # 坚壁清野：粮仓与野谷一一点火
    a4 = vis(t, S('c06d'), E('c06e') + 0.3)
    k_out = ss(ramp(t, S('c06f'), S('c06f') + 1.2))
    g = np.random.default_rng(8)
    for i in range(16):
        lon = g.uniform(104.0, 104.6); lat = g.uniform(30.7, 31.5)
        x, y = cam.p(lon, lat)
        on = ss(ramp(t, S('c06d') + 1.0 + i * 0.18, S('c06d') + 1.4 + i * 0.18))
        fire(c, x, y, t, a4 * on * (1 - k_out), 0.6, seed=i)
    if a4 > 0:
        tag(c, 70, 300, '郑度之计：坚壁清野，不过百日', '#E2C27A', a4, 28)
    a5 = vis(t, S('c06e'), E('c06e'))
    if a5 > 0:
        tag(c, xf + 40, yf + 40, '法正：「終不能用，無可憂也」', LIU, a5, 26)
    a6 = vis(t, S('c06f'), 9e9)
    if a6 > 0:
        x0, y0 = 80, 250
        tag(c, x0, y0, '郑度之计', '#9A9590', a6, 30)
        line(c, [(x0, y0 + 24), (x0 + 170, y0 + 24)], '#FF5A3C', 5, a6 * ss(ramp(t, S('c06f') + 0.6, S('c06f') + 1.2)))
        text(c, '刘璋：不用', x0 + 190, y0 + 34, 32, '#D8CCF2', 'sans', a6, stroke=5)

@scene('c07', 'c12')
def sc_c_siege(c, t):
    tr = Track([(S('c07') - 0.4, C(104.4, 30.95, 1.9, 740)), (S('c09'), C(107.6, 30.5, 9.4, 760), E('c09') - S('c09')), (S('c10') + 0.5, C(105.0, 30.4, 4.6, 760)), (S('c11'), C(104.25, 30.8, 1.8, 760)), (S('c12'), C(104.6, 30.9, 3.8, 760))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    capture = ss(ramp(t, S('c11') + 1.0, S('c11') + 2.5))
    terr(c, cam, D.T_YI, mix(ZHANG, LIU, capture), 0.9); terr(c, cam, D.T_JING, LIU, 0.8)
    luo_fall = ss(ramp(t, S('c10'), S('c10') + 1.2))
    cities(c, cam, ['成都', '雒城', '绵竹', '涪城', '江州', '白帝', '江阳', '江陵'], 1, None, 26, major=('成都',),
           facs={'成都': 'liu' if capture > 0.5 else 'zhang', '雒城': 'liu' if luo_fall > 0.5 else 'zhang', '绵竹': 'liu', '涪城': 'liu', '江州': 'liu' if t > S('c09') + 3 else 'zhang',
                 '白帝': 'liu' if t > S('c09') + 2 else 'zhang', '江阳': 'liu' if t > S('c09') + 4 else 'zhang', '江陵': 'liu'})
    # 雒城之围
    xl, yl = cam.p(*D.CITY['雒城'])
    a7 = vis(t, S('c07'), E('c08') + 0.5)
    if a7 > 0:
        for k in range(14):
            ang = k / 14 * 6.283 + t * 0.15; R = 95
            circle(c, xl + math.cos(ang) * R, yl + math.sin(ang) * R * 0.7, 9, LIU, a7)
        line(c, [(xl + math.cos(a_ / 40 * 6.283) * 95, yl + math.sin(a_ / 40 * 6.283) * 66) for a_ in range(41)], LIU_L, 2, 0.6 * a7, dash=(6, 6), phase=t * 20)
        tag(c, xl + 110, yl - 90, '围攻将近一年', LIU, a7, 26)
        arrows_rain(c, cam, (104.22, 30.93), D.CITY['雒城'], t, a7 * 0.8, 18, spread=(0.02, 0.015))
    a8 = vis(t, S('c08'), E('c08') + 0.3)
    if a8 > 0:
        x, y = xl - 140, yl + 80
        rrect(c, x - 10, y - 34, 250, 80, 6, '#0A0A0D', 0.8 * a8)
        text(c, '庞统 · 中流矢卒', x, y, 30, '#F4E6C2', 'serif', a8); text(c, '年三十六（《庞统传》）', x, y + 34, 22, '#CDBF9C', 'sansm', a8)
    # 三路溯江
    a9 = vis(t, S('c09'), E('c10') + 0.6)
    for i, (r, nm) in enumerate(((D.R_ZL, '诸葛亮'), (D.R_ZF, '张飞'), (D.R_ZY, '赵云'))):
        u = ramp(t, S('c09') + 0.3 + i * 0.25, E('c09') + 1.5)
        pts = PP(cam, r); arrow(c, pts, LIU, u, 7, a9, 24)
        if u > 0.05:
            x, y, _ = along(pts, u); text(c, nm, x + 14, y - 18 - i * 4, 28, LIU_L, 'sans', a9, stroke=5)
    # 成都
    xc, yc = cam.p(*D.CITY['成都'])
    a11 = vis(t, S('c10') + 1.5, 9e9)
    if a11 > 0:
        for k in range(18):
            ang = k / 18 * 6.283; R = 80 - 8 * ss(ramp(t, S('c11'), S('c11') + 1.5))
            circle(c, xc + math.cos(ang) * R, yc + math.sin(ang) * R * 0.75, 8, LIU, a11)
        pulse(c, xc, yc, t, LIU, 12, 140, 1.5, capture)
        tag(c, xc + 40, yc + 50, '建安十九年（214）· 刘璋出降', LIU, capture * a11, 26)
    a12 = vis(t, S('c12'), 9e9)
    if a12 > 0:   # 三十年时间条
        x0, x1, y = 120, 960, 300
        rrect(c, x0 - 30, y - 70, x1 - x0 + 60, 140, 10, '#0A0A0D', 0.78 * a12)
        line(c, [(x0, y), (x0 + (x1 - x0) * ease(ramp(t, S('c12') + 0.5, S('c12') + 3.0)), y)], LIU, 8, a12)
        text(c, '184 起兵 · 23 岁', x0, y - 22, 28, '#E8DCC0', 'sans', a12); text(c, '214 得益州 · 53 岁', x1, y + 46, 28, LIU_L, 'sans', a12 * ss(ramp(t, S('c12') + 2.6, S('c12') + 3.2)), 'r')
        text(c, '三十年', (x0 + x1) / 2, y + 46, 30, '#F4E6C2', 'serifx', a12, 'c')

@scene('c13', 'c15')
def sc_c_fuzi(c, t):
    cam = C(104.5, 30.9, 4.0, 700)
    draw_base(c, cam, ('#050507', 0.55))
    terr(c, cam, D.T_YI, LIU, 0.7)
    a = vis(t, S('c13'), E('c13') + 0.3)
    if a > 0:
        rrect(c, 70, 330, 940, 200, 8, '#0A0A0D', 0.82 * a)
        text(c, '赵戬（曹操丞相掾）', 110, 390, 30, '#B9C0C8', 'sans', a)
        text(c, '「拙於用兵，每戰則敗」', 110, 470, 52, '#D9DEE4', 'serifx', a)
        text(c, '—— 《先主傳》裴注引《傅子》', 980, 515, 24, '#9AA3AC', 'serifm', a, 'r')
    a15 = vis(t, S('c15') + 1.0, 9e9)
    if a15 > 0:
        text(c, '赢的不是一场仗', W / 2, 430, 64, '#F4E6C2', 'serifx', a15, 'c', shadow=10)
        text(c, '是情报与人心', W / 2, 520, 64, LIU_L, 'serifx', a15 * ss(ramp(t, S('c15') + 1.8, S('c15') + 2.6)), 'c', shadow=10)

# ---------- 叁 汉中 ----------
@scene('z01', 'z05', pre=T.chap[3][1] - T.chap[3][0] + 0.3)
def sc_z_intro(c, t):
    tr = Track([(T.chap[3][0], C(106.4, 32.0, 7.5, 780)), (S('z02'), C(106.8, 32.6, 6.5, 780)), (S('z03'), C(106.6, 32.3, 6.0, 780))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    terr(c, cam, D.T_YI, LIU, 0.9)
    lost = ss(ramp(t, S('z02') + 1.0, S('z02') + 2.5))
    terr(c, cam, D.T_HZ, mix(ZL, CAO, lost), 1.0); terr(c, cam, D.T_CAO, CAO, 0.8)
    region_label(c, cam, (104.2, 30.0), '益州 · 刘备', 1, 40, LIU_L)
    a1 = vis(t, S('z01'), 9e9)
    x, y = cam.p(107.0, 33.08)
    if a1 > 0:
        pulse(c, x, y, t, '#D9B65A', 14, 110, 1.8, a1 * (1 - lost * 0.5))
        text(c, '益州北大门', x, y - 70, 40, '#F4E6C2', 'serifx', a1, 'c', stroke=6, shadow=8)
    a2 = vis(t, S('z02'), 9e9)
    arrow(c, PP(cam, D.R_CAO215), '#D9B65A', ramp(t, S('z02'), S('z02') + 1.8), 9, a2, 28)
    tag(c, 70, 300, '215 · 曹操亲征，张鲁投降', '#D9B65A', a2 * (1 - vis(t, S('z03'), 9e9)), 28)
    if a2 > 0:
        unit(c, x - 40, y + 60, 'cao', '夏侯渊', a2 * ss(ramp(t, S('z02') + 3, S('z02') + 3.8)), 0.9, label_side='l')
        unit(c, x + 50, y + 60, 'cao', '张郃', a2 * ss(ramp(t, S('z02') + 3.3, S('z02') + 4.1)), 0.9, label_side='r')
    a3 = vis(t, S('z03'), 9e9)
    tag(c, 70, 300, '217 · 法正献策', LIU, a3, 28)
    if a3 > 0:
        xa, ya = cam.p(*D.CITY['长安'])
        arrow(c, PP(cam, [(107.1, 33.3), (107.9, 33.9), D.CITY['长安']]), '#D9B65A', ramp(t, S('z03') + 2.2, S('z03') + 3.6), 6, a3, 22, dash=(10, 9))
        text(c, '「內有憂偪」', xa - 10, ya - 50, 34, '#F4E6C2', 'serifx', a3 * ss(ramp(t, S('z03') + 3.6, S('z03') + 4.2)), 'c', stroke=5)

def hz_labels(c, cam, a, t, more=True):
    mountain_label(c, cam, (106.95, 33.52), '秦  岭', a, 46)
    mountain_label(c, cam, (106.95, 32.74), '大 巴 山', a, 42)
    x, y = cam.p(106.47, 33.10); text(c, '沔水', x, y, 30, '#BFE8FF', 'serifm', a, 'c', stroke=5, shadow=5)
    x, y = cam.p(107.15, 33.035); text(c, '汉水', x, y, 30, '#BFE8FF', 'serifm', a, 'c', stroke=5, shadow=5)
    if more:
        x, y = cam.p(*D.CITY['南郑']); city(c, x, y, '南郑', 'cao', a, 28)

@scene('z06', 'z08')
def sc_z_terrain(c, t):
    tr = Track([(S('z06') - 0.4, C(106.85, 33.12, 1.25, 760)), (S('z07'), C(106.75, 33.14, 0.95, 760)), (S('z08'), C(106.70, 33.14, 0.80, 760))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.95, ('Han',), vis(t, S('z06') + 4.0, E('z06') + 0.5))
    hz_labels(c, cam, vis(t, S('z06') + 0.5, 9e9), t)
    x, y = cam.p(*YPG)
    a = vis(t, S('z07'), 9e9)
    city(c, x, y, '阳平关', None, a, 32, major=True, anchor='r', dx=20)
    if a > 0: pulse(c, x, y, t, '#F4E6C2', 10, 70, 1.8, a * 0.7)
    a8 = vis(t, S('z08'), 9e9)
    if a8 > 0:
        shake = math.sin(t * 9) * 2.5
        unit(c, x - 70 + shake, y + 10, 'liu', '刘备', a8, 0.95, label_side='l')
        unit(c, x + 90 - shake, y + 10, 'cao', '夏侯渊', a8, 0.95, label_side='r')
        unit(c, x + 160 - shake, y + 70, 'cao', '张郃', a8, 0.85, label_side='r')
        tag(c, 70, 300, '218—219 · 阳平关对峙一年', '#E2C27A', a8, 28)

@scene('z09', 'z15')
def sc_z_move(c, t):
    tr = Track([(S('z09') - 0.4, C(106.66, 33.13, 0.62, 760)), (S('z14'), C(106.63, 33.12, 0.50, 720)), (E('z15'), C(106.63, 33.12, 0.48, 720))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.95, ('Han',), vis(t, S('z11'), E('z11')))
    hz_labels(c, cam, 0.85, t, more=False)
    x, y = cam.p(*YPG); city(c, x, y, '阳平关', None, 1, 28, anchor='r', dx=20)
    path = [YPG, (106.565, 33.150), (106.57, 33.125), (106.575, 33.105), DJS]
    u = ramp(t, S('z09') + 0.8, E('z11'))
    arrow(c, PP(cam, path), LIU, u, 14, 1.0, 40)
    up = ss(ramp(t, E('z11') - 1.0, E('z11')))
    hill_glow(c, cam, DJS, up, t, LIU, 130)
    xd, yd = cam.p(*DJS)
    if up > 0:
        text(c, '定军山', xd, yd + 76, 44, '#FFE3CF', 'serifx', up, 'c', stroke=6, shadow=10, spacing=10)
        banner(c, xd - 10, yd - 6, 120, t, up, LIU, '劉', 0.55)
    # 夏侯渊营
    camp(c, cam, NANWEI, 0.022, vis(t, S('z12') - 1, 9e9), '夏侯渊', t=t)
    # 机制一
    a13 = vis(t, S('z13'), 9e9)
    tag(c, 70, 300, '① 抢高地 · 攻守易位', LIU, a13, 34)
    a14 = vis(t, S('z14'), 9e9)
    if a14 > 0:
        u2 = ss(ramp(t, S('z14') + 3.0, S('z14') + 5.0))
        pts = PP(cam, [NANWEI, (106.615, 33.11), (106.60, 33.097)])
        arrow(c, trim(pts, 0, 0.8), '#D9B65A', u2, 9, a14, 28)
        text(c, '来争其地', pts[1][0] + 30, pts[1][1] + 10, 30, '#F4D78F', 'sans', a14 * u2, stroke=5)
    # 剖面小图
    a15 = vis(t, S('z15'), 9e9)
    if a15 > 0: profile(c, t, a15)

def profile(c, t, a):
    """地形剖面：定军山（刘）居高，曹军仰攻。"""
    x0, y0, w, h = 560, 360, 460, 250
    rrect(c, x0, y0, w, h, 8, '#0A0A0D', 0.84 * a)
    text(c, '剖面示意', x0 + 18, y0 + 34, 22, '#CDBF9C', 'sansm', a)
    pts = []
    for i in range(61):
        u = i / 60; hh = 0.15 + 0.75 * math.exp(-((u - 0.28) / 0.17) ** 2) + 0.03 * math.sin(u * 30)
        pts.append((x0 + 20 + u * (w - 40), y0 + h - 20 - hh * (h - 80)))
    poly = pts + [(x0 + w - 20, y0 + h - 20), (x0 + 20, y0 + h - 20)]
    c.drawPath(mkpath(poly, True), skia.Paint(AntiAlias=True, Color=rgba('#5A4A36', a)))
    line(c, pts, '#C9B08A', 2.5, a)
    px, py = pts[17]; unit(c, px, py - 26, 'liu', None, a, 0.6)
    qx, qy = pts[48]; unit(c, qx, qy - 22, 'cao', None, a, 0.6)
    arrow(c, [(qx - 20, qy - 30), (pts[30][0], pts[30][1] - 40)], '#D9B65A', ss(ramp(t % 3.0, 0, 1.6)), 5, a, 18, glow=False)
    text(c, '居高', px, py - 64, 26, LIU_L, 'sans', a, 'c'); text(c, '仰攻', qx, qy - 60, 26, '#F4D78F', 'sans', a, 'c')

@scene('z16', 'z20')
def sc_z_split(c, t):
    cam = Track([(S('z16') - 0.4, C(106.67, 33.12, 0.42, 760)), (E('z20'), C(106.665, 33.12, 0.40, 760))])(t)
    draw_base(c, cam, ('#05060A', 0.25 * vis(t, S('z17'), E('z17') + 1)))
    draw_rivers(c, cam, 0.9)
    tag(c, 70, 300, '② 分兵 · 主将身边被摊薄', LIU, vis(t, S('z16'), 9e9), 34)
    xd, yd = cam.p(*DJS); hill_glow(c, cam, DJS, 0.6, t, LIU, 90); banner(c, xd - 10, yd - 6, 110, t, 1, LIU, '劉', 0.5)
    burn = ss(ramp(t, S('z17') + 0.5, S('z17') + 2.0))
    camp(c, cam, NANWEI, 0.020, 1, '南围 · 夏侯渊', burn=burn * 0.7, t=t, sub='轻兵')
    camp(c, cam, DONGWEI, 0.020, vis(t, S('z17') + 2.0, 9e9), '东围 · 张郃', burn=burn, t=t)
    # 刘军攻东围
    a18 = vis(t, S('z18'), 9e9)
    pts = PP(cam, [DJS, (106.66, 33.105), (106.71, 33.125), DONGWEI])
    arrow(c, trim(pts, 0, 0.92), LIU, ramp(t, S('z18'), S('z18') + 1.6), 11, a18, 32)
    if a18 > 0: arrows_rain(c, cam, (106.70, 33.118), DONGWEI, t, a18, 20, spread=(0.006, 0.004))
    # 夏侯渊兵力一分为二
    xn, yn = cam.p(*NANWEI); xe, ye = cam.p(*DONGWEI)
    half = ss(ramp(t, S('z18') + 2.6, S('z18') + 4.2))
    unit(c, xn, yn - 70, 'cao', None, 1, 1.0, strength=1 - 0.5 * half)
    if half > 0:
        u = half
        unit(c, xn + (xe - xn) * u, yn - 70 + (ye - yn) * u * 0.9, 'cao', '分兵一半', vis(t, S('z18') + 2.6, 9e9), 0.8, label_side='t')
    a20 = vis(t, S('z20'), 9e9)
    if a20 > 0:
        glow(c, xn, yn - 70, 120, '#FFFFFF', 0.12 * a20)
        tag(c, xn - 60, yn + 40, '主将身边：薄薄一层', '#D9B65A', a20, 28, 'r')

TIDE_Z = Tide(2200, DJS, NANWEI, (0.016, 0.008), (0.010, 0.0045), seed=21, delay=0.4)
CROWD_Z = Crowd(700, NANWEI, (0.012, 0.0055), seed=22, flee=(0.06, 0.05))
@scene('z21', 'z24')
def sc_z_charge(c, t):
    tr = Track([(S('z21') - 0.4, C(106.615, 33.108, 0.22, 620)), (S('z22'), C(106.612, 33.106, 0.12, 640)), (S('z24'), C(106.625, 33.112, 0.24, 600))])
    cam = tr(t); draw_base(c, cam, ('#2A0E08', 0.15 * vis(t, S('z22'), 9e9)))
    draw_rivers(c, cam, 0.9)
    u = ramp(t, S('z22') + 0.2, S('z23') + 3.0)
    rout = ramp(t, S('z23') + 0.5, E('z24'))
    camp(c, cam, NANWEI, 0.012, 1 - 0.5 * rout, '夏侯渊', burn=ss(ramp(t, S('z22'), S('z22') + 1)), t=t)
    draw_crowd(c, cam, CROWD_Z, rout, CAO, CAO_L, 1, 5.0, t, kill=0.55 * rout)
    dust(c, cam, ((DJS[0] + NANWEI[0]) / 2, (DJS[1] + NANWEI[1]) / 2), t, vis(t, S('z22'), 9e9), 180, 20)
    draw_tide(c, cam, TIDE_Z, u, LIU, '#FF6E52', 1, 5.4, 0.08, t=t)
    arrows_rain(c, cam, DJS, NANWEI, t, vis(t, S('z22'), E('z23')), 40, spread=(0.004, 0.003))
    xd, yd = cam.p(*DJS); banner(c, xd - 10, yd - 6, 150, t, 1, LIU, '黃', 0.7, 1.6)
    a21 = vis(t, S('z21'), E('z21') + 0.6)
    big_caption(c, '可击矣', a21, 330, 130)
    xn, yn = cam.p(*NANWEI)
    k = ss(ramp(t, S('z23') + 1.2, S('z23') + 1.8))
    if k > 0:
        glow(c, xn, yn, 200, '#FF4030', 0.6 * k * (1 - ramp(t, S('z23') + 2, S('z24'))))
        tag(c, xn + 30, yn - 110, '夏侯渊 战死', '#FF5A3C', k, 34)
    a24 = vis(t, S('z24') + 0.2, 9e9)
    big_caption(c, '一战斩渊', a24, 330, 120)

@scene('z25', 'z28')
def sc_z_collapse(c, t):
    cam = C(106.64, 33.12, 0.5, 760)
    draw_base(c, cam, ('#040406', 0.70))
    tag(c, 70, 300, '③ 主将阵亡 · 体系崩溃', LIU, vis(t, S('z25'), 9e9), 34)
    # 指挥树
    cut = ss(ramp(t, S('z27') + 0.2, S('z27') + 1.0))
    sc_ = ss(ramp(t, S('z27') + 1.0, E('z28')))
    top = (540, 520); mids = [(240, 760), (440, 760), (640, 760), (840, 760)]
    g = np.random.default_rng(5)
    leaves = [(mx + (j - 1.5) * 44, 980) for mx, _ in mids for j in range(4)]
    drift = [(g.normal(0, 1) * 160, g.uniform(40, 260)) for _ in leaves]
    a = vis(t, S('z25'), 9e9)
    for i, m in enumerate(mids):
        flick = 1 - cut * (0.6 + 0.4 * (math.sin(t * 40 + i) > 0))
        line(c, [top, m], '#D9B65A', 3, a * max(0, flick))
        for j in range(4):
            L = leaves[i * 4 + j]; d = drift[i * 4 + j]
            lp = (L[0] + d[0] * sc_, L[1] + d[1] * sc_)
            line(c, [m, lp], '#D9B65A', 1.6, a * (1 - sc_) * 0.8)
            circle(c, lp[0], lp[1], 11, CAO, a * (1 - 0.6 * sc_)); circle(c, lp[0], lp[1], 11, '#D9B65A', a * (1 - 0.5 * sc_), stroke=2)
        mx, my = m[0] + (g.normal() * 30) * sc_, m[1] + 30 * sc_
        circle(c, m[0], m[1], 22, CAO, a); circle(c, m[0], m[1], 22, '#D9B65A', a, stroke=2.5)
    circle(c, top[0], top[1], 44, CAO, a); circle(c, top[0], top[1], 44, '#D9B65A', a, stroke=3)
    text(c, '主将', top[0], top[1] + 12, 32, '#F4D78F', 'serifx', a, 'c')
    text(c, '旗鼓 · 号令 · 赏罚', top[0], top[1] - 70, 30, '#E8DCC0', 'sans', vis(t, S('z26'), 9e9), 'c')
    if cut > 0:
        line(c, [(top[0] - 50, top[1] - 50), (top[0] + 50, top[1] + 50)], '#FF4030', 10, cut * a)
        line(c, [(top[0] + 50, top[1] - 50), (top[0] - 50, top[1] + 50)], '#FF4030', 10, cut * a)
    a28 = vis(t, S('z28'), 9e9)
    if a28 > 0:
        x0, y0 = 120, 1110 if not QA(t) else 1110
        text(c, '交锋', 200, 1130, 34, '#E8DCC0', 'sans', a28, 'c'); text(c, '溃散之后', 760, 1130, 34, '#FF9C86', 'sans', a28, 'c')
        hh1 = 60 * ease(ramp(t, S('z28') + 0.5, S('z28') + 1.5)); hh2 = 210 * ease(ramp(t, S('z28') + 1.5, S('z28') + 3))
        rrect(c, 150, 1080 - hh1 - 20, 100, hh1, 3, '#8C99A8', a28); rrect(c, 710, 1080 - hh2 - 20, 100, hh2, 3, LIU, a28)
        text(c, '示意：伤亡多发生在溃散后', 540, 1180, 24, '#B9B0A0', 'sansm', a28, 'c')

@scene('z29', 'z39')
def sc_z_cao(c, t):
    tr = Track([(S('z29') - 0.4, C(107.6, 33.6, 2.6, 780)), (S('z31'), C(107.4, 33.5, 2.2, 780)), (S('z34'), C(107.3, 33.55, 2.1, 760)), (S('z37'), C(107.6, 33.65, 2.4, 760))])
    cam = tr(t); draw_base(c, cam)
    draw_rivers(c, cam, 0.85)
    mountain_label(c, cam, (107.6, 33.85), '秦  岭', 0.9, 46)
    cities(c, cam, ['长安', '斜谷口', '阳平关', '南郑'], 1, None, 26, facs={'长安': 'cao', '斜谷口': 'cao', '阳平关': 'liu', '南郑': 'liu'})
    xd, yd = cam.p(*DJS); banner(c, xd - 6, yd, 90, t, 1, LIU, '劉', 0.42)
    u = ramp(t, S('z29') + 1.0, E('z29') + 1.5)
    route = PP(cam, D.R_CAO219)
    stall = 0.93
    arrow(c, route, '#D9B65A', min(stall, u), 16, 1.0, 46)
    x, y, _ = along(route, min(stall, u) * 0.98)
    unit(c, x + 30, y - 60, 'cao', '曹操', vis(t, S('z29') + 1, 9e9), 1.2, sub='亲率主力', label_side='r')
    # 据险：红色盾牌
    a35 = vis(t, S('z35'), 9e9)
    for i, ll in enumerate([(106.60, 33.20), (106.75, 33.24), (106.66, 33.11)]):
        xs, ys = cam.p(*ll); k = a35 * ss(ramp(t, S('z35') + 0.3 * i, S('z35') + 0.5 + 0.3 * i))
        if k > 0:
            pth = skia.Path(); pth.moveTo(xs - 18, ys - 20); pth.lineTo(xs + 18, ys - 20); pth.lineTo(xs + 18, ys + 2); pth.quadTo(xs + 14, ys + 18, xs, ys + 26); pth.quadTo(xs - 14, ys + 18, xs - 18, ys + 2); pth.close()
            c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba(LIU, k))); c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#FFE3CF', k), Style=skia.Paint.kStroke_Style, StrokeWidth=2.5))
    # 粮道
    a37 = vis(t, S('z37'), 9e9)
    if a37 > 0:
        line(c, route, '#F4D78F', 3, 0.6 * a37, dash=(8, 10), phase=-t * 30)
        n_bags = 10; left = 1 - ss(ramp(t, S('z37') + 1.0, E('z39')))
        x0, y0 = 90, 250
        rrect(c, x0 - 20, y0 - 50, 520, 150, 8, '#0A0A0D', 0.8 * a37)
        text(c, '曹军粮草', x0, y0 - 10, 28, '#F4D78F', 'sans', a37)
        for i in range(n_bags):
            on = 1.0 if i < n_bags * left else 0.15
            bx = x0 + i * 46; by = y0 + 20
            rrect(c, bx, by, 36, 44, 10, '#C9A45A', a37 * on); text(c, '粮', bx + 18, by + 32, 22, '#3A2508', 'serifx', a37 * on, 'c')
        # 逃亡
        a38 = vis(t, S('z38'), 9e9)
        if a38 > 0:
            text(c, '亡者日多', x0 + 470, y0 - 10, 28, '#FF9C86', 'sans', a38, 'r')
            g = np.random.default_rng(4)
            for k in range(26):
                ph = g.uniform(0, 1); uu = ((t - S('z38')) * 0.25 + ph) % 1.0
                ll = (107.0 + g.normal(0, 0.12), 33.35 + g.normal(0, 0.08))
                xp, yp = cam.p(*ll); circle(c, xp + uu * 60, yp - uu * 90, 4, '#9AA0A8', a38 * (1 - uu))
    a39 = vis(t, S('z39'), 9e9)
    if a39 > 0:
        text(c, '后勤战', W / 2, 520, 92, '#F4E6C2', 'serifx', a39 * (0 if QA(t) else 1), 'c', stroke=8, shadow=12, spacing=20)

@scene('z40', 'z43')
def sc_z_jilei(c, t):
    """帐中：烛火、案几、一碗鸡肋、竹简令「雞肋」（情景演绎）。"""
    c.clear(rgba('#0B0705'))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeRadial((540, 760), 900, [rgba('#3A2210'), rgba('#120A06'), rgba('#050302')], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # 帐幕褶皱
    for i in range(14):
        x = i * 80 + 20; line(c, [(x, 0), (x + 30, 1300)], '#000000', 18, 0.18, blur=8)
    fl = 0.9 + 0.1 * math.sin(t * 11) * math.sin(t * 5.3)
    # 案几
    rrect(c, 120, 900, 840, 60, 6, '#2B170B', 1); rrect(c, 120, 900, 840, 14, 6, '#5A3418', 1)
    rrect(c, 170, 960, 40, 200, 4, '#1E1008', 1); rrect(c, 870, 960, 40, 200, 4, '#1E1008', 1)
    # 烛
    rrect(c, 790, 760, 34, 140, 4, '#E8DCC4', 1)
    glow(c, 807, 735, 360 * fl, '#FFB45A', 0.55)
    pth = skia.Path(); pth.moveTo(807, 690 - 8 * fl); pth.quadTo(822, 730, 807, 752); pth.quadTo(792, 730, 807, 690 - 8 * fl)
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#FFE7A8', 1)))
    # 碗与鸡肋
    zoom = 1 + 0.25 * ease(ramp(t, S('z40'), E('z40') + 2))
    c.save(); c.translate(430, 880); c.scale(zoom, zoom)
    pth = skia.Path(); pth.moveTo(-150, -10); pth.quadTo(0, 120, 150, -10); pth.close()
    c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#3B2A1C')))
    c.drawOval(skia.Rect.MakeLTRB(-150, -30, 150, 10), skia.Paint(AntiAlias=True, Color=rgba('#5C4630')))
    # 肋骨：弯曲细骨 + 零星肉丝
    for k, (dx, ang) in enumerate(((-60, -0.3), (-10, -0.1), (40, 0.15))):
        c.save(); c.translate(dx, -30); c.rotate(math.degrees(ang))
        bp = skia.Path(); bp.moveTo(-8, 10); bp.cubicTo(-30, -40, -10, -110, 30, -140)
        line_p = skia.Paint(AntiAlias=True, Color=rgba('#EADFC8'), Style=skia.Paint.kStroke_Style, StrokeWidth=12); line_p.setStrokeCap(skia.Paint.kRound_Cap)
        c.drawPath(bp, skia.Paint(AntiAlias=True, Color=rgba('#000000', 0.5), Style=skia.Paint.kStroke_Style, StrokeWidth=16))
        c.drawPath(bp, line_p)
        circle(c, -12, -40, 6, '#A0623A', 0.8); circle(c, 6, -95, 5, '#A0623A', 0.7)
        c.restore()
    c.restore()
    # 竹简令
    a = vis(t, S('z40') + 1.5, 9e9)
    for i in range(5):
        rrect(c, 560 + i * 34, 380, 30, 360, 4, '#C8A86C', a); line(c, [(560 + i * 34, 400), (590 + i * 34, 400)], '#6B4A22', 2, a)
    for j, ch in enumerate('雞肋'):
        text(c, ch, 645, 480 + j * 110, 76, '#24140A', 'serifx', a, 'c')
    text(c, '口令', 645, 360, 30, '#E8D6B0', 'sans', a, 'c')
    # 人影：杨修收拾行装
    a41 = vis(t, S('z41'), 9e9)
    if a41 > 0:
        x0 = 240; y0 = 560
        c.drawCircle(x0, y0 - 140, 46, skia.Paint(AntiAlias=True, Color=rgba('#000000', 0.85 * a41)))
        pth = skia.Path(); pth.moveTo(x0 - 110, y0 + 340); pth.quadTo(x0 - 100, y0 - 80, x0, y0 - 90); pth.quadTo(x0 + 100, y0 - 80, x0 + 110, y0 + 340); pth.close()
        c.drawPath(pth, skia.Paint(AntiAlias=True, Color=rgba('#000000', 0.85 * a41)))
        text(c, '主簿 杨修', x0, y0 + 230, 30, '#E8D6B0', 'sans', a41 * (0 if QA(t) and False else 1), 'c')
    tag(c, 70, 300, '情景演绎', '#D8B66A', 0.85, 24, fname='sansm')
    vignette(c, 1.0)

@scene('z44', 'z44')
def sc_z_back(c, t):
    cam = Track([(S('z44') - 0.4, C(107.5, 33.55, 2.4, 780)), (E('z44'), C(107.4, 33.4, 2.0, 780))])(t)
    draw_base(c, cam); draw_rivers(c, cam, 0.85)
    route = PP(cam, D.R_CAO_BACK)
    k = ss(ramp(t, S('z44') + 1.5, S('z44') + 3.0))
    terr(c, cam, D.T_HZ, mix(CAO, LIU, k), 1.0)
    arrow(c, route, '#D9B65A', ramp(t, S('z44'), S('z44') + 2.8), 12, 1 - 0.4 * k, 36)
    cities(c, cam, ['长安', '阳平关', '南郑'], 1, None, 26, facs={'长安': 'cao', '阳平关': 'liu', '南郑': 'liu' if k > 0.5 else 'cao'})
    x, y = cam.p(*D.CITY['南郑']); banner(c, x, y, 160, t, k, LIU, '劉', 0.7)
    tag(c, 70, 300, '219 · 夏五月 · 曹操引军还长安', '#D9B65A', vis(t, S('z44'), 9e9), 28)

@scene('z45', 'z46')
def sc_z_yanyi(c, t):
    cam = C(107.2, 33.3, 2.4, 700); draw_base(c, cam, ('#050507', 0.66))
    yanyi_card(c, YANYI[0], YANYI[1], vis(t, S('z45'), 9e9), 640, ramp(t, S('z46') - 0.2, S('z46') + 0.6))

@scene('z47', 'z49')
def sc_z_sum(c, t):
    cam = C(106.65, 33.12, 0.55, 760); draw_base(c, cam, ('#050507', 0.55))
    items = [('抢高地', '逼对手来攻'), ('趁分兵', '一击斩首'), ('据险不战', '拖垮补给')]
    for i, (a_, b_) in enumerate(items):
        k = vis(t, S('z47') + 0.8 + i * 2.4, 9e9)
        y = 420 + i * 200
        rrect(c, 110, y - 70, 860, 160, 10, '#0A0A0D', 0.8 * k)
        rrect(c, 110, y - 70, 10, 160, 3, LIU, k)
        text(c, '①②③'[i], 170, y + 26, 64, LIU_L, 'serifx', k, 'c')
        text(c, a_, 250, y + 6, 54, '#F4E6C2', 'serifx', k); text(c, b_, 250, y + 60, 32, '#D8CFBE', 'sansm', k)
    a48 = vis(t, S('z48'), 9e9)
    text(c, '出谋：法正', W / 2, 1060, 44, '#F4E6C2', 'serifx', a48, 'c')
    a49 = vis(t, S('z49'), 9e9)
    text(c, '敢押全军：刘备', W / 2, 1140, 52, LIU_L, 'serifx', a49, 'c', shadow=8)

# ---------- 肆 称王 ----------
@scene('k01', 'k03', pre=T.chap[4][1] - T.chap[4][0] + 0.3)
def sc_k_king(c, t):
    """汉中城头：暮色、城垛剪影，朱红大纛升起。"""
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 1300)], [rgba('#1A1424'), rgba('#5A2A22'), rgba('#C86A3A')], [0, 0.6, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    glow(c, 760, 1180, 420, '#FFB070', 0.45)
    # 远山
    g = np.random.default_rng(2); pts = [(0, 1150)]
    for i in range(41): pts.append((i * 27, 1080 - 60 * math.sin(i * 0.33) - g.uniform(0, 40)))
    pts += [(W, 1150), (W, 1300), (0, 1300)]
    c.drawPath(mkpath(pts, True), skia.Paint(AntiAlias=True, Color=rgba('#2A1A1C', 0.9)))
    # 城墙
    wall = skia.Path(); y0 = 1230; wall.moveTo(0, H); wall.lineTo(0, y0)
    for i in range(14):
        x = i * 80; wall.lineTo(x, y0); wall.lineTo(x, y0 - 44); wall.lineTo(x + 44, y0 - 44); wall.lineTo(x + 44, y0);
    wall.lineTo(W, y0); wall.lineTo(W, H); wall.close()
    c.drawPath(wall, skia.Paint(AntiAlias=True, Color=rgba('#0E0A0A')))
    rise = ease(ramp(t, S('k02'), S('k02') + 4.5))
    banner(c, 470, 1190, 220 + 520 * rise, t, 1, LIU, '漢', 1.5, 1.2)
    a3 = vis(t, S('k03'), 9e9)
    big_caption(c, '五十八岁', a3 * (0 if QA(t) else 1), 600, 130)
    tag(c, 70, 300, '建安二十四年（219）· 秋', '#E2C27A', vis(t, S('k01') - 1, 9e9), 28)

@scene('k04', 'k05')
def sc_k_map(c, t):
    cam = Track([(S('k04') - 0.4, C(111.0, 31.5, 19.0, 760), E('k04') - S('k04') + 0.4), (S('k05') + 0.8, C(107.5, 32.6, 6.5, 760))])(t)
    draw_base(c, cam); draw_rivers(c, cam, 0.8)
    terr(c, cam, D.T_CAO, CAO, 1); terr(c, cam, D.T_SUN, SUN, 0.9)
    terr(c, cam, D.T_YI, LIU, 1); terr(c, cam, D.T_HZ, LIU, 1); terr(c, cam, D.T_JING, LIU, 1)
    region_label(c, cam, (105.5, 30.5), '刘备', 1, 56, LIU_L); region_label(c, cam, (112.0, 36.0), '曹操', 1, 56, CAO_L); region_label(c, cam, (117.5, 28.5), '孙权', 1, 56, SUN_L)
    a5 = vis(t, S('k05'), 9e9)
    if a5 > 0:
        x, y = cam.p(*D.CITY['南郑']); city(c, x, y, '南郑', 'liu', a5, 32, major=True)
        tag(c, x + 30, y + 40, '前206 · 刘邦为汉王，都南郑', '#E2C27A', a5, 26)

@scene('k06', 'k08b')
def sc_k_analogy(c, t):
    cam = C(107.0, 32.0, 6.0, 640); draw_base(c, cam, ('#050507', 0.5))
    terr(c, cam, D.T_YI, LIU, 1); terr(c, cam, D.T_HZ, LIU, 1)
    a = vis(t, S('k08b'), 9e9)
    if a > 0:
        u = ease(ramp(t, S('k08b') + 1.0, E('k08b')))
        x, y = 540 + 300 * u, 520 - 200 * u
        rrect(c, x - 70, y - 70, 140, 140, 10, '#B8862E', a * (1 - 0.6 * u)); rrect(c, x - 60, y - 60, 120, 120, 6, '#000000', 0, stroke='#3A2508', sw=3)
        text(c, '左將軍', x, y - 6, 34, '#2A1804', 'serifx', a * (1 - 0.6 * u), 'c'); text(c, '印綬', x, y + 38, 30, '#2A1804', 'serifx', a * (1 - 0.6 * u), 'c')
        text(c, '上还印绶 · 从此不是任何人的部下', W / 2, 760, 38, '#F4E6C2', 'serifx', a, 'c', shadow=8)

@scene('k09', 'k11')
def sc_k_peak(c, t):
    cam = Track([(S('k09') - 0.4, C(109.5, 31.5, 11.0, 760)), (E('k11'), C(109.8, 31.4, 10.0, 760))])(t)
    draw_base(c, cam); draw_rivers(c, cam, 0.8)
    lost = ss(ramp(t, S('k10') + 0.8, S('k10') + 2.4))
    terr(c, cam, D.T_CAO, CAO, 1); terr(c, cam, D.T_SUN, SUN, 0.9)
    terr(c, cam, D.T_YI, LIU, 1); terr(c, cam, D.T_HZ, LIU, 1); terr(c, cam, D.T_JING, mix(LIU, SUN, lost), 1)
    a = vis(t, S('k10'), 9e9)
    arrow(c, PP(cam, [(106.8, 33.2), (107.6, 34.0), (108.6, 34.3)]), LIU, 1, 8, a, 26)
    p2 = PP(cam, [(112.1, 30.6), (112.3, 32.0), (112.6, 33.6)])
    arrow(c, p2, LIU, 1, 8, a * (1 - lost), 26)
    if lost > 0:
        x, y = p2[1]
        line(c, [(x - 40, y - 40), (x + 40, y + 40)], '#FF4030', 9, lost * a); line(c, [(x + 40, y - 40), (x - 40, y + 40)], '#FF4030', 9, lost * a)
        tag(c, x + 50, y - 20, '219 · 关羽失荆州', '#B6C9D4', lost * a, 26)
    region_label(c, cam, (111.6, 28.5), '荆州', 1, 44, mix(LIU_L, SUN_L, lost))
    a9 = vis(t, S('k09'), E('k09') + 0.4)
    big_caption(c, '一生的顶点', a9, 440, 96)

# ---------- 伍 清点 ----------
LEDGER = [('族叔刘元起', '资助读书', 'e02'), ('名师卢植', '同学公孙瓒', 'e02'), ('马贩张世平、苏双', '资助起兵', 'e03'),
          ('徐州精英', '陈登、糜竺', 'e04'), ('左将军', '高级名分', 'e05'), ('「天下英雄」', '曹操的评级', 'e05'),
          ('隆中对', '战略', 'e06'), ('荆州', '根据地', 'e06'), ('益州', '立国之本', 'e06')]
@scene('e01', 'e08', pre=T.chap[5][1] - T.chap[5][0] + 0.3)
def sc_e_ledger(c, t):
    c.clear(rgba('#0C0A09'))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, H)], [rgba('#17120F'), rgba('#0A0807')])); c.drawRect(skia.Rect.MakeWH(W, H), p)
    n = len(LEDGER)
    for i, (a_, b_, bid) in enumerate(LEDGER):
        sub_i = sum(1 for j in range(i) if LEDGER[j][2] == bid)
        k = ss(ramp(t, S(bid) + 0.8 + sub_i * 1.4, S(bid) + 1.4 + sub_i * 1.4))
        x = 90 + i * 62; y = 1180 - i * 92
        rrect(c, x, y, 1080 - x - 60, 74, 6, '#16110E', 0.92 * k)
        rrect(c, x, y, 8, 74, 2, LIU, k)
        text(c, a_, x + 30, y + 50, 36, '#F4E6C2', 'serifx', k); text(c, b_, 1080 - 80, y + 48, 26, '#CDBF9C', 'sansm', k, 'r')
    # 登阶的红点
    prog = sum(ss(ramp(t, S(b) + 0.8 + sum(1 for j in range(i) if LEDGER[j][2] == b) * 1.4, S(b) + 1.4 + sum(1 for j in range(i) if LEDGER[j][2] == b) * 1.4)) for i, (_, _, b) in enumerate(LEDGER))
    if prog > 0:
        i = min(n - 1, int(prog - 1e-6)); fr = prog - i
        x = 90 + i * 62 - 26; y = 1180 - i * 92 + 37
        glow(c, x, y, 50, LIU, 0.8); circle(c, x, y, 12, '#FFD2C2', 1)
    a7 = vis(t, S('e07'), 9e9)
    top = 1180 - (n - 1) * 92
    if a7 > 0:
        rrect(c, 90 + n * 62 - 40, top - 130, 300, 90, 8, LIU, a7)
        text(c, '汉中王', 90 + n * 62 + 110, top - 70, 52, '#FFF2E4', 'serifx', a7, 'c', spacing=10)
    a8 = vis(t, S('e08'), 9e9)
    if a8 > 0:
        rrect(c, 56, 1300, 968, 200, 10, '#0A0A0D', 0.9 * a8)
        p2 = skia.Paint(AntiAlias=True, Color=rgba('#D8B66A', 0.8 * a8), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(57, 1301, 966, 198), 10, 10), p2)
        text(c, '可迁移的一句判断', 96, 1350, 26, '#D8B66A', 'sans', a8)
        for j, l in enumerate(wrap('受邀进场的人，最值钱的不是被给予的资源，而是在场内积累的信息与人心。', 'serifx', 40, 880)):
            text(c, l, 96, 1412 + j * 56, 40, '#F4E6C2', 'serifx', a8)

@scene('e09', None)
def sc_e_end(c, t):
    cam = Track([(S('e09') - 0.4, C(106.60, 33.10, 0.55, 860)), (T.total, C(106.62, 33.11, 0.40, 880))])(t)
    draw_base(c, cam, ('#2A0E08', 0.30))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 900)], [rgba('#C86A3A', 0.35), rgba('#C86A3A', 0.0)])); c.drawRect(skia.Rect.MakeWH(W, 900), p)
    a12 = vis(t, S('e12') - 0.3, 9e9, 0.8)
    xd, yd = cam.p(*DJS); banner(c, xd, yd + 40, 260, t, 1 - a12, LIU, '漢', 0.9)
    a11 = vis(t, S('e11'), E('e11') + 0.5)
    big_caption(c, '起 跳', a11, 520, 150, spacing=40)
    a12 = vis(t, S('e12') - 0.3, 9e9, 0.8)
    if a12 > 0:
        dim(c, 0.72 * a12, '#050505')
        rrect(c, W / 2 - 300, 560, 600, 4, 2, '#D9B65A', a12)
        text(c, '下一集', W / 2, 520, 40, '#D9B65A', 'sans', a12, 'c', spacing=12)
        text(c, '曹操篇', W / 2, 720, 140, '#F2E2B4', 'serifx', a12, 'c', spacing=30, shadow=16)
        text(c, '一个宦官家的孙子，怎样被一句评语定了一生', W / 2, 820, 36, '#E6DCC6', 'sansm', a12, 'c')

seam()

# ================= 叠加层 =================
def overlays(c, t):
    # 古文卡
    for k, (b0, b1, q) in QUOTES.items():
        a = fade(t, S(b0) - 0.15, E(b1) + 0.55, 0.45, 0.45)
        if a > 0:
            rv = ramp(t, S(b0) - 0.1, S(b0) + max(1.0, min(3.0, (E(b0) - S(b0)) * 0.8)))
            y = 1010 if k not in ('e09', 'z21', 'z35') else (980 if k != 'e09' else 820)
            if k in ('h05',): y = 980
            quote_card(c, q, a, y, rv)
    for k, (b0, b1, body, bias, bb) in ANALOGY.items():
        a = fade(t, S(b0) - 0.15, E(b1) + 0.5, 0.45, 0.45)
        ab = fade(t, S(bb) - 0.1, E(b1) + 0.5, 0.45, 0.45)
        if a > 0: analogy_card(c, body, a, 820 if k == 'r31' else 900, bias, ab)

def subtitles(c, t):
    s = T.sub_at(t)
    if not s: return
    c0, c1, txt, q, bid = s
    if q and any(S(b0) - 0.2 <= t <= E(b1) + 0.3 for (b0, b1, _) in QUOTES.values()): return   # 引文已在古文卡上
    if bid == 'e08': return   # 与「可迁移判断」卡重复
    a = fade(t, c0 - 0.06, c1 + 0.04, 0.08, 0.08)
    subtitle(c, txt, a, quote=q, y=1580)

def hud(c, t):
    sec = None
    for b in BEATS:
        if S(b['id']) - 2.6 <= t: sec = b['sec']
    dates = {0: None, 1: ('建安十六年', '公元211年'), 2: ('建安十七—十九年', '公元212—214年'), 3: ('建安二十二—二十四年', '公元217—219年'), 4: ('建安二十四年秋', '公元219年'), 5: None}
    d = dates.get(sec)
    in_chap = any(a0 - 0.2 <= t <= a1 + 0.2 for a0, a1 in T.chap.values())
    if d and not in_chap and t < S('e01'):
        a = 0.9
        if any(sc_fn in (sc_z_jilei, sc_k_king) and t0 <= t < t1 for t0, t1, sc_fn in SC): a = 0
        date_tag(c, d[0], a, d[1])

def draw_frame(c, t, fi):
    cur = None; nxt = None
    for i, (t0, t1, fn) in enumerate(SC):
        if t0 <= t < t1: cur = i
    if cur is None: cur = len(SC) - 1 if t >= SC[-1][0] else 0
    t0, t1, fn = SC[cur]
    fn(c, t)
    # 交叉淡化（0.45 秒）
    XF = 0.45
    if cur + 1 < len(SC) and t > t1 - XF:
        k = ss((t - (t1 - XF)) / XF)
        c.saveLayerAlpha(None, int(255 * k)); SC[cur + 1][2](c, t); c.restore()
    top_grad(c, 0.9)
    # 章节卡
    for sec, (a0, a1) in T.chap.items():
        if a0 - 0.1 <= t <= a1 + 0.1: chapter_card(c, sec, ramp(t, a0 - 0.1, a1 + 0.1), SECTIONS[sec])
    overlays(c, t)
    subtitles(c, t)
    hud(c, t)
    corner(c, 1.0, '地图为示意' if fn not in (sc_z_jilei, sc_k_king, sc_e_ledger, sc_question, sc_r_insider) else None)
    vignette(c, 0.8)
    grain(c, fi, 0.018)
