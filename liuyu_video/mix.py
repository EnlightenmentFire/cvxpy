# -*- coding: utf-8 -*-
"""旁白 + 配乐混音：人声 50 Hz 高通、统一到 -18 dBFS RMS；音乐在人声下自动压低；最后限幅。

python mix.py NARR_DIR OUT.wav [t0 t1]
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import music  # noqa: E402
import script  # noqa: E402
from timeline import Timeline  # noqa: E402

SR = 48000
VOICE_RMS_DB = -18.0
MUSIC_BED_DB = -27.0      # 无旁白处音乐的 RMS
DUCK_DB = -10.0


def merged_meta(narr_dir, fallback="/home/user/work/narr_main/meta.json"):
    m = {x["id"]: x for x in json.load(open(os.path.join(narr_dir, "meta.json")))}
    fb = {x["id"]: x for x in json.load(open(fallback))}
    out = []
    for d in script.LINES:
        out.append(m.get(d["id"]) or fb[d["id"]])
    p = os.path.join(narr_dir, "meta_merged.json")
    json.dump(out, open(p, "w"), ensure_ascii=False)
    return p, set(m)


def rms_db(x, thr_db=-50.0):
    win = int(0.02 * SR)
    k = len(x) // win
    fr = x[: k * win].reshape(k, win)
    r = np.sqrt((fr ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(r + 1e-9)
    v = r[db > thr_db]
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-9) if len(v) else -120.0


def build_voice(T, narr_dir, have):
    n = int(T.total * SR) + SR
    v = np.zeros(n, np.float32)
    for ent in T.lines:
        if ent["id"] not in have:
            continue
        w, sr = sf.read(os.path.join(narr_dir, ent["id"] + ".wav"), dtype="float32")
        if sr != SR:
            w = resample_poly(w, SR, sr).astype(np.float32)
        # 逐句统一响度（有声段 RMS），避免不同 seed 之间忽大忽小
        w = w * 10 ** ((VOICE_RMS_DB - rms_db(w)) / 20)
        i = int(ent["start"] * SR)
        v[i:i + len(w)] += w[: max(0, n - i)]
    sos = butter(2, 50, btype="highpass", fs=SR, output="sos")
    v = sosfilt(sos, v).astype(np.float32)
    g = 10 ** ((VOICE_RMS_DB - rms_db(v)) / 20)
    return v * g


def main(narr_dir, out, t0=None, t1=None):
    meta_path, have = merged_meta(narr_dir)
    T = Timeline(meta_path)
    voice = build_voice(T, narr_dir, have)
    mus = music.compose(T)
    n = min(len(voice), len(mus))
    voice, mus = voice[:n], mus[:n]
    # 音乐电平：以无旁白段为准
    ref = mus[int(T.sec_start["S1"] * SR): int(T.sec_end["S2"] * SR)].mean(1)
    mus *= 10 ** ((MUSIC_BED_DB - rms_db(ref, thr_db=-70)) / 20)
    mus = music.duck(mus, voice, depth_db=DUCK_DB)
    mix = mus + voice[:, None]
    if t0 is not None:
        mix = mix[int(t0 * SR): int(t1 * SR)]
    tmp = out + ".pre.wav"
    sf.write(tmp, mix.astype(np.float32), SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", tmp, "-af",
                    "alimiter=limit=0.891:attack=5:release=60:level=disabled", "-ar", str(SR), "-c:a", "pcm_s16le", out],
                   check=True)
    os.remove(tmp)
    # 记录电平
    vr = rms_db(voice)
    print(f"voice RMS {vr:.1f} dBFS · total {T.total:.1f}s · wrote {out}")
    return T


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], float(a[3]) if len(a) > 3 else None, float(a[4]) if len(a) > 4 else None)
