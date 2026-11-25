# -*- coding: utf-8 -*-
"""Original orchestral underscore ("恢宏": drums, horns, strings), composed procedurally,
rendered with FluidSynth + FluidR3_GM (MIT-licensed soundfont). Sections follow timeline.json.
Output: /tmp/claude-0/work/audio/music.wav (48k stereo)."""
import json, os, subprocess, math
import mido

WORK = "/tmp/claude-0/work"
TL = json.load(open(f"{WORK}/timeline.json"))
BPM = 84
BEAT = 60 / BPM
TPB = 480
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

# intensity per scene: 0 silent-ish pad, 1 pad, 2 ostinato, 3 +horns, 4 +drums, 5 full
INT = dict(s00=4, s01=1, s02=2, s02b=2, s03=3, s04=4, s05=5, s05b=3, s06=1, s07=3, end=2)
# D minor epic progression, 2 bars each (root midi, chord tones)
PROG = [(38, [50, 53, 57]), (34, [50, 53, 58]), (41, [48, 53, 57]), (36, [48, 52, 55]),
        (38, [50, 53, 57]), (43, [50, 55, 58]), (34, [50, 53, 58]), (33, [49, 52, 57])]
CH = dict(pad=0, str=1, cello=2, bass=3, horn=4, brass=5, timp=6, taiko=7, choir=8, perc=9)
PROGRAM = dict(pad=89, str=48, cello=42, bass=43, horn=60, brass=61, timp=47, taiko=116, choir=52)


def scene_at(t):
    for s in TL["scenes"]:
        if s["t0"] <= t < s["t1"]:
            return s["id"]
    return "end"


def main():
    total = TL["total"]
    nbars = int(math.ceil(total / (4 * BEAT))) + 1
    ev = []  # (tick, msg)

    def note(ch, t_beats, dur_beats, n, vel):
        t0 = int(t_beats * TPB); t1 = int((t_beats + dur_beats) * TPB) - 5
        ev.append((t0, mido.Message("note_on", channel=ch, note=n, velocity=max(1, min(127, int(vel))))))
        ev.append((t1, mido.Message("note_off", channel=ch, note=n, velocity=0)))

    for name, ch in CH.items():
        if name != "perc":
            ev.append((0, mido.Message("program_change", channel=ch, program=PROGRAM[name])))
        ev.append((0, mido.Message("control_change", channel=ch, control=91, value=70)))  # reverb
    # opening hit
    for n in (38, 50, 57, 62):
        note(CH["brass"], 0, 3, n, 120)
    note(CH["timp"], 0, 2, 38, 127); note(CH["taiko"], 0, 2, 50, 127)
    note(CH["perc"], 0, 1, 49, 110)
    for bar in range(nbars):
        tb = bar * 4
        tsec = tb * BEAT
        sid = scene_at(tsec + 0.01)
        lv = INT.get(sid, 2)
        # in s00, hold intensity 4 for the first ~12 s, then 2, punch near the end
        if sid == "s00":
            lv = 4 if tsec < 10 else 2
        root, tones = PROG[(bar // 2) % len(PROG)]
        # volume ramps over 4 bars at section changes handled by CC7 per bar
        ev.append((tb * TPB, mido.Message("control_change", channel=CH["pad"], control=7, value=80 if lv <= 2 else 60)))
        # pad + strings sustain
        for n in tones:
            note(CH["pad"], tb, 4, n, 55 + 8 * lv)
            if lv >= 1:
                note(CH["str"], tb, 4, n + 12, 45 + 10 * lv)
        note(CH["bass"], tb, 4, root, 60 + 8 * lv)
        if lv >= 2:  # cello ostinato 8ths
            pat = [root + 12, root + 12, root + 19, root + 12, root + 15, root + 12, root + 19, root + 24]
            for k, n in enumerate(pat):
                note(CH["cello"], tb + k * 0.5, 0.45, n, (60 if k % 2 == 0 else 48) + 8 * lv)
        if lv >= 3:  # horn melody, 2-bar phrase
            mel = [(0, 2, tones[2] + 12), (2, 1, tones[1] + 12), (3, 1, tones[0] + 12)] if bar % 2 == 0 else [(0, 3, tones[0] + 12), (3, 1, tones[2])]
            for o, d, n in mel:
                note(CH["horn"], tb + o, d, n, 50 + 12 * (lv - 2))
        if lv >= 4:  # taiko + timpani drive
            for k, (o, v) in enumerate(((0, 120), (1.5, 90), (2, 110), (3, 85), (3.5, 95))):
                note(CH["taiko"], tb + o, 0.4, 50 if k % 2 == 0 else 47, v - (10 if lv == 4 else 0))
            note(CH["timp"], tb, 1, root + 12 if root < 40 else root, 100)
            note(CH["timp"], tb + 2, 1, root + 12 + 7 if root + 19 < 60 else root + 7, 85)
        if lv >= 5:  # brass chords + choir
            for n in tones:
                note(CH["brass"], tb, 2, n, 95); note(CH["brass"], tb + 2.5, 1.5, n, 85)
                note(CH["choir"], tb, 4, n + 12, 70)
            note(CH["perc"], tb, 1, 49 if bar % 4 == 0 else 57, 90)
    # section accents: drum + brass hit at scene starts
    for s in TL["scenes"]:
        if s["id"] in ("s02", "s03", "s04", "s05", "s07"):
            b = s["t0"] / BEAT
            note(CH["timp"], b, 1.5, 38, 120); note(CH["taiko"], b, 1.5, 50, 120)
            for n in (50, 57):
                note(CH["brass"], b, 2, n, 100)
    ev.sort(key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1))
    mid = mido.MidiFile(ticks_per_beat=TPB); tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM)))
    last = 0
    for t, m in ev:
        tr.append(m.copy(time=t - last)); last = t
    os.makedirs(f"{WORK}/audio", exist_ok=True)
    mid.save(f"{WORK}/audio/score.mid")
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", "48000", "-F", f"{WORK}/audio/music_raw.wav", SF2, f"{WORK}/audio/score.mid"], check=True, capture_output=True)
    # trim to length, gentle fade out, normalize later in mix
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/audio/music_raw.wav", "-af",
                    f"atrim=0:{total:.2f},afade=t=out:st={total - 5:.2f}:d=5", "-ar", "48000", "-ac", "2", f"{WORK}/audio/music.wav"], check=True)
    print("music ok", total)


if __name__ == "__main__":
    main()
