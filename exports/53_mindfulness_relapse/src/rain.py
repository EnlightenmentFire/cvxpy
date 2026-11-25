# -*- coding: utf-8 -*-
"""Rain-on-window scene: out-of-focus city behind glass, refracting droplets that merge into rivulets,
a seated silhouette breathing slowly, warm lamp, optional dawn."""
import functools
import numpy as np, cv2
from PIL import Image, ImageDraw
from engine import W, H, FPS, rgb, clamp, ease

GLASS_BOTTOM = 1390           # sill top edge
MULLION_X, MULLION_W = 790, 24
TRANSOM_Y, TRANSOM_H = 470, 20


# ---------------------------------------------------------------- background behind the glass
@functools.lru_cache(maxsize=4)
def city(seed=7):
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = rgb((8, 12, 24)); mid = rgb((20, 34, 52)); low = rgb((34, 40, 52))
    g = np.where(yy < 0.55, top + (mid - top) * (yy / 0.55), mid + (low - mid) * ((yy - 0.55) / 0.45))
    img = np.broadcast_to(g, (H, W, 3)).copy()
    # far building blocks (very soft)
    for _ in range(14):
        x0 = rng.uniform(-100, W); w = rng.uniform(80, 260); y0 = rng.uniform(620, 980)
        c = rgb((14, 20, 32)) * rng.uniform(0.8, 1.2)
        cv2.rectangle(img, (int(x0), int(y0)), (int(x0 + w), H), c.tolist(), -1)
    lights = np.zeros((H, W, 3), np.float32)
    pal = [(255, 178, 92), (255, 206, 140), (120, 190, 255), (255, 120, 80), (180, 220, 255), (255, 228, 180)]
    for _ in range(260):
        x = rng.uniform(0, W); y = rng.uniform(560, 1500) if rng.random() < 0.8 else rng.uniform(150, 600)
        r = rng.uniform(3, 14) * (1.6 if y > 1000 else 1)
        c = np.array(pal[rng.integers(len(pal))], np.float32) / 255 * rng.uniform(0.25, 0.9)
        cv2.circle(lights, (int(x), int(y)), int(r), c.tolist(), -1, cv2.LINE_AA)
    # street-light streaks (car lights) low in frame
    for _ in range(18):
        y = rng.uniform(1150, 1380); x = rng.uniform(0, W); L = rng.uniform(40, 160)
        c = np.array(pal[rng.integers(3)], np.float32) / 255 * 0.5
        cv2.line(lights, (int(x), int(y)), (int(x + L), int(y + rng.uniform(-5, 5))), c.tolist(), 4, cv2.LINE_AA)
    sharp = img + cv2.GaussianBlur(lights, (0, 0), 7) * 1.4 + cv2.GaussianBlur(lights, (0, 0), 24) * 0.8
    sharp = cv2.GaussianBlur(sharp, (0, 0), 2.5)
    fog = cv2.GaussianBlur(sharp, (0, 0), 22) * 0.92 + rgb((22, 30, 42)) * 0.12
    return sharp.astype(np.float32), fog.astype(np.float32)


@functools.lru_cache(maxsize=4)
def dawn_sky(seed=9):
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = rgb((92, 124, 160)); mid = rgb((214, 190, 168)); low = rgb((246, 206, 150))
    g = np.where(yy < 0.5, top + (mid - top) * (yy / 0.5), mid + (low - mid) * np.clip((yy - 0.5) / 0.35, 0, 1))
    img = np.broadcast_to(g, (H, W, 3)).copy()
    rng = np.random.default_rng(seed)
    for _ in range(12):  # distant rooftops, hazy
        x0 = rng.uniform(-100, W); w = rng.uniform(90, 280); y0 = rng.uniform(900, 1150)
        cv2.rectangle(img, (int(x0), int(y0)), (int(x0 + w), H), (rgb((150, 140, 140)) * rng.uniform(0.85, 1.05)).tolist(), -1)
    sun = np.zeros((H, W, 1), np.float32)
    cv2.circle(sun, (820, 880), 70, 1.0, -1, cv2.LINE_AA)
    img += cv2.GaussianBlur(sun, (0, 0), 60)[..., None].reshape(H, W, 1) * rgb((255, 220, 160)) * 0.9
    img += cv2.GaussianBlur(sun, (0, 0), 12).reshape(H, W, 1) * rgb((255, 240, 210)) * 0.6
    sharp = cv2.GaussianBlur(img, (0, 0), 9)
    fog = cv2.GaussianBlur(sharp, (0, 0), 18)
    return sharp.astype(np.float32), fog.astype(np.float32)


# ---------------------------------------------------------------- interior: frame, silhouette, lamp
@functools.lru_cache(maxsize=2)
def silhouette_mask():
    S = 2
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)
    def P(pts):
        return [(x * S, y * S) for x, y in pts]
    # seated on the window seat, back to the left wall, knees drawn up, looking out to the right
    body = [(150, 1392), (138, 1300), (140, 1200), (158, 1120), (190, 1072), (232, 1046), (256, 1022),
            (262, 996), (312, 996), (330, 1030), (352, 1060), (420, 1074), (470, 1080), (510, 1090), (534, 1116),
            (540, 1170), (548, 1260), (556, 1340), (566, 1376), (606, 1384), (612, 1392), (520, 1392),
            (508, 1340), (500, 1270), (488, 1200), (472, 1166), (420, 1205), (360, 1260), (300, 1320),
            (250, 1372), (240, 1392)]
    d.polygon(P(body), fill=255)
    d.ellipse(P([(238, 870), (354, 1002)]), fill=255)            # head
    d.ellipse(P([(210, 890), (258, 938)]), fill=255)             # low bun
    d.polygon(P([(348, 922), (362, 944), (348, 954)]), fill=255)  # nose hint
    m = np.asarray(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0
    return m


@functools.lru_cache(maxsize=2)
def interior_layers():
    """Returns (frame_alpha, frame_rgb, room_rgb_alpha) static pieces."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    frame_a = np.zeros((H, W), np.float32)
    frame_a[:, MULLION_X:MULLION_X + MULLION_W] = 1
    frame_a[TRANSOM_Y:TRANSOM_Y + TRANSOM_H, :] = 1
    frame_a[:, :26] = 1; frame_a[:, W - 26:] = 1
    frame_a[GLASS_BOTTOM:, :] = 1
    frame_a = cv2.GaussianBlur(frame_a, (0, 0), 0.8)
    room = np.zeros((H, W, 3), np.float32)
    room[:] = rgb((12, 11, 12))
    sill = (yy >= GLASS_BOTTOM) & (yy < GLASS_BOTTOM + 70)
    room[sill] = rgb((44, 34, 28))
    room[(yy >= GLASS_BOTTOM) & (yy < GLASS_BOTTOM + 6)] = rgb((96, 78, 62))
    room[(yy >= GLASS_BOTTOM + 70)] = rgb((10, 9, 9))
    # frame wood
    fr = np.ones((H, W, 3), np.float32) * rgb((22, 19, 18))
    edge = np.zeros((H, W), np.float32)
    edge[:, MULLION_X:MULLION_X + 3] = 1; edge[TRANSOM_Y + TRANSOM_H - 3:TRANSOM_Y + TRANSOM_H, :] = 1
    fr += cv2.GaussianBlur(edge, (0, 0), 1.0)[..., None] * rgb((70, 80, 96))
    frame_rgb = np.where((yy >= GLASS_BOTTOM)[..., None], room, fr)
    # lamp glow (warm, lower-left), applied additively
    d2 = ((xx - 40) / 760) ** 2 + ((yy - 1540) / 760) ** 2
    lamp = np.exp(-d2 * 2.2)[..., None] * rgb((255, 170, 96)) * np.where(yy > GLASS_BOTTOM + 70, 0.45, 1.0)[..., None]
    return frame_a, frame_rgb.astype(np.float32), lamp.astype(np.float32)


# ---------------------------------------------------------------- droplets
K_LENS = 2.6


@functools.lru_cache(maxsize=64)
def drop_template(r, aspect=1.0):
    """Unit-drop arrays for radius r (px): local (u,v), alpha, shade, spec."""
    rx, ry = r, r * aspect
    R = int(np.ceil(max(rx, ry))) + 2
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    u, v = xx / rx, yy / ry
    dd = np.sqrt(u * u + v * v)
    alpha = np.clip((1 - dd) * min(rx, ry) * 0.9, 0, 1)
    shade = 1.0 - 0.6 * np.clip((dd - 0.55) / 0.45, 0, 1) ** 1.5 * (0.6 + 0.4 * np.clip(v + 0.3, 0, 1))
    spec = np.exp(-(((u + 0.33) ** 2 + (v + 0.42) ** 2) / 0.035)) * 0.9 * min(1.0, max(0.15, (r - 1.5) / 6))
    spec += np.exp(-(((u - 0.1) ** 2 + (v - 0.62) ** 2) / 0.05)) * 0.18
    return R, u.astype(np.float32), v.astype(np.float32), alpha.astype(np.float32), shade.astype(np.float32), spec.astype(np.float32)


class RainField:
    """Deterministic droplet field over [0, dur] seconds."""

    def __init__(self, dur, seed=1, n_static=2600, slide_per_min=40, respawn=True, heroes=()):
        rng = np.random.default_rng(seed)
        self.dur = dur
        n = n_static
        self.sx = rng.uniform(28, W - 28, n).astype(np.float32)
        self.sy = rng.uniform(10, GLASS_BOTTOM - 8, n).astype(np.float32)
        self.sr = np.clip(1.7 + rng.pareto(1.9, n) * 2.9, 1.7, 15).astype(np.float32)
        self.sa = rng.uniform(0.92, 1.12, n).astype(np.float32)
        self.born = np.where(rng.random(n) < 0.6, -1.0, rng.uniform(0, dur, n)).astype(np.float32) if respawn else np.full(n, -1, np.float32)
        # sliding drops
        m = max(3, int(slide_per_min * dur / 60) + 4)
        self.paths = []
        ts = np.arange(0, dur + 2, 1 / FPS)
        for k in range(m):
            t0 = rng.uniform(-6, dur - 1)
            x0 = rng.uniform(60, W - 60)
            y0 = rng.uniform(20, GLASS_BOTTOM * 0.6)
            r = rng.uniform(9, 15)
            # stick-slip velocity
            base = rng.uniform(70, 200)
            nseg = int((dur + 10) * 2)
            seg = rng.random(nseg)
            vel = np.where(seg < 0.25, 0.0, base * rng.uniform(0.6, 1.8, nseg))
            tt = np.arange(nseg) * 0.5 + t0
            vt = np.interp(ts, tt, vel, left=0, right=0)
            vt[ts < t0] = 0
            y = y0 + np.cumsum(vt) / FPS
            x = x0 + 6 * np.sin((y - y0) / 90 + rng.uniform(0, 6)) + np.cumsum(rng.normal(0, 0.15, len(ts)))
            alive = (ts >= t0) & (y < GLASS_BOTTOM - 4)
            self.paths.append(dict(t0=t0, x=x.astype(np.float32), y=y.astype(np.float32), r=r, alive=alive))
        for (hx, hy, ht0, hv, hr) in heroes:     # guaranteed rivulets in view (opening shot)
            vt = np.where(ts >= ht0, hv * (0.75 + 0.25 * np.sin(ts * 1.7 + hx)), 0.0)
            y = hy + np.cumsum(vt) / FPS
            x = hx + 5 * np.sin((y - hy) / 80) + np.cumsum(rng.normal(0, 0.12, len(ts)))
            alive = (ts >= ht0) & (y < GLASS_BOTTOM - 4)
            self.paths.append(dict(t0=ht0, x=x.astype(np.float32), y=y.astype(np.float32), r=hr, alive=alive))
        # erase static drops swallowed by sliders; trail drops
        self.erase = np.full(n, 1e9, np.float32)
        tx, ty, tr, tb = [], [], [], []
        for p in self.paths:
            idx = np.nonzero(p["alive"])[0]
            if len(idx) == 0:
                continue
            px, py = p["x"][idx], p["y"][idx]
            for j in range(0, len(idx), 2):
                d2 = (self.sx - px[j]) ** 2 + (self.sy - py[j]) ** 2
                hit = d2 < (p["r"] + self.sr) ** 2
                tj = idx[j] / FPS
                self.erase = np.where(hit & (self.born < tj), np.minimum(self.erase, tj), self.erase)
            # trail every ~18 px of travel
            last = -1e9
            for j in range(len(idx)):
                if py[j] - last > rng.uniform(12, 26):
                    last = py[j]
                    tx.append(px[j] + rng.normal(0, 1.5)); ty.append(py[j] - p["r"] * 0.8)
                    tr.append(rng.uniform(1.4, 3.2)); tb.append(idx[j] / FPS)
        self.tx, self.ty = np.array(tx, np.float32), np.array(ty, np.float32)
        self.tr, self.tb = np.array(tr, np.float32), np.array(tb, np.float32)

    def frame_drops(self, t, evap=0.0):
        """List of (x, y, r, aspect) visible at time t."""
        out = []
        vis = (self.born <= t) & (self.erase > t)
        shrink = 1 - evap
        for x, y, r, a in zip(self.sx[vis], self.sy[vis], self.sr[vis], self.sa[vis]):
            rr = r * shrink
            if rr >= 1.2:
                out.append((x, y, rr, a))
        tv = self.tb <= t
        for x, y, r in zip(self.tx[tv], self.ty[tv], self.tr[tv]):
            rr = r * shrink
            if rr >= 1.1:
                out.append((x, y, rr, 1.0))
        fi = int(t * FPS)
        for p in self.paths:
            if fi < len(p["alive"]) and p["alive"][fi]:
                x, y, r = p["x"][fi], p["y"][fi], p["r"] * shrink
                if r > 1.5:
                    out.append((x, y - r * 0.9, r * 0.62, 1.1))   # tail
                    out.append((x, y, r, 1.18))
        return out

    def clear_mask(self, t, clear=None):
        """Streaks wiped through the fog by sliding drops (fog slowly returns)."""
        m = np.zeros((H // 2, W // 2), np.float32)
        fi = int(t * FPS)
        for p in self.paths:
            a = p["alive"][:fi + 1]
            idx = np.nonzero(a)[0]
            if len(idx) < 2:
                continue
            idx = idx[::3]
            for j0, j1 in zip(idx[:-1], idx[1:]):
                age = t - j1 / FPS
                inten = float(np.exp(-age / 18.0))
                if inten < 0.05:
                    continue
                cv2.line(m, (int(p["x"][j0] / 2), int(p["y"][j0] / 2)), (int(p["x"][j1] / 2), int(p["y"][j1] / 2)),
                         inten, max(1, int(p["r"] * 0.75)), cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 2.5)
        return cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)


def render_drops(glass, sharp, drops):
    """Composite refracting droplets onto `glass` (in place) sampling `sharp`."""
    mapx = np.tile(np.arange(W, dtype=np.float32), (H, 1))
    mapy = np.tile(np.arange(H, dtype=np.float32)[:, None], (1, W))
    A = np.zeros((H, W), np.float32)
    S = np.ones((H, W), np.float32)
    SP = np.zeros((H, W), np.float32)
    for x, y, r, a in drops:
        rq = round(float(r) * 2) / 2
        R, u, v, al, sh, sp = drop_template(rq, round(float(a), 1))
        xi, yi = int(round(x)), int(round(y))
        x0, y0, x1, y1 = xi - R, yi - R, xi + R + 1, yi + R + 1
        if x0 < 0 or y0 < 0 or x1 > W or y1 > GLASS_BOTTOM:
            continue
        m = al > A[y0:y1, x0:x1]
        mapx[y0:y1, x0:x1][m] = (x - u * rq * K_LENS)[m]
        mapy[y0:y1, x0:x1][m] = (y - v * rq * K_LENS * a)[m]
        A[y0:y1, x0:x1][m] = al[m]
        S[y0:y1, x0:x1][m] = sh[m]
        SP[y0:y1, x0:x1][m] = sp[m]
    ref = cv2.remap(sharp, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ref = ref * S[..., None] * 1.12 + SP[..., None] * np.array([1.0, 0.93, 0.85], np.float32)
    glass *= (1 - A[..., None])
    glass += ref * A[..., None]
    return glass


def rain_streaks(t, amount, seed=5):
    if amount <= 0.01:
        return None
    rng = np.random.default_rng(seed + int(t * FPS))
    L = np.zeros((H // 2, W // 2), np.float32)
    for _ in range(int(60 * amount)):
        x = rng.uniform(0, W / 2); y = rng.uniform(0, GLASS_BOTTOM / 2); l = rng.uniform(18, 50)
        cv2.line(L, (int(x), int(y)), (int(x - l * 0.18), int(y + l)), float(rng.uniform(0.15, 0.5)), 1, cv2.LINE_AA)
    L = cv2.GaussianBlur(L, (0, 0), 0.8)
    return cv2.resize(L, (W, H))[..., None] * np.array([0.65, 0.72, 0.8], np.float32) * 0.5


class RainWindow:
    def __init__(self, dur, seed=1, rain=1.0, dawn=(0.0, 0.0), push=(1.0, 1.07), person=True, breath=(4.2, 6.0),
                 n_static=2600, slide_per_min=40, evap=(0.0, 0.0), heroes=()):
        self.dur, self.rain, self.dawn, self.push, self.person = dur, rain, dawn, push, person
        self.breath, self.evap = breath, evap
        self.field = RainField(dur, seed=seed, n_static=n_static, slide_per_min=slide_per_min, heroes=heroes)
        self.seed = seed

    def render(self, t):
        u = clamp(t / max(self.dur, 1e-3))
        dawn = self.dawn[0] + (self.dawn[1] - self.dawn[0]) * ease(u)
        evap = self.evap[0] + (self.evap[1] - self.evap[0]) * ease(u)
        cs, cf = city()
        if dawn > 0:
            ds, df = dawn_sky()
            sharp = cs * (1 - dawn) + ds * dawn
            fog = cf * (1 - dawn) + df * dawn
        else:
            sharp, fog = cs, cf
        # slow drift of the background (parallax)
        dx = 10 * np.sin(t * 0.05)
        Mx = np.float32([[1, 0, dx], [0, 1, 0]])
        sharp = cv2.warpAffine(sharp, Mx, (W, H), borderMode=cv2.BORDER_REFLECT)
        fog = cv2.warpAffine(fog, Mx, (W, H), borderMode=cv2.BORDER_REFLECT)
        fogk = 0.85 * (1 - 0.7 * dawn)
        clr = self.field.clear_mask(t)
        mix = np.clip(1 - fogk + clr * fogk * 1.2, 0, 1)[..., None]
        glass = fog * (1 - mix) + sharp * mix
        rs = rain_streaks(t, self.rain * (1 - dawn))
        if rs is not None:
            glass += rs * (0.5 + 0.5 * mix)
        drops = self.field.frame_drops(t, evap=evap)
        render_drops(glass, sharp, drops)
        frame_a, frame_rgb, lamp = interior_layers()
        fa = frame_a[..., None]
        img = glass * (1 - fa) + frame_rgb * fa
        room_light = 1.0 + 1.6 * dawn
        img = img * np.where(fa > 0.5, room_light, 1.0)
        if self.person:
            m = silhouette_mask()
            br = self.breath[0] + (self.breath[1] - self.breath[0]) * u
            s = 1 + 0.008 * np.sin(2 * np.pi * t / br)
            M = np.float32([[1, 0, 0], [0, s, 1392 * (1 - s)]])
            mm = cv2.warpAffine(m, M, (W, H))
            rim_c = cv2.GaussianBlur(np.clip(mm - np.roll(mm, -5, axis=1), 0, 1), (0, 0), 2.0)
            rim_w = cv2.GaussianBlur(np.clip(mm - np.roll(mm, 7, axis=1), 0, 1), (0, 0), 3.0)
            body = rgb((10, 11, 14)) * (1 + 1.0 * dawn)
            img += lamp * (0.42 * (1 - 0.6 * dawn)) * (1 - 0.9 * mm[..., None])
            img = img * (1 - mm[..., None]) + body * mm[..., None]
            img += rim_c[..., None] * rgb((120, 150, 190)) * (0.55 + 0.6 * dawn)
            img += rim_w[..., None] * rgb((255, 170, 100)) * 0.45 * (1 - 0.5 * dawn)
            img += rim_c[..., None] * rgb((255, 210, 150)) * 0.6 * dawn
        else:
            img += lamp * (0.42 * (1 - 0.6 * dawn))
        if dawn > 0:   # morning shaft across the sill
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            shaft = np.clip(1 - np.abs((xx - 0.55 * (yy - 700) - 620) / 260), 0, 1) ** 2 * (yy > 900)
            img += cv2.GaussianBlur(shaft.astype(np.float32), (0, 0), 30)[..., None] * rgb((255, 214, 150)) * 0.22 * dawn
        # slow push-in
        k = self.push[0] + (self.push[1] - self.push[0]) * ease(u)
        if abs(k - 1) > 1e-3:
            cx, cy = W * 0.45, H * 0.52
            M = np.float32([[k, 0, cx * (1 - k)], [0, k, cy * (1 - k)]])
            img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return img
