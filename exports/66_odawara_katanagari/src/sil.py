"""Procedural silhouettes and atmosphere: riders, camels, dust storm, walls, cliffs."""
import math, functools
import numpy as np, skia
from scipy import ndimage as ndi
from engine import *

def _leg(path, hx, hy, ang1, ang2, l1, l2):
    kx, ky = hx + math.sin(ang1) * l1, hy + math.cos(ang1) * l1
    fx, fy = kx + math.sin(ang2) * l2, ky + math.cos(ang2) * l2
    return (hx, hy), (kx, ky), (fx, fy)

def horse_rider(c, x, y, s=1.0, ph=0.0, color=INK, a=1.0, flip=False, rider=True, banner=False, gallop=True, pose=None):
    """x,y = ground contact centre. ph = gait phase (radians). pose: 'leap' stretches legs."""
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s)
    p = paint(color, a); ps = paint(color, a, stroke=7, cap=skia.Paint.kRound_Cap)
    bob = math.sin(ph * 2) * 3 if gallop else 0
    by = -62 + bob
    # body
    c.drawOval(skia.Rect(-46, by - 17, 44, by + 17), p)
    # neck + head
    nk = skia.Path(); nk.moveTo(26, by - 10); nk.lineTo(48, by - 44); nk.lineTo(60, by - 46); nk.lineTo(74, by - 30)
    nk.lineTo(70, by - 24); nk.lineTo(56, by - 30); nk.lineTo(44, by + 4); nk.close(); c.drawPath(nk, p)
    c.drawLine(50, by - 46, 52, by - 54, paint(color, a, stroke=4))  # ear
    # tail
    tl = skia.Path(); tl.moveTo(-44, by - 8); tl.quadTo(-70, by - 4 + bob, -74, by + 22); tl.quadTo(-60, by + 6, -44, by + 4); tl.close(); c.drawPath(tl, p)
    # legs
    if pose == "leap":
        legs = [(30, 1.1, 0.4), (20, 0.9, 0.2), (-30, -0.9, -0.3), (-38, -1.1, -0.5)]
        for hx, a1, a2 in legs:
            _, k, f = _leg(None, hx, by + 8, a1, a2 + a1 * 0.3, 26, 26)
            pth = skia.Path(); pth.moveTo(hx, by + 8); pth.lineTo(*k); pth.lineTo(*f); c.drawPath(pth, ps)
    else:
        for i, hx in enumerate([30, 22, -30, -38]):
            off = [0, 0.6, math.pi, math.pi + 0.6][i] if gallop else [0, math.pi, math.pi, 0][i]
            sw = math.sin(ph + off)
            a1 = sw * (0.55 if gallop else 0.35); a2 = a1 + (0.5 + 0.5 * math.cos(ph + off)) * (0.7 if i < 2 else -0.5) * (1 if gallop else 0.5)
            _, k, f = _leg(None, hx, by + 8, a1, a2, 26, 28)
            pth = skia.Path(); pth.moveTo(hx, by + 8); pth.lineTo(*k); pth.lineTo(*f); c.drawPath(pth, ps)
    if rider:
        ry = by - 14
        tr = skia.Path(); tr.moveTo(-14, ry); tr.lineTo(6, ry); tr.lineTo(4, ry - 40); tr.lineTo(-8, ry - 42); tr.close(); c.drawPath(tr, p)
        c.drawCircle(-1, ry - 52, 10, p)
        hat = skia.Path(); hat.moveTo(-12, ry - 54); hat.lineTo(10, ry - 54); hat.lineTo(-1, ry - 70); hat.close(); c.drawPath(hat, p)
        c.drawLine(-4, ry - 30, 22, ry - 18, paint(color, a, stroke=5))
        if banner:
            c.drawLine(-12, ry + 6, -18, ry - 120, paint(color, a, stroke=3.5))
            fl = skia.Path(); fl.moveTo(-18, ry - 120); w = math.sin(ph * 1.3) * 6
            fl.quadTo(-40, ry - 112 + w, -58, ry - 116); fl.lineTo(-52, ry - 100); fl.quadTo(-36, ry - 98 - w, -17, ry - 96); fl.close()
            c.drawPath(fl, p)
        else:
            c.drawLine(-14, ry - 10, -26, ry - 96, paint(color, a, stroke=3))  # spear
    c.restore()

def camel(c, x, y, s=1.0, ph=0.0, color=INK, a=1.0, flip=False, load=True):
    if a <= 0: return
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s)
    p = paint(color, a); ps = paint(color, a, stroke=7)
    by = -78 + math.sin(ph * 2) * 1.5
    c.drawOval(skia.Rect(-48, by - 18, 44, by + 20), p)
    h = skia.Path(); h.moveTo(-30, by - 8); h.quadTo(-10, by - 52, 14, by - 8); h.close(); c.drawPath(h, p)
    nk = skia.Path(); nk.moveTo(36, by - 6); nk.quadTo(62, by + 4, 66, by - 34); nk.lineTo(70, by - 52); nk.lineTo(88, by - 50)
    nk.lineTo(88, by - 42); nk.lineTo(76, by - 40); nk.quadTo(74, by + 16, 40, by + 12); nk.close(); c.drawPath(nk, p)
    if load:
        c.drawRect(skia.Rect(-34, by - 30, -6, by + 6), p); c.drawRect(skia.Rect(0, by - 22, 22, by + 6), p)
    for i, hx in enumerate([30, 22, -32, -40]):
        sw = math.sin(ph + [0, math.pi, math.pi, 0][i]) * 0.3
        pth = skia.Path(); pth.moveTo(hx, by + 14); pth.lineTo(hx + math.sin(sw) * 30, by + 44); pth.lineTo(hx + math.sin(sw) * 34 + 2, by + 78)
        c.drawPath(pth, ps)
    c.restore()

def person(c, x, y, s=1.0, color=INK, a=1.0, arm=0.0):
    c.save(); c.translate(x, y); c.scale(s, s); p = paint(color, a)
    b = skia.Path(); b.moveTo(-14, 0); b.lineTo(14, 0); b.lineTo(9, -70); b.lineTo(-9, -70); b.close(); c.drawPath(b, p)
    c.drawCircle(0, -84, 12, p)
    c.drawLine(8, -62, 8 + 26 * math.cos(arm), -62 - 26 * math.sin(arm), paint(color, a, stroke=6))
    c.restore()

# --------------------------------------------------------------- textures
@functools.lru_cache(maxsize=8)
def dust_tex(seed, w=1080, h=960, sigma=(18, 60), warm=(190, 140, 80)):
    rng = np.random.default_rng(seed)
    n = np.zeros((h, w), np.float32)
    for k, sg in enumerate([sigma[1], sigma[0], sigma[0] / 3]):
        layer = ndi.gaussian_filter(rng.normal(0, 1, (h, w)), (sg * 0.5, sg), mode="wrap")
        n += layer / (layer.std() + 1e-6) * [1.0, 0.5, 0.25][k]
    n = (n - n.min()) / (n.max() - n.min())
    al = np.clip((n - 0.35) * 1.8, 0, 1)
    yy = np.linspace(0, 1, h)[:, None]
    al = al * (np.sin(np.pi * yy) ** 1.5)
    rgb = np.zeros((h, w, 4), np.uint8)
    rgb[..., 0] = warm[0]; rgb[..., 1] = warm[1]; rgb[..., 2] = warm[2]; rgb[..., 3] = (al * 255).astype(np.uint8)
    # premultiply
    rgb[..., :3] = (rgb[..., :3].astype(np.float32) * al[..., None]).astype(np.uint8)
    return skia.Image.fromarray(rgb, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)

def dust_layer(c, seed, t, speed, y0, hgt, a, scale=1.0):
    img = dust_tex(seed)
    off = (t * speed) % W
    smp = skia.SamplingOptions(skia.FilterMode.kLinear)
    p = skia.Paint(); p.setAlphaf(clamp(a))
    for k in (-1, 0, 1):
        c.drawImageRect(img, skia.Rect(off + k * W, y0, off + (k + 1) * W, y0 + hgt), smp, p)

def sky(c, top=(40, 28, 20), mid=(150, 96, 48), hor=(210, 150, 80), hy=1150, sun=None):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, hy)], [col(top), col(mid), col(hor)], [0, 0.6, 1]))
    c.drawRect(skia.Rect(0, 0, W, hy + 2), p)
    if sun:
        sx, sy, sr, sa = sun
        c.drawCircle(sx, sy, sr * 3.2, paint((255, 200, 120), 0.25 * sa, blur=60))
        c.drawCircle(sx, sy, sr, paint((255, 228, 170), 0.85 * sa, blur=6))

def ground(c, hy=1150, top=(70, 48, 30), bot=(18, 14, 10)):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, hy), skia.Point(0, H)], [col(top), col(bot)]))
    c.drawRect(skia.Rect(0, hy, W, H), p)
