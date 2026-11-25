# -*- coding: utf-8 -*-
"""Timeline + frame compositor + parallel renderer.
python render.py still <t1> <t2> ...     -> preview/still_<t>.jpg
python render.py chunk <i> <n>           -> out/chunk_<i>.mp4
"""
import sys, os, json, math, re, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art import *
import scenes as SC

D = os.path.dirname(os.path.abspath(__file__))
FPS = 25
TL = json.load(open(f"{D}/timeline.json"))
LINES = TL["lines"]
TOTAL = TL["total"]

# scene spans: from first line start (minus lead) to next scene start
SPANS = []
for i, l in enumerate(LINES):
    if i == 0 or l["scene"] != LINES[i - 1]["scene"]:
        SPANS.append(dict(scene=l["scene"], t0=0.0 if i == 0 else l["start"] - 0.25, lines=[]))
    SPANS[-1]["lines"].append(l)
for k, s in enumerate(SPANS):
    s["t1"] = SPANS[k + 1]["t0"] if k + 1 < len(SPANS) else TOTAL


def split_sub(text, maxc=15):
    """Split subtitle into display chunks of <= ~2 rows of maxc chars, breaking at punctuation."""
    parts = re.split(r"(?<=[，。；：？！、])", text)
    parts = [p for p in parts if p.strip()]
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= maxc * 2 - 2 or not cur:
            cur += p
        else:
            chunks.append(cur); cur = p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        while len(c) > maxc * 2:
            out.append(c[:maxc * 2]); c = c[maxc * 2:]
        out.append(c)
    return out


def wrap2(c, maxc=15):
    c = c.rstrip("，。；：、")
    if len(c) <= maxc:
        return c
    # break near middle at punctuation if possible
    mid = len(c) // 2
    best = None
    for k in range(len(c)):
        if c[k] in "，；：、？！" and 3 <= k + 1 <= len(c) - 2:
            if best is None or abs(k + 1 - mid) < abs(best - mid):
                best = k + 1
    if best is None or abs(best - mid) > 6:
        best = mid
    return c[:best] + "\n" + c[best:]


SUBFONT = font("kai", 60)
MAXW = 900


def tw(s):
    return SUBFONT.getlength(s)


import jieba
jieba.setLogLevel(60)
for _w in ["享乐跑步机", "慈心禅", "四无量心", "主动对照", "效应量", "拓展与建构", "发表偏差", "心不在焉", "约翰斯·霍普金斯", "芭芭拉·弗雷德里克森", "诚实话", "醒着", "智者大师", "修行人", "企业员工", "密集禅修", "每个人", "当心炒作", "心理科学视角", "别的活动", "教人", "弗雷德里克森", "不快乐"]:
    jieba.add_word(_w)
PUNCT = "，。；：？！、」）"


def tokens(text):
    out = []
    for w in jieba.cut(text, HMM=False):
        if out and (w[0] in PUNCT or (out[-1][-1] in "「（《" )):
            out[-1] += w
        else:
            out.append(w)
    # glue non-Han tokens (numbers, %, ·, spaces, latin) to neighbours
    g = []
    i = 0
    while i < len(out):
        w = out[i]
        if g and g[-1][-1] not in PUNCT and (all(not ('\u4e00' <= ch <= '\u9fff') for ch in w) or g[-1][-1] in "·" or w[0] in "·%"):
            g[-1] += w
            if i + 1 < len(out) and all(not ('\u4e00' <= ch <= '\u9fff') for ch in w) and w.strip() and w.strip()[-1] not in PUNCT:
                g[-1] += out[i + 1]; i += 1
        else:
            g.append(w)
            if all(not ('\u4e00' <= ch <= '\u9fff') for ch in w) and w.strip() and i + 1 < len(out) and out[i + 1][0] not in PUNCT:
                j = i + 1
                while j < len(out) and all(not ('\u4e00' <= ch <= '\u9fff') for ch in out[j]):
                    g[-1] += out[j]; j += 1
                if j < len(out):
                    g[-1] += out[j]
                i = j
        i += 1
    out = g
    # keep 「 《 attached to following token
    res = []
    for w in out:
        if res and res[-1] and res[-1][-1] in "「《（":
            res[-1] += w
        else:
            res.append(w)
    return res


def balance(toks, nrows):
    """split token list into nrows rows minimizing max width, prefer punctuation."""
    if nrows == 1:
        return ["".join(toks)]
    tot = tw("".join(toks)); target = tot / nrows
    best, bs = None, 1e18
    acc = ""
    for k in range(1, len(toks)):
        acc += toks[k - 1]
        w = tw(acc)
        if w > MAXW:
            break
        rest = toks[k:]
        if tw("".join(rest)) > MAXW * (nrows - 1):
            continue
        sc = abs(w - target) - (0.35 * target if acc[-1] in PUNCT else 0)
        if acc[-1] not in PUNCT and (len(toks[k - 1]) == 1 or len(toks[k]) == 1):
            sc += 0.25 * target
        if acc.rstrip()[-1:].isdigit() or acc[-1] == " " or acc.count("《") > acc.count("》"):
            continue
        if acc.count("「") > acc.count("」"):
            sc += 0.6 * target
        if sc < bs:
            best, bs = k, sc
    if best is None:
        return None
    nxt = balance(toks[best:], nrows - 1)
    return None if nxt is None else ["".join(toks[:best])] + nxt


def layout_sub(text):
    import math as _m
    text = text.strip()
    # clause-level chunks of <= 2 rows
    clauses = [c for c in re.split(r"(?<=[，。；：？！])", text) if c]
    chunks, cur = [], ""
    for c in clauses:
        if tw(cur + c) <= MAXW * 1.9 or not cur:
            cur += c
        else:
            chunks.append(cur); cur = c
    if cur:
        chunks.append(cur)
    out = []
    for ch in chunks:
        toks = tokens(ch)
        n = max(1, _m.ceil(tw(ch) / MAXW))
        rows = balance(toks, n)
        while (rows is None or max(tw(x) for x in rows) > MAXW) and n < 6:
            n += 1; rows = balance(toks, n)
        rows = [x for x in rows if x.strip()]
        for i in range(0, len(rows), 2):
            pair = rows[i:i + 2]
            if len(pair) == 2:
                out.append(pair[0].rstrip("，、") + "\n" + pair[1])
            else:
                out.append(pair[0])
    return out


SUBS = []
for l in LINES:
    chunks = layout_sub(l["sub"])
    n = sum(len(c) for c in chunks)
    t = l["start"]
    for c in chunks:
        dt = l["dur"] * len(c) / n
        SUBS.append(dict(t0=t, t1=t + dt, text=c.rstrip("。，；"), kind=l["kind"]))
        t += dt
# extend each subtitle to next start (max +0.4 s) to avoid flicker
for i, s in enumerate(SUBS):
    nxt = SUBS[i + 1]["t0"] if i + 1 < len(SUBS) else TOTAL
    s["t1"] = min(nxt, s["t1"] + 0.4)


@functools.lru_cache(maxsize=256)
def sub_img(text):
    ti = text_img(text, "kai", 60, INK, spacing=16)
    bg = Image.new("RGBA", (max(ti.width + 90, 400), ti.height + 46), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 26, fill=(246, 241, 229, 228))
    bg.alpha_composite(ti, ((bg.width - ti.width) // 2, 23))
    return bg


@functools.lru_cache(maxsize=64)
def chip_img(txt):
    ti = text_img(txt, "serif", 34, (250, 244, 232))
    bg = Image.new("RGBA", (ti.width + 44, ti.height + 18), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 14, fill=(60, 56, 50, 220))
    bg.alpha_composite(ti, (22, 9))
    return bg


@functools.lru_cache(maxsize=64)
def tag_img(txt, dark):
    return text_img(txt, "serif", 36, (225, 216, 196) if dark else INK2)


@functools.lru_cache(maxsize=64)
def src_img(txt, dark):
    return text_img(txt, "serif_r", 28, (190, 182, 166) if dark else GREY)


@functools.lru_cache(maxsize=2)
def ai_img(dark):
    ti = text_img("AI 配音 · 画面示意", "serif_r", 26, (200, 192, 176) if dark else GREY)
    return ti


@functools.lru_cache(maxsize=1)
def help_img():
    ti = text_img("如有困扰，请寻求专业帮助", "serif", 32, (250, 244, 232))
    bg = Image.new("RGBA", (ti.width + 40, ti.height + 16), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, bg.width - 1, bg.height - 1], 12, fill=RED + (215,))
    bg.alpha_composite(ti, (20, 8))
    return bg


DARK = {"yz", "jgj", "tj"}


def frame(t):
    k = 0
    while k + 1 < len(SPANS) and SPANS[k + 1]["t0"] <= t:
        k += 1
    sp = SPANS[k]
    lt = t - sp["t0"]
    ev = [(l["start"] - sp["t0"], l["start"] + l["dur"] - sp["t0"], l["sub"]) for l in sp["lines"]]
    im = SC.SCENES[sp["scene"]](lt, sp["t1"] - sp["t0"], ev)
    # crossfade from previous scene (0.35 s)
    if k > 0 and lt < 0.35:
        pv = SPANS[k - 1]
        plt = t - pv["t0"]
        pev = [(l["start"] - pv["t0"], l["start"] + l["dur"] - pv["t0"], l["sub"]) for l in pv["lines"]]
        prev = SC.SCENES[pv["scene"]](plt, pv["t1"] - pv["t0"], pev)
        im = Image.blend(prev, im, ease(lt / 0.35))
    dark = sp["scene"] in DARK
    tag, chip, src = SC.META.get(sp["scene"], (None, None, None))
    if tag:
        im.alpha_composite(tag_img(tag, dark), (60, 92))
    im.alpha_composite(ai_img(dark), (W - ai_img(dark).width - 50, 98))
    if chip:
        c = chip_img(chip)
        im.alpha_composite(c, (60, 150))
    if src:
        s = src_img(src, dark)
        im.alpha_composite(s, ((W - s.width) // 2, 1800))
    if sp["scene"] in SC.HELP_SCENES:
        h = help_img()
        im.alpha_composite(h, ((W - h.width) // 2, 1730))
    # subtitles
    for s in SUBS:
        if s["t0"] <= t < s["t1"]:
            si = sub_img(s["text"])
            a = min(1.0, (t - s["t0"]) / 0.12, (s["t1"] - t) / 0.12)
            paste_c(im, si, W / 2, 1590, a)
            break
    return im.convert("RGB")


def render_chunk(i, n, out):
    nf = int(math.ceil(TOTAL * FPS))
    a, b = nf * i // n, nf * (i + 1) // n
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - a) % 500 == 0:
            print(f"chunk {i}: {f - a}/{b - a}", flush=True)
    p.stdin.close(); p.wait()
    print(f"chunk {i} done frames {a}-{b}", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        os.makedirs(f"{D}/preview", exist_ok=True)
        for ts in sys.argv[2:]:
            frame(float(ts)).save(f"{D}/preview/still_{float(ts):07.2f}.jpg", quality=88)
    elif sys.argv[1] == "scenes":
        os.makedirs(f"{D}/preview", exist_ok=True)
        for s in SPANS:
            t = s["t0"] + min(0.75 * (s["t1"] - s["t0"]), 6.0)
            frame(t).save(f"{D}/preview/sc_{s['t0']:07.2f}_{s['scene']}.jpg", quality=85)
    elif sys.argv[1] == "chunk":
        i, n = int(sys.argv[2]), int(sys.argv[3])
        os.makedirs(f"{D}/out", exist_ok=True)
        render_chunk(i, n, f"{D}/out/chunk_{i:02d}.mp4")
