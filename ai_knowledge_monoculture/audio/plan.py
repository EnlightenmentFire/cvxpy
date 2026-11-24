"""Sound effects per segment (music now comes from MusicGen, see music_build.py).
Only the effects the brief asks for, plus a few very soft transition whooshes:
typing, copier hum, pebbles into pots, urgent alerts + one brake, corn-field wind, one comic 'bo'."""
import numpy as np

import synth as S


def typing_clicks(t0, t1, rate=15.0, seed=0, gain=0.22):
    rng = np.random.default_rng(seed)
    ev = []
    t = t0
    k = 0
    while t < t1:
        ev.append((t, S.sfx_key(seed * 1000 + k), gain * rng.uniform(0.6, 1.0), rng.uniform(-0.3, 0.3)))
        t += rng.exponential(1.0 / rate) * 0.6 + 0.4 / rate
        k += 1
    return ev


def coldopen(seg, ev):
    sfx = []
    rob = ev.get("c0_robot")
    sfx += typing_clicks(ev["c0_1"].start + 0.3, ev["c0_2"].end, seed=1)
    sfx += typing_clicks(ev["c0_3"].start, ev["c0_3"].end - 0.2, seed=2)
    sfx += typing_clicks(ev["c0_4"].start, ev["c0_4"].end + 0.1, rate=20, seed=3)
    g9_end = (rob.end - 0.15) if rob else ev["c0_5"].end + 5
    sfx += typing_clicks(ev["c0_5"].start, g9_end, rate=18, seed=4, gain=0.16)
    pop_t = (rob.end + 0.05) if rob else g9_end
    sfx.append((pop_t, S.sfx_pop(), 0.55, 0.15))            # the one comic "bo"
    sfx.append((ev["c0_7"].start - 0.15, S.sfx_whoosh(0.7), 0.25, 0.0))
    sfx.append((ev["c0_9"].start, S.pulse_kick(0.6, 46), 0.45, 0.0))
    split = ev["c0_9"].start + (ev["c0_9"].end - ev["c0_9"].start) * 0.47
    sfx.append((split, S.pulse_kick(0.6, 52), 0.4, 0.0))
    sfx.append((ev["c0_9"].end + 0.35, S.pulse_kick(0.9, 40), 0.55, 0.0))   # title card
    return sfx


def photocopy(seg, ev):
    sfx = []
    s, e = ev["c1_6"].start, ev["c1_6"].end
    sfx.append((s + (e - s) * 0.05 - 0.2, S.sfx_copier(2.6), 0.30, -0.2))
    for i in (1, 2):
        sfx.append((s + (e - s) * (0.05 + 0.33 * i) - 0.2, S.sfx_copier(1.4), 0.22, -0.2))
    return sfx


def athens(seg, ev):
    sfx = []
    # same schedule as the drawing in segments_a.athens: pebble i lands when pv*2.2 - 0.07*i reaches 1
    s = ev["c4_6"].start - 0.3
    span = max(1.0, ev["c4_6"].end - ev["c4_6"].start + 0.8)
    rng = np.random.default_rng(5)
    for i in range(16):
        tt = s + span * (1 + 0.07 * i) / 2.2
        sfx.append((tt, S.sfx_pebble(i), 0.30 * rng.uniform(0.6, 1.0), -0.35 if i % 9 < 5 else 0.35))
    return sfx


def hiring(seg, ev):
    sfx = []
    s, e = ev["c5_7"].start, ev["c5_7"].end
    span = max(1.0, e - s)
    for i in range(1, 7, 2):           # each tagged resume gets the minus stamp (see segments_b.hiring)
        ph_at = (1.4 * (840 / 1240) + 0.28 * i) / 2.2
        tt = s + span * ph_at
        if s < tt < e:
            sfx.append((tt, S.pulse_kick(0.25, 90), 0.35, 0.3))
    return sfx


def flash(seg, ev):
    sfx = []
    s, e = ev["c6_10"].start, ev["c6_10"].end
    k = 0
    t = s + 0.3
    while t < e:
        sfx.append((t, S.sfx_beep(1318.5, 0.07), 0.18, 0.2))
        sfx.append((t + 0.11, S.sfx_beep(1046.5, 0.07), 0.16, 0.2))
        t += 0.9 if k < 3 else 0.6
        k += 1
    sfx.append((ev["c6_12"].start + 0.6, S.sfx_brake(), 0.7, 0.0))      # the one brake
    return sfx


def corn(seg, ev):
    dur = seg.end - seg.start
    return [(seg.start, S.sfx_wind(dur), 0.22, 0.0)]


def knight(seg, ev):
    sfx = []
    sfx.append((ev["c8_4"].start + 0.2, S.sfx_beep(880, 0.12), 0.2, 0.3))
    sfx.append((ev["c8_4"].start + 0.4, S.sfx_beep(880, 0.12), 0.2, 0.3))
    s, e = ev["c8_5"].start, ev["c8_6"].end
    t = s
    k = 0
    while t < e:
        sfx.append((t, S.sfx_clock_tick(k), 0.16, -0.2 if k % 2 else 0.2))
        t += 0.25
        k += 1
    return sfx


def transitions(segs):
    return [(s.start + 0.05, S.sfx_whoosh(0.8), 0.14, 0.0) for s in segs[1:]]


PLANS = {"coldopen": coldopen, "photocopy": photocopy, "athens": athens, "hiring": hiring, "flash": flash,
         "corn": corn, "knight": knight}
