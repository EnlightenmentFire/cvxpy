"""Compose frames: background (theme) -> stage -> wheel -> header -> notes -> subtitles.

python render.py still <t_or_lineid[+offset]> out.png
python render.py video out.mp4 [t0 t1]
"""
import json
import math
import os
import re
import subprocess
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(__file__))
from gfx import (W, H, FPS, hexc, with_alpha, mix, paint, font, draw_text, clamp, ease, ease_out, wrap_cjk,
                 background_image, theme_key, CINNABAR, seal)
from timeline import Timeline, SEG_NUM, han_len, load_durations
from wheel import draw_wheel
import stages
from stages import Ctx, STAGES

BUILD = "/home/user/wude_build"
SUB_Y = 1418          # centre of the subtitle block
SUB_MAXC_N = 17
SUB_MAXC_Q = 16


# ------------------------------------------------------------------ subtitles
PUNCT = "，。；：？！、"


def chunks_for(line):
    text = line["text"]
    if line["kind"] == "T" and text.startswith("这说明："):
        text = text[4:]
    maxc = SUB_MAXC_Q if line["kind"] == "Q" else SUB_MAXC_N
    # clauses
    clauses, cur = [], ""
    depth = 0
    for ch in text:
        cur += ch
        if ch in "“「":
            depth += 1
        elif ch in "”」":
            depth = max(0, depth - 1)
        if ch in PUNCT and (depth == 0 or len(cur) > maxc * 2 - 4):
            clauses.append(cur)
            cur = ""
    if cur:
        clauses.append(cur)
    limit = maxc * 2
    pieces = []
    for cl in clauses:  # hard-split over-long clauses
        while len(cl) > limit:
            pieces.append(cl[:limit])
            cl = cl[limit:]
        if cl:
            pieces.append(cl)
    # DP: fewest chunks (each <= limit), then most balanced (min sum of squares)
    n = len(pieces)
    INF = 10 ** 12
    best = [INF] * (n + 1)
    prev = [0] * (n + 1)
    best[0] = 0
    for i in range(1, n + 1):
        for j in range(i - 1, -1, -1):
            L = sum(len(x) for x in pieces[j:i])
            if L > limit:
                break
            if best[j] == INF:
                continue
            chunk = "".join(pieces[j:i])
            cand = best[j] + 900 + L * L + (0 if clean_split(chunk, maxc) else 1500)
            if cand < best[i]:
                best[i], prev[i] = cand, j
    out, i = [], n
    while i > 0:
        j = prev[i]
        out.append("".join(pieces[j:i]))
        i = j
    out = out[::-1]
    # timing weights
    weights = [han_len(c) + 1.2 * sum(c.count(p) for p in PUNCT) + 0.5 for c in out]
    tot = sum(weights)
    times, acc = [], 0.0
    for w in weights:
        times.append(acc / tot)
        acc += w
    return out, times, maxc


_chunk_cache = {}


_WB = {}


def word_breaks(text):
    """Allowed row-break positions: after punctuation (preferred) or at jieba word boundaries."""
    if text not in _WB:
        import jieba
        jieba.setLogLevel(60)
        pos, cut = set(), 0
        for w in jieba.cut(text, HMM=False):
            cut += len(w)
            pos.add(cut)
        _WB[text] = pos
    return _WB[text]


PUNCT_ROW = "，。；：？！、”」"


def best_row_split(text, maxc):
    mid = len(text) / 2
    wb = word_breaks(text)
    best, best_score = None, 1e9
    for i in range(1, len(text)):
        if i > maxc or len(text) - i > maxc:
            continue
        if text[i] in PUNCT_ROW:   # never start a row with punctuation
            continue
        if text[i - 1] in PUNCT_ROW:
            sc = abs(i - mid)
        elif i in wb:
            sc = abs(i - mid) + 2.5
        else:
            continue
        if sc < best_score:
            best, best_score = i, sc
    return best


def clean_split(text, maxc):
    return len(text) <= maxc or best_row_split(text, maxc) is not None


def balanced_rows(text, maxc):
    """Split a chunk into one or two rows, breaking after punctuation or between words."""
    if len(text) <= maxc:
        return [text]
    i = best_row_split(text, maxc)
    if i is None:
        if len(text) > 2 * maxc:
            return wrap_cjk(text, maxc)
        i = int(math.ceil(len(text) / 2))
    return [text[:i], text[i:]]


def subtitle_state(tl, t):
    ln, active = tl.line_at(t)
    if ln is None:
        return None
    # keep the last chunk visible through short gaps, hide in long gaps
    if not active and t - ln["t1"] > 0.35:
        return None
    if ln["id"] not in _chunk_cache:
        _chunk_cache[ln["id"]] = chunks_for(ln)
    chunks, times, maxc = _chunk_cache[ln["id"]]
    p = (t - ln["t0"]) / max(ln["dur"], 0.01)
    idx = 0
    for i, tt in enumerate(times):
        if p >= tt:
            idx = i
    t_chunk = ln["t0"] + times[idx] * ln["dur"]
    fade_in = clamp((t - t_chunk) / 0.12)
    fade_out = 1 - clamp((t - ln["t1"] - 0.2) / 0.15) if not active else 1.0
    return dict(line=ln, text=chunks[idx], maxc=maxc, alpha=fade_in * fade_out, first=(idx == 0))


def draw_subtitles(cv, tl, t, th):
    s = subtitle_state(tl, t)
    if not s or s["alpha"] <= 0.01:
        return
    ln = s["line"]
    kind = ln["kind"]
    a = s["alpha"]
    dark = th["dark"]
    rows = balanced_rows(s["text"], s["maxc"])
    if kind == "Q":
        f = font("serif", "Bold", 56)
        col = th["quote"]
    elif kind == "T":
        f = font("sans", "Bold", 54)
        col = th["sub"]
    else:
        f = font("sans", "Medium", 54)
        col = th["sub"]
    lh = 78
    n = len(rows)
    y0 = SUB_Y - (n - 1) * lh / 2 + 19
    # soft band for legibility
    band = skia.Paint()
    bc = (0.0, 0.0, 0.0) if dark else (0.98, 0.95, 0.88)
    ba = 0.42 if dark else 0.38
    band.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, 1270), skia.Point(0, 1590)],
        [skia.Color4f(*bc, 0), skia.Color4f(*bc, ba * a), skia.Color4f(*bc, ba * a), skia.Color4f(*bc, 0)],
        [0.0, 0.25, 0.75, 1.0]))
    cv.drawRect(skia.Rect.MakeLTRB(0, 1270, W, 1590), band)
    shadow = ((0, 0, 0, 0.75), 5, (0, 2)) if dark else ((1, 0.98, 0.9, 0.7), 4, (0, 0))
    for i, r in enumerate(rows):
        draw_text(cv, r, W / 2, y0 + i * lh, f, col, "center", a, shadow=shadow)
    # source label / takeaway tag
    top = y0 - lh * 0.85 - 6
    if kind == "Q" and ln.get("src"):
        fs = font("serif", "Bold", 32)
        draw_text(cv, ln["src"], W / 2, top, fs, with_alpha(th["quote"], 0.8), "center", a)
    if kind == "T":
        fs = font("sans", "Bold", 32)
        label = "这说明"
        w = fs.measureText(label) + 40
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(W / 2 - w / 2, top - 36, w, 50), 10, 10)
        cv.drawRRect(rr, paint(CINNABAR, alpha=a))
        draw_text(cv, label, W / 2, top - 0, fs, (1, 0.96, 0.88, 1), "center", a)


# ------------------------------------------------------------------ header & notes
def draw_header(cv, tl, t, th):
    seg = tl.seg_at(t)
    col = th["sub"]
    acc = th["accent"]
    fs = font("sans", "Medium", 30)
    draw_text(cv, "命理与正统 · 第一期 · 五德终始", 70, 214, fs, with_alpha(col, 0.72), "left", 1.0, spacing=1.5)
    num = SEG_NUM.get(seg["id"])
    if not num:
        return
    k = ease((t - seg["t0"] + 0.6) / 0.9)
    x = 70 - 30 * (1 - k)
    seal(cv, x + 30, 282, 58, num, color=CINNABAR, alpha=k, rot=0)
    title = seg["title"]
    fsz = 44 if len(title) <= 12 else 35
    draw_text(cv, title, x + 76, 298, font("serif", "Black", fsz), col, "left", k,
              shadow=((0, 0, 0, 0.6), 4, (0, 2)) if th["dark"] else None)


def draw_notes(cv, tl, t, th):
    for (text, a) in tl.notes_at(t):
        f = font("sans", "Regular", 30)
        draw_text(cv, "※ " + text, W / 2, 1282, f, with_alpha(th["sub"], 0.78), "center", a,
                  shadow=((0, 0, 0, 0.6), 3, (0, 1)) if th["dark"] else None)


# ------------------------------------------------------------------ frame
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.surface = skia.Surface(W, H)

    def frame(self, t):
        cv = self.surface.getCanvas()
        th = self.tl.theme_at(t)
        cv.drawImage(background_image(theme_key(th)), 0, 0)
        wheel = self.tl.wheel_at(t)
        name, ts, prev, pts, k = self.tl.stage_at(t)
        if prev and k < 1 and prev in STAGES:
            STAGES[prev](cv, Ctx(self.tl, t, pts, th, 1 - k, wheel))
        if name in STAGES:
            STAGES[name](cv, Ctx(self.tl, t, ts, th, k, wheel))
        draw_wheel(cv, wheel, th)
        draw_header(cv, self.tl, t, th)
        draw_notes(cv, self.tl, t, th)
        draw_subtitles(cv, self.tl, t, th)
        # fade in / out of the whole film
        fade = min(clamp(t / 0.6), clamp((self.tl.total - t) / 1.0))
        if fade < 1:
            cv.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0, 1), alpha=1 - fade))
        return self.surface

    def png(self, t, path):
        self.frame(t).makeImageSnapshot().save(path, skia.kPNG)

    def rgb(self, t):
        a = self.frame(t).makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        return a[..., :3]


def build_timeline(durations_path=None):
    segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
    return Timeline(segs, load_durations(durations_path))


def resolve_time(tl, spec):
    m = re.match(r"^([A-Z]\d_\d\d)(@end)?([+-][\d.]+)?$", spec)
    if m:
        ln = next(l for l in tl.lines if l["id"] == m.group(1))
        base = ln["t1"] if m.group(2) else ln["t0"]
        return base + float(m.group(3) or 0)
    m = re.match(r"^([A-Z]\d_\d\d)%([\d.]+)$", spec)
    if m:
        ln = next(l for l in tl.lines if l["id"] == m.group(1))
        return ln["t0"] + ln["dur"] * float(m.group(2))
    return float(spec)


if __name__ == "__main__":
    mode = sys.argv[1]
    dur_path = os.environ.get("DURATIONS")
    tl = build_timeline(dur_path)
    R = Renderer(tl)
    if mode == "still":
        for spec, out in zip(sys.argv[2::2], sys.argv[3::2]):
            t = resolve_time(tl, spec)
            R.png(t, out)
            print(f"{out} @ {t:.2f}s")
    elif mode == "video":
        out = sys.argv[2]
        a = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
        b = float(sys.argv[4]) if len(sys.argv) > 4 else None
        export_video(tl, out, a, b, audio=os.environ.get("AUDIO"), crf=int(os.environ.get("CRF", "20")),
                     vbitrate=os.environ.get("VBITRATE"))
        print("wrote", out)
    elif mode == "info":
        print(f"total {tl.total:.1f}s ({tl.total/60:.1f} min), lines {len(tl.lines)}")
        for s in tl.segs:
            print(s["id"], f"{s['t0']:.1f}-{s['t1']:.1f}", s["title"])


# ------------------------------------------------------------------ video export
def export_video(tl, out_mp4, t0=0.0, t1=None, audio=None, crf=20, preset="slow", workers=4,
                 vbitrate=None):
    """Render frames in parallel chunks (each chunk -> its own x264 file), then concat + mux."""
    import multiprocessing as mp
    t1 = t1 if t1 is not None else tl.total
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = out_mp4 + ".parts"
    os.makedirs(tmp, exist_ok=True)
    chunks = []
    step = max(1, (n1 - n0 + workers - 1) // workers)
    for i, a in enumerate(range(n0, n1, step)):
        chunks.append((i, a, min(n1, a + step), f"{tmp}/part{i:02d}.mp4", crf, preset, vbitrate))
    with mp.get_context("fork").Pool(len(chunks)) as pool:
        pool.starmap(_render_chunk, [(tl,) + c for c in chunks])
    lst = f"{tmp}/list.txt"
    with open(lst, "w") as f:
        for c in chunks:
            f.write(f"file '{os.path.abspath(c[3])}'\n")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if audio:
        cmd += ["-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", audio, "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)
    return out_mp4


def _render_chunk(tl, idx, a, b, path, crf, preset, vbitrate):
    R = Renderer(tl)
    enc = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", preset, "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.2", "-g", "60", "-threads", "2"]
    if vbitrate:
        enc += ["-b:v", vbitrate, "-maxrate", vbitrate, "-bufsize", "4M", "-x264-params", "nal-hrd=none"]
    else:
        enc += ["-crf", str(crf)]
    enc += ["-tune", "stillimage" if False else "film", path]
    p = subprocess.Popen(enc, stdin=subprocess.PIPE)
    prev_key, prev_bytes = None, None
    for fi in range(a, b):
        t = fi / FPS
        arr = R.rgb(t)
        p.stdin.write(np.ascontiguousarray(arr).tobytes())
    p.stdin.close()
    p.wait()
