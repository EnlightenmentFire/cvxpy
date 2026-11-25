"""Original chiptune music + sound effects, synthesized from scratch with numpy."""
import numpy as np

SR = 44100
rng = np.random.default_rng(1849)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a=0.005, d=0.05, s=0.7, r=0.05, dur=None):
    tot = n
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    e = np.full(tot, s, np.float32)
    A = min(A, tot)
    e[:A] = np.linspace(0, 1, A, endpoint=False) if A else e[:A]
    D2 = min(D, tot - A)
    if D2 > 0:
        e[A:A + D2] = np.linspace(1, s, D2)
    R2 = min(R, tot)
    if R2 > 0:
        e[-R2:] *= np.linspace(1, 0, R2)
    return e


def osc_square(freq, dur, duty=0.5, vib=0.0, vib_rate=6.0, bend=None):
    t = t_(dur)
    f = np.full_like(t, freq) if np.isscalar(freq) else freq
    if vib:
        f = f * (1 + vib * np.sin(2 * np.pi * vib_rate * t) * np.clip(t * 4, 0, 1))
    if bend is not None:
        f = f * bend(t)
    ph = np.cumsum(f) / SR
    return np.where((ph % 1.0) < duty, 1.0, -1.0).astype(np.float32)


def osc_tri(freq, dur, bend=None):
    t = t_(dur)
    f = np.full_like(t, freq) if np.isscalar(freq) else freq
    if bend is not None:
        f = f * bend(t)
    ph = (np.cumsum(f) / SR) % 1.0
    # 4-bit stepped triangle like old sound chips
    tri = 2 * np.abs(2 * ph - 1) - 1
    return (np.round(tri * 7.5) / 7.5).astype(np.float32)


def osc_saw(freq, dur):
    ph = (np.cumsum(np.full(int(dur * SR), freq)) / SR) % 1.0
    return (2 * ph - 1).astype(np.float32)


def noise(dur, period=1):
    n = int(dur * SR)
    x = rng.uniform(-1, 1, n // period + 1).astype(np.float32)
    return np.repeat(x, period)[:n]


def pluck(freq, dur, bright=0.5, decay=0.996):
    """Karplus-Strong twang (banjo/guitar-ish)."""
    n = int(dur * SR)
    N = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, N).astype(np.float32)
    blocks = []
    for _ in range(n // N + 1):
        blocks.append(buf)
        buf = decay * (bright * buf + (1 - bright) * np.roll(buf, -1))
    return np.concatenate(blocks)[:n].astype(np.float32)


def lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y


def onepole_lp(x, cutoff):
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x).astype(np.float32)


def bandpass(x, lo, hi):
    from scipy.signal import butter, sosfilt
    sos = butter(2, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def hp(x, f):
    from scipy.signal import butter, sosfilt
    sos = butter(2, f, btype="high", fs=SR, output="sos")
    return sosfilt(sos, x).astype(np.float32)


def place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * gain


# ------------------------------------------------------------------ drums
def kick():
    d = 0.18
    t = t_(d)
    f = 150 * np.exp(-t * 30) + 45
    ph = np.cumsum(f) / SR
    return (np.sin(2 * np.pi * ph) * np.exp(-t * 18)).astype(np.float32)


def snare():
    d = 0.16
    t = t_(d)
    return (noise(d, 2) * np.exp(-t * 22) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4).astype(np.float32)


def hat(open_=False):
    d = 0.12 if open_ else 0.04
    t = t_(d)
    return (hp(noise(d, 1), 6000) * np.exp(-t * (20 if open_ else 80))).astype(np.float32)


def clop(pitch=1.0):
    d = 0.06
    t = t_(d)
    return (bandpass(noise(d, 1), 700 * pitch, 2500 * pitch) * np.exp(-t * 70) * 2.2
            + np.sin(2 * np.pi * 420 * pitch * t) * np.exp(-t * 60) * 0.5).astype(np.float32)


# ------------------------------------------------------------------ music
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def nn(s):
    """'C5' -> midi number; '-' rest"""
    if s in ("-", "."):
        return None
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTE[name]


def seq(notes, step, voice, gain=1.0, total=None):
    """notes: list of (note_str or None, steps). voice(freq, dur)->array"""
    tot = total or sum(n[1] for n in notes) * step
    buf = np.zeros(int(tot * SR) + SR, np.float32)
    pos = 0.0
    for name, steps in notes:
        dur = steps * step
        m = nn(name) if isinstance(name, str) else name
        if m is not None:
            x = voice(midi(m), dur)
            place(buf, x, pos, gain)
        pos += dur
    return buf[:int(tot * SR)]


def v_lead(freq, dur):
    d = dur * 0.92
    return osc_square(freq, d, 0.25, vib=0.006) * env(int(d * SR), 0.004, 0.08, 0.55, 0.03) * 0.33


def v_lead2(freq, dur):
    d = dur * 0.85
    return osc_square(freq, d, 0.5) * env(int(d * SR), 0.003, 0.05, 0.4, 0.02) * 0.22


def v_arp(freq, dur):
    d = dur * 0.8
    return osc_square(freq, d, 0.125) * env(int(d * SR), 0.002, 0.04, 0.3, 0.01) * 0.16


def v_bass(freq, dur):
    d = dur * 0.9
    return osc_tri(freq, d) * env(int(d * SR), 0.003, 0.02, 0.9, 0.02) * 0.55


def v_twang(freq, dur):
    d = min(dur * 1.6, 1.2)
    p = pluck(freq, d, bright=0.62, decay=0.994)
    sq = osc_square(freq, d, 0.25, vib=0.01, vib_rate=5.5, bend=lambda t: 1 + 0.03 * np.exp(-t * 25)) * env(int(d * SR), 0.003, 0.1, 0.25, 0.1)
    return (p * 0.42 + sq * 0.16).astype(np.float32)


def v_banjo(freq, dur):
    d = min(dur * 1.3, 0.5)
    return pluck(freq, d, bright=0.75, decay=0.99) * 0.3


def drum_pattern(bars, step, pattern, gain=0.5):
    """pattern: dict of name -> string of 16 chars per bar ('x' hit)."""
    tot = bars * 16 * step
    buf = np.zeros(int(tot * SR) + SR, np.float32)
    samples = {"k": kick(), "s": snare(), "h": hat(), "o": hat(True), "c": clop(1.0), "C": clop(0.75)}
    for name, pat in pattern.items():
        for b in range(bars):
            for i, ch in enumerate(pat):
                if ch == "x":
                    place(buf, samples[name], (b * 16 + i) * step, gain)
    return buf[:int(tot * SR)]


def adventure(duration, bpm=144, intensity=1.0):
    """Upbeat 16-bit adventure loop. C major: C - Am - F - G, 8 bars, repeats."""
    step = 60 / bpm / 4  # 16th notes
    mel = [  # 8 bars x 16 steps (original melody)
        ("G5", 2), ("C6", 2), ("E6", 2), ("G6", 3), ("E6", 1), ("D6", 2), ("C6", 2), ("D6", 2),
        ("E6", 2), ("C6", 2), ("A5", 4), ("-", 2), ("A5", 1), ("B5", 1), ("C6", 2), ("E6", 2), ("D6", 2),
        ("C6", 2), ("A5", 2), ("F5", 2), ("A5", 2), ("C6", 3), ("D6", 1), ("C6", 2), ("A5", 2),
        ("B5", 2), ("D6", 2), ("G6", 4), ("F6", 2), ("E6", 2), ("D6", 2), ("B5", 2),
        ("C6", 2), ("E6", 2), ("G6", 2), ("C7", 3), ("B6", 1), ("G6", 2), ("E6", 2), ("G6", 2),
        ("A6", 2), ("G6", 2), ("E6", 4), ("-", 2), ("C6", 1), ("D6", 1), ("E6", 2), ("C6", 2),
        ("F6", 2), ("E6", 2), ("D6", 2), ("C6", 2), ("A5", 2), ("C6", 2), ("F6", 2), ("A6", 2),
        ("G6", 3), ("F6", 1), ("E6", 2), ("D6", 2), ("G6", 4), ("-", 4),
    ]
    roots = ["C3", "A2", "F2", "G2", "C3", "A2", "F2", "G2"]
    chords = {"C3": [0, 4, 7], "A2": [0, 3, 7], "F2": [0, 4, 7], "G2": [0, 4, 7]}
    bass, arp = [], []
    for r in roots:
        m = nn(r)
        bass += [(m, 2), (m + 12, 2), (m, 2), (m + 12, 2), (m + 7, 2), (m + 12, 2), (m, 2), (m + 7, 2)]
        c = chords[r]
        for i in range(16):
            arp.append((m + 24 + c[i % 3] + (12 if (i // 3) % 2 else 0), 1))
    loop_len = 8 * 16 * step
    n_loops = int(np.ceil(duration / loop_len)) + 1
    L = seq(mel * n_loops, step, v_lead) * (0.9 if intensity < 1 else 1.0)
    B = seq(bass * n_loops, step, v_bass)
    A = seq(arp * n_loops, step, v_arp) * (0.6 + 0.4 * intensity)
    pat = {"k": "x...x...x...x...", "s": "....x.......x...", "h": "x.x.x.x.x.x.x.xx"}
    if intensity > 1.1:
        pat = {"k": "x.x.x...x.x.x..x", "s": "....x..x....x.x.", "h": "xxxxxxxxxxxxxxxx", "o": "..x...x...x...x."}
    D = drum_pattern(8 * n_loops, step, pat, 0.45)
    n = min(len(L), len(B), len(A), len(D))
    mix = L[:n] + B[:n] + A[:n] + D[:n]
    return mix[:int(duration * SR)]


def western(duration, bpm=112, slow=False):
    """Twangy western chiptune, E minor -> G. Galloping clip-clop rhythm."""
    if slow:
        bpm = 88
    step = 60 / bpm / 4
    mel = [  # original tune, 8 bars
        ("E5", 3), ("B4", 1), ("E5", 2), ("G5", 2), ("F#5", 3), ("E5", 1), ("D5", 4),
        ("E5", 2), ("G5", 2), ("A5", 3), ("B5", 1), ("A5", 2), ("G5", 2), ("E5", 4),
        ("B5", 3), ("A5", 1), ("G5", 2), ("E5", 2), ("D5", 3), ("E5", 1), ("G5", 4),
        ("F#5", 2), ("E5", 2), ("D#5", 2), ("F#5", 2), ("E5", 6), ("-", 2),
        ("G5", 3), ("A5", 1), ("B5", 2), ("D6", 2), ("B5", 3), ("A5", 1), ("G5", 4),
        ("A5", 2), ("B5", 2), ("A5", 2), ("G5", 2), ("E5", 4), ("D5", 4),
        ("E5", 2), ("G5", 2), ("B5", 3), ("A5", 1), ("G5", 2), ("F#5", 2), ("E5", 2), ("D5", 2),
        ("B4", 2), ("D5", 2), ("F#5", 2), ("D#5", 2), ("E5", 8),
    ]
    roots = ["E2", "D2", "C2", "B1", "G2", "D2", "C2", "B1"]
    bass, banjo = [], []
    for r in roots:
        m = nn(r)
        # oom-pah gallop
        bass += [(m, 3), (None, 1), (m + 7, 2), (None, 2), (m, 3), (None, 1), (m + 7, 2), (None, 2)]
        minor = r in ("E2", "B1")
        third = 3 if r == "E2" else 4
        if r == "B1":
            third = 4
        banjo += [(m + 24, 2), (m + 24 + third, 1), (m + 31, 1)] * 4
    loop_len = 8 * 16 * step
    n_loops = int(np.ceil(duration / loop_len)) + 1
    L = seq(mel * n_loops, step, v_twang)
    B = seq(bass * n_loops, step, v_bass) * 0.9
    J = seq(banjo * n_loops, step, v_banjo) * 0.55
    D = drum_pattern(8 * n_loops, step, {"c": "x..xx..xx..xx..x" if not slow else "x...x...x...x...", "C": "..x...x...x...x." if not slow else "..x.......x....."}, 0.5)
    n = min(len(L), len(B), len(J), len(D))
    mix = L[:n] + B[:n] + J[:n] + D[:n]
    return mix[:int(duration * SR)]


# ------------------------------------------------------------------ SFX
def sfx_warp():
    d = 1.4
    t = t_(d)
    f = 200 * 2 ** (t * 3.2)
    a = osc_square(f, d, 0.5, vib=0.08, vib_rate=18) * 0.35
    b = osc_square(f * 1.5, d, 0.25, vib=0.05, vib_rate=12) * 0.2
    e = np.clip(t * 6, 0, 1) * np.clip((d - t) * 4, 0, 1)
    return ((a + b) * e).astype(np.float32)


def sfx_coin():
    a = osc_square(midi(83), 0.07, 0.5) * 0.35
    b = osc_square(midi(88), 0.35, 0.5) * env(int(0.35 * SR), 0.001, 0.05, 0.6, 0.25) * 0.35
    return np.concatenate([a, b])


def sfx_buzz(short=False):
    d = 0.14 if short else 0.32
    x = (osc_square(98, d, 0.5) * 0.5 + osc_square(103, d, 0.3) * 0.4) * env(int(d * SR), 0.002, 0.02, 0.9, 0.03)
    return x.astype(np.float32)


def sfx_fanfare():
    notes = [(72, 0.09), (76, 0.09), (79, 0.09), (84, 0.09), (79, 0.09), (84, 0.45)]
    out = []
    for m, d in notes:
        x = osc_square(midi(m), d, 0.25) * 0.3 + osc_square(midi(m - 12), d, 0.5) * 0.15
        out.append(x * env(len(x), 0.002, 0.04, 0.7, 0.02))
    trill = []
    for i in range(10):
        m = 84 if i % 2 == 0 else 88
        trill.append(osc_square(midi(m), 0.05, 0.25) * 0.25)
    return np.concatenate(out + trill + [osc_square(midi(91), 0.5, 0.25) * env(int(0.5 * SR), 0.002, 0.1, 0.5, 0.35) * 0.3]).astype(np.float32)


def sfx_levelup():
    out = []
    for m in [67, 71, 74, 79, 83, 86]:
        x = osc_square(midi(m), 0.06, 0.125) * 0.3
        out.append(x)
    out.append(osc_square(midi(91), 0.3, 0.125) * env(int(0.3 * SR), 0.001, 0.05, 0.5, 0.2) * 0.3)
    return np.concatenate(out).astype(np.float32)


def sfx_roar():
    d = 1.3
    t = t_(d)
    f = 70 + 40 * np.sin(2 * np.pi * 7 * t) * np.exp(-t)
    growl = osc_square(f * (1 + 0.4 * np.exp(-t * 3)), d, 0.3) * 0.5
    nz = bandpass(noise(d, 3), 200, 1800) * 1.4
    e = np.clip(t * 8, 0, 1) * np.exp(-t * 1.6)
    x = np.tanh((growl + nz) * 2.0) * e * 0.55
    return x.astype(np.float32)


def sfx_whir(d=2.0):
    t = t_(d)
    f = 300 + 1600 * (t / d) ** 1.5
    x = osc_square(f, d, 0.5) * 0.12 + osc_saw(1, d) * 0
    x += bandpass(noise(d, 1), 2000, 6000) * 0.15 * (t / d)
    return (x * np.clip(t * 5, 0, 1)).astype(np.float32)


def sfx_heehaw():
    out = []
    for k in range(2):
        d1, d2 = 0.32, 0.42
        t1, t2 = t_(d1), t_(d2)
        hee = osc_square(880 + 120 * np.sin(2 * np.pi * 3 * t1), d1, 0.3, vib=0.04, vib_rate=28) * 0.25
        hee += bandpass(noise(d1, 1), 1500, 3500) * 0.18
        hee *= env(len(hee), 0.03, 0.05, 0.8, 0.05)
        haw = osc_square(300 - 60 * t2, d2, 0.4, vib=0.06, vib_rate=24) * 0.35
        haw += bandpass(noise(d2, 2), 300, 1200) * 0.2
        haw = np.tanh(haw * 2) * 0.4 * env(len(haw), 0.02, 0.05, 0.8, 0.12)
        out += [hee, haw]
    return np.concatenate(out).astype(np.float32)


def sfx_splash():
    d = 0.9
    t = t_(d)
    x = bandpass(noise(d, 1), 400, 5000) * np.exp(-t * 5) * 0.9
    for i in range(8):
        at = 0.08 + i * 0.07 + rng.uniform(0, 0.04)
        f0 = rng.uniform(700, 1500)
        dd = 0.06
        b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + t_(dd) * 8)) / SR) * np.exp(-t_(dd) * 50) * 0.3
        place(x, b.astype(np.float32), at)
    return x.astype(np.float32)


def sfx_gameover():
    out = []
    for m, d in [(72, 0.22), (71, 0.22), (70, 0.22), (69, 0.22), (64, 0.22), (60, 0.8)]:
        x = osc_square(midi(m), d, 0.5, vib=0.01 if d > 0.5 else 0) * 0.28 + osc_tri(midi(m - 12), d) * 0.3
        out.append(x * env(len(x), 0.004, 0.05, 0.7, 0.06))
    return np.concatenate(out).astype(np.float32)


def sfx_thud():
    d = 0.5
    t = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 5) + 30) / SR) * np.exp(-t * 7) * 0.8
    x += onepole_lp(noise(d, 1), 900) * np.exp(-t * 9) * 1.2
    return x.astype(np.float32)


def sfx_clang():
    d = 0.7
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) * a for f, k, a in [(1320, 6, .3), (2071, 8, .25), (2930, 10, .2), (3710, 12, .12), (660, 5, .15)])
    x += hp(noise(0.03, 1), 3000)[:int(0.03 * SR)].tolist() and 0
    return (x * 0.7).astype(np.float32)


def sfx_whoosh(d=0.5, up=True):
    t = t_(d)
    lo = 300 + (2500 if up else -0) * (t / d)
    x = bandpass(noise(d, 1), 400, 3000) * np.sin(np.pi * t / d) * 0.6
    return x.astype(np.float32)


def sfx_key():
    d = 0.08
    t = t_(d)
    x = hp(noise(d, 1), 1500) * np.exp(-t * 60) * 0.7 + np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40) * 0.6
    return x.astype(np.float32)


def sfx_fire(d=2.5):
    t = t_(d)
    x = onepole_lp(noise(d, 1), 1200) * 0.4
    for i in range(int(d * 25)):
        at = rng.uniform(0, d)
        c = hp(noise(0.01, 1), 2000) * rng.uniform(0.2, 0.7)
        place(x, c, at)
    return (x * np.clip(t * 3, 0, 1) * np.clip((d - t) * 3, 0, 1)).astype(np.float32)


def sfx_steam(d=1.2):
    t = t_(d)
    return (hp(noise(d, 1), 3000) * 0.35 * np.clip(t * 10, 0, 1) * np.clip((d - t) * 2, 0, 1)).astype(np.float32)


def sfx_unroll(d=3.0):
    t = t_(d)
    x = bandpass(noise(d, 1), 800, 4000) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t))
    for i in range(int(d * 10)):
        place(x, sfx_key() * 0.25, i * 0.1)
    return (x * np.clip((d - t) * 2, 0, 1)).astype(np.float32)


def sfx_select():
    return np.concatenate([osc_square(midi(76), 0.05, 0.25), osc_square(midi(83), 0.08, 0.25)]) * 0.25


def sfx_ding():
    d = 0.6
    return (osc_square(midi(96), d, 0.5) * env(int(d * SR), 0.001, 0.02, 0.4, 0.5) * 0.2).astype(np.float32)


def sfx_zap():
    d = 0.35
    t = t_(d)
    return (osc_square(1500 * np.exp(-t * 6) + 100, d, 0.5) * np.exp(-t * 6) * 0.3).astype(np.float32)


def sfx_pop():
    d = 0.12
    t = t_(d)
    return (osc_square(400 * (1 + t * 20), d, 0.5) * np.exp(-t * 25) * 0.3).astype(np.float32)


def sfx_drumroll(d=1.0):
    x = np.zeros(int(d * SR), np.float32)
    s = snare()
    n = int(d / 0.045)
    for i in range(n):
        place(x, s * (0.3 + 0.5 * i / n), i * 0.045)
    return x


SFX = {
    "warp": sfx_warp, "coin": sfx_coin, "buzz": sfx_buzz, "buzz_short": lambda: sfx_buzz(True), "fanfare": sfx_fanfare,
    "levelup": sfx_levelup, "roar": sfx_roar, "whir": sfx_whir, "heehaw": sfx_heehaw, "splash": sfx_splash,
    "gameover": sfx_gameover, "thud": sfx_thud, "clang": sfx_clang, "whoosh": sfx_whoosh, "key": sfx_key,
    "fire": sfx_fire, "steam": sfx_steam, "unroll": sfx_unroll, "select": sfx_select, "ding": sfx_ding,
    "zap": sfx_zap, "pop": sfx_pop, "drumroll": sfx_drumroll,
}
