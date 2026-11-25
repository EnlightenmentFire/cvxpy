# -*- coding: utf-8 -*-
"""原创配乐（全部 numpy 合成，无任何第三方采样/曲库）：古琴式拨弦、泛音、磬、箫、铺底。
D 宫五声（D E F# A B）。按场景分段换情绪，段间交叉。
usage: python music.py  -> $WORK/music.wav, $WORK/bell.wav（开场磬声单独一轨，两个版本都用）"""
import os, sys, json, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SR = 48000
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
rng = np.random.default_rng(56)

PENTA = [0, 2, 4, 7, 9]  # D 宫


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def scale_note(deg, base=50):  # base 50 = D3
    o, i = divmod(deg, 5)
    return base + 12 * o + PENTA[i]


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "bandpass", fs=SR, output="sos"), x)


def guqin(f, dur, vel=1.0, vib=True, slide=0.0):
    """拨弦：加性分音、高次衰减快、拨弦噪声、尾部吟猱与滑音。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    fm = np.ones(n) * f
    if vib:
        fm *= 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.35) / 0.4, 0, 1)
    if slide:
        fm *= 2 ** (slide / 12 * np.clip((t - 0.25) / 0.5, 0, 1))
    ph = 2 * np.pi * np.cumsum(fm) / SR
    y = np.zeros(n)
    for k in range(1, 13):
        if f * k > 9000:
            break
        a = (1 / k ** 1.25) * (0.6 + 0.4 * rng.random()) * (1.0 if k % 2 else 0.75)
        tau = 2.6 / (1 + 0.55 * (k - 1))
        y += a * np.sin(k * ph * (1 + 0.0004 * k * k)) * env_exp(n, tau)
    att = np.clip(t / 0.004, 0, 1)
    nz = rng.standard_normal(n) * env_exp(n, 0.012) * 0.25
    y = y * att + bp(nz, 800, 4000)
    y = lp(y, 3800)
    return y * vel * 0.25


def harmonic(f, dur, vel=1.0):
    """泛音：清亮、长衰减。"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * 2 * f * t) * env_exp(n, 0.8)
    y *= env_exp(n, 2.8) * np.clip(t / 0.003, 0, 1)
    return y * vel * 0.16


def qing(f, dur=9.0, vel=1.0):
    """磬：非谐分音。"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for r, a, tau in [(1, 1.0, 4.5), (2.32, 0.55, 3.0), (4.25, 0.35, 1.8), (6.63, 0.22, 1.1), (9.38, 0.12, 0.6), (1.006, 0.5, 4.0)]:
        y += a * np.sin(2 * np.pi * f * r * t + rng.random() * 6) * env_exp(n, tau)
    y *= np.clip(t / 0.002, 0, 1)
    strike = bp(rng.standard_normal(n) * env_exp(n, 0.006), 1500, 6000) * 0.3
    return (y + strike) * vel * 0.22


def xiao(notes, vel=1.0):
    """箫：notes=[(start, dur, midi)] 连奏。返回 (offset, signal)。"""
    end = max(s + d for s, d, _ in notes) + 0.6
    n = int(end * SR); t = np.arange(n) / SR
    f = np.zeros(n); amp = np.zeros(n)
    for s, d, m in notes:
        i0, i1 = int(s * SR), int((s + d) * SR)
        f[i0:i1] = midi_hz(m)
        seg = np.arange(i1 - i0) / SR
        a = np.clip(seg / 0.18, 0, 1) * np.clip((d - seg) / 0.25, 0, 1)
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
    # 平滑音高（滑音）
    nz = f > 0
    idx = np.where(nz, np.arange(n), 0); np.maximum.accumulate(idx, out=idx)
    f = f[idx]; f[f == 0] = midi_hz(notes[0][2])
    k = int(0.06 * SR); f = np.convolve(f, np.ones(k) / k, mode="same")
    f *= 1 + 0.006 * np.sin(2 * np.pi * 4.8 * t) * amp
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    breath = bp(rng.standard_normal(n), 900, 3200) * 0.10
    amp = np.convolve(amp, np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same")
    return lp((y + breath) * amp, 4200) * vel * 0.14


def pad(dur, midis, vel=1.0, dark=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for j, m in enumerate(midis):
        f = midi_hz(m)
        for det in (-0.12, 0.0, 0.11):
            fd = f * 2 ** (det / 12)
            y += np.sin(2 * np.pi * fd * t + rng.random() * 6) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + 0.017 * j) * t + j)) \
                 + 0.25 * np.sin(4 * np.pi * fd * t) * (1 - dark)
    y = lp(y, 900 - 500 * dark)
    fade = np.clip(t / 3.0, 0, 1) * np.clip((dur - t) / 3.0, 0, 1)
    return y * fade * vel * 0.035


def place(buf, sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 < 0:
        sig = sig[-i0:]; i0 = 0
    if i0 >= buf.shape[0] or len(sig) == 0:
        return
    sig = sig[: buf.shape[0] - i0]
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    buf[i0:i0 + len(sig), 0] += sig * gain * l * 1.41
    buf[i0:i0 + len(sig), 1] += sig * gain * r * 1.41


# ---------------------------------------------------------------- 段落写法
MOODS = {
    # mood: (拨弦密度 notes/秒, 音区 base, 泛音?, 铺底和弦, 暗度, 箫?)
    "hook":   dict(rate=1.1, base=50, harm=0.15, chord=[38, 45, 50], dark=0.1, xiao=False, bells=0),
    "realms": dict(rate=0.6, base=50, harm=0.25, chord=[38, 45, 54], dark=0.0, xiao=False, bells=9),
    "hell":   dict(rate=0.35, base=43, harm=0.0, chord=[35, 42, 47], dark=0.8, xiao=False, bells=0),
    "door":   dict(rate=0.6, base=50, harm=0.2, chord=[38, 45, 54], dark=0.2, xiao=True, bells=0),
    "ghost":  dict(rate=1.4, base=45, harm=0.0, chord=[33, 40, 45], dark=0.6, xiao=False, bells=0, ostinato=True),
    "ghost2": dict(rate=0.6, base=50, harm=0.2, chord=[38, 45, 50], dark=0.2, xiao=False, bells=0),
    "heaven": dict(rate=1.0, base=62, harm=0.6, chord=[50, 57, 62], dark=0.0, xiao=False, bells=0),
    "fade":   dict(rate=0.4, base=62, harm=0.3, chord=[50, 57], dark=0.5, xiao=False, bells=0),
    "asura":  dict(rate=1.6, base=45, harm=0.0, chord=[33, 40], dark=0.5, xiao=False, bells=0, ostinato=True),
    "human":  dict(rate=0.7, base=50, harm=0.2, chord=[38, 45, 54], dark=0.1, xiao=True, bells=0),
    "bounds": dict(rate=0.45, base=50, harm=0.15, chord=[38, 45, 50], dark=0.2, xiao=False, bells=12),
    "end":    dict(rate=0.8, base=50, harm=0.3, chord=[38, 45, 54, 57], dark=0.0, xiao=True, bells=0),
}
SEC_LU = {"hook": -21.0, "realms": -22.0, "hell": -24.0, "door": -22.0, "ghost": -23.0, "ghost2": -22.5, "heaven": -21.5,
          "fade": -23.5, "asura": -23.0, "human": -22.0, "bounds": -22.5, "end": -21.0}
SCENE_MOOD = {"s01": "hook", "s02": "hook", "s03": "hook", "s04": "realms", "s05": "realms", "s06": "realms",
              "s07": "hell", "s08": "hell", "s09": "door", "s10": "ghost", "s11": "ghost", "s12": "ghost2",
              "s13": "heaven", "s14": "fade", "s15": "asura", "s16": "human", "s17": "human", "s18": "bounds",
              "s19": "end", "s20": "end"}


def section(t0, t1, mood, buf, seed):
    r = np.random.default_rng(seed)
    M = MOODS[mood]
    dur = t1 - t0
    place(buf, pad(dur + 3, M["chord"], 1.0, M["dark"]), t0 - 1.5, 1.0)
    # 拨弦：乐句 = 4–7 个音，句间留白
    t = t0 + 0.5
    deg = 5
    beat = 60 / 66
    while t < t1 - 1.0:
        nphr = r.integers(4, 8)
        if M.get("ostinato"):
            patt = [0, 2, 1, 2] if mood == "ghost" else [0, 0, 3, 0, 1]
            for k in range(nphr * 2):
                if t > t1 - 1: break
                m = scale_note(patt[k % len(patt)], M["base"])
                place(buf, guqin(midi_hz(m), 2.2, 0.7 + 0.2 * r.random(), vib=False), t, 1.0, -0.2)
                t += beat / M["rate"] * 0.9
        else:
            for k in range(nphr):
                if t > t1 - 1: break
                deg = int(np.clip(deg + r.choice([-2, -1, -1, 1, 1, 2, 0]), 0, 9))
                m = scale_note(deg, M["base"])
                if r.random() < M["harm"]:
                    place(buf, harmonic(midi_hz(m + 12), 4.0, 0.9), t, 1.0, 0.25)
                else:
                    sl = r.choice([0, 0, 0, 2, -2]) if r.random() < 0.3 else 0
                    place(buf, guqin(midi_hz(m), 4.0, 0.8 + 0.2 * r.random(), slide=sl), t, 1.0, r.uniform(-0.3, 0.3))
                t += beat * r.choice([1, 1, 2, 0.5, 1.5]) / max(M["rate"], 0.3)
        t += beat * r.integers(2, 5)
    if M["bells"]:
        tb = t0 + 2.0
        while tb < t1 - 2:
            place(buf, qing(midi_hz(62), 8, 0.6), tb, 1.0, 0.1)
            tb += M["bells"]
    if M["xiao"]:
        tx = t0 + 2.0
        while tx < t1 - 6:
            notes, s = [], 0.0
            d0 = r.integers(3, 7)
            for k in range(r.integers(3, 6)):
                d0 = int(np.clip(d0 + r.choice([-1, 1, 2, -2]), 2, 9))
                L = r.choice([1.2, 1.8, 2.4])
                notes.append((s, L, scale_note(d0, 62)))
                s += L
            place(buf, xiao(notes, 1.0), tx, 1.0, -0.15)
            tx += s + r.uniform(5, 9)


def reverb(x, rt=2.8, wet=0.28):
    n = int(rt * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = np.random.default_rng(ch + 3).standard_normal(n) * np.exp(-6.9 * t / rt)
        ir = lp(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x * (1 - wet) + out * wet * 1.6


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    scenes = tl["scenes"]  # [{id,t0,t1}]
    buf = np.zeros((int((total + 4) * SR), 2))
    # 合并相同情绪的相邻场景
    segs = []
    for s in scenes:
        m = SCENE_MOOD[s["id"]]
        if segs and segs[-1][2] == m:
            segs[-1][1] = s["t1"]
        else:
            segs.append([s["t0"], s["t1"], m])
    for i, (a, b, m) in enumerate(segs):
        part = np.zeros_like(buf)
        section(a, b + 1.5, m, part, 100 + i)
        ia_, ib_ = int(max(a, 0) * SR), int(min(b, total) * SR)
        if ib_ - ia_ > 3 * SR:
            import pyloudnorm as pyln
            lu = pyln.Meter(SR).integrated_loudness(part[ia_:ib_])
            part *= 10 ** ((SEC_LU.get(m, -22.0) - lu) / 20)
        # 段落边缘 2 秒交叉淡化
        e = np.ones(len(buf))
        ia, ib = int(max(a - 1.5, 0) * SR), int(min(b + 1.5, total + 4) * SR)
        e[:ia] = 0; e[ib:] = 0
        ra = int(2.0 * SR)
        if a > 0:
            e[ia:ia + ra] = np.linspace(0, 1, ra)[: len(e[ia:ia + ra])]
        e[max(ib - ra, 0):ib] *= np.linspace(1, 0, ib - max(ib - ra, 0))
        buf += part * e[:, None]
    # 收尾：最后一句后磬声一记，余音 2.5 秒
    place(buf, qing(midi_hz(57), 6, 0.8), tl["last_end"] + 0.4, 1.0)
    buf = reverb(buf)
    buf = buf[: int(total * SR)]
    fo = int(2.5 * SR)
    buf[-fo:] *= np.linspace(1, 0, fo)[:, None]
    buf /= np.abs(buf).max() + 1e-9
    sf.write(f"{WORK}/music.wav", (buf * 0.8).astype(np.float32), SR)
    # 开场磬（声音钩子）
    b = np.zeros((int(8 * SR), 2))
    place(b, qing(midi_hz(62), 8, 1.0), 0.0, 1.0)
    place(b, qing(midi_hz(69) * 1.003, 6, 0.35), 0.0, 1.0, 0.3)
    b = reverb(b, 3.0, 0.3)
    b /= np.abs(b).max()
    sf.write(f"{WORK}/bell.wav", (b * 0.8).astype(np.float32), SR)
    print("music", buf.shape[0] / SR)


if __name__ == "__main__":
    main()
