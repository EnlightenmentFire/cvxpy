"""原创配乐：程序作曲（MIDI）+ FluidR3_GM 音色库（MIT 授权）渲染。大气、有推进感的纪录片配乐。
按时间线分段设强度：0 静 / 1 铺底 / 2 推进 / 3 恢宏。D 小调，84 BPM。
python music.py  -> $WORK/music.wav
"""
import os, sys, json, subprocess, random
import mido
from render import timeline

WK = os.environ.get("WORK", "/tmp/claude-0/work")
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
TPB = 480

# 各场景强度（可在中途变化：列表里给出 (相对时间比例, 强度)）
INTENS = {
    "inn": 0.5, "inn2": 0.5, "death": 2, "timeline": 2, "levers0": 1.5, "levers": 2.5,
    "map": 1, "map2": 1, "audience": 1, "debate": 2, "debate2": 1.5,
    "pole": 2, "pole2": 2, "prince": 2, "prince2": 2,
    "ladder": 2, "ladder2": 2.5, "fields": 2, "fields2": 2, "class": 3,
    "county": 1.5, "sheng": 1, "sheng2": 1.5, "grid": 1, "grid2": 0.7, "praise": 1, "praise2": 1,
    "rise": 3, "zhaoliang": 1, "zhaoliang2": 1, "fall": 2, "fall2": 2.5, "horses": 0,
    "machine": 2.5, "machine2": 3, "slips": 2.5, "verdict": 1, "verdict2": 1, "inn3": 0.7, "end": 2, "end2": 1.2,
}
DARK = {"inn", "inn2", "death", "grid", "grid2", "praise", "praise2", "fall", "fall2", "horses", "inn3", "zhaoliang2"}

# 和弦（根音 MIDI 号与和弦音）
D, F, G, A, Bb, C, E = 50, 53, 55, 57, 58, 60, 52
PROG_BRIGHT = [(D, [0, 3, 7]), (Bb - 12, [0, 4, 7]), (F, [0, 4, 7]), (C - 12, [0, 4, 7])]     # i VI III VII
PROG_DARK = [(D, [0, 3, 7]), (G, [0, 3, 7]), (Bb - 12, [0, 4, 7]), (A - 12, [0, 4, 7])]      # i iv VI V
PENTA = [62, 64, 65, 67, 69, 72, 74, 76, 77]   # D 小调音阶片段

CH = dict(pad=0, bass=1, ost=2, horn=3, timp=4, choir=5, harp=6, taiko=7, cello=8)
PROG = dict(pad=48, bass=43, ost=49, horn=60, timp=47, choir=52, harp=46, taiko=116, cello=42)


def build(segs, total):
    mid = mido.MidiFile(ticks_per_beat=TPB)
    tracks = {k: mido.MidiTrack() for k in CH}
    for k, tr in tracks.items():
        mid.tracks.append(tr)
        tr.append(mido.Message("program_change", channel=CH[k], program=PROG[k], time=0))
        tr.append(mido.Message("control_change", channel=CH[k], control=91, value=70, time=0))   # reverb
        tr.append(mido.Message("control_change", channel=CH[k], control=7, value=100, time=0))
    tracks["pad"].insert(0, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    ev = {k: [] for k in CH}   # (abs_sec, type, note, vel)

    def note(k, t, n, dur, vel):
        if vel <= 0:
            return
        ev[k].append((t, "on", n, min(127, int(vel))))
        ev[k].append((t + dur, "off", n, 0))

    def intens_at(t):
        for s in segs:
            if s["start"] <= t < s["end"]:
                return INTENS.get(s["sc"], 1), s["sc"]
        return 1, "end2"

    nbars = int(total / BAR) + 2
    rnd = random.Random(5)
    prev_I = 0
    for b in range(nbars):
        t0 = b * BAR
        if t0 > total - 0.5:
            break
        I, sc = intens_at(t0 + 0.1)
        dark = sc in DARK
        prog = PROG_DARK if dark else PROG_BRIGHT
        root, iv = prog[b % 4]
        fade_out = max(0.0, min(1.0, (total - t0) / 6.0))
        g = fade_out
        # 铺底弦乐（始终有）
        for k in iv:
            note("pad", t0, root + k + 12, BAR * 0.98, (38 + 10 * I) * g)
        note("bass", t0, root - 12, BAR * 0.98, (40 + 12 * I) * g)
        if I >= 1.5:   # 推进：低音弦乐八分音符脉动
            for q in range(8):
                acc = 1.15 if q % 4 == 0 else 1.0
                note("ost", t0 + q * BEAT / 2, root, BEAT / 2 * 0.8, (30 + 14 * I) * acc * g)
                note("cello", t0 + q * BEAT / 2, root - 12 + (7 if q % 4 == 2 else 0), BEAT / 2 * 0.8, (28 + 12 * I) * acc * g)
        if I >= 2:     # 定音鼓每小节
            note("timp", t0, root - 12 if root - 12 >= 38 else root, BEAT, (50 + 15 * I) * g)
            if I >= 2.5:
                note("timp", t0 + 2.5 * BEAT, root - 12 if root - 12 >= 38 else root, BEAT / 2, (40 + 10 * I) * g)
        if I >= 2.5:   # 圆号长音旋律
            mel = [root + 12 + iv[1], root + 12 + iv[2], root + 24, root + 12 + iv[2]]
            note("horn", t0, mel[b % 4], BAR * 0.95, (44 + 14 * I) * g)
        if I >= 3:     # 合唱 + 太鼓
            for k in iv:
                note("choir", t0, root + k + 12, BAR * 0.95, (40 + 8 * I) * g)
            for q in (0, 1.5, 2, 3):
                note("taiko", t0 + q * BEAT, 45, BEAT / 2, (55 + 10 * (q == 0)) * g)
        if 0.6 <= I <= 1.6 and not dark:   # 安静段：竖琴五声琶音（古意）
            for q in range(4):
                n = rnd.choice(PENTA[:7])
                note("harp", t0 + q * BEAT + rnd.uniform(0, 0.05), n, BEAT * 1.5, 34 * g)
        if dark and I <= 1:   # 暗段：低弦心跳
            note("timp", t0, 38, BEAT / 2, 34 * g)
            note("timp", t0 + 0.35, 38, BEAT / 2, 26 * g)
        prev_I = I
    # 写入轨道
    for k, tr in tracks.items():
        evs = sorted(ev[k], key=lambda e: (e[0], e[1] == "on"))
        last = 0
        for t, typ, n, v in evs:
            tick = int(round(t / BEAT * TPB))
            dt = max(0, tick - last); last = tick
            if typ == "on":
                tr.append(mido.Message("note_on", channel=CH[k], note=n, velocity=v, time=dt))
            else:
                tr.append(mido.Message("note_off", channel=CH[k], note=n, velocity=0, time=dt))
    return mid


if __name__ == "__main__":
    lines, segs, total = timeline()
    mid = build(segs, total)
    mp = f"{WK}/music.mid"; mid.save(mp)
    raw = f"{WK}/music_raw.wav"
    subprocess.run(["fluidsynth", "-ni", "-g", "0.6", "-r", "48000", "-F", raw, "/usr/share/sounds/sf2/FluidR3_GM.sf2", mp],
                   check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-t", f"{total:.3f}", "-af",
                    "highpass=f=35,lowpass=f=12000,afade=t=in:d=1.5", "-ar", "48000", "-ac", "2", f"{WK}/music.wav"], check=True)
    print("music ok", total)
