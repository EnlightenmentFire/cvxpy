# -*- coding: utf-8 -*-
"""Timeline + frame renderer.
  python render.py timeline [est]       build timeline.json from processed wavs (or estimate)
  python render.py stills t1 t2 ...     render PNG stills at times (s)
  python render.py video [nproc]        render all segments + concat to video_noaudio.mp4
"""
import sys, os, json, re, math, subprocess, time
import numpy as np
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from script_data import all_lines, S
import scenes as SC
from widgets import header, ai_badge

WORK = "/tmp/claude-0/work"
PROC = f"{WORK}/tts/proc"
TL = f"{WORK}/timeline.json"
FPS = 25
SCENE_GAP = 0.55
END_DUR = 6.0
LEAD = 0.35
SHIFT = 55

def bg_fill(ctx):
    SC.bg(ctx, 0)



def hanzi(s):
    return len(re.sub(r"[^一-鿿A-Za-z0-9]", "", s))


def build_timeline(est=False):
    import soundfile as sf
    lines = all_lines()
    t = LEAD
    out_lines, scenes = [], []
    cur = None
    for d in lines:
        if cur != d["scene"]:
            if cur is not None:
                t += SCENE_GAP
            scenes.append(dict(id=d["scene"], t0=max(0.0, t - (SCENE_GAP / 2 if cur else LEAD))))
            cur = d["scene"]
        p = f"{PROC}/{d['id']}.wav"
        if not est and os.path.exists(p):
            dur = sf.info(p).duration
        else:
            dur = hanzi(d["say"]) / 4.6 + 0.2
        out_lines.append(dict(id=d["id"], scene=d["scene"], t=d["t"], q=d["q"], s0=round(t, 3), s1=round(t + dur, 3)))
        t += dur + d["p"]
    scenes.append(dict(id="end", t0=t + 0.2))
    for i, s in enumerate(scenes):
        s["t1"] = scenes[i + 1]["t0"] if i + 1 < len(scenes) else t + 0.2 + END_DUR
    json.dump(dict(lines=out_lines, scenes=scenes, total=scenes[-1]["t1"]), open(TL, "w"), ensure_ascii=False, indent=1)
    print(f"total {scenes[-1]['t1']:.1f}s, {len(out_lines)} lines")


class Sc:
    def __init__(self, s, lines):
        self.id, self.t0, self.t1 = s["id"], s["t0"], s["t1"]
        self.dur = self.t1 - self.t0
        self.lines = [dict(l, s0=l["s0"] - self.t0, s1=l["s1"] - self.t0) for l in lines if l["scene"] == self.id]
        self.T = 0

    def cue(self, i):
        if i >= len(self.lines):
            return -1e9
        return self.T - self.lines[i]["s0"]

    def ld(self, i):
        return self.lines[i]["s1"] - self.lines[i]["s0"]


def sub_chunks(text, s0, s1, maxc=15):
    """Split a line into subtitle cards: by punctuation, greedy merge up to maxc chars."""
    disp = text
    parts = re.findall(r"[^，。？！；：,]+[，。？！；：,]?", disp)
    cards, cur = [], ""
    for p in parts:
        pc = p.rstrip("，。；：,")
        if hanzi(cur + pc) <= maxc or not cur:
            cur = cur + pc if not cur else cur + "，" + pc if not cur.endswith(("？", "！", "」")) else cur + pc
        else:
            cards.append(cur); cur = pc
    if cur:
        cards.append(cur)
    cards = [c.strip("，") for c in cards]
    tot = sum(max(1, hanzi(c)) for c in cards)
    out, t = [], s0
    for c in cards:
        d = (s1 - s0) * max(1, hanzi(c)) / tot
        out.append((c, t, t + d)); t += d
    return out


class Film:
    def __init__(self):
        tl = json.load(open(TL))
        self.total = tl["total"]
        self.scenes = [Sc(s, tl["lines"]) for s in tl["scenes"]]
        self.subs = []
        for l in tl["lines"]:
            for c, a, b in sub_chunks(l["t"], l["s0"], l["s1"]):
                self.subs.append((c, a, b, l["q"]))

    def frame(self, t, fi=0):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        sc = next((s for s in self.scenes if s.t0 <= t < s.t1), self.scenes[-1])
        sc.T = t - sc.t0
        ctx.save()
        if sc.id not in ("s00",):
            bg_fill(ctx); ctx.translate(0, SHIFT)
        SC.SCENES[sc.id](ctx, sc.T, sc, fi); ctx.restore()
        # scene transition dip
        d_in, d_out = sc.T, sc.t1 - t
        dip = max(0, 1 - d_in / 0.28) if sc.id != "s00" else 0
        dip = max(dip, max(0, 1 - d_out / 0.28) if sc.id != "end" else 0)
        if dip > 0:
            rgba(ctx, (0, 0, 0), 0.85 * dip); ctx.paint()
        # overlays
        ha = 1.0 if sc.id not in ("s00", "end") else 0.0
        if sc.id == "s00":
            ha = 0.0
        header(ctx, SC.TITLES.get(sc.id, ""), ha)
        if sc.id == "s00":
            text(ctx, "历史的关键一局 · 中途岛", 54, 196, 30, GOLD, 0.9, SERIF, True, "l", spacing=0.05)
        ai_badge(ctx)
        self.subtitle(ctx, t)
        grain(ctx, fi)
        return surf

    def subtitle(self, ctx, t):
        cur = [s for s in self.subs if s[1] - 0.05 <= t < s[2] + 0.05]
        if not cur:
            return
        c, a, b, q = cur[-1]
        al = min(1, (t - a + 0.05) / 0.12, (b + 0.05 - t) / 0.12)
        size = 54
        rows = wrap_cn(c, W - 120, size, SANS, True)
        if len(rows) == 2:
            n = len(c); k = (n + 1) // 2
            while k < n and c[k] in "，。！？、：；」』）》": k += 1
            rows = [c[:k], c[k:]]
        y0 = 1535 - (len(rows) - 1) * size * 0.65
        maxw = max(text_w(r, size, SANS, True) for r in rows)
        rrect(ctx, W / 2 - maxw / 2 - 30, y0 - size * 1.05, maxw + 60, size * 1.3 * len(rows) + 18, 12)
        rgba(ctx, (0, 0, 0), 0.5 * al); ctx.fill()
        for i, r in enumerate(rows):
            text(ctx, r, W / 2, y0 + i * size * 1.3, size, GOLD if q else WHITE, al, SANS, True, stroke=5, stroke_c=(0, 0, 0))


def to_bytes(surf):
    return bytes(surf.get_data())


def render_range(film, f0, f1, out):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(to_bytes(film.frame(f / FPS, f)))
    p.stdin.close(); p.wait()


def main():
    mode = sys.argv[1]
    if mode == "timeline":
        build_timeline(est=len(sys.argv) > 2)
    elif mode == "stills":
        film = Film(); os.makedirs(f"{WORK}/stills", exist_ok=True)
        for a in sys.argv[2:]:
            t = float(a); surf = film.frame(t, int(t * FPS))
            surf.write_to_png(f"{WORK}/stills/t{t:07.2f}.png")
        print("ok")
    elif mode == "seg":
        film = Film(); f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        t = time.time(); render_range(film, f0, f1, out); print(f"seg {f0}-{f1} {time.time() - t:.0f}s", flush=True)
    elif mode == "video":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        film = Film(); nf = int(math.ceil(film.total * FPS))
        os.makedirs(f"{WORK}/segs", exist_ok=True)
        chunk = 750
        jobs = [(f, min(nf, f + chunk)) for f in range(0, nf, chunk)]
        procs = []
        for i, (a, b) in enumerate(jobs):
            out = f"{WORK}/segs/seg{i:03d}.mp4"
            if os.path.exists(out) and os.environ.get("KEEP"):
                continue
            while len([p for p in procs if p.poll() is None]) >= n:
                time.sleep(1)
            procs.append(subprocess.Popen([sys.executable, __file__, "seg", str(a), str(b), out]))
        for p in procs:
            p.wait()
        with open(f"{WORK}/segs/list.txt", "w") as f:
            for i in range(len(jobs)):
                f.write(f"file 'seg{i:03d}.mp4'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/segs/list.txt", "-c", "copy", f"{WORK}/video_noaudio.mp4"], check=True)
        print("frames", nf)


if __name__ == "__main__":
    main()
