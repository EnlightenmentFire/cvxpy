# -*- coding: utf-8 -*-
"""Timeline + frame compositor + parallel ffmpeg render.
usage:
  python render.py timeline                 # build timeline.json from processed voice (or estimates)
  python render.py stills t1 t2 ...         # write PNG stills at global times (seconds)
  python render.py video [workers]          # render picture.mp4 (25 fps)
"""
import os, sys, json, re, math, subprocess
import numpy as np
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
from frame import S, header_grad, draw_header, draw_badges, split_sub, sub_display, draw_subtitle
from script_data import SCENES, all_lines
import scenes as SC

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
FPS = 25
LINE_GAP = 0.50          # between sentences (VOICE_SPEC)
SCENE_GAP = 0.90         # extra breath between scenes
LEAD_IN = 0.35           # first word starts this early (hook: no black, no logo)
TAIL = 3.5


def voice_dur(lid, say):
    p = f"{WORK}/tts/proc/{lid}.wav"
    if os.path.exists(p):
        import soundfile as sf
        info = sf.info(p)
        return info.frames / info.samplerate
    n = len(re.sub(r"[，。？！：；、“”《》\s]", "", say))
    return n * 0.215 + 0.2


def build_timeline():
    t = LEAD_IN
    out = []
    lines = all_lines()
    for si, sc in enumerate(SCENES):
        sl = [d for d in lines if d["scene"] == sc["id"]]
        if si > 0:
            t += SCENE_GAP
        s0 = t - (LEAD_IN if si == 0 else SCENE_GAP / 2)
        ls = []
        for i, d in enumerate(sl):
            if i > 0:
                t += LINE_GAP
            dur = voice_dur(d["id"], d["say"])
            ls.append(dict(id=d["id"], cue=d["cue"], say=d["say"], sub=d["sub"], start=round(t, 3), end=round(t + dur, 3)))
            t += dur
        out.append(dict(id=sc["id"], start=round(max(s0, 0), 3), lines=ls))
    for i in range(len(out)):
        out[i]["end"] = out[i + 1]["start"] if i + 1 < len(out) else round(t + TAIL, 3)
    total = out[-1]["end"]
    tl = dict(total=total, fps=FPS, scenes=out)
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), ensure_ascii=False, indent=1)
    return tl


def load_timeline():
    return json.load(open(f"{WORK}/timeline.json"))


SCMAP = {s["id"]: s for s in SCENES}


class Comp:
    def __init__(self, tl):
        self.tl = tl
        self.scs = tl["scenes"]
        self.prev_clock = {}
        pc = None
        for s in self.scs:
            self.prev_clock[s["id"]] = pc
            c = SCMAP[s["id"]]["clock"]
            if c:
                pc = c
        # subtitle chunks
        self.subs = []
        for s in self.scs:
            for L in s["lines"]:
                ch = split_sub(L.get("sub", L["say"]))
                n = sum(len(c) for c in ch)
                tt = L["start"]
                for c in ch:
                    d = (L["end"] - L["start"]) * len(c) / n
                    self.subs.append((tt, tt + d, sub_display(c)))
                    tt += d
        self.hg = header_grad()
        self.vig = vignette_surface(0.55)

    def scene_at(self, t):
        for i, s in enumerate(self.scs):
            if s["start"] <= t < s["end"]:
                return i
        return len(self.scs) - 1

    def state(self, i, t):
        s = self.scs[i]
        lt = t - s["start"]
        lines = [dict(cue=L["cue"], t0=L["start"] - s["start"], t1=L["end"] - s["start"]) for L in s["lines"]]
        return S(SCMAP[s["id"]], lt, lines, s["end"] - s["start"], t)

    def draw_scene(self, ctx, i, t):
        st = self.state(i, t)
        vis = SCMAP[self.scs[i]["id"]]["vis"]
        SC.RENDERERS[vis](ctx, st)
        return st

    def frame(self, t):
        surf, ctx = new_surface()
        i = self.scene_at(t)
        st = self.draw_scene(ctx, i, t)
        # crossfade from previous scene
        XF = 0.45
        s = self.scs[i]
        if i > 0 and t - s["start"] < XF:
            k = (t - s["start"]) / XF
            ps, pc = new_surface()
            self.draw_scene(pc, i - 1, t)
            ctx.set_source_surface(ps, 0, 0); ctx.paint_with_alpha(1 - ease(k))
        ctx.set_source_surface(self.vig, 0, 0); ctx.paint()
        sid = s["id"]
        meta = SCMAP[sid]
        ctx.set_source_surface(self.hg, 0, 0); ctx.paint_with_alpha(1.0 if sid != "s00" else 0.7)
        if sid != "s00":
            ha = clamp((t - s["start"]) / 0.6) if i > 0 and SCMAP[self.scs[i - 1]["id"]]["title"] != meta["title"] else 1.0
            axis_a = 1.0 if meta["clock"] else 0.0
            k = clamp((t - s["start"]) / 1.5)
            draw_header(ctx, meta["title"], meta["clock"], self.prev_clock[sid], k, ha, axis_a)
        draw_badges(ctx, SC.BADGE[meta["vis"]])
        for (a, b, txt) in self.subs:
            if a - 0.02 <= t < b + 0.12:
                draw_subtitle(ctx, txt, 1.0)
                break
        # end fade
        T = self.tl["total"]
        if t > T - 1.2:
            ctx.set_source_rgba(0, 0, 0, clamp((t - (T - 1.2)) / 1.2)); ctx.paint()
        return surf


def stills(times, prefix="still"):
    tl = load_timeline()
    C = Comp(tl)
    os.makedirs(f"{WORK}/stills", exist_ok=True)
    out = []
    for t in times:
        s = C.frame(float(t))
        fn = f"{WORK}/stills/{prefix}_{float(t):07.2f}.png"
        s.write_to_png(fn)
        out.append(fn)
    return out


def render_chunk(args):
    k, f0, f1 = args
    tl = load_timeline()
    C = Comp(tl)
    fn = f"{WORK}/video/chunk_{k:03d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                          "-r", str(FPS), fn], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        s = C.frame(f / FPS)
        p.stdin.write(bytes(s.get_data()))
    p.stdin.close(); p.wait()
    return fn


def video(workers=4, start=0.0, end=None, name="picture.mp4"):
    from multiprocessing import Pool
    tl = load_timeline()
    os.makedirs(f"{WORK}/video", exist_ok=True)
    F0 = int(start * FPS)
    F1 = int(math.ceil((end or tl["total"]) * FPS))
    n = max(1, (F1 - F0) // 250)
    edges = [F0 + (F1 - F0) * i // n for i in range(n + 1)]
    jobs = [(i, edges[i], edges[i + 1]) for i in range(n)]
    with Pool(workers) as pool:
        files = []
        for i, fn in enumerate(pool.imap(render_chunk, jobs)):
            files.append(fn)
            print(f"chunk {i + 1}/{n}", flush=True)
    lst = f"{WORK}/video/list.txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    f"{WORK}/video/{name}"], check=True)
    print("done", f"{WORK}/video/{name}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        tl = build_timeline(); print("total", tl["total"])
    elif cmd == "stills":
        print("\n".join(stills(sys.argv[2:])))
    elif cmd == "video":
        video(int(sys.argv[2]) if len(sys.argv) > 2 else 4,
              float(sys.argv[3]) if len(sys.argv) > 3 else 0.0,
              float(sys.argv[4]) if len(sys.argv) > 4 else None,
              sys.argv[5] if len(sys.argv) > 5 else "picture.mp4")
