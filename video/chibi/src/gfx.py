# -*- coding: utf-8 -*-
"""绘图图元：文字、标签、部队标识、箭头、面板、引文卡、字幕。"""
import math, skia, numpy as np
from geo import W, H, Cam, merc

FD = '/usr/share/fonts/opentype/noto/'
_tf = {}
def tf(name):
    if name not in _tf:
        f = {'serif': 'NotoSerifCJK-Bold.ttc', 'serifx': 'NotoSerifCJK-Black.ttc', 'serifm': 'NotoSerifCJK-SemiBold.ttc',
             'sans': 'NotoSansCJK-Bold.ttc', 'sansm': 'NotoSansCJK-Medium.ttc', 'sansx': 'NotoSansCJK-Black.ttc'}[name]
        _tf[name] = skia.Typeface.MakeFromFile(FD + f, 2)
    return _tf[name]
_fonts = {}
def font(name, size):
    k = (name, round(size, 1))
    if k not in _fonts:
        f = skia.Font(tf(name), size); f.setSubpixel(True); f.setEdging(skia.Font.Edging.kAntiAlias); _fonts[k] = f
    return _fonts[k]

# ---- 颜色 ----
def rgba(hexs, a=1.0):
    hexs = hexs.lstrip('#'); r, g, b = int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))
LIU, LIU_D, LIU_L = '#C63A2E', '#6E1D18', '#F08A7A'
CAO, CAO_D, CAO_L = '#8C99A8', '#3F4853', '#C9D3DE'
SUN, SUN_D, SUN_L = '#0F8A93', '#07474D', '#6FD3D6'
GOLD, INK, PAPER = '#E6CC8F', '#0E0F11', '#F3EEE4'
AMBER = '#F2A93B'
FAC = {'liu': (LIU, LIU_D, LIU_L), 'cao': (CAO, CAO_D, CAO_L), 'sun': (SUN, SUN_D, SUN_L)}

# ---- 缓动 ----
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ramp(t, t0, t1): return 0.0 if t1 <= t0 else clamp((t - t0) / (t1 - t0))
def fade(t, t0, t1, din=0.5, dout=0.5):
    """t0 淡入、t1 淡出的可见度。"""
    return ss(ramp(t, t0, t0 + din)) * (1 - ss(ramp(t, t1 - dout, t1)))
def lerp(a, b, t): return a + (b - a) * t
def mix(c1, c2, t):
    a = [int(c1.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]; b = [int(c2.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02X%02X%02X' % tuple(int(round(lerp(x, y, clamp(t)))) for x, y in zip(a, b))

# ---- 文字 ----
def tw(s, fname, size): return font(fname, size).measureText(s)
def text(c, s, x, y, size, color=PAPER, fname='serif', a=1.0, anchor='l', stroke=0.0, stroke_color=INK, shadow=0.0, spacing=0.0):
    """y 为基线。anchor: l/c/r。"""
    if a <= 0.003 or not s: return 0
    f = font(fname, size)
    if spacing:
        w = sum(f.measureText(ch) for ch in s) + spacing * (len(s) - 1)
    else:
        w = f.measureText(s)
    x0 = x - (w / 2 if anchor == 'c' else w if anchor == 'r' else 0)
    def run(paint):
        if spacing:
            xx = x0
            for ch in s:
                c.drawString(ch, xx, y, f, paint); xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, x0, y, f, paint)
    if shadow > 0:
        p = skia.Paint(AntiAlias=True, Color=rgba('#000000', 0.75 * a)); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow))
        c.save(); c.translate(0, shadow * 0.35); run(p); c.restore()
    if stroke > 0:
        p = skia.Paint(AntiAlias=True, Color=rgba(stroke_color, 0.92 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join); run(p)
    run(skia.Paint(AntiAlias=True, Color=rgba(color, a)))
    return w

PUNC_NOSTART = '，。、；：？！”’》）…—·'
def wrap(s, fname, size, maxw):
    f = font(fname, size); lines = []; cur = ''
    for ch in s:
        if ch == '\n': lines.append(cur); cur = ''; continue
        if f.measureText(cur + ch) > maxw and cur and ch not in PUNC_NOSTART:
            lines.append(cur); cur = ch
        else: cur += ch
    if cur: lines.append(cur)
    return lines

def rrect(c, x, y, w, h, r, color, a=1.0, stroke=None, sw=2.0, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=rgba(color, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)
    if stroke:
        p = skia.Paint(AntiAlias=True, Color=rgba(stroke, a), Style=skia.Paint.kStroke_Style, StrokeWidth=sw)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)

def panel(c, x, y, w, h, a=1.0, r=10, fill='#0B0D10', fa=0.80, edge='#FFFFFF', ea=0.10):
    if a <= 0.003: return
    rrect(c, x, y + 6, w, h, r, '#000000', 0.45 * a, blur=18)
    rrect(c, x, y, w, h, r, fill, fa * a)
    rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, r, edge, 0.0, stroke=edge, sw=1.0) if False else None
    p = skia.Paint(AntiAlias=True, Color=rgba(edge, ea * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 0.6, y + 0.6, w - 1.2, h - 1.2), r, r), p)

# ---- 路径 ----
def smooth(pts, it=2):
    """Chaikin 平滑。"""
    for _ in range(it):
        q = [pts[0]]
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            q.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1)); q.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        q.append(pts[-1]); pts = q
    return pts
def plen(pts):
    return sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
def along(pts, u):
    """沿折线取点，u∈[0,1]，返回 (x,y,angle)。"""
    u = clamp(u); L = plen(pts); d = u * L
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; s = math.hypot(x1 - x0, y1 - y0)
        if d <= s or i == len(pts) - 2:
            k = 0 if s == 0 else clamp(d / s)
            return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, math.atan2(y1 - y0, x1 - x0)
        d -= s
def trim(pts, u0, u1):
    """截取折线的 [u0,u1] 段。"""
    L = plen(pts); a, b = clamp(u0) * L, clamp(u1) * L; out = []; d = 0
    if b <= a: return []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; s = math.hypot(x1 - x0, y1 - y0)
        if s == 0: continue
        if d + s >= a and d <= b:
            k0 = clamp((a - d) / s); k1 = clamp((b - d) / s)
            p0 = (x0 + (x1 - x0) * k0, y0 + (y1 - y0) * k0); p1 = (x0 + (x1 - x0) * k1, y0 + (y1 - y0) * k1)
            if not out: out.append(p0)
            out.append(p1)
        d += s
    return out
def mkpath(pts, close=False):
    p = skia.Path()
    for i, (x, y) in enumerate(pts):
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    if close: p.close()
    return p
def line(c, pts, color, w=3.0, a=1.0, dash=None, phase=0.0, cap='round', blur=0.0):
    if a <= 0.003 or len(pts) < 2: return
    p = skia.Paint(AntiAlias=True, Color=rgba(color, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == 'round' else skia.Paint.kButt_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(list(dash), phase))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawPath(mkpath(pts), p)
def arrow(c, pts, color, prog=1.0, w=7.0, a=1.0, head=22.0, dash=None, glow=True, outline=True):
    """沿折线推进的箭头。"""
    if a <= 0.003 or prog <= 0.002: return
    seg = trim(pts, 0, prog)
    if len(seg) < 2: return
    x, y, ang = along(pts, prog)
    body = trim(pts, 0, max(0.0, prog - head * 0.8 / max(1.0, plen(pts))))
    if glow: line(c, seg, color, w * 2.6, 0.22 * a, blur=w * 1.2)
    if len(body) >= 2:
        if outline: line(c, body, INK, w + 4, 0.55 * a, dash=dash, cap='butt' if dash else 'round')
        line(c, body, color, w, a, dash=dash, cap='butt' if dash else 'round')
    hp = skia.Path(); hw = head * 0.62
    hp.moveTo(x, y); hp.lineTo(x - head * math.cos(ang) + hw * math.sin(ang), y - head * math.sin(ang) - hw * math.cos(ang))
    hp.lineTo(x - head * 0.72 * math.cos(ang), y - head * 0.72 * math.sin(ang))
    hp.lineTo(x - head * math.cos(ang) - hw * math.sin(ang), y - head * math.sin(ang) + hw * math.cos(ang)); hp.close()
    if outline: c.drawPath(hp, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.55 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=4))
    c.drawPath(hp, skia.Paint(AntiAlias=True, Color=rgba(color, a)))

def circle(c, x, y, r, color, a=1.0, stroke=0.0, blur=0.0):
    if a <= 0.003 or r <= 0: return
    p = skia.Paint(AntiAlias=True, Color=rgba(color, a))
    if stroke: p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawCircle(x, y, r, p)
def glow(c, x, y, r, color, a=1.0):
    if a <= 0.003: return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((x, y), r, [rgba(color, 0.85 * a), rgba(color, 0.25 * a), rgba(color, 0.0)], [0.0, 0.45, 1.0]))
    p.setBlendMode(skia.BlendMode.kPlus); c.drawCircle(x, y, r, p)
def pulse(c, x, y, t, color, r0=14, r1=70, period=1.8, a=1.0, n=2, w=3.0):
    for i in range(n):
        u = ((t / period) + i / n) % 1.0
        circle(c, x, y, lerp(r0, r1, u), color, a * (1 - u) ** 1.5 * 0.9, stroke=w)

# ---- 地图元素 ----
def city(c, x, y, name, fac=None, a=1.0, size=30, major=False, dx=14, dy=10, anchor='l', sub=None, dim=False):
    """城邑：方框城标 + 宋体标签。fac 决定颜色。"""
    if a <= 0.003: return
    col = FAC[fac][0] if fac else '#D8D2C4'; dk = FAC[fac][1] if fac else '#2A2A2A'
    r = 9 if major else 6.5
    if dim: a *= 0.55
    rrect(c, x - r - 2.5, y - r - 2.5, 2 * r + 5, 2 * r + 5, 2.5, INK, 0.75 * a)
    rrect(c, x - r, y - r, 2 * r, 2 * r, 1.5, col, a)
    rrect(c, x - r * 0.45, y - r * 0.45, r * 0.9, r * 0.9, 1, dk, a)
    if name:
        lx = x + dx if anchor == 'l' else x - dx if anchor == 'r' else x
        ly = y + dy if anchor != 'c' else y + dy
        text(c, name, lx, ly, size, PAPER, 'serifx' if major else 'serif', a, anchor, stroke=5, shadow=6)
        if sub:
            text(c, sub, lx, ly + size * 0.95, size * 0.62, '#D9D2C2', 'sansm', a * 0.95, anchor, stroke=4, shadow=4)

def unit(c, x, y, fac, name=None, a=1.0, s=1.0, kind='army', sub=None, label_side='r', strength=1.0, flag=None):
    """部队标识：阵营色方块 + 兵种符号（步骑=交叉线，水军=船形）。名称标签跟随。"""
    if a <= 0.003: return
    col, dk, lt = FAC[fac]
    w, h = 62 * s, 42 * s
    c.save(); c.translate(x, y)
    rrect(c, -w / 2 - 3, -h / 2 + 5, w + 6, h + 4, 5 * s, '#000000', 0.5 * a, blur=8)
    if kind == 'fleet':
        p = skia.Path(); p.moveTo(-w / 2, -h * 0.30); p.lineTo(w / 2, -h * 0.30); p.lineTo(w * 0.34, h * 0.46); p.lineTo(-w * 0.34, h * 0.46); p.close()
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=7 * s))
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(col, a)))
        c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(lt, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.2 * s))
        # 帆
        sp = skia.Path(); sp.moveTo(0, -h * 0.30); sp.lineTo(0, -h * 0.95); sp.lineTo(w * 0.30, -h * 0.36); sp.close()
        c.drawPath(sp, skia.Paint(AntiAlias=True, Color=rgba(flag or PAPER, a)))
        c.drawPath(sp, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.8 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6 * s))
        line(c, [(-w * 0.22, h * 0.10), (w * 0.22, h * 0.10)], lt, 2.2 * s, 0.8 * a)
    else:
        rrect(c, -w / 2 - 3, -h / 2 - 3, w + 6, h + 6, 5 * s, INK, 0.9 * a)
        rrect(c, -w / 2, -h / 2, w, h, 3 * s, col, a)
        if strength < 1.0:
            rrect(c, -w / 2 + w * strength, -h / 2, w * (1 - strength), h, 3 * s, '#15171A', 0.72 * a)
        rrect(c, -w / 2, -h / 2, w, h, 3 * s, lt, 0.0, stroke=lt, sw=2.0 * s) if False else None
        p = skia.Paint(AntiAlias=True, Color=rgba(lt, 0.95 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.4 * s)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), 3 * s, 3 * s), p)
        c.drawLine(-w / 2, -h / 2, w / 2, h / 2, p); c.drawLine(-w / 2, h / 2, w / 2, -h / 2, p)
    c.restore()
    if name:
        fs = 27 * (0.85 + 0.15 * s)
        tx = x + (w / 2 + 12 if label_side == 'r' else -w / 2 - 12 if label_side == 'l' else 0)
        ty = y + (9 if label_side in 'lr' else (-h / 2 - 14 if label_side == 't' else h / 2 + 32))
        anc = 'l' if label_side == 'r' else 'r' if label_side == 'l' else 'c'
        text(c, name, tx, ty, fs, lt, 'sans', a, anc, stroke=5, shadow=5)
        if sub: text(c, sub, tx, ty + fs * 0.98, fs * 0.72, '#E4DDCF', 'sansm', a * 0.95, anc, stroke=4, shadow=4)

def tag(c, x, y, s, color=GOLD, a=1.0, size=24, anchor='l', fill='#0B0D10', fa=0.82, fname='sans', padx=12, pady=7, tcol=None):
    """小标签牌。x,y 为左上（anchor=l）。"""
    if a <= 0.003: return 0
    w = tw(s, fname, size) + padx * 2; h = size + pady * 2
    x0 = x - (w / 2 if anchor == 'c' else w if anchor == 'r' else 0)
    rrect(c, x0, y, w, h, 5, fill, fa * a)
    rrect(c, x0, y, 5, h, 2, color, a)
    text(c, s, x0 + padx + 2, y + pady + size * 0.86, size, tcol or PAPER, fname, a)
    return w

def beacon(c, x, y, lit, t, a=1.0, s=1.0):
    """江边屯候：小望楼 + 灯火。lit∈[0,1]。"""
    if a <= 0.003: return
    col = mix('#5B5F63', AMBER, lit)
    if lit > 0.02:
        fl = 0.85 + 0.15 * math.sin(t * 9 + x * 0.05)
        glow(c, x, y - 12 * s, 34 * s * fl, AMBER, 0.75 * lit * a)
    p = skia.Path(); p.moveTo(x - 7 * s, y + 8 * s); p.lineTo(x - 4.5 * s, y - 6 * s); p.lineTo(x + 4.5 * s, y - 6 * s); p.lineTo(x + 7 * s, y + 8 * s); p.close()
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(INK, 0.9 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=4 * s))
    c.drawPath(p, skia.Paint(AntiAlias=True, Color=rgba(mix('#3A3D40', LIU, lit), a)))
    circle(c, x, y - 11 * s, 5.2 * s, INK, 0.9 * a); circle(c, x, y - 11 * s, 3.8 * s, col, a)
    if lit < 0.5:
        k = (0.5 - lit) * 2 * a
        line(c, [(x - 8 * s, y - 16 * s), (x + 8 * s, y + 6 * s)], SUN_L, 2.6 * s, k)
        line(c, [(x + 8 * s, y - 16 * s), (x - 8 * s, y + 6 * s)], SUN_L, 2.6 * s, k)

# ---- 引文卡 ----
LEVEL_COL = {'正史': '#E6CC8F', '裴注': '#9FC3D8', '注家': '#C9B6E0', '解读': '#F2A93B', '演义': '#D9776A', '经典': '#E6CC8F'}
LEVEL_TXT = {'正史': '正史 · 《三国志》正文', '裴注': '裴注 · 裴松之注所引', '注家': '注家评断', '解读': '本集解读', '演义': '《三国演义》情节', '经典': '经典'}
def cite_card(c, cite, a=1.0, y=1040, x=64, w=872, big=False):
    """引文卡：层级徽标 + 出处 + 原文（宋体）+ 校记。返回高度。"""
    if a <= 0.003: return 0
    col = LEVEL_COL[cite['level']]; qs = 42 if not big else 50
    pad = 28; lines = []
    for part in cite['q'].split('／'):
        lines += wrap(part.strip(), 'serif', qs, w - pad * 2 - 10)
        lines.append(None)
    lines = lines[:-1]
    note = cite.get('note')
    gl = wrap('白话｜' + cite['gloss'], 'sansm', 29, w - pad * 2 - 10) if cite.get('gloss') else []
    hq = sum(qs * 1.42 if l is not None else qs * 0.35 for l in lines)
    h = 64 + hq + (46 if note else 14) + 10 + len(gl) * 40
    yy = y - (1 - ss(a)) * -14
    panel(c, x, yy, w, h, a, r=8, fa=0.84)
    rrect(c, x, yy, 7, h, 3, col, a)
    # 徽标
    bw = tw(LEVEL_TXT[cite['level']], 'sans', 22) + 22
    rrect(c, x + pad, yy + 18, bw, 34, 4, col, 0.95 * a)
    text(c, LEVEL_TXT[cite['level']], x + pad + 11, yy + 18 + 25, 22, INK, 'sans', a)
    text(c, cite['src'], x + pad + bw + 14, yy + 18 + 26, 25, '#D9D2C2', 'serifm', a)
    ty = yy + 64 + qs * 1.0
    for l in lines:
        if l is None: ty += qs * 0.35; continue
        text(c, l, x + pad + 4, ty, qs, PAPER if cite['level'] != '正史' else '#F6EBCB', 'serif', a); ty += qs * 1.42
    for l in gl:
        ty += 4; text(c, l, x + pad + 4, ty, 29, '#CFC8B8', 'sansm', a); ty += 40
    if note:
        text(c, note, x + pad + 4, yy + h - 20, 23, '#B7B0A2', 'sansm', a)
    return h

# ---- 字幕 ----
def subtitle(c, s, a=1.0, quote=False, y=1418):
    if a <= 0.003 or not s: return
    size = 50; fname = 'serifx' if quote else 'sans'
    col = '#F3DFA6' if quote else '#FFFFFF'
    maxw = 850; cx = 498
    w = tw(s, fname, size)
    if w <= maxw: lines = [s]
    elif w <= maxw * 1.16:
        size = size * maxw / w; lines = [s]
    else:
        # 两行：在最接近中点的标点后断开
        best = None
        for i, ch in enumerate(s[:-1]):
            if ch in '，。；：、？！':
                d = abs(tw(s[:i + 1], fname, size) - w / 2)
                if best is None or d < best[0]: best = (d, i + 1)
        k = best[1] if best and best[0] < w * 0.22 else len(s) // 2
        lines = [s[:k].rstrip('，'), s[k:]]
        mw = max(tw(l, fname, size) for l in lines)
        if mw > maxw: size = size * maxw / mw
    y0 = y - (len(lines) - 1) * size * 1.32
    for i, l in enumerate(lines):
        text(c, l, cx, y0 + i * size * 1.32, size, col, fname, a, 'c', stroke=7, shadow=8)

# ---- 整屏效果 ----
_vig = None
def vignette(c, a=1.0):
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        dx = (xx - W / 2) / (W / 2); dy = (yy - H * 0.46) / (H / 2)
        d = np.sqrt(dx * dx * 0.85 + dy * dy * 0.70)
        al = np.clip((d - 0.62) / 0.80, 0, 1) ** 1.7 * 0.50
        al += np.random.default_rng(1).uniform(-0.004, 0.004, al.shape)   # 抖动，防色带
        arr = np.zeros((H, W, 4), np.uint8); arr[..., 3] = (np.clip(al, 0, 1) * 255).astype(np.uint8)
        _vig = skia.Image.fromarray(arr, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    c.drawImage(_vig, 0, 0)
_grain = None
def grain(c, fi, a=0.024):
    """胶片颗粒：预生成 6 张全幅颗粒图轮换（每 2 帧换一张），直接叠加。"""
    global _grain
    if _grain is None:
        rng = np.random.default_rng(7); _grain = []
        for k in range(6):
            n = rng.normal(0, 1, (H // 2 + 1, W // 2 + 1)).astype(np.float32)
            n = (n + np.roll(n, 1, 0) * 0.35 + np.roll(n, 1, 1) * 0.35) / 1.25
            n = np.kron(n, np.ones((2, 2), np.float32))[:H, :W]
            al = np.clip(np.abs(n) * a * 1.9, 0, 0.5)
            v = (n > 0).astype(np.float32)
            arr = np.zeros((H, W, 4), np.float32); arr[..., 0] = arr[..., 1] = arr[..., 2] = v * al * 255; arr[..., 3] = al * 255
            _grain.append(skia.Image.fromarray(arr.astype(np.uint8), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c.drawImage(_grain[(fi // 2) % 6], 0, 0)
def dim(c, a, color='#06070A'):
    if a <= 0.003: return
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=rgba(color, a)))
def top_grad(c, a=1.0):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 420)], [rgba('#000000', 0.62 * a), rgba('#000000', 0.0)]))
    c.drawRect(skia.Rect.MakeWH(W, 420), p)
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, 1180), (0, 1920)], [rgba('#000000', 0.0), rgba('#000000', 0.80 * a)]))
    c.drawRect(skia.Rect.MakeXYWH(0, 1180, W, 740), p)
