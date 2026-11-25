"""The eight scenes. Each draw(img, ctx) paints native-res world + queues overlay pops.
All animation is a pure function of time so frames can render in parallel."""
import math
import numpy as np
import gfx as G
from core import (draw_pete, draw_zoe, draw_mule, draw_riggy, steam, coins_rain, sparkles, stars_bg, banner, tip,
                  h01, PAN, RACK, UP)

_BG = {}


def cached(key, fn):
    if key not in _BG:
        _BG[key] = fn()
    return _BG[key].copy()


GOLD = (255, 200, 40)
CYAN = (60, 232, 255)
MAG = (255, 70, 220)
WHITE = (255, 255, 255)
RED = (255, 70, 70)
GREEN = (120, 255, 140)


def shake(ctx, t0, dur=0.4, amt=3):
    dt = ctx.t - t0
    if 0 <= dt < dur:
        a = amt * (1 - dt / dur)
        ctx.shake = (int(round(math.sin(dt * 90) * a)), int(round(math.cos(dt * 70) * a)))


# =============================================================== SCENE 1 — 1849 desert
def bg_desert(L):
    W, H = L.W, L.H
    img = G.dither_gradient(H, W, [(0, (70, 150, 230)), (0.35, (130, 195, 240)), (0.55, (250, 220, 160)), (1, (250, 220, 160))])
    hz = L.ground - L.P(52, 38)
    # sun
    G.circle(img, W * 0.78, hz - L.P(60, 40), 10, (255, 240, 170))
    G.circle(img, W * 0.78, hz - L.P(60, 40), 8, (255, 250, 210))
    # mesas (two layers)
    for layer, (col, base, amp, seed) in enumerate([((214, 120, 80), hz, 22, 1), ((178, 86, 60), hz + 6, 14, 2)]):
        x = 0
        while x < W:
            w = 18 + int(h01(x, seed) * 30)
            hh = int(6 + h01(x, seed + 1) * amp)
            if h01(x, seed + 3) > 0.35:
                G.rect(img, x, base - hh, w, hh + 2, col)
                G.rect(img, x, base - hh, w, 2, tuple(min(255, c + 30) for c in col))
                G.rect(img, x - 3, base - hh // 2, 3, hh // 2 + 2, col)
                G.rect(img, x + w, base - hh // 3, 4, hh // 3 + 2, col)
            x += w + int(h01(x, seed + 4) * 12)
    # sand
    G.rect(img, 0, hz + 2, W, H - hz, (232, 190, 120))
    for i in range(int(W * H / 60)):
        x, y = int(h01(i, 11) * W), int(hz + 4 + h01(i, 12) * (H - hz))
        if y < H:
            img[y, x] = (210, 165, 100)
    # river band
    ry = L.ground + 2
    G.rect(img, 0, ry, W, L.P(16, 12), (60, 120, 200))
    G.rect(img, 0, ry, W, 2, (110, 170, 230))
    G.rect(img, 0, ry + L.P(16, 12), W, 2, (190, 150, 90))
    # cacti
    for cx in [L.P(118, 210), L.P(4, 12)]:
        cy = hz + L.P(30, 18)
        G.rect(img, cx, cy - 16, 4, 16, (60, 150, 70))
        G.rect(img, cx - 4, cy - 11, 4, 2, (60, 150, 70)); G.rect(img, cx - 4, cy - 15, 2, 5, (60, 150, 70))
        G.rect(img, cx + 4, cy - 8, 4, 2, (60, 150, 70)); G.rect(img, cx + 6, cy - 13, 2, 6, (60, 150, 70))
        G.rect(img, cx + 1, cy - 16, 1, 16, (90, 190, 100))
    return img


def bird(img, x, y, T, i):
    flap = int(T * 6 + i) % 2
    c = (40, 30, 40)
    G.safe_px(img, x, y, c)
    for d in (1, 2):
        G.safe_px(img, x - d, y - (d if flap else 0), c)
        G.safe_px(img, x + d, y - (d if flap else 0), c)


def scene1(img, ctx):
    L = ctx.L
    t = ctx.t
    S = 2
    img[:] = cached(("desert", L.v), lambda: bg_desert(L))
    W, H, gy = L.W, L.H, L.ground
    T = ctx.T
    # animated river shimmer
    ry = gy + 2
    for i in range(14):
        x = (h01(i, 1) * W + T * 12 * (0.5 + h01(i, 2))) % W
        y = ry + 3 + int(h01(i, 3) * L.P(11, 8))
        G.rect(img, x, y, 3, 1, (170, 210, 250))
    # vultures circling, waiting for something to happen
    for i in range(2):
        a = T * (0.8 + 0.3 * i) + i * 3
        bird(img, W * (0.3 + 0.4 * i) + math.cos(a) * 14, L.P(62, 30) + math.sin(a) * 4, T, i)
    # tumbleweed rolling in the far back
    tw_x = (T * 18) % (W + 40) - 20
    G.circle(img, tw_x, gy - L.P(34, 26), 3, (170, 130, 80))
    G.circle(img, tw_x, gy - L.P(34, 26), 2, (200, 160, 100))
    l0, l1 = ctx.ln("s1_pete")
    px = L.P(34, 74)
    mx = L.P(-22, 8)
    cart_x = L.P(86, 168)
    # rails
    G.rect(img, cart_x - 16, gy - 1, 80, 2, (90, 60, 40))
    for k in range(9):
        G.rect(img, cart_x - 14 + k * 9, gy - 2, 3, 4, (110, 70, 40))
    banner(ctx, "STAGE 1: THE YEAR 1849", 0.1, 2.3)
    ctx.text("GOLD: 0", L.P(4, 4), L.P(L.top_safe + 15, 16), 3, GOLD, center=False)
    portal_t = l1 + 0.2
    jump_t = portal_t + 0.4
    glow = 0.0
    ccx, ccy = cart_x + 12 * S, gy - 6 * S
    if t > portal_t:
        glow = 0.5 + 0.5 * math.sin((t - portal_t) * 16)
        G.circle(img, ccx, ccy, 26 + 6 * glow, (255, 240, 140), 0.35)
    cart_tint = (255, 255, 160, 0.5 * glow) if glow else None
    if t < jump_t:
        G.blit(img, G.MINECART, cart_x, gy - 12 * S, S, tint=cart_tint)
    if t > portal_t:
        sparkles(img, T, ccx, ccy, 26, 10, 3)
    pan_kick = 1.5
    if t < jump_t:
        mood = "sad" if (1.9 < t < 3.0) or (l0 + 3.4 < t < l1 + 0.3) else "idle"
        draw_mule(img, ctx, mx, gy, 1, mood, scale=S)
        if 1.9 < t < 3.2:
            k = (t - 1.9) / 1.3
            G.circle(img, mx + 54 + k * 8, gy - 30 - k * 10, 3 + k * 5, (240, 240, 250), 0.8 * (1 - k))
            ctx.pop_text("sigh...", mx + 50, gy - 58, 1.95, 1.2, 3, (230, 230, 240))
        if l0 + 3.4 < t < l1 + 0.3:
            cx = mx + 46
            cy = gy - L.P(68, 64)
            for dx, r in [(-7, 5), (0, 7), (7, 5)]:
                G.circle(img, cx + dx, cy, r, (120, 125, 140))
            for i in range(8):
                ph = (T * 2.5 + h01(i, 7)) % 1
                G.rect(img, cx - 9 + i * 2.5, cy + 5 + ph * 18, 1, 3, (120, 170, 240))
        if t < pan_kick:
            wob = int(math.sin(t * 18) * 1.5)
            draw_pete(img, ctx, px, gy, 1, pick=False, scale=S)
            G.blit(img, PAN, px + 15 * S + wob, gy - 15 * S, S)
            if 0.6 < t < 1.3:
                sparkles(img, T, px + 21 * S, gy - 15 * S, 5, 2, 9)
                ctx.pop_text("+0 GOLD", px + 22, gy - 84, 0.75, 0.8, 4, GOLD)
        else:
            draw_pete(img, ctx, px, gy, 1, pick=True, pose="surprised" if t < pan_kick + 0.4 else None, scale=S)
            k = t - pan_kick
            if k < 1.2:
                pxp = px + 36 + k * 110
                pyp = gy - 30 - 90 * k + 100 * k * k
                G.blit(img, G.rotate_sprite(PAN, k * 720), pxp, pyp, S)
            ctx.pop_text("CLANG!", px + 50, gy - 88, pan_kick + 0.05, 0.6, 5, WHITE)
    else:
        k = G.clamp((t - jump_t) / 0.55)
        if k < 1:
            G.blit(img, G.MINECART, cart_x, gy - 12 * S, S, tint=cart_tint)
            sx = px + (cart_x + 4 - px) * k
            sy = gy - math.sin(k * math.pi) * 40 - 20 * k
            sp = G.rotate_sprite(ctx_pete_frame(ctx), -k * 360)
            G.blit(img, sp, sx, sy - sp.shape[0] * S, S)
            kk = G.clamp(k * 1.1)
            mxk = mx + (cart_x + 20 - mx) * kk
            m = G.rotate_sprite(G.mule_frames_cache()["idle"], -k * 300)
            G.blit(img, m, mxk, gy - math.sin(kk * math.pi) * 34 - m.shape[0] * S - 16 * k, S)
        else:
            # heads poking out of the cart
            G.blit(img, ctx_pete_frame(ctx)[:13], cart_x + 2 * S, gy - 22 * S, S)
            G.blit(img, G.mule_frames_cache()["idle"][:11, 14:], cart_x + 10 * S, gy - 21 * S, S)
            G.blit(img, G.MINECART, cart_x, gy - 12 * S, S, tint=cart_tint)
    p_t = jump_t + 0.45
    if t > p_t:
        k = t - p_t
        R = 6 + k * 140
        cols = [(255, 70, 220), (60, 232, 255), (255, 230, 90), (120, 80, 255)]
        for r in range(int(R), 0, -5):
            c = cols[int(r / 5 + k * 20) % 4]
            G.ring(img, ccx + math.sin(k * 6 + r * 0.2) * 3, ccy + math.cos(k * 6 + r * 0.2) * 3, max(0, r - 5), r, c)
        ctx.pop_text("WARP!", W / 2, L.P(70, 30), p_t + 0.1, 1.2, 10, WHITE)
        ctx.fade = ("white", G.clamp((k - 0.75) / 0.45))


def ctx_pete_frame(ctx):
    from core import PETE
    return PETE["surprised"]


def _mfc():
    from core import MULE
    return MULE


G.mule_frames_cache = _mfc


# =============================================================== SCENE 2/6 — warehouse
def bg_warehouse(L):
    W, H = L.W, L.H
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (18, 20, 34)
    gy = L.ground
    # back wall panels
    for x in range(0, W, 16):
        G.rect(img, x, 0, 1, gy, (26, 28, 46))
    # ceiling lights
    for x in range(10, W, 40):
        G.rect(img, x, L.P(18, 4), 14, 2, (200, 220, 255))
        for k in range(1, 40):
            a = 0.08 * (1 - k / 40)
            G.rect(img, x - k // 3, L.P(20, 6) + k, 14 + 2 * (k // 3), 1, (120, 140, 200), a)
    # rows of racks on back wall (two tiers)
    for tier, (yb, hh) in enumerate([(gy - L.P(62, 44), L.P(26, 20)), (gy - L.P(30, 22), L.P(24, 18))]):
        for x in range(2 - tier * 6, W, 12):
            G.rect(img, x, yb - hh, 10, hh, (34, 38, 56))
            G.rect(img, x, yb - hh, 10, 1, (60, 66, 90))
            for r in range(2, hh - 1, 3):
                G.rect(img, x + 1, yb - hh + r, 8, 2, (26, 28, 42))
    # floor
    G.rect(img, 0, gy, W, H - gy, (40, 44, 64))
    for y in range(gy, H, 6):
        G.rect(img, 0, y, W, 1, (50, 56, 80))
    for x in range(0, W, 14):
        G.rect(img, x, gy, 1, H - gy, (50, 56, 80))
    # cables
    for k in range(3):
        y = gy + 4 + k * 3
        for x in range(W):
            yy = int(y + math.sin(x * 0.15 + k) * 1.2)
            if 0 <= yy < H:
                img[yy, x] = [(20, 20, 30), (90, 30, 40), (30, 60, 110)][k]
    return img


def warehouse_live(img, ctx, L, rate=1.0):
    """Blinking LEDs on the back racks + steam vents."""
    T = ctx.T
    W = L.W
    gy = L.ground
    for tier, (yb, hh) in enumerate([(gy - L.P(62, 44), L.P(26, 20)), (gy - L.P(30, 22), L.P(24, 18))]):
        for xi, x in enumerate(range(2 - tier * 6, W, 12)):
            for r in range(2, hh - 1, 3):
                for k in range(3):
                    on = h01(xi, r, k, tier, int(T * 6 * rate + h01(xi, r) * 9)) > 0.5
                    xx = x + 2 + k * 2
                    if on and 0 <= xx < W:
                        c = [(80, 255, 120), (255, 190, 40), (60, 232, 255)][(k + r) % 3]
                        img[yb - hh + r, xx] = c
    steam(img, T, L.P(20, 30), gy - L.P(62, 44) - L.P(26, 20), 6, 10, 20)
    steam(img, T + 0.7, L.P(110, 200), gy - L.P(62, 44) - L.P(26, 20), 6, 10, 20)


def desk(img, x, gy, T):
    G.rect(img, x, gy - 14, 26, 3, (110, 70, 44))
    G.rect(img, x + 2, gy - 11, 2, 11, (80, 50, 30))
    G.rect(img, x + 22, gy - 11, 2, 11, (80, 50, 30))
    # laptop
    G.rect(img, x + 6, gy - 24, 13, 9, (40, 44, 60))
    G.rect(img, x + 7, gy - 23, 11, 7, (40, 120, 160))
    for i in range(3):
        if h01(i, int(T * 4)) > 0.4:
            G.rect(img, x + 8, gy - 22 + i * 2, 4 + int(h01(i, int(T * 4), 2) * 6), 1, (180, 240, 255))
    G.rect(img, x + 4, gy - 15, 17, 1, (90, 94, 110))
    # energy drink can
    G.rect(img, x + 21, gy - 19, 3, 5, (120, 230, 60))
    G.rect(img, x + 21, gy - 19, 3, 1, (200, 200, 210))


def riggy_place(L):
    """Giant Riggy: 2x in vertical, extra-tall in horizontal. Returns (x, ground, scale, extra, center_x, top_y)."""
    if L.v:
        rs, ex = 2, 0
        rx, rgy = 31, 146
        return rx, rgy, rs, ex, rx + 18 * rs, rgy - 59 * rs
    rs, ex = 1, 22
    rx, rgy = 112, L.ground - 2
    return rx, rgy, rs, ex, rx + 18, rgy - 81


def scene2(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    img[:] = cached(("wh", L.v), lambda: bg_warehouse(L))
    warehouse_live(img, ctx, L)
    gy = L.ground
    banner(ctx, "STAGE 2: THE 'MINE'", 0.2, 2.2)
    p1 = ctx.ln("s2_pete1")
    z1 = ctx.ln("s2_zoe1")
    r1 = ctx.ln("s2_riggy1")
    p2 = ctx.ln("s2_pete2")
    z2 = ctx.ln("s2_zoe2")
    px = L.P(16, 44)
    mx = L.P(-6, 6)
    zx = L.P(108, 188)
    rx, rgy, rs, ex, rcx, rtop = riggy_place(L)
    eyes = "happy" if r1[0] < t < r1[1] + 0.3 else "normal"
    if z1[0] < t < r1[0]:
        eyes = "x"
    if r1[0] - 0.1 < t < r1[1] + 0.3:
        for i in range(5):
            c = [(255, 70, 220), (60, 232, 255), (255, 230, 90), (120, 255, 140), (255, 120, 60)][(i + int(T * 8)) % 5]
            x0 = rcx + (i - 2) * 26
            for k in range(0, rgy - 20, 2):
                G.rect(img, x0 + (k * (i - 2)) // 5, 20 + k, 3, 2, c, 0.22)
        ctx.pop_text("PLAYER 2 JOINED!", L.W / 2, L.P(100, 12), r1[0] + 0.2, r1[1] - r1[0] + 0.2, 4, MAG)
    draw_riggy(img, ctx, rx, rgy, scale=rs, extra=ex, eyes=eyes, dance=0.6 if r1[0] < t < r1[1] else 0)
    # Zoe at her desk facing her laptop (not looking up), turns only to explain
    zface = 1 if t < z2[0] - 0.2 else -1
    desk(img, zx + (4 if L.v else 12), gy, T)
    draw_zoe(img, ctx, zx, gy, face=zface)
    land = 0.75
    if t < land:
        k = t / land
        yy = -40 + (gy + 40) * k * k
        G.blit(img, G.MINECART, px + 4, yy - 12)
        G.blit(img, ctx_pete_frame(ctx)[:12], px + 6, yy - 22)
        ctx.fade = ("white", 1 - G.clamp(t / 0.35))
        return
    shake(ctx, land, 0.45, 3)
    dk = t - land
    if dk < 0.8:
        for i in range(12):
            a = h01(i, 4) * math.pi
            r = dk * 44 * (0.5 + h01(i, 5))
            G.circle(img, px + 14 + math.cos(a) * r, gy - 3 - math.sin(a) * r * 0.4, 3 * (1 - dk), (150, 140, 130), 0.8)
    ctx.pop_text("THUD!", px + 20, gy - 56, land, 0.6, 5, WHITE)
    G.blit(img, G.rotate_sprite(G.MINECART, 12), px - L.P(6, 30) + (0 if not L.v else 0), gy - 14) if not L.v else None
    mood = "hee" if land + 0.15 < t < land + 0.9 else "idle"
    draw_mule(img, ctx, mx, gy, 1, mood)
    pose = None
    ang = None
    if p1[0] - 0.2 < t < z1[1]:
        pose = "up"
        ang = 70 + 15 * math.sin(T * 10) if t < p1[1] else 70
    if r1[0] < t < r1[1] + 0.4:
        pose = "surprised"
    face = 1
    if p2[0] - 0.9 < t < p2[0]:
        face = 1 if int((t - p2[0]) * 3) % 2 == 0 else -1
    draw_pete(img, ctx, px, gy, face, pose=pose, pick_angle=ang)
    if p1[0] < t < p1[1]:
        ctx.pop_text("GOLD?!", px + 16, gy - 60, p1[0] + 0.1, 1.0, 4, GOLD)
    if z1[0] < t < z1[1] + 0.3:
        ctx.pop_text("DON'T!", rcx, rtop - 8, z1[0] + 0.15, 0.9, 4, CYAN)
    tw0 = p2[0] - 0.85
    if tw0 < t < p2[1] + 0.8:
        k = (t - tw0) / 1.6
        x = -10 + k * (L.W + 20)
        r = 4
        bounce = abs(math.sin(k * 12)) * 4
        for a in range(0, 360, 45):
            aa = math.radians(a + T * 500)
            G.rect(img, x + math.cos(aa) * r, gy - r - 1 - bounce + math.sin(aa) * r, 2, 2, (170, 130, 80))
        G.circle(img, x, gy - r - 1 - bounce, 2, (200, 160, 100))
    if p2[0] < t < p2[1] + 0.4:
        ctx.pop_text("?", px + 14, gy - 52, p2[0], p2[1] - p2[0] + 0.4, 6, WHITE)
    tip(ctx, "TIP: MINING HERE = GUESSING", z2[0] + 0.9, z2[1] - z2[0] + 0.3, color=CYAN)



# =============================================================== SCENE 3 — the shared notebook
def bg_city(L):
    W, H = L.W, L.H
    img = G.dither_gradient(H, W, [(0, (60, 120, 230)), (0.6, (140, 200, 250)), (1, (200, 230, 255))])
    # clouds
    for i in range(6):
        cx, cy = h01(i, 1) * W, 30 + h01(i, 2) * (H * 0.4)
        for k in range(4):
            G.circle(img, cx + k * 6 - 9, cy + (k % 2) * 2, 5 + (k % 2) * 2, (240, 248, 255))
    # skyline
    base = L.ground + L.P(10, 6)
    x = 0
    i = 0
    while x < W:
        w = 10 + int(h01(i, 3) * 12)
        hh = 18 + int(h01(i, 4) * L.P(50, 40))
        col = [(70, 80, 120), (84, 90, 140), (60, 66, 104)][i % 3]
        G.rect(img, x, base - hh, w, hh + 60, col)
        for wy in range(base - hh + 3, base, 4):
            for wx in range(x + 2, x + w - 2, 3):
                if h01(wx, wy) > 0.45:
                    G.safe_px(img, wx, wy, (255, 230, 120))
        x += w + 1
        i += 1
    G.rect(img, 0, base, W, H - base, (50, 54, 80))
    return img


def notebook(img, ctx, cx, cy, w, h, page_flip=0.0, lines=4, glow=0.0):
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    # shadow + cover
    G.rect(img, x0 - 3, y0 - 2, w + 6, h + 5, (120, 40, 40))
    G.rect(img, x0 - 3, y0 + h + 1, w + 6, 2, (80, 24, 30))
    # pages
    G.rect(img, x0, y0, w // 2 - 1, h, (250, 246, 230))
    G.rect(img, x0 + w // 2 + 1, y0, w // 2 - 1, h, (250, 246, 230))
    G.rect(img, x0 + w // 2 - 1, y0, 2, h, (200, 190, 170))
    for yy in range(y0 + 4, y0 + h - 2, 4):
        G.rect(img, x0 + 2, yy, w // 2 - 5, 1, (190, 210, 240))
        G.rect(img, x0 + w // 2 + 3, yy, w // 2 - 5, 1, (190, 210, 240))
    if glow > 0:
        G.rect(img, x0 - 3, y0 - 2, w + 6, h + 5, (255, 240, 140), 0.3 * glow)
    if page_flip > 0:
        k = G.clamp(page_flip)
        pw = int((w // 2) * abs(math.cos(k * math.pi)))
        if k < 0.5:
            G.rect(img, x0 + w // 2 + 1, y0 - int(4 * math.sin(k * math.pi)), pw, h, (255, 252, 240))
        else:
            G.rect(img, x0 + w // 2 - 1 - pw, y0 - int(4 * math.sin(k * math.pi)), pw, h, (255, 252, 240))


LEDGER = ["Ann paid Bob 3", "Bob paid Cy 1", "Cy paid Dee 2", "Dee paid Ann 5", "Eve paid Cy 4", "Bob paid Eve 2"]


def scene3(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    z1 = ctx.ln("s3_zoe1")
    p1 = ctx.ln("s3_pete1")
    z2 = ctx.ln("s3_zoe2")
    city = cached(("city", L.v), lambda: bg_city(L))
    # camera: starts on the warehouse among buildings, scrolls up to reveal the notebook
    rise = G.ease(t / 1.0)
    off = int((1 - rise) * L.P(60, 40))
    img[:] = np.roll(city, -off, axis=0) if off else city
    if off:
        img[H - off:] = (50, 54, 80)
    banner(ctx, "STAGE 3: THE NOTEBOOK", 0.3, 2.2)
    # floating notebook
    nb_w, nb_h = L.P(104, 120), L.P(70, 50)
    ncx = W / 2
    ncy = L.P(94, 50) + off + math.sin(T * 1.5) * 1.5
    flip_k = 0
    if z2[0] + 1.0 < t < z2[0] + 1.8:
        flip_k = (t - z2[0] - 1.0) / 0.8
    notebook(img, ctx, ncx, ncy, nb_w, nb_h, flip_k, glow=0.0)
    # ledger text drawn on overlay
    nwrite = int(G.clamp((t - z1[0]) / 2.5) * 4) if t > z1[0] else 1
    if t > z2[0] + 1.0:
        nwrite = 0 if t < z2[0] + 1.8 else 1
    page_lines = LEDGER[:4] if t < z2[0] + 1.0 else LEDGER[4:5]
    x0 = int(ncx - nb_w / 2) + 2
    y0 = int(ncy - nb_h / 2) + L.P(3, 3)
    sc = 2 if L.v else 2
    lh = L.P(5, 5)
    for i, s in enumerate(page_lines[:max(1, nwrite)]):
        ctx.text(s, x0 + 1, y0 + i * lh * 2 - 1, sc, (40, 40, 90), center=False, outline=None)
    if t > z2[0] + 1.8:
        ctx.text("NEXT PAGE?", ncx + nb_w / 4, y0 + 2, sc, (180, 40, 60), outline=None)
    ctx.text("WHO PAID WHOM", ncx, int(ncy - nb_h / 2) - L.P(9, 9), 3, WHITE)
    # tiny people on rooftops each holding an identical copy
    n_people = L.P(70, 110)
    flash = (t > z1[0] + 0.8) and (int((t - z1[0]) * 2.5) % 2 == 0) and t < z1[1]
    cheat_i = 17
    for i in range(n_people):
        px = int((i + 0.5) * W / n_people + (h01(i, 1) - 0.5) * 2)
        py = gy + L.P(6, 4) - int(h01(i, 2) * L.P(24, 28)) + off
        if py > H - 2:
            continue
        col = [(255, 200, 150), (200, 140, 100), (150, 100, 70)][i % 3]
        img[py - 2:py, px] = (30, 30, 50)
        img[py - 3, px] = col
        bc = (255, 255, 160) if flash else (245, 245, 235)
        cheat = (i == cheat_i) and (z1[0] + 3.2 < t < z1[1] + 0.2)
        if cheat:
            bc = (255, 60, 60)
        if 0 <= py - 4 < H and px + 1 < W:
            img[py - 4:py - 2, px + 1] = bc
        if cheat:
            ctx.pop_text("DOESN'T MATCH!", px + 4, py - L.P(18, 16), z1[0] + 3.3, 1.8, 3, RED)
            G.ring(img, px + 1, py - 3, 3, 4, RED)
    # copy-lines from the notebook to the crowd (sync)
    if flash:
        for i in range(0, n_people, 7):
            px = int((i + 0.5) * W / n_people)
            py = gy + L.P(6, 4) - int(h01(i, 2) * L.P(24, 28)) + off
            G.line(img, ncx, ncy + nb_h / 2 + 2, px, py - 5, (255, 255, 180))
    tip(ctx, "EVERYONE HAS THE SAME COPY", z1[0] + 1.0, z1[1] - z1[0] - 0.6, y=L.P(132, 64), color=GREEN)
    # foreground roof with Pete, Biscuit, Zoe looking up
    fy = H - L.P(78, 30) + off // 2
    fy = L.P(gy + 8, gy + 4) + off
    G.rect(img, 0, fy, W, 4, (70, 60, 70))
    G.rect(img, 0, fy + 4, W, H, (46, 40, 52))
    if off < 30:
        draw_mule(img, ctx, L.P(-10, 20), fy, 1)
        draw_pete(img, ctx, L.P(14, 52), fy, 1, pick=False)
        draw_zoe(img, ctx, L.P(104, 172), fy, -1)
    # saloon tab gag
    if p1[0] - 0.1 < t < p1[1] + 0.5:
        k = G.ease_out_back((t - p1[0] + 0.1) / 0.3)
        sx = int(L.P(36, 170))
        sy = int(L.P(124, 56) + (1 - k) * 60)
        G.rect(img, sx - 2, sy - 2, 64, 40, (90, 54, 30))
        G.rect(img, sx, sy, 60, 36, (180, 130, 80))
        G.rect(img, sx, sy, 60, 2, (210, 160, 100))
        ctx.text("SALOON TAB", sx + 30, sy + 3, 2, (60, 30, 10), outline=None)
        # tally marks get secretly erased then a stamp
        n = 9 - int(G.clamp((t - p1[0]) / 1.2) * 6)
        for i in range(n):
            G.rect(img, sx + 8 + i * 5, sy + 16, 1, 9, (40, 20, 10))
            if i % 5 == 4:
                G.line(img, sx + 6 + (i - 4) * 5, sy + 24, sx + 8 + i * 5 + 1, sy + 17, (40, 20, 10))
        if t > p1[0] + 1.3:
            ctx.pop_text("NOT HONEST", sx + 30, sy + 26, p1[0] + 1.3, p1[1] - p1[0], 3, RED, wobble=False)
    # giant pen descends on "write the next page"
    if t > z2[0] + 1.6:
        k = G.ease_out_back((t - z2[0] - 1.6) / 0.6)
        pxn = ncx + nb_w / 4
        pyn = ncy - nb_h / 2 - 30 + 24 * k
        for i in range(24):
            G.rect(img, pxn + i * 0.5, pyn + i, 4, 2, (255, 210, 60) if i < 20 else (60, 60, 80))
        ctx.pop_text("WHO WRITES NEXT?", W / 2, L.P(150, 92) + off, z2[0] + 1.7, 3.0, 3, GOLD)


# =============================================================== SCENE 4 — the guessing game
BALL_COLS = [(255, 90, 90), (90, 200, 255), (255, 220, 80), (140, 255, 140), (220, 120, 255), (255, 160, 60)]


def bg_cosmos(L):
    W, H = L.W, L.H
    img = G.dither_gradient(H, W, [(0, (20, 8, 50)), (0.6, (60, 20, 90)), (1, (110, 40, 110))])
    # mountain base
    gy = L.ground
    for x in range(W):
        hh = int(L.P(52, 30) * (1 - abs(x - W / 2) / (W / 2)) ** 0.6) + int(h01(x // 4, 2) * 3)
        G.rect(img, x, gy - hh, 1, hh + H, (70, 50, 90))
        G.rect(img, x, gy - hh, 1, 2, (110, 90, 140))
    G.rect(img, 0, gy, W, H - gy, (40, 28, 60))
    return img


def scene4(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    img[:] = cached(("cosmos", L.v), lambda: bg_cosmos(L))
    stars_bg(img, T, 80, 3, ymax=gy - 20)
    z1 = ctx.ln("s4_zoe1")
    r1 = ctx.ln("s4_riggy1")
    p1 = ctx.ln("s4_pete1")
    z2 = ctx.ln("s4_zoe2")
    r2 = ctx.ln("s4_riggy2")
    banner(ctx, "STAGE 4: THE GUESSING GAME", 0.2, 2.3)
    # machine: glass dome on a base
    cx = W / 2
    cy = L.P(86, 46)
    R = L.P(48, 38)
    G.circle(img, cx, cy, R + 2, (180, 200, 255))
    G.circle(img, cx, cy, R, (30, 20, 60))
    G.circle(img, cx - R * 0.35, cy - R * 0.4, R * 0.25, (80, 70, 140), 0.5)
    jackpot_t = r2[0] - 1.4
    speed = 1.0 + (3.0 if r1[0] < t < p1[0] else 0)
    nb = 420 if L.v else 380
    for i in range(nb):
        a = h01(i, 1) * 6.283 + T * (0.6 + h01(i, 2) * 2) * speed * (1 if i % 2 else -1)
        rr = math.sqrt(h01(i, 3)) * (R - 2)
        bx = cx + math.cos(a) * rr
        by = cy + math.sin(a * 1.3 + i) * rr * 0.9
        c = BALL_COLS[i % len(BALL_COLS)]
        if t > jackpot_t and i != 7:
            c = tuple(int(v * 0.35) for v in c)
        img[int(by), int(bx)] = c
        if i % 9 == 0:
            G.rect(img, bx, by, 2, 2, c)
    # base with lights
    G.rect(img, cx - R * 0.7, cy + R - 4, R * 1.4, 14, (120, 60, 160))
    G.rect(img, cx - R * 0.7, cy + R - 4, R * 1.4, 2, (200, 140, 255))
    for i in range(int(R * 1.4 / 5)):
        on = (i + int(T * 10)) % 3 == 0
        G.rect(img, cx - R * 0.7 + 2 + i * 5, cy + R + 2, 2, 2, (255, 240, 120) if on else (90, 60, 90))
    ctx.text("MAGIC NUMBER MACHINE", cx, cy + R + L.P(13, 12), 2, (255, 230, 255))
    # prize: the pen hovering above
    if z1[0] < t < r1[0]:
        pk = G.ease_out_back((t - z1[0]) / 0.5)
        py = cy - R - 14 + (1 - pk) * -30
        for i in range(20):
            G.rect(img, cx - 10 + i, py + i * 0.3, 3, 3, (255, 210, 60) if i < 16 else (60, 60, 80))
        ctx.text("PRIZE: THE PEN", cx, py - L.P(12, 10), 2, GOLD)
        # icons: skill / trick crossed out
        seg = (z1[1] - z1[0])
        ctx.pop_text("SKILL  X", L.P(36, 40), cy - 8, z1[0] + seg * 0.62, seg * 0.4 + 0.3, 3, RED, wobble=False)
        ctx.pop_text("TRICK  X", L.P(100, 200), cy - 8, z1[0] + seg * 0.75, seg * 0.27 + 0.3, 3, RED, wobble=False)
        ctx.pop_text("JUST GUESSING!", cx, cy + 6, z1[0] + seg * 0.88, seg * 0.14 + 0.5, 3, GREEN, wobble=False)
    # Riggy at bottom right, Pete & Zoe bottom left
    rx = L.P(96, 196)
    dance = 1.0 if t > r2[0] - 0.3 else 0
    draw_riggy(img, ctx, rx, gy + 2, eyes="happy" if t > jackpot_t else "normal", dance=dance, led_rate=4 if r1[0] < t else 1)
    draw_pete(img, ctx, L.P(4, 14), gy + 2, 1, pick=True, pose="surprised" if r1[1] < t < p1[0] else None)
    draw_zoe(img, ctx, L.P(30, 40), gy + 2, 1)
    # guesses-per-second HUD + WRONG storm
    if r1[0] < t < z2[1]:
        ctx.text("GUESSES/SEC:", L.P(4, 4), L.P(L.top_safe + 14, 14), 2, CYAN, center=False)
        ctx.text("100,000,000,000,000", L.P(4, 4), L.P(L.top_safe + 22, 22), 2, WHITE, center=False)
    wrong_a, wrong_b = r1[1] - 0.2, z2[1]
    if wrong_a < t < wrong_b:
        n = int((t - wrong_a) * 30)
        for i in range(min(n, 24)):
            j = n - i
            x = h01(j, 1) * (W - 30) + 15
            y = L.P(40, 20) + h01(j, 2) * (gy - L.P(60, 40))
            a = 1.0 - i / 24
            ctx.text("WRONG", x, y, 2 if i > 3 else 3, RED, alpha=a)
        ctx.text("WRONG x" + str(int((t - wrong_a) * 1e6 * 13 + 1)), cx, cy - 4, 3, RED)
    if p1[0] < t < p1[1]:
        ctx.pop_text("$?", L.P(16, 25), gy - 50, p1[0] + 0.3, 1.2, 3, GOLD) if False else None
    # jackpot
    if t > jackpot_t:
        k = t - jackpot_t
        bx, by = cx + 10, cy + 6
        rr = min(10, 1 + k * 14)
        G.circle(img, bx, by, rr + 3, (255, 255, 200), 0.35)
        G.circle(img, bx, by, rr, (255, 220, 60))
        G.circle(img, bx - rr * 0.3, by - rr * 0.3, rr * 0.35, (255, 255, 220))
        ctx.text("THE ONE!", bx, by - rr - 12, 2, WHITE)
        ctx.pop_text("JACKPOT!", cx, L.P(56, 8), jackpot_t + 0.25, 3.5, 7, GOLD)
        coins_rain(img, T, ctx.scene["start"] + jackpot_t + 0.3, W, H, 50)
    if t > r2[0] + 0.1:
        tip(ctx, "WINNER WRITES THE PAGE + GETS NEW COINS", r2[0] + 0.2, r2[1] - r2[0] + 1.0, y=L.P(L.top_safe + 1, 64), color=GOLD)


# =============================================================== SCENE 5 — everyone joins
def bg_plain(L):
    W, H = L.W, L.H
    img = G.dither_gradient(H, W, [(0, (30, 20, 70)), (0.45, (200, 90, 120)), (0.6, (255, 170, 100)), (1, (255, 170, 100))])
    hz = L.ground - L.P(40, 34)
    G.rect(img, 0, hz, W, H - hz, (90, 60, 80))
    for y in range(hz, H, 3):
        G.rect(img, 0, y, W, 1, (100 + (y - hz), 66, 86))
    return img


def hourglass(img, ctx, x, y, s=1.0, stretch=1.0, label=True):
    T = ctx.T
    w, h = int(16 * s), int(28 * s * stretch)
    G.rect(img, x - 2, y - 2, w + 4, 3, (150, 100, 50))
    G.rect(img, x - 2, y + h - 1, w + 4, 3, (150, 100, 50))
    for yy in range(h):
        k = abs(yy - h / 2) / (h / 2)
        ww = max(1, int(w * (0.12 + 0.88 * k)))
        G.rect(img, x + (w - ww) // 2, y + yy, ww, 1, (190, 220, 255))
    # sand
    for yy in range(h // 2 + 2, h - 1):
        k = abs(yy - h / 2) / (h / 2)
        ww = max(1, int(w * (0.12 + 0.88 * k)) - 2)
        if yy > h - 1 - (h // 2) * 0.6:
            G.rect(img, x + (w - ww) // 2, y + yy, ww, 1, (240, 200, 90))
    for yy in range(2, h // 2 - 4):
        k = abs(yy - h / 2) / (h / 2)
        ww = max(1, int(w * (0.12 + 0.88 * k)) - 2)
        if yy > h // 2 * 0.45:
            G.rect(img, x + (w - ww) // 2, y + yy, ww, 1, (240, 200, 90))
    if int(T * 10) % 2 == 0:
        G.rect(img, x + w // 2, y + h // 2 - 2, 1, h // 2 - 2, (240, 200, 90))
    if label:
        ctx.text("10 MIN", x + w / 2, y + h + 4, 3, WHITE)


def scene5(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    img[:] = cached(("plain", L.v), lambda: bg_plain(L))
    hz = gy - L.P(40, 34)
    p1 = ctx.ln("s5_pete1")
    z1 = ctx.ln("s5_zoe1")
    z2 = ctx.ln("s5_zoe2")
    p2 = ctx.ln("s5_pete2")
    z3 = ctx.ln("s5_zoe3")
    p3 = ctx.ln("s5_pete3")
    banner(ctx, "STAGE 5: EVERYONE JOINS", 0.1, 2.2)
    # rigs pouring in from the horizon: count grows over time
    count = int(min(260, 4 + (t ** 2) * 6))
    transform_t = p1[1] + 0.2
    for i in range(count):
        born = math.sqrt(max(0, (i - 4) / 6))
        age = t - born
        depth = G.clamp(age / 3.5)
        x = (h01(i, 1) * 1.4 - 0.2) * W
        x = W / 2 + (x - W / 2) * (0.3 + depth)
        y = hz + depth * L.P(34, 30)
        if t > transform_t + h01(i, 9) * 1.5 and i % 3 != 0:
            continue
        if depth < 0.35:
            img[int(y) - 1:int(y) + 1, int(x) % W] = (40, 44, 60)
        elif 0 <= x < W:
            sz = depth
            if sz < 0.7:
                G.rect(img, x, y - 4, 3, 4, (50, 54, 76))
                if h01(i, int(T * 6)) > 0.5:
                    G.safe_px(img, x + 1, y - 3, (80, 255, 120))
            else:
                G.blit(img, RACK, x, y - 22)
    # dragons
    if t > transform_t:
        nd = int(min(40, (t - transform_t) * 14))
        for i in range(nd):
            k = (t - transform_t - i * 0.07)
            if k < 0:
                continue
            spd = 18 + h01(i, 3) * 20
            x = W + 10 - ((k * spd + h01(i, 4) * W * 1.5) % (W + 60))
            y = L.P(30, 8) + h01(i, 5) * (hz - L.P(40, 24)) + math.sin(k * 3 + i) * 3
            fr = G.DRAGON[int(T * 6 + i) % 2]
            G.blit(img, fr, x, y)
            if h01(i, int(T * 3)) > 0.85:
                for f in range(6):
                    G.rect(img, x - 3 - f * 2, y + 6 + (f % 2), 2, 2, (255, 150 + f * 15, 40))
        # flash at transform moment
        fk = t - transform_t
        if fk < 0.25:
            img[:] = (img * (1 - (0.25 - fk) * 3) + 255 * (0.25 - fk) * 3).clip(0, 255).astype(np.uint8)
        ctx.pop_text("RAWR!", W * 0.6, L.P(60, 30), transform_t + 0.1, 1.0, 6, (255, 140, 60))
    # difficulty target: shrinking bullseye
    tx, ty = L.P(30, 46), L.P(82, 42)
    if t > z1[0] + 0.8:
        k = G.clamp((t - z1[0] - 0.8) / 2.5)
        r = 14 - 11 * k
        G.circle(img, tx, ty, 16, (40, 20, 40))
        G.ring(img, tx, ty, 15, 16, WHITE)
        G.circle(img, tx, ty, max(1, r), (255, 80, 80))
        G.circle(img, tx, ty, max(0.6, r * 0.5), WHITE)
        ctx.text("MAGIC", tx, ty - 26, 2, WHITE)
        ctx.text("NUMBER", tx, ty - 20, 2, WHITE)
        ctx.text("HARD" if k > 0.6 else "EASY", tx, ty + 19, 2, RED if k > 0.6 else GREEN)
        ctx.pop_text("DIFFICULTY UP!", W / 2, L.P(118, 20), z1[0] + 1.2, 1.8, 4, RED)
    # hourglass that refuses to change
    if t > z1[0] + 1.0:
        hx, hy = L.P(98, 196), L.P(62, 18)
        crowd = G.clamp((t - z1[0] - 1.0) / 3)
        st = 1.0 + 0.18 * math.sin(T * 9) * crowd * (1 if t < p2[0] else 0.2)
        hourglass(img, ctx, hx, hy, 1.0, st)
        ctx.pop_text("STILL 10 MIN!", L.P(W / 2 + 22, hx + 8), hy + L.P(46, 48), z2[0] + 1.6, z2[1] - z2[0], 3, GOLD, wobble=False)
    # foreground characters
    fg = gy + L.P(0, 0)
    draw_mule(img, ctx, L.P(-14, 10), fg, 1, "idle")
    draw_pete(img, ctx, L.P(12, 46), fg, 1, pose="up" if p1[0] - 0.1 < t < p1[1] + 0.2 else None)
    draw_zoe(img, ctx, L.P(104, 190), fg, -1, pose="smile" if t > z3[0] else None)
    if p3[0] + 0.8 < t < p3[1] + 0.6:
        # a single proud tear
        k = (t - p3[0] - 0.8) % 1.2
        G.rect(img, L.P(12, 46) + 14, fg - 26 + k * 6, 1, 2, (120, 200, 255))
    tip(ctx, "MORE MINERS -> HARDER GAME -> STILL ~10 MIN PER PAGE", z2[0] + 0.3, z2[1] - z2[0] + 0.5, y=L.P(L.top_safe + 1, 62), color=GOLD)


# =============================================================== SCENE 6 — the bill
def meter(img, ctx, x, y, spin, fire):
    T = ctx.T
    G.rect(img, x - 2, y - 2, 30, 34, (70, 74, 90))
    G.rect(img, x, y, 26, 30, (200, 200, 190))
    G.circle(img, x + 13, y + 13, 10, (240, 240, 230))
    G.ring(img, x + 13, y + 13, 9, 10, (60, 60, 70))
    a = spin
    G.line(img, x + 13, y + 13, x + 13 + math.cos(a) * 8, y + 13 + math.sin(a) * 8, (220, 40, 40))
    G.rect(img, x + 4, y + 25, 18, 3, (60, 60, 70))
    for i in range(5):
        d = int((T * (3 + i * 7) * (1 + fire * 30)) % 10)
        ctx.text(str(d), x + 6 + i * 3.6, y + 24, 1, (255, 255, 255), center=False, outline=None)
    if fire > 0:
        for i in range(int(18 * fire)):
            ph = (T * 2 + h01(i, 1)) % 1
            fx = x + 2 + h01(i, 2) * 24 + math.sin(T * 9 + i) * 2
            fy = y - ph * 18
            c = (255, 220, 80) if ph < 0.3 else ((255, 140, 40) if ph < 0.6 else (200, 40, 30))
            G.rect(img, fx, fy, 3 - int(ph * 2), 3 - int(ph * 2), c)


def scene6(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    img[:] = cached(("wh", L.v), lambda: bg_warehouse(L))
    warehouse_live(img, ctx, L, 2.0)
    p1 = ctx.ln("s6_pete1")
    z1 = ctx.ln("s6_zoe1")
    p2 = ctx.ln("s6_pete2")
    r1 = ctx.ln("s6_riggy1")
    z2 = ctx.ln("s6_zoe2")
    banner(ctx, "STAGE 6: THE BILL", 0.1, 2.0)
    mx_, my_ = L.P(4, 14), L.P(36, 14)
    sp = 1 + G.clamp((t - 0.5) / 3) * 30
    fire = G.clamp((t - z1[0]) / 1.0) if t > z1[0] else 0
    heat = G.clamp((t - p2[1] + 0.2) / 0.8) if t > p2[1] - 0.2 else 0.25
    tub_t = r1[1] + 0.3
    if L.v:
        rx, rgy, rs, ex = 58, 146, 2, 0
        rtop = rgy - 59 * rs
    else:
        rx, rgy, rs, ex = 118, gy - 2, 1, 22
        rtop = rgy - 81
    draw_riggy(img, ctx, rx, rgy, scale=rs, extra=ex, heat=heat, eyes="x" if r1[0] < t < r1[1] else "normal", led_rate=3)
    meter(img, ctx, mx_, my_, T * sp, fire)
    ctx.text("POWER", mx_ + 13, my_ - 8, 2, WHITE)
    if t > r1[0]:
        tx, ty, th = (rx - 9, rtop + 10, 80) if L.v else (rx + 40, rtop + 4, 60)
        G.rect(img, tx, ty, 5, th, (230, 230, 240))
        G.rect(img, tx + 1, ty + 1 + int((th - 2) * (1 - heat)), 3, int((th - 2) * heat), (255, 50, 50))
        G.circle(img, tx + 2.5, ty + th, 4, (255, 50, 50))
        ctx.pop_text("HEAT 999%", L.P(rx + 36, rx + 18), L.P(rtop + 74, rtop + 30), r1[0] + 0.2, 2.5, 4, RED)
    tbx, tby = (66, gy - 1) if L.v else (166, gy + 2)
    tw = 54
    if t > tub_t - 0.4:
        k = G.ease_out_back((t - tub_t + 0.4) / 0.4)
        G.rect(img, tbx, tby - 12 * k, tw, 12 * k + 2, (130, 80, 50))
        G.rect(img, tbx, tby - 12 * k, tw, 2, (170, 110, 70))
        G.rect(img, tbx + 2, tby - 10 * k, tw - 4, 4, (80, 200, 255))
        steam(img, T, tbx + tw / 2, tby - 10, 10, 44, 18)
        for i in range(5):
            ph = (T * 2 + h01(i, 3)) % 1
            G.circle(img, tbx + 6 + i * 10, tby - 8 - ph * 3, 1, (220, 250, 255))
        ctx.pop_text("BONUS: FREE HOT TUB!", W / 2, L.P(L.top_safe + 4, 24), tub_t + 0.3, z2[0] - tub_t + 1.6, 4, CYAN)
        ctx.pop_text("SPLASH!", tbx + 27, tby - 30, tub_t + 0.2, 0.6, 3, WHITE)
    if z2[0] + 0.2 < t < z2[1] - 0.5:
        k = G.ease_out_back((t - z2[0] - 0.2) / 0.4)
        gx, gy2 = L.P(4, 192), L.P(80, 6)
        gw = int(44 * min(1, k))
        G.rect(img, gx, gy2 + 10, gw, 20, (170, 230, 240))
        for i in range(0, gw, 6):
            G.rect(img, gx + i, gy2 + 10, 1, 20, (240, 255, 255))
            G.rect(img, gx + i + 2, gy2 + 22, 2, 8, (60, 170, 70))
            G.rect(img, gx + i + 1, gy2 + 20, 4, 3, (90, 210, 90))
        for i in range(gw // 2):
            G.safe_px(img, gx + 22 - i, gy2 + 10 - i // 2, (240, 255, 255))
            G.safe_px(img, gx + 22 + i, gy2 + 10 - i // 2, (240, 255, 255))
        ctx.text("GREENHOUSE", gx + 22, gy2 + 32, 2, GREEN)
    shout = p2[0]
    shake(ctx, shout, 0.8, 4)
    px = L.P(10, 50)
    faint_k = G.clamp((t - shout - 0.3) / 0.5) if t > shout + 0.3 else 0
    draw_mule(img, ctx, L.P(-14, 2), gy, 1, "sad" if t > z1[0] else "idle", faint=faint_k)
    if faint_k >= 1:
        ctx.pop_text("HEE-HAW!", L.P(20, 26), gy - 36, shout + 0.4, 1.0, 3, WHITE)
    pose = "surprised" if p2[0] - 0.05 < t < p2[1] + 0.3 else None
    draw_pete(img, ctx, px, gy, 1, pose=pose, pick=True)
    if p2[0] < t < p2[0] + 1.2:
        k = t - p2[0]
        hy = gy - 34 - k * 60 + k * k * 60
        G.rect(img, px + 1, hy, 18, 3, (205, 170, 105))
        G.rect(img, px + 5, hy - 4, 10, 4, (205, 170, 105))
    if p2[0] < t < p2[1]:
        ctx.pop_text("!!!", px + 12, gy - 54, p2[0], p2[1] - p2[0], 6, GOLD)
    if t > tub_t:
        draw_zoe(img, ctx, tbx + 6, tby - 2, 1, pose="smile")
        G.rect(img, tbx + 2, tby - 8, tw - 4, 3, (80, 200, 255))
        G.rect(img, tbx, tby - 5, tw, 7, (130, 80, 50))
        G.rect(img, tbx, tby - 5, tw, 1, (170, 110, 70))   # tub front hides her feet in the water
    else:
        draw_zoe(img, ctx, L.P(108, 200), gy, -1)
    # the electric bill unrolls down the whole screen, keeps going, then falls away
    b0 = z1[0] + 0.3
    if b0 < t:
        k = t - b0
        drop = max(0.0, k - 2.7) * 320
        if drop < H + 10:
            bw = L.P(56, 64)
            bx = W / 2 - bw / 2
            top = L.P(26, 0) + drop
            h = min(H * 3, k * 100)
            G.rect(img, bx, top, bw, h, (250, 248, 236))
            G.rect(img, bx, top, 2, h, (210, 205, 190))
            G.rect(img, bx + bw - 2, top, 2, h, (210, 205, 190))
            for yy in range(int(top + 52), int(min(H, top + h)), 5):
                G.rect(img, bx + 5, yy, bw - 20 - int(h01(yy - int(top), 1) * 12), 1, (150, 150, 160))
                G.rect(img, bx + bw - 12, yy, 7, 1, (150, 150, 160))
            G.rect(img, bx - 2, top + h - 3, bw + 4, 6, (230, 225, 210))
            ctx.text("ELECTRIC BILL", bx + bw / 2, top + 4, 2, (180, 30, 40), outline=None)
            if k > 0.6:
                ctx.text("TOTAL:", bx + bw / 2, top + 18, 2, (40, 40, 60), outline=None)
                ctx.text("A SMALL", bx + bw / 2, top + 28, 3, (180, 30, 40), outline=None)
                ctx.text("COUNTRY", bx + bw / 2, top + 38, 3, (180, 30, 40), outline=None)
    tip(ctx, "GUESSING BURNS LOTS OF ELECTRICITY + MAKES HEAT", r1[0] - 0.1, r1[1] - r1[0] + 0.7, y=L.P(L.top_safe + 2, 2), color=RED)


def scene7(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    img[:] = cached(("wh", L.v), lambda: bg_warehouse(L))
    warehouse_live(img, ctx, L)
    p1 = ctx.ln("s7_pete1")
    z1 = ctx.ln("s7_zoe1")
    p2 = ctx.ln("s7_pete2")
    banner(ctx, "STAGE 7: PETE TRIES", 0.1, 2.0)
    if L.v:
        cx, cw = 34, 62
        mxx, myy, mon_w, mon_h = 10, 40, 116, 80
        cols, rows, sc = 5, 8, 2
    else:
        cx, cw = 110, 40
        mxx, myy, mon_w, mon_h = 98, gy - 18 - 50, 66, 50
        cols, rows, sc = 4, 6, 1
    # crates
    for k in range(2 if L.v else 1):
        cy0 = gy - 18 * (k + 1)
        G.rect(img, cx, cy0, cw, 18, (150, 100, 50))
        G.rect(img, cx, cy0, cw, 2, (190, 130, 70))
        G.line(img, cx, cy0 + 2, cx + cw, cy0 + 17, (110, 70, 40))
    if L.v:
        G.rect(img, mxx + mon_w // 2 - 6, myy + mon_h, 12, gy - 36 - myy - mon_h, (150, 146, 130))
    G.rect(img, mxx, myy, mon_w, mon_h, (200, 196, 176))
    G.rect(img, mxx + 4, myy + 4, mon_w - 8, mon_h - 12, (10, 30, 20))
    G.rect(img, mxx + mon_w - 12, myy + mon_h - 6, 6, 2, (80, 255, 120))
    # keyboard in front of Pete
    kx, ky = (cx - 4, gy - 37) if L.v else (cx - 2, gy - 22)
    G.rect(img, kx, ky, 30, 4, (180, 176, 160))
    for i in range(7):
        G.rect(img, kx + 2 + i * 4, ky, 3, 1, (120, 116, 100))
    pound_rate = 4.5
    pound = int(t * pound_rate)
    swing = (t * pound_rate) % 1.0
    px = L.P(2, 70)
    pgy = gy
    draw_pete(img, ctx, px, pgy, 1, pose="up" if swing < 0.5 else None, pick=True, pick_angle=-120 + 40 * swing if swing < 0.5 else -60)
    if swing < 0.15:
        ctx.text("GUESS!", kx + 16 + (pound % 3 - 1) * 8, ky - 14 - (pound % 2) * 6, 3, GOLD)
    n_wrong = min(999, pound * 3)
    cell_w = (mon_w - 12) / cols
    cell_h = (mon_h - 16) / rows
    for i in range(min(cols * rows, n_wrong)):
        c, r = i % cols, i // cols
        ctx.text("WRONG", mxx + 6 + c * cell_w, myy + 6 + r * cell_h, sc, (255, 80, 80), center=False, outline=None)
    if (t > 2.2 or not L.v) and not (p2[0] + 1.75 < t < p2[0] + 3.9):
        ctx.text("WRONG x" + str(n_wrong), mxx + mon_w / 2, myy - 10, 3, RED)
    if t > z1[0] + 1.2:
        ey = L.P(myy + mon_h - 31, 20)
        ctx.orect(W / 2 - L.P(56, 58), ey - 3, L.P(112, 116), 13, (8, 16, 30), 0.92)
        ctx.pop_text("ETA: 3,000 YEARS", W / 2, ey, z1[0] + 1.2, 99, 4, CYAN, wobble=False)
        bx, by, bw = (16, myy + mon_h - 20, 100) if L.v else (60, 31, 120)
        G.rect(img, bx, by, bw, 6, (255, 255, 255))
        G.rect(img, bx + 1, by + 1, bw - 2, 4, (20, 20, 30))
        G.rect(img, bx + 1, by + 1, 1, 4, (80, 255, 120))
        ctx.text("PROGRESS: 0.0001%", bx + bw / 2, by + 8, 2, GREEN)
    draw_zoe(img, ctx, L.P(110, 196), gy, -1)
    draw_mule(img, ctx, L.P(-22, 2), gy, 1, "idle") if not L.v else None
    if p2[0] + 1.6 < t:
        ctx.pop_text("WARMED UP!", W / 2, L.P(L.top_safe + 2, 2), p2[0] + 1.8, 2.0, 6, GOLD)


def bg_sunset(L):
    W, H = L.W, L.H
    img = G.dither_gradient(H, W, [(0, (40, 20, 80)), (0.3, (160, 60, 120)), (0.5, (255, 120, 80)), (0.62, (255, 200, 110)), (1, (255, 200, 110))])
    gy = L.ground
    G.circle(img, W / 2, gy - L.P(46, 36), L.P(22, 18), (255, 230, 140))
    for k in range(0, 12, 3):
        G.rect(img, 0, gy - L.P(46, 36) + k + 6, W, 1, (255, 150, 110))
    wx, ww = L.P(20, 60), L.P(96, 120)
    G.rect(img, wx, gy - L.P(44, 34), ww, L.P(44, 34), (44, 26, 56))
    G.rect(img, wx + 6, gy - L.P(54, 42), 8, 12, (44, 26, 56))
    G.rect(img, 0, gy, W, H - gy, (70, 40, 60))
    return img


def scene8(img, ctx):
    L = ctx.L
    t = ctx.t
    T = ctx.T
    W, H, gy = L.W, L.H, L.ground
    p1 = ctx.ln("s8_pete1")
    z1 = ctx.ln("s8_zoe1")
    pa = ctx.ln("s8_pete2a")
    pb = ctx.ln("s8_pete2b")
    r1 = ctx.ln("s8_riggy1")
    go_t = r1[0] - 0.1
    end_t = r1[1] + 0.5
    if t < go_t:
        img[:] = cached(("sunset", L.v), lambda: bg_sunset(L))
        banner(ctx, "STAGE 8: SUNSET", 0.1, 2.0)
        wx = L.P(20, 60)
        for i in range(10):
            if h01(i, int(T * 3)) > 0.5:
                img[gy - L.P(30, 22) + (i % 3) * 6, wx + 8 + i * 8] = (80, 255, 120)
        steam(img, T, wx + 10, gy - L.P(54, 42), 5, 6, 16, col=(200, 160, 200))
        for i in range(3):
            bird(img, (T * 8 + i * 37) % (W + 20) - 10, L.P(50, 24) + i * 5, T, i)
        fy = gy + L.P(4, 4)
        G.rect(img, 0, fy, W, H - fy, (50, 30, 46))
        S = 2 if L.v else 1
        # Biscuit soaking in the hot tub (further back, right)
        tbx = L.P(92, 150)
        tby = fy + L.P(-6, 0)
        G.rect(img, tbx, tby - 14, 46, 3, (170, 110, 70))
        m = G.mule_frames_cache()["idle"]
        G.blit(img, m, tbx + 6, tby - 26)
        G.rect(img, tbx + 2, tby - 11, 42, 4, (80, 200, 255))
        G.rect(img, tbx, tby - 7, 46, 8, (130, 80, 50))
        G.rect(img, tbx, tby - 7, 46, 1, (170, 110, 70))
        steam(img, T, tbx + 23, tby - 12, 8, 30, 14)
        ctx.pop_text("zzz", tbx + 36, tby - 36, 0.5, 99, 3, WHITE, wobble=True)
        # Pete and Zoe sitting in a two-cart train (carts drawn over their legs)
        fw, fh = 58, 46
        fg = G.offscreen(fw, fh)
        ffy = fh - 2
        cx = 4
        draw_pete(fg, ctx, cx, ffy - 3, 1, pick=False, bob=False)
        draw_zoe(fg, ctx, cx + 27, ffy - 3, -1, pose="smile" if t > pb[1] else None)
        G.blit(fg, G.MINECART, cx - 3, ffy - 12)
        G.blit(fg, G.MINECART, cx + 22, ffy - 12)
        ox = L.P(4, 44)
        oy = fy + 2 - fh * S
        G.blit(img, G.key_to_rgba(fg), ox, oy, S)
    elif t < end_t:
        img[:] = (8, 6, 16)
        stars_bg(img, T, 40, 9)
        ctx.pop_text("GAME OVER", W / 2, L.P(70, 30), go_t, 99, 8, RED, wobble=False)
        if t - go_t > 0.6 and int(T * 2.5) % 2 == 0:
            ctx.text("INSERT ELECTRICITY", W / 2, L.P(100, 56), 3, WHITE)
            ctx.text("TO CONTINUE", W / 2, L.P(108, 64), 3, WHITE)
        G.rect(img, W / 2 - 8, L.P(122, 78), 16, 12, (120, 120, 140))
        G.rect(img, W / 2 - 4, L.P(125, 81), 2, 5, (20, 20, 30))
        G.rect(img, W / 2 + 2, L.P(125, 81), 2, 5, (20, 20, 30))
        G.rect(img, W / 2 - 1, L.P(134, 90), 2, 10, (40, 40, 50))
    else:
        ctx.hide_box = True
        img[:] = (8, 6, 16)
        stars_bg(img, T, 40, 9)
        kk = G.clamp((t - end_t) / 0.4)
        ctx.text("CRYPTO MINING:", W / 2, L.P(72, 30), 5, GOLD, alpha=kk)
        ctx.text("the world's most", W / 2, L.P(90, 48), 4, WHITE, alpha=kk)
        ctx.text("expensive", W / 2, L.P(102, 60), 4, WHITE, alpha=kk)
        ctx.text("guessing game.", W / 2, L.P(114, 72), 4, WHITE, alpha=kk)
        for i in range(6):
            G.blit(img, G.COIN_FRAMES[int(T * 8 + i) % 4], W / 2 - 30 + i * 10, L.P(134, 92))



SCENES = {1: scene1, 2: scene2, 3: scene3, 4: scene4, 5: scene5, 6: scene6, 7: scene7, 8: scene8}
