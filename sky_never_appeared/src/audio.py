"""Self-synthesised score + sound design (no external samples).

Everything is generated with numpy/scipy at 48 kHz stereo.
"""
import math
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(1983)


def secs(n):
    return int(round(n * SR))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def nm(s):
    """'A2' -> midi number"""
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTE[name]


# ------------------------------------------------------------------ oscillators
def phase(freq, n, ph0=0.0):
    f = np.broadcast_to(np.asarray(freq, np.float64), (n,))
    return (ph0 + np.cumsum(f) / SR) % 1.0, f


def saw(freq, n, ph0=0.0):
    p, f = phase(freq, n, ph0)
    y = 2 * p - 1
    dt = f / SR
    # polyBLEP
    m1 = p < dt
    t = p[m1] / dt[m1]
    y[m1] -= t + t - t * t - 1
    m2 = p > 1 - dt
    t = (p[m2] - 1) / dt[m2]
    y[m2] -= t * t + t + t + 1
    return y


def square(freq, n, pw=0.5):
    return 0.5 * (saw(freq, n) - saw(freq, n, ph0=pw))


def sine(freq, n, ph0=0.0):
    p, _ = phase(freq, n, ph0)
    return np.sin(2 * np.pi * p)


def noise(n):
    return RNG.normal(0, 1, n)


def brown(n):
    x = np.cumsum(RNG.normal(0, 1, n))
    x = signal.sosfilt(signal.butter(1, 20, 'hp', fs=SR, output='sos'), x)
    return x / (np.abs(x).max() + 1e-9)


# ------------------------------------------------------------------ filters / fx
def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR / 2 - 100), 'lp', fs=SR, output='sos'), x, axis=0)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'hp', fs=SR, output='sos'), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'bp', fs=SR, output='sos'), x, axis=0)


def lp_sweep(x, fc_curve, block=512):
    """time-varying low-pass (block-wise, state-carrying one-pole cascade)."""
    y = np.zeros_like(x)
    z1 = 0.0; z2 = 0.0
    for i in range(0, len(x), block):
        fc = float(fc_curve[min(i, len(fc_curve) - 1)])
        a = math.exp(-2 * math.pi * fc / SR)
        seg = x[i:i + block]
        out = np.empty_like(seg)
        for j, s in enumerate(seg):
            z1 = (1 - a) * s + a * z1
            z2 = (1 - a) * z1 + a * z2
            out[j] = z2
        y[i:i + block] = out
    return y


def lp_sweep_fast(x, fc_start, fc_end, nseg=24):
    """piecewise-constant butterworth low-pass with crossfades (fast)."""
    n = len(x)
    out = np.zeros_like(x)
    edges = np.linspace(0, n, nseg + 1).astype(int)
    fade = 2048
    for k in range(nseg):
        a, b = max(0, edges[k] - fade), min(n, edges[k + 1] + fade)
        fc = fc_start * (fc_end / fc_start) ** ((k + 0.5) / nseg)
        seg = lp(x[a:b], fc)
        w = np.ones(b - a)
        if k > 0:
            w[:fade * 2] = np.linspace(0, 1, fade * 2)[:len(w[:fade * 2])]
        if k < nseg - 1:
            w[-fade * 2:] = np.linspace(1, 0, fade * 2)[-len(w[-fade * 2:]):]
        out[a:b] += seg * (w if x.ndim == 1 else w[:, None])
    return out


def env(n, a=0.005, d=0.1, s=0.7, r=0.2, hold=None):
    """ADSR over n samples; release at the end."""
    A, D, R = secs(a), secs(d), secs(r)
    e = np.full(n, s, np.float64)
    A = min(A, n); e[:A] = np.linspace(0, 1, A, endpoint=False)
    D2 = min(D, n - A)
    if D2 > 0:
        e[A:A + D2] = np.linspace(1, s, D2, endpoint=False)
    R = min(R, n)
    if R > 0:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def perc(n, a=0.002, decay=0.15):
    t = np.arange(n) / SR
    e = np.exp(-t / decay)
    A = secs(a)
    if A > 0:
        e[:A] *= np.linspace(0, 1, A)
    return e


_IR = {}
def reverb(x, seconds=2.2, mix=0.25, pre=0.02, bright=6000, seed=5):
    key = (seconds, bright, seed)
    if key not in _IR:
        r = np.random.default_rng(seed)
        n = secs(seconds)
        t = np.arange(n) / SR
        ir = r.normal(0, 1, (n, 2)) * np.exp(-t * 6.9 / seconds)[:, None]
        ir = lp(ir, bright)
        ir[:secs(pre)] = 0
        ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
        _IR[key] = ir
    ir = _IR[key]
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - mix) + wet * mix * 1.6


def delay(x, t, fb=0.35, mix=0.3, pingpong=True):
    d = secs(t)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = x.copy()
    tap = x.copy()
    for k in range(1, 6):
        tap = np.roll(tap, d, axis=0) * fb
        tap[:d] = 0
        if pingpong:
            tap = tap[:, ::-1]
        y += tap * mix / fb
    return y


def pan(x, p):
    """p in [-1, 1]."""
    l = math.cos((p + 1) * math.pi / 4)
    r = math.sin((p + 1) * math.pi / 4)
    return np.stack([x * l, x * r], 1)


def stereo(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


def place(buf, x, t0, gain=1.0):
    """add x (mono or stereo) into stereo buffer at time t0."""
    x = stereo(x) * gain
    i = secs(t0)
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n]


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


# ------------------------------------------------------------------ instruments
def kick(n_s=0.45):
    n = secs(n_s)
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t / 0.04)
    x = sine(f, n) * np.exp(-t / 0.18)
    x += lp(noise(n), 2000) * np.exp(-t / 0.006) * 0.3
    return np.tanh(x * 1.6) * 0.9


def clap(n_s=0.5):
    n = secs(n_s)
    t = np.arange(n) / SR
    e = np.zeros(n)
    for k, dt in enumerate((0, 0.011, 0.022)):
        i = secs(dt)
        e[i:] += np.exp(-(t[:n - i]) / (0.012 if k < 2 else 0.16))
    x = bp(noise(n), 900, 5000) * e
    return reverb(x, 1.2, 0.35)


def hat(n_s=0.08, open_=False):
    n = secs(0.3 if open_ else n_s)
    t = np.arange(n) / SR
    return hp(noise(n), 7000) * np.exp(-t / (0.08 if open_ else 0.018)) * 0.35


def pluck_saw(freq, dur, cutoff=3000, decay=0.25):
    n = secs(dur)
    x = saw(freq, n) * 0.6 + square(freq * 1.003, n) * 0.4
    x = lp(x, cutoff)
    return x * perc(n, 0.002, decay)


def pad(notes, dur, detune=0.08, cutoff=1800, attack=1.5, release=1.5, vib=0.0):
    n = secs(dur)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for k, m in enumerate(notes):
        f0 = midi(m)
        for j, dt in enumerate((-detune, 0.0, detune)):
            f = f0 * 2 ** (dt / 12) * (1 + vib * 0.004 * np.sin(2 * np.pi * 5.2 * t + j))
            x = saw(f, n, ph0=RNG.uniform())
            out += pan(x, (j - 1) * 0.6)
    out = lp(out, cutoff)
    out *= env(n, attack, 0.5, 1.0, release)[:, None]
    return out / (len(notes) * 3)


# ------------------------------------------------------------------ synthwave theme
CHORDS = [('A', [57, 60, 64]), ('F', [53, 57, 60]), ('C', [48, 52, 55]), ('G', [55, 59, 62])]
BASS = {'A': nm('A1'), 'F': nm('F1'), 'C': nm('C2'), 'G': nm('G1')}


def synth_theme(dur, bpm=104, intensity=1.0, drums=True, arp=True, dark=0.0, octave_shift=0, seed=0):
    """80s-style theme: pulse bass, bright arpeggio, pad, gated drums.
    dark 0..1 darkens (lower cutoffs, sparser)."""
    n = secs(dur)
    out = np.zeros((n, 2))
    beat = 60.0 / bpm
    bar = beat * 4
    nbars = int(math.ceil(dur / bar)) + 1
    cut_main = 5200 * (1 - 0.75 * dark)
    for b in range(nbars):
        name, ch = CHORDS[b % 4]
        t0 = b * bar
        if t0 >= dur:
            break
        # pad
        p = pad([m + 12 * octave_shift for m in ch], bar + 1.2, cutoff=2400 * (1 - 0.6 * dark), attack=0.4, release=1.0)
        place(out, p * 0.55, t0)
        # bass 8ths with sidechain feel
        for k in range(8):
            f = midi(BASS[name] + 12 * octave_shift + (12 if k % 2 else 0) * (1 - dark))
            x = pluck_saw(f, beat / 2 * 0.95, cutoff=900 * (1 - 0.5 * dark) + 300, decay=0.16)
            place(out, x * 0.42, t0 + k * beat / 2)
        # arp 16ths
        if arp:
            seq = ch + [m + 12 for m in ch] + [ch[1] + 12, ch[2]]
            for k in range(16):
                m = seq[(k + seed) % len(seq)] + 12 + 12 * octave_shift
                x = pluck_saw(midi(m), beat / 4 * 0.9, cutoff=cut_main, decay=0.09)
                place(out, pan(x, 0.35 if k % 2 else -0.35) * 0.16 * intensity, t0 + k * beat / 4)
        if drums:
            for k in range(4):
                place(out, kick() * 0.55 * intensity, t0 + k * beat)
                if k in (1, 3):
                    place(out, clap() * 0.35 * intensity, t0 + k * beat)
            for k in range(8):
                place(out, pan(hat(), 0.2) * 0.5 * intensity, t0 + k * beat / 2 + beat / 4)
    out = out[:n]
    # sidechain pump
    if drums:
        t = np.arange(n) / SR
        ph = (t % beat) / beat
        pump = 0.55 + 0.45 * np.clip(ph / 0.35, 0, 1)
        out *= pump[:, None]
    out = delay(out, beat * 0.75, fb=0.3, mix=0.18)[:n]
    out = reverb(out, 2.4, 0.22)
    return out


def lead_line(dur, bpm=104, notes=None):
    """simple heroic lead (square + vibrato), for the cold-open climax."""
    beat = 60.0 / bpm
    notes = notes or [('E5', 2), ('D5', 1), ('C5', 1), ('D5', 2), ('G4', 2), ('A4', 3), ('C5', 1), ('B4', 4)]
    n = secs(dur)
    out = np.zeros((n, 2))
    t = 0.0
    for name, beats in notes:
        L = beats * beat
        m = secs(L)
        tt = np.arange(m) / SR
        f = midi(nm(name)) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt / 0.3, 0, 1))
        x = (square(f, m, 0.3) * 0.6 + saw(f * 1.004, m) * 0.4)
        x = lp(x, 3800) * env(m, 0.01, 0.2, 0.8, 0.12)
        place(out, x * 0.22, t)
        t += L
        if t >= dur:
            break
    return reverb(delay(out, beat * 0.75, 0.35, 0.25), 2.6, 0.3)


# ------------------------------------------------------------------ reality textures
def drone(dur, root='E1', cold=1.0):
    n = secs(dur)
    t = np.arange(n) / SR
    f = midi(nm(root))
    x = sine(f, n) * 0.5 + sine(f * 1.5 * (1 + 0.0015 * np.sin(2 * np.pi * 0.07 * t)), n) * 0.18
    x += sine(f * 2.003, n) * 0.12
    nb = lp(brown(n), 300) * 0.25 + bp(noise(n), 2500, 6000) * 0.012 * cold
    y = (x + nb) * env(n, 2.0, 0.1, 1.0, 2.0)
    return reverb(y * 0.6, 3.0, 0.3)


def ping(freq=1760, dur=1.5):
    n = secs(dur)
    t = np.arange(n) / SR
    x = (sine(freq, n) + 0.3 * sine(freq * 2.76, n)) * np.exp(-t / 0.4)
    return reverb(x * 0.25, 2.5, 0.4)


def typewriter_key(seed=0):
    r = np.random.default_rng(seed)
    n = secs(0.09)
    t = np.arange(n) / SR
    x = bp(noise(n), 1800 + r.uniform(-300, 600), 5200) * np.exp(-t / 0.012)
    x += sine(160 + r.uniform(-20, 20), n) * np.exp(-t / 0.02) * 0.5
    return x * 0.6


def typewriter(times):
    """list of key times -> mono track"""
    if not times:
        return np.zeros(1)
    n = secs(max(times) + 0.3)
    out = np.zeros(n)
    for k, tt in enumerate(times):
        x = typewriter_key(k)
        i = secs(tt)
        out[i:i + len(x)] += x[:len(out) - i]
    return out


def clock(dur, rate=1.0, level=0.5):
    n = secs(dur)
    out = np.zeros(n)
    k = 0
    tt = 0.0
    while tt < dur:
        m = secs(0.03)
        e = np.exp(-np.arange(m) / SR / 0.004)
        x = bp(noise(m), 2500 if k % 2 == 0 else 1900, 7000) * e
        i = secs(tt)
        out[i:i + m] += x[:max(0, min(m, n - i))]
        k += 1
        tt += rate
    return reverb(out * level, 1.4, 0.25)


def strings(notes, dur, level=0.3):
    return pad(notes, dur, detune=0.12, cutoff=1500, attack=2.5, release=2.5, vib=1.0) * level


def descending_tone(dur=7.0, f0=330.0, f1=38.0):
    n = secs(dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    x = sine(f, n) * 0.6 + saw(f, n) * 0.15
    x = lp(x, 1800) * env(n, 0.4, 0.1, 1.0, 1.5)
    x = np.tanh(x * (1 + 2 * t / dur))
    return reverb(x * 0.5, 3.0, 0.35)


# ------------------------------------------------------------------ sfx
def zap(dur=0.35, f0=2400, f1=320):
    n = secs(dur)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    x = (sine(f, n) * 0.6 + saw(f * 0.5, n) * 0.2) * np.exp(-t / 0.12)
    x += hp(noise(n), 3000) * np.exp(-t / 0.03) * 0.3
    return reverb(x * 0.5, 1.5, 0.3)


def boom(dur=2.5, big=1.0):
    n = secs(dur)
    t = np.arange(n) / SR
    x = sine(38 + 30 * np.exp(-t / 0.15), n) * np.exp(-t / (0.5 * big)) * 0.9
    x += lp(noise(n), 700 * big) * np.exp(-t / (0.35 * big)) * 0.6
    x += hp(noise(n), 3000) * np.exp(-t / 0.04) * 0.3
    return reverb(np.tanh(x * 1.5) * 0.7, 2.8, 0.3)


def whoosh(dur=1.2, up=True):
    n = secs(dur)
    t = np.arange(n) / SR
    x = noise(n)
    x = lp_sweep_fast(x, 300 if up else 6000, 6000 if up else 300, 16)
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return reverb(x * e * 0.35, 1.8, 0.3)


def impact(dur=3.0):
    n = secs(dur)
    t = np.arange(n) / SR
    x = sine(55 * np.exp(-t / 1.5) + 28, n) * np.exp(-t / 0.9)
    x += lp(noise(n), 1500) * np.exp(-t / 0.25) * 0.5
    x += hp(noise(n), 5000) * np.exp(-t / 0.08) * 0.25
    return reverb(np.tanh(x * 2) * 0.6, 3.5, 0.35)


def reverse_swell(dur=1.6):
    n = secs(dur)
    t = np.arange(n) / SR
    x = hp(noise(n), 2000) * (t / dur) ** 3
    return reverb(x * 0.35, 2.0, 0.4)


def crack(dur=1.2):
    n = secs(dur)
    t = np.arange(n) / SR
    x = hp(noise(n), 1500) * np.exp(-t / 0.03) * 1.0
    x += sine(70, n) * np.exp(-t / 0.2) * 0.6
    return reverb(np.tanh(x * 2) * 0.5, 1.8, 0.3)


def rumble(dur=8.0):
    n = secs(dur)
    t = np.arange(n) / SR
    x = lp(brown(n), 160) * 1.2 + lp(noise(n), 900) * 0.15
    e = np.clip(t / 2.0, 0, 1) * np.clip((dur - t) / 2.0, 0, 1)
    return reverb(np.tanh(x * e * 2) * 0.6, 2.5, 0.2)


def tape_stop(x, dur=0.6):
    """slow a stereo buffer's tail to a halt (synth 'cuts off')."""
    n = secs(dur)
    if len(x) < n:
        return x
    head = x[:-n]
    tail = x[-n:]
    t = np.linspace(0, 1, n)
    pos = np.cumsum(1 - t) / n * n * 0.5
    idx = np.clip(pos.astype(int), 0, n - 1)
    slowed = tail[idx] * (1 - t)[:, None]
    return np.concatenate([head, slowed])


# ------------------------------------------------------------------ voice processing
def voice_chain(v, sr_in=24000):
    """resample to 48k, high-pass, gentle compression, presence, short room."""
    from scipy.signal import resample_poly
    v = resample_poly(v, SR, sr_in)
    v = hp(v, 75)
    # presence lift + de-boom
    v = v + bp(v, 2500, 5000) * 0.18 - bp(v, 180, 320) * 0.12
    # soft compression
    envl = np.sqrt(np.maximum(lp(v ** 2, 12), 0))
    g = np.minimum(1.0, (0.12 / (envl + 1e-4)) ** 0.35)
    v = v * g
    v = norm(v, 0.9)
    return reverb(v, 0.9, 0.08, pre=0.01, bright=5000)


def duck_curve(voice_st, depth_db=10, attack=0.08, release=0.5):
    e = np.abs(voice_st).max(1)
    e = np.maximum(lp(e, 6), 0)
    on = (e > 0.02).astype(np.float64)
    # smooth on/off with different attack/release
    out = np.zeros_like(on)
    a = math.exp(-1 / (attack * SR)); r = math.exp(-1 / (release * SR))
    s = 0.0
    # vectorised approximation: two passes of one-pole
    out = signal.lfilter([1 - r], [1, -r], on)
    out = np.maximum(out, signal.lfilter([1 - a], [1, -a], on))
    out = np.clip(out * 1.5, 0, 1)
    g = 10 ** (-depth_db * out / 20)
    return g


def master(mix, target_peak=0.95):
    # gentle bus compression + limiter
    x = mix.copy()
    envl = np.maximum(lp(np.abs(x).max(1), 8), 1e-4)
    g = np.minimum(1.0, (0.5 / envl) ** 0.25)
    x = x * g[:, None]
    x = np.tanh(x * 1.1) / 1.1
    return norm(x, target_peak)
