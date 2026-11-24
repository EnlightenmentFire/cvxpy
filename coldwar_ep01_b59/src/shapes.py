"""Vector silhouettes (generic, schematic — not exact ship plans)."""
import math

import numpy as np


def _xf(pts, cx, cy, scale, angle_deg=0.0, flip_y=True):
    p = np.asarray(pts, np.float64)
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    x = p[:, 0] * scale
    y = (-p[:, 1] if flip_y else p[:, 1]) * scale
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


def superellipse(n=160, a=0.5, b=0.05, p=5.0):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    ct, st = np.cos(t), np.sin(t)
    x = a * np.sign(ct) * np.abs(ct) ** (2 / p)
    y = b * np.sign(st) * np.abs(st) ** (2 / p)
    return np.stack([x, y], 1)


# --------------------------------------------------------------------------
# side profiles (x: -0.5..0.5 along length, y up; bow at +x)
# --------------------------------------------------------------------------

def sub_side():
    """Foxtrot-like diesel submarine side profile, length 1. Returns (hull, sail)."""
    xs = np.linspace(-0.5, 0.5, 200)
    u = (xs + 0.5)  # 0 stern .. 1 bow
    top = 0.046 * np.clip(1 - np.abs(2 * u - 1) ** 7, 0, 1) ** 0.5
    bow = np.clip((u - 0.9) / 0.1, 0, 1)
    stern = np.clip((0.12 - u) / 0.12, 0, 1)
    top = top * (1 - 0.35 * stern ** 2)
    bot = -0.044 * np.clip(1 - np.abs(2 * u - 1) ** 6, 0, 1) ** 0.5 * (1 - 0.25 * bow)
    deck = top + 0.006 * ((u > 0.08) & (u < 0.93))
    hull = np.concatenate([np.stack([xs, deck], 1), np.stack([xs[::-1], bot[::-1]], 1)])
    sail = np.array([[-0.10, 0.045], [-0.085, 0.128], [0.035, 0.132], [0.06, 0.118], [0.075, 0.045]])
    fins = np.array([[-0.5, 0.0], [-0.47, 0.03], [-0.44, 0.0], [-0.47, -0.03]])
    return hull, sail, fins


def destroyer_side():
    """Generic WWII-era destroyer, length 1, waterline at y=0."""
    hull = np.array([[-0.5, 0.0], [-0.5, 0.035], [-0.2, 0.04], [0.3, 0.045], [0.5, 0.07], [0.46, 0.0]])
    sup = np.array([[0.08, 0.04], [0.08, 0.1], [0.16, 0.12], [0.24, 0.12], [0.26, 0.04]])
    stack1 = np.array([[-0.02, 0.04], [-0.01, 0.14], [0.04, 0.14], [0.05, 0.04]])
    stack2 = np.array([[-0.16, 0.04], [-0.15, 0.12], [-0.11, 0.12], [-0.10, 0.04]])
    aft = np.array([[-0.38, 0.035], [-0.37, 0.075], [-0.28, 0.075], [-0.27, 0.035]])
    mast = np.array([[0.135, 0.12], [0.14, 0.26], [0.15, 0.26], [0.155, 0.12]])
    return [hull, sup, stack1, stack2, aft, mast]


def carrier_side():
    """Generic WWII-era fleet carrier, length 1."""
    hull = np.array([[-0.5, 0.0], [-0.52, 0.06], [-0.5, 0.085], [0.5, 0.085], [0.53, 0.06], [0.47, 0.0]])
    island = np.array([[0.06, 0.085], [0.06, 0.15], [0.09, 0.175], [0.16, 0.175], [0.17, 0.085]])
    mast = np.array([[0.11, 0.17], [0.115, 0.25], [0.125, 0.25], [0.13, 0.17]])
    return [hull, island, mast]


# --------------------------------------------------------------------------
# top views (x along length, bow at +x)
# --------------------------------------------------------------------------

def sub_top():
    hull = superellipse(180, 0.5, 0.042, 4.2)
    # taper the stern
    hull[:, 1] *= np.where(hull[:, 0] < -0.3, 1 - (-0.3 - hull[:, 0]) * 1.6, 1.0)
    sail = superellipse(80, 0.075, 0.018, 3.0) + np.array([0.0, 0.0])
    return hull, sail


def destroyer_top():
    xs = np.linspace(-0.5, 0.5, 120)
    half = 0.052 * np.where(xs < 0.25, 1.0 - 0.15 * ((xs + 0.5) / 0.75 - 0.6) ** 2, np.clip((0.5 - xs) / 0.25, 0, 1) ** 0.75)
    half = np.maximum(half, 0.0005)
    half[0] *= 0.85
    hull = np.concatenate([np.stack([xs, half], 1), np.stack([xs[::-1], -half[::-1]], 1)])
    sup = superellipse(60, 0.12, 0.028, 4) + np.array([0.12, 0])
    stacks = [superellipse(30, 0.03, 0.02, 2) + np.array([x, 0]) for x in (-0.02, -0.14)]
    return hull, [sup] + stacks


def plane_top():
    """Twin-engine carrier ASW plane, generic. Nose at +x, length 1 (wingspan ~1.3)."""
    fus = superellipse(80, 0.5, 0.055, 2.6)
    wing = np.array([[0.12, 0.65], [0.2, 0.65], [0.24, 0.05], [0.24, -0.05], [0.2, -0.65], [0.12, -0.65], [0.05, -0.05], [0.05, 0.05]])
    tail = np.array([[-0.42, 0.24], [-0.36, 0.24], [-0.32, 0.03], [-0.32, -0.03], [-0.36, -0.24], [-0.42, -0.24]])
    eng = [superellipse(30, 0.13, 0.04, 2.2) + np.array([0.24, y]) for y in (0.22, -0.22)]
    return [fus, wing, tail] + eng


def place(poly, cx, cy, scale, angle=0.0, flip_y=True):
    return _xf(poly, cx, cy, scale, angle, flip_y)
