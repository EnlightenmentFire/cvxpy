# -*- coding: utf-8 -*-
"""Original score, synthesised from scratch (no samples, no third-party recordings → no licence issue).
Guqin-like plucks (additive, 吟猱 vibrato, slides), qing/bowl strikes (inharmonic partials), xiao (breathy flute),
a low drone, then a synthetic hall reverb. Follows the timeline's sections.
usage: python music.py  -> /tmp/claude-0/work/stems/music.wav (48 kHz stereo), /tmp/claude-0/work/stems/sfx.wav
"""
import json, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, oaconvolve

SR = 48000
WORK = "/tmp/claude-0/work"
TL = json.load(open(f"{WORK}/timeline.json"))
DUR = TL["total"] + 0.5
N = int(DUR * SR)
rng = np.random.default_rng(53)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


# ------------------------------------------------------------------ instruments
def guqin(f0, dur=4.5, vel=1.0, slide=0.0, vib=True, harmonic=False):
    n = int(dur * SR); t = np.arange(n) / SR
    glide = 1 + slide * (1 - np.exp(-t / 0.22))
    vibr = 1 + (0.0035 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.35) / 0.4, 0, 1) * np.exp(-t / 2.5) if vib else 0)
    f = f0 * glide * vibr
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros(n)
    if harmonic:     # 泛音: bell-like, few partials
        for k, a, tau in [(1, 1.0, 2.2), (2, 0.25, 1.2), (3, 0.08, 0.7)]:
            out += a * np.sin(k * ph) * np.exp(-t / tau)
    else:
        pos = 0.16
        for k in range(1, 12):
            a = abs(np.sin(np.pi * k * pos)) / k ** 1.15
            tau = 2.6 / (1 + 0.55 * (k - 1))
            inh = 1 + 0.0004 * k * k
            out += a * np.sin(k * inh * ph) * np.exp(-t / tau)
        nz = rng.normal(0, 1, n) * np.exp(-t / 0.012)
        out += 0.10 * lp(nz, 2200)
        out = lp(out, 2600 + 1200 * vel)
    out *= np.clip(t / 0.004, 0, 1)
    return out * vel * 0.32


def qing(f0, dur=10.0, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for r, a, tau in [(1.0, 1.0, 7.0), (2.32, 0.55, 4.0), (4.25, 0.35, 2.2), (6.63, 0.18, 1.2), (9.38, 0.1, 0.6)]:
        for det in (-0.25, 0.25):
            out += 0.5 * a * np.sin(2 * np.pi * (f0 * r + det) * t + rng.uniform(0, 6)) * np.exp(-t / tau)
    strike = lp(rng.normal(0, 1, n) * np.exp(-t / 0.006), 5000) * 0.3
    out = (out + strike) * np.clip(t / 0.002, 0, 1)
    return out * vel * 0.22


def xiao(f0, dur, vel=1.0, scoop=True):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.clip(t / 0.28, 0, 1) * np.clip((dur - t) / 0.55, 0, 1)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 4.8 * t) * np.clip((t - 0.5) / 0.6, 0, 1)
    sc = 1 - (0.018 * np.exp(-t / 0.12) if scoop else 0)
    ph = 2 * np.pi * np.cumsum(f0 * vib * sc) / SR
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.07 * np.sin(3 * ph)
    breath = bp(rng.normal(0, 1, n), f0 * 1.5, min(f0 * 6, 9000)) * 0.18
    return (tone + breath) * env * vel * 0.16


def drone(f0, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.clip(t / 4, 0, 1) * np.clip((dur - t) / 4, 0, 1)
    sw = 0.75 + 0.25 * np.sin(2 * np.pi * t / 13.0)
    out = sum(a * np.sin(2 * np.pi * f0 * k * (1 + d) * t) for k, a, d in [(1, 1, 0), (1, 0.6, 0.002), (2, 0.25, -0.001), (3, 0.08, 0)])
    return lp(out, 900) * env * sw * vel * 0.05


# ------------------------------------------------------------------ arrangement
L = np.zeros(N); R = np.zeros(N)


def put(sig, t0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[:N - i]
    L[i:i + len(s)] += s * np.sqrt(0.5 * (1 - pan))
    R[i:i + len(s)] += s * np.sqrt(0.5 * (1 + pan))


sc = {s["id"]: s for s in TL["scenes"]}
def S(i):
    return sc[i]["start"]
def E(i):
    return sc[i]["end"]

MINOR = [50, 53, 55, 57, 60, 62, 65, 67, 69, 72]      # D F G A C pentatonic (D3..)
MAJOR = [50, 52, 54, 57, 59, 62, 64, 66, 69, 71]      # D E F# A B


def qin_phrases(t0, t1, scale, density=1.0, beat=0.78, base_oct=0, vel=0.8, seed=0):
    r = np.random.default_rng(seed)
    t = t0
    idx = 3
    while t < t1 - 2:
        nnotes = r.integers(3, 7)
        for k in range(nnotes):
            idx = int(np.clip(idx + r.choice([-2, -1, -1, 1, 1, 2, 0]), 0, len(scale) - 1))
            m = scale[idx] + 12 * base_oct - 12
            harm = r.random() < 0.12
            slide = r.choice([0, 0, 0, 0.03, -0.02, 0.06]) if not harm else 0
            put(guqin(midi(m + (12 if harm else 0)), 4.5, vel * r.uniform(0.7, 1.0), slide=slide, harmonic=harm), t,
                pan=r.uniform(-0.35, 0.35))
            t += beat * r.choice([1, 1, 0.5, 1.5, 2]) / density
            if t > t1 - 2:
                break
        t += beat * r.uniform(2, 5) / density


def xiao_line(t0, t1, notes, seed=0, vel=0.8):
    r = np.random.default_rng(seed)
    t = t0
    for m, d in notes:
        if t + d > t1:
            break
        if m is not None:
            put(xiao(midi(m), d, vel), t, pan=0.15)
        t += d


# opening: deep bowl strike exactly at frame 0 (the sound hook), drone, sparse qin
put(qing(midi(45) * 1.0, 14, 1.25), 0.0, pan=0.0)
put(qing(midi(69), 8, 0.35), 0.02, pan=0.2)
put(drone(midi(38), E("s05_disclaimer") + 4, 0.9), 0.0)
qin_phrases(2.0, E("s05_disclaimer"), MINOR, density=0.55, seed=1, vel=0.65)
# mechanism (relapse, rumination, origin, design): flowing qin, drone continues
put(drone(midi(38), E("s10_decenter") - S("s06_relapse") + 4, 0.8), S("s06_relapse") - 2)
put(qing(midi(57), 9, 0.5), S("s06_relapse"), pan=-0.2)
qin_phrases(S("s06_relapse") + 1, E("s07_rumination"), MINOR, density=0.8, seed=2, vel=0.7)
put(qing(midi(62), 9, 0.45), S("s08_origin"), pan=0.2)
qin_phrases(S("s08_origin") + 1, E("s10_decenter"), MINOR, density=1.0, seed=3, vel=0.7)
# evidence: steadier, lighter (higher register), drone on A
put(qing(midi(57), 9, 0.5), S("s11_teasdale"), pan=-0.1)
put(drone(midi(45), E("s15_goyal") - S("s11_teasdale") + 4, 0.7), S("s11_teasdale") - 1)
qin_phrases(S("s11_teasdale") + 1, E("s15_goyal"), MINOR, density=1.1, seed=4, vel=0.6, base_oct=1)
# limits & ledger: sparse, thoughtful
put(qing(midi(55), 9, 0.4), S("s16_limits"), pan=0.1)
put(drone(midi(43), E("s16b_ledger") - S("s16_limits") + 3, 0.7), S("s16_limits") - 1)
qin_phrases(S("s16_limits") + 2, E("s16b_ledger"), MINOR, density=0.5, seed=5, vel=0.55)
# sutra: qing strike on the quote, xiao melody, sparse qin
put(qing(midi(45), 14, 0.9), S("s17_arrow"), pan=0.0)
put(drone(midi(38), E("s19_verse") - S("s17_arrow") + 5, 0.9), S("s17_arrow"))
xiao_line(S("s17_arrow") + 3, E("s17_arrow"), [(69, 3.2), (None, 0.8), (67, 1.6), (65, 1.6), (62, 3.8), (None, 2.0),
                                                (65, 2.0), (67, 1.2), (69, 2.4), (72, 3.0), (None, 2.5), (69, 4.0)], seed=6)
qin_phrases(S("s18_two_arrows") + 1, E("s18_two_arrows"), MINOR, density=0.6, seed=7, vel=0.6)
put(qing(midi(62), 10, 0.55), S("s19_verse"), pan=0.2)
xiao_line(S("s19_verse") + 2, E("s19_verse"), [(62, 3.0), (65, 1.5), (67, 1.5), (69, 4.0), (None, 2.0), (72, 2.0),
                                               (69, 2.0), (67, 3.5), (None, 2.0), (62, 5.0)], seed=8)
# dawn: major pentatonic, qin brightens, xiao answers, final bowl
put(drone(midi(38), E("s21_end") - S("s20_yinzhao") + 2, 0.8), S("s20_yinzhao") - 1)
qin_phrases(S("s20_yinzhao") + 0.5, E("s21_end") - 3, MAJOR, density=0.9, seed=9, vel=0.65, base_oct=1)
xiao_line(S("s21_end") + 0.5, E("s21_end"), [(66, 2.0), (69, 2.0), (71, 1.5), (69, 3.5)], seed=10, vel=0.7)
put(qing(midi(50), 12, 0.9), E("s21_end") - 4.2, pan=0.0)

# ------------------------------------------------------------------ reverb (synthetic hall)
def hall(x, seed):
    r = np.random.default_rng(seed)
    n = int(2.9 * SR); t = np.arange(n) / SR
    ir = r.normal(0, 1, n) * np.exp(-t / 0.75)
    ir = lp(ir, 5000); ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    return oaconvolve(x, ir)[:len(x)]


wet = 0.42
L2 = L * (1 - wet) + hall(L, 1) * wet * 1.6
R2 = R * (1 - wet) + hall(R, 2) * wet * 1.6
mus = np.stack([L2, R2], 1)
mus = sosfilt(butter(2, 45, "highpass", fs=SR, output="sos"), mus, axis=0)
mus /= np.abs(mus).max() + 1e-9
mus *= 0.7
os.makedirs(f"{WORK}/stems", exist_ok=True)
sf.write(f"{WORK}/stems/music.wav", mus.astype(np.float32), SR, subtype="FLOAT")


# ------------------------------------------------------------------ SFX: rain ambience + water drops
def rain_bed(dur, level):
    n = int(dur * SR)
    w = rng.normal(0, 1, (n, 2))
    pink = sosfilt(butter(1, 800, "lowpass", fs=SR, output="sos"), w, axis=0) * 3 + sosfilt(butter(2, [2000, 9000], "bandpass", fs=SR, output="sos"), w, axis=0) * 0.6
    env = 0.85 + 0.15 * np.sin(2 * np.pi * np.arange(n) / SR / 7.0)[:, None]
    out = pink * env
    # sparse droplet ticks on the glass
    for _ in range(int(dur * 7)):
        i = rng.integers(0, n - 4000); f = rng.uniform(1800, 4200)
        tt = np.arange(3000) / SR
        tick = np.sin(2 * np.pi * f * tt * (1 - 0.3 * tt / tt[-1])) * np.exp(-tt / 0.006) * rng.uniform(0.2, 0.6)
        pan = rng.uniform(-1, 1)
        out[i:i + 3000, 0] += tick * (1 - pan) / 2; out[i:i + 3000, 1] += tick * (1 + pan) / 2
    out /= np.abs(out).max()
    return out * level


def plop(f0=420):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.8 * np.exp(-t / 0.03))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.09)
    return s * 0.5


fx = np.zeros((N, 2))
def putfx(sig, t0):
    i = int(t0 * SR)
    s = sig[:N - i]
    if s.ndim == 1:
        s = np.stack([s, s], 1) * 0.7
    fx[i:i + len(s)] += s

a0, a1 = 0.0, E("s03_thesis") + 1.5
bed = rain_bed(a1 - a0, 0.22)
bed[-int(1.5 * SR):] *= np.linspace(1, 0, int(1.5 * SR))[:, None]
bed[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
putfx(bed, a0)
b0, b1 = S("s20_yinzhao") - 0.5, E("s20_yinzhao") + 3
bed2 = rain_bed(b1 - b0, 0.12)
bed2 *= np.linspace(1, 0, len(bed2))[:, None] ** 1.5
bed2[:int(1.0 * SR)] *= np.linspace(0, 1, int(1.0 * SR))[:, None]
putfx(bed2, b0)
# drops into water when rings start (rumination: accelerating; settle: one stone)
from water import Water  # noqa: E402  (same ring schedule as the picture)
wr = Water(E("s07_rumination") - S("s07_rumination") + 1, "ruminate")
for (cx, cy, t0, amp, *_r) in wr.rings:
    if S("s07_rumination") + t0 < E("s07_rumination"):
        putfx(plop(380 + 40 * rng.normal()) * min(1.0, 0.35 + 0.15 * amp), S("s07_rumination") + t0)
ws = Water(10, "settle")
for (cx, cy, t0, amp, *_r) in ws.rings:
    putfx(plop(330) * (0.5 * amp / 2), S("s18_two_arrows") + t0)
sf.write(f"{WORK}/stems/sfx.wav", fx.astype(np.float32), SR, subtype="FLOAT")
print("music/sfx", DUR, "s")
