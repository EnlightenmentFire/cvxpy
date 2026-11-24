# -*- coding: utf-8 -*-
"""自合成配乐（不使用任何外部素材）+ 旁白压低 + 混音 -> build/mix.wav
暗调氛围垫底：缓慢和弦垫音 + 稀疏的钟琴样泛音 + 紧张段落的低频脉冲。
"做完会死"那一句前后各 2 秒，音乐完全静音。
"""
import json, os, numpy as np, soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt, resample_poly
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
TL = json.load(open(os.path.join(ROOT, 'timeline.json')))
SR = 44100; DUR = TL['duration']; N = int(DUR * SR); t = np.arange(N) / SR
rng = np.random.default_rng(7)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
SC = {s['name']: s for s in TL['scenes']}; CUE = {l['cue']: l for l in TL['lines'] if l.get('cue')}

def lp(x, fc, order=2): return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2): return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)
def env_seg(a, b, fi=3.0, fo=3.0):
    return np.clip((t - a) / fi, 0, 1) * np.clip((b - t) / fo, 0, 1)

# 和弦进行（D 小调，慢），每 12 秒换一次；结尾两场转到关系大调，亮一点
DARK = [[38, 45, 50, 53, 57], [34, 41, 46, 50, 53], [31, 43, 46, 50, 55], [33, 40, 45, 52, 57]]   # Dm  Bb  Gm  Asus
WARM = [[41, 48, 53, 57, 60], [34, 46, 50, 53, 58], [36, 43, 48, 52, 55], [38, 45, 50, 53, 57]]   # F  Bb  C  Dm
def pad(prog, a, b, bright=1.0):
    out = np.zeros((2, N)); L = 12.0; k = 0; x = a; X = 4.0   # X: 和弦之间的交叠
    while x < b:
        ch = prog[k % len(prog)]
        n0 = max(0, int((x - X) * SR)); n1 = min(N, int((min(x + L, b) + X) * SR)); tt = t[n0:n1]
        e = np.clip((tt - (x - X)) / X, 0, 1) * np.clip((min(x + L, b) + X - tt) / X, 0, 1)
        for j, m in enumerate(ch):
            f = hz(m)
            for d, pan in ((-0.07, .25), (0.05, .75), (0.0, .5)):
                ph = rng.uniform(0, 6.28); ff = f * 2 ** (d / 12); a1 = 2 * np.pi * ff * tt + ph
                w = np.sin(a1) + bright * 0.35 * np.sin(2 * a1) + bright * 0.12 * np.sin(3 * a1)
                w *= (0.75 + 0.25 * np.sin(2 * np.pi * (0.05 + 0.02 * j) * tt + ph)) * e * (0.9 if j else 1.3) / (1 + j * 0.25)
                out[0, n0:n1] += w * (1 - pan); out[1, n0:n1] += w * pan
        x += L; k += 1
    return out
def bells(a, b, scale, density=0.16, seed=1):
    r = np.random.default_rng(seed); out = np.zeros((2, N)); x = a + 2
    while x < b - 3:
        m = scale[r.integers(len(scale))] + 12 * r.integers(1, 3); f = hz(m); n0 = int(x * SR); L = int(5 * SR)
        if n0 + L < N:
            tt = np.arange(L) / SR
            w = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2.01 * f * tt) * np.exp(-tt * 3) + 0.2 * np.sin(2 * np.pi * 3.98 * f * tt) * np.exp(-tt * 6)) * np.exp(-tt * 1.3) * (1 - np.exp(-tt * 200))
            pan = r.uniform(.2, .8); g = r.uniform(.5, 1)
            out[0, n0:n0 + L] += w * g * (1 - pan); out[1, n0:n0 + L] += w * g * pan
        x += r.exponential(1 / density) + 1.5
    return out
def pulse(a, b, bpm=56):
    out = np.zeros(N); step = 60 / bpm; x = a
    while x < b:
        for off, g in ((0, 1.0), (0.22, 0.6)):
            n0 = int((x + off) * SR); L = int(0.5 * SR)
            if n0 + L < N:
                tt = np.arange(L) / SR
                out[n0:n0 + L] += g * np.sin(2 * np.pi * (46 + 30 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
        x += step
    return out * env_seg(a, b, 4, 3)

mus = np.zeros((2, N))
s_end = SC['result']['start']
mus += pad(DARK, 0, s_end, 0.8) * 0.055
mus += pad(WARM, s_end - 1, DUR, 1.3) * 0.06
mus += bells(0, s_end, [38, 41, 45, 48, 50], 0.13, 3) * 0.05
mus += bells(s_end, DUR, [41, 45, 48, 50, 53], 0.2, 5) * 0.06
for nm in ('dilemma', 'time'):
    p = pulse(SC[nm]['start'] + 2, SC[nm]['end'] - 1) * 0.16
    mus[0] += p; mus[1] += p
# 低频底噪（房间感）
room = lp(rng.standard_normal(N), 120, 2) * 0.012
mus[0] += room; mus[1] += np.roll(room, 911)
# 混响
L = int(3.2 * SR); ir = rng.standard_normal((2, L)) * np.exp(-np.arange(L) / SR * 2.2); ir[:, :200] = 0
wet = np.stack([fftconvolve(mus[c], ir[c])[:N] for c in range(2)]); wet /= np.abs(wet).max() + 1e-9
mus = mus / (np.abs(mus).max() + 1e-9) * 0.6 + wet * 0.45
mus = np.stack([hp(lp(mus[c], 6500), 28) for c in range(2)])
mus /= np.abs(mus).max()

# 旁白
nar, sr0 = sf.read(os.path.join(ROOT, 'narration.wav'), dtype='float32')
nar = resample_poly(nar, 147, 80)[:N]; nar = np.pad(nar, (0, N - len(nar)))
nar = hp(nar, 70); nar = nar / np.abs(nar).max() * 0.9
# 旁白包络 -> 音乐压低（提前 0.25s 开始压，说完 0.9s 才慢慢放开）
ev = np.abs(nar); w = int(0.05 * SR); ev = np.convolve(ev, np.ones(w) / w, 'same') > 0.012
act = ev.astype(float); k1 = int(0.25 * SR); act = np.maximum(act, np.roll(act, -k1))
rel = int(0.9 * SR); sm = np.convolve(act, np.ones(rel) / rel, 'same'); sm = np.clip(sm * 2.2, 0, 1)
gain = 10 ** ((-10.5 - 10.5 * sm) / 20)          # 无旁白 -10.5 dB，旁白下 -21 dB
# "做完会死"：前后各 2 秒 + 说这句的时候，音乐全静
q = CUE['q_die']; hush = CUE['hush']
a, b = hush['end'] - 0.15, q['end'] + 2.0
mute = 1 - np.clip((t - (a - 0.7)) / 0.7, 0, 1) * np.clip((b + 1.6 - t) / 1.6, 0, 1)
mute[(t >= a) & (t <= b)] = 0
# "另外 24 种"：这一句也把音乐压到很低，留出空
q2 = CUE['q_24']; dip = 1 - 0.75 * np.clip((t - (q2['start'] - 1.0)) / 0.5, 0, 1) * np.clip((q2['end'] + 1.2 - t) / 0.6, 0, 1)
fade = np.clip(t / 2.0, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
mus *= gain * mute * dip * fade
floor = lp(rng.standard_normal(N), 900, 1) * 10 ** (-58 / 20)   # 极低的底噪，避免“静音”听起来像断流
mix = np.stack([nar, nar]) * 0.92 + mus + floor
mix = np.tanh(mix * 1.05) / 1.05
sf.write(os.path.join(ROOT, 'mix.wav'), mix.T.astype(np.float32), SR)
sf.write(os.path.join(ROOT, 'music_only.wav'), mus.T.astype(np.float32), SR)
print('mix ok', round(DUR, 1), 'peak', float(np.abs(mix).max()))
