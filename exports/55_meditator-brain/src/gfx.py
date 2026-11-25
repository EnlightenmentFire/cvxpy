"""Drawing helpers on skia for the vertical video (1080x1920)."""
import math, os, functools
import numpy as np, skia

W, H = 1080, 1920
FONT_DIR = os.environ.get('EP_FONT_DIR', os.path.expanduser('~/fonts'))

@functools.lru_cache(None)
def typeface(name):
    files = {'serif': 'NotoSerifSC-Regular.otf', 'serif_b': 'NotoSerifSC-Bold.otf', 'serif_k': 'NotoSerifSC-Black.otf',
             'serif_tc': 'NotoSerifTC-Bold.otf', 'sans': 'NotoSansSC-Medium.otf', 'sans_b': 'NotoSansSC-Bold.otf'}
    return skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, files[name]))

@functools.lru_cache(None)
def font(name, size):
    f = skia.Font(typeface(name), size); f.setSubpixel(True); f.setEdging(skia.Font.Edging.kAntiAlias)
    return f

def rgba(hexs, a=1.0):
    hexs = hexs.lstrip('#'); r, g, b = int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), r, g, b)

def paint(col='#ffffff', a=1.0, stroke=None, cap='round', blur=None, join='round'):
    p = skia.Paint(AntiAlias=True, Color=rgba(col, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap({'round': skia.Paint.kRound_Cap, 'butt': skia.Paint.kButt_Cap, 'square': skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

# ---------- timing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def ap(t, t0, d=0.6): return smooth((t - t0) / d)
def lerp(a, b, k): return a + (b - a) * k

# ---------- text ----------
def text_w(s, fname, size): return font(fname, size).measureText(s)

def text(c, s, x, y, size, fname='serif_b', col='#ffffff', a=1.0, align='center', shadow=None, stroke=None, spacing=0):
    """y = baseline."""
    if a <= 0.003 or not s: return
    f = font(fname, size)
    if spacing:
        w = sum(f.measureText(ch) for ch in s) + spacing * (len(s) - 1)
    else:
        w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    def draw(p, dx=0, dy=0):
        if spacing:
            xx = x0
            for ch in s:
                c.drawString(ch, xx + dx, y + dy, f, p); xx += f.measureText(ch) + spacing
        else:
            c.drawString(s, x0 + dx, y + dy, f, p)
    if shadow:
        draw(paint(shadow[0], a * shadow[1], blur=shadow[2]), shadow[3], shadow[4])
    if stroke:
        draw(paint(stroke[0], a * stroke[1], stroke=stroke[2]))
    draw(paint(col, a))
    return w

def wrap(s, fname, size, maxw):
    lines, cur = [], ''
    for ch in s:
        if text_w(cur + ch, fname, size) > maxw and cur:
            if ch in '，。；：？！、）」』”':
                cur += ch; lines.append(cur); cur = ''; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

def para(c, s, x, y, size, maxw, fname='serif', col='#ffffff', a=1.0, align='center', lh=1.5, **kw):
    ls = wrap(s, fname, size, maxw)
    for i, l in enumerate(ls):
        text(c, l, x, y + i * size * lh, size, fname, col, a, align, **kw)
    return len(ls) * size * lh

def vtext(c, s, x, y, size, fname='serif_tc', col='#222222', a=1.0, gap=1.12):
    """vertical column, top at y."""
    for i, ch in enumerate(s):
        if ch in '，。、；：':
            text(c, ch, x + size * 0.3, y + (i + 0.55) * size * gap, size, fname, col, a)
        else:
            text(c, ch, x, y + (i + 0.85) * size * gap, size, fname, col, a)

# ---------- shapes ----------
def rrect(c, x, y, w, h, r, p): c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), p)

def chip(c, s, x, y, size=30, fg='#ffffff', bg='#a8322d', a=1.0, align='center', fname='sans_b', pad=18):
    w = text_w(s, fname, size) + pad * 2; h = size * 1.6
    x0 = x - w / 2 if align == 'center' else (x if align == 'left' else x - w)
    rrect(c, x0, y, w, h, h / 2, paint(bg, a))
    text(c, s, x0 + w / 2, y + h * 0.5 + size * 0.36, size, fname, fg, a)
    return w

def seal(c, s, x, y, size=46, a=1.0, col='#a8322d'):
    """vermilion square seal with 2-4 chars."""
    n = len(s); cols = 2 if n == 4 else 1
    rows = 2 if n >= 2 else 1
    w = size * cols + size * 0.5; h = size * rows + size * 0.5
    rrect(c, x - w / 2, y - h / 2, w, h, size * 0.12, paint(col, a * 0.92))
    rrect(c, x - w / 2 + 5, y - h / 2 + 5, w - 10, h - 10, size * 0.1, paint('#f3e9d8', a * 0.85, stroke=2.5))
    if n == 4:
        order = [s[0], s[1], s[2], s[3]]
        pos = [(1, 0), (1, 1), (0, 0), (0, 1)]  # read right col top->bottom, then left
        for ch, (cx, cy) in zip(order, pos):
            text(c, ch, x - w / 2 + size * 0.25 + cx * size + size / 2, y - h / 2 + size * 0.25 + cy * size + size * 0.86, size * 0.92, 'serif_k', '#f6ecdc', a)
    else:
        for i, ch in enumerate(s):
            text(c, ch, x, y - h / 2 + size * 0.25 + i * size + size * 0.86, size * 0.92, 'serif_k', '#f6ecdc', a)

def person(c, x, y, s, col, a=1.0):
    c.drawCircle(x, y - s * 0.62, s * 0.22, paint(col, a))
    path = skia.Path(); path.moveTo(x - s * 0.36, y + s * 0.2)
    path.cubicTo(x - s * 0.36, y - s * 0.38, x + s * 0.36, y - s * 0.38, x + s * 0.36, y + s * 0.2); path.close()
    c.drawPath(path, paint(col, a))

def arrow(c, x0, y0, x1, y1, col, a=1.0, w=8, head=28, prog=1.0, curve=0.0, ink=False):
    prog = clamp(prog)
    if prog <= 0: return
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    cx, cy = mx + nx * curve, my + ny * curve
    pts = []
    N = 40
    for i in range(int(N * prog) + 1):
        u = i / N
        px = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1
        py = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1
        pts.append((px, py))
    if len(pts) < 2: return
    if ink:
        for k in range(len(pts) - 1):
            u = k / N
            ww = w * (0.55 + 0.9 * math.sin(math.pi * min(1, u * 1.15 + 0.05)))
            c.drawLine(pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], paint(col, a, stroke=ww))
    else:
        path = skia.Path(); path.moveTo(*pts[0])
        for p in pts[1:]: path.lineTo(*p)
        c.drawPath(path, paint(col, a, stroke=w))
    if prog > 0.97:
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        ang = math.atan2(by - ay, bx - ax)
        hp = skia.Path(); hp.moveTo(bx + math.cos(ang) * head * 0.4, by + math.sin(ang) * head * 0.4)
        hp.lineTo(bx + math.cos(ang + 2.6) * head, by + math.sin(ang + 2.6) * head)
        hp.lineTo(bx + math.cos(ang - 2.6) * head, by + math.sin(ang - 2.6) * head); hp.close()
        c.drawPath(hp, paint(col, a))

def catmull(pts, closed=True, n=12):
    out = []; m = len(pts)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = pts[(i - 1) % m], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        if not closed:
            p0 = pts[max(i - 1, 0)]; p3 = pts[min(i + 2, m - 1)]; p2 = pts[i + 1]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    return out

BRAIN = [(0.12, 0.30), (0.20, 0.13), (0.38, 0.04), (0.58, 0.03), (0.76, 0.09), (0.90, 0.21), (0.97, 0.37), (0.955, 0.50),
         (0.91, 0.585), (0.93, 0.66), (0.85, 0.75), (0.73, 0.75), (0.665, 0.69), (0.635, 0.80), (0.60, 0.94), (0.53, 0.94),
         (0.545, 0.75), (0.45, 0.705), (0.31, 0.67), (0.235, 0.575), (0.16, 0.555), (0.095, 0.50), (0.07, 0.40)]

def brain_path(x, y, w):
    pts = catmull([(x + px * w, y + py * w) for px, py in BRAIN])
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    p.close(); return p

def brain(c, x, y, w, col, a=1.0, fill=None, gyri=True, lw=5, seed=3):
    p = brain_path(x, y, w)
    if fill: c.drawPath(p, paint(fill[0], a * fill[1]))
    if gyri:
        c.save(); c.clipPath(p, doAntiAlias=True)
        r = np.random.default_rng(seed)
        for k in range(48):
            cx, cy = x + w * r.uniform(0.12, 0.92), y + w * r.uniform(0.08, 0.62)
            L = w * r.uniform(0.04, 0.10); ang = r.uniform(0, math.pi)
            pts = [(cx + math.cos(ang) * L * (u - 0.5) + math.sin(u * 9 + k) * w * 0.012,
                    cy + math.sin(ang) * L * (u - 0.5) + math.cos(u * 7 + k) * w * 0.012) for u in np.linspace(0, 1, 9)]
            pp = skia.Path(); pp.moveTo(*pts[0])
            for q in pts[1:]: pp.lineTo(*q)
            c.drawPath(pp, paint(col, a * 0.45, stroke=lw * 0.6))
        # lateral sulcus
        pp = skia.Path(); pp.moveTo(x + w * 0.30, y + w * 0.52); pp.quadTo(x + w * 0.5, y + w * 0.43, x + w * 0.66, y + w * 0.36)
        c.drawPath(pp, paint(col, a * 0.5, stroke=lw * 0.8))
        c.restore()
    c.drawPath(p, paint(col, a, stroke=lw))

def rglow(c, x, y, r, col, a=1.0, sx=1.0, sy=1.0):
    """soft radial halo via gradient shader (cheap replacement for big blurs)."""
    if a <= 0.003: return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(0, 0), r, [rgba(col, a), rgba(col, a * 0.35), rgba(col, 0)], [0.0, 0.45, 1.0]))
    c.save(); c.translate(x, y); c.scale(sx, sy); c.drawCircle(0, 0, r, p); c.restore()

def glow(c, x, y, r, col, a=1.0):
    rglow(c, x, y, r * 3.2, col, a * 0.45)
    c.drawCircle(x, y, r * 0.85, paint(col, a * 0.95))

def img_from_rgba(arr):
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)

def draw_img(c, img, x, y, w, h, a=1.0):
    p = skia.Paint(AntiAlias=True); p.setAlphaf(clamp(a))
    c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear), p)
