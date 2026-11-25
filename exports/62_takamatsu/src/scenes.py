# -*- coding: utf-8 -*-
"""高松城水攻 — 各场景画面。每个渲染器 f(ctx, S)；S 见 frame.S（S.t 场内秒、S.p(cue) 0..1 缓动等）。"""
import math
import numpy as np
import cairo
from gfx import *
from frame import panel, quote_card, big_number, legend, PLATE_CY
import world as WD
from world import Cam, L_FIELDS, L_TOWN, L_BAILEY, L_FINAL, P, DIKE
import bigmap as BM
from bigmap import BCam, lerp_cam

INK = (0.06, 0.06, 0.07)
RICE = (0.93, 0.88, 0.72)


# ---------------------------------------------------------------- helpers
def blit(ctx, surf, alpha=1.0):
    ctx.set_source_surface(surf, 0, 0); ctx.paint_with_alpha(alpha)


def tag(ctx, s, x, y, color=GOLD, alpha=1.0, size=30, anchor="mm", fill=(0.04, 0.04, 0.05)):
    if alpha <= 0:
        return
    font(ctx, size, bold=True)
    w = text_w(ctx, s) + size * 1.0
    h = size * 1.6
    x0 = x - w / 2 if anchor[0] == "m" else (x if anchor[0] == "l" else x - w)
    rrect(ctx, x0, y - h / 2, w, h, 8); ctx.set_source_rgba(*fill, 0.80 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*color, 0.85 * alpha); ctx.set_line_width(2.5); ctx.stroke()
    text(ctx, s, x0 + w / 2, y, size, color if color != GOLD else IVORY, alpha, "mm", bold=True)


def card_lines(ctx, lines, y, alpha=1.0, size=48, color=IVORY, gap=1.5, serif=True, bold=True):
    if alpha <= 0:
        return
    for i, L in enumerate(lines):
        c = color
        if isinstance(L, tuple):
            L, c = L
        text(ctx, L, W / 2, y + i * size * gap, size, c, alpha, "mm", bold=bold, serif=serif, halo=size * 0.18, halo_a=0.7)


def dim(ctx, a):
    if a > 0:
        ctx.set_source_rgba(0, 0, 0, a); ctx.paint()


def xmark(ctx, x, y, r, alpha=1.0, color=RED, w=9):
    if alpha <= 0:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in (0, 1):
        ctx.move_to(x - r, y - r * (1 if k else -1)); ctx.line_to(x + r, y + r * (1 if k else -1))
    ctx.set_source_rgba(0, 0, 0, 0.5 * alpha); ctx.set_line_width(w + 6); ctx.stroke_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.set_line_width(w); ctx.stroke()


def pulse(ctx, x, y, t, color=GOLD, r=40, alpha=1.0):
    if alpha <= 0:
        return
    for k in range(2):
        ph = (t * 0.8 + k * 0.5) % 1
        ctx.arc(x, y, r * (0.6 + ph), 0, 2 * math.pi)
        ctx.set_source_rgba(*color, alpha * (1 - ph) * 0.8); ctx.set_line_width(4); ctx.stroke()


def coin(ctx, x, y, r, alpha=1.0):
    """方孔铜钱"""
    if alpha <= 0:
        return
    ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgba(0.72, 0.55, 0.26, alpha); ctx.fill()
    ctx.arc(x, y, r * 0.86, 0, 2 * math.pi); ctx.set_source_rgba(0.88, 0.70, 0.36, alpha); ctx.set_line_width(r * 0.08); ctx.stroke()
    ctx.rectangle(x - r * 0.24, y - r * 0.24, r * 0.48, r * 0.48); ctx.set_source_rgba(0.08, 0.06, 0.04, alpha); ctx.fill()


def rice_bag(ctx, x, y, s, alpha=1.0):
    if alpha <= 0:
        return
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.move_to(-30, 30); ctx.curve_to(-38, -10, -22, -30, -12, -34); ctx.line_to(12, -34)
    ctx.curve_to(22, -30, 38, -10, 30, 30); ctx.close_path()
    ctx.set_source_rgba(0.74, 0.64, 0.44, alpha); ctx.fill_preserve()
    ctx.set_source_rgba(0.35, 0.28, 0.18, alpha); ctx.set_line_width(2.5); ctx.stroke()
    ctx.move_to(-14, -26); ctx.line_to(14, -26); ctx.stroke()
    ctx.restore()


def scroll_icon(ctx, x, y, s=1.0, alpha=1.0, color=IVORY, seal=RED):
    if alpha <= 0:
        return
    w, h = 120 * s, 80 * s
    rrect(ctx, x - w / 2, y - h / 2, w, h, 6 * s); ctx.set_source_rgba(*color, 0.95 * alpha); ctx.fill()
    for i in range(4):
        ctx.move_to(x - w * 0.38, y - h * 0.25 + i * h * 0.16); ctx.line_to(x + w * 0.2, y - h * 0.25 + i * h * 0.16)
    ctx.set_source_rgba(0.2, 0.2, 0.2, 0.6 * alpha); ctx.set_line_width(2 * s); ctx.stroke()
    if seal:
        ctx.rectangle(x + w * 0.24, y + h * 0.05, w * 0.18, w * 0.18); ctx.set_source_rgba(*seal, alpha); ctx.fill()


def unit(ctx, x, y, color, alpha=1.0, w=40, h=26):
    unit_block(ctx, x, y, w, h, color, alpha, kind="inf")


def flagpost(ctx, x, y, color, alpha=1.0, s=1.0, t=0.0, ph=0.0):
    """2D nobori banner for maps"""
    if alpha <= 0:
        return
    hgt = 70 * s; wv = 22 * s
    ctx.set_source_rgba(0.05, 0.05, 0.05, alpha); ctx.set_line_width(3 * s)
    ctx.move_to(x, y); ctx.line_to(x, y - hgt); ctx.stroke()
    sway = math.sin(t * 2.6 + ph) * 3 * s
    ctx.move_to(x, y - hgt); ctx.line_to(x + wv + sway, y - hgt + 2); ctx.line_to(x + wv + sway * 1.3, y - hgt * 0.35)
    ctx.line_to(x, y - hgt * 0.38); ctx.close_path()
    ctx.set_source_rgba(0, 0, 0, 0.4 * alpha); ctx.set_line_width(3); ctx.stroke_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.fill()


# local-map camera ------------------------------------------------------------
class TD:
    def __init__(self, cx, cy, s, cys=PLATE_CY):
        self.cx, self.cy, self.s, self.cys = cx, cy, s, cys

    def __call__(self, x, y):
        return W / 2 + (x - self.cx) * self.s, self.cys - (y - self.cy) * self.s

    def mix(self, o, k):
        k = ease(k)
        return TD(lerp(self.cx, o.cx, k), lerp(self.cy, o.cy, k), math.exp(lerp(math.log(self.s), math.log(o.s), k)),
                  lerp(self.cys, o.cys, k))


def td_bg(ctx, cam, level, t, rain=0.0, tint=0.0, dimv=0.0):
    surf = WD.topdown(level, t, cam.cx, cam.cy, cam.s, cam.cys, tint=tint, rain=rain, dim=dimv)
    blit(ctx, surf)


def dike_line(ctx, cam, prog, alpha=1.0, width=10, glow=True):
    pts = [cam(*p) for p in DIKE]
    if prog <= 0 or alpha <= 0:
        return
    seg = cut(pts, prog)
    if len(seg) < 2:
        return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if glow:
        for wd, a in ((width * 4, 0.10), (width * 2.2, 0.22)):
            path(ctx, seg); ctx.set_source_rgba(*RED, a * alpha); ctx.set_line_width(wd); ctx.stroke()
    path(ctx, seg); ctx.set_source_rgba(*RED, alpha); ctx.set_line_width(width); ctx.stroke()
    x, y = seg[-1]
    if prog < 1:
        ctx.arc(x, y, width * 1.3, 0, 2 * math.pi); ctx.set_source_rgba(1, 0.85, 0.6, alpha); ctx.fill()


def local_labels(ctx, cam, alpha=1.0, names=("龙王山", "石井山", "蛙鼻", "门前村"), size=30):
    for n in names:
        x, y = cam(*P[n])
        label(ctx, n, x, y - 34, size, IVORY, alpha, dot=None)


def castle_label(ctx, cam, alpha=1.0, s="高松城", size=36, dy=-70):
    x, y = cam(0, 0)
    label(ctx, s, x, y + dy, size, (1, 0.95, 0.85), alpha, bold=True)


def river_label(ctx, cam, alpha=1.0):
    x, y = cam(-2.55, 2.6)
    label(ctx, "足守川", x - 10, y, 28, (0.75, 0.85, 0.95), alpha)


def worker_dots(ctx, cam, t, prog, alpha=1.0, n=420):
    """thousands of carriers streaming from villages to the dike front"""
    if alpha <= 0:
        return
    rng = np.random.default_rng(5)
    pts = WD.smooth([cam(*p) for p in DIKE], 6) if hasattr(WD, "smooth") else [cam(*p) for p in DIKE]
    seg = cut(pts, max(prog, 0.02))
    L = polyline_len(seg)
    srcs = [cam(-2.4, 0.6), cam(-0.1, -0.7), cam(0.7, 0.2), cam(-1.0, -0.6), cam(0.45, -0.6), cam(-1.5, 1.2)]
    for i in range(n):
        sx, sy = srcs[i % len(srcs)]
        # target: random point along built dike
        d = rng.random() * L
        acc = 0; tx, ty = seg[-1]
        for a, b in zip(seg[:-1], seg[1:]):
            dd = math.dist(a, b)
            if acc + dd >= d:
                k = (d - acc) / dd; tx, ty = lerp(a[0], b[0], k), lerp(a[1], b[1], k); break
            acc += dd
        ph = (t * rng.uniform(0.12, 0.25) + rng.random()) % 1
        x = lerp(sx, tx, ph) + rng.normal(0, 8); y = lerp(sy, ty, ph) + rng.normal(0, 8)
        a = alpha * min(1, ph * 5) * min(1, (1 - ph) * 5)
        ctx.arc(x, y, 3.2, 0, 2 * math.pi); ctx.set_source_rgba(1.0, 0.72, 0.45, 0.85 * a); ctx.fill()


# =============================================================================== s00 flood (hook)
def castle_sprites(ctx, cam, level, alpha=1.0):
    CS = 2.4
    bl = [  # (x, y, base height, size)
        (-0.03, 0.025, 6.9, 1.4), (0.02, 0.03, 6.9, 1.0), (0.025, -0.01, 6.9, 1.1), (-0.025, -0.015, 6.9, 0.9),
        (-0.10, 0.06, 4.95, 1.0), (-0.11, -0.06, 4.95, 0.9), (0.09, -0.07, 4.95, 0.8),
        (-0.17, 0.12, 4.75, 0.8), (0.15, 0.12, 4.75, 0.8), (-0.18, -0.13, 4.75, 0.7), (0.17, -0.12, 4.75, 0.8),
    ]
    items = []
    for (x, y, base, sz) in bl:
        p = cam.project(x * CS, y * CS, 0)
        if p and p[2] < 9000:
            items.append((p[2], p, base, sz))
    items.sort(key=lambda e: e[0])
    for _, p, base, sz in items:
        sub = clamp((level - base) / 1.6)
        if sub >= 1:
            continue
        WD.hut(ctx, p, alpha, sub=sub, w=sz * 2.6)


def town_sprites(ctx, cam, level, alpha=1.0, seed=2, n=70):
    rng = np.random.default_rng(seed)
    items = []
    for i in range(n):
        cx, cy, rr = [(-0.05, -0.62, 0.22), (0.62, 0.1, 0.16), (-0.7, 0.35, 0.15)][i % 3]
        x = cx + rng.normal(0, rr * 0.5); y = cy + rng.normal(0, rr * 0.5)
        base = 4.0 + rng.uniform(-0.3, 0.3)
        p = cam.project(x, y, 0)
        if p:
            items.append((p[2], p, base, rng.uniform(0.7, 1.1)))
    items.sort(key=lambda e: e[0])
    for _, p, base, sz in items:
        sub = clamp((level - base) / 1.4)
        if sub >= 1:
            continue
        WD.hut(ctx, p, alpha * 0.9, sub=sub, w=sz, color=(0.26, 0.23, 0.20))


def dike_glow_3d(ctx, cam, alpha=1.0, prog=1.0):
    pts = []
    for (a, b) in zip(DIKE[:-1], DIKE[1:]):
        for k in range(12):
            x, y = lerp(a[0], b[0], k / 12), lerp(a[1], b[1], k / 12)
            p = cam.project(x, y, 0.004)
            pts.append(p)
    pts.append(cam.project(*DIKE[-1], 0.004))
    pts = [p for p in pts if p]
    if len(pts) < 2:
        return
    seg = cut([(p[0], p[1]) for p in pts], prog)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for wd, a in ((22, 0.10), (10, 0.25), (4, 0.9)):
        path(ctx, seg); ctx.set_source_rgba(*RED, a * alpha); ctx.set_line_width(wd); ctx.stroke()


def inflow(ctx, cam, t, alpha=1.0):
    """muddy torrent pouring from the river into the basin at 门前"""
    if alpha <= 0:
        return
    src = (-2.15, 0.9)
    rng = np.random.default_rng(9)
    for i in range(90):
        ph = (t * rng.uniform(0.5, 0.9) + rng.random()) % 1
        ang = rng.uniform(-0.9, 0.2)
        r = 0.05 + ph * rng.uniform(0.4, 1.0)
        x = src[0] + math.cos(ang) * r; y = src[1] + math.sin(ang) * r - 0.1 * ph
        p = cam.project(x, y, 0.001)
        if not p:
            continue
        a = alpha * (1 - ph) * 0.8
        ctx.arc(p[0], p[1], max(1.5, p[2] * 0.004), 0, 2 * math.pi)
        ctx.set_source_rgba(0.85, 0.78, 0.62, a); ctx.fill()


def flood_level(t, t0=0.0, t1=9.0, a=4.1, b=L_FINAL):
    return lerp(a, b, ease_out(clamp((t - t0) / (t1 - t0))))


def sc_flood(ctx, S):
    t = S.t
    k = clamp(t / 16)
    cam = Cam(lerp(0.25, 0.05, k), lerp(-1.45, -1.05, k), lerp(0.24, 0.15, k), lerp(-9, -3, k), lerp(12, 9, k), F=1150)
    level = flood_level(t)
    flash = 0.0
    for ts in (1.3, 6.6, 12.4):
        d = t - ts
        if 0 <= d < 0.5:
            flash = max(flash, (1 - d / 0.5) * (0.9 if d < 0.08 or 0.15 < d < 0.22 else 0.4))
    blit(ctx, WD.oblique_surface(cam, level, t, rain=1.0, flash=flash))
    WD.ridges(ctx, cam, t, seed=1)
    dike_glow_3d(ctx, cam, 0.85)
    town_sprites(ctx, cam, level)
    castle_sprites(ctx, cam, level)
    inflow(ctx, cam, t, 1.0 - clamp((t - 9) / 3))
    for i, (x, y) in enumerate([(-1.9, 0.6), (-1.6, -0.6), (-0.6, -1.25), (0.4, -1.2), (1.0, -0.8), (1.25, 2.1), (1.5, 0.4)]):
        WD.banner(ctx, cam.project(x, y, 0), RED, 0.9, t, i, size=1.4)
    for ts in (1.3, 6.6, 12.4):
        WD.lightning(ctx, 300 + 420 * ((ts * 7) % 1), t - ts, seed=int(ts * 10), y1=cam.project(0, 3, 0)[1] if cam.project(0, 3, 0) else 700)
    WD.rain_overlay(ctx, t, 1.3, 0.5)
    # title on first frame (no black, no logo)
    a = 1 - clamp((t - S.c0("who")) / 0.8) * 0.0
    text(ctx, "高松城水攻", W / 2, 250, 112, (1, 0.97, 0.9), a, "mm", bold=True, serif=True, halo=14, halo_a=0.8)
    text(ctx, "不攻城，造一片湖", W / 2, 372, 52, GOLD, a, "mm", bold=True, serif=True, halo=10, halo_a=0.8)
    text(ctx, "1582 · 备中", W / 2, 448, 34, IVORY, 0.85 * a, "mm", serif=True, halo=8)
    # name card
    na = S.span("who", 0.5)
    if na > 0:
        panel(ctx, 70, 1120, 560, 150, na, RED)
        ctx.rectangle(70, 1120, 10, 150); ctx.set_source_rgba(*RED, na); ctx.fill()
        text(ctx, "羽柴秀吉", 110, 1172, 54, IVORY, na, "lm", bold=True, serif=True)
        text(ctx, "后来的丰臣秀吉 · 织田信长部将", 110, 1232, 28, GOLD, na, "lm")


# =============================================================================== s01 hookmap
def sc_hookmap(ctx, S):
    t = S.t
    c_marsh = TD(0, 0.05, 520)
    c_wide = TD(-0.45, 0.15, 175)
    c_west = TD(-1.6, -0.3, 128)
    cam = c_marsh.mix(c_wide, S.p("dike", 1.6))
    cam = cam.mix(c_west, S.p("flags", 1.6))
    cam = cam.mix(TD(-0.45, 0.1, 165), S.p("q", 1.4))
    lv = lerp(0.0, L_FINAL, ease(clamp((t - S.c0("rain") - 0.3) / 6.0)))
    rain = S.p("rain", 0.8) * (1 - S.p("flags", 2))
    td_bg(ctx, cam, lv, t, rain=rain)
    # marsh highlight
    ma = S.span("marsh", 0.5, until="dike")
    if ma > 0:
        x, y = cam(0, 0)
        ctx.arc(x, y, 330, 0, 2 * math.pi); ctx.set_source_rgba(0.45, 0.65, 0.55, 0.22 * ma); ctx.set_line_width(120); ctx.stroke()
        tag(ctx, "三面深沼", x - 300, y - 360, IVORY, ma * S.p("marsh", 0.6, 0.6), 34)
        tag(ctx, "一面水堀", x + 300, y + 340, IVORY, ma * S.p("marsh", 0.6, 1.6), 34)
        for i, s in enumerate(["骑兵冲不起来", "铁炮摆不开"]):
            aa = ma * S.p("marsh", 0.5, 3.0 + i * 1.2)
            tag(ctx, s, W / 2, 1080 + i * 78, RED, aa, 34)
    castle_label(ctx, cam, S.fin() * (1 - S.p("q", 0.6)), dy=-50 if cam.s < 300 else -160)
    # dike
    dp = S.lin("dike", 4.0, 0.4)
    dike_line(ctx, cam, dp, S.fin(), width=9)
    if S.on("dike"):
        a = S.span("dike", 0.5, until="coin")
        big_number(ctx, "12天", None, 820, 1150, a * S.p("dike", 0.6, 2.5), RED, 120)
        tag(ctx, "长堤 约4公里（通说）", 330, 1150, IVORY, a * S.p("dike", 0.6, 1.0), 32)
        local_labels(ctx, cam, a, ("门前村", "蛙鼻"))
    # coins / workers
    ca = S.span("coin", 0.5, until="rain")
    if ca > 0:
        worker_dots(ctx, cam, t, 1.0, ca, 300)
        panel(ctx, 120, 1000, 840, 230, ca, GOLD)
        rice_bag(ctx, 230, 1115, 1.3, ca)
        text(ctx, "=", 330, 1115, 64, GOLD, ca, "mm", bold=True)
        for i in range(3):
            coin(ctx, 420 + i * 22, 1115 - i * 6, 42, ca)
        text(ctx, "100文", 560, 1115, 52, IVORY, ca, "lm", bold=True, serif=True)
        text(ctx, "+ 米1升", 740, 1115, 52, IVORY, ca, "lm", bold=True, serif=True)
    # rain / lake
    if S.on("rain"):
        WD.rain_overlay(ctx, t, rain * 1.1, 0.42 * rain)
        a = S.span("rain", 0.5, until="flags")
        tag(ctx, "梅雨 · 足守川暴涨", W / 2, 1150, (0.75, 0.85, 0.95), a * S.p("rain", 0.6, 0.4), 34)
        river_label(ctx, cam, a)
        ia = S.span("rain2", 0.5, until="flags")
        tag(ctx, "湖面约200公顷", W / 2, 1150 - 0, GOLD, ia, 34)
        x, y = cam(0, 0)
        pulse(ctx, x, y, t, GOLD, 60, ia)
    # relief army
    fa = S.p("flags", 0.8) * (1 - S.p("q", 0.8) * 0.6)
    if fa > 0:
        for i, n in enumerate(["岩崎山", "日差山"]):
            hx, hy = P[n]
            for j in range(6):
                x, y = cam(hx + (j % 3 - 1) * 0.22, hy + (j // 3) * 0.2 - 0.1)
                flagpost(ctx, x, y, BLUE, fa * S.p("flags", 0.5, 0.2 + 0.12 * j + i * 0.4), 1.0, t, j)
            x, y = cam(hx, hy)
            label(ctx, n, x, y + 40, 28, (0.8, 0.88, 1.0), fa)
        tag(ctx, "毛利援军 · 约5万（秀吉书信）", W / 2, 1150, BLUE, S.span("flags", 0.5, until="q"), 32)
        ga = S.span("flags2", 0.5, until="q")
        a0 = cam(*P["岩崎山"]); b0 = cam(-0.25, 0.1)
        dashed(ctx, [a0, ((a0[0] + b0[0]) / 2, a0[1] - 30), b0], S.lin("flags2", 1.2), BLUE, 7, ga)
        mx, my = cam(-1.35, 0.4)
        xmark(ctx, mx, my, 30, ga * S.p("flags2", 0.4, 1.2))
    # questions
    qa = S.p("q", 0.7)
    if qa > 0:
        dim(ctx, 0.55 * qa)
        qs = ["为什么不攻城，偏要造一片湖？", "五万援军，为什么只能隔水看着？", "城，是被水攻下的，还是谈下来的？"]
        for i, q in enumerate(qs):
            cue = "q" if i < 2 else "q2"
            a = qa * S.p(cue, 0.6, 0.3 + (i * 2.2 if i < 2 else 0))
            panel(ctx, 80, 640 + i * 170, 920, 130, a, GOLD)
            text(ctx, f"{i + 1}", 140, 705 + i * 170, 56, GOLD, a, "mm", bold=True, serif=True)
            text(ctx, q, 190, 705 + i * 170, 42, IVORY, a, "lm", bold=True, serif=True)


# =============================================================================== s02 bigmap
CAM_WIDE = BCam(133.6, 34.9, 300, 860)
CAM_KINAI = BCam(134.6, 34.95, 330, 860)
CAM_ROUTE = BCam(134.25, 34.85, 520, 880)
CAM_BORDER = BCam(133.85, 34.75, 1300, 860)
CAM_TAK = BCam(133.82, 34.69, 2600, 860)


def sc_bigmap(ctx, S):
    t = S.t
    cam = CAM_KINAI
    cam = lerp_cam(cam, CAM_WIDE, S.p("mori", 1.6))
    cam = lerp_cam(cam, CAM_ROUTE, S.p("hide", 1.6))
    cam = lerp_cam(cam, CAM_BORDER, S.p("seven", 1.8))
    cam = lerp_cam(cam, CAM_TAK, S.p("siege", 1.8))
    BM.draw_map(ctx, cam, mori=S.p("mori", 1.0), oda=S.p("zoom", 1.0, 0.3))
    pa = S.fin()
    for n in ("京都", "安土"):
        BM.place(ctx, cam, n, pa, 32, dot=RED)
    if S.on("zoom"):
        x, y = cam(*BM.PLACES["京都"])
        tag(ctx, "织田信长", x, y - 80, RED, S.span("zoom", 0.5, until="hide") , 32)
    ma = S.p("mori", 0.8)
    BM.place(ctx, cam, "吉田郡山", ma * (1 - S.p("seven", 0.8)), 30, dot=BLUE)
    if ma > 0:
        x, y = cam(131.9, 34.95)
        text(ctx, "毛利氏", x, y, 64, (0.75, 0.85, 1.0), ma * (1 - S.p("seven", 0.8)), "mm", bold=True, serif=True, halo=10)
        x, y = cam(133.6, 34.25)
        text(ctx, "濑户内海", x, y, 30, (0.55, 0.65, 0.75), ma * (1 - S.p("seven", 0.8)) * 0.9, "mm", serif=True, halo=6)
        tag(ctx, "中国地方 = 本州西部", W / 2, 1180, IVORY, S.span("mori", 0.5, until="hide"), 32)
    # hideyoshi route
    ha = S.p("hide", 0.6)
    BM.place(ctx, cam, "姬路", ha, 32, dot=RED)
    if S.on("hide"):
        tag(ctx, "羽柴秀吉 · 西进总指挥", W / 2, 1180, RED, S.span("hide", 0.5, until="past"), 32)
    pa2 = S.p("past", 0.6)
    for i, (n, s) in enumerate([("三木", "三木城 围约两年"), ("鸟取", "鸟取城 围约四个月")]):
        a = pa2 * S.p("past", 0.5, 1.5 + i * 1.5) * (1 - S.p("seven", 0.6))
        x, y = BM.place(ctx, cam, n, a, 28, dot=RED, castle=True)
        if a > 0:
            tag(ctx, s, x, y - 52, IVORY, a, 26)
    # march arrow
    pts = [cam(134.69, 34.83), cam(134.35, 34.72), cam(133.95, 34.68), cam(133.84, 34.69)]
    arrow(ctx, pts, S.lin("march", 3.0, 0.3), RED, 46, S.fin(), dark=RED_D)
    BM.place(ctx, cam, "冈山", S.p("march", 0.6, 1.5), 28, dot=RED)
    if S.on("march"):
        a = S.span("march", 0.5, until="seven")
        tag(ctx, "羽柴 2万", 300, 1120, RED, a * S.p("march", 0.5, 0.4), 32)
        tag(ctx, "宇喜多 1万", 640, 1120, RED, a * S.p("march", 0.5, 3.0), 32)
        tag(ctx, "≈ 3万", W / 2, 1210, GOLD, a * S.p("march", 0.5, 5.0), 40)
    # border forts
    sa = S.p("seven", 0.8)
    forts = [(133.88, 34.80), (133.86, 34.75), (133.82, 34.69), (133.80, 34.66), (133.78, 34.63), (133.84, 34.61), (133.90, 34.72)]
    for i, (lo, la) in enumerate(forts):
        x, y = cam(lo, la)
        a = sa * S.p("seven", 0.4, 0.4 + i * 0.25)
        big = i == 2
        r = 16 if big else 10
        ctx.rectangle(x - r, y - r, 2 * r, 2 * r); ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.fill()
        ctx.rectangle(x - r + 3, y - r + 3, 2 * r - 6, 2 * r - 6); ctx.set_source_rgba(*BLUE, a); ctx.fill()
    if sa > 0:
        tag(ctx, "境目七城（示意）", W / 2, 1180, BLUE, S.span("seven", 0.5, until="siege"), 32)
    # siege ring
    ga = S.p("siege", 0.8, 1.2)
    if ga > 0:
        x, y = cam(133.82, 34.69)
        ctx.arc(x, y, 150, 0, 2 * math.pi); ctx.set_source_rgba(*RED, 0.9 * ga); ctx.set_line_width(14)
        ctx.set_dash([30, 18], -t * 40); ctx.stroke(); ctx.set_dash([])
        text(ctx, "备中高松城", x, y + 200, 44, IVORY, ga, "mm", bold=True, serif=True, halo=8)
        tag(ctx, "龙王山 · 秀吉本阵", x + 130, y - 200, RED, ga * S.p("siege", 0.5, 2.0), 28)


# =============================================================================== s03 offer
def ink_bg(ctx, t, warm=0.0):
    fill_bg(ctx, (0.07 + 0.03 * warm, 0.065 + 0.02 * warm, 0.06))
    g = cairo.RadialGradient(W / 2, 850, 50, W / 2, 850, 900)
    g.add_color_stop_rgba(0, 0.30, 0.24, 0.16, 0.35 + 0.2 * warm); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.paint()


def person(ctx, x, y, s, color, alpha=1.0, name=None, sub=None):
    """abstract seated figure (silhouette badge) — no portrait"""
    if alpha <= 0:
        return
    ctx.arc(x, y - 120 * s, 46 * s, 0, 2 * math.pi); ctx.set_source_rgba(*color, alpha); ctx.fill()
    ctx.move_to(x - 95 * s, y + 40 * s); ctx.curve_to(x - 90 * s, y - 60 * s, x - 40 * s, y - 70 * s, x, y - 70 * s)
    ctx.curve_to(x + 40 * s, y - 70 * s, x + 90 * s, y - 60 * s, x + 95 * s, y + 40 * s); ctx.close_path()
    ctx.fill()
    if name:
        text(ctx, name, x, y + 90 * s, 44 * s, IVORY, alpha, "mm", bold=True, serif=True, halo=6)
    if sub:
        text(ctx, sub, x, y + 145 * s, 28 * s, GOLD, alpha, "mm")


def sc_offer(ctx, S):
    t = S.t
    ink_bg(ctx, t)
    a = S.fin()
    person(ctx, 260, 820, 1.0, RED, a * S.p("offer", 0.6), "羽柴秀吉", "攻方")
    person(ctx, 820, 820, 1.0, BLUE, a, "清水宗治", "城主 · 守兵三千至五千")
    # offer card travels to the right
    k = S.p("offer", 1.6, 1.5)
    if S.on("offer"):
        x = lerp(330, 640, k)
        oa = a * S.span("offer", 0.4, until="refuse") if not S.on("refuse") else a * (1 - S.p("refuse", 0.4))
        panel(ctx, x - 150, 470, 300, 130, oa, GOLD)
        text(ctx, "备中 + 备后", x, 515, 42, IVORY, oa, "mm", bold=True, serif=True)
        text(ctx, "两国", x, 568, 30, GOLD, oa, "mm")
    # refusal: oath scroll goes to Mori Terumoto (up right)
    if S.on("refuse"):
        k2 = S.p("refuse", 2.2, 1.6)
        sx, sy = lerp(820, 700, k2), lerp(620, 480, k2)
        scroll_icon(ctx, sx, sy, 1.1, a * S.p("refuse", 0.4))
        tag(ctx, "信长誓书", sx, sy - 70, IVORY, a * S.p("refuse", 0.4), 28)
        ra = a * S.p("refuse", 0.6, 2.6)
        text(ctx, "→ 原封送交主君 毛利辉元", W / 2, 1060, 40, (0.8, 0.88, 1.0), ra, "mm", bold=True, serif=True, halo=6)
        xmark(ctx, 485, 535, 40, a * S.p("refuse", 0.4, 0.2) * (1 - S.p("assault", 0.5)))
    if S.on("refuse2"):
        text(ctx, "这座城，不卖。", W / 2, 1190, 76, (1, 0.95, 0.85), a * S.span("refuse2", 0.4, until="assault"), "mm", bold=True, serif=True, halo=10)
    if S.on("assault"):
        aa = a * S.p("assault", 0.5)
        arrow(ctx, [(260, 1120), (470, 1080), (650, 1060)], S.lin("assault", 1.2, 0.3) * (1 - 0.0), RED, 42, aa, dark=RED_D)
        arrow(ctx, [(700, 1170), (520, 1210), (330, 1220)], S.lin("assault", 1.0, 2.6), BLUE, 36, aa, dark=BLUE_D)
        tag(ctx, "4月27日 宇喜多军强攻 · 被击退", W / 2, 1320, RED, aa, 30)


# =============================================================================== s04 assault
def sc_assault(ctx, S):
    t = S.t
    cam = TD(-0.15, -0.1, 430)
    cam = cam.mix(TD(-0.45, 0.1, 170), S.p("flip", 1.6))
    lv = lerp(0, L_FIELDS + 0.15, S.p("flip", 2.5, 2.5))
    td_bg(ctx, cam, lv, t, dimv=0.15 * S.p("other", 0.6) * (1 - S.p("flip", 0.6)))
    a = S.fin()
    castle_label(ctx, cam, a * (1 - S.p("flip", 0.5)), dy=-200)
    # narrow causeways
    paths = [[(-1.0, -0.15), (-0.55, -0.1), (-0.28, -0.06)], [(-0.15, -1.0), (-0.08, -0.55), (-0.03, -0.3)], [(0.7, 0.5), (0.4, 0.3), (0.2, 0.15)]]
    pa = S.p("paths", 0.6) * (1 - S.p("flip", 0.6))
    for i, pp in enumerate(paths):
        pts = [cam(*q) for q in pp]
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        path(ctx, pts); ctx.set_source_rgba(0.85, 0.75, 0.55, 0.55 * pa); ctx.set_line_width(26); ctx.stroke()
        # red columns marching
        for j in range(6):
            ph = (t * 0.06 + j / 6) % 1
            q = cut(pts, ph)[-1]
            hit = S.on("cost") and (j + i) % 2 == 0 and ph > 0.55
            unit_block(ctx, q[0], q[1], 30, 20, RED, pa * (0.35 if hit else 1.0))
            if hit:
                xmark(ctx, q[0], q[1], 14, pa, IVORY, 4)
        # gunfire from castle
        if S.on("paths"):
            for k in range(3):
                ph = (t * 1.3 + k * 0.37 + i * 0.2) % 1
                if ph < 0.18:
                    tx = cut(pts, 0.75)[-1]
                    sx, sy = cam(pp[-1][0] * 0.6, pp[-1][1] * 0.6)
                    ctx.move_to(sx, sy); ctx.line_to(lerp(sx, tx[0], ph / 0.18), lerp(sy, tx[1], ph / 0.18))
                    ctx.set_source_rgba(1, 0.9, 0.6, pa * 0.9); ctx.set_line_width(3); ctx.stroke()
                    ctx.arc(sx, sy, 10, 0, 2 * math.pi); ctx.set_source_rgba(*FIRE, pa * (1 - ph / 0.18)); ctx.fill()
    if S.on("mud"):
        tag(ctx, "烂泥地：陷到小腿", W / 2, 1150, IVORY, S.span("mud", 0.5, until="paths"), 34)
    if S.on("paths"):
        tag(ctx, "只能挤在窄土路上", W / 2, 1150, RED, S.span("paths", 0.5, until="cost"), 34)
    if S.on("cost"):
        tag(ctx, "每一步，都拿人命去填", W / 2, 1150, RED, S.span("cost", 0.5, until="other"), 34)
    oa = S.span("other", 0.5, until="flip")
    if oa > 0:
        dim(ctx, 0.45 * oa)
        panel(ctx, 90, 560, 900, 520, oa)
        text(ctx, "秀吉的另一笔账", W / 2, 630, 44, GOLD, oa, "mm", bold=True, serif=True)
        rows = [("三木城", "围了将近两年", 1.0), ("鸟取城", "围了约四个月", 2.5)]
        for i, (n, s, d) in enumerate(rows):
            ra = oa * S.p("other", 0.5, d)
            text(ctx, n, 230, 740 + i * 100, 44, IVORY, ra, "lm", bold=True, serif=True)
            text(ctx, s, 470, 740 + i * 100, 40, IVORY, ra, "lm", serif=True)
        ra = oa * S.p("other", 0.6, 5.0)
        text(ctx, "围  <  攻", W / 2, 990, 72, GOLD, ra, "mm", bold=True, serif=True)
        text(ctx, "（代价）", W / 2 + 200, 995, 30, DIM, ra, "lm")
        ta = S.p("time", 0.5)
        if ta > 0:
            pass
    ta = S.span("time", 0.5, until="flip")
    if ta > 0:
        panel(ctx, 140, 1100, 800, 110, ta, BLUE)
        text(ctx, "毛利大军随时会到 · 等不起", W / 2, 1155, 38, (0.8, 0.88, 1.0), ta, "mm", bold=True)
    fa = S.p("flip", 0.6)
    if fa > 0:
        panel(ctx, 110, 1060, 860, 150, fa)
        text(ctx, "护城河", 300, 1135, 54, (0.75, 0.85, 0.95), fa, "mm", bold=True, serif=True)
        arrow(ctx, [(430, 1135), (620, 1135)], S.lin("flip", 0.8, 0.6), GOLD, 26, fa, glow=False)
        text(ctx, "蓄水池", 790, 1135, 54, GOLD, fa * S.p("flip", 0.5, 1.2), "mm", bold=True, serif=True)


# =============================================================================== s05 build
def sc_build(ctx, S):
    t = S.t
    cam = TD(-0.5, 0.1, 185)
    cam = cam.mix(TD(-0.45, -0.35, 230), S.p("pay", 1.4))
    cam = cam.mix(TD(-0.5, 0.1, 185), S.p("days", 1.4))
    td_bg(ctx, cam, 0.0, t, dimv=0.25 * S.p("money", 0.6))
    a = S.fin()
    # north/east hills highlight
    la = S.span("line", 0.5, until="line2")
    if la > 0:
        for (x, y, s) in [(0.4, 2.6, "北：山"), (2.0, 0.5, "东：山"), (-1.6, -1.6, "西南：敞开")]:
            sx, sy = cam(x, y)
            tag(ctx, s, sx, sy, IVORY if "敞" not in s else RED, la, 32)
    # dike drawn progressively: over line2 then grows by days
    prog = 0.0
    if S.on("line2"):
        prog = 0.999 * S.lin("line2", 4.5, 0.3)
    if S.on("pay"):
        prog = lerp(0.12, 0.999, clamp((t - S.c0("pay")) / max(S.c0("money") - S.c0("pay"), 1)))
    if S.on("line2") and not S.on("pay"):
        dashed(ctx, [cam(*p) for p in DIKE], prog, RED, 7, a)
    if S.on("pay"):
        worker_dots(ctx, cam, t, prog, a * S.p("pay", 0.8) * (1 - S.p("money", 0.8)), 520)
        dike_line(ctx, cam, prog, a, 10)
    local_labels(ctx, cam, a * S.p("line2", 0.6), ("门前村", "蛙鼻", "龙王山", "石井山"))
    castle_label(ctx, cam, a, dy=-60)
    river_label(ctx, cam, a * S.p("line2", 0.6))
    sa = S.span("spec", 0.5, until="pay")
    if sa > 0:
        panel(ctx, 110, 1020, 860, 200, sa)
        text(ctx, "通说（示意）", W / 2, 1060, 28, GOLD, sa, "mm")
        for i, (k, v) in enumerate([("长", "约4公里"), ("高", "约8米"), ("底宽", "24米"), ("顶宽", "12米")]):
            x = 210 + i * 220
            text(ctx, k, x, 1115, 30, DIM, sa, "mm")
            text(ctx, v, x, 1170, 40, IVORY, sa, "mm", bold=True, serif=True)
    pa = S.span("pay", 0.5, until="days")
    if pa > 0:
        panel(ctx, 120, 1020, 840, 190, pa, GOLD)
        rice_bag(ctx, 220, 1115, 1.1, pa)
        text(ctx, "每一袋土", 300, 1115, 40, IVORY, pa, "lm", bold=True)
        for i in range(2):
            coin(ctx, 560 + i * 20, 1115 - i * 5, 36, pa)
        text(ctx, "100文 + 米1升", 630, 1115, 40, GOLD, pa, "lm", bold=True)
        # counter
        n = int(clamp((t - S.c0("pay")) / 12) * 12000)
        text(ctx, f"已运土袋 {n:,}+", W / 2, 960, 34, IVORY, pa * 0.8, "mm", halo=6)
    if S.on("crowd"):
        tag(ctx, "苦役 → 抢着干的活计", W / 2, 1270, GOLD, S.span("crowd", 0.5, until="days"), 32)
    # days progress bar
    da = S.span("days", 0.5, until="money")
    if da > 0:
        k = S.lin("days", 3.0, 0.3)
        d = 8 + int(k * 11)
        panel(ctx, 110, 1030, 860, 180, da)
        text(ctx, f"5月{d}日", W / 2, 1085, 50, IVORY, da, "mm", bold=True, serif=True)
        ctx.rectangle(170, 1140, 740, 22); ctx.set_source_rgba(1, 1, 1, 0.15 * da); ctx.fill()
        ctx.rectangle(170, 1140, 740 * k, 22); ctx.set_source_rgba(*RED, da); ctx.fill()
        text(ctx, "开工", 170, 1185, 26, DIM, da, "lm"); text(ctx, "完工 · 12天", 910, 1185, 26, GOLD, da, "rm")
    # money mechanism
    ma = S.p("money", 0.6)
    if ma > 0:
        dim(ctx, 0.35 * ma)
        panel(ctx, 80, 560, 920, 640, ma, GOLD)
        coin(ctx, W / 2, 680, 70, ma)
        text(ctx, "钱", W / 2, 790, 44, GOLD, ma, "mm", bold=True, serif=True)
        for i, (s, x) in enumerate([("换时间", 300), ("换人命", 780)]):
            aa = ma * S.p("money", 0.5, 1.0 + i * 1.5)
            arrow(ctx, [(W / 2, 830), (x, 930)], aa, GOLD, 26, aa, glow=False)
            text(ctx, s, x, 990, 48, IVORY, aa, "mm", bold=True, serif=True)
        m2 = S.p("money2", 0.6)
        if m2 > 0:
            for i, (s, c, v) in enumerate([("拼人命", RED, 0.35), ("拼财力", GOLD, 0.9)]):
                y = 1075 + i * 62
                text(ctx, s, 160, y, 34, IVORY, m2, "lm", bold=True)
                ctx.rectangle(330, y - 16, 560, 32); ctx.set_source_rgba(1, 1, 1, 0.1 * m2); ctx.fill()
                kk = S.p("money2", 1.2, 0.4 + i * 1.2)
                ctx.rectangle(330, y - 16, 560 * v * kk if i else 560 * lerp(1, v, kk), 32); ctx.set_source_rgba(*c, m2); ctx.fill()


# =============================================================================== s06 lake (oblique, 3 rises)
def lake_level(S):
    lv = 3.0
    for cue, L in (("lv1", L_FIELDS + 0.1), ("lv2", L_TOWN + 0.15), ("lv3", L_BAILEY + 0.1), ("island", L_FINAL)):
        if S.on(cue):
            lv = lerp(lv, L, S.p(cue, 3.0))
    return lv


def sc_lake(ctx, S):
    t = S.t
    k = clamp(t / max(S.dur, 1))
    cam = Cam(lerp(-0.1, 0.25, k), lerp(-2.3, -1.85, k), lerp(0.42, 0.30, k), lerp(-6, 4, k), lerp(14, 11, k), F=1150)
    lv = lake_level(S)
    rain = 1.0 - 0.5 * S.p("watch", 1.5)
    flash = 0.0
    for ts in (2.0, 13.0, 24.0):
        d = t - ts
        if 0 <= d < 0.4:
            flash = (1 - d / 0.4) * 0.7
    blit(ctx, WD.oblique_surface(cam, lv, t, rain=rain, flash=flash))
    WD.ridges(ctx, cam, t, seed=4)
    town_sprites(ctx, cam, lv)
    castle_sprites(ctx, cam, lv)
    if S.on("lv3"):
        rng = np.random.default_rng(4)
        for i in range(5):
            x = rng.uniform(-0.6, 0.5) + 0.02 * t; y = rng.uniform(-0.5, 0.6)
            WD.boat(ctx, cam.project(x, y, 0), S.p("lv3", 1.0, 1.0 + i * 0.4) * (1 - S.p("watch", 1.0) * 0.5))
    # watch tower + red banners on dike (foreground)
    wa = S.p("watch", 0.8)
    for i, (x, y) in enumerate([(-0.85, -1.18), (-0.3, -1.29), (0.2, -1.27), (0.65, -1.15)]):
        WD.banner(ctx, cam.project(x, y, 0), RED, 0.6 + 0.4 * wa, t, i, 1.2)
    if wa > 0:
        p = cam.project(-0.05, -1.30, 0)
        if p:
            x, y, kk = p
            hh = 0.05 * kk; ww = 0.015 * kk
            ctx.set_source_rgba(0.12, 0.09, 0.07, wa); ctx.set_line_width(max(2, ww * 0.12))
            for dx in (-ww / 2, ww / 2):
                ctx.move_to(x + dx, y); ctx.line_to(x + dx * 0.6, y - hh); ctx.stroke()
            ctx.rectangle(x - ww * 0.55, y - hh - ww * 0.4, ww * 1.1, ww * 0.4); ctx.fill()
            ctx.move_to(x - ww * 0.75, y - hh - ww * 0.4); ctx.line_to(x, y - hh - ww * 0.9); ctx.line_to(x + ww * 0.75, y - hh - ww * 0.4)
            ctx.close_path(); ctx.fill()
            tag(ctx, "瞭望台", x, y - hh - ww * 1.3 - 40, RED, wa, 30)
    WD.rain_overlay(ctx, t, rain, 0.45 * rain)
    # water gauge (left)
    ga = S.fin()
    x0, y0, y1 = 70, 1180, 560
    ctx.rectangle(x0, y1, 16, y0 - y1); ctx.set_source_rgba(1, 1, 1, 0.12 * ga); ctx.fill()
    marks = [("稻田", L_FIELDS), ("屋舍", L_TOWN), ("城内", L_BAILEY), ("本丸", 6.9)]
    def gy(v):
        return y0 - (v - 3.0) / (7.2 - 3.0) * (y0 - y1)
    for i, (n, v) in enumerate(marks):
        yy = gy(v)
        ctx.move_to(x0, yy); ctx.line_to(x0 + 32, yy); ctx.set_source_rgba(*IVORY, 0.7 * ga); ctx.set_line_width(2); ctx.stroke()
        hit = lv >= v - 0.05
        text(ctx, n, x0 + 44, yy, 26, GOLD if hit else IVORY, ga * (1 if hit else 0.6), "lm", bold=hit, halo=6)
    ctx.rectangle(x0, gy(lv), 16, y0 - gy(lv)); ctx.set_source_rgba(*WD.MUD, ga); ctx.fill()
    for i, cue in enumerate(("lv1", "lv2", "lv3")):
        if S.on(cue):
            ia = S.span(cue, 0.4)
            big_number(ctx, f"第{'一二三'[i]}次上涨", None, W / 2, 560, ia, GOLD, 64)
    ia = S.span("island", 0.5)
    if ia > 0:
        p = cam.project(0, 0, 0)
        if p:
            pulse(ctx, p[0], p[1], t, GOLD, 50, ia)
            tag(ctx, "本丸 · 湖中孤岛", p[0], p[1] - 140, GOLD, ia, 32)


# =============================================================================== s07 section
def sc_section(ctx, S):
    t = S.t
    ink_bg(ctx, t)
    a = S.fin()
    # diagram coords: 1 m = 70 px vertical, width scaled 1 m = 26 px
    base_y = 1060
    cx = W / 2
    def X(m):
        return cx + m * 26
    def Y(m):
        return base_y - m * 48
    # ground
    ctx.rectangle(40, base_y, 1000, 30); ctx.set_source_rgba(0.35, 0.28, 0.18, a); ctx.fill()
    text(ctx, "地面", 70, base_y + 60, 26, DIM, a, "lm")
    la = S.p("legend", 0.8) if S.on("legend") else S.p("q", 0.8, 0.5)
    # legendary dike trapezoid: bottom 24, top 12, h 8 (relative to ground ~ 3 m)
    pts = [(X(-12), Y(0)), (X(-6), Y(8)), (X(6), Y(8)), (X(12), Y(0))]
    path(ctx, pts); ctx.close_path()
    ctx.set_source_rgba(0.62, 0.50, 0.34, 0.85 * la * (1 - 0.5 * S.p("survey", 0.8))); ctx.fill_preserve()
    ctx.set_source_rgba(*RED, la); ctx.set_line_width(3); ctx.stroke()
    if la > 0:
        text(ctx, "通说：高约8米", X(6) + 30, Y(8), 34, IVORY, la, "lm", bold=True)
        text(ctx, "顶宽12米", W / 2, Y(8) - 36, 30, IVORY, la, "mm")
        text(ctx, "底宽24米", W / 2, base_y + 60, 30, IVORY, la, "mm")
        text(ctx, "示意 · 不按比例", W - 60, base_y + 60, 24, DIM, la, "rm")
    sa = S.p("survey", 0.8, 0.8)
    if sa > 0:
        # survey crest: elevation ~5 m; ground around 3 m -> ~2 m above plain
        yv = Y(2.0)
        dashed(ctx, [(70, yv), (1010, yv)], S.lin("survey", 1.5, 0.8), (0.75, 0.88, 1.0), 6, sa, (18, 12))
        text(ctx, "2008年调查推测：堤顶约在海拔5米上下", W / 2, yv + 50, 34, (0.8, 0.9, 1.0), sa, "mm", bold=True, halo=6)
        text(ctx, "（平原地面约海拔3米上下，示意）", W / 2, yv + 100, 26, DIM, sa, "mm")
    src_a = S.p("survey", 0.6, 2.0)
    text(ctx, "冈山市教育委员会《备中高松城水攻筑堤迹》（2008）", W / 2, 1290, 28, GOLD, src_a * a, "mm")
    qa = S.span("q", 0.5, until="legend")
    if qa > 0:
        text(ctx, "真有那么高吗？", W / 2, 500, 72, IVORY, qa, "mm", bold=True, serif=True, halo=8)
    if S.on("smaller"):
        text(ctx, "水攻是真的，规模可能被讲大了", W / 2, 500, 50, GOLD, S.span("smaller", 0.5, until="point"), "mm", bold=True, serif=True)
    if S.on("point"):
        text(ctx, "要点：让低地蓄得住水", W / 2, 500, 58, IVORY, S.p("point", 0.6), "mm", bold=True, serif=True)


# =============================================================================== s08 relief
def sc_relief(ctx, S):
    t = S.t
    cam = TD(-2.4, -0.6, 118)
    cam = cam.mix(TD(-1.9, -0.3, 150), S.p("forward", 1.6))
    td_bg(ctx, cam, L_FINAL, t, dimv=0.2 * S.p("count", 0.6) * (1 - S.p("same", 0.6)))
    a = S.fin()
    dike_line(ctx, cam, 1.0, a, 7, glow=False)
    castle_label(ctx, cam, a, dy=-50)
    for i, (x, y) in enumerate([(1.25, 2.15), (1.5, 0.4), (1.0, -0.8), (-0.6, -1.3), (-1.6, -0.75)]):
        sx, sy = cam(x, y)
        flagpost(ctx, sx, sy, RED, a, 0.8, t, i)
    # blue arrows from the west (from 猿挂城 off-map)
    ar = S.p("arrive", 0.6)
    for i, (dst, nm, who) in enumerate([(P["岩崎山"], "岩崎山", "吉川元春"), (P["日差山"], "日差山", "小早川隆景")]):
        src = (-8.5, dst[1] + (0.6 if i == 0 else -0.6))
        pts = [cam(*src), cam(lerp(src[0], dst[0], 0.6), dst[1] + (0.2 if i == 0 else -0.2)), cam(dst[0] - 0.25, dst[1])]
        arrow(ctx, pts, S.lin("arrive", 3.0, 1.0 + i * 0.8), BLUE, 52, a, dark=BLUE_D)
        ha = S.p("hills", 0.6, 0.3 + i * 1.8)
        for j in range(7):
            x, y = cam(dst[0] + ((j % 4) - 1.5) * 0.18, dst[1] + (j // 4) * 0.22 - 0.1)
            flagpost(ctx, x, y, BLUE, ha * S.p("hills", 0.4, 0.4 + i * 1.8 + j * 0.1), 1.0, t, j)
        x, y = cam(*dst)
        label(ctx, nm, x, y + 50, 30, (0.8, 0.88, 1.0), ha)
        tag(ctx, who, x, y - 110, BLUE, ha, 30)
    x, y = cam(-6.2, -0.1)
    tag(ctx, "← 猿挂城 · 毛利辉元本阵", max(x, 280), y, BLUE, S.p("arrive", 0.6, 0.5) * (1 - S.p("count", 0.5)), 28)
    # count card
    ca = S.span("count", 0.5, until="same")
    if ca > 0:
        panel(ctx, 80, 980, 920, 300, ca, BLUE)
        rows = [("约5万", "秀吉书信（《浅野家文书》）", 0.4), ("8万余", "《惟任退治记》（秀吉方编）", 2.6), ("约1万？", "现代研究的一种推测", 5.0)]
        for i, (n, s, d) in enumerate(rows):
            ra = ca * S.p("count", 0.5, d)
            text(ctx, n, 170, 1040 + i * 85, 50, (0.8, 0.88, 1.0), ra, "lm", bold=True, serif=True)
            text(ctx, s, 420, 1040 + i * 85, 30, IVORY, ra, "lm")
    if S.on("same"):
        tag(ctx, "城在眼前 · 中间隔着一片湖", W / 2, 1150, GOLD, S.span("same", 0.5, until="forward"), 34)
    # forward: arrows press toward water and halt
    fa = S.p("forward", 0.6)
    if fa > 0:
        for i, (sx_, sy_, ex, ey) in enumerate([(-3.5, 1.3, -2.25, 0.9), (-4.0, -2.5, -2.0, -1.2)]):
            pts = [cam(sx_, sy_), cam(ex, ey)]
            arrow(ctx, pts, S.lin("forward", 1.8, 0.4 + 0.5 * i), BLUE, 40, fa, dark=BLUE_D)
            if S.lin("forward", 1.8, 0.4 + 0.5 * i) >= 1:
                x, y = cam(ex, ey)
                pulse(ctx, x + 40, y, t, (0.8, 0.9, 1.0), 34, fa)
        tag(ctx, "5月21日 前移 · 再往前，就是水", W / 2, 1150, BLUE, fa, 32)


# =============================================================================== s09 mechanism
def node(ctx, x, y, w, h, title, sub, color, alpha):
    if alpha <= 0:
        return
    panel(ctx, x - w / 2, y - h / 2, w, h, alpha, color)
    text(ctx, title, x, y - (16 if sub else 0), 40, IVORY, alpha, "mm", bold=True, serif=True)
    if sub:
        text(ctx, sub, x, y + 30, 26, color if color != GOLD else GOLD, alpha, "mm")


def sc_mech(ctx, S):
    t = S.t
    sea_on = S.span("sea", 0.6, until="dig")
    ink_bg(ctx, t)
    a = S.fin()
    if S.on("normal"):
        text(ctx, "水攻改变了援军要解的题", W / 2, 470, 46, GOLD, a * S.p("normal", 0.6), "mm", bold=True, serif=True)
    # normal relief = battle
    ba = S.p("battle", 0.6) * (1 - S.p("now", 0.6))
    if ba > 0:
        node(ctx, W / 2, 600, 560, 110, "平常：解围 = 一场会战", None, GOLD, ba)
        k = S.p("battle", 1.5, 1.0)
        unit(ctx, lerp(260, 470, k), 760, BLUE, ba, 70, 46)
        unit(ctx, lerp(820, 610, k), 760, RED, ba, 70, 46)
        if k > 0.95:
            for j in range(3):
                ph = (t * 2 + j * 0.3) % 1
                ctx.arc(540, 760, 30 + ph * 60, 0, 2 * math.pi); ctx.set_source_rgba(*FIRE, (1 - ph) * ba * 0.7); ctx.set_line_width(4); ctx.stroke()
        text(ctx, "打赢了，围就解了", W / 2, 860, 34, IVORY, ba * S.p("battle", 0.5, 2.5), "mm")
    na = S.p("now", 0.6) * (1 - sea_on)
    if na > 0:
        node(ctx, W / 2, 660, 600, 110, "现在：先过水", "两条路", BLUE, na)
        node(ctx, 290, 900, 380, 130, "造船渡湖", "→ 船从哪来？", BLUE, na * S.p("now", 0.5, 1.2))
        node(ctx, 790, 900, 380, 130, "掘开大堤", "→ 堤上是三万人", BLUE, na * S.p("now", 0.5, 2.0))
        for x in (290, 790):
            ctx.move_to(W / 2, 715); ctx.line_to(x, 835); ctx.set_source_rgba(*IVORY, 0.4 * na); ctx.set_line_width(3); ctx.stroke()
        xa = S.p("boat", 0.5, 2.5)
        xmark(ctx, 290, 900, 50, na * xa)
        if S.on("boat"):
            tag(ctx, "连运粮的船都凑不齐", 290, 1010, RED, na * S.p("boat", 0.5, 1.0), 28)
        da = S.p("dig", 0.5, 2.0)
        xmark(ctx, 790, 900, 50, na * da)
        if S.on("dig"):
            tag(ctx, "踩烂泥 · 撞上以逸待劳之敌", 790, 1010, RED, na * S.p("dig", 0.5, 0.8), 28)
        wa = S.p("wait", 0.6)
        node(ctx, W / 2, 1130, 520, 110, "不渡不掘：只能等", "→ 城里的粮食等不起", RED, na * wa)
        sa = S.p("sum", 0.6)
        if sa > 0:
            dim(ctx, 0.5 * sa)
            card_lines(ctx, ["一兵不动", ("会战  →  工程难题", GOLD)], 760, sa, 70, gap=1.6)
    if sea_on > 0:
        # Seto Inland Sea inset: navy defection
        cam = BCam(133.4, 34.35, 900, 850)
        ctx.save()
        BM.draw_map(ctx, cam, mori=0.7, oda=0.5)
        ctx.restore()
        dim(ctx, 0.15)
        for i, (n, lo, la) in enumerate([("来岛水军", 132.98, 34.12), ("盐饱水军", 133.75, 34.36), ("（高畠等）", 133.95, 34.48)]):
            x, y = cam(lo, la)
            k = S.p("sea", 0.6, 1.2 + i * 1.0)
            col = tuple(lerp(BLUE[j], RED[j], k) for j in range(3))
            for j in range(3):
                bx = x + (j - 1) * 34; by = y + (j % 2) * 18
                ctx.move_to(bx - 16, by); ctx.line_to(bx + 16, by); ctx.line_to(bx + 10, by + 10); ctx.line_to(bx - 10, by + 10); ctx.close_path()
                ctx.set_source_rgba(*col, sea_on); ctx.fill()
            label(ctx, n, x, y - 40, 30, IVORY, sea_on)
        BM.place(ctx, cam, "备中高松", sea_on, 30, dot=GOLD, castle=True)
        tag(ctx, "倒向秀吉 · 毛利失去制海权", W / 2, 1150, RED, sea_on * S.p("sea", 0.5, 3.0), 32)
        tag(ctx, "补给只能走陆路 · 本阵缺粮", W / 2, 1240, IVORY, sea_on * S.p("sea", 0.5, 5.5), 30)


# =============================================================================== s10 standoff
def sc_standoff(ctx, S):
    t = S.t
    inside = S.p("inside", 2.0)
    sw = math.sin(t * 0.32) * 26
    cam1 = Cam(-0.6, -1.35, 0.085, -62 + sw, 2.5, F=1150)
    cam2 = Cam(-0.35, 0.05, 0.045, -80 + math.sin(t * 0.2) * 8, 2.5, F=1150)
    if inside < 0.5:
        cam = cam1
    else:
        cam = cam2
    flash = 0.0
    strikes = [1.5, 7.0, 12.8, 19.5, 27.0, 36.0, 44.0]
    for ts in strikes:
        d = t - ts
        if 0 <= d < 0.45:
            flash = max(flash, (1 - d / 0.45) * (0.9 if d < 0.07 or 0.14 < d < 0.2 else 0.35))
    night = 0.35 * inside
    sky_top = WD.SKY_TOP * (1 - night); sky_hor = WD.SKY_HOR * (1 - night * 1.2); fog = WD.FOG * (1 - night * 1.2)
    blit(ctx, WD.oblique_surface(cam, L_FINAL, t, rain=1.0, flash=flash, sky_top=sky_top, sky_hor=sky_hor, fog=fog))
    WD.ridges(ctx, cam, t, seed=6)
    # hills with blue banners (west) and red on dike
    rng = np.random.default_rng(2)
    items = []
    for i in range(40):
        hx, hy = (P["岩崎山"] if i % 2 == 0 else P["日差山"])
        items.append((hx + rng.normal(0, 0.25), hy + rng.normal(0, 0.2), BLUE))
    for i in range(30):
        k = rng.random()
        seg = int(k * (len(DIKE) - 1)); kk = k * (len(DIKE) - 1) - seg
        x = lerp(DIKE[seg][0], DIKE[seg + 1][0], kk); y = lerp(DIKE[seg][1], DIKE[seg + 1][1], kk)
        items.append((x, y, RED))
    pr = []
    for (x, y, c) in items:
        p = cam.project(x, y, 0)
        if p:
            pr.append((p[2], p, c))
    pr.sort(key=lambda e: e[0])
    for i, (_, p, c) in enumerate(pr):
        WD.banner(ctx, p, c, 0.95, t, i, 1.6)
    castle_sprites(ctx, cam, L_FINAL)
    if inside > 0.5:
        # campfires on the western hills (night)
        for i in range(24):
            hx, hy = (P["岩崎山"] if i % 2 == 0 else P["日差山"])
            p = cam.project(hx + rng.normal(0, 0.3), hy + rng.normal(0, 0.25), 0)
            if p:
                fl = 0.6 + 0.4 * math.sin(t * 7 + i * 1.3)
                g = cairo.RadialGradient(p[0], p[1], 0, p[0], p[1], 14)
                g.add_color_stop_rgba(0, 1, 0.75, 0.4, 0.9 * fl); g.add_color_stop_rgba(1, 1, 0.5, 0.2, 0)
                ctx.set_source(g); ctx.arc(p[0], p[1], 14, 0, 2 * math.pi); ctx.fill()
    for ts in strikes:
        WD.lightning(ctx, 200 + 680 * ((ts * 3.7) % 1), t - ts, seed=int(ts * 10), y1=WD.horizon_y(cam) + 20)
    WD.rain_overlay(ctx, t, 1.4, 0.5)
    a = S.fin()
    if not S.on("inside"):
        sa = S.span("face", 0.5, until="inside")
        tag(ctx, "山上：毛利蓝旗", 270, 1150, BLUE, sa * S.p("face", 0.5, 0.8), 32)
        tag(ctx, "堤上：羽柴红旗", 810, 1150, RED, sa * S.p("face", 0.5, 2.0), 32)
        if S.on("storm"):
            tag(ctx, "谁先动，谁吃亏", W / 2, 1240, GOLD, S.span("storm", 0.5, until="inside"), 34)
    # food meter
    fa = S.p("food", 0.6) * a
    if fa > 0:
        panel(ctx, 140, 1100, 800, 120, fa, RED)
        text(ctx, "城中存粮", 200, 1160, 34, IVORY, fa, "lm", bold=True)
        k = 1 - 0.85 * S.p("food", 10.0, 0.5)
        ctx.rectangle(380, 1145, 500, 30); ctx.set_source_rgba(1, 1, 1, 0.12 * fa); ctx.fill()
        ctx.rectangle(380, 1145, 500 * k, 30); ctx.set_source_rgba(*RICE, fa); ctx.fill()
    if S.on("hope2"):
        ha = S.p("hope2", 1.0)
        dim(ctx, 0.45 * ha)
        card_lines(ctx, ["先垮掉的，", ("是心里那个念头：援军会来", GOLD)], 760, ha * S.p("hope2", 0.6, 5.5), 54, gap=1.6)


# =============================================================================== s11 nobunaga
def sc_nobunaga(ctx, S):
    t = S.t
    cam = BCam(134.9, 34.95, 330, 880)
    BM.draw_map(ctx, cam, mori=0.8, oda=0.8, dim=0.15 * S.p("menu", 0.6))
    a = S.fin()
    BM.place(ctx, cam, "安土", a, 32, dot=RED)
    BM.place(ctx, cam, "京都", a, 32, dot=RED, anchor="rm", dx=22)
    BM.place(ctx, cam, "姬路", a * 0.7, 28, dot=RED)
    x, y = BM.place(ctx, cam, "备中高松", a, 32, dot=GOLD, castle=True)
    # messenger to Azuchi
    ka = S.p("ask", 0.5)
    pts = [cam(133.84, 34.69), cam(134.7, 34.9), cam(135.6, 35.2), cam(136.12, 35.16)]
    dashed(ctx, pts, S.lin("ask", 2.5, 0.5), GOLD, 6, ka * (1 - S.p("yes", 0.6) * 0.6))
    if S.on("ask"):
        tag(ctx, "秀吉请主君亲征", W / 2, 1150, GOLD, S.span("ask", 0.5, until="yes"), 32)
    ya = S.p("yes", 0.6)
    if ya > 0:
        pts2 = [cam(136.12, 35.16), cam(135.77, 35.01), cam(134.9, 34.85), cam(134.0, 34.72)]
        arrow(ctx, pts2, S.lin("yes", 3.5, 0.5) * 0.98, RED, 52, ya * 0.85, dark=RED_D)
        tag(ctx, "信长亲征（计划）", W / 2, 1150, RED, ya * (1 - S.p("menu", 0.5)), 32)
        x2, y2 = cam(135.77, 35.01)
        tag(ctx, "本能寺 · 五月底", x2, y2 + 70, IVORY, ya * S.p("yes", 0.5, 3.0) * (1 - S.p("menu", 0.5)), 26)
    if S.on("set"):
        card_lines(ctx, ["仗还没打", ("先让对手觉得：大势已定", GOLD)], 560, S.span("set", 0.5, until="menu"), 52)
    ma = S.p("menu", 0.6)
    if ma > 0:
        dim(ctx, 0.5 * ma)
        text(ctx, "毛利的选项", W / 2, 520, 48, GOLD, ma, "mm", bold=True, serif=True)
        opts = [("打", "踩烂泥撞堤"), ("等", "城中粮尽"), ("退", "白丢一座城")]
        for i, (o, c) in enumerate(opts):
            aa = ma * S.p("menu", 0.4, 0.8 + i * 1.4)
            y0 = 640 + i * 150
            panel(ctx, 160, y0, 760, 120, aa, BLUE)
            text(ctx, o, 240, y0 + 60, 60, IVORY, aa, "mm", bold=True, serif=True)
            text(ctx, c, 330, y0 + 60, 40, IVORY, aa, "lm")
            text(ctx, "代价 ↑", 880, y0 + 60, 34, RED, aa, "rm", bold=True)
        ta = ma * S.p("menu", 0.5, 6.0)
        panel(ctx, 160, 1100, 760, 120, ta, GOLD)
        text(ctx, "谈", 240, 1160, 60, GOLD, ta, "mm", bold=True, serif=True)
        text(ctx, "剩下最便宜的一条路", 330, 1160, 40, GOLD, ta, "lm", bold=True)


# =============================================================================== s12 talk (情景演绎)
_table = {}


def table_bg():
    if "t" not in _table:
        rng = np.random.default_rng(8)
        n = noise2d(H, W, 8, rng, 3)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        grain = np.sin((xx * 0.02 + n * 6.0 + yy * 0.002) * 3.0) * 0.5 + 0.5
        base = np.stack([0.20 + 0.06 * grain, 0.12 + 0.04 * grain, 0.07 + 0.02 * grain], -1)
        _table["t"] = surface_from_rgb(base)
    return _table["t"]


def candle(ctx, x, y, t, alpha=1.0):
    fl = 0.85 + 0.15 * math.sin(t * 9) * math.sin(t * 5.3 + 1)
    g = cairo.RadialGradient(x, y - 60, 10, x, y - 60, 900)
    g.add_color_stop_rgba(0, 1.0, 0.75, 0.40, 0.45 * fl * alpha); g.add_color_stop_rgba(0.4, 0.8, 0.45, 0.2, 0.12 * alpha)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.paint()
    ctx.rectangle(x - 16, y - 40, 32, 110); ctx.set_source_rgba(0.90, 0.86, 0.75, alpha); ctx.fill()
    ctx.move_to(x, y - 95 - 8 * fl); ctx.curve_to(x + 14, y - 70, x + 10, y - 48, x, y - 45)
    ctx.curve_to(x - 10, y - 48, x - 14, y - 70, x, y - 95 - 8 * fl)
    ctx.set_source_rgba(1, 0.85, 0.45, alpha); ctx.fill()


def prov_card(ctx, x, y, name, alpha, color=BLUE, struck=0.0, w=170, h=96):
    if alpha <= 0:
        return
    rrect(ctx, x - w / 2, y - h / 2, w, h, 8); ctx.set_source_rgba(0.93, 0.89, 0.78, 0.95 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.set_line_width(4); ctx.stroke()
    text(ctx, name, x, y, 46, (0.12, 0.10, 0.08), alpha * (1 - 0.6 * struck), "mm", bold=True, serif=True)
    if struck > 0:
        ctx.move_to(x - w / 2 + 10, y); ctx.line_to(x - w / 2 + 10 + (w - 20) * struck, y)
        ctx.set_source_rgba(*RED, alpha); ctx.set_line_width(7); ctx.stroke()


def sc_talk(ctx, S):
    t = S.t
    honno = S.span("honno", 0.6, until="seal")
    blit(ctx, table_bg())
    candle(ctx, 880, 560, t, 1.0)
    vg = cairo.RadialGradient(W / 2, 850, 200, W / 2, 900, 1200)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.set_source(vg); ctx.paint()
    a = S.fin()
    if S.on("go"):
        text(ctx, "安国寺惠琼（毛利方使僧）", W / 2, 520, 40, (0.8, 0.88, 1.0), a * S.span("go", 0.5, until="five"), "mm", bold=True, halo=6)
        scroll_icon(ctx, W / 2, 700, 1.6, a * S.span("go", 0.5, until="five"), seal=BLUE)
    names = ["备中", "备后", "美作", "伯耆", "出云"]
    pos = [(200, 640), (400, 640), (600, 640), (300, 770), (500, 770)]
    pa = S.p("five", 0.6) * (1 - honno)
    slide = S.p("five", 1.2, 0.5)
    for i, (n, (x, y)) in enumerate(zip(names, pos)):
        struck = S.p("three", 0.8, 2.0 + i * 0.3) if n in ("备后", "出云") else 0.0
        prov_card(ctx, x + 60 + (1 - slide) * -300, y, n, pa * S.p("five", 0.4, 0.8 + i * 0.35), BLUE, struck)
    if S.on("five"):
        text(ctx, "毛利开价：割五国，保全城兵", W / 2, 470, 42, (0.8, 0.88, 1.0), pa * S.p("five", 0.5, 2.5) * (1 - S.p("three", 0.5)), "mm", bold=True, halo=6)
    if S.on("demand"):
        da = pa * S.p("demand", 0.5) * (1 - S.p("three", 0.5) * 0.0)
        panel(ctx, 180, 900, 720, 120, da, RED)
        text(ctx, "秀吉：五国 + 清水宗治切腹", W / 2, 960, 42, (1, 0.8, 0.7), da, "mm", bold=True)
    if S.on("stuck"):
        tag(ctx, "谈判僵住", W / 2, 1110, IVORY, S.span("stuck", 0.5, until="mune"), 34)
    if S.on("mune"):
        ma = S.span("mune", 0.5, until="honno")
        panel(ctx, 100, 1060, 880, 150, ma, BLUE)
        text(ctx, "宗治（据记载，大意）：", 150, 1105, 28, GOLD, ma, "lm")
        text(ctx, "主家与城兵得活，此头不足惜", W / 2, 1160, 42, IVORY, ma, "mm", bold=True, serif=True)
    if honno > 0:
        dim(ctx, 0.75 * honno)
        cam = BCam(135.6, 35.0, 900, 760)
        ctx.push_group()
        BM.draw_map(ctx, cam, oda=0.4)
        x, y = cam(135.77, 35.01)
        g = cairo.RadialGradient(x, y, 0, x, y, 260)
        g.add_color_stop_rgba(0, 1.0, 0.55, 0.2, 0.9); g.add_color_stop_rgba(0.35, 0.9, 0.3, 0.1, 0.45); g.add_color_stop_rgba(1, 0.4, 0.1, 0, 0)
        ctx.set_source(g); ctx.arc(x, y, 260, 0, 2 * math.pi); ctx.fill()
        BM.place(ctx, cam, "京都", 1.0, 40, dot=FIRE, bold=True)
        ctx.pop_group_to_source(); ctx.paint_with_alpha(honno)
        big_number(ctx, "6月2日", None, W / 2, 1090, honno, FIRE, 110)
        text(ctx, "本能寺之变 · 信长身死", W / 2, 1200, 44, IVORY, honno, "mm", bold=True, serif=True, halo=8)
        if S.on("know"):
            ka = honno * S.p("know", 0.5)
            panel(ctx, 100, 360, 880, 170, ka, GOLD)
            text(ctx, "秀吉：6月3日夜得知（通说）", W / 2, 415, 36, (1, 0.8, 0.7), ka, "mm", bold=True)
            text(ctx, "毛利：秀吉撤走后才听说", W / 2, 480, 36, (0.8, 0.88, 1.0), ka * S.p("know", 0.5, 3.0), "mm", bold=True)
    if S.on("seal"):
        sa = S.p("seal", 0.5) * (1 - S.p("three", 0.5))
        scroll_icon(ctx, 820, 760, 1.3, sa, seal=None)
        ctx.set_source_rgba(0.1, 0.1, 0.1, sa); ctx.set_line_width(10)
        ctx.move_to(740, 710); ctx.line_to(900, 810); ctx.move_to(900, 710); ctx.line_to(740, 810); ctx.stroke()
        tag(ctx, "封锁消息 · 加速谈判", W / 2, 1110, GOLD, sa, 34)
    if S.on("three"):
        tag(ctx, "五国 → 三国：备中、美作、伯耆", W / 2, 470, GOLD, S.p("three", 0.5), 34)
        panel(ctx, 180, 900, 720, 120, S.p("three", 0.5, 3.0), RED)
        text(ctx, "宗治必须死 —— 这一条不改", W / 2, 960, 40, (1, 0.8, 0.7), S.p("three", 0.5, 3.0), "mm", bold=True)
    if S.on("accept"):
        aa = S.p("accept", 0.3)
        sc_ = 1 + 0.4 * (1 - aa)
        ctx.save(); ctx.translate(W / 2, 1150); ctx.scale(sc_, sc_)
        rrect(ctx, -110, -60, 220, 120, 10); ctx.set_source_rgba(*RED, 0.9 * aa); ctx.fill()
        text(ctx, "和议", 0, 0, 64, (1, 0.95, 0.9), aa, "mm", bold=True, serif=True)
        ctx.restore()


# =============================================================================== s13 boat
def sc_boat(ctx, S):
    t = S.t
    k = clamp(t / max(S.dur, 1))
    cam = Cam(lerp(-0.42, -0.36, k), lerp(-0.62, -0.55, k), 0.05, 32, 2.5, F=1150)
    sky_top = np.array([0.14, 0.15, 0.20], np.float32); sky_hor = np.array([0.62, 0.55, 0.48], np.float32)
    fog = np.array([0.50, 0.47, 0.43], np.float32)
    blit(ctx, WD.oblique_surface(cam, L_FINAL, t * 0.4, rain=0.0, sky_top=sky_top, sky_hor=sky_hor, fog=fog, fogd=3.0))
    WD.ridges(ctx, cam, t, seed=9, color=(0.20, 0.19, 0.20))
    castle_sprites(ctx, cam, L_FINAL)
    # boat leaves the honmaru towards camera-right
    bk = clamp((t - S.c0("dawn") - 1.5) / 25)
    bx, by = lerp(0.0, -0.12, bk), lerp(-0.2, -0.36, bk)
    p = cam.project(bx, by, 0)
    WD.boat(ctx, p, S.p("dawn", 1.0), people=3)
    if p:
        for j in range(3):
            ph = (t * 0.5 + j / 3) % 1
            ctx.save(); ctx.translate(p[0], p[1] + 4); ctx.scale(1, 0.22)
            ctx.arc(0, 0, 20 + ph * 90, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgba(0.9, 0.85, 0.75, (1 - ph) * 0.3); ctx.set_line_width(2); ctx.stroke()
    a = S.fin()
    if S.on("trade"):
        card_lines(ctx, ["以自己一死", ("换城中将士活命", GOLD)], 560, S.span("trade", 0.6, until="poem"), 58)
    if S.on("poem"):
        qa = S.span("poem", 0.6, until="open")
        quote_card(ctx, "浮世をば　今こそ渡れ\n武士の　名を高松の　苔に残して",
                   "如今我渡过这浮世，把武士的名字，留在高松的青苔上",
                   "清水宗治辞世（传）· 据日文维基百科「清水宗治」条转引", qa, y=760, latin=None, orig_size=42, zh_size=40)
    if S.on("open"):
        card_lines(ctx, ["不是被水攻破", "不是被刀枪攻破", ("是在谈判桌上交出来的", GOLD)], 520, S.span("open", 0.6, until="after"), 52)
    if S.on("after"):
        aa = S.p("after", 0.6)
        panel(ctx, 90, 470, 900, 300, aa, BLUE)
        text(ctx, "毛利得知信长死讯时，秀吉已撤围东返", W / 2, 530, 32, IVORY, aa, "mm", bold=True)
        text(ctx, "吉川元春：追击", W / 2, 610, 40, (0.8, 0.88, 1.0), aa * S.p("after", 0.5, 3.5), "mm", bold=True, serif=True)
        text(ctx, "小早川隆景：誓书已换，守约", W / 2, 680, 40, GOLD, aa * S.p("after", 0.5, 6.0), "mm", bold=True, serif=True)


# =============================================================================== s14 sources
def sc_sources(ctx, S):
    t = S.t
    ink_bg(ctx, t)
    a = S.fin()
    text(ctx, "史料争议", W / 2, 470, 54, GOLD, a * S.p("c1", 0.6), "mm", bold=True, serif=True)
    rows = [("idea", "谁出的主意", "黑田孝高献策：一说", "另说：黑田家臣吉田长利"),
            ("cost", "花了多少钱", "钱63万余贯、米6万余石", "出自江户逸话集《武将感状记》，不可当真"),
            ("army", "援军多少人", "约5万：秀吉书信", "报敌数，有往大里说的动机"),
            ("letter", "怎么得知本能寺", "截获光秀密使：常见说法", "具体经过，各书不一")]
    for i, (cue, q, ans, note) in enumerate(rows):
        ra = a * S.p(cue, 0.6)
        cur = S.on(cue) and (i == 3 or not S.on(rows[i + 1][0]))
        y0 = 560 + i * 165
        panel(ctx, 70, y0, 940, 145, ra, GOLD if cur else (0.45, 0.42, 0.38))
        text(ctx, f"{i + 1}", 120, y0 + 72, 50, GOLD, ra, "mm", bold=True, serif=True)
        text(ctx, q, 170, y0 + 42, 32, GOLD, ra, "lm", bold=True)
        text(ctx, ans, 170, y0 + 88, 34, IVORY, ra, "lm", bold=True, serif=True)
        text(ctx, note, 170, y0 + 125, 24, DIM, ra, "lm")
    ca = S.p("core", 0.6)
    if ca > 0:
        dim(ctx, 0.9 * ca)
        steps = ["包围", "筑堤", "引水", "援军受阻", "谈判", "宗治自尽"]
        text(ctx, "能确定的骨架", W / 2, 640, 46, GOLD, ca, "mm", bold=True, serif=True)
        for i, s in enumerate(steps):
            aa = ca * S.p("core", 0.4, 0.6 + i * 0.45)
            x = 200 + (i % 3) * 340; y = 790 + (i // 3) * 150
            tag(ctx, s, x, y, GOLD, aa, 40)
        text(ctx, "细节数字：打个折扣看", W / 2, 1110, 38, IVORY, ca * S.p("core", 0.5, 4.5), "mm", bold=True)


# =============================================================================== s15 ending
def sc_ending(ctx, S):
    t = S.t
    k = clamp(t / max(S.dur, 1))
    cam = TD(-0.4, lerp(0.15, 0.0, k), lerp(165, 150, k))
    lv = lerp(L_FINAL, 0.0, ease(clamp(t / 18)))
    td_bg(ctx, cam, lv, t, tint=0.15, dimv=0.35)
    a = S.fin()
    dike_line(ctx, cam, 1.0, a * 0.6, 6, glow=False)
    qa = S.span("sunzi", 0.6, until="cut")
    if S.on("gloss"):
        qa = S.span("sunzi", 0.6, until="cut")
    if qa > 0:
        quote_card(ctx, "故以火佐攻者明，以水佐攻者強。\n水可以絕，不可以奪。",
                   "用火助攻效果显著，用水助攻威力强大；水能把敌人隔断，却不能替你夺取",
                   "《孙子·火攻》", qa, y=820, latin=False, orig_size=46, zh_size=38)
    if S.on("cut"):
        ca = S.span("cut", 0.5, until="but")
        for i, s in enumerate(["切断援军", "切断粮道", "切断体面的选项"]):
            tag(ctx, "水 · " + s, W / 2, 640 + i * 120, (0.75, 0.85, 0.95), ca * S.p("cut", 0.4, 1.0 + i * 1.3), 38)
    if S.on("but"):
        card_lines(ctx, ["城不是水拿下的", ("最后一步，靠谈判", GOLD)], 720, S.span("but", 0.6, until="schelling"), 62)
    if S.on("schelling"):
        sa = S.span("schelling", 0.6, until="work") if not S.on("lake") else S.span("schelling", 0.6, until="work")
        panel(ctx, 90, 560, 900, 420, sa, GOLD)
        text(ctx, "谢林《冲突的战略》（1960）", W / 2, 630, 34, GOLD, sa, "mm", bold=True)
        card_lines(ctx, ["谈判桌上的筹码，", "往往在桌子之外先摆好"], 740, sa, 46)
        if S.on("lake"):
            text(ctx, "秀吉的湖 = 提前摆好的筹码", W / 2, 920, 40, (1, 0.85, 0.7), sa * S.p("lake", 0.5), "mm", bold=True, serif=True)
    if S.on("work"):
        wa = S.span("work", 0.6, until="next")
        dim(ctx, 0.4 * wa)
        card_lines(ctx, ["硬攻不下时，", "先改变战场的形状，", ("让对手的每个选项都变贵", GOLD)], 640, wa, 58, gap=1.7)
    if S.on("next"):
        na = S.p("next", 0.8)
        dim(ctx, 0.55 * na)
        scroll_icon(ctx, W / 2, 760, 2.2, na * S.p("next", 0.6, 1.5), seal=(0.15, 0.15, 0.15))
        text(ctx, "谈判桌下的那封密信", W / 2, 960, 56, IVORY, na * S.p("next", 0.6, 2.0), "mm", bold=True, serif=True, halo=8)
        text(ctx, "下一集", W / 2, 560, 40, GOLD, na * S.p("next", 0.6, 4.0), "mm", bold=True, serif=True)


RENDERERS = {"flood": sc_flood, "hookmap": sc_hookmap, "bigmap": sc_bigmap, "offer": sc_offer, "assault": sc_assault,
             "build": sc_build, "lake": sc_lake, "section": sc_section, "relief": sc_relief, "mech": sc_mech,
             "standoff": sc_standoff, "nobunaga": sc_nobunaga, "talk": sc_talk, "boat": sc_boat, "sources": sc_sources,
             "ending": sc_ending}
BADGE = {"flood": "ill", "hookmap": "map", "bigmap": "map", "offer": "card", "assault": "map", "build": "map",
         "lake": "ill", "section": "card", "relief": "map", "mech": "card", "standoff": "ill", "nobunaga": "map",
         "talk": "act", "boat": "ill", "sources": "card", "ending": "map"}
