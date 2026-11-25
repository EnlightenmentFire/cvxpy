# -*- coding: utf-8 -*-
"""自生成配乐 + 音效（全部程序合成，无第三方素材）。
输出：music.wav（配乐，未定电平）、sfx.wav（音效）、voice.wav（旁白，按原句级时码放置）。
配乐随段落能量变化：D 小调，100 BPM；弦乐铺底、持续音型、太鼓、号角、镲声渐强、混响。"""
import json, math, os, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sawtooth, resample_poly, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
from script_data import S
import visuals2 as V

OUT = sys.argv[1]
SR = 48000
tl = json.load(open(os.path.join(HERE, 'timeline_yy.json')))
VT = tl['total']; TOTAL = VT + V.OUTRO['dur']
NF = int(round(TOTAL * 25)); N = int(round(NF / 25 * SR))      # 与视频帧数严格对齐
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


# ───── 能量曲线 ─────
E = np.full(N, 0.4, np.float32)
for sg in tl['segs']:
    a, b = int(sg['start'] * SR), int((sg['start'] + sg['dur']) * SR)
    E[a:b] = 0.5 if sg.get('chap') else V.energy(sg['i'])
E[:int(0.45 * SR)] = 0.9
E[int(VT * SR):] = 0.7
k = int(1.2 * SR)
E = np.convolve(E, np.ones(k, np.float32) / k, mode='same').astype(np.float32)
def e_at(t): return float(E[min(N - 1, max(0, int(t * SR)))])


# ───── 乐器 ─────
def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR / 2 - 100), 'lowpass', fs=SR, output='sos'), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'highpass', fs=SR, output='sos'), x)
def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], 'bandpass', fs=SR, output='sos'), x)
def note_f(n):  # MIDI → Hz
    return 440.0 * 2 ** ((n - 69) / 12)
def env_adsr(n, a, r):
    e = np.ones(n, np.float32); na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

BPM = 100; BEAT = 60 / BPM; BAR = 4 * BEAT
# D 小调和弦（MIDI 根音与组成音）
EPIC = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]      # Dm Bb F C
CALM = [[50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [45, 52, 57, 61]]      # Dm Bb Gm A

music = np.zeros(N, np.float32)
drums = np.zeros(N, np.float32)
horn = np.zeros(N, np.float32)

def add(buf, x, t0, g=1.0):
    i0 = int(t0 * SR)
    if i0 >= N: return
    seg = x[:N - i0]; buf[i0:i0 + len(seg)] += g * seg

# 弦乐铺底 + 持续音型
nbar = int(TOTAL / BAR) + 2
for b in range(nbar):
    t0 = b * BAR; e = e_at(t0 + BAR / 2)
    prog = EPIC if e >= 0.6 else CALM
    ch = prog[b % 4] if e >= 0.6 else prog[(b // 2) % 4]
    dur = BAR + 0.9; n = int(dur * SR); tt = np.arange(n) / SR
    pad = np.zeros(n, np.float32)
    for m in ch:
        for det in (-0.07, 0.0, 0.08):
            f = note_f(m - 12 if m > 55 else m) * 2 ** (det / 12)
            pad += sawtooth(2 * np.pi * f * tt + rng.uniform(0, 6)).astype(np.float32)
    pad = lp(pad, 380 + 1500 * e) * env_adsr(n, 0.5, 0.9) / 12
    add(music, pad.astype(np.float32), t0, 0.8 + 0.5 * e)
    if e >= 0.5:      # 八分音符低音持续音型
        root = ch[0] - 12
        for s8 in range(8):
            ts = t0 + s8 * BEAT / 2; nn = int(0.22 * SR); tt2 = np.arange(nn) / SR
            f = note_f(root + (12 if s8 % 4 == 3 else 0))
            x = sawtooth(2 * np.pi * f * tt2).astype(np.float32)
            x = lp(x, 900) * np.exp(-tt2 * 14)
            add(music, x.astype(np.float32), ts, 0.30 * (e - 0.35) * (1.25 if s8 % 2 == 0 else 0.85))
    if e >= 0.8:      # 高音弦乐（八度上）
        n2 = int((BAR + 0.6) * SR); tt3 = np.arange(n2) / SR; sh = np.zeros(n2, np.float32)
        for m in ch[1:]:
            sh += np.sin(2 * np.pi * note_f(m + 12) * tt3 * (1 + 0.003 * np.sin(2 * np.pi * 5 * tt3))).astype(np.float32)
        add(music, (sh * env_adsr(n2, 0.6, 0.6) / 6).astype(np.float32), t0, 0.35 * (e - 0.6))

# 太鼓
def taiko(big=True):
    n = int((1.4 if big else 0.6) * SR); tt = np.arange(n) / SR
    f = (44 if big else 70) + (60 if big else 90) * np.exp(-tt * 18)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * (3.2 if big else 7))
    skin = lp(rng.standard_normal(n), 1600) * np.exp(-tt * 40)
    x = body + 0.5 * skin
    return (x / np.max(np.abs(x))).astype(np.float32)
TBIG, TSMALL = taiko(True), taiko(False)
for b in range(nbar):
    t0 = b * BAR; e = e_at(t0 + 0.1)
    if e < 0.45:
        add(drums, TBIG, t0, 0.35); continue
    add(drums, TBIG, t0, 1.0)
    add(drums, TBIG, t0 + 2 * BEAT, 0.75)
    add(drums, TSMALL, t0 + 1.5 * BEAT, 0.5); add(drums, TSMALL, t0 + 3 * BEAT, 0.55)
    if e >= 0.85:
        for s8 in (1, 3, 5, 7): add(drums, TSMALL, t0 + s8 * BEAT / 2, 0.35)
        if b % 4 == 3:
            for s16 in range(12, 16): add(drums, TSMALL, t0 + s16 * BEAT / 4, 0.45 + 0.1 * (s16 - 12))

# 号角动机
def horn_note(m, dur, g=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 0.4, 0, 1)
    x = sawtooth(2 * np.pi * note_f(m) * np.cumsum(vib) / SR).astype(np.float32)
    x = bp(x, 250, 1600) + 0.35 * bp(x, 900, 2600)
    return (x * env_adsr(n, 0.12, min(0.5, dur * 0.4)) * g).astype(np.float32)
MOTIF = [(62, 1.0), (69, 1.0), (65, 0.5), (64, 0.5), (62, 2.0)]        # D A F E D
def call(t0, g=1.0, low=True):
    tt = t0
    for m, beats in MOTIF:
        d = beats * BEAT
        add(horn, horn_note(m, d + 0.15), tt, g)
        if low: add(horn, horn_note(m - 7, d + 0.15), tt, 0.6 * g)
        tt += d
horn_times = [0.05]
for sg in tl['segs']:
    if sg.get('chap'): horn_times.append(sg['start'] + 0.1)
for i in (5, 79, 87, 108, 117):
    sg = next(s for s in tl['segs'] if s['i'] == i); horn_times.append(sg['start'] + 0.2)
horn_times.append(VT + 0.4)
for ht in horn_times: call(ht, 1.0)

# 镲声渐强（章节前）
def swell(dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (hp(rng.standard_normal(n), 4000) * (tt / dur) ** 2.2 * 0.5).astype(np.float32)
for sg in tl['segs']:
    if sg.get('chap'): add(music, swell(), max(0, sg['start'] - 1.5), 0.5)

mus = music + 0.9 * drums + 0.55 * horn
# 混响（合成冲激响应，立体声去相关）
def ir(seed):
    r = np.random.default_rng(seed); n = int(2.4 * SR); tt = np.arange(n) / SR
    x = r.standard_normal(n) * np.exp(-tt * 2.6); x = lp(x, 5000); x[0] = 0
    return (x / np.sqrt(np.sum(x * x))).astype(np.float32)
wetL = fftconvolve(mus, ir(1), mode='full')[:N]; wetR = fftconvolve(mus, ir(2), mode='full')[:N]
ML = mus * 0.75 + wetL * 0.55; MR = mus * 0.75 + wetR * 0.55
mstereo = np.stack([ML, MR], 1).astype(np.float32)
mstereo /= np.max(np.abs(mstereo)) + 1e-9
sf.write(os.path.join(OUT, 'music.wav'), mstereo * 0.8, SR, subtype='FLOAT')

# ───── 旁白（原句级时码，不改）─────
voice = np.zeros(N, np.float32)
for sg in tl['segs']:
    if sg.get('chap'): continue
    a, sr = sf.read(sg['file'], dtype='float32')
    if a.ndim > 1: a = a.mean(1)
    if sr != SR: a = resample_poly(a, SR // math.gcd(SR, sr), sr // math.gcd(SR, sr)).astype(np.float32)
    add(voice, a, sg['start'])
sf.write(os.path.join(OUT, 'voice.wav'), voice, SR, subtype='FLOAT')

# ───── 音效（无配乐版也保留）─────
sfx = np.zeros(N, np.float32)
def whoosh(dur=0.8):
    n = int(dur * SR); tt = np.arange(n) / SR; x = rng.standard_normal(n).astype(np.float32); out = np.zeros(n, np.float32)
    seg = 2400
    for k0 in range(0, n, seg):
        fc = 300 + 2800 * (k0 / n); out[k0:k0 + seg] = bp(x[k0:k0 + seg], fc * 0.6, fc * 1.6)
    return (out * np.sin(np.pi * tt / dur) ** 2 / (np.max(np.abs(out)) + 1e-9)).astype(np.float32)
def boom(dur=1.8):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = 36 + 40 * np.exp(-tt * 6); y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.4)
    y += 0.4 * lp(rng.standard_normal(n), 700) * np.exp(-tt * 30)
    return (y / np.max(np.abs(y))).astype(np.float32)
# 风：全片铺底，地图/战场段更强
wind = lp(hp(rng.standard_normal(N).astype(np.float32), 180), 1400)
wmod = 0.5 + 0.5 * np.sin(2 * np.pi * t_all / 7.3) * np.sin(2 * np.pi * t_all / 3.1 + 1)
wl = np.zeros(N, np.float32)
for sg in tl['segs']:
    nm = (V.OVERRIDE.get(sg['i']) if hasattr(V, 'OVERRIDE') else None) or S[sg['i']]['v']
    nm = nm[0]
    lvl = {'opener': 1.0, 'siege': 0.8, 'battle': 0.9, 'retreat': 0.9, 'cnmap': 0.5, 'hfmap': 0.5, 'bridge': 0.6, 'walk': 0.6,
           'gate': 0.5, 'dots': 0.6}.get(nm, 0.25)
    if sg['i'] == 0: lvl = 1.0
    wl[int(sg['start'] * SR):int((sg['start'] + sg['dur']) * SR)] = lvl
wl[int(VT * SR):] = 0.4
wl = np.convolve(wl, np.ones(SR) / SR, mode='same').astype(np.float32)
sfx += wind * wmod * wl * 0.05
# 行军脚步（开场、围城、撤军）
step = (lp(rng.standard_normal(int(0.12 * SR)), 300) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30)).astype(np.float32)
def march(t0, t1, g=0.25):
    tt = t0
    while tt < t1:
        add(sfx, step, tt + rng.uniform(-0.02, 0.02), g * rng.uniform(0.7, 1.0)); tt += 0.33
for sg in tl['segs']:
    nm = S[sg['i']]['v'][0] if sg['i'] != 0 else 'opener'
    if nm in ('opener', 'siege') or (nm == 'retreat' and S[sg['i']]['v'][1].get('p', (9,))[0] < 2):
        march(sg['start'], sg['start'] + sg['dur'], 0.22)
# 火声（营火、火把）
def crackle(dur):
    n = int(dur * SR); x = np.zeros(n, np.float32)
    for _ in range(int(dur * 18)):
        i = rng.integers(0, n - 400); x[i:i + 200] += hp(rng.standard_normal(200), 2000).astype(np.float32) * rng.uniform(0.2, 1)
    return x + 0.15 * lp(rng.standard_normal(n), 600).astype(np.float32)
for sg in tl['segs']:
    nm, prm = S[sg['i']]['v']
    if (nm == 'battle' and prm['p'][0] < 1.4) or (nm == 'gate' and prm.get('mode') in ('night', 'close', 'out')) or (nm == 'siege'):
        add(sfx, crackle(sg['dur']), sg['start'], 0.05)
# 水声（桥、船）
for sg in tl['segs']:
    nm = S[sg['i']]['v'][0]
    if nm in ('bridge', 'boat'):
        n = int(sg['dur'] * SR); tt = np.arange(n) / SR
        w = lp(rng.standard_normal(n), 500).astype(np.float32) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 2.3)) ** 2
        add(sfx, (w * env_adsr(n, 0.4, 0.4)).astype(np.float32), sg['start'], 0.35)
# Whoosh：章节、箭头扫过、战术镜头切入
WH = whoosh(); BM = boom()
add(sfx, WH, 0.0, 0.35); add(sfx, BM, 0.05, 0.6)
for sg in tl['segs']:
    i = sg['i']; nm = S[i]['v'][0] if i not in (0,) else 'opener'
    if sg.get('chap'): add(sfx, WH, max(0, sg['start'] - 0.5), 0.3); add(sfx, BM, sg['start'], 0.45)
    elif nm in ('cnmap', 'hfmap', 'battle', 'retreat', 'siege') and i not in (0,):
        add(sfx, WH, max(0, sg['start'] - 0.2), 0.16)
    if i in V.SHAKE:
        t0, A = V.SHAKE[i]; add(sfx, BM, sg['start'] + t0, 0.25 + A / 40); add(sfx, WH, max(0, sg['start'] + t0 - 0.45), 0.3)
add(sfx, BM, VT, 0.35)
sf.write(os.path.join(OUT, 'sfx.wav'), sfx, SR, subtype='FLOAT')
json.dump({'N': N, 'SR': SR, 'TOTAL': N / SR, 'VT': VT}, open(os.path.join(OUT, 'audio_meta.json'), 'w'))
print('ok', N / SR)
