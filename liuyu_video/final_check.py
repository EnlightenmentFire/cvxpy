# -*- coding: utf-8 -*-
"""成片音频质检（对应《配乐规范》第五节）：
- 整体响度 / 真峰值（EBU R128）
- 有旁白时人声比音乐高多少 dB（目标 15–18）
- 逐句 ASR：纯人声 vs 混音 vs 模拟手机外放（300 Hz–7 kHz 单声道）
python final_check.py MIX_DIR NARR_DIR
环境变量 IDS=s2e,s2f…：只重跑这几句的 ASR，其余句沿用 check.json 里的旧结果（用于只改了个别句的情况）
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import Timeline  # noqa: E402
import qtts  # noqa: E402
import qnarr  # noqa: E402

SR = 48000


def ebur128(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1))
    LRA = float(re.search(r"LRA:\s+(-?[\d.]+) LU", s).group(1))
    TP = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))
    return dict(I=I, LRA=LRA, TP=TP)


def momentary_lufs(x):
    """EBU R128 瞬时响度：K 加权，400 ms 窗，100 ms 步进"""
    from scipy.signal import lfilter
    if x.ndim == 1:
        x = x[:, None]
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]; a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]; a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x.astype(np.float64), axis=0), axis=0)
    p = (y ** 2).sum(1)
    hop, win = int(0.1 * SR), int(0.4 * SR)
    c = np.concatenate([[0], np.cumsum(p)])
    idx = np.arange(0, len(p) - win, hop)
    return -0.691 + 10 * np.log10((c[idx + win] - c[idx]) / win + 1e-12)


def frames_db(x, win=0.05):
    if x.ndim == 2:
        x = x.mean(1)
    n = int(win * SR)
    k = len(x) // n
    return 20 * np.log10(np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)


def main(mix_dir, narr_dir):
    T = Timeline(os.path.join(narr_dir, "meta.json"))
    out = {}
    out["mix_loudness"] = ebur128(os.path.join(mix_dir, "mix.wav"))
    v, _ = sf.read(os.path.join(mix_dir, "voice.wav"), dtype="float32")
    m, _ = sf.read(os.path.join(mix_dir, "music_ducked.wav"), dtype="float32")
    n = min(len(v), len(m))
    dv, dm = frames_db(v[:n]), frames_db(m[:n])
    on = dv > -32
    diff = dv[on] - dm[on]
    out["voice_minus_music_db"] = dict(median=round(float(np.median(diff)), 1), p10=round(float(np.percentile(diff, 10)), 1),
                                       p90=round(float(np.percentile(diff, 90)), 1))
    # 标准量法：K 加权 400 ms 瞬时响度，说话中的窗口里人声比压低后的音乐高多少
    mv, mm = momentary_lufs(v[:n]), momentary_lufs(m[:n])
    speech = mv > (np.median(mv[mv > -60]) - 10)
    dk = mv[speech] - mm[speech]
    out["voice_minus_music_lufs_400ms"] = dict(median=round(float(np.median(dk)), 1),
                                               p10=round(float(np.percentile(dk, 10)), 1),
                                               p90=round(float(np.percentile(dk, 90)), 1))
    out["music_lufs_speech_median"] = round(float(np.median(mm[speech])), 1)
    out["music_lufs_pause_median"] = round(float(np.median(mm[mv < -60])), 1)
    # 高潮空白处音乐电平（应明显回升）
    p0 = T.end("s6g")
    seg = dm[int((p0 + 0.3) / 0.05): int((p0 + 1.5) / 0.05)]
    out["climax_gap_music_db"] = round(float(np.mean(seg)), 1)
    out["speech_music_db_median"] = round(float(np.median(dm[on])), 1)
    # 逐句 ASR
    mix, _ = sf.read(os.path.join(mix_dir, "mix.wav"), dtype="float32")
    import librosa
    from scipy.signal import butter, sosfilt
    sos_hp = butter(2, 300, btype="highpass", fs=SR, output="sos")
    sos_lp = butter(4, 7000, btype="lowpass", fs=SR, output="sos")
    only = [x for x in os.environ.get("IDS", "").split(",") if x]
    old_rows = {}
    if only and os.path.exists(os.path.join(mix_dir, "check.json")):
        old_rows = {r["id"]: r for r in json.load(open(os.path.join(mix_dir, "check.json"))).get("asr_rows", [])}
    rows = []
    for ent in T.lines:
        if only and ent["id"] not in only and ent["id"] in old_rows:
            rows.append(old_rows[ent["id"]])
            continue
        a, b = int((ent["start"] - 0.05) * SR), int((ent["end"] + 0.1) * SR)
        want = qtts.syllables(ent["text"])
        res = {}
        for tag, src in (("voice", v[:, 0] if v.ndim == 2 else v), ("mix", mix.mean(1))):
            clip = librosa.resample(src[a:b], orig_sr=SR, target_sr=24000)
            wt, _ = qtts.asr(clip)
            pt = qnarr.paraformer(clip)
            res[tag] = max(qtts.similarity(want, qtts.syllables(wt)), qtts.similarity(want, qtts.syllables(pt)))
        phone = sosfilt(sos_lp, sosfilt(sos_hp, mix.mean(1)[a:b]))
        clip = librosa.resample(phone.astype(np.float32), orig_sr=SR, target_sr=24000)
        wt, _ = qtts.asr(clip)
        pt = qnarr.paraformer(clip)
        res["phone"] = max(qtts.similarity(want, qtts.syllables(wt)), qtts.similarity(want, qtts.syllables(pt)))
        rows.append(dict(id=ent["id"], **{k: round(x, 3) for k, x in res.items()}))
        print(rows[-1], flush=True)
    for k in ("voice", "mix", "phone"):
        vals = [r[k] for r in rows]
        out[f"asr_{k}_mean"] = round(float(np.mean(vals)), 4)
        out[f"asr_{k}_min"] = round(float(np.min(vals)), 3)
    out["asr_rows"] = rows
    json.dump(out, open(os.path.join(mix_dir, "check.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "asr_rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
