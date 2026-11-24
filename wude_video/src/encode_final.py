"""Final H.264/AAC encode under 100 MB (two-pass, size-targeted), plus the 无配乐 version and a
short excerpt around the climax (轮盘翻面) for listening.

usage: encode_final.py <picture_master.mp4> <mix.wav> <mix_nomusic.wav> <out_dir> <climax_t>
"""
import json
import os
import subprocess
import sys

TARGET_MB = 94.0
AUDIO_KBPS = 128


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    pic, mix, nomusic, out, climax_t = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
    os.makedirs(out, exist_ok=True)
    T = dur(pic)
    audio_bits = AUDIO_KBPS * 1000 * T
    vbits = TARGET_MB * 1e6 * 8 * 0.985 - audio_bits
    vk = int(vbits / T / 1000)
    print(f"duration {T:.1f}s -> video {vk} kbps + audio {AUDIO_KBPS} kbps", flush=True)
    x264 = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 3)}k",
            "-bufsize", f"{int(vk * 6)}k", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
            "-r", "30", "-g", "60", "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=1,1"]
    passlog = os.path.join(out, "x264pass")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, *x264, "-pass", "1", "-passlogfile", passlog,
         "-an", "-f", "mp4", os.devnull])
    final = os.path.join(out, "五德终始_命理与正统01.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", mix, "-map", "0:v", "-map", "1:a", *x264,
         "-pass", "2", "-passlogfile", passlog, "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ar", "48000",
         "-movflags", "+faststart", "-shortest", final])
    # 无配乐: same video stream, voice + accents only
    nm = os.path.join(out, "五德终始_命理与正统01_无配乐.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", final, "-i", nomusic, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ar", "48000", "-movflags", "+faststart",
         "-shortest", nm])
    # climax excerpt (for 配乐规范 §五: listen to the climax on its own)
    ex = os.path.join(out, "高潮片段_轮盘翻面.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, climax_t - 12):.2f}", "-t", "40", "-i", final,
         "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", ex])
    for p in (final, nm, ex):
        print(os.path.basename(p), f"{os.path.getsize(p) / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
