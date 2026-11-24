# -*- coding: utf-8 -*-
"""合成配乐与音效（全部由本脚本用 numpy 生成，无外部素材），并与旁白混音。
输出：audio/narration.wav、audio/music.wav、audio/mix.wav（48 kHz 立体声）。"""
import json, os, sys, numpy as np, soundfile as sf, librosa
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
TL = json.load(open(f"{ROOT}/src/timeline.json"))
TOTAL = TL['total'] + 0.5
N = int(TOTAL * SR)
rng = np.random.default_rng(423)
def LT(prefix):
    return [l for l in TL['lines'] if l['text'].startswith(prefix)][0]
AT = lambda p: LT(p)['start']
ET = lambda p: LT(p)['end']
S = TL['secs']

def box(x, k):          # 滑动平均（累加和实现，O(N)）
    c = np.cumsum(np.concatenate([[0.0], x])); h = k // 2
    i0 = np.clip(np.arange(len(x)) - h, 0, len(x)); i1 = np.clip(np.arange(len(x)) + (k - h), 0, len(x))
    return (c[i1] - c[i0]) / k

def add(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]; l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.414; buf[i:i + len(x), 1] += x * gain * r * 1.414

def env(n, a=0.01, d=0.5, curve=4.0):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d * curve / 4)

def fft_filter(x, lo=None, hi=None, order=4):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * g, len(x))

# ---------- 音色 ----------
def taiko(f0=62, dur=1.6, hard=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.4 * np.exp(-t / 0.035)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.42) + 0.35 * np.sin(2.02 * ph) * np.exp(-t / 0.16)
    click = fft_filter(rng.normal(size=n) * np.exp(-t / 0.012), 300, 3500, 2) * 0.5 * hard
    return np.tanh((body + click) * 1.6) * 0.8

def tom(f0=110, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.8 * np.exp(-t / 0.02)); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.13) + fft_filter(rng.normal(size=n) * np.exp(-t / 0.008), 500, 4000, 2) * 0.3) * 0.7

def pluck(freq, dur=3.2, bright=1.0):      # 筝/琴类拨弦：加法合成，泛音衰减随次数加快
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for h in range(1, 14):
        fh = freq * h * (1 + 0.00035 * h * h)
        if fh > 9000: break
        x += np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28)) * np.exp(-t * (0.9 + 0.55 * h)) * (1.0 / h ** (1.25 / bright)) * (1 if h % 2 else 0.8)
    att = np.minimum(t / 0.004, 1); bend = 1.0
    return x * att * 0.5

def pad(freqs, dur, cutoff=700, vib=0.0):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f in freqs:
        for det in (-0.006, 0.0, 0.007):
            ff = f * (1 + det)
            for h in range(1, 9):
                if ff * h > cutoff * 3: break
                x += np.sin(2 * np.pi * ff * h * t + rng.uniform(0, 6.28)) / h ** 1.6 / (1 + (ff * h / cutoff) ** 2)
    a = np.minimum(t / (dur * 0.3), 1) * np.minimum((dur - t) / (dur * 0.35), 1)
    return x * a * (1 + 0.12 * np.sin(2 * np.pi * 0.17 * t + rng.uniform(0, 6.28))) * 0.12

def whoosh(dur=0.9, f0=500, f1=3500):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(size=n)
    nb = 8; out = np.zeros(n)
    for b in range(nb):
        seg = slice(b * n // nb, (b + 1) * n // nb); fc = f0 * (f1 / f0) ** (b / (nb - 1))
        y = fft_filter(x, fc * 0.6, fc * 1.6, 2); w = np.zeros(n); w[seg] = 1
        k = int(SR * 0.04); w = np.convolve(w, np.hanning(k) / np.hanning(k).sum(), 'same'); out += y * w
    return out * np.sin(np.pi * t / dur) ** 1.5 * 0.6

def clank(dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f, d in ((523, 0.09), (1310, 0.06), (2140, 0.05), (3370, 0.035), (188, 0.12)):
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / d)
    x += fft_filter(rng.normal(size=n) * np.exp(-t / 0.01), 800, 7000, 2) * 0.8
    return x * 0.3 + taiko(80, dur, 0.5)[:n] * 0.6

def rumble(dur, rate=38, level=1.0):     # 马蹄/人群：大量低沉的小冲击
    n = int(dur * SR); x = np.zeros(n); k = int(0.09 * SR); t = np.arange(k) / SR
    base = np.sin(2 * np.pi * 70 * t * (1 + 0.6 * np.exp(-t / 0.01))) * np.exp(-t / 0.022)
    for _ in range(int(dur * rate)):
        i = rng.integers(0, n - k); x[i:i + k] += base * rng.uniform(0.3, 1.0)
    return fft_filter(x, 40, 420, 2) * 0.22 * level

def water(dur):
    n = int(dur * SR); x = fft_filter(rng.normal(size=n), 250, 2200, 1)
    t = np.arange(n) / SR; return x * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t)) * 0.05

NOTE = lambda semis: 146.83 * 2 ** (semis / 12)        # D3 为 0
PENT = [0, 3, 5, 7, 10, 12, 15, 17]                   # D 小调五声

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

# ---------- 旁白 ----------
def narration():
    buf = np.zeros(N)
    for l in TL['lines']:
        a, sr = sf.read(f"{ROOT}/audio/lines/{l['i']:03d}.wav"); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
        i = int(l['start'] * SR); buf[i:i + len(a)] += a[: N - i]
    buf = fft_filter(buf, 75, None, 2)
    # 轻压缩
    w = int(0.03 * SR); e = np.sqrt(np.maximum(box(buf ** 2, w), 0)) + 1e-6
    thr = 0.09; g = np.where(e > thr, (thr / e) ** 0.45, 1.0); g = box(g, w)
    buf = buf * g; buf = buf / np.abs(buf).max() * 0.86
    return buf


# ---------- 新增音色 ----------
def bowed(freq, dur, bright=1.0, vib=5.2):      # 低音弦乐：慢起音、带揉弦的加法合成
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    v = 1 + 0.004 * np.sin(2 * np.pi * vib * t + rng.uniform(0, 6.28)) * np.minimum(t / 0.8, 1)
    ph = 2 * np.pi * np.cumsum(freq * v) / SR
    for h in range(1, 13):
        if freq * h > 5200: break
        x += np.sin(h * ph + rng.uniform(0, 6.28)) / h ** (1.15 / bright) * (1.0 if h % 2 else 0.75) / (1 + (freq * h / (1300 * bright)) ** 2)
    att = min(0.9, dur * 0.3); rel = min(1.4, dur * 0.35)
    a = np.minimum(t / att, 1) ** 1.5 * np.minimum((dur - t) / rel, 1)
    return x * a * 0.2

def wind(dur, lo=180, hi=900, depth=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    x = fft_filter(rng.normal(size=n), lo, hi, 1) + 0.5 * fft_filter(rng.normal(size=n), lo * 2.2, hi * 2.4, 1)
    m = 0.55 + depth * (0.5 * np.sin(2 * np.pi * 0.11 * t + 1.0) + 0.3 * np.sin(2 * np.pi * 0.27 * t + 2.3) + 0.2 * np.sin(2 * np.pi * 0.53 * t))
    a = np.minimum(t / 2.0, 1) * np.minimum((dur - t) / 2.5, 1)
    return x * np.clip(m, 0.05, None) * a * 0.09

def drip(dur=0.5, f=1400):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * (1 + 0.5 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.05) * 0.25

def music():
    dry = np.zeros((N, 2)); perc = np.zeros((N, 2)); fx = np.zeros((N, 2)); amb = np.zeros((N, 2))
    t = np.arange(N) / SR
    # —— 静默段：傅弘之（肆）与那口井（玖），以及冷开场的井，音乐几乎收掉
    h1a, h1b = AT('断后的傅弘之被俘'), AT('长安的百姓，把朱龄石')
    h2a, h2b = AT('接着，就是开头那口井'), ET('孤城能做的')
    c0, c1 = AT('围城的魏军从地下挖过来'), AT('守这座城的人')
    def dip(a, b, lo, fi=1.6, fo=2.2):
        return 1 - (1 - lo) * np.clip((t - a) / fi, 0, 1) * np.clip((b - t) / fo, 0, 1)
    hush = dip(h1a, h1b + 0.5, 0.06) * dip(h2a - 0.5, h2b, 0.08) * dip(c0, c1, 0.3) * dip(AT('城要破了'), ET('我发过誓'), 0.25)
    # 1) 持续低音（D）
    drone = np.zeros(N)
    for f, a in ((36.71, 0.5), (73.42, 0.42), (110.0, 0.16), (146.83, 0.08)):
        drone += a * np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * 0.05 * t + f)) * (1 + 0.25 * np.sin(2 * np.pi * (0.03 + f / 9000) * t))
    keys = [(0, 0.5), (S['title']['start'], 0.85), (S['s1']['start'], 0.5), (S['s2']['start'], 0.55), (S['s3']['start'], 0.7), (S['s4']['start'], 0.75), (S['s5']['start'], 0.5),
            (S['s6']['start'], 0.65), (S['s7']['start'], 0.75), (S['s8']['start'], 0.6), (S['s9']['start'], 0.8), (S['s10']['start'], 0.6), (S['s11']['start'], 0.5), (S['s12']['start'], 0.55), (TOTAL - 4, 0.45), (TOTAL, 0.0)]
    inten = np.interp(t, [k[0] for k in keys], [k[1] for k in keys])
    low = drone * inten * 0.17
    # 2) 和声垫底
    chords = {'Dm': [0, 7, 12, 15], 'Bb': [-4, 3, 8, 12], 'Gm': [-7, 0, 5, 10], 'Asus': [-5, 2, 7, 12], 'F': [-9, 3, 7, 12], 'C': [-2, 5, 10, 14], 'Em7b5': [2, 5, 8, 12], 'A': [-5, 1, 7, 12]}
    plan = []
    def seq(t0, t1, names, step=8.0, gain=1.0, cut=650):
        k = 0; tt = t0
        while tt < t1 - 1: plan.append((tt, min(step, t1 - tt) + 2.5, names[k % len(names)], gain, cut)); tt += step; k += 1
    seq(0, S['title']['start'], ['Dm', 'Bb'], 9, 0.8, 520)
    seq(S['title']['start'], S['s1']['start'], ['Dm'], 4, 1.2, 900)
    seq(S['s1']['start'], S['s2']['start'], ['Dm', 'Gm', 'Bb', 'Asus'], 9, 0.75)
    seq(S['s2']['start'], S['s3']['start'], ['Gm', 'Dm', 'Em7b5', 'Asus'], 9, 0.7, 540)
    seq(S['s3']['start'], S['s4']['start'], ['Dm', 'Em7b5', 'Gm', 'A'], 8, 0.85, 600)
    seq(S['s4']['start'], S['s5']['start'], ['Dm', 'Bb', 'Gm', 'Asus'], 8, 0.9, 620)
    seq(S['s5']['start'], S['s6']['start'], ['F', 'C', 'Dm', 'Bb'], 8, 0.75, 700)
    seq(S['s6']['start'], S['s7']['start'], ['Dm', 'Gm', 'Em7b5', 'A'], 9, 0.8, 560)
    seq(S['s7']['start'], S['s8']['start'], ['Dm', 'Bb', 'Gm', 'Asus'], 7, 0.9, 680)
    seq(S['s8']['start'], S['s9']['start'], ['Gm', 'Dm', 'Em7b5', 'Asus'], 9, 0.75, 540)
    seq(S['s9']['start'], S['s10']['start'], ['Dm', 'Dm', 'Bb', 'A'], 8, 0.95, 600)
    seq(S['s10']['start'], S['s11']['start'], ['Dm', 'Gm', 'Bb', 'Dm'], 9, 0.8, 520)
    seq(S['s11']['start'], S['s12']['start'], ['Bb', 'F', 'Gm', 'Dm'], 9, 0.8, 640)
    seq(S['s12']['start'], TOTAL - 1, ['Bb', 'Gm', 'Dm', 'Dm'], 7, 1.0, 700)
    for (t0, d, nm, g, cut) in plan:
        add(dry, pad([NOTE(s - 12) for s in chords[nm]], d, cut), t0 - 1.2, 0.5 * g, rng.uniform(-0.25, 0.25))
    # 3) 低音弦乐线（缓慢的下行音型）
    def line(t0, semis, step=4.0, gain=0.55, octave=-12, bright=1.0):
        for k, sm in enumerate(semis):
            if sm is None: continue
            add(dry, bowed(NOTE(sm + octave), step * 1.25, bright), t0 + k * step, gain, rng.uniform(-0.3, 0.3))
    line(AT('关中的父老找上门来'), [12, 10, 7, 5, 7, 3, 2, 0], 3.3, 0.5)
    line(AT('刘裕也难过'), [7, 5, 3, 2], 2.6, 0.45)
    line(AT('第二年正月'), [0, None, 3, None, 2, None, 0, None, -2, None, 0, None, 3], 4.0, 0.5, -12, 0.8)
    line(AT('消息传到彭城'), [12, 10, 8, 7, 5, 3, 2, 0], 2.4, 0.55)
    line(AT('现在说毛德祖'), [0, 3, 5, 7, 5, 3, 7, 10, 7, 5, 3, 0], 4.0, 0.42)
    line(AT('四二三年四月'), [0, None, -2, None, 0, 3, None, 2, None, 0, None, -2, 0], 4.0, 0.45, -12, 0.8)
    line(AT('虎牢被围二百日'), [0, 0, 3, 2, 0, -2, 0, 0], 3.6, 0.55, -12, 0.8)
    line(AT('滑台、洛阳、虎牢'), [7, 5, 3, 2, 0, None, 3, 2, 0], 3.6, 0.5)
    line(AT('这年十一月，拓跋嗣死了'), [12, 10, 7, 5, 3, 2, 0], 2.4, 0.5)
    line(S['s12']['start'], [0, 3, 5, 7, 5, 3, 0, 0], 2.2, 0.55)
    # 4) 拨弦动机（五声），稀疏
    def motif(t0, notes, step=0.9, gain=0.45, octave=0):
        for k, nidx in enumerate(notes):
            if nidx is None: continue
            add(dry, pluck(NOTE(PENT[nidx] + octave), 3.4), t0 + k * step + rng.uniform(-0.012, 0.012), gain * rng.uniform(0.8, 1.0), rng.uniform(-0.45, 0.45))
    motif(S['title']['start'] + 0.4, [0, None, 3, 2, None, 0], 0.6, 0.5)
    motif(S['s1']['body'], [3, 2, 0, None, 1, 2, None, None, 3, 4, 3, None, 2, 0], 1.3, 0.38)
    motif(S['s2']['body'], [0, None, None, 2, 1, None, None, 0, None, None, 3, 2, None, None, 1], 1.7, 0.32)
    motif(AT('刘裕私下回了'), [5, None, 4, 3, None, None, 2, None, 0], 1.1, 0.34, -12)
    motif(S['s5']['body'], [0, 2, 3, None, 3, 4, 5, None, 4, 3, 2, None, 3, 2, 0, None], 1.15, 0.36)
    motif(AT('虎牢，在今天河南荥阳'), [0, 2, 4, 5, None, 4, 5, 7, None, 5, 4, 2], 0.95, 0.34)
    motif(S['s6']['body'], [3, None, 2, None, 0, None, None, None, 4, None, 3, None, 2, None, None, None] * 2, 1.0, 0.3)
    motif(AT('第三招，是几封信'), [5, None, 4, None, 3, None, None, 2, None, 0, None, None] * 2, 0.9, 0.3)
    motif(AT('建康那边，三位辅政大臣'), [3, None, 2, None, 0, None, None, 1, None, 2, None, 0], 1.3, 0.34)
    motif(AT('元嘉六年'), [0, None, 2, 3, None, None, 4, 3, None, 0], 1.1, 0.4)
    # 5) 鼓
    def beat(t0, t1, bpm, pattern, gain=1.0):
        st = 60 / bpm / 2; k = 0; tt = t0
        while tt < t1:
            p = pattern[k % len(pattern)]
            if p == 'X': add(perc, taiko(58, 1.4), tt, 0.85 * gain, 0)
            elif p == 'x': add(perc, taiko(74, 0.9, 0.7), tt, 0.42 * gain, rng.uniform(-0.3, 0.3))
            elif p == 'o': add(perc, tom(118, 0.4), tt, 0.3 * gain, rng.uniform(-0.5, 0.5))
            elif p == 'i': add(perc, tom(156, 0.3), tt, 0.2 * gain, rng.uniform(-0.6, 0.6))
            tt += st; k += 1
    add(perc, taiko(48, 2.6, 1.3), S['title']['start'] + 0.15, 1.3)
    for sid in ('s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'):
        add(perc, taiko(52, 2.2, 1.1), S[sid]['card'][0] + 0.12, 1.0); add(fx, whoosh(1.1, 200, 1500)[::-1].copy(), S[sid]['card'][0] - 1.0, 0.22)
    beat(1.5, c0, 44, 'X...............', 0.7)
    beat(S['s1']['body'], AT('这年十一月'), 60, 'X...o...x...o.o.', 0.45)          # 北伐
    beat(AT('刘裕也难过'), S['s2']['start'] - 1, 48, 'X.......x.......', 0.4)
    beat(S['s2']['body'], S['s3']['start'] - 1, 50, 'X...............', 0.36)
    beat(S['s3']['body'], AT('到这年冬天'), 56, 'X.......x...o...', 0.45)
    for p, g in (('沈田子把王镇恶请到', 3.2), ('长史王修随即', 1.9)): add(perc, taiko(44, 3.0, 1.3), AT(p) + g, 1.15)   # 三条人命：三记重鼓
    add(perc, taiko(44, 3.0, 1.3), ET('王镇恶要反，所以') - 1.6, 1.15)
    beat(AT('人心又散又怕'), S['s4']['start'] - 1, 46, 'X...............', 0.5)
    beat(S['s4']['body'], AT('夏军三万追上来'), 66, 'X..ox.o.x..ox.oi', 0.42)        # 车队
    beat(AT('夏军三万追上来'), AT('刘义真一个人躲进草丛'), 88, 'X.oxX.oix.oxXooi', 0.8)
    beat(AT('刘义真一个人躲进草丛'), h1a, 52, 'X.......x.......', 0.4)
    add(perc, taiko(46, 3.2, 1.2), AT('北伐拿下的关中') - 0.1, 0.9)
    beat(AT('关中崩溃前后'), AT('虎牢，在今天河南荥阳'), 60, 'X...o...x...o...', 0.4)
    beat(AT('十月，魏将奚斤'), S['s7']['start'] - 1, 72, 'X..ox.o.X.oox.oi', 0.6)            # 魏军南下
    beat(S['s7']['body'], AT('第二招，他出城野战'), 76, 'X.oix.o.x.oix.oo', 0.5)                # 地道
    beat(AT('第二招，他出城野战'), AT('第三招，是几封信'), 88, 'X.oxX.oix.oxXooi', 0.75)             # 野战
    beat(AT('第三招，是几封信'), S['s8']['start'] - 1, 50, 'X...............', 0.35)
    beat(S['s8']['body'], AT('援军在哪儿'), 54, 'X.......x.......', 0.45)
    beat(AT('援军在哪儿'), AT('皆畏魏兵强'), 66, 'X...o...x...o.o.', 0.45)
    beat(AT('建康的朝廷里'), S['s9']['start'] - 1, 44, 'X...............', 0.4)
    beat(S['s9']['body'], h2a - 1, 52, 'X.....x.X.......', 0.62)                                      # 二百日：沉重的行进
    for p in ('拓跋嗣下令', '毛德祖被俘'): add(perc, taiko(46, 3.0, 1.1), AT(p) - 0.1, 0.8)
    add(perc, taiko(44, 3.4, 1.3), ET('一座孤城独自守了快一年') - 4.3, 0.9)                              # “不许”
    for l in [l for l in TL['lines'] if l['sec'] == 's12']: add(perc, taiko(48, 2.8, 1.0), l['start'] - 0.08, 0.95)
    # 6) 环境与音效
    add(amb, wind(S['s5']['start'] - S['s4']['start'] + 3, 180, 900), S['s4']['start'] - 1, 1.0)           # 青泥的寒风（静默段保留）
    add(amb, wind(h1b - h1a + 6, 260, 1400, 0.8), h1a - 2, 1.5)
    add(amb, wind(S['s1']['end'] - AT('刘裕也难过') + 2, 200, 800), AT('刘裕也难过') - 1, 0.6)
    add(amb, wind(S['s11']['end'] - AT('这年十一月，拓跋嗣死了') + 2, 200, 800), AT('这年十一月，拓跋嗣死了') - 1, 0.8)
    add(fx, rumble(AT('刘义真一个人躲进草丛') - AT('夏军三万追上来') + 2, 40), AT('夏军三万追上来') - 0.5, 0.8)
    add(fx, rumble(AT('第三招，是几封信') - AT('第二招，他出城野战'), 34), AT('第二招，他出城野战'), 0.7)
    add(fx, rumble(8, 26), AT('十月，魏将奚斤'), 0.6)
    add(fx, rumble(S['s10']['start'] - S['s9']['body'] - 8, 16), S['s9']['body'], 0.45)
    for a_, b_ in ((c0 + 3.2, c1 - 6), (h2a + 2.2, h2a + 4.8)):       # 井水被引走：几滴水声，越来越稀
        tt = a_; gap = 0.35
        while tt < b_: add(amb, drip(0.5, rng.uniform(1100, 1700)), tt, 0.5, rng.uniform(-0.4, 0.4)); tt += gap; gap *= 1.35
    add(fx, whoosh(1.6, 300, 1400), AT('夏军三万追上来') + 3.0, 0.4)
    mus = reverb(dry, 3.4, 0.5) + reverb(perc, 2.0, 0.28) * 0.9 + reverb(fx, 1.6, 0.22) * 0.75
    mus = mus * hush[:, None]
    out = mus + (low * (0.35 + 0.65 * hush))[:, None] + reverb(amb, 2.2, 0.35)
    return out

def main():
    os.makedirs(f"{ROOT}/audio", exist_ok=True)
    nar = narration(); sf.write(f"{ROOT}/audio/narration.wav", nar, SR, subtype='PCM_16')
    mus = music(); mus /= np.abs(mus).max() + 1e-9
    # 旁白时压低音乐
    w = int(0.05 * SR); e = np.sqrt(np.maximum(box(nar ** 2, w), 0))
    gate = (e > 0.02).astype(np.float64); k = int(0.45 * SR); gate = box(gate, k); gate = np.clip(gate * 2.2, 0, 1)
    k2 = int(0.25 * SR); gate = box(box(gate, k2 // 2), k2 // 2)
    g = 0.66 - 0.44 * gate                      # 无旁白 0.66，有旁白 0.22（约 -9.5 dB）
    mus = mus * g[:, None]
    fade = np.minimum(np.arange(N) / (0.8 * SR), 1) * np.minimum((N - np.arange(N)) / (3.0 * SR), 1); mus *= fade[:, None]
    sf.write(f"{ROOT}/audio/music.wav", mus, SR, subtype='PCM_16')
    mix = mus + nar[:, None] * 0.92
    mix = np.tanh(mix * 1.15) / np.tanh(1.15); mix = mix / np.abs(mix).max() * 0.89
    sf.write(f"{ROOT}/audio/mix.wav", mix, SR, subtype='PCM_16')
    def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("dur %.1f  nar %.1f dB  music %.1f dB  mix %.1f dB" % (N / SR, db(nar[np.abs(nar) > 0.01]), db(mus), db(mix)))
    for nm, a_, b_ in (('傅弘之', AT('弘之不屈'), AT('长安的百姓，把朱龄石') - 1), ('井', AT('接着，就是开头那口井') + 1.5, ET('孤城能做的')), ('野战', AT('第二招，他出城野战') + 2, AT('第三招，是几封信'))):
        print('  music level', nm, '%.1f dB' % db(mus[int(a_ * SR):int(b_ * SR)]))

if __name__ == "__main__":
    main()
