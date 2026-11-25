# -*- coding: utf-8 -*-
"""音频：旁白按时间轴拼接；配乐与音效全部用 numpy 程序合成（原创，无外部素材，可商用）。
配乐：低音弦乐铺底（D 小调）、近古琴音色的拨弦、下邳之围与出走段的战鼓。旁白处自动压低。
输出：$WORK/audio/voice.wav  music.wav  sfx.wav  mix.wav（含乐）  mix_nomusic.wav（无配乐，只有旁白和音效）
"""
import os, sys, json, math, subprocess
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
OUT = f"{WORK}/audio"
SR = 48000
T = timeline.build()
N = int((T["total"] + 0.5) * SR)
rng = np.random.default_rng(7)
SC = {s["id"]: s for s in T["scenes"]}


def cue(sid, name):
    return SC[sid]["cues"][name]


def put(buf, t0, x, g=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * g


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2)); return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high"); return signal.lfilter(b, a, x)


def bp(x, f0, f1, order=2):
    b, a = signal.butter(order, [f0 / (SR / 2), f1 / (SR / 2)], "band"); return signal.lfilter(b, a, x)


# ───────── 旁白 ─────────
def narration():
    out = np.zeros(N, np.float32)
    for l in T["lines"]:
        p = f"{WORK}/tts/proc/{l['id']}.wav"
        if not os.path.exists(p):
            continue
        w, sr = sf.read(p, dtype="float32")
        put(out, l["t0"], w)
    return out


# ───────── 乐器 ─────────
NOTE = {n: 440 * 2 ** ((i - 9) / 12) for i, n in enumerate(["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])}


def hz(name):
    n, o = name[:-1], int(name[-1])
    return NOTE[n] * 2 ** (o - 4)


def strings(freqs, dur, gain=1.0, att=1.6, rel=2.2, bright=1.0):
    n = int((dur + rel) * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.13):
            ff = f * (1 + det / 100 * 4)
            vib = 1 + 0.002 * np.sin(2 * np.pi * (4.6 + det) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * ff * np.cumsum(vib) / SR
            for h in range(1, 9):
                if ff * h > 3500:
                    break
                y += (bright ** (h - 1)) / h * np.sin(h * ph + rng.uniform(0, 6))
    env = np.minimum(1, t / att) * np.clip((dur + rel - t) / rel, 0, 1)
    env *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.15 * t)
    return (y * env * gain / (len(freqs) * 3)).astype(np.float32)


def qin(f, gain=1.0, dur=4.0, slide=0.0):
    """拨弦（近古琴）：非谐泛音 + 指甲噪声 + 可选滑音。"""
    n = int(dur * SR); t = np.arange(n) / SR
    bend = 1 + slide * np.clip((t - 0.35) / 0.6, 0, 1)
    ph = 2 * np.pi * f * np.cumsum(bend) / SR
    y = np.zeros(n)
    for h in range(1, 9):
        y += (1 / h ** 1.1) * np.sin(h * ph * (1 + 0.0004 * h * h)) * np.exp(-t * (1.1 + 0.9 * h))
    nz = bp(rng.normal(0, 1, n), 1500, 6000) * np.exp(-t * 60) * 0.25
    y = (y + nz) * np.minimum(1, t * 600)
    return (y * gain * 0.45).astype(np.float32)


def drum(gain=1.0, f0=55, dur=2.0, tone=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-t * 26)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 3.4) + 0.4 * np.sin(ph * 1.52 + 0.3) * np.exp(-t * 6)
    skin = bp(rng.normal(0, 1, n), 160, 1500) * np.exp(-t * 28) * 0.5 * tone
    return ((body + skin) * gain).astype(np.float32)


def tick(gain=0.4):
    n = int(0.3 * SR); t = np.arange(n) / SR
    return ((bp(rng.normal(0, 1, n), 900, 3800) * np.exp(-t * 55) + 0.5 * np.sin(2 * np.pi * 220 * t) * np.exp(-t * 40)) * gain).astype(np.float32)


def reverb(x, wet=0.25, tail=2.8):
    n = int(tail * SR); t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 2.4); ir = lp(ir, 3000); ir[:int(0.015 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    return (x + wet * signal.fftconvolve(x, ir)[:len(x)]).astype(np.float32)


# ───────── 配乐编排 ─────────
CH = {  # 和弦（低→高）
    "Dm": ["D2", "A2", "D3", "F3"], "Bb": ["Bb1", "F2", "Bb2", "D3"], "Gm": ["G1", "D2", "G2", "Bb2"], "A": ["A1", "E2", "A2", "C#3"],
    "F": ["F2", "C3", "F3", "A3"], "C": ["C2", "G2", "C3", "E3"], "Am": ["A1", "E2", "A2", "C3"], "Eb": ["Eb2", "Bb2", "Eb3", "G3"],
    "D": ["D2", "A2", "D3", "F#3"],
}
# 场景：(和弦序列, 弦乐增益, 古琴密度/秒, 鼓型, 亮度)
PLAN = {
    "A": (["Dm"], 0.55, 0.0, None, 0.6), "B": (["Dm", "Eb"], 0.6, 0.15, None, 0.6), "C": (["Bb", "F"], 0.55, 0.25, None, 0.7),
    "D": (["Dm", "Bb", "Gm", "A"], 0.6, 0.2, None, 0.7), "E": (["Dm", "Bb", "Gm", "A"], 0.6, 0.12, "pulse", 0.65),
    "F": (["Gm", "Dm"], 0.5, 0.25, None, 0.6), "G": (["Bb", "F", "C", "Dm"], 0.55, 0.2, None, 0.7),
    "H": (["Dm", "Eb", "Dm", "A"], 0.7, 0.0, "war", 0.75), "I": (["Bb", "F"], 0.45, 0.15, None, 0.6),
    "J": (["Dm", "F"], 0.4, 0.35, None, 0.6), "K": (["Gm", "Dm", "Bb", "A"], 0.5, 0.3, None, 0.65),
    "L": (["Bb", "F", "C", "Dm"], 0.55, 0.25, None, 0.7), "M": (["Dm", "Eb"], 0.55, 0.0, "heart", 0.55),
    "N": (["Dm"], 0.45, 0.1, None, 0.55), "O": (["Eb", "Dm"], 0.5, 0.1, None, 0.55), "P": (["Gm", "Dm", "Eb", "A"], 0.55, 0.15, "heart", 0.6),
    "Q": (["Dm", "Bb", "C", "A"], 0.65, 0.0, "march", 0.75), "R": (["Dm", "Eb", "Dm", "A"], 0.7, 0.0, "war", 0.75),
    "S": (["Bb", "F", "Gm", "A"], 0.6, 0.15, "march_soft", 0.7), "T": (["Dm", "F"], 0.4, 0.3, None, 0.6),
    "U": (["Bb", "F", "C", "Dm"], 0.5, 0.25, None, 0.65), "V": (["Bb", "F", "Gm", "D"], 0.55, 0.3, None, 0.65),
}
PENTA = ["D4", "F4", "G4", "A4", "C5", "D5", "F5", "G5", "A3", "C4"]


def music():
    y = np.zeros(N, np.float32)
    drums = np.zeros(N, np.float32)
    for s in T["scenes"]:
        chords, g, qd, dr, br = PLAN[s["id"]]
        t0, t1 = s["t0"], s["t1"]
        L = t1 - t0
        seg = max(5.0, L / max(1, len(chords)) if L / len(chords) < 10 else 8.0)
        t = t0; k = 0
        while t < t1 - 0.5:
            d = min(seg, t1 - t)
            put(y, t - 0.6, strings([hz(n) for n in CH[chords[k % len(chords)]]], d + 0.6, g, att=1.8, rel=2.0, bright=br))
            t += seg; k += 1
        # 古琴
        if qd > 0:
            tt = t0 + rng.uniform(0.5, 2.0)
            while tt < t1 - 1:
                nn = PENTA[rng.integers(0, len(PENTA))]
                put(y, tt, qin(hz(nn), 0.9 * rng.uniform(0.7, 1.0), slide=rng.choice([0, 0, -0.03, 0.04])))
                if rng.uniform() < 0.35:
                    put(y, tt + 0.28, qin(hz(nn) * 1.5, 0.5))
                tt += rng.exponential(1 / qd) + 0.6
        # 鼓
        if dr == "pulse":
            tt = t0 + 1
            while tt < t1 - 1:
                put(drums, tt, drum(0.45, 60, 1.5, 0.5)); tt += 1.6
        elif dr == "heart":
            tt = t0 + 0.8
            while tt < t1 - 1:
                put(drums, tt, drum(0.5, 48, 1.0, 0.2)); put(drums, tt + 0.28, drum(0.35, 46, 1.0, 0.2)); tt += 1.25
        elif dr in ("war", "march", "march_soft"):
            bpm = {"war": 92, "march": 100, "march_soft": 84}[dr]
            b = 60 / bpm; tt = t0 + 0.5; i = 0
            ramp_in = 6.0
            while tt < t1 - 0.8:
                gg = min(1, (tt - t0) / ramp_in + 0.3) * (0.6 if dr == "march_soft" else 1.0)
                if i % 4 == 0:
                    put(drums, tt, drum(0.9 * gg, 52, 2.2, 1.0))
                elif i % 4 == 2:
                    put(drums, tt, drum(0.6 * gg, 58, 1.6, 0.8))
                if dr != "march_soft":
                    put(drums, tt + b / 2, tick(0.22 * gg))
                if dr == "war" and i % 8 == 7:
                    put(drums, tt + b * 0.5, drum(0.5 * gg, 70, 1.0, 1.0)); put(drums, tt + b * 0.75, drum(0.5 * gg, 70, 1.0, 1.0))
                tt += b; i += 1
    y = reverb(lp(y, 2600), 0.3)
    drums = reverb(drums, 0.22, 2.0)
    # 片尾淡出
    fo = int(3.0 * SR); y[-fo:] *= np.linspace(1, 0, fo); drums[-fo:] *= np.linspace(1, 0, fo)
    return y + drums * 0.9


# ───────── 音效 ─────────
def thunder(gain=1.0, crack=True, dur=5.5):
    n = int(dur * SR); t = np.arange(n) / SR
    rumble = lp(rng.normal(0, 1, n), 180, 3) * (np.exp(-t * 0.9) * (1 + 0.6 * np.sin(2 * np.pi * 1.7 * t) * np.exp(-t)))
    rumble *= np.minimum(1, t / 0.08)
    y = rumble * 3.0
    if crack:
        cr = hp(rng.normal(0, 1, n), 600) * np.exp(-t * 18) * 1.2 + bp(rng.normal(0, 1, n), 200, 2500) * np.exp(-t * 6) * 0.6
        y += cr
    return (y * gain / np.abs(y).max()).astype(np.float32)


def clink(gain=1.0, f=2600):
    """象牙/木箸落案：短促的硬木敲击 + 高频泛音。"""
    n = int(0.6 * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for k, (m, d) in enumerate([(1, 38), (2.76, 55), (5.4, 80), (8.9, 110)]):
        y += np.sin(2 * np.pi * f * m * t / 2.76 + k) * np.exp(-t * d) / (k + 1)
    y += bp(rng.normal(0, 1, n), 1500, 7000) * np.exp(-t * 120) * 0.8
    return (y * gain / np.abs(y).max()).astype(np.float32)


def rain(dur, gain=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    y = bp(rng.normal(0, 1, n), 1200, 9000) * (0.6 + 0.4 * lp(np.abs(rng.normal(0, 1, n)), 3))
    env = np.minimum(1, t / 2) * np.minimum(1, (dur - t) / 2)
    return (y * env * gain / 3).astype(np.float32)


def water(dur, gain=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    y = lp(rng.normal(0, 1, n), 700, 2) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t))
    env = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 2)
    return (y * env * gain).astype(np.float32)


def crowd(dur, gain=0.4):
    n = int(dur * SR); t = np.arange(n) / SR
    y = bp(rng.normal(0, 1, n), 150, 900) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t + 1))
    env = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5)
    return (y * env * gain).astype(np.float32)


def whoosh(gain=0.3, dur=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    y = bp(rng.normal(0, 1, n), 800, 5000) * np.sin(np.pi * t / dur) ** 2
    return (y * gain).astype(np.float32)


def thud(gain=0.8):
    n = int(1.5 * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 70 * (1 + 0.5 * np.exp(-t * 30)) * t) * np.exp(-t * 6) + lp(rng.normal(0, 1, n), 400) * np.exp(-t * 25) * 2
    return (y * gain / np.abs(y).max()).astype(np.float32)


def chime(gain=0.3):
    n = int(3 * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((1318, 1.5), (1976, 2.0), (2637, 2.6)))
    return (y * gain / 3).astype(np.float32)


def sfx():
    y = np.zeros(N, np.float32)
    A = SC["A"]["t0"]
    put(y, A + 0.0, thunder(1.0))
    for k in range(3):
        put(y, A + 0.41 + 0.04 * k, clink(0.9 - 0.15 * k, 2600 + 300 * k))
        put(y, A + 0.41 + 0.04 * k + 0.09, clink(0.3, 2900))
    put(y, A + 6.3, thunder(0.6, crack=False))
    put(y, A + 4.0, rain(SC["A"]["t1"] - A - 4.0 + 0.5, 0.25))
    # D 金印落定
    put(y, SC["D"]["t0"] + 0.85, thud(0.8)); put(y, SC["D"]["t0"] + 0.9, chime(0.35))
    # B/E 吕布夺城
    put(y, cue("B", "lost") + 0.6, thud(0.5))
    put(y, cue("E", "lvbu") + 1.2, thud(0.5))
    # H 下邳之围
    put(y, cue("H", "march"), crowd(cue("H", "collapse") - cue("H", "march") + 2, 0.22))
    tsg, tcl = cue("H", "siege"), cue("H", "collapse")
    tt = tsg + 1
    while tt < tcl:
        put(y, tt, whoosh(0.18, 0.45)); tt += rng.uniform(0.25, 0.7)
    put(y, cue("H", "flood"), water(cue("H", "capture") - cue("H", "flood") + 2, 0.55))
    put(y, cue("H", "capture"), thud(0.7))
    # N 匕箸落案、O 雷
    td = cue("N", "drop")
    for k in range(3):
        put(y, td + 0.64 + 0.04 * k, clink(0.8 - 0.15 * k, 2600 + 300 * k))
    put(y, td + 1.0, thud(0.6))
    th = cue("O", "thunder")
    put(y, th + 0.32, thunder(1.0)); put(y, th + 0.78, thunder(0.6, crack=False))
    put(y, SC["O"]["t0"], rain(SC["O"]["t1"] - SC["O"]["t0"], 0.25))
    # Q 聚众
    put(y, cue("Q", "rally"), crowd(5.0, 0.3))
    put(y, cue("Q", "chezhou") + 0.8, thud(0.5))
    # S 印到邺、新野时发光
    for k in ("ye", "xinye"):
        put(y, cue("S", k) + 1.0, chime(0.3))
    # V 周易
    put(y, cue("V", "zhouyi"), chime(0.3))
    return y


def env_follow(x, rel=0.4):
    b = int(0.03 * SR)
    e = np.sqrt(signal.lfilter(np.ones(b) / b, [1], x.astype(np.float64) ** 2))
    k = math.exp(-1 / (rel * SR / 256)); out = np.zeros(len(e)); v = 0.0
    for i in range(0, len(e), 256):
        m = e[i:i + 256].max(); v = max(m, v * k); out[i:i + 256] = v
    return out


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = r.rfind("Integrated loudness:")
    return float(r[i:].split("I:")[1].split("LUFS")[0])


def main():
    os.makedirs(OUT, exist_ok=True)
    v = narration(); m = music(); fx = sfx()
    sf.write(f"{OUT}/voice.wav", v, SR, subtype="FLOAT")
    # 闪避：有旁白时音乐再压 6 dB
    e = env_follow(v)
    act = np.clip(e / 0.02, 0, 1)
    duck = (1 - 0.5 * act).astype(np.float32)
    m = m * duck
    sf.write(f"{OUT}/music_raw.wav", m, SR, subtype="FLOAT")
    lv = lufs(f"{OUT}/voice.wav"); lm = lufs(f"{OUT}/music_raw.wav")
    target_gap = float(os.environ.get("MUSIC_GAP", 21.0))
    gm = 10 ** ((lv - target_gap - lm) / 20)
    m = m * gm
    sf.write(f"{OUT}/music.wav", m, SR, subtype="FLOAT")
    sf.write(f"{OUT}/sfx.wav", fx * 0.35, SR, subtype="FLOAT")
    print(f"voice {lv:.1f} LUFS, music (ducked) {lv - target_gap:.1f} LUFS, gap {target_gap} dB")
    sf.write(f"{OUT}/mix_pre.wav", v + m + fx * 0.35, SR, subtype="FLOAT")
    sf.write(f"{OUT}/nomusic_pre.wav", v + fx * 0.35, SR, subtype="FLOAT")
    for src, dst in (("mix_pre", "mix"), ("nomusic_pre", "mix_nomusic")):
        # 两遍 loudnorm 到 -15 LUFS / -1.5 dBTP
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{OUT}/{src}.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        js = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
        af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
              f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{OUT}/{src}.wav", "-af", af, "-ar", "48000", f"{OUT}/{dst}.wav"], check=True)
        print(dst, "LUFS", lufs(f"{OUT}/{dst}.wav"))


if __name__ == "__main__":
    main()
