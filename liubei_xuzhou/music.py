# -*- coding: utf-8 -*-
"""原创配乐（numpy 程序合成，无任何外部素材，可商用）。
D 小调。乐器：低音弦乐铺底（加性合成＋慢起音＋颤音）、太鼓（扫频正弦＋噪声）、古琴（Karplus-Strong）、
低铜（滤波锯齿）。混响用合成脉冲响应卷积。
按 timeline.json 的章节排布：
  战争段（冷开场、二·救徐州、失与得）：太鼓 ostinato ＋ 低弦 ＋ 铜管长音（恢宏）
  让州段：古琴＋低弦（庄重）
  其余：低弦铺底＋零星古琴
python music.py  → /tmp/claude-0/work/audio/music.wav（48k 立体声）
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
OUT = "/tmp/claude-0/work/audio"
BPM = 72
BEAT = 60 / BPM
rng = np.random.default_rng(7)

# D 小调和声进行（每个和弦 2 小节 = 8 拍）
PROG = [("Dm", [38, 50, 53, 57]), ("Bb", [34, 46, 50, 53]), ("Gm", [31, 43, 46, 50]), ("A", [33, 45, 49, 52]),
        ("Dm", [38, 50, 53, 57]), ("F", [41, 48, 53, 57]), ("Gm", [31, 43, 46, 50]), ("A", [33, 45, 49, 52])]
SCALE = [50, 52, 53, 55, 57, 58, 60, 62, 64, 65, 67, 69]   # D 自然小调（D4 起）
PENTA = [50, 53, 55, 57, 60, 62, 65, 67, 69, 72]           # D 小调五声


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n); e[:na] = np.linspace(0, 1, na)
    nd = min(nd, n - na); e[na:na + nd] = np.linspace(1, s, nd)
    if nr > 0 and n > nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def strings(midi, dur, amp=0.1, bright=1800):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.07, 0.0, 0.06):
        f = mtof(midi + det) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6))
        ph = 2 * np.pi * np.cumsum(f) / SR
        # 锯齿近似（前 12 个谐波）
        for k in range(1, 13):
            if f[0] * k > 9000:
                break
            out += np.sin(k * ph) / k * (0.85 ** k)
    out = lp(out, bright)
    return out * env_adsr(n, min(1.2, dur * 0.3), 0.5, 0.85, min(1.5, dur * 0.35)) * amp / 3


def brass(midi, dur, amp=0.08):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = mtof(midi)
    ph = 2 * np.pi * f * t
    x = sum(np.sin(k * ph) / k for k in range(1, 16))
    cut = 400 + 1400 * env_adsr(n, 0.6, 0.8, 0.6, 0.8)
    # 时变低通：分块滤波
    y = np.zeros(n)
    blk = 4800
    for i in range(0, n, blk):
        y[i:i + blk] = lp(x[i:i + blk], float(cut[i]), 2)
    return y * env_adsr(n, 0.35, 0.6, 0.8, min(1.2, dur * 0.4)) * amp


def guqin(midi, dur=3.5, amp=0.25):
    f = mtof(midi)
    N = int(SR / f)
    n = int(dur * SR)
    buf = rng.uniform(-1, 1, N)
    buf = lp(buf, 3000)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % N]
        buf[i % N] = 0.996 * 0.5 * (buf[i % N] + buf[(i + 1) % N])
    # 吟猱：轻微滑音靠重采样近似 → 省略；加一点胴体共鸣
    out = lp(out, 2500) + 0.3 * hp(out, 1800)
    return out * amp * np.exp(-np.arange(n) / SR * 0.6)


def taiko(amp=0.6, big=False):
    dur = 1.6 if big else 0.9
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = (55 if big else 75) * (1 + 1.6 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (2.5 if big else 5))
    noise = lp(rng.normal(0, 1, n), 1800) * np.exp(-t * 30) * 0.5
    sub = np.sin(2 * np.pi * 38 * t) * np.exp(-t * 3) * (0.7 if big else 0.2)
    return (body + noise + sub) * amp


def reverb_ir(sec=3.2, decay=2.6):
    n = int(sec * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for c in range(2):
        r = rng.normal(0, 1, n) * np.exp(-t * decay)
        ir[:, c] = lp(r, 5000)
    ir[:int(0.012 * SR)] = 0
    return ir / np.abs(ir).sum(0).max() * 6


def place(buf, x, t0, pan=0.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    x = x[:len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * l
    buf[i:i + len(x), 1] += x * r


def build():
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    T = tl["end"]
    n = int((T + 4) * SR)
    pad = np.zeros((n, 2)); drum = np.zeros((n, 2)); pluck = np.zeros((n, 2))
    # 章节区间 → 情绪
    marks = {c["ch"]: c["t0"] for c in tl["cards"]}
    seg = [("war", 0.0, marks["c1"]), ("calm", marks["c1"], marks["c2"]), ("war", marks["c2"], marks["c3"]),
           ("solemn", marks["c3"], marks["c4"]), ("war_soft", marks["c4"], marks["c5"]), ("calm", marks["c5"], marks["c6"]),
           ("coda", marks["c6"], T)]
    mood_at = lambda tt: next((m for m, a, b in seg if a <= tt < b), "coda")
    bar = 4 * BEAT
    nchord = int(T / (2 * bar)) + 2
    for k in range(nchord):
        t0 = k * 2 * bar
        if t0 > T:
            break
        name, notes = PROG[k % len(PROG)]
        m = mood_at(t0 + 0.1)
        dur = 2 * bar + 1.2
        if m in ("war", "war_soft"):
            place(pad, strings(notes[0] - 12, dur, 0.16, 900), t0, -0.2)
            place(pad, strings(notes[0], dur, 0.10, 1400), t0, 0.2)
            for nn in notes[1:3]:
                place(pad, strings(nn, dur, 0.06, 1800), t0, rng.uniform(-0.5, 0.5))
            if m == "war":
                place(pad, brass(notes[0] - 12 + 12, dur * 0.9, 0.05), t0 + 0.05, 0)
        elif m == "solemn":
            place(pad, strings(notes[0] - 12, dur, 0.12, 700), t0, -0.2)
            place(pad, strings(notes[2], dur, 0.05, 1200), t0, 0.3)
        else:
            place(pad, strings(notes[0] - 12, dur, 0.10, 700), t0, -0.2)
            place(pad, strings(notes[1], dur, 0.045, 1100), t0, 0.25)
        # 古琴
        if m in ("solemn", "calm", "coda"):
            phr = rng.choice(PENTA, 4)
            for j, nn in enumerate(phr):
                if rng.random() < (0.75 if m == "solemn" else 0.5):
                    place(pluck, guqin(int(nn) - 12, 3.5, 0.22), t0 + j * BEAT * 2 + rng.uniform(0, 0.08), rng.uniform(-0.4, 0.4))
    # 太鼓 ostinato（战争段）：每小节 1. . 1 + 3 (+ 弱拍)
    tb = 0.0
    while tb < T:
        m = mood_at(tb + 0.01)
        if m in ("war", "war_soft"):
            a = 0.55 if m == "war" else 0.35
            place(drum, taiko(a, big=True), tb, 0)
            place(drum, taiko(a * 0.45), tb + BEAT * 1.5, -0.3)
            place(drum, taiko(a * 0.7), tb + BEAT * 2, 0.3)
            if m == "war":
                place(drum, taiko(a * 0.35), tb + BEAT * 3, -0.2)
                place(drum, taiko(a * 0.35), tb + BEAT * 3.5, 0.2)
        tb += bar
    ir = reverb_ir()
    wet_pad = np.stack([fftconvolve(pad[:, c], ir[:, c])[:n] for c in range(2)], 1)
    wet_pl = np.stack([fftconvolve(pluck[:, c], ir[:, c])[:n] for c in range(2)], 1)
    wet_dr = np.stack([fftconvolve(drum[:, c], ir[:, c] * 0.6)[:n] for c in range(2)], 1)
    mix = 0.55 * pad + 0.6 * wet_pad + 0.7 * pluck + 0.5 * wet_pl + 0.8 * drum + 0.35 * wet_dr
    # 章节过渡：段与段之间 2 秒推子
    gain = np.ones(n)
    for _, a, b in seg:
        i = int(a * SR); k = int(1.5 * SR)
        if i > k:
            gain[i - k:i + k] *= np.concatenate([np.linspace(1, 0.35, k), np.linspace(0.35, 1, k)])
    mix *= gain[:, None]
    # 结尾淡出
    e = int((T - 0.2) * SR)
    mix[e:] *= np.linspace(1, 0, n - e)[:, None] ** 2
    mix = hp(mix.T, 35).T
    mix /= np.abs(mix).max() + 1e-9
    mix *= 0.7
    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/music.wav", mix[:int((T + 0.5) * SR)].astype(np.float32), SR)
    print("music", T, "s")


if __name__ == "__main__":
    build()
