# -*- coding: utf-8 -*-
"""全部声音程序生成（无第三方素材，可商用无版权问题）：
- 底乐：古琴式拨弦（加吟猱）、低音铺底、箫式气声长音、偶尔一声磬；五声 D 宫调，沉静但有流动感
- 音效：开场一声低沉的钟 + 手机轻振；朱印盖下的闷响
- 旁白轨：按 timeline.json 把逐句 wav 放到时间点上
usage: python audio.py stems    -> WORK/voice.wav WORK/music.wav WORK/sfx.wav
"""
import os, sys, json, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SR = 48000
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
VOICE = os.environ.get("VOICE_DIR", f"{WORK}/tts/proc")
R = np.random.default_rng(52)

SCALE = [0, 2, 4, 7, 9]            # D 宫五声
D3 = 146.83


def note_hz(deg, octv=0):
    o, k = divmod(deg, 5)
    return D3 * 2 ** ((SCALE[k] + 12 * (o + octv)) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "bandpass", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- 乐器
def guqin(f, dur=4.5, vel=1.0, slide=0.0, yin=True):
    """古琴式拨弦：加性合成，高次谐波衰减快；可带下滑音（slide 半音）与吟（微颤）。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    glide = 2 ** (slide * (1 - np.exp(-t / 0.35)) / 12)
    vib = 1 + (0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.4) / 0.6, 0, 1) if yin else 0)
    inst = f * glide * vib
    ph = 2 * np.pi * np.cumsum(inst) / SR
    y = np.zeros(n)
    for k in range(1, 10):
        amp = 1 / k ** 1.25 * (0.6 if k == 2 else 1)
        tau = 2.6 / (1 + 0.55 * (k - 1))
        y += amp * np.sin(k * ph * (1 + 0.0008 * k * k)) * np.exp(-t / tau)
    att = np.clip(t / 0.004, 0, 1)
    noise = R.normal(0, 1, n) * np.exp(-t / 0.02) * 0.25
    y = (y * att + lp(noise, 2500)) * vel
    # 木质共鸣：低通 + 一点 200Hz 箱体
    y = lp(y, 3200) + 0.15 * bp(y, 150, 300)
    return y * 0.22


def xiao(f, dur, vel=1.0):
    """箫式长音：基音 + 少量谐波 + 带通气声，慢起慢收，轻颤。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.clip(t / 0.6, 0, 1) * np.clip((dur - t) / 0.9, 0, 1)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.8) / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    breath = bp(R.normal(0, 1, n), f * 0.8, f * 3.2) * 0.35
    return (y + breath) * env * vel * 0.10


def bell(f, dur=9.0, vel=1.0, kind="zhong"):
    """钟/磬：非谐泛音，长衰减。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "zhong":
        parts = [(0.5, 1.0, 7.0), (1.0, 0.7, 5.0), (1.19, 0.35, 3.5), (1.5, 0.25, 3.0), (2.0, 0.3, 2.4), (2.52, 0.12, 1.6), (3.0, 0.08, 1.2)]
    else:   # 磬（铜磬）
        parts = [(1.0, 1.0, 6.0), (2.71, 0.45, 3.5), (5.15, 0.2, 1.8), (8.4, 0.08, 0.9)]
    y = np.zeros(n)
    for r_, a, tau in parts:
        det = 1 + R.uniform(-0.002, 0.002)
        y += a * np.sin(2 * np.pi * f * r_ * det * t) * np.exp(-t / tau) * (1 + 0.15 * np.sin(2 * np.pi * 1.3 * t))
    strike = lp(R.normal(0, 1, n) * np.exp(-t / 0.008), 1800) * 0.4
    y = (y + strike) * np.clip(t / 0.003, 0, 1)
    return y * vel * 0.25


def pad(dur, f=D3 / 2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / 23.0)
    y = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t + 1) + 0.25 * np.sin(2 * np.pi * f * 2 * t + 2)) * lfo
    air = lp(R.normal(0, 1, n), 500) * 0.25 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 17.0))
    return lp(y * 0.05 + air * 0.03, 900)


def thump(vel=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (70 + 40 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.09)
    y += lp(R.normal(0, 1, n), 1200) * np.exp(-t / 0.02) * 0.6
    return y * 0.35 * vel


def buzz():
    n = int(0.55 * SR); t = np.arange(n) / SR
    gate = ((t < 0.16) | ((t > 0.26) & (t < 0.42))).astype(float)
    y = np.sign(np.sin(2 * np.pi * 160 * t)) * gate
    y = lp(y, 400) * 0.08
    return y


def add(buf, x, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m] * gain


# ---------------------------------------------------------------- 编排
# 每个场景的音乐密度：(拨弦乐句间隔秒, 箫概率, 音量)
DENSITY = {
    "hook": (5.5, 0.0, 1.0), "verdict": (6.5, 0.0, 0.9), "sampling": (7.0, 0.0, 0.85), "sampling2": (7.5, 0.1, 0.85),
    "goyal": (7.0, 0.0, 0.85), "goyal2": (8.0, 0.0, 0.8), "metta": (6.0, 0.35, 0.95), "spiral": (6.0, 0.2, 0.95),
    "hype": (11.0, 0.0, 0.7), "bias": (12.0, 0.0, 0.65), "adverse": (10.0, 0.0, 0.7),
    "jingang": (7.0, 0.5, 1.0), "tanjing": (7.0, 0.5, 1.0), "mirror": (7.0, 0.3, 0.95),
    "breath": (6.5, 0.45, 1.0), "ending": (5.5, 0.6, 1.1),
}


def phrase(buf, t0, vol, flow=1.0):
    """一句古琴：3–6 个音，五声音阶上随机游走，末音落在宫或徵。"""
    nnotes = R.integers(3, 7)
    deg = R.choice([5, 7, 8, 9])
    t = t0
    for k in range(nnotes):
        step = R.choice([-2, -1, -1, 1, 1, 2])
        deg = int(np.clip(deg + step, 3, 12))
        if k == nnotes - 1:
            deg = min([5, 8, 10], key=lambda d: abs(d - deg))
        f = note_hz(deg)
        sl = R.choice([0, 0, 0, -1, 1]) if k == nnotes - 1 else 0
        v = vol * R.uniform(0.7, 1.0)
        add(buf, guqin(f, 4.5, v, slide=sl), t)
        if R.random() < 0.18:
            add(buf, guqin(f / 2, 4.5, v * 0.6), t + 0.01)   # 低八度散音
        t += R.choice([0.45, 0.6, 0.8, 1.0, 1.3]) / flow
    return t


def build_music(tl):
    total = tl["total"]
    n = int((total + 1) * SR)
    m = np.zeros(n)
    add(m, pad(total + 1), 0, 1.0)
    for sc in tl["scenes"]:
        gap, pxiao, vol = DENSITY[sc["kind"]]
        t = sc["t0"] + 0.8
        while t < sc["t1"] - 1.0:
            t_end = phrase(m, t, vol * 0.9)
            if R.random() < pxiao:
                deg = R.choice([5, 7, 8, 10])
                add(m, xiao(note_hz(deg, 1), R.uniform(2.5, 4.0), vol), t_end + 0.3)
            t = t_end + 1.4 * gap * R.uniform(0.75, 1.25)
    # 磬：大段落开头轻敲（不在开场，开场用钟）
    for sc in tl["scenes"]:
        if sc["id"] in ("s3", "s5", "s6", "s7b"):
            add(m, bell(note_hz(5, 1), 7, 0.5, "qing"), sc["t0"] + 0.2)
    # 结尾：慢慢收住，最后一声琴 + 磬
    end = tl["lines"][-1]["end"]
    add(m, guqin(note_hz(5), 6, 1.0), end + 0.6)
    add(m, guqin(note_hz(0), 6, 0.8), end + 0.62)
    fade_out = np.clip((total + 0.5 - np.arange(n) / SR) / 3.0, 0, 1)
    m *= fade_out
    # 简易混响：多抽头延迟
    rev = np.zeros_like(m)
    for d, g in ((0.031, 0.35), (0.053, 0.3), (0.089, 0.25), (0.137, 0.2), (0.211, 0.15), (0.347, 0.1)):
        k = int(d * SR); rev[k:] += m[:-k] * g
    m = m + lp(rev, 3000) * 0.8
    st = np.stack([m, np.roll(m, int(0.011 * SR)) * 0.96 + m * 0.04], 1)   # 轻微立体声
    return st


def build_sfx(tl):
    n = int((tl["total"] + 1) * SR)
    s = np.zeros(n)
    add(s, bell(98.0, 10, 1.0, "zhong"), 0.0)     # 开场：一声低沉的钟（首帧即响）
    add(s, buzz(), 0.30, 1.0)                      # 手机轻振，配合“你现在在想什么？”
    # 朱印盖下
    L = {x["id"]: x for x in tl["lines"]}
    stamps = [("s2b_07", 0.3)] + [("s4b_07", 0.4 + 0.9 * i) for i in range(3)] + \
             [("s5b_01", 1.0), ("s5b_01", 1.6)] + [(f"s5b_0{i+2}", 0.2) for i in range(3)]
    for lid, off in stamps:
        add(s, thump(0.9), L[lid]["start"] + off + 0.12)
    return np.stack([s, s], 1)


def build_voice(tl):
    n = int((tl["total"] + 1) * SR)
    v = np.zeros(n)
    for x in tl["lines"]:
        w, sr = sf.read(f"{VOICE}/{x['id']}.wav")
        assert sr == SR, sr
        if w.ndim > 1:
            w = w.mean(1)
        add(v, w, x["start"])
    return np.stack([v, v], 1)


if __name__ == "__main__":
    tl = json.load(open(f"{WORK}/timeline.json"))
    what = sys.argv[1:] or ["voice", "music", "sfx"]
    if "voice" in what:
        sf.write(f"{WORK}/voice.wav", build_voice(tl), SR, subtype="PCM_24")
    if "music" in what:
        m = build_music(tl)
        sf.write(f"{WORK}/music.wav", m / (np.abs(m).max() + 1e-9) * 0.7, SR, subtype="PCM_24")
    if "sfx" in what:
        sf.write(f"{WORK}/sfx.wav", build_sfx(tl), SR, subtype="PCM_24")
    print("ok", what)
