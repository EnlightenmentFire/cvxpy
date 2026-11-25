# -*- coding: utf-8 -*-
"""分镜：按时间轴绘制每一帧。背景三条轨（插画 / 地图 / 暗底），前景为卡片与地图标注，最后统一字幕与角标。"""
import math, numpy as np, skia
from gfx import *
from cards import *
from geo import W, H, Cam, Base, merc
import illus
from data import *
from data import T as T_
from timeline import TL

T = TL()
FAC['lu'] = FAC['oth']; FAC['ma'] = FAC['oth']
S, E = T.S, T.E
def SC(k): return T.sc[k]
def win(t, a, b, din=0.45, dout=0.45): return fade(t, a, b, din, dout)
def ln(i): return (S(i), E(i))

_B = {}
def bases():
    if not _B:
        _B[6] = Base('/home/user/work/dem/base6_r.png'); _B[8] = Base('/home/user/work/dem/base8_r.png'); _B[9] = Base('/home/user/work/dem/base9_r.png')
    return _B

# ───────── 相机 ─────────
V_CHINA = Cam(110.5, 33.0, 30.0, 540, 760)
V_WANDER = Cam(115.2, 35.6, 12.5, 540, 760)
V_JING = Cam(112.35, 32.15, 3.6, 540, 700)
V_LZ = Cam(109.5, 32.2, 22.0, 540, 700)
V_LZJ = Cam(111.6, 30.2, 14.0, 540, 700)
V_LZY = Cam(106.2, 30.4, 14.0, 540, 700)
V_LZALL = Cam(108.8, 32.0, 18.0, 540, 700)
V_CHIBI = Cam(113.3, 30.6, 6.8, 540, 700)
V_SI = Cam(112.2, 28.6, 10.5, 540, 700)
V_NEXT = Cam(108.5, 31.0, 13.0, 540, 700)

def _cams():
    k = []   # (t_move_start, t_move_end, cam)
    k.append((0, 0, Cam(110.6, 31.5, 26.0, 540, 760)))
    k.append((S('a08') - 1.0, S('a09') + 1.0, Cam(109.2, 31.2, 20.0, 540, 760)))
    k.append((S('a10'), E('a11'), V_CHINA))
    k.append((S('b01') - 0.4, S('b01') + 2.0, V_WANDER))
    k.append((S('b05') - 0.8, S('b05') + 2.2, V_JING))
    k.append((S('b12') - 1.0, S('b12') + 1.6, V_CHINA))
    k.append((S('d03') - 0.8, S('d03') + 1.6, V_LZ))
    k.append((S('d08') - 0.6, S('d08') + 1.6, V_LZJ))
    k.append((S('d10') - 0.6, S('d10') + 1.6, V_LZY))
    k.append((S('d11') - 0.6, S('d11') + 1.6, V_LZALL))
    k.append((S('d17b') - 0.6, S('d17b') + 1.4, Cam(109.4, 30.8, 9.5, 540, 700)))
    k.append((S('f01') - 1.0, S('f01') + 1.4, V_CHIBI))
    k.append((S('f04') - 0.2, S('f04') + 1.8, V_SI))
    k.append((S('g07') - 0.8, S('g07') + 1.6, V_NEXT))
    return k
CAMK = _cams()
def cam_at(t):
    cur = CAMK[0][2]
    for t0, t1, cm in CAMK[1:]:
        if t >= t1: cur = cm
        elif t > t0:
            cur = Cam.lerp(cur, cm, ease((t - t0) / (t1 - t0))); break
        else: break
    return cur

# ───────── 地图图元 ─────────
_poly = {}
def poly_pts(key, pts):
    if key not in _poly: _poly[key] = smooth(list(pts) + [pts[0]], 3)
    return _poly[key]

def terr(c, cam, key, pts, col, a=1.0, fa=0.34, edge=None, ea=0.9, ew=2.5, blur=10, dash=None, wipe=None):
    """势力范围：羽化填色 + 边线。wipe=(u, 'n2s'|'w2e') 自北向南/自西向东展开。"""
    if a <= 0.003: return
    P = [cam.p(*q) for q in poly_pts(key, pts)]
    path = mkpath(P, True)
    c.save()
    if wipe is not None:
        u, mode = wipe
        ys = [p[1] for p in P]; xs = [p[0] for p in P]
        if mode == 'n2s':
            y0, y1 = min(ys), max(ys); c.clipRect(skia.Rect.MakeLTRB(-50, -50, W + 50, y0 + (y1 - y0) * u))
        else:
            x0, x1 = min(xs), max(xs); c.clipRect(skia.Rect.MakeLTRB(-50, -50, x0 + (x1 - x0) * u, H + 50))
    p = skia.Paint(AntiAlias=True, Color=rgba(col, fa * a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(path, p)
    if edge:
        q = skia.Paint(AntiAlias=True, Color=rgba(edge, ea * a), Style=skia.Paint.kStroke_Style, StrokeWidth=ew)
        q.setStrokeJoin(skia.Paint.kRound_Join)
        if dash: q.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
        c.drawPath(path, q)
    c.restore()

def fac_label(c, cam, k, a=1.0, size=40, sub=None, color=None, dy=0):
    if a <= 0.003: return
    x, y = cam.p(*FAC_LABEL_AT[k]); y += dy
    col = color or FAC[k][2]
    text(c, FAC_NAME[k], x, y, size, col, 'serifx', a, 'c', stroke=6, shadow=8)
    if sub: text(c, sub, x, y + size * 0.95, size * 0.58, '#E8E1D3', 'sansm', a, 'c', stroke=4, shadow=5)

def CP(cam, name): return cam.p(*CITY[name])

def flow(c, pts, t, color, a=1.0, w=5.0, speed=0.35, n=10, r=4.0):
    """沿路线流动的粒子（兵团流动感）。"""
    if a <= 0.003 or len(pts) < 2: return
    for i in range(n):
        u = (t * speed + i / n) % 1.0
        x, y, _ = along(pts, u)
        circle(c, x, y, r, color, a * (0.35 + 0.65 * math.sin(math.pi * u)))
        glow(c, x, y, r * 4, color, 0.35 * a)

def fire(c, x, y, t, a=1.0, s=1.0):
    if a <= 0.003: return
    for k in range(14):
        ph = k * 1.37
        u = (t * 0.9 + k / 14) % 1.0
        xx = x + math.sin(ph * 3 + t * 2) * 26 * s * (1 - u) + (k - 7) * 5 * s
        yy = y - u * 90 * s
        glow(c, xx, yy, (30 - 18 * u) * s, '#FF7A2A', a * (1 - u) * 0.9)
        circle(c, xx, yy, (6 - 4 * u) * s, '#FFD27A', a * (1 - u))
    glow(c, x, y, 120 * s, '#FF5A1F', 0.45 * a)

def draw_map(c, t, cam, a, layers):
    if a <= 0.003: return
    B = bases()
    if a < 0.999: c.saveLayerAlpha(None, int(a * 255))
    c.drawColor(rgba('#141A20'))
    B[6].draw(c, cam)
    if cam.span < 20: B[8].draw(c, cam, clamp((20 - cam.span) / 5))
    if cam.span < 6.5: B[9].draw(c, cam, clamp((6.5 - cam.span) / 1.8))
    dim(c, 0.18)
    layers(c, t, cam)
    if a < 0.999: c.restore()

# ───────── 暗底（插画虚化） ─────────
_plate = {}
def plate(c, a=1.0, warm=0.0):
    if a <= 0.003: return
    if 'p' not in _plate:
        s = skia.Surface(W, H); cc = s.getCanvas()
        illus.draw(cc, 2.0, door=1.0, light=1.0, mapu=1.0, mglow=1.0, lit=(1, 1), snow_a=0.0)
        img = s.makeImageSnapshot()
        s2 = skia.Surface(W, H); c2 = s2.getCanvas()
        p = skia.Paint(); p.setImageFilter(skia.ImageFilters.Blur(22, 22))
        c2.drawImage(img, 0, 0, skia.SamplingOptions(), p)
        c2.drawColor(rgba('#07090C', 0.72))
        _plate['p'] = s2.makeImageSnapshot()
    pa = skia.Paint(); pa.setAlphaf(a)
    c.drawImage(_plate['p'], 0, 0, skia.SamplingOptions(), pa)

# ───────── 各场景 ─────────
def L_hook4(c, t, cam):
    k = ease(ramp(t, S('a08') + 0.2, S('a08') + 1.6))
    for f in ('cao', 'sun', 'zhang', 'biao', 'lu', 'ma'):
        terr(c, cam, f, T_[f], FAC[f][0], 0.6 * win(t, S('a08') - 0.6, SC('hook5')[1] + 0.5), fa=0.22, edge=FAC[f][2], ea=0.35, ew=1.5)
    terr(c, cam, 'biao_r', T_['biao'], LIU, k, fa=0.55, edge=LIU_L, ew=3, wipe=(k, 'n2s'))
    k2 = ease(ramp(t, S('a08') + 1.0, S('a08') + 2.4))
    terr(c, cam, 'zhang_r', T_['zhang'], LIU, k2, fa=0.55, edge=LIU_L, ew=3, wipe=(k2, 'w2e'))
    for nm, (x, y) in (('荆州', cam.p(112.0, 29.3)), ('益州', cam.p(104.3, 28.8))):
        text(c, nm, x, y, 52, '#FFE3D8', 'serifx', max(k, k2) * win(t, S('a08'), SC('hook4')[1] + 0.3), 'c', stroke=7, shadow=10)

from data import T as T_


def L_wander(c, t, cam):
    t0 = S('b01') + 0.8; t1 = E('b04') - 0.5
    pts = [CITY[w[0]] for w in WANDER]
    P = [cam.p(*q) for q in pts]
    u = ease(ramp(t, t0, t1))
    # 已走过的路线
    arrow(c, smooth(P, 2), LIU, u, w=7, head=26, dash=None)
    n = len(P)
    for i, (nm, yr, who) in enumerate(WANDER):
        ui = i / (n - 1)
        ka = ss(ramp(u, ui - 0.02, ui + 0.04))
        if ka <= 0: continue
        x, y = P[i]
        if nm == '下邳' and i == 4: continue
        city(c, x, y, nm, 'liu' if i == n - 1 else None, ka, size=30, major=(i == n - 1), anchor='l' if x < 760 else 'r', dx=16)
        if who:
            side = 1 if x < 760 else -1
            tag(c, x + side * 18, y + 22, f'{yr} · {who}', LIU if i else GOLD, ka, size=24, anchor='l' if side > 0 else 'r')
    # 吕布（求和）旁注
    kb = ss(ramp(u, 0.36, 0.44)) * win(t, S('b02'), SC('wander')[1])
    x, y = cam.p(*CITY['小沛'])
    tag(c, x - 18, y - 70, '196 · 向吕布求和', OTH_L, kb, size=22, anchor='r')

def O_wander(c, t):
    a = win(t, S('b01'), SC('wander')[1] + 0.2)
    if a <= 0: return
    panel(c, 60, 1040, 960, 250, a, fa=0.82)
    yrs = int(lerp(184, 207, ease(ramp(t, S('b01') + 0.5, E('b01')))))
    text(c, f'{yrs}', 100, 1150, 92, LIU_L, 'serifx', a)
    text(c, '年', 100 + tw(f'{yrs}', 'serifx', 92) + 8, 1150, 40, '#E8E1D3', 'serif', a)
    text(c, '从起兵到隆中：二十三年', 330, 1118, 34, GOLD, 'serif', a)
    text(c, '依附五个东家：公孙瓒 陶谦 曹操 袁绍 刘表', 330, 1170, 30, '#EDE6D8', 'sansm', a * win(t, S('b02'), 1e9))
    text(c, '徐州两得两失 · 无一块稳固的地盘', 100, 1250, 32, '#F2B6A8', 'sansm', a * win(t, S('b03'), 1e9))


def L_jing(c, t, cam):
    a0 = win(t, S('b05') - 0.4, SC('bairou')[0] + 0.6)
    terr(c, cam, 'biao', T_['biao'], BIAO, a0, fa=0.30, edge=BIAO_L, ea=0.7, ew=3)
    terr(c, cam, 'cao', T_['cao'], '#0C0C0E', a0, fa=0.62, edge=CAO_L, ea=0.95, ew=3.5)
    # 曹军压力：北方金线脉动
    x, y = cam.p(112.53, 33.25)
    text(c, '曹操', x, y - 40, 50, CAO_L, 'serifx', a0, 'c', stroke=7, shadow=10)
    text(c, '已定河北，兵锋向南', x, y + 4, 28, '#E8DDC2', 'sansm', a0, 'c', stroke=4, shadow=5)
    for k in range(3):
        xx = x - 160 + k * 160
        arrow(c, [(xx, y + 40), (xx + 10, y + 150)], CAO_L, ease(ramp(t, S('b06'), S('b06') + 1.2)), w=9, a=a0 * 0.8, head=26)
    for nm, fac, maj, anc, dy in (('宛', 'cao', False, 'l', 10), ('襄阳', 'biao', True, 'l', 44), ('樊城', None, False, 'l', 4), ('隆中', None, False, 'r', 10)):
        x2, y2 = CP(cam, nm)
        city(c, x2, y2, nm, fac, a0, size=34 if maj else 30, major=maj, anchor=anc, dx=18, dy=dy)
    xn, yn = CP(cam, '新野')
    city(c, xn, yn, '', 'liu', a0, major=True)
    unit(c, xn + 70, yn - 6, 'liu', '刘备', a0 * win(t, S('b05'), 1e9), s=1.1, sub='驻新野 · 兵数千')
    pulse(c, xn, yn, t, LIU, a=a0 * 0.8)
    xb, yb = CP(cam, '襄阳')
    text(c, '刘表', xb - 40, yb + 150, 44, BIAO_L, 'serifx', a0, 'r', stroke=6, shadow=8)
    text(c, '荆州牧 · 驻襄阳', xb - 40, yb + 190, 26, '#DDE8D6', 'sansm', a0, 'r', stroke=4, shadow=5)
    # 看大门
    kd = win(t, S('b06') + 0.6, E('b06') + 2.0)
    tag(c, xn - 40, yn - 120, '北门的门卫', LIU, kd, size=30, anchor='r')
    # 刘表的戒备：襄阳→新野 虚线监视
    kw = win(t, S('b07'), E('b08') + 0.6)
    if kw > 0:
        line(c, [(xb + 10, yb - 10), (xn - 12, yn + 12)], BIAO_L, 4, kw, dash=(16, 10), phase=-t * 40)
        mx, my = (xb + xn) / 2 + 40, (yb + yn) / 2
        text(c, '表疑其心，阴御之', mx + 20, my, 30, BIAO_L, 'serif', kw, 'l', stroke=5, shadow=6)
    # 隆中
    xl, yl = CP(cam, '隆中')
    glow(c, xl, yl, 40, '#FFC870', 0.5 * a0 * (0.6 + 0.4 * math.sin(t * 2)))


def L_cao(c, t, cam):
    a = win(t, S('b12') - 0.3, SC('caonorth')[1] + 0.4)
    k = ease(ramp(t, S('b12') + 0.3, S('b12') + 2.4))
    terr(c, cam, 'cao', T_['cao'], '#0C0C0E', a, fa=0.66, edge=CAO_L, ea=0.95, ew=3, wipe=(k, 'n2s'))
    x, y = cam.p(113.6, 37.0)
    text(c, '曹操', x, y, 58, CAO_L, 'serifx', a * k, 'c', stroke=7, shadow=10)
    text(c, '平定河北 · 北征乌桓（207）', x, y + 46, 30, '#F0E4C4', 'sansm', a * k, 'c', stroke=4, shadow=5)
    x1, y1 = cam.p(*CITY['邺城']); x2, y2 = cam.p(*CITY['柳城'])
    arrow(c, [(x1, y1), (x1 + 120, y1 - 120), (x2, y2)], CAO_L, ease(ramp(t, S('b12') + 1.6, S('b12') + 3.2)), w=8, a=a, head=24)
    xn, yn = CP(cam, '新野')
    circle(c, xn, yn, 9, LIU, a); pulse(c, xn, yn, t, LIU, r0=8, r1=36, a=a)
    tag(c, xn + 20, yn + 14, '刘备 · 新野', LIU, a, size=22)


def L_lz(c, t, cam):
    s1, s2, s3, s4, s5, s6 = S('d03'), S('d05'), S('d08'), S('d10'), S('d11'), S('d12')
    end = SC('rank')[1] + 0.3
    aa = win(t, s1 - 0.6, end)
    # 底色：各方势力
    for f in ('ma', 'lu'):
        terr(c, cam, f, T_[f], FAC['oth'][0] if f == 'ma' else FAC['oth'][0], aa, fa=0.25, edge=OTH_L, ea=0.4, ew=1.5)
    # ① 曹操：玄黑描金，然后上锁变灰
    lk = ease(ramp(t, s1 + 2.2, s1 + 3.4))
    terr(c, cam, 'cao', T_['cao'], mix('#0C0C0E', '#4A4E54', lk), aa, fa=0.66, edge=mix(CAO_L, '#9AA0A6', lk), ea=0.95, ew=3)
    if lk > 0:
        x, y = cam.p(113.2, 35.4); y = max(y, 330)
        lock_icon(c, x, y - 10, 1.25, aa * lk)
        text(c, '不可与争锋', x, y + 100, 40, '#E4E6E8', 'serifx', aa * lk, 'c', stroke=6, shadow=8)
    # ② 孙权：同盟色带
    ka = win(t, s2 - 0.2, end)
    terr(c, cam, 'sun', T_['sun'], SUN, ka, fa=0.38, edge=SUN_L, ea=0.8, ew=2.5)
    kb = ease(ramp(t, s2 + 2.0, s2 + 3.4))
    if kb > 0:
        band = [cam.p(115.6, 31.2), cam.p(115.3, 30.1), cam.p(114.8, 29.2), cam.p(114.3, 28.0), cam.p(114.0, 26.2)]
        line(c, trim(smooth(band, 2), 0, kb), SUN_L, 22, 0.35 * ka, blur=8)
        line(c, trim(smooth(band, 2), 0, kb), SUN_L, 8, 0.9 * ka)
        x, y = cam.p(118.4, 28.6)
        text(c, '可以为援', x, y, 40, SUN_L, 'serifx', ka * kb, 'c', stroke=6, shadow=8)
        text(c, '而不可图', x, y + 48, 40, SUN_L, 'serifx', ka * kb, 'c', stroke=6, shadow=8)
    # ③ 荆州
    kj = ease(ramp(t, s3 + 0.2, s3 + 2.0))
    terr(c, cam, 'biao', T_['biao'], BIAO, aa * (1 - kj), fa=0.28, edge=BIAO_L, ea=0.6, ew=2)
    terr(c, cam, 'biao_r', T_['biao'], LIU, aa * kj, fa=0.55, edge=LIU_L, ew=3.5, wipe=(kj, 'n2s'))
    if kj > 0:
        x, y = cam.p(112.0, 28.8)
        text(c, '荆州', x, y, 54, '#FFE3D8', 'serifx', aa * kj, 'c', stroke=7, shadow=10)
        text(c, '用武之国', x, y + 44, 30, '#FFD3C6', 'sansm', aa * kj, 'c', stroke=5, shadow=6)
        # 四通：汉沔 / 南海 / 吴会 / 巴蜀
        kk = win(t, s3 + 1.6, s4 + 0.5)
        cx, cy = cam.p(112.3, 30.6)
        for (lo, la, nm) in ((112.4, 33.6, '北据汉沔'), (113.0, 24.2, '利尽南海'), (116.3, 30.9, '东连吴会'), (108.6, 31.2, '西通巴蜀')):
            x2, y2 = cam.p(lo, la)
            arrow(c, [(cx, cy), (x2, y2)], '#FFB08F', ease(ramp(t, s3 + 1.6, s3 + 2.6)), w=4, a=kk * 0.9, head=16, glow=False)
            text(c, nm, x2, y2 + (-14 if la > 30.6 else 36), 28, '#FFE3D8', 'serif', kk, 'c', stroke=5, shadow=6)
    # ④ 益州
    ky = ease(ramp(t, s4 + 0.2, s4 + 2.0))
    terr(c, cam, 'zhang', T_['zhang'], ZHANG, aa * (1 - ky) * win(t, s1 - 0.6, end), fa=0.30, edge=ZHANG_L, ea=0.6, ew=2)
    terr(c, cam, 'zhang_r', T_['zhang'], LIU, aa * ky, fa=0.55, edge=LIU_L, ew=3.5, wipe=(ky, 'w2e'))
    if ky > 0:
        x, y = cam.p(104.0, 28.6)
        text(c, '益州', x, y, 54, '#FFE3D8', 'serifx', aa * ky, 'c', stroke=7, shadow=10)
        text(c, '天府之土 · 刘璋暗弱', x, y + 44, 28, '#FFD3C6', 'sansm', aa * ky, 'c', stroke=5, shadow=6)
        xh, yh = cam.p(*CITY['汉中'])
        text(c, '张鲁', xh + 30, yh - 20, 30, OTH_L, 'serif', aa * ky, 'l', stroke=5, shadow=6)
    # ⑤ 保其岩阻：外缘发光 + 西和诸戎、南抚夷越
    kr = win(t, s5, end)
    if kr > 0:
        for key in ('biao_r', 'zhang_r'):
            P = [cam.p(*q) for q in poly_pts(key, T_['biao' if key == 'biao_r' else 'zhang'])]
            line(c, P, '#FFCF9E', 10, 0.30 * kr * (0.7 + 0.3 * math.sin(t * 3)), blur=6)
        for (lo, la, nm) in ((99.5, 31.5, '西和诸戎'), (106.0, 23.4, '南抚夷越')):
            x, y = cam.p(lo, la)
            text(c, nm, x, y, 30, '#F3DFA6', 'serif', kr * ease(ramp(t, s5 + 1.5, s5 + 2.5)), 'c', stroke=5, shadow=6)
        kq = ease(ramp(t, s5 + 3.0, s5 + 4.2))
        x1, y1 = cam.p(113.0, 30.5); x2, y2 = cam.p(116.6, 30.0)
        line(c, [(x1, y1), (x2, y2)], SUN_L, 5, kr * kq, dash=(14, 10), phase=-t * 30)
        text(c, '外结好孙权', (x1 + x2) / 2 + 10, (y1 + y2) / 2 - 24, 28, SUN_L, 'serif', kr * kq, 'c', stroke=5, shadow=6)
    # ⑥ 两路北伐
    for path, d0, lab, at in ((R_JING_N, s6 + 0.6, '荆州之军 → 宛、洛', (113.0, 33.4)), (R_YI_N, S('d13') + 0.2, '益州之众 → 秦川', (105.6, 34.4))):
        P = smooth([cam.p(*q) for q in path], 2)
        u = ease(ramp(t, d0, d0 + 2.4))
        ka2 = win(t, d0 - 0.1, end)
        if u > 0:
            arrow(c, P, LIU, u, w=20, a=ka2, head=56)
            flow(c, trim(P, 0, u), t, '#FFD0B8', ka2 * 0.9, speed=0.5, n=8, r=4.5)
            x, y = cam.p(*at)
            text(c, lab, x, y, 32, '#FFE3D8', 'serifx', ka2 * ss(ramp(u, 0.6, 1)), 'c', stroke=6, shadow=8)
    for nm in ('洛阳', '长安', '宛', '成都', '江陵', '襄阳', '汉中'):
        kc = aa * (win(t, s6 - 0.2, end) if nm in ('洛阳', '长安', '宛') else win(t, s3 if nm in ('江陵', '襄阳') else s4, end))
        x, y = CP(cam, nm)
        city(c, x, y, nm, None, kc, size=26)
    # 三峡（后世批评）
    kx = win(t, S('d17b'), E('d17b') + 0.5)
    if kx > 0:
        x1, y1 = cam.p(109.4, 31.6); x2, y2 = cam.p(110.6, 30.2)
        line(c, [(x1, y1), (x2, y2)], '#FFFFFF', 6, kx, dash=(12, 10))
        xs, ys = cam.p(*CITY['白帝'])
        tag(c, xs + 30, ys - 140, '三峡相隔 · 兵力一分为二', '#BFC6CC', kx, size=28)
        text(c, '后世常见的批评', xs + 42, ys - 74, 24, '#D9DEE2', 'sansm', kx, stroke=4, shadow=5)


def L_chibi(c, t, cam):
    st = SC('chibi')[0]; en = SC('chibi')[1] + 0.3
    a = win(t, st - 0.4, en)
    terr(c, cam, 'cao', T_['cao'], '#0C0C0E', a, fa=0.55, edge=CAO_L, ea=0.8, ew=3)
    terr(c, cam, 'sun', T_['sun'], SUN, a, fa=0.32, edge=SUN_L, ea=0.6, ew=2)
    # 曹军南下
    P = smooth([cam.p(*q) for q in R_CAO_S], 2)
    u = ease(ramp(t, S('f01') + 0.4, S('f01') + 3.8))
    arrow(c, P, '#2A2A2E', u, w=22, a=a, head=56)
    line(c, trim(P, 0, max(0, u - 0.04)), CAO_L, 3, a * 0.9)
    flow(c, trim(P, 0, u), t, CAO_L, a * 0.8, speed=0.6, n=10, r=4)
    kc = win(t, S('f01') + 0.2, E('f01') + 1)
    tag(c, 70, 300, '208 · 刘表病死 · 刘琮投降', CAO_L, kc, size=30)
    # 刘备南撤、长坂
    P2 = smooth([cam.p(*q) for q in R_LIU_RET], 2)
    u2 = ease(ramp(t, S('f02'), S('f02') + 2.4))
    arrow(c, P2, LIU, u2, w=12, a=a, head=34)
    xd, yd = CP(cam, '当阳')
    kx = ss(ramp(t, S('f02') + 2.2, S('f02') + 3.2))
    if kx > 0:
        for k in range(10):
            ang = k * 0.63 + 0.3; r = 20 + 60 * kx
            circle(c, xd + math.cos(ang) * r, yd + math.sin(ang) * r, 6 * (1 - kx * 0.6), LIU, a * (1 - kx) * 0.9 + 0.1 * a)
        glow(c, xd, yd, 90, '#FF4A2A', 0.5 * a * (1 - kx * 0.5))
        text(c, '长坂', xd - 30, yd + 10, 34, '#FFFFFF', 'serifx', a, 'r', stroke=6, shadow=8)
        text(c, '几乎全军覆没', xd - 30, yd + 48, 26, '#F2B6A8', 'sansm', a * kx, 'r', stroke=4, shadow=5)
    P3 = smooth([cam.p(*q) for q in R_LIU_E], 2)
    arrow(c, P3, LIU, ease(ramp(t, S('f02') + 3.0, S('f02') + 4.6)), w=8, a=a * 0.9, head=24, dash=(18, 10))
    # 出使江东
    P4 = smooth([cam.p(*q) for q in R_ENVOY], 2)
    u4 = ease(ramp(t, S('f03'), S('f03') + 2.0))
    arrow(c, P4, '#FFE3A8', u4, w=6, a=a, head=22, dash=(14, 10))
    xc, yc = CP(cam, '柴桑')
    tag(c, xc - 30, yc + 30, '诸葛亮出使 · 说孙权', GOLD, a * ss(ramp(u4, 0.6, 1)), size=24, anchor='r')
    # 孙刘联军上溯、赤壁之火
    P5 = smooth([cam.p(*q) for q in R_SUN_UP], 2)
    u5 = ease(ramp(t, S('f03') + 2.4, S('f03') + 4.4))
    arrow(c, P5, SUN, u5, w=16, a=a, head=44)
    P6 = smooth([cam.p(*q) for q in R_CAO_DOWN], 2)
    arrow(c, P6, '#2A2A2E', ease(ramp(t, S('f03') + 1.4, S('f03') + 3.4)), w=16, a=a, head=44)
    xr, yr = CP(cam, '赤壁')
    kf = ss(ramp(t, S('f03') + 4.3, S('f03') + 5.0)) * win(t, S('f03'), en)
    fire(c, xr, yr, t, kf, 1.3)
    text(c, '赤壁', xr, yr + 64, 40, '#FFE3C8', 'serifx', kf, 'c', stroke=6, shadow=10)
    kr = ease(ramp(t, S('f03') + 5.6, S('f03') + 7.6))
    P7 = smooth([cam.p(*q) for q in R_CAO_RET], 2)
    arrow(c, P7, '#55575C', kr, w=12, a=a * win(t, S('f03') + 5, E('f04') - 1), head=34, dash=(16, 12))
    # 南四郡
    k4 = ease(ramp(t, S('f04') + 1.6, S('f04') + 3.4))
    terr(c, cam, 'si', T_SI, LIU, a * k4, fa=0.55, edge=LIU_L, ew=3.5, wipe=(k4, 'n2s'))
    for nm in ('武陵', '长沙', '桂阳', '零陵'):
        x, y = CP(cam, nm)
        city(c, x, y, nm, 'liu', a * k4, size=30)
    for nm, anc in (('江陵', 'l'), ('夏口', 'l'), ('襄阳', 'r'), ('柴桑', 'l')):
        x, y = CP(cam, nm); city(c, x, y, nm, None, a * (1 - k4 * 0.5), size=26, anchor=anc)
    tag(c, 70, 300, '南征四郡 · 第一次有了自己的地盘', LIU, a * k4, size=30)


def L_next(c, t, cam):
    a = win(t, S('g07') - 0.6, T.total + 1)
    terr(c, cam, 'si2', T_SI, LIU, a, fa=0.5, edge=LIU_L, ew=3)
    terr(c, cam, 'zhang', T_['zhang'], ZHANG, a, fa=0.35, edge=ZHANG_L, ew=2.5)
    P = smooth([cam.p(*q) for q in R_RUSHU], 2)
    u = ease(ramp(t, S('g07') + 0.8, S('g07') + 3.4))
    arrow(c, P, LIU, u, w=18, a=a, head=50)
    flow(c, trim(P, 0, u), t, '#FFD0B8', a, speed=0.5, n=8)
    x, y = CP(cam, '汉中'); kh = ss(ramp(t, S('g07') + 3.6, S('g07') + 4.6))
    glow(c, x, y, 90, '#FFC870', 0.7 * a * kh); city(c, x, y, '汉中', 'liu', a * kh, size=34, major=True)
    x, y = CP(cam, '成都'); city(c, x, y, '成都', None, a, size=30)


def map_layers(c, t, cam):
    if t < SC('wander')[0] + 0.5: L_hook4(c, t, cam)
    if SC('wander')[0] - 0.5 < t < SC('xinye')[0] + 2: L_wander(c, t, cam)
    if SC('xinye')[0] - 1 < t < SC('caonorth')[0] + 1: L_jing(c, t, cam)
    if SC('caonorth')[0] - 0.5 < t < SC('q3')[1]: L_cao(c, t, cam)
    if SC('lz1')[0] - 1 < t < SC('rank')[1] + 1: L_lz(c, t, cam)
    if SC('chibi')[0] - 1 < t < SC('chibi')[1] + 1: L_chibi(c, t, cam)
    if t > SC('next')[0] - 1: L_next(c, t, cam)


# ───────── 背景轨 ─────────
def tracks(t):
    """返回 (插画, 地图, 暗底, 地图压暗) 的可见度。"""
    il = 0.0; mp = 0.0; pl = 0.0; md = 0.0
    # 开场插画：到 hook4 推进地图
    il = max(il, 1 - ss(ramp(t, S('a08') - 0.2, S('a08') + 0.9)))
    # 地图段
    for a, b in ((S('a08') - 0.2, SC('bairou')[0] + 0.8), (SC('caonorth')[0] - 0.6, SC('q3')[0] + 1.2),
                 (SC('lz1')[0] - 0.8, SC('rank')[1] + 0.8), (SC('chibi')[0] - 0.8, SC('chibi')[1] + 0.8), (SC('next')[0] - 0.8, T.total + 2)):
        mp = max(mp, fade(t, a, b, 0.8, 0.8))
    # 暗底（插画虚化）
    for a, b in ((SC('hook1')[0] - 0.4, S('a08') + 0.6), (SC('bairou')[0] + 0.2, SC('caonorth')[0] + 0.2), (SC('q3')[0] + 0.6, SC('lz0')[0] + 0.4),
                 (SC('ana3')[0] - 0.6, SC('chibi')[0] + 0.4), (SC('takeaway')[0] - 0.4, SC('next')[0] + 0.4)):
        pl = max(pl, fade(t, a, b, 0.7, 0.7))
    # 插画回归：隆中对开场、结尾
    for a, b in ((SC('lz0')[0] - 0.6, SC('lz1')[0] + 0.6), (SC('end')[0] - 0.6, SC('takeaway')[0] + 0.4)):
        il = max(il, fade(t, a, b, 0.8, 0.8))
    # 地图段压暗（卡片在上）
    md = max(win(t, SC('hook5')[0], SC('hook5')[1], 0.6, 0.6) * 0.55,
             win(t, SC('rank')[0] + 0.5, S('d17b') - 0.3, 0.6, 0.6) * 0.45)
    return il, mp, pl, md


SECT = [('open', '一 · 隆中一幕'), ('wander', '二 · 新野的处境'), ('src1', '三 · 三顾的史料'), ('lz0', '四 · 隆中对'),
        ('fish', '五 · 鱼水'), ('chibi', '六 · 一年之后'), ('end', '七 · 收束')]


def section(t):
    cur = None
    for k, s in SECT:
        if t >= SC(k)[0] - 0.2: cur = (k, s)
    return cur


# ───────── 前景卡片 ─────────
def overlays(c, t):
    # ===== 开场 =====
    st, en = SC('open')
    if t < en + 0.6:
        a1 = 1.0 if t < E('a01') else 1 - ss(ramp(t, E('a01'), E('a01') + 0.4))
        big(c, '四十七岁', 300, 120, '#FFF2E6', a1, stroke=9)
        text(c, '换过五个东家 · 没有一块自己的地盘', 540, 384, 40, '#F3E6D8', 'sans', a1, 'c', stroke=6, shadow=8)
        a2 = win(t, S('a02') - 0.1, E('a02') + 0.3, 0.3, 0.4)
        big(c, '二十六岁的年轻人', 290, 86, '#FFE7C2', a2, stroke=9)
        text(c, '给了他一张地图', 540, 370, 46, '#FFD9A0', 'serifx', a2, 'c', stroke=7, shadow=10)
        a3 = win(t, S('a03'), en + 0.3)
        tag(c, 60, 240, '建安十二年（207）前后 · 隆中（襄阳城西）', GOLD, a3, size=28)
        text(c, '刘备 · 四十七岁', 770, 940, 34, '#FFFFFF', 'serifx', a3, 'c', stroke=6, shadow=8)
        text(c, '诸葛亮 · 二十六岁', 425, 935, 32, '#FFE7C2', 'serifx', a3, 'c', stroke=6, shadow=8)
    # ===== 钩子：三张卡 =====
    a = win(t, *SC('hook1'))
    if a > 0:
        big(c, '三顾茅庐', 420, 110, '#F3DFA6', a, stroke=8)
        for i in range(3):
            ka = ss(ramp(t, S('a04') + 2.2 + i * 0.7, S('a04') + 2.6 + i * 0.7)) * a
            circle(c, 360 + i * 180, 560, 52, LIU, ka); text(c, '一二三'[i] + '往', 360 + i * 180, 576, 36, '#FFFFFF', 'serifx', ka, 'c')
        quote_card(c, '由是先主遂詣亮，凡三往，乃見。', '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=720, baihua='于是刘备去见诸葛亮，去了三次才见到。', hl='凡三往，乃見', hla=ramp(t, S('a05'), S('a05') + 0.8))
    a = win(t, *SC('hook2'))
    if a > 0:
        big(c, '另一种说法', 400, 92, '#BFD9E8', a, stroke=8)
        flip = ease(ramp(t, S('a06') + 1.6, S('a06') + 2.6))
        xl, xr, yy = 250, 830, 640
        circle(c, xl, yy, 74, LIU, a); text(c, '刘备', xl, yy + 14, 40, '#FFFFFF', 'serifx', a, 'c')
        circle(c, xr, yy, 74, '#E9DFC6', a); text(c, '诸葛亮', xr, yy + 13, 36, INK, 'serifx', a, 'c')
        arrow(c, [(xl + 90, yy - 30), (xr - 90, yy - 30)], LIU, 1.0, w=10, a=a * (1 - flip) + 0.25 * a * flip, head=30)
        text(c, '陈寿：刘备三往', 540, yy - 60, 28, '#F5C4B8', 'sans', a * (1 - flip * 0.7), 'c', stroke=5)
        arrow(c, [(xr - 90, yy + 34), (xl + 90, yy + 34)], '#9FC3D8', flip, w=10, a=a, head=30)
        text(c, '《魏略》：亮先北行见备', 540, yy + 100, 28, '#CFE3EE', 'sans', a * flip, 'c', stroke=5)
        quote_card(c, '亮乃北行見備，備與亮非舊，又以其年少，以諸生意待之。', '《諸葛亮傳》裴注引魚豢《魏略》', 'pei', a * flip, y=820,
                   baihua='诸葛亮主动北上见刘备；刘备看他年轻，当普通书生对待。')
    a = win(t, *SC('hook3'))
    if a > 0:
        big(c, '当事人怎么说', 400, 92, '#F3DFA6', a, stroke=8)
        tag(c, 540, 470, '诸葛亮自述 · 二十年后（227）', GOLD, a, size=28, anchor='c')
        quote_card(c, '先帝不以臣卑鄙，猥自枉屈，\n三顧臣於草廬之中', '諸葛亮《出師表》，載《三國志·諸葛亮傳》', 'zishu', a, y=600, size=54,
                   baihua='先帝不嫌我卑微，屈尊三次到草庐来看我。', hl='三顧臣於草廬之中', hla=ramp(t, S('a07') + 3.5, S('a07') + 4.5))
    a = win(t, *SC('hook4'))
    if a > 0:
        quote_card(c, '若跨有荊、益，保其巖阻', '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=1010, size=58, baihua='如果占有荆州、益州，守住险要。')
    a = win(t, *SC('hook5'))
    if a > 0:
        big(c, '他缺的是什么？', 330, 88, '#FFFFFF', a, stroke=8)
        items = [('关羽 张飞 赵云', S('a10') + 1.4), ('名气 · 帝室之胄', S('a10') + 2.4), ('左将军名号', S('a10') + 3.2)]
        for i, (s_, t0) in enumerate(items):
            k = ss(ramp(t, t0, t0 + 0.4)) * a
            panel(c, 120, 430 + i * 104, 840, 84, k, fa=0.8)
            text(c, s_, 160, 486 + i * 104, 38, '#F2EEE6', 'sans', k)
            text(c, '有', 900, 488 + i * 104, 38, '#9FD39A', 'sansx', k, 'r')
        kq = ss(ramp(t, S('a11'), S('a11') + 0.5)) * a
        panel(c, 120, 780, 840, 84, kq, fa=0.8)
        text(c, '兵', 160, 836, 38, '#F2EEE6', 'sans', kq); text(c, '不是关键', 900, 838, 34, '#D8D2C4', 'sansm', kq, 'r')
        kr = ss(ramp(t, S('a11') + 2.6, S('a11') + 3.2)) * a
        panel(c, 90, 930, 900, 230, kr, fill='#2A0F0B', fa=0.88, edge=LIU_L, ea=0.6)
        text(c, '缺一张', 540, 1012, 40, '#F5C4B8', 'sans', kr, 'c')
        text(c, '排好先后顺序的路线图', 540, 1100, 62, '#FFE3D8', 'serifx', kr, 'c', stroke=4)
    # ===== 新野 =====
    O_wander(c, t)
    a = win(t, S('b07') - 0.2, E('b08') + 0.4)
    if a > 0:
        quote_card(c, '荊州豪傑歸先主者日益多，表疑其心，陰禦之。', '《三國志·蜀書·先主傳》', 'zheng', a, y=1000, baihua='投奔刘备的人越多，刘表越防着他。')
    a = win(t, *SC('bairou'))
    if a > 0:
        big(c, '髀肉复生', 420, 130, '#F3DFA6', a, stroke=9, spacing=10)
        text(c, '寄人篱下的第六七年', 540, 500, 34, '#E8E1D3', 'sansm', a, 'c', stroke=5) if False else None
        quote_card(c, '吾常身不離鞍，髀肉皆消。今不復騎，髀裏肉生。\n日月若馳，老將至矣，而功業不建，是以悲耳。', '《先主傳》裴注引《九州春秋》', 'pei', a, y=560, size=46,
                   baihua='我常年不离马鞍，大腿上的肉都消了；如今不骑马，肉又长回来。时光飞驰，人快老了，功业还没建，所以伤心。')
    a = win(t, *SC('q3'))
    if a > 0:
        rows = [('手里有什么', ['兵：数千人（《魏略》亮语「將軍之眾不過數千人」）', '名号：左将军（曹操表奏）', '人：关羽 张飞 赵云；荆州士人在观望'], ss(ramp(t, S('b14'), S('b14') + 0.5))),
                ('借了谁的势', ['刘表的庇护', '「帝室之冑」的名分'], ss(ramp(t, S('b16'), S('b16') + 0.5))),
                ('做对了哪一步', ['放下身段，向荆州本地士人网络', '求战略、求人才'], ss(ramp(t, S('b17'), S('b17') + 0.5)))]
        q3_card(c, rows, a, y=330)
    a = win(t, *SC('ana1'))
    if a > 0:
        analogy_card(c, '左将军：像朝廷正式授予的高级将衔，位次在三公之后，可手下只有几千人。整个处境，像一个名声在外的流亡将领，寄身地方实力派，被派去守边境当缓冲。',
                     '刘备的名号来自汉朝廷，名义上不比刘表低；他寄人篱下，却不是谁的部下。', a, ab=ss(ramp(t, S('b20'), S('b20') + 0.5)), y=420)
    # ===== 三顾的史料 =====
    srcs_on = win(t, SC('src1')[0], SC('pei')[1])
    if srcs_on > 0:
        cur = 0 if t < SC('src2')[0] else 1 if t < SC('src3')[0] else 2 if t < SC('pei')[0] else 3
        labs = [('① 陈寿正文', GOLD), ('②《出师表》自述', '#F1D68E'), ('③ 裴注引《魏略》', '#9FC3D8')]
        for i, (s_, col) in enumerate(labs):
            on = 1.0 if (i == cur or cur == 3) else 0.35
            x = 60 + i * 325
            rrect(c, x, 236, 310, 58, 4, col if i == cur else '#0B0D10', srcs_on * (0.92 if i == cur else 0.7))
            text(c, s_, x + 155, 275, 27, INK if i == cur else col, 'sans', srcs_on * (1 if i == cur else on), 'c')
    a = win(t, S('c01b') - 0.2, E('c01b') + 0.3)
    if a > 0:
        panel(c, 60, 360, 960, 170, a, fa=0.82)
        text(c, '诸葛亮 · 字孔明', 100, 430, 46, '#FFE7C2', 'serifx', a)
        text(c, '琅邪阳都人 · 早孤，随叔父依刘表 · 躬耕隆中', 100, 490, 30, '#E8E1D3', 'sansm', a)
        quote_card(c, '每自比於管仲、樂毅，時人莫之許也。', '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=590, baihua='常把自己比作管仲、乐毅，当时的人大多不认可。')
    a = win(t, S('c02') - 0.2, SC('src1')[1])
    if a > 0:
        quote_card(c, '先主曰：「君與俱來。」\n庶曰：「此人可就見，不可屈致也。」', '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=380, baihua='这个人只能亲自去见，不能叫他来。',
                   hl='此人可就見，不可屈致也', hla=ramp(t, S('c03') + 1.2, S('c03') + 2.2))
        k = win(t, S('c05') - 0.2, SC('src1')[1])
        quote_card(c, '由是先主遂詣亮，凡三往，乃見。', '《三國志·蜀書·諸葛亮傳》', 'zheng', k, y=840, baihua='于是刘备前后去了三次，才见到。')
    a = win(t, *SC('src2'))
    if a > 0:
        quote_card(c, '先帝不以臣卑鄙，猥自枉屈，三顧臣於草廬之中，諮臣以當世之事', '諸葛亮《出師表》（227），載《諸葛亮傳》', 'zishu', a, y=380, size=50,
                   baihua='先帝不嫌我卑微，屈尊三次到草庐来看我，向我询问天下大事。')
        k = win(t, S('c08'), SC('src2')[1])
        for i, s_ in enumerate(['写给后主刘禅的奏表', '满朝文武都会读到', '编造先帝之事，风险极高']):
            kk = k * ss(ramp(t, S('c08') + i * 1.4, S('c08') + i * 1.4 + 0.4))
            panel(c, 60, 900 + i * 96, 960, 78, kk, fa=0.82)
            text(c, s_, 100, 952 + i * 96, 36, '#F2EEE6', 'sans', kk)
        text(c, '→ 最硬的证据', 1000, 1230, 38, GOLD, 'serifx', k * ss(ramp(t, S('c08') + 4.0, S('c08') + 4.6)), 'r', stroke=5)
    a = win(t, *SC('src3'))
    if a > 0:
        panel(c, 60, 360, 960, 150, a, fa=0.82)
        text(c, '鱼豢《魏略》', 100, 425, 42, '#CFE3EE', 'serifx', a)
        text(c, '曹魏一方的私家史书 · 裴松之注引用', 100, 480, 30, '#DDE6EC', 'sansm', a)
        k = win(t, S('c10') - 0.2, SC('src3')[1])
        quote_card(c, '劉備屯於樊城。是時曹公方定河北，亮知荊州次當受敵，而劉表性緩，不曉軍事。', '《諸葛亮傳》裴注引《魏略》', 'pei', k, y=560, size=44)
        k2 = win(t, S('c11') - 0.2, SC('src3')[1])
        quote_card(c, '亮乃北行見備，備與亮非舊，又以其年少，以諸生意待之。', '《諸葛亮傳》裴注引《魏略》', 'pei', k2, y=890, size=46,
                   baihua='两人素不相识，刘备嫌他年轻，当普通书生对待。')
    a = win(t, *SC('maoniu'))
    if a > 0:
        # 牦牛尾饰（毦）
        cx, cy = 540, 520
        k = ss(ramp(t, S('c13') + 1.0, S('c13') + 2.0)) * a
        rrect(c, cx - 14, cy - 150, 28, 60, 6, '#8A6A3A', k)
        for i in range(36):
            ang = -0.55 + i * 0.03 + 0.04 * math.sin(t * 1.5 + i)
            L_ = 220 + 30 * math.sin(i * 1.7)
            line(c, [(cx, cy - 92), (cx + math.sin(ang) * L_ * 0.6, cy - 92 + math.cos(ang) * L_)], mix('#E9E2D2', '#B9AE98', (i % 5) / 5), 3, k * 0.9)
        text(c, '毦（ěr）：用牦牛尾编的饰物', 540, 760, 32, '#E8E1D3', 'sansm', k, 'c', stroke=5)
        k2 = win(t, S('c14') - 0.2, SC('maoniu')[1])
        quote_card(c, '明將軍當復有遠志，但結毦而已邪！', '《諸葛亮傳》裴注引《魏略》', 'pei', k2 * (1 - ss(ramp(t, S('c16') - 0.4, S('c16')))), y=830, size=52,
                   baihua='将军难道没有远大的志向，就只会编这个吗？')
        k3 = win(t, S('c16') - 0.2, SC('maoniu')[1])
        quote_card(c, '備知亮非常人也，乃投毦而答曰：\n「是何言與！我聊以忘憂耳。」', '《諸葛亮傳》裴注引《魏略》', 'pei', k3, y=830, size=46,
                   baihua='刘备把东西一扔：这是什么话！我不过借此解闷。')
    a = win(t, *SC('huji'))
    if a > 0:
        draw_huji(c, t, a)
    a = win(t, *SC('pei'))
    if a > 0:
        quote_card(c, '臣松之以為亮表云「先帝不以臣卑鄙，猥自枉屈，三顧臣於草廬之中，諮臣以當世之事」，則非亮先詣備，明矣。', '《諸葛亮傳》裴松之按語', 'pei_an', a, y=350, size=44,
                   baihua='可见不是诸葛亮先去见刘备。', hl='則非亮先詣備，明矣', hla=ramp(t, S('c25') + 3.0, S('c25') + 4.0))
        k = win(t, S('c27'), SC('pei')[1])
        rows = [('三顾茅庐', '当事人自述 + 正史 → 可信度高', GOLD, S('c28')), ('《魏略》先诣说', '另一种记载 → 并列保存，不必二选一', '#9FC3D8', S('c28') + 3.2),
                ('它至少说明', '诸葛亮也懂户口、兵源这种实务', '#E8E1D3', S('c29'))]
        for i, (h_, b_, col, t0) in enumerate(rows):
            kk = k * ss(ramp(t, t0, t0 + 0.5))
            panel(c, 60, 880 + i * 128, 960, 108, kk, fa=0.84)
            rrect(c, 60, 880 + i * 128, 8, 108, 3, col, kk)
            text(c, h_, 96, 925 + i * 128, 32, col, 'serif', kk)
            text(c, b_, 96, 968 + i * 128, 31, '#F2EEE6', 'sansm', kk)
    a = win(t, *SC('yanyi'))
    if a > 0:
        big(c, '演义 vs 史书', 470, 96, '#FFFFFF', a, stroke=8)
        yanyi_card(c, '刘备冒雪三访；张飞嚷着要去屋后放一把火。', '《诸葛亮传》只有「凡三往，乃見」：没有雪，也没有火。', a, a2=ss(ramp(t, S('c31') + 2.6, S('c31') + 3.2)), y=600)
    a = win(t, *SC('ana2'))
    if a > 0:
        analogy_card(c, '为什么非得亲自去？像想请一位不肯出山的名家：只能登门拜访，不能发个通知调人。',
                     '东汉名士拒绝征召本身就是身份资本，拒绝越多名声越高；今天没有这种制度化的清高。', a, ab=ss(ramp(t, S('c33'), S('c33') + 0.5)), y=480)
    # ===== 隆中对 =====
    a = win(t, *SC('lz0'))
    if a > 0:
        big(c, '隆中对', 330, 130, '#FFE7C2', a, stroke=9, spacing=14)
        text(c, '三步，一张路线图', 540, 410, 40, '#F3E6D8', 'sans', a * ss(ramp(t, S('d02'), S('d02') + 0.5)), 'c', stroke=6, shadow=8)
        quote_card(c, '孤不度德量力，欲信大義於天下，而智術淺短……君謂計將安出？', '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=1060, size=40, baihua='我想伸张大义于天下，可是谋略浅短……您看该怎么办？')
    lzq = [('lz1', '今操已擁百萬之眾，挾天子而令諸侯，此誠不可與爭鋒。', '曹操兵多，又挟持天子，不能跟他正面争。', '第一步 · 曹操'),
           ('lz2', '孫權據有江東，已歷三世，國險而民附，賢能為之用，此可以為援而不可圖也。', '孙权根基稳固，可以当盟友，不能打他的主意。', '第二步 · 孙权'),
           ('lz3', '荊州北據漢、沔，利盡南海，東連吳會，西通巴、蜀，此用武之國，而其主不能守', '四通八达的兵家要地，主人却守不住。', '第三步 · 荆州'),
           ('lz4', '益州險塞，沃野千里，天府之土……劉璋闇弱，張魯在北', '益州地势险要、物产丰饶；刘璋软弱，北边还有张鲁。', '第三步 · 益州'),
           ('lz5', '若跨有荊、益，保其巖阻，西和諸戎，南撫夷越，外結好孫權，內修政理', '占有荆益、守住险要，安抚周边，联孙权，修内政。', '核心'),
           ('lz6', '天下有變，則命一上將將荊州之軍以向宛、洛，將軍身率益州之眾出於秦川', '天下一旦有变，两路北伐。', '最后一步 · 等待')]
    for k_, q, bh, hd in lzq:
        a = win(t, *SC(k_))
        if a > 0:
            tag(c, 60, 236, hd, LIU if k_ != 'lz2' else SUN_L, a, size=32)
            quote_card(c, q, '《三國志·蜀書·諸葛亮傳》', 'zheng', a, y=1010 if k_ not in ('lz5', 'lz6') else 1000, size=42, baihua=bh)
    a = win(t, SC('rank')[0], S('d17b') - 0.2)
    if a > 0:
        rows = [('先做', '取荆州，取益州', LIU, S('d15')), ('不做', '不与曹操争锋，不打孙权主意', '#9AA0A6', S('d15') + 2.6),
                ('结盟', '孙权', SUN_L, S('d16')), ('等待', '天下有变，两路北伐', GOLD, S('d16') + 1.6)]
        big(c, '价值在于排序', 330, 84, '#FFFFFF', a, stroke=8)
        for i, (h_, b_, col, t0) in enumerate(rows):
            kk = a * ss(ramp(t, t0, t0 + 0.45))
            y = 420 + i * 138
            panel(c, 90, y, 900, 116, kk, fa=0.86)
            rrect(c, 90, y, 150, 116, 6, col, kk * 0.92)
            text(c, h_, 165, y + 74, 46, INK if col != '#9AA0A6' else '#111111', 'serifx', kk, 'c')
            text(c, b_, 270, y + 74, 40, '#F2EEE6', 'sans', kk)
    a = win(t, S('d18') - 0.2, SC('rank')[1])
    if a > 0:
        big(c, '战略，也是起家资源', 640, 74, '#FFE3D8', a, stroke=8)
        text(c, '不能当饭吃，但决定了几千人往哪里用', 540, 720, 38, '#F3E6D8', 'sans', a, 'c', stroke=6, shadow=8)
    a = win(t, *SC('ana3'))
    if a > 0:
        analogy_card(c, '一个流亡多年的军政人物，第一次请到本地智囊。智囊拿出的不是口号，而是一份分阶段的区域战略：哪些对手不碰，跟谁结盟，先拿哪两块根据地，什么条件下再出手。',
                     '诸葛亮带来的不只是方案，还有一整张荆州士族关系网；今天的智囊很少自带这种家族资源。', a, ab=ss(ramp(t, S('d21'), S('d21') + 0.5)), y=360)
    a = win(t, *SC('net'))
    if a > 0:
        draw_net(c, t, a)
    # ===== 鱼水 =====
    a = win(t, *SC('fish'))
    if a > 0:
        draw_fish(c, t, a)
    a = win(t, *SC('ana4'))
    if a > 0:
        analogy_card(c, '像一支打了多年仗的老部队，主帅请来一位年轻参谋长，当众宣布：他的话，就是我的话。',
                     '关张与刘备「寢則同床，恩若兄弟」（《關羽傳》），摩擦多在情分上，不是今天那种职位之争。', a, ab=ss(ramp(t, S('e08'), S('e08') + 0.5)), y=480)
    # ===== 收束 =====
    a = win(t, S('g01') - 0.3, E('g01') + 0.4)
    if a > 0:
        for i, s_ in enumerate(['四十七岁', '寄人篱下', '兵不过数千']):
            kk = a * ss(ramp(t, S('g01') + 2.6 + i * 0.9, S('g01') + 3.0 + i * 0.9))
            text(c, s_, 540, 330 + i * 92, 60, '#FFF2E6', 'serifx', kk, 'c', stroke=8, shadow=12)
    a = win(t, S('g02') - 0.2, E('g04') + 0.5)
    if a > 0:
        quote_card(c, '受任於敗軍之際，\n奉命於危難之間。', '諸葛亮《出師表》，載《三國志·諸葛亮傳》', 'zishu', a, y=360, size=66,
                   baihua='在兵败的时候接受任命，在危难之中奉命出使。', ba=a * ss(ramp(t, S('g04') - 0.2, S('g04') + 0.4)))
    a = win(t, S('g05') - 0.2, SC('end')[1] + 0.2)
    if a > 0:
        text(c, '路线图最值钱的时候，', 540, 420, 52, '#FFF2E6', 'serifx', a, 'c', stroke=8, shadow=12)
        text(c, '是你手里什么都没有的时候。', 540, 500, 52, '#FFE3C2', 'serifx', a, 'c', stroke=8, shadow=12)
    a = win(t, *SC('takeaway'))
    if a > 0:
        panel(c, 60, 520, 960, 520, a, fill='#120D0B', fa=0.9, edge=GOLD, ea=0.5)
        text(c, '一句可以带走的判断', 110, 610, 34, GOLD, 'sans', a)
        for i, s_ in enumerate(['缺资源的时候，', '最先要补的往往不是钱和人，', '而是一张排好先后顺序的', '路线图。']):
            text(c, s_, 110, 720 + i * 82, 54 if i < 3 else 70, '#FFF6E6' if i < 3 else '#FFB9A6', 'serifx', a * ss(ramp(t, S('g06') + i * 0.8, S('g06') + i * 0.8 + 0.5)))
    a = win(t, S('g07') - 0.3, T.total + 1)
    if a > 0:
        tag(c, 60, 236, '下一集', LIU, a, size=34)
        big(c, '入蜀与汉中称王', 360, 84, '#FFE3D8', a, stroke=8)
        text(c, '乱世起家录｜刘备篇', 540, 1230, 36, '#E8E1D3', 'serif', a * ss(ramp(t, S('g07') + 2, S('g07') + 3)), 'c', stroke=5, shadow=6)


# ───────── 户籍机制动画 ─────────
_ppl = None
def draw_huji(c, t, a):
    global _ppl
    if _ppl is None:
        r = np.random.default_rng(21)
        _ppl = [(110 + (i % 16) * 54 + r.uniform(-8, 8), 400 + (i // 16) * 54 + r.uniform(-8, 8), r.random() < 0.22, r.random()) for i in range(16 * 7)]
    tag(c, 60, 236, '另一种记载 · 裴注引《魏略》', '#9FC3D8', a, size=28)
    text(c, '荆州人口（示意）', 100, 372, 30, '#E8E1D3', 'sans', a)
    conv = ease(ramp(t, S('c20') + 0.5, S('c21') + 2.0))
    flowk = ease(ramp(t, S('c22'), S('c22') + 2.5))
    for x, y, reg, ph in _ppl:
        on = reg or (ph < conv)
        col = LIU_L if on else '#6B7078'
        if on and not reg and conv < 1 and ph > conv - 0.08:
            glow(c, x, y, 26, '#FFD0B8', 0.6 * a)
        circle(c, x, y - 7, 8, col, a * (1 if on else 0.75))
        rrect(c, x - 9, y + 3, 18, 18, 6, col, a * (1 if on else 0.75))
    k1 = win(t, S('c18') - 0.2, SC('huji')[1])
    tag(c, 100, 790, '著籍者（在户口上）', LIU_L, k1 * (1 - conv * 0.6), size=26)
    tag(c, 440, 790, '游户（没上户口）：国家看不见', '#9AA0A6', k1 * (1 - conv), size=26)
    if flowk > 0:
        for i, (lab, col) in enumerate((('兵源', LIU), ('赋税', GOLD))):
            y = 870 + i * 70
            text(c, lab, 100, y + 40, 34, col, 'sans', a * ss(flowk * 3))
            rrect(c, 190, y + 8, 780, 44, 6, '#20242A', a * 0.8)
            rrect(c, 190, y + 8, 780 * (0.22 + 0.68 * flowk), 44, 6, col, a)
    k2 = win(t, S('c19'), S('c22') - 0.3)
    quote_card(c, '今荊州非少人也，而著籍者寡，平居發調，則人心不悅；可語鎮南，令國中凡有游戶，皆使自實，因錄以益眾可也。', '《諸葛亮傳》裴注引《魏略》', 'pei', k2, y=870, size=40,
               baihua='让游户自己申报、登记入籍，就能增加兵员。', hl='皆使自實', hla=ramp(t, S('c20'), S('c20') + 1.0))
    k3 = win(t, S('c23') - 0.2, SC('huji')[1])
    quote_card(c, '備從其計，故眾遂強。', '《諸葛亮傳》裴注引《魏略》', 'pei', k3, y=1040, size=50, baihua='刘备照办，队伍就壮大了。')


# ───────── 荆州士人网络 ─────────
def draw_net(c, t, a):
    N = {'亮': (540, 760, '诸葛亮', '#FFE7C2'), '黄': (250, 560, '黄承彦', '#E8E1D3'), '妻': (250, 760, '黄氏（妻）', '#E8E1D3'),
         '蔡': (540, 360, '蔡讽', '#B8B0C9'), '长': (290, 420, '长女', '#B8B0C9'), '小': (810, 420, '小女', '#B8B0C9'),
         '表': (830, 600, '刘表', BIAO_L), '庞': (830, 920, '庞德公之子', '#E8E1D3'), '徽': (250, 960, '司马徽', '#E8E1D3'), '统': (540, 1060, '庞统（凤雏）', '#E8E1D3')}
    tA, tB, tC, tD = S('d22'), S('d23'), S('d25'), S('d25b')
    E_ = [('黄', '妻', '父女', tA), ('妻', '亮', '夫妻', tA + 1.0), ('蔡', '长', '', tB + 2.0), ('长', '黄', '妻', tB + 3.0), ('蔡', '小', '', tB + 3.6),
          ('小', '表', '后妻', tB + 4.4), ('庞', '亮', '娶亮二姐', tC + 0.8), ('徽', '亮', '伏龙', tD + 3.0), ('徽', '统', '凤雏', tD + 4.0)]
    vis = {'亮': tA - 0.4, '黄': tA, '妻': tA + 0.8, '蔡': tB + 1.6, '长': tB + 2.2, '小': tB + 3.4, '表': tB + 4.2, '庞': tC + 0.4, '徽': tD + 1.0, '统': tD + 3.8}
    tag(c, 60, 236, '一张网 · 荆州士人圈', GOLD, a, size=30)
    for u, v, lab, t0 in E_:
        k = ease(ramp(t, t0, t0 + 0.7)) * a
        if k <= 0: continue
        x1, y1 = N[u][:2]; x2, y2 = N[v][:2]
        line(c, [(x1, y1), (x1 + (x2 - x1) * k, y1 + (y2 - y1) * k)], GOLD if u != '小' else BIAO_L, 4, 0.85 * a)
        if lab: text(c, lab, (x1 + x2) / 2 + 12, (y1 + y2) / 2 - 10, 28, '#F3DFA6', 'sansm', k, 'l', stroke=5)
    for key, (x, y, nm, col) in N.items():
        k = ss(ramp(t, vis[key], vis[key] + 0.5)) * a
        if k <= 0: continue
        big_ = key == '亮'
        r_ = 78 if big_ else 66
        circle(c, x, y, r_, '#0B0D10', 0.9 * k)
        circle(c, x, y, r_, col, k, stroke=3)
        if big_: glow(c, x, y, 160, '#FFC870', 0.35 * k)
        fs = 38 if big_ else (32 if len(nm) < 4 else 25 if len(nm) < 6 else 22)
        text(c, nm, x, y + fs * 0.36, fs, col, 'serifx', k, 'c')
    # 关键句：岳母与刘表夫人是亲姐妹
    k = win(t, S('d24'), SC('net')[1])
    if k > 0:
        line(c, [(356, 420), (744, 420)], '#FFB9A6', 4, k, dash=(12, 8))
        text(c, '亲姐妹', 540, 470, 34, '#FFB9A6', 'serifx', k, 'c', stroke=5)
    # 出处卡（随句换）
    cards = [(S('d22'), S('d23') - 0.2, '黃承彥者，高爽開列，為沔南名士', '《諸葛亮傳》裴注引《襄陽記》', 'pei'),
             (S('d23') - 0.2, S('d25') - 0.2, '漢末，諸蔡最盛。蔡諷……長女為黃承彥妻；小女為劉景升後婦', '習鑿齒《襄陽記》（後人輯本）', 'ji'),
             (S('d25') - 0.2, S('d25b') - 0.2, '德公子山民，亦有令名，娶諸葛孔明小姊', '《龐統傳》裴注引《襄陽記》', 'pei'),
             (S('d25b') - 0.2, SC('net')[1], '此間自有伏龍、鳳雛', '《諸葛亮傳》裴注引《襄陽記》', 'pei')]
    for t0, t1, q, src, lay in cards:
        k = win(t, t0, t1, 0.3, 0.3) * a
        if k > 0: quote_card(c, q, src, lay, k, y=1150, size=38, w=960)


# ───────── 鱼水 ─────────
def draw_fish(c, t, a):
    cx, cy = 540, 520
    # 水波
    for i in range(4):
        u = ((t * 0.25) + i / 4) % 1
        circle(c, cx, cy, 80 + u * 260, '#7FB2C9', a * (1 - u) * 0.6, stroke=3)
    # 鱼（简笔）
    ang = t * 0.9
    fx, fy = cx + math.cos(ang) * 150, cy + math.sin(ang) * 90
    c.save(); c.translate(fx, fy); c.rotate(math.degrees(ang) + 90)
    p = skia.Path(); p.moveTo(-60, 0); p.cubicTo(-30, -34, 30, -30, 54, 0); p.cubicTo(30, 30, -30, 34, -60, 0); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba('#E8502F', a)))
    tp = skia.Path(); tp.moveTo(-56, 0); tp.lineTo(-96, -26 + 8 * math.sin(t * 6)); tp.lineTo(-96, 26 + 8 * math.sin(t * 6)); tp.close()
    c.drawPath(tp, skia.Paint(AntiAlias=True, Color=rgba('#C63A2E', a)))
    circle(c, 34, -8, 5, '#111111', a)
    c.restore()
    k = win(t, S('e04') - 0.2, SC('fish')[1])
    quote_card(c, '孤之有孔明，猶魚之有水也。\n願諸君勿復言。', '《三國志·蜀書·諸葛亮傳》', 'zheng', k * (1 - ss(ramp(t, S('e06') - 0.4, S('e06')))), y=860, size=56,
               baihua='我有孔明，就像鱼有了水。请各位不要再说了。')
    k0 = win(t, S('e01'), S('e04') - 0.3)
    if k0 > 0:
        # 关张 vs 诸葛亮
        for (x, y, nm, col) in ((260, 960, '关羽 张飞', '#E8E1D3'), (820, 960, '诸葛亮', '#FFE7C2'), (540, 1180, '刘备', LIU_L)):
            circle(c, x, y, 76, '#0B0D10', 0.9 * k0); circle(c, x, y, 76, col, k0, stroke=3)
            text(c, nm, x, y + 12, 30, col, 'serifx', k0, 'c')
        ks = win(t, S('e02'), S('e04') - 0.3)
        for i in range(6):
            xx = 540 + math.sin(t * 13 + i * 2) * 60; yy = 960 + math.cos(t * 11 + i * 3) * 30
            line(c, [(xx - 14, yy - 14), (xx + 14, yy + 14)], AMBER, 4, ks * (0.5 + 0.5 * math.sin(t * 20 + i)))
        text(c, '老兄弟不悦', 540, 880, 30, AMBER, 'sans', ks, 'c', stroke=5)
        kp = win(t, S('e03'), S('e04') - 0.3)
        line(c, [(560, 1110), (790, 1020)], LIU_L, 9, kp)
        text(c, '当众表态', 720, 1110, 30, LIU_L, 'serifx', kp, 'l', stroke=5)
    k2 = win(t, S('e05') - 0.2, E('e05') + 0.4)
    if k2 > 0:
        text(c, '羽、飛乃止。', 540, 760, 60, '#FFFFFF', 'tcx', k2 * ss(ramp(t, S('e05') + 3.0, S('e05') + 3.6)), 'c', stroke=8, shadow=12)
    k3 = win(t, S('e06') - 0.2, SC('fish')[1])
    if k3 > 0:
        for i, s_ in enumerate(['引入新核心', '老人必有摩擦', '一把手公开表态，不留余地']):
            kk = k3 * ss(ramp(t, S('e06') + i * 1.6, S('e06') + i * 1.6 + 0.4))
            panel(c, 120, 860 + i * 120, 840, 96, kk, fa=0.86)
            text(c, s_, 540, 922 + i * 120, 40, '#F2EEE6' if i < 2 else '#FFD3C6', 'sans', kk, 'c')
            if i < 2: text(c, '↓', 540, 972 + i * 120, 30, GOLD, 'sans', kk, 'c')


# ───────── 主函数 ─────────
def draw_frame(c, t, fi):
    c.clear(rgba('#07090C'))
    il, mp, pl, md = tracks(t)
    if il > 0.003:
        st = SC('open')
        if t < SC('hook5')[0]:
            door = 0.62 + 0.38 * ease(ramp(t, 0.1, 1.3))
            mapu = ease(ramp(t, S('a02') - 0.6, S('a02') + 0.8))
            lit = (ss(ramp(t, S('a02') + 1.0, S('a02') + 1.5)), ss(ramp(t, S('a02') + 1.6, S('a02') + 2.1)))
            z = 1.0 + 0.08 * ramp(t, 0, S('a08')) + 3.2 * ease(ramp(t, S('a08') - 1.2, S('a08') + 0.9))
            if pl > 0.003 and t < S('a08') - 1.2: z = 1.0 + 0.08 * ramp(t, 0, S('a08'))
            illus.draw(c, t, door=door, light=1.0, mapu=mapu, mglow=1.0, lit=lit, a=il, zoom=z, zx=290, zy=1150)
        else:
            illus.draw(c, t, door=1.0, light=1.0, mapu=1.0, mglow=1.0, lit=(1, 1), a=il, zoom=1.04 + 0.03 * math.sin(t * 0.1))
    if mp > 0.003:
        cam = cam_at(t)
        draw_map(c, t, cam, mp, map_layers)
    if pl > 0.003:
        plate(c, pl)
    if md > 0.003: dim(c, md)
    top_grad(c, 1.0)
    overlays(c, t)
    vignette(c)
    grain(c, fi)
    sec = section(t)
    if sec and t > 1.0:
        k = sec[0]
        section_tag(c, sec[1], 1.0 if k != 'open' else win(t, S('a03'), SC('open')[1]))
    corner(c, 1.0, mp if mp > 0.5 else 0.0)
    # 字幕
    for c0, c1, s, i in T.subs:
        if c0 - 0.05 <= t < c1:
            subtitle(c, s, fade(t, c0 - 0.05, c1, 0.08, 0.08), y=1500)
            break
