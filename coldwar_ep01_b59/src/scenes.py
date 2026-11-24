"""Scene renderers. Each scene(t, **kw) -> float32 HxWx3 image (pre-finish).

t is seconds since the scene started. Scenes are deterministic in t.
"""
import functools
import math
import os

import cv2
import numpy as np
from PIL import Image

import globe as G
import shapes as S
from engine import (ALERT, ASSETS, BG, BG2, H, HYPO, NEU, NEU_DIM, SAFE_BOTTOM, SAFE_TOP, SONAR, SU, SU_DIM,
                    US, US_DIM, W, blit_mask, blur, canvas, chroma_shift, clamp01, corner_tag, dashed,
                    draw_text, ease_in_out, ease_out, glow, grid, hypo_frame, lerp, mask_circle, mask_ellipse,
                    mask_poly, mask_polyline, noise_tile, paint, radial, ramp, scroll_noise, subtitle,
                    text_size, thermal_map, value_noise, vgrad)


# ============================================================================
# 1. title card
# ============================================================================

def title_card(t, sub=None):
    img = vgrad(np.array([0.010, 0.016, 0.028], np.float32), np.array([0.025, 0.045, 0.075], np.float32), power=1.4)
    wl = 1180
    # sea below horizon: darker, with faint moving glints
    xx, yy = grid()
    sea = (yy > wl).astype(np.float32)
    tile = noise_tile(512, 40, 3, 4)
    n = scroll_noise(H, W, tile, t * 6, t * 2, zoom=1.0)
    streak = cv2.blur(n, (61, 1))
    depth = np.clip((yy - wl) / 700, 0, 1)
    glint = np.clip((streak - 0.55) * 6, 0, 1) * (1 - depth) ** 2 * sea
    img = img * (1 - sea[..., None] * 0.65)
    img += glint[..., None] * np.array([0.10, 0.16, 0.24], np.float32)
    # horizon line glow
    hl = np.exp(-((yy - wl) / 2.0) ** 2) * np.clip(1 - np.abs(xx - W / 2) / (W * 0.62), 0, 1)
    img += glow(hl[..., None] * np.array([0.35, 0.55, 0.85], np.float32), (2, 8, 30), (0.8, 0.5, 0.3))
    # tiny conning-tower silhouette sitting on the horizon (amber rim)
    hull, sail, _ = S.sub_side()
    cx = 700
    sail_pts = S.place(sail, cx, wl + 2, 240)
    hull_pts = S.place(hull, cx, wl + 2, 240)
    m = mask_poly([sail_pts, hull_pts])
    m *= (yy < wl + 1)
    paint(img, m, (0.004, 0.006, 0.01), 1.0)
    rim = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1)
    img += glow(rim[..., None] * SU * 0.8, (1.5, 6), (0.8, 0.5))
    # type
    a = ease_out(ramp(t, 0.2, 1.4))
    draw_text(img, "冷 战 核 按 钮", W / 2, 560, size=40, weight="medium", color=NEU_DIM, alpha=a, anchor="mm", tracking=0.25)
    draw_text(img, "第一期", W / 2, 625, size=34, weight="regular", color=NEU_DIM, alpha=a, anchor="mm", tracking=0.4)
    a2 = ease_out(ramp(t, 0.6, 2.0))
    draw_text(img, "海底那一夜", W / 2, 790, size=150, weight="black", color=NEU, alpha=a2, anchor="mm", tracking=0.06,
              glow=0.18)
    lw = 420 * ease_in_out(ramp(t, 1.0, 2.2))
    line = np.zeros((H, W), np.float32)
    cv2.line(line, (int(W / 2 - lw / 2), 905), (int(W / 2 + lw / 2), 905), 1.0, 2, cv2.LINE_AA)
    img += glow(line[..., None] * SU * 0.9, (1, 5), (1.0, 0.4))
    draw_text(img, "1962 · 10 · 27", W / 2, 960, size=36, weight="mono", color=SU, alpha=ease_out(ramp(t, 1.4, 2.6)),
              anchor="mm", tracking=0.15)
    if sub:
        subtitle(img, sub)
    return img


# ============================================================================
# 2. U-2 photo with wireframe annotation
# ============================================================================

@functools.lru_cache(maxsize=1)
def u2_photo():
    im = Image.open(os.path.join(ASSETS, "archive/u2_sancristobal_19621014.jpg")).convert("L")
    return np.asarray(im, np.float32) / 255.0


# boxes in source-image pixel coords (1920x1620): (x0, y0, x1, y1, label, placement)
U2_BOXES = [
    (470, 1135, 585, 1235, "导弹拖车", "below-left"),
    (1395, 985, 1545, 1100, "帐篷区", "above-right"),
    (940, 975, 1000, 1030, "设备车辆", "below-right"),
]


def u2_scene(t, sub=None, zoom0=1.0, zoom1=1.32, dur=8.0, focus=(990, 1110)):
    img = canvas(np.array([0.012, 0.016, 0.022], np.float32))
    ph = u2_photo()
    ih, iw = ph.shape
    k = ease_in_out(ramp(t, 0, dur))
    z = lerp(zoom0, zoom1, k)
    top, bottom = 300, 1190
    vh = bottom - top
    s = W / iw * z  # screen px per image px
    fx = lerp(iw / 2, focus[0], k)
    fy = lerp(ih / 2, focus[1], k)
    M = np.array([[s, 0, W / 2 - fx * s], [0, s, top + vh / 2 - fy * s]], np.float32)
    warped = cv2.warpAffine(ph, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    win = np.zeros((H, W), np.float32)
    win[top:bottom] = 1
    win = cv2.GaussianBlur(win, (0, 0), 2)
    gray = (warped * 0.92 + 0.02) * win
    tint = np.array([0.80, 0.90, 1.0], np.float32)
    img = img * (1 - win[..., None]) + gray[..., None] * tint
    xx, yy = grid()
    sy = top + (t * 140) % vh
    scan = np.exp(-((yy - sy) / 3.0) ** 2) * win
    img += scan[..., None] * US * 0.25
    fm = np.zeros((H, W), np.float32)
    L = 46
    for (x, y, dx, dy) in [(40, top - 14, 1, 1), (W - 40, top - 14, -1, 1), (40, bottom + 14, 1, -1), (W - 40, bottom + 14, -1, -1)]:
        cv2.line(fm, (x, y), (x + dx * L, y), 1.0, 2, cv2.LINE_AA)
        cv2.line(fm, (x, y), (x, y + dy * L), 1.0, 2, cv2.LINE_AA)
    paint(img, fm, US, 0.9)
    for i, (x0, y0, x1, y1, lab, place_) in enumerate(U2_BOXES):
        a = ease_out(ramp(t, 1.2 + i * 0.6, 1.8 + i * 0.6))
        if a <= 0:
            continue
        X0, Y0 = (x0 - fx) * s + W / 2, (y0 - fy) * s + top + vh / 2
        X1, Y1 = (x1 - fx) * s + W / 2, (y1 - fy) * s + top + vh / 2
        pad = 10
        m = np.zeros((H, W), np.float32)
        cv2.rectangle(m, (int(X0 - pad), int(Y0 - pad)), (int(X1 + pad), int(Y1 + pad)), 1.0, 2, cv2.LINE_AA)
        tw, th = text_size(lab, "bold", 32)
        vert, horiz = place_.split("-")
        ly = (Y1 + pad + 70) if vert == "below" else (Y0 - pad - 70 - th)
        if horiz == "left":
            lx = min(max(56, X0 - 40), W - 56 - tw)
        else:
            lx = max(min(W - 56 - tw, X1 + 40 - tw), 56)
        ly = min(max(ly, top + 16), bottom - th - 16)
        # leader from box edge to label
        bx = (X0 + X1) / 2
        by = (Y1 + pad) if vert == "below" else (Y0 - pad)
        ty = ly if vert == "below" else ly + th - 6
        tx = min(max(bx, lx + 10), lx + tw - 10)
        cv2.line(m, (int(bx), int(by)), (int(tx), int(ty)), 1.0, 2, cv2.LINE_AA)
        m *= win
        paint(img, m, US, a)
        img += glow(m[..., None] * US * 0.25 * a, (3, 9), (0.6, 0.3))
        plate = np.zeros((H, W), np.float32)
        cv2.rectangle(plate, (int(lx - 12), int(ly - 4)), (int(lx + tw + 12), int(ly + th - 4)), 1.0, -1)
        paint(img, plate * win, (0.01, 0.03, 0.06), 0.85 * a)
        draw_text(img, lab, lx, ly, size=32, weight="bold", color=US, alpha=a, anchor="lt")
    corner_tag(img, "1962.10.14  U-2 侦察照片", 48, top - 64, color=NEU, size=28)
    corner_tag(img, "SAN CRISTOBAL NO.1", W - 48, top - 64, color=NEU_DIM, size=24, anchor="rt")
    draw_text(img, "来源：美国国家档案馆 NARA 193926（美国政府作品，公有领域）", W - 48, bottom + 22, size=22,
              weight="regular", color=NEU_DIM, anchor="rt")
    if sub:
        subtitle(img, sub)
    return img


# ============================================================================
# 3. globe with missile range rings
# ============================================================================
SITE_CUBA = (22.72, -83.06)
WASHINGTON = (38.90, -77.04)


def globe_range(t, sub=None, ring_km=2000):
    cam = G.Cam(lat0=29.5, lon0=-81.0, R=1750, cx=W / 2, cy=930)
    img = canvas(np.array([0.010, 0.016, 0.026], np.float32))
    disk = G.disk_mask(cam)
    ocean = vgrad(np.array([0.012, 0.024, 0.045], np.float32), np.array([0.006, 0.012, 0.024], np.float32))
    img = img * (1 - disk[..., None]) + ocean * disk[..., None]
    land, zz = G.land_mask(cam)
    img += land[..., None] * np.array([0.030, 0.042, 0.058], np.float32)
    grat = G.graticule_mask(cam, step=5, thickness=1.0)
    paint(img, grat, US_DIM, 0.10)
    coast = G.coast_mask(cam, thickness=1.7)
    img += coast[..., None] * NEU * 0.55
    img += glow(coast[..., None] * np.array([0.35, 0.55, 0.85], np.float32) * 0.35, (2, 7), (0.6, 0.3))
    # cities: dim everywhere, bright when inside reached ring
    v, wts, lat, lon = G.cities()
    d = np.array([G.gc_distance_km(SITE_CUBA[0], SITE_CUBA[1], a, b) for a, b in zip(lat, lon)])
    k = ease_out(ramp(t, 1.0, 5.0))
    cur_r = ring_km * k
    lit = (d < cur_r).astype(np.float32)
    sx, sy, vis, _ = cam.project(v)
    base = G.splat_points(sx[vis], sy[vis], (wts[vis] * (0.25 + 1.4 * lit[vis])))
    lights = cv2.GaussianBlur(base, (0, 0), 1.1) * 3.0 + blur(base, 5) * 14
    img += lights[..., None] * np.array([0.85, 0.92, 1.0], np.float32) * 0.6
    # rings (amber = Soviet weapon)
    ring = np.zeros((H, W), np.float32)
    for i, rk in enumerate([500, 1000, 1500, 2000]):
        if rk > cur_r + 1:
            continue
        pts = G.small_circle(SITE_CUBA[0], SITE_CUBA[1], rk)
        x, y, vv, _ = cam.project(pts)
        ring = np.maximum(ring, mask_polyline([np.stack([x, y], 1)], thickness=2.4 if rk == 2000 else 1.4, closed=True)
                          * (1.0 if rk == 2000 else 0.55))
    # ripple front
    if 0 < k < 1:
        pts = G.small_circle(SITE_CUBA[0], SITE_CUBA[1], max(10, cur_r))
        x, y, vv, _ = cam.project(pts)
        ring = np.maximum(ring, mask_polyline([np.stack([x, y], 1)], thickness=4, closed=True))
    img += ring[..., None] * SU * 0.95 + glow(ring[..., None] * SU * 0.5, (3, 12, 30), (0.7, 0.4, 0.25))
    # site marker
    p = G.ll2v(np.array(SITE_CUBA[0]), np.array(SITE_CUBA[1]))
    x, y, _, _ = cam.project(p[None])
    x, y = float(x[0]), float(y[0])
    dot = mask_circle(x, y, 9)
    img += glow(dot[..., None] * SU * 2.0, (2, 8, 20), (1, 0.6, 0.3)) + dot[..., None] * SU
    draw_text(img, "导弹阵地", x + 22, y + 6, size=30, weight="bold", color=SU, anchor="lt")
    # Washington
    p = G.ll2v(np.array(WASHINGTON[0]), np.array(WASHINGTON[1]))
    wx, wy, _, _ = cam.project(p[None])
    wx, wy = float(wx[0]), float(wy[0])
    wa = ease_out(ramp(t, 3.5, 4.5))
    if wa > 0:
        m = mask_circle(wx, wy, 16, fill=False, thickness=2.5)
        img += m[..., None] * US * wa + glow(m[..., None] * US * wa, (3, 10), (0.8, 0.4))
        draw_text(img, "华盛顿", wx - 26, wy - 6, size=36, weight="bold", color=NEU, alpha=wa, anchor="rb", shadow=0.8)
    # range label on ring
    if k > 0.95:
        pts = G.small_circle(SITE_CUBA[0], SITE_CUBA[1], ring_km, n=360)
        x, y, vv, _ = cam.project(pts)
        i = int(np.argmin(np.abs(np.degrees(np.arctan2(x - W / 2, 1)) * 0) + np.abs(y - (cam.cy + 260)) + (x < W / 2) * 1e6))
        draw_text(img, "射程约 2000 公里", x[i] - 20, y[i] + 10, size=28, weight="medium", color=SU, anchor="rt",
                  alpha=ease_out(ramp(t, 5.0, 5.8)), shadow=0.8)
    corner_tag(img, "R-12 中程弹道导弹 · 射程示意", 48, SAFE_TOP + 10, color=NEU_DIM, size=24)
    corner_tag(img, "地图仅示海岸线", W - 48, SAFE_TOP + 10, color=NEU_DIM, size=22, anchor="rt")
    if sub:
        subtitle(img, sub)
    return img


# ============================================================================
# 4. timeline: 10月27日, three red dots
# ============================================================================

def timeline(t, sub=None, active=3):
    img = vgrad(np.array([0.012, 0.016, 0.026], np.float32), np.array([0.02, 0.03, 0.05], np.float32))
    a0 = ease_out(ramp(t, 0.0, 0.8))
    draw_text(img, "1962 · 10 · 27  星期六", W / 2, SAFE_TOP + 60, size=34, weight="medium", color=NEU_DIM, alpha=a0,
              anchor="mm", tracking=0.12)
    draw_text(img, "黑色星期六", W / 2, SAFE_TOP + 165, size=116, weight="black", color=NEU, alpha=a0, anchor="mm",
              tracking=0.08)
    ax0, ax1, ay = 90, 990, 930

    def hx(hh):
        return ax0 + (ax1 - ax0) * hh / 24.0
    axis = np.zeros((H, W), np.float32)
    cv2.line(axis, (ax0, ay), (ax1, ay), 1.0, 2, cv2.LINE_AA)
    for hh in range(0, 25, 3):
        x = int(hx(hh))
        e = 12 if hh % 12 == 0 else 7
        cv2.line(axis, (x, ay - e), (x, ay + e), 1.0, 2, cv2.LINE_AA)
    paint(img, axis, NEU_DIM, 0.9 * a0)
    for lab, h0, h1 in [("凌晨", 0, 6), ("上午", 6, 12), ("下午", 12, 18), ("夜里", 18, 24)]:
        draw_text(img, lab, hx((h0 + h1) / 2), ay + 26, size=26, weight="regular", color=NEU_DIM, alpha=a0 * 0.9,
                  anchor="mt")
    # (hour, title, desc, label box top-left, label anchor side)
    events = [
        (10.4, "古巴上空", "U-2 被萨姆导弹击落", (70, 610), "l"),
        (11.7, "北极上空", "U-2 迷航，闯入苏联领空", (70, 1050), "l"),
        (16.98, "大西洋海底", "B-59 · 16:59—20:50", (W - 70, 610), "r"),
    ]
    for i, (hh, title, desc, (lx, ly), side) in enumerate(events):
        a = ease_out(ramp(t, 0.6 + i * 0.9, 1.2 + i * 0.9))
        if a <= 0:
            continue
        x = hx(hh)
        if i == 2:
            bar = np.zeros((H, W), np.float32)
            cv2.line(bar, (int(hx(16.98)), ay), (int(hx(20.83)), ay), 1.0, 6, cv2.LINE_AA)
            img += bar[..., None] * ALERT * a * 0.9
        # leader: dot -> elbow -> label
        up = ly < ay
        ey = ly + (118 if up else -16)
        stem = np.zeros((H, W), np.float32)
        cv2.line(stem, (int(x), ay), (int(x), int(ey)), 1.0, 2, cv2.LINE_AA)
        ex = lx + (260 if side == "l" else -260)
        cv2.line(stem, (int(x), int(ey)), (int(ex), int(ey)), 1.0, 2, cv2.LINE_AA)
        paint(img, stem, ALERT, 0.75 * a)
        dot = mask_circle(x, ay, 13)
        pulse = 0.5 + 0.5 * math.sin((t - i) * 4.0)
        img += glow(dot[..., None] * ALERT * (1.2 + (1.0 if i + 1 == active else 0.3) * pulse) * a, (3, 10, 26),
                    (1, 0.6, 0.35)) + dot[..., None] * ALERT * a
        if i + 1 == active:
            for kk in range(3):
                ph = ((t * 0.9 + kk / 3.0) % 1.0)
                ring = mask_circle(x, ay, 14 + ph * 90, fill=False, thickness=2.0)
                img += ring[..., None] * ALERT * (1 - ph) * 0.8 * a
        anc = "l" if side == "l" else "r"
        draw_text(img, title, lx, ly, size=52, weight="black", color=NEU, alpha=a, anchor=anc + "t")
        draw_text(img, desc, lx, ly + 72, size=28, weight="medium", color=ALERT * 0.55 + NEU * 0.45, alpha=a,
                  anchor=anc + "t")
    if sub:
        subtitle(img, sub)
    return img


# ============================================================================
# 5. underwater: sonar + practice depth charges
# ============================================================================

def _ship_side_mask(polys, cx, cy, scale, angle=0.0):
    return mask_poly([S.place(p, cx, cy, scale, angle) for p in polys])


def sonar_scene(t, sub=None, hits=(1.2, 1.75, 2.3, 2.9, 3.4), hits2=(), show_sub_label=True):
    img = vgrad(np.array([0.010, 0.040, 0.052], np.float32), np.array([0.002, 0.007, 0.010], np.float32), power=0.75)
    xx, yy = grid()
    surf = 420
    sky = (yy < surf).astype(np.float32)[..., None]
    img = img * (1 - sky) + sky * np.array([0.005, 0.008, 0.014], np.float32)
    sl = np.exp(-((yy - surf) / 1.6) ** 2)
    img += sl[..., None] * np.array([0.25, 0.45, 0.6], np.float32) * 0.6
    for (cx, sc, flip) in [(300, 330, 1), (800, 300, -1)]:
        polys = [p * np.array([flip, 1.0]) for p in S.destroyer_side()]
        m = _ship_side_mask(polys, cx, surf + 3, sc)
        m *= (yy < surf + 2)
        paint(img, m, (0.004, 0.006, 0.01), 1.0)
        rim = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1)
        img += rim[..., None] * US * 0.9 + glow(rim[..., None] * US * 0.4, (2, 6), (0.6, 0.3))
    tile = noise_tile(512, 60, 7, 3)
    rays = scroll_noise(H, W, tile, t * 8, 0, zoom=2.0)
    rays = cv2.blur(rays, (3, 121))
    rays = np.clip((rays - 0.45) * 2.5, 0, 1) * np.clip(1 - (yy - surf) / 650, 0, 1) * (yy > surf)
    img += rays[..., None] * np.array([0.05, 0.12, 0.14], np.float32) * 0.5
    scx, scy, slen = 540, 1150, 840
    hull, sail, fins = S.sub_side()
    # --- sonar fan (passive array listening upward) ---
    ox, oy = scx + 0.28 * slen, scy - 44
    fan_a = math.radians(52)
    ang = np.arctan2(xx - ox, -(yy - oy))
    rr = np.hypot(xx - ox, yy - oy)
    R = 700
    inside = (np.abs(ang) < fan_a) & (rr < R) & (yy > surf)
    fan = np.zeros((H, W), np.float32)
    fan += inside * 0.05
    for r in np.arange(R / 4, R + 1, R / 4):
        fan += np.exp(-((rr - r) / 1.2) ** 2) * inside * 0.5
    for b in np.radians(np.arange(-50, 51, 10)):
        fan += np.exp(-((ang - b) * rr / 1.2) ** 2) * inside * 0.25
    fan += np.exp(-((np.abs(ang) - fan_a) * rr / 1.4) ** 2) * (rr < R) * (yy > surf) * 0.6
    sw = math.sin(t * 1.2) * fan_a * 0.95
    fan += np.exp(-((ang - sw) * rr / 2.0) ** 2) * inside * 1.0
    fan += np.clip(1 - np.abs(ang - sw) / 0.45, 0, 1) ** 3 * inside * 0.18
    # --- depth charges ---
    flash = 0.0
    rings = np.zeros((H, W), np.float32)
    dots = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(5)
    for i, th in enumerate(list(hits) + list(hits2)):
        hx_ = scx + rng.uniform(-300, 300)
        hy_ = scy - rng.uniform(170, 330)
        sink0 = th - 1.5
        if sink0 < t < th:
            k = (t - sink0) / 1.5
            y = lerp(surf + 8, hy_, k)
            dots += mask_circle(hx_, y, 3.5)
            tr = np.zeros((H, W), np.float32)
            cv2.line(tr, (int(hx_), int(max(surf, y - 50))), (int(hx_), int(y)), 1.0, 1, cv2.LINE_AA)
            dots += tr * 0.3
        if t >= th:
            age = t - th
            if age < 2.2:
                r = 14 + age * 560
                fade = (1 - age / 2.2) ** 1.6
                rings += mask_circle(hx_, hy_, r, fill=False, thickness=2.5) * fade
                rings += blur(mask_circle(hx_, hy_, r * 0.93, fill=False, thickness=10), 6) * fade * 0.5
                flash = max(flash, math.exp(-age * 6.0))
                dots += mask_circle(hx_, hy_, 8 + 26 * min(age, 0.25)) * math.exp(-age * 9) * 2.5
    rings *= (yy > surf)
    img += fan[..., None] * SONAR * 0.30
    img += glow(dots[..., None] * np.array([0.8, 1.0, 1.0], np.float32), (2, 8, 22), (1, 0.6, 0.3)) + dots[..., None]
    img += rings[..., None] * np.array([0.55, 0.95, 1.0], np.float32) * 0.85
    img += glow(rings[..., None] * SONAR * 0.35, (4, 14), (0.6, 0.3))
    # --- submarine ---
    pts_h = S.place(hull, scx, scy, slen)
    pts_s = S.place(sail, scx, scy, slen)
    pts_f = S.place(fins, scx, scy, slen)
    m = mask_poly([pts_h, pts_s, pts_f])
    paint(img, m, (0.012, 0.013, 0.015), 1.0)
    comp = np.zeros((H, W), np.float32)
    for u in np.linspace(-0.36, 0.38, 7):
        x = int(scx + u * slen)
        cv2.line(comp, (x, int(scy - 30)), (x, int(scy + 30)), 1.0, 1, cv2.LINE_AA)
    img += (comp * m)[..., None] * SU * (0.18 + 0.4 * flash)
    rim = mask_polyline([pts_h, pts_s], thickness=2.2, closed=True)
    rim_int = 0.6 + 1.8 * flash
    img += rim[..., None] * SU * rim_int + glow(rim[..., None] * SU * rim_int * 0.6, (2, 8, 24), (0.8, 0.5, 0.3))
    img += flash * np.array([0.06, 0.10, 0.11], np.float32)
    if flash > 0.02:
        dx = int(round(math.sin(t * 90) * 12 * flash))
        dy = int(round(math.cos(t * 77) * 9 * flash))
        img = np.roll(np.roll(img, dx, 1), dy, 0)
    corner_tag(img, "B-59 · 声呐示意", 48, SAFE_TOP + 10, color=SONAR * 0.8, size=26)
    draw_text(img, "16:59  比尔号投下 5 枚", W - 48, SAFE_TOP + 6, size=30, weight="medium", color=US, anchor="rt",
              alpha=1.0 if t > hits[0] - 1.5 else 0.35)
    draw_text(img, "17:29  科尼号投下 5 枚", W - 48, SAFE_TOP + 50, size=30, weight="medium", color=US, anchor="rt",
              alpha=1.0 if (hits2 and t > hits2[0] - 1.5) else 0.35)
    draw_text(img, "训练深弹 · 手榴弹大小", W - 48, SAFE_TOP + 96, size=24, weight="regular", color=NEU_DIM, anchor="rt")
    if show_sub_label:
        draw_text(img, "B-59", scx - 0.42 * slen, scy + 60, size=30, weight="mono", color=SU, anchor="lt")
    if sub:
        subtitle(img, sub, y=1440)
    return img


# ============================================================================
# 6. hypothetical: underwater nuclear burst (thermal false colour)
# ============================================================================

def _splat(buf, xs, ys, wts):
    h, w = buf.shape
    xi = xs.astype(np.int32)
    yi = ys.astype(np.int32)
    ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    np.add.at(buf, (yi[ok], xi[ok]), wts[ok])


def _puffs(h, w, xs, ys, rs, wts, bins=(3, 6, 10, 15, 22, 32, 46)):
    """Sum of gaussian puffs, binned by radius (peak of each puff ~= its weight)."""
    D = np.zeros((h, w), np.float32)
    rs = np.asarray(rs)
    edges = [0] + [(a + b) / 2 for a, b in zip(bins[:-1], bins[1:])] + [1e9]
    for i, b in enumerate(bins):
        sel = (rs >= edges[i]) & (rs < edges[i + 1])
        if not np.any(sel):
            continue
        buf = np.zeros((h, w), np.float32)
        _splat(buf, xs[sel], ys[sel], np.asarray(wts, np.float32)[sel])
        sg = b * 0.6
        D += blur(buf, sg) * (2 * np.pi * sg * sg)
    return D


def burst_intensity(tb, seed=11, hw=(960, 540), wl=600, cx=270):
    """Stylised underwater burst at half resolution. tb in [0,1]."""
    h, w = hw
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    I = np.zeros((h, w), np.float32)
    nz = value_noise(h, w, 24, seed=seed + 1, octaves=5)
    nz2 = value_noise(h, w, 9, seed=seed + 2, octaves=3)
    under = np.clip((yy - wl) / 3.0, 0, 1)
    above = 1 - under
    # 1) underwater fireball / bubble
    k1 = ease_out(ramp(tb, 0.0, 0.22))
    fade1 = 1 - 0.7 * ramp(tb, 0.22, 0.9)
    by = wl + 170 - 55 * ramp(tb, 0.1, 0.5)
    br = 22 + 140 * k1
    rd = np.hypot(xx - cx, (yy - by) * 1.05)
    edge = br * (0.82 + 0.36 * nz)
    ball = np.clip(1 - rd / edge, 0, 1) ** 0.5
    core = np.clip(1 - rd / (edge * 0.5), 0, 1) ** 1.3
    I += (ball * 0.7 + core * 0.9) * fade1 * under
    ang = np.arctan2(yy - by, xx - cx)
    shafts = (0.5 + 0.5 * np.sin(ang * 9 + 2.2 * np.sin(ang * 3 + seed))) ** 4
    I += shafts * np.exp(-rd / (br * 2.6 + 1)) * 0.4 * fade1 * under * k1
    I += np.exp(-rd / (br * 1.7 + 1)) * 0.28 * fade1 * under
    # underside of the surface lit from below
    I += np.exp(-np.abs(yy - wl - 3) / 4) * np.exp(-np.abs(xx - cx) / (br * 2 + 30)) * 0.5 * fade1 * k1
    # 2) spray dome
    k2 = ease_out(ramp(tb, 0.05, 0.28))
    if k2 > 0:
        dome_fade = 1 - 0.85 * ramp(tb, 0.3, 0.6)
        rx = 40 + 165 * k2
        ry = 14 + 118 * k2
        dd = ((xx - cx) / rx) ** 2 + ((yy - wl) / ry) ** 2
        dome = np.clip(1 - dd, 0, 1) ** 0.35 * above * (0.65 + 0.55 * nz2)
        I += dome * dome_fade * (0.6 + 0.4 * k2)
    # 3) column of puffs
    k3 = ease_out(ramp(tb, 0.16, 0.62))
    top = wl - (30 + 330 * k3)
    if k3 > 0:
        r = np.random.default_rng(seed + 10)
        n = 1100
        u = r.random(n)
        j1, j2, j3 = r.standard_normal(n), r.random(n), r.random(n)
        ys = wl - (wl - top) * u ** 0.9
        half = 50 + 80 * u + 30 * k3
        xs = cx + j1 * half * 0.42 + np.sin(u * 17 + tb * 5) * 6
        rs = 5 + 11 * j2 + 8 * u
        wts = 0.16 + 0.16 * j3
        Dcol = _puffs(h, w, xs, ys, rs, wts) * above
    else:
        Dcol = np.zeros((h, w), np.float32)
    Dcap = np.zeros((h, w), np.float32)
    if k3 > 0:
        # 4) cauliflower cap
        k4 = ease_out(ramp(tb, 0.30, 0.85))
        if k4 > 0:
            r = np.random.default_rng(seed + 20)
            m = 600
            a = r.random(m) * 2 * np.pi
            rad = np.sqrt(r.random(m))
            crx, cry = 50 + 150 * k4, 30 + 62 * k4
            xs = cx + np.cos(a) * rad * crx * (1 + 0.05 * np.sin(tb * 4 + a * 3))
            ys = top + 14 + np.sin(a) * rad * cry * 0.8 - 26 * k4 * (1 - rad)
            rs = 7 + 14 * r.random(m) + 8 * k4
            wts = 0.20 + 0.18 * r.random(m)
            Dcap = _puffs(h, w, xs, ys, rs, wts) * (1 - 0.25 * ramp(tb, 0.85, 1.0))
    # 5) base surge rolling outward
    k5 = ease_out(ramp(tb, 0.40, 1.0))
    if k5 > 0:
        r = np.random.default_rng(seed + 30)
        m = 900
        side = np.sign(r.random(m) - 0.5)
        u = r.random(m)
        reach = 50 + 520 * k5
        xs = cx + side * (25 + u * reach)
        ys = wl - (6 + 58 * k5 * (1 - u) ** 0.7) * r.random(m) - 4
        rs = 6 + 12 * r.random(m) + 10 * k5 * (1 - u)
        wts = (0.18 + 0.2 * r.random(m)) * (1 - 0.45 * u)
        Dsur = _puffs(h, w, xs, ys, rs, wts)
    else:
        Dsur = np.zeros((h, w), np.float32)
    D = Dcol + Dcap + Dsur
    cloud = 1 - np.exp(-1.15 * D)
    Ds = cv2.GaussianBlur(D, (0, 0), 3)
    gy_ = cv2.Sobel(Ds, cv2.CV_32F, 0, 1, ksize=5)
    gx_ = cv2.Sobel(Ds, cv2.CV_32F, 1, 0, ksize=5)
    # light comes from below (the fireball): surfaces facing down/out glow, tops are shadowed
    lit = np.clip(0.78 + (gy_ * 0.018) + np.abs(gx_) * 0.005, 0.3, 1.25)
    I += cloud * lit * (0.66 + 0.40 * nz) * (0.85 + 0.40 * np.clip(D, 0, 2) / 2)
    # texture & spray specks
    I *= (0.92 + 0.16 * nz2)
    if k3 > 0:
        r = np.random.default_rng(seed + 40)
        m = 3000
        xs = cx + r.standard_normal(m) * (150 + 130 * k3)
        ys = wl - r.random(m) ** 1.6 * (500 * k3)
        sp = np.zeros((h, w), np.float32)
        _splat(sp, xs, ys, (r.random(m) * 1.1).astype(np.float32))
        I += cv2.GaussianBlur(sp, (0, 0), 0.7) * 0.7 * k3
    return I


def hypo_explosion(t, sub=None, tb=None, hypo_alpha=1.0, frame_scale=1.0, seed=11):
    if tb is None:
        tb = clamp01(t / 9.0)
    hh, hw = 960, 540
    wl = 600
    I = burst_intensity(tb, seed=seed, wl=wl)
    yy, xx = np.mgrid[0:hh, 0:hw].astype(np.float32)
    # ambient: sky faint, water faint
    I += 0.05 * np.exp(-np.abs(yy - wl) / 260)
    # ships: carrier left (lifted/tilted with surge), destroyer right
    lift = 18 * ease_out(ramp(tb, 0.45, 0.9))
    tilt_c = -9 * ease_out(ramp(tb, 0.5, 1.0))
    tilt_d = 14 * ease_out(ramp(tb, 0.45, 0.95))
    car = [S.place(p, 92, wl + 2 - lift * 0.6, 230, tilt_c) for p in S.carrier_side()]
    des = [S.place(p * np.array([-1, 1.0]), 462, wl + 2 - lift, 150, tilt_d) for p in S.destroyer_side()]
    shipm = mask_poly(car + des, h=hh, w=hw, ss=3)
    # silhouettes are cold (dark) and occlude; faint warm rim
    I = I * (1 - shipm) + shipm * 0.02
    rim = np.clip(shipm - cv2.erode(shipm, np.ones((3, 3), np.uint8)), 0, 1)
    I += rim * 0.25
    # map to thermal palette and upscale
    col = thermal_map(np.clip(I, 0, 1.4) / 1.25)
    col = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC)
    bright = np.clip(cv2.resize(I, (W, H)) - 0.85, 0, None)[..., None]
    col += glow(bright * np.array([1.0, 0.45, 0.8], np.float32), (6, 20, 60), (0.35, 0.25, 0.2))
    # scanlines & slight jitter, chroma shift
    yyF = grid()[1]
    col *= (0.94 + 0.06 * np.sin(yyF * math.pi / 2.0))[..., None]
    jit = int(round(math.sin(t * 37.0) * 2))
    col = np.roll(col, jit, 0)
    col = chroma_shift(col, 3)
    hypo_frame(col, t, alpha=hypo_alpha, scale=frame_scale)
    if sub:
        subtitle(col, sub)
    return col


# ============================================================================
# 7. hypothetical: escalation globe
# ============================================================================
LAUNCH = {
    "cuba": [(22.7, -83.0), (22.9, -82.7), (22.5, -79.9)],
    "us": [(47.5, -111.2), (41.15, -104.86), (48.4, -101.4), (34.7, -120.6), (44.65, -73.47), (39.1, -94.6)],
    "eu": [(52.4, 0.75), (40.8, 16.9), (38.4, 27.2)],
    "su": [(62.9, 40.6), (55.0, 37.5), (52.0, 24.0), (50.5, 30.5), (57.8, 28.3), (47.2, 39.7)],
}
TARGETS = {
    "us": [(38.9, -77.0), (40.7, -74.0), (41.9, -87.6), (29.8, -95.4), (33.7, -84.4), (42.4, -71.1), (47.6, -122.3),
           (34.1, -118.2), (39.7, -105.0)],
    "su": [(55.75, 37.6), (59.9, 30.3), (50.45, 30.5), (53.9, 27.6), (56.3, 44.0), (48.7, 44.5), (54.7, 20.5)],
    "eu": [(51.5, -0.1), (48.85, 2.35), (41.9, 12.5), (50.7, 7.1), (52.5, 13.4), (40.4, -3.7)],
}


def _escalation_list(seed=3):
    rng = np.random.default_rng(seed)
    out = []
    # (launch_lat, launch_lon, tgt_lat, tgt_lon, t_launch, colour_key)
    t0 = 0.0
    for (la, lo) in LAUNCH["cuba"]:
        tg = TARGETS["us"][rng.integers(0, 6)]
        out.append((la, lo, tg[0], tg[1], t0 + rng.uniform(0, 0.6), "hot"))
    for (la, lo) in LAUNCH["us"]:
        for _ in range(2):
            tg = TARGETS["su"][rng.integers(0, len(TARGETS["su"]))]
            out.append((la, lo, tg[0], tg[1], 1.2 + rng.uniform(0, 1.4), "hot"))
    for (la, lo) in LAUNCH["eu"]:
        tg = TARGETS["su"][rng.integers(0, len(TARGETS["su"]))]
        out.append((la, lo, tg[0], tg[1], 2.0 + rng.uniform(0, 1.0), "hot"))
    for (la, lo) in LAUNCH["su"]:
        for _ in range(3):
            if rng.random() < 0.6:
                tg = TARGETS["us"][rng.integers(0, len(TARGETS["us"]))]
            else:
                tg = TARGETS["eu"][rng.integers(0, len(TARGETS["eu"]))]
            out.append((la, lo, tg[0], tg[1], 2.4 + rng.uniform(0, 2.0), "hot"))
    return out


ESC = _escalation_list()


def hypo_globe(t, sub=None, lon_from=-50, lon_to=-6, dur=10.0, hypo_alpha=1.0):
    k = ease_in_out(ramp(t, 0, dur))
    lon0 = lerp(lon_from, lon_to, k)
    cam = G.Cam(lat0=50, lon0=lon0, R=780, cx=W / 2, cy=1010)
    img = canvas(np.array([0.012, 0.004, 0.016], np.float32))
    disk = G.disk_mask(cam)
    img += disk[..., None] * np.array([0.030, 0.008, 0.030], np.float32)
    land, zz = G.land_mask(cam)
    img += (land * (0.35 + 0.65 * zz))[..., None] * np.array([0.10, 0.025, 0.075], np.float32)
    grat = G.graticule_mask(cam, step=15, thickness=1.0)
    img += grat[..., None] * HYPO * 0.08
    coast = G.coast_mask(cam, thickness=1.5)
    img += coast[..., None] * np.array([1.0, 0.35, 0.75], np.float32) * 0.6
    img += G.city_lights(cam, gain=0.45)[..., None] * np.array([1.0, 0.55, 0.35], np.float32) * 0.5
    img += G.atmosphere(cam, np.array([1.0, 0.2, 0.6], np.float32), strength=0.5, width=0.05)
    # launches and arcs
    arcs = np.zeros((H, W), np.float32)
    heads = np.zeros((H, W), np.float32)
    flares = np.zeros((H, W), np.float32)
    tt = t * 0.75
    n_active = 0
    for (la, lo, tla, tlo, tl, _) in ESC:
        if tt < tl:
            continue
        n_active += 1
        dist = G.gc_distance_km(la, lo, tla, tlo)
        flight = 1.2 + dist / 4000.0
        prog = clamp01((tt - tl) / flight)
        hgt = 0.03 + 0.11 * min(1.0, dist / 8000)
        pts, ts = G.arc_points(la, lo, tla, tlo, height=hgt, n=140, t_end=max(0.02, prog))
        sx, sy, vis, _ = cam.project(pts)
        polys = G.draw_polylines_vis(sx, sy, vis, 1.5)
        if polys:
            arcs = np.maximum(arcs, mask_polyline(polys, thickness=1.8, ss=1))
        if prog < 1 and vis[-1]:
            heads += mask_circle(sx[-1], sy[-1], 3.5, ss=1)
        # launch flare
        age = tt - tl
        if age < 1.6:
            p0 = G.ll2v(np.array(la), np.array(lo))
            fx, fy, fv, _ = cam.project(p0[None])
            if fv[0]:
                flares += mask_circle(float(fx[0]), float(fy[0]), 5 + 10 * age, ss=1) * (1 - age / 1.6)
                st = np.zeros((H, W), np.float32)
                cv2.line(st, (int(fx[0]), int(fy[0])), (int(fx[0]), int(fy[0] - 70 * min(1, age * 2))), 1.0, 2, cv2.LINE_AA)
                flares += st * (1 - age / 1.6)
    arc_col = np.array([1.0, 0.35, 0.55], np.float32)
    img += arcs[..., None] * arc_col * 0.75 + glow(arcs[..., None] * arc_col * 0.35, (2, 7, 20), (0.7, 0.5, 0.3))
    img += glow(heads[..., None] * np.array([1.0, 0.85, 0.6], np.float32) * 1.5, (2, 6, 16), (1, 0.6, 0.3)) + heads[..., None]
    img += glow(flares[..., None] * np.array([1.0, 0.75, 0.4], np.float32) * 1.4, (3, 10, 30), (1, 0.6, 0.35))
    # countdown
    secs = max(0, int(900 - t * 37))
    cd = f"T-{secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}"
    draw_text(img, cd, W - 60, SAFE_TOP + 70, size=44, weight="monobold", color=(1.0, 0.55, 0.8), anchor="rt", glow=0.4)
    draw_text(img, f"弹道 {n_active:02d}", W - 60, SAFE_TOP + 126, size=28, weight="mono", color=(1.0, 0.6, 0.85),
              anchor="rt", alpha=0.85)
    yyF = grid()[1]
    img *= (0.94 + 0.06 * np.sin(yyF * math.pi / 2.0))[..., None]
    img = chroma_shift(img, 2)
    hypo_frame(img, t, alpha=hypo_alpha)
    if sub:
        subtitle(img, sub)
    return img


# ============================================================================
# 8. surfaced: top-down, searchlights, aircraft, cannon splashes beside the sub
# ============================================================================

@functools.lru_cache(maxsize=1)
def _haze_tex():
    return cv2.GaussianBlur(cv2.resize(value_noise(H // 4, W // 4, 18, seed=4, octaves=3), (W, H)), (0, 0), 6)


def _wedge(src, dst, w0, w1, h=H, w=W):
    """Soft light wedge from src (width w0) to dst (width w1). Returns intensity & 'along' fraction."""
    xx, yy = grid(h, w)
    dx, dy = dst[0] - src[0], dst[1] - src[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = xx - src[0], yy - src[1]
    along = (px * ux + py * uy) / L
    perp = np.abs(-px * uy + py * ux)
    width = w0 + (w1 - w0) * np.clip(along, 0, 1.3)
    prof = np.exp(-(perp / np.maximum(width, 1)) ** 2 * 2.2)
    inside = (along > 0) & (along < 1.35)
    tail = np.clip(1 - (along - 1.0) / 0.35, 0, 1)
    return prof * inside * np.where(along > 1, tail, 1.0), along


def _splash_sprite(cx, cy, size, f, ang0=0.0):
    m = mask_circle(cx, cy, 2.5 + 2.5 * f)
    lines = np.zeros((H, W), np.float32)
    for k in range(5):
        a = ang0 + k * (2 * math.pi / 5) + 0.4 * math.sin(k * 3.1)
        L = size * (0.35 + 0.35 * math.sin(k * 1.7) ** 2)
        cv2.line(lines, (int(cx), int(cy)), (int(cx + math.cos(a) * L), int(cy + math.sin(a) * L)), 1.0, 1, cv2.LINE_AA)
    ring = mask_circle(cx, cy, size * 1.1, fill=False, thickness=1.2)
    return m * f + lines * f * 0.7 + ring * f * 0.35


SUB_POS = (540, 990, 600, -14.0)  # cx, cy, length px, heading deg


def surface_topdown(t, sub=None, plane_t=None, lights=1.0, beams_on=(1, 1, 1), plane_on=True, splashes=True,
                    labels=True, pass_mode="strafe"):
    img = canvas(np.array([0.004, 0.007, 0.012], np.float32))
    xx, yy = grid()
    # stylised sea: faint wave contour lines + soft noise
    tile = noise_tile(512, 38, 21, 3)
    n1 = scroll_noise(H, W, tile, t * 6, t * 2.5, zoom=1.3)
    n2 = scroll_noise(H, W, tile, -t * 4 + 200, t * 5 + 100, zoom=0.7)
    hgt = n1 * 0.6 + n2 * 0.4
    th = math.radians(28)
    wave = np.sin((xx * math.cos(th) + yy * math.sin(th)) * 0.11 + hgt * 3.5 + t * 1.6)
    contour = np.clip((wave - 0.86) / 0.14, 0, 1) ** 2 * np.clip((n2 - 0.35) * 2.5, 0, 1)
    img += contour[..., None] * np.array([0.008, 0.016, 0.026], np.float32)
    scx, scy, slen, sang = SUB_POS
    sa = math.radians(sang)
    hdir = np.array([math.cos(sa), math.sin(sa)])
    nrm = np.array([-math.sin(sa), math.cos(sa)])
    # ships: (cx, cy, heading, length)
    ships = [(170, 450, 35, 520), (960, 1560, 212, 520), (1090, 330, 148, 480)]
    cold = np.array([0.70, 0.85, 1.0], np.float32)
    beam_sum = np.zeros((H, W), np.float32)
    srcs = []
    for i, (cx, cy, ang, L) in enumerate(ships):
        a = math.radians(ang)
        src = (cx + math.cos(a) * L * 0.22, cy + math.sin(a) * L * 0.22)
        srcs.append(src)
        if not beams_on[i % len(beams_on)]:
            continue
        sw = math.sin(t * 0.5 + i * 1.9) * 26
        dst = (scx + hdir[0] * sw * 2, scy + hdir[1] * sw * 2 + math.cos(t * 0.45 + i) * 10)
        wdg, along = _wedge(src, dst, 6, 70)
        ramp_al = 0.30 + 0.70 * np.clip(along, 0, 1) ** 1.5
        beam_sum += wdg * ramp_al * (0.92 + 0.08 * math.sin(t * 2.1 + i))
    beam_sum *= lights
    haze = _haze_tex()
    img += (beam_sum * (0.6 + 0.4 * haze))[..., None] * cold * 0.20
    img += glow((beam_sum * 0.25)[..., None] * cold, (6, 24), (0.4, 0.25))
    sparkle = contour * beam_sum
    img += sparkle[..., None] * cold * 0.45
    pool = np.exp(-(((xx - scx) * hdir[0] + (yy - scy) * hdir[1]) / 360) ** 2
                  - (((xx - scx) * nrm[0] + (yy - scy) * nrm[1]) / 140) ** 2) * lights
    img += pool[..., None] * cold * 0.10
    # sub: lit steel
    hull, sail = S.sub_top()
    ph = S.place(hull, scx, scy, slen, sang, flip_y=False)
    ps = S.place(sail, scx + 8, scy - 2, slen, sang, flip_y=False)
    subm = mask_poly([ph])
    sailm = mask_poly([ps])
    wake = cv2.GaussianBlur(cv2.dilate(subm, np.ones((13, 13), np.uint8)) - subm, (0, 0), 4)
    img += np.clip(wake, 0, 1)[..., None] * np.array([0.5, 0.6, 0.7], np.float32) * (0.10 + 0.5 * pool[..., None])
    across = ((xx - scx) * nrm[0] + (yy - scy) * nrm[1]) / (slen * 0.042)
    curv = np.clip(1 - np.abs(across), 0, 1) ** 0.5
    hull_col = np.array([0.03, 0.034, 0.04], np.float32) + (curv * pool)[..., None] * np.array([0.16, 0.17, 0.19], np.float32)
    img = img * (1 - subm[..., None]) + hull_col * subm[..., None]
    casing = mask_polyline([S.place(np.array([[-0.42, 0.0], [0.45, 0.0]]), scx, scy, slen, sang, flip_y=False)],
                           thickness=1.2)
    img += (casing * subm)[..., None] * np.array([0.10, 0.11, 0.12], np.float32) * (0.4 + pool[..., None])
    img = img * (1 - sailm[..., None]) + sailm[..., None] * (np.array([0.07, 0.075, 0.085], np.float32)
                                                             + pool[..., None] * np.array([0.25, 0.26, 0.29], np.float32))
    rim = mask_polyline([ph], thickness=1.4, closed=True)
    img += rim[..., None] * SU * 0.45
    # destroyers: solid, rim-lit, deck lights
    dh, dsup = S.destroyer_top()
    for (cx, cy, ang, L) in ships:
        p = S.place(dh * np.array([1.0, 1.5]), cx, cy, L, ang, flip_y=False)
        m = mask_poly([p])
        img = img * (1 - m[..., None]) + m[..., None] * np.array([0.035, 0.042, 0.055], np.float32)
        for q in dsup:
            pm = mask_poly([S.place(q * np.array([1.0, 1.4]), cx, cy, L, ang, flip_y=False)])
            img = img * (1 - pm[..., None]) + pm[..., None] * np.array([0.07, 0.08, 0.10], np.float32)
        r = mask_polyline([p], thickness=1.6, closed=True)
        img += r[..., None] * US * 0.55
    for i, src in enumerate(srcs):
        if not beams_on[i % len(beams_on)]:
            continue
        lm = mask_circle(src[0], src[1], 6)
        img += glow(lm[..., None] * cold * 3.0 * lights, (3, 12, 36), (1, 0.6, 0.35)) + lm[..., None] * lights
    # aircraft low pass; cannon splashes land alongside (not on) the boat
    if plane_t is None:
        plane_t = t
    pk = (plane_t % 6.0) / 6.0
    if pass_mode == "strafe":
        # flies alongside the hull (stern -> bow side offset), firing past the boat
        off = -nrm * 150
        path0 = np.array([scx, scy]) - hdir * 1100 + off
        path1 = np.array([scx, scy]) + hdir * 1100 + off
    else:
        # low overflight across the conning tower
        path0, path1 = np.array([1350.0, 700.0]), np.array([-350.0, 1220.0])
    pos = path0 + (path1 - path0) * pk
    pang = math.degrees(math.atan2(path1[1] - path0[1], path1[0] - path0[0]))
    if splashes and pass_mode == "strafe":
        spl = np.zeros((H, W), np.float32)
        for j in range(12):
            u = (j - 5.5) / 5.5
            p = np.array([scx, scy]) + hdir * u * 300 - nrm * (215 + 12 * math.sin(j * 2.1))
            # each round lands as the plane approaches that point
            pj = 0.5 + (u * 300) / 2200.0
            age = (pk - pj + 0.10) * 6.0
            if 0 < age < 1.4:
                f = 1 - age / 1.4
                spl += _splash_sprite(p[0], p[1], 7 + 12 * age, f, ang0=j)
        img += spl[..., None] * np.array([0.92, 0.96, 1.0], np.float32)
        img += glow(spl[..., None] * cold * 0.8, (2, 7, 18), (0.8, 0.4, 0.2))
    if plane_on:
        pp = S.plane_top()
        sc = 230
        shadow = mask_poly([S.place(q, pos[0] + 50, pos[1] + 65, sc, pang, flip_y=False) for q in pp])
        img *= (1 - 0.6 * cv2.GaussianBlur(shadow, (0, 0), 6))[..., None]
        fwd = np.array([math.cos(math.radians(pang)), math.sin(math.radians(pang))])
        side = np.array([-fwd[1], fwd[0]])
        # landing light cone ahead
        wdg, along = _wedge(pos + fwd * 100, pos + fwd * 520, 8, 90)
        img += (wdg * (1 - np.clip(along, 0, 1)) ** 1.2)[..., None] * cold * 0.22
        plane = mask_poly([S.place(q, pos[0], pos[1], sc, pang, flip_y=False) for q in pp])
        body_col = np.array([0.075, 0.085, 0.10], np.float32)
        img = img * (1 - plane[..., None]) + plane[..., None] * body_col
        prim = np.clip(plane - cv2.erode(plane, np.ones((3, 3), np.uint8)), 0, 1)
        img += prim[..., None] * US * 0.7
        for off, c, rr in [(fwd * 112, cold, 5), (fwd * 30 + side * 150, np.array([0.3, 1.0, 0.5], np.float32), 3),
                           (fwd * 30 - side * 150, np.array([1.0, 0.35, 0.3], np.float32), 3)]:
            q = pos + off
            lm = mask_circle(q[0], q[1], rr)
            img += glow(lm[..., None] * c * 2.2, (2, 8, 22), (1, 0.5, 0.3)) + lm[..., None] * c
    if labels:
        corner_tag(img, "20:50  B-59 浮出水面 · 俯视示意", 48, SAFE_TOP + 10, color=NEU, size=26)
        p = np.array([scx, scy]) - hdir * 330 - nrm * 60
        draw_text(img, "B-59", p[0], p[1], size=32, weight="mono", color=SU, anchor="mm")
        draw_text(img, "美舰探照灯", 300, 640, size=26, weight="medium", color=US, anchor="lt", alpha=0.9)
        q = np.array([scx, scy]) - hdir * 120 - nrm * 285
        draw_text(img, "机炮弹着点：艇旁水面", q[0], q[1], size=26, weight="medium", color=NEU, anchor="mm", alpha=0.9)
    if sub:
        subtitle(img, sub, y=1440)
    return img
