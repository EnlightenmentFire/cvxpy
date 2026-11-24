# -*- coding: utf-8 -*-
"""Drawing primitives: fonts, supersampled sprites, text layout, figures, icons."""
import functools
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
SCRATCH = os.environ.get(
    "HLC_SCRATCH",
    "/tmp/claude-0/-home-user-cvxpy/3146234e-c880-5dd6-b7f5-20b7a9aa7973/scratchpad")
FONT_DIR = os.path.join(SCRATCH, "fonts")

# ---------------------------------------------------------------- palette
BG = (245, 241, 232)
BG2 = (234, 228, 215)
BG3 = (223, 215, 199)
INK = (46, 49, 53)
INK2 = (104, 106, 110)
INK3 = (160, 156, 148)
LINE = (210, 202, 188)
WHITE = (255, 255, 255)
TEAL = (0, 134, 148)        # 唯一强调色：只用于“真实意思”
TEAL_D = (0, 104, 116)
TEAL_L = (210, 236, 238)
WOOD = (226, 208, 178)
WOOD_D = (200, 178, 142)
# 人物（低饱和）
C_WANG = (230, 160, 74)
C_MIKE = (86, 110, 148)
C_SARAH = (186, 116, 108)
C_CHEN = (116, 138, 104)
C_GRAY = (150, 146, 138)
C_SAND = (196, 178, 146)
C_PLUM = (138, 110, 140)
C_OLIVE = (150, 150, 100)
C_BROWN = (150, 112, 86)
PEOPLE = [C_WANG, C_MIKE, C_SARAH, C_CHEN, C_PLUM, C_OLIVE, C_BROWN, C_SAND, C_GRAY]
# 1945 段
PAPER = (232, 222, 199)
PAPER_D = (214, 200, 172)
SEPIA = (66, 54, 42)
SEPIA2 = (120, 102, 80)
RUST = (150, 72, 52)


def font(name, size):
    return _font(name, int(round(size)))


@functools.lru_cache(maxsize=256)
def _font(name, size):
    files = {
        "r": "NotoSansCJKsc-Regular.otf",
        "m": "NotoSansCJKsc-Medium.otf",
        "b": "NotoSansCJKsc-Bold.otf",
        "k": "NotoSansCJKsc-Black.otf",
        "serif": "NotoSerifSC-Bold.otf",
        "serifk": "NotoSerifSC-Black.otf",
        "jp": "NotoSerifJP-Black.otf",
        "en": "Inter-Regular.ttf",
        "enm": "Inter-Medium.ttf",
        "ens": "Inter-SemiBold.ttf",
        "enb": "Inter-Bold.ttf",
        "eni": "Inter-Italic.ttf",
        "enmi": "Inter-MediumItalic.ttf",
    }
    return ImageFont.truetype(os.path.join(FONT_DIR, files[name]), size)


def is_ascii_word_char(ch):
    return ch.isascii() and (ch.isalnum() or ch in "'’-.,!?…:;\"“”()")


NO_LINE_START = set("，。、：；！？）」』”’》…,.!?:;)")


def tokenize(text):
    """Split into tokens: CJK chars individually, ASCII words with trailing space."""
    toks = []
    buf = ""
    for ch in text:
        if ch.isascii() and ch != " ":
            buf += ch
        elif ch == " ":
            if buf:
                toks.append(buf + " ")
                buf = ""
            else:
                toks.append(" ")
        else:
            if buf:
                toks.append(buf)
                buf = ""
            toks.append(ch)
    if buf:
        toks.append(buf)
    return toks


def text_w(text, f):
    if not text:
        return 0
    return f.getlength(text)


def wrap(text, f, maxw):
    """Greedy wrap for mixed CJK / Latin text."""
    lines = []
    for para in text.split("\n"):
        toks = tokenize(para)
        cur = ""
        for tk in toks:
            trial = cur + tk
            if text_w(trial.rstrip(), f) <= maxw or not cur.strip():
                cur = trial
            else:
                if tk and tk[0] in NO_LINE_START:
                    # pull punctuation onto current line
                    cur = trial
                    continue
                lines.append(cur.rstrip())
                cur = tk.lstrip()
        if cur.strip() or not lines:
            lines.append(cur.rstrip())
    return lines


def balance_wrap(text, f, maxw):
    """Wrap, then try to balance two-line results."""
    lines = wrap(text, f, maxw)
    if len(lines) == 2:
        total = text_w(text, f)
        lo, hi = total / 2, maxw
        best = lines
        w = lo
        while w <= hi:
            cand = wrap(text, f, w)
            if len(cand) == 2:
                best = cand
                break
            w += 12
        return best
    return lines


# ---------------------------------------------------------------- sprites
class Sprite:
    """Supersampled RGBA canvas; coordinates in output pixels."""

    def __init__(self, w, h, ss=2, bg=(0, 0, 0, 0)):
        self.w, self.h, self.ss = int(w), int(h), ss
        self.im = Image.new("RGBA", (self.w * ss, self.h * ss), bg)
        self.d = ImageDraw.Draw(self.im)

    def s(self, v):
        return v * self.ss

    def box(self, b):
        return [x * self.ss for x in b]

    def rrect(self, b, r, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(self.box(b), radius=r * self.ss, fill=fill, outline=outline,
                                 width=int(width * self.ss))

    def rect(self, b, fill=None, outline=None, width=0):
        self.d.rectangle(self.box(b), fill=fill, outline=outline, width=int(width * self.ss))

    def ellipse(self, b, fill=None, outline=None, width=0):
        self.d.ellipse(self.box(b), fill=fill, outline=outline, width=int(width * self.ss))

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def poly(self, pts, fill=None, outline=None, width=0):
        p = [(x * self.ss, y * self.ss) for x, y in pts]
        self.d.polygon(p, fill=fill, outline=outline, width=int(width * self.ss) if width else 1)

    def line(self, pts, fill, width=2, joint="curve"):
        p = [(x * self.ss, y * self.ss) for x, y in pts]
        self.d.line(p, fill=fill, width=int(width * self.ss), joint=joint)

    def arc(self, b, start, end, fill, width=2):
        self.d.arc(self.box(b), start, end, fill=fill, width=int(width * self.ss))

    def pieslice(self, b, start, end, fill):
        self.d.pieslice(self.box(b), start, end, fill=fill)

    def text(self, xy, txt, fnt, size, fill, anchor="la", stroke=0, stroke_fill=None, spacing=0):
        f = font(fnt, size * self.ss)
        self.d.text((xy[0] * self.ss, xy[1] * self.ss), txt, font=f, fill=fill, anchor=anchor,
                    stroke_width=int(stroke * self.ss), stroke_fill=stroke_fill)

    def paste(self, sp, x, y):
        """Paste another (already downsampled) sprite image at output coords."""
        im = sp if isinstance(sp, Image.Image) else sp.img()
        big = im.resize((im.width * self.ss, im.height * self.ss), Image.LANCZOS)
        self.im.alpha_composite(big, (int(x * self.ss), int(y * self.ss)))

    def img(self):
        if self.ss == 1:
            return self.im
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def shadow(img, radius=14, offset=(0, 8), opacity=0.16, pad=None):
    """Return a new image with a soft drop shadow (bigger canvas) and the pad used."""
    pad = pad if pad is not None else radius * 2 + max(abs(offset[0]), abs(offset[1]))
    w, h = img.size
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    a = img.split()[3]
    sh = Image.new("RGBA", img.size, (40, 36, 30, 0))
    sh.putalpha(a.point(lambda v: int(v * opacity)))
    out.alpha_composite(sh, (pad + offset[0], pad + offset[1]))
    out = out.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(img, (pad, pad))
    return out, pad


# ---------------------------------------------------------------- text sprites
def text_sprite(txt, fnt, size, fill, maxw=None, align="left", line_gap=0.32, stroke=0,
                stroke_fill=None, pad=4):
    f = font(fnt, size)
    lines = wrap(txt, f, maxw) if maxw else txt.split("\n")
    asc, desc = f.getmetrics()
    lh = int(size * (1 + line_gap))
    widths = [text_w(l, f) for l in lines]
    w = int(max(widths) if widths else 1) + pad * 2 + stroke * 2
    h = lh * (len(lines) - 1) + asc + desc + pad * 2 + stroke * 2
    im = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        if align == "center":
            x = (w - widths[i]) / 2
        elif align == "right":
            x = w - pad - stroke - widths[i]
        else:
            x = pad + stroke
        d.text((x, pad + stroke + i * lh), l, font=f, fill=fill, stroke_width=stroke,
               stroke_fill=stroke_fill)
    return im


def pill(txt, fnt, size, fg, bg, padx=18, pady=8, r=None, outline=None):
    f = font(fnt, size)
    tw = text_w(txt, f)
    asc, desc = f.getmetrics()
    w = int(tw + padx * 2)
    h = int(size * 1.05 + pady * 2)
    sp = Sprite(w, h)
    sp.rrect((0, 0, w - 1, h - 1), r if r is not None else h / 2, fill=bg, outline=outline,
             width=2 if outline else 0)
    sp.text((w / 2, h / 2 + size * 0.04), txt, fnt, size, fg, anchor="mm")
    return sp.img()


# ---------------------------------------------------------------- figures
def person_front(color, h=200, head_ratio=0.34, label=None, label_color=INK2, tilt=0.0,
                 skin=(236, 214, 190), hair=None):
    """Geometric standing/sitting person, front view, no face."""
    w = int(h * 0.62)
    lab_h = 44 if label else 0
    sp = Sprite(w, h + lab_h)
    hr = h * head_ratio / 2
    cx = w / 2
    # body
    bt = hr * 2 + h * 0.04
    sp.rrect((cx - w * 0.42, bt, cx + w * 0.42, h + w * 0.2), w * 0.3, fill=color)
    # mask lower overflow
    sp.im.paste((0, 0, 0, 0), tuple(int(v) for v in sp.box((0, h, w, h + lab_h + 1))))
    # head
    sp.circle(cx, hr + 2, hr, fill=skin)
    if hair:
        sp.pieslice((cx - hr, 2, cx + hr, 2 + hr * 2), 180, 360, fill=hair)
    if label:
        sp.text((cx, h + 8), label, "m", 30, label_color, anchor="ma")
    return sp.img()


def person_top(color, r=38, skin=(236, 214, 190), hair=None):
    """Top-down person: shoulders ellipse + head."""
    w = int(r * 2.6)
    h = int(r * 1.9)
    sp = Sprite(w, h)
    sp.ellipse((0, h * 0.18, w - 1, h - 1), fill=color)
    hc = hair or tuple(max(0, c - 70) for c in skin)
    sp.circle(w / 2, h * 0.5, r * 0.62, fill=hc)
    return sp.img()


def bubble(txt, fnt="m", size=40, fg=INK, bg=WHITE, maxw=600, tail="bl", padx=30, pady=20,
           outline=None, r=30, tail_len=34):
    f = font(fnt, size)
    lines = wrap(txt, f, maxw)
    lh = int(size * 1.35)
    tw = max(text_w(l, f) for l in lines)
    w = int(tw + padx * 2)
    h = int(lh * len(lines) + pady * 2 - (lh - size * 1.15))
    sp = Sprite(w + 8, h + tail_len + 8)
    ox, oy = 4, 4
    sp.rrect((ox, oy, ox + w, oy + h), r, fill=bg, outline=outline, width=3 if outline else 0)
    if tail:
        if tail == "bl":
            tx = ox + 50
            pts = [(tx, oy + h - 2), (tx + 34, oy + h - 2), (tx - 6, oy + h + tail_len)]
        elif tail == "br":
            tx = ox + w - 50
            pts = [(tx - 34, oy + h - 2), (tx, oy + h - 2), (tx + 6, oy + h + tail_len)]
        else:  # bottom center
            tx = ox + w / 2
            pts = [(tx - 18, oy + h - 2), (tx + 18, oy + h - 2), (tx, oy + h + tail_len)]
        sp.poly(pts, fill=bg)
        if outline:
            sp.line([pts[0], pts[2], pts[1]], outline, 3)
            sp.line([(pts[0][0] + 2, oy + h - 1.5), (pts[1][0] - 2, oy + h - 1.5)], bg, 4)
    y = oy + pady
    for l in lines:
        sp.text((ox + padx, y), l, fnt, size, fg)
        y += lh
    return sp.img()


def thought_dots(color=INK3, n=3, r=7, gap=22):
    sp = Sprite(gap * n + r * 2, r * 2 + 4)
    for i in range(n):
        sp.circle(r + i * gap, r + 2, r, fill=color)
    return sp.img()


# ---------------------------------------------------------------- icons
def icon_calendar(day_text, month_text="", w=220, color=INK):
    h = int(w * 1.05)
    sp = Sprite(w, h)
    sp.rrect((4, 14, w - 4, h - 4), 22, fill=WHITE, outline=LINE, width=3)
    sp.rrect((4, 14, w - 4, 70), 22, fill=(196, 92, 72))
    sp.rect((4, 46, w - 4, 70), fill=(196, 92, 72))
    for x in (w * 0.3, w * 0.7):
        sp.rrect((x - 7, 0, x + 7, 34), 7, fill=INK2)
    if month_text:
        sp.text((w / 2, 42), month_text, "b", 26, WHITE, anchor="mm")
    sp.text((w / 2, (70 + h) / 2 + 4), day_text, "k", int(w * 0.42), color, anchor="mm")
    return sp.img()


def icon_email(w=200, color=INK2, fill=WHITE, flap=True):
    h = int(w * 0.68)
    sp = Sprite(w, h)
    sp.rrect((3, 3, w - 3, h - 3), 14, fill=fill, outline=color, width=4)
    if flap:
        sp.line([(10, 12), (w / 2, h * 0.58), (w - 10, 12)], color, 4)
    return sp.img()


def icon_doc(w=200, h=260, lines=6, title=None, color=INK2, fill=WHITE, fold=True):
    sp = Sprite(w, h)
    f = 40 if fold else 0
    pts = [(3, 3), (w - 3 - f, 3), (w - 3, 3 + f), (w - 3, h - 3), (3, h - 3)]
    sp.poly(pts, fill=fill, outline=color, width=3)
    if fold:
        sp.poly([(w - 3 - f, 3), (w - 3 - f, 3 + f), (w - 3, 3 + f)], fill=LINE)
    y0 = 30
    if title:
        sp.text((22, 22), title, "enb", 22, INK)
        y0 = 70
    for i in range(lines):
        y = y0 + i * ((h - y0 - 24) / max(lines, 1))
        ww = (w - 50) * (0.55 if i == lines - 1 else (0.9 - 0.08 * (i % 3)))
        sp.rrect((22, y, 22 + ww, y + 10), 5, fill=LINE)
    return sp.img()


def icon_bulb(size=34, color=INK2):
    sp = Sprite(size, size)
    s = size
    sp.circle(s / 2, s * 0.4, s * 0.3, fill=color)
    sp.rrect((s * 0.36, s * 0.62, s * 0.64, s * 0.92), 3, fill=color)
    return sp.img()


def icon_salt(w=60, color=WHITE, label="盐"):
    h = int(w * 1.5)
    sp = Sprite(w, h)
    sp.rrect((4, h * 0.25, w - 4, h - 3), 12, fill=color, outline=INK2, width=3)
    sp.rrect((w * 0.18, 4, w * 0.82, h * 0.3), 8, fill=(170, 170, 176), outline=INK2, width=3)
    for i in range(3):
        sp.circle(w * (0.32 + i * 0.18), h * 0.14, 2.5, fill=INK2)
    sp.text((w / 2, h * 0.64), label, "b", int(w * 0.42), INK2, anchor="mm")
    return sp.img()


def icon_kettle(w=110, color=(150, 160, 170)):
    h = int(w * 0.9)
    sp = Sprite(w, h)
    sp.ellipse((w * 0.12, h * 0.3, w * 0.82, h - 4), fill=color)
    sp.rrect((w * 0.3, h * 0.18, w * 0.64, h * 0.36), 8, fill=color)
    sp.poly([(w * 0.78, h * 0.62), (w - 4, h * 0.36), (w - 4, h * 0.46), (w * 0.8, h * 0.76)], fill=color)
    sp.arc((w * 0.25, h * 0.0, w * 0.7, h * 0.5), 180, 360, INK2, 5)
    return sp.img()


def icon_ear(size=200, color=INK):
    sp = Sprite(size, size)
    s = size
    sp.arc((s * 0.18, s * 0.06, s * 0.82, s * 0.9), 160, 410, color, s * 0.07)
    sp.arc((s * 0.36, s * 0.28, s * 0.66, s * 0.66), 170, 390, color, s * 0.055)
    sp.line([(s * 0.66, s * 0.62), (s * 0.5, s * 0.86), (s * 0.36, s * 0.86)], color, s * 0.07)
    return sp.img()


def icon_teacup(w=420, color=(196, 160, 132)):
    h = int(w * 0.62)
    sp = Sprite(w, h)
    sp.ellipse((w * 0.04, h * 0.80, w * 0.86, h - 2), fill=(214, 190, 166))
    sp.pieslice((w * 0.14, h * -0.36, w * 0.76, h * 0.88), 0, 180, fill=color)
    sp.rect((w * 0.14, h * 0.24, w * 0.76, h * 0.27), fill=color)
    sp.arc((w * 0.68, h * 0.28, w * 0.94, h * 0.62), 270, 120, color, w * 0.035)
    sp.rect((w * 0.14, h * 0.235, w * 0.76, h * 0.285), fill=(176, 138, 112))
    return sp.img()


def arrow(x0, y0, x1, y1, color=INK2, width=6, head=22, curve=0.0, dashed=False):
    """Return (sprite, ox, oy) for an arrow from (x0,y0) to (x1,y1) (optionally curved)."""
    pad = head + width + 6
    minx, maxx = min(x0, x1) - pad - abs(curve), max(x0, x1) + pad + abs(curve)
    miny, maxy = min(y0, y1) - pad - abs(curve), max(y0, y1) + pad + abs(curve)
    sp = Sprite(maxx - minx, maxy - miny)
    ax, ay, bx, by = x0 - minx, y0 - miny, x1 - minx, y1 - miny
    mx, my = (ax + bx) / 2, (ay + by) / 2
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    cx, cy = mx + nx * curve, my + ny * curve
    pts = []
    for i in range(41):
        t = i / 40
        x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx
        y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t * t * by
        pts.append((x, y))
    # stop the line a bit before the head
    end_dx, end_dy = pts[-1][0] - pts[-3][0], pts[-1][1] - pts[-3][1]
    el = math.hypot(end_dx, end_dy) or 1
    ux, uy = end_dx / el, end_dy / el
    if dashed:
        for i in range(0, 38, 4):
            sp.line(pts[i:i + 3], color, width)
    else:
        sp.line(pts[:-2] + [(bx - ux * head * 0.6, by - uy * head * 0.6)], color, width)
    hx, hy = bx, by
    sp.poly([(hx, hy), (hx - ux * head - uy * head * 0.6, hy - uy * head + ux * head * 0.6),
             (hx - ux * head + uy * head * 0.6, hy - uy * head - ux * head * 0.6)], fill=color)
    return sp.img(), minx, miny


def flat_bg(color=BG):
    return Image.new("RGBA", (W, H), color + (255,))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def back_out(x, s=1.4):
    x = max(0.0, min(1.0, x))
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def with_alpha(im, a):
    if a >= 0.999:
        return im
    if a <= 0.001:
        return None
    r, g, b, al = im.split()
    al = al.point(lambda v: int(v * a))
    return Image.merge("RGBA", (r, g, b, al))
