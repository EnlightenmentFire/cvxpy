# -*- coding: utf-8 -*-
"""Reusable drawn elements (cached Layers). All procedural."""
import functools, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
from gfx import *

CX = W // 2


# ----------------------------------------------------------------------------- background
@functools.lru_cache(maxsize=1)
def bg_base():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top, bot = np.array(BG_TOP, np.float32), np.array(BG_BOT, np.float32)
    g = top * (1 - y) + bot * y
    g = np.repeat(g, W, axis=1)
    # vignette + fine grain
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.45) / (H * 0.7)) ** 2
    g *= (1 - 0.35 * np.clip(v, 0, 1))[..., None]
    n = value_noise(H, W, 6, seed=3, octaves=2)
    g += (n[..., None] - 0.5) * 0.025
    return np.ascontiguousarray(g.astype(np.float32))


@functools.lru_cache(maxsize=4)
def mist_tex(seed, scale=420):
    n = value_noise(H * 2 // 3, W * 2, scale, seed=seed, octaves=5)
    n = np.clip((n - 0.42) * 2.2, 0, 1) ** 1.6
    hh = n.shape[0]
    ramp = np.clip(np.minimum(np.arange(hh), hh - 1 - np.arange(hh)) / 260.0, 0, 1)
    n *= (ramp * ramp * (3 - 2 * ramp))[:, None]
    return n.astype(np.float32)


def draw_mist(frame, t, strength=0.12, color=MIST, seed=1, speed=8.0, y0=0):
    m = mist_tex(seed)
    mh, mw = m.shape
    off = int((t * speed) % (mw - W))
    a = m[:, off:off + W] * strength
    ys = slice(y0, min(H, y0 + mh))
    a = a[: ys.stop - ys.start]
    c = np.array(color, np.float32)
    frame[ys] = frame[ys] * (1 - a[..., None]) + c * a[..., None]


# ----------------------------------------------------------------------------- cave + seated figure
@functools.lru_cache(maxsize=1)
def cave_layers():
    # opening light (dawn haze inside the arch)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = CX, 1000
    d = np.sqrt(((xx - cx) / 520) ** 2 + ((yy - cy) / 760) ** 2)
    glow = np.clip(1 - d, 0, 1) ** 1.5
    light = Layer(0, 0, (glow[..., None] * np.array(hexc("#8c8578"), np.float32) * 0.55).astype(np.float32),
                  np.zeros((H, W), np.float32))
    # rock frame: everything outside a noisy arch
    rng = np.random.default_rng(5)
    mask = Image.new("L", (W, H), 255)
    dr = ImageDraw.Draw(mask)
    pts = []
    n_ = value_noise(1, 400, 18, seed=9, octaves=4)[0]
    for i in range(400):
        th = math.pi * i / 399
        r = 1.0 + (n_[i] - 0.5) * 0.10
        x = cx - math.cos(th) * 400 * r
        y = 700 - math.sin(th) * 430 * r
        pts.append((x, y))
    left = [(cx - 400 + (n_[i % 400] - 0.5) * 50, 700 + i * 12) for i in range(0, 60)]
    right = [(cx + 400 + (n_[(i * 7) % 400] - 0.5) * 50, 700 + i * 12) for i in range(0, 60)]
    poly = left[::-1] + pts + right
    dr.polygon(poly, fill=0)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(2.5)), np.float32) / 255
    tex = value_noise(H, W, 40, seed=11, octaves=5)
    rock = np.array(hexc("#0a0d0f"), np.float32) + (tex[..., None] - 0.5) * 0.06
    # inner rim light on the arch edge
    edge = cv2.GaussianBlur(m, (0, 0), 18) - m
    edge = np.clip(edge * 2.5, 0, 1)
    rim = np.clip(edge, 0, 1)[..., None] * np.array(GOLD, np.float32) * 0.35
    rgb = rock * m[..., None] + rim
    a = np.clip(m + edge * 0.3, 0, 1)
    rock_L = Layer(0, 0, (rgb * 1.0).astype(np.float32), a.astype(np.float32))
    rock_L.rgb = rock * m[..., None] + rim * a[..., None]
    return light, rock_L


@functools.lru_cache(maxsize=2)
def seated_figure(cy=900, s=1.0, col="#07090b"):
    """Frontal seated meditating silhouette with halo and soft rim light."""
    ss = 3
    c = Canvas(CX - 360, cy - 420, 720, 760, ss)
    k = hexc(col)
    ox, oy = CX, cy
    def P(x, y):
        return (ox + x * s, oy + y * s)
    # halo
    c.circle(*P(0, -255), 150 * s, outline=GOLD, a=0.20, width=3)
    # lotus / base
    c.ellipse(*P(0, 255), 300 * s, 46 * s, k)
    for i in range(-4, 5):
        c.ellipse(*P(i * 62, 240), 46 * s, 26 * s, k)
    # legs
    c.ellipse(*P(0, 190), 255 * s, 78 * s, k)
    # torso / robe
    torso = [P(-150, 160), P(-165, 40), P(-140, -70), P(-105, -140), P(-55, -168), P(55, -168), P(105, -140),
             P(140, -70), P(165, 40), P(150, 160)]
    c.poly(torso, k)
    # arms & hands in lap
    c.ellipse(*P(0, 120), 120 * s, 50 * s, k)
    # neck
    c.poly([P(-30, -175), P(30, -175), P(26, -200), P(-26, -200)], k)
    # head
    c.ellipse(*P(0, -258), 58 * s, 70 * s, k)
    c.ellipse(*P(0, -330), 26 * s, 22 * s, k)  # ushnisha
    c.ellipse(*P(-60, -240), 12 * s, 38 * s, k)
    c.ellipse(*P(60, -240), 12 * s, 38 * s, k)
    L = c.layer()
    # rim light: blurred alpha minus alpha, warm
    G = blur_layer(L, 6, pad=20)
    inner = np.zeros_like(G.a)
    inner[20:20 + L.h, 20:20 + L.w] = L.a
    rim = np.clip(G.a - inner, 0, 1) * 0.0
    edge = np.clip(cv2.GaussianBlur(inner, (0, 0), 2) - cv2.erode(inner, np.ones((5, 5), np.uint8)), 0, 1)
    edge *= np.linspace(1.0, 0.2, edge.shape[0], dtype=np.float32)[:, None]
    R = Layer(G.x, G.y, (edge[..., None] * np.array(GOLD, np.float32) * 0.7).astype(np.float32),
              np.zeros_like(edge))
    return L, R


# ----------------------------------------------------------------------------- brain (sagittal, line art)
BRAIN_C = (CX, 830)
NODES = {  # name: (x, y, label)
    "mpfc": (CX - 235, 815, "内侧前额叶"),
    "pcc": (CX + 95, 735, "后扣带回"),
    "dacc": (CX - 95, 700, "背侧前扣带回"),
    "dlpfc": (CX - 185, 610, "调控注意的前额叶（外侧）"),
    "mtl": (CX + 10, 935, "内侧颞叶"),
    "ang": (CX + 250, 700, "顶叶"),
}


def brain_outline_pts(n=600, sx=1.0, sy=1.0, cx=None, cy=None):
    cx = BRAIN_C[0] if cx is None else cx
    cy = BRAIN_C[1] if cy is None else cy
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        rx, ry = 345, 250
        x = math.cos(th) * rx
        y = -math.sin(th) * ry
        # flatten bottom, frontal bulge (left = frontal), occipital point (right)
        if y > 0:
            y *= 0.62 + 0.25 * max(0, -math.cos(th))
        if math.cos(th) < 0:
            x *= 1.04
            y *= 1.0 + 0.06 * (-math.cos(th))
        if math.cos(th) > 0.6 and y > -60:
            x *= 1.03
        pts.append((cx + x * sx, cy + y * sy))
    return pts


@functools.lru_cache(maxsize=2)
def brain_layer(col=WHITE, alpha=0.55):
    c = Canvas(CX - 420, BRAIN_C[1] - 330, 840, 640, 2)
    pts = brain_outline_pts()
    c.line(pts + [pts[0]], col, 4, alpha)
    # temporal notch line
    c.line([(CX - 180, 905), (CX - 60, 925), (CX + 60, 925), (CX + 150, 905)], col, 2.5, alpha * 0.6)
    # cerebellum
    cbx, cby = CX + 255, 975
    c.ellipse(cbx, cby, 105, 62, outline=col, a=alpha, width=3)
    for k in range(1, 4):
        c.ellipse(cbx + 5, cby + 4, 105 - k * 22, 62 - k * 13, outline=col, a=alpha * 0.35, width=1.5)
    # brainstem
    c.line([(CX + 120, 935), (CX + 140, 1010), (CX + 145, 1090)], col, 3, alpha)
    c.line([(CX + 60, 940), (CX + 85, 1010), (CX + 95, 1090)], col, 3, alpha)
    # corpus callosum arc
    cc = [(CX - 150 + 300 * u, 790 - 70 * math.sin(math.pi * u) ** 0.8) for u in np.linspace(0, 1, 60)]
    c.line(cc, col, 6, alpha * 0.55)
    cc2 = [(CX - 130 + 260 * u, 812 - 52 * math.sin(math.pi * u) ** 0.8) for u in np.linspace(0, 1, 60)]
    c.line(cc2, col, 2, alpha * 0.4)
    # sulci: smooth random curves inside the cortex band
    rng = np.random.default_rng(21)
    for k in range(26):
        th = rng.uniform(0.05, math.pi - 0.05) if k < 22 else rng.uniform(math.pi + 0.3, math.pi + 0.9)
        r0 = rng.uniform(0.62, 0.9)
        L = rng.uniform(0.10, 0.26)
        seg = []
        for u in np.linspace(0, 1, 24):
            r = r0 + L * u
            a = th + 0.18 * math.sin(u * 5 + k)
            x = CX + math.cos(a) * 345 * r
            y = BRAIN_C[1] - math.sin(a) * 250 * r * (0.9 if math.sin(a) > 0 else 0.6)
            seg.append((x, y))
        c.line(seg, col, 2.2, alpha * 0.45)
    return c.layer()


def glow_blob(x, y, r, col, inten=1.0):
    s = int(r * 3)
    yy, xx = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
    g = np.exp(-(xx ** 2 + yy ** 2) / (2 * r * r)) * inten
    return Layer(x - s, y - s, (g[..., None] * np.array(col, np.float32)).astype(np.float32), np.zeros_like(g))


@functools.lru_cache(maxsize=64)
def ink_blot(x, y, r, col=GOLD, seed=0):
    """Ink-wash bleed blob (alpha), irregular edge."""
    s = int(r * 2.2)
    n = value_noise(2 * s + 1, 2 * s + 1, r * 0.5, seed=seed, octaves=4)
    yy, xx = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
    d = np.sqrt(xx ** 2 + yy ** 2) / r + (n - 0.5) * 0.7
    a = np.clip(1.15 - d, 0, 1) ** 0.8
    a = cv2.GaussianBlur(a, (0, 0), r * 0.08 + 1)
    a *= 0.85
    return Layer(x - s, y - s, (a[..., None] * np.array(col, np.float32)).astype(np.float32), a.astype(np.float32))


def node_label(name, col=WHITE, side=None, dy=0):
    x, y, lab = NODES[name]
    side = side or ("l" if x < CX else "r")
    if side == "l":
        return text_layer(lab, ("serif", 34, 600), col, x - 40, y - 62 + dy, anchor="rm")
    return text_layer(lab, ("serif", 34, 600), col, x + 40, y - 62 + dy, anchor="lm")


# ----------------------------------------------------------------------------- paper card
@functools.lru_cache(maxsize=64)
def paper_card(lines, src, y=830, width=920, fnt=("kaim", 58), lh=1.55, seal=None, src_size=30, align="m",
               small=None):
    """Rice-paper card with classical text. lines: tuple of str. small: optional tuple of extra lines (white-on-paper smaller)."""
    f = font(*fnt)
    asc, desc = f.getmetrics()
    lhp = int(fnt[1] * lh)
    small = small or ()
    fs = font("serif", 30, 400)
    h = 110 + lhp * len(lines) + (len(small) * 44 + 20 if small else 0) + 80
    x0, y0 = CX - width // 2, y - h // 2
    ss = 2
    img = Image.new("RGBA", (width * ss, h * ss), (0, 0, 0, 0))
    # paper with deckle edge
    tex = value_noise(h * ss, width * ss, 30, seed=len(src), octaves=5)
    edge_n = value_noise(h * ss, width * ss, 6, seed=7, octaves=3)
    yy, xx = np.mgrid[0:h * ss, 0:width * ss].astype(np.float32)
    dist = np.minimum.reduce([xx, yy, width * ss - 1 - xx, h * ss - 1 - yy])
    a = np.clip((dist - 4 - edge_n * 14) / 6, 0, 1)
    base = np.array(PAPER, np.float32) * (0.93 + 0.1 * tex[..., None])
    fib = value_noise(h * ss, width * ss, 3, seed=4, octaves=2)
    base -= (fib[..., None] > 0.72) * 0.03
    arr = np.concatenate([base, a[..., None]], axis=2)
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    fS = font(fnt[0], fnt[1] * ss, fnt[2] if len(fnt) > 2 else None)
    ty = 70 * ss
    for i, l in enumerate(lines):
        if align == "m":
            d.text((width * ss / 2, ty + i * lhp * ss), l, font=fS, fill=(28, 27, 25, 255), anchor="mt")
        else:
            d.text((70 * ss, ty + i * lhp * ss), l, font=fS, fill=(28, 27, 25, 255), anchor="lt")
    yy2 = ty + len(lines) * lhp * ss + 10 * ss
    fsS = font("serif", 30 * ss, 500)
    for i, l in enumerate(small):
        d.text((width * ss / 2, yy2 + i * 44 * ss), l, font=fsS, fill=(74, 71, 65, 255), anchor="mt")
    # source
    fsrc = font("serif", src_size * ss, 500)
    d.text((width * ss - 70 * ss, h * ss - 50 * ss), src, font=fsrc, fill=(90, 84, 74, 255), anchor="rm")
    if seal:
        sx, sy = 70 * ss, h * ss - 50 * ss
        d.rounded_rectangle([sx, sy - 26 * ss, sx + 52 * ss, sy + 26 * ss], radius=4 * ss, fill=(178, 64, 46, 235))
        d.text((sx + 26 * ss, sy), seal, font=font("brush", 30 * ss), fill=(240, 230, 214, 255), anchor="mm")
    img = img.resize((width, h), Image.LANCZOS)
    L = layer_from_pil(img, x0, y0, trim=False)
    # soft shadow
    S = blur_layer(L, 14)
    S.rgb = np.zeros_like(S.rgb)
    S.a = S.a * 0.55
    S.y += 10
    return [S, L]


# ----------------------------------------------------------------------------- tags
TAG_COL = {"实证": TEAL, "小样本": CINNABAR, "类比": GOLD_D, "理论": INDIGO, "争议": CINNABAR, "推断": CINNABAR,
           "相关": CINNABAR, "局限": CINNABAR, "经文": GOLD_D, "示意": GREY}


@functools.lru_cache(maxsize=64)
def tag_layer(text):
    parts = text.split(" · ")
    f = font("serif", 32, 700)
    widths = [int(f.getlength(p)) + 36 for p in parts]
    tot = sum(widths) + 10 * (len(parts) - 1)
    x = W - 60 - tot
    c = Canvas(x - 4, 120, tot + 8, 70, 3)
    for p, w_ in zip(parts, widths):
        key = next((k for k in TAG_COL if k in p), "示意")
        col = TAG_COL[key]
        c.rrect(x, 128, x + w_, 178, 8, c=col, a=0.22, outline=col, width=2)
        c.text(x + w_ / 2, 153, p, ("serif", 32, 700), WHITE)
        x += w_ + 10
    return c.layer()


# ----------------------------------------------------------------------------- lamp
@functools.lru_cache(maxsize=2)
def lamp_body(cx=CX, base_y=1150):
    c = Canvas(cx - 260, base_y - 330, 520, 360, 3)
    k = hexc("#2b2620")
    rim = hexc("#6a5a45")
    # stand
    c.poly([(cx - 30, base_y - 170), (cx + 30, base_y - 170), (cx + 22, base_y - 20), (cx - 22, base_y - 20)], k)
    c.ellipse(cx, base_y - 10, 120, 22, k)
    c.ellipse(cx, base_y - 14, 120, 18, outline=rim, width=2, a=0.6)
    # dish
    c.poly([(cx - 150, base_y - 220), (cx + 150, base_y - 220), (cx + 100, base_y - 172), (cx - 100, base_y - 172)], k)
    c.ellipse(cx, base_y - 220, 150, 20, hexc("#3a3128"))
    c.ellipse(cx, base_y - 220, 150, 20, outline=rim, width=2, a=0.7)
    # wick
    c.line([(cx, base_y - 222), (cx + 4, base_y - 250)], hexc("#191512"), 6)
    return c.layer()


def flame_layers(t, cx=CX, wick_y=900, wind=0.0, seed=0):
    """Return (glow_add_layer, flame_layer). wind in [0,1] tilts and detaches the flame."""
    rng_t = t * 7.0
    fl = 1 + 0.06 * math.sin(rng_t * 2.3 + seed) + 0.04 * math.sin(rng_t * 5.1)
    tilt = wind * (0.9 * math.sin(t * 1.7) + 0.5 * math.sin(t * 3.9 + 1))
    lift = wind * (8 + 10 * (0.5 + 0.5 * math.sin(t * 2.6)))
    hgt = 95 * fl
    wdt = 26 * (1 + 0.05 * math.sin(rng_t * 3.3))
    c = Canvas(cx - 160, wick_y - 220, 320, 260, 2)
    pts = []
    for u in np.linspace(0, 1, 50):
        # teardrop: width profile
        wv = wdt * math.sin(math.pi * u ** 0.75) * (1 - u) ** 0.35
        y = wick_y - 6 - lift - u * hgt
        xoff = tilt * 70 * u ** 1.6
        pts.append((cx + xoff + wv, y))
    pts2 = []
    for u in np.linspace(1, 0, 50):
        wv = wdt * math.sin(math.pi * u ** 0.75) * (1 - u) ** 0.35
        y = wick_y - 6 - lift - u * hgt
        xoff = tilt * 70 * u ** 1.6
        pts2.append((cx + xoff - wv, y))
    c.poly(pts + pts2, hexc("#ffd38a"), a=0.95)
    inner = [(x * 0.55 + (cx + tilt * 20) * 0.45, y + 0.25 * (wick_y - y)) for x, y in pts + pts2]
    c.poly(inner, hexc("#fff4d8"), a=0.9)
    F = c.layer()
    F = blur_layer(F, 1.6)
    gx = cx + tilt * 30
    G = glow_blob(int(gx), int(wick_y - 50 - lift), 70 * fl, hexc("#ffb85a"), 0.45)
    G2 = glow_blob(int(gx), int(wick_y - 40), 260, hexc("#c78b45"), 0.16 * fl)
    return [("add", G2), ("add", G), F]


# ----------------------------------------------------------------------------- ink arrow
@functools.lru_cache(maxsize=4)
def ink_arrow(length=520, col=PAPER, seed=0):
    """Horizontal ink-brush arrow pointing right, tip at local (length, 0). Returns Layer with x,y relative to tip."""
    c = Canvas(0, 0, length + 40, 120, 3)
    y = 60
    # tapered shaft
    pts_top, pts_bot = [], []
    rng = np.random.default_rng(seed)
    for u in np.linspace(0, 1, 40):
        w = 3 + 4.5 * math.sin(math.pi * u) + rng.uniform(-0.4, 0.4)
        x = 20 + u * (length - 60)
        pts_top.append((x, y - w))
        pts_bot.append((x, y + w))
    c.poly(pts_top + pts_bot[::-1], col, a=0.95)
    # head
    tip = 20 + length
    c.poly([(tip, y), (tip - 70, y - 26), (tip - 52, y), (tip - 70, y + 26)], col, a=0.95)
    # fletching
    for k in range(3):
        x = 30 + k * 18
        c.poly([(x, y), (x - 26, y - 30), (x - 14, y - 30), (x + 12, y)], col, a=0.75)
        c.poly([(x, y), (x - 26, y + 30), (x - 14, y + 30), (x + 12, y)], col, a=0.75)
    L = c.layer()
    L.x -= 20 + length
    L.y -= 60
    return L


def place(L, x, y, angle=0.0):
    """Rotate layer about its local origin (0,0 = tip) and place at (x, y)."""
    h, w = L.h, L.w
    ox, oy = -L.x, -L.y  # origin inside layer
    if abs(angle) > 1e-3:
        M = cv2.getRotationMatrix2D((ox, oy), -math.degrees(angle), 1.0)
        cs, sn = abs(M[0, 0]), abs(M[0, 1])
        nw, nh = int(h * sn + w * cs) + 4, int(h * cs + w * sn) + 4
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        rgb = cv2.warpAffine(L.rgb, M, (nw, nh), flags=cv2.INTER_LINEAR)
        a = cv2.warpAffine(L.a, M, (nw, nh), flags=cv2.INTER_LINEAR)
        nox = M[0, 0] * ox + M[0, 1] * oy + M[0, 2]
        noy = M[1, 0] * ox + M[1, 1] * oy + M[1, 2]
        return Layer(x - nox, y - noy, rgb, a)
    return Layer(x - ox, y - oy, L.rgb, L.a)


def smoke_layer(t, x, y, n=60, seed=0, col=PAPER, spread=1.0):
    """Particles drifting up/out; t in [0, 1+]."""
    rng = np.random.default_rng(seed)
    pad = 260
    img = np.zeros((2 * pad, 2 * pad), np.float32)
    for i in range(n):
        ang = rng.uniform(-math.pi, 0.2)
        sp = rng.uniform(40, 200) * spread
        px = pad + math.cos(ang) * sp * t + rng.uniform(-200, 30)
        py = pad + math.sin(ang) * sp * t * 0.8 - 60 * t * t + rng.uniform(-8, 8)
        r = rng.uniform(5, 16) * (1 + 1.5 * t)
        if 0 <= px < 2 * pad and 0 <= py < 2 * pad:
            cv2.circle(img, (int(px), int(py)), int(r), float(rng.uniform(0.3, 0.8)), -1, cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 6 + 10 * t)
    a = np.clip(img, 0, 1) * max(0, 1 - t) * 0.9
    return Layer(x - pad, y - pad, (a[..., None] * np.array(col, np.float32)).astype(np.float32), a)
