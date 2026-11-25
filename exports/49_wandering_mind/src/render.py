# -*- coding: utf-8 -*-
"""Timeline + frame rendering.
  python render.py timeline            build timeline.json from processed voice (or estimates)
  python render.py still 12.5 [...]    write PNG stills at given seconds
  python render.py video out.mp4 [N]   render all frames with N worker processes (intermediate high-quality mp4)
"""
import os, sys, json, math, re, subprocess
import numpy as np
from gfx import *
from art import tag_layer, bg_base, CX
import scenes
from script_data import SCENES, all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WORK}/tts/proc"
TL_PATH = f"{WORK}/timeline.json"
LEAD = 0.12          # first line starts this many seconds after frame 0
SCENE_GAP = 0.9      # extra breathing room between scenes (music only)

HEADER = dict(A="", B="走神有多普遍", C="本期口径", D="心不可得", E="一 · 走神的网络", F="二 · 「我」是一个模型？",
              G="三 · 苦与预测", H="冷静的声音", I="第二支箭")

# tag shown from this line until changed (within a scene); "" clears
TAG = {"b01": "实证 · 大样本", "b08": "相关研究 · 因果为推断", "c01": "", "d01": "经文",
       "e01": "", "e02": "实证", "e07": "实证 · 小样本", "e11b": "实证 · 小样本", "e12": "小样本 · 部分未复现",
       "e16b": "方法局限", "e17": "",
       "f01": "", "f02": "经文", "f06": "哲学理论", "f11": "实证", "f17": "理论 · 类比", "f21": "类比",
       "g01": "", "g02": "理论框架", "g08": "实证", "g09": "理论模型 · 实证尚早", "g11": "经文", "g17": "类比",
       "g19": "实证 · 小样本", "h01": "", "h07": "", "i01": "", "i09": "经文"}

# source line (small, under the main visual)
SRC = {"a02": "《雜阿含經》卷十二 · 《維摩詰所說經·香積佛品》亦有「心如猨猴」",
       "a03": "大脑示意图",
       "b01": "Killingsworth & Gilbert, Science 330:932 (2010) · 2,250 名成年人",
       "c01": "", "d01": "《金剛經》一體同觀分第十八（通行分段）",
       "e02": "Raichle et al., PNAS 2001；Mason et al., Science 2007",
       "e07": "Brewer et al., PNAS 108(50):20254 (2011) · 12 对 12",
       "e11b": "Hasenkamp et al., NeuroImage 59(1):750 (2012) · 14 人",
       "e12": "Kral et al., J Cogn Neurosci 34(9):1576 (2022)",
       "e16b": "", "f01": "",
       "f06": "Metzinger, Being No One (MIT Press, 2003)", "f11": "", "f17": "", "g01": "",
       "g02": "Clark, Surfing Uncertainty (2016)；Friston, 自由能原理", "g08": "", "g09": "", "g11": "", "g15": "",
       "h01": "", "h02": "Thompson, Why I Am Not a Buddhist (Yale UP, 2020)", "h07": "", "i01": ""}

SUB_MAX = 15


def est_dur(s):
    return len(re.sub(r"[，。？！：；、「」《》“”·\s…]", "", s)) / 4.6 + 0.3


def build_timeline():
    L = all_lines()
    t = LEAD
    out = []
    prev_scene = None
    for d in L:
        if prev_scene is not None and d["scene"] != prev_scene:
            t += SCENE_GAP
        p = f"{PROC}/{d['id']}.wav"
        if os.path.exists(p):
            import soundfile as sf
            dur = sf.info(p).duration
        else:
            dur = est_dur(d["say"])
        out.append(dict(id=d["id"], scene=d["scene"], kind=d["kind"], t0=round(t, 3), t1=round(t + dur, 3),
                        say=d["say"], sub=d["sub"], pause=d["pause"]))
        t += dur + d["pause"]
        prev_scene = d["scene"]
    total = t + 1.5
    tl = dict(lines=out, total=round(total, 3))
    json.dump(tl, open(TL_PATH, "w"), ensure_ascii=False, indent=1)
    return tl


def load_timeline():
    if not os.path.exists(TL_PATH):
        return build_timeline()
    return json.load(open(TL_PATH))


# ----------------------------------------------------------------------------- subtitles
def sub_chunks(text):
    """Split subtitle text into screens of <= 2 lines x SUB_MAX chars."""
    parts = re.findall(r"[^，。？！：；…]+[，。？！：；…」]*", text)
    screens, cur = [], ""
    for p in parts:
        if len(cur + p) <= SUB_MAX * 2 - 2 and len(wrap_cjk(cur + p, SUB_MAX)) <= 2:
            cur += p
        else:
            if cur:
                screens.append(cur)
            cur = p
    if cur:
        screens.append(cur)
    out = []
    for s in screens:
        s2 = s.rstrip("，。；：")
        out.append((s2, len(re.sub(r"[，。？！：；、「」《》“”·\s…]", "", s))))
    return out


def build_subs(tl):
    subs = []
    for d in tl["lines"]:
        ch = sub_chunks(d["sub"])
        tot = sum(n for _, n in ch) or 1
        t = d["t0"]
        dur = d["t1"] - d["t0"]
        for s, n in ch:
            t1 = t + dur * n / tot
            subs.append((t, t1, s))
            t = t1
    # extend each subtitle slightly into the following pause (but not over the next)
    out = []
    for i, (a, b, s) in enumerate(subs):
        nxt = subs[i + 1][0] if i + 1 < len(subs) else b + 1.0
        out.append((a, min(b + 0.35, nxt), s))
    return out


_sub_cache = {}


def sub_layer(s):
    if s not in _sub_cache:
        lines = wrap_cjk(s, SUB_MAX)
        _sub_cache[s] = text_layer("\n".join(lines), ("serif", 52, 650), WHITE, CX, 1490, anchor="mm",
                                   shadow=((0, 0, 0), 5, 0.95))
    return _sub_cache[s]


def write_srt(subs, path):
    def ts(x):
        h, r = divmod(x, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (a, b, s) in enumerate(subs, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{s}\n\n")


# ----------------------------------------------------------------------------- frame
class Renderer:
    def __init__(self):
        self.tl = load_timeline()
        self.lines = {d["id"]: (d["t0"], d["t1"]) for d in self.tl["lines"]}
        self.scene_of = {}
        self.scenes = []
        for s in SCENES:
            ids = [l["id"] for l in s["lines"]]
            t0 = self.lines[ids[0]][0]
            self.scenes.append(dict(id=s["id"], kind=s["kind"], ids=ids, t0=t0))
        for i, s in enumerate(self.scenes):
            s["start"] = 0.0 if i == 0 else s["t0"] - SCENE_GAP * 0.6
        for i, s in enumerate(self.scenes):
            s["end"] = self.scenes[i + 1]["start"] if i + 1 < len(self.scenes) else self.tl["total"]
        self.subs = build_subs(self.tl)
        self.line_list = self.tl["lines"]
        self.bg = bg_base()
        self.badge = text_layer("AI 配音", ("sans", 28, 500), GREY, 60, 153, anchor="lm")
        self.hdr = {}

    def active_line(self, t):
        cur = None
        for d in self.line_list:
            if d["t0"] <= t:
                cur = d
            else:
                break
        return cur

    def meta_at(self, t, table, scene_id):
        val = None
        for d in self.line_list:
            if d["t0"] - 0.2 > t:
                break
            if d["scene"] != scene_id:
                if d["id"] in table or True:
                    pass
            if d["id"] in table:
                val = table[d["id"]] if d["scene"] == scene_id else None
            if d["scene"] != scene_id and d["t0"] <= t:
                val = val if d["scene"] == scene_id else None
        return val

    def scene_content(self, frame, sc, t):
        ctx = scenes.Ctx(self.lines, sc["start"], sc["end"], t)
        scenes.DRAW[sc["kind"]](frame, t, ctx)

    def overlays(self, frame, sc, t, k=1.0):
        # header
        h = HEADER.get(sc["id"], "")
        if h:
            if h not in self.hdr:
                self.hdr[h] = [text_layer(h, ("serif", 42, 700), GOLD, CX, 258, anchor="mm"),
                               scenes.cached_rule(CX - 60, CX + 60, 300, GOLD, 2)]
            comp_any(frame, self.hdr[h], k * 0.95)
        # tag + source: last entry at or before t within this scene
        tag = src = None
        for d in self.line_list:
            if d["t0"] - 0.15 > t:
                break
            if d["scene"] != sc["id"]:
                continue
            if d["id"] in TAG:
                tag = TAG[d["id"]]
            if d["id"] in SRC:
                src = SRC[d["id"]]
        if tag:
            comp(frame, tag_layer(tag), k)
        if src:
            comp_any(frame, scenes.T(src, 26, CX, 1345, GREY, shadow=False), k * 0.9)

    def frame(self, t):
        f = self.bg.copy()
        idx = max(i for i, s in enumerate(self.scenes) if s["start"] <= t) if t >= 0 else 0
        sc = self.scenes[idx]
        XF = 0.6
        if idx + 1 < len(self.scenes) and t > sc["end"] - XF:
            # cross-fade into next scene
            u = ease((t - (sc["end"] - XF)) / XF)
            a = f.copy()
            self.scene_content(a, sc, t)
            self.overlays(a, sc, t)
            b = f.copy()
            nx = self.scenes[idx + 1]
            self.scene_content(b, nx, t)
            self.overlays(b, nx, t)
            f = a * (1 - u) + b * u
        else:
            self.scene_content(f, sc, t)
            # fade out overlays at the very start of a scene for smoothness
            self.overlays(f, sc, t)
        comp_any(f, self.badge, 0.8)
        for a, b, s in self.subs:
            if a <= t < b:
                kk = min(1.0, (t - a) / 0.12, (b - t) / 0.12)
                comp_any(f, sub_layer(s), kk)
                break
        # global fade in from tail
        if t > self.tl["total"] - 1.0:
            f *= max(0.0, (self.tl["total"] - t) / 1.0) * 0.6 + 0.4
        return np.clip(f, 0, 1)


def to_u8(f):
    return (f * 255 + 0.5).astype(np.uint8)


def render_range(f0, f1, out):
    R = Renderer()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        fr = R.frame(i / FPS)
        p.stdin.write(to_u8(fr).tobytes())
        if (i - f0) % 500 == 0:
            print(f"[{os.getpid()}] {i}/{f1}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "timeline":
        tl = build_timeline()
        print("total", tl["total"], "s", len(tl["lines"]), "lines")
        write_srt(build_subs(tl), f"{WORK}/narration.srt")
    elif cmd == "still":
        from PIL import Image
        R = Renderer()
        os.makedirs(f"{WORK}/stills", exist_ok=True)
        for a in sys.argv[2:]:
            if a[0].isalpha():
                d = next(x for x in R.line_list if x["id"] == a.split("+")[0])
                t = d["t0"] + (float(a.split("+")[1]) if "+" in a else (d["t1"] - d["t0"]) * 0.7)
            else:
                t = float(a)
            Image.fromarray(to_u8(R.frame(t))).save(f"{WORK}/stills/{a}.png")
            print("saved", a, round(t, 2))
    elif cmd == "range":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif cmd == "video":
        out = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        tl = load_timeline()
        N = int(math.ceil(tl["total"] * FPS))
        cuts = [N * k // n for k in range(n + 1)]
        procs, parts = [], []
        for k in range(n):
            part = f"{WORK}/part_{k}.mp4"
            parts.append(part)
            procs.append(subprocess.Popen([sys.executable, __file__, "range", str(cuts[k]), str(cuts[k + 1]), part]))
        for p in procs:
            p.wait()
        with open(f"{WORK}/parts.txt", "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/parts.txt",
                        "-c", "copy", out], check=True)
        print("video", out, N, "frames")
