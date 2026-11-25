# -*- coding: utf-8 -*-
"""Encode deliverables and run QA.
usage: python final.py <frames.mp4> <outdir>
  -> <outdir>/<title>.mp4, <title>_无配乐版.mp4, qa.json
"""
import os, sys, json, subprocess, re
import numpy as np

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
TITLE = "为什么一走神，人就不快乐"
LIMIT_MB = 100


def run(a, **k):
    return subprocess.run(a, check=True, capture_output=True, text=True, **k)


def probe(p):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,r_frame_rate,width,height,nb_frames",
             "-show_entries", "format=duration,size", "-of", "json", p])
    return json.loads(r.stdout)


def encode(frames, audio, out, vkbps):
    common = ["-i", frames, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "slow",
              "-b:v", f"{vkbps}k", "-maxrate", f"{int(vkbps * 2.2)}k", "-bufsize", f"{int(vkbps * 4)}k",
              "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "25", "-g", "50",
              "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    log = f"{WORK}/x264pass"
    run(["ffmpeg", "-y", "-loglevel", "error"] + common + ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", "/dev/null"])
    run(["ffmpeg", "-y", "-loglevel", "error"] + common + ["-pass", "2", "-passlogfile", log,
         "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", out])


def loud(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))
    return I, tp


def main():
    frames, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    tl = json.load(open(f"{WORK}/timeline.json"))
    dur = tl["total"]
    vkbps = int((LIMIT_MB * 0.93 * 8e6 / dur - 128e3) / 1e3)
    vkbps = min(vkbps, 1400)
    qa = dict(duration_s=dur, video_kbps=vkbps)
    for name, audio in ((f"{TITLE}.mp4", f"{WORK}/mix_music.wav"), (f"{TITLE}_无配乐版.mp4", f"{WORK}/mix_nomusic.wav")):
        out = os.path.join(outdir, name)
        encode(frames, audio, out, vkbps)
        p = probe(out)
        st = {s["codec_type"]: s for s in p["streams"]}
        vd, ad = float(st["video"]["duration"]), float(st["audio"]["duration"])
        I, tp = loud(out)
        qa[name] = dict(size_mb=round(int(p["format"]["size"]) / 1e6, 1), video_s=vd, audio_s=ad,
                        av_diff_s=round(abs(vd - ad), 3), fps=st["video"]["r_frame_rate"],
                        res=f'{st["video"]["width"]}x{st["video"]["height"]}', lufs=I, true_peak_dbfs=tp)
        print(name, qa[name], flush=True)
    json.dump(qa, open(os.path.join(WORK, "qa_encode.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
