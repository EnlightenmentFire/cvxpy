"""Timeline + frame compositor."""
import json
import re
import numpy as np
import skia
from theme import *  # noqa
from prims import *  # noqa
from scenes import SCENES, Ctx, chapter_card
from script_data import SEGMENTS

GAP = 0.32        # default silence between lines (<= 0.4 s)
LEAD = 0.55       # scene settles before the first line
TAIL = 0.45
CH_DUR = 2.5      # chapter card


def est_duration(line, cps=4.7):
    n = len(re.sub(r"[^一-鿿A-Za-z0-9]", "", line["tts"]))
    return n / cps / (line["rate"] or 1.0) + 0.25


def build_timeline(durs=None):
    T = 0.0
    items, lines = [], []
    for seg in SEGMENTS:
        if seg.get("card"):
            items.append(dict(kind="scene", scene=seg["scene"], seg=seg["id"], start=T, end=T + seg["card"], cues={}))
            T += seg["card"]
            continue
        if seg.get("chapter"):
            items.append(dict(kind="chapter", seg=seg["id"], start=T, end=T + CH_DUR, num=seg["chapter"][0], title=seg["chapter"][1]))
            T += CH_DUR
        start = T
        t = LEAD
        cues = {}
        for ln in seg["lines"]:
            d = durs[ln["id"]] if durs and ln["id"] in durs else est_duration(ln)
            cues[ln["id"]] = (t, t + d)
            lines.append(dict(start=start + t, end=start + t + d, text=ln["text"], id=ln["id"], seg=seg["id"]))
            t += d + (ln["gap"] if ln["gap"] is not None else GAP)
        dur = t + TAIL
        items.append(dict(kind="scene", scene=seg["scene"], seg=seg["id"], start=start, end=start + dur, cues=cues))
        T = start + dur
    return items, lines, T


# ------------------------------------------------------------------ subtitles
SUB_SIZE = 50
SUB_MAXW = 930
_SPLIT = "。；！？，：、"


def sub_clean(s):
    s = s.strip()
    while s and s[-1] in "。，；":
        s = s[:-1]
    return s


def chunk_sub(s, max_lines=2):
    """Split a long line into chunks that each fit in max_lines subtitle rows."""
    s = sub_clean(s)
    if len(balanced_wrap(s, "medium", SUB_SIZE, SUB_MAXW)) <= max_lines:
        return [s]
    # split at the punctuation closest to the middle, recursively
    best, bi = None, None
    mid = len(s) / 2
    for i, ch in enumerate(s):
        if ch in _SPLIT and 4 < i < len(s) - 4:
            if best is None or abs(i - mid) < best:
                best, bi = abs(i - mid), i
    if bi is None:
        bi = int(mid)
    a, b = s[:bi + 1], s[bi + 1:]
    return chunk_sub(a, max_lines) + chunk_sub(b, max_lines)


def subtitle_at(lines, T):
    for i, ln in enumerate(lines):
        nxt = lines[i + 1]["start"] if i + 1 < len(lines) else ln["end"] + 0.3
        hold = min(nxt - 0.06, ln["end"] + 0.35)
        if ln["start"] - 0.04 <= T < hold:
            chunks = chunk_sub(ln["text"])
            if len(chunks) == 1:
                k, t0, t1 = 0, ln["start"], hold
            else:
                w = np.array([len(c_) for c_ in chunks], float)
                edges = ln["start"] + np.concatenate([[0], np.cumsum(w) / w.sum()]) * (ln["end"] - ln["start"])
                k = int(np.searchsorted(edges, T, side="right") - 1)
                k = max(0, min(len(chunks) - 1, k))
                t0 = edges[k]
                t1 = edges[k + 1] if k + 1 < len(chunks) else hold
            a = min(ramp(T, t0 - 0.04, t0 + 0.10), 1 - ramp(T, t1 - 0.10, t1))
            return chunks[k], a
    return None, 0.0


def draw_subtitle(c, s, a):
    if not s or a <= 0:
        return
    rows = balanced_wrap(s, "medium", SUB_SIZE, SUB_MAXW)
    lh = 72
    y0 = SUB_Y - (len(rows) - 1) * lh / 2 + 18
    for i, r in enumerate(rows):
        shadow_text(c, r, W / 2, y0 + i * lh, "medium", SUB_SIZE, CREAM, a, "c", 0, sh=(0, 0, 0), sh_a=0.9, sh_blur=7)


# ------------------------------------------------------------------ frame
class Renderer:
    def __init__(self, items, lines, total):
        self.items, self.lines, self.total = items, lines, total
        self.surface = skia.Surface(W, H)
        self.grain = make_grain(6)
        self.vig = vignette_paint(0.62)
        bgsh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.42), H * 0.62,
                                              [col(BG_HI), col(BG), col(BG_LO)], [0.0, 0.55, 1.0])
        self.bgp = skia.Paint()
        self.bgp.setShader(bgsh)

    def item_at(self, T):
        for it in self.items:
            if it["start"] <= T < it["end"]:
                return it
        return self.items[-1]

    def draw(self, T, frame=0, subtitles=True):
        c = self.surface.getCanvas()
        c.clear(col(BG))
        c.drawRect(skia.Rect.MakeWH(W, H), self.bgp)
        it = self.item_at(T)
        t = T - it["start"]
        dur = it["end"] - it["start"]
        c.save()
        if it["kind"] == "chapter":
            chapter_card(c, t, dur, it["num"], it["title"])
        else:
            SCENES[it["scene"]](c, Ctx(t, dur, it["cues"], frame))
        c.restore()
        fade = fade_window(t, 0, dur, 0.42)
        if fade < 1:
            c.drawRect(skia.Rect.MakeWH(W, H), fill(BG_LO, 1 - fade))
        if subtitles:
            s, a = subtitle_at(self.lines, T)
            draw_subtitle(c, s, a)
        gp = skia.Paint(Alphaf=0.075)
        gp.setBlendMode(skia.BlendMode.kOverlay)
        c.drawImage(self.grain[(frame // 2) % len(self.grain)], 0, 0, skia.SamplingOptions(), gp)
        c.drawRect(skia.Rect.MakeWH(W, H), self.vig)
        return self.surface.makeImageSnapshot()

    def frame_bgra(self, T, frame=0):
        return self.draw(T, frame).toarray()

    def frame_rgb(self, T, frame=0):
        return self.draw(T, frame).toarray()[:, :, [2, 1, 0]]


def load_durations(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
