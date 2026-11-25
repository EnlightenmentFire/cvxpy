# -*- coding: utf-8 -*-
"""按《配乐规范》编排配乐：三层起伏（铺底 / 推进 / 高潮）+ 结尾收束，段落间 3 秒等功率交叉淡化。
输入：时间线 tl、MusicGen 片段（music_manifest.json 中挑定的版本）。输出：48 kHz 立体声配乐轨。
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR = 48000
XF = 3.0          # 段落间交叉淡化（秒）

# 每层挑定的版本（由 music_select.py 写入 music_choice.json；缺省用 _0）
DEFAULT_CHOICE = {"L1_pad": ["L1_pad_0", "L1_pad_1"], "L2_push": ["L2_push_0", "L2_push_1"],
                  "L3_climax": ["L3_climax_0"], "L3_elegy": ["L3_elegy_0", "L3_elegy_1"],
                  "L4_think": ["L4_think_0", "L4_think_1"],
                  "L4_piano": ["L4_piano_0", "L4_piano_1"], "L5_end": ["L5_end_0"]}

# 配乐提示（cue）：(起始 beat, 结束 beat（含）, 层, 基准电平 dB, 选项)
CUES = [
    ("s0_08", "s2_14", "L1_pad", -4.0, dict(fade_in=2.0, keys=["L1_pad_0"])),  # 铺底：片头淡入，只用干净的长音版
    ("ch3", "s3_35", "L2_push", -3.0, dict(ramp_db=4.0, heartbeat=True)),      # 推进：逐步抬高 + 心跳低鼓
    ("s3_38", "s3_40", "L3_elegy", 0.0, dict(fade_in=0.25, xf_in=0.0, keys=["L3_elegy_1", "L3_elegy_0"], alone_boost_db=6.0)),  # 高潮
    ("ch4", "s4_11", "L4_piano", -4.0, {}),
    ("ch5", "s5_15", "L2_push", -5.0, dict(tape=True, variant=1)),             # 1978：老音色 + 磁带底噪
    ("ch6", "s6_08", "L4_think", -5.0, {}),
    ("ch7", "s7_22", "L4_piano", -5.0, dict(variant=1)),
    ("ch8", "s8_10", "L4_think", -5.0, dict(variant=1)),
    ("ch9", "s9_12", "L1_pad", -5.0, dict(keys=["L1_pad_0"], lowpass=1800)),
    ("ch10", "s10_06", "L4_piano", -4.0, {}),
    ("s11_01", "s12_01", "L5_end", -2.0, dict(fade_out=3.0, keys=["L5_end_1", "L5_end_0"])),  # 结尾：推起后收成余音
]


# 截掉片段里的瞬态/爆音（秒），由频谱人工检查确定
TRIM = {"L1_pad_0": (0.0, 19.0), "L2_push_0": (0.0, 20.5), "L2_push_1": (0.0, 22.0),
        "L3_elegy_1": (5.0, 24.0)}      # 高潮从弦乐已经推起来的地方切入


def _load(path, key=None):
    w, sr = sf.read(path, dtype="float32", always_2d=True)
    if key in TRIM:
        a, b = TRIM[key]
        w = w[int(a * sr):int(b * sr)]
    if w.shape[1] == 1:
        w = np.repeat(w, 2, 1)
    if sr != SR:
        w = resample_poly(w, SR, sr, axis=0).astype(np.float32)
    # 去掉开头的静音
    e = np.abs(w).mean(1)
    k = int(0.02 * SR)
    env = np.convolve(e, np.ones(k) / k, mode="same")
    thr = env.max() * 0.03
    i0 = int(np.argmax(env > thr))
    return w[max(0, i0 - int(0.05 * SR)):]


def _eqpow(n):
    t = np.linspace(0, 1, n, dtype=np.float32)
    return np.cos(t * np.pi / 2), np.sin(t * np.pi / 2)


def chain(clips, dur, offsets=(0.0, 0.0, 4.0, 7.0)):
    """用片段链出 dur 秒：轮换版本、每一轮换个起点，3 秒等功率交叉淡化，避免听出循环。"""
    n = int(dur * SR)
    xf = int(XF * SR)
    out = np.zeros((n, 2), np.float32)
    pos, k = 0, 0
    while True:
        c = clips[k % len(clips)]
        offs = offsets if len(clips) > 1 else (0.0, 6.0, 11.0, 3.0, 9.0)     # 单片段循环时每轮换起点
        off = int(offs[(k // len(clips)) % len(offs)] * SR)
        seg = c[min(off, len(c) // 3):].copy()
        if k > 0:
            fo, fi = _eqpow(xf)
            seg[:xf] *= fi[:, None]
            out[pos:pos + xf] *= fo[:min(xf, n - pos), None]
        end = min(n, pos + len(seg))
        out[pos:end] += seg[:end - pos]
        if end >= n:
            return out
        pos = end - xf
        k += 1


def heartbeat(dur, bpm0=58, bpm1=70, db0=-30, db1=-21):
    """稀疏的心跳式低鼓（lub-dub）：逐渐加快、逐渐变响。"""
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    t = 0.4
    while t < dur - 0.5:
        k = t / dur
        amp = 10 ** (lerp_(db0, db1, k) / 20)
        for off, a in ((0.0, 1.0), (0.27, 0.62)):
            i = int((t + off) * SR)
            L = min(int(0.35 * SR), n - i)
            if L <= 0:
                continue
            tt = np.arange(L) / SR
            f = 38 + 22 * np.exp(-tt / 0.03)
            ph = 2 * np.pi * np.cumsum(f) / SR
            out[i:i + L] += (np.sin(ph) * np.exp(-tt / 0.11) * amp * a).astype(np.float32)
        t += 60.0 / lerp_(bpm0, bpm1, k)
    return np.stack([out, out], 1)


def lerp_(a, b, k):
    return a + (b - a) * k


def tape(x, seed=5):
    """1978 段：带限、轻抖动、磁带底噪。"""
    t = np.arange(len(x)) / SR
    wow = 1 + 0.0035 * np.sin(2 * np.pi * 0.55 * t) + 0.0012 * np.sin(2 * np.pi * 6.3 * t)
    idx = np.clip(np.cumsum(wow) - wow[0], 0, len(x) - 1)
    y = np.stack([np.interp(idx, np.arange(len(x)), x[:, ch]) for ch in range(2)], 1)
    y = sosfilt(butter(2, [110, 5500], btype="bandpass", fs=SR, output="sos"), y, axis=0)
    y = np.tanh(y * 1.4) / 1.4
    hiss = np.random.default_rng(seed).normal(0, 1, y.shape)
    hiss = sosfilt(butter(2, 2500, btype="highpass", fs=SR, output="sos"), hiss, axis=0) * 0.004
    return (y + hiss).astype(np.float32)


def build_score(tl, t0, t1, work, choice=None):
    man = json.load(open(os.path.join(work, "music_manifest.json")))
    cp = os.path.join(work, "music_choice.json")
    choice = choice or (json.load(open(cp)) if os.path.exists(cp) else DEFAULT_CHOICE)
    cache = {}

    def clips_for(layer, variant, fixed=None):
        keys = list(fixed) if fixed else list(choice.get(layer, DEFAULT_CHOICE[layer]))
        keys = [k for k in keys if k in man] or [k for k in man if man[k]["layer"] == layer]
        if variant and len(keys) > 1:
            keys = keys[variant % len(keys):] + keys[:variant % len(keys)]
        out = []
        for k in keys:
            if k not in cache:
                cache[k] = _load(man[k]["file"], k)
            out.append(cache[k])
        return out

    by_id = {e["id"]: e for e in tl}
    n = int((t1 - t0) * SR)
    score = np.zeros((n, 2), np.float32)
    for (b0, b1, layer, base_db, opt) in CUES:
        if b0 not in by_id or b1 not in by_id:
            continue
        a = by_id[b0]["start"]
        b = by_id[b1]["start"] + by_id[b1]["dur"]
        if b <= t0 or a >= t1:
            continue
        xf_in = opt.get("xf_in", XF)
        seg_start = a - xf_in / 2
        seg_end = b if opt.get("fade_out") else b + XF / 2
        dur = seg_end - seg_start
        seg = chain(clips_for(layer, opt.get("variant", 0), opt.get("keys")), dur)
        if opt.get("tape"):
            seg = tape(seg)
        if opt.get("heartbeat"):
            seg = seg + heartbeat(len(seg) / SR)[:len(seg)]
        if opt.get("lowpass"):
            seg = sosfilt(butter(2, opt["lowpass"], btype="lowpass", fs=SR, output="sos"), seg, axis=0).astype(np.float32)
        g = np.full(len(seg), 10 ** (base_db / 20), np.float32)
        if opt.get("ramp_db"):
            g *= 10 ** (np.linspace(0, opt["ramp_db"], len(seg)) / 20).astype(np.float32)
        if opt.get("alone_boost_db"):
            # 高潮：旁白开口前音乐单独出来的那几秒抬高，开口时 0.6 秒内回落
            e0 = by_id[b0]
            t_alone = e0.get("lead", 0.0)
            i1 = int((a + t_alone - seg_start) * SR)
            r = int(0.6 * SR)
            env = np.zeros(len(seg), np.float32)
            env[:i1] = opt["alone_boost_db"]
            env[i1:i1 + r] = np.linspace(opt["alone_boost_db"], 0, len(env[i1:i1 + r]))
            g *= (10 ** (env / 20)).astype(np.float32)
        seg *= g[:, None]
        # 进出淡化（段落间等功率交叉；片头 / 高潮 / 结尾按选项）
        fin = int((opt.get("fade_in") or xf_in or 0.05) * SR)
        fout = int((opt.get("fade_out") or XF) * SR)
        if fin > 0:
            seg[:fin] *= (np.sin(np.linspace(0, np.pi / 2, fin)) if not opt.get("fade_in") else
                          np.linspace(0, 1, fin))[:, None].astype(np.float32)
        if fout > 0:
            seg[-fout:] *= np.cos(np.linspace(0, np.pi / 2, fout))[:, None].astype(np.float32)
        i = int(round((seg_start - t0) * SR))
        lo, hi = max(0, i), min(n, i + len(seg))
        if hi > lo:
            score[lo:hi] += seg[lo - i:hi - i]
    # 近地警告倒数时撤掉音乐；撞山后彻底静音（由混音阶段统一处理静音窗口）
    for e in tl:
        if e["id"] == "s3_36" and t0 <= e["start"] <= t1:
            i = int((e["start"] - t0) * SR)
            f = int(0.5 * SR)
            score[i:i + f] *= np.linspace(1, 0, min(f, n - i))[:, None]
            j = int((by_id["s3_38"]["start"] - t0) * SR) if "s3_38" in by_id else n
            score[i + f:j] = 0
    return score
