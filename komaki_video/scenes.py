# -*- coding: utf-8 -*-
"""Scene renderers for 小牧长久手. Each: fn(ctx, S) draws the full frame under the overlays."""
import math
import numpy as np
import cairo
from gfx import *
from frame import S, quote_card, panel, big_number, legend, PLATE_CY
import geo
from geo import OWARI, NATION, REGION, draw_place
import illus
from illus import ashigaru, rider, nobori, earthwork, pine, fog, drift, muzzle, smoke_puffs, golden_fan, castle, hills, particles

_M = {}


def base(name):
    if name not in _M:
        _M[name] = geo.build_base(name)
        _M["P_" + name] = geo.proj(name)
    return _M[name]


def P(name):
    base(name)
    return _M["P_" + name]


def O(n):
    return P("owari")(*OWARI[n])


def Oll(lo, la):
    return P("owari")(lo, la)


def N(n):
    return P("nation")(*NATION[n])


def Nll(lo, la):
    return P("nation")(lo, la)


def R(n):
    return P("region")(*REGION[n])


def Rll(lo, la):
    return P("region")(lo, la)


# ---------------------------------------------------------------- camera / helpers
class Cam:
    def __init__(self, S, keys, tr=2.2):
        """keys: [(cue_or_None, (cx, cy), zoom)]"""
        cx, cy = keys[0][1]; z = keys[0][2]
        for k_ in keys[1:]:
            cue, (x, y), zz = k_[:3]
            d = k_[3] if len(k_) > 3 else tr
            k = S.p(cue, d)
            cx, cy, z = lerp(cx, x, k), lerp(cy, y, k), lerp(z, zz, k)
        self.cx, self.cy, self.z = cx, cy, z

    def apply(self, ctx):
        ctx.translate(W / 2, PLATE_CY); ctx.scale(self.z, self.z); ctx.translate(-self.cx, -self.cy)

    def sc(self, p):
        return (W / 2 + (p[0] - self.cx) * self.z, PLATE_CY + (p[1] - self.cy) * self.z)


def map_base(ctx, name, cam, dim=0.0):
    fill_bg(ctx, (0.03, 0.045, 0.06))
    ctx.save(); cam.apply(ctx)
    ctx.set_source_surface(base(name), 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
    if dim > 0:
        ctx.set_source_rgba(0, 0, 0, dim); ctx.paint()


def sp(cam, pts):
    return [cam.sc(p) for p in pts]


def burst(ctx, x, y, t, r=40, alpha=1.0, color=FIRE, seed=0):
    if alpha <= 0:
        return
    for k in range(3):
        ph = t * 7 + k * 2.1 + seed
        f = 0.5 + 0.5 * math.sin(ph)
        ox, oy = math.cos(seed * 3 + k * 2) * r * 0.6, math.sin(seed * 5 + k) * r * 0.5
        rr = r * (0.5 + 0.6 * f)
        g = cairo.RadialGradient(x + ox, y + oy, 0, x + ox, y + oy, rr)
        g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.85 * alpha * f); g.add_color_stop_rgba(0.4, *color, 0.5 * alpha * f)
        g.add_color_stop_rgba(1, *color, 0)
        ctx.set_source(g); ctx.arc(x + ox, y + oy, rr, 0, 6.3); ctx.fill()


def pulse_ring(ctx, x, y, t, color=GOLD, r=40, alpha=1.0):
    if alpha <= 0:
        return
    ctx.new_path()
    for k in range(2):
        ph = ((t * 0.8 + k * 0.5) % 1.0)
        ctx.arc(x, y, r * (0.6 + ph * 1.4), 0, 6.3)
        ctx.set_source_rgba(*color, alpha * (1 - ph) * 0.9); ctx.set_line_width(4); ctx.stroke()


def ruler(ctx, a, b, txt, alpha=1.0, color=IVORY, off=-30):
    if alpha <= 0:
        return
    ctx.save(); ctx.set_dash([6, 8]); ctx.set_line_width(3)
    ctx.move_to(*a); ctx.line_to(*b); ctx.set_source_rgba(*color, 0.85 * alpha); ctx.stroke(); ctx.restore()
    for p in (a, b):
        ctx.arc(p[0], p[1], 6, 0, 6.3); ctx.set_source_rgba(*color, alpha); ctx.fill()
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    text(ctx, txt, mx + 20, my + off, 32, color, alpha, "lm", bold=True, halo=8)


def cross(ctx, x, y, r, alpha=1.0, color=RED, width=10):
    if alpha <= 0:
        return
    ctx.set_line_width(width + 6); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgba(0, 0, 0, 0.6 * alpha)
    ctx.move_to(x - r, y - r); ctx.line_to(x + r, y + r); ctx.move_to(x - r, y + r); ctx.line_to(x + r, y - r); ctx.stroke()
    ctx.set_line_width(width); ctx.set_source_rgba(*color, alpha)
    ctx.move_to(x - r, y - r); ctx.line_to(x + r, y + r); ctx.move_to(x - r, y + r); ctx.line_to(x + r, y - r); ctx.stroke()


def tag(ctx, s, x, y, color, alpha=1.0, size=30):
    if alpha <= 0:
        return
    font(ctx, size, bold=True)
    w = text_w(ctx, s) + 30
    rrect(ctx, x - w / 2, y - size * 0.78, w, size * 1.56, size * 0.4)
    ctx.set_source_rgba(*[c * 0.45 for c in color], 0.92 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.set_line_width(2.5); ctx.stroke()
    text(ctx, s, x, y, size, IVORY, alpha, "mm", bold=True)


def card_text(ctx, lines, y, alpha=1.0, size=46, color=IVORY, gap=1.45, bold=True):
    for i, L in enumerate(lines):
        text(ctx, L, W / 2, y + i * size * gap, size, color, alpha, "mm", bold=bold, serif=True, halo=8, halo_a=0.6)


def dark_card_bg(ctx, a=1.0):
    fill_bg(ctx, (0.05, 0.05, 0.06), a)


def unit(ctx, x, y, color, alpha=1.0, w=46, h=30, label=None, lsize=28, side=1):
    unit_block(ctx, x, y, w, h, color, alpha, 0, "inf")
    if label and alpha > 0:
        if side > 0:
            text(ctx, label, x + w / 2 + 12, y, lsize, IVORY, alpha, "lm", bold=True, halo=7)
        elif side < 0:
            text(ctx, label, x - w / 2 - 12, y, lsize, IVORY, alpha, "rm", bold=True, halo=7)
        else:
            text(ctx, label, x, y - h / 2 - 22, lsize, IVORY, alpha, "mm", bold=True, halo=7)


def at_poly(pts, u):
    """point at fraction u along a smoothed polyline"""
    sm = smooth(pts, 10)
    seg = cut(sm, clamp(u))
    return seg[-1]


def fortline(ctx, pts, prog, color, z=1.0, alpha=1.0):
    """earthwork line on map: thick dark rampart + coloured crenellation ticks"""
    if prog <= 0 or alpha <= 0:
        return
    seg = cut(smooth(pts, 10), prog)
    if len(seg) < 2:
        return
    ctx.save(); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    path(ctx, seg); ctx.set_source_rgba(0, 0, 0, 0.6 * alpha); ctx.set_line_width(20 / z); ctx.stroke()
    path(ctx, seg); ctx.set_source_rgba(*color, 0.25 * alpha); ctx.set_line_width(34 / z); ctx.stroke()
    path(ctx, seg); ctx.set_source_rgba(*[c * 0.7 for c in color], alpha); ctx.set_line_width(10 / z); ctx.stroke()
    ctx.set_dash([4 / z, 10 / z])
    path(ctx, seg); ctx.set_source_rgba(1, 0.95, 0.85, 0.8 * alpha); ctx.set_line_width(16 / z); ctx.stroke()
    ctx.restore()


def owari_labels(ctx, cam, alpha=1.0, only=None, size=34, castle_set=("小牧山", "犬山城", "清洲城", "小幡城", "岩崎城", "冈崎城")):
    side = {"小牧山": -1, "犬山城": 1, "乐田": 1, "羽黑": 1, "清洲城": -1, "小幡城": -1, "岩崎城": 1, "白山林": -1, "长久手": 1,
            "冈崎城": -1, "色金山": 1}
    for nm in OWARI:
        if only is not None and nm not in only:
            continue
        x, y = cam.sc(O(nm))
        dot = IVORY
        draw_place(ctx, nm, x, y, alpha, size, dot, side.get(nm, 1), bold=nm in ("小牧山", "长久手"), castle=nm in castle_set)


def legend_rb(ctx, a=1.0, y=1300):
    legend(ctx, [(RED, "羽柴军"), (BLU, "织田·德川军")], a, y)


def shake(ctx, t, t0, amp=14, dur=0.4):
    if t0 <= t < t0 + dur:
        k = 1 - (t - t0) / dur
        ctx.translate(math.sin(t * 90) * amp * k, math.cos(t * 77) * amp * k * 0.7)


def flash(ctx, t, t0, dur=0.18, a=0.8, col=(1, 0.95, 0.85)):
    if t0 <= t < t0 + dur:
        ctx.set_source_rgba(*col, a * (1 - (t - t0) / dur)); ctx.paint()


# ================================================================ shared illustration pieces
def standoff_plate(ctx, t, volley_t=None, push=0.0):
    """open plain between two earthwork lines (red far, blue near), wind."""
    ctx.save()
    z = 1.0 + 0.05 * push
    ctx.translate(W / 2, 900); ctx.scale(z, z); ctx.translate(-W / 2, -900)
    paint_surface(ctx, illus.sky("plain"), 0, 0)
    hills(ctx, 820, 110, (0.13, 0.14, 0.15), seed=2)
    drift(ctx, fog(31, 0.35, (0.55, 0.56, 0.55), 500), 520, t, 18, 0.8)
    # plain
    ctx.rectangle(0, 860, W, H); g = cairo.LinearGradient(0, 860, 0, H)
    g.add_color_stop_rgb(0, 0.20, 0.19, 0.15); g.add_color_stop_rgb(1, 0.06, 0.055, 0.045)
    ctx.set_source(g); ctx.fill()
    earthwork(ctx, 900, 0.42, RED, t, n_flags=12, seed=4)
    # grass in wind
    rng = np.random.default_rng(12)
    ctx.set_line_width(1.6)
    for i in range(420):
        y0 = rng.uniform(930, 1250); x = rng.uniform(-20, W + 20)
        sc_ = (y0 - 860) / 400
        hgt = rng.uniform(10, 26) * sc_
        sw = (6 + 8 * sc_) * math.sin(t * 2.3 + x * 0.02 + y0 * 0.01)
        ctx.move_to(x, y0); ctx.line_to(x + sw, y0 - hgt)
        ctx.set_source_rgba(0.50, 0.44, 0.28, 0.45); ctx.stroke()
    earthwork(ctx, 1290, 1.25, BLU, t, n_flags=5, seed=9)
    # near gunners kneeling behind rampart (blue)
    for i in range(7):
        x = 80 + i * 150
        ashigaru(ctx, x, 1300, 0.95, 0, BLU, "teppo", 1, 1.0, aim=True, lean=-0.05)
    if volley_t is not None:
        age = t - volley_t
        for i in range(7):
            x = 80 + i * 150 + 66
            a_ = age - i * 0.025
            muzzle(ctx, x, 1300 - 100 * 0.95, a_, 1, 1.4)
            smoke_puffs(ctx, x, 1300 - 98, a_, seed=i, size=1.3)
    ctx.restore()


def forest_plate(ctx, t, march=0.0, ambush=-1.0, rout=0.0, red_n=14):
    """misty pine wood; red column marching right; blue bursting from the left-rear at `ambush` time."""
    paint_surface(ctx, illus.sky("forest"), 0, 0)
    for k, (yb, h, a, col) in enumerate(((980, 520, 0.55, (0.16, 0.19, 0.19)), (1060, 700, 0.75, (0.10, 0.12, 0.12)))):
        rng = np.random.default_rng(40 + k)
        for i in range(16):
            pine(ctx, rng.uniform(-40, W + 40), yb + rng.uniform(-20, 30), h * rng.uniform(0.7, 1.1), seed=i + 10 * k, col=col, alpha=a,
                 sway=6 * math.sin(t * 0.7 + i))
    drift(ctx, fog(41, 0.55, (0.62, 0.66, 0.64), 600), 650, t, 10, 0.85)
    ctx.rectangle(0, 1080, W, H); g = cairo.LinearGradient(0, 1080, 0, H)
    g.add_color_stop_rgb(0, 0.12, 0.13, 0.10); g.add_color_stop_rgb(1, 0.03, 0.03, 0.03)
    ctx.set_source(g); ctx.fill()
    # red column
    for i in range(red_n):
        bx = -200 + i * 95 + march * 140
        phase = t * 6 + i * 0.9
        x, y = bx, 1150 + (i % 2) * 22
        a = 1.0
        dx = 0
        if rout > 0:
            rng = np.random.default_rng(i)
            dx = rout * rng.uniform(80, 360)
            y += rout * rng.uniform(-30, 40)
            a = 1 - 0.5 * rout * rng.uniform(0, 1)
        ashigaru(ctx, x + dx, y, 0.85, phase * (1 + rout), RED, "yari", 1, a, run=rout)
    drift(ctx, fog(43, 0.35, (0.65, 0.68, 0.66), 400), 980, t + 30, 14, 0.6)
    if ambush >= 0:
        age = t - ambush
        if age >= 0:
            # riders surge in from left foreground
            for i in range(4):
                u = clamp((age - i * 0.25) / 2.5)
                x = -260 + u * 620 + i * 120
                rider(ctx, x, 1420 + i * 40, 1.25 - i * 0.06, t * 9 + i, BLU, 1, clamp(u * 4))
            for i in range(6):
                x = 40 + i * 110
                y = 1290 + (i % 2) * 30
                ashigaru(ctx, x, y, 1.05, 0, BLU, "teppo", 1, clamp(age * 3), aim=True)
                fa = age - 0.3 - i * 0.07
                muzzle(ctx, x + 70, y - 104, fa % 2.3 if fa > 0 else -1, 1, 1.3)
                smoke_puffs(ctx, x + 70, y - 100, fa, seed=20 + i, size=1.4)
    vg = cairo.LinearGradient(0, 0, W, 0)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0.35); vg.add_color_stop_rgba(0.5, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.3)
    ctx.set_source(vg); ctx.paint()


# ================================================================ s00 hook
VOLLEY_T = 1.15


def sc_hook(ctx, S):
    t = S.t
    tw = S.c0("twist")
    if t < tw:
        ctx.save()
        shake(ctx, t, VOLLEY_T, 18, 0.45)
        standoff_plate(ctx, t, VOLLEY_T, push=clamp(t / 8))
        ctx.restore()
        flash(ctx, t, VOLLEY_T, 0.15, 0.55)
        a = S.p("volley", 0.5, 0.15)
        a0 = clamp(t / 0.2 + 0.4)
        text(ctx, "十万", 300, 560, 150, RED, a0, "mm", bold=True, serif=True, halo=14, halo_a=0.8)
        text(ctx, "对", W / 2, 575, 64, IVORY, a0, "mm", serif=True, halo=8)
        text(ctx, "三万", 780, 560, 150, BLU, a0, "mm", bold=True, serif=True, halo=14, halo_a=0.8)
        if a > 0:
            b = S.p("volley", 0.6, 2.6)
            text(ctx, "大的一方 · 先输一仗 · 折两员大将", W / 2, 700, 42, IVORY, b, "mm", bold=True, halo=8)
    else:
        lt = t - tw
        ctx.save(); shake(ctx, t, tw + 0.5, 12, 0.4)
        forest_plate(ctx, t, march=lt * 0.8, ambush=tw + 0.2, rout=clamp((lt - 1.2) / 2.5))
        ctx.restore()
        flash(ctx, t, tw, 0.2, 0.7)
        tag(ctx, "长久手 · 1584", W / 2, 520, BLU, S.p("twist", 0.5, 0.4), 34)


# ================================================================ s01 hookmap (owari)
GAKUDEN_LINE = [(136.885, 35.336), (136.905, 35.337), (136.930, 35.330), (136.957, 35.3215), (136.985, 35.312)]
KOMAKI_LINE = [(136.880, 35.270), (136.898, 35.284), (136.912, 35.2925), (136.935, 35.297), (136.960, 35.286), (136.985, 35.272)]
NAKAIRI = [(136.957, 35.3215), (136.990, 35.270), (137.010, 35.236), (137.028, 35.206), (137.040, 35.178), (137.0418, 35.1595),
           (137.08, 35.10), (137.12, 35.02), (137.159, 34.9563)]
NAKAIRI_REAL = NAKAIRI[:6]
TOK_OBATA = [(136.912, 35.2925), (136.930, 35.260), (136.955, 35.225), (136.964, 35.2049)]
TOK_VAN = [(136.964, 35.2049), (136.990, 35.215), (137.012, 35.218), (137.028, 35.208)]
TOK_MAIN = [(136.964, 35.2049), (137.000, 35.190), (137.035, 35.190), (137.064, 35.188), (137.060, 35.179)]


def ll(pts):
    return [Oll(a, b) for a, b in pts]


def sc_hookmap(ctx, S):
    t = S.t
    K = O("小牧山")
    cam = Cam(S, [(None, (K[0] + 80, K[1] + 350), 0.50), ("komaki", (K[0] + 40, K[1] - 20), 1.05, 1.5),
                  ("nakairi", (K[0] + 330, K[1] + 520), 0.55, 1.6), ("nagakute", (O("长久手")[0] - 40, O("长久手")[1] - 40), 1.15, 1.6),
                  ("peace", (K[0] + 100, K[1] + 300), 0.48, 1.4)])
    dim = 0.25 + 0.45 * S.p("forces", 0.8) * (1 - S.p("komaki", 0.6)) + 0.55 * S.p("peace", 0.8)
    map_base(ctx, "owari", cam, dim=dim)
    ctx.save(); cam.apply(ctx)
    z = cam.z
    fortline(ctx, ll(KOMAKI_LINE), S.p("komaki", 2.0), BLU, z)
    fortline(ctx, ll(GAKUDEN_LINE), S.p("komaki", 2.0, 2.5), RED, z)
    if S.on("nakairi"):
        dashed(ctx, ll(NAKAIRI), S.lin("nakairi", 5.0), RED, 9 / z, 0.9 * (1 - S.p("peace", 0.6)), offset=-t * 30)
        arrow(ctx, ll(NAKAIRI_REAL), S.p("nakairi", 3.0, 0.5), RED, 44 / z, 1 - S.p("peace", 0.6))
    if S.on("nagakute"):
        a = 1 - S.p("peace", 0.6)
        arrow(ctx, ll(TOK_OBATA + TOK_MAIN[1:]), S.p("nagakute", 2.2), BLU, 48 / z, a)
    ctx.restore()
    owari_labels(ctx, cam, (1 - S.p("forces", 0.5) * (1 - S.p("komaki", 0.6))) * (1 - S.p("peace", 0.6)),
                 only=("小牧山", "犬山城", "乐田", "冈崎城", "长久手", "岩崎城", "清洲城"))
    # forces
    if S.on("forces") and not S.on("komaki"):
        a = S.span("forces", 0.5, "komaki")
        text(ctx, "羽柴秀吉", 290, 560, 46, IVORY, a, "mm", bold=True, serif=True, halo=8)
        text(ctx, "十万", 290, 680, 130, RED, a, "mm", bold=True, serif=True, halo=12)
        text(ctx, "织田信雄 · 德川家康", 790, 560, 42, IVORY, a * S.p("forces", 0.5, 2.5), "mm", bold=True, serif=True, halo=8)
        text(ctx, "三万", 790, 680, 130, BLU, a * S.p("forces", 0.5, 2.5), "mm", bold=True, serif=True, halo=12)
        b = a * S.p("forces2", 0.5)
        # 3:1 bars
        ctx.rectangle(140, 860, 600 * S.p("forces2", 1.0), 54); ctx.set_source_rgba(*RED, 0.9 * b); ctx.fill()
        ctx.rectangle(140, 940, 200 * S.p("forces2", 1.0, 0.3), 54); ctx.set_source_rgba(*BLU, 0.9 * b); ctx.fill()
        text(ctx, "3", 770, 887, 54, RED, b, "lm", bold=True)
        text(ctx, "1", 370, 967, 54, BLU, b, "lm", bold=True)
        tag(ctx, "通说 · 各书出入很大", W / 2, 1090, GOLD, b * S.p("forces2", 0.5, 1.0), 30)
    if S.on("komaki") and not S.on("nakairi"):
        k = cam.sc(K)
        tag(ctx, "家康 · 小牧山", k[0] - 40, k[1] + 120, BLU, S.p("komaki", 0.6, 1.2))
        g = cam.sc(O("乐田"))
        tag(ctx, "秀吉 · 乐田", g[0] + 60, g[1] - 110, RED, S.p("komaki", 0.6, 4.0))
        text(ctx, "谁也不敢先动", W / 2, 1180, 44, GOLD, S.p("komaki", 0.6, 6.0), "mm", bold=True, serif=True, halo=8)
    if S.on("nakairi") and not S.on("nagakute"):
        a = S.p("nakairi", 0.6, 1.5)
        o = cam.sc(O("冈崎城"))
        tag(ctx, "三河 · 冈崎", o[0] - 30, o[1] - 70, BLU, a)
        text(ctx, "中入", W / 2, 560, 120, RED, S.p("nakairi", 0.6, 5.5), "mm", bold=True, serif=True, halo=12)
        text(ctx, "なかいり · 插进去", W / 2, 660, 36, IVORY, S.p("nakairi", 0.6, 6.0), "mm", halo=8)
    if S.on("nagakute") and not S.on("peace"):
        n = cam.sc(O("长久手"))
        burst(ctx, n[0], n[1], t, 70, S.p("nagakute", 0.4, 1.5), FIRE, 2)
        a1 = S.p("nagakute", 0.4, 4.2); a2 = S.p("nagakute", 0.4, 6.6)
        cross(ctx, n[0] - 150, n[1] + 150, 28, a1); text(ctx, "池田恒兴 战死", n[0] - 110, n[1] + 150, 36, IVORY, a1, "lm", bold=True, halo=8)
        cross(ctx, n[0] - 150, n[1] + 240, 28, a2); text(ctx, "森长可 战死", n[0] - 110, n[1] + 240, 36, IVORY, a2, "lm", bold=True, halo=8)
    if S.on("peace") and not S.on("question"):
        a = S.p("peace", 0.6)
        panel(ctx, 90, 470, 900, 640, a)
        text(ctx, "战场", 280, 560, 44, DIM, a, "mm", serif=True)
        text(ctx, "家康 胜", 280, 650, 70, BLU, a, "mm", bold=True, serif=True)
        text(ctx, "结局", 800, 560, 44, DIM, a * S.p("peace", 0.6, 2.5), "mm", serif=True)
        text(ctx, "秀吉 胜", 800, 650, 70, RED, a * S.p("peace", 0.6, 2.5), "mm", bold=True, serif=True)
        b = a * S.p("peace", 0.6, 4.5)
        text(ctx, "1584.11  信雄单独讲和", W / 2, 840, 42, IVORY, b, "mm", bold=True)
        text(ctx, "1584.12  家康次子 → 大坂", W / 2, 920, 42, IVORY, a * S.p("peace", 0.6, 7.5), "mm", bold=True)
        ctx.set_source_rgba(*GOLD, 0.6 * a); ctx.set_line_width(2); ctx.move_to(W / 2, 520); ctx.line_to(W / 2, 720); ctx.stroke()
    if S.on("question"):
        a = S.p("question", 0.6) * (1 - S.p("open", 0.6, 1.5))
        text(ctx, "赢了战场", W / 2, 600, 80, BLU, a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "为什么输了整盘棋？", W / 2, 720, 70, IVORY, a * S.p("question", 0.6, 1.4), "mm", bold=True, serif=True, halo=10)
        b = S.p("question", 0.6, 3.6) * (1 - S.p("open", 0.6, 1.5))
        text(ctx, "战术胜利  ≠  战略胜利", W / 2, 900, 54, GOLD, b, "mm", bold=True, serif=True, halo=8)
    if S.on("open"):
        a = S.p("open", 0.8, 1.2)
        text(ctx, "小牧山 → 谈判桌", W / 2, 760, 70, GOLD, a, "mm", bold=True, serif=True, halo=10)


# ================================================================ s02 nation
RED_DOM = [(135.52, 34.69), (135.76, 35.01), (134.69, 34.83), (136.10, 35.20), (135.20, 34.60)]
BLU_DOM = [(137.16, 34.95), (137.73, 34.71), (138.38, 34.98), (138.57, 35.66), (138.00, 36.20), (138.25, 36.45)]
ALLY_RED = [("春日山", "上杉景胜", (-1, -1)), ("常陆", "佐竹义重", (1, 0))]
ALLY_BLU = [("小田原", "北条", (1, 1)), ("土佐", "长宗我部", (-1, 1)), ("纪州", "杂贺众·根来众", (-1, 1)), ("越中", "佐佐成政", (-1, -1))]


def dom_fog(ctx, pts, color, a, r=90):
    if a <= 0:
        return
    for (lo, la) in pts:
        x, y = Nll(lo, la)
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, *color, 0.45 * a); g.add_color_stop_rgba(1, *color, 0)
        ctx.set_source(g); ctx.arc(x, y, r, 0, 2 * math.pi); ctx.fill()


def link(ctx, a, b, prog, color, z, alpha=1.0, bend=0.18, width=5, broken=0.0, t=0.0):
    """thin glowing curved alliance line from a to b"""
    if prog <= 0 or alpha <= 0:
        return
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    c = (mx - dy * bend, my + dx * bend)
    pts = [a, c, b]
    seg = cut(smooth(pts, 16), prog)
    if len(seg) < 2:
        return
    ctx.save(); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if broken > 0:
        ctx.set_dash([18 / z, (6 + 40 * broken) / z])
    al = alpha * (1 - 0.8 * broken)
    path(ctx, seg); ctx.set_source_rgba(*color, 0.18 * al); ctx.set_line_width(width * 4 / z); ctx.stroke()
    path(ctx, seg); ctx.set_source_rgba(*color, 0.9 * al); ctx.set_line_width(width / z); ctx.stroke()
    ctx.restore()
    # travelling spark
    if prog >= 1 and broken == 0:
        u = (t * 0.35) % 1.0
        x, y = cut(smooth(pts, 16), u)[-1]
        ctx.arc(x, y, 7 / z, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 0.8 * alpha); ctx.fill()


def nation_nets(ctx, S, cam, red_p, blu_p, alpha=1.0, broken=None, t=0.0):
    z = cam.z
    hub_r, hub_b = N("大坂"), N("尾张·小牧")
    for i, (nm, who, d) in enumerate(ALLY_RED):
        link(ctx, hub_r, N(nm), clamp(red_p * 2 - i * 0.5), RED, z, alpha, 0.15, t=t)
    for i, (nm, who, d) in enumerate(ALLY_BLU):
        br = broken.get(nm, 0) if broken else 0
        link(ctx, N("滨松") if nm in ("小田原",) else hub_b, N(nm), clamp(blu_p * 2.5 - i * 0.5), BLU, z, alpha, -0.15, broken=br, t=t)


def nation_ally_labels(ctx, S, cam, red_a, blu_a, broken=None):
    for nm, who, (dx, dy) in ALLY_RED:
        x, y = cam.sc(N(nm))
        draw_place(ctx, who, x, y, red_a, 32, RED, dx)
    for nm, who, (dx, dy) in ALLY_BLU:
        x, y = cam.sc(N(nm))
        br = broken.get(nm, 0) if broken else 0
        draw_place(ctx, who, x, y, blu_a * (1 - 0.6 * br), 32, BLU, dx)
        if br > 0:
            cross(ctx, x, y, 16, br * blu_a, (0.9, 0.9, 0.9), 6)


def sc_nation(ctx, S):
    t = S.t
    Kc = N("尾张·小牧")
    cam = Cam(S, [(None, (Nll(136.3, 35.6)[0], Nll(136.3, 35.6)[1]), 1.0), ("ieyasu", (Nll(137.4, 35.6)[0], Nll(137.4, 35.6)[1]), 1.05),
                  ("net", (Nll(136.6, 35.3)[0], Nll(136.6, 35.3)[1] - 60), 0.52, 2.5),
                  ("two", (Kc[0], Kc[1]), 0.9, 3.0)])
    map_base(ctx, "nation", cam, dim=0.1)
    ctx.save(); cam.apply(ctx)
    dom_fog(ctx, RED_DOM, RED, S.p("shizu", 1.5, 1.0) * (1 - 0.4 * S.p("net", 1.0)), 110)
    dom_fog(ctx, BLU_DOM, BLU, S.p("ieyasu", 1.5, 2.0) * (1 - 0.4 * S.p("net", 1.0)), 110)
    nation_nets(ctx, S, cam, S.lin("red", 3.0), S.lin("blue", 6.0), 1.0, t=t)
    if S.on("kishu"):
        arrow(ctx, [N("纪州"), Nll(135.25, 34.45), Nll(135.45, 34.62)], S.p("kishu", 1.5), BLU, 30 / cam.z, S.span("kishu", 0.5, "two"))
    ctx.restore()
    # shizugatake
    if S.on("shizu") and not S.on("nobukatsu"):
        x, y = cam.sc(Nll(136.19, 35.54))
        a = S.span("shizu", 0.5, "nobukatsu")
        burst(ctx, x, y, t, 50, a * 0.8, FIRE, 1)
        tag(ctx, "1583 贱岳 · 秀吉胜", x, y - 80, RED, a)
        o = cam.sc(N("大坂"))
        draw_place(ctx, "大坂", o[0], o[1], a * S.p("shizu", 0.5, 4.0), 34, RED, -1, True, True)
    if S.on("nobukatsu") and not S.on("ieyasu"):
        a = S.span("nobukatsu", 0.5, "ieyasu")
        panel(ctx, 90, 470, 900, 520, a)
        text(ctx, "织田信雄", 300, 580, 60, BLU, a, "mm", bold=True, serif=True)
        text(ctx, "信长次子 · 名义上的主君", 300, 650, 30, IVORY, a, "mm")
        text(ctx, "羽柴秀吉", 780, 580, 60, RED, a * S.p("nobukatsu", 0.6, 1.5), "mm", bold=True, serif=True)
        text(ctx, "织田家臣 · 贱岳之后坐大", 780, 650, 30, IVORY, a * S.p("nobukatsu", 0.6, 1.5), "mm")
        b = a * S.p("nobukatsu", 0.6, 3.5)
        text(ctx, "辅佐？", W / 2, 790, 50, DIM, b, "mm", bold=True, serif=True)
        ctx.set_source_rgba(*RED, b); ctx.set_line_width(5); ctx.move_to(W / 2 - 80, 795); ctx.line_to(W / 2 + 80, 795); ctx.stroke()
        text(ctx, "取代", W / 2, 900, 70, RED, a * S.p("nobukatsu", 0.6, 5.0), "mm", bold=True, serif=True, halo=8)
        if S.on("break"):
            c = S.p("break", 0.3)
            ctx.set_source_rgba(1, 0.4, 0.3, c); ctx.set_line_width(8)
            ctx.move_to(W / 2 - 10, 470); ctx.line_to(W / 2 + 25, 600); ctx.line_to(W / 2 - 20, 720); ctx.line_to(W / 2 + 15, 990); ctx.stroke()
            tag(ctx, "1584.3 信雄杀亲秀吉家老", W / 2, 1060, RED, c, 32)
    if S.on("ieyasu") and not S.on("net"):
        a = S.span("ieyasu", 0.6, "net")
        x, y = cam.sc(Nll(138.2, 35.4))
        tag(ctx, "德川家康 · 五国", x, y + 40, BLU, a, 36)
        k = cam.sc(Kc)
        draw_place(ctx, "尾张", k[0], k[1], a, 34, BLU, -1, True)
    if S.on("net"):
        a = 1 - S.p("two", 0.8, 3.0) * 0.3
        nation_ally_labels(ctx, S, cam, S.p("red", 0.8, 1.0) * a, S.p("blue", 0.8, 1.0) * a)
        o = cam.sc(N("大坂")); k = cam.sc(Kc)
        draw_place(ctx, "秀吉 · 大坂", o[0], o[1], S.p("net", 0.6), 32, RED, -1, True, True)
        draw_place(ctx, "小牧", k[0], k[1], S.p("net", 0.6), 32, BLU, 1, True, True)
        legend_rb(ctx, S.p("net", 0.6))
    if S.on("kishu") and not S.on("two"):
        x, y = cam.sc(N("大坂"))
        burst(ctx, x, y + 40, t, 60, S.span("kishu", 0.5, "two"), FIRE, 4)
    if S.on("two"):
        k = cam.sc(Kc)
        pulse_ring(ctx, k[0], k[1], t, GOLD, 50, S.p("two", 0.6, 2.0))
        text(ctx, "两张网", W / 2, 520, 72, GOLD, S.p("two", 0.6, 0.5) * (1 - S.p("two", 0.6, 9.0)), "mm", bold=True, serif=True, halo=10)


# ================================================================ s03 / s04 owari theatre
DEF_FIG = None


def cross_section(ctx, S, a):
    """attacker crossing open ground under fire vs defender behind rampart"""
    if a <= 0:
        return
    t = S.t
    panel(ctx, 50, 440, 980, 720, a)
    # ground
    ctx.rectangle(70, 900, 940, 6); ctx.set_source_rgba(*DIM, 0.6 * a); ctx.fill()
    # rampart on right
    ctx.move_to(760, 906); ctx.line_to(800, 820); ctx.line_to(1000, 820); ctx.line_to(1000, 906); ctx.close_path()
    ctx.set_source_rgba(0.35, 0.30, 0.22, a); ctx.fill()
    for i in range(3):
        ashigaru(ctx, 830 + i * 60, 822, 0.75, 0, BLU, "teppo", -1, a, aim=True, col=(0.75, 0.72, 0.66))
        age = (t * 0.9 + i * 0.37) % 1.6
        muzzle(ctx, 830 + i * 60 - 52, 745, age, -1, 0.7)
    # attackers advancing from left, falling
    adv = (t * 0.12) % 1.0
    for i in range(8):
        x = 100 + i * 52 + adv * 220
        fall = 1 if (i % 3 == 0 and adv > 0.4) else 0
        ashigaru(ctx, x, 900, 0.7, t * 6 + i, RED, "yari", 1, a * (0.4 if fall else 1), run=0.6, lean=1.2 * fall, col=(0.75, 0.72, 0.66))
    # fire cone
    ctx.move_to(800, 770); ctx.line_to(260, 830); ctx.line_to(260, 905); ctx.close_path()
    ctx.set_source_rgba(1, 0.6, 0.2, 0.10 * a); ctx.fill()
    text(ctx, "开阔地 · 射程内", 380, 960, 30, IVORY, a, "mm", bold=True)
    text(ctx, "土垒后 · 只管开火", 880, 960, 30, IVORY, a, "mm", bold=True)
    text(ctx, "进攻", 200, 500, 40, RED, a, "mm", bold=True, serif=True)
    text(ctx, "防守", 880, 500, 40, BLU, a, "mm", bold=True, serif=True)


def rule_card(ctx, S, a):
    if a <= 0:
        return
    panel(ctx, 70, 440, 940, 700, a)
    text(ctx, "攻坚的经验法则", W / 2, 520, 40, GOLD, a, "mm", bold=True, serif=True)
    text(ctx, "3 : 1", W / 2, 690, 190, IVORY, a, "mm", bold=True, serif=True, halo=12)
    text(ctx, "进攻方 ≈ 守方的三倍", W / 2, 830, 40, IVORY, a, "mm")
    b = a * S.p("rule2", 0.6, 0.3)
    text(ctx, "秀吉手里：恰好三比一", W / 2, 940, 44, RED, b, "mm", bold=True)
    text(ctx, "账面刚好够 · 代价是人命", W / 2, 1020, 40, DIM, a * S.p("rule2", 0.6, 2.8), "mm", bold=True)


def shizu_card(ctx, S, a):
    """1583 Shizugatake: Sakuma's raid & Hideyoshi's counter-blow (schematic)"""
    if a <= 0:
        return
    t = S.t
    panel(ctx, 70, 440, 940, 700, a)
    text(ctx, "一年前 · 贱岳（1583）", W / 2, 510, 40, GOLD, a, "mm", bold=True, serif=True)
    # two fort lines schematic
    ctx.set_line_width(14)
    ctx.set_source_rgba(*BLU_D, a); ctx.move_to(160, 640); ctx.line_to(920, 620); ctx.stroke()   # Shibata (north) - colour neutral-ish
    ctx.set_source_rgba(*RED, a); ctx.move_to(160, 900); ctx.line_to(920, 880); ctx.stroke()
    text(ctx, "柴田方 砦线", 200, 600, 30, IVORY, a, "lm")
    text(ctx, "秀吉方 砦线", 200, 950, 30, IVORY, a, "lm")
    p = S.p("shizu2", 2.5, 0.5)
    arrow(ctx, [(700, 650), (820, 760), (720, 860)], p, BLU_D, 30, a)
    text(ctx, "佐久间盛政 绕道突袭", 830, 760, 30, IVORY, a * p, "lm")
    q = S.p("shizu2", 2.0, 5.0)
    arrow(ctx, [(300, 1060), (520, 960), (700, 840)], q, RED, 40, a)
    text(ctx, "秀吉回师反扑", 300, 1100, 32, RED, a * q, "lm", bold=True)


def sc_owari(ctx, S):
    t = S.t
    sid = S.scene["id"]
    K = O("小牧山")
    if sid == "s03":
        cam = Cam(S, [(None, (O("犬山城")[0], O("犬山城")[1] + 80), 1.05), ("haguro", (O("羽黑")[0], O("羽黑")[1] + 60), 1.1),
                      ("komakiyama", (K[0] + 20, K[1] - 10), 1.25), ("gakuden", (K[0] + 30, K[1] - 80), 1.05),
                      ("lines", (K[0] + 30, K[1] - 60), 0.95), ("itch", (K[0] + 220, K[1] + 300), 0.62)])
    else:
        cam = Cam(S, [(None, (O("乐田")[0] + 30, O("乐田")[1] + 40), 1.0), ("plan", (K[0] + 330, K[1] + 650), 0.50, 2.5),
                      ("depart", (O("乐田")[0] + 60, O("乐田")[1] + 140), 1.0), ("snake", (K[0] + 230, K[1] + 330), 0.72, 3.0),
                      ("obata", (K[0] + 200, K[1] + 290), 0.66), ("hunter", (O("白山林")[0], O("白山林")[1] + 40), 0.9, 3.0)])
    night = 0.0
    if sid == "s04":
        night = 0.35 * S.p("depart", 1.0) * (1 - S.p("hunter", 2.0)) + 0.3 * S.span("mech1", 0.5, "slow") + 0.3 * S.span("mech2", 0.5, "spy")
    # mechanism cards hide map
    card_a = 0.0
    if sid == "s03":
        card_a = max(S.span("cost", 0.5, "rule"), S.span("rule", 0.5, "shizu2"), S.span("shizu2", 0.5, "itch"))
    map_base(ctx, "owari", cam, dim=0.15 + night + 0.6 * card_a)
    z = cam.z
    ctx.save(); cam.apply(ctx)
    if sid == "s03":
        # opening moves
        if S.on("inuyama"):
            arrow(ctx, [Oll(136.86, 35.42), Oll(136.90, 35.40), O("犬山城")], S.p("inuyama", 2.0, 1.5), RED, 40 / z, 1 - S.p("komakiyama", 1.0))
        if S.on("haguro"):
            aa = 1 - S.p("komakiyama", 1.0)
            arrow(ctx, [O("犬山城"), Oll(136.945, 35.37), O("羽黑")], S.p("haguro", 1.6), RED, 40 / z, aa * (1 - 0.6 * S.p("haguro", 1.0, 3.5)))
            arrow(ctx, [Oll(136.93, 35.29), Oll(136.945, 35.32), Oll(136.950, 35.345)], S.p("haguro", 1.2, 2.5), BLU, 44 / z, aa)
        fortline(ctx, ll(KOMAKI_LINE), S.p("dorui", 2.5), BLU, z)
        fortline(ctx, ll(GAKUDEN_LINE), S.p("gakuden", 2.5, 0.6), RED, z)
        if S.on("itch"):
            arrow(ctx, ll(NAKAIRI[:4]), S.p("itch", 2.5, 3.5), RED, 36 / z, 0.8)
    else:
        fortline(ctx, ll(KOMAKI_LINE), 1, BLU, z)
        fortline(ctx, ll(GAKUDEN_LINE), 1, RED, z)
        if S.on("plan") and not S.on("depart"):
            a = S.span("plan", 0.5, "depart")
            dashed(ctx, ll(NAKAIRI), S.lin("plan", 3.0), RED, 9 / z, a, offset=-t * 30)
        if S.on("depart"):
            # the snake: four units along the route; head advances over the scene
            prog = 0.08 + 0.62 * S.lin("snake", 26.0) + 0.04 * S.lin("depart", 3.0)
            stretch = 0.035 + 0.06 * S.p("slow", 4.0)
            dashed(ctx, ll(NAKAIRI_REAL), prog, RED, 7 / z, 0.6, offset=-t * 20)
            for i in range(4):
                u = prog - i * stretch
                if u > 0:
                    x, y = at_poly(ll(NAKAIRI_REAL), u)
                    unit(ctx, x, y, RED, S.p("depart", 0.6, 0.5 + i * 0.4), 46 / z, 30 / z)
            if S.on("obata"):
                arrow(ctx, ll(TOK_OBATA), S.p("obata", 2.5), BLU, 44 / z, 1.0)
            if S.on("hunter"):
                hp = S.p("hunter", 5.0)
                tail = at_poly(ll(NAKAIRI_REAL), prog - 3 * stretch)
                ob = O("小幡城")
                mid = ((ob[0] + tail[0]) / 2 - 30, (ob[1] + tail[1]) / 2 - 40)
                dashed(ctx, [ob, mid, tail], hp, BLU, 9 / z, 0.95, offset=-t * 40)
    ctx.restore()
    # labels
    if sid == "s03":
        la = 1 - card_a
        owari_labels(ctx, cam, la, only=("小牧山", "犬山城", "乐田", "羽黑", "小幡城", "清洲城", "岩崎城", "冈崎城"))
        if S.on("inuyama") and not S.on("haguro"):
            x, y = cam.sc(O("犬山城"))
            burst(ctx, x, y, t, 46, S.p("inuyama", 0.5, 2.8), FIRE, 1)
            tag(ctx, "3.13 池田恒兴取犬山", x, y - 90, RED, S.p("inuyama", 0.5, 3.0))
        if S.on("haguro") and not S.on("komakiyama"):
            x, y = cam.sc(O("羽黑"))
            tag(ctx, "3.17 羽黑 · 酒井忠次反击", x, y + 90, BLU, S.p("haguro", 0.5, 2.5))
        if S.on("komakiyama") and not S.on("lines"):
            x, y = cam.sc(K)
            pulse_ring(ctx, x, y, t, BLU, 40, S.span("komakiyama", 0.5, "lines"))
            tag(ctx, "1563 信长筑城 · 平原上的高点", x, y + 110, GOLD, S.span("komakiyama", 0.5, "gakuden"), 30)
        if S.on("lines") and not S.on("why"):
            a = S.span("lines", 0.5, "why")
            ruler(ctx, cam.sc(Oll(136.935, 35.297)), cam.sc(Oll(136.935, 35.330)), "相隔数公里", a, GOLD)
            text(ctx, "对峙 数月", W / 2, 520, 72, GOLD, a * S.p("lines", 0.6, 3.5), "mm", bold=True, serif=True, halo=10)
        if S.on("why") and not S.on("cost"):
            text(ctx, "人多的一方，为什么不冲？", W / 2, 560, 54, IVORY, S.span("why", 0.5, "cost"), "mm", bold=True, serif=True, halo=10)
        cross_section(ctx, S, S.span("cost", 0.5, "rule"))
        rule_card(ctx, S, S.span("rule", 0.5, "shizu2"))
        shizu_card(ctx, S, S.span("shizu2", 0.5, "itch"))
        if S.on("itch"):
            text(ctx, "正面算不过来 → 找侧面", W / 2, 540, 54, GOLD, S.p("itch", 0.6, 4.0), "mm", bold=True, serif=True, halo=10)
        legend_rb(ctx, la * S.p("inuyama", 0.6))
    else:
        owari_labels(ctx, cam, 1.0, only=("小牧山", "乐田", "小幡城", "岩崎城", "冈崎城", "白山林", "长久手"))
        if not S.on("plan"):
            x, y = cam.sc(O("乐田"))
            tag(ctx, "池田恒兴", x + 10, y + 90, RED, S.p("ikeda", 0.6, 1.0))
            text(ctx, "信长乳兄弟 · 女婿刚在羽黑吃了败仗", W / 2, 1180, 36, IVORY, S.p("ikeda", 0.6, 3.5), "mm", bold=True, halo=8)
        if S.on("plan") and not S.on("who"):
            a = S.span("plan", 0.5, "who")
            o = cam.sc(O("冈崎城"))
            pulse_ring(ctx, o[0], o[1], t, BLU, 40, a)
            tag(ctx, "三河空虚？", o[0] - 40, o[1] - 80, BLU, a * S.p("plan", 0.5, 2.5))
            b = a * S.p("plan", 0.6, 5.0)
            panel(ctx, 110, 460, 860, 300, b)
            text(ctx, "家康不回救", 300, 540, 40, IVORY, b, "mm", bold=True)
            text(ctx, "→ 丢了根本", 300, 610, 40, RED, b, "mm", bold=True)
            text(ctx, "家康回救", 780, 540, 40, IVORY, b * S.p("plan", 0.6, 7.0), "mm", bold=True)
            text(ctx, "→ 走出工事", 780, 610, 40, RED, b * S.p("plan", 0.6, 7.0), "mm", bold=True)
            text(ctx, "两头都是赢？", W / 2, 700, 34, GOLD, b * S.p("plan", 0.6, 9.0), "mm")
        if S.on("who") and not S.on("depart"):
            tag(ctx, "通说：池田献策、秀吉批准（多出后世记载）", W / 2, 560, GOLD, S.span("who", 0.5, "depart"), 30)
        if S.on("order") and not S.on("mech1"):
            a = S.span("order", 0.5, "mech1")
            rows = [("① 池田恒兴", "约六千"), ("② 森长可", "约三千"), ("③ 堀秀政", "约三千"), ("④ 羽柴秀次", "约八千")]
            panel(ctx, 150, 440, 780, 420, a)
            for i, (n_, c_) in enumerate(rows):
                k = a * S.p("order", 0.4, 0.3 + i * 2.2)
                unit_block(ctx, 230, 510 + i * 80, 44, 28, RED, k)
                text(ctx, n_, 280, 510 + i * 80, 40, IVORY, k, "lm", bold=True)
                text(ctx, c_, 860, 510 + i * 80, 40, RED, k, "rm", bold=True)
            text(ctx, "合计 约两万", W / 2, 820, 36, GOLD, a * S.p("order", 0.5, 9.5), "mm", bold=True)
        if S.on("mech1") and not S.on("mech2"):
            a = S.span("mech1", 0.5, "mech2")
            text(ctx, "机制一", W / 2, 500, 40, GOLD, a, "mm", serif=True, halo=8)
            text(ctx, "分兵绕后 · 最怕慢", W / 2, 580, 64, IVORY, a, "mm", bold=True, serif=True, halo=10)
            if S.on("slow"):
                h = at_poly(ll(NAKAIRI_REAL), 0.08 + 0.62 * S.lin("snake", 26.0) + 0.04)
                tl_ = at_poly(ll(NAKAIRI_REAL), 0.08 + 0.62 * S.lin("snake", 26.0) + 0.04 - 3 * (0.035 + 0.06 * S.p("slow", 4.0)))
                ruler(ctx, cam.sc(tl_), cam.sc(h), "首尾好几公里", S.p("slow", 0.6, 3.0) * a, GOLD, off=0)
        if S.on("mech2") and not S.on("obata"):
            a = S.span("mech2", 0.5, "obata")
            text(ctx, "机制二", W / 2, 500, 40, GOLD, a, "mm", serif=True, halo=8)
            text(ctx, "信息", W / 2, 580, 64, IVORY, a, "mm", bold=True, serif=True, halo=10)
            if S.on("spy"):
                k = cam.sc(K)
                b = S.p("spy", 0.6, 1.0) * a
                for i, (lo, la) in enumerate(((136.99, 35.27), (137.01, 35.24), (136.975, 35.255))):
                    v = cam.sc(Oll(lo, la))
                    dashed(ctx, [v, k], clamp(S.lin("spy", 2.0, 1.0 + i * 0.6)), GOLD, 4, b, dash=(10, 10))
                    ctx.arc(v[0], v[1], 9, 0, 6.3); ctx.set_source_rgba(*GOLD, b); ctx.fill()
                tag(ctx, "沿途百姓报信", k[0] - 60, k[1] - 90, GOLD, b)
        if S.on("obata"):
            o = cam.sc(O("小幡城"))
            tag(ctx, "4.8 夜 家康主力 → 小幡城", o[0] - 30, o[1] + 90, BLU, S.p("obata", 0.6, 2.0) * (1 - S.p("hunter", 0.6, 3.0)))
        if S.on("hunter"):
            a = S.p("hunter", 0.6, 3.0)
            text(ctx, "猎人", 300, 540, 64, BLU, a, "mm", bold=True, serif=True, halo=10)
            text(ctx, "⇄", W / 2, 540, 64, GOLD, a, "mm", bold=True)
            text(ctx, "猎物", 780, 540, 64, RED, a, "mm", bold=True, serif=True, halo=10)
        if S.on("depart") and not S.on("order"):
            text(ctx, "4月6日 夜", W / 2, 540, 70, IVORY, S.span("depart", 0.5, "order"), "mm", bold=True, serif=True, halo=10)
        legend_rb(ctx, 1.0)


# ================================================================ s05 forest (Hakusanbayashi)
def mini_map(ctx, S, cam_center, zoom, a, draw):
    """map plate (full frame) used inside illustration scenes"""
    pass


def sc_forest(ctx, S):
    t = S.t
    if not S.on("rest"):
        # Iwasaki castle on map
        I = O("岩崎城")
        cam = Cam(S, [(None, (I[0] - 40, I[1] - 100), 1.1), ("iwasaki", (I[0], I[1] - 60), 1.35, 6.0)])
        map_base(ctx, "owari", cam, 0.15)
        ctx.save(); cam.apply(ctx)
        z = cam.z
        for i, u in enumerate((0.93, 0.86, 0.80, 0.68)):
            x, y = at_poly(ll(NAKAIRI_REAL), u)
            unit(ctx, x, y, RED, 1.0, 46 / z, 30 / z)
        ctx.restore()
        owari_labels(ctx, cam, 1.0, only=("岩崎城", "白山林", "长久手", "色金山"))
        x, y = cam.sc(I)
        burst(ctx, x, y, t, 60, S.p("iwasaki", 0.5, 1.0), FIRE, 3)
        tag(ctx, "岩崎城 · 丹羽氏重战死", x - 40, y + 100, BLU, S.p("iwasaki", 0.6, 2.5))
        text(ctx, "时间 · 耽误了", W / 2, 540, 60, GOLD, S.p("iwasaki", 0.6, 5.5), "mm", bold=True, serif=True, halo=10)
        legend_rb(ctx, 1.0)
        return
    if not S.on("panic"):
        amb = S.c0("ambush")
        rout = clamp((t - amb - 1.0) / 3.0) if S.on("ambush") else 0
        ctx.save(); shake(ctx, t, amb + 0.35, 14, 0.5)
        forest_plate(ctx, t, march=(t - S.c0("rest")) * 0.25 * (1 - rout), ambush=amb if S.on("ambush") else -1, rout=rout)
        # cooking smoke while resting
        if not S.on("ambush"):
            for i in range(3):
                x = 250 + i * 280
                for k in range(5):
                    u = ((t * 0.25 + k * 0.2 + i * 0.13) % 1.0)
                    r = 14 + 40 * u
                    g = cairo.RadialGradient(x + u * 30, 1130 - u * 260, 0, x + u * 30, 1130 - u * 260, r)
                    g.add_color_stop_rgba(0, 0.75, 0.75, 0.72, 0.35 * (1 - u)); g.add_color_stop_rgba(1, 0.75, 0.75, 0.72, 0)
                    ctx.set_source(g); ctx.arc(x + u * 30, 1130 - u * 260, r, 0, 6.3); ctx.fill()
        ctx.restore()
        flash(ctx, t, amb + 0.3, 0.15, 0.5)
        tag(ctx, "4.9 清晨 · 白山林", W / 2, 520, RED, S.p("rest", 0.5) * (1 - S.p("ambush", 0.5)), 34)
        if S.on("hidetsugu"):
            text(ctx, "秀次 丢马而逃", W / 2, 560, 64, IVORY, S.p("hidetsugu", 0.5), "mm", bold=True, serif=True, halo=10)
        return
    if not S.on("contagion"):
        # panic flows forward on the map
        H_ = O("白山林")
        cam = Cam(S, [(None, (H_[0] + 40, H_[1] + 40), 1.0)])
        map_base(ctx, "owari", cam, 0.2)
        ctx.save(); cam.apply(ctx)
        z = cam.z
        for i, u in enumerate((0.93, 0.86, 0.80)):
            x, y = at_poly(ll(NAKAIRI_REAL), u)
            unit(ctx, x, y, RED, 1.0, 46 / z, 30 / z)
        x, y = at_poly(ll(NAKAIRI_REAL), 0.66)
        lt = t - S.c0("panic")
        particles(ctx, x, y, lt / 3.0, 80, 120, RED, seed=5, drift=(80, 160))
        arrow(ctx, ll(TOK_VAN), 1.0, BLU, 44 / z, 1.0)
        ctx.restore()
        owari_labels(ctx, cam, 1.0, only=("白山林", "岩崎城", "长久手", "小幡城"))
        hx, hy = cam.sc(at_poly(ll(NAKAIRI_REAL), 0.66))
        cross(ctx, hx, hy, 26, S.p("panic", 0.4), RED)
        tag(ctx, "秀次队 溃散", hx - 140, hy - 60, RED, S.p("panic", 0.5))
        for i in range(3):
            a0 = cam.sc(at_poly(ll(NAKAIRI_REAL), 0.70 + i * 0.04)); a1 = cam.sc(at_poly(ll(NAKAIRI_REAL), 0.76 + i * 0.06))
            arrow(ctx, [a0, a1], S.p("panic", 1.0, 0.8 + i * 0.5), (1.0, 0.55, 0.45), 18, 0.8, glow=False)
        legend_rb(ctx, 1.0)
        return
    # contagion diagram
    dark_card_bg(ctx)
    lt = t - S.c0("contagion")
    a = S.p("contagion", 0.6)
    text(ctx, "溃败的传染", W / 2, 500, 64, GOLD, a, "mm", bold=True, serif=True, halo=8)
    n = 11
    for i in range(n):
        x = 110 + i * 86
        trig = 0.8 + (n - 1 - i) * 0.45
        k = clamp((lt - trig) / 0.6)
        col = tuple(lerp(RED[j], (0.95, 0.85, 0.75)[j], k * 0.0) for j in range(3))
        facing = 1 if k < 0.5 else -1
        ashigaru(ctx, x + k * (-30), 880, 0.75, lt * 6 * (0.2 + k), RED, "yari", facing, a, run=k,
                 col=(lerp(0.70, 0.95, k), lerp(0.66, 0.45, k), lerp(0.58, 0.35, k)))
        if k > 0.1:
            ctx.new_path(); ctx.arc(x, 640, 8 + 6 * k, 0, 6.3); ctx.set_source_rgba(1, 0.5, 0.35, 0.7 * k * a); ctx.fill()
    text(ctx, "← 队尾先乱", 980, 960, 34, IVORY, a * S.p("contagion", 0.5, 1.0), "rm", bold=True)
    text(ctx, "看见别人跑，自己也跑", W / 2, 1080, 46, IVORY, a * S.p("contagion", 0.5, 4.0), "mm", bold=True, serif=True)


# ================================================================ s06 fan (Hori Hidemasa)
def sc_fan(ctx, S):
    t = S.t
    if not S.on("fan"):
        Hh = Oll(137.045, 35.185)
        cam = Cam(S, [(None, (Hh[0] - 20, Hh[1] + 10), 1.25)])
        map_base(ctx, "owari", cam, 0.2)
        ctx.save(); cam.apply(ctx)
        z = cam.z
        unit(ctx, Hh[0], Hh[1], RED, 1.0, 52 / z, 34 / z)
        pursue = [Oll(137.020, 35.212), Oll(137.032, 35.200), Oll(137.040, 35.191)]
        k = S.p("hori", 2.0, 2.0)
        back = S.p("hori", 1.5, 6.5)
        arrow(ctx, pursue, k * (1 - 0.45 * back), BLU, 40 / z, 1 - 0.5 * back)
        ctx.restore()
        owari_labels(ctx, cam, 1.0, only=("白山林", "长久手", "色金山", "岩崎城"))
        x, y = cam.sc(Hh)
        tag(ctx, "③ 堀秀政 掉头布阵", x + 20, y + 80, RED, S.p("hori", 0.5, 0.5))
        if S.on("hori"):
            for i in range(4):
                age = (t - S.c0("hori") - 5.0 - i * 0.12)
                muzzle(ctx, x - 60 + i * 22, y - 40, age % 1.3 if age > 0 else -1, -1, 0.6)
            text(ctx, "一齐开火 · 打退追兵", W / 2, 540, 54, IVORY, S.p("hori", 0.6, 6.5), "mm", bold=True, serif=True, halo=10)
        legend_rb(ctx, 1.0)
        return
    if not S.on("retreat"):
        paint_surface(ctx, illus.sky("hill"), 0, 0)
        hills(ctx, 980, 260, (0.12, 0.10, 0.08), seed=5, freq=0.004)
        rise = S.p("fan", 2.5, 0.4)
        golden_fan(ctx, 640, 860 - 40 * rise + 120 * (1 - rise), 1.0, t, clamp(rise * 1.5), glow=rise)
        for i in range(6):
            ashigaru(ctx, 470 + i * 60, 880 + (i % 2) * 10, 0.55, 0, BLU, "yari", -1, rise)
        drift(ctx, fog(51, 0.4, (0.6, 0.55, 0.45), 500), 820, t, 14, 0.7)
        hills(ctx, 1350, 260, (0.05, 0.045, 0.04), seed=6, freq=0.005)
        for i in range(5):
            ashigaru(ctx, 140 + i * 70, 1300 + (i % 2) * 14, 1.1, 0, RED, "teppo", 1, 1.0)
        if S.on("ieyasu"):
            text(ctx, "家康本人，到了", W / 2, 520, 72, GOLD, S.p("ieyasu", 0.6, 0.5), "mm", bold=True, serif=True, halo=12)
            text(ctx, "金扇马印", 640, 1060, 36, (1, 0.85, 0.5), S.p("ieyasu", 0.6), "mm", bold=True, halo=8)
        return
    Hh = Oll(137.045, 35.185)
    cam = Cam(S, [(None, (Hh[0] - 40, Hh[1] - 40), 0.85)])
    map_base(ctx, "owari", cam, 0.2 + 0.4 * S.p("retreat2", 0.6))
    ctx.save(); cam.apply(ctx)
    z = cam.z
    arrow(ctx, [Hh, Oll(137.025, 35.215), Oll(137.00, 35.245), Oll(136.98, 35.27)], S.p("retreat", 3.0, 1.0), RED, 40 / z, 1.0)
    for i, u in enumerate((0.93, 0.86)):
        x, y = at_poly(ll(NAKAIRI_REAL), u)
        unit(ctx, x, y, RED, 1.0, 46 / z, 30 / z)
    g = O("色金山")
    ctx.restore()
    gx, gy = cam.sc(g)
    golden_fan(ctx, gx, gy, 0.22, t, 1.0, 0.6)
    owari_labels(ctx, cam, 1.0, only=("长久手", "色金山", "白山林", "岩崎城"))
    if S.on("retreat2"):
        a = S.p("retreat2", 0.6)
        panel(ctx, 110, 460, 860, 380, a)
        text(ctx, "明智？", 300, 560, 60, IVORY, a, "mm", bold=True, serif=True)
        text(ctx, "见死不救？", 760, 560, 60, IVORY, a * S.p("retreat2", 0.6, 1.2), "mm", bold=True, serif=True)
        text(ctx, "四队之中 · 唯一全身而退", W / 2, 720, 46, GOLD, a * S.p("retreat2", 0.6, 3.0), "mm", bold=True)
    legend_rb(ctx, 1.0)


# ================================================================ s07 clash (Nagakute)
def clash_plate(ctx, t, lt, intensity=1.0):
    paint_surface(ctx, illus.sky("hill"), 0, 0)
    hills(ctx, 860, 200, (0.14, 0.12, 0.10), seed=11)
    drift(ctx, fog(61, 0.5, (0.72, 0.70, 0.66), 600), 600, t, 22, 0.9)
    ctx.rectangle(0, 960, W, H); g = cairo.LinearGradient(0, 960, 0, H)
    g.add_color_stop_rgb(0, 0.18, 0.15, 0.11); g.add_color_stop_rgb(1, 0.04, 0.035, 0.03)
    ctx.set_source(g); ctx.fill()
    # far line of blue gunners on a rise, volleys
    for i in range(10):
        x = 560 + i * 52
        ashigaru(ctx, x, 990, 0.5, 0, BLU, "teppo", -1, 1.0, aim=True)
        age = (lt * 0.8 + i * 0.09) % 2.2
        muzzle(ctx, x - 36, 940, age, -1, 0.7)
        smoke_puffs(ctx, x - 36, 942, age, seed=i, size=0.7, facing=-1)
    # charging blue riders right->left, red spearmen left
    for i in range(5):
        u = (lt * 0.25 + i * 0.2) % 1.0
        x = W + 200 - u * (W + 500)
        rider(ctx, x, 1250 + i * 34, 1.1 - i * 0.05, t * 10 + i, BLU, -1, clamp(intensity * 2))
    for i in range(7):
        x = 60 + i * 80 + 25 * math.sin(lt * 1.5 + i)
        ashigaru(ctx, x, 1360 + (i % 2) * 30, 1.05, lt * 3 + i, RED, "yari", 1, 1.0, run=0.3, lean=0.12 * math.sin(lt * 2 + i))
    drift(ctx, fog(63, 0.4, (0.75, 0.73, 0.70), 500), 1000, t + 20, 30, 0.7)
    for i in range(4):
        age = (lt * 1.1 + i * 0.6) % 2.6
        muzzle(ctx, 200 + i * 220, 1210 - (i % 2) * 40, age, 1 if i % 2 else -1, 1.0)


def sc_clash(ctx, S):
    t = S.t
    Nk = O("长久手")
    if not S.on("battle"):
        cam = Cam(S, [(None, (Nk[0] - 60, Nk[1] - 30), 0.95)])
        map_base(ctx, "owari", cam, 0.2)
        ctx.save(); cam.apply(ctx)
        z = cam.z
        p = S.p("turn", 3.0, 0.5)
        for i, (u, lab) in enumerate(((0.93, "池田"), (0.86, "森"))):
            x0, y0 = at_poly(ll(NAKAIRI_REAL), u)
            x1, y1 = lerp(x0, Nk[0], p), lerp(y0, Nk[1], p)
            unit(ctx, x1 + i * 40 / z, y1 + i * 40 / z, RED, 1.0, 46 / z, 30 / z)
        arrow(ctx, ll(TOK_MAIN), S.p("turn", 3.0, 3.0), BLU, 52 / z, 1.0)
        ctx.restore()
        owari_labels(ctx, cam, 1.0, only=("长久手", "色金山", "岩崎城", "小幡城", "白山林"))
        x, y = cam.sc(Nk)
        burst(ctx, x, y, t, 70, S.p("turn", 0.4, 5.0), FIRE, 2)
        tag(ctx, "家康本队", cam.sc(O("色金山"))[0] + 30, cam.sc(O("色金山"))[1] - 80, BLU, S.p("turn", 0.5, 3.5))
        legend_rb(ctx, 1.0)
        return
    if not S.on("hide"):
        lt = t - S.c0("battle")
        ctx.save(); shake(ctx, t, S.c0("battle") + 0.2, 16, 0.5); shake(ctx, t, S.c0("mori") + 0.3, 12, 0.4)
        clash_plate(ctx, t, lt)
        ctx.restore()
        flash(ctx, t, S.c0("battle"), 0.15, 0.6)
        if S.on("mori"):
            a = S.p("mori", 0.4, 0.6) * (1 - S.p("loss", 0.5, 2.5))
            panel(ctx, 140, 440, 800, 120, a * 0.9)
            cross(ctx, 220, 500, 26, a); text(ctx, "森长可 · 眉心中弹", 280, 500, 46, IVORY, a, "lm", bold=True, serif=True)
        if S.on("ikeda"):
            a = S.p("ikeda", 0.4, 0.6) * (1 - S.p("loss", 0.5, 2.5))
            panel(ctx, 140, 580, 800, 120, a * 0.9)
            cross(ctx, 220, 640, 26, a); text(ctx, "池田恒兴 · 元助父子", 280, 640, 46, IVORY, a, "lm", bold=True, serif=True)
        if S.on("loss"):
            a = S.p("loss", 0.6, 2.0)
            ctx.set_source_rgba(0, 0, 0, 0.55 * a); ctx.paint()
            particles(ctx, W / 2, 800, (t - S.c0("loss")) / 4.0, 260, 420, RED, seed=9, drift=(0, -120), r=7)
            text(ctx, "两万绕后部队", W / 2, 720, 50, IVORY, a, "mm", bold=True, serif=True, halo=8)
            text(ctx, "死的死  散的散", W / 2, 820, 70, RED, a, "mm", bold=True, serif=True, halo=10)
        return
    cam = Cam(S, [(None, (O("小幡城")[0] + 60, O("小幡城")[1] - 40), 0.75)])
    map_base(ctx, "owari", cam, 0.2)
    ctx.save(); cam.apply(ctx)
    z = cam.z
    arrow(ctx, [O("乐田"), Oll(136.985, 35.27), Oll(137.005, 35.235)], S.p("hide", 2.5, 0.5), RED, 60 / z, 1.0)
    arrow(ctx, [Nk, Oll(137.02, 35.195), O("小幡城")], S.p("hide", 2.0, 3.0), BLU, 40 / z, 1.0)
    arrow(ctx, [O("小幡城"), Oll(136.935, 35.25), O("小牧山")], S.p("hide", 2.0, 5.5), BLU, 40 / z, 1.0)
    fortline(ctx, ll(KOMAKI_LINE), 1, BLU, z)
    fortline(ctx, ll(GAKUDEN_LINE), 1, RED, z)
    ctx.restore()
    owari_labels(ctx, cam, 1.0, only=("小牧山", "乐田", "小幡城", "长久手"))
    g = cam.sc(Oll(137.005, 35.235))
    tag(ctx, "秀吉亲率大军", g[0] + 30, g[1] - 70, RED, S.p("hide", 0.5, 1.5))
    if S.on("nogreed"):
        text(ctx, "打完就走", W / 2, 540, 72, BLU, S.p("nogreed", 0.6), "mm", bold=True, serif=True, halo=10)
        text(ctx, "不给对方决战的机会", W / 2, 630, 44, IVORY, S.p("nogreed", 0.6, 1.5), "mm", bold=True, serif=True, halo=8)
    legend_rb(ctx, 1.0)


# ================================================================ s08 mechanism: 知 / 分
def sc_mech(ctx, S):
    t = S.t
    dark_card_bg(ctx)
    if not S.on("sunzi"):
        a = S.p("know", 0.6)
        text(ctx, "知", 270, 560, 200, BLU, a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "家康", 270, 720, 44, IVORY, a, "mm", bold=True)
        text(ctx, "知道对方在哪儿", 270, 790, 34, IVORY, a * S.p("know", 0.6, 1.5), "mm")
        text(ctx, "对方不知道他在哪儿", 270, 845, 34, DIM, a * S.p("know", 0.6, 3.0), "mm")
        b = S.p("divide", 0.6)
        text(ctx, "分", 810, 560, 200, RED, b, "mm", bold=True, serif=True, halo=10)
        text(ctx, "秀吉", 810, 720, 44, IVORY, b, "mm", bold=True)
        # red bar splitting into four segments; blue fist hits one at a time
        sp_ = S.p("divide", 1.5, 2.0)
        for i in range(4):
            x = 600 + i * (90 + 20 * sp_)
            hit = S.p("divide", 0.4, 5.5 + i * 0.9)
            ctx.rectangle(x, 800, 70, 40); ctx.set_source_rgba(*RED, b * (1 - 0.7 * hit)); ctx.fill()
            if hit > 0 and hit < 1:
                burst(ctx, x + 35, 820, t, 40, (1 - hit) * b, FIRE, i)
        text(ctx, "首尾不能相顾 · 一段一段被吃掉", 810, 900, 30, IVORY, b * S.p("divide", 0.6, 4.0), "mm")
        ctx.set_source_rgba(*GOLD, 0.5 * a); ctx.set_line_width(2); ctx.move_to(W / 2, 470); ctx.line_to(W / 2, 960); ctx.stroke()
        return
    if not S.on("total"):
        a = S.span("sunzi", 0.6, "total") if S.on("quote") else S.p("sunzi", 0.6)
        quote_card(ctx, "我專為一，敵分為十，是以十攻其一也。", "我集中成一个拳头，敌人分成十份——我是在用十倍的力量，打它的一份。",
                   "《孫子·虛實》", a, y=820, latin=False, orig_size=54, zh_size=40)
        return
    a = S.p("total", 0.6)
    text(ctx, "总兵力", 270, 520, 44, DIM, a, "mm", bold=True)
    ctx.rectangle(110, 580, 330, 50); ctx.set_source_rgba(*RED, a); ctx.fill()
    ctx.rectangle(110, 650, 110, 50); ctx.set_source_rgba(*BLU, a); ctx.fill()
    text(ctx, "家康是少数", 270, 760, 40, IVORY, a, "mm", bold=True)
    b = S.p("total", 0.6, 2.5)
    text(ctx, "长久手那个上午", 810, 520, 44, GOLD, b, "mm", bold=True)
    ctx.rectangle(650, 580, 140, 50); ctx.set_source_rgba(*RED, b); ctx.fill()
    ctx.rectangle(650, 650, 300, 50); ctx.set_source_rgba(*BLU, b); ctx.fill()
    text(ctx, "家康是多数", 810, 760, 40, BLU, b, "mm", bold=True)


# ================================================================ s09 pivot (region map)
NOBU_CASTLES = [(136.74, 35.335), (136.70, 35.10), (136.62, 35.03), (136.55, 34.88), (136.45, 34.73), (136.60, 34.57)]


def sc_pivot(ctx, S):
    t = S.t
    if not S.on("turn"):
        K = O("小牧山")
        cam = Cam(S, [(None, (K[0] + 60, K[1] + 60), 0.75)])
        map_base(ctx, "owari", cam, 0.25)
        ctx.save(); cam.apply(ctx)
        z = cam.z
        fortline(ctx, ll(KOMAKI_LINE), 1, BLU, z)
        fortline(ctx, ll(GAKUDEN_LINE), 1, RED, z)
        if S.on("ifnot"):
            arrow(ctx, [O("乐田"), Oll(136.935, 35.31), Oll(136.918, 35.298)], S.p("ifnot", 1.5, 2.5), RED, 70 / z, 1 - S.p("no", 0.4))
        ctx.restore()
        owari_labels(ctx, cam, 1.0, only=("小牧山", "乐田", "长久手"))
        k = cam.sc(K)
        if not S.on("ifnot"):
            pulse_ring(ctx, k[0], k[1], t, BLU, 50, S.p("fame", 0.6))
            tag(ctx, "家康 · 名声大振", k[0], k[1] + 110, BLU, S.p("fame", 0.6, 1.0))
        if S.on("ifnot") and not S.on("see"):
            text(ctx, "回去硬拼？", W / 2, 540, 70, IVORY, S.span("ifnot", 0.5, "see"), "mm", bold=True, serif=True, halo=10)
        if S.on("no") and not S.on("see"):
            cross(ctx, k[0] + 40, k[1] - 40, 70, S.p("no", 0.3), RED, 16)
        if S.on("see"):
            a = S.p("see", 0.6)
            pulse_ring(ctx, k[0], k[1], t, BLU, 70, a)
            text(ctx, "这是对方最擅长的地方", W / 2, 540, 56, BLU, a * S.p("see", 0.6, 1.5), "mm", bold=True, serif=True, halo=10)
        legend_rb(ctx, 1.0)
        return
    Pr = P("region")
    c1 = Rll(136.8, 35.05)
    c1 = Rll(136.45, 34.95)
    cam = Cam(S, [(None, (R("小牧山")[0], R("小牧山")[1]), 1.6), ("turn", (c1[0], c1[1]), 0.56, 3.0)])
    map_base(ctx, "region", cam, 0.15)
    ctx.save(); cam.apply(ctx)
    z = cam.z
    # Nobukatsu's lands (Owari west + Ise) shade
    na = S.p("nominal", 1.0)
    for (lo, la) in ((136.75, 35.25), (136.65, 35.05), (136.55, 34.85), (136.45, 34.65), (136.20, 34.75)):
        x, y = Rll(lo, la)
        g = cairo.RadialGradient(x, y, 0, x, y, 120)
        g.add_color_stop_rgba(0, *BLU, 0.35 * na); g.add_color_stop_rgba(1, *BLU, 0)
        ctx.set_source(g); ctx.arc(x, y, 120, 0, 6.3); ctx.fill()
    arrow(ctx, [R("小牧山"), Rll(136.80, 35.30), R("竹鼻城")], S.p("turn", 2.0, 2.5), RED, 46 / z, 1.0)
    arrow(ctx, [Rll(136.80, 35.25), Rll(136.72, 35.12), Rll(136.62, 34.95)], S.p("turn", 2.0, 4.0), RED, 46 / z, 1.0)
    arrow(ctx, [R("大坂"), Rll(135.9, 34.75), R("伊贺")], S.p("ise", 2.0, 0.5), RED, 40 / z, 1.0)
    ctx.restore()
    for nm, side in (("大坂", -1), ("长岛城", 1), ("伊贺", -1), ("伊势", 1), ("小牧山", 1), ("冈崎", 1), ("滨松", 1), ("竹鼻城", -1)):
        x, y = cam.sc(R(nm))
        draw_place(ctx, nm, x, y, 1.0, 32, IVORY, side, nm in ("大坂", "小牧山"), nm in ("大坂", "长岛城", "竹鼻城"))
    if S.on("nominal"):
        x, y = cam.sc(Rll(136.55, 34.95))
        tag(ctx, "织田信雄的领地", x, y, BLU, S.span("nominal", 0.5, "takegahana"))
    if S.on("takegahana"):
        x, y = cam.sc(R("竹鼻城"))
        a = S.p("takegahana", 0.6, 4.0)
        for k in range(3):
            ph = ((t * 0.4 + k / 3) % 1.0)
            ctx.arc(x, y, 30 + ph * 70, 0, 6.3); ctx.set_source_rgba(0.45, 0.70, 0.95, a * (1 - ph)); ctx.set_line_width(5); ctx.stroke()
        tag(ctx, "竹鼻城 · 水攻", x + 10, y - 80, (0.45, 0.70, 0.95), a)
    if S.on("ise") or S.on("takegahana"):
        for i, (lo, la) in enumerate(NOBU_CASTLES):
            x, y = cam.sc(Rll(lo, la))
            k = S.p("takegahana", 0.4, 1.0 + i * 0.25) if i == 0 else S.p("ise", 0.4, 0.3 + i * 0.6)
            col = tuple(lerp(BLU[j], RED[j], k) for j in range(3))
            ctx.rectangle(x - 12, y - 12, 24, 24); ctx.set_source_rgba(0, 0, 0, 0.7); ctx.fill()
            ctx.rectangle(x - 9, y - 9, 18, 18); ctx.set_source_rgba(*col, 1); ctx.fill()
    if S.on("allies"):
        a = S.p("allies", 0.6)
        panel(ctx, 70, 440, 940, 330, a)
        text(ctx, "家康的盟友 · 各自被拖住", W / 2, 500, 38, GOLD, a, "mm", bold=True, serif=True)
        text(ctx, "佐佐成政", 250, 590, 40, BLU, a * S.p("allies", 0.5, 1.5), "mm", bold=True)
        text(ctx, "被前田利家挡在末森城", 640, 590, 34, IVORY, a * S.p("allies", 0.5, 1.5), "mm")
        text(ctx, "北条", 250, 680, 40, BLU, a * S.p("allies", 0.5, 5.0), "mm", bold=True)
        text(ctx, "被佐竹牵制在关东", 640, 680, 34, IVORY, a * S.p("allies", 0.5, 5.0), "mm")
    legend_rb(ctx, 1.0)


# ================================================================ s10 alliance weak link
def chain(ctx, cx, cy, a, crack=0.0, t=0.0):
    for i, (dx, col, lab) in enumerate(((-150, BLU, "德川家康"), (150, BLU_D, "织田信雄"))):
        x = cx + dx + (crack * 60 if i else -crack * 10)
        y = cy + (crack * 40 if i else 0)
        ctx.new_path(); ctx.save(); ctx.translate(x, y)
        ctx.scale(1.0, 0.62)
        ctx.arc(0, 0, 150, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*col, a); ctx.set_line_width(36 if i == 0 else 20); ctx.stroke()
        text(ctx, lab, x, y + 140, 40, IVORY, a, "mm", bold=True)
    if crack > 0:
        x = cx + 150 + 60 * crack - 140
        ctx.new_path(); ctx.set_source_rgba(1, 0.4, 0.3, a * crack); ctx.set_line_width(6)
        ctx.move_to(x, cy - 80); ctx.line_to(x + 20, cy - 20); ctx.line_to(x - 10, cy + 20); ctx.line_to(x + 15, cy + 80); ctx.stroke()


def sc_alliance(ctx, S):
    t = S.t
    if not S.on("weak"):
        c = Rll(136.95, 34.95)
        cam = Cam(S, [(None, c, 0.95)])
        map_base(ctx, "region", cam, 0.15)
        a = S.p("land", 0.6)
        for i, (lo, la) in enumerate(((136.74, 35.30), (136.65, 35.08), (136.55, 34.85), (136.45, 34.68))):
            x, y = cam.sc(Rll(lo, la))
            burst(ctx, x, y, t, 46, a, FIRE, i)
        for i, (lo, la) in enumerate(((137.16, 34.95), (137.73, 34.71))):
            x, y = cam.sc(Rll(lo, la))
            g = cairo.RadialGradient(x, y, 0, x, y, 110)
            g.add_color_stop_rgba(0, *BLU, 0.45 * S.p("land", 0.6, 4.5)); g.add_color_stop_rgba(1, *BLU, 0)
            ctx.set_source(g); ctx.arc(x, y, 110, 0, 6.3); ctx.fill()
        for nm, side in (("伊势", -1), ("长岛城", -1), ("冈崎", 1), ("滨松", 1), ("小牧山", 1)):
            x, y = cam.sc(R(nm))
            draw_place(ctx, nm, x, y, 1.0, 32, IVORY, side)
        x, y = cam.sc(Rll(136.55, 35.0))
        tag(ctx, "信雄：烧的是自家田地", x, y - 180, BLU_D, a)
        x, y = cam.sc(Rll(137.45, 34.85))
        tag(ctx, "家康：毫发无损", x, y - 130, BLU, S.p("land", 0.6, 4.5))
        legend_rb(ctx, 1.0)
        return
    dark_card_bg(ctx)
    if not S.on("nov"):
        a = S.p("weak", 0.6)
        text(ctx, "联盟的薄弱环节", W / 2, 500, 60, GOLD, a, "mm", bold=True, serif=True)
        chain(ctx, W / 2, 780, a, S.p("weak", 1.0, 4.0), t)
        text(ctx, "本钱更少 · 损失更直接 → 先撑不住", W / 2, 1060, 40, IVORY, a * S.p("weak", 0.6, 4.0), "mm", bold=True)
        return
    if not S.on("ogi"):
        a = S.p("nov", 0.6) * (1 - S.p("noreason", 0.5))
        text(ctx, "1584 年 11 月", W / 2, 490, 44, GOLD, a, "mm", bold=True)
        text(ctx, "信雄 单独讲和", W / 2, 580, 70, IVORY, a, "mm", bold=True, serif=True, halo=8)
        items = ["交出伊贺", "割让伊势半国", "送出人质"]
        for i, s in enumerate(items):
            k = a * S.p("nov", 0.5, 3.0 + i * 1.3)
            tag(ctx, s, W / 2, 700 + i * 90, RED, k, 38)
        if S.on("noreason"):
            b = S.p("noreason", 0.6)
            ctx.set_source_rgba(0, 0, 0, 0.6 * b); ctx.paint()
            text(ctx, "家康的出兵名义", W / 2, 640, 60, BLU, b, "mm", bold=True, serif=True)
            ctx.set_source_rgba(*RED, b * S.p("noreason", 0.4, 1.5)); ctx.set_line_width(8)
            ctx.move_to(260, 645); ctx.line_to(820, 645); ctx.stroke()
            text(ctx, "替织田家主持公道 → 与天下作对", W / 2, 780, 40, IVORY, b * S.p("noreason", 0.6, 4.0), "mm", bold=True)
        return
    c = Rll(136.65, 34.85)
    cam = Cam(S, [(None, c, 0.47)])
    map_base(ctx, "region", cam, 0.2 + 0.3 * S.p("hostage", 0.6))
    ctx.save(); cam.apply(ctx)
    z = cam.z
    arrow(ctx, [R("滨松"), Rll(136.9, 34.75), Rll(136.2, 34.62), R("大坂")], S.p("ogi", 3.0, 1.5), BLU, 26 / z, 1.0, glow=False)
    ctx.restore()
    for nm, side in (("大坂", -1), ("滨松", 1), ("冈崎", 1)):
        x, y = cam.sc(R(nm))
        draw_place(ctx, nm, x, y, 1.0, 32, IVORY, side, nm == "大坂", nm == "大坂")
    o = cam.sc(R("大坂"))
    tag(ctx, "1584.12 于义丸（结城秀康）", o[0] + 150, o[1] + 110, BLU, S.p("ogi", 0.6, 3.0))
    if S.on("hostage"):
        a = S.p("hostage", 0.6)
        panel(ctx, 110, 460, 860, 300, a)
        text(ctx, "德川家说", 300, 540, 36, DIM, a, "mm")
        text(ctx, "养子", 300, 640, 80, BLU, a, "mm", bold=True, serif=True)
        text(ctx, "秀吉这边看", 780, 540, 36, DIM, a * S.p("hostage", 0.6, 1.8), "mm")
        text(ctx, "人质", 780, 640, 80, RED, a * S.p("hostage", 0.6, 1.8), "mm", bold=True, serif=True)
    legend_rb(ctx, 1.0)


# ================================================================ s11 Clausewitz
def sc_clause(ctx, S):
    t = S.t
    dark_card_bg(ctx)
    ctx.set_source_surface(illus.fog(71, 0.25, (0.5, 0.45, 0.4), 700), -((t * 10) % W), 600); ctx.paint_with_alpha(0.5)
    if not S.on("quote"):
        a = S.p("intro", 0.6)
        text(ctx, "克劳塞维茨", W / 2, 700, 80, IVORY, a, "mm", bold=True, serif=True)
        text(ctx, "Carl von Clausewitz · 1780–1831", W / 2, 800, 34, GOLD, a, "mm", family=LATIN_I, italic=True)
        text(ctx, "普鲁士将军 · 《战争论》", W / 2, 870, 36, DIM, a, "mm")
        return
    if not S.on("means"):
        quote_card(ctx, "Der Krieg ist eine bloße Fortsetzung der Politik mit anderen Mitteln.", "战争只是政治以另一种手段的继续。",
                   "克劳塞维茨《战争论》第一篇第一章第二十四节", S.p("quote", 0.6), y=820, latin=True, orig_size=42, zh_size=52)
        return
    a = S.p("means", 0.6)
    text(ctx, "战斗 = 手段", W / 2, 560, 64, DIM, a, "mm", bold=True, serif=True)
    text(ctx, "政治 = 目的", W / 2, 660, 64, GOLD, a * S.p("means", 0.6, 1.2), "mm", bold=True, serif=True)
    b = S.p("verdict", 0.6)
    panel(ctx, 80, 780, 920, 330, b)
    text(ctx, "家康", 200, 870, 50, BLU, b, "mm", bold=True, serif=True)
    text(ctx, "赢下一场战斗", 590, 870, 48, IVORY, b, "mm", bold=True)
    text(ctx, "秀吉", 200, 1010, 50, RED, b * S.p("verdict", 0.6, 2.5), "mm", bold=True, serif=True)
    text(ctx, "让对方没理由再打", 590, 1010, 48, IVORY, b * S.p("verdict", 0.6, 2.5), "mm", bold=True)


# ================================================================ s12 aftermath
def sc_aftermath(ctx, S):
    t = S.t
    if not S.on("same"):
        c = Nll(136.5, 35.4)
        cam = Cam(S, [(None, c, 0.52), ("1586", Nll(136.6, 35.0), 0.68, 2.5)])
        map_base(ctx, "nation", cam, 0.1)
        br = {"纪州": S.p("1585", 0.6, 1.5), "土佐": S.p("1585", 0.6, 2.5), "越中": S.p("1585", 0.6, 3.5)}
        ctx.save(); cam.apply(ctx)
        nation_nets(ctx, S, cam, 1.0, 1.0, 1.0, broken=br, t=t)
        if S.on("1586"):
            arrow(ctx, [N("滨松"), Nll(136.8, 34.85), Nll(136.0, 34.75), N("大坂")], S.p("1586", 3.0, 1.0), BLU, 40 / cam.z, 1.0)
        ctx.restore()
        nation_ally_labels(ctx, S, cam, 1.0, 1.0, br)
        for nm, yr, dx in (("纪州", "1585.4", -1), ("土佐", "1585.8", -1), ("越中", "1585.8", 1)):
            x, y = cam.sc(N(nm))
            tag(ctx, yr + " 平定", x + dx * 120, y + 60, RED, br[nm] * (1 - S.p("kampaku", 0.5)), 26)
        o = cam.sc(N("大坂"))
        draw_place(ctx, "大坂", o[0], o[1], 1.0, 34, RED, -1, True, True)
        if S.on("kampaku") and not S.on("1586"):
            a = S.span("kampaku", 0.5, "1586")
            panel(ctx, 90, 440, 900, 340, a)
            rows = [("1585.7", "秀吉任关白"), ("1586.5", "妹妹朝日姬嫁给家康"), ("1586.10", "母亲大政所到冈崎为质")]
            for i, (d, s) in enumerate(rows):
                k = a * S.p("kampaku", 0.5, 0.4 + i * 2.0)
                text(ctx, d, 260, 520 + i * 90, 40, GOLD, k, "mm", bold=True)
                text(ctx, s, 380, 520 + i * 90, 40, IVORY, k, "lm", bold=True)
        if S.on("1586"):
            tag(ctx, "1586.10 家康上洛 · 大坂城称臣", W / 2, 1150, BLU, S.p("1586", 0.6, 3.0), 34)
        legend_rb(ctx, 1.0, 1240)
        return
    # Osaka at dusk
    paint_surface(ctx, illus.sky("dusk"), 0, 0)
    hills(ctx, 1160, 120, (0.07, 0.05, 0.05), seed=21, freq=0.003)
    castle(ctx, W / 2, 1150, 1.25, 1.0, lit=0.6 * S.p("same", 1.0))
    hills(ctx, 1450, 120, (0.03, 0.025, 0.025), seed=22, freq=0.004)
    a = S.p("same", 0.8, 0.5)
    text(ctx, "战场上没被打败的人", W / 2, 520, 54, IVORY, a, "mm", bold=True, serif=True, halo=10)
    text(ctx, "在谈判桌上低了头", W / 2, 610, 64, GOLD, a * S.p("same", 0.6, 2.0), "mm", bold=True, serif=True, halo=10)


# ================================================================ s13 sources
def book(ctx, x, y, w, h, title, sub, a, col=(0.45, 0.32, 0.20)):
    if a <= 0:
        return
    rrect(ctx, x, y, w, h, 8); ctx.set_source_rgba(*col, a); ctx.fill_preserve()
    ctx.set_source_rgba(*GOLD, 0.7 * a); ctx.set_line_width(2); ctx.stroke()
    ctx.rectangle(x + 18, y + 18, 6, h - 36); ctx.set_source_rgba(*GOLD, 0.5 * a); ctx.fill()
    ly = y + 70
    for L in title:
        text(ctx, L, x + w / 2 + 8, ly, 34, IVORY, a, "mm", bold=True, serif=True); ly += 48
    text(ctx, sub, x + w / 2 + 8, y + h - 50, 24, GOLD, a, "mm")


def go_board(ctx, x0, y0, size, a, t, S):
    n = 13
    cell = size / (n - 1)
    rrect(ctx, x0 - 30, y0 - 30, size + 60, size + 60, 10); ctx.set_source_rgba(0.55, 0.42, 0.24, a); ctx.fill()
    ctx.set_line_width(1.5); ctx.set_source_rgba(0.1, 0.08, 0.05, a)
    for i in range(n):
        ctx.move_to(x0, y0 + i * cell); ctx.line_to(x0 + size, y0 + i * cell)
        ctx.move_to(x0 + i * cell, y0); ctx.line_to(x0 + i * cell, y0 + size)
    ctx.stroke()
    rng = np.random.default_rng(3)
    k_all = S.p("corner", 3.0, 3.0)
    stones = []
    for i in range(n):
        for j in range(n):
            if i <= 2 and j >= n - 3:
                stones.append((i, j, BLU, 0.0))
            elif rng.random() < 0.45 and not (i <= 3 and j >= n - 4):
                stones.append((i, j, RED, rng.uniform(0, 1)))
    for (i, j, col, d) in stones:
        k = S.p("corner", 0.4, 0.3) if col == BLU else clamp((k_all - d * 0.8) / 0.2)
        if k <= 0:
            continue
        ctx.arc(x0 + i * cell, y0 + j * cell, cell * 0.44, 0, 6.3); ctx.set_source_rgba(*col, a * k); ctx.fill()


def sc_sources(ctx, S):
    t = S.t
    dark_card_bg(ctx)
    if not S.on("d1"):
        a = S.p("why", 0.6)
        text(ctx, "为什么只记得「家康大胜」？", W / 2, 520, 50, IVORY, a, "mm", bold=True, serif=True)
        b = S.p("tokugawa", 0.6)
        text(ctx, "写历史的，是德川家", W / 2, 640, 60, BLU, b, "mm", bold=True, serif=True, halo=8)
        c = S.p("edo", 0.6)
        if c > 0:
            # scroll
            rrect(ctx, 140, 740, 800, 360, 12); ctx.set_source_rgba(0.80, 0.72, 0.56, c); ctx.fill()
            for k in (140, 920):
                rrect(ctx, k - 14, 724, 34, 392, 10); ctx.set_source_rgba(0.30, 0.18, 0.10, c); ctx.fill()
            text(ctx, "神君", W / 2, 860, 110, (0.55, 0.12, 0.08), c, "mm", bold=True, serif=True)
            text(ctx, "长久手 以少胜多", W / 2, 990, 50, (0.20, 0.14, 0.08), c * S.p("edo", 0.6, 2.0), "mm", bold=True, serif=True)
            text(ctx, "如何收场 …… 一笔带过", W / 2, 1060, 34, (0.35, 0.28, 0.20), c * S.p("edo", 0.6, 7.0), "mm")
            tag(ctx, "江户时代 · 德川一方史书与后世军记", W / 2, 1180, GOLD, c * S.p("edo", 0.6, 1.0), 28)
        return
    if not S.on("fujita"):
        items = [("d1", "折扣一", "立场", "多出德川一方 · 胜仗被放大"), ("d2", "折扣二", "数字", "十万对三万 · 通说，各家差得远"),
                 ("d3", "折扣三", "说法", "谁的计策？养子还是人质？")]
        for i, (cue, h, k_, s) in enumerate(items):
            a = S.p(cue, 0.6)
            y = 560 + i * 230
            panel(ctx, 90, y - 95, 900, 190, a)
            text(ctx, h, 150, y - 40, 30, GOLD, a, "lm", bold=True)
            text(ctx, k_, 150, y + 25, 64, IVORY, a, "lm", bold=True, serif=True)
            text(ctx, s, 960, y + 25, 34, IVORY, a, "rm")
        return
    if not S.on("corner"):
        a = S.p("fujita", 0.6)
        text(ctx, "近年学界：放回全国的棋盘", W / 2, 500, 46, GOLD, a, "mm", bold=True, serif=True)
        book(ctx, 120, 580, 400, 520, ["小牧·长久手", "之战的构造"], "战场论 上", a * S.p("fujita", 0.5, 1.0))
        book(ctx, 560, 580, 400, 520, ["近世成立期的", "大规模战争"], "战场论 下", a * S.p("fujita", 0.5, 1.6), (0.30, 0.30, 0.38))
        text(ctx, "藤田达生 编 · 岩田书院 2006", W / 2, 1160, 32, IVORY, a * S.p("fujita", 0.5, 2.0), "mm")
        return
    a = S.p("corner", 0.6)
    go_board(ctx, 220, 540, 640, a, t, S)
    text(ctx, "家康 · 赢了一个角", 330, 470, 36, BLU, a * S.p("corner", 0.5, 1.5), "mm", bold=True)
    text(ctx, "秀吉 · 收了全盘的官", W / 2, 1255, 44, RED, a * S.p("corner", 0.5, 5.0), "mm", bold=True, serif=True, halo=8)


# ================================================================ s14 ending
def sc_ending(ctx, S):
    t = S.t
    paint_surface(ctx, illus.sky("dusk"), 0, 0)
    hills(ctx, 1160, 120, (0.07, 0.05, 0.05), seed=21, freq=0.003)
    castle(ctx, W / 2, 1150, 1.25, 1.0, lit=0.5)
    hills(ctx, 1450, 120, (0.03, 0.025, 0.025), seed=22, freq=0.004)
    ctx.set_source_rgba(0, 0, 0, 0.55 * S.p("quote", 0.6) * (1 - S.p("next", 1.0))); ctx.paint()
    if S.on("sunzi") and not S.on("quote"):
        text(ctx, "《孫子·謀攻》", W / 2, 640, 60, GOLD, S.p("sunzi", 0.6), "mm", bold=True, serif=True, halo=10)
    if S.on("quote") and not S.on("map"):
        a = S.p("quote", 0.6) * (1 - S.p("map", 0.5))
        quote_card(ctx, "上兵伐謀，其次伐交，其次伐兵，其下攻城。", "最好的是挫败对方的谋划，其次是瓦解对方的联盟，再次是野战，最下等是攻城。",
                   "《孫子·謀攻》", a, y=800, latin=False, orig_size=52, zh_size=40)
    if S.on("map") and not S.on("work"):
        a = S.p("map", 0.6) * (1 - S.p("work", 0.5))
        panel(ctx, 110, 430, 860, 640, a)
        rungs = [("伐谋", ""), ("伐交", "秀吉"), ("伐兵", "家康"), ("攻城", "（秀吉没有去攻小牧山）")]
        for i, (r_, who) in enumerate(rungs):
            y = 520 + i * 140
            text(ctx, r_, 300, y, 64, IVORY if i < 3 else DIM, a, "mm", bold=True, serif=True)
            col = RED if who == "秀吉" else BLU if who == "家康" else DIM
            k = a * (S.p("map", 0.5, 4.5) if who == "秀吉" else S.p("map", 0.5, 1.0) if who == "家康" else S.p("map", 0.5, 7.0))
            text(ctx, who, 460, y, 46 if i < 3 else 30, col, k, "lm", bold=True)
            if i < 3:
                ctx.set_source_rgba(*GOLD, 0.3 * a); ctx.set_line_width(2); ctx.move_to(200, y + 70); ctx.line_to(880, y + 70); ctx.stroke()
    if S.on("work") and not S.on("next"):
        a = S.p("work", 0.6) * (1 - S.p("next", 0.5))
        card_text(ctx, ["输掉一场正面对决不可怕"], 560, a, 52, IVORY)
        card_text(ctx, ["可怕的是", "还在对方最擅长的地方", "继续硬拼"], 700, a * S.p("work", 0.6, 3.0), 58, GOLD)
    if S.on("next"):
        a = S.p("next", 0.8)
        text(ctx, "天下只剩", W / 2, 560, 50, IVORY, a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "关东 · 北条", W / 2, 660, 80, GOLD, a * S.p("next", 0.6, 1.5), "mm", bold=True, serif=True, halo=12)
        text(ctx, "下一回 · 一场几乎不用打的仗", W / 2, 790, 44, IVORY, a * S.p("next", 0.6, 4.0), "mm", bold=True, halo=8)


RENDERERS = {
    "hook": sc_hook, "hookmap": sc_hookmap, "nation": sc_nation, "owari": sc_owari, "forest": sc_forest, "fan": sc_fan,
    "clash": sc_clash, "mech": sc_mech, "pivot": sc_pivot, "alliance": sc_alliance, "clause": sc_clause,
    "aftermath": sc_aftermath, "sources": sc_sources, "ending": sc_ending,
}
BADGE = {"hook": "ill", "hookmap": "map", "nation": "map", "owari": "map", "forest": "mix", "fan": "mix", "clash": "mix",
         "mech": "card", "pivot": "map", "alliance": "map", "clause": "card", "aftermath": "map", "sources": "card", "ending": "ill"}
