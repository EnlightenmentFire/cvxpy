"""Final encode: mux rendered video + mixed audio, two-pass H.264 sized under a byte budget.

python encode.py VIDEO_IN AUDIO_WAV OUT.mp4 [--max-mb 95]
"""
import json
import os
import subprocess
import sys


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main():
    vin, ain, out = sys.argv[1:4]
    max_mb = 95.0
    for a in sys.argv[4:]:
        if a.startswith("--max-mb="):
            max_mb = float(a.split("=")[1])
    dur = duration(vin)
    audio_k = 128
    total_k = max_mb * 8 * 1024 * 1024 / 1000 / dur          # kbit/s budget
    video_k = int(min(4000, (total_k - audio_k) * 0.97))
    for a in sys.argv[4:]:
        if a.startswith("--kbps="):
            video_k = int(a.split("=")[1])
    print(f"duration {dur:.1f}s -> video {video_k} kbps + audio {audio_k} kbps")
    logdir = os.path.dirname(os.path.abspath(out))
    passlog = os.path.join(logdir, "x264pass")
    common = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
              "-b:v", f"{video_k}k", "-maxrate", f"{int(video_k * 2.5)}k", "-bufsize", f"{int(video_k * 5)}k",
              "-tune", "animation", "-r", "30", "-g", "120", "-passlogfile", passlog]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vin, *common, "-pass", "1", "-an", "-f", "mp4", os.devnull],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vin, "-i", ain, *common, "-pass", "2",
                    "-c:a", "aac", "-b:a", f"{audio_k}k", "-ar", "48000", "-ac", "2", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    for f in os.listdir(logdir):
        if f.startswith("x264pass"):
            os.remove(os.path.join(logdir, f))
    mb = os.path.getsize(out) / 1024 / 1024
    print(f"wrote {out}: {mb:.1f} MB")


if __name__ == "__main__":
    main()
