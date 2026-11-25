# -*- coding: utf-8 -*-
"""封面：1080×1920（竖版）与 1080×1440（3:4 裁切）。"""
import os, sys, math
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import scenes as SC


def main(out_dir):
    surf = skia.Surface(W, H); c = surf.getCanvas()
    SC.stage_begin(c, 0.9)
    SC.room(c, 0.05, flash=0.75, rain=0.5)
    SC.figure(c, 230, 1300, 1.18, 1, robe=(26, 24, 26), trim=GOLD, rim=1.0, pose="cup", hand=1)
    SC.figure(c, 850, 1300, 1.18, -1, robe=(96, 26, 22), trim=(230, 150, 110), rim=1.0, pose="drop")
    SC.table(c)
    SC.utensils(c, 0.18, 0, slow=0.45)
    c.restore()
    grad_rect(c, 0, 0, W, 760, (6, 5, 4), 0.92, (6, 5, 4), 0.0)
    grad_rect(c, 0, 1250, W, 670, (6, 5, 4), 0.0, (6, 5, 4), 0.95)
    vignette(c, 0.6, 0.4)
    draw_text(c, "天下英雄", W / 2, 380, 150, GOLD_HI, 1, "tc", True, "center", stroke=8, stroke_a=0.7, shadow=18, spacing=16)
    draw_text(c, "唯使君與操耳", W / 2, 505, 92, (244, 230, 200), 1, "tc", True, "center", stroke=6, stroke_a=0.7, shadow=14, spacing=10)
    SC.stamp(c, "失匕箸", 915, 820, 96, 1.0)
    draw_text(c, "最落魄的时候", W / 2, 1500, 84, WHITE, 1, "sans", True, "center", stroke=8, shadow=14)
    draw_text(c, "拿到一张用了二十年的名片", W / 2, 1610, 72, GOLD_HI, 1, "sans", True, "center", stroke=8, shadow=14)
    img = surf.makeImageSnapshot().toarray()[..., [2, 1, 0]]
    from PIL import Image
    im = Image.fromarray(np.ascontiguousarray(img))
    im.save(f"{out_dir}/封面_1080x1920.png")
    # 3:4：取中间偏上
    im.crop((0, 240, 1080, 1680)).save(f"{out_dir}/封面_3x4_1080x1440.png")
    print("cover ok")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else f"{WORK}")
