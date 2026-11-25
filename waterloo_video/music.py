# -*- coding: utf-8 -*-
"""Original score, generated per scene: drums / horns / strings in D minor, rendered with fluidsynth + FluidR3_GM (MIT).
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
STR, TREM, CELLO, BASS, HORN, BRASS, TPT, TIMP, CHOIR = 48, 44, 42, 43, 60, 61, 56, 47, 52
D = 62  # D4
# progressions (root offsets from D, minor/major)
PROG_A = [(0, "m"), (-4, "M"), (-7, "m"), (-5, "M")]          # Dm Bb Gm A
PROG_B = [(0, "m"), (3, "M"), (-2, "M"), (-5, "M")]           # Dm F C A
PROG_C = [(0, "m"), (-7, "m"), (-4, "M"), (-5, "M")]          # Dm Gm Bb A

MOOD = {  # scene -> (style, bpm, intensity 0..1)
    "s00": ("hook", 84, 1.0), "s01": ("drive", 84, 0.7), "s02": ("map", 76, 0.45), "s03": ("map", 76, 0.5),
    "s04": ("dark", 66, 0.35), "s05": ("tension", 80, 0.55), "s06": ("tension", 80, 0.6), "s07": ("drive", 88, 0.55),
    "s08": ("dark", 66, 0.35), "s09": ("battle", 92, 0.75), "s10": ("battle", 96, 0.85), "s11": ("battle", 92, 0.8),
    "s12": ("tension", 84, 0.7), "s13": ("climax", 88, 1.0), "s14": ("dark", 66, 0.45), "s15": ("rout", 80, 0.7),
    "s16": ("map", 72, 0.4), "s17": ("elegy", 64, 0.45), "s18": ("elegy", 60, 0.55),
}


def chord(root, q):
    third = 3 if q == "m" else 4
    return [root, root + third, root + 7]


class Song:
    def __init__(self, bpm):
        self.mid = mido.MidiFile(ticks_per_beat=480)
        self.bpm = bpm
        self.ev = {}   # ch -> list of (tick, msg)
        self.prog = {}

    def t(self, beats):
        return int(beats * 480)

    def note(self, ch, beat, dur, pitch, vel):
        vel = int(max(1, min(127, vel)))
        self.ev.setdefault(ch, []).append((self.t(beat), mido.Message("note_on", channel=ch, note=int(pitch), velocity=vel)))
        self.ev[ch].append((self.t(beat + dur) - 1, mido.Message("note_off", channel=ch, note=int(pitch), velocity=0)))

    def program(self, ch, prog):
        self.prog[ch] = prog

    def cc(self, ch, beat, num, val):
        self.ev.setdefault(ch, []).append((self.t(beat), mido.Message("control_change", channel=ch, control=num, value=int(val))))

    def save(self, fn):
        tr0 = mido.MidiTrack(); self.mid.tracks.append(tr0)
        tr0.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm), time=0))
        for ch, evs in self.ev.items():
            tr = mido.MidiTrack(); self.mid.tracks.append(tr)
            if ch != 9:
                tr.append(mido.Message("program_change", channel=ch, program=self.prog.get(ch, 0), time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=70, time=0))   # reverb
            evs.sort(key=lambda e: (e[0], e[1].type == "note_on"))
            last = 0
            for tk, m in evs:
                tr.append(m.copy(time=tk - last)); last = tk
        self.mid.save(fn)


def compose(style, bpm, inten, seconds, seed):
    rng = np.random.default_rng(seed)
    s = Song(bpm)
    beats = seconds * bpm / 60.0
    bars = int(math.ceil(beats / 4)) + 1
    s.program(0, STR); s.program(1, CELLO); s.program(2, BASS); s.program(3, HORN); s.program(4, BRASS)
    s.program(5, TIMP); s.program(6, TREM); s.program(7, TPT); s.program(8, CHOIR)
    prog = {"hook": PROG_C, "drive": PROG_A, "map": PROG_B, "dark": PROG_C, "tension": PROG_A, "battle": PROG_A,
            "climax": PROG_C, "rout": PROG_C, "elegy": PROG_B}[style]
    v = 50 + 50 * inten
    for b in range(bars):
        r, q = prog[b % 4]
        c = chord(D + r - 12, q)
        B = b * 4
        grow = min(1.0, b / max(bars - 1, 1))
        # sustained strings pad
        if style != "hook" or b > 0:
            for p in c:
                s.note(0, B, 4, p, v * 0.55 + 10 * grow)
            s.note(0, B, 4, c[0] + 12, v * 0.45)
        # bass
        s.note(2, B, 4, D + r - 36 + (12 if D + r - 36 < 28 else 0), v * 0.7)
        if style in ("map", "tension", "drive", "battle", "climax", "rout", "hook"):
            # cello ostinato in 8ths
            pat = [0, 7, 12, 7, 0, 7, 12, 7] if style == "map" else [0, 0, 7, 0, 3 if q == "m" else 4, 0, 7, 12]
            step = 0.5
            for k, iv in enumerate(pat):
                s.note(1, B + k * step, step * 0.9, D + r - 24 + iv, v * (0.55 if style == "map" else 0.75) * (1.1 if k % 2 == 0 else 0.85))
        if style in ("drive", "battle", "climax", "hook", "rout", "tension"):
            # timpani on 1 & 3, rolls before downbeats every 4 bars
            s.note(5, B, 1, D + r - 26 if D + r - 26 > 36 else D + r - 14, v * 0.9)
            s.note(5, B + 2, 1, D - 26 + 7, v * 0.7)
            if b % 4 == 3:
                for k in range(8):
                    s.note(5, B + 3 + k * 0.125, 0.12, D - 26, v * (0.5 + 0.06 * k))
        if style in ("battle", "climax", "drive", "hook"):
            # military snare march: ra-ta-ta
            for k, (bt, vv) in enumerate([(0, 1), (1, 0.7), (1.5, 0.6), (2, 0.9), (3, 0.7), (3.25, 0.5), (3.5, 0.6), (3.75, 0.55)]):
                s.note(9, B + bt, 0.2, 38, v * 0.75 * vv)
            s.note(9, B, 0.5, 36, v * 0.9)
            if style == "climax" or (style == "battle" and b % 2 == 0):
                s.note(9, B + 2, 0.5, 36, v * 0.8)
        if style in ("hook", "tension", "climax") and b % 2 == 0:
            for p in c:
                s.note(6, B, 8, p + 12, v * 0.45)
        # horn calls (motif): D-A-D'-C'-A
        motif = [(0, 1.5, 0), (1.5, 0.5, 7), (2, 1.5, 12), (3.5, 0.5, 10), (4, 3, 7)]
        if style in ("hook", "climax", "battle", "drive") and b % 4 in (0, 2):
            for bt, du, iv in motif:
                s.note(3, B + bt, du, D - 12 + r + iv, v * 0.85)
            if style in ("climax", "hook"):
                for bt, du, iv in motif:
                    s.note(4, B + bt, du, D - 12 + r + iv + 12, v * 0.6)
        if style in ("elegy", "map", "dark") and b % 4 == 0 and b > 0:
            for bt, du, iv in [(0, 3, 7), (3, 1, 5), (4, 4, 3 if q == "m" else 4)]:
                s.note(3, B + bt, du, D - 12 + r + iv, v * 0.6)
        if style == "climax" and b % 4 == 2:
            for bt in (0, 0.5, 1):
                s.note(7, B + bt, 0.4, D + r, v * 0.7)
            s.note(9, B, 2, 49, v * 0.6)
        if style == "elegy" and b % 2 == 1:
            for p in c:
                s.note(8, B, 4, p + 12, v * 0.35)
    if style == "hook":
        # opening hit at time 0: bass drum + timpani + crash + brass stab
        s.note(9, 0, 1, 36, 127); s.note(9, 0, 2, 49, 110); s.note(5, 0, 2, D - 26, 127)
        for p in chord(D - 12, "m"):
            s.note(4, 0, 2.5, p, 120)
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
        song = compose(style, bpm, inten, dur, i)
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
