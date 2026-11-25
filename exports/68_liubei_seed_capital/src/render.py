# -*- coding: utf-8 -*-
"""Timeline, overlays and frame rendering.
usage:
  python render.py stills [scene_ids...]      -> preview jpgs
  python render.py seg <i> <n>                -> render segment i of n to out/seg_i.mp4
"""
import sys, os, json, math, re, subprocess
import numpy as np
import skia
import soundfile as sf
import gfx
from gfx import W, H, paint, draw_text, font, ease, ramp, fade_win, INK, WHITE, GOLD, GOLD_L, RED, RED_L, rrect, seal
import scenes
from script import SCENES, all_lines

FPS = 25
PROC = "/home/user/work/tts/proc"
OUT = "/home/user/work/out"
os.makedirs(OUT, exist_ok=True)

GAP_N, GAP_Q_BEFORE, GAP_Q_AFTER, GAP_SCENE, GAP_SECTION = 0.28, 0.30, 0.55, 0.30, 0.70
LEAD = 1.0   # sound hook before first line
TAIL = 3.0
REENACT = {"open", "tree", "teaser_study", "teaser_classmate", "teaser_horses", "uncle", "luzhi", "lecture", "gsz", "youxia",
           "horses", "dianlue", "duyou", "finale"}
SECTION_LABEL = {"hook": "", "c1": "第一笔 · 族叔刘元起", "c2": "第二笔 · 名师卢植", "c3": "第三笔 · 同学公孙瓒",
                 "c4": "第四笔 · 马贩子", "c5": "兑现 · 黄巾之乱", "end": "合账"}


def line_dur(d):
    p = f"{PROC}/{d['id']}.wav"
    if os.path.exists(p):
        return sf.info(p).duration
    n = len(re.findall(r"[一-鿿]", d["say"]))
    return n * (0.30 if d["k"] == "q" else 0.235) + 0.3


def build_timeline():
    t = LEAD
    scs = []
    prev_k = None
    for si, sc in enumerate(SCENES):
        if si > 0:
            t += GAP_SCENE + (GAP_SECTION if sc.get("title") else 0)
        st = t - (0.25 if si > 0 else LEAD)
        L = []
        for i, ln in enumerate(sc["lines"]):
            if i > 0:
                t += GAP_N
            if ln["k"] == "q" and prev_k != "q":
                t += GAP_Q_BEFORE
            d = dict(ln); d["id"] = f"{sc['id']}_{i:02d}"
            dur = line_dur(d)
            L.append((t, t + dur))
            t += dur
            if ln["k"] == "q":
                nxt = sc["lines"][i + 1] if i + 1 < len(sc["lines"]) else None
                if not (nxt and nxt["k"] == "q"):
                    t += GAP_Q_AFTER
                if ln.get("seal"):
                    t += 2.2
            prev_k = ln["k"]
        scs.append(dict(sc=sc, start=st, L=L))
    for i, s in enumerate(scs):
        s["end"] = scs[i + 1]["start"] if i + 1 < len(scs) else t + TAIL
    return scs, scs[-1]["end"]


# ───────── subtitles ─────────
def chunks(text, maxc=15):
    parts = re.findall(r"[^，。！？；：、]+[，。！？；：、]?", text)
    out, cur = [], ""
    for p in parts:
        bare = p.rstrip("，。！？；：、")
        if len(cur) + len(bare) <= maxc and cur:
            cur += p
        elif not cur:
            cur = p
        else:
            out.append(cur); cur = p
    if cur:
        out.append(cur)
    res = []
    for o in out:
        while len(o.rstrip("，。！？；：、")) > maxc + 3:
            cut = maxc
            res.append(o[:cut]); o = o[cut:]
        res.append(o)
    return res


def clean_sub(s):
    s = s.rstrip("，、；：")
    if s.endswith("。"):
        s = s[:-1]
    return s


def sub_events(scs):
    ev = []
    for s in scs:
        for i, ln in enumerate(s["sc"]["lines"]):
            if ln["k"] == "q":
                continue
            a, b = s["L"][i]
            cs = chunks(ln["say"])
            w = [max(1, len(re.sub(r"[，。！？；：、“”《》]", "", c))) for c in cs]
            tot = sum(w)
            acc = a
            for c, ww in zip(cs, w):
                d = (b - a) * ww / tot
                ev.append((acc, acc + d, clean_sub(c)))
                acc += d
    return ev


def card_events(scs):
    ev = []
    for s in scs:
        lines = s["sc"]["lines"]
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln["k"] == "q":
                card = ln["card"]
                a = s["L"][i][0]
                j = i
                while j + 1 < len(lines) and lines[j + 1].get("card") == "same":
                    j += 1
                b = s["L"][j][1]
                nxt = s["L"][j + 1][0] if j + 1 < len(lines) else s["end"]
                ev.append((a - 0.25, b + 0.35 if lines[j].get("seal") else min(b + 1.6, nxt + 0.6), card, lines[j].get("seal")))
                i = j + 1
            else:
                i += 1
    return ev


def seal_times(scs):
    out = {}
    for s in scs:
        for i, ln in enumerate(s["sc"]["lines"]):
            if ln.get("seal"):
                out[ln["seal"] - 1] = s["L"][i][1] + (0.9 if ln["k"] == "q" else -1.15)
    return out


# ───────── overlays ─────────
def draw_card(c, card, a):
    orig, src, plain = card
    f = font("serif_tc", 56 if len(orig) <= 24 else (50 if len(orig) <= 44 else 44))
    lines = gfx.balanced_wrap(orig, f, 800)
    fp = font("sans_m", 36)
    pl = gfx.wrap(plain, fp, 860)
    lh = f.getSize() * 1.5
    hh = 90 + len(lines) * lh + 60 + len(pl) * 54 + 50
    y0 = 960 - hh / 2
    c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, 0.38 * a))
    rrect(c, 50, y0, 980, hh, 18, fill=(16, 13, 12), fill_a=0.84 * a, border=GOLD, border_a=0.85 * a, bw=2.5, shadow=30)
    rrect(c, 62, y0 + 12, 956, hh - 24, 12, border=GOLD, border_a=0.3 * a, bw=1.2)
    y = y0 + 70 + f.getSize() * 0.8
    for ln in lines:
        draw_text(c, ln, W / 2, y, f, GOLD_L, a, spacing=3)
        y += lh
    draw_text(c, "—— " + src, 1000, y - lh * 0.35 + 18, font("serif_tc", 30), (200, 170, 120), a, align="r")
    y += 50
    c.drawLine(110, y - 30, 970, y - 30, paint(GOLD, 0.3 * a, stroke=1))
    for ln in pl:
        y += 54
        draw_text(c, ln, W / 2, y - 14, fp, (236, 230, 220), a)


def draw_sub(c, text, a):
    f = font("sans_b", 52)
    lines = gfx.wrap(text, f, 960)
    y = 1560 - (len(lines) - 1) * 66
    for ln in lines:
        draw_text(c, ln, W / 2, y, f, WHITE, a, stroke=8, stroke_a=0.95, shadow=10)
        y += 70


def draw_header(c, T, sc, sec_label, hud_seals, show_hud):
    # series tag
    draw_text(c, "乱世起家录｜刘备篇", 48, 118, font("sans_m", 30), GOLD, 0.95, align="l", stroke=4)
    # corner AI tags
    x = W - 48
    for lab in (["AI 生成"] + (["情景演绎"] if sc["vis"] in REENACT else [])):
        f = font("sans_m", 24)
        w = gfx.text_w(lab, f) + 22
        rrect(c, x - w, 92, w, 38, 6, fill=INK, fill_a=0.45, border=(200, 190, 170), border_a=0.6, bw=1.2)
        draw_text(c, lab, x - w / 2, 119, f, (230, 222, 205), 0.9)
        x -= w + 10
    if sec_label:
        draw_text(c, sec_label, 48, 196, font("serif_blk", 44), WHITE, 0.95, align="l", stroke=5, shadow=8)
        c.drawLine(48, 218, 48 + 120, 218, paint(GOLD, 0.9, stroke=3))
    if show_hud:
        for i in range(4):
            xx = W - 60 - (3 - i) * 62
            yy = 176
            dash = paint(GOLD, 0.6, stroke=1.6)
            c.drawRect(skia.Rect.MakeXYWH(xx - 26, yy - 26, 52, 52), dash)
            st = hud_seals.get(i)
            if st is not None and T > st + 0.8:
                seal(c, xx, yy, 48, scenes.SEAL_TXT[i], a=1, prog=ramp(T, st + 0.8, st + 1.3))


def draw_hook_title(c, T):
    a = 1 - ramp(T, 7.0, 7.8)
    if a <= 0:
        return
    rrect(c, 0, 250, W, 330, 0, fill=INK, fill_a=0.35 * a)
    draw_text(c, "卖草鞋的刘备", W / 2, 400, font("serif_blk", 118), GOLD_L, a, stroke=8, shadow=16, spacing=6, glow=18, glow_col=GOLD)
    draw_text(c, "第一笔钱是谁给的？", W / 2, 520, font("serif_blk", 78), WHITE, a, stroke=7, shadow=12, spacing=4)


def draw_section_sting(c, T, s):
    sc = s["sc"]
    if not sc.get("title"):
        return
    st = s["start"]
    a = fade_win(T, st + 0.05, st + 2.4, 0.25, 0.45)
    if a <= 0:
        return
    k = ease(ramp(T, st, st + 0.5))
    c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, 0.55 * a))
    big, small = sc["title"]
    draw_text(c, big, W / 2, 860 + (1 - k) * 30, font("serif_blk", 150), GOLD_L, a, stroke=8, glow=24, glow_col=GOLD, spacing=24)
    c.drawLine(W / 2 - 220 * k, 920, W / 2 + 220 * k, 920, paint(GOLD, a, stroke=3))
    draw_text(c, small, W / 2, 1010, font("serif_blk", 64), WHITE, a, stroke=6, spacing=10)


class Renderer:
    def __init__(self):
        self.scs, self.total = build_timeline()
        self.subs = sub_events(self.scs)
        self.cards = card_events(self.scs)
        self.hud = seal_times(self.scs)
        self.surf = skia.Surface(W, H)

    def scene_at(self, T):
        for s in self.scs:
            if s["start"] <= T < s["end"]:
                return s
        return self.scs[-1]

    def frame(self, T):
        c = self.surf.getCanvas()
        c.clear(skia.Color4f(0, 0, 0, 1))
        s = self.scene_at(T)
        sc = s["sc"]
        L = [(a - s["start"], b - s["start"]) for a, b in s["L"]]
        S = scenes.Ctx(T - s["start"], s["end"] - s["start"], L, sc["lines"], T)
        scenes.VIS[sc["vis"]](c, S)
        # scene crossfade-in from black (short) except first
        if s is not self.scs[0]:
            fi = 1 - ramp(T - s["start"], 0, 0.35)
            if fi > 0:
                c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, fi))
        # cards
        for a, b, card, _ in self.cards:
            if a <= T <= b:
                draw_card(c, card, fade_win(T, a, b, 0.35, 0.45))
        # header
        sec = sc["sec"]
        draw_header(c, T, sc, SECTION_LABEL.get(sec, ""), self.hud, show_hud=T > self.scs[5]["start"] + 1.5)
        if T < 8:
            draw_hook_title(c, T)
        draw_section_sting(c, T, s)
        # subtitles
        for a, b, txt in self.subs:
            if a <= T < b:
                draw_sub(c, txt, 1.0)
                break
        img = self.surf.makeImageSnapshot()
        return img.toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]


def stills(ids):
    from PIL import Image
    R = Renderer()
    os.makedirs(OUT + "/stills", exist_ok=True)
    for s in R.scs:
        if ids and s["sc"]["id"] not in ids:
            continue
        L = s["L"]
        ts = [s["start"] + 0.6] + [a + (b - a) * 0.6 for a, b in L]
        for j, T in enumerate(ts):
            fr = R.frame(T)
            Image.fromarray(fr).resize((540, 960)).save(f"{OUT}/stills/{s['sc']['id']}_{j:02d}.jpg", quality=85)
    print("total", R.total)


def seg(i, n):
    R = Renderer()
    nf = int(math.ceil(R.total * FPS))
    a, b = nf * i // n, nf * (i + 1) // n
    out = f"{OUT}/seg_{i:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                         stdin=subprocess.PIPE)
    for f in range(a, b):
        fr = R.frame(f / FPS)
        p.stdin.write(np.ascontiguousarray(fr).tobytes())
        if (f - a) % 250 == 0:
            print(f"seg{i} {f - a}/{b - a}", flush=True)
    p.stdin.close(); p.wait()
    json.dump(dict(a=a, b=b), open(out + ".json", "w"))


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        stills(sys.argv[2:])
    elif sys.argv[1] == "seg":
        seg(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "timeline":
        R = Renderer()
        json.dump(dict(total=R.total, scenes=[dict(id=s["sc"]["id"], start=s["start"], end=s["end"], L=s["L"]) for s in R.scs],
                       subs=R.subs), open(OUT + "/timeline.json", "w"), ensure_ascii=False, indent=1)
        print(R.total)
