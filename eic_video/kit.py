# -*- coding: utf-8 -*-
"""Reusable stage elements: header, subtitles, quote cards, mechanism cards, counters, bars, node graphs."""
import math, functools
from PIL import Image, ImageDraw, ImageFilter
from art import *

SUB_Y = 1450
SUB_W = 940


class G:
    """Per-frame context handed to a shot group."""
    def __init__(self, T, cue_times, line_info, frame_t):
        self.T = T                    # seconds since group start
        self.cue_times = cue_times    # {cue: start time relative to group start}
        self.line = line_info         # current line dict (with start/end absolute)
        self.t = frame_t              # absolute time

    def ct(self, name):
        """seconds since cue started (None if not yet / not in group)."""
        c = self.cue_times.get(name)
        if c is None or self.T < c:
            return None
        return self.T - c

    def r(self, name, delay=0.0, dur=0.8):
        """eased 0..1 ramp from cue start + delay."""
        c = self.ct(name)
        if c is None:
            return 0.0
        return ease((c - delay) / dur) if c > delay else 0.0

    def seen(self, name):
        return self.ct(name) is not None

    def cue_len(self, name):
        return self.cue_times.get("__len__" + name, 6.0)


# ---------------------------------------------------------------- header / tags

@functools.lru_cache(maxsize=32)
def _header_layer(chapter):
    tl = TextLayer()
    tl.add((W / 2, 128), "权力与组织 · 东印度公司", font(SANS, 30), (200, 180, 140, 235))
    if chapter:
        tl.add((W / 2, 192), chapter, font(SERIF_B, 50), GOLD_L)
    layer = tl.render(shadow=0.7)
    d = ImageDraw.Draw(layer)
    if chapter:
        tw = font(SERIF_B, 50).getlength(chapter)
        gold_rule(d, W / 2, 196, tw / 2 + 120, color=GOLD + (220,))
        # erase middle part of rule behind text
        d.rectangle((W / 2 - tw / 2 - 16, 170, W / 2 + tw / 2 + 16, 222), fill=(0, 0, 0, 0))
    return layer


def header(img, chapter, a=1.0):
    comp(img, _header_layer(chapter), a)


@functools.lru_cache(maxsize=4)
def _ai_tag():
    im = new(size=(150, 46))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 149, 45), radius=10, fill=(0, 0, 0, 110), outline=(255, 255, 255, 90), width=1)
    d.text((75, 23), "AI配音", font=font(SANS, 24), fill=(255, 255, 255, 190), anchor="mm")
    return im


def ai_tag(img):
    comp(img, _ai_tag(), 1.0, (W - 190, 70))


@functools.lru_cache(maxsize=8)
def _schematic_tag(text):
    im = new(size=(150, 44))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 149, 43), radius=8, fill=(0, 0, 0, 120), outline=GOLD + (140,), width=1)
    d.text((75, 22), text, font=font(SANS, 24), fill=GOLD_L + (220,), anchor="mm")
    return im


def schematic(img, text="示意", xy=(W - 190, 1300), a=1.0):
    comp(img, _schematic_tag(text), a, xy)


# ---------------------------------------------------------------- subtitles

@functools.lru_cache(maxsize=512)
def _sub_layer(text, size=54):
    f = font(SANS_B, size)
    lines = balance_cjk(text, f, SUB_W)
    if len(lines) > 2:
        f = font(SANS_B, int(size * 0.9))
        lines = balance_cjk(text, f, SUB_W)
    lh = f.size * 1.38
    n = len(lines)
    y0 = SUB_Y - (n - 1) * lh / 2
    layer = new()
    # soft dark band behind subtitles
    band = new(); bd = ImageDraw.Draw(band)
    maxw = max(f.getlength(l) for l in lines)
    bd.rounded_rectangle((W / 2 - maxw / 2 - 36, y0 - lh / 2 - 14, W / 2 + maxw / 2 + 36, y0 + (n - 1) * lh + lh / 2 + 14),
                         radius=22, fill=(0, 0, 0, 120))
    layer.alpha_composite(band.filter(ImageFilter.GaussianBlur(10)))
    tl = TextLayer()
    for i, l in enumerate(lines):
        tl.add((W / 2, y0 + i * lh), l, f, WHITE, stroke=2, stroke_fill=(0, 0, 0, 255))
    layer.alpha_composite(tl.render(shadow=0.8, blur=4))
    return layer


def subtitle(img, text, a=1.0):
    if text:
        comp(img, _sub_layer(text), a)


def split_sub(text, maxchars=34):
    """Split a long line into subtitle chunks at punctuation; returns list of (chunk, weight)."""
    import re
    n = len(text)
    if n <= maxchars:
        return [text]
    parts = re.split(r"(?<=[，。；：？！])", text)
    parts = [p for p in parts if p]
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > maxchars and cur:
            chunks.append(cur); cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    # strip trailing comma/full stop of chunks for cleaner display
    out = []
    for c in chunks:
        c = c.rstrip("，；：")
        if c.endswith("。") and not c.endswith("”。"):
            c = c[:-1]
        out.append(c)
    return out


# ---------------------------------------------------------------- cards

def quote_card(img, q, zh, prog_in, reveal, a=1.0, y_center=820):
    """Quote card. q: dict(en=..., zh=..., src=...); zh: plain Chinese rendering. reveal: 0..1 for zh chars."""
    if a <= 0.01:
        return
    lay = _quote_static(q.get("en", ""), q.get("zh", ""), q["src"], zh, y_center)
    dy = (1 - ease_out(prog_in)) * 40
    comp(img, lay["panel"], a * prog_in, (0, dy))
    if zh:
        n = len(zh)
        k = int(round(n * clamp01(reveal)))
        txt = lay["zh_lines"]
        tl = TextLayer()
        used = 0
        for (xy, line) in txt:
            if used >= k:
                break
            part = line[:max(0, k - used)]
            used += len(line)
            tl.add((xy[0], xy[1] + dy), part, lay["zh_font"], GOLD_L, anchor="lm")
        comp(img, tl.render(shadow=0.6), a * prog_in)


@functools.lru_cache(maxsize=16)
def _quote_static(en, czh, src, zh, y_center):
    fe = font(EN_SERIF_I, 42)
    fz = font(SERIF_B, 50)
    fc = font(SERIF_B, 84)
    fs = font(SANS, 28)
    maxw = 860
    en_lines = wrap_words(en, fe, maxw) if en else []
    czh_lines = wrap_cjk(czh, fc, maxw) if czh else []
    zh_lines = balance_cjk(zh, fz, maxw) if zh else []
    src_lines = balance_cjk("—— " + src, fs, maxw - 40)
    h = 120 + len(en_lines) * 58 + len(czh_lines) * 130 + 60 + len(zh_lines) * 72 + 50 + 40 * len(src_lines)
    top = y_center - h / 2
    panel = new()
    d = ImageDraw.Draw(panel)
    sh = new(); ImageDraw.Draw(sh).rounded_rectangle((60, top + 10, W - 60, top + h + 20), radius=26, fill=(0, 0, 0, 160))
    panel.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d.rounded_rectangle((60, top, W - 60, top + h), radius=26, fill=(14, 18, 26, 232), outline=GOLD + (210,), width=2)
    d.rounded_rectangle((74, top + 14, W - 74, top + h - 14), radius=20, outline=GOLD + (80,), width=1)
    d.text((110, top + 66), "“", font=font(EN_SERIF_B, 120), fill=GOLD + (150,), anchor="lm")
    tl = TextLayer()
    y = top + 100
    for l in en_lines:
        tl.add((W / 2, y), l, fe, IVORY, anchor="mm"); y += 58
    for l in czh_lines:
        tl.add((W / 2, y + 30), l, fc, GOLD_L, anchor="mm"); y += 130
    y += 20
    rule_y = y
    y += 44
    zh_pos = []
    for l in zh_lines:
        x0 = W / 2 - fz.getlength(l) / 2
        zh_pos.append(((x0, y), l)); y += 72
    for i, l in enumerate(src_lines):
        tl.add((W - 110, top + h - 48 - 40 * (len(src_lines) - 1 - i)), l, fs, (200, 190, 165), anchor="rm")
    panel.alpha_composite(tl.render(shadow=0.5))
    gold_rule(d, W / 2, rule_y, 200, color=GOLD + (200,))
    return dict(panel=panel, zh_lines=zh_pos, zh_font=fz)


def title_card(img, title, sub=None, a=1.0, y=820, size=88, color=GOLD_L, sub_color=IVORY, sub_size=40):
    tl = TextLayer()
    tl.add((W / 2, y), title, font(SERIF_B, size), color)
    if sub:
        tl.add((W / 2, y + size * 0.95), sub, font(SANS, sub_size), sub_color)
    comp(img, tl.render(shadow=0.8, blur=8), a)


def label(img, xy, text, size=36, color=IVORY, a=1.0, anchor="mm", fontspec=None, box=None, pad=16):
    f = font(fontspec or SANS_B, size)
    if box:
        w_ = f.getlength(text)
        bl = new(); d = ImageDraw.Draw(bl)
        x, y = xy
        if anchor == "mm":
            x0 = x - w_ / 2 - pad
        elif anchor == "lm":
            x0 = x - pad
        else:
            x0 = x - w_ - pad
        d.rounded_rectangle((x0, y - size * 0.75, x0 + w_ + 2 * pad, y + size * 0.75), radius=10,
                            fill=tuple(box[:3]) + ((box[3] if len(box) > 3 else 200),))
        comp(img, bl, a)
    tl = TextLayer().add(xy, text, f, color, anchor=anchor)
    comp(img, tl.render(shadow=0.6), a)


def mech_card(img, left, right, prog, a=1.0, y=820, tag="机制"):
    """'left  →  right' mechanism card; prog 0..1 reveals arrow and right side."""
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((70, y - 230, W - 70, y + 230), radius=28, fill=(10, 14, 22, 225), outline=GOLD + (200,), width=2)
    d.rounded_rectangle((W / 2 - 70, y - 252, W / 2 + 70, y - 208), radius=12, fill=GOLD + (255,))
    d.text((W / 2, y - 230), tag, font=font(SANS_B, 28), fill=(20, 16, 10, 255), anchor="mm")
    comp(img, lay, a)
    fl = font(SERIF_B, 50)
    lines_l = balance_cjk(left, fl, 820)
    lines_r = balance_cjk(right, fl, 820)
    tl = TextLayer()
    for i, l in enumerate(lines_l):
        tl.add((W / 2, y - 120 + i * 64 - (len(lines_l) - 1) * 32), l, fl, IVORY)
    comp(img, tl.render(), a)
    ar = thick_arrow([(W / 2, y - 50), (W / 2, y + 40)], 26, GOLD, prog=ease(prog * 1.6))
    comp(img, ar, a)
    tl = TextLayer()
    for i, l in enumerate(lines_r):
        tl.add((W / 2, y + 120 + i * 64 - (len(lines_r) - 1) * 32), l, fl, GOLD_L)
    comp(img, tl.render(), a * ramp(prog, 0.35, 0.4))


def counter(img, xy, value, prefix="", suffix="", size=120, color=GOLD_L, a=1.0, fmt="{:,.0f}"):
    s = prefix + fmt.format(value) + suffix
    tl = TextLayer().add(xy, s, font(SERIF_B, size), color)
    comp(img, tl.render(shadow=0.8, blur=8), a)


def hbar(img, x, y, w, h, frac, color, a=1.0, label_l=None, label_r=None, lsize=34):
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=(255, 255, 255, 25))
    if frac > 0.003:
        d.rounded_rectangle((x, y, x + max(h, w * frac), y + h), radius=h // 2, fill=tuple(color) + (240,))
    comp(img, lay, a)
    if label_l:
        label(img, (x, y - lsize * 0.9), label_l, size=lsize, anchor="lm", a=a)
    if label_r:
        label(img, (x + w, y - lsize * 0.9), label_r, size=lsize, anchor="rm", a=a, color=color)


def node(img, xy, title, sub=None, color=GOLD, a=1.0, w=360, h=130, fill=(14, 20, 30, 235), glow_=False):
    x, y = xy
    lay = new(); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), radius=20, fill=fill, outline=tuple(color) + (230,), width=3)
    if glow_:
        lay = glow(lay, 10)
    comp(img, lay, a)
    tl = TextLayer()
    if sub:
        tl.add((x, y - 22), title, font(SERIF_B, 42), WHITE)
        tl.add((x, y + 30), sub, font(SANS, 28), tuple(color))
    else:
        tl.add((x, y), title, font(SERIF_B, 42), WHITE)
    comp(img, tl.render(shadow=0.5), a)


def flow_dots(img, pts, color, t, speed=0.5, n=6, r=9, a=1.0):
    lay = new(); d = ImageDraw.Draw(lay)
    for i in range(n):
        f = (t * speed + i / n) % 1.0
        x, y = point_at(pts, f)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(color) + (255,))
    comp(img, glow(lay, 6), a)


def stamp(img, text, xy, prog, color=RED, size=110, angle=-12, a=1.0):
    if prog <= 0:
        return
    f = font(SERIF_B, size)
    tw = f.getlength(text)
    s = int(max(tw, size) + 120)
    lay = new(size=(s, s)); d = ImageDraw.Draw(lay)
    c = s / 2
    d.rounded_rectangle((c - tw / 2 - 30, c - size * 0.7, c + tw / 2 + 30, c + size * 0.7), radius=12,
                        outline=tuple(color) + (235,), width=8)
    d.text((c, c), text, font=f, fill=tuple(color) + (235,), anchor="mm")
    lay = lay.rotate(angle, resample=Image.BICUBIC)
    sc = 1.0 + 0.6 * (1 - ease_out(min(1, prog * 2.5)))
    if sc != 1:
        lay = lay.resize((int(s * sc), int(s * sc)), Image.BICUBIC)
    comp(img, lay, a * min(1, prog * 3), (xy[0] - lay.size[0] / 2, xy[1] - lay.size[1] / 2))


def timeline_bar(img, years, marks, prog, y=820, a=1.0, x0=110, x1=970, highlight=None):
    """years: (y0, y1); marks: list of (year, text, color)."""
    lay = new(); d = ImageDraw.Draw(lay)
    xe = x0 + (x1 - x0) * ease(prog)
    d.line((x0, y, xe, y), fill=GOLD + (230,), width=4)
    comp(img, lay, a)
    span = years[1] - years[0]
    for i, (yr, txt, col) in enumerate(marks):
        x = x0 + (x1 - x0) * (yr - years[0]) / span
        if x > xe + 1:
            continue
        up = i % 2 == 0
        lay = new(); d = ImageDraw.Draw(lay)
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=tuple(col) + (255,), outline=(20, 16, 10, 255), width=2)
        d.line((x, y - (20 if up else -20), x, y - (90 if up else -90)), fill=tuple(col) + (200,), width=2)
        comp(img, lay, a)
        label(img, (x, y - 120 if up else y + 120), str(yr), size=40, color=col, a=a, fontspec=SERIF_B)
        label(img, (x, y - 170 if up else y + 172), txt, size=32, color=IVORY, a=a)
