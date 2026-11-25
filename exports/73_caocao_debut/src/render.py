# -*- coding: utf-8 -*-
"""Frame compositor + parallel segment renderer.
usage: python render.py stills t1 t2 ...        -> out/stills/*.jpg
       python render.py seg K N                 -> out/seg_K.mp4 (frames K::N chunked contiguous)
"""
import sys, os, math, json, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw
from gfx import *
from overlays import card_img, ana_img, q3_parts, yy_parts, sub_img, title_big, title_small, corner
from scenes import VIS
import timeline

OUT = "/tmp/claude-0/w73/out"
TL = timeline.build()
VISL = TL["visuals"]
ZOOM = {"gate": 0.07, "map": 0.04, "luoyang": 0.04, "stele": 0.05, "seal": 0.04}


@functools.lru_cache(maxsize=64)
def static_for(i):
    v = VISL[i]
    return VIS[v["name"]].static(v["p"])


def vis_frame(i, t):
    v = VISL[i]
    tl = t - v["t0"]
    base = static_for(i).copy()
    ev = dict(lines=v["lines"], strikes=[s - v["t0"] for s in TL["strikes"]])
    sh = VIS[v["name"]].dyn(base, tl, v["t1"] - v["t0"], v["p"], ev) or 0
    z = ZOOM.get(v["name"])
    if z:
        k = 1 + z * ease(tl / max(4.0, v["t1"] - v["t0"]))
        cw, ch = W / k, H / k
        cx, cy = W / 2, min(H * 0.55, H - ch / 2)
        base = base.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    if sh:
        dx = int(sh * math.sin(t * 90)); dy = int(sh * math.cos(t * 77))
        b2 = Image.new("RGBA", (W, H), (0, 0, 0, 255)); b2.alpha_composite(base, (max(dx, 0), max(dy, 0)), (max(-dx, 0), max(-dy, 0)))
        base = b2
    return base


def active(lst, t):
    return [o for o in lst if o["t0"] <= t < o["t1"]]


def fade(t, t0, t1, fi=0.35, fo=0.35):
    return clamp01((t - t0) / fi) * clamp01((t1 - t) / fo)


def frame(t):
    # visual (+ crossfade)
    idx = max(i for i, v in enumerate(VISL) if v["t0"] <= t + 1e-9) if t >= VISL[0]["t0"] else 0
    img = vis_frame(idx, t)
    v = VISL[idx]
    XF = 0.45
    if idx > 0 and t - v["t0"] < XF:
        prev = vis_frame(idx - 1, t)
        k = ease((t - v["t0"]) / XF)
        img = Image.blend(prev, img, k)
    # dim under overlays
    ovs = active(TL["overlays"], t)
    titles = [ti for ti in TL["titles"] if ti["t0"] <= t < ti["t1"]]
    dim = 0.0
    for o in ovs:
        dim = max(dim, 0.55 * fade(t, o["t0"], o["t1"]))
    for ti in titles:
        dim = max(dim, 0.55 * fade(t, ti["t0"], ti["t1"], 0.3, 0.4))
    if dim > 0:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * dim))))
    for o in ovs:
        draw_overlay(img, o, t)
    for ti in titles:
        a = fade(t, ti["t0"], ti["t1"], 0.3, 0.4)
        k = ease_out((t - ti["t0"]) / 0.6)
        paste_c(img, title_big(ti["text"]), 540, 860 - 20 * (1 - k), a)
    # persistent small chapter title
    cur = [ti for ti in TL["titles"] if ti["t1"] <= t]
    curscene = next((r["scene"] for r in reversed(TL["lines"]) if r["t0"] <= t + 0.6), "s01")
    if cur and t > 2 and cur[-1]["scene"] == curscene:
        last = cur[-1]
        # only within its scene: until next title starts
        paste(img, title_small(last["text"]), 0, 150, clamp01((t - last["t1"]) / 0.5) * 0.9)
    # subtitles
    for s in TL["subs"]:
        if s["t0"] <= t < s["t1"] + 0.02:
            si = sub_img(s["text"])
            paste(img, si, 540 - si.width / 2, 1460, 1.0)
            break
    # corner tags
    c = corner("AI配音"); paste(img, c, W - c.width - 36, 60, 0.9)
    tag = VIS[v["name"]].tag
    if tag:
        c2 = corner(tag); paste(img, c2, W - c.width - c2.width - 50, 60, 0.9)
    return img.convert("RGB")


def draw_overlay(img, o, t):
    a = fade(t, o["t0"], o["t1"])
    k = ease_out((t - o["t0"]) / 0.45)
    L = TL["lines"]
    if o["kind"] == "card":
        d = o["data"]
        im = card_img(d["text"], d["src"], d["lv"], d["bh"], d.get("big", False), d.get("dashed", False))
        cy = 820 if not d.get("big") else 880
        y = min(cy - im.height / 2, 1420 - im.height)
        paste(img, im, 60, max(290, y) + 30 * (1 - k), a)
    elif o["kind"] == "ana":
        d = o["data"]; im = ana_img(d["ana"], d["bias"])
        paste(img, im, 60, max(290, 830 - im.height / 2) + 30 * (1 - k), a)
    elif o["kind"] == "q3":
        d = o["data"]; head, rows = q3_parts(d["have"], d["lean"], d["step"])
        paste(img, head, 60, 300, a)
        y = 490
        for j, r in enumerate(rows):
            if j < len(o["lines"]):
                lt = L[o["lines"][j]]["t0"] - 0.2
                kk = ease_out((t - lt) / 0.4)
                paste(img, r, 60, y + 24 * (1 - kk), a * kk)
            y += r.height + 22
    elif o["kind"] == "yy":
        d = o["data"]; r1, r2 = yy_parts(d["yy"], d["sx"])
        y0 = 560
        paste(img, r1, 60, y0 + 24 * (1 - k), a)
        if len(o["lines"]) > 1:
            lt = L[o["lines"][1]]["t0"] - 0.2
            kk = ease_out((t - lt) / 0.4)
            paste(img, r2, 60, y0 + r1.height + 40 + 24 * (1 - kk), a * kk)


def stills(ts):
    os.makedirs(f"{OUT}/stills", exist_ok=True)
    for t in ts:
        frame(float(t)).save(f"{OUT}/stills/t{float(t):07.1f}.jpg", quality=88)


def seg(K, N):
    nf = int(math.ceil(TL["total"] * FPS))
    per = int(math.ceil(nf / N))
    a, b = K * per, min(nf, (K + 1) * per)
    os.makedirs(OUT, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", f"{OUT}/seg_{K:02d}.mp4"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - a) % 500 == 0:
            print(f"seg{K}: {f - a}/{b - a}", flush=True)
    p.stdin.close(); p.wait()
    print(f"seg{K} done", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills(sys.argv[2:])
    elif sys.argv[1] == "seg":
        seg(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "dump":
        json.dump({k: TL[k] for k in ("lines", "titles", "beats", "total", "strikes", "subs")}, open(f"{OUT}/timeline.json", "w"), ensure_ascii=False, indent=1)
