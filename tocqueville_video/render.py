# -*- coding: utf-8 -*-
"""Timeline + frame composer + parallel renderer for the picture track (1080x1920, 30 fps).

python render.py timeline            -> writes timeline.json (needs processed voice lines)
python render.py still <t> [out.png] -> one frame at time t
python render.py range <f0> <f1> <out.mp4>  (worker)
python render.py all [workers]       -> renders everything into /tmp/claude-0/work/video/picture.mp4
"""
import sys, os, json, math, re, subprocess, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import SCENES, all_lines
from art import W, H, paper, Ink, INK, hexc, font, FONT_CJK_SB, balance_cjk, to_u8
import layout
from layout import PX0, PY0, PX1, PY1

FPS = 30
DYN_FPS = 15
WORK = "/tmp/claude-0/work"
PROC = f"{WORK}/tts/proc"
TL_PATH = f"{WORK}/timeline.json"

SCENE_PAD_IN = {"s00": 1.6, "s09": 1.2}
SCENE_PAD_OUT = {"s09": 1.2, "s10": 4.0}
XFADE = 0.8
TAIL = 3.0          # teaser card + black at the very end


# ------------------------------------------------------------------ timeline

def line_dur(d):
    p = f"{PROC}/{d['id']}.wav"
    if os.path.exists(p):
        import soundfile as sf
        info = sf.info(p)
        return info.frames / info.samplerate
    n = len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"]))
    return n / (4.9 if d["k"] == "n" else 4.5)


def build_timeline():
    t = 0.0
    scenes = []
    for s in SCENES:
        st = t
        t += SCENE_PAD_IN.get(s["id"], 0.9)
        lines = []
        for i, d in enumerate(s["lines"]):
            dd = dict(d)
            dd.setdefault("sub", dd["say"])
            dd.setdefault("gap", 0.3)
            dur = line_dur(dd)
            lines.append(dict(id=dd["id"], k=dd["k"], start=round(t, 3), end=round(t + dur, 3), sub=dd["sub"],
                              fr=dd.get("fr"), src=dd.get("src"), cue=dd.get("cue")))
            gap = max(0.38, dd["gap"] + 0.12)
            if i + 1 < len(s["lines"]) and s["lines"][i + 1]["k"] != dd["k"]:
                gap += 0.25
            t += dur + gap
        t += SCENE_PAD_OUT.get(s["id"], 0.5)
        scenes.append(dict(id=s["id"], chapter=s["chapter"], palette=s["palette"], start=round(st, 3), end=round(t, 3), lines=lines))
    total = t + TAIL
    tl = dict(fps=FPS, total=round(total, 3), scenes=scenes)
    json.dump(tl, open(TL_PATH, "w"), ensure_ascii=False, indent=1)
    return tl


def load_timeline():
    return json.load(open(TL_PATH))


# ------------------------------------------------------------------ context for scenes

def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Ctx:
    def __init__(self, scene, t):
        self.scene = scene
        self.t = t - scene["start"]                     # local time
        self.tq = math.floor(self.t * DYN_FPS) / DYN_FPS  # quantized for dynamic drawing
        self.dur = scene["end"] - scene["start"]
        self.cues = {}
        for ln in scene["lines"]:
            self.cues[ln["id"]] = (ln["start"] - scene["start"], ln["end"] - scene["start"])
            if ln.get("cue"):
                self.cues.setdefault(ln["cue"], (ln["start"] - scene["start"], ln["end"] - scene["start"]))

    def at(self, cue):
        return self.cues.get(cue, (None, None))[0]

    def end(self, cue):
        return self.cues.get(cue, (None, None))[1]

    def since(self, cue):
        a = self.at(cue)
        return -1e9 if a is None else self.tq - a

    def p(self, cue, dur=1.0, delay=0.0, smooth=True):
        s = self.since(cue) - delay
        x = min(1.0, max(0.0, s / max(1e-6, dur)))
        return ease(x) if smooth else x

    def past(self, cue, delay=0.0):
        return self.since(cue) >= delay

    def phase(self, order):
        """order: list of (cue_or_None, name). returns (name, prev_name, crossfade 0..1)"""
        cur, prev, start = order[0][1], None, -1e9
        for cue, name in order[1:]:
            a = self.at(cue)
            if a is not None and self.tq >= a - 0.3:
                prev, cur, start = cur, name, a - 0.3
        x = (self.tq - start) / XFADE if prev else 1.0
        return cur, prev, ease(x)


# ------------------------------------------------------------------ affine overlay cache

class Overlay:
    """Captures any per-pixel affine drawing op (out = c*k + d) into a cropped layer."""

    def __init__(self, draw_fn):
        z = np.zeros((H, W, 3), np.float32)
        o = np.ones((H, W, 3), np.float32)
        draw_fn(z); draw_fn(o)
        k = o - z
        d = z
        diff = (np.abs(k - 1).max(2) > 1e-3) | (np.abs(d).max(2) > 1e-3)
        ys, xs = np.nonzero(diff)
        if len(ys) == 0:
            self.box = None
            return
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        self.box = (y0, y1, x0, x1)
        self.k = k[y0:y1, x0:x1].astype(np.float32)
        self.d = d[y0:y1, x0:x1].astype(np.float32)

    def apply(self, canvas, op=1.0):
        if self.box is None or op <= 0:
            return canvas
        y0, y1, x0, x1 = self.box
        c = canvas[y0:y1, x0:x1]
        tgt = c * self.k + self.d
        canvas[y0:y1, x0:x1] = tgt if op >= 1 else c + (tgt - c) * op
        return canvas


_OV = {}


def overlay(key, fn):
    if key not in _OV:
        _OV[key] = Overlay(fn)
    return _OV[key]


# ------------------------------------------------------------------ subtitles

SUB_MAX = 36


def chunk_sub(text, start, end):
    """split long subtitles into <=2-line chunks at punctuation, timed by character share."""
    clean = text.strip()
    if len(clean) <= SUB_MAX:
        return [(start, end, clean)]
    parts = re.findall(r"[^。？！；：]+[。？！；：]?", clean)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= SUB_MAX:
            cur += p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > SUB_MAX:
                n = math.ceil(len(p) / SUB_MAX)
                commas = [m.end() for m in re.finditer(r"[，、]", p)]
                cuts, last = [], 0
                for j in range(1, n):
                    target = len(p) * j / n
                    cands = [x for x in commas if last < x < len(p) - 2]
                    cut = min(cands, key=lambda x: abs(x - target)) if cands else int(target)
                    cuts.append(cut); last = cut
                prev_c = 0
                for cut in cuts:
                    chunks.append(p[prev_c:cut]); prev_c = cut
                p = p[prev_c:]
            cur = p
    if cur:
        chunks.append(cur)
    tot = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        dt = (end - start) * len(c) / tot
        out.append((t, t + dt, c))
        t += dt
    return out


# ------------------------------------------------------------------ page cache

_PAGE = {}


def page(scene):
    key = scene["id"]
    if key not in _PAGE:
        import anim
        tone = anim.SCENE_TONE.get(scene["id"], "warm")
        base = paper(tone, 1)
        base = layout.compose_plate(base, base)  # border only
        if scene["chapter"]:
            layout.header(base, scene["chapter"])
        _PAGE[key] = base
    return _PAGE[key]


_PM = None


def plate_mask():
    global _PM
    if _PM is None:
        _PM = layout.plate_mask()[PY0 - 4:PY1 + 4, PX0 - 4:PX1 + 4, None]
    return _PM


def camera_apply(ill, zoom, fx, fy):
    """crop the plate region of ill around focus (fx,fy) with zoom>=1, resize back to plate size."""
    pw, ph = PX1 - PX0 + 8, PY1 - PY0 + 8
    x0p, y0p = PX0 - 4, PY0 - 4
    if zoom <= 1.0005:
        return ill[y0p:y0p + ph, x0p:x0p + pw]
    cw, ch = pw / zoom, ph / zoom
    cx = min(max(fx, x0p + cw / 2), x0p + pw - cw / 2)
    cy = min(max(fy, y0p + ch / 2), y0p + ph - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    im = Image.fromarray(to_u8(ill[int(box[1]) - 2:int(box[3]) + 3, int(box[0]) - 2:int(box[2]) + 3]))
    ox, oy = box[0] - (int(box[0]) - 2), box[1] - (int(box[1]) - 2)
    im = im.transform((pw, ph), Image.EXTENT, (ox, oy, ox + cw, oy + ch), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255


# ------------------------------------------------------------------ frame

class Renderer:
    def __init__(self, tl):
        import anim
        self.anim = anim
        self.tl = tl
        self.scenes = tl["scenes"]
        self.subs = []
        for s in self.scenes:
            for ln in s["lines"]:
                if ln["k"] == "n":
                    for a, b, c in chunk_sub(ln["sub"], ln["start"], ln["end"]):
                        self.subs.append((a - 0.08, b + 0.12, c, s["id"]))
        self._ill_cache = {}

    def scene_at(self, t):
        for i, s in enumerate(self.scenes):
            if s["start"] <= t < s["end"]:
                return i
        return len(self.scenes) - 1

    def ill(self, s, t):
        c = Ctx(s, t)
        key, fn = self.anim.scene_illustration(s["id"], c)
        ck = (s["id"],) + tuple(key)
        if ck not in self._ill_cache:
            if len(self._ill_cache) > 6:
                self._ill_cache.pop(next(iter(self._ill_cache)))
            self._ill_cache[ck] = fn()
        return self._ill_cache[ck], c

    def scene_frame(self, i, t):
        s = self.scenes[i]
        ill, c = self.ill(s, t)
        zoom, fx, fy = self.anim.scene_camera(s["id"], c)
        content = camera_apply(ill, zoom, fx, fy)
        fr = page(s).copy()
        m = plate_mask()
        y0p, x0p = PY0 - 4, PX0 - 4
        reg = fr[y0p:y0p + content.shape[0], x0p:x0p + content.shape[1]]
        fr[y0p:y0p + content.shape[0], x0p:x0p + content.shape[1]] = reg * (1 - m) + content * m
        # scene-specific overlays drawn over the page (titles etc.)
        self.anim.scene_overlay(s["id"], c, fr, overlay)
        # quote cards
        for ln in s["lines"]:
            if ln["k"] != "q":
                continue
            a, b = ln["start"] - 0.35, ln["end"] + 0.45
            if a - 0.4 <= t <= b + 0.4:
                op = min(ease((t - (a - 0.4)) / 0.4), ease(((b + 0.4) - t) / 0.4))
                ov = overlay(("q", ln["id"]), lambda cv, ln=ln: layout.quote_card(cv, ln["fr"], ln["sub"], ln["src"]))
                ov.apply(fr, op)
        # subtitles (narration only)
        for a, b, txt, sid in self.subs:
            if sid == s["id"] and a - 0.15 <= t <= b + 0.15:
                op = min(ease((t - (a - 0.15)) / 0.15), ease(((b + 0.15) - t) / 0.15))
                ov = overlay(("sub", txt), lambda cv, txt=txt: layout.subtitle(cv, txt))
                ov.apply(fr, op)
        # fade to black (scene-defined, e.g. Memphis)
        blk = self.anim.scene_black(s["id"], c)
        if blk > 0:
            fr *= (1 - blk)
        return fr

    def frame(self, t):
        i = self.scene_at(t)
        s = self.scenes[i]
        if t >= self.tl["total"] - TAIL:
            return self.anim.tail_frame(t - (self.tl["total"] - TAIL), TAIL, overlay)
        fr = self.scene_frame(i, t)
        # crossfade into the next scene
        if i + 1 < len(self.scenes) and t > s["end"] - XFADE / 2:
            nxt = self.scene_frame(i + 1, t)
            x = ease((t - (s["end"] - XFADE / 2)) / XFADE)
            fr = fr * (1 - x) + nxt * x
        elif i > 0 and t < s["start"] + XFADE / 2:
            prv = self.scene_frame(i - 1, t)
            x = ease((t - (s["start"] - XFADE / 2)) / XFADE)
            fr = prv * (1 - x) + fr * x
        return fr


# ------------------------------------------------------------------ encoding

def render_range(f0, f1, out):
    tl = load_timeline()
    R = Renderer(tl)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        fr = R.frame(f / FPS)
        p.stdin.write(to_u8(fr).tobytes())
        if (f - f0) % 300 == 0:
            el = time.time() - t0
            print(f"[{out}] {f - f0}/{f1 - f0} frames, {el:.0f}s", flush=True)
    p.stdin.close(); p.wait()


def render_all(workers=4, out=f"{WORK}/video/picture.mp4"):
    tl = load_timeline()
    n = int(round(tl["total"] * FPS))
    os.makedirs(f"{WORK}/video", exist_ok=True)
    bounds = [round(n * i / workers) for i in range(workers + 1)]
    procs, parts = [], []
    for i in range(workers):
        part = f"{WORK}/video/part{i}.mp4"
        parts.append(part)
        procs.append(subprocess.Popen([sys.executable, os.path.abspath(__file__), "range", str(bounds[i]), str(bounds[i + 1]), part]))
    for p in procs:
        p.wait()
    with open(f"{WORK}/video/parts.txt", "w") as f:
        for part in parts:
            f.write(f"file '{part}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/video/parts.txt", "-c", "copy", out], check=True)
    print("picture:", out, n, "frames")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        tl = build_timeline()
        print("total", tl["total"], "s")
        for s in tl["scenes"]:
            print(s["id"], s["start"], s["end"], round(s["end"] - s["start"], 1))
    elif cmd == "still":
        t = float(sys.argv[2])
        out = sys.argv[3] if len(sys.argv) > 3 else f"{WORK}/still_{t:.1f}.png"
        R = Renderer(load_timeline())
        t0 = time.time()
        Image.fromarray(to_u8(R.frame(t))).save(out)
        print("ok", out, round(time.time() - t0, 2), "s")
    elif cmd == "range":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "all":
        render_all(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
