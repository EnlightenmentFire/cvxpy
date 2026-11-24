"""Deterministic synthetic series for the 示意 (illustrative) charts.

Nothing here is real market or trader data; every chart that uses it is
labelled 示意 on screen.
"""
import numpy as np


def _rolling_max(x, n):
    out = np.full_like(x, np.nan)
    for i in range(n, len(x)):
        out[i] = x[i - n:i].max()
    return out


def _rolling_min(x, n):
    out = np.full_like(x, np.nan)
    for i in range(n, len(x)):
        out[i] = x[i - n:i].min()
    return out


def donchian(seed=3, n=130, brk=78):
    """Range-bound market that breaks out upward around day `brk`."""
    rng = np.random.default_rng(seed)
    p = [100.0]
    for i in range(1, n):
        if i < brk:
            drift = (100 - p[-1]) * 0.08
            p.append(p[-1] + drift + rng.normal(0, 1.25))
        else:
            p.append(p[-1] + 0.85 + rng.normal(0, 1.15))
    close = np.array(p)
    hi = close + np.abs(rng.normal(0.9, 0.35, n))
    lo = close - np.abs(rng.normal(0.9, 0.35, n))
    up = _rolling_max(hi, 20)
    dn = _rolling_min(lo, 20)
    entry = next(i for i in range(60, n) if close[i] > up[i])
    return dict(close=close, hi=hi, lo=lo, up=up, dn=dn, entry=entry)


def ranges(seed=5, n=20):
    """Daily high-low bars for the N (average true range) demo."""
    rng = np.random.default_rng(seed)
    mid = 100 + np.cumsum(rng.normal(0, 0.8, n))
    half = np.abs(rng.normal(1.6, 0.6, n)) + 0.4
    gap_day = 13
    mid[gap_day:] += 2.4  # an overnight gap
    return dict(hi=mid + half, lo=mid - half, gap_day=gap_day)


def trend_then_reverse(seed=11, n=120):
    """Breakout, strong trend, then a reversal; for adds / stops / exits."""
    rng = np.random.default_rng(seed)
    p = [100.0]
    for i in range(1, n):
        if i < 20:
            d = rng.normal(0, 0.8) + (100 - p[-1]) * 0.1
        elif i < 82:
            d = 0.62 + rng.normal(0, 1.0)
        else:
            d = -0.85 + rng.normal(0, 1.1)
        p.append(p[-1] + d)
    close = np.array(p)
    lo10 = _rolling_min(close, 10)
    return dict(close=close, lo10=lo10)


def streak_equity(n_loss=9, seed=2):
    """Equity per trade: a run of small 1-2% losses, then one big trend win."""
    rng = np.random.default_rng(seed)
    eq = [100.0]
    path = [100.0]            # intra-trade path for drawing
    marks = []                # index into path where each trade closes
    for k in range(n_loss):
        start = eq[-1]
        up = start * (1 + rng.uniform(0.003, 0.012))
        end = start * (1 - rng.uniform(0.012, 0.02))
        path += list(np.linspace(start, up, 4)[1:]) + list(np.linspace(up, end, 5)[1:])
        eq.append(end)
        marks.append(len(path) - 1)
    start = eq[-1]
    big = list(start * (1 + 0.42 * (1 - np.exp(-np.linspace(0, 3.2, 26)))) + rng.normal(0, 0.5, 26))
    path += big
    eq.append(big[-1])
    marks.append(len(path) - 1)
    return dict(path=np.array(path), marks=marks, n_loss=n_loss)


def giveback(seed=4, n=90):
    """Open profit that rises, then is partly given back before the exit signal."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    peak = 58
    prof = np.where(t <= peak, 40 * (t / peak) ** 1.2, 40 - 20 * (np.clip(t - peak, 0, None) / (n - 1 - peak)) ** 0.9)
    prof = prof + rng.normal(0, 0.9, n) * (t > 3)
    prof[0] = 0
    return dict(profit=prof, peak=peak)


def diverge(n_people=13, n=220, seed=21):
    """Illustrative equity curves that start together and fan out."""
    rng = np.random.default_rng(seed)
    curves = []
    drifts = np.linspace(0.0105, -0.0022, n_people)
    rng.shuffle(drifts[1:])
    for k in range(n_people):
        x = [1.0]
        vol = 0.018 + 0.006 * rng.random()
        for i in range(1, n):
            x.append(x[-1] * (1 + drifts[k] + rng.normal(0, vol)))
        curves.append(np.array(x))
    order = np.argsort([c[-1] for c in curves])[::-1]
    curves = [curves[i] for i in order]
    # two curves end early: dropped from the programme (illustrative)
    cut = {len(curves) - 1: 70, len(curves) - 3: 118}
    return dict(curves=curves, cut=cut)


def drawdown_curve(seed=8, n=160):
    """Rise, then a long drawdown that could be either 'normal' or 'broken'."""
    rng = np.random.default_rng(seed)
    x = [1.0]
    for i in range(1, n):
        d = 0.006 if i < 70 else -0.0035
        x.append(x[-1] * (1 + d + rng.normal(0, 0.012)))
    return np.array(x)
