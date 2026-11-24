"""Reusable animated widgets: panels, cards, icons, counters."""
import math

import cairo
import numpy as np

from engine import (CYAN, GREY, ORANGE, RED, SAFE_TOP, W, WHITE, clamp, draw_text, ease_back, ease_out,
                    hexrgb, rounded_rect, set_color, wrap)


def win(t, t0, t1, fin=0.35, fout=0.35):
    """Visibility of something shown from t0 to t1 with fades."""
    if t < t0 - 1e-6 or t > t1 + fout:
        return 0.0
    a = ease_out((t - t0) / fin) if fin > 0 else 1.0
    b = 1 - clamp((t - t1) / fout) if fout > 0 else (1.0 if t <= t1 else 0.0)
    return clamp(min(a, b))


def rise(t, t0, d=0.5, dist=40):
    """(alpha, dy) for an element sliding up into place at t0."""
    k = ease_out((t - t0) / d)
    return k, (1 - k) * dist


def card(ctx, x, y, w, h, alpha=1.0, fill="#0D1626", stroke="#22314A", r=22, lw=2):
    rounded_rect(ctx, x, y, w, h, r)
    set_color(ctx, fill, 0.92 * alpha)
    ctx.fill_preserve()
    set_color(ctx, stroke, alpha)
    ctx.set_line_width(lw)
    ctx.stroke()


def label_box(ctx, text, cx, cy, size=34, color=WHITE, fill="#0D1626", stroke=None, alpha=1.0, font="sans_bold",
              padx=28, pady=18):
    from engine import text_width
    tw = text_width(text, font, size)
    w, h = tw + 2 * padx, size + 2 * pady
    rounded_rect(ctx, cx - w / 2, cy - h / 2, w, h, h / 2)
    set_color(ctx, fill, 0.92 * alpha)
    ctx.fill_preserve()
    set_color(ctx, stroke or color, 0.9 * alpha)
    ctx.set_line_width(2.5)
    ctx.stroke()
    draw_text(ctx, text, cx, cy + size * 0.02, font, size, color, alpha, "mm")
    return w, h


def big_lines(ctx, lines, y, alpha=1.0, size=52, color=WHITE, font="sans_black", lh=1.35, glow=0, glow_color=None):
    for i, ln in enumerate(lines):
        col = color
        if isinstance(ln, tuple):
            ln, col = ln
        draw_text(ctx, ln, W / 2, y + i * size * lh, font, size, col, alpha, "ms", glow=glow,
                  glow_color=glow_color or col, glow_alpha=0.35)


def point_card(ctx, t, t0, t1, lines, accent=CYAN, y=720, dark=True):
    """The recurring '这说明什么' card at the end of every story."""
    a = win(t, t0, t1 + 0.3, 0.45, 0.4)
    if a <= 0:
        return
    k, dy = rise(t, t0, 0.5, 50)
    ctx.save()
    if dark:
        set_color(ctx, "#03060B", 0.78 * a)
        ctx.paint()
    h = 150 + 92 * len(lines)
    x0, y0 = 70, y - h / 2 + dy
    card(ctx, x0, y0, W - 140, h, a, fill="#0B1322", stroke=accent, lw=3)
    set_color(ctx, accent, a)
    ctx.rectangle(x0, y0 + 40, 8, 54)
    ctx.fill()
    draw_text(ctx, "这说明什么", x0 + 40, y0 + 82, "sans_bold", 36, accent, a, "ls")
    yy = y0 + 170
    for ln in lines:
        col = WHITE
        if isinstance(ln, tuple):
            ln, col = ln
        draw_text(ctx, ln, W / 2, yy, "sans_black", 50, col, a, "ms")
        yy += 92
    ctx.restore()


def chapter_flash(ctx, t, t0, title, sub=None, accent=CYAN, dur=1.6, light=False):
    """Big chapter title at the very start of a segment."""
    a = win(t, t0, t0 + dur, 0.3, 0.45)
    if a <= 0:
        return
    set_color(ctx, "#F3EBDA" if light else "#03060B", 0.88 * a)
    ctx.paint()
    s = 1 + 0.03 * clamp((t - t0) / dur)
    ctx.save()
    ctx.translate(W / 2, 860)
    ctx.scale(s, s)
    set_color(ctx, accent, a)
    ctx.rectangle(-60, -120, 120, 6)
    ctx.fill()
    draw_text(ctx, title, 0, 0, "sans_black", 84, "#1E1A14" if light else WHITE, a, "ms")
    if sub:
        draw_text(ctx, sub, 0, 80, "sans_medium", 36, accent, a, "ms")
    ctx.restore()


# ---------------------------------------------------------------- icons
def icon_model(ctx, cx, cy, s=1.0, color=CYAN, alpha=1.0, label="模型", fill_alpha=0.16):
    w, h = 150 * s, 110 * s
    rounded_rect(ctx, cx - w / 2, cy - h / 2, w, h, 22 * s)
    set_color(ctx, color, fill_alpha * alpha)
    ctx.fill_preserve()
    set_color(ctx, color, alpha)
    ctx.set_line_width(3 * s)
    ctx.stroke()
    for i in (-1, 1):
        set_color(ctx, color, alpha)
        ctx.arc(cx + i * 32 * s, cy - 10 * s, 9 * s, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_line_width(3 * s)
    ctx.move_to(cx - 28 * s, cy + 22 * s)
    ctx.line_to(cx + 28 * s, cy + 22 * s)
    ctx.stroke()
    ctx.move_to(cx, cy - h / 2)
    ctx.line_to(cx, cy - h / 2 - 22 * s)
    ctx.stroke()
    ctx.arc(cx, cy - h / 2 - 28 * s, 7 * s, 0, 2 * math.pi)
    ctx.fill()
    if label:
        draw_text(ctx, label, cx, cy + h / 2 + 40 * s, "sans_bold", 30 * s, color, alpha, "ms")


def icon_doc(ctx, x, y, s=1.0, color=WHITE, alpha=1.0, lines=4, accent=None):
    w, h = 90 * s, 116 * s
    ctx.new_path()
    ctx.move_to(x, y)
    ctx.line_to(x + w - 24 * s, y)
    ctx.line_to(x + w, y + 24 * s)
    ctx.line_to(x + w, y + h)
    ctx.line_to(x, y + h)
    ctx.close_path()
    set_color(ctx, "#0D1626", 0.95 * alpha)
    ctx.fill_preserve()
    set_color(ctx, color, alpha)
    ctx.set_line_width(2.5 * s)
    ctx.stroke()
    set_color(ctx, accent or color, 0.7 * alpha)
    for i in range(lines):
        ctx.rectangle(x + 14 * s, y + (34 + i * 18) * s, (w - 28 * s) * (0.9 if i % 3 else 0.65), 5 * s)
    ctx.fill()


def icon_person(ctx, cx, cy, s=1.0, color=WHITE, alpha=1.0):
    set_color(ctx, color, alpha)
    ctx.arc(cx, cy - 26 * s, 14 * s, 0, 2 * math.pi)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(cx - 26 * s, cy + 30 * s)
    ctx.curve_to(cx - 26 * s, cy - 6 * s, cx + 26 * s, cy - 6 * s, cx + 26 * s, cy + 30 * s)
    ctx.close_path()
    ctx.fill()


def icon_building(ctx, cx, cy, s=1.0, color=WHITE, alpha=1.0):
    w, h = 90 * s, 110 * s
    set_color(ctx, color, 0.15 * alpha)
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.fill()
    set_color(ctx, color, alpha)
    ctx.set_line_width(2.5 * s)
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.stroke()
    for r in range(3):
        for c in range(3):
            ctx.rectangle(cx - w / 2 + (14 + c * 24) * s, cy - h / 2 + (14 + r * 26) * s, 14 * s, 14 * s)
    ctx.fill()


def icon_server(ctx, x, y, s=1.0, color=CYAN, alpha=1.0, led=None):
    w, h = 120 * s, 46 * s
    rounded_rect(ctx, x, y, w, h, 8 * s)
    set_color(ctx, "#0D1626", 0.95 * alpha)
    ctx.fill_preserve()
    set_color(ctx, color, alpha)
    ctx.set_line_width(2.5 * s)
    ctx.stroke()
    for i in range(4):
        ctx.rectangle(x + 14 * s + i * 14 * s, y + 14 * s, 8 * s, h - 28 * s)
    ctx.fill()
    set_color(ctx, led or color, alpha)
    ctx.arc(x + w - 20 * s, y + h / 2, 7 * s, 0, 2 * math.pi)
    ctx.fill()


def icon_clock(ctx, cx, cy, r, frac, color=WHITE, alpha=1.0):
    set_color(ctx, color, alpha)
    ctx.set_line_width(4)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.stroke()
    a = -math.pi / 2 + 2 * math.pi * frac
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8)
    ctx.stroke()
    ctx.move_to(cx, cy)
    ctx.line_to(cx + math.cos(a / 12) * r * 0.5, cy + math.sin(a / 12) * r * 0.5)
    ctx.stroke()


def icon_brake(ctx, cx, cy, r=60, color=CYAN, alpha=1.0):
    set_color(ctx, "#06101A", 0.95 * alpha)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    set_color(ctx, color, alpha)
    ctx.set_line_width(5)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.stroke()
    ctx.rectangle(cx - r * 0.32, cy - r * 0.38, r * 0.2, r * 0.76)
    ctx.rectangle(cx + r * 0.12, cy - r * 0.38, r * 0.2, r * 0.76)
    ctx.fill()


def icon_leaf(ctx, cx, cy, s=1.0, alpha=1.0, rot=-0.4):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(s, s)
    ctx.new_path()
    ctx.move_to(0, 46)
    ctx.curve_to(-50, 12, -44, -50, 0, -76)
    ctx.curve_to(44, -50, 50, 12, 0, 46)
    ctx.close_path()
    set_color(ctx, "#7BD389", 0.97 * alpha)
    ctx.fill()
    set_color(ctx, "#2F6B3A", alpha)
    ctx.set_line_width(3)
    ctx.move_to(0, 58)
    ctx.line_to(0, -64)
    ctx.stroke()
    ctx.restore()


def arrow(ctx, x1, y1, x2, y2, color=GREY, alpha=1.0, lw=3, head=14, dash=None):
    set_color(ctx, color, alpha)
    ctx.set_line_width(lw)
    if dash:
        ctx.set_dash(dash)
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()
    ctx.set_dash([])
    a = math.atan2(y2 - y1, x2 - x1)
    ctx.move_to(x2, y2)
    ctx.line_to(x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45))
    ctx.line_to(x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
    ctx.close_path()
    ctx.fill()


def counter_text(v, fmt="{:,.0f}"):
    return fmt.format(v)


def quote_card(ctx, t, t0, t1, en, zh, y=760, alpha_scale=1.0, dark=True, en_font="serif", zh_font="serif_bold",
               color_en="#C9D3DD", color_zh=WHITE, bg="#0B1322", stroke="#2A3A55"):
    a = win(t, t0, t1, 0.4, 0.35) * alpha_scale
    if a <= 0:
        return
    en_lines = wrap(en, en_font, 36, W - 220)
    zh_lines = wrap(zh, zh_font, 44, W - 220)
    h = 120 + len(en_lines) * 52 + len(zh_lines) * 64
    k, dy = rise(t, t0, 0.5, 30)
    x0, y0 = 70, y - h / 2 + dy
    card(ctx, x0, y0, W - 140, h, a, fill=bg, stroke=stroke)
    yy = y0 + 76
    for ln in en_lines:
        draw_text(ctx, ln, W / 2, yy, en_font, 36, color_en, a, "ms")
        yy += 52
    yy += 18
    for ln in zh_lines:
        draw_text(ctx, ln, W / 2, yy, zh_font, 44, color_zh, a, "ms")
        yy += 64
