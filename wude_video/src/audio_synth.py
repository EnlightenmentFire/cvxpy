"""Synthesised score + sound effects (编钟 / 磬 / 低鼓 / 埙 / drones) and the final mix.

All sounds are generated here from sine partials and filtered noise (no samples), so the
music is free of third-party rights.
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng_global = np.random.default_rng(1234)

# A-minor pentatonic
NOTE = {"A1": 55.0, "E2": 82.41, "A2": 110.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "G3": 196.0,
        "A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.0, "A4": 440.0, "C5": 523.25,
        "D5": 587.33, "E5": 659.26, "G5": 783.99, "A5": 880.0, "D2": 73.42, "G2": 98.0, "B3": 246.94}
PENTA = ["A3", "C4", "D4", "E4", "G4", "A4", "C5", "D5", "E5"]


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def bandnoise(n, lo, hi, seed=0):
    r = np.random.default_rng(seed)
    x = r.standard_normal(n)
    sos = butter(2, [lo, hi], btype="bandpass", fs=SR, output="sos")
    return sosfilt(sos, x)


def bell(f, dur=6.0, vel=1.0, seed=0):
    """Bronze chime bell (编钟), two-tone: strike tone + minor-third side tone."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(0.5, 0.30, 5.5), (1.0, 1.0, 3.8), (1.19, 0.55, 3.0), (1.5, 0.22, 2.0), (2.0, 0.42, 1.6),
             (2.52, 0.20, 1.0), (2.98, 0.14, 0.8), (4.07, 0.10, 0.45), (5.33, 0.06, 0.28)]
    y = np.zeros(n)
    r = np.random.default_rng(seed)
    for ratio, amp, tau in parts:
        for det in (-0.0014, 0.0014):
            fr = f * ratio * (1 + det + r.normal(0, 0.0004))
            y += amp * 0.5 * np.sin(2 * np.pi * fr * t + r.random() * 6.28) * np.exp(-t / tau)
    att = np.minimum(1, t / 0.002)
    y *= att
    strike = bandnoise(n, 1800, 5200, seed) * np.exp(-t / 0.012) * 0.25
    return (y + strike) * vel * 0.22


def qing(f=740.0, dur=3.0, vel=1.0, seed=0):
    """Stone chime (磬): inharmonic, bright, quicker decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 1.6), (2.32, 0.55, 0.8), (3.86, 0.32, 0.45), (5.1, 0.22, 0.3), (6.9, 0.12, 0.18)]
    y = np.zeros(n)
    for ratio, amp, tau in parts:
        y += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / tau)
    y *= np.minimum(1, t / 0.0015)
    y += bandnoise(n, 3000, 8000, seed) * np.exp(-t / 0.006) * 0.35
    return y * vel * 0.25


def drum(vel=1.0, dry=False, seed=0, f0=92.0, f1=52.0):
    dur = 0.9
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / (0.22 if dry else 0.38))
    sos = butter(2, 260, btype="lowpass", fs=SR, output="sos")
    r = np.random.default_rng(seed)
    y += sosfilt(sos, r.standard_normal(n)) * np.exp(-t / 0.03) * 0.8
    return y * vel * 0.55


def clack(vel=1.0, seed=0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    y = bandnoise(n, 1500, 4500, seed) * np.exp(-t / 0.012) * 1.2
    y += np.sin(2 * np.pi * 1250 * t) * np.exp(-t / 0.02) * 0.4
    return y * vel * 0.3


def xun(f, dur, vel=0.6, seed=0):
    """Breathy vessel flute (埙-like)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1, t / 0.6)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = bandnoise(n, f * 0.8, f * 2.5, seed) * 0.18
    envl = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.35)
    envl = np.clip(envl, 0, 1) ** 1.3
    return (y + breath) * envl * vel * 0.16


def drone(dur, root=55.0, fifth=True, vel=1.0, seed=0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    comps = [(root, 1.0), (root * 2, 0.55), (root * 3, 0.18)]
    if fifth:
        comps += [(root * 1.5, 0.35), (root * 3.0 / 1.0 * 0.999, 0.1)]
    for f, a in comps:
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (0.03 + 0.05 * r.random()) * t + r.random() * 6)
        y += a * np.sin(2 * np.pi * f * t + r.random() * 6) * lfo
    wind = bandnoise(n, 180, 900, seed) * 0.06 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t))
    y += wind
    fade = np.minimum(1, np.minimum(t / 2.5, (dur - t) / 2.5))
    return y * np.clip(fade, 0, 1) * vel * 0.06


def swell(dur=6.0, f=110.0, vel=1.0, seed=0):
    """Long bowed-metal tone for the yellow dragon."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    y = np.zeros(n)
    for ratio, amp in [(1.0, 1.0), (2.0, 0.5), (2.76, 0.3), (4.0, 0.25), (5.4, 0.18), (6.8, 0.1)]:
        y += amp * np.sin(2 * np.pi * f * ratio * t * (1 + r.normal(0, 0.0007)) + r.random() * 6)
    envl = np.minimum(1, t / 1.6) * np.exp(-np.maximum(0, t - 1.6) / 2.6)
    return y * envl * vel * 0.10


def whoosh(dur=1.0, vel=1.0, seed=0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = bandnoise(n, 300, 2500, seed)
    envl = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return y * envl * vel * 0.10


def slash(vel=1.0, seed=0):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    y = bandnoise(n, 2500, 9000, seed) * np.exp(-t / 0.05) * 0.8
    y += np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.25) * 0.15
    return y * vel * 0.35


# ---------------------------------------------------------------- reverb
def make_ir(rt60=2.6, seed=0):
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    r = np.random.default_rng(seed)
    decay = np.exp(-6.9 * t / rt60)
    irl = r.standard_normal(n) * decay
    irr = r.standard_normal(n) * decay
    sos = butter(1, 4500, btype="lowpass", fs=SR, output="sos")
    irl, irr = sosfilt(sos, irl), sosfilt(sos, irr)
    irl[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    irr[: int(0.017 * SR)] *= np.linspace(0, 1, int(0.017 * SR))
    norm = np.sqrt(np.sum(irl ** 2))
    return irl / norm, irr / norm


def reverb(stereo, wet=0.3, rt60=2.6):
    irl, irr = make_ir(rt60)
    mono = stereo.mean(axis=1)
    l = fftconvolve(mono, irl)[: len(mono)]
    r = fftconvolve(mono, irr)[: len(mono)]
    out = stereo * (1 - wet)
    out[:, 0] += l * wet
    out[:, 1] += r * wet
    return out


# ---------------------------------------------------------------- score
class Track:
    def __init__(self, dur):
        self.n = int(dur * SR) + SR * 8
        self.buf = np.zeros((self.n, 2))

    def add(self, t, y, pan=0.0, gain=1.0):
        i = int(t * SR)
        if i >= self.n or i + len(y) <= 0:
            return
        if i < 0:
            y = y[-i:]
            i = 0
        y = y[: self.n - i]
        lg = math.cos((pan + 1) * math.pi / 4) * gain
        rg = math.sin((pan + 1) * math.pi / 4) * gain
        self.buf[i:i + len(y), 0] += y * lg
        self.buf[i:i + len(y), 1] += y * rg


SEG_STYLE = {
    "S0": dict(root="A1", drums=None, xun=False, bells=0.10),
    "S1": dict(root="A1", drums=None, xun=True, bells=0.16),
    "S2": dict(root="A1", drums="qin", xun=False, bells=0.05),
    "S3": dict(root="D2", drums="soft", xun=False, bells=0.10),
    "S4": dict(root="D2", drums="soft", xun=True, bells=0.08),
    "S5": dict(root="G2", drums=None, xun=True, bells=0.16),
    "S6": dict(root="A1", drums=None, xun=True, bells=0.14),
    "S7": dict(root="D2", drums="soft", xun=False, bells=0.12),
    "S8": dict(root="A1", drums=None, xun=True, bells=0.10),
    "S9": dict(root="A1", drums=None, xun=False, bells=0.12),
}


def build_music(tl, music_stops=(), drum_stop_times=(), seed=7):
    """Score that follows the segments. Returns stereo buffer (music only)."""
    T = Track(tl.total)
    r = np.random.default_rng(seed)
    for seg in tl.segs:
        st = SEG_STYLE.get(seg["id"], SEG_STYLE["S1"])
        t0, t1 = seg["t0"] - 1.0, seg["t1"] + 1.5
        dur = t1 - t0
        root = NOTE[st["root"]]
        T.add(t0, drone(dur, root, seed=r.integers(1e6)), pan=0.0, gain=1.0)
        # sparse bells on the pentatonic scale
        t = t0 + 2.0
        while t < t1 - 2:
            if r.random() < st["bells"] * 3:
                note = NOTE[PENTA[r.integers(0, 6)]]
                T.add(t, bell(note, 5.0, vel=0.55 + 0.3 * r.random(), seed=r.integers(1e6)),
                      pan=r.uniform(-0.5, 0.5), gain=0.8)
            t += r.uniform(3.5, 7.0)
        # xun phrases
        if st["xun"]:
            t = t0 + 4.0
            idx = 3
            while t < t1 - 6:
                if r.random() < 0.55:
                    nnotes = r.integers(3, 6)
                    tt = t
                    for _ in range(nnotes):
                        idx = int(np.clip(idx + r.choice([-2, -1, -1, 1, 1, 2]), 0, len(PENTA) - 1))
                        d = r.choice([1.2, 1.6, 2.2, 2.8])
                        T.add(tt, xun(NOTE[PENTA[idx]] / 2 if idx > 5 else NOTE[PENTA[idx]], d, vel=0.55,
                                      seed=r.integers(1e6)), pan=-0.2, gain=0.9)
                        tt += d * 0.92
                    t = tt + r.uniform(5, 10)
                else:
                    t += r.uniform(6, 10)
        # drums
        if st["drums"] == "qin":
            stop = min([s for s in drum_stop_times if t0 < s < t1] or [t1])
            beat = 60 / 64
            k = 0
            t = seg["t0"] + 0.5
            while t < stop - 0.1:
                accent = (k % 4 == 0)
                T.add(t, drum(vel=0.9 if accent else 0.55, dry=True, seed=k), pan=0.0, gain=1.0)
                if k % 2 == 1:
                    T.add(t, clack(vel=0.5, seed=k), pan=0.25, gain=0.7)
                t += beat
                k += 1
        elif st["drums"] == "soft":
            t = seg["t0"] + 1.0
            k = 0
            while t < t1 - 2:
                T.add(t, drum(vel=0.45 if k % 2 == 0 else 0.3, seed=k + 99), pan=0.0, gain=0.8)
                t += 60 / 50 * (2 if k % 3 == 2 else 1)
                k += 1
    music = reverb(T.buf, wet=0.32, rt60=3.0)
    # sudden stops (新垣平)
    for (ts, d) in music_stops:
        i0, i1 = int(ts * SR), int((ts + d) * SR)
        f = int(0.03 * SR)
        music[i0:i0 + f] *= np.linspace(1, 0, f)[:, None]
        music[i0 + f:i1] = 0
        rr = int(0.8 * SR)
        music[i1:i1 + rr] *= np.linspace(0, 1, rr)[:, None]
    return music


def build_sfx(tl):
    T = Track(tl.total)
    r = np.random.default_rng(3)
    # 磬 at each wheel step
    for (tg, el, lab, fa, ta) in tl.wk_go:
        if abs(ta - fa) > 1:
            T.add(tg + 0.35, qing(740.0, vel=0.9, seed=r.integers(1e6)), pan=0.35, gain=1.0)
    if tl.wk_flip:
        ft, fd = tl.wk_flip
        for i, nm in enumerate(["A3", "C4", "D4", "E4", "G4", "A4"]):
            T.add(ft + 0.1 + i * 0.17, bell(NOTE[nm], 5.0, vel=0.9, seed=i), pan=-0.6 + i * 0.24, gain=1.0)
        T.add(ft + fd * 0.5, bell(NOTE["A2"], 7.0, vel=1.0, seed=77), pan=0, gain=1.2)
    for (t, name) in tl.sfx:
        if name == "bells_soft":
            for i, nm in enumerate(["E4", "D4", "A3"]):
                T.add(t + i * 0.6, bell(NOTE[nm], 6.0, vel=0.6, seed=i + 40), pan=-0.3 + 0.3 * i, gain=0.9)
        elif name == "long_tone":
            T.add(t - 0.2, swell(7.0, 110.0, vel=1.0), gain=1.0)
            T.add(t + 1.3, bell(NOTE["A2"], 7.0, vel=0.8, seed=5), gain=0.9)
        elif name == "seal":
            T.add(t, drum(vel=0.6, dry=True, f0=140, f1=70), gain=0.9)
            T.add(t, clack(vel=0.6), gain=0.8)
    for (t, name, p) in tl.fx:
        if name == "banner":
            T.add(t, whoosh(1.2, vel=1.0), pan=0.3)
            T.add(t + 0.3, drum(vel=0.9, seed=11), gain=1.0)
        elif name == "snake_cut":
            T.add(t, slash(vel=1.0), pan=0.1)
        elif name == "list":
            T.add(t, drum(vel=0.8, dry=True, seed=int(p.get("i", 0)) + 50), gain=0.9)
        elif name == "dragon":
            pass
        elif name in ("seal_stamp",):
            T.add(t, drum(vel=0.7, dry=True, f0=150, f1=70), gain=0.9)
            T.add(t, clack(vel=0.7), gain=0.8)
        elif name == "zhongshi":
            pass
    # title / slip reveal bell
    s0 = tl.segs[0]
    T.add(s0["t0"] + 0.8, bell(NOTE["A2"], 7.0, vel=0.8, seed=9), gain=0.9)
    return reverb(T.buf, wet=0.25, rt60=2.6)


def voice_track(tl, voice_dir):
    n = int(tl.total * SR) + SR * 8
    v = np.zeros(n)
    for ln in tl.lines:
        p = f"{voice_dir}/{ln['id']}.wav"
        if not os.path.exists(p):
            continue
        y, sr = sf.read(p)
        i = int(ln["t0"] * SR)
        v[i:i + len(y)] += y[: n - i]
    return v


def duck_curve(voice, depth_db=-13.0, attack=0.08, release=0.45):
    win = int(0.03 * SR)
    pad = np.pad(np.abs(voice), (win, win))
    c = np.convolve(pad, np.ones(win) / win, mode="same")[win:-win]
    active = (c > 10 ** (-42 / 20)).astype(float)
    g = np.ones_like(active)
    lo = 10 ** (depth_db / 20)
    a_c = math.exp(-1 / (attack * SR))
    r_c = math.exp(-1 / (release * SR))
    target = np.where(active > 0, lo, 1.0)
    # one-pole smoothing (vectorised in blocks for speed)
    out = np.empty_like(target)
    prev = 1.0
    blk = 480
    for i in range(0, len(target), blk):
        tv = target[i:i + blk].min()
        coef = a_c if tv < prev else r_c
        coef = coef ** blk
        prev = tv + (prev - tv) * coef
        out[i:i + blk] = prev
    return out


def mix(tl, voice_dir, out_wav, music_gain_db=9.0, sfx_gain_db=2.0):
    stops = [(t, 1.1) for (t, n) in tl.sfx if n == "cut"]
    drum_stops = [t for (t, n) in tl.sfx if n == "drum_stop"]
    music = build_music(tl, music_stops=stops, drum_stop_times=drum_stops)
    sfx = build_sfx(tl)
    v = voice_track(tl, voice_dir)
    n = min(len(v), len(music), len(sfx))
    v, music, sfx = v[:n], music[:n], sfx[:n]
    g = duck_curve(v)
    music = music * g[:, None] * 10 ** (music_gain_db / 20)
    sfx = sfx * 10 ** (sfx_gain_db / 20)
    outp = np.zeros((n, 2))
    outp += v[:, None] * 0.98
    outp += music + sfx
    end = int(tl.total * SR)
    outp = outp[: end]
    fo = int(2.0 * SR)
    outp[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pk = np.abs(outp).max()
    if pk > 0.95:
        outp *= 0.95 / pk
    sf.write(out_wav, outp.astype(np.float32), SR, subtype="PCM_24")
    return out_wav
