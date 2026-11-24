import sys, json
import PIL.Image as I
from engine import *
from director import Director
d = Director("timeline.json")
segs = {s["id"]: s for s in d.tl["segments"]}
out = []
for spec in sys.argv[1:]:
    sid, i, frac = spec.split(":")
    ln = segs[sid]["lines"][int(i)]
    T = ln["t0"] + (ln["t1"] - ln["t0"]) * float(frac)
    s = new_surface(); c = s.getCanvas(); d.frame(c, T)
    out.append(I.fromarray(surface_to_rgb(s)).resize((540, 960), I.LANCZOS))
sheet = I.new("RGB", (545 * len(out), 960))
for k, im in enumerate(out): sheet.paste(im, (k * 545, 0))
sheet.save("test/show.jpg", quality=88)
