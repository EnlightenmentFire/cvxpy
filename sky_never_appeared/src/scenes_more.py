"""Remaining reality / schematic scenes. Every function: (t local seconds) -> (canvas, emis)."""
import math, os
import numpy as np
import cv2
from common import *
import fx
from scenes2d import (bg_reality, BLUE, AMBER, RED, WHITE, GREY, DIM, draw_missile, shield_poly,
                      hofdi, polyus_craft)


def card(c, x0, y0, x1, y1, alpha=1.0, border=GREY, fill=None):
    rect(c, x0, y0, x1, y1, hexc('0e151e') if fill is None else fill, 0.95 * alpha)
    frame_rect(c, x0, y0, x1, y1, border, 2, 0.75 * alpha)


def tag(c, s, x, y, alpha=1.0, color=None, anchor='lc'):
    """small source tag like 【美方记录】."""
    color = GREY if color is None else color
    w_, h_ = text(c, s, x, y, 'medium', 28, color, alpha * 0.95, anchor=anchor)
    return w_


def big(c, s, y, alpha=1.0, color=WHITE, size=78, kind='black'):
    text(c, s, W / 2, y, kind, size, color, alpha, line_gap=1.3)


# ------------------------------------------------------------------ 02 terror: treaty card
def treaty(t):
    c = bg_reality('grid'); e = np.zeros_like(c)
    k = smooth(remap(t, 0.0, 0.6))
    text(c, '1972', W / 2, 360, 'black', 120, WHITE, k)
    text(c, '反导条约', W / 2, 480, 'black', 64, WHITE, k, tracking=8)
    text(c, '反导系统：拦截来袭导弹的系统', W / 2, 560, 'medium', 34, GREY, smooth(remap(t, 0.4, 1.0)))
    # two sides, each two sites -> one site
    for side, col in ((-1, BLUE), (1, AMBER)):
        cx = W / 2 + side * 230
        ka = smooth(remap(t, 0.8, 1.5))
        n_sites = 2 if t < 3.2 else 1
        for s in range(2):
            a = ka * (1.0 if s < n_sites else max(0.0, 1 - smooth(remap(t, 3.2, 3.8))))
            y = 720 + s * 150
            ring(c, cx, y, 46, col, 3, a, add=False)
            text(c, '≤100', cx, y, 'bold', 30, col, a)
        text(c, '美' if side < 0 else '苏', cx, 650, 'black', 40, col, ka)
    text(c, '每方两处、每处最多一百枚拦截弹', W / 2, 1040, 'bold', 36, GREY, smooth(remap(t, 1.2, 1.8)))
    text(c, '1974 年：减为一处', W / 2, 1100, 'bold', 36, WHITE, smooth(remap(t, 3.2, 3.8)))
    return c, e


# ------------------------------------------------------------------ 03 reagan
_ENV = {}
def clip_env(name):
    if name not in _ENV:
        import soundfile as sf
        w, sr = sf.read(os.path.join(SCRATCH, 'reagan', name + '.wav'))
        if w.ndim == 2:
            w = w.mean(1)
        hop = sr // FPS
        n = len(w) // hop
        env = np.array([np.sqrt((w[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
        _ENV[name] = env / (env.max() + 1e-9)
    return _ENV[name]


def speech_card(t, clip=None, en_text='', highlight=None):
    """date card + waveform of the original broadcast audio + English text."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, '1983 年 3 月 23 日 · 白宫', W / 2, 300, 'bold', 40, WHITE, smooth(remap(t, 0, 0.5)))
    text(c, '全国电视讲话 · 原声', W / 2, 352, 'medium', 30, GREY, smooth(remap(t, 0.2, 0.7)))
    # waveform
    if clip:
        env = clip_env(clip)
        fi = int(t * FPS)
        bars = 48
        for b in range(bars):
            idx = fi - (bars - b) // 2
            v = env[idx] if 0 <= idx < len(env) else 0.0
            h = 6 + 150 * v
            x = W / 2 + (b - bars / 2) * 16
            rect(c, x, 560 - h / 2, x + 8, 560 + h / 2, BLUE, 0.85)
            rect(e, x, 560 - h / 2, x + 8, 560 + h / 2, BLUE * 0.25, 1.0)
    if en_text:
        k = smooth(remap(t, 0.3, 1.0))
        lines = wrap_en(en_text, 30)
        y0 = 700 if len(lines) > 6 else 760
        for i, ln in enumerate(lines):
            text(c, ln, W / 2, y0 + i * 54, 'type', 41, WHITE, k)
        if highlight:
            text(c, highlight, W / 2, y0 + len(lines) * 54 + 50, 'typeb', 54, AMBER, smooth(remap(t, 1.0, 1.6)))
    return c, e


def wrap_en(s, n):
    words, lines, cur = s.split(), [], ''
    for w_ in words:
        if len(cur) + len(w_) + 1 > n:
            lines.append(cur); cur = w_
        else:
            cur = (cur + ' ' + w_).strip()
    if cur:
        lines.append(cur)
    return lines


def plain_meaning(t):
    """'你敢打我→立刻毁灭你' crossed out -> intercept arc."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    k1 = smooth(remap(t, 0, 0.5))
    text(c, '“你敢打我，我就立刻毁灭你”', W / 2, 420, 'black', 50, GREY, k1)
    ks = smooth(remap(t, 1.2, 1.7))
    if ks > 0:
        draw_polyline(c, [(140, 420), (140 + 800 * ks, 420)], RED, 6, 1.0)
    # missile arc intercepted
    k2 = remap(t, 1.6, 3.4)
    pts = [(160 + 760 * u, 1050 - 520 * math.sin(math.pi * u)) for u in np.linspace(0, min(k2, 0.62), 40)]
    if len(pts) > 1 and k2 > 0:
        fx.plume(e, pts, AMBER, head=1.0 if k2 < 0.62 else 0.0, width=3)
    if k2 >= 0.62:
        hx, hy = 160 + 760 * 0.62, 1050 - 520 * math.sin(math.pi * 0.62)
        fx.Burst(seed=5, n=30).draw(e, hx, hy, (t - (1.6 + 0.62 * 1.8)) * 0.6, scale=0.7, color=(0.7, 0.85, 1.0))
    draw_polyline(c, [(100, 1080), (980, 1080)], DIM, 2, 0.8)
    text(c, '落地之前，把它打下来', W / 2, 1180, 'black', 56, BLUE, smooth(remap(t, 2.6, 3.2)))
    return c, e


def shield_vs_spear(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    k = smooth(remap(t, 0, 0.6))
    text(c, '他要的不是更多的矛', W / 2, 430, 'black', 64, GREY, k)
    ks = smooth(remap(t, 0.8, 1.5))
    sp = shield_poly(W / 2, 760, 300 * (0.7 + 0.3 * ks))
    fill_poly(c, sp, BLUE * 0.18, ks)
    draw_polyline(c, sp, BLUE, 5, ks, closed=True)
    draw_polyline(e, sp, BLUE * 0.7, 8, ks * 0.7, closed=True, add=True)
    text(c, '而是一面盾', W / 2, 1060, 'black', 76, BLUE, ks)
    q = smooth(remap(t, 2.2, 2.8))
    text(c, 'Wouldn’t it be better to save lives', W / 2, 1180, 'type', 36, GREY, q)
    text(c, 'than to avenge them?', W / 2, 1228, 'type', 36, GREY, q)
    return c, e


_ART = {}
def concept_art(t, dur=6.0):
    """1984 USAF artwork (public domain), slow push, labelled as official imagination."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    if 'img' not in _ART:
        im = cv2.imread(os.path.join(SCRATCH, 'sources', 'concept_art', 'Space_Laser_Satellite_Defense_System_Concept.jpg'))
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        _ART['img'] = im
    im = _ART['img']
    k = smooth(remap(t, 0, 0.6))
    z = 1.0 + 0.12 * remap(t, 0, dur)
    # crop region drifting toward the laser station
    h0, w0 = im.shape[:2]
    cw, ch = int(w0 / z), int(h0 / z)
    cx = int(w0 * 0.48 - cw / 2 + (w0 - cw) * 0.1 * remap(t, 0, dur))
    cy = int((h0 - ch) * 0.3)
    crop = im[max(0, cy):cy + ch, max(0, cx):cx + cw]
    tw = W - 80
    th = int(tw * crop.shape[0] / crop.shape[1])
    crop = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA)
    y0 = 520
    reg = c[y0:y0 + th, 40:40 + tw]
    reg[:] = reg * (1 - k) + crop[:reg.shape[0]] * k
    frame_rect(c, 40, y0, 40 + tw, y0 + th, GREY, 2, 0.8 * k)
    text(c, '当年官方想象图', W / 2, 380, 'black', 58, WHITE, k)
    text(c, '美国空军 · 1984 年', W / 2, 450, 'medium', 32, GREY, k)
    text(c, '“太空激光卫星防御系统”概念图（美国政府作品）', W / 2, y0 + th + 50, 'medium', 28, GREY, k)
    return c, e


def star_wars_name(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    k = smooth(remap(t, 0, 0.5))
    text(c, '1983 年 3 月 24 日 ·《华盛顿邮报》', W / 2, 360, 'bold', 38, GREY, k)
    text(c, '“reckless', W / 2, 520, 'type', 60, GREY, k)
    text(c, 'STAR WARS', W / 2, 640, 'black', 120, WHITE, smooth(remap(t, 0.3, 0.9)), tracking=6)
    text(c, 'schemes”', W / 2, 760, 'type', 60, GREY, k)
    text(c, '——参议员肯尼迪的批评', W / 2, 860, 'medium', 34, GREY, smooth(remap(t, 0.6, 1.1)))
    kk = smooth(remap(t, 2.4, 3.0))
    text(c, '正式名称：战略防御倡议', W / 2, 1040, 'black', 50, BLUE, kk)
    text(c, 'Strategic Defense Initiative', W / 2, 1110, 'type', 34, GREY, kk)
    return c, e


def reagan_admits(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    k = smooth(remap(t, 0, 0.6))
    text(c, '里根在同一篇讲话里：', W / 2, 400, 'bold', 40, GREY, k)
    for i, ln in enumerate(wrap_en('“If paired with offensive systems, they can be viewed as fostering an aggressive policy, and no one wants that.”', 30)):
        text(c, ln, W / 2, 540 + i * 60, 'type', 40, WHITE, k)
    text(c, '防御系统和进攻力量配在一起，', W / 2, 900, 'black', 48, AMBER, smooth(remap(t, 1.0, 1.6)))
    text(c, '可能被看成一种侵略', W / 2, 970, 'black', 48, AMBER, smooth(remap(t, 1.0, 1.6)))
    return c, e


def takeaway(t, lines, color=WHITE, y=640, size=66):
    """chapter-closing '这说明什么' card."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, '这说明什么？', W / 2, y - 150, 'bold', 40, GREY, smooth(remap(t, 0, 0.5)))
    for i, ln in enumerate(lines):
        text(c, ln, W / 2, y + i * (size + 26), 'black', size, color, smooth(remap(t, 0.4 + 0.5 * i, 1.0 + 0.5 * i)))
    return c, e


# ------------------------------------------------------------------ 04 excalibur
def boost_decoy(t, phase='boost'):
    """schematic of boost phase -> bus releasing warheads + decoys (imagined)."""
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    rng = np.random.default_rng(4)
    for _ in range(220):
        splat(e, rng.uniform(0, W), rng.uniform(0, 1300), 0.7, (0.9, 0.9, 1), rng.uniform(0.05, 0.4))
    # earth limb
    cy_e = 3300
    m = np.zeros((H, W), np.float32)
    cv2.circle(m, (W // 2, cy_e), 2000, 1.0, -1, cv2.LINE_AA)
    c[...] = c * (1 - m[..., None]) + hexc('061020') * m[..., None]
    ring(e, W / 2, cy_e, 2000, (0.3, 0.55, 1.0), 6, 0.6)
    # rising missile
    tb = 4.0
    u = min(t, tb) / tb
    path = lambda uu: (300 + 420 * uu, 1290 - 900 * (1 - (1 - uu) ** 2))
    pts = [path(x) for x in np.linspace(0, u, 40)]
    fx.plume(e, pts, AMBER, head=1.0 if t < tb else 0.0, width=4, fade=1.0 if t < tb + 1 else max(0, 1 - (t - tb - 1)))
    if t < tb + 0.5:
        text(c, '助推段：火箭还在燃烧', 600, 1240, 'bold', 40, AMBER, smooth(remap(t, 0.5, 1.0)) * (1 - smooth(remap(t, tb, tb + 0.5))), anchor='center')
    # release objects
    if t > tb:
        hx, hy = path(1.0)
        tau = t - tb
        objs = [(-1.0, 'w'), (-0.6, 'd'), (-0.2, 'w'), (0.2, 'd'), (0.6, 'd'), (1.0, 'w'), (0.0, 'd')]
        for k, (dx, kind) in enumerate(objs):
            # spread out, then drift slowly so the labelled objects stay in frame
            x = hx + dx * 170 * min(tau, 2.5) / 2.5 + 25 * min(tau, 2.5) + 5 * max(tau - 2.5, 0)
            y = hy + 60 * min(tau, 2.5) + 12 * max(tau - 2.5, 0) + (k % 3 - 1) * 40 * min(tau, 2.0)
            splat(e, x, y, 6, (1.0, 0.95, 0.85), 1.6)
            if phase == 'decoy' and t > tb + 2.0:
                lab = '真弹头' if kind == 'w' else '诱饵'
                col = WHITE if kind == 'w' else GREY
                a = smooth(remap(t, tb + 2.0, tb + 2.6))
                if k in (0, 1, 3):
                    text(c, lab, x, y - 44, 'bold', 38, col, a)
    return c, e


def xray_schematic(t):
    """imagined: bomb at centre, bundle of rods, flash, beams. labelled as concept."""
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    cx, cy = W / 2, 760
    rng = np.random.default_rng(12)
    dirs = [(math.cos(a), math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False) + 0.1]
    flash_t = 3.0
    if t < flash_t:
        ring(c, cx, cy, 70, (0.75, 0.78, 0.85), 3, 1.0, add=False)
        fill_poly(c, [(cx - 50, cy - 50), (cx + 50, cy - 50), (cx + 50, cy + 50), (cx - 50, cy + 50)], hexc('3a404a'), 0.9)
        text(c, '核弹', cx, cy, 'bold', 32, WHITE, 1.0)
        kr = smooth(remap(t, 0.4, 1.4))
        for dx, dy in dirs:
            draw_polyline(c, [(cx + dx * 90, cy + dy * 90), (cx + dx * (90 + 200 * kr), cy + dy * (90 + 200 * kr))], (0.8, 0.84, 0.9), 5, kr)
        text(c, '周围一圈细棒', cx, cy + 380, 'bold', 42, GREY, smooth(remap(t, 1.0, 1.6)))
    else:
        tau = t - flash_t
        fx.Burst(seed=8, n=50).draw(e, cx, cy, tau * 0.6, scale=1.0, color=(0.9, 0.9, 1.0), power=1.3)
        on = math.exp(-max(tau - 0.2, 0) / 1.2)
        for dx, dy in dirs:
            fx.beam(e, (cx + dx * 90, cy + dy * 90), (cx + dx * 1400, cy + dy * 1400), (0.75, 0.55, 1.0), 1.4, on * 0.9)
        text(c, '一瞬间，每根射出一道 X 射线', cx, cy + 420, 'bold', 42, WHITE, smooth(remap(t, flash_t + 0.6, flash_t + 1.2)))
        text(c, '打完，它自己也没了', cx, cy + 490, 'black', 48, AMBER, smooth(remap(t, flash_t + 1.6, flash_t + 2.2)))
    text(c, 'X 射线激光 · 设想示意', W / 2, 330, 'bold', 40, (0.95, 0.85, 1.0), smooth(remap(t, 0, 0.5)))
    return c, e


def submarine(t):
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    # sea
    rect(c, 0, 980, W, H, hexc('061322'), 1.0)
    draw_polyline(c, [(0, 980), (W, 980)], (0.3, 0.5, 0.8), 2, 0.8)
    # sub silhouette
    sx, sy = 520, 1120
    hull = [(sx - 300, sy), (sx - 250, sy - 40), (sx + 260, sy - 40), (sx + 320, sy), (sx + 260, sy + 38), (sx - 250, sy + 38)]
    fill_poly(c, hull, hexc('1b2430'))
    draw_polyline(c, hull, GREY, 2, 0.9, closed=True)
    fill_poly(c, [(sx - 40, sy - 40), (sx - 20, sy - 100), (sx + 60, sy - 100), (sx + 70, sy - 40)], hexc('1b2430'))
    k = remap(t, 1.0, 3.5)
    if k > 0:
        pts = [(sx + 20, 980 - 900 * (u ** 1.4)) for u in np.linspace(0, k, 30)]
        fx.plume(e, pts, AMBER, 1.0, width=4)
    text(c, '警报一响，再发射到太空', W / 2, 420, 'black', 54, WHITE, smooth(remap(t, 0.2, 0.8)))
    text(c, '设想示意', W / 2, 340, 'medium', 32, (0.95, 0.85, 1.0), smooth(remap(t, 0.2, 0.8)))
    return c, e


def nevada(t, phase=0):
    """phase 0: desert top-down + dive underground + blast; date cards come from caller."""
    c = new_canvas(hexc('0b0a09')); e = np.zeros_like(c)
    if 'sand' not in _ART:
        rng = np.random.default_rng(2)
        n = np.zeros((H, W), np.float32)
        for s, a in ((256, 0.5), (64, 0.3), (8, 0.2)):
            g = rng.normal(0, 1, (H // s + 2, W // s + 2)).astype(np.float32)
            n += cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC) * a
        _ART['sand'] = (n * 0.5 + 0.5).clip(0, 1)
    sand = _ART['sand']
    dive = smooth(remap(t, 2.0, 4.0))
    if dive < 1.0:
        z = 1.0 + 2.5 * dive
        M = np.array([[z, 0, W / 2 * (1 - z)], [0, z, 760 * (1 - z)]], np.float32)
        sd = cv2.warpAffine(sand, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        col = hexc('5a4a38') * (0.6 + 0.5 * sd[..., None])
        c[:] = col * (1 - dive)
        ring(c, W / 2, 760, 26 * (1 + 2.5 * dive), (0.85, 0.85, 0.8), 3, 1 - dive, add=False)
        text(c, '内华达试验场 · 地下', W / 2, 330, 'bold', 40, WHITE, smooth(remap(t, 0.2, 0.7)) * (1 - dive))
    if dive > 0:
        # cross-section: sky band, desert surface, rock strata, shaft, device chamber
        g = dive
        rect(c, 0, 0, W, 520, hexc('0c0e12') * g, 1.0)
        rect(c, 0, 520, W, H, hexc('4a3b2a') * g, 1.0)
        for k in range(7):
            y = 560 + k * 120
            col = [hexc('5a4834'), hexc('4c3c2b'), hexc('5e4c37'), hexc('463726'), hexc('544330'), hexc('3f3123'), hexc('4d3d2c')][k]
            rect(c, 0, y, W, y + 120, col * g, 1.0)
            draw_polyline(c, [(0, y), (W, y + 6 * math.sin(k * 1.7))], hexc('2a2118') * g, 2, 1.0)
        rect(c, W / 2 - 9, 520, W / 2 + 9, 1010, hexc('0b0b0b'), g)
        rect(c, W / 2 - 40, 1010, W / 2 + 40, 1070, hexc('1a1a1a'), g)
        text(c, '地表', 150, 495, 'bold', 30, GREY, g, anchor='lc')
        text(c, '竖井', W / 2 + 40, 760, 'bold', 30, GREY, g, anchor='lc')
        text(c, '核装置 + 测量设备', W / 2 + 70, 1040, 'bold', 30, GREY, g * (1 - smooth(remap(t, 4.4, 4.8))), anchor='lc')
        tb = 4.8
        if t > tb:
            tau = t - tb
            r = 60 + 300 * (1 - math.exp(-tau * 1.8))
            splat(e, W / 2, 1040, r * 0.45, (1.0, 0.85, 0.6), 3.0 * math.exp(-tau / 0.6))
            for k in range(4):
                ring(e, W / 2, 1040, r * (0.55 + 0.35 * k), (1.0, 0.65, 0.35), 4, 0.6 * math.exp(-tau / (0.7 + 0.3 * k)))
            lift = 70 * (1 - math.exp(-max(tau - 0.4, 0) * 1.2))
            if lift > 1:
                fill_poly(c, [(0, 520), (W, 520), (W, 520 - lift * 0.4), (W / 2 + 260, 520 - lift), (W / 2 - 260, 520 - lift), (0, 520 - lift * 0.4)],
                          hexc('7a6448'), 0.9)
    return c, e


def date_card(c, s1, s2, y, alpha, col=WHITE, col2=GREY):
    if alpha <= 0:
        return
    card(c, 120, y - 70, W - 120, y + 70, alpha)
    text(c, s1, W / 2, y - 22, 'black', 44, col, alpha)
    text(c, s2, W / 2, y + 34, 'medium', 32, col2, alpha)


def unsent(t):
    """Woodruff's correction letter: drafted, not sent. schematic."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    k = ease_out(remap(t, 0, 0.6))
    x0, y0, x1, y1 = 250, 420, 830, 1000
    rect(c, x0, y0, x1, y1, hexc('cfc8b8'), 0.95 * k)
    for i in range(9):
        rect(c, x0 + 50, y0 + 90 + i * 50, x1 - 60 - (i % 3) * 60, y0 + 102 + i * 50, hexc('a9a294'), k)
    text(c, '更正信（示意）', W / 2, y0 + 50, 'bold', 30, hexc('5a554c'), k)
    ks = smooth(remap(t, 0.8, 1.2))
    if ks > 0:
        text(c, '未发出', W / 2, (y0 + y1) / 2, 'black', 110, RED, ks * 0.9)
        frame_rect(c, W / 2 - 200, (y0 + y1) / 2 - 80, W / 2 + 200, (y0 + y1) / 2 + 80, RED, 6, ks * 0.9)
    text(c, '伍德拉夫：主任“命令”我别发', W / 2, 1110, 'bold', 40, WHITE, smooth(remap(t, 1.2, 1.7)))
    text(c, '主任：只是“建议”', W / 2, 1170, 'bold', 40, GREY, smooth(remap(t, 1.8, 2.3)))
    return c, e


def glow_mirror(t):
    """measuring device heating up and glowing: measured = laser + device glow."""
    c = bg_reality('grid'); e = np.zeros_like(c)
    # mirror plate
    k = smooth(remap(t, 0, 0.5))
    heat = smooth(remap(t, 1.0, 2.5))
    plate = [(W / 2 - 260, 640), (W / 2 + 260, 600), (W / 2 + 260, 700), (W / 2 - 260, 740)]
    col = hexc('9aa6b4') * (1 - heat) + hexc('ff9a50') * heat
    fill_poly(c, plate, col * 0.8, k)
    draw_polyline(c, plate, GREY, 2, k, closed=True)
    if heat > 0:
        fill_poly(e, plate, hexc('ff7a30') * heat * 0.8, 1.0, add=True)
    text(c, '测量设备', W / 2, 520, 'bold', 40, WHITE, k)
    # bar chart: measured brightness = laser + glow (unknown split)
    kb = smooth(remap(t, 2.4, 3.2))
    bx, by = W / 2 - 60, 1180
    rect(c, bx, by - 300 * kb, bx + 120, by, BLUE, 0.9)
    rect(c, bx, by - 300 * kb, bx + 120, by - 300 * kb + 120 * kb, hexc('ff9a50'), 0.9 * smooth(remap(t, 3.4, 4.0)))
    text(c, '测到的亮度', W / 2, by + 50, 'bold', 34, GREY, kb)
    text(c, '有多少是激光？', bx + 300, by - 240, 'black', 40, AMBER, smooth(remap(t, 3.6, 4.2)))
    return c, e


def two_versions(t, title, left, right, lcol=GREY, rcol=WHITE, y=700):
    """two narratives side by side, with source tags."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, title, W / 2, 360, 'bold', 42, WHITE, smooth(remap(t, 0, 0.5)))
    for i, (col, (head, body, src)) in enumerate(((lcol, left), (rcol, right))):
        a = smooth(remap(t, 0.4 + 0.9 * i, 1.0 + 0.9 * i))
        y0 = y - 220 + i * 420
        card(c, 90, y0, W - 90, y0 + 360, a)
        text(c, head, 130, y0 + 60, 'bold', 34, GREY, a, anchor='lc')
        for j, ln in enumerate(body.split('\n')):
            text(c, ln, 130, y0 + 150 + j * 70, 'black', 50, col, a, anchor='lc')
        text(c, src, W - 130, y0 + 320, 'medium', 26, DIM * 1.5, a, anchor='rc')
    return c, e


# ------------------------------------------------------------------ 05 HOE extras
def target_heat(t):
    """target flown side-on + heated to 100F -> IR signature about doubled (GAO 1994)."""
    c = bg_reality('grid'); e = np.zeros_like(c)
    k = smooth(remap(t, 0, 0.5))
    rot = smooth(remap(t, 0.6, 1.6)) * math.pi / 2
    cx, cy = 360, 700
    # re-entry vehicle cone, rotates from nose-on to side-on
    L, R = 230, 70
    cone = np.array([[-L / 2, -R], [L / 2, -14], [L / 2, 14], [-L / 2, R]])
    Rm = np.array([[math.cos(rot - math.pi / 2), -math.sin(rot - math.pi / 2)], [math.sin(rot - math.pi / 2), math.cos(rot - math.pi / 2)]])
    pts = cone @ Rm.T + [cx, cy]
    heat = smooth(remap(t, 1.8, 3.2))
    col = hexc('7a7f88') * (1 - heat) + hexc('ff7040') * heat
    fill_poly(c, pts, col * 0.85, k)
    draw_polyline(c, pts, GREY, 2, k, closed=True)
    if heat > 0:
        fill_poly(e, pts, hexc('ff5020') * heat * 0.5, 1.0, add=True)
    text(c, '侧过身来飞', cx, 420, 'bold', 40, WHITE, smooth(remap(t, 0.8, 1.3)))
    # thermometer
    tx, ty0, ty1 = 700, 520, 900
    rect(c, tx - 14, ty0, tx + 14, ty1, hexc('1a222c'), k)
    frame_rect(c, tx - 14, ty0, tx + 14, ty1, GREY, 2, k)
    lvl = ty1 - (ty1 - ty0) * (0.45 + 0.4 * heat)
    rect(c, tx - 10, lvl, tx + 10, ty1, RED, k)
    ring(c, tx, ty1 + 26, 30, RED, 6, k, add=False)
    text(c, f'{int(75 + 25 * heat)}°F', tx + 120, lvl, 'black', 44, RED if heat > 0.5 else GREY, k)
    text(c, '加热到 100°F', tx, 420, 'bold', 40, WHITE, smooth(remap(t, 2.0, 2.5)))
    # IR bars
    kb = smooth(remap(t, 3.2, 4.0))
    rect(c, 260, 1240 - 120, 400, 1240, GREY, kb)
    rect(c, 560, 1240 - 120 - 132 * kb, 700, 1240, RED, kb)
    text(c, '原计划', 330, 1290, 'bold', 32, GREY, kb)
    text(c, '约 2.1 倍', 630, 1290, 'black', 36, RED, kb)
    text(c, '红外信号', W / 2, 1060 - 60, 'medium', 30, GREY, kb)
    return c, e


# ------------------------------------------------------------------ 06 physics
def orders(t):
    c = bg_reality('grid'); e = np.zeros_like(c)
    text(c, '1987 年 4 月 · 美国物理学会', W / 2, 330, 'bold', 40, WHITE, smooth(remap(t, 0, 0.5)))
    vals = ['×1', '×10', '×100', '×1000']
    for i, v in enumerate(vals):
        a = smooth(remap(t, 0.5 + 0.5 * i, 1.0 + 0.5 * i))
        h = [40, 120, 320, 620][i]
        x = 190 + i * 210
        rect(c, x, 1080 - h * a, x + 130, 1080, BLUE * (0.5 + 0.15 * i), 0.95)
        text(c, v, x + 65, 1080 - h * a - 40, 'black', 40, WHITE, a)
    text(c, '“几个数量级”：一个数量级 = 十倍', W / 2, 1160, 'black', 44, WHITE, smooth(remap(t, 2.4, 3.0)))
    kk = smooth(remap(t, 4.0, 4.6))
    if kk > 0:
        rect(c, 0, 0, W, H, (0, 0, 0), 0.55 * kk)
        text(c, '十年以上的密集研究', W / 2, 600, 'black', 70, AMBER, kk)
        text(c, '才能判断它到底有没有用', W / 2, 700, 'black', 56, WHITE, kk)
    return c, e


def pebbles(t):
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    cx, cy, R = W / 2, 760, 230
    m = np.zeros((H, W), np.float32)
    cv2.circle(m, (int(cx), int(cy)), R, 1.0, -1, cv2.LINE_AA)
    c[...] = c * (1 - m[..., None]) + hexc('0a1626') * m[..., None]
    ring(e, cx, cy, R, (0.3, 0.55, 1.0), 4, 0.6)
    rng = np.random.default_rng(6)
    n = int(600 * smooth(remap(t, 0.3, 2.0)))
    for i in range(n):
        inc = rng.uniform(0, math.pi)
        ph = rng.uniform(0, 2 * math.pi) + t * 0.25
        rr = R * rng.uniform(1.15, 1.6)
        x = cx + rr * math.cos(ph)
        y = cy + rr * math.sin(ph) * math.cos(inc)
        splat(e, x, y, 1.2, (0.7, 0.85, 1.0), 0.7)
    text(c, '“智能卵石”', W / 2, 330, 'black', 56, WHITE, smooth(remap(t, 0, 0.5)))
    text(c, '成千上万枚小型拦截弹，靠直接撞击', W / 2, 400, 'medium', 34, GREY, smooth(remap(t, 0.3, 0.8)))
    k2 = smooth(remap(t, 3.0, 3.5))
    text(c, '1993 年叫停', W / 2, 1120, 'black', 54, RED, k2)
    text(c, '花费三百多亿美元 · 部署：0', W / 2, 1200, 'black', 44, WHITE, smooth(remap(t, 4.0, 4.5)))
    return c, e


# ------------------------------------------------------------------ 07 Reykjavik
def house(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    # night sky gradient + sea
    rect(c, 0, 1150, W, H, hexc('05080c'), 1.0)
    draw_polyline(c, [(0, 1150), (W, 1150)], hexc('31404f'), 2, 1.0)
    k = smooth(remap(t, 0, 1.0))
    hofdi(c, W / 2, 1150, 0.95, alpha=k, lit=0.9)
    text(c, '1986 年 10 月 11–12 日', W / 2, 330, 'bold', 40, WHITE, smooth(remap(t, 0.3, 0.8)))
    text(c, '雷克雅未克 · 霍夫迪楼', W / 2, 395, 'medium', 34, GREY, smooth(remap(t, 0.5, 1.0)))
    return c, e


def table_cards(t):
    """the Soviet package as cards on a table (top view)."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    rect(c, 150, 380, W - 150, 1300, hexc('241c16'), 1.0)
    frame_rect(c, 150, 380, W - 150, 1300, hexc('4a3a2c'), 3, 1.0)
    items = [('十年', '不退出反导条约', WHITE), ('实验室', '太空部件只能在这里研究测试', AMBER),
             ('前五年', '战略进攻武器 −50%', WHITE), ('后五年', '剩下的全部削减', WHITE), ('1996', '完全消除', AMBER)]
    for i, (a_, b_, col) in enumerate(items):
        a = smooth(remap(t, 0.3 + 0.7 * i, 0.8 + 0.7 * i))
        y = 470 + i * 160
        card(c, 200, y - 60, W - 200, y + 60, a, border=hexc('8a7a66'), fill=hexc('e9e4d8') * 0.92)
        text(c, a_, 250, y, 'black', 46, hexc('2a2a2a') if col is WHITE else hexc('b5651d'), a, anchor='lc')
        text(c, b_, W - 240, y, 'bold', 34, hexc('3a3a3a'), a, anchor='rc')
    text(c, '戈尔巴乔夫的方案', W / 2, 330, 'black', 44, AMBER, smooth(remap(t, 0, 0.4)))
    tag(c, '据美苏双方会谈记录', W / 2, 1340, smooth(remap(t, 0, 0.4)), anchor='center')
    return c, e


def quote_card(t, head, body, src, col=WHITE, y=640):
    c = bg_reality('plain'); e = np.zeros_like(c)
    a = smooth(remap(t, 0, 0.6))
    text(c, head, W / 2, y - 260, 'bold', 38, GREY, a)
    lines = body.split('\n')
    for i, ln in enumerate(lines):
        text(c, ln, W / 2, y - 120 + i * 92, 'black', 60, col, smooth(remap(t, 0.3 + 0.4 * i, 0.9 + 0.4 * i)))
    tag(c, src, W / 2, y - 120 + len(lines) * 92 + 40, smooth(remap(t, 0.8, 1.3)), color=GREY, anchor='center')
    return c, e


def party(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    hofdi(c, W / 2, 1150, 0.6, alpha=0.6, lit=1.0)
    rect(c, 0, 1150, W, H, hexc('05080c'), 1.0)
    k = smooth(remap(t, 0.3, 1.0))
    for side, col in ((-1, BLUE), (1, AMBER)):
        draw_missile(c, W / 2 + side * 150, 820, 260, col, k)
    kd = smooth(remap(t, 2.0, 3.0))
    if kd > 0:
        rng = np.random.default_rng(1)
        for i in range(120):
            x = rng.uniform(100, W - 100); y = rng.uniform(380, 1000)
            splat(e, x, y + 40 * kd, 2.2, [(1, .8, .4), (.6, .8, 1), (1, 1, 1)][i % 3], 0.9 * kd)
    text(c, '十年后：各自带着最后一枚导弹', W / 2, 360, 'black', 46, WHITE, smooth(remap(t, 0, 0.5)))
    text(c, '当场销毁，为全世界开一个盛大的派对', W / 2, 430, 'bold', 38, GREY, smooth(remap(t, 1.5, 2.0)))
    tag(c, '据美苏双方会谈记录', W / 2, 1220, k, anchor='center')
    return c, e


def lab_quotes(t):
    """'实验室' already split; then the 'fool' line and 'one word / principle'."""
    c = bg_reality('plain'); e = np.zeros_like(c)
    a1 = smooth(remap(t, 0, 0.6))
    text(c, '“我会被叫作傻瓜，', W / 2, 470, 'black', 62, WHITE, a1)
    text(c, '而不是领导人”', W / 2, 560, 'black', 62, WHITE, a1)
    tag(c, '戈尔巴乔夫 · 美苏双方记录都有', W / 2, 640, a1, anchor='center')
    a2 = smooth(remap(t, 2.0, 2.6))
    card(c, 110, 760, W - 110, 900, a2)
    text(c, '里根：这只是一个词的问题', W / 2, 830, 'black', 48, BLUE, a2)
    a3 = smooth(remap(t, 3.2, 3.8))
    card(c, 110, 930, W - 110, 1070, a3)
    text(c, '戈尔巴乔夫：这是原则问题', W / 2, 1000, 'black', 48, AMBER, a3)
    return c, e


def memoir_vs_record(t):
    return two_versions(t, '同一时刻，两种记载',
                        ('苏方会谈记录', '“那就到此为止，\n忘了雷克雅未克吧”', '美国国家安全档案馆公布'),
                        ('舒尔茨回忆录（1993）', '“要么实验室，\n要么再见”', 'Turmoil and Triumph'))


def memoir_lines(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, '据舒尔茨回忆', W / 2, 340, 'bold', 40, GREY, smooth(remap(t, 0, 0.5)))
    a1 = smooth(remap(t, 0.3, 0.9))
    card(c, 180, 430, W - 180, 690, a1, fill=hexc('e9e4d8') * 0.9, border=hexc('8a7a66'))
    text(c, '纸条：“我错了吗？”', W / 2, 515, 'black', 52, hexc('202020'), a1)
    text(c, '“没有，你是对的。”', W / 2, 615, 'bold', 44, hexc('404040'), smooth(remap(t, 1.6, 2.1)))
    a2 = smooth(remap(t, 3.4, 4.0))
    text(c, '“我不知道我还能做什么。”', W / 2, 820, 'black', 50, AMBER, a2)
    text(c, '“你本可以说‘好’。”', W / 2, 910, 'black', 50, BLUE, smooth(remap(t, 4.6, 5.2)))
    a3 = smooth(remap(t, 6.0, 6.6))
    text(c, '双方的会谈记录里都没有这几句', W / 2, 1060, 'bold', 38, GREY, a3)
    return c, e


def two_views(t):
    return two_versions(t, '苏联为什么让了这么大的步？',
                        ('舒尔茨（回忆录）', '星球大战推动了让步，\n苏联怕美国技术更先进', 'Shultz, Turmoil and Triumph'),
                        ('波德维格（苏联档案）', '从没拿战略核力量去换；\n它更像绊脚石，不是筹码', 'Podvig, Science & Global Security, 2017'),
                        lcol=BLUE, rcol=AMBER)


# ------------------------------------------------------------------ 08 Soviet sky
def soviet_station(t, cam_t=0.0):
    """imagined Soviet laser station (amber) in orbit over the Arctic."""
    import earth as E, models3d as M3
    cam = E.orbit_cam(64, 30, 0.25, 82, 25, look_alt=0.1, fov=55)
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    E.render_stars(c, cam, amount=1.3)
    E.render_earth(c, e, cam, sun=E.ll2xyz(-5, -60), atm_amt=1.2, light_amt=1.0)
    pos = cam.pos + cam.f * 0.03 + cam.r * 0.002 + cam.u * 0.006
    mesh = M3.battle_station(1.0, smooth(remap(t, 0.2, 2.5)), charge=0.3)
    d = cam.r * math.cos(0.4 + 0.15 * t) + cam.f * 0.3 + cam.u * 0.2
    R = M3.look_rot(d / np.linalg.norm(d), up=pos / np.linalg.norm(pos))
    M3.render_mesh(c, e, mesh, cam, M=R, t=pos, scale=0.0014, light=cam.r * 0.5 + cam.u * 0.6 - cam.f * 0.5,
                   ambient=0.18, rim_col=(1.0, 0.7, 0.35), tint=(1.15, 0.82, 0.5))
    return c, e


def energia_launch(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    rect(c, 0, 1250, W, H, hexc('08090b'), 1.0)
    rise = ease_in(remap(t, 1.0, 6.0), 2) * 900
    cx, base = W / 2, 1230 - rise
    # silhouette (side view): core + boosters + black payload
    def r_(x0, y0, x1, y1, col):
        rect(c, x0, y0, x1, y1, col, 1.0)
    r_(cx - 34, base - 520, cx + 34, base, hexc('d8ccb0'))
    r_(cx - 66, base - 330, cx - 36, base, hexc('cfc8b8'))
    r_(cx + 36, base - 330, cx + 66, base, hexc('cfc8b8'))
    r_(cx + 70, base - 470, cx + 112, base - 130, hexc('121417'))
    fill_poly(c, [(cx - 34, base - 520), (cx, base - 580), (cx + 34, base - 520)], hexc('d8ccb0'))
    fill_poly(c, [(cx + 70, base - 470), (cx + 91, base - 520), (cx + 112, base - 470)], hexc('121417'))
    ign = smooth(remap(t, 0.2, 1.0))
    if ign > 0:
        fx.tapered_beam(e, (cx, base + 10), (cx, base + 220 + 160 * ign), (1.0, 0.6, 0.28), 70, 8, 0.55 * ign)
        splat(e, cx, base + 30, 38, (1, .9, .7), 0.9 * ign)
        rng = np.random.default_rng(int(t * 30))
        for _ in range(30):
            splat(c, cx + rng.normal(0, 150), min(1250, base + 260 + rng.normal(0, 90)), rng.uniform(25, 70), (0.42, 0.40, 0.38), 0.10 * ign)
    text(c, '1987 年 5 月 15 日', W / 2, 330, 'black', 50, WHITE, smooth(remap(t, 0, 0.5)))
    text(c, '“能源号”首次发射', W / 2, 400, 'bold', 38, GREY, smooth(remap(t, 0.2, 0.7)))
    text(c, '黑色的“极地”号挂在箭体一侧', W / 2, 470, 'medium', 32, GREY, smooth(remap(t, 1.0, 1.5)))
    return c, e


def polyus_specs(t):
    c = bg_reality('grid'); e = np.zeros_like(c)
    k = smooth(remap(t, 0, 0.6))
    polyus_craft(c, W / 2, 620, 0.0, L=640, Wd=96, alpha=k)
    text(c, '“极地”号 · 演示样机', W / 2, 400, 'black', 50, WHITE, k)
    text(c, '约 37 米 · 约 80 吨', W / 2, 800, 'bold', 40, GREY, smooth(remap(t, 0.6, 1.1)))
    text(c, '身上的名字：“极地”“和平-2”', W / 2, 880, 'bold', 40, GREY, smooth(remap(t, 1.4, 1.9)))
    text(c, '没有装作战激光器', W / 2, 990, 'black', 56, AMBER, smooth(remap(t, 2.6, 3.2)))
    tag(c, 'Lantratov 2005；Day & Kennedy 2010', W / 2, 1060, smooth(remap(t, 2.6, 3.2)), anchor='center')
    return c, e


def restrictions(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, '发射前被取消的项目', W / 2, 360, 'black', 50, WHITE, smooth(remap(t, 0, 0.5)))
    items = ['释放模拟靶标', '雷达与瞄准测试', '太空喷放气体']
    for i, s in enumerate(items):
        a = smooth(remap(t, 0.5 + 0.6 * i, 1.0 + 0.6 * i))
        y = 560 + i * 150
        card(c, 180, y - 55, W - 180, y + 55, a)
        text(c, s, W / 2, y, 'bold', 44, WHITE, a)
        ks = smooth(remap(t, 1.0 + 0.6 * i, 1.4 + 0.6 * i))
        if ks > 0:
            draw_polyline(c, [(200, y), (200 + (W - 400) * ks, y)], RED, 6, 1.0)
    text(c, '高层的政治压力', W / 2, 1060, 'bold', 38, GREY, smooth(remap(t, 2.6, 3.0)))
    tag(c, '各方说法不一：政治局成员推动 / 国家委员会决定', W / 2, 1120, smooth(remap(t, 2.6, 3.0)), anchor='center')
    return c, e


def ocean_fall(t):
    import earth as E
    cam = E.orbit_cam(36, -150, 0.035, 46, -150, look_alt=0.0, fov=55)
    c = new_canvas(hexc('020308')); e = np.zeros_like(c)
    E.render_stars(c, cam, amount=1.0)
    E.render_earth(c, e, cam, sun=E.ll2xyz(20, -110), atm_amt=1.4, day_amt=0.35, light_amt=0.0, coast_amt=0.0)
    k = remap(t, 0.3, 4.0)
    pts = [(760 - 520 * u, 300 + 900 * u ** 1.5) for u in np.linspace(0, k, 40)]
    if len(pts) > 1 and k > 0:
        fx.plume(e, pts, (1.0, 0.55, 0.25), head=1.0 if k < 1 else 0.0, width=5)
    text(c, '太平洋', W / 2, 1300, 'black', 52, WHITE, smooth(remap(t, 3.0, 3.6)))
    return c, e


# ------------------------------------------------------------------ 09 myth
def inf_card(t):
    c = bg_reality('grid'); e = np.zeros_like(c)
    a = smooth(remap(t, 0, 0.5))
    text(c, '1987 年 2 月', W / 2, 330, 'bold', 40, GREY, a)
    text(c, '中导谈判与星球大战脱钩', W / 2, 400, 'black', 46, WHITE, a)
    b = smooth(remap(t, 1.5, 2.0))
    text(c, '1987.12.8', W / 2, 600, 'black', 110, WHITE, b)
    text(c, '中导条约', W / 2, 720, 'black', 64, BLUE, b)
    text(c, '销毁射程 500–5500 公里的全部陆基导弹', W / 2, 820, 'bold', 38, GREY, smooth(remap(t, 2.2, 2.7)))
    text(c, '条约生效后共销毁 2692 枚', W / 2, 890, 'bold', 38, GREY, smooth(remap(t, 2.6, 3.1)))
    return c, e


def soviet_projects(t):
    c = bg_reality('grid'); e = np.zeros_like(c)
    text(c, '苏联的“反制计划”', W / 2, 330, 'black', 50, AMBER, smooth(remap(t, 0, 0.5)))
    rng = np.random.default_rng(9)
    labels = ['1985 年前已有'] * 9 + ['纸面'] * 7 + ['新项目'] * 4
    rng.shuffle(labels)
    for i, lab in enumerate(labels):
        a = smooth(remap(t, 0.3 + 0.06 * i, 0.6 + 0.06 * i))
        r, cidx = divmod(i, 4)
        x0 = 120 + cidx * 220; y0 = 420 + r * 130
        hi = lab == '新项目' and t > 3.0
        card(c, x0, y0, x0 + 190, y0 + 105, a, border=AMBER if hi else GREY)
        text(c, lab, x0 + 95, y0 + 52, 'bold', 26, AMBER if hi else GREY, a * (0.5 if (t > 3.0 and not hi) else 1.0))
    text(c, '真正动手的：便宜的反卫星武器、让导弹更难拦截的改进', W / 2, 1120, 'bold', 32, WHITE, smooth(remap(t, 3.2, 3.8)))
    tag(c, '示意 · 据 Podvig 2017（苏联国防工业档案）', W / 2, 1180, smooth(remap(t, 3.2, 3.8)), anchor='center')
    return c, e


def verdict(t):
    c = bg_reality('plain'); e = np.zeros_like(c)
    text(c, '“星球大战拖垮了苏联”？', W / 2, 360, 'black', 54, WHITE, smooth(remap(t, 0, 0.5)))
    for i, (h1, h2, col) in enumerate((('影响了谈判', '有依据 · 方向有争议', BLUE), ('拖垮了经济', '证据不支持', AMBER))):
        a = smooth(remap(t, 0.6 + 0.8 * i, 1.2 + 0.8 * i))
        x0 = 90 + i * 460
        card(c, x0, 520, x0 + 440, 980, a, border=col)
        text(c, h1, x0 + 220, 640, 'black', 52, col, a)
        text(c, h2, x0 + 220, 780, 'bold', 36, WHITE, a)
    return c, e
