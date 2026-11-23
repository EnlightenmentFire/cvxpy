"""地图：真实高程的暗色晕渲底图 + 相机 + 屏幕空间的海岸线、河流、地名。

投影：Web 墨卡托。所有坐标统一用 z8 全局像素 (gx, gy)。
地名经纬度见 PLACES，均为今地（括注明代名称）。
"""
import os
import pickle

import cv2
import numpy as np

from gfx import W, H, rgb, text_sprite, blit, add_glow, smooth

Z8 = 65536.0
ORIGIN = {'z8': (199 * 256, 102 * 256, 1.0), 'z7': (188 * 256, 98 * 256, 2.0)}  # 左上角 gx, gy, 每个纹素合多少 z8 像素

# ── 地名（经度, 纬度）──
PLACES = {
    '龙场': (106.59, 26.84),      # 龙场驿，今贵州修文县龙场镇
    '贵阳': (106.71, 26.58),
    '余姚': (121.15, 30.05),
    '南昌': (115.86, 28.68),      # 洪都
    '广信': (117.94, 28.45),      # 广信府，今上饶
    '白鹿洞': (116.03, 29.50),    # 白鹿洞书院，庐山五老峰南麓
    '漳州': (117.65, 24.51),
    '赣州': (114.93, 25.83),
    '横水': (114.31, 25.68),      # 今崇义县治横水镇
    '浰头': (114.75, 24.55),      # 今和平县浰源一带
    '和平': (114.94, 24.44),
    '崇义': (114.31, 25.68),
    '南安': (114.36, 25.40),      # 南安府治，今大余
    '思恩': (108.20, 23.50),      # 思恩府（今马山、武鸣一带）
    '田州': (106.92, 23.74),      # 今田阳
    '南宁': (108.32, 22.82),
    '八寨': (108.70, 23.75),      # 今上林、忻城一带
    '断藤峡': (110.00, 23.50),    # 黔江下游，今桂平西北
    '汀州': (116.36, 25.83),      # 今长汀
    '南岭': (112.60, 25.20),
    '武夷山': (117.60, 27.20),
    '苗岭': (107.60, 26.20),
}

# 龙场九驿（示意）：龙场、陆广、谷里、水西、奢香、金鸡、阁鸦、归化、毕节
NINE_POSTS = [(106.59, 26.84), (106.42, 26.98), (106.22, 27.04), (106.03, 27.03), (105.84, 27.09),
              (105.68, 27.14), (105.52, 27.19), (105.40, 27.24), (105.29, 27.30)]


def lonlat_to_g(lon, lat):
    lon = np.asarray(lon, np.float64)
    lat = np.radians(np.asarray(lat, np.float64))
    gx = (lon + 180.0) / 360.0 * Z8
    gy = (1 - np.log(np.tan(lat) + 1 / np.cos(lat)) / np.pi) / 2 * Z8
    return gx, gy


# ── 底图纹理 ──
def _hillshade(elev, px_m, exag=5.0):
    e = cv2.GaussianBlur(elev, (0, 0), 0.9)
    dzdx = cv2.Sobel(e, cv2.CV_32F, 1, 0, ksize=3) / (8 * px_m) * exag
    dzdy = cv2.Sobel(e, cv2.CV_32F, 0, 1, ksize=3) / (8 * px_m) * exag
    out = np.zeros_like(e)
    for az, w in ((315, 0.65), (20, 0.20), (250, 0.15)):
        alt = np.radians(42)
        a = np.radians(az)
        lx, ly, lz = np.sin(a) * np.cos(alt), -np.cos(a) * np.cos(alt), np.sin(alt)
        n = 1.0 / np.sqrt(dzdx ** 2 + dzdy ** 2 + 1)
        sh = (-dzdx * lx - dzdy * ly + lz) * n
        out += w * np.clip(sh, 0, 1)
    return out


def build_textures(work):
    """由高程生成底图与掩膜，缓存到 work/map/。"""
    for name in ('z8', 'z7'):
        dst = f'{work}/map/tex_{name}.npy'
        if os.path.exists(dst):
            continue
        elev = np.load(f'{work}/map/elev_{name}.npy')
        land = (elev > 0.5).astype(np.float32)
        land = cv2.GaussianBlur(land, (0, 0), 0.7)
        e = np.clip(elev, 0, None)
        px_m = 550.0 * ORIGIN[name][2]
        sh = _hillshade(e, px_m, exag=5.0 if name == 'z8' else 7.0)
        # 高程色带（很克制的冷灰）
        stops = np.array([0, 300, 1000, 2500, 4500, 6500], np.float32)
        cols = np.array([[0.046, 0.060, 0.074], [0.066, 0.084, 0.102], [0.100, 0.122, 0.145],
                         [0.150, 0.176, 0.203], [0.215, 0.242, 0.270], [0.270, 0.295, 0.320]], np.float32)
        base = np.stack([np.interp(e, stops, cols[:, c]) for c in range(3)], -1).astype(np.float32)
        flat = np.sin(np.radians(42))
        lum = 0.30 + 1.05 * (sh / flat)                       # 平地约 1.35 -> 归一
        lum = np.clip(lum / 1.35, 0.25, 1.9)
        tex = base * lum[..., None]
        sea = rgb('#04070a')
        tex = tex * land[..., None] + sea * (1 - land[..., None])
        np.save(dst, tex.astype(np.float32))
        hi = smooth((e - 240.0) / 120.0) * land                # 海拔约 300 米以上
        np.save(f'{work}/map/hi_{name}.npy', (hi * 255).astype(np.uint8))
        low = (1 - smooth((e - 200.0) / 150.0)) * land          # 低地
        np.save(f'{work}/map/low_{name}.npy', (low * 255).astype(np.uint8))
        np.save(f'{work}/map/land_{name}.npy', (land * 255).astype(np.uint8))
    vec = f'{work}/map/vectors.pkl'
    if not os.path.exists(vec):
        import shapefile
        out = {'coast': [], 'rivers': [], 'lakes': []}
        bbox = (84.0, 5.0, 130.0, 39.5)

        def keep(pts):
            a = np.asarray(pts, np.float64)
            m = (a[:, 0] > bbox[0]) & (a[:, 0] < bbox[2]) & (a[:, 1] > bbox[1]) & (a[:, 1] < bbox[3])
            return a if m.sum() >= 2 else None

        def parts(shape):
            idx = list(shape.parts) + [len(shape.points)]
            for i in range(len(idx) - 1):
                yield shape.points[idx[i]:idx[i + 1]]

        r = shapefile.Reader(f'{work}/map/ne_10m_coastline/ne_10m_coastline.shp')
        for s in r.shapes():
            for p in parts(s):
                a = keep(p)
                if a is not None:
                    out['coast'].append(np.stack(lonlat_to_g(a[:, 0], a[:, 1]), -1).astype(np.float32))
        r = shapefile.Reader(f'{work}/map/ne_10m_rivers_lake_centerlines/ne_10m_rivers_lake_centerlines.shp')
        fields = [f[0] for f in r.fields[1:]]
        for sr in r.shapeRecords():
            rec = dict(zip(fields, sr.record))
            rank = rec.get('scalerank', 9)
            if rank is None or rank > 7:
                continue
            for p in parts(sr.shape):
                a = keep(p)
                if a is not None:
                    out['rivers'].append((int(rank), np.stack(lonlat_to_g(a[:, 0], a[:, 1]), -1).astype(np.float32)))
        r = shapefile.Reader(f'{work}/map/ne_10m_lakes/ne_10m_lakes.shp')
        fields = [f[0] for f in r.fields[1:]]
        for sr in r.shapeRecords():
            rec = dict(zip(fields, sr.record))
            if (rec.get('scalerank') or 9) > 4:
                continue
            for p in parts(sr.shape):
                a = keep(p)
                if a is not None and len(a) > 8:
                    out['lakes'].append(np.stack(lonlat_to_g(a[:, 0], a[:, 1]), -1).astype(np.float32))
        pickle.dump(out, open(vec, 'wb'))


class MapData:
    def __init__(self, work):
        build_textures(work)
        self.tex, self.hi, self.low, self.land = {}, {}, {}, {}
        for name in ('z8', 'z7'):
            t = np.load(f'{work}/map/tex_{name}.npy')
            self.tex[name] = [t, cv2.resize(t, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)]
            self.tex[name].append(cv2.resize(self.tex[name][1], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
            for store, key in ((self.hi, 'hi'), (self.low, 'low'), (self.land, 'land')):
                m = np.load(f'{work}/map/{key}_{name}.npy')
                store[name] = [m, cv2.resize(m, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)]
                store[name].append(cv2.resize(store[name][1], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
        self.vec = pickle.load(open(f'{work}/map/vectors.pkl', 'rb'))


class Camera:
    """center=(lon,lat), span=画面宽度对应的经度跨度。cy_frac 是中心点在画面中的纵向位置(0..1)。"""

    def __init__(self, lon, lat, span, cy_frac=0.5):
        self.gx, self.gy = [float(v) for v in lonlat_to_g(lon, lat)]
        self.span = float(span)
        self.cy_frac = cy_frac

    @property
    def scale(self):
        return W / (self.span / 360.0 * Z8)

    def to_screen(self, lon, lat):
        gx, gy = lonlat_to_g(lon, lat)
        return self.g_to_screen(gx, gy)

    def g_to_screen(self, gx, gy):
        s = self.scale
        return (gx - self.gx) * s + W / 2, (gy - self.gy) * s + H * self.cy_frac

    @staticmethod
    def lerp(a, b, u):
        c = Camera(0, 0, 1)
        c.gx = a.gx + (b.gx - a.gx) * u
        c.gy = a.gy + (b.gy - a.gy) * u
        c.span = float(np.exp(np.log(a.span) + (np.log(b.span) - np.log(a.span)) * u))
        c.cy_frac = a.cy_frac + (b.cy_frac - a.cy_frac) * u
        return c


def _warp(levels, name, cam, interp=cv2.INTER_LINEAR):
    ox, oy, k = ORIGIN[name]
    se = cam.scale * k
    lvl = 0
    while se < 0.62 and lvl < 2:
        se *= 2
        lvl += 1
    kk = k * (2 ** lvl)
    s = cam.scale * kk
    # 源像素 (u,v) -> g = o + (u+0.5)*kk -> 屏幕
    tx = (ox + 0.5 * kk - cam.gx) * cam.scale + W / 2
    ty = (oy + 0.5 * kk - cam.gy) * cam.scale + H * cam.cy_frac
    M = np.array([[s, 0, tx], [0, s, ty]], np.float32)
    return cv2.warpAffine(levels[lvl], M, (W, H), flags=interp, borderMode=cv2.BORDER_REPLICATE)


def _pick(cam):
    """宽视野用 z7，近处用 z8，中间过渡。返回 z8 的权重（标量）。"""
    return float(1 - smooth((cam.span - 21.0) / 5.0))


def _valid8(cam, feather=90.0):
    """z8 纹理在屏幕上的有效范围（逐像素 0..1，边缘羽化）；全在范围内时返回 None。"""
    ox, oy, _ = ORIGIN['z8']
    s = cam.scale
    xl, xr = (ox - cam.gx) * s + W / 2, (ox + 19 * 256 - cam.gx) * s + W / 2
    yt, yb = (oy - cam.gy) * s + H * cam.cy_frac, (oy + 13 * 256 - cam.gy) * s + H * cam.cy_frac
    if xl <= -feather and xr >= W + feather and yt <= -feather and yb >= H + feather:
        return None
    xs = np.arange(W, dtype=np.float32)
    ys = np.arange(H, dtype=np.float32)
    vx = np.clip((xs - xl) / feather, 0, 1) * np.clip((xr - xs) / feather, 0, 1)
    vy = np.clip((ys - yt) / feather, 0, 1) * np.clip((yb - ys) / feather, 0, 1)
    return (vy[:, None] * vx[None, :]).astype(np.float32)


def _blend(md_store, cam, to_float):
    w8 = _pick(cam)
    v = _valid8(cam) if w8 > 0.001 else None
    if w8 <= 0.001:
        return to_float(_warp(md_store['z7'], 'z7', cam))
    a = to_float(_warp(md_store['z8'], 'z8', cam))
    if w8 >= 0.999 and v is None:
        return a
    b = to_float(_warp(md_store['z7'], 'z7', cam))
    wgt = w8 if v is None else v * w8
    if a.ndim == 3 and not np.isscalar(wgt):
        wgt = wgt[..., None]
    return a * wgt + b * (1 - wgt)


def render_base(md, cam, hi=0.0, hi_color=(0.085, 0.092, 0.095)):
    """底图。hi: 海拔 300 米以上的提亮程度 0..1。"""
    img = _blend(md.tex, cam, lambda x: x)
    if hi > 0:
        mask = _blend(md.hi, cam, lambda x: x.astype(np.float32) / 255.0)
        lum = img.mean(-1, keepdims=True)
        img = img + (np.asarray(hi_color, np.float32) * (0.35 + lum * 9.0)) * (mask[..., None] * hi)
    return img


def warp_mask(md, cam, key):
    return _blend(getattr(md, key), cam, lambda x: x.astype(np.float32) / 255.0)


def draw_vectors(img, md, cam, coast=0.55, rivers=0.42):
    """屏幕空间描海岸线、主要河流（线宽恒定）。"""
    s = cam.scale
    off = np.array([W / 2 - cam.gx * s, H * cam.cy_frac - cam.gy * s], np.float32)
    layer = np.zeros((H, W), np.uint8)
    if rivers > 0:
        pl = []
        for rank, a in md.vec['rivers']:
            if cam.span > 30 and rank > 5:
                continue
            p = a * s + off
            if p[:, 0].max() < 0 or p[:, 0].min() > W or p[:, 1].max() < 0 or p[:, 1].min() > H:
                continue
            pl.append(np.round(p * 16).astype(np.int32))
        if pl:
            cv2.polylines(layer, pl, False, int(255 * rivers), 1, cv2.LINE_AA, shift=4)
        a = layer.astype(np.float32)[..., None] / 255.0
        img += a * (rgb('#3f5870') - img) * 0.9
        layer[:] = 0
    if coast > 0:
        pl = []
        for a in md.vec['coast']:
            p = a * s + off
            if p[:, 0].max() < 0 or p[:, 0].min() > W or p[:, 1].max() < 0 or p[:, 1].min() > H:
                continue
            pl.append(np.round(p * 16).astype(np.int32))
        if pl:
            cv2.polylines(layer, pl, False, int(255 * coast), 1, cv2.LINE_AA, shift=4)
        a = layer.astype(np.float32)[..., None] / 255.0
        img += a * (rgb('#56677a') - img)
    return img


def marker(img, cam, lon, lat, alpha=1.0, color=(0.93, 0.88, 0.76), r=4.0, glow=1.0, pulse=0.0, square=False):
    x, y = cam.to_screen(lon, lat)
    x, y = float(x), float(y)
    if alpha <= 0.003 or x < -50 or x > W + 50 or y < -50 or y > H + 50:
        return x, y
    add_glow(img, x, y, r * 5.5, color, 0.16 * glow * alpha * (1 + 0.5 * pulse))
    ov = np.zeros((H, W), np.uint8)
    c = (int(round(x * 16)), int(round(y * 16)))
    if square:
        rr = r * 1.15
        p0 = (int(round((x - rr) * 16)), int(round((y - rr) * 16)))
        p1 = (int(round((x + rr) * 16)), int(round((y + rr) * 16)))
        cv2.rectangle(ov, p0, p1, 255, 2, cv2.LINE_AA, shift=4)
    else:
        cv2.circle(ov, c, int(round(r * 16)), 255, -1, cv2.LINE_AA, shift=4)
        cv2.circle(ov, c, int(round(r * 2.9 * 16)), 110, 1, cv2.LINE_AA, shift=4)
    x0, x1 = max(int(x) - 40, 0), min(int(x) + 40, W)
    y0, y1 = max(int(y) - 40, 0), min(int(y) + 40, H)
    if x0 < x1 and y0 < y1:
        a = ov[y0:y1, x0:x1].astype(np.float32)[..., None] / 255.0 * alpha
        img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + np.asarray(color, np.float32) * a
    return x, y


def label(img, x, y, text, alpha=1.0, size=38, color=(0.86, 0.83, 0.76), dx=20, dy=-3, anchor='l',
          fontname='serif-m', spacing=3.0):
    if alpha <= 0.003:
        return
    sp, sw, sh = text_sprite(text, fontname, size, tuple(color), spacing, shadow=5.0)
    pad = int(size * 0.6) + 15
    if anchor == 'l':
        blit(img, sp, x + dx - pad, y + dy, alpha, 'l')
    elif anchor == 'r':
        blit(img, sp, x - dx + pad, y + dy, alpha, 'r')
    else:
        blit(img, sp, x + dx, y + dy, alpha, 'c')


def polyline(img, cam, pts_lonlat, alpha=1.0, color=(0.85, 0.80, 0.68), frac=1.0, dotted=False, thick=1):
    """按进度 frac 画折线（经纬度）。dotted: 只画节点小圆。"""
    if alpha <= 0.003:
        return
    pts = np.array([cam.to_screen(lo, la) for lo, la in pts_lonlat], np.float64)
    seg = np.sqrt((np.diff(pts, axis=0) ** 2).sum(1))
    total = seg.sum()
    target = total * float(np.clip(frac, 0, 1))
    out = [pts[0]]
    acc = 0.0
    for i, L in enumerate(seg):
        if acc + L <= target:
            out.append(pts[i + 1])
            acc += L
        else:
            u = (target - acc) / max(L, 1e-6)
            out.append(pts[i] + (pts[i + 1] - pts[i]) * u)
            break
    out = np.array(out)
    ov = np.zeros((H, W), np.uint8)
    if dotted:
        # 细虚线 + 节点
        d = 0.0
        for i in range(len(out) - 1):
            a, b = out[i], out[i + 1]
            L = np.linalg.norm(b - a)
            n = max(int(L / 9), 1)
            for k in range(n):
                if k % 2 == 0:
                    p = a + (b - a) * (k / n)
                    q = a + (b - a) * ((k + 1) / n)
                    cv2.line(ov, tuple(np.round(p * 16).astype(int)), tuple(np.round(q * 16).astype(int)), 200,
                             thick, cv2.LINE_AA, shift=4)
        for p in out[:-1] if frac < 1 else out:
            cv2.circle(ov, tuple(np.round(p * 16).astype(int)), int(2.6 * 16), 255, -1, cv2.LINE_AA, shift=4)
    else:
        cv2.polylines(ov, [np.round(out * 16).astype(np.int32)], False, 255, thick, cv2.LINE_AA, shift=4)
    a = ov.astype(np.float32)[..., None] / 255.0 * alpha
    img *= (1 - a)
    img += np.asarray(color, np.float32) * a


if __name__ == '__main__':
    import sys
    from PIL import Image
    work = sys.argv[1]
    md = MapData(work)
    tests = {
        'wide': (Camera(105.5, 22.0, 44, 0.5), 0.9),
        'south': (Camera(113.6, 26.3, 23.5, 0.47), 0.0),
        'south_hi': (Camera(113.6, 26.3, 23.5, 0.47), 1.0),
        'longchang': (Camera(106.6, 26.6, 9.0, 0.42), 0.6),
        'nangan': (Camera(115.2, 25.3, 8.5, 0.42), 0.6),
    }
    os.makedirs(work + '/out/maptest', exist_ok=True)
    for k, (cam, hi) in tests.items():
        img = render_base(md, cam, hi)
        img = draw_vectors(img, md, cam)
        for name in ('龙场', '余姚', '白鹿洞', '漳州', '赣州', '南昌', '广信'):
            lo, la = PLACES[name]
            x, y = marker(img, cam, lo, la)
            label(img, x, y, name)
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(f'{work}/out/maptest/{k}.png')
        print(k, 'scale %.3f' % cam.scale, img.mean())
