"""时间线 + 合成 + 并行渲染。
python render.py stills [t1 t2 ...]     -> 抽帧 jpg
python render.py video [nproc]          -> 分块渲染并拼接为无声 mp4
"""
import sys, os, json, re, math, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw
from base import *
import scenes
from script_data import all_lines

WK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WK}/tts/proc"
LEAD = 0.35         # 首句起点（首帧即画面，声音钩子从 0 开始）
TAIL = 3.0
XF = 0.5            # 场景交叉淡化
SUB_Y = 1515

CHAPTER = {"a": "", "b": "壹 · 入秦", "c": "贰 · 杠杆一：信用", "d": "叁 · 杠杆二：激励", "e": "肆 · 杠杆三：信息",
           "f": "伍 · 改革者之死", "g": "陆 · 余论"}


def est_dur(d):
    n = len(re.sub(r"[，。？！：；、“”《》\s·]", "", d["say"]))
    return n / 4.3


@functools.lru_cache(None)
def timeline():
    tl = json.load(open(f"{WK}/timeline.json")) if os.path.exists(f"{WK}/timeline.json") else None
    lines = all_lines()
    out = []
    t = LEAD
    for d in lines:
        if tl and d["id"] in tl:
            dur = tl[d["id"]]["dur"]
        elif os.path.exists(f"{PROC}/{d['id']}.wav"):
            import soundfile as sf
            dur = sf.info(f"{PROC}/{d['id']}.wav").duration
        else:
            dur = est_dur(d)
        out.append(dict(d, start=t, dur=dur))
        t += dur + d["gap"]
    total = t + TAIL
    # 场景段
    segs = []
    for i, d in enumerate(out):
        if not segs or segs[-1]["sc"] != d["sc"]:
            segs.append(dict(sc=d["sc"], start=0.0 if not segs else d["start"] - 0.15, lines=[]))
        segs[-1]["lines"].append(d)
    for i, s in enumerate(segs):
        s["end"] = segs[i + 1]["start"] if i + 1 < len(segs) else total
        s["ev"] = {d["id"]: (d["start"] - s["start"], d["dur"]) for d in s["lines"]}
    return out, segs, total


def scene_frame(seg, t):
    fn = scenes.SCENES[seg["sc"]]
    return fn(t - seg["start"], seg["end"] - seg["start"], seg["ev"])


# ── 字幕 ──
def sub_chunks(d):
    """长句按标点切成 ≤2 行的小段，按字数分配时间。"""
    f = font("sans", 52, "Medium")
    s = d["sub"]
    parts = re.findall(r"[^，。！？；：]+[，。！？；：]?", s)
    chunks, cur = [], ""
    for p in parts:
        if cur and len(balanced_wrap(cur + p, f, 940)) > 2:
            chunks.append(cur); cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    n = [max(1, len(c)) for c in chunks]
    tot = sum(n); t = d["start"]; out = []
    for c, k in zip(chunks, n):
        dt = d["dur"] * k / tot
        out.append((t, t + dt, c)); t += dt
    return out


@functools.lru_cache(None)
def sub_events():
    lines, _, _ = timeline()
    ev = []
    for i, d in enumerate(lines):
        ch = sub_chunks(d)
        if i == 0:
            ch[0] = (0.0, ch[0][1], ch[0][2])
        for j, (a, b, c) in enumerate(ch):
            # 最后一段延到下一句开始前（最多 +gap）
            if j == len(ch) - 1:
                b = b + min(d["gap"], 0.4)
            ev.append((a, b, c.rstrip("，。；：")))
    return ev


def draw_subs(img, t):
    f = font("sans", 52, "Medium")
    for a, b, c in sub_events():
        if a <= t < b:
            ls = balanced_wrap(c, f, 940)
            n = len(ls)
            for i, l in enumerate(ls):
                y = SUB_Y + (i - (n - 1) / 2) * 72
                img = draw_text(img, (W / 2, y), l, f, fill=(250, 246, 236), shadow=5, stroke=3, stroke_fill=(12, 10, 8))
            break
    return img


# ── 引文卡 ──
@functools.lru_cache(None)
def card_img(orig, src, bh):
    fo = font("serif", 62 if len(orig) <= 14 else 54 if len(orig) <= 28 else 46, "Black", tc=True)
    fs = font("serif", 32, "Medium", tc=True)
    fb = font("sans", 38, "Regular")
    lo = balanced_wrap(orig, fo, 880) if len(orig) <= 30 else wrap(orig, fo, 880)
    lb = wrap(bh, fb, 860)
    ls = wrap(src, fs, 880)
    lh_o, lh_b = fo.size * 1.35, 54
    h = int(70 + len(lo) * lh_o + 20 + len(ls) * 44 + 30 + len(lb) * lh_b + 60)
    w = 980
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=(12, 9, 7, 222), outline=GOLD + (200,), width=3)
    d.line([(40, 26), (w - 40, 26)], fill=GOLD + (120,), width=1)
    y = 70
    for l in lo:
        im = draw_text(im, (w / 2, y + fo.size * 0.4), l, fo, fill=GOLD2, shadow=0)
        y += lh_o
    y += 10
    for l in ls:
        im = draw_text(im, (w / 2, y + 12), l, fs, fill=(196, 180, 150), shadow=0)
        y += 44
    d = ImageDraw.Draw(im)
    d.line([(w / 2 - 120, y + 10), (w / 2 + 120, y + 10)], fill=GOLD + (140,), width=2)
    y += 40
    for l in lb:
        im = draw_text(im, (w / 2, y + 18), l, fb, fill=PAPER, shadow=0)
        y += lh_b
    return im


def draw_card(img, t):
    lines, _, _ = timeline()
    for i, d in enumerate(lines):
        if not d["card"]:
            continue
        a, b = d["start"] + 0.15, d["start"] + d["dur"] + d["gap"] + 0.6
        # 下一句无卡时多停留一会儿
        if i + 1 < len(lines) and not lines[i + 1]["card"]:
            b = min(b + 1.2, lines[i + 1]["start"] + lines[i + 1]["dur"])
        if a - 0.3 <= t < b:
            k = ramp(t, a - 0.3, 0.35) * (1 - ramp(t, b - 0.35, 0.35))
            im = card_img(*d["card"])
            dy = 18 * (1 - k)
            img = img.convert("RGBA") if img.mode != "RGBA" else img
            paste_center(img, im, W / 2, 300 + im.height / 2 + dy, alpha=k)
            return img
    return img


def draw_hook(img, t):
    """开场 0–3.6 秒：本期最强的一句结论，第一帧即在（不淡入）。"""
    lines, _, _ = timeline()
    end = lines[1]["start"] + 0.05
    if t >= end:
        return img
    a = 1 - ramp(t, end - 0.4, 0.4)
    img = draw_text(img, (W / 2, 420), "他改出了最强的秦国", font("serif", 74, "Black"), fill=PAPER, alpha=a, shadow=8)
    img = draw_text(img, (W / 2, 530), "却死在自己的法里", font("serif", 92, "Black"), fill=RED2, alpha=a, shadow=8)
    return img


def draw_chrome(img, t, seg):
    lines, _, _ = timeline()
    cid = seg["lines"][0]["id"][0]
    lab = CHAPTER.get(cid, "")
    if lab:
        img = draw_text(img, (40, 172), lab, font("serif", 36, "Bold"), fill=GOLD2, anchor="lm", shadow=4, alpha=0.92)
    img = draw_text(img, (W - 40, 172), "AI 配音", font("sans", 28, "Medium"), fill=(200, 190, 170), anchor="rm", shadow=3, alpha=0.75)
    return img


def frame(fi):
    lines, segs, total = timeline()
    t = fi / FPS
    si = max(i for i, s in enumerate(segs) if s["start"] <= t + 1e-9)
    seg = segs[si]
    img = scene_frame(seg, t)
    # 交叉淡化
    if si + 1 < len(segs) and t > segs[si + 1]["start"] - XF / 2:
        pass
    if si > 0 and t < seg["start"] + XF / 2 and segs[si - 1]["sc"] != "horses":
        prev = segs[si - 1]
        k = (t - (seg["start"] - XF / 2)) / XF
        a = scene_frame(prev, t)
        img = Image.blend(a.convert("RGB"), img.convert("RGB"), ease(k))
    img = img.convert("RGBA")
    img = draw_hook(img, t)
    img = draw_card(img, t)
    img = draw_subs(img, t)
    img = draw_chrome(img, t, seg)
    return finish(img.convert("RGB"), fi)


def render_chunk(args):
    i0, i1, path = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    for fi in range(i0, i1):
        p.stdin.write(frame(fi).tobytes())
    p.stdin.close(); p.wait()
    return path


if __name__ == "__main__":
    cmd = sys.argv[1]
    lines, segs, total = timeline()
    if cmd == "info":
        print(f"total {total:.1f}s  {total/60:.2f} min, {len(segs)} segs")
        for s in segs:
            print(f"{s['start']:7.1f} {s['end']-s['start']:6.1f} {s['sc']}")
    elif cmd == "stills":
        out = f"{WK}/stills"; os.makedirs(out, exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] or [s["start"] + (s["end"] - s["start"]) * 0.7 for s in segs]
        for t in ts:
            Image.fromarray(frame(int(t * FPS))).save(f"{out}/f_{t:07.2f}.jpg", quality=85)
        print("ok", len(ts))
    elif cmd == "video":
        from multiprocessing import Pool
        nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        N = int(total * FPS)
        out = f"{WK}/chunks"; os.makedirs(out, exist_ok=True)
        csz = 750
        jobs = [(i, min(N, i + csz), f"{out}/c_{i:06d}.mp4") for i in range(0, N, csz)]
        todo = [j for j in jobs if not os.path.exists(j[2] + ".done")]
        print("frames", N, "chunks", len(jobs), "todo", len(todo), flush=True)
        with Pool(nproc) as pool:
            for pth in pool.imap_unordered(render_chunk, todo):
                open(pth + ".done", "w").close(); print("done", pth, flush=True)
        with open(f"{out}/list.txt", "w") as f:
            for j in jobs:
                f.write(f"file '{j[2]}'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{out}/list.txt", "-c", "copy", f"{WK}/video_silent.mp4"], check=True)
        print("silent video ok")
