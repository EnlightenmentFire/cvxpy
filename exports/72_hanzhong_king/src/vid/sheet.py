import sys, skia
import scenes
from scenes import S, E, T
from geo import W, H
from PIL import Image
ids = sys.argv[2:]; out = sys.argv[1]
s = skia.Surface(W, H); c = s.getCanvas(); ims = []
for b in ids:
    if b.startswith('@'): t = float(b[1:])
    else:
        if ':' in b: b, off = b.split(':'); off = float(off)
        else: off = None
        t = S(b) + (off if off is not None else (E(b) - S(b)) * 0.7)
    scenes.draw_frame(c, t, int(t * 25))
    a = s.toarray()[..., [2, 1, 0]] if False else s.makeImageSnapshot().toarray()
    im = Image.fromarray(a[..., :3][..., ::-1] if a.shape[2] == 4 else a).resize((360, 640)); ims.append(im)
Wd = Image.new('RGB', (360 * min(6, len(ims)), 640 * ((len(ims) + 5) // 6)))
for i, im in enumerate(ims): Wd.paste(im, ((i % 6) * 360, (i // 6) * 640))
Wd.save(out, quality=85)
