# -*- coding: utf-8 -*-
"""封面：9:16（1080×1920）与 3:4（1080×1440）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from art import *
import visuals

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)) + "/preview"


def make():
    im = visuals.street(0.62, 3.0, dim=0.35, walkers=True)
    # 六道小圆
    names = ["地狱", "饿鬼", "畜生", "阿修罗", "人", "天"]
    for i, n in enumerate(names):
        x = 150 + i * 156
        over(im, glow(84, visuals.FACE_COL[n], 1.6, 0.7), (x, 1040))
        d = ImageDraw.Draw(im)
        d.ellipse((x - 62, 1040 - 62, x + 62, 1040 + 62), fill=(12, 12, 16, 220), outline=visuals.FACE_COL[n] + (255,), width=3)
        over(im, text_img(n, "ukai", 46 if len(n) < 3 else 36, visuals.FACE_COL[n]), (x, 1040))
    over(im, text_img("一天之内", "serif", 120, MIST, shadow=8), (W // 2, 470))
    over(im, text_img("你可能走过六道", "serif", 140, GOLD, shadow=8), (W // 2, 640))
    over(im, text_img("六道轮回的心理学读法", "serif", 56, (230, 220, 200), shadow=5), (W // 2, 800))
    over(im, text_img("地狱不在地下 · 可能就在一个人的心里", "sans", 40, (200, 190, 175), shadow=4), (W // 2, 1250))
    return im.convert("RGB")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    c = make()
    c.save(f"{OUT}/cover_9x16.png")
    # 3:4：取中段 1080×1440
    c.crop((0, 240, 1080, 1680)).save(f"{OUT}/cover_3x4.png")
    print("cover ok")
