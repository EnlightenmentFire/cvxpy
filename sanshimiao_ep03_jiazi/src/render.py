# -*- coding: utf-8 -*-
"""三十秒一问 03《六十甲子》— single-scene renderer (pycairo).

One picture for the whole film: two meshing gold gears on an ink-blue ground.
Left gear: 10 teeth, 天干.  Right gear: 12 teeth, 地支.  A fixed pointer above each gear;
the characters under the two pointers form the current pair shown in the box below.

Mechanics (state variable s = number of steps taken, s=0 -> 甲子, counter 1):
  left gear turns clockwise 36 deg per step, right gear counter-clockwise 30 deg per step.
  Pitch radii 190 / 228 px share module 19 px/tooth, so the rims move the same arc per step
  and the teeth stay meshed.  Pair shown = GAN[n%10] + ZHI[n%12], counter = n%60 + 1.

Usage:
  python render.py still  timeline.json  t_seconds  out.png
  python render.py video  timeline.json  out.mp4  [audio.wav]
"""
import json
import math
import subprocess
import sys

import cairo
import numpy as np

W, H = 1080, 1920
FPS = 30
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

SERIF = "Noto Serif CJK SC"          # with FONT_WEIGHT_BOLD -> NotoSerifCJKsc-Bold
SERIF_BLACK = "Noto Serif CJK SC Black"
SANS_BLACK = "Noto Sans CJK SC Black"
SANS = "Noto Sans CJK SC"            # Bold
MONO = "JetBrains Mono ExtraBold"

YELLOW = (1.0, 0.831, 0.0)           # #FFD400
WHITE = (1, 1, 1)
GOLD = (0.906, 0.725, 0.306)         # #E7B94E
GOLD_HI = (1.0, 0.91, 0.64)
GOLD_LO = (0.54, 0.37, 0.08)
INK = (0.035, 0.07, 0.15)
RED = (0.898, 0.282, 0.302)

# ---------------- layout ----------------
MOD = 19.0
R1, N1 = 190.0, 10                   # 天干
R2, N2 = 228.0, 12                   # 地支
ADD, DED = 0.55 * 38, 0.75 * 38      # addendum / dedendum (module 38 in diameter terms)
CY = 870.0
SPAN = (R1 + ADD) + (R1 + R2) + (R2 + ADD)
CX1 = (W - SPAN) / 2 + R1 + ADD
CX2 = CX1 + R1 + R2
BOX = (230, 1192, 620, 160)          # x, y, w, h
TAG_Y = 1372
CHOU_Y = 1450
CAP_Y = 336                          # caption centre line


def ease_out_back(x, k=1.25):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, t0, d):
    """0 before t0, 1 after t0+d, smooth between."""
    if d <= 0:
        return 1.0 if t >= t0 else 0.0
    return smooth((t - t0) / d)


# ---------------- timeline helpers ----------------
class TL:
    def __init__(self, d):
        self.d = d
        self.steps = d["step_times"]          # step k (1..60) begins at steps[k-1]
        self.lines = {l["id"]: l for l in d["lines"]}
        self.dur = d["duration"]

    def s_at(self, t):
        st = self.steps
        k = 0
        while k < len(st) and st[k] <= t:
            k += 1
        if k == 0:
            return 0.0
        t0 = st[k - 1]
        gap = (st[k] - t0) if k < len(st) else 10.0
        if k == len(st):                   # the final click
            return (k - 1) + ease_out_back((t - t0) / 0.22, 1.6)
        if gap < 0.14:                     # continuous spin
            return (k - 1) + (t - t0) / gap
        d = min(0.2, gap * 0.8)
        return (k - 1) + ease_out_back((t - t0) / d, 1.25)

    def step_index_at(self, t):
        """number of completed clicks (for the readout): click k counts once it has started 60%."""
        st = self.steps
        n = 0
        for k, tk in enumerate(st):
            gap = (st[k + 1] - tk) if k + 1 < len(st) else 0.2
            d = min(0.2, gap * 0.8) if gap >= 0.14 else gap
            if t >= tk + 0.35 * d:
                n = k + 1
        return n

    def ev(self, name, default=None):
        return self.d["events"].get(name, default)


# ---------------- primitives ----------------
def font(ctx, fam, size, bold=False):
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def text_center(ctx, s, x, y, ink=True):
    """move to a point so that s is centred on (x, y). ink=True centres the ink box, else baseline-ish."""
    e = ctx.text_extents(s)
    if ink:
        ctx.move_to(x - e.x_bearing - e.width / 2, y - e.y_bearing - e.height / 2)
    else:
        fe = ctx.font_extents()
        ctx.move_to(x - e.x_advance / 2, y + (fe[0] - fe[1]) / 2)
    return e


def rounded_rect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def rich_line(ctx, segs, cx, cy, size, fam=SANS_BLACK, stroke=9.0, alpha=1.0, scale=1.0):
    """segs: [(text, rgb, size_mult)] centred at (cx, cy) baseline-centred; black outline."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    widths = []
    for txt, col, mult in segs:
        font(ctx, fam, size * mult)
        widths.append(ctx.text_extents(txt).x_advance)
    total = sum(widths)
    font(ctx, fam, size)
    asc, desc = ctx.font_extents()[0], ctx.font_extents()[1]
    base = (asc - desc) / 2 * 0.92
    x = -total / 2
    ctx.new_path()
    for (txt, col, mult), wdt in zip(segs, widths):
        font(ctx, fam, size * mult)
        ctx.move_to(x, base)
        ctx.text_path(txt)
        x += wdt
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(0, 0, 0, 0.92 * alpha)
    ctx.set_line_width(stroke * 2)
    ctx.stroke()
    x = -total / 2
    for (txt, col, mult), wdt in zip(segs, widths):
        font(ctx, fam, size * mult)
        ctx.move_to(x, base)
        ctx.text_path(txt)
        ctx.set_source_rgba(*col, alpha)
        ctx.fill()
        x += wdt
    ctx.restore()
    return total * scale


# ---------------- gear ----------------
def gear_path(ctx, cx, cy, R, N, rot):
    """tooth outline; rot = rotation (rad, clockwise on screen). Tooth centres at rot + j*2pi/N."""
    Ra, Rr = R + ADD, R - DED
    P = 2 * math.pi / N
    hw_t, hw_r = 0.17 * P, 0.31 * P
    M = 64 * N
    ctx.new_path()
    for i in range(M + 1):
        a = i * 2 * math.pi / M
        phi = ((a - rot) / P + 0.5) % 1.0 - 0.5          # in tooth pitches, centred on a tooth
        phi = abs(phi) * P
        if phi <= hw_t:
            r = Ra
        elif phi >= hw_r:
            r = Rr
        else:
            r = Ra + (Rr - Ra) * smooth((phi - hw_t) / (hw_r - hw_t))
        x, y = cx + r * math.sin(a), cy - r * math.cos(a)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()


def gold_grad(cx, cy, R, flash=0.0):
    g = cairo.LinearGradient(cx - R, cy - R, cx + R, cy + R)
    f = flash
    def mix(c):
        return tuple(min(1.0, v + (1 - v) * f) for v in c)
    g.add_color_stop_rgb(0.0, *mix(GOLD_HI))
    g.add_color_stop_rgb(0.35, *mix(GOLD))
    g.add_color_stop_rgb(0.75, *mix((0.78, 0.57, 0.18)))
    g.add_color_stop_rgb(1.0, *mix(GOLD_LO))
    return g


def draw_gear(ctx, cx, cy, R, N, labels, s_ang, sign, t, top_idx, flash=0.0, label="", sub="",
              mark=None, sweep=0.0):
    """labels placed so label k sits at angle sign*k*P - sign*s_ang ... (see module doc)."""
    P = 2 * math.pi / N
    rot = -sign * s_ang                    # sign=-1 for left (labels CCW, gear CW): rot=+s_ang
    # body
    gear_path(ctx, cx, cy, R, N, rot)
    ctx.set_source(gold_grad(cx, cy, R + ADD, flash))
    ctx.fill_preserve()
    ctx.set_source_rgba(0.30, 0.19, 0.03, 0.9)
    ctx.set_line_width(2.4)
    ctx.stroke()
    # light sweep (screen-space band) clipped to the gear
    if sweep > 0:
        ctx.save()
        gear_path(ctx, cx, cy, R, N, rot)
        ctx.clip()
        band = cairo.LinearGradient(cx - R * 1.6, cy - R * 1.6, cx + R * 1.6, cy + R * 1.6)
        p = (t * 0.22) % 1.6 - 0.3
        for o, a in ((p - 0.12, 0), (p, 0.33 * sweep), (p + 0.12, 0)):
            band.add_color_stop_rgba(min(max(o, 0), 1), 1, 0.97, 0.85, a)
        ctx.set_source(band)
        ctx.set_operator(cairo.OPERATOR_SCREEN)
        ctx.paint()
        ctx.restore()
    # label ring
    ro, ri = R - DED - 7, R - DED - 78
    ctx.new_path()
    ctx.arc(cx, cy, ro, 0, 2 * math.pi)
    ctx.arc_negative(cx, cy, ri, 2 * math.pi, 0)
    ctx.set_source_rgb(0.055, 0.09, 0.17)
    ctx.fill()
    for rr, a in ((ro, 0.85), (ri, 0.85)):
        ctx.arc(cx, cy, rr, 0, 2 * math.pi)
        ctx.set_source_rgba(0.35, 0.24, 0.06, a)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.arc(cx, cy, rr + (1.5 if rr == ri else -1.5), 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.9, 0.6, 0.35)
        ctx.set_line_width(1)
        ctx.stroke()
    # radial dividers between labels (rotate with gear)
    for k in range(N):
        a = rot + (k + 0.5) * P
        ctx.move_to(cx + (ri + 6) * math.sin(a), cy - (ri + 6) * math.cos(a))
        ctx.line_to(cx + (ro - 6) * math.sin(a), cy - (ro - 6) * math.cos(a))
    ctx.set_source_rgba(0.85, 0.68, 0.32, 0.25)
    ctx.set_line_width(1.5)
    ctx.stroke()
    # labels
    rc = (ro + ri) / 2
    font(ctx, SERIF, 54, bold=True)
    for k in range(N):
        a = rot + sign * k * P            # left: rot - kP (labels run CCW), right: rot + kP (CW)
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(a)
        ctx.translate(0, -rc)
        hi = (k == top_idx)
        mk = mark.get(k, 0) if mark else 0
        if mk > 0:
            ctx.new_path()
            ctx.arc(0, 0, 35, 0, 2 * math.pi)
            ctx.set_source_rgba(*YELLOW, 0.18 * mk)
            ctx.fill_preserve()
            ctx.set_source_rgba(*YELLOW, 0.95 * mk)
            ctx.set_line_width(3.5)
            ctx.stroke()
        e = text_center(ctx, labels[k], 0, 0)
        ctx.text_path(labels[k])
        if hi:
            ctx.set_source_rgba(1, 0.86, 0.3, 0.55)
            ctx.set_line_width(7)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke_preserve()
            ctx.set_source_rgb(1, 1, 1)
        elif mk > 0:
            ctx.set_source_rgba(1, 0.93 - 0.1 * mk, 0.86 - 0.86 * mk, 0.82 + 0.18 * mk)
        else:
            ctx.set_source_rgba(0.93, 0.91, 0.86, 0.82)
        ctx.fill()
        ctx.restore()
    # hub band: small bolts
    hb = ri - 6
    nb = 5 if N == 10 else 6
    for k in range(nb):
        a = rot + k * 2 * math.pi / nb + P / 2
        bx, by = cx + (hb - 12) * math.sin(a), cy - (hb - 12) * math.cos(a)
        ctx.arc(bx, by, 5.5, 0, 2 * math.pi)
        ctx.set_source_rgba(0.33, 0.21, 0.04, 0.9)
        ctx.fill()
        ctx.arc(bx - 1.2, by - 1.2, 2.2, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.93, 0.7, 0.7)
        ctx.fill()
    # fixed hub cap (does not rotate): name plate
    cap = hb - 30
    g = cairo.RadialGradient(cx - cap * 0.3, cy - cap * 0.3, 2, cx, cy, cap)
    g.add_color_stop_rgb(0, 0.10, 0.16, 0.28)
    g.add_color_stop_rgb(1, 0.035, 0.06, 0.12)
    ctx.arc(cx, cy, cap, 0, 2 * math.pi)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(*GOLD, 0.9)
    ctx.set_line_width(2.5)
    ctx.stroke()
    font(ctx, SANS, 34 if N == 10 else 38, bold=True)
    ctx.set_source_rgb(*GOLD_HI)
    text_center(ctx, label, cx, cy - 15)
    ctx.show_text(label)
    font(ctx, MONO, 26 if N == 10 else 28)
    ctx.set_source_rgba(*GOLD, 0.85)
    text_center(ctx, sub, cx, cy + 26)
    ctx.show_text(sub)


def draw_pointer(ctx, x, y_tip, glow=0.0):
    w, h = 40, 34
    if glow > 0:
        for rad, a in ((40, 0.10), (26, 0.16)):
            g = cairo.RadialGradient(x, y_tip - h / 2, 0, x, y_tip - h / 2, rad + 30 * glow)
            g.add_color_stop_rgba(0, 1, 0.85, 0.3, a * (0.6 + glow))
            g.add_color_stop_rgba(1, 1, 0.85, 0.3, 0)
            ctx.set_source(g)
            ctx.paint()
    ctx.move_to(x, y_tip)
    ctx.line_to(x - w / 2, y_tip - h)
    ctx.line_to(x + w / 2, y_tip - h)
    ctx.close_path()
    g = cairo.LinearGradient(x, y_tip - h, x, y_tip)
    g.add_color_stop_rgb(0, 1, 0.97, 0.88)
    g.add_color_stop_rgb(1, 1, 0.80, 0.25)
    ctx.set_source(g)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.25, 0.15, 0.0, 0.9)
    ctx.set_line_width(2)
    ctx.stroke()
    # mount bar
    rounded_rect(ctx, x - 5, y_tip - h - 26, 10, 28, 4)
    ctx.set_source_rgba(*GOLD, 0.9)
    ctx.fill()


# ---------------- static background ----------------
def make_background():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    g = cairo.RadialGradient(W / 2, CY, 80, W / 2, CY, 1250)
    g.add_color_stop_rgb(0, 0.085, 0.16, 0.29)
    g.add_color_stop_rgb(0.55, 0.045, 0.085, 0.17)
    g.add_color_stop_rgb(1, 0.02, 0.04, 0.09)
    ctx.set_source(g)
    ctx.paint()
    # faint drafting marks: dotted pitch circles and centre line
    ctx.set_line_width(1.2)
    for cx, R in ((CX1, R1), (CX2, R2)):
        for rr in (R + ADD + 26, R + ADD + 60):
            ctx.set_dash([2, 9])
            ctx.arc(cx, CY, rr, 0, 2 * math.pi)
            ctx.set_source_rgba(0.55, 0.68, 0.95, 0.08)
            ctx.stroke()
    ctx.set_dash([])
    ctx.move_to(40, CY)
    ctx.line_to(W - 40, CY)
    ctx.set_source_rgba(0.55, 0.68, 0.95, 0.06)
    ctx.stroke()
    # drop shadows of the gears (blurred discs)
    sh = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    for cx, R in ((CX1, R1), (CX2, R2)):
        d = np.hypot(xx - cx - 10, yy - CY - 18)
        sh = np.maximum(sh, np.clip((R + ADD * 0.6 - d) / 40 + 0.5, 0, 1))
    from scipy.ndimage import gaussian_filter
    sh = gaussian_filter(sh, 18) * 0.55
    arr = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    for c in range(3):
        arr[..., c] = (arr[..., c].astype(np.float32) * (1 - sh)).astype(np.uint8)
    surf.mark_dirty()
    return surf


# ---------------- scene ----------------
class Scene:
    def __init__(self, tl):
        self.tl = tl
        self.bg = make_background()

    def frame(self, t):
        tl = self.tl
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        ctx.set_source_surface(self.bg)
        ctx.paint()

        s = tl.s_at(t)
        n = tl.step_index_at(t)
        T_ANS = tl.steps[-1]
        ans_flash = 0.0
        if t >= T_ANS:
            ans_flash = max(0.0, 1 - (t - T_ANS) / 0.7) ** 1.5 * 0.55
        # per-click micro flash on the pointers
        k_last = max([k for k, tk in enumerate(tl.steps) if tk <= t], default=-1)
        click_glow = 0.0
        if k_last >= 0:
            click_glow = max(0.0, 1 - (t - tl.steps[k_last]) / 0.25)
        idle = 0.5 + 0.5 * math.sin(t * 2 * math.pi / 1.6)    # breathing pointer glow when static
        moving = 1.0 if (tl.steps[0] <= t < tl.steps[-2] + 0.3) else 0.0

        # gears ------------------------------------------------------------
        ang1 = s * 2 * math.pi / N1
        ang2 = s * 2 * math.pi / N2
        top1, top2 = n % 10, n % 12
        # "还差两格" marks on the right gear at 甲戌
        mark = None
        e_cha = tl.ev("cha_on")
        if e_cha is not None and e_cha <= t < tl.ev("cha_off", e_cha + 2.0):
            a = ramp(t, e_cha, 0.25) * (1 - ramp(t, tl.ev("cha_off") - 0.3, 0.3))
            mark = {11: a, 0: a}
        lap_flash = 0.0
        if e_cha is not None and t >= e_cha:
            lap_flash = max(0.0, 1 - (t - e_cha) / 0.6) * 0.35
        sweep = 1.0 - moving * 0.7
        draw_gear(ctx, CX1, CY, R1, N1, GAN, ang1, -1, t, top1, flash=max(ans_flash, lap_flash),
                  label="天干", sub="10", sweep=sweep)
        draw_gear(ctx, CX2, CY, R2, N2, ZHI, ang2, +1, t + 1.3, top2, flash=ans_flash,
                  label="地支", sub="12", mark=mark, sweep=sweep)
        # "还差 2 格" arc on the right gear
        if mark:
            a = mark[11]
            self.cha_arc(ctx, a)
        if lap_flash > 0 or (e_cha is not None and e_cha <= t < tl.ev("cha_off", e_cha + 2)):
            a = ramp(t, e_cha, 0.25) * (1 - ramp(t, tl.ev("cha_off") - 0.3, 0.3))
            self.lap_badge(ctx, a)

        # pointers
        pg = max(click_glow * 0.8, ans_flash * 1.8, 0.25 * idle * (1 - moving))
        draw_pointer(ctx, CX1, CY - R1 - ADD - 8, pg)
        draw_pointer(ctx, CX2, CY - R2 - ADD - 8, pg)

        # box + counter ----------------------------------------------------
        self.combo_box(ctx, t, n, s, click_glow, ans_flash)
        self.years(ctx, t)
        self.tags(ctx, t, n)
        self.captions(ctx, t)
        return surf

    # -- pieces --
    def series_label(self, ctx):
        font(ctx, SANS, 30, bold=True)
        ctx.set_source_rgba(*GOLD, 0.75)
        ctx.move_to(62, 236)
        ctx.show_text("三十秒一问 · 03")

    def cha_arc(self, ctx, a):
        if a <= 0.01:
            return
        # arc outside the right gear from the top (戌) to +60 deg (子), i.e. the two missing steps
        r = R2 + ADD + 30
        a0, a1 = -math.pi / 2 + math.radians(8), -math.pi / 2 + math.radians(60)
        ctx.save()
        ctx.set_line_width(6)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*YELLOW, a)
        ctx.new_path()
        ctx.arc(CX2, CY, r, a0, a0 + (a1 - a0) * a)
        ctx.stroke()
        # arrow head at the end
        ex, ey = CX2 + r * math.cos(a1), CY + r * math.sin(a1)
        if a > 0.95:
            tx, ty = -math.sin(a1), math.cos(a1)       # tangent direction (increasing angle)
            nx, ny = math.cos(a1), math.sin(a1)
            ctx.move_to(ex + tx * 18, ey + ty * 18)
            ctx.line_to(ex - nx * 13, ey - ny * 13)
            ctx.line_to(ex + nx * 13, ey + ny * 13)
            ctx.close_path()
            ctx.fill()
        # label
        rich_line(ctx, [("还差 ", WHITE, 1.0), ("2", YELLOW, 1.25), (" 格", WHITE, 1.0)], CX2 + 178, CY - R2 - ADD - 70, 40,
                  stroke=6, alpha=a)
        ctx.restore()

    def lap_badge(self, ctx, a):
        if a <= 0.01:
            return
        rich_line(ctx, [("转满一圈", WHITE, 1.0)], CX1, CY - R1 - ADD - 96, 40, stroke=6, alpha=a)

    def combo_box(self, ctx, t, n, s, click_glow, ans_flash):
        x, y, w, h = BOX
        # glow
        if ans_flash > 0:
            g = cairo.RadialGradient(x + w / 2, y + h / 2, 40, x + w / 2, y + h / 2, w * 0.75)
            g.add_color_stop_rgba(0, 1, 0.85, 0.3, ans_flash * 0.6)
            g.add_color_stop_rgba(1, 1, 0.85, 0.3, 0)
            ctx.set_source(g)
            ctx.paint()
        rounded_rect(ctx, x, y, w, h, 26)
        ctx.set_source_rgba(0.02, 0.05, 0.11, 0.88)
        ctx.fill_preserve()
        ctx.set_source_rgba(*GOLD, 0.95)
        ctx.set_line_width(3.5)
        ctx.stroke()
        rounded_rect(ctx, x + 7, y + 7, w - 14, h - 14, 20)
        ctx.set_source_rgba(*GOLD, 0.25)
        ctx.set_line_width(1.2)
        ctx.stroke()
        # divider
        dx = x + 360
        ctx.move_to(dx, y + 28)
        ctx.line_to(dx, y + h - 28)
        ctx.set_source_rgba(*GOLD, 0.45)
        ctx.set_line_width(2)
        ctx.stroke()
        # pair
        pair = GAN[n % 10] + ZHI[n % 12]
        font(ctx, SERIF_BLACK, 112)
        cx = x + 180
        cy = y + h / 2
        sc = 1.0 + 0.06 * click_glow
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(sc, sc)
        text_center(ctx, pair, 0, 0)
        ctx.text_path(pair)
        if ans_flash > 0:
            ctx.set_source_rgba(1, 0.86, 0.3, 0.7 * ans_flash / 0.55)
            ctx.set_line_width(10)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.stroke_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        ctx.restore()
        # counter: 第 NN 年
        num = n % 60 + 1
        ccx = dx + (x + w - dx) / 2
        font(ctx, SANS, 30, bold=True)
        ctx.set_source_rgba(*GOLD, 0.9)
        text_center(ctx, "第", ccx - 82, cy + 2)
        ctx.show_text("第")
        text_center(ctx, "年", ccx + 82, cy + 2)
        ctx.show_text("年")
        font(ctx, MONO, 84)
        txt = str(num)
        ctx.set_source_rgb(*(YELLOW if (ans_flash > 0 or num == 60) else (1, 1, 1)))
        e0 = ctx.text_extents("0")
        ctx.move_to(ccx - ctx.text_extents(txt).x_advance / 2, cy + e0.height / 2)
        ctx.show_text(txt)

    def years(self, ctx, t):
        tl = self.tl
        a_on, b_on, off = tl.ev("year_a"), tl.ev("year_b"), tl.ev("year_off")
        if a_on is None or t < a_on or t > off + 0.4:
            return
        fade = 1 - ramp(t, off, 0.35)
        y = BOX[1] - 32
        aa = ramp(t, a_on, 0.18) * fade
        bb = ramp(t, b_on, 0.18) * fade
        size = 44
        if bb > 0:
            segs = [("1984 甲子", (0.93, 0.9, 0.82), 1.0), ("  →  ", GOLD, 1.0), ("2044", YELLOW, 1.0), (" 甲子", (0.93, 0.9, 0.82), 1.0)]
            rich_line(ctx, segs, W / 2, y, size, fam=SANS, stroke=6, alpha=max(aa * (1 - bb), 0) + bb)
        else:
            rich_line(ctx, [("1984 甲子", (0.93, 0.9, 0.82), 1.0)], W / 2, y, size, fam=SANS, stroke=6, alpha=aa)

    def tags(self, ctx, t, n):
        tl = self.tl
        on = tl.ev("tags_on")
        if on is None or t < on:
            return
        off = tl.ev("tags_off")
        fade = 1 - ramp(t, off, 0.4) if off else 1.0
        if fade <= 0:
            return
        names = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
        times = tl.ev("tag_times")
        cw, ch, gap = 132, 58, 14
        x0 = W / 2 - (6 * cw + 5 * gap) / 2
        for i, (nm, tt) in enumerate(zip(names, times)):
            if t < tt:
                continue
            a = ramp(t, tt, 0.18) * fade
            pop = 1 + 0.18 * max(0, 1 - (t - tt) / 0.25)
            newest = (i == len([x for x in times if x <= t]) - 1)
            x = x0 + i * (cw + gap)
            ctx.save()
            ctx.translate(x + cw / 2, TAG_Y + ch / 2 + 16 * (1 - ramp(t, tt, 0.18)))
            ctx.scale(pop, pop)
            rounded_rect(ctx, -cw / 2, -ch / 2, cw, ch, 14)
            ctx.set_source_rgba(0.03, 0.06, 0.13, 0.9 * a)
            ctx.fill_preserve()
            ctx.set_source_rgba(*(YELLOW if newest and off is None or (newest and t < off) else GOLD), 0.9 * a)
            ctx.set_line_width(2.5)
            ctx.stroke()
            font(ctx, SERIF, 40, bold=True)
            ctx.set_source_rgba(1, 1, 1, a)
            text_center(ctx, nm, 0, 0)
            ctx.show_text(nm)
            ctx.restore()
        # 甲丑: grey, floats up, gets crossed out
        c_on = tl.ev("chou_on")
        if c_on is not None and t >= c_on:
            a = ramp(t, c_on, 0.25) * fade
            yoff = 26 * (1 - ease_out_cubic((t - c_on) / 0.5))
            cx, cy = W / 2, CHOU_Y + ch / 2 + yoff
            ctx.save()
            rounded_rect(ctx, cx - cw / 2, cy - ch / 2, cw, ch, 14)
            ctx.set_source_rgba(0.16, 0.18, 0.22, 0.85 * a)
            ctx.fill_preserve()
            ctx.set_dash([7, 6])
            ctx.set_source_rgba(0.55, 0.58, 0.64, 0.9 * a)
            ctx.set_line_width(2.2)
            ctx.stroke()
            ctx.set_dash([])
            font(ctx, SERIF, 40, bold=True)
            ctx.set_source_rgba(0.72, 0.75, 0.80, a)
            text_center(ctx, "甲丑", cx, cy)
            ctx.show_text("甲丑")
            x_on = tl.ev("chou_x")
            if t >= x_on:
                p = ease_out_cubic((t - x_on) / 0.22)
                ctx.set_line_width(5)
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.set_source_rgba(*RED, 0.78 * a)
                L = 58
                ctx.move_to(cx - L, cy - L * 0.62)
                ctx.line_to(cx - L + 2 * L * min(1, p * 2), cy - L * 0.62 + 2 * L * 0.62 * min(1, p * 2))
                ctx.stroke()
                if p > 0.5:
                    q = (p - 0.5) * 2
                    ctx.move_to(cx + L, cy - L * 0.62)
                    ctx.line_to(cx + L - 2 * L * q, cy - L * 0.62 + 2 * L * 0.62 * q)
                    ctx.stroke()
            ctx.restore()

    def captions(self, ctx, t):
        tl = self.tl
        caps = tl.d["captions"]
        cur = None
        for c in caps:
            if c["start"] <= t:
                cur = c
        if cur is None:
            return
        nxt = [c for c in caps if c["start"] > cur["start"]]
        end = nxt[0]["start"] if nxt else 1e9
        a_in = 1.0 if cur["start"] <= 0 else ramp(t, cur["start"], 0.14)
        a_out = 1 - ramp(t, end - 0.08, 0.08)
        a = a_in * a_out
        sc = 0.94 + 0.06 * a_in
        if cur.get("answer"):
            self.answer_caption(ctx, t, cur)
            return
        segs = [(s, YELLOW if hi else WHITE, 1.0) for s, hi in cur["segs"]]
        rich_line(ctx, segs, W / 2, CAP_Y, cur.get("size", 82), stroke=10, alpha=a, scale=sc)

    def answer_caption(self, ctx, t, cur):
        t0 = cur["start"]
        a1 = ramp(t, t0, 0.16)
        sc = 1.0 + 0.12 * (1 - ease_out_back((t - t0) / 0.35, 1.6)) if t - t0 < 0.35 else 1.0
        rich_line(ctx, [("10", WHITE, 1.0), (" 和 ", WHITE, 1.0), ("12", WHITE, 1.0), (" 的", WHITE, 1.0)],
                  W / 2, 262, 96, stroke=10, alpha=a1, scale=sc)
        rich_line(ctx, [("最小公倍数 = ", WHITE, 1.0), ("60", YELLOW, 1.32)], W / 2, 388, 96, stroke=10, alpha=a1, scale=sc)
        t1 = cur.get("small_start", t0 + 1.5)
        a2 = ramp(t, t1, 0.2)
        if a2 > 0:
            rich_line(ctx, [("所以六十年，一个甲子", (0.96, 0.93, 0.86), 1.0)], W / 2, 484, 48, fam=SANS, stroke=7, alpha=a2)


# ---------------- entry points ----------------
def surf_to_rgb(surf):
    a = np.ndarray((H, W, 4), np.uint8, surf.get_data())
    return a[..., [2, 1, 0]].copy()


def frame_blurred(sc, t):
    """Motion blur: average sub-frames over a half-frame shutter centred on t when the gears move fast."""
    tl = sc.tl
    sh = 0.5 / FPS
    ds = abs(tl.s_at(t + sh / 2) - tl.s_at(t - sh / 2)) if t > 0 else 0.0
    nsub = int(min(8, max(1, np.ceil(ds / 0.05))))
    if nsub == 1:
        return surf_to_rgb(sc.frame(t))
    acc = np.zeros((H, W, 3), np.float32)
    for j in range(nsub):
        tj = t - sh / 2 + sh * (j + 0.5) / nsub
        acc += surf_to_rgb(sc.frame(tj))
    return (acc / nsub + 0.5).astype(np.uint8)


def main():
    mode = sys.argv[1]
    tl = TL(json.load(open(sys.argv[2])))
    sc = Scene(tl)
    if mode == "still":
        t = float(sys.argv[3])
        out = sys.argv[4]
        surf = sc.frame(t)
        surf.write_to_png(out)
    elif mode == "video":
        # python render.py video timeline.json out.mp4 [first_frame last_frame_exclusive]
        out = sys.argv[3]
        nfr = int(round(tl.dur * FPS))
        f0, f1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, nfr)
        f1 = min(f1, nfr)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8",
               "-pix_fmt", "yuv444p", "-r", str(FPS), out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(f0, f1):
            p.stdin.write(frame_blurred(sc, i / FPS).tobytes())
            if (i - f0) % 60 == 0:
                print(f"frame {i} ({f0}-{f1})", flush=True)
        p.stdin.close()
        p.wait()


if __name__ == "__main__":
    main()
