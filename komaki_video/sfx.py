# -*- coding: utf-8 -*-
"""Synthesized sound effects (numpy only), placed by timeline cues. Output: WORK/stems/sfx.wav (48 kHz stereo)."""
import os, json
import numpy as np, soundfile as sf

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
rng = np.random.default_rng(1)


def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    # one-pole low-pass via cumulative filter (vectorized approximation using lfilter if scipy present)
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def hp(x, a):
    return x - lp(x, a)


def env(n, att, dec):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(att, 1e-4)) * np.exp(-t / dec)


def cannon(dist=1.0):
    n = int(3.5 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    body = lp(noise, 0.995) * 30 * env(n, 0.004, 0.45 * dist)
    thump = np.sin(2 * np.pi * (48 - 20 * t) * t) * env(n, 0.002, 0.25) * 0.9
    crack = hp(noise, 0.6) * env(n, 0.001, 0.03) * 0.25 / dist
    tail = lp(noise, 0.999) * 60 * env(n, 0.3, 1.4) * 0.5
    return (body + thump + crack + tail) * 0.6 / dist


def volley(n_shots=40, spread=0.6):
    n = int((spread + 2.0) * SR)
    out = np.zeros(n)
    for _ in range(n_shots):
        a = int(rng.uniform(0, spread) * SR)
        m = int(0.6 * SR)
        x = rng.standard_normal(m)
        shot = hp(x, 0.3) * env(m, 0.0005, 0.02) * 0.5 + lp(x, 0.97) * 6 * env(m, 0.001, 0.12) * 0.4
        out[a:a + m] += shot * rng.uniform(0.4, 1.0)
    out += lp(rng.standard_normal(n), 0.998) * 40 * env(n, 0.2, 0.9) * 0.3
    return out * 0.5


def crackle(seconds, rate=6):
    n = int(seconds * SR)
    out = np.zeros(n)
    for _ in range(int(seconds * rate)):
        a = int(rng.uniform(0, seconds - 0.3) * SR)
        m = int(0.3 * SR)
        x = rng.standard_normal(m)
        out[a:a + m] += hp(x, 0.5) * env(m, 0.0005, 0.015) * rng.uniform(0.1, 0.35)
    return out


def rain(seconds):
    n = int(seconds * SR)
    x = rng.standard_normal(n)
    r = hp(lp(x, 0.6), 0.9) * 0.12
    drops = np.zeros(n)
    idx = rng.integers(0, n, int(seconds * 300))
    drops[idx] = rng.uniform(0.05, 0.25, len(idx))
    drops = hp(lp(drops, 0.3), 0.95)
    return r + drops * 0.5


def hooves(seconds, rate=7.0, gallop=True):
    n = int(seconds * SR)
    out = np.zeros(n)
    t = 0.0
    while t < seconds - 0.2:
        for k, off in enumerate((0, 0.07, 0.16) if gallop else (0,)):
            a = int((t + off) * SR); m = int(0.12 * SR)
            if a + m < n:
                tt = np.arange(m) / SR
                out[a:a + m] += (np.sin(2 * np.pi * 110 * tt) * 0.5 + lp(rng.standard_normal(m), 0.9) * 2) * env(m, 0.001, 0.025) * 0.35
        t += 1.0 / rate * 3 if gallop else 1.0 / rate
    return out


def wind(seconds):
    n = int(seconds * SR)
    x = lp(rng.standard_normal(n), 0.995) * 12
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(n) / SR / 5.0)
    return x * mod * 0.2


def flags(seconds):
    """banner cloth flapping in gusts"""
    n = int(seconds * SR)
    x = hp(lp(rng.standard_normal(n), 0.7), 0.97)
    t = np.arange(n) / SR
    flap = 0.5 + 0.5 * np.sin(2 * np.pi * (5.5 + 1.5 * np.sin(2 * np.pi * t / 3.1)) * t) ** 7
    gust = 0.4 + 0.6 * np.clip(np.sin(2 * np.pi * t / 4.3) * 0.6 + 0.6, 0, 1)
    return x * flap * gust * 0.35


def horagai(seconds=3.2, f0=233.0):
    """conch-shell trumpet: breathy buzzy tone with a scoop up and vibrato"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = f0 * (0.92 + 0.08 * np.minimum(1, t / 0.35)) * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = sum((0.9 ** k) * np.sin(k * ph) for k in range(1, 9))
    tone = lp(tone, 0.55)
    breath = hp(lp(rng.standard_normal(n), 0.6), 0.9) * 0.25
    e = np.minimum(1, t / 0.25) * np.clip((seconds - t) / 0.6, 0, 1)
    return (tone * 0.35 + breath) * e * 0.5


def taiko_boom():
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (70 - 25 * np.minimum(t, 0.3)) * t) * env(n, 0.002, 0.45)
    skin = lp(rng.standard_normal(n), 0.9) * env(n, 0.001, 0.04) * 0.8
    return (body + skin) * 0.9


def bell(seconds=7.0, f0=98.0):
    """temple bell (bonsho)-like inharmonic strike"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 4.0), (2.0, 0.5, 3.0), (2.76, 0.35, 2.2), (5.4, 0.2, 1.2), (8.9, 0.1, 0.7)]
    y = sum(a * np.sin(2 * np.pi * f0 * r * t + 0.3 * np.sin(2 * np.pi * 0.7 * t)) * np.exp(-t / d) for r, a, d in parts)
    y += lp(rng.standard_normal(n), 0.8) * env(n, 0.001, 0.05) * 0.4
    return y * 0.45


def water(seconds):
    n = int(seconds * SR)
    x = lp(hp(rng.standard_normal(n), 0.95), 0.5)
    t = np.arange(n) / SR
    return x * (0.5 + 0.3 * np.sin(2 * np.pi * t / 2.3)) * 0.25


def fire(seconds):
    n = int(seconds * SR)
    roar = lp(rng.standard_normal(n), 0.99) * 6 * 0.25
    return roar + crackle(seconds, 14) * 0.8


def place(out, x, t, gain=1.0, pan=0.0, fade=0.0):
    a = int(t * SR)
    if a >= len(out):
        return
    b = min(len(out), a + len(x))
    y = x[:b - a] * gain
    if fade > 0:
        f = min(int(fade * SR), len(y) // 2)
        y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    out[a:b, 0] += y * l * 1.41; out[a:b, 1] += y * r * 1.41


def build():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    out = np.zeros((int((total + 1) * SR), 2))
    sc = {s["id"]: s for s in tl["scenes"]}

    def cue(sid, c):
        for L in sc[sid]["lines"]:
            if L["cue"] == c:
                return L["start"], L["end"]
        raise KeyError((sid, c))

    def span(sid):
        return sc[sid]["start"], sc[sid]["end"]

    VOLLEY = 1.15   # scenes.VOLLEY_T
    # ---- sound hook: wind + banners from frame 0, a matchlock volley tears it open, taiko under it (score)
    a, b = span("s00")
    tw, _ = cue("s00", "twist")
    place(out, wind(tw + 1.0), 0.0, 1.3, fade=0.0)
    place(out, flags(tw + 1.0), 0.0, 1.0, 0.3)
    place(out, volley(26, 0.18), VOLLEY, 2.2, -0.1)
    place(out, taiko_boom(), VOLLEY + 0.02, 1.3)
    # cut to the wood at Nagakute: second volley, hooves
    place(out, volley(30, 0.4), tw + 0.45, 1.6, -0.4)
    place(out, hooves(b - tw, 8), tw + 0.2, 1.0, -0.3, fade=0.4)
    # s01: quiet wind bed under the map
    a, b = span("s01"); place(out, wind(b - a), a, 0.6, fade=2.0)
    t0, _ = cue("s01", "nagakute"); place(out, volley(20, 0.5), t0 + 1.2, 0.8, 0.2)
    # s03: standoff wind
    a, b = span("s03"); place(out, wind(b - a), a, 0.7, fade=2.0); place(out, flags(b - a), a, 0.35, 0.4, fade=2.0)
    t0, _ = cue("s03", "inuyama"); place(out, volley(15, 0.6), t0 + 3.0, 0.6, 0.3)
    t0, _ = cue("s03", "haguro"); place(out, volley(18, 0.6), t0 + 2.6, 0.6, -0.2)
    # s04: night march (soft footsteps rhythm = muted hooves) + wind
    t0, _ = cue("s04", "depart"); t1 = sc["s04"]["end"]
    place(out, hooves(t1 - t0, 3.0, gallop=False), t0, 0.35, fade=2.0); place(out, wind(t1 - t0), t0, 0.5, fade=2.0)
    # s05 Hakusanbayashi
    t0, _ = cue("s05", "iwasaki"); place(out, volley(18, 0.8), t0 + 1.0, 0.7, 0.3); place(out, fire(6), t0 + 1.5, 0.6, fade=1.0)
    t0, _ = cue("s05", "ambush")
    place(out, horagai(2.6, 220.0), t0 - 0.4, 1.0, -0.5)
    place(out, volley(40, 0.35), t0 + 0.4, 1.5, -0.3)
    place(out, hooves(7, 9), t0 + 0.6, 1.0, -0.6, fade=0.5)
    place(out, crackle(8, 9), t0 + 1.0, 0.8, 0.0, fade=1.0)
    # s06 Hori's volley; the fan appears (bell-like swell is in score) 
    t0, _ = cue("s06", "hori"); place(out, volley(35, 0.3), t0 + 5.0, 1.2, 0.2)
    t0, _ = cue("s06", "fan"); place(out, horagai(3.5, 196.0), t0 + 0.6, 0.9, 0.4); place(out, wind(8), t0, 0.5, fade=1.0)
    # s07 Nagakute battle
    t0, _ = cue("s07", "battle")
    place(out, horagai(2.5, 233.0), t0 - 0.6, 0.9)
    place(out, volley(50, 0.4), t0 + 0.2, 1.6)
    t1, _ = cue("s07", "loss")
    place(out, hooves(t1 - t0, 9), t0 + 0.3, 1.0, 0.4, fade=0.6)
    place(out, crackle(t1 - t0, 12), t0 + 0.5, 0.9, -0.2, fade=1.0)
    for k in range(4):
        place(out, volley(25, 0.5), t0 + 2.5 + k * 3.0, 0.9, rng.uniform(-0.6, 0.6))
    t0, _ = cue("s07", "mori"); place(out, volley(1, 0.0), t0 + 0.3, 1.4)
    # s09 water attack, Ise
    t0, _ = cue("s09", "takegahana"); place(out, water(9), t0 + 3.0, 0.8, fade=1.5)
    # s10 burning fields
    t0, t1 = cue("s10", "land"); place(out, fire(t1 - t0 + 1), t0, 0.7, -0.3, fade=1.0)
    # bells: Clausewitz, aftermath, ending quote
    t0, _ = cue("s11", "quote"); place(out, bell(8, 98.0), t0 - 0.3, 1.0)
    t0, _ = cue("s12", "same"); place(out, bell(8, 87.3), t0 - 0.2, 0.9)
    t0, _ = cue("s14", "quote"); place(out, bell(9, 98.0), t0 - 0.3, 1.0)
    a, b = span("s14"); place(out, wind(b - a), a, 0.5, fade=2.5)
    out = out[:int(total * SR)]
    out = 0.9 * np.tanh(out / 0.9)          # soft limiter so the volleys do not dominate loudness normalisation
    sf.write(f"{WORK}/stems/sfx.wav", out.astype(np.float32), SR, subtype="FLOAT")
    print("sfx", len(out) / SR, "peak", np.abs(out).max())


if __name__ == "__main__":
    build()
