# -*- coding: utf-8 -*-
"""Cover images: 1080x1920 and 1080x1440 (3:4)."""
import sys, os, math
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import scenes as SC
from widgets import strike

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/cover"


class FakeSc:
    def __init__(self):
        self.lines = [dict(s0=0, s1=3), dict(s0=3, s1=6), dict(s0=1.0, s1=9), dict(s0=99, s1=100), dict(s0=99, s1=100), dict(s0=99, s1=100)]
        self.T = 0
        self.cover = True

    def cue(self, i):
        return self.T - self.lines[i]["s0"]

    def ld(self, i):
        return self.lines[i]["s1"] - self.lines[i]["s0"]


def draw(ctx, h):
    sc = FakeSc(); sc.T = 4.2
    ctx.save()
    if h != H:
        ctx.translate(0, -(H - h) / 2 + 120)
    SC.s00(ctx, sc.T, sc, 0)
    ctx.restore()
    # cover the hook's own overlay text area with a dark band and set the title
    yb = h * 0.56
    g = cairo.LinearGradient(0, yb - 260, 0, yb + 420)
    g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(0.35, 0, 0, 0, 0.75); g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
    ctx.set_source(g); ctx.rectangle(0, yb - 260, W, h - yb + 260); ctx.fill()
    text(ctx, "历史的关键一局 · 中途岛", W / 2, yb - 120, 40, GOLD, 1, SERIF, True, stroke=5)
    text(ctx, "命运的五分钟", W / 2, yb + 30, 138, GOLD, 1, SERIF, True, stroke=10, glow=18)
    strike(ctx, 150, yb - 15, W - 150, 1.0, 0.95, RED, 14)
    text(ctx, "可能根本不存在？", W / 2, yb + 170, 80, WHITE, 1, SERIF, True, stroke=8)
    text(ctx, "四艘航母，一个上午 · 史料对质", W / 2, yb + 260, 40, (0.85, 0.88, 0.92), 1, SANS, True, stroke=5)


for name, h in (("cover_1080x1920.png", 1920), ("cover_1080x1440.png", 1440)):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, h)
    ctx = cairo.Context(surf)
    draw(ctx, h)
    os.makedirs(OUT, exist_ok=True)
    surf.write_to_png(f"{OUT}/{name}")
print("cover ok")
