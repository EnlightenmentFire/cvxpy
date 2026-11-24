"""Scene compositions. Each scene is draw(ctx, t, **state) on a 1080x1920 canvas.
For the style frames we call them at a representative moment; the full render drives the parameters."""
import math

import cairo
import numpy as np
from PIL import Image

import art
from engine import (CYAN, GREY, H, ORANGE, RED, SAFE_TOP, W, WHITE, clamp, draw_chapter_tag, draw_series_tag,
                    draw_subtitle, draw_text, ease_back, ease_out, fill_bg, hexrgb, overlay_grain, pil_to_surface,
                    rounded_rect, set_color, vignette, wrap)


# ---------------------------------------------------------------------------- common backdrop
def tech_backdrop(ctx, grid_alpha=0.05):
    fill_bg(ctx, "#04070D", "#0A1322")
    set_color(ctx, "#9FB3C8", grid_alpha)
    for y in range(SAFE_TOP + 20, 1330, 60):
        for x in range(60, W, 60):
            ctx.rectangle(x, y, 2, 2)
    ctx.fill()


# ============================================================================ S1 cold open: terminal + jackrabbits
GEN_TEXT = {
    0: ("Revival architecture such as St. John's Cathedral in London. The earliest surviving example of "
        "Perpendicular Revival architecture is found in the 18th-century Church of Our Lady of Guernsey…",
        "……复兴式建筑，比如伦敦的圣约翰大教堂。现存最早的垂直复兴式建筑……"),
    1: ("architecture such as St. Peter's Basilica in Rome or St. Peter's Basilica in Buenos Aires.",
        "……比如罗马的圣彼得大教堂，或者布宜诺斯艾利斯的圣彼得大教堂。"),
    5: ("ism, which had been translated into more than 100 languages including English, French, German, "
        "Italian, Spanish, Portuguese, Dutch, Swedish, Norwegian, Polish…",
        "……被翻译成一百多种语言，包括英语、法语、德语、意大利语、西班牙语……"),
    9: ("architecture. In addition to being home to some of the world's largest populations of black-tailed "
        "jackrabbits, white-tailed jackrabbits, blue-tailed jackrabbits, red-tailed jackrabbits, yellow-",
        "建筑。此外，这里还是世界上最大的黑尾长耳大野兔、白尾长耳大野兔、蓝尾长耳大野兔、红尾长耳大野兔、黄尾……的栖息地之一。"),
}
RABBIT_WORDS = [("black", "#9AA3AE"), ("white", "#F4F6F8"), ("blue", "#4D9CFF"), ("red", "#FF5A5F"),
                ("yellow", "#F5C542")]
TERM = (44, SAFE_TOP + 10, W - 88, 1100)


def terminal_frame(ctx, x, y, w, h, title, alpha=1.0):
    rounded_rect(ctx, x, y, w, h, 18)
    set_color(ctx, "#060A10", 0.96 * alpha)
    ctx.fill_preserve()
    set_color(ctx, "#22314A", alpha)
    ctx.set_line_width(2)
    ctx.stroke()
    rounded_rect(ctx, x, y, w, 58, 18)
    ctx.rectangle(x, y + 30, w, 28)
    set_color(ctx, "#0E1624", alpha)
    ctx.fill()
    for i, c in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        set_color(ctx, c, 0.85 * alpha)
        ctx.arc(x + 34 + i * 28, y + 29, 8, 0, 2 * math.pi)
        ctx.fill()
    draw_text(ctx, title, x + w / 2, y + 30, "mono", 24, GREY, alpha, "mm")


def draw_gen_block(ctx, gen, x, y, w, alpha=1.0, highlight=False, chars=None, en_size=27, zh_size=25, zh_alpha=1.0):
    """chars: number of English characters typed so far (None = all)."""
    en, zh = GEN_TEXT[gen]
    col = ORANGE if gen == 9 else CYAN
    draw_text(ctx, f"第 {gen} 代", x, y, "sans_bold", 26, col, alpha, "ls")
    lines = wrap(en, "mono", en_size, w)
    yy = y + 46
    left = len(en) if chars is None else chars
    for ln in lines:
        shown = ln[:max(0, left)]
        left -= len(ln) + 1
        if shown:
            adv = draw_text(ctx, shown, x, yy, "mono", en_size, "#D7DEE6" if highlight else "#AAB4C0", alpha, "ls")
            if 0 <= left < 1 and chars is not None:   # caret
                set_color(ctx, CYAN, alpha)
                ctx.rectangle(x + adv + 3, yy - en_size * 0.8, en_size * 0.55, en_size * 0.95)
                ctx.fill()
        yy += en_size * 1.42
    yy += 6
    for ln in wrap(zh, "sans", zh_size, w):
        draw_text(ctx, ln, x, yy, "sans", zh_size, "#7F8C9C", alpha * zh_alpha, "ls")
        yy += zh_size * 1.5
    return yy - y


def rabbit_flood(ctx, x0, y0, w, rows, t=0.0, alpha=1.0, seed=4):
    rng = np.random.default_rng(seed)
    offs = rng.uniform(0, 260, 40)
    for r in range(rows):
        xx = x0 - offs[r] - (t * 90 * (1 + (r % 3) * 0.4)) % 600
        ry = y0 + r * 44
        k = r % 5
        while xx < x0 + w:
            word, col = RABBIT_WORDS[k % 5]
            s = f"{word}-tailed jackrabbits, "
            adv = draw_text(ctx, s, xx, ry, "mono_bold" if k % 5 == 4 else "mono", 27, col,
                            alpha * (0.9 - 0.03 * r), "ls")
            xx += adv
            k += 1


def draw_rabbit_pop(ctx, cx, base_y, px=15, pop=1.0, tail_idx=4, glow=1.0):
    """Pixel jackrabbit with a dark spotlight and pixel sparkles. pop: 0..1 entrance."""
    rw, rh = len(art.RABBIT[0]) * px, len(art.RABBIT) * px
    s = ease_back(pop) if pop < 1 else 1.0
    cy = base_y - rh / 2
    g = cairo.RadialGradient(cx, cy, 10, cx, cy, 330)
    g.add_color_stop_rgba(0, 0.01, 0.02, 0.04, 0.92 * glow)
    g.add_color_stop_rgba(0.65, 0.01, 0.02, 0.04, 0.7 * glow)
    g.add_color_stop_rgba(1, 0.01, 0.02, 0.04, 0.0)
    ctx.set_source(g)
    ctx.arc(cx, cy, 330, 0, 2 * math.pi)
    ctx.fill()
    rng = np.random.default_rng(9)
    for i in range(18):
        a = i / 18 * 2 * math.pi + 0.2
        d = (200 + rng.uniform(0, 70)) * min(1, pop * 1.2)
        sz = rng.choice([8, 10, 12])
        col = art.TAIL_COLORS[i % 5]
        set_color(ctx, col if col != "#2A2A2A" else "#8A93A0", 0.85 * clamp(pop * 2))
        ctx.rectangle(cx + math.cos(a) * d - sz / 2, cy + math.sin(a) * d - sz / 2, sz, sz)
        ctx.fill()
    ctx.save()
    ctx.translate(cx, base_y)
    ctx.scale(s, s)
    art.draw_pixel_rabbit(ctx, -rw / 2, -rh, px, art.TAIL_COLORS[tail_idx])
    ctx.restore()


def scene_coldopen(ctx, t, gens_shown=(5, 9), typed9=None, flood=1.0, rabbit=1.0, tail_idx=4, sub=None):
    fill_bg(ctx, "#020408", "#05080E")
    set_color(ctx, "#000000", 0.18)
    for yy in range(0, H, 4):
        ctx.rectangle(0, yy, W, 1)
    ctx.fill()
    x0, y0, w0, h0 = TERM
    terminal_frame(ctx, x0, y0, w0, h0, "recursive_training.log")
    draw_text(ctx, "《自然》2024 年 7 月 · 一个小语言模型，用自己写的文字训练下一代", x0 + 36, y0 + 104, "sans", 25,
              GREY, 1.0, "ls")
    ctx.save()
    rounded_rect(ctx, x0 + 2, y0 + 130, w0 - 4, h0 - 190, 0)
    ctx.clip()
    yy = y0 + 172
    for g in gens_shown:
        if g == 9:
            hgt = draw_gen_block(ctx, 9, x0 + 36, yy, w0 - 72, 1.0, highlight=True, chars=typed9)
        else:
            hgt = draw_gen_block(ctx, g, x0 + 36, yy, w0 - 72, 0.35)
        yy += hgt + 26
    if flood > 0:
        rabbit_flood(ctx, x0 + 36, yy, w0, int(16 * flood), t)
    ctx.restore()
    set_color(ctx, "#060A10")
    ctx.rectangle(x0 + 2, y0 + h0 - 58, w0 - 4, 50)
    ctx.fill()
    draw_text(ctx, "注：原文写作 black @-@ tailed，“@-@”是数据集里连字符的写法，此处去掉。", x0 + 36, y0 + h0 - 24,
              "sans", 21, "#5D6B7C", 1.0, "ls")
    if rabbit > 0:
        draw_rabbit_pop(ctx, W / 2 + 160, y0 + h0 - 150, 15, rabbit, tail_idx)
    if sub:
        draw_subtitle(ctx, sub)


# ============================================================================ S2 photocopy + bell curve
_copy_cache = {}


def copy_surface(gen, w=290, h=368):
    key = (gen, w, h)
    if key not in _copy_cache:
        im = art.photocopy(art.church_painting(), gen)
        sheet = Image.new("RGB", (im.width + 40, im.height + 40), (236, 236, 230) if gen else (250, 248, 242))
        sheet.paste(im, (20, 20))
        sheet = sheet.resize((w, h), Image.Resampling.LANCZOS)
        _copy_cache[key] = pil_to_surface(sheet)
    return _copy_cache[key]


def bell(x, mu, sd):
    return np.exp(-0.5 * ((x - mu) / sd) ** 2)


def scene_photocopy(ctx, t, sub=None, gens=(0, 4, 9), collapse=1.0, show_tails=1.0):
    tech_backdrop(ctx)
    draw_chapter_tag(ctx, "复印件的复印件 · 模型崩溃")
    draw_series_tag(ctx)
    cw, ch = 292, 370
    xs = [44 + i * (cw + 37) for i in range(3)]
    ytop = SAFE_TOP + 110
    for i, g in enumerate(gens):
        x = xs[i]
        set_color(ctx, "#000000", 0.45)
        ctx.rectangle(x + 8, ytop + 10, cw, ch)
        ctx.fill()
        ctx.set_source_surface(copy_surface(g, cw, ch), x, ytop)
        ctx.paint()
        lab = "原图" if g == 0 else f"复印 {g} 次"
        draw_text(ctx, lab, x + cw / 2, ytop + ch + 48, "sans_bold", 30, WHITE if g == 0 else ORANGE, 1, "ms")
        if i < 2:
            ax = x + cw + 6
            set_color(ctx, GREY, 0.8)
            ctx.move_to(ax + 4, ytop + ch / 2)
            ctx.line_to(ax + 25, ytop + ch / 2 - 12)
            ctx.line_to(ax + 25, ytop + ch / 2 + 12)
            ctx.close_path()
            ctx.fill()
    # ----- bell curves
    gx0, gx1 = 90, W - 90
    gy_base = 1250
    gh = 300
    xs_ = np.linspace(-4, 4, 400)
    X = lambda xv: gx0 + (xv + 4) / 8 * (gx1 - gx0)

    def pts_for(sd, height):
        return [(X(xv), gy_base - yv) for xv, yv in zip(xs_, bell(xs_, 0, sd) * height)]

    sd0 = 1.25
    pts0 = pts_for(sd0, gh * 0.55)
    for side in (-1, 1):
        sel = [p for p, xv in zip(pts0, xs_) if side * xv > 1.9]
        if sel:
            ctx.new_path()
            ctx.move_to(sel[0][0], gy_base)
            for px, py in sel:
                ctx.line_to(px, py)
            ctx.line_to(sel[-1][0], gy_base)
            ctx.close_path()
            set_color(ctx, RED, 0.32 * show_tails)
            ctx.fill()
    ctx.new_path()
    for i, (px, py) in enumerate(pts0):
        (ctx.move_to if i == 0 else ctx.line_to)(px, py)
    set_color(ctx, WHITE, 0.85)
    ctx.set_line_width(3.5)
    ctx.set_dash([10, 8])
    ctx.stroke()
    ctx.set_dash([])
    stages = [(0.95, 0.68, 0.35), (0.7, 0.82, 0.55), (0.42, 1.0, 1.0)]
    for k, (sd, hh, a) in enumerate(stages):
        if collapse < (k + 1) / len(stages) - 1e-6:
            continue
        ctx.new_path()
        for i, (px, py) in enumerate(pts_for(sd, gh * hh)):
            (ctx.move_to if i == 0 else ctx.line_to)(px, py)
        set_color(ctx, ORANGE, a)
        ctx.set_line_width(4 if k == 2 else 3)
        ctx.stroke()
    set_color(ctx, GREY, 0.7)
    ctx.set_line_width(2)
    ctx.move_to(gx0, gy_base)
    ctx.line_to(gx1, gy_base)
    ctx.stroke()
    draw_text(ctx, "最常见", W / 2, gy_base + 44, "sans", 26, GREY, 1, "ms")
    draw_text(ctx, "少见", gx0 + 40, gy_base + 44, "sans", 26, GREY, 1, "ms")
    draw_text(ctx, "少见", gx1 - 40, gy_base + 44, "sans", 26, GREY, 1, "ms")
    # tail label
    draw_text(ctx, "尾巴：少见，但真实存在", gx0, 900, "sans_medium", 28, "#FF8A8D", show_tails, "ls")
    set_color(ctx, "#FF8A8D", 0.9 * show_tails)
    ctx.set_line_width(2)
    ctx.move_to(gx0 + 60, 914)
    ctx.line_to(X(-2.6), gy_base - 30)
    ctx.stroke()
    draw_text(ctx, "第 0 代", X(2.3), gy_base - 128, "sans", 26, WHITE, 0.9, "ls")
    if collapse >= 1:
        draw_text(ctx, "第 9 代", W / 2 + 60, gy_base - gh + 8, "sans_bold", 28, ORANGE, 1, "ls")
    for xv in (-2.0, 2.0):
        sx = X(xv)
        set_color(ctx, RED, 0.9 * show_tails)
        ctx.set_line_width(3)
        ctx.set_dash([6, 6])
        ctx.move_to(sx, gy_base - 150)
        ctx.line_to(sx, gy_base + 6)
        ctx.stroke()
        ctx.set_dash([])
        draw_text(ctx, "✂", sx, gy_base - 160, "sans", 40, "#FF8A8D", show_tails, "ms")
    if sub:
        draw_subtitle(ctx, sub)


# ============================================================================ S3 Plymouth 1906 (Victorian engraving)
# Galton (1907) "Vox Populi", Nature 75: estimates at each 5 degrees of the array (lb); 50 = median.
GALTON_PCT = [(0.05, 1074), (0.10, 1109), (0.15, 1126), (0.20, 1148), (0.25, 1162), (0.30, 1174),
              (0.35, 1181), (0.40, 1188), (0.45, 1197), (0.50, 1207), (0.55, 1214), (0.60, 1219), (0.65, 1225),
              (0.70, 1230), (0.75, 1236), (0.80, 1243), (0.85, 1254), (0.90, 1267), (0.95, 1293)]


def galton_estimates(n=787, seed=11):
    """787 values whose 5..95 percentiles follow Galton's printed table; the outer 5% tails
    (not printed by Galton) are extended smoothly for the illustration only."""
    rng = np.random.default_rng(seed)
    q = (np.arange(n) + 0.5) / n
    ps = [0.0] + [p for p, _ in GALTON_PCT] + [1.0]
    vs = [1005] + [v for _, v in GALTON_PCT] + [1350]
    vals = np.interp(q, ps, vs) + rng.normal(0, 1.0, n)
    rng.shuffle(vals)
    return vals


PAPER = "#EFE5CC"
INK = "#2B2117"
INK_RED = "#A8382A"
INK_BLUE = "#1F3D66"


def paper_backdrop(ctx, seed=2, base=PAPER, edge="#C9B68E"):
    set_color(ctx, base)
    ctx.paint()
    rng = np.random.default_rng(seed)
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(2, 18)
        set_color(ctx, "#B49A6A", rng.uniform(0.02, 0.06))
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()
    g = cairo.RadialGradient(W / 2, H * 0.42, H * 0.3, W / 2, H * 0.42, H * 0.78)
    g.add_color_stop_rgba(0, *hexrgb(edge)[:3], 0)
    g.add_color_stop_rgba(1, *hexrgb(edge)[:3], 0.85)
    ctx.set_source(g)
    ctx.paint()


def victorian_border(ctx, x, y, w, h, ink=INK):
    set_color(ctx, ink)
    ctx.set_line_width(4)
    ctx.rectangle(x, y, w, h)
    ctx.stroke()
    ctx.set_line_width(1.5)
    ctx.rectangle(x + 12, y + 12, w - 24, h - 24)
    ctx.stroke()
    for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
        ctx.arc(cx, cy, 14, 0, 2 * math.pi)
        set_color(ctx, PAPER)
        ctx.fill_preserve()
        set_color(ctx, ink)
        ctx.set_line_width(2.5)
        ctx.stroke()
        ctx.arc(cx, cy, 5, 0, 2 * math.pi)
        ctx.fill()


def scene_plymouth(ctx, t, sub=None, dots=1.0, lines=1.0, copying=0.0, show_ox=1.0):
    paper_backdrop(ctx)
    victorian_border(ctx, 40, SAFE_TOP - 10, W - 80, 1140)
    draw_text(ctx, "VOX POPULI", W / 2, SAFE_TOP + 92, "fell", 84, INK, 1, "ms", tracking=0.08)
    draw_text(ctx, "人民的声音 · 高尔顿，《自然》1907 年 3 月", W / 2, SAFE_TOP + 146, "serif_medium", 30, INK, 0.9, "ms")
    set_color(ctx, INK)
    ctx.set_line_width(1.5)
    ctx.move_to(W / 2 - 300, SAFE_TOP + 170)
    ctx.line_to(W / 2 + 300, SAFE_TOP + 170)
    ctx.stroke()
    draw_text(ctx, "Plymouth · 1906 · West of England Fat Stock and Poultry Exhibition", W / 2, SAFE_TOP + 204,
              "fell_italic", 27, INK, 0.85, "ms")
    if show_ox > 0:
        art.draw_ox_engraving(ctx, 200, SAFE_TOP + 215, 0.66)
    # ---- dot plot of 787 estimates
    vals = galton_estimates()
    lo, hi = 990, 1370
    ax0, ax1 = 100, W - 100
    base_y = 1215
    X = lambda v: ax0 + (v - lo) / (hi - lo) * (ax1 - ax0)
    binw = 5.0
    dot_r = 3.3
    counts = {}
    rng = np.random.default_rng(1)
    n_show = int(len(vals) * dots)
    order = np.argsort(rng.random(len(vals)))
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
    draw_text(ctx, "每个点是一张票（示意：按高尔顿公布的分位数绘制）", ax0, base_y - 300, "serif", 22, INK, 0.7, "ls")
    if lines > 0:
        for v, col, lab, dx, anchor, ly in [(1207, INK_RED, "中位数 1207", 12, "ls", base_y - 250),
                                            (1198, INK_BLUE, "实际 1198", -12, "rs", base_y - 250)]:
            set_color(ctx, col, lines)
            ctx.set_line_width(3)
            ctx.move_to(X(v), base_y - 270)
            ctx.line_to(X(v), base_y + 2)
            ctx.stroke()
            draw_text(ctx, lab, X(v) + dx, ly, "serif_bold", 30, col, lines, anchor)
        draw_text(ctx, "787 张有效票 · 只差 9 磅（0.8%）", W / 2, 1298, "serif_bold", 34, INK, lines, "ms")
    if sub:
        draw_subtitle(ctx, sub, band=True)


# ============================================================================ S4 Athens 399 BC (red-figure)
CLAY = "#C8643B"
CLAY_LIGHT = "#E59A6B"
POT_BLACK = "#120D0A"


def scene_athens(ctx, t, sub=None, pebbles=1.0, verdict=1.0):
    set_color(ctx, POT_BLACK)
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
    draw_text(ctx, "公元前 399 年 · 雅典", W / 2, SAFE_TOP + 132, "serif_bold", 44, CLAY_LIGHT, 1, "ms", tracking=0.06)
    draw_text(ctx, "约 500 名普通公民组成陪审团，审判哲学家苏格拉底", W / 2, SAFE_TOP + 186, "serif", 30, CLAY, 1, "ms")
    uy = SAFE_TOP + 330
    s = 0.82
    for cx, lab in [(W / 2 - 215, "有罪"), (W / 2 + 215, "无罪")]:
        art.draw_urn(ctx, cx, uy, s, CLAY, POT_BLACK)
        draw_text(ctx, lab, cx, uy + 446 * s + 58, "serif_black", 44, CLAY_LIGHT, 1, "ms")
    # pebbles dropping into the urns (between the caption and the urn mouths)
    k = int(14 * pebbles)
    for i in range(k):
        side = -1 if i % 9 < 5 else 1
        cx = W / 2 + side * 215 + rng.normal(0, 14)
        cy = uy - 22 - (i % 5) * 18 + rng.normal(0, 4)
        set_color(ctx, "#EAD8BC", 0.92)
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(1.0, 0.8)
        ctx.arc(0, 0, 8, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if verdict > 0:
        draw_text(ctx, "差 30 票", W / 2, 1125, "serif_black", 120, "#F3E1C2", verdict, "ms", glow=18,
                  glow_color=CLAY, glow_alpha=0.5)
        draw_text(ctx, "“只要再有三十票投到另一边，我就被判无罪了。”", W / 2, 1192, "serif", 29, CLAY_LIGHT, verdict, "ms")
        draw_text(ctx, "—— 苏格拉底，见柏拉图《申辩篇》", W / 2, 1236, "serif", 25, CLAY, verdict, "ms")
    if sub:
        draw_subtitle(ctx, sub)


# ============================================================================ S5 flash crash 2010-05-06
def flash_series():
    """Schematic DJIA path, % from prior close, 14:30-15:10. Anchors: indices already down >4% by 14:41;
    a further 5-6% fall to 14:45; DJIA low -9.16% at 14:47 (SEC chair testimony); most recovered by ~15:00."""
    pts = [(0, -2.6), (5, -3.1), (8, -3.6), (11, -4.2), (13, -4.8), (14.5, -6.0), (15.5, -7.6), (16.3, -8.6),
           (17, -9.16), (17.6, -8.3), (18.5, -7.0), (20, -6.1), (22, -5.5), (25, -5.0), (28, -4.6), (30, -4.4),
           (34, -4.1), (40, -3.9)]
    xs = np.linspace(0, 40, 400)
    ys = np.interp(xs, [p[0] for p in pts], [p[1] for p in pts])
    rng = np.random.default_rng(2)
    ys = ys + np.convolve(rng.normal(0, 0.09, len(xs)), np.ones(5) / 5, mode="same")
    return xs, ys


def scene_flash(ctx, t, sub=None, reveal=1.0, brake=1.0, potato=0.6):
    tech_backdrop(ctx)
    draw_chapter_tag(ctx, "闪电崩盘 · 2010 年 5 月 6 日", accent=ORANGE)
    draw_series_tag(ctx)
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
    xs, ys = flash_series()
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
    if reveal > 0.45:
        lx, ly = X(17), Y(-9.16)
        set_color(ctx, RED)
        ctx.arc(lx, ly, 9, 0, 2 * math.pi)
        ctx.fill()
        draw_text(ctx, "14:47 最低 −9.16%", lx + 22, ly + 10, "sans_bold", 28, "#FF8A8D", 1, "ls")
        draw_text(ctx, "比前一天收盘低了将近 1000 点", lx + 22, ly + 48, "sans", 24, "#FF8A8D", 0.9, "ls")
    bx = X(15.47)
    if brake > 0:
        set_color(ctx, CYAN, 0.9 * brake)
        ctx.set_line_width(3)
        ctx.set_dash([8, 6])
        ctx.move_to(bx, cy0)
        ctx.line_to(bx, cy1)
        ctx.stroke()
        ctx.set_dash([])
        draw_text(ctx, "14:45:28", bx - 10, cy0 + 24, "mono_bold", 22, CYAN, brake, "rs")
    # ---- hot potato ring
    ny0 = 1065
    draw_text(ctx, "“烫手山芋”：程序之间互相倒手", W / 2, ny0 - 175, "sans_bold", 34, WHITE, 1, "ms")
    draw_text(ctx, "“hot-potato” volume effect", W / 2, ny0 - 132, "serif", 26, GREY, 1, "ms")
    nodes = []
    for i in range(18):
        a = i / 18 * 2 * math.pi
        r = 300 + (i % 2) * 40
        nodes.append((W / 2 + r * math.cos(a), ny0 + 88 * math.sin(a)))
    path_idx = [0, 7, 3, 11, 5, 15, 9, 1, 13, 6, 16, 4]
    hop = potato * (len(path_idx) - 1)
    for k in range(min(len(path_idx) - 1, int(hop) + 1)):
        (x1, y1), (x2, y2) = nodes[path_idx[k]], nodes[path_idx[k + 1]]
        set_color(ctx, RED, 0.16 + 0.06 * k)
        ctx.set_line_width(2.5)
        ctx.move_to(x1, y1)
        ctx.curve_to(x1, y1 - 70, x2, y2 - 70, x2, y2)
        ctx.stroke()
    for (x, y) in nodes:
        rounded_rect(ctx, x - 22, y - 22, 44, 44, 8)
        set_color(ctx, ORANGE, 0.18)
        ctx.fill_preserve()
        set_color(ctx, ORANGE, 0.9)
        ctx.set_line_width(2.5)
        ctx.stroke()
    k = min(len(path_idx) - 2, int(hop))
    f = hop - int(hop)
    (x1, y1), (x2, y2) = nodes[path_idx[k]], nodes[path_idx[k + 1]]
    tt = f
    hx = (1 - tt) ** 3 * x1 + 3 * (1 - tt) ** 2 * tt * x1 + 3 * (1 - tt) * tt ** 2 * x2 + tt ** 3 * x2
    hy = (1 - tt) ** 3 * y1 + 3 * (1 - tt) ** 2 * tt * (y1 - 70) + 3 * (1 - tt) * tt ** 2 * (y2 - 70) + tt ** 3 * y2
    for r, a in [(40, 0.12), (26, 0.25), (15, 1.0)]:
        set_color(ctx, RED, a)
        ctx.arc(hx, hy, r, 0, 2 * math.pi)
        ctx.fill()
    draw_text(ctx, "14 秒倒手 27,000 多份合约，净买进只有约 200 份", W / 2, ny0 + 160, "sans_medium", 30, ORANGE, 1, "ms")
    if brake > 0:
        bx, by = W / 2, ny0
        rounded_rect(ctx, bx - 125, by - 46, 250, 92, 46)
        set_color(ctx, "#06101A", 0.94 * brake)
        ctx.fill_preserve()
        set_color(ctx, CYAN, brake)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.rectangle(bx - 86, by - 20, 12, 40)
        ctx.rectangle(bx - 66, by - 20, 12, 40)
        ctx.fill()
        draw_text(ctx, "暂停 5 秒", bx - 40, by + 2, "sans_black", 38, CYAN, brake, "lm")
    if sub:
        draw_subtitle(ctx, sub)


# ============================================================================ S6 corn 1970 (warm film)
def scene_corn(ctx, t, sub=None, blight=0.45, seed_film=3):
    set_color(ctx, "#5A4426")
    ctx.paint()
    sp = 76
    for y in range(SAFE_TOP - 40, 1360, sp):
        set_color(ctx, "#4A3820", 0.55)
        ctx.rectangle(0, y + sp * 0.62, W, 12)
        ctx.fill()
    rows = list(range(SAFE_TOP + 10, 1360, sp))
    front = 1360 - blight * (1360 - SAFE_TOP)   # blight moves bottom (south) -> top (north)
    rng = np.random.default_rng(21)
    for ri, y in enumerate(rows):
        for ci, x in enumerate(range(20 + (ri % 2) * sp // 2, W + 40, sp)):
            jitter = rng.normal(0, 2)
            d = (y - front) / 240
            health = 1.0 - clamp(d + rng.normal(0, 0.15))
            art.corn_plant(ctx, x + jitter, y + jitter, 37, healthy=health, rot=0.3, seed=ri * 100 + ci)
    # warm 1970s film grade
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    set_color(ctx, "#F2B84B", 0.38)
    ctx.paint()
    ctx.restore()
    set_color(ctx, "#FFE2A8", 0.06)
    ctx.paint()
    vignette(ctx, 0.75, (0.12, 0.06, 0.0))
    overlay_grain(ctx, seed_film, 0.09)
    g = cairo.LinearGradient(W, 0, W - 260, 0)
    g.add_color_stop_rgba(0, 1.0, 0.45, 0.15, 0.26)
    g.add_color_stop_rgba(1, 1.0, 0.45, 0.15, 0.0)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()
    rounded_rect(ctx, 60, SAFE_TOP + 20, W - 120, 214, 14)
    set_color(ctx, "#1C1308", 0.78)
    ctx.fill()
    draw_text(ctx, "1970 · 美国玉米带", 96, SAFE_TOP + 86, "sans_black", 46, "#FFE3A3", 1, "ls")
    draw_text(ctx, "约 85% 的商品玉米种子，靠同一种 T 型细胞质生产", 96, SAFE_TOP + 146, "sans_medium", 30, "#F7D9A0", 1, "ls")
    draw_text(ctx, "玉米小斑病新菌株：从南往北，全国减产约 15%", 96, SAFE_TOP + 198, "sans_medium", 30, "#F7D9A0", 1, "ls")
    rounded_rect(ctx, W - 150, SAFE_TOP + 262, 90, 60, 10)
    set_color(ctx, "#1C1308", 0.7)
    ctx.fill()
    draw_text(ctx, "北 ↑", W - 105, SAFE_TOP + 304, "sans_bold", 32, "#FFE3A3", 1, "ms")
    rounded_rect(ctx, W - 150, 1252, 90, 60, 10)
    set_color(ctx, "#1C1308", 0.7)
    ctx.fill()
    draw_text(ctx, "南", W - 105, 1294, "sans_bold", 32, "#FFE3A3", 1, "ms")
    if sub:
        draw_subtitle(ctx, sub)


# ============================================================================ S7 parchment (1788)
PARCH = "#E8D8B0"
QUILL_INK = "#2A1B0C"


def parchment_backdrop(ctx, seed=4):
    set_color(ctx, PARCH)
    ctx.paint()
    rng = np.random.default_rng(seed)
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.uniform(20, 120)
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, 0.55, 0.42, 0.22, rng.uniform(0.03, 0.08))
        g.add_color_stop_rgba(1, 0.55, 0.42, 0.22, 0)
        ctx.set_source(g)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()
    g = cairo.RadialGradient(W / 2, H * 0.4, H * 0.28, W / 2, H * 0.4, H * 0.8)
    g.add_color_stop_rgba(0, 0.35, 0.22, 0.08, 0)
    g.add_color_stop_rgba(1, 0.35, 0.22, 0.08, 0.9)
    ctx.set_source(g)
    ctx.paint()


def scene_parchment(ctx, t, sub=None, q1=1.0, q2=1.0):
    parchment_backdrop(ctx)
    draw_text(ctx, "THE FEDERALIST", W / 2, SAFE_TOP + 90, "fell_sc", 64, QUILL_INK, 1, "ms", tracking=0.06)
    draw_text(ctx, "No. LI  ·  1788", W / 2, SAFE_TOP + 150, "fell", 40, QUILL_INK, 0.9, "ms")
    draw_text(ctx, "《联邦党人文集》第 51 篇 · 一般认为出自麦迪逊", W / 2, SAFE_TOP + 205, "serif_medium", 29, QUILL_INK, 0.85, "ms")
    set_color(ctx, QUILL_INK, 0.8)
    ctx.set_line_width(1.5)
    for dy in (232, 238):
        ctx.move_to(W / 2 - 280, SAFE_TOP + dy)
        ctx.line_to(W / 2 + 280, SAFE_TOP + dy)
    ctx.stroke()
    y = SAFE_TOP + 360
    for ln in ["“Ambition must be made", "to counteract ambition.”"]:
        draw_text(ctx, ln, W / 2, y, "fell_italic", 72, QUILL_INK, q1, "ms")
        y += 92
    draw_text(ctx, "要用野心，去对抗野心。", W / 2, y + 40, "serif_bold", 54, "#6B2B12", q1, "ms")
    y += 200
    for ln in ["“If men were angels, no", "government would be necessary.”"]:
        draw_text(ctx, ln, W / 2, y, "fell_italic", 56, QUILL_INK, 0.9 * q2, "ms")
        y += 74
    draw_text(ctx, "如果人都是天使，就不需要政府了。", W / 2, y + 30, "serif_medium", 40, "#6B2B12", 0.95 * q2, "ms")
    art.draw_quill(ctx, W - 230, 1235, 1.1, angle=-0.75)
    set_color(ctx, QUILL_INK, 0.85)
    ctx.arc(W - 232, 1240, 6, 0, 2 * math.pi)
    ctx.fill()
    if sub:
        draw_subtitle(ctx, sub, band=True)


# ============================================================================ S8 gears + scale (ending)
def scene_gears(ctx, t, sub=None, rot=0.0, leaf=1.0, lines=None, line_alpha=None):
    tech_backdrop(ctx, grid_alpha=0.03)
    cx, cy = W / 2, SAFE_TOP + 290
    r1 = 132
    art.draw_gear(ctx, cx - 110, cy, r1, 18, rot, CYAN)
    art.draw_gear(ctx, cx + 118, cy - 66, 96, 13, -rot * r1 / 96 + 0.12, ORANGE)
    art.draw_gear(ctx, cx + 104, cy + 120, 84, 12, -rot * r1 / 84 + 0.2, ORANGE, alpha=0.8)
    draw_text(ctx, "一个声音", cx - 110, cy + r1 + 52, "sans_bold", 30, CYAN, 1, "ms")
    draw_text(ctx, "许多声音", cx + 250, cy + 222, "sans_bold", 30, ORANGE, 1, "ls")
    draw_text(ctx, "互相卡住，谁也转不快", W / 2, cy + 300, "sans", 28, GREY, 1, "ms")
    # balance scale with the real world (a leaf) at its centre
    top = cy + 470
    set_color(ctx, WHITE, 0.85)
    ctx.set_line_width(5)
    ctx.move_to(cx, top)
    ctx.line_to(cx, top + 230)
    ctx.stroke()
    ctx.move_to(cx - 300, top + 20)
    ctx.line_to(cx + 300, top + 20)
    ctx.stroke()
    ctx.move_to(cx - 90, top + 230)
    ctx.line_to(cx + 90, top + 230)
    ctx.stroke()
    for sx, col in [(-300, CYAN), (300, ORANGE)]:
        ctx.set_line_width(2)
        set_color(ctx, WHITE, 0.6)
        ctx.move_to(cx + sx, top + 20)
        ctx.line_to(cx + sx - 70, top + 130)
        ctx.move_to(cx + sx, top + 20)
        ctx.line_to(cx + sx + 70, top + 130)
        ctx.stroke()
        ctx.save()
        ctx.translate(cx + sx, top + 130)
        ctx.scale(1, 0.25)
        ctx.arc(0, 0, 80, 0, math.pi)
        ctx.restore()
        set_color(ctx, col, 0.85)
        ctx.fill()
    if leaf > 0:
        lx, ly = cx, top - 62
        ctx.save()
        ctx.translate(lx, ly)
        ctx.rotate(-0.4)
        s = 1.0 * (ease_back(leaf) if leaf < 1 else 1)
        ctx.scale(s, s)
        g = cairo.RadialGradient(0, 0, 5, 0, 0, 90)
        g.add_color_stop_rgba(0, 0.5, 0.9, 0.55, 0.35)
        g.add_color_stop_rgba(1, 0.5, 0.9, 0.55, 0.0)
        ctx.set_source(g)
        ctx.arc(0, 0, 90, 0, 2 * math.pi)
        ctx.fill()
        ctx.new_path()
        ctx.move_to(0, 46)
        ctx.curve_to(-50, 12, -44, -50, 0, -76)
        ctx.curve_to(44, -50, 50, 12, 0, 46)
        ctx.close_path()
        set_color(ctx, "#7BD389", 0.97)
        ctx.fill()
        set_color(ctx, "#2F6B3A")
        ctx.set_line_width(3)
        ctx.move_to(0, 58)
        ctx.line_to(0, -64)
        ctx.stroke()
        for k in range(4):
            yy = -40 + k * 22
            ctx.move_to(0, yy + 10)
            ctx.line_to(-22, yy - 6)
            ctx.move_to(0, yy + 10)
            ctx.line_to(22, yy - 6)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.restore()
        draw_text(ctx, "真实世界", lx + 78, ly - 10, "sans_bold", 32, "#9BE3A6", leaf, "ls")
    if lines:
        yy = 1335
        for i, (ln, col) in enumerate(lines):
            a = 1.0 if line_alpha is None else line_alpha[i]
            draw_text(ctx, ln, W / 2, yy, "sans_bold", 44, col, a, "ms", shadow=6)
            yy += 72
    if sub:
        draw_subtitle(ctx, sub)
