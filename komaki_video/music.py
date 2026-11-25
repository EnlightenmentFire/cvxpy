# -*- coding: utf-8 -*-
"""Original score for 小牧长久手, generated per scene and rendered with fluidsynth + FluidR3_GM (MIT licence).
Palette: taiko / timpani, low strings, horns, shakuhachi & koto colour, pizzicato + bells for the diplomacy part.
Key D minor with miyako-bushi colour (D Eb G A Bb). Each scene gets a section as long as the scene; sections crossfade.
Output: WORK/stems/music.wav (48 kHz stereo).   usage: python music.py
"""
import os, json, subprocess, math
import numpy as np, soundfile as sf
import mido

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SR = 48000
OUT = f"{WORK}/music"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{WORK}/stems", exist_ok=True)

STR, TREM, CELLO, BASS, HORN, BRASS, TIMP, CHOIR = 48, 44, 42, 43, 60, 61, 47, 52
TAIKO, SHAKU, KOTO, PIZZ, BELLS, HARP = 116, 77, 107, 45, 14, 46
D = 62
PROG_DARK = [(0, "m"), (-4, "M"), (-2, "M"), (0, "m")]         # Dm Bb C Dm
PROG_DRIVE = [(0, "m"), (-2, "M"), (-4, "M"), (-5, "M")]       # Dm C Bb A
PROG_PLUCK = [(0, "m"), (-7, "m"), (-4, "M"), (-5, "M")]       # Dm Gm Bb A
PROG_FINAL = [(0, "m"), (-4, "M"), (-2, "M"), (3, "M")]        # Dm Bb C F
MIYAKO = [0, 1, 5, 7, 8, 12]                                   # D Eb G A Bb D'

MOOD = {  # scene -> (style, bpm, intensity)
    "s00": ("hook", 90, 0.95), "s01": ("drive", 90, 0.62), "s02": ("map", 80, 0.42), "s03": ("standoff", 64, 0.32),
    "s04": ("build", 84, 0.55), "s05": ("battle", 100, 0.90), "s06": ("battle", 100, 0.85), "s07": ("climax", 104, 1.0),
    "s08": ("dark", 64, 0.32), "s09": ("pluck", 84, 0.45), "s10": ("pluck", 84, 0.45), "s11": ("bell", 60, 0.33),
    "s12": ("pluck", 84, 0.50), "s13": ("dark", 60, 0.30), "s14": ("finale", 70, 0.70),
}


def chord(root, q):
    return [root, root + (3 if q == "m" else 4), root + 7]


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
    for ch, p in ((0, STR), (1, CELLO), (2, BASS), (3, HORN), (4, BRASS), (5, TIMP), (6, TREM), (7, SHAKU), (8, KOTO),
                  (10, TAIKO), (11, PIZZ), (12, BELLS), (13, CHOIR)):
        s.program(ch, p)
    prog = {"hook": PROG_DRIVE, "drive": PROG_DRIVE, "map": PROG_DARK, "standoff": PROG_DARK, "build": PROG_DRIVE,
            "battle": PROG_DRIVE, "climax": PROG_DRIVE, "dark": PROG_DARK, "pluck": PROG_PLUCK, "bell": PROG_DARK,
            "finale": PROG_FINAL}[style]
    v = 48 + 52 * inten
    O = offset_beats
    for b in range(bars):
        r, q = prog[b % 4]
        c = chord(D + r - 12, q)
        B = O + b * 4
        grow = min(1.0, b / max(bars - 1, 1))
        # pads
        if style in ("standoff", "dark", "bell"):
            if b % 2 == 0:
                s.note(1, B, 8, c[0] - 12, v * 0.55)
                s.note(0, B, 8, c[0], v * 0.40); s.note(0, B, 8, c[2], v * 0.35)
        elif style != "pluck":
            for p in c:
                s.note(0, B, 4, p, v * 0.50 + 12 * grow)
            s.note(0, B, 4, c[0] + 12, v * 0.40)
        s.note(2, B, 4, D + r - 36 + (12 if D + r - 36 < 28 else 0), v * (0.5 if style in ("pluck", "bell") else 0.7))
        # cello ostinato
        if style in ("map", "build", "drive", "battle", "climax", "hook"):
            pat = [0, 7, 12, 7, 0, 7, 12, 7] if style == "map" else [0, 0, 7, 0, 3 if q == "m" else 4, 0, 7, 12]
            for k, iv in enumerate(pat):
                s.note(1, B + k * 0.5, 0.45, D + r - 24 + iv, v * (0.5 if style == "map" else 0.72 + 0.15 * grow * (style == "build")) * (1.1 if k % 2 == 0 else 0.85))
        # taiko (GM 116) on channel 10 as pitched taiko + GM drum kit kicks on 9
        if style in ("hook", "drive", "battle", "climax", "finale"):
            pat = [(0, 1.0), (1.5, 0.6), (2, 0.9), (3, 0.6), (3.5, 0.7)] if style != "finale" else [(0, 1.0), (2, 0.7)]
            for bt, vv in pat:
                s.note(10, B + bt, 0.8, 50, v * 0.95 * vv)
            s.note(9, B, 0.5, 35, v * 0.9)
            if style in ("battle", "climax"):
                s.note(9, B + 2, 0.5, 35, v * 0.8)
                for k in range(4):
                    s.note(10, B + 3 + k * 0.25, 0.2, 55, v * (0.45 + 0.1 * k))
            if b % 4 == 3:
                for k in range(8):
                    s.note(5, B + 2 + k * 0.25, 0.2, D - 26, v * (0.4 + 0.07 * k))
        elif style in ("map", "build"):
            s.note(10, B, 1.0, 48, v * (0.75 if style == "build" else 0.6))
            if style == "build":
                s.note(10, B + 2, 1.0, 48, v * (0.4 + 0.45 * grow))
                if grow > 0.5:
                    s.note(10, B + 3, 0.5, 52, v * 0.5 * grow); s.note(10, B + 3.5, 0.5, 52, v * 0.6 * grow)
        elif style == "standoff" and b % 4 == 0:
            s.note(10, B, 2, 45, v * 0.7)
        # strings tremolo tension
        if style in ("battle", "climax", "build", "hook") and b % 2 == 0:
            for p in c:
                s.note(6, B, 8, p + 12, v * (0.42 if style != "build" else 0.30 + 0.2 * grow))
        # horn calls (miyako-bushi motif)
        motif = [(0, 1.5, 0), (1.5, 0.5, 1), (2, 1.5, 7), (3.5, 0.5, 8), (4, 3, 7)]
        if style in ("hook", "battle", "climax", "drive", "finale") and b % 4 in ((0, 2) if style != "drive" else (2,)):
            for bt, du, iv in motif:
                s.note(3, B + bt, du, D - 12 + iv, v * 0.85)
            if style in ("climax", "hook", "finale"):
                for bt, du, iv in motif:
                    s.note(4, B + bt, du, D + iv, v * 0.6)
        # shakuhachi phrase (sparse, breathy colour)
        if style in ("standoff", "dark", "map") and b % 4 == 1:
            st = rng.integers(0, 3)
            ph = [MIYAKO[(st + k) % len(MIYAKO)] for k in (0, 1, 3, 2)]
            for k, iv in enumerate(ph):
                s.note(7, B + k * 1.5, 1.4 if k < 3 else 3, D + iv, v * 0.55)
        # koto / pizzicato pluck ostinato for diplomacy
        if style == "pluck":
            pat = [0, 7, 12, 8, 7, 12, 5, 7]
            for k, iv in enumerate(pat):
                s.note(11, B + k * 0.5, 0.4, D + r - 12 + iv, v * (0.7 if k % 2 == 0 else 0.5))
            if b % 2 == 0:
                for k, iv in enumerate((12, 8, 7, 5)):
                    s.note(8, B + 2 + k * 0.5, 0.5, D + iv, v * 0.45)
            if b % 4 == 0:
                s.note(12, B, 4, D + 12 + r, v * 0.45)
        if style == "bell" and b % 2 == 0:
            s.note(12, B, 6, D + 12, v * 0.5); s.note(12, B + 3, 6, D + 7, v * 0.35)
        if style == "finale" and b % 2 == 1:
            for p in c:
                s.note(13, B, 4, p + 12, v * 0.35)
    if style == "hook":
        s.note(10, O, 2, 47, 127); s.note(9, O, 2, 35, 127); s.note(5, O, 2, D - 26, 127); s.note(9, O, 2, 49, 100)
        for p in chord(D - 12, "m"):
            s.note(4, O, 2.5, p, 118)
    if style == "finale":
        # final cadence: D major chord swell at the end
        end = beats - 4
        for p in (D - 12, D - 12 + 4, D - 12 + 7, D):
            s.note(0, end, 6, p, v * 0.8)
        s.note(10, end, 2, 47, 120); s.note(5, end, 3, D - 26, 110)
    return s


def render_midi(mfn, wfn):
    subprocess.run(["fluidsynth", "-ni", "-g", "0.7", "-r", str(SR), "-F", wfn, SF2, mfn], check=True, capture_output=True)


HOOK_HIT = 1.15   # = scenes.VOLLEY_T : music enters on the volley


def build():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    out = np.zeros((int((total + 3) * SR), 2), np.float32)
    XF = 2.0
    for i, sc in enumerate(tl["scenes"]):
        style, bpm, inten = MOOD[sc["id"]]
        start = sc["start"] + (HOOK_HIT if i == 0 else 0)
        dur = sc["end"] - start + XF + 2
        song = compose(style, bpm, inten, dur, i)
        mfn = f"{OUT}/{sc['id']}.mid"; wfn = f"{OUT}/{sc['id']}.wav"
        song.save(mfn); render_midi(mfn, wfn)
        x, sr = sf.read(wfn, always_2d=True)
        x = x.astype(np.float32)
        n = int(dur * SR)
        x = x[:n] if len(x) >= n else np.pad(x, ((0, n - len(x)), (0, 0)))
        fr = x[: len(x) // 2400 * 2400].mean(1).reshape(-1, 2400)
        rms = np.sqrt((fr ** 2).mean(1)); act = rms[rms > rms.max() * 0.05]
        cur = 20 * np.log10(np.sqrt((act ** 2).mean()) + 1e-9) if len(act) else -60
        x *= 10 ** (((-24 + 7 * inten) - cur) / 20)
        f = int(XF * SR)
        if i > 0:
            x[:f] *= np.linspace(0, 1, f)[:, None]
        x[-f:] *= np.linspace(1, 0, f)[:, None]
        a = int(max(start - (XF / 2 if i else 0), 0) * SR)
        b = min(len(out), a + len(x))
        out[a:b] += x[:b - a]
        print(sc["id"], style, f"{dur:.1f}s", flush=True)
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
