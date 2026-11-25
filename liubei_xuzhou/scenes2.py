# -*- coding: utf-8 -*-
"""场景（下半）：让州、失与得、演义对照、收束。"""
import math

import cairo
import numpy as np

import engine as E
import geomap as G
import widgets as Wd
from engine import W, H, C, clamp, prog, ease_out, ease_in, ease_io, smooth, lerp, fade
from scenes import (scene, caption, dark_bg, tint_poly, fortress, figure, name_tile, big_text, troop, flagsea,
                    CAM_MACRO, CAM_CLOSE, CAM_XU)


# ═════════════════════ 三 让州 ═════════════════════
@scene("sick", qy=1180)
def sick(ctx, t, S):
    dark_bg(ctx, "#0b0908", "#15110d", 2)
    lt = t - S.t0
    Wd.fire(ctx, 900, 560, 18, t, 0.9, seed=7)
    E.rect(ctx, 889, 560, 22, 100, "#d8c8a6", 0.8)
    g = cairo.RadialGradient(900, 540, 0, 900, 540, 650)
    g.add_color_stop_rgba(0, 1, 0.75, 0.4, 0.16); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    a0 = fade(lt, 0.2, None, 0.4)
    name_tile(ctx, 420, 430, "陶谦", "徐州牧 · 病笃", C["green"], a0, 70)
    pa = prog(t, S.a("c02"), 0.6)
    for i, (nm, x) in enumerate((("陶商", 260), ("陶应", 580))):
        a = ease_out(pa)
        E.line(ctx, 420, 520, x, 640, "#8a8274", 3, a * 0.7)
        name_tile(ctx, x, 700, nm, "不仕", "#6f685d", a * 0.8, 46)
    if pa > 0:
        E.draw_text(ctx, "裴注引《吴书》：二子皆不仕", 420, 820, "sans", "Regular", 28, "#a9c0d6", ease_out(pa), "cm")
    pq = prog(t, S.a("c03"), 0.5)
    name_tile(ctx, 820, 760, "麋竺", "别驾", "#c9b27a", ease_out(pq), 54)
    if pq > 0:
        E.line(ctx, 560, 470, 760, 700, C["gold"], 3, ease_out(pq) * 0.7, dash=[8, 8])
    caption(ctx, "州交给谁？", fade(t, S.a("c02") + 2.5, S.a("c03"), 0.4), y=960)


@scene("welcome", qy=1200)
def welcome(ctx, t, S):
    lt = t - S.t0
    cam = CAM_CLOSE
    G.base(ctx, cam, dim=0.8, prov_labels=False)
    tint_poly(ctx, cam, "徐州", C["green"], 0.12)
    tx, ty = cam.p("郯")
    xx, xy = cam.p("小沛")
    for nm in ("郯", "下邳", "彭城"):
        G.city(ctx, cam, nm, 1, "#e8dcc0", 34)
    fortress(ctx, xx, xy, 36, C["red2"])
    G.city(ctx, cam, "小沛", 1, C["red2"], 42, side="l")
    P = E.smooth_path([(tx, ty), cam(117.9, 34.5), cam(117.4, 34.55), (xx + 40, xy + 10)], 10)
    f = ease_io(prog(lt, 0.3, 5.0))
    E.polyline(ctx, P, "#e6c886", 4, 0.6, f)
    if not hasattr(welcome, "lag"):
        welcome.lag = np.random.default_rng(3).random(160)
    for i, lg in enumerate(welcome.lag):
        u = clamp(f * 1.15 - lg * 0.15)
        if u <= 0:
            continue
        x, y, _ = E.point_along(P, u)
        E.rect(ctx, x - 3 + (i % 5 - 2) * 6, y - 3 + (i % 3 - 1) * 6, 6, 6, "#e9d7a8" if i % 7 else "#ffcf7a", 0.9)
    Wd.label_pill(ctx, "麋竺率州人", (tx + xx) / 2 + 60, ty - 140, "#c9b27a", fade(lt, 0.8, None, 0.3), 30)
    pn = prog(t, S.a("c06") + 1.6, 0.4)
    if pn > 0:
        E.set_col(ctx, "#000000", 0.4 * pn); ctx.rectangle(0, 0, W, H); ctx.fill()
        big_text(ctx, "未敢当", W / 2, 900, 150, C["gold2"], pn, scale=lerp(1.4, 1, ease_out(pn)), tracking=0.3)
    caption(ctx, "陶谦死 · 迎刘备", fade(lt, 0, None, 0.3))


def hall(ctx, t, speaker, extra=None):
    """情景演绎：州府大堂。speaker ∈ {'chen','liu','kong',None}"""
    dark_bg(ctx, "#0d0a08", "#18130e", 7)
    # 地面透视线
    vx, vy = W / 2, 520
    for k in range(-8, 9):
        E.line(ctx, vx + k * 30, vy, vx + k * 260, H, "#3a2c20", 2, 0.5)
    for k in range(8):
        yy = vy + (k / 8) ** 1.8 * (H - vy)
        E.line(ctx, 0, yy, W, yy, "#3a2c20", 1.5, 0.35)
    # 柱
    for x, s in ((120, 1.0), (960, 1.0), (300, 0.65), (780, 0.65)):
        E.rect(ctx, x - 36 * s, 200, 72 * s, 1300 * s, "#4a1e16", 0.9)
        E.rect(ctx, x - 36 * s, 200, 10 * s, 1300 * s, "#7a3a2a", 0.5)
    E.rect(ctx, 0, 180, W, 40, "#2a1d14", 1)
    # 匾
    Wd.panel(ctx, W / 2 - 170, 250, 340, 90, 1, C["gold"], fill="#1c140d", fa=0.95)
    E.draw_text(ctx, "徐州府", W / 2, 296, "serif", "Black", 52, C["gold2"], 1, "cm", tracking=0.3)
    sp = {"chen": (230, 1060), "kong": (850, 1060), "mi": (390, 900), "liu": (W / 2, 760)}
    people = [("mi", "麋竺", "#b39a66"), ("chen", "陈登", "#9fa79a"), ("kong", "孔融", "#a69fb3"), ("liu", "刘备", C["red"])]
    for key, nm, col in people:
        x, y = sp[key]
        on = key == speaker
        rise = 1.0 if on else 0.82
        s = 330 if key != "liu" else 260
        figure(ctx, x, y, s, "#0e0b09", 1, rise=rise, seated=not on)
        figure(ctx, x, y, s, col, 0.55 if on else 0.18, rise=rise, seated=not on)
        if on:
            g = cairo.RadialGradient(x, y - s * 0.6, 0, x, y - s * 0.6, s * 1.1)
            c = E.hexrgb(col)
            g.add_color_stop_rgba(0, c[0], c[1], c[2], 0.25); g.add_color_stop_rgba(1, 0, 0, 0, 0)
            ctx.set_source(g); ctx.arc(x, y - s * 0.6, s * 1.1, 0, 6.283); ctx.fill()
        E.draw_text(ctx, nm, x, y + 40, "serif", "Bold", 40 if on else 32, "#f2e6cc" if on else "#8f8676", 1, "cm", shadow=5)
    Wd.badge(ctx, "情景演绎", W - 40, 240, 1)


@scene("hall_chen", qy=1330)
def hall_chen(ctx, t, S):
    hall(ctx, t, "chen")
    E.draw_text(ctx, "下邳陈登", W / 2, 420, "sans", "Medium", 32, "#c9bda4", fade(t, S.t0, None, 0.3), "cm")


@scene("hall_liu", qy=1330)
def hall_liu(ctx, t, S):
    hall(ctx, t, "liu")
    a = fade(t, S.a("c10") + 1.0, None, 0.4)
    name_tile(ctx, 830, 520, "袁术", "寿春 · 四世五公", C["yellow"], a, 56)


@scene("hall_chen2", qy=1330)
def hall_chen2(ctx, t, S):
    hall(ctx, t, "chen")
    p = prog(t, S.a("c12"), 0.6)
    if p > 0:
        big_text(ctx, "步骑十万", W / 2, 560, 110, C["gold2"], ease_out(p) * (1 - prog(t, S.a("c12b"), 0.3)))
    pz = prog(t, S.a("c12d"), 0.35)
    if pz > 0:
        E.set_col(ctx, "#000000", 0.5 * pz); ctx.rectangle(0, 0, W, H); ctx.fill()
        big_text(ctx, "逼", W / 2, 760, 320, C["red2"], pz, scale=lerp(1.6, 1, ease_out(pz)))


@scene("hall_kong", qy=1330)
def hall_kong(ctx, t, S):
    hall(ctx, t, "kong")
    E.draw_text(ctx, "北海相孔融 · 孔子二十世孙", W / 2, 420, "sans", "Medium", 30, "#c9bda4", fade(t, S.t0, None, 0.3), "cm")
    ps = prog(t, S.a("c15") + 2.4, 0.3)
    if ps > 0:
        E.set_col(ctx, "#000000", 0.4 * ps); ctx.rectangle(0, 0, W, H); ctx.fill()
        E.draw_seal(ctx, "领徐州", W / 2, 760, 260, ps, C["red"], -0.06, lerp(1.8, 1, ease_out(ps)))


@scene("who_ask", qy=1220)
def who_ask(ctx, t, S):
    dark_bg(ctx, "#0f0c0a", "#1b1611", 8)
    a1 = fade(t, S.a("c16") + 1.5, None, 0.4)
    Wd.panel(ctx, 80, 330, 440, 460, a1, "#c9b27a")
    E.draw_text(ctx, "麋竺", 300, 410, "serif", "Black", 72, "#f2e6cc", a1, "cm")
    E.draw_text(ctx, "东海朐县 · 豪商", 300, 480, "sans", "Medium", 30, "#d8c79a", a1, "cm")
    for k in range(5):  # 钱堆
        for j in range(4 - k // 2):
            E.circle(ctx, 200 + k * 50, 700 - j * 16, 22, "#c9a45c", a1 * 0.9)
            E.circle(ctx, 200 + k * 50, 700 - j * 16, 22, "#6b5222", a1, stroke=True, width=2)
    a2 = fade(t, S.a("c18") + 1.5, None, 0.4)
    Wd.panel(ctx, 560, 330, 440, 460, a2, "#9fa79a")
    E.draw_text(ctx, "陈登", 780, 410, "serif", "Black", 72, "#f2e6cc", a2, "cm")
    E.draw_text(ctx, "下邳 · 官宦大族", 780, 480, "sans", "Medium", 30, "#c7cec2", a2, "cm")
    E.draw_text(ctx, "父陈珪，沛相", 780, 560, "sans", "Regular", 30, "#c7cec2", a2, "cm")
    for k in range(3):
        E.rect(ctx, 700 + k * 60, 620, 40, 120, "#6c7468", a2 * 0.8)
    a3 = fade(t, S.a("c19"), None, 0.4)
    Wd.panel(ctx, 120, 850, 840, 150, a3, C["gold"])
    E.draw_text(ctx, "能打仗 ＋ 压不住他们", W / 2, 925, "serif", "Black", 64, C["gold2"], a3, "cm")


@scene("balance", qy=1250)
def balance(ctx, t, S):
    dark_bg(ctx, "#0e0c0a", "#1a1510", 9)
    lt = t - S.t0
    py = 980
    # 先放袁术，再换刘备
    tc = S.a("c22")
    yuan_in = ease_out(prog(t, S.a("c21"), 0.6)) * (1 - ease_in(prog(t, tc - 0.2, 0.5)))
    liu_in = ease_out(prog(t, tc + 0.2, 0.6))
    target = 0.0
    if yuan_in > 0:
        target = 0.33 * yuan_in
    ang = target * (1 - liu_in) + 0.0
    ang += math.sin(t * 1.3) * 0.01 * (1 - yuan_in)
    # 支点
    ctx.move_to(W / 2, py); ctx.line_to(W / 2 - 70, py + 260); ctx.line_to(W / 2 + 70, py + 260); ctx.close_path()
    E.set_col(ctx, "#6b5a40", 1); ctx.fill()
    L_ = 400
    lx, ly = W / 2 - math.cos(ang) * L_, py - math.sin(ang) * L_
    rx, ry = W / 2 + math.cos(ang) * L_, py + math.sin(ang) * L_
    E.line(ctx, lx, ly, rx, ry, "#c9a45c", 14, 1)
    E.circle(ctx, W / 2, py, 18, "#e6c886", 1)

    def pan(x, y, col, a=1.0):
        E.line(ctx, x - 90, y + 140, x, y, col, 3, a); E.line(ctx, x + 90, y + 140, x, y, col, 3, a)
        ctx.move_to(x - 120, y + 140); ctx.curve_to(x - 100, y + 190, x + 100, y + 190, x + 120, y + 140); ctx.close_path()
        E.set_col(ctx, col, a); ctx.fill()
    pan(lx, ly, "#9b8a6a"); pan(rx, ry, "#9b8a6a")
    # 左盘：本地精英
    for k, nm in enumerate(("麋", "陈", "豪族")):
        E.draw_text(ctx, nm, lx - 60 + k * 55, ly + 100, "serif", "Black", 44, "#e8dcc0", 1, "cm")
    E.draw_text(ctx, "徐州本地精英", lx, ly - 40, "sans", "Medium", 32, "#e8dcc0", fade(lt, 0.3, None, 0.4), "cm")
    # 右盘：候选
    if yuan_in > 0:
        sz = 210
        Wd.panel(ctx, rx - sz / 2, ry + 120 - sz, sz, sz, yuan_in, C["yellow"], fill="#3a2e14", fa=0.95)
        E.draw_text(ctx, "袁术", rx, ry + 120 - sz / 2 - 30, "serif", "Black", 60, "#f6e2b0", yuan_in, "cm")
        E.draw_text(ctx, "四世五公", rx, ry + 120 - sz / 2 + 40, "sans", "Bold", 30, "#f6e2b0", yuan_in, "cm")
        for i, tg in enumerate(("自带班底", "兵强马壮")):
            Wd.label_pill(ctx, tg, rx, ry - 200 - i * 64, C["yellow"], yuan_in * fade(t, S.a("c21") + 1.2 + i * 0.6, None, 0.3), 28)
        pa = fade(t, S.a("c21") + 3.0, None, 0.3) * yuan_in
        big_text(ctx, "附庸", lx, ly - 140, 80, C["yellow2"], pa)
    if liu_in > 0:
        sz = 160
        Wd.panel(ctx, rx - sz / 2, ry + 120 - sz, sz, sz, liu_in, C["red2"], fill="#3a1410", fa=0.95)
        E.draw_text(ctx, "刘备", rx, ry + 120 - sz / 2 - 18, "serif", "Black", 52, "#ffe2da", liu_in, "cm")
        tags = ("会打仗", "有名声", "在徐州没有根", "兵、钱粮靠本地")
        for i, tg in enumerate(tags):
            Wd.label_pill(ctx, tg, rx - 40 if i % 2 else rx + 10, ry - 120 - i * 62, C["red"], liu_in * fade(t, tc + 0.8 + i * 0.7, None, 0.3), 26, "#fff2ee")
    pz = prog(t, S.a("c23"), 0.5)
    if pz > 0:
        big_text(ctx, "最优弱主", W / 2, 1430, 110, C["gold2"], ease_out(pz), scale=lerp(1.3, 1, ease_out(pz)), tracking=0.2)
    caption(ctx, "本地精英的天平", fade(lt, 0, None, 0.3))


@scene("decline", qy=1250)
def decline(ctx, t, S):
    dark_bg(ctx, "#0f0c0a", "#1b1611", 10)
    steps = [("一推", "刘备：未敢当", "推举者：公开出面相迎"),
             ("二推", "刘备：让给袁术", "推举者：当众否定袁术"),
             ("三推", "刘备：仍不应", "推举者：许下步骑十万")]
    base_t = S.a("c25")
    for i, (no, a_, b_) in enumerate(steps):
        a = fade(t, base_t + 1.0 + i * 2.0, None, 0.35)
        y = 360 + i * 240
        Wd.panel(ctx, 80, y, 920, 200, a, C["gold"] if i < 2 else C["red2"])
        E.draw_text(ctx, no, 160, y + 100, "serif", "Black", 64, C["gold2"], a, "cm")
        E.draw_text(ctx, a_, 260, y + 65, "sans", "Medium", 36, "#d8cdb6", a, "lm")
        E.draw_text(ctx, b_, 260, y + 135, "serif", "Bold", 40, "#f6e9d0", a, "lm")
    pr = prog(t, S.a("c26"), 0.5)
    if pr > 0:
        cx, cy = W / 2, 1150
        n = 18
        for k in range(n):
            ang = math.pi * (0.1 + 0.8 * k / (n - 1))
            x, y = cx + math.cos(ang) * 380, cy + 150 - math.sin(ang) * 140
            a = fade(t, S.a("c26") + 0.5 + k * 0.08, None, 0.25)
            figure(ctx, x, y + 60, 70, "#c9b27a", a)
            E.line(ctx, x, y - 10, cx, cy, C["gold"], 2, a * 0.5)
        E.circle(ctx, cx, cy, 60, C["red"], ease_out(pr))
        E.draw_text(ctx, "州", cx, cy, "serif", "Black", 66, "#fff2ee", ease_out(pr), "cm")
        E.draw_text(ctx, "责任，分摊给每一个劝进者", W / 2, 1400, "serif", "Bold", 44, C["gold2"],
                    fade(t, S.a("c26") + 3.0, None, 0.4), "cm")
    caption(ctx, "推辞，是一个合法性动作", fade(t, S.t0, None, 0.3), y=260)


@scene("yuanshao", qy=1300)
def yuanshao(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam(115.9, 35.4, 190)
    G.base(ctx, cam, dim=0.75)
    G.city(ctx, cam, "下邳", 1, C["red2"], 36)
    G.city(ctx, cam, "邺", 1, C["yellow2"], 40, label="邺（袁绍）", side="l")
    P = E.smooth_path([cam.p("下邳"), cam(116.5, 35.2), cam(115.2, 35.9), cam.p("邺")], 10)
    f = ease_io(prog(lt, 0.5, 3.5))
    ctx.set_dash([12, 9]); E.polyline(ctx, P, C["gold2"], 4, 0.9, f); ctx.set_dash([])
    x, y, _ = E.point_along(P, max(0.01, f))
    Wd.panel(ctx, x - 26, y - 18, 52, 36, 1, C["gold"], fill="#d9c79a", fa=1, r=4)
    Wd.label_pill(ctx, "盟主背书", *cam(115.4, 36.5), C["yellow"], fade(lt, 1.5, None, 0.3), 30)
    pg = prog(t, S.a("c28b"), 0.5)
    if pg > 0:
        E.set_col(ctx, "#000000", 0.55 * pg); ctx.rectangle(0, 0, W, H); ctx.fill()
        txt = "輒共奉故平原相劉備府君以為宗主"
        Wd.panel(ctx, 60, 620, 960, 330, pg, C["gold"])
        E.draw_text(ctx, "裴注引书", 100, 650, "sans", "Medium", 24, "#a9c0d6", pg * 0.85, "lt")
        size = 58
        x0 = W / 2 - E.text_size(txt, "tc", "Bold", size)[0] / 2
        for i, ch in enumerate(txt):
            xx = x0 + E.text_size(txt[:i], "tc", "Bold", size)[0]
            hl = ch == "共"
            if hl:
                rr = prog(t, S.a("c28b") + 2.0, 0.6)
                E.circle(ctx, xx + size / 2, 780, 46, C["red2"], ease_out(rr), stroke=True, width=5)
            E.draw_text(ctx, ch, xx, 780, "tc", "Bold", size, C["red2"] if hl and t > S.a("c28b") + 2 else "#f4e7c8", pg, "lm")
        E.draw_text(ctx, "—— 《先主傳》裴注引《獻帝春秋》", W - 100, 880, "serif", "Medium", 30, C["gold2"], pg, "rm")
    caption(ctx, "事后：请盟主背书", fade(lt, 0, None, 0.3))


@scene("analogy2", qy=900)
def analogy2(ctx, t, S):
    dark_bg(ctx, "#0b0d10", "#141820", 11)
    a = fade(t, S.a("c31"), None, 0.4)
    big_text(ctx, "两年以后", W / 2, 1420, 96, C["blue2"], a)


# ═════════════════════ 四 失与得 ═════════════════════
@scene("lose", qy=1300)
def lose(ctx, t, S):
    lt = t - S.t0
    cam = G.Cam(118.25, 33.75, 400)
    G.base(ctx, cam, dim=0.85, prov_labels=False)
    tint_poly(ctx, cam, "徐州", C["red"], 0.12 * (1 - prog(t, S.a("d02"), 2)), C["red2"])
    for nm in ("下邳", "盱眙", "淮阴", "寿春", "广陵", "海西"):
        G.city(ctx, cam, nm, 1, "#e8dcc0", 32, side="r" if nm != "寿春" else "cb")
    # 袁术来攻
    Wd.thick_arrow(ctx, [cam.p("寿春"), cam(117.6, 32.9), cam(118.3, 33.05)], ease_out(prog(lt, 0.3, 2.5)), 50, 90,
                   **Wd.arrow_style("yuan"))
    x, y = cam(118.65, 33.25)
    troop("ls_liu", 400, (70, 90), 81, C["red2"], None, 4.5).draw(ctx, x + 30, y, t, 1,
                                                                    rout=ease_out(prog(t, S.a("d02") + 1.5, 4)), rout_dir=(0.8, 0.6))
    Wd.label_pill(ctx, "相持经月", x + 160, y - 160, C["red"], fade(lt, 1.5, None, 0.3), 28, "#fff2ee")
    # 吕布袭下邳
    pb = ease_out(prog(t, S.a("d02"), 2.0))
    xp = cam.p("下邳")
    Wd.thick_arrow(ctx, [(xp[0] - 420, xp[1] - 260), (xp[0] - 200, xp[1] - 120), (xp[0] - 20, xp[1] - 10)], pb, 40, 80,
                   **Wd.arrow_style("lv"))
    if pb > 0:
        fortress(ctx, xp[0], xp[1], 40, C["blue2"] if pb > 0.9 else "#e8dcc0")
    pc = prog(t, S.a("d02b"), 0.5)
    if pc > 0:
        Wd.label_pill(ctx, "张飞欲杀曹豹", xp[0] + 120, xp[1] - 170, C["red"], pc, 28, "#fff2ee")
        Wd.label_pill(ctx, "曹豹招吕布", xp[0] + 120, xp[1] - 100, C["blue"], fade(t, S.a("d02b") + 2.5, None, 0.3), 28)
    pg = prog(t, S.a("d02d"), 0.5)
    if pg > 0:
        Wd.label_pill(ctx, "丹阳兵开门", xp[0] - 40, xp[1] + 90, C["green"], pg, 32)
        for k in range(3):
            Wd.glow_dot(ctx, xp[0] - 30 + k * 30, xp[1] + 20, 6, C["green2"], pg, math.sin(t * 5 + k))
    pd = prog(t, S.a("d03"), 0.5)
    if pd > 0:
        Wd.label_pill(ctx, "陶谦旧部", xp[0] - 40, xp[1] + 150, C["green"], pd, 30)
    pe = prog(t, S.a("d03b"), 0.6)
    if pe > 0:
        E.set_col(ctx, "#000000", 0.5 * pe); ctx.rectangle(0, 0, W, H); ctx.fill()
        troop("ls_regrow", 900, (200, 160), 82, C["red2"], None, 4).draw(ctx, W / 2, 900, t, pe, count=int(900 * ease_out(pe)))
        big_text(ctx, "回小沛 · 万余人", W / 2, 1180, 72, C["red2"], pe)
    caption(ctx, "196年 · 徐州得而复失", fade(lt, 0, None, 0.3))


@scene("gain", qy=1250)
def gain(ctx, t, S):
    dark_bg(ctx, "#100d0a", "#1c1712", 12)
    a0 = fade(t, S.a("d04"), None, 0.4)
    E.draw_text(ctx, "攒下了什么", W / 2, 360, "serif", "Black", 66, C["gold2"], a0, "cm", tracking=0.2)
    E.draw_text(ctx, "第一样：名分", W / 2, 470, "serif", "Bold", 48, "#f2e6cc", fade(t, S.a("d05"), None, 0.4), "cm")
    tabs = [("一州之主", 0.3), ("镇东将军", 4.6), ("宜城亭侯", 5.6)]
    for i, (tx, dt) in enumerate(tabs):
        a = fade(t, S.a("d05") + dt, None, 0.3)
        x = 200 + i * 340
        Wd.panel(ctx, x - 130, 560, 260, 420, a, C["gold"], fill="#1d150c", fa=0.95)
        E.draw_text(ctx, tx, x, 770, "serif", "Black", 62, "#f4e2b8", a, "cm", vertical=True)
    pb = fade(t, S.a("d05b"), None, 0.4)
    if pb > 0:
        Wd.panel(ctx, 140, 1060, 800, 150, pb, C["red2"])
        E.draw_text(ctx, "投曹操 → 豫州牧", W / 2, 1110, "serif", "Black", 56, C["red2"], pb, "cm")
        E.draw_text(ctx, "徐州那段履历，成了身价", W / 2, 1175, "sans", "Medium", 32, "#e8dcc0", pb, "cm")


@scene("gain2", qy=1230)
def gain2(ctx, t, S):
    dark_bg(ctx, "#100d0a", "#1c1712", 13)
    E.draw_text(ctx, "第二样：人和钱", W / 2, 330, "serif", "Bold", 52, "#f2e6cc", fade(t, S.t0, None, 0.4), "cm")
    cx, cy = W / 2, 820
    # 刘备：困匮的小红点 → 复振
    fl = prog(t, S.a("d07"), 6.0)
    r = lerp(40, 90, ease_out(fl))
    Wd.glow_dot(ctx, cx, cy, r * 0.5, C["red"], 1, math.sin(t * 3))
    E.draw_text(ctx, "刘备", cx, cy, "serif", "Black", 44, "#fff2ee", 1, "cm")
    E.draw_text(ctx, "广陵海西 · 困匮", cx, cy + 110, "sans", "Medium", 30, "#cfc3aa", 1 - fl, "cm")
    # 麋竺：金与人流入
    mx, my = 220, 520
    name_tile(ctx, mx, my, "麋竺", "东海豪商", "#c9b27a", fade(t, S.t0 + 1, None, 0.4), 54)
    if not hasattr(gain2, "lag"):
        rng = np.random.default_rng(21)
        gain2.lag = rng.random(500); gain2.off = rng.normal(0, 1, (500, 2)) * 40; gain2.gold = rng.random(500) < 0.35
    u = np.clip(fl * 1.5 - gain2.lag * 0.5, 0, 1)
    us = u * u * (3 - 2 * u)
    bx = (1 - us) * mx + us * cx + gain2.off[:, 0] * (1 - us * 0.7)
    by = (1 - us) * (my + 100) + us * cy + gain2.off[:, 1] * (1 - us * 0.7) - np.sin(us * np.pi) * 120
    for sel, col in ((gain2.gold, "#e6c35c"), (~gain2.gold, "#e9d7a8")):
        idx = np.where(sel & (u > 0) & (u < 1))[0]
        E.set_col(ctx, col, 0.9)
        for i in idx:
            ctx.rectangle(bx[i] - 2.5, by[i] - 2.5, 5, 5)
        ctx.fill()
    for i, (tx, dt) in enumerate((("妹妹为夫人", 0.5), ("奴客二千", 2.0), ("金银货币", 3.5))):
        Wd.label_pill(ctx, tx, 820, 470 + i * 70, "#8a7038", fade(t, S.a("d07") + dt, None, 0.3), 30, "#fff4d8")
    pm = fade(t, S.a("d08"), None, 0.4)
    if pm > 0:
        Wd.panel(ctx, 120, 1060, 840, 120, pm, "#c9b27a")
        E.draw_text(ctx, "麋竺、麋芳 · 皆去官，随先主周旋", W / 2, 1120, "serif", "Bold", 44, "#f2e6cc", pm, "cm")
    pz = fade(t, S.a("d09"), None, 0.4)
    big_text(ctx, "地盘丢了，人没丢", W / 2, 1300, 72, C["gold2"], pz)


# ═════════════════════ 五 演义 ═════════════════════
@scene("novel", qy=1200)
def novel(ctx, t, S):
    dark_bg(ctx, "#0f0d0b", "#1b1712", 14)
    a1 = fade(t, S.a("e02"), None, 0.4)
    a2 = fade(t, S.a("e03"), None, 0.4)
    E.draw_text(ctx, "三让徐州", W / 2, 360, "serif", "Black", 80, C["gold2"], fade(t, S.a("e01"), None, 0.4), "cm", tracking=0.25)
    Wd.panel(ctx, 70, 470, 940, 220, a1, "#8a8274")
    E.draw_text(ctx, "演义说", 110, 520, "sans", "Bold", 34, "#bcb3a3", a1, "lm")
    E.draw_text(ctx, "陶谦三次让徐州", 110, 600, "serif", "Black", 54, "#e3dacb", a1, "lm")
    E.draw_text(ctx, "刘备三次推辞", 110, 660, "sans", "Medium", 36, "#bcb3a3", a1, "lm")
    Wd.panel(ctx, 70, 730, 940, 300, a2, C["gold"])
    E.draw_text(ctx, "史书说", 110, 780, "sans", "Bold", 34, C["gold2"], a2, "lm")
    E.draw_text(ctx, "陶谦临终一句话", 110, 860, "serif", "Black", 54, "#f6e9d0", a2, "lm")
    E.draw_text(ctx, "当面劝进：麋竺、陈登、孔融", 110, 940, "serif", "Bold", 44, "#f6e9d0", a2, "lm")
    a3 = fade(t, S.a("e04"), None, 0.4)
    E.draw_text(ctx, "一个人的仁厚", 290, 1120, "serif", "Black", 50, "#bcb3a3", a3, "cm")
    E.draw_text(ctx, "→", W / 2, 1120, "serif", "Black", 50, C["gold"], a3, "cm")
    E.draw_text(ctx, "一州精英的选择", 790, 1120, "serif", "Black", 50, C["red2"], a3, "cm")
    a4 = fade(t, S.a("e05") + 4.0, None, 0.4)
    E.draw_text(ctx, "算盘一变，人也会变", W / 2, 1240, "serif", "Bold", 48, C["gold2"], a4, "cm")


# ═════════════════════ 收束 ═════════════════════
@scene("end", qy=1230)
def end(ctx, t, S):
    dark_bg(ctx, "#0e0c0a", "#1a1510", 15)
    lt = t - S.t0
    # 桃树
    tx, ty = W / 2, 760
    E.set_col(ctx, "#3b2a1e", 1)
    ctx.move_to(tx - 30, ty + 260); ctx.curve_to(tx - 20, ty + 120, tx - 60, ty + 40, tx - 10, ty - 60)
    ctx.line_to(tx + 20, ty - 50); ctx.curve_to(tx - 10, ty + 40, tx + 30, ty + 120, tx + 30, ty + 260); ctx.close_path(); ctx.fill()
    for (bx, by, bw) in ((-10, -60, 18), (-120, -160, 12), (110, -170, 12), (-60, -230, 9), (60, -240, 9)):
        E.line(ctx, tx - 5, ty - 40, tx + bx, ty + by, "#3b2a1e", bw, 1)
    if not hasattr(end, "bl"):
        rng = np.random.default_rng(31)
        ang = rng.random(240) * 6.283; rr = np.sqrt(rng.random(240)) * 240
        end.bl = np.stack([np.cos(ang) * rr * 1.2, np.sin(ang) * rr * 0.65 - 200], 1); end.ph = rng.random(240) * 6.28
    bl_a = fade(lt, 0.3, None, 2.0)
    for i, (bx, by) in enumerate(end.bl):
        E.circle(ctx, tx + bx, ty + by, 9 + 2 * math.sin(t * 2 + end.ph[i]), "#f0a7b4" if i % 3 else "#f7e3e6", bl_a * 0.85)
    # 小路：人从四面走来
    pth = fade(lt, 1.0, None, 3.0)
    E.set_col(ctx, "#8a7656", 0.28 * pth)
    ctx.move_to(tx - 40, ty + 260); ctx.curve_to(tx - 60, ty + 450, tx - 280, ty + 600, tx - 360, H)
    ctx.line_to(tx - 200, H); ctx.curve_to(tx - 120, ty + 600, tx + 20, ty + 450, tx + 40, ty + 260); ctx.close_path(); ctx.fill()
    if not hasattr(end, "walk"):
        end.walk = np.random.default_rng(5).random(60)
    for i, lg in enumerate(end.walk):
        u = (lt * 0.06 + lg) % 1.0
        x = lerp(tx - 280 + (i % 5) * 18, tx + (i % 3 - 1) * 20, u)
        y = lerp(H - 40, ty + 270, u)
        E.rect(ctx, x - 3, y - 3, 6, 6, "#e9d7a8", pth * (1 - u) * 0.9)
    words = [("平原的刺客", 230, 1240), ("路上的饥民", 540, 1320), ("徐州的豪商", 850, 1240)]
    for i, (w_, x, y) in enumerate(words):
        a = fade(t, S.a("f02") + 0.5 + i * 1.2, S.a("f02b") - 0.4, 0.4, 0.4)
        E.draw_text(ctx, w_, x, y, "serif", "Bold", 44, "#f2e6cc", a, "cm", shadow=6)
    pa = fade(t, S.a("f02b"), S.a("f03") - 0.3, 0.4)
    E.draw_text(ctx, "先让人离不开他", W / 2, 1220, "serif", "Black", 60, C["gold2"], pa, "cm")
    E.draw_text(ctx, "再等人来请", W / 2, 1310, "serif", "Black", 60, C["gold2"], pa, "cm")
    a5 = fade(t, S.a("f05"), None, 0.5)
    big_text(ctx, "人心，是自己走过来的", W / 2, 1320, 64, "#f6e9d0", a5)


@scene("takeaway", qy=1100)
def takeaway(ctx, t, S):
    dark_bg(ctx, "#0f0c0a", "#1c1610", 16)
    a = fade(t, S.a("f06") - 0.2, None, 0.5)
    E.draw_text(ctx, "可以带走的一句判断", W / 2, 470, "sans", "Medium", 34, C["gold"], fade(t, S.t0, None, 0.4), "cm", tracking=0.2)
    lines_ = ["有时你被选中，", "不是因为你最强，", "而是因为你强到能办事，", "又弱到让别人放心。"]
    for i, l in enumerate(lines_):
        ai = fade(t, S.a("f06") + i * 0.9, None, 0.4)
        col = C["red2"] if i == 3 else "#f4ead4"
        E.draw_text(ctx, l, W / 2, 640 + i * 120, "serif", "Black", 66, col, ai, "cm")


@scene("next", qy=1100)
def next_(ctx, t, S):
    dark_bg(ctx, "#0a0908", "#141210", 17)
    lt = t - S.t0
    a = fade(lt, 0.2, None, 0.6)
    E.draw_text(ctx, "下一集", W / 2, 560, "sans", "Medium", 40, C["gold"], a, "cm", tracking=0.3)
    big_text(ctx, "寄人篱下的上将", W / 2, 720, 100, "#f4ead4", a, tracking=0.1)
    E.draw_text(ctx, "品级很高，手下却没有兵", W / 2, 860, "serif", "Bold", 50, C["red2"], fade(lt, 1.5, None, 0.5), "cm")
    E.draw_text(ctx, "乱世起家录 · 刘备篇", W / 2, 1100, "sans", "Medium", 34, "#bfb39b", fade(lt, 2.5, None, 0.6), "cm", tracking=0.2)
    # 收尾渐黑
    fo = prog(t, S.t1 - 1.0, 1.0)
    if fo > 0:
        E.set_col(ctx, "#000000", fo); ctx.rectangle(0, 0, W, H); ctx.fill()
