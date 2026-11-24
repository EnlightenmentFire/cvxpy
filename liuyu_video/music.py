# -*- coding: utf-8 -*-
"""自己合成的配乐（无采样素材）：低音铺底、拨弦（Karplus-Strong）、低鼓、锣、风声。
按时间轴分段控制强度；旁白处自动压低（sidechain duck）。"""
import math

import numpy as np
from scipy.signal import fftconvolve, lfilter, butter, sosfilt

SR = 48000
RNG = np.random.default_rng(404)


def note_hz(n):  # MIDI → Hz
    return 440.0 * 2 ** ((n - 69) / 12)


# D 商调五声：D E G A C（取 D 为宫附近的暗色）
SCALE = [50, 52, 55, 57, 60, 62, 64, 67, 69, 72]   # D3..C5


def env_adsr(n, a, d, s, r, sr=SR):
    t = np.arange(n) / sr
    e = np.ones(n)
    na, nd, nr = int(a * sr), int(d * sr), int(r * sr)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nd:
        e[na:na + nd] = np.linspace(1, s, min(nd, max(0, n - na)))
    e[na + nd:] = s
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def pluck(freq, dur, bright=0.5, sr=SR):
    """Karplus-Strong 拨弦，近似古琴/琵琶的空弦"""
    n = int(dur * sr)
    N = max(2, int(sr / freq))
    burst = RNG.uniform(-1, 1, N)
    b, a = butter(1, 1500 + 4000 * bright, fs=sr)
    burst = lfilter(b, a, burst)
    x = np.zeros(n); x[:N] = burst
    g = 0.996 - 0.002 * (freq / 400)
    den = np.zeros(N + 2); den[0] = 1.0; den[N] = -g * 0.5; den[N + 1] = -g * 0.5
    y = lfilter([1.0], den, x)
    y *= np.exp(-np.arange(n) / (sr * dur * 0.45))
    return y / (np.abs(y).max() + 1e-9)


def drum(dur=1.4, f0=58, sr=SR, hard=1.0):
    n = int(dur * sr)
    t = np.arange(n) / sr
    f = f0 * (1 + 1.4 * np.exp(-t * 28))
    ph = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t * (4.5 - 1.5 * hard))
    noise = RNG.normal(0, 1, n) * np.exp(-t * 40) * 0.35 * hard
    b, a = butter(2, 900, fs=sr)
    noise = lfilter(b, a, noise)
    return (body + noise) * 0.9


def gong(dur=6.0, f0=110, sr=SR):
    n = int(dur * sr)
    t = np.arange(n) / sr
    parts = [(1.0, 1.0), (1.52, 0.6), (2.27, 0.45), (2.94, 0.3), (3.7, 0.22), (4.9, 0.12)]
    y = np.zeros(n)
    for r, amp in parts:
        y += amp * np.sin(2 * np.pi * f0 * r * t + RNG.uniform(0, 6.28)) * np.exp(-t * (0.5 + r * 0.35))
    y *= np.minimum(1, t / 0.01)
    return y / np.abs(y).max()


def pad_tone(freqs, dur, sr=SR, cutoff=900):
    n = int(dur * sr)
    t = np.arange(n) / sr
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.25, 0.0, 0.27):
            ff = f * 2 ** (det / 12)
            # 软锯齿：前几次谐波
            for h in range(1, 7):
                y += np.sin(2 * np.pi * ff * h * t + RNG.uniform(0, 6.28)) / (h ** 1.3)
    b, a = butter(2, cutoff, fs=sr)
    y = lfilter(b, a, y)
    return y / (np.abs(y).max() + 1e-9)


def reverb_ir(sec=3.2, sr=SR):
    n = int(sec * sr)
    t = np.arange(n) / sr
    ir = RNG.normal(0, 1, (n, 2)) * np.exp(-t * 2.2)[:, None]
    sos = butter(2, 5000, fs=sr, output="sos")
    ir = sosfilt(sos, ir, axis=0)
    ir[0] = [1.0, 1.0]
    return ir / np.sqrt((ir ** 2).sum(0))[None, :]


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    l = math.cos((pan + 1) * math.pi / 4)
    r = math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l
    buf[i:i + len(x), 1] += x * gain * r


def compose(T, total=None):
    """T: Timeline。返回 (stereo 音乐, 强度包络说明)"""
    total = total or T.total
    n = int(total * SR) + SR
    dry = np.zeros((n, 2))
    wet_send = np.zeros((n, 2))
    sec = T.sec_start
    # 强度曲线（0..1）
    pts = [(0, 0.35), (sec["S1"], 0.35), (sec["S3"], 0.45), (sec["S4"], 0.5), (sec["S5"], 0.55),
           (sec["S6"], 0.62), (T.start("s6g"), 0.8), (T.start("s6h"), 0.5), (sec["S7"], 0.4), (sec["S8"], 0.45),
           (sec["S9"], 0.35), (T.total - 2, 0.2), (T.total + 1, 0.0)]
    tt = np.arange(n) / SR
    inten = np.interp(tt, [p[0] for p in pts], [p[1] for p in pts])

    # 1) 低音铺底：D2 + A2，缓慢起伏；按段落换和声根音
    roots = [(0, [38, 45]), (sec["S2"], [38, 45]), (sec["S3"], [41, 48]), (sec["S4"], [34, 41]),
             (sec["S5"], [38, 45]), (sec["S6"], [36, 43]), (T.start("s6g"), [38, 45]), (sec["S7"], [41, 48]),
             (sec["S8"], [34, 41]), (sec["S9"], [38, 45])]
    for i, (t0, notes) in enumerate(roots):
        t1 = roots[i + 1][0] if i + 1 < len(roots) else total + 1
        dur = t1 - t0 + 2.0
        y = pad_tone([note_hz(m) for m in notes], dur, cutoff=520)
        e = env_adsr(len(y), 1.8, 0.1, 1.0, 1.8)
        lfo = 0.85 + 0.15 * np.sin(2 * np.pi * np.arange(len(y)) / SR / 9.0)
        place(dry, y * e * lfo, max(0, t0 - 1.0), gain=0.30)
        place(wet_send, y * e * lfo, max(0, t0 - 1.0), gain=0.10)

    # 2) 高处的弦乐垫（只在中段出现）
    for t0, t1, notes in ((sec["S1"], sec["S3"], [62, 69]), (sec["S7"], sec["S8"], [65, 72]), (sec["S8"], sec["S9"], [62, 67])):
        y = pad_tone([note_hz(m) for m in notes], t1 - t0 + 2, cutoff=1400)
        place(dry, y * env_adsr(len(y), 3.0, 0.1, 1.0, 3.0), t0, gain=0.07)
        place(wet_send, y * env_adsr(len(y), 3.0, 0.1, 1.0, 3.0), t0, gain=0.10)

    # 3) 拨弦：稀疏五声动机
    motif = [62, 64, 67, 69, 67, 64, 62, 57]
    t = 2.0
    k = 0
    while t < total - 3:
        level = np.interp(t, tt[::SR], inten[::SR])
        gap = 2.8 - 1.4 * level + RNG.uniform(-0.4, 0.4)
        if not (T.start("s6e") < t < T.start("s6h")):
            m = motif[k % len(motif)] + (12 if RNG.random() < 0.15 else 0)
            y = pluck(note_hz(m), 3.2, bright=0.35 + 0.3 * RNG.random())
            pan = RNG.uniform(-0.5, 0.5)
            place(dry, y, t, gain=0.16 + 0.06 * level, pan=pan)
            place(wet_send, y, t, gain=0.22, pan=pan)
            k += 1
        t += gap

    # 4) 低鼓：起兵段起，脉冲渐密；覆舟山放火处滚奏
    def drums(t0, t1, bpm, gain, accent=4):
        beat = 60.0 / bpm
        i = 0
        t = t0
        while t < t1:
            hard = 1.0 if i % accent == 0 else 0.6
            place(dry, drum(f0=52 if i % accent == 0 else 60, hard=hard), t, gain=gain * hard, pan=RNG.uniform(-0.15, 0.15))
            place(wet_send, drum(f0=52, hard=0.5), t, gain=gain * 0.25)
            t += beat
            i += 1
    drums(T.start("s5b") - 0.2, T.start("s5h"), 60, 0.22)
    drums(sec["S6"] + 0.5, T.start("s6e"), 72, 0.24)
    drums(T.start("s6e"), T.start("s6g"), 84, 0.26)
    # 滚奏
    t0, t1 = T.start("s6g") - 0.4, T.start("s6h") - 0.6
    t = t0
    while t < t1:
        p = (t - t0) / max(1e-3, (t1 - t0))
        place(dry, drum(dur=0.6, f0=64, hard=0.5 + 0.5 * p), t, gain=0.12 + 0.14 * p, pan=RNG.uniform(-0.3, 0.3))
        t += 0.18 - 0.08 * p

    # 5) 锣：片名、每个章节、高潮收束
    hits = [(T.title_start + 0.05, 0.55, 98)] + [(sec[k] - 0.2, 0.32, 110) for k in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")]
    hits += [(T.start("s6h") - 0.3, 0.6, 87), (T.end_card + 0.1, 0.4, 98)]
    for t0, g, f in hits:
        y = gong(f0=f)
        place(dry, y, t0, gain=g * 0.5)
        place(wet_send, y, t0, gain=g * 0.6)

    # 6) 风声：开头与结尾
    for t0, t1, g in ((0, T.title_start + 3, 0.16), (sec["S9"] - 1, total, 0.14)):
        m = int((t1 - t0) * SR)
        w = RNG.normal(0, 1, (m, 2))
        sos = butter(2, [180, 900], btype="band", fs=SR, output="sos")
        w = sosfilt(sos, w, axis=0)
        mod = 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(m) / SR / 5.5 + np.array([[0.0, 1.3]]).T).T
        w = w * mod / (np.abs(w).max() + 1e-9)
        w *= env_adsr(m, 2.0, 0.1, 1.0, 2.0)[:, None]
        i = int(t0 * SR)
        dry[i:i + m] += w[: len(dry) - i] * g

    # 混响
    ir = reverb_ir()
    wet = np.stack([fftconvolve(wet_send[:, c], ir[:, c])[:n] for c in range(2)], 1)
    mix = dry + wet * 0.8
    mix *= (0.55 + 0.45 * inten)[:, None]
    # 首尾淡入淡出
    fi = int(1.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(2.5 * SR)
    end = int(total * SR)
    mix[end - fo:end] *= np.linspace(1, 0, fo)[:, None]
    mix[end:] = 0
    return mix[:end]


def duck(music, voice, sr=SR, depth_db=-12.0, attack=0.06, release=0.35, thr_db=-40.0):
    """voice: 单声道同长度。按人声包络压低音乐。"""
    win = int(0.02 * sr)
    k = len(voice) // win
    rms = np.sqrt((voice[: k * win].reshape(k, win) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    on = (db > thr_db).astype(float)
    g = np.zeros(k)
    a_c = math.exp(-0.02 / attack)
    r_c = math.exp(-0.02 / release)
    cur = 0.0
    for i in range(k):
        tgt = on[i]
        c = a_c if tgt > cur else r_c
        cur = tgt + (cur - tgt) * c
        g[i] = cur
    # 提前一点压（看前 80ms）
    look = 4
    g = np.maximum(g, np.concatenate([g[look:], np.zeros(look)]))
    gain_db = depth_db * g
    gain = 10 ** (np.repeat(gain_db, win) / 20)
    gain = np.concatenate([gain, np.full(len(voice) - len(gain), gain[-1] if len(gain) else 1.0)])
    return music * gain[:, None]
