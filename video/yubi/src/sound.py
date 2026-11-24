# -*- coding: utf-8 -*-
"""音色库：全部用 numpy 合成（无外部采样）。鼓、弦乐长音、低音弦乐、拨弦、风声、箭声、纸声、混响。"""
import numpy as np

SR = 48000
rng = np.random.default_rng(546)


def fft_filter(x, lo=None, hi=None, order=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * g, len(x))


def add(buf, x, t, gain=1.0, pan=0.0):
    N = len(buf); i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]; l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.414; buf[i:i + len(x), 1] += x * gain * r * 1.414


# ---------- 鼓 ----------
def taiko(f0=58, dur=1.6, hard=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.4 * np.exp(-t / 0.035)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.45) + 0.35 * np.sin(2.02 * ph) * np.exp(-t / 0.16)
    click = fft_filter(rng.normal(size=n) * np.exp(-t / 0.012), 300, 3500, 2) * 0.45 * hard
    return np.tanh((body + click) * 1.6) * 0.8


def tom(f0=110, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.8 * np.exp(-t / 0.02)); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.13) + fft_filter(rng.normal(size=n) * np.exp(-t / 0.008), 500, 4000, 2) * 0.3) * 0.7


def rim(dur=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return fft_filter(rng.normal(size=n) * np.exp(-t / 0.02), 1200, 6000, 2) * 0.5 + np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.03) * 0.3


# ---------- 弦乐 ----------
def _saw(freq, t, vib=0.0, vr=5.2):
    ph = 2 * np.pi * np.cumsum(freq * (1 + vib * np.sin(2 * np.pi * vr * t + rng.uniform(0, 6.28)))) / SR
    x = np.zeros_like(t)
    for h in range(1, 18):
        if freq * h > 7000: break
        x += np.sin(h * ph) / h
    return x


def strings(freqs, dur, bright=900, att=0.6, rel=0.9, vib=0.004):
    """弓弦长音：多声部、轻微失谐与揉弦，低通 + 慢起慢收。"""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0.0, 0.005):
            x += _saw(f * (1 + det), t, vib)
    x = fft_filter(x, 60, bright, 2)
    env = np.minimum(t / att, 1) * np.minimum(np.maximum(dur - t, 0) / rel, 1)
    bow = 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
    return x * env * bow * 0.05


def cello_note(freq, dur, accent=1.0):
    """低音弦乐的短促奏（用于紧张段落的固定音型）。"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = _saw(freq, t, 0.002) + 0.5 * _saw(freq * 2, t, 0.002)
    x = fft_filter(x, 40, 650 + 500 * accent, 2)
    env = np.minimum(t / 0.025, 1) * np.exp(-t / (0.25 + 0.2 * accent))
    return x * env * 0.12 * accent


def pluck(freq, dur=3.2, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for h in range(1, 14):
        fh = freq * h * (1 + 0.00035 * h * h)
        if fh > 9000: break
        x += np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28)) * np.exp(-t * (0.9 + 0.55 * h)) * (1.0 / h ** (1.25 / bright)) * (1 if h % 2 else 0.8)
    return x * np.minimum(t / 0.004, 1) * 0.5


def drone(dur, f=36.71):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for k, a in ((1, 0.5), (2, 0.42), (3, 0.16), (4, 0.08)):
        x += a * np.sin(2 * np.pi * f * k * t + 0.6 * np.sin(2 * np.pi * 0.05 * t + k)) * (1 + 0.25 * np.sin(2 * np.pi * (0.03 + k / 900) * t))
    return x


# ---------- 音效 ----------
def wind(dur, level=1.0, gust=0.11):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(size=n)
    lo = fft_filter(x, 90, 700, 2); hi = fft_filter(rng.normal(size=n), 900, 3800, 2)
    g1 = 0.55 + 0.45 * np.sin(2 * np.pi * gust * t + 1.3) * np.sin(2 * np.pi * gust * 0.37 * t + 0.4)
    g2 = 0.5 + 0.5 * np.sin(2 * np.pi * gust * 1.7 * t + 2.1)
    whistle = np.sin(2 * np.pi * (520 + 80 * np.sin(2 * np.pi * 0.07 * t)) * t) * 0.012 * g2
    return (lo * g1 * 0.06 + hi * g2 * g1 * 0.018 + whistle) * level


def whoosh(dur=0.9, f0=500, f1=3500):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(size=n); nb = 8; out = np.zeros(n)
    for b in range(nb):
        seg = slice(b * n // nb, (b + 1) * n // nb); fc = f0 * (f1 / f0) ** (b / (nb - 1))
        y = fft_filter(x, fc * 0.6, fc * 1.6, 2); w = np.zeros(n); w[seg] = 1
        k = int(SR * 0.04); w = np.convolve(w, np.hanning(k) / np.hanning(k).sum(), 'same'); out += y * w
    return out * np.sin(np.pi * t / dur) ** 1.5 * 0.6


def arrow_fly(dur=0.55):
    """箭飞过：短促、上扬的气流声 + 尾羽颤音。"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = whoosh(dur, 900, 5200) * 1.1
    flutter = fft_filter(rng.normal(size=n), 2000, 7000, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * t)) * np.sin(np.pi * t / dur) ** 2 * 0.25
    return x + flutter


def thunk(dur=0.45):
    """箭钉入木头。"""
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 180 * t * (1 + 0.4 * np.exp(-t / 0.01))) * np.exp(-t / 0.05)
    crack = fft_filter(rng.normal(size=n) * np.exp(-t / 0.006), 1500, 8000, 2) * 0.6
    ring = np.sin(2 * np.pi * 950 * t) * np.exp(-t / 0.09) * 0.12
    return (body * 0.7 + crack + ring) * 0.8


def paper(dur=0.8):
    """纸卷展开的沙沙声。"""
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(size=n)
    crk = np.zeros(n)
    for _ in range(int(dur * 70)):
        i = rng.integers(0, n - 400); crk[i:i + 400] += rng.normal(size=400) * np.exp(-np.arange(400) / 60) * rng.uniform(0.2, 1)
    y = fft_filter(x, 1800, 9000, 2) * 0.12 + fft_filter(crk, 1200, 9000, 2) * 0.5
    return y * np.sin(np.pi * t / dur) ** 0.8


def rumble(dur, rate=38, level=1.0):
    n = int(dur * SR); x = np.zeros(n); k = int(0.09 * SR); t = np.arange(k) / SR
    base = np.sin(2 * np.pi * 70 * t * (1 + 0.6 * np.exp(-t / 0.01))) * np.exp(-t / 0.022)
    for _ in range(int(dur * rate)):
        i = rng.integers(0, n - k); x[i:i + k] += base * rng.uniform(0.3, 1.0)
    return fft_filter(x, 40, 420, 2) * 0.22 * level


def crash(dur=2.2):
    """城墙塌落：低频轰响 + 碎石。"""
    n = int(dur * SR); t = np.arange(n) / SR
    low = fft_filter(rng.normal(size=n), 30, 220, 2) * np.exp(-t / 0.7) * 1.4
    deb = np.zeros(n)
    for _ in range(140):
        i = rng.integers(0, int(n * 0.8)); m = int(SR * rng.uniform(0.01, 0.04)); deb[i:i + m] += rng.normal(size=m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.1, 0.6)
    return low + fft_filter(deb, 300, 4000, 2) * np.exp(-t / 1.2) * 0.7


def fire(dur, level=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    roar = fft_filter(rng.normal(size=n), 80, 900, 2) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t)) * 0.12
    cr = np.zeros(n)
    for _ in range(int(dur * 25)):
        i = rng.integers(0, n - 300); cr[i:i + 300] += rng.normal(size=300) * np.exp(-np.arange(300) / 40) * rng.uniform(0.1, 0.8)
    return (roar + fft_filter(cr, 1500, 8000, 2) * 0.35) * level


def reverb(x, t60=2.6, wet=0.3):
    n = int(t60 * SR); t = np.arange(n) / SR
    ir = np.stack([rng.normal(size=n), rng.normal(size=n)], 1) * np.exp(-6.9 * t / t60)[:, None]
    ir[: int(0.012 * SR)] = 0
    for c in range(2): ir[:, c] = fft_filter(ir[:, c], 150, 5200, 1)
    ir /= np.sqrt((ir ** 2).sum(0)).mean()
    m = len(x) + n; out = np.zeros_like(x)
    for c in range(2):
        out[:, c] = np.fft.irfft(np.fft.rfft(x[:, c], m) * np.fft.rfft(ir[:, c], m), m)[: len(x)]
    return x * (1 - wet * 0.3) + out * wet * 0.5


NOTE = lambda semis: 146.83 * 2 ** (semis / 12)     # D3 = 0
CH = {'Dm': [0, 7, 12, 15], 'Bb': [-4, 3, 8, 12], 'Gm': [-7, 0, 5, 10], 'Asus': [-5, 2, 7, 12], 'A': [-5, 2, 7, 11],
      'F': [-9, 3, 7, 12], 'C': [-2, 5, 10, 14], 'Em7b5': [2, 5, 8, 12], 'Dsus': [0, 7, 12, 17], 'Ebmaj': [1, 8, 13, 17]}
