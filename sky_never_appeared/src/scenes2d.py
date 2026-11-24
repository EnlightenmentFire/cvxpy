"""Reality-side motion graphics (cold blue / grey-white; US blue, Soviet amber)."""
import math
import numpy as np
import cv2
from common import *
import fx

BLUE = PAL['us']; AMBER = PAL['su']; RED = PAL['red']; WHITE = PAL['white']; GREY = PAL['grey']; DIM = PAL['dim']


# ------------------------------------------------------------------ backgrounds
_BG = {}
def bg_reality(kind='plain'):
    if kind not in _BG:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        g = np.exp(-(((x - W * 0.5) / (W * 0.9)) ** 2 + ((y - H * 0.42) / (H * 0.55)) ** 2))
        c = hexc('04070b')[None, None] + (hexc('0d1520') - hexc('04070b'))[None, None] * g[..., None]
        if kind == 'grid':
            m = np.zeros((H, W), np.float32)
            for gx in range(0, W, 60):
                m[:, gx] = 1
            for gy in range(0, H, 60):
                m[gy, :] = 1
            c = c + m[..., None] * hexc('1a2a3e')[None, None] * 0.35 * g[..., None]
        _BG[kind] = c.astype(np.float32)
    return _BG[kind].copy()


def finish(canvas, emis, fi, grain_amt=0.016, bloom_amt=1.0):
    out = canvas + emis + bloom(emis, 0.9 * bloom_amt)
    out = grade_reality(out)
    out = tonemap(out)
    out = vignette(out, 0.45)
    out = grain(out, fi, grain_amt)
    return out


# ------------------------------------------------------------------ glyphs
def missile_poly(x, y, h, angle=0.0):
    """slender ICBM silhouette, nose up, centred at (x, y), height h."""
    w = h * 0.13
    pts = np.array([[0, -0.5], [0.5, -0.36], [0.5, 0.38], [0.95, 0.5], [-0.95, 0.5], [-0.5, 0.38], [-0.5, -0.36]])
    pts = pts * [w, h]
    c, s = math.cos(angle), math.sin(angle)
    R = np.array([[c, -s], [s, c]])
    return pts @ R.T + [x, y]


def draw_missile(layer, x, y, h, color, alpha=1.0, angle=0.0, outline=True):
    p = missile_poly(x, y, h, angle)
    fill_poly(layer, p, color * 0.32, alpha)
    if outline:
        draw_polyline(layer, p, color, 2, alpha, closed=True)


def shield_poly(x, y, s):
    """heater shield: flat top with rounded corners, sides curving to a point."""
    pts = [(-0.5, -0.42), (-0.44, -0.5), (0.44, -0.5), (0.5, -0.42)]
    for k in np.linspace(0, 1, 14):
        pts.append((0.5 - 0.5 * k ** 1.7, -0.42 + 0.92 * k))
    for k in np.linspace(1, 0, 14):
        pts.append((-0.5 + 0.5 * k ** 1.7, -0.42 + 0.92 * k))
    return np.array(pts) * s + [x, y]


# ------------------------------------------------------------------ scene: balance of terror
def balance(t, phase='shield', fi=0):
    """phase: 'level' (balance), 'treaty', 'shield' (shield tips the balance)."""
    c = bg_reality('grid')
    e = np.zeros_like(c)
    cx, cy = W / 2, 820
    tilt = 0.0
    shield_a = 0.0
    if phase == 'shield':
        shield_a = smooth(remap(t, 0.3, 1.2))
        tilt = -0.16 * ease_out(remap(t, 0.8, 2.2))
    # fulcrum
    fill_poly(c, [(cx, cy + 6), (cx - 60, cy + 120), (cx + 60, cy + 120)], hexc('1a2330'))
    draw_polyline(c, [(cx, cy + 6), (cx - 60, cy + 120), (cx + 60, cy + 120)], GREY, 2, 0.8, closed=True)
    # beam
    L = 290
    ca, sa = math.cos(tilt), math.sin(tilt)
    left = (cx - L * ca, cy - L * sa)
    right = (cx + L * ca, cy + L * sa)
    draw_polyline(c, [left, right], WHITE, 4, 0.9)
    splat(e, cx, cy, 6, WHITE, 0.6)
    # pans with missiles
    for side, col, (px, py) in ((-1, BLUE, left), (1, AMBER, right)):
        for k in range(4):
            mx = px + (k - 1.5) * 44
            my = py - 88 - (abs(k - 1.5) * 5)
            jitter = 0.0
            if phase == 'shield' and side == 1:
                jitter = math.sin(t * 40 + k) * 2.0 * smooth(remap(t, 1.4, 2.0))
            draw_missile(c, mx + jitter, my, 140, col, 0.95)
        draw_polyline(c, [(px - 110, py - 12), (px + 110, py - 12)], col, 3, 0.9)
        draw_polyline(c, [(px - 110, py - 12), (px, py), (px + 110, py - 12)], col * 0.6, 1.5, 0.6)
    # shield in front of blue
    if shield_a > 0:
        sp = shield_poly(left[0] + 150, left[1] - 95, 200 * (0.6 + 0.4 * shield_a))
        fill_poly(c, sp, BLUE * 0.18, 0.85 * shield_a)
        draw_polyline(c, sp, BLUE, 4, shield_a, closed=True)
        draw_polyline(e, sp, BLUE * 0.8, 6, shield_a * 0.8, closed=True, add=True)
    # labels
    if phase in ('level', 'treaty'):
        text(c, '挡不住', left[0], cy + 210, 'bold', 46, BLUE, 0.95)
        text(c, '挡不住', right[0], cy + 210, 'bold', 46, AMBER, 0.95)
        text(c, '谁都不敢先动手', W / 2, 470, 'black', 76, WHITE, smooth(remap(t, 0.2, 0.8)))
        text(c, '恐怖平衡', W / 2, 375, 'medium', 38, GREY, smooth(remap(t, 0.0, 0.6)), tracking=12)
    if phase == 'shield':
        text(c, '矛 ＋ 盾', left[0] + 40, cy + 230, 'black', 56, BLUE, shield_a)
        text(c, '矛', right[0], cy + 230, 'black', 56, AMBER, shield_a)
        k = smooth(remap(t, 1.6, 2.4))
        text(c, '在对手眼里：', W / 2, 400, 'medium', 40, GREY, k)
        text(c, '先打你，', W / 2, 482, 'black', 74, AMBER, k)
        text(c, '再挡住你的还击', W / 2, 572, 'black', 74, AMBER, smooth(remap(t, 2.0, 2.8)))
    return c, e


# ------------------------------------------------------------------ scene: the letter
def letter(t, fi=0, show_box=True, quote='entering the engineering phase'):
    """schematic (not a facsimile) of Teller's Dec 1983 letter: typewriter lines, key phrase boxed."""
    c = bg_reality('plain')
    e = np.zeros_like(c)
    # paper card
    px0, py0, px1, py1 = 130, 300, 950, 1080
    k_in = ease_out(remap(t, 0.0, 0.8))
    dy = (1 - k_in) * 120
    paper = hexc('d9d3c5')
    rect(c, px0 + 10, py0 + 14 + dy, px1 + 10, py1 + 14 + dy, (0, 0, 0), 0.45 * k_in)
    rect(c, px0, py0 + dy, px1, py1 + dy, paper, 0.96 * k_in)
    ink = hexc('2b2b2e')
    text(c, '示意图 · 原信未公开，引文据后来报道', px1 - 24, py0 + 40 + dy, 'medium', 26, hexc('8a8478'), k_in, anchor='rc')
    text(c, 'December 22, 1983', px0 + 60, py0 + 110 + dy, 'type', 34, ink, k_in, anchor='lc')
    # greyed placeholder lines (not real text)
    rng = np.random.default_rng(4)
    yy = py0 + 190
    for i in range(11):
        if i == 5:
            yy += 80
            continue
        wline = rng.uniform(0.55, 0.95) * (px1 - px0 - 120)
        rect(c, px0 + 60, yy + dy, px0 + 60 + wline, yy + 12 + dy, hexc('bdb6a6'), k_in)
        yy += 44
    qy = py0 + 190 + 5 * 44 + 30
    typed = int(len(quote) * clamp((t - 0.9) / 1.4))
    text(c, quote[:typed], W / 2, qy + dy, 'typeb', 42, ink, k_in, anchor='center')
    if show_box:
        kb = smooth(remap(t, 2.5, 3.0))
        if kb > 0:
            tw = font('typeb', 42).getlength(quote)
            bx0, bx1 = W / 2 - tw / 2 - 22, W / 2 + tw / 2 + 22
            pts = [(bx0, qy - 40), (bx0 + (bx1 - bx0) * kb, qy - 40)]
            frame_rect(c, bx0, qy - 42 + dy, bx0 + (bx1 - bx0) * kb, qy + 40 + dy, RED, 5, kb)
    text(c, '泰勒致白宫科学顾问的信', W / 2, py1 + 70, 'bold', 40, WHITE, smooth(remap(t, 0.5, 1.0)))
    text(c, '“进入工程阶段”', W / 2, py1 + 150, 'black', 58, RED, smooth(remap(t, 2.8, 3.3)))
    return c, e


# ------------------------------------------------------------------ scene: HOE intercept + deception plan card
def hoe(t, fi=0, card=1.0, hit_t=1.2, strike_t=0.8):
    c = bg_reality('plain')
    e = np.zeros_like(c)
    # stars
    rng = np.random.default_rng(9)
    for _ in range(160):
        splat(e, rng.uniform(0, W), rng.uniform(0, H * 0.8), 0.7, (0.8, 0.85, 1), rng.uniform(0.1, 0.5))
    # two dots converging, collision at hit_t
    cx, cy = 540, 470
    k = clamp(t / max(hit_t, 1e-3))
    a0 = np.array([140.0, 820.0]); a1 = np.array([cx, cy])
    b0 = np.array([1000.0, 260.0]); b1 = np.array([cx, cy])
    if t < hit_t:
        pa = a0 + (a1 - a0) * k; pb = b0 + (b1 - b0) * k
        segs = []
        for j in range(12):
            q0 = a0 + (a1 - a0) * max(0, k - 0.2 * (j + 1) / 12); q1 = a0 + (a1 - a0) * max(0, k - 0.2 * j / 12)
            segs.append((tuple(q0), tuple(q1), 0.6 * (1 - j / 12), 2))
        draw_graded(e, segs, BLUE)
        splat(e, pa[0], pa[1], 4, BLUE, 1.6)
        splat(e, pb[0], pb[1], 4, (0.9, 0.9, 0.9), 1.2)
        text(c, '拦截弹', pa[0] + 70, pa[1] + 20, 'medium', 34, BLUE, 0.9, anchor='lc')
        text(c, '模拟弹头', pb[0] - 30, pb[1] - 50, 'medium', 34, GREY, 0.9, anchor='rc')
    else:
        burst = fx.Burst(seed=31, n=70)
        burst.draw(e, cx, cy, (t - hit_t) * 0.45, scale=1.1, color=(0.75, 0.85, 1.0))
    text(c, '1984 年 6 月  第四次试验', W / 2, 270, 'bold', 42, WHITE, smooth(remap(t, 0.0, 0.5)) * (1 - 0.5 * card))
    text(c, '太空中直接撞毁', W / 2, 760, 'black', 64, WHITE, smooth(remap(t, 1.6, 2.2)) * (1 - card))
    # deception plan card (schematic)
    if card > 0:
        k = smooth(card)
        rect(c, 0, 0, W, H, (0, 0, 0), 0.35 * k)
        x0, y0, x1, y1 = 110, 640, 970, 1240
        y0 += (1 - k) * 80; y1 += (1 - k) * 80
        rect(c, x0, y0, x1, y1, hexc('0e151e'), 0.97 * k)
        frame_rect(c, x0, y0, x1, y1, GREY, 2, 0.8 * k)
        text(c, '欺骗计划（示意）', x0 + 40, y0 + 58, 'bold', 36, GREY, k, anchor='lc')
        fade_txt = 1 - 0.45 * smooth(remap(t, strike_t + 0.1, strike_t + 0.6))
        text(c, '如果拦截弹没打中，但飞得够近', x0 + 40, y0 + 150, 'black', 46, WHITE, k * fade_txt, anchor='lc')
        text(c, '→ 引爆靶弹，假装命中', x0 + 40, y0 + 230, 'black', 46, AMBER, k * fade_txt, anchor='lc')
        text(c, '目的：影响苏联的判断、军控谈判和开支', x0 + 40, y0 + 310, 'medium', 32, GREY, k * fade_txt, anchor='lc')
        ks = smooth(remap(t, strike_t, strike_t + 0.5)) * k
        if ks > 0:
            draw_polyline(c, [(x0 + 30, y0 + 350), (x0 + 30 + (x1 - x0 - 60) * ks, y0 + 110)], RED, 7, ks)
            text(c, '1983 年 9 月，计划取消', x0 + 40, y0 + 440, 'black', 50, RED, smooth(remap(t, strike_t + 0.5, strike_t + 0.9)) * k, anchor='lc')
            text(c, '第三次试验前取消 · 第四次是真撞上的', x0 + 40, y0 + 515, 'bold', 38, WHITE, smooth(remap(t, strike_t + 0.6, strike_t + 1.0)) * k, anchor='lc')
    return c, e


# ------------------------------------------------------------------ scene: Reykjavik
def hofdi(layer, x, y, s, alpha=1.0, lit=1.0):
    """simple silhouette of a white two-storey house with a pitched roof (Hofdi, schematic)."""
    wall = hexc('d8dde2') * 0.85
    roof = hexc('2a3038')
    w, h = 520 * s, 230 * s
    rect(layer, x - w / 2, y - h, x + w / 2, y, wall, alpha)
    fill_poly(layer, [(x - w / 2 - 14 * s, y - h), (x + w / 2 + 14 * s, y - h), (x + w / 2 - 60 * s, y - h - 120 * s),
                      (x - w / 2 + 60 * s, y - h - 120 * s)], roof, alpha)
    # central gable
    fill_poly(layer, [(x - 90 * s, y - h), (x + 90 * s, y - h), (x, y - h - 150 * s)], wall, alpha)
    draw_polyline(layer, [(x - 100 * s, y - h), (x, y - h - 160 * s), (x + 100 * s, y - h)], roof, 6 * s, alpha)
    rect(layer, x + 120 * s, y - h - 160 * s, x + 150 * s, y - h - 70 * s, roof, alpha)
    for row in range(2):
        for col in range(6):
            if col in (2, 3) and row == 0:
                continue
            wx = x - w / 2 + 40 * s + col * 80 * s
            wy = y - h + 40 * s + row * 100 * s
            rect(layer, wx, wy, wx + 36 * s, wy + 56 * s, hexc('ffd99a') * (0.25 + 0.75 * lit), alpha)
    rect(layer, x - 30 * s, y - 80 * s, x + 30 * s, y, hexc('2a3038'), alpha)


def reykjavik_lab(t, fi=0):
    """'实验室' fills the screen, then splits."""
    c = bg_reality('plain')
    e = np.zeros_like(c)
    # night sky gradient + house at bottom
    hofdi(c, W / 2, 1250, 0.72, alpha=0.9, lit=0.8)
    rect(c, 0, 1250, W, H, hexc('06090d'), 1.0)
    k = ease_out(remap(t, 0.0, 0.7))
    split = smooth(remap(t, 1.4, 2.4))
    size = int(250 + 30 * k)
    word = '实验室'
    spr = text_sprite(word, 'black', size, (0.95, 0.96, 0.98), 30, 0.0, 0, (0, 0, 0), 1.2, 'center')
    rgb, a = spr
    hh, ww = a.shape
    cy0 = 600
    # crack: jagged line through the middle, halves drift apart
    if split <= 0:
        blit(c, spr, W / 2, cy0, alpha=k)
    else:
        rng = np.random.default_rng(3)
        xs = np.linspace(0, ww, 14)
        ys = hh / 2 + rng.normal(0, hh * 0.06, 14)
        yy, xx = np.mgrid[0:hh, 0:ww]
        cut = np.interp(xx[0], xs, ys)[None, :]
        top = yy < cut
        for part, dy, dx, rot in ((top, -1, -1, -0.03), (~top, 1, 1, 0.03)):
            aa = a * part
            M = cv2.getRotationMatrix2D((ww / 2, hh / 2), math.degrees(rot * split), 1.0)
            M[0, 2] += dx * 26 * split
            M[1, 2] += dy * 46 * split
            r2 = cv2.warpAffine(rgb, M, (ww, hh))
            a2 = cv2.warpAffine(aa.astype(np.float32), M, (ww, hh))
            blit(c, (r2, a2), W / 2, cy0, alpha=k)
        # glowing crack
        pts = [(W / 2 - ww / 2 + x_, cy0 - hh / 2 + y_) for x_, y_ in zip(xs, ys)]
        draw_polyline(e, pts, AMBER * 1.4, 3, split * (1 - smooth(remap(t, 2.4, 3.2))) + 0.2 * split, add=True)
    text(c, 'LABORATORY', W / 2, cy0 + 200, 'type', 44, GREY, k, tracking=10)
    text(c, '1986 年 10 月 · 雷克雅未克', W / 2, 300, 'bold', 40, WHITE, smooth(remap(t, 0.2, 0.7)))
    return c, e


# ------------------------------------------------------------------ scene: Polyus rotation diagram
def polyus_craft(layer, cx, cy, ang, L=300, Wd=52, alpha=1.0, burn=0.0, emis=None):
    """side-view silhouette: long black cylinder, nose cone, engine block at the +x end."""
    body = np.array([[-L / 2, -Wd / 2], [L / 2, -Wd / 2], [L / 2, Wd / 2], [-L / 2, Wd / 2]])
    nose = np.array([[-L / 2, -Wd / 2], [-L / 2 - 46, 0], [-L / 2, Wd / 2]])
    noz = np.array([[L / 2, -14], [L / 2 + 30, -24], [L / 2 + 30, 24], [L / 2, 14]])
    band = np.array([[L / 2 - 70, -Wd / 2], [L / 2 - 58, -Wd / 2], [L / 2 - 58, Wd / 2], [L / 2 - 70, Wd / 2]])
    Rm = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    for poly, col in ((body, hexc('16181c')), (nose, hexc('16181c')), (noz, hexc('5a606a')), (band, hexc('3a3f47'))):
        p = poly @ Rm.T + [cx, cy]
        fill_poly(layer, p, col, alpha)
        draw_polyline(layer, p, GREY, 2, 0.85 * alpha, closed=True)
    if burn > 0 and emis is not None:
        tip = np.array([L / 2 + 30, 0]) @ Rm.T + [cx, cy]
        far = np.array([L / 2 + 30 + 220 * burn, 0]) @ Rm.T + [cx, cy]
        fx.tapered_beam(emis, tip, far, AMBER * 1.3, 24, 3, burn)
        splat(emis, tip[0], tip[1], 14, AMBER, 1.2 * burn)


def polyus_diagram(t, fi=0):
    """planned half turn (dashed) vs. the ~two full tumbles reported by the official Soviet
    post-flight report (solid spiral). t in seconds; rotation runs 0.6..4.6 s."""
    c = bg_reality('grid')
    e = np.zeros_like(c)
    cx, cy = W / 2, 760
    R = 215
    # planned: half circle, dashed
    kp = smooth(remap(t, 0.2, 0.9))
    angs = np.linspace(math.pi, math.pi + math.pi * kp, 72)
    for i in range(0, 70, 4):
        p = [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in angs[i:i + 2]]
        draw_polyline(c, p, GREY, 4, 0.9)
    if kp > 0.99:
        ex, ey = cx + R * math.cos(2 * math.pi), cy + R * math.sin(2 * math.pi)
        draw_polyline(c, [(ex - 16, ey - 16), (ex, ey), (ex + 16, ey - 16)], GREY, 4, 0.9)
    text(c, '计划：掉头转半圈，再点火', cx, 420, 'bold', 42, GREY, kp)
    # actual: ~2 revolutions, drawn as an outward spiral so the turns are countable
    ka = remap(t, 0.6, 4.6)
    turns = 2.0 * ease_io(ka)
    n = max(2, int(220 * turns / 2) + 2)
    th = np.linspace(0, 2 * math.pi * turns, n)
    rr = R + 36 + th / (2 * math.pi) * 40
    pts = [(cx + r_ * math.cos(math.pi + a), cy + r_ * math.sin(math.pi + a)) for a, r_ in zip(th, rr)]
    if turns > 0.01:
        draw_polyline(c, pts, AMBER, 5, 1.0)
        draw_polyline(e, pts, AMBER * 0.6, 8, 0.5, add=True)
        hx, hy = pts[-1]
        splat(e, hx, hy, 9, AMBER, 1.5)
    lab = '第 1 圈' if turns < 1.0 else '第 2 圈'
    if 0.15 < turns < 1.98:
        text(c, lab, cx + 330, cy - 250, 'black', 44, AMBER, 1.0)
    # craft rotates with the actual angle
    ang = 2 * math.pi * turns
    burn = smooth(remap(t, 3.6, 4.2)) * (1 - smooth(remap(t, 6.0, 6.6)))
    polyus_craft(c, cx, cy, ang, L=250, Wd=46, burn=burn, emis=e)
    ks = smooth(remap(t, 4.6, 5.2))
    text(c, '实际：停不下来，翻了约两整圈', cx, 1110, 'black', 46, AMBER, ks)
    text(c, '发动机在翻滚中点火 → 没能入轨', cx, 1180, 'bold', 40, WHITE, smooth(remap(t, 5.0, 5.6)))
    text(c, '据苏联官方事后报告', cx, 1240, 'medium', 30, GREY, smooth(remap(t, 4.8, 5.4)))
    text(c, '1987 年 5 月 15 日 · “极地”号', W / 2, 290, 'bold', 40, WHITE, smooth(remap(t, 0.0, 0.5)))
    return c, e


# ------------------------------------------------------------------ title card
def title_card(t, fi=0):
    c = bg_reality('plain')
    e = np.zeros_like(c)
    k = smooth(remap(t, 0.2, 1.2))
    text(c, '冷战核按钮 · 第二期', W / 2, 640, 'medium', 40, GREY, k, tracking=10)
    text(c, '一片没有出现的', W / 2, 800, 'black', 108, WHITE, smooth(remap(t, 0.5, 1.5)))
    text(c, '天空', W / 2, 950, 'black', 150, WHITE, smooth(remap(t, 0.8, 1.8)))
    draw_polyline(e, [(W / 2 - 220 * k, 1070), (W / 2 + 220 * k, 1070)], BLUE * 0.9, 2, k, add=True)
    text(c, '1983 — 1987', W / 2, 1130, 'type', 40, GREY, smooth(remap(t, 1.2, 2.0)), tracking=6)
    return c, e
