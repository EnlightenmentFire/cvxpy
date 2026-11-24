"""Original chamber-style cues (solo piano / violin), rendered with fluidsynth + FluidR3_GM (MIT).
Cues: america (D major waltz), france (A minor, sparse), dark (D minor, low), ending (violin + piano).
usage: python music.py   -> writes /tmp/claude-0/work/music/<cue>.wav (48 kHz stereo)
"""
import os, subprocess, random
import mido

OUT = "/tmp/claude-0/work/music"
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
        "A": 9, "A#": 10, "Bb": 10, "B": 11}


def n(s):
    """'F#5' -> midi number"""
    name, octv = s[:-1], int(s[-1])
    return 12 * (octv + 1) + NOTE[name]


CHORDS = {  # root, third, fifth, (seventh)
    "D": ["D", "F#", "A"], "Bm": ["B", "D", "F#"], "G": ["G", "B", "D"], "A": ["A", "C#", "E"], "A7": ["A", "C#", "E", "G"],
    "F#m": ["F#", "A", "C#"], "Em7": ["E", "G", "B", "D"], "D/F#": ["F#", "A", "D"], "Em": ["E", "G", "B"],
    "Am": ["A", "C", "E"], "Dm": ["D", "F", "A"], "E": ["E", "G#", "B"], "F": ["F", "A", "C"], "C": ["C", "E", "G"],
    "Dm/F": ["F", "A", "D"], "C/E": ["E", "G", "C"], "Bb": ["Bb", "D", "F"], "Gm": ["G", "Bb", "D"], "E7": ["E", "G#", "B", "D"],
}


class Song:
    def __init__(self, bpm, beats_per_bar, seed=0):
        self.bpm, self.bpb = bpm, beats_per_bar
        self.ev = []  # (start_beat, dur_beats, pitch, vel, channel)
        self.rng = random.Random(seed)

    def note(self, start, dur, pitch, vel, ch=0):
        self.ev.append((start, dur, pitch, vel, ch))

    def arp(self, bar, chord, low_oct=2, vel=46, ch=0, pattern=(0, 2, 4, 2, 5, 2), sub=0.5, last=False):
        tones = CHORDS[chord]
        root = n(tones[0] + str(low_oct))
        up = [n(t + str(low_oct + 1)) for t in tones]
        up = sorted(up)
        seq = [root, root + 7, up[1 % len(up)], up[2 % len(up)], root + 12, up[1 % len(up)]]
        b0 = bar * self.bpb
        steps = int(self.bpb / sub)
        for i in range(steps):
            p = seq[pattern[i % len(pattern)] % len(seq)]
            d = sub * (3.5 if i == 0 else 1.6)
            self.note(b0 + i * sub, d, p, vel + (8 if i == 0 else 0) + self.rng.randint(-4, 4), ch)
            if last and i == 0:
                self.note(b0, self.bpb * 2, root, vel + 6, ch)
                break

    def mel(self, bar, notes, vel=62, ch=0):
        """notes: list of (pitch_str or None, beats)"""
        t = bar * self.bpb
        for p, d in notes:
            if p:
                self.note(t, d * 0.98, n(p), vel + self.rng.randint(-5, 5), ch)
            t += d

    def write(self, path, programs, tail_beats=6, rubato=0.0, reverb=None):
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(self.bpm)))
        for ch, prog in programs.items():
            tr.append(mido.Message("program_change", channel=ch, program=prog, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=reverb if reverb is not None else 70, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=93, value=0, time=0))
            if prog == 0:
                pass
        msgs = []
        for st, du, p, v, ch in self.ev:
            j = self.rng.gauss(0, 0.012)
            on = max(0.0, st + j)
            msgs.append((on, 1, mido.Message("note_on", channel=ch, note=p, velocity=max(1, min(127, v)))))
            msgs.append((on + du, 0, mido.Message("note_off", channel=ch, note=p, velocity=0)))
        end = max(st + du for st, du, *_ in self.ev) + tail_beats
        msgs.append((end, 0, mido.Message("control_change", channel=0, control=123, value=0)))
        msgs.sort(key=lambda x: (x[0], x[1]))
        last = 0
        for t, _, m in msgs:
            dt = int(round((t - last) * 480))
            m.time = max(0, dt)
            tr.append(m)
            last = t
        mid.save(path)


def render(mid, wav, gain=0.55):
    subprocess.run(["fluidsynth", "-ni", "-g", str(gain), "-r", "48000", "-F", wav, SF2, mid], check=True, capture_output=True)


def america(seed=1, reps=2):
    s = Song(66, 3, seed)
    A = ["D", "Bm", "G", "A", "D", "F#m", "G", "A7"]
    B = ["Bm", "G", "D", "A", "G", "D/F#", "Em7", "A7", "D"]
    melA = [[("F#5", 1), ("E5", 1), ("D5", 1)], [("D5", 2), ("B4", 1)], [("B4", 1.5), ("A4", 0.5), ("G4", 1)], [("A4", 3)],
            [("F#5", 1), ("A5", 1), ("F#5", 1)], [("E5", 2), ("C#5", 1)], [("D5", 1), ("B4", 1), ("E5", 1)], [("C#5", 3)]]
    melB = [[("D5", 1), ("F#5", 1), ("B5", 1)], [("A5", 2), ("G5", 1)], [("F#5", 1), ("E5", 1), ("D5", 1)], [("E5", 3)],
            [("D5", 1), ("B4", 1), ("G5", 1)], [("F#5", 2), ("A4", 1)], [("G4", 1), ("B4", 1), ("E5", 1)], [("C#5", 2), ("E5", 1)], [("D5", 3)]]
    bar = 0
    # intro: two bars of arpeggio
    s.arp(bar, "D", vel=40); bar += 1
    s.arp(bar, "A", vel=40); bar += 1
    for r in range(reps):
        for i, c in enumerate(A):
            s.arp(bar, c, vel=42)
            if not (r == 0 and i < 0):
                s.mel(bar, melA[i], vel=58 if r == 0 else 54)
            bar += 1
        for i, c in enumerate(B):
            s.arp(bar, c, vel=42, last=(i == len(B) - 1 and r == reps - 1))
            s.mel(bar, melB[i], vel=58 if r == 0 else 54)
            bar += 1
    return s


def france(seed=2, reps=2):
    s = Song(56, 4, seed)
    prog = ["Am", "Dm/F", "E", "Am", "F", "C/E", "Dm", "E"]
    mel = [[("E5", 2), ("C5", 2)], [("D5", 2), ("A4", 2)], [("B4", 2), ("G#4", 2)], [("A4", 4)],
           [("C5", 2), ("A4", 2)], [("G4", 2), ("E4", 2)], [("F4", 2), ("A4", 1), ("D5", 1)], [("B4", 4)]]
    bar = 0
    for r in range(reps):
        for i, c in enumerate(prog):
            tones = CHORDS[c]
            root = n(tones[0] + "2")
            s.note(bar * 4, 4, root, 40)
            s.note(bar * 4 + 1, 3, n(tones[1] + "3"), 32)
            s.note(bar * 4 + 2, 2, n(tones[2] + "3"), 30)
            if r > 0 or i % 2 == 0 or True:
                s.mel(bar, [(p.replace("4", "5").replace("5", "6") if False else p, d) for p, d in mel[i]], vel=50)
            bar += 1
    s.note(bar * 4, 8, n("A2"), 42); s.note(bar * 4, 8, n("E3"), 32); s.note(bar * 4, 8, n("A4"), 40)
    return s


def dark(seed=3, reps=2):
    s = Song(52, 4, seed)
    prog = ["Dm", "Bb", "Gm", "A", "Dm", "Gm", "E7", "A"]
    bar = 0
    for r in range(reps):
        for i, c in enumerate(prog):
            tones = CHORDS[c]
            s.note(bar * 4, 4, n(tones[0] + "2"), 44)
            s.note(bar * 4, 4, n(tones[0] + "1"), 30)
            s.note(bar * 4 + 2, 2, n(tones[1] + "3"), 28)
            if i % 2 == 1:
                s.note(bar * 4 + 1, 3, n(tones[2] + "4"), 34)
            bar += 1
    s.note(bar * 4, 8, n("D2"), 40); s.note(bar * 4, 8, n("A2"), 30)
    return s


def ending(seed=4):
    s = Song(60, 3, seed)
    A = ["D", "Bm", "G", "A", "D", "F#m", "G", "A7", "Bm", "G", "D", "A", "G", "D/F#", "Em7", "A7", "D"]
    mel = [[("F#5", 1), ("E5", 1), ("D5", 1)], [("D5", 2), ("B4", 1)], [("B4", 1.5), ("A4", 0.5), ("G4", 1)], [("A4", 3)],
           [("F#5", 1), ("A5", 1), ("F#5", 1)], [("E5", 2), ("C#5", 1)], [("D5", 1), ("B4", 1), ("E5", 1)], [("C#5", 3)],
           [("D5", 1), ("F#5", 1), ("B5", 1)], [("A5", 2), ("G5", 1)], [("F#5", 1), ("E5", 1), ("D5", 1)], [("E5", 3)],
           [("D5", 1), ("B4", 1), ("G5", 1)], [("F#5", 2), ("A4", 1)], [("G4", 1), ("B4", 1), ("E5", 1)], [("C#5", 2), ("E5", 1)], [("D5", 3)]]
    s.arp(0, "D", vel=38); s.arp(1, "A", vel=38)
    for i, c in enumerate(A):
        s.arp(i + 2, c, vel=40, last=(i == len(A) - 1))
        s.mel(i + 2, [(p.replace("5", "4") if p else p, d) for p, d in mel[i]] if False else mel[i], vel=72, ch=1)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    cues = {"america": (america(), {0: 0}), "france": (france(), {0: 0}), "dark": (dark(), {0: 0}),
            "ending": (ending(), {0: 0, 1: 40})}
    for name, (song, progs) in cues.items():
        mid = f"{OUT}/{name}.mid"
        song.write(mid, progs, reverb=75)
        render(mid, f"{OUT}/{name}.wav", gain=0.5)
        print("rendered", name)


if __name__ == "__main__":
    main()
