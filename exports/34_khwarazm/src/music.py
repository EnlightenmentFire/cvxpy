"""Original orchestral underscore (D minor), composed procedurally per chapter and rendered with FluidSynth + FluidR3_GM (MIT).
usage: python music.py -> stems/music.wav (length = timeline total)"""
import json, os, subprocess, math, random
import numpy as np, soundfile as sf, mido
W = "/tmp/claude-0/work"; ST = f"{W}/stems"; MD = f"{W}/music"; os.makedirs(ST, exist_ok=True); os.makedirs(MD, exist_ok=True)
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"; SR = 48000
TPB = 480
# channel: (program, base volume)
CH = {"pad": (49, 80), "strings": (48, 88), "bass": (43, 92), "cb": (32 + 0, 0), "horn": (60, 84), "brass": (61, 80),
      "timp": (47, 100), "taiko": (116, 110), "choir": (52, 70), "harp": (46, 70), "low": (58, 76)}
CHN = {k: i for i, k in enumerate(["pad", "strings", "bass", "horn", "brass", "timp", "taiko", "choir", "harp", "low"])}
CHN["taiko"] = 10; CHN["timp"] = 11; CHN["choir"] = 12; CHN["low"] = 13  # avoid drum channel 9
D = 50  # D3
PROG = {
    "epic": [(0, "m"), (-4, "M"), (3, "M"), (-2, "M")],      # Dm Bb F C
    "dark": [(0, "m"), (5, "m"), (-4, "M"), (-5, "M")],      # Dm Gm Bb A
    "tense": [(0, "m"), (1, "M"), (0, "m"), (-2, "M")],      # Dm Eb Dm C
    "heroic": [(0, "m"), (-2, "M"), (-4, "M"), (-5, "M")],   # Dm C Bb A
    "calm": [(0, "m"), (-4, "M"), (5, "m"), (-5, "sus")],    # Dm Bb Gm Asus
}
def chord(root, q):
    third = 3 if q == "m" else (4 if q == "M" else 5)
    return [root, root + third, root + 7]

SPEC = {  # scene -> (progression, intensity, tempo, extras)
    "s0": ("epic", 3, 96, {"hit": True}),
    "s1": ("epic", 2, 96, {}),
    "s2": ("dark", 1, 84, {}),
    "s3": ("tense", 1, 84, {}),
    "s4": ("epic", 2, 96, {"build": True}),
    "s5": ("dark", 1, 84, {}),
    "s6": ("tense", 3, 104, {}),
    "s7": ("heroic", 2, 90, {"build": True}),
    "s8": ("calm", 0, 76, {"end": True}),
}
MOTIF = [(0, 2), (7, 1), (5, 1), (3, 2), (2, 1), (0, 1), (-2, 2), (0, 4)]  # degrees in semitones from D, beats

def compose(sid, dur, seed):
    prog, inten, bpm, ex = SPEC[sid]
    rnd = random.Random(seed)
    spb = 60 / bpm; beats = int(dur / spb) + 8
    mid = mido.MidiFile(ticks_per_beat=TPB)
    tr = {k: mido.MidiTrack() for k in CHN}
    for k, t in tr.items(): mid.tracks.append(t)
    tr["pad"].append(mido.MetaMessage("set_tempo", tempo=int(spb * 1e6)))
    ev = {k: [] for k in CHN}  # (beat_time, type, note, vel)
    def note(k, b, n, length, v):
        ev[k].append((b, 1, n, max(1, min(127, int(v))))); ev[k].append((b + length, 0, n, 0))
    P = PROG[prog]
    bars = beats // 4
    for bar in range(bars):
        b0 = bar * 4
        root, q = P[bar % len(P)]
        ch = chord(D + root, q)
        prog_t = bar / max(1, bars - 1)
        lvl = inten + (prog_t * 1.2 if ex.get("build") else 0)
        if ex.get("end"): lvl = max(0, 0.8 - prog_t)
        # pad (always): long chord, two octaves
        for n in ch: note("pad", b0, n + 12, 4, 58 + 10 * min(lvl, 3))
        note("pad", b0, ch[0], 4, 50 + 8 * min(lvl, 3))
        # bass
        note("bass", b0, ch[0] - 12, 2, 70 + 10 * min(lvl, 3)); note("bass", b0 + 2, ch[0] - 12, 2, 64 + 10 * min(lvl, 3))
        note("low", b0, ch[0] - 24, 4, 40 + 12 * min(lvl, 3)) if lvl >= 1.5 else None
        if lvl >= 0.9:  # ostinato 8ths
            pat = [0, 7, 12, 7, 0, 7, 12, 15] if q == "m" else [0, 7, 12, 7, 0, 7, 12, 16]
            step = 0.5 if lvl < 2.6 else 0.25
            k = 0
            t = 0.0
            while t < 4 - 1e-6:
                n = ch[0] + 12 + pat[k % 8] - 12
                acc = 1.0 if k % 4 == 0 else 0.78
                note("strings", b0 + t, n, step * 0.6, (62 + 14 * min(lvl, 3)) * acc)
                t += step; k += 1
        if lvl >= 1.0:  # percussion
            note("taiko", b0, 36, 0.5, 70 + 18 * min(lvl, 3))
            if lvl >= 1.8:
                note("taiko", b0 + 1.5, 36, 0.4, 60 + 14 * min(lvl, 3)); note("taiko", b0 + 2, 38, 0.4, 70 + 14 * min(lvl, 3))
            if lvl >= 2.6:
                note("taiko", b0 + 3, 36, 0.3, 80); note("taiko", b0 + 3.5, 36, 0.3, 90)
            note("timp", b0, ch[0] - 12, 1, 50 + 15 * min(lvl, 3))
        if lvl >= 2.0 and bar % 4 == 0:  # horn motif every 4 bars
            t = 0.0
            for semi, ln in MOTIF:
                note("horn", b0 + t, D + 12 + semi, ln * 0.95, 70 + 10 * min(lvl, 3)); t += ln
        if lvl >= 2.5 and bar % 2 == 1:
            for n in ch: note("brass", b0 + 3.5, n, 0.5, 86)
        if lvl >= 2.2 and bar % 8 == 4:
            for n in ch: note("choir", b0, n + 12, 8, 60)
        if prog in ("calm", "dark") and lvl < 1.5 and bar % 2 == 0:  # harp arpeggio
            for i, n in enumerate(ch + [ch[0] + 12, ch[1] + 12]):
                note("harp", b0 + i * 0.5, n + 12, 1.5, 52)
    if ex.get("hit"):
        for n in chord(D, "m"):
            note("brass", 0, n, 2, 110); note("horn", 0, n + 12, 3, 100)
        note("taiko", 0, 36, 1, 127); note("timp", 0, D - 12, 2, 120)
        for i in range(6): note("taiko", 0.5 + i * 0.25, 36 if i % 2 else 38, 0.2, 80 + i * 6)
    for k, t in tr.items():
        c = CHN[k]; prog_n, vol = CH[k]
        t.append(mido.Message("program_change", channel=c, program=prog_n, time=0))
        t.append(mido.Message("control_change", channel=c, control=7, value=vol, time=0))
        t.append(mido.Message("control_change", channel=c, control=91, value=70, time=0))  # reverb
        evs = sorted(ev[k], key=lambda e: (e[0], e[1]))
        last = 0
        for b, typ, n, v in evs:
            tick = int(round(b * TPB)); dt = max(0, tick - last); last = tick
            t.append(mido.Message("note_on" if typ else "note_off", channel=c, note=int(n), velocity=v, time=dt))
    p = f"{MD}/{sid}.mid"; mid.save(p); return p

def render(mid, out):
    subprocess.run(["fluidsynth", "-ni", "-g", "0.5", "-r", str(SR), "-F", out, SF2, mid], check=True, capture_output=True)

def main():
    tl = json.load(open(f"{W}/timeline.json"))
    sc = tl["scenes"]; total = tl["total"]
    bounds = []
    for i, s in enumerate(sc):
        a = 0.0 if i == 0 else s["start"] - 0.8
        b = total if i == len(sc) - 1 else sc[i + 1]["start"] - 0.8
        bounds.append((s["id"], a, b))
    out = np.zeros((int(total * SR) + SR * 4, 2), np.float32)
    XF = 2.5
    for i, (sid, a, b) in enumerate(bounds):
        mid = compose(sid, b - a + XF + 2, 100 + i)
        wav = f"{MD}/{sid}.wav"; render(mid, wav)
        x, sr = sf.read(wav, always_2d=True); x = x.astype(np.float32)
        L = int((b - a + XF) * SR); x = x[:L]
        if len(x) < L: x = np.vstack([x, np.zeros((L - len(x), 2), np.float32)])
        f = int(XF * SR)
        if i > 0: x[:f] *= np.linspace(0, 1, f)[:, None] ** 0.5
        if i < len(bounds) - 1: x[-f:] *= np.linspace(1, 0, f)[:, None] ** 0.5
        else:
            ff = int(5 * SR); x[-ff:] *= np.linspace(1, 0, ff)[:, None] ** 1.5
        s0 = int(a * SR); out[s0:s0 + len(x)] += x
        print(sid, f"{a:.1f}-{b:.1f}", flush=True)
    out = out[:int(total * SR)]
    out /= (np.abs(out).max() + 1e-9) / 0.89
    sf.write(f"{ST}/music.wav", out, SR, subtype="FLOAT")
    print("music", out.shape[0] / SR)

if __name__ == "__main__":
    main()
