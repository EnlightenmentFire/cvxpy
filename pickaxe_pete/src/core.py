"""Rendering core: layout, characters, particles, UI overlay, dialogue box."""
import math
import numpy as np
import gfx as G
from script_data import SPEAKER_COLOR

FPS = 30
UP = 4  # native -> overlay layer scale
PETE = G.pete_frames()
ZOE = G.zoe_frames()
MULE = G.mule_frames()
PAN = G.sprite(["..kkkkkk..", "kxxxxxxxxk", ".kKKKKKKk."])
RACK = G.rack_sprite()


def h01(*a):
    """Deterministic hash -> [0,1)."""
    x = 0
    for v in a:
        x = (x * 1000003) ^ int(v * 7919 + 17)
        x &= 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5BD1E995) & 0xFFFFFFFF
    x ^= x >> 15
    return (x % 100000) / 100000.0


class Layout:
    def __init__(self, vertical):
        self.v = vertical
        if vertical:
            self.W, self.H = 135, 240
            self.ground = 152
            self.box = (6, 160, 123, 40)      # native coords of dialogue box (x,y,w,h)
            self.top_safe = 27
        else:
            self.W, self.H = 240, 135
            self.ground = 100
            self.box = (24, 106, 192, 26)
            self.top_safe = 4

    def P(self, v, h):
        return v if self.v else h


class Ctx:
    """Per-frame context. Time in seconds."""

    def __init__(self, T, t, scene, tl, env, L):
        self.T = T          # global time
        self.t = t          # scene-local time
        self.scene = scene  # scene dict from timeline
        self.tl = tl
        self.env = env
        self.L = L
        self.pops = []      # overlay draws: callables(layer)
        self.shake = (0, 0)
        self.hide_box = False
        self.fade = None

    def ln(self, lid):
        s, e = self.tl["line_index"][lid]
        return s - self.scene["start"], e - self.scene["start"]

    def since(self, lid, which=0):
        return self.t - self.ln(lid)[which]

    def amp(self, spk):
        a = self.env.get(spk)
        if a is None:
            return 0.0
        i = int(self.T * FPS)
        if 0 <= i < len(a):
            return float(a[i])
        return 0.0

    # overlay helpers (positions in native coords; scale in overlay px per glyph pixel)
    def text(self, s, x, y, scale, color, center=True, alpha=1.0, outline=(16, 10, 26), shadow=True):
        def f(layer):
            X, Y = int(x * UP), int(y * UP)
            if center:
                G.draw_text_centered(layer, s, X, Y, scale, color, alpha=alpha, outline=outline, shadow=shadow)
            else:
                G.draw_text(layer, s, X, Y, scale, color, alpha=alpha, outline=outline, shadow=shadow)
        self.pops.append(f)

    def orect(self, x, y, w, h, color, alpha=0.9):
        def f(layer):
            X, Y, Wd, Hd = int(x * UP), int(y * UP), int(w * UP), int(h * UP)
            reg = layer[max(0, Y):Y + Hd, max(0, X):X + Wd].astype(np.float32)
            layer[max(0, Y):Y + Hd, max(0, X):X + Wd] = (reg * (1 - alpha) + np.array(color) * alpha).astype(np.uint8)
        self.pops.append(f)

    def pop_text(self, s, x, y, t0, dur=1.2, scale=6, color=(255, 255, 255), wobble=True, rise=0):
        """Game-style popup that springs in at scene time t0."""
        dt = self.t - t0
        if dt < 0 or dt > dur:
            return
        k = G.ease_out_back(dt / 0.25)
        sc = max(1, int(round(scale * min(1.0, 0.3 + 0.7 * k))))
        yy = y - rise * dt / dur
        if wobble:
            yy += math.sin(dt * 14) * 0.6
        alpha = 1.0 if dt < dur - 0.2 else max(0.0, (dur - dt) / 0.2)
        self.text(s, x, yy, sc, color, alpha=alpha)


# ------------------------------------------------------------------ characters
def mouth_frame(frames, amp, t):
    if amp > 0.38:
        return frames["talk2"]
    if amp > 0.12:
        return frames["talk1"]
    if (t % 3.3) < 0.12:
        return frames["blink"]
    return frames["idle"]


def draw_pete(img, ctx, x, gy, face=1, pose=None, pick=True, pick_angle=None, scale=1, bob=True):
    amp = ctx.amp("PETE")
    if pose == "surprised":
        spr = PETE["surprised"]
    elif pose == "up":
        spr = PETE["up"] if amp < 0.12 else (PETE["talk2"] if amp > 0.38 else PETE["talk1"])
    else:
        spr = mouth_frame(PETE, amp, ctx.T)
    h, w = spr.shape[:2]
    dy = -1 if (bob and amp > 0.3 and int(ctx.T * 10) % 2 == 0) else 0
    if face < 0:
        spr = G.flip(spr)
    cv = G.Canvas(w + 44, h + 48, 22, 30)
    if pick:
        ang = pick_angle
        if ang is None:
            ang = 0 if pose != "up" else 70
        pk = G.rotate_sprite(G.PICKAXE if face > 0 else G.flip(G.PICKAXE), ang * face)
        ph, pw = pk.shape[:2]
        if pose == "up":
            hx = (w - 3 if face > 0 else 2)
            cv.put(pk, hx - pw // 2 - (2 if face > 0 else -2), 6 - ph + 6 + dy)
        else:
            hx = (w - 2 if face > 0 else 1)
            cv.put(pk, hx - (2 if face > 0 else pw - 2), 21 - ph + 3 + dy)
    cv.put(spr, 0, dy)
    cv.blit_to(img, x, gy - h * scale, scale)
    return x, gy - h * scale, w * scale, h * scale


def draw_zoe(img, ctx, x, gy, face=-1, pose=None, scale=1):
    amp = ctx.amp("ZOE")
    spr = ZOE["smile"] if (pose == "smile" and amp < 0.12) else mouth_frame(ZOE, amp, ctx.T + 1.3)
    h, w = spr.shape[:2]
    if face < 0:
        spr = G.flip(spr)
    dy = -1 if (amp > 0.3 and int(ctx.T * 8) % 2 == 0) else 0
    G.blit(img, spr, x, gy - h * scale + dy * scale, scale)
    return x, gy - h * scale, w * scale, h * scale


def draw_mule(img, ctx, x, gy, face=1, mood="idle", faint=0.0, scale=1):
    if mood == "sad":
        spr = MULE["sad"]
    elif mood == "hee":
        spr = MULE["hee"]
    else:
        spr = MULE["blink"] if (ctx.T % 4.1) < 0.12 else MULE["idle"]
    if face < 0:
        spr = G.flip(spr)
    h, w = spr.shape[:2]
    if faint > 0:
        r = G.rotate_sprite(spr, -90 * G.ease(faint) * face)
        h2, w2 = r.shape[:2]
        G.blit(img, r, x + ((w - w2) // 2 + int(6 * faint)) * scale, gy - h2 * scale, scale)
        if faint >= 1:
            ex = x + ((w - w2) // 2 + int(6 * faint) + (w2 - 7 if face > 0 else 4)) * scale
            ey = gy - 8 * scale
            for i in range(3):
                a = ctx.T * 5 + i * 2.1
                G.blit(img, G.SPARKLE[1], ex + math.cos(a) * 6 * scale, ey - 8 * scale + math.sin(a) * 2 * scale)
        return
    G.blit(img, spr, x, gy - h * scale, scale)


def draw_riggy(img, ctx, x, gy, scale=1, heat=0.0, dance=0.0, eyes="normal", led_rate=1.0, extra=0):
    """Giant server rack with an LED face. x,gy = left, ground."""
    amp = ctx.amp("RIGGY")
    T = ctx.T
    W, H = 34, 56 + extra
    bounce = 0
    tilt = 0
    if dance > 0:
        bounce = int(abs(math.sin(T * 9)) * 4 * dance)
        tilt = int(math.sin(T * 9) * 2 * dance)
    elif amp > 0.25:
        bounce = 1 if int(T * 12) % 2 == 0 else 0
    spr = np.zeros((H, W, 4), np.uint8)
    spr[..., 3] = 255
    base = np.array([62, 66, 86], np.float32)
    hot = np.array([150, 60, 70], np.float32)
    body = (base * (1 - heat) + hot * heat).astype(np.uint8)
    spr[..., :3] = body
    spr[0:2, :, :3] = (96, 102, 128)
    spr[:, 0:2, :3] = (40, 42, 58)
    spr[:, -2:, :3] = (40, 42, 58)
    # face screen
    spr[4:20, 4:30, :3] = (12, 8, 20)
    spr[3, 4:30, :3] = (120, 126, 150)
    # eyes
    ec = (255, 70, 220) if amp > 0.05 or dance > 0 else (220, 60, 200)
    if heat > 0.6:
        ec = (255, 120, 80)
    def px(yy, xx, c):
        if 0 <= yy < H and 0 <= xx < W:
            spr[yy, xx, :3] = c
    blink = (T % 3.7) < 0.1
    if eyes == "happy" or dance > 0:
        for (ex) in (9, 21):
            px(9, ex, ec); px(8, ex + 1, ec); px(8, ex + 2, ec); px(9, ex + 3, ec)
    elif eyes == "x":
        for ex in (9, 21):
            for d in range(4):
                px(7 + d, ex + d, ec); px(10 - d, ex + d, ec)
    elif blink:
        spr[9, 9:13, :3] = ec
        spr[9, 21:25, :3] = ec
    else:
        spr[7:11, 9:13, :3] = ec
        spr[7:11, 21:25, :3] = ec
        spr[7:9, 10:12, :3] = (255, 220, 250)
        spr[7:9, 22:24, :3] = (255, 220, 250)
    # mouth: LED equalizer
    mc = np.array((60, 232, 255), np.uint8)
    for i in range(10):
        hh = 1 + int(amp * 5 * (0.5 + 0.5 * math.sin(i * 1.7 + T * 31)))
        if dance > 0:
            hh = 1 + int(2 * (0.5 + 0.5 * math.sin(i * 0.9 + T * 12)))
        x0 = 11 + i * 1
        spr[16 - hh // 2:16 + (hh + 1) // 2, x0, :3] = mc if amp > 0.04 or dance > 0 else (40, 120, 140)
    # body panels with blinking LEDs
    for r in range((H - 26) // 5):
        y0 = 23 + r * 5
        spr[y0:y0 + 4, 4:30, :3] = (40, 44, 60)
        spr[y0 + 1:y0 + 3, 20:29, :3] = (26, 28, 40)
        for k in range(6):
            on = h01(r, k, int(T * 8 * led_rate + h01(k, r) * 5)) > 0.45
            c = [(80, 255, 120), (255, 190, 40), (60, 232, 255)][(r + k) % 3]
            if heat > 0.6:
                c = (255, 80, 60)
            spr[y0 + 1, 6 + k * 2, :3] = c if on else (30, 40, 40)
            spr[y0 + 2, 6 + k * 2, :3] = (30, 30, 40)
    # vents
    for yy in range(23, H - 4, 2):
        spr[yy, 31:32, :3] = (30, 30, 40)
    # feet
    feet = np.zeros((3, W, 4), np.uint8)
    feet[:, 3:9] = (30, 30, 36, 255)
    feet[:, 25:31] = (30, 30, 36, 255)
    full = np.concatenate([spr, feet], 0)
    full = G.add_outline(full)
    if tilt:
        full = G.rotate_sprite(full, tilt * 2)
    fh, fw = full.shape[:2]
    G.blit(img, full, x, gy - fh * scale - bounce * scale, scale)
    # sweat drops + steam when hot
    if heat > 0.3:
        for i in range(int(8 * heat)):
            ph = (T * 1.2 + h01(i, 3)) % 1.0
            dx = x + (3 + h01(i, 1) * (W - 4)) * scale
            dy = gy - (fh - 6 - ph * 30) * scale
            G.rect(img, dx, dy, scale, 2 * scale, (120, 200, 255))
        steam(img, T, x + W * scale // 2, gy - fh * scale - 2, n=int(12 * heat), spread=W * 0.6 * scale, height=30 * scale)
    return x, gy - fh * scale, fw * scale, fh * scale


def steam(img, T, cx, y, n=8, spread=20, height=30, col=(220, 220, 230), speed=1.0):
    for i in range(n):
        p = 1.2 + h01(i, 9)
        ph = ((T * speed + h01(i, 2) * p) % p) / p
        px = cx + (h01(i, 5) - 0.5) * spread + math.sin(T * 2 + i) * 3 * ph
        py = y - ph * height
        r = 1 + ph * 3
        a = 0.75 * (1 - ph)
        G.circle(img, px, py, r, col, a)


def coins_rain(img, T, t0, W, H, n=40, until=None):
    dt = T - t0
    if dt < 0 or (until is not None and T > until):
        return
    for i in range(n):
        delay = h01(i, 1) * 1.2
        d = dt - delay
        if d < 0:
            continue
        x = h01(i, 2) * W
        y = -8 + d * (60 + 50 * h01(i, 3)) + 0.5 * 80 * d * d
        if y > H + 8:
            continue
        f = G.COIN_FRAMES[int((T * 12 + i) % 4)]
        G.blit(img, f, x, y)


def sparkles(img, T, cx, cy, r, n=6, seed=0):
    for i in range(n):
        ph = (T * 1.5 + h01(i, seed)) % 1.0
        if ph > 0.5:
            continue
        a = h01(i, seed + 1) * 6.28
        rr = r * h01(i, seed + 2)
        G.blit(img, G.SPARKLE[0 if ph < 0.25 else 1], cx + math.cos(a) * rr - 2, cy + math.sin(a) * rr - 2)


def stars_bg(img, T, n=60, seed=0, ymax=None):
    H, W = img.shape[:2]
    ymax = ymax or H
    for i in range(n):
        x = int(h01(i, seed) * W)
        y = int(h01(i, seed + 7) * ymax)
        tw = (T * (1 + h01(i, 3) * 2) + h01(i, 4) * 3) % 3
        c = (255, 255, 255) if tw < 0.3 else (150, 150, 200)
        img[y, x] = c


# ------------------------------------------------------------------ overlay: dialogue box + banners
def split_pages(text, maxw, scale, max_lines):
    import re
    lines = G.wrap(text, maxw, scale)
    if len(lines) <= max_lines:
        return [lines]
    # split at sentence boundaries
    sents = re.split(r"(?<=[.!?])\s+", text)
    pages, cur = [], ""
    for s in sents:
        t = (cur + " " + s).strip()
        if len(G.wrap(t, maxw, scale)) <= max_lines or not cur:
            cur = t
        else:
            pages.append(cur)
            cur = s
    if cur:
        pages.append(cur)
    out = []
    for p in pages:
        ls = G.wrap(p, maxw, scale)
        while len(ls) > max_lines:
            out.append(ls[:max_lines])
            ls = ls[max_lines:]
        out.append(ls)
    return out


def draw_dialogue(layer, L, line, T):
    """line: dict with speaker, text, start, end. Draw RPG-style box on overlay layer."""
    spk = line["speaker"]
    col = SPEAKER_COLOR[spk]
    bx, by, bw, bh = [v * UP for v in L.box]
    scale = 3
    pad = 12
    maxw = bw - pad * 2
    max_lines = 3 if L.v else 2
    pages = split_pages(line["text"], maxw, scale, max_lines)
    dur = line["end"] - line["start"]
    n_chars = [sum(len(l) for l in p) for p in pages]
    tot = sum(n_chars)
    # page timing proportional to chars
    t = T - line["start"]
    acc = 0.0
    pi = len(pages) - 1
    page_t0 = 0.0
    for i, nc in enumerate(n_chars):
        span = dur * nc / tot
        if t < acc + span or i == len(pages) - 1:
            pi = i
            page_t0 = acc
            page_span = span
            break
        acc += span
    page = pages[pi]
    lt = t - page_t0
    reveal_time = min(0.45, page_span * 0.35)
    nshow = int(sum(len(l) for l in page) * G.clamp(lt / max(0.01, reveal_time)) + 0.999)
    # box appear anim
    k = G.clamp((T - line["start"] + 0.12) / 0.12)
    # box body
    reg = layer[by:by + bh, bx:bx + bw].astype(np.float32)
    reg = reg * 0.1 + np.array((14, 12, 34), np.float32) * 0.9
    layer[by:by + bh, bx:bx + bw] = reg.astype(np.uint8)
    b = 3
    for (x, y, w, h, c) in [
        (bx, by, bw, b, (255, 255, 255)), (bx, by + bh - b, bw, b, (255, 255, 255)),
        (bx, by, b, bh, (255, 255, 255)), (bx + bw - b, by, b, bh, (255, 255, 255)),
        (bx + b, by + b, bw - 2 * b, b, col), (bx + b, by + bh - 2 * b, bw - 2 * b, b, col),
        (bx + b, by + b, b, bh - 2 * b, col), (bx + bw - 2 * b, by + b, b, bh - 2 * b, col),
    ]:
        layer[y:y + h, x:x + w] = c
    # name tag
    tag = spk
    tw = G.text_width(tag, 3) + 18
    tx, ty = bx + 12, by - 30
    layer[ty:ty + 30, tx:tx + tw] = col
    layer[ty + 3:ty + 30, tx + 3:tx + tw - 3] = (14, 12, 34)
    G.draw_text(layer, tag, tx + 9, ty + 6, 3, col, shadow=False)
    # text
    y = by + pad + 2
    shown = 0
    lh = 9 * scale + 6 if L.v else 9 * scale + 3
    if not L.v:
        y = by + 8
    for ln in page:
        s = ln[:max(0, nshow - shown)]
        shown += len(ln)
        if s:
            G.draw_text(layer, s, bx + pad, y, scale, col)
        y += lh
    # "next" arrow blink when done
    if nshow >= sum(len(l) for l in page) and int(T * 3) % 2 == 0 and pi < len(pages) - 1:
        G.draw_text(layer, ">", bx + bw - 24, by + bh - 34, 3, (255, 255, 255), shadow=False)


def banner(ctx, text, t0=0.15, dur=2.0, color=(255, 230, 90)):
    """Stage title banner that slides in under the top safe zone."""
    dt = ctx.t - t0
    if dt < 0 or dt > dur:
        return
    L = ctx.L
    k = G.ease(dt / 0.3) if dt < dur - 0.3 else G.ease((dur - dt) / 0.3)
    y = L.top_safe + 3 if L.v else 4
    def f(layer, k=k, y=y):
        W = layer.shape[1]
        h = 44
        Y = int(y * UP)
        w = int(W * k)
        x0 = (W - w) // 2
        reg = layer[Y:Y + h, x0:x0 + w].astype(np.float32)
        layer[Y:Y + h, x0:x0 + w] = (reg * 0.25 + np.array((20, 10, 40)) * 0.75).astype(np.uint8)
        layer[Y:Y + 3, x0:x0 + w] = color
        layer[Y + h - 3:Y + h, x0:x0 + w] = color
        if k > 0.95:
            G.draw_text_centered(layer, text, W // 2, Y + 9, 3, color, shadow=False)
    ctx.pops.append(f)


def tip(ctx, text, t0, dur, y=None, color=(120, 255, 140)):
    """Tutorial 'TIP' card (fact callout)."""
    dt = ctx.t - t0
    if dt < 0 or dt > dur:
        return
    L = ctx.L
    yy = y if y is not None else (L.top_safe + 16 if L.v else 18)
    k = G.ease_out_back(dt / 0.3)
    alpha = 1.0 if dt < dur - 0.25 else max(0, (dur - dt) / 0.25)
    def f(layer):
        W = layer.shape[1]
        lines = G.wrap(text, W - 80, 3)
        h = len(lines) * 30 + 18
        Y = int(yy * UP)
        w = int(max(G.text_width(l, 3) for l in lines) + 36)
        sc = max(0.05, min(1.0, k))
        ww = int(w * sc)
        x0 = (W - ww) // 2
        if ww < 10:
            return
        reg = layer[Y:Y + h, x0:x0 + ww].astype(np.float32)
        layer[Y:Y + h, x0:x0 + ww] = (reg * (1 - 0.85 * alpha) + np.array((10, 40, 24)) * 0.85 * alpha).astype(np.uint8)
        for (x, y_, w_, h_) in [(x0, Y, ww, 3), (x0, Y + h - 3, ww, 3), (x0, Y, 3, h), (x0 + ww - 3, Y, 3, h)]:
            layer[y_:y_ + h_, x:x + w_] = color
        if sc > 0.95:
            for i, l in enumerate(lines):
                G.draw_text_centered(layer, l, W // 2, Y + 10 + i * 30, 3, color, alpha=alpha, shadow=False)
    ctx.pops.append(f)
