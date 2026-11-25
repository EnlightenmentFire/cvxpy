# -*- coding: utf-8 -*-
"""拼接无声视频段 -> 两遍 x264 编码到 <100MB（恒定 25fps）-> 混入成片音频（aresample=async=1）；
无配乐版直接复用视频流。最后 ffprobe 核对音视频时长差。"""
import os, subprocess, json, glob, sys

R = "/tmp/claude-0/w74/render"
A = "/tmp/claude-0/w74/audio"
D = "/tmp/claude-0/w74/deliver"
NAME = "74_曹操收编青州兵"


def run(cmd):
    print(" ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


def dur(p, sel):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "stream=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True).stdout.strip()
    return float(r.split()[0])


def main():
    segs = sorted(glob.glob(f"{R}/seg_*.mp4"))
    with open(f"{R}/segs.txt", "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{R}/segs.txt", "-c", "copy", f"{R}/silent_hq.mp4"])
    vd = dur(f"{R}/silent_hq.mp4", "v:0")
    ad = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{A}/mix_music.wav"],
                              capture_output=True, text=True).stdout)
    T = min(vd, ad)
    budget_bits = 96.0e6 * 8
    vbr = int((budget_bits / T - 128000) * 0.97)
    print(f"video {vd:.2f}s audio {ad:.2f}s -> v bitrate {vbr/1000:.0f} kbps")
    os.makedirs(D, exist_ok=True)
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", str(vbr), "-maxrate", str(int(vbr * 2.2)), "-bufsize", str(int(vbr * 4)),
              "-pix_fmt", "yuv420p", "-r", "25", "-fps_mode", "cfr", "-g", "50", "-profile:v", "high", "-tune", "animation"]
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{R}/silent_hq.mp4", "-t", f"{T:.3f}"] + common + ["-pass", "1", "-passlogfile", f"{R}/x264", "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{R}/silent_hq.mp4", "-t", f"{T:.3f}"] + common + ["-pass", "2", "-passlogfile", f"{R}/x264", "-an", f"{R}/video_final.mp4"])
    for tag, wav, out in [("music", f"{A}/mix_music.wav", f"{D}/{NAME}.mp4"), ("nomusic", f"{A}/mix_nomusic.wav", f"{D}/{NAME}_无配乐版.mp4")]:
        run(["ffmpeg", "-v", "error", "-y", "-i", f"{R}/video_final.mp4", "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-t", f"{T:.3f}", "-movflags", "+faststart", out])
        v, a = dur(out, "v:0"), dur(out, "a:0")
        sz = os.path.getsize(out) / 1e6
        print(f"{tag}: video {v:.3f}s audio {a:.3f}s diff {abs(v - a):.3f}s size {sz:.1f} MB")


if __name__ == "__main__":
    main()
