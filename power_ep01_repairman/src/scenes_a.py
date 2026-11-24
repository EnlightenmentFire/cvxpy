"""Scenes: cold open, title card, intro, section 1 (rules everywhere)."""
import math

import skia

from gfx import *
from icons import *
from gfx import _hash, _rrect


class Ctx:
    def __init__(self, tl, t, frame):
        self.tl, self.t, self.frame = tl, t, frame

    def ls(self, i):
        return self.tl["lines"][i][0]

    def le(self, i):
        return self.tl["lines"][i][1]

    def ev(self, kind, payload=None):
        for (tt, k, p) in self.tl["events"]:
            if k == kind and (payload is None or p == payload):
                return tt
        return None

    def at(self, i, d=0.7, off=0.0):
        """eased progress of an animation starting at line i start (+off)."""
        return ease(seg(self.t, self.ls(i) + off, self.ls(i) + off + d))

    def after(self, i, d=0.7, off=0.0):
        """eased progress starting at the END of line i."""
        return ease(seg(self.t, self.le(i) + off, self.le(i) + off + d))

    def frac(self, i, f):
        """time at fraction f of line i (for syncing to a word)."""
        s, e = self.tl["lines"][i]
        return s + (e - s) * f

    def win(self, i0, i1=None, fin=0.45, fout=0.45, lead=0.0):
        """alpha envelope: visible from start of i0 until start of i1 (or end of i0)."""
        a = self.ls(i0) - lead
        if i1 == "__end__":
            b = 1e9
        else:
            b = self.ls(i1) if i1 else self.le(i0) + 0.3
        return ease(seg(self.t, a, a + fin)) * (1 - ease(seg(self.t, b - fout * 0.5, b + fout * 0.5)))


def word_time(ctx, i, word, nth=0):
    """approximate time when `word` is spoken in line i (by character position)."""
    from script_data import BY_ID
    txt = BY_ID[i]["text"]
    pos = -1
    for _ in range(nth + 1):
        pos = txt.find(word, pos + 1)
    if pos < 0:
        return ctx.ls(i)
    return ctx.frac(i, pos / max(1, len(txt)))


def label(c, s, x, y, size=34, rgb=INK, a=1.0, font_name="serif_bold", align="center", box=False, pad=14,
          box_fill=CARD, box_stroke=INK2):
    if a <= 0.003:
        return
    if box:
        w = text_width(s, font_name, size) + pad * 2
        h = size * 1.5
        x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x - pad)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y - h / 2, w, h), 8, 8), paint(box_fill, a))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y - h / 2, w, h), 8, 8), paint(box_stroke, a, stroke=2.2))
    draw_text(c, s, x, y, font_name, size, rgb, a, align=align)


def para(c, lines, x, y, size=40, rgb=INK, a=1.0, font_name="serif_bold", lh=1.45, align="center"):
    for k, s in enumerate(lines):
        draw_text(c, s, x, y + k * size * lh, font_name, size, rgb, a, align=align)


def gloss_card(c, x, y, w, h, term, defs, a=1.0, ang=0.0, tag="名词", sub=None, extra=None, term_size=64,
               def_size=42):
    """Glossary card: tag, big term, definition lines."""
    if a <= 0.003:
        return

    def body(cc, ww, hh):
        draw_text(cc, tag, -ww / 2 + 30, -hh / 2 + 34, "sans_bold", 28, INK3, 1)
        cc.drawLine(-ww / 2 + 30, -hh / 2 + 56, ww / 2 - 30, -hh / 2 + 56, paint(INK4, 1, stroke=1.5))
        draw_text(cc, term, 0, -hh / 2 + 56 + term_size * 0.95, "serif_heavy", term_size, INK, 1, align="center")
        yy = -hh / 2 + 56 + term_size * 1.85
        if sub:
            draw_text(cc, sub, 0, yy, "sans", 26, INK3, 1, align="center")
            yy += 46
        for k, d in enumerate(defs):
            draw_text(cc, d, 0, yy + k * def_size * 1.45, "serif_semi", def_size, INK2, 1, align="center")
        if extra:
            extra(cc, ww, hh)

    card(c, x, y, w, h, "", a=a, ang=ang, body_fn=body)


def camera_to(c, scale, tx, ty):
    """Scale by `scale` and bring world point (tx, ty) to the stage centre."""
    c.translate(540, STAGE_CY)
    c.scale(scale, scale)
    c.translate(-tx, -ty)


def camera(c, scale=1.0, cx=540, cy=STAGE_CY, dx=0, dy=0):
    c.translate(cx + dx, cy + dy)
    c.scale(scale, scale)
    c.translate(-cx, -cy)


# =====================================================================================
# COLD OPEN (示意)
# =====================================================================================
FRONT_FLOOR = 1150
LINE_TOP = 1032
STATIONS = [170, 410, 650, 890]
JAM = 2  # index of the station that jams


def sc_cold(c, ctx):
    t = ctx.t
    stop_t = ctx.ev("stop", "c03") or 1e9
    since = t - stop_t
    running = 1.0 if since < 0 else max(0.0, 1 - since * 6)
    look_t = ctx.ls("c04") + 0.5
    look = ease(seg(t, look_t, look_t + 0.8))
    arm_stop = ease(seg(t, ctx.ls("c04"), ctx.ls("c04") + 0.6))
    c.save()
    # camera choreography: wide -> push on the jam -> pan to the nominal boss -> pull back wide
    keys = [(0.0, 1.0, 540, 830), (stop_t, 1.04, 540, 830), (stop_t + 1.4, 1.34, 640, 955),
            (ctx.ls("c05"), 1.34, 640, 955), (ctx.ls("c05") + 1.3, 1.3, 330, 760),
            (ctx.ls("c06") + 0.2, 1.3, 330, 760), (ctx.ls("c06") + 1.6, 1.02, 560, 830)]
    sc_, tx_, ty_ = keys[0][1:]
    for (ta, sa, xa, ya), (tb, sb, xb, yb) in zip(keys, keys[1:]):
        if t >= ta:
            u = ease(seg(t, ta, tb))
            sc_, tx_, ty_ = lerp(sa, sb, u), lerp(xa, xb, u), lerp(ya, yb, u)
    camera_to(c, sc_, tx_, ty_)
    # back wall with skylights
    c.drawRect(skia.Rect.MakeXYWH(-200, 300, 1480, 280), paint(PAPER_DEEP, 0.55))
    # sawtooth roof seen from inside: glazed north lights between trusses
    roof = skia.Path()
    roof.moveTo(-200, 470)
    for k in range(9):
        x0 = -200 + k * 180
        roof.lineTo(x0 + 130, 360)
        roof.lineTo(x0 + 130, 470)
        roof.lineTo(x0 + 180, 470)
    for k in range(9):
        x0 = -200 + k * 180
        p = skia.Path().moveTo(x0 + 18, 462).lineTo(x0 + 122, 375).lineTo(x0 + 122, 462).close()
        c.drawPath(p, paint(CARD, 0.95))
        for q in (1, 2):
            xx = x0 + 18 + q * 35
            c.drawLine(xx, 462, xx, 462 - (xx - x0 - 18) * 87 / 104, paint(INK4, 0.8, stroke=1.6))
    c.drawPath(roof, paint(INK3, 0.85, stroke=3))
    c.drawLine(-200, 470, 1280, 470, paint(INK3, 0.85, stroke=3))
    c.drawLine(-40, 580, 1120, 580, paint(INK3, 0.7, stroke=2.5))
    # back row (dimmer)
    for k, mx in enumerate([230, 470, 710]):
        machine_side(c, mx, 742, 150, 92, t + k, running=1.0, a=0.55, seed=20 + k)
        osc = math.sin(t * 5 + k) * 0.5 + 0.5
        figure_side(c, mx + 186, 742, 120, "worker", face=-1, arm=0.35 + 0.3 * osc, a=0.55)
    # shop director (left) – the nominal boss
    dim_dir = 0.45 * ease(seg(t, ctx.ls("c06") + 0.6, ctx.ls("c06") + 1.6))
    figure_side(c, 105, 800, 175, "chief", face=1, arm=0.15, dim=dim_dir)
    c.drawRect(skia.Rect.MakeXYWH(150, 730, 70, 70), paint(mix(UMBER, PAPER, 0.4)))
    c.drawRect(skia.Rect.MakeXYWH(150, 730, 70, 70), paint(INK2, 1, stroke=2))
    # maintenance corner (right)
    c.drawRect(skia.Rect.MakeXYWH(900, 735, 150, 18), paint(UMBER_D))
    c.drawRect(skia.Rect.MakeXYWH(912, 753, 12, 50), paint(UMBER_D))
    c.drawRect(skia.Rect.MakeXYWH(1025, 753, 12, 50), paint(UMBER_D))
    wrench_icon(c, 980, 640, 30, INK3, 0.8, ang=10)
    wrench_icon(c, 1030, 655, 24, INK3, 0.8, ang=60)
    figure_side(c, 965, 805, 170, "maint", face=-1, arm=0.25)
    # gaze lines (c06)
    gz = ease(seg(t, look_t + 0.3, look_t + 1.3))
    # front row: women behind the long machine
    for k, sx in enumerate(STATIONS):
        osc = math.sin(t * 6.2 + k * 1.3) * 0.5 + 0.5
        arm = lerp(0.25 + 0.45 * osc * running, 0.05, arm_stop) if since > 0 else 0.25 + 0.45 * osc
        lk = look * (1 if k != 3 else 1)
        figure_side(c, sx + 70, FRONT_FLOOR, 262, "worker", face=-1, arm=arm, look=lk)
        if gz > 0:
            hx, hy = sx + 70 + (-1.5 * lk) * -2.62, FRONT_FLOOR - 92 * 2.62
            tx, ty = 960, 650
            ex, ey = lerp(hx, tx, gz * 0.92), lerp(hy, ty, gz * 0.92)
            dp = paint(INK2, 0.55 * gz, stroke=3)
            dp.setPathEffect(skia.DashPathEffect.Make([4, 12], 0))
            c.drawLine(hx + 24, hy, ex, ey, dp)
    # the long production line (front)
    wrect(c, 30, LINE_TOP, 1020, 118, fill=METAL, stroke=INK, sw=3.5, seed=5, amp=0.7)
    c.drawRect(skia.Rect.MakeXYWH(30, LINE_TOP - 14, 1020, 16), paint(INK2))
    # cigarettes moving left on top
    ph = (t if since < 0 else stop_t) * 70
    for k in range(26):
        xx = 1040 - ((k * 40 + ph) % 1010)
        c.drawRect(skia.Rect.MakeXYWH(xx, LINE_TOP - 22, 20, 7), paint(CARD))
        c.drawRect(skia.Rect.MakeXYWH(xx, LINE_TOP - 22, 20, 7), paint(INK3, 1, stroke=1))
    for k, sx in enumerate(STATIONS):
        tt = t if since < 0 else stop_t + (0 if k == JAM else 0)
        jerk = 0.0
        if k == JAM and 0 < since < 0.25:
            jerk = math.sin(since * 60) * 0.06 * (1 - since / 0.25)
        draw_gear(c, sx, LINE_TOP + 52, 38, tt * 2.3 + jerk, METAL_D, teeth=12)
        draw_gear(c, sx + 56, LINE_TOP + 70, 24, -tt * 3.6, METAL_D, teeth=9)
    for k in range(5):
        c.drawRect(skia.Rect.MakeXYWH(60 + k * 235, LINE_TOP + 118, 16, 26), paint(METAL_D))
    if since > 0:
        ring_pulse(c, STATIONS[JAM], LINE_TOP + 52, since, rmax=170, w=7)
        gl = paint(ACCENT, 0.9, stroke=6)
        c.drawCircle(STATIONS[JAM], LINE_TOP + 52, 44, gl)
    # label for the shop director (c05)
    la = ctx.win("c05", "intro_dummy") if False else ease(seg(t, ctx.ls("c05") + 0.3, ctx.ls("c05") + 0.9))
    label(c, "车间主任", 112, 575, 34, INK, la, box=True)
    c.restore()
    stamp(c, "示意", 100, 362, 26)


# =====================================================================================
# TITLE
# =====================================================================================
def sc_title(c, t, T):
    a = ease(seg(t, 0, 0.5)) * (1 - ease(seg(t, T - 0.45, T)))
    if a <= 0:
        return
    lay = c.saveLayerAlpha(None, int(255 * a))
    cy = 760
    draw_text(c, "组织里的权力", 540, cy - 230, "serif_bold", 50, INK2, 1, align="center", spacing=12)
    draw_text(c, "第一期", 540, cy - 160, "sans", 32, INK3, 1, align="center", spacing=10)
    sc = 1 + 0.03 * ease(seg(t, 0, T))
    c.save(); c.translate(540, cy + 10); c.scale(sc, sc)
    draw_text(c, "维修工", 0, 0, "serif_heavy", 210, INK, 1, align="center", spacing=18)
    c.restore()
    c.drawLine(300, cy + 160, 780, cy + 160, paint(INK3, 1, stroke=2))
    draw_text(c, "上世纪五十年代 · 法国一家国营烟草厂", 540, cy + 215, "serif_semi", 36, INK2, 1, align="center")
    draw_gear(c, 540, cy + 330, 34, 0.4, METAL_D, teeth=11)
    c.drawCircle(540, cy + 330, 52, paint(ACCENT, 0.85, stroke=5))
    c.restore()


# =====================================================================================
# INTRO
# =====================================================================================
def smoke(c, x, y, t, a=1.0):
    for k in range(6):
        ph = (t * 0.35 + k / 6) % 1
        r = 16 + ph * 46
        c.drawCircle(x + ph * 90 + math.sin(ph * 6 + k) * 10, y - ph * 230, r, paint((190, 182, 168), a * (1 - ph) * 0.55))


def sc_intro(c, ctx):
    t = ctx.t
    # ---- i01: establishing factory
    a = ctx.win("i01", "i02")
    if a > 0:
        c.save(); camera(c, lerp(1.0, 1.04, seg(t, ctx.ls("i01"), ctx.ls("i02"))))
        smoke(c, 860, 650, t, a)
        factory_front(c, 130, 1110, 820, 390, a=a)
        c.restore()
        label(c, "1950 年代 · 法国 · 国营烟草厂", 540, 420, 38, INK, a * ctx.at("i01", 0.6, 0.3), box=True)
    # ---- i02: field work
    a = ctx.win("i02", "i03")
    if a > 0:
        notebook(c, 540, 760, 640, 400, a, prog=seg(t, ctx.ls("i02"), ctx.le("i02")))
        pen(c, 820, 900, 120, a)
        label(c, "实地调查", 540, 470, 56, INK, a, font_name="serif_heavy")
        label(c, "亲自到现场 · 去看 · 去问", 540, 1060, 36, INK2, a * ctx.at("i02", 0.6, 1.2))
    # ---- i03: the book
    a = ctx.win("i03", "i04")
    if a > 0:
        k = ctx.at("i03", 0.8)
        book(c, 330, 760, 300, 430, ["LE PHÉNOMÈNE", "BUREAUCRATIQUE"], "1963", (124, 92, 66), a * k, ang=-3, size=25)
        book(c, 750, 770, 300, 430, ["THE", "BUREAUCRATIC", "PHENOMENON"], "1964", (92, 86, 78), a * ctx.at("i03", 0.8, 0.5), ang=2, size=25)
        label(c, "《科层现象》", 540, 1070, 52, INK, a * ctx.at("i03", 0.6, 1.0), font_name="serif_heavy")
        draw_text(c, "法文原版 1963 · 英译本 1964", 540, 1135, "sans", 28, INK3, a * ctx.at("i03", 0.6, 1.2), align="center")
    # ---- i04-i05: glossary 科层制
    a = ctx.win("i04", "i06")
    if a > 0:
        def icons_row(cc, ww, hh):
            ia = ctx.at("i05", 0.6, 1.5)
            building_columns(cc, -230, hh / 2 - 52, 150, INK2, ia)
            office_tower(cc, 0, hh / 2 - 52, 170, INK2, ctx.at("i05", 0.6, 2.0))
            factory_icon(cc, 230, hh / 2 - 52, 170, INK2, ctx.at("i05", 0.6, 2.5))
            draw_text(cc, "政府机关", -230, hh / 2 - 12, "sans_bold", 30, INK2, ia, align="center")
            draw_text(cc, "大公司", 0, hh / 2 - 12, "sans_bold", 30, INK2, ctx.at("i05", 0.6, 2.0), align="center")
            draw_text(cc, "工厂", 230, hh / 2 - 12, "sans_bold", 30, INK2, ctx.at("i05", 0.6, 2.5), align="center")
        defs = ["学术用语，不是骂人的话"]
        if t >= ctx.ls("i05"):
            defs = ["学术用语，不是骂人的话", "按规章、按层级办事的组织"]
        gloss_card(c, 540, 770, 820, 640, "科层制 · 官僚制", defs, a, ang=-1.2, extra=icons_row)
    # ---- i06-i07: org chart glossary + the least conspicuous group
    a = ctx.win("i06", "i08")
    if a > 0:
        def tree(cc, ww, hh):
            pr = seg(t, ctx.ls("i06") + 0.6, ctx.ls("i06") + 2.6)
            nodes = [(0, -40), (-170, 70), (170, 70), (-250, 180), (-90, 180), (90, 180), (250, 180)]
            edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
            for k, (i0, i1) in enumerate(edges):
                ep = clamp(pr * 7 - k * 0.8)
                if ep > 0:
                    (x0, y0), (x1, y1) = nodes[i0], nodes[i1]
                    cc.drawLine(x0, y0, lerp(x0, x1, ep), lerp(y0, y1, ep), paint(INK2, 1, stroke=3))
            for k, (nx, ny) in enumerate(nodes):
                na = clamp(pr * 8 - k)
                if na > 0:
                    cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(nx - 44, ny - 26, 88, 52), 8, 8), paint(CARD, na))
                    cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(nx - 44, ny - 26, 88, 52), 8, 8), paint(INK2, na, stroke=2.5))
            # i07: highlight a side node
            hp = ease(seg(t, ctx.ls("i07") + 0.8, ctx.ls("i07") + 1.6))
            if hp > 0:
                nx, ny = nodes[3]
                cc.drawCircle(nx, ny + 70, 0, paint(INK))
                dp = paint(INK, hp, stroke=3)
                dp.setPathEffect(skia.DashPathEffect.Make([8, 8], t * 20))
                cc.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(nx - 58, ny - 40, 116, 80), 14, 14), dp)
                bust(cc, nx, ny - 6, 13, "maint", hp)
                draw_text(cc, "最不起眼？", nx + 66, ny + 64, "sans_bold", 32, INK, hp)
        gloss_card(c, 540, 770, 820, 680, "组织图", ["画着“谁管谁”的那张树状图"], a, ang=1.0, extra=tree)
    # ---- i08: the maintenance man
    a = ctx.win("i08", "i09")
    if a > 0:
        k = ease_back(seg(t, ctx.ls("i08") - 0.1, ctx.ls("i08") + 0.6))
        figure_side(c, 540, 1130, 520 * (0.85 + 0.15 * k), "maint", face=1, arm=0.55, a=a)
        label(c, "维修工", 540, 455, 64, INK, a, font_name="serif_heavy")
    # ---- i09: the question
    a = ctx.win("i09", None)
    if a > 0:
        a2 = a * (1 - ease(seg(t, ctx.le("i09") + 0.1, ctx.le("i09") + 0.5)))
        draw_text(c, "?", 540, 700, "garamond", 360, INK, a2 * ctx.at("i09", 0.6), align="center")
        draw_text(c, "权力，到底从哪儿来", 540, 1010, "serif_heavy", 66, INK, a2 * ctx.at("i09", 0.6, 1.6), align="center")


# =====================================================================================
# SECTION 1: cards cover the factory
# =====================================================================================
FAC_X, FAC_BOT, FAC_W, FAC_H = 110, 1185, 860, 430
SLOT_W, SLOT_H = 280, 132
SLOT_X0, SLOT_Y0 = 120, 790
MACHINE_SLOT = (2, 1)  # row, col left open


def slot_center(r, cidx):
    return SLOT_X0 + cidx * (SLOT_W + 6) + SLOT_W / 2, SLOT_Y0 + r * (SLOT_H + 3) + SLOT_H / 2


S1_CARDS = [
    # (line id, slot(row, col), title, sub)
    ("s1_02", (0, 0), "国家专卖", "MONOPOLE"),
    ("s1_03", (0, 1), "巴黎统一定", "PARIS"),
    ("s1_04", (0, 2), "三十家厂一个样", "~30 USINES"),
    ("s1_05", (1, 0), "车间编制", "L'ATELIER"),
    ("s1_07", (1, 1), "计件工资", "AUX PIÈCES"),
    ("s1_08", (1, 2), "资历排队", "ANCIENNETÉ"),
    ("s1_09", (2, 0), "照章办事", "RÈGLEMENT"),
    ("s1_10", (2, 2), "个人拿主意：最低", "MINIMUM"),
]
S1_NEXT = {"s1_02": "s1_03", "s1_03": "s1_04", "s1_04": "s1_05", "s1_05": "s1_07", "s1_07": "s1_08",
           "s1_08": "s1_09", "s1_09": "s1_10", "s1_10": "s1_11"}


def machine_window(c, t, running=1.0, glow=0.0, a=1.0):
    r, k = MACHINE_SLOT
    cx, cy = slot_center(r, k)
    c.drawRect(skia.Rect.MakeXYWH(cx - SLOT_W / 2, cy - SLOT_H / 2, SLOT_W, SLOT_H), paint(mix(PAPER_DEEP, INK4, 0.25), a))
    machine_side(c, cx - 100, cy + 58, 200, 96, t, running=running, a=a)
    if glow > 0:
        c.drawRect(skia.Rect.MakeXYWH(cx - SLOT_W / 2 - 4, cy - SLOT_H / 2 - 4, SLOT_W + 8, SLOT_H + 8), paint(ACCENT, glow, stroke=6))


def card_body(cid):
    """Return a body painter for the big readable version of each S1 card."""
    def b02(cc, w, h):
        factory_icon(cc, -170, 40, 120, INK2)
        draw_text(cc, "×1", -170, 90, "serif_heavy", 40, INK, 1, align="center")
        for k, xx in enumerate((60, 170, 280)):
            factory_icon(cc, xx, 40, 80, INK4)
            cc.drawLine(xx - 40, -20, xx + 40, 50, paint(INK, 1, stroke=4))
            cc.drawLine(xx + 40, -20, xx - 40, 50, paint(INK, 1, stroke=4))
        draw_text(cc, "全国烟草和火柴，只此一家 · 没有竞争", 0, h / 2 - 34, "serif_semi", 30, INK2, 1, align="center")

    def b03(cc, w, h):
        star(cc, -230, -10, 30, INK)
        draw_text(cc, "巴黎总部", -230, 45, "sans_bold", 26, INK, 1, align="center")
        for k, s in enumerate(["原料", "价格", "工资标准"]):
            yy = -50 + k * 52
            arrow(cc, -170, -10, 60, yy, INK2, 4, 1, head=14)
            draw_text(cc, s, 80, yy, "serif_bold", 34, INK, 1)
        draw_text(cc, "统一定，下面照办", 0, h / 2 - 34, "serif_semi", 30, INK2, 1, align="center")

    def b04(cc, w, h):
        for i in range(3):
            for j in range(10):
                factory_icon(cc, -300 + j * 66, -40 + i * 50, 40, INK3)
        draw_text(cc, "约 30 家工厂 · 组织方式几乎一模一样", 0, h / 2 - 34, "serif_semi", 30, INK2, 1, align="center")

    def b05(cc, w, h):
        bust(cc, -260, -40, 24, "chief")
        draw_text(cc, "车间主任 ×1", -260, 58, "sans_bold", 27, INK, 1, align="center")
        for i in range(3):
            for j in range(6):
                bust(cc, -95 + j * 34, -62 + i * 40, 10, "worker")
        draw_text(cc, "生产工人 60–120", 0, 58, "sans_bold", 27, INK, 1, align="center")
        for j in range(3):
            bust(cc, 220 + j * 40, -40, 14, "maint")
        draw_text(cc, "维修工 几人到十来人", 260, 58, "sans_bold", 27, INK, 1, align="center")
        draw_text(cc, "生产工人多为女工 · 维修工是男性技术工人", 0, h / 2 - 34, "serif_semi", 28, INK2, 1, align="center")

    def b07(cc, w, h):
        tt = cc_time[0]
        n = int(tt * 3) % 9 + 1
        for k in range(n):
            cc.drawRect(skia.Rect.MakeXYWH(-300 + k * 26, -30, 18, 60), paint(CARD))
            cc.drawRect(skia.Rect.MakeXYWH(-300 + k * 26, -30, 18, 60), paint(INK2, 1, stroke=1.5))
        arrow(cc, -40, 0, 60, 0, INK2, 5, 1, head=16)
        for k in range(n):
            coin(cc, 140 + (k % 3) * 46, 30 - (k // 3) * 22, 20)
        draw_text(cc, "做多少件，拿多少钱", 0, h / 2 - 34, "serif_semi", 32, INK2, 1, align="center")

    def b08(cc, w, h):
        years = ["1931", "1937", "1946", "1950", "1955"]
        for k, y in enumerate(years):
            xx = -240 + k * 120
            figure_side(cc, xx, 60, 110, "worker", face=-1, arm=0.1)
            draw_text(cc, y, xx, 82, "courier_bold", 22, INK2, 1, align="center")
        cc.drawLine(-300, 66, 300, 66, paint(INK3, 1, stroke=2))
        draw_text(cc, "按进厂年头排队：谁先来，谁先挑", 0, h / 2 - 30, "serif_semi", 30, INK2, 1, align="center")

    def b09(cc, w, h):
        items = ["干什么：写明", "怎么干：写明", "谁来分：照章"]
        for k, s in enumerate(items):
            yy = -50 + k * 46
            cc.drawRect(skia.Rect.MakeXYWH(-200, yy - 14, 28, 28), paint(INK2, 1, stroke=2.5))
            p = skia.Path().moveTo(-195, yy).lineTo(-187, yy + 9).lineTo(-170, yy - 12)
            cc.drawPath(p, paint(INK, 1, stroke=4))
            draw_text(cc, s, -150, yy, "serif_bold", 32, INK, 1)
        draw_text(cc, "几乎没有什么，留给个人拿主意", 0, h / 2 - 34, "serif_semi", 30, INK2, 1, align="center")

    def b10(cc, w, h):
        dial(cc, 0, 50, 110, 0.04, "个人拿主意", "")
        draw_text(cc, "“人说了算”：压到最低", 0, h / 2 - 34, "serif_semi", 30, INK2, 1, align="center")

    return {"s1_02": b02, "s1_03": b03, "s1_04": b04, "s1_05": b05, "s1_07": b07, "s1_08": b08,
            "s1_09": b09, "s1_10": b10}[cid]


cc_time = [0.0]


def sc_s1(c, ctx):
    t = ctx.t
    cc_time[0] = t
    zoom = ease(seg(t, ctx.ls("s1_11"), ctx.le("s1_11")))
    c.save()
    wx, wy = slot_center(*MACHINE_SLOT)
    camera(c, lerp(1.0, 1.25, zoom), cx=lerp(540, wx, zoom), cy=lerp(STAGE_CY, wy, zoom))
    # factory base
    fa = ease(seg(t, ctx.ls("s1_01") - 0.4, ctx.ls("s1_01") + 0.5))
    factory_front(c, FAC_X, FAC_BOT, FAC_W, FAC_H, a=fa)
    machine_window(c, t, 1.0, glow=0.55 * ease(seg(t, ctx.frac("s1_11", 0.55), ctx.le("s1_11"))), a=fa)
    # cards: settled ones first, then the one being shown
    showing = None
    for k, (lid, slot, title, sub) in enumerate(S1_CARDS):
        t_show = ctx.ls(lid) - 0.2
        nxt = S1_NEXT[lid]
        t_fly = ctx.ls(nxt) - 0.35 if lid != "s1_05" else ctx.ls("s1_07") - 0.35
        if t < t_show:
            continue
        sx, sy = slot_center(*slot)
        ang_s = (_hash(k, 3) - 0.5) * 6
        if t >= t_fly:
            f = ease(seg(t, t_fly, t_fly + 0.7))
            if f < 1:
                showing = (lid, title, sub, f, sx, sy, ang_s)
                continue
            card(c, sx, sy, SLOT_W, SLOT_H, title, lines=2, ang=ang_s, seed=k, title_size=34, sub=sub,
                 fill=mix(CARD, (200, 192, 178), 0.25))
        else:
            showing = (lid, title, sub, 0.0, sx, sy, ang_s)
    if showing:
        lid, title, sub, f, sx, sy, ang_s = showing
        ap = ease_back(seg(t, ctx.ls(lid) - 0.2, ctx.ls(lid) + 0.4))
        x = lerp(540, sx, f)
        y = lerp(560 - (1 - ap) * 120, sy, f)
        w = lerp(820, SLOT_W, f)
        h = lerp(340, SLOT_H, f)
        if f < 0.5:
            body = card_body(lid)
            c.save(); c.translate(x, y); sc = w / 820; c.scale(sc, sc)
            card(c, 0, 0, 820, 340, title, ang=lerp(-1.5, ang_s, f), title_size=50, sub=sub,
                 body_fn=lambda cc, ww, hh: body(cc, ww, hh), a=clamp(ap * 1.5))
            c.restore()
        else:
            card(c, x, y, w, h, title, lines=2, ang=lerp(-1.5, ang_s, f), title_size=lerp(50, 34, f), sub=sub)
    c.restore()
    if t > ctx.ls("s1_04") + 1.6 and t < ctx.ls("s1_05"):
        pass
