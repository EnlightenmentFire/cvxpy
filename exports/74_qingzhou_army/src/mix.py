# -*- coding: utf-8 -*-
"""混音：旁白（按时间线摆放）+ 配乐（电平跟随压动态、人声处闪避、停顿处略抬）+ 音效。
输出 mix_music.wav（成片）与 mix_nomusic.wav（无配乐版），两遍 loudnorm 到 -15 LUFS / -1.5 dBTP。"""
import os, json, subprocess
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d, maximum_filter1d
from timeline import build

A = "/tmp/claude-0/w74/audio"
SR = 48000
MUSIC_UNDER = float(os.environ.get("MUSIC_UNDER", 21.0))   # 有旁白时，音乐比人声低多少 dB


def lufs_quick(x):
    # K 加权近似：只做高通 + 能量（用于相对比较）
    from scipy.signal import butter, sosfilt
    y = sosfilt(butter(2, 100, "highpass", fs=SR, output="sos"), x if x.ndim == 1 else x.mean(1))
    return 10 * np.log10((y ** 2).mean() + 1e-12) - 0.691


def main():
    lines, total = build()
    n = int((total + 0.5) * SR)
    voice = np.zeros(n, np.float32)
    for d in lines:
        x, sr = sf.read(f"/tmp/claude-0/w74/tts/proc/{d['id']}.wav")
        i = int(d["start"] * SR)
        voice[i:i + len(x)] += x[: n - i].astype(np.float32)
    mus, _ = sf.read(f"{A}/music.wav"); mus = mus[:n].astype(np.float32)
    if len(mus) < n:
        mus = np.vstack([mus, np.zeros((n - len(mus), 2), np.float32)])
    sfx, _ = sf.read(f"{A}/sfx.wav"); sfx = sfx[:n].astype(np.float32)
    if len(sfx) < n:
        sfx = np.vstack([sfx, np.zeros((n - len(sfx), 2), np.float32)])
    # ---- 语音活动（含 0.35s 余量）
    hop = SR // 100
    ve = np.sqrt(np.maximum(uniform_filter1d(voice.astype(np.float64) ** 2, hop * 3)[::hop], 0))
    act = maximum_filter1d((ve > 10 ** (-45 / 20)).astype(float), 70)  # 0.7s 窗
    act = uniform_filter1d(act, 40)  # 平滑过渡 0.4s
    # ---- 音乐电平跟随：把 3s 能量往目标拉 70%
    mm = mus.mean(1).astype(np.float64)
    me = 10 * np.log10(uniform_filter1d(mm ** 2, SR * 3)[::hop] + 1e-10)
    vl = lufs_quick(voice[voice != 0]) if np.any(voice) else -20
    target = vl - MUSIC_UNDER
    corr = np.clip((target - me) * 0.7, -10, 14)
    # 有旁白：target；停顿处 +5 dB；高潮段允许再高 3 dB
    ev = {d["v"]: d for d in lines}
    tt = np.arange(len(corr)) * hop / SR
    boost = np.zeros_like(corr)
    for v, extra, dur in [("transform", 3.0, 18.0), ("end_quote", 3.0, 10.0), ("tide_flash", 2.0, 6.0), ("battle_bian", 2.0, 10.0)]:
        t0 = ev[v]["start"] - 1.0
        boost += extra * np.clip((tt - t0) / 1.5, 0, 1) * np.clip((t0 + dur - tt) / 2.0, 0, 1)
    gain_db = corr + (1 - act) * 5.0 + boost
    gain_db[: int(0.45 * 100)] = corr[: int(0.45 * 100)] + 6  # 开场声音钩子：鼓先出
    g = 10 ** (np.interp(np.arange(n) / SR, tt, gain_db) / 20)
    music = mus * g[:, None].astype(np.float32)
    v2 = np.stack([voice, voice], 1)
    sfx_g = 10 ** (-4 / 20)
    mixes = {"music": v2 + music + sfx * sfx_g, "nomusic": v2 + sfx * sfx_g}
    # 测量：旁白区间里，音乐比人声低多少
    vm = act[: len(me)] > 0.99
    idx = (np.where(vm)[0] * hop)
    sel = np.zeros(n, bool)
    for i in idx[::10]:
        sel[i:i + hop * 10] = True
    sel[n:] = False
    dv = lufs_quick(voice[sel]); dm = lufs_quick(music[sel])
    adj = (dv - float(os.environ.get("UNDER", 22.0))) - dm
    music *= 10 ** (adj / 20)
    mixes = {"music": v2 + music + sfx * sfx_g, "nomusic": v2 + sfx * sfx_g}
    dm2 = lufs_quick(music[sel]); sil = ~sel; sil[:int(0.5 * SR)] = False
    print("speech-region: voice %.1f, music %.1f, diff %.1f dB (adj %.1f)" % (dv, dm2, dv - dm2, adj))
    for k, x in mixes.items():
        p = f"{A}/pre_{k}.wav"; sf.write(p, x, SR, subtype="FLOAT")
        # 两遍 loudnorm
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        js = json.loads(r[r.rfind("{"):r.rfind("}") + 1])
        af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
              f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,aresample=48000")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", af, "-ar", "48000", f"{A}/mix_{k}.wav"], check=True)
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{A}/mix_{k}.wav", "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        tail = r[r.rfind("Summary"):]
        I = [l for l in tail.splitlines() if "I:" in l][0].strip(); TP = [l for l in tail.splitlines() if "Peak:" in l][0].strip()
        print(k, I, TP)
    # 旁白单独轨（备用）
    sf.write(f"{A}/narration.wav", voice, SR, subtype="PCM_24")


if __name__ == "__main__":
    main()
