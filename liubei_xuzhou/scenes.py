# -*- coding: utf-8 -*-
"""各场景画面。每个场景函数 f(ctx, t, S)：t 为全片绝对时间，S 为场景信息（含句子时间）。"""
import math

import cairo
import numpy as np

import engine as E
import geomap as G
import widgets as Wd
import polys
from engine import W, H, C, clamp, prog, ease_out, ease_in, ease_io, smooth, lerp, fade

SC = {}


def scene(name, qy=1120):
    def deco(f):
        f.qy = qy
        SC[name] = f
        return f
    return deco


class S_:
    def __init__(self, sc, lines):
        self.t0, self.t1, self.name = sc["t0"], sc["t1"], sc["sc"]
        self.ls = {ln["id"]: (ln["t0"], ln["t1"]) for ln in lines if ln["sc"] == sc["sc"] and sc["t0"] - 0.01 <= ln["t0"] <= sc["t1"]}

    def a(self, i):
        return self.ls[i][0] if i in self.ls else self.t0

    def b(self, i):
        return self.ls[i][1] if i in self.ls else self.t1

    def p(self, i, d=None, off=0.0):
        a, b = self.a(i) + off, self.b(i)
        return prog(self._t, a, d if d else max(0.3, b - a))


# ── 小工具 ────────────────────────────────────────────────
def caption(ctx, text, a, y=300, col=None, size=44):
    if a <= 0.01:
        return
    w, h = E.text_size(text, "serif", "Bold", size)
    E.set_col(ctx, "#000000", 0.45 * a)
    E.rrect_path(ctx, W / 2 - w / 2 - 34, y - h / 2 - 14, w + 68, h + 28, 8); ctx.fill()
    E.line(ctx, W / 2 - w / 2 - 20, y + h / 2 + 8, W / 2 + w / 2 + 20, y + h / 2 + 8, col or C["gold"], 2, 0.6 * a)
    E.draw_text(ctx, text, W / 2, y, "serif", "Bold", size, "#f3e7cc", a, "cm", shadow=5)


def dark_bg(ctx, tone="#0e0c0a", tone2="#1b1712", seed=1):
    E.paint_surface(ctx, E.paper_texture(seed, tone, tone2))


def tint_poly(ctx, cam, name, col, a, edge=None):
    if a <= 0.01:
        return
    P = polys.load()[name]
    ctx.new_path()
    for rings in P:
        for ring in rings:
            for i, (lon, lat) in enumerate(ring):
                x, y = cam(lon, lat)
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            ctx.close_path()
    E.set_col(ctx, col, a)
    ctx.fill_preserve()
    E.set_col(ctx, edge or col, min(1, a * 2.2)); ctx.set_line_width(3); ctx.stroke()


def fortress(ctx, x, y, s, col="#d8c8a6", alpha=1.0, banner=None):
    """简笔城池：城墙＋城楼"""
    if alpha <= 0.01:
        return
    E.set_col(ctx, "#0c0a08", 0.7 * alpha); ctx.rectangle(x - s * 1.05, y - s * 0.55, s * 2.1, s * 0.85); ctx.fill()
    E.set_col(ctx, col, alpha)
    ctx.set_line_width(max(2, s * 0.07))
    ctx.rectangle(x - s, y - s * 0.5, s * 2, s * 0.75); ctx.stroke()
    for k in range(-4, 5):
        ctx.rectangle(x + k * s * 0.22 - s * 0.06, y - s * 0.62, s * 0.12, s * 0.12)
    ctx.fill()
    ctx.move_to(x - s * 0.45, y - s * 0.5); ctx.line_to(x - s * 0.35, y - s * 0.95); ctx.line_to(x + s * 0.35, y - s * 0.95)
    ctx.line_to(x + s * 0.45, y - s * 0.5); ctx.stroke()
    ctx.move_to(x - s * 0.6, y - s * 0.95); ctx.line_to(x, y - s * 1.25); ctx.line_to(x + s * 0.6, y - s * 0.95); ctx.close_path(); ctx.fill()
    ctx.arc(x, y + s * 0.25, s * 0.25, math.pi, 0); ctx.line_to(x + s * 0.25, y + s * 0.25); ctx.close_path()
    E.set_col(ctx, "#0c0a08", alpha); ctx.fill()


def figure(ctx, x, y, s, col, alpha=1.0, rise=1.0, seated=False, hat=True):
    """简笔人像剪影（古装）。y 为脚底。"""
    if alpha <= 0.01:
        return
    E.set_col(ctx, col, alpha)
    hh = s * (0.78 if seated else 1.0) * lerp(0.82, 1.0, rise)
    # 袍
    ctx.move_to(x - s * 0.34, y)
    ctx.curve_to(x - s * 0.30, y - hh * 0.45, x - s * 0.22, y - hh * 0.62, x - s * 0.16, y - hh * 0.74)
    ctx.line_to(x + s * 0.16, y - hh * 0.74)
    ctx.curve_to(x + s * 0.22, y - hh * 0.62, x + s * 0.30, y - hh * 0.45, x + s * 0.34, y)
    ctx.close_path(); ctx.fill()
    # 袖
    ctx.move_to(x - s * 0.18, y - hh * 0.70); ctx.curve_to(x - s * 0.42, y - hh * 0.55, x - s * 0.40, y - hh * 0.40, x - s * 0.22, y - hh * 0.36)
    ctx.line_to(x + s * 0.22, y - hh * 0.36); ctx.curve_to(x + s * 0.40, y - hh * 0.40, x + s * 0.42, y - hh * 0.55, x + s * 0.18, y - hh * 0.70)
    ctx.close_path(); ctx.fill()
    # 头
    ctx.arc(x, y - hh * 0.83, s * 0.10, 0, 6.283); ctx.fill()
    if hat:
        ctx.rectangle(x - s * 0.05, y - hh * 0.99, s * 0.10, s * 0.08); ctx.fill()


def name_tile(ctx, x, y, name, sub, col, a=1.0, size=64, w=None):
    if a <= 0.01:
        return
    tw = max(E.text_size(name, "serif", "Black", size)[0], E.text_size(sub, "sans", "Regular", 28)[0] if sub else 0)
    w = w or tw + 70
    E.rrect_path(ctx, x - w / 2, y - size * 0.95, w, size * (1.9 if sub else 1.5), 10)
    E.set_col(ctx, "#0b0907", 0.8 * a); ctx.fill_preserve()
    E.set_col(ctx, col, 0.85 * a); ctx.set_line_width(3); ctx.stroke()
    E.rect(ctx, x - w / 2, y - size * 0.95, 10, size * (1.9 if sub else 1.5), col, a)
    E.draw_text(ctx, name, x + 5, y - size * 0.2, "serif", "Black", size, "#f4ead4", a, "cm")
    if sub:
        E.draw_text(ctx, sub, x + 5, y + size * 0.55, "sans", "Regular", 28, "#cfc3aa", a, "cm")


def big_text(ctx, text, x, y, size, col, a, family="serif", weight="Black", scale=1.0, anchor="cm", tracking=0.05):
    E.draw_text(ctx, text, x, y, family, weight, size, col, a, anchor, tracking=tracking, shadow=8, scale=scale)


# 预置兵团
TR = {}


def troop(key, *args, **kw):
    if key not in TR:
        TR[key] = Wd.Troop(*args, **kw)
    return TR[key]


FS = {}


def flagsea(key, *args, **kw):
    if key not in FS:
        FS[key] = Wd.FlagSea(*args, **kw)
    return FS[key]


# 相机
CAM_XU = G.Cam(117.75, 34.85, 300)
CAM_MACRO = G.Cam(116.7, 35.2, 205)
CAM_NORTH = G.Cam(116.9, 36.55, 270)
CAM_CLOSE = G.Cam(117.55, 34.55, 640)
CAM_TAN = G.Cam(118.58, 34.60, 1000)


# ═════════════════════ 冷开场 ═════════════════════
@scene("hook", qy=1150)
def hook(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.9, 34.75, 380), G.Cam(117.75, 34.85, 330), ease_io(prog(t, S.t0, 10)))
    G.base(ctx, cam, dim=0.85, prov_labels=False)
    tan = cam.p("郯")
    # 曹军黑旗海：从西北压向郯
    sea_c = (tan[0] - 330 + 60 * ease_out(prog(lt, 0, 9)), tan[1] - 40)
    tr = troop("hook_cao", 4200, (420, 330), 5, "#121110", C["gold"], 4.2)
    tr.draw(ctx, sea_c[0], sea_c[1] + 40, t, 0.95, march=0.4)
    for k, (fx, fy) in enumerate([(-170, -140), (-40, -210), (60, -60), (-230, 60), (-90, 120), (40, 190)]):
        Wd.fire(ctx, sea_c[0] + fx, sea_c[1] + fy + 60, 16, t, 0.75, seed=k)
        Wd.smoke(ctx, sea_c[0] + fx, sea_c[1] + fy + 40, 30, t, 0.8, seed=k)
    flagsea("hook", 90, 820, 600).draw(ctx, sea_c[0], sea_c[1], t, size=32, char="曹", persp=0.5)
    # 黑色粗箭头压向郯
    Wd.thick_arrow(ctx, [(sea_c[0] - 200, sea_c[1] - 300), (sea_c[0] + 40, sea_c[1] - 90), (tan[0] - 70, tan[1] - 10)],
                   ease_out(prog(lt, 0.0, 2.2)), 70, 110, **Wd.arrow_style("cao"))
    fortress(ctx, tan[0], tan[1], 58, "#e8dcc0")
    E.draw_text(ctx, "郯", tan[0], tan[1] + 70, "serif", "Black", 54, "#f4ead4", 1, "ct", shadow=6)
    E.draw_text(ctx, "徐州治所", tan[0], tan[1] + 132, "sans", "Regular", 28, "#cfc3aa", 0.9, "ct", shadow=4)
    # 红色小队：从北方地平线冲来
    path = [(tan[0] + 60, -60), (tan[0] + 130, 260), (tan[0] + 90, tan[1] - 260), (tan[0] + 40, tan[1] - 90)]
    f = ease_out(prog(lt, 0.2, 5.5))
    Wd.thick_arrow(ctx, path, f, 14, 30, **Wd.arrow_style("liu"))
    x, y, ang = E.point_along(E.smooth_path(path, 10), max(0.02, f * 0.96))
    troop("hook_liu", 150, (34, 60), 9, C["red2"], "#ffd7cc", 5.0).draw(ctx, x, y - 40, t, 1.0, ang=ang - math.pi / 2, march=1)
    Wd.flag(ctx, x + 10, y - 90, 34, C["red"], "#ffd0c4", t, 1.0, 0.3, "刘")
    # 体量对比标签
    a = fade(lt, 1.0, None, 0.6)
    Wd.label_pill(ctx, "曹操大军", sea_c[0] - 40, sea_c[1] + 300, "#1a1918", a, 32, C["gold2"])
    Wd.label_pill(ctx, "不足两千", x + 120, y - 30, C["red"], a * clamp((f - 0.2) * 3), 30, "#fff2ee")
    # 一年后：徐州染红
    p2 = prog(t, S.a("o02") + 0.6, 2.0)
    tint_poly(ctx, cam, "徐州", C["red"], 0.30 * ease_out(p2), C["red2"])
    if p2 > 0:
        big_text(ctx, "一年后", W / 2, 470, 96, "#f3e3c8", ease_out(p2))
    caption(ctx, "公元194年 · 徐州", fade(lt, 0.0, None, 0.3))


@scene("who", qy=1210)
def who(ctx, t, S):
    dark_bg(ctx)
    a0 = fade(t, S.t0, None, 0.4)
    name_tile(ctx, W / 2, 420, "刘备", "平原相 · 田楷副手 · 公孙瓒阵营", C["red"], a0, 92, 640)
    # 三堆家底
    items = [("千余人", "自有兵", 1000, C["red2"], 0), ("乌丸杂胡骑", "幽州骑兵", 300, "#d98a6a", 1), ("饥民数千", "沿路收拢", 3000, "#a49a88", 2)]
    pa = prog(t, S.a("o04"), 3.0)
    for i, (lab, sub, n, col, k) in enumerate(items):
        cx = 200 + i * 340
        ai = ease_out(clamp(pa * 3 - i))
        tr = troop(f"who{i}", min(n // 4 + 40, 700), (120, 120) if i != 2 else (140, 150), 20 + i, col, None, 4.5 if i < 2 else 3.6)
        tr.draw(ctx, cx, 760, t, ai, count=int(tr.n * ai))
        E.draw_text(ctx, lab, cx, 930, "serif", "Black", 46, "#f2e6cc", ai, "cm")
        E.draw_text(ctx, sub, cx, 985, "sans", "Regular", 28, "#bfb39b", ai, "cm")
    E.draw_text(ctx, "史书里的家底", W / 2, 600, "sans", "Medium", 30, C["gold"], a0 * 0.85, "cm", tracking=0.2)


@scene("gift", qy=1250)
def gift(ctx, t, S):
    dark_bg(ctx)
    a0 = fade(t, S.t0, None, 0.4)
    L_ = (300, 640); R_ = (800, 420)
    name_tile(ctx, R_[0], R_[1], "陶谦", "徐州牧 · 丹阳人", C["green"], a0, 70)
    name_tile(ctx, L_[0], L_[1], "刘备", "客将", C["red"], a0, 70)
    # 田楷：先连线，后断开
    T_ = (250, 360)
    name_tile(ctx, T_[0], T_[1], "田楷", "青州刺史", C["gray"], a0 * 0.9, 50)
    cut = prog(t, S.a("o07") + 1.0, 0.8)
    E.line(ctx, T_[0], T_[1] + 55, L_[0], L_[1] - 70, C["gray"], 3, a0 * (1 - 0.7 * cut), dash=[10, 8])
    if cut > 0:
        mx, my = (T_[0] + L_[0]) / 2, (T_[1] + 55 + L_[1] - 70) / 2
        s = 26 * ease_out(cut)
        E.line(ctx, mx - s, my - s, mx + s, my + s, C["red2"], 6, 1)
        E.line(ctx, mx - s, my + s, mx + s, my - s, C["red2"], 6, 1)
    # 四千丹阳兵：绿点流向刘备，到达后变红
    fl = prog(t, S.t0 + 0.6, 4.5)
    tr = troop("gift_flow", 800, (60, 30), 31, C["green"], None, 4.0)
    rng = np.random.default_rng(5)
    if not hasattr(gift, "lag"):
        gift.lag = rng.random(800)
        gift.off = rng.normal(0, 1, (800, 2)) * np.array([38, 38])
    u = np.clip(fl * 1.6 - gift.lag * 0.6, 0, 1)
    us = u * u * (3 - 2 * u)
    sx, sy, ex, ey = R_[0], R_[1] + 90, L_[0] + 30, L_[1] + 140
    cxp, cyp = (sx + ex) / 2 + 80, max(sy, ey) + 260
    bx = (1 - us) ** 2 * sx + 2 * (1 - us) * us * cxp + us ** 2 * ex + gift.off[:, 0] * (0.3 + 0.7 * us)
    by = (1 - us) ** 2 * sy + 2 * (1 - us) * us * cyp + us ** 2 * ey + gift.off[:, 1] * (0.3 + 0.7 * us)
    for sel, col in ((us < 0.98, C["green"]), (us >= 0.98, C["red2"])):
        idx = np.where(sel & (fl > 0))[0]
        E.set_col(ctx, col, 0.95)
        for i in idx:
            ctx.rectangle(bx[i] - 2.2, by[i] - 2.2, 4.4, 4.4)
        ctx.fill()
    n = int(4000 * clamp(fl * 1.15))
    E.draw_text(ctx, f"+{n:,}".replace(",", ""), W / 2 + 40, 980, "serif", "Black", 120, C["green2"], a0 * clamp(fl * 4), "cm", shadow=8)
    E.draw_text(ctx, "丹阳兵", W / 2 + 40, 1075, "serif", "Bold", 44, "#e4f1df", a0 * clamp(fl * 4), "cm")
    # “好几倍”：对比条
    pb = prog(t, S.a("o08"), 1.2)
    if pb > 0:
        y = 1180
        E.draw_text(ctx, "自有兵", 120, y, "sans", "Medium", 30, "#e8dcc0", pb, "lm")
        E.rect(ctx, 260, y - 16, 120 * ease_out(pb), 32, C["red"], pb)
        E.draw_text(ctx, "陶谦给的", 120, y + 60, "sans", "Medium", 30, "#e8dcc0", pb, "lm")
        E.rect(ctx, 260, y + 44, 520 * ease_out(pb), 32, C["green"], pb)
    if prog(t, S.a("o08") + 2.0, 0.5) > 0 and S.a("o07") < t:
        pass


@scene("beaten", qy=1250)
def beaten(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(118.4, 34.7, 700), CAM_TAN, ease_io(prog(lt, 0, 5)))
    G.base(ctx, cam, dim=0.85, prov_labels=False)
    tan = cam.p("郯")
    fortress(ctx, tan[0], tan[1], 46)
    E.draw_text(ctx, "郯", tan[0] - 70, tan[1], "serif", "Black", 48, "#f4ead4", 1, "rm", shadow=6)
    ex, ey = tan[0] + 230, tan[1] + 20
    hit = prog(lt, 1.6, 1.0)
    rout = ease_out(prog(lt, 2.3, 2.6))
    troop("bt_liu", 180, (60, 40), 41, C["red2"], None, 5).draw(ctx, ex + 20, ey + 40, t, 1, rout=rout, rout_dir=(0.6, 0.8))
    troop("bt_cb", 220, (70, 45), 42, C["green"], None, 5).draw(ctx, ex + 40, ey - 70, t, 1, rout=rout, rout_dir=(0.9, -0.3))
    Wd.thick_arrow(ctx, [(tan[0] - 300, tan[1] - 520), (tan[0] - 40, tan[1] - 240), (ex - 40, ey - 30)],
                   ease_out(prog(lt, 0.3, 1.6)), 80, 120, **Wd.arrow_style("cao"))
    if hit > 0:
        Wd.smoke(ctx, ex, ey, 60, t, hit, seed=3)
        Wd.fire(ctx, ex - 30, ey, 18, t, (1 - rout) * hit, seed=4)
    a = fade(lt, 2.2, None, 0.3)
    big_text(ctx, "击破", min(ex + 40, W - 200), ey + 260, 110, C["gold2"], a, scale=lerp(1.4, 1.0, ease_out(prog(lt, 2.2, 0.4))))
    caption(ctx, "194年夏 · 郯城东", fade(lt, 0, None, 0.3))
    Wd.label_pill(ctx, "曹豹＋刘备", ex + 40, ey - 170, C["green"], fade(lt, 0.5, None, 0.4) * (1 - rout), 28)


@scene("deathbed", qy=1060)
def deathbed(ctx, t, S):
    dark_bg(ctx, "#0b0908", "#15110d", 2)
    lt = t - S.t0
    # 帷帐与烛
    for k in range(7):
        x = 90 + k * 150
        E.line(ctx, x, 180, x + math.sin(t * 0.4 + k) * 6, 1500, "#3a2d22", 26, 0.25)
    Wd.fire(ctx, W / 2, 640, 26, t, 0.95, seed=9)
    E.rect(ctx, W / 2 - 16, 640, 32, 150, "#d8c8a6", 0.85)
    g = cairo.RadialGradient(W / 2, 620, 0, W / 2, 620, 700)
    g.add_color_stop_rgba(0, 1, 0.75, 0.4, 0.18); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    E.draw_text(ctx, "徐", 180, 420, "serif", "Black", 300, C["green"], 0.06, "cm")
    E.draw_text(ctx, "州", 900, 1350, "serif", "Black", 300, C["green"], 0.06, "cm")
    caption(ctx, "陶谦病笃 · 194年", fade(lt, 0, None, 0.4), y=330)


@scene("question", qy=1100)
def question(ctx, t, S):
    dark_bg(ctx)
    items = ["兵不多", "仗没打赢", "没有一寸地盘"]
    for i, it in enumerate(items):
        a = fade(t, S.a("o12") + 0.4 + i * 0.9, None, 0.3)
        y = 470 + i * 150
        E.draw_text(ctx, it, W / 2, y, "serif", "Black", 78, "#d9cdb4", a, "cm")
        st = prog(t, S.a("o12") + 0.8 + i * 0.9, 0.35)
        if st > 0:
            w = E.text_size(it, "serif", "Black", 78)[0]
            E.line(ctx, W / 2 - w / 2 - 20, y + 4, W / 2 - w / 2 - 20 + (w + 40) * st, y + 4, C["red"], 7, 0.9)
    q = prog(t, S.a("o13"), 0.6)
    big_text(ctx, "为什么是他？", W / 2, 1020, 130, C["red2"], ease_out(q), scale=lerp(1.25, 1, ease_out(q)))
    a2 = fade(t, S.a("o13") + 2.0, None, 0.4)
    E.draw_text(ctx, "徐州豪族，凭什么点头？", W / 2, 1180, "serif", "Bold", 54, "#e8dcc0", a2, "cm")


@scene("title", qy=1100)
def title(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.9, 34.8, 250), G.Cam(117.9, 34.6, 270), prog(lt, 0, 8))
    G.base(ctx, cam, dim=0.55, prov_labels=False, borders=False)
    tint_poly(ctx, cam, "徐州", C["red"], 0.22 * fade(lt, 0.2, None, 1.0), C["red2"])
    E.set_col(ctx, "#000000", 0.35); ctx.rectangle(0, 0, W, H); ctx.fill()
    a = ease_out(prog(lt, 0.2, 0.9))
    big_text(ctx, "刘备入主徐州", W / 2, 700, 118, "#f6ecd6", a, scale=lerp(1.08, 1, a), tracking=0.12)
    E.line(ctx, W / 2 - 330 * a, 800, W / 2 + 330 * a, 800, C["gold"], 2, 0.8 * a)
    E.draw_text(ctx, "一个客将，怎样被请去当一州之主", W / 2, 870, "serif", "Bold", 50, C["gold2"], fade(lt, 0.7, None, 0.6), "cm")
    E.draw_seal(ctx, "刘备", W / 2 + 360, 540, 110, fade(lt, 1.2, None, 0.2), C["red"], -0.08,
                lerp(1.6, 1.0, ease_out(prog(lt, 1.2, 0.3))))


# ═════════════════════ 一 平原相 ═════════════════════
@scene("pingyuan", qy=1250)
def pingyuan(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.0, 36.2, 230), CAM_NORTH, ease_io(prog(lt, 0, 6)))
    G.base(ctx, cam, dim=0.9)
    px, py = cam.p("平原")
    Wd.glow_dot(ctx, px, py, 12, C["red"], fade(t, S.a("a02") + 2.5, None, 0.5), math.sin(t * 4))
    G.city(ctx, cam, "平原", fade(t, S.a("a02") + 2.5, None, 0.5), C["red2"], 42, side="r", modern=True)
    G.city(ctx, cam, "临淄", fade(lt, 0.8, None, 0.5), "#d6dce4", 34, label="临淄（田楷）", side="l")
    # 袁绍：冀州，土黄旗
    a_y = fade(t, S.a("a02") + 1.0, None, 0.6)
    yx, yy = cam(115.6, 37.6)
    flagsea("ys", 14, 260, 160, seed=8).draw(ctx, yx, yy, t, 30, a_y, C["yellow"], "#f5e3b5", "袁")
    Wd.label_pill(ctx, "袁绍", yx, yy + 130, C["yellow"], a_y, 32)
    # 公孙瓒阵营：从北方压下的冷蓝灰箭头
    Wd.thick_arrow(ctx, [cam(117.8, 39.6), cam(117.4, 38.4), cam(116.8, 37.5)], ease_out(prog(t, S.a("a02"), 2.0)),
                   40, 70, **Wd.arrow_style("tian"))
    Wd.label_pill(ctx, "公孙瓒阵营", *cam(118.4, 38.6), C["gray"], a_y, 30)
    ah = fade(t, S.a("a03"), None, 0.5)
    hx, hy = cam(116.0, 36.75)
    E.draw_text(ctx, "黄河（示意）", hx - 40, hy + 50, "sans", "Medium", 28, "#a9c4d8", ah, "cm", shadow=4)
    caption(ctx, "数年前 · 青州平原", fade(lt, 0, None, 0.4))


@scene("assassin", qy=1230)
def assassin(ctx, t, S):
    dark_bg(ctx, "#0a0b0d", "#13151a", 3)
    lt = t - S.t0
    # 月与窗
    E.circle(ctx, 820, 420, 70, "#e9e2c9", 0.85)
    E.set_col(ctx, "#2a2620", 0.9); ctx.set_line_width(10)
    ctx.rectangle(680, 280, 290, 290); ctx.stroke()
    E.line(ctx, 825, 280, 825, 570, "#2a2620", 8); E.line(ctx, 680, 425, 970, 425, "#2a2620", 8)
    # 案几与灯
    E.rect(ctx, 260, 980, 560, 26, "#3d2f22", 1)
    E.rect(ctx, 300, 1006, 20, 80, "#3d2f22", 1); E.rect(ctx, 760, 1006, 20, 80, "#3d2f22", 1)
    Wd.fire(ctx, 540, 960, 14, t, 0.9, seed=2)
    g = cairo.RadialGradient(540, 940, 0, 540, 940, 520)
    g.add_color_stop_rgba(0, 1, 0.7, 0.35, 0.2); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    # 主人（刘备，朱红镶边）与刺客
    figure(ctx, 330, 1000, 300, "#251c17", 1, seated=True)
    figure(ctx, 330, 1000, 300, C["red"], 0.25, seated=True)
    drop = ease_in(prog(t, S.a("a06") + 1.5, 1.2))
    figure(ctx, 760, 1000, 330, "#0f0e0d", 1)
    # 匕首
    ang = lerp(-0.9, 1.3, drop)
    dx, dy = 850 + 0 * drop, 760 + 220 * drop
    ctx.save(); ctx.translate(dx, dy); ctx.rotate(ang)
    E.set_col(ctx, "#cfd6dc", 0.9); ctx.move_to(0, -6); ctx.line_to(90, 0); ctx.line_to(0, 6); ctx.close_path(); ctx.fill()
    E.rect(ctx, -26, -5, 26, 10, "#5a4630", 1)
    ctx.restore()
    E.draw_text(ctx, "刘备", 330, 1110, "serif", "Bold", 40, C["red2"], fade(lt, 0.5, None, 0.4), "cm")
    E.draw_text(ctx, "刺客", 760, 1110, "serif", "Bold", 40, "#c9c2b4", fade(lt, 0.5, None, 0.4), "cm")
    Wd.badge(ctx, "情景演绎", W - 40, 240, 1)
    a = fade(t, S.a("a06") + 3.0, None, 0.4)
    E.draw_text(ctx, "待客甚厚", W / 2, 1180, "serif", "Black", 64, C["gold2"], a, "cm", tracking=0.2)


@scene("famine", qy=1240)
def famine(ctx, t, S):
    dark_bg(ctx, "#100d0a", "#1c1712", 4)
    lt = t - S.t0
    cx, cy = W / 2, 760
    n = 1400
    if not hasattr(famine, "p0"):
        rng = np.random.default_rng(11)
        ang = rng.random(n) * 6.283; r = 380 + rng.random(n) * 420
        famine.p0 = np.stack([np.cos(ang) * r, np.sin(ang) * r * 0.9], 1)
        famine.lag = rng.random(n); famine.ph = rng.random(n) * 6.28
    cu = np.clip(prog(t, S.a("a07") + 1.0, 9) * 1.3 - famine.lag * 0.3, 0, 1)
    conv = cu * cu * (3 - 2 * cu)
    rr = lerp(1.0, 0.16, conv)
    p = famine.p0 * rr[:, None] + np.stack([np.sin(t * 0.8 + famine.ph), np.cos(t * 0.7 + famine.ph)], 1) * 8
    E.set_col(ctx, "#b5aa94", 0.75)
    for i in range(n):
        ctx.rectangle(cx + p[i, 0] - 2, cy + p[i, 1] - 2, 4, 4)
    ctx.fill()
    Wd.glow_dot(ctx, cx, cy, 26, C["red"], 1, math.sin(t * 3))
    E.draw_text(ctx, "平原", cx, cy + 70, "serif", "Black", 44, "#f4ead4", 1, "cm", shadow=5)
    caption(ctx, "人民饥馑，屯聚钞暴", fade(lt, 0.3, S.a("a09b") - 0.4, 0.4))
    # 三条兵源
    pb = prog(t, S.a("a09b"), 0.5)
    if pb > 0:
        E.set_col(ctx, "#000000", 0.55 * pb); ctx.rectangle(0, 0, W, H); ctx.fill()
        src = [("朝廷给的", 220), ("豪族带的", 540), ("流民投的", 860)]
        for i, (lab, x) in enumerate(src):
            a = fade(t, S.a("a09b") + 0.6 + i * 0.7, None, 0.3)
            col = C["red2"] if i == 2 else "#8a8274"
            Wd.panel(ctx, x - 140, 380, 280, 120, a, col)
            E.draw_text(ctx, lab, x, 440, "serif", "Black", 46, "#f2e6cc" if i == 2 else "#9d9483", a, "cm")
            E.line(ctx, x, 510, x, 650, col, 4, a * 0.8, dash=None if i == 2 else [8, 8])
        for i in range(2):
            c = prog(t, S.a("a09c") + 0.3 + i * 0.4, 0.3)
            x = src[i][1]
            if c > 0:
                E.line(ctx, x - 100, 400, x - 100 + 200 * c, 480, C["red"], 7, 0.9)
        E.draw_text(ctx, "刘备", 860, 700, "serif", "Black", 56, C["red2"], fade(t, S.a("a09c"), None, 0.3), "cm")


@scene("analogy1", qy=900)
def analogy1(ctx, t, S):
    dark_bg(ctx, "#0b0d10", "#141820", 5)
    a = fade(t, S.a("a12"), None, 0.4)
    big_text(ctx, "人心", 300, 1370, 96, "#f2e6cc", a)
    E.draw_text(ctx, "→", W / 2, 1370, "serif", "Black", 96, C["gold"], a, "cm")
    big_text(ctx, "兵力", 780, 1370, 96, C["red2"], a)


# ═════════════════════ 二 救徐州 ═════════════════════
def factions(ctx, cam, a, t, cao=True, tao=True, tian=True, yuan=True):
    if cao:
        x, y = cam(116.0, 35.6)
        flagsea("f_cao", 12, 220, 140, seed=21).draw(ctx, x, y, t, 30, a, "#141312", C["gold"], "曹")
        Wd.label_pill(ctx, "曹操 · 兖州", x, y + 120, "#141312", a, 30, C["gold2"])
    if tao:
        x, y = cam(118.6, 34.4)
        Wd.label_pill(ctx, "陶谦 · 徐州", x + 40, y, C["green"], a, 30)
    if tian:
        x, y = cam(118.4, 36.95)
        Wd.label_pill(ctx, "田楷 · 青州", x + 80, y - 30, C["gray"], a, 30)
    if yuan:
        x, y = cam(115.2, 37.4)
        Wd.label_pill(ctx, "袁绍 · 冀州", x, y, C["yellow"], a, 30)


@scene("bigmap", qy=1250)
def bigmap(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.2, 35.2, 170), CAM_MACRO, ease_io(prog(lt, 0, 5)))
    G.base(ctx, cam, dim=0.9, hi_prov={"徐州", "兖州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.16 * fade(lt, 0.3, None, 0.8))
    tint_poly(ctx, cam, "兖州", "#000000", 0.30 * fade(lt, 0.3, None, 0.8), C["gold"])
    factions(ctx, cam, fade(lt, 0.6, None, 0.5), t)
    pa = prog(t, S.a("b02"), 0.6)
    x, y = G.city(ctx, cam, "琅邪", ease_out(pa), "#f4ead4", 36, side="r")
    if pa > 0:
        s = 28 * ease_out(pa)
        E.line(ctx, x - s, y - s, x + s, y + s, C["red2"], 6, pa)
        E.line(ctx, x - s, y + s, x + s, y - s, C["red2"], 6, pa)
        Wd.label_pill(ctx, "曹嵩遇害", x, y - 70, "#2a1410", pa, 28, "#f4c9b8")
    caption(ctx, "193年 · 东征缘起", fade(lt, 0, None, 0.4))


@scene("invade1", qy=1250)
def invade1(ctx, t, S):
    lt = t - S.t0
    cam = CAM_MACRO
    G.base(ctx, cam, dim=0.9, hi_prov={"徐州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.14)
    factions(ctx, cam, 1, t, tian=False, yuan=False)
    path = [cam(115.6, 35.5), cam(116.6, 35.0), cam(117.4, 34.55), cam(118.1, 34.65)]
    f = ease_io(prog(lt, 0.2, 4.5))
    Wd.thick_arrow(ctx, path, f, 90, 140, **Wd.arrow_style("cao"))
    cities = [(116.9, 35.1), (117.1, 34.75), (117.3, 34.45), (117.6, 34.7), (117.5, 34.25), (117.85, 34.5),
              (117.9, 34.9), (117.7, 35.05), (118.0, 34.35), (118.1, 34.8), (117.35, 34.95)]
    for k, (lo, la) in enumerate(cities):
        tk = 0.6 + k * 0.32
        x, y = cam(lo, la)
        on = prog(lt, tk, 0.3)
        fortress(ctx, x, y, 18, "#d8c8a6" if on <= 0 else "#3a3632", 1)
        if on > 0:
            Wd.fire(ctx, x, y - 8, 12, t, on * (1 - 0.5 * prog(lt, tk + 2, 2)), seed=k)
            Wd.smoke(ctx, x, y - 20, 22, t, on, seed=k + 9)
    n = min(10, int(max(0, lt - 0.6) / 0.32))
    E.draw_text(ctx, f"下{['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][n] if n <= 10 else '十'}城" if n < 10 else "下十余城",
                W / 2, 1300, "serif", "Black", 92, C["gold2"], fade(lt, 0.6, None, 0.3), "cm")
    tx, ty = cam.p("郯")
    fortress(ctx, tx, ty, 34, C["green2"])
    E.draw_text(ctx, "陶谦守城不敢出", tx + 10, ty + 70, "serif", "Bold", 34, C["green2"], fade(lt, 3.0, None, 0.4), "ct", shadow=5)
    caption(ctx, "193年秋 · 曹操第一次东征", fade(lt, 0, None, 0.3))


@scene("rescue", qy=1250)
def rescue(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(CAM_MACRO, G.Cam(117.6, 35.6, 210), ease_io(prog(lt, 0, 3)))
    G.base(ctx, cam, dim=0.9, hi_prov={"徐州", "青州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.14)
    G.city(ctx, cam, "临淄", 1, "#d6dce4", 34, label="齐（临淄）")
    tx, ty = cam.p("郯")
    fortress(ctx, tx, ty, 34, C["green2"])
    p1 = [cam(118.2, 36.75), cam(118.5, 35.9), cam(118.45, 35.1), cam(118.38, 34.75)]
    p0 = [cam(118.0, 36.75), cam(118.2, 35.9), cam(118.2, 35.1), cam(118.25, 34.75)]
    Wd.thick_arrow(ctx, p0, ease_out(prog(lt, 0.4, 3.5)), 18, 34, **Wd.arrow_style("tian"))
    f = ease_out(prog(lt, 0.8, 3.6))
    Wd.thick_arrow(ctx, p1, f, 14, 30, **Wd.arrow_style("liu"))
    x, y, ang = E.point_along(E.smooth_path(p1, 10), max(0.02, f * 0.9))
    troop("rs_liu", 140, (26, 40), 51, C["red2"], None, 4.5).draw(ctx, x, y, t, 1, ang=ang - math.pi / 2, march=1)
    Wd.label_pill(ctx, "田楷", p0[1][0] - 80, p0[1][1], C["gray"], fade(lt, 0.8, None, 0.3), 28)
    Wd.label_pill(ctx, "刘备", p1[1][0] + 80, p1[1][1], C["red"], fade(lt, 1.2, None, 0.3), 28, "#fff2ee")
    caption(ctx, "田楷、刘备东援", fade(lt, 0, None, 0.3))


@scene("xiaopei", qy=1250)
def xiaopei(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.6, 35.0, 260), CAM_CLOSE, ease_io(prog(lt, 0, 3.5)))
    G.base(ctx, cam, dim=0.9, prov_labels=False)
    tint_poly(ctx, cam, "徐州", C["green"], 0.12)
    for nm in ("郯", "下邳", "彭城"):
        G.city(ctx, cam, nm, 1, "#e8dcc0", 34)
    x, y = cam.p("小沛")
    a = fade(lt, 1.5, None, 0.5)
    tr = troop("xp_red", 260, (55, 45), 61, C["red2"], None, 4.5)
    tr.draw(ctx, x + 10, y + 70, t, a)
    tg = troop("xp_green", 500, (70, 55), 62, C["green"], None, 4.2)
    ag = prog(lt, 2.5, 3.0)
    tg.draw(ctx, lerp(cam.p("郯")[0], x + 20, ease_io(ag)), lerp(cam.p("郯")[1], y + 70, ease_io(ag)), t, a if ag < 1 else a * 0.0)
    if ag >= 1:
        troop("xp_merge", 700, (80, 60), 63, C["red2"], None, 4.3).draw(ctx, x + 10, y + 70, t, a)
    Wd.glow_dot(ctx, x, y, 14, C["red"], a, math.sin(t * 4))
    G.city(ctx, cam, "小沛", a, C["red2"], 44, side="l", modern=True)
    Wd.label_pill(ctx, "豫州刺史 · 屯小沛", x + 40, y - 120, C["red"], fade(lt, 3.0, None, 0.4), 32, "#fff2ee")


@scene("supply", qy=880)
def supply(ctx, t, S):
    lt = t - S.t0
    cam = CAM_MACRO
    G.base(ctx, cam, dim=0.8, prov_labels=False)
    a = fade(lt, 0.2, None, 0.4)
    path = [cam.p("鄄城"), cam(116.6, 35.1), cam(117.4, 34.75), cam(118.0, 34.7)]
    P = E.smooth_path(path, 10)
    E.polyline(ctx, P, C["gold"], 5, a * 0.8)
    # 粮车
    for k in range(9):
        u = ((lt * 0.07 + k / 9) % 1.0)
        x, y, ang = E.point_along(P, u)
        ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
        E.rect(ctx, -14, -9, 28, 18, "#c8a46a", a); E.circle(ctx, -8, 11, 5, "#2a2018", a); E.circle(ctx, 8, 11, 5, "#2a2018", a)
        ctx.restore()
    G.city(ctx, cam, "鄄城", a, "#e8dcc0", 32, label="兖州后方")
    E.draw_text(ctx, "数百里粮道", cam(116.9, 35.25)[0], cam(116.9, 35.25)[1] - 40, "serif", "Bold", 40, C["gold2"], a, "cm", shadow=5)
    # 退兵
    r = ease_io(prog(t, S.a("b06c"), 3.0))
    Wd.thick_arrow(ctx, [cam(118.0, 34.5), cam(117.2, 34.6), cam(116.3, 35.2)], r, 60, 100, **Wd.arrow_style("cao"))
    E.draw_text(ctx, "退兵", cam(117.1, 34.3)[0], cam(117.1, 34.3)[1] + 40, "serif", "Black", 64, "#f3e7cc", r, "cm", shadow=6)
    caption(ctx, "194年春 · 曹军粮尽", fade(lt, 0, None, 0.3))


@scene("gate", qy=1250)
def gate(ctx, t, S):
    lt = t - S.t0
    hi = {"泗水", "沂水"} if t > S.a("b08b") else None
    cam = G.Cam.blend(CAM_CLOSE, G.Cam(117.15, 34.75, 520), ease_io(prog(t, S.a("b08"), 3)))
    G.base(ctx, cam, dim=0.92, hi_rivers=hi, hi_prov={"徐州", "兖州", "豫州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.13)
    tint_poly(ctx, cam, "兖州", "#000000", 0.22, C["gold"])
    for nm in ("郯", "下邳", "彭城"):
        G.city(ctx, cam, nm, 1, "#e8dcc0", 34)
    x, y = cam.p("小沛")
    troop("xp_merge", 700, (80, 60), 63, C["red2"], None, 4.3).draw(ctx, x + 10, y + 70, t, 1)
    fortress(ctx, x, y, 40, C["red2"])
    G.city(ctx, cam, "小沛", 1, C["red2"], 44, side="l")
    pa = prog(t, S.a("b08"), 0.6)
    Wd.label_pill(ctx, "豫州 · 沛国", x - 60, y + 190, C["gray"], pa, 28)
    # 曹军从西来，撞在小沛
    for k, dy in enumerate((-160, 0, 160)):
        Wd.thick_arrow(ctx, [(x - 560, y + dy - 60), (x - 300, y + dy * 0.6), (x - 70, y + dy * 0.2)],
                       ease_out(prog(t, S.a("b08") + 1.5 + k * 0.3, 1.4)), 30, 56, **Wd.arrow_style("cao"))
    if hi:
        ph = fade(t, S.a("b08b"), None, 0.5)
        sx, sy = cam(116.75, 35.3)
        Wd.label_pill(ctx, "泗水", sx - 40, sy, "#4f7896", ph, 32, "#eef6fc")
        ox, oy = cam(118.42, 35.3)
        Wd.label_pill(ctx, "沂水", ox + 40, oy, "#4f7896", ph, 32, "#eef6fc")
        # 水道上的舟点
        P = E.smooth_path([cam(*p) for p in G.SI], 8)
        for k in range(7):
            u = (t * 0.05 + k / 7) % 1
            bx, by, _ = E.point_along(P, u)
            E.circle(ctx, bx, by, 6, "#e6c886", ph)
        E.draw_text(ctx, "运粮道 ＝ 进兵道", W / 2, 1360, "serif", "Black", 64, "#cfe3f2", ph, "cm", shadow=6)
    pg = prog(t, S.a("b09"), 0.4)
    if pg > 0:
        E.draw_seal(ctx, "看门", x + 170, y - 140, 130, pg, C["red"], -0.1, lerp(1.6, 1, ease_out(pg)))
    caption(ctx, "徐州的西门", fade(t, S.a("b07"), None, 0.3))


@scene("invade2", qy=1250)
def invade2(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(CAM_MACRO, G.Cam(117.7, 35.0, 250), ease_io(prog(lt, 0, 4)))
    G.base(ctx, cam, dim=0.86, hi_prov={"徐州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.12)
    paths = [[cam(115.8, 35.6), cam(117.0, 35.4), cam(118.2, 35.15), cam(118.9, 34.95)],
             [cam(115.9, 35.2), cam(117.1, 34.9), cam(118.2, 34.75), cam(118.9, 34.6)]]
    for k, p in enumerate(paths):
        Wd.thick_arrow(ctx, p, ease_io(prog(lt, 0.2 + k * 0.5, 4.0)), 70, 110, **Wd.arrow_style("cao"))
    for k in range(10):
        u = 0.25 + k * 0.07
        p = E.smooth_path(paths[k % 2], 10)
        x, y, _ = E.point_along(p, u)
        on = prog(lt, 0.8 + k * 0.35, 0.4)
        Wd.fire(ctx, x + (k % 3 - 1) * 30, y + 40, 15, t, on, seed=k)
        Wd.smoke(ctx, x, y + 20, 34, t, on, seed=k + 20)
    G.city(ctx, cam, "琅邪", 1, "#e8dcc0", 32)
    Wd.label_pill(ctx, "东海", *cam(119.1, 34.85), "#2b2a28", fade(lt, 3, None, 0.4), 30, "#f3e7cc")
    caption(ctx, "194年夏 · 第二次东征", fade(lt, 0, None, 0.3))


@scene("tandong", qy=1300)
def tandong(ctx, t, S):
    lt = t - S.t0
    cam = CAM_TAN
    G.base(ctx, cam, dim=0.85, prov_labels=False)
    tan = cam.p("郯")
    fortress(ctx, tan[0], tan[1], 50)
    E.draw_text(ctx, "郯", tan[0] - 80, tan[1], "serif", "Black", 52, "#f4ead4", 1, "rm", shadow=6)
    ex, ey = tan[0] + 250, tan[1] - 40
    clash = prog(t, S.a("b13"), 1.0)
    rout = ease_out(prog(t, S.a("b13") + 1.3, 3.0))
    troop("td_cb", 420, (80, 60), 71, C["green"], None, 4.6).draw(ctx, ex + 30, ey - 70, t, 1, rout=rout, rout_dir=(0.8, -0.4))
    troop("td_liu", 360, (70, 55), 72, C["red2"], None, 4.6).draw(ctx, ex + 50, ey + 80, t, 1, rout=rout, rout_dir=(0.7, 0.7))
    # 曹军：从西北横扫
    fx = lerp(tan[0] - 620, ex - 120, ease_io(prog(lt, 0.5, max(1.0, S.a("b13") + 1.0 - S.t0 - 0.5))))
    troop("td_cao", 1300, (200, 260), 73, "#151413", C["gold"], 4.4).draw(ctx, fx, ey - 20, t, 1, march=1)
    flagsea("td", 16, 260, 360, seed=31).draw(ctx, fx - 40, ey - 10, t, 28, 1, char="曹")
    Wd.thick_arrow(ctx, [(fx - 120, ey - 360), (fx + 40, ey - 180), (ex - 10, ey - 20)], clash, 60, 100, **Wd.arrow_style("cao"))
    if clash > 0:
        for k in range(4):
            Wd.smoke(ctx, ex + k * 40 - 40, ey + 20, 50, t, clash, seed=k + 40)
    Wd.label_pill(ctx, "曹豹", ex + 120, ey - 190, C["green"], fade(lt, 0.4, None, 0.3) * (1 - rout), 28)
    Wd.label_pill(ctx, "刘备", ex + 150, ey + 190, C["red"], fade(lt, 0.4, None, 0.3) * (1 - rout), 28, "#fff2ee")
    # 陶谦欲走丹阳：向南的虚线
    pd = prog(t, S.a("b14b"), 1.5)
    if pd > 0:
        x0, y0 = tan[0], tan[1] + 60
        E.set_col(ctx, C["green2"], pd); ctx.set_dash([14, 10]); ctx.set_line_width(5)
        ctx.move_to(x0, y0); ctx.line_to(x0 - 60 * pd, y0 + 600 * pd); ctx.stroke(); ctx.set_dash([])
        E.arrow_head(ctx, x0 - 60 * pd, y0 + 600 * pd, math.atan2(600, -60), 24, C["green2"], pd)
        E.draw_text(ctx, "丹阳 →", x0 - 90, y0 + 640 * pd, "serif", "Bold", 40, C["green2"], pd, "rm", shadow=5)
    caption(ctx, "郯东之战", fade(lt, 0, None, 0.3))


@scene("lubu", qy=880)
def lubu(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(G.Cam(117.6, 35.0, 230), CAM_MACRO, ease_io(prog(lt, 0, 3)))
    G.base(ctx, cam, dim=0.88, hi_prov={"兖州", "徐州"})
    tint_poly(ctx, cam, "徐州", C["green"], 0.12)
    pb = prog(t, S.a("b16"), 2.5)
    tint_poly(ctx, cam, "兖州", "#000000", 0.25 * (1 - pb), C["gold"])
    tint_poly(ctx, cam, "兖州", C["blue"], 0.30 * ease_out(pb), C["blue2"])
    # 吕布蓝箭头：从陈留插入兖州
    Wd.thick_arrow(ctx, [cam(114.0, 34.5), cam.p("陈留"), cam(115.2, 35.0), cam(115.9, 35.45)], ease_out(pb), 50, 96,
                   **Wd.arrow_style("lv"))
    G.city(ctx, cam, "陈留", fade(t, S.a("b16"), None, 0.3), C["blue2"], 32, side="l", label="陈留（张邈）")
    Wd.label_pill(ctx, "吕布", *cam(115.2, 34.75), C["blue"], fade(t, S.a("b16") + 0.8, None, 0.3), 32)
    # 三城
    pc = prog(t, S.a("b16b"), 0.6)
    for nm in ("鄄城", "范", "东阿"):
        G.city(ctx, cam, nm, ease_out(pc), C["gold2"], 32, ring=C["gold"], side="r")
    # 曹军掉头
    pr = ease_io(prog(t, S.a("b17"), 3.0))
    Wd.thick_arrow(ctx, [cam(118.3, 34.7), cam(117.5, 34.45), cam(116.8, 34.75), cam(116.2, 35.3)], pr, 70, 110,
                   **Wd.arrow_style("cao"))
    if pr > 0:
        E.draw_text(ctx, "回师", cam(117.4, 34.2)[0], cam(117.4, 34.2)[1] + 30, "serif", "Black", 66, "#f3e7cc", pr, "cm", shadow=6)
    # 为什么非回不可
    pm = prog(t, S.a("b17b"), 0.5)
    if pm > 0:
        E.set_col(ctx, "#000000", 0.45 * pm); ctx.rectangle(0, 0, W, H); ctx.fill()
        items = ["粮草从兖州来", "家小在兖州", "后方一丢：补给先断，军心先散"]
        for i, it in enumerate(items):
            a = fade(t, S.a("b17b") + 0.3 + i * 1.6, None, 0.3)
            Wd.panel(ctx, 120, 560 + i * 130, 840, 100, a, C["blue2"] if i < 2 else C["red2"])
            E.draw_text(ctx, it, W / 2, 610 + i * 130, "serif", "Bold", 44, "#f2e9d8", a, "cm")
    caption(ctx, "194年 · 曹操后院起火", fade(lt, 0, None, 0.3))


@scene("lubu2", qy=1100)
def lubu2(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam.blend(CAM_MACRO, G.Cam(117.6, 34.7, 330), ease_io(prog(lt, 0, 3)))
    G.base(ctx, cam, dim=0.8, prov_labels=False)
    tint_poly(ctx, cam, "徐州", C["green"], 0.14)
    x, y = cam.p("小沛")
    Wd.glow_dot(ctx, x, y, 16, C["red"], 1, math.sin(t * 4))
    G.city(ctx, cam, "小沛", 1, C["red2"], 40, side="l")
    a = fade(lt, 2.5, None, 0.4)
    E.draw_text(ctx, "没打赢一场大仗", W / 2, 1240, "serif", "Bold", 52, "#cfc3aa", fade(lt, 0.8, None, 0.4), "cm")
    big_text(ctx, "却拿到了救援者的名分", W / 2, 1340, 66, C["red2"], a)


@scene("q3", qy=1100)
def q3(ctx, t, S):
    dark_bg(ctx, "#0f0c0a", "#1c1610", 6)
    a0 = fade(t, S.t0, None, 0.4)
    Wd.panel(ctx, 70, 300, 940, 1040, a0, C["gold"], fa=0.6)
    E.draw_text(ctx, "起家三问", W / 2, 370, "serif", "Black", 66, C["gold2"], a0, "cm", tracking=0.3)
    E.draw_text(ctx, "刘备 · 194年", W / 2, 440, "sans", "Medium", 28, "#bfb39b", a0, "cm")
    rows = [("b20", "手里有什么", ["自有兵千余 · 乌丸杂胡骑", "饥民数千 · 丹阳兵四千"]),
            ("b21", "借了谁的势", ["陶谦的求援", "曹操后院起火"]),
            ("b22", "做对了哪一步", ["去楷归谦", "从偏师，变成屏障"])]
    for i, (lid, q, ans) in enumerate(rows):
        a = fade(t, S.a(lid), None, 0.4)
        y = 520 + i * 260
        E.draw_text(ctx, f"{'一二三'[i]}", 130, y + 30, "serif", "Black", 64, C["red2"], a, "cm")
        E.draw_text(ctx, q, 190, y + 30, "serif", "Black", 50, "#f2e6cc", a, "lm")
        for j, an in enumerate(ans):
            E.draw_text(ctx, an, 190, y + 105 + j * 56, "sans", "Medium", 38, "#d8cdb6", a * fade(t, S.a(lid) + 0.8 + j * 0.8, None, 0.3), "lm")
        E.line(ctx, 120, y + 225, 960, y + 225, C["gold"], 1, 0.3 * a)
    # 偏师 → 屏障
    pb = prog(t, S.a("b23"), 0.5)
    if pb > 0:
        E.set_col(ctx, "#000000", 0.6 * pb); ctx.rectangle(0, 0, W, H); ctx.fill()
        Wd.panel(ctx, 80, 640, 420, 300, pb, C["gray"])
        E.draw_text(ctx, "田楷那里", 290, 700, "sans", "Medium", 34, "#c3c9d2", pb, "cm")
        E.draw_text(ctx, "偏师", 290, 800, "serif", "Black", 96, "#aeb6c2", pb, "cm")
        E.draw_text(ctx, "可有可无", 290, 890, "sans", "Regular", 32, "#9aa2ae", pb, "cm")
        pc = fade(t, S.a("b23") + 2.2, None, 0.4)
        Wd.panel(ctx, 580, 640, 420, 300, pc, C["red2"])
        E.draw_text(ctx, "陶谦这里", 790, 700, "sans", "Medium", 34, "#f2d6cf", pc, "cm")
        E.draw_text(ctx, "屏障", 790, 800, "serif", "Black", 96, C["red2"], pc, "cm")
        E.draw_text(ctx, "唯一挡在西门", 790, 890, "sans", "Regular", 32, "#f2d6cf", pc, "cm")
        E.draw_text(ctx, "→", W / 2 + 0, 800, "serif", "Black", 80, C["gold"], pc, "cm")
        pd = fade(t, S.a("b24"), None, 0.4)
        big_text(ctx, "被人依赖，才有分量", W / 2, 1120, 74, C["gold2"], pd)
