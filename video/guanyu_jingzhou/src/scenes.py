# -*- coding: utf-8 -*-
"""分镜：按时间绘制每一帧。"""
import math, json, numpy as np, skia
from geo import W, H, Cam, Base, merc
from gfx import *
import data as D
from data import CITY
from script import BEATS, SECTIONS
from timeline import TL

T = TL()
S, E = T.S, T.E
B7 = Base('/home/user/work/vid/base7.png'); B9 = Base('/home/user/work/vid/base9.png')
BID = {b['id']: b for b in BEATS}

# ------------------------------------------------------------------ 镜头
AY = 720
C_JL = Cam(112.19, 30.36, 0.9, ay=AY)
C_TH = Cam(112.35, 31.05, 5.4, ay=AY)
C_WIDE = Cam(108.4, 31.2, 12.6, ay=AY)
C_FAN = Cam(112.12, 32.06, 1.7, ay=AY)
C_NORTH = Cam(112.9, 32.85, 5.6, ay=AY)
C_REAR = Cam(112.0, 30.85, 3.9, ay=760)
C_XIANG = Cam(112.6, 28.9, 7.0, ay=AY)
C_EAST = Cam(115.4, 30.9, 8.6, ay=AY)
C_FLEET = Cam(114.35, 30.0, 4.4, ay=AY)
C_POSTS = Cam(112.82, 29.9, 2.25, ay=AY)
C_GA = Cam(112.18, 30.2, 1.5, ay=AY)
C_MC = Cam(112.0, 30.95, 2.6, ay=AY)
C_SY = Cam(111.2, 31.75, 4.6, ay=700)
C_YL = Cam(110.6, 30.8, 6.2, ay=AY)

def _keys():
    K = []
    def k(t0, t1, cam): K.append((t0, t1, cam))
    k(0, 0, C_JL)
    k(S('a3') - 0.3, S('a3') + 3.2, C_TH)
    k(T.title[1] - 0.6, S('b1') + 0.4, C_WIDE)
    k(S('b2') - 0.5, S('b2') + 2.2, C_TH)
    k(S('b3') - 0.6, S('b3') + 2.0, C_FAN)
    k(S('b5') - 0.4, S('b5') + 2.6, C_NORTH)
    k(T.chap[2][0], S('c1') + 0.8, C_REAR)
    k(T.chap[3][0], S('d1') + 0.8, C_XIANG)
    k(S('d2') - 0.3, S('d2') + 2.0, Cam(112.5, 30.0, 5.6, ay=AY))
    k(S('d3') - 0.3, S('d3') + 2.6, C_EAST)
    k(S('d5') - 0.4, S('d5') + 2.0, C_TH)
    k(S('d6') - 0.3, S('d6') + 2.0, Cam(112.5, 30.2, 6.4, ay=AY))
    k(T.chap[4][0], S('e1') + 0.6, C_FLEET)
    k(E('e1') - 1.4, E('e1') + 1.2, C_POSTS)
    k(S('e3') - 0.5, S('e3') + 1.8, C_GA)
    k(S('e4') - 0.3, S('e4') + 2.0, C_JL)
    k(S('e7') - 0.4, S('e7') + 2.4, C_TH)
    k(S('e8') + 1.0, E('e8') - 0.5, C_MC)
    k(T.chap[5][0], S('f1') + 0.6, C_WIDE)
    k(S('f3') - 0.4, S('f3') + 2.0, C_SY)
    k(S('f4') - 0.3, S('f4') + 2.4, C_WIDE)
    k(T.chap[6][0], S('g1') + 0.6, C_MC)
    k(S('g2') - 0.3, S('g2') + 2.4, C_WIDE)
    k(S('g3') - 0.3, S('g3') + 2.2, C_YL)
    k(S('g4') + 0.5, S('g4') + 3.5, C_WIDE)
    k(S('h1') - 1.2, S('h1') + 0.6, Cam(112.19, 30.36, 1.6, ay=AY))
    k(S('h2') - 0.5, S('h2') + 1.2, Cam(111.6, 29.6, 7.5, ay=AY))
    k(S('h3') - 0.5, S('h3') + 1.6, C_WIDE)
    return K
KEYS = _keys()
def cam_at(t):
    cur = KEYS[0][2]; hold0 = 0.0; nxt = None
    for i, (t0, t1, cam) in enumerate(KEYS):
        if t >= t1:
            cur = cam; hold0 = t1; nxt = KEYS[i + 1][0] if i + 1 < len(KEYS) else T.total
        elif t >= t0:
            u = ease((t - t0) / max(1e-6, t1 - t0))
            # 起点是上一个镜头在 t0 时刻（含缓推）的状态
            a = _drift(cur, hold0, t0, KEYS[i][0])
            return Cam.lerp(a, cam, u)
        else: break
    return _drift(cur, hold0, t, nxt if nxt else T.total)
def _drift(cam, t0, t, t_end):
    """镜头停留期间的缓推：每秒约 0.35%。"""
    d = max(0.0, t - t0)
    k = 1.0 - 0.0035 * d
    return Cam(cam.lon, cam.lat + 0.0, cam.span * max(0.86, k), cam.ax, cam.ay)

# ------------------------------------------------------------------ 归属随时间变化
def fac_of(name, t):
    liu = {'成都', '汉中', '阆中', '江州', '白帝', '秭归', '夷陵', '江陵', '公安', '麦城', '临沮', '上庸', '房陵', '武陵', '零陵', '沔阳', '猇亭'}
    sun = {'陆口', '巴丘', '益阳', '长沙', '夏口', '寻阳', '建业', '桂阳', '江夏'}
    cao = {'襄阳', '樊城', '宛', '许都', '洛阳', '长安', '陆浑', '梁', '郏'}
    if name == '公安' and t >= E('e3') - 0.8: return 'sun'
    if name == '江陵' and t >= S('e4') + GATE_OFF: return 'sun'
    if name in ('夷陵', '秭归', '麦城', '临沮', '武陵', '零陵', '猇亭') and t >= S('f1'): return 'sun'
    if name in ('上庸', '房陵') and t >= S('g2') + 3.5: return 'cao'
    return 'liu' if name in liu else 'sun' if name in sun else 'cao' if name in cao else None
GATE_OFF = 6.0   # e4 内城门开启的时刻偏移

def P(cam, name): return cam.p(*CITY[name])
def PL(cam, pts): return [cam.p(lo, la) for lo, la in pts]

# ------------------------------------------------------------------ 底图层
def draw_base(c, cam):
    c.clear(skia.Color(18, 20, 22))
    B7.draw(c, cam)
    k9 = cam.S / (256 * 2 ** 9)
    if k9 > 0.22: B9.draw(c, cam, clamp((k9 - 0.22) / 0.18))

_TM = {}
_TZ = 6; _TN = 256 * 2 ** _TZ
_TX0 = int(merc(97, 42)[0] * _TN); _TY0 = int(merc(97, 42)[1] * _TN)
_TW = int(merc(125, 18)[0] * _TN) - _TX0; _TH = int(merc(125, 18)[1] * _TN) - _TY0
def terr(c, cam, poly, color, a, key=None):
    """势力范围：多边形预先栅格化并羽化成低分辨率蒙版，绘制时只做缩放。"""
    if a <= 0.004: return
    key = key or (id(poly), color)
    if key not in _TM:
        from scipy import ndimage as ndi
        s = skia.Surface(_TW, _TH); cc = s.getCanvas(); cc.clear(0)
        pts = [(merc(lo, la)[0] * _TN - _TX0, merc(lo, la)[1] * _TN - _TY0) for lo, la in poly]
        cc.drawPath(mkpath(pts, True), skia.Paint(AntiAlias=True, Color=skia.ColorWHITE))
        m = s.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255.0
        m = ndi.gaussian_filter(m, 13)
        r, g, b = [int(color.lstrip('#')[k:k + 2], 16) for k in (0, 2, 4)]
        arr = np.zeros((_TH, _TW, 4), np.float32); arr[..., 0] = r * m; arr[..., 1] = g * m; arr[..., 2] = b * m; arr[..., 3] = 255 * m
        _TM[key] = skia.Image.fromarray(arr.astype(np.uint8), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    k = cam.S / _TN; m0 = merc(cam.lon, cam.lat)
    tx = cam.ax + (_TX0 / _TN - m0[0]) * cam.S; ty = cam.ay + (_TY0 / _TN - m0[1]) * cam.S
    x0 = max(0.0, (0 - tx) / k - 2); y0 = max(0.0, (0 - ty) / k - 2); x1 = min(_TW, (W - tx) / k + 2); y1 = min(_TH, (H - ty) / k + 2)
    if x1 <= x0 or y1 <= y0: return
    p = skia.Paint(); p.setAlphaf(clamp(a))
    c.drawImageRect(_TM[key], skia.Rect.MakeLTRB(x0, y0, x1, y1), skia.Rect.MakeLTRB(tx + x0 * k, ty + y0 * k, tx + x1 * k, ty + y1 * k), skia.SamplingOptions(skia.FilterMode.kLinear), p)

def territories(c, cam, t, k=1.0):
    fall = ss(ramp(t, S('e4') + GATE_OFF - 0.5, S('e4') + GATE_OFF + 3.0))
    sy = ss(ramp(t, S('g2') + 3.0, S('g2') + 5.5))
    CAO_T = '#7E9BC4'
    terr(c, cam, D.T_CAO, CAO_T, 0.30 * k)
    terr(c, cam, D.T_SUN, SUN, 0.42 * k)
    terr(c, cam, D.T_YI_CORE, LIU, 0.36 * k)
    terr(c, cam, D.T_SHANGYONG, LIU, 0.36 * k * (1 - sy)); terr(c, cam, D.T_SHANGYONG, CAO_T, 0.30 * k * sy)
    terr(c, cam, D.T_JING, LIU, 0.38 * k * (1 - fall)); terr(c, cam, D.T_JING, SUN, 0.42 * k * fall)

_RP = None
def rivers(c, cam, a=1.0):
    """河流：路径在墨卡托像素坐标里建一次，之后只做画布变换。"""
    global _RP
    if a <= 0.004: return
    N = 256 * 2 ** 9
    if _RP is None:
        _RP = []
        for pts, cls, n in D.RIVERS:
            p = skia.Path()
            for i, (lo, la) in enumerate(pts):
                mx_, my_ = merc(lo, la)
                p.moveTo(mx_ * N, my_ * N) if i == 0 else p.lineTo(mx_ * N, my_ * N)
            _RP.append((p, cls))
    sc = clamp(cam.S / 72000, 0.45, 2.6); k = cam.S / N; m0 = merc(cam.lon, cam.lat)
    c.save(); c.translate(cam.ax - m0[0] * cam.S, cam.ay - m0[1] * cam.S); c.scale(k, k)
    for outline in (True, False):
        for p, cls in _RP:
            if cls < 1 and sc < 0.75: continue
            if outline and cls < 1.5: continue
            w = (1.6 + cls * 2.2) * (0.55 + 0.45 * sc)
            pt = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style)
            pt.setStrokeCap(skia.Paint.kRound_Cap); pt.setStrokeJoin(skia.Paint.kRound_Join)
            if outline: pt.setColor(rgba('#0A1820', 0.45 * a)); pt.setStrokeWidth((w + 3.5) / k)
            else: pt.setColor(rgba('#86BACF' if cls >= 1.5 else '#6E9DB0', (0.95 if cls >= 1.5 else 0.6) * a)); pt.setStrokeWidth(w / k)
            c.drawPath(p, pt)
    c.restore()

def river_labels(c, cam, a=1.0, names=('长江', '汉水')):
    spots = {'长江': [(110.3, 30.95), (114.75, 30.35), (107.6, 30.25)], '汉水': [(111.75, 32.35), (112.9, 30.95), (108.6, 32.75)], '湘水': [(112.8, 27.9)]}
    for n in names:
        for lo, la in spots[n]:
            x, y = cam.p(lo, la)
            if 40 < x < W - 60 and 230 < y < 1330:
                text(c, n, x, y, 26, '#A9D2E2', 'serifm', 0.85 * a, 'c', stroke=4, shadow=4, spacing=6); break

def cities(c, cam, t, names, a=1.0, major=(), subs=None, left=(), up=(), size=None):
    sc = clamp(cam.S / 72000, 0.6, 1.5)
    for n in names:
        x, y = P(cam, n)
        if not (-40 < x < W + 40 and 150 < y < 1700): continue
        sz = size or (35 if n in major else 29) * (0.86 + 0.14 * sc)
        anc = 'r' if n in left else 'l'
        dy = -16 if n in up else 10
        city(c, x, y, n, fac_of(n, t), a, sz, n in major, anchor=anc, dy=dy, sub=(subs or {}).get(n))

def faction_names(c, cam, t, a=1.0):
    for n, (lo, la), col in (('曹', (111.2, 33.75), CAO_L), ('刘', (105.6, 30.9), LIU_L), ('孙', (114.6, 28.6), SUN_L)):
        x, y = cam.p(lo, la)
        text(c, n, x, y, 120, col, 'serifx', 0.16 * a, 'c')

# ------------------------------------------------------------------ 洪水
_fe = np.load('/home/user/work/vid/flood_e.npy'); _fm = json.load(open('/home/user/work/vid/flood_e.json'))
def flood(c, cam, level, t, a=1.0):
    if level <= 0.01 or a <= 0.003: return
    d = level - _fe
    al = np.clip(d / 2.5, 0, 1)
    wob = 0.90 + 0.10 * np.sin(t * 1.6 + np.arange(_fe.shape[1])[None, :] * 0.21 + np.arange(_fe.shape[0])[:, None] * 0.13)
    arr = np.zeros(_fe.shape + (4,), np.float32)
    dep = np.clip(d / 12.0, 0, 1)
    arr[..., 0] = 78 - 34 * dep; arr[..., 1] = 142 - 44 * dep; arr[..., 2] = 178 - 30 * dep
    arr[..., 3] = al * wob * 0.80 * a * 255
    arr[..., :3] *= (arr[..., 3:4] / 255.0)   # premultiply
    img = skia.Image.fromarray(arr.astype(np.uint8), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    n = 256 * 2 ** _fm['z']; k = cam.S / n; m0 = merc(cam.lon, cam.lat)
    tx = cam.ax + (_fm['L'] / n - m0[0]) * cam.S; ty = cam.ay + (_fm['T'] / n - m0[1]) * cam.S
    c.save(); c.translate(tx, ty); c.scale(k, k)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.CubicResampler.Mitchell())); c.restore()

def rain(c, t, a=1.0):
    if a <= 0.003: return
    rng = np.random.default_rng(11)
    xs = rng.uniform(-200, W + 200, 170); ys = rng.uniform(0, H, 170); sp = rng.uniform(900, 1500, 170); ln = rng.uniform(26, 60, 170)
    p = skia.Paint(AntiAlias=True, Color=rgba('#CFE3EE', 0.20 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6)
    for i in range(170):
        y = (ys[i] + sp[i] * t) % (H + 100) - 50; x = xs[i] - 0.22 * ((ys[i] + sp[i] * t) % (H + 100))
        c.drawLine(x + 150, y, x + 150 - ln[i] * 0.22, y + ln[i], p)

PCY, PR = 650, 262
PKY = PCY + PR + 132   # 江面中心线
def plan_river(c, a):
    rrect(c, -20, PKY - 40, W + 40, 96, 30, '#5E9BB3', 0.42 * a, blur=6)
    text(c, '长 江', 110, PKY + 18, 28, '#BFE0EC', 'serifm', 0.8 * a, spacing=10)
def plan_alpha(t):
    a = 1 - ss(ramp(t, S('a3') - 0.2, S('a3') + 1.6)) if t < S('a3') + 2 else 0.0
    return max(a, fade(t, S('e4') + 0.9, S('e7') + 0.9, 0.9, 0.9))
# ------------------------------------------------------------------ 江陵城示意
def city_plan(c, t, a, gate, flag=0.0, cx=540, cy=PCY, R_=PR, name='江陵城', amb=0.0, warm=0.0, sub='（示意）'):
    """方城示意图：城墙、四门、街坊；gate∈[0,1] 南门开启；flag 0=刘 1=孙。"""
    if a <= 0.003: return
    wallc = mix(LIU, SUN, flag)
    # 护城河
    rrect(c, cx - R_ - 26, cy - R_ - 26, 2 * R_ + 52, 2 * R_ + 52, 10, '#4F8FA8', 0.0)
    p = skia.Paint(AntiAlias=True, Color=rgba('#5E9BB3', 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=9)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - R_ - 28, cy - R_ - 28, 2 * R_ + 56, 2 * R_ + 56), 14, 14), p)
    # 城内
    rrect(c, cx - R_, cy - R_, 2 * R_, 2 * R_, 4, '#1B1D1F', 0.82 * a)
    # 街坊
    rng = np.random.default_rng(5); n = 6; g = 2 * R_ / n
    for i in range(n):
        for j in range(n):
            if (i in (2, 3) and j in (2, 3)): continue
            x0 = cx - R_ + i * g + 9; y0 = cy - R_ + j * g + 9
            v = rng.uniform(0.25, 0.5)
            col = mix('#3A3A38', '#E9B15A', warm * rng.uniform(0.35, 1.0))
            rrect(c, x0, y0, g - 18, g - 18, 2, col, (v + 0.35 * warm) * a)
    # 府
    rrect(c, cx - g + 6, cy - g + 6, 2 * g - 12, 2 * g - 12, 3, mix('#5A2A25', '#0B4C52', flag), 0.9 * a)
    text(c, '郡府', cx, cy + 10, 30, PAPER, 'serif', 0.9 * a, 'c')
    # 城墙（留出四门）
    gw = 46
    pw = skia.Paint(AntiAlias=True, Color=rgba('#D9CDB4', a), Style=skia.Paint.kStroke_Style, StrokeWidth=13)
    pk = skia.Paint(AntiAlias=True, Color=rgba(INK, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=19)
    segs = []
    for sx, sy_, ex, ey in ((cx - R_, cy - R_, cx + R_, cy - R_), (cx + R_, cy - R_, cx + R_, cy + R_), (cx + R_, cy + R_, cx - R_, cy + R_), (cx - R_, cy + R_, cx - R_, cy - R_)):
        mx_, my_ = (sx + ex) / 2, (sy_ + ey) / 2; ux, uy = (ex - sx) / (2 * R_), (ey - sy_) / (2 * R_)
        segs.append(((sx, sy_), (mx_ - ux * gw / 2, my_ - uy * gw / 2))); segs.append(((mx_ + ux * gw / 2, my_ + uy * gw / 2), (ex, ey)))
    for (p0, p1) in segs: c.drawLine(*p0, *p1, pk)
    for (p0, p1) in segs: c.drawLine(*p0, *p1, pw)
    # 垛口
    pd = skia.Paint(AntiAlias=True, Color=rgba('#6B6252', a), Style=skia.Paint.kStroke_Style, StrokeWidth=13)
    pd.setPathEffect(skia.DashPathEffect.Make([4, 14], 0)); pd.setStrokeCap(skia.Paint.kButt_Cap)
    for (p0, p1) in segs: c.drawLine(*p0, *p1, pd)
    # 角楼与旗
    for sx, sy_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        rrect(c, cx + sx * R_ - 15, cy + sy_ * R_ - 15, 30, 30, 3, INK, 0.9 * a); rrect(c, cx + sx * R_ - 11, cy + sy_ * R_ - 11, 22, 22, 2, wallc, a)
    # 三座闭着的门
    pg = skia.Paint(AntiAlias=True, Color=rgba('#7A5A32', a), Style=skia.Paint.kStroke_Style, StrokeWidth=9)
    c.drawLine(cx - gw / 2, cy - R_, cx + gw / 2, cy - R_, pg); c.drawLine(cx - R_, cy - gw / 2, cx - R_, cy + gw / 2, pg); c.drawLine(cx + R_, cy - gw / 2, cx + R_, cy + gw / 2, pg)
    # 南门：两扇门向内开启
    ang = gate * math.radians(82)
    gy = cy + R_
    if gate > 0.01:
        lp = skia.Path(); lp.moveTo(cx - gw / 2, gy); lp.lineTo(cx + gw / 2, gy); lp.lineTo(cx + gw * 1.9, gy + 210); lp.lineTo(cx - gw * 1.9, gy + 210); lp.close()
        pl = skia.Paint(AntiAlias=True)
        pl.setShader(skia.GradientShader.MakeLinear([(cx, gy), (cx, gy + 210)], [rgba('#FFD890', 0.55 * gate * a), rgba('#FFD890', 0.0)]))
        pl.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9)); c.drawPath(lp, pl)
    half = gw / 2 + 1
    for sgn in (-1, 1):
        hx = cx + sgn * gw / 2
        ex = hx - sgn * half * math.cos(ang); ey = gy - half * math.sin(ang)
        c.drawLine(hx, gy, ex, ey, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=13))
        c.drawLine(hx, gy, ex, ey, skia.Paint(AntiAlias=True, Color=rgba('#C08A45', a), Style=skia.Paint.kStroke_Style, StrokeWidth=8))
    text(c, '南门', cx + gw / 2 + 16, gy - 20, 22, '#E4DDCF', 'sansm', 0.9 * a, stroke=4)
    text(c, name, cx + R_ - tw(sub, 'sansm', 22) - 6, cy - R_ - 40, 40, PAPER, 'serifx', a, 'r', stroke=6, shadow=8)
    text(c, sub, cx + R_, cy - R_ - 42, 22, '#C9C2B4', 'sansm', a, 'r', stroke=4)
    # 伏兵
    if amb > 0.01:
        for i, (dx, dy_) in enumerate(((-150, -120), (120, -165), (175, 60), (-185, 40))):
            k = ss(ramp(amb, i * 0.15, i * 0.15 + 0.4))
            pulse(c, cx + dx, cy + dy_, t + i * 0.3, AMBER, 8, 34, 1.4, 0.8 * k * a, 2, 2.2)
            circle(c, cx + dx, cy + dy_, 8, AMBER, k * a); text(c, '伏', cx + dx, cy + dy_ - 16, 24, AMBER, 'serif', k * a, 'c', stroke=4)

def wall_gauge(c, level, a, x=64, y=850):
    """樊城城墙水位示意：level∈[0,1] → 水面升至距墙顶数板。"""
    if a <= 0.003: return
    w, h = 372, 250
    panel(c, x, y, w, h, a, r=8, fa=0.80)
    text(c, '樊城城墙 · 水位（示意）', x + 20, y + 36, 24, '#D9D2C2', 'sans', a)
    bx, by, bw, bh = x + 36, y + 62, 120, 150   # 墙体
    # 水
    wl = by + bh - bh * (0.04 + 0.86 * level)
    c.save(); c.clipRect(skia.Rect.MakeXYWH(x + 14, y + 52, w - 28, h - 70))
    pw = skia.Paint(AntiAlias=True, Color=rgba('#3F7FA3', 0.60 * a)); wp = skia.Path(); wp.moveTo(x + 14, wl)
    for i in range(0, w, 12): wp.lineTo(x + 14 + i, wl + 3 * math.sin(i * 0.11 + level * 30))
    wp.lineTo(x + w, y + h); wp.lineTo(x + 14, y + h); wp.close(); c.drawPath(wp, pw); c.restore()
    # 墙（版筑层）
    rrect(c, bx, by, bw, bh, 2, '#B9AA8C', 0.96 * a)
    for i in range(1, 12): line(c, [(bx, by + bh * i / 12), (bx + bw, by + bh * i / 12)], '#7A6E58', 1.4, 0.8 * a, cap='butt')
    for i in range(5): rrect(c, bx + 4 + i * 24, by - 14, 14, 14, 1, '#B9AA8C', 0.96 * a)
    # 水下部分压暗
    if wl < by + bh: rrect(c, bx, max(by, wl), bw, by + bh - max(by, wl), 0, '#1F4C66', 0.55 * a)
    # 标注
    k = ss(ramp(level, 0.75, 1.0))
    line(c, [(bx + bw + 10, by), (bx + bw + 34, by)], GOLD, 2, a * k); line(c, [(bx + bw + 10, wl), (bx + bw + 34, wl)], GOLD, 2, a * k)
    line(c, [(bx + bw + 22, by), (bx + bw + 22, wl)], GOLD, 2, a * k)
    text(c, '城不没者数板', bx + bw + 46, by + 26, 30, '#F6EBCB', 'serif', a * k, stroke=5)
    text(c, '《曹仁传》', bx + bw + 46, by + 56, 20, '#D9D2C2', 'sansm', a * k, stroke=4)
    text(c, '“平地水数丈”', bx + bw + 46, by + 118, 26, '#DCEFF7', 'serif', a * ss(ramp(level, 0.3, 0.6)), stroke=5)
    text(c, '《于禁传》', bx + bw + 46, by + 148, 20, '#D9D2C2', 'sansm', a * ss(ramp(level, 0.3, 0.6)), stroke=4)

# ------------------------------------------------------------------ 各章地图内容
def sec0(c, t, cam):
    a_plan = 1 - ss(ramp(t, S('a3') - 0.2, S('a3') + 1.6))
    g = ease(ramp(t, S('a1') + 2.2, S('a1') + 4.6))
    if a_plan > 0.01:
        dim(c, 0.34 * a_plan)
        plan_river(c, a_plan)
        zz = 1.0 + 0.045 * ramp(t, 0, S('a3') + 1.6)
        c.save(); c.translate(540, PCY); c.scale(zz, zz); c.translate(-540, -PCY)
        city_plan(c, t, a_plan, g)
        c.restore()
        k2 = ss(ramp(t, S('a2') + 0.2, S('a2') + 1.2)) * a_plan
        tag(c, 540 - 150, PCY + PR - 96, '南郡太守  麋芳', LIU_L, k2, 28)
        k3 = ss(ramp(t, S('a2') + 2.6, S('a2') + 3.8)) * a_plan
        for i in range(3): unit(c, 400 + i * 110 - (1 - k3) * 160, PKY + 8, 'sun', None, k3, 0.95, 'fleet')
        unit(c, 540 + 110, PCY + PR + 50, 'sun', '吕蒙', k3, 0.9, label_side='b')
    a_map = ss(ramp(t, S('a3') + 0.4, S('a3') + 2.4))
    if a_map > 0.01:
        territories(c, cam, t, 0.9 * a_map)
        cities(c, cam, t, ['江陵', '公安', '樊城', '襄阳', '陆口', '夷陵'], a_map, major=('江陵', '樊城'), left=('襄阳', '公安'))
        x, y = P(cam, '樊城'); unit(c, x - 10, y + 66, 'liu', '关羽 · 主力', a_map, 1.0, label_side='r')
        x2, y2 = P(cam, '江陵'); unit(c, x2 + 70, y2 + 62, 'sun', '吕蒙', a_map, 0.9, 'fleet', label_side='r')
        line(c, [(x, y + 92), (x2, y2 - 22)], '#E9E2D2', 2.4, 0.55 * a_map, dash=(10, 10))
        mx_, my_ = (x + x2) / 2, (y + y2) / 2
        tag(c, mx_ + 18, my_ - 20, '主帅在前线，后方已易手', GOLD, a_map * ss(ramp(t, S('a3') + 2.6, S('a3') + 3.6)), 24)

def sec1(c, t, cam):
    territories(c, cam, t)
    a = 1.0
    # b1：刘备取汉中、称王
    if t < S('b3'):
        k = ramp(t, S('b1') + 0.6, S('b1') + 3.6)
        vis = fade(t, S('b1'), S('b2') + 1.2, 0.6, 0.8)
        faction_names(c, cam, t, vis)
        arrow(c, PL(cam, D.R_LIU_HZ), LIU, ease(k), 8, vis)
        cities(c, cam, t, ['成都', '汉中', '江陵', '樊城', '长安', '许都', '上庸'], vis, major=('成都', '汉中', '江陵'), left=('长安',))
        x, y = P(cam, '汉中')
        kk = ss(ramp(t, S('b1') + 3.4, S('b1') + 4.2)) * vis
        unit(c, x + 4, y - 58, 'liu', '刘备', kk, 1.0, label_side='r')
        tag(c, x - 330, y - 176, '夏　曹操退兵，刘备取汉中', LIU_L, kk, 24)
        k2 = ss(ramp(t, S('b1') + 4.6, S('b1') + 5.4)) * vis
        tag(c, x - 330, y - 130, '七月　沔阳称汉中王', GOLD, k2, 24)
        pulse(c, x, y, t, GOLD, 12, 60, 1.6, 0.8 * k2)
    # b2：关羽北上围樊
    v2 = fade(t, S('b2') - 0.2, S('b3') + 0.7, 0.8, 0.7)
    if v2 > 0.01:
        k = ease(ramp(t, S('b2') + 0.8, S('b2') + 4.0))
        route = PL(cam, D.R_GUAN_N)
        arrow(c, route, LIU, k, 9, v2)
        cities(c, cam, t, ['江陵', '公安', '樊城', '襄阳', '宛', '夷陵', '陆口', '上庸'], v2, major=('江陵', '樊城'), left=('襄阳', '公安'))
        x, y, _ = along(route, k)
        unit(c, x - 58, y + 8, 'liu', '关羽', v2, 1.0, label_side='l', sub='前将军 · 假节钺')
        fx, fy = P(cam, '樊城'); unit(c, fx + 62, fy - 40, 'cao', '曹仁', v2 * ss(ramp(t, S('b2') + 1.0, S('b2') + 1.8)), 0.85, label_side='r')
    # b3-b4：水淹七军
    v3 = fade(t, S('b3') + 0.4, S('b5') + 1.4, 1.0, 1.0)
    if v3 > 0.01:
        lvl_u = ease(ramp(t, S('b3') + 1.8, S('b4') + 5.5))
        flood(c, cam, 1.0 + 15.0 * lvl_u, t, v3)
        fx, fy = P(cam, '樊城'); sx, sy_ = P(cam, '襄阳')
        # 于禁七军：自北而来，屯于城北
        kin = ease(ramp(t, S('b3') - 0.3, S('b3') + 2.0))
        sink = ss(ramp(t, S('b4') + 1.0, S('b4') + 4.6))
        sc = cam.S / 228700
        for i in range(7):
            ox = (-3 + i) * 58 * sc * 1.0 + (20 if i % 2 else -6) * sc; oy = (-150 - (i % 2) * 62) * sc - (1 - kin) * 330
            ua = v3 * kin * (1 - 0.5 * ss(ramp(sink, i * 0.09, i * 0.09 + 0.4)))
            unit(c, fx + ox, fy + oy, 'cao', None, ua, 0.62 * sc ** 0.5, strength=1 - ss(ramp(sink, i * 0.09, i * 0.09 + 0.4)))
        tag(c, fx - 250 * sc, fy - 318 * sc, '于禁 · 七军', CAO_L, v3 * kin * (1 - sink * 0.2), 26)
        k_no = ss(ramp(sink, 0.75, 1.0)) * v3
        text(c, '皆没', fx + 190 * sc, fy - 196 * sc, 64, '#CFE6F2', 'serifx', k_no, 'l', stroke=8, shadow=10)
        text(c, '步骑三万，尽为所虏', fx + 190 * sc, fy - 150 * sc, 24, '#D9D2C2', 'sansm', k_no, 'l', stroke=5)
        text(c, '《吴主传》', fx + 190 * sc, fy - 122 * sc, 20, '#A8A294', 'sansm', k_no, 'l', stroke=4)
        cities(c, cam, t, ['樊城', '襄阳'], v3, major=('樊城',), left=('襄阳',), size=34)
        unit(c, fx + 150 * sc, fy - 6, 'cao', '曹仁', v3 * 0.95, 0.8, label_side='r', sub='数千人守城')
        # 关羽：围城；水涨后乘船攻
        kb = ss(ramp(t, S('b4') + 2.2, S('b4') + 4.0))
        unit(c, fx - 150 * sc, fy + 120 * sc, 'liu', '关羽', v3 * (1 - kb), 1.0, label_side='l')
        for i in range(3):
            unit(c, fx - (210 - i * 105) * sc + (1 - kb) * -200, fy - (40 + (i % 2) * 54) * sc, 'liu', '关羽 · 乘大船就攻' if i == 2 else None, v3 * kb, 0.8, 'fleet', label_side='r', flag=LIU_L)
        rain(c, t, v3 * (1 - ss(ramp(t, E('b4') - 1.0, E('b4') + 0.8))))
        wall_gauge(c, lvl_u, fade(t, S('b4') + 0.2, S('b5') + 0.6, 0.6, 0.6))
        river_labels(c, cam, v3, ('汉水',))
    # b5：威震华夏
    v5 = fade(t, S('b5') + 0.8, T.chap[2][0] + 0.6, 1.0, 0.6)
    if v5 > 0.01:
        fx, fy = P(cam, '樊城')
        for i in range(3):
            u = ((t - S('b5')) / 3.2 + i / 3) % 1.0
            circle(c, fx, fy, 40 + u * 520, LIU_L, v5 * (1 - u) ** 1.3 * 0.55, stroke=3.5)
        cities(c, cam, t, ['樊城', '襄阳', '宛', '许都', '洛阳', '江陵'], v5, major=('许都', '樊城'), left=('襄阳', '洛阳'), subs={'许都': '汉献帝所在'})
        unit(c, fx - 70, fy + 52, 'liu', '关羽', v5, 1.0, label_side='l')
        for n in ('陆浑', '梁', '郏'):
            x, y = P(cam, n); kk = v5 * ss(ramp(t, S('b5') + 1.6, S('b5') + 2.6))
            glow(c, x, y, 26, LIU, 0.8 * kk); circle(c, x, y, 6, LIU_L, kk); text(c, n, x + 12, y + 8, 22, LIU_L, 'serif', kk, stroke=4)
        x, y = P(cam, '陆浑'); text(c, '群盗遥受羽印号', x - 30, y - 34, 22, '#E4DDCF', 'sansm', v5 * ss(ramp(t, S('b5') + 2.0, S('b5') + 3.0)), stroke=4)
        hx, hy = P(cam, '许都'); k = ease(ramp(t, S('b5') + 3.6, S('b5') + 5.6))
        arrow(c, [(hx - 10, hy - 26), (hx - 60, hy - 130), (hx - 170, hy - 215)], CAO_L, k, 6, v5, dash=(14, 9), glow=False)
        tag(c, hx - 120, hy + 78, '曹操：议徙许都以避其锐', CAO_L, v5 * ss(ramp(k, 0.5, 1.0)), 26)

def sec2(c, t, cam):
    territories(c, cam, t)
    v = fade(t, T.chap[2][0] + 0.8, T.chap[3][0] + 0.5, 0.8, 0.6)
    fx, fy = P(cam, '樊城'); jx, jy = P(cam, '江陵'); gx, gy = P(cam, '公安')
    route = PL(cam, D.R_SUPPLY)
    # 补给线
    broken = ss(ramp(t, S('c5') + 1.2, S('c5') + 3.6))
    line(c, route, INK, 9, 0.5 * v); line(c, route, mix('#E8B87A', '#6B6B6B', broken), 4.5, 0.9 * v, dash=(16, 12), phase=-(t * 26) % 28 if broken < 0.5 else 0)
    for i in range(6):
        u = ((t * 0.085) + i / 6) % 1.0
        if u < 0.96:
            x, y, _ = along(route, u); circle(c, x, y, 7, INK, 0.8 * v * (1 - broken)); circle(c, x, y, 5, '#F4D9A0', v * (1 - broken))
    mx_, my_, _ = along(route, 0.52)
    tag(c, mx_ + 22, my_ - 22, '军资补给线', '#E8B87A', v * (1 - broken) * ss(ramp(t, S('c1') + 1.0, S('c1') + 2.0)), 24)
    kx = ss(ramp(broken, 0.5, 1.0)) * v
    line(c, [(mx_ - 22, my_ - 22), (mx_ + 22, my_ + 22)], '#FF6A55', 7, kx); line(c, [(mx_ + 22, my_ - 22), (mx_ - 22, my_ + 22)], '#FF6A55', 7, kx)
    tag(c, mx_ + 34, my_ - 22, '不悉相救', '#FF6A55', kx, 28, fname='serif')
    cities(c, cam, t, ['江陵', '公安', '樊城', '襄阳', '夷陵', '麦城'], v, major=('江陵', '公安', '樊城'), left=('襄阳', '公安', '麦城'))
    unit(c, fx + 76, fy + 30, 'liu', '关羽', v, 1.0, label_side='r', sub='董督荆州事')
    # 两座城的高亮
    hl = ss(ramp(t, S('c1') + 0.6, S('c1') + 1.8)) * v
    fear = ss(ramp(t, S('c5') + 4.0, S('c6') + 1.0))
    for (x, y) in ((jx, jy), (gx, gy)):
        pulse(c, x, y, t, mix(GOLD, '#FF6A55', fear), 16, 58 + 22 * fear, 1.7 - 0.6 * fear, 0.85 * hl, 2, 3)
    # 人物牌
    k_m = ss(ramp(t, S('c2') + 1.0, S('c2') + 1.8)) * v
    k_s = ss(ramp(t, S('c2') + 2.8, S('c2') + 3.6)) * v
    k_p = ss(ramp(t, S('c7') + 0.6, S('c7') + 1.6)) * v
    tag(c, jx + 30, jy - 62, '麋芳｜南郡太守', LIU_L, k_m, 26)
    tag(c, gx + 30, gy + 26, '士仁｜将军', LIU_L, k_s, 26)
    tag(c, jx + 30, jy - 112, '潘濬｜荆州治中 · 典留州事', LIU_L, k_p, 26)
    # “还当治之”
    k_z = ss(ramp(t, S('c5') + 3.2, S('c5') + 4.2)) * (1 - ss(ramp(t, E('c6') - 0.2, E('c6') + 0.8))) * v
    arrow(c, [(fx - 30, fy + 60), (fx - 70, (fy + jy) / 2), (jx - 34, jy - 40)], '#FF6A55', ease(ramp(t, S('c5') + 3.2, S('c5') + 4.6)), 5, k_z, dash=(12, 8), glow=False)
    text(c, '“还当治之”', fx - 86, (fy + jy) / 2 - 10, 46, '#FFD9C9', 'serifx', k_z, 'r', stroke=8, shadow=10)
    text(c, '惧', jx - 46, jy + 16, 44, '#FFB199', 'serifx', fear * v * (1 - ss(ramp(t, S('c7') - 0.2, S('c7') + 0.6))), 'r', stroke=7)
    text(c, '惧', gx - 110, gy + 60, 44, '#FFB199', 'serifx', fear * v * (1 - ss(ramp(t, S('c7') - 0.2, S('c7') + 0.6))), 'r', stroke=7)
    k_n = ss(ramp(t, S('c7') + 4.6, S('c7') + 5.6)) * v
    tag(c, jx - 400, jy + 150, '后方三人：嫌 · 隙 · 不穆', '#FF6A55', k_n, 28, fname='serif')

def card_mi(c, t):
    """c3–c4：麋芳其人。"""
    a = fade(t, S('c3') + 0.2, E('c4') + 0.2, 0.6, 0.5)
    if a <= 0.003: return
    x, y, w, h = 64, 326, 872, 470
    dim(c, 0.30 * a)
    panel(c, x, y, w, h, a, r=10, fa=0.88)
    rrect(c, x, y, 8, h, 3, LIU, a)
    text(c, '麋芳', x + 36, y + 78, 62, PAPER, 'serifx', a)
    text(c, '字子方 · 东海朐人', x + 180, y + 74, 28, '#D9D2C2', 'serifm', a)
    rows = [(S('c3') + 1.4, '兄', '麋竺：“祖世货殖，僮客万人，赀产巨亿”'),
            (S('c3') + 4.2, '姻', '建安元年，麋竺“进妹于先主为夫人”'),
            (S('c3') + 6.8, '资', '“奴客二千，金银货币以助军资”'),
            (S('c4') + 0.4, '仕', '曹操表为彭城相，“去官，随先主周旋”'),
            (S('c4') + 3.6, '今', '南郡太守，守江陵，“与关羽共事”')]
    yy = y + 138
    for t0, k, s in rows:
        ka = ss(ramp(t, t0, t0 + 0.6)) * a
        rrect(c, x + 36, yy - 30, 40, 40, 4, GOLD, 0.92 * ka); text(c, k, x + 56, yy, 26, INK, 'serif', ka, 'c')
        text(c, s, x + 94, yy + 1, 31, PAPER, 'serif', ka)
        yy += 60
    text(c, '《三国志·麋竺传》', x + w - 28, y + h - 22, 22, '#A8A294', 'sansm', a, 'r')
    k2 = ss(ramp(t, S('c4') + 5.6, S('c4') + 6.4)) * a
    panel(c, x, y + h + 16, w, 96, k2, r=8, fa=0.86)
    text(c, '对照：麋竺为安汉将军，位在诸葛亮之上，却“未尝有所统御”。', x + 26, y + h + 54, 26, '#E4DDCF', 'sansm', k2)
    text(c, '不掌兵的是哥哥；守江陵、管军资的是弟弟麋芳。', x + 26, y + h + 92, 26, GOLD, 'sansm', k2)

def sec3(c, t, cam):
    territories(c, cam, t)
    # d1 湘水为界
    v1 = fade(t, T.chap[3][0] + 0.8, S('d2') + 1.2, 0.8, 0.8)
    if v1 > 0.01:
        xp = PL(cam, D.seg(D.XIANG, 111.0, 113.1))
        k = ease(ramp(t, S('d1') + 3.2, S('d1') + 6.0))
        line(c, trim(xp, 0, 1), '#FFFFFF', 12, 0.25 * v1 * k, blur=8); line(c, trim(xp[::-1], 0, k), '#F4F0E6', 5, v1, dash=(14, 8))
        cities(c, cam, t, ['江陵', '公安', '长沙', '益阳', '陆口', '巴丘', '零陵', '武陵', '桂阳', '夏口'], v1, major=('江陵', '陆口'), left=('益阳', '公安', '武陵', '零陵'))
        kk = ss(ramp(t, S('d1') + 5.0, S('d1') + 6.2)) * v1
        x, y = cam.p(112.95, 28.0); text(c, '湘 水', x + 16, y - 70, 30, '#DCEFF7', 'serifm', v1, stroke=5, spacing=8)
        x, y = cam.p(110.9, 27.9); text(c, '以西属刘', x, y, 44, LIU_L, 'serifx', kk, 'c', stroke=7, shadow=8); text(c, '南郡 · 零陵 · 武陵', x, y + 42, 26, '#F1D6CF', 'sansm', kk, 'c', stroke=5)
        x, y = cam.p(114.3, 27.9); text(c, '以东属孙', x, y, 44, SUN_L, 'serifx', kk, 'c', stroke=7, shadow=8); text(c, '长沙 · 江夏 · 桂阳', x, y + 42, 26, '#CFEDEE', 'sansm', kk, 'c', stroke=5)
        x, y = P(cam, '益阳'); tag(c, x - 330, y + 34, '建安二十年　益阳对峙，未战而和', GOLD, v1 * ss(ramp(t, S('d1') + 1.6, S('d1') + 2.6)), 24)
    # d2 求婚被辱
    v2 = fade(t, S('d2') + 0.6, S('d3') + 1.0, 0.8, 0.8)
    if v2 > 0.01:
        cities(c, cam, t, ['江陵', '公安', '陆口', '巴丘', '夏口', '樊城', '襄阳', '长沙'], v2, major=('江陵',), left=('襄阳', '公安'))
        jx, jy = P(cam, '江陵'); rp = PL(cam, D.seg(D.YANGTZE, 112.25, 115.2)[::-1])
        k = ease(ramp(t, S('d2') + 1.0, S('d2') + 3.6))
        arrow(c, rp, SUN_L, k, 5, v2, dash=(12, 9), glow=False)
        x, y, _ = along(rp, 0.3); tag(c, x - 40, y - 64, '孙权遣使：为子求婚', SUN_L, v2 * ss(ramp(k, 0.2, 0.5)), 26)
        kx = ss(ramp(t, S('d2') + 3.8, S('d2') + 4.6)) * v2
        line(c, [(jx + 20, jy - 30), (jx + 64, jy + 14)], '#FF6A55', 8, kx); line(c, [(jx + 64, jy - 30), (jx + 20, jy + 14)], '#FF6A55', 8, kx)
        text(c, '骂辱其使，不许婚', jx - 20, jy - 54, 38, '#FFD9C9', 'serifx', kx, 'c', stroke=7, shadow=8)
    # d3 上流；d4 吕蒙称病，陆逊代
    v3 = fade(t, S('d3') + 1.2, S('d5') + 1.0, 1.0, 0.8)
    if v3 > 0.01:
        cities(c, cam, t, ['江陵', '陆口', '夏口', '寻阳', '建业', '樊城', '巴丘'], v3, major=('江陵', '建业', '陆口'), subs={'建业': '孙权所在'}, left=('樊城',), up=('巴丘',))
        yp = PL(cam, D.seg(D.YANGTZE, 112.19, 118.9))
        kfl = ss(ramp(t, S('d3') + 2.4, S('d3') + 3.6)) * (1 - ss(ramp(t, S('d4') - 0.4, S('d4') + 0.6))) * v3
        line(c, yp, '#FFFFFF', 13, 0.20 * kfl, blur=9)
        for i in range(7):
            u = ((t * 0.10) + i / 7) % 1.0; x, y, ang = along(yp, u)
            ax_, ay_ = x + 26 * math.cos(ang), y + 26 * math.sin(ang)
            arrow(c, [(x, y), (ax_, ay_)], '#FFE9B8', 1.0, 4.5, kfl * math.sin(u * math.pi) ** 0.6, head=16, glow=False)
        jx, jy = P(cam, '江陵'); bx, by = P(cam, '建业')
        text(c, '上流', jx + 4, jy - 60, 44, LIU_L, 'serifx', kfl, 'c', stroke=7, shadow=8)
        text(c, '下游', bx - 20, by + 96, 44, SUN_L, 'serifx', kfl, 'c', stroke=7, shadow=8)
        x, y, _ = along(yp, 0.45); text(c, '顺流而下', x, y - 44, 26, '#FFE9B8', 'sansm', kfl, 'c', stroke=5)
        # 吕蒙 / 陆逊
        lx, ly = P(cam, '陆口'); hp = PL(cam, D.R_LVMENG_HOME)
        kgo = ease(ramp(t, S('d4') + 0.6, S('d4') + 3.6))
        kv = ss(ramp(t, S('d3') + 6.0, S('d3') + 7.0)) * v3
        x, y, _ = along(hp, kgo)
        if kgo > 0.01: line(c, trim(hp, 0, kgo), SUN_L, 3.5, 0.55 * v3, dash=(10, 8))
        unit(c, x, y - 44, 'sun', '吕蒙' + ('（称病）' if kgo > 0.05 else ''), kv, 0.95, 'fleet', label_side='t')
        klu = ss(ramp(t, S('d4') + 3.4, S('d4') + 4.4)) * v3
        unit(c, lx + 6, ly + 56, 'sun', '陆逊', klu, 0.78, label_side='r', sub='“未有远名，非羽所忌”')
        # 书信
        kl = ramp(t, S('d4') + 5.0, S('d4') + 7.0); fx, fy = P(cam, '樊城')
        if 0 < kl < 1:
            x = lerp(lx, fx, ease(kl)); y = lerp(ly, fy, ease(kl)) - 60 * math.sin(kl * math.pi)
            rrect(c, x - 20, y - 14, 40, 28, 3, INK, 0.9 * v3); rrect(c, x - 17, y - 11, 34, 22, 2, '#F3EEE4', v3)
            line(c, [(x - 17, y - 11), (x, y + 2), (x + 17, y - 11)], '#9A8F7A', 2, v3)
        unit(c, fx - 10, fy + 60, 'liu', '关羽', v3, 0.9, label_side='r')
    # d5 撤备兵；d6 湘关米
    v5 = fade(t, S('d5') + 0.8, T.chap[4][0] + 0.5, 0.8, 0.6)
    if v5 > 0.01:
        cities(c, cam, t, ['江陵', '公安', '樊城', '襄阳', '陆口', '巴丘', '夷陵', '长沙', '益阳'], v5, major=('江陵', '樊城'), left=('襄阳', '公安', '益阳'))
        route = PL(cam, D.R_GUAN_N); jx, jy = P(cam, '江陵'); gx, gy = P(cam, '公安'); fx, fy = P(cam, '樊城')
        line(c, route, INK, 7, 0.4 * v5); line(c, route, LIU_L, 3, 0.6 * v5, dash=(10, 10))
        n_left = 0
        for i in range(6):
            t0 = S('d5') + 1.4 + i * 0.62; u = ease(ramp(t, t0, t0 + 2.4))
            if i >= 4: u = 0
            if u < 1:
                if u <= 0:
                    bx_, by_ = (jx - 150 + (i % 3) * 46, jy + 60 + (i // 3) * 38) if i < 3 else (jx - 150 + (i % 3) * 46, jy + 98)
                    n_left += 1
                else:
                    sx_, sy_ = (jx - 150 + (i % 3) * 46, jy + 60 + (i // 3) * 38)
                    px_, py_, _ = along(route, u); bx_ = lerp(sx_, px_, ss(ramp(u, 0, 0.15))); by_ = lerp(sy_, py_, ss(ramp(u, 0, 0.15)))
                unit(c, bx_, by_, 'liu', None, v5, 0.5)
        tag(c, jx - 420, jy + 132, '留守公安、南郡的备兵：稍撤以赴樊', LIU_L, v5 * ss(ramp(t, S('d5') + 2.0, S('d5') + 3.0)) * (1 - ss(ramp(t, S('d6') + 3.0, S('d6') + 3.8))), 24)
        unit(c, fx - 10, fy + 60, 'liu', '关羽', v5, 1.0, label_side='r', sub='降卒数万 · 粮乏' if t > S('d6') + 0.8 else None)
        # 湘关米
        k6 = ss(ramp(t, S('d6') + 3.2, S('d6') + 4.2)) * v5
        x, y = cam.p(112.95, 28.75)
        rp = [(x, y), (x - 60, (y + jy) / 2 + 40), (jx + 10, jy + 40)]
        arrow(c, rp, '#F4D9A0', ease(ramp(t, S('d6') + 3.4, S('d6') + 5.4)), 6, k6, dash=(12, 8), glow=False)
        circle(c, x, y, 9, INK, k6); circle(c, x, y, 6.5, '#F4D9A0', k6)
        tag(c, x + 18, y - 20, '擅取湘关米', '#F4D9A0', k6, 28, fname='serif')
        text(c, '（湘关确址有争议，示意）', x + 22, y + 46, 20, '#C9C2B4', 'sansm', k6, stroke=4)

def sec4(c, t, cam):
    territories(c, cam, t)
    # e1-e2 白衣渡江
    v1 = fade(t, T.chap[4][0] + 0.8, S('e3') + 1.2, 0.8, 0.9)
    if v1 > 0.01:
        fl = PL(cam, D.R_FLEET); L = D.R_FLEET; tot = plen(fl)
        idx = [min(range(len(L)), key=lambda i: (L[i][0] - b[0]) ** 2 + (L[i][1] - b[1]) ** 2) for b in D.BEACONS]
        us = [plen(fl[:i + 1]) / tot for i in idx]
        # 船队进度：e1 自寻阳溯江至辖境边；e2 逐一经过屯候
        u = 0.02 + (us[0] - 0.07) * ease(ramp(t, S('e1') + 1.0, E('e1') + 0.2))
        if t > E('e1') + 0.2: u = (us[0] - 0.05) + (0.985 - us[0] + 0.05) * ramp(t, E('e1') + 0.2, S('e3') + 0.6)
        cities(c, cam, t, ['江陵', '公安', '陆口', '巴丘', '夏口', '寻阳'], v1, major=('江陵', '寻阳'), left=('公安',), up=('巴丘',), subs={'寻阳': '吕蒙伏兵登船'})
        line(c, trim(fl, 0, u), SUN_L, 4, 0.55 * v1, dash=(8, 8))
        bs = 1.0 + 0.9 * ss(ramp(cam.S, 80000, 150000))
        for i, b in enumerate(D.BEACONS):
            x, y = cam.p(*b); lit = 1 - ss(ramp(u, us[i] - 0.010, us[i] + 0.004))
            beacon(c, x, y - 6, lit, t, v1, bs)
            if 0 < lit < 1: circle(c, x, y - 12, 24 + 70 * (1 - lit), SUN_L, v1 * lit * 0.8, stroke=3)
        n_out = sum(1 for i in range(8) if u > us[i])
        tag(c, 64, 372, '屯候：关羽设于江边的哨所（位置示意）', AMBER, v1 * fade(t, S('e1') + 5.5, S('e2') + 0.2, 0.8, 0.5), 25)
        tag(c, 64, 372, '已被收缚　%d / 8' % n_out, SUN_L, v1 * ss(ramp(t, S('e2') + 0.2, S('e2') + 1.0)), 28)
        x, y, ang = along(fl, u)
        for i in (2, 1, 0):
            xx, yy, _ = along(fl, max(0, u - i * 0.02)); unit(c, xx, yy - 8, 'sun', None, v1 * (1.0 if i == 0 else 0.9), 0.8 if i else 0.92, 'fleet')
        tag(c, x - 90, y + 40, '吕蒙 · 白衣摇橹', SUN_L, v1, 25)
        text(c, '↑ 关羽主力在樊城', 930, 372, 26, LIU_L, 'sans', v1 * 0.95, 'r', stroke=5)
        river_labels(c, cam, v1 * 0.9, ('长江',))
    # e3 公安
    v3 = fade(t, S('e3') + 0.6, S('e4') + 1.0, 0.8, 0.8)
    if v3 > 0.01:
        cities(c, cam, t, ['江陵', '公安'], v3, major=('江陵', '公安'), size=38)
        gx, gy = P(cam, '公安'); jx, jy = P(cam, '江陵')
        for i in range(3): unit(c, gx + 120 + i * 60, gy - 70 - i * 26, 'sun', '吕蒙' if i == 0 else None, v3, 0.75, 'fleet', label_side='t')
        kl = ramp(t, S('e3') + 1.6, S('e3') + 3.2)
        if 0 < kl < 1:
            x = lerp(gx + 120, gx + 10, ease(kl)); y = lerp(gy - 70, gy - 8, ease(kl)) - 40 * math.sin(kl * math.pi)
            rrect(c, x - 22, y - 15, 44, 30, 3, INK, 0.9 * v3); rrect(c, x - 19, y - 12, 38, 24, 2, '#F3EEE4', v3); line(c, [(x - 19, y - 12), (x, y + 2), (x + 19, y - 12)], '#9A8F7A', 2, v3)
        tag(c, gx + 50, gy + 40, '虞翻致书', SUN_L, v3 * ss(ramp(t, S('e3') + 1.4, S('e3') + 2.0)), 26)
        k0 = fade(t, S('e3') + 0.8, S('e4') + 0.6, 0.6, 0.5)
        panel(c, 64, 366, 872, 92, k0, r=6, fa=0.78)
        text(c, '此前，《关羽传》：“权阴诱芳、仁，芳、仁使人迎权。”', 84, 404, 26, '#F6EBCB', 'serif', k0)
        text(c, '两人与东吴早有往来；各传记载详略不同', 84, 440, 22, '#B7B0A2', 'sansm', k0)
        kk = ss(ramp(t, E('e3') - 1.2, E('e3') - 0.4)) * v3
        tag(c, gx - 250, gy + 40, '士仁：流涕而降', '#FFB199', kk, 28, fname='serif')
        pulse(c, gx, gy, t, SUN_L, 14, 70, 1.5, kk)
    # e4-e6 江陵城
    v4 = fade(t, S('e4') + 0.9, S('e7') + 0.9, 0.9, 0.9)
    if v4 > 0.01:
        dim(c, 0.46 * v4)
        g = ease(ramp(t, S('e4') + GATE_OFF, S('e4') + GATE_OFF + 2.2))
        flg = ss(ramp(t, S('e4') + GATE_OFF + 1.6, S('e4') + GATE_OFF + 3.4))
        amb = ramp(t, S('e5') + 5.6, S('e5') + 8.0) * (1 - ss(ramp(t, S('e6') - 0.3, S('e6') + 0.6)))
        warm = ss(ramp(t, S('e6') + 1.6, S('e6') + 4.0))
        plan_river(c, v4)
        zz = 1.0 + 0.05 * ramp(t, S('e4'), S('e7') + 0.9)
        c.save(); c.translate(540, PCY); c.scale(zz, zz); c.translate(-540, -PCY)
        city_plan(c, t, v4, g, flg, amb=amb, warm=warm)
        c.restore()
        gy = PCY + PR
        k1 = ss(ramp(t, S('e4') + 1.4, S('e4') + 2.4)) * v4
        inn = ease(ramp(t, S('e6') + 0.2, S('e6') + 2.0))
        for i in range(3): unit(c, 400 + i * 110, PKY + 8, 'sun', None, k1 * (1 - 0.5 * inn), 0.95, 'fleet')
        unit(c, lerp(540 + 110, 540, inn), lerp(gy + 50, gy - 96, inn), 'sun', '吕蒙', k1, 0.9, label_side='b')
        ks = ss(ramp(t, S('e4') + 2.6, S('e4') + 3.6)) * v4 * (1 - ss(ramp(t, S('e5') - 0.3, S('e5') + 0.5)))
        person(c, 540 - 150, gy + 60, '士仁', 'liu', ks)
        text(c, '已降', 540 - 150, gy + 104, 22, '#FFB199', 'sansm', ks, 'c', stroke=4)
        arrow(c, [(540 - 96, gy + 56), (540 - 50, gy + 44), (540 - 22, gy + 24)], '#FFB199', ease(ramp(t, S('e4') + 3.0, S('e4') + 4.0)), 4, ks, head=14, glow=False)
        text(c, '“蒙以仁示之”', 64, gy + 70, 32, '#FFD9C9', 'serif', ks, stroke=5)
        km = ss(ramp(t, S('e4') + 1.0, S('e4') + 1.8)) * v4
        tag(c, 540 - 150, gy - 96, '麋芳｜开城出降' if g > 0.6 else '麋芳｜城守', mix(LIU_L, '#FFB199', g), km * (1 - ss(ramp(t, S('e5') + 5.0, S('e5') + 5.6))), 28)
        k5 = fade(t, S('e5') + 0.6, S('e6') - 0.1, 0.6, 0.5) * v4
        person(c, 540 + 300, gy + 50, '虞翻', 'sun', k5)
        text(c, '“城中之人岂可尽信”', 930, gy + 110, 26, '#CFEDEE', 'serif', k5, 'r', stroke=5)
        k6 = fade(t, S('e6') + 2.2, S('e7') + 0.4, 0.6, 0.5) * v4
        tag(c, 540 - 200, PCY - PR + 60, '关羽将士家属：皆抚慰', '#F4D9A0', k6, 28)
        k62 = fade(t, S('e6') + 5.0, S('e7') + 0.4, 0.6, 0.5) * v4
        tag(c, 540 - 200, PCY + PR - 150, '取民家一笠 → 垂涕斩之', '#FF8E7A', k62, 28)
    # e7-e8 军心瓦解
    v7 = fade(t, S('e7') + 1.2, T.chap[5][0] + 0.5, 1.0, 0.6)
    if v7 > 0.01:
        cities(c, cam, t, ['江陵', '公安', '樊城', '襄阳', '麦城', '临沮', '夷陵', '陆口'], v7, major=('江陵',), left=('襄阳', '公安', '临沮'), subs={'临沮': '章乡'}, up=('临沮',))
        ret = PL(cam, D.R_GUAN_RET); end = PL(cam, D.R_GUAN_END)
        u = ease(ramp(t, S('e7') + 1.6, S('e8') + 3.0)); u2 = ease(ramp(t, S('e8') + 3.4, E('e8') + 0.6))
        x, y, _ = along(ret, u)
        if u2 > 0: x, y, _ = along(end, u2 * 0.78)
        line(c, trim(ret, 0, u), LIU_L, 3.5, 0.6 * v7, dash=(10, 8))
        if u2 > 0: line(c, trim(end, 0, u2 * 0.78), LIU_L, 3.5, 0.6 * v7, dash=(10, 8))
        strength = 1 - 0.88 * ss(ramp(t, S('e7') + 5.0, S('e8') + 5.5))
        # 散去的士卒
        rng = np.random.default_rng(21)
        for i in range(46):
            t0 = S('e7') + 4.6 + rng.uniform(0, 1) * (E('e8') - S('e7') - 6.0); k = ramp(t, t0, t0 + 3.2)
            ang = rng.uniform(0, 2 * math.pi); dist = rng.uniform(60, 190)
            if 0 < k < 1:
                bx_, by_, _ = along(ret, clamp(ease(ramp(t0, S('e7') + 1.6, S('e8') + 3.0))))
                jx, jy = P(cam, '江陵')
                tx_ = lerp(bx_ + dist * math.cos(ang), jx, 0.35); ty_ = lerp(by_ + dist * math.sin(ang), jy, 0.35)
                circle(c, lerp(bx_, tx_, eout(k)), lerp(by_, ty_, eout(k)), 4.2, LIU_L, v7 * (1 - k) * 0.95)
        # 使者往来
        jx, jy = P(cam, '江陵')
        for i in range(2):
            k = ((t - S('e7')) * 0.22 + i * 0.5) % 1.0
            if t < S('e8') + 1.5:
                px_ = lerp(x, jx, k if i == 0 else 1 - k); py_ = lerp(y, jy, k if i == 0 else 1 - k)
                circle(c, px_, py_, 6, INK, 0.8 * v7); circle(c, px_, py_, 4.2, '#F4D9A0', v7)
        tag(c, jx + 34, jy - 60, '吕蒙据城 · 家家致问', SUN_L, v7 * ss(ramp(t, S('e7') + 2.0, S('e7') + 3.0)), 24)
        unit(c, x + 8, y + 4, 'liu', '关羽', v7, 0.55 + 0.45 * strength, label_side='r', strength=max(0.14, strength), sub='吏士无斗心' if strength < 0.75 else None)
        if u2 > 0.2:
            lx, ly = P(cam, '临沮')
            kk = ss(ramp(u2, 0.3, 0.9)) * v7
            unit(c, lx - 86, ly - 70, 'sun', '朱然 · 潘璋', kk, 0.75, label_side='t')
            tag(c, lx - 300, ly - 30, '断其径路', SUN_L, kk, 26)

def sec5(c, t, cam):
    k_ter = 1.0
    territories(c, cam, t, k_ter)
    jx, jy = P(cam, '江陵'); cx_, cy_ = P(cam, '成都')
    # f1 时间条 + f2 无援
    v1 = fade(t, T.chap[5][0] + 0.8, S('f3') + 1.0, 0.8, 0.8)
    if v1 > 0.01:
        faction_names(c, cam, t, v1 * 0.8)
        cities(c, cam, t, ['成都', '汉中', '江陵', '樊城', '上庸', '白帝', '江州'], v1, major=('成都', '江陵'), up=('樊城',))
        k = ease(ramp(t, S('f2') + 6.0, S('f2') + 9.0)); kv = ss(ramp(t, S('f2') + 5.6, S('f2') + 6.4)) * v1
        pts = [(cx_ + 20, cy_ - 4), ((cx_ + jx) / 2, cy_ - 120), (jx - 26, jy - 14)]
        arrow(c, smooth(pts, 3), '#E9E2D2', k, 5, 0.75 * kv, dash=(14, 12), glow=False)
        mx_, my_ = (cx_ + jx) / 2, cy_ - 108
        text(c, '援兵？', mx_, my_ - 26, 54, PAPER, 'serifx', kv * ss(ramp(k, 0.4, 0.8)), 'c', stroke=8, shadow=10)
        text(c, '史书无载', mx_, my_ + 62, 30, '#F4D9A0', 'sans', kv * ss(ramp(k, 0.7, 1.0)), 'c', stroke=6)
        tag(c, cx_ - 60, cy_ + 36, '刘备“还治成都”', LIU_L, v1 * ss(ramp(t, S('f2') + 0.6, S('f2') + 1.4)), 24)
        month_bar(c, t, v1)
    # f3 上庸
    v3 = fade(t, S('f3') + 0.6, S('f4') + 1.0, 0.8, 0.8)
    if v3 > 0.01:
        cities(c, cam, t, ['上庸', '房陵', '樊城', '襄阳', '江陵', '汉中', '夷陵', '白帝'], v3, major=('上庸', '樊城'), left=('襄阳', '房陵'))
        sx, sy_ = P(cam, '上庸'); fx, fy = P(cam, '樊城')
        unit(c, sx + 6, sy_ - 56, 'liu', '刘封 · 孟达', v3, 0.95, label_side='t')
        unit(c, fx + 60, fy + 50, 'liu', '关羽', v3, 0.95, label_side='r')
        for i in range(3):
            u = ((t - S('f3')) * 0.42 + i / 3) % 1.0
            if S('f3') + 2.0 < t < S('f3') + 7.0:
                x = lerp(fx, sx, u); y = lerp(fy, sy_, u) - 40 * math.sin(u * math.pi)
                circle(c, x, y, 7, LIU_L, v3 * math.sin(u * math.pi)); circle(c, x, y, 14, LIU_L, 0.35 * v3 * math.sin(u * math.pi), stroke=2)
        text(c, '“连呼封、达”', (fx + sx) / 2, (fy + sy_) / 2 - 70, 34, '#FFD9C9', 'serif', v3 * fade(t, S('f3') + 2.0, S('f3') + 7.0, 0.5, 0.5), 'c', stroke=6, shadow=6)
        kx = ss(ramp(t, S('f3') + 6.4, S('f3') + 7.2)) * v3
        mx_, my_ = (fx + sx) / 2, (fy + sy_) / 2 - 6
        line(c, [(sx + 50, sy_ + 6), (fx - 40, fy - 4)], '#8A8A8A', 4, 0.8 * kx, dash=(12, 10))
        line(c, [(mx_ - 22, my_ - 22), (mx_ + 22, my_ + 22)], '#FF6A55', 8, kx); line(c, [(mx_ + 22, my_ - 22), (mx_ - 22, my_ + 22)], '#FF6A55', 8, kx)
        tag(c, sx - 80, sy_ + 64, '“山郡初附，未可动摇”', '#FFB199', kx, 26, fname='serif')
    # f4-f6 人被抽走
    v5 = fade(t, S('f4') + 1.2, S('f7') + 0.6, 1.0, 0.7)
    if v5 > 0.01:
        cities(c, cam, t, ['成都', '汉中', '江陵', '樊城', '白帝', '江州'], v5, major=('成都', '江陵'), up=('樊城',))
        route = PL(cam, D.R_WEST214)
        go = ramp(t, S('f6') + 0.6, S('f6') + 4.6)
        names = [('诸葛亮', '调赋税 · 充军实', 0.0), ('张飞', None, 0.12), ('赵云', None, 0.24)]
        ky = ss(ramp(t, S('f5') + 0.3, S('f5') + 1.0)) * v5
        year = '建安十六年（211）' if t < S('f6') + 0.4 else '建安十九年（214）'
        text(c, year, 64, 300, 44, GOLD, 'serifx', ky, 'l', stroke=7, shadow=10)
        text(c, '四人同守荆州' if t < S('f6') + 0.4 else '诸葛亮、张飞、赵云入蜀', 66, 346, 28, '#E4DDCF', 'sans', ky, 'l', stroke=5)
        if go > 0: line(c, trim(route, 0, ease(go)), LIU_L, 4, 0.55 * v5, dash=(10, 8))
        for i, (n, sub, off) in enumerate(names):
            kin = ss(ramp(t, S('f5') + 0.8 + i * 0.5, S('f5') + 1.4 + i * 0.5)) * v5
            u = ease(ramp(go, off, off + 0.76))
            hx, hy = jx - 60 - i * 6, jy + 70 + i * 62
            if u <= 0: x, y = hx, hy
            else:
                rx, ry, _ = along(route, u); x = lerp(hx, rx, ss(ramp(u, 0, 0.12))); y = lerp(hy, ry, ss(ramp(u, 0, 0.12)))
                if u > 0.9: x = lerp(x, cx_ + 30, ss(ramp(u, 0.9, 1))); y = lerp(y, cy_ + 60 + i * 50, ss(ramp(u, 0.9, 1)))
            person(c, x, y, n, 'liu', kin, sub=sub if u <= 0 and t > S('f5') + 4.0 else None)
        kin = ss(ramp(t, S('f5') + 2.4, S('f5') + 3.0)) * v5
        alone = ss(ramp(go, 0.8, 1.0))
        person(c, jx - 10, jy - 62, '关羽', 'liu', kin, hl=alone)
        text(c, '独当一面', jx - 10, jy - 104, 30, '#F4D9A0', 'serifx', alone * v5, 'c', stroke=6, shadow=6)
        if alone > 0.01: pulse(c, jx - 10, jy - 62, t, LIU_L, 40, 110, 2.0, 0.6 * alone * v5)
        river_labels(c, cam, v5 * 0.8, ('长江',))
    # f9 距离 / 飞地
    v9 = fade(t, S('f9') - 0.3, S('f10') + 0.8, 0.8, 0.8)
    if v9 > 0.01:
        cities(c, cam, t, ['成都', '汉中', '江陵', '樊城', '白帝', '上庸'], v9, major=('成都', '江陵'), up=('樊城',))
        k = ease(ramp(t, S('f9') + 0.3, S('f9') + 2.6))
        line(c, [(cx_, cy_), (lerp(cx_, jx, k), lerp(cy_, jy, k))], '#000000', 9, 0.5 * v9); line(c, [(cx_, cy_), (lerp(cx_, jx, k), lerp(cy_, jy, k))], '#F4F0E6', 4.5, v9, dash=(16, 10))
        kk = ss(ramp(k, 0.6, 1.0)) * v9
        text(c, '直线约 780 公里', lerp(cx_, jx, 0.36), lerp(cy_, jy, 0.36) - 30, 44, PAPER, 'serifx', kk, 'c', stroke=8, shadow=10)
        gx_, gy_ = cam.p(110.2, 31.0); k3 = ss(ramp(t, S('f9') + 3.4, S('f9') + 4.2)) * v9
        for i in range(3): line(c, [(gx_ - 46 + i * 36, gy_ - 46), (gx_ - 60 + i * 36, gy_ + 46)], '#F4D9A0', 4, 0.9 * k3)
        text(c, '三峡', gx_ - 10, gy_ + 96, 36, '#F4D9A0', 'serifx', k3, 'c', stroke=7)
        k4 = ss(ramp(t, S('f9') + 5.0, S('f9') + 6.0)) * v9
        pth = mkpath(PL(cam, D.T_JING), True)
        pp = skia.Paint(AntiAlias=True, Color=rgba(LIU_L, 0.95 * k4), Style=skia.Paint.kStroke_Style, StrokeWidth=4); pp.setPathEffect(skia.DashPathEffect.Make([14, 10], -(t * 18) % 24))
        c.drawPath(pth, pp)
        x, y = cam.p(111.6, 28.6); text(c, '飞地', x, y, 78, LIU_L, 'serifx', k4, 'c', stroke=9, shadow=12)
    # f10-f12 引文为主：地图压暗
    v10 = fade(t, S('f10') + 0.4, T.chap[6][0] + 0.4, 0.8, 0.5)
    if v10 > 0.01:
        cities(c, cam, t, ['成都', '汉中', '江陵', '樊城', '上庸'], v10 * 0.9, major=('成都', '江陵', '汉中'), up=('樊城',))
        if t < S('f11'):
            hx, hy = P(cam, '汉中'); sx, sy_ = P(cam, '上庸')
            pulse(c, hx, hy, t, GOLD, 14, 64, 1.8, 0.8 * v10)
            tag(c, hx - 110, hy - 96, '“后至汉中”', GOLD, v10 * ss(ramp(t, S('f10') + 1.6, S('f10') + 2.4)), 26, fname='serif')
            tag(c, jx - 190, jy + 30, '“关侯身死”', '#FFB199', v10 * ss(ramp(t, S('f10') + 3.0, S('f10') + 3.8)), 26, fname='serif')
            tag(c, sx - 60, sy_ + 30, '“上庸覆败”', '#FFB199', v10 * ss(ramp(t, S('f10') + 4.6, S('f10') + 5.4)), 26, fname='serif')

def person(c, x, y, name, fac, a=1.0, sub=None, hl=0.0, size=30):
    """人物牌：圆点 + 姓名。"""
    if a <= 0.003: return
    col, dk, lt = FAC[fac]
    w = tw(name, 'serifx', size) + 30; h = size + 18
    rrect(c, x - w / 2, y - h / 2 + 4, w, h, h / 2, '#000000', 0.45 * a, blur=7)
    rrect(c, x - w / 2, y - h / 2, w, h, h / 2, mix(dk, col, 0.35 + 0.4 * hl), 0.96 * a, stroke=lt, sw=2.2)
    text(c, name, x, y + size * 0.36, size, PAPER, 'serifx', a, 'c')
    if sub: text(c, sub, x + w / 2 + 10, y + 9, 23, '#F4D9A0', 'sansm', a, stroke=5)

def month_bar(c, t, a):
    """f1：建安二十四年八月—十二月的时间条。"""
    if a <= 0.003: return
    x, y, w, h = 64, 326, 872, 232
    panel(c, x, y, w, h, a, r=8, fa=0.84)
    text(c, '建安二十四年（219）', x + 24, y + 42, 28, GOLD, 'serif', a)
    months = ['八月', '九月', '十月', '闰十月', '十一月', '十二月']
    x0, x1, yy = x + 70, x + w - 70, y + 120
    k = ease(ramp(t, S('f1') + 0.4, S('f1') + 4.0))
    line(c, [(x0, yy), (x1, yy)], '#5A5A58', 6, a); line(c, [(x0, yy), (lerp(x0, x1, k), yy)], LIU_L, 6, a)
    ev = {0: ('水淹七军', LIU_L), 3: ('吕蒙袭江陵', SUN_L), 4: ('陆逊取宜都', SUN_L), 5: ('关羽被擒', '#FFB199')}
    for i, m in enumerate(months):
        xx = lerp(x0, x1, i / 5); on = ss(ramp(k, i / 5 - 0.05, i / 5 + 0.03))
        circle(c, xx, yy, 11, INK, a); circle(c, xx, yy, 8, mix('#6A6A68', ev[i][1] if i in ev else '#D9D2C2', on), a)
        text(c, m, xx, yy - 26, 24, PAPER, 'sans', a * (0.5 + 0.5 * on), 'c')
        if i in ev: text(c, ev[i][0], xx, yy + 46, 25, ev[i][1], 'serif', a * on, 'c')
    kk = ss(ramp(t, S('f1') + 3.8, S('f1') + 4.6)) * a
    text(c, '近五个月 · 《先主传》仅一句', x + w - 24, y + 42, 25, '#F4D9A0', 'sansm', kk, 'r')
    text(c, '月份据《武帝纪》《吴主传》《陆逊传》', x + w - 24, y + h - 16, 19, '#8F897C', 'sansm', a, 'r')

# ---- 权力结构图
def chip(c, x, y, w, name, sub, col, a, hl=False, h=50):
    if a <= 0.003: return
    rrect(c, x, y, w, h, 6, '#15181B', 0.92 * a, stroke=col if hl else '#3A3D40', sw=2.4 if hl else 1.2)
    rrect(c, x, y, 5, h, 2, col, a)
    text(c, name, x + 16, y + h / 2 + 10, 28, PAPER, 'serif', a)
    if sub: text(c, sub, x + w - 10, y + h / 2 + 8, 20, '#B7B0A2', 'sansm', a, 'r')
def structure(c, t):
    a = fade(t, S('f7') - 0.2, S('f9') - 0.1, 0.7, 0.6)
    if a <= 0.003: return
    dim(c, 0.74 * a)
    X0, X1 = 60, 940
    text(c, '建安二十四年 · 刘备集团的权力结构', X0, 276, 34, GOLD, 'serifx', a)
    text(c, '（示意）', X0 + tw('建安二十四年 · 刘备集团的权力结构', 'serifx', 34) + 6, 274, 22, '#B7B0A2', 'sansm', a)
    # 决策圈
    kr = ss(ramp(t, S('f7') + 0.8, S('f7') + 1.8)) * a
    p = skia.Paint(AntiAlias=True, Color=rgba(GOLD, 0.9 * kr), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
    p.setPathEffect(skia.DashPathEffect.Make([12, 8], -(t * 14) % 20))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(X0 + 150, 300, 580, 252), 26, 26), p)
    rrect(c, X0 + 150, 300, 580, 252, 26, GOLD, 0.06 * kr)
    text(c, '决策圈', X0 + 742, 336, 28, GOLD, 'serifx', kr)
    # 刘备
    rrect(c, 330, 318, 340, 84, 8, LIU_D, 0.95 * a, stroke=LIU_L, sw=2.5)
    text(c, '刘备', 356, 376, 46, PAPER, 'serifx', a); text(c, '汉中王 · 还治成都', 656, 372, 23, '#F1D6CF', 'sansm', a, 'r')
    # 法正
    kf = ss(ramp(t, S('f7') + 1.2, S('f7') + 2.0)) * a
    line(c, [(500, 402), (500, 426)], GOLD, 3, kf)
    rrect(c, 250, 426, 500, 108, 8, '#1C1A12', 0.96 * kf, stroke=GOLD, sw=2.5)
    text(c, '法正', 274, 478, 42, PAPER, 'serifx', kf); text(c, '尚书令 · 护军将军', 736, 466, 23, '#E4DDCF', 'sansm', kf, 'r')
    text(c, '汉中之战首谋 ·“外统都畿，内为谋主”', 274, 518, 23, '#F4D9A0', 'serifm', kf)
    # 诸葛亮
    kz = ss(ramp(t, S('f7') + 7.2, S('f7') + 8.0)) * a
    line(c, [(500, 552), (500, 590)], '#8A8A8A', 2.5, kz, dash=(6, 6))
    rrect(c, 250, 590, 500, 108, 8, '#16191C', 0.96 * kz, stroke='#9FC3D8', sw=2.0)
    text(c, '诸葛亮', 274, 642, 42, PAPER, 'serifx', kz); text(c, '军师将军 · 署左将军府事', 736, 630, 23, '#E4DDCF', 'sansm', kz, 'r')
    text(c, '后方 ·“镇守成都，足食足兵”', 274, 682, 23, '#BFDCEB', 'serifm', kz)
    text(c, '《法正传》《诸葛亮传》', X1, 722, 19, '#8F897C', 'sansm', a, 'r')
    # 三栏
    kc = ss(ramp(t, S('f7') + 3.0, S('f7') + 4.2)) * a
    cols = [('元从 · 荆州旧部', LIU, [('张飞', '右将军 · 巴西'), ('赵云', '翊军将军'), ('麋竺', '安汉将军'), ('魏延', '镇汉中')]),
            ('东州 · 刘璋旧部', GOLD, [('法正', '扶风'), ('李严', '南阳 · 犍为太守'), ('孟达', '扶风 · 屯上庸'), ('许靖', '汝南 · 太傅')]),
            ('益州本土', '#B9D4A0', [('黄权', '巴西'), ('杨洪', '犍为 · 蜀郡太守'), ('张裔', '蜀郡')])]
    cw = 284; gap = 14
    for i, (ttl, col, ms) in enumerate(cols):
        x = X0 + i * (cw + gap); y = 748
        text(c, ttl, x + 4, y + 26, 26, col if col != LIU else LIU_L, 'serifx', kc)
        for j, (n, s) in enumerate(ms):
            chip(c, x, y + 42 + j * 56, cw, n, s, col, kc * ss(ramp(t, S('f7') + 3.2 + j * 0.2 + i * 0.3, S('f7') + 3.8 + j * 0.2 + i * 0.3)), hl=(n == '法正'), h=48)
    text(c, '分栏据田余庆“新人／旧人”说及后人的三分法，属今人归纳', X0 + 4, 1026, 19, '#8F897C', 'sansm', kc)
    # 汉中
    kh = ss(ramp(t, S('f8') + 0.3, S('f8') + 1.2)) * a
    rrect(c, X0, 1046, 880, 78, 8, '#231C10', 0.96 * kh, stroke=GOLD, sw=2)
    text(c, '汉中之战', X0 + 20, 1098, 34, GOLD, 'serifx', kh)
    text(c, '“男子当战，女子当运”', X0 + 196, 1097, 32, '#F6EBCB', 'serif', kh * ss(ramp(t, S('f8') + 3.2, S('f8') + 4.0)))
    text(c, '《杨洪传》', X1 - 16, 1096, 20, '#A8A294', 'sansm', kh, 'r')
    for i in range(3):
        xx = X0 + cw / 2 + i * (cw + gap)
        arrow(c, [(xx, 1012), (xx, 1044)], GOLD, ease(ramp(t, S('f8') + 0.8 + i * 0.15, S('f8') + 1.6 + i * 0.15)), 4, kh, head=13, glow=False, outline=False)
    # 荆州
    kj = ss(ramp(t, S('f7') + 5.0, S('f7') + 6.0)) * a
    rrect(c, X0, 1150, 880, 172, 8, '#1F1211', 0.96 * kj, stroke=LIU_L, sw=2.2)
    text(c, '荆州', X0 + 20, 1200, 34, LIU_L, 'serifx', kj); text(c, '距成都约 780 公里', X0 + 110, 1198, 22, '#D9B6AE', 'sansm', kj)
    rrect(c, X0 + 20, 1220, 300, 84, 6, LIU_D, 0.95 * kj, stroke=LIU_L, sw=2)
    text(c, '关羽', X0 + 36, 1262, 36, PAPER, 'serifx', kj); text(c, '前将军 · 董督荆州事', X0 + 36, 1292, 20, '#F1D6CF', 'sansm', kj)
    text(c, '在樊城前线', X0 + 306, 1258, 20, '#F4D9A0', 'sansm', kj, 'r')
    for j, (n, s) in enumerate((('麋芳', '江陵'), ('士仁', '公安'), ('潘濬', '留州事'))):
        xx = X0 + 372 + j * 170
        chip(c, xx, 1238, 156, n, s, LIU, kj, h=48)
        line(c, [(xx - 44, 1262), (xx - 8, 1262)], '#FF6A55', 2.5, kj, dash=(5, 5)) if j == 0 else None
    text(c, '后方 —— 皆与关羽不和', X0 + 372, 1222, 21, '#FFB199', 'sansm', kj)
    # 荆州与决策圈之间的虚线
    kl = ss(ramp(t, S('f7') + 5.6, S('f7') + 6.6)) * a
    line(c, [(X0 + 22, 1150), (X0 + 22, 760)], '#6A6A68', 0, 0)
    line(c, [(946, 1160), (962, 1160), (962, 360), (742, 360)], '#FF6A55', 2.5, 0.0)

def sec6(c, t, cam):
    territories(c, cam, t)
    jx, jy = P(cam, '江陵')
    v1 = fade(t, T.chap[6][0] + 0.8, S('g2') + 1.0, 0.8, 0.8)
    if v1 > 0.01:
        cities(c, cam, t, ['江陵', '公安', '麦城', '临沮', '夷陵', '樊城', '襄阳'], v1, major=('江陵', '临沮'), left=('襄阳', '公安', '麦城'), subs={'临沮': '章乡'})
        lx, ly = P(cam, '临沮'); k = ss(ramp(t, S('g1') + 0.8, S('g1') + 1.6)) * v1
        line(c, [(lx - 30, ly - 80), (lx + 22, ly - 28)], '#FF6A55', 9, k); line(c, [(lx + 22, ly - 80), (lx - 30, ly - 28)], '#FF6A55', 9, k)
        tag(c, lx + 44, ly - 96, '十二月　关羽、关平被杀', '#FFB199', k, 28, fname='serif')
        k2 = ss(ramp(t, S('g1') + 3.4, S('g1') + 4.4)) * v1
        text(c, '荆州尽入孙权', jx + 150, jy - 150, 50, SUN_L, 'serifx', k2, 'c', stroke=8, shadow=10)
    v2 = fade(t, S('g2') + 0.8, S('g3') + 1.0, 0.9, 0.8)
    if v2 > 0.01:
        faction_names(c, cam, t, v2 * 0.7)
        cities(c, cam, t, ['成都', '汉中', '江陵', '上庸', '白帝', '樊城'], v2, major=('成都', '上庸'), up=('樊城',))
        cx_, cy_ = P(cam, '成都'); sx, sy_ = P(cam, '上庸')
        k = ss(ramp(t, S('g2') + 1.2, S('g2') + 2.0)) * v2
        pulse(c, sx, sy_, t, CAO_L, 14, 64, 1.6, 0.8 * ss(ramp(t, S('g2') + 3.0, S('g2') + 4.0)) * v2)
        rf = PL(cam, [(110.15, 32.20), (108.6, 32.0), (106.6, 31.4), (104.5, 30.85)])
        arrow(c, smooth(rf, 2), LIU_L, ease(ramp(t, S('g2') + 4.8, S('g2') + 6.6)), 5, v2, dash=(12, 9), glow=False)
    v3 = fade(t, S('g3') + 0.8, S('g4') + 1.6, 0.9, 1.0)
    if v3 > 0.01:
        cities(c, cam, t, ['成都', '江州', '白帝', '秭归', '夷陵', '猇亭', '江陵', '公安'], v3, major=('成都', '夷陵', '白帝'), left=('秭归',), up=('猇亭',), subs={'白帝': '永安'})
        route = PL(cam, D.R_LIU_EAST)
        k = ease(ramp(t, S('g3') + 1.0, S('g3') + 3.8)); back = ease(ramp(t, E('g3') - 1.2, E('g3') + 1.6))
        arrow(c, route, LIU, k, 8, v3 * (1 - 0.6 * back))
        hx, hy = P(cam, '猇亭'); kb = ss(ramp(t, E('g3') - 2.0, E('g3') - 1.0)) * v3
        fl_ = 0.8 + 0.2 * math.sin(t * 11)
        glow(c, hx - 30, hy - 6, 90 * fl_, '#FF7A2E', kb * 0.9); glow(c, hx - 80, hy - 20, 60 * fl_, '#FFC04A', kb * 0.7)
        text(c, '夷陵大败', hx - 60, hy + 92, 50, '#FFB199', 'serifx', kb, 'c', stroke=8, shadow=10)
        text(c, '章武二年（222）', hx - 60, hy + 130, 24, '#E4DDCF', 'sansm', kb, 'c', stroke=5)
        unit(c, hx + 74, hy + 16, 'sun', '陆逊', v3 * ss(ramp(t, S('g3') + 2.4, S('g3') + 3.2)), 0.9, label_side='r')
        bx, by = P(cam, '白帝'); x, y, _ = along(route, k)
        if back > 0: x = lerp(x, bx, back); y = lerp(y, by - 50, back)
        unit(c, x - 6, y - 46, 'liu', '刘备', v3, 1.0 - 0.45 * back, label_side='t', strength=1 - 0.7 * back)
    v5 = fade(t, S('g4') + 2.4, S('h1') - 0.6, 1.0, 0.8)
    if v5 > 0.01:
        faction_names(c, cam, t, v5 * 0.8)
        cities(c, cam, t, ['成都', '汉中', '白帝', '江陵', '上庸', '江州'], v5, major=('成都', '白帝'), subs={'白帝': '永安宫'})
        route = PL(cam, D.R_ZHUGE_223); k = ease(ramp(t, S('g5') + 0.4, S('g5') + 3.4))
        kv = ss(ramp(t, S('g5') + 0.2, S('g5') + 0.9)) * v5
        line(c, trim(route, 0, k), LIU_L, 4, 0.6 * kv, dash=(10, 8))
        x, y, _ = along(route, k); person(c, x, y - 34, '诸葛亮', 'liu', kv, hl=ss(ramp(k, 0.9, 1.0)))
        bx, by = P(cam, '白帝'); pulse(c, bx, by, t, GOLD, 14, 70, 1.8, 0.8 * ss(ramp(k, 0.85, 1.0)) * v5)
        tag(c, bx - 150, by + 70, '章武三年　白帝城托孤', GOLD, v5 * ss(ramp(k, 0.9, 1.0)), 26)
        k2 = ss(ramp(t, E('g5') - 4.0, E('g5') - 3.0)) * v5
        pth = mkpath(PL(cam, D.T_YI_CORE), True)
        pp = skia.Paint(AntiAlias=True, Color=rgba(LIU_L, 0.9 * k2), Style=skia.Paint.kStroke_Style, StrokeWidth=4); pp.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
        c.drawPath(pth, pp)
        x, y = cam.p(105.4, 29.2); text(c, '只剩益州', x, y, 56, LIU_L, 'serifx', k2, 'c', stroke=8, shadow=10)

def ledger(c, t):
    """第六章：事后的人事账。"""
    a = fade(t, S('g1') + 2.0, S('h1') - 0.8, 0.6, 0.6)
    if a <= 0.003: return
    rows = [(S('g1') + 2.2, '219 冬', '关羽', '斩于临沮', '#FFB199'), (S('g2') + 1.0, '220', '法正', '卒，年四十五', GOLD),
            (S('g2') + 2.8, '220', '孟达', '率部曲四千余家降魏', CAO_L), (S('g2') + 5.2, '220', '刘封', '赐死 ·“不救羽”', '#FFB199'),
            (S('g2') + 7.6, '220—', '麋竺', '面缚请罪，惭恚病卒', '#D9D2C2'),
            (S('g3') + 0.6, '221', '刘备', '东征 ·“群臣多谏，一不从”', LIU_L), (E('g3') - 1.8, '222', '夷陵', '大军败绩', '#FFB199'),
            (S('g5') + 0.6, '223', '诸葛亮', '受托孤 ·“咸决于亮”', GOLD)]
    x, y = 64, 250
    n = sum(1 for r in rows if t >= r[0])
    if n == 0: return
    h = 54 + n * 46
    panel(c, x, y, 620, h, a, r=8, fa=0.82)
    text(c, '事后的账', x + 20, y + 38, 26, GOLD, 'serifx', a)
    for i, (t0, yr, who, what, col) in enumerate(rows[:n]):
        k = ss(ramp(t, t0, t0 + 0.5)) * a; yy = y + 84 + i * 46
        text(c, yr, x + 20, yy, 22, '#A8A294', 'sansm', k)
        text(c, who, x + 116, yy, 28, col, 'serifx', k)
        text(c, what, x + 214, yy, 25, PAPER, 'serifm', k)

def sec7(c, t, cam):
    territories(c, cam, t, 0.9)
    k1 = fade(t, S('h1') - 0.6, S('h2') - 0.3, 0.6, 0.5); k2 = fade(t, S('h2') - 0.2, S('h3') - 0.3, 0.6, 0.5); k3 = ss(ramp(t, S('h3') - 0.2, S('h3') + 0.8))
    if k1 > 0.01:
        cities(c, cam, t, ['江陵', '公安'], k1, major=('江陵',), size=40)
        x, y = P(cam, '江陵'); pulse(c, x, y, t, SUN_L, 18, 90, 1.8, 0.8 * k1)
    if k2 > 0.01:
        pth = mkpath(PL(cam, D.T_JING), True)
        pp = skia.Paint(AntiAlias=True, Color=rgba(PAPER, 0.9 * k2), Style=skia.Paint.kStroke_Style, StrokeWidth=4); pp.setPathEffect(skia.DashPathEffect.Make([14, 10], -(t * 18) % 24))
        c.drawPath(pth, pp)
        cities(c, cam, t, ['江陵', '成都', '白帝'], k2, major=('江陵', '成都'))
    if k3 > 0.01:
        cities(c, cam, t, ['成都', '江陵', '汉中'], k3, major=('成都', '江陵'))
        cx_, cy_ = P(cam, '成都'); jx, jy = P(cam, '江陵')
        line(c, [(cx_, cy_), (jx, jy)], '#F4F0E6', 4, 0.9 * k3, dash=(16, 10), phase=-(t * 20) % 26)
        x, y = (cx_ + jx) / 2, (cy_ + jy) / 2
        text(c, '后方', x, y - 24, 40, GOLD, 'serifx', k3, 'c', stroke=7, shadow=8); text(c, '无人', x, y + 54, 40, '#FFB199', 'serifx', k3, 'c', stroke=7, shadow=8)

def ending_lines(c, t):
    lines = [('h1', '麋芳开的，是一座城。'), ('h2', '关羽丢的，是一块飞地。'), ('h3', '刘备集团在荆州和益州之间，')]
    a_all = 1 - ss(ramp(t, T.end[0] - 0.6, T.end[0]))
    if t < S('h1') - 0.2 or a_all <= 0: return
    dim(c, 0.28 * ss(ramp(t, S('h1') - 0.4, S('h1') + 0.4)) * a_all)
    y = 1040
    for i, (bid, s) in enumerate(lines):
        k = ss(ramp(t, S(bid), S(bid) + 0.7)) * a_all
        text(c, s, 80, y + i * 86 + (1 - k) * 14, 54, PAPER if i < 2 else GOLD, 'serifx', k, stroke=8, shadow=12)
    k = ss(ramp(t, S('h3') + 1.6, S('h3') + 2.3)) * a_all
    text(c, '没人替他守后方。', 80, y + 3 * 86 + (1 - k) * 14, 54, GOLD, 'serifx', k, stroke=8, shadow=12)

# ------------------------------------------------------------------ 整屏卡
def title_card(c, t):
    t0, t1 = T.title
    a = fade(t, t0, t1, 0.6, 0.6)
    if a <= 0.003: return
    dim(c, 0.80 * a)
    k = ss(ramp(t, t0 + 0.2, t0 + 1.0))
    text(c, '细节与胜负手', 540, 560, 30, GOLD, 'sans', a * k, 'c', spacing=12)
    line(c, [(540 - 150 * k, 592), (540 + 150 * k, 592)], GOLD, 2, a)
    text(c, '关羽失荆州', 540, 730 + (1 - k) * 16, 132, PAPER, 'serifx', a * k, 'c', shadow=16, spacing=6)
    k2 = ss(ramp(t, t0 + 0.8, t0 + 1.6))
    text(c, '麋芳为什么开城', 540, 850, 66, '#F3DFA6', 'serifx', a * k2, 'c', shadow=12, spacing=8)
    text(c, '建安二十四年 · 公元 219 年', 540, 940, 30, '#D9D2C2', 'serifm', a * k2, 'c', spacing=4)

def chapter_card(c, t):
    for sec, (t0, t1) in T.chap.items():
        a = fade(t, t0, t1 + 0.5, 0.45, 0.6)
        if a <= 0.003: continue
        num, ttl, sub = SECTIONS[sec]
        dim(c, 0.66 * a)
        k = ss(ramp(t, t0 + 0.1, t0 + 0.8))
        text(c, num, 540, 610, 54, GOLD, 'serifx', a * k, 'c')
        line(c, [(540 - 60 * k, 640), (540 + 60 * k, 640)], GOLD, 2.5, a)
        text(c, ttl, 540, 760 + (1 - k) * 12, 98 if len(ttl) <= 5 else 84, PAPER, 'serifx', a * k, 'c', shadow=14, spacing=6)
        text(c, sub, 540, 840, 30, '#D9D2C2', 'serifm', a * k, 'c', spacing=4)

def end_card(c, t):
    t0, t1 = T.end
    a = ss(ramp(t, t0 - 0.4, t0 + 0.6))
    if a <= 0.003: return
    dim(c, 0.90 * a)
    y = 300
    text(c, '关羽失荆州 · 麋芳为什么开城', 80, y, 40, GOLD, 'serifx', a)
    rows = [('史料', '《三国志》关羽、吕蒙、陆逊、虞翻、先主、法正、'), ('', '诸葛亮、刘封、麋竺、杨洪、廖立、杨戏诸传及裴松之注；'), ('', '《资治通鉴》卷六十八、六十九'),
            ('论说', '田余庆《〈隆中对〉再认识》《李严兴废与诸葛用人》；'), ('', '章太炎《訄书·正葛》；朱绍侯、方诗铭相关论文'),
            ('说明', '演义情节不用；“解读”部分为推论，非史书原文。'), ('', '地图为今地示意，古城与河道位置取近似。'),
            ('地形', 'Mapzen Terrain Tiles（SRTM 等）· 河流 Natural Earth'), ('字体', 'Noto Serif / Sans CJK（SIL OFL）'),
            ('配音', 'Qwen3-TTS 合成（Apache-2.0）· 音乐为程序合成')]
    yy = y + 90
    for k, s in rows:
        if k: text(c, k, 80, yy, 26, GOLD, 'serif', a)
        text(c, s, 170, yy, 26, '#E4DDCF', 'sansm', a); yy += 50 if True else 0

# ------------------------------------------------------------------ 常驻 UI
STAMPS = [('a1', 'a3', '建安二十四年 · 闰十月', '江陵'), ('b1', 'b1', '建安二十四年 · 夏—七月', '汉中'), ('b2', 'b2', '建安二十四年 · 七月', '关羽北攻樊城'),
          ('b3', 'b4', '建安二十四年 · 八月', '樊城'), ('b5', 'b5', '建安二十四年 · 冬十月前后', '许都'),
          ('c1', 'c7', '建安二十四年 · 秋', '关羽的后方'), ('d1', 'd1', '建安二十年（215）', '湘水划界'), ('d2', 'd6', '建安二十四年 · 秋', '孙权一侧'),
          ('e1', 'e2', '建安二十四年 · 闰十月', '寻阳 → 南郡'), ('e3', 'e3', '建安二十四年 · 闰十月', '公安'), ('e4', 'e6', '建安二十四年 · 闰十月', '江陵'),
          ('e7', 'e8', '建安二十四年 · 十一月—十二月', '关羽南还'), ('f1', 'f3', '建安二十四年 · 八月—十二月', '成都 · 上庸'),
          ('g1', 'g1', '建安二十四年 · 十二月', '临沮'), ('g2', 'g2', '建安二十五年（220）', '成都 · 上庸'), ('g3', 'g4', '章武元年—二年（221—222）', '夷陵'), ('g5', 'g5', '章武三年（223）', '永安')]
def stamp(c, t):
    for b0, b1, s1, s2 in STAMPS:
        a = fade(t, S(b0) + 0.1, E(b1) + 0.25, 0.5, 0.4)
        if a <= 0.003: continue
        if b0 in ('c3',): continue
        w = max(tw(s1, 'serif', 30), tw(s2, 'sans', 24)) + 44
        # 被整屏面板遮住的时段隐藏
        if S('f4') < t < S('h1'): continue
        panel(c, 64, 250, w, 96, a, r=6, fa=0.72)
        rrect(c, 64, 250, 6, 96, 2, GOLD, a)
        text(c, s1, 86, 290, 30, PAPER, 'serif', a); text(c, s2, 86, 328, 24, '#D9D2C2', 'sansm', a)

def in_structure(t): return S('f7') - 0.2 < t < S('f9') - 0.1
def jiedu_badge(c, t):
    a = fade(t, S('f4') + 0.2, E('f12') + 0.3, 0.5, 0.5)
    if a <= 0.003: return
    s = '解读' if in_structure(t) else '解读 · 以下为推论，非史书原文'
    w = tw(s, 'sans', 26) + 36
    rrect(c, 930 - w, 232, w, 44, 6, AMBER, 0.95 * a)
    text(c, s, 930 - w / 2, 232 + 32, 26, INK, 'sans', a, 'c')
    if t < S('f4') + 3.5:
        k = fade(t, S('f4') + 0.2, S('f4') + 3.6, 0.5, 0.6)
        dim(c, 0.45 * k)
        text(c, '解读', 540, 700, 150, AMBER, 'serifx', k, 'c', shadow=16, spacing=20)
        text(c, '以下为推论，附原文依据与不同看法', 540, 780, 32, PAPER, 'sans', k, 'c')

NOCARD = {'f7', 'f8'}
def cite_layer(c, t):
    for b in BEATS:
        ct = b.get('cite')
        if not ct or b['id'] in NOCARD: continue
        t0 = S(b['id']) + 0.25
        # 持续到下一段有引文卡出现或本段结束后 0.5 秒
        t1 = E(b['id']) + 0.45
        a = fade(t, t0, t1, 0.4, 0.4)
        if a <= 0.003: continue
        big = b['id'] in ('f10', 'f11', 'f12', 'g4')
        # 估算高度以底对齐
        hh = cite_card(skia.Surface(8, 8).getCanvas(), ct, 1.0, y=0, big=big)
        cite_card(c, ct, a, y=1326 - hh, big=big)

def sub_layer(c, t):
    if t >= S('h1') - 0.5: return
    for (c0, c1, s, q, bid) in T.subs:
        if c0 - 0.05 <= t < c1:
            a = ss(ramp(t, c0 - 0.05, c0 + 0.10)) * (1 - ss(ramp(t, c1 - 0.08, c1)))
            subtitle(c, s, a, q); break

def chapter_tag(c, t):
    for sec, (num, ttl, sub) in SECTIONS.items():
        t0, t1 = T.sec_range(sec)
        a = fade(t, T.chap[sec][1] + 0.3, t1 + 0.3, 0.5, 0.4)
        if a <= 0.003: continue
        s = num + ' · ' + ttl
        if in_structure(t): continue
        yy = 322 if S('f4') + 0.2 < t < E('f12') + 0.3 else 292
        text(c, s, 930, yy, 30, GOLD, 'serif', a, 'r', stroke=6, shadow=8)

# ------------------------------------------------------------------ 主入口
def sec_of(t):
    if t < T.title[1] - 0.6: return 0
    cur = 0
    for sec, (t0, t1) in T.chap.items():
        if t >= t0 + 0.55: cur = sec
    if t >= S('h1') - 1.2: cur = 7
    return cur
def draw_frame(c, t, fi=0):
    cam = cam_at(t)
    draw_base(c, cam)
    sec = sec_of(t)
    rivers(c, cam, 1 - plan_alpha(t))
    [sec0, sec1, sec2, sec3, sec4, sec5, sec6, sec7][sec](c, t, cam)
    if sec in (0, 1, 2, 3) and not (S('b3') < t < S('b5')): river_labels(c, cam, 0.8)
    top_grad(c, 1.0)
    if sec == 2: card_mi(c, t)
    if sec == 5: structure(c, t)
    if sec == 6: ledger(c, t)
    stamp(c, t); chapter_tag(c, t)
    jiedu_badge(c, t)
    cite_layer(c, t)
    ending_lines(c, t)
    vignette(c, 1.0)
    title_card(c, t); chapter_card(c, t); end_card(c, t)
    sub_layer(c, t)
    grain(c, fi)
    # 片头淡入 / 片尾淡出
    a = (1 - ss(ramp(t, 0, 0.9))) + ss(ramp(t, T.total - 0.8, T.total))
    dim(c, a, '#000000')
