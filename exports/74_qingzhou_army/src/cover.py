# -*- coding: utf-8 -*-
"""封面：竖版 1080x1440 与 1080x1920。正中大字钩子问句 + 强视觉主体（玄黑描金方阵 + 曹字大旗 + 赭色潮水转色）。"""
import math
import numpy as np
import skia
from eng import *

Q1, Q2 = "几千残兵，", "怎么变三十万？"


def draw(c, w, h):
    T = 1.3
    c.drawColor(C(8, 8, 10))
    sh = skia.GradientShader.MakeRadial((w / 2, h * 0.62), h * 0.75, [C(92, 62, 26), C(30, 20, 12), C(6, 6, 8)], [0, 0.45, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(w, h), p)
    r = np.random.default_rng(3)
    cy0 = h * 0.70
    # 后方赭色潮水（未转色）
    n = 5000
    ox = r.normal(0, 1, n); oy = r.uniform(0, 1, n)
    xs = w / 2 + ox * w * 0.42; ys = cy0 + 40 + oy * h * 0.30
    turned = (ys - cy0) < h * 0.13 + ox * 30
    draw_pts(c, xs[~turned], ys[~turned], HJ, 0.85, 4.0)
    # 前方玄黑描金方阵（透视）
    rows = 26
    for rr in range(rows):
        u = rr / (rows - 1)
        sc = 0.55 + 0.9 * u
        y = cy0 - h * 0.08 + u * h * 0.27
        ncol = 34
        xs2 = np.linspace(w / 2 - w * 0.40 * sc, w / 2 + w * 0.40 * sc, ncol)
        ys2 = np.full(ncol, y)
        draw_pts(c, xs2, ys2, GOLD, 0.9, 11 * sc)
        draw_pts(c, xs2, ys2, (16, 14, 12), 1, 6.5 * sc)
        for x in xs2[::3]:
            c.drawLine(x + 3 * sc, y, x + 10 * sc, y - 34 * sc, paint(GOLD_L, 0.55, stroke=1.6 * sc))
    # 大旗
    flag(c, w / 2 - 20, cy0 - h * 0.05, "曹", CAO, GOLD, 1.9, 1, T)
    flag(c, w / 2 - 330, cy0 - h * 0.03, "青", CAO, GOLD, 1.5, 1, T + 1)
    flag(c, w / 2 + 300, cy0 - h * 0.03, "曹", CAO, GOLD, 1.5, 1, T + 2)
    # 顶部压暗，给大字
    sh = skia.GradientShader.MakeLinear([(0, h * 0.15), (0, h * 0.52)], [C(0, 0, 0, 200), C(0, 0, 0, 0)])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeLTRB(0, 0, w, h * 0.52), p)
    size = 128
    y1 = h * 0.40 - size * 1.3
    text(c, Q1, w / 2, y1 + size * 0.4, "serifB", size, WHITE, 1, stroke=8, stroke_col=(0, 0, 0), shadow=0.9)
    text(c, Q2, w / 2, y1 + size * 1.75, "serifB", size, GOLD_L, 1, stroke=8, stroke_col=(0, 0, 0), glow=(GOLD, 26, 0.6))
    vignette_wh(c, w, h)


def vignette_wh(c, w, h):
    sh = skia.GradientShader.MakeRadial((w / 2, h * 0.5), h * 0.75, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 170)], [0, 0.6, 1])
    p = skia.Paint(); p.setShader(sh); c.drawRect(skia.Rect.MakeWH(w, h), p)


def save(w, h, path):
    surf = skia.Surface(w, h)
    with surf as c:
        draw(c, w, h)
    from PIL import Image
    a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    Image.fromarray(a).save(path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/w74/render"
    save(1080, 1440, f"{out}/cover_1080x1440.png")
    save(1080, 1920, f"{out}/cover_1080x1920.png")
    print("ok")
