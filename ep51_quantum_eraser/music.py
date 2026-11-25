"""原创底乐（全部用 numpy 合成，无任何采样或曲库素材 → 无版权问题）。

乐器：磬（非谐泛音、长衰减）、类古琴拨弦（加法合成，带上滑与吟）、箫（气声 + 颤音）、
      玻璃钟（物理部分的冷色高音）、低音持续音。调式：D 宫五声（D E F# A B）。
结构跟随 timeline.json：物理段偏冷、流动的玻璃钟琶音；佛法段古琴与箫；场景切换处一声磬。
开场第 0 秒即一声磬作声音钩子。
usage: python music.py   -> stems/music.wav（48 kHz 立体声，峰值归一 -6 dBFS）
"""
import os, json
import numpy as np, soundfile as sf
from scipy.signal import oaconvolve, butter, sosfilt

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
rng = np.random.default_rng(51)

D3 = 146.83
PENTA = [0, 2, 4, 7, 9]  # D E F# A B（半音）


def note(deg, octv=0):
    """五声音阶第 deg 级（可越过八度），相对 D3"""
    o, i = divmod(deg, 5)
    return D3 * 2 ** ((PENTA[i] + 12 * (o + octv)) / 12)


def env_ad(n, a, sr=SR):
    e = np.ones(n, np.float32)
    na = max(1, int(a * sr))
    e[:na] = np.linspace(0, 1, na) ** 1.5
    return e


def qing(f0=D3 * 2, amp=1.0, dur=9.0):
    """磬 / 钵：非谐泛音，带拍频"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    ratios = [1.0, 2.71, 4.95, 7.6, 10.7]
    decays = [5.5, 3.2, 1.8, 1.1, 0.6]
    gains = [1.0, 0.55, 0.32, 0.18, 0.1]
    y = np.zeros(n, np.float32)
    for r, dc, g in zip(ratios, decays, gains):
        f = f0 * r
        beat = 1 + 0.5 * np.cos(2 * np.pi * (0.7 + r * 0.13) * t)
        y += (g * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / dc) * beat).astype(np.float32)
    y *= env_ad(n, 0.004)
    return amp * y / np.abs(y).max()


def qin(f, amp=1.0, dur=5.0, slide=True, yin=True):
    """类古琴拨弦：谐波加法合成，高次谐波衰减快；起音轻微上滑，后段吟（慢颤）"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    fi = np.full(n, f, np.float64)
    if slide:
        fi *= 2 ** ((-0.6 * np.exp(-t / 0.06)) / 12)
    if yin:
        fi *= 2 ** ((0.18 * np.sin(2 * np.pi * 4.2 * t) * np.clip((t - 0.5) / 0.8, 0, 1)) / 12)
    ph = 2 * np.pi * np.cumsum(fi) / SR
    y = np.zeros(n, np.float64)
    for h in range(1, 11):
        inh = 1 + 0.0004 * h * h
        y += (1 / h ** 1.25) * np.sin(h * inh * ph) * np.exp(-t * (0.55 + 0.45 * h))
    pluck = rng.normal(0, 1, n) * np.exp(-t / 0.012)
    sos = butter(2, [f * 1.5, min(f * 12, 9000)], "bandpass", fs=SR, output="sos")
    y += 0.25 * sosfilt(sos, pluck)
    y *= env_ad(n, 0.003)
    return (amp * y / np.abs(y).max()).astype(np.float32)


def xiao(f, amp=1.0, dur=4.0):
    """箫：基音为主 + 弱二三次谐波 + 气声，缓起，颤音逐渐加深"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.4) / 1.0, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = rng.normal(0, 1, n)
    sos = butter(2, [f * 0.8, f * 3.5], "bandpass", fs=SR, output="sos")
    y = y + 0.35 * sosfilt(sos, breath) / 3
    e = np.ones(n)
    a, r = int(0.45 * SR), int(0.9 * SR)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[-r:] = np.linspace(1, 0, r) ** 1.5
    e *= 1 + 0.08 * np.sin(2 * np.pi * 0.35 * t)
    return (amp * y * e / 1.2).astype(np.float32)


def glass(f, amp=1.0, dur=3.0):
    """玻璃钟：近谐、柔和、中等衰减"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.01 * f * t) * np.exp(-t / 0.4) + 0.08 * np.sin(2 * np.pi * 3.98 * f * t) * np.exp(-t / 0.2)
    y = y * np.exp(-t / 1.3) * env_ad(n, 0.006)
    return (amp * y).astype(np.float32)


def place(buf, x, t0, pan=0.0):
    i = int(t0 * SR)
    if i >= buf.shape[1] or i < 0:
        return
    x = x[: buf.shape[1] - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(x)] += x * l * 1.414
    buf[1, i:i + len(x)] += x * r * 1.414


def drone(total, segs):
    """低音持续：D2+A2，按段落淡入淡出；segs=[(t0,t1,level)]"""
    n = int(total * SR)
    t = np.arange(n) / SR
    lvl = np.zeros(n, np.float32)
    for a, b, g in segs:
        i0, i1 = int(a * SR), min(n, int(b * SR))
        if i1 <= i0:
            continue
        seg = np.full(i1 - i0, g, np.float32)
        fl = min(int(4 * SR), (i1 - i0) // 2)
        seg[:fl] *= np.linspace(0, 1, fl)
        seg[-fl:] *= np.linspace(1, 0, fl)
        lvl[i0:i1] = np.maximum(lvl[i0:i1], seg)
    y = (np.sin(2 * np.pi * 73.42 * t) * 0.6 + np.sin(2 * np.pi * 110.0 * t + 1) * 0.35 + np.sin(2 * np.pi * 146.83 * t * 1.001) * 0.2)
    y *= 1 + 0.25 * np.sin(2 * np.pi * 0.05 * t)
    air = sosfilt(butter(2, [300, 1800], "bandpass", fs=SR, output="sos"), rng.normal(0, 1, n)) * 0.05
    y = (y + air) * lvl
    return np.stack([y, np.roll(y, int(0.013 * SR))]).astype(np.float32)


def reverb_ir(rt=3.6):
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n), np.float32)
    for c in range(2):
        noise = rng.normal(0, 1, n) * np.exp(-6.9 * t / rt)
        noise = sosfilt(butter(1, 5200, "lowpass", fs=SR, output="sos"), noise)
        ir[c] = noise
        for k in range(6):  # 早期反射
            ir[c, int(rng.uniform(0.008, 0.06) * SR)] += rng.uniform(0.3, 0.7)
    return ir / np.abs(ir).max() * 0.08


def compose(tl):
    total = tl["total"]
    sc = {s["id"]: s for s in tl["scenes"]}
    lines = tl["lines"]
    dry = np.zeros((2, int(total * SR) + 12 * SR), np.float32)
    phys_end = sc["sum"]["end"]
    budd_start = sc["penit"]["start"]

    # 声音钩子：第 0 秒一声磬（D4），加一声低八度的余音
    place(dry, qing(note(5), 1.0, 10), 0.0, -0.1)
    place(dry, qing(note(0), 0.45, 10), 0.02, 0.15)

    # 场景切换处的磬
    for sid, f, a in [("slit", note(5), 0.55), ("kim", note(7), 0.5), ("facts", note(5), 0.5), ("sum", note(3), 0.6),
                      ("penit", note(0), 0.7), ("moon", note(5), 0.55), ("close", note(3), 0.55)]:
        place(dry, qing(f, a, 10), max(0, sc[sid]["start"] - 0.45), rng.uniform(-0.3, 0.3))
    brush = [e for e in lines if e["cue"] == "brush"][0]
    place(dry, qing(note(0), 0.85, 12), brush["start"] + 1.2, 0)
    place(dry, qing(note(5), 0.5, 12), brush["end"] + 1.6, 0.2)

    # 物理段：玻璃钟琶音（流动，两小节一组，和声在 D-A-B-E 之间转）
    pats = [[5, 7, 9, 12], [4, 7, 8, 11], [3, 5, 8, 10], [5, 6, 9, 13]]
    t, k = 1.5, 0
    while t < phys_end + 4:
        dens = 0.55 if t < sc["slit"]["start"] else 1.0
        pat = pats[k % len(pats)]
        step = 0.42 if k % 3 else 0.55
        order = pat if k % 2 == 0 else pat[::-1]
        for j, deg in enumerate(order):
            if rng.random() < 0.9 * dens:
                place(dry, glass(note(deg, 1), 0.16 * rng.uniform(0.7, 1.0), 3.2), t + j * step + rng.uniform(0, 0.03), rng.uniform(-0.6, 0.6))
        if k % 2 == 0:  # 低音琴弦托底
            place(dry, qin(note([0, 3, 4, 1][(k // 2) % 4], -1), 0.22, 6, yin=False), t, -0.2)
        t += 4 * step + rng.uniform(2.2, 3.6)
        k += 1

    # 过渡（星空）：上行闪烁
    ts = [e for e in lines if e["cue"] == "to_stars"][0]
    for j in range(14):
        place(dry, glass(note(5 + j % 9, 1), 0.1, 2.5), ts["start"] + j * 0.28, rng.uniform(-0.8, 0.8))

    # 佛法段：古琴乐句 + 箫
    phrases = [[0, 2, 3, 2], [3, 4, 5, 3, 2], [5, 4, 3, 2, 0], [2, 3, 5, 7, 5], [7, 5, 4, 3], [3, 2, 0, -2, 0]]
    t, k = budd_start + 1.0, 0
    while t < total - 6:
        ph = phrases[k % len(phrases)]
        tt = t
        for j, deg in enumerate(ph):
            dur = rng.choice([0.55, 0.7, 0.9, 1.2]) if j < len(ph) - 1 else 1.6
            place(dry, qin(note(deg + 5), 0.42 * rng.uniform(0.8, 1.0), 5.5), tt, rng.uniform(-0.3, 0.3))
            if j == 0:
                place(dry, qin(note(deg), 0.2, 6, yin=False), tt + 0.02, -0.25)
            tt += dur
        t = tt + rng.uniform(3.0, 5.5)
        k += 1
    # 箫：段落内长音
    xs = budd_start + 14
    while xs < total - 8:
        deg = rng.choice([5, 7, 8, 9, 10])
        d = rng.uniform(3.5, 5.5)
        place(dry, xiao(note(deg), 0.2, d), xs, 0.25)
        if rng.random() < 0.6:
            place(dry, xiao(note(deg - 1), 0.17, d * 0.7), xs + d - 0.3, 0.25)
        xs += d + rng.uniform(7, 12)

    # 结尾：古琴泛音式的高音收束
    for j, deg in enumerate([10, 9, 7, 5]):
        place(dry, qin(note(deg), 0.28, 7), total - 5.5 + j * 0.9, 0.1)

    # 混响
    ir = reverb_ir()
    wet = np.stack([oaconvolve(dry[c], ir[c])[: dry.shape[1]] for c in range(2)]).astype(np.float32)
    mix = dry * 0.62 + wet * 1.0
    mix += np.pad(drone(total, [(0, phys_end + 2, 0.05), (budd_start - 2, total, 0.06)]), ((0, 0), (0, mix.shape[1] - int(total * SR))))
    mix = mix[:, : int(total * SR)]
    fo = int(4 * SR)
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    mix *= 10 ** (-6 / 20) / np.abs(mix).max()
    return mix


if __name__ == "__main__":
    tl = json.load(open(f"{WORK}/timeline.json"))
    m = compose(tl)
    os.makedirs(f"{WORK}/stems", exist_ok=True)
    sf.write(f"{WORK}/stems/music.wav", m.T, SR, subtype="PCM_24")
    print("music", m.shape[1] / SR, "s")
