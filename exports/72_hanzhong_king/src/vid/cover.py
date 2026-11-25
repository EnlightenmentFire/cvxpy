# -*- coding: utf-8 -*-
"""封面：定军山冲锋画面 + 大标题。输出 1080×1920 与 1080×1440（3:4）两版。"""
import skia, numpy as np
import scenes
from scenes import sc_open, S
from gfx import *
from ui import big_caption
from geo import W, H
_bc = scenes.big_caption; scenes.big_caption = lambda *a, **k: None
s = skia.Surface(W, H); c = s.getCanvas()
sc_open(c, 1.9)
dim(c, 0.18)
p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 760)], [rgba('#000000', 0.80), rgba('#000000', 0.0)])); c.drawRect(skia.Rect.MakeWH(W, 760), p)
p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 1150), (0, H)], [rgba('#000000', 0.0), rgba('#000000', 0.85)])); c.drawRect(skia.Rect.MakeXYWH(0, 1150, W, 770), p)
def draw_titles(c, y0):
    text(c, '五十八岁', W / 2, y0, 92, '#F4E6C2', 'serifx', 1, 'c', stroke=8, shadow=14, spacing=14)
    big_caption(c, '终于赢了曹操', 1, y0 + 170, 132, spacing=6)
    rrect(c, W / 2 - 330, y0 + 222, 660, 4, 2, '#D9B65A', 1)
    text(c, '刘备一生唯一一次正面赢曹操，是怎么赢的？', W / 2, y0 + 290, 40, '#EDE3CF', 'sans', 1, 'c', stroke=5, shadow=8)
draw_titles(c, 250)
rrect(c, 70, 1640, 360, 64, 6, LIU, 1); text(c, '乱世起家录 · 刘备篇', 250, 1684, 34, '#FFF2E4', 'sans', 1, 'c')
text(c, '定军山 · 公元219年', W - 70, 1684, 32, '#E8DCC0', 'serifm', 1, 'r', stroke=4)
s.makeImageSnapshot().save('/tmp/claude-0/work/vid/cover_1080x1920.png', skia.kPNG)
# 3:4 版（取中间 1440 高，标题重排）
s2 = skia.Surface(W, 1440); c2 = s2.getCanvas()
c2.save(); c2.translate(0, -240); sc_open(c2, 1.9); c2.restore()
scenes.big_caption = _bc
dim(c2, 0.18)
p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, 640)], [rgba('#000000', 0.82), rgba('#000000', 0.0)])); c2.drawRect(skia.Rect.MakeWH(W, 640), p)
draw_titles(c2, 170)
rrect(c2, 70, 1320, 360, 64, 6, LIU, 1); text(c2, '乱世起家录 · 刘备篇', 250, 1364, 34, '#FFF2E4', 'sans', 1, 'c')
s2.makeImageSnapshot().save('/tmp/claude-0/work/vid/cover_1080x1440.png', skia.kPNG)
print('ok')
