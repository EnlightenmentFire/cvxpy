# -*- coding: utf-8 -*-
"""合成每一帧：镜头 + 卡片 + 字幕 + 角标。
python render.py still T1 T2 ...        -> 输出预览 jpg
python render.py seg K N                -> 渲染第 K/N 段到 mp4（无声）
"""
import sys, os, re, math, subprocess
import numpy as np
import skia
from eng import *
import scenes
from scenes import SHOT, SHOT_FN, Ctx, shot_start, SECTION
from timeline import build

OUT = "/tmp/claude-0/w74/render"
os.makedirs(OUT, exist_ok=True)
LINES, TOTAL = build()

MAPSHOTS = {"map", "battle", "tide", "end"}


def chunks(s):
    """字幕切块：按标点切，每块不超过 ~30 字"""
    parts = re.findall(r"[^，。？！：；]+[，。？！：；]?", s)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > 30 and cur:
            out.append(cur); cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    return out


def strip_end(s):
    return s.rstrip("，。；：")


def draw_frame(c, T):
    ctx = Ctx(LINES, T)
    cur = ctx.cur
    sh = SHOT[cur["v"]]
    ss = shot_start(ctx, cur)
    # 镜头切换：交叉淡化 0.45s
    i = ctx.i
    prev = None
    if i > 0 and SHOT[LINES[i - 1]["v"]] != sh and T - ss < 0.45 and T >= ss:
        prev = LINES[i - 1]
    if prev is not None:
        pctx = Ctx(LINES, T); pctx.cur = prev; pctx.i = i - 1
        SHOT_FN[SHOT[prev["v"]]](c, pctx, T - shot_start(pctx, prev))
        c.saveLayerAlpha(None, int(255 * ease((T - ss) / 0.45)))
        SHOT_FN[sh](c, ctx, T - ss)
        c.restore()
    else:
        SHOT_FN[sh](c, ctx, T - ss)
    topbot_shade(c, 0.7, 0.9)
    vignette(c, 0.55)
    # ---- 卡片
    card_line, tt, hold_to = None, 0, 0
    for j in range(max(0, i - 1), i + 1):
        d = LINES[j]
        if not d["card"]:
            continue
        end = d["end"] + 0.35
        nxt = LINES[j + 1] if j + 1 < len(LINES) else None
        hold = d["card"]["t"] == "a" or (d["card"]["t"] == "q" and len(d["card"]["yuan"]) > 22)
        if nxt and not nxt["card"] and hold and nxt["scene"] == d["scene"]:
            end = nxt["end"] + 0.35
        if d["start"] <= T < end:
            card_line, tt, hold_to = d, T - d["start"], end
    if card_line:
        a = ease(tt / 0.4) * ease((hold_to - T) / 0.35)
        cd = card_line["card"]
        if cd["t"] == "q":
            quote_card(c, cd, a, y=1440, tt=tt)
        elif cd["t"] == "a":
            nxt = LINES[LINES.index(card_line) + 1]
            ba = ease((T - nxt["start"]) / 0.4)
            analogy_card(c, cd, a, y=1440, tt=tt, bias_a=ba)
        elif cd["t"] == "d":
            duizhao_card(c, cd["rows"], a, y=1440, tt=tt)
    # ---- 字幕
    d = cur
    if d["start"] <= T < d["end"] + 0.25:
        ch = chunks(d["sub"])
        tot = sum(len(x) for x in ch)
        acc = 0
        for k, x in enumerate(ch):
            t0 = d["start"] + d["dur"] * acc / tot
            acc += len(x)
            t1 = d["start"] + d["dur"] * acc / tot if k < len(ch) - 1 else d["end"] + 0.25
            if t0 <= T < t1:
                subtitle(c, strip_end(x), 1.0)
    corner(c, SECTION.get(cur["scene"], ""), 1.0 if sh in MAPSHOTS else 0.0)
    pass  # 不加颗粒：省码率


def frame_np(T):
    surf = skia.Surface(W, H)
    with surf as c:
        c.clear(C(0, 0, 0))
        draw_frame(c, T)
    img = surf.makeImageSnapshot()
    return img.toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]


def still(ts, tag=""):
    from PIL import Image
    for T in ts:
        a = frame_np(T)
        Image.fromarray(a).save(f"{OUT}/still_{tag}{T:07.2f}.jpg", quality=88)


def seg(k, n):
    nf = int(math.ceil(TOTAL * FPS))
    a, b = nf * k // n, nf * (k + 1) // n
    out = f"{OUT}/seg_{k:02d}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "1", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for f in range(a, b):
        p.stdin.write(np.ascontiguousarray(frame_np(f / FPS)).tobytes())
        if (f - a) % 250 == 0:
            print(f"seg{k} {f - a}/{b - a} {time.time() - t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        still([float(x) for x in sys.argv[2:]])
    elif sys.argv[1] == "seg":
        seg(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "v":
        # 按 v 标记取若干帧：v 名 + 句内偏移
        ev = {d["v"]: d for d in LINES}
        ts = []
        for x in sys.argv[2:]:
            v, off = (x.split("@") + ["0.6"])[:2]
            ts.append(ev[v]["start"] + float(off) * (ev[v]["dur"] if float(off) <= 1 else 1))
        still(ts)
