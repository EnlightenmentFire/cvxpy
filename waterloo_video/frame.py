# -*- coding: utf-8 -*-
"""Scene context, shared overlays (header, time axis, subtitles, badges, quote cards)."""
import math, re
import numpy as np
import cairo
from gfx import *

AXIS = ["11:30", "13:00", "13:30", "16:00", "16:30", "18:30", "19:30", "20:00"]
AXIS_LABEL = {"11:30": "乌古蒙", "13:00": "望见普军", "13:30": "德隆军", "16:00": "骑兵冲击", "16:30": "普朗斯努瓦",
              "18:30": "拉艾圣陷落", "19:30": "近卫军", "20:00": "全线溃退"}
PLATE_CY = 830          # visual centre of interest


class S:
    """per-frame scene state"""

    def __init__(self, scene, t, lines, dur, gt=0.0):
        self.scene, self.t, self.lines, self.dur, self.gt = scene, t, lines, dur, gt
        self.cues = {}
        for L in lines:
            self.cues.setdefault(L["cue"], (L["t0"], L["t1"]))

    def c0(self, cue):
        return self.cues.get(cue, (1e9, 1e9))[0]

    def c1(self, cue):
        return self.cues.get(cue, (1e9, 1e9))[1]

    def p(self, cue, d=1.2, delay=0.0):
        return ease((self.t - self.c0(cue) - delay) / d)

    def lin(self, cue, d=1.2, delay=0.0):
        return clamp((self.t - self.c0(cue) - delay) / d)

    def on(self, cue):
        return self.t >= self.c0(cue)

    def span(self, cue, fade=0.5, until=None):
        """fade in at cue start, fade out at the end of cue line (or at `until` cue start)"""
        a = self.c0(cue)
        b = self.c0(until) if until else self.c1(cue)
        return clamp((self.t - a) / fade) * clamp((b - self.t) / fade + 1.0)

    def fin(self, d=0.6):
        return clamp(self.t / d) * clamp((self.dur - self.t) / d)


# ---------------------------------------------------------------- overlays
_cache = {}


def header_grad():
    if "hg" not in _cache:
        arr = np.zeros((H, W, 4), np.float32)
        y = np.arange(H)[:, None]
        a = np.clip(1 - (y - 120) / 330, 0, 1) ** 1.4 * 0.92
        b = np.clip((y - 1180) / 320, 0, 1) ** 1.2 * 0.94
        arr[..., 3] = np.maximum(a, b)
        _cache["hg"] = surface_from_rgba(arr)
    return _cache["hg"]


def draw_header(ctx, title, clock, prev_clock, k, alpha=1.0, axis_alpha=1.0):
    """series line + chapter title + time axis. k: 0..1 transition from prev_clock to clock"""
    text(ctx, "历史的关键一局 · 滑铁卢 1815", W / 2, 168, 28, GOLD, 0.85 * alpha, "mm", serif=True)
    if title:
        text(ctx, title, W / 2, 232, 50, IVORY, alpha, "mm", bold=True, serif=True, halo=8, halo_a=0.6)
    if axis_alpha <= 0:
        return
    x0, x1, y = 90, 990, 318
    a = axis_alpha
    ctx.set_source_rgba(*DIM, 0.55 * a); ctx.set_line_width(2)
    ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
    n = len(AXIS)
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]

    def xi(c):
        return xs[AXIS.index(c)] if c in AXIS else None

    cx = xi(clock); px = xi(prev_clock) if prev_clock else None
    cur = cx if px is None or cx is None else lerp(px, cx, ease(k))
    if cur is not None:
        ctx.set_source_rgba(*GOLD, 0.9 * a); ctx.set_line_width(4)
        ctx.move_to(x0, y); ctx.line_to(cur, y); ctx.stroke()
    for c, x in zip(AXIS, xs):
        hit = cur is not None and x <= cur + 1
        is_cur = c == clock
        r = 9 if is_cur else 6
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(*(GOLD if hit else DIM), (1 if hit else 0.6) * a); ctx.fill()
        text(ctx, c, x, y - 28, 30 if is_cur else 24, GOLD if is_cur else DIM, (1.0 if is_cur else 0.7) * a, "mm", bold=is_cur)
        if is_cur:
            text(ctx, "约 " + AXIS_LABEL[c], min(max(x, 120), W - 120), y + 34, 26, IVORY, 0.9 * a * ease(k), "mm")


def draw_badges(ctx, kind="map"):
    lab = {"map": "地图示意", "ill": "情景示意", "card": None}.get(kind)
    for i, s in enumerate(["AI配音"] + ([lab] if lab else [])):
        font(ctx, 22)
        w = text_w(ctx, s) + 22
        x = W - 30 - w; y = 380 + i * 42
        rrect(ctx, x, y, w, 32, 6); ctx.set_source_rgba(0, 0, 0, 0.45); ctx.fill()
        text(ctx, s, x + w / 2, y + 16, 22, IVORY, 0.8, "mm")


# ---------------------------------------------------------------- subtitles
def split_sub(say, maxc=30):
    """split a narration line into display chunks (each <= ~2 rows)"""
    parts = re.findall(r"[^，。？！：；]+[，。？！：；]?", say)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxc or not cur:
            cur += p
        else:
            chunks.append(cur); cur = p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        while len(c) > maxc + 6:
            out.append(c[:maxc]); c = c[maxc:]
        out.append(c)
    return out


def sub_display(c):
    c = c.strip()
    c = re.sub(r"[，。：；]$", "", c)
    return c


def draw_subtitle(ctx, s, alpha=1.0, y=1420):
    if not s or alpha <= 0:
        return
    size = 54
    lines = wrap_cjk(ctx, s, 940, size, bold=True)
    if len(lines) == 2 and len(lines[1]) <= 3:
        lines = wrap_cjk(ctx, s, 760, size, bold=True)
    y0 = y - (len(lines) - 1) * 36
    for i, L in enumerate(lines):
        text(ctx, L, W / 2, y0 + i * 72, size, (1, 0.98, 0.93), alpha, "mm", bold=True, halo=9, halo_a=0.9)


# ---------------------------------------------------------------- cards
def panel(ctx, x, y, w, h, alpha=1.0, border=GOLD):
    rrect(ctx, x, y, w, h, 14); ctx.set_source_rgba(0.05, 0.05, 0.06, 0.82 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*border, 0.65 * alpha); ctx.set_line_width(2); ctx.stroke()


def quote_card(ctx, orig, zh, src, alpha=1.0, y=830, latin=True, tag=None, orig_size=40, zh_size=50):
    """original text (italic Latin or CJK), Chinese gloss, source line."""
    if alpha <= 0:
        return
    maxw = 860
    if latin:
        ol = wrap_words(ctx, orig, maxw, orig_size)
    else:
        ol = wrap_cjk(ctx, orig, maxw, orig_size, serif=True)
    zl = wrap_cjk(ctx, zh, maxw, zh_size, bold=True, serif=True)
    sl = wrap_cjk(ctx, src, maxw, 26)
    hh = len(ol) * orig_size * 1.35 + 40 + len(zl) * zh_size * 1.35 + 30 + len(sl) * 36 + 80
    top = y - hh / 2
    panel(ctx, 60, top, 960, hh, alpha)
    text(ctx, "“", 100, top + 50, 110, GOLD, 0.5 * alpha, "mm", serif=True)
    yy = top + 60
    if tag:
        text(ctx, tag, 980, top + 34, 22, GOLD, 0.8 * alpha, "rm")
    for L in ol:
        if latin:
            text(ctx, L, W / 2, yy + orig_size * 0.5, orig_size, (0.86, 0.82, 0.72), alpha, "mm", family=LATIN_I, italic=True)
        else:
            text(ctx, L, W / 2, yy + orig_size * 0.5, orig_size, (0.86, 0.82, 0.72), alpha, "mm", serif=True)
        yy += orig_size * 1.35
    yy += 24
    ctx.set_source_rgba(*GOLD, 0.5 * alpha); ctx.set_line_width(1.5); ctx.move_to(W / 2 - 80, yy); ctx.line_to(W / 2 + 80, yy); ctx.stroke()
    yy += 30
    for L in zl:
        text(ctx, L, W / 2, yy + zh_size * 0.5, zh_size, IVORY, alpha, "mm", bold=True, serif=True)
        yy += zh_size * 1.35
    yy += 20
    for L in sl:
        text(ctx, L, W / 2, yy + 14, 26, GOLD, 0.9 * alpha, "mm")
        yy += 36


def big_number(ctx, s, sub, x, y, alpha=1.0, color=GOLD, size=150):
    if alpha <= 0:
        return
    text(ctx, s, x, y, size, color, alpha, "mm", bold=True, serif=True, halo=12, halo_a=0.7)
    if sub:
        text(ctx, sub, x, y + size * 0.62, 38, IVORY, alpha, "mm", halo=8)


def legend(ctx, items, alpha=1.0, y=1205):
    """items: [(color, label)]"""
    if alpha <= 0:
        return
    font(ctx, 26)
    tot = sum(text_w(ctx, l) + 70 for _, l in items)
    x = W / 2 - tot / 2
    for c, l in items:
        ctx.rectangle(x, y - 10, 36, 20); ctx.set_source_rgba(*c, 0.95 * alpha); ctx.fill()
        text(ctx, l, x + 46, y, 26, IVORY, 0.9 * alpha, "lm", halo=6)
        x += text_w(ctx, l) + 70
