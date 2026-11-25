# -*- coding: utf-8 -*-
"""场景元素：夜空、山、石桥、河水、锦袍、人物剪影、马、火把、剑光、宫墙、炭火、漆器。"""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *


# ---------------------------------------------------------------- 天空 / 山 / 雾
@lru_cache(maxsize=8)
def night_sky(seed=1, moon=(760, 380), moon_r=70, top="#03060c", bot="#16233a", stars=True, w=W, h=H):
    img = vgrad(h, w, hexc(top), hexc(bot), 0.9)
    cl = fbm(w // 2, h // 2, seed, 6, 3)
    cl = np.asarray(Image.fromarray(cl, "F").resize((w, h), Image.BICUBIC))
    img += (np.clip(cl - 0.45, 0, 1) ** 1.5)[:, :, None] * hexc("#3a4d6e") * 0.9
    if stars:
        rng = np.random.default_rng(seed)
        n = 500
        xs, ys = rng.integers(0, w, n), rng.integers(0, int(h * 0.55), n)
        b = rng.random(n) ** 3
        st = np.zeros((h, w), np.float32)
        st[ys, xs] = b
        st = blur(st, 1.0) * 2.5 + st * 0.6
        img += st[:, :, None] * MOON * (1 - cl[:, :, None])
    if moon:
        mx, my = moon
        img += radial(h, w, mx, my, moon_r * 7, 2.2)[:, :, None] * hexc("#6d86ad") * 0.55
        disc = mask_from_poly([("ellipse", (mx - moon_r, my - moon_r, mx + moon_r, my + moon_r))], w, h)
        tex = fbm(w // 4, h // 4, seed + 9, 5, 6)
        tex = np.asarray(Image.fromarray(tex, "F").resize((w, h), Image.BICUBIC))
        img = over(img, hexc("#f2eedf") * (0.86 + 0.14 * tex[:, :, None]), disc)
        # 薄云掠过月面
        img = over(img, hexc("#2b3a55"), np.clip(cl - 0.55, 0, 1)[:, :, None] * 1.4 * disc[:, :, None])
    return img.astype(np.float32)


def ridge(w, seed, base_y, amp, rough=0.55, octaves=7):
    rng = np.random.default_rng(seed)
    xs = np.zeros(w, np.float32)
    a = 1.0
    for o in range(octaves):
        n = 3 * 2 ** o + 2
        g = rng.random(n).astype(np.float32)
        xs += a * np.interp(np.linspace(0, n - 1, w), np.arange(n), g)
        a *= rough
    xs = (xs - xs.min()) / (xs.max() - xs.min() + 1e-6)
    return base_y - xs * amp


@lru_cache(maxsize=8)
def mountains(seed=3, n=5, y0=980, y1=1500, col_far="#33445f", col_near="#080b10", amp=520, w=W, h=H, mist="#55688a"):
    """层叠水墨山，返回 (rgb, alpha) 合成到天空上用。"""
    rgb = np.zeros((h, w, 3), np.float32)
    al = np.zeros((h, w), np.float32)
    yy = np.arange(h, dtype=np.float32)[:, None]
    cf, cn, cm = hexc(col_far), hexc(col_near), hexc(mist)
    for i in range(n):
        u = i / max(n - 1, 1)
        base = y0 + (y1 - y0) * u
        r = ridge(w, seed * 10 + i, base, amp * (1 - 0.45 * u), 0.42 + 0.04 * i, octaves=6)
        m = clamp01((yy - r[None, :]) / 2.0)
        col = cf * (1 - u) + cn * u
        # 山脚雾
        fog = np.exp(-np.clip(yy - r[None, :], 0, None) / (60 + 80 * (1 - u)))
        layer = col * (1 - 0.0) + (cm - col) * (fog[:, :, None] * 0.0)
        shade = 0.85 + 0.15 * fbm(w // 4, h // 4, seed + i, 4, 8)
        shade = np.asarray(Image.fromarray(shade, "F").resize((w, h)))[:, :, None]
        rgb = rgb * (1 - m[:, :, None]) + layer * shade * m[:, :, None]
        # 层间雾带
        band = np.exp(-((yy - (base + 40)) / 70) ** 2)[:, :] * (0.55 - 0.4 * u)
        rgb = rgb * (1 - band[:, :, None] * m[:, :, None] * 0) + 0
        al = np.maximum(al, m)
        rgb = rgb + (cm * band[:, :, None] * 0.5) * (al[:, :, None])
    return rgb, al


def mist_layer(t, seed=5, y=1300, height=420, k=0.35, speed=18, col="#8fa3c4"):
    n = _mist_tex(seed)
    off = int(t * speed) % W
    m = np.roll(n, off, 1)
    yy = np.arange(H, dtype=np.float32)[:, None]
    band = np.exp(-((yy - y) / height) ** 2)
    return (m * band)[:, :, None] * hexc(col) * k


@lru_cache(maxsize=4)
def _mist_tex(seed):
    a = fbm(W // 2, H // 2, seed, 5, 2)
    return np.asarray(Image.fromarray(np.clip(a - 0.35, 0, 1) * 1.6, "F").resize((W, H), Image.BICUBIC))


# ---------------------------------------------------------------- 石桥 / 河水
def bridge_shape(x0=-60, x1=1140, deck_y=1080, hump=70, arch_c=540, arch_r=230, thick=70):
    """返回 (桥身多边形列表, 栏杆多边形列表, 桥面曲线点)。"""
    xs = np.linspace(x0, x1, 80)
    yd = deck_y - hump * np.cos(np.clip((xs - arch_c) / (x1 - x0) * math.pi, -math.pi / 2, math.pi / 2))
    top = list(zip(xs, yd))
    bottom_y = deck_y + 260
    body = top + [(x1, bottom_y), (x0, bottom_y)]
    # 拱洞（用多边形近似半圆，后面减掉）
    arches = []
    for cx, r in [(arch_c, arch_r), (arch_c - 380, 95), (arch_c + 380, 95)]:
        a = np.linspace(math.pi, 0, 40)
        spring = deck_y + thick + r * 0.15 if r > 150 else deck_y + thick + 60
        pts = [(cx + r * math.cos(t), spring + 120 - r * math.sin(t) * 1.0) for t in a]
        pts = [(cx - r, bottom_y + 10)] + pts + [(cx + r, bottom_y + 10)]
        arches.append(pts)
    # 栏杆
    rail = []
    rail_h = 46
    rail_poly = top + [(x, y - rail_h) for x, y in top[::-1]]
    posts = []
    for i in range(3, 78, 6):
        x, y = top[i]
        posts.append([(x - 9, y + 2), (x + 9, y + 2), (x + 9, y - rail_h - 22), (x, y - rail_h - 32), (x - 9, y - rail_h - 22)])
    return body, arches, rail_poly, posts, top


@lru_cache(maxsize=6)
def bridge_layer(deck_y=1080, hump=70, lit="#9fb3d1", seed=11, arch_r=230):
    body, arches, rail, posts, top = bridge_shape(deck_y=deck_y, hump=hump, arch_r=arch_r)
    m = mask_from_poly([body])
    ma = mask_from_poly(arches)
    m = np.clip(m - ma, 0, 1)
    mr = mask_from_poly([rail] + posts)
    # 栏杆镂空
    holes = []
    for i in range(3, 75, 6):
        xa, ya = top[i]; xb, yb = top[i + 6] if i + 6 < len(top) else top[-1]
        holes.append([(xa + 16, ya - 10), (xb - 16, yb - 10), (xb - 16, yb - 34), (xa + 16, ya - 34)])
    mr = np.clip(mr - mask_from_poly(holes) * 0.85, 0, 1)
    al = np.clip(m + mr, 0, 1)
    tex = fbm(W // 2, H // 2, seed, 6, 10)
    tex = np.asarray(Image.fromarray(tex, "F").resize((W, H), Image.BICUBIC))
    # 石缝
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    bricks = (np.abs(np.sin(yy / 22 * math.pi)) < 0.08) | (np.abs(np.sin((xx + (yy // 44) * 30) / 60 * math.pi)) < 0.04)
    base = hexc("#1a2232") * (0.75 + 0.5 * tex[:, :, None])
    base = base * (1 - 0.35 * bricks[:, :, None])
    # 月光照亮桥面上沿
    tops = np.array(top)
    edge = np.zeros(W, np.float32) + 9999
    edge[np.clip(tops[:, 0].astype(int), 0, W - 1)] = tops[:, 1]
    edge = np.minimum.accumulate(np.where(edge > 9000, np.nan, edge)[::1]) if False else np.interp(np.arange(W), tops[:, 0], tops[:, 1])
    d = yy - edge[None, :]
    rim = np.exp(-np.clip(d, 0, None) / 18) * (d > -60)
    base = base + rim[:, :, None] * hexc(lit) * 0.35
    # 拱洞内沿高光
    ma_edge = np.clip(blur(ma, 3) - ma, 0, 1) * 3
    base = base + ma_edge[:, :, None] * hexc(lit) * 0.25
    return base.astype(np.float32), al.astype(np.float32), ma


def river(t, y0=1300, h=620, moon_x=760, k=1.0, col="#0b1626", seed=21):
    """河面：深色 + 流动波纹 + 月光倒影碎光。返回 (rgb, alpha)。"""
    tex = _river_tex(seed)
    off = int(t * 40) % tex.shape[1]
    tt = np.roll(tex, -off, 1)[:h, :W]
    yy = np.arange(h, dtype=np.float32)[:, None] / h
    rgb = hexc(col) * (0.6 + 0.6 * tt[:, :, None]) * (0.7 + 0.5 * yy[:, :, None])
    # 月光柱
    xx = np.arange(W, dtype=np.float32)[None, :]
    col_mask = np.exp(-((xx - moon_x) / (40 + 160 * yy)) ** 2) * 0.8
    spark = np.clip(tt - 0.66, 0, 1) * 5
    rgb = rgb + (col_mask * spark)[:, :, None] * hexc("#dfe7f2") * 0.9 * k
    out = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    y1 = min(H, y0 + h)
    out[y0:y1] = rgb[:y1 - y0]
    al[y0:y1] = 1
    return out, al


@lru_cache(maxsize=2)
def _river_tex(seed):
    a = fbm(W // 3, 700, seed, 6, 10, 0.62)
    a = np.asarray(Image.fromarray(a, "F").resize((W * 2, 700), Image.BICUBIC))
    # 横向拉长 = 水波
    return np.tile(a, (1, 1))


# ---------------------------------------------------------------- 锦袍
ROBE_PTS = [(0, -330), (-70, -320), (-170, -290), (-330, -250), (-420, -210), (-430, -120), (-380, -60), (-300, -80),
            (-210, -130), (-180, -100), (-195, 150), (-215, 420), (-240, 560), (-150, 585), (0, 595), (150, 585),
            (240, 560), (215, 420), (195, 150), (180, -100), (210, -130), (300, -80), (380, -60), (430, -120),
            (420, -210), (330, -250), (170, -290), (70, -320)]


@lru_cache(maxsize=2)
def robe_layer(cx=540, cy=820, scale=1.0):
    pts = [(cx + x * scale, cy + y * scale) for x, y in ROBE_PTS]
    m = mask_from_poly([pts], blur_r=0.6)
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    u, v = (xx - cx) / scale, (yy - cy) / scale
    # 织锦纹：菱格 + 团纹
    pat = (np.abs(np.sin(u / 26) * np.sin(v / 26)) > 0.82).astype(np.float32)
    ring = np.abs(np.sqrt(((u % 104) - 52) ** 2 + ((v % 104) - 52) ** 2) - 24) < 1.6
    pat = np.clip(pat * 0.6 + ring * 1.0, 0, 1)
    folds = fbm(48, 16, 31, 4, 3)
    folds = np.asarray(Image.fromarray(folds, "F").resize((W, H), Image.BICUBIC))
    fold = 0.55 + 0.6 * folds[:, :, None]
    base = hexc("#5e1410") * fold + pat[:, :, None] * GOLD_D * 0.32 * fold
    # 领口、袖缘的金边
    edge = np.clip(blur(m, 2.5) * (1 - blur(m, 2.5)) * 4, 0, 1)
    collar = mask_from_poly([[(cx - 70 * scale, cy - 320 * scale), (cx, cy - 120 * scale), (cx + 70 * scale, cy - 320 * scale),
                              (cx + 40 * scale, cy - 322 * scale), (cx, cy - 170 * scale), (cx - 40 * scale, cy - 322 * scale)]])
    base = over(base, GOLD * 0.9, np.clip(edge * 1.4 + collar * 0.8, 0, 1))
    # 中缝
    seam = np.exp(-(u / 3) ** 2) * (v > -120)
    base = base * (1 - 0.4 * seam[:, :, None])
    # 左上月光
    light = clamp01(0.55 - (u + v) / 1400)
    base = base * (0.65 + 0.7 * light[:, :, None])
    return base.astype(np.float32), m.astype(np.float32)


def robe_cut(rgb, al, cuts, n_done, sep, t_since):
    """cuts: [(p0, p1), ...] 斜线；n_done 刀已砍；sep 为分开距离（像素）。返回裂开的 (rgb, alpha)。"""
    if n_done <= 0:
        return rgb, al
    yy, xx = np.mgrid[:H, :W]
    label = np.zeros((H, W), np.int32)
    disp = []
    for i, (p0, p1) in enumerate(cuts[:n_done]):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        side = ((xx - p0[0]) * dy - (yy - p0[1]) * dx) > 0
        label |= (side.astype(np.int32) << i)
        L = math.hypot(dx, dy)
        disp.append((-dy / L, dx / L))
    out_rgb = np.zeros_like(rgb)
    out_a = np.zeros_like(al)
    for lab in range(2 ** n_done):
        mk = (label == lab)
        if not mk.any():
            continue
        ox = oy = 0.0
        for i in range(n_done):
            s = -1 if (lab >> i) & 1 else 1
            k = sep[i] if isinstance(sep, (list, tuple)) else sep
            ox += s * disp[i][0] * k * 0.5
            oy += s * disp[i][1] * k * 0.5 + (k * 0.25 if s > 0 else 0)
        ox, oy = int(round(ox)), int(round(oy))
        a = np.where(mk, al, 0)
        r = rgb * mk[:, :, None]
        a = np.roll(np.roll(a, ox, 1), oy, 0)
        r = np.roll(np.roll(r, ox, 1), oy, 0)
        out_rgb = out_rgb + r
        out_a = out_a + a
    nrm = np.maximum(out_a, 1.0)[:, :, None]
    return out_rgb / nrm, np.clip(out_a, 0, 1)


# ---------------------------------------------------------------- 人物剪影
def _xf(pts, x, y, s, flip=False):
    return [((-px if flip else px) * s + x, py * s + y) for px, py in pts]


STAND = [(-0.045, -0.845), (-0.13, -0.815), (-0.19, -0.72), (-0.235, -0.52), (-0.265, -0.40), (-0.20, -0.375),
         (-0.17, -0.52), (-0.165, -0.30), (-0.19, -0.10), (-0.235, 0.0), (0.235, 0.0), (0.19, -0.10), (0.165, -0.30),
         (0.17, -0.52), (0.20, -0.375), (0.265, -0.40), (0.235, -0.52), (0.19, -0.72), (0.13, -0.815), (0.045, -0.845)]
KNEEL = [(-0.05, -0.56), (-0.14, -0.53), (-0.2, -0.44), (-0.25, -0.30), (-0.30, -0.16), (-0.36, -0.03), (-0.38, 0.0),
         (0.30, 0.0), (0.28, -0.06), (0.18, -0.12), (0.18, -0.30), (0.17, -0.44), (0.12, -0.53), (0.04, -0.56)]
WALK = [(-0.045, -0.845), (-0.13, -0.81), (-0.18, -0.70), (-0.22, -0.50), (-0.25, -0.38), (-0.19, -0.36), (-0.16, -0.50),
        (-0.17, -0.28), (-0.24, -0.10), (-0.34, 0.0), (0.0, -0.02), (0.20, 0.0), (0.18, -0.12), (0.15, -0.30),
        (0.18, -0.48), (0.26, -0.36), (0.30, -0.40), (0.24, -0.56), (0.18, -0.72), (0.12, -0.81), (0.045, -0.845)]


def figure_polys(kind, x, y, s, flip=False, crown=True):
    """kind: stand / kneel / walk / strike（举剑）。返回多边形列表（剪影）。"""
    if kind == "kneel":
        body, hy = KNEEL, -0.62
    elif kind in ("walk",):
        body, hy = WALK, -0.90
    else:
        body, hy = STAND, -0.90
    polys = [_xf(body, x, y, s, flip)]
    hr = 0.058 * s
    hx = x + (0.0 if kind != "kneel" else 0.0)
    polys.append(("ellipse", (hx - hr, y + hy * s - hr * 1.15, hx + hr, y + hy * s + hr * 1.15)))
    if crown:  # 冠 / 发髻
        cy = y + (hy - 0.07) * s
        polys.append([(hx - 0.028 * s, cy + 0.03 * s), (hx - 0.022 * s, cy - 0.035 * s), (hx + 0.022 * s, cy - 0.035 * s),
                      (hx + 0.028 * s, cy + 0.03 * s)])
        polys.append([(hx - 0.06 * s, cy - 0.03 * s), (hx + 0.06 * s, cy - 0.03 * s), (hx + 0.06 * s, cy - 0.022 * s),
                      (hx - 0.06 * s, cy - 0.022 * s)])
    if kind == "strike":
        # 举剑的手臂（宽袖）
        sx = -1 if flip else 1
        sh = (x + sx * 0.12 * s, y - 0.78 * s)
        hand = (x + sx * 0.22 * s, y - 1.12 * s)
        polys.append([(sh[0] - 0.07 * s, sh[1] + 0.05 * s), (sh[0] + 0.07 * s * sx, sh[1] - 0.04 * s),
                      (hand[0] + 0.04 * s, hand[1]), (hand[0] - 0.05 * s, hand[1] + 0.02 * s)])
        polys.append([(hand[0] - 0.05 * s, hand[1] + 0.02 * s), (hand[0] - 0.16 * s * sx, hand[1] + 0.30 * s),
                      (hand[0] - 0.02 * s * sx, hand[1] + 0.26 * s)])  # 垂下的袖
    return polys


@lru_cache(maxsize=96)
def figure_layer(kind, x, y, s, flip=False, blur_r=0.7):
    return mask_from_poly(figure_polys(kind, x, y, s, flip), blur_r=blur_r)


def rim_light(mask, dx, dy, col, k=0.9, r=3):
    """剪影边缘光：mask 与平移后 mask 的差。"""
    sh = np.roll(np.roll(mask, int(dx), 1), int(dy), 0)
    e = clamp01(mask - sh)
    e = blur(e, r)
    return e[:, :, None] * hexc(col) * k if isinstance(col, str) else e[:, :, None] * col * k


HORSE = [(-0.50, -0.20), (-0.40, -0.40), (-0.28, -0.50), (-0.05, -0.66), (0.12, -0.80), (0.22, -0.98), (0.29, -1.10),
         (0.31, -1.05), (0.33, -1.09), (0.36, -1.03), (0.52, -0.93), (0.50, -0.87), (0.33, -0.88), (0.30, -0.76),
         (0.32, -0.66), (0.45, -0.67), (0.53, -0.58), (0.49, -0.49), (0.45, -0.52), (0.47, -0.58), (0.37, -0.59),
         (0.39, -0.53), (0.41, -0.44), (0.37, -0.43), (0.33, -0.52), (0.20, -0.48), (0.0, -0.38), (-0.08, -0.30),
         (0.0, -0.15), (0.05, 0.0), (-0.04, 0.0), (-0.10, -0.14), (-0.18, -0.22), (-0.12, -0.03), (-0.20, 0.0),
         (-0.28, -0.20), (-0.32, -0.40), (-0.33, -0.44), (-0.45, -0.31), (-0.53, -0.17)]


@lru_cache(maxsize=64)
def horse_layer(x, y, s, flip=False, rear=1.0):
    pts = HORSE
    if rear < 1.0:  # 前身抬起程度：绕后蹄旋转
        ang = (1 - rear) * 0.45
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(px * ca - py * sa, px * sa + py * ca) for px, py in pts]
    return mask_from_poly([_xf(pts, x, y, s, flip)], blur_r=0.8)


# ---------------------------------------------------------------- 火把 / 光 / 剑
def torch_glow(img, pts, t, k=1.0, r=180, seed=0):
    rng = np.random.default_rng(seed)
    lay = np.zeros((H // 4, W // 4), np.float32)
    flames = np.zeros((H, W), np.float32)
    for i, (x, y) in enumerate(pts):
        f = 0.8 + 0.2 * math.sin(t * 11 + i * 1.7) + 0.1 * math.sin(t * 23 + i)
        yy, xx = np.ogrid[:H // 4, :W // 4]
        d = np.sqrt((xx - x / 4) ** 2 + (yy - y / 4) ** 2)
        lay += np.exp(-(d / (r / 4)) ** 2) * f
    g = np.asarray(Image.fromarray(lay, "F").resize((W, H), Image.BILINEAR))
    img = img + g[:, :, None] * FIRE * 0.55 * k
    # 火苗
    polys = []
    for i, (x, y) in enumerate(pts):
        h = 34 + 8 * math.sin(t * 13 + i * 2.3)
        sw = 3 * math.sin(t * 9 + i)
        polys.append([(x - 10, y), (x - 6 + sw, y - h * 0.6), (x + sw * 2, y - h), (x + 7 + sw, y - h * 0.5), (x + 10, y)])
        polys.append([(x - 3, y + 2), (x + 3, y + 2), (x + 4, y + 70), (x - 4, y + 70)])  # 火把杆
    fm = mask_from_poly(polys[0::2])
    pole = mask_from_poly(polys[1::2])
    img = img * (1 - pole[:, :, None] * 0.9)
    img = img + fm[:, :, None] * hexc("#ffd48a") * 1.2 * k + blur(fm, 8)[:, :, None] * FIRE * 1.2 * k
    return img


def sword_flash(img, p0, p1, prog, width=7, col="#e8f2ff", k=1.0, tail=0.55):
    """从 p0 扫向 p1 的剑光；prog 0..1 为扫过进度，之后保留残影衰减由 k 控制。"""
    if k <= 0.01 or prog <= 0:
        return img
    a = max(0.0, prog - tail)
    q0 = (p0[0] + (p1[0] - p0[0]) * a, p0[1] + (p1[1] - p0[1]) * a)
    q1 = (p0[0] + (p1[0] - p0[0]) * prog, p0[1] + (p1[1] - p0[1]) * prog)
    n = 16
    polys = []
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        x0, y0 = q0[0] + (q1[0] - q0[0]) * u0, q0[1] + (q1[1] - q0[1]) * u0
        x1, y1 = q0[0] + (q1[0] - q0[0]) * u1, q0[1] + (q1[1] - q0[1]) * u1
        polys.append(("line", [(x0, y0), (x1, y1)], width * (0.25 + 0.75 * u1)))
    m = mask_from_poly(polys, ss=1)
    c = hexc(col)
    img = img + m[:, :, None] * c * 1.6 * k + blur(m, 14)[:, :, None] * c * 1.4 * k + blur(m, 50)[:, :, None] * hexc("#7fb0ff") * 0.9 * k
    return img


# ---------------------------------------------------------------- 宫墙 / 炭火 / 漆器 / 纸
@lru_cache(maxsize=2)
def palace_wall(seed=4):
    img = vgrad(H, W, hexc("#05070b"), hexc("#141a24"))
    # 墙面
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    tex = fbm(W // 2, H // 2, seed, 6, 6)
    tex = np.asarray(Image.fromarray(tex, "F").resize((W, H), Image.BICUBIC))
    wall = (yy > 560) & (yy < 1500)
    base = hexc("#5a4a3a") * (0.45 + 0.5 * tex[:, :, None])
    img = np.where(wall[:, :, None], base, img)
    # 屋檐（瓦）
    eave = [(-40, 560), (1120, 560), (1120, 520), (1000, 470), (540, 440), (80, 470), (-40, 520)]
    em = mask_from_poly([eave])
    tiles = (np.abs(np.sin(xx / 14)) > 0.75) * 0.25
    img = over(img, hexc("#0c0f15") * (1 + tiles[:, :, None]), em)
    # 地面
    gnd = yy > 1500
    img = np.where(gnd[:, :, None], hexc("#0d1118") * (0.7 + 0.5 * tex[:, :, None]), img)
    return img.astype(np.float32)


def plaster_strokes(t, n_vis, seed=2, region=(160, 700, 920, 1380)):
    """泥刀抹墙：返回 alpha（刷过的新泥）。n_vis 已完成的笔数（可小数）。"""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = region
    polys = []
    full = int(n_vis)
    for i in range(min(24, full + 1)):
        cy = y0 + (i % 12) * (y1 - y0) / 12 + rng.uniform(-10, 10)
        lx0 = x0 + rng.uniform(0, 80)
        lx1 = x1 - rng.uniform(0, 80)
        u = 1.0 if i < full else n_vis - full
        xe = lx0 + (lx1 - lx0) * u
        polys.append([(lx0, cy - 22), (xe, cy - 26), (xe, cy + 24), (lx0, cy + 20)])
    return mask_from_poly(polys, blur_r=6) * 0.7 if polys else np.zeros((H, W), np.float32)


@lru_cache(maxsize=2)
def ember_bed(seed=8):
    """炭火特写：发光裂纹 + 炭块。返回 (base, heat)。"""
    a = fbm(W // 2, H // 2, seed, 6, 7)
    a = np.asarray(Image.fromarray(a, "F").resize((W, H), Image.BICUBIC))
    cells = fbm(W // 2, H // 2, seed + 1, 3, 9)
    cells = np.asarray(Image.fromarray(cells, "F").resize((W, H), Image.BICUBIC))
    cracks = np.exp(-((cells - 0.5) / 0.035) ** 2)
    heat = np.clip(cracks * (0.4 + a) + np.clip(a - 0.7, 0, 1) * 2, 0, 1.5)
    base = hexc("#0d0b0a") * (0.5 + a[:, :, None])
    return base.astype(np.float32), heat.astype(np.float32)


def heat_color(h):
    h = np.clip(h, 0, 1.5)[:, :, None]
    return hexc("#5a0b02") * np.clip(h * 2, 0, 1) + hexc("#ff6a1a") * np.clip(h * 2 - 0.6, 0, 1) + hexc("#ffd27a") * np.clip(h * 2 - 1.6, 0, 1)


def smoke(t, seed=12, k=0.4, col="#6b6f78", rise=40):
    s = _smoke_tex(seed)
    off = int(t * rise) % H
    m = np.roll(s, -off, 0)
    return m[:, :, None] * hexc(col) * k


@lru_cache(maxsize=2)
def _smoke_tex(seed):
    a = fbm(W // 3, H // 3, seed, 5, 3)
    a = np.clip(a - 0.45, 0, 1) * 2
    return np.asarray(Image.fromarray(a, "F").resize((W, H), Image.BICUBIC))


def vessel_polys(cx, cy, s):
    """漆器饮器剪影（圆腹、短足），只做暗影，不做写实。"""
    pts = path([(cx - 1.0 * s, cy - 0.35 * s), (cx - 1.15 * s, cy + 0.35 * s), (cx - 0.55 * s, cy + 0.85 * s),
                (cx - 0.25 * s, cy + 0.9 * s)],
               [(cx - 0.25 * s, cy + 0.9 * s), (cx - 0.28 * s, cy + 1.1 * s)],
               [(cx - 0.28 * s, cy + 1.1 * s), (cx - 0.55 * s, cy + 1.2 * s), (cx + 0.55 * s, cy + 1.2 * s),
                (cx + 0.28 * s, cy + 1.1 * s)],
               [(cx + 0.28 * s, cy + 1.1 * s), (cx + 0.25 * s, cy + 0.9 * s)],
               [(cx + 0.25 * s, cy + 0.9 * s), (cx + 0.55 * s, cy + 0.85 * s), (cx + 1.15 * s, cy + 0.35 * s),
                (cx + 1.0 * s, cy - 0.35 * s)])
    return [pts]


@lru_cache(maxsize=2)
def paper_tex(seed=6, col="#d9cdb0"):
    a = fbm(W // 2, H // 2, seed, 6, 8)
    a = np.asarray(Image.fromarray(a, "F").resize((W, H), Image.BICUBIC))
    fib = fbm(W // 1, 64, seed + 1, 4, 40)
    fib = np.asarray(Image.fromarray(fib, "F").resize((W, H), Image.BICUBIC))
    return (hexc(col) * (0.82 + 0.18 * a[:, :, None]) * (0.95 + 0.05 * fib[:, :, None])).astype(np.float32)


def water_reflect(img, wl, t, k=0.45, seed=3):
    """把水线 wl 以上的画面倒映到水线以下（带波纹扭曲、变暗），再叠河面纹理。"""
    h = H - wl
    rows = np.clip(wl - 1 - np.arange(h) * 1.0, 0, H - 1).astype(int)
    ref = img[rows]
    yy = np.arange(h, dtype=np.float32)
    dx = (np.sin(yy / 7.0 + t * 3.0) * (2 + yy / 60)).astype(int)
    xs = (np.arange(W)[None, :] + dx[:, None]) % W
    ref = ref[np.arange(h)[:, None], xs]
    fade = np.exp(-yy / 520)[:, None, None]
    r, a = river(t, wl, h)
    out = img.copy()
    out[wl:] = r[wl:] + ref * k * fade
    return out
