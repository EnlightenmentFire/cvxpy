"""混音：旁白（逐句按时间线摆放）+ 音效 + 原创配乐（侧链压低），两遍 loudnorm 到 −15 LUFS / −1.5 dBTP。
同时导出无配乐版。输出 48 kHz 立体声 wav，并写 timeline.json / narration.srt / sentences.json。
usage: python mix.py <outdir>"""
import os, sys, json, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timeline, music, sfx

SR = 48000
W = os.environ.get("WORK", "/tmp/claude-0/work")

def srt_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"

def loudnorm(inp, out, target=-15.0, tp=-1.5):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", inp, "-af", f"loudnorm=I={target}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", inp, "-af", af + ",aresample=48000", "-c:a", "pcm_s24le", out], check=True)

def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = r[r.rindex("Summary:"):]
    I = float(tail.split("I:")[1].split("LUFS")[0]); P = float(tail.split("Peak:")[1].split("dBFS")[0])
    return I, P

def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    lines, scenes, total = timeline.build()
    if os.environ.get("MAXDUR"):
        total = min(total, float(os.environ["MAXDUR"]))
        lines = [l for l in lines if l["end"] <= total]
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for ln in lines:
        p = f"{timeline.PROC}/{ln['id']}.wav"
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p)
        i = int(ln["start"] * SR); voice[i:i + len(x)] += x[: n - i]
    V = np.stack([voice, voice], 1)
    # sfx
    S = np.zeros((n, 2), np.float32)
    sfx.place(S, sfx.hook_sound(), 0.0)
    secs = {}
    for s in scenes:
        k = s["lines"][0]["id"][0]
        if k not in secs:
            secs[k] = s["t0"]
    for k, t0 in secs.items():
        if k != "a":
            sfx.place(S, sfx.whoosh(1.6, 0.10), max(0, t0 - 1.0))
            sfx.place(S, sfx.pulse(0.22), t0 + 0.05)
    # key-line pulses (big conclusions)
    for lid in ("a12", "c11", "d13", "f14", "g14", "h02"):
        ln = [l for l in lines if l["id"] == lid]
        if not ln:
            continue
        ln = ln[0]
        sfx.place(S, sfx.pulse(0.16), ln["start"])
    # music
    M = music.build(n / SR, secs)[:n]
    # sidechain: envelope of voice (attack 30 ms, release 600 ms)
    env = np.abs(voice)
    env = sosfilt(butter(1, 8, "low", fs=SR, output="sos"), env)
    a = np.clip(env / (env.max() * 0.25 + 1e-9), 0, 1)
    # smooth with asymmetric follower (vectorised via downsampled loop)
    hop = 480; d = a[::hop]; g = np.zeros_like(d); cur = 0.0
    for i, v in enumerate(d):
        cur = cur + (v - cur) * (0.6 if v > cur else 0.08)
        g[i] = cur
    g = np.repeat(g, hop)[:n]
    duck_db = -4.0 * np.clip(g * 1.5, 0, 1)
    M *= (10 ** (duck_db / 20))[:, None]
    # set music level: measure voice & music loudness (speech-gated) and place music ≈ 21 dB under the voice
    def rms_db(x, mask=None):
        x = x if x.ndim == 1 else x.mean(1)
        if mask is not None: x = x[mask]
        return 10 * np.log10((x ** 2).mean() + 1e-12)
    sp = g > 0.3
    v_db = rms_db(voice, sp); m_db = rms_db(M, sp)
    M *= 10 ** ((v_db - 21.0 - m_db) / 20)
    print(f"voice {v_db:.1f} dB, music under speech set to {v_db - 21:.1f} dB (−21 dB rel.)")
    # loudness of sfx: hook sound is allowed to be loud during the first 0.25 s, then ducks with music
    S *= 10 ** ((v_db - 6 - rms_db(S[: int(0.3 * SR)])) / 20)
    mixd = V + M + S
    nomus = V + S
    tmp1, tmp2 = f"{W}/mix_raw.wav", f"{W}/nomus_raw.wav"
    sf.write(tmp1, mixd.astype(np.float32), SR, subtype="FLOAT"); sf.write(tmp2, nomus.astype(np.float32), SR, subtype="FLOAT")
    loudnorm(tmp1, f"{outdir}/mix.wav"); loudnorm(tmp2, f"{outdir}/mix_nomusic.wav")
    sf.write(f"{outdir}/narration_only.wav", voice, SR, subtype="PCM_24")
    sf.write(f"{outdir}/music_only.wav", M.astype(np.float32), SR, subtype="FLOAT")
    for p in ("mix.wav", "mix_nomusic.wav"):
        print(p, "LUFS/peak", lufs(f"{outdir}/{p}"))
    # timeline / srt / sentences
    json.dump([dict(id=l["id"], start=round(l["start"], 3), end=round(l["end"], 3), text=l["say"], sub=l["sub"], scene=l["scene"]) for l in lines],
              open(f"{outdir}/timeline.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{outdir}/narration.srt", "w") as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i}\n{srt_time(l['start'])} --> {srt_time(l['end'])}\n{l['sub']}\n\n")
    print("total", round(total, 2))

if __name__ == "__main__":
    main(sys.argv[1])
