# -*- coding: utf-8 -*-
"""Render the silent picture track in parallel chunks.
usage: python render.py <out_dir> [n_workers] [fps]
"""
import os, sys, json, subprocess, time, math
from multiprocessing import Process

HERE = os.path.dirname(os.path.abspath(__file__))

def worker(idx, f0, f1, fps, out_path):
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from engine import new_surface, W, H
    import skia
    from director import Director
    d = Director(os.path.join(HERE, "timeline.json"))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "12",
           "-pix_fmt", "yuv420p", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = new_surface()
    t0 = time.time()
    for f in range(f0, f1):
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        d.frame(c, f / fps)
        p.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        if (f - f0) % 300 == 0:
            el = time.time() - t0
            print(f"[w{idx}] {f - f0}/{f1 - f0} frames, {el:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print(f"[w{idx}] done in {time.time() - t0:.0f}s", flush=True)

if __name__ == "__main__":
    out = sys.argv[1]
    nw = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    os.makedirs(out, exist_ok=True)
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    nf = int(math.ceil(tl["total"] * fps))
    per = int(math.ceil(nf / nw))
    procs = []
    parts = []
    for i in range(nw):
        a, b = i * per, min(nf, (i + 1) * per)
        if a >= b:
            break
        path = os.path.join(out, f"part{i}.mp4")
        parts.append(path)
        pr = Process(target=worker, args=(i, a, b, fps, path)); pr.start(); procs.append(pr)
    for pr in procs:
        pr.join()
    with open(os.path.join(out, "parts.txt"), "w") as fh:
        for pth in parts:
            fh.write(f"file '{pth}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(out, "parts.txt"),
                    "-c", "copy", os.path.join(out, "picture.mp4")], check=True)
    print("frames", nf, "->", os.path.join(out, "picture.mp4"))
