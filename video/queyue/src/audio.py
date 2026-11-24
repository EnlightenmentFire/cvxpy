# -*- coding: utf-8 -*-
"""合成配乐与音效（全部由本脚本用 numpy 生成，无外部素材），并与旁白混音。
输出：audio/narration.wav、audio/music.wav、audio/mix.wav（48 kHz 立体声）。"""
import json, os, sys, numpy as np, soundfile as sf, librosa
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
TL = json.load(open(f"{ROOT}/src/timeline.json"))
TOTAL = TL['total'] + 0.5
N = int(TOTAL * SR)
rng = np.random.default_rng(417)
A = lambda sec, k: [l for l in TL['lines'] if l['sec'] == sec and l['k'] == k][0]['start']
E = lambda sec, k: [l for l in TL['lines'] if l['sec'] == sec and l['k'] == k][0]['end']
S = TL['secs']

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
    w = int(0.03 * SR); e = np.sqrt(np.convolve(buf ** 2, np.ones(w) / w, 'same')) + 1e-6
    thr = 0.09; g = np.where(e > thr, (thr / e) ** 0.45, 1.0); g = np.convolve(g, np.ones(w) / w, 'same')
    buf = buf * g; buf = buf / np.abs(buf).max() * 0.86
    return buf

# ---------- 配乐 ----------
def music():
    dry = np.zeros((N, 2)); perc = np.zeros((N, 2)); fx = np.zeros((N, 2))
    # 1) 持续低音（D），全片
    t = np.arange(N) / SR
    drone = np.zeros(N)
    for f, a in ((36.71, 0.5), (73.42, 0.42), (110.0, 0.16), (146.83, 0.08)):
        drone += a * np.sin(2 * np.pi * f * t + 0.6 * np.sin(2 * np.pi * 0.05 * t + f)) * (1 + 0.25 * np.sin(2 * np.pi * (0.03 + f / 9000) * t))
    inten = np.interp(t, [0, S['title']['start'], S['s1']['start'], S['s3']['start'], S['s4']['start'], A('s4', 3), A('s4', 9), S['s5']['start'], S['s6']['start'], S['s7']['start'], S['s8']['start'], TOTAL - 4, TOTAL],
                      [0.5, 0.8, 0.55, 0.6, 0.75, 1.0, 0.9, 0.55, 0.6, 0.7, 0.6, 0.5, 0.0])
    dry[:, 0] += drone * inten * 0.16; dry[:, 1] += drone * inten * 0.16
    # 2) 和声垫底：Dm / Bb / Gm / A(sus)，每和弦 8 秒；陆章转大调提亮，柒章用下行
    chords = {'Dm': [0, 7, 12, 15], 'Bb': [-4, 3, 8, 12], 'Gm': [-7, 0, 5, 10], 'Asus': [-5, 2, 7, 12], 'F': [-9, 3, 7, 12], 'C': [-2, 5, 10, 14], 'Em7b5': [2, 5, 8, 12]}
    plan = []
    def seq(t0, t1, names, step=8.0, gain=1.0, cut=650):
        k = 0; tt = t0
        while tt < t1 - 1: plan.append((tt, min(step, t1 - tt) + 2.5, names[k % len(names)], gain, cut)); tt += step; k += 1
    seq(0, S['title']['start'], ['Dm', 'Bb'], 9, 0.9)
    seq(S['title']['start'], S['s1']['start'], ['Dm'], 4, 1.2, 900)
    seq(S['s1']['start'], S['s2']['start'], ['Dm', 'Gm', 'Bb', 'Asus'], 8, 0.8)
    seq(S['s2']['start'], S['s3']['start'], ['Gm', 'Dm', 'Em7b5', 'Asus'], 8, 0.75, 560)
    seq(S['s3']['start'], S['s4']['start'], ['Dm', 'Bb', 'Gm', 'Asus'], 8, 0.9, 700)
    seq(S['s4']['start'], S['s5']['start'], ['Dm', 'Dm', 'Bb', 'Asus'], 6, 1.1, 800)
    seq(S['s5']['start'], S['s6']['start'], ['Dm', 'Gm', 'Bb', 'Asus'], 8, 0.7, 600)
    seq(S['s6']['start'], S['s7']['start'], ['F', 'C', 'Dm', 'Bb'], 5.5, 1.0, 900)
    seq(S['s7']['start'], S['s8']['start'], ['Dm', 'Bb', 'Gm', 'Em7b5', 'Asus', 'Dm'], 9, 0.85, 560)
    seq(S['s8']['start'], TOTAL - 1, ['Bb', 'Gm', 'Dm', 'Dm'], 8, 1.0, 700)
    for (t0, d, nm, g, cut) in plan:
        add(dry, pad([NOTE(s - 12) for s in chords[nm]], d, cut), t0 - 1.2, 0.5 * g, rng.uniform(-0.25, 0.25))
    # 3) 拨弦动机（五声）
    def motif(t0, notes, step=0.9, gain=0.55, octave=0):
        for k, nidx in enumerate(notes):
            if nidx is None: continue
            add(dry, pluck(NOTE(PENT[nidx] + octave), 3.4), t0 + k * step + rng.uniform(-0.012, 0.012), gain * rng.uniform(0.8, 1.0), rng.uniform(-0.45, 0.45))
    motif(1.0, [0, None, 3, 2, None, 0], 1.3, 0.5)
    motif(S['s1']['body'], [3, 2, 0, None, 1, 2, None, None, 3, 4, 3, None, 2, 0], 1.25, 0.42)
    motif(S['s1']['body'] + 20, [5, 4, 3, None, 2, 3, None, 0], 1.25, 0.4)
    motif(S['s2']['body'], [0, None, None, 2, 1, None, None, 0, None, None, 3, 2, None, None, 1], 1.6, 0.36)
    motif(S['s3']['body'], [0, 2, 3, None, 3, 4, 5, None, 4, 3, 2, None, 3, 2, 0, None], 1.0, 0.4)
    motif(S['s3']['body'] + 18, [0, 2, 3, None, 3, 4, 5, None, 7, 5, 4, None, 5, 4, 3, None], 1.0, 0.4)
    motif(S['s5']['body'], [3, None, 2, None, 0, None, None, None, 4, None, 3, None, 2, None, None, None] * 2, 0.8, 0.32)
    motif(S['s6']['body'], [0, 2, 4, 5, None, 4, 5, 7, None, 5, 4, 2, None, 3, 4, 5, 7, None], 0.72, 0.4)
    for k in range(7): motif(S['s7']['body'] + k * 8.6, [5, None, 4, 3, None, None, 2, None, 0], 0.95, 0.36, 0 if k % 2 else -12)
    motif(S['s8']['body'], [3, None, 2, None, 0], 1.4, 0.4)
    motif(A('s8', 6), [0, None, 2, 3, None, None, 4, 3, None, 0], 1.1, 0.45)
    # 4) 鼓
    def beat(t0, t1, bpm, pattern, gain=1.0):
        st = 60 / bpm / 2; k = 0; tt = t0
        while tt < t1:
            p = pattern[k % len(pattern)]
            if p == 'X': add(perc, taiko(58, 1.4), tt, 0.85 * gain, 0)
            elif p == 'x': add(perc, taiko(74, 0.9, 0.7), tt, 0.42 * gain, rng.uniform(-0.3, 0.3))
            elif p == 'o': add(perc, tom(118, 0.4), tt, 0.3 * gain, rng.uniform(-0.5, 0.5))
            elif p == 'i': add(perc, tom(156, 0.3), tt, 0.2 * gain, rng.uniform(-0.6, 0.6))
            tt += st; k += 1
    beat(1.2, S['title']['start'] - 1, 50, 'X.......x.......', 0.8)
    add(perc, taiko(48, 2.6, 1.3), S['title']['start'] + 0.15, 1.3)
    for sid in ('s1', 's2', 's3', 's4', 's5', 's6', 's7'):
        add(perc, taiko(52, 2.2, 1.1), S[sid]['card'][0] + 0.12, 1.0); add(fx, whoosh(1.1, 200, 1500)[::-1].copy(), S[sid]['card'][0] - 1.0, 0.25)
    beat(S['s1']['body'], S['s2']['start'] - 1, 60, 'X...o...x...o.o.', 0.5)
    beat(S['s2']['body'], S['s3']['start'] - 1, 54, 'X.......x.......', 0.42)
    beat(S['s3']['body'], A('s3', 4), 72, 'X..oi.o.x..oi.oo', 0.5)
    beat(A('s3', 4), A('s3', 6), 72, 'X.......x.......', 0.4)
    beat(A('s3', 6), S['s4']['start'] - 1, 72, 'X.ooi.o.x.ooi.oo', 0.62)
    beat(S['s4']['body'], A('s4', 3) - 0.6, 84, 'X..ox.o.X.oox.oi', 0.6)
    beat(A('s4', 3) - 0.6, A('s4', 6) + 0.9, 84, 'X.oxX.oix.oxXooi', 0.85)
    beat(A('s4', 6) + 0.9, E('s4', 8) - 1.6, 84, 'X...............', 0.4)
    beat(E('s4', 8) - 1.6, A('s4', 9) + 0.5, 84, 'X.oxX.oix.oxXooi', 0.9)
    beat(A('s4', 9) + 0.5, S['s5']['start'] - 1, 84, 'X...x...X..ox...', 0.6)
    beat(S['s5']['body'], A('s5', 6), 60, 'X...o...x...o...', 0.4)
    beat(A('s5', 6), S['s6']['start'] - 1, 66, 'X..ox.o.x..ox.oi', 0.55)
    beat(S['s6']['body'], S['s7']['start'] - 1, 76, 'X.oix.o.X.oix.oo', 0.55)
    beat(S['s7']['body'], S['s8']['start'] - 1, 46, 'X...............', 0.5)
    for k in (3, 4, 5): add(perc, taiko(50, 2.4, 1.0), A('s8', k) - 0.05, 0.9)
    add(perc, taiko(46, 3.0, 1.2), A('s8', 6) - 0.1, 0.9)
    # 5) 音效
    add(fx, water(A('s1', 2) + 30)[: int((S['s1']['end'] - A('s1', 2) + 0.5) * SR)], A('s1', 2) - 0.5, 1.0)
    add(fx, water(S['s3']['end'] - S['s3']['body']), S['s3']['body'], 0.7)
    vol = A('s4', 4) + 0.15
    for k in range(3): add(fx, whoosh(0.7, 900, 5200), vol + 1.7 * k - 0.08, 1.0, 0); add(perc, taiko(66, 1.0, 1.4), vol + 1.7 * k, 0.9)
    cold_v = None
    mass0, rout = A('s4', 3) - 0.6, A('s4', 9) + 0.5
    r = rumble(rout + 5 - mass0, 46); n = len(r); tt = np.arange(n) / SR
    r *= np.minimum(tt / 5.0, 1) * np.minimum((tt[-1] - tt) / 5.0 + 0.05, 1)
    d0, d1 = A('s4', 6) + 0.9, E('s4', 8) - 1.6
    duck = 1 - 0.75 * (np.clip((tt + mass0 - d0) / 0.6, 0, 1) * np.clip((d1 - tt - mass0) / 0.6, 0, 1)); add(fx, r * duck, mass0, 1.0)
    add(fx, rumble(A('s4', 3) - S['s4']['body'], 14), S['s4']['body'], 0.6)
    add(fx, rumble(12, 40), 4.5, 0.7)                                   # 冷开场
    add(fx, rumble(E('s5', 9) - A('s5', 6), 30), A('s5', 6) + 2, 0.6)   # 尉武
    tk = d0 + 1.1 + 1.0
    while tk < d1: add(fx, clank(), tk, 1.0, -0.2); add(fx, whoosh(0.35, 1500, 6000), tk + 0.01, 0.6, 0.3); tk += 2.3
    tk = d1 + 0.3
    while tk < rout: add(fx, clank(0.4), tk, 0.45, rng.uniform(-0.6, 0.6)); tk += rng.uniform(0.35, 0.7)
    add(fx, whoosh(2.2, 300, 1200), rout - 0.2, 0.7)
    for k in range(3): add(perc, taiko(60, 1.6, 1.2), A('s7', 5) + 2.2 + k * (E('s7', 5) - A('s7', 5) - 2.6) / 3 + 0.6, 0.8)
    add(fx, whoosh(1.4, 400, 2600), A('s3', 3) + 2.0, 0.3)             # 白毦
    mix = reverb(dry, 3.2, 0.45) + reverb(perc, 2.0, 0.28) * 0.9 + reverb(fx, 1.6, 0.22) * 0.75
    return mix

def main():
    os.makedirs(f"{ROOT}/audio", exist_ok=True)
    nar = narration(); sf.write(f"{ROOT}/audio/narration.wav", nar, SR, subtype='PCM_16')
    mus = music(); mus /= np.abs(mus).max() + 1e-9
    # 旁白时压低音乐
    w = int(0.05 * SR); e = np.sqrt(np.convolve(nar ** 2, np.ones(w) / w, 'same'))
    gate = (e > 0.02).astype(np.float64); k = int(0.45 * SR); gate = np.convolve(gate, np.ones(k) / k, 'same'); gate = np.clip(gate * 2.2, 0, 1)
    k2 = int(0.25 * SR); gate = np.convolve(gate, np.hanning(k2) / np.hanning(k2).sum(), 'same')
    g = 0.68 - 0.41 * gate                      # 无旁白 0.62，有旁白 0.22（约 -9 dB）
    mus = mus * g[:, None]
    fade = np.minimum(np.arange(N) / (0.8 * SR), 1) * np.minimum((N - np.arange(N)) / (3.0 * SR), 1); mus *= fade[:, None]
    sf.write(f"{ROOT}/audio/music.wav", mus, SR, subtype='PCM_16')
    mix = mus + nar[:, None] * 0.92
    mix = np.tanh(mix * 1.15) / np.tanh(1.15); mix = mix / np.abs(mix).max() * 0.89
    sf.write(f"{ROOT}/audio/mix.wav", mix, SR, subtype='PCM_16')
    def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("dur %.1f  nar %.1f dB  music %.1f dB  mix %.1f dB" % (N / SR, db(nar[np.abs(nar) > 0.01]), db(mus), db(mix)))

if __name__ == "__main__":
    main()
