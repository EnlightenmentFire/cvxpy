# -*- coding: utf-8 -*-
"""Cover images: 1080x1920 (full) and 1080x1440 (3:4 feed crop), plus a 120 px legibility check."""
import os, sys, math
import numpy as np
from PIL import Image
from gfx import *
from art import *
import scenes

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work"


def cover():
    f = bg_base().copy()
    light, rock = cave_layers()
    comp_add(f, light, 1.0)
    draw_mist(f, 3.0, 0.22, seed=2, speed=10, y0=500)
    fig, rim = seated_figure()
    comp(f, fig)
    comp_add(f, rim, 0.9)
    comp(f, brain_layer(), 0.75)
    for i, n in enumerate(["mpfc", "pcc", "mtl", "ang", "dacc"]):
        x, y, _ = NODES[n]
        comp_add(f, glow_blob(x, y, 16, GOLD, 1.0))
        comp_add(f, glow_blob(x, y, 50, GOLD, 0.35))
    comp(f, scenes.net_lines(), 0.7)
    comp(f, rock, 1.0)
    # darken top for the title
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    f *= (0.5 + 0.5 * np.clip((yy - 0.08) / 0.22, 0, 1))
    comp_any(f, text_layer("一走神", ("serif", 150, 900), WHITE, CX, 300, shadow=((0, 0, 0), 10, 0.9)))
    comp_any(f, text_layer("就不快乐？", ("serif", 150, 900), GOLD, CX, 470, shadow=((0, 0, 0), 10, 0.9)))
    comp_any(f, text_layer("两千多年前的佛经 × 今天的脑科学", ("serif", 50, 600), WHITE, CX, 1390,
                           shadow=((0, 0, 0), 8, 0.9)))
    comp_any(f, text_layer("印照，不是证明", ("serif", 44, 600), GREY, CX, 1470, shadow=((0, 0, 0), 8, 0.9)))
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    a = cover()
    im = Image.fromarray(a)
    im.save(f"{OUT}/封面_1080x1920.png")
    # 3:4 crop keeping title + figure
    c34 = im.crop((0, 140, 1080, 1580))
    c34.save(f"{OUT}/封面_1080x1440.png")
    c34.resize((120, 160), Image.LANCZOS).save(f"{OUT}/封面_120px自检.png")
    print("ok")
