# -*- coding: utf-8 -*-
"""Frame composer: header, illustration layer (scenes), cards, takeaways, captions."""
import functools
import math
import re

from PIL import Image

import gfx
from gfx import (BG, BG2, INK, INK2, INK3, LINE, TEAL, TEAL_D, TEAL_L, WHITE, W, H, ease, ease_out,
                 back_out, with_alpha, font, text_sprite, pill, wrap, text_w, Sprite, shadow)
from script_data import SPEAKERS
import timeline as TL

ILL_Y0, ILL_Y1 = 290, 1440      # illustration layer region on the frame
CARD_Y = 1000                   # card zone top
CAP_Y = 1515                    # caption center line


def comp(base, im, x, y, a=1.0):
    if im is None:
        return
    if a < 0.999:
        im = with_alpha(im, a)
        if im is None:
            return
    x, y = int(round(x)), int(round(y))
    # clip to base
    bw, bh = base.size
    if x >= bw or y >= bh or x + im.width <= 0 or y + im.height <= 0:
        return
    if x < 0 or y < 0 or x + im.width > bw or y + im.height > bh:
        cx0, cy0 = max(0, -x), max(0, -y)
        cx1, cy1 = min(im.width, bw - x), min(im.height, bh - y)
        im = im.crop((cx0, cy0, cx1, cy1))
        x, y = max(x, 0), max(y, 0)
    base.alpha_composite(im, (x, y))


def appear(base, im, x, y, t, t0, dur=0.45, mode="up", dist=26, t1=None, out_dur=0.35, anchor="tl"):
    """Composite `im` with an entrance animation starting at t0 (and optional exit at t1)."""
    if t0 is None or t < t0:
        return 0.0
    p = (t - t0) / dur if dur > 0 else 1.0
    a = ease(p)
    if t1 is not None and t > t1:
        a *= 1 - ease((t - t1) / out_dur)
        if a <= 0.001:
            return 0.0
    if anchor == "c":
        x -= im.width / 2
        y -= im.height / 2
    elif anchor == "tc":
        x -= im.width / 2
    elif anchor == "bc":
        x -= im.width / 2
        y -= im.height
    ox = oy = 0
    if mode == "up":
        oy = dist * (1 - ease_out(p))
    elif mode == "down":
        oy = -dist * (1 - ease_out(p))
    elif mode == "left":
        ox = dist * (1 - ease_out(p))
    elif mode == "right":
        ox = -dist * (1 - ease_out(p))
    elif mode == "pop":
        s = 0.82 + 0.18 * back_out(min(1, p * 1.1))
        if s < 0.999:
            nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
            im2 = im.resize((nw, nh), Image.BILINEAR)
            comp(base, im2, x + (im.width - nw) / 2, y + (im.height - nh) / 2, a)
            return a
    comp(base, im, x + ox, y + oy, a)
    return a


# ------------------------------------------------------------------ cached text
@functools.lru_cache(maxsize=2048)
def T(txt, fnt="m", size=40, fill=INK, maxw=None, align="left", stroke=0, stroke_fill=None, gap=0.32):
    return text_sprite(txt, fnt, size, fill, maxw=maxw, align=align, stroke=stroke,
                       stroke_fill=stroke_fill, line_gap=gap)


@functools.lru_cache(maxsize=512)
def P(txt, fnt="b", size=26, fg=WHITE, bg=INK, padx=16, pady=7, outline=None):
    return pill(txt, fnt, size, fg, bg, padx=padx, pady=pady, outline=outline)


# ------------------------------------------------------------------ header
@functools.lru_cache(maxsize=64)
def header_img(chapter):
    sp = Sprite(W, 130)
    tag = pill("美国文化与职场", "b", 26, WHITE, INK, padx=16, pady=7)
    sp.paste(tag, 60, 14)
    sp.text((60 + tag.width + 18, 14 + tag.height / 2 + 1), "美国人到底怎么说话", "m", 28, INK2, anchor="lm")
    if chapter:
        sp.text((62, 84), chapter, "b", 34, INK, anchor="lm")
    return sp.img()


@functools.lru_cache(maxsize=8)
def badge_img(kind):
    if kind == "shiyi":
        return pill("示意 · 非真实事件", "m", 24, INK2, BG2, padx=14, pady=6, outline=LINE)
    if kind == "history":
        return pill("真实历史 · 见出处", "m", 24, INK2, BG2, padx=14, pady=6, outline=LINE)
    return None


# ------------------------------------------------------------------ captions
MAXC = 940


def _split_long(phrase, f, maxw=MAXC):
    """Split a phrase that is wider than maxw into roughly equal single-line pieces."""
    if text_w(phrase, f) <= maxw:
        return [phrase]
    n = int(text_w(phrase, f) // maxw) + 1
    toks = gfx.tokenize(phrase)
    target = len(toks) / n
    out, cur = [], ""
    for i, tk in enumerate(toks):
        cur += tk
        if len(out) < n - 1 and (i + 1) >= target * (len(out) + 1) and tk not in "“‘《（":
            # avoid leaving a closing mark at the next line start
            out.append(cur)
            cur = ""
    if cur:
        if cur.strip() and cur.strip()[0] in gfx.NO_LINE_START and out:
            out[-1] += cur.strip()[0]
            cur = cur.strip()[1:]
        if cur:
            out.append(cur)
    return [o.strip() for o in out if o.strip()]


def _pack(pieces, f, maxw):
    """Minimal-raggedness packing of pieces into single lines (<= maxw)."""
    n = len(pieces)
    INF = float("inf")
    best = [INF] * (n + 1)
    nxt = [n] * (n + 1)
    best[n] = 0
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            line = "".join(pieces[i:j])
            w = text_w(line.rstrip("，。：；"), f)
            if w > maxw and j > i + 1:
                break
            cost = (maxw - w) ** 2 + best[j] + 4e4
            if cost < best[i]:
                best[i], nxt[i] = cost, j
    out, i = [], 0
    while i < n:
        out.append("".join(pieces[i:nxt[i]]))
        i = nxt[i]
    return out


def split_caption(text, f, maxw=MAXC):
    """Single-line subtitle chunks: split at sentence punctuation, then pack comma pieces."""
    sents = re.findall(r"[^。：；！？]+[。：；！？]?|[。：；！？]", text)
    chunks = []
    for snt in sents:
        if text_w(snt.rstrip("，。：；"), f) <= maxw:
            chunks.append(snt)
            continue
        parts = re.findall(r"[^，、]+[，、]?|[，、]", snt)
        pieces = []
        for p in parts:
            pieces.extend(_split_long(p, f, maxw))
        chunks.extend(_pack(pieces, f, maxw))
    # merge very short tails into previous chunk when they fit
    out = []
    for c in chunks:
        if out and len(re.sub(r"\W", "", c)) <= 4 and text_w((out[-1] + c).rstrip("，。：；"), f) <= maxw:
            out[-1] += c
        else:
            out.append(c)
    return [c for c in out if c.strip("，。：；")]


@functools.lru_cache(maxsize=2048)
def caption_img(txt):
    shown = txt.strip().rstrip("，。：；").replace("——", "")
    return text_sprite(shown, "m", 44, INK, align="center", line_gap=0.3, stroke=5, stroke_fill=BG)


def caption_chunks(line):
    f = font("m", 44)
    chunks = split_caption(line["text"], f)
    n = sum(max(1, len(re.sub(r"\W", "", c))) for c in chunks)
    out, t = [], line["t0"]
    span = line["t1"] - line["t0"]
    for c in chunks:
        k = max(1, len(re.sub(r"\W", "", c)))
        d = span * k / n
        out.append((t, t + d, c))
        t += d
    return out


# ------------------------------------------------------------------ cards
SPK_COLORS = {"mike": gfx.C_MIKE, "amy": gfx.C_SARAH, "dave": gfx.C_CHEN, "hr": gfx.C_GRAY,
              "brit": gfx.C_PLUM}


@functools.lru_cache(maxsize=128)
def en_bubble(en, spk):
    sp_info = SPEAKERS.get(spk, dict(name="", role=""))
    f = font("ens", 46)
    lines = wrap("“" + en + "”", f, 880)
    lh = 58
    w = 960
    h = 34 + 40 + len(lines) * lh + 16
    s = Sprite(w, h + 26)
    col = SPK_COLORS.get(spk, INK2)
    s.rrect((0, 0, w - 1, h), 30, fill=WHITE, outline=LINE, width=2)
    s.poly([(70, h - 2), (110, h - 2), (58, h + 24)], fill=WHITE)
    s.line([(70, h - 1), (58, h + 24), (110, h - 1)], LINE, 2)
    s.rect((72, h - 4, 108, h + 1), fill=WHITE)
    s.circle(48, 40, 11, fill=col)
    s.text((68, 40), f"{sp_info['name']} · {sp_info['role']}", "m", 26, INK2, anchor="lm")
    y = 74
    for l in lines:
        s.text((40, y), l, "ens", 46, INK)
        y += lh
    return s.img()


@functools.lru_cache(maxsize=128)
def zh_bubble(zh):
    f = font("b", 48)
    lines = wrap("“" + zh + "”", f, 880)
    lh = 64
    w = 960
    h = 34 + 40 + len(lines) * lh + 16
    s = Sprite(w, h + 26)
    s.rrect((0, 0, w - 1, h), 30, fill=WHITE, outline=LINE, width=2)
    s.poly([(w - 110, h - 2), (w - 70, h - 2), (w - 58, h + 24)], fill=WHITE)
    s.line([(w - 110, h - 1), (w - 58, h + 24), (w - 70, h - 1)], LINE, 2)
    s.rect((w - 108, h - 4, w - 72, h + 1), fill=WHITE)
    s.circle(48, 40, 11, fill=gfx.C_CHEN)
    s.text((68, 40), "陈经理 · 合作方", "m", 26, INK2, anchor="lm")
    y = 74
    for l in lines:
        s.text((40, y), l, "b", 48, INK)
        y += lh
    return s.img()


@functools.lru_cache(maxsize=256)
def strip_img(label, txt, kind, width=960):
    """kind: 'lit' (white) or 'real' (teal)."""
    if kind == "lit":
        fg, bg, lfg, lbg, fnt, size = INK, WHITE, INK2, BG2, "m", 40
    else:
        fg, bg, lfg, lbg, fnt, size = WHITE, TEAL, TEAL, WHITE, "b", 42
    lab = pill(label, "b", 24, lfg, lbg, padx=12, pady=5)
    f = font(fnt, size)
    textw = width - 56 - lab.width - 20
    lines = wrap(txt, f, textw)
    lh = int(size * 1.36)
    h = max(lab.height + 28, len(lines) * lh + 30)
    s = Sprite(width, h)
    s.rrect((0, 0, width - 1, h - 1), 20, fill=bg, outline=LINE if kind == "lit" else None,
            width=2 if kind == "lit" else 0)
    s.paste(lab, 22, 16 + (lh - lab.height) / 2 - 2)
    y = 14
    for l in lines:
        s.text((22 + lab.width + 18, y + (lh - size * 1.2) / 2), l, fnt, size, fg)
        y += lh
    return s.img()


@functools.lru_cache(maxsize=64)
def trans_frames():
    out = []
    for i in range(4):
        s = Sprite(220, 46)
        s.rrect((0, 0, 219, 45), 23, fill=BG2)
        s.text((24, 23), "翻译中", "m", 24, INK2, anchor="lm")
        for j in range(3):
            on = j < i or i == 3
            s.circle(130 + j * 22, 24, 6, fill=INK2 if on else LINE)
        out.append(s.img())
    return out


@functools.lru_cache(maxsize=256)
def why_img(txt):
    f = font("r", 32)
    lines = wrap(txt, f, 880)
    h = len(lines) * 46 + 8
    s = Sprite(960, h)
    s.paste(gfx.icon_bulb(30, INK3), 4, 6)
    y = 0
    for l in lines:
        s.text((48, y), l, "r", 32, INK2)
        y += 46
    return s.img()


def draw_card(fr, c, t, y0=CARD_Y):
    """Two-layer subtitle card. Returns bottom y."""
    t_end = c.get("t_end")
    fade = 1.0
    if t_end is not None and t > t_end:
        fade = 1 - ease((t - t_end) / 0.35)
        if fade <= 0:
            return y0
    x = 60
    y = y0
    if c["kind"] == "E":
        b = en_bubble(c["en"], c["spk"])
        a = appear(fr, b, x, y, t, c["t0"], 0.35, "pop")
        y += b.height + 10
    else:
        b = zh_bubble(c["zh"])
        appear(fr, b, x, y, t, c["t0"], 0.35, "pop")
        y += b.height + 10
    if fade < 1:
        pass
    # literal strip
    lit = strip_img("字面", c["lit"], "lit")
    if c.get("t_lit") is not None and t >= c["t_lit"]:
        appear(fr, lit, x, y, t, c["t_lit"], 0.35, "up", 18)
    y += lit.height + 10
    # translating indicator
    tt = c.get("t_trans")
    tr_ = c.get("t_real")
    if tt is not None and t >= tt and (tr_ is None or t < tr_ + 0.25):
        k = int((t - tt) * 4.0) % 4
        im = trans_frames()[k]
        a = ease((t - tt) / 0.2)
        if tr_ is not None and t > tr_:
            a *= 1 - ease((t - tr_) / 0.25)
        comp(fr, im, W / 2 - im.width / 2, y + 4, a)
    # real meaning strip floats up
    real = strip_img("真实意思", c["real"], "real")
    if tr_ is not None and t >= tr_:
        appear(fr, real, x, y, t, tr_, 0.6, "up", 46)
    y += real.height + 14
    if c.get("why") and c.get("t_why") is not None and t >= c["t_why"]:
        wi = why_img(c["why"])
        appear(fr, wi, x + 4, y, t, c["t_why"], 0.45, "up", 12)
        y += wi.height
    return y


# ---- quick chinese cards (2x2 grid)
@functools.lru_cache(maxsize=64)
def quick_card_parts(zh, lit, real):
    w = 470
    top = Sprite(w, 120)
    top.rrect((0, 0, w - 1, 119), 22, fill=WHITE, outline=LINE, width=2)
    top.text((w / 2, 62), "“" + zh + "”", "k", 46 if len(zh) <= 5 else 40, INK, anchor="mm")
    f = font("m", 30)
    l1 = wrap("字面：" + lit, f, w - 40)
    li = Sprite(w, 22 + 42 * len(l1))
    li.rrect((0, 0, w - 1, li.h - 1), 16, fill=WHITE, outline=LINE, width=2)
    for i, l in enumerate(l1):
        li.text((20, 10 + i * 42), l, "m", 30, INK2)
    f2 = font("b", 31)
    l2 = wrap(real, f2, w - 40)
    re_ = Sprite(w, 24 + 44 * len(l2))
    re_.rrect((0, 0, w - 1, re_.h - 1), 16, fill=TEAL)
    for i, l in enumerate(l2):
        re_.text((20, 11 + i * 44), l, "b", 31, WHITE)
    return top.img(), li.img(), re_.img()


def draw_quick(fr, c, t):
    if t < c["t0"] or (c.get("t_end") and t > c["t_end"] + 0.4):
        return
    slot = c["slot"]
    x = 60 + (slot % 2) * 490
    y = 430 + (slot // 2) * 410
    top, li, re_ = quick_card_parts(c["zh"], c["lit"], c["real"])
    t1 = c.get("t_end")
    appear(fr, top, x, y, t, c["t0"], 0.35, "pop", t1=t1)
    appear(fr, li, x, y + top.height + 8, t, c["t_lit"], 0.35, "up", 14, t1=t1)
    appear(fr, re_, x, y + top.height + 16 + li.height, t, c["t_real"], 0.5, "up", 30, t1=t1)


# ------------------------------------------------------------------ takeaway
@functools.lru_cache(maxsize=64)
def takeaway_img(text):
    body = text
    if body.startswith("这说明什么？"):
        body = body[len("这说明什么？"):]
    w = 960
    f = font("b", 46)
    lines = wrap(body, f, w - 80)
    lh = 66
    h = 96 + lh * len(lines) + 30
    s = Sprite(w, h)
    s.rrect((0, 0, w - 1, h - 1), 28, fill=INK)
    s.text((40, 50), "这说明什么？", "b", 30, (190, 226, 229), anchor="lm")
    s.rect((40, 76, 120, 80), fill=(190, 226, 229))
    y = 98
    for l in lines:
        s.text((40, y), l, "b", 46, WHITE)
        y += lh
    return s.img()


# ------------------------------------------------------------------ chapter card
@functools.lru_cache(maxsize=32)
def chapter_img(num, title):
    s = Sprite(W, 380)
    s.text((W / 2, 110), f"第 {num} 章", "m", 40, INK2, anchor="mm")
    s.rect((W / 2 - 40, 160, W / 2 + 40, 165), fill=INK)
    f = font("k", 76)
    lines = wrap(title, f, 900)
    y = 230
    for l in lines:
        s.text((W / 2, y), l, "k", 76, INK, anchor="mm")
        y += 100
    return s.img()


class Composer:
    def __init__(self, tl, scenes_mod):
        self.tl = tl
        self.scenes_mod = scenes_mod
        self.scene_cache = {}
        self.bg = gfx.flat_bg(BG)
        self.cap_chunks = []
        for line in tl["narr"]:
            if line.get("hide_caption") or line.get("takeaway"):
                continue
            self.cap_chunks.extend(caption_chunks(line))
        self.chapter_nums = {}
        n = 0
        for s in tl["segs"]:
            if s["chapter"]:
                n += 1
                self.chapter_nums[s["id"]] = n

    def scene(self, name):
        if name not in self.scene_cache:
            self.scene_cache[name] = self.scenes_mod.make(name)
        return self.scene_cache[name]

    def frame(self, t):
        tl = self.tl
        seg = TL.seg_at(tl, t)
        fr = self.bg.copy()
        # ---- illustration
        st, sname = TL.scene_at(seg, t)
        sc = self.scene(sname)
        prev = None
        idx = seg["scenes"].index((st, sname))
        if idx > 0 and t - st < 0.5:
            prev = seg["scenes"][idx - 1]
        layer = Image.new("RGBA", (W, ILL_Y1 - ILL_Y0), (0, 0, 0, 0))
        start = st + (1.0 if (idx == 0 and seg.get("chapter_t") is not None) else 0.0)
        sc.draw(layer, t, start, seg["trig"], seg)
        # slow push-in
        prog = min(1.0, max(0.0, (t - st) / 14.0))
        z = 1.0 + 0.025 * ease(prog)
        a_in = ease((t - start) / 0.5)
        if z > 1.001:
            nw, nh = int(layer.width * z), int(layer.height * z)
            big = layer.resize((nw, nh), Image.BILINEAR)
            ox, oy = (nw - layer.width) // 2, int((nh - layer.height) * 0.4)
            layer = big.crop((ox, oy, ox + layer.width, oy + layer.height))
        if prev is not None:
            psc = self.scene(prev[1])
            pl = Image.new("RGBA", (W, ILL_Y1 - ILL_Y0), (0, 0, 0, 0))
            psc.draw(pl, t, prev[0], seg["trig"], seg)
            comp(fr, pl, 0, ILL_Y0 + getattr(psc, "oy", 0), 1 - ease((t - st) / 0.5))
        comp(fr, layer, 0, ILL_Y0 + getattr(sc, "oy", 0), a_in)
        if prev is not None and hasattr(psc, "overlay"):
            ol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            psc.overlay(ol, t, prev[0], seg["trig"], seg)
            comp(fr, ol, 0, 0, 1 - ease((t - st) / 0.5))
        if hasattr(sc, "overlay"):
            tk = [l for l in tl["takeaways"] if l["seg"] == seg["id"] and l["t0"] - 0.1 <= t]
            if tk:
                ol = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                sc.overlay(ol, t, start, seg["trig"], seg)
                comp(fr, ol, 0, 0, 1 - ease((t - tk[-1]["t0"] + 0.1) / 0.3))
            else:
                sc.overlay(fr, t, start, seg["trig"], seg)
        # ---- chapter card
        if seg.get("chapter_t") is not None:
            ct = seg["chapter_t"]
            if ct <= t < ct + 1.5:
                a = ease((t - ct) / 0.3) * (1 - ease((t - ct - 1.05) / 0.4))
                im = chapter_img(self.chapter_nums.get(seg["id"], 0), seg["chapter"])
                comp(fr, im, 0, 640, a)
        # ---- cards
        for c in tl["cards"]:
            if c["kind"] == "CQ":
                draw_quick(fr, c, t)
                continue
            if c["t0"] <= t <= (c.get("t_end") or 1e9) + 0.4:
                draw_card(fr, c, t, getattr(sc, "card_y", CARD_Y))
        # ---- takeaway
        for line in tl["takeaways"]:
            if line["t0"] - 0.1 <= t <= line["t1"] + 0.9:
                im = takeaway_img(line["text"])
                y = getattr(sc, "takeaway_y", 1150)
                appear(fr, im, 60, y, t, line["t0"] - 0.1, 0.45, "up", 30, t1=line["t1"] + 0.6)
        # ---- caption
        for (a0, a1, txt) in self.cap_chunks:
            if a0 - 0.05 <= t < a1 + 0.12:
                im = caption_img(txt)
                al = min(ease((t - a0 + 0.05) / 0.12), 1 - ease((t - a1) / 0.12)) if t > a1 else ease((t - a0 + 0.05) / 0.12)
                comp(fr, im, W / 2 - im.width / 2, CAP_Y - im.height / 2, al)
                break
        # ---- header & badges
        if sname not in ("title",) and not (sname == "ending" and t > seg["trig"].get("endcard", 1e9)):
            comp(fr, header_img(seg["chapter"]), 0, 160)
        badge = None
        if seg.get("shiyi") or getattr(sc, "shiyi", False):
            badge = badge_img("shiyi")
        elif seg.get("history"):
            badge = badge_img("history")
        if badge is not None and sname != "title":
            comp(fr, badge, W - 60 - badge.width, 196)
        return fr.convert("RGB")
