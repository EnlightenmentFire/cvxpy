"""Render frames (multiprocess) and encode with ffmpeg.
usage: python render.py vertical|horizontal preview|final [start end]"""
import json, os, subprocess, sys, time
import numpy as np
from multiprocessing import Pool
import gfx as G
import core
from core import Layout, Ctx, UP, FPS, draw_dialogue
from scenes import SCENES

TL = json.load(open("timeline.json"))
TL["line_index"] = {k: tuple(v) for k, v in TL["line_index"].items()}
ENV = {k: np.array(v) for k, v in json.load(open("envelopes.json")).items()}
_L = None


def scene_at(T):
    for s in TL["scenes"]:
        if s["start"] <= T < s["end"]:
            return s
    return TL["scenes"][-1]


def active_line(T):
    lines = TL["lines"]
    for i, l in enumerate(lines):
        nxt = lines[i + 1]["start"] if i + 1 < len(lines) else 1e9
        hold_end = min(l["end"] + 0.45, nxt - 0.02)
        if l["start"] - 0.05 <= T < hold_end:
            return l
    return None


def render_frame(i):
    L = _L
    T = i / FPS
    sc = scene_at(T)
    ctx = Ctx(T, T - sc["start"], sc, TL, ENV, L)
    img = np.zeros((L.H, L.W, 3), np.uint8)
    SCENES[sc["scene"]](img, ctx)
    # camera shake
    dx, dy = ctx.shake
    if dx or dy:
        img = np.roll(np.roll(img, dy, 0), dx, 1)
    # scene fades (pixel dissolve) — black at cuts unless the scene asked for something else
    fade = None
    t_in, t_out = ctx.t, sc["end"] - T
    if ctx.fade is not None:
        fade = ctx.fade
    elif t_in < 0.3 and sc["scene"] != 1 or (sc["scene"] == 1 and t_in < 0.5):
        fade = ("black", 1 - t_in / (0.3 if sc["scene"] != 1 else 0.5))
    elif t_out < 0.25 and sc["scene"] not in (1, 8):
        fade = ("black", 1 - t_out / 0.25)
    if fade and fade[1] > 0:
        k = G.clamp(fade[1])
        th = np.tile(G.BAYER4, (L.H // 4 + 1, L.W // 4 + 1))[:L.H, :L.W]
        col = (255, 255, 255) if fade[0] == "white" else (0, 0, 0)
        img[th < k] = col
    layer = np.repeat(np.repeat(img, UP, 0), UP, 1)
    for f in ctx.pops:
        f(layer)
    if not ctx.hide_box:
        l = active_line(T)
        if l is not None:
            draw_dialogue(layer, L, l, T)
    return layer.tobytes()


def init(vertical):
    global _L
    _L = Layout(vertical)


def main():
    orient = sys.argv[1]
    mode = sys.argv[2]
    vertical = orient == "vertical"
    init(vertical)
    L = _L
    t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    t1 = float(sys.argv[4]) if len(sys.argv) > 4 else TL["total"]
    f0, f1 = int(t0 * FPS), int(t1 * FPS)
    lw, lh = L.W * UP, L.H * UP
    os.makedirs("out", exist_ok=True)
    if mode == "preview":
        out = f"out/preview_{orient}.mp4"
        vf = "null"
        venc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26"]
    else:
        out = f"out/final_{orient}.mp4"
        vf = "scale=iw*2:ih*2:flags=neighbor"
        venc = ["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-tune", "animation", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-x264-params", "keyint=60"]
    if len(sys.argv) > 3:
        out = out.replace(".mp4", f"_{t0:.0f}_{t1:.0f}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{lw}x{lh}", "-r", str(FPS), "-i", "-",
           "-ss", f"{t0:.3f}", "-t", f"{(f1 - f0) / FPS:.3f}", "-i", "audio/mix_final.wav",
           "-vf", vf + (",format=yuv420p" if mode == "preview" else ""), *venc,
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    st = time.time()
    with Pool(4, initializer=init, initargs=(vertical,)) as pool:
        for k, buf in enumerate(pool.imap(render_frame, range(f0, f1), chunksize=8)):
            p.stdin.write(buf)
            if k % 300 == 0:
                print(f"  frame {k}/{f1 - f0}  {time.time() - st:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", out, f"{time.time() - st:.0f}s")


if __name__ == "__main__":
    main()
