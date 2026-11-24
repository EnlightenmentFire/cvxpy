# -*- coding: utf-8 -*-
"""配乐 + 音效 + 旁白混音。全部程序合成，不用外部素材。
输入 audio/narration.wav + .json → 输出 audio/mix.wav (48k 立体声)
"""
import json, sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly, fftconvolve

SR = 48000
D = json.load(open('audio/narration.json', encoding='utf-8'))
LN = {l['id']: l for l in D['lines']}
at = lambda i: LN[i]['start']
en = lambda i: LN[i]['end']
cl = lambda i, k: LN[i]['clauses'][k]['start']
ce = lambda i, k: LN[i]['clauses'][k]['end']
TOTAL = D['total']
N = int(TOTAL * SR) + SR
rng = np.random.default_rng(1984)
tt = np.arange(N) / SR


def filt(x, kind, f, order=2):
    sos = butter(order, np.array(f) / (SR / 2) if np.ndim(f) else f / (SR / 2), kind, output='sos')
    return sosfilt(sos, x)


def place(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i < 0: return
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * g


def env_points(pts):
    """[(t, v), ...] → 逐样本线性包络"""
    ts, vs = zip(*pts)
    return np.interp(tt, ts, vs)


# ── 旁白 ──
vo, sr0 = sf.read('audio/narration.wav')
vo = resample_poly(vo, SR, sr0).astype(np.float64)
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo = filt(vo, 'highpass', 75)
# 简单压缩
e = np.abs(vo); k = int(.01 * SR); e = np.convolve(e, np.ones(k) / k, 'same')
thr = .12; g = np.where(e > thr, (thr + (e - thr) / 2.8) / np.maximum(e, 1e-9), 1.0)
gk = int(.03 * SR); g = np.convolve(g, np.ones(gk) / gk, 'same'); vo = vo * g
vo = vo / np.max(np.abs(vo)) * .82
# 旁白包络（给音乐做闪避）
ve = np.abs(vo); k = int(.25 * SR); ve = np.convolve(ve, np.ones(k) / k, 'same'); ve = np.clip(ve / .06, 0, 1)
k2 = int(.5 * SR); ve = np.maximum(ve, np.convolve(ve, np.ones(k2) / k2, 'same'))

# ── 场景时间（与画面一致）──
T_title = en('0.5') + .55
T_ch1 = at('1.1') - .3
T_ch2 = en('1.8') + .5
T_five = at('2.3') - .25
T_pledge = at('3.1') - .25
T_ch3 = en('3.4') + .5
T_office = at('4.1') + 1.5
W0 = en('4.3') + .35 + .25          # 批示开始写
W1 = cl('4.4', 2) - .15             # 写完
T_paper = at('4.6') - .25
T_depts = at('5.1') - .25
T_rmrb = at('5.4') - .25
T_gwy = at('6.1') - .25
T_weeks = at('6.2') - .25
T_side = at('6.3') - .25
T_oct = at('6.8') - .25
T_end = en('6.8') + .7
T_black = en('7.3') + .9

# 强度曲线
I = env_points([(0, .0), (.8, .28), (T_title - .3, .28), (T_title + .4, .62), (T_ch1 + .5, .5), (T_ch1 + 2.5, .42),
                (T_ch2 - .5, .42), (T_ch2 + .3, .6), (T_five, .5), (T_pledge - 1, .5), (T_pledge + .5, .3),
                (T_ch3 - .5, .3), (T_ch3 + .3, .62), (T_office + 2, .55), (at('4.3') - .3, .5), (en('4.3') + .2, .0),
                (W1 - .2, .0), (W1 + 2.5, .22), (T_paper - .5, .25), (T_paper + .6, .62), (T_depts, .62), (T_rmrb, .66),
                (T_gwy - 1, .66), (T_gwy + .8, .85), (T_oct - 1.2, .85), (T_oct + .5, .5), (T_end, .34),
                (T_black - .6, .3), (T_black + .15, 0), (TOTAL + 1, 0)])

# ── 配乐：D 小调，66 拍 ──
BPM = 66; BEAT = 60 / BPM; BAR = BEAT * 4
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = [[38, 45, 50, 53, 57], [34, 41, 46, 50, 53], [29, 41, 45, 48, 53], [36, 43, 48, 52, 55]]   # Dm  Bb  F  C


def chord_at(t): return CH[int(t // (BAR * 2)) % 4]


pad = np.zeros(N); pulse = np.zeros(N); keys = np.zeros(N); hi = np.zeros(N)
nseg = int(TOTAL // (BAR * 2)) + 2
for s in range(nseg):
    t0 = s * BAR * 2; c = CH[s % 4]; L = int((BAR * 2 + 1.6) * SR); x = np.arange(L) / SR
    a = np.minimum(1, x / 1.6) * np.minimum(1, (x[-1] - x) / 1.6)
    seg = np.zeros(L)
    for j, m in enumerate(c):
        f = midi(m)
        for det in (-.18, .0, .21):
            ff = f * (1 + det / 100)
            seg += (np.sin(2 * np.pi * ff * x + j) + .28 * np.sin(4 * np.pi * ff * x + 2 * j) + .1 * np.sin(6 * np.pi * ff * x)) * (.5 if j == 0 else .28)
    place(pad, seg * a, t0, .05)
    segh = np.zeros(L)
    for m in (c[2] + 12, c[4] + 12):
        f = midi(m); segh += np.sin(2 * np.pi * f * x) + .5 * np.sin(2 * np.pi * f * 1.003 * x + 1)
    place(hi, segh * a, t0, .02)
# 脉冲：八分音符的闷音根音
nb = int(TOTAL / (BEAT / 2)) + 1
for b in range(nb):
    t0 = b * BEAT / 2; c = chord_at(t0); f = midi(c[0] + (12 if b % 8 in (3, 6) else 0))
    L = int(.34 * SR); x = np.arange(L) / SR
    n = (np.sin(2 * np.pi * f * x) + .35 * np.sin(4 * np.pi * f * x) + .12 * np.sin(6 * np.pi * f * x)) * np.exp(-x * 13) * np.minimum(1, x / .004)
    place(pulse, n, t0, .16 * (1.0 if b % 4 == 0 else .62))
# 琴键：稀疏的动机
pat = [(0, 2), (1.5, 3), (2.5, 4), (4, 3), (6, 2), (7, 1)]
for s in range(nseg):
    t0 = s * BAR * 2; c = CH[s % 4]
    for (bt, idx) in pat:
        if rng.random() < .22: continue
        f = midi(c[idx] + 12); L = int(2.6 * SR); x = np.arange(L) / SR
        n = (np.sin(2 * np.pi * f * x) + .4 * np.sin(4 * np.pi * f * x) * np.exp(-x * 3) + .15 * np.sin(6 * np.pi * f * x) * np.exp(-x * 6)) * np.exp(-x * 2.2) * np.minimum(1, x / .006)
        place(keys, n, t0 + bt * BEAT, .07)
pad = filt(pad, 'lowpass', 1400); pulse = filt(pulse, 'lowpass', 900)
g_pulse = np.clip((I - .36) / .2, 0, 1); g_keys = np.clip((I - .44) / .16, 0, 1); g_hi = np.clip((I - .68) / .14, 0, 1)
music = pad * np.clip(I / .3, 0, 1) * (.6 + .6 * I) + pulse * g_pulse * (.5 + .8 * I) + keys * g_keys + hi * g_hi

# 混响
irL = int(1.6 * SR); ir = rng.standard_normal(irL) * np.exp(-np.arange(irL) / SR * 3.6); ir = filt(ir, 'lowpass', 3500); ir /= np.sqrt((ir ** 2).sum())
wet = fftconvolve(music, ir)[:N] * .5
irR = rng.standard_normal(irL) * np.exp(-np.arange(irL) / SR * 3.6); irR = filt(irR, 'lowpass', 3500); irR /= np.sqrt((irR ** 2).sum())
wetR = fftconvolve(music, irR)[:N] * .5
duck = (1 - .78 * ve) * .8
mL = (music + wet) * duck; mR = (music + wetR) * duck

# ── 音效 ──
fxL = np.zeros(N); fxR = np.zeros(N)


def fx(x, t, g=1.0, pan=0.0):
    place(fxL, x, t, g * (1 - max(0, pan) * .6)); place(fxR, x, t, g * (1 + min(0, pan) * .6))


def pen_strokes(t0, t1, nchar, g=1.0, seed=1):
    r = np.random.default_rng(seed); out = np.zeros(int((t1 - t0 + .5) * SR))
    for i in range(nchar):
        tc = (t1 - t0) * i / nchar
        for s in range(r.integers(2, 4)):
            d = r.uniform(.05, .13); L = int(d * SR); x = np.arange(L) / SR
            n = r.standard_normal(L); n = filt(n, 'bandpass', [1800 + r.uniform(-300, 600), 6500], 2)
            e = np.sin(np.pi * x / d) ** .7 * (1 + .5 * np.sin(2 * np.pi * r.uniform(25, 60) * x))
            j = int((tc + s * (t1 - t0) / nchar / 3.4 + r.uniform(0, .02)) * SR)
            if j + L < len(out): out[j:j + L] += n * e * r.uniform(.5, 1)
    body = filt(out, 'bandpass', [250, 900], 2) * .7       # 纸面/桌面的闷响
    return (out + body) * g


pen = pen_strokes(W0, W1, 49, 1.0, 3); fx(pen, W0, .11, -.15)                       # 批示：只留写字声
fx(pen_strokes(cl('2.1', 4) - .2, en('2.1') + .2, 8, 1.0, 5), cl('2.1', 4) - .2, .035, .1)   # 写信标题
fx(pen_strokes(at('3.2') + .6, en('3.3') + .3, 55, 1.0, 7), at('3.2') + .6, .022, .2)        # 55 个签名


def thud(f0=95, d=.22):
    L = int(d * SR); x = np.arange(L) / SR
    f = f0 * np.exp(-x * 9) + 42; ph = 2 * np.pi * np.cumsum(f) / SR
    c = filt(rng.standard_normal(L), 'bandpass', [700, 3000]) * np.exp(-x * 70) * .5
    return np.sin(ph) * np.exp(-x * 16) + c


for i in range(5): fx(thud(), cl('1.7', i) - .08 + .2, .3, (-.4, .5, .4, -.4, -.5)[i])      # 五枚图章


def whoosh(d=.55, lo=300, hi=2500):
    L = int(d * SR); x = np.arange(L) / SR
    return filt(rng.standard_normal(L), 'bandpass', [lo, hi]) * np.sin(np.pi * x / d) ** 2


for t in (at('2.1') + 1.7, T_pledge, T_office + .1, T_paper, T_rmrb, T_gwy, at('5.7') - .05): fx(whoosh(), t, .05)


def boom(d=2.4):
    L = int(d * SR); x = np.arange(L) / SR
    return (np.sin(2 * np.pi * 55 * x) + .5 * np.sin(2 * np.pi * 36.7 * x)) * np.exp(-x * 2.2) * np.minimum(1, x / .02)


for t in (T_title + .1, T_ch1, T_ch2, T_ch3, T_gwy + .1): fx(boom(), t, .26)


def tick(f=2400, d=.03):
    L = int(d * SR); x = np.arange(L) / SR
    return np.sin(2 * np.pi * f * x) * np.exp(-x * 160) + filt(rng.standard_normal(L), 'highpass', 3000) * np.exp(-x * 300) * .4


for i in range(9): fx(tick(1900), cl('4.2', 1) - .1 + 2.0 * (i / 8) ** 1.0, .09)             # 钟
TA = cl('6.2', 0) + .3; TB = ce('6.2', 1) + .2
for i in range(50): fx(tick(2600 if i < 49 else 1500, .03), TA + (TB - TA) * i / 49, .05 if i < 49 else .12, (i % 7 - 3) / 5)   # 49 天
for i in range(55): fx(tick(3000, .02), at('0.5') - .25 + .25 + i * 2.2 / 55, .03, (i % 11 - 5) / 8)     # 55
# 收尾三句：三个低音
for t, m in ((at('7.1') - .1, 38), (at('7.2') - .1, 45), (at('7.3') - .1, 50)):
    f = midi(m); L = int(4 * SR); x = np.arange(L) / SR
    n = (np.sin(2 * np.pi * f * x) + .4 * np.sin(4 * np.pi * f * x) * np.exp(-x * 2) + .2 * np.sin(6 * np.pi * f * x) * np.exp(-x * 4)) * np.exp(-x * 1.1) * np.minimum(1, x / .008)
    fx(n, t, .16)
fxwet = fftconvolve(fxL + fxR, ir)[:N] * .12

L_ = vo + mL + fxL + fxwet; R_ = vo + mR + fxR + fxwet
# 结尾黑场静音
fade = np.clip((T_black + .35 - tt) / .5, 0, 1); L_ *= fade; R_ *= fade
out = np.stack([L_, R_], 1)[:int(TOTAL * SR)]
pk = np.max(np.abs(out)); out = out / pk * .9 if pk > .9 else out
sf.write('audio/mix.wav', out.astype(np.float32), SR)
sf.write('audio/music_only.wav', np.stack([mL + fxL + fxwet, mR + fxR + fxwet], 1)[:int(TOTAL * SR)].astype(np.float32), SR)
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
print('total %.2f  peak %.2f  vo rms %.1f dB  music rms %.1f dB  pen-gap music rms %.1f dB' % (TOTAL, pk, rms(vo), rms(mL), rms(mL[int(W0 * SR):int(W1 * SR)])))
