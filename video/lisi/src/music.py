# -*- coding: utf-8 -*-
"""配乐与音效：全部用 numpy 现场合成（无任何外部素材），再与旁白混音。
输出 build/music.wav（纯配乐）与 build/mix.wav（旁白 + 配乐，48k 立体声）。"""
import json, os, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

ROOT = os.path.join(os.path.dirname(__file__), ".."); SR = 48000
TL = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
SEG = {s["id"]: s for s in TL["segs"]}; SCN = {s["id"]: s for s in TL["scenes"]}
S = lambda i: SEG[i]["s"]; E = lambda i: SEG[i]["e"]; D = lambda i: E(i) - S(i)
TOTAL = TL["total"]; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(87)
dry = np.zeros((N, 2), np.float32)      # 直达声
wet = np.zeros((N, 2), np.float32)      # 送混响
NOTE = dict(D1=36.71, A1=55.0, D2=73.42, F2=87.31, G2=98.0, A2=110.0, C3=130.81, D3=146.83, Eb3=155.56, F3=174.61, G3=196.0, A3=220.0,
            C4=261.63, D4=293.66, Eb4=311.13, F4=349.23, G4=392.0, A4=440.0, C5=523.25, D5=587.33)

def put(buf, t, x, pan=0.5, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    x = x[: N - i]
    buf[i:i+len(x), 0] += x * g * np.cos(pan * np.pi / 2); buf[i:i+len(x), 1] += x * g * np.sin(pan * np.pi / 2)

def lp(x, fc, order=2): return sosfilt(butter(order, fc, btype="low", fs=SR, output="sos"), x)
def hp(x, fc, order=2): return sosfilt(butter(order, fc, btype="high", fs=SR, output="sos"), x)

def pluck(f, dur=4.0, bright=0.5, decay=0.996):
    """Karplus-Strong 拨弦（偏古琴：低、暗、余音长）"""
    n = int(SR / f); buf = lp(rng.uniform(-1, 1, n), 800 + 5000 * bright); out = np.empty(int(dur * SR), np.float32)
    k = 0
    while k < len(out):
        m = min(n, len(out) - k); out[k:k+m] = buf[:m]
        buf = decay * 0.5 * (buf + np.roll(buf, 1)); k += n
    env = np.minimum(1, np.arange(len(out)) / (0.004 * SR)) * np.exp(-np.arange(len(out)) / (dur * 0.45 * SR))
    return (out * env).astype(np.float32)

def bell(f, dur=6.0):
    """编钟感的钟声：非谐泛音"""
    t = np.arange(int(dur * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in [(1, 1, .7), (2.76, .5, 1.3), (5.4, .25, 2.4), (8.93, .12, 4)])
    return (x * np.minimum(1, t / .003)).astype(np.float32) * 0.5

def drum(f0=78, f1=42, dur=1.6, noise=0.25):
    t = np.arange(int(dur * SR)) / SR; fr = f1 + (f0 - f1) * np.exp(-t * 18)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 4.2)
    x += noise * lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t * 30)
    return x.astype(np.float32)

def knock(dur=0.25):
    t = np.arange(int(dur * SR)) / SR
    return ((np.sin(2 * np.pi * 420 * t) + .6 * np.sin(2 * np.pi * 910 * t)) * np.exp(-t * 55) + .3 * hp(rng.normal(0, 1, len(t)), 2000) * np.exp(-t * 120)).astype(np.float32)

def tick():
    t = np.arange(int(0.08 * SR)) / SR
    return (hp(rng.normal(0, 1, len(t)), 3000) * np.exp(-t * 160) * .5 + np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 120) * .3).astype(np.float32)

def P(t, name, g=0.5, pan=0.5, dur=4.5, bright=0.45, wetg=0.6):
    x = pluck(NOTE[name], dur, bright); put(dry, t, x, pan, g); put(wet, t, x, pan, g * wetg)
def B(t, name, g=0.2, pan=0.5):
    x = bell(NOTE[name]); put(dry, t, x, pan, g * .5); put(wet, t, x, pan, g)
def DR(t, g=0.6, **kw):
    x = drum(**kw); put(dry, t, x, .5, g); put(wet, t, x, .5, g * .35)

# ---------- 持续低音（随段落改变明暗） ----------
t = np.arange(N) / SR
def envelope(points):
    xs, ys = zip(*points); return np.interp(t, xs, ys).astype(np.float32)
sc = lambda i: SCN[i]["cut_in"]
sil0, sil1 = E("s18") + 0.25, S("s19") - 0.15          # 沙丘：真正的静音
drone_env = envelope([(0, 0), (2.5, .55), (E("c5"), .6), (S("r1"), .5), (sc("xun"), .55), (sc("zhuke"), .7), (sc("hanfei"), .5), (S("h13"), .35),
                      (sc("peak"), .75), (S("p9"), .5), (sc("shaqiu"), .35), (S("s7"), .28), (S("s16"), .45), (sil0 - .05, .7), (sil0, 0), (sil1, 0), (sil1 + 2, .3),
                      (sc("duze"), .6), (sc("trap"), .6), (sc("prison"), .7), (S("j11"), .4), (sc("end"), .45), (E("e12") + 1, .4), (TOTAL - .3, 0), (TOTAL + 2, 0)])
dr = np.zeros(N, np.float32)
for f, a, lfo in [(36.71, .55, .05), (73.42, .5, .07), (73.9, .3, .043), (110.0, .22, .031), (146.83, .1, .09)]:
    dr += a * np.sin(2 * np.pi * f * t + 1.5 * np.sin(2 * np.pi * lfo * t)) * (0.75 + 0.25 * np.sin(2 * np.pi * lfo * 1.7 * t + f))
air = lp(hp(rng.normal(0, 1, N), 180), 900).astype(np.float32) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * t))
dark = envelope([(0, 0), (sc("shaqiu"), 0), (sc("shaqiu") + 3, 1), (sc("duze"), 1), (sc("duze") + 2, .2), (TOTAL, .2)])   # 沙丘的风
drone = (dr * 0.16 + air * (0.035 + 0.09 * dark)) * drone_env
dry[:, 0] += drone; dry[:, 1] += np.roll(drone, 331)
# 紧张的噪声渐强（赵高摊牌），在静音前戛然而止
sw0, sw1 = S("s16") + 2.0, sil0
i0, i1 = int(sw0 * SR), int(sw1 * SR); x = lp(hp(rng.normal(0, 1, i1 - i0), 90), 420) * (np.linspace(0, 1, i1 - i0) ** 2.2) * 0.22
put(dry, sw0, x.astype(np.float32), .5, 1); put(wet, sw0, x.astype(np.float32), .5, .2)

# ---------- 段落音乐 ----------
# 冷开场：三声，下行
for tt, n in [(S("c3") + .2, "A3"), (S("c3") + 2.4, "G3"), (S("c4") + .6, "D3"), (S("c5") + 1.0, "A2")]: P(tt, n, .5, .45)
# 片名
T0 = E("c5") + 0.3; DR(T0, .8); [P(T0 + i * .05, n, .45, .4 + i * .1) for i, n in enumerate(["D2", "D3", "A3", "D4"])]; B(T0 + 1.4, "A4", .12)
# 壹：厕（低暗）→ 仓（亮一点）
for k, n in enumerate(["D3", "F3", "D3", "A2"]): P(S("r1") + .4 + k * 3.1, n, .38, .35, bright=.3)
for k, n in enumerate(["A3", "D4", "F4", "A3"]): P(S("r5") + .2 + k * 2.4, n, .36, .65, bright=.6)
P(S("r9") + .1, "D3", .55); P(S("r9") + .15, "A3", .4, .6); P(S("r11") + .4, "D2", .45); B(S("r11") + 3.2, "D5", .08)
# 贰、叁：一级一级往上走
steps = ["D3", "F3", "G3", "A3", "C4", "D4", "F4", "G4", "A4"]; a0, a1 = S("x1"), E("q7")
for k in range(int((a1 - a0) / 2.6)):
    tt = a0 + .5 + k * 2.6; n = steps[min(len(steps) - 1, int(k * len(steps) / ((a1 - a0) / 2.6)))]
    P(tt, n, .36, .4 + .2 * (k % 2), bright=.5); P(tt + 1.3, steps[max(0, steps.index(n) - 2)], .2, .6, bright=.4)
    if k % 2 == 0: DR(tt, .16, f0=60, f1=40, dur=1.0, noise=.05)
P(S("x3") + .1, "A2", .5); P(S("q4") + .1, "D2", .5); DR(S("q4") + D("q4") * .68, .35)
# 肆：逐客（脉冲加紧）→ 上书（开阔）
for k in range(int((S("z5") - S("z1")) / 1.3)): DR(S("z1") + k * 1.3, .14 + .012 * k, f0=64, f1=42, dur=.9, noise=.05)
DR(S("z1") + D("z1") * .56, .55)
for k in range(10): P(S("z2") + D("z2") * .45 + k * .18, "A3", .16 + .012 * k, .5 + .03 * k, dur=1.2, bright=.7)
for k, n in enumerate(["D3", "A3", "D4", "F4", "A3", "D4", "A4", "D4"]): P(S("z6") + .1 + k * D("z6") / 8, n, .4, .3 + .05 * k, bright=.6)
DR(S("z8") + .5, .6); P(S("z8") + .55, "D3", .45); P(S("z9") + .5, "A2", .4); P(S("z9") + D("z9") * .5, "F3", .32); P(S("z9") + D("z9") * .68, "D4", .32, .7)
# 伍：韩非（两个声部，一高一低；药到之后只剩低音）
for k in range(4): P(S("h1") + .6 + k * 3.4, "A4", .22, .75, bright=.7); P(S("h1") + 2.3 + k * 3.4, "D3", .3, .25, bright=.35)
P(S("h7") + 1.0, "Eb3", .32, .3, bright=.3); P(S("h10"), "D2", .5); B(S("h11") + .4, "Eb4", .1, .7); P(S("h12") + D("h12") * .45, "D3", .3, .3); P(S("h13") + .4, "A2", .35)
# 陆：位极人臣（最满）→ 叹息
DR(S("p1") + .5, .75)
for k, n in enumerate(["D2", "A2", "D3", "F3", "A3", "D4"]): P(S("p1") + .5 + k * .09, n, .42, .2 + .12 * k, bright=.6)
B(S("p1") + 1.6, "D5", .12)
for k in range(int((S("p6") - S("p2")) / 2.2)): P(S("p2") + k * 2.2, ["F3", "D3", "C3", "A2"][k % 4], .34, .4, bright=.4)
DR(S("p2") + D("p2") * .28, .4); DR(S("p2") + D("p2") * .72, .4)
for k in range(8): P(S("p6") + .3 + k * D("p6") / 9, ["D4", "F4", "A4", "D5"][k % 4], .2 + .02 * k, .2 + .08 * k, dur=2, bright=.75)
P(S("p9") + .1, "D3", .5); P(S("p9") + D("p9") * .5, "A2", .45); P(S("p10") + 1.5, "D2", .4); B(S("p10") + 3.0, "A4", .07)
# 柒：沙丘
B(S("s1") + .2, "D4", .12); B(S("s3") + .2, "A3", .1, .3); B(S("s5") + 1.2, "F4", .07, .7); DR(S("s6") + .2, .3, f0=55, f1=36)
for i, q in enumerate(["s8", "s9", "s10", "s11", "s12"]): DR(S(q) - .05, .22 + .03 * i, f0=58, f1=38, dur=1.2, noise=.04)
for i in range(5): DR(S("s15") + .25 + i * .34, .5, f0=120, f1=60, dur=.5, noise=.6)
for k in range(int((S("s20") - S("s19")) / 1.7)):                      # 心跳
    DR(S("s19") + .2 + k * 1.7, .26, f0=52, f1=38, dur=.5, noise=.02); DR(S("s19") + .5 + k * 1.7, .18, f0=50, f1=36, dur=.5, noise=.02)
P(S("s20") + .2, "A3", .4, .6); P(S("s20") + D("s20") * .55, "D3", .45, .4); P(S("s21") + .3, "D2", .5); DR(S("s22") + D("s22") * .36, .4)
# 捌：一级一级往下走
down = ["D4", "C4", "A3", "G3", "F3", "D3", "C3", "A2", "D2"]; b0, b1 = S("d1"), S("d8")
for k in range(int((b1 - b0) / 2.5)): P(b0 + .4 + k * 2.5, down[min(8, int(k * 9 / ((b1 - b0) / 2.5)))], .36, .5, bright=.4); DR(b0 + .4 + k * 2.5, .14, f0=60, f1=40, dur=1.0, noise=.05)
P(S("d6") + .1, "D2", .55)
for i in range(12): put(dry, S("d9") + .2 + i * D("d9") * .5 / 12 * 1.0, tick(), .3 + .03 * i, .25)
for i in range(22): put(dry, S("d9") + D("d9") * .5 + i * (E("d10") - S("d9") - D("d9") * .5) / 22, tick(), .2 + .025 * i, .16 + .008 * i);
DR(S("d11") + D("d11") * .55, .55)
# 玖：三次叩门
t3 = S("t1") + D("t1") * .56; st = D("t1") * .13
for i in range(3): [put(dry, t3 + i * st + st * .5 + j * .16, knock(), .5, .4) or put(wet, t3 + i * st + st * .5 + j * .16, knock(), .5, .25) for j in range(2)]
P(S("t1") + .3, "D3", .35); DR(S("t5") - .05, .6); P(S("t5"), "Eb3", .35, .4, bright=.3)
for k in range(3): P(S("t7") + D("t7") * [.12, .5, .82][k], ["A2", "G2", "D2"][k], .4, .5, bright=.35)
# 拾：狱
DR(S("j1") - .1, .7, f0=70, f1=36, dur=2.2)
for k in range(3): DR(S("j2") + .1 + k * .42, .34, f0=110, f1=55, dur=.45, noise=.5)
DR(S("j4") + D("j4") * .72, .8, f0=90, f1=40, dur=2.0, noise=.5)
for i in range(3): put(dry, S("j7") + D("j7") * .45 + i * D("j7") * .16, knock(), .25 + .25 * i, .25)
for i in range(3): DR(S("j7") + D("j7") * .72 + i * .3, .28, f0=110, f1=55, dur=.4, noise=.5)
P(S("j8") + D("j8") * .5, "D2", .45); P(S("j11") + .3, "A2", .4); P(S("j11") + D("j11") * .5, "D2", .5)
# 终：开头的三声回来
DR(S("e1") + D("e1") * .72, .7, f0=70, f1=36, dur=2.4)
for tt, n in [(S("e2") + .3, "A3"), (S("e2") + 2.5, "G3"), (S("e2") + D("e2") * .55, "D3")]: P(tt, n, .5, .45)
P(S("e5") + .1, "D3", .45); P(S("e5") + .15, "A3", .3, .65); P(S("e8") + .1, "F3", .42); P(S("e8") + D("e8") * .5, "D3", .42)
P(S("e10") + .2, "A3", .42, .45); P(S("e11") + .2, "D4", .42, .6)
cl = S("e12") + D("e12") * .35 + 1.25; DR(cl, .85, f0=66, f1=34, dur=2.6, noise=.4)        # 仓门合上
P(E("e12") + 2.2, "D2", .5, dur=6); B(E("e12") + 2.4, "D4", .08)

# ---------- 混响 ----------
irn = int(3.2 * SR); ir = rng.normal(0, 1, (irn, 2)) * np.exp(-np.arange(irn) / (0.75 * SR))[:, None]; ir = lp(ir.T, 3500).T; ir[: int(.012 * SR)] = 0
rev = np.stack([fftconvolve(wet[:, c], ir[:, c])[:N] for c in range(2)], 1).astype(np.float32) * 0.035
music = dry + rev
# 静音窗口：连混响尾巴一起收掉
gate = envelope([(0, 1), (sil0 - .02, 1), (sil0 + .25, 0), (sil1 - .1, 0), (sil1 + .6, 1), (TOTAL - 1.2, 1), (TOTAL - .1, 0), (TOTAL + 2, 0)])
music *= gate[:, None]
music = music[: int(TOTAL * SR)]
music /= max(1e-6, np.abs(music).max()) / 0.8

# ---------- 旁白 + 闪避 ----------
nar, sr = sf.read(os.path.join(ROOT, "build", "narration.wav"), dtype="float32"); nar = resample_poly(nar, 2, 1).astype(np.float32)[: len(music)]
nar = np.pad(nar, (0, len(music) - len(nar)))
nar = hp(nar, 70).astype(np.float32); nar = np.tanh(nar / (np.percentile(np.abs(nar[np.abs(nar) > 0.01]), 99.5)) * 1.05) * 0.86     # 轻限幅
env = lp(np.abs(nar), 6); env = np.maximum.reduce([env, np.roll(env, int(.12 * SR)), np.roll(env, -int(.08 * SR))]); env = np.clip(lp(env, 3) / 0.06, 0, 1)
duck = 1 - 0.62 * env                                       # 有旁白时配乐压到约 1/3
MUSIC_GAIN = 0.85
mix = np.stack([nar, nar], 1) + music * duck[:, None] * MUSIC_GAIN
pk = np.abs(mix).max(); mix = mix / pk * 0.94 if pk > 0.94 else mix
mix = mix * 0.72                                            # 整体约 -14.5 LUFS，给平台二次压缩留余量
sf.write(os.path.join(ROOT, "build", "music.wav"), music, SR); sf.write(os.path.join(ROOT, "build", "mix.wav"), mix, SR)
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
print("music %.1fs | narration RMS %.1f dB | ducked-music RMS %.1f dB | silence window %.2f–%.2fs (music RMS there %.1f dB)" % (
    len(music) / SR, rms(nar[np.abs(nar) > .01]), rms(music * duck[:, None] * MUSIC_GAIN), sil0, sil1, rms((music * MUSIC_GAIN)[int((sil0 + .4) * SR): int((sil1 - .2) * SR)])))
