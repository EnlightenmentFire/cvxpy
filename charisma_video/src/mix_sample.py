# -*- coding: utf-8 -*-
"""~1 minute voice sample: cold open + title + start of the Weber section, with synthesized score & SFX."""
import os, sys, json, subprocess
import numpy as np, soundfile as sf
from audio import *

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = os.path.join(HERE, "voice", "lines")
PROC = os.path.join(HERE, "voice", "proc"); os.makedirs(PROC, exist_ok=True)
OUT = sys.argv[1]

def voice(key, tempo=1.06):
    src = os.path.join(LINES, key + ".wav") if not key.startswith("en_") else os.path.join(HERE, "voice", key + ".wav")
    dst = os.path.join(PROC, f"{key}_{tempo:.2f}.wav")
    ffmpeg_proc(src, dst, tempo)
    y = load(dst)
    y = compress_pauses(y)
    return normalize_voice(y, -18.0)

seq = [  # (key, gap_after, tempo)
    ("cold_00", 0.35, 1.06), ("cold_01", 0.35, 1.06), ("cold_02", 0.55, 1.06),
    ("en_5", 1.1, 0.80),
    ("cold_04", 0.7, 1.06), ("cold_05", 0.35, 1.06), ("cold_06", 0.35, 1.06), ("cold_07", 1.4, 1.06),
    ("title_00", 0.45, 1.06), ("title_01", 1.0, 1.06),
    ("weber_00", 0.4, 1.06), ("weber_01", 0.35, 1.06), ("weber_02", 0.35, 1.06), ("weber_03", 0.8, 1.06),
]

t = 1.6
marks = {}
clips = []
for key, gap, tempo in seq:
    y = voice(key, tempo)
    if key.startswith("en_"):
        y = y * undb(-1.5)
    marks[key] = (t, t + len(y) / SR)
    clips.append((y, t))
    t += len(y) / SR + gap
total = t + 2.5
N = int(total * SR)
vbus = np.zeros(N)
for y, at in clips:
    place(vbus, y, at)

# ---------------- music
mbus = np.zeros(N)
title_t = marks["title_00"][0] - 1.2
en_t = marks["en_5"][0]
# cold open: piano motif (company theme) + very soft low pad
motif = [("D4", 0.0), ("F4", 0.9), ("A4", 1.8), ("G4", 3.0), ("F4", 3.9), ("E4", 4.8), ("D4", 6.4), ("A3", 7.6)]
for k, (nm, dt) in enumerate(motif):
    at = 1.2 + dt
    if at < en_t - 0.6:
        place(mbus, piano(note_freq(nm), 2.6, 0.16), at)
pad = strings(note_freq("D2"), en_t - 1.0, 0.07, attack=2.5, release=1.0, bright=900)
place(mbus, pad, 1.0)
# after the silence: a low cello note
after = marks["cold_04"][1] + 0.2
place(mbus, strings(note_freq("A1"), title_t - after + 0.4, 0.08, attack=1.5, release=1.2, bright=700, seed=2), after)
for k, (nm, dt) in enumerate([("A3", 0), ("D4", 1.4), ("C4", 4.2), ("A3", 5.6)]):
    if after + 1.5 + dt < title_t - 1:
        place(mbus, piano(note_freq(nm), 2.6, 0.12), after + 1.5 + dt)
# title: boom + strings swell
place(mbus, low_boom(0.45), title_t)
chord = ["D2", "A2", "D3", "F3", "A3"]
title_len = marks["weber_00"][0] - title_t + 0.8
for k, nm in enumerate(chord):
    place(mbus, strings(note_freq(nm), title_len, 0.06 if k else 0.09, attack=1.8, release=1.6, bright=1500, seed=k), title_t)
# weber: slow progression Dm – Bb – Gm – A
wt = marks["weber_00"][0] - 0.3
prog = [["D2", "A2", "D3", "F3"], ["Bb1", "F2", "D3", "F3"], ["G1", "D2", "Bb2", "D3"], ["A1", "E2", "C#3", "E3"]]
seg_len = (total - wt) / 4 + 1.2
for i, ch in enumerate(prog):
    for k, nm in enumerate(ch):
        place(mbus, strings(note_freq(nm), seg_len, 0.07 if k else 0.09, attack=1.6, release=1.6, bright=1200, seed=10 + i * 4 + k),
              wt + i * (seg_len - 1.2))
mbus = reverb(mbus, 2.6, 0.32)[:N]
mbus = duck(mbus, vbus, -10)

# ---------------- sfx
sbus = np.zeros(N)
place(sbus, room_tone(title_t + 0.5), 0)
place(sbus, chair_scrape(0.22), 0.5)
place(sbus, chair_scrape(0.10, seed=8), marks["cold_04"][0] - 0.3)
sbus = reverb(sbus, 0.8, 0.2, seed=4)[:N]

mix = vbus + mbus * 0.9 + sbus
peak = np.max(np.abs(mix))
if peak > undb(-1.0):
    mix = mix / peak * undb(-1.0)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sf.write(OUT + ".wav", mix.astype(np.float32), SR)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT + ".wav", "-c:a", "aac", "-b:a", "192k", OUT + ".m4a"], check=True)
json.dump({k: [round(a, 2), round(b, 2)] for k, (a, b) in marks.items()}, open(OUT + "_marks.json", "w"), indent=1)
print("dur", round(total, 1), "voice rms dB", round(db(speech_rms(vbus)), 1), "music rms dB", round(db(np.sqrt(np.mean(mbus ** 2))), 1))
