# -*- coding: utf-8 -*-
"""响度测量（ITU-R BS.1770 K 加权 + 门限），用于片段归一与混音核对。输入 48 kHz。"""
import numpy as np
from scipy.signal import lfilter

_B1, _A1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
_B2, _A2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]


def kweight(x):
    return lfilter(_B2, _A2, lfilter(_B1, _A1, x, axis=0), axis=0)


def blocks(x, sr=48000, win=0.4, hop=0.1):
    """每个 400 ms 块（重叠 75%）的 K 加权均方，按声道求和。返回 (块起点秒, 均方)。"""
    y = kweight(x if x.ndim == 2 else x[:, None]); n, h = int(win * sr), int(hop * sr)
    c = np.cumsum(np.concatenate([np.zeros((1, y.shape[1])), y ** 2]), 0)
    st = np.arange(0, max(1, len(y) - n + 1), h)
    ms = ((c[st + n] - c[st]) / n).sum(1)
    return st / sr, ms


def lufs(x, sr=48000):
    """积分响度（绝对门限 -70 LUFS + 相对门限 -10 LU）。"""
    _, ms = blocks(x, sr); L = -0.691 + 10 * np.log10(ms + 1e-12)
    g = ms[L > -70]
    if len(g) == 0: return -99.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = ms[(L > -70) & (L > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def short_term(x, sr=48000, win=3.0, hop=0.1):
    t, ms = blocks(x, sr, win, hop); return t + win / 2, -0.691 + 10 * np.log10(ms + 1e-12)
