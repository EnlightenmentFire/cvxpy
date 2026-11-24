"""Synthesised score + sound design (no samples, everything generated here).

Layers
  beat   : cigarette-machine clack loop (bandpassed noise + metallic pings + low thunk)
  pad    : restrained accordion (two slightly detuned reeds, bellows swell), D minor
  piano  : sparse low-register notes
  hum    : low drone used after every 'machine stop' (the sound mark for uncertainty)
The beat follows a tempo map built from the timeline: it cuts dead at each 'stop' event, drops out
for the three questions, tightens during the vicious circle and relaxes when rules turn into a shield.
"""
import math

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def _env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def _bandnoise(n, lo, hi):
    x = rng.normal(0, 1, n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.max(np.abs(y)) + 1e-9)


_CLACKS = {}


def clack(accent=1.0, bright=1.0):
    key = (bright, int(rng.integers(0, 6)))
    if key not in _CLACKS:
        _CLACKS[key] = _clack_raw(bright)
    return _CLACKS[key] * accent


def _clack_raw(bright=1.0):
    accent = 1.0
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    y = _bandnoise(n, 1400, 5200 * bright) * _env_exp(n, 0.010) * 0.8
    for f, a, tau in ((1230, 0.35, 0.030), (2710, 0.25, 0.022), (4130, 0.12, 0.015)):
        y += a * np.sin(2 * np.pi * f * t + rng.random() * 6) * _env_exp(n, tau)
    return y * 0.5 * accent


def thunk(accent=1.0):
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f = 78 * (1 + 0.6 * np.exp(-t / 0.01))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env_exp(n, 0.045) * 0.55 * accent


def big_clack():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    y = _bandnoise(n, 300, 6000) * _env_exp(n, 0.03)
    y += 0.6 * np.sin(2 * np.pi * 95 * t) * _env_exp(n, 0.08)
    y += 0.4 * np.sin(2 * np.pi * 1630 * t) * _env_exp(n, 0.05)
    # a short mechanical grind
    g = _bandnoise(n, 200, 1500) * (np.sin(2 * np.pi * 31 * t) > 0) * _env_exp(n, 0.09) * 0.4
    return (y + g) * 0.7


def hum(dur, f0=55.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * 2 * f0 * 1.003 * t) +
         0.25 * np.sin(2 * np.pi * 3 * f0 * 0.998 * t) + 0.12 * np.sin(2 * np.pi * 5 * f0 * t))
    y *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.7 * t)
    a = int(0.25 * SR)
    env = np.ones(n)
    env[:a] = np.linspace(0, 1, a)
    r = int(min(dur * 0.6, 2.5) * SR)
    env[-r:] *= np.linspace(1, 0, r) ** 1.5
    return y * env * 0.065


# ------------------------------------------------------------------ tonal layers
NOTE = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


CHORDS = [  # restrained D-minor cycle
    [("D", 3), ("A", 3), ("D", 4), ("F", 4)],
    [("Bb", 2), ("F", 3), ("D", 4), ("F", 4)],
    [("G", 2), ("D", 3), ("Bb", 3), ("D", 4)],
    [("A", 2), ("E", 3), ("C#", 4), ("E", 4)],
]


def reed(freq, dur, detune_cents=4.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for d in (-detune_cents / 2, detune_cents / 2):
        f = freq * 2 ** (d / 1200)
        for h in range(1, 12):
            if f * h > 5000:
                break
            amp = (1.0 / h) * (1.0 if h % 2 else 0.55)
            y += amp * np.sin(2 * np.pi * f * h * t + h * 0.3)
    return y


_PADS = {}


def pad_chord(chord, dur):
    key = (tuple(chord), round(dur, 2))
    if key not in _PADS:
        _PADS[key] = _pad_raw(chord, dur)
    return _PADS[key]


def _reed_cached(freq, dur):
    # one long buffer per pitch, sliced (phase continuity is irrelevant between chords)
    k = round(freq, 3)
    need = int(dur * SR)
    buf = _REEDS.get(k)
    if buf is None or len(buf) < need:
        buf = reed(freq, max(dur, 12.0))
        _REEDS[k] = buf
    return buf[:need]


_REEDS = {}


def _pad_raw(chord, dur):
    n = int(dur * SR)
    y = np.zeros(n)
    for (nm, oc) in chord:
        y += _reed_cached(hz(nm, oc), dur)
    t = np.arange(n) / SR
    att = np.clip(t / 0.6, 0, 1)
    rel = np.clip((dur - t) / 0.8, 0, 1)
    swell = 0.8 + 0.2 * np.sin(np.pi * t / dur)
    y *= att * rel * swell
    # gentle low-pass via moving average
    k = 9
    y = np.convolve(y, np.ones(k) / k, mode="same")
    return y / (np.max(np.abs(y)) + 1e-9) * 0.22


def piano_note(freq, dur=3.5, vel=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for h in range(1, 9):
        fh = freq * h * (1 + 0.0004 * h * h)
        y += (0.7 ** h) * np.sin(2 * np.pi * fh * t) * np.exp(-t * (0.9 + 0.5 * h))
    y *= np.clip(t / 0.004, 0, 1)
    return y * vel * 0.35


def add(buf, x, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * gain


# ------------------------------------------------------------------ the score
def build_score(tl, total=None):
    total = total or tl["total"]
    n = int(total * SR) + SR
    beat = np.zeros(n)
    tonal = np.zeros(n)
    sfx = np.zeros(n)
    L = tl["lines"]
    ev = tl["events"]
    stops = [t for (t, k, p) in ev if k == "stop"]

    def lt(i, end=False):
        return L[i][1] if end else L[i][0]

    # --- beat tempo/level map -------------------------------------------------------
    # segments: (start, end, bpm, level)
    segs = []
    cold_stop = stops[0]
    segs.append((0.0, cold_stop, 104, 1.0))
    # after the cold stop: silence until the intro settles, then a soft beat under the intro
    segs.append((lt("i01") + 0.5, lt("s1_01") - 2.0, 104, 0.35))
    segs.append((lt("s1_01"), stops[1], 104, 0.5))
    segs.append((lt("s2_05"), lt("s3_09"), 104, 0.4))
    segs.append((lt("s3_14"), lt("s4_05"), 104, 0.4))
    segs.append((lt("s4_11"), lt("s5_02"), 104, 0.4))
    segs.append((lt("s5_04"), lt("s6_01"), 104, 0.45))
    segs.append((lt("s6_03"), lt("s6_04"), 104, 0.5))
    # vicious circle: tighter and tighter
    segs.append((lt("s6_04"), lt("s6_06"), "accel", 0.7))
    segs.append((lt("s6_06"), lt("s6_08") + 1.5, 120, 0.5))
    segs.append((lt("s6_08") + 1.5, lt("s6_11", True), 78, 0.35))
    segs.append((lt("s7_05"), lt("s7_07", True), 92, 0.3))
    for (a, b, bpm, lvl) in segs:
        t = a
        k = 0
        while t < b - 0.05:
            if bpm == "accel":
                u = (t - a) / max(1e-6, b - a)
                cur = 104 + 52 * u ** 1.4
            else:
                cur = bpm
            step = 60.0 / cur / 2  # eighth notes
            acc = 1.0 if k % 4 == 0 else (0.7 if k % 2 == 0 else 0.45)
            fade = min(1.0, (t - a) / 1.2, (b - t) / 0.4)
            add(beat, clack(acc, 1.0 if bpm != 78 else 0.6), t, lvl * fade)
            if k % 4 == 0:
                add(beat, thunk(1.0), t, lvl * fade)
            t += step
            k += 1
    # conveyor hiss under the cold open
    hiss = _bandnoise(int(cold_stop * SR), 300, 2500) * 0.04
    add(beat, hiss, 0.0)

    # --- stops: big clack, half-second silence, then the hum -----------------------------
    for st in stops:
        add(sfx, big_clack(), st - 0.02, 0.9)
        add(sfx, hum(6.0 if st == cold_stop else 4.5), st + 0.5, 1.0)

    # light 'uncertainty' marks (beat dropout handled by segments; add a low tone)
    for lid in ("s2_03", "s4_07"):
        add(sfx, hum(3.0, 49.0), lt(lid) + 0.2, 0.55)

    # --- tonal layers -------------------------------------------------------------------
    bar = 60.0 / 104 * 4
    chord_len = bar * 2

    def pad_run(a, b, gain=1.0, start_chord=0):
        t = a
        k = start_chord
        while t < b - 0.5:
            d = min(chord_len, b - t) + 0.8
            add(tonal, pad_chord(CHORDS[k % 4], d), t, gain)
            t += chord_len
            k += 1

    title = [c for c in tl["cards"] if c["sec"] == "title"][0]
    pad_run(title["start"], tl["sections"]["intro"][1], 1.0)
    add(tonal, piano_note(hz("D", 3), 5.0, 0.8), title["start"] + 0.1)
    add(tonal, piano_note(hz("A", 3), 4.0, 0.5), title["start"] + 1.2)
    for sec in ("s1", "s2", "s3", "s4", "s5", "s6", "s7"):
        a, b = tl["sections"][sec]
        lvl = {"s7": 0.75}.get(sec, 0.6)
        pad_run(a, b, lvl, start_chord={"s1": 0, "s2": 2, "s3": 0, "s4": 1, "s5": 2, "s6": 3, "s7": 0}[sec])
        # chapter card: one low piano note
        add(tonal, piano_note(hz("D", 3) if sec != "s6" else hz("A", 2), 4.0, 0.7), a + 0.05)
    # three questions: a single piano note under each question
    for lid, (nm, oc) in (("s7_02", ("F", 4)), ("s7_03", ("E", 4)), ("s7_04", ("D", 4))):
        add(tonal, piano_note(hz(nm, oc), 4.0, 0.45), lt(lid))
    # ending
    a, b = tl["sections"]["end"]
    pad_run(a, tl["end_main"] + 3.0, 0.7)
    for lid, (nm, oc) in (("e01", ("A", 3)), ("e02", ("F", 3)), ("e03", ("D", 3))):
        add(tonal, piano_note(hz(nm, oc), 5.0, 0.55), lt(lid))
    add(sfx, clack(1.0), tl["end_main"] + 0.6, 0.8)
    pad_run(tl["teaser"][0], tl["sources"][1], 0.45, start_chord=0)
    return beat, tonal, sfx


def duck_envelope(voice, depth_db=-13.0, attack=0.06, release=0.45):
    """Gain curve for music given the narration track (1.0 = no duck)."""
    win = int(0.02 * SR)
    e = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, mode="same"))
    active = (e > 10 ** (-45 / 20)).astype(float)
    # hold short gaps so the music doesn't pump between words
    hold = int(0.35 * SR)
    act = np.convolve(active, np.ones(hold), mode="same") > 0
    target = np.where(act, 10 ** (depth_db / 20), 1.0)
    g = np.empty_like(target)
    a_c = math.exp(-1 / (attack * SR))
    r_c = math.exp(-1 / (release * SR))
    cur = 1.0
    # vectorised enough for minutes of audio at 48k: process in python with stride
    step = 48
    for i in range(0, len(target), step):
        tg = target[i]
        c = a_c ** step if tg < cur else r_c ** step
        cur = tg + (cur - tg) * c
        g[i:i + step] = cur
    return g


def lowpass(y, fc):
    from scipy.signal import butter, sosfilt
    sos = butter(2, fc / (SR / 2), output="sos")
    return sosfilt(sos, y)
