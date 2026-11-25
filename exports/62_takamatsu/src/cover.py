# -*- coding: utf-8 -*-
"""封面：1080x1920（9:16）与 1080x1440（3:4）。画面取自开场：暴雨中的人造湖与孤岛。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import world as WD
import scenes as SC

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def cover(out, h=H):
    cam = WD.Cam(0.12, -1.2, 0.18, -5, 9.5, F=1150)
    lv = 5.25
    surf = WD.oblique_surface(cam, lv, 3.0, rain=1.0, flash=0.25)
    ctx = cairo.Context(surf)
    WD.ridges(ctx, cam, 0, seed=1)
    SC.dike_glow_3d(ctx, cam, 0.9)
    SC.town_sprites(ctx, cam, lv)
    SC.castle_sprites(ctx, cam, lv)
    for i, (x, y) in enumerate([(-1.6, -0.6), (-0.6, -1.25), (0.4, -1.2), (1.0, -0.8), (1.25, 2.1), (1.5, 0.4)]):
        WD.banner(ctx, cam.project(x, y, 0), RED, 0.9, 1.0, i, size=1.4)
    WD.lightning(ctx, 760, 0.05, seed=3, y1=WD.horizon_y(cam) + 10)
    WD.rain_overlay(ctx, 2.0, 1.2, 0.45)
    ctx.set_source_surface(vignette_surface(0.7), 0, 0); ctx.paint()
    g = cairo.LinearGradient(0, 0, 0, 760); g.add_color_stop_rgba(0, 0, 0, 0, 0.88); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 760); ctx.fill()
    g = cairo.LinearGradient(0, 1250, 0, H); g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.92)
    ctx.set_source(g); ctx.rectangle(0, 1250, W, H - 1250); ctx.fill()
    text(ctx, "从无名小卒到天下人", W / 2, 300, 40, GOLD, 0.95, "mm", serif=True)
    text(ctx, "高松城水攻", W / 2, 440, 160, (1, 0.97, 0.9), 1, "mm", bold=True, serif=True, halo=16)
    text(ctx, "不攻城，造一片湖", W / 2, 600, 68, GOLD, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "攻不下的城，", W / 2, 1420, 70, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "他干脆把它变成一座孤岛", W / 2, 1520, 70, IVORY, 1, "mm", bold=True, serif=True, halo=10)
    text(ctx, "1582 · 备中高松", W / 2, 1650, 40, GOLD, 0.9, "mm", serif=True)
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
