"""自合成配乐 + 环境声 + 混音（全部由本脚本用 numpy 生成，无第三方素材）。
输出 audio/out/music.wav（配乐+音效）与 audio/out/mix.wav（旁白+配乐，已做旁白时压低）。"""
import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly
SR = 48000
TL = json.load(open('render/timeline.json')); DUR = TL['dur']; N = int(DUR * SR); t = np.arange(N) / SR
LI = {l['id']: l for l in TL['lines']}; SEC = {s['id']: s for s in TL['sections']}
T = lambda i: LI[i]['start']; TE = lambda i: LI[i]['end']
def K(i, w):
    l = LI[i]
    for s in l['subs']:
        k = s['text'].find(w)
        if k >= 0: return s['start'] + (s['end'] - s['start']) * k / max(1, len(s['text']))
    k = l['sub'].find(w); return l['start'] + (l['end'] - l['start']) * max(k, 0) / len(l['sub'])
rs = np.random.RandomState(1978)
def filt(x, fc, kind='low', order=2):
    return sosfilt(butter(order, np.array(fc) / (SR / 2), kind, output='sos'), x)
def env_pts(pts):  # piecewise-linear envelope from (time, value)
    xs, ys = zip(*pts); return np.interp(t, xs, ys).astype(np.float32)
def mixs(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n, np.float32)
    for x in xs: o[:len(x)] += x
    return o
def place(buf, x, at):
    i = int(at * SR)
    if i >= N or i < 0: return
    n = min(len(x), N - i); buf[i:i + n] += x[:n]
def saw(f, n, nh=8, det=0.0):
    tt = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for k in range(1, nh + 1): out += (np.sin(2 * np.pi * k * f * (1 + det) * tt + rs.rand() * 6.28) / k).astype(np.float32)
    return out
# ---------- section intensity ----------
S = SEC
iron_cut = TE('h3') + 0.15; flow = TE('h3') + 1.1; h4 = T('h4')
inten = env_pts([(0, 0), (1.5, .45), (K('c4', '行政人员'), .5), (K('c4', '行政人员') + 2.5, .85), (T('c6'), .6), (S['title']['start'], .9), (S['title']['end'], .8),
  (S['gap']['start'] + 2, .55), (S['tokyo']['start'], .55), (S['pile']['start'], .6), (K('d2', '打下'), .8), (S['debate']['start'], .7), (T('e8'), .8), (T('e13'), .6),
  (S['halt']['start'], .55), (T('f4'), .5), (S['ledger']['start'], .55), (T('g5'), .7), (T('g6'), .85), (T('g7'), .6), (S['iron']['start'], .6), (T('h1'), .7), (T('h3'), .8),
  (iron_cut, .0), (h4 - .2, .0), (h4 + 1.5, 1.0), (S['end']['start'], .7), (T('z3'), .6), (TE('z3') + .6, .45), (DUR - .15, 0), (DUR, 0)])
# ---------- drone ----------
roots = {'D': 36.71, 'Bb': 29.14, 'C': 32.70, 'G': 24.50, 'A': 27.50, 'F': 43.65}
BAR = 12.0; prog = ['D', 'D', 'Bb', 'D', 'G', 'D', 'C', 'D']
drone = np.zeros(N, np.float32); pad = np.zeros(N, np.float32)
nb = int(np.ceil(DUR / BAR)) + 1; seg = int((BAR + 4) * SR); win = np.ones(seg, np.float32); f = int(4 * SR)
win[:f] = np.sin(np.linspace(0, np.pi / 2, f)) ** 2; win[-f:] = np.cos(np.linspace(0, np.pi / 2, f)) ** 2
tri = {'D': (1, 1.189, 1.498), 'Bb': (1, 1.26, 1.498), 'C': (1, 1.26, 1.498), 'G': (1, 1.189, 1.498), 'A': (1, 1.189, 1.498), 'F': (1, 1.26, 1.498)}
for b in range(nb):
    r = roots[prog[b % len(prog)]]
    x = saw(r, seg, 10) + .8 * saw(r * 2, seg, 8, .004) + .6 * saw(r * 2, seg, 8, -.005) + .35 * saw(r * 3, seg, 5, .002)
    place(drone, x * win, b * BAR - 2 if b else 0)
    p = sum(saw(r * 4 * m, seg, 4, d) for m, d in zip(tri[prog[b % len(prog)]], (.003, -.004, .002))) + .5 * saw(r * 8, seg, 2, .001)
    place(pad, p * win, b * BAR - 2 if b else 0)
drone = filt(drone, 170) * (1 + .25 * np.sin(2 * np.pi * .06 * t))
pad = filt(filt(pad, 900), 140, 'high') * (.7 + .3 * np.sin(2 * np.pi * .045 * t + 1))
# ---------- pulse (slow heartbeat) + tense ostinato in the debate ----------
pulse = np.zeros(N, np.float32)
n1 = int(.9 * SR); tt = np.arange(n1) / SR
thump = (np.sin(2 * np.pi * (52 * tt + 22 * (1 - np.exp(-tt * 18)) / 18)) * np.exp(-tt * 5.5)).astype(np.float32)
tick = filt(rs.randn(int(.08 * SR)).astype(np.float32), [2500, 7000], 'band') * np.exp(-np.arange(int(.08 * SR)) / SR * 70)
k = 0
while k * 2.0 < DUR:
    tm = 2.0 + k * 2.0
    if not (iron_cut - 1 < tm < h4 + 1) and tm < S['end']['start'] + 2: place(pulse, thump * (.9 if k % 2 == 0 else .55), tm); place(pulse, tick * .12, tm + 1.0)
    k += 1
ost = np.zeros(N, np.float32); n2 = int(.42 * SR); tt2 = np.arange(n2) / SR
for (a, b_, g) in [(T('e8') - 1, T('e13') - .5, 1.0), (T('e1'), T('e3'), .6), (T('g1'), T('g6'), .7), (K('c4', '行政人员'), T('c6'), .7)]:
    tm = a; i = 0
    while tm < b_:
        fr = 73.42 * (1.0 if i % 4 != 3 else 1.189); pl = filt(saw(fr, n2, 12), 700) * np.exp(-tt2 * 9) * (1 if i % 4 == 0 else .6)
        place(ost, pl * g * min(1, (tm - a) / 3 + .2), tm); tm += .5; i += 1
# ---------- hits / stamps / pile driver ----------
hits = np.zeros(N, np.float32)
def metal(f0, dur=3.0, bright=1.0):
    n = int(dur * SR); x = np.arange(n) / SR; out = np.zeros(n, np.float32)
    for m, a, d in [(1, 1, 2.2), (2.76, .6, 3.5), (5.40, .35 * bright, 5), (8.93, .2 * bright, 8), (13.3, .1 * bright, 12)]:
        out += (a * np.sin(2 * np.pi * f0 * m * x + rs.rand() * 6) * np.exp(-x * d)).astype(np.float32)
    return out
def boom(dur=2.2, f=42):
    n = int(dur * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * (f * x + 30 * (1 - np.exp(-x * 14)) / 14)) * np.exp(-x * 2.4)).astype(np.float32)
def thud():
    n = int(.5 * SR); x = np.arange(n) / SR
    return (np.sin(2 * np.pi * (70 * x + 60 * (1 - np.exp(-x * 30)) / 30)) * np.exp(-x * 13) + .5 * filt(rs.randn(n), 1200) * np.exp(-x * 40)).astype(np.float32)
for sid in ['gap', 'tokyo', 'pile', 'debate', 'halt', 'ledger', 'iron']:
    st = S[sid]['start']; place(hits, mixs(boom() * .9, metal(146.8, 3.5, .7) * .22), st + .12)
place(hits, mixs(boom(3, 36) * 1.0, metal(110, 4.5) * .3), S['title']['start'] + .25)
place(hits, boom(2.4, 38) * .8, K('c4', '行政人员') + .1)
for w in ['一期', '二期', '两板']: place(hits, thud() * 1.1, K('f2', w))
place(hits, mixs(thud() * 1.3, boom(1.5, 50) * .5), K('g6', '改列') + .5)
u0 = K('d2', '打下')
for k in range(7): place(hits, mixs(thud() * .8, metal(310, 1.2, 1.4) * .16), u0 + k * .55 + .25)
for w in ['调整', '退够', '下好']: place(hits, boom(1.4, 46) * .5, K('f4', w))
# ---------- reverb ----------
irn = int(2.8 * SR); ir = (rs.randn(irn) * np.exp(-np.arange(irn) / SR * 2.6)).astype(np.float32); ir = filt(ir, 3200); ir /= np.sqrt((ir ** 2).sum())
def verb(x, wet=.5): return x + wet * fftconvolve(x, ir)[:len(x)].astype(np.float32)
# ---------- ambience for the tapping scene ----------
brown = np.cumsum(rs.randn(N).astype(np.float32)); brown = filt(brown - np.linspace(brown[0], brown[-1], N), 20, 'high'); brown /= np.abs(brown).max()
roar = filt(brown, 240) * 3.0
hiss = filt(rs.randn(N).astype(np.float32), [1800, 7000], 'band') * .25
tIg = K('h1', '点火')
amb_env = env_pts([(0, 0), (tIg - .2, 0), (tIg + 2.5, .30), (T('h3'), .38), (iron_cut, .55), (flow, .7), (flow + 1.2, 1.0), (h4 + 2.5, .75), (S['end']['start'] + 1.5, 0), (DUR, 0)])
crk = np.zeros(N, np.float32); i0 = int(flow * SR); i1 = int((S['end']['start'] + .5) * SR)
idx = i0 + np.sort(rs.randint(0, i1 - i0, 2600)); crk[idx] = rs.rand(len(idx)) ** 3
crk = filt(crk, [1500, 9000], 'band') * 9 * env_pts([(0, 0), (flow, 0), (flow + .6, 1), (h4 + 2, .8), (S['end']['start'] + .5, 0), (DUR, 0)])
nw = int(2.2 * SR); xw = np.arange(nw) / SR; whoosh = filt(rs.randn(nw).astype(np.float32), [300, 2400], 'band') * np.sin(np.pi * np.clip(xw / 2.2, 0, 1)) ** 2 * .9
amb = (roar + hiss * (.4 + .6 * (t > flow))) * amb_env + crk; place(amb, whoosh, flow - .5)
# crowd-flood shimmer in the cold open
sh = filt(rs.randn(N).astype(np.float32), [3000, 9000], 'band') * env_pts([(0, 0), (K('c4', '行政人员'), 0), (K('c4', '行政人员') + 1.6, .09), (K('c4', '行政人员') + 2.8, 0), (DUR, 0)])
# warm resolve chord at h4 (D major)
res = np.zeros(N, np.float32); n3 = int(14 * SR); x3 = np.arange(n3) / SR
ch = sum(saw(fq, n3, 5, d) for fq, d in [(73.42, 0), (110, .002), (146.83, -.002), (185.0, .003), (220, -.003), (293.66, .001)]) * np.minimum(1, x3 / 2.2) * np.exp(-np.maximum(0, x3 - 6) / 4)
place(res, filt(ch, 1400).astype(np.float32), h4 - .1)
# ---------- music bus ----------
music = (drone * .50 + pad * .13) * inten + pulse * .5 * np.minimum(1, inten * 1.5) + ost * .16 * (inten > 0) + res * .07
music = verb(music.astype(np.float32), .35) + verb(hits, .6) * .5 + sh
music = np.tanh(music * 1.3) / 1.3
# stereo: decorrelate with short delays
def st(x, d=.011):
    k = int(d * SR); L = x.copy(); R = np.concatenate([np.zeros(k, np.float32), x[:-k]]); return np.stack([.85 * L + .15 * R, .15 * L + .85 * R], 1)
mus = st(music) + st(amb.astype(np.float32) * .55, .017)
# ---------- narration + ducking ----------
nar, sr0 = sf.read('audio/out/narration.wav', dtype='float32'); nar = resample_poly(nar, SR, sr0).astype(np.float32)[:N]; nar = np.pad(nar, (0, N - len(nar)))
nar = filt(nar, 70, 'high'); nar /= (np.abs(nar).max() + 1e-9); nar *= .82
e = np.abs(nar); e = filt(e, 6); e = np.clip(e / (np.percentile(e, 95) + 1e-9), 0, 1)
hold = int(.35 * SR); from scipy.ndimage import maximum_filter1d
e = filt(maximum_filter1d(e, hold), 3); e = np.clip(e * 1.4, 0, 1)
duck = 1 - .80 * e
mus *= duck[:, None]
peak = np.abs(mus).max(); mus *= .50 / peak
sf.write('audio/out/music.wav', mus, SR)
mix = mus + nar[:, None]; mix /= max(1, np.abs(mix).max() / .98)
sf.write('audio/out/mix.wav', mix, SR)
def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
a, b = int(T('a3') * SR), int(TE('a5') * SR); g0, g1 = int((flow) * SR), int((h4 - .1) * SR)
print(f'dur {DUR:.1f}s  nar rms {db(nar[a:b]):.1f} dB  music under voice {db(mus[a:b]):.1f} dB  tapping ambience (no voice) {db(mus[g0:g1]):.1f} dB')
