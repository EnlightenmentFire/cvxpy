# -*- coding: utf-8 -*-
"""音频：旁白拼接；程序合成的配乐（战鼓、号角、弦乐铺底、悬疑拨弦）与音效（金鼓呐喊、山谷回声、箭雨、重击）；
侧链压低配乐；整体 -15 LUFS / -1.5 dBTP。全部原创合成，无外部素材。输出 mix.wav（成片）与 nomusic.wav（无配乐版）。"""
import numpy as np, subprocess, os, re, soundfile as sf
from scipy import signal
from timeline import TL
from script import BEATS
SR = 48000
T = TL(); S, E = T.S, T.E; N = int((T.total + 0.5) * SR)
rng = np.random.default_rng(42)
PROC = '/tmp/claude-0/work/tts/proc/'
OUTD = '/tmp/claude-0/work/vid/'

def place(buf, t0, y, g=1.0):
    i = int(max(0, t0) * SR); n = min(len(y), len(buf) - i)
    if n > 0: buf[i:i + n] += y[:n] * g

def narration():
    out = np.zeros(N, np.float32)
    for a in T.audio:
        p = PROC + a['id'] + '.wav'
        if not os.path.exists(p): continue
        w, sr = sf.read(p, dtype='float32'); place(out, a['t'], w)
    return out

# ---------- 乐器 ----------
def adsr(n, a=0.01, d=0.1, s=0.7, r=0.3):
    t = np.arange(n) / SR; L = n / SR; e = np.ones(n) * s
    e[t < a] = t[t < a] / a
    m = (t >= a) & (t < a + d); e[m] = 1 - (1 - s) * (t[m] - a) / d
    m = t > L - r; e[m] *= np.clip((L - t[m]) / r, 0, 1)
    return e
def drum(f0=55, dur=2.2, tone=1.0, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.6 * np.exp(-t * 28)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 3.0) + 0.45 * np.sin(ph * 1.5 + 0.3) * np.exp(-t * 6)
    b, a = signal.butter(2, [180 / (SR / 2), 1600 / (SR / 2)], 'band'); skin = signal.lfilter(b, a, rng.normal(0, 1, n)) * np.exp(-t * 30) * 0.55 * tone
    return (body + skin) * g
def tick(g=0.4):
    n = int(0.3 * SR); t = np.arange(n) / SR; b, a = signal.butter(2, [900 / (SR / 2), 4000 / (SR / 2)], 'band')
    return (signal.lfilter(b, a, rng.normal(0, 1, n)) * np.exp(-t * 55) + 0.5 * np.sin(2 * np.pi * 230 * t) * np.exp(-t * 40)) * g
def saw(f, n, det=(-0.12, 0.0, 0.11)):
    t = np.arange(n) / SR; y = np.zeros(n)
    for d in det:
        ph = (f * (1 + d / 100) * t + rng.uniform()) % 1.0; y += 2 * ph - 1
    return y / len(det)
def horn(f, dur, g=0.5, vib=4.8):
    """号角：锯齿波 + 共振峰带通 + 缓起音 + 轻颤音。"""
    n = int(dur * SR); t = np.arange(n) / SR
    fm = f * (1 + 0.004 * np.sin(2 * np.pi * vib * t) * np.clip(t / 0.6, 0, 1)) * (1 - 0.03 * np.exp(-t * 12))
    ph = np.cumsum(fm) / SR; y = 2 * (ph % 1.0) - 1
    out = np.zeros(n)
    for fc, bw, gg in ((500, 260, 1.0), (1100, 400, 0.6), (2400, 700, 0.25)):
        b, a = signal.butter(2, [max(40, fc - bw / 2) / (SR / 2), (fc + bw / 2) / (SR / 2)], 'band'); out += signal.lfilter(b, a, y) * gg
    bright = np.clip(t / 0.35, 0, 1)
    b, a = signal.butter(1, 3000 / (SR / 2)); out = signal.lfilter(b, a, out)
    return out * adsr(n, 0.18, 0.2, 0.85, min(0.6, dur * 0.4)) * g * (0.7 + 0.3 * bright)
def strings(freqs, dur, g=0.3, att=1.5, rel=2.0, cut=1800):
    n = int(dur * SR); y = np.zeros(n)
    for f in freqs: y += saw(f, n, (-0.18, -0.05, 0.07, 0.16))
    b, a = signal.butter(2, cut / (SR / 2)); y = signal.lfilter(b, a, y)
    t = np.arange(n) / SR; y *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.21 * t)
    return y * adsr(n, att, 0.5, 0.9, rel) * g / max(1, len(freqs)) * 2
_PC = {}
def pluck(f, g=0.5, dur=2.5):
    if (f, dur) in _PC: return _PC[(f, dur)] * g
    n = int(dur * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p)
    b, a = signal.butter(1, 2200 / (SR / 2)); buf = signal.lfilter(b, a, buf)
    y = np.zeros(n); y[:p] = buf
    for i in range(p, n): y[i] = 0.4965 * (y[i - p] + y[i - p + 1])
    _PC[(f, dur)] = y
    return y * g
def shout(dur=3.0, g=0.6, voices=40):
    """万人呐喊：多声部元音共振峰噪声 + 音高滑动。"""
    n = int(dur * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for v in range(voices):
        f0 = rng.uniform(110, 230); st = rng.uniform(0, 0.4)
        ph = np.cumsum(f0 * (1 + 0.12 * np.clip((t - st) / 0.5, 0, 1) - 0.06 * np.clip((t - st - 1.2) / 1.5, 0, 1))) / SR
        src = (2 * (ph % 1) - 1) + 0.3 * rng.normal(0, 1, n)
        e = np.clip((t - st) / 0.15, 0, 1) * np.clip((dur - t) / 1.2, 0, 1)
        y += src * e * rng.uniform(0.5, 1.0)
    out = np.zeros(n)
    for fc, bw, gg in ((750, 300, 1.0), (1200, 400, 0.7), (2600, 600, 0.3)):   # 「啊」
        b, a = signal.butter(2, [(fc - bw / 2) / (SR / 2), (fc + bw / 2) / (SR / 2)], 'band'); out += signal.lfilter(b, a, y) * gg
    return out / voices * g * 3
def echo(x, delays=(0.32, 0.71, 1.18, 1.75), gains=(0.45, 0.3, 0.2, 0.12)):
    y = x.copy()
    for d, gg in zip(delays, gains):
        k = int(d * SR); b, a = signal.butter(1, 2200 / (SR / 2)); y[k:] += signal.lfilter(b, a, x[:-k]) * gg
    return y
def whoosh(dur=0.9, g=0.4, up=True):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.normal(0, 1, n); y = np.zeros(n)
    fc = np.linspace(300, 3000, n) if up else np.linspace(3000, 300, n)
    for i in range(0, n, 512):
        b, a = signal.butter(2, [max(50, fc[i] * 0.7) / (SR / 2), fc[i] * 1.3 / (SR / 2)], 'band'); y[i:i + 512] = signal.lfilter(b, a, x[i:i + 512])
    return y * np.sin(np.pi * t / dur) ** 2 * g
def arrows_sfx(dur=2.5, g=0.25, k=14):
    n = int(dur * SR); y = np.zeros(n)
    for i in range(k):
        st = rng.uniform(0, dur - 0.5); L = rng.uniform(0.25, 0.45); m = int(L * SR); tt = np.arange(m) / SR
        f = np.linspace(rng.uniform(2600, 3400), rng.uniform(1200, 1800), m)
        w = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / L) ** 2 * 0.3 + rng.normal(0, 0.05, m) * np.sin(np.pi * tt / L)
        j = int(st * SR); y[j:j + m] += w
    return y * g
def reverb(x, wet=0.3, tail=2.6):
    ir_n = int(tail * SR); t = np.arange(ir_n) / SR
    ir = rng.normal(0, 1, ir_n) * np.exp(-t * 2.4); b, a = signal.butter(2, 2600 / (SR / 2)); ir = signal.lfilter(b, a, ir); ir[:int(0.015 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    return x + wet * signal.oaconvolve(x, ir)[:len(x)]

# ---------- 编曲 ----------
Dm = [73.42, 110.0, 146.83, 174.61]; Bb = [58.27, 116.54, 146.83, 174.61]; Gm = [49.0, 98.0, 146.83, 196.0]; A7 = [55.0, 110.0, 138.59, 164.81]; F = [43.65, 87.31, 130.81, 174.61]
def section_bounds():
    secs = {}
    for b in BEATS: secs.setdefault(b['sec'], []).append(b['id'])
    out = {}
    for s, ids in secs.items():
        t0 = T.chap[s][0] if s in T.chap else 0.0
        out[s] = (t0, E(ids[-1]) + 0.6)
    return out
SB = section_bounds()

def score():
    mus = np.zeros(N + 10 * SR); sfx = np.zeros(N + 10 * SR)
    def M(t0, y, g=1.0): place(mus, t0, y, g)
    def X(t0, y, g=1.0): place(sfx, t0, y, g)
    # ===== 开场：金鼓 + 呐喊回声（声音钩子）=====
    X(0.0, echo(drum(46, 3.0, 1.3)), 1.0); X(0.0, echo(shout(3.2, 0.9)), 0.9)
    for k, tt in enumerate((0.42, 0.84, 1.26, 1.68, 2.1, 2.52)): X(tt, drum(58 if k % 2 else 50, 1.6, 1.0), 0.75)
    X(0.3, arrows_sfx(3.0, 0.3, 18), 1.0)
    M(0.05, horn(146.83, 2.6, 0.55)); M(0.05, horn(220.0, 2.6, 0.4)); M(2.4, horn(174.61, 1.6, 0.4)); M(3.6, horn(146.83, 3.2, 0.45))
    # 战鼓持续到 h04
    t = 2.9; i = 0
    while t < E('h03'):
        M(t, drum(52, 1.8, 0.9), 0.55 + 0.1 * (i % 2));
        if i % 2: M(t + 0.33, tick(0.3))
        t += 0.66; i += 1
    M(S('h03') + 7.0, echo(drum(42, 3.0, 1.2)), 0.9)
    M(0.0, strings(Dm, E('h04') + 1, 0.35, 0.3, 2.0, 1400))
    # h05–h14：悬疑推进
    t0, t1 = S('h05') - 0.5, E('h14') + 1.0
    M(t0, strings([73.42, 146.83, 220.0], t1 - t0, 0.28, 2.0, 2.0, 1100))
    t = S('h07'); seq = [146.83, 174.61, 220.0, 174.61]; k = 0
    while t < S('h12'): M(t, pluck(seq[k % 4], 0.22)); t += 0.48; k += 1
    for bid in ('h09', 'h12', 'h13', 'h14'): M(S(bid) - 0.1, drum(48, 2.2, 1.0), 0.6)
    M(S('h12') + 3.4, horn(146.83, 2.2, 0.35)); M(S('h12') + 5.4, horn(220.0, 2.6, 0.38))
    # ===== 章节卡 =====
    for sec, (c0, c1) in T.chap.items():
        M(c0 + 0.1, echo(drum(44, 3.0, 1.2)), 0.9); M(c0 + 0.15, horn(146.83 if sec != 4 else 174.61, 2.0, 0.42)); M(c0 + 0.15, horn(220.0, 2.0, 0.28))
        X(c0 - 0.2, whoosh(0.7, 0.25))
    # ===== 壹 入蜀：悬疑弦乐 + 拨弦 ostinato =====
    a, b = SB[1]
    chords = [Dm, Bb, Gm, A7]; L = 8.0; t = T.chap[1][1]; k = 0
    while t < b:
        M(t, strings(chords[k % 4][1:], min(L + 2, b - t + 1), 0.30, 2.0, 2.5, 1000)); M(t, strings(chords[k % 4][:1], min(L + 2, b - t + 1), 0.25, 2.0, 2.5, 600)); t += L; k += 1
    t = T.chap[1][1] + 0.3; seq = [146.83, 174.61, 220.0, 196.0, 174.61, 146.83, 130.81, 146.83]; k = 0
    while t < b:
        M(t, pluck(seq[k % 8], 0.18)); t += 0.5; k += 1
    for bid in ('r08', 'r12b', 'r16', 'r25'): M(S(bid) - 0.15, drum(50, 2.0, 0.8), 0.55)
    M(S('r27') - 0.1, echo(drum(44, 2.6, 1.0)), 0.7); M(S('r33'), drum(40, 3.0, 1.1), 0.8)
    # ===== 贰 取成都：节奏加快 =====
    a, b = SB[2]
    t = T.chap[2][1]; k = 0
    while t < b:
        M(t, strings(chords[k % 4], min(6.5, b - t + 1), 0.30, 1.0, 2.0, 1300)); t += 6.0; k += 1
    turn = S('c04') + 1.0
    X(turn, echo(drum(36, 3.5, 1.5)), 1.1); X(turn - 0.6, whoosh(0.7, 0.4)); M(turn, horn(110.0, 3.0, 0.55)); M(turn, horn(164.81, 3.0, 0.4))
    t = turn + 0.5; i = 0
    while t < E('c12'):
        M(t, drum(54, 1.6, 0.9), 0.42 if i % 4 else 0.62)
        if i % 2: M(t + 0.25, tick(0.22))
        t += 0.52; i += 1
    X(S('c07') + 1, arrows_sfx(3.0, 0.2, 14)); X(S('c11') + 1.0, echo(drum(40, 3.0, 1.2)), 0.9); M(S('c11') + 1.0, horn(146.83, 3.5, 0.5)); M(S('c11') + 1.0, horn(220.0, 3.5, 0.35))
    for k2, f in enumerate((146.83, 174.61, 220.0)): X(S('c09') + 0.4 + k2 * 0.3, whoosh(0.6, 0.2))
    # ===== 叁 汉中：推到最高 =====
    a, b = SB[3]
    t = T.chap[3][1]; k = 0
    while t < S('z21'):
        M(t, strings(chords[k % 4], min(8.5, S('z21') - t + 1.5), 0.32, 1.5, 2.0, 1500)); t += 8.0; k += 1
    t = S('z09'); i = 0
    while t < S('z21'):
        g = 0.38 + 0.3 * (t - S('z09')) / (S('z21') - S('z09'))
        M(t, drum(54, 1.6, 0.9), g)
        if i % 2: M(t + 0.3, tick(0.2))
        t += 0.6 - 0.15 * (t - S('z09')) / (S('z21') - S('z09')); i += 1
    for bid in ('z13', 'z16', 'z25'): M(S(bid) - 0.1, echo(drum(44, 2.6, 1.1)), 0.8)
    X(S('z17') + 0.5, signal.lfilter(*signal.butter(2, [200 / (SR / 2), 2500 / (SR / 2)], 'band'), rng.normal(0, 1, int(3 * SR))) * np.sin(np.linspace(0, np.pi, int(3 * SR))) * 0.08)
    # 可击矣 → 冲锋
    X(S('z21') + 1.2, echo(drum(38, 3.5, 1.5)), 1.0)
    ch0 = S('z22'); ch1 = E('z24') + 0.4
    M(ch0, strings([73.42, 146.83, 220.0, 293.66], ch1 - ch0 + 2, 0.42, 0.6, 2.5, 2400))
    M(ch0, horn(146.83, 3.0, 0.62)); M(ch0, horn(220.0, 3.0, 0.45)); M(ch0 + 3.0, horn(174.61, 2.0, 0.55)); M(ch0 + 5.0, horn(220.0, 3.5, 0.6)); M(ch0 + 5.0, horn(293.66, 3.5, 0.4))
    t = ch0; i = 0
    while t < ch1:
        M(t, drum(50 if i % 2 else 58, 1.4, 1.1), 0.75); M(t + 0.16, tick(0.28)); t += 0.32; i += 1
    X(ch0 + 0.2, echo(shout(4.0, 1.0, 60)), 0.8); X(ch0 + 0.5, arrows_sfx(4.0, 0.35, 26)); X(S('z23') + 1.4, echo(drum(36, 4.0, 1.6)), 1.1)
    # 崩溃 → 曹操亲征 → 后勤战
    M(S('z25'), strings([73.42, 110.0, 155.56], E('z28') - S('z25') + 1.5, 0.30, 1.0, 2.0, 900))
    t = S('z29'); k = 0
    while t < E('z39'):
        M(t, strings(chords[k % 4], min(8.5, E('z39') - t + 1.5), 0.30, 1.5, 2.0, 1200)); t += 8.0; k += 1
    t = S('z29'); i = 0
    while t < S('z32'):
        M(t, drum(48, 2.0, 1.0), 0.6); t += 0.9; i += 1
    M(S('z29') + 0.6, horn(110.0, 3.0, 0.5)); M(S('z29') + 0.6, horn(146.83, 3.0, 0.4))
    M(S('z32') - 0.1, echo(drum(42, 3.0, 1.2)), 0.85)
    # 鸡肋：留白，只剩低弦
    M(S('z40') - 0.3, strings([55.0, 82.41], E('z43') - S('z40') + 1.5, 0.22, 1.5, 2.0, 600))
    M(S('z44'), horn(146.83, 3.0, 0.45)); M(S('z44') + 0.4, horn(220.0, 3.0, 0.35)); M(S('z44'), echo(drum(44, 3.0, 1.2)), 0.8)
    t = S('z45'); k = 0
    while t < b:
        M(t, strings(chords[k % 4], min(8.5, b - t + 1.5), 0.26, 1.5, 2.0, 1200)); t += 8.0; k += 1
    # ===== 肆 称王：庄重 =====
    a, b = SB[4]
    prog = [Dm, F, Bb, A7]; t = T.chap[4][1]; k = 0
    while t < b:
        M(t, strings(prog[k % 4], min(8.5, b - t + 1.5), 0.34, 1.5, 2.0, 1700)); t += 8.0; k += 1
    M(S('k02'), horn(146.83, 4.0, 0.5)); M(S('k02') + 2.0, horn(220.0, 4.0, 0.42)); M(S('k02'), echo(drum(42, 3.0, 1.2)), 0.8)
    for bid in ('k03', 'k09'): M(S(bid) - 0.1, echo(drum(44, 2.8, 1.1)), 0.75)
    # ===== 伍 清点 + 结尾 =====
    a, b = SB[5]
    t = T.chap[5][1]; k = 0
    while t < T.total:
        M(t, strings(prog[k % 4], min(8.5, T.total - t + 1), 0.32, 1.5, 2.5, 1500)); t += 8.0; k += 1
    for (_, _, bid) in [('', '', 'e02'), ('', '', 'e03'), ('', '', 'e04'), ('', '', 'e05'), ('', '', 'e06')]: M(S(bid) + 0.8, drum(54, 1.6, 0.8), 0.45)
    M(S('e09') - 0.2, echo(drum(40, 3.2, 1.3)), 0.9); M(S('e09'), horn(146.83, 4.0, 0.5)); M(S('e09'), horn(220.0, 4.0, 0.38))
    M(S('e11'), horn(174.61, 3.0, 0.45)); M(S('e11') + 2.0, horn(220.0, 4.0, 0.5)); M(S('e11') + 2.0, horn(293.66, 4.0, 0.35))
    M(S('e12'), echo(drum(40, 3.5, 1.3)), 0.8)
    mus = reverb(mus[:N], 0.30); sfx = reverb(sfx[:N], 0.22)
    t = np.arange(N) / SR
    mus *= np.clip((T.total - t) / 3.0, 0, 1); sfx *= np.clip((T.total - t) / 2.0, 0, 1)
    return mus.astype(np.float32), sfx.astype(np.float32)

def env(x, win=0.05):
    k = int(win * SR); e = np.sqrt(np.maximum(0, signal.oaconvolve(x.astype(np.float64) ** 2, np.ones(k) / k)[:len(x)])); return e
def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)

def build():
    nar = narration(); mus, sfx = score()
    # 侧链：旁白在时音乐压到人声下约 -22 dB；停顿处略抬
    e = env(nar, 0.08); active = e > 10 ** (-40 / 20)
    k = int(0.35 * SR); act = signal.oaconvolve(active.astype(np.float64), np.ones(k) / k)[:N]; act = np.clip(act * 1.6, 0, 1)
    nar_db = 20 * np.log10(np.sqrt(np.mean(nar[active] ** 2)) + 1e-12)
    m_db = 20 * np.log10(np.sqrt(np.mean(mus[active] ** 2)) + 1e-12)
    g_mus = 10 ** ((nar_db - 22.0 - m_db) / 20)
    gain = g_mus * (1 - act + act * 1.0) * (1 + 0.6 * (1 - act))   # 停顿处 +4 dB
    music = mus * gain
    sfx_db = 20 * np.log10(np.sqrt(np.mean(sfx[sfx != 0] ** 2)) + 1e-12)
    sfx_g = (1 - 0.55 * act)
    mix = nar + music + sfx * sfx_g * 0.45
    nomus = nar + sfx * sfx_g * 0.45
    print('narration speech dB', round(nar_db, 1), 'music under speech dB', round(rms_db((music)[active]), 1), 'diff', round(nar_db - rms_db(music[active]), 1))
    for arr, name in ((mix, 'mix'), (nomus, 'nomusic')):
        st = np.stack([arr, arr], 1).astype(np.float32); d = int(0.012 * SR)
        if name == 'mix': st[d:, 1] += (music[:-d] * 0.15).astype(np.float32); st[d:, 0] -= (music[:-d] * 0.05).astype(np.float32)
        raw = OUTD + name + '.raw.wav'; sf.write(raw, st, SR, subtype='FLOAT')
        g = 0.0
        for it in range(3):
            af = f"volume={g:.2f}dB,alimiter=limit=0.83:attack=2:release=60:level=disabled,aresample=48000"
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', af, '-ar', '48000', '-c:a', 'pcm_s16le', OUTD + name + '.wav'], check=True)
            r = subprocess.run(['ffmpeg', '-hide_banner', '-i', OUTD + name + '.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
            I = float(re.findall(r'I:\s+(-?[0-9.]+) LUFS', r)[-1]); tp = float(re.findall(r'Peak:\s+(-?[0-9.]+) dBFS', r)[-1])
            print(name, 'iter', it, 'I', I, 'TP', tp)
            if abs(I + 15) < 0.3: break
            g += -15 - I
        m = {'input_i': I}
        print(name, 'in', m['input_i'])
    sf.write(OUTD + 'nar_only.wav', nar, SR)
    sf.write(OUTD + 'music_only.wav', music, SR)

if __name__ == '__main__': build()
