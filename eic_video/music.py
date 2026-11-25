# -*- coding: utf-8 -*-
"""Original underscore, composed procedurally and rendered with FluidSynth + FluidR3_GM (MIT-licensed SoundFont).
Documentary / power-and-organisation mood: D minor, strings + low ostinato + horns + timpani, follows the picture sections.
usage: python music.py  -> /tmp/claude-0/work/audio/music.wav (48 kHz stereo)
"""
import json, os, subprocess, math
import numpy as np
import mido

WORK = "/tmp/claude-0/work"
TL = json.load(open(f"{WORK}/timeline.json"))
BPM = 80
BEAT = 60 / BPM
BAR = 4 * BEAT
TPB = 480
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

# group -> (mood, level 0..3)
SECTION = {
    "battle_open": ("epic", 3), "teaser_diwani": ("epic", 2), "teaser_army": ("epic", 2), "teaser_hq": ("tense", 1.5),
    "teaser_question": ("tense", 1.5), "teaser_nodes": ("tense", 2), "teaser_smith": ("noble", 1.5),
    "charter": ("noble", 1), "world_route": ("noble", 1.5), "shares": ("noble", 1), "voc": ("noble", 1), "powers": ("tense", 1.5),
    "debate": ("tense", 1),
    "india_forts": ("noble", 1.5), "factory": ("noble", 1), "mughal_break": ("tense", 2), "dupleix": ("tense", 1.5),
    "mech1": ("tense", 1), "dastak": ("tense", 1), "bengal_1756": ("tense", 2),
    "conspiracy": ("tense", 1.5), "battle_map": ("epic", 3), "spoils": ("noble", 1.5),
    "atm": ("tense", 1.5), "buxar": ("epic", 2.5), "diwani_tent": ("noble", 2), "ledger": ("tense", 1.5), "mech2": ("tense", 1),
    "dual": ("tense", 1), "smith1": ("noble", 1),
    "famine": ("somber", 0.5), "hastings_doc": ("somber", 0.5), "flows": ("tense", 1.5), "crisis": ("tense", 2),
    "clive_q": ("tense", 1), "smith2": ("somber", 1), "mencius": ("somber", 1), "lag": ("tense", 1.5),
    "westminster": ("noble", 2), "unwinding": ("epic", 2), "synth": ("noble", 1), "lesson": ("noble", 1),
    "final": ("noble", 2.5),
}

PROG = {
    "epic": [("D", "m"), ("Bb", ""), ("F", ""), ("C", ""), ("D", "m"), ("Bb", ""), ("G", "m"), ("A", "")],
    "tense": [("D", "m"), ("D", "m"), ("Bb", ""), ("A", ""), ("G", "m"), ("G", "m"), ("Bb", ""), ("A", "")],
    "somber": [("D", "m"), ("G", "m"), ("Bb", ""), ("A", ""), ("D", "m"), ("F", ""), ("G", "m"), ("A", "")],
    "noble": [("Bb", ""), ("F", ""), ("G", "m"), ("D", "m"), ("Bb", ""), ("C", ""), ("F", ""), ("A", "")],
}
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11, "Bb": 10}


def chord(root, q, base=48):
    r = NOTE[root]
    third = 3 if q == "m" else 4
    return [base + r, base + r + 7, base + 12 + r, base + 12 + r + third, base + 12 + r + 7]


def section_at(t):
    gs = TL["groups"]
    cur = gs[0]
    for g in gs:
        if g["start"] <= t:
            cur = g
    return SECTION.get(cur["name"], ("noble", 1))


class Track:
    def __init__(self, ch, program, name):
        self.ch, self.program, self.name = ch, program, name
        self.ev = []  # (tick, msg)

    def note(self, t, dur, n, vel):
        if vel <= 0:
            return
        a = int(round(t / BEAT * TPB)); b = int(round((t + dur) / BEAT * TPB))
        self.ev.append((a, mido.Message("note_on", channel=self.ch, note=int(n), velocity=int(max(1, min(127, vel))))))
        self.ev.append((b, mido.Message("note_off", channel=self.ch, note=int(n), velocity=0)))

    def cc(self, t, ctl, val):
        self.ev.append((int(round(t / BEAT * TPB)), mido.Message("control_change", channel=self.ch, control=ctl, value=int(val))))

    def to_track(self):
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=self.name))
        if self.ch != 9:
            tr.append(mido.Message("program_change", channel=self.ch, program=self.program, time=0))
        last = 0
        for tick, msg in sorted(self.ev, key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1)):
            tr.append(msg.copy(time=tick - last)); last = tick
        return tr


def compose():
    total = TL["total"]
    end_music = total - 0.5
    strings = Track(0, 48, "strings"); low = Track(1, 42, "cello"); horn = Track(2, 60, "horns")
    timp = Track(3, 47, "timpani"); taiko = Track(4, 116, "taiko"); piano = Track(5, 0, "piano")
    choir = Track(6, 52, "choir"); bass = Track(7, 43, "contrabass"); brass = Track(8, 61, "brass")
    for tr, v in ((strings, 92), (low, 80), (horn, 78), (timp, 90), (taiko, 92), (piano, 72), (choir, 64), (bass, 84), (brass, 70)):
        tr.cc(0, 7, v); tr.cc(0, 91, 70)
    nbars = int(end_music / BAR)
    idx = {k: 0 for k in PROG}
    prev_mood = None
    rng = np.random.default_rng(7)
    mel_pat = [0, 2, 3, 2, 4, 3, 1, 0]
    for b in range(nbars):
        t = b * BAR
        mood, lev = section_at(t + 0.1)
        if mood != prev_mood:
            idx[mood] = 0
        prev_mood = mood
        prog = PROG[mood]
        root, q = prog[(idx[mood] // 2) % len(prog)] if mood == "somber" else prog[idx[mood] % len(prog)]
        idx[mood] += 1
        ch = chord(root, q)
        fade_out = max(0.0, min(1.0, (end_music - t) / 12.0))
        k = fade_out
        # strings pad (always)
        sv = (46 + 14 * lev) * k
        for n in ch[1:]:
            strings.note(t, BAR * 0.98, n + 12, sv)
        bass.note(t, BAR * 0.98, ch[0] - 12, (50 + 12 * lev) * k)
        # low ostinato (level >= 1)
        if lev >= 1:
            for e in range(8):
                acc = 1.15 if e % 4 == 0 else (0.9 if e % 2 else 1.0)
                n = ch[0] if e % 4 != 3 else ch[1]
                low.note(t + e * BEAT / 2, BEAT / 2 * 0.8, n, (40 + 16 * lev) * acc * k)
        # horns melody (level >= 2): long tones on chord tones
        if lev >= 2:
            tones = [ch[2], ch[3], ch[4], ch[3] + 12 - 12]
            p = mel_pat[b % len(mel_pat)]
            m1 = ch[2 + (p % 3)] + 12
            horn.note(t, BEAT * 2.9, m1, 58 + 12 * (lev - 2))
            horn.note(t + BEAT * 3, BEAT * 0.95, ch[2 + ((p + 1) % 3)] + 12, 52 + 10 * (lev - 2))
        # brass swell at section level 3 every 4 bars
        if lev >= 2.5 and b % 4 == 0:
            for n in ch[1:4]:
                brass.note(t, BAR * 1.9, n, 60)
        # timpani
        if lev >= 2:
            timp.note(t, BEAT, ch[0] - 12 + 12 if ch[0] < 45 else ch[0] - 12, 70 + 14 * (lev - 2))
            if lev >= 3:
                timp.note(t + BEAT * 2.5, BEAT * 0.5, ch[0] - 12, 60)
                timp.note(t + BEAT * 3, BEAT * 0.5, ch[0] - 12, 66)
        if lev >= 3:
            for e in (0, 1.5, 2, 3, 3.5):
                taiko.note(t + e * BEAT, BEAT * 0.5, 45 if e in (0, 2) else 52, 92 if e == 0 else 70)
        # piano (somber/noble low levels): broken chord
        if mood in ("somber",) or (mood == "noble" and lev <= 1):
            for e, n in enumerate([ch[0] + 12, ch[1] + 12, ch[3] + 12, ch[4] + 12]):
                piano.note(t + e * BEAT, BEAT * 1.8, n, (44 if mood == "somber" else 38) * k)
        # choir on finale
        if mood == "noble" and lev >= 2.5:
            for n in ch[2:]:
                choir.note(t, BAR * 0.98, n + 12, 58 * k)
    # opening hit: everything sforzando at t=0
    for n in chord("D", "m")[0:3]:
        brass.note(0.0, 2.5, n, 100)
    timp.note(0.0, 2.0, 38, 120); taiko.note(0.0, 1.5, 45, 127); taiko.note(0.02, 1.5, 52, 110)
    # final chord at the end of the last quote
    tend = TL["lines"][-1]["end"]
    for n in chord("D", "m"):
        strings.note(tend + 0.2, 4.0, n + 12, 70); choir.note(tend + 0.2, 4.0, n + 12, 50)
    bass.note(tend + 0.2, 4.0, 26, 70); timp.note(tend + 0.2, 2.0, 38, 80)
    mid = mido.MidiFile(ticks_per_beat=TPB)
    meta = mido.MidiTrack(); meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM)))
    mid.tracks.append(meta)
    for tr in (strings, low, horn, timp, taiko, piano, choir, bass, brass):
        mid.tracks.append(tr.to_track())
    os.makedirs(f"{WORK}/audio", exist_ok=True)
    mid.save(f"{WORK}/audio/music.mid")
    return f"{WORK}/audio/music.mid"


if __name__ == "__main__":
    m = compose()
    out = f"{WORK}/audio/music_raw.wav"
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-R", "1", "-C", "1", "-F", out, "-r", "48000", SF2, m], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("music rendered", out)
