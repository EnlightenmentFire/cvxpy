# -*- coding: utf-8 -*-
"""Background music, synthesised from scratch, built around three ideas:

1. 题材情绪 — each chapter gets its own mood (key, tempo, instrument, pattern).
2. 三层起伏 — three stems rendered separately and faded in/out by a story-driven
   intensity schedule:
       L1 底层  bed: soft pad + bass (always there, the floor)
       L2 中层  motion: arpeggio / pulse / shaker (when the story moves)
       L3 顶层  top: melodic line + bell (only at peaks: title, takeaways, ending)
3. 侧链 — handled in mix.py: a voice-keyed, band-split compressor on the music bus.

NOTE: provisional implementation; replace parameters once 配乐规范.md is available.
"""
import math

import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

SR = 48000
RNG = np.random.default_rng(2024)


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ instruments
def pluck(freq, dur=1.4, vel=1.0, bright=0.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k in range(1, 9):
        f = freq * k * (1 + 0.0007 * k * k)
        if f > 9000:
            break
        amp = (1.0 / k ** 1.4) * (bright if k > 2 else 1.0)
        out += (amp * np.exp(-(2.2 + 1.6 * k) * t) * np.sin(2 * np.pi * f * t + RNG.uniform(0, 6.28))).astype(np.float32)
    return (out * np.minimum(1, t / 0.006) * vel * 0.35).astype(np.float32)


def epiano(freq, dur=2.2, vel=1.0):
    """Soft electric-piano-ish tone (sine + bell partial, slow decay)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) * np.exp(-1.6 * t)
         + 0.35 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-3.0 * t)
         + 0.12 * np.sin(2 * np.pi * freq * 3.98 * t) * np.exp(-7.0 * t))
    tail = np.clip((dur - t) / 0.2, 0, 1)
    return (s * np.minimum(1, t / 0.004) * tail * vel * 0.3).astype(np.float32)


def bell(freq, dur=2.5, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) * np.exp(-2.2 * t)
         + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-4.0 * t)
         + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-7.0 * t))
    return (s * np.minimum(1, t / 0.002) * vel * 0.18).astype(np.float32)


def bass(freq, dur=1.3, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 0.012) * np.exp(-1.8 * t) * np.clip((dur - t) / 0.08, 0, 1)
    w = np.sin(2 * np.pi * freq * t) + 0.22 * np.sin(4 * np.pi * freq * t)
    return (w * env * vel * 0.34).astype(np.float32)


def pad(freqs, dur, att=1.5, rel=1.5, vel=1.0, cutoff=1100):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.0035, 0.0, 0.004):
            saw = 2 * ((t * f * (1 + det) + RNG.uniform(0, 1)) % 1.0) - 1
            out += saw.astype(np.float32)
    out = sosfilt(butter(2, cutoff, btype="lowpass", fs=SR, output="sos"), out).astype(np.float32)
    env = np.clip(np.minimum(t / att, (dur - t) / rel), 0, 1)
    lfo = 1 + 0.06 * np.sin(2 * np.pi * 0.13 * t)
    return (out * env * lfo * vel * 0.045 / max(1, len(freqs) / 3)).astype(np.float32)


def shaker(dur=0.08, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = RNG.standard_normal(n).astype(np.float32)
    x = sosfilt(butter(2, [5000, 11000], btype="bandpass", fs=SR, output="sos"), nz)
    return (x * np.minimum(1, t / 0.008) * np.exp(-45 * t) * vel * 0.25).astype(np.float32)


# ------------------------------------------------------------------ harmony
CH = {
    "C": [48, 55, 60, 64, 67], "Cmaj9": [48, 55, 59, 62, 64], "Am7": [45, 52, 55, 60, 64],
    "Fmaj7": [41, 53, 57, 60, 64], "G6": [43, 50, 55, 59, 64], "Gsus": [43, 50, 55, 60, 62],
    "Em7": [40, 52, 55, 59, 62], "Dm7": [38, 50, 53, 57, 60], "G7sus": [43, 50, 55, 60, 65],
    "Cmaj7": [48, 55, 59, 64, 67], "Am": [45, 52, 57, 60, 64], "F": [41, 53, 57, 60, 65],
    "G": [43, 50, 55, 59, 62], "Dm": [38, 50, 53, 57, 62], "Bb": [46, 53, 58, 62, 65],
}

# 题材情绪：chapter -> mood parameters
MOOD = {
    # 冷启动：好奇、悬着（sus 和弦，不落地）
    "s01": dict(bpm=92, prog=["Cmaj9", "Am7", "Fmaj7", "Gsus"], l2="arp", l3="motif"),
    # 反过来：同一个动机移到 F，像照镜子
    "s02": dict(bpm=92, prog=["Fmaj7", "G6", "Em7", "Am7"], l2="arp", l3="motif"),
    "title": dict(bpm=92, prog=["Cmaj9"], l2="none", l3="sting"),
    # 历史 + 饭桌：温和讲故事
    "s03": dict(bpm=78, prog=["Fmaj7", "Cmaj7", "Dm7", "G6"], l2="piano", l3="motif"),
    # 概念展开：稳定脉冲，往前推
    "s04": dict(bpm=96, prog=["Dm7", "G7sus", "Cmaj7", "Am7"], l2="pulse", l3="motif"),
    # 小词典：轻快、俏皮
    "s05": dict(bpm=104, prog=["Cmaj9", "Am7", "Dm7", "G6"], l2="arp_shaker", l3="motif"),
    # 反转：转到小调色彩，再回到轻快
    "s06": dict(bpm=96, prog=["Am", "F", "C", "G"], l2="syncop", l3="motif"),
    # 中文那一边：亲切、安静
    "s07": dict(bpm=80, prog=["Fmaj7", "Em7", "Dm7", "Cmaj7"], l2="piano", l3="motif"),
    # 1945：低沉长音，无节奏
    "s08": dict(bpm=60, prog=None, l2="none", l3="none", drone=True),
    # 为什么是美国：有方向感的推进
    "s10": dict(bpm=96, prog=["Am7", "Fmaj7", "C", "G"], l2="pulse", l3="motif"),
    # 收尾：温暖落地
    "s11": dict(bpm=84, prog=["Fmaj7", "G6", "Em7", "Am7"], l2="arp", l3="motif", end=True),
}


class Stems:
    def __init__(self, n):
        self.n = n
        self.L = {k: np.zeros(n, np.float32) for k in ("l1", "l2", "l3")}
        self.R = {k: np.zeros(n, np.float32) for k in ("l1", "l2", "l3")}

    def add(self, layer, sig, t0, pan=0.0, gain=1.0):
        i = int(t0 * SR)
        if i >= self.n or i < 0:
            return
        j = min(self.n, i + len(sig))
        gl = math.cos((pan + 1) * math.pi / 4) * gain
        gr = math.sin((pan + 1) * math.pi / 4) * gain
        self.L[layer][i:j] += sig[: j - i] * gl
        self.R[layer][i:j] += sig[: j - i] * gr


def render_segment(st, seg_id, t0, t1):
    md = MOOD.get(seg_id, MOOD["s04"])
    beat = 60 / md["bpm"]
    bar = beat * 4
    if md.get("drone"):
        dur = t1 - t0 + 2.5
        st.add("l1", pad([mhz(38), mhz(45), mhz(50)], dur, att=3.0, rel=2.5, cutoff=520), t0 - 0.3, 0, 1.3)
        st.add("l1", pad([mhz(57), mhz(62)], dur, att=6, rel=3, cutoff=900, vel=0.4), t0 + 2.5, 0.25)
        # sparse low piano tolls (counted as L2 so the schedule can thin them)
        tt = t0 + 3.0
        notes = [50, 45, 53, 45, 50, 41]
        k = 0
        while tt < t1 - 2:
            st.add("l2", epiano(mhz(notes[k % len(notes)]), 4.0, 0.55), tt, -0.2 + 0.4 * (k % 2))
            tt += 5.2
            k += 1
        return
    if md["l3"] == "sting":
        for k, m in enumerate(CH["Cmaj9"]):
            st.add("l3", epiano(mhz(m + 12), 3.5, 0.8), t0 + 0.05 + k * 0.06, -0.4 + 0.2 * k)
        st.add("l3", bell(mhz(84), 3.0, 0.9), t0 + 0.4, 0.3)
        st.add("l1", bass(mhz(36), 3.0, 1.0), t0 + 0.05)
        st.add("l1", pad([mhz(m) for m in CH["Cmaj9"][1:]], t1 - t0 + 1.5, att=0.3, rel=1.2), t0)
        return
    prog = md["prog"]
    bt, k = t0, 0
    while bt < t1 - 0.25:
        ch = CH[prog[k % len(prog)]]
        bl = min(bar, t1 - bt + 1.0)
        # L1 bed
        st.add("l1", pad([mhz(m) for m in ch[1:4]], bl + 0.6, att=0.5, rel=0.6), bt, 0.0)
        root = ch[0] if ch[0] <= 45 else ch[0] - 12
        st.add("l1", bass(mhz(root), beat * 2.2, 0.9), bt)
        st.add("l1", bass(mhz(root), beat * 1.8, 0.55), bt + beat * 2.5)
        # L2 motion
        sty = md["l2"]
        if sty in ("arp", "arp_shaker"):
            pat = [1, 2, 3, 4, 3, 2, 4, 3]
            for e in range(8):
                st.add("l2", pluck(mhz(ch[pat[e]] + 12), 1.3, 0.7 if e % 2 == 0 else 0.48), bt + e * beat / 2,
                       -0.35 + 0.1 * e)
            if sty == "arp_shaker":
                for e in range(8):
                    st.add("l2", shaker(0.08, 0.9 if e % 2 else 0.55), bt + e * beat / 2 + 0.01, 0.4)
        elif sty == "piano":
            for e, idx in enumerate([1, 3, 2, 4]):
                st.add("l2", epiano(mhz(ch[idx] + 12), 2.0, 0.55), bt + e * beat, -0.25 + 0.17 * e)
        elif sty == "pulse":
            for e in range(8):
                m = ch[2] + 12 if e % 4 != 3 else ch[3] + 12
                st.add("l2", pluck(mhz(m), 0.5, 0.45 if e % 2 else 0.6, 0.5), bt + e * beat / 2, 0.15)
        elif sty == "syncop":
            for e in (0, 1.5, 3, 4.5, 6):
                st.add("l2", pluck(mhz(ch[2 + int(e) % 3] + 12), 1.0, 0.6), bt + e * beat / 2, -0.2 + 0.05 * e)
        # L3 top line: a short motif on chord tones, every other bar
        if md["l3"] == "motif" and k % 2 == 0:
            top = [ch[3] + 12, ch[4] + 12, ch[2] + 24, ch[4] + 12]
            for e, m in enumerate(top):
                st.add("l3", epiano(mhz(m), 1.8, 0.55), bt + e * beat, 0.25)
            st.add("l3", bell(mhz(ch[4] + 24), 2.0, 0.5), bt + beat * 3.5, -0.3)
        bt += bar
        k += 1
    if md.get("end"):
        tend = t1 - 0.2
        for kk, m in enumerate(CH["Cmaj9"]):
            st.add("l3", epiano(mhz(m + 12), 5.0, 0.7), tend + kk * 0.07, -0.4 + 0.2 * kk)
        st.add("l1", bass(mhz(36), 5.0, 1.0), tend)
        st.add("l3", bell(mhz(88), 4.0, 0.7), tend + 0.5, 0.3)


# ------------------------------------------------------------------ 三层起伏：intensity schedule
def schedule(tl):
    """Keyframes (t, g1, g2, g3) driven by story beats."""
    kf = []

    def k(t, a, b, c):
        kf.append((t, a, b, c))

    for seg in tl["segs"]:
        sid, t0, tr = seg["id"], seg["t0"], seg["trig"]
        scenes = {name: ts for ts, name in seg["scenes"]}
        cards = [c for c in tl["cards"] if c["seg"] == sid and c.get("t_real")]
        tk = [l for l in tl["takeaways"] if l["seg"] == sid]
        if sid == "s01":
            k(t0, 1, 0.0, 0)
            if "calendar" in tr:
                k(tr["calendar"], 1, 1, 0)          # 时间流逝：节奏进来
            for c in cards:
                k(c["t_real"], 1, 0.5, 0.8)          # 真相浮出：顶层点一下
                k(c["t_real"] + 4, 1, 0.4, 0)
        elif sid == "s02":
            k(t0, 1, 0.4, 0)
            if "schedule" in tr:
                k(tr["schedule"], 1, 1, 0)
            k(seg["t1"] - 6, 1, 0.3, 0)
        elif sid == "title":
            k(t0, 1, 0, 1)
        elif sid == "s03":
            k(t0, 1, 0, 0)
            if "book1976" in tr:
                k(tr["book1976"], 1, 0.5, 0)
            if "soup" in scenes:
                k(scenes["soup"], 1, 0.8, 0)
            if "defs" in tr:
                k(tr["defs"], 1, 0.6, 0.5)
        elif sid == "s04":
            k(t0, 1, 0.4, 0)
            if "ruler" in tr:
                k(tr["ruler"], 1, 0.8, 0)
            if "room" in scenes:
                k(scenes["room"], 1, 1, 0)
            if "shared_cloud" in tr:
                k(tr["shared_cloud"], 1, 0.5, 0)
            if "caveat" in scenes:
                k(scenes["caveat"], 1, 0, 0)        # 提醒：收起来
        elif sid == "s05":
            k(t0, 1, 1, 0)
        elif sid == "s06":
            k(t0, 1, 0, 0)                          # 反转：先停一下
            if "ruler2" in tr:
                k(tr["ruler2"], 1, 0.6, 0)
            if "sandwich" in scenes:
                k(scenes["sandwich"], 1, 1, 0)
            if "sandwich_story" in scenes:
                k(scenes["sandwich_story"], 1, 0.4, 0)
            if "teacup" in scenes:
                k(scenes["teacup"], 1, 1, 0)
        elif sid == "s07":
            k(t0, 1, 0.4, 0)
            if "old_friends" in scenes:
                k(scenes["old_friends"], 1, 0.6, 0.3)
        elif sid == "s08":
            k(t0, 1, 0.8, 0)
        elif sid == "s10":
            k(t0, 1, 0.6, 0)
            if "contract" in scenes:
                k(scenes["contract"], 1, 0.8, 0)
            if "rules" in scenes:
                k(scenes["rules"], 1, 1, 0)
            if "not_written" in tr:
                k(tr["not_written"], 1, 1, 0.8)
        elif sid == "s11":
            k(t0, 1, 0.5, 0)
            if "l2" in tr:
                k(tr["l2"], 1, 1, 0)
            if "l3" in tr:
                k(tr["l3"], 1, 1, 1)
        for l in tk:                                # 每章“这说明什么”：三层全开
            k(l["t0"] - 0.3, 1, 1, 1 if sid != "s08" else 0)
    kf.sort()
    return kf


def gain_curves(kf, n, fade=1.2):
    """Piecewise-constant targets, smoothed with a one-pole filter (~fade seconds)."""
    blk = 480  # 10 ms
    m = n // blk + 1
    tgt = np.zeros((m, 3), np.float32)
    cur = np.array([1.0, 0.0, 0.0], np.float32)
    j = 0
    for i in range(m):
        t = i * blk / SR
        while j < len(kf) and kf[j][0] <= t:
            cur = np.array(kf[j][1:], np.float32)
            j += 1
        tgt[i] = cur
    out = np.zeros_like(tgt)
    a = 1 - math.exp(-1 / (fade / 0.01 / 3))
    g = tgt[0].copy()
    for i in range(m):
        g += (tgt[i] - g) * a
        out[i] = g
    return [np.repeat(out[:, c], blk)[:n] for c in range(3)]


def render(tl, total):
    n = int(total * SR) + SR * 6
    st = Stems(n)
    for seg in tl["segs"]:
        t1 = seg["t1"]
        if seg["id"] == "s11" and "endcard" in seg["trig"]:
            t1 = seg["trig"]["endcard"] + 0.3   # final chord lands on the end card
        render_segment(st, seg["id"], seg["t0"] + (0.15 if seg.get("chapter_t") is None else 0.9), t1)
    g1, g2, g3 = gain_curves(schedule(tl), n)
    # layer balance
    lv = {"l1": 0.9, "l2": 0.85, "l3": 0.8}
    L = st.L["l1"] * g1 * lv["l1"] + st.L["l2"] * g2 * lv["l2"] + st.L["l3"] * g3 * lv["l3"]
    R = st.R["l1"] * g1 * lv["l1"] + st.R["l2"] * g2 * lv["l2"] + st.R["l3"] * g3 * lv["l3"]
    sos = butter(2, [45, 11000], btype="bandpass", fs=SR, output="sos")
    L = sosfiltfilt(sos, L).astype(np.float32)
    R = sosfiltfilt(sos, R).astype(np.float32)
    # end fade
    nf = int(2.5 * SR)
    e = int(total * SR)
    if e < n:
        fade = np.linspace(1, 0, min(nf, e))
        L[e - len(fade):e] *= fade
        R[e - len(fade):e] *= fade
        L[e:] = 0
        R[e:] = 0
    return L[: int(total * SR)], R[: int(total * SR)]
