"""Procedural illustrations (no external images, no logos)."""
import math
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from engine import hexrgb, set_color

# ====================================================================== church tower painting
@lru_cache(maxsize=2)
def church_painting(w=600, h=760):
    """A small colourful painting of an English Perpendicular parish-church tower.
    (The 2024 Nature experiment started from a Wikipedia passage about such towers.)"""
    im = Image.new("RGB", (w, h))
    px = np.zeros((h, w, 3), np.float32)
    top, bot = np.array([62, 128, 186]), np.array([246, 214, 160])
    for y in range(h):
        t = min(1, y / (h * 0.78))
        px[y, :] = top * (1 - t) + bot * t
    im = Image.fromarray(px.astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    # sun + clouds
    for r, a in [(90, 40), (70, 60), (48, 255)]:
        d.ellipse([470 - r, 150 - r, 470 + r, 150 + r], fill=(255, 214, 107, a))
    for cx, cy, s in [(140, 120, 1.0), (330, 80, 0.7), (520, 300, 0.6)]:
        for dx, dy, r in [(-40, 6, 30), (0, -8, 40), (42, 4, 32), (10, 14, 34)]:
            rr = r * s
            d.ellipse([cx + dx * s - rr, cy + dy * s - rr, cx + dx * s + rr, cy + dy * s + rr],
                      fill=(255, 255, 255, 200))
    # hills + ground
    d.polygon([(0, 560), (120, 520), (260, 545), (420, 505), (600, 540), (600, 760), (0, 760)], fill=(118, 160, 102))
    d.polygon([(0, 640), (600, 610), (600, 760), (0, 760)], fill=(86, 138, 70))
    d.polygon([(300, 760), (340, 660), (380, 660), (450, 760)], fill=(205, 182, 138))
    # nave
    d.polygon([(40, 470), (290, 470), (290, 650), (40, 650)], fill=(196, 178, 146))
    d.polygon([(30, 472), (165, 395), (300, 472)], fill=(128, 62, 46))
    for wx in (80, 150, 220):
        d.rectangle([wx, 520, wx + 34, 590], fill=(52, 60, 84))
        d.pieslice([wx, 503, wx + 34, 537], 180, 360, fill=(52, 60, 84))
        d.line([wx + 17, 508, wx + 17, 590], fill=(120, 140, 175), width=2)
    # tower body (with right-side shading)
    d.rectangle([280, 190, 440, 660], fill=(206, 188, 152))
    d.rectangle([400, 190, 440, 660], fill=(170, 150, 118))
    # buttresses
    for bx in (268, 432):
        for k, (y0, y1) in enumerate([(200, 330), (330, 480), (480, 660)]):
            ww = 14 + k * 4
            d.rectangle([bx - k * 2, y0, bx + ww - k * 2, y1], fill=(184, 166, 132))
    # battlements + pinnacles
    for i in range(9):
        if i % 2 == 0:
            d.rectangle([280 + i * 17.8, 172, 280 + (i + 1) * 17.8, 192], fill=(206, 188, 152))
    for pxx in (272, 360, 448):
        d.polygon([(pxx - 12, 192), (pxx, 110), (pxx + 12, 192)], fill=(190, 172, 136))
        d.ellipse([pxx - 4, 102, pxx + 4, 112], fill=(190, 172, 136))
    # belfry louvred window
    d.rectangle([326, 250, 394, 330], fill=(40, 40, 52))
    d.pieslice([326, 216, 394, 284], 180, 360, fill=(40, 40, 52))
    for ly in range(262, 330, 11):
        d.line([328, ly, 392, ly + 4], fill=(150, 132, 100), width=3)
    # clock
    d.ellipse([328, 352, 392, 416], fill=(244, 235, 213), outline=(90, 70, 50), width=3)
    d.line([360, 384, 360, 362], fill=(40, 30, 20), width=3)
    d.line([360, 384, 376, 392], fill=(40, 30, 20), width=3)
    # great west window with perpendicular tracery
    d.rectangle([316, 486, 404, 596], fill=(40, 70, 112))
    d.pieslice([316, 442, 404, 530], 180, 360, fill=(40, 70, 112))
    for mx in (338, 360, 382):
        d.line([mx, 460, mx, 596], fill=(208, 196, 168), width=3)
    d.line([316, 530, 404, 530], fill=(208, 196, 168), width=3)
    for gx, gy, col in [(327, 560, (196, 64, 60)), (349, 505, (230, 186, 70)), (371, 565, (80, 150, 90)), (393, 512, (196, 64, 60))]:
        d.rectangle([gx - 7, gy - 12, gx + 7, gy + 12], fill=col)
    # door
    d.rectangle([340, 616, 380, 660], fill=(96, 58, 40))
    d.pieslice([340, 596, 380, 636], 180, 360, fill=(96, 58, 40))
    # trees
    for cx, cy, r, col in [(520, 560, 70, (47, 90, 52)), (565, 520, 55, (63, 110, 63)), (470, 600, 50, (55, 100, 58)),
                           (40, 600, 45, (50, 96, 56))]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    d.rectangle([515, 600, 528, 660], fill=(80, 56, 36))
    # birds
    for bx, by in [(150, 230), (185, 205), (210, 245)]:
        d.line([bx - 12, by - 6, bx, by, bx + 12, by - 6], fill=(40, 40, 50), width=3)
    # a few red flowers (rare details -> the first to vanish)
    rng = np.random.default_rng(3)
    for _ in range(26):
        fx, fy = rng.uniform(20, 580), rng.uniform(675, 750)
        d.ellipse([fx - 4, fy - 4, fx + 4, fy + 4], fill=(220, 60, 80) if rng.random() < .6 else (250, 220, 80))
    return im


def photocopy(im, gen, seed=7):
    """Simulate copying a copy `gen` times: blur, fewer colours (rare colours vanish first),
    desaturation, contrast creep, toner specks and slight misregistration."""
    rng = np.random.default_rng(seed)
    out = im.copy()
    w, h = out.size
    for g in range(1, gen + 1):
        out = out.filter(ImageFilter.GaussianBlur(1.1 + 0.25 * g))
        k = max(2, int(48 / (1.7 ** g)))
        out = out.quantize(colors=k, method=Image.Quantize.MEDIANCUT).convert("RGB")
        out = ImageEnhance.Color(out).enhance(0.62)
        out = ImageEnhance.Contrast(out).enhance(1.06)
        dx, dy = rng.integers(-3, 4, 2)
        out = out.transform(out.size, Image.Transform.AFFINE, (1.005, 0, dx, 0, 1.005, dy),
                            resample=Image.Resampling.BILINEAR, fillcolor=(226, 226, 222))
        arr = np.asarray(out).astype(np.float32)
        arr = arr * 0.93 + 0.07 * arr.mean(axis=(0, 1), keepdims=True)   # drift to the average
        n = rng.random((h, w)) < 0.0025 * g
        arr[n] *= 0.35
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return out


# ====================================================================== pixel jackrabbit
RABBIT = [
    "........EE.EE...........",
    "........EPEEPE..........",
    "........EPEEPE..........",
    "........EPEEPE..........",
    "........EPEEPE..........",
    ".........EPEEPE.........",
    ".........EEEEEE.........",
    "......HHHHHHHHH.........",
    ".....HHHHHHHHHHH........",
    "....HHKHHHHHHHHHH.......",
    "...NHHHHHHHHHHHHHBBB....",
    "....HHHHHHHHHHHBBBBBBB..",
    "......HHHHHHBBBBBBBBBBT.",
    ".......BBBBBBBBBBBBBBBTT",
    "......BBBBBBBBBBBBBBBBTT",
    "......BBBBBBBBBBBBBBBBB.",
    ".......BBBBBBBBBBBBBBB..",
    ".......FF.BBBBBBBBBBB...",
    "......FFF..FFFFFFFFF....",
]
RABBIT_COLORS = {
    "E": "#C9B79A", "P": "#F2A7B4", "H": "#D9C7A8", "K": "#1A1A1A", "N": "#E58A9A",
    "B": "#CDB997", "F": "#B9A584",
}
TAIL_COLORS = ["#2A2A2A", "#FFFFFF", "#3B82F6", "#E5484D", "#F5C542"]  # black, white, blue, red, yellow


def draw_pixel_rabbit(ctx, x, y, px=16, tail_color="#F5C542", alpha=1.0, outline=True):
    """Top-left at (x, y); each pixel is px wide."""
    rows = RABBIT
    if outline:
        set_color(ctx, "#05070B", alpha)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch != ".":
                    ctx.rectangle(x + c * px - px * 0.25, y + r * px - px * 0.25, px * 1.5, px * 1.5)
        ctx.fill()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            col = tail_color if ch == "T" else RABBIT_COLORS[ch]
            set_color(ctx, col, alpha)
            ctx.rectangle(x + c * px, y + r * px, px + 0.5, px + 0.5)
            ctx.fill()
    return len(rows[0]) * px, len(rows) * px


# ====================================================================== ox (engraving)
def ox_path(ctx, ox, oy, s):
    """Profile of a fat ox facing left, in a ~1000x620 box scaled by s."""
    P = lambda x, y: (ox + x * s, oy + y * s)
    ctx.new_path()
    ctx.move_to(*P(368, 148))
    ctx.curve_to(*P(480, 132), *P(640, 150), *P(760, 140))           # back
    ctx.curve_to(*P(830, 134), *P(872, 160), *P(880, 214))           # rump
    ctx.curve_to(*P(892, 290), *P(880, 360), *P(850, 420))           # buttock
    ctx.curve_to(*P(842, 470), *P(846, 520), *P(842, 566))           # rear leg (far edge)
    ctx.line_to(*P(800, 566))
    ctx.curve_to(*P(798, 520), *P(790, 470), *P(770, 440))           # hock inner
    ctx.curve_to(*P(750, 430), *P(732, 436), *P(728, 470))
    ctx.curve_to(*P(726, 510), *P(730, 540), *P(728, 566))           # near rear leg
    ctx.line_to(*P(686, 566))
    ctx.curve_to(*P(684, 520), *P(684, 470), *P(676, 430))
    ctx.curve_to(*P(560, 452), *P(440, 450), *P(380, 432))           # belly
    ctx.curve_to(*P(376, 480), *P(380, 520), *P(378, 566))           # front leg (back edge)
    ctx.line_to(*P(334, 566))
    ctx.curve_to(*P(336, 520), *P(330, 480), *P(322, 440))
    ctx.curve_to(*P(312, 470), *P(312, 520), *P(312, 566))           # far front leg
    ctx.line_to(*P(272, 566))
    ctx.curve_to(*P(270, 500), *P(262, 440), *P(258, 400))
    ctx.curve_to(*P(236, 380), *P(222, 360), *P(214, 330))           # dewlap
    ctx.curve_to(*P(196, 318), *P(170, 300), *P(150, 282))           # jaw
    ctx.curve_to(*P(120, 268), *P(96, 262), *P(84, 238))             # muzzle
    ctx.curve_to(*P(76, 220), *P(80, 196), *P(96, 184))              # nose
    ctx.curve_to(*P(116, 160), *P(136, 140), *P(160, 126))           # face
    ctx.curve_to(*P(168, 104), *P(186, 84), *P(214, 76))             # horn outer
    ctx.curve_to(*P(200, 92), *P(192, 110), *P(196, 124))            # horn inner
    ctx.curve_to(*P(226, 116), *P(250, 122), *P(262, 132))           # ear
    ctx.curve_to(*P(300, 128), *P(336, 140), *P(368, 148))           # neck top
    ctx.close_path()


def tail_path(ctx, ox, oy, s):
    P = lambda x, y: (ox + x * s, oy + y * s)
    ctx.new_path()
    ctx.move_to(*P(872, 176))
    ctx.curve_to(*P(910, 230), *P(904, 330), *P(896, 420))
    ctx.curve_to(*P(910, 440), *P(906, 470), *P(890, 486))
    ctx.curve_to(*P(872, 470), *P(874, 440), *P(886, 420))
    ctx.curve_to(*P(892, 330), *P(896, 240), *P(864, 190))
    ctx.close_path()


def hatch(ctx, x0, y0, x1, y1, spacing=7, angle=-35, width=1.6, color="#2B2117", alpha=1.0):
    """Hatch lines across a bounding box (caller sets clip)."""
    set_color(ctx, color, alpha)
    ctx.set_line_width(width)
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0) / 2 + 10
    k = -R
    while k <= R:
        px, py = cx + nx * k, cy + ny * k
        ctx.move_to(px - dx * R, py - dy * R)
        ctx.line_to(px + dx * R, py + dy * R)
        k += spacing
    ctx.stroke()


def draw_ox_engraving(ctx, ox, oy, s, ink="#2B2117", paper="#EFE6D0"):
    # body fill (paper tone) + hatching for volume
    ox_path(ctx, ox, oy, s)
    set_color(ctx, "#E4D7B8")
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    hatch(ctx, ox, oy, ox + 1000 * s, oy + 620 * s, spacing=6.5 * s * 1.2, angle=-32, width=1.1, color=ink, alpha=0.55)
    # shadow side: cross hatch on belly / legs / neck underside
    ctx.new_path()
    ctx.save()
    ctx.translate(ox + 560 * s, oy + 470 * s)
    ctx.scale(420 * s, 140 * s)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.clip()
    hatch(ctx, ox, oy, ox + 1000 * s, oy + 620 * s, spacing=5 * s * 1.2, angle=40, width=1.0, color=ink, alpha=0.6)
    ctx.restore()
    # outline
    ox_path(ctx, ox, oy, s)
    set_color(ctx, ink)
    ctx.set_line_width(3.2 * s * 1.3)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    tail_path(ctx, ox, oy, s)
    set_color(ctx, ink)
    ctx.fill()
    # eye
    set_color(ctx, ink)
    ctx.arc(ox + 150 * s, oy + 170 * s, 7 * s, 0, 2 * math.pi)
    ctx.fill()
    # ground line + grass strokes
    ctx.set_line_width(2.2)
    ctx.move_to(ox + 180 * s, oy + 570 * s)
    ctx.line_to(ox + 960 * s, oy + 570 * s)
    ctx.stroke()
    rng = np.random.default_rng(5)
    for i in range(70):
        gx = ox + rng.uniform(150, 980) * s
        gy = oy + 572 * s
        ctx.move_to(gx, gy)
        ctx.line_to(gx + rng.uniform(-6, 6) * s, gy + rng.uniform(6, 16) * s)
    ctx.set_line_width(1.2)
    ctx.stroke()


# ====================================================================== Greek urn
def urn_path(ctx, cx, top, s):
    """Amphora-like profile, centre x, top y, scale s (height ~ 440*s)."""
    prof = [(46, 0), (40, 14), (30, 30), (30, 66), (60, 96), (112, 136), (134, 210), (128, 290),
            (100, 360), (62, 404), (42, 420), (44, 432), (66, 446)]
    pts_r = [(cx + x * s, top + y * s) for x, y in prof]
    pts_l = [(cx - x * s, top + y * s) for x, y in reversed(prof)]
    ctx.new_path()
    ctx.move_to(*pts_r[0])
    for i in range(1, len(pts_r)):
        x0, y0 = pts_r[i - 1]
        x1, y1 = pts_r[i]
        ctx.curve_to(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, x1, y1)
    ctx.line_to(*pts_l[0])
    for i in range(1, len(pts_l)):
        x0, y0 = pts_l[i - 1]
        x1, y1 = pts_l[i]
        ctx.curve_to(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, x1, y1)
    ctx.close_path()


def draw_urn(ctx, cx, top, s, clay="#C8643B", black="#120D0A", label=None):
    urn_path(ctx, cx, top, s)
    set_color(ctx, clay)
    ctx.fill_preserve()
    set_color(ctx, black)
    ctx.set_line_width(3)
    ctx.stroke()
    # handles
    ctx.set_line_width(9 * s)
    set_color(ctx, clay)
    for sign in (-1, 1):
        ctx.new_path()
        ctx.move_to(cx + sign * 32 * s, top + 40 * s)
        ctx.curve_to(cx + sign * 110 * s, top + 20 * s, cx + sign * 130 * s, top + 90 * s, cx + sign * 96 * s, top + 118 * s)
        ctx.stroke()
    # decoration bands (black on clay)
    ctx.save()
    urn_path(ctx, cx, top, s)
    ctx.clip()
    set_color(ctx, black)
    ctx.rectangle(cx - 200 * s, top + 140 * s, 400 * s, 10 * s)
    ctx.rectangle(cx - 200 * s, top + 300 * s, 400 * s, 10 * s)
    ctx.fill()
    meander(ctx, cx - 160 * s, top + 160 * s, 320 * s, 34 * s, black)
    # tongues near the foot
    for i in range(-8, 9):
        x = cx + i * 18 * s
        ctx.move_to(x - 7 * s, top + 330 * s)
        ctx.curve_to(x - 7 * s, top + 370 * s, x + 7 * s, top + 370 * s, x + 7 * s, top + 330 * s)
        ctx.close_path()
    ctx.fill()
    ctx.restore()
    return


def meander(ctx, x, y, w, h, color, alpha=1.0, lw=None):
    """Greek key band from (x,y), width w, height h."""
    set_color(ctx, color, alpha)
    u = h / 5.0
    lw = lw or u * 0.9
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
    n = int(w // (5 * u))
    for i in range(n):
        x0 = x + i * 5 * u
        pts = [(0, 5), (0, 0), (4, 0), (4, 3.5), (1.5, 3.5), (1.5, 1.5), (2.6, 1.5)]
        ctx.move_to(x0 + pts[0][0] * u, y + pts[0][1] * u)
        for px, py in pts[1:]:
            ctx.line_to(x0 + px * u, y + py * u)
        ctx.move_to(x0, y + 5 * u)
        ctx.line_to(x0 + 5 * u, y + 5 * u)
    ctx.stroke()


# ====================================================================== corn plant (top view)
def corn_plant(ctx, cx, cy, r, healthy=1.0, rot=0.0, seed=0):
    """Top-down maize plant: eight leaves radiating from a centre. healthy 1 = green, 0 = blighted."""
    green = np.array(hexrgb("#4E8A35")[:3])
    green2 = np.array(hexrgb("#7FB04A")[:3])
    sick = np.array(hexrgb("#B79A3A")[:3])
    dead = np.array(hexrgb("#7A5A2A")[:3])
    h = max(0.0, min(1.0, healthy))
    base = green * h + (sick * min(1, (1 - h) * 2) + dead * max(0, (1 - h) * 2 - 1)) * (1 - h) / max(1e-6, (1 - h)) * (1 - h) if h < 1 else green
    if h < 1:
        t = 1 - h
        base = green * (1 - t) + (sick if t < 0.6 else dead) * t
    for i in range(8):
        a = rot + i * math.pi / 4 + (0.12 if i % 2 else -0.08)
        L = r * (1.0 if i % 2 == 0 else 0.78)
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(a)
        ctx.new_path()
        ctx.move_to(0, 0)
        ctx.curve_to(L * 0.3, -r * 0.16, L * 0.75, -r * 0.12, L, r * 0.04)
        ctx.curve_to(L * 0.7, r * 0.12, L * 0.3, r * 0.12, 0, 0)
        c = base if i % 2 == 0 else (base * 0.85 + green2 * 0.15 * h)
        ctx.set_source_rgba(*c, 1)
        ctx.fill_preserve()
        ctx.set_source_rgba(*(c * 0.6), 1)
        ctx.set_line_width(1.2)
        ctx.stroke()
        ctx.restore()
    ctx.set_source_rgba(*(base * 0.7 + 0.2), 1)
    ctx.arc(cx, cy, r * 0.12, 0, 2 * math.pi)
    ctx.fill()
    if h < 0.75:
        rng = np.random.default_rng(seed)
        ctx.set_source_rgba(0.35, 0.22, 0.1, 0.8 * (1 - h))
        for _ in range(5):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(0.2, 0.8) * r
            ctx.arc(cx + math.cos(a) * d, cy + math.sin(a) * d, r * 0.05, 0, 2 * math.pi)
            ctx.fill()


# ====================================================================== gear
def gear_path(ctx, cx, cy, r, teeth, rot=0.0, depth=None):
    depth = depth or r * 0.16
    ctx.new_path()
    n = teeth * 4
    for i in range(n + 1):
        a = rot + i * 2 * math.pi / n
        k = i % 4
        rr = r if k in (1, 2) else r - depth
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        if i == 0:
            ctx.move_to(x, y)
        else:
            ctx.line_to(x, y)
    ctx.close_path()


def draw_gear(ctx, cx, cy, r, teeth, rot, color, alpha=1.0, glow=True):
    if glow:
        for k, a in [(10, 0.06), (5, 0.10)]:
            gear_path(ctx, cx, cy, r + k, teeth, rot)
            set_color(ctx, color, a * alpha)
            ctx.fill()
    gear_path(ctx, cx, cy, r, teeth, rot)
    set_color(ctx, color, 0.16 * alpha)
    ctx.fill_preserve()
    set_color(ctx, color, alpha)
    ctx.set_line_width(4)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    ctx.arc(cx, cy, r * 0.42, 0, 2 * math.pi)
    ctx.stroke()
    ctx.arc(cx, cy, r * 0.12, 0, 2 * math.pi)
    set_color(ctx, color, alpha)
    ctx.fill()
    for i in range(5):
        a = rot + i * 2 * math.pi / 5
        ctx.move_to(cx + r * 0.14 * math.cos(a), cy + r * 0.14 * math.sin(a))
        ctx.line_to(cx + r * 0.42 * math.cos(a), cy + r * 0.42 * math.sin(a))
    ctx.set_line_width(5)
    ctx.stroke()


# ====================================================================== quill
def draw_quill(ctx, x, y, s, angle=-0.9, alpha=1.0):
    """Feather quill with its nib at (x, y)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.scale(s, s)
    # vane
    ctx.new_path()
    ctx.move_to(40, 0)
    ctx.curve_to(120, -40, 260, -54, 380, -20)
    ctx.curve_to(300, 4, 180, 18, 60, 6)
    ctx.close_path()
    ctx.set_source_rgba(0.95, 0.92, 0.86, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.35, 0.28, 0.2, 0.7 * alpha)
    ctx.set_line_width(1.5)
    ctx.stroke()
    # barbs
    ctx.set_source_rgba(0.45, 0.38, 0.3, 0.45 * alpha)
    ctx.set_line_width(1)
    for i in range(30):
        t = i / 29
        bx = 60 + t * 310
        ctx.move_to(bx, -2 + t * -10)
        ctx.line_to(bx + 18, -28 + 18 * t * t)
        ctx.move_to(bx, 2)
        ctx.line_to(bx + 14, 12 - 8 * t)
    ctx.stroke()
    # shaft
    ctx.set_source_rgba(0.3, 0.24, 0.17, alpha)
    ctx.set_line_width(3)
    ctx.move_to(0, 0)
    ctx.curve_to(120, -6, 260, -14, 392, -22)
    ctx.stroke()
    ctx.restore()
