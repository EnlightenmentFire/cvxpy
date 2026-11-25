# -*- coding: utf-8 -*-
"""Cover: 1080x1920 and 3:4 (1080x1440) crop."""
from PIL import Image, ImageDraw, ImageFilter
from gfx import *
from scenes import gate_static, lantern_img, lantern_glow, big_title

OUT = "/tmp/claude-0/w73/out"
b = gate_static(moon=False).copy()
for x in (300, 780):
    paste(b, lantern_glow(), x - 350, 1050 - 350, 0.9)
    paste(b, lantern_img(), x - 110, 920)
dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(dark)
for y in range(0, 900):
    d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / 900))))
b.alpha_composite(dark)
t1 = glow(text_img("治世之能臣", sc_font(KAI, 150), GOLD_L, stroke=3, stroke_fill=(50, 30, 6)), 26, 1.6)
t2 = glow(text_img("乱世之奸雄", sc_font(KAI, 150), GOLD_L, stroke=3, stroke_fill=(50, 30, 6)), 26, 1.6)
paste_c(b, t1, 540, 360); paste_c(b, t2, 540, 560)
q = text_img("曹操听完，为什么大笑？", sc_font(SERIF_B, 66), IVORY, stroke=4, stroke_fill=(0, 0, 0))
paste_c(b, q, 540, 760)
band = rrect((900, 120), 60, (10, 10, 12, 220), outline=GOLD + (255,), width=3)
paste_c(b, band, 540, 1600)
s = text_img("二十岁 · 五色棒 · 一句评语", sc_font(SANS_B, 52), GOLD_L)
paste_c(b, s, 540, 1600)
sub = text_img("乱世起家录｜曹操篇", sc_font(SERIF_R, 40), (210, 200, 180))
paste_c(b, sub, 540, 1740)
b.convert("RGB").save(f"{OUT}/cover_1080x1920.png")
b.convert("RGB").crop((0, 240, 1080, 1680)).save(f"{OUT}/cover_1080x1440_3x4.png")
print("ok")
