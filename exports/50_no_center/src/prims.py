"""可复用的画面元件：神经星海、特征图、卡片、脑轮廓、图表、HUD。"""
import math, functools
import numpy as np, cv2
from engine import *

# ---------------- 3D neural field ----------------
class NeuralField:
    def __init__(self, n=2200, seed=7, depth=50.0, spread=13.0, k=2):
        rng = np.random.default_rng(seed)
        self.n = n
        self.depth = depth
        self.p = np.stack([rng.normal(0, spread, n), rng.normal(0, spread * 1.5, n), rng.uniform(0, depth, n)], 1).astype(np.float32)
        self.phase = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
        self.freq = rng.uniform(0.3, 1.6, n).astype(np.float32)
        self.hue = rng.random(n)
        # neighbours (in base coords; wrap ignored)
        P = self.p
        edges = []
        for i in range(n):
            d = np.sum((P - P[i]) ** 2, 1); d[i] = 1e9
            for j in np.argpartition(d, k)[:k]:
                if d[j] < (spread * 0.55) ** 2:
                    edges.append((i, int(j)))
        self.edges = np.array(sorted(set(tuple(sorted(e)) for e in edges)), np.int32)
        self.epulse = rng.uniform(0, 1, len(self.edges)).astype(np.float32)
        self.espeed = rng.uniform(0.2, 0.7, len(self.edges)).astype(np.float32)

    def draw(self, fr, t, camz=0.0, cx=W / 2, cy=H * 0.46, f=900.0, bright=1.0, cols=(CYAN, VIOLET, BLUE),
             rot=0.0, pulses=True, sharp=True, dim_center=0.0, ylim=(0, H)):
        P = self.p.copy()
        if rot:
            c, s = math.cos(rot), math.sin(rot)
            x = P[:, 0] * c - (P[:, 2] - self.depth / 2) * s
            z = P[:, 0] * s + (P[:, 2] - self.depth / 2) * c + self.depth / 2
            P[:, 0], P[:, 2] = x, z
        z = (P[:, 2] - camz) % self.depth + 0.8
        sx = cx + P[:, 0] / z * f
        sy = cy + P[:, 1] / z * f
        fog = np.clip(1.2 - z / self.depth, 0, 1) ** 1.3
        near = np.clip((z - 0.8) / 2.5, 0, 1)
        flick = 0.75 + 0.6 * np.sin(t * self.freq * 2.2 + self.phase)
        inten = fog * near * flick * bright
        if dim_center:
            dc = np.sqrt((sx - cx) ** 2 + (sy - cy) ** 2)
            inten *= 1 - dim_center * np.exp(-(dc / 170) ** 2)
        # edges, bucketed by brightness
        e = self.edges
        a, b = e[:, 0], e[:, 1]
        ok = (np.abs(z[a] - z[b]) < self.depth * 0.5) & (inten[a] > 0.03)
        ok &= (sy[a] > ylim[0]) & (sy[a] < ylim[1]) & (sy[b] > ylim[0]) & (sy[b] < ylim[1])
        ok &= (np.abs(sx[a] - sx[b]) + np.abs(sy[a] - sy[b])) < 320
        ei = np.minimum(inten[a], inten[b]) * 0.5
        for bk in range(5):
            lo, hi = bk / 5 * 0.6, (bk + 1) / 5 * 0.6 if bk < 4 else 9
            m = ok & (ei >= lo) & (ei < hi)
            if not m.any():
                continue
            segs = np.stack([np.stack([sx[a[m]], sy[a[m]]], 1), np.stack([sx[b[m]], sy[b[m]]], 1)], 1) / 2
            col = gcol(cols[bk % len(cols)], (lo + 0.05) * 0.55)
            cv2.polylines(fr.g, segs.astype(np.int32), False, col, 1, cv2.LINE_AA)
        if pulses:
            ph = (self.epulse + t * self.espeed) % 1.0
            sel = ok & (ei > 0.12) & (ph < 0.999)
            idx = np.nonzero(sel)[0][::3]
            for i in idx:
                k = ph[i]
                px = sx[a[i]] + (sx[b[i]] - sx[a[i]]) * k
                py = sy[a[i]] + (sy[b[i]] - sy[a[i]]) * k
                gdot(fr, (px, py), 3, WHITE, 0.6 * ei[i] * 2)
        # nodes
        order = np.argsort(-z)
        for i in order:
            it = inten[i]
            if it < 0.04 or not (ylim[0] < sy[i] < ylim[1]) or not (-50 < sx[i] < W + 50):
                continue
            r = np.clip(14.0 / z[i], 1.0, 12)
            c = cols[int(self.hue[i] * len(cols)) % len(cols)]
            hub = self.hue[i] > 0.975
            gdot(fr, (sx[i], sy[i]), r * (9 if hub else 3.2), c, it * (0.55 if hub else 0.7))
            if sharp and r > 1.2:
                circle(fr.img, (sx[i], sy[i]), r * 0.6, scale(mix(c, WHITE, 0.7), min(1, it * 1.5)))
        return sx, sy, inten

# ---------------- layered feature graph ----------------
class FeatureGraph:
    def __init__(self, layers=(6, 9, 11, 11, 9, 6), x0=110, x1=970, y0=560, y1=1300, seed=5, horizontal=False):
        rng = np.random.default_rng(seed)
        self.nodes = []
        L = len(layers)
        for li, n in enumerate(layers):
            for j in range(n):
                fx = li / (L - 1)
                fy = (j + 0.5) / n
                jx, jy = rng.normal(0, 0.012), rng.normal(0, 0.15 / n)
                if horizontal:
                    x, y = x0 + (x1 - x0) * (fx + jx), y0 + (y1 - y0) * (fy + jy)
                else:
                    x, y = x0 + (x1 - x0) * (fy + jy), y1 - (y1 - y0) * (fx + jx)
                self.nodes.append((x, y, li))
        self.nodes = np.array(self.nodes, np.float32)
        self.edges = []
        for i, (x, y, li) in enumerate(self.nodes):
            nxt = np.nonzero(self.nodes[:, 2] == li + 1)[0]
            if len(nxt):
                for j in rng.choice(nxt, size=min(3, len(nxt)), replace=False):
                    self.edges.append((i, int(j)))
        self.edges = np.array(self.edges, np.int32)
        self.phase = rng.uniform(0, 6.28, len(self.nodes))
        self.ephase = rng.uniform(0, 1, len(self.edges))

    def draw(self, fr, t, alpha=1.0, hot=None, hot_edges=None, col=CYAN, col2=VIOLET, flow=1.0, base=0.35):
        N = self.nodes
        for k, (i, j) in enumerate(self.edges):
            hk = hot_edges.get((i, j), 0) if hot_edges else 0
            c = mix(col, AMBER, hk)
            gline(fr, N[i][:2], N[j][:2], c, alpha * (0.10 + 0.6 * hk))
            if flow and alpha > 0.1:
                ph = (self.ephase[k] + t * 0.5) % 1
                p = N[i][:2] + (N[j][:2] - N[i][:2]) * ph
                gdot(fr, p, 3, WHITE if hk else col, alpha * (0.35 + hk) * flow)
        for i, (x, y, li) in enumerate(N):
            hv = hot.get(i, 0) if hot else 0
            fl = base + 0.3 * math.sin(t * 1.7 + self.phase[i])
            c = mix(col if i % 3 else col2, AMBER, hv)
            gdot(fr, (x, y), 10 + 10 * hv, c, alpha * (fl * 0.5 + hv))
            circle(fr.img, (x, y), 4 + 3 * hv, scale(mix(c, WHITE, 0.5), alpha * (0.5 + 0.5 * hv)))

# ---------------- brain outlines ----------------
@functools.lru_cache(maxsize=4)
def _brain_side_pts(seed=2):
    # side view outline (normalized, x right = front)
    pts = []
    for a in np.linspace(0, 2 * np.pi, 160, endpoint=False):
        r = 1.0 + 0.025 * math.sin(5 * a) + 0.015 * math.sin(11 * a + 1)
        x = math.cos(a) * 1.0 * r
        y = -math.sin(a) * 0.72 * r
        if math.sin(a) < 0:   # flatten bottom
            y *= 0.75
        pts.append((x, y))
    rng = np.random.default_rng(seed)
    gyri = []
    for _ in range(16):
        x0, y0 = rng.uniform(-0.75, 0.75), rng.uniform(-0.5, 0.35)
        ang = rng.uniform(0, np.pi)
        seg = []
        for s in np.linspace(0, 1, 14):
            seg.append((x0 + math.cos(ang) * s * 0.45 + 0.05 * math.sin(s * 14), y0 + math.sin(ang) * s * 0.3 + 0.04 * math.cos(s * 17)))
        gyri.append(seg)
    return np.array(pts), gyri

def brain_side(fr, cx, cy, s, col=CYAN, k=1.0, gyri=True):
    pts, gy = _brain_side_pts()
    P = (pts * s + (cx, cy)).astype(np.int32)
    cv2.polylines(fr.img, [P], True, scale(col, 0.75 * k), 3, cv2.LINE_AA)
    cv2.polylines(fr.g, [(P / 2).astype(np.int32)], True, gcol(col, 0.35 * k), 2, cv2.LINE_AA)
    if gyri:
        for seg in gy:
            q = (np.array(seg) * s + (cx, cy)).astype(np.int32)
            q = q[[((x - cx) / s) ** 2 + ((y - cy) / (0.62 * s)) ** 2 < 0.8 for x, y in q]]
            if len(q) > 1:
                cv2.polylines(fr.img, [q], False, scale(col, 0.28 * k), 2, cv2.LINE_AA)
    # cerebellum + stem
    cv2.ellipse(fr.img, (int(cx - 0.62 * s), int(cy + 0.5 * s)), (int(0.28 * s), int(0.16 * s)), 10, 0, 360, scale(col, 0.4 * k), 2, cv2.LINE_AA)
    line(fr.img, (cx - 0.25 * s, cy + 0.5 * s), (cx - 0.32 * s, cy + 0.95 * s), scale(col, 0.4 * k), 3)

def brain_top(fr, cx, cy, s, col=CYAN, k=1.0, gap=0.0, lcol=None, rcol=None, lk=1.0, rk=1.0):
    """top view, two hemispheres; gap separates them (pixels)"""
    for side in (-1, 1):
        c = (lcol if side < 0 else rcol) or col
        kk = k * (lk if side < 0 else rk)
        pts = []
        for a in np.linspace(-np.pi / 2, np.pi / 2, 60):
            x = math.cos(a) * 0.52 * s * (1 + 0.04 * math.sin(7 * a))
            y = math.sin(a) * 0.78 * s
            pts.append((cx + side * (x + 8 + gap / 2), cy + y))
        pts.append((cx + side * (8 + gap / 2), cy + 0.78 * s))
        pts.append((cx + side * (8 + gap / 2), cy - 0.78 * s))
        P = np.array(pts, np.int32)
        cv2.polylines(fr.img, [P], True, scale(c, 0.8 * kk), 3, cv2.LINE_AA)
        cv2.polylines(fr.g, [(P / 2).astype(np.int32)], True, gcol(c, 0.4 * kk), 2, cv2.LINE_AA)
        for j in range(7):
            yy = cy - 0.6 * s + j * 0.2 * s
            q = [(cx + side * (gap / 2 + 20 + u * 0.38 * s), yy + 12 * math.sin(u * 9 + j)) for u in np.linspace(0, 1, 12)]
            cv2.polylines(fr.img, [np.array(q, np.int32)], False, scale(c, 0.25 * kk), 2, cv2.LINE_AA)

# ---------------- cards ----------------
def card_box(img, x0, y0, x1, y1, a=1.0, border=CYAN, fill=(8, 14, 28), fa=0.82):
    if a <= 0.01:
        return
    rect_alpha(img, x0, y0, x1, y1, fill, fa * a)
    rounded(img, x0, y0, x1, y1, 14, scale(border, 0.8 * a), 2)

def tag(img, s, x, y, col=AMBER, a=1.0, size=34, anchor="m"):
    if a <= 0.01:
        return
    w, h = text_size(s, size, "sansb")
    pad = 18
    x0 = x - w / 2 - pad if anchor == "m" else x
    rect_alpha(img, x0, y - h / 2 - 6, x0 + w + 2 * pad, y + h / 2 + 4, scale(col, 0.18), 0.85 * a)
    rounded(img, x0, y - h / 2 - 6, x0 + w + 2 * pad, y + h / 2 + 4, 10, scale(col, a), 2)
    text(img, s, x0 + pad + w / 2, y, size, "sansb", col, "mm", a)

def book_card(img, y, title_cn, title_en, meta, a=1.0, extra=None, col=CYAN):
    if a <= 0.01:
        return
    y = int(y + (1 - ease_out(a)) * 40)
    lines_en = wrap(title_en, 38, "serif", 820)
    hgt = 120 + 56 * len(lines_en) + (64 if meta else 0) + (60 if extra else 0)
    card_box(img, 80, y, W - 80, y + hgt, a, col)
    text(img, title_cn, W / 2, y + 62, 54, "serifb", WHITE, "mm", a)
    yy = y + 112
    for ln in lines_en:
        text(img, ln, W / 2, yy, 38, "serif", scale(GREY, 1.15), "mt", a); yy += 56
    if meta:
        text(img, meta, W / 2, yy + 14, 34, "sans5", col, "mt", a); yy += 64
    if extra:
        text(img, extra, W / 2, yy + 8, 30, "sans", GREY, "mt", a)
    return y + hgt

def quote_card(img, y, original, source, plain=None, a=1.0, col=AMBER, size=50, fname="serifb", en=False, maxw=860):
    if a <= 0.01:
        return y
    y = int(y + (1 - ease_out(a)) * 30)
    ls = wrap(original, size, fname, maxw)
    pl = wrap(plain, 38, "sans", maxw) if plain else []
    sl = wrap(source, 30, "sans", maxw)
    hgt = 70 + len(ls) * size * 1.55 + 30 + len(sl) * 44 + (30 + len(pl) * 56 if pl else 0) + 30
    card_box(img, 70, y, W - 70, y + hgt, a, col, fa=0.86)
    line(img, (100, y + 40), (100, y + hgt - 40), scale(col, 0.8 * a), 4)
    yy = y + 52
    for ln in ls:
        text(img, ln, 130, yy, size, fname, WHITE, "lt", a); yy += size * 1.55
    yy += 18
    for ln in sl:
        text(img, ln, W - 110, yy, 30, "sans", col, "rt", a); yy += 44
    if pl:
        yy += 22
        line(img, (130, yy - 10), (W - 110, yy - 10), scale(GREY, 0.4 * a), 1)
        for ln in pl:
            text(img, ln, 130, yy + 6, 38, "sans", scale(WHITE, 0.92), "lt", a); yy += 56
    return y + hgt

# ---------------- chart ----------------
def chart_axes(fr, x0, y0, x1, y1, a=1.0, xl="模型规模 →", yl="得分", col=GREY):
    img = fr.img
    line(img, (x0, y1), (x1, y1), scale(col, a), 3)
    line(img, (x0, y1), (x0, y0), scale(col, a), 3)
    cv2.arrowedLine(img, (int(x1 - 20), int(y1)), (int(x1 + 10), int(y1)), scale(col, a), 3, cv2.LINE_AA, tipLength=0.9)
    text(img, xl, x1, y1 + 46, 32, "sans5", scale(col, 1.2), "rm", a)
    text(img, yl, x0 + 14, y0 - 30, 32, "sans5", scale(col, 1.2), "lm", a)

def curve(fr, pts, col, a=1.0, upto=1.0, th=5, dots=True):
    n = max(2, int(len(pts) * clamp(upto)))
    P = np.array(pts[:n], np.int32)
    cv2.polylines(fr.img, [P], False, scale(col, a), th, cv2.LINE_AA)
    cv2.polylines(fr.g, [(P / 2).astype(np.int32)], False, gcol(col, 0.6 * a), 3, cv2.LINE_AA)
    if dots:
        for p in pts[:n][::max(1, len(pts) // 9)]:
            circle(fr.img, p, 8, scale(col, a))

# ---------------- HUD ----------------
def reticle(fr, cx, cy, r, t, col=CYAN, a=1.0):
    img = fr.img
    for k, rr in enumerate((r, r * 0.62)):
        ang = t * (40 if k == 0 else -65)
        for q in range(4):
            cv2.ellipse(img, (int(cx), int(cy)), (int(rr), int(rr)), ang + q * 90, 8, 62, scale(col, a * (0.9 - 0.3 * k)), 3, cv2.LINE_AA)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        line(img, (cx + dx * r * 1.1, cy + dy * r * 1.1), (cx + dx * r * 1.35, cy + dy * r * 1.35), scale(col, a), 3)
    gring(fr, (cx, cy), r, col, 0.25 * a, 2)

def scanlines(img, t, a=0.06):
    y = int((t * 260) % H)
    rect_alpha(img, 0, y, W, y + 3, CYAN, a)

def arrow(img, p, q, col, th=4, a=1.0, tip=0.12):
    cv2.arrowedLine(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), scale(col, a), th, cv2.LINE_AA, tipLength=tip)

def head_profile(fr, cx, cy, s, col=AMBER, k=1.0, glow=True):
    """side-facing head silhouette outline (facing right)"""
    pts = [(-0.55, 0.95), (-0.5, 0.55), (-0.62, 0.2), (-0.62, -0.3), (-0.45, -0.68), (-0.1, -0.88), (0.25, -0.85), (0.5, -0.65),
           (0.6, -0.35), (0.6, -0.1), (0.72, 0.12), (0.62, 0.2), (0.64, 0.32), (0.58, 0.38), (0.6, 0.48), (0.5, 0.6), (0.3, 0.62),
           (0.25, 0.95)]
    P = np.array([(cx + x * s, cy + y * s) for x, y in pts])
    # smooth via chaikin
    for _ in range(3):
        Q = []
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]
            Q += [a * 0.75 + b * 0.25, a * 0.25 + b * 0.75]
        P = np.array([P[0]] + Q + [P[-1]])
    Pi = P.astype(np.int32)
    cv2.polylines(fr.img, [Pi], False, scale(col, 0.85 * k), 3, cv2.LINE_AA)
    if glow:
        cv2.polylines(fr.g, [(P / 2).astype(np.int32)], False, gcol(col, 0.5 * k), 3, cv2.LINE_AA)
    return P

def seated_figure(fr, cx, cy, s, col=WHITE, k=1.0):
    """meditating silhouette: crossed legs, torso, arms resting, head; dark fill with soft warm rim"""
    img = fr.img
    dark = (5, 7, 13)
    rim = scale(col, 0.45 * k)
    legs = ((int(cx), int(cy + 0.28 * s)), (int(0.95 * s), int(0.24 * s)))
    torso = np.array([(cx - 0.36 * s, cy - 0.62 * s), (cx + 0.36 * s, cy - 0.62 * s), (cx + 0.30 * s, cy + 0.15 * s),
                      (cx - 0.30 * s, cy + 0.15 * s)], np.int32)
    shoulders = ((int(cx), int(cy - 0.6 * s)), (int(0.40 * s), int(0.16 * s)))
    arms = [((int(cx + d * 0.42 * s), int(cy - 0.2 * s)), (int(0.13 * s), int(0.45 * s)), d * -18) for d in (-1, 1)]
    head = ((int(cx), int(cy - 1.0 * s)), int(0.2 * s))
    neck = ((int(cx), int(cy - 0.78 * s)), (int(0.08 * s), int(0.1 * s)))
    for th, c in ((5, rim), (-1, dark)):
        cv2.ellipse(img, legs[0], legs[1], 0, 0, 360, c, th, cv2.LINE_AA)
        for (p, ax, ang) in arms:
            cv2.ellipse(img, p, ax, ang, 0, 360, c, th, cv2.LINE_AA)
        if th < 0:
            cv2.fillPoly(img, [torso], c, cv2.LINE_AA)
        else:
            cv2.polylines(img, [torso], True, c, th, cv2.LINE_AA)
        cv2.ellipse(img, shoulders[0], shoulders[1], 0, 180, 360, c, th, cv2.LINE_AA)
        cv2.ellipse(img, neck[0], neck[1], 0, 0, 360, c, th, cv2.LINE_AA)
        cv2.circle(img, head[0], head[1], c, th, cv2.LINE_AA)
    cv2.ellipse(fr.g, (int(cx / 2), int((cy - 0.3 * s) / 2)), (int(0.6 * s), int(0.75 * s)), 0, 0, 360, gcol(col, 0.015 * k), -1, cv2.LINE_AA)
