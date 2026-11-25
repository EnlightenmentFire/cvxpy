# -*- coding: utf-8 -*-
"""逐帧渲染。
python render.py still t1 t2 ...        # 出预览图
python render.py part K N               # 第 K/N 段渲染为 out/parts/K.mp4
"""
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine as E
import widgets as Wd
from engine import W, H, C, FPS, clamp, prog, ease_out, fade
import scenes
import scenes2  # noqa: F401  注册下半场景
from scenes import SC, S_

WORK = "/tmp/claude-0/work/render"
MAP_SCENES = {"hook", "beaten", "title", "pingyuan", "bigmap", "invade1", "rescue", "xiaopei", "supply", "gate",
              "invade2", "tandong", "lubu", "lubu2", "welcome", "yuanshao", "lose"}


class Film:
    def __init__(self, tl=None):
        self.tl = tl or json.load(open(os.path.join(HERE, "timeline.json")))
        self.lines = self.tl["lines"]
        self.scenes = self.tl["scenes"]
        self.S = [S_(s, self.lines) for s in self.scenes]
        self.end = self.tl["end"]
        self.chname = {c["ch"]: c["title"] for c in self.tl["cards"]}
        # 引文卡窗口
        self.qwin = []
        qs = [ln for ln in self.lines if ln["k"] == "q"]
        for i, ln in enumerate(self.lines):
            if ln["k"] != "q":
                continue
            sc = self.scene_at(ln["t0"] + 0.01)
            nq = [q["t0"] for q in qs if q["t0"] > ln["t0"]]
            e = min(ln["t1"] + 1.6, sc[0]["t1"] - 0.12, (nq[0] - 0.3) if nq else 1e9)
            self.qwin.append((ln["t0"] - 0.12, e, ln, sc[1]))
        # 类比卡窗口
        self.awin = []
        for i, ln in enumerate(self.lines):
            if ln["k"] == "a":
                b = self.lines[i + 1] if i + 1 < len(self.lines) and self.lines[i + 1]["k"] == "b" else None
                sc = self.scene_at(ln["t0"] + 0.01)
                self.awin.append((ln["t0"] - 0.15, sc[0]["t1"] - 0.15, ln, b))

    def scene_at(self, t):
        for s, S in zip(self.scenes, self.S):
            if s["t0"] <= t < s["t1"]:
                return s, S
        return self.scenes[-1], self.S[-1]

    def frame(self, t, idx=0):
        surf, ctx = E.new_frame()
        s, S = self.scene_at(t)
        S._t = t
        f = SC[s["sc"]]
        f(ctx, t, S)
        # 章节签
        ln_now = [ln for ln in self.lines if ln["t0"] - 3 <= t]
        ch = ln_now[-1]["ch"] if ln_now else "open"
        in_card = any(c["t0"] <= t < c["t1"] for c in self.tl["cards"])
        if ch != "open" and not in_card:
            Wd.chapter_tag(ctx, self.chname.get(ch, ""), 1.0)
        # 卡片底暗
        dim = 0.0
        for a, b, ln, Sq in self.qwin:
            if a <= t <= b:
                dim = max(dim, fade(t, a, b - 0.3, 0.3, 0.3))
        for a, b, ln, bl in self.awin:
            if a <= t <= b:
                dim = max(dim, fade(t, a, b - 0.3, 0.3, 0.3))
        if dim > 0:
            E.set_col(ctx, "#000000", 0.32 * dim); ctx.rectangle(0, 0, W, H); ctx.fill()
        for a, b, ln, Sq in self.qwin:
            if a <= t <= b:
                al = fade(t, a, b - 0.3, 0.3, 0.3)
                ap = clamp((t - ln["t0"]) / max(0.6, (ln["t1"] - ln["t0"]) * 0.8))
                Wd.quote_card(ctx, ln["q"], al, y=f.qy, appear=ap, bai_a=fade(t, ln["t0"] + (ln["t1"] - ln["t0"]) * 0.5, None, 0.5))
        for a, b, ln, bl in self.awin:
            if a <= t <= b:
                al = fade(t, a, b - 0.3, 0.3, 0.3)
                ab = fade(t, bl["t0"] - 0.1, None, 0.4) if bl else 0
                Wd.analogy_card(ctx, ln["t"].replace("打个比方：", ""), bl["t"].replace("但这个比方有一处不成立：", "").replace("但这个比方也有不成立的地方：", "") if bl else "",
                                al, ab, y=860)
        # 章节卡
        for c in self.tl["cards"]:
            if c["t0"] <= t < c["t1"]:
                Wd.chapter_card(ctx, t, c["title"], c["t0"], c["t1"] - c["t0"])
        # 字幕
        for sb in self.tl["subs"]:
            if sb["t0"] - 0.02 <= t < sb["t1"] + 0.05:
                ln = next(l for l in self.lines if l["id"] == sb["id"])
                if ln["k"] in ("a", "b") or s["sc"] == "takeaway":
                    break
                Wd.draw_subtitle(ctx, sb["text"], fade(t, sb["t0"] - 0.02, sb["t1"] - 0.03, 0.08, 0.08))
                break
        # 角标
        Wd.badge(ctx, "AI配音", W - 40, 120, 0.9)
        if s["sc"] in MAP_SCENES:
            Wd.badge(ctx, "地图示意 · 州界示意", 40, H - 300, 0.8, "lt", size=22)
        return E.postprocess(surf, idx)


def still(times, prefix="still"):
    os.makedirs(WORK, exist_ok=True)
    fm = Film()
    from PIL import Image
    out = []
    for t in times:
        buf = fm.frame(float(t))
        im = Image.fromarray(buf[..., [2, 1, 0]].copy())
        p = f"{WORK}/{prefix}_{float(t):07.2f}.jpg"
        im.save(p, quality=88)
        out.append(p)
    return out


def part(k, n):
    fm = Film()
    nf = int(round(fm.end * FPS))
    a, b = nf * k // n, nf * (k + 1) // n
    os.makedirs(f"{WORK}/parts", exist_ok=True)
    out = f"{WORK}/parts/{k:02d}.mp4"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for i in range(a, b):
        buf = fm.frame(i / FPS, i)
        p.stdin.write(buf.tobytes())
        if (i - a) % 250 == 0:
            print(f"part {k}: {i - a}/{b - a} frames, {time.time() - t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print(f"part {k} done {b - a} frames in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        for p in still(sys.argv[2:]):
            print(p)
    elif sys.argv[1] == "part":
        part(int(sys.argv[2]), int(sys.argv[3]))
