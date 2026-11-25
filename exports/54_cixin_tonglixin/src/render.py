# -*- coding: utf-8 -*-
"""时间线 + 合成 + 渲染。
python render.py timeline            # 由 tts/proc 生成 timeline.json（无配音时按字数估算）
python render.py stills [scene...]   # 每场景抽帧预览
python render.py video               # 4 进程并行渲染无声视频 out/video.mp4
"""
import sys, os, json, math, re, subprocess
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art import *
import scenes as SC
from script_data import all_lines

WK = "/tmp/claude-0/work"
PROC = f"{WK}/tts/proc"
FPS = 25
LEAD = 0.5           # 第一句开始前（磬声先响）
SCENE_LEAD = 0.25    # 场景先于其首句出现
XFADE = 0.35
TAIL = 2.6           # 末句后留白


def build_timeline():
    import soundfile as sf
    lines = all_lines()
    t = LEAD
    tl = []
    for d in lines:
        p = f"{PROC}/{d['id']}.wav"
        if os.path.exists(p):
            info = sf.info(p); dur = info.frames / info.samplerate; est = False
        else:
            n = len(re.sub(r"[，。？！：；、“”《》·\s]", "", d["say"])); dur = n / 4.7; est = True
        tl.append(dict(id=d["id"], scene=d["scene"], start=round(t, 3), end=round(t + dur, 3), sub=d["sub"], est=est))
        t += dur + d["pause"]
    total = tl[-1]["end"] + TAIL
    # 场景区间
    sc = []
    for x in tl:
        if not sc or sc[-1]["scene"] != x["scene"] or sc[-1].get("closed"):
            sc.append(dict(scene=x["scene"], start=max(0.0, x["start"] - SCENE_LEAD), lines=[x["start"]]))
        else:
            sc[-1]["lines"].append(x["start"])
    sc[0]["start"] = 0.0
    for i, s in enumerate(sc):
        s["end"] = sc[i + 1]["start"] if i + 1 < len(sc) else total
    J = dict(total=total, lines=tl, scenes=sc)
    json.dump(J, open(f"{WK}/timeline.json", "w"), ensure_ascii=False, indent=1)
    return J


def load_tl():
    return json.load(open(f"{WK}/timeline.json"))


_cache = {}


def scene_fn(i, J):
    if i not in _cache:
        s = J["scenes"][i]
        ctx = dict(dur=s["end"] - s["start"], lt=[l - s["start"] for l in s["lines"]])
        _cache[i] = SC.SCENES[s["scene"]](ctx)
        if len(_cache) > 4:
            for k in list(_cache)[:-4]:
                if k != i:
                    _cache.pop(k, None)
    return _cache[i]


def chunks(sub):
    """把一句字幕切成每屏 ≤16 字的小段（尽量在标点处断）。"""
    s = sub.strip()
    parts = re.split(r"(?<=[，。；：！？])", s)
    out = []
    for p in parts:
        if not p: continue
        while len(p) > 17:
            cut = 16
            for j in range(16, 9, -1):
                if p[j - 1] in "、，的和是在": cut = j; break
            out.append(p[:cut]); p = p[cut:]
        if out and len(out[-1]) + len(p) <= 15 and not out[-1].endswith(("。", "？", "！", "；")):
            out[-1] += p
        else:
            out.append(p)
    return [o for o in out if o.strip()]


def sub_at(t, J):
    for x in J["lines"]:
        if x["start"] - 0.05 <= t < x["end"] + 0.15:
            cs = chunks(x["sub"])
            n = [len(c) for c in cs]; tot = sum(n)
            u = (t - x["start"]) / max(1e-3, x["end"] - x["start"])
            acc = 0
            for c, k in zip(cs, n):
                acc += k / tot
                if u < acc + 1e-6:
                    return c
            return cs[-1]
    return None


def strip_punct(s):
    return re.sub(r"[，。；：、]$", "", s)


def overlay_ui(im, theme, scene, t, J):
    d = ImageDraw.Draw(im)
    light = theme == "light"
    fg = (60, 56, 52) if light else (200, 204, 212)
    # 系列名 & AI 配音角标
    f = font("sans", 28, 500)
    d.text((70, 200), "佛法与心智 · 静坐的科学", font=f, fill=fg)
    tw, _ = text_size("AI 配音", f)
    d.rounded_rectangle((W - 70 - tw - 24, 194, W - 70, 240), 10, outline=fg, width=2)
    d.text((W - 70 - tw - 12, 200), "AI 配音", font=f, fill=fg)
    # 区段标题 & 证据标签
    sec = None
    for s in J["scenes"]:
        if s["start"] <= t and SC.SECTION.get(s["scene"]) is not None:
            sec = SC.SECTION[s["scene"]]
        if s["scene"] in ("hook", "dawn") and s["start"] <= t:
            sec = None if s["scene"] == "hook" else None
    if sec:
        d.text((70, 262), sec, font=font("serif", 34, 700), fill=fg)
    tag = SC.TAG.get(scene)
    if tag:
        txt, col = tag
        ff = font("sans", 28, 600)
        tw, _ = text_size(txt, ff)
        x1 = W - 70; x0 = x1 - tw - 32
        d.rounded_rectangle((x0, 260, x1, 306), 10, fill=col)
        d.text((x0 + 16, 264), txt, font=ff, fill=(252, 248, 240))
    # 字幕
    s = sub_at(t, J)
    if s:
        s = strip_punct(s)
        ff = font("sans", 54, 600)
        tw, th = text_size(s, ff)
        x = (W - tw) / 2; y = 1450
        if light:
            d.text((x, y), s, font=ff, fill=(28, 26, 26), stroke_width=5, stroke_fill=(246, 240, 228))
        else:
            d.text((x, y), s, font=ff, fill=(250, 248, 242), stroke_width=5, stroke_fill=(10, 12, 16))
    return im


def frame(t, J):
    sc = J["scenes"]
    i = max(k for k, s in enumerate(sc) if s["start"] <= t + 1e-6)
    theme, fn = scene_fn(i, J)
    im = fn(t - sc[i]["start"]).convert("RGBA")
    if i > 0 and t - sc[i]["start"] < XFADE:
        th0, fn0 = scene_fn(i - 1, J)
        prev = fn0(t - sc[i - 1]["start"]).convert("RGBA")
        im = Image.blend(prev, im, ease((t - sc[i]["start"]) / XFADE))
    im = overlay_ui(im, theme, sc[i]["scene"], t, J)
    return im.convert("RGB")


def stills(names):
    J = load_tl()
    os.makedirs(f"{WK}/stills", exist_ok=True)
    for i, s in enumerate(J["scenes"]):
        if names and s["scene"] not in names: continue
        for frac in (0.3, 0.92):
            t = s["start"] + (s["end"] - s["start"]) * frac
            frame(t, J).resize((540, 960)).save(f"{WK}/stills/{i:02d}_{s['scene']}_{int(frac*100)}.jpg", quality=85)
        print(i, s["scene"], round(s["end"] - s["start"], 1), flush=True)


def render_chunk(args):
    k, f0, f1 = args
    J = load_tl()
    out = f"{WK}/out/part_{k:02d}.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(frame(fi / FPS, J).tobytes())
        if (fi - f0) % 500 == 0:
            print(f"chunk {k}: {fi - f0}/{f1 - f0}", flush=True)
    p.stdin.close(); p.wait()
    return out


def video(nproc=4):
    J = load_tl()
    os.makedirs(f"{WK}/out", exist_ok=True)
    N = int(math.ceil(J["total"] * FPS))
    # 按场景边界切块，块数多于进程数以均衡
    nchunks = nproc * 3
    edges = [int(N * i / nchunks) for i in range(nchunks + 1)]
    jobs = [(k, edges[k], edges[k + 1]) for k in range(nchunks)]
    with Pool(nproc) as pool:
        parts = pool.map(render_chunk, jobs, chunksize=1)
    with open(f"{WK}/out/parts.txt", "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/out/parts.txt", "-c", "copy",
                    f"{WK}/out/video.mp4"], check=True)
    print("frames", N, "dur", N / FPS)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        J = build_timeline(); print("total", round(J["total"], 1), "s;", len(J["scenes"]), "scenes; est lines:", sum(x["est"] for x in J["lines"]))
    elif cmd == "stills":
        stills(sys.argv[2:])
    elif cmd == "video":
        video(int(os.environ.get("NPROC", 4)))
