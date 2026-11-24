# 把若干静帧拼成一张缩略联系表，便于自查
import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
h = 800; w = int(h * 1080 / 1920)
im = Image.new("RGB", (w * len(files) + 6 * (len(files) - 1), h), (40, 40, 40))
for i, f in enumerate(files):
    im.paste(Image.open(f).convert("RGB").resize((w, h), Image.LANCZOS), (i * (w + 6), 0))
im.save(out, quality=88)
