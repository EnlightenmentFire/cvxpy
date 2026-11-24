"""Mix stems and mux with the picture track into the final MP4 (H.264 + AAC, < 100 MB).

Music is a separate stem. Until the music spec (配乐规范.md) is applied, `--preview-music` lays the existing
cues per scene with simple voice-keyed ducking and labels the output as a PREVIEW.
usage: python final_mux.py <out.mp4> [--preview-music]
"""
import sys, os, json, subprocess
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mixlib import SR, load, place, envelope, rms_db, fit_music, limiter

WORK = "/tmp/claude-0/work"
CUE_FOR = {"s00": "america", "s01": "france", "s02": "america", "s03": "america", "s04": "america", "s05": "america",
           "s06": "america", "s07": "france", "s08": "dark", "s09": None, "s10": "ending"}


def preview_music(tl, n):
    mus = np.zeros((n, 2), np.float32)
    cache = {}
    for s in tl["scenes"]:
        cue = CUE_FOR.get(s["id"])
        if not cue:
            continue
        if cue not in cache:
            m = load(f"{WORK}/music/{cue}.wav", stereo=True)
            cache[cue] = m / (10 ** (rms_db(m.mean(1)[m.mean(1) != 0]) / 20)) * 10 ** (-24 / 20)
        d = s["end"] - s["start"] + 1.0
        seg = fit_music(cache[cue], d, 2.0, 2.5)
        place(mus, seg, s["start"] - 0.5)
    return mus


def mix(preview):
    tl = json.load(open(f"{WORK}/timeline.json"))
    voice = load(f"{WORK}/stems/voice.wav")
    fx = load(f"{WORK}/stems/sfx.wav")
    n = max(len(voice), len(fx))
    voice = np.pad(voice, (0, n - len(voice))); fx = np.pad(fx, (0, n - len(fx)))
    if preview:
        mus = preview_music(tl, n)
        env = envelope(voice)
        mus *= (10 ** (-10.0 * env / 20))[:, None]
    else:
        mus = load(f"{WORK}/stems/music.wav", stereo=True)
        mus = np.pad(mus, ((0, n - len(mus)), (0, 0)))
    out = mus + (voice + fx)[:, None]
    out = limiter(out)
    p = f"{WORK}/stems/mix.wav"
    sf.write(p, out, SR, subtype="FLOAT")
    return p, tl["total"]


def mux(out, preview):
    wav, total = mix(preview)
    norm = f"{WORK}/stems/mix_norm.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", norm], check=True)
    pic = f"{WORK}/video/picture.mp4"
    budget_bits = 94 * 1024 * 1024 * 8
    a_kbps = 128
    v_kbps = int(budget_bits / total / 1000 - a_kbps - 8)
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 2.2)}k",
              "-bufsize", f"{v_kbps * 4}k", "-pix_fmt", "yuv420p", "-r", "30", "-g", "300"]
    os.chdir(f"{WORK}/video")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic] + common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", norm] + common +
                   ["-pass", "2", "-c:a", "aac", "-b:a", f"{a_kbps}k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
    sz = os.path.getsize(out) / 1024 / 1024
    print(f"{out}: {sz:.1f} MB, video {v_kbps} kbps")


if __name__ == "__main__":
    mux(sys.argv[1], "--preview-music" in sys.argv)
