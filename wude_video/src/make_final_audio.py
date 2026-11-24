"""Build the final soundtrack: arrange MusicGen material along the story, mix per 配乐规范, QC.

usage: make_final_audio.py <selection.json> <out_dir>
selection.json: {"base": [wav, ...], "push_cold": [...], ...}  (chosen clips, in order of use)
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from timeline import Timeline
import audio_synth as A
import music_arrange as M
import final_mix as F

BUILD = "/home/user/wude_build"


def line(tl, lid):
    return next(l for l in tl.lines if l["id"] == lid)


def seg(tl, sid):
    return next(s for s in tl.segs if s["id"] == sid)


def fx_t(tl, name):
    return next(t for (t, n, p) in tl.fx if n == name)


def sfx_t(tl, name):
    return next(t for (t, n) in tl.sfx if n == name)


def plan(tl):
    """(t, layer, extra_gain_db, crossfade_s) — the three layers follow the story."""
    flip_t = tl.wk_flip[0]
    S = [
        (0.0, "base@0", 0.0, 0.0),                                 # 铺底: 冷启动 + 邹衍
        (seg(tl, "S2")["t0"] - 1.0, "push_cold", 0.0, 3.0),         # 推进: 秦
        (sfx_t(tl, "drum_stop"), "DROP", 0.0, 0.0),                # 鼓声停，「刚毅戾深」
        (line(tl, "S2_20")["t0"], "base", -2.0, 3.0),               # 低铺底
        (seg(tl, "S3")["t0"] - 1.0, "push_tension", 0.0, 3.0),      # 推进: 汉初的别扭
        (fx_t(tl, "dragon") - 0.3, "climax@2", -2.0, 1.5),          # 黄龙: 音乐单独出来
        (line(tl, "S4_14")["t0"], "push_tension", 0.0, 3.0),
        (sfx_t(tl, "cut"), "STOP", 0.0, 0.0),                      # 新垣平: 骤停一拍
        (sfx_t(tl, "cut") + 2.0, "base", -2.0, 2.0),                # 停一拍（约 1 秒静），再慢慢回来
        (seg(tl, "S5")["t0"] - 1.0, "push_warm", 0.0, 3.0),         # 太初
        (flip_t, "climax@0", 0.0, 1.0),                            # 全片高潮: 轮盘翻面
        (line(tl, "S6_09")["t0"], "push_tension", 0.0, 4.0),        # 闰位、王莽
        (line(tl, "S6_27")["t0"], "push_warm", 0.0, 3.0),           # 收束 → 东汉
        (seg(tl, "S8")["t0"] - 1.0, "base", 0.0, 4.0),              # "终始": 回到铺底
        (seg(tl, "S9")["t0"] - 0.5, "climax@1", -3.0, 4.0),         # 尾声上扬
        (line(tl, "S9_03")["t0"] + 0.5, "ending@0", 0.0, 3.0),      # 收成单件古琴 + 余音
    ]
    return S


def sfx_track(tl):
    """Event accents only (the score itself now comes from MusicGen)."""
    T = A.Track(tl.total)
    r = np.random.default_rng(3)
    for (tg, el, lab, fa, ta) in tl.wk_go:
        if abs(ta - fa) > 1:
            T.add(tg + 0.03, A.qing(740.0, vel=0.9, seed=int(r.integers(1e6))), pan=0.3, gain=1.0)
    if tl.wk_flip:
        ft, fd = tl.wk_flip
        for i, nm in enumerate(["A3", "C4", "D4", "E4", "G4", "A4"]):
            T.add(ft + 0.1 + i * 0.17, A.bell(A.NOTE[nm], 5.0, vel=0.9, seed=i), pan=-0.6 + i * 0.24, gain=1.0)
        T.add(ft + fd * 0.5, A.bell(A.NOTE["A2"], 7.0, vel=1.0, seed=77), pan=0, gain=1.1)
    for (t, name) in tl.sfx:
        if name == "bells_soft":
            for i, nm in enumerate(["E4", "D4", "A3"]):
                T.add(t + i * 0.6, A.bell(A.NOTE[nm], 6.0, vel=0.6, seed=i + 40), pan=-0.3 + 0.3 * i, gain=0.9)
        elif name == "long_tone":
            T.add(t - 0.2, A.swell(7.0, 110.0, vel=1.0), gain=0.9)
        elif name == "seal":
            T.add(t, A.drum(vel=0.5, dry=True, f0=140, f1=70), gain=0.8)
            T.add(t, A.clack(vel=0.5), gain=0.7)
    for (t, name, p) in tl.fx:
        if name == "banner":
            T.add(t, A.whoosh(1.2, vel=1.0), pan=0.3)
        elif name == "snake_cut":
            T.add(t, A.slash(vel=0.9), pan=0.1)
        elif name == "seal_stamp":
            T.add(t, A.drum(vel=0.6, dry=True, f0=150, f1=70), gain=0.8)
            T.add(t, A.clack(vel=0.6), gain=0.7)
    T.add(tl.segs[0]["t0"] + 0.8, A.bell(A.NOTE["A2"], 7.0, vel=0.7, seed=9), gain=0.8)
    out = A.reverb(T.buf, wet=0.25, rt60=2.6)
    return out[: int(tl.total * A.SR)]


def main():
    sel = json.load(open(sys.argv[1]))["choice"]
    for layer, paths in sel.items():   # use the continued (longer) version of the chosen clip when present
        ext = paths[0][:-4] + "_ext.wav"
        if os.path.exists(ext):
            paths[0] = ext
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
    durs = json.load(open(f"{BUILD}/voice_post/durations.json"))
    tl = Timeline(segs, durs)
    print(f"timeline {tl.total:.1f}s", flush=True)
    # voice
    lufs0, g = F.write_voice(tl, f"{BUILD}/voice_post", f"{out}/voice.wav")
    print(f"voice: {lufs0:.1f} LUFS -> -16 (gain {g:+.1f} dB)", flush=True)
    # music
    mat = M.load_material(sel)
    music = M.build(plan(tl), tl.total, mat)
    sf.write(f"{out}/music.wav", music.astype(np.float32), M.SR, subtype="FLOAT")
    sfx = sfx_track(tl)
    sf.write(f"{out}/sfx.wav", sfx.astype(np.float32), A.SR, subtype="FLOAT")
    # calibrate the sidechain (attack 15 ms / release 500 ms / ratio 10 as in the spec):
    #   * music 15-18 dB under the voice while narrating (aim 16.5)
    #   * in longer pauses the music comes back up, but stays ~8 dB under the voice level
    cal = []
    for th in (0.05, 0.08, 0.11, 0.15):
        lo, hi = 0.05, 2.0
        rep = None
        for _ in range(7):                       # bisection on music volume
            vol = (lo * hi) ** 0.5
            F.ducked_music(f"{out}/voice.wav", f"{out}/music.wav", f"{out}/sfx.wav", f"{out}/duck.wav", tl.total,
                           music_vol=vol, th=th)
            rep = F.ducking_report(tl, f"{out}/voice.wav", f"{out}/duck.wav")
            d = rep["voice_minus_music_median"]
            if abs(d - 16.5) < 0.4:
                break
            if d > 16.5:
                lo = vol
            else:
                hi = vol
        gap = rep["voice_speech_db"] - (rep["music_in_long_pauses_db"] or -99)
        cal.append(dict(th=th, vol=vol, rep=rep, pause_gap=gap))
        print(f"th={th} vol={vol:.3f} speech_diff={rep['voice_minus_music_median']:.1f} pause_gap={gap:.1f}",
              flush=True)
    best = min(cal, key=lambda c: abs(c["rep"]["voice_minus_music_median"] - 16.5) * 2 + abs(c["pause_gap"] - 8))
    vol, th = best["vol"], best["th"]
    F.ducked_music(f"{out}/voice.wav", f"{out}/music.wav", f"{out}/sfx.wav", f"{out}/duck.wav", tl.total,
                   music_vol=vol, th=th)
    json.dump(dict(chosen=best, tried=cal), open(f"{out}/ducking.json", "w"), indent=1)
    m1, m2 = F.mix(f"{out}/voice.wav", f"{out}/music.wav", f"{out}/sfx.wav", f"{out}/mix.wav", tl.total,
                   music_vol=vol, th=th)
    print("loudnorm pass1", m1, "\npass2", m2, flush=True)
    # 无配乐 fallback: voice + accents only
    silent = np.zeros_like(music)
    sf.write(f"{out}/music_silent.wav", silent.astype(np.float32), M.SR, subtype="FLOAT")
    F.mix(f"{out}/voice.wav", f"{out}/music_silent.wav", f"{out}/sfx.wav", f"{out}/mix_nomusic.wav", tl.total,
          music_vol=vol, th=th)
    print("done", flush=True)


if __name__ == "__main__":
    main()
