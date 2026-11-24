"""Music, sound effects and the final mix. Everything here is synthesised
(no samples), so there is nothing to license.

usage: python audio.py LINES_DIR OUT_WAV [--segments cold,title,bet] [--total SECONDS]
"""
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt

from compose import build_timeline
from scenes import Ctx, RULES, streak_times

SR = 48000
RNG = np.random.default_rng(1983)


def db(x):
    return 10 ** (x / 20)


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na > 0:
        e[:na] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, na))
    if nr > 0:
        e[-nr:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nr))
    return e


def lp(x, fc, order=2):
    sos = butter(order, fc, btype="lowpass", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0)


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="bandpass", fs=SR, output="sos")
    return sosfilt(sos, x, axis=0)


# ------------------------------------------------------------------ instruments
_PAD_CACHE = {}


def pad_block(midis, dur, fc, seed=0):
    key = (tuple(midis), dur, fc)
    if key in _PAD_CACHE:
        return _PAD_CACHE[key]
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed + int(fc))
    out = np.zeros((n, 2))
    for m in midis:
        f0 = mf(m)
        for dc, pan in ((-7, -0.7), (0, 0.0), (6, 0.7)):
            f = f0 * 2 ** (dc / 1200)
            sig = np.zeros(n)
            vib = 0.0018 * np.sin(2 * np.pi * (0.13 + 0.05 * rng.random()) * t + rng.uniform(0, 6.28))
            for k in range(1, 48):
                fk = k * f
                if fk > 9000:
                    break
                amp = (1.0 / k) / math.sqrt(1 + (fk / fc) ** 4)
                if amp < 2e-3:
                    break
                sig += amp * np.sin(2 * np.pi * fk * t * (1 + vib) + rng.uniform(0, 6.28))
            out[:, 0] += sig * (1 - pan) / 2
            out[:, 1] += sig * (1 + pan) / 2
    out /= (np.abs(out).max() + 1e-9)
    out *= env_ar(n, min(2.5, dur * 0.3), min(2.5, dur * 0.3))[:, None]
    _PAD_CACHE[key] = out
    return out


def pluck(m, dur=0.42, bright=2600):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = mf(m)
    sig = np.zeros(n)
    for k in range(1, 16, 2):
        fk = k * f
        if fk > 8000:
            break
        sig += (1 / k) / math.sqrt(1 + (fk / bright) ** 4) * np.sin(2 * np.pi * fk * t)
    sig *= np.exp(-t / 0.11) * (1 - np.exp(-t / 0.002))
    return sig / (np.abs(sig).max() + 1e-9)


def sub(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = mf(m)
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    s *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.09 * t)
    return s * env_ar(n, 1.5, 1.5) / 1.18


CHORDS = {  # voicings (MIDI)
    "Am9": [45, 52, 55, 60, 71], "Fmaj7": [41, 48, 52, 57, 64], "Dm9": [38, 50, 53, 57, 64],
    "Esus4": [40, 47, 52, 57, 59], "Cadd9": [36, 48, 55, 62, 64], "G6": [43, 50, 55, 59, 64],
}
ROOT = {"Am9": 33, "Fmaj7": 29, "Dm9": 38, "Esus4": 28, "Cadd9": 36, "G6": 31}
CYCLE = ["Am9", "Fmaj7", "Dm9", "Esus4"]
END_CYCLE = ["Am9", "Fmaj7", "Cadd9", "Cadd9"]
CH = 8.0  # seconds per chord

# per-segment mix: pad level, brightness (lowpass Hz), arp level, arp division, sub level
SECTION = {
    "cold": (0.55, 700, 0.0, 0, 0.8), "title": (0.9, 1500, 0.0, 0, 1.0), "bet": (0.55, 850, 0.22, 2, 0.7),
    "out": (0.55, 950, 0.30, 2, 0.7), "rules": (0.48, 900, 0.36, 4, 0.6), "hard": (0.38, 650, 0.0, 0, 0.8),
    "div": (0.55, 950, 0.28, 2, 0.7), "t88": (0.10, 500, 0.0, 0, 0.75), "doubt": (0.40, 700, 0.0, 0, 0.7),
    "end": (0.75, 1300, 0.16, 2, 0.8), "credits": (0.55, 1100, 0.0, 0, 0.6),
}
BPM = 92


# ------------------------------------------------------------------ sfx
def sfx_key(seed):
    r = np.random.default_rng(seed)
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    click = r.normal(0, 1, n) * np.exp(-t / 0.0045)
    click = bp(click, 1800, 6500)
    thump = np.sin(2 * np.pi * r.uniform(140, 190) * t) * np.exp(-t / 0.012) * 0.6
    bar = bp(r.normal(0, 1, n), 600, 1500) * np.exp(-np.maximum(0, t - 0.012) / 0.008) * (t > 0.012) * 0.35
    x = click + thump + bar
    return x / (np.abs(x).max() + 1e-9)


def sfx_ding():
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = 2350.0
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.55) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.22)
         + 0.25 * np.sin(2 * np.pi * f * 5.40 * t) * np.exp(-t / 0.09))
    x[: int(0.003 * SR)] *= np.linspace(0, 1, int(0.003 * SR))
    return x / np.abs(x).max()


def sfx_tick():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.028) + 0.25 * bp(RNG.normal(0, 1, n), 300, 1200) * np.exp(-t / 0.01)
    return x / np.abs(x).max()


def sfx_boom():
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    f = 34 + 50 * np.exp(-t / 0.18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.9) + 0.3 * lp(RNG.normal(0, 1, n), 300) * np.exp(-t / 0.25)
    return x / np.abs(x).max()


def sfx_stamp():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.06) + 0.5 * lp(RNG.normal(0, 1, n), 900) * np.exp(-t / 0.03)
    return x / np.abs(x).max()


def sfx_swell(dur=2.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(RNG.normal(0, 1, n), 700) * np.sin(np.pi * t / dur) ** 2
    return x / np.abs(x).max()


def sfx_paper(n_hits=10, dur=2.2):
    n = int(dur * SR)
    x = np.zeros(n)
    for k in range(n_hits):
        p = int(RNG.uniform(0, dur - 0.15) * SR)
        m = int(0.12 * SR)
        tt = np.arange(m) / SR
        x[p:p + m] += bp(RNG.normal(0, 1, m), 900, 5000) * np.exp(-tt / 0.03) * RNG.uniform(0.4, 1)
    return x / (np.abs(x).max() + 1e-9)


def sfx_fax(dur=3.4):
    """Generic fax-style handshake: calling tones, answer tone, FSK warble, then paper feed."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)

    def seg(a, b):
        return (t >= a) & (t < b)

    for a in (0.0, 0.75):
        m = seg(a, a + 0.45)
        x[m] += 0.5 * np.sin(2 * np.pi * 1100 * t[m])
    m = seg(1.3, 1.9)
    x[m] += 0.45 * np.sin(2 * np.pi * 2100 * t[m])
    m = seg(1.95, 2.55)
    bits = (np.floor(t[m] * 300) % 2) * 2 - 1
    f = np.where(bits > 0, 1850, 1650)
    x[m] += 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    m = seg(2.5, dur)
    nn = m.sum()
    feed = lp(RNG.normal(0, 1, nn), 1800) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t[m])) * 0.5
    feed += 0.15 * np.sin(2 * np.pi * 120 * t[m])
    x[m] += feed * env_ar(nn, 0.1, 0.4)
    x = bp(x, 300, 3400)
    return x / np.abs(x).max()


# ------------------------------------------------------------------ events
def add(buf, x, t, gain_db, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    if x.ndim == 1:
        x = np.stack([x * min(1.0, 1 - pan), x * min(1.0, 1 + pan)], 1)
    j = min(len(buf), i + len(x))
    if i < 0:
        x = x[-i:]
        j = min(len(buf), len(x))
        i = 0
    buf[i:j] += x[: j - i] * db(gain_db)


def typing_events(items):
    """(time, kind) for typewriter sounds; must mirror scenes.py typing speeds."""
    ev = []

    def seg(sid):
        return next((i for i in items if i["seg"] == sid and i["kind"] == "scene"), None)

    def type_run(start, n, cps, ding, kind="key"):
        for k in range(n):
            ev.append((start + k / cps, kind))
        if ding:
            ev.append((start + n / cps + 0.05, "ding"))

    it = seg("rules")
    if it:
        x = Ctx(0, 0, it["cues"])
        s0 = it["start"]
        type_run(s0 + x.s("r_paper") + 0.4, len("海龟交易规则 · 摘要"), 9, True)
        for i, r in enumerate(RULES):
            if f"r{i + 1}" in it["cues"]:
                type_run(s0 + x.s(f"r{i + 1}"), len(r), 13, True)
        type_run(s0 + x.s("r5_quote") + 0.3, 160, 30, False, "softkey")
        ev.append((s0 + x.s("r_nosecret"), "stamp"))
    it = seg("bet")
    if it:
        x = Ctx(0, 0, it["cues"])
        type_run(it["start"] + x.s("b_quote"), 74, 22, False, "softkey")
        type_run(it["start"] + x.s("b_deny") + 0.5, 82, 26, False, "softkey")
    it = seg("div")
    if it:
        x = Ctx(0, 0, it["cues"])
        type_run(it["start"] + x.s("v_q1") - 0.2, 330, 24, False, "softkey")
    return ev


# ------------------------------------------------------------------ music track
def music_track(items, total):
    n = int(total * SR) + SR
    buf = np.zeros((n, 2))
    seg_of = []  # (start, end, sid)
    for it in items:
        sid = it["seg"]
        seg_of.append((it["start"], it["end"], sid, it["kind"]))
    # chord blocks every CH seconds, each block takes the section's settings at its centre
    t = 0.0
    k = 0
    while t < total:
        mid = t + CH / 2
        sid = next((s for a, b, s, kd in seg_of if a <= mid < b), "credits")
        kind = next((kd for a, b, s, kd in seg_of if a <= mid < b), "scene")
        lvl, fc, arp, div, sl = SECTION.get(sid, SECTION["bet"])
        if kind == "chapter":
            lvl, fc = max(lvl, 0.7), max(fc, 1100)
        cyc = END_CYCLE if sid in ("end", "credits") else CYCLE
        name = cyc[k % 4]
        blk = pad_block(CHORDS[name], CH + 3.0, fc, seed=k % 4)
        add(buf, blk, t - 1.5, 20 * math.log10(max(lvl, 1e-3)) - 12)
        if sl > 0:
            add(buf, sub(ROOT[name] + 12, CH + 2.0), t - 1.0, 20 * math.log10(sl) - 17)
        if arp > 0 and div > 0:
            step = 60.0 / BPM / div
            notes = sorted(CHORDS[name][1:]) + [CHORDS[name][2] + 12]
            j = 0
            tt = t
            while tt < t + CH:
                if RNG.random() < (0.85 if div == 2 else 0.7):
                    m = notes[j % len(notes)] + 12
                    add(buf, pluck(m, bright=1800 + fc), tt, 20 * math.log10(arp) - 21, pan=0.45 * math.sin(j * 1.7))
                j += 1
                tt += step
        t += CH
        k += 1
    # "the music opens" on the big win, then sinks back
    it = next((i for i in items if i["seg"] == "hard" and i["kind"] == "scene"), None)
    if it:
        x = Ctx(0, 0, it["cues"])
        _, tb0, tb1 = streak_times(x)
        t0 = it["start"] + tb0
        blk = pad_block([45, 52, 57, 60, 64, 69, 76], 9.0, 3200, seed=9)
        add(buf, blk, t0 - 0.2, -10)
        add(buf, sub(33, 9.0), t0 - 0.2, -14)
        step = 60.0 / BPM / 4
        for j in range(int(7.0 / step)):
            m = [69, 72, 76, 79, 81, 79, 76, 72][j % 8]
            add(buf, pluck(m, bright=4200), t0 + 0.3 + j * step, -24 - 6 * (j * step / 7.0), pan=0.4 * math.sin(j))
    return buf[:n]


# ------------------------------------------------------------------ mix
def mix(lines_dir, out_wav, segments=None, total_override=None):
    durs = {}
    voice = {}
    for f in os.listdir(lines_dir):
        if f.endswith(".wav") and not f.startswith("."):
            y, sr = sf.read(os.path.join(lines_dir, f), dtype="float32")
            assert sr == SR
            voice[f[:-4]] = y
            durs[f[:-4]] = len(y) / SR
    items, lines, total = build_timeline(durs)
    if segments:
        keep = [i for i in items if i["seg"] in segments]
        total = max(i["end"] for i in keep)
    if total_override:
        total = total_override
    n = int(total * SR) + SR
    vbuf = np.zeros((n, 2))
    for ln in lines:
        if ln["start"] < total and ln["id"] in voice:
            add(vbuf, voice[ln["id"]], ln["start"], 0.0)
    mus = music_track(items, total)[:n]
    # duck music under the voice
    v = np.abs(vbuf).max(1)
    win = int(0.03 * SR)
    envv = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, mode="same"))
    act = (envv > db(-40)).astype(float)
    # attack 40 ms, release 450 ms
    g = np.zeros(n)
    a_c, r_c = math.exp(-1 / (0.04 * SR)), math.exp(-1 / (0.45 * SR))
    st = 0.0
    act_ds = act[::48]
    gd = np.zeros(len(act_ds))
    a_c, r_c = math.exp(-1 / (0.04 * SR / 48)), math.exp(-1 / (0.45 * SR / 48))
    for i, aa in enumerate(act_ds):
        c_ = a_c if aa > st else r_c
        st = c_ * st + (1 - c_) * aa
        gd[i] = st
    g = np.interp(np.arange(n), np.arange(len(gd)) * 48, gd)
    duck = db(-9.0) ** g
    mus *= duck[:, None]
    # sfx
    fx = np.zeros((n, 2))
    keys = [sfx_key(s) for s in range(12)]
    ding, tick, stamp = sfx_ding(), sfx_tick(), sfx_stamp()
    for tt, kind in typing_events(items):
        if tt >= total:
            continue
        if kind == "key":
            add(fx, keys[int(RNG.integers(0, 12))], tt, -24 + RNG.uniform(-2, 2), pan=RNG.uniform(-0.3, 0.3))
        elif kind == "softkey":
            add(fx, keys[int(RNG.integers(0, 12))], tt, -31 + RNG.uniform(-2, 2), pan=RNG.uniform(-0.3, 0.3))
        elif kind == "ding":
            add(fx, ding, tt, -23, pan=0.35)
        elif kind == "stamp":
            add(fx, stamp, tt, -14)
    for it in items:
        if it["start"] >= total:
            continue
        if it["kind"] == "chapter":
            add(fx, sfx_swell(2.4), it["start"] + 0.05, -30)
        if it["seg"] == "title" and it["kind"] == "scene":
            add(fx, sfx_boom(), it["start"] + 0.75, -12)
        if it["kind"] != "scene":
            continue
        x = Ctx(0, 0, it["cues"])
        if it["seg"] == "hard":
            t_loss, tb0, _ = streak_times(x)
            for k, tl in enumerate(t_loss):
                add(fx, tick, it["start"] + tl, -25 + k * 0.6)
            add(fx, sfx_boom(), it["start"] + tb0, -20)
        if it["seg"] == "t88":
            add(fx, sfx_fax(), it["start"] + x.s("t_end") + 0.4, -21)
        if it["seg"] == "out":
            add(fx, sfx_paper(14, 2.3), it["start"] + x.s("o_apps") - 0.3, -33)
    mixbuf = vbuf + mus + fx
    peak = np.abs(mixbuf).max()
    lim = db(-1.0)
    if peak > lim:
        mixbuf = np.tanh(mixbuf / lim) * lim
    sf.write(out_wav, mixbuf[: int(total * SR)].astype(np.float32), SR, subtype="FLOAT")
    json.dump(dict(total=total, lines=lines), open(out_wav[:-4] + ".timeline.json", "w"), ensure_ascii=False, indent=0)
    v_rms = 20 * math.log10(np.sqrt((vbuf[act > 0] ** 2).mean()) + 1e-12) if act.any() else 0
    m_on = 20 * math.log10(np.sqrt((mus[act > 0] ** 2).mean()) + 1e-12) if act.any() else 0
    m_off = 20 * math.log10(np.sqrt((mus[act == 0] ** 2).mean()) + 1e-12) if (act == 0).any() else 0
    try:
        import pyloudnorm as pyln
        lufs = pyln.Meter(SR).integrated_loudness(mixbuf[: int(total * SR)])
    except Exception:
        lufs = float("nan")
    print(f"music under voice {m_on:.1f} dBFS, music alone {m_off:.1f} dBFS, integrated {lufs:.1f} LUFS")
    print(f"mixed {total:.1f}s -> {out_wav}; voice RMS (active) {v_rms:.1f} dBFS; peak {20*math.log10(peak+1e-12):.1f} dBFS")
    return total


if __name__ == "__main__":
    args = sys.argv[1:]
    segs = None
    tot = None
    if "--segments" in args:
        i = args.index("--segments")
        segs = args[i + 1].split(",")
        args = args[:i] + args[i + 2:]
    if "--total" in args:
        i = args.index("--total")
        tot = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    mix(args[0], args[1], segs, tot)
