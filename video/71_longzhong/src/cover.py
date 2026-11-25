# -*- coding: utf-8 -*-
"""封面 1080×1920：开场插画 + 大标题。usage: python cover.py out.png"""
import sys, os, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import illus
from gfx import *
from cards import big
from geo import W, H
s = skia.Surface(W, H); c = s.getCanvas()
illus.draw(c, 2.5, door=1.0, light=1.0, mapu=1.0, mglow=1.0, lit=(1, 1), zoom=1.0)
p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 760)], [rgba('#05070A', 0.88), rgba('#05070A', 0.0)]))
c.drawRect(skia.Rect.MakeWH(W, 760), p)
text(c, '混了二十多年没地盘', 540, 300, 84, '#FFF2E6', 'serifx', 1, 'c', stroke=10, shadow=16)
text(c, '刘备缺的到底是什么？', 540, 420, 84, '#FFD9A0', 'serifx', 1, 'c', stroke=10, shadow=16)
tag(c, 540, 500, '隆中对 · 三顾茅庐', LIU, 1, size=40, anchor='c')
p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 1500), (0, H)], [rgba('#05070A', 0.0), rgba('#05070A', 0.85)]))
c.drawRect(skia.Rect.MakeXYWH(0, 1500, W, 420), p)
text(c, '乱世起家录｜刘备篇', 540, 1700, 44, '#E8E1D3', 'serif', 1, 'c', stroke=6, shadow=8)
text(c, '他四十七岁，一个二十六岁的年轻人给了他一张地图', 540, 1770, 30, '#D9D2C2', 'sansm', 1, 'c', stroke=4, shadow=6)
s.makeImageSnapshot().save(sys.argv[1])
print('cover', sys.argv[1])
