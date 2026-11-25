# -*- coding: utf-8 -*-
"""Render the picture track in parallel chunks (constant 25 fps), then concatenate.
usage: python render.py [nproc] [t0 t1]   -> /tmp/claude-0/work/render/video.mp4
"""
import sys, os, json, subprocess, time
import numpy as np
from multiprocessing import Process

WORK = "/tmp/claude-0/work"
OUT = f"{WORK}/render"
FPS = 25


def worker(k, f0, f1):
    import cv2
    cv2.setNumThreads(1)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from film import Film
    from engine import to_u8, W, H
    film = Film()
    path = f"{OUT}/chunk_{k:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "13",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), path], stdin=subprocess.PIPE)
    t_start = time.time()
    for f in range(f0, f1):
        img = film.frame(f / FPS)
        p.stdin.write(to_u8(img).tobytes())
        if (f - f0) % 250 == 0:
            el = time.time() - t_start
            print(f"[{k}] {f - f0}/{f1 - f0} frames, {el:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print(f"[{k}] done {time.time() - t_start:.0f}s", flush=True)


def main():
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    tl = json.load(open(f"{WORK}/timeline.json"))
    if len(sys.argv) > 3:
        F0, F1 = int(float(sys.argv[2]) * FPS), int(float(sys.argv[3]) * FPS)
    else:
        F0, F1 = 0, int(np.ceil(tl["total"] * FPS))
    os.makedirs(OUT, exist_ok=True)
    # cost-balanced split: rain-window frames are ~4x the cost of the others
    sc = tl["scenes"]
    heavy = {"s01_hook", "s02_headline", "s03_thesis", "s20_yinzhao", "s21_end"}
    cost = np.ones(F1 - F0)
    for s in sc:
        if s["id"] in heavy:
            a, b = int(s["start"] * FPS) - F0, int(s["end"] * FPS) - F0
            cost[max(0, a):max(0, b)] = 4.0
    cum = np.cumsum(cost)
    cuts = [F0] + [F0 + int(np.searchsorted(cum, cum[-1] * i / nproc)) for i in range(1, nproc)] + [F1]
    only = [int(x) for x in os.environ.get("ONLY", "").split(",") if x != ""]
    ps = [Process(target=worker, args=(k, cuts[k], cuts[k + 1])) for k in range(nproc) if not only or k in only]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    with open(f"{OUT}/list.txt", "w") as f:
        for k in range(nproc):
            f.write(f"file 'chunk_{k:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt",
                    "-c", "copy", f"{OUT}/video.mp4"], check=True)
    print("video ->", f"{OUT}/video.mp4")


if __name__ == "__main__":
    main()
