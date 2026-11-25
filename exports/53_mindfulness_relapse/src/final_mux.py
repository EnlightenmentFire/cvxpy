# -*- coding: utf-8 -*-
"""Two-pass H.264 encode of the picture track to fit < 100 MB, then mux the two mixes (AAC 128k, aresample async).
Verifies stream durations (|video - audio| <= 0.1 s) with ffprobe.
usage: python final_mux.py <out_dir> <basename>
"""
import sys, os, json, subprocess

WORK = "/tmp/claude-0/work"
OUT, BASE = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
src = f"{WORK}/render/video.mp4"


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,r_frame_rate,nb_frames,width,height",
                        "-show_entries", "format=duration,size", "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout)


vdur = float(probe(src)["format"]["duration"])
budget_bytes = 96.0e6
abr = 128_000
vbr = int((budget_bytes * 8 / vdur - abr) * 0.97)
vbr = min(vbr, 2_600_000)
print(f"video {vdur:.2f}s -> target video bitrate {vbr / 1000:.0f} kb/s")
enc = f"{WORK}/render/video_enc.mp4"
common = ["-c:v", "libx264", "-preset", "slow", "-b:v", str(vbr), "-maxrate", str(int(vbr * 1.8)), "-bufsize", str(int(vbr * 3)),
          "-pix_fmt", "yuv420p", "-r", "25", "-g", "50", "-profile:v", "high", "-movflags", "+faststart"]
os.chdir(f"{WORK}/render")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, *common, "-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, *common, "-pass", "2", "-an", enc], check=True)

for tag, wav in [("", f"{WORK}/stems/mix_full.wav"), ("_无配乐", f"{WORK}/stems/mix_nomusic.wav")]:
    out = f"{OUT}/{BASE}{tag}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", enc, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", f"{vdur:.3f}",
                    "-movflags", "+faststart", out], check=True)
    p = probe(out)
    v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in p["streams"] if s["codec_type"] == "audio"][0]
    diff = abs(float(v["duration"]) - float(a["duration"]))
    size = int(p["format"]["size"])
    print(f"{os.path.basename(out)}: {v['width']}x{v['height']} {v['r_frame_rate']} video {float(v['duration']):.3f}s "
          f"audio {float(a['duration']):.3f}s diff {diff:.3f}s size {size / 1e6:.1f} MB")
    assert diff <= 0.1, "A/V duration mismatch"
    assert size < 100e6, "file too large"
