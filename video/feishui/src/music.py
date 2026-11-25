# -*- coding: utf-8 -*-
"""原创配乐（本仓库代码作曲）：按时间轴生成 MIDI，用 FluidSynth + FluidR3_GM（MIT 许可）渲染。
战争类「恢宏」：鼓、号角、弦乐推进。强度曲线跟着叙事走；几个关键点打重音：开场、洛涧夜袭、「秦兵敗矣」、晋军渡河、屐齿折。
输出 WORK/music/music.wav（48 kHz 立体声）。"""
import os, json, math, subprocess, random
import mido

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
TL = json.load(open(f"{HERE}/timeline.json"))
L = {l["id"]: l for l in TL["lines"]}
A = lambda i: L[i]["start"]
E = lambda i: L[i]["end"]
S0 = lambda s: TL["secs"][s]["start"]
TOTAL = TL["total"]
BPM = 80.0
BEAT = 60 / BPM
TPB = 480

# 强度曲线：分段线性 [(t, I)]
KEYS = [
    (0, 0.95), (E("s1_01"), 0.85), (A("s1_03"), 0.8), (A("s1_06"), 0.55), (A("s1_08"), 0.7), (A("s1_09"), 0.75), (S0("s2") - 0.5, 0.6),
    (S0("s2") + 2, 0.45), (A("s2_03"), 0.5), (A("s2_08"), 0.45), (A("s2_12"), 0.62), (A("s2_16"), 0.7), (A("s2_22"), 0.5), (A("s2_24"), 0.55),
    (S0("s3"), 0.5), (A("s3_05"), 0.7), (A("s3_07"), 0.92), (A("s3_08") + 3, 0.6), (A("s3_09"), 0.4), (A("s3_12"), 0.55), (A("s3_13"), 0.45), (A("s3_15"), 0.35),
    (S0("s4"), 0.3), (A("s4_06"), 0.35), (A("s4_10"), 0.42), (S0("s5") - 0.5, 0.4),
    (S0("s5"), 0.45), (A("s5_07"), 0.5), (A("s5_11"), 0.62), (A("s5_13"), 0.7), (A("s5_14"), 0.35), (A("s5_22"), 0.45), (A("s5_26"), 0.75),
    (A("s5_28"), 0.25), (A("s5_29") - 0.05, 0.15), (A("s5_29"), 1.0), (A("s5_33") + 3, 0.95), (A("s5_36") + 2, 0.85), (A("s5_37"), 0.35), (A("s5_41"), 0.88),
    (A("s5_43"), 0.5), (S0("s6") - 0.3, 0.35),
    (S0("s6"), 0.32), (A("s6_07"), 0.35), (A("s6_13"), 0.4), (A("s6_18"), 0.45), (A("s6_22"), 0.4), (A("s6_23"), 0.6), (S0("s7") - 0.3, 0.3),
    (S0("s7"), 0.25), (A("s7_09"), 0.3), (TOTAL - 3, 0.25), (TOTAL, 0.0),
]
HITS = [0.0, A("s3_07") + 0.8, A("s5_29"), A("s5_41") + 1.0]
CLOG = A("s7_09") + (E("s7_09") - A("s7_09")) * 0.62

def I(t):
    for (t0, a), (t1, b) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            return a + (b - a) * (t - t0) / max(1e-6, t1 - t0)
    return KEYS[-1][1]

def mood(t):
    if t < S0("s2"): return "war"
    if t < S0("s4"): return "war"
    if t < S0("s5"): return "intrigue"
    if t < S0("s6"): return "war"
    if t < S0("s7"): return "elegy"
    return "calm"

# D 小调和声进行（MIDI 根音）
PROG = {"war": [(50, "m"), (46, "M"), (43, "m"), (45, "M")], "intrigue": [(50, "m"), (48, "M"), (46, "M"), (45, "M")],
        "elegy": [(50, "m"), (43, "m"), (46, "M"), (45, "M")], "calm": [(50, "m"), (46, "M"), (41, "M"), (45, "M")]}
def chord(root, q):
    return [root, root + (3 if q == "m" else 4), root + 7]

class Track:
    def __init__(s, ch, prog, name):
        s.ch, s.prog, s.ev = ch, prog, []
        s.name = name
    def note(s, t, dur, n, v):
        if t < 0 or t > TOTAL: return
        v = max(1, min(127, int(v)))
        s.ev.append((t, 1, n, v)); s.ev.append((t + dur, 0, n, 0))
    def cc(s, t, c, val):
        s.ev.append((t, 2, c, int(val)))

def build():
    random.seed(383)
    pad = Track(0, 48, "strings"); ost = Track(1, 48, "ostinato"); low = Track(2, 57, "trombones"); horn = Track(3, 60, "horns")
    timp = Track(4, 47, "timpani"); taiko = Track(5, 116, "taiko"); choir = Track(6, 52, "choir"); flute = Track(7, 77, "shakuhachi")
    harp = Track(8, 46, "harp"); perc = Track(9, 0, "perc"); cello = Track(10, 42, "cello")
    tracks = [pad, ost, low, horn, timp, taiko, choir, flute, harp, perc, cello]
    bar = 4 * BEAT
    nb = int(TOTAL / bar) + 1
    hornMotif = [(0, 2, 62), (2, 1, 69), (3, 1, 67), (4, 2, 65), (6, 2, 64), (8, 4, 62)]  # D A G F E D（以拍计）
    for b in range(nb):
        t = b * bar
        i = I(t + 0.01); m = mood(t)
        root, q = PROG[m][b % 4]
        ch = chord(root, q)
        # 弦乐长音铺底
        if i > 0.08:
            for n in ch + [root + 12]:
                pad.note(t, bar * 0.98, n, 34 + 50 * i)
        # 大提琴低音
        if i > 0.2: cello.note(t, bar * 0.95, root - 12, 40 + 50 * i)
        # 低音弦乐八分音符推进
        if i > 0.42 and m in ("war", "intrigue"):
            pat = [0, 0, 7, 0, 3 if q == "m" else 4, 0, 7, 5] if m == "war" else [0, 7, 0, 7, 0, 7, 0, 7]
            for k in range(8):
                vv = (45 + 60 * i) * (1.0 if k % 2 == 0 else 0.8)
                ost.note(t + k * BEAT / 2, BEAT / 2 * 0.6, root - 12 + pat[k] + 12, vv)
        # 长号
        if i > 0.62 and m == "war":
            low.note(t, bar * 0.9, root - 12, 40 + 60 * (i - 0.5))
            low.note(t, bar * 0.9, root - 5, 35 + 55 * (i - 0.5))
        # 定音鼓
        if i > 0.38 and m != "calm":
            for k in (0, 2):
                timp.note(t + k * BEAT, BEAT * 0.9, 38 + (root - 38) % 12, 50 + 60 * i)
            if i > 0.7: timp.note(t + 3.5 * BEAT, BEAT * 0.4, 38 + (root - 38) % 12, 45 + 50 * i)
        # 太鼓
        if i > 0.68 and m == "war":
            for k, vv in [(0, 1), (1.5, 0.7), (2, 0.9), (3, 0.75), (3.5, 0.6)]:
                taiko.note(t + k * BEAT, BEAT * 0.5, 45, (60 + 60 * i) * vv)
        # 低音大鼓（打击乐声道）
        if i > 0.5 and m == "war":
            perc.note(t, 0.3, 36, 60 + 50 * i)
            if i > 0.8: perc.note(t + 2 * BEAT, 0.3, 36, 55 + 50 * i)
        # 号角动机：每 4 小节一次，强度够时
        if m == "war" and i > 0.55 and b % 4 == 1:
            for (bt, d, n) in hornMotif:
                horn.note(t + bt * BEAT, d * BEAT * 0.95, n - (0 if q == "m" else 0), 50 + 55 * i)
        # 尺八（溃逃之夜）
        if m == "elegy" and b % 2 == 0:
            phrase = [(0, 3, 74), (3, 1, 72), (4, 2, 69), (6, 2, 67), (8, 4, 69)] if b % 4 == 0 else [(0, 2, 65), (2, 2, 67), (4, 4, 69), (8, 3, 62)]
            for (bt, d, n) in phrase:
                flute.note(t + bt * BEAT, d * BEAT * 0.95, n, 55 + 30 * i)
        # 竖琴分解和弦（谋划、尾声）
        if m in ("intrigue", "calm"):
            arp = ch + [root + 12, ch[1] + 12, ch[2]]
            for k in range(8):
                harp.note(t + k * BEAT / 2, BEAT * 1.2, arp[k % len(arp)] + 12, 38 + 30 * i)
    # 重音
    for h in HITS:
        perc.note(h, 2.5, 49, 115); perc.note(h, 0.6, 36, 127)
        taiko.note(h, 1.5, 45, 127); taiko.note(h + 0.02, 1.5, 47, 120)
        timp.note(h, 2.5, 38, 120)
        for n in (38, 45, 50, 53, 57): low.note(h, 3.5, n, 110) if n < 54 else horn.note(h, 3.5, n + 12 - 12, 105)
        pad.note(h, 4.0, 62, 100); pad.note(h, 4.0, 69, 100)
    # 开场：定音鼓滚奏引向第一记重音之后的第二记
    for k in range(24):
        timp.note(2.0 + k * 0.09, 0.1, 38, 40 + k * 3)
    perc.note(4.2, 2.0, 49, 100); taiko.note(4.2, 1.0, 45, 120)
    # 「秦兵敗矣」：合唱 + 全奏长音
    sh = A("s5_29")
    for n in (50, 57, 62, 65, 69): choir.note(sh, 7.0, n, 110)
    for k in range(10): taiko.note(sh + 1.5 + k * 0.375, 0.3, 45, 100 - k * 3)
    # 晋军渡河：号角齐鸣
    cr = A("s5_41") + 1.0
    for (bt, d, n) in [(0, 1, 62), (1, 1, 65), (2, 2, 69), (4, 4, 74)]:
        horn.note(cr + bt * BEAT, d * BEAT, n, 112); horn.note(cr + bt * BEAT, d * BEAT, n - 12, 100)
    # 屐齿折：竖琴上行 + 弦乐 D 大三和弦（皮卡第三度）余音
    for k, n in enumerate([62, 66, 69, 74, 78, 81]): harp.note(CLOG + 0.1 + k * 0.12, 3.0, n, 70)
    for n in (50, 57, 62, 66, 69): pad.note(CLOG + 0.3, TOTAL - CLOG - 0.3, n, 70)
    return tracks

def write_midi(tracks, path):
    mid = mido.MidiFile(ticks_per_beat=TPB)
    meta = mido.MidiTrack(); meta.append(mido.MetaMessage("set_tempo", tempo=int(60e6 / BPM))); mid.tracks.append(meta)
    for tr in tracks:
        mt = mido.MidiTrack(); mid.tracks.append(mt)
        ch = tr.ch
        if ch != 9: mt.append(mido.Message("program_change", channel=ch, program=tr.prog, time=0))
        mt.append(mido.Message("control_change", channel=ch, control=91, value=70, time=0))   # 混响
        mt.append(mido.Message("control_change", channel=ch, control=7, value=100, time=0))
        pan = {0: 64, 1: 50, 2: 76, 3: 84, 4: 60, 5: 64, 6: 64, 7: 54, 8: 72, 9: 64, 10: 44}[ch]
        mt.append(mido.Message("control_change", channel=ch, control=10, value=pan, time=0))
        ev = sorted(tr.ev, key=lambda e: (e[0], e[1]))
        last = 0
        for (t, kind, n, v) in ev:
            tick = int(round(t / BEAT * TPB)); dt = max(0, tick - last); last = max(last, tick)
            if kind == 1: mt.append(mido.Message("note_on", channel=ch, note=n, velocity=v, time=dt))
            elif kind == 0: mt.append(mido.Message("note_off", channel=ch, note=n, velocity=0, time=dt))
            else: mt.append(mido.Message("control_change", channel=ch, control=n, value=v, time=dt))
    mid.save(path)

if __name__ == "__main__":
    os.makedirs(f"{WORK}/music", exist_ok=True)
    tr = build()
    write_midi(tr, f"{WORK}/music/score.mid")
    subprocess.run(["fluidsynth", "-ni", "-g", "0.5", "-r", "48000", "-R", "1", "-C", "1", "-F", f"{WORK}/music/music_raw.wav", SF2, f"{WORK}/music/score.mid"], check=True, capture_output=True)
    # 裁到片长
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{WORK}/music/music_raw.wav", "-t", f"{TOTAL:.3f}", "-af", f"afade=t=out:st={TOTAL-3:.3f}:d=3", f"{WORK}/music/music.wav"], check=True)
    print("music ok", TOTAL)
