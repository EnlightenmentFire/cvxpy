# -*- coding: utf-8 -*-
"""地形瓦片（terrarium）→ 晕渲底图。三级：z6 全国、z8 中景、z9 荆益近景。"""
import numpy as np, math, json, glob, os
from PIL import Image
from scipy import ndimage as ndi
D = '/home/user/work/dem/'

def mosaic(z):
    fs = glob.glob(D + f'tiles/{z}_*_*.png')
    xs = sorted({int(os.path.basename(f).split('_')[1]) for f in fs}); ys = sorted({int(os.path.basename(f).split('_')[2].split('.')[0]) for f in fs})
    H = np.zeros(((ys[-1] - ys[0] + 1) * 256, (xs[-1] - xs[0] + 1) * 256), np.float32)
    for f in fs:
        _, x, y = os.path.basename(f)[:-4].split('_'); x = int(x); y = int(y)
        a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        H[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return H, xs[0], ys[0]

def ramp(h):
    stops = [(-50, (26, 34, 42)), (0, (46, 52, 46)), (80, (56, 60, 50)), (300, (72, 72, 56)), (800, (96, 88, 66)),
             (1600, (120, 104, 80)), (2800, (140, 124, 100)), (4200, (162, 152, 136)), (5600, (196, 192, 186))]
    xs = [s[0] for s in stops]; out = np.zeros(h.shape + (3,), np.float32)
    for c in range(3): out[..., c] = np.interp(h, xs, [s[1][c] for s in stops])
    return out

def shade(H, z, exag):
    mpp = 156543.03 * math.cos(math.radians(31)) / 2 ** z
    gy, gx = np.gradient(H * exag / mpp)
    def hs(az, alt=45):
        az = math.radians(az); alt = math.radians(alt)
        lx = math.sin(az) * math.cos(alt); ly = -math.cos(az) * math.cos(alt); lz = math.sin(alt)
        n = np.sqrt(gx * gx + gy * gy + 1)
        return np.clip((-gx * lx - gy * ly + lz) / n, 0, 1)
    return 0.6 * hs(315) + 0.25 * hs(270) + 0.15 * hs(0)

def build(z, exag, out, feather=0, blur=0.8):
    H, x0, y0 = mosaic(z)
    H = np.where(H < -200, -200, H)
    Hs = ndi.gaussian_filter(H, blur)
    s = shade(Hs, z, exag)
    rel = s - math.sin(math.radians(45))
    rgb = ramp(Hs) * (1 + 1.5 * rel[..., None])
    loc = Hs - ndi.gaussian_filter(Hs, 12)
    rgb *= (1 + np.clip(loc / 900, -0.22, 0.25))[..., None]
    sea = (H <= 0.5) & (ndi.uniform_filter((H <= 0.5).astype(np.float32), 9) > 0.95)
    rgb[sea] = (20, 28, 36)
    rng = np.random.default_rng(3)
    rgb += (ndi.gaussian_filter(rng.normal(0, 1, H.shape), 1.2) * 5 + rng.normal(0, 1, H.shape) * 1.5)[..., None]
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    if feather:
        a = np.ones(H.shape, np.float32)
        for k in range(feather):
            v = k / feather; a[k, :] = np.minimum(a[k, :], v); a[-1 - k, :] = np.minimum(a[-1 - k, :], v); a[:, k] = np.minimum(a[:, k], v); a[:, -1 - k] = np.minimum(a[:, -1 - k], v)
        rgb = np.dstack([rgb, (a * 255).astype(np.uint8)])
    Image.fromarray(rgb).save(D + out)
    json.dump({'z': z, 'x0': x0, 'y0': y0, 'w': H.shape[1], 'h': H.shape[0]}, open(D + out + '.json', 'w'))
    print(out, rgb.shape)

if __name__ == '__main__':
    build(6, 3.0, 'base6.png', blur=0.6)
    build(8, 2.0, 'base8.png', feather=120)
    build(9, 1.5, 'base9.png', feather=160)


def bake_rivers(name, wscale):
    """把河流、湖泊烘进底图（按该级像素坐标）。"""
    import skia, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data import RIVERS, LAKES
    from geo import merc
    m = json.load(open(D + name + '.json')); im = np.asarray(Image.open(D + name).convert('RGBA')).copy()
    a = im[..., 3:4].astype(np.float32) / 255
    pm = im.copy(); pm[..., :3] = (im[..., :3] * a).astype(np.uint8)
    s = skia.Surface(pm.shape[1], pm.shape[0]); c = s.getCanvas()
    c.drawImage(skia.Image.fromarray(np.ascontiguousarray(pm), skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), 0, 0)
    n = 256 * 2 ** m['z']
    def P(lon, lat):
        x, y = merc(lon, lat); return x * n - m['x0'] * 256, y * n - m['y0'] * 256
    for poly in LAKES:
        pth = skia.Path(); [pth.moveTo(*P(*q)) if i == 0 else pth.lineTo(*P(*q)) for i, q in enumerate(poly)]; pth.close()
        c.drawPath(pth, skia.Paint(AntiAlias=True, Color=skia.Color(38, 62, 78, 235)))
        c.drawPath(pth, skia.Paint(AntiAlias=True, Color=skia.Color(110, 150, 170, 150), Style=skia.Paint.kStroke_Style, StrokeWidth=1.2 * wscale))
    for pts, wcls, nm in sorted(RIVERS, key=lambda r: r[1]):
        if wcls < 0.6 and m['z'] < 8: continue
        pth = skia.Path()
        for i, q in enumerate(pts):
            pth.moveTo(*P(*q)) if i == 0 else pth.lineTo(*P(*q))
        w = max(0.7, wcls * wscale)
        p = skia.Paint(AntiAlias=True, Color=skia.Color(20, 30, 36, 120), Style=skia.Paint.kStroke_Style, StrokeWidth=w + 1.6 * wscale / 1.5)
        p.setStrokeJoin(skia.Paint.kRound_Join); p.setStrokeCap(skia.Paint.kRound_Cap); c.drawPath(pth, p)
        p = skia.Paint(AntiAlias=True, Color=skia.Color(96, 140, 166, 235 if wcls >= 1 else 170), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
        p.setStrokeJoin(skia.Paint.kRound_Join); p.setStrokeCap(skia.Paint.kRound_Cap); c.drawPath(pth, p)
    out = s.makeImageSnapshot().toarray()  # BGRA premul on little endian? use PIL via encode
    s.makeImageSnapshot().save(D + name.replace('.png', '_r.png'))
    json.dump(m, open(D + name.replace('.png', '_r.png') + '.json', 'w'))
    print('baked', name)
