# -*- coding: utf-8 -*-
"""混音：旁白按 timeline 摆放；底乐按人声包络自动压低（说话时比人声低约 21 dB，较长停顿处抬 4 dB）；
开头 3 秒让磬声露出（声音钩子）。两遍 loudnorm 到 -15 LUFS / -1.5 dBTP。
输出：audio/mix_music.wav（有配乐）、audio/mix_voice.wav（无配乐）、audio/narration.srt
"""
import json, os, subprocess, re
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d

WK = "/tmp/claude-0/work"
SR = 48000
UNDER_DB = float(os.environ.get("UNDER_DB", 21))
GAP_LIFT_DB = 4.0


def db(x):
    return 20 * np.log10(x + 1e-12)


def env_follow(x, win=0.05):
    n = int(win * SR)
    e = np.sqrt(uniform_filter1d(x ** 2, n))
    return e


def smooth_gain(g, att=0.08, rel=0.5):
    """单极平滑（dB 域）：降得快，升得慢。"""
    out = np.empty_like(g); cur = g[0]
    a_a = np.exp(-1 / (att * SR / 64)); a_r = np.exp(-1 / (rel * SR / 64))
    gd = g[::64]; od = np.empty_like(gd)
    for i, v in enumerate(gd):
        a = a_a if v < cur else a_r
        cur = a * cur + (1 - a) * v; od[i] = cur
    return np.repeat(od, 64)[: len(g)]


def loudnorm(inp, out, I=-15.0, TP=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", inp, "-af", f"loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", out], check=True)


def measure(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    s = r.stderr[r.stderr.rindex("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)); tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))
    return I, tp


def srt_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    J = json.load(open(f"{WK}/timeline.json"))
    N = int(np.ceil(J["total"] * SR))
    voice = np.zeros(N, np.float32)
    for x in J["lines"]:
        w, sr = sf.read(f"{WK}/tts/proc/{x['id']}.wav"); assert sr == SR
        i = int(round(x["start"] * SR)); voice[i:i + len(w)] += w[: N - i]
    m, sr = sf.read(f"{WK}/audio/music.wav"); assert sr == SR
    m = m[:N] if len(m) >= N else np.pad(m, ((0, N - len(m)), (0, 0)))
    # 人声活动
    ve = env_follow(voice)
    active = ve > 10 ** (-40 / 20)
    # 把句内短停顿视作仍在说话：闭运算 0.8 s
    k = int(0.8 * SR)
    act = uniform_filter1d(active.astype(np.float32), k) > 0.02
    # 参考电平：说话段人声 RMS、整体音乐 RMS
    v_rms = np.sqrt((voice[active] ** 2).mean())
    mm = m.mean(1)
    m_rms = np.sqrt((mm ** 2).mean())
    base_db = db(v_rms) - UNDER_DB - db(m_rms)      # 说话时音乐增益
    g = np.where(act, base_db, base_db + GAP_LIFT_DB).astype(np.float32)
    t = np.arange(N) / SR
    g = np.where(t < 3.0, np.maximum(g, base_db + 8 - 8 * np.clip((t - 1.5) / 1.5, 0, 1)), g)   # 开头磬声露出
    g = smooth_gain(g)
    gl = 10 ** (g / 20)
    music = m * gl[:, None]
    mix = np.stack([voice, voice], 1) * 0.92 + music
    os.makedirs(f"{WK}/audio", exist_ok=True)
    sf.write(f"{WK}/audio/_mix_raw.wav", mix.astype(np.float32), SR, subtype="FLOAT")
    sf.write(f"{WK}/audio/_voice_raw.wav", np.stack([voice, voice], 1), SR, subtype="FLOAT")
    loudnorm(f"{WK}/audio/_mix_raw.wav", f"{WK}/audio/mix_music.wav")
    loudnorm(f"{WK}/audio/_voice_raw.wav", f"{WK}/audio/mix_voice.wav")
    # 实测：说话段音乐比人声低多少
    sp = act & (t > 3)
    mu = np.sqrt((music.mean(1)[sp] ** 2).mean()); vo = np.sqrt((voice[sp] ** 2).mean())
    gp = (~act) & (t > 3)
    print(f"music under voice (speech): {db(vo) - db(mu):.1f} dB; music in gaps vs speech-voice: {db(vo) - db(np.sqrt((music.mean(1)[gp] ** 2).mean())):.1f} dB")
    for p in ("mix_music.wav", "mix_voice.wav"):
        print(p, "I=%.1f LUFS, TP=%.1f dBTP" % measure(f"{WK}/audio/{p}"))
    # SRT（整句）
    with open(f"{WK}/audio/narration.srt", "w") as f:
        for i, x in enumerate(J["lines"], 1):
            f.write(f"{i}\n{srt_time(x['start'])} --> {srt_time(x['end'])}\n{x['sub']}\n\n")


if __name__ == "__main__":
    main()
