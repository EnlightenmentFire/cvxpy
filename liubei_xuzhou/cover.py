# -*- coding: utf-8 -*-
"""封面：1080×1920（竖版全屏）＋ 1080×1440（3:4 裁切，信息集中在中部）。"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import engine as E
import geomap as G
import widgets as Wd
from engine import W, H, C
from scenes import tint_poly, fortress, troop, flagsea

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/cover"


def main():
    os.makedirs(OUT, exist_ok=True)
    surf, ctx = E.new_frame()
    cam = G.Cam(117.85, 34.95, 330, sy=H * 0.52)
    G.base(ctx, cam, dim=0.75, prov_labels=False)
    tint_poly(ctx, cam, "徐州", C["red"], 0.17, C["red2"])
    tan = cam.p("郯")
    t = 3.0
    sea = (tan[0] - 380, tan[1] - 30)
    troop("cv_cao", 4200, (420, 330), 5, "#121110", C["gold"], 4.2).draw(ctx, sea[0], sea[1] + 40, t, 0.9)
    flagsea("cv", 90, 820, 600).draw(ctx, sea[0], sea[1], t, size=32, char="曹", persp=0.5)
    for k, (fx, fy) in enumerate([(-170, -140), (60, -60), (-230, 60), (40, 190)]):
        Wd.fire(ctx, sea[0] + fx, sea[1] + fy + 60, 18, t, 0.8, seed=k)
    fortress(ctx, tan[0], tan[1], 60, "#f0e4c8")
    path = [(tan[0] + 60, -60), (tan[0] + 130, 300), (tan[0] + 90, tan[1] - 260), (tan[0] + 40, tan[1] - 90)]
    Wd.thick_arrow(ctx, path, 0.95, 16, 34, **Wd.arrow_style("liu"))
    x, y, ang = E.point_along(E.smooth_path(path, 10), 0.9)
    troop("cv_liu", 150, (34, 60), 9, C["red2"], "#ffd7cc", 5.0).draw(ctx, x, y - 40, t, 1.0, ang=ang - math.pi / 2)
    # 压暗上下，放大字
    import cairo
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.85); g.add_color_stop_rgba(0.38, 0, 0, 0, 0.15)
    g.add_color_stop_rgba(0.62, 0, 0, 0, 0.15); g.add_color_stop_rgba(1, 0, 0, 0, 0.9)
    ctx.set_source(g); ctx.rectangle(0, 0, W, H); ctx.fill()
    E.draw_text(ctx, "带一千人去救火", W / 2, 330, "serif", "Black", 104, "#f6ecd6", 1, "cm", shadow=10, tracking=0.04)
    E.draw_text(ctx, "怎么就当上了", W / 2, 470, "serif", "Black", 104, "#f6ecd6", 1, "cm", shadow=10, tracking=0.04)
    E.draw_text(ctx, "徐州之主？", W / 2, 620, "serif", "Black", 132, C["red2"], 1, "cm", shadow=12, tracking=0.06)
    E.draw_text(ctx, "非劉備不能安此州也", W / 2, 1500, "tc", "Bold", 64, C["gold2"], 1, "cm", shadow=8, tracking=0.12)
    E.draw_text(ctx, "—— 陶谦临终", W / 2, 1585, "serif", "Medium", 36, "#d8cdb6", 0.9, "cm")
    E.draw_text(ctx, "乱世起家录 · 刘备篇", W / 2, 1700, "sans", "Medium", 34, "#cfc3aa", 0.85, "cm", tracking=0.2)
    E.draw_seal(ctx, "刘备", W - 150, 760, 110, 1, C["red"], -0.08)
    buf = E.postprocess(surf, 0, grain=False)
    im = Image.fromarray(buf[..., [2, 1, 0]].copy())
    im.save(f"{OUT}/封面_1080x1920.png")
    im.crop((0, 200, 1080, 1640)).save(f"{OUT}/封面_3x4_1080x1440.png")
    print("cover ok")


if __name__ == "__main__":
    main()
