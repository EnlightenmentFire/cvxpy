# -*- coding: utf-8 -*-
"""按《配乐规范》"每层生成 2–3 版，挑最好听、最不抢人声的一版"：用客观指标排序。
指标：① 1–4 kHz 人声频段能量占比（越低越不抢）② 短时响度突跳（"突然冒出来"）③ 是否混进类人声
     ④ 掩蔽测试：一段旁白 + 该配乐（按规范的 EQ 与 16 dB 差值）后的 ASR 误读率 ⑤ 削波 / 中途断音。
输出 music_choice.json 与评分表 music_scores.json。
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
SR = 48000
PROBE_BEATS = ["s1_09", "s1_10", "s1_11"]    # 用来做掩蔽测试的旁白


def load48(p):
    w, sr = sf.read(p, dtype="float32", always_2d=True)
    if sr != SR:
        w = resample_poly(w, SR, sr, axis=0).astype(np.float32)
    return w


def band_ratio(x):
    m = x.mean(1)
    spec = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    f = np.fft.rfftfreq(len(m), 1 / SR)
    return float(spec[(f >= 1000) & (f <= 4000)].sum() / (spec[f >= 40].sum() + 1e-12))


def jumps(x):
    from mix_spec import short_term_lufs
    L = short_term_lufs(x, 0.4, 0.1)
    L = L[L > -70]
    if len(L) < 5:
        return 0.0, 99.0
    d = np.diff(L[::4])
    return float(np.max(d)) if len(d) else 0.0, float(np.percentile(L, 95) - np.percentile(L, 10))


def dropouts(x):
    m = np.abs(x.mean(1))
    k = int(0.05 * SR)
    env = np.convolve(m, np.ones(k) / k, mode="same")
    ref = np.percentile(env, 90)
    low = env < ref * 0.02
    # 中段（去掉首尾 2 秒）出现 >0.8 秒的近静音
    s, e = int(2 * SR), len(low) - int(2 * SR)
    run, best = 0, 0
    for v in low[s:e:int(0.01 * SR)]:
        run = run + 1 if v else 0
        best = max(best, run)
    return best * 0.01


def main():
    from asr_check import transcribe
    from tts_build import cer
    man = json.load(open(os.path.join(WORK, "music_manifest.json")))
    vman = json.load(open(os.path.join(WORK, "manifest.json")))
    # 旁白探针
    parts, ref = [], ""
    for bid in PROBE_BEATS:
        w = load48(vman[bid]["file"]).mean(1)
        parts += [w, np.zeros(int(0.3 * SR), np.float32)]
        ref += vman[bid]["say"]
    probe = np.concatenate(parts)
    probe *= 10 ** (-18 / 20) / (np.sqrt(np.mean(probe[np.abs(probe) > 0.01] ** 2)) + 1e-9)
    tmp = os.path.join(WORK, "_probe.wav")
    sf.write(tmp, probe, SR)
    base_cer = cer(ref, transcribe(tmp))
    eq = butter(2, [2000, 4000], btype="bandstop", fs=SR, output="sos")
    scores = {"_voice_only_cer": base_cer}
    by_layer = {}
    for key, info in sorted(man.items()):
        x = load48(info["file"])
        br = band_ratio(x)
        jmax, lra = jumps(x)
        drop = dropouts(x)
        peak = float(np.abs(x).max())
        # 类人声检测：music-only 让 ASR 自动识别语言，若吐出成串文字则可疑
        mo = os.path.join(WORK, "_mo.wav")
        sf.write(mo, x.mean(1), SR)
        segs = transcribe(mo, lang=None, words=True)
        vocal_txt = "".join(s.text for s in segs if getattr(s, "no_speech_prob", 0) < 0.5).strip()
        # 掩蔽：音乐按规范削 3 kHz 4 dB（近似带阻的 40%）、低于人声 16 dB
        L = len(probe)
        m = np.resize(x.mean(1), L)
        m = m - 0.37 * sosfilt(eq, m)
        rv = np.sqrt(np.mean(probe[np.abs(probe) > 0.01] ** 2))
        rm = np.sqrt(np.mean(m ** 2)) + 1e-9
        mix = probe + m * (rv / rm) * 10 ** (-16 / 20)
        mp = os.path.join(WORK, "_mix_probe.wav")
        sf.write(mp, mix, SR)
        c = cer(ref, transcribe(mp))
        s = (c - base_cer) * 10 + br * 4 + max(0, jmax - 6) * 0.3 + drop * 2 + (3 if len(vocal_txt) > 12 else 0) \
            + (1 if peak > 0.99 else 0)
        scores[key] = dict(layer=info["layer"], speech_band=round(br, 3), max_jump_db=round(jmax, 1),
                           range_db=round(lra, 1), dropout_s=round(drop, 2), peak=round(peak, 3),
                           asr_cer_with_music=round(c, 3), vocal_like=vocal_txt[:40], score=round(s, 3))
        by_layer.setdefault(info["layer"], []).append((s, key))
        print(key, scores[key], flush=True)
    choice = {lay: [k for _, k in sorted(v)] for lay, v in by_layer.items()}
    json.dump(scores, open(os.path.join(WORK, "music_scores.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(choice, open(os.path.join(WORK, "music_choice.json"), "w"), indent=1)
    print("choice:", choice)


if __name__ == "__main__":
    main()
