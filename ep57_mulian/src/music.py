"""Original score + SFX, synthesized here (no samples, no third-party recordings -> no licence issue).
Instruments: guqin-like plucked string (Karplus-Strong + 吟 vibrato), guqin harmonics (泛音), xiao (breathy sine
stack), 磬/bowl (inharmonic partials), low drone. Mode: D 羽 pentatonic (D F G A C).
python music.py  -> WORK/audio/music.wav, WORK/audio/sfx.wav (48 kHz stereo)"""
import os, sys, json, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
R = np.random.default_rng(57)
D3 = 146.83
SCALE = [0, 3, 5, 7, 10]          # D F G A C (semitones)


def hz(deg, octv=0):
    o, k = divmod(deg, 5)
    return D3 * 2 ** ((SCALE[k] + 12 * (o + octv)) / 12)


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x)


def pluck(f, dur, bright=0.5, yin=0.0):
    """Karplus-Strong string, with optional slow pitch wobble (吟) via resampling"""
    n = int(dur * SR)
    N = int(SR / f)
    buf = R.uniform(-1, 1, N) * np.hanning(N) ** 0.3
    buf = lp(buf, 1500 + 4000 * bright, 1)
    out = np.zeros(n)
    b = buf.copy(); idx = 0
    decay = 0.996 + 0.0025 * (1 - min(f / 600, 1))
    # vectorised-by-period KS
    pos = 0
    while pos < n:
        seg = b.copy()
        L = min(N, n - pos)
        out[pos:pos + L] = seg[:L]
        b = decay * 0.5 * (seg + np.roll(seg, -1))
        pos += N
    if yin > 0:
        t = np.arange(n) / SR
        warp = t + yin * np.sin(2 * np.pi * 4.5 * t) * np.clip(t - 0.25, 0, None) / (1 + t) / (2 * np.pi * 4.5 * 50)
        out = np.interp(warp * SR, np.arange(n), out)
    env = np.exp(-np.arange(n) / SR / (dur * 0.45))
    body = lp(out, 2600, 2) * env
    return body * 0.5


def harmonic(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(2 * np.pi * 2 * f * t)
    return x * np.exp(-t / (dur * 0.3)) * np.minimum(1, t / 0.004) * 0.35


def qing(f, dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    parts = [(1.0, 1.0, 1.0), (2.76, 0.45, 0.55), (5.40, 0.22, 0.3), (8.93, 0.1, 0.18), (1.006, 0.6, 1.0)]
    x = np.zeros(n)
    for r, a, dk in parts:
        x += a * np.sin(2 * np.pi * f * r * t + R.random() * 6) * np.exp(-t / (dur * 0.35 * dk))
    x *= np.minimum(1, t / 0.002)
    return x * 0.3 * amp


def xiao(f, dur, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.4) / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    x = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    br = bp(R.normal(0, 1, n), f * 0.8, f * 3.5) * 0.18
    env = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.6).clip(0, 1)
    return (x + br) * env * 0.22 * amp


def drone(total, segs):
    """segs: list of (t0, t1, root_hz, level)"""
    n = int(total * SR); out = np.zeros(n); t = np.arange(n) / SR
    for (a, b, f, lv) in segs:
        i0, i1 = int(a * SR), min(n, int(b * SR))
        tt = t[i0:i1]
        x = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.5 * tt + 1) +
             0.35 * np.sin(2 * np.pi * f * 2.003 * tt + 2)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * tt))
        L = i1 - i0
        env = np.minimum(1, np.arange(L) / (SR * 3)) * np.minimum(1, (L - np.arange(L)) / (SR * 3))
        out[i0:i1] += x * env * lv
    return lp(out, 900) * 0.09


def place(buf, x, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i >= buf.shape[0]:
        return
    j = min(buf.shape[0], i + len(x))
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    buf[i:j, 0] += x[:j - i] * g * l * 1.41
    buf[i:j, 1] += x[:j - i] * g * r * 1.41


def reverb(x, secs=3.2, mix=0.32):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = R.normal(0, 1, n) * np.exp(-t / (secs / 6.9) * 1.0)
        ir = lp(ir, 5000)
        ir[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
        ir /= np.sqrt((ir ** 2).sum())
        out[:, c] = fftconvolve(x[:, c], ir)[: len(x)]
    return x * (1 - mix) + out * mix * 1.2


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"] + 1.0
    sec = {}
    for d in tl["lines"]:
        sec.setdefault(d["id"][0], d["t0"])
    lines = {d["id"]: d for d in tl["lines"]}
    order = "abcdefg"
    bounds = [(c, sec[c] - 0.3 if c != "a" else 0.0) for c in order]
    bounds = [(c, a, (bounds[i + 1][1] if i + 1 < len(bounds) else total)) for i, (c, a) in enumerate(bounds)]
    n = int(total * SR)
    M = np.zeros((n, 2))
    # density / register per section: (notes per bar, octave shift, xiao?, harmonics?)
    style = {"a": (0.8, -1, False, False), "b": (1.4, -1, False, True), "c": (1.8, 0, True, True),
             "d": (2.4, 0, True, True), "e": (2.2, 0, False, True), "f": (2.8, 0, False, True),
             "g": (2.0, 0, True, True)}
    bar = 60 / 66 * 4
    roots = {"a": D3 / 2, "b": D3 / 2, "c": hz(2) / 2, "d": D3 / 2, "e": hz(3) / 4, "f": hz(2) / 2, "g": D3 / 2}
    M[:, 0] += drone(total, [(a, b + 3, roots[c], 1.0 if c != "a" else 0.8) for c, a, b in bounds])
    M[:, 1] += M[:, 0]
    deg = 5
    for c, a, b in bounds:
        dens, octv, use_x, use_h = style[c]
        t = a + (2.5 if c == "a" else 0.6)
        while t < b - 1.0:
            # a phrase: 3-7 notes stepping through the mode, then rest
            k = int(R.integers(3, 8))
            step_t = bar / 4 / max(dens / 2, 0.6)
            for j in range(k):
                deg = int(np.clip(deg + R.choice([-2, -1, -1, 1, 1, 2, 0]), 0, 11))
                f = hz(deg, octv)
                dur = 3.5 if f < 200 else 2.6
                place(M, pluck(f, dur, bright=0.35 + 0.3 * R.random(), yin=1.0 if R.random() < 0.35 else 0), t,
                      pan=R.uniform(-0.35, 0.35), g=0.9)
                if use_h and R.random() < 0.18:
                    place(M, harmonic(f * 4, 2.2), t + step_t * 0.5, pan=R.uniform(-0.5, 0.5), g=0.6)
                t += step_t * R.choice([1, 1, 1, 2, 0.5])
            t += bar * R.uniform(0.6, 1.6) / max(dens / 1.6, 0.5)
        if use_x:
            tx = a + 4.0
            while tx < b - 6:
                ph = int(R.integers(2, 4))
                xd = int(np.clip(deg, 4, 9))
                for j in range(ph):
                    xd = int(np.clip(xd + R.choice([-1, 1, 2, -2]), 4, 10))
                    du = R.uniform(2.2, 4.0)
                    place(M, xiao(hz(xd, 0), du, 0.9), tx, pan=0.15, g=0.8)
                    tx += du * 0.92
                tx += R.uniform(10, 18)
        # section bell (except the opening, which has the louder hook bell below)
        if c != "a":
            place(M, qing(hz(0, 1), 7.0, 0.55), a + 0.1, pan=-0.1)
    # final: bell under the last quote, and a gentle closing strike
    g05 = lines.get("g05")
    if g05:
        place(M, qing(hz(0, 0), 9.0, 0.9), g05["t0"] - 0.1)
    place(M, qing(hz(0, 1), 8.0, 0.6), tl["lines"][-1]["t1"] + 0.6)
    M = reverb(M)
    # fade out tail
    fo = int(3.0 * SR)
    M[-fo:] *= np.linspace(1, 0, fo)[:, None]
    M /= np.abs(M).max() + 1e-9
    M *= 0.7
    os.makedirs(f"{WORK}/audio", exist_ok=True)
    sf.write(f"{WORK}/audio/music.wav", M.astype(np.float32), SR)

    # ---------------- SFX
    S = np.zeros((n, 2))
    a02 = lines["a02"]
    tf = a02["t0"] + 0.66 * (a02["t1"] - a02["t0"])
    def whoosh(dur):
        m = int(dur * SR); t = np.arange(m) / SR
        x = bp(R.normal(0, 1, m), 120, 1800) * np.minimum(1, t / 0.08) * np.exp(-t / 0.7)
        return x * 0.5
    def crackle(dur, rate=18):
        m = int(dur * SR); x = np.zeros(m)
        for _ in range(int(dur * rate)):
            i = int(R.random() * (m - 400))
            x[i:i + 300] += R.normal(0, 1, 300) * np.exp(-np.arange(300) / 40) * R.uniform(0.2, 1)
        return bp(x, 900, 7000) * 0.35 * np.minimum(1, np.arange(m) / SR / 0.3) * np.minimum(1, (m - np.arange(m)) / SR / 1.0)
    place(S, whoosh(2.5), tf - 0.05, g=0.9)
    place(S, crackle(5.0), tf, g=0.8)
    # bowl-fire close-up
    b10 = lines.get("b10")
    if b10:
        t2 = b10["t0"] + 0.62 * (b10["t1"] - b10["t0"])
        place(S, whoosh(2.0), t2 - 0.05, g=0.6)
        place(S, crackle(6.0, 14), t2, g=0.6)
    # rain during 雨安居
    shots = tl["shots"]
    for s in shots:
        if s["key"] in ("rain_retreat", "temple_south"):
            m = int((s["t1"] - s["t0"] + 0.5) * SR)
            x = bp(R.normal(0, 1, m), 1500, 9000) * 0.06
            env = np.minimum(1, np.arange(m) / SR / 1.0) * np.minimum(1, (m - np.arange(m)) / SR / 1.0)
            place(S, x * env * (1.0 if s["key"] == "rain_retreat" else 0.6), s["t0"], pan=-0.2)
            place(S, bp(R.normal(0, 1, m), 1500, 9000) * 0.06 * env, s["t0"], pan=0.2)
        if s["key"] in ("river", "river_people", "lantern_tease"):
            m = int((s["t1"] - s["t0"] + 0.5) * SR)
            x = lp(R.normal(0, 1, m), 600) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * np.arange(m) / SR)) * 0.08
            env = np.minimum(1, np.arange(m) / SR / 1.5) * np.minimum(1, (m - np.arange(m)) / SR / 1.5)
            place(S, x * env, s["t0"], pan=-0.3); place(S, np.roll(x, 3000) * env, s["t0"], pan=0.3)
    # opening sound hook (kept in the no-music version too): 磬 strike exactly on frame 0, deep + bright pair
    H = np.zeros((int(10 * SR), 2))
    place(H, qing(hz(0, 0), 9.0, 1.4), 0.0, pan=0.0)
    place(H, qing(hz(3, 1), 7.0, 0.7), 0.012, pan=0.2)
    H = reverb(H, 2.5, 0.25)
    S[:len(H)] += H * 0.55
    sf.write(f"{WORK}/audio/sfx.wav", S.astype(np.float32), SR)
    print("music", M.shape[0] / SR, "s")


if __name__ == "__main__":
    main()
