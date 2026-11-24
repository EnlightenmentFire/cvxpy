# -*- coding: utf-8 -*-
"""Reusable silhouette shapes (normalized coordinates) -> skia paths."""
import math
import skia
from engine import path_from

def xf(points, cx, cy, s, flip=False, sy=None):
    sy = s if sy is None else sy
    return [((-x if flip else x) * s + cx, y * sy + cy) for x, y in points]

# ---- Roman profile bust, facing right, box ~[-0.8,0.8]x[-1,0.8]
PROFILE = [(-0.05, -0.95), (0.20, -0.92), (0.38, -0.80), (0.47, -0.62), (0.50, -0.50),
           (0.47, -0.43), (0.53, -0.36), (0.62, -0.26), (0.53, -0.23), (0.555, -0.18),
           (0.52, -0.145), (0.545, -0.10), (0.49, -0.045), (0.51, 0.03), (0.42, 0.10),
           (0.27, 0.14), (0.23, 0.30), (0.32, 0.45), (0.60, 0.60), (0.70, 0.80),
           (-0.62, 0.80), (-0.52, 0.56), (-0.30, 0.42), (-0.26, 0.22), (-0.40, 0.06),
           (-0.56, -0.18), (-0.57, -0.52), (-0.42, -0.80), (-0.22, -0.93)]
BEARD = [(0.47, -0.13), (0.52, 0.04), (0.44, 0.17), (0.28, 0.22), (0.10, 0.16),
         (-0.02, 0.0), (0.05, -0.12), (0.20, -0.20), (0.35, -0.20)]

def profile_path(cx, cy, s, flip=False):
    return path_from(xf(PROFILE, cx, cy, s, flip), closed=True, smooth=True)

def beard_path(cx, cy, s, flip=False):
    return path_from(xf(BEARD, cx, cy, s, flip), closed=True, smooth=True)

def laurel(c, cx, cy, s, paint_leaf, flip=False):
    """laurel wreath leaves along an arc around the head"""
    sign = -1 if flip else 1
    for i in range(11):
        a = math.radians(200 + i * 14)  # from back-bottom to front-top
        r = 0.62
        x = cx + sign * (math.cos(a) * r * s * 0.95 - 0.02 * s)
        y = cy + math.sin(a) * r * s * 0.95 - 0.30 * s
        c.save()
        c.translate(x, y)
        c.rotate(sign * (math.degrees(a) + 90) + (30 if i % 2 else -30))
        rr = skia.Rect.MakeXYWH(-0.05 * s, -0.11 * s, 0.10 * s, 0.22 * s)
        c.drawOval(rr, paint_leaf)
        c.restore()

# ---- horse, facing right, box ~[-0.8,0.9]x[-0.8,0.86]
HORSE = [(0.88, -0.37), (0.86, -0.30), (0.78, -0.28), (0.64, -0.33), (0.56, -0.38),
         (0.52, -0.22), (0.49, -0.08), (0.48, 0.06), (0.46, 0.20), (0.45, 0.44), (0.445, 0.70),
         (0.465, 0.86), (0.395, 0.86), (0.395, 0.70), (0.39, 0.46), (0.37, 0.30),
         (0.345, 0.46), (0.335, 0.70), (0.345, 0.86), (0.275, 0.86), (0.28, 0.70), (0.28, 0.46),
         (0.24, 0.28), (0.05, 0.31), (-0.22, 0.28), (-0.30, 0.34), (-0.29, 0.52),
         (-0.31, 0.70), (-0.30, 0.86), (-0.37, 0.86), (-0.375, 0.70), (-0.38, 0.55),
         (-0.40, 0.48), (-0.43, 0.58), (-0.445, 0.72), (-0.435, 0.86), (-0.505, 0.86),
         (-0.515, 0.72), (-0.525, 0.53), (-0.57, 0.40), (-0.62, 0.18), (-0.62, -0.02),
         (-0.57, -0.13), (-0.42, -0.18), (-0.18, -0.14), (0.08, -0.15), (0.28, -0.23),
         (0.40, -0.40), (0.50, -0.58), (0.565, -0.68), (0.56, -0.79), (0.61, -0.70),
         (0.66, -0.66), (0.74, -0.56), (0.82, -0.46)]
HORSE_TAIL = [(-0.58, -0.12), (-0.68, -0.05), (-0.74, 0.12), (-0.76, 0.32), (-0.72, 0.52),
              (-0.66, 0.40), (-0.65, 0.20), (-0.62, 0.02)]
HORSE_MANE = [(0.29, -0.23), (0.37, -0.40), (0.47, -0.58), (0.555, -0.68), (0.52, -0.56),
              (0.43, -0.38), (0.33, -0.22)]

def horse_paths(cx, cy, s, flip=False):
    body = path_from(xf(HORSE, cx, cy, s, flip), closed=True, smooth=True)
    tail = path_from(xf(HORSE_TAIL, cx, cy, s, flip), closed=True, smooth=True)
    mane = path_from(xf(HORSE_MANE, cx, cy, s, flip), closed=True, smooth=True)
    return body, tail, mane

# ---- bull facing left (own drawing), box ~[-0.9,0.9]x[-0.7,0.8]
BULL = [(-0.86, -0.14), (-0.88, -0.02), (-0.80, 0.06), (-0.66, 0.06), (-0.56, 0.16),
        (-0.50, 0.30), (-0.48, 0.55), (-0.47, 0.78), (-0.40, 0.78), (-0.40, 0.55),
        (-0.36, 0.38), (-0.30, 0.55), (-0.29, 0.78), (-0.22, 0.78), (-0.22, 0.55),
        (-0.18, 0.36), (0.10, 0.38), (0.36, 0.34), (0.40, 0.55), (0.40, 0.78),
        (0.47, 0.78), (0.48, 0.55), (0.52, 0.40), (0.56, 0.56), (0.57, 0.78),
        (0.64, 0.78), (0.64, 0.55), (0.66, 0.30), (0.70, 0.05), (0.72, -0.12),
        (0.66, -0.22), (0.40, -0.26), (0.10, -0.30), (-0.20, -0.42), (-0.40, -0.40),
        (-0.55, -0.28), (-0.62, -0.30), (-0.74, -0.26)]
BULL_TAIL = [(0.72, -0.10), (0.82, 0.05), (0.86, 0.30), (0.84, 0.50)]
BULL_HORN = [(-0.66, -0.30), (-0.70, -0.46), (-0.62, -0.58), (-0.52, -0.60)]
BULL_HORN2 = [(-0.58, -0.32), (-0.56, -0.46), (-0.46, -0.52), (-0.38, -0.50)]

def bull_paths(cx, cy, s):
    body = path_from(xf(BULL, cx, cy, s), closed=True, smooth=True)
    tail = path_from(xf(BULL_TAIL, cx, cy, s), smooth=True)
    h1 = path_from(xf(BULL_HORN, cx, cy, s), smooth=True)
    h2 = path_from(xf(BULL_HORN2, cx, cy, s), smooth=True)
    return body, tail, h1, h2

# minimalist bull: a few lines (own design)
def bull_lines(cx, cy, s):
    P = lambda pts: path_from(xf(pts, cx, cy, s), smooth=True)
    return [
        P([(-0.80, -0.10), (-0.56, -0.30), (-0.20, -0.40), (0.30, -0.26), (0.70, -0.12)]),  # back
        P([(-0.80, -0.10), (-0.64, 0.06), (-0.50, 0.30), (-0.10, 0.36), (0.40, 0.34), (0.68, 0.10)]),  # belly
        P([(-0.62, -0.28), (-0.68, -0.48), (-0.52, -0.60)]),  # horn
        P([(-0.46, 0.30), (-0.46, 0.78)]),
        P([(-0.26, 0.34), (-0.26, 0.78)]),
        P([(0.44, 0.34), (0.44, 0.78)]),
        P([(0.62, 0.20), (0.62, 0.78)]),
        P([(0.70, -0.12), (0.84, 0.10), (0.84, 0.46)]),  # tail
    ]

# ---- standing lecturer, facing left, with beard (generic silhouette)
def lecturer_path(cx, cy, s):
    head = profile_path(cx, cy - 0.95 * s, s * 0.42, flip=True)
    pa = skia.Path(head)
    torso = path_from(xf([(-0.36, -0.62), (0.30, -0.66), (0.42, -0.40), (0.48, 0.40),
                          (-0.46, 0.40), (-0.44, -0.30), (-0.52, -0.10), (-0.70, -0.18),
                          (-0.66, -0.30), (-0.48, -0.46)], cx, cy, s), closed=True, smooth=True)
    pa.addPath(torso)
    beard = beard_path(cx, cy - 0.95 * s, s * 0.42, flip=True)
    pa.addPath(beard)
    return pa

def drop_path(cx, cy, r):
    pa = skia.Path()
    pa.moveTo(cx, cy - r * 1.6)
    pa.cubicTo(cx + r * 0.3, cy - r * 0.9, cx + r, cy - r * 0.4, cx + r, cy + r * 0.15)
    pa.cubicTo(cx + r, cy + r * 0.75, cx + r * 0.5, cy + r, cx, cy + r)
    pa.cubicTo(cx - r * 0.5, cy + r, cx - r, cy + r * 0.75, cx - r, cy + r * 0.15)
    pa.cubicTo(cx - r, cy - r * 0.4, cx - r * 0.3, cy - r * 0.9, cx, cy - r * 1.6)
    pa.close()
    return pa

def gothic_arch(x, y, w, h, pointed=0.62):
    """Pointed arch window outline: rect from (x,y) top-left; arch occupies top."""
    pa = skia.Path()
    r = w * pointed
    spring = y + h * 0.0 + w * 0.55
    pa.moveTo(x, y + h)
    pa.lineTo(x, spring)
    # left arc to apex
    pa.quadTo(x, y, x + w / 2, y - w * 0.05)
    pa.quadTo(x + w, y, x + w, spring)
    pa.lineTo(x + w, y + h)
    pa.close()
    return pa

def ogee_arch(x, y, w, h):
    pa = skia.Path()
    spring = y + w * 0.6
    pa.moveTo(x, y + h)
    pa.lineTo(x, spring)
    pa.cubicTo(x, y + w * 0.15, x + w * 0.42, y + w * 0.25, x + w / 2, y - w * 0.12)
    pa.cubicTo(x + w * 0.58, y + w * 0.25, x + w, y + w * 0.15, x + w, spring)
    pa.lineTo(x + w, y + h)
    pa.close()
    return pa

def star8(cx, cy, r, inner=0.42):
    pts = []
    for i in range(16):
        a = math.pi / 8 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return path_from(pts, closed=True)
