"""Render the film from timeline.json.

  python3 render.py preview [TIMELINE]        # one frame per shot -> contact sheet
  python3 render.py shots [ids...]            # render shot segments (parallel) -> SEG/<id>.mp4
  python3 render.py concat                    # concat segments -> picture.mp4
"""
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import engine as E  # noqa: E402

SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
EDIT = os.path.join(SCR, "edit")
SEG = os.path.join(SCR, "segments")
FADE_IN = {"timeline": 0.3, "section": 0.4, "surfacing": 0.5, "vote": 0.4, "split": 0.4, "ending": 0.6, "u2": 0.0}

_TL = None
_SCN = None


def _init(tl_path):
    global _TL, _SCN
    E.SS = 1
    _TL = json.load(open(tl_path))
    import scenes2
    _SCN = scenes2


def shot_at(T):
    for sh in _TL["shots"]:
        if sh["start"] <= T < sh["end"]:
            return sh
    return _TL["shots"][-1]


def sub_at(T):
    for s in _TL["subs"]:
        if s["start"] <= T < s["end"]:
            return s
    return None


def frame(i):
    T = (i + 0.5) / _TL["fps"]
    sh = shot_at(T)
    t = T - sh["start"]
    D = sh["end"] - sh["start"]
    cues = {k: tuple(v) for k, v in sh["cues"].items()}
    img = getattr(_SCN, sh["fn"])(t, D, cues)
    fi = FADE_IN.get(sh["id"], 0.0)
    if fi > 0 and t < fi:
        img = img * E.ease_in_out(t / fi)
    s = sub_at(T)
    if s is not None:
        a = min(1.0, (T - s["start"]) / 0.12, (s["end"] - T) / 0.12)
        E.subtitle(img, s["text"], alpha=max(0.0, a))
    img = E.finish(img, vig=0.30, grain_amt=0.008, seed=i)
    return E.to_u8(img).tobytes()


def render_shot(sid, tl_path, workers=4):
    tl = json.load(open(tl_path))
    sh = [s for s in tl["shots"] if s["id"] == sid][0]
    f0 = int(round(sh["start"] * tl["fps"]))
    f1 = int(round(sh["end"] * tl["fps"]))
    os.makedirs(SEG, exist_ok=True)
    out = os.path.join(SEG, f"{sid}.mp4")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}",
           "-r", str(tl["fps"]), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
           "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(workers, initializer=_init, initargs=(tl_path,)) as pool:
        for b in pool.imap(frame, range(f0, f1), chunksize=2):
            p.stdin.write(b)
    p.stdin.close()
    p.wait()
    dt = time.time() - t0
    print(f"{sid}: {f1 - f0} frames in {dt:.0f}s ({dt / max(1, f1 - f0):.2f}s/f)", flush=True)


def preview(tl_path, out_path):
    from PIL import Image, ImageDraw
    _init(tl_path)
    tl = _TL
    thumbs = []
    for sh in tl["shots"]:
        T = sh["start"] + (sh["end"] - sh["start"]) * 0.62
        t0 = time.time()
        b = frame(int(T * tl["fps"]))
        dt = time.time() - t0
        im = Image.frombytes("RGB", (E.W, E.H), b).resize((216, 384))
        d = ImageDraw.Draw(im)
        d.text((4, 4), f"{sh['id']} {dt:.1f}s", fill=(255, 255, 0))
        thumbs.append(im)
        print(sh["id"], f"{dt:.2f}s", flush=True)
    cols = 9
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 220, rows * 388), (20, 20, 20))
    for k, im in enumerate(thumbs):
        sheet.paste(im, ((k % cols) * 220, (k // cols) * 388))
    sheet.save(out_path, quality=85)


def concat(tl_path):
    tl = json.load(open(tl_path))
    lst = os.path.join(SEG, "list.txt")
    with open(lst, "w") as f:
        for sh in tl["shots"]:
            f.write(f"file '{os.path.join(SEG, sh['id'] + '.mp4')}'\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(EDIT, "picture.mp4")], check=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    tlp = os.path.join(EDIT, "timeline.json")
    if cmd == "preview":
        tlp = sys.argv[2] if len(sys.argv) > 2 else tlp
        preview(tlp, os.path.join(SCR, "preview_sheet.jpg"))
    elif cmd == "shots":
        tl = json.load(open(tlp))
        ids = sys.argv[2:] or [s["id"] for s in tl["shots"]]
        for sid in ids:
            render_shot(sid, tlp)
    elif cmd == "concat":
        concat(tlp)
