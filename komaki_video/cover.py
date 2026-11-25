# -*- coding: utf-8 -*-
"""Cover images: 1080x1920 (9:16) and 1080x1440 (3:4)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import illus
from illus import golden_fan, hills, ashigaru, fog, nobori

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def cover(out, h=H):
    surf, ctx = new_surface(W, H)
    t = 2.0
    ctx.set_source_surface(illus.sky("hill"), 0, 0); ctx.paint()
    hills(ctx, 1170, 300, (0.12, 0.10, 0.08), seed=5, freq=0.004)
    golden_fan(ctx, 700, 1090, 1.05, t, 1.0, glow=1.0)
    for i in range(7):
        ashigaru(ctx, 470 + i * 62, 1095 + (i % 2) * 10, 0.6, 0, BLU, "yari", -1, 1.0)
    ctx.set_source_surface(fog(51, 0.4, (0.6, 0.55, 0.45), 500), 0, 960); ctx.paint_with_alpha(0.7)
    hills(ctx, 1480, 260, (0.05, 0.045, 0.04), seed=6, freq=0.005)
    for i in range(6):
        ashigaru(ctx, 90 + i * 72, 1440 + (i % 2) * 14, 1.25, 0, RED, "teppo", 1, 1.0)
    nobori(ctx, 30, 1300, 330, RED, t, 1); nobori(ctx, 980, 1290, 300, RED, t, 2)
    ctx.set_source_surface(vignette_surface(0.7), 0, 0); ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0, 0.88); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 760); ctx.fill()
    g = cairo.LinearGradient(0, 1250, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.92)
    ctx.set_source(g); ctx.rectangle(0, 1250, W, H - 1250); ctx.fill()
    text(ctx, "从无名小卒到天下人", W / 2, 250, 40, GOLD, 0.9, "mm", serif=True)
    text(ctx, "小牧长久手", W / 2, 390, 150, IVORY, 1, "mm", bold=True, serif=True, halo=16)
    text(ctx, "打输了一仗，怎样赢下整局", W / 2, 535, 58, GOLD, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "十万", 300, 1330, 110, RED, 1, "mm", bold=True, serif=True, halo=12)
    text(ctx, "对", W / 2, 1340, 50, IVORY, 1, "mm", serif=True, halo=8)
    text(ctx, "三万", 780, 1330, 110, BLU, 1, "mm", bold=True, serif=True, halo=12)
    text(ctx, "秀吉唯一没打赢的对手，", W / 2, 1490, 58, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "最后为什么还是低了头？", W / 2, 1580, 58, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "1584 · 尾张", W / 2, 1700, 38, GOLD, 0.9, "mm", serif=True)
    if h == H:
        surf.write_to_png(out)
    else:
        s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, h); c2 = cairo.Context(s2)
        c2.set_source_surface(surf, 0, -240); c2.paint(); s2.write_to_png(out)


if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    cover(f"{WORK}/out/cover_1080x1920.png")
    cover(f"{WORK}/out/cover_1080x1440_3x4.png", 1440)
    print("ok")
