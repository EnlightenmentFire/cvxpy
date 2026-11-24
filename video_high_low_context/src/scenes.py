# -*- coding: utf-8 -*-
"""Scene illustrations. Each scene draws onto the illustration layer (1080 x 1000),
which sits at frame y = 290 .. 1290. Cards live at frame y >= 1000 (layer y >= 710),
so scenes that share the screen with cards keep their drawing above layer y ~ 690."""
import math
import functools

from PIL import Image

import gfx
from gfx import (BG, BG2, BG3, INK, INK2, INK3, LINE, TEAL, TEAL_L, WHITE, WOOD, WOOD_D, W,
                 C_WANG, C_MIKE, C_SARAH, C_CHEN, C_GRAY, C_SAND, C_PLUM, C_OLIVE, C_BROWN,
                 PAPER, PAPER_D, SEPIA, SEPIA2, RUST, Sprite, ease, ease_out, font, wrap)
from engine import appear, comp, T, P, ILL_Y0

LW, LH = 1080, 1000


def LY(frame_y):
    return frame_y - ILL_Y0


def first_card_t(sc, seg, kind=None):
    for c in sc.tl["cards"]:
        if c["seg"] == seg["id"] and (kind is None or c["kind"] == kind):
            return c["t0"]
    return None


def cards_in(sc, seg):
    return [c for c in sc.tl["cards"] if c["seg"] == seg["id"]]


def narr_lines(sc, seg):
    return [l for l in sc.tl["narr"] if l["seg"] == seg["id"]]


def footnote(txt, size=24, color=INK3, maxw=960):
    return T(txt, "r", size, color, maxw=maxw)


# ====================================================================== helpers
@functools.lru_cache(maxsize=32)
def room_floor(w=960, h=650, window=True):
    s = Sprite(w, h)
    s.rrect((0, 0, w - 1, h - 1), 36, fill=BG2)
    for i in range(1, 8):
        x = i * w / 8
        s.line([(x, 20), (x, h - 20)], (228, 221, 207), 2)
    if window:
        s.rrect((80, 14, w - 80, 34), 8, fill=(214, 228, 232))
        for i in range(1, 6):
            x = 80 + i * (w - 160) / 6
            s.line([(x, 14), (x, 34)], BG2, 4)
    return s.img()


@functools.lru_cache(maxsize=32)
def table_top(w=520, h=240):
    s = Sprite(w + 20, h + 20)
    s.rrect((10, 16, w + 10, h + 16), 60, fill=(0, 0, 0, 28))
    s.rrect((10, 10, w + 10, h + 10), 60, fill=WOOD, outline=WOOD_D, width=4)
    return s.img()


@functools.lru_cache(maxsize=32)
def laptop(rot=0):
    s = Sprite(84, 58)
    s.rrect((2, 2, 82, 56), 8, fill=(200, 204, 208), outline=(150, 154, 160), width=3)
    s.rrect((12, 10, 72, 40), 4, fill=(232, 236, 240))
    im = s.img()
    return im.rotate(rot, expand=True, resample=Image.BICUBIC) if rot else im


@functools.lru_cache(maxsize=32)
def teacup_small(rot=0):
    s = Sprite(56, 56)
    s.circle(28, 28, 24, fill=WHITE, outline=INK3, width=3)
    s.circle(28, 28, 15, fill=(196, 170, 110))
    return s.img()


@functools.lru_cache(maxsize=64)
def ptop(color, r=40, rot=0):
    im = gfx.person_top(color, r)
    return im.rotate(rot, expand=True, resample=Image.BICUBIC) if rot else im


@functools.lru_cache(maxsize=64)
def pfront(color, h=200, label=None):
    return gfx.person_front(color, h, label=label)


@functools.lru_cache(maxsize=64)
def bub(txt, size=40, fnt="m", maxw=520, tail="bl", fg=INK, bg=WHITE, outline=LINE):
    return gfx.bubble(txt, fnt, size, fg, bg, maxw=maxw, tail=tail, outline=outline)


@functools.lru_cache(maxsize=8)
def qmark_bubble():
    return gfx.bubble("？", "k", 64, INK, WHITE, maxw=200, tail="bc", padx=34, pady=10, outline=LINE)


def name_tag(txt, color):
    return P(txt, "b", 26, WHITE, color, padx=14, pady=5)


class Scene:
    shiyi = False
    card_y = 930
    takeaway_y = 1120

    def __init__(self):
        self.tl = None

    def draw(self, L, t, t0, trig, seg):
        pass


# ====================================================================== s01 meeting
class MeetingUS(Scene):
    shiyi = True

    def __init__(self):
        super().__init__()
        self.floor = room_floor(960, 590)
        self.table = table_top(520, 230)

    def people(self):
        return [  # (img, x, y)
            (ptop(C_MIKE, 42, 180), 540, 140, "Mike", C_MIKE),
            (ptop(C_WANG, 42, 0), 420, 495, "小王", C_WANG),
            (ptop(C_GRAY, 40, 0), 660, 495, None, None),
            (ptop(C_SAND, 40, 270), 190, 318, None, None),
            (ptop(C_PLUM, 40, 90), 890, 318, None, None),
        ]

    def draw(self, L, t, t0, trig, seg):
        appear(L, self.floor, 60, 30, t, t0 - 0.2, 0.5, "up", 10)
        appear(L, self.table, 540, 318, t, t0, 0.5, "up", 10, anchor="c")
        for i, (im, x, y, lab, col) in enumerate(self.people()):
            appear(L, im, x, y, t, t0 + 0.15 + i * 0.08, 0.4, "pop", anchor="c")
            if lab:
                tg = name_tag(lab, col)
                dy = -88 if y < 300 else 46
                appear(L, tg, x, y + dy, t, t0 + 0.6, 0.35, "up", 8, anchor="tc")
        for (x, y, r) in [(540, 228, 180), (420, 405, 0), (660, 405, 0), (300, 318, 270), (780, 318, 90)]:
            appear(L, laptop(r), x, y, t, t0 + 0.4, 0.4, "pop", anchor="c")
        ct = first_card_t(self, seg, "E")
        if ct is not None:
            b = bub("“Interesting idea!”", 34, "ens", 400, "bl")
            appear(L, b, 610, 30, t, ct, 0.35, "pop", t1=trig.get("calendar"))
        cal = trig.get("calendar")
        if cal is not None and t >= cal:
            days = ["3", "10", "17"]
            k = min(2, int((t - cal) / 1.25))
            im = gfx.icon_calendar(days[k], "星期一", 200)
            if k > 0 and (t - cal) - k * 1.25 < 0.25:
                p = ((t - cal) - k * 1.25) / 0.25
                im = im.resize((im.width, max(1, int(im.height * (0.6 + 0.4 * p)))), Image.BILINEAR)
            appear(L, im, 780, 18, t, cal, 0.35, "pop")
            appear(L, P("两周过去了", "b", 28, WHITE, INK), 880, 260, t, cal + 2.5, 0.35, "up", 10, anchor="tc")
        wq = trig.get("wang_q")
        if wq is not None:
            qb = qmark_bubble()
            appear(L, qb, 420, 455 - qb.height, t, wq + 0.2, 0.4, "pop", anchor="tc")


# ====================================================================== s02 meeting cn
class MeetingCN(Scene):
    shiyi = True

    def __init__(self):
        super().__init__()
        self.floor = room_floor(960, 590)
        self.table = table_top(560, 220)

    def draw(self, L, t, t0, trig, seg):
        appear(L, self.floor, 60, 30, t, t0 - 0.2, 0.5, "up", 10)
        appear(L, self.table, 540, 318, t, t0, 0.5, "up", 10, anchor="c")
        ppl = [(ptop(C_SARAH, 42, 0), 400, 495, "Sarah", C_SARAH), (ptop(C_GRAY, 40, 0), 640, 495, None, None),
               (ptop(C_CHEN, 42, 180), 460, 140, "陈经理", C_CHEN), (ptop(C_OLIVE, 40, 180), 680, 140, None, None)]
        for i, (im, x, y, lab, col) in enumerate(ppl):
            appear(L, im, x, y, t, t0 + 0.15 + i * 0.08, 0.4, "pop", anchor="c")
            if lab:
                tg = name_tag(lab, col)
                dy = -88 if y < 300 else 46
                appear(L, tg, x, y + dy, t, t0 + 0.6, 0.35, "up", 8, anchor="tc")
        for (x, y) in [(400, 405), (640, 405), (460, 232), (680, 232)]:
            appear(L, teacup_small(), x, y, t, t0 + 0.4, 0.4, "pop", anchor="c")
        # plant
        pl = Sprite(120, 120)
        pl.circle(60, 60, 54, fill=(150, 176, 140))
        pl.circle(60, 60, 30, fill=(124, 150, 112))
        appear(L, pl.img(), 140, 120, t, t0 + 0.3, 0.4, "pop")
        sch = trig.get("schedule")
        if sch is not None:
            appear(L, self.plan_board(), 600, 20, t, sch, 0.45, "pop")
            # launch bar slides in
            p = ease((t - sch - 0.5) / 0.8)
            if t > sch + 0.5:
                bar = Sprite(int(140 * p) + 2, 34)
                bar.rrect((0, 0, bar.w - 1, 33), 10, fill=C_SARAH)
                comp(L, bar.img(), 600 + 210, 20 + 196)
            if t > sch + 1.3:
                appear(L, T("上线", "b", 26, WHITE), 600 + 222, 20 + 194, t, sch + 1.3, 0.3, "pop")

    @functools.lru_cache(maxsize=2)
    def plan_board(self):
        s = Sprite(420, 260)
        s.rrect((0, 0, 419, 259), 22, fill=WHITE, outline=LINE, width=3)
        s.text((24, 34), "Sarah 的计划表", "b", 28, INK, anchor="lm")
        rows = [("设计", 0.0, 0.35), ("开发", 0.3, 0.7), ("上线", None, None)]
        for i, (lab, a, b) in enumerate(rows):
            y = 80 + i * 58
            s.text((24, y + 17), lab, "m", 26, INK2, anchor="lm")
            s.line([(100, y + 17), (400, y + 17)], BG2, 2)
            if a is not None:
                s.rrect((100 + a * 300, y + 2, 100 + b * 300, y + 32), 10, fill=C_SAND)
        return s.img()


# ====================================================================== title
class Title(Scene):
    oy = 60

    def draw(self, L, t, t0, trig, seg):
        appear(L, P("美国文化与职场", "b", 34, WHITE, INK, padx=22, pady=10), 540, 120, t, t0, 0.4, "up", 14, anchor="tc")
        appear(L, T("美国人", "k", 120, INK, align="center"), 540, 250, t, t0 + 0.15, 0.5, "up", 20, anchor="tc")
        appear(L, T("到底怎么说话", "k", 120, INK, align="center"), 540, 410, t, t0 + 0.3, 0.5, "up", 20, anchor="tc")
        b1 = bub("That's interesting.", 40, "ens", 600, "bl")
        b2 = bub("原则上同意。", 40, "b", 600, "br", bg=BG2)
        appear(L, b1, 110, 640, t, t0 + 0.7, 0.4, "pop")
        appear(L, b2, 970 - b2.width, 790, t, t0 + 1.0, 0.4, "pop")
        appear(L, T("同一句话 · 不同的耳朵", "m", 34, INK2, align="center"), 540, 960 - 60, t, t0 + 1.4, 0.5, "up", 10, anchor="tc")


# ====================================================================== hall
class Hall(Scene):
    card_y = 1000

    @functools.lru_cache(maxsize=1)
    def board(self):
        s = Sprite(760, 330)
        s.rrect((0, 0, 759, 329), 18, fill=(62, 76, 70), outline=(120, 100, 76), width=10)
        ch = (232, 232, 220)
        # clock
        s.circle(120, 130, 58, outline=ch, width=5)
        s.line([(120, 130), (120, 92)], ch, 5)
        s.line([(120, 130), (150, 146)], ch, 5)
        s.text((120, 238), "时间", "m", 28, ch, anchor="mm")
        # distance: two stick figures + arrow
        for x in (270, 400):
            s.circle(x, 92, 16, outline=ch, width=4)
            s.line([(x, 108), (x, 160)], ch, 4)
            s.line([(x - 22, 128), (x + 22, 128)], ch, 4)
            s.line([(x, 160), (x - 16, 196)], ch, 4)
            s.line([(x, 160), (x + 16, 196)], ch, 4)
        s.line([(296, 214), (374, 214)], ch, 4)
        s.poly([(374, 206), (388, 214), (374, 222)], fill=ch)
        s.poly([(296, 206), (282, 214), (296, 222)], fill=ch)
        s.text((335, 252), "距离", "m", 28, ch, anchor="mm")
        # silence bubble
        s.rrect((470, 76, 600, 168), 30, outline=ch, width=4)
        s.text((535, 116), "……", "m", 34, ch, anchor="mm")
        s.text((535, 238), "沉默", "m", 28, ch, anchor="mm")
        # occasion
        s.rrect((630, 86, 712, 168), 10, outline=ch, width=4)
        s.line([(640, 112), (702, 112)], ch, 3)
        s.text((671, 238), "场合", "m", 28, ch, anchor="mm")
        s.text((380, 296), "词汇之外的东西", "b", 30, ch, anchor="mm")
        return s.img()

    @functools.lru_cache(maxsize=4)
    def book(self, title, year, color):
        s = Sprite(250, 330)
        s.rrect((8, 8, 249, 329), 10, fill=(0, 0, 0, 40))
        s.rrect((0, 0, 240, 320), 10, fill=color)
        s.rect((0, 0, 22, 320), fill=tuple(max(0, c - 30) for c in color))
        y = 70
        for l in title.split("\n"):
            s.text((130, y), l, "enb", 30, WHITE, anchor="mm")
            y += 40
        s.rect((60, 200, 200, 204), fill=WHITE)
        s.text((130, 250), year, "enb", 40, WHITE, anchor="mm")
        s.text((130, 296), "Edward T. Hall", "en", 18, (240, 240, 240), anchor="mm")
        return s.img()

    @functools.lru_cache(maxsize=1)
    def quote_card(self):
        w = 960
        zh = ("高语境的交流，大部分信息要么在环境里，要么已经内化在人的心里，"
              "真正明说出来的部分很少。低语境的交流正好相反：大量信息都放在明说的话里。")
        f = font("m", 36)
        lines = wrap(zh, f, w - 90)
        h = 70 + len(lines) * 52 + 110
        s = Sprite(w, h)
        s.rrect((0, 0, w - 1, h - 1), 26, fill=WHITE, outline=LINE, width=2)
        s.rect((0, 26, 8, h - 26), fill=INK)
        s.text((44, 44), "霍尔的定义（中文意译）", "b", 28, INK2, anchor="lm")
        y = 78
        for l in lines:
            s.text((44, y), l, "m", 36, INK)
            y += 52
        s.text((44, y + 18), "Edward T. Hall, Beyond Culture (1976), p. 91", "eni", 24, INK3)
        return s.img()

    def draw(self, L, t, t0, trig, seg):
        appear(L, self.board(), 160, 40, t, t0, 0.5, "up", 12)
        appear(L, pfront((86, 96, 110), 230, None), 60, 240, t, t0 + 0.2, 0.45, "up")
        for i in range(6):
            x = 150 + i * 150
            im = gfx.person_front([C_SAND, C_GRAY, C_OLIVE, C_BROWN, C_PLUM, C_MIKE][i], 150)
            appear(L, im, x, 520 + (i % 2) * 14, t, t0 + 0.35 + i * 0.06, 0.4, "up")
        appear(L, footnote("示意图 · 1950 年代前半，美国国务院外交学院（Foreign Service Institute）的课堂"),
               60, 700, t, t0 + 0.6, 0.4, "up", 6)
        b1 = trig.get("book1959")
        if b1 is not None:
            appear(L, self.book("The Silent\nLanguage", "1959", (150, 112, 86)), 560, 300, t, b1, 0.5, "pop")
        b2 = trig.get("book1976")
        if b2 is not None:
            appear(L, self.book("Beyond\nCulture", "1976", (86, 110, 148)), 790, 330, t, b2, 0.5, "pop")

    def overlay(self, fr, t, t0, trig, seg):
        q = trig.get("book1976")
        if q is not None:
            appear(fr, self.quote_card(), 60, 1000, t, q + 2.6, 0.5, "up", 20)


# ====================================================================== soup
class Soup(Scene):
    shiyi = True
    card_y = 1000
    oy = 90

    def table(self):
        s = Sprite(940, 140)
        s.rrect((0, 0, 939, 40), 14, fill=WOOD, outline=WOOD_D, width=3)
        s.rect((60, 40, 84, 140), fill=WOOD_D)
        s.rect((856, 40, 880, 140), fill=WOOD_D)
        return s.img()

    @functools.lru_cache(maxsize=1)
    def bowl(self):
        s = Sprite(200, 150)
        for i, x in enumerate((70, 100, 130)):
            pts = [(x + 8 * math.sin(k / 4 + i), 10 + k * 6) for k in range(10)]
            s.line(pts, INK3, 4)
        s.pieslice((10, 30, 190, 150), 0, 180, fill=WHITE)
        s.ellipse((10, 66, 190, 102), fill=(226, 178, 110), outline=INK3, width=3)
        return s.img()

    def draw(self, L, t, t0, trig, seg):
        # family left, guest right
        fam = [(C_SARAH, 140, "妈妈"), (C_MIKE, 330, "爸爸"), (C_WANG, 520, "孩子")]
        for i, (c, x, lab) in enumerate(fam):
            h = 260 if lab != "孩子" else 200
            appear(L, pfront(c, h), x, 400 - h, t, t0 + i * 0.08, 0.4, "up")
            appear(L, T(lab, "m", 28, INK2), x + h * 0.31, 560, t, t0 + 0.4, 0.3, "up", 6, anchor="tc")
        guest_t = trig.get("guest_confused")
        gx = 790
        appear(L, pfront(C_PLUM, 260), gx, 140, t, t0 + 0.3, 0.4, "up")
        appear(L, T("外国客人", "m", 28, INK2), gx + 80, 560, t, t0 + 0.6, 0.3, "up", 6, anchor="tc")
        appear(L, self.table(), 70, 400, t, t0, 0.45, "up", 8)
        appear(L, self.bowl(), 380, 270, t, t0 + 0.3, 0.4, "pop")
        appear(L, gfx.icon_salt(50), 640, 330, t, t0 + 0.4, 0.4, "pop")
        appear(L, gfx.icon_kettle(90), 230, 322, t, t0 + 0.45, 0.4, "pop")
        ms = trig.get("mom_says")
        expl = trig.get("explicit")
        fg = trig.get("family_gets_it")
        if ms is not None:
            appear(L, bub("汤有点咸。", 42, "b", 400, "bl"), 120, 20, t, ms, 0.35, "pop", t1=fg)
        if fg is not None:
            salt = gfx.icon_salt(36)
            for i, (c, x, lab) in enumerate(fam):
                h = 260 if lab != "孩子" else 200
                cx = x + h * 0.31
                dot = Sprite(80, 80)
                dot.circle(40, 40, 38, fill=WHITE, outline=LINE, width=3)
                dot.paste(salt, 40 - salt.width / 2, 40 - salt.height / 2)
                appear(L, dot.img(), cx, 400 - h - 96, t, fg + 0.2 + i * 0.18, 0.4, "pop", anchor="tc", t1=expl)
            appear(L, P("一家人：都懂", "b", 26, WHITE, INK), 340, 612, t, fg + 0.8, 0.35, "up", 8, anchor="tc")
        if guest_t is not None:
            appear(L, bub("这是在抱怨？\n是让我别喝了？", 32, "m", 300, "br"), 650, 20, t, guest_t + 0.3, 0.35, "pop", t1=expl)
            appear(L, P("客人：一头雾水", "b", 26, WHITE, C_PLUM), 870, 612, t, guest_t + 0.8, 0.35, "up", 8, anchor="tc")
        if expl is not None:
            b = bub("汤咸了，我兑点开水；盐罐先拿开，别再加了。", 36, "m", 640, "bl")
            appear(L, b, 120, 10, t, expl, 0.4, "pop", t1=trig.get("defs"))

    def overlay(self, fr, t, t0, trig, seg):
        d = trig.get("defs")
        if d is not None:
            self.defs(fr, t, d, trig)

    @functools.lru_cache(maxsize=4)
    def def_card(self, which):
        w, h = 960, 190
        s = Sprite(w, h)
        if which == "high":
            title, l1, l2 = "高语境", "意思藏在关系、场合和语气里", "话说一半，听的人负责猜"
        else:
            title, l1, l2 = "低语境", "意思全部放进字面", "说的人负责说清楚"
        s.rrect((0, 0, w - 1, h - 1), 26, fill=WHITE, outline=LINE, width=2)
        # icon: iceberg (high) / open box (low)
        if which == "high":
            s.rect((40, 96, 190, 100), fill=(150, 190, 210))
            s.poly([(90, 96), (115, 50), (140, 96)], fill=(200, 220, 230))
            s.poly([(60, 100), (170, 100), (150, 150), (80, 150)], fill=(170, 200, 214))
        else:
            s.rrect((60, 46, 170, 140), 10, fill=(236, 230, 214), outline=INK3, width=3)
            for i in range(4):
                s.rrect((76, 62 + i * 18, 154 - (i % 2) * 20, 70 + i * 18), 4, fill=INK3)
        s.text((220, 50), title, "k", 46, INK, anchor="lm")
        s.text((220, 100), l1, "m", 34, INK, anchor="lm")
        s.text((220, 148), l2, "m", 32, INK2, anchor="lm")
        return s.img()

    def defs(self, L, t, d, trig):
        hi = self.def_card("high")
        lo = self.def_card("low")
        th = trig.get("def_high", d + 0.3)
        tlo = trig.get("def_low", d + 0.6)
        appear(L, hi, 60, 1052, t, th, 0.45, "up", 20)
        appear(L, lo, 60, 1052 + hi.height + 16, t, tlo, 0.45, "up", 20)


# ====================================================================== ruler
COUNTRIES1 = [("美国", 0.0, True), ("荷兰", 0.13, False), ("德国", 0.21, True), ("英国", 0.33, False),
              ("法国", 0.62, True), ("中国", 0.82, False), ("日本", 1.0, True)]
RX0, RX1 = 210, 870


def draw_ruler(L, t, t_show, y, left, right, sub_l="", sub_r="", alpha=1.0, title="", by=150):
    """Ruler sprite: optional title at y+22, bar at y+by, end labels beside the bar."""
    if t_show is None or t < t_show:
        return
    a = ease((t - t_show) / 0.5) * alpha
    s = Sprite(LW, by + 60)
    if title:
        s.text((LW / 2, 22), title, "b", 32, INK, anchor="mm")
    s.text((RX0 - 22, by - (12 if sub_l else 0)), left, "b", 30, INK, anchor="rm")
    s.text((RX1 + 22, by - (12 if sub_r else 0)), right, "b", 30, INK, anchor="lm")
    if sub_l:
        s.text((RX0 - 22, by + 24), sub_l, "r", 22, INK2, anchor="rm")
    if sub_r:
        s.text((RX1 + 22, by + 24), sub_r, "r", 22, INK2, anchor="lm")
    n = 48
    for i in range(n):
        xa = RX0 + (RX1 - RX0) * i / n
        xb = RX0 + (RX1 - RX0) * (i + 1) / n + 1
        s.rect((xa, by - 6, xb, by + 6), fill=(int(214 - 110 * i / n), int(206 - 112 * i / n), int(192 - 112 * i / n)))
    for i in range(11):
        x = RX0 + (RX1 - RX0) * i / 10
        s.line([(x, by - (12 if i % 5 == 0 else 8)), (x, by + (12 if i % 5 == 0 else 8))], INK2, 3)
    comp(L, s.img(), 0, y, a)


@functools.lru_cache(maxsize=64)
def country_pin(name, big=False, up=True, stem=40, wide=124):
    w = max(wide, 124) + 8
    nl = name.count("\n") + 1
    ph = 50 if nl == 1 else 20 + 32 * nl
    h = ph + stem + 10
    s = Sprite(w, h)
    col = INK if big else INK2
    cx = w / 2
    if up:
        s.rrect((cx - wide / 2, 0, cx + wide / 2, ph), 25, fill=col if big else WHITE, outline=col, width=3)
        for k, ln in enumerate(name.split("\n")):
            s.text((cx, ph / 2 + (k - (nl - 1) / 2) * 32 + 1), ln, "b", 26, WHITE if big else col, anchor="mm")
        s.line([(cx, ph), (cx, h - 10)], col, 3)
        s.circle(cx, h - 8, 7, fill=col)
    else:
        s.circle(cx, 8, 7, fill=col)
        s.line([(cx, 10), (cx, stem + 10)], col, 3)
        s.rrect((cx - wide / 2, stem + 10, cx + wide / 2, stem + 60), 25, fill=col if big else WHITE, outline=col,
                width=3)
        s.text((cx, stem + 36), name, "b", 26, WHITE if big else col, anchor="mm")
    return s.img()


def place_pins(L, t, ts, y_bar, countries, hl=("美国",), stagger=0.14, alpha=1.0):
    if ts is None or t < ts:
        return
    for i, c in enumerate(countries):
        nm, pos, up = c[0], c[1], c[2]
        wide = c[3] if len(c) > 3 else 124
        tt = ts + i * stagger
        if t < tt:
            continue
        x = RX0 + (RX1 - RX0) * pos
        im = country_pin(nm, nm in hl, up, 40, wide)
        yy = y_bar - im.height + 2 if up else y_bar - 8
        p = ease_out((t - tt) / 0.5)
        comp(L, im, x - im.width / 2, yy - (1 - p) * (20 if up else -20), ease((t - tt) / 0.35) * alpha)


class Ruler(Scene):
    oy = 150

    @functools.lru_cache(maxsize=1)
    def meyer_book(self):
        s = Sprite(240, 320)
        s.rrect((8, 8, 239, 319), 10, fill=(0, 0, 0, 40))
        s.rrect((0, 0, 230, 310), 10, fill=(196, 92, 72))
        s.text((115, 80), "The", "enb", 30, WHITE, anchor="mm")
        s.text((115, 120), "Culture", "enb", 38, WHITE, anchor="mm")
        s.text((115, 164), "Map", "enb", 38, WHITE, anchor="mm")
        for i in range(5):
            s.line([(40, 200 + i * 10), (190, 196 + i * 12)], (240, 200, 190), 2)
        s.text((115, 284), "Erin Meyer · 2014", "en", 20, WHITE, anchor="mm")
        return s.img()

    def draw(self, L, t, t0, trig, seg):
        mt = t0 + 0.2
        rt = trig.get("ruler")
        appear(L, self.meyer_book(), 80, 20, t, mt, 0.5, "pop")
        appear(L, T("艾琳·迈耶 Erin Meyer", "b", 34, INK), 360, 60, t, mt + 0.3, 0.4, "up", 8)
        appear(L, T("美国人，法国 INSEAD 商学院教授", "m", 30, INK2), 360, 114, t, mt + 0.45, 0.4, "up", 8)
        appear(L, T("《文化地图》The Culture Map（2014）", "m", 30, INK2), 360, 162, t, mt + 0.6, 0.4, "up", 8)
        appear(L, P("八把尺子 · 第一把：沟通", "b", 28, WHITE, INK), 360, 226, t, (rt or 1e9) + 0.2, 0.4, "up", 8)
        y = 400
        draw_ruler(L, t, rt, y, "低语境", "高语境", sub_l="靠字面", sub_r="靠语境")
        place_pins(L, t, trig.get("countries"), y + 150, COUNTRIES1)
        if trig.get("countries") is not None:
            appear(L, footnote("大致位置，据 Erin Meyer《The Culture Map》（2014）图 1.1 示意；\n排序是作者的观察和总结，不是测量结果"),
                   120, 700, t, trig["countries"] + 1.0, 0.4, "up", 6)


# ====================================================================== room
import random


class Room(Scene):
    oy = 70

    def __init__(self):
        super().__init__()
        rnd = random.Random(7)
        self.ppl = []
        cols = [C_WANG, C_MIKE, C_SARAH, C_CHEN, C_PLUM, C_OLIVE, C_BROWN, C_SAND, C_GRAY]
        spots = [(200, 230), (330, 170), (470, 250), (610, 180), (760, 230), (880, 170),
                 (180, 420), (330, 380), (480, 450), (640, 400), (790, 440), (900, 370)]
        for i, (x, y) in enumerate(spots):
            ang = rnd.uniform(0, 2 * math.pi)
            self.ppl.append(dict(x=x, y=y, c=cols[i % len(cols)], dx=math.cos(ang) * 600, dy=math.sin(ang) * 400,
                                 d=rnd.uniform(0, 0.9)))
        self.pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11),
                      (0, 6), (2, 8), (4, 10), (5, 11)]

    @functools.lru_cache(maxsize=1)
    def mini_bubble(self):
        s = Sprite(54, 40)
        s.rrect((0, 0, 53, 30), 10, fill=WHITE, outline=INK3, width=2)
        s.poly([(14, 29), (24, 29), (12, 39)], fill=WHITE)
        for i in range(3):
            s.rrect((10, 8 + i * 6, 44 - i * 8, 11 + i * 6), 2, fill=INK3)
        return s.img()

    def draw_strangers(self, L, t, t0, trig, ox=0, oy=0, sc=1.0, alpha=1.0, hide_room=False):
        fl = room_floor(900, 560, window=False)
        if sc != 1.0:
            fl = fl.resize((int(fl.width * sc), int(fl.height * sc)), Image.BILINEAR)
        if not hide_room:
            comp(L, fl, ox + 90 * sc, oy + 30 * sc, alpha * ease((t - t0 + 0.2) / 0.5))
        bt = trig.get("bubbles")
        if bt is not None and t > bt:
            ln = Sprite(LW, 800, ss=1)
            mids = []
            for k, (i, j) in enumerate(self.pairs):
                tt = bt + k * 0.08
                if t < tt:
                    continue
                a, b = self.ppl[i], self.ppl[j]
                pa = ease((t - tt) / 0.4)
                xa, ya = ox + a["x"] * sc, oy + a["y"] * sc
                xb, yb = ox + (a["x"] + (b["x"] - a["x"]) * pa) * sc, oy + (a["y"] + (b["y"] - a["y"]) * pa) * sc
                ln.line([(xa, ya), (xb, yb)], INK3, 3)
                if pa > 0.9:
                    mids.append(((xa + xb) / 2, (ya + yb) / 2))
            comp(L, ln.img(), 0, 0, alpha * 0.8)
            mb = self.mini_bubble()
            if sc != 1.0:
                mb = mb.resize((max(1, int(mb.width * max(sc, 0.6))), max(1, int(mb.height * max(sc, 0.6)))), Image.BILINEAR)
            for (mx, my) in mids:
                comp(L, mb, mx - mb.width / 2, my - mb.height * 0.85, alpha)
        for p in self.ppl:
            tt = t0 + p["d"]
            if t < tt:
                continue
            k = ease_out((t - tt) / 1.1)
            x = ox + (p["x"] + p["dx"] * (1 - k)) * sc
            y = oy + (p["y"] + p["dy"] * (1 - k)) * sc
            im = pfront(p["c"], int(110 * sc) if sc != 1 else 110)
            comp(L, im, x - im.width / 2, y - im.height / 2, alpha * ease((t - tt) / 0.4))

    def draw(self, L, t, t0, trig, seg):
        sc_t = trig.get("shared_cloud")
        if sc_t is None or t < sc_t:
            self.draw_strangers(L, t, t0, trig)
            appear(L, P("来自不同地方的人 · 没有共同的“背景”", "b", 28, WHITE, INK), 540, 620, t, t0 + 1.0, 0.4,
                   "up", 8, anchor="tc")
            return
        # split view
        p = ease((t - sc_t) / 0.7)
        sc = 1.0 - 0.5 * p
        self.draw_strangers(L, t, t0, trig, ox=0 + 10 * p, oy=230 * p, sc=sc)
        appear(L, T("陌生人社会：只能说出来", "b", 30, INK), 270, 180, t, sc_t + 0.4, 0.4, "up", 8, anchor="tc")
        # right: shared cloud group
        rx = 560
        appear(L, room_floor(460, 420, window=False), rx, 250, t, sc_t + 0.3, 0.5, "up", 10)
        cloud = Sprite(380, 150)
        for (cx, cy, r) in [(90, 90, 56), (160, 64, 64), (240, 78, 58), (300, 98, 46), (190, 110, 50)]:
            cloud.circle(cx, cy, r, fill=(214, 228, 232))
        cloud.text((190, 98), "共同的背景", "b", 30, INK2, anchor="mm")
        appear(L, cloud.img(), rx + 40, 270, t, sc_t + 0.7, 0.5, "pop")
        for i in range(5):
            im = pfront(C_CHEN if i % 2 else (126, 146, 112), 100)
            appear(L, im, rx + 60 + i * 72, 450 + (i % 2) * 20, t, sc_t + 0.5 + i * 0.06, 0.4, "up")
        appear(L, T("熟人社会：很多话不必说满", "b", 30, INK), rx + 230, 180, t, sc_t + 0.6, 0.4, "up", 8, anchor="tc")


# ====================================================================== email
class Email(Scene):
    oy = 40

    def draw(self, L, t, t0, trig, seg):
        appear(L, pfront(C_MIKE, 250), 120, 250, t, t0, 0.4, "up")
        appear(L, pfront(C_CHEN, 250), 780, 250, t, t0 + 0.1, 0.4, "up")
        appear(L, T("低语境的人", "b", 30, INK), 200, 520, t, t0 + 0.3, 0.3, "up", 6, anchor="tc")
        appear(L, T("高语境的人", "b", 30, INK), 860, 520, t, t0 + 0.3, 0.3, "up", 6, anchor="tc")
        ed = trig.get("email_doubt")
        appear(L, bub("话不说清？\n是不是藏着什么？", 32, "m", 340, "bl"), 60, 40, t, t0 + 0.6, 0.35, "pop", t1=ed)
        if ed is not None:
            p = ease((t - ed) / 1.0)
            env = gfx.icon_email(150)
            x = 270 + (600 - 270) * p
            y = 330 - 120 * math.sin(math.pi * p)
            comp(L, env, x - 75, y - 50, ease((t - ed) / 0.3))
            if t > ed + 0.4:
                comp(L, T("会议纪要", "m", 24, INK2), x - 48, y + 54, ease((t - ed - 0.4) / 0.3))
            appear(L, bub("你是不是\n不信任我？", 34, "m", 300, "br"), 690, 30, t, ed + 1.1, 0.35, "pop")
        ew = trig.get("email_why")
        if ew is not None:
            s = Sprite(460, 220)
            s.rrect((0, 0, 459, 219), 20, fill=WHITE, outline=LINE, width=2)
            s.text((26, 36), "Recap：今天的会议", "b", 28, INK, anchor="lm")
            s.rrect((26, 70, 434, 116), 10, fill=BG2)
            s.text((40, 93), "先说明：写下来，是怕大家漏掉", "m", 26, INK, anchor="lm")
            for i in range(3):
                s.rrect((26, 134 + i * 24, 400 - i * 60, 144 + i * 24), 5, fill=LINE)
            appear(L, s.img(), 310, 560, t, ew, 0.45, "pop")
            appear(L, P("迈耶的建议：多文化团队用低语境的规矩", "b", 28, WHITE, INK), 540, 800, t, ew + 0.8, 0.4, "up", 8,
                   anchor="tc")


# ====================================================================== caveat
class Caveat(Scene):
    oy = 60

    def draw(self, L, t, t0, trig, seg):
        w = 900
        s = Sprite(w, 120)
        s.text((w / 2, 60), "有用，但不是定律", "k", 64, INK, anchor="mm")
        appear(L, s.img(), 90, 40, t, t0, 0.45, "up", 12)
        items = [
            (t0 + 0.6, "依据", "大量访谈 + 作者自己的教学经验，案例多，系统数据少"),
            (trig.get("caveat2"), "批评", "学界有综述指出：高低语境理论缺少严格的实证检验（Cardon 2008）"),
            ((trig.get("caveat2") or 0) + 3.2 if trig.get("caveat2") else None, "另一种排法",
             "霍尔（1976）：美国“偏低，但不是最低”；德国、瑞士德语区、北欧更低"),
        ]
        y = 200
        for (tt, lab, txt) in items:
            card = Sprite(940, 150)
            card.rrect((0, 0, 939, 149), 22, fill=WHITE, outline=LINE, width=2)
            pl = pill(lab, "b", 26, WHITE, INK2, padx=14, pady=6)
            card.paste(pl, 26, 22)
            ls = wrap(txt, font("m", 32), 880)
            for i, l in enumerate(ls[:2]):
                card.text((28, 72 + i * 42), l, "m", 32, INK)
            appear(L, card.img(), 70, y, t, tt, 0.45, "up", 16)
            y += 170


def pill(txt, fnt, size, fg, bg, padx=16, pady=7):
    return gfx.pill(txt, fnt, size, fg, bg, padx=padx, pady=pady)


# ====================================================================== dictionary vignettes
class Dict(Scene):
    shiyi = True

    def __init__(self):
        super().__init__()

    def vignette(self, name, L, t, t0):
        if name == "coffee":
            m = Sprite(200, 300)
            m.rrect((0, 0, 199, 299), 20, fill=(120, 124, 130))
            m.rrect((30, 30, 170, 110), 10, fill=(180, 210, 214))
            m.rrect((60, 170, 140, 260), 10, fill=(90, 94, 100))
            m.rrect((78, 200, 122, 250), 8, fill=WHITE)
            appear(L, m.img(), 120, 300, t, t0, 0.4, "up")
            appear(L, pfront(C_SARAH, 260), 420, 340, t, t0 + 0.1, 0.4, "up")
            appear(L, pfront(C_WANG, 250), 700, 350, t, t0 + 0.15, 0.4, "up")
            appear(L, bub("Hey!", 40, "ens", 300, "bl"), 470, 200, t, t0 + 0.5, 0.35, "pop")
            appear(L, T("茶水间", "m", 28, INK3), 120, 620, t, t0 + 0.3, 0.3, "up", 6)
        elif name == "lunch":
            tb = Sprite(760, 60)
            tb.rrect((0, 0, 759, 30), 12, fill=WOOD, outline=WOOD_D, width=3)
            appear(L, pfront(C_CHEN, 240), 260, 330, t, t0, 0.4, "up")
            appear(L, pfront(C_WANG, 240), 640, 330, t, t0 + 0.1, 0.4, "up")
            appear(L, tb.img(), 160, 560, t, t0 + 0.05, 0.4, "up")
            for x in (300, 660):
                tr = Sprite(170, 40)
                tr.rrect((0, 0, 169, 30), 8, fill=(200, 204, 208))
                tr.circle(50, 14, 12, fill=(214, 120, 90))
                tr.circle(110, 14, 12, fill=(150, 180, 110))
                appear(L, tr.img(), x, 528, t, t0 + 0.3, 0.3, "pop")
            appear(L, T("午饭", "m", 28, INK3), 120, 620, t, t0 + 0.3, 0.3, "up", 6)
        elif name in ("meeting", "meeting_end"):
            fl = room_floor(900, 570, window=True)
            appear(L, fl, 90, 40, t, t0, 0.4, "up", 8)
            appear(L, table_top(460, 200), 540, 330, t, t0, 0.4, "up", 8, anchor="c")
            for (c, x, y, r) in [(C_MIKE, 540, 165, 180), (C_WANG, 430, 500, 0), (C_GRAY, 650, 500, 0),
                                 (C_SAND, 240, 330, 270), (C_PLUM, 840, 330, 90)]:
                appear(L, ptop(c, 40, r), x, y, t, t0 + 0.15, 0.35, "pop", anchor="c")
            appear(L, name_tag("Mike", C_MIKE), 540, 70, t, t0 + 0.4, 0.3, "up", 6, anchor="tc")
            appear(L, name_tag("小王", C_WANG), 430, 560, t, t0 + 0.4, 0.3, "up", 6, anchor="tc")
            if name == "meeting_end":
                wb = Sprite(330, 210)
                wb.rrect((0, 0, 329, 209), 16, fill=WHITE, outline=INK3, width=4)
                wb.text((20, 34), "Action items", "enb", 28, INK, anchor="lm")
                for i, h in enumerate(["谁", "做什么", "哪天之前"]):
                    wb.text((24 + i * 100, 82), h, "b", 24, INK2, anchor="lm")
                for r in range(2):
                    for i in range(3):
                        wb.rrect((24 + i * 100, 112 + r * 40, 100 + i * 100, 124 + r * 40), 5, fill=LINE)
                appear(L, wb.img(), 700, 60, t, t0 + 0.5, 0.4, "pop")
        elif name == "talk":
            desk = Sprite(520, 60)
            desk.rrect((0, 0, 519, 30), 10, fill=WOOD, outline=WOOD_D, width=3)
            appear(L, pfront(C_WANG, 230), 250, 330, t, t0, 0.4, "up")
            appear(L, pfront(C_MIKE, 280), 640, 290, t, t0 + 0.1, 0.4, "up")
            appear(L, desk.img(), 140, 540, t, t0 + 0.05, 0.4, "up")
            cal = Sprite(300, 170)
            cal.rrect((0, 0, 299, 169), 16, fill=WHITE, outline=LINE, width=3)
            for r in range(4):
                for c in range(5):
                    col = (214, 120, 90) if (r + c) % 3 else C_SAND
                    cal.rrect((16 + c * 56, 16 + r * 37, 62 + c * 56, 44 + r * 37), 6, fill=col)
            appear(L, cal.img(), 80, 80, t, t0 + 0.3, 0.4, "pop")
            appear(L, T("排满了", "b", 30, INK2), 230, 270, t, t0 + 0.5, 0.3, "up", 6, anchor="tc")
        elif name == "review":
            s = Sprite(600, 560)
            s.rrect((0, 0, 599, 559), 20, fill=WHITE, outline=INK3, width=3)
            s.text((40, 54), "Performance Review", "enb", 36, INK, anchor="lm")
            s.text((40, 100), "年度绩效评价（示意）", "m", 26, INK2, anchor="lm")
            for i in range(3):
                s.rrect((40, 140 + i * 30, 540 - i * 90, 152 + i * 30), 6, fill=LINE)
            labels = ["1", "2", "3", "4", "5"]
            for i, lb in enumerate(labels):
                x = 60 + i * 100
                s.rrect((x, 290, x + 80, 370), 14, fill=BG2 if i != 2 else (236, 230, 214),
                        outline=INK if i == 2 else LINE, width=4 if i == 2 else 2)
                s.text((x + 40, 330), lb, "enb", 36, INK if i == 2 else INK3, anchor="mm")
            s.text((60, 400), "低", "m", 24, INK3, anchor="lm")
            s.text((540, 400), "高", "m", 24, INK3, anchor="rm")
            s.ellipse((200, 430, 400, 500), outline=INK, width=4)
            s.text((300, 466), "Meets", "ens", 28, INK, anchor="mm")
            s.text((300, 530), "（在一些公司：中间一档）", "m", 24, INK2, anchor="mm")
            appear(L, s.img(), 240, 60, t, t0, 0.45, "pop")
        elif name == "email":
            s = Sprite(760, 420)
            s.rrect((0, 0, 759, 419), 22, fill=WHITE, outline=LINE, width=3)
            s.text((34, 42), "收件箱", "b", 30, INK, anchor="lm")
            rows = [("Recap：今天的会议 · 谁 / 做什么 / 哪天之前", True), ("周五团队午餐", False), ("系统维护通知", False),
                    ("Q3 计划草稿", False)]
            for i, (r, hl) in enumerate(rows):
                y = 84 + i * 80
                if hl:
                    s.rrect((20, y, 740, y + 68), 14, fill=BG2)
                    s.circle(44, y + 34, 8, fill=INK)
                s.text((70, y + 34), r, "b" if hl else "m", 28, INK if hl else INK3, anchor="lm")
            appear(L, s.img(), 160, 120, t, t0, 0.45, "pop")
            appear(L, gfx.icon_email(130), 120, 60, t, t0 + 0.3, 0.4, "pop")

    def draw(self, L, t, t0, trig, seg):
        vs = trig.get("vignettes", [])
        cur = None
        prev = None
        for i, (vt, vn) in enumerate(vs):
            if vt <= t:
                prev = cur
                cur = (vt, vn)
        if cur is None:
            # intro: dictionary cover
            s = Sprite(520, 620)
            s.rrect((10, 10, 519, 619), 24, fill=(0, 0, 0, 36))
            s.rrect((0, 0, 500, 600), 24, fill=C_MIKE)
            s.rect((0, 0, 40, 600), fill=(66, 88, 124))
            s.text((270, 200), "美国职场", "k", 64, WHITE, anchor="mm")
            s.text((270, 290), "小词典", "k", 64, WHITE, anchor="mm")
            s.text((270, 400), "Workplace", "enb", 36, (220, 228, 240), anchor="mm")
            s.text((270, 446), "Phrasebook", "enb", 36, (220, 228, 240), anchor="mm")
            s.text((270, 540), "（示意 · 常见说法）", "m", 26, (220, 228, 240), anchor="mm")
            appear(L, s.img(), 280, 40, t, t0, 0.5, "pop")
            return
        vt, vn = cur
        if prev is not None and t - vt < 0.35:
            pl = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
            self.vignette(prev[1], pl, t, prev[0])
            comp(L, pl, 0, 0, 1 - ease((t - vt) / 0.35))
        self.vignette(vn, L, t, vt)
        # counter
        es = [c for c in cards_in(self, seg) if c["kind"] == "E"]
        n = sum(1 for c in es if c["t0"] <= t)
        uniq = []
        for c in es:
            if c["en"].split(".")[0] not in uniq:
                uniq.append(c["en"].split(".")[0])
        if n:
            k = len({c["en"].split(".")[0].split("…")[0] for c in es if c["t0"] <= t})
            appear(L, P(f"小词典 {k}/7", "b", 26, WHITE, INK), 60, 24, t, vt, 0.3, "up", 6)


# ====================================================================== ruler 2
COUNTRIES1b = [("美国", 0.0, True), ("法国", 0.62, True), ("日本", 1.0, True)]
COUNTRIES2 = [("俄罗斯\n以色列\n荷兰", 0.03, True), ("德国", 0.2, False), ("法国", 0.31, True),
              ("美国", 0.52, False), ("英国", 0.62, True), ("日本", 1.0, False)]


class Ruler2(Scene):
    oy = 40

    def draw(self, L, t, t0, trig, seg):
        draw_ruler(L, t, t0, 0, "低语境", "高语境", alpha=0.8, title="第一把尺子：怎么讲事情")
        place_pins(L, t, t0 + 0.3, 150, COUNTRIES1b, hl=("美国", "法国"), alpha=0.8)
        r2 = trig.get("ruler2")
        draw_ruler(L, t, r2, 300, "直接", "委婉", title="第二把尺子：怎么批评人", by=210)
        place_pins(L, t, trig.get("countries2"), 300 + 210, COUNTRIES2, hl=("美国", "法国"))
        ft = trig.get("france")
        if ft is not None and t > ft:
            x1 = RX0 + (RX1 - RX0) * 0.62
            x2 = RX0 + (RX1 - RX0) * 0.31
            p = ease((t - ft) / 0.8)
            ln = Sprite(LW, 600, ss=1)
            ya, yb = 150 + 8, 510 - 100
            pts = [(x1, ya), (x1 + (x2 - x1) * p, ya + (yb - ya) * p)]
            ln.line(pts, INK, 5)
            ln.circle(pts[-1][0], pts[-1][1], 9, fill=INK)
            comp(L, ln.img(), 0, 0)
            appear(L, P("法国：讲事情偏“绕”，批评人却很直", "b", 30, WHITE, INK), 540, 660, t, ft + 0.6, 0.4, "up", 8,
                   anchor="tc")
        if trig.get("countries2") is not None:
            appear(L, footnote("大致位置，据《The Culture Map》（2014）图 1.1、图 2.2 示意"), 120, 750, t,
                   trig["countries2"] + 1.2, 0.4, "up", 6)


# ====================================================================== sandwich
@functools.lru_cache(maxsize=4)
def bread(w, h, label):
    s = Sprite(w, h)
    s.rrect((0, 0, w - 1, h - 1), h * 0.45, fill=(206, 160, 98))
    s.rrect((10, 8, w - 11, h - 10), h * 0.4, fill=(236, 204, 150))
    s.text((w / 2, h / 2), label, "b", 34, (120, 80, 40), anchor="mm")
    return s.img()


@functools.lru_cache(maxsize=4)
def filling(w, h, label):
    s = Sprite(w, h)
    s.rrect((0, 0, w - 1, h - 1), h / 2, fill=(196, 92, 72))
    s.text((w / 2, h / 2), label, "b", 28, WHITE, anchor="mm")
    return s.img()


class Sandwich(Scene):
    oy = 90

    def draw(self, L, t, t0, trig, seg):
        cx = 540
        appear(L, bread(420, 110, "好话 · 好话"), cx, 60, t, t0 + 0.1, 0.4, "down", 30, anchor="tc")
        appear(L, filling(380, 50, "问题"), cx, 182, t, t0 + 0.45, 0.4, "pop", anchor="tc")
        appear(L, bread(420, 110, "好话"), cx, 244, t, t0 + 0.75, 0.4, "up", 30, anchor="tc")
        appear(L, T("“三句表扬，配一句批评”", "b", 34, INK, align="center"), cx, 378, t, t0 + 1.1, 0.4, "up", 8,
               anchor="tc")
        dg = trig.get("downgraders")
        if dg is not None:
            appear(L, T("批评时的“减弱词”", "b", 30, INK2), 60, 462, t, dg, 0.3, "up", 6)
            for i, (en, zh) in enumerate([("a little", "有一点"), ("maybe", "也许"), ("kind of", "有那么点"),
                                          ("you might want to consider", "你或许可以考虑")]):
                ch = chip(en, zh)
                appear(L, ch, 60, 520 + i * 74, t, dg + 0.3 + i * 0.25, 0.35, "left", 20)
        ug = trig.get("upgraders")
        if ug is not None:
            appear(L, T("夸人时的用词", "b", 30, INK2), 640, 462, t, ug, 0.3, "up", 6)
            for i, (en, zh) in enumerate([("awesome", "太棒了"), ("amazing", "了不起"), ("excellent", "非常好")]):
                appear(L, chip(en, zh), 640, 520 + i * 74, t, ug + 0.3 + i * 0.25, 0.35, "right", 20)


@functools.lru_cache(maxsize=32)
def chip(en, zh):
    f1, f2 = font("ens", 32), font("m", 28)
    w = int(f1.getlength(en) + f2.getlength(zh) + 76)
    s = Sprite(w, 60)
    s.rrect((0, 0, w - 1, 59), 30, fill=WHITE, outline=LINE, width=2)
    s.text((22, 30), en, "ens", 32, INK, anchor="lm")
    s.text((w - 22, 30), zh, "m", 28, INK2, anchor="rm")
    return s.img()


class SandwichStory(Scene):
    oy = 90

    def draw(self, L, t, t0, trig, seg):
        appear(L, pfront(C_MIKE, 300), 150, 220, t, t0, 0.4, "up")
        appear(L, pfront(C_SARAH, 280), 700, 240, t, t0 + 0.1, 0.4, "up")
        appear(L, T("美国上司", "b", 28, INK), 245, 530, t, t0 + 0.3, 0.3, "up", 6, anchor="tc")
        appear(L, T("法国财务总监（派驻芝加哥）", "b", 28, INK), 790, 530, t, t0 + 0.3, 0.3, "up", 6, anchor="tc")
        bo = trig.get("bread_only")
        # praise bubbles
        for i, txt in enumerate(["做得很好", "很有想法", "团队很喜欢你"]):
            b = bub(txt, 30, "m", 300, "bl")
            appear(L, b, 340 + i * 30, 30 + i * 70, t, t0 + 0.8 + i * 0.45, 0.3, "pop", t1=bo)
        appear(L, bub("…表格可以再仔细一点", 22, "r", 300, "bl", fg=INK3), 380, 250, t, t0 + 2.4, 0.3, "pop", t1=bo)
        if bo is not None:
            # she holds two breads; the filling drops & fades
            appear(L, bread(220, 60, "好话"), 680, 80, t, bo, 0.35, "pop")
            appear(L, bread(220, 60, "好话"), 680, 150, t, bo + 0.15, 0.35, "pop")
            if t > bo + 0.6:
                p = ease((t - bo - 0.6) / 1.2)
                f = filling(180, 34, "问题")
                comp(L, f, 700 + 40 * p, 116 + 300 * p, 1 - p)
            appear(L, bub("最好的一次评价！", 32, "b", 360, "br"), 640, -10, t, bo + 1.2, 0.35, "pop")
            th = gfx.bubble("再不改进，恐怕保不住……", "m", 28, INK2, BG2, maxw=380, tail="bl")
            appear(L, th, 60, 40, t, bo + 2.6, 0.35, "pop")
        appear(L, footnote("据 Erin Meyer《The Culture Map》（2014）引言中的例子；书中人名为作者所用"), 60, 680, t, t0 + 1.0,
               0.4, "up", 6)


# ====================================================================== teacup
class Teacup(Scene):
    def draw(self, L, t, t0, trig, seg):
        card = Sprite(820, 400)
        card.rrect((0, 0, 819, 399), 30, fill=(238, 228, 212), outline=(214, 196, 170), width=4)
        card.rrect((16, 16, 803, 383), 22, outline=(214, 196, 170), width=2)
        appear(L, card.img(), 130, 40, t, t0, 0.45, "pop")
        appear(L, gfx.icon_teacup(300), 400, 70, t, t0 + 0.2, 0.45, "pop")
        appear(L, T("“英国人话语翻译表”", "k", 44, INK, align="center"), 540, 290, t, t0 + 0.4, 0.4, "up", 8, anchor="tc")
        appear(L, T("匿名网络段子 · 讲的是英国人 · 2004 年已有记载，2011 年走红", "m", 26, INK2, align="center"), 540,
               360, t, t0 + 0.6, 0.4, "up", 8, anchor="tc")
        appear(L, P("网络段子", "b", 28, WHITE, (170, 110, 80)), 150, 60, t, t0 + 0.5, 0.35, "pop")
        appear(L, footnote("在迈耶的第一把尺子上，英国是英语国家里最“高语境”的一个"), 140, 470, t, t0 + 1.5, 0.4, "up", 6)


# ====================================================================== chinese side
class CNPhrases(Scene):
    def draw(self, L, t, t0, trig, seg):
        appear(L, T("中文里，“听的人负责猜”的话", "b", 36, INK), 60, 10, t, t0, 0.4, "up", 8)
        appear(L, footnote("日常和职场里常见的客气话 · 真实意思要看关系、场合、语气"), 60, 60, t, t0 + 0.3, 0.4, "up", 6)


class OldFriends(Scene):
    oy = 70

    def draw(self, L, t, t0, trig, seg):
        cloud = Sprite(640, 200)
        for (cx, cy, r) in [(120, 120, 74), (230, 84, 90), (360, 96, 84), (470, 120, 66), (300, 140, 70)]:
            cloud.circle(cx, cy, r, fill=(214, 228, 232))
        cloud.text((300, 128), "多年的共同经历", "b", 34, INK2, anchor="mm")
        appear(L, cloud.img(), 220, 20, t, t0 + 0.4, 0.5, "pop")
        tb = Sprite(620, 60)
        tb.rrect((0, 0, 619, 30), 12, fill=WOOD, outline=WOOD_D, width=3)
        appear(L, pfront(C_CHEN, 260), 230, 300, t, t0, 0.4, "up")
        appear(L, pfront((126, 146, 112), 260), 680, 300, t, t0 + 0.1, 0.4, "up")
        appear(L, tb.img(), 230, 540, t, t0 + 0.05, 0.4, "up")
        for x in (380, 640):
            appear(L, teacup_small(), x, 500, t, t0 + 0.3, 0.3, "pop")
        appear(L, T("老同事", "b", 28, INK), 540, 610, t, t0 + 0.4, 0.3, "up", 6, anchor="tc")
        w = trig.get("wink")
        if w is not None:
            appear(L, bub("还行。", 44, "b", 300, "bl"), 330, 200, t, w, 0.35, "pop")
            sp = Sprite(300, 60)
            for i in range(7):
                sp.circle(20 + i * 42, 30, 6, fill=INK3)
            appear(L, sp.img(), 390, 330, t, w + 0.6, 0.4, "pop")
            appear(L, P("一句话 + 一个眼神 = 全部意思", "b", 28, WHITE, INK), 540, 660, t, w + 1.0, 0.4, "up", 8,
                   anchor="tc")


# ====================================================================== 1945 newspaper
class Newspaper(Scene):
    card_y = 1000

    @functools.lru_cache(maxsize=1)
    def paper(self):
        w, h = 960, 680
        s = Sprite(w, h)
        s.rect((0, 0, w - 1, h - 1), fill=PAPER, outline=PAPER_D, width=4)
        s.rect((24, 24, w - 25, 96), fill=SEPIA)
        for i in range(6):
            s.rrect((60 + i * 60, 46, 96 + i * 60, 74), 4, fill=PAPER_D)
        s.text((w - 50, 60), "1945 · 7 · 28", "enb", 30, PAPER, anchor="rm")
        s.line([(24, 110), (w - 25, 110)], SEPIA2, 3)
        # vertical columns of "text"
        for col in range(18):
            x = w - 50 - col * 50
            if 300 < x < 660:
                continue
            for k in range(10):
                y = 130 + k * 34
                ln = 22 if (col * 7 + k * 3) % 5 else 12
                s.rect((x - 4, y, x + 4, y + ln), fill=(180, 166, 140))
        return s.img()

    @functools.lru_cache(maxsize=1)
    def word(self):
        s = Sprite(380, 260)
        s.rect((0, 0, 379, 259), fill=(242, 234, 216), outline=SEPIA, width=4)
        s.text((190, 130), "黙殺", "jp", 150, SEPIA, anchor="mm")
        return s.img()

    @functools.lru_cache(maxsize=4)
    def meaning(self, n, txt, sub):
        s = Sprite(420, 118)
        s.rrect((0, 0, 419, 117), 18, fill=(250, 244, 230), outline=SEPIA2, width=3)
        s.text((24, 38), n, "b", 30, RUST, anchor="lm")
        s.text((70, 38), txt, "b", 30, SEPIA, anchor="lm")
        s.text((24, 86), sub, "m", 24, SEPIA2, anchor="lm")
        return s.img()

    def draw(self, L, t, t0, trig, seg):
        appear(L, self.paper(), 60, 20, t, t0, 0.5, "up", 10)
        wt = trig.get("word")
        if wt is not None:
            appear(L, self.word(), 540, 150, t, wt, 0.5, "pop", anchor="tc")
        jt = trig.get("jp")
        if jt is not None:
            appear(L, P("もくさつ · mokusatsu", "b", 30, PAPER, SEPIA, padx=20), 540, 424, t, jt, 0.35, "pop",
                   anchor="tc")
        at = trig.get("arrows")
        pk = trig.get("pick")
        if at is not None:
            m1 = self.meaning("①", "不理睬、置之不理", "词典里的意思")
            m2 = self.meaning("②", "不予置评、暂不回应", "战后一些回忆里的说法")
            a1, ax1, ay1 = gfx.arrow(440, 484, 300, 514, SEPIA2, 5, 16, curve=-10)
            a2, ax2, ay2 = gfx.arrow(640, 484, 780, 514, SEPIA2, 5, 16, curve=10)
            appear(L, a1, ax1, ay1, t, at, 0.4, "up", 0)
            appear(L, a2, ax2, ay2, t, at + 0.2, 0.4, "up", 0)
            fade2 = 1.0
            sc1 = 1.0
            if pk is not None and t > pk:
                fade2 = 1 - 0.75 * ease((t - pk) / 0.8)
                sc1 = 1 + 0.08 * ease((t - pk) / 0.8)
            if t >= at:
                a = ease((t - at) / 0.4)
                im1 = m1 if sc1 == 1 else m1.resize((int(m1.width * sc1), int(m1.height * sc1)), Image.BILINEAR)
                comp(L, im1, 270 - im1.width / 2, 518, a)
                comp(L, m2, 810 - m2.width / 2, 518, a * fade2 if t > at + 0.2 else 0)
        if pk is not None:
            s = Sprite(940, 70)
            s.rrect((0, 0, 939, 69), 14, fill=SEPIA)
            s.text((30, 35), "英译：ignore（无视）", "b", 30, PAPER, anchor="lm")
            s.text((470, 35), "→  西方报道：“日本拒绝”", "b", 30, (240, 200, 170), anchor="lm")
            appear(L, s.img(), 70, 664, t, pk + 0.5, 0.45, "up", 12)

    def overlay(self, fr, t, t0, trig, seg):
        ct = trig.get("caveat")
        if ct is not None:
            self.caveat(fr, t, ct, trig)

    def caveat(self, L, t, ct, trig):
        w = 960
        s = Sprite(w, 300)
        s.rrect((0, 0, w - 1, 299), 24, fill=WHITE, outline=LINE, width=2)
        s.rect((0, 24, 8, 276), fill=INK)
        s.text((40, 44), "史学界普遍认为", "b", 30, INK, anchor="lm")
        s.text((40, 96), "当时日本政府内部并没有准备接受公告。", "m", 32, INK, anchor="lm")
        s.text((40, 152), "「……黙殺、断乎戦争完遂に邁進する……」", "jp", 32, SEPIA, anchor="lm")
        s.text((40, 200), "后半句：坚决把战争进行到底（据当时日本报纸报道，各报措辞略有不同）", "r", 24, INK2, anchor="lm")
        s.text((40, 250), "出处：Butow 1954；Frank 1999；Hasegawa 2005 · 证据：表态明载，因果有争议", "r", 22, INK3,
               anchor="lm")
        appear(L, s.img(), 60, 1030, t, ct, 0.5, "up", 20)
        ot = trig.get("order")
        if ot is not None:
            s2 = Sprite(w, 130)
            s2.rrect((0, 0, w - 1, 129), 24, fill=BG2, outline=LINE, width=2)
            s2.text((40, 40), "· 盟军关键作战命令：7 月 25 日已下达，早于这次表态", "m", 30, INK, anchor="lm")
            s2.text((40, 90), "· “黙殺”算不算有歧义：学界至今仍有争论", "m", 30, INK, anchor="lm")
            appear(L, s2.img(), 60, 1342, t, ot, 0.5, "up", 20)

    takeaway_y = 1150


# ====================================================================== US map
US_POLY = [(-124.7, 48.4), (-123.0, 49.0), (-95.2, 49.0), (-94.8, 49.4), (-89.6, 48.0), (-84.8, 46.5),
           (-82.4, 43.0), (-83.1, 42.0), (-79.0, 42.9), (-76.5, 44.2), (-75.0, 45.0), (-71.5, 45.0),
           (-70.0, 46.7), (-69.2, 47.45), (-67.8, 47.1), (-67.0, 44.8), (-70.2, 43.6), (-70.6, 42.6),
           (-70.0, 41.7), (-71.4, 41.4), (-73.9, 40.6), (-74.0, 39.6), (-75.0, 38.8), (-76.0, 37.0),
           (-75.5, 35.2), (-77.9, 33.9), (-79.9, 32.7), (-81.4, 30.3), (-80.0, 26.8), (-80.4, 25.2),
           (-81.8, 26.2), (-82.7, 28.0), (-84.3, 30.0), (-86.5, 30.4), (-89.0, 30.3), (-89.4, 29.0),
           (-91.0, 29.3), (-93.8, 29.7), (-95.0, 29.2), (-97.2, 27.7), (-97.4, 26.0), (-99.5, 27.5),
           (-101.4, 29.8), (-103.2, 29.0), (-104.5, 29.6), (-106.5, 31.8), (-108.2, 31.8), (-111.1, 31.3),
           (-114.8, 32.5), (-117.1, 32.5), (-118.5, 34.0), (-120.6, 34.6), (-122.5, 37.7), (-123.8, 39.8),
           (-124.2, 41.9), (-124.0, 46.3)]
CITIES = [(-122.3, 47.6), (-122.4, 37.8), (-118.2, 34.05), (-105.0, 39.7), (-96.8, 32.8), (-87.6, 41.9),
          (-84.4, 33.7), (-74.0, 40.7), (-71.06, 42.36), (-80.2, 25.8), (-112.1, 33.4), (-93.3, 44.98),
          (-97.7, 30.3)]


def proj(lon, lat, x0=90, y0=40, w=900):
    k = math.cos(math.radians(38))
    sx = w / ((-66.5 + 125) * k)
    return x0 + (lon + 125) * k * sx, y0 + (49.6 - lat) * sx


class USMap(Scene):
    oy = 0

    @functools.lru_cache(maxsize=1)
    def base(self):
        s = Sprite(LW, 620)
        pts = [proj(*p) for p in US_POLY]
        s.poly([(x + 6, y + 8) for x, y in pts], fill=(0, 0, 0, 24))
        s.poly(pts, fill=(226, 218, 200), outline=INK3, width=3)
        for c in CITIES:
            x, y = proj(*c)
            s.circle(x, y, 9, fill=INK2)
            s.circle(x, y, 4, fill=WHITE)
        return s.img()

    def draw(self, L, t, t0, trig, seg):
        appear(L, self.base(), 0, 0, t, t0, 0.5, "up", 10)
        rnd = random.Random(3)
        pairs = [(0, 7), (2, 5), (8, 3), (4, 1), (6, 11), (9, 2), (10, 7), (12, 0), (5, 9), (3, 8), (11, 4), (1, 6)]
        for k, (i, j) in enumerate(pairs):
            start = t0 + 0.6 + k * 0.55
            per = 2.6
            if t < start:
                continue
            ph = ((t - start) % (per * 3)) / per
            if ph > 1.0:
                continue
            xa, ya = proj(*CITIES[i])
            xb, yb = proj(*CITIES[j])
            p = ease(ph)
            mx, my = (xa + xb) / 2, (ya + yb) / 2 - 90
            pts = []
            for q in range(0, 21):
                u = p * q / 20
                x = (1 - u) ** 2 * xa + 2 * (1 - u) * u * mx + u * u * xb
                y = (1 - u) ** 2 * ya + 2 * (1 - u) * u * my + u * u * yb
                pts.append((x, y))
            xs = [q[0] for q in pts]
            ys = [q[1] for q in pts]
            bx0, by0 = int(min(xs)) - 14, int(min(ys)) - 14
            ln = Sprite(int(max(xs)) - bx0 + 16, int(max(ys)) - by0 + 16)
            ln.line([(x - bx0, y - by0) for x, y in pts], (196, 92, 72), 4)
            hx, hy = pts[-1]
            ln.circle(hx - bx0, hy - by0, 9, fill=(196, 92, 72))
            comp(L, ln.img(), bx0, by0, 1 - ease((ph - 0.8) / 0.2))
        appear(L, P("换工作 · 换城市", "b", 28, WHITE, INK), 540, 600, t, t0 + 1.0, 0.4, "up", 8, anchor="tc")

    def overlay(self, L, t, t0, trig, seg):
        jt = trig.get("jobs")
        if jt is not None:
            appear(L, stat_card("≈13 份", "1957–64 年出生的美国人\n18 到 58 岁，平均做过 12.9 份工作",
                                "美国劳工统计局 NLSY79，2025 年发布"), 60, 1000, t, jt + 0.5, 0.45, "up", 20)
        tt = trig.get("tenure")
        if tt is not None:
            appear(L, stat_card("4.1 年", "在现在的雇主那里干了多久（中位数）\n其中 25–34 岁的人：3.0 年",
                                "美国劳工统计局 Employee Tenure，2026 年 1 月数据"), 60, 1190, t, tt + 0.3, 0.45,
                   "up", 20)


@functools.lru_cache(maxsize=8)
def stat_card(big, txt, src):
    w = 960
    s = Sprite(w, 170)
    s.rrect((0, 0, w - 1, 169), 24, fill=WHITE, outline=LINE, width=2)
    s.text((40, 84), big, "k", 64, INK, anchor="lm")
    f = font("m", 30)
    ls = []
    for part in txt.split("\n"):
        ls.extend(wrap(part, f, 610))
    for i, l in enumerate(ls[:2]):
        s.text((320, 40 + i * 42), l, "m", 30, INK)
    s.text((320, 136), src, "r", 22, INK3, anchor="lm")
    return s.img()


# ====================================================================== contract / rules
class Contract(Scene):
    oy = 60

    def draw(self, L, t, t0, trig, seg):
        doc = Sprite(560, 640)
        doc.rect((10, 12, 559, 639), fill=(0, 0, 0, 30))
        doc.rect((0, 0, 548, 626), fill=WHITE, outline=INK3, width=3)
        doc.text((274, 70), "AGREEMENT", "enb", 44, INK, anchor="mm")
        doc.text((274, 116), "合同 · 书面约定（示意）", "m", 26, INK2, anchor="mm")
        for i in range(9):
            doc.rrect((50, 160 + i * 34, 498 - (i % 3) * 40, 172 + i * 34), 5, fill=LINE)
        doc.line([(60, 520), (250, 520)], INK2, 2)
        doc.line([(300, 520), (490, 520)], INK2, 2)
        pts = [(70 + k * 9, 500 - 18 * math.sin(k / 2.2) - (k % 4) * 3) for k in range(20)]
        doc.line(pts, INK, 3)
        appear(L, doc.img(), 260, 20, t, t0, 0.5, "up", 16)
        st = t0 + 1.4
        if t > st:
            stamp = Sprite(240, 240)
            stamp.circle(120, 120, 112, outline=(196, 92, 72), width=10)
            stamp.circle(120, 120, 86, outline=(196, 92, 72), width=4)
            stamp.text((120, 104), "SIGNED", "enb", 40, (196, 92, 72), anchor="mm")
            stamp.text((120, 150), "已签署", "b", 34, (196, 92, 72), anchor="mm")
            im = stamp.img().rotate(-14, expand=True, resample=Image.BICUBIC)
            p = ease_out((t - st) / 0.25)
            s = 1.6 - 0.6 * p
            im2 = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            comp(L, im2, 640 - im2.width / 2, 470 - im2.height / 2, min(1, (t - st) / 0.15) * 0.92)
        appear(L, P("书面合同 · 诉讼 · 留下记录", "b", 28, WHITE, INK), 540, 680, t, t0 + 2.0, 0.4, "up", 8, anchor="tc")


class Rules(Scene):
    oy = 90

    def draw(self, L, t, t0, trig, seg):
        tiles = [
            ("会议结束前", "谁、做什么、哪天之前", "board"),
            ("散会后", "发邮件复述结论", "email"),
            ("绩效评价", "一条一条写下来", "doc"),
        ]
        for i, (h, sub, kind) in enumerate(tiles):
            s = Sprite(300, 380)
            s.rrect((0, 0, 299, 379), 26, fill=WHITE, outline=LINE, width=2)
            if kind == "board":
                s.rrect((50, 40, 250, 180), 12, outline=INK3, width=4)
                s.text((150, 70), "Action items", "enb", 22, INK, anchor="mm")
                for r in range(3):
                    s.rrect((70, 100 + r * 24, 230 - r * 30, 110 + r * 24), 4, fill=LINE)
            elif kind == "email":
                s.paste(gfx.icon_email(190), 55, 50)
                s.text((150, 200), "Recap", "enb", 26, INK2, anchor="mm")
            else:
                s.paste(gfx.icon_doc(140, 170, 5, None), 80, 30)
            s.text((150, 262), h, "b", 34, INK, anchor="mm")
            ls = wrap(sub, font("m", 25), 270)
            for k, l in enumerate(ls):
                s.text((150, 312 + k * 34), l, "m", 25, INK2, anchor="mm")
            appear(L, s.img(), 60 + i * 330, 40, t, t0 + 0.3 + i * 1.6, 0.45, "pop")
        nw = trig.get("not_written")
        if nw is not None:
            s = Sprite(900, 150)
            s.rrect((0, 0, 899, 149), 30, fill=INK)
            s.text((450, 75), "没写下来 ＝ 没发生", "k", 60, WHITE, anchor="mm")
            appear(L, s.img(), 90, 470, t, nw, 0.5, "pop")
            appear(L, footnote("美国职场常见的一句口头禅（不是法律规定）"), 540, 640, t, nw + 0.8, 0.4, "up", 6, anchor="tc")


# ====================================================================== ending
class Ending(Scene):
    oy = 90

    def draw(self, L, t, t0, trig, seg):
        ec = trig.get("endcard")
        fade = 1.0 if ec is None or t < ec else 1 - ease((t - ec) / 0.6)
        if fade > 0:
            lay = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
            l1, l2, l3 = trig.get("l1"), trig.get("l2"), trig.get("l3")
            appear(lay, T("低语境，不是更真诚；", "k", 58, INK, align="center"), 540, 60, t, l1, 0.5, "up", 16, anchor="tc")
            appear(lay, T("高语境，也不是更虚伪。", "k", 58, INK, align="center"), 540, 150, t, (l1 or 0) + 1.6 if l1 else None,
                   0.5, "up", 16, anchor="tc")
            appear(lay, T("一个是陌生人合作时，成本最低的办法；", "m", 40, INK2, align="center"), 540, 300, t, l2, 0.5, "up",
                   12, anchor="tc")
            appear(lay, T("一个是老熟人之间，效率最高的办法。", "m", 40, INK2, align="center"), 540, 366, t,
                   (l2 or 0) + 2.4 if l2 else None, 0.5, "up", 12, anchor="tc")
            if l3 is not None:
                appear(lay, gfx.icon_ear(170, INK), 300, 470, t, l3, 0.5, "pop")
                appear(lay, gfx.icon_ear(170, TEAL).transpose(Image.FLIP_LEFT_RIGHT), 610, 470, t, l3 + 0.3, 0.5, "pop")
                appear(lay, T("换了地方，就得换一副耳朵。", "k", 56, INK, align="center"), 540, 680, t, l3 + 0.4, 0.5, "up",
                       14, anchor="tc")
            comp(L, lay, 0, 0, fade)
        if ec is not None and t >= ec:
            a = ease((t - ec - 0.3) / 0.6)
            s = Sprite(LW, 900)
            s.text((540, 80), "美国人到底怎么说话", "k", 60, INK, anchor="mm")
            s.text((540, 150), "「美国文化与职场」", "m", 34, INK2, anchor="mm")
            s.rrect((90, 230, 990, 380), 24, fill=WHITE, outline=LINE, width=2)
            s.text((540, 272), "下期预告", "b", 28, INK2, anchor="mm")
            s.text((540, 330), "美国人的时间表：“准时”到底是几点？", "b", 38, INK, anchor="mm")
            refs = ["主要参考：Edward T. Hall《The Silent Language》1959、《Beyond Culture》1976；",
                    "Erin Meyer《The Culture Map》2014；R. Butow《Japan's Decision to Surrender》1954；",
                    "美国劳工统计局 NLSY79（2025）、Employee Tenure（2026）。",
                    "本期职场场景均为示意，不指向任何真实的人或公司。"]
            for i, r in enumerate(refs):
                s.text((540, 470 + i * 44), r, "r", 24, INK2, anchor="mm")
            comp(L, s.img(), 0, 60, a)


SCENES = {
    "meeting_us": MeetingUS, "meeting_cn": MeetingCN, "title": Title, "hall": Hall, "soup": Soup,
    "ruler": Ruler, "room": Room, "email": Email, "caveat": Caveat, "dict": Dict, "ruler2": Ruler2,
    "sandwich": Sandwich, "sandwich_story": SandwichStory, "teacup": Teacup, "cn_phrases": CNPhrases,
    "old_friends": OldFriends, "newspaper": Newspaper, "usmap": USMap, "contract": Contract, "rules": Rules,
    "ending": Ending,
}

_TL = None


def make(name):
    sc = SCENES[name]()
    sc.tl = _TL
    return sc
