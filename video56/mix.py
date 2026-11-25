# -*- coding: utf-8 -*-
"""混音：旁白 + 开场磬 + 配乐（随旁白自动压低：有旁白时比人声低约 21 dB，停顿处抬 3 dB）。
两遍 loudnorm 到 -15 LUFS / 真峰值 -1.5 dBTP。输出 mix_music.wav 与 mix_dry.wav（无配乐，仅旁白+开场磬）。"""
import os, json, subprocess, re
import numpy as np, soundfile as sf
import pyloudnorm as pyln

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
UNDER_DB = 21.0
PAUSE_LIFT = 3.0


def smooth_env(active, att=0.08, rel=0.45):
    g = np.zeros_like(active, dtype=np.float32)
    a_up, a_dn = np.exp(-1 / (att * SR / 480)), np.exp(-1 / (rel * SR / 480))
    v = 0.0
    for i, x in enumerate(active):
        c = a_up if x > v else a_dn
        v = c * v + (1 - c) * x
        g[i] = v
    return g


def loudnorm(inp, out):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", inp, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true:print_format=json")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", inp, "-af", af, "-ar", "48000", "-c:a", "pcm_f32le", out],
                       capture_output=True, text=True)
    js2 = json.loads(re.search(r"\{[^{}]*\"output_i\"[^{}]*\}", r.stderr, re.S).group(0))
    return js2


def main():
    nar, _ = sf.read(f"{WORK}/narration.wav"); nar = nar.astype(np.float32)
    mus, _ = sf.read(f"{WORK}/music.wav"); mus = mus.astype(np.float32)
    bell, _ = sf.read(f"{WORK}/bell.wav"); bell = bell.astype(np.float32)
    n = len(nar)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    meter = pyln.Meter(SR)
    v_lu = meter.integrated_loudness(nar)
    # 旁白活动（10 ms 帧）
    hop = SR // 100
    fr = nar[: n // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    act = (db > -45).astype(np.float32)
    # 句内小停顿不抬：先做 0.35 s 闭运算
    k = 35
    act = np.convolve(act, np.ones(k), mode="same") > 0
    env = smooth_env(act.astype(np.float32))
    env = np.repeat(env, hop); env = np.pad(env, (0, n - len(env)), mode="edge")
    # 配乐基准电平：使其整体响度 = 旁白 - UNDER_DB
    m_lu = meter.integrated_loudness(mus)
    base = 10 ** ((v_lu - UNDER_DB - m_lu) / 20)
    gain_db = -0.0 * env + PAUSE_LIFT * (1 - env)
    g = base * 10 ** (gain_db / 20)
    # 开头 1.2 秒配乐渐入
    fi = int(1.2 * SR); g[:fi] *= np.linspace(0, 1, fi)
    mus_d = mus * g[:, None]
    # 开场磬：峰值段约比旁白低 4 dB，开口后压低 6 dB
    b = np.zeros((n, 2), np.float32); b[: len(bell)] = bell[:n]
    b_lu = meter.integrated_loudness(np.concatenate([b[: 2 * SR], np.zeros((SR, 2), np.float32)]))
    bg = 10 ** ((v_lu - 4 - b_lu) / 20)
    bd = np.ones(n, np.float32) * bg
    bd *= 10 ** (-6 * env / 20)
    b *= bd[:, None]
    voice2 = np.stack([nar, nar], 1)
    full = voice2 + mus_d + b
    dry = voice2 + b
    sf.write(f"{WORK}/premix_music.wav", full, SR, subtype="FLOAT")
    sf.write(f"{WORK}/premix_dry.wav", dry, SR, subtype="FLOAT")
    r1 = loudnorm(f"{WORK}/premix_music.wav", f"{WORK}/mix_music.wav")
    r2 = loudnorm(f"{WORK}/premix_dry.wav", f"{WORK}/mix_dry.wav")
    # 实测：有旁白时配乐比人声低多少
    va = env > 0.9
    def lu_on(x, mask):
        idx = np.where(mask)[0]
        return meter.integrated_loudness(x[idx]) if len(idx) > SR * 5 else float("nan")
    rep = dict(mix_music=r1, mix_dry=r2, voice_lufs_premix=v_lu,
               music_under_voice_db_speech=v_lu - lu_on(mus_d, va),
               music_under_voice_db_pauses=v_lu - lu_on(mus_d, env < 0.1))
    json.dump(rep, open(f"{WORK}/mix_report.json", "w"), indent=1, default=float)
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in ('output_i', 'output_tp')}) for k, v in rep.items()},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
