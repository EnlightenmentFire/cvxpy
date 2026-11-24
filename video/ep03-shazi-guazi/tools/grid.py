import sys, json, subprocess
from PIL import Image, ImageDraw
t0, t1, n = float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]); name = sys.argv[1]
ts = [round(t0 + (t1-t0)*i/(n-1), 2) for i in range(n)]
subprocess.run(['node', 'tools/still.js', f'build/stills/{name}'] + [str(t) for t in ts], check=True)
per = 8; rows = (n+per-1)//per; tw, th = 252, 448
s = Image.new('RGB', (per*(tw+4), rows*(th+4)), 'white'); d = ImageDraw.Draw(s)
for i, t in enumerate(ts):
    im = Image.open(f"build/stills/{name}_{str(t).replace('.', '_')}.jpg").resize((tw, th), Image.LANCZOS)
    x, y = (i % per)*(tw+4), (i//per)*(th+4); s.paste(im, (x, y)); d.text((x+4, y+4), f'{t:.1f}', fill='yellow')
s.save(f'build/stills/grid_{name}.jpg', quality=80)
