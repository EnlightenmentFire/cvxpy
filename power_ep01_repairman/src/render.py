"""Frame compositor + video renderer.

python render.py keyframes OUTDIR t1 t2 ...    -> PNGs at given global times
python render.py video OUT.mp4 [--from S --to E] -> raw frames piped to ffmpeg (no audio)
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
import skia

import scenes_a as A
from gfx import *
from timeline import build, load_durations, subtitles

try:
    import scenes_b as B
except Exception:  # pragma: no cover - during development
    B = None

SECTION_FN = {}


def register():
    SECTION_FN["cold"] = A.sc_cold
    SECTION_FN["intro"] = A.sc_intro
    SECTION_FN["s1"] = A.sc_s1
    if B is not None:
        for k in ("s2", "s3", "s4", "s5", "s6", "s7", "end"):
            fn = getattr(B, "sc_" + k, None)
            if fn:
                SECTION_FN[k] = fn


register()

ORDER = ["cold", "intro", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "end"]


def section_at(tl, t):
    for k in ORDER:
        a, b = tl["sections"][k]
        if a <= t < b:
            return k
    return "end"


def draw_scene(c, tl, sec, t, frame):
    fn = SECTION_FN.get(sec)
    if fn is None:
        draw_text(c, f"[{sec}]", 540, STAGE_CY, "sans", 40, INK3, 1, align="center")
        return
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(0, 300, W, 952))
    if sec not in ("cold",):
        # a very slow push-in over each section ("镜头缓推")
        a, b = tl["sections"][sec]
        z = 1.0 + 0.025 * ease(seg(t, a, b))
        c.translate(540, STAGE_CY)
        c.scale(z, z)
        c.translate(-540, -STAGE_CY)
    fn(c, A.Ctx(tl, t, frame))
    c.restore()


def chapter_card(c, crd, t):
    T = crd["end"] - crd["start"]
    lt = t - crd["start"]
    a = ease(seg(lt, 0, 0.4)) * (1 - ease(seg(lt, T - 0.4, T)))
    if a <= 0:
        return 0.0
    # paper sheet over the stage
    c.drawRect(skia.Rect.MakeXYWH(0, 300, W, 952), paint(PAPER, a))
    lay = c.saveLayerAlpha(None, int(255 * a))
    dy = (1 - ease_out(seg(lt, 0, 0.6))) * 30
    draw_text(c, crd["num"], 540, 690 + dy, "serif_heavy", 230, INK, 1, align="center")
    c.drawLine(380, 850 + dy, 700, 850 + dy, paint(INK3, 1, stroke=2))
    draw_text(c, crd["title"], 540, 925 + dy, "serif_heavy", 66, INK, 1, align="center")
    c.restore()
    return a


def chrome(c, tl, t):
    """Persistent page furniture: series tag + thin rules framing the stage."""
    title_card = [k for k in tl["cards"] if k["sec"] == "title"][0]
    hide = 1.0 - (ease(seg(t, title_card["start"] - 0.3, title_card["start"])) *
                  (1 - ease(seg(t, title_card["end"] - 0.3, title_card["end"]))))
    a = hide * ease(seg(t, 0.2, 1.2))
    if a > 0:
        draw_text(c, "组织里的权力 · 第一期《维修工》", 540, 272, "serif_semi", 28, INK3, a, align="center", spacing=2)
    c.drawLine(70, 304, 1010, 304, paint(INK4, 0.9, stroke=1.6))
    c.drawLine(70, 1250, 1010, 1250, paint(INK4, 0.9, stroke=1.6))


def draw_subs(c, subs, t, suppress=()):
    for s in subs:
        if s["start"] - 0.05 <= t < s["end"]:
            if s["id"] in suppress:
                return
            a = ease(seg(t, s["start"] - 0.05, s["start"] + 0.12)) * (1 - ease(seg(t, s["end"] - 0.1, s["end"])))
            lines = s["lines"]
            if s["lang"] == "Chinese":
                size = 54
                n = len(lines)
                y0 = 1360 - (n - 1) * size * 0.68
                for k, ln in enumerate(lines):
                    draw_text(c, ln, 540, y0 + k * size * 1.36, "serif_bold", size, INK, a, align="center")
            else:
                # English/French quote: italic serif, wrapped
                from textwrap import wrap
                txt = lines[0]
                ww = wrap(txt, 34)
                size = 44
                y0 = 1360 - (len(ww) - 1) * size * 0.62
                for k, ln in enumerate(ww):
                    draw_text(c, ln, 540, y0 + k * size * 1.24, "garamond_it", size, INK, a, align="center")
            return


SUPPRESS_SUBS = ("e01", "e02", "e03")


def render_frame(tl, subs, t, frame=0):
    s = new_surface()
    c = s.getCanvas()
    draw_paper(c)
    sec = section_at(tl, t)
    # chapter cards: the scene under the card is the previous one while fading in
    crd = None
    for k in tl["cards"]:
        if k["start"] <= t < k["end"]:
            crd = k
    if crd is not None and crd["sec"] != "title":
        mid = (crd["start"] + crd["end"]) / 2
        if t < mid:
            prev = ORDER[max(0, ORDER.index(crd["sec"]) - 1)]
            draw_scene(c, tl, prev, min(t, tl["sections"][prev][1] - 1e-3), frame)
        else:
            draw_scene(c, tl, crd["sec"], t, frame)
        chapter_card(c, crd, t)
    elif crd is not None and crd["sec"] == "title":
        T = crd["end"] - crd["start"]
        lt = t - crd["start"]
        if lt < 0.5:
            draw_scene(c, tl, "cold", min(t, tl["sections"]["cold"][1] - 1e-3), frame)
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint(PAPER, ease(seg(lt, 0, 0.5))))
        elif lt > T - 0.5:
            draw_scene(c, tl, "intro", t, frame)
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint(PAPER, 1 - ease(seg(lt, T - 0.5, T))))
        else:
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint(PAPER, 1))
        A.sc_title(c, lt, T)
    else:
        draw_scene(c, tl, sec, t, frame)
    chrome(c, tl, t)
    draw_subs(c, subs, t, SUPPRESS_SUBS)
    apply_overlay(c)
    return s


def to_rgb(surface):
    return surface.makeImageSnapshot().toarray()[..., :3]


def get_timeline(dur_path=None):
    durs = load_durations(dur_path or os.environ.get("EP_DURATIONS", ""))
    tl = build(durs)
    return tl, subtitles(tl)


def main():
    mode = sys.argv[1]
    tl, subs = get_timeline()
    if mode == "keyframes":
        from PIL import Image
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        for spec in sys.argv[3:]:
            if "@" in spec:  # lineid@fraction
                lid, f = spec.split("@")
                s0, e0 = tl["lines"][lid]
                t = s0 + (e0 - s0) * float(f)
            else:
                t = float(spec)
            img = to_rgb(render_frame(tl, subs, t, int(t * FPS)))
            fn = os.path.join(out, f"kf_{spec.replace('@', '_')}.png")
            Image.fromarray(img).save(fn)
            print(fn, round(t, 2))
    elif mode == "info":
        print(json.dumps({k: [round(v[0], 2), round(v[1], 2)] for k, v in tl["sections"].items()}, indent=1))
        print("total", tl["total"])
    elif mode == "segment":
        # render frames [n0, n1) to an intermediate high-quality file
        out, n0, n1 = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
               "-pix_fmt", "yuv420p", "-threads", "1", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for n in range(n0, n1):
            img = to_rgb(render_frame(tl, subs, n / FPS, n))
            p.stdin.write(np.ascontiguousarray(img).tobytes())
        p.stdin.close()
        p.wait()
    elif mode == "video":
        # parallel render: python render.py video OUT.mp4 [t0 t1] [--jobs N]
        import tempfile
        import time
        out = sys.argv[2]
        args = [a for a in sys.argv[3:] if not a.startswith("--")]
        jobs = 4
        for a in sys.argv[3:]:
            if a.startswith("--jobs="):
                jobs = int(a.split("=")[1])
        t0 = float(args[0]) if len(args) > 0 else 0.0
        t1 = float(args[1]) if len(args) > 1 else tl["total"]
        n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
        tmpd = tempfile.mkdtemp(prefix="seg_", dir=os.path.dirname(os.path.abspath(out)))
        bounds = np.linspace(n0, n1, jobs + 1).astype(int)
        procs = []
        st = time.time()
        for k in range(jobs):
            segf = os.path.join(tmpd, f"seg{k:02d}.mp4")
            procs.append((segf, subprocess.Popen([sys.executable, os.path.abspath(__file__), "segment", segf,
                                                  str(bounds[k]), str(bounds[k + 1])], env=os.environ.copy())))
        for segf, p in procs:
            p.wait()
            if p.returncode != 0:
                raise SystemExit(f"segment failed: {segf}")
        lst = os.path.join(tmpd, "list.txt")
        with open(lst, "w") as f:
            for segf, _ in procs:
                f.write(f"file '{segf}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                       check=True)
        print(f"rendered {n1 - n0} frames in {time.time() - st:.0f}s -> {out}")


if __name__ == "__main__":
    main()
