# -*- coding: utf-8 -*-
"""Original procedural score: guqin-like plucks (Karplus-Strong), qing/bowl strikes, xiao-like breath tones, soft drone.
All synthesized here (no samples, no third-party music), so it is ours to use commercially.
Also renders the SFX stem (opening temple bell, arrow whooshes).
usage: python music.py   -> WORK/music.wav, WORK/sfx.wav (48 kHz stereo)
"""
import os, json, math
import numpy as np, soundfile as sf
from scipy.signal import lfilter, butter, sosfilt

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
RNG = np.random.default_rng(49)

# D yu-mode pentatonic: D F G A C
PENTA = [0, 3, 5, 7, 10]
D2 = 73.416


def deg2hz(deg, base=D2):
    o, k = divmod(deg, 5)
    return base * 2 ** (o + PENTA[k] / 12)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR)).astype(np.float32)


# ----------------------------------------------------------------------------- instruments
def guqin(f, dur=4.0, vel=0.6, slide=0.0, bright=0.5):
    """Karplus-Strong pluck; optional upward/downward slide (semitones) after the attack."""
    n = int(dur * SR)
    N = max(2, int(round(SR / f)))
    exc = RNG.uniform(-1, 1, N).astype(np.float32)
    # soften excitation (finger/nail): lowpass
    b, a = butter(1, 1200 + 3500 * bright, fs=SR)
    exc = lfilter(b, a, exc).astype(np.float32)
    # pluck-position comb for the nasal guqin colour
    p = max(1, N // 7)
    exc = exc - 0.6 * np.roll(exc, p)
    x = np.zeros(n, np.float32)
    x[:N] = exc * vel
    g = 0.9985 - 0.0007 * (f / 300)
    den = np.zeros(N + 2, np.float32)
    den[0] = 1.0
    den[N] = -0.5 * g
    den[N + 1] = -0.5 * g
    y = lfilter([1.0], den, x).astype(np.float32)
    if abs(slide) > 1e-3:
        # time-varying pitch bend starting 0.35 s in
        t = np.arange(n) / SR
        bend = slide * np.clip((t - 0.35) / 0.6, 0, 1) ** 1.5
        rate = 2 ** (bend / 12)
        ph = np.cumsum(rate)
        ph = ph[ph < n - 1]
        y = np.interp(ph, np.arange(n), y).astype(np.float32)
        y = np.pad(y, (0, n - len(y)))
    # body: gentle low resonance + air
    sos = butter(2, [70, 5000], btype="band", fs=SR, output="sos")
    y = sosfilt(sos, y).astype(np.float32)
    y *= np.minimum(1, np.arange(n) / (0.003 * SR))
    y[-2000:] *= np.linspace(1, 0, 2000)
    return y


def harmonic_tone(f, dur=4.0, vel=0.3):
    """guqin 'fanyin' (flageolet): near-sine with soft inharmonic shimmer."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * 2.01 * f * t) * np.exp(-t * 2)) * vel
    y *= np.exp(-t / 1.4) * np.minimum(1, t / 0.004)
    return y.astype(np.float32)


def qing(f=392.0, dur=9.0, vel=0.5):
    """Stone chime / bowl: inharmonic partials, long decay, slight beating."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 5.0), (2.76, 0.5, 3.0), (5.40, 0.25, 1.6), (8.93, 0.12, 0.9), (1.003, 0.6, 5.5)]
    y = sum(a * np.sin(2 * np.pi * f * r * t + RNG.uniform(0, 6)) * np.exp(-t / tau) for r, a, tau in parts)
    y *= np.minimum(1, t / 0.002) * vel / 2.2
    return y.astype(np.float32)


def temple_bell(dur=10.0, vel=0.9):
    """Large bronze bell: hum, prime, tierce (minor third), quint, nominal; long hum."""
    f = 98.0
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(0.5, 0.8, 7.0), (1.0, 1.0, 5.0), (1.19, 0.55, 3.5), (1.5, 0.35, 2.8), (2.0, 0.45, 2.2),
             (2.52, 0.2, 1.4), (3.0, 0.12, 1.0), (0.502, 0.5, 8.0)]
    y = sum(a * np.sin(2 * np.pi * f * r * t + k) * np.exp(-t / tau) for k, (r, a, tau) in enumerate(parts))
    strike = RNG.normal(0, 1, int(0.03 * SR)).astype(np.float32) * np.exp(-np.arange(int(0.03 * SR)) / (0.006 * SR))
    sos = butter(2, [300, 3000], btype="band", fs=SR, output="sos")
    y[:len(strike)] += sosfilt(sos, strike) * 0.6
    y *= np.minimum(1, t / 0.003) * vel / 2.5
    return y.astype(np.float32)


def xiao(f, dur, vel=0.18):
    """Breathy end-blown flute: sine + 2nd/3rd partials, slow attack, delayed vibrato, filtered breath noise."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.6) / 0.8, 0, 1)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    noise = RNG.normal(0, 1, n).astype(np.float32)
    sos = butter(2, [f * 0.8, f * 3.5], btype="band", fs=SR, output="sos")
    y = y + 0.35 * sosfilt(sos, noise)
    a = np.clip(t / 0.45, 0, 1) ** 1.5 * np.clip((dur - t) / 0.9, 0, 1)
    swell = 0.85 + 0.15 * np.sin(np.pi * t / dur)
    return (y * a * swell * vel).astype(np.float32)


def drone(n, f=D2, vel=0.05):
    t = np.arange(n) / SR
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * t / 23.0)
    y = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 1) + 0.3 * np.sin(2 * np.pi * f * 2 * t + 2)) * lfo
    return (y * vel).astype(np.float32)


def whoosh(dur=0.7, vel=0.4, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = RNG.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32)
    blk = 1024
    for i in range(0, n, blk):
        u = i / n
        fc = 400 + 2600 * (u if up else 1 - u)
        sos = butter(2, [fc * 0.6, fc * 1.4], btype="band", fs=SR, output="sos")
        out[i:i + blk] = sosfilt(sos, noise[i:i + blk])
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return (out * e * vel).astype(np.float32)


def thud(vel=0.5):
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 30)) * t) * np.exp(-t / 0.09)
    return (y * vel).astype(np.float32)


# ----------------------------------------------------------------------------- arrangement
def add(buf, x, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= buf.shape[0]:
        return
    x = x[: buf.shape[0] - i]
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.41
    buf[i:i + len(x), 1] += x * gain * r * 1.41


def phrase(buf, t0, t1, density=1.0, lo=4, hi=12, bpm=58, seed=0, harm=0.15, slide_p=0.25):
    """Guqin phrases between t0 and t1."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    t = t0
    deg = rng.integers(lo, hi)
    while t < t1 - 2:
        nnotes = rng.integers(3, 7)
        for k in range(nnotes):
            if t >= t1 - 2:
                break
            deg = int(np.clip(deg + rng.choice([-2, -1, -1, 1, 1, 2, 0, 3, -3]), lo, hi))
            f = deg2hz(deg)
            last = k == nnotes - 1
            if rng.random() < harm and not last:
                add(buf, harmonic_tone(f * 2, 3.0, 0.22), t, pan=rng.uniform(-0.3, 0.3))
            else:
                sl = 0.0
                if last and rng.random() < slide_p * 2:
                    sl = float(rng.choice([2, -2, 3]))
                v = rng.uniform(0.45, 0.7)
                add(buf, guqin(f, 5.0 if last else 3.5, v, slide=sl, bright=rng.uniform(0.3, 0.7)), t,
                    pan=rng.uniform(-0.35, 0.35))
                # occasional octave doubling (two-string unison colour)
                if rng.random() < 0.15:
                    add(buf, guqin(f / 2, 3.5, v * 0.6), t + 0.03, pan=-0.2)
            dur = rng.choice([1, 1, 0.5, 0.5, 1.5, 2]) * beat / max(0.4, density)
            t += dur * (2.2 if last else 1.0)
        t += rng.uniform(2.0, 4.5) * beat / max(0.4, density)


def build(total, scene_starts, events):
    n = int((total + 2) * SR)
    mus = np.zeros((n, 2), np.float32)
    sfx = np.zeros((n, 2), np.float32)
    # drone throughout, gently faded
    dr = drone(n)
    fade_in = np.clip(np.arange(n) / (4 * SR), 0, 1)
    fade_out = np.clip((total + 1.5 - np.arange(n) / SR) / 6, 0, 1)
    dr *= fade_in * fade_out
    mus[:, 0] += dr; mus[:, 1] += dr
    keys = list(scene_starts.keys())
    for i, k in enumerate(keys):
        a = scene_starts[k]
        b = scene_starts[keys[i + 1]] if i + 1 < len(keys) else total
        # chime at each new section (not the very first: the temple bell covers it)
        if i > 0:
            add(mus, qing(392.0 if i % 2 else 440.0, 8, 0.35), max(0, a - 0.35), pan=0.15 * (-1) ** i)
        dens = dict(A=0.8, B=1.0, C=0.7, D=0.6, E=1.0, F=0.85, G=0.9, H=0.75, I=0.6).get(k, 0.8)
        phrase(mus, a + 1.0, b - 0.5, density=dens, seed=100 + i, lo=3 if k in "DGI" else 4, hi=11)
        if k in ("D", "F", "I", "H"):
            # xiao long tones, sparse
            rng = np.random.default_rng(300 + i)
            t = a + 3
            while t < b - 6:
                deg = int(rng.choice([7, 8, 9, 10, 11]))
                d = float(rng.uniform(4, 7))
                add(mus, xiao(deg2hz(deg), d, 0.10), t, pan=0.25)
                t += d + rng.uniform(4, 9)
    # sfx
    add(sfx, temple_bell(11, 0.95), 0.0)
    for name, t in events:
        if name == "whoosh":
            add(sfx, whoosh(0.7, 0.35), t, pan=-0.3)
        elif name == "thud":
            add(sfx, thud(0.45), t)
        elif name == "qing":
            add(sfx, qing(523.25, 8, 0.4), t)
    return mus, sfx


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    L = {d["id"]: d for d in tl["lines"]}
    starts = {}
    for d in tl["lines"]:
        starts.setdefault(d["scene"], d["t0"] - 0.6 if d["scene"] != "A" else 0.0)
    ev = [("whoosh", L["g15"]["t0"] - 0.1), ("thud", L["g15"]["t0"] + 0.6), ("whoosh", L["g16"]["t0"] + 0.3),
          ("qing", L["i09"]["t0"] - 0.3)]
    mus, sfx = build(tl["total"], starts, ev)
    # normalise stems to a fixed peak; final levels are set in the mix
    for x in (mus, sfx):
        x /= max(1e-6, np.abs(x).max()) / 0.8
    sf.write(f"{WORK}/music.wav", mus, SR, subtype="PCM_24")
    sf.write(f"{WORK}/sfx.wav", sfx, SR, subtype="PCM_24")
    print("music", mus.shape[0] / SR, "s")


if __name__ == "__main__":
    main()
