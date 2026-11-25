# -*- coding: utf-8 -*-
"""Scene 0: cold open at Plassey + rapid teaser beats."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from art import *
from kit import *

SC = 1.14   # oversize factor for camera moves
CW, CH = int(W * SC), int(H * SC)
HOR = int(1010 * SC)


def _cloud_noise(seed, w, h, scales=((90, 0.5), (30, 0.3), (10, 0.2))):
    rng = np.random.default_rng(seed)
    cl = np.zeros((h, w), np.float32)
    for sc_, w_ in scales:
        small = rng.random((h // sc_ + 2, w // sc_ + 2)).astype(np.float32)
        cl += np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 * w_
    return cl


@functools.lru_cache(maxsize=1)
def _sky():
    yy = np.arange(CH, dtype=np.float32)[:, None]
    d = (HOR - yy) / HOR                       # 1 at top, 0 at horizon
    top = np.array([10, 12, 18], np.float32); glowc = np.array([168, 150, 118], np.float32)
    k = np.clip(1 - d, 0, 1) ** 5
    col = top + (glowc - top) * k[..., None]
    arr = np.repeat(col[:, None, :] if col.ndim == 2 else col, 1, axis=1)
    arr = np.broadcast_to(col[:, None, :], (CH, CW, 3)).copy() if col.ndim == 2 else np.repeat(col, CW, axis=1)
    cl = _cloud_noise(5, CW, CH)
    # cloud banks: darker blobs, stronger high up
    sky = (yy < HOR)[..., 0][:, None] if False else (yy < HOR)
    m = np.clip(d, 0, 1) ** 0.6
    arr *= (1 - 0.55 * np.clip(cl[..., None] - 0.35, 0, 1) * 2 * m[..., None])
    # brighter break in clouds right of centre
    xx = np.arange(CW, dtype=np.float32)[None, :]
    brk = np.exp(-(((xx - CW * 0.68) / 260) ** 2) - (((yy - HOR * 0.78) / 170) ** 2))
    arr += (np.array([120, 110, 90], np.float32) * (brk * (cl > 0.45))[..., None] * 0.5)
    # ground
    g = yy >= HOR
    gt = np.asarray(noise_tex(8, (CW, CH)), np.float32) / 255
    gy = np.clip((yy - HOR) / (CH - HOR), 0, 1)
    ground = np.array([30, 30, 22], np.float32)[None, None] * (0.8 + 0.3 * gt[..., None]) * (1 - 0.55 * gy[..., None])
    # wet sheen near the horizon
    sheen = np.exp(-((yy - HOR) / 60.0) ** 2) * g
    ground += np.array([90, 84, 70], np.float32) * sheen[..., None] * 0.6
    arr = np.where(g[..., None], ground, arr)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # river reflection band on the left
    riv = new(size=(CW, CH)); rd = ImageDraw.Draw(riv)
    rd.polygon([(0, HOR + 18), (CW * 0.38, HOR + 12), (CW * 0.22, HOR + 60), (0, HOR + 150)], fill=(150, 145, 128, 120))
    img.alpha_composite(riv.filter(ImageFilter.GaussianBlur(5)))
    # far tree line (whole horizon) + the mango grove (left, large, dark)
    trees = new(size=(CW, CH)); td = ImageDraw.Draw(trees)
    rng = np.random.default_rng(2)
    for i in range(90):
        x = rng.random() * CW
        tree(td, x, HOR + 4, 26 + rng.random() * 22, (52, 52, 46, 255), rng)
    img.alpha_composite(trees.filter(ImageFilter.GaussianBlur(2.2)))
    grove = new(size=(CW, CH)); gd = ImageDraw.Draw(grove)
    for i in range(55):
        x = rng.random() * CW * 0.44 - 40
        tree(gd, x, HOR + 30 + rng.random() * 40, 150 + rng.random() * 120, (16, 19, 15, 255), rng)
    img.alpha_composite(grove.filter(ImageFilter.GaussianBlur(0.8)))
    hz_l = new(size=(CW, CH)); hd = ImageDraw.Draw(hz_l)
    hd.rectangle((0, HOR - 40, CW, HOR + 50), fill=(170, 160, 140, 60))
    img.alpha_composite(hz_l.filter(ImageFilter.GaussianBlur(36)))
    return img


def redcoat(d, x, y, h, coat=(110, 28, 24, 255), dark=(12, 11, 11, 255), white=(150, 140, 120, 255)):
    """Foreground company infantryman silhouette, feet at y."""
    hd = h * 0.07
    d.ellipse((x - hd, y - h * 0.9, x + hd, y - h * 0.9 + 2 * hd), fill=dark)
    d.polygon([(x - h * 0.15, y - h * 0.885), (x - h * 0.08, y - h * 0.955), (x + h * 0.08, y - h * 0.955), (x + h * 0.15, y - h * 0.885),
               (x, y - h * 0.905)], fill=dark)
    d.polygon([(x - h * 0.1, y - h * 0.76), (x + h * 0.1, y - h * 0.76), (x + h * 0.13, y - h * 0.5), (x + h * 0.16, y - h * 0.36),
               (x - h * 0.16, y - h * 0.36), (x - h * 0.13, y - h * 0.5)], fill=coat)
    d.line((x - h * 0.08, y - h * 0.75, x + h * 0.11, y - h * 0.46), fill=white, width=max(1, int(h * 0.012)))
    d.line((x - h * 0.1, y - h * 0.72, x - h * 0.14, y - h * 0.48), fill=coat, width=max(3, int(h * 0.05)))   # arm
    d.line((x - h * 0.06, y - h * 0.38, x - h * 0.08, y), fill=dark, width=max(3, int(h * 0.055)))
    d.line((x + h * 0.06, y - h * 0.38, x + h * 0.09, y), fill=dark, width=max(3, int(h * 0.055)))
    d.line((x + h * 0.12, y - h * 0.6, x + h * 0.19, y - h * 1.16), fill=dark, width=max(2, int(h * 0.022)))
    d.line((x + h * 0.19, y - h * 1.16, x + h * 0.205, y - h * 1.28), fill=(140, 140, 140, 255), width=max(1, int(h * 0.01)))


def company_flag(d, x, y, h):
    d.line((x, y, x, y - h), fill=(14, 12, 12, 255), width=6)
    fw, fh = h * 0.42, h * 0.26
    top = y - h + 6
    for k in range(9):
        d.rectangle((x + 3, top + k * fh / 9, x + 3 + fw, top + (k + 1) * fh / 9), fill=(150, 34, 30, 255) if k % 2 == 0 else (170, 160, 140, 255))
    d.rectangle((x + 3, top, x + 3 + fw * 0.36, top + fh * 0.5), fill=(170, 160, 140, 255))
    d.line((x + 3 + fw * 0.18, top, x + 3 + fw * 0.18, top + fh * 0.5), fill=(150, 34, 30, 255), width=5)
    d.line((x + 3, top + fh * 0.25, x + 3 + fw * 0.36, top + fh * 0.25), fill=(150, 34, 30, 255), width=5)


def _army_layer(part, colour):
    """Nawab host on the horizon (right). part='loyal' or 'jafar'."""
    lay = new(size=(CW, CH)); d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(11 if part == "loyal" else 12)
    c = tuple(colour) + (255,)
    ce = tuple(min(255, v + 22) for v in colour) + (255,)
    if part == "loyal":
        x0, x1, ys = CW * 0.6, CW * 1.04, (HOR + 10, HOR + 75)
        eles = [(CW * (0.67 + 0.105 * k), HOR + 40 + (k % 2) * 22, 190 + 14 * (k % 2)) for k in range(4)]
    else:
        x0, x1, ys = CW * 0.40, CW * 0.62, (HOR + 14, HOR + 80)
        eles = [(CW * (0.46 + 0.12 * k), HOR + 50, 160) for k in range(2)]
    for (ex, ey, es) in eles:
        d.line((ex + 20, ey - es * 0.95, ex + 20, ey - es * 1.75), fill=c, width=4)
        d.polygon([(ex + 22, ey - es * 1.75), (ex + 100, ey - es * 1.68), (ex + 22, ey - es * 1.6)],
                  fill=(34, 70, 48, 255) if part == "loyal" else c)
    for row in range(6):
        y = ys[0] + row * (ys[1] - ys[0]) / 5
        hgt = 30 + row * 6
        n = int((x1 - x0) / (hgt * 0.34))
        for i in range(n):
            x = x0 + i * (x1 - x0) / n + rng.random() * 8
            soldier(d, x, y, hgt, c, gun=rng.random() < 0.6)
            if rng.random() < 0.08:
                d.line((x, y - hgt, x + 2, y - hgt * 2.4), fill=c, width=2)
    for (ex, ey, es) in eles:
        hw = (58, 30, 22, 255) if part == "loyal" else tuple(int(v * 0.8) for v in colour) + (255,)
        # rim light: draw slightly larger lighter copy first
        elephant(d, ex + 2, ey, es * 1.03, ce, howdah=ce)
        elephant(d, ex, ey, es, c, howdah=hw)
    if part == "loyal":
        for k in range(3):
            cannon(d, CW * (0.7 + 0.11 * k), HOR + 110, 80, c, facing=-1)
    return lay


@functools.lru_cache(maxsize=1)
def _layers():
    loyal = _army_layer("loyal", (26, 30, 42))
    jafar = _army_layer("jafar", (26, 30, 42))
    jafar_grey = _army_layer("jafar", (128, 128, 128))
    comp_l = new(size=(CW, CH)); d = ImageDraw.Draw(comp_l)
    rng = np.random.default_rng(4)
    company_flag(d, CW * 0.2, int(1250 * SC), 430)
    for row in range(3):
        y = int(1250 * SC) + row * 85
        hgt = 200 + row * 55
        n = 10 - row * 2
        for i in range(n):
            x = CW * 0.02 + i * hgt * 0.27 + row * 45 + rng.random() * 10
            coat = (110, 28, 24, 255) if (i * 3 + row) % 5 else (58, 46, 38, 255)
            redcoat(d, x, y + rng.random() * 8, hgt * (0.96 + rng.random() * 0.08), coat=coat)
    for k in range(2):
        x = CW * (0.62 + 0.18 * k); y = int(1500 * SC)
        cannon(d, x, y, 170, (14, 12, 12, 255), facing=1)
        d.polygon([(x - 120, y - 70), (x + 60, y - 130), (x + 160, y - 50), (x - 60, y - 5)], fill=(62, 54, 38, 245))
    return loyal, jafar, jafar_grey, comp_l


@functools.lru_cache(maxsize=1)
def _rain_tex():
    rng = np.random.default_rng(7)
    lay = new(size=(W, H * 2)); d = ImageDraw.Draw(lay)
    for i in range(1400):
        x = rng.random() * (W + 400) - 200; y = rng.random() * H * 2
        L = 40 + rng.random() * 70
        a = int(50 + rng.random() * 90)
        d.line((x, y, x - L * 0.25, y + L), fill=(210, 220, 230, a), width=2 if rng.random() < 0.3 else 1)
    return lay


def _rain(img, t, strength):
    if strength <= 0:
        return
    tex = _rain_tex()
    off = int((t * 1900) % H)
    crop = tex.crop((0, H - off, W, 2 * H - off))
    comp(img, crop, strength)
    off2 = int((t * 1300 + 500) % H)
    crop2 = tex.crop((0, H - off2, W, 2 * H - off2)).transpose(Image.FLIP_LEFT_RIGHT)
    comp(img, crop2, strength * 0.5)


def _smoke(img, t, cam, strength, origins):
    if strength <= 0:
        return
    lay = new(); d = ImageDraw.Draw(lay)
    for k, (ox, oy) in enumerate(origins):
        for j in range(6):
            ph = (t * 0.22 + j / 6 + k * 0.13) % 1.0
            x = ox + ph * 80 + math.sin(ph * 6 + k) * 20
            y = oy - ph * 260
            r = 26 + ph * 90
            a = int(120 * (1 - ph) * strength)
            d.ellipse((x - r, y - r, x + r, y + r), fill=(225, 228, 230, a))
    comp(img, lay.filter(ImageFilter.GaussianBlur(14)))


def _cam(base_layer, z, px, py):
    """Crop a window of the oversize layer (zoom z, pan px/py in oversize px) and scale to the frame."""
    vw, vh = CW / (z * 1.06), CH / (z * 1.06)
    x0 = (CW - vw) / 2 + px
    y0 = (CH - vh) / 2 + py
    return base_layer.transform((W, H), Image.EXTENT, (x0, y0, x0 + vw, y0 + vh), Image.BILINEAR)


def battle_open(img, g):
    T = g.T
    z = 1.0 + 0.07 * min(T / 40.0, 1.0)
    sky = _sky()
    loyal, jafar, jgrey, comp_l = _layers()
    frame = _cam(sky, z * 0.985, -10 * T / 40, 0)
    img.alpha_composite(frame)
    mid = new(size=(CW, CH))
    mid.alpha_composite(loyal)
    gr = g.r("grey", 0.3, 1.2)
    if gr < 1:
        mid.alpha_composite(jafar)
    if gr > 0:
        mid.alpha_composite(fade(jgrey, gr) or new(size=(CW, CH)))
    img.alpha_composite(_cam(mid, z, -18 * T / 40, 0))
    # atmospheric haze over the mid layer
    rain_s = 0.25 + 0.45 * g.r("rain", 0, 1.5) - 0.35 * g.r("flee", 0, 2.0)
    _smoke(img, T, z, 0.4 + 0.7 * g.r("rain", 0.5, 2), [(690, 1010), (800, 1015), (905, 1012)])
    img.alpha_composite(_cam(comp_l, z * 1.01, -30 * T / 40, 10))
    _rain(img, T, max(0.15, rain_s))
    # lightning
    fl = (0.42 if 0.55 < T < 0.63 else 0) + (0.25 if 0.75 < T < 0.82 else 0)
    if g.seen("rain"):
        c = g.ct("rain")
        fl += 0.6 if 0.1 < c < 0.22 else 0
    if fl > 0:
        comp(img, Image.new("RGBA", (W, H), (235, 240, 255, 255)), min(0.9, fl))
    # darken top for title legibility
    # ---- overlays
    a_t = 1 - g.r("nawab", 0, 0.6)
    title_card(img, "1757", "普拉西 · 孟加拉", a=a_t, y=420, size=150, sub_size=46)
    if g.seen("title"):
        label(img, (W / 2, 640), "6月23日 · 一场打了不到一天的仗", size=38, color=GOLD_L, a=g.r("title") * a_t, box=(0, 0, 0, 150))
    if g.seen("nawab"):
        a = g.r("nawab") * (1 - g.r("company", 0.3))
        label(img, (W * 0.74, 700), "纳瓦布大军", size=52, color=BLUE_L, a=a, fontspec=SERIF_B)
        label(img, (W * 0.74, 770), "约5万人 · 50余门炮 · 战象", size=34, color=IVORY, a=a, box=(10, 20, 40, 170))
    if g.seen("company"):
        a = g.r("company") * (1 - g.r("rain", 0.3))
        label(img, (W * 0.30, 1060), "东印度公司", size=52, color=RED_L, a=a, fontspec=SERIF_B)
        label(img, (W * 0.30, 1128), "约3000人 · 约三分之二是印度士兵", size=32, color=IVORY, a=a, box=(40, 10, 10, 170))
    if g.seen("rain"):
        a = g.r("rain", 0.8) * (1 - g.r("grey", 0, 0.5))
        label(img, (W * 0.74, 700), "火药受潮 · 炮火转稀", size=40, color=IVORY, a=a, box=(10, 20, 40, 180))
        label(img, (W * 0.30, 1060), "油布盖住火药", size=40, color=IVORY, a=a, box=(40, 10, 10, 180))
    if g.seen("grey"):
        a = g.r("grey", 0.8) * (1 - g.r("flee", 0, 0.5))
        x = W * 0.46
        lay = new(); d = ImageDraw.Draw(lay)
        d.rounded_rectangle((W * 0.36, 820, W * 0.62, 1010), radius=14, outline=(220, 220, 220, 230), width=4)
        comp(img, lay, a)
        label(img, (W * 0.49, 770), "这一支：一枪没放", size=46, color=WHITE, a=a, fontspec=SERIF_B, box=(60, 60, 60, 200))
    if g.seen("flee"):
        c = g.ct("flee")
        lay = new(); d = ImageDraw.Draw(lay)
        camel(d, W * 0.86 + c * 30, 975, 60, (20, 20, 24, 255))
        comp(img, lay, g.r("flee"))
        label(img, (W / 2, 700), "公司阵亡 约22人", size=56, color=GOLD_L, a=g.r("flee", 1.2), fontspec=SERIF_B, box=(0, 0, 0, 170))
    # letterbox gradient top for header-less open
    return img


# ---------------------------------------------------------------- teaser beats

@functools.lru_cache(maxsize=1)
def _miniature():
    """Miniature-painting style panel: emperor on an armchair set on a table, handing a scroll (schematic)."""
    w, h = 900, 980
    p = parchment(w, h, seed=9, tone=(228, 205, 150))
    im = p.copy(); d = ImageDraw.Draw(im)
    # ornamental border
    for i, col in enumerate([(140, 30, 30), (200, 150, 60), (40, 70, 110)]):
        m = 26 + i * 12
        d.rectangle((m, m, w - m, h - m), outline=col + (255,), width=8 if i == 0 else 4)
    for k in range(0, w, 40):
        d.ellipse((k + 14, 14, k + 26, 26), fill=(200, 150, 60, 255)); d.ellipse((k + 14, h - 26, k + 26, h - 14), fill=(200, 150, 60, 255))
    # tent canopy
    d.polygon([(110, 260), (w / 2, 120), (w - 110, 260)], fill=(170, 60, 50, 255))
    for k in range(9):
        x = 110 + k * (w - 220) / 8
        d.line((x, 260, x, 300), fill=(220, 180, 90, 255), width=6)
    d.rectangle((110, 260, w - 110, 300), fill=(200, 150, 60, 255))
    d.line((150, 300, 150, 860), fill=(120, 80, 40, 255), width=10); d.line((w - 150, 300, w - 150, 860), fill=(120, 80, 40, 255), width=10)
    # floor carpet
    d.rectangle((90, 760, w - 90, 900), fill=(130, 40, 40, 255))
    for k in range(10):
        cx_ = 125 + k * 72
        d.polygon([(cx_, 795), (cx_ + 22, 830), (cx_, 865), (cx_ - 22, 830)], outline=(220, 180, 90, 255), width=3)
    # English dining table + armchair throne
    d.rectangle((300, 560, 600, 590), fill=(110, 70, 35, 255))
    for x in (315, 575):
        d.rectangle((x, 590, x + 12, 760), fill=(90, 55, 28, 255))
    d.rectangle((370, 430, 530, 470), fill=(60, 110, 90, 255))                 # chair back drape
    d.rectangle((370, 470, 390, 560), fill=(60, 110, 90, 255)); d.rectangle((510, 470, 530, 560), fill=(60, 110, 90, 255))
    # emperor (seated, profile, halo)
    d.ellipse((410, 340, 490, 420), outline=(230, 190, 80, 255), width=6)
    d.ellipse((428, 360, 472, 404), fill=(150, 105, 70, 255))
    d.ellipse((424, 340, 476, 372), fill=(235, 230, 215, 255))                # turban
    d.polygon([(410, 410), (490, 410), (505, 545), (395, 545)], fill=(235, 220, 160, 255))
    d.line((490, 460, 560, 500), fill=(235, 220, 160, 255), width=14)       # arm with scroll
    d.rectangle((555, 490, 600, 512), fill=(245, 240, 225, 255))
    # Clive & officers (red coats) on the right, standing
    for k, x in enumerate((660, 730)):
        d.ellipse((x - 18, 470, x + 18, 506), fill=(225, 195, 170, 255))
        d.polygon([(x - 26, 506), (x + 26, 506), (x + 30, 650), (x - 30, 650)], fill=(180, 40, 36, 255))
        d.polygon([(x - 26, 476), (x, 452), (x + 26, 476)], fill=(30, 30, 30, 255))
        d.rectangle((x - 22, 650, x - 6, 760), fill=(240, 235, 220, 255)); d.rectangle((x + 6, 650, x + 22, 760), fill=(240, 235, 220, 255))
    # courtiers on the left
    for k, x in enumerate((200, 260)):
        d.ellipse((x - 16, 480, x + 16, 512), fill=(150, 105, 70, 255))
        d.ellipse((x - 18, 466, x + 18, 490), fill=(240, 235, 220, 255))
        d.polygon([(x - 26, 512), (x + 26, 512), (x + 34, 760), (x - 34, 760)], fill=(230, 210, 150, 255) if k else (90, 130, 170, 255))
    d.text((w / 2, 945), "示意 · 仿细密画风格", font=font(SANS, 26), fill=(90, 60, 30, 255), anchor="mm")
    return im


def teaser_diwani(img, g):
    img.alpha_composite(bg_copy(tint=(80, 50, 10)))
    T = g.T
    m = _miniature()
    s = 0.92 + 0.04 * min(1, T / 6)
    mm = m.resize((int(m.size[0] * s), int(m.size[1] * s)), Image.BICUBIC)
    comp(img, mm, ramp(T, 0, 0.5), ((W - mm.size[0]) / 2, 300 + (1 - ease_out(min(1, T / 0.6))) * 40))
    label(img, (W / 2, 1250), "1765 · 三省征税权 → 公司", size=46, color=GOLD_L, a=ramp(T, 0.8, 0.6), fontspec=SERIF_B, box=(0, 0, 0, 170))


def teaser_army(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    title_card(img, "1803年", None, a=ramp(T, 0, 0.5), y=380, size=96)
    p = ease(T / 1.8)
    hbar(img, 120, 620, 840, 70, 1.0 * p, RED, label_l="东印度公司军队", label_r=f"约 {int(200000 * p):,} 人+", lsize=40)
    p2 = ease((T - 0.8) / 1.5)
    hbar(img, 120, 840, 840, 70, 0.5 * p2, (150, 150, 160), label_l="英国本土常备军", label_r="约一半", lsize=40, a=ramp(T, 0.6, 0.5))
    # rows of tiny soldiers
    lay = new(); d = ImageDraw.Draw(lay)
    n = int(40 * p)
    for i in range(n):
        soldier(d, 140 + i * 20.5, 1080, 44, (200, 60, 50, 255), gun=False)
    for i in range(int(20 * p2)):
        soldier(d, 140 + i * 20.5, 1170, 44, (150, 150, 160, 255), gun=False)
    comp(img, lay)
    label(img, (W / 2, 1260), "据 Dalrymple《无政府》", size=28, color=(190, 180, 160), a=ramp(T, 1.5, 0.5))


@functools.lru_cache(maxsize=1)
def _east_india_house(w=760, h=820, windows=5, dusk=False):
    """Georgian façade, five windows wide (the pre-1790s Leadenhall Street house), schematic."""
    im = new(size=(w, h)); d = ImageDraw.Draw(im)
    stone = (150, 138, 118, 255)
    d.rectangle((60, 120, w - 60, h - 40), fill=stone)
    d.rectangle((40, 100, w - 40, 130), fill=(120, 108, 90, 255))
    d.rectangle((40, h - 50, w - 40, h - 20), fill=(110, 100, 84, 255))
    ww = (w - 120) / windows
    for r in range(3):
        for c in range(windows):
            x = 60 + c * ww + ww * 0.25
            y = 170 + r * 190
            d.rectangle((x, y, x + ww * 0.5, y + 120), fill=(38, 44, 56, 255) if (r + c) % 3 else (230, 180, 90, 255))
            d.line((x + ww * 0.25, y, x + ww * 0.25, y + 120), fill=stone, width=3)
            d.line((x, y + 60, x + ww * 0.5, y + 60), fill=stone, width=3)
    d.rectangle((w / 2 - 55, h - 200, w / 2 + 55, h - 50), fill=(50, 36, 26, 255))
    d.pieslice((w / 2 - 55, h - 255, w / 2 + 55, h - 145), 180, 360, fill=(50, 36, 26, 255))
    # ship weather-vane / company figure on top
    d.line((w / 2, 100, w / 2, 40), fill=(60, 50, 40, 255), width=4)
    ship(d, w / 2, 40, 70, hull=(60, 50, 40, 255), sail=(60, 50, 40, 255))
    return im


def teaser_hq(img, g):
    img.alpha_composite(bg_copy(tint=(40, 40, 60)))
    T = g.T
    h = _east_india_house()
    comp(img, h, ramp(T, 0, 0.5), ((W - h.size[0]) / 2, 340))
    # five window ticks
    lay = new(); d = ImageDraw.Draw(lay)
    ww = (760 - 120) / 5
    for c in range(5):
        x = (W - 760) / 2 + 60 + c * ww + ww * 0.5
        a = ramp(T, 0.6 + c * 0.18, 0.3)
        if a > 0:
            d.text((x, 300), str(c + 1), font=font(SERIF_B, 44), fill=GOLD_L + (int(255 * a),), anchor="mm")
    comp(img, lay)
    label(img, (W / 2, 1220), "伦敦 · 利德贺街总部：五扇窗宽", size=40, color=GOLD_L, a=ramp(T, 0.3, 0.5), fontspec=SERIF_B, box=(0, 0, 0, 170))
    c = g.ct("hq") or 0
    if T > 3.0:
        counter(img, (W / 2, 1050), 35 * ease((T - 3.0) / 1.2), suffix=" 人", size=110, a=ramp(T, 3.0, 0.4))
        label(img, (W / 2, 1130), "成立百年时的总部正式职员", size=32, color=IVORY, a=ramp(T, 3.2, 0.4), box=(0, 0, 0, 160))


def _icon_army(d, cx, cy, s, col):
    for k in range(3):
        soldier(d, cx - s * 0.4 + k * s * 0.4, cy + s * 0.5, s * 0.9, col)


def _icon_court(d, cx, cy, s, col):
    d.polygon([(cx - s * 0.6, cy - s * 0.2), (cx, cy - s * 0.6), (cx + s * 0.6, cy - s * 0.2)], fill=col)
    for k in range(4):
        x = cx - s * 0.45 + k * s * 0.3
        d.rectangle((x - s * 0.06, cy - s * 0.15, x + s * 0.06, cy + s * 0.4), fill=col)
    d.rectangle((cx - s * 0.65, cy + s * 0.42, cx + s * 0.65, cy + s * 0.55), fill=col)


def _icon_tax(d, cx, cy, s, col):
    for k in range(5):
        coin(d, cx - s * 0.2 + (k % 2) * 6, cy + s * 0.4 - k * s * 0.16, s * 0.36)
    d.rectangle((cx + s * 0.15, cy - s * 0.5, cx + s * 0.62, cy + s * 0.5), fill=(235, 225, 200, 255))
    for k in range(5):
        d.line((cx + s * 0.22, cy - s * 0.38 + k * s * 0.18, cx + s * 0.55, cy - s * 0.38 + k * s * 0.18), fill=(90, 70, 40, 255), width=3)


def teaser_question(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    items = [("军队", _icon_army), ("法庭", _icon_court), ("税收", _icon_tax)]
    for i, (nm, fn) in enumerate(items):
        a = ramp(T, 0.3 + i * 0.5, 0.4)
        cx = 210 + i * 330
        lay = new(); d = ImageDraw.Draw(lay)
        d.ellipse((cx - 130, 640 - 130, cx + 130, 640 + 130), outline=GOLD + (220,), width=3, fill=(20, 26, 38, 230))
        fn(d, cx, 630, 120, GOLD_L + (255,))
        comp(img, lay, a)
        label(img, (cx, 840), nm, size=50, color=GOLD_L, a=a, fontspec=SERIF_B)
    title_card(img, "一家公司？", None, a=ramp(T, 1.8, 0.5), y=1080, size=100, color=WHITE)


def teaser_nodes(img, g):
    img.alpha_composite(bg_copy())
    T = g.T
    pos = [("股东", "伦敦", (300, 520)), ("董事会", "伦敦 · 利德贺街", (780, 520)),
           ("驻印职员", "加尔各答", (300, 1050)), ("议会", "威斯敏斯特", (780, 1050))]
    for i, (a_, b_, xy) in enumerate(pos):
        node(img, xy, a_, b_, a=ramp(T, 0.2 + i * 0.45, 0.4), w=380, h=150)
    p = ramp(T, 2.2, 1.2)
    # tangled arrows: command (blue) vs money (gold)
    if p > 0:
        comp(img, thick_arrow(bezier((780, 610), (560, 760), (330, 960)), 18, BLUE_L, prog=p))
        comp(img, thick_arrow(bezier((360, 960), (520, 760), (330, 610)), 18, GOLD, prog=ramp(T, 3.0, 1.0)))
        comp(img, thick_arrow(bezier((760, 960), (640, 800), (760, 610)), 18, (200, 200, 200), prog=ramp(T, 3.8, 1.0)))
    label(img, (W / 2, 1240), "命令流 ≠ 钱流", size=52, color=GOLD_L, a=ramp(T, 4.2, 0.6), fontspec=SERIF_B)
    lay = new(); d = ImageDraw.Draw(lay)
    d.line((370, 1300, 430, 1300), fill=BLUE_L + (255,), width=8); d.line((640, 1300, 700, 1300), fill=GOLD + (255,), width=8)
    comp(img, lay, ramp(T, 4.2, 0.6))
    label(img, (500, 1300), "命令", size=30, a=ramp(T, 4.2, 0.6))
    label(img, (760, 1300), "钱", size=30, a=ramp(T, 4.2, 0.6))


def teaser_smith(img, g):
    img.alpha_composite(bg_copy(tint=(60, 40, 10)))
    T = g.T
    lay = new(); d = ImageDraw.Draw(lay)
    d.ellipse((W / 2 - 220, 380, W / 2 + 220, 820), fill=(30, 34, 44, 255), outline=GOLD + (230,), width=4)
    person_bust(d, W / 2, 660, 330, (12, 14, 20, 255), hat="wig")
    comp(img, lay, ramp(T, 0, 0.5))
    title_card(img, "亚当·斯密", "《国富论》1776", a=ramp(T, 0.4, 0.5), y=930, size=72)
    label(img, (W / 2, 1150), "一句判断 · 片尾揭晓", size=44, color=GOLD_L, a=ramp(T, 1.2, 0.5), box=(0, 0, 0, 160))


GROUPS = {
    "battle_open": (battle_open, ["open", "title", "nawab", "company", "rain", "grey", "flee"]),
    "teaser_diwani": (teaser_diwani, ["diwani"]),
    "teaser_army": (teaser_army, ["army"]),
    "teaser_hq": (teaser_hq, ["hq"]),
    "teaser_question": (teaser_question, ["question"]),
    "teaser_nodes": (teaser_nodes, ["nodes"]),
    "teaser_smith": (teaser_smith, ["smith_tease"]),
}
