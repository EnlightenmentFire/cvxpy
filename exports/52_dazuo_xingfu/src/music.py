# -*- coding: utf-8 -*-
"""Original procedural score for EP52 (self-generated, no third-party samples).
Guqin-like plucks (with 泛音 harmonics and 滑音 slides), xiao-like flute, soft drone, 磬 (qing) strikes.
D-gong pentatonic. Writes music.wav (48 kHz stereo) and sfx.wav (qing + phone tick).
usage: python music.py
"""
import json, os, math
import numpy as np, soundfile as sf
from scipy.signal import oaconvolve, butter, sosfilt

D = os.path.dirname(os.path.abspath(__file__))
SR = 48000
TL = json.load(open(f"{D}/timeline.json"))
TOTAL = TL["total"]
N = int(TOTAL * SR) + SR
R = np.random.default_rng(52)

# D gong pentatonic, MIDI
SCALE = [50, 52, 54, 57, 59]  # D3 E3 F#3 A3 B3


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pent(idx):
    o, k = divmod(idx, 5)
    return SCALE[k] + 12 * o


def guqin(f, dur=4.0, vel=1.0, slide=0.0, harmonic=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if slide:
        # 吟猱/上下滑: glide from f*2^(slide/12) to f over 0.35 s after a 0.08 s hold
        g = np.clip((t - 0.08) / 0.35, 0, 1)
        g = g * g * (3 - 2 * g)
        fr = f * 2 ** (slide * (1 - g) / 12)
    else:
        # subtle 吟 vibrato after 0.6 s
        fr = f * (1 + 0.003 * np.sin(2 * np.pi * 4.5 * t) * np.clip((t - 0.6) / 0.6, 0, 1))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.zeros(n)
    if harmonic:  # 泛音: bell-like, few partials, long decay
        for k, a, dec in [(1, 1.0, 0.9), (2, 0.25, 1.6), (3, 0.08, 2.4)]:
            y += a * np.sin(k * ph) * np.exp(-dec * t)
        y *= 0.55
    else:
        B = 0.00025
        for k in range(1, 13):
            kk = k * math.sqrt(1 + B * k * k)
            if f * kk > 9000:
                break
            a = 1.0 / k ** 1.15 * (1 + 0.6 * math.sin(k * 1.7) ** 2)
            dec = 1.1 + 0.45 * k
            y += a * np.sin(kk * ph + R.uniform(0, 6.28)) * np.exp(-dec * t)
        # pluck noise
        nb = R.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / (0.002 * SR))
        y[:len(nb)] += 0.25 * nb
        y *= 0.32
    att = np.clip(t / 0.004, 0, 1)
    return y * att * vel


def xiao(f, dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t + 1.0) * np.clip((t - 0.4) / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    br = R.standard_normal(n)
    sos = butter(2, [f * 0.8, f * 3.5], "bandpass", fs=SR, output="sos")
    br = sosfilt(sos, br) * 0.35
    env = np.clip(t / 0.35, 0, 1) * np.clip((dur - t) / 0.6, 0, 1)
    env *= 0.85 + 0.15 * np.sin(np.pi * np.clip(t / dur, 0, 1))
    return (y + br) * env * vel * 0.22


def qing(dur=7.0, f=520.0, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, a, dec in [(1.0, 1.0, 0.55), (2.76, 0.45, 0.9), (5.40, 0.22, 1.6), (8.93, 0.10, 2.6), (1.005, 0.6, 0.5)]:
        y += a * np.sin(2 * np.pi * f * ratio * t + R.uniform(0, 6)) * np.exp(-dec * t)
    strike = R.standard_normal(int(0.006 * SR)) * np.exp(-np.arange(int(0.006 * SR)) / (0.0015 * SR))
    y[:len(strike)] += 0.3 * strike
    return y * 0.3 * vel


def reverb_ir(sec=3.4, seed=1):
    r = np.random.default_rng(seed)
    n = int(sec * SR)
    t = np.arange(n) / SR
    irs = []
    for ch in range(2):
        x = r.standard_normal(n) * np.exp(-t / (sec / 6.9) * 1.0)
        # darken tail progressively: simple one-pole with time varying coefficient approximated by two bands
        lo = sosfilt(butter(1, 2500, "low", fs=SR, output="sos"), x)
        mix = np.exp(-t / 0.6)
        x = x * mix + lo * (1 - mix)
        x[:int(0.012 * SR)] *= 0.2
        irs.append(x / np.sqrt((x ** 2).sum()))
    return irs


def add(buf, sig, t0, pan=0.0):
    i = int(t0 * SR)
    if i >= buf.shape[1]:
        return
    j = min(buf.shape[1], i + len(sig))
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i:j] += sig[:j - i] * l
    buf[1, i:j] += sig[:j - i] * r


# ---- sections from timeline ----
lines = TL["lines"]
SEC = {}
order = ["一", "二", "三", "四", "五", "六"]
sec_of = {"hook": 0, "hook_q": 0, "stat": 0, "paper": 0, "bars": 0, "causal": 0, "title": 0,
          "funnel": 1, "control": 1, "scroll": 1, "es": 1, "scroll2": 1, "verdict": 1,
          "metta": 2, "fred": 2, "build": 2, "fredlim": 2,
          "hype": 3, "hype1": 3, "hype2": 3, "pubbias": 3, "placebo": 3, "lindahl": 3, "zhiyi": 3,
          "yz": 4, "jgj": 4, "tj": 4, "wander": 4, "notproof": 4,
          "breath": 5, "street": 5, "end": 5}
starts = {}
for l in lines:
    s = sec_of[l["scene"]]
    starts.setdefault(s, l["start"])
bounds = [0.0] + [starts[k] - 0.6 for k in range(1, 6)] + [TOTAL]
title_t = next(l["start"] for l in lines if l["scene"] == "title")
end_t = next(l["start"] for l in lines if l["scene"] == "end")
last_line = lines[-1]
# (density notes/sec, harmonic prob, xiao on, drone level, register offset)
STYLE = [
    (0.55, 0.45, False, 1.0, 5),   # 一 hook: flowing, light
    (0.85, 0.20, False, 0.9, 0),   # 二 evidence: steady flow
    (0.90, 0.25, True, 0.9, 5),    # 三 metta: warm, xiao
    (0.45, 0.10, False, 0.8, -2),  # 四 limits: sparse, plain
    (0.40, 0.55, True, 1.0, 5),    # 五 印照: harmonics + xiao
    (0.70, 0.35, True, 1.0, 3),    # 六 ending
]

mus = np.zeros((2, N))
# guqin phrases
for si in range(6):
    a, b = bounds[si], bounds[si + 1]
    dens, hp, xon, dl, reg = STYLE[si]
    t = a + 0.8
    idx = 7 + reg // 2
    while t < b - 1.0:
        # phrase of 4-8 notes then a breath
        nn = R.integers(4, 9)
        for _ in range(nn):
            if t >= b - 1.0:
                break
            step = R.choice([-2, -1, -1, 0, 1, 1, 2, 3, -3])
            idx = int(np.clip(idx + step, 3, 13))
            m = pent(idx) + 0  # around D3..B4
            harm = R.random() < hp
            f = mtof(m + (12 if harm else 0))
            sl = 0.0 if harm else (R.choice([0, 0, 0, -2, 2]) if R.random() < 0.3 else 0)
            vel = R.uniform(0.6, 1.0)
            note = guqin(f, 4.5 if not harm else 5.0, vel, sl, harm)
            add(mus, note, t, pan=R.uniform(-0.35, 0.35))
            if R.random() < 0.18 and not harm:  # octave/fifth dyad (撮)
                add(mus, guqin(f * 1.5, 3.5, vel * 0.5), t + 0.02, pan=0.2)
            t += R.choice([0.5, 0.75, 0.75, 1.0, 1.0, 1.5]) / dens * 0.62
        t += R.uniform(1.5, 3.5)
    # xiao lines
    if xon:
        t = a + R.uniform(4, 9)
        while t < b - 6:
            k = R.integers(2, 5)
            for _ in range(k):
                m = pent(int(np.clip(R.integers(8, 13), 0, 14))) + 12
                d = R.uniform(2.2, 4.0)
                add(mus, xiao(mtof(m), d, R.uniform(0.6, 0.9)), t, pan=-0.25)
                t += d * R.uniform(0.85, 1.0)
            t += R.uniform(14, 24)

# drone pad D2/A2 with slow swell
tt = np.arange(N) / SR
lvl = np.interp(tt, [(bounds[i] + bounds[i + 1]) / 2 for i in range(6)], [STYLE[i][3] for i in range(6)])
pad = (np.sin(2 * np.pi * mtof(38) * tt) * 0.5 + np.sin(2 * np.pi * mtof(45) * tt + 1) * 0.3 +
       np.sin(2 * np.pi * mtof(50) * tt * 1.001) * 0.15)
pad *= (0.75 + 0.25 * np.sin(2 * np.pi * tt / 23.0)) * lvl * 0.10
nz = sosfilt(butter(2, [180, 900], "bandpass", fs=SR, output="sos"), R.standard_normal(N)) * 0.02
mus[0] += pad + nz; mus[1] += pad * 0.97 + np.roll(nz, 977)

# qing strikes at section changes (soft), and title
for k in range(1, 6):
    add(mus, qing(7, 520, 0.55), bounds[k] + 0.3, pan=0.1)
add(mus, qing(7, 520, 0.45), title_t - 0.4, pan=-0.1)

# reverb
irs = reverb_ir()
wet = np.stack([oaconvolve(mus[0], irs[0])[:N], oaconvolve(mus[1], irs[1])[:N]])
mix = mus * 0.75 + wet * 0.55
# fade in quick (music present from frame 0), fade out after last line
fo0 = last_line["start"] + last_line["dur"] + 0.5
env = np.clip(tt / 0.05, 0, 1) * np.clip(1 - (tt - fo0) / (TOTAL - fo0 + 0.01), 0, 1)
mix *= env
mix = mix[:, :int(TOTAL * SR)]
mix /= np.abs(mix).max() + 1e-9
mix *= 0.7
sf.write(f"{D}/music.wav", mix.T.astype(np.float32), SR)

# sfx: opening qing (clear, attention) + soft phone tick at 0.45 s
sfx = np.zeros((2, int(TOTAL * SR)))
add(sfx, qing(8, 600, 1.0), 0.0, pan=0.0)
add(sfx, qing(8, 600 * 1.5, 0.35), 0.04, pan=0.15)
irs2 = reverb_ir(2.5, 3)
q = np.stack([oaconvolve(sfx[0], irs2[0])[:sfx.shape[1]], oaconvolve(sfx[1], irs2[1])[:sfx.shape[1]]]) * 0.5 + sfx
tick_t = np.arange(int(0.12 * SR)) / SR
tick = (np.sin(2 * np.pi * 1318 * tick_t) * (tick_t < 0.055) + np.sin(2 * np.pi * 1760 * tick_t) * (tick_t >= 0.06)) * np.exp(-tick_t / 0.05) * 0.12
add(q, tick, 0.55)
q /= np.abs(q).max() + 1e-9
sf.write(f"{D}/sfx.wav", (q * 0.8).T.astype(np.float32), SR)
print("music", mix.shape[1] / SR, "s")
