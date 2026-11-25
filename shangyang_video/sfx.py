"""音效全部用 numpy 合成，按时间线落点。开场声音钩子：关口夜风 + 更夫梆子 + 马蹄停下。
python sfx.py -> $WORK/sfx.wav
"""
import os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
from render import timeline

WK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
rng = np.random.default_rng(1)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def wind(dur, level=0.12):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    t = np.arange(n) / SR
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.13 * t + 1) * np.sin(2 * np.pi * 0.071 * t)
    y = bp(x, 180, 900) * mod + 0.4 * bp(x, 900, 2200) * mod ** 2
    y /= np.abs(y).max() + 1e-9
    return y * level


def clapper(level=0.5):
    """梆子：硬木空腔，短促高音 + 共鸣。"""
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 1180 * t) * 0.8 + np.sin(2 * np.pi * 1740 * t) * 0.4 + np.sin(2 * np.pi * 620 * t) * 0.5) * env(n, 0.001, 0.045)
    y += bp(rng.normal(0, 1, n), 1500, 5000) * env(n, 0.0005, 0.008) * 0.6
    return y / np.abs(y).max() * level


def hoof(level=0.35):
    n = int(0.18 * SR)
    y = lp(rng.normal(0, 1, n), 700) * env(n, 0.001, 0.025)
    t = np.arange(n) / SR
    y += np.sin(2 * np.pi * 140 * t) * env(n, 0.001, 0.03) * 0.8
    return y / np.abs(y).max() * level


def thud(level=0.6, f=55, d=0.5):
    n = int(d * 3 * SR)
    t = np.arange(n) / SR
    fr = f * (1 + 0.8 * np.exp(-t / 0.04))
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(n, 0.002, d)
    y += lp(rng.normal(0, 1, n), 400) * env(n, 0.001, 0.05) * 0.5
    return y / np.abs(y).max() * level


def wood(level=0.4):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 320 * t) + 0.6 * np.sin(2 * np.pi * 510 * t)) * env(n, 0.001, 0.05)
    y += bp(rng.normal(0, 1, n), 800, 3000) * env(n, 0.001, 0.01)
    return y / np.abs(y).max() * level


def coins(level=0.25):
    n = int(1.2 * SR)
    y = np.zeros(n)
    for k in range(9):
        s = int(rng.uniform(0, 0.6) * SR)
        m = int(0.4 * SR)
        t = np.arange(m) / SR
        f = rng.uniform(3000, 6000)
        c = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.48 * t)) * env(m, 0.0005, 0.08)
        y[s:s + m] += c[: n - s] * rng.uniform(0.4, 1)
    return y / np.abs(y).max() * level


def bell(level=0.5, f=110, d=4.0):
    """青铜钟：非谐分音。"""
    n = int(d * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for r, a, dd in [(1, 1, d), (2.0, 0.5, d * 0.6), (2.76, 0.35, d * 0.4), (5.4, 0.2, d * 0.2), (0.5, 0.4, d)]:
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / dd)
    y *= np.minimum(1, t / 0.003)
    return y / np.abs(y).max() * level


def whoosh(dur=1.2, level=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    e = np.sin(np.pi * t / dur) ** 2
    y = bp(x, 300, 3000) * e
    return y / np.abs(y).max() * level


def put(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m]


if __name__ == "__main__":
    lines, segs, total = timeline()
    L = {d["id"]: d for d in lines}
    S = {}
    for s in segs:
        S.setdefault(s["sc"], s)
    buf = np.zeros(int((total + 1) * SR))
    # ── 开场声音钩子（第 0 帧即有声） ──
    w = wind(L["a04"]["start"] + L["a04"]["dur"] + 2.0, 0.10)
    w[-SR:] *= np.linspace(1, 0, SR)
    put(buf, w, 0.0)
    put(buf, clapper(0.42), 0.0)
    put(buf, clapper(0.36), 0.42)
    for k in range(7):      # 马蹄由慢到停
        put(buf, hoof(0.22 * (1 - k / 9)), 1.0 + k * (0.28 + 0.05 * k))
    put(buf, wood(0.30), L["a02"]["start"] + 1.6)      # 店主敲墙上的木牍
    put(buf, thud(0.55, 48, 0.9), L["a05"]["start"])    # 死亡的重击
    put(buf, bell(0.30, 98, 5.0), L["a12"]["start"] + 1.4)
    # 廷辩：竹简对撞
    put(buf, thud(0.45, 70, 0.4), L["b13"]["start"] + 1.0 + (S["debate"]["start"] - S["debate"]["start"]))
    put(buf, wood(0.35), L["b13"]["start"] + 1.0)
    put(buf, thud(0.5, 60, 0.5), L["b19"]["start"] + 0.6)        # 变法之令盖印
    put(buf, coins(0.22), L["c05"]["start"] + 1.0)               # 五十金
    put(buf, wood(0.35), L["c05"]["start"] + 2.2)                # 搬起木头
    put(buf, thud(0.45, 60, 0.5), L["c05"]["start"] + 6.0)       # 以明不欺 印
    put(buf, thud(0.5, 50, 0.6), L["c11"]["start"] + 1.2)        # 刑
    put(buf, thud(0.5, 50, 0.6), L["c11"]["start"] + 3.0)        # 黥
    put(buf, whoosh(1.6, 0.16), L["e18"]["start"] + 3.0)         # 迁边城
    for k in range(10):                                          # 灯火熄灭
        put(buf, whoosh(0.35, 0.05), L["e15"]["start"] + 1.0 + k * 0.9)
    put(buf, bell(0.28, 92, 5.0), L["f05"]["start"] + 0.2)
    # 车裂：马蹄四散 + 重击 + 静
    hs = L["f13"]["start"]
    for k in range(26):
        put(buf, hoof(0.32 * (1 - k / 30)), hs + 0.5 + k * 0.11)
    put(buf, whoosh(2.0, 0.22), hs + 0.6)
    put(buf, thud(0.65, 42, 1.4), hs + 3.4)
    put(buf, bell(0.32, 87, 6.0), L["g10"]["start"] - 0.1)       # 结尾钟声
    peak = np.abs(buf).max()
    if peak > 0.95:
        buf *= 0.95 / peak
    st = np.stack([buf, buf], 1)
    sf.write(f"{WK}/sfx.wav", st[: int(total * SR)], SR, subtype="PCM_24")
    print("sfx ok")
