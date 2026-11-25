# -*- coding: utf-8 -*-
"""Cover images: 1080x1920 (9:16) and 1080x1440 (3:4)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import illus
from frame import panel

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def cover(out, h=H):
    surf, ctx = new_surface(W, H)
    illus.draw_dusk(ctx, 4.0, 0.78, rise=1.0, fire=0.8)
    ctx.set_source_surface(vignette_surface(0.7), 0, 0); ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 700); g.add_color_stop_rgba(0, 0, 0, 0, 0.85); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 700); ctx.fill()
    g = cairo.LinearGradient(0, 1150, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.9)
    ctx.set_source(g); ctx.rectangle(0, 1150, W, H - 1150); ctx.fill()
    text(ctx, "历史的关键一局", W / 2, 250, 40, GOLD, 0.9, "mm", serif=True)
    text(ctx, "滑铁卢", W / 2, 390, 170, IVORY, 1, "mm", bold=True, serif=True, halo=16)
    text(ctx, "拿破仑最后一天的调兵", W / 2, 540, 56, GOLD, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "La Garde recule !", W / 2, 1300, 70, (1, 0.9, 0.78), 0.95, "mm", family=LATIN_I, italic=True, halo=12)
    text(ctx, "他赢过几十场仗，", W / 2, 1450, 60, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "为什么最后一天调不动一支军队？", W / 2, 1540, 56, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "1815 · 6 · 18", W / 2, 1660, 40, GOLD, 0.9, "mm", serif=True)
    if h == H:
        surf.write_to_png(out)
    else:
        # 3:4 crop centred on the title block + column
        s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, h); c2 = cairo.Context(s2)
        c2.set_source_surface(surf, 0, -240); c2.paint(); s2.write_to_png(out)


if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    cover(f"{WORK}/out/cover_1080x1920.png")
    cover(f"{WORK}/out/cover_1080x1440_3x4.png", 1440)
    print("ok")
