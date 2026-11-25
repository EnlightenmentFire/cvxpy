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


def flood(seconds):
    """river torrent pouring into the basin: broadband roar + low surge"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    roar = lp(x, 0.80) * 0.5 + hp(lp(x, 0.5), 0.97) * 0.25
    surge = lp(rng.standard_normal(n), 0.9995) * 60
    mod = 0.75 + 0.25 * np.sin(2 * np.pi * t / 3.1) + 0.1 * lp(rng.standard_normal(n), 0.9999) * 40
    rumble = np.sin(2 * np.pi * (38 + 4 * np.sin(2 * np.pi * t / 7)) * t) * 0.35
    return (roar * mod + surge * 0.4 + rumble) * 0.6


def thunder(dist=1.0):
    n = int(6.0 * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    crack = hp(x, 0.4) * env(n, 0.002, 0.08) * 0.6 / dist
    body = lp(x, 0.995) * 40 * env(n, 0.05, 1.2)
    roll = lp(rng.standard_normal(n), 0.998) * 60 * env(n, 0.4, 2.2) * (0.6 + 0.4 * np.sin(2 * np.pi * t * 1.3) ** 2)
    return (crack + body * 0.5 + roll * 0.5) * 0.7 / dist


def clink(k=3):
    """copper coins dropping into a pile"""
    n = int(1.2 * SR)
    out = np.zeros(n)
    tt = 0.0
    for i in range(k):
        a = int(tt * SR); m = int(0.5 * SR)
        t = np.arange(m) / SR
        f0 = rng.uniform(2100, 3200)
        y = sum(np.sin(2 * np.pi * f0 * r * t) / (j + 1) for j, r in enumerate((1, 1.47, 2.09, 2.76)))
        y *= env(m, 0.0005, 0.09 + rng.uniform(0, 0.05)) * 0.25
        if a + m <= n:
            out[a:a + m] += y
        tt += rng.uniform(0.07, 0.16)
    return out


def lap(seconds):
    """gentle water lapping"""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = lp(rng.standard_normal(n), 0.97) * 4
    mod = np.clip(np.sin(2 * np.pi * t / 2.3) * np.sin(2 * np.pi * t / 0.9 + 1), 0, 1) ** 2
    return x * (0.15 + 0.85 * mod) * 0.25


def murmur(seconds):
    n = int(seconds * SR)
    x = lp(rng.standard_normal(n), 0.985) * 5
    t = np.arange(n) / SR
    m = 0.7 + 0.3 * np.sin(2 * np.pi * t / 1.7) * np.sin(2 * np.pi * t / 0.43)
    thuds = np.zeros(n)
    for _ in range(int(seconds * 3)):
        a = rng.integers(0, max(1, n - SR // 4)); mm = SR // 4
        thuds[a:a + mm] += lp(rng.standard_normal(mm), 0.95) * 8 * env(mm, 0.002, 0.04)
    return (x * m * 0.4 + thuds * 0.25) * 0.5


def fire(seconds):
    n = int(seconds * SR)
    return lp(rng.standard_normal(n), 0.99) * 20 * 0.25 + crackle(seconds, 14) * 0.8


def wind(seconds):
    n = int(seconds * SR)
    x = lp(rng.standard_normal(n), 0.995) * 12
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(n) / SR / 5.0)
    return x * mod * 0.2


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

    # ---- opening sound hook: downpour + river torrent from frame 0; thunder with the lightning; taiko is in the score
    a, b = span("s00")
    place(out, rain(b - a + 2), a, 1.0, fade=0.05)
    fl = flood(b - a + 1.5); fl[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    place(out, fl, a, 0.9)
    for ts, d in ((1.3, 1.0), (6.6, 1.3), (12.4, 1.6)):
        place(out, thunder(d), a + ts + 0.15, 0.9, rng.uniform(-0.5, 0.5))
    # hookmap: coins, rain, flood
    t0, _ = cue("s01", "coin")
    for k in range(4):
        place(out, clink(3), t0 + 0.8 + k * 0.9, 0.7, rng.uniform(-0.4, 0.4))
    t0, _ = cue("s01", "rain"); t1, _ = cue("s01", "flags")
    place(out, rain(t1 - t0 + 1), t0, 0.7, fade=1.0); place(out, flood(t1 - t0), t0 + 0.5, 0.5, fade=1.0)
    # assault: musket crackle
    t0, _ = cue("s04", "paths"); t1, _ = cue("s04", "other")
    place(out, crackle(t1 - t0, 5), t0, 0.7, 0.2, fade=0.6)
    # build: work murmur + coins
    t0, _ = cue("s05", "pay"); t1, _ = cue("s05", "money")
    place(out, murmur(t1 - t0), t0, 0.7, fade=1.5)
    for k in range(int((t1 - t0) / 2.5)):
        place(out, clink(rng.integers(2, 5)), t0 + 0.5 + k * 2.5, 0.55, rng.uniform(-0.5, 0.5))
    # lake: rain + three surges + thunder
    a, b = span("s06")
    place(out, rain(b - a), a, 0.8, fade=1.0)
    for c in ("lv1", "lv2", "lv3"):
        t0, _ = cue("s06", c); place(out, flood(4.0), t0, 0.55, fade=1.2)
    for ts in (2.0, 13.0, 24.0):
        place(out, thunder(1.4), a + ts + 0.4, 0.8, rng.uniform(-0.5, 0.5))
    t0, _ = cue("s06", "lv3"); place(out, lap(8), t0 + 1.5, 0.5, fade=1.0)
    # relief: distant drums are in the score; rain light
    # standoff: storm
    a, b = span("s10")
    place(out, rain(b - a), a, 0.9, fade=1.0)
    for ts in [1.5, 7.0, 12.8, 19.5, 27.0, 36.0, 44.0]:
        if a + ts < b:
            place(out, thunder(rng.uniform(0.9, 1.6)), a + ts + rng.uniform(0.2, 0.9), 0.95, rng.uniform(-0.6, 0.6))
    # talk: Honnoji fire
    t0, t1 = cue("s12", "honno"); place(out, fire(t1 - t0 + 4), t0, 0.6, fade=1.0)
    # boat: calm water, oar splashes
    a, b = span("s13")
    place(out, lap(b - a), a, 0.7, fade=2.0)
    # ending: wind over drained fields
    a, b = span("s15"); place(out, wind(b - a), a, 0.5, fade=2.0)
    out = out[:int(total * SR)]
    sf.write(f"{WORK}/stems/sfx.wav", out.astype(np.float32), SR, subtype="FLOAT")
    print("sfx", len(out) / SR, "peak", np.abs(out).max())


if __name__ == "__main__":
    build()
