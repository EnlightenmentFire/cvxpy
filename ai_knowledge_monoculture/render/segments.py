"""Animated segment renderers driven by the timeline (cue = sentence start/end times)."""
import math

import cairo
import numpy as np

import art
import scenes
from engine import (CYAN, GREY, H, ORANGE, SAFE_TOP, W, WHITE, clamp, draw_text, ease_in_out, ease_out, fade,
                    fill_bg, rounded_rect, set_color, wrap)


class Cues:
    """Helper: times of sentences inside a segment."""

    def __init__(self, seg, evmap):
        self.seg = seg
        self.ev = evmap

    def s(self, lid):
        return self.ev[lid].start

    def e(self, lid):
        return self.ev[lid].end

    def prog(self, t, lid, a=0.0, b=1.0):
        """0..1 progress through sentence lid (optionally a sub-range a..b of it)."""
        s, e = self.s(lid), self.e(lid)
        s2, e2 = s + (e - s) * a, s + (e - s) * b
        return clamp((t - s2) / max(1e-3, e2 - s2))


# ============================================================================ cold open
GEN9_PREFIX = "architecture. In addition to being home to some of the world's largest populations of "


def coldopen(ctx, t, cues):
    c = cues
    x0, y0, w0, h0 = scenes.TERM
    fill_bg(ctx, "#020408", "#05080E")
    set_color(ctx, "#000000", 0.18)
    for yy in range(0, H, 4):
        ctx.rectangle(0, yy, W, 1)
    ctx.fill()
    # ---- phase A: the terminal (until c0_7 starts)
    t_card = c.s("c0_7")
    term_out = ease_in_out(clamp((t - t_card + 0.2) / 0.7))
    if term_out < 1:
        ctx.save()
        sc = 1 - 0.12 * term_out
        ctx.translate(W / 2, y0 + h0 / 2)
        ctx.scale(sc, sc)
        ctx.translate(-W / 2, -(y0 + h0 / 2))
        a = (1 - term_out) * ease_out(t / 0.5)
        ctx.push_group()
        scenes.terminal_frame(ctx, x0, y0, w0, h0, "recursive_training.log")
        draw_text(ctx, "《自然》2024 年 7 月 · 一个小语言模型，用自己写的文字训练下一代", x0 + 36, y0 + 104, "sans", 25,
                  GREY, 1.0, "ls")
        ctx.save()
        ctx.rectangle(x0 + 2, y0 + 130, w0 - 4, h0 - 190)
        ctx.clip()
        # which generation blocks, typed how far
        blocks = []
        g0_t0, g0_t1 = c.s("c0_1") + 0.3, c.e("c0_2")
        g1_t0, g1_t1 = c.s("c0_3"), c.e("c0_3") - 0.2
        g5_t0, g5_t1 = c.s("c0_4"), c.e("c0_4") + 0.1
        g9_t0 = c.s("c0_5")
        rob = c.ev.get("c0_robot")
        g9_mid = rob.start if rob else c.e("c0_5") + 0.3
        g9_t1 = (rob.end - 0.15) if rob else g9_mid + 5
        en9 = scenes.GEN_TEXT[9][0]

        def typed(text, ta, tb):
            return int(len(text) * clamp((t - ta) / max(0.1, tb - ta)))

        if t >= g0_t0:
            blocks.append((0, typed(scenes.GEN_TEXT[0][0], g0_t0, g0_t1), t >= g0_t1))
        if t >= g1_t0:
            blocks.append((1, typed(scenes.GEN_TEXT[1][0], g1_t0, g1_t1), t >= g1_t1))
        if t >= g5_t0:
            blocks.append((5, typed(scenes.GEN_TEXT[5][0], g5_t0, g5_t1), t >= g5_t1))
        if t >= g9_t0:
            if t < g9_mid:
                n9 = int(len(GEN9_PREFIX) * clamp((t - g9_t0) / max(0.1, g9_mid - g9_t0)))
            else:
                n9 = len(GEN9_PREFIX) + int((len(en9) - len(GEN9_PREFIX)) * clamp((t - g9_mid) / max(0.1, g9_t1 - g9_mid)))
            blocks.append((9, n9, t >= g9_t1))
        # layout with scrolling: measure heights
        heights = []
        for g, n, done in blocks:
            en, zh = scenes.GEN_TEXT[g]
            nl = len(wrap(en, "mono", 27, w0 - 72))
            nz = len(wrap(zh, "sans", 25, w0 - 72))
            heights.append(46 + nl * 27 * 1.42 + 6 + nz * 25 * 1.5 + 26)
        visible_h = h0 - 230
        total = sum(heights)
        flood_t0 = (rob.end - 0.6) if rob else g9_t1
        flood = clamp((t - flood_t0) / 1.2)
        want = max(0.0, total - visible_h + (420 * flood))
        yy = y0 + 172 - want
        for (g, n, done), hgt in zip(blocks, heights):
            older = g != blocks[-1][0]
            draw_gen_typing(ctx, g, x0 + 36, yy, w0 - 72, n, done, older)
            yy += hgt
        if flood > 0:
            scenes.rabbit_flood(ctx, x0 + 36, yy, w0, int(3 + 14 * flood), t - flood_t0, alpha=flood)
        ctx.restore()
        set_color(ctx, "#060A10")
        ctx.rectangle(x0 + 2, y0 + h0 - 58, w0 - 4, 50)
        ctx.fill()
        if t > g9_t0:
            draw_text(ctx, "注：原文写作 black @-@ tailed，“@-@”是数据集里连字符的写法，此处去掉。", x0 + 36, y0 + h0 - 24,
                      "sans", 21, "#5D6B7C", 1.0, "ls")
        # the rabbit pops at the end of the machine reading
        pop_t = rob.end + 0.05 if rob else g9_t1
        if t >= pop_t:
            pop = clamp((t - pop_t) / 0.45)
            # tail colour cycles with the words of c0_6
            tail = 4
            if t >= c.s("c0_6"):
                k = int(clamp((t - c.s("c0_6")) / max(0.1, c.e("c0_6") - c.s("c0_6"))) * 6)
                tail = [0, 1, 2, 3, 4, 4][min(5, k)]
            scenes.draw_rabbit_pop(ctx, W / 2 + 160, y0 + h0 - 150, 15, pop, tail)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        ctx.restore()
    # ---- phase B: the paper card (c0_7) and the thesis (c0_8, c0_9)
    if t >= t_card - 0.1:
        k = ease_out(clamp((t - t_card) / 0.6)) * (1 - clamp((t - c.s("c0_8")) / 0.5))
        if k > 0:
            paper_card(ctx, k)
        th = clamp((t - c.s("c0_8") + 0.1) / 0.5)
        if th > 0 and t < c.e("c0_9") + 0.4:
            thesis(ctx, t, c, th)
        # title card
        tt0 = c.e("c0_9") + 0.35
        if t >= tt0:
            title_card(ctx, t - tt0)


def draw_gen_typing(ctx, g, x, y, w, n, done, older):
    en, zh = scenes.GEN_TEXT[g]
    col = ORANGE if g == 9 else CYAN
    alpha = 0.38 if older else 1.0
    draw_text(ctx, f"第 {g} 代", x, y, "sans_bold", 26, col, alpha, "ls")
    lines = wrap(en, "mono", 27, w)
    yy = y + 46
    left = n
    caret_drawn = False
    for ln in lines:
        shown = ln[:max(0, left)]
        if shown:
            adv = draw_text(ctx, shown, x, yy, "mono", 27, "#D7DEE6" if not older else "#AAB4C0", alpha, "ls")
        else:
            adv = 0
        if not done and not caret_drawn and left <= len(ln):
            set_color(ctx, CYAN, alpha)
            ctx.rectangle(x + adv + 3, yy - 22, 15, 26)
            ctx.fill()
            caret_drawn = True
        left -= len(ln) + 1
        yy += 27 * 1.42
    if done:
        yy += 6
        for ln in wrap(zh, "sans", 25, w):
            draw_text(ctx, ln, x, yy, "sans", 25, "#7F8C9C", alpha, "ls")
            yy += 25 * 1.5


def paper_card(ctx, k):
    cx, cy = W / 2, 760
    wcard, hcard = 900, 560
    y = cy - hcard / 2 + (1 - k) * 60
    rounded_rect(ctx, cx - wcard / 2, y, wcard, hcard, 24)
    set_color(ctx, "#F4F1EA", k)
    ctx.fill()
    draw_text(ctx, "期刊论文", cx - wcard / 2 + 60, y + 96, "sans_bold", 44, "#1A1A1A", k, "ls")
    draw_text(ctx, "《自然》第 631 卷 · 2024 年 7 月 24 日", cx - wcard / 2 + 60, y + 150, "sans", 26, "#555555", k, "ls")
    set_color(ctx, "#1A1A1A", 0.15 * k)
    ctx.rectangle(cx - wcard / 2 + 60, y + 178, wcard - 120, 2)
    ctx.fill()
    yy = y + 240
    for ln in ["AI models collapse when trained", "on recursively generated data"]:
        draw_text(ctx, ln, cx - wcard / 2 + 60, yy, "serif_bold", 42, "#111111", k, "ls")
        yy += 56
    draw_text(ctx, "用 AI 自己生成的数据反复训练，AI 模型会“崩溃”", cx - wcard / 2 + 60, yy + 30, "sans_medium", 32,
              "#C0392B", k, "ls")
    draw_text(ctx, "作者：Shumailov 等六人", cx - wcard / 2 + 60, yy + 90, "sans", 24, "#666666", k, "ls")


def thesis(ctx, t, c, k):
    a1 = clamp((t - c.s("c0_9") + 0.1) / 0.4)
    split = c.s("c0_9") + (c.e("c0_9") - c.s("c0_9")) * 0.47
    a2 = clamp((t - split) / 0.4)
    out = 1 - clamp((t - c.e("c0_9") - 0.1) / 0.3)
    draw_text(ctx, "人类花了两千多年才学会的道理", W / 2, 560, "sans_medium", 36, GREY, k * out, "ms")
    draw_text(ctx, "一个声音说了算，", W / 2, 760, "sans_black", 68, CYAN, a1 * out, "ms", glow=14, glow_alpha=0.35)
    draw_text(ctx, "很危险；", W / 2, 860, "sans_black", 68, CYAN, a1 * out, "ms", glow=14, glow_alpha=0.35)
    draw_text(ctx, "所有声音变成同一个声音，", W / 2, 1030, "sans_black", 60, ORANGE, a2 * out, "ms", glow=14,
              glow_alpha=0.35)
    draw_text(ctx, "也很危险。", W / 2, 1130, "sans_black", 60, ORANGE, a2 * out, "ms", glow=14, glow_alpha=0.35)


def title_card(ctx, lt):
    a = ease_out(clamp(lt / 0.5)) * (1 - clamp((lt - 2.7) / 0.4))
    if a <= 0:
        return
    set_color(ctx, "#03060B", a)
    ctx.paint()
    draw_text(ctx, "AI 知识", W / 2, 640, "sans_bold", 40, GREY, a, "ms", tracking=0.3)
    s = 1 + 0.04 * ease_out(clamp(lt / 3))
    ctx.save()
    ctx.translate(W / 2, 880)
    ctx.scale(s, s)
    draw_text(ctx, "防暴君，", 0, -10, "sans_black", 118, CYAN, a, "ms", glow=22, glow_alpha=0.45)
    draw_text(ctx, "也防暴民", 0, 150, "sans_black", 118, ORANGE, a, "ms", glow=22, glow_alpha=0.45)
    ctx.restore()
    set_color(ctx, GREY, 0.5 * a)
    ctx.rectangle(W / 2 - 160, 1110, 320, 2)
    ctx.fill()
    draw_text(ctx, "一个声音说了算很危险，所有声音变成一个声音也很危险", W / 2, 1170, "sans", 28, GREY, a, "ms")


# ============================================================================ registry
RENDERERS = {"coldopen": coldopen}

import segments_a  # noqa: E402

RENDERERS.update(segments_a.RENDERERS)

import segments_b  # noqa: E402
import segments_c  # noqa: E402

RENDERERS.update(segments_b.RENDERERS)
RENDERERS.update(segments_c.RENDERERS)
