"""原创配乐（程序生成，无第三方版权）：科幻感合成器铺底 + 空间混响。
分层：pad（失谐锯齿波低通）、sub 低音、钟琴琶音（部分段落）、高频 shimmer；按章节强度自动起落。
usage: python music.py <duration_s> <out.wav> [timeline.json]"""
import sys, json, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, oaconvolve

SR = 48000
rng = np.random.default_rng(50)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

# band-limited saw wavetable
TBL_N = 4096
_ph = np.arange(TBL_N) / TBL_N
SAW = sum(((-1) ** (k + 1)) * np.sin(2 * np.pi * k * _ph) / k for k in range(1, 48)).astype(np.float32) * 0.6
SINE = np.sin(2 * np.pi * _ph).astype(np.float32)

def osc(tbl, f, n, ph0=0.0):
    ph = (ph0 + np.cumsum(np.full(n, f / SR))) % 1.0
    return tbl[(ph * TBL_N).astype(np.int32)]

# progression (D dorian-ish, cinematic): each chord 8 s
CHORDS = [
    [50, 57, 60, 64, 69],   # Dm9 (D A C E A)
    [46, 53, 57, 62, 65],   # Bbmaj7 (Bb F A D F)
    [41, 48, 55, 60, 64],   # Fmaj7/add9 (F C G C E)
    [48, 55, 59, 62, 67],   # C(add9) / G
    [50, 57, 62, 65, 69],   # Dm
    [43, 50, 57, 59, 62],   # Gm6/9-ish
    [46, 53, 58, 62, 65],   # Bb
    [45, 52, 57, 61, 64],   # A (sus-ish, tension)
]
CH_LEN = 8.0

def pad_layer(dur, warm_curve):
    n = int(dur * SR)
    out = np.zeros((n, 2), np.float32)
    seg = int(CH_LEN * SR); xf = int(2.5 * SR)
    i = 0; k = 0
    while i < n:
        ch = CHORDS[k % len(CHORDS)]
        L = min(seg + xf, n - i)
        env = np.ones(L, np.float32)
        a = min(xf, L)
        env[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        if L > seg:
            env[seg:] = np.cos(np.linspace(0, np.pi / 2, L - seg)) ** 2
        s = np.zeros((L, 2), np.float32)
        for vi, note in enumerate(ch[1:]):
            for det, pan in ((-0.09, 0.2), (0.0, 0.5), (0.11, 0.8)):
                f = midi(note) * 2 ** (det / 12)
                w = osc(SAW, f, L, rng.random())
                s[:, 0] += w * (1 - pan); s[:, 1] += w * pan
        out[i:i + L] += s * env[:, None] * 0.07
        i += seg; k += 1
    # slow-moving low-pass: brightness follows warm_curve (0..1)
    lo = sosfilt(butter(2, 700, "low", fs=SR, output="sos"), out, axis=0)
    hi = sosfilt(butter(2, 2200, "low", fs=SR, output="sos"), out, axis=0)
    wc = warm_curve[:, None]
    return (lo * (1 - wc) + hi * wc).astype(np.float32)

def sub_layer(dur):
    n = int(dur * SR); out = np.zeros(n, np.float32)
    seg = int(CH_LEN * SR); i = 0; k = 0
    while i < n:
        root = CHORDS[k % len(CHORDS)][0] - 12
        L = min(seg, n - i)
        env = np.minimum(1, np.minimum(np.arange(L) / (0.8 * SR), (L - np.arange(L)) / (0.8 * SR)))
        out[i:i + L] += osc(SINE, midi(root), L) * env * 0.16
        i += seg; k += 1
    return np.stack([out, out], 1)

def arp_layer(dur, mask):
    """bell-like plucks, 16ths at 96 bpm, through ping-pong delay"""
    n = int(dur * SR); out = np.zeros((n, 2), np.float32)
    step = 60 / 96 / 4
    t = 0.0; j = 0
    L = int(1.2 * SR); tt = np.arange(L) / SR
    while t < dur - 1.3:
        k = int(t // CH_LEN)
        ch = CHORDS[k % len(CHORDS)]
        pat = [ch[2] + 12, ch[3] + 12, ch[4] + 12, ch[3] + 12, ch[1] + 24, ch[4] + 12, ch[2] + 12, ch[3] + 24]
        m = mask[min(len(mask) - 1, int(t * SR))]
        if m > 0.02 and (j % 8 != 5):
            f = midi(pat[j % 8])
            v = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2.01 * f * tt) * np.exp(-tt * 9)) * np.exp(-tt * 5.5)
            v *= 0.05 * m * (0.8 + 0.2 * rng.random())
            i = int(t * SR); pan = 0.5 + 0.3 * math.sin(j * 0.7)
            out[i:i + L, 0] += v * (1 - pan); out[i:i + L, 1] += v * pan
        t += step; j += 1
    # ping-pong delay (3/16)
    d = int(step * 3 * SR)
    y = out.copy()
    for r in range(1, 5):
        g = 0.45 ** r
        sh = d * r
        if r % 2:
            y[sh:, 0] += out[:-sh, 1] * g; y[sh:, 1] += out[:-sh, 0] * g
        else:
            y[sh:, 0] += out[:-sh, 0] * g; y[sh:, 1] += out[:-sh, 1] * g
    return sosfilt(butter(2, 5000, "low", fs=SR, output="sos"), y, axis=0).astype(np.float32)

def shimmer_layer(dur, mask):
    n = int(dur * SR)
    nz = rng.normal(0, 1, (n, 2)).astype(np.float32)
    nz = sosfilt(butter(2, [5500, 9000], "band", fs=SR, output="sos"), nz, axis=0)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(n) / SR / 11.0)
    return (nz * (0.012 * lfo * mask)[:, None]).astype(np.float32)

def reverb(x, secs=4.0, wet=0.45):
    L = int(secs * SR)
    t = np.arange(L) / SR
    ir = np.stack([rng.normal(0, 1, L), rng.normal(0, 1, L)], 1) * np.exp(-t * 6.9 / secs)[:, None]
    ir = sosfilt(butter(1, 4500, "low", fs=SR, output="sos"), ir, axis=0)
    ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(0))
    y = np.stack([oaconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    return (x * (1 - wet) + y * wet * 1.6).astype(np.float32)

def curve_from_points(dur, pts):
    """pts: [(t, value)] piecewise-linear"""
    n = int(dur * SR); tt = np.arange(n) / SR
    xs, ys = zip(*pts)
    return np.interp(tt, xs, ys).astype(np.float32)

def build(dur, sec_times):
    """sec_times: dict section-letter -> start time"""
    S = sec_times
    def T(k, off=0.0): return S.get(k, dur) + off
    # intensity / brightness / arp / shimmer automation by section
    inten = curve_from_points(dur, [(0, 1.0), (T("b", -2), 0.85), (T("b", 2), 0.7), (T("c"), 0.8), (T("d"), 0.7), (T("e"), 0.6),
                                    (T("e", 30), 0.5), (T("f"), 0.8), (T("g"), 0.9), (T("h"), 1.0), (T("h", 40), 0.9),
                                    (T("h", 55), 0.55), (dur - 5, 0.5), (dur, 0.0)])
    warm = curve_from_points(dur, [(0, 0.9), (T("b"), 0.4), (T("c"), 0.6), (T("d"), 0.4), (T("e"), 0.2), (T("f"), 0.6), (T("g"), 0.8),
                                   (T("h"), 0.9), (T("h", 50), 0.3), (dur, 0.2)])
    arpm = curve_from_points(dur, [(0, 1.0), (T("b", -3), 1.0), (T("b", 1), 0.0), (T("c"), 0.0), (T("c", 3), 0.5), (T("d", -2), 0.5),
                                   (T("d", 1), 0.0), (T("f", -1), 0.0), (T("f", 3), 0.8), (T("g"), 0.9), (T("h", 30), 0.9),
                                   (T("h", 45), 0.0), (dur, 0.0)])
    shim = curve_from_points(dur, [(0, 1.0), (T("b"), 0.4), (T("e"), 0.2), (T("g"), 0.8), (T("h", 50), 1.0), (dur, 0.6)])
    x = pad_layer(dur, warm) + sub_layer(dur) + arp_layer(dur, arpm) + shimmer_layer(dur, shim)
    x = reverb(x, 4.5, 0.5)
    x *= inten[:, None]
    # fade in very fast (no slow intro), fade out at end
    f = int(0.05 * SR); x[:f] *= np.linspace(0, 1, f)[:, None]
    return x

if __name__ == "__main__":
    dur = float(sys.argv[1]); out = sys.argv[2]
    secs = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    x = build(dur, secs)
    x /= np.abs(x).max() + 1e-9
    sf.write(out, (x * 0.7).astype(np.float32), SR, subtype="FLOAT")
    print("music", out, dur)
