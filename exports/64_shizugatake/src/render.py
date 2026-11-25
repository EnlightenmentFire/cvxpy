# -*- coding: utf-8 -*-
"""Render frames. usage:
  python render.py still T [T...]            -> /tmp/claude-0/work/stills/t_<T>.png
  python render.py seg i n                   -> segment i of n (contiguous frame range) -> work/segs/seg_i.mp4
  python render.py all [n]                   -> spawn n workers and concat to work/video_noaudio.mp4
"""
import sys, os, json, math, subprocess, bisect
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import film

WK = "/tmp/claude-0/work"
FPS = 25
TL = json.load(open(f"{WK}/timeline.json"))
SC = TL["scenes"]
STARTS = [s["start"] for s in SC]
SUBS = [s for L in TL["lines"] for s in L["sub"]]
SUB_S = [s["s"] for s in SUBS]


def make_bg_blur():
    p = f"{WK}/base/bg_blur.png"
    if os.path.exists(p):
        return
    from PIL import Image, ImageFilter, ImageEnhance
    im = Image.open(f"{WK}/base/region_day.png")
    w, h = im.size
    cr = im.crop((int(w * 0.15), int(h * 0.2), int(w * 0.75), int(h * 0.85))).resize((1200, 2100))
    cr = cr.filter(ImageFilter.GaussianBlur(10))
    cr = ImageEnhance.Brightness(cr).enhance(0.55)
    cr.save(p)


def subtitle(c, T):
    i = bisect.bisect_right(SUB_S, T) - 1
    if i < 0:
        return
    s = SUBS[i]
    nxt = SUBS[i + 1]["s"] if i + 1 < len(SUBS) else s["e"] + 1
    end = min(s["e"] + 0.35, nxt)
    if T > end:
        return
    a = min(1.0, (T - s["s"]) / 0.08, (end - T) / 0.08 + 0.0001)
    a = clamp(a)
    y = 1545
    size = 56
    tw = measure(s["text"], size)
    rrect(c, W / 2 - tw / 2 - 30, y - 62, tw + 60, 88, 14, INK, 0.42 * a, blur=10)
    text(c, s["text"], W / 2, y, size, "serif", WHITE, a, stroke=9, sa=0.9)


def chapter(c, T, sc):
    if not sc.get("chapter"):
        return
    t = T - sc["start"]
    if t > 4.2:
        return
    num, name = sc["chapter"]
    a = fio(t, 0.0, 4.2, 0.4)
    c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, 0.45 * fio(t, 0, 1.6, 0.3)))
    y = 210
    rrect(c, 70, y - 64, 120, 120, 8, RED, a)
    text(c, num, 130, y + 22, 76, "brush", WHITE, a)
    text(c, name, 220, y + 24, 70, "brush", WHITE, a, "l", stroke=8, shadow=10)
    c.drawLine(220, y + 54, 220 + measure(name, 70, "brush") * ev(t, 0.2, 0.8), y + 54, paint(GOLD, a, stroke=3))


MAPSCENES = {"firedragon", "ridges", "leave", "raid", "orders", "ogaki", "winter", "winterwar", "deploy", "patience", "tomino",
             "raidmap", "stay", "trap", "niwa", "decide", "march", "retreat", "maeda", "kitanosho", "lake"}


def chrome(c, T, sc):
    # top gradient + series tag
    vgrad(c, 0, 180, INK, 0.55, INK, 0.0)
    vgrad(c, 1380, H, INK, 0.0, INK, 0.62)
    text(c, "从无名小卒到天下人 · 贱岳之战", 50, 72, 30, "semi", GOLD, 0.85, "l", stroke=4)
    text(c, "AI配音", W - 50, 72, 28, "sansm", (230, 225, 215), 0.75, "r", stroke=4)
    if sc["vis"] in MAPSCENES:
        text(c, "地图示意", W - 50, 112, 26, "sansm", (230, 225, 215), 0.7, "r", stroke=4)
    if sc["vis"] in MAPSCENES and sc["vis"] not in ("winter", "winterwar"):
        text(c, "地形 Mapzen/SRTM · 水系 © OpenStreetMap", W - 50, 1405, 20, "sansm", (220, 215, 205), 0.55, "r", stroke=3)


def frame(c, T):
    i = max(0, bisect.bisect_right(STARTS, T) - 1)
    sc = SC[i]
    t = T - sc["start"]
    S = dict(L=sc["L"], E=sc["E"], dur=sc["end"] - sc["start"])
    c.save()
    film.SCENE_FN[sc["vis"]](c, t, S)
    c.restore()
    # scene fade-in
    if i > 0 and t < 0.35:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, 0.6 * (1 - t / 0.35)))
    chrome(c, T, sc)
    chapter(c, T, sc)
    subtitle(c, T)
    # global fade-out at end
    if T > TL["total"] - 1.2:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, clamp((T - TL["total"] + 1.2) / 1.0)))


def surface():
    return skia.Surface(W, H)


def still(Ts):
    os.makedirs(f"{WK}/stills", exist_ok=True)
    s = surface()
    for T in Ts:
        c = s.getCanvas(); c.clear(col(INK))
        frame(c, float(T))
        s.makeImageSnapshot().save(f"{WK}/stills/t_{float(T):07.2f}.png", skia.kPNG)
        print("still", T)


def seg(i, n):
    N = int(math.ceil(TL["total"] * FPS))
    f0, f1 = N * i // n, N * (i + 1) // n
    os.makedirs(f"{WK}/segs", exist_ok=True)
    out = f"{WK}/segs/seg_{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    s = surface()
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    buf = np.empty((H, W, 4), np.uint8)
    for f in range(f0, f1):
        c = s.getCanvas(); c.clear(col(INK))
        frame(c, f / FPS)
        s.readPixels(info, buf, W * 4, 0, 0)
        p.stdin.write(buf.tobytes())
        if (f - f0) % 250 == 0:
            print(f"seg{i} {f - f0}/{f1 - f0}", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, flush=True)


if __name__ == "__main__":
    make_bg_blur()
    cmd = sys.argv[1]
    if cmd == "still":
        still(sys.argv[2:])
    elif cmd == "cover":
        out = sys.argv[2]
        s = surface(); c = s.getCanvas(); film.cover(c)
        img = s.makeImageSnapshot()
        img.save(out + "/封面_1080x1920.png", skia.kPNG)
        from PIL import Image
        im = Image.open(out + "/封面_1080x1920.png").convert("RGB")
        im.crop((0, 90, 1080, 1530)).save(out + "/封面_3x4_1080x1440.png")
        print("cover ok")
    elif cmd == "seg":
        seg(int(sys.argv[2]), int(sys.argv[3]))
