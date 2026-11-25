# -*- coding: utf-8 -*-
"""通用画面部件：字幕、古文卡、类比卡、章节签、角标、粗箭头、兵团粒子、旗海、火与烟。"""
import math
import functools

import cairo
import numpy as np

import engine as E
from engine import W, H, C, clamp, prog, ease_out, ease_in, ease_io, smooth, lerp, fade

SUB_Y = 1530          # 字幕基线中心
SAFE_TOP = 170


# ── 字幕 ──────────────────────────────────────────────────
def split_sub(text, maxc=16):
    """把一句旁白切成若干屏（每屏 1–2 行，每行 ≤maxc 字），优先在标点处断。"""
    import re
    parts = re.findall(r"[^，。？！；：、]+[，。？！；：、]?", text)
    screens, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxc * 2 and (not cur or len(cur) + len(p) <= maxc * 2):
            cur += p
        else:
            if cur:
                screens.append(cur)
            cur = p
        while len(cur) > maxc * 2:
            screens.append(cur[:maxc * 2]); cur = cur[maxc * 2:]
    if cur:
        screens.append(cur)
    return screens


def sub_lines(screen, maxc=16):
    s = screen.rstrip("，。；：、")
    if len(s) <= maxc:
        return [s]
    # 两行：找最接近中间的标点，否则对半
    mid = len(s) / 2
    best = None
    for i, ch in enumerate(s):
        if ch in "，；：、？！" and 3 <= i + 1 <= len(s) - 3:
            if best is None or abs(i + 1 - mid) < abs(best - mid):
                best = i + 1
    if best is None or abs(best - mid) > maxc * 0.45 or best > maxc or len(s) - best > maxc:
        best = math.ceil(len(s) / 2)
    return [s[:best].rstrip("，；：、"), s[best:]]


def draw_subtitle(ctx, text, alpha=1.0, y=SUB_Y):
    ls = sub_lines(text)
    size = 54
    gap = 74
    y0 = y - (len(ls) - 1) * gap / 2
    for i, l in enumerate(ls):
        E.draw_text(ctx, l, W / 2, y0 + i * gap, "sans", "Bold", size, "#f6efe0", alpha, "cm",
                    stroke=3, stroke_color="#0a0806", shadow=6)


# ── 小角标 ────────────────────────────────────────────────
def badge(ctx, text, x, y, alpha=1.0, anchor="rt", col="#d9ccb0", size=24):
    w, h = E.text_size(text, "sans", "Medium", size)
    ax = {"l": 0, "r": 1, "c": 0.5}[anchor[0]]
    x0 = x - ax * (w + 24)
    E.rrect_path(ctx, x0, y, w + 24, h + 10, 6)
    E.set_col(ctx, "#000000", 0.38 * alpha); ctx.fill_preserve()
    E.set_col(ctx, col, 0.45 * alpha); ctx.set_line_width(1.2); ctx.stroke()
    E.draw_text(ctx, text, x0 + 12, y + 5, "sans", "Medium", size, col, 0.9 * alpha, "lt")


def chapter_tag(ctx, title, alpha=1.0):
    E.draw_text(ctx, "乱世起家录 · 刘备篇", 54, SAFE_TOP, "sans", "Medium", 26, C["gold"], 0.75 * alpha, "lt", tracking=0.12)
    if title:
        E.draw_text(ctx, title, 54, SAFE_TOP + 42, "serif", "Bold", 40, "#efe6d2", 0.92 * alpha, "lt", shadow=5)


def chapter_card(ctx, t, idx_title, t0, dur=2.0):
    """章节过场大字（t0 起，持续 dur）"""
    a = fade(t, t0, t0 + dur - 0.45, 0.35, 0.45)
    if a <= 0:
        return
    E.set_col(ctx, "#000000", 0.45 * a); ctx.rectangle(0, 0, W, H); ctx.fill()
    no, _, name = idx_title.partition(" · ")
    sc = 1.0 + 0.04 * prog(t, t0, dur)
    if name:
        E.draw_text(ctx, no, W / 2, H * 0.40, "serif", "Black", 120, C["gold"], a, "cm", shadow=8, scale=sc)
        E.line(ctx, W / 2 - 150 * a, H * 0.45, W / 2 + 150 * a, H * 0.45, C["gold"], 2, 0.7 * a)
        E.draw_text(ctx, name, W / 2, H * 0.49, "serif", "Black", 96, "#f3ead6", a, "cm", tracking=0.18, shadow=8, scale=sc)
    else:
        E.draw_text(ctx, idx_title, W / 2, H * 0.45, "serif", "Black", 104, "#f3ead6", a, "cm", tracking=0.2, shadow=8, scale=sc)


# ── 古文卡 ────────────────────────────────────────────────
LVL = {1: ("《三国志》正文", "#d9b46a"), 2: ("裴注引书", "#a9c0d6"), 4: ("《资治通鉴》", "#b8b0a0"), 9: ("经典", "#d9b46a")}


def quote_card(ctx, q, a, y=1020, appear=1.0, bai_a=None, width=960):
    """q = dict(orig, src, bai, lvl)。y 为卡片中心。"""
    if a <= 0.003:
        return
    size = 58 if len(q["orig"]) <= 30 else 52
    lines_ = E.wrap_cjk(q["orig"], "tc", "Bold", size, width - 110, tracking=0.06)
    lh = size * 1.42
    bsize = 36
    blines = E.wrap_cjk(q["bai"], "sans", "Regular", bsize, width - 110)
    bh = len(blines) * bsize * 1.45
    h = 70 + len(lines_) * lh + 64 + 26 + bh + 46
    y = min(y, 1455 - h / 2)
    x0 = (W - width) / 2
    y0 = y - h / 2 + (1 - ease_out(appear)) * 40
    # 底
    E.rrect_path(ctx, x0, y0, width, h, 14)
    E.set_col(ctx, "#0b0907", 0.80 * a); ctx.fill_preserve()
    E.set_col(ctx, C["gold"], 0.55 * a); ctx.set_line_width(2); ctx.stroke()
    E.rrect_path(ctx, x0 + 9, y0 + 9, width - 18, h - 18, 10)
    E.set_col(ctx, C["gold"], 0.18 * a); ctx.set_line_width(1); ctx.stroke()
    # 层级角标
    lab, lc = LVL.get(q.get("lvl", 1), LVL[1])
    E.draw_text(ctx, lab, x0 + 44, y0 + 30, "sans", "Medium", 24, lc, 0.85 * a, "lt", tracking=0.1)
    # 原文：逐字显现
    n_total = sum(len(l) for l in lines_)
    shown = n_total * clamp(appear * 1.0)
    k = 0
    yy = y0 + 76
    for l in lines_:
        for i, ch in enumerate(l):
            ca = clamp(shown - k) * a
            if ca > 0:
                xx = x0 + 55 + E.text_size(l[:i], "tc", "Bold", size, 0.06)[0] + i * 0  # tracking included
                E.draw_text(ctx, ch, xx, yy, "tc", "Bold", size, "#f4e7c8", ca, "lt", shadow=3)
            k += 1
        yy += lh
    # 出处（右下）
    yy += 6
    E.draw_text(ctx, "—— " + q["src"], x0 + width - 50, yy, "serif", "Medium", 30, C["gold2"], 0.9 * a, "rt")
    yy += 56
    E.line(ctx, x0 + 50, yy, x0 + width - 50, yy, C["gold"], 1, 0.35 * a)
    yy += 22
    ba = a * (1 if bai_a is None else bai_a)
    for bl in blines:
        E.draw_text(ctx, bl, x0 + 55, yy, "sans", "Regular", bsize, "#d8cdb6", ba, "lt")
        yy += bsize * 1.45
    return y0, y0 + h


# ── 现代类比卡 ────────────────────────────────────────────
def analogy_card(ctx, text, bias, a, ab, y=880, width=960):
    if a <= 0.003:
        return
    size = 42
    lines_ = E.wrap_cjk(text, "sans", "Medium", size, width - 100)
    blines = E.wrap_cjk(bias, "sans", "Regular", 36, width - 100) if bias else []
    h = 100 + len(lines_) * size * 1.5 + (80 + len(blines) * 36 * 1.5 if bias else 0) + 40
    x0 = (W - width) / 2
    y0 = y - h / 2
    E.rrect_path(ctx, x0, y0, width, h, 14)
    E.set_col(ctx, "#10141a", 0.84 * a); ctx.fill_preserve()
    E.set_col(ctx, "#7fa3c4", 0.55 * a); ctx.set_line_width(2); ctx.stroke()
    # 标签
    E.rrect_path(ctx, x0 + 40, y0 + 30, 150, 46, 6)
    E.set_col(ctx, "#7fa3c4", 0.9 * a); ctx.fill()
    E.draw_text(ctx, "现代类比", x0 + 115, y0 + 53, "sans", "Bold", 28, "#0d1116", a, "cm")
    yy = y0 + 100
    for l in lines_:
        E.draw_text(ctx, l, x0 + 50, yy, "sans", "Medium", size, "#e8eef4", a, "lt")
        yy += size * 1.5
    if bias and ab > 0:
        yy += 20
        E.line(ctx, x0 + 50, yy, x0 + width - 50, yy, "#c9785a", 1.5, 0.6 * ab)
        yy += 20
        E.draw_text(ctx, "类比偏差", x0 + 50, yy, "sans", "Bold", 30, "#e39a76", ab, "lt", tracking=0.1)
        yy += 52
        for l in blines:
            E.draw_text(ctx, l, x0 + 50, yy, "sans", "Regular", 36, "#efd9cb", ab, "lt")
            yy += 36 * 1.5


# ── 粗箭头 ────────────────────────────────────────────────
def thick_arrow(ctx, pts, frac, w0, w1, fill, edge, alpha=1.0, head=2.4, glow=None, smooth_n=10):
    """沿折线生长的锥形粗箭头。pts 屏幕坐标；frac 0..1"""
    if frac <= 0.01 or alpha <= 0:
        return
    P = E.smooth_path(pts, smooth_n) if len(pts) > 2 else pts
    seg = [math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1]) for i in range(len(P) - 1)]
    total = sum(seg)
    L = total * clamp(frac)
    hl = min(w1 * head * 1.1, L * 0.5)
    # 取到 L - hl 的身体中心线
    body = [P[0]]
    acc = 0
    for i, s in enumerate(seg):
        if acc + s >= L - hl:
            r = (L - hl - acc) / s if s else 0
            body.append((P[i][0] + (P[i + 1][0] - P[i][0]) * r, P[i][1] + (P[i + 1][1] - P[i][1]) * r))
            break
        body.append(P[i + 1]); acc += s
    tip_x, tip_y, ang = E.point_along(P, frac)
    if len(body) < 2:
        body = [P[0], (tip_x - math.cos(ang), tip_y - math.sin(ang))]
    # 左右边
    n = len(body)
    left, right = [], []
    cum = [0]
    for i in range(1, n):
        cum.append(cum[-1] + math.hypot(body[i][0] - body[i - 1][0], body[i][1] - body[i - 1][1]))
    blen = cum[-1] or 1
    for i in range(n):
        if i == 0:
            dx, dy = body[1][0] - body[0][0], body[1][1] - body[0][1]
        elif i == n - 1:
            dx, dy = body[-1][0] - body[-2][0], body[-1][1] - body[-2][1]
        else:
            dx, dy = body[i + 1][0] - body[i - 1][0], body[i + 1][1] - body[i - 1][1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = lerp(w0, w1, (cum[i] / blen) ** 0.8) / 2
        left.append((body[i][0] + nx * w, body[i][1] + ny * w))
        right.append((body[i][0] - nx * w, body[i][1] - ny * w))
    bx, by = body[-1]
    hw = w1 * head / 2 * 1.15
    nx, ny = -math.sin(ang), math.cos(ang)
    poly = left + [(bx + nx * hw, by + ny * hw), (tip_x + math.cos(ang) * 4, tip_y + math.sin(ang) * 4),
                   (bx - nx * hw, by - ny * hw)] + right[::-1]
    if glow:
        for k, (gw, ga) in enumerate(((22, 0.10), (12, 0.16))):
            ctx.new_path()
            for i, p in enumerate(poly):
                (ctx.move_to if i == 0 else ctx.line_to)(*p)
            ctx.close_path()
            E.set_col(ctx, glow, ga * alpha); ctx.set_line_width(gw); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ctx.new_path()
    for i, p in enumerate(poly):
        (ctx.move_to if i == 0 else ctx.line_to)(*p)
    ctx.close_path()
    # 渐变：尾淡头实
    g = cairo.LinearGradient(P[0][0], P[0][1], tip_x, tip_y)
    r, gg, b, _ = E.hexrgb(fill)
    g.add_color_stop_rgba(0, r, gg, b, 0.35 * alpha)
    g.add_color_stop_rgba(0.6, r, gg, b, 0.92 * alpha)
    g.add_color_stop_rgba(1, r, gg, b, 1.0 * alpha)
    ctx.set_source(g); ctx.fill_preserve()
    E.set_col(ctx, edge, 0.95 * alpha); ctx.set_line_width(3); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def arrow_style(side):
    return {
        "cao": dict(fill="#141312", edge=C["gold"], glow="#000000"),
        "liu": dict(fill=C["red"], edge="#ffb19f", glow=C["red2"]),
        "lv": dict(fill=C["blue"], edge="#cfe3f7", glow=C["blue2"]),
        "tao": dict(fill=C["green"], edge="#e2f2dc", glow=C["green"]),
        "yuan": dict(fill=C["yellow"], edge="#f6e2b0", glow=C["yellow2"]),
        "tian": dict(fill=C["gray"], edge="#d6dce4", glow=C["gray"]),
    }[side]


# ── 兵团粒子 ──────────────────────────────────────────────
class Troop:
    """一群士兵粒子，围绕一个锚点（可沿路径移动）成阵；可溃散。"""

    def __init__(self, n, spread=(90, 50), seed=1, col="#d23a2c", edge=None, size=4.0, shape="ellipse"):
        rng = np.random.default_rng(seed)
        self.n = n
        if shape == "ellipse":
            r = np.sqrt(rng.random(n)); th = rng.random(n) * 2 * np.pi
            self.off = np.stack([r * np.cos(th) * spread[0], r * np.sin(th) * spread[1]], 1)
        else:  # 方阵
            cols = int(math.sqrt(n * spread[0] / spread[1])) + 1
            ii = np.arange(n)
            self.off = np.stack([(ii % cols) / cols * 2 - 1, (ii // cols) / (n / cols) * 2 - 1], 1) * np.array(spread)
            self.off += rng.normal(0, 2.5, (n, 2))
        self.ph = rng.random(n) * 2 * np.pi
        self.vel = rng.normal(0, 1, (n, 2))
        self.lag = rng.random(n)
        self.col, self.edge, self.size = col, edge, size

    def draw(self, ctx, x, y, t, alpha=1.0, ang=0.0, rout=0.0, rout_dir=(0, 0), scale=1.0, march=0.0, count=None):
        if alpha <= 0.01:
            return
        off = self.off * scale
        if ang:
            ca, sa = math.cos(ang), math.sin(ang)
            off = np.stack([off[:, 0] * ca - off[:, 1] * sa, off[:, 0] * sa + off[:, 1] * ca], 1)
        jit = np.stack([np.sin(t * 3 + self.ph), np.cos(t * 2.3 + self.ph * 1.3)], 1) * (1.2 + march * 2.5)
        p = np.array([x, y]) + off + jit
        a = np.full(self.n, alpha)
        if rout > 0:
            d = np.array(rout_dir, float)
            p = p + (self.vel * 140 + d[None, :] * (120 + 160 * self.lag[:, None])) * rout
            a = a * np.clip(1 - rout * (0.4 + self.lag), 0, 1)
        m = self.n if count is None else int(min(self.n, count))
        s = self.size
        if self.edge:
            E.set_col(ctx, self.edge, 0.55 * alpha)
            for i in range(m):
                if a[i] > 0.02:
                    ctx.rectangle(p[i, 0] - s / 2 - 1, p[i, 1] - s / 2 - 1, s + 2, s + 2)
            ctx.fill()
        # 按透明度分 4 档批量填充
        bins = np.clip((a[:m] * 4).astype(int), 0, 4)
        for b in range(1, 5):
            idx = np.where(bins == b)[0]
            if len(idx) == 0:
                continue
            E.set_col(ctx, self.col, b / 4)
            for i in idx:
                ctx.rectangle(p[i, 0] - s / 2, p[i, 1] - s / 2, s, s)
            ctx.fill()
        return p


# ── 旗 ────────────────────────────────────────────────────
def flag(ctx, x, y, s, col, edge, t, alpha=1.0, ph=0.0, char=None):
    if alpha <= 0.01:
        return
    E.line(ctx, x, y, x, y - s * 1.9, "#2a2520", max(1.5, s * 0.08), alpha)
    ctx.new_path()
    wv = math.sin(t * 4 + ph) * s * 0.12
    ctx.move_to(x, y - s * 1.9)
    ctx.curve_to(x + s * 0.4, y - s * 1.9 + wv, x + s * 0.8, y - s * 1.9 - wv, x + s * 1.15, y - s * 1.85 + wv)
    ctx.line_to(x + s * 1.1, y - s * 1.15 + wv)
    ctx.curve_to(x + s * 0.8, y - s * 1.2 - wv, x + s * 0.4, y - s * 1.1 + wv, x, y - s * 1.15)
    ctx.close_path()
    E.set_col(ctx, col, alpha); ctx.fill_preserve()
    E.set_col(ctx, edge, 0.8 * alpha); ctx.set_line_width(max(1, s * 0.06)); ctx.stroke()
    if char and s > 26:
        E.draw_text(ctx, char, x + s * 0.55, y - s * 1.5, "serif", "Black", int(s * 0.52), edge, alpha, "cm")


class FlagSea:
    def __init__(self, n, w, h, seed=3):
        rng = np.random.default_rng(seed)
        self.p = rng.random((n, 2)) * np.array([w, h]) - np.array([w / 2, h / 2])
        self.p = self.p[np.argsort(self.p[:, 1])]
        self.ph = rng.random(n) * 6.28
        self.s = rng.uniform(0.75, 1.15, n)
        self.n = n

    def draw(self, ctx, cx, cy, t, size=26, alpha=1.0, col="#111111", edge=None, char="曹", count=None, persp=0.0):
        edge = edge or C["gold"]
        m = self.n if count is None else int(count)
        for i in range(m):
            x, y = cx + self.p[i, 0], cy + self.p[i, 1]
            sc = self.s[i] * (1 + persp * (self.p[i, 1] / 400))
            flag(ctx, x, y, size * sc, col, edge, t, alpha, self.ph[i], char if sc * size > 30 else None)


# ── 火与烟 ────────────────────────────────────────────────
def fire(ctx, x, y, s, t, alpha=1.0, seed=0):
    if alpha <= 0.01:
        return
    rng = np.random.default_rng(seed)
    g = cairo.RadialGradient(x, y - s * 0.3, 0, x, y - s * 0.3, s * 2.2)
    g.add_color_stop_rgba(0, 1.0, 0.55, 0.15, 0.45 * alpha)
    g.add_color_stop_rgba(1, 1.0, 0.3, 0.05, 0)
    ctx.set_source(g); ctx.arc(x, y - s * 0.3, s * 2.2, 0, 6.283); ctx.fill()
    for k in range(5):
        ph = seed * 1.7 + k * 1.3
        fl = 0.75 + 0.25 * math.sin(t * 9 + ph) + 0.1 * math.sin(t * 23 + ph * 2)
        hx = x + (k - 2) * s * 0.22 + math.sin(t * 5 + ph) * s * 0.08
        hh = s * (1.1 + 0.5 * (k % 2)) * fl
        ctx.new_path()
        ctx.move_to(hx - s * 0.28, y)
        ctx.curve_to(hx - s * 0.3, y - hh * 0.5, hx - s * 0.05, y - hh * 0.7, hx + math.sin(t * 7 + ph) * s * 0.1, y - hh)
        ctx.curve_to(hx + s * 0.08, y - hh * 0.65, hx + s * 0.3, y - hh * 0.45, hx + s * 0.28, y)
        ctx.close_path()
        col = (1.0, 0.42 + 0.3 * (k % 3) / 2, 0.08) if k % 2 == 0 else (1.0, 0.78, 0.3)
        ctx.set_source_rgba(*col, (0.85 if k % 2 == 0 else 0.7) * alpha)
        ctx.fill()


def smoke(ctx, x, y, s, t, alpha=1.0, seed=0, n=6):
    rng = np.random.default_rng(seed)
    for k in range(n):
        ph = (t * 0.35 + k / n + rng.random() * 0.1) % 1.0
        px = x + math.sin(k * 2.1 + t * 0.6) * s * 0.4 + ph * s * 0.6
        py = y - ph * s * 3.2
        r = s * (0.5 + ph * 1.4)
        a = alpha * 0.22 * math.sin(ph * math.pi)
        g = cairo.RadialGradient(px, py, 0, px, py, r)
        g.add_color_stop_rgba(0, 0.32, 0.30, 0.28, a)
        g.add_color_stop_rgba(1, 0.2, 0.2, 0.2, 0)
        ctx.set_source(g); ctx.arc(px, py, r, 0, 6.283); ctx.fill()


def glow_dot(ctx, x, y, r, col, alpha=1.0, pulse=0.0):
    rr = r * (1 + 0.15 * pulse)
    g = cairo.RadialGradient(x, y, 0, x, y, rr * 4)
    c = E.hexrgb(col)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], 0.6 * alpha)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g); ctx.arc(x, y, rr * 4, 0, 6.283); ctx.fill()
    E.circle(ctx, x, y, rr, col, alpha)
    E.circle(ctx, x, y, rr, "#ffffff", 0.6 * alpha, stroke=True, width=2)


def panel(ctx, x, y, w, h, alpha=1.0, edge=None, fill="#0c0a08", r=12, fa=0.82):
    E.rrect_path(ctx, x, y, w, h, r)
    E.set_col(ctx, fill, fa * alpha); ctx.fill_preserve()
    E.set_col(ctx, edge or C["gold"], 0.5 * alpha); ctx.set_line_width(2); ctx.stroke()


def label_pill(ctx, text, x, y, col, alpha=1.0, size=30, txt="#0c0a08", anchor="cm"):
    w, h = E.text_size(text, "sans", "Bold", size)
    ax = {"l": 0, "c": 0.5, "r": 1}[anchor[0]]
    x0 = x - ax * (w + 30)
    E.rrect_path(ctx, x0, y - (h + 12) / 2, w + 30, h + 12, (h + 12) / 2)
    E.set_col(ctx, col, alpha); ctx.fill()
    E.draw_text(ctx, text, x0 + (w + 30) / 2, y, "sans", "Bold", size, txt, alpha, "cm")
