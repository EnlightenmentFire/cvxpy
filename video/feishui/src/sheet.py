import sys, glob
from PIL import Image
fs = sorted(glob.glob(sys.argv[1] + '/t*.jpg')); out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
w, h = 240, 427
rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, h * rows))
for i, f in enumerate(fs): sheet.paste(Image.open(f).resize((w, h)), ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=85)
