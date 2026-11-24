"""Scenes: sections 2–7 and the ending."""
import math

import skia

from gfx import *
from gfx import _hash, _rrect
from icons import *
from scenes_a import (Ctx, camera, gloss_card, label, machine_window, para, slot_center, word_time, MACHINE_SLOT,
                      S1_CARDS, FAC_X, FAC_BOT, FAC_W, FAC_H, SLOT_W, SLOT_H)


# =====================================================================================
# shared: org-chart nodes
# =====================================================================================
NODE_W, NODE_H = 210, 190

KINDS = {
    "director": ("厂长", "director", ""),
    "engineer": ("技术工程师", "engineer", ""),
    "chief": ("车间主任", "chief", "1 人"),
    "maint": ("维修工", "maint", "十来人"),
    "workers": ("生产工人", "worker", "多为女工"),
}


def node(c, x, y, key, s=1.0, a=1.0, dim=0.0, outline=None, rings=0.0, t=0.0, sub=True):
    if a <= 0.003:
        return
    name, kind, subtxt = KINDS[key]
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    w, h = NODE_W, NODE_H
    if rings > 0:
        for k in range(3):
            rr = clamp(rings * 3 - k)
            if rr > 0:
                c.drawRRect(_rrect(-w / 2 - 14 - k * 16, -h / 2 - 14 - k * 16, w + 28 + k * 32, h + 28 + k * 32, 26 + k * 10),
                            paint(INK2, a * rr * (0.55 - k * 0.13), stroke=4 - k))
    fill = mix(CARD, (214, 208, 196), dim)
    c.drawRRect(_rrect(-w / 2 + 5, -h / 2 + 7, w, h, 18), paint(INK, 0.14 * a, blur=5))
    c.drawRRect(_rrect(-w / 2, -h / 2, w, h, 18), paint(fill, a))
    c.drawRRect(_rrect(-w / 2, -h / 2, w, h, 18), paint(outline or mix(INK2, INK4, dim), a, stroke=3 if outline is None else 6))
    if key == "workers":
        for dx, sc_ in ((-46, 0.8), (46, 0.8), (0, 1.0)):
            bust(c, dx, -38 + (0 if sc_ == 1 else 8), 24 * sc_, kind, a, dim)
    else:
        bust(c, 0, -38, 26, kind, a, dim)
    tcol = mix(INK, (150, 144, 136), dim)
    draw_text(c, name, 0, 46, "serif_heavy", 36, tcol, a, align="center")
    if sub and subtxt:
        draw_text(c, subtxt, 0, 80, "sans", 24, mix(INK3, (170, 164, 156), dim), a, align="center")
    if key == "maint":
        draw_gear(c, w / 2 - 26, -h / 2 + 26, 15, t * 0.0, METAL_D, a, teeth=9, sw=1.8)
    c.restore()


def elbow(c, x0, y0, x1, y1, a=1.0, prog=1.0, rgb=INK2, w=4):
    """Org-chart connector from parent bottom (x0,y0) to child top (x1,y1)."""
    if prog <= 0 or a <= 0:
        return
    ym = (y0 + y1) / 2
    pts = [(x0, y0), (x0, ym), (x1, ym), (x1, y1)]
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    stroke_reveal(c, p, prog, rgb, w, a)


TREE = {"director": (540, 455), "engineer": (285, 720), "chief": (795, 720), "maint": (285, 990), "workers": (795, 990)}
DEP = {"maint": (540, 545), "workers": (255, 985), "chief": (825, 985)}


def draw_tree(c, a=1.0, s=0.92, offset=(0, 0), scale=1.0, prog=1.0, dims=None, outlines=None, t=0.0):
    dims = dims or {}
    outlines = outlines or {}
    ox, oy = offset

    def P(k):
        x, y = TREE[k]
        return (540 + (x - 540) * scale + ox, 760 + (y - 760) * scale + oy)

    hh = NODE_H * s * scale / 2
    for k, (p0, p1) in enumerate((("director", "engineer"), ("director", "chief"), ("engineer", "maint"), ("chief", "workers"))):
        (x0, y0), (x1, y1) = P(p0), P(p1)
        elbow(c, x0, y0 + hh, x1, y1 - hh, a, clamp(prog * 4 - k * 0.7), w=4 * scale)
    for k, key in enumerate(("director", "engineer", "chief", "maint", "workers")):
        x, y = P(key)
        na = a * clamp(prog * 5 - k * 0.8)
        node(c, x, y, key, s * scale, na, dims.get(key, 0.0), outlines.get(key), t=t)


# =====================================================================================
# SECTION 2: the only crack
# =====================================================================================
def sc_s2(c, ctx):
    t = ctx.t
    stop = ctx.ev("stop", "s2_01") or 1e9
    since = t - stop
    # beat 1 (s2_01–s2_02): zoom into the window, machine big, then jam
    a = ctx.win("s2_01", "s2_03", lead=2.0)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        running = 1.0 if since < 0 else 0.0
        tt = t if since < 0 else stop
        c.drawRect(skia.Rect.MakeXYWH(90, 420, 900, 640), paint(mix(PAPER_DEEP, INK4, 0.2)))
        c.drawRect(skia.Rect.MakeXYWH(90, 420, 900, 640), paint(INK2, 1, stroke=5))
        gx, gy = machine_side(c, 230, 960, 620, 330, tt, running=running)
        label(c, "规章管不了的事：机器什么时候坏", 540, 1120, 38, INK, ctx.at("s2_01", 0.6, 0.6))
        if since > 0:
            ring_pulse(c, gx, gy, since, rmax=230, w=8)
            c.drawCircle(gx, gy, 82, paint(ACCENT, 0.9, stroke=7))
        # s2_02: question tags
        qs = [("什么时候坏？", 250, 500), ("坏多久？", 560, 470), ("好不好修？", 830, 520)]
        for k, (q, qx, qy) in enumerate(qs):
            qa = ease(seg(t, word_time(ctx, "s2_02", ["什么时候坏", "坏多久", "好不好修"][k]) - 0.1,
                          word_time(ctx, "s2_02", ["什么时候坏", "坏多久", "好不好修"][k]) + 0.4))
            if qa > 0:
                draw_text(c, "?", qx - text_width(q, "serif_heavy", 40) / 2 - 30, qy, "garamond", 64, ACCENT, qa, align="center")
                draw_text(c, q, qx + 10, qy, "serif_heavy", 40, INK, qa, align="center")
        c.restore()
    # beat 2 (s2_03): glossary
    a = ctx.win("s2_03", "s2_04")
    if a > 0:
        def qmk(cc, ww, hh):
            draw_text(cc, "?", 0, hh / 2 - 120, "garamond", 150, ACCENT, 1, align="center")
        gloss_card(c, 540, 770, 840, 640, "不确定性", ["事先说不准", "规章也写不进去的事"], a, ang=-1, extra=qmk, def_size=44)
    # beat 3 (s2_04): piece rate stalls, waiting
    a = ctx.win("s2_04", "s2_05")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        figure_side(c, 250, 1120, 430, "worker", face=1, arm=0.0, look=0.0)
        clock(c, 800, 560, 100, t * 2.0)
        # counter frozen
        c.drawRRect(_rrect(610, 760, 380, 120, 12), paint(CARD))
        c.drawRRect(_rrect(610, 760, 380, 120, 12), paint(INK2, 1, stroke=3))
        draw_text(c, "今日件数", 640, 790, "sans_bold", 28, INK3, 1)
        draw_text(c, "0 3 1 8", 800, 840, "courier_bold", 56, INK, 1, align="center")
        draw_text(c, "停", 960, 840, "serif_heavy", 40, ACCENT, ease(seg(t, ctx.ls("s2_04"), ctx.ls("s2_04") + 0.5)), align="center")
        steps = ["机器停", "活就断了", "只能等维修工"]
        for k, s_ in enumerate(steps):
            sa = ease(seg(t, ctx.frac("s2_04", 0.15 + k * 0.28), ctx.frac("s2_04", 0.15 + k * 0.28) + 0.5))
            draw_text(c, s_, 800, 950 + k * 62, "serif_heavy", 42, INK, sa, align="center")
            if k < 2:
                draw_text(c, "↓", 800, 981 + k * 62, "sans_bold", 28, INK3, sa, align="center")
        c.restore()
    # beat 4 (s2_05–s2_06): rule tiles, one orange tile
    a = ctx.win("s2_05", "s2_07")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        rows, cols = 6, 7
        x0, y0, tw, th = 95, 420, 122, 92
        jam = (4, 3)
        for i in range(rows):
            for j in range(cols):
                ta = ease(seg(t, ctx.ls("s2_05") + (i * cols + j) * 0.03, ctx.ls("s2_05") + (i * cols + j) * 0.03 + 0.3))
                x, y = x0 + j * (tw + 6), y0 + i * (th + 6)
                if (i, j) == jam:
                    c.drawRRect(_rrect(x, y, tw, th, 8), paint(CARD, ta))
                    c.drawRRect(_rrect(x, y, tw, th, 8), paint(ACCENT, ta, stroke=5))
                    draw_gear(c, x + tw / 2, y + th / 2, 30, 0.2, METAL_D, ta, teeth=10)
                else:
                    c.drawRRect(_rrect(x, y, tw, th, 8), paint(mix(CARD, INK4, 0.45), ta))
                    for q in range(3):
                        c.drawRect(skia.Rect.MakeXYWH(x + 14, y + 22 + q * 20, tw * (0.5 + 0.3 * _hash(i * 9 + j + q)), 6), paint(INK4, ta))
        label(c, "全厂唯一重要的不确定性：机器停机", 540, 1060, 40, INK, ctx.at("s2_05", 0.6, 1.5), box=True)
        ea = ctx.at("s2_05", 0.6, 2.4) * (1 - ctx.at("s2_06", 0.4))
        draw_text(c, "“machine stoppages are the only major happenings that cannot be predicted”", 540, 1135,
                  "garamond_it", 30, INK2, ea, align="center")
        draw_text(c, "Crozier 1964, p. 109", 540, 1180, "sans", 24, INK3, ea, align="center")
        # s2_06: control -> power
        pa = ctx.at("s2_06", 0.6)
        if pa > 0:
            jx, jy = x0 + jam[1] * (tw + 6) + tw / 2, y0 + jam[0] * (th + 6) + th / 2
            bust(c, jx + 230, jy - 10, 34, "maint", pa)
            arrow(c, jx + 70, jy, jx + 180, jy, INK, 6, pa, head=18)
            draw_text(c, "谁控制它 → 谁有权力", 540, 1150, "serif_heavy", 44, INK, pa, align="center")
        c.restore()
    # beat 5 (s2_07): back to the covered factory, the crack glows
    a = ctx.win("s2_07", None, fout=0.6)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        c.save()
        camera(c, 0.92, dy=-30)
        factory_front(c, FAC_X, FAC_BOT, FAC_W, FAC_H)
        machine_window(c, t, 0.0, glow=0.6 + 0.4 * math.sin(t * 3) ** 2)
        for k, (lid, slot, title, sub) in enumerate(S1_CARDS):
            sx, sy = slot_center(*slot)
            card(c, sx, sy, SLOT_W, SLOT_H, title, lines=2, ang=(_hash(k, 3) - 0.5) * 6, seed=k, title_size=34, sub=sub,
                 fill=mix(CARD, (200, 192, 178), 0.25))
        c.restore()
        label(c, "规章伸不进去的地方", 540, 430, 46, INK, ctx.at("s2_07", 0.6, 1.5), font_name="serif_heavy")
        c.restore()


# =====================================================================================
# SECTION 3: who guards the crack — org chart & dependency
# =====================================================================================
def relation_edge(c, p0, p1, style, prog, a=1.0, t=0.0):
    (x0, y0), (x1, y1) = p0, p1
    if prog <= 0:
        return
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    n = 80
    pts = []
    for i in range(int(n * prog) + 1):
        u = i / n
        x, y = lerp(x0, x1, u), lerp(y0, y1, u)
        if style == "wavy":
            off = math.sin(u * 22 + t * 2) * 9
        elif style == "zig":
            off = (1 if i % 4 < 2 else -1) * 12 if 0.08 < u < 0.92 else 0
        else:
            off = 0
        pts.append((x + nx * off, y + ny * off))
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    w = {"calm": 3, "wavy": 4.5, "zig": 7}[style]
    c.drawPath(p, paint(INK2 if style != "zig" else INK, a, stroke=w, join="miter" if style == "zig" else "round"))


def note_card(c, x, y, lines, a=1.0, size=32, ang=0.0, w=None):
    if a <= 0.003:
        return
    ww = w or max(text_width(s, "serif_bold", size) for s in lines) + 44
    hh = len(lines) * size * 1.45 + 26
    c.save(); c.translate(x, y); c.rotate(ang)
    c.drawRRect(_rrect(-ww / 2 + 4, -hh / 2 + 6, ww, hh, 10), paint(INK, 0.14 * a, blur=4))
    c.drawRRect(_rrect(-ww / 2, -hh / 2, ww, hh, 10), paint(CARD, a))
    c.drawRRect(_rrect(-ww / 2, -hh / 2, ww, hh, 10), paint(INK2, a, stroke=2))
    for k, s in enumerate(lines):
        draw_text(c, s, 0, -hh / 2 + 13 + size * 0.72 + k * size * 1.45, "serif_bold", size, INK, a, align="center")
    c.restore()


def manual(c, x, y, a, blank, t):
    """Open maintenance manual whose lines fade away (blank: 0..1)."""
    w, h = 720, 470
    c.drawRRect(_rrect(x - w / 2 + 8, y - h / 2 + 10, w, h, 8), paint(INK, 0.16 * a, blur=6))
    c.drawRRect(_rrect(x - w / 2, y - h / 2, w, h, 8), paint(CARD, a))
    c.drawRRect(_rrect(x - w / 2, y - h / 2, w, h, 8), paint(INK2, a, stroke=3))
    c.drawLine(x, y - h / 2 + 8, x, y + h / 2 - 8, paint(INK3, a, stroke=2))
    draw_text(c, "维修说明", x - w / 4, y - h / 2 + 50, "serif_heavy", 40, INK, a * (1 - clamp(blank * 1.4 - 0.2)), align="center")
    # left page: a machine diagram; right page: numbered steps
    da = a * (1 - clamp(blank * 2.2 - 0.1))
    if da > 0:
        draw_gear(c, x - w / 4 - 40, y + 20, 56, 0.3, INK4, da, teeth=12, outline=INK3)
        draw_gear(c, x - w / 4 + 50, y + 70, 36, -0.2, INK4, da, teeth=9, outline=INK3)
        for k in range(3):
            c.drawLine(x - w / 4 - 140, y + 140 + k * 20, x - w / 4 + 120, y + 140 + k * 20, paint(INK4, da, stroke=5))
    for k in range(9):
        la = a * (1 - clamp(blank * 2.4 - k * 0.12))
        if la <= 0:
            continue
        yy = y - h / 2 + 60 + k * 44
        draw_text(c, f"{k + 1}.", x + 40, yy, "courier_bold", 24, INK3, la)
        c.drawRRect(_rrect(x + 78, yy - 5, (w / 2 - 120) * (0.55 + 0.4 * _hash(k + 3)), 10, 5), paint(INK4, la))


def sc_s3(c, ctx):
    t = ctx.t
    # beat 1 (s3_01): maintenance man by the machine
    a = ctx.win("s3_01", "s3_02", lead=2.0)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        gx, gy = machine_side(c, 120, 1080, 520, 290, t, running=0.0)
        c.drawCircle(gx, gy, 70, paint(ACCENT, 0.85, stroke=6))
        figure_side(c, 820, 1110, 500, "maint", face=-1, arm=0.6)
        label(c, "维修工", 820, 470, 64, INK, 1, font_name="serif_heavy")
        c.restore()
    # beat 2 (s3_02–s3_03): standard org chart
    a = ctx.win("s3_02", "s3_04")
    if a > 0:
        pr = seg(t, ctx.ls("s3_02") - 0.2, ctx.ls("s3_02") + 2.2)
        hi = ease(seg(t, word_time(ctx, "s3_02", "归厂里"), word_time(ctx, "s3_02", "归厂里") + 0.5))
        draw_tree(c, a, prog=pr, outlines={"engineer": INK if hi > 0.5 else None, "maint": INK if hi > 0.5 else None}, t=t)
        if hi > 0:
            (x0, y0), (x1, y1) = TREE["engineer"], TREE["maint"]
            draw_text(c, "归技术工程师管", x0 - 22, (y0 + y1) / 2 - 4, "serif_heavy", 32, INK, hi * a, align="right")
        # s3_03: dashed "no authority" link chief -> maint
        xa = ease(seg(t, ctx.ls("s3_03") + 0.4, ctx.ls("s3_03") + 1.2))
        if xa > 0:
            (x0, y0), (x1, y1) = TREE["chief"], TREE["maint"]
            dp = paint(INK2, a * xa, stroke=4)
            dp.setPathEffect(skia.DashPathEffect.Make([12, 10], 0))
            xs, ys, xe, ye = x0 - 80, y0 + 70, x1 + 95, y1 - 40
            c.drawLine(xs, ys, lerp(xs, xe, xa), lerp(ys, ye, xa), dp)
            mx, my = (xs + xe) / 2, (ys + ye) / 2
            k = ease(seg(t, ctx.ls("s3_03") + 1.1, ctx.ls("s3_03") + 1.5))
            c.drawLine(mx - 22 * k, my - 22 * k, mx + 22 * k, my + 22 * k, paint(INK, a, stroke=8))
            c.drawLine(mx + 22 * k, my - 22 * k, mx - 22 * k, my + 22 * k, paint(INK, a, stroke=8))
            draw_text(c, "管不着", mx + 34, my + 34, "serif_heavy", 36, INK, a * k)
    # beat 3 (s3_04–s3_08): relation triangle
    a = ctx.win("s3_04", "s3_09")
    if a > 0:
        P = {"chief": (245, 520), "maint": (835, 520), "workers": (540, 1035)}
        e1 = ease(seg(t, ctx.ls("s3_05"), ctx.ls("s3_05") + 1.0))
        e2 = ease(seg(t, ctx.ls("s3_06"), ctx.ls("s3_06") + 1.0))
        e3 = ease(seg(t, ctx.ls("s3_08"), ctx.ls("s3_08") + 1.0))
        relation_edge(c, P["chief"], P["workers"], "calm", e1, a, t)
        relation_edge(c, P["maint"], P["workers"], "wavy", e2, a, t)
        relation_edge(c, P["chief"], P["maint"], "zig", e3, a, t)
        for k, key in enumerate(("chief", "maint", "workers")):
            na = a * ease(seg(t, ctx.ls("s3_04") + k * 0.25, ctx.ls("s3_04") + k * 0.25 + 0.5))
            node(c, P[key][0], P[key][1], key, 0.9, na, t=t, sub=False)
        note_card(c, 250, 800, ["关系挺松", "彼此容忍，甚至互不关心"], a * e1, size=32, ang=-2)
        n2 = ease(seg(t, ctx.ls("s3_07"), ctx.ls("s3_07") + 0.6))
        note_card(c, 830, 800, ["女工：离不开，又憋着气", "有所保留的敌意 · 不公开"] + (["维修工：宽容的家长作风"] if n2 > 0 else []), a * e2, size=30, ang=2)
        n3 = ease(seg(t, word_time(ctx, "s3_08", "问卷里"), word_time(ctx, "s3_08", "问卷里") + 0.6))
        note_card(c, 540, 600, ["公开 · 很紧张", "维修工不停挑主任毛病"] + (["46% 维修工：信不过主任", "问到被拆台：1/3 主任拒答"] if n3 > 0 else []),
                  a * e3, size=30)
    # beat 4 (s3_09–s3_13): THE MORPH
    a = ctx.win("s3_09", "s3_14")
    if a > 0:
        m = ease(seg(t, ctx.ls("s3_09") + 1.2, ctx.ls("s3_09") + 3.4))   # morph progress
        cmp_ = ease(seg(t, ctx.ls("s3_13") - 0.1, ctx.ls("s3_13") + 1.0))  # side-by-side comparison
        if cmp_ < 1:
            lay = c.saveLayerAlpha(None, int(255 * a * (1 - cmp_)))
            draw_morph(c, ctx, t, m, 1.0, (0, 0))
            c.restore()
        if cmp_ > 0:
            lay = c.saveLayerAlpha(None, int(255 * a * cmp_))
            draw_compare(c, ctx, t)
            c.restore()
    # beat 5 (s3_14): the know-how stays in their heads
    a = ctx.win("s3_14", "s3_15")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        bust(c, 400, 800, 120, "maint")
        thought_bubble(c, 730, 560, 140, 1)
        draw_gear(c, 700, 545, 62, t * 0.8, METAL_D, teeth=12)
        draw_gear(c, 790, 600, 40, -t * 1.2, METAL_D, teeth=9)
        label(c, "门道：只在他们脑子里", 540, 1150, 46, INK, ctx.at("s3_14", 0.6, 1.5), font_name="serif_heavy")
        c.restore()
    # beat 6 (s3_15): blueprints and maintenance directions disappear from the plants (Crozier 1964, p. 153)
    a = ctx.win("s3_15", "s3_16")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        blank = seg(t, word_time(ctx, "s3_15", "而且还让"), ctx.le("s3_15") + 0.2)
        manual(c, 540, 760, 1, blank, t)
        draw_text(c, "维修工：对图纸和维修说明一概不理", 540, 450, "serif_heavy", 40, INK, ctx.at("s3_15", 0.6, 0.6), align="center")
        draw_text(c, "“…have been able to make them disappear from the plants.”", 540, 1065, "garamond_it", 32, INK2,
                  ease(seg(t, word_time(ctx, "s3_15", "而且还让"), word_time(ctx, "s3_15", "而且还让") + 0.6)), align="center")
        draw_text(c, "Crozier 1964, p. 153", 540, 1110, "sans", 24, INK3, ctx.at("s3_15", 0.6, 1.0), align="center")
        c.restore()
    # beat 7 (s3_16): the evidence — none in the plants, plenty at head office (p. 153 n.)
    a = ctx.win("s3_16", "s3_16c")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        k1 = ctx.at("s3_16", 0.6, 0.3)
        k2 = ease(seg(t, word_time(ctx, "s3_16", "可在巴黎"), word_time(ctx, "s3_16", "可在巴黎") + 0.6))
        for (x0, ttl, kk) in ((60, "三家厂里", k1), (560, "巴黎总部", k2)):
            c.drawRRect(_rrect(x0, 420, 460, 520, 16), paint(CARD, 0.6 * kk))
            c.drawRRect(_rrect(x0, 420, 460, 520, 16), paint(INK3, kk, stroke=2.5))
            draw_text(c, ttl, x0 + 230, 470, "serif_heavy", 40, INK, kk, align="center")
        # empty shelf: dashed outlines of missing binders
        for k in range(5):
            dp = paint(INK3, k1, stroke=2.5)
            dp.setPathEffect(skia.DashPathEffect.Make([8, 7], 0))
            c.drawRect(skia.Rect.MakeXYWH(110 + k * 72, 600, 56, 190), dp)
        c.drawLine(90, 795, 490, 795, paint(INK2, k1, stroke=6))
        draw_text(c, "找不到一份书面说明", 290, 870, "serif_bold", 34, INK, k1, align="center")
        # full shelf at head office
        for k in range(5):
            col_ = [(124, 92, 66), (92, 86, 78), (140, 110, 70), (110, 82, 60), (98, 90, 80)][k]
            c.drawRect(skia.Rect.MakeXYWH(610 + k * 72, 600, 56, 190), paint(col_, k2))
            c.drawRect(skia.Rect.MakeXYWH(622 + k * 72, 630, 32, 10), paint(CARD, k2))
        c.drawLine(590, 795, 990, 795, paint(INK2, k2, stroke=6))
        draw_text(c, "随手就能拿到", 790, 870, "serif_bold", 34, INK, k2, align="center")
        k3 = ease(seg(t, word_time(ctx, "s3_16", "至于"), word_time(ctx, "s3_16", "至于") + 0.6))
        label(c, "怎么不见的？书里没有说", 540, 1030, 40, INK, k3, box=True, font_name="serif_heavy")
        draw_text(c, "Crozier 1964, p. 153 脚注", 540, 1100, "sans", 24, INK3, k1, align="center")
        c.restore()
    # beat 7b (s3_16c): hands off the machines
    a = ctx.win("s3_16c", "s3_17")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        gx, gy = machine_side(c, 90, 1080, 520, 290, t, running=0.0)
        reach = ease(seg(t, ctx.ls("s3_16c") + 0.3, ctx.ls("s3_16c") + 1.2))
        figure_side(c, 820, 1110, 440, "worker", face=-1, arm=0.35 + 0.55 * reach)
        k = ease(seg(t, word_time(ctx, "s3_16c", "最不可饶恕"), word_time(ctx, "s3_16c", "最不可饶恕") + 0.4))
        cx_, cy_ = 610, 790
        c.drawLine(cx_ - 50 * k, cy_ - 50 * k, cx_ + 50 * k, cy_ + 50 * k, paint(INK, 1, stroke=12))
        c.drawLine(cx_ + 50 * k, cy_ - 50 * k, cx_ - 50 * k, cy_ + 50 * k, paint(INK, 1, stroke=12))
        draw_text(c, "女工最不可饶恕的错：自己摆弄机器", 540, 450, "serif_heavy", 42, INK, ctx.at("s3_16c", 0.6, 0.4), align="center")
        draw_text(c, "Crozier 1964, p. 153", 540, 505, "sans", 24, INK3, ctx.at("s3_16c", 0.6, 0.4), align="center")
        c.restore()
    # beat 7c (s3_17): perhaps… (psychology only as a "perhaps")
    a = ctx.win("s3_17", "s3_18")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        bust(c, 360, 820, 110, "maint")
        thought_bubble(c, 700, 560, 150, 1)
        c.save(); c.translate(700, 560); c.scale(0.3, 0.3)
        manual(c, 0, 0, 1, 1.0, t)
        c.restore()
        draw_text(c, "也许……", 700, 760, "serif_heavy", 44, INK2, 1, align="center")
        stamp(c, "示意", 940, 420, 28)
        c.restore()
    # beat 8 (s3_18–s3_19): real but not legitimate
    a = ctx.win("s3_18", "s3_20")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        r1 = ease_back(seg(t, ctx.ls("s3_18") + 0.2, ctx.ls("s3_18") + 0.7))
        r2 = ease_back(seg(t, word_time(ctx, "s3_18", "但不合法"), word_time(ctx, "s3_18", "但不合法") + 0.5))
        c.save(); c.translate(300, 560); c.scale(0.6 + 0.4 * r1, 0.6 + 0.4 * r1)
        stamp(c, "真实", 0, 0, 62, INK, r1, angle=-6)
        c.restore()
        c.save(); c.translate(780, 560); c.scale(0.6 + 0.4 * r2, 0.6 + 0.4 * r2)
        stamp(c, "合法", 0, 0, 62, INK3, r2, angle=5)
        c.drawLine(-110, 40, 110, -40, paint(INK, r2, stroke=8))
        c.restore()
        ex = ease(seg(t, word_time(ctx, "s3_18", "这里的"), word_time(ctx, "s3_18", "这里的") + 0.6))
        para(c, ["不合法 ≠ 犯法", "是“名不正”：组织图上没写，规章里不承认"], 540, 760, 36, INK, ex)
        pills = ["靠攥着", "靠强硬", "靠不让别人学会"]
        for k, s_ in enumerate(pills):
            pa = ease(seg(t, word_time(ctx, "s3_19", s_), word_time(ctx, "s3_19", s_) + 0.4))
            label(c, s_, 230 + k * 300 + (40 if k == 2 else 0), 1010, 38, INK, pa, box=True, font_name="serif_heavy")
        c.restore()
    # beat 9 (s3_20): summary
    a = ctx.win("s3_20", None, fout=0.6)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        sa = ctx.at("s3_20", 0.6, 1.2)
        draw_text(c, "职位", 300, 640, "serif_heavy", 70, INK3, sa, align="center")
        c.drawLine(220, 640, 380, 640, paint(INK, sa, stroke=7))
        draw_text(c, "不确定性", 760, 640, "serif_heavy", 70, INK, ctx.at("s3_20", 0.6, 2.0), align="center")
        c.drawCircle(760, 540, 14, paint(ACCENT, ctx.at("s3_20", 0.6, 2.0)))
        draw_text(c, "权力跟着它走", 540, 860, "serif_heavy", 64, INK, ctx.at("s3_20", 0.6, 2.8), align="center")
        c.restore()


def draw_morph(c, ctx, t, m, a, off):
    """Org tree (m=0) -> dependency graph (m=1)."""
    # node positions
    pos = {}
    for key in ("director", "engineer", "chief", "maint", "workers"):
        x0, y0 = TREE[key]
        if key in DEP:
            x1, y1 = DEP[key]
        else:
            x1, y1 = x0, y0 - 60
        pos[key] = (lerp(x0, x1, m), lerp(y0, y1, m))
    scale = {"director": 0.92, "engineer": 0.92, "chief": lerp(0.92, 0.78, m), "maint": lerp(0.92, 1.32, m),
             "workers": lerp(0.92, 1.0, m)}
    fade = 1 - ease(seg(m, 0.0, 0.45))
    alpha = {"director": fade, "engineer": fade, "chief": 1.0, "maint": 1.0, "workers": 1.0}
    dims = {"chief": 0.55 * m}
    # tree connectors fade
    ta = fade * a
    if ta > 0:
        hh = NODE_H * 0.92 / 2
        for p0, p1 in (("director", "engineer"), ("director", "chief"), ("engineer", "maint"), ("chief", "workers")):
            (x0, y0), (x1, y1) = TREE[p0], TREE[p1]
            elbow(c, x0, y0 + hh, x1, y1 - hh, ta, 1.0, w=4)
    # dependency arrows
    w1 = ease(seg(t, ctx.ls("s3_10") + 0.1, ctx.ls("s3_10") + 1.1))
    w2 = ease(seg(t, ctx.ls("s3_11") + 0.1, ctx.ls("s3_11") + 1.1))
    w3 = ease(seg(t, ctx.ls("s3_12") + 0.1, ctx.ls("s3_12") + 0.9))
    mx, my = pos["maint"]
    wx, wy = pos["workers"]
    cx, cy = pos["chief"]
    if w1 > 0:
        curved_arrow(c, [(wx + 60, wy - 105), (wx + 60, my + 60), (mx - 150, my + 70)], INK, 20, a, head=26, prog=w1)
        note_card(c, wx + 10, wy + 160, ["离不开：机器一停，钱就少"], a * w1, size=31, ang=-2)
    if w2 > 0:
        curved_arrow(c, [(cx - 50, cy - 95), (cx - 50, my + 60), (mx + 150, my + 70)], INK, 11, a, head=22, prog=w2)
        note_card(c, cx - 10, cy + 160, ["也离不开：他说了不算"], a * w2, size=31, ang=2)
    if w3 > 0:
        dp = paint(INK3, a * w3, stroke=3)
        dp.setPathEffect(skia.DashPathEffect.Make([6, 9], 0))
        c.drawLine(mx - 60, my + 140, lerp(mx - 60, wx + 100, w3), lerp(my + 140, wy - 60, w3), dp)
        c.drawLine(mx + 60, my + 140, lerp(mx + 60, cx - 90, w3), lerp(my + 140, cy - 60, w3), dp)
        draw_text(c, "维修工：不太需要求他们", mx, my + 210, "serif_bold", 30, INK2, a * w3, align="center")
    for key in ("director", "engineer", "workers", "chief", "maint"):
        x, y = pos[key]
        node(c, x, y, key, scale[key], a * alpha[key], dims.get(key, 0.0), t=t,
             rings=(0.35 * m if key == "maint" else 0.0))
    # legend
    la = a * ease(seg(m, 0.55, 1.0))
    if la > 0:
        draw_text(c, "箭头 = 谁离不开谁   越粗 = 越离不开", 540, 380, "serif_bold", 32, INK2, la, align="center")
    ha = a * (1 - ease(seg(m, 0.0, 0.45)))
    if ha > 0:
        draw_text(c, "组织图：谁管谁", 540, 380, "serif_bold", 34, INK2, ha * ease(seg(t, ctx.ls("s3_09"), ctx.ls("s3_09") + 0.5)), align="center")


def draw_compare(c, ctx, t):
    """Left: org chart (who manages whom). Right: dependency (who can't do without whom)."""
    for k, (x0, title) in enumerate(((30, "按组织图：谁管谁"), (555, "按谁离不开谁"))):
        c.drawRRect(_rrect(x0, 360, 495, 790, 16), paint(CARD, 0.55))
        c.drawRRect(_rrect(x0, 360, 495, 790, 16), paint(INK3, 1, stroke=2.5))
        draw_text(c, title, x0 + 247, 408, "serif_heavy", 36, INK, 1, align="center")
    S = 0.66
    hh = NODE_H * S / 2
    pos = {"engineer": (160, 610), "chief": (395, 610), "maint": (160, 905), "workers": (395, 905)}
    # stems up to the (implied) plant director
    c.drawLine(160, 610 - hh, 160, 500, paint(INK2, 1, stroke=3))
    c.drawLine(395, 610 - hh, 395, 500, paint(INK2, 1, stroke=3))
    c.drawLine(160, 500, 395, 500, paint(INK2, 1, stroke=3))
    c.drawLine(277, 500, 277, 470, paint(INK2, 1, stroke=3))
    draw_text(c, "厂长", 330, 468, "sans_bold", 26, INK3, 1, align="center")
    for p0, p1 in (("engineer", "maint"), ("chief", "workers")):
        (x0, y0), (x1, y1) = pos[p0], pos[p1]
        c.drawLine(x0, y0 + hh, x1, y1 - hh, paint(INK2, 1, stroke=3))
    for key, (x, y) in pos.items():
        node(c, x, y, key, S, 1, dim=0.35 if key in ("engineer", "workers") else 0.0,
             outline=INK if key in ("chief", "maint") else None, sub=False, t=t)
    draw_text(c, "上", 58, 610, "serif_heavy", 34, INK3, 1, align="center")
    draw_text(c, "下", 58, 905, "serif_heavy", 34, INK3, 1, align="center")
    rp = {"maint": (815, 600), "workers": (690, 920), "chief": (935, 920)}
    curved_arrow(c, [(700, 850), (690, 700), (740, 640)], INK, 15, 1, head=20)
    curved_arrow(c, [(925, 855), (935, 700), (890, 640)], INK, 8, 1, head=16)
    node(c, rp["maint"][0], rp["maint"][1], "maint", 0.8, 1, outline=INK, sub=False, rings=0.3, t=t)
    node(c, rp["workers"][0], rp["workers"][1], "workers", 0.6, 1, dim=0.35, sub=False, t=t)
    node(c, rp["chief"][0], rp["chief"][1], "chief", 0.56, 1, dim=0.5, outline=INK, sub=False, t=t)
    draw_text(c, "上", 583, 600, "serif_heavy", 34, INK3, 1, align="center")
    draw_text(c, "下", 583, 920, "serif_heavy", 34, INK3, 1, align="center")
    ca = ease(seg(t, word_time(ctx, "s3_13", "按谁离不开谁"), word_time(ctx, "s3_13", "按谁离不开谁") + 0.6))
    cb = ease(seg(t, ctx.ls("s3_13b"), ctx.ls("s3_13b") + 0.5))
    draw_text(c, "车间主任 ⇅ 维修工：上下颠倒", 540, 1098, "serif_heavy", 42, INK, ca * (1 - cb), align="center")
    draw_text(c, "维修工，才是真正的老板", 540, 1080, "serif_heavy", 44, INK, cb, align="center")
    draw_text(c, "“…they are the real bosses.”  Crozier 1964, p. 126", 540, 1128, "garamond_it", 26, INK2, cb, align="center")


# =====================================================================================
# SECTION 4: theory
# =====================================================================================
def quote_block(c, text, x, y, width_chars, size, a, font_name="garamond_it", src=None, prog=1.0, lh=1.28):
    from textwrap import wrap
    lines = wrap(text, width_chars)
    total = sum(len(s) for s in lines)
    shown = int(total * clamp(prog))
    acc = 0
    y0 = y - (len(lines) - 1) * size * lh / 2
    for k, s in enumerate(lines):
        n = clamp((shown - acc) / max(1, len(s)))
        acc += len(s)
        if n <= 0:
            break
        part = s[: int(len(s) * n + 0.999)]
        draw_text(c, part, x - text_width(s, font_name, size) / 2, y0 + k * size * lh, font_name, size, INK, a)
    draw_text(c, "“", x - 420, y0 - size * 0.4, "garamond", 160, INK4, a * 0.8, align="center")
    if src:
        draw_text(c, src, x, y0 + len(lines) * size * lh + 10, "sans", 26, INK3, a * clamp(prog * 3 - 2), align="center")


def condition_row(c, x, y, title, sub, tick, a, size=42):
    c.drawRRect(_rrect(x, y - 36, 72, 72, 10), paint(CARD, a))
    c.drawRRect(_rrect(x, y - 36, 72, 72, 10), paint(INK2, a, stroke=4))
    check_mark(c, x + 36, y, 64, tick, INK, 10)
    draw_text(c, title, x + 100, y - 10, "serif_heavy", size, INK, a)
    draw_text(c, sub, x + 100, y + 38, "sans", 28, INK3, a)


def sc_s4(c, ctx):
    t = ctx.t
    # beat 1 (s4_01): proposition
    a = ctx.win("s4_01", "s4_02")
    if a > 0:
        pa = ctx.at("s4_01", 0.6, 0.3)
        draw_text(c, "权力", 540, 560, "serif_heavy", 120, INK, a * pa, align="center")
        arrow(c, 540, 900, 540, 660, INK, 8, a * ctx.at("s4_01", 0.6, 1.4), head=26)
        c.drawCircle(540, 950, 22, paint(ACCENT, a * ctx.at("s4_01", 0.6, 1.4)))
        draw_text(c, "对不确定性的控制", 540, 1040, "serif_heavy", 56, INK, a * ctx.at("s4_01", 0.6, 2.2), align="center")
    # beat 2 (s4_02): Crozier's sentence
    a = ctx.win("s4_02", "s4_04")
    if a > 0:
        quote_block(c, BYID["s4_02"]["text"], 540, 720, 30, 46, a, prog=seg(t, ctx.ls("s4_02"), ctx.frac("s4_02", 0.62)),
                    src="Michel Crozier, The Bureaucratic Phenomenon, 1964, p. 158")
    # beat 3 (s4_03–s4_04): A / B
    a = ctx.win("s4_04", "s4_05")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        bust(c, 280, 650, 80, "maint")
        bust(c, 800, 650, 80, "worker")
        draw_text(c, "A", 280, 480, "garamond", 64, INK, 1, align="center")
        draw_text(c, "B", 800, 480, "garamond", 64, INK, 1, align="center")
        p1 = ease(seg(t, ctx.ls("s4_04") + 0.4, ctx.ls("s4_04") + 1.2))
        arrow(c, 400, 600, 680, 600, INK, 7, 1, head=22, prog=p1)
        draw_text(c, "猜得准", 540, 560, "serif_heavy", 38, INK, p1, align="center")
        p2 = ease(seg(t, ctx.ls("s4_04") + 1.4, ctx.ls("s4_04") + 2.2))
        dp = paint(INK2, p2, stroke=6)
        dp.setPathEffect(skia.DashPathEffect.Make([12, 10], 0))
        c.drawLine(680, 760, lerp(680, 420, p2), 760, dp)
        draw_text(c, "猜不准", 540, 810, "serif_heavy", 38, INK2, p2, align="center")
        draw_text(c, "?", 800, 470 - 0, "garamond", 0.1, ACCENT, 0)
        if p2 > 0:
            draw_text(c, "?", 905, 520, "garamond", 110, ACCENT, p2, align="center")
        s4 = ease(seg(t, word_time(ctx, "s4_04", "说白了") + 2.4, word_time(ctx, "s4_04", "说白了") + 3.0))
        para(c, ["我能猜准你，你猜不准我", "→ 我占上风"], 540, 960, 46, INK, s4, font_name="serif_heavy")
        c.restore()
    # beat 4 (s4_05–s4_07): zone d'incertitude
    a = ctx.win("s4_05", "s4_07b", lead=-0.5)
    if a > 0:
        wp = seg(t, ctx.frac("s4_05", 0.7), ctx.frac("s4_05", 0.7) + 1.6)
        txt = "zone d'incertitude"
        fsz = 112
        wtot = text_width(txt, "script", fsz)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(540 - wtot / 2 - 20, 380, (wtot + 40) * ease(wp), 260))
        draw_text(c, txt, 540, 520, "script", fsz, INK, a, align="center")
        c.restore()
        c.drawLine(540 - wtot / 2, 590, lerp(540 - wtot / 2, 540 + wtot / 2, ease(seg(t, ctx.frac("s4_05", 0.7) + 1.4, ctx.frac("s4_05", 0.7) + 2.0))), 590,
                   paint(INK2, a, stroke=3))
        da = ease(seg(t, ctx.ls("s4_07"), ctx.ls("s4_07") + 0.6))
        draw_text(c, "不确定区域", 540, 690, "serif_heavy", 72, INK, a * da, align="center")
        d2 = ease(seg(t, word_time(ctx, "s4_07", "在一个组织里"), word_time(ctx, "s4_07", "在一个组织里") + 0.6))
        para(c, ["别人做事要依赖、", "却又预测不了的那块地方"], 540, 830, 42, INK2, a * d2, font_name="serif_bold")
        d3 = ease(seg(t, word_time(ctx, "s4_07", "谁能控制它"), word_time(ctx, "s4_07", "谁能控制它") + 0.6))
        draw_text(c, "谁控制它，谁就有权力", 540, 1000, "serif_heavy", 46, INK, a * d3, align="center")
        draw_text(c, "Crozier & Friedberg, L'Acteur et le système, 1977", 540, 1100, "sans", 26, INK3, a * da, align="center")
    # beat 4b (s4_07b): what is uncertainty for the problem is power for the actors
    a = ctx.win("s4_07b", "s4_09")
    if a > 0:
        k1 = ease(seg(t, word_time(ctx, "s4_07b", "从事情"), word_time(ctx, "s4_07b", "从事情") + 0.6))
        k2 = ease(seg(t, word_time(ctx, "s4_07b", "从人的"), word_time(ctx, "s4_07b", "从人的") + 0.6))
        c.drawRRect(_rrect(70, 470, 440, 420, 18), paint(CARD, a * k1))
        c.drawRRect(_rrect(70, 470, 440, 420, 18), paint(INK3, a * k1, stroke=2.5))
        draw_text(c, "从事情的角度看", 290, 540, "serif_bold", 36, INK2, a * k1, align="center")
        draw_text(c, "?", 290, 680, "garamond", 130, ACCENT, a * k1, align="center")
        draw_text(c, "不确定性", 290, 820, "serif_heavy", 58, INK, a * k1, align="center")
        c.drawRRect(_rrect(570, 470, 440, 420, 18), paint(CARD, a * k2))
        c.drawRRect(_rrect(570, 470, 440, 420, 18), paint(INK, a * k2, stroke=5))
        draw_text(c, "从人的角度看", 790, 540, "serif_bold", 36, INK2, a * k2, align="center")
        bust(c, 790, 650, 46, "maint", a * k2)
        draw_text(c, "权力", 790, 820, "serif_heavy", 58, INK, a * k2, align="center")
        arrow(c, 515, 680, 565, 680, INK, 6, a * k2, head=16)
        draw_text(c, "« ce qui est incertitude du point de vue des problèmes", 540, 975, "garamond_it", 34, INK2, a * k2, align="center")
        draw_text(c, "est pouvoir du point de vue des acteurs »", 540, 1020, "garamond_it", 34, INK2, a * k2, align="center")
        draw_text(c, "Crozier & Friedberg, L'Acteur et le système, 1977", 540, 1085, "sans", 26, INK3, a * k2, align="center")
    # beat 5 (s4_09–s4_10): French sentence + power is a relation
    a = ctx.win("s4_09", "s4_11")
    if a > 0:
        qa = 1 - ease(seg(t, ctx.ls("s4_10") - 0.2, ctx.ls("s4_10") + 0.4))
        if qa > 0:
            quote_block(c, BYID["s4_08"]["text"], 540, 640, 38, 36, a * qa, prog=seg(t, ctx.ls("s4_09"), ctx.ls("s4_09") + 4.0),
                        src="Crozier & Friedberg, L'Acteur et le système, 1977, pp. 59–60")
            draw_text(c, "权力，就在那一点“余地”里", 540, 1010, "serif_heavy", 50, INK, a * qa * ease(seg(t, ctx.ls("s4_09") + 2.5, ctx.ls("s4_09") + 3.2)), align="center")
        ra = ease(seg(t, ctx.ls("s4_10"), ctx.ls("s4_10") + 0.6))
        if ra > 0:
            lay = c.saveLayerAlpha(None, int(255 * a * ra))
            seal(c, 280, 720, 220)
            k = ease(seg(t, word_time(ctx, "s4_10", "而是"), word_time(ctx, "s4_10", "而是") + 0.4))
            c.drawLine(160, 560, 400, 790, paint(INK, k, stroke=9))
            c.drawLine(400, 560, 160, 790, paint(INK, k, stroke=9))
            draw_text(c, "不是一枚印章", 280, 880, "serif_heavy", 40, INK, 1, align="center")
            r2 = ease(seg(t, word_time(ctx, "s4_10", "而是"), word_time(ctx, "s4_10", "而是") + 0.8))
            figure_side(c, 650, 820, 260, "worker", face=1, a=r2)
            figure_side(c, 920, 820, 260, "maint", face=-1, a=r2)
            sag = 30 * (1 - ease(seg(t, word_time(ctx, "s4_10", "谁更离不开谁"), word_time(ctx, "s4_10", "谁更离不开谁") + 0.6)))
            rp = skia.Path().moveTo(690, 650).quadTo(785, 650 + sag + 10, 880, 650)
            c.drawPath(rp, paint(INK2, r2, stroke=5))
            draw_text(c, "而是一段关系", 785, 880, "serif_heavy", 40, INK, r2, align="center")
            draw_text(c, "谁更离不开谁", 540, 1030, "serif_heavy", 54, INK, ease(seg(t, word_time(ctx, "s4_10", "谁更离不开谁"), word_time(ctx, "s4_10", "谁更离不开谁") + 0.5)), align="center")
            c.restore()
    # beat 6 (s4_11–s4_12): four sources
    a = ctx.win("s4_11", "s4_13")
    if a > 0:
        items = [("别人难以替代的专长", "一"), ("跟外部环境打交道的关系", "二"), ("信息和沟通的渠道", "三"), ("会用组织的规章本身", "四")]
        hl = ease(seg(t, ctx.ls("s4_12"), ctx.ls("s4_12") + 0.5))
        for k, (s_, n_) in enumerate(items):
            x = 290 + (k % 2) * 500
            y = 560 + (k // 2) * 360
            ia = a * ease(seg(t, word_time(ctx, "s4_11", n_ + "，"), word_time(ctx, "s4_11", n_ + "，") + 0.5))
            dimk = hl * (0.6 if k > 0 else 0.0)
            c.drawRRect(_rrect(x - 225, y - 150, 450, 300, 18), paint(mix(CARD, (214, 208, 196), dimk), ia))
            c.drawRRect(_rrect(x - 225, y - 150, 450, 300, 18), paint(INK if (k == 0 and hl > 0.5) else INK3, ia, stroke=6 if (k == 0 and hl > 0.5) else 2.5))
            ic = mix(INK2, INK4, dimk)
            if k == 0:
                wrench_icon(c, x, y - 40, 70, ic, ia)
            elif k == 1:
                door_out(c, x, y - 40, 110, ic, ia)
            elif k == 2:
                envelope(c, x, y - 40, 120, ic, ia)
            else:
                rulebook(c, x, y - 40, 130, ic, ia)
            draw_text(c, n_, x - 190, y - 112, "serif_heavy", 40, mix(INK, INK4, dimk), ia)
            draw_text(c, s_, x, y + 80, "serif_heavy", 34, mix(INK, INK4, dimk), ia, align="center")
        if hl > 0:
            bust(c, 400, 470, 30, "maint", a * hl)
            draw_text(c, "维修工", 400, 405, "serif_heavy", 30, INK, a * hl, align="center")
    # beat 7 (s4_13–s4_14): Hickson et al.
    a = ctx.win("s4_13", "s4_15")
    if a > 0:
        def ex(cc, ww, hh):
            k = ease(seg(t, ctx.ls("s4_14"), ctx.ls("s4_14") + 0.6))
            draw_text(cc, "权变 = 看情况", 0, 40, "serif_heavy", 54, INK, k, align="center")
            draw_text(cc, "权力不固定在位置上，", 0, 130, "serif_bold", 38, INK2, ease(seg(t, word_time(ctx, "s4_14", "这个理论说"), word_time(ctx, "s4_14", "这个理论说") + 0.6)), align="center")
            draw_text(cc, "要看谁能应付最要紧的事", 0, 185, "serif_bold", 38, INK2, ease(seg(t, word_time(ctx, "s4_14", "要看谁"), word_time(ctx, "s4_14", "要看谁") + 0.6)), align="center")
        gloss_card(c, 540, 770, 860, 640, "战略权变理论", [], a, ang=-1, tag="1971 · Hickson 等 · 《管理科学季刊》", extra=ex)
    # beat 8 (s4_15–s4_22): three conditions & score
    a = ctx.win("s4_15", "s4_23")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        qv = ease(seg(t, ctx.ls("s4_17") - 0.2, ctx.ls("s4_17") + 0.3)) * (1 - ease(seg(t, ctx.ls("s4_19") - 0.3, ctx.ls("s4_19") + 0.3)))
        rows = [("能应对不确定性", "光有不确定性不够，要能对付", "s4_16"),
                ("难以被替代", "别人顶不上你的位置", "s4_19"),
                ("在主流程上", "你一停，整条线马上受影响", "s4_20")]
        ticks = [word_time(ctx, "s4_22", "打勾", 0), word_time(ctx, "s4_22", "打勾", 1), word_time(ctx, "s4_22", "打勾", 2)]
        level = 0.0
        for k, (ttl, sub, lid) in enumerate(rows):
            ra = ease(seg(t, ctx.ls(lid), ctx.ls(lid) + 0.5))
            tk = ease(seg(t, ticks[k] - 0.35, ticks[k] + 0.15))
            level += tk
            y = 860 + k * 125 if qv > 0.01 else 560 + k * 150
            y = lerp(560 + k * 150, 790 + k * 120, qv) if t < ctx.ls("s4_19") + 0.3 else 560 + k * 150
            condition_row(c, 70, y, ttl, sub, tk, ra * (1 - 0.0), size=42 if qv < 0.5 else 36)
        if qv > 0:
            quote_block(c, BYID["s4_17"]["text"], 540, 520, 30, 44, qv, prog=seg(t, ctx.ls("s4_17"), ctx.frac("s4_17", 0.6)),
                        src="Hickson et al., ASQ 16(2), 1971, p. 219")
        # the maintenance node levels up with each tick
        ma = ease(seg(t, ctx.ls("s4_21"), ctx.ls("s4_21") + 0.6))
        if ma > 0:
            node(c, 840, 1060, "maint", 0.8 + 0.08 * level, ma, rings=level / 3, t=t, sub=False)
        allc = ease(seg(t, word_time(ctx, "s4_22", "三条全中"), word_time(ctx, "s4_22", "三条全中") + 0.4))
        if allc > 0:
            draw_text(c, "三条全中", 300, 1060, "serif_heavy", 64, INK, allc * (1 - ease(seg(t, ctx.ls("s4_22b"), ctx.ls("s4_22b") + 0.4))), align="center")
        hb = ease(seg(t, word_time(ctx, "s4_22b", "他们还补了"), word_time(ctx, "s4_22b", "他们还补了") + 0.5))
        if hb > 0:
            note_card(c, 330, 1030, ["Hickson 等：难以替换，", "很可能也有工会协议护着"], hb, size=31, ang=-1.5)
        hc = ease(seg(t, word_time(ctx, "s4_22b", "他们的结论"), word_time(ctx, "s4_22b", "他们的结论") + 0.5))
        if hc > 0:
            c.drawRect(skia.Rect.MakeXYWH(0, 380, W, 120), paint(PAPER, 0.92 * hc))
            draw_text(c, "得三条一起解释，不能只靠“不确定性”", 540, 440, "serif_heavy", 42, INK, hc, align="center")
        c.restore()
    # beat 9 (s4_23): summary
    a = ctx.win("s4_23", None, fout=0.6)
    if a > 0:
        draw_text(c, "权力不是职位给的", 540, 520, "serif_heavy", 58, INK, a * ctx.at("s4_23", 0.6, 1.0), align="center")
        items = ["别人离不开你", "又替不了你", "还离主线很近"]
        for k, s_ in enumerate(items):
            ia = a * ease(seg(t, word_time(ctx, "s4_23", s_[:3]), word_time(ctx, "s4_23", s_[:3]) + 0.4))
            label(c, s_, 540, 700 + k * 130, 50, INK, ia, box=True, font_name="serif_heavy")


from script_data import BY_ID as BYID  # noqa: E402


# =====================================================================================
# SECTION 5: why here
# =====================================================================================
def sc_s5(c, ctx):
    t = ctx.t
    a = ctx.win("s5_01", "s5_02")
    if a > 0:
        draw_text(c, "常识版：", 540, 520, "sans_bold", 36, INK3, a, align="center")
        draw_text(c, "懂技术 = 有话语权", 540, 640, "serif_heavy", 70, INK, a, align="center")
        k = ease(seg(t, word_time(ctx, "s5_01", "可克罗齐耶"), word_time(ctx, "s5_01", "可克罗齐耶") + 0.5))
        c.drawLine(200, 645, lerp(200, 880, k), 635, paint(INK, a, stroke=8))
        draw_text(c, "克罗齐耶看到的，深一层", 540, 860, "serif_heavy", 54, INK, a * ease(seg(t, word_time(ctx, "s5_01", "比这深一层"), word_time(ctx, "s5_01", "比这深一层") + 0.5)), align="center")
    a = ctx.win("s5_02", "__end__", fout=0.6)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        la = ease(seg(t, ctx.ls("s5_02"), ctx.ls("s5_02") + 0.6))
        ra = ease(seg(t, ctx.ls("s5_04"), ctx.ls("s5_04") + 0.6))
        # left: everything uncertain
        c.drawRRect(_rrect(30, 360, 495, 760, 16), paint(CARD, 0.5 * la))
        c.drawRRect(_rrect(30, 360, 495, 760, 16), paint(INK3, la, stroke=2.5))
        draw_text(c, "什么都说不准的地方", 277, 405, "serif_heavy", 34, INK, la, align="center")
        for k in range(18):
            x = 70 + _hash(k, 1) * 410
            y = 470 + _hash(k, 2) * 560
            da = la * ease(seg(t, ctx.ls("s5_03") + k * 0.12, ctx.ls("s5_03") + k * 0.12 + 0.4))
            c.drawCircle(x, y, 13, paint(ACCENT, da * 0.9))
            figure_side(c, x + 28, y + 38, 70, ["worker", "maint", "chief", "engineer"][k % 4], face=-1, a=da)
        for k, s_ in enumerate(["原料价格", "订单", "对手"]):
            draw_text(c, s_ + "会变", 277, 1060 + k * 0, "serif_bold", 0.1, INK, 0)
        tags = ["原料价格会变", "订单会变", "对手会变"]
        for k, s_ in enumerate(tags):
            ta = la * ease(seg(t, word_time(ctx, "s5_03", s_[:2]), word_time(ctx, "s5_03", s_[:2]) + 0.4))
            label(c, s_, 277, 520 + k * 200, 30, INK, ta, box=True)
        # right: this plant
        c.drawRRect(_rrect(555, 360, 495, 760, 16), paint(CARD, 0.5 * ra))
        c.drawRRect(_rrect(555, 360, 495, 760, 16), paint(INK3, ra, stroke=2.5))
        draw_text(c, "这家厂", 802, 405, "serif_heavy", 34, INK, ra, align="center")
        for i in range(7):
            for j in range(4):
                x, y = 585 + j * 112, 445 + i * 92
                if (i, j) == (4, 2):
                    continue
                c.drawRRect(_rrect(x, y, 102, 82, 6), paint(mix(CARD, INK4, 0.5), ra))
        ox, oy = 585 + 2 * 112 + 51, 445 + 4 * 92 + 41
        c.drawCircle(ox, oy, 22, paint(ACCENT, ra))
        aa = ease(seg(t, word_time(ctx, "s5_04", "所有的依赖"), word_time(ctx, "s5_04", "所有的依赖") + 0.8))
        for k in range(8):
            ang = k * math.pi / 4 + 0.3
            sx, sy = ox + math.cos(ang) * 230, oy + math.sin(ang) * 230
            sx = clamp(sx, 580, 1030)
            sy = clamp(sy, 450, 1100)
            arrow(c, sx, sy, ox + math.cos(ang) * 40, oy + math.sin(ang) * 40, INK, 5, ra * aa, head=16, prog=aa)
        fa = ease(seg(t, ctx.ls("s5_05"), ctx.ls("s5_05") + 0.6))
        if fa > 0:
            c.drawRect(skia.Rect.MakeXYWH(0, 980, W, 200), paint(PAPER, 0.92 * fa))
            draw_text(c, "规章越细 → 剩下的余地越金贵", 540, 1050, "serif_heavy", 50, INK, fa, align="center")
            fq = ease(seg(t, word_time(ctx, "s5_05", "克罗齐耶的原话"), word_time(ctx, "s5_05", "克罗齐耶的原话") + 0.6))
            draw_text(c, "“parallel power increases in direct ratio to its rarity”  Crozier 1964, p. 192", 540, 1120,
                      "garamond_it", 27, INK2, fq, align="center")
        c.restore()


# =====================================================================================
# SECTION 6: the vicious circle; rules as shield
# =====================================================================================
CYCLE = ["依附", "怨气", "更多规章", "更僵", "缝更值钱"]


def sc_s6(c, ctx):
    t = ctx.t
    a = ctx.win("s6_01", "s6_04", lead=2.0)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        figure_side(c, 260, 1120, 460, "worker", face=1, arm=0.0)
        figure_side(c, 820, 1120, 460, "maint", face=1, arm=0.5)
        tags = [("看他脸色", 0.25), ("等他有空", 0.38), ("求他快一点", 0.5)]
        for k, (s_, f) in enumerate(tags):
            ta = ease(seg(t, word_time(ctx, "s6_02", s_[:3]), word_time(ctx, "s6_02", s_[:3]) + 0.4))
            label(c, s_, 470, 520 + k * 110, 38, INK, ta, box=True)
        ra = ease(seg(t, ctx.ls("s6_03"), ctx.ls("s6_03") + 0.4))
        for k in range(5):
            ka = ease(seg(t, ctx.ls("s6_03") + 0.5 + k * 0.35, ctx.ls("s6_03") + 0.9 + k * 0.35))
            if ka > 0:
                y = lerp(300, 610 - k * 26, ka)
                card(c, 820 + (k % 2) * 18 - 9, y, 300, 90, "规章", lines=1, ang=(k - 2) * 3, title_size=30, a=ra)
        c.restore()
    a = ctx.win("s6_04", "s6_06")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        cx, cy, R = 540, 760, 310
        t0 = ctx.ls("s6_04")
        # travelling highlight accelerates (two laps)
        u = seg(t, t0 + 0.3, ctx.le("s6_04"))
        lapf = 2.0 * u ** 1.6
        for k, s_ in enumerate(CYCLE):
            ang = -math.pi / 2 + k * 2 * math.pi / 5
            x, y = cx + math.cos(ang) * R, cy + math.sin(ang) * R
            na = ease(seg(t, t0 + k * 0.4, t0 + k * 0.4 + 0.4))
            act = max(0.0, 1 - abs(((lapf * 5) % 5) - k) * 1.2) if u > 0 else 0
            c.drawCircle(x, y, 92, paint(CARD, na))
            c.drawCircle(x, y, 92, paint(INK, na, stroke=3 + 5 * act))
            fs = 38 if len(s_) <= 2 else 32
            draw_text(c, s_, x, y, "serif_heavy", fs, INK, na, align="center")
            ang2 = ang + 2 * math.pi / 5
            a0, a1 = ang + 0.34, ang2 - 0.34
            p0 = (cx + math.cos(a0) * R, cy + math.sin(a0) * R)
            p1 = (cx + math.cos(a1) * R, cy + math.sin(a1) * R)
            mid = (a0 + a1) / 2
            ctrl = (cx + math.cos(mid) * R * 1.12, cy + math.sin(mid) * R * 1.12)
            curved_arrow(c, [p0, ctrl, p1], INK2, 5, na, head=16)
        va = ease(seg(t, ctx.ls("s6_05"), ctx.ls("s6_05") + 0.8))
        txt = "cercle vicieux"
        wtot = text_width(txt, "script", 86)
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(cx - wtot / 2 - 10, cy - 120, (wtot + 20) * va, 200))
        draw_text(c, txt, cx, cy - 30, "script", 86, INK, 1, align="center")
        c.restore()
        draw_text(c, "恶性循环", cx, cy + 60, "serif_heavy", 54, INK, va, align="center")
        c.restore()
    a = ctx.win("s6_06", "s6_08b")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        for k in range(4):
            figure_side(c, 110 + k * 120, 1110, 330, "worker", face=1, arm=0.0)
        figure_side(c, 900, 1110, 400, "maint", face=-1, arm=0.5)
        sp = ease(seg(t, word_time(ctx, "s6_08", "有一条"), word_time(ctx, "s6_08", "有一条") + 1.2))
        if sp < 1:
            for k in range(6):
                kx = lerp(560 + (k % 3 - 1) * 120, 680, sp)
                ky = lerp(520 + (k // 3) * 110, 800, sp)
                card(c, kx, ky, lerp(220, 120, sp), lerp(80, 60, sp), "规章", lines=1, ang=(k - 2.5) * 5 * (1 - sp), title_size=26, a=1 - sp * 0.9)
        if sp > 0:
            c.save(); c.translate(680, 800); c.scale(0.4 + 0.6 * sp, 0.4 + 0.6 * sp)
            shield(c, 0, 0, 380, CARD, INK, sp, stroke=7)
            draw_text(c, "规章", 0, -30, "serif_heavy", 64, INK, sp, align="center")
            draw_text(c, "对事不对人", 0, 50, "serif_heavy", 36, INK2, sp, align="center")
            c.restore()
        ha = ease(seg(t, word_time(ctx, "s6_07", "反而会推着"), word_time(ctx, "s6_07", "反而会推着") + 0.5))
        label(c, "下面的人：要新规章，限制上面的权力", 420, 470, 36, INK, ha, box=True, font_name="serif_heavy")
        draw_text(c, "Crozier 1964, pp. 160–161", 420, 525, "sans", 24, INK3, ha, align="center")
        c.restore()
    a = ctx.win("s6_08b", "s6_09")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        draw_text(c, "科层系统的心理动机：躲开……", 540, 450, "serif_heavy", 42, INK, ctx.at("s6_08b", 0.6, 0.6), align="center")
        items = [("当面的上下级紧张", "当面的"), ("当事人说：专断、偏袒", "当事人"), ("说到底：人对人的依附", "说到底")]
        for k, (s_, anchor) in enumerate(items):
            ia = ease(seg(t, word_time(ctx, "s6_08b", anchor), word_time(ctx, "s6_08b", anchor) + 0.4))
            label(c, s_, 540, 610 + k * 150, 50, INK, ia, box=True, font_name="serif_heavy", pad=26)
        draw_text(c, "Crozier, Sociologie du travail, 1960", 540, 1090, "sans", 24, INK3, ctx.at("s6_08b", 0.6, 0.6), align="center")
        c.restore()
    a = ctx.win("s6_09", "s6_10")
    if a > 0:
        def ex(cc, ww, hh):
            k = ease(seg(t, word_time(ctx, "s6_09", "让每个人"), word_time(ctx, "s6_09", "让每个人") + 0.6))
            figure_side(cc, -230, hh / 2 - 50, 200, "worker", face=1, a=k)
            figure_side(cc, 230, hh / 2 - 50, 200, "maint", face=-1, a=k)
            shield(cc, 0, hh / 2 - 150, 150, CARD, INK, k, stroke=4)
            draw_text(cc, "减少面对面的依附", 0, hh / 2 - 15, "sans_bold", 28, INK2, k, align="center")
        gloss_card(c, 540, 770, 860, 700, "潜在功能", ["不写在明面上，", "却实实在在起作用的用处"], a, ang=1, extra=ex, def_size=40,
                   tag="名词 · Friedberg 2010 年导言")
    a = ctx.win("s6_10", "s6_11")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        for k in range(3):
            figure_side(c, 120 + k * 110, 1080, 300, "worker", face=1)
        l1 = ease(seg(t, word_time(ctx, "s6_10", "受人拿捏"), word_time(ctx, "s6_10", "受人拿捏") + 0.5))
        label(c, "受人拿捏的一方：", 290, 540, 34, INK, l1, box=False, font_name="serif_heavy")
        label(c, "要对事不对人的规矩", 290, 600, 34, INK, l1, box=False, font_name="serif_heavy")
        sh = ease(seg(t, word_time(ctx, "s6_10", "维修工要的"), word_time(ctx, "s6_10", "维修工要的") + 0.8))
        c.drawOval(skia.Rect.MakeXYWH(640, 820, 380, 300), paint(INK, 0.32 * sh, blur=30))
        figure_side(c, 830, 1080, 340, "maint", face=-1, dim=0.3 * sh)
        label(c, "维修工：", 800, 540, 34, INK, sh, box=False, font_name="serif_heavy")
        label(c, "自己的地盘，不许外人插手", 800, 600, 34, INK, sh, box=False, font_name="serif_heavy")
        draw_text(c, "每一群人都在争：保住、扩大自己说了算的地方", 540, 450, "serif_bold", 34, INK, ctx.at("s6_10", 0.5, 0.3), align="center")
        draw_text(c, "Crozier 1964, pp. 153, 156", 540, 1160, "sans", 24, INK3, ctx.at("s6_10", 0.5, 0.5), align="center")
        c.restore()
    a = ctx.win("s6_11", None, fout=0.6)
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        k1 = ctx.at("s6_11", 0.6, 0.8)
        k2 = ease(seg(t, word_time(ctx, "s6_11", "也是盾牌"), word_time(ctx, "s6_11", "也是盾牌") + 0.6))
        cage(c, 300, 760, 320, INK2, k1)
        draw_text(c, "笼子", 300, 990, "serif_heavy", 56, INK, k1, align="center")
        shield(c, 780, 740, 330, CARD, INK, k2, stroke=7)
        draw_text(c, "盾牌", 780, 990, "serif_heavy", 56, INK, k2, align="center")
        k3 = ease(seg(t, word_time(ctx, "s6_11", "要看你"), word_time(ctx, "s6_11", "要看你") + 0.6))
        draw_text(c, "看你站在哪一边", 540, 1110, "serif_heavy", 46, INK, k3, align="center")
        c.restore()


# =====================================================================================
# SECTION 7: three questions, and the other side (inference)
# =====================================================================================
def balance(c, x, y, s, tilt, a=1.0, left="", right=""):
    """A simple balance scale; tilt in radians (positive = right side down)."""
    c.drawLine(x, y, x, y + s * 0.9, paint(INK2, a, stroke=6))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.3, y + s * 0.9, s * 0.6, 10), paint(INK2, a))
    dx, dy = math.cos(tilt) * s, math.sin(tilt) * s
    c.drawLine(x - dx, y - dy, x + dx, y + dy, paint(INK, a, stroke=7))
    c.drawCircle(x, y, 9, paint(INK, a))
    for sgn, txt in ((-1, left), (1, right)):
        px, py = x + sgn * dx, y + sgn * dy
        c.drawLine(px, py, px - s * 0.22, py + s * 0.45, paint(INK2, a, stroke=2.5))
        c.drawLine(px, py, px + s * 0.22, py + s * 0.45, paint(INK2, a, stroke=2.5))
        c.drawArc(skia.Rect.MakeXYWH(px - s * 0.3, py + s * 0.3, s * 0.6, s * 0.3), 0, 180, True, paint(CARD, a))
        c.drawArc(skia.Rect.MakeXYWH(px - s * 0.3, py + s * 0.3, s * 0.6, s * 0.3), 0, 180, True, paint(INK2, a, stroke=3))
        draw_text(c, txt, px, py + s * 0.75, "serif_heavy", 34, INK, a, align="center")


def sc_s7(c, ctx):
    t = ctx.t
    a = ctx.win("s7_01", "s7_05")
    if a > 0:
        qs = [("s7_02", "别人搞不定、又离不开？"), ("s7_03", "能不能被替代？"), ("s7_04", "离主线有多近？")]
        for k, (lid, s_) in enumerate(qs):
            qa = a * ease(seg(t, ctx.ls(lid), ctx.ls(lid) + 0.7))
            y = 520 + k * 230
            draw_text(c, "?", 170, y, "garamond", 150, INK, qa, align="center")
            draw_text(c, s_, 270, y + 6, "serif_heavy", 50, INK, qa)
    # the other side: two conditions, and the dilemma (L'Acteur et le système, p. 67)
    a = ctx.win("s7_05", "s7_06")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        cond = ease(seg(t, ctx.ls("s7_05"), ctx.ls("s7_05") + 0.6))
        para(c, ["撑着它的两个条件：", "机器一直不太可靠 · 门道一直不外传"], 540, 450, 38, INK, cond)
        k1 = ease(seg(t, ctx.ls("s7_05b"), ctx.ls("s7_05b") + 0.6)) * (1 - ease(seg(t, ctx.ls("s7_05c") - 0.2, ctx.ls("s7_05c") + 0.3)))
        if k1 > 0:
            gx, gy = machine_side(c, 140, 1060, 480, 270, t, running=0.0, a=k1)
            ring_pulse(c, gx, gy, (t - ctx.ls("s7_05b")) % 1.6 + 0.2, rmax=140, a=k1, w=6)
            para(c, ["坏得太勤", "→ 生产停摆", "→ 这张牌也废了"], 840, 700, 40, INK, k1, font_name="serif_heavy")
        k2 = ease(seg(t, ctx.ls("s7_05c"), ctx.ls("s7_05c") + 0.6))
        if k2 > 0:
            tilt = 0.12 * math.sin(t * 1.3)
            balance(c, 540, 700, 280, tilt, k2, left="转得够好", right="有点难搞")
            draw_text(c, "权力，跟机器的毛病绑在一起", 540, 1110, "serif_heavy", 44, INK, k2, align="center")
            draw_text(c, "（推到极端的说法，不是说故意搞破坏）", 540, 1170, "sans", 28, INK3, k2, align="center")
        c.restore()
    a = ctx.win("s7_06", "s7_07")
    if a > 0:
        lay = c.saveLayerAlpha(None, int(255 * a))
        stamp(c, "推论", 930, 420, 34, INK2, 0.9)
        r = ease(seg(t, word_time(ctx, "s7_06", "一旦"), word_time(ctx, "s7_06", "一旦") + 1.2))
        machine_side(c, 120, 1020, 440, 250, t, running=r, a=1)
        if r < 1:
            c.drawCircle(120 + 440 * 0.28, 1020 - 250 * 0.62, 60, paint(ACCENT, 0.85 * (1 - r), stroke=6))
        rb = ease(seg(t, word_time(ctx, "s7_06", "把维修写成"), word_time(ctx, "s7_06", "把维修写成") + 0.6))
        pm = ease(seg(t, word_time(ctx, "s7_06", "预防性维护"), word_time(ctx, "s7_06", "预防性维护") + 0.5)) * (1 - rb)
        if pm > 0:
            note_card(c, 560, 560, ["预防性维护", "不等机器坏，提前定期保养"], pm, size=34)
        rulebook(c, 690, 760, 170, INK2, rb, label="流程")
        lv = 1 - ease(seg(t, word_time(ctx, "s7_06", "就会消失"), word_time(ctx, "s7_06", "就会消失") + 1.0))
        node(c, 880, 900, "maint", 0.62, 1, rings=lv * 0.9, dim=0.5 * (1 - lv), sub=False, t=t)
        hk = ease(seg(t, ctx.ls("s7_06a"), ctx.ls("s7_06a") + 0.6))
        draw_text(c, "办法写下来、看得见 → 替代的人找得到", 540, 470, "serif_heavy", 38, INK, hk, align="center")
        he = ease(seg(t, word_time(ctx, "s7_06a", "他们还估计"), word_time(ctx, "s7_06a", "他们还估计") + 0.5))
        draw_text(c, "Hickson 等估计：这家厂的维修工会抵制（1971, p. 224）", 540, 525, "sans", 26, INK2, he, align="center")
        cl = ease(seg(t, ctx.ls("s7_06b"), ctx.ls("s7_06b") + 0.8))
        if cl > 0:
            for k in range(6):
                c.drawCircle(820 + k * 26, 660 + math.sin(k * 1.7) * 14, 36 + 6 * math.sin(k), paint((150, 142, 130), 0.55 * cl))
            draw_text(c, "怨气还在", 890, 590, "serif_heavy", 40, INK, cl, align="center")
        c.restore()
    a = ctx.win("s7_07", "__end__", fout=0.6)
    if a > 0:
        para(c, ["靠不确定性得来的权力，", "本身也是不确定的"], 540, 700, 56, INK, a * ctx.at("s7_07", 0.6, 1.0), font_name="serif_heavy")


# =====================================================================================
# ENDING
# =====================================================================================
def sc_end(c, ctx):
    t = ctx.t
    tl = ctx.tl
    lines = [("e01", "组织图画的，是谁管谁。"), ("e02", "真正的权力，画在谁离不开谁。"), ("e03", "而对手里什么都没有的人，"),
             ("e03b", "规章，是他们最后的那面墙。")]
    fade_all = 1 - ease(seg(t, tl["end_main"] + 1.2, tl["end_main"] + 2.0))
    for k, (lid, s_) in enumerate(lines):
        src = "e03" if lid == "e03b" else lid
        st = ctx.ls(src) + (ctx.le("e03") - ctx.ls("e03")) * 0.45 if lid == "e03b" else ctx.ls(src)
        la = ease(seg(t, st - 0.1, st + 0.6)) * fade_all
        y = 560 + k * 130 + (40 if k >= 2 else 0)
        draw_text(c, s_, 540, y, "serif_heavy", 54 if k < 2 else 52, INK, la, align="center")
    # small emblem under the lines
    ea = ease(seg(t, ctx.ls("e03"), ctx.ls("e03") + 1.0)) * fade_all
    if ea > 0:
        brick_wall(c, 330, 1040, 420, 102, ea)
        for k in range(3):
            figure_side(c, 420 + k * 120, 1150, 0.1, "worker", a=0)
    # teaser
    t0, t1 = tl["teaser"]
    ta = ease(seg(t, t0, t0 + 0.6)) * (1 - ease(seg(t, t1 - 0.5, t1)))
    if ta > 0:
        # one small line, as a closing note
        draw_text(c, "组织里的权力", 540, 700, "serif_heavy", 56, INK, ta, align="center", spacing=10)
        c.drawLine(400, 760, 680, 760, paint(INK3, ta, stroke=2))
        draw_text(c, "下一期 · 罗伯特·摩西：从没当选过公职，却主导了纽约几十年的建设", 540, 1150, "serif_semi", 30, INK2, ta,
                  align="center")
    # sources
    s0, s1 = tl["sources"]
    sa = ease(seg(t, s0, s0 + 0.6)) * (1 - ease(seg(t, s1 - 0.6, s1)))
    if sa > 0:
        draw_text(c, "资料来源", 540, 440, "serif_heavy", 44, INK, sa, align="center")
        src = ["Michel Crozier, Le phénomène bureaucratique, Seuil, 1963",
               "（英译 The Bureaucratic Phenomenon, Univ. of Chicago Press, 1964；",
               "2010 年 Transaction 再版，Erhard Friedberg 导言）",
               "M. Crozier, « Les relations de pouvoir dans un système d'organisation",
               "bureaucratique », Sociologie du travail, 1960, pp. 61–75",
               "Michel Crozier & Erhard Friedberg, L'Acteur et le système, Seuil, 1977",
               "D. J. Hickson et al., “A Strategic Contingencies' Theory of",
               "Intraorganizational Power”, ASQ 16(2), 1971, pp. 216–229",
               "",
               "画面为示意插画，人物无具体原型；部分细节为二手转述或推论，已在片中标明"]
        for k, s_ in enumerate(src):
            fn = "sans" if any("一" <= ch <= "鿿" for ch in s_) else "garamond"
            draw_text(c, s_, 540, 540 + k * 62, fn, 27 if fn == "sans" else 31, INK2, sa, align="center")
