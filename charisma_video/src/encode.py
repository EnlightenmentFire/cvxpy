# -*- coding: utf-8 -*-
"""Final mix + encode. usage:
python encode.py <picture.mp4> <voice.wav> <sfx.wav> <music.wav|none> <out.mp4> [target_MB]
Voice ~ -18 dBFS RMS (already normalised per line). Music is expected to be already ducked under the voice.
"""
import sys, os, subprocess, json
import numpy as np, soundfile as sf
from audio import SR, undb, db, speech_rms

def main():
    pic, voice, sfx, music, out = sys.argv[1:6]
    target_mb = float(sys.argv[6]) if len(sys.argv) > 6 else 92.0
    v, _ = sf.read(voice, dtype="float32")
    s, _ = sf.read(sfx, dtype="float32")
    n = max(len(v), len(s))
    mix = np.zeros(n, np.float32)
    mix[:len(v)] += v
    mix[:len(s)] += s
    if music != "none":
        m, _ = sf.read(music, dtype="float32")
        if m.ndim > 1:
            m = m.mean(1)
        mix[:min(n, len(m))] += m[:n]
    peak = float(np.max(np.abs(mix)))
    if peak > undb(-1.0):
        # soft-knee limiter on peaks only
        thr = undb(-3.0)
        over = np.abs(mix) > thr
        mix[over] = np.sign(mix[over]) * (thr + (undb(-1.0) - thr) * np.tanh((np.abs(mix[over]) - thr) / (undb(-1.0) - thr)))
    wav = os.path.splitext(out)[0] + "_mix.wav"
    sf.write(wav, mix, SR)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pic]).strip())
    a_kbps = 160
    v_kbps = int(target_mb * 8e3 / dur - a_kbps)
    log = os.path.splitext(out)[0] + "_2pass"
    base = ["ffmpeg", "-y", "-loglevel", "error", "-i", pic]
    subprocess.run(base + ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_kbps}k", "-pass", "1", "-passlogfile", log,
                           "-pix_fmt", "yuv420p", "-an", "-f", "mp4", "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-b:v", f"{v_kbps}k", "-pass", "2", "-passlogfile", log,
                    "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30",
                    "-c:a", "aac", "-b:a", f"{a_kbps}k", "-ar", str(SR), "-movflags", "+faststart", "-shortest", out], check=True)
    size = os.path.getsize(out) / 1e6
    print(json.dumps(dict(out=out, seconds=round(dur, 1), video_kbps=v_kbps, size_MB=round(size, 1),
                          voice_rms_db=round(db(speech_rms(v)), 1))))

if __name__ == "__main__":
    main()
