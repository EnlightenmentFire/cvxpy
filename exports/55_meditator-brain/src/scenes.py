"""Scenes for episode 55. Each scene: fn(c, t, d, L) ; t local seconds, d duration, L local line start times."""
import math, functools
import numpy as np, skia
from scipy.ndimage import gaussian_filter, zoom as ndzoom
from gfx import *

INK, PAPER, RED, GOLD = '#25211c', '#efe7d7', '#a8322d', '#b8893b'
CYAN, TEAL, LAB_TXT = '#5fe3ff', '#38c6b8', '#d9f4ff'
VIS_TOP, VIS_BOT = 330, 1440
CX = W / 2

# ---------------- backgrounds ----------------
@functools.lru_cache(None)
def paper_img():
    r = np.random.default_rng(7)
    base = np.array([239, 231, 215], np.float32)
    n1 = gaussian_filter(r.standard_normal((H // 4, W // 4)), 18); n1 = ndzoom(n1, 4, order=1)[:H, :W]
    n1 = n1 / (np.abs(n1).max() + 1e-6)
    fine = r.standard_normal((H, W)) * 3.0
    img = base[None, None, :] + (n1 * 9 + fine)[:, :, None] * np.array([1, 1, 0.9])
    # ink-wash mountains at bottom & top mist
    y = np.arange(H)[:, None]; x = np.arange(W)[None, :]
    for k, (base_y, amp, dark, sig) in enumerate([(1500, 120, 26, 6), (1600, 160, 42, 3)]):
        ridge = base_y - amp * (0.5 + 0.5 * np.sin(x / 170.0 + k * 2) * np.cos(x / 97.0 + k)) - 40 * gaussian_filter(r.standard_normal(W), 25)[None, :] * 8
        m = (y > ridge).astype(np.float32)
        m *= np.clip(1 - (y - ridge) / 420.0, 0.15, 1)
        m = gaussian_filter(m, sig * 3)
        img -= (m * dark)[:, :, None]
    v = (((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
    img *= (1 - 0.18 * v)[:, :, None]
    out = np.concatenate([np.clip(img, 0, 255), np.full((H, W, 1), 255.0)], 2).astype(np.uint8)
    return img_from_rgba(out)

@functools.lru_cache(None)
def lab_img():
    y = np.arange(H)[:, None].astype(np.float32); x = np.arange(W)[None, :].astype(np.float32)
    top = np.array([7, 11, 20.]); bot = np.array([13, 24, 40.])
    k = (y / H)[:, :, None]
    img = top * (1 - k) + bot * k + np.zeros((H, W, 3))
    v = (((x - W / 2) / (W * 0.6)) ** 2 + ((y - H * 0.45) / (H * 0.6)) ** 2)
    img *= np.clip(1.15 - 0.55 * v, 0.3, 1.2)[:, :, None]
    r = np.random.default_rng(3); img += r.standard_normal((H, W, 1)) * 1.6
    out = np.concatenate([np.clip(img, 0, 255), np.full((H, W, 1), 255.0)], 2).astype(np.uint8)
    return img_from_rgba(out)

def bg_paper(c, t):
    c.drawImage(paper_img(), 0, 0)
    # drifting mist
    for i in range(3):
        xx = (t * (8 + 4 * i) + i * 400) % (W + 600) - 300
        rglow(c, xx + 50, 1240 + i * 70, 380, '#ffffff', 0.10, sy=0.25)

def bg_lab(c, t):
    c.drawImage(lab_img(), 0, 0)
    g = paint('#1f3a55', 0.35, stroke=1)
    off = (t * 6) % 60
    for i in range(-1, 34):
        c.drawLine(0, i * 60 + off, W, i * 60 + off, g)
    for j in range(0, 19):
        c.drawLine(j * 60, 0, j * 60, H, g)
    r = np.random.default_rng(11)
    for k in range(40):
        x0, y0, sp = r.uniform(0, W), r.uniform(0, H), r.uniform(4, 14)
        yy = (y0 - t * sp) % H
        c.drawCircle(x0 + 10 * math.sin(t * 0.3 + k), yy, r.uniform(1, 2.6), paint(CYAN, 0.25 + 0.2 * math.sin(t + k)))

# ---------------- EEG primitives ----------------
ELECS = [(0, -0.05)] + [(0.33 * math.cos(a), 0.33 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)] + \
        [(0.64 * math.cos(a), 0.64 * math.sin(a)) for a in np.linspace(math.pi / 12, 2 * math.pi + math.pi / 12, 14, endpoint=False)] + \
        [(0.86 * math.cos(a), 0.86 * math.sin(a)) for a in np.linspace(0.2, 2 * math.pi + 0.2, 10, endpoint=False)]

def head_top(c, x, y, R, t, lit=1.0, a=1.0, sync=0.0):
    # nose & ears
    p = skia.Path(); p.moveTo(x - R * 0.12, y - R * 0.98); p.lineTo(x, y - R * 1.14); p.lineTo(x + R * 0.12, y - R * 0.98)
    c.drawPath(p, paint(LAB_TXT, a * 0.7, stroke=4))
    for sx in (-1, 1):
        c.drawOval(skia.Rect.MakeXYWH(x + sx * R - 14 - (8 if sx < 0 else -8), y - 40, 28, 80), paint(LAB_TXT, a * 0.6, stroke=4))
    c.drawCircle(x, y, R, paint('#0c1a2b', a * 0.9))
    c.drawCircle(x, y, R, paint(LAB_TXT, a * 0.85, stroke=4))
    n = len(ELECS)
    # synchrony links
    if sync > 0:
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 1.2)
        for i in range(n):
            for j in range(i + 1, n):
                if (i * 7 + j * 3) % 5 == 0:
                    (ax, ay), (bx, by) = ELECS[i], ELECS[j]
                    c.drawLine(x + ax * R, y + ay * R, x + bx * R, y + by * R, paint(CYAN, a * sync * (0.12 + 0.25 * pulse), stroke=2))
    for i, (ex, ey) in enumerate(ELECS):
        on = clamp(lit * n - i)
        px, py = x + ex * R, y + ey * R
        c.drawCircle(px, py, 13, paint('#22384f', a))
        if on > 0:
            fl = 0.75 + 0.25 * math.sin(t * 9 + i * 1.7) if sync <= 0 else 0.8 + 0.2 * math.sin(t * 2 * math.pi * 1.2)
            glow(c, px, py, 10, CYAN, a * on * fl)

def trace(c, x, y, w, h, t, amp, sync, seed, col=CYAN, a=1.0, lw=3):
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28, 6); fr = r.uniform(0.7, 1.4, 6)
    xs = np.linspace(0, 1, 260)
    tt = xs * 2.2 + t * 0.9
    noise = sum(np.sin(2 * math.pi * (fr[k] * (k + 2) * 3) * tt + ph[k]) / (k + 1) for k in range(6)) * 0.35
    gam = np.sin(2 * math.pi * 14 * tt) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.9 * tt))
    yv = (1 - sync) * noise * 0.6 + sync * gam
    yv = yv * amp
    p = skia.Path(); p.moveTo(x, y - yv[0] * h)
    for i in range(1, len(xs)): p.lineTo(x + xs[i] * w, y - yv[i] * h)
    c.drawPath(p, paint(col, a * 0.18, stroke=lw * 3.5))
    c.drawPath(p, paint(col, a, stroke=lw))

def scope(c, x, y, w, h, t, sync, amp, a=1.0, label=None, rows=6, col=CYAN):
    rrect(c, x, y, w, h, 18, paint('#06121c', a * 0.85))
    rrect(c, x, y, w, h, 18, paint('#2d5a78', a * 0.9, stroke=2))
    for i in range(rows):
        yy = y + h * (i + 0.5) / rows
        c.drawLine(x + 20, yy, x + w - 20, yy, paint('#1d3b52', a * 0.6, stroke=1))
        trace(c, x + 24, yy, w - 48, h / rows * 0.42, t, amp, sync, seed=i + 1, col=col, a=a, lw=2.5)
    if label:
        text(c, label, x + 6, y - 16, 30, 'sans', LAB_TXT, a * 0.85, align='left')

def L_(L, k): return L[k] if k < len(L) else 1e9

# ---------------- scenes ----------------
def s_hook_eeg(c, t, d, L):
    bg_lab(c, t)
    lit = clamp(0.6 + t / 1.4)
    sync = smooth((t - 1.3) / 1.0)
    head_top(c, CX, 690, 250, t, lit=lit, sync=sync * 0.7)
    scope(c, 70, 1010, W - 140, 400, t, sync, lerp(0.55, 1.0, sync), label='EEG · 示意')
    if sync > 0.2:
        text(c, '高振幅 · 高同步', W - 76, 994, 30, 'sans_b', CYAN, sync, align='right')

def s_hook_gamma(c, t, d, L):
    bg_lab(c, t + 8)
    head_top(c, CX, 640, 230, t + 8, lit=1, sync=1)
    scope(c, 70, 960, W - 140, 330, t + 8, 1, 1.0, rows=4)
    text(c, 'γ 伽马波', CX, 1370, 64, 'serif_b', CYAN, ap(t, 0.2))
    text(c, '每秒振荡约 25–42 次（本研究所测频段）', CX, 1425, 32, 'sans', LAB_TXT, ap(t, 0.6) * 0.85)
    if t > L_(L, 1) - 0.2:
        k = ap(t, L_(L, 1))
        chip(c, '修行时间越长 → 静息时比值越高', CX, 380, 34, '#06121c', CYAN, k)

def cortex_field(bump, res=(300, 300)):
    yy, xx = np.mgrid[0:res[0], 0:res[1]] / np.array(res[0])
    r = np.random.default_rng(5)
    f = gaussian_filter(r.standard_normal(res), 22) * 30
    f += 0.6 * np.sin(xx * 9) * np.cos(yy * 7)
    for (bx, by, s, amp) in [(0.30, 0.34, 0.09, 1.0), (0.68, 0.60, 0.07, 0.9)]:
        f += bump * amp * 2.6 * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * s * s))
    return f

def cortex_map(c, x, y, size, t, bump, a=1.0, theme='lab'):
    f = cortex_field(bump)
    k = 5.0
    band = np.abs(((f * k) % 1.0) - 0.5)
    line = np.clip((0.5 - band - 0.40) / 0.06, 0, 1)
    hi = np.clip((f - 0.8) / 2.0, 0, 1)
    yy, xx = np.mgrid[0:300, 0:300] / 300.0
    mask = np.clip((0.48 - np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)) / 0.03, 0, 1)
    if theme == 'lab':
        rgb = np.stack([95 + 160 * hi, 227 - 40 * hi, 255 - 120 * hi], -1)
    else:
        rgb = np.stack([37 + 140 * hi, 33 + 20 * hi, 28 + 10 * hi], -1)
    alpha = (line * (0.55 + 0.45 * hi) + hi * 0.18) * mask * a
    img = np.concatenate([rgb, (alpha * 255)[..., None]], -1).astype(np.uint8)
    draw_img(c, img_from_rgba(img), x, y, size, size)

def s_hook_cortex(c, t, d, L):
    bg_lab(c, t + 20)
    cortex_map(c, CX - 420, 420, 840, t, smooth(t / 2.5))
    k = smooth((t - 1.6) / 0.8)
    for (bx, by, lab) in [(0.30, 0.34, '更厚'), (0.68, 0.60, '更厚')]:
        glow(c, CX - 420 + bx * 840, 420 + by * 840, 14, '#ffb35c', k)
        text(c, lab, CX - 420 + bx * 840, 420 + by * 840 - 40, 40, 'serif_b', '#ffd59a', k)
    chip(c, '核磁共振 · 皮层厚度 · 示意', CX, 1300, 32, '#06121c', CYAN, ap(t, 0.3))

def two_paths(c, t, L, k0, k1, col=INK, base_y=640, show_cross=False):
    # path A
    a1 = ap(t, k0, 0.8)
    text(c, '冥想', 240, base_y, 64, 'serif_k', col, a1)
    arrow(c, 340, base_y - 22, 690, base_y - 22, col, a1, w=12, prog=smooth((t - k0) / 1.0), ink=True)
    text(c, '大脑改变', 850, base_y, 64, 'serif_k', col, a1)
    text(c, '路径一 · 训练造成差异', CX, base_y + 70, 32, 'sans', col, a1 * 0.7)
    a2 = ap(t, k1, 0.8)
    yb = base_y + 260
    text(c, '本来不同的人', 270, yb, 56, 'serif_k', RED, a2)
    arrow(c, 460, yb - 20, 690, yb - 20, RED, a2, w=12, prog=smooth((t - k1) / 1.0), ink=True)
    text(c, '更愿意冥想', 850, yb, 56, 'serif_k', RED, a2)
    text(c, '路径二 · 自我选择', CX, yb + 70, 32, 'sans', RED, a2 * 0.8)
    return yb

def s_hook_paths(c, t, d, L):
    bg_paper(c, t)
    text(c, '是冥想改变了大脑，', CX, 470, 58, 'serif_b', INK, ap(t, 0))
    text(c, '还是不一样的人才去冥想？', CX, 550, 58, 'serif_b', INK, ap(t, 0.5))
    two_paths(c, t, L, 1.0, 2.2, base_y=800)

def s_hook_verdict(c, t, d, L):
    bg_paper(c, t)
    a = ap(t, 0.1)
    rrect(c, 110, 480, W - 220, 230, 20, paint('#ffffff', a * 0.35))
    text(c, '差异', 260, 620, 80, 'serif_k', INK, a)
    text(c, '被测到了', 650, 620, 80, 'serif_k', INK, a)
    seal(c, '实证', 945, 595, 40, ap(t, 0.8))
    b = ap(t, 1.6)
    rrect(c, 110, 760, W - 220, 230, 20, paint('#ffffff', b * 0.35))
    text(c, '因果', 260, 900, 80, 'serif_k', RED, b)
    text(c, '尚无定论', 650, 900, 80, 'serif_k', RED, b)
    k = ap(t, L_(L, 1))
    for i, (s, col) in enumerate([('哪里强', '#2f6b4f'), ('哪里弱', GOLD), ('哪里说不清', RED)]):
        chip(c, s, 250 + i * 290, 1100, 40, '#fff8ec', col, ap(t, L_(L, 1) + i * 0.6))

def s_title(c, t, d, L):
    bg_paper(c, t)
    a = ap(t, 0)
    text(c, '修行几万小时的人', CX, 690, 92, 'serif_k', INK, a, spacing=4)
    text(c, '大脑有什么不一样？', CX, 820, 92, 'serif_k', INK, ap(t, 0.3), spacing=4)
    c.drawLine(CX - 200, 900, CX + 200, 900, paint(RED, ap(t, 0.8) * 0.8, stroke=3))
    text(c, '科学与修行 可以相互印照', CX, 990, 44, 'serif', INK, ap(t, 1.0))
    text(c, '但印照，不是证明', CX, 1060, 44, 'serif_b', RED, ap(t, 2.0))
    seal(c, '印照', CX, 1210, 44, ap(t, 2.4))

def study_card(c, cite, journal, a, theme='lab', y=380):
    fg = LAB_TXT if theme == 'lab' else INK
    bgc = '#0a1a2a' if theme == 'lab' else '#ffffff'
    rrect(c, 70, y, W - 140, 150, 20, paint(bgc, a * (0.85 if theme == 'lab' else 0.45)))
    rrect(c, 70, y, W - 140, 150, 20, paint(CYAN if theme == 'lab' else INK, a * 0.6, stroke=2))
    text(c, cite, CX, y + 66, 42, 'serif_b', fg, a)
    text(c, journal, CX, y + 118, 30, 'sans', fg, a * 0.75)

def people_row(c, n, x0, y, cols, s, col, t, t0, gap=None, a=1.0):
    gap = gap or s * 1.05
    for i in range(n):
        k = ap(t, t0 + i * 0.07, 0.3)
        person(c, x0 + (i % cols) * gap, y + (i // cols) * s * 1.3 + (1 - k) * 20, s, col, a * k)

def s_lutz_intro(c, t, d, L):
    bg_lab(c, t + 30)
    study_card(c, 'Lutz 等，2004', '《美国国家科学院院刊》PNAS 101(46): 16369–16373', ap(t, 0))
    k1 = L_(L, 1)
    text(c, '长期修行的僧人', 290, 680, 44, 'serif_b', '#ffd59a', ap(t, k1))
    people_row(c, 8, 140, 800, 4, 90, '#ffd59a', t, k1)
    text(c, '8 人', 290, 1080, 72, 'serif_k', '#ffd59a', ap(t, k1 + 0.5))
    text(c, '约 1 万–5 万小时', 290, 1150, 34, 'sans', LAB_TXT, ap(t, k1 + 0.9))
    text(c, '跨 15–40 年', 290, 1200, 34, 'sans', LAB_TXT, ap(t, k1 + 1.1))
    k2 = L_(L, 2)
    text(c, '学生志愿者', 790, 680, 44, 'serif_b', CYAN, ap(t, k2))
    people_row(c, 10, 610, 800, 5, 80, CYAN, t, k2, gap=88)
    text(c, '10 人', 790, 1080, 72, 'serif_k', CYAN, ap(t, k2 + 0.5))
    text(c, '冥想训练 1 周', 790, 1150, 34, 'sans', LAB_TXT, ap(t, k2 + 0.9))
    c.drawLine(CX, 660, CX, 1220, paint('#2d5a78', ap(t, k2) * 0.8, stroke=2))

def meditator(c, x, y, s, col, a=1.0):
    c.drawCircle(x, y - s * 1.05, s * 0.2, paint(col, a))
    p = skia.Path(); p.moveTo(x, y - s * 0.85)
    p.cubicTo(x - s * 0.45, y - s * 0.7, x - s * 0.42, y - s * 0.1, x - s * 0.75, y + s * 0.15)
    p.cubicTo(x - s * 0.5, y + s * 0.32, x + s * 0.5, y + s * 0.32, x + s * 0.75, y + s * 0.15)
    p.cubicTo(x + s * 0.42, y - s * 0.1, x + s * 0.45, y - s * 0.7, x, y - s * 0.85); p.close()
    c.drawPath(p, paint(col, a))

def s_lutz_method(c, t, d, L):
    bg_paper(c, t + 5)
    for i in range(6):
        ph = ((t * 0.18 + i / 6) % 1.0)
        c.drawCircle(CX, 930, 120 + ph * 520, paint(GOLD, (1 - ph) * 0.45, stroke=3))
    rglow(c, CX, 930, 420, '#f7d9a0', 0.45)
    meditator(c, CX, 1010, 210, INK, 0.92)
    text(c, '无对象的慈悲', CX, 520, 84, 'serif_k', INK, ap(t, 0.2), spacing=6)
    text(c, '不针对某一个人 · 无条件地遍满一切', CX, 600, 36, 'serif', INK, ap(t, 1.2) * 0.85)
    text(c, '论文用语：unconditional loving-kindness and compassion', CX, 1340, 26, 'sans', INK, ap(t, 2.0) * 0.6)

def s_lutz_result(c, t, d, L):
    bg_lab(c, t + 40)
    scope(c, 70, 420, W - 140, 420, t, 1.0, 1.0, label='长期修行者 · 冥想中 · 示意', rows=5, col='#ffd59a')
    scope(c, 70, 900, W - 140, 290, t, 0.0, 0.35, label='对照组 · 冥想中 · 示意', rows=4)
    k = ap(t, L_(L, 1))
    rrect(c, 90, 1215, W - 180, 190, 16, paint('#0a1a2a', k * 0.9))
    text(c, '“就我们所知，是非病理状态下', CX, 1280, 36, 'serif_b', '#ffd59a', k)
    text(c, '文献报道过的最高水平”', CX, 1335, 36, 'serif_b', '#ffd59a', k)
    text(c, '—— Lutz 等，2004（意译）', CX, 1385, 26, 'sans', LAB_TXT, k * 0.7)

def scatter(c, x, y, w, h, t, t0, col, axcol, pts, xlabel, ylabel, a=1.0, r_label=None):
    c.drawLine(x, y + h, x + w, y + h, paint(axcol, a, stroke=3))
    c.drawLine(x, y, x, y + h, paint(axcol, a, stroke=3))
    text(c, xlabel, x + w / 2, y + h + 60, 32, 'sans', axcol, a)
    c.save(); c.translate(x - 30, y + h / 2); c.rotate(-90)
    text(c, ylabel, 0, 0, 32, 'sans', axcol, a); c.restore()
    for i, (px, py) in enumerate(pts):
        k = ap(t, t0 + i * 0.15, 0.3)
        glow(c, x + px * w, y + (1 - py) * h, 11, col, a * k)
    kk = ap(t, t0 + len(pts) * 0.15 + 0.2, 0.8)
    c.drawLine(x + 0.05 * w, y + 0.82 * h, x + lerp(0.05, 0.95, kk) * w, y + lerp(0.82, 0.18, kk) * h, paint(col, a * 0.7, stroke=4))
    if r_label: text(c, r_label, x + w - 10, y + 40, 34, 'sans_b', col, a * kk, align='right')

def s_lutz_trait(c, t, d, L):
    bg_lab(c, t + 50)
    text(c, '冥想开始前 · 静息基线', CX, 430, 46, 'serif_b', LAB_TXT, ap(t, 0))
    text(c, '伽马（25–42Hz）÷ 慢波（4–13Hz）', CX, 490, 34, 'sans', CYAN, ap(t, 0.4))
    pts = [(0.12, 0.25), (0.25, 0.32), (0.38, 0.30), (0.5, 0.52), (0.6, 0.48), (0.72, 0.66), (0.83, 0.62), (0.93, 0.85)]
    scatter(c, 190, 580, 760, 560, t, L_(L, 1), '#ffd59a', LAB_TXT, pts, '一生累计修行时长', '静息比值', r_label='8 人 · r ≈ 0.79')
    text(c, '示意 · 点位非原始数据', W - 70, 1290, 26, 'sans', LAB_TXT, ap(t, 1) * 0.6, align='right')
    k = ap(t, L_(L, 2))
    chip(c, '状态 → 特质？（研究者的推测）', CX, 1330, 36, '#06121c', '#ffd59a', k)

def s_gamma_meaning(c, t, d, L):
    bg_lab(c, t + 60)
    brain(c, 170, 470, 740, LAB_TXT, 0.9, fill=('#0c1a2b', 0.9))
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    nodes = [(0.25, 0.25), (0.55, 0.15), (0.8, 0.35), (0.45, 0.45), (0.7, 0.55)]
    for i, (a_, b_) in enumerate(nodes):
        for (c_, d_) in nodes[i + 1:]:
            c.drawLine(170 + a_ * 740, 470 + b_ * 740, 170 + c_ * 740, 470 + d_ * 740, paint(CYAN, 0.2 + 0.3 * pulse, stroke=2))
        glow(c, 170 + a_ * 740, 470 + b_ * 740, 12, CYAN, 0.9)
    chip(c, '注意力集中', 300, 400, 36, '#06121c', CYAN, ap(t, 0.5))
    chip(c, '感觉信息整合', 780, 400, 36, '#06121c', CYAN, ap(t, 1.2))
    k = ap(t, L_(L, 1))
    text(c, '伽马波 = 慈悲？', 330, 1150, 50, 'serif_b', LAB_TXT, k)
    text(c, '伽马波 = 觉悟？', 760, 1150, 50, 'serif_b', LAB_TXT, k)
    for xx in (330, 760):
        c.drawLine(xx - 170, 1133, xx + 170, 1133, paint('#ff6b5c', ap(t, L_(L, 1) + 1.2), stroke=6))
    text(c, '不能直接画等号', CX, 1260, 46, 'serif_k', '#ff8a7a', ap(t, L_(L, 1) + 1.6))

def caveat_list(c, t, L, items, title, theme='paper', y0=470, step=165):
    fg = INK if theme == 'paper' else LAB_TXT
    text(c, title, CX, y0 - 30, 60, 'serif_k', fg, ap(t, 0))
    for i, (k_idx, s1, s2) in enumerate(items):
        k = ap(t, L_(L, k_idx) if k_idx >= 0 else 0.3 + i * 0.4)
        y = y0 + 40 + i * step
        rrect(c, 90, y, W - 180, step - 25, 16, paint('#ffffff' if theme == 'paper' else '#0a1a2a', k * 0.5))
        c.drawCircle(150, y + (step - 25) / 2, 32, paint(RED, k))
        text(c, str(i + 1), 150, y + (step - 25) / 2 + 13, 38, 'sans_b', '#fff8ec', k)
        text(c, s1, 210, y + 62, 44, 'serif_b', fg, k, align='left')
        text(c, s2, 210, y + 110, 30, 'sans', fg, k * 0.75, align='left')

def s_lutz_caveat(c, t, d, L):
    bg_paper(c, t + 9)
    caveat_list(c, t, L, [(1, '小样本', '8 位修行者 对 10 名学生'), (2, '横断面比较', '只比一个时间点，没有追踪同一群人'),
                          (3, '年龄差距大', '平均 49 岁 对 21 岁'), (4, '作者自注', '这些特征是否由训练造成，有待证明')],
                '先放慢脚步', y0=470, step=190)

def s_emg(c, t, d, L):
    bg_lab(c, t + 70)
    # face profile with muscle zones
    fx, fy = 300, 720
    c.drawCircle(fx, fy, 200, paint('#0c1a2b', 0.95)); c.drawCircle(fx, fy, 200, paint(LAB_TXT, 0.8, stroke=4))
    k1 = ap(t, L_(L, 1))
    for (dx, dy, lab) in [(-60, -110, '皱眉'), (60, -10, '眼动'), (-20, 120, '咬牙')]:
        pul = 0.6 + 0.4 * math.sin(t * 7 + dx)
        glow(c, fx + dx, fy + dy, 22, '#ff6b5c', k1 * pul)
        text(c, lab, fx + dx + 36, fy + dy + 12, 34, 'sans_b', '#ff9b8e', k1, align='left')
    # spectrum
    x, y, w, h = 560, 560, 450, 360
    c.drawLine(x, y + h, x + w, y + h, paint(LAB_TXT, 0.8, stroke=3)); c.drawLine(x, y, x, y + h, paint(LAB_TXT, 0.8, stroke=3))
    xs = np.linspace(0, 1, 120)
    sp = 0.9 * np.exp(-xs * 4) + 0.08
    emg = np.clip((xs - 0.25) * 2, 0, 1) * 0.28 * k1
    pth = skia.Path(); pth.moveTo(x, y + h)
    for i, xv in enumerate(xs): pth.lineTo(x + xv * w, y + h - (sp[i] + emg[i]) * h * 0.9)
    pth.lineTo(x + w, y + h); pth.close()
    c.drawPath(pth, paint(CYAN, 0.25))
    c.save(); c.clipRect(skia.Rect.MakeXYWH(x + 0.25 * w, y, 0.75 * w, h))
    c.drawPath(pth, paint('#ff6b5c', 0.5 * k1)); c.restore()
    text(c, '20Hz', x + 0.25 * w, y + h + 42, 28, 'sans', LAB_TXT, 0.8)
    text(c, '频率 →', x + w - 10, y + h + 42, 28, 'sans', LAB_TXT, 0.8, align='right')
    text(c, '头皮信号功率 · 示意', x + w / 2, y - 24, 30, 'sans', LAB_TXT, 0.8)
    text(c, '肌电混入', x + 0.62 * w, y + h * 0.55, 36, 'sans_b', '#ff9b8e', k1)
    k2 = ap(t, L_(L, 2))
    rrect(c, 80, 1000, W - 160, 180, 16, paint('#0a1a2a', k2 * 0.9))
    text(c, 'Whitham 等，2007 · 临床神经生理学', CX, 1060, 34, 'serif_b', LAB_TXT, k2)
    text(c, '肌肉麻痹对照：20Hz 以上头皮信号，大部分源自肌肉', CX, 1120, 32, 'sans', '#ff9b8e', k2)
    k3 = ap(t, L_(L, 3))
    rrect(c, 80, 1210, W - 160, 180, 16, paint('#0a1a2a', k3 * 0.9))
    text(c, 'Braboszcz 等，2017 · PLOS ONE', CX, 1270, 34, 'serif_b', LAB_TXT, k3)
    text(c, '用独立成分分析排除伪迹后，冥想者伽马仍更高', CX, 1330, 32, 'sans', CYAN, k3)

def s_lutz_tag(c, t, d, L):
    bg_paper(c, t + 12)
    text(c, '伽马同步研究 · 证据分量', CX, 520, 54, 'serif_k', INK, ap(t, 0))
    for i, (s, col) in enumerate([('实证', '#2f6b4f'), ('小样本', GOLD), ('有方法争议', RED)]):
        k = ap(t, 0.6 + i * 0.7, 0.4)
        sc = 1 + 0.25 * (1 - ease_out((t - 0.6 - i * 0.7) / 0.4))
        c.save(); c.translate(CX, 690 + i * 150); c.scale(sc, sc)
        chip(c, s, 0, -45, 56, '#fff8ec', col, k)
        c.restore()
    k = ap(t, L_(L, 1))
    para(c, '作者之一马蒂厄·里卡尔，本人也是长期修行者：贴近经验，也要留意期待效应', CX, 1180, 38, 860, 'serif', INK, k)

def mri_slice(c, x, y, w, t, a=1.0, theme='lab'):
    col = LAB_TXT if theme == 'lab' else INK
    brain(c, x, y, w, col, a, fill=('#0c1a2b' if theme == 'lab' else '#ffffff', 0.8))
    sy = y + ((t * 0.35) % 1.0) * w * 0.95
    c.save(); c.clipPath(brain_path(x, y, w), doAntiAlias=True)
    rglow(c, x + w / 2, sy, w * 0.6, CYAN, 0.25 * a, sy=0.1)
    c.drawLine(x, sy, x + w, sy, paint(CYAN, 0.8 * a, stroke=3))
    c.restore()

def s_lazar_intro(c, t, d, L):
    bg_lab(c, t + 80)
    mri_slice(c, 170, 620, 740, t)
    text(c, '不看脑电 · 量皮层厚度', CX, 480, 52, 'serif_b', LAB_TXT, ap(t, 0.3))
    k = ap(t, L_(L, 1))
    study_card(c, 'Lazar 等，2005', '《神经报告》NeuroReport 16(17): 1893–1897', k, y=1230)

def s_lazar_people(c, t, d, L):
    bg_paper(c, t + 15)
    text(c, '不是僧人，是普通人', CX, 480, 60, 'serif_k', INK, ap(t, 0))
    people_row(c, 20, 140, 640, 5, 70, '#7a4b1f', t, 0.6, gap=74)
    text(c, '内观冥想者 20 人', 290, 1080, 40, 'serif_b', '#7a4b1f', ap(t, 1.2))
    k2 = L_(L, 2) if len(L) > 2 else L_(L, 1)
    people_row(c, 15, 640, 640, 5, 70, '#5b6b78', t, L_(L, 2), gap=74)
    text(c, '对照 15 人', 790, 1080, 40, 'serif_b', '#5b6b78', ap(t, L_(L, 2)))
    k = ap(t, L_(L, 1))
    chip(c, '平均冥想 9 年', 300, 1160, 36, '#fff8ec', '#7a4b1f', k)
    chip(c, '多数每天约 40 分钟', 300, 1240, 36, '#fff8ec', '#7a4b1f', ap(t, L_(L, 1) + 0.5))
    chip(c, '有工作 · 有家庭', 300, 1320, 36, '#fff8ec', '#7a4b1f', ap(t, 0.8))
    chip(c, '年龄、性别等相近', 790, 1160, 36, '#fff8ec', '#5b6b78', ap(t, L_(L, 2) + 0.4))

def s_lazar_result(c, t, d, L):
    bg_lab(c, t + 90)
    cortex_map(c, CX - 360, 400, 720, t, smooth(t / 2.0))
    k = smooth((t - 1.0) / 0.8)
    glow(c, CX - 360 + 0.30 * 720, 400 + 0.34 * 720, 14, '#ffb35c', k)
    text(c, '前额叶', CX - 360 + 0.30 * 720, 400 + 0.34 * 720 - 40, 40, 'serif_b', '#ffd59a', k)
    glow(c, CX - 360 + 0.68 * 720, 400 + 0.60 * 720, 14, '#ffb35c', k)
    text(c, '右前脑岛', CX - 360 + 0.68 * 720, 400 + 0.60 * 720 - 40, 40, 'serif_b', '#ffd59a', k)
    text(c, '横断面研究 · 示意', W - 80, 1120, 26, 'sans', LAB_TXT, 0.6, align='right')
    k2 = ap(t, L_(L, 1))
    rrect(c, 70, 1140, W - 140, 290, 16, paint('#0a1a2a', k2 * 0.92))
    lines = ['“Brain regions associated with attention,', 'interoception and sensory processing were', 'thicker in meditation participants than', 'matched controls”']
    for i, l in enumerate(lines):
        text(c, l, CX, 1192 + i * 44, 31, 'serif', '#ffd59a', k2)
    text(c, '—— Lazar 等，2005，摘要原文', CX, 1395, 26, 'sans', LAB_TXT, k2 * 0.7)

def s_lazar_insula(c, t, d, L):
    bg_lab(c, t + 100)
    brain(c, 170, 520, 740, LAB_TXT, 0.9, fill=('#0c1a2b', 0.9))
    k1 = ap(t, 0.2)
    ix, iy = 170 + 0.46 * 740, 520 + 0.47 * 740
    glow(c, ix, iy, 26, '#ffb35c', k1 * (0.7 + 0.3 * math.sin(t * 5)))
    text(c, '前脑岛', ix, iy + 80, 42, 'serif_b', '#ffd59a', k1)
    text(c, '内感受：心跳 · 呼吸 · 内脏', CX, 440, 42, 'serif_b', '#ffd59a', k1)
    # heartbeat line
    xs = np.linspace(0, 1, 200)
    p = skia.Path()
    for i, xv in enumerate(xs):
        ph = (xv * 3 - t * 1.1) % 1.0
        yv = 0 if not (0.4 < ph < 0.5) else math.sin((ph - 0.4) * 10 * math.pi) * (1 if ph < 0.45 else -0.4)
        X, Y = 120 + xv * (W - 240), 1150 - yv * 70
        p.moveTo(X, Y) if i == 0 else p.lineTo(X, Y)
    c.drawPath(p, paint('#ff8a7a', k1, stroke=4))
    k2 = ap(t, L_(L, 0) + 4.0)
    fx, fy = 170 + 0.17 * 740, 520 + 0.30 * 740
    glow(c, fx, fy, 22, CYAN, k2)
    chip(c, '前额叶：注意 · 自我调控', CX, 1260, 40, '#06121c', CYAN, k2)

def s_lazar_age(c, t, d, L):
    bg_paper(c, t + 18)
    x, y, w, h = 170, 520, 780, 500
    c.drawLine(x, y + h, x + w, y + h, paint(INK, 0.9, stroke=3)); c.drawLine(x, y, x, y + h, paint(INK, 0.9, stroke=3))
    text(c, '年龄 →', x + w, y + h + 55, 32, 'sans', INK, 0.8, align='right')
    text(c, '前额叶皮层厚度', x + 10, y - 25, 32, 'sans', INK, 0.8, align='left')
    k = smooth((t - L_(L, 1)) / 2.0)
    for col, slope, lab in [('#5b6b78', 0.55, '对照'), ('#a8322d', 0.18, '冥想者')]:
        p = skia.Path(); p.moveTo(x + 20, y + 90)
        n = int(60 * k) + 1
        for i in range(n):
            u = i / 60; p.lineTo(x + 20 + u * (w - 40), y + 90 + slope * u * h * 0.9 + 6 * math.sin(u * 13))
        c.drawPath(p, paint(col, 0.95, stroke=6))
        if k > 0.95:
            text(c, lab, x + w - 10, y + 90 + slope * h * 0.9 - 20, 36, 'serif_b', col, 1, align='right')
    text(c, '示意：差异在年长者更明显', CX, y + h + 110, 34, 'serif_b', INK, ap(t, L_(L, 1) + 1.5))
    k3 = ap(t, L_(L, 2))
    rrect(c, 90, 1180, W - 180, 230, 16, paint('#ffffff', k3 * 0.55))
    text(c, '与冥想经验相关的两个区域', CX, 1245, 40, 'serif_b', INK, k3)
    text(c, '右侧前脑岛 · 枕颞视觉区', CX, 1320, 44, 'serif_k', RED, k3)
    text(c, '（相关，不等于因果）', CX, 1380, 30, 'sans', INK, k3 * 0.7)

def s_lazar_caveat(c, t, d, L):
    bg_paper(c, t + 21)
    caveat_list(c, t, L, [(0, '小样本', '20 人 对 15 人'), (0, '横断面', '只能说明相关'), (0, '全是白人', '代表性有限'), (1, '更厚 ≠ 更好', '厚度受多种因素影响，不是能力分数')],
                '同样要标清楚', y0=470, step=190)

def s_causal_q(c, t, d, L):
    bg_paper(c, t + 24)
    text(c, '关键问题', CX, 520, 50, 'serif', RED, ap(t, 0))
    text(c, '冥想 → 大脑？', CX, 720, 96, 'serif_k', INK, ap(t, 0.4))
    text(c, '还是', CX, 850, 50, 'serif', INK, ap(t, 1.5))
    text(c, '大脑 → 冥想？', CX, 1000, 96, 'serif_k', RED, ap(t, 2.2))

def s_causal_paths(c, t, d, L):
    bg_paper(c, t + 27)
    text(c, '两条路径 · 都要画出来', CX, 470, 48, 'serif_b', INK, ap(t, 0))
    two_paths(c, t, L, L_(L, 1), L_(L, 2), base_y=640)
    k = ap(t, L_(L, 3))
    chip(c, '横断面研究：分不开', CX, 1040, 44, '#fff8ec', INK, k)
    # survivorship funnel
    k4 = L_(L, 4)
    if t > k4 - 0.5:
        r = np.random.default_rng(4)
        for i in range(60):
            x0 = 200 + (i % 15) * 48; y0 = 1180 + (i // 15) * 30
            stay = (i % 7 == 0)
            fall = smooth((t - k4 - (i % 10) * 0.05) / 1.5)
            yy = y0 + (0 if stay else fall * 160); aa = ap(t, k4 - 0.4) * (1 if stay else 1 - fall)
            c.drawCircle(x0 + (0 if stay else r.uniform(-20, 20) * fall), yy, 10, paint(RED if stay else '#5b6b78', aa))
        text(c, '坐不住的人早早离开 · 留下的是被筛选的少数', CX, 1430, 32, 'sans', INK, ap(t, k4 + 1.2))

def s_confound(c, t, d, L):
    bg_paper(c, t + 30)
    text(c, '生活方式的混杂', CX, 480, 60, 'serif_k', INK, ap(t, 0))
    brain(c, CX - 180, 790, 360, INK, 0.85, fill=('#ffffff', 0.5), lw=4)
    items = [('饮食', 220, 680), ('作息', 860, 680), ('烟酒', 220, 1180), ('社群', 860, 1180)]
    for i, (s, x, y) in enumerate(items):
        k = ap(t, 0.8 + i * 0.6)
        c.drawCircle(x, y, 95, paint('#ffffff', k * 0.6)); c.drawCircle(x, y, 95, paint(INK, k, stroke=4))
        text(c, s, x, y + 22, 60, 'serif_k', INK, k)
        arrow(c, x + (80 if x < CX else -80), y + (50 if y < 900 else -50), CX + (-120 if x < CX else 120), 930 + (-40 if y < 900 else 60), RED, k, w=6, head=22, prog=smooth((t - 1.0 - i * 0.6) / 0.8))
    text(c, '任何一项，都可能在大脑留下痕迹', CX, 1380, 40, 'serif_b', RED, ap(t, L_(L, 1)))

def s_plastic(c, t, d, L):
    bg_paper(c, t + 33)
    k1 = L_(L, 1)
    study_card(c, 'Draganski 等，2004', '《自然》Nature 427: 311–312', ap(t, k1), theme='paper', y=400)
    # juggling balls
    for i in range(3):
        ph = (t * 0.9 + i / 3) % 1.0
        x = CX + math.cos(ph * 2 * math.pi) * 170
        y = 790 - abs(math.sin(ph * 2 * math.pi)) * 180
        c.drawCircle(x, y, 26, paint([RED, GOLD, '#2f6b4f'][i], 0.9))
    person(c, CX, 980, 160, INK, 0.9)
    text(c, '练习抛接杂耍 3 个月', CX, 1060, 40, 'serif_b', INK, ap(t, k1 + 0.6))
    # bar timeline: before / after 3mo / after stop
    ks = ap(t, k1 + 1.2)
    vals = [0.45, 0.75, 0.58]; labs = ['练习前', '练习 3 个月', '停练后']
    for i, (v, lb) in enumerate(zip(vals, labs)):
        bx = 250 + i * 290; hh = v * 220 * ks
        rrect(c, bx - 55, 1340 - hh, 110, hh, 10, paint([INK, RED, GOLD][i], 0.85 * ks))
        text(c, lb, bx, 1390, 30, 'sans', INK, ks)
    text(c, '视觉运动相关脑区灰质 · 示意', CX, 1090 + 70, 28, 'sans', INK, ks * 0.7)
    k2 = ap(t, L_(L, 2))
    chip(c, '问题不是能不能变，而是能否被反复验证', CX, 1420, 34, '#fff8ec', RED, k2)

def s_rct(c, t, d, L):
    bg_paper(c, t + 36)
    text(c, '随机分组 · 前后追踪', CX, 480, 60, 'serif_k', INK, ap(t, 0))
    r = np.random.default_rng(9)
    pts = [(r.uniform(-1, 1), r.uniform(-1, 1)) for _ in range(36)]
    k = smooth((t - 1.5) / 1.6)
    for i, (px, py) in enumerate(pts):
        g = i % 3
        tx = [250, CX, 830][g] + px * 60; ty = 900 + py * 60
        x = lerp(CX + px * 160, tx, k); y = lerp(660 + py * 60, ty, k)
        c.drawCircle(x, y, 13, paint([RED, GOLD, '#5b6b78'][g], 0.9))
    for i, s in enumerate(['练', '主动对照', '不练（等待）']):
        text(c, s, [250, CX, 830][i], 1020, 36, 'serif_b', INK, k)
    k2 = ap(t, 3.5)
    for i, s in enumerate(['前测扫描', '训练', '后测扫描']):
        chip(c, s, 220 + i * 320, 1120, 36, '#fff8ec', INK, ap(t, 3.5 + i * 0.5))
        if i < 2: arrow(c, 330 + i * 320, 1150, 420 + i * 320, 1150, INK, k2, w=4, head=16)
    k3 = ap(t, L_(L, 1))
    text(c, '结果：有正有负', CX, 1340, 56, 'serif_k', RED, k3)

def s_holzel(c, t, d, L):
    bg_paper(c, t + 39)
    study_card(c, 'Hölzel 等，2011', '《精神病学研究：神经影像》191(1): 36–43', ap(t, 0), theme='paper', y=420)
    text(c, '8 周正念减压', CX, 720, 64, 'serif_k', INK, ap(t, 0.5))
    text(c, '海马等区域灰质密度 ↑', CX, 830, 56, 'serif_b', '#2f6b4f', ap(t, 1.2))
    k = ap(t, L_(L, 1))
    chip(c, '16 人 对 17 人', 300, 960, 40, '#fff8ec', GOLD, k)
    chip(c, '非随机分组', 780, 960, 40, '#fff8ec', RED, ap(t, L_(L, 1) + 0.6))
    seal(c, '线索', CX, 1180, 50, ap(t, L_(L, 1) + 1.4))
    text(c, '初步线索，不是定论', CX, 1350, 40, 'serif_b', INK, ap(t, L_(L, 1) + 1.6))

def s_kral(c, t, d, L):
    bg_paper(c, t + 42)
    study_card(c, 'Kral 等，2022', '《科学进展》Science Advances 8(20): eabk3316', ap(t, 0), theme='paper', y=400)
    k1 = L_(L, 1)
    groups = [('正念减压', 75, RED), ('健康促进', 73, GOLD), ('等待组', 70, '#5b6b78')]
    for i, (g, n, col) in enumerate(groups):
        x = 230 + i * 310
        k = ap(t, k1 + i * 0.4)
        people_row(c, 9, x - 80, 700, 3, 60, col, t, k1 + i * 0.4, gap=80, a=1)
        text(c, g, x, 960, 40, 'serif_b', col, k)
        text(c, f'n = {n}', x, 1010, 32, 'sans', INK, k)
    k2 = L_(L, 2)
    ks = ap(t, k2)
    text(c, '灰质体积 · 灰质密度 · 皮层厚度', CX, 1100, 36, 'sans', INK, ks)
    for i in range(3):
        bx = 230 + i * 310; hh = 120 * ks
        rrect(c, bx - 60, 1280 - hh, 120, hh, 8, paint(groups[i][2], 0.8 * ks))
    text(c, '≈ 无可检测差异', CX, 1360, 52, 'serif_k', RED, ap(t, k2 + 2.5))
    k3 = ap(t, L_(L, 3))
    text(c, '作者：也许需要长得多的训练', CX, 1430, 34, 'sans', INK, k3)

def s_vandam(c, t, d, L):
    bg_paper(c, t + 45)
    study_card(c, 'Van Dam 等，2018', 'Perspectives on Psychological Science 13(1): 36–61', ap(t, 0), theme='paper', y=420)
    text(c, 'Mind the Hype', CX, 740, 84, 'serif_k', INK, ap(t, 0.6))
    text(c, '《警惕炒作》（意译）', CX, 820, 40, 'serif', INK, ap(t, 1.0))
    for i, s in enumerate(['定义不清', '样本太小', '宣传走在证据前面']):
        chip(c, s, CX, 920 + i * 120, 46, '#fff8ec', RED, ap(t, L_(L, 1) + i * 0.7))

def s_honest(c, t, d, L):
    bg_paper(c, t + 48)
    text(c, '元分析：21 项研究 · 约 300 名修行者', CX, 470, 40, 'serif_b', INK, ap(t, 0))
    text(c, 'Fox 等，2014 · Neurosci Biobehav Rev', CX, 520, 28, 'sans', INK, ap(t, 0) * 0.7)
    r = np.random.default_rng(21)
    x0 = 300; zero = 380; sc = 260
    c.drawLine(zero, 570, zero, 1150, paint(INK, 0.6, stroke=2))
    for i in range(21):
        k = ap(t, 0.4 + i * 0.08, 0.3)
        dv = r.normal(0.46, 0.35); ci = r.uniform(0.25, 0.6)
        y = 590 + i * 25
        c.drawLine(zero + (dv - ci) * sc, y, zero + (dv + ci) * sc, y, paint(INK, 0.6 * k, stroke=2))
        c.drawRect(skia.Rect.MakeXYWH(zero + dv * sc - 6, y - 6, 12, 12), paint(INK, k))
    k2 = ap(t, 2.4)
    p = skia.Path(); yd = 1150; xm = zero + 0.46 * sc
    p.moveTo(xm - 50, yd); p.lineTo(xm, yd - 18); p.lineTo(xm + 50, yd); p.lineTo(xm, yd + 18); p.close()
    c.drawPath(p, paint(RED, k2))
    text(c, '平均效应 d ≈ 0.46（中等）', xm + 80, yd + 12, 34, 'serif_b', RED, k2, align='left')
    text(c, '示意森林图', W - 70, 1210, 26, 'sans', INK, 0.6, align='right')
    chip(c, '作者提醒：发表偏倚与方法局限', CX, 1250, 38, '#fff8ec', RED, ap(t, L_(L, 1)))
    k3 = ap(t, L_(L, 2))
    text(c, '结构变化的复现性有限', CX, 1400, 50, 'serif_k', INK, k3)

def s_altered(c, t, d, L):
    bg_paper(c, t + 51)
    a = ap(t, L_(L, 1))
    rrect(c, CX - 230, 420, 460, 600, 14, paint('#2d3e4a', a * 0.92))
    text(c, 'Altered', CX, 610, 76, 'serif_k', '#f3e9d8', a)
    text(c, 'Traits', CX, 700, 76, 'serif_k', '#f3e9d8', a)
    c.drawLine(CX - 140, 750, CX + 140, 750, paint(GOLD, a, stroke=3))
    text(c, 'Goleman & Davidson', CX, 820, 32, 'sans', '#f3e9d8', a * 0.9)
    text(c, '2017', CX, 880, 32, 'sans', '#f3e9d8', a * 0.9)
    text(c, '文字示意，非原书封面', CX, 1060, 26, 'sans', INK, a * 0.6)
    k = ap(t, L_(L, 2))
    text(c, '6000+ 项研究', 300, 1180, 52, 'serif_k', INK, k)
    arrow(c, 480, 1162, 600, 1162, RED, k, w=6, head=20)
    text(c, '约 60 项', 780, 1180, 52, 'serif_k', RED, k)
    text(c, '只讲方法最严谨的（据作者介绍）', CX, 1250, 32, 'sans', INK, k * 0.8)
    k2 = ap(t, L_(L, 3))
    para(c, '“早期许多研究，包括我实验室早年的工作，看的是冥想当下的变化；真正要紧的是持久的改变。”—— 戴维森（访谈意译）', CX, 1330, 32, 900, 'serif', INK, k2, lh=1.45)

def s_states(c, t, d, L):
    bg_paper(c, t + 54)
    # ripples (state) vs carved stone layers (trait)
    text(c, '状态', 280, 520, 72, 'serif_k', INK, ap(t, 0))
    text(c, '一时 · 短期练习', 280, 590, 32, 'sans', INK, ap(t, 0.3))
    for i in range(4):
        ph = (t * 0.5 + i / 4) % 1
        c.drawOval(skia.Rect.MakeXYWH(280 - 40 - ph * 150, 780 - 12 - ph * 45, 80 + ph * 300, 24 + ph * 90), paint(INK, (1 - ph) * 0.7, stroke=3))
    k = ap(t, 1.5)
    text(c, '特质', 800, 520, 72, 'serif_k', RED, k)
    text(c, '持久 · 长期大量修行', 800, 590, 32, 'sans', RED, k)
    for i in range(7):
        y = 680 + i * 32
        c.drawLine(640, y, 960, y + 6 * math.sin(i), paint(['#8a6a4a', '#7a5a3a', '#6b4c30'][i % 3], k * 0.9, stroke=22))
    text(c, '≠', CX, 820, 120, 'serif_k', INK, ap(t, L_(L, 1)))
    text(c, '几周的课程  ≠  几十年的修行', CX, 1100, 48, 'serif_b', INK, ap(t, L_(L, 1) + 0.6))
    k3 = ap(t, L_(L, 2))
    chip(c, '二手材料 · 作者自评', CX, 1220, 38, '#fff8ec', GOLD, k3)
    text(c, '越让人兴奋的结论，越要慢一点下', CX, 1390, 42, 'serif_b', RED, ap(t, L_(L, 2) + 1.5))

def lamp_water(c, t, cx=CX, top=520, a=1.0, ripple=0.0, wh=320):
    # lamp: base + flame
    flick = 1 + 0.03 * math.sin(t * 11) + 0.02 * math.sin(t * 17)
    rglow(c, cx, top + 160, 380, '#ffcf7a', 0.28 * a)
    rrect(c, cx - 90, top + 300, 180, 26, 10, paint('#5a4632', a))
    rrect(c, cx - 22, top + 230, 44, 80, 8, paint('#6b5440', a))
    p = skia.Path(); fy = top + 230
    p.moveTo(cx, fy - 150 * flick); p.cubicTo(cx + 46, fy - 80, cx + 38, fy - 10, cx, fy)
    p.cubicTo(cx - 38, fy - 10, cx - 46, fy - 80, cx, fy - 150 * flick); p.close()
    c.drawPath(p, paint('#ffb347', a * 0.95, blur=3))
    rglow(c, cx, fy - 60, 120, '#fff2c4', a * 0.55, sy=1.4)
    # water
    wy = top + 470
    rrect(c, 60, wy, W - 120, wh, 30, paint('#2c3a44', a * 0.85))
    # reflection
    c.save(); c.clipRect(skia.Rect.MakeXYWH(60, wy, W - 120, wh))
    for i in range(26):
        yy = wy + 40 + i * 13
        off = ripple * 30 * math.sin(i * 1.3 + t * 3)
        ww = (80 - i * 2) * (1 + ripple * 0.5)
        c.drawLine(cx - ww + off, yy, cx + ww + off, yy, paint('#ffcf7a', a * (0.55 - i * 0.018), stroke=6))
    c.restore()
    rglow(c, cx, wy + 120, 300, '#ffcf7a', 0.10 * a)

def s_return(c, t, d, L):
    bg_paper(c, t + 57)
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint('#1b1814', 0.25))
    lamp_water(c, t, top=560, a=ap(t, 0, 1.2), ripple=max(0, 1 - t / 3))

def s_tanjing(c, t, d, L):
    bg_paper(c, t + 60)
    cols = ['定慧一體，不是二', '定是慧體，慧是定用', '即慧之時定在慧', '即定之時慧在定']
    for i, col in enumerate(cols):
        x = 830 - i * 150
        vtext(c, col, x, 400, 74, 'serif_tc', INK, ap(t, 0.2 + i * 1.6, 1.0))
    seal(c, '六祖壇經', 190, 1010, 44, ap(t, 2.0))
    text(c, '《六祖坛经·定慧品》（宗宝本）', CX, 1250, 34, 'serif', INK, ap(t, 1.0) * 0.85)
    k = ap(t, L_(L, 1))
    rrect(c, 80, 1300, W - 160, 140, 16, paint('#ffffff', k * 0.5))
    text(c, '安定是智慧的本体', CX, 1358, 42, 'serif_b', RED, k)
    text(c, '智慧是安定的作用', CX, 1418, 42, 'serif_b', RED, k)

def s_tanjing2(c, t, d, L):
    bg_paper(c, t + 63)
    lamp_water(c, t + 5, top=470, a=1, ripple=0)
    text(c, '不是大脑某处变厚', CX, 1330, 46, 'serif_b', INK, ap(t, 0.3))
    text(c, '而是安定与明白，一起生长', CX, 1400, 46, 'serif_k', RED, ap(t, 2.5))

def s_analogy(c, t, d, L):
    bg_paper(c, t + 66)
    k = ap(t, 0)
    rrect(c, 80, 480, 430, 520, 20, paint('#ffffff', k * 0.5)); rrect(c, 570, 480, 430, 520, 20, paint('#ffffff', k * 0.5))
    text(c, '脑科学', 295, 580, 58, 'serif_k', '#2d5a78', k)
    for i, s in enumerate(['测量', '统计', '可重复']): text(c, s, 295, 680 + i * 80, 42, 'serif', '#2d5a78', k)
    text(c, '坛经', 785, 580, 58, 'serif_k', RED, k)
    for i, s in enumerate(['心地', '体验', '实修']): text(c, s, 785, 680 + i * 80, 42, 'serif', RED, k)
    k2 = ap(t, L_(L, 1))
    text(c, '≈ 印照 · 类比', CX, 1130, 64, 'serif_k', INK, k2)
    text(c, '≠ 证明', CX, 1240, 64, 'serif_k', RED, ap(t, L_(L, 1) + 1.2))

def s_traces(c, t, d, L):
    bg_paper(c, t + 69)
    brain(c, 220, 520, 640, INK, 0.75, fill=('#ffffff', 0.35), lw=4)
    for (bx, by) in [(0.2, 0.3), (0.46, 0.47)]:
        glow(c, 220 + bx * 640, 520 + by * 640, 16, GOLD, 0.6 + 0.3 * math.sin(t * 2))
    chip(c, '注意更稳一些', 320, 1050, 38, '#fff8ec', '#2d5a78', ap(t, 1.0))
    chip(c, '内在觉察更细一些', 760, 1050, 38, '#fff8ec', '#2d5a78', ap(t, 2.0))
    k = ap(t, L_(L, 1))
    text(c, '不急着下结论 · 不把小样本当铁证', CX, 1220, 42, 'serif_b', INK, k)
    text(c, '看清楚再说，本身就接近“慧”', CX, 1300, 46, 'serif_k', RED, ap(t, L_(L, 1) + 2.5))

def s_lamp(c, t, d, L):
    bg_paper(c, t + 72)
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint('#1b1814', 0.35))
    lamp_water(c, t, top=470, a=1, ripple=max(0, 0.8 - t / 2.5))
    text(c, '灯不摇，水才静', CX, 1330, 50, 'serif_k', '#f3e9d8', ap(t, 0.2))
    text(c, '水静了，灯影才清楚', CX, 1405, 50, 'serif_k', '#f3e9d8', ap(t, 1.6))

def s_ending(c, t, d, L):
    bg_paper(c, t + 75)
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), paint('#1b1814', 0.35 * (1 - ap(t, 0, 1.5))))
    lamp_water(c, t + 3, top=330, a=0.6, ripple=0, wh=250)
    k = ap(t, 0.3)
    rrect(c, 70, 1080, W - 140, 240, 20, paint('#fffaf0', k * 0.8))
    text(c, '别把修行当成要刷出来的成绩单', CX, 1150, 44, 'serif_b', INK, k)
    text(c, '安定与明白', CX, 1225, 54, 'serif_k', RED, k)
    text(c, '本来就是一起长出来的', CX, 1292, 44, 'serif_b', INK, k)
    k2 = ap(t, L_(L, 1))
    text(c, '定是慧體，慧是定用', CX, 1400, 60, 'serif_tc', INK, k2, spacing=4)
    text(c, '——《六祖坛经·定慧品》', CX, 1462, 32, 'serif', INK, k2 * 0.8)

SCENES = {k[2:]: v for k, v in globals().items() if k.startswith('s_') and callable(v)}
LAB_SCENES = {'hook_eeg', 'hook_gamma', 'hook_cortex', 'lutz_intro', 'lutz_result', 'lutz_trait', 'gamma_meaning', 'emg',
              'lazar_intro', 'lazar_result', 'lazar_insula'}
