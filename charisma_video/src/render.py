# -*- coding: utf-8 -*-
"""Render the silent picture track in resumable 30-second chunks (each finished chunk is kept;
a restart only re-renders missing chunks).
usage: python render.py <out_dir> [n_workers] [fps]
"""
import os, sys, json, subprocess, time, math
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNK = 900  # frames (30 s)
_D = None

def _init():
    global _D
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    from director import Director
    _D = Director(os.path.join(HERE, "timeline.json"))

def render_chunk(args):
    idx, f0, f1, fps, out_dir = args
    import skia
    from engine import new_surface, W, H
    final = os.path.join(out_dir, f"chunk_{idx:04d}.mp4")
    if os.path.exists(final):
        return idx, "skip"
    tmp = final + ".part.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "12",
           "-pix_fmt", "yuv420p", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = new_surface()
    t0 = time.time()
    for f in range(f0, f1):
        c = surf.getCanvas()
        c.clear(skia.Color(0, 0, 0))
        _D.frame(c, f / fps)
        p.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on chunk {idx}")
    os.replace(tmp, final)
    return idx, f"{f1 - f0} frames in {time.time() - t0:.0f}s"

if __name__ == "__main__":
    out = sys.argv[1]
    nw = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    os.makedirs(out, exist_ok=True)
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    nf = int(math.ceil(tl["total"] * fps))
    jobs = [(i, a, min(nf, a + CHUNK), fps, out) for i, a in enumerate(range(0, nf, CHUNK))]
    with Pool(nw, initializer=_init) as pool:
        for idx, msg in pool.imap_unordered(render_chunk, jobs):
            print(f"chunk {idx}/{len(jobs) - 1}: {msg}", flush=True)
    with open(os.path.join(out, "chunks.txt"), "w") as fh:
        for i, *_ in jobs:
            fh.write(f"file '{os.path.join(out, f'chunk_{i:04d}.mp4')}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(out, "chunks.txt"),
                    "-c", "copy", os.path.join(out, "picture.mp4")], check=True)
    print("frames", nf, "->", os.path.join(out, "picture.mp4"), flush=True)
