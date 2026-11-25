"""Cover images: 1080x1920 (9:16) and 1080x1440 (3:4 crop-safe)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from gfx import *  # noqa
import scenes as S
from PIL import Image, ImageDraw

out = sys.argv[1]
img = S.field_bg().copy()
d = ImageDraw.Draw(img)
# darken top for title
top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(top)
for y in range(0, 900):
    td.line([(0, y), (W, y)], fill=(246, 238, 216, int(235 * (1 - y / 900) ** 0.6)))
img.alpha_composite(top)
paste(img, official(1.25, hold="book"), 300, 1500, anchor="b")
paste(img, farmer(1.25, head_dx=-8), 760, 1490, anchor="b")
paste(img, ledger(760, 330), W / 2, 1420)
for i in range(8):
    x = 220 + i * 86 if i < 4 else 600 + (i - 4) * 86
    tick(d, x, 1430, 46, 1.0, RED, 8)
draw_text(img, (W / 2, 330), "设计得这么好的政策", font("brush", 104), INK + (255,))
draw_text(img, (W / 2, 480), "为什么一到地方", font("brush", 104), INK + (255,))
draw_text(img, (W / 2, 630), "就变了味？", font("brush", 130), (150, 24, 20, 255))
draw_text(img, (W / 2, 790), "王安石变法为什么失败", font("serif_black", 52), (60, 50, 40, 255))
paste(img, seal("不借也得借"[:4] if False else "青苗", 150, rot=-6), 900, 960)
band = Image.new("RGBA", (W, 160), (20, 16, 12, 200))
img.alpha_composite(band, (0, 1640))
draw_text(img, (W / 2, 1720), "青苗钱：不借也得借", font("serif_black", 64), (250, 240, 220, 255))
img.convert("RGB").save(out)
# 3:4 version (center title area)
c = Image.open(out).crop((0, 200, 1080, 1640))
c.save(out.replace(".png", "_3x4.png"))
print("cover ok")
