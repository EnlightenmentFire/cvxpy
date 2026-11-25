"""Original underscore for ep.66, composed procedurally per section and rendered with FluidSynth + FluidR3_GM (MIT licence).
War half: taiko, timpani, horns, strings ostinato (D minor). Ishigakiyama: build to the loudest point, then silence at the gate.
Institutions half: koto (in-scale arpeggios), shakuhachi long tones, low strings. Ending: solo shakuhachi only.
usage: python music.py -> stems/music.wav (length = timeline total)"""
import json, os, subprocess, math, random
import numpy as np, soundfile as sf, mido
W = "/tmp/claude-0/work"; ST = f"{W}/stems"; MD = f"{W}/music"; os.makedirs(ST, exist_ok=True); os.makedirs(MD, exist_ok=True)
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"; SR = 48000
TPB = 480
CH = {"pad": (49, 78), "strings": (48, 86), "bass": (43, 90), "horn": (60, 82), "brass": (61, 76), "timp": (47, 100),
      "taiko": (116, 112), "choir": (52, 66), "koto": (107, 92), "shaku": (77, 96), "low": (58, 70)}
CHN = {"pad": 0, "strings": 1, "bass": 2, "horn": 3, "brass": 4, "koto": 5, "shaku": 6, "low": 7, "taiko": 10, "timp": 11, "choir": 12}
D = 50  # D3
PROG = {
    "epic": [(0, "m"), (-4, "M"), (3, "M"), (-2, "M")],      # Dm Bb F C
    "dark": [(0, "m"), (5, "m"), (-4, "M"), (-5, "M")],      # Dm Gm Bb A
    "tense": [(0, "m"), (1, "M"), (0, "m"), (-2, "M")],      # Dm Eb Dm C
    "calm": [(0, "m"), (-4, "M"), (5, "m"), (-5, "sus")],    # Dm Bb Gm Asus
    "still": [(0, "m"), (5, "m"), (0, "m"), (-4, "M")],
}
IN_SCALE = [0, 1, 5, 7, 8, 12, 13, 17, 19, 20, 24]  # miyako-bushi on D: D Eb G A Bb
def chord(root, q):
    third = 3 if q == "m" else (4 if q == "M" else 5)
    return [root, root + third, root + 7]

# section -> (progression, intensity start, intensity end, bpm, flavour)
SPEC = {
    "s0": ("epic", 2.6, 2.4, 96, "war"),
    "s1": ("epic", 1.6, 2.0, 92, "war"),
    "s2": ("dark", 1.4, 2.4, 92, "war"),
    "s3": ("tense", 1.6, 3.2, 100, "war"),
    "s3b": ("still", 0.2, 0.4, 72, "jp"),
    "s4": ("calm", 0.4, 0.9, 76, "jp"),
    "s5": ("calm", 0.6, 0.5, 76, "jp"),
    "s5b": ("still", 0.0, 0.0, 60, "solo"),
}
MOTIF = [(0, 2), (7, 1), (5, 1), (3, 2), (2, 1), (0, 1), (-2, 2), (0, 4)]
SHAKU = [(12, 3), (13, 1), (17, 4), (19, 2), (17, 1), (13, 1), (12, 6), (8, 2), (7, 4), (5, 2), (7, 6)]

def compose(sid, dur, seed):
    prog, i0, i1, bpm, fl = SPEC[sid]
    rnd = random.Random(seed)
    spb = 60 / bpm; beats = int(dur / spb) + 8
    mid = mido.MidiFile(ticks_per_beat=TPB)
    tr = {k: mido.MidiTrack() for k in CHN}
    for k, t in tr.items(): mid.tracks.append(t)
    tr["pad"].append(mido.MetaMessage("set_tempo", tempo=int(spb * 1e6)))
    ev = {k: [] for k in CHN}
    def note(k, b, n, length, v):
        ev[k].append((b, 1, n, max(1, min(127, int(v))))); ev[k].append((b + length, 0, n, 0))
    P = PROG[prog]; bars = beats // 4
    for bar in range(bars):
        b0 = bar * 4
        root, q = P[bar % len(P)]
        ch = chord(D + root, q)
        lvl = i0 + (i1 - i0) * bar / max(1, bars - 1)
        if fl == "solo":
            if bar % 4 == 0:
                t = 0.0
                for semi, ln in SHAKU:
                    if t >= 16: break
                    note("shaku", b0 + t, D + 12 + semi, ln * 0.92, 74 + rnd.randint(-6, 6)); t += ln
            continue
        # pad
        pv = 52 + 9 * min(lvl, 3) if fl == "war" else 44 + 8 * lvl
        for n in ch: note("pad", b0, n + 12, 4, pv)
        note("pad", b0, ch[0], 4, pv - 6)
        note("bass", b0, ch[0] - 12, 2 if fl == "war" else 4, (66 + 10 * min(lvl, 3)) if fl == "war" else 58)
        if fl == "war":
            note("bass", b0 + 2, ch[0] - 12, 2, 60 + 10 * min(lvl, 3))
            if lvl >= 1.5: note("low", b0, ch[0] - 24, 4, 40 + 12 * min(lvl, 3))
            if lvl >= 1.0:
                pat = [0, 7, 12, 7, 0, 7, 12, 15] if q == "m" else [0, 7, 12, 7, 0, 7, 12, 16]
                step = 0.5 if lvl < 2.7 else 0.25
                k = 0; t = 0.0
                while t < 4 - 1e-6:
                    acc = 1.0 if k % 4 == 0 else 0.78
                    note("strings", b0 + t, ch[0] + pat[k % 8], step * 0.6, (60 + 14 * min(lvl, 3)) * acc)
                    t += step; k += 1
            # taiko patterns (the war heartbeat)
            note("taiko", b0, 36, 0.5, 72 + 16 * min(lvl, 3))
            if lvl >= 1.6:
                note("taiko", b0 + 1.5, 36, 0.4, 62 + 14 * min(lvl, 3)); note("taiko", b0 + 2, 38, 0.4, 70 + 14 * min(lvl, 3))
            if lvl >= 2.4:
                note("taiko", b0 + 3, 36, 0.3, 84); note("taiko", b0 + 3.5, 36, 0.3, 94)
            if lvl >= 2.9:
                for kk in range(4): note("taiko", b0 + 2.5 + kk * 0.25, 38, 0.2, 80 + kk * 8)
            note("timp", b0, ch[0] - 12, 1, 48 + 15 * min(lvl, 3))
            if lvl >= 1.9 and bar % 4 == 0:
                t = 0.0
                for semi, ln in MOTIF:
                    note("horn", b0 + t, D + 12 + semi, ln * 0.95, 66 + 10 * min(lvl, 3)); t += ln
            if lvl >= 2.6 and bar % 2 == 1:
                for n in ch: note("brass", b0 + 3.5, n, 0.5, 88)
            if lvl >= 2.4 and bar % 8 == 4:
                for n in ch: note("choir", b0, n + 12, 8, 62)
        else:
            # koto: in-scale arpeggio, sparse, flowing
            if lvl > 0.05:
                pat = [0, 5, 7, 12, 13, 12, 7, 5] if bar % 2 == 0 else [0, 7, 8, 12, 17, 12, 8, 7]
                for i, sft in enumerate(pat):
                    if rnd.random() < 0.15: continue
                    note("koto", b0 + i * 0.5, D + 12 + sft + (root if root in (0, 5) else 0), 1.2, 54 + 14 * lvl + rnd.randint(-5, 5))
            # shakuhachi phrase every 4 bars
            if bar % 4 == 2:
                t = 0.0
                for semi, ln in SHAKU[:7]:
                    note("shaku", b0 + t, D + 12 + semi, ln * 0.9, 56 + 10 * lvl); t += ln
            # soft low strings
            note("strings", b0, ch[0], 4, 40 + 10 * lvl)
            note("low", b0, ch[0] - 12, 4, 34 + 10 * lvl)
    for k, t in tr.items():
        c = CHN[k]; prog_n, vol = CH[k]
        t.append(mido.Message("program_change", channel=c, program=prog_n, time=0))
        t.append(mido.Message("control_change", channel=c, control=7, value=vol, time=0))
        t.append(mido.Message("control_change", channel=c, control=91, value=78 if k in ("shaku", "koto") else 68, time=0))
        evs = sorted(ev[k], key=lambda e: (e[0], e[1]))
        last = 0
        for b, typ, n, v in evs:
            tick = int(round(b * TPB)); dt = max(0, tick - last); last = tick
            t.append(mido.Message("note_on" if typ else "note_off", channel=c, note=int(n), velocity=v, time=dt))
    p = f"{MD}/{sid}.mid"; mid.save(p); return p

def render(mid, out):
    subprocess.run(["fluidsynth", "-ni", "-g", "0.5", "-r", str(SR), "-F", out, SF2, mid], check=True, capture_output=True)

def beat_start(tl, v):
    return next(b["start"] for b in tl["beats"] if b["v"] == v)

def main():
    tl = json.load(open(f"{W}/timeline.json")); total = tl["total"]
    sc = {s["id"]: s for s in tl["scenes"]}
    HOOK = 3.0   # the opening is tree-crack SFX + silence + one taiko hit; music enters after it
    t_sur = beat_start(tl, "surrender"); t_osaka = beat_start(tl, "osaka")
    segs = [("s0", HOOK, sc["s1"]["start"] - 0.8), ("s1", sc["s1"]["start"] - 0.8, sc["s2"]["start"] - 0.8),
            ("s2", sc["s2"]["start"] - 0.8, sc["s3"]["start"] - 0.8), ("s3", sc["s3"]["start"] - 0.8, t_sur),
            ("s3b", t_sur + 2.6, sc["s4"]["start"] - 0.8), ("s4", sc["s4"]["start"] - 0.8, sc["s5"]["start"] - 0.8),
            ("s5", sc["s5"]["start"] - 0.8, t_osaka), ("s5b", t_osaka - 0.5, total)]
    out = np.zeros((int(total * SR) + SR * 6, 2), np.float32)
    XF = 2.5
    for i, (sid, a, b) in enumerate(segs):
        mid = compose(sid, b - a + XF + 3, 100 + i)
        wav = f"{MD}/{sid}.wav"; render(mid, wav)
        x, sr = sf.read(wav, always_2d=True); x = x.astype(np.float32)
        hard_end = sid == "s3"     # cut to silence at the gate
        L = int((b - a + (0.25 if hard_end else XF)) * SR); x = x[:L]
        if len(x) < L: x = np.vstack([x, np.zeros((L - len(x), 2), np.float32)])
        f = int(XF * SR)
        if i > 0 and sid not in ("s3b",): x[:f] *= np.linspace(0, 1, f)[:, None] ** 0.5
        if sid == "s3b": fi = int(3.0 * SR); x[:fi] *= np.linspace(0, 1, fi)[:, None] ** 1.5
        if sid == "s0": fi = int(0.05 * SR); x[:fi] *= np.linspace(0, 1, fi)[:, None]
        if hard_end:
            ff = int(0.25 * SR); x[-ff:] *= np.linspace(1, 0, ff)[:, None]
        elif i < len(segs) - 1: x[-f:] *= np.linspace(1, 0, f)[:, None] ** 0.5
        else:
            ff = int(4 * SR); x[-ff:] *= np.linspace(1, 0, ff)[:, None] ** 1.5
        # section level trims (dB)
        trim = {"s0": 0, "s1": -1.5, "s2": -0.5, "s3": 1.0, "s3b": 0, "s4": 4, "s5": 4, "s5b": 4}[sid]
        x *= 10 ** (trim / 20)
        s0 = int(a * SR); out[s0:s0 + len(x)] += x
        print(sid, f"{a:.1f}-{b:.1f}", flush=True)
    out = out[:int(total * SR)]
    out /= (np.abs(out).max() + 1e-9) / 0.89
    sf.write(f"{ST}/music.wav", out, SR, subtype="FLOAT")
    print("music", out.shape[0] / SR)

if __name__ == "__main__":
    main()
