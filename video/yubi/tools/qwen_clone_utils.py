# -*- coding: utf-8 -*-
"""逐句音频处理的公用函数：音高测量、50 Hz 高通、压长停顿、去首尾静音。"""
import numpy as np, parselmouth


def f0(w, sr):
    s = parselmouth.Sound(w.astype(np.float64), sr)
    f = s.to_pitch_ac(time_step=0.01, pitch_floor=55, pitch_ceiling=350).selected_array['frequency']; f = f[f > 0]
    if len(f) < 10: return 999.0, 999.0
    return round(float(np.median(f)), 1), round(float(np.percentile(f, 90)), 1)


def hp50(w, sr):
    X = np.fft.rfft(w); fr = np.fft.rfftfreq(len(w), 1 / sr); g = 1 / np.sqrt(1 + (50 / np.maximum(fr, 1e-3)) ** 8)
    return np.fft.irfft(X * g, len(w)).astype(np.float32)


def squeeze_pauses(w, sr, maxp=0.4, th_rel=0.04):
    win = int(sr * 0.02); n = len(w) // win
    if n < 5: return w
    e = np.sqrt((w[:n * win].reshape(n, win) ** 2).mean(1)); q = e < max(0.006, e.max() * th_rel)
    keep = np.ones(len(w), bool); i = 0
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]: j += 1
            dur = (j - i) * 0.02
            if dur > maxp and i > 0 and j < n:
                cut = dur - maxp; a = int((i * 0.02 + maxp / 2) * sr); b = a + int(cut * sr); keep[a:b] = False
            i = j
        else: i += 1
    return w[keep]


def trim(w, sr, th=0.006, pad=0.06):
    win = int(sr * 0.01); env = np.convolve(np.abs(w), np.ones(win) / win, 'same'); idx = np.where(env > th)[0]
    if len(idx) == 0: return w
    a = w[max(0, idx[0] - int(pad * sr)): min(len(w), idx[-1] + int(pad * 2.2 * sr))].copy()
    k = min(len(a) // 4, int(0.01 * sr)); a[:k] *= np.linspace(0, 1, k); k2 = min(len(a) // 4, int(0.03 * sr)); a[-k2:] *= np.linspace(1, 0, k2)
    return a
