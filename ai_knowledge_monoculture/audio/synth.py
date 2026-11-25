"""Music beds and sound effects, all synthesised here with numpy (no third-party samples).
Everything is mono float32 at SR unless stated; the mixer pans/sums later."""
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

SR = 48000
RNG = np.random.default_rng(1234)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate([np.linspace(0, 1, a_n, endpoint=False), np.linspace(1, s, d_n, endpoint=False),
                        np.full(s_n, s), np.linspace(s, 0, r_n)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def lp(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), "low", output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), "high", output="sos"), x)


def bp(x, f1, f2, order=2):
    return sosfilt(butter(order, [f1 / (SR / 2), f2 / (SR / 2)], "band", output="sos"), x)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ instruments
def pluck(freq, dur, damp=0.996, bright=0.5, seed=0):
    """Karplus-Strong plucked string (lyre / harpsichord)."""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p)
    buf = bright * buf + (1 - bright) * np.convolve(buf, np.ones(3) / 3, mode="same")
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        nxt = buf[(i + 1) % p]
        buf[i % p] = damp * 0.5 * (buf[i % p] + nxt)
    return out


def pluck_fast(freq, dur, damp=0.996, bright=0.5, seed=0):
    """Vectorised Karplus-Strong (period-block recursion)."""
    n = int(dur * SR)
    p = max(2, int(round(SR / freq)))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p)
    buf = bright * buf + (1 - bright) * np.convolve(buf, np.ones(3) / 3, mode="same")
    blocks = [buf]
    for _ in range(n // p + 1):
        b = blocks[-1]
        nb = damp * 0.5 * (b + np.roll(b, -1))
        blocks.append(nb)
    return np.concatenate(blocks)[:n]


def reed(freq, dur, vib=5.2, seed=0):
    """Accordion-like reed: two slightly detuned pulse-ish waves with tremolo."""
    t = t_axis(dur)
    out = np.zeros_like(t)
    for det in (1.0, 1.0035):
        ph = 2 * np.pi * freq * det * t
        w = sum(np.sin(k * ph) / k ** 1.15 for k in range(1, 9))
        out += w
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * vib * t)
    return lp(out, 3200) * env_adsr(len(t), 0.03, 0.1, 0.85, 0.12)


def epiano(freq, dur, seed=0):
    """Soft FM electric piano (1970s colour)."""
    t = t_axis(dur)
    mod = np.sin(2 * np.pi * freq * 1.0 * t) * 1.3 * np.exp(-t * 3.5)
    car = np.sin(2 * np.pi * freq * t + mod)
    return car * np.exp(-t * 1.6) * env_adsr(len(t), 0.004, 0.2, 0.9, 0.15)


def pad(freqs, dur, cutoff=1400, detune=0.004):
    t = t_axis(dur)
    out = np.zeros_like(t)
    for f in freqs:
        for d in (-detune, 0, detune):
            ph = (f * (1 + d) * t) % 1.0
            out += (2 * ph - 1) * 0.33
    out = lp(lp(out, cutoff), cutoff)
    return out * env_adsr(len(t), min(1.2, dur * 0.3), 0.3, 0.9, min(1.5, dur * 0.3)) / max(1, len(freqs))


def pulse_kick(dur=0.35, f0=58):
    t = t_axis(dur)
    f = f0 * (1 + 1.6 * np.exp(-t * 30))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9)


def tick(dur=0.04, f1=6000, f2=11000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, int(dur * SR))
    return bp(x, f1, f2) * np.exp(-t_axis(dur) * 120)


# ------------------------------------------------------------------ sound effects
def sfx_key(seed=0):
    rng = np.random.default_rng(seed)
    d = 0.035
    x = rng.normal(0, 1, int(d * SR)) * np.exp(-t_axis(d) * 260)
    body = np.sin(2 * np.pi * rng.uniform(1800, 2600) * t_axis(d)) * np.exp(-t_axis(d) * 180) * 0.4
    return bp(x, 1500, 7000) * 0.6 + body


def sfx_pop():
    """The one comic 'bo' for the jackrabbit."""
    d = 0.16
    t = t_axis(d)
    f = 820 * np.exp(-t * 14) + 230
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 26)
    x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    return x * 0.9


def sfx_copier(dur=2.2):
    t = t_axis(dur)
    hum = (np.sin(2 * np.pi * 100 * t) * 0.5 + np.sin(2 * np.pi * 200 * t) * 0.25 + np.sin(2 * np.pi * 300 * t) * 0.1)
    noise = RNG.normal(0, 1, len(t))
    sweep = bp(noise, 600, 2400) * (0.5 + 0.5 * np.sin(np.pi * np.clip(t / dur, 0, 1)))
    clunk = np.zeros_like(t)
    k = pulse_kick(0.12, 90) * 0.8
    clunk[: len(k)] += k
    e = env_adsr(len(t), 0.08, 0.1, 0.9, 0.35)
    return (hum * 0.35 + sweep * 0.25 + clunk) * e


def sfx_pebble(seed=0):
    rng = np.random.default_rng(seed)
    d = 0.25
    t = t_axis(d)
    click = bp(rng.normal(0, 1, len(t)), 1500, 5000) * np.exp(-t * 90)
    pot = np.sin(2 * np.pi * rng.uniform(260, 340) * t) * np.exp(-t * 22) * 0.6
    ring = np.sin(2 * np.pi * rng.uniform(900, 1200) * t) * np.exp(-t * 35) * 0.25
    return click * 0.7 + pot + ring


def sfx_beep(f=1046.5, d=0.09):
    t = t_axis(d)
    return np.sin(2 * np.pi * f * t) * env_adsr(len(t), 0.003, 0.02, 0.8, 0.03) * 0.5


def sfx_brake():
    d = 1.4
    t = t_axis(d)
    thunk = pulse_kick(0.5, 45) * 1.0
    hiss = lp(hp(RNG.normal(0, 1, len(t)), 2500), 9000) * np.exp(-t * 3.2) * 0.25
    hiss[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))   # soften the attack (no inter-sample spikes)
    out = hiss
    out[: len(thunk)] += thunk
    return out


def sfx_wind(dur):
    t = t_axis(dur)
    n = RNG.normal(0, 1, len(t))
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t) * np.sin(2 * np.pi * 0.07 * t + 1)
    return bp(n, 200, 1400) * lfo * 0.5


def sfx_clock_tick(seed=0):
    return tick(0.03, 2500, 6000, seed) * 0.8


def sfx_whoosh(d=0.6):
    t = t_axis(d)
    n = RNG.normal(0, 1, len(t))
    e = np.sin(np.pi * t / d) ** 2
    lo = lp(n, 900) * e
    return lo * 0.6


def sfx_sting():
    """Short title sting: low pulse + bright pluck chord."""
    out = np.zeros(int(2.2 * SR))
    k = pulse_kick(0.6, 50)
    out[: len(k)] += k * 0.9
    for i, m in enumerate([57, 64, 69, 72]):
        p = pluck_fast(midi(m), 2.0, 0.9993, 0.7, seed=i) * 0.22
        out[int(0.01 * SR * i): int(0.01 * SR * i) + len(p)] += p
    return out


# ------------------------------------------------------------------ music beds
def bed_tech(dur, bpm=88, root=50, dark=False):
    """Minimal steady electronic pulse + pad (Dm - Bb - F - C)."""
    n = int(dur * SR)
    out = np.zeros(n + SR * 3)
    beat = 60 / bpm
    prog = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]] if not dark else \
           [[50, 53, 57], [49, 53, 56], [50, 53, 57], [46, 50, 53]]
    bar = beat * 4
    i = 0
    tt = 0.0
    while tt < dur:
        ch = prog[i % len(prog)]
        p = pad([midi(m) for m in ch], bar + 0.6, cutoff=900 if dark else 1200) * 0.5
        s = int(tt * SR)
        out[s: s + len(p)] += p
        for b in range(4):
            bt = tt + b * beat
            k = pulse_kick(0.35, 52) * (0.55 if b % 2 == 0 else 0.32)
            s2 = int(bt * SR)
            out[s2: s2 + len(k)] += k
            h = tick(0.05, 7000, 12000, seed=b + i) * 0.10
            s3 = int((bt + beat / 2) * SR)
            out[s3: s3 + len(h)] += h
        tt += bar
        i += 1
    return out[:n]


def bed_lyre(dur, seed=0):
    """Athens: sparse lyre-like plucks in D Dorian."""
    n = int(dur * SR)
    out = np.zeros(n + SR * 4)
    scale = [62, 64, 65, 67, 69, 71, 72, 74]
    rng = np.random.default_rng(seed)
    tt = 0.0
    k = 0
    while tt < dur:
        m = scale[rng.integers(0, len(scale))] if k % 4 else 62
        p = pluck_fast(midi(m - 12 if k % 8 == 0 else m), 3.0, 0.9992, 0.45, seed=k) * 0.35
        s = int(tt * SR)
        out[s: s + len(p)] += p
        tt += rng.choice([0.5, 0.75, 1.0])
        k += 1
    drone = pad([midi(38), midi(45)], dur, cutoff=500) * 0.25
    return out[:n] + drone[:n]


def bed_harpsichord(dur, bpm=96):
    """1788: a simple baroque progression on a harpsichord-like pluck (D major)."""
    n = int(dur * SR)
    out = np.zeros(n + SR * 4)
    prog = [[50, 62, 66, 69], [45, 61, 64, 69], [47, 62, 66, 71], [42, 61, 66, 69],
            [43, 62, 67, 71], [38, 62, 66, 69], [43, 59, 67, 71], [45, 61, 64, 69]]
    beat = 60 / bpm
    tt = 0.0
    i = 0
    while tt < dur:
        ch = prog[i % len(prog)]
        for b, m in enumerate([ch[0], ch[1], ch[2], ch[3], ch[2], ch[1], ch[2], ch[3]]):
            p = pluck_fast(midi(m), 1.6, 0.9985, 0.85, seed=i * 8 + b)
            p = hp(p, 180) * (0.32 if b else 0.4)
            s = int((tt + b * beat / 2) * SR)
            out[s: s + len(p)] += p
        tt += beat * 4
        i += 1
    return out[:n]


def bed_accordion(dur, bpm=104):
    """1906 Plymouth fair: a gentle 3/4 accordion waltz (G major)."""
    n = int(dur * SR)
    out = np.zeros(n + SR * 4)
    beat = 60 / bpm
    bars = [(43, [59, 62, 67]), (50, [57, 62, 66]), (43, [59, 62, 67]), (48, [55, 60, 64]),
            (43, [59, 62, 67]), (50, [57, 62, 66]), (48, [55, 60, 64]), (50, [57, 62, 66])]
    mel = [71, 74, 71, 69, 67, 69, 71, 67, 64, 66, 67, 69, 71, 69, 67, 66, 67, 71, 74, 72, 71, 69, 67, 69]
    tt = 0.0
    i = 0
    while tt < dur:
        bass, ch = bars[i % len(bars)]
        b = reed(midi(bass - 12), beat * 0.9) * 0.28
        s = int(tt * SR)
        out[s: s + len(b)] += b
        for k in (1, 2):
            c = sum(reed(midi(m), beat * 0.6) for m in ch) * 0.07
            s2 = int((tt + k * beat) * SR)
            out[s2: s2 + len(c)] += c
        for k in range(3):
            m = mel[(i * 3 + k) % len(mel)]
            r = reed(midi(m), beat * 0.95) * 0.12
            s3 = int((tt + k * beat) * SR)
            out[s3: s3 + len(r)] += r
        tt += beat * 3
        i += 1
    return out[:n]


def bed_70s(dur, bpm=80):
    """1970 corn: warm electric-piano chords (A minor-ish), slow."""
    n = int(dur * SR)
    out = np.zeros(n + SR * 4)
    prog = [[57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62]]
    beat = 60 / bpm
    tt = 0.0
    i = 0
    while tt < dur:
        for m in prog[i % len(prog)]:
            p = epiano(midi(m), beat * 4 + 0.5) * 0.12
            s = int(tt * SR)
            out[s: s + len(p)] += p
        tt += beat * 4
        i += 1
    return out[:n]


def bed_tension(dur, bpm=120):
    """Flash crash / 45 minutes: tighter pulse, low drone."""
    n = int(dur * SR)
    out = bed_tech(dur, bpm=bpm, dark=True) * 0.8
    drone = pad([midi(38), midi(45), midi(50)], dur, cutoff=420) * 0.35
    return out[:n] + drone[:n]
