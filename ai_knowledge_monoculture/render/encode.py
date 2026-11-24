"""Two-pass H.264 encode to a size budget (WeChat Channels: < 100 MB), 1080x1920 30 fps, AAC audio."""
import os
import subprocess
import sys


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout
    return float(out.strip())


def encode(video, audio, out, target_mb=92.0, abr=128, tmpdir=None):
    dur = duration(video)
    total_kbps = target_mb * 8 * 1024 * 1024 / 1000 / dur
    vb = int(total_kbps - abr - 8)
    tmpdir = tmpdir or os.path.dirname(out)
    log = os.path.join(tmpdir, "x264pass")
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-profile:v", "high", "-pix_fmt", "yuv420p",
              "-r", "30", "-g", "60", "-b:v", f"{vb}k", "-maxrate", f"{int(vb * 2.2)}k", "-bufsize", f"{int(vb * 4)}k",
              "-passlogfile", log]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video] + common + ["-pass", "1", "-an", "-f", "null",
                                                                                   "/dev/null"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a"] + common +
                   ["-pass", "2", "-c:a", "aac", "-b:a", f"{abr}k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                    out], check=True)
    return vb, os.path.getsize(out) / 1024 / 1024


def swap_audio(encoded, audio, out, abr=128):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", encoded, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", f"{abr}k", "-ar", "48000", "-shortest", "-movflags",
                    "+faststart", out], check=True)
    return os.path.getsize(out) / 1024 / 1024


if __name__ == "__main__":
    vb, mb = encode(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 92.0)
    print(f"video bitrate {vb} kbps -> {mb:.1f} MB")
