"""Synthesized sound effects (numpy, 48 kHz mono float32). All original, no samples."""
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

SR = 48000


def _rng(seed):
    return np.random.default_rng(seed)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def smooth_noise(n, rate, rng):
    """slow random envelope with `rate` changes per second"""
    k = max(2, int(n / SR * rate) + 2)
    pts = rng.random(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


def norm(x, db):
    r = np.sqrt((x ** 2).mean()) + 1e-12
    return (x / r * 10 ** (db / 20)).astype(np.float32)


def fade(x, a=0.3, b=0.3):
    na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)
    if nb: x[-nb:] *= np.linspace(1, 0, nb)
    return x


def wind(dur, seed=1, level=-38, bright=600):
    rng = _rng(seed); n = int(dur * SR)
    x = rng.normal(size=n)
    x = lp(x, bright, 2) * (0.4 + 0.6 * smooth_noise(n, 0.4, rng))
    x = x + 0.3 * bp(rng.normal(size=n), 900, 1600) * smooth_noise(n, 0.7, rng) ** 3
    return fade(norm(x, level), 1.5, 1.5)


def waves(dur, seed=2, level=-30):
    rng = _rng(seed); n = int(dur * SR)
    x = lp(rng.normal(size=n), 1800, 2)
    t = np.arange(n) / SR
    env = np.zeros(n)
    tt = 0.0
    while tt < dur:
        period = rng.uniform(4.5, 7.5)
        c = tt + period * 0.4
        env += np.exp(-((t - c) / (period * 0.22)) ** 2) * rng.uniform(0.6, 1.0)
        tt += period
    x = x * (0.15 + env)
    x = x + 0.15 * hp(rng.normal(size=n), 3000) * env ** 2
    return fade(norm(x, level), 2, 2)


def creak(dur=1.2, seed=3, level=-24):
    rng = _rng(seed); n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = 90 + 40 * np.sin(2 * np.pi * 0.7 * t) + 20 * rng.normal(size=n).cumsum() / np.sqrt(n)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    pulses = (np.sin(ph) > 0.97).astype(float)
    x = bp(pulses + 0.05 * rng.normal(size=n), 300, 2500)
    return fade(norm(x * smooth_noise(n, 6, rng), level), 0.05, 0.3)


def crash(seed=4, level=-16):
    rng = _rng(seed); dur = 2.6; n = int(dur * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (55 - 15 * t) * t) * np.exp(-t * 5)
    noise = lp(rng.normal(size=n), 2500) * np.exp(-t * 3.0)
    cr = np.zeros(n)
    for _ in range(160):
        i = int(rng.uniform(0, 1.6) ** 1.6 * SR)
        L = int(rng.uniform(0.002, 0.012) * SR)
        if i + L < n:
            cr[i:i + L] += rng.normal(size=L) * rng.uniform(0.2, 1) * np.exp(-np.arange(L) / (L / 3))
    cr = bp(cr, 1200, 7000)
    leaves = bp(rng.normal(size=n), 2000, 8000) * np.exp(-((t - 0.25) / 0.6) ** 2) * 0.5
    x = 1.6 * thump + 0.6 * noise + 0.8 * cr + leaves
    return fade(norm(x, level), 0.005, 0.5)


def saw(dur=3.0, seed=5, level=-24, rate=2.2):
    rng = _rng(seed); n = int(dur * SR)
    t = np.arange(n) / SR
    stroke = np.abs(np.sin(np.pi * rate * t)) ** 0.6
    teeth = (np.sin(2 * np.pi * (rate * 38) * t + 3 * np.sin(np.pi * rate * t)) > 0.6).astype(float)
    x = bp(rng.normal(size=n) * (0.4 + teeth), 1500, 6000) * stroke
    x = x + 0.3 * bp(rng.normal(size=n), 300, 900) * stroke
    return fade(norm(x, level), 0.1, 0.3)


def murmur(dur, seed=6, level=-34, voices=7):
    """indistinct crowd talk: formant-filtered pulse trains with syllabic envelopes"""
    rng = _rng(seed); n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for v in range(voices):
        f0 = rng.uniform(95, 180) * (1 + 0.08 * np.sin(2 * np.pi * rng.uniform(0.2, 0.5) * t))
        ph = 2 * np.pi * np.cumsum(f0) / SR
        src = np.sign(np.sin(ph)) * 0.3 + 0.05 * rng.normal(size=n)
        syl = smooth_noise(n, rng.uniform(4, 6), rng) ** 2
        phrase = (smooth_noise(n, 0.5, rng) > 0.45).astype(float)
        phrase = lp(phrase, 3, 1)
        y = bp(src, 300, 900) + 0.6 * bp(src, 1000, 2400)
        out += y * syl * phrase
    out = lp(out, 2200, 2)
    return fade(norm(out, level), 0.6, 0.8)


def birds(dur, seed=7, level=-40, n_chirps=10):
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(n_chirps):
        st = int(rng.uniform(0, dur - 0.5) * SR)
        for k in range(int(rng.integers(2, 5))):
            L = int(rng.uniform(0.05, 0.12) * SR)
            tt = np.arange(L) / SR
            f = rng.uniform(2800, 4200) + rng.uniform(-1500, 1500) * tt / tt[-1]
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
            s = st + k * int(rng.uniform(0.12, 0.2) * SR)
            if s + L < n:
                out[s:s + L] += y * rng.uniform(0.4, 1)
    return norm(out, level)


def paper_flutter(dur=2.0, seed=8, level=-30, density=30):
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(int(density * dur)):
        s = int(rng.uniform(0, dur - 0.1) * SR); L = int(rng.uniform(0.02, 0.08) * SR)
        y = bp(rng.normal(size=L), 1500, 7000) * np.hanning(L)
        out[s:s + L] += y * rng.uniform(0.3, 1)
    return fade(norm(out, level), 0.2, 0.3)


def ice(dur, seed=9, level=-34, n_hits=14):
    """floating ice knocking: short inharmonic resonances"""
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(n_hits):
        s = int(rng.uniform(0, dur - 0.5) * SR); L = int(0.45 * SR)
        tt = np.arange(L) / SR
        y = np.zeros(L)
        base = rng.uniform(600, 1400)
        for r, a in ((1, 1), (2.76, 0.5), (5.4, 0.3), (8.9, 0.15)):
            y += a * np.sin(2 * np.pi * base * r * tt) * np.exp(-tt * rng.uniform(18, 40) * r ** 0.5)
        y += 0.3 * bp(rng.normal(size=L), 2000, 6000) * np.exp(-tt * 60)
        out[s:s + L] += y * rng.uniform(0.3, 1)
    return norm(out, level)


def howl(dur=5.5, seed=10, level=-20, pitch=1.0):
    """long dog howl: harmonic voice with gliding pitch, vowel 'oo' formants, breath."""
    rng = _rng(seed); n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    contour = 430 + 230 * np.sin(np.pi * np.clip(u * 1.15, 0, 1)) ** 0.7 - 120 * np.clip(u - 0.75, 0, 1) * 4
    contour = contour * pitch * (1 + 0.012 * np.sin(2 * np.pi * 5.2 * t) + 0.004 * rng.normal(size=n).cumsum() / np.sqrt(n) * 20)
    ph = 2 * np.pi * np.cumsum(contour) / SR
    y = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.55), (3, 0.25), (4, 0.12), (5, 0.06)):
        y += a * np.sin(k * ph)
    env = np.clip(u / 0.12, 0, 1) ** 1.5 * np.clip((1 - u) / 0.25, 0, 1) ** 1.2
    y = y * env
    # formants (oo -> ow)
    y = 0.8 * bp(y, 350, 1200) + 0.4 * bp(y, 1200, 2600) + 0.1 * y
    br = bp(rng.normal(size=n), 800, 3500) * env * 0.08
    return fade(norm(y + br, level), 0.05, 0.4)


def splash(seed=11, level=-28):
    rng = _rng(seed); dur = 1.2; n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(rng.normal(size=n), 400, 6000) * np.exp(-t * 6) + 0.4 * lp(rng.normal(size=n), 400) * np.exp(-t * 4)
    return fade(norm(x, level), 0.003, 0.3)


def hooves(dur, seed=12, level=-32, rate=1.6):
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n)
    tt = 0.0
    while tt < dur - 0.2:
        for off in (0.0, 0.11):
            s = int((tt + off) * SR); L = int(0.06 * SR)
            if s + L < n:
                k = np.arange(L) / SR
                out[s:s + L] += (np.sin(2 * np.pi * rng.uniform(180, 260) * k) * np.exp(-k * 70) + 0.3 * rng.normal(size=L) * np.exp(-k * 120))
        tt += 1 / rate + rng.normal(0, 0.02)
    return fade(norm(lp(out, 2500), level), 0.3, 0.3)


def page_turn(seed=13, level=-30):
    rng = _rng(seed); dur = 0.7; n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(rng.normal(size=n), 1000, 8000) * (np.sin(np.pi * t / dur) ** 2) * (0.5 + 0.5 * smooth_noise(n, 30, rng))
    return norm(x, level)


def quill(dur=1.5, seed=14, level=-36):
    rng = _rng(seed); n = int(dur * SR)
    x = bp(rng.normal(size=n), 3000, 9000) * (smooth_noise(n, 12, rng) ** 3)
    return fade(norm(x, level), 0.1, 0.2)


def hall_room(dur, seed=15, level=-40):
    rng = _rng(seed); n = int(dur * SR)
    return fade(norm(lp(rng.normal(size=n), 400) * (0.7 + 0.3 * smooth_noise(n, 1, rng)), level), 1, 1)


def rustle(dur=1.2, seed=16, level=-32):
    """clothes rustle (hands raised)"""
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(40):
        s = int(rng.uniform(0, dur - 0.2) * SR); L = int(rng.uniform(0.05, 0.2) * SR)
        out[s:s + L] += bp(rng.normal(size=L), 800, 5000) * np.hanning(L) * rng.uniform(0.2, 1)
    return fade(norm(out, level), 0.1, 0.3)


def drum_far(dur, seed=17, level=-34, rate=1.3):
    rng = _rng(seed); n = int(dur * SR)
    out = np.zeros(n); tt = 0.3
    while tt < dur - 0.4:
        s = int(tt * SR); L = int(0.4 * SR); k = np.arange(L) / SR
        if s + L < n:
            out[s:s + L] += np.sin(2 * np.pi * 85 * k) * np.exp(-k * 9) * rng.uniform(0.6, 1)
        tt += 1 / rate
    return fade(norm(lp(out, 600), level), 0.5, 0.5)
