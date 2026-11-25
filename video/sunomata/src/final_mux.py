"""成片：画面 + 混音，aresample=async=1，两遍 x264 控制在 100 MB 内；核对音视频流时长差。
python final_mux.py <video.mp4> <audio.wav> <out.mp4> [视频码率k]
"""
import sys, subprocess, json, os
v, a, out = sys.argv[1:4]
kb = int(sys.argv[4]) if len(sys.argv) > 4 else 900
d = os.path.dirname(out) or "."
common = ["-i", v, "-i", a, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium", "-b:v", f"{kb}k",
          "-maxrate", f"{int(kb*2.2)}k", "-bufsize", f"{kb*4}k", "-pix_fmt", "yuv420p", "-r", "25", "-g", "50"]
plog = f"/tmp/claude-0/work/x264pass"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + common + ["-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", "/dev/null"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + common + ["-pass", "2", "-passlogfile", plog, "-af", "aresample=async=1",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", out], capture_output=True, text=True).stdout)
durs = {s["codec_type"]: float(s["duration"]) for s in pr["streams"]}
print(out, f"{os.path.getsize(out)/1e6:.1f} MB", durs, "diff", round(abs(durs["video"] - durs["audio"]), 3))
