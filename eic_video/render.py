# -*- coding: utf-8 -*-
"""Timeline + frame composer + parallel renderer (1080x1920, 25 fps).

python render.py timeline              -> timeline.json from processed voice lines
python render.py still <t> [out.png]   -> one frame
python render.py sheet t1 t2 ...       -> contact sheet jpg of several times
python render.py range <f0> <f1> <out> -> worker: frames [f0,f1) to mp4 (intermediate quality)
python render.py all [workers]         -> picture.mp4
"""
import sys, os, json, re, subprocess, time, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import SCENES, all_lines
from art import W, H, new, comp, ease, fade
import kit

FPS = 25
WORK = "/tmp/claude-0/work"
PROC = f"{WORK}/tts/proc"
TL_PATH = f"{WORK}/timeline.json"
XF = 0.45
LEAD = 0.25
FIRST = 0.45
GAP = 0.5
QGAP = 0.35
SCENE_GAP = 1.0
TAIL = 4.5

import shots_s0, shots_s1, shots_s2, shots_s3, shots_s4, shots_s5, shots_s6
GROUPS = {}
for mod in (shots_s0, shots_s1, shots_s2, shots_s3, shots_s4, shots_s5, shots_s6):
    GROUPS.update(mod.GROUPS)
CUE2GROUP = {}
for gname, (fn, cues) in GROUPS.items():
    for c in cues:
        CUE2GROUP[c] = gname


def line_dur(d):
    p = f"{PROC}/{d['id']}.wav"
    if os.path.exists(p):
        import soundfile as sf
        info = sf.info(p)
        return info.frames / info.samplerate
    n = len(re.sub(r"[，。？！：；、“”《》·\s]", "", d["say"]))
    return n / 4.5


def build_timeline():
    t = FIRST
    lines = []
    prev_scene = None
    L = all_lines()
    scenes = {}
    for i, d in enumerate(L):
        if prev_scene is not None and d["scene"] != prev_scene:
            t += SCENE_GAP
        if d["scene"] not in scenes:
            scenes[d["scene"]] = t - (0 if d["scene"] == "s0" else 0.6)
        dur = line_dur(d)
        lines.append(dict(id=d["id"], scene=d["scene"], k=d["k"], cue=d["cue"], t=d["t"], q=d.get("q"),
                          start=round(t, 3), end=round(t + dur, 3)))
        g = GAP
        if d["k"] == "q" or (i + 1 < len(L) and L[i + 1]["k"] == "q"):
            g += QGAP
        t += dur + g
        prev_scene = d["scene"]
    total = lines[-1]["end"] + TAIL
    # groups
    groups = []
    for ln in lines:
        gname = CUE2GROUP.get(ln["cue"], "missing")
        cs = max(0.0, ln["start"] - LEAD) if ln["id"] != "s0_00" else 0.0
        if groups and groups[-1]["name"] == gname:
            groups[-1]["cues"][ln["cue"]] = round(cs - groups[-1]["start"], 3)
            groups[-1]["cues"]["__len__" + ln["cue"]] = round(ln["end"] - ln["start"], 3)
            groups[-1]["end"] = ln["end"]
        else:
            groups.append(dict(name=gname, start=round(cs, 3), end=ln["end"], cues={ln["cue"]: 0.0, "__len__" + ln["cue"]: round(ln["end"] - ln["start"], 3)}))
    tl = dict(fps=FPS, total=round(total, 3), lines=lines, groups=groups,
              scenes=[dict(id=s["id"], chapter=s["chapter"], start=round(scenes[s["id"]], 3)) for s in SCENES])
    json.dump(tl, open(TL_PATH, "w"), ensure_ascii=False, indent=1)
    return tl


_TL = None


def TL():
    global _TL
    if _TL is None:
        _TL = json.load(open(TL_PATH)) if os.path.exists(TL_PATH) else build_timeline()
    return _TL


def _group_at(t):
    gs = TL()["groups"]
    idx = 0
    for i, g in enumerate(gs):
        if g["start"] <= t:
            idx = i
    return idx


def _line_at(t):
    ls = TL()["lines"]
    cur = ls[0]
    for ln in ls:
        if ln["start"] - LEAD <= t:
            cur = ln
    return cur


def render_group(gi, t):
    g = TL()["groups"][gi]
    img = new((0, 0, 0, 255))
    fn = GROUPS.get(g["name"], (None,))[0]
    ctx = kit.G(t - g["start"], g["cues"], _line_at(t), t)
    if fn is None:
        kit.title_card(img, "[" + g["name"] + "]", ",".join(k for k in g["cues"] if not k.startswith("__")), y=800, size=60)
    else:
        fn(img, ctx)
    return img


def frame(t):
    tl = TL()
    gi = _group_at(t)
    g = tl["groups"][gi]
    img = render_group(gi, t)
    if gi > 0 and t - g["start"] < XF:
        prev = render_group(gi - 1, t)
        a = ease((t - g["start"]) / XF)
        prev.alpha_composite(fade(img, a) or new())
        img = prev
    # header
    sc = None
    for s in tl["scenes"]:
        if s["start"] <= t:
            sc = s
    if sc and sc["chapter"]:
        a = ease((t - sc["start"]) / 0.8)
        kit.header(img, sc["chapter"], a)
    kit.ai_tag(img)
    # subtitles
    ln = None
    ls = tl["lines"]
    for i, x in enumerate(ls):
        nxt = ls[i + 1]["start"] if i + 1 < len(ls) else tl["total"]
        if x["start"] - 0.05 <= t < min(x["end"] + 0.45, nxt - 0.02):
            ln = x
    if ln and ln["k"] != "q":
        chunks = kit.split_sub(ln["t"])
        if len(chunks) == 1:
            kit.subtitle(img, chunks[0])
        else:
            tot = sum(len(c) for c in chunks)
            pos = (t - ln["start"]) / max(0.1, ln["end"] - ln["start"]) * tot
            acc = 0
            sel = chunks[-1]
            for c in chunks:
                acc += len(c)
                if pos < acc:
                    sel = c; break
            kit.subtitle(img, sel)
    # final fade to black
    tail = tl["total"] - t
    if tail < 1.2:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ease(1 - tail / 1.2)))))
    return img.convert("RGB")


def still(t, out):
    frame(t).save(out)


def sheet(times, out, cols=4, scale=0.3):
    ims = [frame(t) for t in times]
    w, h = int(W * scale), int(H * scale)
    rows = math.ceil(len(ims) / cols)
    s = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
    for i, im in enumerate(ims):
        s.paste(im.resize((w, h), Image.BILINEAR), ((i % cols) * w, (i // cols) * h))
    s.save(out, quality=88)


def render_range(f0, f1, out):
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
        if (f - f0) % 250 == 0:
            print(f"[{f0}-{f1}] frame {f} {(time.time()-t0)/max(1,f-f0+1):.3f}s/f", flush=True)
    p.stdin.close(); p.wait()


def render_all(workers=4):
    tl = build_timeline()
    global _TL
    _TL = tl
    nf = int(math.ceil(tl["total"] * FPS))
    # balance by cost: the opening is expensive, give each worker equal frame counts but split opening first
    bounds = [int(nf * i / workers) for i in range(workers + 1)]
    procs = []
    os.makedirs(f"{WORK}/video", exist_ok=True)
    for i in range(workers):
        out = f"{WORK}/video/seg_{i:02d}.mp4"
        procs.append(subprocess.Popen([sys.executable, __file__, "range", str(bounds[i]), str(bounds[i + 1]), out]))
    for p in procs:
        p.wait()
    with open(f"{WORK}/video/list.txt", "w") as f:
        for i in range(workers):
            f.write(f"file 'seg_{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/video/list.txt",
                    "-c", "copy", f"{WORK}/video/picture.mp4"], check=True)
    print("picture done", nf, "frames")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        tl = build_timeline()
        print("total", tl["total"], "lines", len(tl["lines"]), "groups", len(tl["groups"]))
        missing = sorted({g["name"] for g in tl["groups"] if g["name"] == "missing"} |
                         {l["cue"] for l in tl["lines"] if l["cue"] not in CUE2GROUP})
        print("missing cues:", missing)
    elif cmd == "still":
        still(float(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else f"{WORK}/still.png")
    elif cmd == "sheet":
        sheet([float(x) for x in sys.argv[3:]], sys.argv[2])
    elif cmd == "range":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "all":
        render_all(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
