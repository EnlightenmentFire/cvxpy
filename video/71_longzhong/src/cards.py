# -*- coding: utf-8 -*-
"""本期卡片：古文卡（层级角标、出处右下、白话一行）、现代类比卡＋类比偏差、起家三问卡、演义/史书两行对照、排序卡、大字。"""
import math, skia
from gfx import *

# 史料层级角标（颜色区分层级）
LAYER = {
    'zheng': ('①《三国志》正文', '#E6CC8F'),
    'zishu': ('①《三国志》所载 · 当事人自述', '#F1D68E'),
    'pei': ('② 裴松之注所引', '#9FC3D8'),
    'pei_an': ('② 裴松之按语', '#9FC3D8'),
    'ji': ('《襄阳记》后人辑本', '#B8B0C9'),
    'yanyi': ('⑤《三国演义》（明代小说）', '#C98B7E'),
}
X0, CW = 60, 960


def quote_card(c, q, src, layer, a=1.0, y=980, baihua=None, ba=None, size=50, w=CW, x=X0, hl=None, hla=0.0):
    """古文卡：深色半透明底、金色细描边、宋体（繁体）原文、右下出处；卡下一行白话。返回卡底 y。
    hl: 需要高亮（加金色底纹）的子串；hla 高亮强度。"""
    if a <= 0.003: return y
    lab, col = LAYER[layer]
    pad = 34
    lines = []
    for part in q.split('\n'):
        lines += wrap(part, 'tc', size, w - pad * 2)
    lh = size * 1.45
    h = 70 + len(lines) * lh + 58
    yy = y + (1 - ease(min(1, a * 1.4))) * 18
    panel(c, x, yy, w, h, a, r=6, fill='#0A0C0F', fa=0.80, edge=col, ea=0.55)
    # 角标：左上小方签（描边，不用胶囊）
    bw = tw(lab, 'sansm', 23) + 24
    rrect(c, x + pad - 6, yy + 20, bw, 36, 3, col, 0.16 * a)
    rrect(c, x + pad - 6, yy + 20, bw, 36, 3, col, a * 0.9, stroke=col, sw=1.4) if False else None
    p = skia.Paint(AntiAlias=True, Color=rgba(col, 0.85 * a), Style=skia.Paint.kStroke_Style, StrokeWidth=1.4)
    c.drawRect(skia.Rect.MakeXYWH(x + pad - 6, yy + 20, bw, 36), p)
    text(c, lab, x + pad + 6, yy + 20 + 27, 23, col, 'sansm', a)
    ty = yy + 70 + size * 1.08
    for l in lines:
        if hl and hla > 0.01 and hl in l:
            i = l.index(hl); x1 = x + pad + tw(l[:i], 'tc', size); ww = tw(hl, 'tc', size)
            rrect(c, x1 - 4, ty - size * 0.95, ww * ss(hla) + 8, size * 1.25, 3, GOLD, 0.22 * a)
            line(c, [(x1, ty + size * 0.22), (x1 + ww * ss(hla), ty + size * 0.22)], GOLD, 3, 0.9 * a)
        text(c, l, x + pad, ty, size, '#F6ECCF', 'tc', a, shadow=3)
        ty += lh
    text(c, '—— ' + src, x + w - pad, yy + h - 24, 27, '#CFC6B2', 'tcm', a, 'r')
    yb = yy + h
    if baihua:
        ba = a if ba is None else ba
        ls = wrap(baihua, 'sansm', 34, w - 70)
        for i, l in enumerate(ls):
            text(c, ('白话｜' if i == 0 else '　　　') + l, x + 8, yb + 50 + i * 46, 34, '#E9E3D6', 'sansm', ba, stroke=5, shadow=5)
        yb += 50 + len(ls) * 46
    return yb


def analogy_card(c, body, bias=None, a=1.0, ab=0.0, y=900, x=X0, w=CW, head='现代类比'):
    """现代类比卡：独立标签，不与史料卡混排；下方一行“类比偏差”（细描边标签，不用黄色三角牌）。"""
    if a <= 0.003: return y
    pad = 36; size = 40
    bl = wrap(body, 'sansm', size, w - pad * 2)
    bias_l = wrap(bias, 'sansm', 33, w - pad * 2 - 4) if bias else []
    h = 92 + len(bl) * size * 1.5 + (40 + 58 + len(bias_l) * 33 * 1.5 if bias else 12)
    yy = y + (1 - ease(min(1, a * 1.4))) * 18
    panel(c, x, yy, w, h, a, r=10, fill='#0E1620', fa=0.86, edge='#8FB3D9', ea=0.35)
    # 标签
    lw = tw(head, 'sans', 26) + 30
    rrect(c, x + pad - 4, yy + 26, lw, 42, 4, '#5C86B5', a)
    text(c, head, x + pad + 11, yy + 26 + 31, 26, '#FFFFFF', 'sans', a)
    ty = yy + 92 + size * 1.02
    for l in bl:
        text(c, l, x + pad, ty, size, '#F2F5F8', 'sansm', a); ty += size * 1.5
    if bias:
        k = a * ab
        line(c, [(x + pad, ty - size * 0.6 + 10), (x + w - pad, ty - size * 0.6 + 10)], '#8FB3D9', 1.2, 0.30 * a)
        by = ty + 4
        lab = '类比偏差'
        lw2 = tw(lab, 'sans', 25) + 26
        p = skia.Paint(AntiAlias=True, Color=rgba('#E8A867', 0.95 * k), Style=skia.Paint.kStroke_Style, StrokeWidth=1.8)
        c.drawRect(skia.Rect.MakeXYWH(x + pad, by, lw2, 40), p)
        text(c, lab, x + pad + 13, by + 29, 25, '#F0B57A', 'sans', k)
        ty2 = by + 40 + 22 + 33
        for l in bias_l:
            text(c, l, x + pad + 2, ty2, 33, '#EBD9C2', 'sansm', k); ty2 += 33 * 1.5
    return yy + h


def q3_card(c, rows, a=1.0, y=560, x=X0, w=CW, sub='刘备 · 建安十二年（207）前后 · 新野'):
    """起家三问卡（系列固定样式）。rows: [(问题, [答案行...], 可见度)]"""
    if a <= 0.003: return
    pad = 40
    hs = [96 + len(r[1]) * 50 for r in rows]
    h = 150 + sum(hs) + 20
    panel(c, x, y, w, h, a, r=10, fill='#120D0B', fa=0.88, edge=GOLD, ea=0.5)
    rrect(c, x, y, w, 8, 3, LIU, a)
    text(c, '起家三问', x + pad, y + 78, 54, GOLD, 'serifx', a)
    text(c, sub, x + pad + tw('起家三问', 'serifx', 54) + 24, y + 74, 27, '#CDBFA6', 'sansm', a)
    yy = y + 130
    for i, (q, ans, ra) in enumerate(rows):
        k = a * ra
        circle(c, x + pad + 22, yy + 36, 22, LIU, k)
        text(c, '一二三'[i], x + pad + 22, yy + 47, 28, '#FFFFFF', 'serifx', k, 'c')
        text(c, q, x + pad + 62, yy + 48, 38, '#F3DFA6', 'serif', k)
        ay = yy + 48 + 52
        for l in ans:
            text(c, l, x + pad + 62, ay, 32, '#F2EEE6', 'sansm', k); ay += 50
        yy += hs[i]
        if i < len(rows) - 1:
            line(c, [(x + pad, yy - 10), (x + w - pad, yy - 10)], GOLD, 1, 0.22 * a)


def yanyi_card(c, yan, shi, a=1.0, a2=1.0, y=900, x=X0, w=CW):
    """演义说……／史书说……两行对照（上下两行，不做左右分栏）。"""
    if a <= 0.003: return
    pad = 36
    l1 = wrap(yan, 'sansm', 36, w - pad * 2 - 150); l2 = wrap(shi, 'sansm', 36, w - pad * 2 - 150)
    h = 60 + len(l1) * 54 + 40 + len(l2) * 54 + 40
    panel(c, x, y, w, h, a, r=8, fa=0.84)
    ty = y + 66
    rrect(c, x + pad, ty - 34, 118, 46, 4, '#7E3B33', a)
    text(c, '演义说', x + pad + 59, ty - 1, 28, '#F6D9D2', 'sans', a, 'c')
    for l in l1:
        text(c, l, x + pad + 140, ty, 36, '#E7D4CF', 'sansm', a); ty += 54
    ty += 40
    k = a * a2
    rrect(c, x + pad, ty - 34, 118, 46, 4, '#8A6D2E', k)
    text(c, '史书说', x + pad + 59, ty - 1, 28, '#FFF1C9', 'sans', k, 'c')
    for l in l2:
        text(c, l, x + pad + 140, ty, 36, '#FFF6E0', 'sansm', k); ty += 54


def big(c, s, y, size=96, color=PAPER, a=1.0, fname='serifx', x=540, anchor='c', stroke=8, shadow=14, spacing=0.0):
    text(c, s, x, y, size, color, fname, a, anchor, stroke=stroke, shadow=shadow, spacing=spacing)


def section_tag(c, s, a=1.0):
    """左上章节签。"""
    if a <= 0.003: return
    rrect(c, 52, 150, 6, 50, 2, LIU, a)
    text(c, s, 72, 188, 34, '#F3EEE4', 'serif', a, stroke=5, shadow=6)


def corner(c, a=1.0, map_on=0.0):
    """常驻角标：AI 配音；地图出现时标“地图示意”。"""
    tag(c, 1028, 150, 'AI配音', '#8C8C8C', a * 0.85, size=20, anchor='r', fa=0.55, fname='sansm', padx=9, pady=5)
    if map_on > 0.01:
        tag(c, 1028, 192, '地图示意', '#8C8C8C', a * map_on * 0.85, size=20, anchor='r', fa=0.55, fname='sansm', padx=9, pady=5)


def lock_icon(c, x, y, s=1.0, a=1.0, col='#B9BEC4'):
    """灰色锁形。"""
    if a <= 0.003: return
    p = skia.Paint(AntiAlias=True, Color=rgba(col, a), Style=skia.Paint.kStroke_Style, StrokeWidth=9 * s)
    c.drawArc(skia.Rect.MakeLTRB(x - 26 * s, y - 62 * s, x + 26 * s, y - 6 * s), 180, 180, False, p)
    c.drawLine(x - 26 * s, y - 34 * s, x - 26 * s, y - 14 * s, p); c.drawLine(x + 26 * s, y - 34 * s, x + 26 * s, y - 14 * s, p)
    rrect(c, x - 42 * s, y - 18 * s, 84 * s, 66 * s, 8 * s, '#000000', 0.5 * a, blur=10)
    rrect(c, x - 40 * s, y - 20 * s, 80 * s, 64 * s, 8 * s, col, a)
    circle(c, x, y + 6 * s, 9 * s, '#2A2D31', a)
    rrect(c, x - 3.5 * s, y + 8 * s, 7 * s, 20 * s, 2, '#2A2D31', a)
