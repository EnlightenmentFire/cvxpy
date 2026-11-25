# -*- coding: utf-8 -*-
"""Build the voice stem from timeline, mix with music (sidechain-ducked) + SFX, loudnorm to -15 LUFS / -1.5 dBTP,
and mux with the picture (aresample=async=1, H.264 + AAC 128k, < 100 MB). Also a no-music version.
usage: python mix.py stems | mix | mux <out_music.mp4> <out_nomusic.mp4>
"""
import sys, os, json, re, subprocess
import numpy as np, soundfile as sf

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
ST = f"{WORK}/stems"
SR = 48000
TARGET = -15.0
MUSIC_UNDER = 21.0     # music (ducked) sits ~21 dB under narration while speaking
SFX_UNDER = 16.0


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, float(tp[-1]) if tp else None


def stems():
    tl = json.load(open(f"{WORK}/timeline.json"))
    n = int(tl["total"] * SR)
    v = np.zeros(n, np.float32)
    for s in tl["scenes"]:
        for L in s["lines"]:
            fn = f"{WORK}/tts/proc/{L['id']}.wav"
            if not os.path.exists(fn):
                print("MISSING", L["id"]); continue
            x, sr = sf.read(fn); assert sr == SR
            a = int(L["start"] * SR); b = min(n, a + len(x))
            v[a:b] += x[:b - a]
    sf.write(f"{ST}/voice.wav", v, SR, subtype="FLOAT")
    print("voice stem", n / SR, "s", lufs(f"{ST}/voice.wav"))


def speech_mask(v, win=0.05):
    m = int(win * SR); k = len(v) // m
    r = np.sqrt((v[:k * m].reshape(k, m) ** 2).mean(1))
    return 20 * np.log10(r + 1e-9) > -38, m


def mix():
    v, _ = sf.read(f"{ST}/voice.wav"); v = v.astype(np.float32)
    mu, _ = sf.read(f"{ST}/music.wav", always_2d=True); fx, _ = sf.read(f"{ST}/sfx.wav", always_2d=True)
    n = len(v)
    mu = np.pad(mu, ((0, max(0, n - len(mu))), (0, 0)))[:n].astype(np.float32)
    fx = np.pad(fx, ((0, max(0, n - len(fx))), (0, 0)))[:n].astype(np.float32)
    sp, m = speech_mask(v)
    k = len(sp)

    def lvl(x, mask):
        xx = x[:k * m].reshape(k, m, -1) if x.ndim == 2 else x[:k * m].reshape(k, m, 1)
        e = (xx ** 2).mean((1, 2))
        return 10 * np.log10(e[mask].mean() + 1e-12)

    lv = lvl(v, sp)
    # ducking envelope: -6 dB under speech (smoothed), so pauses lift slightly
    duck = np.where(sp, 10 ** (-6 / 20), 1.0).astype(np.float32)
    ker = np.ones(10) / 10
    duck = np.convolve(duck, ker, "same")
    duck = np.repeat(duck, m)
    duck = np.pad(duck, (0, n - len(duck)), constant_values=1.0)[:n]
    mu_d = mu * duck[:, None]
    lm = lvl(mu_d, sp)
    mu_d *= 10 ** ((lv - MUSIC_UNDER - lm) / 20)
    # sfx: scale so its active parts sit SFX_UNDER below speech level
    fr = fx[:k * m].reshape(k, m, 2); e = (fr ** 2).mean((1, 2)); act = e > e.max() * 1e-3
    lf = 10 * np.log10(e[act].mean() + 1e-12) if act.any() else -100
    fx *= 10 ** ((lv - SFX_UNDER - lf) / 20)
    fx *= np.clip(duck[:, None] * 1.4, 0, 1)
    vv = np.stack([v, v], 1)
    for name, mixx in [("mix_music", vv + mu_d + fx), ("mix_nomusic", vv + fx)]:
        pre = f"{ST}/{name}_pre.wav"
        sf.write(pre, mixx.astype(np.float32), SR, subtype="FLOAT")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", f"loudnorm=I={TARGET}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True)
        js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
        ln = (f"loudnorm=I={TARGET}:TP=-1.5:LRA=11:linear=true:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", pre, "-af", ln, "-ar", "48000", "-c:a", "pcm_s24le", f"{ST}/{name}.wav"])
        print(name, lufs(f"{ST}/{name}.wav"))
    # report music level under speech
    print(f"music under speech: {lvl(mu_d, sp) - lv:+.1f} dB ; in pauses: {lvl(mu_d, ~sp) - lv:+.1f} dB ; sfx active {lf:.1f}")


def mux(out_music, out_nomusic):
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    pic = f"{WORK}/video/picture.mp4"
    a_k = 128
    v_k = int(95 * 1000 * 1000 * 8 / total / 1000 - a_k - 10)
    v_k = min(v_k, 3500)
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_k}k", "-maxrate", f"{int(v_k * 1.8)}k", "-bufsize", f"{v_k * 3}k",
              "-pix_fmt", "yuv420p", "-r", "25", "-g", "250", "-profile:v", "high"]
    os.chdir(f"{WORK}/video")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic] + common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_k}k",
         "-maxrate", f"{int(v_k * 1.8)}k", "-bufsize", f"{v_k * 3}k", "-pix_fmt", "yuv420p", "-r", "25", "-g", "250",
         "-profile:v", "high", "-pass", "2", "-an", "video_enc.mp4"])
    for out, aud in [(out_music, "mix_music"), (out_nomusic, "mix_nomusic")]:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video_enc.mp4", "-i", f"{ST}/{aud}.wav", "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", f"{a_k}k", "-ar", "48000",
             "-t", f"{total:.3f}", "-movflags", "+faststart", out])
        print(out, f"{os.path.getsize(out) / 1e6:.1f} MB", f"video {v_k} kbps")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "stems":
        stems()
    elif c == "mix":
        mix()
    elif c == "mux":
        mux(sys.argv[2], sys.argv[3])
