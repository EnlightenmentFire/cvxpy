"""Small pictograms used by the scenes (all flat, brown ink)."""
import math

import skia

from gfx import (ACCENT, CARD, INK, INK2, INK3, INK4, METAL, METAL_D, OCHRE, PAPER, SLATE, UMBER, _rrect,
                 col, draw_gear, draw_text, mix, paint, wobble_path)


def building_columns(c, x, y, s, rgb=INK2, a=1.0):
    """Government building: pediment + columns. (x,y) = bottom centre, s = width."""
    p = skia.Path()
    p.moveTo(x - s * 0.55, y - s * 0.62); p.lineTo(x, y - s * 0.9); p.lineTo(x + s * 0.55, y - s * 0.62); p.close()
    c.drawPath(p, paint(rgb, a))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.5, y - s * 0.62, s, s * 0.07), paint(rgb, a))
    for k in range(5):
        cx = x - s * 0.4 + k * s * 0.2
        c.drawRect(skia.Rect.MakeXYWH(cx - s * 0.045, y - s * 0.54, s * 0.09, s * 0.46), paint(rgb, a))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.56, y - s * 0.08, s * 1.12, s * 0.08), paint(rgb, a))


def office_tower(c, x, y, s, rgb=INK2, a=1.0):
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.28, y - s * 1.0, s * 0.56, s), paint(rgb, a))
    for i in range(6):
        for j in range(3):
            c.drawRect(skia.Rect.MakeXYWH(x - s * 0.21 + j * s * 0.15, y - s * 0.92 + i * s * 0.14, s * 0.09, s * 0.08),
                       paint(CARD, a))


def factory_icon(c, x, y, s, rgb=INK2, a=1.0, fill=None):
    p = skia.Path()
    p.moveTo(x - s * 0.5, y)
    p.lineTo(x - s * 0.5, y - s * 0.45)
    for k in range(3):
        x0 = x - s * 0.5 + k * s / 3
        p.lineTo(x0 + s / 3 * 0.8, y - s * 0.7)
        p.lineTo(x0 + s / 3 * 0.8, y - s * 0.45)
        p.lineTo(x0 + s / 3, y - s * 0.45)
    p.lineTo(x + s * 0.5, y)
    p.close()
    c.drawPath(p, paint(fill or rgb, a))
    c.drawRect(skia.Rect.MakeXYWH(x + s * 0.28, y - s * 0.95, s * 0.1, s * 0.5), paint(rgb, a))


def star(c, x, y, r, rgb=INK, a=1.0):
    p = skia.Path()
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        q = (x + math.cos(ang) * rr, y + math.sin(ang) * rr)
        if i == 0:
            p.moveTo(*q)
        else:
            p.lineTo(*q)
    p.close()
    c.drawPath(p, paint(rgb, a))


def notebook(c, x, y, w, h, a=1.0, prog=1.0, seed=0):
    """Open field notebook with scribbled lines (prog = how much is written)."""
    c.drawRRect(_rrect(x - w / 2 + 6, y - h / 2 + 8, w, h, 10), paint(INK, 0.15 * a, blur=6))
    c.drawRRect(_rrect(x - w / 2, y - h / 2, w, h, 10), paint(CARD, a))
    c.drawRRect(_rrect(x - w / 2, y - h / 2, w, h, 10), paint(INK2, a, stroke=2.5))
    c.drawLine(x, y - h / 2 + 6, x, y + h / 2 - 6, paint(INK3, a, stroke=2))
    nlines = 7
    total = nlines * 2
    for side in (0, 1):
        for k in range(nlines):
            idx = side * nlines + k
            pr = max(0.0, min(1.0, prog * total - idx))
            if pr <= 0:
                continue
            x0 = x - w / 2 + 30 if side == 0 else x + 24
            ln = (w / 2 - 54) * (0.65 + 0.3 * math.sin(idx * 1.7 + seed)) * pr
            yy = y - h / 2 + 46 + k * (h - 80) / nlines
            pts = []
            n = max(2, int(ln / 6))
            for i in range(n + 1):
                xx = x0 + ln * i / n
                pts.append((xx, yy + math.sin(i * 1.3 + idx) * 3.2 + math.sin(i * 0.37 + idx * 2) * 2))
            pth = skia.Path()
            pth.moveTo(*pts[0])
            for q in pts[1:]:
                pth.lineTo(*q)
            c.drawPath(pth, paint(INK2, a * 0.85, stroke=2.4))


def pen(c, x, y, s, a=1.0, ang=35):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.drawRRect(_rrect(-s * 0.06, -s, s * 0.12, s * 0.85, s * 0.05), paint(INK, a))
    p = skia.Path().moveTo(-s * 0.06, -s * 0.15).lineTo(s * 0.06, -s * 0.15).lineTo(0, 0).close()
    c.drawPath(p, paint(INK2, a))
    c.restore()


def book(c, x, y, w, h, title_lines, year, color, a=1.0, ang=0, title_font="garamond", size=30):
    c.save(); c.translate(x, y); c.rotate(ang)
    c.drawRRect(_rrect(-w / 2 + 8, -h / 2 + 10, w, h, 6), paint(INK, 0.18 * a, blur=7))
    c.drawRRect(_rrect(-w / 2, -h / 2, w, h, 4), paint(color, a))
    c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, 14, h), paint(mix(color, INK, 0.3), a))
    c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 34, -h / 2 + 40, w - 60, 3), paint(CARD, a * 0.9))
    yy = -h / 2 + 100
    for tl in title_lines:
        draw_text(c, tl, 7, yy, title_font, size, CARD, a, align="center", spacing=1.5)
        yy += size * 1.25
    c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 34, yy + 4, w - 60, 3), paint(CARD, a * 0.9))
    draw_text(c, year, 7, h / 2 - 50, "garamond", 30, CARD, a, align="center")
    c.restore()


def calendar(c, x, y, s, a=1.0, checks=0):
    c.drawRRect(_rrect(x - s / 2, y - s * 0.42, s, s * 0.84, 8), paint(CARD, a))
    c.drawRRect(_rrect(x - s / 2, y - s * 0.42, s, s * 0.84, 8), paint(INK2, a, stroke=2.5))
    c.drawRect(skia.Rect.MakeXYWH(x - s / 2, y - s * 0.42, s, s * 0.17), paint(INK2, a))
    for i in range(3):
        for j in range(4):
            cx, cy = x - s * 0.36 + j * s * 0.24, y - s * 0.12 + i * s * 0.17
            c.drawRect(skia.Rect.MakeXYWH(cx - s * 0.06, cy - s * 0.05, s * 0.12, s * 0.1), paint(INK4, a * 0.7))
            if i * 4 + j < checks:
                p = skia.Path().moveTo(cx - s * 0.05, cy).lineTo(cx - s * 0.01, cy + s * 0.04).lineTo(cx + s * 0.06, cy - s * 0.05)
                c.drawPath(p, paint(INK, a, stroke=3))


def coin(c, x, y, r, a=1.0):
    c.drawCircle(x, y, r, paint((196, 170, 110), a))
    c.drawCircle(x, y, r, paint(INK2, a, stroke=2))
    c.drawCircle(x, y, r * 0.62, paint(INK2, a * 0.6, stroke=1.4))


def clock(c, x, y, r, t, a=1.0):
    c.drawCircle(x, y, r, paint(CARD, a))
    c.drawCircle(x, y, r, paint(INK2, a, stroke=3))
    for k in range(12):
        ang = k * math.pi / 6
        c.drawLine(x + math.cos(ang) * r * 0.8, y + math.sin(ang) * r * 0.8, x + math.cos(ang) * r * 0.92,
                   y + math.sin(ang) * r * 0.92, paint(INK2, a, stroke=2))
    am = t * 1.6 - math.pi / 2
    ah = t * 0.13 - math.pi / 2 + 1.0
    c.drawLine(x, y, x + math.cos(am) * r * 0.78, y + math.sin(am) * r * 0.78, paint(INK, a, stroke=3))
    c.drawLine(x, y, x + math.cos(ah) * r * 0.5, y + math.sin(ah) * r * 0.5, paint(INK, a, stroke=4.5))
    c.drawCircle(x, y, 4, paint(INK, a))


def envelope(c, x, y, s, rgb=INK2, a=1.0):
    c.drawRRect(_rrect(x - s / 2, y - s * 0.32, s, s * 0.64, 4), paint(CARD, a))
    c.drawRRect(_rrect(x - s / 2, y - s * 0.32, s, s * 0.64, 4), paint(rgb, a, stroke=3))
    p = skia.Path().moveTo(x - s / 2, y - s * 0.32).lineTo(x, y + s * 0.05).lineTo(x + s / 2, y - s * 0.32)
    c.drawPath(p, paint(rgb, a, stroke=3))


def door_out(c, x, y, s, rgb=INK2, a=1.0):
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.4, y - s * 0.5, s * 0.5, s), paint(rgb, a, stroke=3))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.36, y - s * 0.46, s * 0.3, s * 0.92), paint(mix(rgb, PAPER, 0.5), a))
    c.drawLine(x + s * 0.0, y, x + s * 0.48, y, paint(rgb, a, stroke=4))
    p = skia.Path().moveTo(x + s * 0.5, y).lineTo(x + s * 0.34, y - s * 0.14).lineTo(x + s * 0.34, y + s * 0.14).close()
    c.drawPath(p, paint(rgb, a))


def rulebook(c, x, y, s, rgb=INK2, a=1.0, label="规"):
    c.drawRRect(_rrect(x - s * 0.36, y - s * 0.48, s * 0.72, s * 0.96, 5), paint(rgb, a))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.36, y - s * 0.48, s * 0.1, s * 0.96), paint(mix(rgb, INK, 0.35), a))
    c.drawRRect(_rrect(x - s * 0.18, y - s * 0.3, s * 0.42, s * 0.26, 3), paint(CARD, a))
    draw_text(c, label, x + s * 0.03, y - s * 0.17, "serif_heavy", int(s * 0.2), INK, a, align="center")


def seal(c, x, y, s, a=1.0, rgb=INK2):
    """A rubber/official seal (印章) – handle + base."""
    c.drawRRect(_rrect(x - s * 0.12, y - s * 0.75, s * 0.24, s * 0.5, s * 0.1), paint(rgb, a))
    c.drawCircle(x, y - s * 0.8, s * 0.18, paint(rgb, a))
    c.drawRRect(_rrect(x - s * 0.42, y - s * 0.28, s * 0.84, s * 0.22, s * 0.05), paint(rgb, a))
    c.drawRRect(_rrect(x - s * 0.36, y - s * 0.06, s * 0.72, s * 0.08, s * 0.03), paint(mix(rgb, INK, 0.4), a))


def shield(c, x, y, s, fill=CARD, rgb=INK, a=1.0, stroke=5):
    p = skia.Path()
    p.moveTo(x, y - s * 0.6)
    p.cubicTo(x + s * 0.25, y - s * 0.48, x + s * 0.42, y - s * 0.5, x + s * 0.5, y - s * 0.52)
    p.cubicTo(x + s * 0.52, y + s * 0.05, x + s * 0.3, y + s * 0.4, x, y + s * 0.62)
    p.cubicTo(x - s * 0.3, y + s * 0.4, x - s * 0.52, y + s * 0.05, x - s * 0.5, y - s * 0.52)
    p.cubicTo(x - s * 0.42, y - s * 0.5, x - s * 0.25, y - s * 0.48, x, y - s * 0.6)
    p.close()
    c.drawPath(p, paint(fill, a))
    c.drawPath(p, paint(rgb, a, stroke=stroke))
    return p


def cage(c, x, y, s, rgb=INK2, a=1.0):
    c.drawArc(skia.Rect.MakeXYWH(x - s * 0.45, y - s * 0.75, s * 0.9, s * 0.6), 180, 180, False, paint(rgb, a, stroke=5))
    for k in range(7):
        xx = x - s * 0.45 + k * s * 0.15
        top = y - s * 0.45 - math.sqrt(max(0.0, 1 - ((xx - x) / (s * 0.45)) ** 2)) * s * 0.3
        c.drawLine(xx, top, xx, y + s * 0.4, paint(rgb, a, stroke=4))
    c.drawLine(x - s * 0.5, y + s * 0.4, x + s * 0.5, y + s * 0.4, paint(rgb, a, stroke=7))
    c.drawLine(x - s * 0.47, y - s * 0.02, x + s * 0.47, y - s * 0.02, paint(rgb, a, stroke=3))
    c.drawCircle(x, y - s * 0.8, s * 0.06, paint(rgb, a, stroke=4))


def thought_bubble(c, x, y, r, a=1.0):
    c.drawCircle(x, y, r, paint(CARD, a)); c.drawCircle(x, y, r, paint(INK2, a, stroke=3))
    c.drawCircle(x - r * 0.9, y + r * 1.05, r * 0.2, paint(CARD, a)); c.drawCircle(x - r * 0.9, y + r * 1.05, r * 0.2, paint(INK2, a, stroke=2.5))
    c.drawCircle(x - r * 1.25, y + r * 1.45, r * 0.11, paint(CARD, a)); c.drawCircle(x - r * 1.25, y + r * 1.45, r * 0.11, paint(INK2, a, stroke=2))


def oil_can(c, x, y, s, a=1.0):
    c.drawRRect(_rrect(x - s * 0.3, y - s * 0.3, s * 0.6, s * 0.4, 6), paint(METAL_D, a))
    p = skia.Path().moveTo(x + s * 0.25, y - s * 0.25).lineTo(x + s * 0.7, y - s * 0.55).lineTo(x + s * 0.72, y - s * 0.5).lineTo(x + s * 0.3, y - s * 0.15).close()
    c.drawPath(p, paint(METAL_D, a))
    c.drawArc(skia.Rect.MakeXYWH(x - s * 0.28, y - s * 0.55, s * 0.4, s * 0.4), 180, 180, False, paint(INK2, a, stroke=4))


def dial(c, x, y, r, val, label_lo="", label_hi="", a=1.0):
    """Half-circle gauge; val in 0..1."""
    rect = skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r)
    c.drawArc(rect, 180, 180, False, paint(INK2, a, stroke=6))
    for k in range(9):
        ang = math.pi + k * math.pi / 8
        c.drawLine(x + math.cos(ang) * r * 0.82, y + math.sin(ang) * r * 0.82, x + math.cos(ang) * r * 0.95,
                   y + math.sin(ang) * r * 0.95, paint(INK2, a, stroke=3))
    ang = math.pi + val * math.pi
    c.drawLine(x, y, x + math.cos(ang) * r * 0.78, y + math.sin(ang) * r * 0.78, paint(INK, a, stroke=6))
    c.drawCircle(x, y, 9, paint(INK, a))
    if label_lo:
        draw_text(c, label_lo, x - r, y + 30, "sans", 24, INK3, a, align="center")
    if label_hi:
        draw_text(c, label_hi, x + r, y + 30, "sans", 24, INK3, a, align="center")


def brick_wall(c, x, y, w, h, a=1.0, rgb=None):
    rgb = rgb or mix(OCHRE, PAPER, 0.35)
    bh = 34
    rows = int(h / bh)
    for i in range(rows):
        off = 0 if i % 2 == 0 else 40
        xx = x - off
        while xx < x + w:
            x0 = max(x, xx)
            x1 = min(x + w, xx + 78)
            if x1 > x0:
                c.drawRect(skia.Rect.MakeXYWH(x0, y + h - (i + 1) * bh, x1 - x0, bh), paint(rgb, a))
                c.drawRect(skia.Rect.MakeXYWH(x0, y + h - (i + 1) * bh, x1 - x0, bh), paint(INK2, a, stroke=2))
            xx += 80
