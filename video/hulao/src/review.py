import sys, os
from PIL import Image
# 用法: review.py out.jpg t0 t1 step [cols]
out, t0, t1, step = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
ts = []; t = t0
while t < t1: ts.append(t); t += step
w, h = 405, 720; im = Image.new('RGB', (w * len(ts), h))
for i, t in enumerate(ts):
    p = f'cache/frames/f{int(round(t*30)):06d}.jpg'
    if os.path.exists(p): im.paste(Image.open(p).resize((w, h), Image.LANCZOS), (i * w, 0))
im.save(out, quality=85); print(out, [round(x, 1) for x in ts])
