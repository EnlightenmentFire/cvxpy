# -*- coding: utf-8 -*-
"""逍遥津 · 质感重做版渲染器。
深色晕渲动态地图（AWS Terrain Tiles 高程 + Natural Earth 河湖）、上帝视角沙盘、密集军团、粗辉光箭头、
风尘火星粒子、镜头震动、深色宋体原文卡。旁白与句级时码沿用 timeline_yy.json，不改。

  python3 render2.py frames t1,t2,... out_prefix
  python3 render2.py chunk k n out.mp4
"""
import json, math, os, random, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from script_data import S
import gfx as G
from gfx import text, tw, wrap, rrect, panel, arrow, line, circle, glow, pulse, ss, eout, ease, clamp, lerp, ramp, rgba, mix
from geo import W, H, Cam, Base, merc
import visuals2 as V

FPS = 25
DEM = os.environ.get('XYJ_DEM', '/tmp/claude-0/-home-user-cvxpy/8f678480-9a35-54cd-8cf9-5e81f813bb7e/scratchpad/dem')

# ───────── 配色：魏 汉红 / 吴 孙青 ─────────
WEI, WEI_D, WEI_L = '#D8402C', '#6E1D14', '#FF8F73'
WU, WU_D, WU_L = '#1E98A2', '#08454B', '#76DCE0'
LE = '#D6B46A'          # 乐进（守）
GOLD, PAPER, INK = '#E6CC8F', '#F3EEE4', '#0E0F11'
AMBER = '#F2A93B'
WATER = '#5E9DB8'

# ───────── 地理（示意）─────────
P = dict(
    合肥=(117.270, 31.876), 逍遥津=(117.300, 31.842), 居巢=(117.870, 31.600), 濡须口=(118.300, 31.390),
    皖城=(116.570, 30.640), 巢湖=(117.560, 31.560), 汉中=(107.03, 33.07), 邺=(114.38, 36.33), 许=(113.82, 34.03),
    长安=(108.94, 34.27), 陆口=(113.93, 29.84), 建业=(118.78, 32.05), 江陵=(112.19, 30.35))
SHI = [(117.10, 31.935), (117.20, 31.885), (117.255, 31.855), (117.300, 31.842), (117.345, 31.815), (117.375, 31.770),
       (117.400, 31.715), (117.425, 31.668)]          # 施水（南淝河）示意
CAMP = (117.304, 31.872)    # 吴军营（城东，示意）
HILL = (117.317, 31.866)    # 高冢（示意）
GATE = (117.282, 31.868)    # 合肥东门（示意）

BASES = {}


def base(z):
    if z not in BASES:
        BASES[z] = Base(f'{DEM}/base{z}.png')
    return BASES[z]


def load_rivers():
    out = []
    d = json.load(open(f'{DEM}/ne_10m_rivers_lake_centerlines.geojson'))
    keep = {'Chang Jiang', 'Yangtze', 'Huai', 'Hudi', 'Han', 'Xiang', 'Huang', 'Wei', 'Gan'}
    for f in d['features']:
        nm = f['properties'].get('name'); g = f['geometry']
        if not g or nm not in keep: continue
        ls = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for l in ls:
            if any(102 < c[0] < 124 and 25 < c[1] < 39 for c in l):
                w = 3.4 if nm in ('Chang Jiang', 'Yangtze', 'Huang') else 2.2
                out.append((nm, w, [(c[0], c[1]) for c in l]))
    return out


RIVERS = None


def draw_rivers(c, cam, a=1.0, scale=1.0, shi=True):
    global RIVERS
    if RIVERS is None: RIVERS = load_rivers()
    for nm, w, pts in RIVERS:
        sp = [cam.p(*q) for q in pts]
        if all(x < -200 or x > W + 200 for x, y in sp) and all(y < -200 or y > H + 200 for x, y in sp): continue
        ww = w * scale
        line(c, sp, WATER, ww * 3.2, 0.18 * a, blur=ww * 1.5)
        line(c, sp, '#7DB4CC', ww, 0.85 * a)
    if shi:
        sp = [cam.p(*q) for q in SHI]
        line(c, G.smooth(sp, 2), WATER, 6 * scale, 0.2 * a, blur=5)
        line(c, G.smooth(sp, 2), '#7DB4CC', 2.2 * scale, 0.85 * a)


# ───────── 背景、粒子、部队 ─────────
def shade_top(c, a=1.0):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 380)], [rgba('#000000', 0.7 * a), rgba('#000000', 0)]))
    c.drawRect(skia.Rect.MakeWH(W, 380), p)
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 1150), (0, 1340)], [rgba('#000000', 0), rgba('#000000', 0.82 * a)]))
    c.drawRect(skia.Rect.MakeXYWH(0, 1150, W, 190), p)
    c.drawRect(skia.Rect.MakeXYWH(0, 1340, W, H - 1340), skia.Paint(Color=rgba('#000000', 0.82 * a)))


def tint(c, col, a):
    if a > 0.003: c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=rgba(col, a)))


def dawn(c, k=1.0):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 300), (0, 1300)], [rgba('#2A3A5C', 0.25 * k), rgba('#FF8A4A', 0.16 * k)]))
    p.setBlendMode(skia.BlendMode.kScreen); c.drawRect(skia.Rect.MakeWH(W, H), p)


def wind(c, t, a=1.0, n=26, ang=-0.32, seed=1):
    """风：斜向细丝。"""
    if a <= 0.01: return
    rr = random.Random(seed)
    dx, dy = math.cos(ang), math.sin(ang)
    for k in range(n):
        sp = rr.uniform(260, 520); L = rr.uniform(60, 180); y0 = rr.uniform(200, 1300); ph = rr.uniform(0, 3000)
        x = (ph + t * sp) % (W + 600) - 300
        y = y0 + (x * math.tan(ang)) * 0.2
        line(c, [(x, y), (x + dx * L, y + dy * L * 0.2)], '#E8E2D0', 1.3, 0.10 * a * rr.uniform(0.5, 1))


def dust(c, x, y, t, a=1.0, n=14, spread=60, seed=0, col='#B8A27A', drift=(40, -12), size=26):
    if a <= 0.01: return
    rr = random.Random(seed)
    for k in range(n):
        ph = rr.uniform(0, 1); per = rr.uniform(1.6, 2.8)
        u = ((t / per) + ph) % 1.0
        ox, oy = rr.uniform(-spread, spread), rr.uniform(-spread * 0.4, spread * 0.4)
        px, py = x + ox + drift[0] * u * 2, y + oy + drift[1] * u * 2
        circle(c, px, py, size * (0.5 + u), col, 0.16 * a * (1 - u) * math.sin(math.pi * min(1, u * 3)), blur=size * 0.5)


def embers(c, x, y, t, a=1.0, n=10, spread=40, seed=0):
    if a <= 0.01: return
    rr = random.Random(seed)
    for k in range(n):
        ph = rr.uniform(0, 1); per = rr.uniform(1.2, 2.2); u = ((t / per) + ph) % 1.0
        px = x + rr.uniform(-spread, spread) + math.sin(t * 3 + k) * 8 + u * 30
        py = y - u * rr.uniform(80, 160)
        circle(c, px, py, rr.uniform(1.6, 3.2), '#FFB25A', 0.9 * a * (1 - u))
    glow(c, x, y, spread * 1.4, '#FF8A3A', 0.35 * a)


def fire(c, x, y, t, a=1.0, s=1.0, seed=0):
    fl = 0.8 + 0.2 * math.sin(t * 11 + seed)
    glow(c, x, y, 46 * s * fl, '#FF7A2A', 0.6 * a)
    circle(c, x, y, 6 * s * fl, '#FFD27A', a)
    embers(c, x, y, t, a * 0.8, n=5, spread=8 * s, seed=seed)


def block(c, cx, cy, ang, rows, cols, col, a=1.0, gap=9.0, size=5.0, jitter=0.0, t=0.0, seed=0, light=None):
    """方阵：rows×cols 个小方块。"""
    if a <= 0.01: return
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    rr = random.Random(seed)
    for r in range(rows):
        for q in range(cols):
            lx = (q - (cols - 1) / 2) * gap; ly = (r - (rows - 1) / 2) * gap
            if jitter:
                lx += math.sin(t * 2.3 + rr.uniform(0, 6)) * jitter; ly += math.cos(t * 1.9 + rr.uniform(0, 6)) * jitter
            pts.append(skia.Point(cx + lx * ca - ly * sa, cy + lx * sa + ly * ca))
    p = skia.Paint(AntiAlias=False, Color=rgba(INK, 0.7 * a), StrokeWidth=size + 2.4); p.setStrokeCap(skia.Paint.kSquare_Cap)
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, p)
    p = skia.Paint(AntiAlias=False, Color=rgba(col, a), StrokeWidth=size); p.setStrokeCap(skia.Paint.kSquare_Cap)
    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, p)
    if light:
        glow(c, cx, cy, max(rows, cols) * gap * 0.9, light, 0.22 * a)


def dots(c, pts, col, a=1.0, size=5.0, outline=True):
    if a <= 0.01 or not pts: return
    sp = [skia.Point(x, y) for x, y in pts]
    if outline:
        p = skia.Paint(AntiAlias=False, Color=rgba(INK, 0.7 * a), StrokeWidth=size + 2.4); p.setStrokeCap(skia.Paint.kSquare_Cap)
        c.drawPoints(skia.Canvas.kPoints_PointMode, sp, p)
    p = skia.Paint(AntiAlias=False, Color=rgba(col, a), StrokeWidth=size); p.setStrokeCap(skia.Paint.kSquare_Cap)
    c.drawPoints(skia.Canvas.kPoints_PointMode, sp, p)


def banner(c, x, y, col, label, a=1.0, s=1.0, t=0.0):
    if a <= 0.01: return
    line(c, [(x, y), (x, y - 70 * s)], '#E8E2D0', 3.2 * s, a)
    wv = math.sin(t * 3.2) * 6 * s
    p = skia.Path(); p.moveTo(x, y - 70 * s); p.cubicTo(x + 18 * s, y - (76 * s - wv), x + 34 * s, y - (64 * s + wv), x + 52 * s, y - 68 * s)
    p.lineTo(x + 52 * s, y - 36 * s); p.cubicTo(x + 34 * s, y - (32 * s + wv), x + 18 * s, y - (44 * s - wv), x, y - 40 * s); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.6 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=4 * s))
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
    text(c, label, x + 25 * s, y - 43 * s, 24 * s, INK, 'serifx', a, 'c')


def city_wall(c, x, y, size, col=WEI, a=1.0, name='合肥', glow_a=0.5, t=0.0, gate=None):
    """城：方形城墙 + 垛口 + 城名（宋体）。"""
    if a <= 0.01: return
    s = size
    glow(c, x, y, s * 1.4, col, glow_a * a)
    rrect(c, x - s / 2 - 4, y - s / 2 - 4, s + 8, s + 8, 3, INK, 0.8 * a)
    rrect(c, x - s / 2, y - s / 2, s, s, 2, '#211E1B', 0.88 * a)
    srect(c, x - s / 2, y - s / 2, s, s, col, a, 5)
    srect(c, x - s / 2 + 9, y - s / 2 + 9, s - 18, s - 18, col, 0.35 * a, 2)
    n = max(3, int(s / 22))
    for k in range(n):
        for side in range(4):
            u = (k + 0.5) / n
            if side == 0: bx, by = x - s / 2 + u * s, y - s / 2
            elif side == 1: bx, by = x - s / 2 + u * s, y + s / 2
            elif side == 2: bx, by = x - s / 2, y - s / 2 + u * s
            else: bx, by = x + s / 2, y - s / 2 + u * s
            c.drawRect(skia.Rect.MakeXYWH(bx - 3, by - 3, 6, 6), skia.Paint(Color=rgba(col, a)))
    if gate is not None:
        gx, gy = x + s / 2, y + s * 0.15
        c.drawRect(skia.Rect.MakeXYWH(gx - 5, gy - 14, 10, 28), skia.Paint(Color=rgba('#0A0A0A', a)))
        if gate > 0: glow(c, gx, gy, 30 + 30 * gate, '#FFB25A', 0.6 * gate * a)
    if name:
        text(c, name, x, y + s * 0.16, s * 0.34, PAPER, 'serifx', a, 'c', stroke=5, shadow=6)


def srect(c, x, y, w, h, col, a=1.0, sw=4.0, dash=None):
    p_ = skia.Paint(AntiAlias=True, Color=rgba(col, a), Style=skia.Paint.kStroke_Style, StrokeWidth=sw)
    if dash: p_.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p_)


def label(c, s, x, y, size=30, col=PAPER, a=1.0, anchor='c', fname='serif'):
    text(c, s, x, y, size, col, fname, a, anchor, stroke=5, shadow=6)


def big(c, s, y, size=120, col=PAPER, a=1.0, hl=None, hlcol=GOLD, maxw=960, fname='serifx'):
    """大字（宋体），支持局部高亮。"""
    if a <= 0.01: return
    w = tw(s, fname, size)
    if w > maxw: size *= maxw / w; w = maxw
    x0 = W / 2 - w / 2
    parts = [(s, col)]
    if hl and hl in s:
        i = s.index(hl); parts = [(s[:i], col), (hl, hlcol), (s[i + len(hl):], col)]
    xx = x0
    for ss_, cc in parts:
        if not ss_: continue
        text(c, ss_, xx, y, size, cc, fname, a, 'l', stroke=7, shadow=16)
        xx += tw(ss_, fname, size)


def tagbox(c, s, x, y, col=GOLD, a=1.0, size=26, anchor='l'):
    return G.tag(c, x, y, s, col, a, size, anchor)


# ───────── 原文卡 ─────────
def cite(c, d, a=1.0, y=None, x=56, w=968, qs=44, big_=False, reveal=1.0):
    """深色宋体原文卡：层级徽标 + 出处 + 原文（高亮）+ 白话。y=None 时垂直居中。返回 (y, h)。"""
    if a <= 0.01: return 0, 0
    col = V.LEVEL_COL[d['level']]; pad = 30
    qs = 52 if big_ else qs
    lines = []
    for part in d['q'].split('／'):
        lines += wrap(part.strip(), 'serif', qs, w - pad * 2 - 8); lines.append(None)
    lines = lines[:-1]
    bh = d.get('bh') or ''
    bl = wrap('白话｜' + bh, 'sansm', 32, w - pad * 2 - 8) if bh else []
    note = d.get('note')
    nl = wrap(note, 'sansm', 27, w - pad * 2 - 8) if note else []
    title = d.get('title')
    hq = sum(qs * 1.45 if l is not None else qs * 0.4 for l in lines)
    h = 78 + src_extra(d, w, pad) + (56 if title else 0) + hq + (len(bl) * 46 + 22 if bl else 6) + (len(nl) * 38 + 10 if nl else 0) + 14
    if y is None: y = 760 - h / 2
    yy = y + (1 - ss(a)) * 18
    panel(c, x, yy, w, h, a, r=4, fa=0.88)
    rrect(c, x, yy, 7, h, 2, col, a)
    lt = V.LEVEL_TXT[d['level']]
    bw = tw(lt, 'sans', 23) + 24
    rrect(c, x + pad, yy + 20, bw, 36, 3, col, 0.95 * a)
    text(c, lt, x + pad + 12, yy + 20 + 27, 23, INK, 'sans', a)
    src = d.get('src', ''); extra = 0
    if tw(src, 'serifm', 27) <= w - pad * 2 - bw - 20:
        text(c, src, x + pad + bw + 16, yy + 20 + 28, 27, '#D9D2C2', 'serifm', a)
    else:
        for k, l in enumerate(wrap(src, 'serifm', 26, w - pad * 2 - 8)):
            text(c, l, x + pad + 4, yy + 92 + k * 36, 26, '#D9D2C2', 'serifm', a); extra += 36
    ty = yy + 78 + extra
    if title:
        text(c, title, x + pad + 4, ty + 40, 38, GOLD, 'serifx', a); ty += 56
    ty += qs * 1.0
    # 原文逐字显现 + 高亮
    q_all = d['q'].replace('／', '')
    hl = d.get('hl') or ''
    hs = q_all.find(hl) if hl else -1
    he = hs + len(hl) if hs >= 0 else -1
    shown = int(reveal * len(q_all) + 0.999); idx = 0
    f = G.font('serif', qs)
    for l in lines:
        if l is None: ty += qs * 0.4; continue
        xx = x + pad + 4
        for ch in l:
            if idx >= shown: break
            inhl = hs <= idx < he
            if inhl:
                wch = f.measureText(ch)
                c.drawRect(skia.Rect.MakeXYWH(xx - 1, ty + 10, wch + 2, 4), skia.Paint(Color=rgba(GOLD, 0.85 * a)))
            text(c, ch, xx, ty, qs, GOLD if inhl else ('#F6EBCB' if d['level'] in (V.ZS, V.GJ) else PAPER), 'serif', a)
            xx += f.measureText(ch); idx += 1
        ty += qs * 1.45
    if bl:
        ty += 4
        c.drawLine(x + pad, ty - 26, x + w - pad, ty - 26, skia.Paint(Color=rgba('#FFFFFF', 0.10 * a), StrokeWidth=1))
        for l in bl:
            ty += 4; text(c, l, x + pad + 4, ty + 14, 32, '#E9E1CF', 'sansm', a * clamp(reveal * 1.5 - 0.3)); ty += 42
        ty += 18
    for l in nl:
        text(c, l, x + pad + 4, ty + 8, 27, '#B7B0A2', 'sansm', a); ty += 38
    return y, h


def src_extra(d, w=968, pad=30):
    lt = V.LEVEL_TXT[d['level']]; bw = tw(lt, 'sans', 23) + 24; src = d.get('src', '')
    if tw(src, 'serifm', 27) <= w - pad * 2 - bw - 20: return 0
    return 36 * len(wrap(src, 'serifm', 26, w - pad * 2 - 8))


def cite_from_seg(i):
    prm = S[i]['v'][1]
    lvl, bh = V.CITE.get(i, (V.ZS, ''))
    src = prm.get('src', '').replace('（张喜即张憙）', '')
    return dict(level=lvl, src=src, q=prm['q'].replace('……', '……'), hl=prm.get('hl', ''), bh=bh)


# ───────── 场景上下文 ─────────
class X:
    pass


def cam_hf(lon=117.42, lat=31.72, span=0.95, ay=760):
    return Cam(lon, lat, span, 540, ay)


def backdrop(c, x, dimk=0.62, center=(117.35, 31.78), span=0.9):
    """非地图场景的底：缓慢漂移的合肥区域晕渲，压暗。"""
    u = x.t * 0.004
    cam = Cam(center[0] + math.sin(u * 3) * 0.05, center[1] + math.cos(u * 2) * 0.03, span * (1 + 0.04 * math.sin(u * 5)), 540, 760)
    base(10).draw(c, cam)
    draw_rivers(c, cam, 0.6, 1.0)
    G.dim(c, dimk)
    return cam


# ---------- 开场：上帝视角，吴军压向合肥 ----------
def sc_opener(c, prm, x):
    lt, d = x.lt, x.d
    k = ease(clamp(lt / d))
    cam = Cam.lerp(Cam(117.52, 31.66, 1.25, 540, 760), Cam(117.33, 31.80, 0.62, 540, 760), k)
    base(10).draw(c, cam); draw_rivers(c, cam, 0.9, 1.1)
    G.dim(c, 0.18)
    hx, hy = cam.p(*P['合肥'])
    # 吴军：多路纵队从巢湖方向北上
    routes = [[(117.75, 31.48), (117.62, 31.66), (117.45, 31.78), (117.33, 31.86)],
              [(117.92, 31.55), (117.70, 31.70), (117.48, 31.82), (117.34, 31.88)],
              [(117.50, 31.40), (117.44, 31.60), (117.38, 31.76), (117.31, 31.84)],
              [(118.05, 31.62), (117.80, 31.76), (117.55, 31.88), (117.36, 31.90)]]
    for ri, rt in enumerate(routes):
        sp = G.smooth([cam.p(*q) for q in rt], 2)
        prog = 0.35 + 0.55 * k
        arrow(c, sp, WU, prog, w=18, a=0.85, head=50)
        for b in range(16):
            u = prog - b * 0.045
            if u < 0.02: continue
            bx, by, ang = G.along(sp, u)
            for sd in (-1, 1):
                ox, oy = -math.sin(ang) * 26 * sd, math.cos(ang) * 26 * sd
                block(c, bx + ox, by + oy, ang + math.pi / 2, 4, 5, WU_L if b == 0 else WU, 0.95, gap=7.5, size=5, seed=ri * 40 + b * 2 + (sd > 0))
            if b % 3 == 0: dust(c, bx, by, x.t, 0.8, 4, 30, seed=ri * 7 + b, size=20)
    city_wall(c, hx, hy, 110, WEI, 1, '合肥', 0.6, x.t)
    pulse(c, hx, hy, x.t, WEI_L, 60, 170, 1.6, 0.8)
    wind(c, x.t, 1.0)
    for q in ('巢湖', '居巢'):
        qx, qy = cam.p(*P[q]); label(c, q, qx, qy, 34, '#BFD7E2' if q == '巢湖' else PAPER, 0.85)
    # 钩子：密教 + 大字
    a = ss(ramp(lt, 1.2, 2.0))
    slip(c, hx + 250, hy - 60, 0.36, a, x.t)
    big(c, '敌人来了，才准拆开', 470, 96, PAPER, a, '才准拆开')
    text(c, '示意 · 吴军进军路线不按比例', 60, 1250, 24, '#B7B0A2', 'sansm', 0.8)


def slip(c, x, y, s, a=1.0, t=0.0, label_reveal=1.0, opened=0.0):
    """密教：一束木简，绳捆 + 封泥，侧有题签「贼至乃发」。"""
    if a <= 0.01: return
    c.save(); c.translate(x, y); c.scale(s, s)
    glow(c, 0, 0, 420, AMBER, 0.28 * a)
    for k in range(7):
        xx = -150 + k * 50
        sh = skia.GradientShader.MakeLinear([(xx, 0), (xx + 46, 0)], [rgba('#B79A66', a), rgba('#8C7246', a)])
        c.drawRect(skia.Rect.MakeXYWH(xx, -300, 46, 600), skia.Paint(AntiAlias=True, Shader=sh))
        c.drawLine(xx + 46, -300, xx + 46, 300, skia.Paint(Color=rgba('#4A3A22', 0.8 * a), StrokeWidth=2))
    for yy in (-170, 170):
        c.drawRect(skia.Rect.MakeXYWH(-160, yy - 9, 370, 18), skia.Paint(Color=rgba('#5A4026', a)))
    c.drawRect(skia.Rect.MakeXYWH(-160, -9, 370, 18), skia.Paint(Color=rgba('#5A4026', a)))
    rrect(c, -48, -58, 96, 116, 10, '#4A2C20', a)
    srect(c, -48, -58, 96, 116, '#8A5A3A', a, 3)
    text(c, '封', 0, 24, 62, '#D9B48A', 'serifx', a, 'c')
    # 题签
    rrect(c, 222, -250, 64, 300, 3, '#E9DFC6', a)
    G.dim  # noqa
    for i, ch in enumerate('贼至乃发'):
        r = clamp(label_reveal * 4 - i)
        if r > 0: text(c, ch, 254, -250 + 64 + i * 66, 56, '#1A1410', 'serifx', a * r, 'c')
    c.restore()


def sc_letter(c, prm, x):
    mode = prm.get('mode', 'closed'); lt, d, j = x.lt, x.d, x.j
    backdrop(c, x, 0.55)
    u = lt / max(d, 0.1)
    if mode == 'closed':
        s = 1.05 + 0.06 * u + (0.12 if j % 2 else 0)
        slip(c, 470, 720 + 8 * math.sin(x.t), s, 1, x.t)
        embers(c, 470, 1080, x.t, 0.5, 8, 120, 3)
        if prm.get('cap'):
            big(c, prm['cap'], 1180, 80, GOLD, ss(ramp(lt, 0.3, 0.9)))
    elif mode == 'edge':
        c.save(); c.translate(540, 760); c.rotate(-3 + 2 * u)
        slip(c, -480, 60, 2.4 + 0.15 * u, 1, x.t, label_reveal=ease(clamp(lt / 1.4)))
        c.restore()
        if prm.get('cap'): big(c, prm['cap'], 1180, 80, GOLD, ss(ramp(lt, 0.3, 0.9)))
    elif mode in ('open', 'blank'):
        slips_open(c, x, prm, mode)
    elif mode == 'fake':
        fake_letter(c, x, prm)
    elif mode == 'final':
        s = 1.25 + 0.1 * u
        slip(c, 480, 700, s, 1, x.t, opened=0)
        embers(c, 480, 1100, x.t, 0.6, 10, 160, 5)
        big(c, '贼 至 乃 发', 1210, 104, GOLD, ss(ramp(lt, 0.8, 1.8)))


JIAO = [('若孙权至者', PAPER), ('张李将军出战', WEI_L), ('乐将军守护军', LE), ('勿得与战', LE)]


def slips_open(c, x, prm, mode):
    lt, d, j = x.lt, x.d, x.j
    hlseq = prm.get('hlseq')
    rev = 1.0 if (mode == 'blank' or hlseq or not x.first_seg_shot) else ease(clamp(lt / max(1.0, d * 0.6)))
    s = 1.0 if j % 2 == 0 else 1.16
    n = 4 + (2 if mode == 'blank' else 0)
    sw = 120 * s; x0 = 540 + n * sw / 2 - 20; y0 = 330
    hl = None
    if hlseq: hl = [1] if lt < d * 0.5 else [2, 3]
    for k in range(n):
        xx = x0 - (k + 1) * sw
        sh = skia.GradientShader.MakeLinear([(xx, 0), (xx + sw, 0)], [rgba('#C4A774'), rgba('#9A7D4C')])
        c.drawRect(skia.Rect.MakeXYWH(xx + 4, y0, sw - 8, 760 * s), skia.Paint(AntiAlias=True, Shader=sh))
        c.drawRect(skia.Rect.MakeXYWH(xx + 4, y0 + 70 * s, sw - 8, 8), skia.Paint(Color=rgba('#5A4026', 0.8)))
        c.drawRect(skia.Rect.MakeXYWH(xx + 4, y0 + 680 * s, sw - 8, 8), skia.Paint(Color=rgba('#5A4026', 0.8)))
        if k < 4:
            s_, col = JIAO[k]
            r = clamp(rev * 4 - k)
            dimk = 1.0 if hl is None or k in hl else 0.3
            if hl and k in hl:
                srect(c, xx, y0 - 6, sw, 760 * s + 12, GOLD, 1, 5)
                glow(c, xx + sw / 2, y0 + 380 * s, 240, GOLD, 0.25)
            fs = (70 if len(s_) <= 5 else 64) * s
            for i2, ch in enumerate(s_):
                rr_ = clamp(r * len(s_) - i2)
                if rr_ <= 0: break
                cc = '#1A1410' if k == 0 else ('#8A1A10' if k == 1 else '#5A4010')
                text(c, ch, xx + sw / 2, y0 + 120 * s + i2 * fs * 1.04 + fs * 0.8, fs, cc, 'serifx', dimk * rr_, 'c') if not prm.get('blur') else circle(c, xx + sw / 2, y0 + 120 * s + i2 * fs * 1.04 + fs * 0.4, fs * 0.35, '#3A2A1A', 0.5 * rr_, blur=8)
        else:
            pp = skia.Paint(AntiAlias=True, Color=rgba(WEI_L, 0.9), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
            pp.setPathEffect(skia.DashPathEffect.Make([16, 10], 0))
            c.drawRect(skia.Rect.MakeXYWH(xx + 14, y0 + 20, sw - 28, 720 * s), pp)
            text(c, '？', xx + sw / 2, y0 + 400 * s, 90, WEI_L, 'serifx', 1, 'c')
    # 分工箭头：信上的分工弹出（出战红、留守金）
    if mode == 'open' and not prm.get('blur') and not hlseq:
        f = ease(ramp(lt, d * 0.55, d * 0.85))
        if f > 0:
            cx2 = x0 - 2 * sw + sw / 2
            for dx, nm in [(-250, '张辽'), (-40, '李典')]:
                arrow(c, [(cx2, y0 + 700 * s), (cx2 + dx * 0.4, y0 + 800 * s), (cx2 + dx, y0 + 880 * s)], WEI, f, w=16, head=46)
                label(c, nm + ' · 出战', cx2 + dx, y0 + 940 * s, 38, WEI_L, f)
            cx3 = x0 - 3 * sw + sw / 2
            G.circle(c, cx3 + 120, y0 + 880 * s, 34 * f, LE, 0.9 * f, stroke=6)
            label(c, '乐进 · 留守', cx3 + 150, y0 + 950 * s, 38, LE, f)
    if mode == 'blank':
        big(c, '带多少人？怎么打？', 280, 64, GOLD, ss(ramp(lt, 0.4, 1.0)))


def fake_letter(c, x, prm):
    lt, j = x.lt, x.j
    c.save(); c.translate(540, 720); c.rotate(-3 + math.sin(x.t * 0.6))
    s = 1.0 + (0.14 if j % 2 else 0); c.scale(s, s)
    rrect(c, -220, -400, 440, 800, 4, '#000000', 0.5, blur=30)
    sh = skia.GradientShader.MakeLinear([(-220, 0), (220, 0)], [rgba('#C9B387'), rgba('#A88F62')])
    c.drawRect(skia.Rect.MakeXYWH(-220, -400, 440, 800), skia.Paint(AntiAlias=True, Shader=sh))
    for i, ch in enumerate('步骑四万'):
        text(c, ch, 80, -300 + i * 96 + 70, 84, '#1A1410', 'serifx', clamp(lt * 3 - i * 0.5), 'c')
    for i, ch in enumerate('已到雩娄'):
        text(c, ch, -70, -300 + i * 96 + 70, 84, '#1A1410', 'serifx', clamp(lt * 3 - 2 - i * 0.5), 'c')
    a = ss(ramp(lt, 1.6, 2.0))
    if a > 0:
        c.save(); c.translate(110, 230); c.rotate(-12); c.scale(1.6 - 0.6 * a, 1.6 - 0.6 * a)
        srect(c, -90, -90, 180, 180, '#A0261A', 0.9 * a, 10)
        text(c, '伪', 0, 48, 130, '#A0261A', 'serifx', 0.92 * a, 'c')
        c.restore()
    c.restore()
    if prm.get('cap'): big(c, prm['cap'], 1210, 70, GOLD, ss(ramp(lt, 0.4, 1.0)))


def tactical_cam(lt, d, k0=0.0, k1=1.0, z0=0.24, z1=0.16, center=(117.292, 31.866)):
    k = ease(clamp(lerp(k0, k1, lt / max(d, 0.1))))
    sp = math.exp(lerp(math.log(z0), math.log(z1), k))
    return Cam(center[0], center[1], sp, 540, 760)


def tactical_base(c, cam, dimk=0.25):
    base(12).draw(c, cam)
    G.dim(c, dimk)


# ---------- 沙盘公共 ----------
def stage_bg(c, x, zoom=1.0, dimk=0.3, ctr=(117.296, 31.862), span=0.16):
    cam = Cam(ctr[0] + 0.003 * math.sin(x.t * 0.05), ctr[1] + 0.002 * math.cos(x.t * 0.04), span / zoom, 540, 760)
    base(12).draw(c, cam); G.dim(c, dimk)


def push(c, zoom, fx, fy):
    c.translate(540, 760); c.scale(zoom, zoom); c.translate(-fx, -fy)


def river_s(c, pts, t, w=70, a=1.0):
    sp = G.smooth(pts, 3)
    line(c, sp, '#0E1A22', w + 14, 0.9 * a)
    line(c, sp, '#24465A', w, a)
    line(c, sp, WATER, w * 0.35, 0.35 * a, blur=6)
    L = G.plen(sp)
    for k in range(10):
        u = ((t * 0.04) + k / 10) % 1.0
        x1, y1, ang = G.along(sp, u)
        line(c, [(x1 - 18 * math.cos(ang), y1 - 18 * math.sin(ang)), (x1 + 18 * math.cos(ang), y1 + 18 * math.sin(ang))], '#BFE9FF', 2, 0.35 * a)


def ring_blocks(c, cx, cy, n, r0, r1, t, p, col=WU, seed=5, src=(900, 1500), dl_max=0.4, fires=True, ellip=0.85):
    rr = random.Random(seed)
    for k in range(n):
        ang = k / n * 2 * math.pi + rr.uniform(-0.06, 0.06); rad = rr.uniform(r0, r1)
        tx, ty = cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * ellip
        sx, sy = src[0] + rr.uniform(-260, 260), src[1] + rr.uniform(-120, 200)
        dl = rr.uniform(0, dl_max); q = ease(clamp((p - dl) / (1 - dl + 1e-6)))
        bx, by = lerp(sx, tx, q), lerp(sy, ty, q)
        ang2 = math.atan2(ty - sy, tx - sx) if q < 0.98 else ang + math.pi / 2
        block(c, bx, by, ang2 + math.pi / 2, 4, 6, col, 0.95, gap=8.5, size=5.6, seed=k)
        if q < 0.95: dust(c, bx, by, t, 0.8, 4, 26, seed=k, size=22)
        if fires and k % 7 == 0 and q > 0.9: fire(c, bx + 26, by + 14, t, 0.8, 0.9, k)


# ---------- 围城 ----------
def sc_siege(c, prm, x):
    p0, p1 = prm.get('p', (0, 1)); lt, d = x.lt, x.d
    p = lerp(p0, p1, ss(clamp(lt / max(0.1, d * 0.9))))
    z = lerp(1.0, 1.12, ease(clamp(lt / max(1, d)))) * (1.25 if x.j % 2 else 1)
    stage_bg(c, x, z, 0.3)
    c.save(); push(c, z, 540, 740)
    river_s(c, [(-80, 1150), (300, 1110), (620, 1080), (900, 1020), (1180, 980)], x.t, 60, 0.9)
    city_wall(c, 540, 740, 270, WEI, 1, '合肥', 0.55, x.t)
    ring_blocks(c, 540, 740, 64, 230, 430, x.t, p, src=(860, 1560))
    c.restore()
    if prm.get('days'):
        n = int(clamp(lt / max(0.5, d * 0.85)) * 10) + 1
        big(c, f'围城 · 第{"一二三四五六七八九十"[min(n, 10) - 1] if n <= 10 else "十余"}日', 300, 76, GOLD, 1)
        for k in range(6):
            ph = (x.t * 0.7 + k * 0.17) % 1; ang = k * 1.05 + 0.4
            r0 = lerp(400, 150, min(ph, 0.6) / 0.6) + (0 if ph < 0.6 else (ph - 0.6) * 500)
            arrow(c, [(540 + math.cos(ang) * 420, 740 + math.sin(ang) * 380), (540 + math.cos(ang) * r0, 740 + math.sin(ang) * r0 * 0.9)],
                  WU_L, 1, w=8, a=0.9 * (1 - ph), head=24, glow=False)
    else:
        big(c, '号称十万', 300, 100, WU_L, ss(ramp(p, 0.5, 0.8)))
    wind(c, x.t, 0.9)


# ---------- 兵力 ----------
def sc_dots(c, prm, x):
    mode = prm['mode']; lt, d, j = x.lt, x.d, x.j
    z = 1.0 + 0.05 * clamp(lt / max(1, d)) + (0.12 if j % 2 else 0)
    stage_bg(c, x, z, 0.4)
    c.save(); push(c, z, 540, 760)
    city_wall(c, 540, 760, 360, WEI, 1, '', 0.35, x.t)
    pts, gold_pts = [], []
    for k in range(70):
        gx, gy = k % 10, k // 10
        px, py = 540 - 130 + gx * 29, 760 - 95 + gy * 30
        if mode == '800' and k in (33, 34, 35, 36, 43, 44, 45, 46):
            f = ease(ramp(lt, 0.3, 1.3)); gold_pts.append((px + f * 330, py))
        else: pts.append((px, py))
    dots(c, pts, WEI if mode != '800' else '#7A3A30', 1, 12)
    if gold_pts:
        for gx_, gy_ in gold_pts: glow(c, gx_, gy_, 30, GOLD, 0.5)
        dots(c, gold_pts, GOLD, 1, 14)
        arrow(c, [(720, 750), (900, 740)], WEI, ease(ramp(lt, 0.3, 1.3)), w=18, head=44)
    if mode in ('vs', 'vs2'):
        n = int(1000 * (ease(ramp(lt, 0, 1.6)) if x.first_seg_shot else 1)); wp = []
        for k in range(n):
            gx, gy = k % 40, k // 40
            ang = gx / 40 * 2 * math.pi + gy * 0.07; rad = 250 + gy * 9
            wp.append((540 + math.cos(ang) * rad, 760 + math.sin(ang) * rad * 1.05))
        dots(c, wp, WU, 0.95, 7)
    c.restore()
    if mode in ('vs', 'vs2'):
        big(c, '七千余 对 号称十万', 290, 74, PAPER, ss(ramp(lt, 0.6, 1.1)), '号称十万', WU_L)
        if mode == 'vs2': big(c, '换成你，怎么办？', 1210, 72, GOLD, ss(ramp(lt, 1.0, 1.5)))
    else:
        big(c, '七千余人' if mode == '7000' else '站出来八百', 300, 96, WEI_L if mode == '7000' else GOLD, ss(ramp(lt, 0.4, 0.9)))
        text(c, '每点 ≈ 100 人（示意）', 540, 1240, 28, '#B7B0A2', 'sansm', 0.9, 'c')


def roles_sandbox(c, prm, x, i):
    """沙盘：信上分工 → 张辽、李典出城（红箭头），乐进守城（金）。"""
    lt, d = x.lt, x.d
    z = 1.0 + 0.05 * clamp(lt / max(1, d))
    stage_bg(c, x, z, 0.32)
    c.save(); push(c, z, 540, 760)
    city_wall(c, 300, 800, 300, WEI, 1, '', 0.5, x.t, gate=1)
    rr = random.Random(9)
    for k in range(30):
        bx, by = rr.uniform(720, 1040), rr.uniform(420, 1150)
        block(c, bx, by, rr.uniform(-0.3, 0.3), 4, 6, WU, 0.75, gap=8.5, size=5.6, seed=k)
    f = ease(ramp(lt, 0.4, 1.8))
    for dy, nm in [(-130, '张辽'), (130, '李典')]:
        pts = [(470, 800 + dy * 0.2), (600, 800 + dy * 0.8), (700, 800 + dy * 1.3)]
        arrow(c, pts, WEI, f, w=26, head=72)
        ex, ey, _ = G.along(pts, f)
        block(c, ex - 40, ey, 0, 4, 5, WEI_L, f, gap=9, size=6.5, seed=dy)
        label(c, nm + ' · 出战', ex - 40, ey - 60, 44, WEI_L, f, fname='serifx')
        dust(c, ex - 40, ey, x.t, f, 8, 50, seed=dy, size=26)
    a2 = ease(ramp(lt, 1.0, 1.8))
    circle(c, 300, 800, 120, LE, 0.9 * a2, stroke=8)
    label(c, '乐进 · 守城', 300, 815, 46, LE, a2, fname='serifx')
    c.restore()
    if prm.get('letter'): slip(c, 160, 360, 0.3, 1, x.t)
    big(c, '信上分工，事先定死', 300, 66, GOLD, ss(ramp(lt, 1.2, 1.8)))


# ---------- 出城逆击：沙盘 ----------
rb = random.Random(11)
CAMP_B = []
while len(CAMP_B) < 76:
    ux, uy = rb.uniform(-1, 1), rb.uniform(-1, 1)
    if ux * ux + uy * uy > 1: continue
    px, py = 720 + ux * 340, 640 + uy * 420
    if px < 470 and py > 820: continue
    CAMP_B.append((px, py, rb.uniform(-0.35, 0.35)))
RED = []
for k in range(120):
    row = int((math.sqrt(8 * k + 1) - 1) / 2); col = k - row * (row + 1) // 2
    RED.append(((col - row / 2) * 12.5, row * 11.5))
CITY_B, CS_B = (270, 960), 260
GATE_B = (418, 920)
BAN0 = (700, 600)
HILL_B = (800, 455)
TGT = (676, 672)


def battle_rc(p):
    if p < 1: return GATE_B
    if p < 2: q = ease(p - 1); return (lerp(GATE_B[0], TGT[0], q), lerp(GATE_B[1], TGT[1], q))
    if p < 5.5: return TGT
    if p < 6: q = ease((p - 5.5) / 0.5); return (TGT[0] - 70 * q, TGT[1] + 50 * q)
    q = ease(p - 6); return (lerp(TGT[0] - 70, GATE_B[0], q), lerp(TGT[1] + 50, GATE_B[1], q))


def sc_battle(c, prm, x):
    p0, p1 = prm['p']; lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.92)))
    rc = battle_rc(p)
    if prm.get('zoomout'):
        k = ease(clamp(lt / 1.8)); z = lerp(1.6, 0.92, k); f = (lerp(rc[0], 560, k), lerp(rc[1], 740, k))
    else:
        z = lerp(1.0, 1.22, ease(clamp(p / 6.6)))
        k = clamp(p / 3)
        f = (lerp(540, rc[0], 0.5 * k), lerp(760, rc[1], 0.5 * k))
        if j % 2 == 1: z *= 1.3; f = (lerp(f[0], rc[0], 0.7), lerp(f[1], rc[1], 0.7))
    stage_bg(c, x, z, 0.3)
    if prm.get('sky', 'dawn') != 'noon' and p < 6: dawn(c, 1.0 - p / 6.5)
    c.save(); push(c, z, f[0], f[1])
    for k2 in range(5):
        r = 170 - k2 * 32
        c.drawOval(skia.Rect.MakeXYWH(HILL_B[0] - r, HILL_B[1] - r * 0.55, 2 * r, 1.1 * r), skia.Paint(AntiAlias=True, Color=rgba('#B39A6A', 0.10 + 0.06 * k2)))
    label(c, '高冢', HILL_B[0] + 150, HILL_B[1] - 40, 36, '#E3C88E', ss(ramp(p, 2.1, 2.5)), fname='serifx')
    city_wall(c, CITY_B[0], CITY_B[1], CS_B, WEI, 1, '合肥', 0.5, x.t, gate=ss(ramp(p, 0.3, 0.9)))
    sq = BAN0 if p < 2 else (lerp(BAN0[0], HILL_B[0], ease((p - 2) / 0.8)), lerp(BAN0[1], HILL_B[1] + 20, ease((p - 2) / 0.8)))
    ring = ease(clamp(p - 3)); open_ = ease(clamp((p - 5.5) / 0.5)) * (1 - ease(clamp(p - 6.3))); recoil = ease(clamp(p - 6))
    for k2, (bx, by, ang) in enumerate(CAMP_B):
        px, py = bx, by
        dx, dy = px - rc[0], py - rc[1]; dist = math.hypot(dx, dy) + 1e-3
        if 1 <= p < 3.2 and dist < 170:
            push_ = (170 - dist) * 0.95; px += dx / dist * push_; py += dy / dist * push_
        if 2 <= p < 3.2 and k2 % 3 == 0:
            px += 12 * math.sin(x.t * 6 + k2); py += 12 * math.cos(x.t * 5 + k2)
        if k2 % 2 == 0 and ring > 0:
            a_ = k2 * 0.165; rad = 120 + (k2 % 4) * 30
            qx, qy = rc[0] + math.cos(a_) * rad, rc[1] + math.sin(a_) * rad
            if open_ > 0 and math.cos(a_) < -0.1 and math.sin(a_) > -0.3: qx -= 140 * open_; qy += 60 * open_
            px, py = lerp(px, qx, ring), lerp(py, qy, ring); ang = a_ + math.pi / 2
        if recoil > 0: px += 220 * recoil * (0.5 + (k2 % 5) / 10); py -= 120 * recoil * (0.5 + (k2 % 3) / 6)
        block(c, px, py, ang, 4, 6, WU, 0.95 * (1 - 0.35 * recoil), gap=8.5, size=5.6, seed=k2)
        if k2 % 8 == 0 and p < 1.4: fire(c, px + 24, py + 12, x.t, 0.85, 0.9, k2)
    banner(c, sq[0], sq[1], WU, '孙', 1, 1.1, x.t)
    if 2.0 <= p < 4.2: label(c, '孙权', sq[0] - 60, sq[1] - 10, 36, WU_L, fname='serifx')
    vis = ss(ramp(p, 0.6, 1.0)); out = ease(clamp(p - 4)); back = ease(clamp(p - 5))
    rp = []
    ang0 = math.atan2(TGT[1] - GATE_B[1], TGT[0] - GATE_B[0]) - math.pi / 2
    ca, sa = math.cos(ang0), math.sin(ang0)
    for k2, (ox, oy) in enumerate(RED):
        ux, uy = ox * ca - (-oy) * sa, ox * sa + (-oy) * ca
        if 3 <= p < 6:
            a_ = k2 * 0.61; r_ = 6 + k2 * 0.55; ux, uy = math.cos(a_) * r_, math.sin(a_) * r_
        px, py = rc[0] + ux, rc[1] + uy
        if k2 < 22 and 4 <= p < 5.6: px -= 150 * out * (1 - back); py += 110 * out * (1 - back)
        rp.append((px, py))
    dots(c, rp, WEI_L, vis, 6.4)
    if vis > 0:
        lx, ly = rc[0], rc[1] - 26
        if 4 <= p < 5.6: lx -= 150 * out * (1 - back); ly += 110 * out * (1 - back)
        glow(c, lx, ly, 50, '#FFD0A0', vis); circle(c, lx, ly, 10, '#FFE2C0', vis)
        label(c, '张辽', lx - 30, ly - 36, 38, WEI_L, vis, 'r', fname='serifx')
    if 0.8 <= p < 2.3:
        f2 = ease(ramp(p, 0.8, 1.9))
        arrow(c, [GATE_B, (lerp(GATE_B[0], TGT[0], 0.5) - 10, lerp(GATE_B[1], TGT[1], 0.5) + 20), TGT], WEI, f2, w=34, head=88)
        dust(c, rc[0], rc[1] + 20, x.t, 1, 20, 80, 3, size=34)
    if 3.3 <= p < 4.3:
        pp = skia.Paint(AntiAlias=True, Color=rgba(WU_L, 0.85), Style=skia.Paint.kStroke_Style, StrokeWidth=7)
        pp.setPathEffect(skia.DashPathEffect.Make([20, 12], -x.t * 80))
        for r in (150, 215): c.drawCircle(rc[0], rc[1], r * ease(ramp(p, 3.3, 4.0)), pp)
    if 4.0 <= p < 5.0:
        arrow(c, [rc, (rc[0] - 150, rc[1] + 110)], WEI, ease(ramp(p, 4.0, 4.7)), w=28, head=76)
    if 5.0 <= p < 6.0:
        arrow(c, [(rc[0] - 150, rc[1] + 110), (rc[0] - 10, rc[1] - 10)], WEI, ease(ramp(p, 5.0, 5.5)), w=28, head=76)
    if p >= 6.0:
        arrow(c, [(TGT[0] + 40, TGT[1] - 30), (TGT[0] + 330, TGT[1] - 220)], WU_L, ease(ramp(p, 6.0, 6.5)), w=18, a=0.85, head=50, dash=(22, 14))
    if p < 2.3: dust(c, GATE_B[0], GATE_B[1], x.t, vis * 0.8, 12, 70, 7, size=30)
    if 3.0 <= p < 6.0: dust(c, rc[0], rc[1], x.t, 0.9, 14, 110, 11, size=34)
    c.restore()
    if p >= 6.0: big(c, '天亮 → 日中', 300, 72, GOLD, ss(ramp(lt, 0, 0.6)))
    if p >= 6.0 and prm.get('sky') == 'noon':
        glow(c, 920, 330, 160, '#FFE7A0', 0.35); circle(c, 920, 330, 40, '#FFF1C9', 0.95)
    wind(c, x.t, 1.0)
    if prm.get('word'):
        a = eout(ramp(lt, 0.2, 0.55)); scl = 1.2 - 0.2 * a
        c.save(); c.translate(540, 1205); c.scale(scl, scl); c.translate(-540, -1205)
        big(c, prm['word'], 1205, 100, GOLD, a)
        c.restore()


# ---------- 撤军：津北 ----------
RIV_R = [(-80, 900), (250, 870), (600, 822), (900, 760), (1180, 720)]
BRIDGE_R = (600, 822)
ROAD_R = [(520, 560), (575, 700), (600, 822), (630, 950), (740, 1090), (880, 1230), (1040, 1400), (1200, 1560)]
CITY_R, CS_R = (250, 420), 240
rr2 = random.Random(21)
COLB = [rr2.random() for _ in range(62)]


def sc_retreat(c, prm, x):
    p0, p1 = prm['p']; lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.92)))
    if prm.get('wall'): z, f = 1.0, (540, 760)
    elif p > 3.4:
        k = ease(clamp((p - 3.4) / 0.8)); z = lerp(1.15, 1.7, k); f = (lerp(560, BRIDGE_R[0], k), lerp(760, BRIDGE_R[1] + 20, k))
    else:
        z = lerp(1.0, 1.12, clamp(lt / max(1, d))) * (1.22 if j % 2 else 1); f = (540, 760) if j % 2 == 0 else (560, 720)
    stage_bg(c, x, z, 0.3, (117.30, 31.85))
    c.save(); push(c, z, f[0], f[1])
    river_s(c, RIV_R, x.t, 76)
    city_wall(c, CITY_R[0], CITY_R[1], CS_R, WEI, 1, '合肥', 0.45, x.t, gate=ss(ramp(p, 1.8, 2.2)))
    ancient_bridge(c, BRIDGE_R[0], BRIDGE_R[1], 2.1, 1, ang=-1.45)
    gap = ss(ramp(p, 3.6, 4.0))
    if gap > 0:
        srect(c, BRIDGE_R[0] - 30, BRIDGE_R[1] + 22, 60, 40, GOLD, gap, 3, dash=(8, 6))
        label(c, '桥南丈余无版', BRIDGE_R[0] + 170, BRIDGE_R[1] + 70, 36, GOLD, gap, fname='serifx')
    label(c, '逍遥津', BRIDGE_R[0] + 160, BRIDGE_R[1] - 20, 40, '#BFD7E2', 0.95, fname='serifx')
    label(c, '津北', BRIDGE_R[0] - 170, BRIDGE_R[1] - 70, 36, PAPER, 0.9, fname='serifx')
    label(c, '津南', BRIDGE_R[0] - 150, BRIDGE_R[1] + 110, 36, PAPER, 0.9, fname='serifx')
    road = G.smooth(ROAD_R, 3)
    form = ease(clamp(p)); adv = 0.25 + 0.6 * clamp(p / 2)
    for k, r in enumerate(COLB):
        rear = k < 6
        s_ = (0.03 + 0.025 * k) if rear else clamp(0.2 + r * 0.5 + 0.3 * adv)
        lx, ly, ang = G.along(road, s_)
        a0 = k / 62 * 2 * math.pi
        rx, ry = CITY_R[0] + math.cos(a0) * 330, CITY_R[1] + math.sin(a0) * 290
        bx, by = lerp(rx, lx, form), lerp(ry, ly, form)
        if rear and p > 2.6:
            q = ease(clamp((p - 2.6) / 1.2)); bx, by = lerp(bx, BRIDGE_R[0] - 20, q * 0.45), lerp(by, BRIDGE_R[1] - 60, q * 0.45)
        block(c, bx, by, ang + math.pi / 2, 3, 5, WU, 0.95, gap=8.5, size=5.6, seed=k)
        if not rear and k % 4 == 0 and p < 2: dust(c, bx, by, x.t, 0.7, 3, 20, seed=k, size=20)
    if prm.get('wall'):
        a = ss(ramp(lt, 0, 0.5))
        pp = skia.Paint(AntiAlias=True, Color=rgba(WU_L, 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=5)
        pp.setPathEffect(skia.DashPathEffect.Make([12, 10], 0)); c.drawOval(skia.Rect.MakeXYWH(CITY_R[0] - 330, CITY_R[1] - 290, 660, 580), pp)
    if p < 3.8: sq = G.along(road, 0.1)[:2]
    elif p < 4.5:
        q = ease((p - 3.8) / 0.7); sq = (lerp(BRIDGE_R[0] - 10, BRIDGE_R[0] + 15, q), lerp(BRIDGE_R[1] - 60, BRIDGE_R[1] + 110, q))
    else: sq = (BRIDGE_R[0] + 15, BRIDGE_R[1] + 110)
    jump = math.sin(math.pi * clamp(((p - 3.8) / 0.7 - 0.35) / 0.4)) * 34 if 3.8 <= p < 4.5 else 0
    banner(c, sq[0], sq[1] - jump, WU, '孙', 1, 1.0, x.t)
    if 2.0 <= p < 4.2: label(c, '孙权', sq[0] + 80, sq[1] - 30, 36, WU_L, fname='serifx')
    if p > 2.0:
        fs = ease(clamp(p - 2.0))
        tgt = (sq[0] - 40, sq[1] - 30); src = (CITY_R[0] + CS_R / 2 + 10, CITY_R[1] + 40)
        pts = [src, (lerp(src[0], tgt[0], 0.5) - 10, lerp(src[1], tgt[1], 0.5) - 40), tgt]
        arrow(c, pts, WEI, fs, w=36, head=94)
        cx2, cy2, _ = G.along(pts, fs)
        rp = [(cx2 - 50 + math.cos(k * 0.9) * (14 + (k % 6) * 10), cy2 - 20 + math.sin(k * 0.9) * (14 + (k % 6) * 10) * 0.7) for k in range(70)]
        dots(c, rp, WEI_L, 1, 6.2)
        dust(c, cx2, cy2, x.t, fs, 18, 80, 9, size=36)
    if 2.9 < p < 4.2:
        a = ss(ramp(p, 2.9, 3.2)); lx, ly = sq[0] - 90, sq[1] - 60
        block(c, lx, ly, 0.4, 4, 6, WU_L, a, gap=8.5, size=6)
        label(c, '凌统 · 三百人', lx - 40, ly - 50, 34, WU_L, a, 'r', fname='serifx')
    if p > 4.2:
        a = ss(ramp(p, 4.2, 4.6)); hxq, hyq = BRIDGE_R[0] + 110, BRIDGE_R[1] + 230
        for m in range(3): block(c, hxq + m * 70 - 70, hyq + (m % 2) * 30, -0.3, 5, 6, '#5FC8CF', a, gap=8.5, size=6, seed=m)
        label(c, '贺齐 · 三千人', hxq, hyq + 100, 36, WU_L, a, fname='serifx')
    c.restore()
    if prm.get('wall'):
        big(c, '围城时是一堵墙', 290, 72, WU_L, ss(ramp(lt, 0, 0.5))); big(c, '撤军时成了一根线', 1205, 72, WU_L, ss(ramp(lt, 1.0, 1.5)))
    if 2.05 < p < 3.2: big(c, '奄至', 1205, 110, WEI_L, eout(ramp(p, 2.05, 2.4)))
    if p < 0.9 and p0 < 0.1: big(c, '撤军', 1205, 100, WU_L, eout(ramp(lt, 0.3, 0.7)))
    wind(c, x.t, 0.9)


# ---------- 城门 ----------
def sc_gate(c, prm, x):
    mode = prm.get('mode'); lt, d = x.lt, x.d
    night = mode == 'night'
    backdrop(c, x, 0.7 if night else 0.6)
    z = 1.0 + 0.04 * lt / max(1, d) + (0.1 if x.j % 2 else 0)
    c.save(); c.translate(540, 640); c.scale(z, z)
    wc = '#2E2A27'
    c.drawRect(skia.Rect.MakeXYWH(-560, -40, 1120, 420), skia.Paint(Color=rgba(wc)))
    for i in range(16): c.drawRect(skia.Rect.MakeXYWH(-560 + i * 72, -82, 44, 46), skia.Paint(Color=rgba(wc)))
    for r in range(8):
        for q in range(16):
            c.drawRect(skia.Rect.MakeXYWH(-560 + q * 72 + (r % 2) * 36, -30 + r * 52, 68, 48), skia.Paint(Color=rgba('#3A3531', 0.5)))
    arch = skia.Path(); arch.addArc(skia.Rect.MakeXYWH(-150, 40, 300, 300), 180, 180)
    c.drawPath(arch, skia.Paint(AntiAlias=True, Color=rgba('#070707')))
    c.drawRect(skia.Rect.MakeXYWH(-150, 190, 300, 190), skia.Paint(Color=rgba('#070707')))
    o = {'close': 1 - ease(clamp(lt / 1.3)), 'out': ease(clamp(lt / 0.8)), 'two': ease(clamp(lt / 0.8))}.get(mode, 0)
    if o > 0.01: glow(c, 0, 250, 260 * o, '#FF9A4A', 0.7 * o)
    dw = 150 * (1 - o)
    for sgn in (-1, 1):
        x0 = -150 if sgn < 0 else 150 - dw
        c.drawRect(skia.Rect.MakeXYWH(x0, 90, dw, 290), skia.Paint(Color=rgba('#5A2A18')))
        for k in range(5):
            for m in range(3):
                if dw > 30: c.drawCircle(x0 + dw * (0.25 + 0.25 * m), 130 + k * 55, 6, skia.Paint(AntiAlias=True, Color=rgba('#B8904A', 0.9)))
    for tx in (-330, 330):
        fire(c, tx, 40, x.t, 1, 1.2, tx)
    if mode == 'close':
        b = ease(ramp(lt, 1.2, 1.6))
        if b > 0: c.drawRect(skia.Rect.MakeXYWH(-180, 230 - 220 * (1 - b), 360, 28), skia.Paint(Color=rgba('#8A6A3A', b)))
        big_local(c, '关门死守？', -300, 92, PAPER, ss(ramp(lt, 0.5, 1.0)))
    if mode == 'out':
        f = ease(ramp(lt, 0.3, 1.2))
        arrow(c, [(0, 300), (0, 520), (0, 760)], WEI, f, w=34, head=90)
        dust(c, 0, 600, x.t, f, 16, 140, 3, size=40)
        big_local(c, '出去打', -300, 120, WEI_L, ss(ramp(lt, 0.6, 1.0)))
    if mode == 'two':
        f = ease(ramp(lt, 0.3, 2.0))
        for dx, nm, col in [(-90, '张辽', WEI), (90, '李典', WEI)]:
            yy = lerp(260, 640, f)
            block(c, dx * (1 + f * 0.6), yy, 0, 5, 6, col, 1, gap=10, size=6, seed=dx)
            label(c, nm, dx * (1 + f * 0.6), yy + 90, 40, WEI_L, f)
        dust(c, 0, 600, x.t, f, 14, 160, 5, size=36)
    if night:
        a = ss(ramp(lt, 0.3, 0.8))
        c.drawCircle(330, -330, 48, skia.Paint(AntiAlias=True, Color=rgba('#F3E6C6', 0.9)))
        glow(c, 330, -330, 140, '#F3E6C6', 0.25)
        rrect(c, -170, -420, 340, 280, 3, '#C9B387', a)
        srect(c, -170, -420, 340, 280, '#7A1E14', a, 6)
        text(c, '募', 0, -290, 120, '#7A1E14', 'serifx', a, 'c')
        text(c, '敢从之士', 0, -190, 50, '#1A1410', 'serifx', a, 'c')
        n = int(ease(ramp(lt, 0.8, d)) * 30)
        rr = random.Random(2)
        for k in range(n):
            px, py = rr.uniform(-470, 470), rr.uniform(430, 560)
            c.drawRect(skia.Rect.MakeXYWH(px - 4, py - 4, 8, 8), skia.Paint(Color=rgba(WEI_L, 0.95)))
    c.restore()


def big_local(c, s, y, size, col, a):
    if a <= 0.01: return
    text(c, s, 0, y, size, col, 'serifx', a, 'c', stroke=7, shadow=16)


# ---------- 大字 ----------
def sc_bigtext(c, prm, x):
    lt, d, j = x.lt, x.d, x.j
    ctx = prm.get('_bg')
    if ctx == 'battle':
        cam = tactical_cam(lt, d, 0, 1, 0.12, 0.11); tactical_base(c, cam, 0.45); dawn(c, 0.8)
        hx, hy = cam.p(*P['合肥'])
        for k in range(14):
            block(c, hx + 200 + (k % 5) * 70, hy - 300 + (k // 5) * 160, 0.3, 4, 6, WU, 0.6, gap=8, size=5, seed=k)
        G.dim(c, 0.35)
    else:
        backdrop(c, x, 0.62)
    lines = prm['lines']; hl = prm.get('hl'); size = prm.get('size', 140)
    if prm.get('wm'):
        c.save(); c.translate(700, 760); c.rotate(-6 + 2 * math.sin(x.t * 0.3))
        text(c, prm['wm'], 0, 320, 820, GOLD, 'serifx', 0.06, 'c'); c.restore()
    fs = [min(size, size * 940 / max(1, tw(l, 'serifx', size))) for l in lines]
    tot = sum(fs) * 1.3; y = 760 - tot / 2 + fs[0] * 0.9
    z = 1.0 + 0.03 * lt / max(1, d) + (0.1 if j % 2 else 0)
    c.save(); c.translate(540, 760); c.scale(z, z); c.translate(-540, -760)
    for k, l in enumerate(lines):
        st = (k * d * 0.8 / len(lines)) if prm.get('stagger') and x.first_seg_shot else (k * 0.18 if x.first_seg_shot else 0)
        a = eout(ramp(lt, st, st + 0.45))
        big(c, l, y + (1 - a) * 30, fs[k], PAPER, a, hl)
        y += fs[k] * 1.3
    c.restore()
    if prm.get('src'):
        text(c, '——' + prm['src'], 540, y + 20, 32, '#B7B0A2', 'serifm', ss(ramp(lt, 0.4, 0.9)), 'c')


# ---------- 原文卡场景 ----------
def sc_quote(c, prm, x, i):
    lt, d, j = x.lt, x.d, x.j
    backdrop(c, x, 0.66)
    dd = cite_from_seg(i)
    if j % 2 == 1 and (prm.get('big') or prm.get('hl')):
        ph = prm.get('big') or prm.get('hl')
        a = eout(ramp(lt, 0, 0.35)); sc = 1.06 - 0.06 * eout(ramp(lt, 0, 0.5))
        c.save(); c.translate(540, 700); c.scale(sc, sc); c.translate(-540, -700)
        big(c, ph, 700, 180, GOLD, a)
        c.restore()
        text(c, '——' + dd['src'], 540, 820, 34, '#C9C0AE', 'serifm', a, 'c')
        if dd.get('bh'):
            for k, l in enumerate(wrap(dd['bh'], 'sansm', 36, 900)):
                text(c, l, 540, 920 + k * 52, 36, '#E9E1CF', 'sansm', a * 0.95, 'c', stroke=4)
        return
    rev = clamp(lt / max(0.8, min(2.4, d * 0.5))) if x.first_seg_shot else 1.0
    cite(c, dd, eout(ramp(lt, 0, 0.3)) if x.first_seg_shot else 1, None, qs=50, reveal=rev)


# ---------- 人物 ----------
PERS = {'张辽': (WEI, '原属吕布，下邳归曹', '辽'), '乐进': (LE, '容貌短小，以胆烈从太祖', '进'),
        '李典': (WEI_L, '好学问，不与诸将争功', '典'), '薛悌': ('#B7B0A2', '护军 · 持教', '悌')}


def person_card(c, x0, y0, w, h, nm, a=1.0, hl=True, role=None, note=None):
    if a <= 0.01: return
    col, sub, ch = PERS[nm]
    aa = a if hl else a * 0.35
    panel(c, x0, y0, w, h, aa, r=4, fa=0.86)
    rrect(c, x0, y0, 7, h, 2, col, aa)
    text(c, ch, x0 + w - 24, y0 + h - 26, h * 0.62, col, 'serifx', 0.16 * aa, 'r')
    text(c, nm, x0 + 34, y0 + 92, 72, PAPER, 'serifx', aa)
    text(c, note or sub, x0 + 36, y0 + 148, 30, '#D9D2C2', 'sansm', aa)
    if role:
        rc = {'出战': WEI, '守城': LE, '持教': '#B7B0A2'}.get(role, GOLD)
        bw = tw(role, 'sans', 30) + 30
        rrect(c, x0 + w - bw - 26, y0 + 28, bw, 48, 3, rc, aa)
        text(c, role, x0 + w - bw - 11, y0 + 64, 30, INK, 'sans', aa)


def jag(c, xa, ya, xb, yb, t, a=1.0):
    rr = random.Random(int(t * 8)); pts = []
    for k in range(10):
        u = k / 9; px, py = lerp(xa, xb, u), lerp(ya, yb, u)
        if 0 < k < 9:
            dx, dy = -(yb - ya), (xb - xa); L = math.hypot(dx, dy) + 1e-6; o = rr.uniform(-16, 16)
            px += dx / L * o; py += dy / L * o
        pts.append((px, py))
    line(c, pts, WEI, 12, 0.3 * a, blur=6); line(c, pts, WEI_L, 3.4, a)


def sc_roster(c, prm, x, i):
    who = prm['who']; lt, d, j = x.lt, x.d, x.j
    if prm.get('roles') or prm.get('letter'):
        return roles_sandbox(c, prm, x, i)
    backdrop(c, x, 0.66)
    n = len(who)
    w, h = 820, 200
    if n == 1: pos = [(130, 560)]; w, h = 820, 240
    elif n == 2: pos = [(130, 440), (130, 780)]
    elif n == 3: pos = [(130, 330), (130, 600), (130, 870)]
    else: pos = [(130, 290), (130, 520), (130, 750), (130, 980)]
    z = 1 + (0.06 if j % 2 else 0)
    c.save(); c.translate(540, 760); c.scale(z, z); c.translate(-540, -760)
    roles = {'张辽': '出战', '李典': '出战', '乐进': '守城', '薛悌': '持教'}
    for k, (nm, (px, py)) in enumerate(zip(who, pos)):
        a = eout(ramp(lt, k * 0.15 if x.first_seg_shot else 0, (k * 0.15 if x.first_seg_shot else 0) + 0.4))
        role = roles[nm] if (prm.get('hl') == '薛悌' and nm == '薛悌') else None
        person_card(c, px + (1 - a) * 40, py, w, h, nm, a, prm.get('hl') in (None, nm), role, prm.get('note') if n == 1 else None)
    if prm.get('feud') and n >= 2:
        a = ss(ramp(lt, 0.4, 0.9))
        for k in range(n - 1):
            ya, yb = pos[k][1] + h * 0.5, pos[k + 1][1] + h * 0.5
            jag(c, 990, ya, 990, yb, x.t, a)
        if n == 3: jag(c, 1020, pos[0][1] + h * 0.5, 1020, pos[2][1] + h * 0.5, x.t + 0.3, a)
        big(c, '素不睦', 1210, 88, WEI_L, a)
    c.restore()


# ---------- 时间轴 ----------
def sc_timeline(c, prm, x):
    lt, d = x.lt, x.d; anim = prm.get('anim')
    backdrop(c, x, 0.6)
    y = 860; x0, x1 = 90, 990; y0r, y1r = 200, 222
    X_ = lambda yr: lerp(x0, x1, (yr - y0r) / (y1r - y0r))
    f = ease(clamp(lt / 0.8)) if anim == 'in' else 1
    line(c, [(x0, y), (lerp(x0, x1, f), y)], GOLD, 4, 0.8)
    for yr in range(y0r, y1r + 1):
        if X_(yr) > lerp(x0, x1, f): break
        hh = 24 if yr % 5 == 0 else 10
        line(c, [(X_(yr), y - hh), (X_(yr), y + hh)], GOLD, 2.4, 0.7)
        if yr % 5 == 0: text(c, f'{yr}', X_(yr), y + 70, 32, '#B7B0A2', 'sansm', 0.9, 'c')
    a208 = 1 if anim != 'in' else ss(ramp(lt, 0.8, 1.3))
    dim208 = 0.45 if anim == 'to215' else 1
    glow(c, X_(208), y, 60, WU, a208 * dim208)
    circle(c, X_(208), y, 14, WU_L, a208 * dim208)
    text(c, '建安十三年 · 208', X_(208), y - 200, 46, WU_L, 'serifx', a208 * dim208, 'c', stroke=5)
    text(c, '赤壁之年 · 第一次围合肥', X_(208), y - 140, 34, PAPER, 'sansm', a208 * dim208, 'c', stroke=4)
    if anim == 'mark208': pulse(c, X_(208), y, x.t, WU_L, 20, 90, 1.4, 0.9)
    if anim == 'to215':
        f2 = ease(ramp(lt, 0.2, 1.4)); xx = lerp(X_(208), X_(215), f2)
        arrow(c, [(X_(208), y + 150), (xx, y + 150)], GOLD, 1, w=10, head=30)
        text(c, '七年后', (X_(208) + X_(215)) / 2, y + 230, 54, GOLD, 'serifx', f2, 'c', stroke=5)
        a = ss(ramp(lt, 1.2, 1.7))
        glow(c, X_(215), y, 90, WEI, a); circle(c, X_(215), y, 18, WEI_L, a)
        text(c, '建安二十年 · 215', X_(215), y - 260, 56, WEI_L, 'serifx', a, 'c', stroke=5)
        text(c, '逍遥津', X_(215), y - 180, 50, PAPER, 'serifx', a, 'c', stroke=5)


# ---------- 全国示意图 ----------
def sc_cnmap(c, prm, x):
    show = prm.get('show'); lt, d, j = x.lt, x.d, x.j
    foc = {'base': (112.6, 32.4, 15.0), 'cao_west': (110.8, 33.9, 13.0), 'split': (113.0, 29.4, 6.0),
           'sun_north': (115.8, 30.9, 7.0), 'dist': (112.2, 32.6, 15.5), 'dist2': (112.2, 32.6, 15.5)}[show]
    k = ease(clamp(lt / max(1, d)))
    sp = foc[2] * (1.06 - 0.06 * k) * (0.88 if j % 2 else 1)
    cam = Cam(foc[0], foc[1], sp, 540, 760)
    base(7).draw(c, cam); draw_rivers(c, cam, 0.9, 1.0, shi=False); G.dim(c, 0.12)
    def city(nm, col, a=1.0, size=40, major=False, dy=-26):
        px, py = cam.p(*P[nm]); G.city(c, px, py, nm, None, a, size, major, 0, dy, 'c')
        if col: glow(c, px, py, 50, col, 0.5 * a)
        return px, py
    for nm in ('许', '建业'): city(nm, None, 0.75, 32)
    hx, hy = city('合肥', WEI, 1, 46, True)
    pulse(c, hx, hy, x.t, WEI_L, 16, 80, 1.6, 0.8)
    city('汉中', GOLD, 1, 42, True)
    if show == 'cao_west':
        city('邺', WEI, 1, 34)
        pts = [cam.p(*q) for q in [P['邺'], (112.4, 34.8), P['长安'], (107.3, 34.0), (107.05, 33.25)]]
        arrow(c, G.smooth(pts, 2), WEI, ease(ramp(lt, 0.2, 2.6)), w=22, head=60)
        for b in range(6):
            u = ease(ramp(lt, 0.2, 2.6)) - b * 0.05
            if u > 0.02:
                bx, by, ang = G.along(G.smooth(pts, 2), u); block(c, bx, by, ang + math.pi / 2, 3, 5, WEI_L, 0.95, gap=7, size=5, seed=b)
        big(c, '曹操 西征张鲁', 430, 72, WEI_L, ss(ramp(lt, 0.8, 1.3)))
    if show == 'split':
        city('陆口', WU, 1, 34); city('江陵', None, 0.8, 32)
        pts = [cam.p(*q) for q in [(113.0, 29.2), (112.9, 28.2), (112.9, 27.8), (112.6, 26.9)]]
        pp = skia.Paint(AntiAlias=True, Color=rgba(GOLD, 0.95), Style=skia.Paint.kStroke_Style, StrokeWidth=7)
        pp.setPathEffect(skia.DashPathEffect.Make([22, 14], -x.t * 40))
        c.drawPath(G.mkpath(G.trim(G.smooth(pts, 2), 0, ease(ramp(lt, 0, 1.2)))), pp)
        a = ss(ramp(lt, 0.8, 1.3))
        lx, ly = cam.p(111.5, 27.9); label(c, '刘', lx, ly, 90, '#E8A07A', a, fname='serifx')
        lx, ly = cam.p(114.3, 27.9); label(c, '孙', lx, ly, 90, WU_L, a, fname='serifx')
        lx, ly = cam.p(112.8, 26.6); label(c, '以湘水为界（示意）', lx, ly, 36, GOLD, a)
    if show == 'sun_north':
        city('陆口', WU, 1, 34)
        pts = [cam.p(*q) for q in [P['陆口'], (115.0, 30.3), (116.3, 29.9), (117.2, 30.6), (117.9, 31.2), (117.6, 31.55), (117.32, 31.82)]]
        f = ease(ramp(lt, 0.2, 3.0))
        arrow(c, G.smooth(pts, 2), WU, f, w=24, head=64)
        for b in range(8):
            u = f - b * 0.05
            if u > 0.02:
                bx, by, ang = G.along(G.smooth(pts, 2), u); block(c, bx, by, ang + math.pi / 2, 3, 5, WU_L, 0.95, gap=7, size=5, seed=b)
                if b % 2 == 0: dust(c, bx, by, x.t, 0.6, 3, 20, seed=b, size=16)
        big(c, '孙权 掉头北上', 430, 72, WU_L, ss(ramp(lt, 0.8, 1.3)))
    if show in ('dist', 'dist2'):
        a1 = cam.p(*P['汉中']); b1 = hx, hy
        f = ease(ramp(lt, 0, 1.3)) if show == 'dist' else 1
        pp = skia.Paint(AntiAlias=True, Color=rgba(GOLD, 0.95), Style=skia.Paint.kStroke_Style, StrokeWidth=6)
        pp.setPathEffect(skia.DashPathEffect.Make([22, 14], -x.t * 30))
        c.drawLine(a1[0], a1[1], lerp(a1[0], b1[0], f), lerp(a1[1], b1[1], f), pp)
        big(c, '直线约一千公里', 430, 70, GOLD, ss(ramp(lt, 0.8, 1.3)))
        if show == 'dist2':
            u = 0.06 + 0.08 * clamp(lt / d)
            px, py = lerp(a1[0], b1[0], u), lerp(a1[1], b1[1], u)
            block(c, px, py, 0.2, 3, 4, WEI_L, 1, gap=7, size=5)
            label(c, '救兵', px, py + 56, 36, WEI_L)
            label(c, '来不及', hx - 40, hy + 100, 60, WEI_L, ss(ramp(lt, 0.8, 1.3)), fname='serifx')
    text(c, '示意 · 现代地形与河道，仅作方位参考', 60, 1250, 24, '#B7B0A2', 'sansm', 0.85)


# ---------- 合肥区域图 ----------
def sc_hfmap(c, prm, x):
    show = prm.get('show'); lt, d, j = x.lt, x.d, x.j
    k = ease(clamp(lt / max(1, d)))
    if show == 'jin':
        cam = Cam.lerp(Cam(117.33, 31.80, 0.55, 540, 760), Cam(117.296, 31.852, 0.12, 540, 760), ease(ramp(lt, 0, 2.5)))
        base(12 if cam.span < 0.4 else 10).draw(c, cam)
    else:
        cam = Cam(117.42 - 0.03 * k, 31.70 + 0.02 * k, (1.25 - 0.08 * k) * (0.86 if j % 2 else 1), 540, 760)
        base(10).draw(c, cam)
    draw_rivers(c, cam, 1.0, 1.6)
    G.dim(c, 0.1)
    def cty(nm, col, size=40, major=False, dy=-28, a=1.0):
        px, py = cam.p(*P[nm]); G.city(c, px, py, nm, None, a, size, major, 0, dy, 'c')
        if col: glow(c, px, py, 60, col, 0.5 * a)
        return px, py
    hx, hy = cam.p(*P['合肥'])
    if show != 'jin':
        city_wall(c, hx, hy, 64, WEI, 1, '', 0.5, x.t); label(c, '合肥', hx, hy - 52, 46, PAPER, fname='serifx')
        for nm in ('居巢', '濡须口'): cty(nm, None, 34)
        cx, cy = cam.p(*P['巢湖']); label(c, '巢湖', cx, cy + 12, 42, '#BFD7E2')
        lx, ly = cam.p(117.0, 32.42); label(c, '淮河 ↑', lx, ly, 34, '#BFD7E2')
        lx, ly = cam.p(117.8, 31.08); label(c, '长江', lx, ly, 40, '#BFD7E2')
        lx, ly = cam.p(117.36, 31.77); label(c, '施水（示意）', lx + 70, ly, 26, '#BFD7E2', 0.9)
    if show == 'door':
        pts = [cam.p(*q) for q in [P['濡须口'], (118.05, 31.50), (117.75, 31.58), (117.43, 31.67), (117.36, 31.78), (117.29, 31.85)]]
        arrow(c, G.smooth(pts, 2), WU, ease(ramp(lt, 0.1, 2.2)), w=24, head=62)
        a2 = ease(ramp(lt, 1.6, 2.6))
        arrow(c, [(hx, hy - 50), (hx + 10, hy - 260)], WU_L, a2, w=12, head=34, dash=(18, 12))
        big(c, '北上必经之门', 400, 72, GOLD, ss(ramp(lt, 1.0, 1.6)))
    if show == 'empty':
        rr = random.Random(5)
        for kk in range(70):
            sx, sy = rr.uniform(120, 960), rr.uniform(hy + 60, 1080)
            f = ease(clamp((lt - rr.uniform(0, 1.6)) / 2.4))
            c.drawRect(skia.Rect.MakeXYWH(sx - 3, lerp(sy, 1360, f) - 3, 6, 6), skia.Paint(Color=rgba('#E8E2D0', 0.85 * (1 - 0.8 * f))))
        wx, wy = cty('皖城', WEI, 36)
        big(c, '江西遂虚', 400, 76, GOLD, ss(ramp(lt, 1.4, 2.0)))
    if show == 'wancheng':
        f = ss(ramp(lt, 0.3, 0.9))
        wx, wy = cam.p(*P['皖城'])
        G.city(c, wx, wy, '皖城', None, 1, 36, False, 0, -28, 'c'); glow(c, wx, wy, 70, WU if f > 0.5 else WEI, 0.6)
        banner(c, wx + 20, wy - 10, WU, '孙', f, 0.9, x.t)
        pulse(c, hx, hy, x.t, WEI_L, 40, 200, 1.6, 0.9)
        big(c, '孤城', 400, 110, WEI_L, ss(ramp(lt, 1.0, 1.5)))
    if show == 'geo':
        big(c, '江淮之间', 400, 76, GOLD, ss(ramp(lt, 0.6, 1.2)))
    if show == 'jin':
        hx, hy = cam.p(*P['合肥']); S0 = W / cam.span * 0.012
        city_wall(c, hx, hy, max(60, S0 * 1.2), WEI, 1, '合肥', 0.5, x.t)
        jx, jy = cam.p(*P['逍遥津'])
        a = ss(ramp(lt, 1.6, 2.4))
        ancient_bridge(c, jx, jy, 1.0, a)
        pulse(c, jx, jy, x.t, GOLD, 20, 120, 1.6, a)
        label(c, '逍遥津（示意）', jx + 150, jy + 80, 44, GOLD, a, fname='serifx')
        label(c, '津北', jx - 90, jy - 90, 34, PAPER, a); label(c, '津南', jx + 70, jy + 150, 34, PAPER, a)
    text(c, '示意 · 底图为现代地形，河道依今', 60, 1250, 24, '#B7B0A2', 'sansm', 0.85)


def ancient_bridge(c, x, y, s, a=1.0, ang=-0.5):
    """古木桥示意：两排木桩 + 桥板。"""
    if a <= 0.01: return
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang) + 90); c.scale(s, s)
    for k in range(-3, 4):
        c.drawRect(skia.Rect.MakeXYWH(-22, k * 18 - 3, 44, 6), skia.Paint(Color=rgba('#B08A58', a)))
    for sgn in (-1, 1):
        for k in range(-3, 4):
            c.drawCircle(sgn * 26, k * 18, 4, skia.Paint(AntiAlias=True, Color=rgba('#6B4A2A', a)))
    c.restore()


# ---------- 推演链 ----------
CHAIN = ['趁敌未合', '出城逆击', '折其盛势', '以安众心', '然后可守']


def sc_chain(c, prm, x, i):
    a0, a1 = prm['upto']; lt, d, j = x.lt, x.d, x.j
    backdrop(c, x, 0.62)
    check = prm.get('check')
    shown = 5 if (check or not x.first_seg_shot) else a0 + (a1 - a0) * clamp(lt / max(1.0, d * 0.75)) + 0.999
    y0 = 300 if i in V.MECH else 330; step = 150 if i in V.MECH else 190
    for k, s_ in enumerate(CHAIN):
        a = clamp(shown - k)
        if a <= 0: continue
        a = eout(a); y = y0 + k * step
        col = WEI if k in (1, 2) else (LE if k == 4 else GOLD)
        panel(c, 240, y - 54, 600, 108, a, r=4, fa=0.86); rrect(c, 240, y - 54, 7, 108, 2, col, a)
        text(c, s_, 540, y + 24, 64, PAPER, 'serifx', a, 'c')
        if k < 4 and shown > k + 1:
            arrow(c, [(540, y + 58), (540, y + step - 58)], GOLD, 1, w=5, a=0.8, head=16, glow=False)
        if check:
            f = ease(ramp(lt, 0.3 + k * 0.25, 0.6 + k * 0.25))
            if f > 0: line(c, G.trim([(870, y), (895, y + 26), (945, y - 30)], 0, f), '#8FD39A', 11, 1)
    text(c, '——张辽语，见《三国志·张辽传》', 540, y0 + 5 * step - 40, 30, '#B7B0A2', 'serifm', 0.9, 'c')


# ---------- 孙盛 ----------
def sc_sunsheng(c, prm, x, i):
    mode = prm['mode']; lt, d, j = x.lt, x.d, x.j
    backdrop(c, x, 0.66)
    if mode == 'intro':
        panel(c, 130, 460, 820, 300, ss(ramp(lt, 0, 0.4)), r=4, fa=0.86); rrect(c, 130, 460, 7, 300, 2, V.LEVEL_COL[V.GP])
        text(c, '孙盛', 170, 580, 96, PAPER, 'serifx', ss(ramp(lt, 0, 0.4)))
        text(c, '东晋史学家 · 著《魏氏春秋》《晋阳秋》', 172, 650, 32, '#D9D2C2', 'sansm', ss(ramp(lt, 0.2, 0.6)))
        text(c, '其评见《三国志·张辽传》裴松之注', 172, 712, 30, '#B7B0A2', 'sansm', ss(ramp(lt, 0.4, 0.8)))
    elif mode == 'scale':
        c.save(); c.translate(540, 700)
        tilt = 9 * math.sin(x.t * 1.6)
        line(c, [(0, -40), (0, 330)], GOLD, 8, 0.8)
        c.save(); c.translate(0, -40); c.rotate(tilt)
        line(c, [(-380, 0), (380, 0)], GOLD, 8, 1)
        for sx, l1, l2, col in [(-1, '专任勇者', '好战生患', WEI_L), (1, '专任怯者', '惧心难保', LE)]:
            c.save(); c.translate(sx * 320, 0); c.rotate(-tilt)
            line(c, [(-70, 150), (0, 0), (70, 150)], GOLD, 2.6, 0.8)
            panel(c, -170, 150, 340, 170, 1, r=4, fa=0.88); rrect(c, -170, 150, 340, 6, 2, col)
            text(c, l1, 0, 225, 50, PAPER, 'serifx', 1, 'c'); text(c, l2, 0, 290, 44, col, 'serifx', ss(ramp(lt, 0.6, 1.0)), 'c')
            c.restore()
        c.restore(); c.restore()
        big(c, '都不行', 380, 96, GOLD, ss(ramp(lt, 1.4, 1.8)))
        text(c, '——孙盛语，见《张辽传》裴注', 540, 1180, 30, '#B7B0A2', 'serifm', 0.9, 'c')
    elif mode == 'fangyuan':
        f = ease(ramp(lt, 0, 1.0))
        sx = lerp(330, 430, f); cx2 = lerp(750, 650, f)
        rrect(c, sx - 100, 380, 200, 200, 3, WEI, 0.95); text(c, '方', sx, 520, 120, INK, 'serifx', 1, 'c')
        circle(c, cx2, 480, 102, LE, 0.95); text(c, '员', cx2, 522, 120, INK, 'serifx', 1, 'c')
        big(c, '推选方员 · 参以同异', 720, 80, GOLD, ss(ramp(lt, 0.6, 1.1)))
    elif mode == 'fuqi':
        f = ease(ramp(lt, 0, 1.6))
        for sgn in (-1, 1):
            off = lerp(240, 0, f) * sgn
            c.save(); c.translate(540 + off, 560)
            p = skia.Path()
            if sgn < 0:
                p.moveTo(0, -190); p.lineTo(-210, -150); p.quadTo(-260, 0, -210, 150); p.lineTo(0, 190)
            else:
                p.moveTo(0, -190); p.lineTo(210, -150); p.quadTo(260, 0, 210, 150); p.lineTo(0, 190)
            for kk in range(8):
                yy = 190 - kk * 47.5
                p.lineTo(18 if kk % 2 == 0 else 0, yy - 24); p.lineTo(0, yy - 47.5)
            p.close()
            sh = skia.GradientShader.MakeLinear([(-200, -190), (200, 190)], [rgba('#C9A24A'), rgba('#7A5A22')])
            c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh))
            c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba('#2A1A08', 0.8), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
            text(c, '符' if sgn < 0 else '契', sgn * 110, 40, 110, '#2A1A08', 'serifx', 1, 'c')
            c.restore()
        if f > 0.97: glow(c, 540, 560, 320, GOLD, 0.3 * (0.6 + 0.4 * math.sin(x.t * 5)))
        big(c, '事至而应，若合符契', 900, 80, GOLD, ss(ramp(lt, 1.3, 1.8)))


# ---------- 断句对照 ----------
def sc_twocut(c, prm, x):
    lt = x.lt
    backdrop(c, x, 0.66)
    cite(c, dict(level=V.ZS, src='《三国志·张辽传》', q='若孙权至者，张、李将军出战；乐将军守护军，勿得与战。', hl='乐将军守护军',
                 bh='读法一：乐进守护护军（薛悌），不得出战。'), ss(ramp(lt, 0, 0.4)), 270, qs=42)
    cite(c, dict(level=V.TJ, src='卷六十七', q='若孙权至者，张、李将军出战，乐将军守，护军勿得与战。', hl='乐将军守',
                 bh='读法二：乐进守城，护军不得出战。'), ss(ramp(lt, 1.0, 1.4)), 700, qs=42)
    big(c, '无论怎么断：乐进守', 1215, 66, LE, ss(ramp(lt, 2.4, 3.0)))


# ---------- 津桥（侧视） ----------
def sc_bridge(c, prm, x):
    p0, p1 = prm['p']; lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.9)))
    dark = prm.get('dark'); broken = prm.get('broken')
    sh = skia.GradientShader.MakeLinear([(0, 200), (0, 1300)], [rgba('#0A0E14'), rgba('#1A2430' if not dark else '#0E141A')])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    glow(c, 820, 360, 240, '#F3E6C6', 0.12 if dark else 0.2)
    z = (1 + 0.05 * lt / max(1, d)) * (1.15 if j % 2 else 1)
    fx = 620 if j % 2 else 540
    c.save(); c.translate(540, 760); c.scale(z, z); c.translate(-fx, -760)
    for k in range(9):
        y = 900 + k * 40
        pts = [(xx, y + 7 * math.sin(xx * 0.02 + x.t * 1.4 + k)) for xx in range(-60, 1160, 40)]
        line(c, pts, '#5E9DB8', 3, (0.5 - k * 0.04) * (0.5 if dark else 0.9))
    for bx in (200, 420, 640, 860):
        c.drawRect(skia.Rect.MakeXYWH(bx - 16, 780, 32, 260), skia.Paint(Color=rgba('#3A2A1A', 0.95)))
        c.drawRect(skia.Rect.MakeXYWH(bx - 16, 900, 32, 140), skia.Paint(Color=rgba('#000000', 0.35)))
    gap0, gap1 = 700, 840
    for k in range(42):
        x0 = 60 + k * 22
        if x0 > 980: break
        if gap0 <= x0 < gap1: continue
        if broken and 520 <= x0 < 700 and k % 3: continue
        c.drawRect(skia.Rect.MakeXYWH(x0, 760, 19, 24), skia.Paint(Color=rgba('#8A6A42', 0.95 if not dark else 0.6)))
    line(c, [(60, 758), (gap0, 758)], '#C9A878', 3, 0.6); line(c, [(gap1, 758), (980, 758)], '#C9A878', 3, 0.6)
    ga = 0.6 + 0.4 * math.sin(x.t * 4)
    c.drawRect(skia.Rect.MakeXYWH(gap0, 750, gap1 - gap0, 44), skia.Paint(Color=rgba(GOLD, 0.16 * ga)))
    pp = skia.Paint(AntiAlias=True, Color=rgba(GOLD, 0.9), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
    pp.setPathEffect(skia.DashPathEffect.Make([10, 8], 0)); c.drawRect(skia.Rect.MakeXYWH(gap0, 760, gap1 - gap0, 24), pp)
    label(c, '津北', 120, 700, 40, PAPER, 0.85); label(c, '津南', 960, 700, 40, PAPER, 0.85)
    if prm.get('measure'):
        a = ss(ramp(lt, 0, 0.5))
        line(c, [(gap0, 850), (gap1, 850)], GOLD, 4, a); line(c, [(gap0, 830), (gap0, 870)], GOLD, 4, a); line(c, [(gap1, 830), (gap1, 870)], GOLD, 4, a)
        label(c, '一丈 ≈ 2.3 米（汉尺约 23 厘米）', (gap0 + gap1) / 2, 930, 40, GOLD, a)
    if not broken:
        if p < 0.55: bx = lerp(100, gap0 - 30, ease(p / 0.55)); by = 728
        elif p < 0.6: bx, by = gap0 - 30, 728
        else:
            q = ease((p - 0.6) / 0.4); bx = lerp(gap0 - 30, gap1 + 60, q); by = 728 - math.sin(math.pi * q) * 150
        aa = 0.55 if dark else 1
        for k in range(7): circle(c, bx - 18 * k, by + (6 * k if p > 0.6 else 0), 15 - 2 * k, WU_L, 0.16 * aa)
        glow(c, bx, by, 40, WU, aa); circle(c, bx, by, 15, WU_L, aa)
        banner(c, bx - 4, by - 10, WU, '孙', aa, 0.7, x.t)
        if p > 0.45: dust(c, bx - 30, 760, x.t, aa * 0.8, 8, 30, 3, size=20)
        if p > 0.5 and not dark:
            gx_ = bx - 70 if p < 0.6 else gap0 - 110
            circle(c, gx_, 742, 10, '#9FE6EA', 1); label(c, '谷利', gx_ - 10, 700, 32, '#9FE6EA', 1)
            if 0.58 < p < 0.72:
                line(c, [(gx_ + 10, 730), (bx - 20, by - 5)], GOLD, 4, 1); glow(c, bx - 20, by, 60, GOLD, 0.5)
    else:
        q = clamp(lt / max(1, d))
        circle(c, lerp(480, 820, q), 905 + 4 * math.sin(x.t * 3), 11, WU_L, 0.9)
        label(c, '凌统', lerp(480, 820, q), 980, 34, WU_L, 0.9)
    c.restore()
    if broken: big(c, '桥败路绝', 420, 96, GOLD, ss(ramp(lt, 0, 0.6)))
    if prm.get('word'): big(c, prm['word'], 1205, 96, GOLD, eout(ramp(lt, 0.3, 0.65)))
    if dark and not broken and p0 < 0.5: big(c, '十几天后 · 津桥', 420, 80, PAPER, ss(ramp(lt, 0.8, 1.4)) * 0.92)
    text(c, '古桥示意', 60, 1250, 24, '#B7B0A2', 'sansm', 0.85)


# ---------- 文献层 ----------
LAYERS = [('魏略', '鱼豢 · 三国魏', 'ghost'), ('三国志 正文', '陈寿 · 西晋', 'zw'), ('裴松之注', '南朝宋 · 429 年', 'pz'),
          ('蒙求', '唐', 'mq'), ('太平御览', '北宋 · 983 年', 'yl'), ('资治通鉴', '北宋 · 1084 年', 'tj'), ('三国演义', '元末明初', 'yy')]


def sc_layers(c, prm, x):
    mode = prm['mode']; lt, d = x.lt, x.d
    backdrop(c, x, 0.7)
    bh = 112; y_bot = 1120
    marks, hl = {}, set()
    if mode == 'jbz': hl = {'pz'}
    elif mode == 'none3': marks = {'zw': '✕', 'tj': '✕'}; hl = {'zw', 'tj'}
    elif mode == 'yulan': marks = {'zw': '✕', 'tj': '✕', 'yl': '✓'}; hl = {'yl'}
    elif mode == 'weilue': hl = {'ghost', 'yl'}; marks = {'yl': '✓'}
    elif mode == 'rise': hl = {'ghost', 'mq', 'yy'}
    ys = {}
    for k, (nm, sub, key) in enumerate(LAYERS):
        y = y_bot - k * (bh + 12); ys[key] = y
        a = eout(ramp(lt, k * 0.07, k * 0.07 + 0.4)) if x.first_seg_shot else 1
        on = key in hl; col = GOLD if on else '#6A6458'
        if key == 'ghost':
            pp = skia.Paint(AntiAlias=True, Color=rgba(col, a), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
            pp.setPathEffect(skia.DashPathEffect.Make([14, 10], 0)); c.drawRect(skia.Rect.MakeXYWH(120, y - bh / 2, 840, bh), pp)
            text(c, '已佚', 930, y + 12, 32, WEI_L, 'sans', a, 'r')
        else:
            panel(c, 120, y - bh / 2, 840, bh, a, r=3, fa=0.86 if on else 0.6); rrect(c, 120, y - bh / 2, 7, bh, 2, col, a)
        text(c, nm, 160, y + 18, 52, PAPER if on else '#9A948A', 'serifx', a)
        text(c, sub, 600, y + 14, 30, '#D9D2C2' if on else '#7A7468', 'sansm', a)
        if key in marks:
            mk = marks[key]; ma = ss(ramp(lt, 0.6 + k * 0.12, 0.9 + k * 0.12))
            text(c, mk, 925, y + 22, 66, WEI_L if mk == '✕' else '#8FD39A', 'sans', ma, 'r')
    if mode == 'jbz': G.tag(c, 540, 260, '裴注引《江表传》：故事性较强，照原文讲', GOLD, ss(ramp(lt, 0.4, 0.8)), 30, 'c')
    if mode == 'yulan': G.tag(c, 540, 260, '卷四百八十八 · 人事部 · 泣', GOLD, ss(ramp(lt, 0.4, 0.8)), 30, 'c')
    if mode == 'none3': G.tag(c, 540, 260, '正文均未见「止啼」', WEI_L, ss(ramp(lt, 0.6, 1.0)), 30, 'c')
    if mode == 'weilue':
        f = ease(ramp(lt, 0.4, 1.6))
        arrow(c, [(985, ys['ghost']), (1030, (ys['ghost'] + ys['yl']) / 2), (985, ys['yl'])], GOLD, f, w=8, head=24)
        G.tag(c, 540, 260, '《魏略》已佚，靠《御览》转引留存', GOLD, ss(ramp(lt, 0.4, 0.8)), 30, 'c')
    if mode == 'rise':
        f = ease(ramp(lt, 0.3, max(1.0, d * 0.7)))
        arrow(c, [(80, ys['ghost']), (60, ys['mq']), (80, ys['yy'])], GOLD, f, w=9, head=26)
        for key, lab, at in [('ghost', '风声', 0.0), ('mq', '典故', 0.45), ('yy', '小说', 0.9)]:
            G.tag(c, 940, ys[key] - 50, lab, GOLD, ss(ramp(f, at, at + 0.1)), 30, 'r')


# ---------- 两国记载 ----------
def sc_split(c, prm, x):
    mode = prm['mode']; lt, d = x.lt, x.d
    cam = Cam(117.296, 31.858, 0.16, 540, 760); tactical_base(c, cam, 0.45)
    merge = ease(ramp(lt, 0.3, 1.4)) if mode == 'merge' else 0
    f = ease(ramp(lt, 0, 0.6))
    for side, col, t1, t2, t3 in [(-1, WEI, '魏', '《张辽传》', '出城那一冲'), (1, WU, '吴', '《吴主传》《甘宁传》《凌统传》', '撤退差点被擒')]:
        off = lerp(250, 238, merge) if mode != 'intro' else lerp(520, 250, f)
        cx = 540 + side * off
        panel(c, cx - 230, 360, 460, 780, 1, r=4, fa=0.78)
        rrect(c, cx - 230, 360, 460, 7, 2, col)
        text(c, t1, cx, 620, 200, col, 'serifx', 1, 'c')
        for k, l in enumerate(wrap(t2, 'serif', 34, 400)): text(c, l, cx, 720 + k * 46, 34, PAPER, 'serif', 1, 'c')
        if mode in ('both', 'merge'):
            a = ss(ramp(lt, 0.4 + (0.5 if side > 0 else 0), 0.8 + (0.5 if side > 0 else 0)))
            text(c, t3, cx, 900, 52, GOLD, 'serifx', a, 'c', stroke=4)
            if side < 0: arrow(c, [(cx, 1080), (cx, 960)], WEI, a, w=16, head=40)
            else:
                ancient_bridge(c, cx, 1020, 2.2, a, 0)
    if mode == 'merge': big(c, '一场仗 · 各记一半', 300, 80, GOLD, ss(ramp(lt, 1.0, 1.5)))


# ---------- 大船 ----------
def sc_boat(c, prm, x):
    lt, d = x.lt, x.d
    sh = skia.GradientShader.MakeLinear([(0, 200), (0, 1300)], [rgba('#0A0E14'), rgba('#16202A')])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    z = 1 + 0.05 * lt / max(1, d) + (0.12 if x.j % 2 else 0)
    c.save(); c.translate(540, 760); c.scale(z, z)
    bob = 7 * math.sin(x.t * 1.3)
    hull = skia.Path(); hull.moveTo(-400, 60 + bob); hull.lineTo(400, 60 + bob); hull.quadTo(350, 200 + bob, 230, 210 + bob)
    hull.lineTo(-230, 210 + bob); hull.quadTo(-350, 200 + bob, -400, 60 + bob)
    c.drawPath(hull, skia.Paint(AntiAlias=True, Color=rgba('#2A2018')))
    c.drawPath(hull, skia.Paint(AntiAlias=True, Color=rgba('#6B5030', 0.8), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    c.drawRect(skia.Rect.MakeXYWH(-230, -120 + bob, 460, 180), skia.Paint(Color=rgba('#221A14')))
    for k in range(4):
        lx = -170 + k * 113; fl = 0.75 + 0.25 * math.sin(x.t * 5 + k)
        glow(c, lx, -40 + bob, 80 * fl, '#FFB25A', 0.6); circle(c, lx, -40 + bob, 14 * fl, '#FFD99A', 0.95)
    for k in range(7):
        y = 250 + k * 36
        pts = [(xx, y + 6 * math.sin(xx * 0.02 + x.t * 1.4 + k)) for xx in range(-580, 600, 40)]
        line(c, pts, '#5E9DB8', 3, 0.5 - k * 0.06)
    c.restore()
    big(c, '入大船宴饮', 420, 84, GOLD, ss(ramp(lt, 0.3, 0.8)))


# ---------- 尾声：循行 ----------
def sc_walk(c, prm, x):
    p0, p1 = prm['p']; lt, d = x.lt, x.d
    p = lerp(p0, p1, clamp(lt / max(0.1, d)))
    cam = Cam(117.292, 31.862, 0.14 - 0.03 * p, 540, 760); tactical_base(c, cam, 0.35)
    p_ = skia.Paint(); p_.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 1300)], [rgba('#3A2A4A', 0.25), rgba('#FF8A4A', 0.14)]))
    p_.setBlendMode(skia.BlendMode.kScreen); c.drawRect(skia.Rect.MakeWH(W, H), p_)
    hx, hy = cam.p(*P['合肥']); S0 = W / cam.span * 0.012 * 1.15
    city_wall(c, hx, hy, S0, WEI, 1, '合肥', 0.4, x.t)
    pts = [cam.p(*q) for q in [GATE, (117.292, 31.869), (117.304, 31.872), (117.316, 31.866), (117.306, 31.858), (117.296, 31.861)]]
    path = G.smooth(pts, 2)
    line(c, G.trim(path, 0, p), GOLD, 5, 0.8, dash=(6, 12))
    mx, my, _ = G.along(path, max(0.001, p))
    glow(c, mx, my, 40, GOLD, 0.8); circle(c, mx, my, 10, '#FFE9B0', 1)
    label(c, '曹操', mx, my - 30, 32, GOLD)
    hlx, hly = cam.p(*HILL); label(c, '辽战处', hlx + 60, hly - 40, 34, PAPER, 0.8)
    if p0 < 0.25: big(c, '建安二十一年', 400, 76, GOLD, ss(ramp(lt, 0.3, 0.8)))
    if p > 0.5: big(c, '叹息者良久', 1205, 88, GOLD, ss(ramp(p, 0.55, 0.75)))


# ---------- 章节 / 标题 / 片尾 ----------
NUM = {'第一章': '壹', '第二章': '贰', '第三章': '叁', '第四章': '肆', '第五章': '伍', '尾声': '尾声'}


def sc_chapter(c, prm, x):
    lt, d = x.lt, x.d
    cam = Cam(117.42 + 0.02 * lt, 31.72, 1.1 - 0.04 * lt, 540, 760)
    base(10).draw(c, cam); draw_rivers(c, cam, 0.7, 1.4); G.dim(c, 0.5)
    a = eout(ramp(lt, 0, 0.35))
    sweep = (lt / d) * 1.6 - 0.3
    sh = skia.GradientShader.MakeLinear([(0, 0), (W, 0)], [rgba(GOLD, 0), rgba(GOLD, 0.22), rgba(GOLD, 0)],
                                        [clamp(sweep - 0.2), clamp(sweep), clamp(sweep + 0.2)])
    c.drawRect(skia.Rect.MakeXYWH(0, 560, W, 400), skia.Paint(Shader=sh))
    n = NUM.get(prm['n'], prm['n'])
    t = f'{n} · {prm["title"]}'
    line(c, [(lerp(540, 150, a), 620), (lerp(540, 930, a), 620)], GOLD, 2, 0.8)
    line(c, [(lerp(540, 150, a), 900), (lerp(540, 930, a), 900)], GOLD, 2, 0.8)
    sc = 1.1 - 0.1 * eout(ramp(lt, 0, 0.5))
    c.save(); c.translate(540, 790); c.scale(sc, sc); c.translate(-540, -790)
    big(c, t, 800, 108, PAPER, a, n, GOLD)
    c.restore()


def sc_title(c, prm, x):
    lt, d = x.lt, x.d
    cam = Cam(117.30 + 0.01 * lt, 31.85, 0.30 - 0.02 * lt, 540, 760); tactical_base(c, cam, 0.5); dawn(c, 0.6)
    hx, hy = cam.p(*P['合肥'])
    city_wall(c, hx, hy, 120, WEI, 0.7, '', 0.4, x.t)
    a = eout(ramp(lt, 0, 0.4))
    text(c, '历史的关键一局', 540, 560, 40, GOLD, 'serif', a, 'c', stroke=4, spacing=8)
    big(c, '八百人冲阵之前', 720, 116, PAPER, a, '八百人')
    big(c, '那封信写了什么？', 870, 116, PAPER, eout(ramp(lt, 0.2, 0.6)), '那封信')
    text(c, '逍遥津 · 建安二十年 · 公元 215 年', 540, 990, 38, '#C9C0AE', 'serifm', eout(ramp(lt, 0.5, 1.0)), 'c')


def sc_outro(c, x):
    lt, d = x.lt, x.d
    cam = Cam(117.36, 31.76, 0.7 + 0.02 * lt, 540, 760); base(10).draw(c, cam); draw_rivers(c, cam, 0.6, 1.2); G.dim(c, 0.62)
    o = V.OUTRO
    for k, l in enumerate(o['lines']):
        a = eout(ramp(lt, 0.3 + k * 0.6, 0.9 + k * 0.6))
        last = k == len(o['lines']) - 1
        big(c, l, 470 + k * 150, 96 if not last else 110, GOLD if last else PAPER, a * (1 if last or lt < 3.2 else 0.55))
    a = eout(ramp(lt, 2.4, 3.0))
    text(c, '——' + o['src'], 540, 900, 40, '#D9D2C2', 'serifm', a, 'c')
    for k, l in enumerate(wrap('白话｜' + o['bh'], 'sansm', 36, 900)):
        text(c, l, 540, 990 + k * 50, 36, '#E9E1CF', 'sansm', a, 'c', stroke=4)
    for k, l in enumerate(wrap(o['note'], 'sansm', 28, 900)):
        text(c, l, 540, 1120 + k * 40, 28, '#B7B0A2', 'sansm', eout(ramp(lt, 3.2, 3.8)), 'c')
    if lt > d - 0.8: G.dim(c, clamp((lt - (d - 0.8)) / 0.8), '#000000')


# 段号 → 场景覆盖（不改 script_data，只换画面）
OVERRIDE = {0: ('opener', {}), 3: ('bigtext', dict(lines=['八百人冲阵之前', '那封信写了什么？'], hl='那封信', _bg='battle')),
            8: ('bigtext', dict(lines=['八百', '破十万'], hl='八百', size=210, _bg='battle'))}


def scene_of(i):
    if i in OVERRIDE: return OVERRIDE[i]
    return S[i]['v']


def dispatch(c, i, x):
    name, prm = scene_of(i)
    if name == 'opener': return sc_opener(c, prm, x)
    if name in ('quote',): return sc_quote(c, prm, x, i)
    if name in ('roster',): return sc_roster(c, prm, x, i)
    if name in ('chain',): return sc_chain(c, prm, x, i)
    if name in ('sunsheng',): return sc_sunsheng(c, prm, x, i)
    fn = {'letter': sc_letter, 'siege': sc_siege, 'gate': sc_gate, 'bigtext': sc_bigtext, 'timeline': sc_timeline,
          'cnmap': sc_cnmap, 'hfmap': sc_hfmap, 'dots': sc_dots, 'twocut': sc_twocut, 'battle': sc_battle,
          'retreat': sc_retreat, 'bridge': sc_bridge, 'layers': sc_layers, 'split': sc_split, 'boat': sc_boat,
          'walk': sc_walk, 'chapter': sc_chapter, 'title': sc_title}[name]
    return fn(c, prm, x)


# ───────── 时间线与帧 ─────────
def load_tl():
    tl = json.load(open(os.path.join(HERE, 'timeline_yy.json')))
    tl['voice_total'] = tl['total']
    tl['total'] = tl['total'] + V.OUTRO['dur']
    chap = ''
    for sg in tl['segs']:
        if sg.get('chap'): chap = f"{NUM.get(sg['chap'][0], sg['chap'][0])} · {sg['chap'][1]}"
        sg['chapname'] = chap
    prev = None
    for sg in tl['segs']:
        nm = scene_of(sg['i'])[0]; sg['jofs'] = 0
        if prev and prev[0] == nm: sg['jofs'] = (prev[1] + prev[2]) % 2
        prev = (nm, sg['jofs'], sg['shots'])
    return tl


def find_seg(tl, t):
    segs = tl['segs']; lo, hi = 0, len(segs) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segs[mid]['start'] <= t: lo = mid
        else: hi = mid - 1
    return segs[lo]


CONT = ('battle', 'retreat', 'bridge', 'walk', 'siege', 'cnmap', 'hfmap', 'timeline', 'letter', 'chain', 'dots', 'layers',
        'opener', 'gate', 'split', 'roster_sand')


def shake_amt(i, lt):
    if i not in V.SHAKE: return 0.0
    t0, A = V.SHAKE[i]
    if lt < t0: return 0.0
    return A * math.exp(-(lt - t0) * 2.6)


def render_frame(c, t, tl, fi=0):
    c.clear(skia.ColorBLACK)
    x = X(); x.t = t
    if t >= tl['voice_total']:
        x.lt = t - tl['voice_total']; x.d = V.OUTRO['dur']; x.j = 0; x.first_seg_shot = True
        sc_outro(c, x); shade_top(c, 0.6); header(c, t, '尾声 · 回到合肥')
        return
    sg = find_seg(tl, t); i = sg['i']
    name, prm = scene_of(i)
    lt_seg = max(0.0, t - sg['start']); n = sg['shots']; sd = sg['dur'] / n
    j = min(n - 1, int(lt_seg / sd))
    x.j = j + sg.get('jofs', 0)
    cont = name in CONT or (name == 'roster' and (prm.get('roles') or prm.get('letter')))
    x.lt = lt_seg if cont else lt_seg - j * sd
    x.d = sg['dur'] if cont else sd
    x.first_seg_shot = cont or j == 0
    # 震动
    sh = shake_amt(i, lt_seg)
    c.save()
    if sh > 0.05:
        c.translate(sh * math.sin(t * 61.0), sh * math.cos(t * 47.0))
    cut = clamp((lt_seg - j * sd) / 0.16)
    if cut < 1 and not cont:
        s_ = 1.025 - 0.025 * eout(cut); c.translate(540, 760); c.scale(s_, s_); c.translate(-540, -760)
    dispatch(c, i, x)
    c.restore()
    # 叠加原文卡 / 机制卡
    if i in V.EXTRA_CITE:
        e = V.EXTRA_CITE[i]; at = e.get('at', 0.3)
        a = eout(ramp(lt_seg, at, at + 0.4))
        if a > 0:
            if e['pos'] == 'top': cite(c, e, a, 250, qs=38, reveal=clamp((lt_seg - at) / 1.6))
            else:
                hh = cite_height(e, 38); cite(c, e, a, 1250 - hh, qs=38, reveal=clamp((lt_seg - at) / 1.6))
    if i in V.MECH:
        e = dict(V.MECH[i]); at = 0.8
        a = eout(ramp(lt_seg, at, at + 0.4))
        if a > 0:
            hh = cite_height(e, 36); cite(c, e, a, 1250 - hh, qs=36, reveal=clamp((lt_seg - at) / 1.8))
    shade_top(c, 1.0)
    G.vignette(c, 0.8)
    header(c, t, sg['chapname'] if name != 'title' else '')
    # 字幕
    if not sg.get('chap'):
        lt = t - sg['start']; subs = sg['subs']
        for k, (a0, a1, ln) in enumerate(subs):
            last = k == len(subs) - 1
            if a0 <= lt < a1 or (last and lt >= a1 and lt < sg['dur']):
                G.subtitle(c, ln, 1.0, y=1420); break
    if t < tl['total'] and t > tl['total'] - 0.5:
        G.dim(c, clamp((t - (tl['total'] - 0.5)) / 0.5), '#000000')


def cite_height(d, qs):
    pad = 30; w = 968
    lines = []
    for part in d['q'].split('／'):
        lines += wrap(part.strip(), 'serif', qs, w - pad * 2 - 8); lines.append(None)
    lines = lines[:-1]
    bl = wrap('白话｜' + (d.get('bh') or ''), 'sansm', 32, w - pad * 2 - 8) if d.get('bh') else []
    nl = wrap(d['note'], 'sansm', 27, w - pad * 2 - 8) if d.get('note') else []
    hq = sum(qs * 1.45 if l is not None else qs * 0.4 for l in lines)
    return 78 + src_extra(d) + (56 if d.get('title') else 0) + hq + (len(bl) * 46 + 22 if bl else 6) + (len(nl) * 38 + 10 if nl else 0) + 14


def header(c, t, chap):
    text(c, '历史的关键一局', 56, 150, 30, GOLD, 'serif', 0.92, 'l', stroke=4, spacing=3)
    line(c, [(56, 168), (300, 168)], GOLD, 1.5, 0.5)
    if chap: text(c, chap, 1024, 150, 30, PAPER, 'serif', 0.88, 'r', stroke=4)
    if t < 7: text(c, 'AI 配音 · 地图为示意', 1024, 196, 24, '#B7B0A2', 'sansm', 0.85 * (1 - clamp(t - 6)), 'r')


def main():
    cmd = sys.argv[1]
    tl = load_tl()
    surf = skia.Surface(W, H); c = surf.getCanvas()
    if cmd == 'frames':
        for tt in sys.argv[2].split(','):
            render_frame(c, float(tt), tl)
            surf.makeImageSnapshot().save(f"{sys.argv[3]}_{float(tt):07.2f}.png", skia.kPNG)
        return
    if cmd == 'chunk':
        k, n, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        nf = int(round(tl['total'] * FPS))
        f0, f1 = nf * k // n, nf * (k + 1) // n
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                               '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12',
                               '-pix_fmt', 'yuv420p', '-r', str(FPS), out], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            render_frame(c, fi / FPS, tl, fi)
            ff.stdin.write(surf.makeImageSnapshot().tobytes())
            if fi % 500 == 0: print(k, fi, f1, flush=True)
        ff.stdin.close()
        if ff.wait() != 0: sys.exit(1)
        print('done', k, f1 - f0, flush=True)
    if cmd == 'nframes':
        print(int(round(tl['total'] * FPS)))


if __name__ == '__main__':
    main()
