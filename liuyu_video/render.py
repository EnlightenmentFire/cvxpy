# -*- coding: utf-8 -*-
"""多进程渲染：python render.py META OUT.mp4 [t0 t1] [--audio A.wav] [--final]"""
import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Process

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FPS = 30
W, H = 1080, 1920


def worker(meta, f0, f1, path, crf):
    from timeline import Timeline
    from scenes import Film
    T = Timeline(meta)
    F = Film(T)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        surf = F.frame(fi / FPS, fi)
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("meta"); ap.add_argument("out")
    ap.add_argument("t0", nargs="?", type=float); ap.add_argument("t1", nargs="?", type=float)
    ap.add_argument("--audio"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--crf", type=int, default=14)
    ap.add_argument("--final", action="store_true", help="两遍码率编码，控制在 100MB 内")
    ap.add_argument("--vbit", default="1650k")
    a = ap.parse_args()
    from timeline import Timeline
    T = Timeline(a.meta)
    t0 = a.t0 or 0.0
    t1 = a.t1 or T.total
    F0, F1 = int(t0 * FPS), int(math.ceil(t1 * FPS))
    n = F1 - F0
    tmpd = a.out + ".parts"
    os.makedirs(tmpd, exist_ok=True)
    k = a.workers
    bounds = [F0 + n * i // k for i in range(k + 1)]
    t = time.time()
    procs = []
    for i in range(k):
        path = os.path.join(tmpd, f"p{i:02d}.mp4")
        pr = Process(target=worker, args=(a.meta, bounds[i], bounds[i + 1], path, a.crf))
        pr.start(); procs.append(pr)
    for pr in procs:
        pr.join()
    print(f"rendered {n} frames in {time.time()-t:.0f}s", flush=True)
    lst = os.path.join(tmpd, "list.txt")
    open(lst, "w").write("".join(f"file 'p{i:02d}.mp4'\n" for i in range(k)))
    joined = os.path.join(tmpd, "joined.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", joined], check=True)
    if a.final:
        common = ["-c:v", "libx264", "-preset", "slow", "-b:v", a.vbit, "-maxrate", "2600k", "-bufsize", "5200k",
                  "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1", "-g", "60", "-movflags", "+faststart"]
        log = os.path.join(tmpd, "x264")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", joined] + common +
                       ["-pass", "1", "-passlogfile", log, "-an", "-f", "mp4", os.devnull], check=True)
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", joined]
        if a.audio:
            cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "128k", "-ar", "48000"]
        cmd += common + ["-pass", "2", "-passlogfile", log, "-shortest", a.out]
        subprocess.run(cmd, check=True)
    else:
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", joined]
        if a.audio:
            cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest"]
        cmd += ["-c:v", "copy", "-movflags", "+faststart", a.out]
        subprocess.run(cmd, check=True)
    print(f"done {a.out} in {time.time()-t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
