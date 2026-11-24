"""Procedural textures + province outline paths. All self-generated (no third-party imagery)."""
import json, numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(7)
def noise(h, w, scale):
    small = rng.random((h//scale+2, w//scale+2)).astype(np.float32)
    im = Image.fromarray((small*255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32)/255
def paper(path, base, amp=1.0, fibers=900, size=(1080, 1920)):
    w, h = size
    n = 0.5*noise(h, w, 2) + 0.3*noise(h, w, 8) + 0.2*noise(h, w, 64) + 0.25*noise(h, w, 300)
    n = (n - n.mean())/n.std()
    img = np.ones((h, w, 3), np.float32)*np.array(base, np.float32)
    img += n[..., None]*5.5*amp
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # fibers
    from PIL import ImageDraw
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for _ in range(fibers):
        x, y = rng.integers(0, w), rng.integers(0, h); L = rng.integers(6, 28); a = rng.random()*np.pi
        dark = rng.random() < 0.6
        col = (60, 40, 20, int(rng.integers(10, 34))) if dark else (255, 250, 235, int(rng.integers(12, 40)))
        d.line([(x, y), (x+L*np.cos(a), y+L*np.sin(a))], fill=col, width=1)
    im = Image.alpha_composite(im.convert('RGBA'), ov.filter(ImageFilter.GaussianBlur(0.5))).convert('RGB')
    im.save(path, quality=90)
paper('assets/paper.jpg', (232, 221, 198))
paper('assets/kraft.jpg', (186, 148, 96), amp=1.6, fibers=2600)
paper('assets/dark.jpg', (30, 25, 21), amp=0.5, fibers=500)
paper('assets/newsprint.jpg', (214, 205, 184), amp=1.2, fibers=1500)
# grain tile (neutral gray noise, used with overlay blend, low opacity)
g = rng.normal(128, 26, (512, 512)).clip(0, 255).astype(np.uint8)
Image.fromarray(g).filter(ImageFilter.GaussianBlur(0.6)).save('assets/grain.png')
# province outlines -> svg path (simplified), local equirect projection
def simplify(pts, eps):
    # Douglas-Peucker
    pts = np.asarray(pts, float)
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    st = [(0, len(pts)-1)]
    while st:
        a, b = st.pop()
        if b <= a+1: continue
        p, q = pts[a], pts[b]; seg = q-p; L = np.hypot(*seg) or 1e-12
        d = np.abs(seg[0]*(pts[a+1:b, 1]-p[1]) - seg[1]*(pts[a+1:b, 0]-p[0]))/L
        i = d.argmax()
        if d[i] > eps: k = a+1+i; keep[k] = True; st += [(a, k), (k, b)]
    return pts[keep]
out = {}
for code, name, places in [('340000', 'anhui', {'怀远': (117.20, 32.97), '芜湖': (118.38, 31.33), '合肥': (117.23, 31.82)}),
                           ('440000', 'guangdong', {'高要': (112.46, 23.03), '广州': (113.26, 23.13)})]:
    g = json.load(open(f'assets/geo/{code}.json'))['features'][0]['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rings = [np.array(p[0]) for p in polys]
    main = max(rings, key=len)
    lon0, lon1, lat0, lat1 = main[:, 0].min(), main[:, 0].max(), main[:, 1].min(), main[:, 1].max()
    k = np.cos(np.radians((lat0+lat1)/2))
    sx = 1000/max((lon1-lon0)*k, (lat1-lat0))
    proj = lambda P: np.c_[(P[:, 0]-lon0)*k*sx, (lat1-P[:, 1])*sx]
    d = ''
    for r in rings:
        if len(r) < 40 and r is not main: continue
        q = proj(r); m = len(q)//2
        pr = np.vstack([simplify(q[:m+1], 1.6), simplify(q[m:], 1.6)[1:]])
        if len(pr) < 4: continue
        d += 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in pr) + 'Z'
    out[name] = {'d': d, 'w': float((lon1-lon0)*k*sx), 'h': float((lat1-lat0)*sx),
                 'places': {n: [float(v) for v in proj(np.array([ll]))[0]] for n, ll in places.items()}}
    print(name, len(d), out[name]['w'], out[name]['h'], out[name]['places'])
open('assets/geo.js', 'w').write('window.GEO=' + json.dumps(out, ensure_ascii=False) + ';')
