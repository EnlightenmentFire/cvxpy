# -*- coding: utf-8 -*-
"""原创底乐（全部 numpy 合成，无第三方素材）：古琴式拨弦 + 磬 + 箫 + 低音铺底。
D 宫五声（D E F# A B），约 64 bpm，按 timeline 的段落变化密度。
python music.py  -> /tmp/claude-0/work/audio/music.wav（48k 立体声，未混音电平）
"""
import json, math, os
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
WK = "/tmp/claude-0/work"
R = np.random.default_rng(54)

def hz(m):  # midi -> Hz
    return 440.0 * 2 ** ((m - 69) / 12)

SCALE = [50, 52, 54, 57, 59]  # D3 E3 F#3 A3 B3
def deg(i, base=0):
    o, k = divmod(i, 5)
    return SCALE[k] + 12 * (o + base)


def qin(f, dur=4.5, amp=0.3, slide=0.0, vib=True):
    n = int(dur * SR); t = np.arange(n) / SR
    # 音高：起音略高后回落（按音）+ 吟（慢颤音）
    bend = slide * np.exp(-t * 6)
    v = (0.004 * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.5) / 0.8, 0, 1)) if vib else 0
    ph = 2 * np.pi * np.cumsum(f * (1 + bend + v)) / SR
    y = np.zeros(n)
    for h in range(1, 9):
        dec = 1.1 + 0.75 * h
        y += (1.0 / h ** 1.15) * np.sin(h * ph + R.uniform(0, 6)) * np.exp(-t * dec)
    # 拨弦噪声
    nz = R.normal(0, 1, n) * np.exp(-t * 60) * 0.25
    sos = butter(2, [800, 5000], "bandpass", fs=SR, output="sos")
    y += sosfilt(sos, nz)
    env = np.minimum(1, t / 0.004)
    return amp * y * env


def qing(f=hz(74), dur=9.0, amp=0.35):
    """磬/钵：非谐泛音 + 拍频，长尾。"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for ratio, a, dec in [(1, 1.0, 0.35), (1.004, 0.6, 0.38), (2.76, 0.5, 0.7), (2.77, 0.3, 0.75), (5.40, 0.25, 1.4), (8.93, 0.12, 2.4)]:
        y += a * np.sin(2 * np.pi * f * ratio * t + R.uniform(0, 6)) * np.exp(-t * dec)
    y += R.normal(0, 1, n) * np.exp(-t * 90) * 0.15
    return amp * y * np.minimum(1, t / 0.002)


def xiao(f, dur, amp=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.4) / 0.6, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    br = R.normal(0, 1, n)
    sos = butter(2, [f * 0.8, f * 3], "bandpass", fs=SR, output="sos")
    y += 0.35 * sosfilt(sos, br)
    a = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.6)
    return amp * y * np.clip(a, 0, 1)


def pad(total, sections):
    n = int(total * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for m, a in [(38, 0.045), (45, 0.032), (50, 0.02)]:
        f = hz(m)
        y += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.05 * t)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t + m))
    nz = R.normal(0, 1, n)
    sos = butter(2, 400, "lowpass", fs=SR, output="sos")
    y += 0.006 * sosfilt(sos, nz)
    return y


def place(buf, x, t0, pan=0.0):
    i = int(t0 * SR)
    if i >= buf.shape[0]: return
    x = x[: buf.shape[0] - i]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[i:i + len(x), 0] += x * l
    buf[i:i + len(x), 1] += x * r


def reverb(x, secs=3.2, wet=0.35):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = np.stack([R.normal(0, 1, n) * np.exp(-t * 2.2) for _ in range(2)], 1)
    sos = butter(1, 3500, "lowpass", fs=SR, output="sos")
    ir = sosfilt(sos, ir, axis=0); ir /= np.sqrt((ir ** 2).sum(0))
    out = np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return (1 - wet) * x + wet * out


def main():
    J = json.load(open(f"{WK}/timeline.json"))
    total = J["total"] + 1.0
    buf = np.zeros((int(total * SR), 2))
    # 段落：用场景名划分强度
    sc = J["scenes"]
    def scene_at(t):
        s = [x for x in sc if x["start"] <= t]
        return s[-1]["scene"] if s else "hook"
    dense = {"exp_emp": 0.6, "brain_emp": 0.5, "caveat1": 0.5, "limits": 0.4, "limits3": 0.4, "cortex_cav": 0.5}
    xiao_sc = {"exp_comp", "ink", "quote_dz1", "quote_dz2", "quote_dz3", "dawn", "scroll"}
    # 1) 开头磬（声音钩子）
    place(buf, qing(hz(74), 10, 0.55), 0.0, -0.1)
    place(buf, qing(hz(62), 10, 0.22), 0.02, 0.2)
    # 2) 古琴乐句
    t = 1.4; beat = 60 / 64
    phrase_i = 0
    while t < total - 4:
        s = scene_at(t)
        dens = dense.get(s, 1.0)
        nn = int(R.integers(3, 7))
        start = int(R.integers(2, 7))
        cur = start
        for k in range(nn):
            if R.random() < dens:
                f = hz(deg(cur))
                place(buf, qin(f, 4.0, 0.16 * (0.8 + 0.4 * R.random()), slide=R.choice([0, 0, 0.012, -0.008])), t, R.uniform(-0.4, 0.4))
                if R.random() < 0.25:   # 泛音式高八度轻点
                    place(buf, qin(f * 2, 2.5, 0.05, vib=False), t + 0.01, 0.3)
            t += beat * R.choice([1, 1, 1.5, 2, 0.5])
            cur = max(0, min(9, cur + int(R.choice([-2, -1, -1, 1, 1, 2]))))
        # 句尾落在宫/徵
        place(buf, qin(hz(deg(R.choice([0, 3, 5]))), 5.5, 0.14), t, 0)
        t += beat * R.choice([3, 4, 5])
        phrase_i += 1
        # 偶尔一声轻磬
        if phrase_i % 6 == 0:
            place(buf, qing(hz(R.choice([69, 74])), 8, 0.12), t - 1.0, R.uniform(-0.3, 0.3))
    # 3) 箫：在指定场景里慢长音
    for x in sc:
        if x["scene"] in xiao_sc:
            tt = x["start"] + 1.0
            while tt < x["end"] - 3:
                d = float(R.uniform(3.0, 5.5))
                place(buf, xiao(hz(deg(int(R.integers(5, 9)))), d, 0.07), tt, 0.25)
                tt += d + float(R.uniform(1.5, 4))
    # 4) 铺底
    p = pad(total, sc)
    buf[:, 0] += p; buf[:, 1] += p
    # 5) 场景切换处的轻磬（大段落）
    for x in sc:
        if x["scene"] in ("exp_intro", "define", "resource", "limits", "scroll"):
            place(buf, qing(hz(74), 9, 0.18), x["start"], 0.0)
    buf = reverb(buf)
    # 淡入淡出
    n = len(buf); fi = int(0.02 * SR); fo = int(4 * SR)
    buf[:fi] *= np.linspace(0, 1, fi)[:, None]
    buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    buf /= np.abs(buf).max() + 1e-9
    buf *= 0.7
    os.makedirs(f"{WK}/audio", exist_ok=True)
    sf.write(f"{WK}/audio/music.wav", buf.astype(np.float32), SR, subtype="FLOAT")
    print("music", round(n / SR, 1), "s")


if __name__ == "__main__":
    main()
