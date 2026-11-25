# -*- coding: utf-8 -*-
"""合成：场景画面（场景间 0.4 s 交叉淡化）+ 古文/类比卡 + 章节标签 + 角标 + 字幕。
用法：
  python render.py still t1 t2 ...        # 输出静帧 $WORK/stills/t_XXX.jpg
  python render.py seg i n                # 把全片均分 n 段，渲染第 i 段到 $WORK/seg/seg_i.mp4（无声）
"""
import os, sys, json, math, subprocess, time
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import scenes as SC
import timeline

T = timeline.build()
XF = 0.4

CHAPTER = {}
for ids, name in (("ABCD", ""), ("EFGHI", "一 · 败走投曹"), ("JKL", "二 · 一张空头上将衔"), ("MNOP", "三 · 煮酒论英雄"),
                  ("QRS", "四 · 名分跟着人走"), ("TU", "五 · 两条起家路"), ("V", "")):
    for i in ids:
        CHAPTER[i] = name


def scene_at(t):
    for i, s in enumerate(T["scenes"]):
        if s["t0"] <= t < s["t1"]:
            return i
    return len(T["scenes"]) - 1


def draw_scene(c, i, t):
    S = T["scenes"][i]
    SC.VIS[S["vis"]](c, S, t - S["t0"])


def frame(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    i = scene_at(t)
    S = T["scenes"][i]
    draw_scene(c, i, t)
    # 交叉淡化：新场景开头 XF 秒内，盖一层上一场景尾帧的淡出
    if i > 0 and t - S["t0"] < XF:
        prev = skia.Surface(W, H)
        draw_scene(prev.getCanvas(), i - 1, t)
        p = skia.Paint(); p.setAlphaf(1 - ease((t - S["t0"]) / XF))
        c.drawImage(prev.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), p)
    # 卡片
    if S["vis"] != "sanwen":
        for cd in T["cards"]:
            if cd["t0"] - 0.05 <= t < cd["t1"] + 0.35:
                a = ease((t - cd["t0"]) / 0.35) * ease((cd["t1"] + 0.35 - t) / 0.35)
                k = cd["card"]; lt_ = t - cd["t0"]
                if k["kind"] == "quote":
                    h = quote_card_layout(k)[3]
                    draw_quote_card(c, k, 1505 - h, lt_, a)
                elif k["kind"] in ("analogy", "bias"):
                    lines = wrap(k["text"], 50 if k["kind"] == "analogy" else 34, CARD_W - 110, "sans", k["kind"] == "analogy")
                    h = 110 + len(lines) * (50 if k["kind"] == "analogy" else 34) * 1.45 + 40
                    if k["kind"] == "analogy":
                        # 类比卡与偏差卡并存时，类比卡上移
                        nb = [x for x in T["cards"] if x["card"]["kind"] == "bias" and x["t0"] <= t < x["t1"] + 0.35]
                        y = 1505 - h if not nb else 1505 - h - 330
                        draw_text_card(c, "analogy", k["text"], y, lt_, a)
                    else:
                        draw_text_card(c, "bias", k["text"], 1505 - h, lt_, a)
                elif k["kind"] == "duibi":
                    draw_duibi(c, k, 1180, lt_, a)
    # 类比卡在偏差卡出现后仍保留：把 J 场景的类比卡延续
    if S["id"] == "J":
        an = [x for x in T["cards"] if x["card"]["kind"] == "analogy"][0]
        bi = [x for x in T["cards"] if x["card"]["kind"] == "bias"][0]
        if bi["t0"] <= t < bi["t1"] + 0.35:
            a = ease((t - an["t0"]) / 0.35) * ease((bi["t1"] + 0.35 - t) / 0.35)
            lines = wrap(an["card"]["text"], 50, CARD_W - 110, "sans", True)
            h = 110 + len(lines) * 50 * 1.45 + 40
            draw_text_card(c, "analogy", an["card"]["text"], 1505 - 330 - h - 40, 5, a)
    # 章节标签
    ch = CHAPTER.get(S["id"], "")
    if ch:
        a = 0.9
        draw_text(c, ch, 40, 180, 34, GOLD, a, "serif", True, stroke=4, stroke_a=0.6)
        c.drawLine(40, 198, 40 + text_w(ch, 34, "serif", True), 198, paint(GOLD, 0.5, stroke=1.5))
    # 角标
    draw_text(c, "AI 配音", W - 40, 120, 24, (230, 230, 230), 0.7, "sans", False, "right", stroke=3, stroke_a=0.5)
    # 字幕
    for sb in T["subs"]:
        if sb["t0"] <= t < sb["t1"]:
            draw_subtitle(c, sb["text"], 1.0)
            break
    return surf


def to_rgb(surf):
    a = surf.makeImageSnapshot().toarray()  # BGRA
    return np.ascontiguousarray(a[..., [2, 1, 0]])


def still(ts):
    from PIL import Image
    os.makedirs(f"{WORK}/stills", exist_ok=True)
    for t in ts:
        t = float(t)
        Image.fromarray(to_rgb(frame(t))).save(f"{WORK}/stills/t_{t:07.2f}.jpg", quality=88)
        print("still", t)


def seg(i, n):
    total = T["total"]; nf = int(math.ceil(total * FPS))
    f0 = nf * i // n; f1 = nf * (i + 1) // n
    os.makedirs(f"{WORK}/seg", exist_ok=True)
    out = f"{WORK}/seg/seg_{i:02d}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_s = time.time()
    for f in range(f0, f1):
        surf = frame(f / FPS)
        pr.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
        if (f - f0) % 250 == 0:
            print(f"seg{i} {f - f0}/{f1 - f0} {time.time() - t_s:.0f}s", flush=True)
    pr.stdin.close(); pr.wait()
    print("done seg", i, f1 - f0, "frames", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        still(sys.argv[2:])
    elif sys.argv[1] == "seg":
        seg(int(sys.argv[2]), int(sys.argv[3]))
