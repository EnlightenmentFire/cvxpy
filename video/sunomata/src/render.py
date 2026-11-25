"""渲染：python render.py stills t1 t2 ...  → 预览图；python render.py video [N进程] → WORK/video.mp4（无声）。"""
import sys, os, json, subprocess, math, time
from multiprocessing import Process
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import scenes

WORK = "/tmp/claude-0/work"
XF = 0.35  # 交叉淡化
NOSUB = {"B05c", "E15", "F05", "G06"}


class Ctx:
    def __init__(self, t0, lines):
        self.t0 = t0
        self.L = {l["id"]: l for l in lines}
        self.ids = set(self.L)

    def s(self, i):
        return self.L[i]["start"] - self.t0 if i in self.L else 1e9

    def e(self, i):
        return self.L[i]["end"] - self.t0 if i in self.L else 1e9


def load():
    tl = json.load(open(f"{WORK}/timeline.json"))
    starts = {l["id"]: l["start"] for l in tl["lines"]}
    shots = []
    for k, (lid, fn) in enumerate(scenes.SHOTS):
        t0 = 0.0 if k == 0 else starts[lid] - 0.3
        shots.append([t0, None, fn, lid])
    for k in range(len(shots)):
        shots[k][1] = shots[k + 1][0] if k + 1 < len(shots) else tl["total"]
    # 每个镜头的句子
    order = [l["id"] for l in tl["lines"]]
    firsts = [s[3] for s in shots]
    ctxs = []
    for k, s in enumerate(shots):
        a = order.index(firsts[k]); b = order.index(firsts[k + 1]) if k + 1 < len(shots) else len(order)
        ctxs.append(Ctx(s[0], [l for l in tl["lines"] if l["id"] in order[a:b]]))
    return tl, shots, ctxs


def draw_subs(cv, tl, T):
    for s in tl["subs"]:
        if s["start"] - 0.05 <= T < s["end"] + 0.12 and s["id"] not in NOSUB:
            a = ramp(T, s["start"] - 0.05, 0.08) * (1 - ramp(T, s["end"] + 0.04, 0.08))
            txt = s["text"].rstrip("，。、；：")
            text(cv, txt, W / 2, 1575, "sans_b", 56, (255, 255, 255), a, "c", shadow=10, stroke=(9, (0, 0, 0)))
            break


def frame(surface, tl, shots, ctxs, T, fi):
    cv = surface.getCanvas()
    cv.clear(skia.Color4f(BG[0] / 255, BG[1] / 255, BG[2] / 255, 1))
    k = next(i for i, s in enumerate(shots) if s[0] <= T < s[1] or i == len(shots) - 1)
    t0, t1, fn, _ = shots[k]
    if k > 0 and T - t0 < XF:
        p0, p1, pfn, _ = shots[k - 1]
        pfn(cv, T - p0, p1 - p0, ctxs[k - 1])
        cv.saveLayerAlpha(None, int(255 * ease((T - t0) / XF)))
        cv.clear(skia.Color4f(BG[0] / 255, BG[1] / 255, BG[2] / 255, 1))
        fn(cv, T - t0, t1 - t0, ctxs[k])
        cv.restore()
    else:
        fn(cv, T - t0, t1 - t0, ctxs[k])
    vignette(cv, 0.6)
    ai_badge(cv)
    draw_subs(cv, tl, T)
    # 片尾淡出
    if T > tl["total"] - 1.2:
        cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), ease((T - tl["total"] + 1.2) / 1.2)))
    pass  # 不加胶片颗粒：码率留给画面


def stills(ts, out=f"{WORK}/stills"):
    os.makedirs(out, exist_ok=True)
    tl, shots, ctxs = load()
    surf = skia.Surface(W, H)
    for T in ts:
        frame(surf, tl, shots, ctxs, T, int(T * FPS))
        surf.makeImageSnapshot().save(f"{out}/t{T:07.2f}.jpg", skia.kJPEG, 88)
    print("ok", len(ts))


def chunk(i, a, b):
    tl, shots, ctxs = load()
    surf = skia.Surface(W, H)
    out = f"{WORK}/chunks/c{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
    t = time.time()
    for fi in range(a, b):
        frame(surf, tl, shots, ctxs, fi / FPS, fi)
        p.stdin.write(surf.makeImageSnapshot().tobytes())
        if (fi - a) % 500 == 0:
            print(f"chunk {i}: {fi - a}/{b - a} {time.time() - t:.0f}s", flush=True)
    p.stdin.close(); p.wait()


def video(nproc=4):
    tl, _, _ = load()
    nf = int(math.ceil(tl["total"] * FPS))
    os.makedirs(f"{WORK}/chunks", exist_ok=True)
    for f in os.listdir(f"{WORK}/chunks"):
        os.remove(f"{WORK}/chunks/{f}")
    bounds = [round(nf * i / nproc) for i in range(nproc + 1)]
    ps = [Process(target=chunk, args=(i, bounds[i], bounds[i + 1])) for i in range(nproc)]
    [p.start() for p in ps]; [p.join() for p in ps]
    with open(f"{WORK}/chunks/list.txt", "w") as f:
        for i in range(nproc):
            f.write(f"file 'c{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/chunks/list.txt", "-c", "copy", f"{WORK}/video.mp4"], check=True)
    print("video frames", nf)


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills([float(x) for x in sys.argv[2:]])
    else:
        video(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
