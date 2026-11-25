# -*- coding: utf-8 -*-
"""旁白轨、音效轨（程序合成）与混音。
python audio_build.py stems   → narration.wav / sfx.wav
python audio_build.py mix     → mix_music.wav（-15 LUFS）与 mix_nomusic.wav
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
A = "/tmp/claude-0/work/audio"
LINES = "/tmp/claude-0/work/tts/lines"
rng = np.random.default_rng(3)


def lp(x, fc, o=2):
    return sosfilt(butter(o, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, o=2):
    return sosfilt(butter(o, fc, "high", fs=SR, output="sos"), x)


# ── 音效 ──────────────────────────────────────────────────
def war_drum(big=True):
    n = int(2.2 * SR); t = np.arange(n) / SR
    f = 48 * (1 + 2.0 * np.exp(-t * 14))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    skin = lp(rng.normal(0, 1, n), 1200) * np.exp(-t * 25) * 0.7
    sub = np.sin(2 * np.pi * 34 * t) * np.exp(-t * 2.0) * 0.8
    return (body + skin + sub) * (1.0 if big else 0.6)


def gate_bar():
    """城门铁闩落下：低沉木门撞击＋金属铿锵（非谐泛音）"""
    n = int(2.5 * SR); t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * 70 * t * (1 + 0.5 * np.exp(-t * 20))) * np.exp(-t * 6)
    thud += lp(rng.normal(0, 1, n), 500) * np.exp(-t * 18) * 0.8
    metal = np.zeros(n)
    for f, d, a in ((312, 3.5, 0.5), (743, 4.5, 0.35), (1189, 6, 0.3), (1867, 8, 0.2), (2633, 10, 0.12), (3511, 12, 0.08)):
        metal += np.sin(2 * np.pi * f * t + rng.random() * 6) * np.exp(-t * d) * a
    clank = hp(rng.normal(0, 1, n), 2000) * np.exp(-t * 60) * 0.5
    chain = np.zeros(n)
    for k in range(5):  # 铁链余响
        i = int((0.08 + k * 0.05 + rng.random() * 0.02) * SR)
        m = int(0.05 * SR)
        chain[i:i + m] += hp(rng.normal(0, 1, m), 3000) * np.exp(-np.arange(m) / SR * 80) * 0.25
    return thud * 0.9 + metal * 0.55 + clank + chain


def stamp():
    n = int(0.8 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 90 * t) * np.exp(-t * 14) + lp(rng.normal(0, 1, n), 900) * np.exp(-t * 40) * 0.6) * 0.8


def whoosh(dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    y = np.zeros(n); blk = 2400
    for i in range(0, n, blk):
        fc = 300 + 2500 * env[i]
        y[i:i + blk] = lp(x[i:i + blk], fc)
    return y * env * 0.5


def crowd(dur=6.0):
    n = int(dur * SR)
    x = lp(hp(rng.normal(0, 1, n), 200), 900)
    am = lp(rng.normal(0, 1, n), 3) * 6 + 1
    e = np.minimum(1, np.minimum(np.arange(n) / SR / 1.0, (n - np.arange(n)) / SR / 1.0))
    return x * am * e * 0.12


def fire_crackle(dur=8.0):
    n = int(dur * SR)
    y = lp(rng.normal(0, 1, n), 600) * 0.12
    for k in range(int(dur * 25)):
        i = rng.integers(0, n - 2000)
        m = rng.integers(200, 1500)
        y[i:i + m] += hp(rng.normal(0, 1, m), 1500) * np.exp(-np.arange(m) / m * 6) * rng.uniform(0.1, 0.5)
    e = np.minimum(1, np.minimum(np.arange(n) / SR / 0.8, (n - np.arange(n)) / SR / 1.5))
    return y * e * 0.5


def reverb(x, sec=2.2, dec=3.0, wet=0.3):
    n = int(sec * SR); t = np.arange(n) / SR
    ir = lp(rng.normal(0, 1, n), 4000) * np.exp(-t * dec); ir[:int(0.01 * SR)] = 0
    ir /= np.abs(ir).sum() / 4
    return x + wet * fftconvolve(x, ir)[:len(x)]


def place(buf, x, t0, g=1.0):
    i = int(t0 * SR)
    if i < 0 or i >= len(buf):
        return
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x * g


def stems():
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    T = tl["end"]
    n = int((T + 0.5) * SR)
    nar = np.zeros(n)
    for ln in tl["lines"]:
        p = f"{LINES}/{ln['id']}.wav"
        if os.path.exists(p):
            x, sr = sf.read(p)
            assert sr == SR
            place(nar, x, ln["t0"])
    sfx = np.zeros(n)
    L = {ln["id"]: ln for ln in tl["lines"]}
    # 开场：战鼓两响＋城门铁闩
    place(sfx, war_drum(True), 0.0, 0.9)
    place(sfx, gate_bar(), 0.22, 0.8)
    place(sfx, war_drum(False), 0.62, 0.6)
    place(sfx, fire_crackle(9.0), 0.4, 0.5)
    place(sfx, whoosh(1.4), 0.3, 0.6)
    # 章节卡：低鼓
    for c in tl["cards"]:
        place(sfx, war_drum(False), c["t0"] + 0.05, 0.45)
    # 印章与重点落字
    hits = [("title", 1.2), ("beaten", 2.2)]
    sc0 = {s["sc"]: s["t0"] for s in tl["scenes"]}
    for sc, dt in hits:
        if sc in sc0:
            place(sfx, stamp(), sc0[sc] + dt, 0.7)
    for lid, dt in (("b09", 0.0), ("c15", 2.4), ("c12d", 0.0), ("c06", 1.6), ("c23", 0.0)):
        if lid in L:
            place(sfx, stamp(), L[lid]["t0"] + dt, 0.6)
    # 战争场景：箭头呼啸＋火
    for sc, dts in (("invade1", (0.2,)), ("invade2", (0.2, 0.7)), ("tandong", (0.4,)), ("lubu", (0.5,)), ("lose", (0.3,))):
        if sc in sc0:
            for dt in dts:
                place(sfx, whoosh(1.6), sc0[sc] + dt, 0.45)
    for sc in ("invade1", "invade2"):
        if sc in sc0:
            place(sfx, fire_crackle(7.0), sc0[sc] + 0.6, 0.35)
    for sc in ("famine", "welcome"):
        if sc in sc0:
            place(sfx, crowd(6.0), sc0[sc] + 0.5, 0.5)
    sfx = reverb(sfx, wet=0.25)
    os.makedirs(A, exist_ok=True)
    sf.write(f"{A}/narration.wav", nar.astype(np.float32), SR)
    sf.write(f"{A}/sfx.wav", sfx.astype(np.float32), SR)
    print("stems ok", T)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float(r.split("I:")[-1].split("LUFS")[0]); tp = float(r.split("Peak:")[-1].split("dBFS")[0])
    return I, tp


def mix():
    nar, _ = sf.read(f"{A}/narration.wav")
    sfx, _ = sf.read(f"{A}/sfx.wav")
    mus, _ = sf.read(f"{A}/music.wav")
    n = len(nar)
    if mus.ndim == 1:
        mus = np.stack([mus, mus], 1)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    # 人声包络 → 音乐闪避（侧链）
    win = int(0.05 * SR)
    env = np.sqrt(np.convolve(nar ** 2, np.ones(win) / win, "same"))
    talk = (env > 10 ** (-40 / 20)).astype(float)
    # 平滑：attack 0.08 s，release 0.6 s
    g = np.zeros(n); cur = 0.0
    a_up, a_dn = 1 - np.exp(-1 / (0.08 * SR)), 1 - np.exp(-1 / (0.6 * SR))
    tk = talk[::48]  # 1 ms 分辨率
    gs = np.zeros(len(tk))
    for i, v in enumerate(tk):
        cur += (v - cur) * (1 - np.exp(-1 / (0.08 * 1000)) if v > cur else 1 - np.exp(-1 / (0.6 * 1000)))
        gs[i] = cur
    g = np.repeat(gs, 48)[:n]
    g = np.pad(g, (0, n - len(g)))
    # 目标：讲话时音乐比人声低约 21 dB（人声 -18 dBFS RMS → 音乐约 -39 dBFS RMS）；停顿处抬 6 dB
    def rms_db(x):
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    mus_m = mus.mean(1)
    # 分段电平：3 秒窗 RMS → 拉向统一目标（讲话时比人声 -18 dBFS 低 TALK_DB），推子平滑 2 秒
    TALK_DB = float(os.environ.get("TALK_DB", 21.0))
    w3 = int(3 * SR)
    pw = np.convolve(mus_m[::480] ** 2, np.ones(300) / 300, "same")       # 10 ms 分辨率、3 秒窗
    lvl = 10 * np.log10(pw + 1e-10)
    target = -18 - TALK_DB
    gdb = np.clip(target - lvl, -30, 30)
    gdb = np.convolve(gdb, np.ones(200) / 200, "same")                      # 2 秒平滑
    k_talk = 10 ** (np.repeat(gdb, 480)[:n] / 20)
    k_talk = np.pad(k_talk, (0, n - len(k_talk)), mode="edge")
    k_gap = k_talk * 10 ** (6 / 20)
    mg = k_gap + (k_talk - k_gap) * g
    nar2 = np.stack([nar, nar], 1)
    sfx2 = np.stack([sfx, sfx], 1) * (1 - 0.5 * g)[:, None]
    full = nar2 + sfx2 + mus * mg[:, None]
    dry = nar2 + sfx2
    for nm, x in (("mix_music", full), ("mix_nomusic", dry)):
        p = f"{A}/{nm}_pre.wav"
        sf.write(p, x.astype(np.float32), SR)
        # 两遍 loudnorm 到 -15 LUFS / -1.5 dBTP
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "loudnorm=I=-15:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        js = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
        af = (f"loudnorm=I=-15:TP=-2.0:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
              f"aresample=48000")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, "-af", af, "-ar", "48000", f"{A}/{nm}.wav"], check=True)
        print(nm, lufs(f"{A}/{nm}.wav"))
    # 实测：讲话时 人声 vs 音乐
    m_eff = mus.mean(1) * mg
    seg = g > 0.9
    print("talk: voice rms %.1f dB, music rms %.1f dB" % (rms_db(nar[seg]), rms_db(m_eff[seg])))


if __name__ == "__main__":
    {"stems": stems, "mix": mix}[sys.argv[1]]()
