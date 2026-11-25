"""Timeline + frame renderer.
python render.py timeline            -> builds timeline.json from processed voice lines
python render.py still T [T...]      -> preview PNGs
python render.py chunk i n           -> renders chunk i of n to WORK/video/chunk_i.mp4 (25 fps, crf 16)
"""
import sys, os, json, math, re
import numpy as np, soundfile as sf
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
import art
from art import W, H, text_img, font, paste, to_pil, from_pil
from scenes import SHOTS, SECTIONS, ease, ramp

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WORK}/tts/proc"
TL = f"{WORK}/timeline.json"
FPS = 25
LEAD = 0.30     # voice starts 0.3 s after the first frame (bell strike sits on frame 0)
TAIL = 3.5
XF = 0.45       # crossfade


def build_timeline():
    t = LEAD
    out = []
    for d in all_lines():
        p = f"{PROC}/{d['id']}.wav"
        if os.path.exists(p):
            x, sr = sf.read(p); dur = len(x) / sr
        else:   # provisional (preview only)
            dur = len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"])) / 4.6
            print("estimated", d["id"])
        d.update(t0=round(t, 3), t1=round(t + dur, 3))
        out.append(d)
        t += dur + d["gap"]
    total = out[-1]["t1"] + TAIL
    shots = []
    for d in out:
        if not shots or shots[-1]["key"] != d["shot"]:
            shots.append(dict(key=d["shot"], lines=[]))
        shots[-1]["lines"].append(d["id"])
    byid = {d["id"]: d for d in out}
    for i, s in enumerate(shots):
        first = byid[s["lines"][0]]
        s["t0"] = 0.0 if i == 0 else round(first["t0"] - 0.25, 3)
    for i, s in enumerate(shots):
        s["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else round(total, 3)
    json.dump(dict(total=total, lines=out, shots=shots), open(TL, "w"), ensure_ascii=False, indent=1)
    nch = sum(len(re.sub(r"[，。？！：；、“”《》\s]", "", d["say"])) for d in out)
    print(f"total {total:.1f}s ({total/60:.2f} min), {len(shots)} shots, {nch} chars, {nch/(out[-1]['t1']/60):.0f} chars/min")


# ---------------------------------------------------------------- subtitles
PUNCT_END = "。？！；："


def chunks(text, maxc=15):
    """split a subtitle into display chunks at punctuation, each <= maxc visible chars"""
    parts = re.findall(r"[^，。？！；：、]+[，。？！；：、]?", text)
    out, cur = [], ""
    vis = lambda s: len(re.sub(r"[，。？！；：、“”《》\s]", "", s))
    for p in parts:
        if cur and vis(cur + p) > maxc:
            out.append(cur); cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    res = []
    for c in out:
        while vis(c) > maxc + 3:
            res.append(c[:maxc]); c = c[maxc:]
        res.append(c)
    return [r.rstrip("，、；：。") if r[-1:] in "，、；：" or r[-1:] == "。" else r for r in res]


class Renderer:
    def __init__(self):
        self.tl = json.load(open(TL))
        self.lines = {d["id"]: d for d in self.tl["lines"]}
        self.shots = []
        for s in self.tl["shots"]:
            ls = []
            for lid in s["lines"]:
                d = dict(self.lines[lid]); d["t0"] -= s["t0"]; d["t1"] -= s["t0"]
                ls.append(d)
            self.shots.append((s, SHOTS[s["key"]](s["t1"] - s["t0"] + XF, ls)))
        self.subs = []
        for d in self.tl["lines"]:
            if not d["sub"]:
                continue
            cs = chunks(d["sub"])
            n = sum(max(len(c), 1) for c in cs)
            t = d["t0"]
            for c in cs:
                dt = (d["t1"] - d["t0"]) * max(len(c), 1) / n
                self.subs.append((0.0 if not self.subs else t, t + dt, c))
                t += dt
        self._subimg = {}
        self.tag = text_img("AI配音 · 经典故事演绎", font("serif", 30), fill=(200, 195, 185))
        self.sec = {}
        for d in self.tl["lines"]:
            self.sec.setdefault(d["id"][0], d["t0"])

    def sub_img(self, txt):
        if txt not in self._subimg:
            if len(self._subimg) > 40:
                self._subimg.clear()
            self._subimg[txt] = text_img(txt, font("kai" if re.search(r"[a-zāṇ]", txt) else "serif_sb", 58), fill=(250, 246, 236), stroke=3, stroke_fill=(10, 10, 12))
        return self._subimg[txt]

    def shot_frame(self, idx, T):
        s, shot = self.shots[idx]
        t = T - s["t0"]
        img = shot.bg().copy()
        shot.dyn(img, t)
        img *= art.vignette() if art.VIG is None else art.VIG
        if art.VIG is None:
            art.VIG = art.vignette()
        pil = to_pil(img)
        z, fx, fy = shot.cam(t)
        if z > 1.001:
            cw, ch = W / z, H / z
            x0 = min(max(fx - cw / 2, 0), W - cw); y0 = min(max(fy - ch / 2, 0), H - ch)
            pil = pil.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
        shot.over(pil, t)
        return pil

    def frame(self, T):
        idx = 0
        for i, (s, _) in enumerate(self.shots):
            if s["t0"] <= T:
                idx = i
        pil = self.shot_frame(idx, T)
        s = self.shots[idx][0]
        if idx > 0 and T - s["t0"] < XF:
            a = ease((T - s["t0"]) / XF)
            prev = self.shot_frame(idx - 1, T)
            pil = Image.blend(prev, pil, a)
        # end fade
        total = self.tl["total"]
        if T > total - 1.2:
            k = max(0.0, (total - T) / 1.2)
            pil = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), pil, k)
        # overlays
        paste(pil, self.tag, W - self.tag.width - 28, 60, 0.8)
        for (ch, name) in SECTIONS:
            if ch == "a":
                continue
            t0 = self.sec.get(ch)
            if t0 is None:
                continue
            nxt = [self.sec[c] for c, _ in SECTIONS if c > ch and c in self.sec]
            t1 = nxt[0] if nxt else total
            if t0 - 0.3 <= T < t1:
                if not hasattr(self, "_secimg"):
                    self._secimg = {}
                im = self._secimg.setdefault(ch, text_img(name, font("kai", 40), fill=(225, 205, 160)))
                a = ramp(T, t0 - 0.3, t0 + 0.5) * (1 - ramp(T, t1 - 0.6, t1 - 0.1))
                paste(pil, im, 40, 52, a * 0.9)
        for (a, b, txt) in self.subs:
            if a - 0.05 <= T < b + 0.05:
                im = self.sub_img(txt)
                al = min(1.0, (T - a + 0.05) / 0.12 if a > 0 else 1.0, (b + 0.05 - T) / 0.12)
                paste(pil, im, W / 2 - im.width / 2, 1505 - im.height / 2, max(0, al))
                break
        return pil


def render_chunk(i, n):
    import subprocess
    R = Renderer()
    total = R.tl["total"]
    nf = int(math.ceil(total * FPS))
    a, b = nf * i // n, nf * (i + 1) // n
    os.makedirs(f"{WORK}/video", exist_ok=True)
    out = f"{WORK}/video/chunk_{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for f in range(a, b):
        pil = R.frame(f / FPS)
        p.stdin.write(pil.tobytes())
        if (f - a) % 250 == 0:
            print(f"chunk {i}: {f-a}/{b-a} frames, {time.time()-t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()
    print("done", out, flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        build_timeline()
    elif cmd == "still":
        R = Renderer()
        os.makedirs(f"{WORK}/stills", exist_ok=True)
        for a in sys.argv[2:]:
            T = float(a)
            R.frame(T).save(f"{WORK}/stills/s_{T:07.2f}.png")
    elif cmd == "chunk":
        render_chunk(int(sys.argv[2]), int(sys.argv[3]))
