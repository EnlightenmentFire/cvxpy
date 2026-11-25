# -*- coding: utf-8 -*-
"""渲染全部帧为 PNG（多进程）。用法: python render_frames.py timeline.json outdir nproc [t_from t_to]"""
import json, os, sys, time
from multiprocessing import Process
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
FPS = 30


def work(k, n, tl, out, f0, f1):
    import scene
    S = scene.Scene(json.load(open(tl)))
    for i in range(f0, f1):
        if i % n != k:
            continue
        img = S.render(i / FPS)
        Image.fromarray(img).save(f"{out}/f{i:05d}.png", compress_level=1)


if __name__ == "__main__":
    tl, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    T = json.load(open(tl))
    total = int(round(T["end"] * FPS))
    f0 = int(round(float(sys.argv[4]) * FPS)) if len(sys.argv) > 4 else 0
    f1 = min(total, int(round(float(sys.argv[5]) * FPS)) + 1) if len(sys.argv) > 5 else total
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    ps = [Process(target=work, args=(k, n, tl, out, f0, f1)) for k in range(n)]
    [p.start() for p in ps]
    [p.join() for p in ps]
    print(f"rendered frames {f0}..{f1 - 1} in {time.time() - t0:.0f}s")
