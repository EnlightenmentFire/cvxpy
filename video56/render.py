# -*- coding: utf-8 -*-
"""时间线 + 叠加层（标题、分类角标、字幕、AI 标识）+ 渲染。
usage:
  python render.py stills t1 t2 ...        -> preview/still_<t>.jpg
  python render.py seg <i> <n>             -> 第 i/n 段视频（无声）
"""
import sys, os, json, re, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art import *
from script_data import SCENES, all_lines
import visuals

FPS = 25
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
TL_PATH = f"{WORK}/timeline.json"
LEAD = 0.5
XF = 0.45     # 场景交叉淡化


def est_dur(d):
    n = len(re.sub(r"[^一-鿿0-9A-Za-z]", "", d["say"]))
    return n / (3.4 if d.get("slow") else 4.4)


def load_timeline():
    if os.path.exists(TL_PATH):
        return json.load(open(TL_PATH))
    # 估算版（TTS 完成前做样张用）
    t = LEAD
    out = []
    for d in all_lines():
        dur = est_dur(d)
        out.append(dict(id=d["id"], start=t, end=t + dur))
        t += dur + d["gap"]
    return dict(lines=out, total=t + 1.0)


TL = load_timeline()
LINES = all_lines()
for d, tl in zip(LINES, TL["lines"]):
    assert d["id"] == tl["id"]
    d["start"], d["end"] = tl["start"], tl["end"]
TOTAL = TL["total"]

SC = []
for s in SCENES:
    ls = [d for d in LINES if d["scene"] == s["id"]]
    SC.append(dict(s, L=ls))
for i, s in enumerate(SC):
    s["t0"] = 0.0 if i == 0 else SC[i - 1]["t1"]
    s["t1"] = (SC[i + 1]["L"][0]["start"] - 0.15) if i + 1 < len(SC) else TOTAL


# ---------------------------------------------------------------- 字幕切分
def split_sub(text, maxc=17):
    text = text.replace("“", "「").replace("”", "」")
    parts = re.findall(r"[^，。；：？！、]+[，。；：？！、]?", text)
    rows, cur = [], ""
    for p in parts:
        core = p
        if len(cur) + len(core.rstrip("，。；：、")) <= maxc:
            cur += core
        else:
            if cur:
                rows.append(cur)
            while len(core.rstrip("，。；：？！、")) > maxc + 1:
                rows.append(core[:maxc]); core = core[maxc:]
            cur = core
    if cur:
        rows.append(cur)
    clean = [re.sub(r"[，。；：、]+$", "", r).replace("，", " ").replace("；", " ").replace("：", " ").replace("、", " ").replace("。", " ") for r in rows]
    segs = []
    i = 0
    while i < len(clean):
        if i + 1 < len(clean) and len(clean[i]) + len(clean[i + 1]) <= 30:
            segs.append(clean[i] + "\n" + clean[i + 1]); i += 2
        else:
            segs.append(clean[i]); i += 1
    return segs


SUBS = []  # (start, end, text)
for d in LINES:
    if not d.get("sub"):
        continue
    segs = split_sub(d["sub"])
    n = [max(1, len(s.replace("\n", ""))) for s in segs]
    tot = sum(n)
    t = d["start"]
    span = d["end"] - d["start"]
    for s, k in zip(segs, n):
        dt = span * k / tot
        SUBS.append((t, t + dt, s))
        t += dt


def sub_at(T):
    for a, b, s in SUBS:
        if a - 0.05 <= T < b + 0.25:
            # 下一条开始就切换
            return s, a, b
    return None, 0, 0


TAG_COL = {"实证": JADE, "理论修正": GOLD, "实证 · 有复现争议": (214, 150, 80), "实证 · 小样本": (214, 150, 80),
           "类比": (140, 160, 200), "教义介绍": (200, 110, 90), "后续修正": GOLD}


def tag_img(tag):
    col = TAG_COL.get(tag, GREY)
    t = text_img(tag, "sansb", 34, (16, 16, 20))
    w, h = t.width + 44, t.height + 14
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=col + (240,))
    over(im, t, (w // 2, h // 2))
    return im


def overlays(im, T, sc):
    # AI 标识
    over(im, text_img("AI 配音 · 画面为程序生成示意", "sans", 26, (170, 164, 154)), (40, 46), 0.75, anchor="lt")
    # 标题
    if sc["title"]:
        a = ease((T - sc["t0"]) / 0.6)
        tt = text_img(sc["title"], "serif", 46, GOLD, shadow=3)
        over(im, tt, (W // 2, 160), a)
        d = ImageDraw.Draw(im)
        y = 160
        hw = tt.width // 2 + 30
        c = GOLD + (int(150 * a),)
        d.line((W // 2 - hw - 120, y, W // 2 - hw, y), fill=c, width=2)
        d.line((W // 2 + hw, y, W // 2 + hw + 120, y), fill=c, width=2)
    # 角标：当前句的 tag
    cur = None
    for d_ in sc["L"]:
        if d_["start"] - 0.1 <= T:
            cur = d_
    if cur is not None and cur.get("tag") and T < cur["end"] + cur["gap"] + 0.2:
        over(im, tag_img(cur["tag"]), (W // 2, 238), 0.95)
    # 字幕
    s, a, b = sub_at(T)
    if s:
        k = min(ease((T - a + 0.05) / 0.15), 1.0)
        si = text_img(s, "sans", 54, (250, 248, 242), stroke=3, stroke_color=(10, 10, 12), spacing=14, shadow=4)
        over(im, si, (W // 2, 1560), k)


def scene_ctx(sc, T):
    t = T - sc["t0"]
    lines = [dict(l, start=l["start"] - sc["t0"], end=l["end"] - sc["t0"]) for l in sc["L"]]
    li = 0
    for i, l in enumerate(lines):
        if t >= l["start"] - 0.05:
            li = i
    return dict(t=t, dur=sc["t1"] - sc["t0"], lines=lines, li=li, scene=sc,
                lt=t - lines[li]["start"], ld=lines[li]["end"] - lines[li]["start"])


def scene_frame(sc, T):
    return visuals.VISUALS[sc["visual"]](scene_ctx(sc, T))


def frame(T):
    idx = 0
    for i, s in enumerate(SC):
        if s["t0"] <= T:
            idx = i
    sc = SC[idx]
    im = scene_frame(sc, T)
    # 与上一场景交叉淡化
    if idx > 0 and T - sc["t0"] < XF:
        prev = scene_frame(SC[idx - 1], T)
        im = Image.blend(prev, im, ease((T - sc["t0"]) / XF))
    # 片尾淡出（只淡画面里的光，不黑场到底）
    if T > TOTAL - 1.2:
        im = Image.blend(im, Image.new("RGBA", (W, H), INK + (255,)), 0.5 * ease((T - (TOTAL - 1.2)) / 1.2))
    overlays(im, T, sc)
    return im.convert("RGB")


def main():
    mode = sys.argv[1]
    if mode == "stills":
        os.makedirs(f"{HERE}/preview", exist_ok=True)
        for a in sys.argv[2:]:
            T = float(a)
            frame(T).save(f"{HERE}/preview/still_{T:07.2f}.jpg", quality=88)
            print("still", T, flush=True)
    elif mode == "seg":
        i, n = int(sys.argv[2]), int(sys.argv[3])
        nf = int(math.ceil(TOTAL * FPS))
        # 按成本均衡：简单等分
        f0, f1 = nf * i // n, nf * (i + 1) // n
        out = f"{WORK}/seg_{i:02d}.mp4"
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
                              "-r", str(FPS), out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            p.stdin.write(frame(f / FPS).tobytes())
            if (f - f0) % 250 == 0:
                print(f"seg{i} {f - f0}/{f1 - f0}", flush=True)
        p.stdin.close(); p.wait()
        print("done", out, flush=True)
    elif mode == "info":
        print("total", TOTAL)
        for s in SC:
            print(s["id"], round(s["t0"], 1), round(s["t1"], 1), s["visual"])


if __name__ == "__main__":
    main()
