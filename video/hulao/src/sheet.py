import sys, glob
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
n = len(files); w, h = 540, 960
im = Image.new('RGB', (w * n, h))
for i, f in enumerate(files): im.paste(Image.open(f).resize((w, h), Image.LANCZOS), (i * w, 0))
im.save(out, quality=88)
