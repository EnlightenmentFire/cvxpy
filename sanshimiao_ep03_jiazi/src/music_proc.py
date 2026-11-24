# -*- coding: utf-8 -*-
"""Original score for ep03, synthesised from scratch (no samples, no models -> no licence questions).

Bright "clockwork" bed in D major at the timeline's tempo (~118.5 BPM), built on the same beat grid as
the gear clicks, so every click sits in the music:

  bars 1-3   marimba 8th-note ostinato + soft strings pad + woodblock tick-tock   (medium from t=0)
  ~beat 12   + pizzicato bass, shaker                                             (gears about to turn;
             woodblock drops out when the gear clicks take over the tick)
  ~beat 28   + kick, spiccato strings, glockenspiel                               (the spin starts)
  ~beat 38   + snare roll, rising strings line, noise riser                       (racing to 60)
  drop       everything cuts to one long high A (the dominant) while the counter sits on 60
  beat 44    hit on the downbeat: timpani + kick + cymbal + full D-major chord, long sustain
  last bar   the opening ostinato re-enters at the opening level -> loops straight back into bar 1

Outputs music.wav (score, stereo 48k) and sfx.wav (gear clicks), plus stems for checking.
Usage: python music_proc.py timeline.json out_dir
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
rng = np.random.default_rng(20261124)

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(name):
    """'D5' -> Hz (A4 = 440)."""
    n, o = name[:-1], int(name[-1])
    m = 12 * (o + 1) + NOTE[n]
    return 440.0 * 2 ** ((m - 69) / 12)


def db(x):
    return 10 ** (x / 20)


def sos_filter(kind, f, order=2):
    if isinstance(f, (list, tuple)):
        return butter(order, [f[0] / (SR / 2), f[1] / (SR / 2)], btype=kind, output="sos")
    return butter(order, f / (SR / 2), btype=kind, output="sos")


# ---------------------------------------------------------------- instruments (mono)
def marimba(f, vel=1.0, dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = (f / 440) ** 0.45
    y = (1.00 * np.exp(-2.6 * k * t) * np.sin(2 * np.pi * f * t)
         + 0.30 * np.exp(-9.0 * k * t) * np.sin(2 * np.pi * 3.99 * f * t + 0.3)
         + 0.08 * np.exp(-22 * k * t) * np.sin(2 * np.pi * 9.2 * f * t + 1.1))
    att = np.minimum(1, t / 0.0015)
    click = sosfilt(sos_filter("bandpass", (1500, 5000)), rng.standard_normal(n)) * np.exp(-t * 400) * 0.10
    return (y * att + click) * vel


def glock(f, vel=1.0, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * t) * np.exp(-3.2 * t) + 0.35 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-7 * t)
         + 0.12 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-14 * t))
    return y * np.minimum(1, t / 0.001) * vel


def pluck(f, vel=1.0, dur=0.9, damp=0.995, bright=0.5):
    """Karplus-Strong pizzicato via an IIR comb (fast)."""
    n = int(dur * SR)
    N = int(SR / f)
    exc = np.zeros(n)
    burst = rng.standard_normal(N)
    burst = sosfilt(sos_filter("lowpass", 600 + 5000 * bright), burst)
    exc[:N] = burst
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -damp * 0.5
    a[N + 1] = -damp * 0.5
    y = lfilter([1.0], a, exc)
    t = np.arange(n) / SR
    y *= np.exp(-t * 3.0)
    y = sosfilt(sos_filter("highpass", 40), y)
    return y / (np.max(np.abs(y)) + 1e-9) * vel


def saw_voice(f, n, vib=0.0018, vrate=5.2, nh=None, phase=0.0):
    t = np.arange(n) / SR
    fi = f * (1 + vib * np.sin(2 * np.pi * vrate * t + phase))
    ph = 2 * np.pi * np.cumsum(fi) / SR + phase
    nh = nh or max(1, min(40, int(7000 / f)))
    y = np.zeros(n)
    for h in range(1, nh + 1):
        y += np.sin(h * ph) / h * (1 - 0.6 * h / nh)
    return y


def strings(freqs, dur, att=0.25, rel=0.5, vel=1.0, cutoff=3200, detune=(-0.004, 0.0, 0.0045), trem=0.0):
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for i, d in enumerate(detune):
            y += saw_voice(f * (1 + d), n, phase=1.7 * i + f % 1)
    y /= max(1, len(freqs) * len(detune)) ** 0.5 * 2.2
    env = np.minimum(1, t / max(att, 1e-3))
    env *= np.where(t < dur, 1.0, np.exp(-(t - dur) / (rel / 3)))
    if trem:
        env *= 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * trem * t))
    y = sosfilt(sos_filter("lowpass", cutoff), y * env)
    return y * vel


def brass(freqs, dur, vel=1.0, rel=0.8):
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for d in (-0.003, 0.003):
            y += saw_voice(f * (1 + d), n, vib=0.001, nh=max(1, int(4000 / f)))
    y /= (len(freqs) * 2) ** 0.5 * 2.4
    env = np.minimum(1, t / 0.04) * (0.75 + 0.25 * np.exp(-t * 3))
    env *= np.where(t < dur, 1.0, np.exp(-(t - dur) / (rel / 3)))
    # opening filter sweep (brassy "bloom")
    lo = sosfilt(sos_filter("lowpass", 900), y)
    hi = sosfilt(sos_filter("lowpass", 3500), y)
    bloom = np.minimum(1, t / 0.25)
    return (lo * (1 - bloom) + hi * bloom) * env * vel


def kick(vel=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 46 + 95 * np.exp(-t * 32)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    y += sosfilt(sos_filter("bandpass", (1500, 6000)), rng.standard_normal(n)) * np.exp(-t * 300) * 0.25
    return np.tanh(1.4 * y) * vel


def snare(vel=1.0, dur=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = sosfilt(sos_filter("bandpass", (1200, 7000)), rng.standard_normal(n)) * np.exp(-t * 26) * 0.8
    y += np.sin(2 * np.pi * 195 * t) * np.exp(-t * 30) * 0.5
    return y * vel


def shaker(vel=1.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    y = sosfilt(sos_filter("bandpass", (5000, 11000)), rng.standard_normal(n))
    return y * np.minimum(1, t / 0.008) * np.exp(-t * 55) * vel


def woodblock(f, vel=1.0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 55) + 0.4 * np.sin(2 * np.pi * 2.3 * f * t) * np.exp(-t * 90)
    return y * vel


def timpani(f, vel=1.0):
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    fi = f * (1 + 0.04 * np.exp(-t * 12))
    ph = 2 * np.pi * np.cumsum(fi) / SR
    y = (np.sin(ph) * np.exp(-t * 1.3) + 0.5 * np.sin(1.5 * ph) * np.exp(-t * 2.5)
         + 0.25 * np.sin(1.98 * ph) * np.exp(-t * 3.5))
    y += sosfilt(sos_filter("lowpass", 800), rng.standard_normal(n)) * np.exp(-t * 40) * 0.6
    return np.tanh(1.2 * y) * vel


def cymbal(vel=1.0, dur=5.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = sosfilt(sos_filter("highpass", 3500), rng.standard_normal(n))
    for fr in (3150, 4430, 5870, 7210, 8960):
        y += 0.15 * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6))
    fade = np.minimum(1, (dur - t) / (0.35 * dur))
    return y * np.exp(-t * 1.9) * np.minimum(1, t / 0.003) * fade * vel


def riser(dur, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    seg = int(0.02 * SR)
    for i in range(0, n, seg):
        p = i / n
        fc = 500 * (6000 / 500) ** p
        sos = sos_filter("bandpass", (fc * 0.7, min(fc * 1.4, 20000)))
        out[i:i + seg] = sosfilt(sos, x[max(0, i - 2000):i + seg])[-len(out[i:i + seg]):]
    return out * (t / dur) ** 2 * vel


def gear_click(vel=1.0, big=False):
    n = int((0.18 if big else 0.07) * SR)
    t = np.arange(n) / SR
    y = sosfilt(sos_filter("bandpass", (2200, 6500)), rng.standard_normal(n)) * np.exp(-t * (90 if big else 160))
    y += 0.5 * np.sin(2 * np.pi * 3300 * t) * np.exp(-t * 120)          # metallic ping
    y += 0.7 * np.sin(2 * np.pi * (170 if big else 230) * t) * np.exp(-t * (35 if big else 70))   # body "thunk"
    if big:
        y += 0.6 * sosfilt(sos_filter("bandpass", (900, 3000)), rng.standard_normal(n)) * np.exp(-t * 45)
    return y * np.minimum(1, t / 0.0005) * vel


# ---------------------------------------------------------------- mixing helpers
class Bus:
    def __init__(self, n, name):
        self.y = np.zeros((n, 2))
        self.name = name

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= len(self.y) or i + len(sig) <= 0:
            return
        j = min(len(self.y), i + len(sig))
        s = sig[: j - i] * gain
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.y[i:j, 0] += s * l * 1.414
        self.y[i:j, 1] += s * r * 1.414


def make_ir(rt60=1.5, pre=0.015):
    n = int((rt60 * 1.2 + pre) * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for c in range(2):
        x = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)
        x = sosfilt(sos_filter("lowpass", 5500), x)
        x[: int(pre * SR)] = 0
        ir[:, c] = x
    return ir / np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True)) * 0.6


def reverb(y, ir, wet):
    out = np.zeros_like(y)
    for c in range(2):
        out[:, c] = fftconvolve(y[:, c], ir[:, c])[: len(y)]
    return y + out * wet


# ---------------------------------------------------------------- score
CHORDS = {   # root, ostinato tones (low->high), pad voicing, bass
    "D": (["D5", "A5", "F#5", "A5", "D6", "A5", "F#5", "A5"], ["D4", "F#4", "A4"], "D2"),
    "A": (["A4", "E5", "C#5", "E5", "A5", "E5", "C#5", "E5"], ["C#4", "E4", "A4"], "A1"),
    "Bm": (["B4", "F#5", "D5", "F#5", "B5", "F#5", "D5", "F#5"], ["B3", "D4", "F#4"], "B1"),
    "G": (["G4", "D5", "B4", "D5", "G5", "D5", "B4", "D5"], ["B3", "D4", "G4"], "G1"),
    "Asus": (["A4", "E5", "D5", "E5", "A5", "E5", "D5", "E5"], ["D4", "E4", "A4"], "A1"),
}
#            bar: 0    1    2     3    4    5    6     7    8    9     10      11   12   13
PROGRESSION = ["D", "A", "Bm", "G", "D", "A", "Bm", "G", "A", "Bm", "Asus", "D", "D", "D"]


def build(tl):
    ev = tl["events"]
    beat = ev["beat"]
    nbeats = ev["total_beats"]
    dur = tl["duration"]
    hit_b = ev["ans_beat"]
    hit_t = hit_b * beat
    drop_t = ev["drop"]
    T = lambda b: b * beat
    n = int(round(dur * SR))
    ext = n + int(4 * SR)               # room for tails; tails past the end are folded to the start
    B = {k: Bus(ext, k) for k in ("mallet", "pad", "bass", "drums", "fx", "hit")}
    sfx = Bus(ext, "sfx")

    L = {l["id"]: l for l in tl["lines"]}
    b_s1 = 12                                       # pizz bass + shaker (just before the gears start at beat 15)
    b_s2 = int(round(L["L5"]["start"] / beat))      # spin starts
    b_s3 = int(round(L["L7"]["start"] / beat))      # racing
    b_tick_end = 15                                 # woodblock tick-tock until gear clicks take over
    ost_levels = []

    def chord_at(b):
        return PROGRESSION[min(int(b // 4), len(PROGRESSION) - 1)]

    for e8 in range(nbeats * 2):                    # eighth notes
        b = e8 / 2
        t = T(b)
        if drop_t - 0.02 <= t < hit_t:
            continue
        name = chord_at(b)
        tones, pad, bass = CHORDS[name]
        i8 = e8 % 8
        after_hit = t >= hit_t
        # ---- marimba ostinato
        if not after_hit or b >= nbeats - 4:
            if b < b_s1:
                lvl = 0.62
            elif b < b_s2:
                lvl = 0.62
            elif b < b_s3:
                lvl = 0.70
            else:
                lvl = 0.78
            if b >= nbeats - 4:                     # last bar: opening level again (loops into bar 1)
                lvl = 0.62
            acc = 1.0 if i8 % 2 == 0 else 0.72
            B["mallet"].add(marimba(hz(tones[i8]), lvl * acc), t, pan=-0.25 if i8 % 2 else 0.2)
            # racing: 16th-note fills
            if b_s3 <= b and not after_hit:
                B["mallet"].add(marimba(hz(tones[(i8 + 2) % 8]), 0.45), t + beat / 4, pan=0.35)
        # ---- woodblock tick-tock (opening only)
        if (b < b_tick_end or b >= nbeats - 4) and i8 % 2 == 0:
            B["drums"].add(woodblock(1750 if (i8 // 2) % 2 == 0 else 1320, 0.20), t, pan=0.4)
        # ---- shaker 8ths
        if b_s1 <= b and not after_hit:
            B["drums"].add(shaker(0.20 + (0.08 if i8 % 2 else 0.0) + (0.06 if b >= b_s2 else 0)), t, pan=0.5)
        # ---- pizz bass on beats
        if b_s1 <= b and not after_hit and i8 % 2 == 0:
            root = hz(bass) * 2
            f = root if (i8 // 2) % 2 == 0 else root * 1.4983      # root / fifth
            B["bass"].add(pluck(f, 0.85, bright=0.35), t, pan=-0.1)
        # ---- kick
        if b_s2 <= b and not after_hit and i8 % 2 == 0:
            B["drums"].add(kick(0.75 if (i8 // 2) % 2 == 0 else 0.6), t)
        if b_s3 <= b and not after_hit and i8 % 2 == 1:
            B["drums"].add(kick(0.45), t)
        # ---- spiccato strings 8ths + glock on beats
        if b_s2 <= b and not after_hit:
            fr = [hz(x) for x in pad]
            B["pad"].add(strings([f * 2 for f in fr], 0.09, att=0.008, rel=0.12, vel=0.55 + 0.25 * (b >= b_s3)), t,
                         pan=0.3 if i8 % 2 else -0.3)
            if i8 % 2 == 0:
                B["mallet"].add(glock(hz(tones[0][:-1] + "6"), 0.20), t, pan=-0.45)

    # ---- sustained pad per bar (soft from t=0)
    for bar in range(nbeats // 4):
        t0 = T(bar * 4)
        if t0 >= hit_t or t0 + T(4) <= 0:
            continue
        name = PROGRESSION[bar]
        _, pad, _ = CHORDS[name]
        end = min(t0 + T(4), drop_t)
        if end <= t0:
            continue
        lvl = 0.38 if bar * 4 < b_s2 else 0.45
        B["pad"].add(strings([hz(x) for x in pad], end - t0, att=0.12, rel=0.35, vel=lvl), t0)

    # ---- racing: rising strings line + snare roll + riser (b_s3 -> drop)
    scale = ["A4", "B4", "C#5", "D5", "E5", "F#5", "G5", "A5", "B5", "C#6", "D6", "E6"]
    t_r0 = T(b_s3)
    nsteps = len(scale)
    for i, nm in enumerate(scale):
        ti = t_r0 + (drop_t - t_r0) * i / nsteps
        dd = (drop_t - t_r0) / nsteps
        if ti >= drop_t:
            break
        B["pad"].add(strings([hz(nm), hz(nm) / 2], dd * 1.05, att=0.03, rel=0.08, vel=0.55 + 0.35 * i / nsteps), ti, pan=0.15)
    # snare roll + riser start only once L6 ("甲，永远碰不上丑") is over, so its last word stays unmasked
    k = 0
    r_start = max(T(b_s3), L["L6"]["end"] + 0.05)
    t = r_start
    while t < drop_t - 0.01:
        p = (t - r_start) / (drop_t - r_start)
        B["drums"].add(snare(0.15 + 0.55 * p ** 1.5, dur=0.18), t, pan=-0.15)
        t += beat / (4 if p < 0.55 else 8)
        k += 1
    rz = riser(drop_t - r_start, 0.30)
    B["fx"].add(rz, r_start)

    # ---- the drop: a single long high A (dominant) with tremolo, swelling slightly into the hit
    gap = hit_t - drop_t
    held = strings([hz("A5"), hz("A4")], gap + 0.02, att=0.02, rel=0.10, vel=0.55, cutoff=4500, trem=11)
    held *= np.linspace(0.85, 1.15, len(held))
    B["pad"].add(held, drop_t, pan=0.05)

    # ---- the hit (downbeat): timpani + kick + cymbal + full D-major chord, long sustain to the end
    tail = dur - hit_t
    B["hit"].add(timpani(hz("D2"), 0.95), hit_t)
    B["hit"].add(kick(1.0), hit_t)
    B["hit"].add(cymbal(0.30), hit_t, pan=0.25)
    chord = [hz(x) for x in ("D3", "A3", "D4", "F#4", "A4", "D5")]
    st = strings(chord, tail, att=0.015, rel=0.6, vel=1.15, cutoff=5200)
    # decay from the hit level to about the opening pad level by the last bar
    env = np.ones(len(st))
    tt = np.arange(len(st)) / SR
    env *= 0.26 + 0.74 * np.exp(-tt / 1.3)
    B["pad"].add(st * env, hit_t)
    br = brass([hz(x) for x in ("D3", "A3", "D4", "F#4")], min(tail, 2.4), vel=0.75, rel=1.2)
    B["hit"].add(br, hit_t)
    B["bass"].add(pluck(hz("D2"), 0.9, dur=2.0, damp=0.998, bright=0.3), hit_t)
    bs = strings([hz("D2"), hz("D3")], tail, att=0.01, rel=0.5, vel=0.32, cutoff=700)
    bs *= 0.35 + 0.65 * np.exp(-np.arange(len(bs)) / SR / 1.0)
    B["bass"].add(bs, hit_t)
    for i, nm in enumerate(["D5", "F#5", "A5", "D6", "F#6", "A6"]):       # marimba run up
        B["mallet"].add(marimba(hz(nm), 0.55), hit_t + i * beat / 4, pan=-0.3 + 0.12 * i)

    # ---- gear clicks (sfx): light ticks, the final one big
    st_times = tl["step_times"]
    for k, ts in enumerate(st_times):
        if k == len(st_times) - 1:
            sfx.add(gear_click(1.0, big=True), ts)
        else:
            fast = k >= 10
            sfx.add(gear_click(0.55 if not fast else 0.38), ts, pan=0.0)

    # ---- render buses (+ reverb), fold the tail past `dur` back onto the start (loop-friendly)
    ir = make_ir(1.6)
    sends = {"mallet": 0.30, "pad": 0.35, "bass": 0.10, "drums": 0.15, "fx": 0.25, "hit": 0.35}
    gains = {"mallet": db(-14), "pad": db(-13), "bass": db(-15), "drums": db(-17), "fx": db(-24), "hit": db(-12)}
    stems = {}
    mix = np.zeros((ext, 2))
    for k, bus in B.items():
        y = reverb(bus.y * gains[k], ir, sends[k])
        stems[k] = y
        mix += y
    sfx_y = reverb(sfx.y * db(-18), make_ir(0.5), 0.12)
    mix[:n] += 0
    # fold: whatever rings past the end continues at the start when the film loops
    mix = sosfilt(sos_filter("highpass", 40), mix, axis=0)
    music = mix[:n].copy()
    tailpart = mix[n:]
    music[: len(tailpart)] += tailpart[: n]
    sfx_out = sfx_y[:n].copy()
    return music, sfx_out, stems, n


def main():
    tl = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    music, sfx, stems, n = build(tl)
    # gentle bus glue: soft clip, normalise peak to -3 dBFS
    pk = np.max(np.abs(music))
    music = music / pk * db(-3)
    sf.write(f"{out}/music.wav", music.astype(np.float32), SR, subtype="FLOAT")
    sfx = sfx / (np.max(np.abs(sfx)) + 1e-9) * db(-6)
    sf.write(f"{out}/sfx.wav", sfx.astype(np.float32), SR, subtype="FLOAT")
    for k, y in stems.items():
        sf.write(f"{out}/stem_{k}.wav", (y[:n] / pk * db(-3)).astype(np.float32), SR, subtype="FLOAT")
    print("music", n / SR, "s")


if __name__ == "__main__":
    main()
