# -*- coding: utf-8 -*-
"""Top-down dark water with ripple rings, moon reflection; 'ruminate' (rings breed rings) or 'settle'."""
import functools
import numpy as np, cv2
from engine import W, H, rgb, clamp, ease

QW, QH = W // 3, H // 3


@functools.lru_cache(maxsize=2)
def grid():
    yy, xx = np.mgrid[0:QH, 0:QW].astype(np.float32)
    return xx * 3, yy * 3


def height(t, rings):
    xx, yy = grid()
    h = np.zeros((QH, QW), np.float32)
    for (cx, cy, t0, amp, speed, lam, life) in rings:
        a = t - t0
        if a <= 0 or a > life * 3:
            continue
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        front = speed * a
        wpk = 60 + 20 * a
        env = np.exp(-((r - front) / wpk) ** 2) * np.exp(-a / life) * np.clip(a / 0.3, 0, 1)
        h += amp * env * np.cos(2 * np.pi * (r - front) / lam) / (1 + r / 500)
    return h


class Water:
    def __init__(self, dur, mode="ruminate", seed=3, center=(540, 780), moon=(560, 560), still_from=None):
        self.dur, self.mode, self.center, self.moon = dur, mode, center, moon
        rng = np.random.default_rng(seed)
        rings = []
        cx, cy = center
        if mode == "ruminate":
            t0, gap, amp = 0.4, 2.6, 1.0
            while t0 < dur:
                rings.append((cx + rng.normal(0, 30), cy + rng.normal(0, 30), t0, amp, 120 + 10 * amp, 70, 5.0))
                t0 += gap; gap = max(0.7, gap * 0.8); amp = min(2.6, amp * 1.15)
        else:   # settle: one stone, a few echoes that die away
            rings.append((cx, cy, 0.3, 2.0, 140, 70, 3.0))
            rings.append((cx + 40, cy - 20, 1.8, 1.0, 130, 60, 2.2))
            rings.append((cx - 30, cy + 30, 3.4, 0.5, 120, 60, 1.8))
        self.rings = rings

    def render(self, t):
        h = height(t, self.rings)
        gy, gx = np.gradient(h)
        nx, ny = -gx * 2.2, -gy * 2.2
        xx, yy = grid()
        # base water colour: deep blue-black gradient
        base = np.empty((QH, QW, 3), np.float32)
        f = (yy / H)[..., None]
        base[:] = rgb((8, 14, 22)) * (1 - f) + rgb((14, 24, 34)) * f
        # moon reflection sampled with normal offset
        mx, my = self.moon
        sx, sy = xx + nx * 90, yy + ny * 90
        d = ((sx - mx) / 140) ** 2 + ((sy - my) / 220) ** 2
        moon = np.exp(-d * 1.6)[..., None] * rgb((210, 220, 230)) * 0.85
        glow = np.exp(-(((sx - mx) / 420) ** 2 + ((sy - my) / 600) ** 2))[..., None] * rgb((60, 80, 100)) * 0.35
        spec = np.clip(nx * 0.6 - ny * 0.8, 0, None)[..., None] * rgb((150, 175, 200)) * 0.9
        img = base + moon + glow + spec
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
        return np.clip(img, 0, 1).astype(np.float32)
