"""Per-segment sound design: which music bed, which effects, at which cue."""
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
    sfx, music = [], []
    rob = ev.get("c0_robot")
    # typing windows (match segments.coldopen)
    sfx += typing_clicks(ev["c0_1"].start + 0.3, ev["c0_2"].end, seed=1)
    sfx += typing_clicks(ev["c0_3"].start, ev["c0_3"].end - 0.2, seed=2)
    sfx += typing_clicks(ev["c0_4"].start, ev["c0_4"].end + 0.1, rate=20, seed=3)
    g9_end = (rob.end - 0.15) if rob else ev["c0_5"].end + 5
    sfx += typing_clicks(ev["c0_5"].start, g9_end, rate=18, seed=4, gain=0.16)
    pop_t = (rob.end + 0.05) if rob else g9_end
    sfx.append((pop_t, S.sfx_pop(), 0.55, 0.15))            # the one comic "bo"
    sfx.append((ev["c0_7"].start - 0.15, S.sfx_whoosh(0.7), 0.35, 0.0))
    sfx.append((ev["c0_9"].start, S.pulse_kick(0.6, 46), 0.5, 0.0))
    split = ev["c0_9"].start + (ev["c0_9"].end - ev["c0_9"].start) * 0.47
    sfx.append((split, S.pulse_kick(0.6, 52), 0.45, 0.0))
    title_t = ev["c0_9"].end + 0.35
    sfx.append((title_t, S.sfx_sting(), 0.6, 0.0))
    # music: dark terminal drone until the card, then a soft pad under the thesis
    music.append((seg.start, ev["c0_7"].start + 0.5, S.pad([S.midi(38), S.midi(45), S.midi(50)],
                                                           ev["c0_7"].start + 1 - seg.start, cutoff=380)))
    music.append((ev["c0_7"].start, title_t + 3.0, S.pad([S.midi(50), S.midi(53), S.midi(57), S.midi(62)],
                                                       title_t + 3.0 - ev["c0_7"].start, cutoff=900)))
    return sfx, music


def photocopy(seg, ev):
    sfx, music = [], []
    music.append((seg.start, seg.end + 0.5, S.bed_tech(seg.end - seg.start + 1.0, bpm=88)))
    if "c1_6" in ev:
        sfx.append((ev["c1_6"].start + 0.3, S.sfx_copier(2.4), 0.35, -0.2))
    return sfx, music


PLANS = {"coldopen": coldopen, "photocopy": photocopy}
