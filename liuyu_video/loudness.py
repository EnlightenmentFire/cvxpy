# -*- coding: utf-8 -*-
"""EBU R128 瞬时响度（K 加权、400 ms 窗、100 ms 步进），混音和质检共用。"""
import numpy as np
from scipy.signal import lfilter

SR = 48000
HOP = 0.1      # 秒
WIN = 0.4      # 秒

# 48 kHz 下 K 加权的两级双二阶滤波（ITU-R BS.1770）
_B1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
_A1 = [1.0, -1.69065929318241, 0.73248077421585]
_B2 = [1.0, -2.0, 1.0]
_A2 = [1.0, -1.99004745483398, 0.99007225036621]


def momentary_lufs(x, sr=SR):
    """返回每 100 ms 一个值；第 i 个值覆盖 [i·0.1, i·0.1+0.4) 秒，中心在 i·0.1+0.2"""
    assert sr == SR, "K 加权系数按 48 kHz 写死"
    if x.ndim == 1:
        x = x[:, None]
    y = lfilter(_B2, _A2, lfilter(_B1, _A1, x.astype(np.float64), axis=0), axis=0)
    p = (y ** 2).sum(1)
    hop, win = int(HOP * sr), int(WIN * sr)
    c = np.concatenate([[0], np.cumsum(p)])
    idx = np.arange(0, max(1, len(p) - win), hop)
    return -0.691 + 10 * np.log10((c[idx + win] - c[idx]) / win + 1e-12)


def frame_centers(n):
    return np.arange(n) * HOP + WIN / 2


def line_loudness(mv, sel):
    """一句人声的整体响度：有声窗口的能量平均"""
    lv = mv[sel]
    lv = lv[lv > -50]
    return 10 * np.log10(np.mean(10 ** (lv / 10))) if len(lv) else -70.0
