"""Shot renderers for the full film. Signature: fn(t, D, cues) -> float32 HxWx3 (pre-finish, no subtitles).

t: seconds since shot start; D: shot duration; cues: {line_id: (start, end)} in shot-local seconds.
"""
import functools
import math
import os

import cv2
import numpy as np
from PIL import Image

import globe as G
import scenes as SC
import shapes as S
from engine import (ALERT, ASSETS, BG, H, HYPO, NEU, NEU_DIM, SAFE_TOP, SONAR, SU, SU_DIM, US, US_DIM, W, blit_mask,
                    blur, canvas, chroma_shift, clamp01, corner_tag, dashed, draw_text, ease_in, ease_in_out,
                    ease_out, glow, grid, hypo_frame, lerp, mask_circle, mask_ellipse, mask_poly, mask_polyline,
                    noise_tile, paint, ramp, scroll_noise, text_size, thermal_map, value_noise, vgrad)

CONTENT_BOTTOM = 1240  # keep key graphics above the subtitle band


def cue(cues, lid, which=0, default=None):
    if lid in cues:
        return cues[lid][which]
    return default


@functools.lru_cache(maxsize=16)
def _bg(top, bot, power=1.2):
    return vgrad(np.array(top, np.float32), np.array(bot, np.float32), power=power)


def bg(top=(0.010, 0.014, 0.024), bot=(0.020, 0.030, 0.050), power=1.2):
    return _bg(tuple(top), tuple(bot), power).copy()


def fade_text(img, text, x, y, t, t0, size=40, weight="bold", color=NEU, anchor="mm", dur=0.5, rise=18, alpha=1.0,
              tracking=0.0, glow_amt=0.0, shadow=0.0):
    a = ease_out(ramp(t, t0, t0 + dur)) * alpha
    if a <= 0:
        return
    draw_text(img, text, x, y + (1 - a) * rise, size=size, weight=weight, color=color, alpha=a, anchor=anchor,
              tracking=tracking, glow=glow_amt, shadow=shadow)


def panel(img, x0, y0, x1, y1, alpha=1.0, color=(0.015, 0.025, 0.04), edge=US_DIM, edge_a=0.6):
    m = np.zeros((H, W), np.float32)
    cv2.rectangle(m, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, -1)
    paint(img, m, color, 0.88 * alpha)
    e = np.zeros((H, W), np.float32)
    cv2.rectangle(e, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, 1, cv2.LINE_AA)
    paint(img, e, edge, edge_a * alpha)


def line(img, p0, p1, color, alpha=1.0, th=2, glow_amt=0.0):
    m = np.zeros((H, W), np.float32)
    cv2.line(m, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 1.0, th, cv2.LINE_AA)
    img += m[..., None] * np.asarray(color, np.float32) * alpha
    if glow_amt > 0:
        img += glow(m[..., None] * np.asarray(color, np.float32) * glow_amt * alpha, (3, 10), (0.7, 0.35))


def particles_underwater(img, t, n=260, seed=3, speed=40.0, color=(0.35, 0.55, 0.6), alpha=0.5, rise=True):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, W, n)
    y0 = rng.uniform(0, H, n)
    sz = rng.uniform(0.8, 2.4, n)
    sp = rng.uniform(0.4, 1.0, n) * speed
    y = (y0 - (1 if rise else -1) * sp * t) % H
    buf = np.zeros((H, W), np.float32)
    xi, yi = x.astype(int), y.astype(int)
    np.add.at(buf, (yi, xi), sz)
    buf = cv2.GaussianBlur(buf, (0, 0), 1.2)
    img += buf[..., None] * np.asarray(color, np.float32) * alpha


# ============================================================================
# 1  cold open / black text / title
# ============================================================================

def cold_open(t, D, cues):
    tb = 0.12 + 0.55 * clamp01(t / max(D - 0.25, 0.1))
    img = SC.hypo_explosion(t, tb=tb, seed=11)
    if t > D - 0.25:  # flash white for the cut
        k = ramp(t, D - 0.25, D - 0.08)
        img = img * (1 - k) + k * np.array([1.0, 0.95, 0.98], np.float32)
    return img


def open_text(t, D, cues):
    img = canvas(np.array([0.0, 0.0, 0.0], np.float32))
    # a faint horizon emerging
    xx, yy = grid()
    k = ease_in_out(ramp(t, 0.5, D))
    hl = np.exp(-((yy - 980) / 1.5) ** 2) * np.clip(1 - np.abs(xx - W / 2) / (W * 0.55), 0, 1)
    img += hl[..., None] * np.array([0.15, 0.25, 0.4], np.float32) * k
    fade_text(img, "1962 · 10 · 27", W / 2, 900, t, cue(cues, "a02", 0, 3.0), size=34, weight="mono", color=NEU_DIM,
              alpha=0.8, tracking=0.15)
    return img


def title(t, D, cues):
    img = SC.title_card(t + 0.3)
    a = ramp(t, D - 0.4, D)
    return img * (1 - a)


# ============================================================================
# 2  thirteen days
# ============================================================================

def u2(t, D, cues):
    img = SC.u2_scene(t, dur=D)
    if t < 0.4:
        img *= ease_out(t / 0.4)
    return img


def globe_range(t, D, cues):
    return SC.globe_range(t * (6.0 / max(D, 3.0)) + 0.6)


QUAR_CENTER = (23.0, -79.5)


def blockade(t, D, cues):
    img = SC.globe_range(7.0)
    # dim the range rings slightly by overlaying the quarantine arc on top
    cam = G.Cam(lat0=29.5, lon0=-81.0, R=1750, cx=W / 2, cy=930)
    k = ease_in_out(ramp(t, 0.3, 2.6))
    # schematic quarantine arc: north-east of Cuba
    angs = np.linspace(-15, 125, 160)
    pts = []
    for b in angs[: max(2, int(len(angs) * k))]:
        d = 900.0 / G.R_EARTH
        la1, lo1 = math.radians(QUAR_CENTER[0]), math.radians(QUAR_CENTER[1])
        br = math.radians(b)
        la2 = math.asin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * math.cos(br))
        lo2 = lo1 + math.atan2(math.sin(br) * math.sin(d) * math.cos(la1), math.cos(d) - math.sin(la1) * math.sin(la2))
        pts.append(G.ll2v(np.array(math.degrees(la2)), np.array(math.degrees(lo2))))
    pts = np.array(pts)
    sx, sy, vis, _ = cam.project(pts)
    poly = np.stack([sx, sy], 1)
    m = mask_polyline(dashed(poly, 18, 12), thickness=3)
    img += m[..., None] * US * 1.1 + glow(m[..., None] * US * 0.5, (3, 12, 30), (0.8, 0.4, 0.25))
    # US ships on the line
    for j, u in enumerate(np.linspace(0.1, 0.9, 6)):
        if k < u:
            continue
        i = int(u * (len(poly) - 1))
        d = mask_circle(poly[i, 0], poly[i, 1], 6)
        img += glow(d[..., None] * US * 1.5, (2, 7), (1, 0.5)) + d[..., None] * US
    # Soviet ships approaching from NE and stopping at the line
    for j in range(3):
        a0 = 0.8 + j * 0.35
        p = ramp(t, a0, a0 + 3.0)
        start = np.array([W + 60 - j * 40, 160 + j * 90])
        i = int((0.55 + j * 0.12) * (len(poly) - 1)) if len(poly) > 3 else 0
        stop = poly[i] + np.array([40, -30])
        pos = start + (stop - start) * ease_out(p)
        d = mask_circle(pos[0], pos[1], 6)
        img += glow(d[..., None] * SU * 1.4, (2, 7), (1, 0.5)) + d[..., None] * SU
    fade_text(img, "“隔离”＝海上封锁", W / 2, 300, t, 1.0, size=50, weight="black", color=NEU)
    fade_text(img, "隔离线（示意）", poly[len(poly) // 3, 0] + 120 if len(poly) > 3 else 700,
              poly[len(poly) // 3, 1] - 40 if len(poly) > 3 else 500, t, 2.4, size=28, weight="medium", color=US)
    fade_text(img, "1962.10.22  肯尼迪电视讲话", W / 2, 370, t, 1.3, size=28, weight="medium", color=NEU_DIM)
    return img


def defcon(t, D, cues):
    img = bg()
    fade_text(img, "DEFCON", W / 2, 360, t, 0.0, size=110, weight="monobold", color=NEU, tracking=0.08)
    fade_text(img, "美军战备等级 · 数字越小，越接近开战", W / 2, 470, t, 0.3, size=32, weight="medium", color=NEU_DIM)
    xs = [W / 2 + (i - 2) * 175 for i in range(5)]
    lvl = 5
    if t > 0.8:
        lvl = 3
    if t > 1.9:
        lvl = 2
    for i, n in enumerate([5, 4, 3, 2, 1]):
        x = xs[i]
        active = n == lvl
        col = ALERT if (active and n <= 2) else (US if active else NEU_DIM)
        r = 70
        ring = mask_circle(x, 720, r, fill=False, thickness=3)
        img += ring[..., None] * col * (1.0 if active else 0.35)
        if active:
            img += glow(ring[..., None] * col * 0.8, (4, 14, 36), (1, 0.5, 0.3))
        draw_text(img, str(n), x, 720, size=96, weight="monobold", color=col, alpha=1.0 if active else 0.4, anchor="mm")
    draw_text(img, "平时", xs[0], 830, size=28, weight="regular", color=NEU_DIM, anchor="mt")
    draw_text(img, "战争", xs[4], 830, size=28, weight="regular", color=NEU_DIM, anchor="mt")
    if lvl == 2:
        fade_text(img, "1962.10.24 · 美国战略空军 → DEFCON 2", W / 2, 960, t, 1.9, size=34, weight="bold", color=ALERT * 0.6 + NEU * 0.4)
    return img


def _window(img, cx, cy, w, h, col, a=1.0, flicker=0.0):
    m = np.zeros((H, W), np.float32)
    cv2.rectangle(m, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), 1.0, -1)
    lightc = np.asarray(col, np.float32) * (0.55 + 0.1 * flicker)
    img += m[..., None] * lightc * 0.5 * a
    img += glow(m[..., None] * lightc * 0.6 * a, (8, 30, 80), (0.6, 0.4, 0.3))
    # mullions
    mm = np.zeros((H, W), np.float32)
    cv2.line(mm, (int(cx), int(cy - h / 2)), (int(cx), int(cy + h / 2)), 1.0, 5)
    cv2.line(mm, (int(cx - w / 2), int(cy - h / 6)), (int(cx + w / 2), int(cy - h / 6)), 1.0, 5)
    paint(img, mm, (0.01, 0.012, 0.016), 0.95 * a)
    e = np.zeros((H, W), np.float32)
    cv2.rectangle(e, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), 1.0, 3)
    paint(img, e, (0.01, 0.012, 0.016), a)


def rooms(t, D, cues):
    img = bg((0.006, 0.008, 0.014), (0.012, 0.016, 0.026))
    a = ease_out(ramp(t, 0, 0.8))
    _window(img, 290, 640, 260, 330, US, a, math.sin(t * 7) * 0.3)
    _window(img, 790, 640, 260, 330, SU, a, math.sin(t * 6.3 + 1) * 0.3)
    draw_text(img, "华盛顿 · 白宫", 290, 850, size=34, weight="bold", color=US, alpha=a, anchor="mt")
    draw_text(img, "莫斯科 · 克里姆林宫", 790, 850, size=34, weight="bold", color=SU, alpha=a, anchor="mt")
    # steps descending toward the middle: both sides looking for a way down
    s = cue(cues, "b06", 0, 0.0)
    k = ease_in_out(ramp(t, s + 2.2, s + 4.6))
    if k > 0:
        for side, col, x0 in ((-1, US, 420), (1, SU, 660)):
            pts = []
            x, y = x0, 900
            for i in range(5):
                pts += [(x, y), (x - side * 36, y)]
                x -= side * 36
                y += 34
                pts.append((x, y))
            pts = np.array(pts, np.float32)
            n = max(2, int(len(pts) * k))
            m = mask_polyline([pts[:n]], thickness=3)
            img += m[..., None] * col * 0.9 + glow(m[..., None] * col * 0.4, (3, 10), (0.6, 0.3))
        fade_text(img, "找台阶", W / 2, 1110, t, s + 3.6, size=44, weight="black", color=NEU)
    return img


SUB_ROUTE = [(69.2, 33.4), (70.5, 18.0), (66.0, 2.0), (61.0, -12.0), (52.0, -28.0), (42.0, -45.0), (32.0, -58.0),
             (25.5, -66.0)]


def _route_points(n=200):
    pts = []
    for (a, b), (c, d) in zip(SUB_ROUTE[:-1], SUB_ROUTE[1:]):
        for u in np.linspace(0, 1, 30, endpoint=False):
            pts.append((lerp(a, c, u), lerp(b, d, u)))
    pts.append(SUB_ROUTE[-1])
    return np.array(pts)


def subs(t, D, cues):
    k = ease_in_out(ramp(t, 0, D))
    cam = G.Cam(lat0=lerp(52, 40, k), lon0=lerp(-5, -38, k), R=880, cx=W / 2, cy=860)
    img = canvas(np.array([0.008, 0.012, 0.02], np.float32))
    disk = G.disk_mask(cam)
    img += disk[..., None] * np.array([0.010, 0.020, 0.036], np.float32)
    land, zz = G.land_mask(cam)
    img += land[..., None] * np.array([0.030, 0.040, 0.055], np.float32)
    grat = G.graticule_mask(cam, step=15, thickness=1.0)
    paint(img, grat, US_DIM, 0.08)
    coast = G.coast_mask(cam, thickness=1.5)
    img += coast[..., None] * NEU * 0.45
    img += G.atmosphere(cam, np.array([0.25, 0.5, 0.9], np.float32), strength=0.35, width=0.05)
    route = _route_points()
    v = G.ll2v(route[:, 0], route[:, 1])
    sx, sy, vis, _ = cam.project(v)
    prog = ease_in_out(ramp(t, 0.6, D - 0.6))
    n = max(2, int(len(route) * prog))
    m = mask_polyline(dashed(np.stack([sx[:n], sy[:n]], 1), 10, 10), thickness=2)
    img += m[..., None] * SU * 0.6
    for j in range(4):
        idx = max(0, n - 1 - j * 9)
        p = (sx[idx], sy[idx])
        d = mask_circle(p[0], p[1], 7)
        img += glow(d[..., None] * SU * 1.5, (2, 8, 20), (1, 0.6, 0.3)) + d[..., None] * SU
    fade_text(img, "4 艘狐步级柴电潜艇 · 10 月 1 日出发", W / 2, SAFE_TOP + 70, t, 0.4, size=36, weight="bold", color=SU)
    fade_text(img, "每艘带 1 枚核鱼雷", W / 2, SAFE_TOP + 125, t, 1.2, size=32, weight="medium", color=NEU)
    s8 = cue(cues, "b08", 0, D - 2.0)
    fade_text(img, "美国海军：不知道艇上有核武器", W / 2, 1150, t, s8, size=34, weight="bold", color=US)
    return img


# ============================================================================
# 3  black saturday
# ============================================================================

def timeline(t, D, cues):
    return SC.timeline(t + 0.2, active=3)


def _sky(seed=1):
    img = bg((0.004, 0.006, 0.014), (0.02, 0.028, 0.045), power=1.6)
    return img


def ev_cuba(t, D, cues):
    img = _sky()
    xx, yy = grid()
    # ground line
    gl = 1180
    img[gl:] *= 0.4
    line(img, (0, gl), (W, gl), NEU_DIM, 0.35)
    # U-2 flying left->right high up
    px = lerp(-80, W + 80, clamp01(t / 7.0))
    py = 420
    hit = 3.2
    if t > hit:
        dt = t - hit
        px = lerp(-80, W + 80, hit / 7.0) + dt * 60
        py = 420 + 120 * dt ** 1.6
    wing = np.array([[-0.5, 0.0], [0.5, 0.0]])
    m = mask_polyline([S.place(wing, px, py, 160, 8 * clamp01((t - hit) / 2) if t > hit else 0)], thickness=4)
    m += mask_polyline([S.place(np.array([[0, -0.02], [0, 0.5]]), px, py, 120, 90)], thickness=4)
    img += m[..., None] * US * 0.9
    draw_text(img, "U-2", px, py - 40, size=26, weight="mono", color=US, anchor="mb", alpha=0.9 if t < hit + 1 else 0.5)
    # SAM streak (amber) from the ground
    launch = 1.2
    if t > launch:
        u = clamp01((t - launch) / (hit - launch))
        x0, y0 = 380, gl
        x1, y1 = lerp(-80, W + 80, hit / 7.0), 420
        pts = []
        for s in np.linspace(0, u, 60):
            pts.append((lerp(x0, x1, s) + math.sin(s * 3) * 30 * (1 - s), lerp(y0, y1, ease_out(s))))
        pts = np.array(pts)
        tr = mask_polyline([pts], thickness=3)
        fade = 1.0 if t < hit + 0.3 else max(0.0, 1 - (t - hit - 0.3) / 2.5)
        img += tr[..., None] * SU * fade + glow(tr[..., None] * SU * 0.6 * fade, (3, 12), (0.8, 0.4))
        if t < hit:
            hd = mask_circle(pts[-1, 0], pts[-1, 1], 6)
            img += glow(hd[..., None] * SU * 2.5, (3, 10, 30), (1, 0.6, 0.3))
    if t > hit:
        dt = t - hit
        fl = math.exp(-dt * 2.5)
        b = mask_circle(lerp(-80, W + 80, hit / 7.0), 420, 20 + 120 * min(dt, 0.6))
        img += glow(b[..., None] * np.array([1.0, 0.8, 0.5], np.float32) * 2.0 * fl, (6, 20, 60), (1, 0.6, 0.4))
    fade_text(img, "古巴上空", 70, SAFE_TOP + 40, t, 0.2, size=60, weight="black", color=NEU, anchor="lt")
    fade_text(img, "萨姆导弹 ＝ 苏联地对空导弹", 70, SAFE_TOP + 130, t, 0.8, size=32, weight="medium", color=SU, anchor="lt")
    s3 = cue(cues, "c03", 0, D - 3)
    if t > s3:
        panel(img, 70, 900, W - 70, 1090, alpha=ease_out(ramp(t, s3, s3 + 0.4)), edge=SU_DIM)
        fade_text(img, "下令开火：驻古巴苏军现场指挥员", W / 2, 955, t, s3 + 0.1, size=36, weight="bold", color=NEU)
        fade_text(img, "未经莫斯科批准（据后来的研究）", W / 2, 1025, t, s3 + 0.4, size=30, weight="medium", color=SU)
    return img


def ev_arctic(t, D, cues):
    img = bg((0.004, 0.008, 0.016), (0.008, 0.016, 0.03))
    xx, yy = grid()
    cx, cy = W / 2, 700
    # aurora band
    au = np.exp(-((yy - 360 - 30 * np.sin(xx * 0.006 + t * 0.5)) / 60) ** 2)
    au *= (0.6 + 0.4 * np.sin(xx * 0.02 + t))
    img += au[..., None] * np.array([0.05, 0.22, 0.16], np.float32) * 0.5
    # polar grid (no land)
    g = np.zeros((H, W), np.float32)
    for r in (120, 240, 360, 480):
        cv2.circle(g, (int(cx), int(cy)), r, 1.0, 1, cv2.LINE_AA)
    for a in range(0, 360, 30):
        x1 = cx + 480 * math.cos(math.radians(a))
        y1 = cy + 480 * math.sin(math.radians(a))
        cv2.line(g, (int(cx), int(cy)), (int(x1), int(y1)), 1.0, 1, cv2.LINE_AA)
    img += g[..., None] * NEU_DIM * 0.18
    draw_text(img, "北极", cx, cy + 6, size=26, weight="regular", color=NEU_DIM, anchor="mt", alpha=0.7)
    # wandering dashed U-2 track
    track = []
    for s in np.linspace(0, 1, 160):
        x = cx - 60 + 260 * s + 80 * math.sin(s * 7)
        y = cy + 470 - 520 * s + 60 * math.sin(s * 5 + 1)
        track.append((x, y))
    track = np.array(track)
    p = ease_in_out(ramp(t, 0.3, D * 0.7))
    n = max(2, int(len(track) * p))
    m = mask_polyline(dashed(track[:n], 12, 9), thickness=3)
    img += m[..., None] * US + glow(m[..., None] * US * 0.4, (3, 10), (0.6, 0.3))
    head = track[n - 1]
    d = mask_circle(head[0], head[1], 8)
    img += glow(d[..., None] * US * 2, (3, 10, 24), (1, 0.6, 0.3)) + d[..., None] * US
    draw_text(img, "U-2 迷航", head[0] + 20, head[1], size=28, weight="bold", color=US, anchor="lm")
    # MiGs (amber) and US interceptors (blue) closing in
    k2 = ramp(t, D * 0.35, D * 0.9)
    if k2 > 0:
        for j, (sx0, sy0, col, lab) in enumerate([(W + 40, 250, SU, "米格战斗机"), (W + 40, 380, SU, None),
                                                  (-40, 1180, US, "美国截击机 · 核空空导弹"), (60, 1230, US, None)]):
            tgt = head + np.array([60 if col is SU else -60, -40 if col is SU else 60])
            pos = np.array([sx0, sy0]) + (tgt - np.array([sx0, sy0])) * ease_out(k2) * 0.82
            ang = math.atan2(tgt[1] - pos[1], tgt[0] - pos[0])
            tri = np.array([[pos[0] + 18 * math.cos(ang), pos[1] + 18 * math.sin(ang)],
                            [pos[0] + 12 * math.cos(ang + 2.5), pos[1] + 12 * math.sin(ang + 2.5)],
                            [pos[0] + 12 * math.cos(ang - 2.5), pos[1] + 12 * math.sin(ang - 2.5)]])
            tm = mask_poly([tri])
            img += tm[..., None] * col * 1.2 + glow(tm[..., None] * col, (3, 10), (0.8, 0.4))
            if lab:
                draw_text(img, lab, pos[0] + (-20 if col is SU else 20), pos[1] + (-24 if col is SU else 30),
                          size=26, weight="medium", color=col, anchor=("rb" if col is SU else "lt"))
    fade_text(img, "北极上空", 70, SAFE_TOP + 40, t, 0.2, size=60, weight="black", color=NEU, anchor="lt")
    fade_text(img, "示意 · 不含地图", 70, SAFE_TOP + 130, t, 0.6, size=24, weight="regular", color=NEU_DIM, anchor="lt")
    return img


def dive(t, D, cues):
    """Zoom into the third red dot, punch through cloud, sea surface, then sink into darkness."""
    xx, yy = grid()
    if t < 1.2:
        base = SC.timeline(4.0, active=3)
        z = 1 + ease_in(t / 1.2) * 5
        cx, cy = 90 + 900 * 16.98 / 24.0, 930
        M = np.array([[z, 0, W / 2 - cx * z], [0, z, H / 2 - cy * z]], np.float32)
        img = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LINEAR)
        img += ease_in(t / 1.2) * np.array([0.5, 0.15, 0.15], np.float32) * np.exp(-((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / 1e5)[..., None]
        return img
    u = t - 1.2
    img = bg((0.004, 0.012, 0.02), (0.0, 0.002, 0.004), power=0.9)
    # surface light from above fading as we sink
    depth = clamp01(u / 3.5)
    tile = noise_tile(512, 60, 7, 3)
    rays = scroll_noise(H, W, tile, u * 10, 0, zoom=2.2)
    rays = cv2.blur(rays, (3, 151))
    rays = np.clip((rays - 0.45) * 2.5, 0, 1) * np.clip(1 - yy / 1300, 0, 1)
    img += rays[..., None] * np.array([0.08, 0.20, 0.24], np.float32) * (1 - depth) * 0.8
    surf_y = -400 * ease_in(clamp01(u / 1.2)) + 100 * (1 - clamp01(u / 1.2))
    if u < 1.4:
        sl = np.exp(-((yy - surf_y) / 3) ** 2)
        img += sl[..., None] * np.array([0.4, 0.6, 0.8], np.float32) * (1 - u / 1.4)
    particles_underwater(img, u, n=320, speed=120 * (1 - 0.6 * depth), alpha=0.5)
    if t < 1.45:
        img = img * ramp(t, 1.2, 1.45) + (1 - ramp(t, 1.2, 1.45)) * np.array([0.9, 0.95, 1.0], np.float32)
    s6 = cue(cues, "c06", 0, D - 4)
    if t > s6:
        # three red dots, far apart, a faint centre that cannot reach them
        a = ease_out(ramp(t, s6, s6 + 0.6))
        c = np.array([W / 2, 760])
        for (dx, dy) in [(-330, -260), (320, -330), (60, 360)]:
            p = c + np.array([dx, dy])
            m = mask_polyline(dashed(np.array([c, p]), 8, 10), thickness=1)
            img += m[..., None] * NEU_DIM * 0.4 * a
            dm = mask_circle(p[0], p[1], 10)
            img += glow(dm[..., None] * ALERT * 1.6 * a, (3, 10, 24), (1, 0.6, 0.3)) + dm[..., None] * ALERT * a
        cm = mask_circle(c[0], c[1], 16, fill=False, thickness=2)
        img += cm[..., None] * NEU * 0.6 * a
        draw_text(img, "中心", c[0], c[1] + 30, size=26, weight="regular", color=NEU_DIM, alpha=a, anchor="mt")
        fade_text(img, "扳机 · 离中心最远", W / 2, 300, t, s6 + 2.0, size=44, weight="black", color=NEU)
    return img


# ============================================================================
# 4  under the sea
# ============================================================================

def _gauge_bar(img, x, y, w, frac, col, label, value, a=1.0):
    draw_text(img, label, x, y, size=28, weight="medium", color=NEU_DIM, alpha=a, anchor="lt")
    draw_text(img, value, x + w, y, size=30, weight="monobold", color=col, alpha=a, anchor="rt")
    m = np.zeros((H, W), np.float32)
    cv2.rectangle(m, (int(x), int(y + 48)), (int(x + w), int(y + 60)), 1.0, 1, cv2.LINE_AA)
    img += m[..., None] * NEU_DIM * 0.5 * a
    f = np.zeros((H, W), np.float32)
    cv2.rectangle(f, (int(x + 2), int(y + 50)), (int(x + 2 + (w - 4) * frac), int(y + 58)), 1.0, -1)
    img += f[..., None] * np.asarray(col, np.float32) * 0.9 * a


def section(t, D, cues):
    img = bg((0.006, 0.012, 0.02), (0.002, 0.004, 0.008))
    xx, yy = grid()
    particles_underwater(img, t, n=160, speed=12, alpha=0.35)
    scx, scy, slen = 540, 640, 900
    hull, sail, fins = S.sub_side()
    ph = S.place(hull, scx, scy, slen)
    ps = S.place(sail, scx, scy, slen)
    pf = S.place(fins, scx, scy, slen)
    m = mask_poly([ph, ps, pf])
    heat = ramp(t, 2.0, D)
    inner = np.clip(m - cv2.erode(m, np.ones((5, 5), np.uint8)), 0, 1)
    img = img * (1 - m[..., None]) + m[..., None] * (np.array([0.02, 0.016, 0.012], np.float32) + heat * np.array([0.07, 0.025, 0.0], np.float32))
    rim = mask_polyline([ph, ps], thickness=2.2, closed=True)
    img += rim[..., None] * SU * 0.9 + glow(rim[..., None] * SU * 0.35, (2, 8), (0.7, 0.3))
    comp = np.zeros((H, W), np.float32)
    for u in np.linspace(-0.36, 0.38, 7):
        x = int(scx + u * slen)
        cv2.line(comp, (x, int(scy - 34)), (x, int(scy + 34)), 1.0, 1, cv2.LINE_AA)
    img += (comp * m)[..., None] * SU * 0.35
    # battery bank highlight (lower deck, aft)
    bat = np.zeros((H, W), np.float32)
    cv2.rectangle(bat, (int(scx - 0.30 * slen), int(scy + 8)), (int(scx - 0.05 * slen), int(scy + 30)), 1.0, -1)
    blink = 0.5 + 0.5 * math.sin(t * 5)
    img += (bat * m)[..., None] * ALERT * (0.25 + 0.25 * blink) * ramp(t, 1.0, 2.0)
    draw_text(img, "电池", scx - 0.175 * slen, scy + 44, size=24, weight="medium", color=ALERT, anchor="mt",
              alpha=ramp(t, 1.0, 2.0))
    # heat shimmer inside the hull (subtle)
    draw_text(img, "B-59 · 狐步级柴电潜艇（示意）", 60, SAFE_TOP + 20, size=30, weight="bold", color=SU, anchor="lt")
    # readouts
    x0, y0, w = 120, 820, 840
    s2 = cue(cues, "d02", 0, 3.0)
    s3 = cue(cues, "d03", 0, D - 4)
    temp = 30 + 15 * ease_in_out(ramp(t, s2 + 1.5, s2 + 5.0))
    _gauge_bar(img, x0, y0, w, (temp - 20) / 40, ALERT if temp > 40 else SU, "舱内温度（据艇员回忆）", f"{temp:4.0f}℃",
               ease_out(ramp(t, s2, s2 + 0.5)))
    co2 = ease_in_out(ramp(t, s2 + 2.5, s2 + 6.5))
    _gauge_bar(img, x0, y0 + 110, w, 0.35 + 0.55 * co2, ALERT if co2 > 0.5 else SU, "二氧化碳", "超标" if co2 > 0.5 else "上升",
               ease_out(ramp(t, s2 + 2.0, s2 + 2.5)))
    a3 = ease_out(ramp(t, s3, s3 + 0.5))
    if a3 > 0:
        _gauge_bar(img, x0, y0 + 220, w, 0.12, ALERT, "距上次收到莫斯科消息", "2 天", a3)
    # explainer chips at top
    a1 = ease_out(ramp(t, 0.5, 1.2))
    fade_text(img, "水面：柴油机充电　水下：全靠电池", W / 2, 400, t, 0.5, size=32, weight="medium", color=NEU)
    return img


def knock(t, D, cues):
    img = bg()
    s5 = cue(cues, "d05", 0, 1.5)
    s6 = cue(cues, "d06", 0, D - 6)
    if t < s6:
        a = ease_out(ramp(t, s5 - 0.3, s5 + 0.4))
        panel(img, 110, 330, W - 110, 1050, alpha=a, color=(0.03, 0.035, 0.04), edge=NEU_DIM)
        draw_text(img, "潜艇上浮识别程序", W / 2, 400, size=46, weight="black", color=NEU, alpha=a, anchor="mt")
        draw_text(img, "（示意，非原件）", W / 2, 470, size=26, weight="regular", color=NEU_DIM, alpha=a, anchor="mt")
        fade_text(img, "美舰投下 4–5 枚无害声响弹", W / 2, 620, t, s5 + 1.0, size=40, weight="bold", color=US)
        fade_text(img, "＝ 请浮上来，朝东航行", W / 2, 700, t, s5 + 2.0, size=40, weight="bold", color=NEU)
        fade_text(img, "训练深弹：手榴弹大小 · 只会响，炸不穿船", W / 2, 830, t, s5 + 3.5, size=30, weight="medium",
                  color=NEU_DIM)
        fade_text(img, "1962.10.24 前后 · 经外交渠道通知苏联政府", W / 2, 960, t, s5 + 4.5, size=26, weight="regular",
                  color=NEU_DIM)
        fade_text(img, "敲门", W / 2, 230 + SAFE_TOP - 200, t, 0.2, size=40, weight="black", color=NEU, alpha=0.0)
    else:
        u = t - s6
        nodes = [(W / 2, 420, "华盛顿", US), (W / 2, 720, "莫斯科", SU), (W / 2, 1020, "B-59", SU)]
        for i, (x, y, lab, col) in enumerate(nodes):
            a = ease_out(ramp(u, i * 0.4, i * 0.4 + 0.4))
            m = mask_circle(x, y, 14)
            img += glow(m[..., None] * col * 1.5 * a, (3, 10), (1, 0.5)) + m[..., None] * col * a
            draw_text(img, lab, x + 40, y, size=38, weight="bold", color=col, alpha=a, anchor="lm")
        k1 = ease_out(ramp(u, 0.6, 1.4))
        line(img, (W / 2, 440), (W / 2, 440 + (700 - 440) * k1), US, 1.0, 3, 0.6)
        if k1 >= 1:
            draw_text(img, "通知送到 ✓", W / 2 - 40, 570, size=30, weight="medium", color=US, anchor="rm")
        k2 = ease_out(ramp(u, 1.6, 2.6))
        if k2 > 0:
            pts = np.array([[W / 2, 740], [W / 2, 740 + (1000 - 740) * k2]])
            m = mask_polyline(dashed(pts, 10, 12), thickness=3)
            img += m[..., None] * SU * 0.7
        if u > 2.8:
            a = ease_out(ramp(u, 2.8, 3.2))
            draw_text(img, "没有证据表明传到了潜艇 ✗", W / 2 - 40, 870, size=30, weight="bold", color=ALERT, alpha=a,
                      anchor="rm")
        fade_text(img, "信号发出去了，收件人没收到", W / 2, 260 + 40, s6 + 0.0 + (t - s6), 4.0 if D - s6 > 5 else 2.5,
                  size=40, weight="black", color=NEU)
    if t < s5 - 0.2:
        fade_text(img, "“敲门”", W / 2, 700, t, 0.1, size=120, weight="black", color=NEU, tracking=0.1)
    return img


def sonar(t, D, cues):
    import cuelib
    s7 = cue(cues, "d07", 0, 0.5)
    e7 = cue(cues, "d07", 1, D * 0.55)
    s8 = cue(cues, "d08", 0, D * 0.6)
    beale, cony, heavy = cuelib.sonar_hits(cues, D)
    img = SC.sonar_scene(t, hits=beale, hits2=cony + heavy, show_sub_label=True)
    # toilet-paper-roll detail (inset) during the second half of d07
    a = ease_out(ramp(t, s7 + 7.0, s7 + 7.6)) * (1 - ramp(t, e7 + 0.2, e7 + 0.6))
    if a > 0:
        x, y = 820, 760
        panel(img, x - 190, y - 150, x + 190, y + 150, alpha=a, edge=US_DIM)
        m = np.zeros((H, W), np.float32)
        cv2.rectangle(m, (x - 26, y - 70), (x + 26, y + 40), 1.0, 2, cv2.LINE_AA)  # paper tube
        cv2.circle(m, (x, y - 10), 18, 1.0, -1, cv2.LINE_AA)  # grenade inside
        img += m[..., None] * NEU * 0.9 * a
        draw_text(img, "手榴弹 + 卫生纸卷筒", x, y + 70, size=24, weight="medium", color=NEU, alpha=a, anchor="mt")
        draw_text(img, "沉得更深再炸", x, y + 104, size=24, weight="medium", color=US, alpha=a, anchor="mt")
        draw_text(img, "（比尔号值更军官回忆）", x, y - 140, size=20, weight="regular", color=NEU_DIM, alpha=a, anchor="mt")
    if t > s8 + 2.0:
        fade_text(img, "像坐在被大锤砸的汽油桶里", W / 2, 1210, t, s8 + 2.0, size=34, weight="bold", color=SU, alpha=0.0)
    return img


def _quote_block(img, text, cx, cy, t, t0, size=60, color=SU, width_chars=10, line_h=1.35):
    """Big centred quote, wrapped by width_chars, fading in line by line."""
    body = text.strip("“”")
    lines = []
    cur = ""
    for ch in body:
        cur += ch
        if len(cur) >= width_chars and ch in "，。！？：；" or len(cur) >= width_chars + 3:
            lines.append(cur)
            cur = ""
    if cur:
        lines.append(cur)
    lh = size * line_h
    y0 = cy - lh * len(lines) / 2
    for i, l in enumerate(lines):
        fade_text(img, l, cx, y0 + i * lh, t, t0 + i * 0.35, size=size, weight="black", color=color, anchor="mt",
                  glow_amt=0.12)
    return y0 + lh * len(lines)


def quote_sav(t, D, cues):
    img = bg((0.03, 0.012, 0.004), (0.006, 0.003, 0.002), power=0.9)
    xx, yy = grid()
    # pulsing amber dark, slight shake as impacts continue
    pulse = 0.5 + 0.5 * math.sin(t * 2.2)
    img += np.exp(-((xx - W / 2) ** 2 + (yy - 700) ** 2) / 2.5e5)[..., None] * SU * 0.05 * (0.6 + 0.4 * pulse)
    particles_underwater(img, t, n=120, speed=10, color=(0.5, 0.35, 0.2), alpha=0.35)
    draw_text(img, "艇长萨维茨基（据奥尔洛夫回忆）", W / 2, SAFE_TOP + 40, size=30, weight="medium", color=NEU_DIM, anchor="mt")
    for lid, nxt in (("d10", "d11"), ("d12", "d13")):
        if lid in cues:
            s, e = cues[lid]
            n_end = cues.get(nxt, (e, e + 3))[1]
            if s - 0.2 <= t <= n_end + 0.1:
                a_out = 1 - ramp(t, n_end - 0.2, n_end + 0.1)
                tmp = img.copy()
                yb = _quote_block(tmp, cues and dict(d10="“也许上面战争已经开始了，我们还在这里翻跟头！”",
                                                     d12="“我们现在就揍他们！我们会死，但要把他们全部击沉，不能给舰队丢脸。”")[lid],
                                  W / 2, 600, t, s - 0.1, size=66, color=SU, width_chars=9)
                img = img * (1 - a_out) + tmp * a_out
    if t < cue(cues, "d10", 0, 3.0) - 0.2:
        a = ease_out(ramp(t, 0.2, 0.8))
        m = np.zeros((H, W), np.float32)
        cv2.rectangle(m, (380, 560), (700, 760), 1.0, 2, cv2.LINE_AA)
        img += m[..., None] * SU * 0.6 * a
        draw_text(img, "核鱼雷", W / 2, 620, size=48, weight="black", color=SU, alpha=a, anchor="mt")
        fade_text(img, "命令：装配到战斗状态", W / 2, 840, t, 1.5, size=40, weight="bold", color=ALERT * 0.7 + NEU * 0.3)
    return img


def orders(t, D, cues):
    img = bg((0.008, 0.008, 0.01), (0.016, 0.014, 0.012))
    xx, yy = grid()
    # lamp pool
    img += np.exp(-((xx - W / 2) ** 2 / 1.2e5 + (yy - 520) ** 2 / 3e4))[..., None] * np.array([0.12, 0.09, 0.05], np.float32) * 0.6
    s14 = cue(cues, "d14", 0, 0.3)
    s15 = cue(cues, "d15", 0, D * 0.45)
    s17 = cue(cues, "d17", 0, D * 0.65)
    if t < s17 - 0.1:
        fade_text(img, "出发前一天 · 北方舰队参谋长的交代", W / 2, SAFE_TOP + 40, t, s14 + 0.8, size=30, weight="medium",
                  color=NEU_DIM, anchor="mt")
        fade_text(img, "（据 B-4 艇长凯托夫回忆）", W / 2, SAFE_TOP + 86, t, s14 + 0.8, size=24, weight="regular",
                  color=NEU_DIM, anchor="mt")
        items = ["① 水下，艇体被打穿", "② 浮上水面挨打，艇体被打穿", "③ 莫斯科下令"]
        for i, it in enumerate(items):
            fade_text(img, it, 150, 420 + i * 80, t, s14 + 3.0 + i * 0.9, size=40, weight="bold", color=NEU, anchor="lt")
        fade_text(img, "→ 可以使用核武器", 150, 680, t, s14 + 6.0, size=36, weight="medium", color=SU, anchor="lt")
        if t > s15 - 0.2:
            _quote_block(img, "“我建议你们，先用核武器，然后再想怎么办。”", W / 2, 940, t, s15 - 0.1, size=56,
                         color=SU, width_chars=10)
    else:
        u = t - s17
        a = ease_out(ramp(u, 0, 0.5))
        line(img, (W / 2, 330), (W / 2, 1000), NEU_DIM, 0.5 * a)
        draw_text(img, "口头交代", W / 4 + 10, 360, size=36, weight="black", color=SU, alpha=a, anchor="mt")
        draw_text(img, "（凯托夫回忆）", W / 4 + 10, 410, size=24, weight="regular", color=NEU_DIM, alpha=a, anchor="mt")
        for i, l in enumerate(["“先用核武器，", "然后再想", "怎么办”"]):
            draw_text(img, l, W / 4 + 10, 500 + i * 60, size=36, weight="bold", color=NEU, alpha=a, anchor="mt")
        b = ease_out(ramp(u, 1.0, 1.5))
        draw_text(img, "书面命令", 3 * W / 4 - 10, 360, size=36, weight="black", color=US, alpha=b, anchor="mt")
        draw_text(img, "（另一来源）", 3 * W / 4 - 10, 410, size=24, weight="regular", color=NEU_DIM, alpha=b, anchor="mt")
        for i, l in enumerate(["只能凭", "国防部长的", "特别命令"]):
            draw_text(img, l, 3 * W / 4 - 10, 500 + i * 60, size=36, weight="bold", color=NEU, alpha=b, anchor="mt")
        c = ease_out(ramp(u, 3.5, 4.0))
        if c > 0:
            panel(img, 150, 820, W - 150, 930, alpha=c, edge=ALERT * 0.7)
            draw_text(img, "两种说法都可信 · 都没有档案证实", W / 2, 875, size=34, weight="bold", color=NEU, alpha=c, anchor="mm")
            draw_text(img, "—— Savranskaya, 2005", W / 2, 960, size=24, weight="regular", color=NEU_DIM, alpha=c, anchor="mt")
        fade_text(img, "连“什么时候能按按钮”都说不清", W / 2, 1100, t, s17 + 6.5, size=40, weight="black", color=ALERT * 0.5 + NEU * 0.5)
    return img


# ============================================================================
# 5  hypothetical
# ============================================================================

def hypo_launch(t, D, cues):
    """Torpedo leaving the tube (side view, thermal false colour)."""
    hh, hw = 960, 540
    yy, xx = np.mgrid[0:hh, 0:hw].astype(np.float32)
    I = 0.05 + 0.04 * np.exp(-np.abs(yy - 200) / 300)
    hull, sail, fins = S.sub_side()
    subm = mask_poly([S.place(hull, 150, 520, 520), S.place(sail, 150, 520, 520)], h=hh, w=hw)
    I = I * (1 - subm) + subm * 0.10
    rim = np.clip(subm - cv2.erode(subm, np.ones((3, 3), np.uint8)), 0, 1)
    I += rim * 0.35
    k = ease_in(ramp(t, 0.4, D))
    tx = 410 + k * 300
    ty = 528
    torp = mask_ellipse(tx, ty, 34, 6, h=hh, w=hw)
    I += torp * 0.95
    # bubble trail
    rng = np.random.default_rng(4)
    for i in range(60):
        bx = 410 + rng.uniform(0, max(1.0, tx - 410))
        by = ty + rng.normal(0, 6) - (tx - bx) * 0.02
        I += mask_circle(bx, by, rng.uniform(1, 3.5), h=hh, w=hw) * 0.5
    col = thermal_map(np.clip(I, 0, 1))
    col = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC)
    yyF = grid()[1]
    col *= (0.94 + 0.06 * np.sin(yyF * math.pi / 2.0))[..., None]
    col = chroma_shift(col, 3)
    hypo_frame(col, t)
    draw_text(col, "核鱼雷出管", 140, 1080, size=40, weight="black", color=(1.0, 0.85, 0.95), anchor="lt")
    return col


def hypo_burst(t, D, cues):
    # 0.5 s of near-black silence first, then the burst grows across the shot
    if t < 0.5:
        img = canvas(np.array([0.02, 0.0, 0.02], np.float32))
        hypo_frame(img, t)
        return img
    tb = clamp01((t - 0.5) / max(D - 0.8, 1.0)) * 0.98 + 0.02
    img = SC.hypo_explosion(t, tb=tb, seed=11)
    if t < 0.75:  # initial flash
        k = 1 - ramp(t, 0.5, 0.75)
        img = img * (1 - k) + k * np.array([1.0, 0.92, 0.98], np.float32)
    s2 = cue(cues, "e02", 0, D - 4)
    if t > s2:
        a = ease_out(ramp(t, s2, s2 + 0.5))
        draw_text(img, "最近的目标：伦道夫号 · 约 3400 人", W - 90, SAFE_TOP + 170, size=30, weight="bold",
                  color=(1.0, 0.85, 0.95), alpha=a, anchor="rt")
    fade_text(img, "威力 ≈ 一颗广岛原子弹", W - 90, SAFE_TOP + 120, t, 2.5, size=32, weight="bold",
              color=(1.0, 0.8, 0.9), anchor="rt")
    return img


def hypo_globe(t, D, cues):
    img = SC.hypo_globe(t * (10.0 / max(D, 6.0)), dur=10.0)
    s3 = cue(cues, "e03", 0, 0)
    fade_text(img, "核深弹还击 → 连锁反应", 90, 1150, t, s3 + 2.0, size=34, weight="bold", color=(1.0, 0.8, 0.9),
              anchor="lt")
    return img


@functools.lru_cache(maxsize=1)
def _hypo_last():
    return SC.hypo_globe(10.0, dur=10.0, hypo_alpha=0.0)


def hypo_out(t, D, cues):
    if t < 1.1:
        img = _hypo_last().copy()
        k = ease_in_out(ramp(t, 0.0, 0.9))
        # freeze; the 「假想」 tag grows
        img = img * (1 - 0.5 * k)
        tw, th = text_size("假想", "black", int(46 + 220 * k), 0.25)
        draw_text(img, "假想", W / 2 - tw / 2 * k - 70 * (1 - k) + 0, lerp(SAFE_TOP + 4, 700, k), size=int(46 + 220 * k),
                  weight="black", color=(1.0, 0.9, 0.97), tracking=0.25, anchor="lt")
        if t > 0.95:
            f = ramp(t, 0.95, 1.1)
            img = img * (1 - f) + f * np.array([1, 1, 1], np.float32)
        return img
    u = t - 1.1
    img = bg((0.006, 0.012, 0.024), (0.01, 0.02, 0.04))
    if u < 0.12:
        img = img * ramp(u, 0, 0.12) + (1 - ramp(u, 0, 0.12)) * np.array([1, 1, 1], np.float32)
    xx, yy = grid()
    hl = np.exp(-((yy - 1000) / 1.5) ** 2) * np.clip(1 - np.abs(xx - W / 2) / (W * 0.6), 0, 1)
    img += hl[..., None] * np.array([0.12, 0.22, 0.38], np.float32)
    s5 = cue(cues, "e05", 0, 1.3)
    fade_text(img, "这些，都没有发生", W / 2, 640, t, s5 + 0.1, size=62, weight="black", color=NEU)
    fade_text(img, "为什么？", W / 2, 760, t, s5 + 1.6, size=62, weight="black", color=SU)
    return img


# ============================================================================
# 6  surfaced
# ============================================================================

def surfacing(t, D, cues):
    img = bg((0.004, 0.006, 0.012), (0.002, 0.01, 0.018))
    xx, yy = grid()
    wl = 700
    sea = (yy > wl).astype(np.float32)[..., None]
    img = img * (1 - sea) + sea * np.array([0.004, 0.012, 0.02], np.float32)
    tile = noise_tile(512, 40, 3, 4)
    n = scroll_noise(H, W, tile, t * 8, t * 3)
    glint = np.clip((cv2.blur(n, (41, 1)) - 0.55) * 5, 0, 1) * np.clip(1 - (yy - wl) / 500, 0, 1) * sea[..., 0]
    img += glint[..., None] * np.array([0.08, 0.13, 0.2], np.float32)
    k = ease_in_out(ramp(t, 0.5, min(D - 1.0, 6.0)))
    hull, sail, fins = S.sub_side()
    scy = lerp(wl + 220, wl + 18, k)
    m = mask_poly([S.place(hull, 540, scy, 820), S.place(sail, 540, scy, 820), S.place(fins, 540, scy, 820)])
    under = m * sea[..., 0]
    above = m * (1 - sea[..., 0])
    img = img * (1 - m[..., None]) + m[..., None] * np.array([0.01, 0.012, 0.015], np.float32)
    img += under[..., None] * np.array([0.0, 0.02, 0.03], np.float32)
    rim = mask_polyline([S.place(hull, 540, scy, 820), S.place(sail, 540, scy, 820)], thickness=2, closed=True)
    img += (rim * (1 - sea[..., 0]))[..., None] * SU * 0.7 + (rim * sea[..., 0])[..., None] * SU * 0.25
    # spray where the hull breaks the surface
    if 0.3 < k < 1.0:
        rng = np.random.default_rng(int(t * 30))
        sp = np.zeros((H, W), np.float32)
        xs = rng.uniform(200, 880, 400)
        ys = wl - np.abs(rng.normal(0, 18, 400))
        np.add.at(sp, (ys.astype(int), xs.astype(int)), 1.0)
        img += cv2.GaussianBlur(sp, (0, 0), 1.2)[..., None] * np.array([0.6, 0.7, 0.8], np.float32) * (1 - k)
    # searchlight sweeps from the left
    for i, (sx, sy) in enumerate([(-50, 560), (W + 50, 600)]):
        ang = math.radians(10 + 12 * math.sin(t * 0.7 + i * 2)) * (1 if i == 0 else -1)
        dirx = math.cos(ang) * (1 if i == 0 else -1)
        diry = math.sin(ang) * 0.25
        px, py = xx - sx, yy - sy
        along = px * dirx + py * diry
        perp = np.abs(-px * diry + py * dirx)
        beam = np.exp(-(perp / (np.maximum(along, 1) * 0.06 + 4)) ** 2) * (along > 0) * np.exp(-along / 1500)
        img += beam[..., None] * np.array([0.6, 0.78, 1.0], np.float32) * 0.18 * ramp(t, 1.5 + i, 2.5 + i)
    fade_text(img, "20:50 · B-59 浮出水面", 60, SAFE_TOP + 20, t, 0.5, size=34, weight="bold", color=NEU, anchor="lt")
    s2 = cue(cues, "f02", 0, D - 3)
    fade_text(img, "另一种说法：最危险的一刻在水面", W / 2, 1100, t, s2, size=36, weight="bold", color=SU, alpha=0.0)
    return img


def topdown(t, D, cues):
    # plane: strafing pass early, overflight later
    s4 = cue(cues, "f04", 0, 2.0)
    mode = "strafe" if t < s4 + 4.5 else "overfly"
    pt = (t - s4 + 1.7) if mode == "strafe" else (t - s4 - 4.5 + 1.0)
    img = SC.surface_topdown(t, plane_t=pt, pass_mode=mode, splashes=True)
    return img


def _figure(img, x, y, scale, col, a=1.0, down=0.0):
    """Generic standing silhouette (no face). down in [0,1] lowers it through the hatch."""
    head = mask_circle(x, y - 70 * scale + down * 120 * scale, 11 * scale)
    body = mask_poly([np.array([[x - 16 * scale, y - 56 * scale], [x + 16 * scale, y - 56 * scale],
                                [x + 12 * scale, y + 20 * scale], [x - 12 * scale, y + 20 * scale]]) + np.array([0, down * 120 * scale])])
    m = np.clip(head + body, 0, 1)
    img = img * (1 - m[..., None] * a) + m[..., None] * np.array([0.01, 0.012, 0.016], np.float32) * a
    rim = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1)
    img += rim[..., None] * np.asarray(col, np.float32) * 0.9 * a
    return img


def tower(t, D, cues):
    img = bg((0.004, 0.006, 0.012), (0.01, 0.014, 0.02))
    xx, yy = grid()
    # conning tower block (side, close-up)
    m = mask_poly([np.array([[170, 1240], [230, 640], [860, 620], [930, 1240]])])
    img = img * (1 - m[..., None]) + m[..., None] * np.array([0.016, 0.018, 0.022], np.float32)
    edge = mask_polyline([np.array([[170, 1240], [230, 640], [860, 620], [930, 1240]])], thickness=2, closed=True)
    img += edge[..., None] * SU * 0.45
    # hatch on top
    hatch = mask_ellipse(420, 640, 46, 10)
    img += hatch[..., None] * np.array([0.0, 0.0, 0.0], np.float32) - hatch[..., None] * img * 0.9
    s6 = cue(cues, "f06", 0, 0.3)
    s7 = cue(cues, "f07", 0, D * 0.35)
    s8 = cue(cues, "f08", 0, D * 0.6)
    s9 = cue(cues, "f09", 0, D - 3)
    # searchlight flashes and the aircraft passing overhead
    fl = max(0.0, math.sin(t * 2.3)) ** 6 + max(0.0, math.sin(t * 1.7 + 1.0)) ** 8
    img += np.exp(-((xx - 980) ** 2 + (yy - 420) ** 2) / 4e5)[..., None] * np.array([0.6, 0.75, 1.0], np.float32) * 0.25 * fl
    pk = ((t - s6) % 5.0) / 5.0
    px = lerp(W + 200, -200, pk)
    pm = mask_poly([S.place(q, px, 330, 300, 180) for q in [np.array([[-0.5, 0.0], [0.5, 0.0], [0.5, 0.03], [-0.5, 0.03]]),
                                                             np.array([[-0.05, -0.02], [0.05, -0.02], [0.05, 0.25], [-0.05, 0.25]])]])
    img = img * (1 - pm[..., None]) + pm[..., None] * np.array([0.02, 0.024, 0.03], np.float32)
    img += np.clip(pm - cv2.erode(pm, np.ones((3, 3), np.uint8)), 0, 1)[..., None] * US * 0.7
    # muzzle flashes far off, splashes "beside the boat"
    if (t * 3) % 1.0 < 0.3:
        mf = mask_circle(px - 90, 345, 6)
        img += glow(mf[..., None] * np.array([1.0, 0.9, 0.7], np.float32) * 2, (3, 10), (1, 0.5))
    # two figures: captain heading down (blocked), Arkhipov standing looking at the light
    down = ease_in_out(ramp(t, s6 + 3.0, s7 + 1.0)) * 0.35
    if t > s8 + 2.5:
        down = max(0.0, down - ease_in_out(ramp(t, s8 + 2.5, s8 + 4.0)) * 0.35)
    img = _figure(img, 420, 600, 1.1, SU, 1.0, down)
    img = _figure(img, 640, 600, 1.1, NEU, 1.0, 0.0)
    # the blocking signal officer + equipment below the hatch (cutaway hint)
    if t > s7:
        a = ease_out(ramp(t, s7, s7 + 0.5))
        box = np.zeros((H, W), np.float32)
        cv2.rectangle(box, (370, 700), (470, 790), 1.0, 2, cv2.LINE_AA)
        img += box[..., None] * ALERT * 0.8 * a
        draw_text(img, "窄梯被堵", 420, 810, size=28, weight="bold", color=ALERT, alpha=a, anchor="mt")
        draw_text(img, "信号军官和设备", 420, 852, size=24, weight="regular", color=NEU_DIM, alpha=a, anchor="mt")
    a1 = ease_out(ramp(t, s6, s6 + 0.5))
    draw_text(img, "艇长", 420, 470 - down * 0, size=28, weight="bold", color=SU, alpha=a1, anchor="mb")
    draw_text(img, "下令紧急下潜", 420, 430, size=24, weight="medium", color=SU, alpha=a1 * (1 - ramp(t, s8 + 2.5, s8 + 3.0)), anchor="mb")
    draw_text(img, "旅参谋长阿尔希波夫", 700, 470, size=28, weight="bold", color=NEU, alpha=ease_out(ramp(t, s8, s8 + 0.5)), anchor="lb")
    if t > s8 + 1.0:
        a = ease_out(ramp(t, s8 + 1.0, s8 + 1.5))
        draw_text(img, "看清：打信号、拍照", 700, 520, size=26, weight="medium", color=US, alpha=a, anchor="lb")
        draw_text(img, "炮弹落在旁边的水里", 700, 560, size=26, weight="medium", color=US, alpha=a, anchor="lb")
    if t > s8 + 4.0:
        fade_text(img, "命令没有传到鱼雷军官", W / 2, 1000, t, s8 + 4.0, size=34, weight="bold", color=NEU)
    if t > s9 - 0.2:
        a = ease_out(ramp(t, s9 - 0.2, s9 + 0.3))
        panel(img, 90, 1080, W - 90, 1200, alpha=a, edge=NEU_DIM)
        draw_text(img, "据凯托夫等人回忆 · 讲述者均未亲眼看到塔上这几分钟", W / 2, 1140, size=27, weight="medium",
                  color=NEU, alpha=a, anchor="mm")
    corner_tag(img, "指挥塔 · 示意", 60, SAFE_TOP + 20, color=NEU_DIM, size=24)
    return img


@functools.lru_cache(maxsize=1)
def _b59_photo():
    im = Image.open(os.path.join(ASSETS, "archive/b59_asw2.jpg")).convert("L")
    a = np.asarray(im, np.float32) / 255.0
    return a[:700]  # crop off the printed caption strip


def photo(t, D, cues):
    img = canvas(np.array([0.0, 0.0, 0.0], np.float32))
    ph = _b59_photo()
    h, w = ph.shape
    z = 1.0 + 0.06 * t / max(D, 0.1)
    s = W / w * 1.1 * z
    M = np.array([[s, 0, W / 2 - w / 2 * s], [0, s, 760 - h / 2 * s]], np.float32)
    warped = cv2.warpAffine(ph, M, (W, H), flags=cv2.INTER_LINEAR)
    a = ease_out(ramp(t, 0, 0.15)) * (1 - ramp(t, D - 0.25, D))
    img += warped[..., None] * np.array([0.85, 0.92, 1.0], np.float32) * a
    draw_text(img, "美国海军拍摄的 B-59（浮出水面后）", W / 2, 1110, size=32, weight="bold", color=NEU, alpha=a, anchor="mt")
    draw_text(img, "约 1962 年 10 月 28–29 日 · 美国国家档案馆 RG 428", W / 2, 1160, size=24, weight="regular", color=NEU_DIM,
              alpha=a, anchor="mt")
    return img


def arkhipov(t, D, cues):
    img = bg()
    fade_text(img, "瓦西里·阿尔希波夫", W / 2, 420, t, 0.2, size=72, weight="black", color=NEU)
    fade_text(img, "第 69 潜艇旅参谋长 · 二级舰长", W / 2, 520, t, 0.6, size=34, weight="medium", color=NEU_DIM)
    fade_text(img, "军衔与艇长萨维茨基相同", W / 2, 580, t, 1.0, size=34, weight="bold", color=SU)
    s = cue(cues, "f10", 0, 0)
    a = ease_out(ramp(t, s + 4.5, s + 5.0))
    if a > 0:
        line(img, (200, 700), (W - 200, 700), NEU_DIM, 0.4 * a)
        # radiation trefoil (generic hazard icon)
        cx, cy, r = W / 2, 850, 70
        m = np.zeros((H, W), np.float32)
        for k in range(3):
            a0 = -90 + k * 120 - 30
            cv2.ellipse(m, (int(cx), int(cy)), (r, r), 0, a0, a0 + 60, 1.0, -1, cv2.LINE_AA)
        cv2.circle(m, (int(cx), int(cy)), int(r * 0.32), 0.0, -1, cv2.LINE_AA)
        cv2.circle(m, (int(cx), int(cy)), int(r * 0.2), 1.0, -1, cv2.LINE_AA)
        img += m[..., None] * SU * 0.8 * a
        draw_text(img, "1961 · K-19 核潜艇 · 副艇长", W / 2, 960, size=34, weight="bold", color=NEU, alpha=a, anchor="mt")
        draw_text(img, "反应堆事故 · 数名艇员死于辐射", W / 2, 1012, size=30, weight="medium", color=NEU_DIM, alpha=a, anchor="mt")
    return img


def checklist(t, D, cues):
    img = bg()
    s = cue(cues, "f11", 0, 0)
    e = cue(cues, "f11", 1, D)
    items = ["潜艇上恰好多了一个和艇长同级的人", "他恰好站在塔上", "他恰好看清了", "艇长恰好被一条窄梯子挡了一下"]
    span = (e - s) * 0.78
    for i, it in enumerate(items):
        t0 = s + span * i / 4
        y = 400 + i * 130
        a = ease_out(ramp(t, t0, t0 + 0.4))
        if a <= 0:
            continue
        m = mask_circle(130, y + 22, 20, fill=False, thickness=3)
        img += m[..., None] * SU * a
        ck = np.zeros((H, W), np.float32)
        cv2.line(ck, (120, y + 22), (128, y + 31), 1.0, 3, cv2.LINE_AA)
        cv2.line(ck, (128, y + 31), (143, y + 12), 1.0, 3, cv2.LINE_AA)
        img += ck[..., None] * SU * ease_out(ramp(t, t0 + 0.2, t0 + 0.5))
        draw_text(img, it, 180, y, size=40, weight="bold", color=NEU, alpha=a, anchor="lt")
    fade_text(img, "缺一件，结局都可能不同", W / 2, 1020, t, s + span + 0.2, size=50, weight="black", color=SU)
    return img


# ============================================================================
# 7  the tidy story
# ============================================================================

def vote(t, D, cues):
    img = bg()
    s1 = cue(cues, "g01", 0, 0)
    s2 = cue(cues, "g02", 0, D * 0.4)
    fade_text(img, "流传最广的版本", W / 2, SAFE_TOP + 60, t, s1 + 0.1, size=34, weight="medium", color=NEU_DIM)
    cards = [("艇长", True), ("政委", True), ("阿尔希波夫", False)]
    shatter = ease_in_out(ramp(t, s2 + 0.3, s2 + 2.0))
    rng = np.random.default_rng(9)
    for i, (lab, yes) in enumerate(cards):
        cx = 200 + i * 340
        cy = 600
        a = ease_out(ramp(t, s1 + 0.6 + i * 0.5, s1 + 1.0 + i * 0.5)) * (1 - shatter)
        if a > 0:
            panel(img, cx - 140, cy - 190, cx + 140, cy + 190, alpha=a, edge=NEU_DIM)
            draw_text(img, lab, cx, cy - 120, size=36 if len(lab) < 4 else 32, weight="bold", color=NEU, alpha=a, anchor="mt")
            sym = "✓" if yes else "✗"
            draw_text(img, sym, cx, cy + 40, size=120, weight="black", color=(US if yes else ALERT), alpha=a, anchor="mm")
    if shatter > 0:
        # tangled lines replace the tidy cards
        for k in range(40):
            p0 = np.array([rng.uniform(80, W - 80), rng.uniform(420, 800)])
            pts = [p0]
            for j in range(6):
                pts.append(pts[-1] + rng.normal(0, 60, 2))
            pts = np.array(pts)
            m = mask_polyline([pts[: max(2, int(len(pts) * shatter))]], thickness=1.5)
            img += m[..., None] * NEU_DIM * 0.5 * shatter
        a = ease_out(ramp(t, s2 + 2.4, s2 + 3.0))
        for i in range(3):
            kx = W / 2 + (i - 1) * 140
            m = mask_circle(kx, 960, 22, fill=False, thickness=4)
            m += mask_polyline([np.array([[kx + 22, 960], [kx + 80, 960]]), np.array([[kx + 64, 960], [kx + 64, 980]])], thickness=4)
            img += m[..., None] * SU * a
        draw_text(img, "发射需要三把钥匙", W / 2, 1020, size=34, weight="bold", color=NEU, alpha=a, anchor="mt")
        b = ease_out(ramp(t, s2 + 5.0, s2 + 5.6))
        draw_text(img, "核鱼雷并未真正装配到战斗状态", W / 2, 1090, size=34, weight="bold", color=SU, alpha=b, anchor="mt")
        draw_text(img, "—— Savranskaya, 2005", W / 2, 1150, size=24, weight="regular", color=NEU_DIM, alpha=b, anchor="mt")
    return img


def headline(t, D, cues):
    img = bg((0.03, 0.03, 0.032), (0.012, 0.012, 0.014))
    s3 = cue(cues, "g03", 0, 0)
    s4 = cue(cues, "g04", 0, 2.0)
    s5 = cue(cues, "g05", 0, D * 0.6)
    fade_text(img, "2002 年 10 月 · 哈瓦那", W / 2, SAFE_TOP + 60, t, s3 + 0.1, size=30, weight="medium", color=NEU_DIM)
    fade_text(img, "美国国家安全档案馆主任 布兰顿", W / 2, SAFE_TOP + 110, t, s3 + 0.5, size=30, weight="medium", color=NEU_DIM)
    brk = ease_in_out(ramp(t, s5 + 0.5, s5 + 2.5))
    lines = ["一个叫阿尔希波夫的人", "拯救了世界"]
    if t > s4 - 0.2:
        a = ease_out(ramp(t, s4 - 0.2, s4 + 0.4))
        draw_text(img, "“用一句话当标题”", W / 2, 470, size=34, weight="medium", color=NEU_DIM, alpha=a * (1 - brk), anchor="mt")
        for i, l in enumerate(lines):
            for j, ch in enumerate(l):
                cw = 92
                x = W / 2 + (j - (len(l) - 1) / 2) * cw
                y = 600 + i * 130
                rng = np.random.default_rng(i * 31 + j)
                dx, dy = rng.normal(0, 160, 2) * brk
                draw_text(img, ch, x + dx, y + dy + brk * 80, size=92, weight="black", color=NEU,
                          alpha=a * (1 - 0.75 * brk), anchor="mt")
        line(img, (120, 560), (W - 120, 560), NEU, 0.5 * a * (1 - brk), 2)
        line(img, (120, 880), (W - 120, 880), NEU, 0.5 * a * (1 - brk), 2)
    fade_text(img, "标题总是整齐的", W / 2, 1060, t, s5 + 0.2, size=48, weight="black", color=SU)
    return img


# ============================================================================
# 8  the people outside the door
# ============================================================================

def split(t, D, cues):
    img = bg((0.004, 0.006, 0.012), (0.008, 0.012, 0.02))
    xx, yy = grid()
    a = ease_out(ramp(t, 0, 0.6))
    line(img, (W / 2, 300), (W / 2, 1180), NEU_DIM, 0.35 * a)
    # left: Washington room (window + desk), no faces
    _window(img, 270, 560, 230, 280, US, a, math.sin(t * 5) * 0.2)
    desk = np.zeros((H, W), np.float32)
    cv2.rectangle(desk, (140, 780), (400, 800), 1.0, -1)
    img += desk[..., None] * US * 0.35 * a
    draw_text(img, "华盛顿 · 10 月 27 日晚", 270, 860, size=30, weight="bold", color=US, alpha=a, anchor="mt")
    draw_text(img, "罗伯特·肯尼迪 ↔ 苏联大使", 270, 905, size=26, weight="medium", color=NEU, alpha=a, anchor="mt")
    # right: lone light on a dark sea
    sea = (yy > 700) & (xx > W / 2)
    img[sea] *= 0.6
    lm = mask_circle(810, 690, 5)
    img += glow(lm[..., None] * SU * 2.0 * a, (3, 12, 30), (1, 0.6, 0.3)) + lm[..., None] * SU * a
    refl = np.exp(-((xx - 810) / 4) ** 2) * np.exp(-np.clip(yy - 700, 0, None) / 60) * (yy > 700)
    img += refl[..., None] * SU * 0.3 * a
    draw_text(img, "大西洋 · B-59", 810, 860, size=30, weight="bold", color=SU, alpha=a, anchor="mt")
    # dashed line that never connects
    k = ease_in_out(ramp(t, 1.0, 3.0))
    p0, p1 = np.array([400.0, 560.0]), np.array([780.0, 680.0])
    gap_at = 0.62
    pm = p0 + (p1 - p0) * min(k, gap_at)
    m = mask_polyline(dashed(np.array([p0, pm]), 12, 10), thickness=2)
    img += m[..., None] * NEU * 0.6
    s1 = cue(cues, "h01", 0, 0)
    deals = ["不入侵古巴", "土耳其的木星导弹 · 几个月内撤走", "这一条 · 不公开"]
    for i, d in enumerate(deals):
        fade_text(img, d, 270, 990 + i * 52, t, s1 + 4.0 + i * 1.6, size=28, weight="medium",
                  color=(ALERT * 0.4 + NEU * 0.6) if i == 2 else NEU, anchor="mt")
    s2 = cue(cues, "h02", 0, D - 4)
    if t > s2:
        b = ease_out(ramp(t, s2, s2 + 0.5))
        panel(img, 560, 960, W - 60, 1090, alpha=b, edge=SU_DIM)
        draw_text(img, "10 月 28 日：宣布撤走导弹", 810, 990, size=28, weight="bold", color=NEU, alpha=b, anchor="mt")
        draw_text(img, "海底的人不知道", 810, 1040, size=26, weight="medium", color=SU, alpha=b, anchor="mt")
    return img


GITMO = (19.90, -75.15)


def gitmo(t, D, cues):
    cam = G.Cam(lat0=20.3, lon0=-76.2, R=14000, cx=W / 2, cy=720)
    img = canvas(np.array([0.008, 0.012, 0.02], np.float32))
    land, zz = G.land_mask(cam)
    img += land[..., None] * np.array([0.03, 0.04, 0.055], np.float32)
    coast = G.coast_mask(cam, thickness=2.0, limb_fade=False)
    img += coast[..., None] * NEU * 0.6
    p = G.ll2v(np.array(GITMO[0]), np.array(GITMO[1]))
    x, y, _, _ = cam.project(p[None])
    x, y = float(x[0]), float(y[0])
    a = ease_out(ramp(t, 0.3, 0.8))
    d = mask_circle(x, y, 9)
    img += glow(d[..., None] * US * 2 * a, (3, 10), (1, 0.5)) + d[..., None] * US * a
    draw_text(img, "关塔那摩美军基地", x + 20, y + 10, size=30, weight="bold", color=US, alpha=a, anchor="lt")
    k = ease_out(ramp(t, 1.2, 2.6))
    pts = G.small_circle(GITMO[0], GITMO[1], 24.0)
    sx, sy, _, _ = cam.project(pts)
    ring = mask_polyline(dashed(np.stack([sx, sy], 1), 14, 10), thickness=2.5)
    img += ring[..., None] * SU * k + glow(ring[..., None] * SU * 0.5 * k, (3, 12), (0.8, 0.4))
    draw_text(img, "约 24 公里内：一枚核巡航导弹（位置示意）", W / 2, 1010, size=30, weight="bold", color=SU, alpha=k, anchor="mt")
    fade_text(img, "古巴岛上的战术核武器", W / 2, SAFE_TOP + 60, t, 0.2, size=50, weight="black", color=NEU)
    s = cue(cues, "h03", 1, D) - 3.5
    fade_text(img, "美国人直到 1992 年才知道", W / 2, 1080, t, s, size=34, weight="bold", color=NEU)
    corner_tag(img, "古巴东南部 · 仅示海岸线", W - 48, SAFE_TOP + 140, color=NEU_DIM, size=22, anchor="rt")
    return img


def hotline(t, D, cues):
    img = bg()
    s4 = cue(cues, "h04", 0, 0)
    s5 = cue(cues, "h05", 0, D * 0.5)
    a = ease_out(ramp(t, s4, s4 + 0.5))
    pW, pM = np.array([200.0, 560.0]), np.array([880.0, 560.0])
    for p, lab, col in ((pW, "华盛顿", US), (pM, "莫斯科", SU)):
        m = mask_circle(p[0], p[1], 14)
        img += glow(m[..., None] * col * 1.5 * a, (3, 10), (1, 0.5)) + m[..., None] * col * a
        draw_text(img, lab, p[0], p[1] + 36, size=34, weight="bold", color=col, alpha=a, anchor="mt")
    k = ease_in_out(ramp(t, s4 + 0.6, s4 + 2.0))
    line(img, pW + np.array([16, 0]), pW + (pM - pW) * k - np.array([16 * k, 0]), NEU, 1.0, 3, 0.6)
    fade_text(img, "1963.6 · 直通热线", W / 2, 470, t, s4 + 1.5, size=34, weight="bold", color=NEU)
    fade_text(img, "1963.8 · 部分禁止核试验条约（美 · 英 · 苏）", W / 2, 700, t, s4 + 3.0, size=32, weight="medium",
              color=NEU_DIM)
    if t > s5:
        b = ease_out(ramp(t, s5, s5 + 0.6))
        c = np.array([W / 2, 930.0])
        for ang in range(0, 360, 45):
            e = c + np.array([math.cos(math.radians(ang)) * 300, math.sin(math.radians(ang)) * 150])
            m = mask_polyline(dashed(np.array([c, e]), 8, 8), thickness=1)
            img += m[..., None] * NEU_DIM * 0.5 * b
            fl = 0.5 + 0.5 * math.sin(t * 6 + ang)
            dm = mask_circle(e[0], e[1], 7)
            img += glow(dm[..., None] * ALERT * (0.8 + fl) * b, (3, 9), (1, 0.4)) + dm[..., None] * ALERT * b
        cm = mask_circle(c[0], c[1], 16, fill=False, thickness=2)
        img += cm[..., None] * NEU * b
        fade_text(img, "最危险的，是自己控制不了的末端", W / 2, 1140, t, s5 + 2.5, size=40, weight="black", color=NEU)
    return img


# ============================================================================
# 9  ending
# ============================================================================

def ending(t, D, cues):
    img = SC.surface_topdown(t * 0.5, plane_on=False, splashes=False, labels=False,
                             lights=1.0, beams_on=_beams_on(t, cues))
    s1 = cue(cues, "i01", 0, 0)
    s2 = cue(cues, "i02", 0, D * 0.3)
    e2 = cue(cues, "i02", 1, D * 0.6)
    fade_text(img, "1997 · 莫斯科 · 阿尔希波夫唯一一次公开谈起那一夜", W / 2, SAFE_TOP + 40, t, s1 + 0.2, size=28,
              weight="medium", color=NEU_DIM, alpha=1 - ramp(t, s2 - 0.5, s2))
    if s2 - 0.3 < t < e2 + 0.6:
        a = ease_out(ramp(t, s2 - 0.3, s2 + 0.3)) * (1 - ramp(t, e2 + 0.1, e2 + 0.6))
        dim = np.zeros_like(img)
        img = img * (1 - 0.6 * a) + dim * 0.6 * a
        tmp = img.copy()
        _quote_block(tmp, "“指挥员完全可能本能地下令紧急下潜。下潜之后，飞机是朝潜艇开火，还是朝旁边开火，不会再有人去问。那就是战争。”",
                     W / 2, 680, t, s2 - 0.1, size=52, color=NEU, width_chars=11)
        img = img * (1 - a) + tmp * a
    return img


def _beams_on(t, cues):
    s3 = cue(cues, "i03", 0, 999)
    s4 = cue(cues, "i04", 0, 999)
    s5 = cue(cues, "i05", 0, 999)
    return (1 if t < s5 + 1.5 else 0, 1 if t < s4 + 2.0 else 0, 1 if t < s3 + 1.5 else 0)


def credits(t, D, cues):
    img = canvas(np.array([0.0, 0.0, 0.0], np.float32))
    a = ease_out(ramp(t, 0.2, 0.8)) * (1 - ramp(t, D - 0.6, D))
    rows = [("主要来源", "bold", 34, NEU),
            ("Savranskaya, Journal of Strategic Studies 28:2 (2005)", "regular", 26, NEU_DIM),
            ("美国国家安全档案馆电子简报 #75、#399、#808、#813", "regular", 26, NEU_DIM),
            ("Dobbs, One Minute to Midnight (2008)", "regular", 26, NEU_DIM),
            ("", "regular", 20, NEU_DIM),
            ("档案图片：美国国家档案馆（公有领域）", "regular", 24, NEU_DIM),
            ("地图数据：Natural Earth（公有领域）", "regular", 24, NEU_DIM),
            ("「假想」段为示意，并未发生", "bold", 26, (1.0, 0.75, 0.9))]
    y = 560
    for txt, wgt, sz, col in rows:
        if txt:
            draw_text(img, txt, W / 2, y, size=sz, weight=wgt, color=col, alpha=a, anchor="mt")
        y += sz * 1.9
    return img
