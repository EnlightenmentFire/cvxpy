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

    def scene_span(sid):
        return sc[sid]["start"], sc[sid]["end"]

    # opening sound hook: drum hit is in the score; add a cannon boom under it, then distant guns & drums
    place(out, cannon(0.8), 0.0, 1.0)
    a, b = scene_span("s00")
    place(out, crackle(b - a, 3), a, 0.5, -0.3, fade=1.0)
    for k in range(4):
        place(out, cannon(2.0), a + 4 + k * 6.5, 0.6, rng.uniform(-0.6, 0.6))
    t0, _ = cue("s00", "recule"); place(out, cannon(1.0), t0 - 0.3, 0.8)
    # rain
    t0, _ = cue("s03", "rain"); place(out, rain(sc["s03"]["end"] - t0), t0, 0.5, fade=1.5)
    a, b = scene_span("s04"); place(out, rain(b - a), a, 0.7, fade=1.5)
    # Hougoumont
    t0, _ = cue("s05", "hougo"); place(out, crackle(14, 8), t0, 0.8, -0.4, fade=1.0)
    for k in range(3):
        place(out, cannon(1.8), t0 + 1 + k * 4, 0.6, -0.5)
    # courier hooves
    t0, _ = cue("s07", "ride"); t1, _ = cue("s07", "noon"); place(out, hooves(t1 - t0), t0, 0.9, fade=0.8)
    place(out, rain(t1 - t0), t0, 0.35, fade=1.0)
    # grand battery
    t0, _ = cue("s09", "battery")
    for k in range(8):
        place(out, cannon(1.2), t0 + k * 0.9 + rng.uniform(0, 0.3), 0.8, rng.uniform(-0.7, 0.7))
    t0, _ = cue("s09", "stand"); place(out, volley(60, 0.7), t0 + 0.6, 1.0)
    t0, _ = cue("s09", "cav"); place(out, hooves(6, 9), t0, 0.8, 0.2, fade=0.6)
    # cavalry charges
    t0, _ = cue("s10", "charge"); t1, _ = cue("s10", "why"); place(out, hooves(t1 - t0, 9), t0, 1.0, fade=1.0)
    place(out, crackle(t1 - t0, 10), t0, 0.6, 0.3, fade=1.0)
    # Plancenoit
    t0, _ = cue("s11", "bulow")
    for k in range(4):
        place(out, cannon(1.5), t0 + 0.5 + k * 2.2, 0.7, 0.6)
    t0, _ = cue("s11", "street"); place(out, crackle(8, 12), t0, 0.8, 0.5, fade=0.8)
    t0, _ = cue("s12", "lhs"); place(out, cannon(1.0), t0 + 0.4, 0.7); place(out, crackle(6, 10), t0, 0.6, fade=0.6)
    # Guard
    t0, _ = cue("s13", "volley"); place(out, volley(70, 0.5), t0 + 1.2, 1.1, 0.3)
    t0, _ = cue("s13", "flank"); place(out, volley(50, 0.8), t0 + 1.0, 0.9, 0.8)
    t0, _ = cue("s15", "hat"); place(out, crackle(10, 10), t0 + 1, 0.6, fade=1.0)
    for k in range(3):
        place(out, cannon(1.6), t0 + 2 + k * 3, 0.6, rng.uniform(-0.6, 0.6))
    a, b = scene_span("s18"); place(out, wind(b - a), a, 0.6, fade=2.0)
    out = out[:int(total * SR)]
    sf.write(f"{WORK}/stems/sfx.wav", out.astype(np.float32), SR, subtype="FLOAT")
    print("sfx", len(out) / SR, "peak", np.abs(out).max())


if __name__ == "__main__":
    build()
