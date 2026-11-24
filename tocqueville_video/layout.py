# -*- coding: utf-8 -*-
"""Page layout for the vertical 1080x1920 frame: header, illustration plate, subtitles, quote card.
Safe zones for WeChat Channels: keep text between y=150 and y=1500.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import (W, H, paper, Ink, INK, INK_SOFT, RED, font, FONT_CJK, FONT_CJK_B, FONT_CJK_SB, FONT_FR_I,
                 wrap_cjk, balance_cjk, wrap_words, draw_text_rgba, over, blur, hexc, noise2d)

PX0, PY0, PX1, PY1 = 56, 300, 1024, 1250          # illustration plate
SUB_Y = 1335                                      # subtitle block top
SUB_MAXW = 930


def plate_mask(seed=5):
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)
    m[PY0:PY1, PX0:PX1] = 1
    # slightly irregular, inky edge
    n = noise2d(H, W, 6, rng)
    e = blur(m, 1.6)
    m = np.clip((e - 0.5) * 3 + 0.5 + (n - 0.5) * 0.5 * (e * (1 - e)) * 4, 0, 1)
    return m


_PM = None


def compose_plate(base, ill):
    """Place illustration canvas `ill` (full-frame) into `base` through the plate mask, then draw border."""
    global _PM
    if _PM is None:
        _PM = plate_mask()
    m = _PM[..., None]
    out = base * (1 - m) + ill * m
    ink = Ink()
    rng = np.random.default_rng(9)
    for (a, b) in [((PX0 - 1, PY0 - 1), (PX1 + 1, PY0 - 1)), ((PX1 + 1, PY0 - 1), (PX1 + 1, PY1 + 1)),
                   ((PX1 + 1, PY1 + 1), (PX0 - 1, PY1 + 1)), ((PX0 - 1, PY1 + 1), (PX0 - 1, PY0 - 1))]:
        ink.wobble_line(a, b, 2.6, 0.5, rng)
    o = 12
    for (a, b) in [((PX0 - o, PY0 - o), (PX1 + o, PY0 - o)), ((PX1 + o, PY0 - o), (PX1 + o, PY1 + o)),
                   ((PX1 + o, PY1 + o), (PX0 - o, PY1 + o)), ((PX0 - o, PY1 + o), (PX0 - o, PY0 - o))]:
        ink.wobble_line(a, b, 1.1, 0.4, rng)
    ink.apply(out, INK, 0.9)
    return out


def header(canvas, chapter, opacity=1.0):
    if not chapter:
        return canvas
    f = font(FONT_CJK_SB, 40)
    fs = font(FONT_CJK, 24)
    tw = f.getlength(chapter)
    items = [(W / 2, 205, chapter, f, (46, 33, 24, 255), "mm"),
             (W / 2, 150, "托克维尔的美国笔记 · 1831", fs, (90, 70, 50, 230), "mm")]
    rgba = draw_text_rgba((W, H), items)
    over(canvas, rgba, opacity)
    ink = Ink()
    rng = np.random.default_rng(4)
    ink.wobble_line((W / 2 - tw / 2 - 150, 207), (W / 2 - tw / 2 - 30, 207), 1.6, 0.3, rng)
    ink.wobble_line((W / 2 + tw / 2 + 30, 207), (W / 2 + tw / 2 + 150, 207), 1.6, 0.3, rng)
    ink.ellipse(W / 2 - tw / 2 - 20, 207, 4, 4)
    ink.ellipse(W / 2 + tw / 2 + 20, 207, 4, 4)
    ink.apply(canvas, INK, 0.85 * opacity)
    return canvas


def subtitle(canvas, text, opacity=1.0, size=50):
    if not text:
        return canvas
    f = font(FONT_CJK_SB, size)
    lines = balance_cjk(text, f, SUB_MAXW)
    if len(lines) > 3:
        f = font(FONT_CJK_SB, int(size * 0.86))
        lines = balance_cjk(text, f, SUB_MAXW)
    lh = f.size * 1.42
    y0 = SUB_Y + (3 - len(lines)) * lh * 0.35
    items = []
    for i, ln in enumerate(lines):
        items.append((W / 2, y0 + i * lh, ln, f, (40, 28, 20, 255), "ma"))
    rgba = draw_text_rgba((W, H), items)
    # soft paper halo behind text for legibility
    a = rgba[..., 3]
    halo = blur(a, 9) * 0.55
    canvas[:] = canvas * (1 - halo[..., None] * opacity) + hexc("#efe5cd")[None, None, :] * halo[..., None] * opacity
    over(canvas, rgba, opacity)
    return canvas


def quote_card(canvas, fr, zh, src, opacity=1.0, reveal=1.0, tone="#f1e7cf"):
    """Card over the plate: French (italic serif) + plain Chinese + source.
    reveal: 0..1 fraction of Chinese characters shown (typewriter-ish)."""
    if opacity <= 0:
        return canvas
    x0, x1 = PX0 + 34, PX1 - 34
    ff = font(FONT_FR_I, 40)
    fz = font(FONT_CJK_SB, 46)
    fsrc = font(FONT_CJK, 27)
    frl = wrap_words("« " + fr.strip() + " »", ff, x1 - x0 - 80)
    if len(frl) > 9:
        ff = font(FONT_FR_I, 34)
        frl = wrap_words("« " + fr.strip() + " »", ff, x1 - x0 - 80)
    zhl = balance_cjk(zh, fz, x1 - x0 - 90)
    lh_f, lh_z = ff.size * 1.28, fz.size * 1.5
    hgt = len(frl) * lh_f + 70 + len(zhl) * lh_z + 90
    cy = (PY0 + PY1) / 2
    y0 = cy - hgt / 2
    y0 = max(PY0 + 30, y0)
    card_top, card_bot = y0 - 50, y0 + hgt + 30
    # card
    m = np.zeros((H, W), np.float32)
    m[int(card_top):int(card_bot), int(x0):int(x1)] = 1
    m = blur(m, 2)
    sh = blur(np.roll(np.roll(m, 10, 0), 6, 1), 14) * 0.35
    canvas[:] = canvas * (1 - sh[..., None] * opacity)
    col = hexc(tone)
    canvas[:] = canvas * (1 - m[..., None] * 0.93 * opacity) + col * m[..., None] * 0.93 * opacity
    items = []
    y = y0
    for ln in frl:
        items.append((W / 2, y, ln, ff, (70, 48, 32, 255), "ma"))
        y += lh_f
    y += 28
    ysep = y
    y += 42
    nshow = int(round(len(zh) * reveal))
    shown = 0
    for ln in zhl:
        k = max(0, min(len(ln), nshow - shown))
        shown += len(ln)
        if k:
            items.append((x0 + 45 + (x1 - x0 - 90 - fz.getlength(ln)) / 2, y, ln[:k], fz, (36, 24, 18, 255), "la"))
        y += lh_z
    y += 14
    items.append((x1 - 50, y, "—— " + src, fsrc, (110, 80, 55, 255), "ra"))
    over(canvas, draw_text_rgba((W, H), items), opacity)
    ink = Ink()
    rng = np.random.default_rng(2)
    ink.wobble_line((W / 2 - 120, ysep), (W / 2 - 18, ysep), 1.5, 0.3, rng)
    ink.wobble_line((W / 2 + 18, ysep), (W / 2 + 120, ysep), 1.5, 0.3, rng)
    ink.poly([(W / 2, ysep - 8), (W / 2 + 8, ysep), (W / 2, ysep + 8), (W / 2 - 8, ysep)])
    for (a, b) in [((x0 + 14, card_top + 14), (x1 - 14, card_top + 14)), ((x1 - 14, card_top + 14), (x1 - 14, card_bot - 14)),
                   ((x1 - 14, card_bot - 14), (x0 + 14, card_bot - 14)), ((x0 + 14, card_bot - 14), (x0 + 14, card_top + 14))]:
        ink.wobble_line(a, b, 1.0, 0.25, rng)
    ink.apply(canvas, RED, 0.75 * opacity)
    return canvas
