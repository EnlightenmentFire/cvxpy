# -*- coding: utf-8 -*-
"""渲染入口。
  python render.py --stills 3.0,12.5 --out build/stills      # 出静帧
  python render.py --range 0 30 --out build/chunk.mp4        # 渲染片段（无声）
  python render.py --all --out build/video.mp4 [--jobs 4]    # 并行渲染全片（无声），再由 tools/mux.sh 合成
"""
import argparse, os, subprocess, sys, time, pathlib
import skia
from engine import *
import scenes_a as A
import scenes_b as B
try:
    import scenes_c as CC
except ImportError:
    CC = None

ROOT = pathlib.Path(__file__).resolve().parent
SCENES = [("s1", A.scene_s1), ("title", A.scene_title), ("s2", A.scene_s2)]
SCENES += [("s3", B.scene_s3), ("s4", B.scene_s4), ("s5", B.scene_s5)]
if CC:
    SCENES += [("s6", CC.scene_s6), ("s7", CC.scene_s7), ("s8", CC.scene_s8)]
SCENES += [("s9", A.scene_s9), ("s10", A.scene_s10)]


def draw_frame(surface, tl, frame, subs=True):
    t = frame / FPS
    c = surface.getCanvas()
    ctx = Ctx(tl, t)
    background(c, t)
    for sid, fn in SCENES:
        s0, s1 = tl.S(sid)
        if sid == "s10":
            s1 = tl.S("end")[1]
        if s0 - 0.05 <= t <= s1 + 0.05:
            c.save()
            fn(c, ctx)
            c.restore()
    finish(c, t, frame)
    if subs:
        subtitles(c, ctx)
    # 首尾淡入淡出
    k = min(ramp(t, 0, 0.6), 1 - ramp(t, tl.total - 0.7, tl.total - 0.05))
    if k < 1:
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int((1 - k) * 255))))


def render_range(tl, f0, f1, out, crf=17, preset="veryfast"):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = new_surface()
    t0 = time.time()
    for f in range(f0, f1):
        draw_frame(s, tl, f)
        p.stdin.write(s.makeImageSnapshot().tobytes())
        if (f - f0) % 300 == 0:
            print(f"[{f0}-{f1}] frame {f} {time.time()-t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills"); ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--all", action="store_true"); ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out", default="build/out"); ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--nosubs", action="store_true")
    a = ap.parse_args()
    tl = Timeline()
    if a.stills:
        os.makedirs(a.out, exist_ok=True)
        s = new_surface()
        for tok in a.stills.split(","):
            if ":" in tok:        # 行id:偏移秒  或  段id:偏移秒
                k, off = tok.split(":"); off = float(off)
                base = tl.lines[k]["start"] if k in tl.lines else tl.segs[k]["start"]
                t = base + off; name = f"{k}_{off:+.1f}"
            else:
                t = float(tok); name = f"t{t:07.2f}"
            draw_frame(s, tl, int(round(t * FPS)), subs=not a.nosubs)
            s.makeImageSnapshot().save(f"{a.out}/{name}.png", skia.kPNG)
            print("still", name, f"t={t:.2f}")
        return
    if a.range:
        return sys.exit(render_range(tl, int(a.range[0] * FPS), int(a.range[1] * FPS), a.out, a.crf))
    if a.all:
        n = int(round(tl.total * FPS))
        jobs = a.jobs
        per = (n + jobs - 1) // jobs
        procs, parts = [], []
        for j in range(jobs):
            f0, f1 = j * per, min(n, (j + 1) * per)
            part = f"{a.out}.part{j}.mp4"; parts.append(part)
            procs.append(subprocess.Popen([sys.executable, __file__, "--range", str(f0 / FPS), str(f1 / FPS), "--out", part, "--crf", str(a.crf)]))
        rc = [p.wait() for p in procs]
        assert not any(rc), rc
        lst = a.out + ".txt"
        open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", a.out])
        for p in parts + [lst]:
            os.remove(p)
        print("done", a.out)


if __name__ == "__main__":
    main()
