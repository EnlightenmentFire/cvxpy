"""Score + sound design on the edit timeline. Everything is synthesized here."""
import math

import numpy as np

import cuelib
import sound as S

SR = S.SR


def _rms(x):
    return float(np.sqrt(np.mean(x ** 2)) + 1e-12)


def _norm(x, target_rms):
    return x * (target_rms / _rms(x))


def _env(n, pts):
    """piecewise-linear automation: pts = [(sample_index, gain), ...]"""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return np.interp(np.arange(n), xs, ys).astype(np.float32)


def _place(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    if i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * gain


def boom(dur=7.0, seed=1):
    rng = np.random.default_rng(seed)
    t = S.t_axis(dur)
    f = 22 + 30 * np.exp(-t * 1.5)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 0.55)
    rumble = S.lowpass(rng.standard_normal(len(t)), 180) * np.exp(-t * 0.4) * 1.5
    crack = S.bandpass(rng.standard_normal(len(t)), 60, 2500) * np.exp(-t * 7) * 0.8
    x = sub * 1.6 + rumble + crack
    return S.reverb(x, 4.5, 0.4, seed=11)


def tinnitus(dur=7.0, f=7400.0):
    t = S.t_axis(dur)
    return np.sin(2 * np.pi * f * t) * (np.clip(t / 0.3, 0, 1) * np.exp(-t * 0.45))


def whoosh(dur=2.2, seed=2, up=True):
    rng = np.random.default_rng(seed)
    t = S.t_axis(dur)
    n = rng.standard_normal(len(t))
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    lo = S.bandpass(n, 300, 1800) * env
    return S.reverb(lo, 1.5, 0.3, seed=3)


def flyby(dur=3.5, seed=5):
    """Low propeller-aircraft pass: rough tone with doppler-ish sweep."""
    rng = np.random.default_rng(seed)
    t = S.t_axis(dur)
    f = 95 * (1 + 0.12 * np.tanh((dur / 2 - t) * 2.0))
    tone = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * 0.3
    noise = S.bandpass(rng.standard_normal(len(t)), 200, 3000) * 0.6
    env = np.exp(-((t - dur / 2) / (dur / 5)) ** 2)
    return S.lowpass((tone + noise) * env, 4000)


def pop(seed=0):
    rng = np.random.default_rng(seed)
    t = S.t_axis(0.25)
    return S.bandpass(rng.standard_normal(len(t)), 400, 3500) * np.exp(-t * 40)


def heartbeat(dur, period=1.25):
    t = S.t_axis(dur)
    x = np.zeros_like(t)
    for k in range(int(dur / period) + 1):
        for off, a in ((0.0, 1.0), (0.22, 0.7)):
            t0 = k * period + off
            m = (t >= t0) & (t < t0 + 0.25)
            tt = t[m] - t0
            x[m] += a * np.sin(2 * np.pi * 48 * tt) * np.exp(-tt * 18)
    return x


def waves(dur, seed=7):
    rng = np.random.default_rng(seed)
    t = S.t_axis(dur)
    n = S.lowpass(rng.standard_normal(len(t)), 900)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * t + 1) * np.sin(2 * np.pi * 0.047 * t)
    return n * mod


def underwater(dur, seed=8):
    rng = np.random.default_rng(seed)
    t = S.t_axis(dur)
    n = S.lowpass(rng.standard_normal(len(t)), 220)
    return n * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t))


def build(tl, voice, sr):
    assert sr == SR
    total = len(voice) / SR
    n = len(voice)
    shots = {s["id"]: s for s in tl["shots"]}

    def T(sid, which="start"):
        return shots[sid][which]

    music = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)

    # --- base drone, automated per section --------------------------------------
    dr = S.drone(total + 1, 55.0)[:n]
    dr = _norm(dr, 0.016)
    g = [(0, 0.0)]
    def at(sec, gain):
        g.append((int(sec * SR), gain))
    at(T("open_text"), 0.0); at(T("open_text") + 2, 0.6); at(T("title"), 0.9); at(T("u2"), 0.8)
    at(T("timeline"), 1.0); at(T("dive"), 1.1); at(T("sonar"), 1.2); at(T("orders", "end"), 1.0)
    at(T("hypo_launch"), 0.6)
    at(T("hypo_burst"), 0.0); at(T("hypo_burst") + 0.5, 0.0); at(T("hypo_burst") + 3.0, 0.9)
    at(T("hypo_globe"), 1.4); at(T("hypo_out") + 1.0, 1.6); at(T("hypo_out") + 1.1, 0.0)
    at(T("hypo_out") + 3.0, 0.5); at(T("surfacing"), 0.7); at(T("photo"), 0.5); at(T("vote"), 0.6)
    at(T("split"), 0.6); at(T("ending"), 0.5); at(T("credits"), 0.4); at(total, 0.0)
    music += dr * _env(n, g)

    # --- string pad (sparse): section 2, and from section 6 onwards ----------------
    pad1 = _norm(S.string_pad(T("timeline") - T("u2") + 2, [73.42, 110.0, 174.61], attack=4, release=3), 0.010)
    _place(music, pad1, T("u2"))
    dur2 = T("credits", "end") - T("arkhipov")
    pad2 = _norm(S.string_pad(dur2, [73.42, 110.0, 146.83, 220.0], attack=6, release=5), 0.011)
    _place(music, pad2, T("arkhipov"))
    # final long tone over the last line and credits
    last = T("ending", "end") - 8.0
    tone = _norm(S.string_pad(T("credits", "end") - last + 1.5, [55.0, 82.41, 110.0, 164.81], attack=3, release=4), 0.014)
    _place(music, tone, last)

    # --- cold open: hypothetical boom + tinnitus ---------------------------------
    _place(sfx, _norm(boom(6.0), 0.09), T("cold") + 0.1)
    _place(sfx, _norm(tinnitus(5.0), 0.006), T("cold") + 0.6)
    # title hit
    _place(sfx, _norm(S.impact(3.0, seed=4, depth=0.2), 0.05), T("title"))

    # --- black saturday: a low pulse per red dot ---------------------------------
    for k in range(3):
        _place(sfx, _norm(S.sonar_ping(220.0, 2.0), 0.012), T("timeline") + 0.6 + k * 0.9)
    _place(sfx, _norm(whoosh(2.2), 0.03), T("dive") + 0.2)
    _place(sfx, _norm(S.impact(2.5, seed=6, depth=0.1), 0.04), T("dive") + 1.4)  # hitting the water

    # --- under the sea ------------------------------------------------------------
    u0, u1 = T("dive") + 1.4, T("hypo_launch")
    uw = _norm(underwater(u1 - u0 + 1), 0.02)
    uw *= _env(len(uw), [(0, 0), (SR, 1), (len(uw) - SR, 1), (len(uw) - 1, 0)])
    _place(music, uw, u0)
    t = u0 + 2.0
    while t < u1 - 2:
        _place(sfx, _norm(S.sonar_ping(), 0.010), t)
        t += 7.5
    for k, tt in enumerate(np.arange(T("section") + 3, T("orders", "end"), 11.0)):
        _place(sfx, _norm(S.metal_groan(seed=k), 0.008), tt)
    sh = shots["sonar"]
    beale, cony, heavy = cuelib.sonar_hits(sh["cues"], sh["end"] - sh["start"])
    for k, h in enumerate(beale + cony):
        _place(sfx, _norm(S.impact(2.5, seed=10 + k), 0.06), sh["start"] + h)
    for k, h in enumerate(heavy):
        _place(sfx, _norm(S.impact(2.5, seed=30 + k, depth=1.6), 0.10), sh["start"] + h)
    hb = _norm(heartbeat(T("quote_sav", "end") - T("quote_sav")), 0.03)
    _place(music, hb, T("quote_sav"))

    # --- hypothetical --------------------------------------------------------------
    _place(sfx, _norm(whoosh(2.0, seed=9), 0.04), T("hypo_launch") + 0.4)
    hb0 = T("hypo_burst")
    # silence: hard-mute music & sfx for the first 0.5 s of the burst shot
    i0, i1 = int(hb0 * SR), int((hb0 + 0.5) * SR)
    music[i0:i1] = 0
    sfx[i0:i1] = 0
    _place(sfx, _norm(boom(8.0, seed=2), 0.14), hb0 + 0.5)
    _place(sfx, _norm(tinnitus(7.0), 0.008), hb0 + 0.6)
    gl = T("hypo_globe")
    rise = S.drone(T("hypo_out") + 1.1 - gl + 0.5, 46.25, seed=5, bright=900)
    rise = _norm(rise, 0.02) * np.linspace(0.4, 1.6, len(rise))
    _place(music, rise, gl)
    for k in range(8):
        _place(sfx, _norm(S.impact(2.0, seed=50 + k, depth=0.3), 0.025), gl + 1.0 + k * 1.3)
    cut = T("hypo_out") + 1.1
    music[int(cut * SR):int((cut + 1.2) * SR)] *= np.linspace(0, 1, int(1.2 * SR))[: len(music[int(cut * SR):int((cut + 1.2) * SR)])]
    sfx[int(cut * SR):int((cut + 0.6) * SR)] = 0
    _place(sfx, _norm(S.sonar_ping(660.0, 3.0), 0.012), cut + 0.15)

    # --- surfaced: waves, aircraft, cannon -------------------------------------------
    w0 = T("surfacing")
    wv = _norm(waves(T("credits", "end") - w0 + 1), 0.012)
    wv *= _env(len(wv), [(0, 0), (2 * SR, 1), (int((T("ending", "end") - w0) * SR), 1), (len(wv) - 1, 0)])
    _place(music, wv, w0)
    for sid in ("topdown", "tower"):
        s = shots[sid]
        for p in cuelib.plane_passes(s["cues"], s["end"] - s["start"], sid):
            _place(sfx, _norm(flyby(), 0.035), s["start"] + p - 1.75)
    s = shots["topdown"]
    s4 = s["cues"].get("f04", (2.0, 2.0))[0]
    for k in range(14):
        _place(sfx, _norm(pop(k), 0.02), s["start"] + s4 + 0.9 + k * 0.09)
    _place(sfx, _norm(S.impact(2.0, seed=77, depth=0.2), 0.035), T("photo"))

    # --- duck the music under the voice; keep SFX less ducked ----------------------
    music = S.duck(music, voice, depth=0.5)
    sfx = S.duck(sfx, voice, depth=0.25)
    out = (music + sfx).astype(np.float32)
    # fade out at the very end
    k = int(2.0 * SR)
    out[-k:] *= np.linspace(1, 0, k)
    return out


def build_sfx(tl, voice, sr):
    assert sr == SR
    total = len(voice) / SR
    n = len(voice)
    shots = {s["id"]: s for s in tl["shots"]}

    def T(sid, which="start"):
        return shots[sid][which]

    music = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)

    # --- cold open: hypothetical boom + tinnitus ---------------------------------
    _place(sfx, _norm(boom(6.0), 0.09), T("cold") + 0.1)
    _place(sfx, _norm(tinnitus(5.0), 0.006), T("cold") + 0.6)
    # title hit
    _place(sfx, _norm(S.impact(3.0, seed=4, depth=0.2), 0.05), T("title"))

    # --- black saturday: a low pulse per red dot ---------------------------------
    for k in range(3):
        _place(sfx, _norm(S.sonar_ping(220.0, 2.0), 0.012), T("timeline") + 0.6 + k * 0.9)
    _place(sfx, _norm(whoosh(2.2), 0.03), T("dive") + 0.2)
    _place(sfx, _norm(S.impact(2.5, seed=6, depth=0.1), 0.04), T("dive") + 1.4)  # hitting the water

    # --- under the sea ------------------------------------------------------------
    u0, u1 = T("dive") + 1.4, T("hypo_launch")
    uw = _norm(underwater(u1 - u0 + 1), 0.010)
    uw *= _env(len(uw), [(0, 0), (SR, 1), (len(uw) - SR, 1), (len(uw) - 1, 0)])
    _place(music, uw, u0)
    t = u0 + 2.0
    while t < u1 - 2:
        _place(sfx, _norm(S.sonar_ping(), 0.010), t)
        t += 7.5
    for k, tt in enumerate(np.arange(T("section") + 3, T("orders", "end"), 11.0)):
        _place(sfx, _norm(S.metal_groan(seed=k), 0.008), tt)
    sh = shots["sonar"]
    beale, cony, heavy = cuelib.sonar_hits(sh["cues"], sh["end"] - sh["start"])
    for k, h in enumerate(beale + cony):
        _place(sfx, _norm(S.impact(2.5, seed=10 + k), 0.06), sh["start"] + h)
    for k, h in enumerate(heavy):
        _place(sfx, _norm(S.impact(2.5, seed=30 + k, depth=1.6), 0.10), sh["start"] + h)

    # --- hypothetical --------------------------------------------------------------
    _place(sfx, _norm(whoosh(2.0, seed=9), 0.04), T("hypo_launch") + 0.4)
    hb0 = T("hypo_burst")
    # silence: hard-mute music & sfx for the first 0.5 s of the burst shot
    i0, i1 = int(hb0 * SR), int((hb0 + 0.5) * SR)
    music[i0:i1] = 0
    sfx[i0:i1] = 0
    _place(sfx, _norm(boom(8.0, seed=2), 0.14), hb0 + 0.5)
    _place(sfx, _norm(tinnitus(7.0), 0.008), hb0 + 0.6)
    gl = T("hypo_globe")
    cut = T("hypo_out") + 1.1
    music[int(cut * SR):int((cut + 1.2) * SR)] *= np.linspace(0, 1, int(1.2 * SR))[: len(music[int(cut * SR):int((cut + 1.2) * SR)])]
    sfx[int(cut * SR):int((cut + 0.6) * SR)] = 0
    _place(sfx, _norm(S.sonar_ping(660.0, 3.0), 0.012), cut + 0.15)

    # --- surfaced: waves, aircraft, cannon -------------------------------------------
    w0 = T("surfacing")
    wv = _norm(waves(T("credits", "end") - w0 + 1), 0.009)
    wv *= _env(len(wv), [(0, 0), (2 * SR, 1), (int((T("ending", "end") - w0) * SR), 1), (len(wv) - 1, 0)])
    _place(music, wv, w0)
    for sid in ("topdown", "tower"):
        s = shots[sid]
        for p in cuelib.plane_passes(s["cues"], s["end"] - s["start"], sid):
            _place(sfx, _norm(flyby(), 0.035), s["start"] + p - 1.75)
    s = shots["topdown"]
    s4 = s["cues"].get("f04", (2.0, 2.0))[0]
    for k in range(14):
        _place(sfx, _norm(pop(k), 0.02), s["start"] + s4 + 0.9 + k * 0.09)
    _place(sfx, _norm(S.impact(2.0, seed=77, depth=0.2), 0.035), T("photo"))

    # --- duck the music under the voice; keep SFX less ducked ----------------------
    amb = S.duck(music, voice, depth=0.35)   # ambience (underwater rumble, waves)
    sfx = S.duck(sfx, voice, depth=0.25)
    out = (amb + sfx).astype(np.float32)
    # fade out at the very end
    k = int(2.0 * SR)
    out[-k:] *= np.linspace(1, 0, k)
    return out
