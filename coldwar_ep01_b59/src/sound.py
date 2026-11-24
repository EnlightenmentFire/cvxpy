"""Procedural score & sound design (all synthesized here — no third-party samples)."""
import numpy as np
from scipy import signal

SR = 48000


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, fc, order=4):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), f2 / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def env_adsr(n, a, d, s, r, sustain_level=0.7):
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    S = max(0, n - A - D - R)
    e = np.concatenate([np.linspace(0, 1, A, endpoint=False), np.linspace(1, sustain_level, D, endpoint=False),
                        np.full(S, sustain_level), np.linspace(sustain_level, 0, R)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


_ir_cache = {}


def reverb(x, decay=2.8, mix=0.3, seed=0, predelay=0.02):
    key = (decay, seed)
    if key not in _ir_cache:
        rng = np.random.default_rng(seed)
        n = int(decay * SR)
        tt = np.arange(n) / SR
        ir = rng.standard_normal(n) * np.exp(-tt * 6.9 / decay)
        ir = lowpass(ir, 5000)
        ir = np.concatenate([np.zeros(int(predelay * SR)), ir])
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        _ir_cache[key] = ir
    wet = signal.fftconvolve(x, _ir_cache[key])[: len(x)]
    return x * (1 - mix) + wet * mix


def drone(dur, f0=55.0, seed=1, bright=600.0):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    out = np.zeros_like(t)
    for mult, amp in [(1.0, 1.0), (1.498, 0.45), (2.0, 0.35), (3.0, 0.12)]:
        for det in (-0.6, 0.6):
            f = f0 * mult + det * mult * 0.15
            ph = rng.uniform(0, 2 * np.pi)
            lfo = 0.75 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.03, 0.09) * t + ph)
            out += amp * lfo * np.sin(2 * np.pi * f * t + ph)
    noise = lowpass(rng.standard_normal(len(t)), 120) * 0.6
    out = lowpass(out, bright) + noise
    return out / (np.max(np.abs(out)) + 1e-9)


def string_pad(dur, notes_hz, seed=2, attack=3.0, release=3.0, bright=1800.0):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    out = np.zeros_like(t)
    for f in notes_hz:
        for voice in range(3):
            det = 1 + rng.uniform(-0.004, 0.004)
            vib = 1 + 0.003 * np.sin(2 * np.pi * (4.8 + voice * 0.3) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * np.cumsum(f * det * vib) / SR
            saw = np.zeros_like(t)
            for k in range(1, 9):
                saw += np.sin(k * ph) / k
            out += saw
    out = lowpass(out, bright)
    out *= env_adsr(len(t), attack, 0.5, 0, release, 1.0)
    return out / (np.max(np.abs(out)) + 1e-9)


def sonar_ping(freq=1150.0, dur=3.0):
    t = t_axis(dur)
    tone = np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.2) * np.clip(t / 0.004, 0, 1)
    tone += 0.3 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t * 4)
    return reverb(tone, 3.5, 0.55, seed=5)


def impact(dur=2.5, seed=3, depth=1.0):
    """Low-frequency underwater thump (practice depth charge heard from inside the hull)."""
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    f = 30 + 45 * np.exp(-t * 8)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    crack = bandpass(rng.standard_normal(len(t)), 80, 900) * np.exp(-t * 18) * 0.8
    metal = bandpass(rng.standard_normal(len(t)), 300, 1400) * np.exp(-t * 6) * 0.35
    x = body * 1.2 + crack + metal * depth
    return reverb(x, 2.2, 0.35, seed=7)


def metal_groan(dur=4.0, seed=4):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    x = bandpass(rng.standard_normal(len(t)), 150, 600) * env_adsr(len(t), 0.6, 0.5, 0, 2.0, 0.6)
    ring = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 1.5) * a for f, a in [(212, 0.3), (347, 0.2), (529, 0.12)])
    return reverb(x * 0.5 + ring, 3.0, 0.5, seed=9)


def place(buf, x, at):
    i = int(at * SR)
    if i >= len(buf):
        return buf
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n]
    return buf


def duck(music, voice, depth=0.45, att=0.05, rel=0.4):
    """Sidechain: lower music under the voice."""
    env = np.abs(voice)
    win = int(0.03 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    env = env / (np.max(env) + 1e-9)
    g = 1 - depth * np.clip(env * 4, 0, 1)
    # smooth gain
    b, a = signal.butter(1, 3 / (SR / 2), "low")
    g = signal.filtfilt(b, a, g)
    return music * g
