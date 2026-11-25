# -*- coding: utf-8 -*-
"""成片：out/video.mp4（无声）+ audio/mix_*.wav -> 两个版本 mp4（有配乐 / 无配乐）。
视频：若 CRF 20 超过 95 MB，则两遍编码到 ~92 MB。音频 AAC 128k，aresample=async=1，恒定 25 fps。
核对：ffprobe 音视频流时长差 ≤ 0.1 s。"""
import json, os, subprocess, sys

WK = "/tmp/claude-0/work"
OUT = f"{WK}/out"
NAME = "太能共情的人为什么最容易累垮"


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,r_frame_rate,width,height,nb_frames",
                        "-show_entries", "format=duration,size", "-of", "json", p], capture_output=True, text=True)
    return json.loads(r.stdout)


def enc_video(src, dst):
    dur = float(probe(src)["format"]["duration"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "animation",
                    "-pix_fmt", "yuv420p", "-r", "25", "-g", "50", "-movflags", "+faststart", dst], check=True)
    mb = os.path.getsize(dst) / 1e6
    print(f"video crf20: {mb:.1f} MB")
    if mb > 95:
        kbps = int(92 * 8000 / dur - 130)
        for p in (1, 2):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k",
                            "-pass", str(p), "-passlogfile", f"{OUT}/x264pass", "-pix_fmt", "yuv420p", "-r", "25", "-g", "50"]
                           + (["-f", "mp4", "/dev/null"] if p == 1 else ["-movflags", "+faststart", dst]), check=True)
        print(f"video 2-pass {kbps}k: {os.path.getsize(dst) / 1e6:.1f} MB")


def mux(v, a, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                    "-shortest", "-movflags", "+faststart", dst], check=True)
    J = probe(dst)
    vs = [s for s in J["streams"] if s["codec_type"] == "video"][0]
    au = [s for s in J["streams"] if s["codec_type"] == "audio"][0]
    dv, da = float(vs["duration"]), float(au["duration"])
    print(f"{os.path.basename(dst)}: {vs['width']}x{vs['height']} {vs['r_frame_rate']} v={dv:.3f}s a={da:.3f}s diff={abs(dv - da):.3f}s "
          f"size={int(J['format']['size']) / 1e6:.1f} MB")
    assert abs(dv - da) <= 0.1, "A/V duration mismatch"


if __name__ == "__main__":
    venc = f"{OUT}/_video_enc.mp4"
    if "--skip-venc" not in sys.argv:
        enc_video(f"{OUT}/video.mp4", venc)
    mux(venc, f"{WK}/audio/mix_music.wav", f"{OUT}/{NAME}.mp4")
    mux(venc, f"{WK}/audio/mix_voice.wav", f"{OUT}/{NAME}_无配乐版.mp4")
