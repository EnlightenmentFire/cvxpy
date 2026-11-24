# -*- coding: utf-8 -*-
"""音乐与音效全部程序合成（无外部素材）+ 混音。
build_mix(tl, t0, t1) → 48 kHz 立体声 float32。
"""
import math
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt, resample_poly

import scenes as SC

SR = 48000
VOICE_RMS_DB = -18.0


def _bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="bandpass", fs=SR, output="sos"), x)


def _lp(x, fc, order=2):
    return sosfilt(butter(order, fc, btype="lowpass", fs=SR, output="sos"), x)


def _hp(x, fc, order=2):
    return sosfilt(butter(order, fc, btype="highpass", fs=SR, output="sos"), x)


def db(x):
    return 10 ** (x / 20)


# ───────────── 底噪音乐：低沉合成器长音 ─────────────
def drone(n, seed=0, root=55.0, warm=False, tension=0.0, t_offset=0.0):
    t = (np.arange(n) / SR + t_offset).astype(np.float64)
    out = np.zeros((n, 2))
    # 基音与五度：极慢的起伏
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.031 * t + seed)
    base = 0.55 * np.sin(2 * np.pi * root * t) + 0.18 * np.sin(2 * np.pi * root * 2 * t + 0.3)
    fifth = 0.16 * np.sin(2 * np.pi * root * 1.5 * t + 1.1) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.017 * t))
    mono = (base + fifth) * lfo
    # 去谐锯齿 pad，经低通
    pad = np.zeros(n)
    for k, (f, det) in enumerate([(root * 2, 0.0), (root * 2, 0.6), (root * 3, -0.4), (root * 4, 0.3)]):
        ff = f * (1 + det / 1200.0 * 8)
        ph = (ff * t + 0.13 * k) % 1.0
        pad += (2 * ph - 1) * (0.22 if k < 2 else 0.12)
    cutoff = 520 if not warm else 380
    pad = _lp(pad, cutoff, 2) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * t + 0.7 + seed))
    mono = mono + 0.9 * pad
    if tension > 0:   # 极低的“心跳”脉冲
        beat = np.zeros(n)
        period = 1.15
        for st in np.arange(-t_offset % period, n / SR, period):
            i = int(st * SR)
            L = int(0.32 * SR)
            if i >= n:
                break
            tt = np.arange(min(L, n - i)) / SR
            beat[i:i + len(tt)] += np.sin(2 * np.pi * 46 * tt) * np.exp(-tt / 0.09)
        mono = mono + tension * 0.9 * beat
    hiss = np.random.default_rng(seed + 7).normal(0, 1, n)
    air = _lp(_hp(hiss, 200), 1200) * 0.02
    if warm:   # 1978：磁带抖动 + 底噪
        wow = 1 + 0.004 * np.sin(2 * np.pi * 0.55 * t)
        mono = np.interp(np.cumsum(wow) - wow[0], np.arange(n), mono)
        air = air + _hp(hiss, 2500) * 0.012
    out[:, 0] = mono + air
    out[:, 1] = np.roll(mono, int(0.009 * SR)) + np.roll(air, 37)
    return out * 0.16


# ───────────── 环境声 ─────────────
def rain(n, seed=1, amount=1.0):
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    for ch in range(2):
        x = rng.normal(0, 1, n)
        bed = _bp(x, 900, 6500) * 0.05
        gust = 0.7 + 0.3 * np.sin(2 * np.pi * (0.07 + 0.02 * ch) * np.arange(n) / SR + ch)
        out[:, ch] = bed * gust
    # 雨滴
    k = int(n / SR * 26 * amount)
    pos = rng.integers(0, max(1, n - 400), k)
    for p in pos:
        L = int(rng.uniform(0.002, 0.006) * SR)
        burst = rng.normal(0, 1, L) * np.exp(-np.arange(L) / (L / 4))
        pan = rng.uniform(0.2, 0.8)
        g = rng.uniform(0.02, 0.07)
        out[p:p + L, 0] += burst * g * (1 - pan)
        out[p:p + L, 1] += burst * g * pan
    return out * amount


def engine(n, seed=2, amount=1.0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    brown = np.cumsum(rng.normal(0, 1, n))
    brown = _hp(brown, 20)
    brown = brown / (np.max(np.abs(brown)) + 1e-9)
    rumble = _lp(brown, 320) * 0.5
    hum = 0.05 * np.sin(2 * np.pi * (88 + 0.6 * np.sin(2 * np.pi * 0.1 * t)) * t)
    whine = 0.006 * np.sin(2 * np.pi * 2350 * t)
    m = (rumble + hum + whine) * amount * 0.5
    return np.stack([m, np.roll(m, 211)], 1)


def wipers(n, t_on=0.0, period=1.45, seed=3, amount=1.0):
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    st = max(0.0, t_on)
    k = 0
    while st < n / SR:
        i = int(st * SR)
        L = int(0.85 * SR)
        L = min(L, n - i)
        if L <= 0:
            break
        tt = np.arange(L) / SR
        env = np.sin(np.pi * np.clip(tt / 0.85, 0, 1)) ** 2
        sw = _bp(rng.normal(0, 1, L), 350, 2600) * env * 0.11
        pan = 0.35 if k % 2 == 0 else 0.65
        out[i:i + L, 0] += sw * (1 - pan) * 2
        out[i:i + L, 1] += sw * pan * 2
        j = i + L - 1
        Lt = min(int(0.07 * SR), n - j)
        if Lt > 0:
            tt2 = np.arange(Lt) / SR
            th = np.sin(2 * np.pi * 95 * tt2) * np.exp(-tt2 / 0.018) * 0.12
            out[j:j + Lt, 0] += th
            out[j:j + Lt, 1] += th
        st += period
        k += 1
    return out * amount


def chime():
    L = int(1.1 * SR)
    t = np.arange(L) / SR
    x = 0.5 * np.sin(2 * np.pi * 523.25 * t) + 0.35 * np.sin(2 * np.pi * 659.25 * t)
    x = x * np.exp(-t / 0.35)
    return np.stack([x, x], 1) * 0.12


def tone(freq, dur=1.6, amp=0.12):
    L = int(dur * SR)
    t = np.arange(L) / SR
    x = (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t) + 0.08 * np.sin(2 * np.pi * freq * 3 * t))
    x = x * (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.55)
    return np.stack([x, x], 1) * amp


def thud():
    L = int(1.0 * SR)
    t = np.arange(L) / SR
    f = 64 * np.exp(-t / 0.35) + 26
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.28)
    nz = _lp(np.random.default_rng(9).normal(0, 1, L), 180) * np.exp(-t / 0.12) * 0.8
    y = (x + nz)
    y = y / np.max(np.abs(y)) * 0.85
    return np.stack([y, y], 1)


def whoosh(dur=1.2):
    L = int(dur * SR)
    t = np.arange(L) / SR
    nz = _bp(np.random.default_rng(11).normal(0, 1, L), 120, 900)
    env = np.sin(np.pi * t / dur) ** 2
    x = nz * env * 0.05 + 0.08 * np.sin(2 * np.pi * 55 * t) * env
    return np.stack([x, x], 1)


# ───────────── 混音 ─────────────
def _place(buf, x, at):
    i = int(round(at * SR))
    if i >= len(buf) or i + len(x) <= 0:
        return
    a, b = max(0, i), min(len(buf), i + len(x))
    buf[a:b] += x[a - i:b - i]


def load_voice(path):
    w, sr = sf.read(path, dtype="float32")
    if sr != SR:
        w = resample_poly(w, SR, sr).astype(np.float32)
    return w


SCENE_BED = {   # 场景 → (音乐量 dB, 雨, 发动机, 紧张度, 暖色)
    "cold": (None, 0.9, 0.9, 0, False), "title": (-2, 0.4, 0.3, 0, False), "chapter": (-4, 0, 0, 0, False),
    "night": (-3, 0.2, 0.6, 0, False), "cockpit": (-4, 0.7, 0.5, 0, False), "map": (-4, 0.25, 0, 0, False),
    "timeline": (-4, 0.5, 0.4, 0.2, False), "profile": (-5, 0.8, 0.6, 0.55, False), "impact": (None, 0, 0, 0, False),
    "memorial": (-10, 0, 0, 0, False), "report": (-5, 0, 0, 0, False), "cheese": (-5, 0, 0, 0, False),
    "ua173": (-5, 0, 0.35, 0.1, True), "stat": (-5, 0, 0, 0, False), "nasa": (-5, 0, 0, 0, False),
    "sim": (-5, 0, 0, 0, False), "ladder": (-5, 0, 0, 0.15, False), "rules": (-5, 0, 0, 0, False),
    "pdi": (-5, 0, 0, 0, False), "debate": (-5, 0, 0, 0, False), "after": (-4, 0, 0, 0, False),
    "end": (-7, 0, 0, 0, False), "credits": (-5, 0, 0, 0, False),
}
LADDER_NOTES = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]


def build_mix(tl, t0, t1, manifest, gpws_manifest, voice_only=False):
    n = int((t1 - t0) * SR)
    voice = np.zeros(n, np.float32)
    fx = np.zeros((n, 2))
    gp = np.zeros((n, 2))
    # 人声与近地警告
    for e in tl:
        if e["start"] + e["dur"] < t0 or e["start"] > t1:
            continue
        if e["say"] and e["id"] in manifest:
            _place(voice, load_voice(manifest[e["id"]]["file"]), e["start"] + e.get("lead", 0) - t0)
        if e["gpws"] and e["gpws"] in gpws_manifest:
            g = load_voice(gpws_manifest[e["gpws"]]["file"])
            _place(gp, np.stack([g, g], 1) * 0.42, e["start"] - t0)
    # 人声电平：活动语音 RMS → -18 dBFS
    act = np.abs(voice) > 0.01
    if act.any():
        rms = np.sqrt(np.mean(voice[act] ** 2))
        voice *= db(VOICE_RMS_DB) / (rms + 1e-9)
    voice = _hp(voice, 50).astype(np.float32)
    if voice_only:
        out = np.stack([voice, voice], 1)
        return out / max(1.0, np.max(np.abs(out)) / 0.95)
    # 场景底噪（按场景段落生成并淡入淡出拼接）
    bed = np.zeros((n, 2))
    runs = []
    for e in tl:
        if e["start"] + e["dur"] <= t0 or e["start"] >= t1:
            continue
        if runs and runs[-1][0] == e["scene"]:
            runs[-1][2] = e["start"] + e["dur"]
        else:
            runs.append([e["scene"], e["start"], e["start"] + e["dur"]])
    for k, (sc, a, b) in enumerate(runs):
        a0, b0 = max(a, t0) - t0, min(b, t1) - t0
        L = int((b0 - a0 + 0.8) * SR)
        mus, rn, en, ten, warm = SCENE_BED.get(sc, (-5, 0, 0, 0, False))
        seg = np.zeros((L, 2))
        if mus is not None:
            seg += drone(L, seed=k, warm=warm, tension=ten, t_offset=a) * db(mus)
        if rn:
            seg += rain(L, seed=10 + k, amount=rn)
        if en:
            seg += engine(L, seed=20 + k, amount=en)
        if sc == "cold":
            seg += wipers(L, 0.2, amount=0.9)
        fade = int(0.4 * SR)
        env = np.ones(L)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        _place(bed, seg * env[:, None], a0 - 0.2)
    # 事件音效
    for i, e in enumerate(tl):
        if e["start"] + e["dur"] < t0 or e["start"] > t1:
            continue
        st = e["start"] - t0
        if e["scene"] == "chapter":
            _place(fx, whoosh(1.4), st)
        if e["scene"] == "impact":
            _place(fx, thud() * 0.9, st)
            # 撞击后彻底静音 2 秒：清空这段的底噪与人声
            a, b = int((st + 0.9) * SR), int((st + e["dur"]) * SR)
            fx[a:b] = 0
        if e["scene"] == "ladder":
            ev = e["ev"]
            if ev.get("cards", -1) < 0 and ev.get("build", 0) >= 1 and (i == 0 or tl[i - 1]["ev"].get("build") != ev.get("build")):
                _place(fx, tone(LADDER_NOTES[ev["build"] - 1], 1.8, 0.13), st + 0.05)
            if ev.get("cards", -1) >= 1 and (i == 0 or tl[i - 1]["ev"].get("cards") != ev.get("cards")):
                f = [0, 196.0, 246.94, 329.63, 440.0][ev["cards"]]
                _place(fx, tone(f, 1.8, 0.12), st + 0.05)
    # 剖面：01:40:06/01:40:57/01:41:45 高度提醒音；01:41:53 起雨刷
    prof = [e for e in tl if e["scene"] == "profile"]
    if prof:
        import compose
        idx = {id(e): k for k, e in enumerate(tl)}

        def clock_to_t(clk):
            for e in prof:
                j = idx[id(e)]
                c0 = compose.profile_clock(tl, j, e["start"])
                c1 = compose.profile_clock(tl, j, e["start"] + e["dur"] - 1e-3)
                if c0 <= clk <= c1 and c1 > c0:
                    return e["start"] + (clk - c0) / (c1 - c0) * e["dur"]
            return None
        for clk in ("01:40:06", "01:40:57", "01:41:45"):
            tt = clock_to_t(SC.hms(clk))
            if tt is not None:
                _place(fx, chime(), tt - t0)
        tw = clock_to_t(SC.hms("01:41:53"))
        tend = next((e["start"] for e in tl if e["scene"] == "impact"), None)
        if tw is not None and tend is not None:
            L = int((tend - tw) * SR)
            if L > 0:
                _place(fx, wipers(L, 0.0, amount=0.8), tw - t0)
    # 人声下压背景（sidechain duck）
    env = np.abs(voice)
    env = sosfiltfilt(butter(2, 6, fs=SR, output="sos"), env)
    duck = 1 - 0.62 * np.clip(env / 0.03, 0, 1)
    duck = sosfiltfilt(butter(1, 3, fs=SR, output="sos"), duck)
    bed = bed * duck[:, None]
    # 撞击段落：静音窗口作用于全部（含底噪）
    for e in tl:
        if e["scene"] == "impact" and t0 <= e["start"] <= t1:
            a = int((e["start"] - t0 + 0.9) * SR)
            b = int((e["start"] - t0 + e["dur"]) * SR)
            bed[a:b] = 0
            gp[a:b] = 0
    mix = bed + fx + gp + np.stack([voice, voice], 1)
    pk = np.max(np.abs(mix))
    if pk > 0.89:
        mix = np.tanh(mix / 0.89 * 0.9) * 0.89 / np.tanh(0.9)
    return mix.astype(np.float32)


def write_wav(path, x):
    sf.write(path, x, SR, subtype="PCM_16")
