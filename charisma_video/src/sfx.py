# -*- coding: utf-8 -*-
"""Sound-effects bus from the timeline (all synthesized; no violent sounds)."""
import os, json, sys
import numpy as np, soundfile as sf
from audio import *
from director import Director, lamp_schedule

HERE = os.path.dirname(os.path.abspath(__file__))

def low_note(freq=55.0, amp=0.28, dur=2.4):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.1 * np.sin(6 * np.pi * freq * t)
    return y * np.exp(-t * 1.6) * np.clip(t / 0.015, 0, 1) * amp

def clink(amp=0.08):
    n = int(1.6 * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * a for f, d, a in ((880, 3, 1), (1320, 4, .5), (2210, 6, .3)))
    return y * amp

def build(out):
    d = Director(os.path.join(HERE, "timeline.json"))
    tl = d.tl
    N = int(tl["total"] * SR) + SR
    bus = np.zeros(N)
    S = {s.d["id"]: s for s in d.segs}
    cold = S["cold"]
    place(bus, room_tone(S["title"].t0 + 0.5), 0)
    place(bus, chair_scrape(0.22), 0.5)
    place(bus, chair_scrape(0.10, seed=8), cold.t0 + cold.cue("look_up") - 0.2)
    r = S["routine"]
    place(bus, low_boom(0.35, 48, 2.6), r.t0 + r.cue("extinguish") + 0.3)
    place(bus, low_boom(0.30, 55, 2.4), r.t0 + r.cue("split") + 0.2)
    notes = [55.0, 49.0, 46.25, 41.2, 36.7, 32.7]   # A1 G1 F#1 E1 D1 C1, one low note per road
    for i in range(6):
        place(bus, low_note(notes[i] * 2, 0.22), r.t0 + r.cue(f"road{i + 1}") + 0.05)
    e = S["elect"]
    for k in range(5):
        place(bus, tiles(0.22, seed=20 + k, count=6), e.t0 + e.cue("roof") + 0.3 + k * 1.0)
    place(bus, clink(0.07), e.t0 + e.cue("key") + 1.6)
    o = S["ottoman"]
    t0, dur = lamp_schedule(o)
    for i in range(19):
        place(bus, puff(0.10, seed=40 + i), o.t0 + t0 + (i + 0.6) / 19 * dur)
    bus = reverb(bus, 1.2, 0.18, seed=6)[:N]
    sf.write(out, bus.astype(np.float32), SR)
    return bus

if __name__ == "__main__":
    build(sys.argv[1])
