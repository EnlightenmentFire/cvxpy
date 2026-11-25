# -*- coding: utf-8 -*-
"""按《配乐规范》混音。

1. 旁白：50 Hz 高通，逐句统一响度，拼成整轨（voice.wav）。
2. 配乐：铺底 → 推进 → 高潮 → 回落 → 尾声，层与层之间 3 秒等功率交叉淡化；
   高潮最响的一段对准 s6g 之后的 1.6 秒旁白空白。
3. 逐句电平：讲话时每句的音乐都摆到比这句人声低 16.5 dB（冷开场 21 dB）；句内短停顿里音乐最多回升到
   比人声低 9 dB；高潮那 1.6 秒空白再抬 5 dB。
4. 规范里的 ffmpeg 链：音乐 3 kHz −4 dB、2 秒淡入、3 秒淡出、侧链压缩（实测调参：阈值 0.05，比 4，15/700 ms），
   amix 后 loudnorm I=−16 / TP=−2.0（给 AAC 编码留余量）/ LRA=11。

python mix2.py NARR_DIR LAYERS.json OUT_DIR
LAYERS.json: {"base": 路径, "push": 路径, "climax": 路径, "after": 路径, "coda": 路径}
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import Timeline  # noqa: E402
import script  # noqa: E402

SR = 48000
VOICE_RMS_DB = -18.0
LAYER_DB = {"base": -20.0, "push": -18.0, "climax": -14.0, "after": -20.0, "coda": -21.0}
XF = 3.0
# 逐句电平：讲话时这句人声的整体响度比音乐（压低后，K 加权 400 ms）高多少 dB
GAP_DB = 16.5          # 规范 15–18
GAP_DB_OPEN = 21.0     # 冷开场（S0）：规范"铺底…音乐很轻"
SWELL_DB = 5.0         # 高潮那 1.6 秒旁白空白里，在侧链自然回升之外再抬高的量
CEIL_GAP = 9.0         # 句内和句间短空隙里，音乐最多回升到"这句人声响度 − 9 dB"


def rms_db(x, thr_db=-50.0):
    if x.ndim == 2:
        x = x.mean(1)
    win = int(0.02 * SR)
    k = len(x) // win
    if k == 0:
        return -120.0
    r = np.sqrt((x[: k * win].reshape(k, win) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r + 1e-9)
    v = r[db > thr_db]
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-9) if len(v) else -120.0


def load(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2]


def build_voice(T, narr_dir):
    n = int(T.total * SR) + SR
    v = np.zeros(n, np.float32)
    for ent in T.lines:
        p = os.path.join(narr_dir, ent["id"] + ".wav")
        if not os.path.exists(p):
            continue
        w, sr = sf.read(p, dtype="float32")
        if sr != SR:
            w = resample_poly(w, SR, sr).astype(np.float32)
        w = w * 10 ** ((VOICE_RMS_DB - rms_db(w)) / 20)
        i = int(ent["start"] * SR)
        v[i:i + len(w)] += w[: max(0, n - i)]
    sos = butter(2, 50, btype="highpass", fs=SR, output="sos")
    return sosfilt(sos, v).astype(np.float32)


def peak_window(x, win_s=3.0):
    """最响的 win_s 秒窗口的中心（秒）"""
    m = x.mean(1)
    w = int(0.1 * SR)
    k = len(m) // w
    e = (m[: k * w].reshape(k, w) ** 2).mean(1)
    n = int(win_s / 0.1)
    s = np.convolve(e, np.ones(n), mode="valid")
    i = int(np.argmax(s))
    return (i + n / 2) * 0.1


def arrange(T, layers):
    total = T.total
    n = int(total * SR)
    bed = np.zeros((n, 2), np.float32)
    clips = {k: load(p) for k, p in layers.items()}
    for k in clips:
        clips[k] = clips[k] * 10 ** ((LAYER_DB[k] - rms_db(clips[k], thr_db=-60)) / 20)
    pause0 = T.end("s6g")                     # 旁白空白开始
    climax_peak = pause0 + 0.8                 # 空白中点
    cpk = peak_window(clips["climax"])
    t_climax = climax_peak - cpk               # 高潮片段起点
    c_end = min(T.start("s6h") + 4.0 + XF, t_climax + len(clips["climax"]) / SR - 0.3)   # 高潮不循环
    plan = [
        ("base", 0.0, T.sec_start["S4"] + XF),
        ("push", T.sec_start["S4"], t_climax + XF),
        ("climax", t_climax, c_end),
        ("after", c_end - XF, T.sec_start["S9"] + XF),
        ("coda", T.sec_start["S9"], total),
    ]
    for i, (k, a, b) in enumerate(plan):
        x = clips[k]
        need = int((b - a) * SR)
        if len(x) < need:  # 不够长：从片段中段接一次（等功率交叉）
            reps = [x]
            while sum(len(r) for r in reps) < need + int(XF * SR):
                reps.append(x[int(len(x) * 0.2):])
            y = reps[0]
            for r in reps[1:]:
                y = xfade_concat(y, r)
            x = y
        seg = x[:need].copy()
        L = len(seg)
        env = np.ones(L, np.float32)
        f = int(XF * SR)
        if i > 0:
            env[:f] = np.sin(np.linspace(0, math.pi / 2, f)) ** 1
        if i < len(plan) - 1:
            env[-f:] = np.cos(np.linspace(0, math.pi / 2, f)) ** 1
        seg *= env[:, None]
        s = int(a * SR)
        e = min(n, s + L)
        bed[s:e] += seg[: e - s]
    bed = ride(bed, plan)
    return bed, dict(t_climax=t_climax, pause=pause0, plan=[(k, round(a, 2), round(b, 2)) for k, a, b in plan])


def ride(bed, plan, win=3.0, up=8.0, down=10.0):
    """推子跟随：3 秒窗口的 RMS 拉向各层目标电平（最多 +8/−10 dB），平滑后施加。"""
    hop = int(0.1 * SR)
    m = bed.mean(1)
    k = len(m) // hop
    e = (m[: k * hop].reshape(k, hop) ** 2).mean(1)
    n = int(win / 0.1)
    ker = np.hanning(n); ker /= ker.sum()
    env = 10 * np.log10(np.convolve(e, ker, mode="same") + 1e-12)
    tgt = np.full(k, -20.0)
    tt = np.arange(k) * 0.1
    for (name, a, b) in plan:
        sel = (tt >= a) & (tt < b)
        tgt[sel] = LAYER_DB[name]
    tgt = np.convolve(tgt, np.ones(30) / 30, mode="same")          # 层间目标也平滑过渡
    g = np.clip(tgt - env, -down, up)
    g = np.convolve(g, ker, mode="same")
    gl = np.repeat(10 ** (g / 20), hop)
    gl = np.concatenate([gl, np.full(len(m) - len(gl), gl[-1])])
    return (bed * gl[:, None]).astype(np.float32)


def xfade_concat(a, b, xf=XF):
    f = int(xf * SR)
    ea = np.cos(np.linspace(0, math.pi / 2, f))[:, None]
    eb = np.sin(np.linspace(0, math.pi / 2, f))[:, None]
    mid = a[-f:] * ea + b[:f] * eb
    return np.concatenate([a[:-f], mid, b[f:]])


def ff(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def music_chain(dur):
    return (f"[1:a]acompressor=threshold=-12dB:ratio=2:attack=80:release=600,volume=0.5,"
            f"equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2,afade=t=out:st={dur - 3:.2f}:d=3[m]")


# 规范参考值是 threshold=0.02:ratio=10:release=500；在这条人声上会压下 25 dB 以上，
# 实测调到 0.05 / 4 / 700 ms，停顿时回升更平缓
DUCK = "[m][sc]sidechaincompress=threshold=0.05:ratio=4:attack=15:release=700[duck]"


def ducked(vpath, mpath, outpath, dur):
    ff("-i", vpath, "-i", mpath, "-filter_complex", "[0:a]anull[sc];" + music_chain(dur) + ";" + DUCK,
       "-map", "[duck]", "-ar", str(SR), outpath)


def line_frames(T, n_frames):
    """每句的测量帧（去掉句首句尾各 0.3 秒；第一句再避开 2 秒淡入）"""
    from loudness import frame_centers
    t = frame_centers(n_frames)
    out = []
    for e in T.lines:
        a = max(e["start"] + 0.3, 2.6)
        sel = (t > a) & (t < e["end"] - 0.3)
        if sel.sum() >= 3:
            out.append((e, sel))
    return t, out


def level_to_voice(T, voice, bed, tmpdir, iters=6):
    """逐句把音乐摆到"比这句人声低 GAP_DB"，并在句内设天花板：
    - 侧链对每一层压下去的量基本一样，所以压前更响的层（高潮）在人声底下也更响；
      这里按句测量真实结果（跑同一条 ffmpeg 链路），算出每句该补多少 dB。
    - 只看中位数会漏掉句内短停顿里音乐冒上来的情况（侧链一松，鼓点/铜管就顶上来），
      所以句内和句间短空隙（<0.8 秒）再加一道天花板：音乐不得高于"这句人声响度 − CEIL_GAP"。
    - 0.8 秒以上的空白（章节转场、片名卡、高潮那 1.6 秒、片尾）不设天花板，让音乐回升。
    几轮"测—改"收敛。"""
    from loudness import momentary_lufs, line_loudness, frame_centers
    n = len(bed)
    dur = n / SR
    vpath = os.path.join(tmpdir, "lv_voice.wav")
    sf.write(vpath, np.stack([voice, voice], 1), SR, subtype="FLOAT")
    mv = momentary_lufs(np.stack([voice, voice], 1))
    t, lines = line_frames(T, len(mv))
    line_l = {e["id"]: line_loudness(mv, sel) for e, sel in lines}
    # 天花板区域：每句 [起-0.05, 止+0.05]，以及与下一句之间 <0.8 秒的空隙
    ceil = np.full(len(mv), np.inf)
    ent = [e for e, _ in lines]
    for i, e in enumerate(ent):
        L = line_l[e["id"]] - CEIL_GAP
        sel = (t >= e["start"] - 0.05) & (t <= e["end"] + 0.05)
        ceil[sel] = np.minimum(ceil[sel], L)
        if i + 1 < len(ent) and ent[i + 1]["start"] - e["end"] < 0.8:
            nxt = ent[i + 1]
            sel = (t > e["end"]) & (t < nxt["start"])
            ceil[sel] = np.minimum(ceil[sel], min(L, line_l[nxt["id"]] - CEIL_GAP))
    corr = {e["id"]: 0.0 for e in ent}
    att = np.zeros(len(mv))                       # 天花板压下的量（dB，≤0），按测量帧中心计
    grid = np.arange(int(np.ceil(dur / 0.1)) + 1) * 0.1
    ker15 = np.hanning(15); ker15 /= ker15.sum()
    ker5 = np.hanning(5); ker5 /= ker5.sum()
    log = []
    for it in range(iters + 1):
        knots_t, knots_g = [], []
        for e in ent:
            knots_t += [e["start"], e["end"]]; knots_g += [corr[e["id"]]] * 2
        g = np.interp(grid, knots_t, knots_g)
        g = np.convolve(np.pad(g, 7, mode="edge"), ker15, mode="valid")[:len(grid)]
        # 天花板衰减：先向两边各扩 0.2 秒（400 ms 窗的跨度），再短平滑
        a_d = att.copy()
        for sh in (1, 2):
            a_d = np.minimum(a_d, np.minimum(np.roll(att, sh), np.roll(att, -sh)))
        a_d = np.convolve(np.pad(a_d, 2, mode="edge"), ker5, mode="valid")[:len(att)]
        g = g + np.interp(grid, t, a_d)
        gs = np.interp(np.arange(n) / SR, grid, g)
        mpath = os.path.join(tmpdir, "lv_music.wav")
        sf.write(mpath, (bed * (10 ** (gs / 20))[:, None]).astype(np.float32), SR, subtype="FLOAT")
        dpath = os.path.join(tmpdir, "lv_ducked.wav")
        ducked(vpath, mpath, dpath, dur)
        md, _ = sf.read(dpath, dtype="float32")
        mm = momentary_lufs(md)
        k = min(len(mm), len(mv), len(ceil))
        gaps = {}
        for e, sel in lines:
            gaps[e["id"]] = float(np.median(line_l[e["id"]] - mm[:k][sel[:k]]))
        err = {e["id"]: gaps[e["id"]] - (GAP_DB_OPEN if e["sec"] == "S0" else GAP_DB) for e in ent}
        over = mm[:k] - ceil[:k]                    # >0：音乐顶过了天花板
        worst = max(abs(x) for x in err.values())
        worst_over = float(np.max(over[np.isfinite(over)]))
        log.append(dict(iter=it, worst_err_db=round(worst, 2), worst_over_ceiling_db=round(worst_over, 2),
                        gap_min=round(min(gaps.values()), 1), gap_max=round(max(gaps.values()), 1)))
        print(f"  电平第 {it} 轮：中位偏差最大 {worst:.2f} dB，顶过天花板最多 {worst_over:.2f} dB", flush=True)
        if it == iters or (worst < 0.4 and worst_over < 0.5):
            break
        for e in ent:   # 差值大＝音乐太轻→抬；每轮最多改 8 dB，总量限在 −14…+12 dB
            corr[e["id"]] = float(np.clip(corr[e["id"]] + np.clip(err[e["id"]], -8, 8), -14, 12))
        fin = np.isfinite(over)
        step = np.zeros(len(att))
        step[:k][fin] = np.clip(-over[fin], -10, 2)  # 顶过就压，有余量就慢慢松回（每轮最多 2 dB）
        att = np.clip(att + step, -15, 0)
        att[~np.isfinite(ceil)] = 0.0
    return (bed * (10 ** (gs / 20))[:, None]).astype(np.float32), dict(
        line_gain_db={k_: round(v, 2) for k_, v in corr.items()},
        line_gap_db={k_: round(v, 2) for k_, v in gaps.items()},
        ceiling_gap_db=CEIL_GAP, ceiling_frames_attenuated=int((att < -0.5).sum()),
        ceiling_max_att_db=round(float(att.min()), 1), iterations=log)


def climax_swell(T, bed):
    """高潮那 1.6 秒旁白空白：在侧链自然回升之外再抬 SWELL_DB，前后各 0.25 秒余弦过渡"""
    a, b = T.end("s6g"), T.start("s6g2")
    n = len(bed)
    tt = np.arange(n) / SR
    up = np.clip((tt - a) / 0.25, 0, 1)
    down = np.clip((b - 0.05 - tt) / 0.25, 0, 1)
    shape = 0.5 - 0.5 * np.cos(np.pi * np.minimum(up, down))
    g = 10 ** (SWELL_DB * shape / 20)
    return (bed * g[:, None]).astype(np.float32), dict(swell_db=SWELL_DB, start=round(a, 2), end=round(b, 2))


def main(narr_dir, layers_json, out):
    os.makedirs(out, exist_ok=True)
    T = Timeline(os.environ.get("META") or os.path.join(narr_dir, "meta.json"))
    voice = build_voice(T, narr_dir)
    bed, info = arrange(T, json.load(open(layers_json)))
    n = min(len(voice), len(bed))
    voice, bed = voice[:n], bed[:n]
    if os.environ.get("NO_LEVEL") != "1":
        bed, info["leveling"] = level_to_voice(T, voice, bed, out)
        bed, info["climax_swell"] = climax_swell(T, bed)
    vpath, mpath = os.path.join(out, "voice.wav"), os.path.join(out, "music.wav")
    sf.write(vpath, np.stack([voice, voice], 1), SR, subtype="FLOAT")
    sf.write(mpath, bed, SR, subtype="FLOAT")
    dur = n / SR
    # 成片混音（规范的链路）。真峰值目标取 −2.0：AAC 128k 编码后真峰值会抬高约 0.2–0.5 dB，
    # 实测 −1.5 的 WAV 编完是 −1.3 dBTP，超了规范的 −1.5；留出余量后成片 mp4 仍 ≤ −1.5
    ff("-i", vpath, "-i", mpath, "-filter_complex",
       "[0:a]asplit=2[v][sc];" + music_chain(dur) + ";" + DUCK +
       ";[v][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-2.0:LRA=11",
       "-ar", str(SR), os.path.join(out, "mix.wav"))
    # 仅压低后的音乐（用来量人声与音乐的差）
    ducked(vpath, mpath, os.path.join(out, "music_ducked.wav"), dur)
    for f in ("lv_voice.wav", "lv_music.wav", "lv_ducked.wav"):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    json.dump(info, open(os.path.join(out, "arrange.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:4])
