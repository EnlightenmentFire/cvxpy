# -*- coding: utf-8 -*-
"""按《配乐规范》混音：
  · 旁白（含近地警告）作侧链，音乐 sidechaincompress（threshold 0.02 / ratio 10 / attack 15 / release 500）；
  · 音乐 3 kHz 削 4 dB；片头淡入 2 秒、片尾淡出 3 秒；
  · 有旁白时音乐比人声低约 16 dB（实测后自动校准音乐增益）；
  · 两遍 loudnorm：整体 -16 LUFS，真峰值 ≤ -1.5 dBTP。
音效（雨、雨刷、发动机、提示音、闷响）单独一轨，自己做轻度下压。
"""
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt

import audio_mix as AM
import scenes as SC
from score import build_score

SR = 48000
TARGET_GAP_DB = 16.0


def _env(x, fc=6.0):
    m = np.abs(x if x.ndim == 1 else x.mean(1))
    return sosfiltfilt(butter(2, fc, fs=SR, output="sos"), m)


def build_stems(tl, t0, t1, manifest, gpws_manifest, work, with_music=True):
    n = int((t1 - t0) * SR)
    voice = np.zeros(n, np.float32)
    for e in tl:
        if e["start"] + e["dur"] < t0 or e["start"] > t1:
            continue
        if e["say"] and e["id"] in manifest:
            AM._place(voice, AM.load_voice(manifest[e["id"]]["file"]), e["start"] + e.get("lead", 0) - t0)
        if e["gpws"] and e["gpws"] in gpws_manifest:
            AM._place(voice, AM.load_voice(gpws_manifest[e["gpws"]]["file"]) * 0.55, e["start"] - t0)
    voice = AM._hp(voice, 50).astype(np.float32)
    act = np.abs(voice) > 0.01
    if act.any():
        voice *= 10 ** (-18 / 20) / (np.sqrt(np.mean(voice[act] ** 2)) + 1e-9)
    # ── 音效轨 ──
    sfx = np.zeros((n, 2), np.float32)
    runs = []
    for e in tl:
        if e["start"] + e["dur"] <= t0 or e["start"] >= t1:
            continue
        if runs and runs[-1][0] == e["scene"]:
            runs[-1][2] = e["start"] + e["dur"]
        else:
            runs.append([e["scene"], e["start"], e["start"] + e["dur"]])
    AMB = {"cold": (0.9, 0.9, True), "title": (0.35, 0.3, False), "night": (0.2, 0.6, False),
           "cockpit": (0.7, 0.5, False), "map": (0.2, 0.0, False), "timeline": (0.5, 0.4, False),
           "profile": (0.8, 0.6, False), "ua173": (0.0, 0.35, False)}
    for k, (sc, a, b) in enumerate(runs):
        rn, en, wp = AMB.get(sc, (0, 0, False))
        if not (rn or en or wp):
            continue
        a0, b0 = max(a, t0) - t0, min(b, t1) - t0
        L = int((b0 - a0 + 0.8) * SR)
        seg = np.zeros((L, 2))
        if rn:
            seg += AM.rain(L, seed=10 + k, amount=rn)
        if en:
            seg += AM.engine(L, seed=20 + k, amount=en)
        if wp:
            seg += AM.wipers(L, 0.2, amount=0.9)
        f = int(0.4 * SR)
        env = np.ones(L)
        env[:f] = np.linspace(0, 1, f)
        env[-f:] = np.linspace(1, 0, f)
        AM._place(sfx, (seg * env[:, None]).astype(np.float32), a0 - 0.2)
    ladder_build = None
    ladder_cards = None
    for i, e in enumerate(tl):
        if e["start"] + e["dur"] < t0 or e["start"] > t1:
            continue
        st = e["start"] - t0
        if e["scene"] == "chapter":
            AM._place(sfx, AM.whoosh(1.4).astype(np.float32), st)
        if e["scene"] == "impact":
            AM._place(sfx, AM.thud().astype(np.float32) * 0.9, st)
        if e["scene"] == "ladder":
            ev = e["ev"]
            notes = [293.66, 349.23, 392.0, 440.0, 523.25, 587.33]        # D 小调五声，逐级上行
            if ev.get("cards", -1) < 0 and ev.get("build", 0) >= 1 and ev.get("build") != ladder_build:
                AM._place(sfx, AM.tone(notes[ev["build"] - 1], 1.8, 0.11).astype(np.float32), st + 0.05)
            if ev.get("cards", -1) >= 1 and ev.get("cards") != ladder_cards:
                f0 = [0, 146.83, 174.61, 220.0, 293.66][ev["cards"]]
                AM._place(sfx, AM.tone(f0, 1.8, 0.1).astype(np.float32), st + 0.05)
            ladder_build, ladder_cards = ev.get("build"), ev.get("cards")
    # 剖面场景：高度提醒音、01:41:53 起雨刷（按钟表时间换算到片中时间）
    import compose
    prof = [(k, e) for k, e in enumerate(tl) if e["scene"] == "profile"]

    def clock_to_t(clk):
        for k, e in prof:
            c0 = compose.profile_clock(tl, k, e["start"])
            c1 = compose.profile_clock(tl, k, e["start"] + e["dur"] - 1e-3)
            if c0 <= clk <= c1 and c1 > c0:
                return e["start"] + (clk - c0) / (c1 - c0) * e["dur"]
        return None
    for clk in ("01:40:06", "01:40:57", "01:41:45"):
        tt = clock_to_t(SC.hms(clk))
        if tt is not None:
            AM._place(sfx, AM.chime().astype(np.float32), tt - t0)
    tw = clock_to_t(SC.hms("01:41:53"))
    tend = next((e["start"] for e in tl if e["scene"] == "impact"), None)
    if tw is not None and tend is not None and tend > tw:
        AM._place(sfx, AM.wipers(int((tend - tw) * SR), 0.0, amount=0.8).astype(np.float32), tw - t0)
    # 音效在旁白下轻压（约 -7 dB）
    dk = 1 - 0.55 * np.clip(_env(voice) / 0.03, 0, 1)
    sfx *= sosfiltfilt(butter(1, 3, fs=SR, output="sos"), dk)[:, None].astype(np.float32)
    music = build_score(tl, t0, t1, work) if with_music else np.zeros((n, 2), np.float32)
    # 撞山：闷响之后全部静音（≥2 秒）
    for e in tl:
        if e["scene"] == "impact" and t0 <= e["start"] <= t1:
            a = int((e["start"] - t0 + 0.95) * SR)
            b = int((e["start"] - t0 + e["dur"]) * SR)
            sfx[a:b] = 0
            music[a:b] = 0
            voice[a:b] = 0
    return voice, sfx, music


def _ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


GRAPH = ("[0:a]asplit=2[v][sc];"
         "[2:a]volume={g:.4f},equalizer=f=3000:t=q:w=1:g=-4[m];"
         "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];")


def duck_music(voice_wav, music_wav, out_wav, g):
    graph = ("[0:a]anull[sc];[1:a]volume={g:.4f},equalizer=f=3000:t=q:w=1:g=-4[m];"
             "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[out]").format(g=g)
    _ffmpeg(["-i", voice_wav, "-i", music_wav, "-filter_complex", graph, "-map", "[out]", "-c:a", "pcm_f32le",
             out_wav])


def short_term_lufs(x, win=0.4, hop=0.1):
    """简化的 K 加权短时响度（用于相对比较）。"""
    from scipy.signal import lfilter
    m = x if x.ndim == 1 else x.mean(1)
    # K 加权（48 kHz 系数，BS.1770）
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, m))
    W, Hh = int(win * SR), int(hop * SR)
    out = []
    for i in range(0, len(y) - W, Hh):
        out.append(-0.691 + 10 * np.log10(np.mean(y[i:i + W] ** 2) + 1e-12))
    return np.array(out)


def mix(voice, sfx, music, out_wav, work, tag="mix", calibrate=True):
    vw = os.path.join(work, f"_{tag}_voice.wav")
    mw = os.path.join(work, f"_{tag}_music.wav")
    sw = os.path.join(work, f"_{tag}_sfx.wav")
    sf.write(vw, np.stack([voice, voice], 1), SR, subtype="FLOAT")
    sf.write(mw, music, SR, subtype="FLOAT")
    sf.write(sw, sfx, SR, subtype="FLOAT")
    g = 0.5
    report = {}
    has_music = np.abs(music).max() > 1e-4
    if has_music and calibrate:
        for it in range(3):
            dw = os.path.join(work, f"_{tag}_duck.wav")
            duck_music(vw, mw, dw, g)
            d, _ = sf.read(dw, dtype="float32")
            Lv, Lm = short_term_lufs(voice), short_term_lufs(d)
            n = min(len(Lv), len(Lm))
            act = (Lv[:n] > -32) & (Lm[:n] > -70)
            gap = float(np.median(Lv[:n][act] - Lm[:n][act])) if act.any() else 99
            report[f"iter{it}"] = dict(music_gain=round(g, 4), voice_minus_music_db=round(gap, 2))
            print(f"calibrate {it}: gain={g:.3f} voice-music gap={gap:.1f} dB", flush=True)
            if 15.0 <= gap <= 17.5:
                break
            g *= 10 ** ((gap - TARGET_GAP_DB) / 20)
    pre = os.path.join(work, f"_{tag}_pre.wav")
    graph = (GRAPH.format(g=g) + "[v][duck][1:a]amix=inputs=3:duration=first:normalize=0[mx]") if has_music else \
        "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[mx]"
    ins = ["-i", vw, "-i", sw, "-i", mw] if has_music else ["-i", vw, "-i", sw]
    _ffmpeg(ins + ["-filter_complex", graph, "-map", "[mx]", "-c:a", "pcm_f32le", pre])
    # 两遍 loudnorm（-16 LUFS / -1.5 dBTP / LRA 11），片尾 3 秒淡出
    dur = sf.info(pre).duration
    err = _ffmpeg(["-i", pre, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    ln = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**js)
    _ffmpeg(["-i", pre, "-af", f"{ln},afade=t=out:st={max(0, dur - 3):.3f}:d=3,aresample=48000",
             "-c:a", "pcm_s16le", out_wav])
    err = _ffmpeg(["-i", out_wav, "-af", "ebur128=peak=true", "-f", "null", "-"])
    summ = err[err.rindex("Summary:"):]
    report["final"] = " ".join(summ.split())
    report["music_gain"] = g
    return report
