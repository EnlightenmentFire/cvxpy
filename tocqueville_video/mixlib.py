"""Mixing helpers: voice timeline, ducking, music fitting, loudness."""
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

SR = 48000


def load(path, stereo=False):
    x, sr = sf.read(path, always_2d=True)
    x = x.astype(np.float32)
    if sr != SR:
        g = np.gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    if stereo:
        if x.shape[1] == 1:
            x = np.repeat(x, 2, 1)
        return x
    return x.mean(1)


def place(buf, x, t, gain_db=0.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]; i = 0
    L = min(len(x), len(buf) - i)
    g = 10 ** (gain_db / 20)
    if buf.ndim == 2 and x.ndim == 1:
        buf[i:i + L] += g * x[:L, None]
    else:
        buf[i:i + L] += g * x[:L]


def envelope(x, win=0.03, attack=0.06, release=0.45):
    n = int(win * SR)
    m = len(x) // n
    r = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1))
    act = (20 * np.log10(r + 1e-9) > -40).astype(np.float32)
    out = np.zeros_like(act)
    a_c = np.exp(-win / attack); r_c = np.exp(-win / release)
    v = 0.0
    for i, a in enumerate(act):
        c = a_c if a > v else r_c
        v = c * v + (1 - c) * a
        out[i] = v
    e = np.repeat(out, n)
    e = np.pad(e, (0, len(x) - len(e)), mode="edge")
    return e


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


def fit_music(m, dur, fade_in=2.0, fade_out=3.0):
    """trim/loop stereo music to dur seconds with fades"""
    n = int(dur * SR)
    if len(m) < n:
        reps = int(np.ceil(n / len(m)))
        m = np.concatenate([m] * reps, 0)
    m = m[:n].copy()
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi: m[:fi] *= np.linspace(0, 1, fi)[:, None]
    if fo: m[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return m


def limiter(x, ceiling=0.97):
    peak = np.abs(x).max()
    if peak > ceiling:
        # soft clip the excess
        x = np.tanh(x / ceiling) * ceiling
    return x
