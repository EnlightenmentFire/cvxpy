# -*- coding: utf-8 -*-
"""Self-generated score + SFX (numpy). No samples, no third-party audio -> no licensing issue.
writes out/music.wav (stereo 48k) and out/sfx.wav (stereo 48k), aligned to the timeline."""
import json, math, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt
sys.path.insert(0, "/tmp/claude-0/w73/proj")
import timeline

SR = 48000
rng = np.random.default_rng(73)
TL = timeline.build()
T = TL["total"] + 1.0
N = int(T * SR)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def env_adsr(n, a, r):
    e = np.ones(n, np.float32)
    na, nr = min(int(a * SR), n // 2), min(int(r * SR), n // 2)
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


# ---------------------------------------------------------------- scene boundaries
def scene_times():
    L = TL["lines"]; st = {}
    for r in L:
        st.setdefault(r["scene"], [r["t0"], r["t1"]]); st[r["scene"]][1] = r["t1"]
    for ti in TL["titles"]:
        pass
    return st


SC = scene_times()
SECT = []   # (t0, t1, mood)
moods = {"s01": "drum", "s02": "strings", "s03": "qin", "s04": "drum", "s05": "strings", "s06": "qin", "s07": "rise"}
keys = list(SC.keys())
for i, k in enumerate(keys):
    t0 = 0.0 if i == 0 else SC[k][0] - 2.2
    t1 = SC[keys[i + 1]][0] - 2.2 if i + 1 < len(keys) else T
    SECT.append((t0, t1, moods[k]))

# D minor; chord progression i-VI-III-VII  (Dm Bb F C) and variants
CHORDS = [[38, 50, 53, 57, 62], [34, 46, 50, 53, 58], [41, 48, 53, 57, 60], [36, 48, 52, 55, 60]]


def string_pad(t0, t1, gain=1.0, bright=1100, chord_len=8.0):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    ci = 0; c0 = 0.0
    while c0 < t1 - t0:
        c1 = min(t1 - t0, c0 + chord_len)
        a, b = int(c0 * SR), int(min(t1 - t0, c1 + 2.5) * SR)
        seg_t = t[a:b] - c0
        e = env_adsr(b - a, 2.2, 2.6)
        for j, m in enumerate(CHORDS[ci % 4]):
            f = midi(m)
            for dt, pan in ((-0.12, 0.25), (0.0, 0.5), (0.13, 0.75)):
                ff = f * 2 ** (dt / 12)
                ph = rng.uniform(0, 6.28)
                vib = 1 + 0.003 * np.sin(2 * np.pi * 5.1 * seg_t + ph)
                saw = 2 * ((ff * seg_t * vib + ph) % 1.0) - 1
                amp = (0.5 if j == 0 else 0.32) * e
                out[a:b, 0] += (saw * amp * (1 - pan)).astype(np.float32)
                out[a:b, 1] += (saw * amp * pan).astype(np.float32)
        ci += 1; c0 = c1
    out[:, 0] = lp(out[:, 0], bright, 3); out[:, 1] = lp(out[:, 1], bright, 3)
    # slow swell
    sw = 0.75 + 0.25 * np.sin(2 * np.pi * t / 23.0)
    out *= sw[:, None]
    return out * gain


def taiko(dur=1.2, f0=62, f1=44, noise=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 3.2)
    nz = lp(rng.standard_normal(n), 380) * np.exp(-t * 18) * noise
    sk = bp(rng.standard_normal(n), 900, 3000) * np.exp(-t * 60) * 0.25
    x = body + nz + sk
    return (x / np.abs(x).max()).astype(np.float32)


def drums(t0, t1, bpm=66, gain=1.0, density=1.0):
    n = int((t1 - t0) * SR); out = np.zeros((n, 2), np.float32)
    beat = 60.0 / bpm
    pat = [1.0, 0, 0.45, 0, 0.8, 0, 0.35, 0.3] if density >= 1 else [1.0, 0, 0, 0, 0.6, 0, 0, 0]
    k = 0; tt = 0.0
    big, small = taiko(), taiko(0.6, 110, 80, 0.3)
    while tt < t1 - t0:
        v = pat[k % 8]
        if v > 0:
            s = big if v >= 0.6 else small
            a = int(tt * SR); b = min(n, a + len(s))
            out[a:b, 0] += s[:b - a] * v * 0.9; out[a:b, 1] += s[:b - a] * v
        k += 1; tt += beat / 2
    return out * gain


def qin_note(f, dur=3.5, bright=0.5):
    """Karplus-Strong pluck, body-filtered."""
    n = int(dur * SR); p = int(SR / f)
    buf = rng.uniform(-1, 1, p).astype(np.float32)
    buf = lp(buf, 2000 + 3000 * bright)
    out = np.zeros(n, np.float32)
    decay = 0.9965
    idx = 0
    b = buf.copy()
    for i in range(n):
        v = b[idx]
        nxt = b[(idx + 1) % p]
        b[idx] = decay * 0.5 * (v + nxt)
        out[i] = v
        idx = (idx + 1) % p
    out *= np.exp(-np.arange(n) / SR * 0.6)
    return lp(out, 2600).astype(np.float32)


QIN_CACHE = {}


def qin(t0, t1, gain=1.0, gap=(1.6, 3.4)):
    n = int((t1 - t0) * SR); out = np.zeros((n, 2), np.float32)
    scale = [50, 53, 55, 57, 60, 62, 65, 67, 69]
    i = 4; tt = 1.0
    while tt < t1 - t0 - 1:
        i = int(np.clip(i + rng.choice([-2, -1, -1, 1, 1, 2]), 0, len(scale) - 1))
        m = scale[i]
        if m not in QIN_CACHE:
            QIN_CACHE[m] = qin_note(midi(m))
        s = QIN_CACHE[m]
        a = int(tt * SR); b = min(n, a + len(s)); pan = 0.35 + 0.3 * rng.random()
        v = 0.8 + 0.2 * rng.random()
        out[a:b, 0] += s[:b - a] * v * (1 - pan); out[a:b, 1] += s[:b - a] * v * pan
        if rng.random() < 0.35:           # grace note an octave up
            m2 = m + 12
            if m2 not in QIN_CACHE: QIN_CACHE[m2] = qin_note(midi(m2), 2.5)
            s2 = QIN_CACHE[m2]; a2 = a + int(0.18 * SR); b2 = min(n, a2 + len(s2))
            if a2 < n:
                out[a2:b2, 0] += s2[:b2 - a2] * 0.4; out[a2:b2, 1] += s2[:b2 - a2] * 0.4
        tt += rng.uniform(*gap)
    return out * gain


def drone(t0, t1, gain=1.0):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    x = 0.6 * np.sin(2 * np.pi * midi(26) * t) + 0.3 * np.sin(2 * np.pi * midi(38) * t + 0.4) + 0.15 * np.sin(2 * np.pi * midi(45) * t)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * t / 11)
    return np.stack([x, x], 1).astype(np.float32) * gain


def place(buf, seg, t0):
    a = int(t0 * SR); b = min(len(buf), a + len(seg))
    if b > a:
        buf[a:b] += seg[:b - a]


def xfade_env(n, fi=3.0, fo=3.0):
    e = np.ones(n, np.float32)
    a, b = min(n, int(fi * SR)), min(n, int(fo * SR))
    e[:a] = np.linspace(0, 1, a); e[n - b:] *= np.linspace(1, 0, b)
    return e[:, None]


def build_music():
    mus = np.zeros((N, 2), np.float32)
    for (t0, t1, mood) in SECT:
        a0 = max(0, t0 - 1.5); a1 = min(T, t1 + 1.5)
        if mood == "drum":
            seg = 0.55 * string_pad(a0, a1, bright=900) + 0.55 * drums(a0, a1, 66) + 0.4 * drone(a0, a1)
        elif mood == "strings":
            seg = 0.7 * string_pad(a0, a1, bright=1000) + 0.25 * drums(a0, a1, 60, density=0.5) + 0.3 * drone(a0, a1)
        elif mood == "qin":
            seg = 0.75 * qin(a0, a1) + 0.3 * string_pad(a0, a1, bright=700, chord_len=12) + 0.25 * drone(a0, a1)
        else:  # rise
            seg = 0.8 * string_pad(a0, a1, bright=1600) + 0.35 * drums(a0, a1, 60, density=0.5) + 0.3 * drone(a0, a1)
            n = len(seg); seg *= np.linspace(0.8, 1.25, n)[:, None]
        seg *= xfade_env(len(seg))
        place(mus, seg, a0)
    # final release
    fo = int(4 * SR); mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mus[:, 0] = hp(mus[:, 0], 35); mus[:, 1] = hp(mus[:, 1], 35)
    return mus


# ---------------------------------------------------------------- SFX
def gengu():
    """更鼓: two mid drum hits + wooden clapper."""
    out = np.zeros((int(1.0 * SR), 2), np.float32)
    d = taiko(0.7, 150, 110, 0.35) * 0.6
    n = int(0.12 * SR); t = np.arange(n) / SR
    wood = bp(rng.standard_normal(n), 1400, 2600, 3) * np.exp(-t * 55)
    wood = (wood / np.abs(wood).max() * 0.6).astype(np.float32)
    for at in (0.0, 0.34):
        a = int(at * SR)
        out[a:a + len(d), :] += d[:len(out) - a, None] if a + len(d) > len(out) else d[:, None]
        out[a + int(0.02 * SR):a + int(0.02 * SR) + n, :] += wood[:, None]
    return out


def strike():
    """heavy staff blow: whoosh + low thud + crack."""
    n = int(1.4 * SR); t = np.arange(n) / SR
    w = int(0.14 * SR)
    whoosh = bp(rng.standard_normal(w), 500, 3000, 2) * np.linspace(0, 1, w) ** 2 * 0.35
    thud = taiko(1.2, 70, 40, 0.9)
    crack = hp(rng.standard_normal(int(0.05 * SR)), 1800) * np.exp(-np.arange(int(0.05 * SR)) / SR * 90) * 0.8
    out = np.zeros(n + w, np.float32)
    out[:w] += whoosh
    out[w:w + len(thud)] += thud
    out[w:w + len(crack)] += crack
    out = out / np.abs(out).max()
    return np.stack([out, out], 1).astype(np.float32), w / SR


def boom():
    s = taiko(2.0, 50, 32, 0.6) * 0.7
    return np.stack([s, s], 1)


def build_sfx():
    sfx = np.zeros((N, 2), np.float32)
    place(sfx, gengu() * 0.8, 0.0)
    st, lead = strike()
    for s in TL["strikes"]:
        place(sfx, st * 0.95, max(0, s - lead))
    for ti in TL["titles"]:
        place(sfx, boom() * 0.5, ti["t0"] + 0.05)
    return sfx


if __name__ == "__main__":
    out = "/tmp/claude-0/w73/out"
    m = build_music(); m /= np.abs(m).max() + 1e-9
    sf.write(f"{out}/music.wav", m * 0.8, SR, subtype="FLOAT")
    s = build_sfx()
    sf.write(f"{out}/sfx.wav", s, SR, subtype="FLOAT")
    print("music", m.shape[0] / SR, "s; sections", [(round(a), round(b), c) for a, b, c in SECT])
