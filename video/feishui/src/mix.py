# -*- coding: utf-8 -*-
"""混音：旁白（按时间轴摆放）+ 原创配乐（随旁白自动压低）+ 少量合成音效 → 两遍 loudnorm 到 -15 LUFS / -1.5 dBTP。
输出 WORK/mix/mix.wav（含配乐）与 WORK/mix/mix_nomusic.wav（无配乐版：旁白＋音效）。"""
import os, json, subprocess, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, sosfiltfilt

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
TL = json.load(open(f"{HERE}/timeline.json"))
L = {l["id"]: l for l in TL["lines"]}
A = lambda i: L[i]["start"]; E = lambda i: L[i]["end"]; S0 = lambda s: TL["secs"][s]["start"]
N = int(TL["total"] * SR)
MUSIC_UNDER = float(os.environ.get("MUSIC_UNDER", 21.0))   # 有旁白时，音乐比人声低多少 dB
MUSIC_GAP = float(os.environ.get("MUSIC_GAP", 15.0))       # 旁白停顿处


def voice_track():
    v = np.zeros(N, np.float32)
    for l in TL["lines"]:
        x, sr = sf.read(f"{W}/tts/proc/{l['id']}.wav"); assert sr == SR
        i = int(l["start"] * SR); v[i:i + len(x)] += x[:max(0, N - i)]
    return v


def rms_db(x, win):
    k = np.ones(win) / win
    return 10 * np.log10(np.convolve(x.astype(np.float64) ** 2, k, mode="same") + 1e-12)


def smooth(x, tau_s, fs):
    a = np.exp(-1 / (tau_s * fs)); y = np.empty_like(x); acc = x[0]
    for i in range(len(x)): acc = a * acc + (1 - a) * x[i]; y[i] = acc
    return y


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)


def env(n, a, r):
    e = np.ones(n, np.float32); ai, ri = int(a * SR), int(r * SR)
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] = np.linspace(1, 0, ri); return e


def sfx_track():
    s = np.zeros((N, 2), np.float32)
    def put(t, x, g=1.0, pan=0.0):
        i = int(t * SR); x = x[:max(0, N - i)]
        s[i:i + len(x), 0] += x * g * (1 - max(0, pan)); s[i:i + len(x), 1] += x * g * (1 + min(0, pan))
    def wind(t0, t1, seed, g):
        n = int((t1 - t0) * SR); x = noise(n, seed)
        x = sosfilt(butter(2, [150, 900], "bandpass", fs=SR, output="sos"), x)
        lfo = 0.6 + 0.4 * np.sin(np.linspace(0, (t1 - t0) * 0.6, n) * 2 * np.pi + seed)
        put(t0, x * lfo * env(n, 1.5, 2.0), g)
    wind(0, A("s1_03") + 0.5, 1, 0.05)
    wind(S0("s6"), A("s6_05") + 0.5, 2, 0.07)
    wind(A("s6_11"), A("s6_12"), 3, 0.05)
    # 溃奔：低沉的人潮轰鸣
    t0, t1 = A("s5_29") + 0.5, A("s5_37") + 0.5; n = int((t1 - t0) * SR)
    x = sosfilt(butter(2, [60, 400], "bandpass", fs=SR, output="sos"), noise(n, 4))
    put(t0, x * env(n, 3.0, 3.0), 0.09)
    t0, t1 = A("s5_41") + 0.8, A("s5_43"); n = int((t1 - t0) * SR)
    x = sosfilt(butter(2, [80, 600], "bandpass", fs=SR, output="sos"), noise(n, 5))
    put(t0, x * env(n, 1.0, 2.0), 0.08)
    # 洛涧：箭矢破空
    for k, tt in enumerate([A("s3_05") + 1.5, A("s3_07") + 1.2]):
        n = int(0.7 * SR); x = noise(n, 10 + k); f = np.linspace(0, 1, n)
        x = sosfilt(butter(2, [1500, 6000], "bandpass", fs=SR, output="sos"), x) * np.sin(np.pi * f) ** 2
        put(tt, x, 0.12, pan=0.4 - 0.8 * k)
    # 棋子落盘（与画面同一套时刻）
    t2, tE = A("s7_02"), A("s7_09")
    times = [t2 + 1 + i * (tE - t2 - 4) / 20 for i in range(20)] + [A("s7_08") + 0.35]
    for k, tt in enumerate(times):
        n = int(0.12 * SR); tt_ = np.arange(n) / SR
        x = (np.sin(2 * np.pi * 2300 * tt_) * 0.6 + np.sin(2 * np.pi * 3700 * tt_) * 0.4) * np.exp(-tt_ * 60) + noise(n, 30 + k) * np.exp(-tt_ * 200) * 0.3
        put(tt + 0.25, x.astype(np.float32), 0.10 if k < 20 else 0.16, pan=(k % 5 - 2) * 0.1)
    # 屐齿折：木头断裂
    tH = A("s7_09") + (E("s7_09") - A("s7_09")) * 0.62
    n = int(0.5 * SR); tt_ = np.arange(n) / SR
    x = noise(n, 50) * np.exp(-tt_ * 25) + 0.6 * np.sin(2 * np.pi * 180 * tt_) * np.exp(-tt_ * 18)
    x = sosfilt(butter(2, [120, 3500], "bandpass", fs=SR, output="sos"), x)
    put(tH, x.astype(np.float32), 0.35)
    # 碎木落地
    for k in range(3):
        n = int(0.15 * SR); tt_ = np.arange(n) / SR
        put(tH + 0.5 + 0.18 * k, (noise(n, 60 + k) * np.exp(-tt_ * 40)).astype(np.float32), 0.08 / (k + 1))
    return s


def loudnorm(inp, out, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", inp, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inp, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", out], check=True)


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]; P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1]
    return float(I), float(P)


def main():
    os.makedirs(f"{W}/mix", exist_ok=True)
    v = voice_track()
    m, sr = sf.read(f"{W}/music/music.wav"); assert sr == SR
    m = m[:N].astype(np.float32)
    if len(m) < N: m = np.pad(m, ((0, N - len(m)), (0, 0)))
    sfx = sfx_track()
    # 旁白活动：用 50 ms 窗 RMS 判断；有声段的平均电平作为人声基准
    hop = int(0.05 * SR)
    vb = np.sqrt((v[:N // hop * hop].reshape(-1, hop) ** 2).mean(1)) + 1e-9
    vdb = 20 * np.log10(vb)
    active = vdb > -45
    act_s = np.convolve(active.astype(float), np.ones(21) / 21, mode="same") > 0.05     # 前后 0.5 s 内有声算“说话中”
    v_ref = 20 * np.log10(np.sqrt(np.mean(vb[active] ** 2)))
    mb = m[:N // hop * hop].mean(1).reshape(-1, hop)
    mdb = 10 * np.log10(np.convolve((mb ** 2).mean(1), np.ones(60) / 60, mode="same") + 1e-12)  # 3 s 窗
    target = np.where(act_s, v_ref - MUSIC_UNDER, v_ref - MUSIC_GAP)
    g = np.clip(target - mdb, -30, 14)
    g = np.where(mdb < -60, -10, g)
    g = smooth(g, 0.35, 20)
    # 开场第一秒：鼓声钩子不压（人声 0.12 s 即入，但让第一下鼓打出来）
    gain = np.interp(np.arange(N) / SR, (np.arange(len(g)) + 0.5) * hop / SR, 10 ** (g / 20)).astype(np.float32)
    mm = m * gain[:, None]
    under = []
    for a, b in [(S0(s), TL["secs"][s]["end"]) for s in TL["secs"]]:
        i0, i1 = int(a / 0.05), int(b / 0.05)
        sel = active[i0:i1]
        if sel.any():
            mlev = 10 * np.log10((((mb[i0:i1] * (10 ** (g[i0:i1] / 20))[:, None]) ** 2).mean(1))[sel].mean() + 1e-12)
            under.append(round(v_ref - mlev, 1))
    print("music below voice per section (dB, speech frames, RMS):", under)
    vv = np.stack([v, v], 1)
    full = vv + mm + sfx
    nom = vv + sfx
    for name, x in [("mix", full), ("mix_nomusic", nom)]:
        sf.write(f"{W}/mix/{name}_pre.wav", x, SR, subtype="FLOAT")
        loudnorm(f"{W}/mix/{name}_pre.wav", f"{W}/mix/{name}.wav")
        print(name, "LUFS/peak", measure(f"{W}/mix/{name}.wav"))
    sf.write(f"{W}/mix/voice_only.wav", v, SR, subtype="PCM_24")


if __name__ == "__main__":
    main()
