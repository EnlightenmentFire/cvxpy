# -*- coding: utf-8 -*-
"""Original score per scene: taiko / shakuhachi / koto / strings / low brass, D minor with miyako-bushi colour; fluidsynth + FluidR3_GM (MIT).
Each scene gets a section whose length = scene duration; sections are crossfaded. Output: WORK/stems/music.wav (48 kHz stereo).
usage: python music.py
"""
import os, sys, json, subprocess, math
import numpy as np, soundfile as sf
import mido

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SR = 48000
OUT = f"{WORK}/music"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{WORK}/stems", exist_ok=True)

# GM programs
STR, TREM, CELLO, BASS, HORN, BRASS, TIMP, CHOIR = 48, 44, 42, 43, 60, 61, 47, 52
TAIKO, SHAKU, KOTO = 116, 77, 107
D = 62  # D4
# miyako-bushi flavoured D minor: D Eb G A Bb ; chords
PROG_A = [(0, "m"), (-4, "M"), (-7, "m"), (-5, "M")]          # Dm Bb Gm A
PROG_B = [(0, "m"), (1, "M"), (-2, "M"), (0, "m")]            # Dm Eb C Dm
PROG_C = [(0, "m"), (-7, "m"), (-4, "M"), (-5, "M")]          # Dm Gm Bb A
PENTA = [0, 1, 5, 7, 8, 12, 13, 17, 19]                       # D Eb G A Bb D' Eb' G' A'

MOOD = {  # scene -> (style, bpm, intensity 0..1)
    "s00": ("hook", 80, 1.0), "s01": ("drive", 84, 0.75), "s02": ("map", 76, 0.45), "s03": ("tension", 72, 0.45),
    "s04": ("tension", 80, 0.6), "s05": ("work", 92, 0.6), "s06": ("storm", 76, 0.65), "s07": ("map", 70, 0.35),
    "s08": ("drive", 84, 0.75), "s09": ("tension", 84, 0.7), "s10": ("climax", 88, 1.0), "s11": ("drive", 84, 0.7),
    "s12": ("dark", 64, 0.45), "s13": ("elegy", 58, 0.5), "s14": ("map", 70, 0.35), "s15": ("resolve", 64, 0.55),
}


def chord(root, q):
    third = 3 if q == "m" else 4
    return [root, root + third, root + 7]


class Song:
    def __init__(self, bpm):
        self.mid = mido.MidiFile(ticks_per_beat=480)
        self.bpm = bpm
        self.ev = {}
        self.prog = {}

    def t(self, beats):
        return int(beats * 480)

    def note(self, ch, beat, dur, pitch, vel):
        vel = int(max(1, min(127, vel)))
        self.ev.setdefault(ch, []).append((self.t(beat), mido.Message("note_on", channel=ch, note=int(pitch), velocity=vel)))
        self.ev[ch].append((self.t(beat + dur) - 1, mido.Message("note_off", channel=ch, note=int(pitch), velocity=0)))

    def program(self, ch, prog):
        self.prog[ch] = prog

    def save(self, fn):
        tr0 = mido.MidiTrack(); self.mid.tracks.append(tr0)
        tr0.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm), time=0))
        for ch, evs in self.ev.items():
            tr = mido.MidiTrack(); self.mid.tracks.append(tr)
            if ch != 9:
                tr.append(mido.Message("program_change", channel=ch, program=self.prog.get(ch, 0), time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=80, time=0))
            evs.sort(key=lambda e: (e[0], e[1].type == "note_on"))
            last = 0
            for tk, m in evs:
                tr.append(m.copy(time=tk - last)); last = tk
        self.mid.save(fn)


def compose(style, bpm, inten, seconds, seed, offset_beats=0.0):
    rng = np.random.default_rng(seed)
    s = Song(bpm)
    beats = seconds * bpm / 60.0
    bars = int(math.ceil(beats / 4)) + 1
    for ch, pg in [(0, STR), (1, CELLO), (2, BASS), (3, HORN), (4, BRASS), (5, TIMP), (6, TREM), (7, SHAKU), (8, CHOIR),
                   (10, TAIKO), (11, KOTO)]:
        s.program(ch, pg)
    prog = {"hook": PROG_C, "drive": PROG_A, "map": PROG_B, "dark": PROG_C, "tension": PROG_A, "work": PROG_A,
            "storm": PROG_C, "climax": PROG_C, "elegy": PROG_B, "resolve": PROG_B}[style]
    v = 48 + 52 * inten
    O = offset_beats
    for b in range(bars):
        r, q = prog[b % 4]
        c = chord(D + r - 12, q)
        B = O + b * 4
        grow = min(1.0, b / max(bars - 1, 1))
        if B + 4 > beats + 4:
            break
        # strings pad
        for p in c:
            s.note(0, B, 4, p, v * 0.5 + 10 * grow)
        s.note(0, B, 4, c[0] + 12, v * 0.4)
        s.note(2, B, 4, D + r - 36 + (12 if D + r - 36 < 28 else 0), v * 0.7)
        if style in ("drive", "tension", "climax", "hook", "storm", "work"):
            pat = [0, 0, 7, 0, 3 if q == "m" else 4, 0, 7, 12]
            for k, iv in enumerate(pat):
                s.note(1, B + k * 0.5, 0.45, D + r - 24 + iv, v * 0.7 * (1.1 if k % 2 == 0 else 0.8))
        if style == "map":
            for k, iv in enumerate([0, 7, 12, 7]):
                s.note(11, B + k, 0.9, D + r - 12 + iv, v * 0.55)
        # taiko: big hits; patterns by style
        if style in ("hook", "climax", "drive", "storm", "work", "tension"):
            if style in ("hook", "climax"):
                pat = [(0, 1.0), (1.5, 0.6), (2, 0.9), (3, 0.6), (3.5, 0.7)]
            elif style == "work":
                pat = [(0, 0.9), (1, 0.6), (2, 0.8), (3, 0.6), (3.5, 0.5)]
            elif style == "tension":
                pat = [(0, 0.8), (2.5, 0.5)]
            else:
                pat = [(0, 0.9), (2, 0.7), (3.5, 0.5)]
            for bt, vv in pat:
                s.note(10, B + bt, 0.9, 38 if bt == 0 else 45, v * 0.95 * vv)
            if b % 4 == 3 and style in ("hook", "climax", "storm", "drive"):
                for k in range(8):
                    s.note(10, B + 2 + k * 0.25, 0.2, 45, v * (0.45 + 0.07 * k))
            if style in ("hook", "climax"):
                s.note(5, B, 1, D - 26 if D - 26 > 36 else D - 14, v * 0.85)
        if style == "storm":
            s.note(5, B, 4, D - 26, v * 0.5)
            for k in range(16):
                s.note(5, B + k * 0.25, 0.22, D - 26, v * (0.25 + 0.2 * (k / 16)))
        if style in ("hook", "tension", "climax", "storm", "dark") and b % 2 == 0:
            for p in c:
                s.note(6, B, 8, p + 12, v * 0.40)
        # conch-like horn calls (low brass): D - A - D
        if style in ("hook", "climax", "drive") and b % 4 == 0:
            for bt, du, iv in [(0, 2.5, 0), (2.5, 1.5, 7), (4, 4, 12)]:
                s.note(3, B + bt, du, D - 24 + r + iv, v * 0.85)
            if style in ("climax", "hook"):
                for bt, du, iv in [(0, 2.5, 0), (2.5, 1.5, 7), (4, 4, 12)]:
                    s.note(4, B + bt, du, D - 12 + r + iv, v * 0.55)
        # shakuhachi: long, breathy pentatonic phrases
        if style in ("map", "dark", "elegy", "resolve", "tension", "storm") and b % 2 == 0:
            ph = rng.choice(len(PENTA) - 3)
            notes = [PENTA[ph + k] for k in rng.permutation(3)]
            if style in ("elegy", "dark"):
                notes = sorted(notes, reverse=True)
            tb = 0.0
            for k, iv in enumerate(notes):
                du = [3.0, 1.0, 4.0][k]
                s.note(7, B + tb, du, D + iv, v * (0.75 if style != "tension" else 0.5))
                tb += du
        if style in ("elegy", "resolve") and b % 2 == 1:
            for p in c:
                s.note(8, B, 4, p + 12, v * 0.30)
            for k, iv in enumerate([12, 7, 5, 0]):
                s.note(11, B + k * 0.75, 0.7, D + r + iv, v * 0.45)
    if style == "hook":
        s.note(10, O, 2, 38, 127); s.note(5, O, 2, D - 26, 127)
        for p in chord(D - 12, "m"):
            s.note(4, O, 2.5, p, 118)
    return s


def render_midi(mfn, wfn):
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", wfn, SF2, mfn], check=True, capture_output=True)


def build():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    out = np.zeros((int((total + 3) * SR), 2), np.float32)
    XF = 2.0
    for i, sc in enumerate(tl["scenes"]):
        style, bpm, inten = MOOD[sc["id"]]
        dur = sc["end"] - sc["start"] + XF + 2
        off = (1.7 * bpm / 60.0) if sc["id"] == "s00" else 0.0     # hook: rain + flood first, taiko enters ~1.7 s
        song = compose(style, bpm, inten, dur, i, off)
        mfn = f"{OUT}/{sc['id']}.mid"; wfn = f"{OUT}/{sc['id']}.wav"
        song.save(mfn); render_midi(mfn, wfn)
        x, sr = sf.read(wfn, always_2d=True)
        x = x.astype(np.float32)
        n = int(dur * SR)
        x = x[:n] if len(x) >= n else np.pad(x, ((0, n - len(x)), (0, 0)))
        # level each section by intensity (active RMS)
        fr = x[: len(x) // 2400 * 2400].mean(1).reshape(-1, 2400)
        rms = np.sqrt((fr ** 2).mean(1)); act = rms[rms > rms.max() * 0.05]
        cur = 20 * np.log10(np.sqrt((act ** 2).mean()) + 1e-9) if len(act) else -60
        x *= 10 ** (((-24 + 7 * inten) - cur) / 20)
        # fades
        f = int(XF * SR)
        if i > 0:
            x[:f] *= np.linspace(0, 1, f)[:, None]
        x[-f:] *= np.linspace(1, 0, f)[:, None]
        a = int(max(sc["start"] - (XF / 2 if i else 0), 0) * SR)
        b = min(len(out), a + len(x))
        out[a:b] += x[:b - a]
        print(sc["id"], style, f"{dur:.1f}s", flush=True)
    # end: let last section ring out, fade over final 3 s
    e = int(total * SR)
    out = out[:e + int(1.0 * SR)]
    f = int(4.0 * SR)
    out[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    peak = np.abs(out).max()
    if peak > 0.95:
        out = out / peak * 0.95
    sf.write(f"{WORK}/stems/music.wav", out, SR, subtype="FLOAT")
    print("music", len(out) / SR)


if __name__ == "__main__":
    build()
