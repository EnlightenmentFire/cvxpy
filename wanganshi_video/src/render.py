# -*- coding: utf-8 -*-
"""Timeline + frame compositor + parallel encoder.
usage:
  python render.py timeline <durations.json> <out timeline.json>
  python render.py still <timeline.json> <t> <out.png>
  python render.py sheet <timeline.json> <out.jpg>           # contact sheet (one frame per scene)
  python render.py video <timeline.json> <out.mp4> [t0 t1]   # parallel (NPROC) render
"""
import sys, os, json, math, re, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from gfx import *  # noqa
import scenes as S
from script_data import SCENES, all_lines

FPS = 25
TITLE_DUR = 2.4

CHAPTERS = [("s01", "一　不借也得借"), ("s08", "二　一盤大棋"), ("s13", "三　紙面上的好政策"), ("s19", "四　到了縣裡"),
            ("s26", "五　聽不見的聲音"), ("s31", "六　翻來覆去"), ("s34", "七　一個問號")]


def chapter_of(sid):
    order = [s["id"] for s in SCENES] + ["title"]
    cur = CHAPTERS[0][1]
    if sid == "title":
        return ""
    for k, name in CHAPTERS:
        if order.index(sid) >= order.index(k):
            cur = name
    return cur


# ───────────────────────── timeline ─────────────────────────
def build_timeline(durs, lead=0.0):
    t = lead
    lines, scenes = [], []
    for sc in SCENES:
        s0 = t
        for i, d in enumerate(sc["lines"]):
            lid = f"{sc['id']}_{i + 1:02d}"
            du = durs[lid]
            lines.append(dict(id=lid, scene=sc["id"], vis=sc["vis"], k=d["k"], t=d["t"], card=d["card"],
                              start=round(t, 3), end=round(t + du, 3)))
            t += du + d["gap"]
        scenes.append(dict(id=sc["id"], vis=sc["vis"], start=round(s0, 3), end=round(t, 3)))
        if sc["id"] == "s07":
            scenes.append(dict(id="title", vis="title", start=round(t, 3), end=round(t + TITLE_DUR, 3)))
            t += TITLE_DUR
    total = t + 1.0
    scenes[-1]["end"] = round(total, 3)
    return dict(lines=lines, scenes=scenes, total=round(total, 3), fps=FPS)


# ───────────────────────── overlays ─────────────────────────
@functools.lru_cache(maxsize=None)
def header_layer(chapter, dark):
    lay = pil_rgba(W, 240)
    col = (236, 226, 204) if dark else INK
    paste(lay, seal("權力組織", 92, rot=0), 92, 112)
    draw_text(lay, (160, 88), "王安石變法為什麼失敗", font("serif_black_tc", 40), col + (255,), anchor="lm")
    if chapter:
        draw_text(lay, (160, 142), chapter, font("serif_tc", 34), ((214, 120, 100) if dark else (150, 24, 20)) + (255,), anchor="lm")
    # AI badge
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([W - 170, 72, W - 40, 122], radius=10, fill=(0, 0, 0, 90), outline=(255, 255, 255, 150), width=2)
    draw_text(lay, (W - 105, 97), "AI配音", font("sans_med", 28), (255, 255, 255, 230))
    return lay


DARK_VIS = {"hook_rays", "tiaolisi"}


def is_dark(vis, t_local, sc_lines):
    if vis in DARK_VIS:
        return True
    if vis == "bianjing_night":
        return len(sc_lines) > 1 and t_local < sc_lines[1][0]
    return False


def sub_chunks(text, maxlen=15):
    """split subtitle into display chunks (each <= 2 rows of maxlen)."""
    parts = re.split(r"(?<=[，。？！；：])", text)
    parts = [p for p in parts if p]
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxlen * 2 - 2 or not cur:
            cur += p
        else:
            chunks.append(cur); cur = p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        while len(c) > maxlen * 2:
            out.append(c[:maxlen * 2]); c = c[maxlen * 2:]
        out.append(c)
    return out


def strip_end_punct(s):
    return s.rstrip("，。；：、")


@functools.lru_cache(maxsize=4096)
def sub_layer(text):
    f = font("serif_black", 54)
    rows = balanced_wrap(text, f, 900)
    lh = 76
    h = lh * len(rows) + 40
    lay = pil_rgba(W, h)
    d = ImageDraw.Draw(lay)
    widths = [text_size(r, f)[0] for r in rows]
    bw = max(widths) + 70
    d.rounded_rectangle([(W - bw) / 2, 0, (W + bw) / 2, h], radius=18, fill=(18, 16, 14, 150))
    for i, r in enumerate(rows):
        draw_text(lay, (W / 2, 20 + lh * i + lh / 2 - 4), r, f, (250, 244, 228, 255))
    return lay


@functools.lru_cache(maxsize=256)
def card_layer(orig, src, plain):
    latin = all(ord(ch) < 0x2E80 for ch in orig)
    fo = font("serif_reg", 54) if latin else font("serif_black_tc", 64)
    fp = font("sans_med", 42)
    fs = font("serif", 34)
    rows = balanced_wrap(orig, fo, 820)
    prow = balanced_wrap(plain, fp, 820)
    srows = balanced_wrap('—— ' + src, fs, 860)
    h = 90 + len(rows) * int(fo.size * 1.45) + 30 + 48 * len(srows) + 12 + 30 + len(prow) * 62 + 70
    w = 960
    lay = pil_rgba(w, h)
    d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, w, h], fill=(246, 238, 214, 248), outline=(150, 24, 20, 255), width=6)
    d.rectangle([14, 14, w - 14, h - 14], outline=(150, 24, 20, 160), width=2)
    y = 80
    for r in rows:
        draw_text(lay, (w / 2, y + fo.size * 0.5), r, fo, INK + (255,), trad=True)
        y += int(fo.size * 1.45)
    y += 10
    d.line([(w / 2 - 160, y), (w / 2 + 160, y)], fill=(150, 24, 20, 255), width=3)
    y += 44
    for sr in balanced_wrap("—— " + src, fs, 860):
        draw_text(lay, (w / 2, y), sr, fs, (150, 24, 20, 255), trad=True)
        y += 48
    y += 12
    for r in prow:
        draw_text(lay, (w / 2, y + 22), r, fp, (70, 64, 58, 255))
        y += 62
    return lay


# ───────────────────────── frame ─────────────────────────
class Film:
    def __init__(self, tl):
        self.tl = tl
        self.scenes = tl["scenes"]
        self.lines = tl["lines"]
        self.by_scene = {}
        for l in self.lines:
            self.by_scene.setdefault(l["scene"], []).append(l)

    def scene_at(self, t):
        for i, s in enumerate(self.scenes):
            if s["start"] <= t < s["end"]:
                return i
        return len(self.scenes) - 1

    def scene_img(self, i, t):
        s = self.scenes[i]
        ls = self.by_scene.get(s["id"], [])
        L = [(l["start"] - s["start"], l["end"] - s["start"]) for l in ls] or [(0, s["end"] - s["start"])]
        ctx = S.Ctx(t - s["start"], s["end"] - s["start"], L, s["id"])
        img = S.SCENE_FN[s["vis"]](ctx)
        return img, ctx, s

    def frame(self, t):
        i = self.scene_at(t)
        img, ctx, s = self.scene_img(i, t)
        # crossfade from previous scene
        XF = 0.35
        if i > 0 and t - s["start"] < XF:
            prev, _, _ = self.scene_img(i - 1, s["start"] - 1e-3)
            a = ease((t - s["start"]) / XF)
            img = Image.blend(prev, img, a)
        img = img.convert("RGBA")
        if s["vis"] != "title":
            img.alpha_composite(header_layer(chapter_of(s["id"]), is_dark(s["vis"], ctx.t, ctx.L)), (0, 0))
        # quote card
        ls = self.by_scene.get(s["id"], [])
        for j, l in enumerate(ls):
            if l["k"] != "q" or not l["card"]:
                continue
            t0, t1 = l["start"] - 0.15, l["end"] + 1.6
            if j + 1 < len(ls):
                t1 = min(max(t1, ls[j + 1]["start"] + 0.8), ls[j + 1]["end"])
            t1 = min(t1, s["end"] - 0.1)
            if t0 <= t <= t1:
                a = ease((t - t0) / 0.35) * (1 - ease((t - (t1 - 0.35)) / 0.35))
                dim = Image.new("RGBA", (W, H), (20, 16, 12, int(110 * a)))
                img.alpha_composite(dim)
                c = l["card"]
                lay = card_layer(c["orig"], c["src"], c["plain"])
                paste(img, lay, W / 2, 1000 - 30 * (1 - a), alpha=a)
        # subtitles
        for l in ls:
            if l["k"] == "q":
                continue
            if l["start"] - 0.05 <= t < l["end"] + 0.25:
                chunks = sub_chunks(l["t"])
                n = sum(len(c) for c in chunks)
                acc = 0
                dur = l["end"] - l["start"]
                for ch in chunks:
                    c0 = l["start"] + dur * acc / n
                    acc += len(ch)
                    c1 = l["start"] + dur * acc / n
                    if c0 - 0.05 <= t < c1 + (0.25 if acc == n else 0):
                        lay = sub_layer(strip_end_punct(ch))
                        img.alpha_composite(lay, (0, 1700 - lay.height // 2))
                        break
        return img.convert("RGB")


def render_range(tl, out, f0, f1):
    film = Film(tl)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        im = film.frame(fi / FPS)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()


def main():
    cmd = sys.argv[1]
    if cmd == "timeline":
        durs = json.load(open(sys.argv[2]))
        tl = build_timeline(durs)
        json.dump(tl, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
        print("total", tl["total"], "s =", tl["total"] / 60, "min")
    elif cmd == "still":
        tl = json.load(open(sys.argv[2]))
        Film(tl).frame(float(sys.argv[3])).save(sys.argv[4])
    elif cmd == "sheet":
        tl = json.load(open(sys.argv[2]))
        film = Film(tl)
        ims = []
        for s in tl["scenes"]:
            t = s["start"] + (s["end"] - s["start"]) * float(os.environ.get("FRAC", 0.7))
            ims.append(film.frame(t).resize((270, 480)))
        cols = 8
        rows = math.ceil(len(ims) / cols)
        sheet = Image.new("RGB", (cols * 270, rows * 480), (0, 0, 0))
        for k, im in enumerate(ims):
            sheet.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sheet.save(sys.argv[3], quality=85)
    elif cmd == "video":
        tl = json.load(open(sys.argv[2]))
        out = sys.argv[3]
        t0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
        t1 = float(sys.argv[5]) if len(sys.argv) > 5 else tl["total"]
        F0, F1 = int(round(t0 * FPS)), int(round(t1 * FPS))
        n = int(os.environ.get("NPROC", 4))
        segdir = out + ".segs"
        os.makedirs(segdir, exist_ok=True)
        # split into many small chunks so workers stay balanced
        CH = 250
        jobs = [(a, min(F1, a + CH)) for a in range(F0, F1, CH)]
        from multiprocessing import Pool
        args = [(tl, f"{segdir}/{k:05d}.mp4", a, b) for k, (a, b) in enumerate(jobs) if not os.path.exists(f"{segdir}/{k:05d}.mp4.done")]
        with Pool(n) as pool:
            pool.starmap(_job, args)
        with open(f"{segdir}/list.txt", "w") as fh:
            for k in range(len(jobs)):
                fh.write(f"file '{os.path.abspath(segdir)}/{k:05d}.mp4'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{segdir}/list.txt", "-c", "copy", out], check=True)
        print("wrote", out)


def _job(tl, out, a, b):
    render_range(tl, out, a, b)
    open(out + ".done", "w").close()
    print("seg", out, flush=True)


if __name__ == "__main__":
    main()
