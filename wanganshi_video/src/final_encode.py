"""Mux + two-pass x264 to fit <100 MB; CFR 25 fps; aresample=async=1; also no-music version; A/V duration check.
usage: python final_encode.py <video_silent.mp4> <mix_music.wav> <mix_nomusic.wav> <out.mp4> <out_nomusic.mp4>"""
import sys, subprocess, json, os

vid, am, an, out, out2 = sys.argv[1:6]


def dur(p, stream):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration", "-of", "json", p],
                       capture_output=True, text=True).stdout
    return float(json.loads(r)["streams"][0]["duration"])


D = dur(vid, "v:0")
target_mb = float(os.environ.get("TARGET_MB", 94))
total_kbps = target_mb * 8 * 1024 * 1024 / 1000 / D
vk = int(total_kbps - 128 - 6)
print(f"video {D:.2f}s -> video bitrate {vk} kbps")
common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 2)}k", "-bufsize", f"{int(vk * 4)}k",
          "-pix_fmt", "yuv420p", "-r", "25", "-fps_mode", "cfr", "-g", "125", "-tune", "animation"]
pl = out + ".2pass"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid] + common + ["-pass", "1", "-passlogfile", pl, "-an", "-f", "mp4", "/dev/null"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", am, "-map", "0:v", "-map", "1:a"] + common +
               ["-pass", "2", "-passlogfile", pl, "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                "-shortest", "-movflags", "+faststart", out], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-i", an, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out2], check=True)
for p in (out, out2):
    v, a = dur(p, "v:0"), dur(p, "a:0")
    print(f"{os.path.basename(p)}: size {os.path.getsize(p) / 1e6:.1f} MB, video {v:.3f}s audio {a:.3f}s diff {abs(v - a):.3f}s")
for f in os.listdir(os.path.dirname(os.path.abspath(out))):
    if f.startswith(os.path.basename(pl)):
        os.remove(os.path.join(os.path.dirname(os.path.abspath(out)), f))
