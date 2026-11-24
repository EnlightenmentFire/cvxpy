"""Frame loop: timeline -> cairo frames -> ffmpeg (parallel chunks) -> concat."""
import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Process

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import segments  # noqa: E402
import timeline  # noqa: E402
from engine import FPS, GREY, H, W, clamp, draw_subtitle, draw_text, ease_out, new_canvas, set_color  # noqa: E402

NO_SUB = {"c0_8", "c0_9", "c11_1", "c11_2", "c11_3"}
BAND_SEGS = {"plymouth", "federalist"}


class Frame:
    def __init__(self, segs):
        self.segs = segs
        self.evmap = timeline.ev_by_id(segs)
        self.cues = {s.key: segments.Cues(s, self.evmap) for s in segs}
        self.surf, self.ctx = new_canvas()

    def seg_at(self, t):
        for s in self.segs:
            if s.start <= t < s.end:
                return s
        return self.segs[-1]

    def draw(self, t):
        ctx = self.ctx
        s = self.seg_at(t)
        ctx.save()
        fn = segments.RENDERERS.get(s.key)
        if fn is None:
            set_color(ctx, "#05080F")
            ctx.paint()
            draw_text(ctx, s.title, W / 2, H / 2, "sans_bold", 60, GREY, 1, "mm")
        else:
            fn(ctx, t, self.cues[s.key])
        ctx.restore()
        # subtitles: exactly one chunk at a time (the latest one that has started)
        active = None
        for e in s.events:
            if e.id in NO_SUB:
                continue
            for (c0, c1, text) in e.chunks:
                if c0 - 0.05 <= t < c1 + 0.12 and (active is None or c0 > active[0]):
                    active = (c0, c1, text)
        if active:
            c0, c1, text = active
            a = clamp((t - c0 + 0.05) / 0.10) * (1 - clamp((t - c1) / 0.12))
            draw_subtitle(ctx, text, alpha=a, band=s.key in BAND_SEGS)
        # dip between segments
        d_in = 1 - clamp((t - s.start) / 0.35)
        d_out = clamp((t - (s.end - 0.25)) / 0.25) if s is not self.segs[-1] else 0
        k = max(d_in if s is not self.segs[0] else 0, d_out)
        if k > 0:
            ctx.set_source_rgba(0.01, 0.02, 0.04, ease_out(k))
            ctx.paint()
        self.surf.flush()
        return self.surf.get_data()


def worker(segs, f0, f1, out_path, crf):
    fr = Frame(segs)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-g", "60", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        p.stdin.write(fr.draw(f / FPS))
        if (f - f0) % 300 == 0:
            print(f"[{os.path.basename(out_path)}] {f - f0}/{f1 - f0} frames {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


def render(segs, total, out, workers=3, crf=14, tmp=None):
    nfr = int(round(total * FPS))
    tmp = tmp or os.path.splitext(out)[0] + "_parts"
    os.makedirs(tmp, exist_ok=True)
    bounds = [round(i * nfr / workers) for i in range(workers + 1)]
    procs, parts = [], []
    for i in range(workers):
        pth = os.path.join(tmp, f"part{i:02d}.mp4")
        parts.append(pth)
        pr = Process(target=worker, args=(segs, bounds[i], bounds[i + 1], pth, crf))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for pth in parts:
            fh.write(f"file '{os.path.abspath(pth)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--robot", default=None)
    ap.add_argument("--segs", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--still", type=float, nargs="*", help="write PNG frames at these times instead")
    a = ap.parse_args()
    segs, total = timeline.build(a.voice, a.robot, a.segs.split(",") if a.segs else None, allow_missing=True)
    print("timeline total", round(total, 2), "s")
    if a.still:
        from engine import save_png
        fr = Frame(segs)
        for tt in a.still:
            fr.draw(tt)
            save_png(fr.surf, f"{os.path.splitext(a.out)[0]}_{tt:06.2f}.png")
            print("still", tt)
    else:
        render(segs, total, a.out, a.workers)
        print("video", a.out)
