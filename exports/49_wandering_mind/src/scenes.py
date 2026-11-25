# -*- coding: utf-8 -*-
"""Per-scene drawing. Each draw_<kind>(frame, t, c) where c is a Ctx (timing helper)."""
import functools, math
import numpy as np, cv2
from gfx import *
from art import *


class Ctx:
    def __init__(self, lines, scene_t0, scene_t1, t):
        self.L = lines  # id -> (t0, t1)
        self.t0, self.t1, self.t = scene_t0, scene_t1, t

    def st(self, i):
        return self.L[i][0]

    def en(self, i):
        return self.L[i][1]

    def s(self, i):
        return self.t - self.L[i][0]

    def on(self, i):
        return self.t >= self.L[i][0]

    def f(self, i, d=0.6, delay=0.0):
        return fade(self.t, self.L[i][0] + delay, d)

    def at(self, i, frac):
        a, b = self.L[i]
        return a + (b - a) * frac

    def vis(self, a, b=None, d=0.5, delay=0.0, out=0.45):
        """fade in at start of line a (+delay); fade out ending at start of line b (or scene end)."""
        tin = self.L[a][0] + delay if isinstance(a, str) else a
        tout = (self.L[b][0] if isinstance(b, str) else b) if b is not None else self.t1 + 10
        return fade(self.t, tin, d) * (1 - fade(self.t, tout - out, out))


@functools.lru_cache(maxsize=512)
def T(s, size, x, y, col=WHITE, fnt="serif", weight=600, anchor="mm", shadow=True, track=0):
    sh = ((0, 0, 0), 6, 0.6) if shadow else None
    return text_layer(s, (fnt, size, weight) if fnt in ("serif", "sans") else (fnt, size), col, x, y, anchor=anchor,
                      shadow=sh, track=track)


def rule(frame, x0, x1, y, col=GOLD, a=0.6, w=2):
    c = cached_rule(x0, x1, y, col, w)
    comp(frame, c, a)


@functools.lru_cache(maxsize=64)
def cached_rule(x0, x1, y, col, w):
    c = Canvas(x0 - 4, y - 6, x1 - x0 + 8, 12, 2)
    c.line([(x0, y), (x1, y)], col, w)
    return c.layer()


# ============================================================================ A: open
def draw_open(frame, t, c):
    light, rock = cave_layers()
    comp_add(frame, light, 1.0)
    draw_mist(frame, t, 0.22, seed=2, speed=10, y0=500)
    fig, rim = seated_figure()
    # slow push-in
    s = 1.0 + 0.03 * clamp(t / max(1, c.t1))
    comp(frame, scaled(fig, s, CX, 1150))
    comp_add(frame, scaled(rim, s, CX, 1150), 0.9)
    comp(frame, rock, 1.0)
    draw_mist(frame, t, 0.10, seed=5, speed=16, y0=900)
    # hook text: visible from frame 0
    k = 1 - c.vis("a02", None, 0.01) * 0 - fade(t, c.st("a02") - 0.4, 0.5)
    comp_any(frame, T("你此刻", 64, CX, 330, WHITE), k)
    comp_any(frame, T("将近一半的时间", 92, CX, 445, WHITE, weight=800), k)
    comp_any(frame, T("心不在这里", 92, CX, 565, GOLD, weight=800), k)
    # a02: wandering point leaping among branches (monkey metaphor)
    k2 = c.vis("a02", "a03", 0.4)
    if k2 > 0:
        br = branches()
        comp(frame, br, k2 * 0.9)
        s2 = max(0.0, c.s("a02"))
        p = monkey_path(s2)
        comp_add(frame, glow_blob(int(p[0]), int(p[1]), 14, GOLD, 1.2), k2)
        comp_add(frame, glow_blob(int(p[0]), int(p[1]), 45, GOLD, 0.35), k2)
        comp_any(frame, T("「譬如獼猴遊林樹間……攀捉枝條，放一取一」", 34, CX, 330, PAPER, fnt="kai"), k2)
    # a03: translucent brain network over the scene
    k3 = c.f("a03", 1.2)
    if k3 > 0:
        B = brain_layer()
        comp(frame, B, k3 * 0.8)
        for i, n in enumerate(["mpfc", "pcc", "mtl", "ang", "dacc"]):
            x, y, _ = NODES[n]
            kk = fade(t, c.st("a03") + 0.5 + i * 0.35, 0.6)
            pul = 0.8 + 0.2 * math.sin(t * 3 + i)
            comp_add(frame, glow_blob(x, y, 16, GOLD, 1.0 * pul), kk)
            comp_add(frame, glow_blob(x, y, 48, GOLD, 0.3 * pul), kk)
        net = net_lines()
        comp(frame, net, fade(t, c.st("a03") + 1.6, 1.0) * 0.7)
        comp_any(frame, T("一张网络图", 70, CX, 360, GOLD, weight=800), fade(t, c.st("a03") + 1.2, 0.6))


@functools.lru_cache(maxsize=1)
def branches():
    c = Canvas(0, 380, W, 700, 2)
    rng = np.random.default_rng(3)
    for k in range(7):
        x0 = rng.uniform(80, 1000)
        y0 = rng.uniform(450, 1000)
        L = rng.uniform(180, 380)
        ang = rng.uniform(-0.5, 0.5) + (math.pi if x0 > CX else 0)
        pts = [(x0 + math.cos(ang) * u * L, y0 + math.sin(ang) * u * L + 18 * math.sin(u * 4)) for u in np.linspace(0, 1, 20)]
        c.line(pts, hexc("#5b5246"), 6 - k * 0.4, 0.75)
    return c.layer()


MONKEY_PTS = [(200, 620), (420, 520), (640, 700), (860, 560), (700, 900), (360, 860), (520, 610), (880, 820), (250, 760)]


def monkey_path(s):
    hop = 0.55
    i = int(s / hop)
    u = (s % hop) / hop
    a = MONKEY_PTS[i % len(MONKEY_PTS)]
    b = MONKEY_PTS[(i + 1) % len(MONKEY_PTS)]
    u2 = ease(u)
    x = a[0] + (b[0] - a[0]) * u2
    y = a[1] + (b[1] - a[1]) * u2 - 120 * math.sin(math.pi * u)
    return x, y


@functools.lru_cache(maxsize=1)
def net_lines():
    c = Canvas(0, 500, W, 600, 2)
    pairs = [("mpfc", "pcc"), ("pcc", "mtl"), ("mpfc", "mtl"), ("pcc", "ang"), ("mpfc", "dacc")]
    for a, b in pairs:
        xa, ya, _ = NODES[a]
        xb, yb, _ = NODES[b]
        mx, my = (xa + xb) / 2, (ya + yb) / 2 - 50
        pts = [((1 - u) ** 2 * xa + 2 * u * (1 - u) * mx + u * u * xb, (1 - u) ** 2 * ya + 2 * u * (1 - u) * my + u * u * yb)
               for u in np.linspace(0, 1, 40)]
        c.line(pts, GOLD, 2.5, 0.65)
    return c.layer()


# ============================================================================ B: survey
def draw_survey(frame, t, c):
    draw_mist(frame, t, 0.06, seed=3, speed=6, y0=300)
    # phone (b01..b03b)
    kp = c.vis("b01", "b04", 0.6)
    if kp > 0:
        sc = 1 - 0.25 * fade(t, c.st("b03b"), 0.8)
        ph = phone()
        dy = -60 * fade(t, c.st("b03b"), 0.8)
        comp(frame, scaled(ph, sc, CX, 820), kp, dy=dy)
        comp_any(frame, T("2010 · 哈佛大学", 46, CX, 380, GOLD), c.vis("b01", "b02") * kp)
        # ping ripple
        if c.on("b02"):
            for k in range(3):
                ph_t = (c.s("b02") * 0.9 + k / 3) % 1.0
                comp(frame, ring(CX, 560 + int(dy) + 40, int(40 + 160 * ph_t)), (1 - ph_t) * 0.5 * kp * c.vis("b02", "b03b"))
        comp_any(frame, T("两千多名成年人", 52, CX, 1250, WHITE), c.vis("b02", "b03b") * kp)
        # questions inside phone
        qs = ["你现在感觉怎么样？", "你在做什么？", "你在想的，是不是\n正在做的这件事？"]
        for i, q in enumerate(qs):
            tq = c.at("b03", [0.0, 0.32, 0.55][i])
            kq = fade(t, tq, 0.4) * kp * (1 - fade(t, c.st("b03b") - 0.3, 0.3))
            comp_any(frame, qcard(q, 700 + i * 150), kq)
        comp_any(frame, T("经验抽样\nExperience Sampling", 50, CX, 1250, GOLD), c.vis("b03b", "b04") * kp)
    # dots (b04..b07)
    kd = c.vis("b04", "b05", 0.6)
    if kd > 0:
        wander = fade(t, c.st("b04") + 0.6, 2.0)
        comp(frame, dots_layer(t, wander), kd)
        n = 46.9 * fade(t, c.st("b04") + 0.4, 1.8)
        comp_any(frame, T(f"{n:.1f}%", 140, CX, 455, GOLD, weight=800), kd * c.vis("b04", "b05"))
        comp_any(frame, T("的抽样时刻，心在走神", 44, CX, 560, WHITE), kd * c.vis("b04", "b05", delay=0.6))
    kb = c.vis("b05", "b07", 0.6)
    if kb > 0:
        happy_bars(frame, t, c, kb)
    kt = c.vis("b07", "b08", 0.6)
    if kt > 0:
        comp_any(frame, paper_card(("A Wandering Mind", "Is an Unhappy Mind"), "Science 330:932 (2010)",
                                   y=760, width=860, fnt=("serif", 66, 700), small=("走神的心，是不快乐的心",)), kt)
    # caveat: correlation / inference
    kc = c.vis("b08", None, 0.6)
    if kc > 0:
        comp_any(frame, T("走神", 80, CX - 230, 760, WHITE, weight=800), kc)
        comp_any(frame, T("不快乐", 80, CX + 230, 760, WHITE, weight=800), kc)
        comp(frame, double_arrow(), kc)
        comp_any(frame, T("相关 ≠ 因果", 56, CX, 600, CINNABAR, weight=800), kc * c.vis("b08", "b09"))
        k9 = c.f("b09", 0.6)
        comp(frame, fwd_arrow(), k9 * kc)
        comp_any(frame, T("时间滞后分析：走神更可能是「因」", 42, CX, 920, GOLD), k9 * kc)
        comp_any(frame, T("（作者推断，并非实验证明）", 36, CX, 990, GREY), k9 * kc)


@functools.lru_cache(maxsize=1)
def phone():
    c = Canvas(CX - 200, 420, 400, 800, 2)
    c.rrect(CX - 175, 440, CX + 175, 1200, 46, c=hexc("#0b0e11"), outline=hexc("#8f969a"), width=4)
    c.rrect(CX - 155, 500, CX + 155, 1140, 20, c=hexc("#141a1f"))
    c.rrect(CX - 40, 466, CX + 40, 478, 6, c=hexc("#2a3035"))
    return c.layer()


@functools.lru_cache(maxsize=8)
def ring(x, y, r):
    c = Canvas(x - r - 6, y - r - 6, 2 * r + 12, 2 * r + 12, 2)
    c.circle(x, y, r, outline=GOLD, width=3)
    return c.layer()


@functools.lru_cache(maxsize=8)
def qcard(q, y):
    lines = q.split("\n")
    h = 46 * len(lines) + 44
    c = Canvas(CX - 150, y - h // 2 - 4, 300, h + 8, 2)
    c.rrect(CX - 145, y - h // 2, CX + 145, y + h // 2, 14, c=PAPER, a=0.95)
    for i, l in enumerate(lines):
        c.text(CX, y - (len(lines) - 1) * 23 + i * 46, l, ("serif", 30, 700), INK)
    return c.layer()


DOT_RNG = np.random.default_rng(42)
DOT_N = 2250
_cols, _rows = 45, 50
DOT_XY = np.array([(110 + (i % _cols) * 19.5, 640 + (i // _cols) * 13.0) for i in range(DOT_N)], np.float32)
DOT_W = DOT_RNG.random(DOT_N) < 0.469
DOT_PH = DOT_RNG.random((DOT_N, 2)).astype(np.float32) * 6.28


def dots_layer(t, wander):
    x0, y0, w, h = 60, 580, 960, 780
    img = np.zeros((h, w), np.float32)
    col = np.zeros((h, w), np.float32)
    for i in range(DOT_N):
        x, y = DOT_XY[i]
        if DOT_W[i]:
            x += wander * 16 * math.sin(t * 1.3 + DOT_PH[i, 0])
            y += wander * 10 * math.sin(t * 1.1 + DOT_PH[i, 1])
        xi, yi = int(x - x0), int(y - y0)
        if DOT_W[i] and wander > 0.05:
            cv2.circle(col, (xi, yi), 4, 1.0, -1, cv2.LINE_AA)
        else:
            cv2.circle(img, (xi, yi), 4, 1.0, -1, cv2.LINE_AA)
    a = np.clip(img * 0.85 + col * (0.25 + 0.4 * (1 - wander)), 0, 1)
    rgb = img[..., None] * np.array(WHITE, np.float32) * 0.85 + col[..., None] * np.array(GOLD, np.float32) * (0.25 + 0.4 * (1 - wander)) * 1.0
    rgb = rgb + (col[..., None] * np.array(GOLD, np.float32)) * 0.35 * wander
    a = np.clip(a + col * 0.35 * wander, 0, 1)
    return Layer(x0, y0, rgb.astype(np.float32), a.astype(np.float32))


def happy_bars(frame, t, c, k):
    comp_any(frame, T("此刻有多快乐（示意）", 44, CX, 420, GOLD), k)
    items = [("专心做眼前的事", 0.78, WHITE, "b05"), ("走神 · 想愉快的事", 0.76, GOLD, "b06"),
             ("走神 · 想中性的事", 0.62, GOLD, "b05"), ("走神 · 想不愉快的事", 0.45, GOLD, "b05")]
    for i, (lab, v, col, lid) in enumerate(items):
        y = 560 + i * 170
        kk = fade(t, c.st(lid) + (0.3 * i if lid == "b05" else 0.2), 0.6)
        if i == 1:
            kk = fade(t, c.st("b06"), 0.6)
        comp_any(frame, T(lab, 38, 120, y, WHITE, anchor="lm"), k * kk)
        comp(frame, bar(120, y + 40, int(840 * v * ease_out(kk)), 34, col), k * kk)


@functools.lru_cache(maxsize=64)
def bar(x, y, w, h, col):
    if w < 2:
        return None
    c = Canvas(x - 2, y - 2, w + 4, h + 4, 2)
    c.rrect(x, y, x + w, y + h, 6, c=col, a=0.85)
    return c.layer()


@functools.lru_cache(maxsize=1)
def double_arrow():
    c = Canvas(CX - 140, 730, 280, 60, 2)
    c.line([(CX - 110, 760), (CX + 110, 760)], GREY, 4)
    c.poly([(CX + 125, 760), (CX + 100, 745), (CX + 100, 775)], GREY)
    c.poly([(CX - 125, 760), (CX - 100, 745), (CX - 100, 775)], GREY)
    return c.layer()


@functools.lru_cache(maxsize=1)
def fwd_arrow():
    c = Canvas(CX - 140, 800, 280, 60, 2)
    c.line([(CX - 110, 830), (CX + 100, 830)], GOLD, 6)
    c.poly([(CX + 130, 830), (CX + 95, 810), (CX + 95, 850)], GOLD)
    return c.layer()


# ============================================================================ C: stance
def draw_stance(frame, t, c):
    draw_mist(frame, t, 0.08, seed=4, speed=6, y0=400)
    k1 = c.vis("c01", "c03", 0.6)
    comp_any(frame, T("科学没有证明佛法", 76, CX, 640, WHITE, weight=800), k1)
    comp_any(frame, T("佛法也不需要科学背书", 56, CX, 760, GREY), k1 * c.f("c01", 0.6, 1.8))
    comp_any(frame, T("或许，可以相互印照", 70, CX, 940, GOLD, weight=800), k1 * c.f("c02", 0.8))
    k3 = c.vis("c03", None, 0.6)
    if k3 > 0:
        icons = [("网络", "走神的网络", CX - 330, "c03", 0.25), ("月", "「我」的模型", CX, "c03", 0.5),
                 ("箭", "两支箭", CX + 330, "c03", 0.75)]
        for kind, lab, x, lid, fr in icons:
            kk = fade(t, c.at(lid, fr) - 0.3, 0.6)
            comp(frame, emblem(kind, x, 720), k3 * kk)
            comp_any(frame, T(lab, 40, x, 900, WHITE), k3 * kk)
        tags = [("实证", TEAL, 0.15), ("类比", GOLD_D, 0.45), ("小样本", CINNABAR, 0.78)]
        for i, (tg, col, fr) in enumerate(tags):
            kk = fade(t, c.at("c04", fr), 0.5)
            comp(frame, pill(tg, CX - 300 + i * 300, 1100, col), k3 * kk)


@functools.lru_cache(maxsize=8)
def pill(s, x, y, col):
    f = font("serif", 44, 700)
    w = int(f.getlength(s)) + 60
    c = Canvas(x - w // 2 - 4, y - 40, w + 8, 80, 2)
    c.rrect(x - w // 2, y - 34, x + w // 2, y + 34, 12, c=col, a=0.25, outline=col, width=3)
    c.text(x, y, s, ("serif", 44, 700), WHITE)
    return c.layer()


@functools.lru_cache(maxsize=8)
def emblem(kind, x, y):
    c = Canvas(x - 130, y - 130, 260, 260, 3)
    c.circle(x, y, 120, outline=GOLD, a=0.5, width=2)
    if kind == "网络":
        pts = [(x - 60, y - 20), (x + 50, y - 50), (x + 10, y + 55), (x - 40, y + 50), (x + 70, y + 30)]
        for a in pts:
            for b in pts:
                if a < b:
                    c.line([a, b], GOLD, 2, 0.6)
        for p in pts:
            c.circle(*p, 11, GOLD)
    elif kind == "月":
        c.circle(x, y - 40, 34, PAPER, a=0.95)
        for i in range(5):
            yy = y + 30 + i * 12
            ww = 50 - i * 6
            c.line([(x - ww, yy), (x + ww, yy)], PAPER, 4, 0.7 - i * 0.1)
    else:
        c.line([(x - 80, y + 40), (x + 60, y - 40)], PAPER, 6)
        c.poly([(x + 80, y - 52), (x + 40, y - 46), (x + 62, y - 20)], PAPER)
        c.line([(x - 80, y + 80), (x + 30, y + 20)], PAPER, 4, 0.35)
    return c.layer()


# ============================================================================ D: lamp
def draw_lamp(frame, t, c, wind_from="d01", calm_at="d03"):
    draw_mist(frame, t, 0.05, seed=6, speed=5, y0=600)
    lb = lamp_body()
    comp(frame, lb)
    wind = 1.0 - 0.85 * fade(t, c.st(calm_at), 3.0) if calm_at in c.L else 0.1
    comp_any(frame, flame_layers(t, wick_y=900, wind=wind))
    # wind streaks
    if wind > 0.3:
        for i in range(4):
            ph = (t * 0.6 + i * 0.27) % 1.0
            comp(frame, streak(i), 0.25 * wind * math.sin(math.pi * ph), dx=-400 + 900 * ph)
    kc = c.vis("d02", "d03", 0.6)
    comp_any(frame, paper_card(("過去心不可得，", "現在心不可得，", "未來心不可得。"),
                               "《金剛般若波羅蜜經》鳩摩羅什譯", y=520, width=820, fnt=("kaim", 62), seal="經"), kc)
    kd = c.vis("d03", None, 0.6)
    comp_any(frame, T("心无所住", 84, CX, 470, GOLD, fnt="kaim", shadow=True), kd * c.vis("d03", "d04"))
    comp_any(frame, T("往过去、往未来奔跑的心", 54, CX, 440, WHITE), c.f("d04", 0.6))
    comp_any(frame, T("哪一处也抓不住", 66, CX, 540, GOLD, weight=800), c.f("d04", 0.6, 1.5))


@functools.lru_cache(maxsize=4)
def streak(i):
    y = 640 + i * 70
    c = Canvas(0, y - 6, 600, 12, 2)
    c.line([(40, y), (560, y)], MIST, 2, 0.8)
    return c.layer()


# ============================================================================ E: DMN
def draw_dmn(frame, t, c):
    draw_mist(frame, t, 0.04, seed=7, speed=5, y0=300)
    kB = c.vis("e02", "e11b", 0.8) + c.vis("e17", None, 0.8)
    kB = clamp(kB)
    comp_any(frame, T("默认模式网络", 96, CX, 560, GOLD, weight=800), c.vis("e01", "e02", 0.4))
    comp_any(frame, T("Default Mode Network", 46, CX, 680, GREY), c.vis("e01", "e02", 0.4))
    if kB > 0:
        comp(frame, brain_layer(), kB * 0.85)
        # DMN activity level: high at rest, lower for meditators (e09)
        rest = c.f("e03", 1.0)
        med = fade(t, c.st("e09") + 0.4, 2.5) * (1 - c.f("e17", 0.6))
        level = rest * (1 - 0.65 * med)
        for i, n in enumerate(["mpfc", "pcc", "mtl", "ang"]):
            x, y, _ = NODES[n]
            pul = 0.85 + 0.15 * math.sin(t * 2.2 + i)
            comp(frame, ink_blot(x, y, 52, GOLD, i), 0.55 * level * pul)
            comp_add(frame, glow_blob(x, y, 24, GOLD, 0.8 * level * pul))
        kl = c.vis("e04", "e05", 0.5)
        if kl > 0:
            comp_any(frame, node_label("mpfc", GOLD), kl)
            comp_any(frame, node_label("pcc", GOLD), kl * c.f("e04", 0.5, 2.0))
            comp_any(frame, T("大脑正中切面 · 示意", 30, CX, 1140, GREY), kl)
        # e05 thought words orbit
        kw = c.vis("e05", "e07", 0.5)
        if kw > 0:
            words = ["走神", "回忆往事", "想象将来", "琢磨自己"]
            for i, wd in enumerate(words):
                ang = t * 0.25 + i * math.pi / 2
                x = CX + 380 * math.cos(ang) * 0.95
                y = 830 + 300 * math.sin(ang) * 0.9
                comp_any(frame, T(wd, 44, int(x), int(y), WHITE), kw * fade(t, c.at("e05", 0.15 + 0.18 * i), 0.4))
        # e07-e08: study card
        kc = c.vis("e07", "e09", 0.5)
        if kc > 0:
            comp_any(frame, T("12 位资深冥想者　对照　12 位新手", 42, CX, 430, WHITE), kc)
            comp_any(frame, T("平均练习 10,565 小时", 38, CX, 495, GOLD), kc * c.f("e07", 0.5, 2.5))
            ms = ["专注呼吸", "慈心", "无拣择觉察"]
            for i, m in enumerate(ms):
                kk = fade(t, c.at("e08", 0.35 + 0.18 * i), 0.4)
                comp(frame, pill(m, CX - 300 + i * 300, 1200, INDIGO), kc * kk)
        km = c.vis("e09", "e10", 0.5)
        comp_any(frame, T("冥想者：主要节点活动相对更低", 44, CX, 440, WHITE), km)
        # e10: connectivity PCC - dlPFC / dACC
        kx = c.vis("e10", "e11b", 0.6)
        if kx > 0:
            comp(frame, conn_line(), kx)
            for n in ["dlpfc", "dacc"]:
                x, y, _ = NODES[n]
                comp_add(frame, glow_blob(x, y, 20, INDIGO, 1.2), kx)
            comp_any(frame, T("调控注意的前额叶（外侧）", 32, CX - 120, 545, INDIGO), kx)
            comp_any(frame, T("连接更强", 50, CX + 230, 470, INDIGO, weight=800), kx)
    # e11b-d: wander -> notice -> return -> focus cycle
    ky = c.vis("e11b", "e12", 0.6)
    if ky > 0:
        cycle(frame, t, c, ky)
    # e12-e16: caveats
    kq = c.vis("e12", "e16b", 0.6)
    if kq > 0:
        comp_any(frame, T("三点必须说清楚", 64, CX, 430, WHITE, weight=800), kq)
        items = [("e13", "1", "小样本：24 人", "Brewer et al., 2011"), ("e14", "2", "横断面：不能证明因果", "也可能是不同的人选择了冥想"),
                 ("e15", "3", "部分未复现", "2022 年 40 人对 123 人的研究")]
        for i, (lid, num, a, b) in enumerate(items):
            kk = c.f(lid, 0.5)
            y = 610 + i * 220
            comp(frame, numcircle(num, 150, y), kq * kk)
            comp_any(frame, T(a, 52, 230, y - 20, WHITE, anchor="lm", weight=700), kq * kk)
            comp_any(frame, T(b, 34, 230, y + 45, GREY, anchor="lm"), kq * kk)
        comp_any(frame, T("关联，不等于因果", 58, CX, 1290, GOLD, weight=800), kq * c.f("e16", 0.6))
    kf = c.vis("e16b", "e17", 0.6)
    if kf > 0:
        comp(frame, bold_wave(t), kf)
        comp_any(frame, T("核磁共振测的是", 50, CX, 520, WHITE), kf)
        comp_any(frame, T("血流和血氧的变化", 66, CX, 610, GOLD, weight=800), kf)
        comp_any(frame, T("不是念头本身", 66, CX, 1120, WHITE, weight=800), kf * c.f("e16b", 0.5, 2.4))
    if c.on("e17"):
        k17 = c.f("e17", 0.8)
        # many small regions lit -> no single switch
        rng = np.random.default_rng(8)
        for i in range(14):
            pts = brain_outline_pts(14, 0.7, 0.62)[i]
            x, y = pts
            pul = 0.5 + 0.5 * math.sin(t * 2 + i * 1.7)
            comp_add(frame, glow_blob(int(x), int(y), 18, GOLD, 0.7 * pul), k17)
        comp_any(frame, T("没有单一的「开关」", 60, CX, 440, WHITE, weight=800), k17)
        comp_any(frame, T("一组区域协同的结果", 46, CX, 1210, GOLD), k17 * c.f("e17", 0.6, 3.0))


@functools.lru_cache(maxsize=1)
def conn_line():
    c = Canvas(0, 500, W, 400, 2)
    for a, b in [("pcc", "dlpfc"), ("pcc", "dacc")]:
        xa, ya, _ = NODES[a]
        xb, yb, _ = NODES[b]
        mx, my = (xa + xb) / 2, min(ya, yb) - 80
        pts = [((1 - u) ** 2 * xa + 2 * u * (1 - u) * mx + u * u * xb, (1 - u) ** 2 * ya + 2 * u * (1 - u) * my + u * u * yb)
               for u in np.linspace(0, 1, 50)]
        c.line(pts, INDIGO, 7, 0.9)
    return c.layer()


@functools.lru_cache(maxsize=4)
def numcircle(n, x, y):
    c = Canvas(x - 44, y - 44, 88, 88, 3)
    c.circle(x, y, 40, outline=CINNABAR, width=3)
    c.text(x, y, n, ("serif", 46, 800), CINNABAR)
    return c.layer()


def cycle(frame, t, c, k):
    cx, cy, R = CX, 840, 270
    labs = [("走神", "默认模式网络活跃", GOLD), ("觉察", "「突显网络」亮起", TEAL), ("回转", "注意力拉回", INDIGO),
            ("专注", "安住呼吸", WHITE)]
    comp(frame, cycle_ring(cx, cy, R), k * 0.8)
    show = [c.at("e11c", 0.1), c.at("e11c", 0.38), c.at("e11c", 0.66), c.at("e11c", 0.8)]
    for i, (a, b, col) in enumerate(labs):
        ang = -math.pi / 2 + i * math.pi / 2
        x, y = cx + R * math.cos(ang), cy + R * math.sin(ang)
        kk = fade(t, show[i] - 0.2, 0.5) if c.on("e11c") else 0.0
        comp(frame, disc(int(x), int(y), col), k * max(kk, 0.25 if c.on("e11c") else 0))
        comp_any(frame, T(a, 50, int(x), int(y), INK if col == WHITE else WHITE, weight=800, shadow=False), k * max(kk, 0.3))
        lx, ly = int(x), int(y + (-105 if i == 0 else 105))
        comp_any(frame, T(b, 32, lx, ly, GREY), k * kk)
    # moving token
    if c.on("e11c"):
        ph = (c.s("e11c") * 0.22) % 1.0
        ang = -math.pi / 2 + ph * 2 * math.pi
        comp_add(frame, glow_blob(int(cx + R * math.cos(ang)), int(cy + R * math.sin(ang)), 16, GOLD, 1.2), k)
    comp_any(frame, T("14 位冥想者 · 一觉察走神就按键", 40, CX, 440, WHITE), k * (1 - c.f("e11c", 0.5)))
    comp_any(frame, T("不是不走神，而是更快地发现", 50, CX, 1260, GOLD, weight=800), k * c.f("e11d", 0.6))


@functools.lru_cache(maxsize=2)
def cycle_ring(cx, cy, R):
    c = Canvas(cx - R - 20, cy - R - 20, 2 * R + 40, 2 * R + 40, 2)
    c.circle(cx, cy, R, outline=GREY, width=3, a=0.6)
    for i in range(4):
        ang = -math.pi / 2 + i * math.pi / 2 + math.pi / 4
        x, y = cx + R * math.cos(ang), cy + R * math.sin(ang)
        d = ang + math.pi / 2
        c.poly([(x + 16 * math.cos(d), y + 16 * math.sin(d)), (x + 12 * math.cos(d + 2.3), y + 12 * math.sin(d + 2.3)),
                (x + 12 * math.cos(d - 2.3), y + 12 * math.sin(d - 2.3))], GREY, a=0.8)
    return c.layer()


@functools.lru_cache(maxsize=16)
def disc(x, y, col):
    c = Canvas(x - 80, y - 80, 160, 160, 2)
    c.circle(x, y, 74, c=col, a=0.9 if col == WHITE else 0.55, outline=col, width=3)
    return c.layer()


def bold_wave(t):
    x0, y0, w, h = 120, 700, 840, 300
    c = Canvas(x0, y0, w, h, 1)
    pts = []
    for i in range(200):
        u = i / 199
        tt = u * 24 - t * 2
        v = sum(math.exp(-((tt - k * 6) % 24 - 3) ** 2 / 4) for k in range(1)) * 0.8
        y = y0 + h * 0.75 - v * h * 0.55 - 6 * math.sin(u * 40 + t)
        pts.append((x0 + u * w, y))
    c.line(pts, GOLD, 4)
    c.line([(x0, y0 + h * 0.78), (x0 + w, y0 + h * 0.78)], GREY, 1.5, 0.5)
    return c.layer()


# ============================================================================ F: no-self
def draw_noself(frame, t, c):
    draw_mist(frame, t, 0.05, seed=8, speed=5, y0=300)
    comp_any(frame, T("无我", 200, CX, 820, GOLD, fnt="brush", shadow=True), c.vis("f01", "f02", 0.6))
    comp_any(frame, paper_card(("色無常，無常即苦，", "苦即非我，非我者亦非我所。", "如是觀者，名真實正觀。"),
                               "《雜阿含經》卷一 第9經 · 求那跋陀羅譯", y=780, width=940, fnt=("kaim", 54), seal="經"),
             c.vis("f02", "f05", 0.7))
    comp_any(frame, T("变化的，不能让人安住\n不能主宰的，不是「我」，也不是「我的」", 40, CX, 1180, WHITE),
             c.vis("f04", "f05", 0.6))
    # five aggregates
    k5 = c.vis("f05", "f06", 0.6)
    if k5 > 0:
        names = ["色", "受", "想", "行", "识"]
        glos = ["身体", "感受", "认知", "意志", "意识"]
        for i, (n, g) in enumerate(zip(names, glos)):
            ang = -math.pi / 2 + i * 2 * math.pi / 5
            spread = 1 + 0.25 * fade(t, c.at("f05", 0.6), 1.5)
            x = CX + 270 * spread * math.cos(ang)
            y = 870 + 270 * spread * math.sin(ang)
            kk = fade(t, c.at("f05", 0.18 + 0.07 * i), 0.4)
            comp(frame, disc(int(x), int(y), GOLD), k5 * kk * 0.8)
            comp_any(frame, T(n, 66, int(x), int(y), WHITE, fnt="kaim", shadow=False), k5 * kk)
            comp_any(frame, T(g, 30, int(x), int(y) + 105, GREY), k5 * kk)
        q = fade(t, c.at("f05", 0.7), 0.8)
        comp_any(frame, T("？", 90, CX, 870, GREY), k5 * q)
        comp_any(frame, T("五蕴", 64, CX, 400, GOLD, fnt="kaim"), k5)
        kb = c.f("f05b", 0.6)
        comp_any(frame, T("不是「你不存在」", 50, CX, 1240, WHITE), k5 * kb)
    # Metzinger book
    kbk = c.vis("f06", "f09", 0.6)
    if kbk > 0:
        comp(frame, book_layer("Being\nNo One", "Thomas Metzinger · 2003", CX, 760), kbk)
        comp_any(frame, T("直译《谁也不是》", 46, CX, 1100, GOLD), kbk)
        comp_any(frame, T("自我模型理论", 66, CX, 430, WHITE, weight=800), kbk * c.f("f07", 0.6))
        comp_any(frame, T("「我」＝ 大脑构建的模型", 50, CX, 1210, WHITE), kbk * c.f("f08", 0.6))
    # glass window
    kg = c.vis("f09", "f11", 0.6)
    if kg > 0:
        comp(frame, window_scene(), kg)
        sheen = 1 - fade(t, c.at("f09", 0.55), 2.0)
        comp(frame, glass_sheen(), kg * sheen)
        comp_any(frame, T("透明的模型", 70, CX, 430, GOLD, weight=800), kg)
        comp_any(frame, T("看不见玻璃，就以为看到的是世界本身", 40, CX, 1230, WHITE), kg * c.f("f10", 0.5))
    # rubber hand
    kr = c.vis("f11", "f16b", 0.6)
    if kr > 0:
        comp_any(frame, T("橡胶手错觉", 70, CX, 430, GOLD, weight=800), kr)
        comp(frame, rubber_scene(), kr * c.f("f12", 0.6))
        if c.on("f13"):
            ph = math.sin(c.s("f13") * 2 * math.pi * 0.7)
            for hx in (CX - 230, CX + 230):
                comp(frame, brush_icon(), kr, dx=hx - CX, dy=int(70 * ph))
        comp_any(frame, T("这只手……是我的？", 56, CX - 230, 1200, WHITE), kr * c.f("f14", 0.6))
        comp_any(frame, T("「我的身体」：大脑实时拼出来的", 46, CX, 1260, GOLD), kr * c.f("f16", 0.6))
        comp_any(frame, T("Botvinick & Cohen, Nature, 1998", 30, CX, 520, GREY), kr * c.f("f12", 0.6))
    # full body VR
    kv = c.vis("f16b", "f17", 0.6)
    if kv > 0:
        comp_any(frame, T("全身错觉 · 2007", 64, CX, 430, GOLD, weight=800), kv)
        comp(frame, person(CX - 170, 1260, 0.78, PAPER, 0.9), kv)
        comp(frame, person(CX + 150, 960, 0.5, GOLD, 0.45), kv * c.f("f16c", 0.6))
        drift = fade(t, c.at("f16c", 0.6), 2.0)
        comp(frame, dashed_up(), kv * drift)
        comp_any(frame, T("「我」在哪里？", 50, CX, 590, WHITE), kv * drift)
        comp_any(frame, T("Lenggenhager, Tadi, Metzinger & Blanke, Science, 2007", 26, CX, 520, GREY), kv)
    # two columns: not equal
    kq = c.vis("f17", "f21", 0.6)
    if kq > 0:
        comp(frame, column_box(CX - 230, 820, "自我模型理论", ("哲学理论", "部分前提有实验支持", "并非定论"), INDIGO), kq * c.f("f18", 0.6))
        comp(frame, column_box(CX + 230, 820, "佛法的无我", ("修行与解脱的语境", "放下执取", "离苦"), GOLD_D), kq * c.f("f19", 0.6))
        comp_any(frame, T("≈", 110, CX, 820, WHITE, weight=800), kq * c.f("f20", 0.6))
        comp_any(frame, T("印照、类比，不能画等号", 52, CX, 1240, GOLD, weight=800), kq * c.f("f20", 0.6))
    kw = c.f("f21", 1.0)
    if kw > 0:
        water_moon(frame, t, kw)
        comp_any(frame, T("水中月", 80, CX, 430, GOLD, fnt="kaim"), kw)


@functools.lru_cache(maxsize=4)
def book_layer(title, sub, x, y):
    c = Canvas(x - 230, y - 300, 460, 600, 3)
    c.rrect(x - 200, y - 280, x + 200, y + 280, 8, c=hexc("#e4dccb"))
    c.rrect(x - 200, y - 280, x - 172, y + 280, 4, c=hexc("#b9ab90"))
    words = title.split("\n")
    fs = 58 if max(len(w) for w in words) <= 9 else 44
    for i, wd in enumerate(words):
        c.text(x + 14, y - 110 - (len(words) - 2) * 37 + i * 74, wd, ("serif", fs, 800), INK)
    c.line([(x - 120, y + 110), (x + 150, y + 110)], CINNABAR, 3)
    c.text(x + 14, y + 170, sub, ("serif", 26, 500), INK_S)
    return c.layer()


@functools.lru_cache(maxsize=1)
def window_scene():
    c = Canvas(CX - 360, 560, 720, 620, 2)
    # mountains (ink wash)
    for k, (yb, amp, col, a) in enumerate([(980, 120, hexc("#6d746f"), 0.55), (1040, 90, hexc("#4c5350"), 0.75),
                                           (1100, 60, hexc("#2e3331"), 0.95)]):
        pts = [(CX - 330, 1150)]
        for i in range(60):
            u = i / 59
            x = CX - 330 + 660 * u
            y = yb - amp * (0.5 + 0.5 * math.sin(u * 6.3 + k * 1.7)) * (0.6 + 0.4 * math.sin(u * 17 + k))
            pts.append((x, y))
        pts.append((CX + 330, 1150))
        c.poly(pts, col, a=a)
    c.circle(CX + 150, 720, 40, GOLD, a=0.6)
    # frame
    c.rrect(CX - 340, 580, CX + 340, 1160, 6, outline=hexc("#8a7a60"), width=14)
    c.line([(CX, 580), (CX, 1160)], hexc("#8a7a60"), 10)
    return c.layer()


@functools.lru_cache(maxsize=1)
def glass_sheen():
    c = Canvas(CX - 340, 580, 680, 580, 2)
    c.poly([(CX - 200, 580), (CX - 90, 580), (CX - 330, 1160), (CX - 340, 1160), (CX - 340, 1000)], WHITE, a=0.25)
    c.poly([(CX + 60, 580), (CX + 110, 580), (CX - 130, 1160), (CX - 180, 1160)], WHITE, a=0.18)
    c.rrect(CX - 330, 590, CX + 330, 1150, 4, c=MIST, a=0.18)
    return c.layer()


@functools.lru_cache(maxsize=1)
def rubber_scene():
    c = Canvas(60, 580, 960, 600, 2)
    c.rrect(80, 640, 1000, 1120, 18, c=hexc("#2a2622"), a=0.9)
    # partition
    c.rrect(CX - 12, 600, CX + 12, 1150, 4, c=hexc("#8a7a60"))
    hand(c, CX - 230, 900, PAPER, 0.95)  # rubber hand (visible)
    hand(c, CX + 230, 900, GREY, 0.35)  # real hand (hidden)
    c.text(CX - 230, 1090, "橡胶手（看得见）", ("serif", 30, 600), PAPER)
    c.text(CX + 230, 1090, "真手（被挡住）", ("serif", 30, 600), GREY)
    return c.layer()


def hand(c, x, y, col, a):
    c.rrect(x - 70, y - 40, x + 70, y + 130, 40, c=col, a=a)
    for i, (dx, L) in enumerate([(-52, 120), (-18, 150), (16, 145), (50, 120)]):
        c.rrect(x + dx - 15, y - L, x + dx + 15, y, 15, c=col, a=a)
    c.rrect(x + 60, y + 10, x + 110, y + 40, 15, c=col, a=a) if x < CX else c.rrect(x - 110, y + 10, x - 60, y + 40, 15, c=col, a=a)


@functools.lru_cache(maxsize=1)
def brush_icon():
    c = Canvas(CX - 30, 700, 60, 180, 2)
    c.rrect(CX - 9, 720, CX + 9, 830, 6, c=hexc("#b08a55"))
    c.poly([(CX - 18, 830), (CX + 18, 830), (CX + 12, 875), (CX - 12, 875)], hexc("#e8dcc0"))
    return c.layer()


@functools.lru_cache(maxsize=4)
def person(x, y, s, col, a):
    c = Canvas(int(x - 200 * s), int(y - 500 * s), int(400 * s), int(520 * s), 2)
    c.circle(x, y - 420 * s, 55 * s, c=col, a=a)
    c.rrect(x - 60 * s, y - 440 * s, x + 60 * s, y - 410 * s, 10 * s, c=hexc("#20262b"), a=a)  # headset strap
    c.poly([(x - 150 * s, y), (x - 130 * s, y - 300 * s), (x - 70 * s, y - 350 * s), (x + 70 * s, y - 350 * s),
            (x + 130 * s, y - 300 * s), (x + 150 * s, y)], col, a=a)
    return c.layer()


@functools.lru_cache(maxsize=1)
def dashed_up():
    c = Canvas(CX - 120, 760, 260, 200, 2)
    for i in range(6):
        u0, u1 = i / 6.5, (i + 0.5) / 6.5
        c.line([(CX - 100 + 200 * u0, 940 - 150 * u0), (CX - 100 + 200 * u1, 940 - 150 * u1)], GOLD, 4)
    c.poly([(CX + 120, 775), (CX + 88, 782), (CX + 106, 806)], GOLD)
    return c.layer()


@functools.lru_cache(maxsize=4)
def column_box(x, y, title, items, col):
    c = Canvas(x - 200, y - 260, 400, 520, 2)
    c.rrect(x - 190, y - 250, x + 190, y + 250, 16, c=col, a=0.14, outline=col, width=3)
    c.text(x, y - 180, title, ("serif", 42, 800), WHITE)
    for i, it in enumerate(items):
        c.text(x, y - 50 + i * 95, it, ("serif", 34, 500), WHITE)
    return c.layer()


def water_moon(frame, t, k):
    comp(frame, moon_sky(), k)
    # reflection: broken horizontal strokes
    img = np.zeros((420, W), np.float32)
    for i in range(16):
        y = 30 + i * 22
        w = 130 * (1 - i / 22) * (0.75 + 0.25 * math.sin(t * 1.5 + i * 0.9))
        xo = 18 * math.sin(t * 1.1 + i * 0.7)
        cv2.line(img, (int(CX - w + xo), y), (int(CX + w + xo), y), 1.0, 5, cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 1.5)
    a = img * 0.7
    comp(frame, Layer(0, 960, (a[..., None] * np.array(PAPER, np.float32)).astype(np.float32), a.astype(np.float32)), k)


@functools.lru_cache(maxsize=1)
def moon_sky():
    c = Canvas(0, 540, W, 440, 2)
    c.circle(CX, 690, 82, PAPER, a=0.95)
    c.line([(60, 950), (W - 60, 950)], GREY, 2, 0.6)
    return c.layer()


# ============================================================================ G: prediction & arrows
def draw_predict(frame, t, c):
    draw_mist(frame, t, 0.05, seed=9, speed=5, y0=300)
    comp_any(frame, T("三 · 苦", 120, CX, 800, GOLD, fnt="kaim"), c.vis("g01", "g02", 0.5))
    # prediction loop
    kp = c.vis("g02", "g05", 0.6)
    if kp > 0:
        comp_any(frame, T("预测加工", 84, CX, 430, GOLD, weight=800), kp)
        comp_any(frame, T("Predictive Processing", 40, CX, 520, GREY), kp)
        pred_diagram(frame, t, c, kp)
    # stairs
    ks = c.vis("g05", "g07", 0.6)
    if ks > 0:
        stairs(frame, t, c, ks)
    # Clark / Friston
    kc = c.vis("g07", "g08", 0.6)
    if kc > 0:
        comp(frame, book_layer("Surfing\nUncertainty", "Andy Clark · 2016", CX - 220, 800), kc)
        comp_any(frame, T("弗里斯顿", 56, CX + 250, 720, WHITE, weight=800), kc * c.at("g07", 0) and kc * fade(t, c.at("g07", 0.5), 0.5))
        comp_any(frame, T("自由能原理", 46, CX + 250, 800, GOLD), kc * fade(t, c.at("g07", 0.55), 0.5))
        comp_any(frame, T("（数学版本）", 34, CX + 250, 870, GREY), kc * fade(t, c.at("g07", 0.6), 0.5))
    # placebo / expectation
    ke = c.vis("g08", "g09", 0.6)
    if ke > 0:
        comp_any(frame, T("同样的刺激 · 不同的预期", 52, CX, 430, WHITE, weight=800), ke)
        for i, (lab, lv) in enumerate([("预期：轻", 0.3), ("预期：重", 0.8)]):
            x = CX - 230 + i * 460
            comp(frame, heat_icon(x, 640), ke)
            comp_any(frame, T(lab, 44, x, 790, WHITE), ke)
            comp(frame, meter(x, 880, lv * ease_out(fade(t, c.st("g08") + 0.8, 1.2))), ke)
        comp_any(frame, T("扭了一下？还是骨折了？", 46, CX, 1240, GOLD), ke * c.f("g08b", 0.5))
    # hierarchy
    kh = c.vis("g09", "g11", 0.6)
    if kh > 0:
        comp_any(frame, T("冥想：降低高层预测的权重？", 50, CX, 430, WHITE, weight=800), kh)
        names = ["感觉", "动作", "情境", "将来", "「我」"]
        fadek = fade(t, c.at("g09", 0.5), 3.0)
        for i, n in enumerate(names):
            y = 1150 - i * 140
            w = 760 - i * 120
            op = 1.0 if i < 3 else 1.0 - 0.7 * fadek * (i - 2) / 2
            comp(frame, layer_bar(CX, y, w, GOLD if i >= 3 else INDIGO), kh * op * 0.85)
            comp_any(frame, T(n, 42, CX, y, WHITE, shadow=False), kh * op)
        comp_any(frame, T("「我总是倒霉」「事情一定会变糟」", 38, CX, 520, GOLD), kh * c.f("g09b", 0.5))
        comp_any(frame, T("Laukkonen & Slagter, 2021", 30, CX, 1250, GREY), kh)
    # sutra
    k1 = c.vis("g11", "g13", 0.6)
    comp_any(frame, T("箭经", 150, CX, 780, GOLD, fnt="brush"), c.vis("g11", "g12", 0.5))
    comp_any(frame, paper_card(("愚癡無聞凡夫身觸生諸受，", "……增長二受，若身受、若心受。", "譬如士夫身被雙毒箭，極生苦痛。"),
                               "《雜阿含經》卷十七 第470經", y=760, width=960, fnt=("kaim", 50), seal="經"),
             c.vis("g12", "g13", 0.6))
    comp_any(frame, T("身受 + 心受 ＝ 两支毒箭", 56, CX, 760, WHITE, weight=800), c.vis("g13", "g14", 0.5))
    comp_any(frame, paper_card(("多聞聖弟子……唯生一受，", "所謂身受，不生心受。", "譬如士夫被一毒箭，不被第二毒箭。"),
                               "《雜阿含經》卷十七 第470經", y=760, width=960, fnt=("kaim", 50), seal="經"),
             c.vis("g14", "g15", 0.6))
    # arrows
    ka = c.vis("g15", "g19", 0.6)
    if ka > 0:
        arrows(frame, t, c, ka)
    kz = c.vis("g19", None, 0.6)
    if kz > 0:
        comp_any(frame, T("4 天 × 20 分钟冥想训练（15 人）", 44, CX, 430, WHITE), kz)
        for i, (lab, v, col) in enumerate([("难受程度", 0.57, GOLD), ("疼痛强度", 0.40, INDIGO)]):
            y = 640 + i * 240
            kk = fade(t, c.at("g19", 0.62 + 0.1 * i), 0.6)
            comp_any(frame, T(lab, 46, 120, y, WHITE, anchor="lm"), kz * kk)
            comp(frame, bar(120, y + 50, int(840 * v * ease_out(kk)), 50, col), kz * kk)
            comp_any(frame, T(f"−{int(v*100)}%", 60, 140 + int(840 * v) + 20, y + 75, col, anchor="lm", weight=800), kz * kk)
        comp_any(frame, T("Zeidan et al., J. Neurosci., 2011（与静息对比，无另设对照组）", 26, CX, 1230, GREY), kz)


def pred_diagram(frame, t, c, k):
    comp(frame, pred_static(), k)
    # descending prediction pulses and ascending signal pulses
    for i in range(3):
        ph = (t * 0.5 + i / 3) % 1
        comp_add(frame, glow_blob(CX - 140, int(660 + 380 * ph), 14, GOLD, 1.0), k * c.f("g03", 0.5))
        ph2 = (t * 0.5 + i / 3 + 0.5) % 1
        comp_add(frame, glow_blob(CX + 140, int(1040 - 380 * ph2), 14, WHITE, 0.9), k * c.f("g03", 0.5, 1.0))
    ke = c.f("g04", 0.5)
    pul = 0.6 + 0.4 * math.sin(t * 6)
    comp_add(frame, glow_blob(CX, 850, 40, CINNABAR, 0.9 * pul), k * ke)
    comp_any(frame, T("预测误差", 50, CX, 940, CINNABAR, weight=800), k * ke)
    comp_any(frame, T("推动感知 · 学习 · 情绪", 40, CX, 1250, WHITE), k * c.f("g04", 0.5, 1.5))


@functools.lru_cache(maxsize=1)
def pred_static():
    c = Canvas(60, 560, 960, 640, 2)
    c.rrect(CX - 300, 580, CX + 300, 660, 14, c=INDIGO, a=0.25, outline=INDIGO, width=3)
    c.text(CX, 620, "大脑的预测（自上而下）", ("serif", 38, 700), WHITE)
    c.rrect(CX - 300, 1040, CX + 300, 1120, 14, c=TEAL, a=0.25, outline=TEAL, width=3)
    c.text(CX, 1080, "感官信号（自下而上）", ("serif", 38, 700), WHITE)
    c.line([(CX - 140, 670), (CX - 140, 1030)], GOLD, 3, 0.6)
    c.poly([(CX - 140, 1032), (CX - 154, 1005), (CX - 126, 1005)], GOLD, a=0.8)
    c.line([(CX + 140, 1030), (CX + 140, 670)], WHITE, 3, 0.6)
    c.poly([(CX + 140, 668), (CX + 126, 695), (CX + 154, 695)], WHITE, a=0.8)
    return c.layer()


def stairs(frame, t, c, k):
    comp(frame, stairs_static(), k)
    s = c.s("g05")
    # glowing "expected" foot moving down the steps
    steps = [(220, 640), (360, 760), (500, 880), (640, 1000)]
    dur = 0.8
    i = int(max(0, s) / dur)
    u = (max(0, s) % dur) / dur
    if i < 3:
        a, b = steps[i], steps[i + 1]
        x = a[0] + (b[0] - a[0]) * u
        y = a[1] + (b[1] - a[1]) * u - 40 * math.sin(math.pi * u)
    else:
        # missing step: expected at (780, 1120) but falls further
        u2 = clamp((s - 3 * dur) / 0.6)
        x = 640 + 140 * u2
        y = 1000 + 260 * u2 ** 2
        flash = clamp(1 - (s - 3 * dur - 0.35) / 0.8) if s > 3 * dur + 0.3 else 0
        comp_add(frame, glow_blob(780, 1130, 90, CINNABAR, 0.8 * flash), k)
        if s > 3 * dur + 0.3:
            comp_any(frame, T("预测落空", 60, 760, 1270, CINNABAR, weight=800), k * fade(t, c.st("g05") + 3 * dur + 0.3, 0.3))
    comp_add(frame, glow_blob(int(x), int(y), 18, GOLD, 1.2), k)
    comp_any(frame, T("黑暗里下楼梯……", 54, CX, 430, WHITE), k)


@functools.lru_cache(maxsize=1)
def stairs_static():
    c = Canvas(60, 600, 960, 680, 2)
    col = hexc("#5c5a55")
    pts = [(120, 640)]
    for (x, y) in [(220, 640), (360, 760), (500, 880), (640, 1000)]:
        pts += [(x + 70, y + 20), (x + 70, y + 140)] if False else []
    x, y = 140, 660
    for i in range(4):
        c.line([(x, y), (x + 140, y), (x + 140, y + 120)], col, 6)
        x, y = x + 140, y + 120
    # expected (missing) step dashed
    for k in range(7):
        c.line([(x + k * 20, y), (x + k * 20 + 10, y)], GOLD, 4, 0.6)
    c.text(x + 70, y - 30, "以为还有一级", ("serif", 30, 600), GOLD)
    return c.layer()


@functools.lru_cache(maxsize=4)
def heat_icon(x, y):
    c = Canvas(x - 70, y - 90, 140, 180, 2)
    c.poly([(x, y - 80), (x + 45, y + 10), (x + 30, y + 60), (x - 30, y + 60), (x - 45, y + 10)], CINNABAR, a=0.85)
    c.poly([(x, y - 20), (x + 20, y + 25), (x + 12, y + 55), (x - 12, y + 55), (x - 20, y + 25)], GOLD, a=0.9)
    return c.layer()


@functools.lru_cache(maxsize=64)
def _meter(x, y, lv100):
    lv = lv100 / 100
    c = Canvas(x - 60, y - 10, 120, 330, 2)
    c.rrect(x - 40, y, x + 40, y + 300, 20, outline=GREY, width=3)
    h = int(290 * lv)
    if h > 4:
        c.rrect(x - 34, y + 295 - h, x + 34, y + 295, 16, c=CINNABAR, a=0.85)
    return c.layer()


def meter(x, y, lv):
    return _meter(x, y, int(lv * 100))


@functools.lru_cache(maxsize=8)
def layer_bar(x, y, w, col):
    c = Canvas(x - w // 2 - 4, y - 56, w + 8, 112, 2)
    c.rrect(x - w // 2, y - 52, x + w // 2, y + 52, 10, c=col, a=0.35, outline=col, width=2)
    return c.layer()


def arrows(frame, t, c, k):
    # target: seated small figure (body)
    tx, ty = CX + 120, 880
    comp(frame, small_figure(tx, ty), k)
    A = ink_arrow(460, PAPER, 1)
    # first arrow flies in from left during g15
    u = ease_out(clamp(c.s("g15") / 0.7))
    x = -100 + (tx - 40 + 100) * u
    comp(frame, place(A, x, ty - 30 + (1 - u) * -60, angle=0.12 * (1 - u)), k)
    comp_any(frame, T("第一支箭：身体的痛", 50, CX, 430, WHITE, weight=800), k * c.f("g15", 0.5))
    if u >= 1:
        comp_add(frame, glow_blob(tx - 40, ty - 30, 40, CINNABAR, 0.6 * clamp(1 - (c.s("g15") - 0.7) / 1.5)), k)
    if c.on("g16"):
        s = c.s("g16")
        # second arrow approaches slowly from upper left
        u2 = clamp(s / (c.en("g16") - c.st("g16") + 0.5))
        x2 = -80 + (tx - 120 + 80) * ease(u2) * 0.85
        y2 = 620 + 200 * ease(u2) * 0.85
        k_smoke = c.f("g17", 0.5)
        if k_smoke < 1:
            comp(frame, place(ink_arrow(460, CINNABAR, 2), x2, y2, angle=0.45), k * (1 - k_smoke))
        if c.on("g17"):
            comp(frame, smoke_layer(clamp(c.s("g17") / 3.0), int(x2 - 150), int(y2 - 60), seed=3, col=CINNABAR), k)
        comp_any(frame, T("第二支箭：心里补上的", 50, CX, 520, CINNABAR, weight=800), k * c.f("g16", 0.5) * (1 - k_smoke))
        words = ["怎么偏偏是我", "会不会更糟", "凭什么"]
        for i, wd in enumerate(words):
            kk = fade(t, c.at("g16", 0.45 + 0.17 * i), 0.4) * (1 - k_smoke)
            comp_any(frame, T(wd, 40, 210 + i * 40, 1080 + i * 70, GREY, anchor="lm"), k * kk)
        comp_any(frame, T("抵抗 · 担忧 · 关于「我」的故事", 44, CX, 1180, GOLD), k * c.vis("g17", "g18", 0.5))
        comp_any(frame, T("这是类比，不是同一件事", 50, CX, 1180, WHITE), k * c.f("g18", 0.5))


@functools.lru_cache(maxsize=2)
def small_figure(x, y):
    c = Canvas(x - 120, y - 170, 240, 300, 2)
    k = PAPER
    c.circle(x, y - 120, 34, c=k, a=0.85)
    c.poly([(x - 80, y + 70), (x - 70, y - 40), (x - 30, y - 80), (x + 30, y - 80), (x + 70, y - 40), (x + 80, y + 70)], k, a=0.85)
    c.ellipse(x, y + 80, 110, 30, k, a=0.85)
    return c.layer()


# ============================================================================ H: Thompson
def draw_thompson(frame, t, c):
    draw_mist(frame, t, 0.05, seed=10, speed=5, y0=300)
    comp_any(frame, T("一个冷静的声音", 76, CX, 800, WHITE, weight=800), c.vis("h01", "h02", 0.5))
    kb = c.vis("h02", "h04", 0.6)
    if kb > 0:
        comp(frame, lectern(), kb * 0.9)
        comp_any(frame, T("埃文·汤普森", 70, CX, 430, GOLD, weight=800), kb)
        comp_any(frame, T("Evan Thompson · 哲学家", 40, CX, 515, GREY), kb)
        comp_any(frame, T("1991《具身心智》（与瓦雷拉、罗施合著）", 38, CX, 1240, WHITE), kb * c.f("h02", 0.6, 2.5))
        comp(frame, book_layer("Why I Am\nNot a\nBuddhist", "Evan Thompson · 2020", CX, 820), kb * c.f("h03", 0.6))
    kq = c.vis("h04", "h06", 0.6)
    if kq > 0:
        comp_any(frame, T("佛教例外论", 70, CX, 420, GOLD, weight=800), kq)
        comp_any(frame, quote_card(), kq)
    kr = c.vis("h06", "h07", 0.6)
    if kr > 0:
        comp_any(frame, T("平等的对话", 80, CX, 600, GOLD, weight=800), kr)
        comp_any(frame, T("不拿科学给佛法背书", 50, CX, 780, WHITE), kr * c.f("h06", 0.5, 2.5))
        comp_any(frame, T("不拿佛法给科学贴金", 50, CX, 880, WHITE), kr * c.f("h06", 0.5, 4.0))
    kh = c.vis("h07", "h09", 0.6)
    if kh > 0:
        comp_any(frame, paper_card(("Mind the Hype",), "Perspectives on Psychological Science 13(1):36–61",
                                   y=720, width=900, fnt=("serif", 84, 800), small=("《小心炒作》 · Van Dam 等 15 位学者 · 2018",),
                                   src_size=24), kh)
        for i, s in enumerate(["概念不清", "样本偏小", "效果被夸大"]):
            comp(frame, pill(s, CX - 300 + i * 300, 1120, CINNABAR), kh * fade(t, c.at("h08", 0.15 + 0.22 * i), 0.5))
    kf = c.vis("h09", None, 0.8)
    comp_any(frame, T("或许，佛学的讲法也有科学基础", 52, CX, 700, WHITE), kf)
    comp_any(frame, T("算是一种印照", 60, CX, 800, WHITE, weight=800), kf * c.f("h09", 0.6, 2.0))
    comp_any(frame, T("印照，不是证明", 96, CX, 1000, GOLD, weight=900), kf * c.f("h10", 0.6))


@functools.lru_cache(maxsize=1)
def lectern():
    c = Canvas(CX - 300, 560, 600, 700, 2)
    k = hexc("#2a2520")
    c.poly([(CX - 200, 1220), (CX + 200, 1220), (CX + 150, 700), (CX - 150, 700)], k)
    c.poly([(CX - 240, 700), (CX + 240, 700), (CX + 200, 640), (CX - 200, 640)], hexc("#3a3128"))
    return c.layer()


@functools.lru_cache(maxsize=1)
def quote_card():
    en = ["Buddhist exceptionalism is the belief that Buddhism",
          "is superior to other religions in being inherently",
          "rational and empirical, or that Buddhism isn't really",
          "a religion but rather is a kind of ‘mind science,’",
          "therapy, philosophy, or way of life based on",
          "meditation. These beliefs ... are mistaken."]
    zh = ("「佛教例外论，是相信佛教天生理性、讲究经验，", "因而优于其他宗教；或者相信佛教其实不是宗教，",
          "而是一种『心智科学』、疗法、哲学或冥想生活方式。", "这些信念……是错误的。」（本片自译）")
    return paper_card(tuple(en), "Why I Am Not a Buddhist, Introduction, p. 2", y=810, width=980,
                      fnt=("serif", 32, 500), lh=1.45, small=zh, src_size=26, align="l")


# ============================================================================ I: close
def draw_close(frame, t, c):
    draw_mist(frame, t, 0.05, seed=6, speed=4, y0=600)
    k_lamp = c.vis("i01", None, 1.0)
    comp(frame, lamp_body(), k_lamp)
    comp_any(frame, flame_layers(t, wick_y=900, wind=0.05), k_lamp)
    comp_any(frame, T("回到那两支箭", 72, CX, 430, WHITE, weight=800), c.vis("i01", "i03", 0.5))
    steps = [("i03", "一", "痛来时，先停一下：「这是第一支箭」"), ("i04", "二", "看见自己正在拉弓"),
             ("i05", "三", "先不射 · 呼吸三次")]
    ks = c.vis("i03", "i05b", 0.6)
    for i, (lid, n, s) in enumerate(steps):
        kk = c.f(lid, 0.5)
        y = 1150 + i * 0  # stacked one at a time above the lamp
        comp_any(frame, T(n, 70, CX, 380, GOLD, fnt="kaim"), ks * kk * (1 - (c.f(steps[i + 1][0], 0.3) if i < 2 else 0)))
        comp_any(frame, T(s, 46, CX, 480, WHITE, weight=700), ks * kk * (1 - (c.f(steps[i + 1][0], 0.3) if i < 2 else 0)))
    comp_any(frame, T("第一支箭往往躲不开\n第二支，常常是自己射的", 48, CX, 440, GOLD), c.vis("i05b", "i06", 0.5))
    comp_any(frame, T("不是代替治疗\n而是少受一层心里的苦", 50, CX, 440, WHITE), c.vis("i06", "i07", 0.5))
    comp_any(frame, T("大脑里，有没有一个「总指挥」？", 52, CX, 440, GOLD, weight=800), c.vis("i07", "i08", 0.5))
    comp_any(frame, T("先看见第一支箭\n不再补上第二支", 64, CX, 450, WHITE, weight=800), c.vis("i08", "i09", 0.6))
    kf = c.f("i09", 1.0)
    comp_any(frame, T("譬如士夫被一毒箭", 84, CX, 420, PAPER, fnt="kaim"), kf)
    comp_any(frame, T("不被第二毒箭", 84, CX, 540, GOLD, fnt="kaim"), kf * c.f("i09", 0.8, 1.2))
    comp_any(frame, T("——《雜阿含經》卷十七 第470經", 34, CX, 640, GREY), kf * c.f("i09", 0.8, 2.0))


DRAW = dict(open=draw_open, survey=draw_survey, stance=draw_stance, lamp=draw_lamp, dmn=draw_dmn,
            noself=draw_noself, predict=draw_predict, thompson=draw_thompson, close=draw_close)
