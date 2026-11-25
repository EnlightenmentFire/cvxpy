# -*- coding: utf-8 -*-
"""封面 1080x1920：咸阳车驾底 + 两个剪影 + 大标题"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eng import *
import scenes as SC
from PIL import Image, ImageDraw

cv = Image.new('RGBA', (W, H), INK + (255,))
C = {}
SC._procession_bg(C)
SC.zoom_bg(cv, C['bg'], 0, 1, 1.0, 1.0, 0.5, 0.45)
cv.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 120)))
SC.embers(C, n=90).draw(cv, 3.0, 1.0)
b1 = bust('bang', 760, (5, 5, 6, 255), rim=(255, 120, 70))
b2 = bust('bei', 760, (5, 5, 6, 255), rim=(255, 120, 70))
put(cv, b1, 290, 1560, 1.0)
put(cv, b2, 800, 1560, 1.0)
put(cv, txt('刘邦', 64, 'black', RED2, 4), 290, 1880 - 70, 1.0)
put(cv, txt('刘备', 64, 'black', RED2, 4), 800, 1880 - 70, 1.0)
put(cv, txt('VS', 110, 'black', GOLD2, 4, glow=20, gcol=(200, 100, 0)), 545, 1500, 1.0)
cv.alpha_composite(vignette(0.8))
put(cv, txt('刘邦和刘备', 150, 'brush', (255, 236, 205), glow=24, gcol=(0, 0, 0)), W / 2, 430, 1.0)
put(cv, txt('谁才是真草根？', 136, 'brush', RED2, glow=30, gcol=(120, 10, 0)), W / 2, 640, 1.0)
put(cv, txt('没有名字的父亲 · 过期的皇族家谱', 50, 'serifsc', GOLD2, 3, glow=8, gcol=(0, 0, 0)), W / 2, 820, 1.0)
put(cv, tag('乱世起家录｜序章', GOLD, 40, 70), W / 2, 230, 1.0)
cv.convert('RGB').save(sys.argv[1] if len(sys.argv) > 1 else 'cover.png')
