"""逐帧渲染：镜头画面 + 转场 + 原文卡 + 字幕 + 角标，多进程分段编码。
usage: python render.py [--stills t1,t2,...] [--range a b] [--workers N]
"""
import sys, os, json, math, subprocess, time
from functools import lru_cache
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import scenes
from scenes import VIS, panel

WK = os.environ.get("WORK", "/tmp/claude-0/work")
FPS = 25
TL = None
HARD_CUT = {"strike", "final_words", "names", "charcoal_flash", "palace_flash", "vessel", "question", "guoshi_title"}
CHAPTER = dict(s0="", s1="一　三家灭智", s2="二　入宫涂厕", s3="三　漆身吞炭", s4="四　桥下", s5="五　请衣三击", s6="六　不欺其志")


def load():
    global TL
    if TL is None:
        TL = json.load(open(f"{WK}/build/timeline.json"))
    return TL


def shot_at(t):
    for i, s in enumerate(TL["shots"]):
        if s["start"] <= t < s["end"]:
            return i
    return len(TL["shots"]) - 1


def render_shot(i, t):
    s = TL["shots"][i]
    T = s["end"] - s["start"]
    ctx = dict(marks=s["marks"], ends=s["ends"], gt=t, quote=s.get("quote"), qstyle=s.get("qstyle"),
               strikes=s.get("strikes"))
    return VIS[s["vis"]](t - s["start"], T, ctx)


@lru_cache(maxsize=4)
def header_layer(chapter):
    img = np.zeros((H, W, 3), np.float32)
    rgb1, a1 = text_layer(["历史的关键一局"], font("Medium", 30, SC), (0.86, 0.74, 0.5), (64, 150), align="left")
    rgb2, a2 = text_layer(["AI配音 · 情景示意"], font("Regular", 24, SC, sans=True), (0.75, 0.75, 0.75), (W - 64, 150), align="right")
    a = np.maximum(a1, a2 * 0.8)
    rgb = rgb1 * a1[:, :, None] + rgb2 * a2[:, :, None]
    if chapter:
        rgb3, a3 = text_layer([chapter], font("Regular", 26, SC), (0.8, 0.78, 0.72), (64, 196), align="left")
        rgb = rgb + rgb3 * a3[:, :, None]; a = np.maximum(a, a3 * 0.9)
    return rgb, a


@lru_cache(maxsize=64)
def card_layer(orig, src, bai):
    """原文卡：顶部半透明条，原文（繁体）+ 出处 + 白话。返回 (rgb, alpha)。"""
    from gfx import wrap
    fo = font("Bold", 54, TC) if len(orig) < 40 else font("Bold", 46, TC)
    n = 15 if fo.size == 54 else 18
    ol = wrap(orig, n)
    bl = wrap(bai, 24)
    y = 250
    lh = fo.size * 1.42
    h_o = lh * len(ol)
    h_b = 34 * 1.45 * len(bl)
    top, bot = y - 40, y + h_o + 56 + h_b + 40
    im = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    al[int(top):int(bot)] = 0.62
    yy = np.arange(H)[:, None]
    # 上下渐隐边
    al[int(top):int(top) + 30] *= np.linspace(0, 1, 30)[:, None]
    al[int(bot) - 30:int(bot)] *= np.linspace(1, 0, 30)[:, None]
    im[:] = hexc("#05070b")
    for yl in (int(top) + 14, int(bot) - 16):
        im[yl:yl + 2, 120:W - 120] = GOLD_D; al[yl:yl + 2, 120:W - 120] = 0.9
    layers = []
    layers.append(text_layer(ol, fo, GOLD, (W // 2, int(y + lh * (len(ol) - 1) / 2 + fo.size * 0.2)), spacing=1.42))
    layers.append(text_layer(["—— " + src], font("Medium", 28, SC), (0.8, 0.74, 0.6), (W // 2, int(y + h_o + 12))))
    layers.append(text_layer(bl, font("Regular", 34, SC), (0.88, 0.88, 0.86),
                             (W // 2, int(y + h_o + 56 + 34 * 1.45 * (len(bl) - 1) / 2 + 10)), spacing=1.45))
    for rgb, a in layers:
        im = im * (1 - a[:, :, None]) + rgb * a[:, :, None]
        al = np.maximum(al, a)
    return im.astype(np.float32), al.astype(np.float32)


@lru_cache(maxsize=512)
def sub_layer(text):
    n = len(text)
    size = 54 if n <= 16 else int(54 * 16 / n)
    rgb, a, sh = text_layer([text], font("Bold", size, SC), (1, 1, 1), (W // 2, 1490), stroke=3,
                            stroke_fill=(0.02, 0.02, 0.03), shadow=8)
    return rgb, a, sh


def overlays(img, t):
    # 原文卡
    for c in TL["cards"]:
        if c["start"] - 0.05 <= t < c["end"] + 0.35:
            a = ramp(t, c["start"] - 0.05, c["start"] + 0.35) * (1 - ramp(t, c["end"], c["end"] + 0.35))
            rgb, al = card_layer(c["orig"], c["src"], c["bai"])
            img = over(img, rgb, al * a)
    # 字幕
    for L in TL["lines"]:
        if L["start"] - 0.1 <= t < L["end"] + 0.1:
            for s in L["subs"]:
                if s["start"] <= t < s["end"] or (s is L["subs"][-1] and s["end"] <= t < s["end"] + 0.1):
                    rgb, a, sh = sub_layer(s["text"])
                    img = img * (1 - sh[:, :, None] * 0.6)
                    img = over(img, rgb, a)
                    break
            break
    # 角标
    ch = ""
    for L in TL["lines"]:
        if L["start"] <= t + 0.5:
            ch = CHAPTER[L["id"].split("_")[0]]
    rgb, a = header_layer(ch)
    img = over(img, rgb, a * 0.85)
    return img


def frame(fi):
    t = fi / FPS
    i = shot_at(t)
    img = render_shot(i, t)
    s = TL["shots"][i]
    if i > 0 and t - s["start"] < 0.35 and s["vis"] not in HARD_CUT:
        prev = render_shot(i - 1, t)
        k = ease((t - s["start"]) / 0.35)
        img = prev * (1 - k) + img * k
    img = img * vignette(0.55)
    img = grain(img, t, 0.018)
    img = overlays(img, t)
    total = TL["total"]
    img = img * (1 - ramp(t, total - 1.6, total - 0.2))
    return (clamp01(img) * 255 + 0.5).astype(np.uint8)


def encode_range(a, b, out):
    load()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(a, b):
        p.stdin.write(frame(fi).tobytes())
        if (fi - a) % 250 == 0:
            print(f"[{out.split('/')[-1]}] {fi - a}/{b - a} {time.time() - t0:.0f}s", flush=True)
    p.stdin.close(); p.wait()


def main():
    load()
    if "--stills" in sys.argv:
        from PIL import Image
        ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1].split(",")]
        os.makedirs(f"{WK}/stills", exist_ok=True)
        for t in ts:
            t0 = time.time()
            Image.fromarray(frame(int(round(t * FPS)))).save(f"{WK}/stills/f_{t:07.2f}.jpg", quality=88)
            print(f"{t:.2f} {time.time() - t0:.2f}s", flush=True)
        return
    nfr = int(math.ceil(TL["total"] * FPS))
    if "--range" in sys.argv:
        k = sys.argv.index("--range")
        a, b, out = int(sys.argv[k + 1]), int(sys.argv[k + 2]), sys.argv[k + 3]
        encode_range(a, b, out); return
    nw = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    # 按镜头切分，尽量均衡
    os.makedirs(f"{WK}/build/seg", exist_ok=True)
    bounds = [round(nfr * i / nw) for i in range(nw + 1)]
    procs = []
    for i in range(nw):
        out = f"{WK}/build/seg/seg_{i:02d}.mp4"
        procs.append(subprocess.Popen([sys.executable, __file__, "--range", str(bounds[i]), str(bounds[i + 1]), out]))
    for p in procs:
        p.wait()
    with open(f"{WK}/build/seg/list.txt", "w") as f:
        for i in range(nw):
            f.write(f"file 'seg_{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WK}/build/seg/list.txt", "-c", "copy",
                    f"{WK}/build/video_noaudio.mp4"], check=True)
    print("video done", nfr, "frames")


if __name__ == "__main__":
    main()
