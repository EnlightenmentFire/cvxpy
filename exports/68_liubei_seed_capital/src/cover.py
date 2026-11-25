import skia, numpy as np, math
from PIL import Image
import gfx, scenes
from gfx import *
surf = skia.Surface(W, H); c = surf.getCanvas()
t = 3.3
scenes.draw_img(c, scenes.bg_epic(21), 0, 0)
scenes.herd(c, t, 1000, n=30, scale=1.6, speed=600, seed=9)
scenes.dust(c, t, -200, 1300, 1400, n=80, seed=7, col=(230, 150, 90), a=0.6, drift=260, size=60)
# boy weaving foreground, left
figure(c, 300, 1760, 520, color=(10, 6, 6), pose="sit", phase=0.2, rim=(255, 150, 80), rim_a=0.95)
for k in range(14):
    a0 = k * 0.45
    c.drawLine(470, 1640, 470 + math.cos(a0) * 150, 1670 + math.sin(a0) * 50, paint((220, 170, 90), 0.6, stroke=3))
for i in range(30):
    ph = i / 30
    coin(c, 1000 - 500 * ph, 1150 + math.sin(ph * 7) * 60 - 300 * ph, 16, a=0.9 * math.sin(ph * math.pi), spin=i)
c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 800), paint(INK, 0.35, blur=60))
draw_text(c, "卖草鞋的刘备", W / 2, 400, font("serif_blk", 132), GOLD_L, 1, stroke=9, shadow=18, spacing=6, glow=22, glow_col=GOLD)
draw_text(c, "第一笔钱是谁给的？", W / 2, 540, font("serif_blk", 86), WHITE, 1, stroke=8, shadow=14, spacing=4)
for i, s in enumerate(["族叔", "名师", "同学", "马贩子"]):
    x = 165 + i * 250
    seal(c, x, 700, 110, ["宗族", "名師", "同門", "商賈"][i], a=1, prog=1)
    draw_text(c, s, x, 800, font("sans_b", 40), WHITE, 1, stroke=5)
draw_text(c, "乱世起家录｜刘备篇", 48, 118, font("sans_m", 34), GOLD, 1, align="l", stroke=4)
img = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
Image.fromarray(img).save("/home/user/work/out/cover_1080x1920.png")
Image.fromarray(img[0:1440]).save("/home/user/work/out/cover_1080x1440.png")
