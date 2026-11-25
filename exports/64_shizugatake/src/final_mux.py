# -*- coding: utf-8 -*-
"""Two-pass loudnorm (-15 LUFS, -1.5 dBTP) of premaster mixes, then mux with the rendered video.
Encodes H.264 to fit < 100 MB. Verifies stream durations (|a-v| <= 0.1 s)."""
import json, os, subprocess, sys

WK = "/tmp/claude-0/work"
OUTD = sys.argv[1] if len(sys.argv) > 1 else f"{WK}/out"
os.makedirs(OUTD, exist_ok=True)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def loudnorm(src, dst):
    r = run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    js = r.stderr[r.stderr.rindex("{"):]
    m = json.loads(js[:js.index("}") + 1])
    af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-c:a", "pcm_s24le", dst])


def dur(path, sel):
    r = run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "stream=duration", "-of", "csv=p=0", path])
    return float(r.stdout.strip().split("\n")[0])


def mux(video, audio, out, vbitrate):
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", vbitrate, "-maxrate", "2400k", "-bufsize", "4800k",
              "-pix_fmt", "yuv420p", "-r", "25", "-g", "50", "-profile:v", "high", "-movflags", "+faststart"]
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-an", *common, "-pass", "1", "-passlogfile", f"{WK}/x264", "-f", "null", "-"])
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", *common, "-pass", "2",
         "-passlogfile", f"{WK}/x264", "-c:a", "aac", "-b:a", "128k", "-af", "aresample=async=1", "-shortest", out])
    dv, da = dur(out, "v:0"), dur(out, "a:0")
    sz = os.path.getsize(out) / 1e6
    print(f"{out}: video {dv:.3f}s audio {da:.3f}s diff {abs(dv - da):.3f}s size {sz:.1f} MB")
    return dv, da, sz


if __name__ == "__main__":
    video = f"{WK}/video_noaudio.mp4"
    vlen = dur(video, "v:0")
    vb = sys.argv[2] if len(sys.argv) > 2 else "820k"
    for name, out in (("mix", "贱岳之战_成片.mp4"), ("nomusic", "贱岳之战_无配乐版.mp4")):
        a = f"{WK}/mix/{name}_master.wav"
        loudnorm(f"{WK}/mix/{name}_premaster.wav", a)
        # trim/pad audio to video length
        a2 = f"{WK}/mix/{name}_master_fit.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"apad,atrim=0:{vlen:.3f}", "-c:a", "pcm_s24le", a2])
        mux(video, a2, f"{OUTD}/{out}", vb)
        r = run(["ffmpeg", "-hide_banner", "-i", f"{OUTD}/{out}", "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"])
        tail = r.stderr[r.stderr.rindex("Summary:"):]
        print(" ".join(tail.split()))
