# -*- coding: utf-8 -*-
"""封面 1080x1920（关键文字都在中部 3:4 安全区 y 240–1680 内）。usage: python cover.py OUT.png"""
import sys
from art import *
import scenes as SC


def main(out):
    b = SC.bg_courtyard().copy()
    b.alpha_composite(bamboo(0.6, 5, 960, 3, INK, 0.85))
    fig, xy = seated_figure(540, 1330, 0.8)
    b.alpha_composite(fig, xy)
    SC.soft_cover(b, 300, 760, 0.55, 80)
    put(b, text_sprite("打坐让人幸福", 120, "serif", "Black", INK, 4, PAPER), (540, 330), 1, "mt")
    put(b, text_sprite("证据有多硬？", 132, "serif", "Black", ZHU, 4, PAPER), (540, 500), 1, "mt")
    put(b, SC._tag_sprite("四十七项严格试验 · 一项手机研究 · 两句坛经", 34, ZHU, None), (540, 700), 1, "mt")
    put(b, seal("印照", 96, ZHU, seed=91), (850, 1380), 1)
    put(b, text_sprite("静坐的科学", 40, "serif", "SemiBold", INK2), (540, 1420), 1, "mt")
    b.convert("RGB").save(out)


if __name__ == "__main__":
    main(sys.argv[1])
