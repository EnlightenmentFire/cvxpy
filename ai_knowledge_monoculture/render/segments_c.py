"""Segments: AI era, the old answer (1788) + today's remedies, ending + end card."""
import math

import cairo
import numpy as np

import art
import scenes
from engine import (CYAN, GREY, H, ORANGE, RED, SAFE_TOP, W, WHITE, clamp, draw_chapter_tag, draw_series_tag,
                    draw_text, ease_back, ease_in_out, ease_out, hexrgb, lerp, rounded_rect, set_color, wrap)
from segments_a import group
from widgets import (arrow, big_lines, card, chapter_flash, icon_brake, icon_building, icon_clock, icon_doc,
                     icon_leaf, icon_model, icon_person, label_box, point_card, quote_card, rise, win)

ENDCARD_NEXT = "下一期，我们接着聊 AI 里的老道理"


# ============================================================================ AI era
def _reason_card(ctx, idx, title, sub, y, alpha, accent):
    card(ctx, 70, y, W - 140, 190, alpha, stroke=accent)
    rounded_rect(ctx, 100, y + 40, 110, 110, 55)
    set_color(ctx, accent, 0.2 * alpha)
    ctx.fill()
    draw_text(ctx, str(idx), 155, y + 98, "sans_black", 64, accent, alpha, "mm")
    draw_text(ctx, title, 240, y + 82, "sans_black", 40, WHITE, alpha, "ls")
    draw_text(ctx, sub, 240, y + 140, "sans_medium", 30, GREY, alpha, "ls")


def aiera(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_chapter_tag(ctx, "AI 时代")
    draw_series_tag(ctx)
    k1 = win(t, c.s("c9_1"), c.e("c9_5") + 0.2, 0.4, 0.4)
    if k1 > 0:
        ctx.push_group()
        draw_text(ctx, "为什么在 AI 时代特别要命？", W / 2, 420, "sans_black", 50, WHITE, 1, "ms")
        rs = [("c9_3", "模型吃自己吐出来的东西", "网上越来越多文字是 AI 写的", ORANGE),
              ("c9_4", "大家用同一个底层模型", "全城的医院用同一台化验机", CYAN),
              ("c9_5", "机器反应以毫秒计", "人根本来不及插手", RED)]
        for i, (lid, ti, sub, acc) in enumerate(rs):
            a = clamp((t - c.s(lid)) / 0.4)
            if a > 0:
                k, dy = rise(t, c.s(lid), 0.45, 40)
                _reason_card(ctx, i + 1, ti, sub, 520 + i * 230 + dy, a, acc)
        # small callbacks
        if t >= c.s("c9_3"):
            a = win(t, c.s("c9_3") + 1.2, c.e("c9_3"), 0.3, 0.3)
            if a > 0:
                ctx.save()
                ctx.translate(880, 560)
                ctx.scale(0.35, 0.35)
                art.draw_pixel_rabbit(ctx, 0, 0, 12, art.TAIL_COLORS[int(t * 3) % 5])
                ctx.restore()
        if t >= c.s("c9_4"):
            a = clamp((t - c.s("c9_4") - (c.e("c9_4") - c.s("c9_4")) * 0.75) / 0.4)
            if a > 0:
                label_box(ctx, "算法单一化", 820, 790, 30, CYAN, alpha=a)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k1)
    k6 = win(t, c.s("c9_6"), c.e("c9_8"), 0.4, 0.35)
    if k6 > 0:
        ctx.push_group()
        label_box(ctx, "2021 · 《美国国家科学院院刊》", W / 2, 420, 34, WHITE)
        p7 = clamp((t - c.s("c9_7")) / 0.6)
        cy_alg = 760
        for i in range(5):
            bx = 150 + i * 195
            icon_building(ctx, bx, 560, 1.0, WHITE, 1)
            if p7 > 0:
                arrow(ctx, bx, 630, lerp(bx, W / 2, 0.85), cy_alg - 60, CYAN, p7 * 0.8, 3)
        if p7 > 0:
            icon_model(ctx, W / 2, cy_alg, 1.0, CYAN, p7, label="同一个算法")
            draw_text(ctx, "哪怕它单独看更准：所有公司加起来的决定，质量反而可能变差", W / 2, 940, "sans_bold", 30, WHITE,
                      clamp((t - c.s("c9_7") - 2.0) / 0.5), "ms")
        p8 = clamp((t - c.s("c9_8")) / 0.6)
        if p8 > 0:
            icon_person(ctx, W / 2, 1120, 1.6, WHITE, p8)
            for i in range(5):
                bx = 150 + i * 195
                a = clamp((t - c.s("c9_8") - 0.4 - i * 0.25) / 0.3)
                draw_text(ctx, "✕", bx, 1090, "sans_black", 46, RED, a, "ms")
            draw_text(ctx, "被它看走眼的人，可能走到哪家都被拒", W / 2, 1250, "sans_bold", 32, "#FF8A8D", p8, "ms")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k6)
    k9 = win(t, c.s("c9_9"), c.e("c9_10"), 0.4, 0.35)
    if k9 > 0:
        ctx.push_group()
        label_box(ctx, "2024 · 让大模型给新闻摘要打分", W / 2, 420, 34, WHITE)
        icon_model(ctx, W / 2, 620, 1.2, ORANGE, 1, label="打分的模型")
        p = clamp((t - c.s("c9_10")) / max(1, c.e("c9_10") - c.s("c9_10")))
        for i, (lab, own, x) in enumerate([("自己写的", True, 300), ("别人写的", False, 780)]):
            icon_doc(ctx, x - 45, 790, 1.0, ORANGE if own else WHITE, 1)
            draw_text(ctx, lab, x, 950, "sans_bold", 32, ORANGE if own else WHITE, 1, "ms")
            hbar = (190 if own else 130) * clamp(p * 1.8)
            set_color(ctx, ORANGE if own else GREY, 0.9)
            ctx.rectangle(x - 50, 1180 - hbar, 100, hbar)
            ctx.fill()
        draw_text(ctx, "它给的分（示意）", W / 2, 1150, "sans", 26, GREY, clamp(p * 2), "ms")
        a2 = clamp((p - 0.6) / 0.2)
        if a2 > 0:
            label_box(ctx, "在人看来：两篇差不多", W / 2, 1265, 32, WHITE, alpha=a2)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(k9)
    point_card(ctx, t, c.s("c9_11"), c.e("c9_11"), ["让模型给同类当裁判", ("就像让人审自己的案子", ORANGE)], ORANGE)
    chapter_flash(ctx, t, c.seg.start, "AI 时代", "两种老毛病，同时发作", CYAN)


# ============================================================================ the old answer: 1788
QI = scenes.QUILL_INK
RED_INK = "#6B2B12"


def _quote(ctx, en_lines, zh, y, a, size=58, zh_size=46):
    for ln in en_lines:
        draw_text(ctx, ln, W / 2, y, "fell_italic", size, QI, a, "ms")
        y += size * 1.3
    draw_text(ctx, zh, W / 2, y + 36, "serif_bold", zh_size, RED_INK, a, "ms")


def _parchment_part(ctx, t, c):
    scenes.parchment_backdrop(ctx)
    k1 = win(t, c.s("c10_1") - 0.3, c.e("c10_1"), 0.5, 0.4)
    if k1 > 0:
        draw_text(ctx, "两百多年前", W / 2, 760, "serif_black", 84, QI, k1, "ms")
    head = clamp((t - c.s("c10_2")) / 0.6)
    if head > 0:
        draw_text(ctx, "THE FEDERALIST", W / 2, SAFE_TOP + 90, "fell_sc", 64, QI, head, "ms", tracking=0.06)
        draw_text(ctx, "1788 · 报纸连载 · 《联邦党人文集》", W / 2, SAFE_TOP + 150, "serif_medium", 32, QI, head, "ms")
        set_color(ctx, QI, 0.8 * head)
        ctx.set_line_width(1.5)
        for dy in (176, 182):
            ctx.move_to(W / 2 - 280, SAFE_TOP + dy)
            ctx.line_to(W / 2 + 280, SAFE_TOP + dy)
        ctx.stroke()
    k2 = win(t, c.s("c10_2"), c.e("c10_2"), 0.4, 0.35)
    if k2 > 0:
        draw_text(ctx, "美国建国时，一批讨论", W / 2, 700, "serif_bold", 52, QI, k2, "ms")
        draw_text(ctx, "“规矩该怎么立”的文章", W / 2, 790, "serif_bold", 52, QI, k2, "ms")
    k3 = win(t, c.s("c10_3"), c.e("c10_3"), 0.4, 0.35)
    if k3 > 0:
        draw_text(ctx, "No. 51", W / 2, 560, "fell", 44, QI, k3, "ms")
        _quote(ctx, ["“If men were angels, no", "government would be necessary.”"], "如果人都是天使，就不需要政府了。", 700, k3)
    k4 = win(t, c.s("c10_4"), c.e("c10_5"), 0.4, 0.35)
    if k4 > 0:
        draw_text(ctx, "No. 51", W / 2, 560, "fell", 44, QI, k4, "ms")
        _quote(ctx, ["“Ambition must be made", "to counteract ambition.”"], "要用野心，去对抗野心。", 700, k4, 64, 52)
        k5 = clamp((t - c.s("c10_5")) / 0.5) * k4
        if k5 > 0:
            # two weights pushing against each other
            for sgn in (-1, 1):
                x = W / 2 + sgn * 170
                set_color(ctx, QI, k5)
                ctx.set_line_width(3)
                ctx.rectangle(x - 70, 1060, 140, 110)
                ctx.stroke()
                arrow(ctx, x + sgn * 90, 1115, x + sgn * 20 - sgn * 10, 1115, QI, k5, 4)
            draw_text(ctx, "互相牵制", W / 2, 1240, "serif_black", 44, RED_INK, k5, "ms")
    k6 = win(t, c.s("c10_6"), c.e("c10_7"), 0.4, 0.35)
    if k6 > 0:
        draw_text(ctx, "No. 55", W / 2, 560, "fell", 44, QI, k6, "ms")
        _quote(ctx, ["“Had every Athenian citizen been", "a Socrates, every Athenian", "assembly would still have", "been a mob.”"],
               "", 680, k6, 54)
        draw_text(ctx, "就算每个雅典公民都是苏格拉底，", W / 2, 1010, "serif_bold", 42, RED_INK, k6, "ms")
        draw_text(ctx, "每次公民大会也仍是乌合之众。", W / 2, 1070, "serif_bold", 42, RED_INK, k6, "ms")
        a7 = clamp((t - c.s("c10_7")) / 0.4) * k6
        draw_text(ctx, "第 51、55 篇，一般认为出自麦迪逊之手", W / 2, 1180, "serif", 32, QI, a7, "ms")
    k8 = win(t, c.s("c10_8"), c.e("c10_8"), 0.4, 0.5)
    if k8 > 0:
        span = max(1, c.e("c10_8") - c.s("c10_8"))
        rows = [("不信一个人", QI, 0.0), ("也不信一群人", QI, 0.22), ("信：让不同的力量互相牵制", RED_INK, 0.5)]
        for i, (txt, col, d) in enumerate(rows):
            a = clamp((t - c.s("c10_8") - span * d) / 0.4) * k8
            draw_text(ctx, txt, W / 2, 640 + i * 150, "serif_black", 60 if i < 2 else 54, col, a, "ms")
    art.draw_quill(ctx, W - 230, 1270, 1.0, angle=-0.75, alpha=head)


def _remedy(ctx, i, title, sub, x, y, a, icon):
    card(ctx, x, y, 450, 300, a, stroke=CYAN if i % 2 == 0 else ORANGE)
    icon(ctx, x + 225, y + 95, a)
    draw_text(ctx, title, x + 225, y + 210, "sans_black", 34, WHITE, a, "ms")
    draw_text(ctx, sub, x + 225, y + 260, "sans", 25, GREY, a, "ms")


def _today_part(ctx, t, c):
    scenes.tech_backdrop(ctx)
    draw_text(ctx, "今天的 AI：几乎是同一个思路", W / 2, 420, "sans_black", 48, WHITE, clamp((t - c.s("c10_9")) / 0.5), "ms")
    items = [
        ("c10_10", "保留真实数据", "标清哪些是机器写的", lambda cx, x, y, a: icon_leaf(cx, x, y, 0.9, a)),
        ("c10_11", "不同模型互相检查", "不让一个模型自己查自己",
         lambda cx, x, y, a: (icon_model(cx, x - 55, y, 0.45, CYAN, a, label=None),
                              icon_model(cx, x + 55, y, 0.45, ORANGE, a, label=None))),
        ("c10_12", "关键处留一个人", "重要决定由人复核", lambda cx, x, y, a: icon_person(cx, x, y + 10, 1.5, WHITE, a)),
        ("c10_13", "装上熔断", "跑太快时先停一停", lambda cx, x, y, a: icon_brake(cx, x, y, 48, CYAN, a)),
    ]
    for i, (lid, ti, sub, ic) in enumerate(items):
        a = clamp((t - c.s(lid)) / 0.45)
        if a <= 0:
            continue
        k, dy = rise(t, c.s(lid), 0.45, 40)
        x = 70 + (i % 2) * 490
        y = 520 + (i // 2) * 340 + dy
        _remedy(ctx, i, ti, sub, x, y, a, ic)


def federalist(ctx, t, c):
    split = c.s("c10_9") - 0.2
    if t < split + 0.6:
        group(ctx, 1 - clamp((t - split) / 0.6), _parchment_part, t, c)
    if t > split:
        group(ctx, clamp((t - split) / 0.6), _today_part, t, c)
    # climax: the summary card, then the music is left alone for a moment
    t14, e14 = c.s("c10_14"), c.e("c10_14")
    a = win(t, t14, e14 + 2.2, 0.5, 0.6)
    if a > 0:
        set_color(ctx, "#03060B", 0.82 * a)
        ctx.paint()
        draw_text(ctx, "这说明什么", W / 2, 560, "sans_bold", 40, CYAN, a, "ms")
        draw_text(ctx, "老办法没有过时", W / 2, 680, "sans_black", 70, WHITE, a, "ms", glow=14, glow_alpha=0.3)
        words = [("多样", ORANGE), ("独立", ORANGE), ("互相检查", WHITE), ("留刹车", CYAN), ("留真实", "#9BE3A6")]
        span = max(1, e14 - t14)
        for i, (wd, col) in enumerate(words):
            ai = clamp((t - t14 - span * (0.35 + 0.12 * i)) / 0.35) * a
            draw_text(ctx, wd, W / 2, 830 + i * 92, "sans_black", 58, col, ai, "ms", glow=12, glow_alpha=0.3)
    if t < c.s("c10_9"):
        draw_chapter_tag(ctx, "老人的答案 · 1788", color="#5A4A30", accent="#6B2B12")
    else:
        draw_chapter_tag(ctx, "今天的办法")
        draw_series_tag(ctx)
    chapter_flash(ctx, t, c.seg.start, "老人的答案", "1788 · 美国建国时的一批文章", "#C0822F", light=True)


# ============================================================================ ending + end card
def ending(ctx, t, c):
    rot = (t - c.seg.start) * 0.18
    lines = [("好的规矩，不指望出一个圣人", WHITE), ("也不指望人人都是圣人", WHITE),
             ("不指望一个完美的模型", WHITE), ("让许多不一样的东西互相盯着", WHITE), ("永远给真实世界留一个位子", "#9BE3A6")]
    s1, e1 = c.s("c11_1"), c.e("c11_1")
    s2, s3, e3 = c.s("c11_2"), c.s("c11_3"), c.e("c11_3")
    times = [s1, s1 + (e1 - s1) * 0.5, s2, s3, s3 + (e3 - s3) * 0.55]
    alphas = [clamp((t - tt) / 0.5) for tt in times]
    leaf = clamp((t - times[4]) / 0.6)
    ctx.push_group()
    scenes.scene_gears(ctx, t, rot=rot, leaf=leaf, lines=None)
    yy = 1300
    # show at most three lines at a time, newest at the bottom
    vis = [i for i in range(5) if alphas[i] > 0]
    vis = vis[-3:]
    for j, i in enumerate(vis):
        draw_text(ctx, lines[i][0], W / 2, 1290 + j * 72, "sans_bold", 44, lines[i][1], alphas[i], "ms", shadow=6)
    ctx.pop_group_to_source()
    end_t = e3 + 1.0
    fade_out = clamp((t - end_t) / 0.8)
    ctx.paint_with_alpha(1 - fade_out)
    if t > end_t:
        a = clamp((t - end_t - 0.3) / 0.6) * (1 - clamp((t - (c.seg.end - 2.4)) / 1.0))   # ~1.4 s of black + music tail
        set_color(ctx, "#03060B", 1)
        ctx.paint_with_alpha(fade_out)
        draw_text(ctx, "AI 知识", W / 2, 760, "sans_bold", 44, GREY, a, "ms", tracking=0.3)
        draw_text(ctx, "防暴君，", W / 2, 900, "sans_black", 86, CYAN, a, "ms", glow=16, glow_alpha=0.35)
        draw_text(ctx, "也防暴民", W / 2, 1010, "sans_black", 86, ORANGE, a, "ms", glow=16, glow_alpha=0.35)
        draw_text(ctx, ENDCARD_NEXT, W / 2, 1150, "sans", 30, GREY, a, "ms")


RENDERERS = {"aiera": aiera, "federalist": federalist, "ending": ending}
