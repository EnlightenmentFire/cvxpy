# -*- coding: utf-8 -*-
"""可复用的画面部件：字幕、竖排原文卡、章节卡、兵点、图标。"""
import math
import re

import numpy as np
import cairo

from engine import (W, H, C, hexrgb, clamp, prog, ease_out, ease_in, ease_io, ease_back, smooth, lerp, fade,
                    draw_text, text_size, wrap_cjk, set_col, rect, rrect_path, line, circle, polyline,
                    point_along, arrow, arrow_head, draw_seal)

SUB_Y = 1338        # 字幕中心
TOP_Y = 236         # 顶部章节标签
HAN = re.compile(r"[一-鿿0-9]")

BOOK_SEAL = {"宋書": "宋書", "南史": "南史", "魏書": "魏書", "晉書": "晉書", "資治通鑑": "通鑑", "廿二史劄記": "劄記"}


# ── 字幕 ──────────────────────────────────────────────────
def _quote_segments(line_text, in_q):
    """把一行切成 [(片段, 是否在「」里)]，返回片段与行末状态"""
    segs, cur, q = [], "", in_q
    for ch in line_text:
        if ch == "「":
            if cur:
                segs.append((cur, q))
            cur, q = ch, True
        elif ch == "」":
            cur += ch
            segs.append((cur, True)); cur, q = "", False
        else:
            cur += ch
    if cur:
        segs.append((cur, q))
    return segs, q


def balanced_wrap(text, size=50, maxw=900):
    """字幕折行：一行放得下就一行；否则在最靠近中间的标点处断成两行，避免单字成行"""
    if text_size(text, "sans", "Medium", size)[0] <= maxw:
        return [text]
    n = len(text)
    best, best_score = None, 1e9
    for i in range(2, n - 1):
        if text[i - 1] in "，、；：" or (text[i] == "「"):
            score = abs(i - n / 2)
            if score < best_score:
                best, best_score = i, score
    if best is None or best_score > n * 0.3:
        best = (n + 1) // 2
        while best < n - 1 and text[best] in "，。、；：！？」":
            best += 1
    a, b = text[:best].rstrip("，、"), text[best:]
    return [a, b]


def draw_subtitles(ctx, t, subs):
    # 同一时刻只显示一条：当前条从 t0-0.1 起，到下一条开始前 0.08 秒结束
    for i, s in enumerate(subs):
        nxt = subs[i + 1]["t0"] if i + 1 < len(subs) else 1e9
        end = min(s["t1"] + 0.12, nxt - 0.1)
        if not (s["t0"] - 0.1 <= t < end):
            continue
        a = ease_out(prog(t, s["t0"] - 0.1, 0.1))
        if nxt - s["t1"] > 0.3:
            a *= 1 - ease_in(prog(t, end - 0.12, 0.12))
        if a <= 0.01:
            continue
        lines = balanced_wrap(s["text"])
        n = len(lines)
        y0 = SUB_Y - (n - 1) * 34
        in_q = False
        for k, ln in enumerate(lines):
            segs, in_q = _quote_segments(ln, in_q)
            widths = [text_size(sg, "sans", "Medium", 50)[0] for sg, _ in segs]
            x = W / 2 - sum(widths) / 2
            for (sg, q), wdt in zip(segs, widths):
                draw_text(ctx, sg, x, y0 + k * 68, family="sans", weight="Medium", size=50,
                          color="#ecd09a" if q else "#f3ead8", alpha=a, anchor="lm", shadow=6, stroke=2,
                          stroke_color="#0b0806")
                x += wdt
        break


# ── 顶部章节标签 ──────────────────────────────────────────
NUMS = "零一二三四五六七八九"


def chapter_tag(ctx, t, idx, title, t0, t1):
    a = fade(t, t0, t1, 0.5, 0.4)
    if a <= 0:
        return
    w, _ = draw_text(ctx, "第" + NUMS[idx] + "章", 86, TOP_Y, family="serif", weight="Bold", size=28, color=C["gold"],
                     alpha=a, anchor="lm", tracking=0.1) or (0, 0)
    circle(ctx, 86 + w + 16, TOP_Y, 3, C["gold"], a * 0.8)
    draw_text(ctx, title, 86 + w + 32, TOP_Y, family="serif", weight="Bold", size=34, color=C["ink"], alpha=a * 0.92,
              anchor="lm", tracking=0.12)


def chapter_card(ctx, t, idx, title, t0, dur=1.7):
    """章节卡：墨色压暗 + 大字标题"""
    p = (t - t0) / dur
    if p < 0 or p > 1:
        return
    a_in = ease_out(prog(t, t0, 0.35))
    a_out = 1 - ease_in(prog(t, t0 + dur - 0.4, 0.4))
    a = a_in * a_out
    rect(ctx, 0, 0, W, H, "#0c0907", 0.78 * a)
    # 横向墨条
    bw = W * ease_out(prog(t, t0, 0.5))
    rect(ctx, (W - bw) / 2, H * 0.40, bw, 260, "#120d0a", 0.9 * a)
    line(ctx, (W - bw) / 2, H * 0.40, (W + bw) / 2, H * 0.40, C["gold"], 1.5, 0.6 * a)
    line(ctx, (W - bw) / 2, H * 0.40 + 260, (W + bw) / 2, H * 0.40 + 260, C["gold"], 1.5, 0.6 * a)
    s = 1 + 0.04 * (1 - ease_out(prog(t, t0, 0.8)))
    draw_text(ctx, "第" + NUMS[idx] + "章" if idx else "", W / 2, H * 0.40 + 62, family="serif", weight="Bold",
              size=34, color=C["gold"], alpha=a, anchor="cm", tracking=0.5)
    draw_text(ctx, title, W / 2, H * 0.40 + 160, family="serif", weight="Black", size=110, color=C["ink"],
              alpha=a, anchor="cm", tracking=0.25, scale=s, shadow=8)


# ── 竖排原文卡 ────────────────────────────────────────────
def quote_columns(q, maxcol=9):
    parts = [p for p in re.split(r"[，。！？；、]", q.replace("……", "，")) if p]
    cols = []
    for p in parts:
        k = math.ceil(len(p) / maxcol)
        size = math.ceil(len(p) / k)
        for i in range(0, len(p), size):
            cols.append(p[i:i + size])
    return cols


def quote_timing(T, line_id):
    """该行「」引文朗读的起止时间；不朗读的引文给出行首后一个短窗口"""
    ent = T.by_id[line_id]
    text = ent["text"]
    qs = [m for m in re.finditer(r"「([^」]*)」", text) if len(HAN.findall(m.group(1))) >= 4]
    if qs:
        m = qs[0]
        k0 = len(HAN.findall(text[: m.start()]))
        n = len(HAN.findall(m.group(1)))
        ct = ent["char_times"]
        return ct[min(k0, len(ct) - 1)][0], ct[min(k0 + n - 1, len(ct) - 1)][1], True
    return ent["start"] + 0.2, ent["start"] + 1.6, False


def vquote(ctx, t, T, line_id, cx, cy, size=66, alpha=1.0, t_out=None, frame=True, seal=True,
           color=None, src=True, hold=0.5, maxcol=9):
    ent = T.by_id[line_id]
    q, srcl = ent["quote"]
    r0, r1, spoken = quote_timing(T, line_id)
    t_in = r0 - 0.35
    if t_out is None:
        t_out = ent["end"] + hold
    a = fade(t, t_in, t_out, 0.35, 0.45) * alpha
    if a <= 0.005:
        return
    cols = quote_columns(q, maxcol)
    step = size * 1.16
    colw = size * 1.55
    nmax = max(len(c) for c in cols)
    bw = colw * len(cols) + size * 0.9
    bh = step * nmax + size * 0.9
    x0, y0 = cx - bw / 2, cy - bh / 2
    if frame:
        ctx.save()
        rrect_path(ctx, x0 - 30, y0 - 34, bw + 60, bh + 68, 10)
        set_col(ctx, "#0d0a08", 0.86 * a); ctx.fill_preserve()
        set_col(ctx, C["gold"], 0.55 * a); ctx.set_line_width(1.6); ctx.stroke()
        ctx.restore()
        # 角花
        for (xx, yy, sx, sy) in ((x0 - 18, y0 - 22, 1, 1), (x0 + bw + 18, y0 - 22, -1, 1),
                                 (x0 - 18, y0 + bh + 22, 1, -1), (x0 + bw + 18, y0 + bh + 22, -1, -1)):
            line(ctx, xx, yy, xx + 26 * sx, yy, C["gold"], 2.2, a * 0.8)
            line(ctx, xx, yy, xx, yy + 26 * sy, C["gold"], 2.2, a * 0.8)
    total = sum(len(c) for c in cols)
    k = 0
    col_txt = color or C["ink"]
    for ci, ctext in enumerate(cols):
        x = x0 + bw - size * 0.45 - colw * (ci + 0.5)
        for j, ch in enumerate(ctext):
            frac = (k + 0.5) / total
            tc = r0 + (r1 - r0) * frac if spoken else r0 + 1.2 * frac
            ca = ease_out(prog(t, tc - 0.18, 0.28)) * a
            if ca > 0.005:
                dy = 10 * (1 - ease_out(prog(t, tc - 0.18, 0.4)))
                draw_text(ctx, ch, x, y0 + size * 0.45 + j * step + dy, family="serif", weight="Black", size=size,
                          color=col_txt, alpha=ca, anchor="ct")
            k += 1
    if seal:
        book = re.findall(r"《([^》]+)》", srcl)
        name = BOOK_SEAL.get(book[-1], book[-1][:2]) if book else ""
        if "趙翼" in srcl:
            name = "趙翼"
        if "蕭方等" in srcl:
            name = "方等"
        sa = ease_out(prog(t, r1 - 0.1, 0.3)) * a
        if name and sa > 0:
            draw_seal(ctx, name, x0 - 2, y0 + bh - 4, size=78, alpha=sa * 0.95, rot=-0.06,
                      scale=1 + 0.25 * (1 - ease_back(prog(t, r1 - 0.1, 0.35))))
    if src:
        draw_text(ctx, srcl, cx, y0 + bh + 74, family="serif", weight="SemiBold", size=30, color=C["gold"],
                  alpha=a * 0.95, anchor="ct", tracking=0.06)


# ── 兵点 ──────────────────────────────────────────────────
class Dots:
    def __init__(self, n, seed=1):
        self.n = n
        rng = np.random.default_rng(seed)
        self.r = rng.random((n, 6))

    def blob(self, cx, cy, rx, ry, jitter=0.35):
        i = np.arange(self.n) + 0.5
        ang = i * 2.399963
        rad = np.sqrt(i / self.n)
        x = cx + rx * rad * np.cos(ang) + (self.r[:, 0] - 0.5) * jitter * rx * 2 / math.sqrt(self.n)
        y = cy + ry * rad * np.sin(ang) + (self.r[:, 1] - 0.5) * jitter * ry * 2 / math.sqrt(self.n)
        return np.stack([x, y], 1)

    def grid(self, cx, cy, cols, sp, jitter=0.0):
        i = np.arange(self.n)
        rows = math.ceil(self.n / cols)
        x = cx + (i % cols - (cols - 1) / 2) * sp + (self.r[:, 0] - 0.5) * jitter
        y = cy + (i // cols - (rows - 1) / 2) * sp + (self.r[:, 1] - 0.5) * jitter
        return np.stack([x, y], 1)

    def ring(self, cx, cy, r0, r1):
        i = np.arange(self.n)
        ang = self.r[:, 2] * 2 * math.pi
        rad = r0 + (r1 - r0) * self.r[:, 3]
        return np.stack([cx + rad * np.cos(ang), cy + rad * np.sin(ang)], 1)

    def scatter_from(self, pos, cx, cy, dist):
        """以 (cx,cy) 为中心向外散开"""
        d = pos - np.array([cx, cy])
        n = np.linalg.norm(d, axis=1, keepdims=True) + 1e-3
        u = d / n
        ang = (self.r[:, 4] - 0.5) * 0.9
        rot = np.stack([u[:, 0] * np.cos(ang) - u[:, 1] * np.sin(ang), u[:, 0] * np.sin(ang) + u[:, 1] * np.cos(ang)], 1)
        return pos + rot * dist * (0.6 + 0.8 * self.r[:, 5:6])

    def lerp(self, A, B, t, t0, dur, spread=0.0):
        """逐点错峰插值"""
        delay = self.r[:, 2] * spread
        p = np.clip((t - t0 - delay) / max(dur, 1e-3), 0, 1)
        p = p * p * (3 - 2 * p)
        return A + (B - A) * p[:, None]

    def draw(self, ctx, P, col, r=3.0, alpha=1.0, count=None, alphas=None):
        n = self.n if count is None else int(clamp(count, 0, self.n))
        if n <= 0 or alpha <= 0:
            return
        if alphas is None:
            set_col(ctx, col, alpha)
            for i in range(n):
                ctx.move_to(P[i, 0] + r, P[i, 1])
                ctx.arc(P[i, 0], P[i, 1], r, 0, 2 * math.pi)
            ctx.fill()
        else:
            rr, gg, bb, _ = hexrgb(col)
            for i in range(n):
                if alphas[i] <= 0.01:
                    continue
                ctx.set_source_rgba(rr, gg, bb, alpha * alphas[i])
                ctx.arc(P[i, 0], P[i, 1], r, 0, 2 * math.pi)
                ctx.fill()


# ── 卡片、标签 ────────────────────────────────────────────
def tag(ctx, text, x, y, alpha=1.0, col=None, size=30, anchor="lm", bar=True, weight="Medium", family="sans"):
    col = col or C["gold"]
    w, h = text_size(text, family, weight, size)
    ax = {"l": 0, "c": 0.5, "r": 1}[anchor[0]]
    xx = x - ax * (w + (18 if bar else 0))
    if bar:
        rect(ctx, xx, y - size * 0.62, 5, size * 1.24, col, alpha)
        xx += 18
    draw_text(ctx, text, xx, y, family=family, weight=weight, size=size, color=col, alpha=alpha, anchor="lm")


def card(ctx, x, y, w, h, alpha=1.0, edge=None, fill="#0f0c0a", r=10, edge_alpha=0.6):
    rrect_path(ctx, x, y, w, h, r)
    set_col(ctx, fill, 0.9 * alpha); ctx.fill_preserve()
    set_col(ctx, edge or C["gold"], edge_alpha * alpha); ctx.set_line_width(1.6); ctx.stroke()


def name_tile(ctx, x, y, title, sub=None, alpha=1.0, col=None, w=None, size=52, cx=True):
    col = col or C["ink"]
    tw, th = text_size(title, "serif", "Black", size)
    sw = text_size(sub, "sans", "Regular", 26)[0] if sub else 0
    w = w or max(tw, sw) + 60
    h = size + (50 if sub else 26)
    x0 = x - w / 2 if cx else x
    card(ctx, x0, y, w, h, alpha, edge=col)
    draw_text(ctx, title, x0 + w / 2, y + 12 + size / 2, family="serif", weight="Black", size=size, color=col,
              alpha=alpha, anchor="cm")
    if sub:
        draw_text(ctx, sub, x0 + w / 2, y + size + 30, family="sans", weight="Regular", size=26, color=C["dim"],
                  alpha=alpha, anchor="cm")
    return x0, y, w, h


def strike(ctx, x0, y, x1, frac, alpha=1.0, col=None, width=6):
    if frac <= 0:
        return
    col = col or C["red"]
    xe = x0 + (x1 - x0) * clamp(frac)
    set_col(ctx, col, alpha); ctx.set_line_width(width); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y + 3); ctx.line_to(xe, y - 3); ctx.stroke()


def cross(ctx, x, y, s, frac, alpha=1.0, col=None, width=8):
    col = col or C["red"]
    f1, f2 = clamp(frac * 2), clamp(frac * 2 - 1)
    set_col(ctx, col, alpha); ctx.set_line_width(width); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if f1 > 0:
        ctx.move_to(x - s, y - s); ctx.line_to(x - s + 2 * s * f1, y - s + 2 * s * f1); ctx.stroke()
    if f2 > 0:
        ctx.move_to(x + s, y - s); ctx.line_to(x + s - 2 * s * f2, y - s + 2 * s * f2); ctx.stroke()


def big_number(ctx, text, x, y, size=180, alpha=1.0, col=None, label=None, label_col=None, scale=1.0, anchor="cm"):
    col = col or C["red2"]
    draw_text(ctx, text, x, y, family="serif", weight="Black", size=size, color=col, alpha=alpha, anchor=anchor,
              shadow=8, scale=scale)
    if label:
        draw_text(ctx, label, x, y + size * 0.62, family="sans", weight="Medium", size=34, color=label_col or C["ink"],
                  alpha=alpha, anchor="ct")


def takeaway(ctx, t, t0, t1, lines_, y=560, size=58, col=None):
    """“这说明什么”结论卡"""
    a = fade(t, t0, t1, 0.45, 0.4)
    if a <= 0:
        return
    rect(ctx, 0, 0, W, H, "#0b0806", 0.85 * a)   # 底下的卡片压到很暗，结论字不和它们叠在一起
    draw_text(ctx, "这说明什么", W / 2, y - 110, family="serif", weight="Bold", size=34, color=C["gold"], alpha=a,
              anchor="cm", tracking=0.4)
    line(ctx, W / 2 - 150, y - 70, W / 2 + 150, y - 70, C["gold"], 1.5, a * 0.7)
    for i, ln in enumerate(lines_):
        li = ease_out(prog(t, t0 + 0.25 + i * 0.35, 0.5)) * a
        draw_text(ctx, ln, W / 2, y + i * (size * 1.5), family="serif", weight="Black", size=size,
                  color=col or C["ink"], alpha=li, anchor="cm", shadow=6)


# ── 图标 ──────────────────────────────────────────────────
def icon_house(ctx, x, y, s, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.move_to(x - s, y); ctx.line_to(x, y - s * 0.8); ctx.line_to(x + s, y); ctx.close_path(); ctx.fill()
    ctx.rectangle(x - s * 0.72, y, s * 1.44, s * 0.8); ctx.fill()


def icon_flag(ctx, x, y, s, col, alpha=1.0, wave=0.0):
    set_col(ctx, "#cdbb98", alpha * 0.9); ctx.set_line_width(max(1.5, s * 0.08))
    ctx.move_to(x, y); ctx.line_to(x, y - s * 1.5); ctx.stroke()
    set_col(ctx, col, alpha)
    ctx.move_to(x, y - s * 1.5)
    ctx.curve_to(x + s * 0.4, y - s * 1.5 - s * 0.12 * math.sin(wave), x + s * 0.7, y - s * 1.5 + s * 0.12 * math.sin(wave + 1),
                 x + s, y - s * 1.45)
    ctx.line_to(x + s, y - s * 0.95)
    ctx.curve_to(x + s * 0.7, y - s * 0.95 + s * 0.12 * math.sin(wave + 1), x + s * 0.4, y - s * 1.0, x, y - s * 0.95)
    ctx.close_path(); ctx.fill()


def icon_tree(ctx, x, y, s, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.set_line_width(s * 0.14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x, y); ctx.curve_to(x - s * 0.05, y - s * 0.5, x + s * 0.05, y - s * 0.8, x, y - s * 1.1); ctx.stroke()
    for (dx, dy, r) in ((0, -1.45, 0.55), (-0.45, -1.15, 0.42), (0.45, -1.2, 0.45), (-0.2, -1.75, 0.38), (0.3, -1.7, 0.36)):
        ctx.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi); ctx.fill()


def icon_boat(ctx, x, y, s, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.move_to(x - s, y); ctx.curve_to(x - s * 0.6, y + s * 0.45, x + s * 0.6, y + s * 0.45, x + s, y)
    ctx.close_path(); ctx.fill()
    ctx.set_line_width(s * 0.08); ctx.move_to(x, y); ctx.line_to(x, y - s * 1.1); ctx.stroke()
    ctx.move_to(x + s * 0.05, y - s * 1.05); ctx.line_to(x + s * 0.7, y - s * 0.2); ctx.line_to(x + s * 0.05, y - s * 0.2)
    ctx.close_path(); ctx.fill()


def icon_crown(ctx, x, y, s, col, alpha=1.0):
    """冕旒：横板 + 垂旒"""
    set_col(ctx, col, alpha)
    ctx.rectangle(x - s, y - s * 0.12, 2 * s, s * 0.24); ctx.fill()
    ctx.rectangle(x - s * 0.45, y + s * 0.12, s * 0.9, s * 0.5); ctx.fill()
    ctx.set_line_width(max(1.2, s * 0.05))
    for k in range(7):
        xx = x - s * 0.9 + k * s * 0.3
        ctx.move_to(xx, y + s * 0.12); ctx.line_to(xx, y + s * 0.55); ctx.stroke()
        ctx.arc(xx, y + s * 0.6, s * 0.05, 0, 2 * math.pi); ctx.fill()


def icon_gate(ctx, x, y, w, h, col, alpha=1.0, open_=0.0):
    """城门：城楼 + 两扇门（open_ 0..1）"""
    set_col(ctx, col, alpha)
    ctx.rectangle(x - w / 2, y - h, w, h); ctx.fill()
    # 城楼
    ctx.move_to(x - w * 0.42, y - h); ctx.line_to(x - w * 0.5, y - h - h * 0.14); ctx.line_to(x + w * 0.5, y - h - h * 0.14)
    ctx.line_to(x + w * 0.42, y - h); ctx.close_path(); ctx.fill()
    ctx.rectangle(x - w * 0.32, y - h - h * 0.32, w * 0.64, h * 0.18); ctx.fill()
    ctx.move_to(x - w * 0.4, y - h - h * 0.32); ctx.line_to(x, y - h - h * 0.5); ctx.line_to(x + w * 0.4, y - h - h * 0.32)
    ctx.close_path(); ctx.fill()
    # 门洞
    gw, gh = w * 0.34, h * 0.62
    set_col(ctx, "#050403", alpha)
    ctx.move_to(x - gw / 2, y); ctx.line_to(x - gw / 2, y - gh * 0.7)
    ctx.arc(x, y - gh * 0.7, gw / 2, math.pi, 2 * math.pi); ctx.line_to(x + gw / 2, y); ctx.close_path(); ctx.fill()
    # 门扇
    dw = gw / 2 * (1 - open_)
    set_col(ctx, "#5b3a22", alpha)
    ctx.rectangle(x - gw / 2, y - gh * 0.7, dw, gh * 0.7); ctx.fill()
    ctx.rectangle(x + gw / 2 - dw, y - gh * 0.7, dw, gh * 0.7); ctx.fill()
    # 砖缝
    set_col(ctx, "#000000", alpha * 0.35); ctx.set_line_width(1)
    for k in range(1, 8):
        yy = y - h * k / 8
        ctx.move_to(x - w / 2, yy); ctx.line_to(x - gw / 2 - 2, yy)
        ctx.move_to(x + gw / 2 + 2, yy); ctx.line_to(x + w / 2, yy)
    ctx.stroke()


def icon_granary(ctx, x, y, w, h, col, alpha=1.0, open_=0.0):
    set_col(ctx, col, alpha)
    ctx.move_to(x - w * 0.6, y - h * 0.62); ctx.line_to(x, y - h); ctx.line_to(x + w * 0.6, y - h * 0.62); ctx.close_path(); ctx.fill()
    ctx.rectangle(x - w / 2, y - h * 0.62, w, h * 0.62); ctx.fill()
    set_col(ctx, "#000000", alpha * 0.3); ctx.set_line_width(1.2)
    for k in range(1, 6):
        xx = x - w / 2 + w * k / 6
        ctx.move_to(xx, y - h * 0.6); ctx.line_to(xx, y); ctx.stroke()
    # 门
    dw, dh = w * 0.3, h * 0.42
    set_col(ctx, "#f2c879", alpha * 0.55 * open_)
    ctx.rectangle(x - dw / 2, y - dh, dw, dh); ctx.fill()
    set_col(ctx, "#4d321c", alpha)
    ctx.rectangle(x - dw / 2, y - dh, dw / 2 * (1 - open_), dh); ctx.fill()
    ctx.rectangle(x + dw / 2 - dw / 2 * (1 - open_), y - dh, dw / 2 * (1 - open_), dh); ctx.fill()


def icon_coins(ctx, x, y, s, col, alpha=1.0, n=3):
    """串钱"""
    for k in range(n):
        xx = x + (k - (n - 1) / 2) * s * 0.9
        set_col(ctx, col, alpha); ctx.set_line_width(s * 0.06)
        ctx.move_to(xx, y - s * 0.9); ctx.line_to(xx, y + s * 0.9); ctx.stroke()
        for j in range(7):
            yy = y - s * 0.75 + j * s * 0.25
            ctx.save(); ctx.translate(xx, yy); ctx.scale(1, 0.35)
            ctx.arc(0, 0, s * 0.28, 0, 2 * math.pi); ctx.restore()
            set_col(ctx, col, alpha); ctx.fill()


def icon_dice(ctx, x, y, s, col, alpha=1.0, n=5):
    """樗蒲五木：扁平木子"""
    for k in range(n):
        xx = x + (k - (n - 1) / 2) * s * 0.55
        ctx.save(); ctx.translate(xx, y + (k % 2) * s * 0.12); ctx.rotate((k - 2) * 0.18)
        rrect_path(ctx, -s * 0.16, -s * 0.5, s * 0.32, s, s * 0.12)
        set_col(ctx, col if k % 2 else "#1d1711", alpha); ctx.fill_preserve()
        set_col(ctx, col, alpha); ctx.set_line_width(2); ctx.stroke()
        ctx.restore()


def icon_person(ctx, x, y, s, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.arc(x, y - s * 1.55, s * 0.32, 0, 2 * math.pi); ctx.fill()
    ctx.move_to(x - s * 0.55, y); ctx.curve_to(x - s * 0.6, y - s * 0.7, x - s * 0.45, y - s * 1.15, x, y - s * 1.18)
    ctx.curve_to(x + s * 0.45, y - s * 1.15, x + s * 0.6, y - s * 0.7, x + s * 0.55, y); ctx.close_path(); ctx.fill()


def icon_robe(ctx, x, y, s, col, alpha=1.0):
    set_col(ctx, col, alpha)
    ctx.move_to(x - s * 0.25, y - s); ctx.line_to(x - s, y - s * 0.6); ctx.line_to(x - s * 0.8, y - s * 0.25)
    ctx.line_to(x - s * 0.5, y - s * 0.4); ctx.line_to(x - s * 0.55, y + s); ctx.line_to(x + s * 0.55, y + s)
    ctx.line_to(x + s * 0.5, y - s * 0.4); ctx.line_to(x + s * 0.8, y - s * 0.25); ctx.line_to(x + s, y - s * 0.6)
    ctx.line_to(x + s * 0.25, y - s); ctx.line_to(x, y - s * 0.7); ctx.close_path(); ctx.fill()


def icon_fire(ctx, x, y, s, alpha=1.0, phase=0.0):
    for k, (col, sc) in enumerate((("#7a2412", 1.0), ("#d0562c", 0.78), ("#f2a548", 0.5))):
        set_col(ctx, col, alpha * (0.9 if k else 0.8))
        fl = 1 + 0.12 * math.sin(phase * 7 + k)
        ctx.move_to(x - s * 0.5 * sc, y)
        ctx.curve_to(x - s * 0.6 * sc, y - s * 0.6 * sc * fl, x - s * 0.1 * sc, y - s * 0.8 * sc * fl, x, y - s * 1.3 * sc * fl)
        ctx.curve_to(x + s * 0.15 * sc, y - s * 0.8 * sc * fl, x + s * 0.6 * sc, y - s * 0.6 * sc * fl, x + s * 0.5 * sc, y)
        ctx.close_path(); ctx.fill()


def wind_arrows(ctx, t, x0, y0, x1, y1, n, col, alpha, t0):
    """东北风：从右上吹向左下的流线"""
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -math.sin(ang), math.cos(ang)
    for k in range(n):
        off = (k - (n - 1) / 2) * 95
        ph = ((t - t0) * 0.55 + k * 0.37) % 1.0
        sx, sy = x0 + nx * off, y0 + ny * off
        a = alpha * math.sin(ph * math.pi)
        seg = 0.28
        p0 = max(0.0, ph - seg)
        pts = []
        for j in range(12):
            u = p0 + (ph - p0) * j / 11
            pts.append((sx + math.cos(ang) * L * u + nx * 10 * math.sin(u * 9 + k), sy + math.sin(ang) * L * u + ny * 10 * math.sin(u * 9 + k)))
        polyline(ctx, pts, col, 3, a)
        if len(pts) > 1:
            arrow_head(ctx, pts[-1][0], pts[-1][1], math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0]), 12, col, a)
