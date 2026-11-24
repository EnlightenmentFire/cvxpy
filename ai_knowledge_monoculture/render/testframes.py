"""Render one frame per sentence (at a chosen fraction of it) and tile them into contact sheets."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline  # noqa: E402
import video  # noqa: E402
from engine import surface_to_np  # noqa: E402

voice, robot, segkeys, out = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4]
frac = float(sys.argv[5]) if len(sys.argv) > 5 else 0.7
segs, total = timeline.build(voice, robot, None, allow_missing=True)
fr = video.Frame(segs)
f = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 22, index=2)
for key in segkeys:
    seg = [s for s in segs if s.key == key][0]
    tiles = []
    for e in seg.events:
        t = e.start + (e.end - e.start) * frac
        fr.draw(t)
        im = Image.fromarray(surface_to_np(fr.surf)).resize((216, 384), Image.Resampling.LANCZOS)
        tiles.append((e.id, im))
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 226 + 10, rows * 420 + 10), (18, 20, 26))
    d = ImageDraw.Draw(sheet)
    for i, (lid, im) in enumerate(tiles):
        x, y = 10 + (i % cols) * 226, 10 + (i // cols) * 420
        sheet.paste(im, (x, y))
        d.text((x, y + 388), lid, font=f, fill=(200, 205, 215))
    p = os.path.join(out, f"test_{key}.jpg")
    sheet.save(p, quality=85)
    print(p)
