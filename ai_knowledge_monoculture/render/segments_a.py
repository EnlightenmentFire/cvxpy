"""Segments: photocopy (model collapse), two ills, Plymouth 1906, Athens 399 BC."""
import math

import cairo
import numpy as np

import art
import scenes
from engine import (CYAN, GREY, H, ORANGE, RED, SAFE_TOP, W, WHITE, clamp, draw_chapter_tag, draw_series_tag,
                    draw_text, ease_in_out, ease_out, hexrgb, lerp, rounded_rect, set_color, wrap)
from widgets import (arrow, big_lines, card, chapter_flash, icon_doc, icon_model, icon_person, label_box,
                     point_card, quote_card, rise, win)


def group(ctx, a, fn, *args, **kw):
    """Draw fn into a group and composite it with alpha a."""
    if a <= 0.003:
        return
    if a >= 0.997:
        fn(ctx, *args, **kw)
        return
    ctx.push_group()
    fn(ctx, *args, **kw)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ============================================================================ photocopy / model collapse
def _llm_panel(ctx, t, c):
    p2 = c.s("c1_2")
    k, dy = rise(t, c.s("c1_1") - 0.2, 0.6)
    draw_text(ctx, "这个实验是怎么做的", W / 2, 400 + dy, "sans_black", 56, WHITE, k, "ms")
    a2 = clamp((t - p2) / 0.5)
    label_box(ctx, "大语言模型", W / 2, 520, 40, CYAN, alpha=a2)
    draw_text(ctx, "一个读了海量文字、学会了“接话”的程序", W / 2, 610, "sans_medium", 34, GREY, a2, "ms")
    icon_model(ctx, W / 2, 760, 1.1, CYAN, a2, label=None)
    # chat bubbles: "you say the first half, it says the second half"
    tb1 = p2 + (c.e("c1_2") - p2) * 0.66
    tb2 = p2 + (c.e("c1_2") - p2) * 0.83
    for (tb, txt, who, x, col) in [(tb1, "床前明月光，", "你说上半句", 120, "#2A3A55"),
                                   (tb2, "疑是地上霜。", "它接下半句", W - 120, CYAN)]:
        a = clamp((t - tb) / 0.3)
        if a <= 0:
            continue
        n = int(len(txt) * clamp((t - tb) / 0.6))
        w = 420
        bx = x if x < W / 2 else x - w
        by = 930 if x < W / 2 else 1100
        rounded_rect(ctx, bx, by, w, 110, 30)
        set_color(ctx, col, 0.9 * a if col != CYAN else 0.22 * a)
        ctx.fill_preserve()
        set_color(ctx, col if col == CYAN else GREY, a)
        ctx.set_line_width(2.5)
        ctx.stroke()
        draw_text(ctx, txt[:n], bx + w / 2, by + 56, "serif_bold", 46, WHITE, a, "mm")
        draw_text(ctx, who, bx + (24 if x < W / 2 else w - 24), by - 18, "sans", 26, GREY, a, "ls" if x < W / 2 else "rs")


def _books_panel(ctx, t, c):
    a3 = clamp((t - c.s("c1_3") + 0.2) / 0.5)
    label_box(ctx, "训练数据 = 喂给它读的书", W / 2, 420, 40, ORANGE, alpha=a3)
    # bookshelf of documents flowing into the model
    mx, my = W / 2 + 230, 800
    is_opt = t >= c.s("c1_4") - 0.1
    icon_model(ctx, mx, my, 1.25, CYAN, 1.0, label="OPT · 很小的模型" if is_opt else "模型")
    rng = np.random.default_rng(3)
    cols = ["#E5484D", "#3FD3E8", "#F5C542", "#7BD389", "#FF9A3C", "#B48EF0"]
    for i in range(7):
        bx = 100 + (i % 2) * 18
        by = 580 + i * 62
        set_color(ctx, cols[i % len(cols)], 0.85)
        rounded_rect(ctx, bx, by, 300 - (i % 3) * 30, 50, 6)
        ctx.fill()
        set_color(ctx, "#0A0F18", 0.5)
        ctx.rectangle(bx + 20, by + 8, 6, 34)
        ctx.fill()
    # moving documents
    span = c.e("c1_4") - c.s("c1_3")
    for i in range(6):
        ph = ((t - c.s("c1_3")) / max(1, span) * 3 + i / 6) % 1.0
        x = lerp(430, mx - 110, ph)
        y = 760 + math.sin(ph * math.pi) * -60 + (i % 3 - 1) * 30
        icon_doc(ctx, x - 30, y - 40, 0.55, WHITE, 0.9 * math.sin(ph * math.pi))
    if is_opt:
        a4 = clamp((t - c.s("c1_4")) / 0.4)
        label_box(ctx, "维基百科文章", 270, 1080, 32, WHITE, alpha=a4)


def _chain_panel(ctx, t, c):
    label_box(ctx, "自己写的文章，教下一代", W / 2, 400, 40, ORANGE)
    s, e = c.s("c1_5"), c.e("c1_5")
    pts = [(220, 560), (540, 640), (860, 560), (860, 820), (540, 900), (220, 820), (220, 1080), (540, 1160)]
    n = len(pts)
    shown = (t - s) / max(0.5, e - s) * (n + 0.5)
    for i, (x, y) in enumerate(pts):
        a = clamp(shown - i)
        if a <= 0:
            continue
        if i % 2 == 0:
            gen = i // 2
            mix = clamp(gen / 3)
            col = tuple(lerp(hexrgb(CYAN)[j], hexrgb(ORANGE)[j], mix) for j in range(3)) + (1,)
            icon_model(ctx, x, y, 0.72, col, a, label=f"第 {gen} 代")
        else:
            icon_doc(ctx, x - 32, y - 44, 0.72, ORANGE, a, accent=ORANGE)
        if i > 0 and a > 0:
            x0, y0 = pts[i - 1]
            arrow(ctx, x0 + (x - x0) * 0.25, y0 + (y - y0) * 0.25, x0 + (x - x0) * 0.72, y0 + (y - y0) * 0.72,
                  GREY, a * 0.8, 3)
    draw_text(ctx, "……一代一代传下去", W / 2, 1290, "sans_medium", 32, GREY, clamp(shown - n), "ms")


def _copies_panel(ctx, t, c):
    s, e = c.s("c1_6"), c.e("c1_6")
    cw, ch = 292, 370
    ytop = 470
    for i, g in enumerate((0, 4, 9)):
        ti = s + (e - s) * (0.05 + 0.33 * i)
        a = clamp((t - ti) / 0.35)
        if a <= 0:
            continue
        x = 44 + i * (cw + 37)
        ctx.save()
        set_color(ctx, "#000000", 0.45 * a)
        ctx.rectangle(x + 8, ytop + 10, cw, ch)
        ctx.fill()
        ctx.set_source_surface(scenes.copy_surface(g, cw, ch), x, ytop + (1 - a) * 30)
        ctx.paint_with_alpha(a)
        ctx.restore()
        lab = "原图" if g == 0 else f"复印 {g} 次"
        draw_text(ctx, lab, x + cw / 2, ytop + ch + 50, "sans_bold", 32, WHITE if g == 0 else ORANGE, a, "ms")
        if i < 2:
            set_color(ctx, GREY, 0.8 * a)
            ax = x + cw + 6
            ctx.move_to(ax + 4, ytop + ch / 2)
            ctx.line_to(ax + 25, ytop + ch / 2 - 12)
            ctx.line_to(ax + 25, ytop + ch / 2 + 12)
            ctx.close_path()
            ctx.fill()
    draw_text(ctx, "复印件的复印件", W / 2, 400, "sans_black", 52, WHITE, clamp((t - s) / 0.4), "ms")
    a7 = clamp((t - c.s("c1_7")) / 0.4)
    if a7 > 0:
        label_box(ctx, "模型崩溃", W / 2, 1060, 52, ORANGE, alpha=a7, font="sans_black")
        draw_text(ctx, "model collapse", W / 2, 1160, "serif", 36, GREY, a7, "ms")


def _curve_panel(ctx, t, c):
    gx0, gx1 = 90, W - 90
    gy_base = 1080
    gh = 330
    xs_ = np.linspace(-4, 4, 400)
    X = lambda xv: gx0 + (xv + 4) / 8 * (gx1 - gx0)
    bell = scenes.bell
    reveal = clamp((t - c.s("c1_8")) / 1.2)
    tails = clamp((t - c.s("c1_9") - (c.e("c1_9") - c.s("c1_9")) * 0.45) / 0.6)
    collapse = clamp((t - c.s("c1_10")) / max(0.5, (c.e("c1_10") - c.s("c1_10")) * 0.85))
    keep = clamp((t - c.s("c1_11") - (c.e("c1_11") - c.s("c1_11")) * 0.3) / 1.0)
    draw_text(ctx, "最先丢掉的，是少见的东西", W / 2, 420, "sans_black", 50, WHITE, clamp((t - c.s("c1_8")) / 0.4), "ms")
    sd0, h0 = 1.25, gh * 0.55
    n = max(2, int(len(xs_) * reveal))
    pts0 = [(X(xv), gy_base - yv) for xv, yv in zip(xs_, bell(xs_, 0, sd0) * h0)]
    if tails > 0:
        for side in (-1, 1):
            sel = [p for p, xv in zip(pts0, xs_) if side * xv > 1.9]
            ctx.new_path()
            ctx.move_to(sel[0][0], gy_base)
            for px, py in sel:
                ctx.line_to(px, py)
            ctx.line_to(sel[-1][0], gy_base)
            ctx.close_path()
            set_color(ctx, RED, 0.35 * tails * (1 - 0.6 * collapse))
            ctx.fill()
    ctx.new_path()
    for i, (px, py) in enumerate(pts0[:n]):
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    set_color(ctx, WHITE, 0.85)
    ctx.set_line_width(3.5)
    ctx.set_dash([10, 8])
    ctx.stroke()
    ctx.set_dash([])
    # collapsing generations
    if collapse > 0:
        g = collapse * 9
        sd = sd0 * (1 - 0.66 * clamp(g / 9))
        hh = h0 * (1 + 0.82 * clamp(g / 9))
        ctx.new_path()
        for i, (xv, yv) in enumerate(zip(xs_, bell(xs_, 0, sd) * hh)):
            (ctx.move_to if i == 0 else ctx.line_to)(X(xv), gy_base - yv)
        set_color(ctx, ORANGE, 1)
        ctx.set_line_width(4.5)
        ctx.stroke()
        draw_text(ctx, f"第 {int(round(g))} 代", X(0.45), gy_base - hh - 16, "sans_bold", 30, ORANGE, 1, "ls")
        for xv in (-2.0, 2.0):
            sx = X(xv)
            set_color(ctx, RED, 0.9 * min(1, collapse * 3))
            ctx.set_line_width(3)
            ctx.set_dash([6, 6])
            ctx.move_to(sx, gy_base - 150)
            ctx.line_to(sx, gy_base + 6)
            ctx.stroke()
            ctx.set_dash([])
            draw_text(ctx, "✂", sx, gy_base - 160, "sans", 42, "#FF8A8D", min(1, collapse * 3), "ms")
    if keep > 0:
        # with 10% real data each generation: only slight narrowing
        ctx.new_path()
        for i, (xv, yv) in enumerate(zip(xs_, bell(xs_, 0, sd0 * 0.9) * h0 * 1.08)):
            (ctx.move_to if i == 0 else ctx.line_to)(X(xv), gy_base - yv)
        set_color(ctx, "#7BD389", keep)
        ctx.set_line_width(5)
        ctx.stroke()
        label_box(ctx, "每代掺进 10% 真实数据：只轻微退化", W / 2, 1210, 32, "#9BE3A6", alpha=keep)
    set_color(ctx, GREY, 0.7)
    ctx.set_line_width(2)
    ctx.move_to(gx0, gy_base)
    ctx.line_to(gx1, gy_base)
    ctx.stroke()
    if keep <= 0:
        draw_text(ctx, "最常见", W / 2, gy_base + 44, "sans", 26, GREY, reveal, "ms")
        draw_text(ctx, "少见", gx0 + 40, gy_base + 44, "sans", 26, GREY, reveal, "ms")
        draw_text(ctx, "少见", gx1 - 40, gy_base + 44, "sans", 26, GREY, reveal, "ms")
    if tails > 0:
        draw_text(ctx, "尾巴：少见，但真实存在", gx0, 560, "sans_medium", 30, "#FF8A8D", tails * (1 - keep), "ls")
        set_color(ctx, "#FF8A8D", 0.9 * tails * (1 - keep))
        ctx.set_line_width(2)
        ctx.move_to(gx0 + 70, 576)
        ctx.line_to(X(-2.6), gy_base - 30)
        ctx.stroke()


def photocopy(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "复印件的复印件 · 模型崩溃")
    draw_series_tag(ctx)
    group(ctx, win(t, c.s("c1_1") - 0.5, c.e("c1_2")), _llm_panel, t, c)
    group(ctx, win(t, c.s("c1_3"), c.e("c1_4")), _books_panel, t, c)
    group(ctx, win(t, c.s("c1_5"), c.e("c1_5")), _chain_panel, t, c)
    group(ctx, win(t, c.s("c1_6"), c.e("c1_7")), _copies_panel, t, c)
    group(ctx, win(t, c.s("c1_8"), c.e("c1_12") + 0.5), _curve_panel, t, c)
    point_card(ctx, t, c.s("c1_12"), c.e("c1_12"),
               ["只听自己声音的系统", ("离真实世界越来越远", ORANGE)], ORANGE)
    chapter_flash(ctx, t, c.seg.start, "复印件的复印件", "模型崩溃是怎么回事", ORANGE)


# ============================================================================ two old ills
def twoills(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "两种老毛病")
    draw_series_tag(ctx)
    k, dy = rise(t, c.s("c2_1"), 0.6)
    swap = clamp((t - c.s("c2_5")) / 0.4)
    draw_text(ctx, "人立规矩，一直在防两件坏事", W / 2, 380 + dy, "sans_black", 48, WHITE, k * (1 - swap), "ms")
    draw_text(ctx, "AI 时代：两个老毛病都换了新衣服", W / 2, 380, "sans_black", 46, WHITE, swap, "ms")
    lx, rx, cy = W / 2 - 250, W / 2 + 250, 720
    ai_t = c.s("c2_5")
    ai = ease_in_out(clamp((t - ai_t - 0.3) / 1.0))
    focus_left = clamp((t - c.s("c2_6")) / 0.4) * (1 - clamp((t - c.s("c2_7")) / 0.4))
    focus_right = clamp((t - c.s("c2_7")) / 0.4)
    dim_l = 1 - 0.65 * focus_right * (1 - focus_left)
    dim_r = 1 - 0.65 * focus_left
    # --- left: one voice
    a3 = clamp((t - c.s("c2_3")) / 0.5) * dim_l
    if a3 > 0:
        if ai < 1:
            set_color(ctx, CYAN, 0.18 * a3 * (1 - ai))
            ctx.arc(lx, cy, 130, 0, 2 * math.pi)
            ctx.fill()
            set_color(ctx, CYAN, a3 * (1 - ai))
            ctx.set_line_width(5)
            ctx.arc(lx, cy, 130, 0, 2 * math.pi)
            ctx.stroke()
            draw_text(ctx, "1", lx, cy + 8, "sans_black", 120, CYAN, a3 * (1 - ai), "mm")
        if ai > 0:
            # one model, many users
            rng = np.random.default_rng(2)
            err = clamp((t - c.s("c2_6") - (c.e("c2_6") - c.s("c2_6")) * 0.35) / 0.8)
            for i in range(14):
                ang = math.pi * (0.15 + 0.7 * i / 13) + math.pi / 2
                ux, uy = lx + (i % 7 - 3) * 62, cy + 190 + (i // 7) * 90
                set_color(ctx, CYAN, 0.35 * a3 * ai)
                ctx.set_line_width(1.5)
                ctx.move_to(lx, cy + 60)
                ctx.line_to(ux, uy - 30)
                ctx.stroke()
                icon_person(ctx, ux, uy, 0.7, RED if err > (i / 14) else WHITE, a3 * ai)
            icon_model(ctx, lx, cy - 10, 1.0, CYAN, a3 * ai, label=None)
        draw_text(ctx, "一个人说了算", lx, cy - 200, "sans_bold", 38, CYAN, a3, "ms")
        draw_text(ctx, "暴君", lx, cy + 420, "sans_black", 64, CYAN, a3, "ms", glow=12)
        if ai > 0:
            draw_text(ctx, "新样子：所有人用同一个模型", lx, cy + 490, "sans", 28, GREY, a3 * ai, "ms")
    # --- right: many voices, one muddle
    a4 = clamp((t - c.s("c2_4")) / 0.5) * dim_r
    if a4 > 0:
        rng = np.random.default_rng(7)
        conv = clamp((t - c.s("c2_7")) / max(0.5, c.e("c2_7") - c.s("c2_7")))
        base_cols = [hexrgb(x)[:3] for x in ["#FF9A3C", "#F5C542", "#E5484D", "#7BD389", "#4D9CFF", "#B48EF0"]]
        for i in range(30):
            ang = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.uniform(0, 1)) * 120
            jitter = math.sin(t * 2.3 + i) * 6 * (1 - conv)
            x = rx + math.cos(ang) * r * (1 - 0.45 * conv) + jitter
            y = cy + math.sin(ang) * r * (1 - 0.45 * conv)
            bc = base_cols[i % len(base_cols)]
            oc = hexrgb(ORANGE)[:3]
            col = tuple(lerp(bc[j], oc[j], max(conv, 1 - ai)) for j in range(3)) + (1,)
            if ai > 0:
                s = 0.32
                rounded_rect(ctx, x - 24 * s * 2, y - 18 * s * 2, 48 * s * 2, 36 * s * 2, 6)
                set_color(ctx, col, a4 * (0.5 + 0.5 * ai))
                ctx.fill()
            else:
                set_color(ctx, col, a4)
                ctx.arc(x, y, 16, 0, 2 * math.pi)
                ctx.fill()
        if ai > 0:
            set_color(ctx, ORANGE, 0.25 * a4 * ai)
            ctx.set_line_width(1.2)
            pts = [(rx + math.cos(i * 2.4) * 100, cy + math.sin(i * 2.4) * 100) for i in range(12)]
            for i in range(12):
                for j in range(i + 1, 12, 3):
                    ctx.move_to(*pts[i])
                    ctx.line_to(*pts[j])
            ctx.stroke()
        draw_text(ctx, "一群人一起犯糊涂", rx, cy - 200, "sans_bold", 38, ORANGE, a4, "ms")
        draw_text(ctx, "暴民", rx, cy + 420, "sans_black", 64, ORANGE, a4, "ms", glow=12)
        if ai > 0:
            draw_text(ctx, "新样子：模型互相抄、越来越像", rx, cy + 490, "sans", 28, GREY, a4 * ai, "ms")
    chapter_flash(ctx, t, c.seg.start, "两种老毛病", "防暴君，也防暴民", CYAN)


# ============================================================================ Plymouth 1906
INK = scenes.INK


def _ticket(ctx, t, c, a):
    x, y, w, h = 230, 520, 620, 380
    ctx.save()
    ctx.translate(x + w / 2, y + h / 2)
    ctx.rotate(-0.04)
    ctx.translate(-(x + w / 2), -(y + h / 2))
    set_color(ctx, "#F6EFDD", a)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    set_color(ctx, INK, a)
    ctx.set_line_width(3)
    ctx.rectangle(x + 10, y + 10, w - 20, h - 20)
    ctx.stroke()
    draw_text(ctx, "WEIGHT-JUDGING COMPETITION", x + w / 2, y + 62, "fell_sc", 30, INK, a, "ms")
    draw_text(ctx, "猜牛重比赛 · 六便士一张（示意）", x + w / 2, y + 106, "serif", 26, INK, 0.8 * a, "ms")
    for i, lab in enumerate(["姓名  Name", "住址  Address", "估计净重  Estimate"]):
        yy = y + 170 + i * 62
        draw_text(ctx, lab, x + 40, yy, "serif", 28, INK, a, "ls")
        set_color(ctx, INK, 0.6 * a)
        ctx.set_line_width(1.5)
        ctx.move_to(x + 300, yy + 4)
        ctx.line_to(x + w - 40, yy + 4)
        ctx.stroke()
    draw_text(ctx, "cwt.  qrs.  lbs.", x + w - 40, y + 170 + 2 * 62 - 8, "fell_italic", 24, INK, 0.7 * a, "rs")
    ctx.restore()


def _plot(ctx, t, c, dots, lines, copying, label_alpha=1.0):
    vals = scenes.galton_estimates()
    lo, hi = 990, 1370
    ax0, ax1 = 100, W - 100
    base_y = 1215
    X = lambda v: ax0 + (v - lo) / (hi - lo) * (ax1 - ax0)
    binw, dot_r = 5.0, 3.3
    counts = {}
    rng = np.random.default_rng(1)
    order = np.argsort(rng.random(len(vals)))
    n_show = int(len(vals) * dots)
    for j, i in enumerate(order[:n_show]):
        v = vals[i]
        b = int((min(max(v, lo + 1), hi - 1) - lo) // binw)
        k = counts.get(b, 0)
        counts[b] = k + 1
        x = X(lo + (b + 0.5) * binw)
        y = base_y - 8 - k * (dot_r * 2.1)
        if copying > 0:
            tx = X(1320) + rng.normal(0, 8)
            ty = base_y - 30 - (j % 34) * 6.5
            e = ease_out(clamp(copying * 1.5 - (j / len(vals)) * 0.5))
            x, y = x + (tx - x) * e, y + (ty - y) * e
        set_color(ctx, INK, 0.85)
        ctx.arc(x, y, dot_r, 0, 2 * math.pi)
        ctx.fill()
    set_color(ctx, INK)
    ctx.set_line_width(2)
    ctx.move_to(ax0, base_y)
    ctx.line_to(ax1, base_y)
    ctx.stroke()
    for v in range(1000, 1371, 50):
        ctx.move_to(X(v), base_y)
        ctx.line_to(X(v), base_y + 10)
        ctx.stroke()
        draw_text(ctx, f"{v}", X(v), base_y + 40, "fell", 26, INK, 0.9, "ms")
    draw_text(ctx, "磅", ax1 + 26, base_y + 40, "serif", 24, INK, 0.9, "ms")
    draw_text(ctx, "每个点是一张票（示意：按高尔顿公布的分位数绘制）", ax0, base_y - 300, "serif", 22, INK,
              0.7 * label_alpha, "ls")
    if lines > 0:
        for v, col, lab, dx, anchor in [(1207, scenes.INK_RED, "中位数 1207", 12, "ls"),
                                        (1198, scenes.INK_BLUE, "实际 1198", -12, "rs")]:
            set_color(ctx, col, lines)
            ctx.set_line_width(3)
            ctx.move_to(X(v), base_y - 270)
            ctx.line_to(X(v), base_y + 2)
            ctx.stroke()
            draw_text(ctx, lab, X(v) + dx, base_y - 250, "serif_bold", 30, col, lines * label_alpha, anchor)
    if copying > 0:
        draw_text(ctx, "互相抄：一起滑向同一个错的数", X(1320), base_y - 260, "serif_bold", 30, scenes.INK_RED,
                  clamp(copying * 2), "rs")


def _condorcet(ctx, t, c, a):
    draw_text(ctx, "孔多塞 · 1785 · 陪审团定理", W / 2, 520, "serif_bold", 42, INK, a, "ms")
    x0, x1, y0, y1 = 150, W - 110, 620, 1180
    set_color(ctx, INK, a)
    ctx.set_line_width(2)
    ctx.move_to(x0, y0)
    ctx.line_to(x0, y1)
    ctx.line_to(x1, y1)
    ctx.stroke()
    draw_text(ctx, "多数判断正确的可能性", x0 + 10, y0 - 14, "serif", 26, INK, a, "ls")
    draw_text(ctx, "人数 →", x1, y1 + 44, "serif", 26, INK, a, "rs")
    for v, lab in [(0, "0"), (0.5, "50%"), (1, "100%")]:
        yy = y1 - v * (y1 - y0)
        draw_text(ctx, lab, x0 - 12, yy + 8, "fell", 24, INK, a, "rs")
        set_color(ctx, INK, 0.2 * a)
        ctx.move_to(x0, yy)
        ctx.line_to(x1, yy)
        ctx.stroke()
    from math import comb

    def maj(p, n):
        return sum(comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n // 2 + 1, n + 1))

    ns = list(range(1, 202, 4))
    curves = [(0.55, scenes.INK_BLUE, "各想各的，每人对的可能 55%", c.s("c3_16")),
              (0.45, scenes.INK_RED, "各想各的，每人对的可能 45%", c.s("c3_17")),
              (None, "#6B5A3A", "都跟着同一个人投：人再多也一样", c.s("c3_18"))]
    for p, col, lab, ts in curves:
        k = clamp((t - ts) / 1.2)
        if k <= 0:
            continue
        m = max(2, int(len(ns) * k))
        ctx.new_path()
        for i, n in enumerate(ns[:m]):
            v = maj(p, n) if p is not None else 0.55
            xx = x0 + (n - 1) / 200 * (x1 - x0)
            yy = y1 - v * (y1 - y0)
            (ctx.move_to if i == 0 else ctx.line_to)(xx, yy)
        set_color(ctx, col, a)
        ctx.set_line_width(4)
        if p is None:
            ctx.set_dash([12, 8])
        ctx.stroke()
        ctx.set_dash([])
        ly = {0.55: y0 + 60, 0.45: y1 - 50, None: y1 - 0.55 * (y1 - y0) - 22}[p]
        draw_text(ctx, lab, x1, ly, "serif_bold", 28, col, a * k, "rs")


def plymouth(ctx, t, c):
    scenes.paper_backdrop(ctx)
    scenes.victorian_border(ctx, 40, SAFE_TOP - 10, W - 80, 1140)
    # header changes once the article itself is mentioned
    head2 = clamp((t - c.s("c3_10")) / 0.5)
    if head2 < 1:
        draw_text(ctx, "Plymouth · 1906", W / 2, SAFE_TOP + 96, "fell", 70, INK, 1 - head2, "ms")
        draw_text(ctx, "英国普利茅斯 · 牲畜展览会", W / 2, SAFE_TOP + 150, "serif_medium", 32, INK, 1 - head2, "ms")
    if head2 > 0:
        draw_text(ctx, "VOX POPULI", W / 2, SAFE_TOP + 92, "fell", 84, INK, head2, "ms", tracking=0.08)
        draw_text(ctx, "人民的声音 · 高尔顿，《自然》1907 年 3 月", W / 2, SAFE_TOP + 146, "serif_medium", 30, INK,
                  head2, "ms")
    set_color(ctx, INK)
    ctx.set_line_width(1.5)
    ctx.move_to(W / 2 - 300, SAFE_TOP + 170)
    ctx.line_to(W / 2 + 300, SAFE_TOP + 170)
    ctx.stroke()
    draw_text(ctx, "West of England Fat Stock and Poultry Exhibition", W / 2, SAFE_TOP + 204, "fell_italic", 27, INK,
              0.85, "ms")
    # phases
    cond = win(t, c.s("c3_15") - 0.2, c.e("c3_18") + 0.1, 0.5, 0.4)
    main = 1 - cond
    if main > 0.003:
        ctx.push_group()
        ox_a = clamp((t - c.s("c3_1")) / 0.8) if t < c.s("c3_11") else 1.0
        if ox_a > 0:
            ctx.save()
            ctx.rectangle(0, 0, 200 + 1000 * 0.66 * ox_a + 40, H)
            ctx.clip()
            art.draw_ox_engraving(ctx, 200, SAFE_TOP + 215, 0.66)
            ctx.restore()
        if t < c.s("c3_5"):
            draw_text(ctx, "猜：它宰好、收拾干净以后有多重？", W / 2, 1060, "serif_bold", 38, INK, clamp((t - c.s("c3_2")) / 0.5),
                      "ms")
        dots = clamp((t - c.s("c3_5")) / 2.0)
        lines = clamp((t - c.s("c3_7")) / 0.5)
        copying = clamp((t - c.s("c3_14") - 1.2) / 3.0) * (1 - clamp((t - c.e("c3_14")) / 0.6))
        if dots > 0:
            _plot(ctx, t, c, dots, lines * (1 - clamp(copying * 3)), copying)
        if t >= c.s("c3_6") and t < c.s("c3_7"):
            draw_text(ctx, "从小到大排成一排，取正中间那一张", W / 2, 1300, "serif_bold", 32, INK, clamp((t - c.s("c3_6")) / 0.4),
                      "ms")
        k8 = win(t, c.s("c3_8"), c.e("c3_9"), 0.4, 0.4)
        if k8 > 0:
            draw_text(ctx, "787 张有效票 · 只差 9 磅（0.8%）", W / 2, 1300, "serif_bold", 34, INK, k8, "ms")
        k9 = win(t, c.s("c3_9"), c.e("c3_9"), 0.4, 0.4)
        if k9 > 0:
            card(ctx, 600, 850, 400, 170, k9, fill="#F6EFDD", stroke=INK)
            draw_text(ctx, "后人复核（Wallis 2014）", 800, 892, "serif_bold", 26, INK, k9, "ms")
            draw_text(ctx, "中位数 1208 · 实际 1197", 800, 940, "serif", 26, INK, k9, "ms")
            draw_text(ctx, "平均数 1197：正好命中", 800, 990, "serif_bold", 28, scenes.INK_RED, k9, "ms")
        k12 = win(t, c.s("c3_12"), c.e("c3_12"), 0.4, 0.35)
        if k12 > 0:
            card(ctx, 80, 470, W - 160, 330, k12, fill="#F6EFDD", stroke=INK)
            yy = 540
            for ln in wrap("“The judgments were unbiassed by passion and uninfluenced by oratory and the like.”",
                           "fell_italic", 40, W - 260):
                draw_text(ctx, ln, W / 2, yy, "fell_italic", 40, INK, k12, "ms")
                yy += 54
            draw_text(ctx, "这些判断，没被情绪左右，也没被谁的演说带偏。", W / 2, yy + 34, "serif_bold", 34, scenes.INK_RED, k12, "ms")
        k13 = win(t, c.s("c3_13"), c.e("c3_13"), 0.4, 0.35)
        if k13 > 0:
            draw_text(ctx, "← 猜低的　　误差互相抵消　　猜高的 →", W / 2, 860, "serif_bold", 32, INK, k13, "ms")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(main)
    k3 = win(t, c.s("c3_3"), c.e("c3_4"), 0.4, 0.4)
    if k3 > 0:
        ctx.push_group()
        _ticket(ctx, t, c, 1.0)
        if t >= c.s("c3_4"):
            a = clamp((t - c.s("c3_4")) / 0.4)
            draw_text(ctx, "屠夫 · 农夫 · 看牛的高手 · 凭感觉的人", W / 2, 980, "serif_bold", 34, INK, a, "ms")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k3)
    if cond > 0:
        group(ctx, cond, _condorcet, t, c, 1.0)
    k19 = win(t, c.s("c3_19"), c.e("c3_19"), 0.4, 0.4)
    if k19 > 0:
        set_color(ctx, "#EFE5CC", 0.85 * k19)
        ctx.rectangle(60, SAFE_TOP + 240, W - 120, 900)
        ctx.fill()
        card(ctx, 110, 600, W - 220, 380, k19, fill="#E9E1CF", stroke="#6B5A3A")
        draw_text(ctx, "另一面", W / 2, 680, "serif_bold", 36, "#6B5A3A", k19, "ms")
        draw_text(ctx, "高尔顿在 1883 年造了“优生学”这个词，", W / 2, 760, "serif", 32, INK, k19, "ms")
        draw_text(ctx, "这门学问后来被拿去伤害了很多人。", W / 2, 812, "serif", 32, INK, k19, "ms")
        draw_text(ctx, "做对一件事，不等于做的事都对。", W / 2, 900, "serif_bold", 34, scenes.INK_RED, k19, "ms")
    point_card(ctx, t, c.s("c3_20"), c.e("c3_20"), ["群众的聪明，不是来自“人多”", ("而是来自“不一样”", ORANGE)], ORANGE)
    chapter_flash(ctx, t, c.seg.start, "称牛", "1906 · 普利茅斯", ORANGE, light=True)


# ============================================================================ Athens 399 BC
CLAY, CLAY_LIGHT = scenes.CLAY, scenes.CLAY_LIGHT


def _athens_bg(ctx):
    set_color(ctx, scenes.POT_BLACK)
    ctx.paint()
    rng = np.random.default_rng(8)
    for _ in range(500):
        set_color(ctx, "#3A2418", rng.uniform(0.05, 0.2))
        ctx.arc(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 2.0), 0, 2 * math.pi)
        ctx.fill()
    for yb in (SAFE_TOP + 4, 1262):
        set_color(ctx, CLAY)
        ctx.rectangle(40, yb - 6, W - 80, 4)
        ctx.rectangle(40, yb + 52, W - 80, 4)
        ctx.fill()
        art.meander(ctx, 50, yb + 4, W - 100, 40, CLAY)


def _figure(ctx, x, y, s, col, alpha=1.0):
    """Very simple red-figure style standing figure (head + draped body)."""
    set_color(ctx, col, alpha)
    ctx.arc(x, y - 70 * s, 16 * s, 0, 2 * math.pi)
    ctx.fill()
    ctx.new_path()
    ctx.move_to(x - 14 * s, y - 50 * s)
    ctx.curve_to(x - 34 * s, y - 10 * s, x - 30 * s, y + 40 * s, x - 22 * s, y + 70 * s)
    ctx.line_to(x + 24 * s, y + 70 * s)
    ctx.curve_to(x + 30 * s, y + 30 * s, x + 30 * s, y - 20 * s, x + 14 * s, y - 50 * s)
    ctx.close_path()
    ctx.fill()


def athens(ctx, t, c):
    _athens_bg(ctx)
    draw_text(ctx, "公元前 399 年 · 雅典", W / 2, SAFE_TOP + 132, "serif_bold", 44, CLAY_LIGHT, 1, "ms", tracking=0.06)
    a2 = clamp((t - c.s("c4_2") - 1.0) / 0.5)
    draw_text(ctx, "约 500 名普通公民组成陪审团，审判哲学家苏格拉底", W / 2, SAFE_TOP + 186, "serif", 30, CLAY, a2, "ms")
    uy = SAFE_TOP + 330
    s = 0.82
    urns = win(t, c.s("c4_2") + 1.5, c.e("c4_9") + 1, 0.6, 0.3) * (1 - win(t, c.s("c4_3"), c.e("c4_5"), 0.4, 0.4))
    if urns > 0:
        ctx.push_group()
        for cx, lab in [(W / 2 - 215, "有罪"), (W / 2 + 215, "无罪")]:
            art.draw_urn(ctx, cx, uy, s, CLAY, scenes.POT_BLACK)
            draw_text(ctx, lab, cx, uy + 446 * s + 58, "serif_black", 44, CLAY_LIGHT, 1, "ms")
        # pebbles fall during the verdict
        pv = clamp((t - c.s("c4_6") + 0.3) / max(1.0, c.e("c4_6") - c.s("c4_6") + 0.8))
        rng = np.random.default_rng(12)
        for i in range(16):
            side = -1 if i % 9 < 5 else 1
            ph = clamp(pv * 2.2 - i * 0.07)
            if 0 < ph < 1:
                cx = W / 2 + side * 215 + rng.normal(0, 12)
                cy = uy - 160 + ph * 150
                set_color(ctx, "#EAD8BC", 0.95 * (1 - ph * 0.3))
                ctx.arc(cx, cy, 8, 0, 2 * math.pi)
                ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(urns)
    # charges
    k3 = win(t, c.s("c4_3"), c.e("c4_3"), 0.4, 0.35)
    if k3 > 0:
        card(ctx, 140, 560, W - 280, 300, k3, fill="#1C120D", stroke=CLAY, lw=3)
        draw_text(ctx, "罪名", W / 2, 640, "serif_black", 44, CLAY_LIGHT, k3, "ms")
        draw_text(ctx, "不敬城邦的神", W / 2, 730, "serif_bold", 46, "#F3E1C2", k3, "ms")
        draw_text(ctx, "败坏青年", W / 2, 800, "serif_bold", 46, "#F3E1C2", k3, "ms")
    k4 = win(t, c.s("c4_4"), c.e("c4_4"), 0.4, 0.35)
    if k4 > 0:
        _figure(ctx, 260, 830, 2.2, CLAY_LIGHT, k4)
        for i, (q, yy) in enumerate([("你说的“美德”到底是什么？", 600), ("你确定你懂吗？", 760)]):
            a = clamp((t - c.s("c4_4") - 1.0 - i * 1.2) / 0.4) * k4
            card(ctx, 430, yy - 60, 560, 100, a, fill="#1C120D", stroke=CLAY, lw=2.5)
            draw_text(ctx, q, 710, yy + 4, "serif_bold", 36, "#F3E1C2", a, "mm")
    k5 = win(t, c.s("c4_5"), c.e("c4_5"), 0.4, 0.35)
    if k5 > 0:
        # one rumour reaching many listeners: not independent
        src = (W / 2, 520)
        set_color(ctx, RED, 0.9 * k5)
        ctx.arc(*src, 18, 0, 2 * math.pi)
        ctx.fill()
        draw_text(ctx, "同一套坏话", W / 2, 470, "serif_bold", 32, CLAY_LIGHT, k5, "ms")
        prog = clamp((t - c.s("c4_5")) / max(0.5, c.e("c4_5") - c.s("c4_5")))
        for i in range(24):
            fx = 150 + (i % 8) * 112
            fy = 780 + (i // 8) * 150
            pa = clamp(prog * 2 - i / 24)
            set_color(ctx, CLAY, 0.35 * k5 * pa)
            ctx.set_line_width(1.5)
            ctx.move_to(*src)
            ctx.line_to(fx, fy - 90)
            ctx.stroke()
            _figure(ctx, fx, fy, 0.7, CLAY if pa < 1 else RED, k5)
    k7 = win(t, c.s("c4_7"), c.e("c4_7") + 0.2, 0.4, 0.4)
    if k7 > 0:
        draw_text(ctx, "差 30 票", W / 2, 1125, "serif_black", 120, "#F3E1C2", k7, "ms", glow=18, glow_color=CLAY,
                  glow_alpha=0.5)
        draw_text(ctx, "“只要再有三十票投到另一边，我就被判无罪了。” —— 柏拉图《申辩篇》", W / 2, 1195, "serif", 25,
                  CLAY_LIGHT, k7, "ms")
    k8 = win(t, c.s("c4_8"), c.e("c4_8"), 0.4, 0.4)
    if k8 > 0:
        card(ctx, 100, 1048, W - 200, 170, k8, fill="#1C120D", stroke=RED, lw=3)
        draw_text(ctx, "第二轮：死刑", W / 2, 1110, "serif_black", 46, "#F3E1C2", k8, "ms")
        draw_text(ctx, "比刚才投有罪的还多了 80 票（据第欧根尼·拉尔修）", W / 2, 1175, "serif", 27, CLAY_LIGHT, k8, "ms")
    point_card(ctx, t, c.s("c4_9"), c.e("c4_9"), ["一群人也会犯糊涂", ("多数，不等于正确", CLAY_LIGHT)], CLAY_LIGHT)
    chapter_flash(ctx, t, c.seg.start, "雅典", "公元前 399 年", CLAY_LIGHT)


RENDERERS = {"photocopy": photocopy, "twoills": twoills, "plymouth": plymouth, "athens": athens}
