"""Cover: the hook image (bowl turned to fire) + title. Writes 1080x1920 and 1080x1440 PNGs and a 120px check."""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render
from art import text_img, font, paste, seal, W, H

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{WORK}/cover"
os.makedirs(OUT, exist_ok=True)

R = render.Renderer()
s, shot = R.shots[0]
a02 = R.lines["a02"]
T = a02["t0"] + 0.66 * (a02["t1"] - a02["t0"]) + 0.9      # just after the fire flash, wide
img = shot.bg().copy(); shot.dyn(img, T)
import art
img *= art.vignette()
pil = art.to_pil(img)
z, fx, fy = 1.45, shot.bx + 90, shot.by - 120
cw, ch = W / z, H / z
x0 = min(max(fx - cw / 2, 0), W - cw); y0 = min(max(fy - ch / 2, 0), H - ch)
pil = pil.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
# darken top for the title
grad = Image.linear_gradient("L").resize((W, H)).transpose(Image.FLIP_TOP_BOTTOM)
dark = Image.new("RGB", (W, H), (4, 4, 8))
pil = Image.composite(dark, pil, grad.point(lambda v: int(max(0, v - 110) * 1.2)))
t1 = text_img("神通第一的弟子", font("serif_k", 112), fill=(246, 236, 214), stroke=2, stroke_fill=(0, 0, 0))
t2 = text_img("为什么救不了\n自己的母亲？", font("serif_k", 132), fill=(255, 196, 110), stroke=2, stroke_fill=(0, 0, 0), spacing=20)
t3 = text_img("目连救母 · 盂兰盆 · 中元节的来历", font("kai", 52), fill=(230, 220, 200))
paste(pil, t1, W / 2 - t1.width / 2, 250)
paste(pil, t2, W / 2 - t2.width / 2, 400)
paste(pil, t3, W / 2 - t3.width / 2, 1560)
paste(pil, seal("盂蘭", 110), W - 190, 1700)
pil.save(f"{OUT}/cover_1080x1920.png")
c34 = pil.crop((0, 160, 1080, 1600))
c34.save(f"{OUT}/cover_1080x1440.png")
c34.resize((120, 160), Image.LANCZOS).resize((360, 480), Image.NEAREST).save(f"{OUT}/cover_120px_check.png")
print("cover written", OUT)
