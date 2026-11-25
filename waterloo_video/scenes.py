# -*- coding: utf-8 -*-
"""Scene renderers. Each: fn(ctx, S) draws the full frame under the overlays."""
import math
import numpy as np
import cairo
from gfx import *
from frame import S, quote_card, panel, big_number, legend, PLATE_CY
from geo import BIG, FIELD, TOWNS, PLACES, build_bigmap, build_field, draw_big_labels
import illus

_M = {}


def bigmap():
    if "big" not in _M:
        _M["big"] = build_bigmap()
    return _M["big"]


def fieldmap():
    if "field" not in _M:
        _M["field"] = build_field()
    return _M["field"]


def B(name):
    lo, la, _ = TOWNS[name]
    return BIG(lo, la)


def F(name):
    return FIELD(*PLACES[name])


def Fll(lon, lat):
    return FIELD(lon, lat)


def Bll(lon, lat):
    return BIG(lon, lat)


# ---------------------------------------------------------------- camera
class Cam:
    def __init__(self, S, keys, tr=2.2):
        """keys: [(cue_or_None, (cx, cy), zoom)]"""
        cx, cy = keys[0][1]; z = keys[0][2]
        for cue, (x, y), zz in keys[1:]:
            k = S.p(cue, tr)
            cx, cy, z = lerp(cx, x, k), lerp(cy, y, k), lerp(z, zz, k)
        self.cx, self.cy, self.z = cx, cy, z

    def apply(self, ctx):
        ctx.translate(W / 2, PLATE_CY); ctx.scale(self.z, self.z); ctx.translate(-self.cx, -self.cy)

    def sc(self, p):
        return (W / 2 + (p[0] - self.cx) * self.z, PLATE_CY + (p[1] - self.cy) * self.z)


def map_base(ctx, surf, cam, dim=0.0):
    fill_bg(ctx)
    ctx.save(); cam.apply(ctx)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint()
    ctx.restore()
    if dim > 0:
        ctx.set_source_rgba(0, 0, 0, dim); ctx.paint()


def burst(ctx, x, y, t, r=40, alpha=1.0, color=FIRE, seed=0):
    """flickering gunfire/explosion marker in screen coords"""
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


def sp(cam, pts):
    return [cam.sc(p) for p in pts]


def ruler(ctx, a, b, txt, alpha=1.0, color=IVORY):
    if alpha <= 0:
        return
    ctx.save(); ctx.set_dash([6, 8]); ctx.set_line_width(3)
    ctx.move_to(*a); ctx.line_to(*b); ctx.set_source_rgba(*color, 0.85 * alpha); ctx.stroke(); ctx.restore()
    for p in (a, b):
        ctx.arc(p[0], p[1], 6, 0, 6.3); ctx.set_source_rgba(*color, alpha); ctx.fill()
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    text(ctx, txt, mx, my - 30, 34, color, alpha, "mm", bold=True, halo=8)


def icon_letter(ctx, x, y, s=1.0, alpha=1.0, color=IVORY):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -46, -32, 92, 64, 6); ctx.set_source_rgba(0.85, 0.78, 0.62, alpha); ctx.fill_preserve()
    ctx.set_source_rgba(0.2, 0.15, 0.1, alpha); ctx.set_line_width(3); ctx.stroke()
    ctx.move_to(-46, -32); ctx.line_to(0, 6); ctx.line_to(46, -32); ctx.stroke()
    ctx.arc(0, 8, 9, 0, 6.3); ctx.set_source_rgba(0.6, 0.1, 0.08, alpha); ctx.fill()
    ctx.restore()


def icon_clock(ctx, x, y, r, hh, mm, alpha=1.0, color=IVORY):
    ctx.new_path()
    ctx.arc(x, y, r, 0, 6.3); ctx.set_source_rgba(0.05, 0.05, 0.06, 0.8 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.set_line_width(4); ctx.stroke()
    for k in range(12):
        a = k * math.pi / 6
        ctx.move_to(x + math.cos(a) * r * 0.82, y + math.sin(a) * r * 0.82); ctx.line_to(x + math.cos(a) * r * 0.94, y + math.sin(a) * r * 0.94)
    ctx.set_line_width(3); ctx.stroke()
    am = mm / 60 * 2 * math.pi - math.pi / 2
    ah = ((hh % 12) + mm / 60) / 12 * 2 * math.pi - math.pi / 2
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(7); ctx.move_to(x, y); ctx.line_to(x + math.cos(ah) * r * 0.5, y + math.sin(ah) * r * 0.5); ctx.stroke()
    ctx.set_line_width(4); ctx.move_to(x, y); ctx.line_to(x + math.cos(am) * r * 0.78, y + math.sin(am) * r * 0.78); ctx.stroke()


def cross(ctx, x, y, r, alpha=1.0, color=AL):
    ctx.set_line_width(10); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_source_rgba(*color, alpha)
    ctx.move_to(x - r, y - r); ctx.line_to(x + r, y + r); ctx.move_to(x - r, y + r); ctx.line_to(x + r, y - r); ctx.stroke()


def tag(ctx, s, x, y, color, alpha=1.0, size=30):
    """colored pill label"""
    if alpha <= 0:
        return
    font(ctx, size, bold=True)
    w = text_w(ctx, s) + 28
    rrect(ctx, x - w / 2, y - size * 0.75, w, size * 1.5, size * 0.4)
    ctx.set_source_rgba(*[c * 0.55 for c in color], 0.92 * alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*color, alpha); ctx.set_line_width(2); ctx.stroke()
    text(ctx, s, x, y, size, IVORY, alpha, "mm", bold=True)


def card_text(ctx, lines, y, alpha=1.0, size=46, color=IVORY, gap=1.45, bold=True):
    for i, L in enumerate(lines):
        text(ctx, L, W / 2, y + i * size * gap, size, color, alpha, "mm", bold=bold, serif=True, halo=8, halo_a=0.6)


# ================================================================ s00 / s13b : dusk illustration
def sc_guard(ctx, S):
    t = S.t
    adv = 0.45 + 0.35 * clamp(t / max(S.c0("rise"), 1)) + 0.15 * S.p("rise", 3)
    ret = S.p("recule", 2.5) * 0.6 + S.p("rout", 4) * 0.6
    illus.draw_dusk(ctx, t, adv, rise=S.p("rise", 1.5), fire=S.span("rise", 0.3, "rout") * (0.5 + 0.5 * math.sin(t * 13)),
                    retreat=ret, scatter=S.p("rout", 4), red=S.span("recule", 0.2, "rout") * 0.6 + S.p("rout", 2) * 0.3,
                    shake=S.span("recule", 0.15) * 0.8 + S.p("rout", 1) * 0.3 * (1 - S.p("rout", 6, 2)))
    if t < 2.0:     # first-frame title punch
        a = 1.0 if t < 1.4 else clamp((2.0 - t) / 0.6)
        text(ctx, "1815 · 6 · 18", W / 2, 470, 96, GOLD, a, "mm", bold=True, serif=True, halo=12)
        text(ctx, "滑铁卢 · 傍晚七点多", W / 2, 580, 52, IVORY, a, "mm", serif=True, halo=10)
    a = S.span("climb2", 0.4)
    tag(ctx, "帝国近卫军", 330, 600, FR, a, 36)
    a = S.span("recule", 0.15, "rout")
    if a > 0:
        text(ctx, "La Garde recule !", W / 2, 560, 92, (1, 0.92, 0.8), a, "mm", family=LATIN_I, italic=True, halo=14)
        text(ctx, "“近卫军后退了！”", W / 2, 680, 64, (1, 0.85, 0.7), a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "据记载 · 战场呼喊（多份法方回忆）", W / 2, 760, 28, GOLD, a, "mm", halo=6)
    a = S.p("rout", 1.0, 1.5)
    big_number(ctx, "七万多人", "天黑前 全线溃散", W / 2, 560, a * (1 - S.p("rout", 0.8, 8.0)), (1, 0.85, 0.7), 110)


# ================================================================ s01 hook map
def sc_hookmap(ctx, S):
    t = S.t
    cam = Cam(S, [(None, B("瓦弗尔"), 0.95), ("grouchy2", ((B("滑铁卢")[0] + B("让布卢")[0]) / 2, B("瓦尔安")[1] - 40), 1.25),
                  ("three", (B("瓦弗尔")[0] - 80, B("瓦弗尔")[1] + 80), 1.0)])
    map_base(ctx, bigmap(), cam, dim=0.15 + 0.45 * S.p("three", 1.0) - 0.0)
    ctx.save(); cam.apply(ctx)
    gr = [Bll(4.62, 50.52), B("让布卢"), (B("瓦尔安")[0] - 10, B("瓦尔安")[1] + 30), Bll(4.66, 50.66), Bll(4.635, 50.70)]
    dashed(ctx, gr, S.lin("grouchy", 6), FR, 9 / cam.z, 1.0, offset=-t * 30)
    pr = [B("瓦弗尔"), Bll(4.55, 50.712), B("圣朗贝尔"), Bll(4.445, 50.675)]
    arrow(ctx, pr, S.p("prussia", 3.0), PR, 40 / cam.z * 1.0)
    ctx.restore()
    draw_labels_big(ctx, cam, 1 - S.p("three", 0.8) * 0.6)
    if S.on("grouchy2") and not S.on("three"):
        a = S.span("grouchy2", 0.6, "prussia") + 0.0
        g = cam.sc(B("瓦尔安"))
        tag(ctx, "格鲁希 · 约三万三千人", g[0] + 10, g[1] + 90, FR, S.p("grouchy2", 0.6))
        ruler(ctx, cam.sc(B("瓦尔安")), cam.sc(Bll(4.433, 50.665)), "约二十公里", S.p("grouchy2", 1.0, 1.2) * (1 - S.p("prussia", 0.6)))
    if S.on("prussia") and not S.on("three"):
        p = cam.sc(B("圣朗贝尔"))
        tag(ctx, "普鲁士军", p[0], p[1] - 70, PR, S.p("prussia", 0.6, 1.0))
    # three cards
    if S.on("three"):
        a = S.p("three", 0.6) * (1 - S.p("q", 0.5))
        items = [("推迟", "开战晚了几个小时"), ("晚到", "一封含混的信"), ("孤军", "骑兵冲锋没人跟上")]
        for i, (h, s) in enumerate(items):
            k = S.p("three", 0.6, i * 1.6) * a / max(a, 1e-6) * a
            y = 560 + i * 230
            panel(ctx, 140, y - 90, 800, 180, k)
            text(ctx, h, 260, y, 70, GOLD, k, "mm", bold=True, serif=True)
            text(ctx, s, 380, y, 46, IVORY, k, "lm", serif=True)
        if S.on("three2"):
            ctx.set_source_rgba(0.75, 0.15, 0.1, 0.9 * a * S.p("three2", 0.6, 1.5)); ctx.set_line_width(6)
            ctx.move_to(940, 470); ctx.curve_to(1010, 600, 1010, 900, 940, 1030); ctx.stroke()
            text(ctx, "同一天", 990, 1080, 36, (1, 0.6, 0.5), a * S.p("three2", 0.6, 1.5), "rm", bold=True)
    if S.on("q"):
        a = S.p("q", 0.6) * (1 - S.p("aust", 0.5))
        text(ctx, "不问", W / 2, 600, 48, DIM, a, "mm", serif=True)
        text(ctx, "拿破仑为什么输", W / 2, 680, 64, DIM, a, "mm", serif=True, bold=True)
        ctx.set_source_rgba(*AL, a); ctx.set_line_width(6); ctx.move_to(300, 684); ctx.line_to(780, 684); ctx.stroke()
        text(ctx, "只问", W / 2, 840, 48, GOLD, a * S.p("q", 0.6, 3.0), "mm", serif=True)
        text(ctx, "他为什么调不动自己的军队", W / 2, 930, 64, IVORY, a * S.p("q", 0.6, 3.0), "mm", serif=True, bold=True, halo=8)
    if S.on("aust"):
        a = S.p("aust", 0.6)
        panel(ctx, 70, 480, 450, 560, a, GOLD)
        panel(ctx, 560, 480, 450, 560, a * S.p("aust2", 0.6), FR)
        text(ctx, "1805", 295, 580, 84, GOLD, a, "mm", bold=True, serif=True)
        text(ctx, "奥斯特利茨", 295, 680, 50, IVORY, a, "mm", serif=True)
        text(ctx, "调动对手", 295, 820, 42, IVORY, a, "mm")
        text(ctx, "如臂使指", 295, 885, 42, GOLD, a, "mm", bold=True)
        b = a * S.p("aust2", 0.6)
        text(ctx, "1815", 785, 580, 84, FR, b, "mm", bold=True, serif=True)
        text(ctx, "滑铁卢", 785, 680, 50, IVORY, b, "mm", serif=True)
        text(ctx, "同一个人", 785, 820, 42, IVORY, b, "mm")
        text(ctx, "处处慢半拍", 785, 885, 42, (1, 0.6, 0.5), b, "mm", bold=True)


def draw_labels_big(ctx, cam, alpha=1.0, only=None):
    for nm in TOWNS:
        if only and nm not in only:
            continue
        x, y = cam.sc(B(nm))
        if -100 < x < W + 100 and 250 < y < 1400:
            sz = TOWNS[nm][2]
            fs = (30, 36, 44)[sz]; r = (6, 8, 11)[sz]
            ctx.arc(x, y, r + 3, 0, 6.3); ctx.set_source_rgba(0, 0, 0, 0.7 * alpha); ctx.fill()
            ctx.arc(x, y, r, 0, 6.3); ctx.set_source_rgba(*IVORY, alpha); ctx.fill()
            left = nm in ("滑铁卢", "圣让山", "四臂村", "热纳普", "尼韦勒")
            text(ctx, nm, x + (-1 if left else 1) * (r + 12), y, fs, IVORY, alpha, "rm" if left else "lm", bold=sz == 2, halo=fs * 0.3, halo_a=0.9)


# ================================================================ s02 / s03 / s06 campaign map
CAMPAIGN_KEYS = {
    "s02": [(None, (900, 1000), 0.62), ("two", (850, 900), 0.62), ("jun16", (B("四臂村")[0] + 120, B("利尼")[1] - 60), 1.05),
            ("derlon", ((B("四臂村")[0] + B("利尼")[0]) / 2, B("利尼")[1] - 10), 1.35)],
    "s03": [(None, (B("利尼")[0], B("利尼")[1] - 80), 0.95), ("gneis", (B("瓦弗尔")[0] - 40, B("让布卢")[1] - 160), 0.82),
            ("detach", (B("让布卢")[0] - 40, B("让布卢")[1] - 60), 1.05), ("blue", (B("瓦弗尔")[0] - 30, B("瓦尔安")[1] - 20), 0.92),
            ("wel", ((B("圣让山")[0] + B("瓦弗尔")[0]) / 2, B("圣让山")[1] + 60), 0.92)],
    "s06": [(None, ((B("圣让山")[0] + B("圣朗贝尔")[0]) / 2, B("圣让山")[1] + 30), 1.6),
            ("choice", ((B("圣让山")[0] + B("瓦尔安")[0]) / 2, B("瓦尔安")[1] - 50), 1.05)],
}


def sc_campaign(ctx, S):
    t = S.t
    sid = S.scene["id"]
    cam = Cam(S, CAMPAIGN_KEYS[sid])
    dim = 0.0
    if sid == "s06":
        dim = 0.55 * S.span("soultletter", 0.6, "ride") if S.on("soultletter") else 0
    map_base(ctx, bigmap(), cam, dim)
    ctx.save(); cam.apply(ctx)
    z = cam.z
    if sid == "s02":
        aw = S.p("two", 1.5)
        # allied cantonments
        for lo, la in [(4.33, 50.62), (4.40, 50.70), (4.30, 50.68)]:
            x, y = Bll(lo, la)
            ctx.arc(x, y, 70, 0, 6.3); ctx.set_source_rgba(*AL, 0.25 * aw); ctx.fill()
        for lo, la in [(4.62, 50.50), (4.80, 50.47), (4.70, 50.56)]:
            x, y = Bll(lo, la)
            ctx.arc(x, y, 70, 0, 6.3); ctx.set_source_rgba(*PR, 0.3 * aw); ctx.fill()
        # wedge
        w1 = [B("沙勒罗瓦"), Bll(4.45, 50.47), Bll(4.452, 50.555)]
        w2 = [B("沙勒罗瓦"), Bll(4.50, 50.46), Bll(4.565, 50.505)]
        arrow(ctx, w1, S.p("wedge", 2.5), FR, 40 / z)
        arrow(ctx, w2, S.p("wedge", 2.5, 0.6), FR, 40 / z)
        if S.on("jun16"):
            q = B("四臂村"); l = B("利尼")
        # d'Erlon shuttle
        if S.on("derlon"):
            a0 = Bll(4.47, 50.49)
            a1 = Bll(4.545, 50.51)
            a2 = Bll(4.458, 50.556)
            k1 = S.p("derlon2", 3.0); k2 = S.p("derlon2", 3.0, 3.2)
            route = [a0, Bll(4.51, 50.50), a1]
            back = [a1, Bll(4.50, 50.53), a2]
            dashed(ctx, route, k1, FR, 7 / z, 0.9, offset=-t * 20)
            dashed(ctx, back, k2, FR, 7 / z, 0.9, offset=-t * 20)
            if k2 > 0:
                x, y = cut(smooth(back), k2)[-1]
            elif k1 > 0:
                x, y = cut(smooth(route), k1)[-1]
            else:
                x, y = a0
            unit_block(ctx, x, y, 46 / z, 30 / z, FR, S.p("derlon", 0.6))
    if sid in ("s03", "s06"):
        # Prussian retreat north
        pr = [B("利尼"), Bll(4.585, 50.57), Bll(4.60, 50.65), (B("瓦弗尔")[0] - 4, B("瓦弗尔")[1] + 20)]
        pk = S.p("gneis", 3.0) if sid == "s03" else 1
        arrow(ctx, pr, pk, PR, 46 / z)
        # french cavalry east (wrong)
        if sid == "s03":
            ea = [Bll(4.60, 50.50), Bll(4.70, 50.49), Bll(4.80, 50.475)]
            dashed(ctx, ea, S.lin("east", 3.0), FR, 7 / z, 0.9 * (1 - 0.6 * S.p("detach", 1)), offset=-t * 25)
        # Grouchy
        gstart = Bll(4.60, 50.525)
        gr = [gstart, B("让布卢"), Bll(4.69, 50.60), (B("瓦尔安")[0] - 5, B("瓦尔安")[1] + 5), Bll(4.66, 50.67), Bll(4.635, 50.70)]
        if sid == "s03":
            gk = 0.22 * S.lin("rain", 4) + 0.18 * S.lin("blue", 4)
        else:
            gk = 0.55 + 0.25 * S.lin("see", 30)
        dashed(ctx, gr, gk, FR, 9 / z, 1.0, offset=-t * 30)
        if sid == "s03":
            gx, gy = cut(smooth(gr), max(gk, 0.001))[-1]
            unit_block(ctx, gx, gy, 54 / z, 34 / z, FR, S.p("detach", 0.8))
        # wavre concentration
        wv = B("瓦弗尔")
        if sid == "s06" or S.on("blue"):
            for i, (dx, dy) in enumerate([(-50, -30), (30, -45), (-10, 30), (60, 25)]):
                unit_block(ctx, wv[0] + dx / z * 0.9, wv[1] + dy / z * 0.9, 40 / z, 26 / z, PR, S.p("blue", 1.0, i * 0.3) if sid == "s03" else 1)
        # Wellington retreat
        if sid == "s06" or S.on("wel"):
            wr = [B("四臂村"), Bll(4.452, 50.611), Bll(4.416, 50.665), Bll(4.408, 50.684)]
            arrow(ctx, wr, S.p("wel", 3.0) if sid == "s03" else 1, AL, 46 / z)
        if sid == "s06":
            # Bülow appears at Saint-Lambert
            bl = [Bll(4.56, 50.712), B("圣朗贝尔"), Bll(4.465, 50.682)]
            arrow(ctx, bl, 0.55 + 0.45 * S.p("hussar", 3), PR, 40 / z)
            # two options
            if S.on("choice"):
                o1 = [(B("瓦尔安")[0], B("瓦尔安")[1]), Bll(4.60, 50.64), Bll(4.47, 50.65)]
                arrow(ctx, o1, S.p("choice", 2) * (0.6 if S.on("both") else 1), FR, 30 / z, alpha=0.9)
        ctx.restore()
        if sid == "s03":
            draw_labels_big(ctx, cam, 1.0)
            if S.on("gneis"):
                p = cam.sc(Bll(4.60, 50.63))
                tag(ctx, "格奈森瑙：向北", p[0] + 140, p[1], PR, S.span("gneis", 0.6, "east"))
            if S.on("east"):
                p = cam.sc(Bll(4.78, 50.49))
                tag(ctx, "向东？", p[0], p[1] - 60, FR, S.span("east", 0.5, "detach"))
            if S.on("detach"):
                p = cam.sc(B("让布卢"))
                tag(ctx, "格鲁希 · 约三万三千人", p[0] + 60, p[1] + 90, FR, S.span("detach", 0.6, "rain"))
            if S.on("rain") and not S.on("blue"):
                illus.rain(ctx, t, 0.8, 0.35 * S.span("rain", 0.8, "blue"))
            if S.on("wel2"):
                a = S.p("wel2", 1.0)
                ruler(ctx, cam.sc(B("圣让山")), cam.sc(B("瓦弗尔")), "约十五公里", a, PR)
                legend(ctx, [(FR, "法军"), (AL, "英荷联军"), (PR, "普军")], a)
        else:
            draw_labels_big(ctx, cam, 1.0)
            if not S.on("choice"):
                # telescope view
                a = S.span("see", 0.8, "choice")
                if a > 0:
                    p = cam.sc(B("圣朗贝尔"))
                    ctx.save(); ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
                    ctx.rectangle(0, 0, W, H); ctx.arc(p[0], p[1], 210, 0, 6.3)
                    ctx.set_source_rgba(0, 0, 0, 0.65 * a); ctx.fill(); ctx.restore()
                    ctx.arc(p[0], p[1], 210, 0, 6.3); ctx.set_source_rgba(*GOLD, 0.8 * a); ctx.set_line_width(4); ctx.stroke()
                    if S.on("stl"):
                        text(ctx, "“是格鲁希吗？”", p[0], p[1] + 260, 44, IVORY, a * S.p("stl", 0.6, 2.5), "mm", serif=True, halo=8)
                if S.on("hussar"):
                    a = S.span("hussar", 0.5, "choice")
                    icon_letter(ctx, 300, 1060, 1.2, a)
                    text(ctx, "截获：比洛致威灵顿", 380, 1060, 34, IVORY, a, "lm", halo=8)
                    text(ctx, "（据法方记载）", 380, 1105, 26, GOLD, a, "lm", halo=6)
            else:
                a = S.p("choice", 0.6) * (1 - S.p("soultletter", 0.6))
                for i, (s1, s2, c) in enumerate([("A", "叫回格鲁希", FR), ("B", "抢先打垮威灵顿", AL)]):
                    y = 520 + i * 150
                    panel(ctx, 160, y - 60, 760, 120, a)
                    text(ctx, s1, 230, y, 60, c, a, "mm", bold=True)
                    text(ctx, s2, 300, y, 46, IVORY, a, "lm", serif=True)
                    if S.on("both"):
                        k = S.p("both", 1.0, 0.4 + i * 0.5)
                        ctx.rectangle(640, y - 14, 240, 28); ctx.set_source_rgba(0.2, 0.2, 0.2, a); ctx.fill()
                        ctx.rectangle(640, y - 14, 240 * 0.5 * k, 28); ctx.set_source_rgba(*c, a); ctx.fill()
                        text(ctx, "只做了一半", 760, y + 40, 26, DIM, a * k, "mm")
                if S.on("soultletter"):
                    letter_card(ctx, S)
    else:
        ctx.restore()
        draw_labels_big(ctx, cam, 1.0)
        a = S.span("elba", 0.6, "two") + 0 * t
        if S.on("elba") and not S.on("two"):
            a = S.span("elba", 0.6, "two")
            panel(ctx, 140, 440, 800, 230, a)
            text(ctx, "1815 年", W / 2, 510, 64, GOLD, a, "mm", bold=True, serif=True, halo=10)
            text(ctx, "三月 回到巴黎 · 六月 北上比利时", W / 2, 610, 40, IVORY, S.span("elba2", 0.6, "two"), "mm", halo=8)
        if S.on("two"):
            a = S.span("two", 0.6, "jun16")
            p = cam.sc(Bll(4.36, 50.67)); tag(ctx, "威灵顿 · 英荷联军", p[0], p[1] - 110, AL, a)
            p = cam.sc(Bll(4.72, 50.50)); tag(ctx, "布吕歇尔 · 普军", p[0], p[1] + 110, PR, a)
            legend(ctx, [(FR, "法军"), (AL, "英荷联军"), (PR, "普军")], S.p("two", 0.6))
        if S.on("wedge") and not S.on("jun16"):
            p = cam.sc(B("沙勒罗瓦"))
            tag(ctx, "插进两军之间", p[0], p[1] - 330, FR, S.span("wedge", 0.6, "jun16"))
        if S.on("jun16"):
            a = S.span("jun16", 0.6, "derlon")
            q = cam.sc(B("四臂村")); l = cam.sc(B("利尼"))
            burst(ctx, q[0], q[1], t, 50 * cam.z, a * 0.9, seed=1)
            burst(ctx, l[0], l[1], t, 60 * cam.z, a * 0.9, seed=4)
            text(ctx, "6月16日", W / 2, 470, 46, GOLD, a, "mm", bold=True, halo=8)
            if S.on("ligny"):
                tag(ctx, "利尼：法军胜，普军未散", l[0], l[1] + 110, FR, S.p("ligny", 0.6) * a)
        if S.on("derlon"):
            a = S.p("derlon", 0.6)
            tag(ctx, "德隆第一军 · 约两万人", W / 2, 520, FR, a * (1 - S.p("derlon3", 0.5)))
            if S.on("derlon3"):
                text(ctx, "命令在路上跑", W / 2, 520, 56, IVORY, S.p("derlon3", 0.6), "mm", bold=True, serif=True, halo=10)
                text(ctx, "比士兵跑得还乱", W / 2, 600, 56, (1, 0.6, 0.5), S.p("derlon3", 0.6, 0.6), "mm", bold=True, serif=True, halo=10)


def letter_card(ctx, S):
    a = S.p("soultletter", 0.7)
    x0, y0, w, h = 70, 430, 940, 760
    rrect(ctx, x0, y0, w, h, 10); ctx.set_source_rgba(0.80, 0.72, 0.56, 0.96 * a); ctx.fill()
    ctx.set_source_rgba(0.35, 0.25, 0.15, a); ctx.set_line_width(3); rrect(ctx, x0 + 14, y0 + 14, w - 28, h - 28, 6); ctx.stroke()
    ink = (0.18, 0.12, 0.08)
    text(ctx, "Du champ de bataille de Waterloo,", 110, y0 + 70, 32, ink, a, "lm", family=LATIN_I, italic=True)
    text(ctx, "le 18, à une heure après midi", 110, y0 + 115, 32, ink, a, "lm", family=LATIN_I, italic=True)
    text(ctx, "苏尔特致格鲁希 · 下午一点", W - 110, y0 + 160, 28, (0.45, 0.12, 0.08), a, "rm", bold=True)
    yb = y0 + 240
    kb = S.p("body", 0.6)
    text(ctx, "正文：往瓦弗尔走，“符合皇帝的安排”", 110, yb, 38, ink, a * kb, "lm", bold=True)
    kp = S.p("body", 0.6, 3.5)
    text(ctx, "P. S. … ne perdez pas un instant pour vous", 110, yb + 90, 32, ink, a * kp, "lm", family=LATIN_I, italic=True)
    text(ctx, "rapprocher de nous et nous joindre …", 110, yb + 132, 32, ink, a * kp, "lm", family=LATIN_I, italic=True)
    text(ctx, "附言：一刻也别耽误，向我们靠拢", 110, yb + 190, 38, (0.45, 0.10, 0.06), a * kp, "lm", bold=True)
    kw = S.p("which", 0.6)
    if kw > 0:
        ctx.set_source_rgba(0.6, 0.1, 0.05, a * kw); ctx.set_line_width(5)
        ctx.arc(W / 2, yb + 290, 0, 0, 0)
        text(ctx, "往北追？ 还是往西靠？", W / 2, yb + 290, 46, (0.55, 0.08, 0.05), a * kw, "mm", bold=True, serif=True)
        k2 = S.p("which", 0.6, 4.5)
        text(ctx, "« la bataille est gagnée »  /  « engagée »", W / 2, yb + 380, 32, ink, a * k2, "mm", family=LATIN_I, italic=True)
        text(ctx, "已经打赢？ / 已经打响？——抄本不一", W / 2, yb + 430, 32, ink, a * k2, "mm", bold=True)
    text(ctx, "据格鲁希 1819 年刊本、乌赛《1815：滑铁卢》所录；措辞各本有出入", W / 2, y0 + h - 40, 22, (0.35, 0.25, 0.15), a, "mm")


# ================================================================ s04 rain & mud
def sc_rain(ctx, S):
    t = S.t
    zoom = 1.0 + 0.6 * (1 - S.p("mud", 3.0)) if not S.on("gun") else 1.0
    paint_surface(ctx, illus.mud_bg(), 0, 0)
    ctx.set_source_rgba(0.02, 0.03, 0.06, 0.45 * (1 - S.p("mud", 2.5))); ctx.paint()
    sink = 30 + 30 * S.p("gun2", 2)
    ctx.save()
    ctx.translate(W / 2, 1000); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -1000)
    illus.cannon_side(ctx, 520, 1060, 2.3, 1.0, sink=sink)
    ctx.restore()
    illus.rain(ctx, t, 1.2, 0.45 * (1 - 0.5 * S.p("wait", 2)))
    if S.on("night") and not S.on("mud"):
        text(ctx, "6月17日 夜", W / 2, 520, 56, IVORY, S.span("night", 0.6, "mud"), "mm", bold=True, serif=True, halo=10)
    if S.on("gun"):
        a = S.span("gun", 0.6, "wait")
        tag(ctx, "炮兵出身", 300, 560, FR, a)
    if S.on("gun2"):
        a = S.span("gun2", 0.6, "wait")
        # ricochet illustration: ball sinks
        x = 200 + 600 * clamp((t - S.c0("gun2")) / 2.5 % 1.0)
        yb = 700 + 140 * min(1, (x - 200) / 300)
        ctx.arc(x, yb, 14, 0, 6.3); ctx.set_source_rgba(0.05, 0.05, 0.05, a); ctx.fill()
        text(ctx, "炮弹陷进泥里，不再弹跳", W / 2, 520, 44, IVORY, a, "mm", bold=True, halo=8)
    if S.on("wait"):
        a = S.span("wait", 0.6, "soult")
        k = S.lin("wait", S.c1("wait") - S.c0("wait"))
        mins = 9 * 60 + int(150 * k)
        icon_clock(ctx, W / 2, 680, 150, mins // 60, mins % 60, a)
        text(ctx, "原定上午 → 一推再推", W / 2, 900, 44, IVORY, a, "mm", bold=True, halo=8)
    if S.on("soult"):
        a = S.span("soult", 0.6, "calc")
        quote_card(ctx, "« Wellington est un mauvais général, les Anglais sont de mauvaises troupes, et ce sera l'affaire d'un déjeuner. »",
                   "这一仗，不过是吃顿早饭的事。", "据苏尔特副官博杜（Baudus）手稿，乌赛《1815：滑铁卢》转述",
                   a * S.p("soult2", 0.6), y=760, orig_size=34, zh_size=50)
        if not S.on("soult2"):
            text(ctx, "苏尔特：叫回格鲁希一部分", W / 2, 700, 48, IVORY, a, "mm", bold=True, halo=10)
    if S.on("calc"):
        a = S.p("calc", 0.6)
        items = ["普军两天之内缓不过来", "格鲁希会缠住普军"]
        for i, s in enumerate(items):
            y = 620 + i * 150
            panel(ctx, 140, y - 60, 800, 120, a)
            text(ctx, s, 200, y, 46, IVORY, a, "lm", serif=True)
            if S.on("wrong"):
                cross(ctx, 870, y, 30, S.p("wrong", 0.4, i * 0.4))


# ================================================================ battlefield map scenes
FIELD_KEYS = {
    "s05": [(None, (FIELD.w / 2, FIELD.h / 2), 0.62), ("reverse", (F("拉艾圣")[0], F("拉艾圣")[1] - 60), 0.85),
            ("points", (FIELD.w * 0.47, FIELD.h * 0.52), 0.70), ("hougo", (F("乌古蒙")[0] + 120, F("乌古蒙")[1] - 40), 1.05),
            ("clock", (FIELD.w * 0.6, FIELD.h * 0.5), 0.66)],
    "s09": [(None, (F("拉艾圣")[0] + 60, F("拉艾圣")[1] + 30), 0.78), ("same", (F("拉艾圣")[0] + 60, F("拉艾圣")[1]), 0.80)],
    "s11": [(None, ((F("美丽联盟")[0] + F("普朗斯努瓦")[0]) / 2 + 120, F("普朗斯努瓦")[1] - 40), 0.70),
            ("split", (FIELD.w * 0.55, FIELD.h * 0.52), 0.68)],
    "s12": [(None, (F("拉艾圣")[0] + 30, F("拉艾圣")[1] - 10), 0.95), ("ask", (F("拉艾圣")[0] + 80, F("拉艾圣")[1] + 60), 0.78),
            ("gone", (FIELD.w * 0.55, FIELD.h * 0.52), 0.68)],
    "s13": [(None, (FIELD.w * 0.62, FIELD.h * 0.45), 0.70)],
    "s15": [(None, (FIELD.w * 0.55, FIELD.h * 0.5), 0.68), ("meet", (F("美丽联盟")[0], F("美丽联盟")[1]), 0.9)],
}

ALLIED_LINE = [(4.385, 50.6855), (4.398, 50.6852), (4.411, 50.6848), (4.425, 50.6845), (4.440, 50.6838)]
FRENCH_LINE = [(4.388, 50.6690), (4.402, 50.6693), (4.416, 50.6705), (4.428, 50.6705), (4.440, 50.6700)]


def draw_lines_base(ctx, z, S, allied_a=1.0, french_a=1.0, thin=0.0, lhs_lost=False):
    for i, (lo, la) in enumerate(ALLIED_LINE):
        x, y = Fll(lo, la)
        for j in range(3):
            if thin > 0 and (i + j) % 2 == 0 and 1 <= i <= 3:
                aa = allied_a * (1 - thin * 0.8)
            else:
                aa = allied_a
            unit_block(ctx, x - 45 + j * 45, y + (j % 2) * 10, 38, 22, AL, aa)
    for i, (lo, la) in enumerate(FRENCH_LINE):
        x, y = Fll(lo, la)
        for j in range(3):
            unit_block(ctx, x - 45 + j * 45, y + (j % 2) * 10, 38, 22, FR, french_a)


def sc_field(ctx, S):
    t = S.t
    sid = S.scene["id"]
    cam = Cam(S, FIELD_KEYS[sid])
    z = cam.z
    map_base(ctx, fieldmap(), cam, 0.0)
    ctx.save(); cam.apply(ctx)
    hs, lhs, pl, ba = F("乌古蒙"), F("拉艾圣"), F("普朗斯努瓦"), F("美丽联盟")
    if sid == "s05":
        draw_lines_base(ctx, z, S, S.p("reverse", 1.2), S.p("points", 1.2))
        if S.on("hougo"):
            for i in range(4 + int(4 * S.p("hougo2", 4))):
                k = S.p("hougo", 2.0, i * 0.7)
                st = (hs[0] - 60 + i * 30, hs[1] + 300)
                arrow(ctx, [st, (hs[0] - 20 + i * 12, hs[1] + 140), (hs[0] - 10 + i * 8, hs[1] + 40)], k, FR, 26)
        if S.on("wavre"):
            bl = [(FIELD.w + 60, 60), (FIELD.w - 160, 180), (FIELD.w - 260, 300)]
            arrow(ctx, bl, 0.35 + 0.1 * math.sin(t * 2) * 0.1 + 0.05 * S.p("wavre", 2), PR, 36)
    elif sid == "s09":
        draw_lines_base(ctx, z, S, 1, 1)
        # grand battery
        gb = [Fll(4.408 + i * 0.0025, 50.6735) for i in range(7)]
        for i, (x, y) in enumerate(gb):
            unit_block(ctx, x, y, 30, 20, FR, S.p("battery", 0.6, i * 0.1), kind="art")
        # d'Erlon columns
        cols = [Fll(4.414 + i * 0.006, 50.6700) for i in range(4)]
        adv = S.p("derlon", 6.0) * 0.8 + S.p("stand", 2.0) * 0.2
        brk = S.p("cav", 2.0, 1.5)
        for i, (x, y) in enumerate(cols):
            yy = y - adv * 330 + brk * 140
            if brk < 0.5:
                ctx.rectangle(x - 34, yy - 60, 68, 120); ctx.set_source_rgba(*FR, 0.9 * S.p("derlon", 1, i * 0.3)); ctx.fill_preserve()
                ctx.set_source_rgba(1, 1, 1, 0.6 * S.p("derlon", 1, i * 0.3)); ctx.set_line_width(2); ctx.stroke()
                for r in range(6):
                    ctx.move_to(x - 30, yy - 50 + r * 20); ctx.line_to(x + 30, yy - 50 + r * 20)
                ctx.set_source_rgba(1, 1, 1, 0.25); ctx.set_line_width(1); ctx.stroke()
            else:
                rng = np.random.default_rng(i)
                for k in range(16):
                    ctx.rectangle(x + rng.uniform(-80, 80), yy + rng.uniform(-60, 120) + brk * 40, 12, 8)
                ctx.set_source_rgba(*FR, 0.8); ctx.fill()
        if S.on("cav"):
            for i in range(2):
                st = Fll(4.405 + i * 0.016, 50.6880)
                arrow(ctx, [st, (st[0] + 10, st[1] + 180), (st[0] + 30, st[1] + 330 + 220 * S.p("cav2", 3))], S.p("cav", 2.0, i * 0.3), AL, 34)
        if S.on("cav2"):
            ln = [Fll(4.432, 50.6690), Fll(4.428, 50.6730), Fll(4.422, 50.6765)]
            arrow(ctx, ln, S.p("cav2", 2.0, 2.5), FR, 30)
    elif sid == "s11":
        draw_lines_base(ctx, z, S, 1, 1)
        bl = [Fll(4.475, 50.6700), Fll(4.458, 50.6660), Fll(4.440, 50.6630)]
        arrow(ctx, bl, S.p("bulow", 3.0), PR, 44)
        bl2 = [Fll(4.478, 50.6610), Fll(4.460, 50.6600), Fll(4.442, 50.6605)]
        arrow(ctx, bl2, S.p("bulow", 3.0, 0.8), PR, 38)
        if S.on("key"):
            rd = [Fll(4.4190, 50.6610), Fll(4.422, 50.648)]
            ctx.set_source_rgba(1, 0.85, 0.4, 0.9 * S.p("key", 0.6)); ctx.set_line_width(14); path(ctx, rd); ctx.stroke()
        if S.on("lobau"):
            unit_block(ctx, pl[0] - 40, pl[1] - 60, 52, 32, FR, S.p("lobau", 0.6))
        if S.on("young"):
            src = Fll(4.418, 50.6640)
            arrow(ctx, [src, (src[0] + 120, src[1] + 20), (pl[0] - 50, pl[1])], S.p("young", 2.5), FR, 34)
            for i in range(3):
                unit_block(ctx, pl[0] - 60 + i * 40, pl[1] + 20, 34, 22, (0.85, 0.7, 0.3), S.p("young", 1.0, 2.5 + i * 0.3))
        if S.on("street"):
            for i in range(5):
                bx, by = pl[0] + math.cos(i * 2.3) * 50, pl[1] + math.sin(i * 1.7) * 35
                ctx.restore()
                q = cam.sc((bx, by))
                burst(ctx, q[0], q[1], t, 30, S.p("street", 0.6) * (1 - 0.6 * S.p("fist", 1)), seed=i)
                ctx.save(); cam.apply(ctx)
    elif sid == "s12":
        draw_lines_base(ctx, z, S, 1, 1, thin=S.p("close", 2.0))
        if S.on("ask"):
            msg = [(lhs[0] + 10, lhs[1] + 60), (lhs[0] + 50, lhs[1] + 200), (ba[0] + 10, ba[1] + 160)]
            dashed(ctx, msg, S.lin("ask", 2.0), FR, 6, 1.0, offset=-t * 20)
        if S.on("close"):
            for i in range(3):
                x0 = lhs[0] - 40 + i * 40
                y0 = lhs[1] + 60 - S.p("close", 2.0) * 90
                unit_block(ctx, x0, y0, 30, 20, FR, S.p("close", 0.6), kind="art")
    elif sid == "s13":
        draw_lines_base(ctx, z, S, 1, 1, thin=0.6)
        zi = [Fll(4.500, 50.700), Fll(4.470, 50.690), Fll(4.445, 50.6835)]
        arrow(ctx, zi, S.p("zieten", 3.0), PR, 44)
        bl = [Fll(4.475, 50.6700), Fll(4.458, 50.6660), Fll(4.440, 50.6630)]
        arrow(ctx, bl, 1.0, PR, 40, alpha=0.8)
        g = [Fll(4.415, 50.6660), Fll(4.410, 50.6720), Fll(4.402, 50.6790)]
        arrow(ctx, g, S.p("last", 3.0, 2.0), (0.85, 0.7, 0.3), 46)
    elif sid == "s15":
        k = S.p("hat", 2.5)
        draw_lines_base(ctx, z, S, 1, 1 - 0.7 * k)
        for i, (lo, la) in enumerate(ALLIED_LINE):
            x, y = Fll(lo, la)
            arrow(ctx, [(x, y + 20), (x + 5, y + 200), (x + 10, y + 380)], k * (0.6 + 0.4 * S.p("press", 2)), AL, 30)
        for i in range(3):
            st = Fll(4.475 - i * 0.004, 50.6720 - i * 0.004)
            arrow(ctx, [st, (st[0] - 150, st[1] + 40), (st[0] - 330, st[1] + 140)], S.p("press", 2.5, i * 0.3), PR, 36)
        if S.on("squares"):
            for i in range(3):
                x, y = Fll(4.416 + (i - 1) * 0.004, 50.6665 - S.p("squares", 6) * 0.006)
                ctx.rectangle(x - 18, y - 18, 36, 36); ctx.set_source_rgba(0.85, 0.7, 0.3, 0.9); ctx.fill()
    ctx.restore()

    # ---- screen-space annotations
    def lab(name, dy=-50, a=1.0, col=IVORY, size=32):
        p = cam.sc(F(name))
        if a > 0:
            text(ctx, name, p[0], p[1] + dy, size, col, a, "mm", bold=True, halo=9)

    if sid == "s05":
        if S.on("field") and not S.on("reverse"):
            text(ctx, "圣让山战场", W / 2, 470, 54, IVORY, S.span("field", 0.6, "reverse"), "mm", bold=True, serif=True, halo=10)
        if S.on("reverse"):
            cross_section(ctx, S, "reverse", S.span("reverse", 0.6, "points"))
        a = S.p("points", 0.8)
        for nm in ("乌古蒙", "拉艾圣", "帕普洛特"):
            p = cam.sc(F(nm))
            pulse_ring(ctx, p[0], p[1], t, GOLD, 34, a * (1 - S.p("hougo", 1)) * 0.9)
            lab(nm, -52, a)
        lab("美丽联盟", 52, a * 0.8, DIM, 26)
        if S.on("planc"):
            p = cam.sc(F("普朗斯努瓦"))
            pulse_ring(ctx, p[0], p[1], t, PR, 50, S.p("planc", 0.6) * (1 - S.p("hougo", 1)))
            lab("普朗斯努瓦", 70, S.p("planc", 0.6), (0.7, 0.9, 0.7))
        if S.on("hougo"):
            p = cam.sc(hs)
            burst(ctx, p[0], p[1] + 10, t, 50, S.p("hougo", 0.5) * (1 - S.p("clock", 1)), seed=2)
            tag(ctx, "11:30 佯攻乌古蒙", W / 2, 470, FR, S.span("hougo", 0.6, "hougo3"))
            if S.on("hougo2"):
                big_number(ctx, "上万人", "被吸在农庄墙下", W / 2, 1060, S.span("hougo2", 0.6, "clock"), IVORY, 80)
        if S.on("clock"):
            a = S.span("clock", 0.6, "wavre")
            icon_clock(ctx, W / 2, 640, 130, 11, 30 + 30 * S.lin("clock", 3), a)
            text(ctx, "每推迟一小时 = 普军多走一小时", W / 2, 840, 42, IVORY, a, "mm", bold=True, halo=10)
        if S.on("wavre"):
            a = S.p("wavre", 0.6)
            panel(ctx, 120, 430, 840, 240, a, PR)
            text(ctx, "比洛第四军 · 瓦弗尔", W / 2, 490, 44, (0.75, 0.95, 0.75), a, "mm", bold=True)
            text(ctx, "城中失火，窄街堵塞，耽误数小时", W / 2, 570, 38, IVORY, a, "mm")
            burst(ctx, 200, 600, t, 30, a, seed=5)
            burst(ctx, 880, 600, t, 30, a, seed=7)
    elif sid == "s09":
        if S.on("battery"):
            tag(ctx, "约 80 门炮", W / 2, 470, FR, S.span("battery", 0.6, "derlon"))
            for i in range(7):
                p = cam.sc(Fll(4.408 + i * 0.0025, 50.6735))
                burst(ctx, p[0], p[1] - 10, t, 28, S.span("battery", 0.3, "derlon") * 0.8, seed=i)
        if S.on("battery2"):
            cross_section(ctx, S, "battery2", S.span("battery2", 0.6, "derlon"))
        if S.on("derlon"):
            tag(ctx, "德隆第一军 · 一万六七千人", W / 2, 470, FR, S.span("derlon", 0.6, "column"))
        if S.on("column"):
            column_diagram(ctx, S, S.span("column", 0.6, "stand"))
        if S.on("stand"):
            for (lo, la) in ALLIED_LINE[1:4]:
                p = cam.sc(Fll(lo, la))
                burst(ctx, p[0], p[1] + 20, t, 40, S.span("stand", 0.2, "cav"), seed=int(lo * 1000))
            tag(ctx, "坡后英军起立齐射", W / 2, 470, AL, S.span("stand", 0.4, "cav"))
        if S.on("cav"):
            tag(ctx, "英军重骑兵冲下山坡", W / 2, 470, AL, S.span("cav", 0.5, "cav2"))
        if S.on("cav2"):
            tag(ctx, "冲过头 · 被法军枪骑兵反击", W / 2, 470, FR, S.span("cav2", 0.5, "same"))
        if S.on("same"):
            a = S.p("same", 0.6)
            panel(ctx, 110, 430, 860, 200, a)
            text(ctx, "同一种错", W / 2, 490, 52, GOLD, a, "mm", bold=True, serif=True)
            text(ctx, "一个兵种单独冲出去，没人跟上", W / 2, 570, 42, IVORY, a, "mm", serif=True)
    elif sid == "s11":
        if S.on("bulow"):
            tag(ctx, "16:30 普军比洛部", W / 2, 470, PR, S.span("bulow", 0.6, "key"))
            lab("普朗斯努瓦", 80, S.p("bulow", 0.6), (0.75, 0.95, 0.75), 36)
        if S.on("key"):
            p = cam.sc(Fll(4.4205, 50.6545))
            tag(ctx, "法军唯一的退路", p[0] - 180, p[1] + 40, GOLD, S.span("key", 0.6, "young"))
        if S.on("lobau"):
            p = cam.sc(pl); tag(ctx, "洛博第六军", p[0] - 160, p[1] - 120, FR, S.span("lobau", 0.6, "young"))
        if S.on("young"):
            tag(ctx, "青年近卫军 + 老近卫军两个营", W / 2, 470, (0.85, 0.7, 0.3), S.span("young", 0.6, "split"))
        if S.on("split"):
            a = S.p("split", 0.6)
            reserve_split(ctx, S, a)
    elif sid == "s12":
        if S.on("lhs"):
            p = cam.sc(lhs)
            burst(ctx, p[0], p[1], t, 46, S.span("lhs", 0.4, "close"), seed=3)
            tag(ctx, "约 18:00–18:30 拉艾圣失守", W / 2, 470, FR, S.span("lhs", 0.6, "close"))
        if S.on("kgl"):
            a = S.span("kgl", 0.6, "close")
            p = cam.sc(lhs)
            panel(ctx, p[0] - 300, p[1] + 90, 600, 150, a, AL)
            text(ctx, "英王德意志军团 · 轻步兵营", p[0], p[1] + 135, 34, IVORY, a, "mm", bold=True)
            text(ctx, "弹药耗尽", p[0], p[1] + 195, 40, (1, 0.6, 0.5), a, "mm", bold=True)
        if S.on("close"):
            tag(ctx, "法军大炮推到中路跟前", W / 2, 470, FR, S.span("close", 0.6, "ask"))
        if S.on("ask"):
            tag(ctx, "内伊：再给我一点步兵！", W / 2, 470, FR, S.span("ask", 0.6, "answer"))
        if S.on("answer"):
            a = S.span("answer", 0.6, "gone")
            panel(ctx, 100, 980, 880, 190, a)
            text(ctx, "“兵？你要我上哪儿给你变出兵来？”", W / 2, 1050, 42, IVORY, a, "mm", bold=True, serif=True)
            text(ctx, "据记载（内伊副官的回忆）", W / 2, 1115, 26, GOLD, a, "mm")
        if S.on("gone"):
            a = S.p("gone", 0.6)
            icon_clock(ctx, W / 2, 620, 120, 18, 30 + 30 * S.lin("gone", 4), a)
            text(ctx, "最好的半小时", W / 2, 800, 52, IVORY, a, "mm", bold=True, serif=True, halo=10)
    elif sid == "s13":
        if S.on("zieten"):
            p = cam.sc(Fll(4.470, 50.690))
            tag(ctx, "齐腾第一军", p[0], p[1] - 70, PR, S.span("zieten", 0.6, "lie"))
        if S.on("last"):
            a = S.span("last", 0.6, "climb")
            text(ctx, "« Voilà Grouchy ! »", W / 2, 520, 60, (1, 0.9, 0.75), a * S.p("last", 0.6, 2.5), "mm", family=LATIN_I, italic=True, halo=10)
            text(ctx, "“格鲁希到了！”", W / 2, 600, 48, IVORY, a * S.p("last", 0.6, 2.5), "mm", bold=True, halo=8)
        if S.on("lie"):
            a = S.span("lie", 0.4, "climb")
            text(ctx, "其实来的是普鲁士人", W / 2, 700, 52, (0.75, 0.95, 0.75), a, "mm", bold=True, halo=10)
    elif sid == "s15":
        if S.on("hat"):
            tag(ctx, "约 20:00 全线出击", W / 2, 470, AL, S.span("hat", 0.6, "squares"))
        if S.on("squares"):
            tag(ctx, "老近卫军方阵掩护后撤", W / 2, 470, (0.85, 0.7, 0.3), S.span("squares", 0.6, "meet"))
        if S.on("meet"):
            p = cam.sc(ba)
            pulse_ring(ctx, p[0], p[1], t, GOLD, 40, S.p("meet", 0.6))
            text(ctx, "美丽联盟", p[0], p[1] - 70, 40, IVORY, S.p("meet", 0.6), "mm", bold=True, halo=9)
            text(ctx, "威灵顿 · 布吕歇尔 会面（通行说法）", p[0], p[1] + 80, 30, GOLD, S.p("meet", 0.6), "mm", halo=8)
    if sid in ("s05", "s09", "s11", "s12", "s13", "s15"):
        legend(ctx, [(FR, "法军"), (AL, "英荷联军"), (PR, "普军")], 0.9)


def cross_section(ctx, S, cue, a):
    """side view of the ridge: French guns left, crest, infantry lying behind (reverse slope)"""
    if a <= 0:
        return
    x0, y0, w, h = 60, 860, 960, 330
    panel(ctx, x0, y0, w, h, a)
    text(ctx, "剖面示意：反斜面", x0 + 30, y0 + 40, 30, GOLD, a, "lm", bold=True)
    gy = lambda x: y0 + h - 60 - 120 * math.exp(-((x - 640) / 170) ** 2) - 20 * math.exp(-((x - 200) / 120) ** 2)
    ctx.move_to(x0 + 10, y0 + h - 10)
    for x in range(x0 + 10, x0 + w - 10, 8):
        ctx.line_to(x, gy(x))
    ctx.line_to(x0 + w - 10, y0 + h - 10); ctx.close_path()
    ctx.set_source_rgba(0.30, 0.26, 0.18, a); ctx.fill()
    # french guns at left
    for i in range(2):
        gx = 170 + i * 60
        unit_block(ctx, gx, gy(gx) - 16, 34, 22, FR, a, kind="art")
    # infantry lying behind crest
    for i in range(5):
        ix = 730 + i * 50
        ctx.rectangle(ix - 18, gy(ix) - 10, 36, 9); ctx.set_source_rgba(*AL, a); ctx.fill()
    # sight line
    ctx.save(); ctx.set_dash([10, 8]); ctx.set_line_width(3)
    ctx.move_to(200, gy(200) - 20); ctx.line_to(640, gy(640) - 6); ctx.line_to(980, gy(640) + 60)
    ctx.set_source_rgba(1, 0.85, 0.5, 0.8 * a); ctx.stroke(); ctx.restore()
    # flying ball
    k = (S.t * 0.6) % 1.0
    bx = lerp(220, 700, k); by = gy(220) - 20 - math.sin(k * math.pi) * 140 + k * 10
    ctx.arc(bx, by, 7, 0, 6.3); ctx.set_source_rgba(0.1, 0.1, 0.1, a); ctx.fill()
    text(ctx, "法军炮位", 200, y0 + h - 25, 26, (0.7, 0.85, 1), a, "mm")
    text(ctx, "坡顶", 640, gy(640) - 40, 26, IVORY, a, "mm")
    text(ctx, "坡后步兵：看不见、打不着", 820, y0 + h - 25, 26, (1, 0.7, 0.65), a, "mm")


def column_diagram(ctx, S, a):
    if a <= 0:
        return
    x0, y0 = 60, 880
    panel(ctx, x0, y0, 960, 320, a)
    text(ctx, "纵队", 250, y0 + 40, 32, GOLD, a, "mm", bold=True)
    text(ctx, "横队", 760, y0 + 40, 32, GOLD, a, "mm", bold=True)
    for r in range(10):
        ctx.rectangle(160, y0 + 80 + r * 20, 180, 12)
    ctx.set_source_rgba(*FR, a); ctx.fill()
    text(ctx, "正面窄 · 纵深厚", 250, y0 + 300, 26, IVORY, a, "mm")
    for r in range(2):
        ctx.rectangle(560, y0 + 170 + r * 20, 400, 12)
    ctx.set_source_rgba(*AL, a); ctx.fill()
    text(ctx, "每支枪都能开火", 760, y0 + 300, 26, IVORY, a, "mm")
    # fire lines
    for i in range(8):
        x = 580 + i * 50
        ctx.move_to(x, y0 + 165); ctx.line_to(x - 40 - i * 25, y0 + 95)
    ctx.set_source_rgba(1, 0.8, 0.4, 0.5 * a * (0.5 + 0.5 * math.sin(S.t * 8))); ctx.set_line_width(2); ctx.stroke()


def reserve_split(ctx, S, a):
    panel(ctx, 90, 420, 900, 300, a)
    text(ctx, "预备队：本该是一只拳头", W / 2, 470, 40, GOLD, a, "mm", bold=True, serif=True)
    k = S.p("fist", 2.0)
    # blocks gathered -> split
    for i in range(6):
        gx = W / 2 - 120 + (i % 3) * 80
        gy = 570 + (i // 3) * 60
        tx = (300 + (i % 3) * 60) if i < 3 else (700 + (i % 3) * 60)
        x = lerp(gx, tx, k if i < 3 else k)
        unit_block(ctx, x, gy, 60, 40, (0.85, 0.7, 0.3), a)
    if k > 0.5:
        text(ctx, "东边 · 普朗斯努瓦", 360, 690, 28, IVORY, a * k, "mm")
        text(ctx, "中路", 760, 690, 28, IVORY, a * k, "mm")


# ================================================================ s07 courier
def sc_courier(ctx, S):
    t = S.t
    illus.draw_courier(ctx, t)
    ctx.set_source_rgba(0, 0, 0, 0.35 * S.p("noon", 0.8) + 0.25 * S.p("blame", 0.6)); ctx.paint()
    # timer
    if not S.on("noon"):
        k = S.lin("ride", max(S.c0("noon") - 0.5, 1))
        mins = 13 * 60 + int(k * 360)
        a = S.fin()
        panel(ctx, 640, 420, 380, 150, a)
        text(ctx, "信在路上", 830, 455, 28, GOLD, a, "mm")
        text(ctx, f"{mins // 60:02d}:{mins % 60:02d}", 830, 520, 70, IVORY, a, "mm", bold=True)
        if S.on("arrive"):
            ka = S.span("arrive", 0.5, "noon")
            rows = [("约 17:00", "乌赛等史家"), ("约 19:00", "格鲁希自述（1819）"), ("更晚", "另有说法")]
            for i, (h1, h2) in enumerate(rows):
                k2 = S.p("arrive", 0.5, 2.0 + i * 1.6) * ka
                panel(ctx, 100, 620 + i * 120, 520, 100, k2, FR)
                text(ctx, h1, 140, 670 + i * 120, 40, IVORY, k2, "lm", bold=True)
                text(ctx, h2, 600, 670 + i * 120, 28, GOLD, k2, "rm")
        if S.on("late"):
            text(ctx, "掉头也来不及了", W / 2, 1060, 56, (1, 0.6, 0.5), S.p("late", 0.6), "mm", bold=True, serif=True, halo=10)
    if S.on("noon"):
        a = S.span("noon", 0.6, "blame")
        icon_clock(ctx, W / 2, 560, 110, 11, 35, a)
        text(ctx, "6月18日 · 上午十一点半过后", W / 2, 720, 40, IVORY, a, "mm", bold=True, halo=8)
        text(ctx, "瓦尔安 · 公证人家中 · 草莓", W / 2, 780, 34, GOLD, a, "mm", halo=8)
        if S.on("guns"):
            quote_card(ctx, "« Il faut marcher au canon. »", "应该朝着炮声走。",
                       "热拉尔对格鲁希；据乌赛《1815：滑铁卢》引热拉尔军参谋报告", S.span("guns", 0.6, "blame") , y=1000,
                       orig_size=44, zh_size=48)
        if S.on("refuse"):
            text(ctx, "格鲁希：皇帝没让我回去", W / 2, 1230, 44, (0.75, 0.85, 1), S.span("refuse", 0.5, "blame"), "mm", bold=True, halo=10)
    if S.on("blame"):
        a = S.p("blame", 0.6)
        panel(ctx, 70, 470, 450, 420, a, GOLD)
        panel(ctx, 560, 470, 450, 420, a, FR)
        text(ctx, "拿破仑", 295, 540, 50, GOLD, a, "mm", bold=True, serif=True)
        text(ctx, "圣赫勒拿口述", 295, 610, 32, IVORY, a, "mm")
        text(ctx, "“错在格鲁希”", 295, 720, 40, IVORY, a, "mm", serif=True)
        text(ctx, "格鲁希", 785, 540, 50, (0.7, 0.85, 1), a, "mm", bold=True, serif=True)
        text(ctx, "终身撰文辩解", 785, 610, 32, IVORY, a, "mm")
        text(ctx, "“命令就是这么写的”", 785, 720, 40, IVORY, a, "mm", serif=True)
        if S.on("both"):
            k = S.p("both", 0.6)
            panel(ctx, 110, 940, 860, 200, k)
            text(ctx, "过代勒河 · 二十多公里泥路", W / 2, 1000, 40, IVORY, k, "mm", bold=True)
            text(ctx, "多数史家：即使掉头，也未必赶得上", W / 2, 1070, 34, GOLD, k, "mm")


# ================================================================ s08 mechanism 1
def sc_mech1(ctx, S):
    t = S.t
    fill_bg(ctx, (0.07, 0.075, 0.09))
    grid(ctx, 0.05)
    if S.on("sys") and not S.on("delay"):
        a = S.span("sys", 0.5, "delay")
        text(ctx, "不只是某一个人", W / 2, 720, 60, DIM, a, "mm", bold=True, serif=True)
        text(ctx, "是整套系统", W / 2, 840, 76, IVORY, a * S.p("sys", 0.6, 1.5), "mm", bold=True, serif=True, halo=10)
    if not S.on("berthier"):
        # timeline bar
        a = S.p("delay", 0.8)
        x0, x1, y = 140, 940, 620
        if a > 0:
            text(ctx, "信息慢", 140, 540, 50, IVORY, a, "lm", bold=True, serif=True)
            ctx.set_source_rgba(*DIM, a); ctx.set_line_width(4); ctx.move_to(x0, y); ctx.line_to(x1, y); ctx.stroke()
            k = S.p("delay", 3.0, 0.5)
            ctx.set_source_rgba(*AL, a); ctx.set_line_width(14); ctx.move_to(x0, y); ctx.line_to(lerp(x0, x1, k), y); ctx.stroke()
            for xx, s1, s2 in [(x0, "13:00", "望见普军"), (lerp(x0, x1, 0.55), "约17:00", "最早送到"), (x1, "约19:00", "格鲁希自述")]:
                ctx.arc(xx, y, 12, 0, 6.3); ctx.set_source_rgba(*IVORY, a); ctx.fill()
                text(ctx, s1, xx, y + 50, 32, IVORY, a, "mm", bold=True)
                text(ctx, s2, xx, y + 92, 26, GOLD, a, "mm")
        a = S.p("vague", 0.8)
        if a > 0:
            y = 900
            text(ctx, "命令含混", 140, y - 70, 50, IVORY, a, "lm", bold=True, serif=True)
            icon_letter(ctx, W / 2, y + 60, 1.3, a)
            arrow(ctx, [(W / 2, y + 10), (W / 2 + 40, y - 40), (W / 2 + 60, y - 110)], S.p("vague", 1.2, 0.6), FR, 26, glow=False)
            arrow(ctx, [(W / 2 - 60, y + 60), (W / 2 - 180, y + 50), (W / 2 - 300, y + 40)], S.p("vague", 1.2, 1.0), FR, 26, glow=False)
            text(ctx, "北：追普军", W / 2 + 90, y - 120, 30, IVORY, a, "lm")
            text(ctx, "西：靠主力", W / 2 - 300, y + 100, 30, IVORY, a, "mm")
            text(ctx, "？", W / 2 + 170, y + 60, 90, (1, 0.6, 0.5), a * S.p("vague", 0.5, 1.6), "mm", bold=True)
        a = S.p("intent", 0.8)
        if a > 0:
            panel(ctx, 120, 1120, 840, 120, a, AL)
            text(ctx, "缺的那一句：上级到底想要什么", W / 2, 1180, 42, (1, 0.8, 0.7), a, "mm", bold=True, serif=True)
    else:
        a = S.p("berthier", 0.8)
        panel(ctx, 70, 500, 450, 300, a, GOLD)
        panel(ctx, 560, 500, 450, 300, a, FR)
        text(ctx, "贝尔蒂埃", 295, 570, 50, GOLD, a, "mm", bold=True, serif=True)
        text(ctx, "1815年6月1日 坠楼身亡", 295, 640, 28, IVORY, a, "mm")
        text(ctx, "近二十年的参谋长", 295, 700, 32, IVORY, a, "mm")
        text(ctx, "苏尔特", 785, 570, 50, (0.7, 0.85, 1), a, "mm", bold=True, serif=True)
        text(ctx, "1815年5月 出任参谋长", 785, 640, 28, IVORY, a, "mm")
        text(ctx, "能打仗，不擅参谋", 785, 700, 32, IVORY, a, "mm")
        k = S.p("copies", 0.8)
        if k > 0:
            text(ctx, "据说：要紧命令，派几名信使走不同的路", W / 2, 880, 36, IVORY, k, "mm", bold=True)
            sx, sy, ex, ey = 180, 1150, 900, 1150
            for i, off in enumerate([-150, 0, 150]):
                pts = [(sx, sy), (W / 2, sy + off), (ex, ey)]
                ok = i != 1
                dashed(ctx, pts, S.lin("copies", 3.0, i * 0.4), GOLD if ok else DIM, 6, k, offset=-t * 30)
            cross(ctx, W / 2, 1150, 24, k * S.p("copies", 0.5, 3.0))
            icon_letter(ctx, sx, sy, 0.9, k)
            ctx.arc(ex, ey, 28, 0, 6.3); ctx.set_source_rgba(*FR, k); ctx.fill()
            text(ctx, "收信人", ex, ey + 60, 28, IVORY, k, "mm")


def grid(ctx, a=0.06):
    ctx.set_line_width(1); ctx.set_source_rgba(1, 1, 1, a)
    for x in range(0, W, 60):
        ctx.move_to(x, 0); ctx.line_to(x, H)
    for y in range(0, H, 60):
        ctx.move_to(0, y); ctx.line_to(W, y)
    ctx.stroke()


# ================================================================ s10 squares
def sc_squares(ctx, S):
    t = S.t
    fill_bg(ctx, (0.16, 0.15, 0.10))
    paint_surface(ctx, illus.mud_bg(), 0, 0, 0.0)
    rng = np.random.default_rng(1)
    # field texture
    ctx.set_source_rgba(0.24, 0.22, 0.14, 1); ctx.rectangle(0, 380, W, 900); ctx.fill()
    for i in range(300):
        x = rng.uniform(0, W); y = rng.uniform(380, 1280)
        ctx.rectangle(x, y, rng.uniform(20, 60), 2); ctx.set_source_rgba(0.35, 0.3, 0.18, 0.4); ctx.fill()
    form = S.p("square", 2.0)
    zoom = 1.0 + 0.8 * S.span("why", 1.0, "combo")
    ctx.save(); ctx.translate(W / 2, 830); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -830)
    centers = [(250 + (i % 3) * 290 + (145 if (i // 3) % 2 else 0) - (0 if (i // 3) % 2 else 0), 560 + (i // 3) * 260) for i in range(9)]
    centers = [c for c in centers if c[0] < W - 80]
    sq = 70
    for (cx, cy) in centers:
        if form < 1:
            # line -> square transition: draw line segment shrinking
            ctx.rectangle(cx - lerp(130, sq, form), cy - lerp(8, sq, form), 2 * lerp(130, sq, form), 2 * lerp(8, sq, form))
        else:
            ctx.rectangle(cx - sq, cy - sq, 2 * sq, 2 * sq)
        ctx.set_source_rgba(0.95, 0.93, 0.88, 0.95); ctx.set_line_width(12); ctx.stroke_preserve()
        ctx.set_source_rgba(*AL, 0.75); ctx.set_line_width(6); ctx.stroke()
        if form >= 1:
            # bayonets
            ctx.set_source_rgba(0.85, 0.85, 0.9, 0.7); ctx.set_line_width(2)
            for k in range(8):
                o = -sq + k * (2 * sq / 7)
                for (x1, y1, dx, dy) in [(cx + o, cy - sq, 0, -14), (cx + o, cy + sq, 0, 14), (cx - sq, cy + o, -14, 0), (cx + sq, cy + o, 14, 0)]:
                    ctx.move_to(x1, y1); ctx.line_to(x1 + dx, y1 + dy)
            ctx.stroke()
    # cavalry particles: flow from bottom to top, deflect around squares
    if S.on("charge"):
        dens = S.p("charge", 2.0)
        rng = np.random.default_rng(3)
        n = 260
        ph = rng.random(n); xs = rng.uniform(0, W, n); sp = rng.uniform(0.10, 0.16, n)
        wave = 0.5 + 0.5 * math.sin(t * 0.9)
        ctx.set_source_rgba(*FR, 0.9 * dens)
        for i in range(n):
            if rng.random() > dens:
                continue
            u = (ph[i] + t * sp[i]) % 1.0
            # surge forward then fall back (tide)
            y = 1300 - 900 * (u if u < 0.75 else (0.75 - (u - 0.75) * 2.5))
            x = xs[i]
            for (cx, cy) in centers:
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if d < sq * 1.9:
                    push = (sq * 1.9 - d) * 1.0
                    x += dx / (d + 1e-3) * push
                    y += dy / (d + 1e-3) * push * 0.3
            ctx.rectangle(x - 6, y - 10, 12, 20)
        ctx.fill()
    ctx.restore()
    # annotations
    if S.on("ney") and not S.on("charge"):
        a = S.span("ney", 0.6, "charge")
        text(ctx, "约 16:00", W / 2, 470, 44, GOLD, a, "mm", bold=True, halo=8)
        if S.on("mistake"):
            for i in range(10):
                x = 200 + i * 70; y = 700 - S.lin("mistake", 5) * 200 - (i % 3) * 20
                ctx.arc(x, y, 9, 0, 6.3); ctx.set_source_rgba(*AL, 0.9 * a); ctx.fill()
            text(ctx, "伤兵 · 弹药车 · 躲炮的部队", W / 2, 1000, 40, IVORY, a, "mm", bold=True, halo=8)
            text(ctx, "内伊：威灵顿要退了？", W / 2, 1080, 44, (0.75, 0.85, 1), a * S.p("mistake", 0.5, 3), "mm", bold=True, halo=8)
    if S.on("charge"):
        tag(ctx, "近一万骑 · 一波接一波", W / 2, 470, FR, S.span("charge", 0.6, "why"))
    if S.on("why"):
        text(ctx, "马不会往刺刀上撞", W / 2, 470, 50, IVORY, S.span("why", 0.6, "combo"), "mm", bold=True, serif=True, halo=10)
    if S.on("combo"):
        combo_diagram(ctx, S)
    if S.on("spike"):
        a = S.span("spike", 0.6, "result")
        panel(ctx, 100, 980, 880, 200, a)
        text(ctx, "没把缴获的大炮钉死", W / 2, 1040, 44, IVORY, a, "mm", bold=True)
        text(ctx, "骑兵一退，英军炮手又回来开炮", W / 2, 1110, 34, GOLD, a, "mm")
    if S.on("result"):
        a = S.p("result", 0.6)
        panel(ctx, 100, 950, 880, 240, a)
        text(ctx, "十几次冲锋", W / 2, 1020, 56, IVORY, a, "mm", bold=True, serif=True)
        text(ctx, "几乎没有一个方阵被冲垮", W / 2, 1110, 44, GOLD, a, "mm", bold=True)
    text(ctx, "俯视示意：白色方框为英军方阵，蓝色为法军骑兵", W / 2, 1250, 24, DIM, S.fin(), "mm")


def combo_diagram(ctx, S):
    a = S.span("combo", 0.6, "spike")
    if a <= 0:
        return
    ctx.set_source_rgba(0, 0, 0, 0.6 * a); ctx.paint()
    cx, cy = W / 2, 800
    pts = {"骑兵": (cx, cy - 250), "炮兵": (cx - 260, cy + 180), "步兵": (cx + 260, cy + 180)}
    cols = {"骑兵": FR, "炮兵": FR, "步兵": FR}
    ctx.rectangle(cx - 60, cy - 30, 120, 120); ctx.set_source_rgba(0.95, 0.93, 0.88, a); ctx.set_line_width(10); ctx.stroke()
    text(ctx, "方阵", cx, cy + 30, 36, IVORY, a, "mm", bold=True)
    alone = S.p("alone", 0.6)
    for nm, (x, y) in pts.items():
        dead = alone if nm != "骑兵" else 0
        aa = a * (1 - 0.65 * dead)
        ctx.arc(x, y, 80, 0, 6.3); ctx.set_source_rgba(*cols[nm], 0.9 * aa); ctx.fill()
        text(ctx, nm, x, y, 44, IVORY, aa, "mm", bold=True)
        tx, ty = cx + (x - cx) * 0.38, cy + 30 + (y - cy - 30) * 0.38
        arrow(ctx, [(x + (cx - x) * 0.3, y + (cy - y) * 0.3), (tx, ty)], 1.0, IVORY, 18, alpha=aa, glow=False, outline=False)
        if dead > 0:
            cross(ctx, x, y, 40, dead * a)
    text(ctx, "逼你结方阵", pts["骑兵"][0] + 110, pts["骑兵"][1], 30, GOLD, a, "lm")
    text(ctx, "轰开方阵", pts["炮兵"][0], pts["炮兵"][1] + 115, 30, GOLD, a, "mm")
    text(ctx, "火力撕口子", pts["步兵"][0], pts["步兵"][1] + 115, 30, GOLD, a, "mm")
    if S.on("alone"):
        text(ctx, "这天下午：只有骑兵", W / 2, 1210, 46, (1, 0.6, 0.5), a * alone, "mm", bold=True, serif=True)


# ================================================================ s13 guard2 (map then dusk)
def sc_guard2(ctx, S):
    t = S.t
    tc = S.c0("climb")
    if t < tc + 1.0:
        sc_field(ctx, S)
    if t >= tc:
        a = clamp((t - tc) / 1.0)
        surf, c2 = new_surface()
        lt = t - tc
        adv = 0.3 + 0.6 * clamp(lt / max(S.c0("volley") - tc, 1))
        ret = S.p("halt", 3) * 0.7
        illus.draw_dusk(c2, t, adv, rise=S.p("volley", 1.0), fire=S.span("volley", 0.2, "halt") * (0.5 + 0.5 * math.sin(t * 13)),
                        retreat=ret, scatter=S.p("recule", 4) * 0.5, red=S.p("recule", 0.3) * 0.5, shake=S.span("volley", 0.2, "halt") * 0.5)
        if S.on("flank"):
            # flanking fire from right edge
            for i in range(6):
                y = 760 + i * 30
                burst(c2, W - 30, y, t, 40, S.span("flank", 0.3, "halt"), seed=i)
        ctx.set_source_surface(surf, 0, 0); ctx.paint_with_alpha(a)
        if S.on("wheat") and not S.on("volley"):
            text(ctx, "坡后麦田：什么也看不见", W / 2, 520, 46, IVORY, S.span("wheat", 0.5, "volley"), "mm", bold=True, halo=10)
        if S.on("volley"):
            tag(ctx, "几十步外 · 英军近卫步兵起立齐射", W / 2, 480, AL, S.span("volley", 0.4, "flank"), 32)
        if S.on("flank"):
            tag(ctx, "第52团 侧射", W / 2, 480, AL, S.span("flank", 0.4, "halt"), 34)
        a = S.p("recule", 0.15)
        if a > 0:
            text(ctx, "La Garde recule !", W / 2, 560, 92, (1, 0.92, 0.8), a, "mm", family=LATIN_I, italic=True, halo=14)
            text(ctx, "“近卫军后退了！”", W / 2, 680, 64, (1, 0.85, 0.7), a, "mm", bold=True, serif=True, halo=10)
            text(ctx, "据记载 · 战场呼喊", W / 2, 760, 28, GOLD, a, "mm", halo=6)


# ================================================================ s14 panic network
def sc_panic(ctx, S):
    t = S.t
    fill_bg(ctx, (0.06, 0.06, 0.08))
    rng = np.random.default_rng(14)
    n = 120
    pts = np.c_[rng.uniform(90, W - 90, n), rng.uniform(470, 1220, n)]
    # edges: k nearest
    d = np.linalg.norm(pts[:, None] - pts[None], axis=2)
    nb = np.argsort(d, 1)[:, 1:5]
    src = int(np.argmin(np.linalg.norm(pts - np.array([W / 2, 820]), axis=1)))
    # infection time = graph distance-ish (euclid from source) once "floor"/"betray" begins
    start = S.c0("floor")
    dist = np.linalg.norm(pts - pts[src], axis=1)
    sec_src = int(np.argmin(np.linalg.norm(pts - np.array([W - 120, 600]), axis=1)))
    dist2 = np.linalg.norm(pts - pts[sec_src], axis=1)
    inf_t = start + dist / 160.0
    inf_t = np.minimum(inf_t, S.c0("betray") + 1.0 + dist2 / 160.0)
    infected = t >= inf_t
    a = S.p("net", 1.0)
    ctx.set_line_width(1.5)
    for i in range(n):
        for j in nb[i]:
            both = infected[i] and infected[j]
            ctx.move_to(*pts[i]); ctx.line_to(*pts[j])
            ctx.set_source_rgba(*((0.9, 0.3, 0.2) if both else (0.5, 0.55, 0.65)), (0.5 if both else 0.25) * a)
            ctx.stroke()
    for i in range(n):
        x, y = pts[i]
        if infected[i]:
            k = clamp((t - inf_t[i]) / 0.6)
            ctx.arc(x + k * 25 * math.sin(i), y + k * 30, 10, 0, 6.3); ctx.set_source_rgba(0.95, 0.35, 0.25, a); ctx.fill()
        else:
            ctx.arc(x, y, 9, 0, 6.3); ctx.set_source_rgba(*FR, a); ctx.fill()
    if S.on("why") and not S.on("net"):
        text(ctx, "一句话，为什么能打垮一支军队？", W / 2, 820, 50, IVORY, S.span("why", 0.5, "net"), "mm", bold=True, serif=True, halo=10)
    if S.on("net"):
        tag(ctx, "别人还在打吗？后面还有人吗？", W / 2, 1290, IVORY, S.span("net", 0.5, "floor"), 32)
    if S.on("floor"):
        p = pts[src]
        tag(ctx, "近卫军后退", p[0], p[1] - 60, (0.85, 0.7, 0.3), S.span("floor", 0.5, "psy"), 30)
    if S.on("betray"):
        p = pts[sec_src]
        tag(ctx, "“我们被出卖了！”", p[0] - 120, p[1] - 70, PR, S.span("betray", 0.5, "psy"), 30)
    if S.on("psy"):
        a = S.p("psy", 0.6)
        panel(ctx, 100, 1000, 880, 210, a)
        text(ctx, "看不清全局时，人看身边人", W / 2, 1065, 42, IVORY, a, "mm", bold=True, serif=True)
        text(ctx, "一个人跑 = 周围人的信号", W / 2, 1140, 38, GOLD, a, "mm", bold=True)


# ================================================================ s15 rout (field then Wavre)
def sc_rout(ctx, S):
    t = S.t
    tw = S.c0("wavre")
    if t < tw + 1.0:
        sc_field(ctx, S)
    if t >= tw:
        a = clamp((t - tw) / 1.0)
        surf, c2 = new_surface()
        cam = Cam(S, [(None, (B("瓦弗尔")[0] - 20, B("瓦弗尔")[1] + 60), 1.5)])
        map_base(c2, bigmap(), cam, 0.0)
        c2.save(); cam.apply(c2)
        wv = B("瓦弗尔")
        for i in range(3):
            unit_block(c2, wv[0] - 40 + i * 40, wv[1] - 20, 30, 20, PR, 1)
        g = [Bll(4.66, 50.67), Bll(4.635, 50.695), (wv[0] + 10, wv[1] + 10)]
        arrow(c2, g, 0.85 + 0.1 * math.sin(t * 2), FR, 34 / cam.z)
        if S.on("retreat"):
            r = [Bll(4.62, 50.70), Bll(4.66, 50.62), Bll(4.70, 50.55), Bll(4.80, 50.48)]
            dashed(c2, r, S.lin("retreat", 4), FR, 8 / cam.z, 1.0, offset=-t * 30)
        c2.restore()
        draw_labels_big(c2, cam, 1.0, only=("瓦弗尔", "圣朗贝尔", "瓦尔安", "让布卢"))
        p = cam.sc(wv)
        tag(c2, "格鲁希 · 约三万三千", p[0] + 140, p[1] + 260, FR, 1)
        tag(c2, "普军第三军 · 约一万五至一万七", p[0] - 60, p[1] - 180, PR, 1)
        if S.on("claus"):
            k = S.span("claus", 0.6, "retreat")
            panel(c2, 140, 430, 800, 170, k, PR)
            text(c2, "第三军参谋长：克劳塞维茨", W / 2, 485, 44, IVORY, k, "mm", bold=True, serif=True)
            text(c2, "后来写下《战争论》", W / 2, 550, 34, GOLD, k, "mm")
        legend(c2, [(FR, "法军"), (AL, "英荷联军"), (PR, "普军")], 0.9)
        ctx.set_source_surface(surf, 0, 0); ctx.paint_with_alpha(a)


# ================================================================ s16 dispute
def sc_dispute(ctx, S):
    t = S.t
    fill_bg(ctx, (0.07, 0.07, 0.08))
    a = S.p("who", 0.6) * (1 - S.p("desp", 0.6) * 0.85)
    text(ctx, "谁赢了滑铁卢？", W / 2, 470, 60, IVORY, S.p("who", 0.6), "mm", bold=True, serif=True)
    if S.on("uk") or S.on("who"):
        k = S.p("uk", 0.6)
        panel(ctx, 70, 560, 450, 460, a * k, AL)
        panel(ctx, 560, 560, 450, 460, a * k, PR)
        text(ctx, "英国叙事", 295, 630, 46, (1, 0.65, 0.6), a * k, "mm", bold=True)
        text(ctx, "方阵顶住一整天", 295, 760, 36, IVORY, a * k, "mm")
        text(ctx, "普鲁士叙事", 785, 630, 46, (0.7, 0.95, 0.7), a * k, "mm", bold=True)
        text(ctx, "侧面压垮法军", 785, 760, 36, IVORY, a * k, "mm")
        text(ctx, "如 霍夫施罗尔（本身有争议）", 785, 940, 24, GOLD, a * k, "mm")
    if S.on("desp"):
        quote_card(ctx, "“…I should not do justice to my own feelings, or to Marshal Blücher and the Prussian army, if I did not attribute the successful result of this arduous day to the cordial and timely assistance I received from them.”",
                   "这一天的胜利，要归功于布吕歇尔和普军真诚而及时的援助。",
                   "威灵顿致巴瑟斯特伯爵的滑铁卢战报，1815年6月19日", S.span("desp", 0.6, "both") , y=820, orig_size=30, zh_size=44)
    if S.on("both"):
        k = S.p("both", 0.6)
        panel(ctx, 70, 600, 940, 420, k)
        text(ctx, "也许都对", W / 2, 680, 56, GOLD, k, "mm", bold=True, serif=True)
        text(ctx, "没有威灵顿顶住 → 普军无处使劲", W / 2, 800, 38, IVORY, k, "mm")
        text(ctx, "没有普军赶到 → 威灵顿未必顶到天黑", W / 2, 880, 38, IVORY, k, "mm")


# ================================================================ s17 friction
def sc_friction(ctx, S):
    t = S.t
    fill_bg(ctx, (0.065, 0.065, 0.075))
    grid(ctx, 0.035)
    items = ["开战晚了", "信送晚了", "兵种没配合", "预备队拆散", "最后一击太晚"]
    a = S.p("small", 0.6) * (1 - S.p("friction", 0.6))
    if a > 0:
        for i, s in enumerate(items):
            k = S.p("chain", 0.5, i * 0.7) if S.on("chain") else S.p("list", 0.5, i * 1.2) * 0.5
            y = 520 + i * 140
            x = 200 + (i % 2) * 120
            panel(ctx, x, y - 50, 560, 100, a * max(k, 0.25), AL if S.on("chain") else GOLD)
            text(ctx, s, x + 280, y, 44, IVORY, a * max(k, 0.25), "mm", bold=True, serif=True)
            if i < 4 and S.on("chain"):
                ctx.set_source_rgba(1, 0.6, 0.4, a * k); ctx.set_line_width(6)
                ctx.arc(x + 280 + (60 if i % 2 == 0 else -60), y + 70, 18, 0, 6.3); ctx.stroke()
        if not S.on("chain"):
            text(ctx, "每一个，当时都有理由", W / 2, 1250, 40, GOLD, a * S.p("small", 0.6, 2), "mm", bold=True)
    if S.on("friction"):
        a = S.p("friction", 0.6) * (1 - S.p("auftrag", 0.6))
        text(ctx, "Friktion · 摩擦", W / 2, 520, 64, GOLD, a, "mm", bold=True, serif=True)
        quote_card(ctx, "Es ist alles im Kriege sehr einfach, aber das Einfachste ist schwierig.",
                   "战争中的一切都很简单，但最简单的事情也很难。",
                   "克劳塞维茨《战争论》第一篇第七章（英译 Howard & Paret: “Everything in war is very simple, but the simplest thing is difficult.”）",
                   a * S.p("quote", 0.6), y=880, orig_size=40, zh_size=48)
    if S.on("auftrag"):
        a = S.p("auftrag", 0.6) * (1 - S.p("work", 0.6))
        panel(ctx, 70, 470, 940, 640, a)
        text(ctx, "任务式指挥（Auftragstaktik，后来发展）", W / 2, 530, 34, GOLD, a, "mm", bold=True)
        text(ctx, "命令：做什么", 300, 650, 44, IVORY, a, "mm", bold=True, serif=True)
        text(ctx, "+", W / 2, 650, 60, GOLD, a, "mm", bold=True)
        text(ctx, "意图：为什么", 780, 650, 44, (1, 0.85, 0.5), a, "mm", bold=True, serif=True)
        text(ctx, "追击普军", 300, 760, 38, (0.7, 0.85, 1), a * S.p("ifg", 0.6), "mm")
        text(ctx, "绝不让普英会合", 780, 760, 38, (1, 0.85, 0.5), a * S.p("ifg", 0.6, 2.5), "mm", bold=True)
        text(ctx, "听到炮声时 → 也许另作选择", W / 2, 900, 40, IVORY, a * S.p("ifg", 0.6, 6), "mm")
        text(ctx, "（只是假如）", W / 2, 970, 30, DIM, a * S.p("ifg", 0.6, 8), "mm")
    if S.on("work"):
        a = S.p("work", 0.6)
        panel(ctx, 70, 520, 940, 560, a, GOLD)
        card_text(ctx, ["命令只有在接收者", "理解了意图的时候，", "才算真正送到。"], 640, a, 54)
        ctx.set_source_rgba(*GOLD, 0.6 * a); ctx.set_line_width(2); ctx.move_to(340, 880); ctx.line_to(740, 880); ctx.stroke()
        card_text(ctx, ["关键的那一天，别指望一封", "晚到、含混的信替你调兵。"], 950, a * S.p("work", 0.6, 4.5), 40, GOLD, bold=False)


# ================================================================ s18 ending
def sc_ending(ctx, S):
    t = S.t
    paint_surface(ctx, illus.dusk_bg("calm"), 0, 0)
    paint_surface(ctx, illus.smoke_layer(55, 0.25, (0.6, 0.5, 0.45)), -((t * 8) % W), 520, 0.6)
    ctx.move_to(0, 800); ctx.curve_to(300, 740, 700, 780, W, 730); ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path()
    ctx.set_source_rgba(0.12, 0.08, 0.06, 0.9); ctx.fill()
    illus.hill(ctx, (0.08, 0.06, 0.05), True, t)
    ctx.set_source_rgba(0, 0, 0, 0.25 * S.p("hugo", 0.6) * (1 - S.p("wel", 1.0))); ctx.paint()
    if S.on("hugo"):
        a = S.span("hugo", 0.6, "aust")
        quote_card(ctx, "« S'il n'avait pas plu dans la nuit du 17 au 18 juin 1815, l'avenir de l'Europe était changé. … Pour que Waterloo fût la fin d'Austerlitz, la providence n'a eu besoin que d'un peu de pluie. »",
                   "如果那一夜没有下雨，欧洲的未来就会改变。要让滑铁卢成为奥斯特利茨的终点，天意只需要一点雨。",
                   "雨果《悲惨世界》第二部第一卷第三章", a, y=820, orig_size=30, zh_size=40)
    if S.on("aust"):
        a = S.span("aust", 0.6, "wel")
        panel(ctx, 110, 480, 860, 280, a)
        text(ctx, "1805 奥斯特利茨：调动对手", W / 2, 570, 48, GOLD, a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "1815 滑铁卢：调不动自己", W / 2, 670, 48, IVORY, a * S.p("aust", 0.6, 2.2), "mm", bold=True, serif=True, halo=10)
    if S.on("wel"):
        a = S.p("wel", 0.8) * clamp((S.dur - t) / 1.2)
        panel(ctx, 60, 470, 960, 400, a * 0.9)
        text(ctx, "“the nearest run thing", W / 2, 560, 50, (1, 0.93, 0.8), a, "mm", family=LATIN_I, italic=True, halo=10)
        text(ctx, "you ever saw in your life.”", W / 2, 630, 50, (1, 0.93, 0.8), a, "mm", family=LATIN_I, italic=True, halo=10)
        text(ctx, "这是你这辈子见过的，最险的一次。", W / 2, 740, 48, IVORY, a, "mm", bold=True, serif=True, halo=10)
        text(ctx, "威灵顿对克里维语，见《克里维文件》（1904 年版）卷一第 236 页", W / 2, 820, 26, GOLD, a, "mm", halo=6)


RENDERERS = {
    "guard": sc_guard, "hookmap": sc_hookmap, "bigmap": sc_campaign, "bigmap2": sc_campaign, "rain": sc_rain,
    "field": sc_field, "courier": sc_courier, "mech1": sc_mech1, "squares": sc_squares, "guard2": sc_guard2,
    "panic": sc_panic, "rout": sc_rout, "dispute": sc_dispute, "friction": sc_friction, "ending": sc_ending,
}
BADGE = {"guard": "ill", "hookmap": "map", "bigmap": "map", "bigmap2": "map", "rain": "ill", "field": "map", "courier": "ill",
         "mech1": "card", "squares": "ill", "guard2": "map", "panic": "card", "rout": "map", "dispute": "card", "friction": "card",
         "ending": "ill"}
