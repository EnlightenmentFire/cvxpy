"""Effects: beams, explosions, plumes, labels, overlays."""
import math
import numpy as np
import cv2
from common import *


def beam(emis, p0, p1, color, width=2.0, intensity=1.0, core=(1, 1, 1), flicker=0.0, seed=0):
    """laser beam: hot white core + coloured sheath, into emissive layer."""
    if intensity <= 0:
        return
    f = 1.0
    if flicker > 0:
        f = 1 + flicker * math.sin(seed * 12.9898 + intensity * 78.233)
    draw_polyline(emis, [p0, p1], np.asarray(color, np.float32) * intensity * f * 0.9, width * 3.2, add=True)
    draw_polyline(emis, [p0, p1], np.asarray(core, np.float32) * intensity * f * 1.4, max(1.0, width), add=True)


def tapered_beam(emis, p0, p1, color, w0=4.0, w1=1.0, intensity=1.0, steps=10):
    pts = [np.asarray(p0, float) + (np.asarray(p1, float) - np.asarray(p0, float)) * k / steps for k in range(steps + 1)]
    for k in range(steps):
        w = w0 + (w1 - w0) * (k + 0.5) / steps
        draw_polyline(emis, [pts[k], pts[k + 1]], np.asarray(color, np.float32) * intensity, w, add=True)


class Burst:
    """space explosion with flash, shock ring and debris (pre-seeded)."""
    def __init__(self, seed=0, n=40):
        rng = np.random.default_rng(seed)
        v = rng.normal(0, 1, (n, 2))
        self.dirs = v / np.linalg.norm(v, axis=1, keepdims=True)
        self.speed = rng.uniform(0.3, 1.0, n)
        self.size = rng.uniform(0.6, 1.6, n)

    def draw(self, emis, x, y, tau, scale=1.0, color=(1.0, 0.75, 0.45), power=1.0):
        """tau: seconds since detonation."""
        if tau < 0 or tau > 3.0 or power <= 0:
            return
        col = np.asarray(color, np.float32)
        fl = math.exp(-tau / 0.16) * power
        r = scale * (10 + 70 * (1 - math.exp(-tau / 0.12)))
        splat(emis, x, y, r * 0.45, (1.0, 1.0, 1.0), 2.6 * fl)
        splat(emis, x, y, r, col, 1.1 * fl + 0.25 * math.exp(-tau / 0.6) * power)
        rr = scale * (20 + 160 * tau ** 0.6)
        ra = 0.55 * math.exp(-tau / 0.45) * power
        if ra > 0.01:
            ring(emis, x, y, rr, col, width=max(1, int(2 * scale)), alpha=ra)
        da = math.exp(-tau / 0.9) * power
        if da > 0.02:
            segs = []
            for d, s, z in zip(self.dirs, self.speed, self.size):
                k1 = s * scale * 260 * tau ** 0.7
                k0 = s * scale * 260 * max(tau - 0.12, 0) ** 0.7
                segs.append(((x + d[0] * k0, y + d[1] * k0), (x + d[0] * k1, y + d[1] * k1), da * 0.9, max(1.0, z * scale)))
            draw_graded(emis, segs, col)
            for (p0, p1, _, wd), z in zip(segs, self.size):
                splat(emis, p1[0], p1[1], 1.2 * z * scale, (1.0, 0.9, 0.7), 0.9 * da)


def plume(emis, pts, color=(1.0, 0.62, 0.25), head=1.0, width=3.0, fade=1.0):
    """exhaust trail along screen points (oldest first); bright head."""
    n = len(pts)
    if n < 2 or fade <= 0.003:
        return
    col = np.asarray(color, np.float32)
    segs = []
    for i in range(n - 1):
        k = (i + 1) / (n - 1)
        segs.append((pts[i], pts[i + 1], (k ** 1.6) * fade * 0.7, width * (0.6 + 1.6 * k)))
    draw_graded(emis, segs, col)
    hx, hy = pts[-1]
    if head > 0:
        splat(emis, hx, hy, width * 1.1, (1.0, 0.95, 0.85), 1.8 * head * fade)
        splat(emis, hx, hy, width * 3.0, col, 0.35 * head * fade)


def hypo_overlay(canvas, alpha=1.0, label='假想'):
    """persistent marker for imagined sequences: label box top-left + viewfinder corners."""
    if alpha <= 0:
        return
    col = hexc('ffd2f4')
    x0, y0 = 56, SAFE_TOP + 10
    w_, h_ = text(canvas, label, x0 + 18, y0 + 6, kind='bold', size=40, color=col, alpha=alpha * 0.95,
                  anchor='lt', tracking=8)
    # box around label
    frame_rect(canvas, x0, y0 + 10, x0 + w_ + 24, y0 + h_ - 6, col, width=2, alpha=alpha * 0.8)
    # corner brackets
    m, L = 34, 70
    pts = [((m, SAFE_TOP - 40 + L), (m, SAFE_TOP - 40), (m + L, SAFE_TOP - 40)),
           ((W - m - L, SAFE_TOP - 40), (W - m, SAFE_TOP - 40), (W - m, SAFE_TOP - 40 + L)),
           ((m, SAFE_BOTTOM + 30 - L), (m, SAFE_BOTTOM + 30), (m + L, SAFE_BOTTOM + 30)),
           ((W - m - L, SAFE_BOTTOM + 30), (W - m, SAFE_BOTTOM + 30), (W - m, SAFE_BOTTOM + 30 - L))]
    for p in pts:
        draw_polyline(canvas, p, col, 2, alpha * 0.55)


def chapter_label(canvas, num, title, alpha=1.0, color=None):
    """small persistent chapter tag (top right)."""
    if alpha <= 0:
        return
    color = PAL['grey'] if color is None else color
    text(canvas, f'{num:02d}  {title}', W - 56, SAFE_TOP + 34, kind='medium', size=30, color=color,
         alpha=alpha * 0.85, anchor='rc', tracking=2)


def subtitle(canvas, s, alpha=1.0, y=SUB_Y, size=50, color=(0.96, 0.97, 0.98)):
    if not s or alpha <= 0:
        return
    text(canvas, s, W / 2, y, kind='bold', size=size, color=color, alpha=alpha, anchor='center',
         shadow=0.9, stroke=3, line_gap=1.4)


def caption_en(canvas, s, alpha=1.0, y=None, size=34, color=(0.75, 0.82, 0.9)):
    if not s or alpha <= 0:
        return
    y = SUB_Y + 118 if y is None else y
    text(canvas, s, W / 2, y, kind='regular', size=size, color=color, alpha=alpha, anchor='center',
         shadow=0.9, stroke=2, line_gap=1.35)


def white_flash(canvas, amt):
    if amt > 0:
        canvas += amt * 1.4


def scan_glitch(canvas, amt, seed=0):
    if amt <= 0:
        return
    rng = np.random.default_rng(seed)
    for _ in range(int(6 * amt) + 1):
        y = rng.integers(0, H - 40)
        h = rng.integers(4, 40)
        dx = int(rng.normal(0, 40 * amt))
        canvas[y:y + h] = np.roll(canvas[y:y + h], dx, axis=1)
