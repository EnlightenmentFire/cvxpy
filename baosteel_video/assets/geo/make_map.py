"""Clip Natural Earth (public domain) land + Yangtze to East Asia and emit projected SVG paths as JS."""
import json, math
LON0, LON1, LAT0, LAT1 = 110.0, 146.0, 24.0, 47.0
K = math.cos(math.radians(36.0))
def proj(lon, lat):  # equirectangular, units = degrees of latitude; y down
    return ((lon - LON0) * K, (LAT1 - lat))
def clip_ring(ring):
    # Sutherland–Hodgman against bbox
    def clip(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ia and ib: out.append(b)
            elif ia and not ib: out.append(inter(a, b))
            elif not ia and ib: out.append(inter(a, b)); out.append(b)
        return out
    def ix(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def iy(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    pts = [tuple(p[:2]) for p in ring]
    m = 3.0
    for inside, inter in [(lambda p: p[0] >= LON0 - m, ix(LON0 - m)), (lambda p: p[0] <= LON1 + m, ix(LON1 + m)),
                          (lambda p: p[1] >= LAT0 - m, iy(LAT0 - m)), (lambda p: p[1] <= LAT1 + m, iy(LAT1 + m))]:
        if not pts: break
        pts = clip(pts, inside, inter)
    return pts
def simplify(pts, eps):
    # Douglas-Peucker
    if len(pts) < 3: return pts
    import sys; sys.setrecursionlimit(100000)
    def dp(a, b):
        if b <= a + 1: return []
        ax, ay = pts[a]; bx, by = pts[b]; dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy) or 1e-12
        best, bi = 0, -1
        for i in range(a + 1, b):
            d = abs((pts[i][0] - ax) * dy - (pts[i][1] - ay) * dx) / L
            if d > best: best, bi = d, i
        if best > eps: return dp(a, bi) + [bi] + dp(bi, b)
        return []
    idx = [0] + dp(0, len(pts) - 1) + [len(pts) - 1]
    return [pts[i] for i in idx]
land = json.load(open('assets/geo/ne_10m_land.geojson'))
paths = []
for f in land['features']:
    g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        ring = poly[0]
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        if max(xs) < LON0 or min(xs) > LON1 or max(ys) < LAT0 or min(ys) > LAT1: continue
        pts = clip_ring(ring)
        if len(pts) < 4: continue
        pp = simplify([proj(*p) for p in pts], 0.012)
        if len(pp) < 4: continue
        # drop tiny islands
        area = abs(sum(pp[i-1][0]*pp[i][1]-pp[i][0]*pp[i-1][1] for i in range(len(pp))))/2
        if area < 0.004: continue
        paths.append('M' + 'L'.join(f'{x:.3f},{y:.3f}' for x, y in pp) + 'Z')
riv = json.load(open('assets/geo/ne_10m_rivers_lake_centerlines.geojson'))
rpaths = []
for f in riv['features']:
    nm = (f['properties'].get('name') or '') + '|' + (f['properties'].get('name_en') or '')
    if 'Chang Jiang' in nm or 'Yangtze' in nm:
        g = f['geometry']
        lines = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
        for ln in lines:
            pts = [proj(p[0], p[1]) for p in ln if LON0 <= p[0] <= LON1]
            pts = simplify(pts, 0.01)
            if len(pts) > 1: rpaths.append('M' + 'L'.join(f'{x:.3f},{y:.3f}' for x, y in pts))
places = {'anshan': (122.99, 41.11), 'baoshan': (121.49, 31.41), 'tokyo': (139.76, 35.68), 'kimitsu': (139.90, 35.33),
          'beijing': (116.40, 39.90), 'kyoto': (135.77, 35.01), 'wuhan': (114.30, 30.59)}
out = {'land': ' '.join(paths), 'yangtze': ' '.join(rpaths), 'places': {k: proj(*v) for k, v in places.items()},
       'w': (LON1 - LON0) * K, 'h': LAT1 - LAT0}
open('render/mapdata.js', 'w').write('window.MAP=' + json.dumps(out) + ';')
print(len(paths), 'land paths', len(rpaths), 'river paths', len(out['land']) // 1024, 'KB')
