# -*- coding: utf-8 -*-
"""封面 1080×1920：水墨“落水与长竿”+ 标题。输出 out/cover.png"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
from art import *
import scenes as SC

WK = "/tmp/claude-0/work"


def main():
    bgp, mt, wt, bk, dw, jp, st, pole = SC.ink_scene_layers()
    im = bgp
    for l in (mt, wt, bk, dw, jp, st, pole):
        im = Image.alpha_composite(im, l)
    # 下移画面，给标题让位
    im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, -160), fillcolor=(0, 0, 0, 0))
    im = Image.alpha_composite(paper(43).convert("RGBA"), im)
    t1, h = text_layer("太能共情的人，\n为什么最容易累垮？", font("serif", 92, 800), INK + (255,), maxw=1000, y=300, spacing=1.3)
    im = Image.alpha_composite(im, t1)
    t2 = text_layer("同理心与慈悲：大脑里的两条路", font("serif", 50, 700), SEAL + (255,), y=560)[0]
    im = Image.alpha_composite(im, t2)
    lab1 = text_layer("跳下去一起挣扎", font("serif", 40, 700), WARM + (255,), x=720, y=1330)[0]
    lab2 = text_layer("站稳，伸出长竿", font("serif", 40, 700), (150, 100, 20, 255), x=300, y=1330)[0]
    im = Image.alpha_composite(Image.alpha_composite(im, lab1), lab2)
    foot = text_layer("佛法与心智 · 静坐的科学", font("sans", 34, 500), INK_SOFT + (255,), y=1500)[0]
    im = Image.alpha_composite(im, foot)
    im = Image.alpha_composite(im, seal("慈悲", 880, 1480, 90))
    os.makedirs(f"{WK}/out", exist_ok=True)
    im.convert("RGB").save(f"{WK}/out/cover.png")
    im.convert("RGB").resize((540, 960)).save(f"{WK}/out/cover_small.jpg", quality=85)


if __name__ == "__main__":
    main()
