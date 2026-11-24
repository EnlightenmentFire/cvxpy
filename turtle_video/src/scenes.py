"""All scenes. Each scene is f(c, x) with x a Ctx (scene-local time + cues)."""
import math
import numpy as np
import skia
from scipy.ndimage import gaussian_filter
from theme import *  # noqa
from prims import *  # noqa
import data as D


class Ctx:
    def __init__(self, t, dur, cues, frame=0):
        self.t, self.dur, self.cues, self.frame = t, dur, cues, frame

    def s(self, k):
        return self.cues[k][0] if k in self.cues else 1e9

    def e(self, k):
        return self.cues[k][1] if k in self.cues else 1e9

    def on(self, k, d=0.5, delay=0.0):
        return ramp(self.t, self.s(k) + delay, self.s(k) + delay + d)

    def since(self, k):
        return self.t - self.s(k)

    def win(self, a, b=None, d=0.45):
        t0 = self.s(a) if a else -1.0
        t1 = self.s(b) if b else self.dur + 1.0
        return fade_window(self.t, t0, t1, d)

    def prog(self, k, dur=None, delay=0.0):
        st, en = self.cues.get(k, (1e9, 1e9))
        dur = dur if dur else max(0.3, en - st)
        return clamp((self.t - st - delay) / dur)


# ================================================================ shared bits
def sketch(c, a=1.0, y=262):
    if a > 0:
        badge(c, "示意", W - MARGIN, y, GOLD, a)


def note(c, s, a=1.0, y=NOTE_Y, color=MUTED, size=25):
    if a > 0 and s:
        text(c, s, W / 2, y, "medium", size, color, a, "c")


def headline(c, s, y, a=1.0, size=64, color=CREAM, font_name="black", glow=0.0, spacing=2):
    if a > 0:
        text(c, s, W / 2, y, font_name, size, color, a, "c", spacing, glow)


def lamp(c, x, y, r, a=1.0, color=GOLD, strength=0.26):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r,
                                        [col(color, strength * a), col(color, strength * 0.35 * a), col(color, 0)],
                                        [0.0, 0.45, 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    c.drawCircle(x, y, r, p)


def chip(c, s, x, y, a=1.0, color=GOLD, size=34, fill_a=0.75, align="c", font_name="bold"):
    w = mtext_w(s, size, font_name) + 44
    h = size + 30
    x0 = x - w / 2 if align == "c" else x
    c.drawRRect(rrect(x0, y - h / 2, w, h, h / 2), fill(BG_LO, fill_a * a))
    c.drawRRect(rrect(x0, y - h / 2, w, h, h / 2), stroke(color, 2.2, a))
    mtext(c, s, x0 + w / 2, y + size * 0.36, size, color, a, "c", cjk=font_name)
    return w


def arrow(c, x0, y0, x1, y1, color, a=1.0, w=4.0, head=18):
    c.drawLine(x0, y0, x1, y1, stroke(color, w, a))
    ang = math.atan2(y1 - y0, x1 - x0)
    p = skia.Path()
    p.moveTo(x1, y1)
    p.lineTo(x1 - head * math.cos(ang - 0.45), y1 - head * math.sin(ang - 0.45))
    p.lineTo(x1 - head * math.cos(ang + 0.45), y1 - head * math.sin(ang + 0.45))
    p.close()
    c.drawPath(p, fill(color, a))


def chart_path(xs, ys, x0, y0, w, h, lo, hi, n=None):
    """Map data to a panel rectangle; returns list of points (first n)."""
    n = len(xs) if n is None else max(1, min(len(xs), int(n)))
    pts = []
    for i in range(n):
        px = x0 + (xs[i] - xs[0]) / (xs[-1] - xs[0]) * w
        py = y0 + h - (ys[i] - lo) / (hi - lo) * h
        pts.append((px, py))
    return pts


def partial_points(pts, frac):
    """Points of a polyline up to fraction frac (0..1) of its vertex count, interpolated."""
    if frac <= 0:
        return pts[:1]
    f = frac * (len(pts) - 1)
    k = int(math.floor(f))
    out = pts[:k + 1]
    if k + 1 < len(pts):
        u = f - k
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        out = out + [(xa + (xb - xa) * u, ya + (yb - ya) * u)]
    return out


# ================================================================ textures
_CACHE = {}


def _texture(w, h, base, seed, mottle=7.0, fine=5.0, edge=0.20):
    rng = np.random.default_rng(seed)
    low = gaussian_filter(rng.normal(0, 1, ((h + 3) // 4, (w + 3) // 4)), 6)
    low = np.kron(low, np.ones((4, 4)))[:h, :w]
    low = low / (np.abs(low).max() + 1e-6)
    fine_n = rng.normal(0, 1, (h, w))
    yy, xx = np.mgrid[0:h, 0:w]
    ex = np.minimum(xx, w - 1 - xx) / (w * 0.5)
    ey = np.minimum(yy, h - 1 - yy) / (h * 0.5)
    edge_f = 1 - edge * (1 - np.clip(np.minimum(ex, ey) * 4, 0, 1)) ** 2
    img = np.zeros((h, w, 4), np.float32)
    for i in range(3):
        img[..., i] = (base[i] + low * mottle + fine_n * fine) * edge_f
    img[..., 3] = 255
    return np.clip(img, 0, 255).astype(np.uint8)


def paper_image(key, w, h, base=PAPER, seed=3):
    if key not in _CACHE:
        arr = _texture(w, h, base, seed)
        _CACHE[key] = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
    return _CACHE[key]


# ================================================================ title / chapter / credits
def scene_title(c, x):
    t = x.t
    turtle(c, 540, 700, 0.95, 0, t * 0.22, GOLD, ramp(t, 0.1, 1.3), glow=9)
    text(c, "交易系列 · 第一期", 540, 1000, "medium", 40, GOLD, ramp(t, 0.5, 1.3), "c", 8)
    text(c, "海龟实验", 540, 1160, "black", 156, CREAM, ramp(t, 0.8, 1.7), "c", 12, glow=12, glow_a=0.25)
    text(c, "1983 — 1988", 540, 1252, "mono", 40, GOLD_DIM, ramp(t, 1.2, 2.1), "c", 10)


def chapter_card(c, t, dur, num, title):
    a = 1.0
    turtle(c, 540, 650, 0.40, 0, t * 0.35, GOLD, a * ramp(t, 0.0, 0.6), w=2.6)
    text(c, num, 540, 880, "medium", 40, GOLD, a * ramp(t, 0.15, 0.7), "c", 16)
    c.drawLine(470, 912, 610, 912, stroke(GOLD_DIM, 2, a * ramp(t, 0.2, 0.8)))
    size = 92 if len(title) <= 6 else 76 if len(title) <= 9 else 64
    text(c, title, 540, 1030, "black", size, CREAM, a * ramp(t, 0.3, 0.9), "c", 4)


def scene_credits(c, x):
    t = x.t
    a = ramp(t, 0.2, 1.0)
    turtle(c, 540, 470, 0.34, 0, t * 0.3, GOLD_DIM, a, w=2.2)
    text(c, "本期只讲历史和人性，不构成任何投资建议。", 540, 640, "bold", 40, CREAM, a, "c")
    lines = [
        "主要来源",
        "Curtis Faith《Way of the Turtle》(2007)",
        "Curtis Faith《The Original Turtle Trading Rules》(2003)",
        "Michael Covel《The Complete TurtleTrader》(2007)",
        "Jack Schwager《Market Wizards》(1989)",
        "《华尔街日报》1989-09-05；《洛杉矶时报》1988-08-30",
        "《纽约时报》1990-11-21；《纽约时报杂志》1976-04-25",
        "Futures 2011-03（埃克哈特）；Stocks & Commodities 2011-01（费斯）",
        "A. Garner, Active Trader, 2010-02",
        "",
        "说法不一之处已在片中注明出处，未作统一。",
        "价格图、资金曲线均为示意，不是真实行情或学员数据。",
        "人物均以剪影表示。配音由开源模型合成（Apache-2.0），",
        "音乐与音效为程序合成。",
    ]
    y = 730
    for i, s in enumerate(lines):
        aa = a * ramp(t, 0.6 + i * 0.12, 1.2 + i * 0.12)
        if i == 0:
            text(c, s, 540, y, "bold", 32, GOLD, aa, "c")
            y += 58
        elif s == "":
            y += 26
        else:
            mtext(c, s, 540, y, 25, MUTED if i < lines.index("") else CREAM, aa, "c", cjk="medium", mono="mono_r")
            y += 44


# ================================================================ cold open: newspaper
NEWS_W, NEWS_H = 940, 1300
AD = (262, 440, 416, 396)          # x, y, w, h within the page
AD_LINES = [("COMMODITY FUTURES", "news", 29), ("TRADER", "news", 40), ("", None, 8),
            ("Applications accepted.", "news_r", 25), ("A small group will be trained.", "news_r", 25),
            ("Prior experience in trading", "news_r", 25), ("is not necessary.", "news_r", 25), ("", None, 6),
            ("Chicago, Ill.", "news_r", 23)]


def newspaper_image(variant="ad"):
    key = "news_" + variant
    if key in _CACHE:
        return _CACHE[key]
    arr = _texture(NEWS_W, NEWS_H, NEWS, 11, mottle=9, fine=6, edge=0.28)
    img = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
    surf = skia.Surface(NEWS_W, NEWS_H)
    c = surf.getCanvas()
    c.drawImage(img, 0, 0)
    ink = INK
    rng = np.random.default_rng(5)
    c.drawLine(40, 54, NEWS_W - 40, 54, stroke(ink, 2.4, 0.8))
    if variant == "ad":
        text(c, "CLASSIFIED", NEWS_W / 2, 112, "news", 50, ink, 0.86, "c", 8)
    else:   # an illegible headline block: suggests a front page without imitating one
        for k, wfrac in enumerate((0.86, 0.62)):
            ww = (NEWS_W - 80) * wfrac
            c.drawRect(skia.Rect.MakeXYWH(NEWS_W / 2 - ww / 2, 74 + k * 34, ww, 24), fill(ink, 0.8))
    c.drawLine(40, 138, NEWS_W - 40, 138, stroke(ink, 3.0, 0.8))
    c.drawLine(40, 146, NEWS_W - 40, 146, stroke(ink, 1.2, 0.8))
    cols = 4
    gx, cw = 22, (NEWS_W - 80 - 3 * 22) / 4
    ax, ay, aw, ah = AD if variant == "ad" else (40, 170, NEWS_W - 80, 300)
    if variant != "ad":
        c.drawRect(skia.Rect.MakeXYWH(ax, ay, aw * 0.58, ah), fill(INK_SOFT, 0.30))
        for k in range(9):
            c.drawRect(skia.Rect.MakeXYWH(ax + aw * 0.62, ay + 6 + k * 32, aw * 0.38 * (0.6 + 0.4 * ((k * 7) % 5) / 4), 10), fill(ink, 0.36))
    for k in range(cols):
        x0 = 40 + k * (cw + gx)
        y = 176
        while y < NEWS_H - 60:
            # skip the big ad area
            if x0 + cw > ax - 4 and x0 < ax + aw + 4 and y > ay - 18 and y < ay + ah + 14:
                y = ay + ah + 26
                continue
            r = rng.random()
            if r < 0.10:   # small boxed ad
                bh = rng.integers(90, 170)
                if y + bh > NEWS_H - 60:
                    break
                if x0 + cw > ax - 4 and x0 < ax + aw + 4 and y + bh > ay - 18 and y < ay + ah:
                    y = ay + ah + 26
                    continue
                c.drawRect(skia.Rect.MakeXYWH(x0, y, cw, bh), stroke(ink, 1.6, 0.7))
                c.drawRect(skia.Rect.MakeXYWH(x0 + 22, y + 16, cw - 44, 11), fill(ink, 0.62))
                yy = y + 42
                while yy < y + bh - 14:
                    ll = cw - 30 if rng.random() > 0.2 else (cw - 30) * rng.uniform(0.4, 0.9)
                    c.drawRect(skia.Rect.MakeXYWH(x0 + 15, yy, ll, 6), fill(ink, 0.36))
                    yy += 14
                y += bh + 18
            elif r < 0.18:  # bold heading
                c.drawRect(skia.Rect.MakeXYWH(x0, y, cw * rng.uniform(0.5, 0.9), 12), fill(ink, 0.62))
                y += 26
            else:
                n = rng.integers(3, 9)
                for j in range(n):
                    ll = cw if j < n - 1 else cw * rng.uniform(0.25, 0.85)
                    c.drawRect(skia.Rect.MakeXYWH(x0, y, ll, 6.5), fill(ink, 0.33))
                    y += 15
                y += 10
    # the ad itself (illustrative wording)
    if variant != "ad":
        _CACHE[key] = surf.makeImageSnapshot()
        return _CACHE[key]
    c.drawRect(skia.Rect.MakeXYWH(ax, ay, aw, ah), fill((232, 220, 186), 0.94))
    c.drawRect(skia.Rect.MakeXYWH(ax, ay, aw, ah), stroke(ink, 3.0, 0.9))
    c.drawRect(skia.Rect.MakeXYWH(ax + 8, ay + 8, aw - 16, ah - 16), stroke(ink, 1.2, 0.9))
    yy = ay + 62
    for s, fn, sz in AD_LINES:
        if fn:
            text(c, s, ax + aw / 2, yy, fn, sz, ink, 0.95, "c", 2 if sz > 30 else 0)
        yy += sz + 11
    _CACHE[key] = surf.makeImageSnapshot()
    return _CACHE[key]


def scene_newspaper(c, x):
    t = x.t
    img = newspaper_image()
    u = smooth(t / max(1.0, x.dur))
    s = 0.66 + 0.46 * u
    ax, ay, aw, ah = AD
    fx, fy = lerp(NEWS_W / 2, ax + aw / 2, u), lerp(NEWS_H / 2, ay + ah / 2, u)
    c.save()
    c.translate(540, 760)
    c.rotate(-2.2 + 1.4 * u)
    c.scale(s, s)
    c.translate(-fx, -fy)
    sh = fill((0, 0, 0), 0.55)
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24))
    c.drawRect(skia.Rect.MakeXYWH(14, 22, NEWS_W, NEWS_H), sh)
    c.drawImage(img, 0, 0)
    spot = x.on("c_ad", 1.4)
    if spot > 0:
        r = skia.Rect.MakeXYWH(ax - 16, ay - 16, aw + 32, ah + 32)
        c.drawRect(r, stroke(GOLD, 9 / s, 0.45 * spot, blur=10 / s))
        c.drawRect(r, stroke(GOLD, 4 / s, 0.95 * spot))
    c.restore()
    spot = x.on("c_ad", 1.4)
    if spot > 0:
        rot = math.radians(-2.2 + 1.4 * u)
        dx, dy = (ax + aw / 2 - fx) * s, (ay + ah / 2 - fy) * s
        cx = 540 + dx * math.cos(rot) - dy * math.sin(rot)
        cy = 760 + dx * math.sin(rot) + dy * math.cos(rot)
        rad = (aw * s) * 0.85
        sh = skia.GradientShader.MakeRadial(skia.Point(cx, cy), rad * 2.4,
                                            [col((0, 0, 0), 0), col((0, 0, 0), 0.05 * spot), col((0, 0, 0), 0.86 * spot)],
                                            [0.0, 0.30, 0.62])
        p = skia.Paint()
        p.setShader(sh)
        c.drawRect(skia.Rect.MakeWH(W, H), p)
    sketch(c, ramp(t, 0.3, 1.0))
    a = x.on("c_apps", 0.6)
    if a > 0:
        chip(c, "1000+ 份申请", 540, 1180, a, GOLD, 40)
        note(c, "据 WSJ 1989、费斯；广告文字为示意", a, y=1262)


# ================================================================ chapter 1: the bet
def _name_card(c, name, sub, y, a):
    text(c, name, 540, y, "black", 64, CREAM, a, "c", 4)
    mtext(c, sub, 540, y + 58, 30, MUTED, a, "c", cjk="medium", mono="mono_r")


def _commodity(c, kind, x, y, a, label):
    p = stroke(GOLD, 3.2, a)
    if kind == "corn":
        cob = skia.Path()
        cob.addOval(skia.Rect.MakeLTRB(x - 22, y - 52, x + 22, y + 40))
        c.drawPath(cob, p)
        for yy in range(-38, 32, 12):
            c.drawLine(x - 16, y + yy, x + 16, y + yy, stroke(GOLD, 1.4, a * 0.8))
        for s in (-1, 1):
            lf = skia.Path()
            lf.moveTo(x, y + 52)
            lf.cubicTo(x + s * 50, y + 30, x + s * 44, y - 20, x + s * 30, y - 50)
            c.drawPath(lf, p)
    elif kind == "oil":
        d = skia.Path()
        d.moveTo(x, y - 58)
        d.cubicTo(x + 18, y - 24, x + 42, y - 2, x + 42, y + 20)
        d.cubicTo(x + 42, y + 46, x + 22, y + 60, x, y + 60)
        d.cubicTo(x - 22, y + 60, x - 42, y + 46, x - 42, y + 20)
        d.cubicTo(x - 42, y - 2, x - 18, y - 24, x, y - 58)
        c.drawPath(d, p)
        c.drawPath(polyline([(x - 18, y + 26), (x - 12, y + 40), (x + 2, y + 46)]), stroke(GOLD, 2.2, a * 0.8))
    elif kind == "gold":
        g = skia.Path()
        g.addPoly([(x - 56, y + 34), (x + 56, y + 34), (x + 38, y - 22), (x - 38, y - 22)], True)
        c.drawPath(g, p)
        g2 = skia.Path()
        g2.addPoly([(x - 26, y - 22), (x + 26, y - 22), (x + 16, y - 52), (x - 16, y - 52)], True)
        c.drawPath(g2, p)
    text(c, label, x, y + 112, "bold", 32, CREAM, a, "c")


def _pit(c, a, t):
    cx, cy = 540, 820
    for k in range(5, -1, -1):
        r = 130 + k * 66
        pts = [(cx + r * math.cos(math.pi / 8 + i * math.pi / 4), cy + 0.42 * r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        p = skia.Path()
        p.addPoly(pts, True)
        c.drawPath(p, fill(mix(BG_LO, BG_HI, 0.25 + 0.1 * k), a))
        c.drawPath(p, stroke(GOLD_DIM, 2.0, a * 0.8))
    rng = np.random.default_rng(4)
    for k in range(1, 6):
        r = 130 + k * 66 - 33
        for i in range(5 + k * 2):
            ang = rng.uniform(0, 2 * math.pi)
            px, py = cx + r * math.cos(ang), cy + 0.42 * r * math.sin(ang)
            s = 0.20 + 0.03 * (py - cy) / 120
            walker(c, px, py, s, phase=0, a=a, rim_a=0.55, walking=False)
            if rng.random() < 0.5:
                hy = py - 175 * s
                lift = 10 * math.sin(t * 6 + i)
                c.drawLine(px + 10 * s * 3, hy, px + 26 * s * 3, hy - 30 * s * 3 - lift * s, stroke(SILH, 7 * s * 3, a))


def _busts_at_table(c, a, t, x):
    lamp(c, 540, 720, 640, a, GOLD, 0.30)
    c.drawLine(540, 400, 540, 470, stroke(GOLD_DIM, 2, a * 0.7))
    shade = skia.Path()
    shade.addPoly([(470, 520), (610, 520), (580, 470), (500, 470)], True)
    c.drawPath(shade, fill(SILH, a))
    c.drawPath(shade, stroke(GOLD, 2, a * 0.8))
    c.drawOval(skia.Rect.MakeLTRB(500, 512, 580, 532), fill(GOLD_HI, a * 0.9))
    bust(c, 250, 1110, 1.06, a=a)
    bust(c, 830, 1110, 1.06, a=a, mirror=True)
    c.drawRect(skia.Rect.MakeLTRB(60, 1060, 1020, 1140), fill(SILH, a))
    c.drawLine(60, 1060, 1020, 1060, stroke(GOLD, 3, a * 0.85))
    ang = t * 2 * math.pi * 0.9
    coin(c, 540, 860 + 26 * math.sin(t * 2.2), 50, ang, GOLD, a)
    text(c, "丹尼斯", 250, 1200, "bold", 38, CREAM, a, "c")
    text(c, "埃克哈特", 830, 1200, "bold", 38, CREAM, a, "c")
    ya = x.on("b_yes", 0.4) * a
    na = x.on("b_no", 0.4) * a
    if ya > 0:
        chip(c, "能教会", 250, 610, ya, PHOS, 40)
    if na > 0:
        chip(c, "教不会", 830, 610, na, LOSS, 40)
    ea = x.on("b_exp", 0.4) * a
    if ea > 0:
        steps = ["招人", "教", "给真钱", "看结果"]
        xs = [150, 400, 650, 920]
        for i, (s, xx) in enumerate(zip(steps, xs)):
            aa = ea * ramp(x.t, x.s("b_exp") + 1.6 + i * 0.75, x.s("b_exp") + 2.0 + i * 0.75)
            chip(c, s, xx, 320, aa, GOLD, 34)
            if i < 3 and aa > 0:
                arrow(c, xx + 62 + (20 if i == 2 else 0), 320, xs[i + 1] - 66 - (20 if i + 1 == 2 else 0), 320, GOLD_DIM, aa, 3, 12)
        text(c, "实验是真的", 540, 420, "black", 44, CREAM, ea * ramp(x.t, x.s("b_exp") + 0.3, x.s("b_exp") + 0.9), "c", 4)
    da = x.win("b_deny", "b_exp", 0.4) * a
    if da > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), fill(BG, 0.84 * da))
        text(c, "埃克哈特后来的说法", 540, 470, "bold", 40, GOLD, da, "c")
        q = "“...there was no bet. Possibly an argument among hundreds of others, but no bet.”"
        y_end = _quote_block(c, q, (x.t - x.s("b_deny") - 0.5) * 26, 110, 600, 860, da, 36, CREAM, "type", lh=54, cursor_t=x.t)
        text(c, "——《Futures》杂志，2011 年 3 月", 970, y_end + 26, "medium", 26, MUTED, da, "r")
        text(c, "争论是有的，赌，没有", 540, y_end + 150, "black", 54, CREAM, da * x.on("b_deny", 0.5, 3.0), "c", 2)


def _pond(c, a, t):
    x0, y0, w, h = 90, 300, 900, 660
    c.drawRRect(rrect(x0, y0, w, h, 60), fill((10, 38, 34), a))
    c.save()
    c.clipRRect(rrect(x0, y0, w, h, 60), doAntiAlias=True)
    for k in range(9):
        cx = x0 + 120 + (k * 211) % (w - 200)
        cy = y0 + 110 + (k * 137) % (h - 200)
        ph = (t * 0.25 + k * 0.37) % 1.0
        r = 30 + 160 * ph
        c.drawOval(skia.Rect.MakeLTRB(cx - r, cy - r * 0.38, cx + r, cy + r * 0.38), stroke(PHOS_DIM, 2, a * 0.45 * (1 - ph)))
    for k in range(7):
        ang = t * 0.10 * (1 if k % 2 else -1) + k * 0.9
        cx = 540 + 300 * math.cos(ang + k) * (0.55 + 0.08 * k)
        cy = 630 + 220 * math.sin(ang * 1.3 + k * 2) * 0.8
        heading = math.degrees(ang) + (90 if k % 2 else -90) + 30 * k
        turtle(c, cx, cy, 0.20 + 0.03 * (k % 3), heading, t * 0.6 + k * 0.2, GOLD, a * 0.95, w=2.0, fill_bg=(10, 38, 34))
    c.restore()
    c.drawRRect(rrect(x0, y0, w, h, 60), stroke(GOLD_DIM, 2.5, a))


def tiny_turtle(c, x, y, s, ang, ph, color, a):
    c.save()
    c.translate(x, y)
    c.rotate(ang)
    c.scale(s, s)
    sw = math.sin(ph * 2 * math.pi)
    for sx in (-1, 1):
        for sy, L, base in ((-1, 15, 35), (1, 10, -40)):
            c.save()
            c.translate(sx * 9, sy * 7)
            c.rotate(sx * (base * -sy + 14 * sw * sy))
            c.drawOval(skia.Rect.MakeLTRB(-3.5, -L if sy < 0 else 0, 3.5, 0 if sy < 0 else L), fill(color, a))
            c.restore()
    c.drawCircle(0, -18, 5.5, fill(color, a))
    c.drawOval(skia.Rect.MakeLTRB(-12, -14, 12, 14), fill(color, a))
    c.drawOval(skia.Rect.MakeLTRB(-7.5, -9, 7.5, 9), stroke((10, 38, 34), 1.8, a))
    c.drawLine(0, -9, 0, 9, stroke((10, 38, 34), 1.4, a))
    c.restore()


def _vat(c, a, t):
    cx, cy, rx, ry = 540, 640, 420, 300
    c.drawOval(skia.Rect.MakeLTRB(cx - rx - 26, cy - ry - 26, cx + rx + 26, cy + ry + 26), fill(SILH, a))
    c.drawOval(skia.Rect.MakeLTRB(cx - rx - 26, cy - ry - 26, cx + rx + 26, cy + ry + 26), stroke(GOLD_DIM, 3, a))
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), fill((10, 38, 34), a))
    c.save()
    clip = skia.Path()
    clip.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    c.clipPath(clip, doAntiAlias=True)
    rng = np.random.default_rng(31)
    for k in range(44):
        r0 = math.sqrt(rng.random()) * 0.9
        th = rng.uniform(0, 2 * math.pi) + t * rng.uniform(-0.05, 0.05)
        px = cx + rx * r0 * math.cos(th) + 6 * math.sin(t * 1.3 + k)
        py = cy + ry * r0 * math.sin(th) + 6 * math.cos(t * 1.1 + k)
        tiny_turtle(c, px, py, rng.uniform(1.15, 1.5), rng.uniform(0, 360) + 20 * math.sin(t * 0.7 + k), t * 1.6 + k * 0.1, GOLD, a * 0.92)
    c.restore()
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), stroke(GOLD, 3, a))
    text(c, "一口大缸，几千只小海龟", 540, 990, "bold", 34, MUTED, a, "c")


def _quote_block(c, s, n_chars, x0, y0, maxw, a, size=38, color=CREAM, fn="type", lh=None, cursor_t=None):
    lines = wrap(s, fn, size, maxw)
    lh = lh or size * 1.42
    left = n_chars
    y = y0
    for ln in lines:
        k = min(len(ln), max(0, left))
        typewriter(c, ln, k, x0, y, fn, size, color, a, cursor_t if 0 < left <= len(ln) else None)
        left -= len(ln)
        y += lh
    return y


def _filmstrip(c, a, t):
    y0, h = 470, 330
    off = (t * 40) % 150
    c.drawRect(skia.Rect.MakeLTRB(0, y0, W, y0 + h), fill(SILH, a))
    for k in range(-1, 9):
        xx = k * 150 - off
        c.drawRRect(rrect(xx + 40, y0 + 14, 60, 28, 6), fill(BG_HI, a))
        c.drawRRect(rrect(xx + 40, y0 + h - 42, 60, 28, 6), fill(BG_HI, a))
    for k in range(3):
        fx = 60 + k * 330 - off * 0.0
        c.drawRect(skia.Rect.MakeXYWH(fx, y0 + 62, 300, h - 124), fill(BG_LO, a))
        c.drawRect(skia.Rect.MakeXYWH(fx, y0 + 62, 300, h - 124), stroke(GOLD_DIM, 2, a))
        cx, cy = fx + 150, y0 + h - 70
        if k == 0:
            bust(c, cx - 60, cy, 0.5, a=a, rim_a=0.7)
            bust(c, cx + 60, cy, 0.5, a=a, rim_a=0.7, mirror=True)
        elif k == 1:
            coin(c, cx, cy - 80, 40, t * 3.0, GOLD, a)
            mtext(c, "$1", cx, cy - 2, 40, GOLD, a, "c")
        else:
            walker(c, cx, cy + 8, 0.82, t * 0.7, a=a, rim_a=0.7)


def scene_bet(c, x):
    t = x.t
    # A0 Dennis
    a = x.win("b_dennis", "b_fut")
    if a > 0:
        lamp(c, 540, 700, 520, a, GOLD, 0.28)
        bust(c, 540, 1080, 1.35, a=a)
        _name_card(c, "理查德·丹尼斯", "Richard Dennis · 芝加哥期货交易员", 1180, a)
    # A1 futures
    a = x.win("b_fut", "b_long")
    if a > 0:
        x0, y0, w, h = 110, 330, 860, 900
        c.save()
        c.rotate(-1.0)
        c.drawImageRect(paper_image("contract", 860, 900, PAPER, 9), skia.Rect.MakeXYWH(x0, y0, w, h), skia.SamplingOptions(), fill(PAPER, a))
        c.restore()
        text(c, "期货合约", 540, 440, "black", 60, INK, a, "c", 6)
        c.drawLine(200, 480, 880, 480, stroke(INK, 2, a * 0.6))
        rows = [("约定", "将来某一天"), ("价格", "今天就定好"), ("买卖", "一批货")]
        for i, (k, v) in enumerate(rows):
            aa = a * ramp(t, x.s("b_fut") + 0.5 + i * 0.9, x.s("b_fut") + 0.9 + i * 0.9)
            text(c, k, 220, 580 + i * 92, "medium", 36, INK_SOFT, aa)
            text(c, v, 380, 580 + i * 92, "bold", 48, INK, aa)
        ca = a * x.on("b_fut2", 0.5)
        if ca > 0:
            for i, (kind, lab) in enumerate((("corn", "玉米"), ("oil", "原油"), ("gold", "黄金"))):
                aa = ca * ramp(t, x.s("b_fut2") + i * 0.5, x.s("b_fut2") + 0.4 + i * 0.5)
                c.save()
                _commodity(c, kind, 270 + i * 270, 930, aa, lab)
                c.restore()
        sketch(c, a)
    # A1b long / short
    a = x.win("b_long", "b_pit")
    if a > 0:
        ua = a * x.on("b_long", 0.5)
        da = a * x.on("b_long", 0.5, delay=2.6)
        arrow(c, 300, 1000, 300, 520, PHOS, ua, 10, 46)
        arrow(c, 780, 520, 780, 1000, LOSS, da, 10, 46)
        text(c, "做多", 300, 1110, "black", 64, PHOS, ua, "c")
        text(c, "做空", 780, 1110, "black", 64, LOSS, da, "c")
        sa = a * x.on("b_long2", 0.5)
        text(c, "＝ 赌涨", 300, 1190, "bold", 44, CREAM, sa, "c")
        text(c, "＝ 赌跌", 780, 1190, "bold", 44, CREAM, sa, "c")
        text(c, "先买进合约", 300, 450, "medium", 32, MUTED, ua, "c")
        text(c, "先卖出合约", 780, 450, "medium", 32, MUTED, da, "c")
    # A2 trading pit
    a = x.win("b_pit", "b_money")
    if a > 0:
        lamp(c, 540, 800, 620, a, GOLD, 0.18)
        _pit(c, a, t)
        text(c, "Prince of the Pit", 540, 420, "type", 52, GOLD, a * x.on("b_pit", 0.6, 0.3), "c")
        text(c, "“交易池王子”", 540, 500, "black", 56, CREAM, a * x.on("b_pit", 0.6, 0.6), "c")
        text(c, "《纽约时报杂志》1976 年报道的标题", 540, 550, "medium", 24, MUTED, a * x.on("b_pit", 0.6, 1.0), "c")
        note(c, "交易池：交易员面对面喊价、打手势成交", a * x.on("b_pit2", 0.5), y=1190, color=CREAM, size=32)
        sketch(c, a)
    # A2b money
    a = x.win("b_money", "b_eck")
    if a > 0:
        a1 = a * x.on("b_money", 0.5)
        a2 = a * x.on("b_money2", 0.5)
        text(c, "起家的本钱", 540, 440, "medium", 40, MUTED, a1, "c", 4)
        text(c, "几百美元？", 300, 580, "black", 70, CREAM, a1, "c")
        text(c, "几千美元？", 780, 580, "black", 70, CREAM, a * x.on("b_money", 0.5, 1.6), "c")
        text(c, "说法不一", 540, 660, "medium", 30, MUTED, a * x.on("b_money", 0.5, 2.4), "c")
        arrow(c, 540, 710, 540, 850, GOLD_DIM, a2, 4, 18)
        text(c, "到了八十年代", 540, 930, "medium", 40, MUTED, a2, "c")
        text(c, "上亿美元", 540, 1060, "black", 110, GOLD, a2, "c", 4, glow=10, glow_a=0.3)
        text(c, "据报道（《华尔街日报》1989 年称约 2 亿美元）", 540, 1130, "medium", 26, MUTED, a2, "c")
    # A3 the bet
    a = x.win("b_eck", "b_turtle")
    if a > 0:
        _busts_at_table(c, a, t, x)
        na = a * (1 - x.on("b_argue", 0.5))
        if na > 0:
            mtext(c, "William Eckhardt · 数学出身", 830, 1250, 26, MUTED, na, "c", cjk="medium", mono="mono_r")
    # A4 turtle farm + quote
    a = x.win("b_turtle", "b_film")
    if a > 0:
        _vat(c, a, t)
        q = "“We are going to grow traders just like they grow turtles in Singapore.”"
        n = (t - x.s("b_quote")) * 22
        if n > 0:
            _quote_block(c, q, n, 100, 1050, 880, a, 36, CREAM, "type", cursor_t=t)
            text(c, "—— Richard Dennis，Schwager《Market Wizards》（1989）", 980, 1250, "medium", 24, MUTED, a * x.on("b_quote", 0.5, 2.5), "r")
        sketch(c, a)
    # A5 film
    a = x.win("b_film", "b_sowhat")
    if a > 0:
        _filmstrip(c, a, t)
        text(c, "《颠倒乾坤》", 540, 940, "black", 64, CREAM, a, "c")
        mtext(c, "Trading Places · 1983 年 6 月上映 · 虚构电影", 540, 1000, 30, MUTED, a, "c", cjk="medium", mono="mono_r")
        da = a * x.on("b_film3", 0.5)
        text(c, "编剧没听说过丹尼斯，丹尼斯也否认两者有关", 540, 1120, "bold", 34, GOLD, da, "c")
        text(c, "（据 Covel《The Complete TurtleTrader》）", 540, 1170, "medium", 26, MUTED, da, "c")
        sketch(c, a)
    # A6 so what
    a = x.win("b_sowhat", None)
    if a > 0:
        lamp(c, 540, 760, 520, a, GOLD, 0.16)
        coin(c, 540, 760 + 20 * math.sin(t * 2), 64, t * 2 * math.pi * 0.7, GOLD, a)
        text(c, "天生的？", 250, 790, "black", 76, CREAM, a, "c")
        text(c, "学来的？", 830, 790, "black", 76, CREAM, a, "c")
        text(c, "本事", 540, 560, "medium", 44, MUTED, a, "c", 10)


# ================================================================ chapter 2: outsiders
JOBS = [("keyboard", "程序员"), ("ledger", "会计"), ("shield", "保安"), ("cards", "二十一点"), ("dice", "游戏设计"), ("mask", "演员")]
ROW_N, ROW_X0, ROW_DX, ROW_Y, ROW_S = 13, 72, 78, 1170, 1.22


def _envelope(c, x, y, s, a, rot=0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawRect(skia.Rect.MakeXYWH(-40 * s, -26 * s, 80 * s, 52 * s), fill(PAPER, a))
    c.drawRect(skia.Rect.MakeXYWH(-40 * s, -26 * s, 80 * s, 52 * s), stroke(PAPER_DARK, 1.5, a))
    c.drawPath(polyline([(-40 * s, -26 * s), (0, 4 * s), (40 * s, -26 * s)]), stroke(INK_SOFT, 1.5, a * 0.8))
    c.restore()


def scene_outsiders(c, x):
    t = x.t
    rng = np.random.default_rng(12)
    # applications pile -> written test
    a = x.win("o_apps", "o_interview")
    if a > 0:
        pile = a * (1 - x.on("o_test", 0.5))
        if pile > 0:
            k_show = 60 * ramp(t, x.s("o_apps") - 0.3, x.s("o_apps") + 2.0)
            for i in range(60):
                if i > k_show:
                    break
                ex, ey = rng.uniform(170, 910), rng.uniform(560, 1060)
                fall = 1 - ease_out(clamp((k_show - i) / 3))
                _envelope(c, ex, ey - 400 * fall, rng.uniform(0.9, 1.3), pile * (1 - fall * 0.8), rng.uniform(-25, 25))
            chip(c, "1000+ 份申请", 540, 420, pile, GOLD, 42)
        ta = a * x.on("o_test", 0.5)
        if ta > 0:
            c.drawImageRect(paper_image("test", 760, 820, PAPER, 21), skia.Rect.MakeXYWH(160, 360, 760, 820), skia.SamplingOptions(), fill(PAPER, ta))
            text(c, "判断对错", 540, 460, "black", 54, INK, ta, "c", 6)
            for i in range(6):
                yy = 560 + i * 98
                aa = ta * ramp(t, x.s("o_test") + 0.3 + i * 0.35, x.s("o_test") + 0.6 + i * 0.35)
                mtext(c, f"{i + 1:02d}", 210, yy + 10, 30, INK_SOFT, aa)
                for j in range(2):
                    ll = [380, 300, 420, 340, 260, 400][i] if j == 0 else [220, 180, 0, 260, 200, 120][i]
                    if ll:
                        c.drawRect(skia.Rect.MakeXYWH(270, yy - 14 + j * 26, ll, 9), fill(INK_SOFT, aa * 0.55))
                for k, lab in enumerate(("对", "错")):
                    bx = 730 + k * 82
                    c.drawRect(skia.Rect.MakeXYWH(bx, yy - 22, 34, 34), stroke(INK, 2, aa))
                    text(c, lab, bx + 17, yy + 44, "medium", 22, INK_SOFT, aa, "c")
            note(c, "题目内容为示意；题量说法也不一（63 题 / 40 题）", ta, y=1250)
            sketch(c, ta)
    # interview: dots -> a few
    a = x.win("o_interview", "o_select")
    if a > 0:
        thin = ramp(t, x.s("o_interview") + 3.0, x.s("o_interview") + 4.2)
        sel = set([3, 9, 14, 22, 27, 31, 38, 44, 51, 57, 63, 70, 76])
        for i in range(80):
            r, k = divmod(i, 10)
            cx, cy = 180 + k * 80, 560 + r * 74
            keep = i in sel
            aa = a * (1 if keep else 1 - 0.8 * thin)
            colr = GOLD if keep and thin > 0 else MUTED
            c.drawCircle(cx, cy - 16, 12, fill(colr, aa))
            c.drawRRect(rrect(cx - 14, cy, 28, 28, 9), fill(colr, aa))
        text(c, "进面试的人数", 540, 330, "bold", 40, CREAM, a, "c")
        mtext(c, "80 人（费斯 2003；WSJ 1989）", 540, 400, 32, GOLD, a, "c", cjk="bold")
        mtext(c, "40 人（费斯 2007 年的书）", 540, 452, 32, GOLD, a * x.on("o_interview", 0.5, 1.5), "c", cjk="bold")
    # the row of trainees
    a = x.win("o_select", "o_money")
    if a > 0:
        walk_u = ramp(t, x.s("o_train"), x.e("o_train") + 0.9)
        door_a = a * x.on("o_train", 0.5)
        if door_a > 0:
            lamp(c, 960, 880, 400, door_a, GOLD, 0.35)
            c.drawRect(skia.Rect.MakeLTRB(900, 740, 1010, 1170), fill(GOLD_HI, door_a * 0.85))
            c.drawRect(skia.Rect.MakeLTRB(892, 732, 1018, 1170), stroke(GOLD, 4, door_a))
            chip(c, "两周", 955, 630, door_a, GOLD, 40)
        back_a = a * x.on("o_total", 0.6) * (1 - walk_u)
        for i in range(10):
            walker(c, 150 + i * 86, 990, 0.8, a=back_a * 0.55, rim_a=0.35, walking=False)
        for i in range(ROW_N):
            bx = ROW_X0 + i * ROW_DX
            px = bx + walk_u * (1000 - bx + 80 + i * 46)
            if px > 905:
                continue
            aa = a * (1 - ramp(px, 860, 905))
            ph = (t * 1.1 + i * 0.13) if 0 < walk_u < 1 else 0
            walker(c, px, ROW_Y, ROW_S, ph, a=aa, rim_a=0.6, walking=0 < walk_u < 1)
        ja = a * x.on("o_jobs", 0.4) * (1 - walk_u)
        if ja > 0:
            for k, (ic, lab) in enumerate(JOBS):
                i = 1 + 2 * k
                bx = ROW_X0 + i * ROW_DX
                aa = ja * ramp(t, x.s("o_jobs") + 0.5 + k * 0.75, x.s("o_jobs") + 0.9 + k * 0.75)
                icon(c, ic, bx, 830, 1.25, GOLD, aa)
                text(c, lab, bx, 760, "bold", 28, CREAM, aa, "c")
                c.drawLine(bx, 866, bx, 912, stroke(GOLD_DIM, 2, aa))
            note(c, "据 Covel、彭博社 2007 年等对学员背景的记述", ja * (1 - x.on("o_faith", 0.4)), y=1250)
        fa = a * x.win("o_faith", "o_train", 0.4)
        if fa > 0:
            bx = ROW_X0 + 10 * ROW_DX
            c.drawCircle(bx, ROW_Y - 135, 92, stroke(GOLD, 3, fa))
            chip(c, "费斯 · 19 岁 · 会写程序 · 没做过交易", 540, 520, fa, GOLD, 34)
        sa = a * x.win("o_select", "o_total", 0.4)
        if sa > 0:
            chip(c, "第一期 · 十几个人", 540, 520, sa, GOLD, 40)
            note(c, "13 人（费斯书、WSJ 1989）/ 12 人 / 14 人，说法不一", sa, y=1250)
        ta = a * x.win("o_total", "o_jobs", 0.4)
        if ta > 0:
            chip(c, "两期合计 · 约 23 人", 540, 520, ta, GOLD, 40)
    # real money
    a = x.win("o_money", "o_sowhat")
    if a > 0:
        panel(c, 90, 400, 900, 700, a, title="ACCOUNT")
        mtext(c, "1984 年 1 月", 150, 560, 46, PHOS, a * x.on("o_money", 0.5), cjk="black", mono="mono_x")
        mtext(c, "小账户 · 真钱 · 试一个月", 150, 640, 40, PHOS, a * x.on("o_money", 0.5, 0.8), cjk="bold")
        aa = a * x.on("o_acct", 0.5)
        mtext(c, "过关以后：大账户", 150, 770, 40, CREAM, aa, cjk="bold")
        mtext(c, "每人 100 万美元（WSJ 1989、Covel）", 150, 870, 32, GOLD, a * x.on("o_acct", 0.5, 1.0), cjk="bold")
        mtext(c, "50 万–200 万美元（费斯 2003）", 150, 930, 32, GOLD, a * x.on("o_acct", 0.5, 1.8), cjk="bold")
        text(c, "说法不一", 150, 1010, "medium", 28, MUTED, a * x.on("o_acct", 0.5, 2.4))
    a = x.win("o_sowhat", None)
    if a > 0:
        text(c, "赌的不是人", 540, 700, "black", 92, MUTED, a, "c", 6)
        text(c, "是规则", 540, 880, "black", 120, GOLD, a * x.on("o_sowhat", 0.6, 2.2), "c", 10, glow=10, glow_a=0.3)


# ================================================================ chapter 3: one sheet of paper
RULES = [
    "波动：先量 N，平均每天晃多大",
    "仓位：晃 1N，账户盈亏 1%",
    "进场：突破 20 日 / 55 日高低点",
    "加仓：每 0.5N 加一注，最多 4 注",
    "止损：反向 2N 就走，最多亏 2%",
    "出场：反向突破 10 日 / 20 日",
    "缩小：每亏 10%，按少 20% 下注",
]
PX, PY, PW, PH = 84, 262, 912, 566
QX, QY, QW, QH = 84, 852, 912, 404


def _rule_cue(i):
    return f"r{i + 1}"


def _paper(c, x, a, slide):
    c.save()
    c.translate(0, 900 * (1 - ease_out(slide)))
    c.translate(PX + PW / 2, PY + PH / 2)
    c.rotate(-0.8)
    c.translate(-(PX + PW / 2), -(PY + PH / 2))
    sh = fill((0, 0, 0), 0.5 * a)
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    c.drawRect(skia.Rect.MakeXYWH(PX + 10, PY + 16, PW, PH), sh)
    c.drawImageRect(paper_image("rules", PW, PH, PAPER, 31), skia.Rect.MakeXYWH(PX, PY, PW, PH), skia.SamplingOptions(), fill(PAPER, a))
    t = x.t
    tn = (t - x.s("r_paper") - 0.4) * 9
    typewriter(c, "海龟交易规则 · 摘要", tn, PX + 56, PY + 78, "black", 44, INK, a, None)
    sa = a * x.on("r_paper", 0.6, 1.6)
    text(c, "据费斯 2003 年公开的《原始海龟交易规则》整理", PX + 58, PY + 122, "medium", 22, INK_SOFT, sa)
    c.drawLine(PX + 56, PY + 142, PX + PW - 56, PY + 142, stroke(INK, 1.6, sa * 0.6))
    active = None
    for i in range(7):
        st = x.s(_rule_cue(i))
        if t >= st:
            active = i
    for i, s in enumerate(RULES):
        st = x.s(_rule_cue(i))
        if t < st:
            continue
        n = (t - st) * 13
        y = PY + 204 + i * 52
        is_act = (i == active) and t < x.s("r_sum")
        col_ = INK if is_act or t >= x.s("r_sum") else INK_SOFT
        if is_act:
            c.drawRect(skia.Rect.MakeXYWH(PX + 40, y - 30, 7, 38), fill(GOLD, a))
        mtext(c, f"{i + 1}", PX + 64, y, 32, GOLD_DIM if not is_act else (150, 110, 40), a, mono="mono")
        k = int(min(len(s), n))
        mtext(c, s[:k], PX + 104, y, 33, col_, a, cjk="bold", mono="mono")
        if k < len(s):
            w = mtext_w(s[:k], 33)
            c.drawRect(skia.Rect.MakeXYWH(PX + 108 + w, y - 26, 13, 30), fill(INK, a * 0.8))
    # stamp
    sa = a * x.on("r_nosecret", 0.25)
    if sa > 0:
        sc = 1.6 - 0.6 * ease_out(x.prog("r_nosecret", 0.25))
        c.save()
        c.translate(PX + PW - 165, PY + PH - 120)
        c.rotate(-14)
        c.scale(sc * 0.86, sc * 0.86)
        c.drawRRect(rrect(-150, -56, 300, 112, 16), stroke(LOSS, 6, sa * 0.9))
        c.drawRRect(rrect(-138, -44, 276, 88, 10), stroke(LOSS, 2, sa * 0.9))
        text(c, "没有秘密", 0, 22, "black", 58, LOSS, sa * 0.92, "c", 6)
        c.restore()
    c.restore()


def _panel_title(c, s, a):
    mtext(c, s, QX + 28, QY + 48, 28, PHOS, a, cjk="bold", mono="mono")


def _trend_demo(c, x, a):
    t = x.t
    _panel_title(c, "趋势跟踪 · 示意", a)
    d = D.donchian(seed=7, brk=50)
    xs = np.arange(len(d["close"]))
    lo, hi = d["close"].min() - 4, d["close"].max() + 4
    pts = chart_path(xs, d["close"], QX + 40, QY + 80, QW - 80, QH - 120, lo, hi)
    frac = ramp(t, x.s("r_trend"), x.s("r_trend") + 5.0)
    glow_path(c, polyline(partial_points(pts, frac)), PHOS, 3.2, a, 8, 0.5)
    ta = a * ramp(t, x.s("r_trend") + 0.6, x.s("r_trend") + 1.2)
    chip(c, "不猜顶", QX + QW - 330, QY + QH - 52, ta, LOSS, 28)
    chip(c, "不猜底", QX + QW - 150, QY + QH - 52, ta * ramp(t, x.s("r_trend") + 1.2, x.s("r_trend") + 1.8), LOSS, 28)
    fa = a * ramp(t, x.s("r_trend") + 3.6, x.s("r_trend") + 4.4)
    ex, ey = pts[d["entry"] + 4]
    arrow(c, ex - 130, ey - 90, ex - 14, ey - 16, GOLD, fa, 4, 16)
    text(c, "走出来，再跟上", ex - 150, ey - 104, "bold", 30, GOLD, fa, "c")


def _n_demo(c, x, a):
    t = x.t
    _panel_title(c, "N · 真实波幅 · 示意", a)
    r = D.ranges()
    n = len(r["hi"])
    lo, hi = r["lo"].min() - 1, r["hi"].max() + 1
    x0, w = QX + 60, QW - 120
    top, h = QY + 80, QH - 130
    k_show = n * ramp(t, x.s("r1_tr"), x.s("r1_tr") + 3.0)
    drop = ramp(t, x.s("r1_n"), x.s("r1_n") + 1.4)
    rng_len = r["hi"] - r["lo"]
    tr = rng_len.copy()
    g = r["gap_day"]
    tr[g] = r["hi"][g] - min(r["lo"][g], r["hi"][g - 1])
    scale = h / (hi - lo)
    base_y = top + h
    avg = tr.mean()
    for i in range(n):
        if i >= k_show:
            break
        px = x0 + i * w / (n - 1)
        y_hi = top + (hi - r["hi"][i]) * scale
        y_lo = top + (hi - r["lo"][i]) * scale
        if i == g:
            y_lo_tr = top + (hi - min(r["lo"][i], r["hi"][i - 1])) * scale
        else:
            y_lo_tr = y_lo
        L = (y_lo_tr - y_hi)
        yb = lerp(y_lo_tr, base_y, drop)
        yt = yb - L
        colr = GOLD if i == g else PHOS
        c.drawLine(px, yt, px, yb, stroke(colr, 9, a, cap="butt"))
        if i == g and drop < 0.5:
            c.drawLine(px, y_lo, px, y_lo_tr, stroke(GOLD_HI, 9, a * 0.5, cap="butt"))
    ga = a * fade_window(t, x.s("r1_tr") + 2.2, x.s("r1_n") + 0.3, 0.4)
    if ga > 0:
        px = x0 + g * w / (n - 1)
        text(c, "跳空也算", px + 24, top + 30, "bold", 30, GOLD, ga)
    na = a * ramp(t, x.s("r1_n") + 1.2, x.s("r1_n") + 1.8)
    if na > 0:
        yN = base_y - avg * scale
        c.drawLine(x0 - 20, yN, x0 + w + 20, yN, stroke(GOLD, 3.5, na, dash=(14, 10)))
        mtext(c, "N ≈ 平均每天晃多大", x0 + w - 4, yN - 16, 30, GOLD, na, "r")


def _chips(c, x0, y0, n, a):
    for i in range(n):
        c.drawOval(skia.Rect.MakeLTRB(x0 - 46, y0 - i * 22 - 14, x0 + 46, y0 - i * 22 + 14), fill(GOLD_DIM, a))
        c.drawOval(skia.Rect.MakeLTRB(x0 - 46, y0 - i * 22 - 20, x0 + 46, y0 - i * 22 + 8), fill(GOLD, a))
        c.drawOval(skia.Rect.MakeLTRB(x0 - 30, y0 - i * 22 - 14, x0 + 30, y0 - i * 22 + 2), stroke(GOLD_DIM, 2, a))


def _sizing_demo(c, x, a):
    t = x.t
    _panel_title(c, "仓位 · 示意", a)
    rng = np.random.default_rng(3)
    for side, (big, n_chips, lab, lab2) in enumerate(((True, 1, "晃得厉害", "少买"), (False, 4, "晃得少", "多买"))):
        cx = QX + 230 + side * 450
        for i in range(7):
            hh = (rng.uniform(90, 150) if big else rng.uniform(24, 46))
            mid = QY + 200 + rng.normal(0, 18 if big else 6)
            px = cx - 150 + i * 26
            c.drawLine(px, mid - hh / 2, px, mid + hh / 2, stroke(PHOS, 7, a, cap="butt"))
        text(c, lab, cx - 72, QY + 330, "bold", 32, CREAM, a, "c")
        ca = a * x.on("r2_mk", 0.5, 0.3 + side * 1.2)
        _chips(c, cx + 110, QY + 290, n_chips, ca)
        text(c, lab2, cx + 110, QY + 352, "black", 36, GOLD, ca, "c")
    ra = a * x.on("r2_rule", 0.5)
    if ra > 0:
        chip(c, "价格晃 1N  →  账户 ±1%", 540, QY + 106, ra * (1 - x.on("r2_mk", 0.4)), GOLD, 32)


def _donchian_demo(c, x, a):
    t = x.t
    _panel_title(c, "突破 · 唐奇安通道 · 示意", a)
    d = D.donchian()
    n = len(d["close"])
    xs = np.arange(n)
    lo, hi = min(d["lo"].min(), np.nanmin(d["dn"])) - 2, d["hi"].max() + 2
    x0, y0, w, h = QX + 40, QY + 76, QW - 80, QH - 110
    frac = ramp(t, x.s("r3_def"), x.s("r3_buy") + 1.5)
    pts = chart_path(xs, d["close"], x0, y0, w, h, lo, hi)
    ba = a * x.on("r3_dc", 0.8)
    if ba > 0:
        k0 = 20
        up = chart_path(xs[k0:], d["up"][k0:], x0 + k0 * w / (n - 1), y0, w - k0 * w / (n - 1), h, lo, hi)
        dn = chart_path(xs[k0:], d["dn"][k0:], x0 + k0 * w / (n - 1), y0, w - k0 * w / (n - 1), h, lo, hi)
        kk = max(1, int(len(up) * clamp(frac * 1.05)))
        band = skia.Path()
        band.addPoly(up[:kk] + dn[:kk][::-1], True)
        c.drawPath(band, fill(GOLD, 0.10 * ba))
        c.drawPath(polyline(up[:kk]), stroke(GOLD, 2.6, ba))
        c.drawPath(polyline(dn[:kk]), stroke(GOLD, 2.6, ba))
        text(c, "过去 20 天最高", x0 + w - 6, up[min(kk, len(up)) - 1][1] - 16 if kk > 60 else y0 + 30, "medium", 24, GOLD, ba * ramp(frac, 0.5, 0.6), "r")
    glow_path(c, polyline(partial_points(pts, frac)), PHOS, 3.2, a, 8, 0.5)
    e = d["entry"]
    if frac * (n - 1) >= e:
        ex, ey = pts[e]
        ka = a * clamp((frac * (n - 1) - e) / 3)
        c.drawCircle(ex, ey, 12, fill(GOLD_HI, ka))
        c.drawCircle(ex, ey, 26, stroke(GOLD_HI, 3, ka * 0.7))
        chip(c, "买", ex - 4, ey - 70, ka, GOLD_HI, 34)
    sa = a * x.on("r3_sys", 0.5)
    if sa > 0:
        chip(c, "系统一：20 日", QX + 210, QY + QH - 44, sa * (1 - x.on("r3_skip", 0.4)), PHOS, 28)
        chip(c, "系统二：55 日", QX + 520, QY + QH - 44, sa * (1 - x.on("r3_skip", 0.4)), PHOS, 28)
    ka = a * x.win("r3_skip", "r3_guard", 0.4)
    if ka > 0:
        c.drawRRect(rrect(QX + 30, QY + QH - 150, QW - 60, 120, 14), fill(BG_LO, 0.94 * ka))
        c.drawRRect(rrect(QX + 30, QY + QH - 150, QW - 60, 120, 14), stroke(GOLD, 2, ka))
        text(c, "系统一：上一次突破若本来能赚钱 → 这次跳过", QX + 60, QY + QH - 100, "bold", 29, CREAM, ka)
        text(c, "为免漏掉大行情，用 55 日突破兜底", QX + 60, QY + QH - 54, "bold", 29, GOLD, ka)


def _units_demo(c, x, a):
    t = x.t
    _panel_title(c, "加仓 · 每 0.5N 一级 · 示意", a)
    x0, y0, w, h = QX + 70, QY + 90, QW - 140, QH - 140
    base = y0 + h - 10
    step = 64
    prog = ramp(t, x.s("r4_rule"), x.s("r4_rule") + 4.0)
    pts = [(x0, base)]
    for k in range(4):
        pts += [(x0 + 70 + k * 170, base - k * step), (x0 + 70 + k * 170 + 120, base - k * step - 10)]
    pts += [(x0 + w, base - 4 * step + 20)]
    glow_path(c, polyline(partial_points(pts, prog)), PHOS, 3.2, a, 8, 0.5)
    for k in range(4):
        ka = a * clamp((prog * (len(pts) - 1) - (1 + 2 * k)) / 1.0)
        if ka <= 0:
            continue
        px, py = x0 + 70 + k * 170, base - k * step
        c.drawLine(QX + 40, py, QX + QW - 40, py, stroke(GOLD_DIM, 1.6, ka * 0.8, dash=(8, 8)))
        chip(c, f"+{1}", px, py - 44, ka, GOLD, 28)
        if k > 0:
            text(c, "0.5N", px - 62, py + step / 2 + 8, "mono", 22, MUTED, ka, "c")
    ma = a * ramp(prog, 0.92, 1.0)
    chip(c, "最多 4 注", QX + 200, QY + 120, ma, GOLD_HI, 32)
    ca = a * x.on("r4_cap", 0.5)
    if ca > 0:
        c.drawRRect(rrect(QX + 30, QY + QH - 96, QW - 60, 70, 14), fill(BG_LO, 0.94 * ca))
        mtext(c, "合计上限：高度相关 6 注 · 松散相关 10 注 · 同方向 12 注", 540, QY + QH - 50, 25, CREAM, ca, "c", cjk="bold")


def _stop_demo(c, x, a):
    t = x.t
    qa = x.on("r5_quote", 0.5)
    ca = a * (1 - qa)
    if ca > 0:
        _panel_title(c, "止损 · 2N · 示意", ca)
        x0, y0, w, h = QX + 60, QY + 80, QW - 120, QH - 120
        entry_y = y0 + 64
        stop_y = entry_y + 176
        c.drawLine(x0, entry_y, x0 + w, entry_y, stroke(GOLD, 2.6, ca))
        text(c, "进场价", x0 + w - 90, entry_y - 14, "bold", 26, GOLD, ca, "r")
        sa = ca * x.on("r5_line", 0.6)
        c.drawLine(x0, stop_y, x0 + w, stop_y, stroke(LOSS, 3.2, sa, dash=(16, 10)))
        c.drawLine(x0 + w - 60, entry_y + 6, x0 + w - 60, stop_y - 6, stroke(MUTED, 2, sa))
        mtext(c, "2N", x0 + w - 48, (entry_y + stop_y) / 2 + 10, 30, CREAM, sa)
        text(c, "止损线", x0 + w - 90, stop_y - 14, "bold", 26, LOSS, sa, "r")
        pa = ca * x.on("r5_pct", 0.5)
        chip(c, "最多亏 2%", x0 + 150, stop_y + 46, pa, LOSS, 28)
        prog = ramp(t, x.s("r5_line") + 0.6, x.s("r5_pct") + 2.5)
        path = [(x0 + 20, entry_y), (x0 + 90, entry_y - 30), (x0 + 160, entry_y + 40), (x0 + 240, entry_y + 20),
                (x0 + 320, entry_y + 110), (x0 + 380, entry_y + 90), (x0 + 450, stop_y)]
        glow_path(c, polyline(partial_points(path, prog)), PHOS, 3.2, ca, 8, 0.5)
        if prog >= 1:
            c.drawCircle(x0 + 450, stop_y, 12, fill(LOSS, ca))
            chip(c, "离场", x0 + 560, stop_y - 40, ca * ramp(t, x.s("r5_pct") + 2.5, x.s("r5_pct") + 3.0), LOSS, 30)
    if qa > 0:
        _panel_title(c, "原文 · 原始规则第 5 章", a * qa)
        q = ("These stops were non-negotiable exits. If a particular commodity traded at the stop price, "
             "then the position was exited; each time, every time, without fail.")
        n = (t - x.s("r5_quote") - 0.3) * 30
        _quote_block(c, q, n, QX + 40, QY + 110, QW - 80, a * qa, 30, PHOS, "type", lh=46, cursor_t=t)


def _exit_demo(c, x, a):
    t = x.t
    _panel_title(c, "出场 · 示意", a)
    d = D.trend_then_reverse()
    cl, lo10 = d["close"], d["lo10"]
    n = len(cl)
    xs = np.arange(n)
    lo, hi = cl.min() - 3, cl.max() + 3
    x0, y0, w, h = QX + 40, QY + 76, QW - 80, QH - 110
    pts = chart_path(xs, cl, x0, y0, w, h, lo, hi)
    exit_i = next(i for i in range(90, n) if cl[i] < lo10[i])
    peak_i = int(np.argmax(cl[:exit_i]))
    frac = ramp(t, x.s("r6_rule"), x.s("r6_rule") + 4.5)
    kk = int(frac * exit_i)
    tl = chart_path(xs[10:], lo10[10:], x0 + 10 * w / (n - 1), y0, w - 10 * w / (n - 1), h, lo, hi)
    c.drawPath(polyline(tl[:max(1, kk - 10)]), stroke(GOLD, 2.4, a, dash=(10, 8)))
    if kk > 40:
        text(c, "10 日最低价", tl[min(len(tl) - 1, kk - 14)][0], tl[min(len(tl) - 1, kk - 14)][1] + 40, "medium", 24, GOLD, a, "c")
    ga = a * x.on("r6_give", 0.8)
    if ga > 0 and kk > peak_i:
        py = pts[peak_i][1]
        area = skia.Path()
        seg = pts[peak_i:kk + 1]
        area.addPoly([(seg[0][0], py)] + seg + [(seg[-1][0], py)], True)
        c.drawPath(area, fill(GOLD, 0.22 * ga))
        c.drawLine(pts[peak_i][0], py, pts[min(kk, exit_i)][0], py, stroke(GOLD_HI, 1.6, ga, dash=(6, 6)))
        text(c, "浮盈吐回", (pts[peak_i][0] + pts[exit_i][0]) / 2, py - 18, "bold", 28, GOLD_HI, ga, "c")
    main = pts[:kk + 1]
    glow_path(c, polyline(main), PHOS, 3.2, a, 8, 0.5)
    if kk >= exit_i:
        ex, ey = pts[exit_i]
        c.drawCircle(ex, ey, 12, fill(GOLD_HI, a))
        chip(c, "离场信号", ex - 60, ey + 70, a * ramp(frac, 0.98, 1.0), GOLD_HI, 28)


def _shrink_demo(c, x, a):
    t = x.t
    _panel_title(c, "缩小 · 示意", a)
    x0, y0 = QX + 120, QY + 110
    full = 600
    u = ramp(t, x.s("r7_ex"), x.s("r7_ex") + 1.6)
    v = ramp(t, x.s("r7_ex") + 2.4, x.s("r7_ex") + 3.6)
    w1 = full * (1 - 0.10 * u)
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, full, 70), stroke(MUTED, 2, a * 0.6, dash=(8, 8)))
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w1, 70), fill(PHOS_DIM, a))
    mtext(c, "账户  100 万" if u < 0.5 else "账户  90 万（亏 10%）", x0 + 20, y0 + 48, 32, CREAM, a)
    if v > 0:
        c.drawRect(skia.Rect.MakeXYWH(x0, y0 + 130, full * 0.8, 70), stroke(GOLD, 3, v))
        c.drawRect(skia.Rect.MakeXYWH(x0, y0 + 130, full * 0.8, 70), fill(GOLD, 0.18 * v))
        mtext(c, "按 80 万下注", x0 + 20, y0 + 178, 32, GOLD, v)
    ra = a * x.on("r7_rule", 0.5) * (1 - u)
    if ra > 0:
        chip(c, "每亏 10% → 按少 20% 的钱下注", 540, QY + QH - 60, ra, GOLD, 30)


def scene_rules(c, x):
    t = x.t
    slide = ramp(t, x.s("r_paper"), x.s("r_paper") + 1.2)
    ia = x.win("r_intro", "r_paper")
    if ia > 0:
        text(c, "两周里，", 540, 660, "black", 84, MUTED, ia, "c", 6)
        text(c, "到底教了什么？", 540, 800, "black", 96, CREAM, ia, "c", 6)
    if slide > 0:
        _paper(c, x, 1.0, slide)
    pa = x.win("r_trend", None) * (1 - x.on("r_sum", 0.6) * 0.0)
    if pa > 0:
        panel(c, QX, QY, QW, QH, pa)
        demos = [("r_trend", "r1", _trend_demo), ("r1", "r2", _n_demo), ("r2", "r3", _sizing_demo),
                 ("r3", "r4", _donchian_demo), ("r4", "r5", _units_demo), ("r5", "r6", _stop_demo),
                 ("r6", "r7", _exit_demo), ("r7", "r_sum", _shrink_demo)]
        for a_, b_, fn in demos:
            da = x.win(a_, b_, 0.35)
            if da > 0:
                fn(c, x, da * pa)
        sa = x.win("r_sum", None, 0.4) * pa
        if sa > 0:
            text(c, "7 条 · 1 张纸", 540, QY + QH / 2 + 30, "black", 80, GOLD, sa, "c", 6, glow=10, glow_a=0.3)
    # guard captions: what each rule protects against
    for g, phrase in GUARDS.items():
        ga = x.win(g, None, 0.3) * (1 - ramp(t, x.e(g) + 0.2, x.e(g) + 0.6))
        if ga > 0:
            c.drawRRect(rrect(QX + 20, QY + QH - 104, QW - 40, 84, 14), fill(BG_LO, 0.95 * ga))
            c.drawRRect(rrect(QX + 20, QY + QH - 104, QW - 40, 84, 14), stroke(GOLD, 2.4, ga))
            w0 = text(c, "它防的是  ", QX + 52, QY + QH - 48, "medium", 30, MUTED, ga)
            text(c, phrase, QX + 52 + w0, QY + QH - 48, "black", 36, GOLD_HI, ga)


GUARDS = {"r2_guard": "押错一次，就伤筋动骨", "r3_guard": "“我觉得”", "r4_guard": "看对了，却只下了一点点",
          "r5_guard": "“再等等，就回来了”", "r6_guard": "赚一点就跑", "r7_guard": "越亏越急，越急越重"}


# ================================================================ chapter 4: why it is hard
EQ = (60, 300, 960, 900)


def streak_times(x):
    """Loss events (shared with the sound design): three quick ones on
    "一笔，两笔，三笔", then four more, closer and closer together."""
    t0 = x.s("d_count")
    t_loss = [t0 + 0.35, t0 + 1.05, t0 + 1.75]
    t_rest0, t_rest1 = x.s("d_note") + 0.2, x.s("d_seventh") + 0.6
    gaps = np.array([1.0, 0.8, 0.62, 0.5])
    gaps = gaps / gaps.sum() * (t_rest1 - t_rest0)
    acc = t_rest0
    for gg in gaps:
        acc += gg
        t_loss.append(acc)
    t_big0 = x.s("d_big") + 0.2
    return t_loss, t_big0, t_big0 + 2.2


def scene_streak(c, x):
    t = x.t
    ex0, ey0, ew, eh = EQ
    pa = x.win("d_q", None)
    panel(c, ex0, ey0, ew, eh, pa, title=None)
    mtext(c, "资金曲线 · 示意", ex0 + 28, ey0 + 52, 30, PHOS, pa, cjk="bold")
    s = D.streak_equity(n_loss=7)
    path, marks = s["path"], s["marks"]
    t_loss, t_big0, t_big1 = streak_times(x)
    # how much of path to show
    idx = 0.0
    prev_t, prev_m = x.s("d_q"), 0
    for k, tl in enumerate(t_loss):
        if t >= tl:
            idx = marks[k]
            prev_t, prev_m = tl, marks[k]
        else:
            u = clamp((t - (tl - 0.55)) / 0.55)
            idx = prev_m + u * (marks[k] - prev_m) if t > tl - 0.55 else prev_m
            break
    else:
        u = clamp((t - t_big0) / (t_big1 - t_big0))
        idx = marks[len(t_loss) - 1] + ease_out(u) * (marks[-1] - marks[len(t_loss) - 1])
    gx0, gy0, gw, gh = ex0 + 60, ey0 + 140, ew - 120, eh - 230
    lo, hi = 78, 132
    xs = np.arange(len(path))
    pts = chart_path(xs, path, gx0, gy0, gw, gh, lo, hi)
    show = partial_points(pts, idx / (len(path) - 1)) if idx > 0 else pts[:1]
    ga = pa * (1 - x.on("d_give", 0.6))
    if ga > 0:
        y100 = gy0 + gh - (100 - lo) / (hi - lo) * gh
        c.drawLine(gx0, y100, gx0 + gw, y100, stroke(MUTED, 1.6, ga * 0.6, dash=(8, 8)))
        text(c, "起点", gx0 + 6, y100 - 12, "medium", 24, MUTED, ga * 0.8)
        big = t >= t_big0
        glow_path(c, polyline(show), GOLD_HI if big else PHOS, 3.4, ga, 9, 0.55)
        for k, m in enumerate(marks[:-1]):
            if t >= t_loss[k]:
                px, py = pts[m]
                c.drawCircle(px, py, 7, fill(LOSS, ga))
        n_l = sum(1 for tl in t_loss if t >= tl)
        if n_l > 0:
            cnt_a = ga * (1 - ramp(t, t_big0, t_big0 + 0.6))
            text(c, "连续亏损", ex0 + ew - 300, ey0 + 54, "bold", 32, CREAM, cnt_a, "r")
            mtext(c, f"第 {n_l} 笔", ex0 + ew - 40, ey0 + 56, 46, LOSS, cnt_a, "r", cjk="black", mono="mono_x")
        wa = ga * x.win("d_win", "d_why", 0.4)
        if wa > 0:
            chip(c, "胜率：赚钱的交易占几成", 540, ey0 + 160, wa, GOLD, 32)
            chip(c, "海龟系统：不到一半", 540, ey0 + 250, wa * x.on("d_win", 0.5, 2.6), LOSS, 32)
        na = ga * x.win("d_note", "d_seventh", 0.4)
        if na > 0:
            c.drawRRect(rrect(ex0 + 40, ey0 + eh - 130, ew - 80, 96, 14), fill(BG_LO, 0.9 * na))
            text(c, "“一年的利润，可能只来自两三笔大赚”", 540, ey0 + eh - 86, "bold", 30, GOLD, na, "c")
            text(c, "据《原始海龟交易规则》第 4 章", 540, ey0 + eh - 48, "medium", 22, MUTED, na, "c")
        ba = ga * ramp(t, t_big1 - 0.4, t_big1 + 0.3)
        if ba > 0:
            chip(c, "那一笔", pts[marks[-1]][0] - 70, pts[marks[-1]][1] + 70, ba, GOLD_HI, 34)
    # giveback
    va = pa * x.on("d_give", 0.6)
    if va > 0:
        g = D.giveback()
        prof = g["profit"]
        n = len(prof)
        lo2, hi2 = -4, 46
        pts2 = chart_path(np.arange(n), prof, gx0, gy0, gw, gh, lo2, hi2)
        prog = ramp(t, x.s("d_give") + 0.3, x.s("d_give") + 4.2)
        kk = int(prog * (n - 1))
        pk = g["peak"]
        y0l = gy0 + gh - (0 - lo2) / (hi2 - lo2) * gh
        c.drawLine(gx0, y0l, gx0 + gw, y0l, stroke(MUTED, 1.6, va * 0.6, dash=(8, 8)))
        text(c, "浮盈", gx0 + 6, gy0 + 20, "bold", 30, CREAM, va)
        glow_path(c, polyline(pts2[:min(kk, pk) + 1]), GOLD_HI, 3.6, va, 9, 0.55)
        if kk > pk:
            for i in range(pk, kk):
                u = (i - pk) / max(1, (n - 1 - pk))
                colr = mix(GOLD_HI, (70, 58, 34), u)
                c.drawLine(*pts2[i], *pts2[i + 1], stroke(colr, 3.6, va))
            hl = pts2[pk]
            c.drawLine(hl[0], hl[1], gx0 + gw, hl[1], stroke(GOLD, 1.4, va * 0.6, dash=(6, 6)))
            text(c, "到手的利润，吐回去一大截", 540, ey0 + eh - 60, "bold", 32, GOLD, va * ramp(t, x.s("d_give") + 2.4, x.s("d_give") + 3.0), "c")
        if kk >= n - 1:
            chip(c, "离场信号还没出现", pts2[-1][0] - 150, pts2[-1][1] + 70, va * ramp(prog, 0.98, 1.0), MUTED, 26)


# ================================================================ chapter 5: same paper, different people
def scene_diverge(c, x):
    t = x.t
    ex0, ey0, ew, eh = 60, 290, 960, 860
    ca = x.win("v_q", "v_two")
    if ca > 0:
        panel(c, ex0, ey0, ew, eh, ca)
        mtext(c, "资金曲线 · 示意（非真实学员数据）", ex0 + 28, ey0 + 52, 28, PHOS, ca, cjk="bold")
        d = D.diverge()
        curves, cut = d["curves"], d["cut"]
        n = len(curves[0])
        gx0, gy0, gw, gh = ex0 + 50, ey0 + 100, ew - 100, eh - 160
        allv = np.concatenate(curves)
        lo, hi = np.log(allv.min()) - 0.05, np.log(allv.max()) + 0.05
        prog = ramp(t, x.s("v_curve") + 1.0, x.s("v_split") + 2.6)
        kk = max(2, int(prog * n))
        fa = x.on("v_faith", 0.6)
        cutA = x.on("v_cut", 0.6)
        for i, cv in enumerate(curves):
            end = min(kk, cut.get(i, n))
            pts = chart_path(np.arange(n), np.log(cv), gx0, gy0, gw, gh, lo, hi, n=end)
            is_top = i == 0
            is_cut = i in cut
            colr = PHOS
            aa = ca * 0.85
            if is_top and fa > 0:
                colr = mix(PHOS, GOLD_HI, fa)
            if is_cut and cutA > 0:
                colr = mix(PHOS, GRAY, cutA)
            if fa > 0 and not is_top:
                aa *= (1 - 0.35 * fa)
            glow_path(c, polyline(pts), colr, 3.6 if is_top and fa > 0 else 2.4, aa, 6 if is_top else 0, 0.5)
            if is_cut and kk >= cut[i] and cutA > 0:
                px, py = pts[-1]
                c.drawLine(px - 14, py - 14, px + 14, py + 14, stroke(LOSS, 4, ca * cutA))
                c.drawLine(px - 14, py + 14, px + 14, py - 14, stroke(LOSS, 4, ca * cutA))
                text(c, "被除名", px + 22, py + 10, "bold", 28, LOSS, ca * cutA)
            if is_top and fa > 0 and kk > 5:
                px, py = pts[-1]
                chip(c, "费斯（据本人说法）", min(px, ex0 + ew - 220) - 60, py - 56, ca * fa, GOLD_HI, 28)
        y0 = gy0 + gh - (0 - lo) / (hi - lo) * gh
        c.drawLine(gx0, y0, gx0 + gw, y0, stroke(MUTED, 1.4, ca * 0.5, dash=(8, 8)))
        text(c, "同一个起点", gx0 + 4, y0 + 34, "medium", 24, MUTED, ca)
        m2 = ca * x.win("v_faith2", "v_cut", 0.4)
        if m2 > 0:
            mtext(c, "约 3150 万美元", 540, ey0 + eh - 104, 52, GOLD, m2, "c", cjk="black", mono="mono_x")
            text(c, "《华尔街日报》报道（见费斯书封）；是否最好，说法不一", 540, ey0 + eh - 52, "medium", 24, MUTED, m2, "c")
        s1 = ca * x.on("v_sum1", 0.5)
        s2 = ca * x.on("v_sum2", 0.5)
        if s1 > 0 or s2 > 0:
            c.drawRRect(rrect(ex0 + 30, ey0 + 90, 520, 70, 12), fill(BG_LO, 0.9 * s1))
            text(c, "最好的：一贯照规则进场", ex0 + 50, ey0 + 136, "bold", 30, GOLD_HI, s1)
            c.drawRRect(rrect(ex0 + 30, ey0 + eh - 140, 700, 70, 12), fill(BG_LO, 0.9 * s2))
            text(c, "最差和被除名的：该进时没进", ex0 + 50, ey0 + eh - 94, "bold", 30, LOSS, s2)
    # two kinds of drift
    a = x.win("v_two", "v_quote")
    if a > 0:
        text(c, "两种走样", 540, 400, "black", 72, CREAM, a, "c", 6)
        text(c, "（据费斯《Way of the Turtle》）", 540, 460, "medium", 26, MUTED, a, "c")
        a1 = a * x.on("v_one1", 0.5)
        c.drawRRect(rrect(90, 520, 900, 300, 22), fill(BG_LO, 0.9 * a1))
        c.drawRRect(rrect(90, 520, 900, 300, 22), stroke(GOLD_DIM, 2, a1))
        lk = skia.Path()
        lk.addRRect(rrect(160, 640, 90, 74, 10))
        c.drawPath(lk, stroke(GOLD, 4, a1))
        arc = skia.Path()
        arc.moveTo(176, 640)
        arc.cubicTo(176, 586, 234, 586, 234, 640)
        c.drawPath(arc, stroke(GOLD, 4, a1))
        text(c, "?", 205, 698, "mono", 40, GOLD, a1, "c")
        text(c, "怀疑丹尼斯藏着“秘密”", 300, 640, "bold", 38, CREAM, a1)
        text(c, "→ 怀疑和不安，让他没法照规则做", 300, 710, "bold", 32, GOLD, a * x.on("v_one3", 0.5))
        text(c, "第一年没到头，被除名", 300, 770, "medium", 26, MUTED, a * x.on("v_one1", 0.5, 1.0))
        a2 = a * x.on("v_other1", 0.5)
        c.drawRRect(rrect(90, 860, 900, 300, 22), fill(BG_LO, 0.9 * a2))
        c.drawRRect(rrect(90, 860, 900, 300, 22), stroke(GOLD_DIM, 2, a2))
        st = [(150, 1080), (190, 1080), (190, 1040), (230, 1040), (230, 1000), (270, 1000), (270, 960)]
        c.drawPath(polyline(st), stroke(GOLD, 4, a2))
        text(c, "悄悄改规则：加仓慢一点", 320, 980, "bold", 38, CREAM, a2)
        text(c, "→ 看着更稳，可能反而更容易碰到止损", 320, 1050, "bold", 32, GOLD, a * x.on("v_other2", 0.5))
    # the quote
    a = x.win("v_quote", "v_later")
    if a > 0:
        q = ("“I always say that you could publish trading rules in the newspaper and no one would follow them. "
             "The key is consistency and discipline. Almost anybody can make up a list of rules that are 80 percent as good "
             "as what we taught our people. What they couldn't do is give them the confidence to stick to those rules "
             "even when things are going bad.”")
        n = (t - x.s("v_q1") + 0.2) * 24
        y_end = _quote_block(c, q, max(0, n), 96, 400, 888, a, 33, CREAM, "type", lh=48, cursor_t=t)
        text(c, "—— Richard Dennis，引自 Schwager《Market Wizards》（1989）", 984, y_end + 30, "medium", 24, MUTED, a * x.on("v_q1", 0.5, 1.0), "r")
        ea = a * x.on("v_explain", 0.5)
        if ea > 0:
            c.drawRect(skia.Rect.MakeXYWH(96, y_end + 70, 888, 4), fill(GOLD, ea))
            text(c, "规则不值钱，值钱的是守得住", 540, y_end + 150, "black", 52, GOLD, ea, "c", 2)
    # later careers
    a = x.win("v_later", "v_money")
    if a > 0:
        rows = [("杰里·帕克", "Jerry Parker", "Chesapeake Capital"), ("利兹·谢瓦尔", "Liz Cheval", "EMC Capital"),
                ("汤姆·尚克斯", "Tom Shanks", "Hawksbill Capital")]
        text(c, "后来自立门户的学员（部分）", 540, 430, "bold", 40, GOLD, a, "c")
        for i, (zh, en, firm) in enumerate(rows):
            aa = a * ramp(t, x.s("v_later") + 1.6 + i * 0.7, x.s("v_later") + 2.1 + i * 0.7)
            y = 580 + i * 190
            bust(c, 190, y + 70, 0.42, a=aa, rim_a=0.7)
            text(c, zh, 290, y, "black", 46, CREAM, aa)
            text(c, f"{en} · {firm}", 290, y + 52, "mono_r", 28, MUTED, aa)
        note(c, "方法与海龟规则相近，但不完全一样", a * x.on("v_later", 0.5, 5.0), y=1190, color=CREAM, size=30)
    # money: three figures, three sources
    a = x.win("v_money", "v_sowhat")
    if a > 0:
        text(c, "海龟们一共赚了多少？", 540, 420, "black", 56, CREAM, a, "c")
        text(c, "说法不一，不作统一", 540, 480, "medium", 30, MUTED, a, "c")
        rows = [("超过 1 亿美元", "Covel 网站；费斯书"),
                ("约 1.75 亿美元", "常见转引；最早见于一位学员的课程宣传"),
                ("毛利约 1.5 亿，“我们赚了 1.1 亿”", "丹尼斯接受 Art Collins 访谈（Covel 书引）")]
        for i, (num, src) in enumerate(rows):
            aa = a * ramp(t, x.s("v_money") + 2.2 + i * 1.3, x.s("v_money") + 2.7 + i * 1.3)
            y = 620 + i * 190
            c.drawRRect(rrect(90, y - 70, 900, 150, 16), fill(BG_LO, 0.85 * aa))
            c.drawRRect(rrect(90, y - 70, 900, 150, 16), stroke(GOLD_DIM, 2, aa))
            mtext(c, num, 130, y, 44 if i < 2 else 36, GOLD, aa, cjk="black", mono="mono_x")
            mtext(c, src, 130, y + 52, 26, MUTED, aa, cjk="medium", mono="mono_r")
    a = x.win("v_sowhat", None)
    if a > 0:
        text(c, "差别不在规则", 540, 700, "black", 84, MUTED, a, "c", 6)
        text(c, "在执行", 540, 860, "black", 120, GOLD, a * x.on("v_sowhat", 0.6, 2.0), "c", 10, glow=10, glow_a=0.3)


# ================================================================ chapter 6: 1988
def _fax(c, a, t, x):
    bx, by = 260, 640
    body = skia.Path()
    body.addRRect(rrect(bx, by, 560, 280, 24))
    c.drawPath(body, fill(SILH, a))
    c.drawPath(body, stroke(GOLD_DIM, 3, a))
    c.drawRRect(rrect(bx + 40, by + 40, 200, 70, 8), stroke(GOLD_DIM, 2, a))
    for i in range(3):
        for j in range(4):
            c.drawRRect(rrect(bx + 290 + j * 56, by + 50 + i * 58, 40, 38, 6), stroke(GOLD_DIM, 2, a))
    c.drawRect(skia.Rect.MakeXYWH(bx + 60, by - 8, 440, 16), fill(BG_LO, a))
    u = ramp(t, x.s("t_end") + 0.4, x.s("t_end") + 3.4)
    ph = 360 * u
    if ph > 2:
        c.drawRect(skia.Rect.MakeXYWH(bx + 90, by - ph, 380, ph), fill(PAPER, a))
        c.drawRect(skia.Rect.MakeXYWH(bx + 90, by - ph, 380, ph), stroke(PAPER_DARK, 1.5, a))
        if ph > 120:
            text(c, "项目结束", bx + 280, by - ph + 110, "black", 54, INK, a, "c", 6)
            for k in range(3):
                if ph > 170 + k * 40:
                    c.drawRect(skia.Rect.MakeXYWH(bx + 140, by - ph + 160 + k * 40, 280 - k * 50, 9), fill(INK_SOFT, a * 0.5))


def scene_1988(c, x):
    t = x.t
    dark = fill((0, 0, 0), 0.25)
    c.drawRect(skia.Rect.MakeWH(W, H), dark)
    a = x.win("t_1988", "t_funds")
    if a > 0:
        text(c, "1988", 540, 860, "mono_x", 260, GOLD_DIM, a, "c", 10, glow=16, glow_a=0.25)
    a = x.win("t_funds", "t_april")
    if a > 0:
        text(c, "替外部投资人管钱", 540, 560, "black", 64, CREAM, a, "c")
        mtext(c, "含经德崇证券（Drexel Burnham Lambert）", 540, 650, 32, MUTED, a, "c", cjk="medium", mono="mono_r")
        text(c, "发售的公众基金", 540, 700, "medium", 32, MUTED, a, "c")
        ca = a * x.on("t_crash", 0.5)
        if ca > 0:
            pts = [(200, 860), (380, 850), (520, 870), (600, 880), (640, 1100), (760, 1080), (880, 1120)]
            glow_path(c, polyline(partial_points(pts, x.prog("t_crash", 2.0))), LOSS, 4, ca, 8, 0.5)
            mtext(c, "1987.10 美国股市崩盘", 540, 1210, 36, LOSS, ca, "c", cjk="bold")
            sketch(c, ca)
    a = x.win("t_april", "t_end")
    if a > 0:
        # calendar
        c.drawRRect(rrect(340, 290, 400, 220, 18), fill(PAPER, a * 0.92))
        c.drawRect(skia.Rect.MakeXYWH(340, 290, 400, 64), fill(LOSS, a * 0.9))
        mtext(c, "1988", 540, 338, 40, CREAM, a, "c", mono="mono_x")
        text(c, "4 月", 540, 470, "black", 96, INK, a, "c")
        base = 620
        ba = a * x.on("t_april", 0.6, 3.0)
        h1 = 520 * ease_out(x.prog("t_april", 1.6, 3.0)) * 0.55 / 0.55
        c.drawRect(skia.Rect.MakeXYWH(230, base, 220, h1 * 1.0), fill(LOSS, ba))
        mtext(c, "−55%", 340, base + h1 + 70, 64, LOSS, ba, "c", mono="mono_x")
        text(c, "丹尼斯", 340, base - 24, "bold", 36, CREAM, ba, "c")
        ta = a * x.on("t_turtles", 0.6)
        h2 = 520 * 0.11 / 0.55 * ease_out(x.prog("t_turtles", 1.2))
        c.drawRect(skia.Rect.MakeXYWH(630, base, 220, h2), fill(GOLD_DIM, ta))
        mtext(c, "约 −10%~−12%", 740, base + h2 + 64, 44, GOLD, ta, "c", mono="mono_x")
        text(c, "学员（一般）", 740, base - 24, "bold", 36, CREAM, ta, "c")
        c.drawLine(160, base, 920, base, stroke(MUTED, 2, a))
        note(c, "据 Covel《The Complete TurtleTrader》；书中附表里学员当月从 +5.4% 到 −18.3% 不等", ta, y=1250, size=22)
        sa = a * x.on("t_shannon", 0.5)
        if sa > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill(BG, 0.93 * sa))
            text(c, "“有一天我们算过，", 540, 640, "black", 58, CREAM, sa, "c")
            text(c, "他的风险大概是我们的一百倍。”", 540, 730, "black", 58, CREAM, sa, "c")
            text(c, "—— 学员迈克尔·香农（据 Covel 书）", 540, 820, "medium", 28, MUTED, sa, "c")
            q = "“...his risk was probably one hundred times greater than the risk we were taking.”"
            _quote_block(c, q, 999, 130, 940, 820, sa * 0.85, 28, GOLD_DIM, "type_r", lh=40)
    a = x.win("t_end", "t_aug")
    if a > 0:
        _fax(c, a * (1 - x.on("t_why", 0.5)), t, x)
        sketch(c, a)
        da = a * fade_window(t, x.s("t_end") + 1.0, x.s("t_dimaria"), 0.5)
        if da > 0:
            text(c, "据 Covel：丹尼斯发传真通知项目结束", 540, 1110, "bold", 32, GOLD, da, "c")
        ma = a * x.win("t_dimaria", "t_why", 0.4)
        if ma > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill(BG, 0.93 * ma))
            text(c, "“星期一早上来人说：", 540, 640, "black", 58, CREAM, ma, "c")
            text(c, "到星期五，就结束了。”", 540, 730, "black", 58, CREAM, ma, "c")
            text(c, "—— 学员吉姆·迪马里亚（据 Covel 书）", 540, 820, "medium", 28, MUTED, ma, "c")
            _quote_block(c, "“They came in Monday morning and said, 'Friday, we're done.'”", 999, 140, 930, 800, ma * 0.85, 28, GOLD_DIM, "type_r", lh=40)
        wa = a * x.win("t_why", "t_reasons", 0.4)
        if wa > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill(BG, 0.93 * wa))
            text(c, "为什么停？", 540, 690, "black", 80, CREAM, wa, "c")
            text(c, "原因“从未正式说明过”—— Covel", 540, 790, "bold", 36, MUTED, wa, "c")
        ra = a * x.on("t_reasons", 0.4)
        if ra > 0:
            rows = [("法律上的麻烦，律师建议停下", "费斯，2011 年的访谈"),
                    ("基金的亏损", "部分学员的说法"),
                    ("家里的事", "也有学员这么说")]
            text(c, "为什么停？说法不一", 540, 330, "black", 56, CREAM, ra, "c")
            for i, (r_, s_) in enumerate(rows):
                aa = ra * ramp(t, x.s("t_reasons") + 0.3 + i * 2.6, x.s("t_reasons") + 0.8 + i * 2.6)
                y = 440 + i * 150
                c.drawRRect(rrect(110, y, 860, 120, 16), fill(BG_LO, 0.94 * aa))
                c.drawRRect(rrect(110, y, 860, 120, 16), stroke(GOLD_DIM, 2, aa))
                text(c, r_, 150, y + 56, "bold", 38, CREAM, aa)
                mtext(c, s_, 150, y + 98, 25, MUTED, aa, cjk="medium")
            note(c, "Covel：停掉的原因“从未正式说明过”", ra * x.on("t_reasons", 0.5, 6.0), y=1250)
    a = x.win("t_aug", "t_suit")
    if a > 0:
        c.save()
        c.translate(540, 760)
        c.rotate(1.5)
        c.drawImageRect(newspaper_image("headline"), skia.Rect.MakeXYWH(-330, -430, 660, 860), skia.SamplingOptions(), fill(NEWS, a * 0.9))
        c.restore()
        c.drawRect(skia.Rect.MakeXYWH(150, 1060, 780, 170), fill(BG_LO, 0.9 * a))
        mtext(c, "1988 年 8 月：宣布退出交易", 540, 1124, 42, CREAM, a, "c", cjk="black")
        mtext(c, "转向“公共政策和政治”（据《洛杉矶时报》1988-08-30）", 540, 1186, 27, MUTED, a, "c", cjk="medium", mono="mono_r")
        sketch(c, a)
    a = x.win("t_suit", "t_sowhat")
    if a > 0:
        c.drawImageRect(paper_image("legal", 820, 820, PAPER, 41), skia.Rect.MakeXYWH(130, 330, 820, 820), skia.SamplingOptions(), fill(PAPER, a))
        text(c, "投资人起诉", 540, 450, "black", 60, INK, a, "c", 4)
        text(c, "据 Covel：投资人认为他偏离了自己的交易规则", 540, 520, "medium", 28, INK_SOFT, a * x.on("t_suit", 0.5, 2.0), "c")
        s1 = a * x.on("t_settle", 0.5)
        mtext(c, "1990 年和解", 540, 650, 46, INK, s1, "c", cjk="black")
        mtext(c, "近 6000 名投资人 · 分到 250 万美元", 540, 724, 40, INK, s1 * x.on("t_settle", 0.5, 1.6), "c", cjk="bold")
        text(c, "（另加此后三年交易利润的一半）", 540, 772, "medium", 26, INK_SOFT, s1 * x.on("t_settle", 0.5, 1.6), "c")
        s2 = a * x.on("t_settle", 0.5, 4.2)
        c.drawRRect(rrect(200, 820, 680, 110, 14), stroke(LOSS, 4, s2))
        text(c, "丹尼斯一方：不承认有过错", 540, 892, "black", 46, LOSS, s2, "c")
        note(c, "据《纽约时报》1990-11-21；Covel 书", s1, y=1060, color=INK_SOFT)
        da = a * x.on("t_diff", 0.5)
        if da > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), fill(BG, 0.94 * da))
            text(c, "那一年的做法", 540, 600, "black", 64, CREAM, da, "c")
            text(c, "和教给学员的不一样", 540, 690, "black", 64, CREAM, da, "c")
            text(c, "具体怎么不一样，外人说不清", 540, 780, "bold", 38, MUTED, da, "c")
            q = "“His losses were not the result of pure trend-following trading...” —— Covel"
            _quote_block(c, q, 999, 120, 920, 840, da * 0.9, 27, GOLD, "type_r", lh=40)
    a = x.win("t_sowhat", None)
    if a > 0:
        lamp(c, 540, 760, 520, a, GOLD, 0.14)
        coin(c, 540, 760 + 20 * math.sin(t * 2), 64, t * 2 * math.pi * 0.5, GOLD, a)
        ba = a * x.on("t_bet", 0.5)
        text(c, "赢在学生身上", 540, 560, "black", 72, PHOS, ba, "c", 4)
        text(c, "输在自己身上", 540, 1010, "black", 72, LOSS, ba * x.on("t_bet", 0.5, 1.8), "c", 4)


# ================================================================ chapter 7: is following always right?
def scene_doubt(c, x):
    t = x.t
    a = x.win("q_q", "q_bt")
    if a > 0:
        text(c, "照做，", 540, 680, "black", 110, MUTED, a, "c", 8)
        text(c, "就一定对吗？", 540, 840, "black", 110, CREAM, a, "c", 8)
    a = x.win("q_bt", "q_hard")
    if a > 0:
        panel(c, 90, 360, 900, 520, a)
        mtext(c, "回测 · 示意", 118, 412, 28, PHOS, a, cjk="bold")
        c.drawLine(160, 760, 920, 760, stroke(MUTED, 2, a))
        for i, yr in enumerate(("1970", "1980", "1990", "2000", "2010")):
            px = 180 + i * 180
            c.drawLine(px, 752, px, 768, stroke(MUTED, 2, a))
            text(c, yr, px, 806, "mono_r", 26, MUTED, a, "c")
        rw = ramp(t, x.s("q_bt") + 0.8, x.s("q_bt") + 3.2)
        px = lerp(920, 180, rw)
        arrow(c, 920, 640, px, 640, GOLD, a, 4, 18)
        text(c, "拿过去的行情，假装照规则做一遍", 540, 560, "bold", 36, CREAM, a, "c")
        ba = a * x.on("q_bt2", 0.5)
        if ba > 0:
            c.drawRRect(rrect(90, 920, 900, 230, 18), fill(BG_LO, 0.92 * ba))
            c.drawRRect(rrect(90, 920, 900, 230, 18), stroke(GOLD, 2, ba))
            text(c, "据回测：后来的效果，比八十年代差很多", 540, 1000, "black", 38, GOLD, ba, "c")
            mtext(c, "例：A. Garner，Active Trader 2010 年 2 月", 540, 1060, 26, MUTED, ba, "c", cjk="medium", mono="mono_r")
            mtext(c, "回测系统一：九十年代初以后基本不赚钱", 540, 1104, 26, MUTED, ba, "c", cjk="medium", mono="mono_r")
    a = x.win("q_hard", "q_split")
    if a > 0:
        text(c, "这才是", 540, 700, "black", 92, MUTED, a, "c", 6)
        text(c, "真正难的地方", 540, 850, "black", 110, CREAM, a, "c", 6)
    a = x.win("q_split", "q_either")
    if a > 0:
        cv = D.drawdown_curve()
        for side, lab in enumerate(("正常的回撤？", "规则失效了？")):
            px0 = 60 + side * 490
            panel(c, px0, 360, 470, 760, a, grid=50)
            lo, hi = cv.min() - 0.05, cv.max() + 0.05
            prog = ramp(t, x.s("q_split") + 0.4, x.s("q_split") + 3.4)
            pts = chart_path(np.arange(len(cv)), cv, px0 + 30, 480, 410, 560, lo, hi)
            pk = int(np.argmax(cv))
            show = partial_points(pts, prog)
            glow_path(c, polyline(show[:pk + 1]), PHOS, 3.0, a, 6, 0.5)
            if len(show) > pk + 1:
                glow_path(c, polyline(show[pk:]), LOSS, 3.0, a, 6, 0.5)
            text(c, lab, px0 + 235, 440, "black", 44, CREAM if side == 0 else GOLD, a, "c")
        sa = a * x.on("q_same", 0.5)
        if sa > 0:
            chip(c, "一模一样", 540, 1180, sa, GOLD_HI, 38)
        sketch(c, a, y=262)
    a = x.win("q_either", "q_slogan")
    if a > 0:
        grid = [("坚持下去", "纪律", "固执", 0), ("改掉它", "灵活", "怯懦", 1)]
        for r, (head, good, bad, _) in enumerate(grid):
            y = 520 + r * 330
            aa = a * ramp(t, x.s("q_either") + r * 2.4, x.s("q_either") + 0.5 + r * 2.4)
            text(c, head, 540, y, "bold", 40, MUTED, aa, "c")
            text(c, good, 330, y + 130, "black", 92, PHOS, aa, "c")
            text(c, "还是", 540, y + 118, "medium", 34, MUTED, aa, "c")
            text(c, bad, 750, y + 130, "black", 92, LOSS, aa, "c")
    a = x.win("q_slogan", None)
    if a > 0:
        c.save()
        c.translate(540, 760)
        c.rotate(-1.2)
        c.drawImageRect(paper_image("think", 860, 640, PAPER, 51), skia.Rect.MakeXYWH(-430, -320, 860, 640), skia.SamplingOptions(), fill(PAPER, a))
        text(c, "亏钱之前，先写下来", 0, -200, "black", 46, INK, a, "c", 2)
        ta = a * x.on("q_think", 0.5)
        for i, s in enumerate(("亏多少，算正常：", "亏多久，算正常：")):
            yy = -60 + i * 150
            aa = ta * ramp(t, x.s("q_think") + 0.8 + i * 1.6, x.s("q_think") + 1.3 + i * 1.6)
            text(c, s, -350, yy, "bold", 44, INK, aa)
            c.drawLine(40, yy + 10, 350, yy + 10, stroke(INK, 3, aa))
        c.restore()


# ================================================================ ending
def scene_ending(c, x):
    t = x.t
    lines = [("e1", "规则，可以登在报纸上。", CREAM), ("e2", "可扛住连亏的那几个月，", CREAM), ("e2b", "没人能替你。", CREAM),
             ("e3", "包括写规则的那个人。", GOLD)]
    ys = [470, 610, 700, 860]
    for (cue, s, colr), y in zip(lines, ys):
        k = "e2" if cue == "e2b" else cue
        aa = x.on(k, 0.8, 1.2 if cue == "e2b" else 0.0)
        text(c, s, 540, y, "black", 64, colr, aa, "c", 2)
    u = clamp((t - x.s("e1")) / max(1.0, x.dur - x.s("e1")))
    tx = lerp(540, 1240, ease_in(u))
    turtle(c, tx, 1130, 0.46, 90, t * 0.55, GOLD, ramp(t, 0.2, 1.4), w=2.6, glow=6)


SCENES = {
    "newspaper": scene_newspaper, "title": scene_title, "bet": scene_bet, "outsiders": scene_outsiders,
    "rules": scene_rules, "streak": scene_streak, "diverge": scene_diverge, "y1988": scene_1988,
    "doubt": scene_doubt, "ending": scene_ending, "credits": scene_credits,
}
