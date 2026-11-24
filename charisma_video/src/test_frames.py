import sys, json, time
import PIL.Image as I
from engine import *
from director import Director
d = Director("timeline.json")
tl = d.tl
# pick times: middle of a few lines in each segment
picks = []
for s in tl["segments"]:
    n = len(s["lines"])
    for i in sorted(set([0, n // 3, (2 * n) // 3, n - 1])):
        ln = s["lines"][i]
        picks.append((s["id"] + f"_{i}", (ln["t0"] + ln["t1"]) / 2))
sel = sys.argv[1] if len(sys.argv) > 1 else None
if sel:
    picks = [p for p in picks if p[0].startswith(sel)]
imgs = []
for name, T in picks:
    s = new_surface(); c = s.getCanvas()
    t0 = time.time(); d.frame(c, T); dt = time.time() - t0
    imgs.append((name, I.fromarray(surface_to_rgb(s)).resize((270, 480), I.LANCZOS), dt))
cols = 8
rows = (len(imgs) + cols - 1) // cols
sheet = I.new("RGB", (cols * 275, rows * 505), (0, 0, 0))
from PIL import ImageDraw
dr = ImageDraw.Draw(sheet)
for k, (n, im, dt) in enumerate(imgs):
    x, y = (k % cols) * 275, (k // cols) * 505
    sheet.paste(im, (x, y)); dr.text((x + 4, y + 484), f"{n} {dt*1000:.0f}ms", fill=(255, 255, 0))
sheet.save(f"test/sheet_{sel or 'all'}.jpg", quality=85)
print(len(imgs), "frames; mean ms", round(sum(i[2] for i in imgs) / len(imgs) * 1000))
