# -*- coding: utf-8 -*-
"""河道：大尺度用 Natural Earth 10m（公有领域）；玉璧一带的汾河，用 Natural Earth 的走向做引导，在本地高程上找谷底最低线并平滑（今河道，示意）。"""
import os, json, math, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ne = json.load(open(f"{ROOT}/cache/ne_rivers.geojson"))
KEEP = {'Huang': '黄河', 'Fen': '汾水', 'Wei': '渭水', 'Luo': '洛水', 'Yi': '伊水', 'Zhang': '漳水', 'Qin': '沁水', 'Jing': '泾水', 'Hai': '海河', 'Huai': '淮水', 'Han': '汉水', 'Sanggan': '桑干河', 'Hudi': '滹沱', 'Dan': '丹水'}
out = {}
for f in ne['features']:
    p = f['properties']; nm = p.get('name')
    if nm not in KEEP: continue
    g = f['geometry']; cs = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
    for c in cs:
        c = [(round(x, 4), round(y, 4)) for x, y in c if 103 <= x <= 120 and 30 <= y <= 42.5]
        if len(c) > 2: out.setdefault(KEEP[nm], []).append(c)
json.dump(out, open(f"{ROOT}/assets/rivers_macro.json", "w"), ensure_ascii=False)
print({k: sum(len(c) for c in v) for k, v in out.items()})
# --- 本地汾河 ---
m = json.load(open(f"{ROOT}/assets/local.json")); H = np.load(f"{ROOT}/cache/local_dem.npy"); S = m['S']; sc = m['scale'] / S
def to_px(lon, lat):
    X = (lon + 180) / 360; Y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
    return (X - m['mx0']) * sc, (Y - m['my0']) * sc
def to_ll(px, py):
    X = px / sc + m['mx0']; Y = py / sc + m['my0']
    return X * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y))))
fen = [c for c in out['汾水'] if any(110.6 < x < 111.3 and 35.3 < y < 35.8 for x, y in c)]
pts = [p for c in fen for p in c if 110.6 < p[0] < 111.3]
pts.sort()
xs = np.array([to_px(*p)[0] for p in pts]); ys = np.array([to_px(*p)[1] for p in pts])
h, w = H.shape; res = []
Hs = H.copy()
for x in range(0, w):
    yg = np.interp(x, xs, ys); lo, hi = int(max(0, yg - 60)), int(min(h - 1, yg + 60))
    col = Hs[lo:hi, x]; k = int(np.argmin(col)); res.append(lo + k)
res = np.array(res, float)
k = 41; pad = np.pad(res, k, mode='edge'); sm = np.convolve(pad, np.ones(k) / k, 'same')[k:-k]
k2 = 25; pad = np.pad(sm, k2, mode='edge'); sm = np.convolve(pad, np.ones(k2) / k2, 'same')[k2:-k2]
line = [to_ll(x, sm[x]) for x in range(0, w, 6)]
json.dump([(round(a, 5), round(b, 5)) for a, b in line], open(f"{ROOT}/assets/fen_local.json", "w"))
print('fen local pts', len(line), line[0], line[-1])
