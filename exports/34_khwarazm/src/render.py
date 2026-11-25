"""Render frames. usage:
  python render.py still <t1> <t2> ...          -> stills/*.jpg
  python render.py seg <i> <n>                  -> video/seg_i.mp4 (frames i::n chunked contiguously)
  python render.py all [nproc]                  -> video/picture.mp4
"""
import sys, os, json, math, subprocess, bisect, time
import numpy as np, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import scenes as SC
WORK = "/tmp/claude-0/work"
TL = json.load(open(f"{WORK}/timeline.json"))
BEATS = TL["beats"]; LINES = {l["id"]: l for l in TL["lines"]}
STARTS = [b["start"] for b in BEATS]
CHUNKS = [ch for l in TL["lines"] for ch in l["chunks"]]
XF = 0.35

def beat_ctx(b, gt, fi):
    lines = {lid: (LINES[lid]["t0"] - b["start"], LINES[lid]["t1"] - b["start"]) for lid in b["lines"]}
    return SC.Ctx(gt - b["start"], b["end"] - b["start"], fi, lines, gt)

def draw_beat(c, b, gt, fi):
    getattr(SC, "v_" + b["v"])(c, beat_ctx(b, gt, fi))

def frame(gt, fi):
    surf = skia.Surface(W, H); c = surf.getCanvas()
    c.clear(skia.Color(12, 10, 8))
    i = max(0, bisect.bisect_right(STARTS, gt) - 1); b = BEATS[i]
    dt = gt - b["start"]
    if i > 0 and dt < XF:
        pb = BEATS[i - 1]
        draw_beat(c, pb, min(gt, pb["end"] - 1e-3), fi)
        c.saveLayerAlpha(skia.Rect(0, 0, W, H), int(255 * ease(dt / XF)))
        c.clear(skia.Color(12, 10, 8, 255)); draw_beat(c, b, gt, fi); c.restore()
    else:
        draw_beat(c, b, gt, fi)
    ismap = b["v"] in SC.MAPBEATS
    if ismap: vignette(c, 0.55)
    # header
    sc = b["scene"]
    if sc != "s0":
        ha = 1.0
        title = TL["titles"][sc]
        header(c, title, ha)
    badges(c, ismap)
    if b["v"] in ("storm", "caravan", "gate", "envoy", "indusleap", "indusflash", "sunzi4", "dilemma", "staghunt"):
        text(c, "情景示意", W - 52, 146, 28, "sansm", (220, 215, 200), 0.7, "r")
    # subtitles
    for t0, t1, s in CHUNKS:
        if t0 - 0.05 <= gt < t1 + 0.12:
            a = min(clamp((gt - t0 + 0.05) / 0.12), clamp((t1 + 0.12 - gt) / 0.12))
            subtitle(c, s, a); break
    grain(c, fi, 0.05)
    return surf

def still(ts, out=f"{WORK}/stills"):
    os.makedirs(out, exist_ok=True)
    for t in ts:
        t0 = time.time(); s = frame(float(t), int(float(t) * FPS))
        img = s.makeImageSnapshot(); arr = img.toarray(colorType=skia.kRGBA_8888_ColorType)
        from PIL import Image
        Image.fromarray(arr[..., :3]).save(f"{out}/f_{float(t):07.2f}.jpg", quality=88)
        print(t, f"{time.time()-t0:.2f}s", flush=True)

def seg(i, n):
    N = int(math.ceil(TL["total"] * FPS))
    a, b = N * i // n, N * (i + 1) // n
    os.makedirs(f"{WORK}/video", exist_ok=True)
    out = f"{WORK}/video/seg_{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                         stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(a, b):
        s = frame(fi / FPS, fi)
        arr = s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        p.stdin.write(arr.tobytes())
        if (fi - a) % 250 == 0: print(f"seg{i} {fi-a}/{b-a} {time.time()-t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print(f"seg{i} done {time.time()-t0:.0f}s", flush=True)

def all_(nproc):
    procs = [subprocess.Popen([sys.executable, __file__, "seg", str(i), str(nproc)]) for i in range(nproc)]
    for p in procs: p.wait()
    lst = f"{WORK}/video/list.txt"
    open(lst, "w").write("".join(f"file 'seg_{i:02d}.mp4'\n" for i in range(nproc)))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{WORK}/video/picture.mp4"], check=True)
    print("picture done")

if __name__ == "__main__":
    m = sys.argv[1]
    if m == "still": still(sys.argv[2:])
    elif m == "seg": seg(int(sys.argv[2]), int(sys.argv[3]))
    elif m == "all": all_(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
