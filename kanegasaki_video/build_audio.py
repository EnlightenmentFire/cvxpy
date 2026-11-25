"""Narration + synthesized SFX (conch horn, hooves, matchlock volleys, taiko, rain, fire) + music bed (CC BY 4.0, Kevin MacLeod) -> mix.
Outputs (48 kHz float): /tmp/claude-0/work/audio/{voice,sfx,music,mix_music,mix_nomusic}.wav
Music sits ~22 dB under the voice while speaking (spec -20..-24), lifts ~4 dB in pauses.
"""
import os, sys, json, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
SR = 48000; WORK = "/tmp/claude-0/work"; OUT = f"{WORK}/audio"; os.makedirs(OUT, exist_ok=True)
TL = json.load(open(f"{WORK}/timeline.json")); TOTAL = TL["total"]; N = int(TOTAL * SR) + SR
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from script_data import S
ORDER = [l for s in S for l in s["lines"]]
V = {}
for i, l in enumerate(ORDER):
    if l.get("v"):
        d = dict(id=l["id"], **TL["lines"][l["id"]]); d["nx"] = TL["lines"][ORDER[i + 1]["id"]]["t0"] if i + 1 < len(ORDER) else TOTAL; V[l["v"]] = d
SCN = {s["id"]: s for s in TL["scenes"]}
rng = np.random.default_rng(11)

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def taiko(big=1.0):
    n = int(2.6 * SR); t = np.arange(n) / SR
    f = 52 + 70 * np.exp(-t / 0.05); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(n, 0.002, 0.6) + 0.45 * np.sin(ph * 1.52) * env(n, 0.002, 0.22)
    skin = bp(rng.standard_normal(n), 150, 1200) * env(n, 0.001, 0.05) * 0.8
    room = lp(rng.standard_normal(n), 260) * env(n, 0.03, 1.0) * 0.08
    return (body + skin + room) * big
def conch(dur=2.6, f0=233.0):
    n = int(dur * SR); t = np.arange(n) / SR
    bend = f0 * (0.86 + 0.14 * np.minimum(1, t / 0.35)) * (1 + 0.008 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.8))
    ph = 2 * np.pi * np.cumsum(bend) / SR
    x = sum(np.sin(k * ph) * (1 / k ** 1.3) for k in range(1, 12))
    x = bp(x, 180, 2600) + 0.6 * bp(x, 500, 900)                 # horn formant
    breath = bp(rng.standard_normal(n), 300, 3000) * 0.08
    a = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.7)
    y = (x / np.abs(x).max() + breath) * a
    # cheap hall: decaying echoes
    out = y.copy()
    for d, g in [(0.09, 0.35), (0.17, 0.25), (0.29, 0.18), (0.43, 0.12)]:
        k = int(d * SR); out[k:] += y[:-k] * g
    return out / np.abs(out).max() * 0.55
def hoof(g=1.0, cut=1800):
    n = int(0.12 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (110 + 60 * np.exp(-t / 0.01)) * t) * env(n, 0.001, 0.03) + lp(rng.standard_normal(n), cut) * env(n, 0.0005, 0.012) * 0.9
    return x * g
def gallop(dur=3.0, recede=True, stride=0.40, g=1.0):
    n = int(dur * SR); out = np.zeros(n + SR)
    for s0 in np.arange(0, dur, stride):
        p = s0 / dur; gg = g * ((1 - 0.92 * p) if recede else 1.0); cut = 2500 * (1 - 0.7 * p) + 300 if recede else 2200
        for k, dt in enumerate([0, 0.07, 0.14]):
            h = hoof(gg * rng.uniform(0.7, 1.0), cut); i = max(0, int((s0 + dt + rng.uniform(-0.01, 0.01)) * SR)); out[i:i + len(h)] += h
    return lp(out, 3500)
def crack():
    n = int(1.2 * SR); t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 700, 7000) * env(n, 0.0004, 0.018) * 1.4
    x += np.sin(2 * np.pi * (70 + 80 * np.exp(-t / 0.02)) * t) * env(n, 0.001, 0.12) * 0.9
    x += lp(rng.standard_normal(n), 900) * env(n, 0.01, 0.45) * 0.22        # roll-off / tail
    return x
def volley(k=7, spread=0.32):
    out = np.zeros(int(2.0 * SR))
    for i in range(k):
        c = crack(); o = int((i / max(1, k - 1) * spread + rng.uniform(0, 0.03)) * SR); out[o:o + len(c)] += c[:len(out) - o] * rng.uniform(0.6, 1.0)
    return out / np.abs(out).max() * 0.9
def rain_bed(n, level=0.05):
    x = hp(rng.standard_normal(n), 1500) * 0.5 + bp(rng.standard_normal(n), 300, 1200) * 0.3
    drops = np.zeros(n); idx = rng.integers(0, n, n // 300); drops[idx] = rng.uniform(-1, 1, len(idx)); x += bp(drops, 2000, 8000) * 2
    return x * level
def crackle(n, level=0.1):
    x = np.zeros(n); idx = rng.integers(0, n, n // 900); x[idx] = rng.uniform(-1, 1, len(idx))
    return (bp(x, 800, 6000) * 3 + lp(rng.standard_normal(n), 400) * 0.25) * level
def wind(n, level=0.05):
    t = np.arange(n) / SR; x = lp(rng.standard_normal(n), 500); am = 0.6 + 0.4 * np.sin(2 * np.pi * t / 7.3) * np.sin(2 * np.pi * t / 3.1 + 1)
    return hp(x * am, 80) * level
def shouts(n, level=0.05):
    out = np.zeros(n); t = np.arange(n) / SR
    for k in range(16):
        f = rng.uniform(130, 300); vib = 1 + 0.03 * np.sin(2 * np.pi * rng.uniform(4, 7) * t)
        v = np.sin(2 * np.pi * np.cumsum(f * vib) / SR); v = bp(np.sign(v) * np.abs(v) ** 0.5, 300, 2500)
        out += v * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.1, 0.4) * t + rng.uniform(0, 6))) ** 3
    return out / np.abs(out).max() * level
def whoosh(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        c = 300 + 2500 * np.sin(np.pi * i / n); out[i:i + blk] = bp(x[i:i + blk], c * 0.6, c * 1.4)
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5
def boom():
    n = int(3.0 * SR); t = np.arange(n) / SR; f = 38 + 30 * np.exp(-t / 0.15)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.01, 0.9) + lp(rng.standard_normal(n), 200) * env(n, 0.02, 0.5) * 0.2) * 0.7

sfx = np.zeros(N)
def put(x, at, g=1.0):
    i = int(max(0, at) * SR); j = min(N, i + len(x))
    if i < N: sfx[i:j] += x[:j - i] * g
def span(a, b): return int((b - a) * SR)

# ---- opening hook (frame 0): conch horn + galloping hooves near->far, a matchlock volley, then taiko
put(conch(2.4), 0.0, 1.0)
put(gallop(2.6, True, 0.36, 1.3), 0.0, 0.9)
put(volley(9, 0.28), 1.05, 1.0)
put(taiko(1.3), 1.45, 1.0); put(taiko(0.8), 2.35, 0.6); put(taiko(0.6), 3.25, 0.4)
put(wind(span(0, 12), 0.05), 0.0); put(crackle(span(0, 10), 0.05), 0.0)
# ---- chapter cards: taiko + whoosh
for sc in TL["scenes"][1:]: put(taiko(1.0), sc["t0"] + 0.1, 0.8); put(whoosh(1.0), sc["t0"] - 0.6, 0.18)
# ---- quote cards: low boom
for l in ORDER:
    if l.get("q"): put(boom(), TL["lines"][l["id"]]["t0"] - 0.05, 0.3)
# ---- s0 beats
put(taiko(0.7), V["tezutsu"]["t0"] + 1.4, 0.5); put(taiko(0.7), V["tezutsu"]["t0"] + 3.4, 0.5)
for k, r0 in enumerate([V["report1"]["t0"] - 0.2, V["reports"]["t0"] - 0.1, V["reports"]["t0"] + 1.1, V["reports"]["t0"] + 2.2]):
    put(gallop(1.8, False, 0.34, 0.7), r0 + 0.1, 0.7 - k * 0.08)
put(crackle(span(V["report1"]["t0"], V["front_back"]["t0"]), 0.06), V["report1"]["t0"])
put(taiko(1.2), V["turn"]["t0"] + 0.25, 0.9); put(whoosh(1.0), V["turn"]["t0"] - 0.2, 0.25)
put(taiko(0.9), V["q3"]["t0"], 0.4)
# ---- s1 / s2
put(taiko(1.0), V["choose2"]["t0"], 0.7)
put(boom(), V["pincer2"]["t0"], 0.4); put(taiko(0.8), V["pincer2"]["t0"] + 1.0, 0.5)
put(crackle(span(SCN["s2"]["t0"], V["threshold"]["t0"]), 0.05), SCN["s2"]["t0"])
put(taiko(1.2), V["decide"]["t0"], 0.9)
# ---- s3 climax
put(wind(span(V["rout"]["t0"], V["buytime"]["t0"]), 0.04), V["rout"]["t0"])
put(taiko(1.2), V["shingari"]["t0"], 0.9)
put(rain_bed(span(V["castle"]["t0"], V["caveat"]["t0"] + 3), 0.05), V["castle"]["t0"])
g0 = V["guns"]["t0"]; ca = V["counter"]["t0"]; vols = []
v = g0 + 1.6
while v < V["counter"]["nx"] - 0.5:
    if not (ca + 1.2 < v < ca + 3.6): vols.append(v)
    v += 1.45
for k, v in enumerate(vols): put(volley(7, 0.30), v, 0.95)
put(shouts(span(0, 3.0), 0.06), ca + 1.5); put(gallop(1.2, False, 0.3, 0.4), ca + 1.6, 0.5)
for k, at in enumerate(np.arange(V["leapfrog"]["t0"] + 1, V["leapfrog"]["nx"], 2.6)): put(volley(4, 0.15), at, 0.35)
put(crackle(span(V["fires"]["t0"], V["caveat"]["nx"]), 0.09), V["fires"]["t0"])
put(wind(span(V["alone"]["t0"], V["where"]["t0"] + 2), 0.06), V["alone"]["t0"])
put(gallop(6.0, True, 0.42, 0.5), V["kyoto"]["t0"] + 1.0, 0.6)
put(taiko(1.0), V["anegawa"]["t0"] + 2.5, 0.7); put(volley(6, 0.3), V["anegawa"]["t0"] + 2.3, 0.4)
# ---- s4-s6
for key in ["c1b", "c2b", "c3", "c4", "c5b"]: put(taiko(0.6), V[key]["t0"] + (V[key]["t1"] - V[key]["t0"]) * 0.5, 0.35)
put(taiko(0.9), V["irony"]["t0"], 0.5)
put(wind(span(SCN["s6"]["t0"], V["hideyoshi_later"]["t0"]), 0.035), SCN["s6"]["t0"])
put(taiko(1.2), V["work"]["t0"], 0.6)
put(conch(2.6, 220), V["next2"]["t1"] + 0.3, 0.5)

# ---- voice track
voice = np.zeros(N)
for lid, l in TL["lines"].items():
    p = f"{WORK}/tts/proc/{lid}.wav"
    if os.path.exists(p):
        x, sr = sf.read(p); i = int(l["t0"] * SR); voice[i:i + len(x)] += x[:N - i]

# ---- music bed (CC BY 4.0, Kevin MacLeod)
MUS = f"{WORK}/music"
PLAN = [  # (file, offset in track, start time, fade-in)
    ("Asian Drums.mp3", 0.0, 0.0, 0.05),
    ("Ishikari Lore.mp3", 0.0, SCN["s1"]["t0"] - 2, 3.0),
    ("The Chamber.mp3", 20.0, SCN["s2"]["t0"] - 2, 3.0),
    ("Impact Prelude.mp3", 0.0, SCN["s3"]["t0"] - 2, 3.0),
    ("Five Armies.mp3", 0.0, V["castle"]["t0"] - 3, 3.0),
    (None, 0, V["alone"]["t0"] + 0.6, 0.6),                   # silence beat: battle music stops
    ("Lightless Dawn.mp3", 160.0, V["where"]["t0"] - 0.5, 2.5),
    ("Eastern Thought.mp3", 20.0, SCN["s4"]["t0"] - 2, 3.0),
    ("Ascending the Vale.mp3", 0.0, SCN["s5"]["t0"] - 2, 3.0),
    ("Long Road Ahead.mp3", 44.0, SCN["s6"]["t0"] - 2, 3.0),
]
def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
music = np.zeros(N)
for k, (f, off, at, fi) in enumerate(PLAN):
    if f is None: continue
    nxt = PLAN[k + 1] if k + 1 < len(PLAN) else None
    xf = nxt[3] if nxt else 3.0
    end = (nxt[2] + (xf if nxt[0] else 0)) if nxt else TOTAL
    x = load(f"{MUS}/{f}")[int(off * SR):]
    L = int((end - at) * SR)
    if len(x) < L:  # loop with crossfade
        c = int(2 * SR); y = x.copy()
        while len(y) < L:
            r = np.linspace(0, 1, c); y = np.concatenate([y[:-c], y[-c:] * (1 - r) + x[:c] * r, x[c:]])
        x = y
    x = x[:L].copy()
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9; x /= rms * 10
    fiN = int(fi * SR); x[:fiN] *= np.linspace(0, 1, fiN) ** 0.7
    fo = int((xf if nxt else 3.0) * SR); fo = min(fo, len(x)); x[-fo:] *= np.linspace(1, 0, fo) ** 0.7
    i = int(at * SR); music[i:i + L] += x[:N - i]

def rms_env(x, win=0.05):
    n = int(win * SR); m = len(x) // n; e = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)); return np.repeat(e, n)
ve = rms_env(voice); ve = np.pad(ve, (0, N - len(ve)))
speaking = (ve > 10 ** (-40 / 20)).astype(float)
k = int(0.35 * SR); cs = np.concatenate([[0], np.cumsum(speaking)]); idx = np.arange(N); lo = np.clip(idx - k // 2, 0, N); hi = np.clip(idx + k // 2, 0, N)
sp = (cs[hi] - cs[lo]) / k > 0.02; del cs, idx, lo, hi
g = np.where(sp, 1.0, 0.0); blk = 480; gb = g[::blk]; ob = np.zeros_like(gb); y = 0
for i, v in enumerate(gb):
    c = np.exp(-blk / (0.08 * SR)) if v > y else np.exp(-blk / (0.6 * SR)); y = c * y + (1 - c) * v; ob[i] = y
duck = np.repeat(ob, blk)[:N]
import pyloudnorm as pyln
meter = pyln.Meter(SR)
def lufs(x): return meter.integrated_loudness(x)
VL = lufs(voice) if np.abs(voice).max() > 0 else -24.0
REL, LIFT = float(os.environ.get("MUSIC_REL", -22.0)), 4.0
ML = lufs(music)
music_g = music * 10 ** ((VL + REL - ML) / 20) * 10 ** ((LIFT * (1 - duck)) / 20)
music_g[:int(3.0 * SR)] *= 1.6     # hook: drums a little stronger under the opening
sfx_g = sfx * 10 ** ((VL - 13 - lufs(sfx[:int(TOTAL * SR)])) / 20)
for name, x in [("voice", voice), ("sfx", sfx_g), ("music", music_g), ("mix_music", voice + sfx_g + music_g), ("mix_nomusic", voice + sfx_g)]:
    sf.write(f"{OUT}/{name}.wav", x[:int(TOTAL * SR)].astype(np.float32), SR, subtype="FLOAT")
m = duck[:len(voice)] > 0.9
print(f"voice {VL:.1f} LUFS; music while speaking ≈ {lufs(music_g[m][:SR*600]) - lufs(voice[m][:SR*600]):.1f} dB rel voice; sfx {lufs(sfx_g):.1f} LUFS; total {TOTAL:.1f}s")
