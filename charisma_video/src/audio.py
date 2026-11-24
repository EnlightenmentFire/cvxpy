# -*- coding: utf-8 -*-
"""Audio: voice processing, synthesized score (strings/brass/qin/oud/organ/piano), SFX, mixing.
Everything is synthesized here (no third-party samples)."""
import os, subprocess, math, json
import numpy as np
import soundfile as sf

SR = 48000

def db(x):
    return 20 * np.log10(max(x, 1e-9))

def undb(d):
    return 10 ** (d / 20)

# ------------------------------------------------------------------ voice
def ffmpeg_proc(inp, out, tempo=1.0, hp=50):
    filt = [f"highpass=f={hp}"]
    if abs(tempo - 1.0) > 1e-3:
        filt.append(f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inp, "-af", ",".join(filt), "-ar", str(SR), "-ac", "1", out],
                   check=True)

def compress_pauses(y, sr=SR, thresh_db=-42, max_pause=0.38, keep=0.32, edge=0.06):
    """Trim leading/trailing silence; shrink internal pauses longer than max_pause to `keep`."""
    hop = int(0.01 * sr)
    n = len(y) // hop
    rms = np.array([np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    ref = np.percentile(rms, 95)
    voiced = 20 * np.log10(rms / ref + 1e-12) > thresh_db
    if not voiced.any():
        return y
    first, last = np.argmax(voiced), n - 1 - np.argmax(voiced[::-1])
    start = max(0, first * hop - int(edge * sr)); end = min(len(y), (last + 1) * hop + int(edge * 1.5 * sr))
    segs, i = [], first
    out = [y[start:first * hop]]
    cur = first
    while cur <= last:
        if voiced[cur]:
            j = cur
            while j <= last and voiced[j]:
                j += 1
            out.append(y[cur * hop:j * hop]); cur = j
        else:
            j = cur
            while j <= last and not voiced[j]:
                j += 1
            L = (j - cur) * hop
            if L > max_pause * sr:
                k = int(keep * sr)
                seg = y[cur * hop:j * hop]
                fade = int(0.02 * sr)
                a = seg[:k // 2].copy(); b = seg[-(k - k // 2):].copy()
                out.append(np.concatenate([a, b]))
            else:
                out.append(y[cur * hop:j * hop])
            cur = j
    out.append(y[(last + 1) * hop:end])
    return np.concatenate(out)

def speech_rms(y, sr=SR):
    hop = int(0.02 * sr)
    n = len(y) // hop
    r = np.array([np.sqrt(np.mean(y[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    r = r[r > np.percentile(r, 60) * 0.5] if len(r) else r
    return float(np.sqrt(np.mean(r ** 2))) if len(r) else 1e-6

def normalize_voice(y, target_db=-18.0):
    g = undb(target_db) / speech_rms(y)
    y = y * g
    peak = np.max(np.abs(y))
    if peak > 0.89:  # soft limit
        y = np.tanh(y / 0.89) * 0.89
    return y

def load(path):
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(1)
    assert sr == SR, (path, sr)
    return y

# ------------------------------------------------------------------ synthesis helpers
def env_adsr(n, a, d, s, r, sr=SR):
    e = np.ones(n) * s
    A, D, R = int(a * sr), int(d * sr), int(r * sr)
    A = min(A, n); e[:A] = np.linspace(0, 1, A, endpoint=False) if A else e[:A]
    if D > 0 and A + D < n:
        e[A:A + D] = np.linspace(1, s, D)
    if R > 0:
        R = min(R, n)
        e[n - R:] *= np.linspace(1, 0, R)
    return e

def lowpass(x, fc, sr=SR):
    # one-pole x2
    a = math.exp(-2 * math.pi * fc / sr)
    from scipy.signal import lfilter
    y = lfilter([1 - a], [1, -a], x)
    return lfilter([1 - a], [1, -a], y)

def note_freq(name):
    names = {"C": -9, "C#": -8, "Db": -8, "D": -7, "D#": -6, "Eb": -6, "E": -5, "F": -4, "F#": -3, "Gb": -3,
             "G": -2, "G#": -1, "Ab": -1, "A": 0, "A#": 1, "Bb": 1, "B": 2}
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + (o - 4) * 12) / 12)

def strings(freq, dur, amp=0.2, attack=1.2, release=1.5, bright=2200, voices=3, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for v in range(voices):
        det = 1 + (v - (voices - 1) / 2) * 0.0035
        vib = 1 + 0.003 * np.sin(2 * np.pi * (5.0 + 0.3 * v) * t + rng.uniform(0, 6)) * np.clip(t / 1.5, 0, 1)
        ph = 2 * np.pi * np.cumsum(freq * det * vib) / SR + rng.uniform(0, 6)
        for h in range(1, 14):
            if freq * h > bright * 2.2:
                break
            y += np.sin(h * ph) / h * (1 / (1 + (freq * h / bright) ** 2))
    y /= voices
    bow = 1 + 0.08 * lowpass(rng.normal(0, 1, n), 3)
    return y * bow * env_adsr(n, attack, 0.2, 0.9, release) * amp

def brass(freq, dur, amp=0.15, attack=0.25, release=0.8, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * freq * t
    bright = 600 + 1400 * np.clip(t / attack, 0, 1) * np.exp(-t / (dur + 0.5)) + 300
    y = np.zeros(n)
    for h in range(1, 16):
        y += np.sin(h * ph) * (1 / (1 + (freq * h / bright) ** 2)) / (h ** 0.6)
    return y * env_adsr(n, attack, 0.3, 0.75, release) * amp * 0.5

def pluck(freq, dur, amp=0.25, decay=1.2, bright=3000, inharm=0.0, body=None, seed=0):
    """plucked string (qin / oud / piano-ish) via additive partials with per-partial decay"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for h in range(1, 18):
        f = freq * h * math.sqrt(1 + inharm * h * h)
        if f > 12000:
            break
        a = 1 / h * (1 / (1 + (f / bright) ** 2))
        y += a * np.sin(2 * np.pi * f * t) * np.exp(-t * (1 / decay) * (1 + 0.35 * h))
    att = np.clip(t / 0.004, 0, 1)
    y *= att
    rel = int(0.05 * SR)
    y[-rel:] *= np.linspace(1, 0, rel)
    return y * amp

def piano(freq, dur, amp=0.22):
    return pluck(freq, dur, amp, decay=1.8, bright=2600, inharm=0.0004)

def qin(freq, dur, amp=0.28):
    y = pluck(freq, dur, amp, decay=2.2, bright=1600, inharm=0.0002)
    # slide (吟猱) – slight pitch bend via resampling of tail is complex; add soft vibrato by AM
    t = np.arange(len(y)) / SR
    return y * (1 + 0.05 * np.sin(2 * np.pi * 5 * t) * np.clip(t - 0.3, 0, 1))

def oud(freq, dur, amp=0.25):
    return pluck(freq, dur, amp, decay=0.9, bright=2200, inharm=0.0001) + pluck(freq * 1.003, dur, amp * 0.5, decay=0.8, bright=2000)

def organ(freq, dur, amp=0.12, attack=0.4, release=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for mult, a in ((0.5, 0.5), (1, 1.0), (2, 0.6), (3, 0.25), (4, 0.3), (6, 0.1), (8, 0.12)):
        y += a * np.sin(2 * np.pi * freq * mult * t)
    return y * env_adsr(n, attack, 0.1, 1.0, release) * amp * 0.4

def xun(freq, dur, amp=0.12):
    """埙-like breathy vessel flute"""
    n = int(dur * SR); t = np.arange(n) / SR
    rng = np.random.default_rng(int(freq))
    vib = 1 + 0.006 * np.sin(2 * np.pi * 4.5 * t) * np.clip(t - 0.3, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = lowpass(rng.normal(0, 1, n), 1800) * 0.25
    return (y + breath) * env_adsr(n, 0.35, 0.2, 0.85, 0.6) * amp

def reverb(x, seconds=2.4, wet=0.28, seed=1, pre=0.02):
    from scipy.signal import fftconvolve
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 6.9 / seconds)
    ir = lowpass(ir, 5000)
    ir[: int(pre * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    y = fftconvolve(x, ir)[: len(x) + n]
    out = np.zeros(len(y)); out[: len(x)] = x
    return out * (1 - wet) + y * wet

# ------------------------------------------------------------------ SFX
def room_tone(dur, amp=0.004, seed=3):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    pink = lowpass(rng.normal(0, 1, n), 400) * 6 + lowpass(rng.normal(0, 1, n), 2500)
    hum = 0.15 * np.sin(2 * np.pi * 60 * np.arange(n) / SR)
    return (pink + hum) * amp

def chair_scrape(amp=0.25, seed=5):
    rng = np.random.default_rng(seed)
    dur = 0.55; n = int(dur * SR); t = np.arange(n) / SR
    f = 180 + 140 * np.sin(np.pi * t / dur) + 30 * rng.normal(0, 1, n).cumsum() / n
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sign(np.sin(ph)) * 0.3 + np.sin(2 * ph) * 0.2
    grit = rng.normal(0, 1, n) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
    y = lowpass(tone + grit, 1800) * np.sin(np.pi * t / dur) ** 0.7
    return y * amp

def low_boom(amp=0.5, f0=55, dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.6 * np.exp(-t * 8))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    y += 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
    return y * np.clip(t / 0.01, 0, 1) * amp

def tiles(amp=0.35, seed=7, count=7):
    rng = np.random.default_rng(seed)
    dur = 1.6; n = int(dur * SR); y = np.zeros(n)
    for k in range(count):
        st = int(rng.uniform(0, 1.2) * SR); L = int(0.12 * SR)
        t = np.arange(L) / SR
        f = rng.uniform(900, 2200)
        hit = (np.sin(2 * np.pi * f * t) * 0.4 + rng.normal(0, 1, L) * 0.6) * np.exp(-t * 40)
        y[st:st + L] += hit[: max(0, min(L, n - st))] * rng.uniform(0.4, 1)
    return lowpass(y, 5000) * amp

def puff(amp=0.12, seed=9):
    rng = np.random.default_rng(seed)
    dur = 0.6; n = int(dur * SR); t = np.arange(n) / SR
    y = lowpass(rng.normal(0, 1, n), 900) * np.exp(-((t - 0.12) / 0.12) ** 2)
    return y * amp * 3

# ------------------------------------------------------------------ mixing
def place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    L = min(len(x), len(buf) - i)
    buf[i:i + L] += x[:L] * gain

def duck(music, voice, depth_db=-11, attack=0.06, release=0.45):
    hop = int(0.01 * SR)
    n = len(voice) // hop + 1
    env = np.zeros(n)
    for i in range(n):
        seg = voice[i * hop:(i + 1) * hop]
        env[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    active = (20 * np.log10(env + 1e-9) > -40).astype(float)
    g = np.zeros(n); cur = 0.0
    ka = 1 - math.exp(-0.01 / attack); kr = 1 - math.exp(-0.01 / release)
    for i in range(n):
        tgt = active[i]
        cur += (tgt - cur) * (ka if tgt > cur else kr)
        g[i] = cur
    gain = undb(depth_db * g)
    gain = np.repeat(gain, hop)[: len(music)]
    if len(gain) < len(music):
        gain = np.concatenate([gain, np.ones(len(music) - len(gain)) * gain[-1]])
    return music * gain
