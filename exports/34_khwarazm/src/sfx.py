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

def main():
    tl = json.load(open(f"{W}/timeline.json")); T = tl["total"]
    out = np.zeros(int(T * SR) + SR * 4)
    def put(x, t, g=1.0):
        i = int(t * SR); out[i:i + len(x)] += x[:max(0, len(out) - i)] * g
    B = tl["beats"]
    def beats(v): return [b for b in B if b["v"] == v]
    # opening sound hook: drum + horn at frame 0, hooves under the storm
    put(drum(1.0), 0.0, 0.9); put(drum(0.8), 0.62, 0.7); put(drum(0.9), 1.24, 0.8)
    put(horn(2.8), 0.05, 0.55)
    for b in beats("storm"): put(fade(hooves(b["end"] - b["start"]) * 0.5 + wind(b["end"] - b["start"]) * 0.4, 0.05, 1.0), b["start"], 0.8)
    for b in beats("caravan") + beats("gate"):
        d = b["end"] - b["start"]; put(fade(wind(d, 150, 600) * 0.4), b["start"], 0.5)
        for k in range(int(d / 1.3)): put(bell(rng.choice([740, 880, 988])), b["start"] + 0.4 + k * 1.3, 0.35)
    for b in beats("gate"):
        lid = "c04b"; t0 = next(l["t0"] for l in tl["lines"] if l["id"] == lid)
        put(thud(), t0 + 2.2, 0.8)
    for b in beats("envoy"): put(fade(hooves(b["end"] - b["start"], 1.6) * 0.35), b["start"], 0.6)
    for v in ["routes0", "route1", "route2", "route3", "route4b", "route4c", "desertflash", "chaseflash", "flight1", "caucasus", "muqali"]:
        for b in beats(v): put(whoosh(), b["start"] + 0.3, 0.5)
    for b in beats("route4c"): put(drum(1.0), b["start"] + 1.6, 0.7)
    for b in beats("desertflash"): put(drum(1.0), b["start"] + 3.2, 0.6)
    for b in beats("bukhara"): put(fade(wind(b["end"] - b["start"], 120, 500) * 0.3), b["start"], 0.5)
    for v in ["indusleap", "indusflash", "sunzi4"]:
        for b in beats(v): put(fade(water(b["end"] - b["start"])), b["start"], 0.45 if v != "sunzi4" else 0.25)
    for b in beats("indusleap"):
        t7 = next(l["t0"] for l in tl["lines"] if l["id"] == "h07")
        put(hooves(1.6, 2.6) * 0.5, t7 + 2.5, 0.7); put(splash(), t7 + 2.5 + 4.5 * 0.75, 0.6)
    for b in beats("indusflash"): put(splash(), b["start"] + (b["end"] - b["start"]) * 0.9 / 1.05, 0.5)
    for v in ["athir", "end"]:
        for b in beats(v): put(fade(wind(b["end"] - b["start"], 100, 400) * 0.25, 1.0, 2.0), b["start"], 0.4)
    out = out[:int(T * SR)]
    pk = np.abs(out).max(); out = out / pk * 0.7
    sf.write(f"{W}/stems/sfx.wav", np.stack([out, out], 1).astype(np.float32), SR, subtype="FLOAT")
    print("sfx ok", len(out) / SR)
if __name__ == "__main__":
    main()
