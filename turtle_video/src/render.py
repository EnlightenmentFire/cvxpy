"""Render video frames (parallel) and mux with the mixed audio.

usage: python render.py LINES_DIR MIX_WAV OUT_MP4 [--t0 S] [--t1 S] [--workers N] [--crf N | --bitrate K]
"""
import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np
import soundfile as sf

from theme import W, H, FPS

_R = None


def _init(lines_dir):
    global _R
    from compose import build_timeline, Renderer
    durs = {}
    for f in os.listdir(lines_dir):
        if f.endswith(".wav") and not f.startswith("."):
            durs[f[:-4]] = sf.info(os.path.join(lines_dir, f)).duration
    items, lines, total = build_timeline(durs)
    _R = Renderer(items, lines, total)


def _frame(i):
    return _R.frame_bgra(i / FPS, i).tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines_dir")
    ap.add_argument("mix_wav")
    ap.add_argument("out_mp4")
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=None)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--crf", type=int, default=None)
    ap.add_argument("--bitrate", type=int, default=None, help="video kbit/s (2-pass)")
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--abitrate", default="128k")
    a = ap.parse_args()
    dur_audio = sf.info(a.mix_wav).duration
    t1 = a.t1 if a.t1 is not None else dur_audio
    f0, f1 = int(round(a.t0 * FPS)), int(round(t1 * FPS))
    nfr = f1 - f0
    base = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    venc = ["-c:v", "libx264", "-preset", a.preset, "-profile:v", "high", "-pix_fmt", "yuv420p", "-g", "60",
            "-movflags", "+faststart", "-tune", "animation"]
    tmpv = a.out_mp4 + ".video.mp4"
    if a.bitrate:
        # pass 1 renders to a near-lossless intermediate; passes 2/3 encode to the size budget
        inter = a.out_mp4 + ".inter.mkv"
        cmd = base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "8", "-pix_fmt", "yuv420p", inter]
    else:
        cmd = base + venc + ["-crf", str(a.crf or 20), tmpv]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    with Pool(a.workers, initializer=_init, initargs=(a.lines_dir,)) as pool:
        for k, buf in enumerate(pool.imap(_frame, range(f0, f1), chunksize=6)):
            p.stdin.write(buf)
            if k % 300 == 0:
                el = time.time() - t_start
                print(f"frame {k}/{nfr}  {el:.0f}s  ({(k + 1) / max(el, 1e-3):.1f} fps)", flush=True)
    p.stdin.close()
    p.wait()
    if a.bitrate:
        logp = a.out_mp4 + ".2pass"
        common = ["ffmpeg", "-y", "-loglevel", "error", "-i", inter] + venc + ["-b:v", f"{a.bitrate}k",
                                                                             "-maxrate", f"{int(a.bitrate * 2.2)}k", "-bufsize", f"{a.bitrate * 4}k",
                                                                             "-passlogfile", logp]
        subprocess.run(common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(common + ["-pass", "2", tmpv], check=True)
        os.remove(inter)
    # mux audio (AAC 160k)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-ss", f"{a.t0:.3f}", "-t", f"{t1 - a.t0:.3f}", "-i", a.mix_wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", a.abitrate, "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", a.out_mp4], check=True)
    os.remove(tmpv)
    print(f"done {a.out_mp4} in {time.time() - t_start:.0f}s")


if __name__ == "__main__":
    main()
