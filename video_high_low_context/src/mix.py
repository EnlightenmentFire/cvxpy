# -*- coding: utf-8 -*-
"""Voice placement + three-layer music (music.py) + SFX + band-split sidechain -> stereo 48 kHz WAV.

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
import music  # noqa: E402

SR = 48000
RNG = np.random.default_rng(1234)


def db(x):
    return 10 ** (x / 20)


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
MUSIC_RMS = -24.0      # music bus level before sidechain (dBFS RMS)
SC_THR = -46.0         # detector threshold on the voice track (dBFS)
SC_RATIO = 4.0
SC_MAX = {"low": 7.0, "mid": 12.0, "high": 8.0}   # max gain reduction per band (dB)
SC_ATT, SC_REL = 0.015, 0.30                       # seconds


def sidechain(mL, mR, key):
    """Duck the music where the voice is, harder in the 250 Hz-4 kHz speech band."""
    n = len(mL)
    hop = 240  # 5 ms
    m = n // hop + 1
    k = np.pad(key, (0, m * hop - len(key)))[: m * hop].reshape(m, hop)
    lvl = 10 * np.log10((k ** 2).mean(1) + 1e-12)
    # look-ahead 20 ms so the duck starts with the first syllable
    lvl = np.maximum(lvl, np.concatenate([lvl[4:], np.full(4, -120.0)]))
    over = np.maximum(0.0, lvl - SC_THR)
    gr_static = over * (1 - 1 / SC_RATIO)
    a_att = 1 - math.exp(-hop / SR / SC_ATT)
    a_rel = 1 - math.exp(-hop / SR / SC_REL)
    gr = np.zeros(m, np.float32)
    cur = 0.0
    for i in range(m):
        tgt = gr_static[i]
        cur += (tgt - cur) * (a_att if tgt > cur else a_rel)
        gr[i] = cur
    gr = np.repeat(gr, hop)[:n]
    bands = {
        "low": butter(4, 250, btype="lowpass", fs=SR, output="sos"),
        "mid": butter(4, [250, 4000], btype="bandpass", fs=SR, output="sos"),
        "high": butter(4, 4000, btype="highpass", fs=SR, output="sos"),
    }
    outL = np.zeros(n, np.float32)
    outR = np.zeros(n, np.float32)
    for name, sos in bands.items():
        gain = db(-np.minimum(gr, SC_MAX[name]))
        outL += sosfiltfilt(sos, mL).astype(np.float32) * gain
        outR += sosfiltfilt(sos, mR).astype(np.float32) * gain
    return outL, outR


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
    # ---- music: three-layer stems (music.py) ----
    mL, mR = music.render(tl, total)
    if len(mL) < n:
        mL = np.pad(mL, (0, n - len(mL)))
        mR = np.pad(mR, (0, n - len(mR)))
    mL, mR = mL[:n], mR[:n]
    mrms = np.sqrt((mL ** 2 + mR ** 2).mean() / 2 + 1e-12)
    g = db(MUSIC_RMS) / (mrms + 1e-9)
    mL *= g
    mR *= g
    # ---- 侧链：voice-keyed, band-split compressor on the music bus ----
    mL, mR = sidechain(mL, mR, voice)
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
