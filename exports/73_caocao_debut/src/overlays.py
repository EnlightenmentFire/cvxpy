# -*- coding: utf-8 -*-
"""Cached overlay images: 古文卡, 现代类比卡, 起家三问卡, 演义/史书对照, 字幕, 章节标题, 角标."""
import functools, re
from PIL import Image, ImageDraw
from gfx import *

try:
    import opencc
    _t2s = opencc.OpenCC("t2s").convert
except Exception:  # pragma: no cover
    _t2s = lambda s: s

CW = 960


def _dashed_rect(d, box, col, dash=18, gap=12, width=3):
    x0, y0, x1, y1 = box
    for (a, b, horiz, c) in [(x0, x1, True, y0), (x0, x1, True, y1), (y0, y1, False, x0), (y0, y1, False, x1)]:
        p = a
        while p < b:
            q = min(b, p + dash)
            d.line([(p, c), (q, c)] if horiz else [(c, p), (c, q)], fill=col, width=width)
            p = q + gap


@functools.lru_cache(maxsize=64)
def card_img(text, src, lv, bh, big=False, dashed=False):
    pad = 48
    inner = CW - 2 * pad
    fs = 76 if big else (58 if len(text) <= 22 else 50 if len(text) <= 40 else 44)
    t_im = text_img(text, font(SERIF_B, fs), GOLD_L, maxw=inner, spacing=1.42)
    s_im = text_img("—— " + _t2s(src), sc_font(SERIF_R, 30), (200, 188, 160), maxw=inner, align="right")
    b_im = text_img(bh, sc_font(SANS_R, 38), (226, 226, 226), maxw=inner, spacing=1.38)
    tag = pill(LV_NAME[lv], LV_COL[lv], (0, 0, 0, 0), size=28, outline=LV_COL[lv] + (255,))
    if dashed:
        tag2 = pill("孤证", (240, 150, 140), (0, 0, 0, 0), size=28, outline=(240, 150, 140, 255))
    h = pad + tag.height + 22 + t_im.height + 14 + s_im.height + 26 + 2 + 22 + b_im.height + pad - 10
    im = Image.new("RGBA", (CW, h), (0, 0, 0, 0))
    bg = rrect((CW, h), 22, (8, 8, 10, 214), outline=None)
    im.alpha_composite(bg)
    d = ImageDraw.Draw(im)
    if dashed:
        _dashed_rect(d, (1, 1, CW - 2, h - 2), GOLD + (255,), width=3)
    else:
        d.rounded_rectangle([1, 1, CW - 2, h - 2], 22, outline=GOLD + (255,), width=3)
        d.rounded_rectangle([9, 9, CW - 10, h - 10], 16, outline=GOLD + (70,), width=1)
    y = pad
    im.alpha_composite(tag, (pad, y))
    if dashed:
        im.alpha_composite(tag2, (pad + tag.width + 14, y))
    y += tag.height + 22
    im.alpha_composite(t_im, (pad - 4, y)); y += t_im.height + 14
    im.alpha_composite(s_im, (CW - pad - s_im.width + 4, y)); y += s_im.height + 26
    d.line([(pad, y), (CW - pad, y)], fill=GOLD + (110,), width=2); y += 22
    im.alpha_composite(b_im, (pad - 4, y))
    return im


@functools.lru_cache(maxsize=16)
def ana_img(ana, bias):
    pad = 46; inner = CW - 2 * pad
    t1 = pill("现代类比", IVORY, (40, 52, 70, 255), size=30)
    a_im = text_img(ana, sc_font(SANS_R, 40), IVORY, maxw=inner, spacing=1.42)
    t2 = pill("类比偏差", (240, 170, 150), (0, 0, 0, 0), size=30, outline=(240, 170, 150, 255))
    b_im = text_img(bias, sc_font(SANS_R, 34), (214, 204, 198), maxw=inner, spacing=1.42)
    h = pad + t1.height + 18 + a_im.height + 30 + t2.height + 16 + b_im.height + pad
    im = rrect((CW, h), 22, (14, 20, 30, 226), outline=(130, 150, 175, 255), width=3)
    y = pad
    im.alpha_composite(t1, (pad, y)); y += t1.height + 18
    im.alpha_composite(a_im, (pad - 4, y)); y += a_im.height + 30
    ImageDraw.Draw(im).line([(pad, y - 15), (CW - pad, y - 15)], fill=(130, 150, 175, 90), width=2)
    im.alpha_composite(t2, (pad, y)); y += t2.height + 16
    im.alpha_composite(b_im, (pad - 4, y))
    return im


@functools.lru_cache(maxsize=4)
def q3_parts(have, lean, step):
    pad = 46; inner = CW - 2 * pad
    head = Image.new("RGBA", (CW, 170), (0, 0, 0, 0))
    hi = glow(text_img("起家三问", sc_font(KAI, 84), GOLD_L), 14, 1.2)
    head.alpha_composite(hi, ((CW - hi.width) // 2, 0))
    sub = text_img("曹操 · 二十岁 · 洛阳北部尉", sc_font(SERIF_R, 32), (200, 188, 160))
    head.alpha_composite(sub, ((CW - sub.width) // 2, 112))
    rows = []
    for lab, txt in [("手里有什么", have), ("借了谁的势", lean), ("做对了哪一步", step)]:
        p = pill(lab, (20, 16, 10), GOLD + (255,), size=32)
        b = text_img(txt, sc_font(SANS_R, 39), IVORY, maxw=inner, spacing=1.4)
        h = p.height + 14 + b.height + 40
        r = rrect((CW, h), 18, (10, 10, 12, 220), outline=GOLD + (150,), width=2)
        r.alpha_composite(p, (pad, 20)); r.alpha_composite(b, (pad - 4, 20 + p.height + 14))
        rows.append(r)
    return head, rows


@functools.lru_cache(maxsize=8)
def yy_parts(yy, sx):
    pad = 40; inner = CW - 2 * pad
    out = []
    for lab, txt, fg, bg in [("演义说", yy, IVORY, (150, 48, 38, 255)), ("史书说", sx, (20, 16, 10), GOLD + (255,))]:
        p = pill(lab, fg, bg, size=34)
        b = text_img(txt, sc_font(SANS_R, 40), IVORY, maxw=inner, spacing=1.4)
        h = p.height + 16 + b.height + 44
        r = rrect((CW, h), 18, (10, 10, 12, 222), outline=(bg[0], bg[1], bg[2], 170), width=2)
        r.alpha_composite(p, (pad, 20)); r.alpha_composite(b, (pad - 4, 20 + p.height + 16))
        out.append(r)
    return tuple(out)


SUB_F = 56
SUB_MAXW = 960


def sub_chunks(text, maxchars=16):
    """one display line per chunk where possible; long clauses split in balanced halves (2 lines)."""
    parts = re.findall(r"[^，。？！；：]+[，。？！；：]?", text)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(_strip_end(cur + p)) > maxchars:
            chunks.append(cur); cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        n = len(_strip_end(c))
        if n <= maxchars + 1:
            out.append(c)
        elif n <= 2 * maxchars:
            h = (n + 1) // 2; out.append(c[:h] + "\n" + c[h:])
        else:
            k = 0
            while len(c) - k > 2 * maxchars:
                out.append(c[k:k + maxchars] + "\n" + c[k + maxchars:k + 2 * maxchars]); k += 2 * maxchars
            rest = c[k:]; h = (len(rest) + 1) // 2
            out.append(rest if len(_strip_end(rest)) <= maxchars + 1 else rest[:h] + "\n" + rest[h:])
    return out


def _old_sub_chunks(text, maxchars=32):
    """split a subtitle line into display chunks (each <=2 rendered lines)."""
    parts = re.findall(r"[^，。？！；：]+[，。？！；：]?", text)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxchars or not cur:
            cur += p
        else:
            chunks.append(cur); cur = p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:   # hard split very long pieces
        while len(c) > maxchars + 6:
            out.append(c[:maxchars]); c = c[maxchars:]
        out.append(c)
    return out


def _strip_end(c):
    return re.sub(r"[，。；：]$", "", c)


@functools.lru_cache(maxsize=1024)
def sub_img(chunk):
    f = sc_font(SANS_B, SUB_F)
    return text_img(_strip_end(chunk), f, (255, 255, 255), maxw=None, spacing=1.3, stroke=5,
                    stroke_fill=(0, 0, 0), align="center", shadow=6)


@functools.lru_cache(maxsize=32)
def title_big(t):
    return glow(text_img(t, sc_font(KAI, 104), GOLD_L, maxw=980, align="center"), 20, 1.5)


@functools.lru_cache(maxsize=32)
def title_small(t):
    im = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    ti = text_img(t, sc_font(SERIF_B, 40), GOLD)
    im.alpha_composite(ti, ((W - ti.width) // 2, 6))
    d = ImageDraw.Draw(im)
    y = 6 + ti.height // 2 + 2
    d.line([(90, y), ((W - ti.width) // 2 - 20, y)], fill=GOLD + (120,), width=2)
    d.line([((W + ti.width) // 2 + 20, y), (W - 90, y)], fill=GOLD + (120,), width=2)
    return im


@functools.lru_cache(maxsize=8)
def corner(t):
    return pill(t, (205, 205, 205), (0, 0, 0, 120), size=24, outline=(200, 200, 200, 120), pad=(14, 4))
