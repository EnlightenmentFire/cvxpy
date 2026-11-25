# -*- coding: utf-8 -*-
"""音效全部 numpy 合成：箭雨破空、中箭闷响、马嘶、火声、兵器碰撞、人潮、印章重击、转场风声。"""
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, lfilter
from timeline import build

SR = 48000
R = np.random.default_rng(74)


def bp(x, lo, hi, o=2):
    return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)


def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def arrow_whoosh(dur=0.32):
    n = int(dur * SR); x = R.normal(0, 1, n)
    # 频带从高到低扫，模拟掠过
    y = np.zeros(n); seg = 8
    for k in range(seg):
        a, b = k * n // seg, (k + 1) * n // seg
        f = 5200 - 3400 * k / seg
        y[a:b] = bp(x, f * 0.6, f * 1.3)[a:b]
    t = np.linspace(0, 1, n)
    e = np.exp(-((t - 0.55) ** 2) / 0.04)
    return y * e * 0.6


def thud():
    n = int(0.35 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (90 - 40 * t) * t) * np.exp(-t * 14)
    c = bp(R.normal(0, 1, n), 1500, 4000) * np.exp(-t * 60) * 0.5
    return (s + c) * 0.9


def neigh(dur=1.5):
    """马嘶：带强颤音的谐波音，先升后降，鼻腔共振峰，加气声"""
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    f0 = 520 + 420 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) * (1 - u) - 180 * u
    vib = 1 + 0.10 * np.sin(2 * np.pi * (14 + 6 * u) * t) * (0.4 + 0.6 * u)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    x = sum(np.sin(k * ph) / k ** 0.9 for k in range(1, 14))
    x = bp(x, 400, 4200) * 0.7 + bp(x, 1800, 2600) * 0.6
    br = bp(R.normal(0, 1, n), 1500, 6000) * 0.25
    e = env(n, 0.05, 0.5) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t))
    snort = np.zeros(n)
    return (x * 0.5 + br) * e * 0.55


def fire_bed(dur):
    n = int(dur * SR)
    rumble = lp(R.normal(0, 1, n), 300) * 0.5
    cr = np.zeros(n)
    k = int(dur * 18)
    for p in R.integers(0, n - 2000, k):
        L = R.integers(200, 1200)
        cr[p:p + L] += bp(R.normal(0, 1, L), 1500, 7000) * np.exp(-np.arange(L) / (L / 5)) * R.uniform(0.2, 1)
    return (rumble + cr * 0.5) * 0.35


def clash():
    n = int(0.4 * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + R.uniform(0, 6)) for f in (2100, 3330, 4720, 5900)) * np.exp(-t * 18)
    return (x * 0.25 + bp(R.normal(0, 1, n), 2000, 8000) * np.exp(-t * 40) * 0.6) * 0.6


def boom(dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (55 - 20 * t / dur) * t) * np.exp(-t * 2.2)
    nz = lp(R.normal(0, 1, n), 400) * np.exp(-t * 5) * 0.6
    return (s + nz) * 0.9


def crowd(dur):
    n = int(dur * SR)
    x = R.normal(0, 1, n)
    y = bp(x, 200, 1600) * 0.6 + bp(x, 400, 900) * 0.6
    return y * env(n, dur * 0.45, dur * 0.4) * 0.45


def wind(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = R.normal(0, 1, n)
    y = np.zeros(n)
    for k in range(6):
        a, b = k * n // 6, (k + 1) * n // 6
        y[a:b] = bp(x, 300 + 150 * np.sin(k), 1200)[a:b]
    return y * env(n, 0.8, 1.2) * 0.4


def swish(dur=0.6):
    n = int(dur * SR); x = R.normal(0, 1, n); t = np.linspace(0, 1, n)
    return bp(x, 600, 3000) * np.sin(np.pi * t) ** 2 * 0.35


def put(buf, t, x, g=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= len(buf):
        return
    x = x[: len(buf) - i] * g
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * l * 1.41
    buf[i:i + len(x), 1] += x * r * 1.41


def main():
    lines, total = build()
    ev = {d["v"]: d for d in lines}
    S = lambda v: ev[v]["start"]
    E = lambda v: ev[v]["end"]
    buf = np.zeros((int((total + 1) * SR), 2))
    # ---- 开场：箭雨破空 + 马嘶（第一帧就响）
    for k in range(26):
        t = R.uniform(0.0, 2.4)
        put(buf, t, arrow_whoosh(R.uniform(0.22, 0.4)), R.uniform(0.5, 1.0), R.uniform(-0.8, 0.8))
    put(buf, 1.55, thud(), 1.0, -0.2)
    put(buf, 1.9, neigh(1.6), 0.9, 0.3)
    put(buf, 0.0, fire_bed(E("bian_night") + 0.5), 0.6)
    for v in ["caohong", "river_escape"]:
        put(buf, S(v) - 0.3, fire_bed(ev[v]["dur"] + 0.6), 0.45)
    put(buf, S("caohong") + 0.3, neigh(1.3), 0.55, -0.3)
    # 汴水再败
    put(buf, S("west_arrow") + 2.4, boom(1.8), 0.7)
    for k in range(14):
        put(buf, S("west_arrow") + 1.6 + R.uniform(0, 0.8), arrow_whoosh(0.3), 0.4, R.uniform(-0.6, 0.6))
    # 收降人潮
    put(buf, S("tide_flash") - 0.2, crowd(3.0), 0.6)
    put(buf, S("tide_flash"), boom(2.0), 0.6)
    # 汴水会战
    t0 = S("battle_bian")
    for k in range(40):
        put(buf, t0 + R.uniform(0, ev["battle_bian"]["dur"]), clash(), R.uniform(0.25, 0.6), R.uniform(-0.8, 0.8))
    for k in range(30):
        put(buf, t0 + R.uniform(0, ev["battle_bian"]["dur"]), arrow_whoosh(0.3), R.uniform(0.3, 0.7), R.uniform(-0.8, 0.8))
    put(buf, t0, crowd(ev["battle_bian"]["dur"] + 1), 0.4)
    put(buf, S("battle_bian") + 3.0, neigh(1.3), 0.4, 0.5)
    put(buf, S("defeat_stamp") + 0.1, boom(2.0), 0.8)
    # 兖州
    put(buf, S("liudai_fall") + 0.6, boom(1.8), 0.7)
    put(buf, S("tide_in"), crowd(5.0), 0.35)
    # 寿张
    for v in ["scout_fail", "ambush"]:
        for k in range(18):
            put(buf, S(v) + R.uniform(0.5, ev[v]["dur"]), clash(), R.uniform(0.2, 0.45), R.uniform(-0.8, 0.8))
    put(buf, S("scout_fail") + 1.4, boom(1.6), 0.5)
    put(buf, S("baoxin_die") + 0.5, boom(2.0), 0.6)
    put(buf, S("wood_statue"), fire_bed(ev["wood_statue"]["dur"] + 0.8) * 0.5, 0.6)
    # 转色：人潮涌起
    put(buf, S("transform") - 1.0, crowd(6.5), 0.6)
    put(buf, S("transform") + 0.2, boom(2.5), 0.7)
    # 兖州叛变
    put(buf, S("revolt") + 0.8, boom(1.8), 0.5)
    # 下一集：风
    put(buf, S("next"), wind(min(8.0, total - S("next"))), 0.5)
    # 转场 swish：每个段落开头
    seen = set()
    for d in lines:
        if d["scene"] not in seen:
            seen.add(d["scene"])
            if d["start"] > 5:
                put(buf, d["start"] - 0.7, swish(0.8), 0.6)
    buf = np.clip(buf, -1, 1)
    sf.write("/tmp/claude-0/w74/audio/sfx.wav", buf.astype(np.float32), SR)
    print("sfx", total)


if __name__ == "__main__":
    main()
