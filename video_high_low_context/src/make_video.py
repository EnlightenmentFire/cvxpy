# -*- coding: utf-8 -*-
"""Render frames in parallel and encode with ffmpeg; mux with audio.

usage: python make_video.py durations.json audio.wav out.mp4 [t_start t_end] [--workers N]
"""
import os
import subprocess
import sys
import time
from multiprocessing import Process

FPS = 30


def worker(k, dur_path, f0, f1, path, crf, maxrate):
    import render
    tl, comp = render.make(dur_path)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-maxrate", maxrate, "-bufsize", "4M", "-pix_fmt", "yuv420p", "-g", "60", "-tune", "animation",
           "-threads", "1", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(f0, f1):
        im = comp.frame(fi / FPS)
        p.stdin.write(im.tobytes())
        if (fi - f0) % 300 == 0:
            print(f"[w{k}] {fi - f0}/{f1 - f0} frames, {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workers = 4
    for a in sys.argv[1:]:
        if a.startswith("--workers="):
            workers = int(a.split("=")[1])
    crf = int(os.environ.get("CRF", "21"))
    maxrate = os.environ.get("MAXRATE", "1500k")
    dur_path, audio, out = args[0], args[1], args[2]
    import render
    tl, _ = render.make(dur_path)
    t_start = float(args[3]) if len(args) > 3 else 0.0
    t_end = float(args[4]) if len(args) > 4 else tl["total"]
    F0, F1 = int(t_start * FPS), int(t_end * FPS)
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    step = (F1 - F0 + workers - 1) // workers
    procs, parts = [], []
    for k in range(workers):
        a, b = F0 + k * step, min(F1, F0 + (k + 1) * step)
        if a >= b:
            continue
        path = os.path.join(tmp, f"part{k}.mp4")
        parts.append(path)
        pr = Process(target=worker, args=(k, dur_path, a, b, path, crf, maxrate))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    vid = os.path.join(tmp, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid],
                   check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-ss", str(t_start), "-t", str(t_end - t_start),
                    "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    print("done", out, os.path.getsize(out) / 1e6, "MB")


if __name__ == "__main__":
    main()
