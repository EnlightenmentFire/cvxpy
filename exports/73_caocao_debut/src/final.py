# -*- coding: utf-8 -*-
"""Concat rendered segments, 2-pass encode under 100 MB, mux both audio versions, verify A/V durations."""
import subprocess, json, glob, math, os, sys
sys.path.insert(0, "/tmp/claude-0/w73/proj")
import timeline
from gfx import FPS

OUT = "/tmp/claude-0/w73/out"; DEL = "/tmp/claude-0/w73/deliver"
NAME = "73_曹操被一句评语定了一生"
TL = timeline.build()
nf = int(math.ceil(TL["total"] * FPS)); dur = nf / FPS


def run(c):
    print(" ".join(c[:6]), "...", flush=True); subprocess.run(c, check=True)


segs = sorted(glob.glob(f"{OUT}/seg_*.mp4"))
open(f"{OUT}/concat.txt", "w").write("".join(f"file '{s}'\n" for s in segs))
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/concat.txt", "-c", "copy", f"{OUT}/video_raw.mp4"])

target_mb = 94.0
vkbps = int(target_mb * 8 * 1024 / dur - 128 - 8)
vkbps = min(vkbps, 1800)
common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{vkbps}k", "-maxrate", f"{int(vkbps*2)}k", "-bufsize", f"{int(vkbps*4)}k",
          "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 4), "-profile:v", "high", "-tune", "animation"]
os.chdir(OUT)
run(["ffmpeg", "-v", "error", "-y", "-i", "video_raw.mp4", "-t", f"{dur:.3f}", *common, "-pass", "1", "-an", "-f", "mp4", "/dev/null"])
run(["ffmpeg", "-v", "error", "-y", "-i", "video_raw.mp4", "-t", f"{dur:.3f}", *common, "-pass", "2", "-an", "video_enc.mp4"])

os.makedirs(DEL, exist_ok=True)
for wav, suffix in (("mix_music.wav", ""), ("mix_nomusic.wav", "_无配乐")):
    out = f"{DEL}/{NAME}{suffix}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", "video_enc.mp4", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-af", f"aresample=async=1,apad,atrim=0:{dur:.3f}", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
         "-movflags", "+faststart", "-t", f"{dur:.3f}", out])
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", out], capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    print(f"{os.path.basename(out)}: {int(pr['format']['size'])/1e6:.1f} MB, {v['width']}x{v['height']} {v['r_frame_rate']} "
          f"v={float(v['duration']):.3f}s a={float(a['duration']):.3f}s diff={abs(float(v['duration'])-float(a['duration'])):.3f}s")
