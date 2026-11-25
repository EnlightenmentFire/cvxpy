# -*- coding: utf-8 -*-
"""Original documentary score, written as MIDI by code and rendered with FluidSynth + FluidR3_GM (MIT).
Sections follow the film's chapters (from timeline.json). Style: stately, forward-moving orchestral
(strings ostinato, low brass, horns, timpani), D minor with an F-major 'design' chapter.
usage: python music.py <timeline.json> <out.wav>
"""
import sys, os, json, subprocess, random
import mido

SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
BPM = 84
TPB = 480
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# GM programs
STR, CELLO, BASS, HORN, TRB, TIMP, PIANO, OBOE, CHOIR, HARP, PIZZ, SLOWSTR = 48, 42, 43, 60, 57, 47, 0, 68, 52, 46, 45, 49

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def chord(name):
    """'Dm','Bb','F','C','A','Gm','A7','Dm/C' -> (root pc, triad pcs, bass pc)"""
    bass = None
    if "/" in name:
        name, b = name.split("/")
        bass = NOTE[b]
    r = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    q = name[len(r):]
    root = NOTE[r]
    if q.startswith("m"):
        pcs = [root, (root + 3) % 12, (root + 7) % 12]
    elif q.startswith("sus"):
        pcs = [root, (root + 5) % 12, (root + 7) % 12]
    else:
        pcs = [root, (root + 4) % 12, (root + 7) % 12]
    if q.endswith("7"):
        pcs.append((root + 10) % 12)
    return root, pcs, bass if bass is not None else root


def near(pc, center):
    """MIDI note of pitch class pc nearest to center."""
    best = None
    for o in range(0, 10):
        n = o * 12 + pc
        if best is None or abs(n - center) < abs(best - center):
            best = n
    return best


# section presets: progression (one chord per bar), layers, intensity (0..1)
SECTIONS = {
    "hook": dict(prog=["Dm", "Dm/C", "Bb", "A"], layers={"pad", "bass", "ost8", "timp"}, inten=0.65),
    "title": dict(prog=["Dm", "Bb", "Gm", "A"], layers={"pad", "bass", "horn", "timp_roll", "brass"}, inten=0.95),
    "bg": dict(prog=["Dm", "Bb", "F", "C", "Gm", "Bb", "A", "A"], layers={"pad", "bass", "ost8", "horn", "timp"}, inten=0.7),
    "design": dict(prog=["F", "C", "Dm", "Bb", "F", "C", "Bb", "C"], layers={"pad", "bass", "pizz", "piano"}, inten=0.5),
    "exec": dict(prog=["Dm", "Dm/C", "Bb", "Bb", "Gm", "Gm", "A", "A"], layers={"pad", "bass", "ost16", "timp", "brass"}, inten=0.8),
    "politics": dict(prog=["Dm", "Gm", "Bb", "A", "Dm", "F", "Gm", "A"], layers={"pad", "bass", "choir", "timp_sparse", "oboe"}, inten=0.55),
    "after": dict(prog=["Bb", "F", "Gm", "Dm", "Bb", "C", "Dm", "A"], layers={"pad", "bass", "ost8", "oboe", "harp"}, inten=0.6),
    "end": dict(prog=["Dm", "Bb", "Gm", "A", "Dm", "Bb", "Gsus", "A"], layers={"pad", "bass", "piano", "horn"}, inten=0.5),
}

CH_SECTION = [("s01", "hook"), ("title", "title"), ("s08", "bg"), ("s13", "design"), ("s19", "exec"), ("s26", "politics"),
              ("s31", "after"), ("s34", "end")]


class Song:
    def __init__(self):
        self.ev = {}  # ch -> list of (tick, msg)
        self.prog = {}

    def add(self, ch, prog, t_beats, dur_beats, note, vel):
        self.prog[ch] = prog
        a = int(t_beats * TPB)
        b = int((t_beats + dur_beats) * TPB) - 4
        self.ev.setdefault(ch, []).append((a, mido.Message("note_on", channel=ch, note=int(note), velocity=int(max(1, min(127, vel))))))
        self.ev[ch].append((b, mido.Message("note_off", channel=ch, note=int(note), velocity=0)))

    def cc(self, ch, t_beats, ctl, val):
        self.ev.setdefault(ch, []).append((int(t_beats * TPB), mido.Message("control_change", channel=ch, control=ctl, value=int(val))))

    def save(self, path):
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr0 = mido.MidiTrack(); mid.tracks.append(tr0)
        tr0.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        for ch, evs in sorted(self.ev.items()):
            tr = mido.MidiTrack(); mid.tracks.append(tr)
            tr.append(mido.Message("program_change", channel=ch, program=self.prog.get(ch, 0), time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=70, time=0))  # reverb
            evs.sort(key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1))
            last = 0
            for tk, m in evs:
                tr.append(m.copy(time=tk - last)); last = tk
        mid.save(path)


def write_section(song, name, bar0, nbars, rng, fade_in=False, fade_out=False):
    P = SECTIONS[name]
    prog = P["prog"]
    L = P["layers"]
    I = P["inten"]
    for b in range(nbars):
        t = (bar0 + b) * 4.0
        root, pcs, bass = chord(prog[b % len(prog)])
        env = 1.0
        if fade_in:
            env *= min(1.0, 0.45 + 0.55 * b / max(1, min(4, nbars)))
        if fade_out and b >= nbars - 4:
            env *= max(0.2, (nbars - b) / 5)
        v = lambda x: x * env * (0.75 + 0.35 * I)  # noqa
        # string pad (whole bar, voiced around middle C)
        if "pad" in L:
            for k, pc in enumerate(pcs[:3]):
                song.add(0, STR, t, 4.0, near(pc, 58 + k * 5), v(62))
            song.add(1, SLOWSTR, t, 4.0, near(pcs[0], 74), v(40))
        if "bass" in L:
            song.add(2, BASS, t, 4.0, near(bass, 38), v(74))
            song.add(3, CELLO, t, 2.0, near(bass, 50), v(52))
            song.add(3, CELLO, t + 2, 2.0, near(pcs[2] if b % 2 else bass, 50), v(48))
        if "ost8" in L:
            pat = [0, 2, 1, 2, 0, 2, 1, 2]
            for i in range(8):
                n = near(pcs[pat[i] % len(pcs)], 62)
                acc = 1.2 if i in (0, 4) else 0.9
                song.add(4, STR, t + i * 0.5, 0.38, n, v(58 * acc))
        if "ost16" in L:
            for i in range(16):
                n = near(pcs[[0, 0, 2, 0, 1, 0, 2, 0][i % 8]], 50)
                acc = 1.25 if i % 4 == 0 else 0.85
                song.add(4, CELLO, t + i * 0.25, 0.2, n, v(66 * acc))
        if "pizz" in L:
            for i in range(4):
                n = near(pcs[[0, 2, 1, 2][i]], 60)
                song.add(5, PIZZ, t + i, 0.5, n, v(70))
        if "piano" in L:
            arp = [0, 1, 2, 1, 0, 2, 1, 2]
            for i in range(8):
                n = near(pcs[arp[i]], 67 + (i // 4) * 5)
                song.add(6, PIANO, t + i * 0.5, 0.9, n, v(46 + (8 if i == 0 else 0)))
        if "harp" in L and b % 2 == 0:
            for i, pc in enumerate(pcs[:3] * 2):
                song.add(7, HARP, t + i * 0.25, 2.0, near(pc, 64 + (i // 3) * 12), v(50))
        if "timp" in L and b % 2 == 0:
            song.add(9 if False else 8, TIMP, t, 1.0, near(root, 43), v(78))
            song.add(8, TIMP, t + 3.5, 0.5, near(root, 43), v(56))
        if "timp_sparse" in L and b % 4 == 0:
            song.add(8, TIMP, t, 2.0, near(root, 43), v(70))
        if "timp_roll" in L:
            for i in range(16):
                song.add(8, TIMP, t + i * 0.25, 0.25, near(38 % 12 + 2, 43), v(40 + 50 * (i / 16) if b == 0 else 70))
        if "choir" in L:
            for k, pc in enumerate(pcs[:3]):
                song.add(10, CHOIR, t, 4.0, near(pc, 64 + k * 4), v(40))
        if "brass" in L and b % 2 == 0:
            for k, pc in enumerate(pcs[:3]):
                song.add(11, TRB, t, 3.5, near(pc, 50 + k * 5), v(56))
        # melodies: simple motif from chord tones
        if "horn" in L and b % 2 == 0:
            m = [near(pcs[0], 65), near(pcs[2], 69), near(pcs[1], 67), near(pcs[0], 65)]
            rh = [(0, 1.5), (1.5, 0.5), (2, 1), (3, 3)]
            for (o, d), n in zip(rh, m):
                song.add(12, HORN, t + o, d, n, v(68))
        if "oboe" in L and b % 2 == 1:
            m = [near(pcs[1], 72), near(pcs[0], 74), near(pcs[2], 72)]
            for (o, d), n in zip([(0, 1), (1, 1), (2, 2)], m):
                song.add(13, OBOE, t + o, d, n, v(56))


def build(tl, out_wav):
    rng = random.Random(7)
    sc = {s["id"]: s for s in tl["scenes"]}
    total = tl["total"]
    marks = []
    for sid, name in CH_SECTION:
        marks.append((sc[sid]["start"], name))
    song = Song()
    for i, (t0, name) in enumerate(marks):
        t1 = marks[i + 1][0] if i + 1 < len(marks) else total + 3.0
        bar0 = int(round(t0 / BAR))
        bar1 = int(round(t1 / BAR))
        if name == "title":
            bar1 = max(bar1, bar0 + 1)
        nb = max(1, bar1 - bar0)
        write_section(song, name, bar0, nb, rng, fade_in=(i == 0), fade_out=(name == "end"))
    mid = out_wav.replace(".wav", ".mid")
    song.save(mid)
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", "48000", "-R", "1", "-C", "1", "-F", out_wav, SF2, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("music", out_wav)


if __name__ == "__main__":
    build(json.load(open(sys.argv[1])), sys.argv[2])
