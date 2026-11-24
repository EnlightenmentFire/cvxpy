# -*- coding: utf-8 -*-
"""音频：旁白拼接（变速）、程序合成的鼓与垫音、旁白时压低音乐。全部原创合成，无外部素材。"""
import numpy as np, subprocess, os, soundfile as sf, sys
from scipy import signal
from timeline import TL, TEMPO, WAVDIR
from script import BEATS
SR = 48000
T = TL(); N = int((T.total + 0.5) * SR)
rng = np.random.default_rng(42)

def narration():
    out = np.zeros(N, np.float32); os.makedirs('/home/user/work/tts/tmp', exist_ok=True)
    for a in T.audio:
        if a['a0'] is None: continue
        tmp = f"/home/user/work/tts/tmp/{a['id']}.wav"
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f"{a['a0']:.3f}", '-to', f"{a['a1']:.3f}", '-i', WAVDIR + a['id'] + '.wav',
                        '-af', f'atempo={TEMPO},highpass=f=70,aresample={SR}', '-ac', '1', tmp], check=True)
        w, sr = sf.read(tmp, dtype='float32')
        # 每段统一响度
        rms = np.sqrt(np.mean(w ** 2) + 1e-9); w = w * (0.085 / rms)
        f = int(0.012 * SR); w[:f] *= np.linspace(0, 1, f); w[-f:] *= np.linspace(1, 0, f)
        i = int(a['t'] * SR); out[i:i + len(w)] += w[:max(0, N - i)]
    return out

def env_follow(x, att=0.02, rel=0.35):
    e = np.abs(x); b = int(0.05 * SR)
    e = signal.lfilter(np.ones(b) / b, [1], e)
    e = np.maximum.accumulate(e[::-1] * 0 + e)   # no-op placeholder
    k = np.exp(-1 / (rel * SR)); out = np.zeros_like(e); v = 0.0
    step = 64
    for i in range(0, len(e), step):
        m = e[i:i + step].max(); v = max(m, v * k ** step); out[i:i + step] = v
    return out

def drum(t0, gain=1.0, f0=58, dur=2.2, tone=1.0):
    """大鼓：正弦下滑 + 鼓皮噪声 + 余响。"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.6 * np.exp(-t * 28)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 3.2) + 0.45 * np.sin(ph * 1.5 + 0.3) * np.exp(-t * 6)
    nz = rng.normal(0, 1, n); b, a = signal.butter(2, [180 / (SR / 2), 1400 / (SR / 2)], 'band'); skin = signal.lfilter(b, a, nz) * np.exp(-t * 30) * 0.5 * tone
    return t0, (body + skin) * gain
def tick(t0, gain=0.4):
    """鼓边轻击。"""
    n = int(0.35 * SR); t = np.arange(n) / SR
    nz = rng.normal(0, 1, n); b, a = signal.butter(2, [900 / (SR / 2), 3800 / (SR / 2)], 'band')
    return t0, (signal.lfilter(b, a, nz) * np.exp(-t * 55) + 0.5 * np.sin(2 * np.pi * 210 * t) * np.exp(-t * 40)) * gain
def pluck(t0, freq, gain=0.5, dur=3.5):
    """拨弦（Karplus-Strong），近古琴音色。"""
    n = int(dur * SR); p = int(SR / freq); buf = rng.uniform(-1, 1, p)
    b, a = signal.butter(1, 1800 / (SR / 2)); buf = signal.lfilter(b, a, buf)
    y = np.zeros(n); y[:p] = buf
    for i in range(p, n): y[i] = 0.4975 * (y[i - p] + y[i - p + 1 if i - p + 1 < n else i - p])
    t = np.arange(n) / SR
    return t0, y * gain * np.minimum(1, t * 400)
def swell(t0, dur, gain=0.3, lo=60, hi=420):
    """低频涌动（洪水、压迫感）。"""
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.normal(0, 1, n); b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band')
    e = np.sin(np.pi * t / dur) ** 1.5
    return t0, signal.lfilter(b, a, nz) * e * gain * (0.8 + 0.2 * np.sin(2 * np.pi * 0.35 * t))

def pad():
    """垫音：D 小调空五度持续音，缓慢起伏。"""
    t = np.arange(N) / SR; y = np.zeros(N)
    for f, g, lf in ((36.71, 0.55, 0.031), (73.42, 0.9, 0.043), (110.0, 0.5, 0.057), (146.83, 0.35, 0.071), (220.0, 0.10, 0.09), (293.66, 0.06, 0.11)):
        for det in (-0.25, 0.22):
            y += g * np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6.28)) * (0.62 + 0.38 * np.sin(2 * np.pi * lf * t + rng.uniform(0, 6.28)))
    nz = rng.normal(0, 1, N); b, a = signal.butter(2, [90 / (SR / 2), 300 / (SR / 2)], 'band'); y += signal.lfilter(b, a, nz) * 0.9
    return y / np.abs(y).max()

def reverb(x, wet=0.28):
    ir_n = int(2.6 * SR); t = np.arange(ir_n) / SR
    ir = rng.normal(0, 1, ir_n) * np.exp(-t * 2.6); b, a = signal.butter(2, 2600 / (SR / 2)); ir = signal.lfilter(b, a, ir); ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    return x + wet * signal.fftconvolve(x, ir)[:len(x)]

def music():
    S, E = T.S, T.E
    ev = []
    # 片头
    ev += [drum(0.25, 0.9), drum(S('a1') + 2.2, 0.7, 50), tick(S('a2') + 2.6, 0.3), drum(S('a3') + 3.6, 0.55, 52)]
    t0 = T.title[0]
    ev += [drum(t0 + 0.15, 1.2, 46, 3.2), drum(t0 + 0.9, 0.9, 62), pluck(t0 + 0.3, 146.83, 0.55), pluck(t0 + 1.0, 220.0, 0.45), pluck(t0 + 1.6, 174.61, 0.45), pluck(t0 + 2.3, 146.83 / 2, 0.6)]
    # 章节卡：一声重鼓 + 两个拨弦
    motifs = {1: (146.83, 220.0), 2: (130.81, 196.0), 3: (174.61, 220.0), 4: (110.0, 164.81), 5: (146.83, 174.61), 6: (98.0, 146.83)}
    for sec, (c0, c1) in T.chap.items():
        f1, f2 = motifs[sec]
        ev += [drum(c0 + 0.12, 1.1, 48, 3.0), tick(c0 + 0.62, 0.35), pluck(c0 + 0.2, f1, 0.5), pluck(c0 + 0.95, f2, 0.42)]
    # 一：汉中称王、北上、洪水、威震华夏
    ev += [drum(S('b1') + 4.6, 0.6, 60), tick(S('b2') + 0.8, 0.3), tick(S('b2') + 1.6, 0.3), tick(S('b2') + 2.4, 0.3)]
    ev += [swell(S('b3') + 0.5, E('b4') - S('b3') + 1.5, 0.55), drum(S('b4') + 4.4, 0.8, 44, 3.0)]
    for i in range(3): ev.append(drum(S('b5') + 0.9 + i * 1.05, 0.75 - i * 0.12, 54))
    # 二：隐患——稀疏轻击，“还当治之”一记
    for bid in ('c1', 'c2', 'c7'): ev.append(tick(S(bid) + 0.9, 0.28))
    ev += [drum(S('c5') + 3.3, 0.85, 50), tick(S('c6') + 3.6, 0.3), pluck(S('c3') + 0.3, 130.81, 0.3), pluck(S('c4') + 0.3, 116.54, 0.3)]
    # 三：孙权一侧
    ev += [pluck(S('d1') + 0.4, 174.61, 0.3), drum(S('d2') + 3.9, 0.6, 58), pluck(S('d3') + 2.5, 220.0, 0.28), tick(S('d4') + 0.7, 0.3), drum(S('d6') + 3.4, 0.7, 52)]
    # 四：白衣渡江——缓慢的心跳式鼓点，逐渐加密
    t = S('e1') + 0.6; i = 0
    while t < S('e3'):
        ev.append(drum(t, 0.42 + 0.02 * i, 50, 1.6, tone=0.6)); 
        if i % 2: ev.append(tick(t + 0.42, 0.18))
        t += max(1.05, 1.9 - 0.06 * i); i += 1
    ev += [drum(E('e3') - 1.1, 0.8, 48), drum(S('e4') + 6.0, 1.15, 42, 3.4), tick(S('e4') + 6.5, 0.3), tick(S('e5') + 5.8, 0.3), drum(S('e6') + 5.6, 0.7, 56)]
    ev += [swell(S('e7') + 3, E('e8') - S('e7') - 3, 0.25, 50, 200), drum(E('e8') - 1.2, 0.8, 44, 3.0)]
    # 五：解读——以拨弦为主，克制
    ev += [drum(S('f2') + 6.2, 0.7, 50), drum(S('f3') + 6.5, 0.6, 54), drum(S('f4') + 0.3, 1.0, 46, 3.0), pluck(S('f4') + 0.5, 146.83, 0.45)]
    for bid, f in (('f5', 146.83), ('f6', 130.81), ('f7', 174.61), ('f8', 196.0), ('f9', 110.0), ('f10', 146.83), ('f11', 130.81), ('f12', 98.0)):
        ev.append(pluck(S(bid) + 0.25, f, 0.3))
    ev += [drum(S('f9') + 5.2, 0.9, 44, 3.0), drum(E('f12') - 1.6, 0.6, 50)]
    # 六：人事账——每一笔一记
    for bid, off, g in (('g1', 0.9, 0.9), ('g2', 1.0, 0.5), ('g2', 2.8, 0.5), ('g2', 5.2, 0.6), ('g3', 0.7, 0.5), ('g5', 0.6, 0.5)):
        ev.append(drum(S(bid) + off, g, 52))
    ev += [swell(E('g3') - 2.4, 4.0, 0.35, 70, 500), drum(E('g3') - 1.6, 1.0, 44, 3.0), pluck(S('g4') + 0.4, 110.0, 0.35), pluck(E('g5') - 3.8, 98.0, 0.4)]
    # 七：收尾三句
    for bid, f in (('h1', 146.83), ('h2', 130.81), ('h3', 98.0)):
        ev += [drum(S(bid) - 0.25, 0.95, 46, 3.2), pluck(S(bid) - 0.1, f, 0.5)]
    ev += [drum(S('h3') + 1.7, 1.2, 40, 4.0), pluck(T.end[0] + 0.3, 146.83, 0.5), pluck(T.end[0] + 1.2, 220.0, 0.4), pluck(T.end[0] + 2.2, 146.83 / 2, 0.55)]
    perc = np.zeros(N + 5 * SR)
    for t0, y in ev:
        i = int(max(0, t0) * SR); perc[i:i + len(y)] += y[:len(perc) - i]
    perc = reverb(perc[:N] * 0.5, 0.32)
    p = pad()
    # 垫音随章节起伏
    t = np.arange(N) / SR; lvl = np.full(N, 0.5)
    for (a0, a1, v) in ((S('b3'), E('b5'), 0.8), (S('e1'), E('e4'), 0.85), (S('f4'), E('f12'), 0.6), (S('g3'), E('g5'), 0.8), (S('h1'), T.total, 0.9)):
        lvl = np.maximum(lvl, v * np.clip(np.minimum((t - a0) / 3.0, (a1 - t) / 3.0), 0, 1))
    return perc, p * lvl * 0.11

def build(out='/home/user/work/vid/audio.wav'):
    nar = narration()
    perc, p = music()
    e = env_follow(nar); duck = 1.0 - 0.62 * np.clip(e / 0.03, 0, 1)
    k = int(0.25 * SR); duck = signal.lfilter(np.ones(k) / k, [1], duck)
    mus = (perc * 0.95 + p) * duck
    t = np.arange(N) / SR
    mus *= np.clip(t / 0.8, 0, 1) * np.clip((T.total - t) / 2.5, 0, 1)
    mix = nar * 1.0 + mus * 0.80
    st = np.stack([mix, mix], 1)
    # 轻微立体声展宽：音乐部分左右微差
    d = int(0.011 * SR); st[d:, 1] += mus[:-d] * 0.18; st[d:, 0] -= mus[:-d] * 0.06
    pk = np.abs(st).max(); st = st / max(1.0, pk / 0.95)
    sf.write(out + '.raw.wav', st.astype(np.float32), SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', out + '.raw.wav', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=9,alimiter=limit=0.89', '-ar', '48000', out], check=True)
    sf.write('/home/user/work/vid/nar_only.wav', nar, SR)
    print('audio', out, round(T.total, 2))
if __name__ == '__main__': build()
