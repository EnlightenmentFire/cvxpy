import sys, json, subprocess
from PIL import Image
# usage: sheet.py name cue1 cue2 ...  where cue = seconds or lineid[+off] or lineid@frac
TL = json.load(open('build/timeline.json'))
def T(c):
    try: return float(c)
    except ValueError: pass
    off = 0.0
    if '+' in c: c, o = c.split('+'); off = float(o)
    if '@' in c: i, f = c.split('@'); l = TL['lines'][i]; return l['s'] + (l['e']-l['s'])*float(f) + off
    if c.startswith('E:'): return TL['lines'][c[2:]]['e'] + off
    if c.startswith('S:'): return TL['secs'][c[2:]]['s'] + off
    return TL['lines'][c]['s'] + off
name = sys.argv[1]; ts = [round(T(c), 2) for c in sys.argv[2:]]
subprocess.run(['node', 'tools/still.js', f'build/stills/{name}'] + [str(t) for t in ts], check=True)
ims = [Image.open(f"build/stills/{name}_{str(t).replace('.', '_')}.jpg").resize((432, 768), Image.LANCZOS) for t in ts]
per = 4 if len(ims) > 4 else len(ims); rows = (len(ims)+per-1)//per
s = Image.new('RGB', (per*440, rows*776), 'white')
for i, im in enumerate(ims): s.paste(im, ((i % per)*440, (i//per)*776))
s.save(f'build/stills/sheet_{name}.jpg', quality=82); print(ts)
