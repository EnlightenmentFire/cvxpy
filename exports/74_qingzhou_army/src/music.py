# -*- coding: utf-8 -*-
"""原创配乐：按时间线写 MIDI（鼓、定音鼓、低音弦乐、号角、合唱），用 FluidR3_GM（MIT 许可）渲染。
战争题材：恢宏鼓与号角；收编段弦乐推进。D 羽调五声（D F G A C）。"""
import os, subprocess, math, random
import mido
from timeline import build

OUT = "/tmp/claude-0/w74/audio"
os.makedirs(OUT, exist_ok=True)
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
TPS = 960  # ticks per second (tempo 120, 480 tpb)

PROG = {"taiko": 116, "timp": 47, "str": 48, "str2": 49, "bass": 43, "horn": 60, "brass": 61, "choir": 52, "cello": 42, "hit": 55}
CH = {"taiko": 0, "timp": 1, "str": 2, "str2": 3, "bass": 4, "horn": 5, "brass": 6, "choir": 7, "cello": 8, "hit": 10 - 1 + 2}
# 注意避开 9（GM 打击乐通道）
CH["hit"] = 11

D = 50  # D3
SC = [0, 3, 5, 7, 10]  # D F G A C


def deg(k, base=D):
    o, i = divmod(k, 5)
    return base + 12 * o + SC[i]


class Score:
    def __init__(s):
        s.ev = []  # (time_s, msg)

    def note(s, inst, t, dur, n, vel):
        vel = int(max(1, min(127, vel)))
        s.ev.append((t, mido.Message("note_on", channel=CH[inst], note=int(n), velocity=vel)))
        s.ev.append((t + dur, mido.Message("note_off", channel=CH[inst], note=int(n), velocity=0)))

    def cc(s, inst, t, ctl, val):
        s.ev.append((t, mido.Message("control_change", channel=CH[inst], control=ctl, value=int(max(0, min(127, val))))))

    def save(s, path):
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=500000))
        for k, p in PROG.items():
            tr.append(mido.Message("program_change", channel=CH[k], program=p, time=0))
            tr.append(mido.Message("control_change", channel=CH[k], control=91, value=70, time=0))  # reverb
            tr.append(mido.Message("control_change", channel=CH[k], control=7, value=100, time=0))
        evs = sorted(s.ev, key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1))
        last = 0
        for t, m in evs:
            tk = int(round(t * TPS))
            tr.append(m.copy(time=max(0, tk - last))); last = max(last, tk)
        mid.save(path)


def sections(lines):
    sec = {}
    for d in lines:
        sec.setdefault(d["scene"], [d["start"], d["end"]])
        sec[d["scene"]][1] = d["end"]
    ev = {d["v"]: d["start"] for d in lines}
    return sec, ev


def drums(sc, t0, t1, bpm, inten, pattern="war"):
    """太鼓节奏：每小节 8 个八分音符"""
    beat = 60 / bpm
    pat = {"war": [1, 0, 0, 1, 1, 0, 1, 0], "march": [1, 0, 1, 0, 1, 0, 1, 1], "heart": [1, 0, 0, 0, 0.6, 0, 0, 0],
           "build": [1, 0, 1, 1, 1, 0, 1, 1]}[pattern]
    t = t0; k = 0
    while t < t1:
        v = pat[k % 8]
        if v:
            iv = inten(t) if callable(inten) else inten
            sc.note("taiko", t, 0.4, 41 if k % 8 == 0 else 45, 70 + 50 * iv * v)
            if k % 8 == 0 and iv > 0.5:
                sc.note("timp", t, 0.6, 38, 60 + 50 * iv)
        t += beat / 2; k += 1


def ostinato(sc, t0, t1, bpm, vel, root=D - 12):
    beat = 60 / bpm
    seq = [0, 0, 3, 0, 0, 5, 3, 0]
    t = t0; k = 0
    while t < t1:
        v = vel(t) if callable(vel) else vel
        sc.note("str", t, beat * 0.45, root + seq[k % 8], v)
        if k % 2 == 0:
            sc.note("bass", t, beat * 0.9, root + seq[k % 8] - 12 + 12, v * 0.8)
        t += beat / 2; k += 1


def pad(sc, t0, t1, chords, vel, inst="str2", hold=4.0):
    t = t0; k = 0
    while t < t1:
        ch = chords[k % len(chords)]
        v = vel(t) if callable(vel) else vel
        d = min(hold, t1 - t)
        for n in ch:
            sc.note(inst, t, d + 0.3, n, v)
        t += hold; k += 1


def horn_call(sc, t, notes, vel, inst="horn", unit=0.6):
    for n, l in notes:
        if n:
            sc.note(inst, t, unit * l * 0.95, n, vel)
        t += unit * l
    return t


def roll(sc, t, dur, v0, v1, n=38):
    k = 0; step = 0.07
    while k * step < dur:
        u = k * step / dur
        sc.note("timp", t + k * step, 0.12, n, v0 + (v1 - v0) * u)
        k += 1


def build_score(lines, total):
    sec, ev = sections(lines)
    sc = Score()
    Dm = [D - 12, D - 5, D, D + 3]          # D 低五度和弦
    Bb = [D - 16, D - 9, D - 4, D + 1]
    C_ = [D - 14, D - 7, D - 2, D + 5]
    F_ = [D - 9, D - 2, D + 3, D + 7]
    Am = [D - 5, D + 2, D + 7, D + 10]
    # ---------------- 钩子：开场就起，鼓 + 号角
    h0, h1 = 0.0, sec["bian"][0] - 0.3
    sc.note("hit", 0.02, 1.2, D, 110); sc.note("hit", 0.02, 1.2, D - 12, 110)
    roll(sc, 0.0, 1.6, 50, 105)
    drums(sc, 0.0, h1, 92, lambda t: 0.75 if t < 30 else 0.55, "war")
    ostinato(sc, 1.0, h1, 92, lambda t: 62)
    pad(sc, 0.5, h1, [Dm, Bb, C_, Dm], 50, hold=5.2)
    horn_call(sc, 2.0, [(D + 12, 2), (D + 19, 1), (D + 17, 1), (D + 15, 2), (D + 12, 3)], 90)
    horn_call(sc, ev["tide_flash"], [(D + 12, 1), (D + 15, 1), (D + 19, 2), (D + 24, 4)], 100, "brass", 0.55)
    sc.note("hit", ev["tide_flash"], 1.0, D, 100)
    roll(sc, ev["question"] - 1.6, 1.6, 40, 95)
    sc.note("hit", ev["thesis"], 1.2, D, 105)
    # ---------------- 汴水：行军鼓 + 低弦
    b0, b1 = sec["bian"][0], sec["yan"][0] - 0.3
    drums(sc, b0, ev["battle_bian"], 84, 0.4, "march")
    ostinato(sc, b0 + 2, b1, 84, lambda t: 54 if t < ev["battle_bian"] else 48)
    pad(sc, b0, b1, [Dm, F_, C_, Dm], 46, hold=5.7)
    roll(sc, ev["battle_bian"] - 1.5, 1.5, 50, 110)
    drums(sc, ev["battle_bian"], ev["defeat_stamp"], 104, 1.0, "build")
    horn_call(sc, ev["battle_bian"] + 0.5, [(D + 12, 2), (D + 10, 1), (D + 7, 3)], 96, "brass", 0.5)
    sc.note("hit", ev["defeat_stamp"], 1.5, D - 12, 100)
    horn_call(sc, ev["fame"], [(D + 7, 2), (D + 12, 2), (D + 15, 2), (D + 19, 4)], 82, "horn", 0.7)
    # ---------------- 兖州：政治段，心跳鼓 + 弦乐铺底，迎曹时抬起
    y0, y1 = sec["yan"][0], sec["qing"][0] - 0.3
    pad(sc, y0, y1, [Dm, Bb, F_, C_], 44, hold=6.4)
    drums(sc, y0, ev["tide_in"], 70, 0.3, "heart")
    drums(sc, ev["tide_in"], ev["no_master"], 88, 0.6, "war")
    ostinato(sc, ev["tide_in"], ev["no_master"], 88, 52)
    drums(sc, ev["no_master"], ev["welcome"], 70, 0.25, "heart")
    horn_call(sc, ev["welcome"] + 0.5, [(D + 12, 2), (D + 15, 1), (D + 17, 1), (D + 19, 3), (D + 24, 4)], 92, "horn", 0.6)
    sc.note("hit", ev["thesis2"], 1.2, D, 95)
    # ---------------- 青州兵：寿张激战 -> 收编（弦乐推进，合唱，全奏）-> 机制段平稳
    q0 = sec["qing"][0]
    roll(sc, q0 - 1.2, 1.2, 40, 100)
    drums(sc, q0, ev["wood_statue"], 100, lambda t: 0.6 if t < ev["ambush"] else 0.9, "war")
    ostinato(sc, q0, ev["wood_statue"], 100, 60)
    pad(sc, q0, ev["wood_statue"], [Dm, C_, Bb, C_], 50, hold=4.8)
    sc.note("hit", ev["baoxin_die"], 1.2, D - 12, 90)
    pad(sc, ev["wood_statue"], ev["chase_jibei"], [Dm], 40, "cello", hold=8)
    # 收编推进：从 chase 起，逐渐加密加强，transform 处全奏
    tA, tB = ev["chase_jibei"], ev["transform"]
    drums(sc, tA, tB, 96, lambda t: 0.4 + 0.5 * (t - tA) / max(1, tB - tA), "build")
    ostinato(sc, tA, ev["why3"], 96, lambda t: 50 + 30 * min(1, max(0, (t - tA) / max(1, tB - tA))))
    roll(sc, tB - 2.0, 2.0, 50, 120)
    t = tB
    for k, ch in enumerate([Dm, F_, C_, Dm, Bb, C_, Dm]):
        for n in ch:
            sc.note("str2", t, 3.2, n + 12, 92); sc.note("choir", t, 3.2, n + 12, 78)
        sc.note("brass", t, 3.0, ch[0] + 12, 96)
        t += 3.0
    horn_call(sc, tB + 0.2, [(D + 12, 2), (D + 15, 1), (D + 19, 1), (D + 24, 3), (D + 22, 1), (D + 19, 2), (D + 24, 5)], 110, "horn", 0.6)
    drums(sc, tB, ev["why3"], 96, 1.0, "war")
    sc.note("hit", tB, 1.5, D, 120); sc.note("hit", tB, 1.5, D - 12, 120)
    w0 = ev["why3"]; w1 = sec["view"][0] - 0.3
    pad(sc, w0, w1, [Dm, F_, C_, Am], 42, hold=6.0)
    drums(sc, w0, w1, 76, 0.25, "heart")
    horn_call(sc, ev["card3_c"], [(D + 12, 2), (D + 19, 2), (D + 24, 4)], 80, "horn", 0.7)
    # ---------------- 战略观：庄重
    v0, v1 = sec["view"][0], sec["novel"][0] - 0.3
    pad(sc, v0, v1, [Dm, Bb, F_, C_], 46, hold=6.0)
    sc.note("hit", ev["cao_quote"], 1.5, D, 95)
    horn_call(sc, ev["cao_quote"] + 0.3, [(D + 12, 3), (D + 19, 3), (D + 24, 6)], 92, "horn", 0.6)
    drums(sc, ev["revolt"], ev["qing_leave"], 88, 0.5, "war")
    drums(sc, ev["qing_leave"], v1, 72, 0.7, "march")
    # ---------------- 演义对照：轻
    n0, n1 = sec["novel"][0], sec["end"][0] - 0.3
    pad(sc, n0, n1, [Dm, C_], 40, hold=6.0)
    # ---------------- 收束：最后一次全奏在 end_quote，余音
    e0 = sec["end"][0]
    pad(sc, e0, ev["end_quote"], [Dm, F_, C_, Dm], 50, hold=5.0)
    drums(sc, ev["end_c"], ev["end_quote"], 84, 0.6, "build")
    roll(sc, ev["end_quote"] - 1.4, 1.4, 50, 115)
    t = ev["end_quote"]
    for ch in [Dm, Bb, C_, Dm]:
        for n in ch:
            sc.note("str2", t, 3.0, n + 12, 90); sc.note("choir", t, 3.0, n + 12, 70)
        sc.note("brass", t, 2.8, ch[0] + 12, 92)
        t += 2.8
    sc.note("hit", ev["end_quote"], 1.5, D, 115)
    horn_call(sc, ev["end_quote"] + 0.2, [(D + 12, 2), (D + 19, 2), (D + 24, 6)], 105, "horn", 0.7)
    pad(sc, ev["next"], total + 2, [Dm], 44, "cello", hold=12)
    sc.note("timp", total - 2.2, 2.0, 38, 80)
    return sc


def render():
    lines, total = build()
    sc = build_score(lines, total)
    sc.save(f"{OUT}/score.mid")
    subprocess.run(["fluidsynth", "-ni", "-g", "0.8", "-r", "48000", "-R", "1", "-C", "1", "-F", f"{OUT}/music_raw.wav", SF2, f"{OUT}/score.mid"],
                   check=True, capture_output=True)
    # 截到总长，尾部淡出
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/music_raw.wav", "-af",
                    f"atrim=0:{total:.2f},afade=t=out:st={total - 3:.2f}:d=3,highpass=f=35", "-ar", "48000", "-ac", "2", f"{OUT}/music.wav"], check=True)
    print("music", total)


if __name__ == "__main__":
    render()
