"""Procedurally generated background music (self-made, no third-party samples).
Palette: guqin-like plucks, xiao-like flute, qing/bell strikes, soft drone.
Usage: python music.py DURATION_SEC out.wav [--bells t1,t2,...]
"""
import sys, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
rng = np.random.default_rng(55)

def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))

def guqin(f, dur=4.0, amp=0.5, bend=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    # slight pitch glide (吟猱 feel)
    ff = f * (1 + bend * np.exp(-t / 0.25)) * (1 + 0.0025 * np.sin(2*np.pi*4.5*t) * (1 - np.exp(-t/0.6)))
    ph = 2*np.pi*np.cumsum(ff)/SR
    y = np.zeros(n)
    for k in range(1, 9):
        a = 1.0 / k**1.3
        if k == 2: a *= 1.3
        y += a * np.sin(k*ph) * env_exp(n, 1.8 / (1 + 0.55*(k-1)))
    att = np.minimum(1, t / 0.004)
    noise = rng.standard_normal(n) * env_exp(n, 0.012) * 0.25
    y = (y * att + noise)
    sos = butter(2, min(4000, f*10)/(SR/2), 'low', output='sos')
    return amp * sosfilt(sos, y) / 2.2

def fanyin(f, dur=4.5, amp=0.25):  # harmonic (泛音), pure & bell-like
    n = int(dur*SR); t = np.arange(n)/SR
    y = np.sin(2*np.pi*f*t) * env_exp(n, 1.6) + 0.2*np.sin(2*np.pi*2*f*t)*env_exp(n, 0.7)
    return amp * y * np.minimum(1, t/0.003)

def xiao(f, dur, amp=0.12):
    n = int(dur*SR); t = np.arange(n)/SR
    vib = 1 + 0.006*np.sin(2*np.pi*5.0*t + rng.uniform(0, 6)) * np.minimum(1, t/1.2)
    ph = 2*np.pi*np.cumsum(f*vib)/SR
    y = np.sin(ph) + 0.18*np.sin(2*ph) + 0.05*np.sin(3*ph)
    br = rng.standard_normal(n)
    sos = butter(2, [f*0.7/(SR/2), min(0.95, f*3.2/(SR/2))], 'band', output='sos')
    y = y + 0.35*sosfilt(sos, br)
    a = np.minimum(1, t/0.45) * np.minimum(1, (dur - t)/0.9)
    return amp * y * np.clip(a, 0, 1)

def qing(f=392.0, dur=9.0, amp=0.5):
    n = int(dur*SR); t = np.arange(n)/SR
    parts = [(1.0, 1.0, 6.0), (2.76, 0.5, 3.0), (5.40, 0.3, 1.6), (8.93, 0.18, 0.8), (1.006, 0.6, 5.5)]
    y = sum(a*np.sin(2*np.pi*f*r*t + rng.uniform(0, 6))*env_exp(n, d) for r, a, d in parts)
    y += rng.standard_normal(n)*env_exp(n, 0.006)*0.3
    return amp * y * np.minimum(1, t/0.002) / 2.0

def drone(total):
    n = int(total*SR); t = np.arange(n)/SR
    y = np.zeros(n)
    for f, a, lf in [(73.42, 0.10, 0.031), (110.0, 0.06, 0.023), (146.83, 0.035, 0.017), (220.0, 0.015, 0.041)]:
        y += a*np.sin(2*np.pi*f*t)*(0.65+0.35*np.sin(2*np.pi*lf*t + rng.uniform(0, 6)))
    nz = sosfilt(butter(2, 300/(SR/2), 'low', output='sos'), rng.standard_normal(n))*0.012
    return y + nz

def reverb(x, rt=3.2, mix=0.35):
    n = int(rt*SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n)/(rt/6.9*SR))
    ir = sosfilt(butter(1, 3500/(SR/2), 'low', output='sos'), ir)
    ir /= np.sqrt(np.sum(ir**2))
    wet = fftconvolve(x, ir)[:len(x)]
    return (1-mix)*x + mix*wet*0.9

def add(buf, sig, at):
    i = int(at*SR); j = min(len(buf), i+len(sig))
    if i < len(buf): buf[i:j] += sig[:j-i]

def compose(total, bells=()):
    n = int(total*SR) + SR
    buf = np.zeros(n)
    scale = [146.83, 164.81, 185.0, 220.0, 246.94, 293.66, 329.63, 369.99, 440.0, 493.88]  # D pentatonic
    t = 1.2; idx = 4
    while t < total - 4:
        # a phrase: 3-7 plucks, flowing, then a breath
        for _ in range(rng.integers(3, 8)):
            idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2, 0]), 0, len(scale)-1))
            f = scale[idx]
            add(buf, guqin(f, amp=0.42*rng.uniform(0.75, 1.0), bend=rng.choice([0, 0, 0.03, -0.02])), t)
            if rng.random() < 0.25:
                add(buf, guqin(f/2, amp=0.25), t)
            t += rng.choice([0.55, 0.8, 0.8, 1.1, 1.6])
        if rng.random() < 0.35:
            add(buf, fanyin(scale[rng.integers(5, 10)]*2), t)
        t += rng.uniform(1.8, 3.6)
    # xiao lines, sparse
    t = 18.0
    while t < total - 10:
        d = rng.uniform(5, 9)
        f = rng.choice([293.66, 329.63, 369.99, 440.0, 293.66])
        add(buf, xiao(f, d), t)
        if rng.random() < 0.6:
            add(buf, xiao(rng.choice([246.94, 293.66, 220.0]), d*0.8), t + d - 0.3)
        t += d + rng.uniform(20, 40)
    for b in bells:
        add(buf, qing(392.0 if b > 0.5 else 293.66, amp=0.45), b)
    buf[:int(total*SR)] += drone(total)
    y = reverb(buf[:int(total*SR)])
    fade = np.ones_like(y); m = int(4*SR); fade[-m:] = np.linspace(1, 0, m)
    y *= fade
    y /= np.max(np.abs(y)) / 0.8
    return y

if __name__ == '__main__':
    total = float(sys.argv[1]); out = sys.argv[2]
    bells = []
    if len(sys.argv) > 3 and sys.argv[3] == '--bells':
        bells = [float(x) for x in sys.argv[4].split(',') if x]
    y = compose(total, bells)
    sf.write(out, np.stack([y, y], 1).astype(np.float32), SR)
