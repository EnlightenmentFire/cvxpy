# -*- coding: utf-8 -*-
"""Assemble scene objects from the timeline and composite a frame (scene + crossfade + subtitles + badges)."""
import json, re, functools
import numpy as np, cv2
from engine import W, H, FPS, SANS_SC, SERIF_SC, SERIF_TC, text_sprite, blit, ease, clamp, GOLD
import scenes_ep as S
from rain import RainWindow

TL_PATH = "/tmp/claude-0/work/timeline.json"
XF = 0.45   # crossfade half-width (s)

RAIN_A = ["s01_hook", "s02_headline", "s03_thesis"]
RAIN_B = ["s20_yinzhao", "s21_end"]


class Film:
    def __init__(self, tl=None):
        self.tl = tl or json.load(open(TL_PATH))
        self.sc = {s["id"]: s for s in self.tl["scenes"]}
        self.order = [s["id"] for s in self.tl["scenes"]]
        self.lines = self.tl["lines"]
        self.objs = {}
        self.group = {}
        a0, a1 = self.sc[RAIN_A[0]]["start"], self.sc[RAIN_A[-1]]["end"]
        b0, b1 = self.sc[RAIN_B[0]]["start"], self.sc[RAIN_B[-1]]["end"]
        self.rwA = RainWindow(a1 - a0 + 1, seed=1, rain=1.0, push=(1.0, 1.10), breath=(3.6, 6.0),
                              heroes=[(650, 120, -0.6, 150, 14), (930, 520, 0.8, 120, 13), (470, 200, 2.6, 170, 12), (720, 640, 5.0, 140, 13)])
        self.rwB = RainWindow(b1 - b0 + 1, seed=4, rain=0.5, dawn=(0.0, 1.0), evap=(0.0, 0.92), push=(1.04, 1.0),
                              breath=(6.0, 7.0), slide_per_min=20)
        for sid in self.order:
            self.group[sid] = "A" if sid in RAIN_A else "B" if sid in RAIN_B else sid

    def lt(self, sid):
        s0 = self.sc[sid]["start"]
        return [l["start"] - s0 for l in self.lines if l["scene"] == sid]

    def obj(self, sid):
        if sid in self.objs:
            return self.objs[sid]
        s = self.sc[sid]; dur = s["end"] - s["start"]; lt = self.lt(sid)
        A0 = self.sc[RAIN_A[0]]["start"]; B0 = self.sc[RAIN_B[0]]["start"]
        m = {
            "s01_hook": lambda: S.RainSeg(dur, lt, self.rwA, s["start"] - A0, S.ov_hook),
            "s02_headline": lambda: S.RainSeg(dur, lt, self.rwA, s["start"] - A0, S.ov_headline),
            "s03_thesis": lambda: S.RainSeg(dur, lt, self.rwA, s["start"] - A0, S.ov_thesis),
            "s04_arrow_tease": lambda: S.ArrowTease(dur, lt),
            "s05_disclaimer": lambda: S.Disclaimer(dur, lt),
            "s06_relapse": lambda: S.Path(dur, lt),
            "s06b_reactivity": lambda: S.Reactivity(dur, lt),
            "s07_rumination": lambda: S.Rumination(dur, lt),
            "s08_origin": lambda: S.Origin(dur, lt),
            "s09_design": lambda: S.Design(dur, lt),
            "s10_decenter": lambda: S.Decenter(dur, lt),
            "s11_teasdale": lambda: S.Teasdale(dur, lt),
            "s12_kuyken": lambda: S.Kuyken(dur, lt),
            "s13_kuyken_result": lambda: S.Forest(dur, lt),
            "s14_caveat": lambda: S.Caveat(dur, lt),
            "s15_goyal": lambda: S.Goyal(dur, lt),
            "s16_limits": lambda: S.Limits(dur, lt),
            "s16b_ledger": lambda: S.Ledger(dur, lt),
            "s17_arrow": lambda: S.SutraQuote(dur, lt, "譬如士夫被一毒箭\n不被第二毒箭\n當於爾時　唯生一受\n所謂身受　不生心受",
                                              "《雜阿含經》卷十七 · 第四七〇經", 4, size=66, col_len=10),
            "s18_two_arrows": lambda: S.Settle(dur, lt),
            "s19_verse": lambda: S.Verse(dur, lt),
            "s20_yinzhao": lambda: S.RainSeg(dur, lt, self.rwB, s["start"] - B0, S.ov_yinzhao),
            "s21_end": lambda: S.RainSeg(dur, lt, self.rwB, s["start"] - B0, S.ov_end),
        }
        self.objs[sid] = m[sid]()
        return self.objs[sid]

    def scene_at(self, t):
        for i, sid in enumerate(self.order):
            if t < self.sc[sid]["end"] or i == len(self.order) - 1:
                return i

    def frame(self, t):
        i = self.scene_at(t)
        sid = self.order[i]
        s = self.sc[sid]
        img = self.obj(sid).render(t - s["start"])
        # crossfade with neighbour scene when the background changes
        if i > 0 and t - s["start"] < XF:
            prev = self.order[i - 1]
            if self.group[prev] != self.group[sid]:
                k = 0.5 + 0.5 * ease((t - s["start"]) / XF)
                pimg = self.obj(prev).render(t - self.sc[prev]["start"])
                img = img * k + pimg * (1 - k)
        if i < len(self.order) - 1 and s["end"] - t < XF:
            nxt = self.order[i + 1]
            if self.group[nxt] != self.group[sid]:
                k = 0.5 - 0.5 * ease((XF - (s["end"] - t)) / XF)
                nimg = self.obj(nxt).render(max(0.0, t - self.sc[nxt]["start"]))
                img = img * (0.5 + k) + nimg * (0.5 - k)
        self.overlays(img, t)
        return img

    # ------------------------------------------------------------ subtitles & badges
    @functools.lru_cache(maxsize=1)
    def sub_chunks(self):
        out = []
        for i, l in enumerate(self.lines):
            nxt = self.lines[i + 1]["start"] if i + 1 < len(self.lines) else l["end"] + 2.5
            end = min(nxt - 0.05, l["end"] + 0.35)
            parts = split_sub(l["sub"])
            n = sum(len(p) for p in parts)
            t0 = l["start"]
            span = l["end"] - l["start"]
            for j, p in enumerate(parts):
                d = span * len(p) / n
                e = (t0 + d) if j < len(parts) - 1 else end
                out.append((t0, e, p, l["k"]))
                t0 += d
        return out

    def overlays(self, img, t):
        # subtitle band (soft dark gradient for legibility)
        for ci, (a, b, s, k) in enumerate(self.sub_chunks()):
            if ci == 0:
                a = -0.3  # first hook line is on screen from frame 0
            if a - 0.08 <= t < b:
                al = clamp((t - a + 0.08) / 0.12) * clamp((b - t) / 0.12)
                band = img[1540:1800]
                band *= (1 - 0.25 * al)
                spr = text_sprite(s, SERIF_TC if k == "q" else SANS_SC, 52 if k == "q" else 50,
                                  (246, 222, 170) if k == "q" else (250, 248, 242), 600 if k == "q" else 500,
                                  960, "center", 1.32, 4, 0, (0, 0, 0), True, 0)
                blit(img, spr, W / 2, 1668, al)
                break
        badge = text_sprite("AI 配音", SANS_SC, 24, (210, 210, 210), 400, 400, "center", 1.2, 2)
        blit(img, badge, W - 82, 44, 0.55)


def split_sub(s, maxlen=36):
    """Split a long subtitle at punctuation into chunks <= maxlen chars (each shown in turn)."""
    s = s.strip()
    if len(s) <= maxlen:
        return [s]
    pieces = re.findall(r"[^，。；：？！]*[，。；：？！]?", s)
    pieces = [p for p in pieces if p]
    out, cur = [], ""
    for p in pieces:
        if len(cur) + len(p) <= maxlen or not cur:
            cur += p
        else:
            out.append(cur); cur = p
    if cur:
        out.append(cur)
    # strip trailing commas/periods for display
    return [o.rstrip("，；：") if o.endswith(("，", "；", "：")) else o for o in out]
