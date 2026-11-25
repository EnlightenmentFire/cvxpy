# -*- coding: utf-8 -*-
"""版式组件：古文卡、现代类比卡、类比偏差、起家三问卡、演义对照、章节卡、角标。"""
import math, skia
from gfx import *
from geo import W, H

GOLDL = '#D8B66A'
LEVEL = {'正史': ('正史', '#E2C27A'), '裴注': ('裴注', '#A9C6DA'), '评': ('正史·评', '#E2C27A')}

def _lines(s, fname, size, maxw):
    out = []
    for part in s.split('\n'): out += wrap(part, fname, size, maxw)
    return out

def quote_card(c, q, a=1.0, y=1010, reveal=1.0):
    """古文卡：深色半透明底、金描边、宋体原文、右下出处，下接一行白话。q: orig, src, level, bh。"""
    if a <= 0.003: return 0
    x, w = 56, 968; pad = 40
    qs = q.get('size', 54 if len(q['orig']) <= 22 else 48 if len(q['orig']) <= 40 else 44)
    L = _lines(q['orig'], 'serifx', qs, w - pad * 2)
    bh = q.get('bh'); BL = _lines(bh, 'sansm', 33, w - pad * 2) if bh else []
    h = 74 + len(L) * qs * 1.36 + 54 + (len(BL) * 33 * 1.45 + 30 if BL else 0) + 18
    yy = y + (1 - ease(a)) * 26
    # 底
    rrect(c, x, yy + 8, w, h, 6, '#000000', 0.55 * a, blur=22)
    rrect(c, x, yy, w, h, 6, '#0A0A0D', 0.80 * a)
    p = skia.Paint(AntiAlias=True, Color=rgba(GOLDL, 0.85 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 1, yy + 1, w - 2, h - 2), 6, 6), p)
    p2 = skia.Paint(AntiAlias=True, Color=rgba(GOLDL, 0.30 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 9, yy + 9, w - 18, h - 18), 3, 3), p2)
    # 层级角标
    lab, lc = LEVEL[q.get('level', '正史')]
    text(c, lab, x + pad, yy + 50, 24, lc, 'sans', a, spacing=3)
    lw = tw(lab, 'sans', 24) + 3 * len(lab) + 14
    line(c, [(x + pad + lw, yy + 41), (x + pad + lw + 60, yy + 41)], lc, 1.4, 0.6 * a)
    # 原文（逐字显现）
    ty = yy + 74 + qs * 1.02
    total = sum(len(l) for l in L); shown = int(round(total * clamp(reveal))) if reveal < 1 else total; k = 0
    for l in L:
        vis = l[:max(0, min(len(l), shown - k))]; k += len(l)
        text(c, vis, x + pad, ty, qs, '#F4E6C2', 'serifx', a, shadow=4)
        ty += qs * 1.36
    # 出处（右下）
    text(c, '—— ' + q['src'], x + w - pad, ty + 6, 27, '#CDBF9C', 'serifm', a, 'r')
    ty += 30
    if BL:
        line(c, [(x + pad, ty + 4), (x + w - pad, ty + 4)], '#FFFFFF', 1.0, 0.14 * a)
        ty += 40 + 2
        for l in BL:
            text(c, l, x + pad, ty + 4, 33, '#ECE6DA', 'sansm', a); ty += 33 * 1.45
    return h

def analogy_card(c, body, a=1.0, y=980, bias=None, ab=0.0):
    """现代类比卡（与古文卡分开），下方紧跟一行「类比偏差」。"""
    if a <= 0.003: return
    x, w, pad = 56, 968, 36
    L = _lines(body, 'sansm', 38, w - pad * 2)
    h = 70 + len(L) * 38 * 1.45 + 18
    yy = y + (1 - ease(a)) * 24
    rrect(c, x, yy + 8, w, h, 14, '#000000', 0.5 * a, blur=20)
    rrect(c, x, yy, w, h, 14, '#101820', 0.86 * a)
    p = skia.Paint(AntiAlias=True, Color=rgba('#8FB6D0', 0.7 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 1, yy + 1, w - 2, h - 2), 14, 14), p)
    tw0 = tw('现代类比', 'sans', 26) + 30
    rrect(c, x + pad, yy + 20, tw0, 40, 20, '#8FB6D0', 0.95 * a)
    text(c, '现代类比', x + pad + 15, yy + 49, 26, '#0B1218', 'sans', a)
    ty = yy + 70 + 38 * 1.05
    for l in L:
        text(c, l, x + pad, ty, 38, '#F2F5F7', 'sansm', a); ty += 38 * 1.45
    if bias and ab > 0.003:
        bias_card(c, bias, ab, yy + h + 18)
    return h

def bias_card(c, body, a=1.0, y=1300):
    if a <= 0.003: return
    x, w, pad = 56, 968, 34
    L = _lines(body, 'sansm', 32, w - pad * 2 - 150)
    h = max(84, 34 + len(L) * 32 * 1.45 + 14)
    yy = y + (1 - ease(a)) * 18
    rrect(c, x, yy + 6, w, h, 10, '#000000', 0.45 * a, blur=16)
    rrect(c, x, yy, w, h, 10, '#1A0F0E', 0.88 * a)
    rrect(c, x, yy, 8, h, 3, '#E0573F', a)
    text(c, '类比偏差', x + pad, yy + 50, 29, '#FF8C72', 'sans', a)
    ty = yy + 34 + 32 * 0.95
    for l in L:
        text(c, l, x + pad + 150, ty, 32, '#F1E6E2', 'sansm', a); ty += 32 * 1.45

def q3_card(c, rows, a=1.0, y=560, prog=(1, 1, 1)):
    """起家三问卡：rows=[(问, 答), ...]，prog 每行显现度。"""
    if a <= 0.003: return
    x, w, pad = 56, 968, 40
    yy = y + (1 - ease(a)) * 24
    hs = []
    for qq, ans in rows: hs.append(64 + len(_lines(ans, 'sansm', 36, w - pad * 2 - 20)) * 36 * 1.45 + 26)
    h = 120 + sum(hs) + 20
    rrect(c, x, yy + 10, w, h, 8, '#000000', 0.55 * a, blur=24)
    rrect(c, x, yy, w, h, 8, '#0D0B0A', 0.88 * a)
    p = skia.Paint(AntiAlias=True, Color=rgba(LIU, 0.85 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2.2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 1, yy + 1, w - 2, h - 2), 8, 8), p)
    # 标题：朱印
    rrect(c, x + pad, yy + 28, 66, 66, 6, LIU, a)
    text(c, '起', x + pad + 33, yy + 76, 44, '#FFF1E4', 'serifx', a, 'c')
    text(c, '起家三问', x + pad + 90, yy + 76, 50, '#F4E6C2', 'serifx', a, spacing=6)
    text(c, '五十岁 · 葭萌', x + w - pad, yy + 72, 28, '#BFA98A', 'sansm', a, 'r')
    ty = yy + 120
    for i, ((qq, ans), hh) in enumerate(zip(rows, hs)):
        pa = ease(prog[i]) * a
        line(c, [(x + pad, ty), (x + w - pad, ty)], '#FFFFFF', 1, 0.12 * a)
        text(c, f'{"一二三"[i]}  {qq}', x + pad, ty + 50, 34, LIU_L, 'sans', a * (0.45 + 0.55 * ease(prog[i])))
        yl = ty + 50 + 36 * 1.35
        for l in _lines(ans, 'sansm', 36, w - pad * 2 - 20):
            text(c, l, x + pad + 20 + (1 - pa / max(a, 1e-3)) * 20, yl, 36, '#F2EEE6', 'sansm', pa); yl += 36 * 1.45
        ty += hh

def yanyi_card(c, yy_txt, sh_txt, a=1.0, y=980, b=1.0):
    """演义 vs 史书：固定两行对照。"""
    if a <= 0.003: return
    x, w, pad = 56, 968, 36
    L1 = _lines(yy_txt, 'sansm', 35, w - pad * 2 - 150); L2 = _lines(sh_txt, 'sansm', 35, w - pad * 2 - 150)
    h = 40 + len(L1) * 35 * 1.45 + 34 + len(L2) * 35 * 1.45 + 30
    yy = y + (1 - ease(a)) * 22
    rrect(c, x, yy + 8, w, h, 8, '#000000', 0.5 * a, blur=20)
    rrect(c, x, yy, w, h, 8, '#0C0C0E', 0.86 * a)
    ty = yy + 40 + 35
    text(c, '演义说', x + pad, ty, 34, '#9A9590', 'sans', a)
    for l in L1: text(c, l, x + pad + 150, ty, 35, '#B9B4AD', 'sansm', a); ty += 35 * 1.45
    line(c, [(x + pad, ty - 18), (x + w - pad, ty - 18)], '#FFFFFF', 1, 0.12 * a)
    ty += 34
    ab = a * ease(b)
    text(c, '史书说', x + pad, ty, 34, GOLDL, 'sans', ab)
    for l in L2: text(c, l, x + pad + 150, ty, 35, '#F4E6C2', 'sansm', ab); ty += 35 * 1.45

def chapter_card(c, sec, u, info):
    """章节卡：朱印编号 + 大字标题 + 副题。u∈[0,1] 为卡片内进度。"""
    num, title, sub = info
    a = ss(ramp(u, 0, 0.18)) * (1 - ss(ramp(u, 0.82, 1.0)))
    if a <= 0.003: return
    dim(c, 0.80 * a)
    cx, cy = W / 2, 820
    s = 1.0 + 0.06 * (1 - eout(ramp(u, 0, 0.4)))
    c.save(); c.translate(cx, cy); c.scale(s, s); c.translate(-cx, -cy)
    rrect(c, cx - 62, cy - 210, 124, 124, 10, LIU, a)
    p = skia.Paint(AntiAlias=True, Color=rgba('#FFE9DA', 0.5 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=2)
    c.drawRect(skia.Rect.MakeXYWH(cx - 52, cy - 200, 104, 104), p)
    text(c, num, cx, cy - 122, 76, '#FFF4EA', 'serifx', a, 'c')
    text(c, title, cx, cy + 60, 132, '#F6EAD0', 'serifx', a, 'c', shadow=14, spacing=18)
    line(c, [(cx - 220 * eout(ramp(u, 0.1, 0.5)), cy + 110), (cx + 220 * eout(ramp(u, 0.1, 0.5)), cy + 110)], GOLDL, 2, 0.8 * a)
    text(c, sub, cx, cy + 176, 46, '#E2D2AE', 'serifm', a, 'c', shadow=8)
    c.restore()

def corner(c, a=1.0, note='地图为示意'):
    """右上角标：AI 配音、程序生成画面。左下角：地图示意。"""
    tag(c, W - 28, 96, 'AI配音 · 画面为程序生成', '#8FB6D0', 0.85 * a, 21, 'r', fa=0.55, fname='sansm', padx=10, pady=5)
    if note: text(c, note, 40, 1880, 22, '#CFC7B8', 'sansm', 0.7 * a)

def date_tag(c, s, a=1.0, sub=None):
    if a <= 0.003: return
    rrect(c, 40, 88, 6, 46 if not sub else 80, 2, LIU, a)
    text(c, s, 60, 124, 36, '#F4E6C2', 'serifx', a, shadow=6, stroke=4)
    if sub: text(c, sub, 60, 162, 26, '#D8CFBE', 'sansm', a, shadow=4, stroke=3)

def big_caption(c, s, a=1.0, y=760, size=150, color='#F6E7C8', glow_col=LIU, spacing=24, sub=None):
    """大字（书法感）标题：描边 + 外发光。"""
    if a <= 0.003: return
    f = font('serifx', size)
    w = sum(f.measureText(ch) for ch in s) + spacing * (len(s) - 1)
    x0 = W / 2 - w / 2
    p = skia.Paint(AntiAlias=True, Color=rgba(glow_col, 0.55 * a)); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
    xx = x0
    for ch in s: c.drawString(ch, xx, y, f, p); xx += f.measureText(ch) + spacing
    text(c, s, W / 2, y, size, color, 'serifx', a, 'c', stroke=8, stroke_color='#120806', spacing=spacing)
    if sub: text(c, sub, W / 2, y + size * 0.62, size * 0.24, '#E8DCC2', 'serifm', a, 'c', stroke=4, shadow=6)
