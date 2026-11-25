"""乐器与音效合成（numpy），48 kHz。全部自己生成，无外部采样。"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
RNG = np.random.default_rng(1234)


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.3, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr)
    sus = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False),
                        np.full(sus, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n].astype(np.float32)


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 100), "lowpass", fs=SR, output="sos"), x).astype(np.float32)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "highpass", fs=SR, output="sos"), x).astype(np.float32)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], "bandpass", fs=SR, output="sos"), x).astype(np.float32)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, n, nh=24, phase=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, nh + 1):
        if f * k > 9000:
            break
        out += np.sin(2 * np.pi * f * k * t + phase * k) / k
    return out


def string_note(f, dur, bright=1.0, vib=0.004):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for det in (-0.004, 0.0, 0.0045):
        ff = f * (1 + det) * (1 + vib * np.sin(2 * np.pi * 5.2 * t + RNG.random() * 6))
        ph = 2 * np.pi * np.cumsum(ff) / SR
        for k in range(1, 18):
            if f * k > 7000:
                break
            out += np.sin(ph * k) / k ** (1.1 / bright)
    out = lp(out, 900 + 2200 * bright)
    return out / 3


def horn_note(f, dur, a=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ff = f * (1 + 0.003 * np.sin(2 * np.pi * 4.8 * t))
    ph = 2 * np.pi * np.cumsum(ff) / SR
    out = sum(np.sin(ph * k) * (1 / k ** 0.9) for k in range(1, 14))
    out = lp(out.astype(np.float32), 1400)
    return out * env_adsr(n, a, 0.2, 0.85, min(0.8, dur * 0.4))


def taiko(size=1.0, dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = (95 / size) * (1 + 0.8 * np.exp(-t * 30))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (3.2 * size ** -0.5))
    skin = lp(RNG.standard_normal(n).astype(np.float32), 900) * np.exp(-t * 28) * 0.6
    sub = np.sin(2 * np.pi * 42 / size * t) * np.exp(-t * 2.5) * 0.5
    return (body + skin + sub).astype(np.float32) * 0.9


def rim(dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return (bp(RNG.standard_normal(n).astype(np.float32), 1800, 5000) * np.exp(-t * 45) * 0.5 +
            np.sin(2 * np.pi * 420 * t) * np.exp(-t * 30) * 0.3).astype(np.float32)


def guqin(f, dur=3.5, slide=0.0):
    """Karplus-Strong 拨弦，带一点滑音。"""
    n = int(dur * SR)
    L = SR / f
    buf_len = int(L) + 2
    noise = (RNG.random(buf_len) * 2 - 1).astype(np.float32)
    noise = lp(noise, 2500)
    out = np.zeros(n, np.float32)
    buf = np.zeros(buf_len + n, np.float32)
    buf[:buf_len] = noise
    # 简化：用固定周期，滑音由重采样实现
    p = int(L)
    for i in range(buf_len, buf_len + n):
        buf[i] = 0.4985 * (buf[i - p] + buf[i - p - 1])
    out = buf[buf_len:buf_len + n]
    if slide:
        tt = np.arange(n) / SR
        rate = 1 + slide * (1 - np.exp(-tt * 3))
        idx = np.cumsum(rate)
        idx = idx[idx < n - 1]
        out = np.interp(idx, np.arange(n), out).astype(np.float32)
        out = np.pad(out, (0, n - len(out)))
    body = lp(out, 1800) + 0.3 * hp(out, 2000)
    return body * np.exp(-np.arange(n) / SR * 0.6)


def reverb(x, secs=2.6, mix=0.3, seed=0, pre=0.02):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = r.standard_normal(n).astype(np.float32) * np.exp(-t * 6.9 / secs)
        ir = lp(ir, 5000)
        ir[:int(pre * SR)] = 0
        ir /= np.sqrt((ir ** 2).sum())
        out.append(fftconvolve(x, ir)[:len(x)].astype(np.float32))
    wet = np.stack(out, 1)
    dry = np.stack([x, x], 1)
    return dry * (1 - mix) + wet * mix


# ------------------------------------------------------------------ 音效
def sword_ring(dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    parts = [(1180, 1.0, 1.3), (3260, 0.5, 2.2), (5410, 0.35, 3.0), (2470, 0.4, 1.8), (8130, 0.2, 4.5)]
    out = sum(a * np.sin(2 * np.pi * f * t * (1 + 0.0008 * np.sin(2 * np.pi * 6 * t))) * np.exp(-t * d) for f, a, d in parts)
    scrape = bp(RNG.standard_normal(n).astype(np.float32), 2500, 9000) * np.exp(-t * 9) * 0.5 * (t < 0.6)
    return (out * 0.3 + scrape).astype(np.float32)


def whoosh(dur=0.45, f0=600, f1=4000):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = RNG.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32)
    seg = 8
    for i in range(seg):
        a, b = i * n // seg, (i + 1) * n // seg
        fc = f0 + (f1 - f0) * (i / seg)
        out[a:b] = bp(noise, fc * 0.6, min(fc * 1.6, 20000))[a:b]
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return out * e * 0.8


def cloth_tear(dur=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    clicks = (RNG.random(n) < 0.02).astype(np.float32) * RNG.standard_normal(n).astype(np.float32)
    tear = bp(clicks + 0.25 * RNG.standard_normal(n).astype(np.float32), 900, 6000)
    return tear * np.exp(-t * 7) * 1.2


def heartbeat():
    def thump(f=55):
        n = int(0.25 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * f * t * (1 + np.exp(-t * 40))) * np.exp(-t * 18)
    out = np.zeros(int(0.7 * SR), np.float32)
    a = thump(); out[:len(a)] += a
    b = thump(48) * 0.7; o = int(0.22 * SR); out[o:o + len(b)] += b
    return out


def neigh(dur=1.3):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 520 * np.exp(-t * 0.7) * (1 + 0.12 * np.sin(2 * np.pi * 17 * t)) + 120
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = sum(np.sin(ph * k) / k for k in range(1, 20)).astype(np.float32)
    src += 0.3 * RNG.standard_normal(n).astype(np.float32)
    out = bp(src, 700, 1300) + 0.6 * bp(src, 2200, 3200) + 0.3 * bp(src, 350, 600)
    e = np.clip(t / 0.08, 0, 1) * np.exp(-np.clip(t - 0.6, 0, None) * 4)
    return out * e * 0.5


def hooves(dur=1.5, rate=7):
    n = int(dur * SR); out = np.zeros(n, np.float32)
    k = 0
    tt = 0.0
    while tt < dur - 0.1:
        n0 = int(tt * SR); m = int(0.08 * SR); t = np.arange(m) / SR
        c = (bp(RNG.standard_normal(m).astype(np.float32), 300, 2500) * np.exp(-t * 60) +
             np.sin(2 * np.pi * 180 * t) * np.exp(-t * 50) * 0.5)
        out[n0:n0 + m] += c[:max(0, min(m, n - n0))] * (0.7 + 0.3 * RNG.random())
        tt += (1 / rate) * (0.6 if k % 2 else 1.4)
        k += 1
    return out


def river(dur):
    n = int(dur * SR)
    x = RNG.standard_normal(n).astype(np.float32)
    x = lp(np.cumsum(x) * 0.02 - lp(np.cumsum(x) * 0.02, 20), 700) + 0.15 * bp(x, 1500, 5000)
    mod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * np.arange(n) / SR)
    return x * mod / (np.abs(x).max() + 1e-6) * 0.6


def fire(dur):
    n = int(dur * SR)
    base = lp(RNG.standard_normal(n).astype(np.float32), 500) * 0.3
    cr = (RNG.random(n) < 0.0009).astype(np.float32) * RNG.standard_normal(n).astype(np.float32) * 3
    cr = bp(cr, 1500, 8000)
    return base + cr


def wind(dur):
    n = int(dur * SR)
    x = RNG.standard_normal(n).astype(np.float32)
    m = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * np.arange(n) / SR) * np.sin(2 * np.pi * 0.023 * np.arange(n) / SR + 1)
    return bp(x, 200, 900) * m * 0.6


def scrape(dur=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    return bp(RNG.standard_normal(n).astype(np.float32), 800, 3500) * np.sin(np.pi * t / dur) ** 2 * 0.4


def stamp():
    n = int(0.4 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 90 * t) * np.exp(-t * 25) + lp(RNG.standard_normal(n).astype(np.float32), 1200) * np.exp(-t * 40) * 0.5)


def boom(dur=4.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 50 * (1 + 0.6 * np.exp(-t * 6))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.0) +
            lp(RNG.standard_normal(n).astype(np.float32), 200) * np.exp(-t * 2.0) * 0.6).astype(np.float32)
