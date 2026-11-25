# -*- coding: utf-8 -*-
"""Per-scene drawing. Each scene function gets a Ctx and returns a PIL RGBA 1080x1920 image.
Ctx.t: local time (s); Ctx.L[i]: (start, end) of line i (local); Ctx.dur: scene duration."""
import math, functools
import numpy as np, cv2
from PIL import Image, ImageDraw
from gfx import *  # noqa


class Ctx:
    def __init__(self, t, dur, L, sid):
        self.t, self.dur, self.L, self.sid = t, dur, L, sid

    def s(self, i):
        i = min(i, len(self.L) - 1)
        return self.L[i][0]

    def e(self, i):
        i = min(i, len(self.L) - 1)
        return self.L[i][1]

    def p(self, i, d=0.6, off=0.0):
        return ramp(self.t, self.s(i) + off, d)

    def frac(self, i):
        a, b = self.L[min(i, len(self.L) - 1)]
        return clamp((self.t - a) / max(0.01, b - a))

    def cur(self):
        k = 0
        for i, (a, b) in enumerate(self.L):
            if self.t >= a:
                k = i
        return k


@functools.lru_cache(maxsize=None)
def bg_paper(seed=1):
    return Image.fromarray(paper(seed)).convert("RGBA")


@functools.lru_cache(maxsize=None)
def bg_night(seed=3):
    return Image.fromarray(night_bg(seed)).convert("RGBA")


@functools.lru_cache(maxsize=None)
def bg_mountains(seed=5, dark=False):
    base = (paper(seed) if not dark else night_bg(seed)).astype(np.float32)
    col1 = (60, 70, 76) if not dark else (60, 70, 92)
    base = over(base, ridge_layer(560, 160, seed + 1, col1, 0.30, 4, 500))
    base = over(base, ridge_layer(760, 120, seed + 2, (50, 56, 60) if not dark else (40, 46, 66), 0.45, 3, 600))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


def new_canvas(bg):
    return bg.copy()


def label_box(img, cx, cy, text, f=None, fg=INK, bgc=(244, 234, 210), border=INK, pad=22, alpha=1.0, bw=4):
    if alpha <= 0.01:
        return
    f = f or font("serif", 44)
    tw, th = text_size(text, f)
    lay = pil_rgba(tw + 2 * pad + 8, th + 2 * pad + 8)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([4, 4, lay.width - 4, lay.height - 4], radius=10, fill=bgc + (235,), outline=border + (255,), width=bw)
    draw_text(lay, (lay.width / 2, lay.height / 2 - th * 0.06), text, f, fg + (255,))
    paste(img, lay, cx, cy, alpha)


def tablet(img, cx, cy, text, f=None, alpha=1.0, color=(214, 186, 128), ink=INK, w=96):
    """Vertical bamboo/wood slip with characters top-down."""
    if alpha <= 0.01:
        return
    f = f or font("serif_tc", 54)
    n = len(text)
    h = int(n * f.size * 1.12 + 60)
    lay = pil_rgba(w, h)
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([2, 2, w - 2, h - 2], radius=14, fill=color + (255,), outline=(110, 80, 40, 255), width=3)
    for i, ch in enumerate(text):
        draw_text(lay, (w / 2, 30 + f.size * 0.56 + i * f.size * 1.12), ch, f, ink + (255,), trad=True)
    paste(img, lay, cx, cy, alpha)


def big_text(img, cx, cy, text, f, fill=INK, alpha=1.0, stroke=0, stroke_fill=None, maxw=980):
    lines = balanced_wrap(text, f, maxw)
    lh = f.size * 1.3
    y0 = cy - lh * (len(lines) - 1) / 2
    for i, l in enumerate(lines):
        draw_text(img, (cx, y0 + i * lh), l, f, fill, alpha=alpha, stroke=stroke, stroke_fill=stroke_fill)


def stamp(img, text, cx, cy, size, t, t0, rot=-6, color=RED):
    """Seal slams in: scale 1.6->1, alpha 0->1 over 0.25s."""
    if t < t0:
        return
    k = clamp((t - t0) / 0.25)
    sc = 1.6 - 0.6 * ease_out(k)
    paste(img, seal(text, size, color, rot), cx, cy, alpha=k, scale=sc)


def cn_num(n):
    d = "〇一二三四五六七八九"
    return "".join(d[int(c)] for c in str(n))


# ───────────────────────── map (示意) ─────────────────────────
MAP = dict(lon0=99.5, lon1=124.5, lat0=20.5, lat1=42.5, x0=40, x1=1040, y0=330, y1=1400)


def proj(lon, lat):
    m = MAP
    x = m["x0"] + (lon - m["lon0"]) / (m["lon1"] - m["lon0"]) * (m["x1"] - m["x0"])
    y = m["y1"] - (lat - m["lat0"]) / (m["lat1"] - m["lat0"]) * (m["y1"] - m["y0"])
    return x, y


COAST = [(124.2, 40.0), (122.0, 40.5), (121.2, 39.0), (121.8, 40.8), (119.5, 39.8), (117.7, 38.9), (118.9, 37.5), (120.7, 37.8),
         (122.5, 37.3), (120.3, 36.0), (119.2, 34.9), (120.8, 32.4), (121.9, 31.0), (121.6, 29.9), (120.7, 27.9),
         (119.6, 26.0), (118.0, 24.5), (116.5, 23.2), (113.6, 22.3), (110.5, 21.2), (109.7, 21.5), (108.0, 21.5)]
HUANGHE = [(103.8, 36.1), (106.3, 38.5), (107.0, 40.3), (110.0, 40.6), (111.2, 39.6), (110.5, 36.8), (110.3, 34.6),
           (112.4, 34.8), (114.3, 34.9), (115.4, 36.0), (116.6, 37.6), (117.6, 38.8)]
CHANGJIANG = [(102.5, 27.0), (104.6, 28.8), (106.5, 29.5), (108.4, 30.8), (111.3, 30.7), (112.2, 30.2), (114.3, 30.6),
              (116.0, 29.7), (117.6, 30.7), (118.8, 32.0), (120.2, 32.0), (121.5, 31.4)]
BIANJING = (114.35, 34.8)
ROUTES = [("河北", 115.2, 36.6), ("河東", 112.5, 37.9), ("陝西", 108.9, 34.3), ("京東", 118.4, 36.6), ("京西", 112.4, 33.6),
          ("淮南", 118.9, 32.9), ("兩浙", 120.2, 30.3), ("江南", 116.0, 28.8), ("荊湖", 112.6, 28.6), ("福建", 119.3, 26.1),
          ("成都", 104.1, 30.7), ("梓州", 105.6, 31.0), ("廣南", 113.3, 23.1), ("廣西", 108.3, 23.0), ("利州", 105.9, 32.4),
          ("夔州", 109.5, 30.6), ("開封府界", 114.9, 34.4)]


@functools.lru_cache(maxsize=None)
def map_base(dark=True):
    img = (bg_night(7) if dark else bg_paper(7)).copy()
    d = ODraw(img)
    land = (52, 58, 72, 255) if dark else (210, 196, 160, 255)
    line = (120, 140, 170, 255) if dark else (90, 80, 60, 255)
    pts = [proj(*p) for p in COAST]
    poly = [proj(99.5, 42.5)] + [proj(124.2, 42.5)] + pts + [proj(99.5, 21.5)]
    d.polygon(poly, fill=land)
    d.line(pts, fill=line, width=3, joint="curve")
    riv = (110, 150, 190, 255) if dark else (90, 120, 150, 255)
    d.line([proj(*p) for p in HUANGHE], fill=riv, width=5, joint="curve")
    d.line([proj(*p) for p in CHANGJIANG], fill=riv, width=5, joint="curve")
    f = font("serif_reg", 30)
    draw_text(img, proj(108.5, 39.9), "黃河", f, riv)
    draw_text(img, proj(109.0, 29.6), "長江", f, riv)
    draw_text(img, (W - 120, MAP["y1"] - 30), "示意圖", font("sans_med", 28), (200, 200, 210, 200) if dark else (90, 80, 60, 220))
    return img


# ───────────────────────── scenes ─────────────────────────
@functools.lru_cache(maxsize=None)
def field_bg():
    base = paper(11).astype(np.float32)
    # spring field seen from above, rows in mild perspective
    lay = np.zeros((H, W, 4), np.float32)
    img = pil_rgba(W, H)
    d = ODraw(img)
    d.rectangle([0, 420, W, 1440], fill=(150, 166, 110, 150))
    rng = np.random.default_rng(4)
    for r in range(26):
        y = 440 + r * 38 + (r * r) * 0.4
        if y > 1430:
            break
        for c in range(0, W, 26):
            x = c + (r % 2) * 13 + rng.uniform(-3, 3)
            h = 10 + r * 0.6
            d.line([(x, y), (x - 3, y - h)], fill=(70, 120, 60, 230), width=3)
            d.line([(x, y), (x + 4, y - h * 0.8)], fill=(90, 140, 70, 230), width=2)
    # dirt path
    d.polygon([(560, 420), (640, 420), (820, 1440), (520, 1440)], fill=(196, 172, 128, 230))
    base = over(base, to_np(img))
    base = over(base, ridge_layer(470, 110, 21, (70, 86, 80), 0.35, 4, 160))
    # thatched house
    out = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    hd = ImageDraw.Draw(out)
    hd.rectangle([800, 560, 1020, 700], fill=(170, 140, 100, 255))
    hd.polygon([(780, 570), (910, 470), (1040, 570)], fill=(150, 120, 70, 255))
    hd.rectangle([880, 610, 940, 700], fill=(70, 50, 34, 255))
    return out


def s_hook_field(c):
    img = field_bg().copy()
    t = c.t
    # official left, farmer right
    paste(img, official(1.25, hold="book"), 300, 1260, anchor="b")
    shake = 0
    if c.s(0) + 2.0 < t < c.e(1) + 0.5:
        shake = int(round(10 * math.sin((t - c.s(0)) * 9))) if (t - c.s(0)) % 2.4 < 1.2 else 0
    paste(img, farmer(1.25, head_dx=shake), 760, 1250, anchor="b")
    # ledger in front
    lg = ledger(760, 330)
    paste(img, lg, W / 2, 1180)
    d = ODraw(img)
    f = font("serif_tc", 30)
    names = ["張大", "李二", "王三", "趙四", "劉五", "陳六", "孫七", "周八"]
    for i, nm in enumerate(names):
        x = 220 + i * 86 if i < 4 else 220 + 380 + (i - 4) * 86
        for j, ch in enumerate(nm):
            draw_text(img, (x, 1080 + j * 34), ch, f, INK + (255,), trad=True)
        tp = (t - (c.s(0) + 0.6 + i * 0.55))
        if i >= 4:
            tp = t - (c.s(1) + 0.15 + (i - 4) * 0.35)
        tick(d, x, 1190, 46, clamp(tp / 0.35), RED, 7)
    # headline
    a = ramp(t, c.s(1) + 0.9, 0.25)
    if a > 0:
        sc = 1.25 - 0.25 * ease_out(clamp((t - c.s(1) - 0.9) / 0.25))
        lay = pil_rgba(W, 260)
        big_text(lay, W / 2, 130, "不借也得借", font("brush", 170), (150, 24, 20, 255), stroke=4, stroke_fill=(250, 240, 220, 255))
        paste(img, lay, W / 2, 330, alpha=a, scale=sc)
    else:
        big_text(img, W / 2, 330, "青苗錢", font("brush", 150), INK + (255,))
    return img


def cycle_pos(cx, cy, R, ang):
    return cx + R * math.cos(ang), cy + R * math.sin(ang)


def s_hook_cycle(c):
    img = bg_paper(2).copy()
    d = ODraw(img)
    t = c.t
    cx, cy, R = W / 2, 860, 330
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(120, 100, 80, 160), width=6)
    nodes = [("春", "青黃不接", -math.pi / 2, GREEN), ("借", "官府貸錢", 0, BRONZE), ("秋", "麥熟糧收", math.pi / 2, (176, 140, 50)), ("還", "本息歸倉", math.pi, RED)]
    for i, (big, small, ang, col) in enumerate(nodes):
        a = ramp(t, 0.2 + i * 0.5, 0.5)
        x, y = cycle_pos(cx, cy, R, ang)
        d.ellipse([x - 92, y - 92, x + 92, y + 92], fill=(244, 234, 210, int(255 * a)), outline=col + (int(255 * a),), width=7)
        draw_text(img, (x, y - 8), big, font("brush", 100), col + (255,), alpha=a)
        draw_text(img, (x, y + 128), small, font("serif", 38), INK + (255,), alpha=a)
    # coin running around
    ang = -math.pi / 2 + (t * 0.9) % (2 * math.pi)
    x, y = cycle_pos(cx, cy, R, ang)
    paste(img, coin(44), x, y)
    # one-stroke-three-goals
    a = c.p(1, 0.5)
    for i, txt in enumerate(["惠民", "平價", "增收"]):
        stamp(img, txt, 250 + i * 290, 1430, 190, t, c.s(1) + 1.2 + i * 0.9, rot=[-6, 3, -2][i])
    draw_text(img, (W / 2, 860), "一舉三得" if a > 0 else "", font("brush", 96), (150, 24, 20, 255), alpha=c.p(1, 0.5, 4.0))
    return img


def edict(img, cx, cy, w, h, lines, alpha=1.0, f=None):
    lay = pil_rgba(w, h)
    d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, w, h], fill=(214, 172, 70, 255))
    d.rectangle([18, 18, w - 18, h - 18], fill=(244, 222, 160, 255), outline=(160, 110, 40, 255), width=4)
    f = f or font("serif_black_tc", 76)
    ncol = len(lines)
    for ci, col in enumerate(lines):
        x = w - 80 - ci * (f.size * 1.35)
        for j, ch in enumerate(col):
            draw_text(lay, (x, 90 + j * f.size * 1.12), ch, f, INK + (255,), trad=True)
    paste(img, lay, cx, cy, alpha)


def s_hook_ban(c):
    img = bg_paper(3).copy()
    t = c.t
    edict(img, W / 2, 860, 640, 860, ["青苗法條約", "不許抑配"], alpha=c.p(0, 0.5, -0.2) if c.t > 0 else 1)
    stamp(img, "勅", W / 2 - 160, 1180, 170, t, c.s(0) + 1.6)
    if t > c.s(3):
        a = c.p(3, 0.5)
        # crack across edict + money bags pushed in
        d = ODraw(img)
        pts = [(260, 520), (420, 700), (360, 860), (560, 1010), (500, 1200), (720, 1330)]
        k = int(len(pts) * clamp((t - c.s(3)) / 1.2)) + 1
        d.line(pts[:k], fill=(120, 20, 16, int(255 * a)), width=8)
        for i in range(3):
            pa = ramp(t, c.s(3) + 0.6 + i * 0.35, 0.4)
            paste(img, money_bag(160), 230 + i * 310, 1440 - 40 * pa, alpha=pa)
        big_text(img, W / 2, 380, "問題出在哪兒？", font("brush", 110), (150, 24, 20, 255), alpha=c.p(3, 0.5, 1.4))
    return img


def s_hook_rays(c):
    img = map_base(True).copy()
    d = ODraw(img)
    t = c.t
    bx, by = proj(*BIANJING)
    rng = np.random.default_rng(41)
    total = 41
    T = max(4.0, c.dur - 1.5)
    for i in range(total):
        nm, lon, lat = ROUTES[i % len(ROUTES)]
        jit = rng.normal(0, 0.5, 2)
        tx, ty = proj(lon + jit[0], lat + jit[1])
        t0 = 0.3 + i * (T * 0.55 / total)
        k = ease_out((t - t0) / 1.6)
        if k <= 0:
            continue
        x, y = bx + (tx - bx) * k, by + (ty - by) * k
        d.line([(bx, by), (x, y)], fill=(255, 200, 110, 90), width=3)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 220, 140, 255))
    for nm, lon, lat in ROUTES[:-1]:
        x, y = proj(lon, lat)
        draw_text(img, (x, y + 36), nm, font("serif_tc", 30), (230, 220, 200, 230), alpha=ramp(t, 1.0, 1))
    glow = 26 + 6 * math.sin(t * 4)
    d.ellipse([bx - glow, by - glow, bx + glow, by + glow], fill=(255, 190, 90, 120))
    d.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=(255, 240, 200, 255))
    draw_text(img, (bx - 20, by - 60), "汴京", font("serif_black_tc", 44), (255, 220, 160, 255))
    n = min(total, int(total * clamp((t - 0.3) / (T * 0.55 + 1.6))))
    lay = pil_rgba(W, 200)
    draw_text(lay, (W / 2, 70), f"提舉官　{num_cn(n)}員", font("serif_black_tc", 80), (255, 226, 170, 255))
    draw_text(lay, (W / 2, 160), "分赴諸路　督辦新法", font("serif", 44), (220, 214, 200, 255))
    paste(img, lay, W / 2, 1490)
    return img


def num_cn(n):
    units = "〇一二三四五六七八九"
    if n < 10:
        return units[n]
    if n < 20:
        return "十" + (units[n % 10] if n % 10 else "")
    return units[n // 10] + "十" + (units[n % 10] if n % 10 else "")


def s_hook_eunuch(c):
    img = bg_paper(4).copy()
    t = c.t
    # palace backdrop
    paste(img, building("hall", 1.6, label="垂拱殿"), W / 2, 760)
    # two eunuchs walk out then back
    for i in range(2):
        x = 260 + i * 160 + 520 * ease(clamp((t - 0.3) / 3.0)) - (0 if t < c.s(1) else 520 * ease(clamp((t - c.s(1)) / 1.5)))
        paste(img, official(0.9, robe=(120, 90, 60), hold="hu", facing=1 if t < c.s(1) else -1), x, 1300, anchor="b")
    if t > c.s(1):
        a = c.p(1, 0.5, 0.6)
        lay = pil_rgba(620, 520)
        dd = ImageDraw.Draw(lay)
        dd.rectangle([0, 0, 620, 520], fill=(246, 236, 210, 255), outline=(140, 110, 60, 255), width=6)
        f = font("serif_black_tc", 72)
        for ci, col in enumerate(["民皆情願", "無抑配者"]):
            x = 620 - 160 - ci * 160
            for j, ch in enumerate(col):
                draw_text(lay, (x + 30, 80 + j * 92), ch, f, INK + (255,), trad=True)
        paste(img, lay, W / 2, 1140, alpha=a)
        stamp(img, "密奏", W / 2 + 220, 1340, 120, t, c.s(1) + 1.4)
    draw_text(img, (W / 2, 330), "二中使　潛察府界", font("serif_black_tc", 66), INK + (255,), alpha=ramp(t, 0.1, 0.5))
    return img


def s_hook_xiangfu(c):
    img = bg_paper(5).copy()
    t = c.t
    paste(img, building("gate", 1.5, label="祥符縣"), W / 2, 700)
    if t > c.s(0) + 2.0:
        stamp(img, "劾奏", W / 2 + 230, 900, 200, t, c.s(0) + 3.2, rot=8)
    d = ODraw(img)
    if t > c.s(1):
        a = c.p(1, 0.4)
        # balance: 多散 → 功 ; 不散 → 罪
        label_box(img, 300, 1150, "多散　→　功", font("serif_black_tc", 64), fg=(30, 90, 40), alpha=a)
        label_box(img, 780, 1150, "不散　→　罪", font("serif_black_tc", 64), fg=RED, alpha=c.p(1, 0.4, 1.3))
        label_box(img, W / 2, 1350, "上報：皆曰情願", font("serif_black_tc", 64), fg=INK, alpha=c.p(1, 0.4, 2.6))
    return img


CHAIN = ["皇帝", "宰相", "提舉官", "知州", "知縣", "胥吏", "農戶"]


def chain_nodes(img, t, x, y0, step, labels, appear0=0.2, dt=0.25, f=None, dist=None):
    d = ODraw(img)
    f = f or font("serif_black_tc", 54)
    pos = []
    for i, nm in enumerate(labels):
        y = y0 + i * step
        a = ramp(t, appear0 + i * dt, 0.4)
        if i > 0:
            d.line([(x, y - step + 46), (x, y - 46)], fill=(90, 80, 70, int(200 * a)), width=5)
        col = INK if not dist else dist(i)
        label_box(img, x, y, nm, f, fg=col, alpha=a)
        pos.append((x, y))
    return pos


def s_hook_thesis(c):
    img = bg_paper(6).copy()
    t = c.t
    if t < c.s(2):
        pos = chain_nodes(img, t, W / 2, 420, 150, CHAIN)
        # signal travels down, reddening
        k = clamp((t - c.s(1)) / max(1, (c.e(1) - c.s(1))))
        if k > 0:
            yy = 420 + k * 150 * 6
            col = (int(60 + 140 * k), int(140 - 110 * k), int(70 - 40 * k))
            paste(img, coin(40, tone=0), W / 2 + 190, yy)
            d = ODraw(img)
            d.ellipse([W / 2 + 150, yy - 40, W / 2 + 230, yy + 40], outline=col + (255,), width=6)
        draw_text(img, (W / 2, 300), "好設計　變了形", font("brush", 96), (150, 24, 20, 255), alpha=c.p(1, 0.5))
    else:
        # verdict glimpse: Wang silhouette + seals
        paste(img, official(1.5, robe=(88, 60, 96), hold="hu"), W / 2, 1300, anchor="b", alpha=ramp(t, c.s(2), 0.5))
        stamp(img, "罷相", 260, 820, 170, t, c.s(2) + 1.5)
        stamp(img, "再罷", 820, 860, 170, t, c.s(2) + 2.1, rot=7)
        stamp(img, "盡廢", 250, 1120, 170, t, c.s(2) + 3.2, rot=4)
        stamp(img, "復行", 830, 1160, 170, t, c.s(2) + 4.0, rot=-8)
        if t > c.s(3):
            big_text(img, W / 2, 420, "他輸給了誰？", font("brush", 130), (150, 24, 20, 255), alpha=c.p(3, 0.5))
        else:
            draw_text(img, (W / 2, 420), "王安石", font("brush", 120), INK + (255,), alpha=ramp(t, c.s(2), 0.5))
    return img


def s_title(c, title="王安石變法\n為什麼失敗"):
    img = bg_mountains(31).copy()
    lines = title.split("\n")
    for i, l in enumerate(lines):
        draw_text(img, (W / 2, 760 + i * 210), l, font("brush", 180), INK + (255,), alpha=ramp(c.t, 0.0, 0.4))
    paste(img, seal("權力組織", 150), W / 2 + 320, 1240)
    return img


@functools.lru_cache(maxsize=None)
def city_night():
    img = bg_night(9).copy()
    d = ODraw(img)
    d.ellipse([760, 360, 880, 480], fill=(240, 226, 190, 255))
    rng = np.random.default_rng(3)
    for row in range(4):
        y = 820 + row * 150
        for i in range(-1, 8):
            x = i * 170 + (row % 2) * 85 + rng.integers(-20, 20)
            sc = 0.45 + row * 0.12
            b = building("hall", sc, lit=bool(rng.random() < 0.6))
            arr = np.asarray(b).astype(np.float32)
            arr[..., :3] *= 0.55 + row * 0.12
            paste(img, Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), x, y + 60, anchor="b")
    return img


def balance(img, t, cx, cy, tilt, left, right, alpha=1.0):
    d = ODraw(img)
    a = int(255 * alpha)
    d.line([(cx, cy), (cx, cy + 420)], fill=(60, 50, 40, a), width=12)
    d.polygon([(cx - 90, cy + 440), (cx + 90, cy + 440), (cx + 40, cy + 410), (cx - 40, cy + 410)], fill=(60, 50, 40, a))
    L = 330
    ang = tilt
    lx, ly = cx - L * math.cos(ang), cy + L * math.sin(ang)
    rx, ry = cx + L * math.cos(ang), cy - L * math.sin(ang)
    d.line([(lx, ly), (rx, ry)], fill=(60, 50, 40, a), width=10)
    for (px, py, items, col) in [(lx, ly, left, RED), (rx, ry, right, (40, 100, 60))]:
        d.line([(px, py), (px - 110, py + 170)], fill=(80, 70, 60, a), width=3)
        d.line([(px, py), (px + 110, py + 170)], fill=(80, 70, 60, a), width=3)
        d.chord([px - 140, py + 120, px + 140, py + 230], 0, 180, fill=(120, 100, 70, a))
        for i, it in enumerate(items):
            label_box(img, px + (i - (len(items) - 1) / 2) * 96, py + 120 - 36, it, font("serif_black_tc", 40), fg=col, alpha=alpha, pad=12)


def s_bianjing_night(c):
    t = c.t
    if t < c.s(1):
        img = city_night().copy()
        draw_text(img, (W / 2, 420), "一〇六七", font("serif_black", 150), (240, 214, 160, 255), alpha=ramp(t, 0.2, 0.6))
        draw_text(img, (W / 2, 570), "宋神宗即位", font("serif", 60), (230, 220, 200, 255), alpha=ramp(t, 0.8, 0.6))
        return img
    img = bg_paper(8).copy()
    k = ease(clamp((t - c.s(1) - 0.5) / 2.5))
    balance(img, t, W / 2, 620, 0.32 * k, ["兵", "官", "邊費"], ["歲入"])
    draw_text(img, (W / 2, 1330), "入不敷出", font("brush", 140), (150, 24, 20, 255), alpha=ramp(t, c.e(1) - 2.0, 0.5))
    draw_text(img, (220, 420), "遼 ↓", font("serif_black_tc", 60), INK + (255,), alpha=ramp(t, c.s(1) + 3.5, 0.5))
    draw_text(img, (860, 420), "← 西夏", font("serif_black_tc", 60), INK + (255,), alpha=ramp(t, c.s(1) + 4.2, 0.5))
    if t > c.s(2):
        draw_text(img, (W / 2, 1520), "把賬做平　把國做強", font("serif_black_tc", 64), (40, 40, 60, 255), alpha=c.p(2, 0.5))
    return img


def s_memorial_card(c):
    img = bg_paper(9).copy()
    t = c.t
    paste(img, official(1.3, robe=(196, 150, 50), hold="hu", facing=1), 280, 1300, anchor="b")
    paste(img, official(1.3, robe=(88, 60, 96), hold="hu", facing=-1), 800, 1300, anchor="b")
    draw_text(img, (280, 1350), "宋神宗", font("serif", 46), INK + (255,))
    draw_text(img, (800, 1350), "王安石", font("serif", 46), INK + (255,))
    draw_text(img, (W / 2, 380), "熙寧二年二月", font("serif_black_tc", 76), INK + (255,), alpha=ramp(t, 0.2, 0.5))
    stamp(img, "參知政事", W / 2, 600, 200, t, 1.4)
    if t > c.s(1):
        label_box(img, W / 2, 820, "卿所施設以何先？", font("serif_black_tc", 52), alpha=c.p(1, 0.4))
    return img


LAWS = ["農田水利", "青苗", "均輸", "保甲", "免役", "市易", "保馬", "方田"]


def s_tiaolisi(c):
    t = c.t
    img = bg_night(12).copy()
    paste(img, building("hall", 1.7, lit=True, label="條例司"), W / 2, 760)
    draw_text(img, (W / 2, 330), "制置三司條例司", font("serif_black_tc", 72), (240, 214, 160, 255), alpha=ramp(t, 0.2, 0.5))
    if t > c.s(1):
        label_box(img, 260, 1060, "舊：三司", font("serif_black_tc", 50), fg=(90, 90, 100), alpha=c.p(1, 0.4))
        label_box(img, 800, 1060, "新：條例司", font("serif_black_tc", 50), fg=RED, alpha=c.p(1, 0.4, 0.8))
    if t > c.s(2):
        for i, law in enumerate(LAWS):
            a = ramp(t, c.s(2) + 0.25 + i * 0.45, 0.35)
            tablet(img, 110 + i * 123, 1420, law, font("serif_tc", 44), alpha=a, w=86)
    return img


def s_chain(c):
    img = bg_paper(13).copy()
    t = c.t
    labels = ["詔書", "提舉官", "知州", "知縣", "胥吏", "農戶的錢袋"]
    pos = chain_nodes(img, t, W / 2 - 120, 400, 190, labels, 0.3, 0.6)
    d = ODraw(img)
    draw_text(img, (W / 2 + 280, 360), "上千個縣", font("brush", 80), (150, 24, 20, 255), alpha=c.p(0, 0.5, 2.5))
    if t > c.s(2):
        for i, (x, y) in enumerate(pos[1:5]):
            a = ramp(t, c.s(2) + 0.3 + i * 0.4, 0.3)
            abacus(img, x + 330, y + 190, 160, a)
        draw_text(img, (W / 2, 1600), "每一層　都有自己的算盤", font("brush", 80), (150, 24, 20, 255), alpha=c.p(2, 0.5, 1.8))
    return img


def abacus(img, cx, cy, w, alpha=1.0):
    if alpha <= 0.01:
        return
    lay = pil_rgba(w, int(w * 0.6))
    d = ImageDraw.Draw(lay)
    d.rectangle([0, 0, w - 1, lay.height - 1], outline=(90, 60, 30, 255), width=6)
    d.line([(0, lay.height * 0.32), (w, lay.height * 0.32)], fill=(90, 60, 30, 255), width=4)
    for i in range(7):
        x = 14 + i * (w - 28) / 6
        d.line([(x, 4), (x, lay.height - 4)], fill=(120, 90, 50, 255), width=2)
        for j in range(2):
            y = 10 + j * 14 if i % 2 else 22 + j * 12
            d.ellipse([x - 9, y, x + 9, y + 12], fill=(110, 60, 30, 255))
        for j in range(4):
            y = lay.height * 0.42 + j * 14 + (i % 3) * 4
            d.ellipse([x - 9, y, x + 9, y + 12], fill=(110, 60, 30, 255))
    paste(img, lay, cx, cy, alpha)


def s_yinxian(c):
    t = c.t
    img = bg_mountains(15).copy()
    if t < c.s(3):
        paste(img, building("granary", 1.1, label="鄞縣倉"), W / 2, 980)
        paste(img, official(1.0, robe=(60, 80, 110), hold="book"), 260, 1360, anchor="b")
        for i in range(4):
            paste(img, farmer(0.75), 560 + i * 120, 1380, anchor="b")
        draw_text(img, (W / 2, 380), "鄞縣　小試", font("brush", 110), INK + (255,), alpha=ramp(t, 0.2, 0.5))
        if t > c.s(2):
            # eye watching
            d = ODraw(img)
            a = int(255 * c.p(2, 0.4))
            d.ellipse([170, 600, 350, 700], outline=(150, 24, 20, a), width=8)
            d.ellipse([235, 625, 285, 675], fill=(150, 24, 20, a))
            draw_text(img, (260, 760), "親自盯著", font("serif_black_tc", 46), (150, 24, 20, 255), alpha=c.p(2, 0.4))
        return img
    img = map_base(False).copy()
    d = ODraw(img)
    rng = np.random.default_rng(9)
    k = clamp((t - c.s(3)) / 2.5)
    n = int(1200 * ease(k))
    pts = rng.uniform(0, 1, (1200, 2))
    for i in range(n):
        lon = 103 + pts[i, 0] * 18
        lat = 22.5 + pts[i, 1] * 17
        x, y = proj(lon, lat)
        if y > proj(lon, 22)[1]:
            continue
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(150, 24, 20, 200))
    x, y = proj(121.5, 29.9)
    d.ellipse([x - 14, y - 14, x + 14, y + 14], outline=(30, 30, 30, 255), width=4)
    draw_text(img, (x - 60, y + 40), "鄞縣", font("serif_tc", 34), INK + (255,))
    draw_text(img, (W / 2, 1580), "放大到整個天下？", font("brush", 100), (150, 24, 20, 255), alpha=c.p(3, 0.5, 1.0))
    return img


def s_law_card(c):
    img = bg_paper(16).copy()
    t = c.t
    lay = pil_rgba(860, 1000)
    dd = ImageDraw.Draw(lay)
    dd.rectangle([0, 0, 860, 1000], fill=(224, 196, 140, 255), outline=(110, 80, 40, 255), width=8)
    f = font("serif_black_tc", 62)
    cols = ["青苗法者", "以常平糴本", "作青苗錢", "散與人戶", "令出息二分", "春散秋斂"]
    hl = {"常平糴本", "二分", "春散秋斂", "青苗錢"}
    for ci, col in enumerate(cols):
        x = 860 - 90 - ci * 130
        for j, ch in enumerate(col):
            draw_text(lay, (x, 110 + j * 76), ch, f, INK + (255,), trad=True)
    paste(img, lay, W / 2, 920, alpha=ramp(t, 0, 0.4))
    draw_text(img, (W / 2, 330), "青苗法", font("brush", 130), (150, 24, 20, 255))
    return img


def s_granary(c):
    img = bg_mountains(17).copy()
    t = c.t
    paste(img, building("granary", 1.4, label="常平倉"), W / 2, 820)
    d = ODraw(img)
    if t < c.s(1):
        k = (t * 0.6) % 2
        label_box(img, 280, 1150, "豐年　糴入", font("serif_black_tc", 54), fg=(40, 100, 60), alpha=ramp(t, 0.8, 0.4))
        label_box(img, 800, 1150, "荒年　糶出", font("serif_black_tc", 54), fg=RED, alpha=ramp(t, 2.2, 0.4))
        draw_text(img, (W / 2, 1320), "平抑糧價", font("brush", 100), INK + (255,), alpha=ramp(t, 3.4, 0.4))
    else:
        k = clamp((t - c.s(1)) / 3.0)
        for i in range(7):
            h = int(4 + 14 * ease(clamp(k * 1.3 - i * 0.06)))
            paste(img, coin_stack(h, 44), 150 + i * 130, 1420, anchor="b")
        draw_text(img, (W / 2, 1500), "一千四百萬貫石", font("serif_black_tc", 84), (150, 24, 20, 255), alpha=c.p(1, 0.5, 1.6))
        draw_text(img, (W / 2, 1600), "躺著不動的本錢", font("serif", 52), INK + (255,), alpha=c.p(1, 0.5, 4.5))
    return img


def s_usury(c):
    img = bg_paper(18).copy()
    t = c.t
    d = ODraw(img)
    draw_text(img, (W / 2, 330), "青黃不接", font("brush", 130), (60, 100, 50, 255), alpha=ramp(t, 0.2, 0.5))
    paste(img, farmer(1.0, poor=True), W / 2, 960, anchor="b")
    # empty bowl
    d.chord([W / 2 + 120, 860, W / 2 + 260, 960], 0, 180, fill=(140, 110, 80, 255))
    if t > c.s(1):
        a = c.p(1, 0.4)
        # rows: borrow 10 -> repay
        label_box(img, 260, 1080, "富戶放債", font("serif_black_tc", 50), fg=RED, alpha=a)
        label_box(img, 260, 1330, "官府青苗", font("serif_black_tc", 50), fg=(40, 100, 60), alpha=c.p(1, 0.4, 1.0))
        k1 = clamp((t - c.s(1) - 0.6) / 1.5)
        for i in range(int(20 * k1)):
            paste(img, coin(16, legend=False), 440 + (i % 20) * 30, 1080)
        k2 = clamp((t - c.s(1) - 1.8) / 1.5)
        for i in range(int(12 * k2)):
            paste(img, coin(16, legend=False), 440 + i * 30, 1330)
        draw_text(img, (900, 1160), "倍息", font("brush", 72), (150, 24, 20, 255), alpha=ramp(t, c.s(1) + 2.0, 0.4))
        draw_text(img, (900, 1410), "二分", font("brush", 72), (40, 100, 60, 255), alpha=ramp(t, c.s(1) + 3.2, 0.4))
        draw_text(img, (W / 2, 1520), "借十　還多少", font("serif", 44), INK + (220,), alpha=ramp(t, c.s(1) + 1.0, 0.4))
    return img


FLOW = [("常平倉", -math.pi / 2), ("銅錢", -math.pi / 2 + 2 * math.pi / 5), ("農戶", -math.pi / 2 + 4 * math.pi / 5),
        ("秋收", -math.pi / 2 + 6 * math.pi / 5), ("回倉", -math.pi / 2 + 8 * math.pi / 5)]


def flow_loop(img, t, red=False, k_red=0.0, cx=W / 2, cy=900, R=360):
    d = ODraw(img)
    col = (60, 120, 70) if not red else (int(60 + 120 * k_red), int(120 - 90 * k_red), int(70 - 40 * k_red))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=col + (170,), width=8)
    nodes = []
    for i, (nm, ang) in enumerate(FLOW):
        x, y = cycle_pos(cx, cy, R, ang)
        nodes.append((x, y))
    # moving coins
    speed = 0.55 if not red else 0.55 * (1 - 0.6 * k_red)
    for j in range(5):
        a = -math.pi / 2 + (t * speed + j * 2 * math.pi / 5) % (2 * math.pi)
        x, y = cycle_pos(cx, cy, R, a)
        paste(img, coin(26, legend=False), x, y)
    for i, (nm, ang) in enumerate(FLOW):
        x, y = nodes[i]
        label_box(img, x, y, nm, font("serif_black_tc", 52), fg=INK)
    return nodes


def s_flow_clean(c):
    img = bg_paper(19).copy()
    t = c.t
    flow_loop(img, t)
    draw_text(img, (W / 2, 330), "紙面上的設計", font("brush", 110), (60, 100, 50, 255))
    if t > c.s(2):
        stamp(img, "善法", W / 2, 900, 230, t, c.s(2) + 0.4)
    elif t > c.s(1):
        draw_text(img, (W / 2, 900), "錢活起來", font("serif_black_tc", 64), (60, 100, 50, 255), alpha=c.p(1, 0.5, 1.0))
    return img


def s_rate_ledger(c):
    img = bg_paper(20).copy()
    t = c.t
    lg = ledger(940, 900, cols=8)
    paste(img, lg, W / 2, 960)
    f = font("serif_black_tc", 52)
    rows = [("法令", "出息二分"), ("一年", "春夏兩散"), ("韓琦", "借一千　納一千三")]
    for i, (a_, b_) in enumerate(rows):
        a = ramp(t, c.s(min(i, 1)) + (0.4 if i < 2 else 2.8) + (i * 1.2 if i < 2 else 0), 0.4)
        draw_text(img, (260, 640 + i * 150), a_, f, (150, 24, 20, 255), alpha=a)
        draw_text(img, (650, 640 + i * 150), b_, f, INK + (255,), alpha=a)
    if t > c.s(1) + 3.0:
        k = clamp((t - c.s(1) - 3.0) / 1.2)
        paste(img, coin_stack(10, 36), 380, 1330, anchor="b", alpha=k)
        paste(img, coin_stack(13, 36), 700, 1330, anchor="b", alpha=k)
        draw_text(img, (380, 1370), "一千", font("serif", 40), INK + (255,), alpha=k)
        draw_text(img, (700, 1370), "一千三百", font("serif", 40), (150, 24, 20, 255), alpha=k)
    if t > c.s(2):
        draw_text(img, (W / 2, 1530), "年利幾何？學界說法不一", font("serif_black_tc", 58), (150, 24, 20, 255), alpha=c.p(2, 0.5))
    draw_text(img, (W / 2, 330), "利息到底多高", font("brush", 110), INK + (255,))
    return img


def s_suzhe(c):
    img = bg_paper(21).copy()
    t = c.t
    paste(img, official(1.2, robe=(60, 90, 80), hold="hu", facing=1), 280, 1250, anchor="b")
    paste(img, official(1.2, robe=(88, 60, 96), hold="hu", facing=-1), 800, 1250, anchor="b")
    draw_text(img, (280, 1300), "蘇轍", font("serif", 46), INK + (255,))
    draw_text(img, (800, 1300), "王安石", font("serif", 46), INK + (255,))
    if t > c.s(2):
        # calendar pages
        k = clamp((t - c.s(2)) / 2.5)
        for i in range(int(1 + 4 * k)):
            label_box(img, W / 2 - 40 + i * 20, 560 + i * 16, "逾月不言青苗", font("serif_black_tc", 56), alpha=1)
    if t > c.s(3):
        stamp(img, "決意行之", W / 2, 860, 220, t, c.s(3) + 2.2)
        draw_text(img, (W / 2, 1450), "陝西　私行青苗", font("serif_black_tc", 54), INK + (255,), alpha=c.p(3, 0.4, 0.6))
    draw_text(img, (W / 2, 330), "出納之際　吏緣為奸", font("brush", 88), (150, 24, 20, 255), alpha=ramp(t, 0.2, 0.5))
    return img


def s_flow_red(c):
    img = bg_paper(22).copy()
    t = c.t
    k = clamp((t - 1.5) / 3)
    nodes = flow_loop(img, t, True, k)
    x, y = nodes[1]
    # yamen inserted between coins & farmers
    yx, yy = (nodes[1][0] + nodes[2][0]) / 2 + 80, (nodes[1][1] + nodes[2][1]) / 2 + 40
    paste(img, building("gate", 0.55, label="縣衙"), yx, yy, alpha=ramp(t, 0.8, 0.5))
    stamp(img, "指標", yx + 30, yy - 170, 150, t, 2.2, rot=10)
    for i in range(3):
        pa = ramp(t, 3.0 + i * 0.5, 0.4)
        bx = nodes[2][0] - 60 + i * 70 + 30 * pa
        paste(img, money_bag(110), bx, nodes[2][1] + 160, alpha=pa)
    draw_text(img, (W / 2, 330), "鏡頭停在縣衙", font("brush", 100), (150, 24, 20, 255))
    if t > c.s(2):
        big_text(img, W / 2, 1560, "多散為功", font("brush", 150), (150, 24, 20, 255), alpha=c.p(2, 0.4), stroke=3, stroke_fill=(250, 240, 220, 255))
    return img


def s_hu_ledger(c):
    img = bg_paper(23).copy()
    t = c.t
    lg = ledger(960, 980, cols=10)
    paste(img, lg, W / 2, 930)
    f = font("serif_black_tc", 50)
    draw_text(img, (W / 2, 330), "河北　按戶分配", font("brush", 100), INK + (255,))
    if t > c.s(1):
        tiers = [("一等", 15, "十五貫"), ("二等", None, ""), ("三等", None, ""), ("四等", None, ""), ("五等", 1, "一貫")]
        for i, (nm, n, lab) in enumerate(tiers):
            a = ramp(t, c.s(1) + 2.5 + i * 0.5, 0.4)
            x = 900 - i * 180
            draw_text(img, (x, 560), nm, f, (150, 24, 20, 255), alpha=a)
            if n:
                paste(img, coin_stack(n, 40), x, 1260, anchor="b", alpha=a)
                draw_text(img, (x, 1310), lab, font("serif_black_tc", 46), INK + (255,), alpha=a)
            else:
                draw_text(img, (x, 1100), "⋮", font("serif", 70), (120, 100, 80, 255), alpha=a)
        draw_text(img, (W / 2 - 60, 1380), "等而下之", font("serif", 40), (110, 90, 70, 255), alpha=ramp(t, c.s(1) + 4.5, 0.4))
        draw_text(img, (W / 2, 470), "貧富相兼　十人為保", font("serif_black_tc", 46), INK + (255,), alpha=ramp(t, c.s(1) + 1.0, 0.4))
    else:
        label_box(img, 300, 900, "富戶：不願借", font("serif_black_tc", 52), alpha=ramp(t, 0.6, 0.4))
        label_box(img, 780, 900, "貧戶：還不起", font("serif_black_tc", 52), fg=RED, alpha=ramp(t, 2.4, 0.4))
    if t > c.s(2):
        label_box(img, W / 2, 1530, "回奏：民皆歡呼感德", font("serif_black_tc", 60), fg=INK, alpha=c.p(2, 0.4), bgc=(236, 206, 140))
    return img


def chapter_mech(img, t, n, title):
    draw_text(img, (W / 2, 330), f"機制{n}", font("serif_black_tc", 56), (150, 24, 20, 255), alpha=ramp(t, 0, 0.3))
    draw_text(img, (W / 2, 440), title, font("brush", 120), INK + (255,), alpha=ramp(t, 0.15, 0.4))


def s_mech1(c):
    img = bg_paper(24).copy()
    t = c.t
    chapter_mech(img, t, "一", "指標化")
    d = ODraw(img)
    i = c.cur()
    if i <= 2:
        # court sees only two numbers through narrow window
        d.rectangle([140, 620, 940, 1320], fill=(60, 60, 64, 255))
        d.rectangle([300, 820, 780, 1120], fill=(244, 234, 210, 255), outline=GOLD + (255,), width=6)
        if t > c.s(1):
            k = clamp((t - c.s(1)) / max(1, c.dur))
            a = c.p(1, 0.4, 1.5)
            draw_text(img, (540, 900), f"散錢　{int(1000 + 90000 * k):,}貫".replace(",", ""), font("serif_black_tc", 52), INK + (255,), alpha=a)
            draw_text(img, (540, 1030), f"收息　{int(200 + 18000 * k):,}貫".replace(",", ""), font("serif_black_tc", 52), (150, 24, 20, 255), alpha=c.p(1, 0.4, 3.0))
        draw_text(img, (540, 690), "朝廷看得見的", font("serif", 44), (230, 220, 200, 255), alpha=c.p(1, 0.4, 0.5))
        draw_text(img, (540, 1240), "看不見的：田間", font("serif", 44), (160, 160, 170, 255), alpha=c.p(1, 0.4, 5.0))
        if t > c.s(2):
            draw_text(img, (W / 2, 1460), "前程　繫於兩個數", font("serif_black_tc", 62), (150, 24, 20, 255), alpha=c.p(2, 0.4))
    elif i <= 4:
        # 排门抄扎: row of doors being ticked
        for j in range(6):
            x = 140 + j * 160
            d.rectangle([x - 60, 760, x + 60, 1040], fill=(120, 84, 56, 255), outline=INK + (255,), width=4)
            d.line([(x, 760), (x, 1040)], fill=INK + (255,), width=3)
            tick(d, x, 880, 90, clamp((t - c.s(3) - j * 0.5) / 0.35), RED, 12)
        draw_text(img, (W / 2, 1200), "排門抄紥", font("brush", 130), (150, 24, 20, 255), alpha=c.p(3, 0.4, 0.3))
    else:
        paste(img, official(1.1, robe=(120, 90, 60), hold="book", facing=1), 270, 1230, anchor="b")
        draw_text(img, (270, 1280), "府界提舉官", font("serif", 40), INK + (255,))
        draw_text(img, (W / 2, 640), "屢督散錢", font("serif_black_tc", 58), RED + (255,), alpha=c.p(5, 0.4, 0.5))
        label_box(img, 760, 900, "召至中書戒諭", font("serif_black_tc", 50), alpha=c.p(5, 0.4, 4.5))
        if t > c.s(6):
            d.line([(560, 860), (960, 940)], fill=RED + (255,), width=12)
            d.line([(560, 940), (960, 860)], fill=RED + (255,), width=12)
            label_box(img, 760, 1100, "王安石：止之", font("serif_black_tc", 56), fg=RED, alpha=c.p(6, 0.3, 0.3))
        if t > c.s(8):
            label_box(img, W / 2, 1330, "推得急：不罰", font("serif_black_tc", 58), fg=(40, 100, 60), alpha=c.p(8, 0.4, 1.5))
            label_box(img, W / 2, 1470, "推得慢：有罪", font("serif_black_tc", 58), fg=RED, alpha=c.p(8, 0.4, 3.0))
    return img


def s_mech2(c):
    img = bg_paper(25).copy()
    t = c.t
    chapter_mech(img, t, "二", "信息不對稱")
    d = ODraw(img)
    if t < c.s(2):
        paste(img, official(1.3, robe=(70, 70, 90), hold="hu"), 260, 1300, anchor="b")
        draw_text(img, (260, 1350), "韓琦　三朝宰相", font("serif", 40), INK + (255,))
        for i in range(2):
            paste(img, official(0.75, robe=(120, 90, 60), hold="hu", facing=-1), 760 + i * 120, 1300, anchor="b")
        draw_text(img, (820, 1350), "二宦者", font("serif", 40), INK + (255,))
        paste(img, official(0.8, robe=(196, 150, 50), hold="hu", facing=1), W / 2, 1000, anchor="b", alpha=c.p(1, 0.4))
        if t > c.s(1):
            draw_text(img, (W / 2, 1560), "不信三朝宰相　而信二宦者乎？", font("serif_black_tc", 54), (150, 24, 20, 255), alpha=c.p(1, 0.4, 1.5))
    else:
        # pyramid levels with thinning upward arrows
        levels = ["皇帝", "宰相", "提舉官", "知縣", "胥吏"]
        for i, nm in enumerate(levels):
            y = 640 + i * 170
            w2 = 140 + i * 90
            label_box(img, W / 2, y, nm, font("serif_black_tc", 46), alpha=1)
            if i > 0:
                wd = max(2, int(30 - i * 6))
                for side in (-1, 1):
                    arrow(d, (W / 2 + side * w2, y - 20), (W / 2 + side * (w2 - 60), y - 140), (150, 24, 20, 230), width=max(3, 22 - (5 - i) * 4), head=26, prog=ramp(t, c.s(2) + 0.3 + (5 - i) * 0.4, 0.5))
        # farmers blocked at bottom
        for j in range(5):
            paste(img, farmer(0.55), 220 + j * 160, 1620, anchor="b")
        k = c.p(3, 0.4)
        d.rectangle([120, 1380, 960, 1420], fill=(70, 60, 50, int(255 * k)))
        draw_text(img, (W / 2, 1400), "聲音送不上去", font("serif_black_tc", 34), (240, 230, 210, 255), alpha=k)
        draw_text(img, (W / 2 + 280, 560), "「情願」", font("serif_black_tc", 52), (40, 100, 60, 255), alpha=c.p(2, 0.4, 2.5))
    return img


def s_mech3(c):
    img = bg_paper(26).copy()
    t = c.t
    chapter_mech(img, t, "三", "目標衝突")
    d = ODraw(img)
    goals = [("惠民", 220), ("平價", 540), ("收息", 860)]
    focus = c.p(1, 0.6, 2.5)
    for nm, x in goals:
        dim = 1 - 0.6 * focus if nm != "收息" else 1.0
        y = 900
        col = (40, 100, 60) if nm != "收息" else RED
        d.ellipse([x - 120, y - 120, x + 120, y + 120], outline=col + (int(255 * dim),), width=10)
        draw_text(img, (x, y), nm, font("brush", 90), col + (255,), alpha=dim)
        if nm == "收息":
            # ruler / tally marks = measurable
            for k in range(8):
                d.line([(x - 100 + k * 28, y + 150), (x - 100 + k * 28, y + 190 - (k % 2) * 16)], fill=RED + (int(255 * focus),), width=5)
            draw_text(img, (x, y + 240), "可考核", font("serif_black_tc", 46), RED + (255,), alpha=focus)
    if t > c.s(2):
        paste(img, building("granary", 0.6, label="常平倉"), 300, 1460, alpha=c.p(2, 0.4))
        k = c.p(2, 0.4, 2.0)
        d.line([(170, 1300), (430, 1500)], fill=RED + (int(255 * k),), width=12)
        draw_text(img, (300, 1560), "停糴", font("serif_black_tc", 50), RED + (255,), alpha=k)
        arrow(d, (480, 1420), (760, 1420), (150, 24, 20, 255), 12, 34, prog=c.p(2, 1.0, 3.0))
        paste(img, money_bag(150, "放貸"), 860, 1440, alpha=c.p(2, 0.4, 3.5))
    return img


def s_theory(c):
    img = bg_paper(27).copy()
    t = c.t
    d = ODraw(img)
    i = c.cur()
    if i == 0:
        draw_text(img, (W / 2, 360), "委託代理", font("brush", 120), INK + (255,))
        label_box(img, 280, 800, "委託人：朝廷", font("serif_black_tc", 52), alpha=ramp(t, 0.5, 0.4))
        label_box(img, 800, 800, "代理人：提舉官", font("serif_black_tc", 52), alpha=ramp(t, 1.5, 0.4))
        arrow(d, (460, 800), (590, 800), INK + (255,), 8, 28, prog=ramp(t, 1.0, 0.6))
        label_box(img, 280, 1060, "想要：惠民", font("serif_black_tc", 52), fg=(40, 100, 60), alpha=ramp(t, 3.0, 0.4))
        label_box(img, 800, 1060, "考核：散錢", font("serif_black_tc", 52), fg=RED, alpha=ramp(t, 4.0, 0.4))
        draw_text(img, (W / 2, 1060), "≠", font("serif_black", 110), RED + (255,), alpha=ramp(t, 5.0, 0.3))
    elif i == 1:
        draw_text(img, (W / 2, 360), "多任務激勵", font("brush", 110), INK + (255,))
        draw_text(img, (W / 2, 480), "Holmström & Milgrom, 1991", font("serif_reg", 40), (90, 80, 70, 255))
        paste(img, official(1.0, robe=(120, 90, 60), hold="book"), W / 2, 1100, anchor="b")
        tasks = [("惠民", 250, False), ("平價", W / 2, False), ("收息", 830, True)]
        k = c.p(1, 1.0, 3.0)
        for nm, x, meas in tasks:
            y = 1300
            col = RED if meas else (90, 110, 90)
            alpha = 1.0 if meas else 1 - 0.65 * k
            label_box(img, x, y, nm, font("serif_black_tc", 50), fg=col, alpha=alpha)
            if meas:
                arrow(d, (W / 2 + 40, 1060), (x - 40, y - 60), RED + (255,), 10 + int(14 * k), 34, prog=clamp(k * 1.5))
                draw_text(img, (x, y + 90), "被計量", font("serif", 40), RED + (255,), alpha=k)
    else:
        draw_text(img, (W / 2, 360), "古德哈特定律", font("brush", 110), INK + (255,))
        draw_text(img, (W / 2, 480), "Goodhart's law", font("serif_reg", 44), (90, 80, 70, 255))
        if i >= 4 or t > c.s(4) - 0.1:
            # body and its shadow separating
            k = c.p(4, 2.5, 1.0)
            paste(img, farmer(1.2), W / 2 - 40 * k, 1300, anchor="b")
            sh = farmer(1.2)
            arr = np.asarray(sh).copy()
            arr[..., :3] = (40, 40, 50)
            arr[..., 3] = (arr[..., 3] * 0.42).astype(np.uint8)
            paste(img, Image.fromarray(arr), W / 2 + 40 + 280 * k, 1300, anchor="b")
            draw_text(img, (W / 2 - 40 * k, 1360), "本體：百姓受惠", font("serif_black_tc", 44), (40, 100, 60, 255), alpha=c.p(4, 0.4, 0.5))
            draw_text(img, (W / 2 + 40 + 280 * k, 1440), "影子：放貸額", font("serif_black_tc", 44), RED + (255,), alpha=c.p(4, 0.4, 1.5))
    return img


def houses(img, t, n, wealth, hi=None, red=None, gone=None, x0=120, y0=860, cols=5, sp=190):
    d = ODraw(img)
    for i in range(n):
        x = x0 + (i % cols) * sp
        y = y0 + (i // cols) * 300
        w = wealth[i]
        col = (170 - 40 * (1 - w), 140 - 30 * (1 - w), 100)
        if red is not None and red[i] > 0:
            col = tuple(int(col[j] * (1 - red[i]) + RED[j] * red[i]) for j in range(3))
        a = 1.0 if not (gone and gone[i] > 0) else 1 - gone[i]
        d.rectangle([x - 70, y - 40, x + 70, y + 80], fill=tuple(int(v) for v in col) + (int(255 * a),), outline=INK + (int(255 * a),), width=3)
        d.polygon([(x - 90, y - 30), (x, y - 100), (x + 90, y - 30)], fill=(110, 90, 60, int(255 * a)))
        if hi and hi[i] > 0:
            d.rectangle([x - 84, y - 112, x + 84, y + 94], outline=(30, 90, 50, int(255 * hi[i])), width=6)
        draw_text(img, (x, y + 120), ["上", "上", "中", "中", "下", "下", "下", "貧", "貧", "貧"][i], font("serif", 34), INK + (255,), alpha=a)


def s_adverse(c):
    img = bg_paper(28).copy()
    t = c.t
    i = c.cur()
    d = ODraw(img)
    wealth = [1, 0.9, 0.7, 0.6, 0.4, 0.35, 0.3, 0.1, 0.05, 0.0]
    draw_text(img, (W / 2, 360), "誰會來借？", font("brush", 120), INK + (255,))
    if i <= 3:
        hi = [0] * 7 + [c.p(1, 0.5, 2.0)] * 3
        houses(img, t, 10, wealth, hi=hi)
        if i >= 2:
            draw_text(img, (W / 2, 1520), "不許抑配　亦是空文", font("serif_black_tc", 64), RED + (255,), alpha=c.p(2, 0.4))
    else:
        # chain: one leaves, debt spreads
        k = clamp((t - c.s(3) - 1.5) / 1.0)
        gone = [0] * 9 + [k]
        spread = [0] * 10
        for j in range(7, 9):
            spread[j] = clamp((t - c.s(3) - 2.6 - (8 - j) * 0.6) / 0.6)
        for j in range(4, 7):
            spread[j] = clamp((t - c.s(4) - (6 - j) * 0.5) / 0.6)
        houses(img, t, 10, wealth, red=spread, gone=gone)
        if t > c.s(5):
            draw_text(img, (W / 2, 1530), "一張連坐的網", font("brush", 96), (150, 24, 20, 255), alpha=c.p(5, 0.4))
        else:
            draw_text(img, (W / 2, 1530), "逃亡　→　均之鄰保", font("serif_black_tc", 64), RED + (255,), alpha=c.p(3, 0.4, 3.0))
    return img


TAIJIAN = ["劉述", "劉琦", "錢顗", "孫昌齡", "王子韶", "程顥", "張戩", "陳襄", "陳薦", "謝景溫", "楊繪", "劉摯", "范純仁", "李常", "孫覺", "胡宗愈"]


def s_chess(c):
    img = bg_paper(29).copy()
    t = c.t
    d = ODraw(img)
    # board
    bx0, by0, bw, bh = 110, 560, 860, 960
    d.rectangle([bx0, by0, bx0 + bw, by0 + bh], fill=(214, 182, 128, 255), outline=(110, 80, 40, 255), width=8)
    for i in range(1, 8):
        d.line([(bx0, by0 + i * bh / 8), (bx0 + bw, by0 + i * bh / 8)], fill=(120, 90, 50, 255), width=2)
    for i in range(1, 4):
        d.line([(bx0 + i * bw / 4, by0), (bx0 + i * bw / 4, by0 + bh)], fill=(120, 90, 50, 255), width=2)
    draw_text(img, (W / 2, 360), "臺諫：皇帝的耳目", font("brush", 96), INK + (255,))
    rm0 = c.s(2) - 1.0
    for k, nm in enumerate(TAIJIAN):
        r, cc = divmod(k, 4)
        x = bx0 + bw / 8 + cc * bw / 4
        y = by0 + bh / 8 + r * bh / 4
        appear = ramp(t, c.s(1) + k * 0.18, 0.3)
        out = ease(clamp((t - rm0 - k * 0.32) / 0.6))
        x += out * (300 if cc >= 2 else -300)
        a = appear * (1 - out)
        if a <= 0.01:
            continue
        d.ellipse([x - 82, y - 82, x + 82, y + 82], fill=(236, 214, 170, int(255 * a)), outline=(150, 24, 20, int(255 * a)), width=6)
        f = font("serif_black_tc", 44 if len(nm) == 2 else 36)
        draw_text(img, (x, y), nm, f, INK + (255,), alpha=a)
    if t > c.s(3):
        label_box(img, W / 2, 1590, "范鎮三疏言青苗　奪職致仕", font("serif_black_tc", 48), fg=RED, alpha=c.p(3, 0.4))
    return img


def s_portrait(c):
    img = bg_mountains(30).copy()
    t = c.t
    paste(img, official(1.7, robe=(88, 60, 96), hold="hu"), W / 2, 1450, anchor="b")
    draw_text(img, (W / 2, 360), "王安石", font("brush", 130), INK + (255,))
    if t > c.s(2):
        label_box(img, W / 2, 520, "元代史臣評語　帶立場", font("serif_black_tc", 44), fg=RED, alpha=c.p(2, 0.4))
    return img


def s_letter(c):
    img = bg_paper(32).copy()
    t = c.t
    i = c.cur()
    if i <= 1:
        lay = pil_rgba(900, 1040)
        dd = ImageDraw.Draw(lay)
        dd.rectangle([0, 0, 900, 1040], fill=(240, 226, 192, 255), outline=(150, 110, 60, 255), width=5)
        for k in range(9):
            dd.line([(900 - 100 * (k + 1), 20), (900 - 100 * (k + 1), 1020)], fill=(200, 120, 100, 200), width=2)
        f = font("serif_tc", 52)
        cols = ["答司馬諫議書", "某啟昨日蒙教", "蓋儒者所爭", "尤在名實", "至於怨誹之多", "則固前知其如此也", "人習於苟且", "非一日"]
        for ci, col in enumerate(cols):
            x = 900 - 50 - ci * 100
            hl = ci in (4, 5)
            for j, ch in enumerate(col[:16]):
                draw_text(lay, (x, 70 + j * 60), ch, f, ((150, 24, 20) if hl else INK) + (255,), trad=True)
        paste(img, lay, W / 2, 960)
        return img
    # noise filter: real complaints + attacks into a funnel labeled 流俗
    d = ODraw(img)
    draw_text(img, (W / 2, 360), "全當噪音", font("brush", 120), INK + (255,))
    d.polygon([(260, 900), (820, 900), (600, 1240), (480, 1240)], fill=(80, 70, 64, 255))
    draw_text(img, (540, 1010), "流俗", font("brush", 110), (240, 230, 210, 255))
    items = [("攤派", True), ("黨爭", False), ("逃亡", True), ("攻訐", False), ("連坐", True), ("私怨", False)]
    for k, (nm, real) in enumerate(items):
        t0 = c.s(2) + 0.5 + k * 0.55
        p = clamp((t - t0) / 2.2)
        if p <= 0:
            continue
        sx = 140 + (k % 3) * 400
        sy = 560 + (k // 3) * 120
        x = sx + (540 - sx) * ease(p)
        y = sy + (1300 - sy) * ease(p) + (300 * clamp(p - 0.7) / 0.3)
        a = 1 - clamp((p - 0.8) / 0.2)
        label_box(img, x, y, nm, font("serif_black_tc", 46), fg=(RED if real else (90, 90, 100)), alpha=a)
    draw_text(img, (W / 2, 1520), "真實的報警　和攻擊一起被濾掉", font("serif_black_tc", 52), RED + (255,), alpha=c.p(3, 0.4, 1.5))
    return img


def s_shangyang(c):
    img = bg_mountains(33).copy()
    t = c.t
    paste(img, official(1.2, robe=(40, 40, 46), hold="hu", facing=1), 270, 1280, anchor="b", alpha=ramp(t, 0.2, 0.5))
    paste(img, official(1.2, robe=(88, 60, 96), hold="hu", facing=-1), 810, 1280, anchor="b", alpha=ramp(t, 0.2, 0.5))
    draw_text(img, (270, 1330), "商鞅　秦", font("serif", 44), INK + (255,))
    draw_text(img, (810, 1330), "王安石　宋", font("serif", 44), INK + (255,))
    draw_text(img, (W / 2, 360), "兩次變法", font("brush", 130), INK + (255,))
    if t > c.s(2):
        label_box(img, W / 2, 700, "不顧人言", font("serif_black_tc", 60), fg=RED, alpha=c.p(2, 0.4))
    if t > c.s(3):
        draw_text(img, (270, 900), "成", font("brush", 140), (40, 100, 60, 255), alpha=c.p(3, 0.4, 2.5))
        draw_text(img, (810, 900), "敗", font("brush", 140), RED + (255,), alpha=c.p(3, 0.4, 3.2))
        label_box(img, W / 2, 1530, "詳見《商鞅》一期", font("serif_black_tc", 46), alpha=c.p(3, 0.4, 5.0))
    return img


def weather(img, t, cx, cy, kind, a):
    d = ODraw(img)
    if kind == "snow":
        for i in range(18):
            x = cx - 120 + (i * 53) % 240
            y = cy - 120 + ((i * 37 + t * 60) % 240)
            d.text((x, y), "＊", font=font("serif", 30), fill=(230, 236, 244, int(255 * a)))
    else:
        for i in range(24):
            x = cx - 120 + (i * 41) % 240
            y = cy - 120 + ((i * 29 + t * 300) % 240)
            d.line([(x, y), (x - 6, y + 26)], fill=(120, 150, 190, int(255 * a)), width=3)


def s_dialogue(c):
    img = bg_paper(34).copy()
    t = c.t
    paste(img, official(1.25, robe=(196, 150, 50), hold="hu", facing=1), 250, 1400, anchor="b")
    paste(img, official(1.25, robe=(88, 60, 96), hold="hu", facing=-1), 830, 1400, anchor="b")
    draw_text(img, (250, 1450), "神宗", font("serif", 44), INK + (255,))
    draw_text(img, (830, 1450), "王安石", font("serif", 44), INK + (255,))
    i = c.cur()
    f = font("serif_black_tc", 50)
    if i == 0:
        label_box(img, 380, 560, "聞民間殊苦新法", f, alpha=c.p(0, 0.4, 0.5))
    elif i == 1:
        label_box(img, 700, 560, "祁寒暑雨　民猶怨咨", f, alpha=c.p(1, 0.4))
        label_box(img, 700, 700, "此無庸恤", f, fg=RED, alpha=c.p(1, 0.4, 2.5))
        weather(img, t, 300, 820, "snow", c.p(1, 0.4))
        weather(img, t, 780, 900, "rain", c.p(1, 0.4))
    elif i in (2, 3, 4):
        label_box(img, 400, 600, "豈若並祁寒暑雨", f, alpha=1)
        label_box(img, 400, 730, "之怨亦無邪？", f, fg=RED, alpha=1)
    elif i in (5, 6):
        label_box(img, W / 2, 600, "開封民避保甲　截指斷腕", f, alpha=c.p(5, 0.4))
        label_box(img, W / 2, 740, "安石：亦不足怪", f, fg=(90, 90, 100), alpha=c.p(5, 0.4, 4.0))
    else:
        draw_text(img, (W / 2, 640), "怨言裡　有沒有真的？", font("brush", 100), (150, 24, 20, 255), alpha=c.p(7, 0.4))
    return img


def refugee(img, x, y, sc, a, t, ph):
    sp = farmer(sc, head_dx=0, tone=(110, 96, 80), poor=True)
    paste(img, sp, x, y + 4 * math.sin(t * 3 + ph), alpha=a, anchor="b")
    d = ODraw(img)
    d.ellipse([x + 20 * sc, y - 330 * sc, x + 90 * sc, y - 260 * sc], fill=(150, 130, 100, int(255 * a)))


def s_liumin(c):
    img = bg_paper(35).copy()
    t = c.t
    d = ODraw(img)
    # scroll unrolling
    k = ease(clamp((t - c.s(1)) / 2.0)) if t > c.s(1) else 0
    if t < c.s(1):
        # drought: sun + cracked earth
        d.ellipse([W / 2 - 110, 500, W / 2 + 110, 720], fill=(214, 120, 60, 255))
        rng = np.random.default_rng(5)
        for i in range(40):
            x, y = rng.uniform(100, 980), rng.uniform(900, 1400)
            d.line([(x, y), (x + rng.uniform(-80, 80), y + rng.uniform(-40, 40))], fill=(110, 80, 50, 255), width=3)
        draw_text(img, (W / 2, 360), "一〇七四　大旱", font("brush", 110), INK + (255,))
        return img
    sw = int(980 * k)
    d.rectangle([W / 2 - sw / 2, 520, W / 2 + sw / 2, 1260], fill=(226, 210, 172, 255), outline=(120, 90, 50, 255), width=4)
    if k > 0.3:
        for j in range(6):
            x = W / 2 - sw / 2 + 120 + j * 150
            if x < W / 2 + sw / 2 - 60:
                refugee(img, x, 1220, 0.75, clamp((k - 0.3) * 2), t, j)
    draw_text(img, (W / 2, 420), "流民圖", font("brush", 120), INK + (255,))
    draw_text(img, (W / 2, 1360), "鄭俠　監安上門", font("serif", 44), INK + (255,), alpha=k)
    if t > c.s(3):
        draw_text(img, (W / 2, 1500), "繞開所有層級", font("serif_black_tc", 60), RED + (255,), alpha=c.p(3, 0.4, 2.5))
    if t > c.s(4):
        stamp(img, "罷相", W / 2 + 300, 1580, 180, t, c.s(4) + 0.6)
    return img


EVENTS = [("一〇七四", "第一次罷相"), ("一〇七五", "復相"), ("一〇七六", "子雱卒　再罷"), ("一〇八五", "神宗崩　司馬光回朝"),
          ("一〇八六", "元祐：青苗錢不再發放"), ("一〇八六", "王安石卒　司馬光卒")]


def s_timeline(c):
    img = bg_paper(36).copy()
    t = c.t
    d = ODraw(img)
    d.line([(250, 470), (250, 1600)], fill=(100, 80, 60, 255), width=6)
    trig = [0.3, 2.0, 3.6, c.s(1) + 0.2, c.s(1) + 3.2, c.s(2) + 0.2]
    for i, (yr, ev) in enumerate(EVENTS):
        a = ramp(t, trig[i], 0.4)
        y = 520 + i * 200
        d.ellipse([230, y - 20, 270, y + 20], fill=RED + (int(255 * a),))
        draw_text(img, (140, y), yr, font("serif_black", 36), INK + (255,), alpha=a)
        draw_text(img, (300, y), ev, font("serif_black_tc", 48), INK + (255,), alpha=a, anchor="lm")
    return img


def s_fanpu(c):
    img = bg_paper(37).copy()
    t = c.t
    d = ODraw(img)
    # pendulum
    i = c.cur()
    amp = 0.55
    ang = amp * math.sin(t * 1.1)
    px, py = W / 2, 520
    L = 620
    bx, by = px + L * math.sin(ang), py + L * math.cos(ang)
    d.line([(px, py), (bx, by)], fill=(80, 64, 50, 255), width=8)
    d.ellipse([bx - 70, by - 70, bx + 70, by + 70], fill=(150, 110, 60, 255), outline=INK + (255,), width=4)
    draw_text(img, (bx, by), "法", font("brush", 80), (250, 240, 220, 255))
    draw_text(img, (200, 1300), "舊", font("brush", 140), (60, 70, 90, 255))
    draw_text(img, (880, 1300), "新", font("brush", 140), RED + (255,))
    labs = {0: "元祐：舊黨也想復散青苗", 1: "財政窟窿不因換人消失", 2: "紹聖：蔡京請復熙豐條約", 3: "崇寧：配享孔廟", 4: "南宋：削其王封"}
    j = min(i, 4)
    if i >= 3 and t > c.s(4) - 0.1 and i >= 4:
        j = 4
    elif i == 3 and t > c.s(3) + 3.5:
        j = 4
    label_box(img, W / 2, 1530, labs[j], font("serif_black_tc", 50), alpha=1)
    draw_text(img, (W / 2, 360), "翻過去　又翻回來", font("brush", 110), INK + (255,))
    return img


def s_stele(c):
    img = bg_mountains(38).copy()
    t = c.t
    d = ODraw(img)
    i = c.cur()
    # stele
    d.rectangle([300, 520, 780, 1400], fill=(118, 116, 112, 255), outline=(60, 60, 60, 255), width=6)
    d.rounded_rectangle([280, 480, 800, 560], radius=30, fill=(100, 98, 96, 255))
    d.rectangle([240, 1400, 840, 1450], fill=(90, 88, 86, 255))
    cyc = (t * 0.35) % 2
    txt = "新法" if cyc < 1 else "舊法"
    ph = cyc % 1
    a = clamp(ph / 0.25) * (1 - clamp((ph - 0.75) / 0.25))
    for j, ch in enumerate(txt):
        draw_text(img, (540, 820 + j * 220), ch, font("serif_black_tc", 190), (50, 50, 52, 255), alpha=a)
    if ph > 0.75:
        k = (ph - 0.75) / 0.25
        d.rectangle([310, 600, 770, 600 + 760 * k], fill=(140, 138, 134, 120))
    if i >= 2:
        label_box(img, W / 2, 1490, "《神宗實錄》　北宋屢修", font("serif_black_tc", 50), alpha=c.p(2, 0.4))
    if i >= 3:
        label_box(img, W / 2, 1590, "《宋史》　元·脫脫等撰", font("serif_black_tc", 50), alpha=c.p(3, 0.4))
    draw_text(img, (W / 2, 360), "一面站隊的旗" if i < 2 else "歷史也被翻修", font("brush", 110), INK + (255,))
    return img


def s_verdict(c):
    img = bg_paper(39).copy()
    t = c.t
    i = c.cur()
    draw_text(img, (W / 2, 360), "為什麼失敗", font("brush", 130), INK + (255,))
    if i >= 1:
        label_box(img, W / 2, 680, "目標交給只會計數的系統", font("serif_black_tc", 56), fg=INK, alpha=c.p(1, 0.4, 2.0))
        label_box(img, W / 2, 860, "報警被當成噪音", font("serif_black_tc", 56), fg=RED, alpha=c.p(1, 0.4, 5.0))
    if i >= 2:
        lay = pil_rgba(940, 560)
        dd = ImageDraw.Draw(lay)
        dd.rectangle([0, 0, 940, 560], fill=(246, 238, 216, 240), outline=RED + (255,), width=5)
        f = font("serif_black", 46)
        ls = ["一項政策同時背著兩個目標時，", "執行的人會去做", "能被考核的那一個；", "把反對聲音全當噪音，", "你就看不到這種變形。"]
        for k, l in enumerate(ls):
            aa = ramp(t, c.s(2) + k * 0.5 if k < 3 else c.s(3) + (k - 3) * 0.5, 0.4)
            draw_text(lay, (470, 80 + k * 100), l, f, INK + (255,), alpha=aa)
        paste(img, lay, W / 2, 1300, alpha=c.p(2, 0.4))
    return img


def s_sanbuzu(c):
    img = bg_paper(40).copy()
    t = c.t
    i = c.cur()
    d = ODraw(img)
    phr = ["天變不足畏", "祖宗不足法", "人言不足恤"]
    qk = c.p(5, 1.6, 0.6) if len(c.L) > 5 else 0
    for k, p in enumerate(phr):
        x = 760 - k * 220
        a = ramp(t, 0.3 + k * 0.6, 0.4) * (1 - qk)
        for j, ch in enumerate(p):
            draw_text(img, (x, 600 + j * 150), ch, font("serif_black_tc", 120), INK + (255,), alpha=a, trad=True)
    if i >= 2:
        a = c.p(2, 0.5, 2.0) * (1 - qk)
        for j, ch in enumerate("甚者謂"):
            draw_text(img, (980, 600 + j * 150), ch, font("serif_black_tc", 120), RED + (255,), alpha=a, trad=True)
        d.rectangle([905, 510, 1055, 1000], outline=RED + (int(255 * a),), width=6)
    if qk > 0:
        sc = 0.6 + 0.4 * ease_out(qk)
        lay = pil_rgba(700, 900)
        draw_text(lay, (350, 450), "？", font("serif_black", 640), (150, 24, 20, 255))
        paste(img, lay, W / 2, 960, alpha=qk, scale=sc)
    return img


SCENE_FN = {
    "hook_field": s_hook_field, "hook_cycle": s_hook_cycle, "hook_ban": s_hook_ban, "hook_rays": s_hook_rays,
    "hook_eunuch": s_hook_eunuch, "hook_xiangfu": s_hook_xiangfu, "hook_thesis": s_hook_thesis,
    "bianjing_night": s_bianjing_night, "memorial_card": s_memorial_card, "tiaolisi": s_tiaolisi, "chain": s_chain,
    "yinxian": s_yinxian, "law_card": s_law_card, "granary": s_granary, "usury_compare": s_usury,
    "flow_clean": s_flow_clean, "rate_ledger": s_rate_ledger, "suzhe_warn": s_suzhe, "flow_red": s_flow_red,
    "hu_ledger": s_hu_ledger, "mech1": s_mech1, "mech2": s_mech2, "mech3": s_mech3, "theory": s_theory,
    "adverse": s_adverse, "chess": s_chess, "portrait_card": s_portrait, "letter": s_letter, "shangyang": s_shangyang,
    "dialogue": s_dialogue, "liumin": s_liumin, "timeline": s_timeline, "fanpu": s_fanpu, "stele": s_stele,
    "verdict": s_verdict, "sanbuzu": s_sanbuzu, "title": s_title,
}
