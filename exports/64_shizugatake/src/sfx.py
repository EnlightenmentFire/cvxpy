# -*- coding: utf-8 -*-
"""Procedural sound effects (numpy). All mono float32 at 48 kHz."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def env(n, a, d, sus=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4))
    return (e * (1 - sus) + sus * (t < n / SR)).astype(np.float32)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x).astype(np.float32)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x).astype(np.float32)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x).astype(np.float32)


def noise(n):
    return rng.standard_normal(n).astype(np.float32)


def norm(x, peak=0.9):
    m = np.abs(x).max() + 1e-9
    return (x / m * peak).astype(np.float32)


def taiko(big=1.0):
    n = int(SR * 2.2)
    t = np.arange(n) / SR
    f = 58 * big ** -0.2 * (1 + 0.6 * np.exp(-t * 18))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 2.6) + 0.4 * np.sin(ph * 1.52) * np.exp(-t * 6)
    hit = bp(noise(n), 150, 2500) * np.exp(-t * 40) * 0.6
    skin = lp(noise(n), 400) * np.exp(-t * 9) * 0.5
    return norm(body + hit + skin, 0.95)


def horn(dur=2.4, f0=185.0):
    """法螺 (conch): breathy, slightly unstable low horn with formants"""
    n = int(SR * dur); t = np.arange(n) / SR
    vib = 1 + 0.012 * np.sin(2 * np.pi * 5.2 * t) + 0.02 * np.minimum(1, t / 0.3) - 0.02
    bend = 1 - 0.06 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f0 * vib * bend) / SR
    x = sum(np.sin(ph * k) / k ** 0.9 for k in range(1, 14))
    x = bp(x, 160, 1800) + 0.8 * bp(x, 500, 900, 2)
    br = bp(noise(n), 300, 2200) * 0.18
    e = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.5)
    return norm((x + br) * e, 0.8)


def whoosh(dur=0.9):
    n = int(SR * dur); t = np.arange(n) / SR
    e = np.sin(np.pi * np.minimum(1, t / dur)) ** 2
    x = noise(n)
    # sweeping band
    out = np.zeros(n, np.float32)
    seg = 2400
    for i in range(0, n, seg):
        fc = 300 + 2500 * (i / n)
        out[i:i + seg] = bp(x[i:i + seg], fc * 0.6, fc * 1.6)[:len(out[i:i + seg])]
    crack = np.zeros(n, np.float32)
    for k in rng.integers(0, n - 500, 40):
        crack[k:k + 300] += hp(noise(300), 2500) * np.exp(-np.arange(300) / 40) * 0.6
    return norm((out * e + crack * e), 0.7)


def crackle(dur, density=30):
    n = int(SR * dur)
    x = lp(noise(n), 900) * 0.15
    for k in rng.integers(0, n - 800, int(density * dur)):
        L = rng.integers(100, 600)
        x[k:k + L] += hp(noise(L), 2000) * np.exp(-np.arange(L) / (L / 5)) * rng.uniform(0.3, 1.0)
    return norm(x, 0.6)


def hooves(dur, rate=2.6, n_horses=6):
    n = int(SR * dur); x = np.zeros(n, np.float32)
    thump = lambda: (lp(noise(2400), 300) * np.exp(-np.arange(2400) / 300) + bp(noise(2400), 800, 3000) * np.exp(-np.arange(2400) / 80) * 0.4)
    for h in range(n_horses):
        off = rng.uniform(0, 1 / rate); r = rate * rng.uniform(0.93, 1.07)
        t = off
        while t < dur - 0.1:
            for j, dt in enumerate((0, 0.07, 0.15)):
                k = int((t + dt) * SR)
                if k + 2400 < n:
                    x[k:k + 2400] += thump() * rng.uniform(0.5, 1.0) * (0.6 + 0.4 * (h == 0))
            t += 1 / r
    return norm(x, 0.8)


def gunshot():
    n = int(SR * 1.4); t = np.arange(n) / SR
    crack = hp(noise(n), 1200) * np.exp(-t * 70)
    boom = lp(noise(n), 250) * np.exp(-t * 6) * 1.2
    tail = bp(noise(n), 200, 1200) * np.exp(-t * 3) * 0.3
    return norm(crack + boom + tail, 0.9)


def volley(dur, shots=14, seed=0):
    r = np.random.default_rng(seed)
    n = int(SR * dur); x = np.zeros(n, np.float32)
    g = gunshot()
    for _ in range(shots):
        k = int(r.uniform(0, dur - 1.4) * SR)
        x[k:k + len(g)] += g * r.uniform(0.25, 1.0)
    return norm(x, 0.85)


def wind(dur):
    n = int(SR * dur); t = np.arange(n) / SR
    x = noise(n)
    m = 0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t) * np.sin(2 * np.pi * 0.037 * t + 1)
    return norm(bp(x, 150, 900) * m + 0.3 * bp(x, 900, 2500) * m ** 2, 0.5)


def crowd(dur, seed=1):
    """distant battle shouting: formant-filtered noise bursts"""
    r = np.random.default_rng(seed)
    n = int(SR * dur); x = np.zeros(n, np.float32)
    for _ in range(int(dur * 12)):
        L = int(r.uniform(0.3, 1.0) * SR); k = int(r.uniform(0, max(1, n - L)))
        f = r.uniform(300, 700)
        b = bp(noise(L), f, f * 2.2) * np.sin(np.pi * np.arange(L) / L) ** 2
        x[k:k + L] += b * r.uniform(0.3, 1)
    return norm(lp(x, 2500), 0.6)


def boom():
    n = int(SR * 3); t = np.arange(n) / SR
    x = lp(noise(n), 120) * np.exp(-t * 1.4) + np.sin(2 * np.pi * 42 * t) * np.exp(-t * 2)
    return norm(x, 0.95)


def rainsnd(dur):
    n = int(SR * dur)
    return norm(bp(noise(n), 800, 6000) * 0.6 + lp(noise(n), 400) * 0.2, 0.5)


def brush_hit():
    """soft impact for title cards"""
    n = int(SR * 1.5); t = np.arange(n) / SR
    return norm(lp(noise(n), 500) * np.exp(-t * 5) + 0.5 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 4), 0.8)
