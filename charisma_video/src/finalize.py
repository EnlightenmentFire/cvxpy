# -*- coding: utf-8 -*-
"""After the score exists: arrange -> spec mix (calibrated) -> encode -> objective checks.
usage: python finalize.py <out_dir>
"""
import os, sys, json, subprocess, re
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def sh(cmd, **kw):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    return subprocess.run(cmd, check=True, **kw)

def rms_windows(x, sr, win=0.05):
    n = int(win * sr); k = len(x) // n
    x = x[:k * n].reshape(k, n)
    return np.sqrt(np.mean(x ** 2, axis=1) + 1e-12)

def music_gap(voice_path, duck_path):
    v, sr = sf.read(voice_path, dtype="float32")
    m, _ = sf.read(duck_path, dtype="float32")
    if v.ndim > 1: v = v.mean(1)
    if m.ndim > 1: m = m.mean(1)
    L = min(len(v), len(m)); v, m = v[:L], m[:L]
    rv, rm = rms_windows(v, sr), rms_windows(m, sr)
    voiced = 20 * np.log10(rv) > -35
    pauses = (20 * np.log10(rv) < -55)
    gap = 10 * np.log10(np.mean(rv[voiced] ** 2) / np.mean(rm[voiced] ** 2))
    pause_rel = 10 * np.log10(np.mean(rv[voiced] ** 2) / (np.mean(rm[pauses] ** 2) + 1e-12)) if pauses.any() else None
    # sudden jumps of the music while narration is on (50 ms windows, > 8 dB step)
    dm = np.diff(20 * np.log10(rm + 1e-9))
    jumps = int(np.sum((dm > 8) & voiced[1:] & voiced[:-1]))
    return float(gap), (float(pause_rel) if pause_rel is not None else None), jumps

def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    voice = os.path.join(HERE, "voice", "voice_track.wav")
    sfx = os.path.join(HERE, "out", "sfx.wav")
    music = os.path.join(out, "music_bed.wav")
    sh([PY, os.path.join(HERE, "music", "build_music.py"), "arrange", music])
    mix = os.path.join(out, "mix.wav")
    vol = 0.5
    report = {}
    for it in range(3):
        r = subprocess.run([PY, os.path.join(HERE, "final_mix.py"), voice, sfx, music, mix, f"{vol:.3f}"],
                           check=True, capture_output=True, text=True)
        info = json.loads(r.stdout.strip().splitlines()[-1])
        gap, pause_rel, jumps = music_gap(voice, os.path.splitext(mix)[0] + "_music_ducked.wav")
        print(f"iter {it}: vol={vol:.3f} music under voice = -{gap:.1f} dB, in pauses -{pause_rel:.1f} dB, jumps={jumps}, "
              f"I={info['output_I']} TP={info['output_TP']}", flush=True)
        report = dict(volume=vol, gap_db=round(gap, 1), pause_rel_db=round(pause_rel, 1) if pause_rel else None,
                      jumps=jumps, I=info["output_I"], TP=info["output_TP"], LRA=info["output_LRA"])
        if 15.5 <= gap <= 17.5:
            break
        vol *= 10 ** ((gap - 16.5) / 20)
    json.dump(report, open(os.path.join(out, "mix_report.json"), "w"), indent=1)
    # encode (2-pass, < 100 MB)
    final = os.path.join(out, "他走了以后_1080x1920.mp4")
    pic = os.path.join(HERE, "out", "render", "picture.mp4")
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pic]).strip())
    a_kbps = 160
    v_kbps = int(94.0 * 8e3 / dur - a_kbps)
    log = os.path.join(out, "x264pass")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_kbps}k",
        "-pass", "1", "-passlogfile", log, "-pix_fmt", "yuv420p", "-an", "-f", "mp4", "/dev/null"])
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", mix, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_kbps}k", "-pass", "2", "-passlogfile", log,
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30", "-c:a", "aac", "-b:a", f"{a_kbps}k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", final])
    size = os.path.getsize(final) / 1e6
    report.update(file=final, size_MB=round(size, 1), video_kbps=v_kbps, seconds=round(dur, 2))
    json.dump(report, open(os.path.join(out, "mix_report.json"), "w"), indent=1)
    print(json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
