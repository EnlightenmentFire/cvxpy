"""Narration track + synthesized SFX + music bed (CC BY, Kevin MacLeod) -> mix.
Outputs (48 kHz): /tmp/claude-0/work/audio/{voice,sfx,music,mix_music,mix_nomusic}.wav
Music sits ~20-24 dB under the voice while speaking, lifts ~4 dB in pauses.
"""
import os, json, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt
SR = 48000; WORK = "/tmp/claude-0/work"; OUT = f"{WORK}/audio"; os.makedirs(OUT, exist_ok=True)
TL = json.load(open(f"{WORK}/timeline.json")); TOTAL = TL["total"]; N = int(TOTAL * SR) + SR
HERE = os.path.dirname(os.path.abspath(__file__))
import sys; sys.path.insert(0, HERE)
from script_data import S
V = {}; [V.__setitem__(l["v"], dict(id=l["id"], **TL["lines"][l["id"]])) for s in S for l in s["lines"] if l.get("v")]
rng = np.random.default_rng(7)

def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "bandpass", fs=SR, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, "lowpass", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "highpass", fs=SR, output="sos"), x)
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def drum(big=1.0):
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = 48 + 60 * np.exp(-t / 0.06); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(n, 0.002, 0.55) + 0.5 * np.sin(ph * 1.5) * env(n, 0.002, 0.25)
    skin = bp(rng.standard_normal(n), 120, 900) * env(n, 0.001, 0.07) * 0.7
    room = lp(rng.standard_normal(n), 300) * env(n, 0.03, 0.9) * 0.08
    return (body + skin + room) * big
def splash(dur=0.5):
    n = int(dur * SR); x = bp(rng.standard_normal(n), 400, 5000) * env(n, 0.01, dur / 4)
    x += lp(rng.standard_normal(n), 250) * env(n, 0.005, 0.08) * 1.2   # chunk of blade entering
    return x * 0.6
def oars(count=40, spread=0.06):
    out = np.zeros(int(0.9 * SR))
    for _ in range(count):
        s = splash(0.55); o = int(abs(rng.normal(0, spread)) * SR); out[o:o + len(s)] += s[:len(out) - o] * rng.uniform(0.3, 1)
    return out / np.abs(out).max() * 0.9
def horn(dur=2.4, f0=146.8):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.8)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    x = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, 14))
    a = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.6)
    x = lp(x * a, 1800) + 0.3 * lp(x * a, 900); return x / np.abs(x).max() * 0.5
def boom():
    n = int(3.0 * SR); t = np.arange(n) / SR; f = 38 + 30 * np.exp(-t / 0.15)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.01, 0.9) + lp(rng.standard_normal(n), 200) * env(n, 0.02, 0.5) * 0.2) * 0.7
def crash():
    n = int(1.4 * SR); x = bp(rng.standard_normal(n), 200, 3500) * env(n, 0.002, 0.12)
    for k in range(6):
        o = int(rng.uniform(0, 0.25) * SR); m = int(0.25 * SR); x[o:o + m] += bp(rng.standard_normal(m), 600, 4000) * env(m, 0.001, 0.03) * rng.uniform(0.3, 0.8)
    t = np.arange(n) / SR; x += np.sin(2 * np.pi * 70 * t) * env(n, 0.002, 0.2) * 0.8
    return x * 0.7
def whoosh(dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        c = 300 + 2500 * np.sin(np.pi * i / n); out[i:i + blk] = bp(x[i:i + blk], c * 0.6, c * 1.4)
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5
def waves(n, level=0.06):
    x = lp(rng.standard_normal(n), 600); t = np.arange(n) / SR
    am = 0.55 + 0.45 * np.sin(2 * np.pi * t / 6.5) * np.sin(2 * np.pi * t / 2.9 + 1)
    return hp(x * am, 60) * level
def crackle(n, level=0.1):
    x = np.zeros(n); idx = rng.integers(0, n, n // 900); x[idx] = rng.uniform(-1, 1, len(idx))
    return (bp(x, 800, 6000) * 3 + lp(rng.standard_normal(n), 400) * 0.25) * level
def shouts(n, level=0.05):
    out = np.zeros(n); t = np.arange(n) / SR
    for k in range(14):
        f = rng.uniform(140, 320); vib = 1 + 0.03 * np.sin(2 * np.pi * rng.uniform(4, 7) * t)
        v = np.sin(2 * np.pi * np.cumsum(f * vib) / SR); v = bp(np.sign(v) * np.abs(v) ** 0.5, 300, 2500)
        out += v * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.1, 0.4) * t + rng.uniform(0, 6))) ** 3
    return out / np.abs(out).max() * level

sfx = np.zeros(N)
def put(x, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(x));
    if i < N: sfx[i:j] += x[:j - i] * g

# ---- opening sound hook (frame 0): war drum + oars hitting water together, horn under the first line
put(drum(1.2), 0.0, 1.0); put(oars(48), 0.02, 0.9); put(whoosh(1.0), 0.0, 0.25)
for k, at in enumerate([1.45, 2.9, 4.35, 5.8, 7.25]): put(oars(36), at, 0.45 - k * 0.05); put(drum(0.5), at, 0.35 - k * 0.04)
put(horn(2.6, 146.8), 0.25, 0.16)
put(waves(int(14 * SR), 0.05), 0.0)
# ---- each chapter card: drum hit
for sc in TL["scenes"][1:]: put(drum(0.9), sc["t0"] + 0.1, 0.7); put(whoosh(1.0), sc["t0"] - 0.6, 0.18)
# ---- quote cards: low boom
for s in S:
    for l in s["lines"]:
        if l.get("q"): put(boom(), TL["lines"][l["id"]]["t0"] - 0.05, 0.35)
# ---- scene-specific
put(drum(0.8), V["numbers"]["t0"] + 0.3, 0.45); put(drum(0.6), V["twist"]["t0"], 0.6); put(whoosh(), V["letter"]["t0"] - 0.4, 0.25)
b = V["burn"]; put(crackle(int((b["t1"] - b["t0"] + 8) * SR), 0.08), b["t0"])
s4, s5 = TL["scenes"][4], TL["scenes"][5]
put(waves(int((s4["t1"] - s4["t0"]) * SR), 0.035), s4["t0"])
put(waves(int((s5["t1"] - s5["t0"]) * SR), 0.045), s5["t0"])
for at in np.arange(V["deploy"]["t0"], V["trireme"]["t0"], 1.5): put(oars(30), at, 0.22)
put(shouts(int(12 * SR), 0.05), V["cry0"]["t0"])
for key, n_cr in [("wave2", 3), ("broadside", 2), ("greek_strike", 3), ("hdt889", 4), ("push", 2), ("artemisia", 1), ("psy_kill", 2)]:
    l = V[key]
    for k in range(n_cr): put(crash(), l["t0"] + (l["t1"] - l["t0"]) * (0.15 + 0.8 * k / max(1, n_cr)), 0.35)
put(crash(), V["artemisia"]["t0"] + 4.6, 0.5)
put(shouts(int(10 * SR), 0.035), V["greek_strike"]["t0"])
put(drum(1.0), V["lesson"]["t0"] - 0.2, 0.5); put(drum(1.2), V["lesson"]["t1"] + 1.0, 0.6)

# ---- voice track
voice = np.zeros(N)
for lid, l in TL["lines"].items():
    p = f"{WORK}/tts/proc/{lid}.wav"
    if os.path.exists(p):
        x, sr = sf.read(p); i = int(l["t0"] * SR); voice[i:i + len(x)] += x[:N - i]

# ---- music bed
MUS = f"{WORK}/music"
PLAN = [  # (file, start_in_track, at_time, fade_in, crossfade_out_at_next)
    ("Achilles.mp3", 0.0, 0.0),
    ("Majestic Hills.mp3", 0.0, TL["scenes"][1]["t0"] - 6),
    ("The Chamber.mp3", 0.0, TL["scenes"][3]["t0"] - 2),
    ("Oppressive Gloom.mp3", 0.0, TL["scenes"][4]["t0"] - 2),
    ("Stoneworld Battle.mp3", 60.0, TL["scenes"][5]["t0"] - 2),
    ("Long Road Ahead.mp3", 0.0, TL["scenes"][6]["t0"] - 3),
]
def load(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
music = np.zeros(N); XF = 4.0
for k, (f, off, at) in enumerate(PLAN):
    x = load(f"{MUS}/{f}")[int(off * SR):]
    end = PLAN[k + 1][2] + XF if k + 1 < len(PLAN) else TOTAL
    L = min(len(x), int((end - at) * SR)); x = x[:L].copy()
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9; x /= rms * 10           # each track to the same RMS (-20 dBFS)
    fi = int((0.05 if k == 0 else XF) * SR); x[:fi] *= np.linspace(0, 1, fi) ** 0.7
    fo = int(XF * SR) if k + 1 < len(PLAN) else int(3.0 * SR); x[-fo:] *= np.linspace(1, 0, fo) ** 0.7
    i = int(at * SR); music[i:i + L] += x[:N - i]

# ducking: speech envelope -> music gain (dB relative): speaking -> DUCK, pauses -> DUCK + LIFT
def rms_env(x, win=0.05):
    n = int(win * SR); m = len(x) // n; e = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(1)); return np.repeat(e, n), n
ve, _ = rms_env(voice); ve = np.pad(ve, (0, N - len(ve)))
speaking = (ve > 10 ** (-40 / 20)).astype(float)
# hold + smooth (attack 80 ms, release 600 ms)
k = int(0.35 * SR); cs = np.concatenate([[0], np.cumsum(speaking)]); idx = np.arange(N); lo = np.clip(idx - k // 2, 0, N); hi = np.clip(idx + k // 2, 0, N); sp = (cs[hi] - cs[lo]) / k > 0.02; del cs, idx, lo, hi
g = np.where(sp, 1.0, 0.0); out = np.zeros_like(g); a_up, a_dn = np.exp(-1 / (0.08 * SR)), np.exp(-1 / (0.6 * SR))
# one-pole smoother in blocks (fast enough)
blk = 480; gb = g[::blk]; ob = np.zeros_like(gb); y = 0
for i, v in enumerate(gb):
    c = np.exp(-blk / (0.08 * SR)) if v > y else np.exp(-blk / (0.6 * SR)); y = c * y + (1 - c) * v; ob[i] = y
duck = np.repeat(ob, blk)[:N]
def lufs(x):
    import pyloudnorm as pyln; return pyln.Meter(SR).integrated_loudness(x)
VL = lufs(voice)
REL_SPEAK, LIFT = float(os.environ.get("MUSIC_REL", -22.0)), 4.0   # music below voice while speaking
ML = lufs(music)
base = 10 ** ((VL + REL_SPEAK - ML) / 20)
music_g = music * base * 10 ** ((LIFT * (1 - duck)) / 20)
# hook: keep the very first seconds a bit stronger under the drum
music_g[:int(1.0 * SR)] *= 1.4
sfx_g = sfx * 10 ** ((VL - 14 - lufs(sfx[:int(TOTAL * SR)] + 1e-12)) / 20) if np.abs(sfx).max() > 0 else sfx
for name, x in [("voice", voice), ("sfx", sfx_g), ("music", music_g), ("mix_music", voice + sfx_g + music_g), ("mix_nomusic", voice + sfx_g)]:
    sf.write(f"{OUT}/{name}.wav", x[:int(TOTAL * SR)].astype(np.float32), SR, subtype="FLOAT")
sp_mask = duck[:len(voice)] > 0.9
print(f"voice {VL:.1f} LUFS; music while speaking ≈ {lufs(music_g[sp_mask][:SR*600]) - lufs(voice[sp_mask][:SR*600]):.1f} dB rel voice; sfx {lufs(sfx_g):.1f} LUFS; total {TOTAL:.1f}s")
