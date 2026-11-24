# -*- coding: utf-8 -*-
"""Synthesised music bed + SFX + voice placement + ducking -> stereo 48 kHz WAV.

usage: python mix.py clips_dir durations.json out.wav [t_end]
All music and sound effects are generated here from scratch (no samples).
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

SR = 48000
RNG = np.random.default_rng(1234)


def db(x):
    return 10 ** (x / 20)


# ------------------------------------------------------------------ instruments
def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(freq, dur=1.6, vel=1.0, bright=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 9):
        f = freq * k * (1 + 0.0007 * k * k)
        if f > 9000:
            break
        amp = (1.0 / k ** 1.4) * (bright if k > 2 else 1.0)
        dec = 2.2 + 1.6 * k
        out += (amp * np.exp(-dec * t) * np.sin(2 * np.pi * f * t + RNG.uniform(0, 6.28))).astype(np.float32)
    att = np.minimum(1, t / 0.006)
    return (out * att * vel * 0.35).astype(np.float32)


def bass(freq, dur=1.3, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.01) * np.exp(-2.4 * t)
    w = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return (w * env * vel * 0.32).astype(np.float32)


def pad(freqs, dur, att=2.5, rel=2.5, vel=1.0, cutoff=900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.004, 0.0, 0.0045):
            ph = RNG.uniform(0, 1)
            saw = 2 * ((t * f * (1 + det) + ph) % 1.0) - 1
            out += saw.astype(np.float32)
    sos = butter(2, cutoff, btype="lowpass", fs=SR, output="sos")
    out = sosfilt(sos, out).astype(np.float32)
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel)
    env = np.clip(env, 0, 1)
    lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.11 * t)
    return (out * env * lfo * vel * 0.05).astype(np.float32)


CHORDS = {
    "Cmaj9": [48, 55, 59, 62, 64], "Am7": [45, 52, 55, 60, 64], "Fmaj7": [41, 53, 57, 60, 64],
    "G6": [43, 50, 55, 59, 64], "Em7": [40, 52, 55, 59, 62], "Dm7": [38, 50, 53, 57, 60],
    "G7sus": [43, 50, 55, 60, 65], "Cmaj7": [48, 55, 59, 64, 67], "Fadd9": [41, 53, 57, 60, 67],
}
PROGS = {
    "A": ["Cmaj9", "Am7", "Fmaj7", "G6"],
    "B": ["Fmaj7", "G6", "Em7", "Am7"],
    "C": ["Dm7", "G7sus", "Cmaj7", "Am7"],
}
# segment -> (progression, style)
STYLE = {"s01": ("A", "arp"), "s02": ("A", "arp"), "title": ("A", "hit"), "s03": ("B", "sparse"),
         "s04": ("C", "sparse"), "s05": ("A", "arp"), "s06": ("C", "arp"), "s07": ("B", "sparse"),
         "s08": (None, "drone"), "s10": ("C", "sparse"), "s11": ("A", "end")}
BPM = 92


def render_music(tl, total):
    n = int(total * SR) + SR * 4
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)
    beat = 60 / BPM
    bar = beat * 4

    def add(sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        gl = math.cos((pan + 1) * math.pi / 4) * gain
        gr = math.sin((pan + 1) * math.pi / 4) * gain
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    for seg in tl["segs"]:
        prog, style = STYLE.get(seg["id"], ("A", "sparse"))
        t0, t1 = seg["t0"], seg["t1"]
        if style == "drone":
            dur = t1 - t0 + 3
            add(pad([midi_hz(33), midi_hz(40), midi_hz(45)], dur, att=3, rel=3, vel=1.0, cutoff=600), t0 - 0.5, 0, 1.0)
            add(pad([midi_hz(57), midi_hz(64)], dur, att=5, rel=4, vel=0.35, cutoff=1200), t0 + 2, 0.3, 1.0)
            continue
        if style == "hit":
            for k, m in enumerate(CHORDS["Cmaj9"]):
                add(pluck(midi_hz(m + 12), 3.0, 0.9), t0 + 0.05 + k * 0.05, -0.4 + k * 0.2)
            add(bass(midi_hz(36), 2.5, 1.0), t0 + 0.05)
            continue
        chords = PROGS[prog]
        bt = t0 + (0.3 if seg.get("chapter_t") is None else 1.2)
        k = 0
        while bt < t1 - 0.2:
            ch = CHORDS[chords[k % 4]]
            fade = min(1.0, (t1 - bt) / 1.5)
            add(bass(midi_hz(ch[0] - 12 if ch[0] > 40 else ch[0]), bar * 0.95, 0.9 * fade), bt)
            if style == "arp":
                pat = [1, 2, 3, 4, 3, 2, 4, 3]
                for e in range(8):
                    m = ch[pat[e]] + 12
                    vel = (0.75 if e % 2 == 0 else 0.5) * fade
                    add(pluck(midi_hz(m), 1.4, vel, 0.8), bt + e * beat / 2, -0.35 + 0.1 * (e % 8))
            elif style == "sparse":
                for e, idx in enumerate([1, 3, 2, 4]):
                    add(pluck(midi_hz(ch[idx] + 12), 2.2, 0.55 * fade, 0.7), bt + e * beat, -0.3 + 0.2 * e)
            elif style == "end":
                for e, idx in enumerate([1, 2, 3, 4]):
                    add(pluck(midi_hz(ch[idx] + 12), 2.6, 0.5 * fade, 0.7), bt + e * beat * 1.0, -0.3 + 0.2 * e)
            bt += bar
            k += 1
        if style == "end":
            for kk, m in enumerate(CHORDS["Cmaj9"]):
                add(pluck(midi_hz(m + 12), 4.0, 0.7), t1 - 1.0 + kk * 0.06, -0.4 + kk * 0.2)
    sos = butter(2, [60, 9000], btype="bandpass", fs=SR, output="sos")
    L = sosfiltfilt(sos, L).astype(np.float32)
    R = sosfiltfilt(sos, R).astype(np.float32)
    return L, R


# ------------------------------------------------------------------ sfx
def env_exp(n, dec):
    t = np.arange(n) / SR
    return np.exp(-dec * t)


def sfx_pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 520 + 900 * t / t[-1]
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.minimum(1, t / 0.004) * np.exp(-38 * t) * 0.5).astype(np.float32)


def sfx_ding():
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * 1568 * t) * np.exp(-5.5 * t) + 0.45 * np.sin(2 * np.pi * 2349 * t) * np.exp(-8 * t)
         + 0.2 * np.sin(2 * np.pi * 3136 * t) * np.exp(-12 * t))
    return (s * np.minimum(1, t / 0.002) * 0.32).astype(np.float32)


def click(dur=0.025, f0=3000):
    n = int(dur * SR)
    nz = RNG.standard_normal(n).astype(np.float32)
    sos = butter(2, [f0 * 0.6, f0 * 1.6], btype="bandpass", fs=SR, output="sos")
    return (sosfilt(sos, nz) * env_exp(n, 160) * 0.6).astype(np.float32)


def sfx_type(dur=0.8):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    t = 0.02
    while t < dur - 0.05:
        c = click(0.03, RNG.uniform(2200, 3800)) * RNG.uniform(0.6, 1.0)
        i = int(t * SR)
        out[i:i + len(c)] += c[: n - i]
        t += RNG.uniform(0.07, 0.13)
    return out


def sfx_whoosh(dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = RNG.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    # time-varying band: process in blocks
    blk = 1024
    for i in range(0, n, blk):
        fc = 400 + 2600 * (i / n)
        sos = butter(2, [fc * 0.7, fc * 1.4], btype="bandpass", fs=SR, output="sos")
        out[i:i + blk] = sosfilt(sos, nz[i:i + blk])
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return (out * env * 0.35).astype(np.float32)


def sfx_flip():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    nz = RNG.standard_normal(n).astype(np.float32)
    sos = butter(2, [900, 5000], btype="bandpass", fs=SR, output="sos")
    e = np.minimum(1, t / 0.01) * np.exp(-18 * t)
    return (sosfilt(sos, nz) * e * 0.45).astype(np.float32)


def sfx_thud():
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = 110 * np.exp(-6 * t) + 45
    ph = 2 * np.pi * np.cumsum(f) / SR
    nz = sosfilt(butter(2, 800, fs=SR, output="sos"), RNG.standard_normal(n)) * np.exp(-40 * t) * 0.3
    return ((np.sin(ph) * np.exp(-9 * t) + nz) * 0.6).astype(np.float32)


def room_tone(dur):
    n = int(dur * SR)
    nz = RNG.standard_normal(n).astype(np.float32)
    sos = butter(2, [80, 900], btype="bandpass", fs=SR, output="sos")
    x = sosfilt(sos, nz).astype(np.float32)
    x /= (np.sqrt((x ** 2).mean()) + 1e-9)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.0)
    return (x * np.clip(env, 0, 1) * db(-50)).astype(np.float32)


# ------------------------------------------------------------------ main mix
def build(clips_dir, dur_path, t_end=None):
    tl, _ = render.make(dur_path)
    total = tl["total"] if t_end is None else t_end
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for c in tl["clips"]:
        p = os.path.join(clips_dir, c["cid"] + ".wav")
        if not os.path.exists(p) or c["t"] > total:
            continue
        a, sr = sf.read(p, dtype="float32")
        assert sr == SR
        i = int(c["t"] * SR)
        j = min(n, i + len(a))
        voice[i:j] += a[: j - i]
    # ducking envelope
    win = int(0.02 * SR)
    m = n // win
    rms = np.sqrt((voice[: m * win].reshape(m, win) ** 2).mean(1) + 1e-12)
    act = (20 * np.log10(rms + 1e-12) > -42).astype(np.float32)
    # attack 60 ms, release 450 ms smoothing
    g = np.zeros(m, np.float32)
    cur = 0.0
    a_att, a_rel = 1 - math.exp(-1 / 3.0), 1 - math.exp(-1 / 22.0)
    # look-ahead: start ducking slightly before speech
    act = np.maximum(act, np.concatenate([act[4:], np.zeros(4, np.float32)]))
    for i in range(m):
        cur += (act[i] - cur) * (a_att if act[i] > cur else a_rel)
        g[i] = cur
    duck = np.repeat(g, win)
    duck = np.concatenate([duck, np.zeros(n - len(duck), np.float32)])
    mL, mR = render_music(tl, total)
    mL, mR = mL[:n], mR[:n]
    if len(mL) < n:
        mL = np.pad(mL, (0, n - len(mL)))
        mR = np.pad(mR, (0, n - len(mR)))
    # normalise music bed then apply level + duck
    mrms = np.sqrt((mL ** 2 + mR ** 2).mean() / 2 + 1e-12)
    base = db(-25.0) / (mrms + 1e-9)
    mg = base * (1 - (1 - db(-9.0)) * duck)
    mL *= mg
    mR *= mg
    # sfx
    sL = np.zeros(n, np.float32)
    sR = np.zeros(n, np.float32)
    lib = {"pop": (sfx_pop(), -20), "ding": (sfx_ding(), -17), "type": (sfx_type(), -24),
           "whoosh": (sfx_whoosh(), -22), "flip": (sfx_flip(), -20), "thud": (sfx_thud(), -16)}

    def put(name, t, pan=0.0):
        sig, lvl = lib[name]
        i = int(max(0, t) * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        pk = np.abs(sig).max() + 1e-9
        s = sig[: j - i] / pk * db(lvl)
        sL[i:j] += s * math.cos((pan + 1) * math.pi / 4)
        sR[i:j] += s * math.sin((pan + 1) * math.pi / 4)

    for (t, name) in tl["sfx"]:
        if name in lib:
            put(name, t)
    for seg in tl["segs"]:
        tr = seg["trig"]
        if "calendar" in tr:
            for k in range(3):
                put("flip", tr["calendar"] + k * 1.25, 0.4)
        for (st, sname) in seg["scenes"]:
            if sname == "contract":
                put("thud", st + 1.45)
            if sname in ("meeting_us", "meeting_cn"):
                end = min([x for x, _ in seg["scenes"] if x > st] + [seg["t1"]])
                rt = room_tone(end - st)
                i = int(st * SR)
                j = min(n, i + len(rt))
                sL[i:j] += rt[: j - i]
                sR[i:j] += rt[: j - i] * 0.9
    outL = voice + mL + sL
    outR = voice + mR + sR
    out = np.stack([outL, outR], 1)
    pk = np.abs(out).max()
    lim = db(-1.0)
    if pk > lim:
        over = np.abs(out) > lim * 0.8
        out = np.where(over, np.sign(out) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(out) - lim * 0.8) / (lim * 0.2))), out)
    return out[: int(total * SR)].astype(np.float32), voice[: int(total * SR)]


if __name__ == "__main__":
    clips_dir, dur_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    t_end = float(sys.argv[4]) if len(sys.argv) > 4 else None
    out, voice = build(clips_dir, dur_path, t_end)
    sf.write(out_path, out, SR, subtype="PCM_16")
    print("wrote", out_path, round(len(out) / SR, 2), "s")
