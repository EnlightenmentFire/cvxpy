"""Synthesized SFX (numpy), placed by timeline beats. -> stems/sfx.wav"""
import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
W = "/tmp/claude-0/work"; SR = 48000
rng = np.random.default_rng(1)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def drum(boom=1.0):  # big war drum
    n = int(2.0 * SR); t = np.arange(n) / SR
    f = 52 * (1 + 0.8 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    skin = lp(rng.normal(0, 1, n), 900) * np.exp(-t * 30) * 0.6
    return (body + skin) * boom
def horn(d=2.6, f0=146.8):  # low horn call (D3) with swell
    n = int(d * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t)
    ph = 2 * np.pi * np.cumsum(f0 * vib * (1 - 0.03 * np.exp(-t * 6))) / SR
    x = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, 12))
    e = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.6)
    return lp(x * e, 2200) * 0.5
def hooves(d, rate=2.2):
    n = int(d * SR); x = np.zeros(n)
    for k in range(int(d * rate * 4)):
        base = k // 4 / rate; off = [0, 0.07, 0.16, 0.22][k % 4]
        i = int((base + off + rng.uniform(0, 0.01)) * SR)
        if i < n - 2400:
            m = 2400; x[i:i + m] += lp(rng.normal(0, 1, m), 600) * env(m, 0.002, 0.02) * rng.uniform(0.5, 1)
    return x
def wind(d, lo=200, hi=900):
    n = int(d * SR); x = bp(rng.normal(0, 1, n), lo, hi)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(0.12 + 0.05 * rng.normal(0, 1, n) / 50) / SR)
    return x * mod * 0.6
def bell(f=880, d=1.6):
    n = int(d * SR); t = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * r * t) for r, a in [(1, 1), (2.76, 0.5), (5.4, 0.25)]) * np.exp(-t * 3) * 0.3
def thud():
    n = int(1.5 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 45 * t) * np.exp(-t * 5) + lp(rng.normal(0, 1, n), 300) * np.exp(-t * 12) * 0.8)
def splash():
    n = int(2.5 * SR); t = np.arange(n) / SR
    return bp(rng.normal(0, 1, n), 300, 6000) * np.exp(-t * 2.2) * np.minimum(1, t / 0.01)
def water(d):
    n = int(d * SR); return bp(rng.normal(0, 1, n), 150, 1200) * 0.35
def whoosh(d=0.8):
    n = int(d * SR); t = np.arange(n) / SR
    return bp(rng.normal(0, 1, n), 400, 3000) * np.sin(np.pi * t / d) ** 2 * 0.6
def fade(x, a=0.5, b=0.8):
    n = len(x); fa, fb = int(a * SR), int(b * SR)
    x = x.copy(); x[:fa] *= np.linspace(0, 1, fa); x[-fb:] *= np.linspace(1, 0, fb); return x

def crack(big=1.0):
    """tree trunk snapping: sharp broadband splinter + creak + low thump"""
    n = int(1.6 * SR); t = np.arange(n) / SR
    snap = bp(rng.normal(0, 1, n), 900, 7000) * np.exp(-t * 26) * 1.2
    spl = np.zeros(n)
    for k in range(14):
        i = int(rng.uniform(0.0, 0.25) * SR); m = int(0.03 * SR)
        spl[i:i + m] += bp(rng.normal(0, 1, m), 1500, 6000) * env(m, 0.001, 0.008) * rng.uniform(0.3, 1)
    cre = np.sin(2 * np.pi * np.cumsum(180 + 60 * np.sin(t * 9)) / SR) * np.exp(-t * 4) * 0.25
    thump = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 7) * 0.9
    return (snap + spl + bp(cre, 120, 900) + thump) * big
def crash(d=2.5):
    """canopy crashing down + rolling echo"""
    n = int(d * SR); t = np.arange(n) / SR
    x = bp(rng.normal(0, 1, n), 200, 4000) * np.exp(-t * 2.2) * np.minimum(1, t / 0.05)
    x += lp(rng.normal(0, 1, n), 200) * np.exp(-t * 3) * 1.2
    y = x.copy()
    for dl, g in [(0.23, 0.45), (0.51, 0.3), (0.9, 0.18), (1.4, 0.1)]:
        k = int(dl * SR); y[k:] += lp(x[:-k], 2500) * g
    return y * 0.7
def gate(d=4.0):
    """heavy wooden gate creaking open"""
    n = int(d * SR); t = np.arange(n) / SR
    f = 70 + 30 * np.sin(2 * np.pi * 0.7 * t) + 15 * rng.normal(0, 1, n).cumsum() / np.sqrt(n)
    x = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5, 80, 1800)
    x *= np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.8) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.3 * t) ** 2)
    return x * 0.5
def sea(d):
    n = int(d * SR); t = np.arange(n) / SR
    return lp(rng.normal(0, 1, n), 700) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t) ** 2) * 0.5
def chisel(d, rate=1.6):
    n = int(d * SR); x = np.zeros(n)
    for k in range(int(d * rate)):
        i = int((k / rate + rng.uniform(0, 0.2)) * SR); m = int(0.12 * SR)
        if i < n - m:
            tt = np.arange(m) / SR
            x[i:i + m] += (np.sin(2 * np.pi * rng.uniform(1800, 2600) * tt) * 0.4 + bp(rng.normal(0, 1, m), 2000, 6000)) * np.exp(-tt * 40) * rng.uniform(0.4, 1)
    return x
def fire_crackle(d):
    n = int(d * SR); x = bp(rng.normal(0, 1, n), 200, 1200) * 0.15
    for k in range(int(d * 8)):
        i = int(rng.uniform(0, d) * SR); m = int(0.01 * SR)
        if i < n - m: x[i:i + m] += rng.normal(0, 1, m) * rng.uniform(0.2, 0.8)
    return x
def drip():
    n = int(0.6 * SR); t = np.arange(n) / SR
    f = 1400 * np.exp(-t * 6) + 900
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.5

def main():
    tl = json.load(open(f"{W}/timeline.json")); T = tl["total"]
    out = np.zeros(int(T * SR) + SR * 6)
    def put(x, t, g=1.0):
        i = int(t * SR); out[i:i + len(x)] += x[:max(0, len(out) - i)] * g
    B = tl["beats"]
    def beats(v): return [b for b in B if b["v"] == v]
    def L(lid): return next(l for l in tl["lines"] if l["id"] == lid)
    # ---- opening sound hook: giant trees snapping one after another, echo, a beat of silence, then a lone taiko
    put(crack(1.0), 0.00, 1.0); put(crack(0.9), 0.34, 0.9); put(crack(1.0), 0.66, 1.0); put(crash(2.4), 0.70, 0.9)
    for k, tt in enumerate([1.9, 2.5, 3.2, 3.9]): put(crack(0.5), tt, 0.35 - k * 0.05)
    put(drum(1.0), 1.45, 1.0)
    for b in beats("ishi_legend"):
        for k in range(5): put(crack(0.6), b["start"] + 0.6 + k * 0.7, 0.4)
    for b in beats("ichiya"): put(fade(wind(b["end"] - b["start"], 150, 500) * 0.25, 0.5, 1.0), b["start"], 0.5)
    for v in ["mobilize", "march", "yamanaka", "north"]:
        for b in beats(v): put(whoosh(), b["start"] + 0.2, 0.5); put(drum(0.8), b["start"] + 0.5, 0.45)
    for v in ["fleet", "navy"]:
        for b in beats(v): put(fade(sea(b["end"] - b["start"]), 0.8, 1.2), b["start"], 0.6)
    for b in beats("yamanaka"): put(drum(1.0), b["start"] + 3.2, 0.7)
    for b in beats("dominoes"):
        t0 = L("c18")["t0"]
        for dt in (0.3, 2.6, 5.0): put(thud(), t0 + dt, 0.6)
    for b in beats("oldway"):
        t8 = L("a08")["t0"]; put(horn(2.4, 130.8), t8 - 0.3, 0.35); put(horn(2.4, 146.8), t8 + 1.3, 0.35)
    for b in beats("ishi_build"):
        d = b["end"] - b["start"]; put(fade(chisel(d) * 0.5 + fire_crackle(d), 0.5, 1.0), b["start"], 0.55)
    for b in beats("ishi_look"):
        d = b["end"] - b["start"]; put(fade(chisel(d, 0.8) * 0.3, 0.5, 1.0), b["start"], 0.4)
    for b in beats("tea"): put(fade(bell(660, 3.0) * 0.6, 0.01, 1.5), b["start"] + 0.4, 0.4)
    for b in beats("encircle"):
        d = b["end"] - b["start"]
        for k in range(int(d / 0.75)): put(drum(0.7 + 0.3 * k / max(1, d / 0.75)), b["start"] + k * 0.75, 0.35 + 0.35 * k / max(1, d / 0.75))
    for b in beats("surrender"): put(gate(5.0), b["start"] + 0.8, 0.6)
    for b in beats("daibutsu"): put(fade(fire_crackle(b["end"] - b["start"]) * 1.5, 0.8, 1.0), b["start"], 0.5)
    for b in beats("kenchi"): put(fade(wind(b["end"] - b["start"], 300, 1200) * 0.2, 0.8, 1.0), b["start"], 0.35)
    for b in beats("osaka"):
        q0 = L("f11")["t0"]; put(drip(), q0 + 1.0 + 2.0 + 0.05, 0.45)
        put(fade(wind(b["end"] - b["start"], 100, 400) * 0.18, 1.0, 2.5), b["start"], 0.35)
    out = out[:int(T * SR)]
    pk = np.abs(out).max(); out = out / pk * 0.7
    sf.write(f"{W}/stems/sfx.wav", np.stack([out, out], 1).astype(np.float32), SR, subtype="FLOAT")
    print("sfx ok", len(out) / SR)
if __name__ == "__main__":
    main()
