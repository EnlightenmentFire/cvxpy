"""逐帧渲染：场景 + 全局层（章节条、字幕、AI 标识、转场）→ 多进程分段 → ffmpeg。
usage: python render.py [--still T ...] [--seg i n] [--from T --to T]
"""
import os, sys, re, math, subprocess, time, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import timeline
from scenes_b import RENDERERS, Cue

SECTIONS = {
    "a": None,
    "b": ("一", "笛卡尔剧场", "哲学理论 · 有影响也有争议"),
    "c": ("二", "全局工作空间", "实证支持的科学理论 · 仍有争议"),
    "d": ("三", "解释器", "实证 · 经典实验"),
    "e": ("四", "心智社会", "理论设想 ＋ 类比印照"),
    "f": ("五", "涌现之争", "实证研究 · 争论未完"),
    "g": ("六", "打开黑箱", "实证研究 · 方法有局限"),
    "h": ("七", "没有中心", ""),
}

def sub_chunks(line):
    """split subtitle into ≤18-char chunks at punctuation, time proportional to characters"""
    s = line["sub"]
    parts = re.split(r"(?<=[，。？！：；])", s)
    chunks, cur = [], ""
    for p in parts:
        if not p:
            continue
        if len(cur) + len(p) <= 18 or not cur:
            cur += p
        else:
            chunks.append(cur); cur = p
    if cur:
        chunks.append(cur)
    # hard-split long chunks
    out = []
    for ch in chunks:
        while len(ch) > 22:
            k = 18
            out.append(ch[:k]); ch = ch[k:]
        out.append(ch)
    w = [max(1, len(re.sub(r"[，。？！：；、「」《》“”\s]", "", c))) for c in out]
    T = line["end"] - line["start"]
    t = line["start"]
    res = []
    for c, ww in zip(out, w):
        d = T * ww / sum(w)
        res.append((t, t + d, c.rstrip("，。；：")))
        t += d
    return res

class Film:
    def __init__(self):
        self.lines, self.scenes, self.total = timeline.build()
        self.cues = [Cue(s) for s in self.scenes]
        self.subs = []
        for ln in self.lines:
            self.subs += sub_chunks(ln)
    def scene_at(self, t):
        for i, s in enumerate(self.scenes):
            if s["t0"] <= t < s["t1"]:
                return i
        return len(self.scenes) - 1

    def frame(self, t):
        i = self.scene_at(t)
        sc = self.scenes[i]
        fr = Frame()
        RENDERERS[sc["key"]](fr, t, self.cues[i])
        if fr.g.any():
            fr.finish_glow()
        img = fr.img
        vignette(img, 0.8)
        sec = sc["lines"][0]["id"][0]
        # transitions: dip at scene boundaries (longer when section changes)
        prev_sec = self.scenes[i - 1]["lines"][0]["id"][0] if i > 0 else sec
        d_in = 0.5 if sec != prev_sec else 0.22
        k = 0.0
        if i > 0:
            k = max(k, 1 - clamp((t - sc["t0"]) / d_in))
        if i + 1 < len(self.scenes):
            nsec = self.scenes[i + 1]["lines"][0]["id"][0]
            d_out = 0.5 if nsec != sec else 0.18
            k = max(k, clamp((t - (sc["t1"] - d_out)) / d_out))
        else:
            k = max(k, clamp((t - (self.total - 2.0)) / 2.0))
        if k > 0:
            img[:] = (img * (1 - 0.92 * k)).astype(np.uint8)
        # section chip (top)
        S = SECTIONS.get(sec)
        if S:
            s0 = min(s["t0"] for s in self.scenes if s["lines"][0]["id"][0] == sec)
            a = clamp((t - s0 - 0.3) / 0.5)
            text(img, f"{S[0]}  {S[1]}", 60, 150, 36, "sansb", CYAN, "lm", 0.9 * a)
            if S[2]:
                text(img, S[2], 60, 200, 26, "sans", GREY, "lm", 0.85 * a)
            rect_alpha(img, 60, 228, 60 + 120 * a, 232, CYAN, 0.8)
        elif t < 7.5:
            # hook headline from frame 0
            a = 1 - clamp((t - 6.8) / 0.7)
            text(img, "你的大脑里，", W / 2, 150, 64, "serifh", WHITE, "mm", a, 4)
            text(img, "真的有一个「你」吗？", W / 2, 240, 64, "serifh", AMBER, "mm", a, 4)
        # AI label (always)
        text(img, "AI 配音 · 画面示意", W - 40, 80, 24, "sans", (170, 178, 196), "rm", 0.75)
        # subtitles
        for (c0, c1, s) in self.subs:
            if c0 - 0.03 <= t < c1 + 0.08:
                a = clamp((t - c0 + 0.03) / 0.08) * (1 - clamp((t - c1) / 0.08))
                size = 50 if len(s) <= 18 else 42
                y = 1640
                w_, h_ = text_size(s, size, "sansb")
                rect_alpha(img, W / 2 - w_ / 2 - 28, y - h_ / 2 - 12, W / 2 + w_ / 2 + 28, y + h_ / 2 + 8, (0, 0, 0), 0.45 * a)
                text(img, s, W / 2, y, size, "sansb", WHITE, "mm", a, 3, (0, 0, 0))
                break
        return img

def render_range(film, t0, t1, out, crf=None):
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    st = time.time()
    for n in range(n0, n1):
        img = film.frame(n / FPS)
        p.stdin.write(img.tobytes())
        if (n - n0) % 250 == 0:
            print(f"[{out}] {n - n0}/{n1 - n0} {time.time() - st:.0f}s", flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    film = Film()
    a = sys.argv[1:]
    if a and a[0] == "--still":
        import cv2
        os.makedirs("stills", exist_ok=True)
        for x in a[1:]:
            if x.startswith("@"):   # scene key: middle of scene
                key = x[1:]
                s = [s for s in film.scenes if s["key"] == key][0]
                T = (s["t0"] + s["t1"]) / 2
            else:
                T = float(x)
            img = film.frame(T)
            cv2.imwrite(f"stills/{x.strip('@')}.jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
            print("still", x, round(T, 1))
    elif a and a[0] == "--seg":
        i, n = int(a[1]), int(a[2])
        outdir = a[3] if len(a) > 3 else "/tmp/claude-0/work/segs"
        os.makedirs(outdir, exist_ok=True)
        L = film.total / n
        render_range(film, i * L, min(film.total, (i + 1) * L), f"{outdir}/seg_{i:02d}.mp4")
    elif a and a[0] == "--from":
        render_range(film, float(a[1]), float(a[3]), a[4] if len(a) > 4 else "/tmp/claude-0/work/clip.mp4")
    else:
        print(f"total {film.total:.1f}s")
