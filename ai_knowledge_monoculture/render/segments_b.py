"""Segments: hiring machine, flash crash, corn 1970, Knight 45 minutes."""
import math

import cairo
import numpy as np

import art
import scenes
from engine import (CYAN, GREY, H, ORANGE, RED, SAFE_TOP, W, WHITE, clamp, draw_chapter_tag, draw_series_tag,
                    draw_text, ease_in_out, ease_out, hexrgb, lerp, overlay_grain, rounded_rect, set_color, vignette,
                    wrap)
from segments_a import group
from widgets import (arrow, big_lines, card, chapter_flash, icon_brake, icon_building, icon_clock, icon_doc,
                     icon_model, icon_person, icon_server, label_box, point_card, quote_card, rise, win)


# ============================================================================ hiring machine
def _resume(ctx, x, y, s, tag=None, stamp=0.0, alpha=1.0):
    w, h = 170 * s, 220 * s
    rounded_rect(ctx, x, y, w, h, 10 * s)
    set_color(ctx, "#E9EEF4", 0.95 * alpha)
    ctx.fill()
    set_color(ctx, "#9AA6B4", alpha)
    ctx.arc(x + 34 * s, y + 38 * s, 18 * s, 0, 2 * math.pi)
    ctx.fill()
    for i in range(6):
        ctx.rectangle(x + 64 * s if i < 2 else x + 18 * s, y + (26 + i * 26) * s, (w - (82 if i < 2 else 36) * s) * (0.95 if i % 2 else 0.7), 7 * s)
    ctx.fill()
    if tag:
        rounded_rect(ctx, x + 14 * s, y + h - 46 * s, w - 28 * s, 30 * s, 6 * s)
        set_color(ctx, "#F6D6DA", alpha)
        ctx.fill()
        draw_text(ctx, tag, x + w / 2, y + h - 30 * s, "mono_bold", 16 * s, "#8A1C2A", alpha, "mm")
    if stamp > 0:
        set_color(ctx, "#8A1C2A", 0.9 * stamp * alpha)
        ctx.arc(x + w - 30 * s, y + 30 * s, 26 * s * (1.4 - 0.4 * stamp), 0, 2 * math.pi)
        ctx.fill()
        draw_text(ctx, "−", x + w - 30 * s, y + 32 * s, "sans_black", 40 * s, WHITE, stamp * alpha, "mm")


def _machine(ctx, cx, cy, glow=0.0, label="简历打分程序", warn=None):
    w, h = 360, 250
    if glow > 0:
        g = cairo.RadialGradient(cx, cy, 20, cx, cy, 300)
        g.add_color_stop_rgba(0, *hexrgb(RED if warn else CYAN)[:3], 0.35 * glow)
        g.add_color_stop_rgba(1, *hexrgb(RED if warn else CYAN)[:3], 0)
        ctx.set_source(g)
        ctx.arc(cx, cy, 300, 0, 2 * math.pi)
        ctx.fill()
    rounded_rect(ctx, cx - w / 2, cy - h / 2, w, h, 28)
    set_color(ctx, "#0D1626")
    ctx.fill_preserve()
    set_color(ctx, CYAN)
    ctx.set_line_width(4)
    ctx.stroke()
    set_color(ctx, "#05080F")
    ctx.rectangle(cx - w / 2 - 6, cy - 50, 12, 100)
    ctx.rectangle(cx + w / 2 - 6, cy - 50, 12, 100)
    ctx.fill()
    for i in range(5):
        set_color(ctx, CYAN, 0.25 + 0.15 * (i % 2))
        ctx.rectangle(cx - 120 + i * 50, cy - 70, 30, 30)
        ctx.fill()
    draw_text(ctx, label, cx, cy + 40, "sans_bold", 32, CYAN, 1, "ms")
    if warn:
        draw_text(ctx, warn, cx, cy + 90, "sans_black", 36, "#FF8A8D", 1, "ms")


def hiring(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "嫌弃“女子”二字的机器", accent=ORANGE)
    draw_series_tag(ctx)
    k1 = win(t, c.s("c5_1"), c.e("c5_2"), 0.5, 0.4)
    if k1 > 0:
        big_lines(ctx, ["两千多年后", ("这个毛病住进了机器里", ORANGE)], 640, k1, 60)
        a2 = clamp((t - c.s("c5_2")) / 0.4) * k1
        label_box(ctx, "2018 年 10 月 · 路透社报道", W / 2, 960, 36, WHITE, alpha=a2)
    km = win(t, c.s("c5_3"), c.e("c5_9") + 0.2, 0.5, 0.4)
    if km > 0:
        ctx.push_group()
        warn = "规律：男的更好" if t >= c.s("c5_6") else None
        glow = clamp((t - c.s("c5_6")) / 0.5) if warn else 0.5 + 0.3 * math.sin(t * 3)
        _machine(ctx, W / 2, 620, glow, warn=warn)
        if t < c.s("c5_4"):
            draw_text(ctx, "据知情人：2014 年起", W / 2, 400, "sans_bold", 40, WHITE, clamp((t - c.s("c5_3")) / 0.4), "ms")
        k4 = win(t, c.s("c5_4"), c.e("c5_4"), 0.4, 0.3)
        if k4 > 0:
            label_box(ctx, "机器学习：从大量例子里自己找规律", W / 2, 400, 34, CYAN, alpha=k4)
            rng = np.random.default_rng(3)
            pr = clamp((t - c.s("c5_4")) / max(1, c.e("c5_4") - c.s("c5_4")))
            for i in range(40):
                x = rng.uniform(150, 930)
                y = 1050 - (x - 150) * 0.22 + rng.normal(0, 40)
                set_color(ctx, WHITE, 0.7 * k4 * clamp(pr * 3 - i / 40))
                ctx.arc(x, y, 6, 0, 2 * math.pi)
                ctx.fill()
            if pr > 0.6:
                set_color(ctx, CYAN, k4 * clamp((pr - 0.6) * 3))
                ctx.set_line_width(4)
                ctx.move_to(150, 1050)
                ctx.line_to(930, 1050 - 780 * 0.22)
                ctx.stroke()
        k5 = win(t, c.s("c5_5"), c.e("c5_6"), 0.4, 0.3)
        if k5 > 0:
            draw_text(ctx, "过去十年收到的简历", W / 2, 400, "sans_bold", 40, WHITE, k5, "ms")
            for i in range(12):
                _resume(ctx, 120 + (i % 6) * 145, 900 + (i // 6) * 150, 0.6, None, 0, k5)
            draw_text(ctx, "大多数来自男性", W / 2, 1280, "sans_black", 44, ORANGE, k5 * clamp((t - c.s("c5_5") - 1.5) / 0.4), "ms")
        k7 = win(t, c.s("c5_7"), c.e("c5_7"), 0.4, 0.3)
        if k7 > 0:
            span = max(1.0, c.e("c5_7") - c.s("c5_7"))
            for i in range(7):
                ph = ((t - c.s("c5_7")) / span * 2.2 - i * 0.28)
                if not (0 < ph < 1.4):
                    continue
                x = lerp(-120, W + 40, ph / 1.4)
                tagged = i % 2 == 1
                stamp = clamp((x - (W / 2 + 180)) / 40) if tagged else 0
                if abs(x - W / 2) < 170:
                    continue  # inside the machine
                _resume(ctx, x - 85, 520, 0.9, "women's" if tagged else None, stamp, k7)
            quote_card(ctx, t, c.s("c5_7") + 1.0, c.e("c5_7"), "“women's chess club captain”", "“女子国际象棋社社长”：扣分",
                       y=1080)
        k8 = win(t, c.s("c5_8"), c.e("c5_8"), 0.4, 0.3)
        if k8 > 0:
            steps = ["改了程序，不再盯着这几个词", "但没法保证它不换个法子歧视", "2017 年初，团队解散"]
            span = max(1.0, c.e("c5_8") - c.s("c5_8"))
            for i, st in enumerate(steps):
                a = clamp((t - c.s("c5_8") - span * 0.3 * i) / 0.4) * k8
                label_box(ctx, st, W / 2, 920 + i * 120, 34, WHITE if i < 2 else ORANGE, alpha=a)
        k9 = win(t, c.s("c5_9"), c.e("c5_9"), 0.4, 0.3)
        if k9 > 0:
            span = max(1.0, c.e("c5_9") - c.s("c5_9"))
            a1 = k9
            a2 = clamp((t - c.s("c5_9") - span * 0.5) / 0.4) * k9
            card(ctx, 70, 860, W - 140, 170, a1)
            draw_text(ctx, "知情人说", 110, 912, "sans_bold", 28, GREY, a1, "ls")
            draw_text(ctx, "招聘人员看过它的推荐，但从没只靠排名", 110, 975, "sans_medium", 34, WHITE, a1, "ls")
            card(ctx, 70, 1060, W - 140, 170, a2, stroke=CYAN)
            draw_text(ctx, "亚马逊方面表示", 110, 1112, "sans_bold", 28, CYAN, a2, "ls")
            draw_text(ctx, "这个工具从没被招聘人员用来评估求职者", 110, 1175, "sans_medium", 34, WHITE, a2, "ls")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(km)
    point_card(ctx, t, c.s("c5_10"), c.e("c5_10"), ["机器把过去多数人的偏见", ("学成了“规律”", ORANGE)], ORANGE)
    chapter_flash(ctx, t, c.seg.start, "嫌弃“女子”的机器", "2018 · 一份路透社报道", ORANGE)


# ============================================================================ flash crash
def _flash_chart(ctx, t, c, reveal, brake):
    cx0, cx1 = 120, W - 70
    cy0, cy1 = SAFE_TOP + 120, SAFE_TOP + 520
    Y = lambda v: cy0 + (0 - v) / 10.5 * (cy1 - cy0)
    X = lambda m: cx0 + m / 40 * (cx1 - cx0)
    for v in range(0, -11, -2):
        set_color(ctx, "#2A3850", 0.7)
        ctx.set_line_width(1)
        ctx.move_to(cx0, Y(v))
        ctx.line_to(cx1, Y(v))
        ctx.stroke()
        draw_text(ctx, f"{v}%", cx0 - 14, Y(v), "mono", 22, GREY, 0.9, "rm")
    for m, lab in [(0, "14:30"), (10, "14:40"), (20, "14:50"), (30, "15:00"), (40, "15:10")]:
        draw_text(ctx, lab, X(m), cy1 + 36, "mono", 22, GREY, 0.9, "ms")
    draw_text(ctx, "道琼斯指数，相对前一天收盘（示意）", cx0, cy0 - 30, "sans", 24, GREY, 1, "ls")
    xs, ys = scenes.flash_series()
    n = max(2, int(len(xs) * reveal))
    ctx.new_path()
    ctx.move_to(X(xs[0]), Y(0))
    for i in range(n):
        ctx.line_to(X(xs[i]), Y(ys[i]))
    ctx.line_to(X(xs[n - 1]), Y(0))
    ctx.close_path()
    g = cairo.LinearGradient(0, cy0, 0, cy1)
    g.add_color_stop_rgba(0, *hexrgb(ORANGE)[:3], 0.0)
    g.add_color_stop_rgba(1, *hexrgb(ORANGE)[:3], 0.22)
    ctx.set_source(g)
    ctx.fill()
    ctx.new_path()
    for i in range(n):
        (ctx.move_to if i == 0 else ctx.line_to)(X(xs[i]), Y(ys[i]))
    set_color(ctx, ORANGE)
    ctx.set_line_width(4)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    set_color(ctx, WHITE)
    ctx.arc(X(xs[n - 1]), Y(ys[n - 1]), 6, 0, 2 * math.pi)
    ctx.fill()
    if xs[n - 1] >= 17.0:
        lx, ly = X(17), Y(-9.16)
        set_color(ctx, RED)
        ctx.arc(lx, ly, 9, 0, 2 * math.pi)
        ctx.fill()
        draw_text(ctx, "14:47 最低 −9.16%", lx + 22, ly + 10, "sans_bold", 28, "#FF8A8D", 1, "ls")
        draw_text(ctx, "比前一天收盘低了将近 1000 点", lx + 22, ly + 48, "sans", 24, "#FF8A8D", 0.9, "ls")
    if brake > 0:
        bx = X(15.47)
        set_color(ctx, CYAN, 0.9 * brake)
        ctx.set_line_width(3)
        ctx.set_dash([8, 6])
        ctx.move_to(bx, cy0)
        ctx.line_to(bx, cy1)
        ctx.stroke()
        ctx.set_dash([])
        draw_text(ctx, "14:45:28", bx - 10, cy0 + 24, "mono_bold", 22, CYAN, brake, "rs")


def _ring(ctx, t, potato, alpha, cy=1050):
    nodes = []
    for i in range(18):
        a = i / 18 * 2 * math.pi
        r = 300 + (i % 2) * 40
        nodes.append((W / 2 + r * math.cos(a), cy + 88 * math.sin(a)))
    path_idx = [0, 7, 3, 11, 5, 15, 9, 1, 13, 6, 16, 4, 10, 2, 14, 8]
    hop = potato * (len(path_idx) - 1)
    for k in range(min(len(path_idx) - 1, int(hop) + 1)):
        (x1, y1), (x2, y2) = nodes[path_idx[k]], nodes[path_idx[k + 1]]
        set_color(ctx, RED, (0.12 + 0.05 * min(k, 10)) * alpha)
        ctx.set_line_width(2.5)
        ctx.move_to(x1, y1)
        ctx.curve_to(x1, y1 - 70, x2, y2 - 70, x2, y2)
        ctx.stroke()
    for (x, y) in nodes:
        rounded_rect(ctx, x - 22, y - 22, 44, 44, 8)
        set_color(ctx, ORANGE, 0.18 * alpha)
        ctx.fill_preserve()
        set_color(ctx, ORANGE, 0.9 * alpha)
        ctx.set_line_width(2.5)
        ctx.stroke()
    if potato > 0:
        k = min(len(path_idx) - 2, int(hop))
        f = hop - int(hop)
        (x1, y1), (x2, y2) = nodes[path_idx[k]], nodes[path_idx[k + 1]]
        hx = (1 - f) ** 3 * x1 + 3 * (1 - f) ** 2 * f * x1 + 3 * (1 - f) * f ** 2 * x2 + f ** 3 * x2
        hy = (1 - f) ** 3 * y1 + 3 * (1 - f) ** 2 * f * (y1 - 70) + 3 * (1 - f) * f ** 2 * (y2 - 70) + f ** 3 * y2
        for r, a in [(40, 0.12), (26, 0.25), (15, 1.0)]:
            set_color(ctx, RED, a * alpha)
            ctx.arc(hx, hy, r, 0, 2 * math.pi)
            ctx.fill()


def flash(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "闪电崩盘 · 2010 年 5 月 6 日", accent=ORANGE)
    draw_series_tag(ctx)
    # chart reveal schedule (minutes after 14:30 on the x axis: 0..40)
    m = 0.0
    if t >= c.s("c6_2"):
        m = 2.0 * clamp((t - c.s("c6_2")) / 1.0)
    if t >= c.s("c6_3"):
        m = 2 + 4 * clamp((t - c.s("c6_3")) / max(1, c.e("c6_9") - c.s("c6_3")))
    if t >= c.s("c6_10"):
        m = 6 + 11 * ease_in_out(clamp((t - c.s("c6_10")) / max(1, c.e("c6_10") - c.s("c6_10"))))
    if t >= c.s("c6_12"):
        m = 17 + 2 * clamp((t - c.s("c6_12")) / max(1, c.e("c6_12") - c.s("c6_12")))
    if t >= c.s("c6_13"):
        m = 19 + 21 * clamp((t - c.s("c6_13")) / max(1, c.e("c6_13") - c.s("c6_13")))
    chart_a = clamp((t - c.s("c6_2")) / 0.5)
    brake = clamp((t - c.s("c6_12") - 0.6) / 0.4)
    if chart_a > 0:
        group(ctx, chart_a, _flash_chart, t, c, m / 40, brake)
    k1 = win(t, c.s("c6_1") - 0.3, c.e("c6_1"), 0.4, 0.4)
    if k1 > 0:
        big_lines(ctx, ["再看一群反应更快的“人”", ("电脑程序", ORANGE)], 700, k1, 56)
    # lower panel states
    ly = 1050
    k3 = win(t, c.s("c6_3"), c.e("c6_3"), 0.4, 0.3)
    if k3 > 0:
        card(ctx, 80, ly - 170, W - 160, 300, k3, stroke=ORANGE)
        draw_text(ctx, "14:32 · 一家大基金公司的自动卖出程序", W / 2, ly - 100, "sans_bold", 34, ORANGE, k3, "ms")
        draw_text(ctx, "75,000 份合约", W / 2, ly - 10, "sans_black", 64, WHITE, k3, "ms")
        draw_text(ctx, "价值约 41 亿美元", W / 2, ly + 70, "sans_medium", 36, GREY, k3, "ms")
    k4 = win(t, c.s("c6_4"), c.e("c6_4"), 0.4, 0.3)
    if k4 > 0:
        label_box(ctx, "股指期货合约 = 跟着大盘涨跌的合约", W / 2, ly - 40, 36, WHITE, alpha=k4)
    k5 = win(t, c.s("c6_5"), c.e("c6_5"), 0.4, 0.3)
    if k5 > 0:
        card(ctx, 80, ly - 170, W - 160, 300, k5)
        draw_text(ctx, "只认一条：前一分钟成交量的 9%", W / 2, ly - 90, "sans_bold", 38, WHITE, k5, "ms")
        draw_text(ctx, "“without regard to price or time”", W / 2, ly - 10, "serif", 34, GREY, k5, "ms")
        draw_text(ctx, "不看价格，也不看时间", W / 2, ly + 60, "sans_black", 44, ORANGE, k5, "ms")
    kr = win(t, c.s("c6_6"), c.e("c6_9"), 0.4, 0.3)
    if kr > 0:
        potato = clamp((t - c.s("c6_7")) / max(1, c.e("c6_9") - c.s("c6_7")))
        _ring(ctx, t, potato, kr, ly)
        if t < c.s("c6_7"):
            draw_text(ctx, "高频交易：千分之一秒里自动买卖", W / 2, ly - 170, "sans_bold", 34, WHITE, kr, "ms")
        elif t < c.s("c6_8"):
            draw_text(ctx, "“烫手山芋”", W / 2, ly - 175, "sans_black", 44, "#FF8A8D", kr, "ms")
            draw_text(ctx, "“hot-potato” volume effect", W / 2, ly - 125, "serif", 26, GREY, kr, "ms")
        elif t < c.s("c6_9"):
            draw_text(ctx, "14 秒 · 倒手 27,000 多份 · 净买进约 200 份", W / 2, ly - 160, "sans_bold", 34, ORANGE, kr, "ms")
        else:
            draw_text(ctx, "成交越多 → 卖得越快 → 价格越低", W / 2, ly - 160, "sans_bold", 36, "#FF8A8D", kr, "ms")
    k11 = win(t, c.s("c6_11"), c.e("c6_11"), 0.4, 0.3)
    if k11 > 0:
        label_box(ctx, "成交价：1 美分甚至更低", W / 2 - 0, ly - 80, 38, "#FF8A8D", alpha=k11)
        label_box(ctx, "成交价：10 万美元一股", W / 2, ly + 40, 38, "#FF8A8D", alpha=k11 * clamp((t - c.s("c6_11") - 1.2) / 0.4))
    kb = win(t, c.s("c6_12"), c.e("c6_13"), 0.3, 0.3)
    if kb > 0:
        drop = ease_out(clamp((t - c.s("c6_12") - 0.6) / 0.35))
        icon_brake(ctx, W / 2, ly - 300 + 260 * drop, 80, CYAN, kb * drop)
        draw_text(ctx, "自动暂停 5 秒", W / 2, ly + 120, "sans_black", 52, CYAN, kb * drop, "ms")
    k14 = win(t, c.s("c6_14"), c.e("c6_14"), 0.4, 0.3)
    if k14 > 0:
        card(ctx, 80, ly - 190, W - 160, 330, k14, stroke=CYAN)
        icon_brake(ctx, 190, ly - 30, 56, CYAN, k14)
        draw_text(ctx, "单只股票“熔断”（2010 年 6 月起）", 280, ly - 100, "sans_bold", 32, CYAN, k14, "ls")
        draw_text(ctx, "5 分钟内涨跌超过 10%", 280, ly - 20, "sans_black", 42, WHITE, k14, "ls")
        draw_text(ctx, "→ 全市场暂停 5 分钟", 280, ly + 50, "sans_black", 42, WHITE, k14, "ls")
    point_card(ctx, t, c.s("c6_15"), c.e("c6_15"), ["盯着同一个信号的机器", "会把一阵小风吹成风暴", ("对策：关键处装刹车", CYAN)],
               ORANGE, y=780)
    chapter_flash(ctx, t, c.seg.start, "闪电崩盘", "2010 年 5 月 6 日 · 美国股市", ORANGE)


# ============================================================================ corn 1970
def _field(ctx, t, blight, mark=0.0):
    set_color(ctx, "#5A4426")
    ctx.paint()
    sp = 76
    for y in range(SAFE_TOP - 40, 1360, sp):
        set_color(ctx, "#4A3820", 0.55)
        ctx.rectangle(0, y + sp * 0.62, W, 12)
        ctx.fill()
    rows = list(range(SAFE_TOP + 10, 1360, sp))
    front = 1360 - blight * (1360 - SAFE_TOP)
    rng = np.random.default_rng(21)
    sway = 0.0   # static field: cheaper to encode, the blight itself carries the motion
    for ri, y in enumerate(rows):
        for ci, x in enumerate(range(20 + (ri % 2) * sp // 2, W + 40, sp)):
            jitter = rng.normal(0, 2)
            noise = rng.normal(0, 0.15)
            d = (y - front) / 240
            health = 1.0 - clamp(d + noise) if blight > 0 else 1.0
            art.corn_plant(ctx, x + jitter, y + jitter, 37, healthy=health, rot=0.3 + sway, seed=ri * 100 + ci)
            if mark > 0 and (ri * 7 + ci) % 20 < 17:   # ~85% carry the same marker
                set_color(ctx, CYAN, 0.9 * mark)
                ctx.arc(x + jitter, y + jitter, 6, 0, 2 * math.pi)
                ctx.fill()


def _film_grade(ctx, t):
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    set_color(ctx, "#F2B84B", 0.38)
    ctx.paint()
    ctx.restore()
    set_color(ctx, "#FFE2A8", 0.06)
    ctx.paint()
    vignette(ctx, 0.75, (0.12, 0.06, 0.0))
    overlay_grain(ctx, 3, 0.07)   # static grain (a moving grain would eat the bitrate budget)
    g = cairo.LinearGradient(W, 0, W - 260, 0)
    flick = 0.22
    g.add_color_stop_rgba(0, 1.0, 0.45, 0.15, flick)
    g.add_color_stop_rgba(1, 1.0, 0.45, 0.15, 0.0)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()


def _film_caption(ctx, lines, alpha, y=SAFE_TOP + 20):
    if alpha <= 0:
        return
    h = 70 + 62 * len(lines)
    rounded_rect(ctx, 60, y, W - 120, h, 14)
    set_color(ctx, "#1C1308", 0.8 * alpha)
    ctx.fill()
    yy = y + 76
    for i, ln in enumerate(lines):
        draw_text(ctx, ln, 96, yy, "sans_black" if i == 0 else "sans_medium", 44 if i == 0 else 32,
                  "#FFE3A3" if i == 0 else "#F7D9A0", alpha, "ls")
        yy += 62


def corn(ctx, t, c):
    blight = 0.0
    if t >= c.s("c7_6"):
        blight = 0.08 * clamp((t - c.s("c7_6")) / 1.5)
    if t >= c.s("c7_7"):
        blight = 0.08 + 0.72 * ease_in_out(clamp((t - c.s("c7_7")) / max(1, c.e("c7_8") - c.s("c7_7"))))
    if t >= c.e("c7_8"):
        blight = 0.8
    mark = win(t, c.s("c7_5"), c.e("c7_5"), 0.5, 0.5)
    _field(ctx, t, blight, mark)
    _film_grade(ctx, t)
    draw_text(ctx, "北 ↑", W - 90, SAFE_TOP + 330, "sans_bold", 32, "#FFE3A3", 0.9, "rs")
    draw_text(ctx, "南", W - 90, 1310, "sans_bold", 32, "#FFE3A3", 0.9, "rs")
    caps = [
        ("c7_1", "c7_1", ["这一次，“一个人”", "是一种玉米"]),
        ("c7_2", "c7_2", ["1960 年代 · 杂交玉米育种", "苦活：雇很多人下地，掰掉雄穗"]),
        ("c7_3", "c7_3", ["T 型细胞质", "天生不产生有活力的花粉 → 省掉这道活"]),
        ("c7_4", "c7_4", ["1970 年：约 85%", "美国商品玉米种子，都靠它生产"]),
        ("c7_5", "c7_5", ["每一株都是好玉米", "可八成以上，身上都带着同一样东西"]),
        ("c7_6", "c7_6", ["玉米小斑病 · 新菌株", "恰好专门对付 T 型细胞质"]),
        ("c7_7", "c7_7", ["从佛罗里达往北", "夏末已经到了明尼苏达"]),
        ("c7_8", "c7_8", ["减产约 15%", "损失逾 10 亿美元（约合今天 80 多亿）"]),
        ("c7_9", "c7_9", ["单一栽培 monoculture", "后来被研究算法的人借了过去"]),
    ]
    for a_id, b_id, lines in caps:
        _film_caption(ctx, lines, win(t, c.s(a_id), c.e(b_id), 0.4, 0.3))
    point_card(ctx, t, c.s("c7_10"), c.e("c7_10"), ["所有人都用同一样东西", "出一次错，就全错", ("“暴君”的另一张脸", CYAN)],
               CYAN, y=780)
    chapter_flash(ctx, t, c.seg.start, "玉米", "1970 · 美国玉米带", "#F5C542")


# ============================================================================ Knight Capital: 45 minutes
def knight(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "45 分钟 · 2012 年 8 月 1 日")
    draw_series_tag(ctx)
    k1 = win(t, c.s("c8_1") - 0.2, c.e("c8_1"), 0.4, 0.3)
    if k1 > 0:
        icon_clock(ctx, W / 2, 640, 150, 0.5 + 0.02 * clamp((t - c.s("c8_1")) / 3), WHITE, k1)
        draw_text(ctx, "09:30", W / 2, 920, "mono_bold", 110, CYAN, k1, "ms", glow=12)
        draw_text(ctx, "纽约股市开盘", W / 2, 1000, "sans_medium", 36, GREY, k1, "ms")
    k2 = win(t, c.s("c8_2"), c.e("c8_2"), 0.4, 0.3)
    if k2 > 0:
        label_box(ctx, "做市商：随时挂着买单和卖单", W / 2, 420, 38, CYAN, alpha=k2)
        for i in range(6):
            wb = 120 + 60 * ((i * 37) % 5)
            wa = 120 + 60 * ((i * 53) % 5)
            y = 560 + i * 70
            set_color(ctx, "#2ECC71", 0.75 * k2)
            ctx.rectangle(W / 2 - 20 - wb, y, wb, 46)
            ctx.fill()
            set_color(ctx, "#FF6B6B", 0.75 * k2)
            ctx.rectangle(W / 2 + 20, y, wa, 46)
            ctx.fill()
        draw_text(ctx, "买单", W / 2 - 200, 1020, "sans_bold", 34, "#2ECC71", k2, "ms")
        draw_text(ctx, "卖单", W / 2 + 200, 1020, "sans_bold", 34, "#FF6B6B", k2, "ms")
    ks = win(t, c.s("c8_3"), c.e("c8_4"), 0.4, 0.3)
    if ks > 0:
        draw_text(ctx, "8 台服务器", W / 2, 420, "sans_black", 48, WHITE, ks, "ms")
        prog = clamp((t - c.s("c8_3")) / max(1, (c.e("c8_3") - c.s("c8_3")) * 0.8))
        wake = clamp((t - c.s("c8_4")) / 0.8)
        for i in range(8):
            x = 160 + (i % 2) * 420
            y = 520 + (i // 2) * 150
            done = prog > (i + 1) / 8 and i != 7
            col = CYAN if done else (RED if (i == 7 and wake > 0) else GREY)
            led = "#2ECC71" if done else (RED if i == 7 and wake > 0 else "#555555")
            icon_server(ctx, x, y, 2.6, col, ks, led)
            lab = "新代码 ✓" if done else ("漏装 · 旧程序醒了" if i == 7 and wake > 0 else ("漏装新代码" if i == 7 and prog > 0.95 else ""))
            draw_text(ctx, lab, x + 160, y + 140, "sans_bold", 28, col, ks, "ms")
        if wake > 0:
            g = cairo.RadialGradient(580 + 160, 520 + 3 * 150 + 60, 10, 580 + 160, 520 + 3 * 150 + 60, 260)
            g.add_color_stop_rgba(0, 0.9, 0.2, 0.25, 0.35 * wake * ks)
            g.add_color_stop_rgba(1, 0.9, 0.2, 0.25, 0)
            ctx.set_source(g)
            ctx.paint()
    kc = win(t, c.s("c8_5"), c.e("c8_6"), 0.4, 0.3)
    if kc > 0:
        span = max(1.0, c.e("c8_6") - c.s("c8_5"))
        p = clamp((t - c.s("c8_5")) / span)
        secs = int(round(45 * 60 * (1 - p)))
        draw_text(ctx, f"{secs // 60:02d}:{secs % 60:02d}", W / 2, 640, "mono_bold", 170, RED, kc, "ms", glow=16)
        draw_text(ctx, "45 分钟", W / 2, 420, "sans_black", 48, WHITE, kc, "ms")
        orders = int(4_000_000 * min(1, p * 1.25))
        draw_text(ctx, f"成交 {orders:,} 笔", W / 2, 800, "mono_cjk", 48, WHITE, kc, "ms")
        draw_text(ctx, "涉及 154 只股票", W / 2, 870, "sans_medium", 34, GREY, kc, "ms")
        loss_p = clamp((t - c.s("c8_6")) / max(1, c.e("c8_6") - c.s("c8_6")))
        if t >= c.s("c8_6"):
            loss = 460_000_000 * ease_out(loss_p)
            draw_text(ctx, f"−${loss:,.0f}", W / 2, 1040, "mono_bold", 66, RED, kc, "ms", glow=10)
            draw_text(ctx, "亏损 4.6 亿多美元", W / 2, 1110, "sans_bold", 36, "#FF8A8D", kc * clamp(loss_p * 2), "ms")
        # the red switch nobody presses
        set_color(ctx, "#2A0E12", kc)
        ctx.arc(W / 2, 1230, 56, 0, 2 * math.pi)
        ctx.fill()
        set_color(ctx, RED, kc)
        ctx.arc(W / 2, 1230, 44, 0, 2 * math.pi)
        ctx.fill()
        draw_text(ctx, "停", W / 2, 1232, "sans_black", 40, WHITE, kc, "mm")
    k7 = win(t, c.s("c8_7"), c.e("c8_7"), 0.4, 0.3)
    if k7 > 0:
        label_box(ctx, "几天后：投资者注资 4 亿美元续命", W / 2, 700, 38, WHITE, alpha=k7)
        label_box(ctx, "第二年：和另一家公司合并", W / 2, 860, 38, GREY, alpha=k7 * clamp((t - c.s("c8_7") - 1.5) / 0.4))
    point_card(ctx, t, c.s("c8_8"), c.e("c8_8"), ["一个系统，一个开关", "没有人按得住", ("机器时代的“一个人说了算”", CYAN)],
               CYAN, y=780)
    chapter_flash(ctx, t, c.seg.start, "45 分钟", "2012 · 纽约", CYAN)


RENDERERS = {"hiring": hiring, "flash": flash, "corn": corn, "knight": knight}
