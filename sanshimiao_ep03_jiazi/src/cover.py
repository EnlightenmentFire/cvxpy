# -*- coding: utf-8 -*-
"""3:4 cover (1080x1440) for 三十秒一问 03《六十甲子》.
red tag top-left / three-line hook (六十年 in yellow) / the two meshing gears with 甲·子 under the pointers /
series mark in the corner.  Usage: python cover.py out.png"""
import math
import sys

import cairo

import render as R

CW, CH = 1080, 1440


def main(out):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, CW, CH)
    ctx = cairo.Context(surf)
    g = cairo.RadialGradient(CW / 2, 1040, 60, CW / 2, 900, 1050)
    g.add_color_stop_rgb(0, 0.10, 0.19, 0.34)
    g.add_color_stop_rgb(0.55, 0.045, 0.085, 0.17)
    g.add_color_stop_rgb(1, 0.02, 0.04, 0.09)
    ctx.set_source(g)
    ctx.paint()

    # gears (same geometry as the film, slightly larger), centred low
    sc = 1.04
    gy = 1088
    ctx.save()
    ctx.translate(CW / 2, gy)
    ctx.scale(sc, sc)
    ctx.translate(-R.W / 2, -R.CY)
    # soft shadow
    for cx, rr in ((R.CX1, R.R1), (R.CX2, R.R2)):
        for k in range(10, 0, -1):
            ctx.arc(cx + 10, R.CY + 18, rr + R.ADD * 0.6 + k * 4, 0, 2 * math.pi)
            ctx.set_source_rgba(0, 0, 0, 0.035)
            ctx.fill()
    R.draw_gear(ctx, R.CX1, R.CY, R.R1, R.N1, R.GAN, 0.0, -1, 0.0, 0, flash=0.08, label="天干", sub="10", sweep=0)
    R.draw_gear(ctx, R.CX2, R.CY, R.R2, R.N2, R.ZHI, 0.0, +1, 0.0, 0, flash=0.08, label="地支", sub="12", sweep=0)
    R.draw_pointer(ctx, R.CX1, R.CY - R.R1 - R.ADD - 8, 0.6)
    R.draw_pointer(ctx, R.CX2, R.CY - R.R2 - R.ADD - 8, 0.6)
    ctx.restore()

    # red tag
    R.font(ctx, R.SANS_BLACK, 46)
    txt = "1984 和 2044 是同一年"
    e = ctx.text_extents(txt)
    x, y, h = 56, 58, 84
    R.rounded_rect(ctx, x, y, e.x_advance + 56, h, 14)
    ctx.set_source_rgb(0.86, 0.12, 0.14)
    ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    fe = ctx.font_extents()
    ctx.move_to(x + 28, y + h / 2 + (fe[0] - fe[1]) / 2 * 0.92)
    ctx.show_text(txt)

    # hook, three lines
    R.rich_line(ctx, [("为什么", R.WHITE, 1.0)], CW / 2, 284, 132, stroke=12)
    R.rich_line(ctx, [("六十年", R.YELLOW, 1.0)], CW / 2, 468, 210, stroke=16)
    R.rich_line(ctx, [("一个轮回", R.WHITE, 1.0)], CW / 2, 654, 132, stroke=12)

    # series mark, bottom-right corner
    R.font(ctx, R.SANS, 40, bold=True)
    mark = "三十秒一问 03"
    e = ctx.text_extents(mark)
    ctx.set_source_rgba(*R.GOLD, 0.95)
    ctx.move_to(CW - 56 - e.x_advance, CH - 52)
    ctx.show_text(mark)
    surf.write_to_png(out)


if __name__ == "__main__":
    main(sys.argv[1])
