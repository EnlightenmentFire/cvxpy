# -*- coding: utf-8 -*-
"""合成配乐/音效并与旁白混音。全部声音为程序合成（无第三方素材）。
usage: python mix.py [--no-voice]   -> out/audio_mix.wav (+ stems)"""
import json, os, sys, wave
import numpy as np
from scipy import signal
import soundfile as sf

SR = 48000
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TL = json.load(open(os.path.join(ROOT, "audio", "timeline.json"), encoding="utf8"))
TOTAL = TL["total"]; N = int(TOTAL * SR) + SR
rs = np.random.RandomState(318)
SEG = {s["id"]: s for s in TL["segs"]}
LN = {}
for l in TL["lines"]: LN.setdefault(l["seg"], []).append(l)
def ln(seg, i): return LN[seg][i]

NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
def hz(name):
    n, o = name[:-1], int(name[-1]); return 440.0 * 2 ** ((NOTE[n] - 9) / 12 + (o - 4))
def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos"); return signal.sosfilt(sos, x)
def lp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x)
def hp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x)
def smooth(x, sec):
    k = max(1, int(sec * SR)); h = k // 2
    c = np.cumsum(np.concatenate([np.zeros(h + 1), x, np.zeros(k - h)]))
    return (c[k:k + len(x)] - c[:len(x)]) / k
def fade(n, a, r):
    e = np.ones(n); na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na: e[:na] = 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    if nr: e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e

class Track:
    def __init__(self): self.b = np.zeros((N, 2))
    def add(self, x, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= N or i + len(x) <= 0: return
        if i < 0: x = x[-i:]; i = 0
        x = x[: N - i]
        if x.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            self.b[i:i + len(x), 0] += x * gain * l * 1.414; self.b[i:i + len(x), 1] += x * gain * r * 1.414
        else: self.b[i:i + len(x)] += x * gain

def reverb(x, secs=2.8, wet=0.35, seed=1, damp=3500):
    r = np.random.RandomState(seed); n = int(secs * SR); t = np.arange(n) / SR
    ir = np.stack([lp(r.randn(n), damp) * np.exp(-t * 6.9 / secs), lp(r.randn(n), damp) * np.exp(-t * 6.9 / secs)], 1)
    ir[: int(.012 * SR)] *= 0; ir /= np.sqrt((ir ** 2).sum(0)).max()
    if x.ndim == 1: x = np.stack([x, x], 1)
    w = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in (0, 1)], 1)
    return x * (1 - wet * .5) + w * wet

# ── instruments ──
def pipe(notes, kind="xiao", glide=0.09, seed=0):
    """notes: [(name|None, dur)] legato phrase; returns mono"""
    r = np.random.RandomState(100 + seed); tot = sum(d for _, d in notes); n = int(tot * SR); t = np.arange(n) / SR
    f = np.zeros(n); amp = np.zeros(n); pos = 0.0; last = None
    for name, d in notes:
        i0, i1 = int(pos * SR), int((pos + d) * SR)
        if name is None: f[i0:i1] = last or 440.0
        else:
            fr = hz(name); f[i0:i1] = fr; e = np.ones(i1 - i0)
            a = int(min(.16, d * .3) * SR); rl = int(min(.28, d * .35) * SR)
            e[:a] = .55 + .45 * np.sin(.5 * np.pi * np.arange(a) / a); e[-rl:] *= .62 + .38 * np.cos(.5 * np.pi * np.arange(rl) / rl)
            sw = 1 + .22 * np.sin(np.pi * np.arange(i1 - i0) / (i1 - i0)) ** 2
            amp[i0:i1] = e * sw; last = fr
        pos += d
    f = smooth(f, glide if kind != "hujia" else glide * 1.9); amp = smooth(amp, .05)
    # phrase edges
    first = next(i for i, (nm, _) in enumerate(notes) if nm); amp *= fade(n, .22, .6)
    vib_rate = 4.7 if kind != "hujia" else 5.4; depth = (.006 if kind == "xiao" else .004 if kind == "xun" else .011)
    venv = np.clip(smooth(amp, .5), 0, 1) ** 2
    vib = np.sin(2 * np.pi * vib_rate * t + r.rand() * 6) * depth * venv * (1 + .3 * np.sin(2 * np.pi * .23 * t))
    drift = .003 * lp(r.randn(n), 2.0) * 30
    ph = 2 * np.pi * np.cumsum(f * (1 + vib + drift)) / SR
    noise = r.randn(n)
    if kind == "xiao":
        tone = np.sin(ph) + .32 * np.sin(2 * ph + .3) + .1 * np.sin(3 * ph) + .035 * np.sin(4 * ph)
        br = bp(noise, 500, 5000) * .05 + bp(noise, 1800, 7000) * .02
    elif kind == "xun":
        tone = np.sin(ph) + .13 * np.sin(2 * ph) + .035 * np.sin(3 * ph)
        br = bp(noise, 250, 1800) * .11 + bp(noise, 2000, 6000) * .015
    else:  # hujia: reedy, nasal
        tone = sum(np.sin(k * ph + .2 * k) / k ** 1.05 for k in range(1, 13))
        tone = .55 * bp(tone, 650, 1500) + .3 * bp(tone, 1700, 3000) + .28 * lp(tone, 700)
        br = bp(noise, 900, 4500) * .035
    flut = 1 + .05 * lp(r.randn(n), 9.0) * 12
    x = (tone * flut + br * (1.2 + 2 * np.abs(np.gradient(amp)) * SR / 40)) * amp
    return x / (np.abs(x).max() + 1e-9)

def pad(chord, dur, attack=3.0, release=4.0, bright=520, seed=0):
    r = np.random.RandomState(200 + seed); n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for name in chord:
        f0 = hz(name)
        for d in (-.07, .0, .06):
            f = f0 * 2 ** (d / 12 * .25); ph0 = r.rand() * 6.28
            x = sum(np.sin(2 * np.pi * f * k * t + ph0 * k) / k for k in range(1, 9))
            x *= 1 + .12 * np.sin(2 * np.pi * (.11 + .07 * r.rand()) * t + r.rand() * 6)
            p = r.rand(); out[:, 0] += x * np.cos(p * np.pi / 2); out[:, 1] += x * np.sin(p * np.pi / 2)
    out = np.stack([lp(out[:, 0], bright, 2), lp(out[:, 1], bright, 2)], 1)
    out += .012 * np.stack([bp(r.randn(n), 300, 1400), bp(r.randn(n), 300, 1400)], 1) * np.abs(out).max()   # bow noise
    out *= fade(n, attack, release)[:, None]
    return out / (np.abs(out).max() + 1e-9)

def drum(f0=58, dur=2.2, seed=0):
    r = np.random.RandomState(300 + seed); n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + .9 * np.exp(-t * 26)); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    x += .5 * np.sin(2 * np.pi * np.cumsum(f * 1.52) / SR) * np.exp(-t * 6)
    x += .35 * lp(r.randn(n), 900) * np.exp(-t * 38)
    return x / np.abs(x).max()

def chime(f0=587.3, dur=6.0, seed=0):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for ratio, a, dec in [(1, 1, .7), (2.76, .45, 1.3), (5.4, .22, 2.4), (8.93, .1, 4), (.5, .25, .5)]:
        x += a * np.sin(2 * np.pi * f0 * ratio * t) * np.exp(-t * dec)
    x *= fade(n, .004, .5); return x / np.abs(x).max()

def wind(dur, seed=0, lo=250, hi=1100):
    r = np.random.RandomState(400 + seed); n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for c in (0, 1):
        w = r.randn(n); acc = np.zeros(n)
        for k, (cf, q) in enumerate([(lo, 1.2), ((lo * hi) ** .5, 1.6), (hi, 2.2)]):
            m = .5 + .5 * np.sin(2 * np.pi * (.05 + .04 * k) * t + r.rand() * 6) * np.sin(2 * np.pi * .017 * (k + 1) * t + r.rand() * 6)
            acc += bp(w, cf / (1 + .5 / q), cf * (1 + .5 / q)) * (.3 + m)
        gust = np.clip(lp(r.randn(n), .25) * 60 + .55, .15, 1.5)
        out[:, c] = acc * gust
    return out / (np.abs(out).max() + 1e-9)

def whoosh(dur=.4, f0=700, f1=3200, seed=0):
    r = np.random.RandomState(500 + seed); n = int(dur * SR); t = np.arange(n) / n; x = r.randn(n); out = np.zeros(n); blk = 256
    for i in range(0, n, blk):
        u = i / n; cf = f0 * (f1 / f0) ** u; seg = x[max(0, i - blk):i + blk]
        y = bp(seg, cf * .7, min(cf * 1.4, SR / 2 - 100)); out[i:i + blk] = y[-min(blk, n - i) if i else None:][: min(blk, n - i)] if i else y[: min(blk, n - i)]
    out *= np.sin(np.pi * t) ** 1.5; return out / (np.abs(out).max() + 1e-9)

def rooster(seed=0):
    """stylised distant cock-crow: four syllables, rising then falling"""
    r = np.random.RandomState(600 + seed)
    syl = [(.00, .17, 520, 690, .7), (.23, .16, 640, 820, .8), (.45, .30, 760, 1010, 1.0), (.82, 1.05, 1010, 640, 1.0)]
    n = int(2.1 * SR); t = np.arange(n) / SR; f = np.full(n, 500.0); amp = np.zeros(n)
    for s, d, a, b, g in syl:
        i0, i1 = int(s * SR), int((s + d) * SR); u = np.linspace(0, 1, i1 - i0)
        if d > .6: fr = np.where(u < .28, a + (1080 - a) * (u / .28), 1080 - (1080 - b) * np.clip((u - .28) / .72, 0, 1) ** 1.6)
        else: fr = a + (b - a) * u ** .7
        f[i0:i1] = fr; amp[i0:i1] = g * np.sin(np.pi * u) ** (.35 if d > .6 else .6) * (1 - .5 * u * (d > .6))
    f = smooth(f, .012); amp = smooth(amp, .012)
    f *= 1 + .02 * np.sin(2 * np.pi * 31 * t) + .012 * lp(r.randn(n), 60) * 8
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = sum(np.sin(k * ph) / k ** .8 for k in range(1, 15))
    src *= 1 + .35 * np.sign(np.sin(2 * np.pi * 72 * t)) * (amp > .1)      # rasp
    x = bp(src, 900, 1900) + .8 * bp(src, 2300, 3800) + .15 * src
    x = x * amp + .04 * bp(r.randn(n), 1500, 5000) * amp
    return x / np.abs(x).max()

def whistle(dur=2.6, seed=0):
    r = np.random.RandomState(700 + seed); n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    f = 1150 * (1 + .32 * np.sin(np.pi * u) ** 1.2) * (1 + .006 * np.sin(2 * np.pi * 5.2 * t) * u)
    ph = 2 * np.pi * np.cumsum(f) / SR; x = np.sin(ph) + .06 * np.sin(2 * ph) + .25 * bp(r.randn(n), 900, 2200)
    return x * fade(n, .3, 1.2) * (.6 + .4 * np.sin(np.pi * u))

# ── score ──
music, solo, sfx, amb = Track(), Track(), Track(), Track()
def chordseq(t0, t1, chords, gain, bright=520, seed=0):
    """spread chords evenly over [t0,t1] with overlaps"""
    d = (t1 - t0) / len(chords)
    for i, ch in enumerate(chords):
        music.add(pad(ch, d + 5.0, attack=3.2, release=4.6, bright=bright, seed=seed + i), t0 + i * d - 1.5, gain)
Dm, Bb, Gm, F, Am, Dlow, C = ["D2", "A2", "D3", "F3"], ["A#1", "F2", "A#2", "D3"], ["G1", "D2", "G2", "A#2"], ["F2", "C3", "F3", "A3"], ["A1", "E2", "A2", "C3"], ["D1", "D2", "A2"], ["C2", "G2", "C3", "E3"]
S = SEG
# pads
chordseq(2.5, S["s01"]["e"], [Dm, Bb, Dm, Gm], .50, 480, 1)
chordseq(S["s02"]["s"], S["s02"]["e"], [F, Dm], .46, 620, 10)
chordseq(S["s03"]["s"], ln("s03", 5)["s"], [Dm, Gm], .50, 470, 20)
chordseq(ln("s03", 5)["s"], ln("s03", 8)["s"], [Bb, F], .50, 600, 24)
chordseq(ln("s03", 8)["s"], S["s03"]["e"], [Dm], .52, 450, 28)
chordseq(S["s04"]["s"], S["s04"]["e"], [Dlow, Dlow], .30, 380, 30)
chordseq(S["s05"]["s"], ln("s05", 6)["s"], [Dm, Gm, Am], .46, 470, 40)
chordseq(ln("s05", 6)["s"], S["s05"]["e"], [Dlow], .26, 330, 45)
chordseq(S["s06"]["s"], S["s06"]["e"], [Gm, Dm, Bb, Dm], .50, 470, 50)
chordseq(S["s07"]["s"], S["s07"]["e"], [Dm, Am, Gm, Dlow], .54, 500, 60)
chordseq(S["s08"]["s"], S["s08"]["e"], [Bb, F, Gm, Dm], .48, 520, 70)
chordseq(S["s09"]["s"], ln("s09", 1)["e"], [Dm], .36, 420, 80)
chordseq(ln("s09", 5)["s"], S["s09"]["e"], [Dlow, Dlow], .16, 260, 84)        # barely there
chordseq(S["s11"]["s"], S["s11"]["e"], [Dlow, Gm], .22, 330, 90)
chordseq(ln("s12", 3)["s"], S["s12"]["e"] - 1, [Dm, Bb, Gm, Dm], .42, 470, 100)

MOT = [("A4", 1.3), ("C5", .55), ("D5", 2.0), ("C5", .5), ("A4", 1.5), ("G4", .6), ("F4", .7), ("D4", 2.8)]
MOT2 = [("D4", 1.2), ("F4", .6), ("G4", 1.6), ("A4", .6), ("G4", .6), ("F4", 1.8), ("D4", 2.6)]
LOWX = [("D4", 2.2), ("C4", .8), ("A3", 2.6), (None, .6), ("A3", .9), ("C4", .9), ("D4", 3.2)]
HJ1 = [("A4", 1.5), ("D5", 2.0), ("C5", .45), ("D5", .45), ("F5", 2.2), ("D5", .7), ("C5", .8), ("A4", 2.6)]
HJ2 = [("G4", .9), ("A4", .6), ("C5", 1.9), ("A4", .6), ("G4", .7), ("F4", .5), ("G4", 1.4), ("D4", 3.2)]
def play(phrase, t, kind, gain, trk, pan=0.0, seed=0, wet=.42):
    x = reverb(pipe(phrase, kind, seed=seed), 3.2, wet, seed + 3); trk.add(x, t, gain * .5, 0) if False else trk.add(x, t, gain)
tT = ln("s01", 5)["e"] + .4
play(MOT, tT, "xiao", .75, solo, seed=1)                                         # title
play(MOT2, ln("s02", 0)["s"] + 1.0, "xiao", .34, music, seed=2)
play(LOWX, ln("s03", 1)["s"], "xun", .42, music, seed=3)
play([("F4", 1.4), ("A4", .7), ("C5", 2.2), ("A4", .8), ("G4", .8), ("F4", 2.6)], ln("s03", 6)["s"] - .3, "xiao", .36, music, seed=4)   # the warm moment
play(LOWX, ln("s03", 8)["s"] + 2.5, "xun", .40, music, seed=5)
# s04: whistle, then the hujia — solo in the gap
L = LN["s04"]; tw = L[0]["s"] + (L[0]["e"] - L[0]["s"]) * .62
sfx.add(reverb(whistle(2.8), 3.5, .55, 9), tw, .13)
play(HJ1, L[1]["s"] + .6, "hujia", .30, music, seed=6, wet=.5)
play(HJ1[4:] + HJ2, L[1]["e"] - .9, "hujia", .95, solo, seed=7, wet=.5)
play(HJ2, L[2]["s"] + 1.6, "hujia", .28, music, seed=8, wet=.55)
play(LOWX, ln("s05", 2)["s"] + 1, "xun", .34, music, seed=9)
play(LOWX[:3], ln("s06", 1)["s"], "xun", .40, music, seed=10)
play(MOT2, ln("s06", 7)["s"] + .6, "xiao", .40, music, seed=11)
play(MOT[:5], ln("s08", 1)["s"] + 2, "xiao", .34, music, seed=12)
play(LOWX, ln("s08", 5)["s"], "xun", .40, music, seed=13)
# s12: one pipe alone under the couplet
L = LN["s12"]
play([("D5", 2.4), ("C5", .6), ("A4", 2.2), ("G4", .7), ("A4", .7), ("F4", 1.2), ("D4", 3.4)], L[0]["e"] + .1, "xiao", .62, solo, seed=14, wet=.5)
play(MOT, L[5]["s"] + .4, "xiao", .44, music, seed=15)
play([("A4", 1.6), ("G4", .7), ("F4", .9), ("D4", 4.5)], L[7]["e"] + .5, "xiao", .7, solo, seed=16, wet=.55)

# ambience
amb.add(wind(S["s01"]["e"] + 2, 1), 0, .10)
amb.add(wind(ln("s03", 8)["s"] - ln("s03", 5)["s"] + 3, 2) * fade(int((ln("s03", 8)["s"] - ln("s03", 5)["s"] + 3) * SR), 2, 3)[:, None], ln("s03", 5)["s"] - 1, .16)
d = S["s04"]["e"] - S["s04"]["s"]; amb.add(wind(d, 3) * fade(int(d * SR), 2, 3)[:, None], S["s04"]["s"], .13)
t0 = ln("s09", 1)["s"]; d = S["s11"]["s"] - t0 + 2; amb.add(wind(d, 4, 180, 900) * fade(int(d * SR), 4, 4)[:, None], t0, .20)
t0 = ln("s12", 4)["e"]; d = TOTAL - t0; amb.add(wind(d, 5) * fade(int(d * SR), 3, 2.5)[:, None], t0, .14)

# sfx
rc = reverb(lp(rooster(), 4200), 2.6, .5, 4)
sfx.add(rc, 1.6, .16, 0); sfx.add(rc, ln("s01", 1)["s"] + .2, .12)
sfx.add(reverb(lp(rooster(1), 2600), 3.2, .7, 5), ln("s03", 6)["s"] + .6, .035)       # far, when the town comes back
L = LN["s01"]; t = L[3]["s"] + 1.2; k = 0
while t < L[5]["s"] - .6:
    sfx.add(reverb(whoosh(.36 + .1 * (k % 2), 600, 2600, k), 1.2, .3, k), t, .05, pan=(-.4 if k % 2 else .4)); t += 1.02 + .21 * (k % 3); k += 1
tS = L[5]["s"] - .15
sfx.add(reverb(whoosh(.5, 900, 5000, 50), 1.8, .4, 6), tS - .12, .16); sfx.add(reverb(drum(52), 2.5, .3, 7), tS + .05, .34)
L = LN["s05"]; d = L[3]["e"] - L[3]["s"]; sfx.add(reverb(drum(60), 2.2, .3, 8), L[3]["s"] + d * .85, .30)
sfx.add(reverb(chime(hz("D5")), 4, .6, 9), L[6]["s"] + (L[6]["e"] - L[6]["s"]) * .66, .10)
L = LN["s06"]; sfx.add(reverb(drum(50), 2.5, .35, 10), L[5]["s"] + (L[5]["e"] - L[5]["s"]) * .7, .2)
L = LN["s07"]
for i in range(6): sfx.add(drum(64, 1.2, i), L[3]["s"] + i * .42, .10 + .02 * i)
sfx.add(reverb(drum(46, 3.0), 3, .4, 11), L[3]["e"] - .1, .42)
sfx.add(reverb(chime(hz("A4")), 4, .6, 12), L[1]["s"] + (L[1]["e"] - L[1]["s"]) * .4, .09)
L = LN["s09"]; sfx.add(reverb(whoosh(.3, 500, 1800, 60), 1.2, .3, 13), L[1]["s"] + .3, .09); sfx.add(reverb(drum(55, 1.8), 2, .3, 14), L[1]["s"] + .55, .22)
sfx.add(reverb(drum(42, 3.2), 3, .4, 15), L[8]["s"] + (L[8]["e"] - L[8]["s"]) * .34, .26)
L = LN["s10"]; sfx.add(reverb(chime(hz("D4"), 8), 5, .7, 16), L[-1]["e"] + .3, .11)
L = LN["s11"]; sfx.add(reverb(chime(hz("A4"), 7), 5, .7, 17), L[1]["e"] + .2, .08)

# ── voice ──
voice = Track(); speech = np.zeros(N)
if "--no-voice" not in sys.argv:
    for l in TL["lines"]:
        f = os.path.join(ROOT, "audio", "vo", l["id"] + ".wav")
        if not os.path.exists(f): continue
        x, sr = sf.read(f); x = x if x.ndim == 1 else x.mean(1)
        if sr != SR: x = signal.resample_poly(x, SR, sr)
        voice.add(x, l["s"], 1.0); speech[int(l["s"] * SR): int(l["e"] * SR)] = 1
v = voice.b.copy()
if np.abs(v).max() > 0:
    v = np.stack([hp(v[:, 0], 70), hp(v[:, 1], 70)], 1)
    rms = np.sqrt((v[speech > 0] ** 2).mean()); v *= 0.085 / rms                    # ≈ -21.4 dBFS RMS speech
    v = v + .10 * (reverb(v, 1.1, 1.0, 21, 5000) - v * .5)                           # a little room
# ducking
duck = 1 - .62 * np.clip(smooth(smooth(speech, .25), .35), 0, 1)
duck_solo = 1 - .30 * np.clip(smooth(smooth(speech, .25), .35), 0, 1)
bed = music.b * duck[:, None] * .26 + amb.b * (.55 + .45 * duck[:, None]) * .5
if speech.max() > 0:                      # 旁白下的垫乐压到比人声低约 19 dB
    under = np.sqrt((bed[speech > 0] ** 2).mean()); g = 0.085 * 10 ** (-19 / 20) / under; print("bed gain %.2f" % g); bed *= min(g, 1.6)
fore = solo.b * duck_solo[:, None] * .30 + sfx.b * .9
mus = bed + fore
mix = v + mus
mix = np.tanh(mix * 1.6) / 1.6 * 1.25
mix = mix[: int(TOTAL * SR)]
peak = np.abs(mix).max(); print("peak %.3f  voice rms %.4f  music rms %.4f" % (peak, np.sqrt((v ** 2).mean()), np.sqrt((mus ** 2).mean())))
if peak > .97: mix *= .97 / peak
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
sf.write(os.path.join(ROOT, "out", "audio_mix.wav"), mix, SR, subtype="PCM_16")
sf.write(os.path.join(ROOT, "out", "stem_music.wav"), np.clip(mus[: int(TOTAL * SR)] * 2, -1, 1), SR, subtype="PCM_16")
