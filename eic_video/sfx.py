# -*- coding: utf-8 -*-
"""Synthesised sound effects (numpy), placed on the picture timeline -> /tmp/claude-0/work/audio/sfx.wav (48 kHz stereo)."""
import json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

WORK = "/tmp/claude-0/work"
SR = 48000
TL = json.load(open(f"{WORK}/timeline.json"))
rng = np.random.default_rng(3)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def rain(dur, level=1.0):
    n = int(dur * SR)
    w = rng.standard_normal((2, n))
    r = np.stack([bp(w[0], 900, 9000), bp(w[1], 900, 9000)]) * 0.25
    # droplets
    for _ in range(int(dur * 60)):
        i = rng.integers(0, n - 2000)
        c = rng.integers(0, 2)
        r[c, i:i + 600] += bp(rng.standard_normal(600), 2000, 10000) * env(600, 0.0005, 0.004) * 0.6
    return r * level


def thunder(dur=5.0):
    n = int(dur * SR)
    w = rng.standard_normal(n)
    crack = bp(w, 300, 6000) * env(n, 0.002, 0.18) * 1.2
    rumble = lp(w, 180, 4) * env(n, 0.25, 1.6) * 6
    s = crack + rumble
    return np.stack([s, np.roll(s, 300)]) * 0.5


def boom(dur=2.5, dist=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 55 * np.exp(-t * 1.5) + 28
    sine = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.5)
    noise = lp(rng.standard_normal(n), 900 if dist < 1.5 else 400) * env(n, 0.002, 0.25)
    s = (sine * 0.9 + noise * 0.7) / dist
    return np.stack([s, s])


def thud(dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (90 * np.exp(-t * 8) + 50) * t) * env(n, 0.001, 0.08)
    s += lp(rng.standard_normal(n), 1500) * env(n, 0.001, 0.03) * 0.5
    return np.stack([s, s]) * 0.8


def rustle(dur=1.4):
    n = int(dur * SR)
    w = bp(rng.standard_normal(n), 1500, 7000)
    am = np.abs(lp(rng.standard_normal(n), 12)) * 6
    s = w * am * np.sin(np.linspace(0, np.pi, n)) * 0.25
    return np.stack([s, np.roll(s, 200)])


def cue_abs(group, cue):
    for g in TL["groups"]:
        if g["name"] == group and cue in g["cues"]:
            return g["start"] + g["cues"][cue]
    return None


def group_span(name):
    for g in TL["groups"]:
        if g["name"] == name:
            return g["start"], g["end"]
    return None


def main():
    total = TL["total"]
    out = np.zeros((2, int(total * SR) + SR))

    def put(sig, t, gain=1.0):
        i = int(t * SR)
        j = min(out.shape[1], i + sig.shape[1])
        out[:, i:j] += sig[:, :j - i] * gain

    # opening: rain bed + thunder crack synced with the lightning flash (0.55 s)
    s, e = group_span("battle_open")
    e += 0.5
    r = rain(e)
    fade = np.ones(r.shape[1]); fe = int(1.5 * SR); fade[-fe:] = np.linspace(1, 0, fe)
    rain_t = cue_abs("battle_open", "rain")
    lev = np.full(r.shape[1], 0.55)
    if rain_t:
        i = int(rain_t * SR); lev[i:] = np.minimum(1.0, 0.55 + (np.arange(r.shape[1] - i) / SR) * 0.3)
    put(r * fade * lev, 0.0, 0.5)
    put(thunder(6.0), 0.5, 0.9)
    if rain_t:
        put(thunder(5.0), rain_t + 0.1, 0.6)
    nt = cue_abs("battle_open", "nawab")
    if nt:
        for k, dt in enumerate((0.8, 2.6, 4.1)):
            put(boom(2.5, 2.2), nt + dt, 0.5)
    # battle map: cannonade + rain
    ct = cue_abs("battle_map", "b_cannon")
    if ct:
        for k in range(7):
            put(boom(2.2, 1.6 + 0.4 * (k % 3)), ct + 0.3 + k * 0.9 + rng.random() * 0.3, 0.45)
    rt = cue_abs("battle_map", "b_rain")
    if rt:
        at = cue_abs("battle_map", "b_advance") or rt + 15
        d = max(3.0, at - rt + 1.5)
        r = rain(d)
        f = np.ones(r.shape[1]); k1 = int(0.8 * SR); f[:k1] = np.linspace(0, 1, k1); f[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
        put(r * f, rt, 0.35)
        put(thunder(4.0), rt + 0.2, 0.5)
    cht = cue_abs("battle_map", "b_charge")
    if cht:
        put(boom(2.0, 1.0), cht + 1.8, 0.6)
    # paper / seal / stamps
    for grp, cue, dt, fn, gain in [("charter", "charter", 0.0, rustle, 0.5), ("charter", "seal", 0.05, thud, 0.8),
                                   ("conspiracy", "pact", 1.6, thud, 0.7), ("conspiracy", "pact2", 0.3, thud, 0.6),
                                   ("battle_map", "b_deal", 0.8, thud, 0.8), ("crisis", "regulating", 2.2, thud, 0.6),
                                   ("buxar", "buxar", 4.0, thud, 0.6), ("powers", "powers", 1.0, thud, 0.4),
                                   ("powers", "powers", 2.3, thud, 0.4), ("powers", "powers", 3.6, thud, 0.4),
                                   ("powers", "powers", 4.9, thud, 0.4)]:
        t = cue_abs(grp, cue)
        if t is not None:
            put(fn(), t + dt, gain)
    pk = np.abs(out).max()
    out = out / max(pk, 1e-6) * 0.7
    sf.write(f"{WORK}/audio/sfx.wav", out.T.astype(np.float32), SR)
    print("sfx written", out.shape[1] / SR)


if __name__ == "__main__":
    main()
