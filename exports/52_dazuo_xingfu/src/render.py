# -*- coding: utf-8 -*-
"""时间线 + 逐帧渲染 + 并行编码。
usage:
  python render.py timeline            # 由配音时长生成 timeline.json / narration.srt
  python render.py frames  [t1 t2 ...]  # 抽帧预览 jpg
  python render.py video  OUT.mp4       # 渲染无声视频（4 进程并行，25fps 恒定帧率）
"""
import os, sys, json, re, math, subprocess, functools
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines, SCENES
from art import *
import scenes as SC

FPS = 25
WORK = os.environ.get("WORK", "/tmp/claude-0/work")
VOICE = os.environ.get("VOICE_DIR", f"{WORK}/tts/proc")
TL = f"{WORK}/timeline.json"
GAP = 0.50          # 句间停顿（VOICE_SPEC）
SCENE_GAP = 0.70    # 换场额外停顿
Q_PRE, Q_POST = 0.5, 1.4   # 经文前后多留
START = 0.25        # 第一句起点：首帧即钩子
TAIL = 4.0


def wav_dur(p):
    import soundfile as sf
    i = sf.info(p)
    return i.frames / i.samplerate


def build_timeline():
    lines = all_lines()
    t = START
    prev_scene = None
    out = []
    for d in lines:
        if prev_scene and d["scene"] != prev_scene:
            t += SCENE_GAP
        if d["k"] == "q":
            t += Q_PRE
        p = f"{VOICE}/{d['id']}.wav"
        dur = wav_dur(p) if os.path.exists(p) else len(d["tts"]) / 4.7
        out.append(dict(id=d["id"], scene=d["scene"], kind=d["kind"], say=d["say"], k=d["k"],
                        start=round(t, 3), end=round(t + dur, 3), dur=round(dur, 3)))
        t += dur + GAP + (Q_POST if d["k"] == "q" else 0)
        prev_scene = d["scene"]
    total = out[-1]["end"] + TAIL
    # 场景区间：从该场景第一句前（上一场景末句结束+0.25）到下一场景开始
    scenes = []
    for sid, kind, _ in SCENES:
        ls = [x for x in out if x["scene"] == sid]
        scenes.append(dict(id=sid, kind=kind, first=ls[0]["start"], last=ls[-1]["end"]))
    for i, s in enumerate(scenes):
        s["t0"] = 0.0 if i == 0 else round((scenes[i - 1]["last"] + s["first"]) / 2, 3)
    for i, s in enumerate(scenes):
        s["t1"] = scenes[i + 1]["t0"] if i + 1 < len(scenes) else total
    tl = dict(total=round(total, 3), lines=out, scenes=scenes)
    json.dump(tl, open(TL, "w"), ensure_ascii=False, indent=1)
    write_srt(tl, f"{WORK}/narration.srt")
    n = sum(len(re.sub(r"[，。？！：；、“”《》·\s]", "", x["say"])) for x in out)
    print(f"total {total:.1f}s = {total/60:.2f} min; {n} chars; {n/(out[-1]['end']-out[0]['start'])*60:.0f} chars/min")
    return tl


# ---------------------------------------------------------------- 字幕
PUNCT_END = "，。；：！？、"


def chunks_for(say):
    """切成每块 ≤ 30 字的字幕块，每块 ≤ 2 行。"""
    parts = re.findall(r"[^，。；：！？]+[，。；：！？]?", say)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= 30 or not cur:
            cur += p
        else:
            out.append(cur); cur = p
    if cur:
        out.append(cur)
    return out


def rows_for(chunk):
    s = chunk.rstrip("，。；：、")
    if len(s) <= 17:
        return [s]
    best, bi = 99, len(s) // 2
    for i, ch in enumerate(s):
        if ch in PUNCT_END + "“”" and 4 <= i + 1 <= len(s) - 3 and len(s) - i - 1 <= 18 and i + 1 <= 18:
            if abs(i + 1 - len(s) / 2) < best:
                best, bi = abs(i + 1 - len(s) / 2), i + 1
    if best > 8:
        bi = math.ceil(len(s) / 2)
    return [s[:bi].rstrip("，"), s[bi:]]


def subtitle_events(tl):
    ev = []
    for x in tl["lines"]:
        if x["k"] == "q":
            continue
        cs = chunks_for(x["say"])
        n = sum(len(c) for c in cs)
        t = x["start"]
        for c in cs:
            d = x["dur"] * len(c) / n
            ev.append((t, t + d, rows_for(c)))
            t += d
    return ev


def write_srt(tl, path):
    def ts(s):
        h, r = divmod(s, 3600); m, r = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int(round((r - int(r)) * 1000)):03d}"
    with open(path, "w") as f:
        for i, (a, b, rows) in enumerate(subtitle_events(tl)):
            f.write(f"{i+1}\n{ts(a)} --> {ts(b)}\n" + "\n".join(rows) + "\n\n")


@functools.lru_cache(maxsize=512)
def sub_sprite(row):
    return text_sprite(row, 52, "serif", "Bold", INK, 5, PAPER)


def draw_subs(img, t, ev):
    for a, b, rows in ev:
        if a - 0.02 <= t < b + 0.04:
            y = SC.SUB_Y + (0 if len(rows) == 2 else 36)
            band = Image.new("RGBA", (W, 190), PAPER + (150,))
            # 柔边底：上下渐隐
            m = np.ones((190, W), np.float32)
            m[:40] *= np.linspace(0, 1, 40)[:, None]; m[-40:] *= np.linspace(1, 0, 40)[:, None]
            band.putalpha(Image.fromarray((m * 150).astype(np.uint8)))
            img.alpha_composite(band, (0, SC.SUB_Y - 30))
            for i, r in enumerate(rows):
                put(img, sub_sprite(r), (W / 2, y + i * 72), 1.0, "mt")
            return


@functools.lru_cache(None)
def corner_tag():
    return text_sprite("AI 配音", 26, "serif", "Medium", GREY)


# ---------------------------------------------------------------- 帧
@functools.lru_cache(None)
def scene_bg(kind):
    return SC.SCENE_FUNCS[kind][0]()


@functools.lru_cache(None)
def paper_rgba():
    return paper_img(1).convert("RGBA")


def render_frame(tl, ev, t):
    sc = next(s for s in tl["scenes"] if s["t0"] <= t < s["t1"]) if t < tl["total"] else tl["scenes"][-1]
    L = [(x["start"] - sc["t0"], x["end"] - sc["t0"]) for x in tl["lines"] if x["scene"] == sc["id"]]
    lt = t - sc["t0"]
    dur = sc["t1"] - sc["t0"]
    img = scene_bg(sc["kind"]).copy()
    SC.SCENE_FUNCS[sc["kind"]][1](img, lt, L, dur)
    # 换场：淡入淡出到纸色（首场景首帧不淡入）
    k = 1.0
    if sc["t0"] > 0:
        k = min(k, ease(lt / 0.35))
    if sc is not tl["scenes"][-1]:
        k = min(k, ease((sc["t1"] - t) / 0.30))
    else:
        k = min(k, ease((tl["total"] - t) / 1.2))
    if k < 1:
        img = Image.blend(paper_rgba(), img, k)
    draw_subs(img, t, ev)
    put(img, corner_tag(), (40, 96), 0.75)
    return img.convert("RGB")


def frames(ts, outdir):
    tl = json.load(open(TL)); ev = subtitle_events(tl)
    os.makedirs(outdir, exist_ok=True)
    for t in ts:
        render_frame(tl, ev, t).save(f"{outdir}/f_{t:07.2f}.jpg", quality=88)


def render_range(args):
    i0, i1, out = args
    tl = json.load(open(TL)); ev = subtitle_events(tl)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", os.environ.get("CRF", "21"), "-pix_fmt", "yuv420p",
           "-r", str(FPS), "-g", "50", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(render_frame(tl, ev, i / FPS).tobytes())
    p.stdin.close(); p.wait()
    return out


def video(out):
    from multiprocessing import Pool
    tl = json.load(open(TL))
    n = int(round(tl["total"] * FPS))
    nw = int(os.environ.get("NPROC", 4))
    nseg = nw * 3
    bounds = [n * k // nseg for k in range(nseg + 1)]
    segdir = f"{WORK}/segs"; os.makedirs(segdir, exist_ok=True)
    jobs = [(bounds[k], bounds[k + 1], f"{segdir}/seg_{k:02d}.mp4") for k in range(nseg)]
    with Pool(nw) as pool:
        for r in pool.imap_unordered(render_range, jobs):
            print("done", r, flush=True)
    with open(f"{segdir}/list.txt", "w") as f:
        for _, _, s in jobs:
            f.write(f"file '{s}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{segdir}/list.txt", "-c", "copy", out], check=True)
    print("frames", n, "->", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        build_timeline()
    elif cmd == "frames":
        frames([float(x) for x in sys.argv[2:]], f"{WORK}/preview")
    elif cmd == "video":
        video(sys.argv[2])
