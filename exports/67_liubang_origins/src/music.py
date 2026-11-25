# -*- coding: utf-8 -*-
"""自生成底乐与音效（全部 numpy 合成，无外部素材，可商用）。
输出：music.wav（底乐，已按人声闪避）、sfx.wav（开场马铃+竹简+低鼓、转场鼓）
用法：python music.py voice/timeline.json voice/narration.wav outdir"""
import json, sys, os, wave
import numpy as np
from scipy.signal import butter, sosfilt
import pyloudnorm as pyln

SR = 48000
TL = json.load(open(sys.argv[1])); VOICE = sys.argv[2]; OUT = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
TOTAL = TL['total']; N = int(TOTAL * SR)
rng = np.random.RandomState(7)
SC = {s['id']: s for s in TL['scenes']}


def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, f1, f2, o=2): return sosfilt(butter(o, [f1, f2], 'band', fs=SR, output='sos'), x)
def hz(m): return 440 * 2 ** ((m - 69) / 12)


def env_curve(points):
    """points: [(t, value)] 线性插值"""
    t = np.arange(N) / SR
    ts, vs = zip(*points)
    return np.interp(t, ts, vs)


# ── 段落强度 ──
def sv(i, k='vstart'): return SC[i][k]
INT = env_curve([(0, 0.55), (sv('t1'), 0.45), (sv('net'), 0.5), (sv('t2'), 0.42), (sv('myth'), 0.6), (sv('t3'), 0.6),
                 (sv('map1'), 0.85), (sv('siege'), 1.0), (sv('rang'), 0.75), (sv('map2'), 1.0), (sv('three'), 0.8), (sv('t4'), 0.5),
                 (sv('research'), 0.45), (sv('end'), 0.75), (sv('end') + 25, 0.95), (TOTAL - 4, 0.8), (TOTAL, 0.0)])
WAR = env_curve([(0, 0), (sv('map1') - 1, 0), (sv('map1') + 3, 1), (sv('three') + 4, 1), (sv('three') + 10, 0), (TOTAL, 0)])

# ── 和声进行：D 宫/羽调色彩，每 8 秒一换 ──
prog = [(50, 57, 62), (46, 53, 62), (48, 55, 60), (50, 57, 62), (45, 52, 57), (46, 53, 58), (48, 55, 62), (50, 57, 62)]
bar = 8.0
t = np.arange(N) / SR
pad = np.zeros(N)
for k in range(int(TOTAL / bar) + 1):
    ch = prog[k % len(prog)]
    a0 = int(k * bar * SR); a1 = min(N, int((k + 1) * bar * SR + 2.0 * SR))
    if a0 >= N: break
    tt = np.arange(a1 - a0) / SR
    e = np.minimum(1, tt / 2.0) * np.minimum(1, np.maximum(0, (bar + 2.0 - tt) / 2.0))
    seg = np.zeros(a1 - a0)
    for m in ch:
        for det in (-0.06, 0.0, 0.07):
            f = hz(m) * 2 ** (det / 12)
            ph = rng.rand() * 6.28
            seg += (2 * ((f * tt + ph / 6.28) % 1) - 1) * 0.12   # 锯齿 = 弦乐
    seg += np.sin(2 * np.pi * hz(ch[0] - 12) * tt) * 0.35          # 低音
    pad[a0:a1] += seg * e
pad = lp(pad, 900, 2)
pad *= (0.6 + 0.4 * np.sin(2 * np.pi * t / 11.0) ** 2)

# ── 编钟：五声音阶，双音 ──
bell = np.zeros(N)
penta = [62, 65, 67, 69, 72, 74, 77, 79]
tb = 1.0
while tb < TOTAL - 3:
    m = penta[rng.randint(len(penta))]
    f = hz(m)
    L = int(4.0 * SR); a0 = int(tb * SR); a1 = min(N, a0 + L)
    tt = np.arange(a1 - a0) / SR
    s = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.1) + 0.5 * np.sin(2 * np.pi * f * 1.19 * tt) * np.exp(-tt * 1.4)
         + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 3) + 0.2 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt * 6))
    s *= np.minimum(1, tt / 0.004)
    bell[a0:a1] += s * 0.22 * (0.7 + 0.3 * rng.rand())
    tb += rng.choice([4.0, 6.0, 8.0])

# ── 战鼓 ──
def drum(at, amp=1.0, f0=95, f1=48, dec=5.0):
    L = int(1.2 * SR); a0 = int(at * SR)
    if a0 >= N: return np.zeros(0), a0
    tt = np.arange(min(L, N - a0)) / SR
    fr = f1 + (f0 - f1) * np.exp(-tt * 18)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * dec)
    s += lp(rng.randn(len(tt)), 1200) * np.exp(-tt * 40) * 0.5
    return s * amp, a0


drums = np.zeros(N)
def add(buf, s, a0): buf[a0:a0 + len(s)] += s
# 起兵段：鼓点型
beat = 60 / 84
tb = sv('map1')
while tb < sv('three') + 8:
    w = float(np.interp(tb, t[::SR // 10], WAR[::SR // 10]))
    for k, (off, amp) in enumerate([(0, 1.0), (beat, 0.55), (beat * 2, 0.8), (beat * 2.5, 0.45), (beat * 3, 0.6)]):
        s, a0 = drum(tb + off, amp * w); add(drums, s, a0)
    tb += beat * 4
# 其他段落：稀疏心跳鼓
tb = 4.0
while tb < TOTAL - 4:
    if not (sv('map1') - 1 < tb < sv('three') + 8):
        s, a0 = drum(tb, 0.35, 80, 45, 6); add(drums, s, a0)
        s, a0 = drum(tb + 0.42, 0.22, 80, 45, 6); add(drums, s, a0)
    tb += 4.0
# 章节标题大鼓
for s_ in TL['scenes']:
    if s_['kind'] == 'title':
        s, a0 = drum(s_['vstart'] + 0.05, 1.3, 110, 40, 3.0); add(drums, s, a0)

# ── 号角（起兵段）──
horn = np.zeros(N)
for k, (at, m, dur) in enumerate([(sv('siege') + 8, 50, 5), (sv('siege') + 16, 57, 5), (sv('mech') + 2, 50, 6), (sv('map2') + 0.5, 57, 4), (sv('map2') + 5, 62, 6), (sv('end') + 26, 50, 7)]):
    a0 = int(at * SR); L = int(dur * SR); a1 = min(N, a0 + L)
    tt = np.arange(a1 - a0) / SR
    f = hz(m) * (1 + 0.004 * np.sin(2 * np.pi * 5 * tt))
    ph = np.cumsum(f) / SR
    s = sum((1 / h) * np.sin(2 * np.pi * h * ph) for h in range(1, 9))
    e = np.minimum(1, tt / 0.5) * np.minimum(1, (dur - tt) / 1.2)
    horn[a0:a1] += lp(s, 1600) * e * 0.35

music = pad * 0.55 * INT + bell * 0.9 * (0.5 + 0.5 * INT) + drums * 0.9 * (0.4 + 0.6 * INT) + horn * WAR.clip(0.3, 1)
music = hp(music, 35)
st = np.stack([music + 0.02 * np.roll(music, 600), music + 0.02 * np.roll(music, 900)], 1)  # 轻微立体

# ── 开场声音钩子：马铃 + 竹简落地 + 低鼓 ──
sfx = np.zeros((N, 2))
def put(buf, s, at, pan=0.0):
    a0 = int(at * SR); s = s[:max(0, N - a0)]
    buf[a0:a0 + len(s), 0] += s * (1 - pan) ; buf[a0:a0 + len(s), 1] += s * (1 + pan)
# 马铃：一串小铜铃，随马步节奏
for k in range(14):
    at = 0.0 + k * 0.21 + rng.rand() * 0.03
    L = int(0.6 * SR); tt = np.arange(L) / SR
    f = rng.uniform(2600, 4200)
    s = (np.sin(2 * np.pi * f * tt) + 0.6 * np.sin(2 * np.pi * f * 1.47 * tt) + 0.3 * np.sin(2 * np.pi * f * 2.09 * tt)) * np.exp(-tt * 9)
    amp = 0.20 * (1 - k / 18)
    put(sfx, s * amp, at, rng.uniform(-0.4, 0.4))
# 马蹄（低沉）
for k in range(6):
    s, _ = drum(0, 0.18, 140, 90, 25); put(sfx, s, 0.05 + k * 0.42)
# 竹简落地：清脆木声 + 几次弹跳
for k, (at, amp) in enumerate([(0.12, 1.0), (0.21, 0.5), (0.27, 0.28), (0.31, 0.15)]):
    L = int(0.25 * SR); tt = np.arange(L) / SR
    n = rng.randn(L)
    s = (bp(n, 1500, 4500) * np.exp(-tt * 90) * 1.2 + np.sin(2 * np.pi * 1150 * tt) * np.exp(-tt * 45) * 0.6
         + np.sin(2 * np.pi * 2350 * tt) * np.exp(-tt * 60) * 0.4 + np.sin(2 * np.pi * 620 * tt) * np.exp(-tt * 30) * 0.3)
    put(sfx, s * amp * 0.55, at, 0.1)
# 低鼓进入
s, _ = drum(0, 1.2, 100, 42, 2.5); put(sfx, s * 0.9, 0.85)
s, _ = drum(0, 0.8, 100, 42, 3.0); put(sfx, s * 0.7, 1.3)

meter = pyln.Meter(SR)
# 人声
import subprocess
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', VOICE, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
v = np.frombuffer(raw, np.float32).astype(np.float64)
v = np.pad(v, (0, max(0, N - len(v))))[:N]
lv = meter.integrated_loudness(v)
# 底乐整体响度设为人声以下约 21 dB，并在有人声时再闪避 3 dB
mlv = meter.integrated_loudness(st)
st *= 10 ** (((lv - 21) - mlv) / 20)
env = np.convolve(np.abs(v), np.ones(int(0.3 * SR)) / (0.3 * SR), 'same')
act = (env > 0.01).astype(float)
act = np.convolve(act, np.ones(int(0.4 * SR)) / (0.4 * SR), 'same')
duck = 10 ** (-3 * act / 20) * 10 ** (1.5 * (1 - act) / 20)
st *= duck[:, None]
# 结尾淡出
fo = np.minimum(1, np.maximum(0, (TOTAL - t) / 3.0)); st *= fo[:, None]
sfx *= 10 ** ((lv - 4 - meter.integrated_loudness(sfx[:int(3 * SR)] + 1e-9)) / 20) if True else 1


def wr(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
wr(f'{OUT}/music.wav', st); wr(f'{OUT}/sfx.wav', sfx)
print('voice LUFS', round(lv, 1), ' music LUFS', round(meter.integrated_loudness(st), 1), ' diff', round(lv - meter.integrated_loudness(st), 1))
