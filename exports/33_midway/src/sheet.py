import sys, glob
from PIL import Image
fs = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(f).convert("RGB").resize((360, 640)) for f in fs]
cols = min(5, len(ims)); rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * 364, rows * 644), (40, 40, 40))
for i, im in enumerate(ims):
    S.paste(im, ((i % cols) * 364, (i // cols) * 644))
S.save(out, quality=85)
