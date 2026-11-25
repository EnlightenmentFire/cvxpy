"""音效（numpy 合成）：开场电子声音钩子、章节转场的气流声、关键结论处的低频脉冲。"""
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
rng = np.random.default_rng(7)

def env_exp(n, tau):
    return np.exp(-np.arange(n) / SR / tau)

def hook_sound():
    """t=0: 数字“上电”扫频 + 低频冲击 + 数据闪烁（约 3 秒，主体在 0.25 秒前完成，之后压在人声下）"""
    n = int(3.2 * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    # sub impact
    f = 55 * np.exp(-t * 3) + 32
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.9) * 0.9
    out += sub[:, None]
    # rising digital sweep 0..0.22 s
    m = int(0.24 * SR); tt = np.arange(m) / SR
    fs = 300 + 5200 * (tt / 0.24) ** 2
    sw = np.sign(np.sin(2 * np.pi * np.cumsum(fs) / SR)) * 0.18 * np.sin(np.pi * tt / 0.24)
    sw = sosfilt(butter(2, 6000, "low", fs=SR, output="sos"), sw)
    out[:m, 0] += sw; out[:m, 1] += sw
    # data blips (sparkles) across 0..2.5 s, decaying
    for k in range(26):
        t0 = rng.uniform(0.0, 2.4) ** 1.4
        i = int(t0 * SR); L = int(0.05 * SR)
        fr = rng.choice([1760, 2093, 2637, 3136, 3520])
        bl = np.sin(2 * np.pi * fr * np.arange(L) / SR) * env_exp(L, 0.012) * 0.10 * (1 - t0 / 3)
        pan = rng.random()
        if i + L < n:
            out[i:i + L, 0] += bl * (1 - pan); out[i:i + L, 1] += bl * pan
    # airy noise tail
    nz = sosfilt(butter(2, [800, 6000], "band", fs=SR, output="sos"), rng.normal(0, 1, (n, 2)), axis=0)
    out += nz * (env_exp(n, 0.7) * 0.05)[:, None]
    return out.astype(np.float32)

def whoosh(dur=1.6, gain=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.normal(0, 1, (n, 2))
    e = np.sin(np.pi * t / dur) ** 2
    lo = sosfilt(butter(2, [300, 1500], "band", fs=SR, output="sos"), nz, axis=0)
    hi = sosfilt(butter(2, [1500, 7000], "band", fs=SR, output="sos"), nz, axis=0)
    k = (t / dur)[:, None]
    return ((lo * (1 - k) + hi * k) * e[:, None] * gain).astype(np.float32)

def pulse(gain=0.35):
    n = int(1.8 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * (48 * t - 4 * t * t)) * env_exp(n, 0.5) * gain
    s += np.sin(2 * np.pi * 96 * t) * env_exp(n, 0.25) * gain * 0.3
    return np.stack([s, s], 1).astype(np.float32)

def place(track, clip, t):
    i = int(t * SR)
    if i >= len(track): return
    L = min(len(clip), len(track) - i)
    track[i:i + L] += clip[:L]
