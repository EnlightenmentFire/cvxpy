# -*- coding: utf-8 -*-
"""配乐与混音：全部用 numpy 现场合成（无任何外部素材，版权自有）。

  python tools/music.py        # 读 build/timeline.json + build/vo.wav → build/music.wav、build/audio.wav
上半段：低沉鼓点 + 弦乐铺底；s6 司马欣在宫门外：音乐几乎收掉，只留低频心跳；s8 很轻。
旁白出现时自动压低音乐（侧链式闪避）。
"""
import json, math, pathlib, sys
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

ROOT = pathlib.Path(__file__).resolve().parent.parent
SR = 48000
tl = json.load(open(ROOT / "build" / "timeline.json", encoding="utf-8"))
TOTAL = tl["total"]
N = int(TOTAL * SR) + SR
L = {l["id"]: (l["start"], l["end"]) for l in tl["lines"]}
SG = {k: (v["start"], v["end"]) for k, v in tl["segs"].items()}
st = lambda i: L[i][0]
en = lambda i: L[i][1]
rng = np.random.default_rng(20240)

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(n):
    name, octv = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((NOTE[name] - 9) / 12 + (octv - 4))


CH = {
    "Dm": ["D2", "A2", "D3", "F3", "A3"], "Bb": ["Bb1", "F2", "Bb2", "D3", "F3"], "Gm": ["G1", "D2", "G2", "Bb2", "D3"],
    "A5": ["A1", "E2", "A2", "E3"], "D5": ["D2", "A2", "D3", "A3"], "F": ["F2", "C3", "F3", "A3", "C4"], "C": ["C2", "G2", "C3", "E3", "G3"],
    "Cm": ["C2", "G2", "C3", "Eb3", "G3"], "Ab": ["Ab1", "Eb2", "Ab2", "C3", "Eb3"], "Fm": ["F1", "C2", "F2", "Ab2", "C3"],
    "G5": ["G1", "D2", "G2", "D3"], "C5": ["C2", "G2", "C3"],
}

music = np.zeros((N, 2), dtype=np.float32)
dry = np.zeros((N, 2), dtype=np.float32)       # 鼓/心跳：少混响


def env(n, a, r):
    e = np.ones(n, dtype=np.float32)
    na, nr = min(n // 2, int(a * SR)), min(n // 2, int(r * SR))
    if na > 0:
        e[:na] = np.sin(np.linspace(0, np.pi / 2, na)) ** 2
    if nr > 0:
        e[-nr:] = np.cos(np.linspace(0, np.pi / 2, nr)) ** 2
    return e


def pad(t0, dur, chord, amp=0.3, attack=2.5, release=3.5, bright=1.0, trem=0.0):
    """弦乐铺底：每个音三把“琴”微失谐，谐波按 1/n 衰减。"""
    i0 = max(0, int(t0 * SR)); n = min(N - i0, int(dur * SR))
    if n <= 0:
        return
    t = np.arange(n) / SR
    out = np.zeros((n, 2), dtype=np.float32)
    for k, name in enumerate(CH[chord] if isinstance(chord, str) else chord):
        f = hz(name)
        w = 1.0 if k < 2 else 0.8
        for d, pan in ((-0.0035, 0.25), (0.0, 0.5), (0.004, 0.75)):
            ff = f * (1 + d)
            vib = 1 + 0.0025 * np.sin(2 * np.pi * (4.6 + 0.4 * rng.random()) * t + rng.random() * 6.28) * np.clip(t / 2.0, 0, 1)
            ph = 2 * np.pi * np.cumsum(ff * vib) / SR + rng.random() * 6.28
            s = np.zeros(n, dtype=np.float32)
            for h in range(1, 9):
                if ff * h > 5200:
                    break
                s += (np.sin(ph * h) / h ** (1.25 / bright)).astype(np.float32)
            sw = 0.75 + 0.25 * np.sin(2 * np.pi * (0.13 + 0.05 * rng.random()) * t + rng.random() * 6.28)   # 弓压起伏
            s *= sw.astype(np.float32) * w
            out[:, 0] += s * (1 - pan); out[:, 1] += s * pan
    if trem > 0:
        out *= (1 - trem * 0.5 * (1 + np.sin(2 * np.pi * 9.5 * t)))[:, None].astype(np.float32)
    out *= (env(n, attack, release) * amp / 6.0)[:, None]
    music[i0:i0 + n] += out


def drum(t0, amp=0.6, f0=112, f1=44, dec=0.55):
    """低沉大鼓：正弦下滑 + 一点鼓皮噪声。"""
    i0 = int(t0 * SR); n = min(N - i0, int(1.6 * SR))
    if i0 < 0 or n <= 0:
        return
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.05)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dec)
    s += 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.52) / SR) * np.exp(-t / (dec * 0.45))
    nz = rng.normal(0, 1, n) * np.exp(-t / 0.035) * 0.35
    sos = butter(2, 900, "low", fs=SR, output="sos")
    s = s + sosfilt(sos, nz)
    s = np.tanh(s * 2.4) / np.tanh(2.4)            # 轻度饱和：补出手机小喇叭听得见的中频泛音
    s *= np.clip(t / 0.004, 0, 1) * amp
    pan = 0.5 + (rng.random() - 0.5) * 0.12
    dry[i0:i0 + n, 0] += (s * (1 - pan) * 2).astype(np.float32); dry[i0:i0 + n, 1] += (s * pan * 2).astype(np.float32)


def heartbeat(t0, t1, amp=0.5, period=1.08):
    t = t0
    while t < t1:
        k = min(1.0, (t - t0) / 1.5, (t1 - t) / 1.5 + 0.2)
        drum(t, amp * k, f0=118, f1=56, dec=0.15)
        drum(t + 0.27, amp * 0.7 * k, f0=104, f1=52, dec=0.19)
        t += period


def rumble(t0, t1, amp=0.2, lo=28, hi=90):
    i0 = int(t0 * SR); n = min(N - i0, int((t1 - t0) * SR))
    if n <= 0:
        return
    nz = rng.normal(0, 1, (n, 2)).astype(np.float32)
    sos = butter(4, [lo, hi], "band", fs=SR, output="sos")
    s = sosfilt(sos, nz, axis=0)
    s = s / (np.abs(s).max() + 1e-9)
    music[i0:i0 + n] += (s * env(n, min(3.0, (t1 - t0) / 2), min(2.0, (t1 - t0) / 2))[:, None] * amp).astype(np.float32)


def cycle(t0, t1, chords, step=8.0, amp=0.3, **kw):
    t, k = t0, 0
    while t < t1 - 0.5:
        d = min(step, t1 - t)
        pad(t - 1.2, d + 3.2, chords[k % len(chords)], amp, **kw)
        t += step; k += 1


def beat(t0, t1, period=2.0, amp=0.45, ghost=True, skip=()):
    t, k = t0, 0
    while t < t1:
        if not any(a <= t < b for a, b in skip):
            drum(t, amp * (1.0 if k % 2 == 0 else 0.8))
            if ghost:
                drum(t + period * 0.62, amp * 0.32, f0=90, f1=50, dec=0.3)
        t += period; k += 1


# ---------------- 编排 ----------------
s = SG
# s1 冷启动：空五度长音 + 两记鼓
pad(0.2, st("s1_07") + 1.0, "D5", 0.32, attack=3.0, release=3.0, bright=0.9)
drum(en("s1_01") - 0.25, 0.55); drum(st("s1_03") - 0.1, 0.4); drum(st("s1_06") - 0.05, 0.45)
pad(st("s1_07") - 0.5, s["title"][0] - st("s1_07") + 1.2, "Dm", 0.36)
# 片名
drum(s["title"][0] + 0.35, 0.95, dec=0.9); drum(s["title"][0] + 1.25, 0.5)
pad(s["title"][0], 4.6, "Dm", 0.5, attack=0.5, release=3.0, bright=1.25)
# s2 一句兵法：只有弦乐
cycle(s["s2"][0] + 0.5, s["s2"][1], ["Dm", "Bb", "Gm", "A5"], 8.5, 0.34, bright=0.95)
drum(st("s2_05") - 0.05, 0.4); drum(st("s2_08") + 1.0, 0.5, dec=0.8)
# s3 周亚夫：鼓点 + 弦乐
drum(s["s3"][0] + 0.15, 0.85, dec=0.9)
cycle(s["s3"][0] + 0.3, s["s3"][1], ["Dm", "Bb", "Gm", "A5"], 8.0, 0.3)
beat(st("s3_01"), en("s3_07"), 2.0, 0.4)
beat(st("s3_09"), en("s3_11"), 2.0, 0.42)
drum(st("s3_12") - 0.05, 0.85, dec=0.9); drum(en("s3_12") + 0.1, 0.5)
beat(st("s3_14"), s["s3"][1] - 1.0, 2.6, 0.32, ghost=False)
# s4 等：断粮（鼓）→ 夜惊（震音）→ 西北（重击）→ 追击（加快）→ 形篇（暖）
cycle(s["s4"][0], st("s4_03"), ["Dm", "Gm"], 8.0, 0.28)
beat(st("s4_01"), st("s4_03") - 0.6, 2.0, 0.4)
pad(st("s4_03") - 0.5, en("s4_05") - st("s4_03") + 1.5, "A5", 0.34, attack=3.0, release=3.5, trem=0.85, bright=1.2)
rumble(st("s4_03"), en("s4_05") + 0.5, 0.22)
pad(st("s4_05") + 1.0, st("s4_07") - st("s4_05") + 1.0, "D5", 0.2, bright=0.8)
cycle(st("s4_07"), st("s4_11"), ["Gm", "A5", "Dm"], 7.0, 0.28)
beat(st("s4_07"), st("s4_08") + 0.3, 2.0, 0.36)
drum(st("s4_08") + 1.5, 0.9, dec=0.8)
beat(st("s4_10") + 1.6, st("s4_11") - 0.3, 1.0, 0.45, ghost=False)
drum(st("s4_11") + 0.1, 0.9, dec=1.0)
cycle(st("s4_11") + 0.5, s["s4"][1], ["Bb", "F", "Dm"], 6.0, 0.3, bright=1.1)
# s5 章邯：换调（C 小调），鼓更沉
drum(s["s5"][0] + 0.15, 0.85, dec=0.9)
cycle(s["s5"][0] + 0.3, s["s5"][1], ["Cm", "Ab", "Fm", "G5"], 8.0, 0.3)
beat(st("s5_02"), st("s5_07") - 0.5, 2.4, 0.38)
beat(st("s5_07"), st("s5_08") - 0.2, 1.2, 0.5, ghost=False)
drum(st("s5_08") + 0.1, 0.8, dec=1.0)
# s6 后方先塌：相持（稀疏）→ 宫门外（几乎无乐，只留心跳）→ 两封“信”（低音长音）→ 线断（轰鸣）
cycle(s["s6"][0], st("s6_03") + 2.0, ["Cm", "Fm"], 9.0, 0.24, bright=0.85)
beat(st("s6_01") + 0.5, st("s6_03"), 4.8, 0.3, ghost=False)
pad(st("s6_03") + 1.5, en("s6_05") - st("s6_03"), "C5", 0.07, attack=4.0, release=4.0, bright=0.6)
heartbeat(st("s6_04") - 0.8, en("s6_05") + 0.4, 0.62)
heartbeat(en("s6_05") + 0.6, en("s6_08"), 0.3, period=1.2)
pad(st("s6_06") - 1.0, st("s6_12") - st("s6_06") + 2.0, "C5", 0.16, attack=4.0, release=4.0, bright=0.7)
pad(st("s6_09") - 0.5, st("s6_12") - st("s6_09") + 2.0, ["Ab1", "Eb2", "Ab2"], 0.14, attack=3.0, release=4.0, bright=0.7)
cycle(st("s6_12"), s["s6"][1], ["Fm", "G5", "Cm"], 7.5, 0.28)
rumble(st("s6_13"), en("s6_14") + 1.5, 0.3)
drum(st("s6_14") + 0.3, 0.9, dec=1.1)
drum(st("s6_15") + 3.3, 0.7); drum(st("s6_15") + 4.2, 0.85, dec=0.9)
# s7 粮少：一根细弦，停一拍
pad(st("s7_01"), en("s7_03") - st("s7_01") + 0.3, ["G3", "G4"], 0.08, attack=3.0, release=1.2, bright=0.7)
drum(st("s7_02") - 0.05, 0.35, dec=0.8)
pad(st("s7_05") - 0.3, s["s7"][1] - st("s7_05") + 1.5, "Cm", 0.2, attack=3.0, release=4.0, bright=0.85)
drum(st("s7_06") + 0.9, 0.5, dec=1.0)
# s8 回到周亚夫：很轻
drum(s["s8"][0] + 0.15, 0.6, dec=0.9)
cycle(s["s8"][0] + 0.3, st("s8_10") - 0.5, ["Dm", "Bb", "Gm", "A5"], 9.0, 0.13, bright=0.8)
drum(st("s8_10") + 1.6, 0.3, f0=70, f1=40, dec=1.2)
cycle(st("s8_11"), s["s8"][1], ["Bb", "Gm", "D5"], 9.0, 0.13, bright=0.8)
# s9 断点
cycle(s["s9"][0], s["s9"][1], ["Dm", "Bb", "A5"], 8.0, 0.26)
drum(st("s9_02") - 0.05, 0.6, dec=0.9); drum(st("s9_04") + 2.4, 0.7, dec=1.1); drum(st("s9_06") + 1.0, 0.5)
# s10 收尾：转暖，空五度收
cycle(s["s10"][0], st("s10_03"), ["F", "C", "Dm"], 7.0, 0.26, bright=1.1)
pad(st("s10_03") - 0.5, TOTAL - st("s10_03") + 0.3, "D5", 0.3, attack=2.0, release=3.2)
drum(st("s10_04") - 0.05, 0.6, dec=1.0); drum(s["end"][0] + 0.6, 0.45, dec=1.2)

# ---------------- 混响 / 母带 ----------------
ir_n = int(2.6 * SR)
tt = np.arange(ir_n) / SR
ir = (rng.normal(0, 1, (ir_n, 2)) * np.exp(-tt / 0.75)[:, None]).astype(np.float32)
sos = butter(2, [180, 5200], "band", fs=SR, output="sos")
ir = sosfilt(sos, ir, axis=0); ir /= np.sqrt((ir ** 2).sum(0))[None, :]
wet = np.stack([fftconvolve(music[:, k], ir[:, k])[:N] for k in range(2)], 1)
wetd = np.stack([fftconvolve(dry[:, k], ir[:, k])[:N] for k in range(2)], 1)
bus = music * 0.75 + wet * 0.5 + dry * 1.0 + wetd * 0.16
sos = butter(2, 26, "high", fs=SR, output="sos")
bus = sosfilt(sos, bus, axis=0)
bus = bus / (np.abs(bus).max() + 1e-9) * 0.8

# ---------------- 旁白 + 闪避 ----------------
vo, sr = sf.read(str(ROOT / "build" / "vo.wav"), dtype="float32")
assert sr == SR
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
sosv = butter(2, 70, "high", fs=SR, output="sos")
vo = sosfilt(sosv, vo)
# 轻压缩：让旁白更“贴”
hop = 480
frames = N // hop
rms = np.sqrt(np.mean(vo[:frames * hop].reshape(frames, hop) ** 2, axis=1) + 1e-10)
ref = np.percentile(rms[rms > 0.005], 75) if (rms > 0.005).any() else 0.05
g = np.minimum(1.0, (ref / np.maximum(rms, 1e-4)) ** 0.35)
g = np.interp(np.arange(N), np.arange(frames) * hop + hop / 2, g)
vo = vo * g
vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
# 闪避包络：旁白出现 → 音乐降到 ~38%，释放 0.6s
act = (rms > max(0.004, ref * 0.08)).astype(np.float32)
a_up, a_dn = math.exp(-1 / (0.06 * SR / hop)), math.exp(-1 / (0.6 * SR / hop))
e = np.zeros(frames, dtype=np.float32); v = 0.0
for i in range(frames):
    v = a_up * v + (1 - a_up) * act[i] if act[i] > v else a_dn * v + (1 - a_dn) * act[i]
    e[i] = v
duck = 1 - 0.62 * np.interp(np.arange(N), np.arange(frames) * hop + hop / 2, e)
MUSIC_GAIN = 0.62
mus = bus * duck[:, None] * MUSIC_GAIN
mix = mus + (vo * 0.92)[:, None]
pk = np.abs(mix).max()
if pk > 0.97:
    mix = mix / pk * 0.97
n_out = int(TOTAL * SR)
sf.write(str(ROOT / "build" / "music.wav"), mus[:n_out], SR)
sf.write(str(ROOT / "build" / "audio.wav"), mix[:n_out], SR)
print("music/audio written", round(n_out / SR, 2), "s; peak", round(float(pk), 3))
