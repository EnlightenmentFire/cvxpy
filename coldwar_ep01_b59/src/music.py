"""Library score per 配乐规范: cold-war/suspense palette (low drone + sparse low drum), three-layer arc,
2-4 s equal-power crossfades, voice-keyed sidechain ducking (attack 15 ms / release 500 ms) so music sits
~16.5 dB under the narration and comes back up in pauses, -4 dB @ 3 kHz carve, 2 s fade-in / 3 s fade-out.

All music: Kevin MacLeod (incompetech.com), CC BY 4.0 — attribution in the description + end card.
"""
import json
import math
import os

import numpy as np
import soundfile as sf
from scipy import signal

SR = 48000
LIB = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad/music_lib/wav"

VOICE_DB = -18.0          # active RMS of the narration track (before final loudnorm)
UNDER = 16.5              # music sits this many dB under the voice while narration is active

# layer: (track file, source offset s, timeline start, timeline end, pre-duck RMS dBFS)
# start/end are crossfade centres; fades are applied around them.


def plan(T):
    """T: dict shot_id -> start time. Returns list of segments."""
    hypo_end_flash = T["hypo_out"] + 1.1
    return [
        # 1. bed: very light drone from the top to the dive
        dict(name="Ossuary 6 - Air", src=100.0, t0=0.0, t1=T["dive"] + 1.0, level=-31.0, fin=2.0, fout=3.0),
        # 2. build: the same dark drone under the sea; lifts +2.5 dB when the depth charges start
        dict(name="Controlled Chaos - no percussion", src=20.0, t0=T["dive"] - 2.0, t1=T["hypo_launch"] + 0.2,
             level=-28.0, fin=3.0, fout=2.0, auto=[(T["sonar"] - 2.0, 0.0), (T["sonar"] + 2.0, 2.5)]),
        # 2b. sparse heartbeat-style low drum (synthesized here), sonar -> orders
        dict(name="@heartbeat", src=0.0, t0=T["sonar"], t1=T["hypo_launch"] - 0.5, level=-30.0, fin=4.0, fout=2.0),
        # 3. climax: enters under the boom after 0.5 s of silence, peaks in the narration-free beat, cut at the flash
        dict(name="Hitman", src=41.0, t0=T["hypo_burst"] + 0.5, t1=hypo_end_flash, level=-20.0, fin=2.0, fout=0.25,
             ramp=[(T["hypo_burst"] + 0.5, -27.0), (T["hypo_globe"] + 2.0, -23.5), (T["hypo_out"] - 0.4, -19.0)]),
        # 4. thinning out after the climax: low strings only
        dict(name="Dark Times", src=5.0, t0=T["surfacing"] - 0.5, t1=T["headline"] - 1.2, level=-29.0, fin=3.0,
             fout=3.0),
        # 4b. analysis / "the people outside the door": the calmest dark drone in the set
        dict(name="Ossuary 1 - A Beginning", src=1.0, t0=T["headline"] - 1.2, t1=T["ending"] + 1.5, level=-31.0,
             fin=3.0, fout=3.0),
        # 5. ending: single instrument (piano), resolves before black
        dict(name="Colorless Aura", src=8.0, t0=T["ending"] - 1.5, t1=T["credits"] + 4.5, level=-28.0, fin=3.0,
             fout=3.0),
    ]


def _heartbeat(dur, period=1.5):
    """Low two-beat thump (lub-dub), felt more than heard."""
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros_like(t)
    for k in range(int(dur / period) + 1):
        for off, a in ((0.0, 1.0), (0.24, 0.62)):
            t0 = k * period + off
            i0, i1 = int(t0 * SR), int((t0 + 0.35) * SR)
            if i0 >= len(t):
                continue
            tt = t[i0:i1] - t0
            f = 46 + 18 * np.exp(-tt * 30)
            x[i0:i1] += a * np.sin(2 * np.pi * np.cumsum(f) / SR)[: len(tt)] * np.exp(-tt * 11)
    b, a_ = signal.butter(2, 160 / (SR / 2), "low")
    x = signal.lfilter(b, a_, x)
    return np.stack([x, x], 1).astype(np.float32)


def _load(name, dur=None):
    if name == "@heartbeat":
        return _heartbeat(dur + 10)
    x, sr = sf.read(os.path.join(LIB, name + ".wav"), dtype="float32")
    assert sr == SR
    return x  # stereo


def _rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def _equal_power_env(n, fin, fout):
    e = np.ones(n, np.float32)
    a = int(fin * SR)
    b = int(fout * SR)
    if a > 0:
        e[:a] = np.sin(0.5 * np.pi * np.linspace(0, 1, a)) ** 1.0
    if b > 0:
        e[-b:] *= np.cos(0.5 * np.pi * np.linspace(0, 1, b))
    return e


def _st_db(x, win=2.0):
    """short-term RMS level (dB) of a stereo clip, per sample (computed on 50 ms hops)."""
    hop = int(0.05 * SR)
    pw = np.mean(x ** 2, axis=1) if x.ndim == 2 else x ** 2   # channel power, not a mono fold-down
    n = len(pw) // hop
    p = np.mean(pw[: n * hop].reshape(n, hop), axis=1)
    m = pw
    k = max(1, int(win / 0.05))
    p = np.convolve(p, np.ones(k) / k, "same")
    db = 10 * np.log10(p + 1e-12)
    db = np.repeat(db, hop)
    return np.pad(db, (0, len(m) - len(db)), mode="edge")


def _smooth(db, tau=1.5):
    hop = int(0.05 * SR)
    d = db[::hop]
    c = 1 - math.exp(-0.05 / tau)
    out = np.empty_like(d)
    g = d[0]
    for i, v in enumerate(d):
        g += (v - g) * c
        out[i] = g
    out = np.repeat(out, hop)[: len(db)]
    return np.pad(out, (0, max(0, len(db) - len(out))), mode="edge")


def level_ride(clip, target_db, max_cut=18.0, max_boost=6.0, tau=1.5):
    """Slow leveler: rides the clip toward target_db (scalar or per-sample array) so swells don't jump out."""
    st = _st_db(clip)
    g = np.clip(target_db - st, -max_cut, max_boost)
    g = _smooth(g, tau)
    return (clip * (10 ** (g / 20))[:, None]).astype(np.float32)


def peaking_eq(x, f0=3000.0, q=1.0, gain_db=-4.0):
    A = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * f0 / SR
    alpha = math.sin(w0) / (2 * q)
    b = np.array([1 + alpha * A, -2 * math.cos(w0), 1 - alpha * A])
    a = np.array([1 + alpha / A, -2 * math.cos(w0), 1 - alpha / A])
    return signal.lfilter(b / a[0], a / a[0], x, axis=0).astype(np.float32)


def voice_activity_env(voice, attack=0.015, release=0.5):
    """Sidechain key: 1 while narration is sounding, smoothed with attack/release (one-pole)."""
    hop = int(0.005 * SR)
    n = len(voice) // hop
    fr = voice[: n * hop].reshape(n, hop)
    lvl = 20 * np.log10(np.sqrt(np.mean(fr ** 2, axis=1)) + 1e-9)
    key = (lvl > VOICE_DB - 22).astype(np.float32)  # speaking (incl. soft consonants)
    # bridge micro-gaps inside words (<60 ms) so the music doesn't pump within a phrase
    k = int(0.06 / 0.005)
    key = np.convolve(key, np.ones(k), "same") > 0
    key = key.astype(np.float32)
    out = np.zeros_like(key)
    ca = 1 - math.exp(-0.005 / attack)
    cr = 1 - math.exp(-0.005 / release)
    g = 0.0
    for i, v in enumerate(key):
        g += (v - g) * (ca if v > g else cr)
        out[i] = g
    env = np.repeat(out, hop)
    return np.pad(env, (0, len(voice) - len(env)), mode="edge")


def build(tl, voice):
    T = {s["id"]: s["start"] for s in tl["shots"]}
    n = len(voice)
    bus = np.zeros((n, 2), np.float32)
    depth_db = np.zeros(n, np.float32)   # per-sample duck depth (weighted by layer presence)
    weight = np.zeros(n, np.float32)
    log = []
    for seg in plan(T):
        fin, fout = seg["fin"], seg["fout"]
        x = _load(seg["name"], seg["t1"] - seg["t0"] + fin + fout)
        a = seg["t0"] - fin / 2 if seg["t0"] > 0 else 0.0
        b = min(n / SR, seg["t1"] + fout / 2)
        L = int((b - a) * SR)
        s0 = int(max(0.0, seg["src"] - (seg["t0"] - a)) * SR)
        clip = x[s0:s0 + L]
        if len(clip) < L:
            clip = np.pad(clip, ((0, L - len(clip)), (0, 0)))
        g = 10 ** ((seg["level"] - _rms_db(clip[int(fin * SR): max(int(fin * SR) + 1, L - int(fout * SR))])) / 20)
        if seg.get("ramp"):
            ts_ = np.arange(L) / SR + a
            target = np.interp(ts_, [p[0] for p in seg["ramp"]], [p[1] for p in seg["ramp"]])
            clip = level_ride(clip, target, tau=0.8)
        else:
            clip = level_ride(clip, seg["level"], tau=2.0)
        g = 1.0
        env = _equal_power_env(L, fin if seg["t0"] > 0 else 2.0, fout)
        if seg.get("auto"):
            ts = np.arange(L) / SR + a
            pts = seg["auto"]
            env = env * (10 ** (np.interp(ts, [p[0] for p in pts], [p[1] for p in pts]) / 20)).astype(np.float32)
        i0 = int(a * SR)
        i1 = min(n, i0 + L)
        bus[i0:i1] += (clip[: i1 - i0] * g) * env[: i1 - i0, None]
        ts = np.arange(i1 - i0) / SR + a
        lvl_db = seg["level"] + (np.interp(ts, [p[0] for p in seg["auto"]], [p[1] for p in seg["auto"]])
                                 if seg.get("auto") else 0.0)
        d = np.maximum(0.0, lvl_db - (VOICE_DB - UNDER))
        depth_db[i0:i1] += d * env[: i1 - i0] ** 2
        weight[i0:i1] += env[: i1 - i0] ** 2
        log.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in seg.items() if k not in ("auto", "ramp")})
    depth_db = np.where(weight > 1e-4, depth_db / np.maximum(weight, 1e-4), 0.0)
    # hard silence: first 0.5 s of the hypothetical burst, and right after the flash
    for (s, e) in ((T["hypo_burst"], T["hypo_burst"] + 0.5), (T["hypo_out"] + 1.1 + 0.25, T["surfacing"] - 2.0)):
        bus[int(s * SR):int(e * SR)] = 0.0
    # sidechain (voice-keyed): while narration sounds, pull the music down to (voice - UNDER) dB;
    # attack 15 ms / release 500 ms come from the key envelope; music comes back up in the pauses.
    key = voice_activity_env(voice)
    mus_st = _st_db(bus, win=0.4)
    over = np.maximum(0.0, mus_st - (VOICE_DB - UNDER))
    gain_db = -over * key
    gain_db = np.minimum(gain_db, -depth_db * key * 0.0)  # (depth kept for logging only)
    bus *= (10 ** (gain_db / 20))[:, None]
    # carve 2-4 kHz for the voice, then global fades
    bus = peaking_eq(bus, 3000.0, 1.0, -4.0)
    fi, fo = int(2.0 * SR), int(3.0 * SR)
    bus[:fi] *= np.linspace(0, 1, fi)[:, None]
    bus[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return bus, key, depth_db, log
