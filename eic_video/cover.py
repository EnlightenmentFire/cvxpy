"""Cover image (1080x1920 png + 3:4 crop) from the opening battle art with the episode title."""
import sys
from PIL import Image, ImageDraw
from art import *
import kit, shots_s0

img = new((0, 0, 0, 255))
g = kit.G(20.0, {"open": 0.0}, None, 20.0)
shots_s0.battle_open(img, g)
# darken lower part for the title block
ov = new(); d = ImageDraw.Draw(ov)
for y in range(1150, 1920):
    a = int(min(1, (y - 1150) / 300) * 200)
    d.line((0, y, W, y), fill=(0, 0, 0, a))
img.alpha_composite(ov)
kit.title_card(img, "一家公司", None, y=1330, size=120, color=WHITE)
kit.title_card(img, "怎么会有自己的军队和税收？", None, y=1480, size=72, color=GOLD_L)
kit.label(img, (W / 2, 1600), "东印度公司 1600–1874 · 权力与组织", size=36, color=IVORY)
img.convert("RGB").save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/cover.png")
img.convert("RGB").crop((0, 400, 1080, 1840)).resize((1080, 1440)).save("/tmp/claude-0/work/cover_3x4.png")
