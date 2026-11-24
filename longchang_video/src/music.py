"""配乐：全部由程序合成（无采样、无外部素材）。48 kHz 立体声。

层次：
  pad    和弦铺底（加法合成，左右轻微失谐）
  pluck  拨弦（模态合成：一组各自衰减的泛音，近似古琴的散音）
  bowl   磬（几支不成整数倍的分音，长衰减）
  drum   轻鼓（南赣用兵一段）
  fire   洞中柴火的细碎爆裂声
  air    很低的风声
调式：全片以 D 为中心。平时是 D 小调五声的开放和弦；"悟"与收尾转到 D 大调。

用法: python music.py <work> <timeline.json> <out.wav>
"""
import json
import sys

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

import storyboard as sb

SR = 48000
work, tlp, outp = sys.argv[1:4]
tl = json.load(open(tlp))
B = tl['beats']
TOTAL = tl['total']
N = int((TOTAL + 1.0) * SR)
rng = np.random.default_rng(1508)

t0 = lambda b: B[b][0]
t1 = lambda b: B[b][1]
tn = lambda b: B[b][2]
seg = lambda b, i: sb.seg_times(b, B[b][0], B[b][1])[i]
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12.0)

CHORDS = {  # MIDI 音高
    'D5': [38, 45, 50, 57, 62],
    'D5low': [26, 38, 45, 50],
    'Dm7': [38, 45, 53, 57, 60],
    'Bb': [34, 41, 46, 50, 53, 57],
    'F': [41, 48, 53, 57, 60],
    'C': [36, 43, 48, 52, 55],
    'Gm': [31, 43, 50, 55, 58],
    'Am': [33, 40, 45, 48, 52],
    'Dmaj9': [38, 45, 50, 54, 57, 64],
    'D': [38, 45, 50, 54, 57],
    'G': [31, 43, 47, 50, 55, 59],
    'Bm': [35, 42, 47, 50, 54],
    'Asus': [33, 40, 45, 50, 52, 55],
}
tt0, tt1 = tl['title']
e0, e1 = tl['end']
PLAN = [
    (0.0, 'D5', 0.70), (t0('a03'), 'Dm7', 0.70), (tt0 - 0.3, 'D5', 0.95), (t0('a05'), 'Dm7', 0.60),
    (t0('b01'), 'Dm7', 0.80), (t0('b03'), 'Bb', 0.80), (t0('b05'), 'Dm7', 0.80), (t0('b07'), 'C', 0.75), (t0('b09'), 'Dm7', 0.80),
    (t0('c01'), 'F', 0.85), (t0('c03'), 'C', 0.80), (t0('c04'), 'Dm7', 0.80), (t0('c06'), 'Bb', 0.85), (t0('c07'), 'F', 0.85),
    (t0('d01'), 'Dm7', 0.70), (t0('d03'), 'Am', 0.60), (t0('d05'), 'Bb', 0.55), (t0('d06'), 'Am', 0.50),
    (t0('e01'), 'D5', 0.60), (t0('e02'), 'Gm', 0.70), (t0('e03'), 'D5', 0.65), (t0('e04'), 'D5low', 0.50), (t0('e07'), 'D5low', 0.36),
    (t1('e08') + 0.2, None, 0.0), (t0('e09') - 0.25, 'Dmaj9', 1.0),
    (t0('e10'), 'G', 0.75), (seg('e11', 1), 'D', 0.75), (t0('e12'), 'Bm', 0.70), (t0('e13'), 'G', 0.70), (t0('e14'), 'Asus', 0.70),
    (t0('e15'), 'D', 0.85), (tn('e15') - 1.7, 'D5', 0.55),
    (t0('f01'), 'Dm7', 0.80), (t0('f02'), 'Gm', 0.70), (t0('f03'), 'Dm7', 0.85), (t0('f04'), 'Gm', 0.80), (t0('f05'), 'Bb', 0.55),
    (t0('f06') - 0.3, 'D5low', 0.36), (t0('f07'), 'F', 0.70), (t0('f08'), 'Bb', 0.75), (t0('f09'), 'F', 0.80), (t0('f10'), 'C', 0.80),
    (t0('f11'), 'Dm7', 0.80),
    (t0('g01'), 'Dm7', 0.70), (t0('g02'), 'Bb', 0.70), (t1('g03') + 0.4, 'Gm', 0.70), (t0('g05'), 'Asus', 0.60), (t0('g06') - 0.4, 'D5low', 0.40),
    (t0('h01'), 'D5', 0.60), (seg('h01', 1) - 0.2, 'Dmaj9', 0.90), (t0('h03'), 'G', 0.75), (t0('h04'), 'Bm', 0.70), (t0('h05'), 'G', 0.80),
    (t0('h06'), 'Asus', 0.80), (t0('h07'), 'D', 0.90), (t0('h08'), 'G', 0.95), (t1('h08') + 0.6, 'Dmaj9', 1.0),
]
PLAN = sorted(PLAN, key=lambda x: x[0])


def env_seg(n, attack, release_at, release, sr=SR):
    """音符包络：平滑起音，到 release_at 后平滑释放。"""
    t = np.arange(n) / sr
    a = np.clip(t / attack, 0, 1)
    a = a * a * (3 - 2 * a)
    r = np.clip(1 - (t - release_at) / release, 0, 1)
    r = r * r * (3 - 2 * r)
    return (a * r).astype(np.float32)


def add(buf, start_t, sig):
    i = int(start_t * SR)
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(i + len(sig), buf.shape[0])
    if j > i:
        buf[i:j] += sig[:j - i]


# ── pad ──
pad = np.zeros((N, 2), np.float32)
for k, (ts, name, gain) in enumerate(PLAN):
    if name is None:
        continue
    te = PLAN[k + 1][0] if k + 1 < len(PLAN) else TOTAL - 1.0
    nxt = PLAN[k + 1][1] if k + 1 < len(PLAN) else None
    attack = 3.2 if name != 'Dmaj9' else 2.4
    release = 4.2 if nxt is not None else 2.6
    if k + 1 >= len(PLAN):
        release = 5.0
    dur = (te - ts) + release
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    e = env_seg(n, attack, te - ts, release)
    sig = np.zeros((n, 2), np.float32)
    notes = CHORDS[name]
    for j, m in enumerate(notes):
        f = mtof(m)
        low = m < 40
        nh = 3 if low else 5
        w_note = (0.60 if j == 0 else 0.62) * (0.8 if m >= 60 else 1.0) * (0.75 if m < 45 else 1.0)
        for h in range(1, nh + 1):
            if f * h > 2600:
                continue
            amp = w_note / h ** (1.9 if not low else 1.5)
            lfo_f = rng.uniform(0.04, 0.13)
            lfo = 0.80 + 0.20 * np.sin(2 * np.pi * lfo_f * t + rng.uniform(0, 6.28))
            for ch, cents in ((0, -3.5), (1, 3.5)):
                ff = f * h * 2 ** ((cents + rng.uniform(-1.2, 1.2)) / 1200)
                sig[:, ch] += (amp * lfo * np.sin(2 * np.pi * ff * t + rng.uniform(0, 6.28))).astype(np.float32)
    sig *= (e * gain * 0.060)[:, None]
    add(pad, ts, sig)
print('pad done', flush=True)

# ── pluck ──
pluck = np.zeros((N, 2), np.float32)


def pluck_note(m, vel=0.7, dur=6.5, pan=0.0, bright=1.0):
    f = mtof(m)
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    bend = 2 ** (10.0 * np.exp(-t / 0.045) / 1200)           # 起音时弦略紧
    phase = 2 * np.pi * f * np.cumsum(bend) / SR
    y = np.zeros(n)
    for h in range(1, 15):
        if f * h > 5200:
            break
        a = abs(np.sin(np.pi * h * 0.21)) / h ** (1.15 / bright ** 0.3)
        tau = 3.6 / (1 + 0.16 * h ** 1.7) * (1.25 if m < 50 else 1.0)
        inh = np.sqrt(1 + 0.00012 * h * h)
        y += a * np.exp(-t / tau) * np.sin(phase * h * inh)
    att = np.clip(t / 0.006, 0, 1)
    y *= att
    nn = int(0.012 * SR)
    noise = rng.standard_normal(nn) * np.exp(-np.arange(nn) / (0.003 * SR))
    sos = butter(2, [300, 2200], btype='band', fs=SR, output='sos')
    y[:nn] += sosfilt(sos, noise) * 0.25
    y *= vel * 0.16
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    return np.stack([y * l, y * r], -1).astype(np.float32)


# 可以落拨弦的空隙：两句之间
gaps = []
for bid in sb.ORDER:
    a, b = B[bid][1] + 0.30, B[bid][2] - 0.25
    if b - a >= 0.55:
        gaps.append((a, b, bid))
gaps.append((tt0 + 0.5, tt1 - 0.5, 'title'))
SKIP = {'e07', 'e08', 'f05', 'f06', 'g05', 'g06'}        # 这些地方留白
for k, (ts, name, gain) in enumerate(PLAN):
    if name is None or name == 'D5low':
        continue
    te = PLAN[k + 1][0] if k + 1 < len(PLAN) else TOTAL
    notes = CHORDS[name]
    pool = [notes[0] + 12, notes[2] + 12 if notes[2] < 55 else notes[2], notes[-1], notes[1] + 12, notes[0] + 24]
    cnt = 0
    for (ga, gb, bid) in gaps:
        if bid in SKIP or not (ts - 0.2 <= ga < te - 0.3):
            continue
        m = pool[cnt % len(pool)]
        while m > 69:
            m -= 12
        add(pluck, ga + 0.05, pluck_note(m, vel=0.55 + 0.25 * rng.random(), pan=rng.uniform(-0.35, 0.35)))
        if gb - ga > 2.0 and cnt % 2 == 0:                     # 长一点的空隙里再应一声
            m2 = pool[(cnt + 2) % len(pool)]
            while m2 > 66:
                m2 -= 12
            add(pluck, ga + 1.25, pluck_note(m2, vel=0.42, pan=rng.uniform(-0.4, 0.4)))
        cnt += 1
add(pluck, 0.7, pluck_note(50, 0.8, pan=-0.1))
add(pluck, 1.9, pluck_note(57, 0.5, pan=0.2))
add(pluck, tt0 + 0.9, pluck_note(38, 0.9, dur=8, pan=0.0))
add(pluck, tt0 + 2.6, pluck_note(57, 0.55, pan=0.25))
add(pluck, tt0 + 3.6, pluck_note(62, 0.45, pan=-0.2))
# 片尾：山里的灯一盏盏亮，高处几声
for i, (dt, m) in enumerate(((0.8, 69), (2.0, 74), (3.1, 66), (4.3, 76), (5.6, 71), (7.0, 78), (8.6, 74), (10.4, 69))):
    tsx = t0('h08') + (t1('h08') - t0('h08')) * 0.55 + dt
    if tsx < e1 - 3.0:
        add(pluck, tsx, pluck_note(m, 0.34, dur=5, pan=rng.uniform(-0.6, 0.6), bright=1.3))
add(pluck, e0 + 1.0, pluck_note(38, 0.85, dur=9))
add(pluck, e0 + 2.8, pluck_note(57, 0.5))
add(pluck, e0 + 4.4, pluck_note(54, 0.45))
add(pluck, e0 + 6.2, pluck_note(50, 0.55, dur=8))
print('pluck done', flush=True)

# ── bowl ──
bowl = np.zeros((N, 2), np.float32)


def bowl_note(m, vel=0.5, dur=11.0):
    f = mtof(m)
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float64) / SR
    y = np.zeros((n, 2))
    for ratio, a, tau in ((1.0, 1.0, 5.5), (2.71, 0.30, 3.2), (5.15, 0.09, 1.6)):
        for ch, df in ((0, -0.35), (1, 0.35)):
            y[:, ch] += a * np.exp(-t / tau) * np.sin(2 * np.pi * (f * ratio + df) * t)
    y *= np.clip(t / 0.02, 0, 1)[:, None] * vel * 0.085
    return y.astype(np.float32)


add(bowl, tt0 + 0.5, bowl_note(62, 0.55))
add(bowl, t0('e09') - 0.2, bowl_note(62, 0.9))
add(bowl, t0('e09') + 1.6, bowl_note(69, 0.55))
add(bowl, t0('f06') + (t1('f06') - t0('f06')) + 0.5, bowl_note(57, 0.45))
add(bowl, t0('g06') - 0.5, bowl_note(62, 0.6))
add(bowl, seg('h01', 1), bowl_note(62, 0.6))
add(bowl, t1('h08') + 0.8, bowl_note(62, 0.7))
add(bowl, e0 + 0.6, bowl_note(50, 0.6, dur=12))

# ── drum ──
drum = np.zeros((N, 2), np.float32)


def drum_hit(vel=0.7):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 46 + 34 * np.exp(-t / 0.06)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / 0.42) + 0.45 * np.sin(2 * ph) * np.exp(-t / 0.22) + 0.22 * np.sin(3.1 * ph) * np.exp(-t / 0.12)
    nn = int(0.05 * SR)
    sos = butter(2, 420, btype='low', fs=SR, output='sos')
    y[:nn] += sosfilt(sos, rng.standard_normal(nn)) * np.exp(-np.arange(nn) / (0.012 * SR)) * 0.6
    y *= np.clip(t / 0.004, 0, 1) * vel * 0.22
    return np.stack([y, y], -1).astype(np.float32)


for dt, v in ((0.0, 0.8), (1.05, 0.6), (2.1, 0.7)):
    add(drum, seg('f03', 1) - 0.1 + dt, drum_hit(v))
add(drum, t0('f04') + 0.1, drum_hit(0.75))
add(drum, t0('f04') + 1.6, drum_hit(0.5))
add(drum, t1('f04') + 0.4, drum_hit(0.85))
add(drum, t1('g03') + 1.0, drum_hit(0.45))

# ── fire / air ──
fx = np.zeros((N, 2), np.float32)
fa, fb = t0('e04') - 0.5, tn('e08') - 0.5
tcur = fa
sosf = butter(2, [1400, 6500], btype='band', fs=SR, output='sos')
while tcur < fb:
    tcur += rng.exponential(0.16)
    nn = int(rng.uniform(0.002, 0.014) * SR)
    c = sosfilt(sosf, rng.standard_normal(nn + 200))[100:100 + nn] * np.exp(-np.arange(nn) / (nn / 3.0))
    amp = 10 ** rng.uniform(-2.9, -1.75)
    lvl = min((tcur - fa) / 2.0, 1.0) * (1.0 - 0.9 * np.clip((tcur - t0('e08')) / max(tn('e08') - t0('e08') - 0.5, 0.5), 0, 1))
    pan = rng.uniform(0.0, 0.8)                                   # 火在画面右下
    c = c * amp * lvl * 1.4
    add(fx, tcur, np.stack([c * np.sqrt(0.5 * (1 - pan)), c * np.sqrt(0.5 * (1 + pan))], -1).astype(np.float32))
# 火的低鸣
nfire = int((fb - fa) * SR)
rum = sosfilt(butter(2, [70, 320], btype='band', fs=SR, output='sos'), rng.standard_normal(nfire))
rum *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.31 * np.arange(nfire) / SR + 1.0)) * 0.0035
rum *= np.clip(np.arange(nfire) / (2.0 * SR), 0, 1) * np.clip((nfire - np.arange(nfire)) / (3.5 * SR), 0, 1)
add(fx, fa, np.stack([rum * 0.8, rum], -1).astype(np.float32))
# 风：全片很低的一层
air = rng.standard_normal((N, 2))
air = sosfilt(butter(2, [260, 900], btype='band', fs=SR, output='sos'), air, axis=0)
tt = np.arange(N) / SR
lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.043 * tt) * np.sin(2 * np.pi * 0.017 * tt + 1.3)
air = (air * lfo[:, None] * 0.0016).astype(np.float32)
print('fx done', flush=True)

# ── 混响：合成脉冲响应（指数衰减的噪声，高频衰减更快）──
def make_ir(rt60=3.6, seed=3):
    g = np.random.default_rng(seed)
    n = int(rt60 * 1.15 * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for ch in range(2):
        lo = sosfilt(butter(2, 900, btype='low', fs=SR, output='sos'), g.standard_normal(n))
        mid = sosfilt(butter(2, [900, 3200], btype='band', fs=SR, output='sos'), g.standard_normal(n))
        hi = sosfilt(butter(2, 3200, btype='high', fs=SR, output='sos'), g.standard_normal(n))
        ir[:, ch] = lo * 10 ** (-3 * t / rt60) + mid * 10 ** (-3 * t / (rt60 * 0.7)) * 0.8 + hi * 10 ** (-3 * t / (rt60 * 0.32)) * 0.5
    ir *= np.clip(t / 0.012, 0, 1)[:, None]
    ir /= np.sqrt((ir ** 2).sum(0)).mean()
    return ir.astype(np.float32)


IR = make_ir()


def reverb(x, wet):
    out = np.zeros_like(x)
    for ch in range(2):
        out[:, ch] = fftconvolve(x[:, ch], IR[:, ch])[:len(x)]
    return x + out * wet


dry = pad * 1.0 + pluck * 1.0 + bowl + drum * 0.9
mus = reverb(dry, 0.55) + reverb(fx, 0.12) + air
# 低切 + 中低频略收，给人声让出位置
mus = sosfilt(butter(2, 58, btype='high', fs=SR, output='sos'), mus, axis=0)
lowpart = sosfilt(butter(1, 300, btype='low', fs=SR, output='sos'), mus, axis=0)
mus = (mus - 0.28 * lowpart).astype(np.float32)
# 总体淡入淡出
g = np.clip(tt / 1.2, 0, 1) * np.clip((TOTAL - 0.3 - tt) / 4.5, 0, 1)
mus *= g[:, None].astype(np.float32)
mus = mus[:int(TOTAL * SR)]
peak = float(np.abs(mus).max())
rms = float(np.sqrt((mus ** 2).mean()))
print('music peak %.3f rms %.1f dBFS' % (peak, 20 * np.log10(rms + 1e-9)))
sf.write(outp, mus, SR, subtype='FLOAT')
for nm, s in (('pad', pad), ('pluck', pluck), ('bowl', bowl), ('drum', drum), ('fx', fx)):
    print('  %-6s rms %.1f dBFS peak %.3f' % (nm, 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9), np.abs(s).max()))
