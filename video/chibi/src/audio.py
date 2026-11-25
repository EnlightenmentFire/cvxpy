# -*- coding: utf-8 -*-
"""配乐与音效：全部程序合成（鼓、号角、弦乐垫、固定音型、风、火、呼啸），无外部素材。
旁白取自云扬逐句音轨，时码不动；只在片尾追加静音。输出：
  music.wav（纯配乐）  sfx.wav（音效）  mix_music.wav（旁白+配乐+音效）  mix_nomusic.wav（旁白+音效）"""
import json, numpy as np, soundfile as sf, subprocess
from scipy import signal
ROOT = '/tmp/claude-0/-home-user-cvxpy/9a4786ae-0518-5e11-ad24-b93d03b9d022/scratchpad/'
TL = json.load(open(ROOT + 'chibi/timeline_edge.json'))
TAIL_EXTRA = 6.0
TOTAL = TL[-1]['start'] + TL[-1]['dur'] + TAIL_EXTRA
def S(i): return TL[i]['start']
def E(i): return TL[i]['start'] + TL[i]['dur']
SR = 48000; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(42)
def at(t): return int(t * SR)

# ---------------- 旁白 ----------------
v, sr = sf.read(ROOT + 'chibi/narr_fade.wav', dtype='float32')
assert sr == SR
voice = np.zeros(N, np.float32); voice[:len(v)] = v

# ---------------- 乐器 ----------------
def lp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2)); return signal.lfilter(b, a, x)
def bp(x, f0, f1, o=2): b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def saw(f, n, ph=0.0):
    t = np.arange(n) / SR; return 2 * ((f * t + ph) % 1.0) - 1
def taiko(gain=1.0, f0=55, dur=2.4):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.4 * np.exp(-t * 26)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 2.6) + 0.4 * np.sin(ph * 1.52) * np.exp(-t * 5)
    skin = bp(rng.normal(0, 1, n), 150, 1500) * np.exp(-t * 26) * 0.6
    return (body + skin) * gain
def horn(f, dur, gain=0.5, att=0.6, rel=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 1.0)
    ph = np.cumsum(f * vib) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * k * ph + k) for k in range(1, 9))
    x += 0.5 * sum((1 / k) * np.sin(2 * np.pi * k * ph * 1.003) for k in range(1, 7))
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel)
    bright = 900 + 1800 * np.minimum(1, t / (att * 1.5))
    y = lp(x * env, 1600)
    return y * gain / (np.abs(y).max() + 1e-9)
def string_note(f, dur, gain=0.4, att=0.03, dec=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    x = saw(f, n) + saw(f * 1.004, n, 0.3) + 0.5 * saw(f * 2, n, 0.6)
    env = np.minimum(1, t / att) * np.exp(-t / dec)
    return lp(x * env, 1100) * gain
def whoosh(dur=1.2, gain=0.5, up=True):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n); out = np.zeros(n)
    for k in range(0, n, 1024):
        u = k / n; fc = (300 + 3200 * u) if up else (3500 - 3000 * u)
        seg = x[k:k + 1024]; out[k:k + 1024] = bp(seg, max(80, fc * 0.6), min(SR / 2 - 100, fc * 1.4), 1)
    env = np.sin(np.pi * t / dur) ** 2
    return out * env * gain
def add(buf, t0, y, g=1.0):
    i = at(t0)
    if i >= len(buf): return
    m = min(len(y), len(buf) - i); buf[i:i + m] += (y[:m] * g).astype(np.float32)

music = np.zeros(N, np.float32); sfx = np.zeros(N, np.float32)

# 垫音：随章节换和弦（D 小调）
CH = [(0, ('D', 'A', 'F')), (S(13), ('D', 'A', 'F')), (S(43), ('Bb', 'F', 'D')), (S(72), ('G', 'D', 'Bb')), (S(76), ('D', 'A', 'F')),
      (S(99), ('A', 'E', 'C#')), (S(114), ('D', 'A', 'F')), (S(127), ('Bb', 'F', 'D')), (S(130), ('G', 'D', 'Bb')), (S(142), ('D', 'A', 'F')),
      (S(168), ('F', 'C', 'A')), (S(182), ('Bb', 'F', 'D')), (S(197), ('D', 'A', 'F')), (S(203), ('Bb', 'F', 'D')), (S(205), ('D', 'A', 'D'))]
NOTE = {'D': 73.42, 'A': 110.0, 'F': 87.31, 'Bb': 58.27, 'G': 98.0, 'C': 65.41, 'E': 82.41, 'C#': 69.3}
pad = np.zeros(N)
for k, (t0, chord) in enumerate(CH):
    t1 = CH[k + 1][0] if k + 1 < len(CH) else TOTAL
    n = at(t1 + 1.5) - at(t0); tt = np.arange(n) / SR
    y = np.zeros(n)
    for j, nm in enumerate(chord):
        f = NOTE[nm]
        for oc, g in ((1, 0.55), (2, 0.35), (4, 0.10)):
            y += g * (np.sin(2 * np.pi * f * oc * tt + j) + 0.3 * np.sin(2 * np.pi * f * oc * 1.003 * tt))
    env = np.minimum(1, tt / 1.5) * np.minimum(1, np.maximum(0, (n / SR - tt)) / 1.5)
    seg = y * env
    i0 = at(t0); m = min(n, N - i0); pad[i0:i0 + m] += seg[:m]
pad = lp(pad, 900) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.05 * np.arange(N) / SR))
music += (pad / np.abs(pad).max() * 0.22).astype(np.float32)

# 固定音型（紧张段）
def ostinato(t0, t1, bpm=104, root=73.42, gain=0.30, ramp_up=True):
    beat = 60 / bpm / 2; pat = [1, 1, 1.189, 1, 0.891, 0.891, 1, 0.749]
    t = t0; k = 0
    while t < t1:
        u = (t - t0) / max(1e-6, t1 - t0)
        g = gain * (0.55 + 0.45 * u if ramp_up else 1.0) * (1.15 if k % 4 == 0 else 1.0)
        add(music, t, string_note(root * pat[k % 8], beat * 1.6, g)); t += beat; k += 1
ostinato(0.0, S(13) - 0.2, gain=0.26)
ostinato(S(19), E(27), gain=0.20)
ostinato(S(76), E(84), gain=0.18)
ostinato(S(114), S(127) + 0.6, gain=0.22)
ostinato(S(127) + 0.6, E(130), bpm=120, gain=0.34, ramp_up=False)
ostinato(S(133), E(136), bpm=120, gain=0.28)
ostinato(S(159), E(166), bpm=96, gain=0.18)
ostinato(S(197), E(200), gain=0.20)

# 鼓
hits = [(0.30, 1.2, 46), (1.65, 1.0, 50), (S(1) + 0.1, 0.7, 56), (S(2) + 0.1, 0.8, 52), (S(9), 1.2, 44), (S(9) + 0.6, 0.8, 58)]
for i in (13, 43, 99, 142, 182): hits += [(S(i) + 0.05, 1.2, 44), (S(i) + 0.75, 0.7, 56)]
hits += [(S(22) + 1.0, 0.7, 54), (S(23) + 3.0, 0.9, 50), (S(25) + 1.6, 0.6, 56), (S(41) + 0.1, 1.0, 48), (S(45) + 0.1, 0.7, 52), (S(46) + 0.1, 0.7, 52)]
hits += [(S(68) + 0.7, 1.4, 42), (S(69) + 0.2, 0.8, 50), (S(76) + 0.4, 0.8, 50), (S(79) + 0.4, 0.9, 48), (S(84) + 0.3, 0.8, 50)]
hits += [(S(95) + 0.3, 0.8, 52), (S(98) + 0.4, 1.0, 44), (S(102) + 0.4, 0.8, 50), (S(105) + 0.1, 0.9, 50), (S(116) + 0.2, 0.7, 54), (S(118) + 0.4, 0.9, 48)]
t = S(127) + 0.6
while t < E(129):
    hits.append((t, 1.0, 46)); hits.append((t + 0.29, 0.45, 60)); t += 0.58
t = S(136)
while t < E(136):
    hits.append((t, 0.9, 50)); t += 0.43
hits += [(S(141) + 0.2, 1.2, 42), (S(144) + 0.2, 0.7, 52), (S(157) + 0.2, 0.7, 52), (S(172) + 0.6, 0.8, 50), (S(179) + 0.2, 1.0, 46)]
hits += [(S(197) + 0.1, 1.1, 46), (S(203) + 0.2, 0.9, 46), (S(204) + 0.1, 1.3, 42)]
tq = TL[205]['subs'][-1][1] + 0.4
hits += [(tq, 1.0, 44), (TOTAL - 3.0, 1.3, 42), (TOTAL - 2.4, 0.8, 56)]
for t0, g, f0 in hits: add(music, t0, taiko(g, f0), 0.55)

# 号角
for t0, f, dur, g in ((0.05, 73.42, 3.6, 0.40), (0.9, 110.0, 2.8, 0.25), (S(9) + 0.1, 73.42, 3.2, 0.35), (S(99) + 0.1, 110.0, 3.0, 0.3),
                      (S(127) + 0.6, 73.42, 4.0, 0.42), (S(128) + 0.2, 87.31, 3.2, 0.3), (S(130), 65.41, 3.0, 0.32), (S(136) + 0.1, 110.0, 4.0, 0.32),
                      (tq + 0.2, 73.42, 4.5, 0.3), (TOTAL - 3.0, 73.42, 3.0, 0.35), (TOTAL - 3.0, 110.0, 3.0, 0.22)):
    add(music, t0, horn(f, dur, g))

# ---------------- 音效 ----------------
# 呼啸：卡片砸下、镜头大移动、章节
for t0 in [0.2, S(1), S(4) - 0.5, S(9) - 0.2, S(41) - 0.1, S(45), S(76) - 0.3, S(101) - 0.2, S(117) - 0.1, S(127) + 0.3, S(130) - 0.2,
           S(142) - 0.3, S(168) - 0.3, S(197) - 0.1, S(203) - 0.2] + [S(i) - 0.2 for i in (13, 43, 99, 182)]:
    add(sfx, max(0, t0), whoosh(1.1, 0.35))
# 风：S124–S139
def noise_bed(t0, t1, lo, hi, gain, mod=0.25):
    n = at(t1) - at(t0); tt = np.arange(n) / SR
    y = bp(rng.normal(0, 1, n), lo, hi) * (0.7 + 0.3 * np.sin(2 * np.pi * mod * tt + rng.uniform(0, 6)))
    env = np.minimum(1, tt / 1.2) * np.minimum(1, (n / SR - tt) / 1.5)
    add(sfx, t0, y * env * gain)
noise_bed(S(124), E(130), 200, 1400, 0.10)
noise_bed(S(131), E(139), 200, 1400, 0.08)
noise_bed(S(161), E(163), 2000, 7000, 0.04, 1.3)   # 雨
# 火：噼啪
def crackle(t0, t1, gain):
    n = at(t1) - at(t0); tt = np.arange(n) / SR
    y = bp(rng.normal(0, 1, n), 300, 2500) * 0.25
    pops = np.zeros(n); idx = rng.integers(0, n, int((t1 - t0) * 35)); pops[idx] = rng.uniform(0.3, 1.0, len(idx)) * rng.choice([-1, 1], len(idx))
    pops = signal.lfilter([1], [1, -0.85], pops); pops = bp(pops, 800, 6000)
    env = np.minimum(1, tt / 0.8) * np.minimum(1, (n / SR - tt) / 1.5)
    add(sfx, t0, (y + pops * 0.6) * env * gain)
crackle(S(127) + 0.6, E(131), 0.30)
crackle(S(159), E(160), 0.12)
crackle(S(166), E(166), 0.12)

# ---------------- 混音 ----------------
def env_follow(x, win=0.05, rel=0.4):
    b = int(win * SR); e = np.sqrt(np.convolve(x.astype(np.float64) ** 2, np.ones(b) / b, 'same'))
    k = np.exp(-1 / (rel * SR / 256)); out = np.zeros_like(e); vv = 0.0
    for i in range(0, len(e), 256):
        m = e[i:i + 256].max(); vv = max(m, vv * k); out[i:i + 256] = vv
    return out
ve = env_follow(voice)
speech_rms = np.sqrt(np.mean(voice[np.abs(voice) > 0.01] ** 2))
mus_rms = np.sqrt(np.mean(music ** 2) + 1e-12)
# 人声时音乐比人声低约 22 dB；停顿时抬高约 9 dB；火攻高潮再加 4 dB
speaking = np.clip(ve / (speech_rms * 0.35), 0, 1)
g_db = -19.8 + 9.0 * (1 - speaking)
tt = np.arange(N) / SR
g_db += 4.0 * ((tt >= S(127) + 0.6) & (tt < E(130)))
g_db += 3.0 * (tt < 3.5) + 3.0 * (tt >= TOTAL - 3.2)
g = (speech_rms / mus_rms) * 10 ** (g_db / 20)
g = signal.lfilter([1 - 0.9995], [1, -0.9995], g)   # 平滑
music_d = (music * g).astype(np.float32)
sfx_rms = np.sqrt(np.mean(sfx[np.abs(sfx) > 1e-4] ** 2) + 1e-12)
sfx_g = (speech_rms / sfx_rms) * 10 ** (-17 / 20)
sfx_d = (sfx * sfx_g * (1 - 0.5 * speaking)).astype(np.float32)
sf.write(ROOT + 'chibi2/mix_music.wav', voice + music_d + sfx_d, SR, subtype='FLOAT')
sf.write(ROOT + 'chibi2/mix_nomusic.wav', voice + sfx_d, SR, subtype='FLOAT')
sf.write(ROOT + 'chibi2/music_only.wav', music_d, SR, subtype='FLOAT')
print('written', TOTAL, 'speech_rms', speech_rms)
