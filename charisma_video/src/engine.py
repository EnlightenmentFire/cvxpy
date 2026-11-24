# -*- coding: utf-8 -*-
"""Rendering helpers on top of skia-python. 1080x1920 vertical frames."""
import math, os, functools
import numpy as np
import skia

W, H = 1080, 1920
FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONTDIR = os.path.join(HERE, "..", "fonts")

# ---------------------------------------------------------------- palette
def C(r, g, b, a=255):
    return skia.Color(int(r), int(g), int(b), int(max(0, min(255, a))))

BG0 = (8, 26, 23)
BG1 = (15, 43, 38)
GOLD = (214, 178, 94)
GOLD_HI = (246, 222, 160)
GOLD_DIM = (120, 98, 52)
RED = (196, 86, 70)        # "暗红" readable on deep green
RED_DEEP = (130, 40, 34)
IVORY = (238, 230, 212)
MUTED = (150, 168, 158)
INK = (6, 14, 12)

# layout
TOP_LABEL_Y = 228
STAGE_TOP, STAGE_BOT = 300, 1250
SUB_Y = 1395   # centre of subtitle block

# ---------------------------------------------------------------- fonts
FONT_FILES = {
    "serif": "NotoSerifCJKsc-Regular.otf",
    "serif_sb": "NotoSerifCJKsc-SemiBold.otf",
    "serif_b": "NotoSerifCJKsc-Bold.otf",
    "sans": "NotoSansCJKsc-Regular.otf",
    "sans_m": "NotoSansCJKsc-Medium.otf",
    "garamond": "EBGaramond[wght].ttf",
    "garamond_i": "EBGaramond-Italic[wght].ttf",
    "cinzel": "Cinzel[wght].ttf",
}

@functools.lru_cache(None)
def typeface(name):
    return skia.Typeface.MakeFromFile(os.path.join(FONTDIR, FONT_FILES[name]))

@functools.lru_cache(None)
def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f

FALLBACK = {"garamond": "serif", "garamond_i": "serif", "cinzel": "serif"}

@functools.lru_cache(None)
def has_glyph(fname, ch):
    return typeface(fname).unicharToGlyph(ord(ch)) != 0

def runs(s, fname):
    fb = FALLBACK.get(fname)
    if not fb:
        return [(s, fname)]
    out = []
    for ch in s:
        fn = fname if (has_glyph(fname, ch) or ch == " ") else fb
        if out and out[-1][1] == fn:
            out[-1] = (out[-1][0] + ch, fn)
        else:
            out.append((ch, fn))
    return out

def text_width(s, fname, size, tracking=0.0):
    w = sum(font(fn, size).measureText(r) for r, fn in runs(s, fname))
    return w + tracking * size * max(0, len(s) - 1)

def draw_text(c, s, x, y, fname, size, color, alpha=1.0, align="left", tracking=0.0,
              glow=0.0, glow_color=None, shadow=0.0):
    """Draw single-line text with baseline y. align: left/center/right."""
    if alpha <= 0.002 or not s:
        return
    f = font(fname, size)
    w = text_width(s, fname, size, tracking)
    if align == "center":
        x = x - w / 2
    elif align == "right":
        x = x - w
    def _draw(paint):
        xx = x
        for r, fn in runs(s, fname):
            ff = font(fn, size)
            if tracking == 0:
                c.drawString(r, xx, y, ff, paint)
                xx += ff.measureText(r)
            else:
                for ch in r:
                    c.drawString(ch, xx, y, ff, paint)
                    xx += ff.measureText(ch) + tracking * size
    if shadow > 0:
        p = skia.Paint(AntiAlias=True, Color=C(0, 0, 0, 200 * alpha))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, shadow))
        c.save(); c.translate(0, shadow * 0.4); _draw(p); c.restore()
    if glow > 0:
        gc = glow_color or color
        p = skia.Paint(AntiAlias=True, Color=C(*gc[:3], 170 * alpha))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        _draw(p)
    p = skia.Paint(AntiAlias=True, Color=C(*color[:3], 255 * alpha))
    _draw(p)
    return w

@functools.lru_cache(4096)
def wrap_cjk(s, fname, size, maxw):
    """Greedy wrap for mixed CJK/Latin text; keeps latin words together and
    avoids starting a line with closing punctuation."""
    tokens, buf = [], ""
    for ch in s:
        if (ord(ch) < 0x2E80 and (ch.isalnum() or ch in "'’-.,!?;:()„“\"")):
            buf += ch
        else:
            if buf:
                tokens.append(buf); buf = ""
            tokens.append(ch)
    if buf:
        tokens.append(buf)
    lines, cur = [], ""
    no_start = "，。、；：？！”’）》」』…—,.;:?!)"
    for tk in tokens:
        trial = cur + tk
        if text_width(trial, fname, size) <= maxw or not cur:
            cur = trial
        else:
            if tk[0] in no_start:
                cur = trial  # allow slight overflow rather than orphan punctuation
            else:
                lines.append(cur.rstrip()); cur = tk.lstrip()
    if cur:
        lines.append(cur.rstrip())
    return lines

def draw_paragraph(c, s, cx, y, fname, size, color, maxw, alpha=1.0, line_h=1.45,
                   align="center", **kw):
    lines = wrap_cjk(s, fname, size, maxw)
    for i, ln in enumerate(lines):
        draw_text(c, ln, cx, y + i * size * line_h, fname, size, color, alpha, align=align, **kw)
    return len(lines)

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ease(x):  # smoothstep
    x = clamp(x); return x * x * (3 - 2 * x)

def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def ease_in(x):
    x = clamp(x); return x ** 3

def prog(t, t0, dur):
    return clamp((t - t0) / max(dur, 1e-6))

def lerp(a, b, x):
    return a + (b - a) * x

def mix(c1, c2, x):
    return tuple(lerp(a, b, x) for a, b in zip(c1, c2))

# ---------------------------------------------------------------- paints
def paint(color, alpha=1.0, stroke=None, cap="round", blur=0.0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=C(*color[:3], (color[3] if len(color) > 3 else 255) * alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def glow_circle(c, x, y, r, color, alpha=1.0, layers=((3.0, 0.10), (1.8, 0.22), (1.2, 0.45))):
    for k, a in layers:
        p = paint(color, alpha * a, blur=r * k * 0.35)
        c.drawCircle(x, y, r * k * 0.6, p)

def radial(c, x, y, r, inner, outer, alpha=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        center=(x, y), radius=r,
        colors=[C(*inner[:3], (inner[3] if len(inner) > 3 else 255) * alpha),
                C(*outer[:3], (outer[3] if len(outer) > 3 else 0) * alpha)]))
    c.drawCircle(x, y, r, p)

def linear_rect(c, rect, p0, p1, c0, c1):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(points=[p0, p1], colors=[C(*c0), C(*c1)]))
    c.drawRect(rect, p)

def path_from(points, closed=False, smooth=False):
    pa = skia.Path()
    if not points:
        return pa
    pa.moveTo(*points[0])
    if smooth and len(points) > 2:
        # Catmull-Rom -> cubic
        pts = [points[0]] + list(points) + [points[-1]]
        for i in range(1, len(pts) - 2):
            p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            pa.cubicTo(*c1, *c2, *p2)
    else:
        for pt in points[1:]:
            pa.lineTo(*pt)
    if closed:
        pa.close()
    return pa

def trimmed(pa, start, stop):
    """Return paint path effect for trim; usage: p.setPathEffect(trim_effect(..))"""
    return skia.TrimPathEffect.Make(clamp(start), clamp(stop))

def draw_path_progress(c, pa, p, frac):
    if frac <= 0:
        return
    if frac < 1:
        p = skia.Paint(p)
        p.setPathEffect(skia.TrimPathEffect.Make(0, clamp(frac)))
    c.drawPath(pa, p)

def path_point(pa, frac):
    meas = skia.PathMeasure(pa, False)
    L = meas.getLength()
    pos, tan = meas.getPosTan(clamp(frac) * L)
    return (pos.x(), pos.y()), (tan.x(), tan.y()), L

# ---------------------------------------------------------------- textures
_rng = np.random.default_rng(7)

def to_image(arr):
    arr = np.ascontiguousarray(arr.astype(np.uint8))
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)

@functools.lru_cache(None)
def noise_image(w=W, h=H, amp=10, seed=3, scale=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h // scale + 1, w // scale + 1))
    if scale > 1:
        n = np.kron(n, np.ones((scale, scale)))[:h, :w]
    a = np.clip(128 + n * amp, 0, 255).astype(np.uint8)
    img = np.dstack([a, a, a, np.full_like(a, 255)])
    return to_image(img)

@functools.lru_cache(None)
def base_background(tint=None, vignette=0.55):
    """Deep ink-green background with paper grain + vignette, as skia.Image."""
    t0 = np.array(tint[0] if tint else BG0, float)
    t1 = np.array(tint[1] if tint else BG1, float)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # soft centre light
    cx, cy = W * 0.5, H * 0.40
    d = np.sqrt(((xx - cx) / (W * 0.9)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    m = np.clip(1.0 - d, 0, 1) ** 1.3
    img = t0[None, None, :] * (1 - m[..., None]) + t1[None, None, :] * m[..., None]
    # large-scale mottling
    rng = np.random.default_rng(11)
    low = rng.normal(0, 1, (H // 120 + 2, W // 120 + 2))
    from numpy import kron
    low = kron(low, np.ones((120, 120)))[:H, :W]
    # cheap blur of the blocks
    for _ in range(3):
        low = (np.roll(low, 40, 0) + np.roll(low, -40, 0) + np.roll(low, 40, 1) + np.roll(low, -40, 1) + low) / 5
    img += low[..., None] * 3.0
    # grain
    img += rng.normal(0, 3.2, (H, W))[..., None]
    # vignette
    dv = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.62)) ** 2)
    v = 1 - vignette * np.clip(dv - 0.35, 0, 1) ** 1.5
    img *= v[..., None]
    img = np.clip(img, 0, 255)
    out = np.dstack([img.astype(np.uint8), np.full((H, W), 255, np.uint8)])
    return to_image(out)

def draw_bg(c, tint=None):
    c.drawImage(base_background(tint), 0, 0)

# ---------------------------------------------------------------- common overlays
def chapter_label(c, text, alpha=1.0, sub=None):
    if alpha <= 0:
        return
    draw_text(c, text, W / 2, TOP_LABEL_Y, "serif_sb", 38, GOLD, alpha, align="center", tracking=0.18)
    w = text_width(text, "serif_sb", 38, 0.18)
    p = paint(GOLD_DIM, alpha * 0.9, stroke=1.6)
    c.drawLine(W / 2 - w / 2 - 70, TOP_LABEL_Y - 13, W / 2 - w / 2 - 18, TOP_LABEL_Y - 13, p)
    c.drawLine(W / 2 + w / 2 + 18, TOP_LABEL_Y - 13, W / 2 + w / 2 + 70, TOP_LABEL_Y - 13, p)
    if sub:
        draw_text(c, sub, W / 2, TOP_LABEL_Y + 44, "sans", 24, MUTED, alpha * 0.9, align="center", tracking=0.05)

def tag_badge(c, text, alpha=1.0, y=None):
    """Small badge e.g. 对照例子 / 韦伯原文提到的例子 / 情景示意"""
    if alpha <= 0 or not text:
        return
    y = y or (TOP_LABEL_Y + 62)
    size = 22
    w = text_width(text, "sans", size) + 30
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(W / 2 - w / 2, y - 26, w, 38), 19, 19)
    c.drawRRect(r, paint(GOLD_DIM, alpha * 0.9, stroke=1.4))
    draw_text(c, text, W / 2, y + 1, "sans", size, GOLD, alpha * 0.95, align="center")

@functools.lru_cache(2048)
def balanced_wrap(text, fname, size, maxw):
    lines = wrap_cjk(text, fname, size, maxw)
    if len(lines) < 2:
        return lines
    n = len(lines)
    lo, hi = maxw * 0.4, maxw
    for _ in range(14):
        mid = (lo + hi) / 2
        if len(wrap_cjk(text, fname, size, mid)) <= n:
            hi = mid
        else:
            lo = mid
    return wrap_cjk(text, fname, size, hi + 1)

def subtitle(c, text, alpha=1.0, y=SUB_Y, size=50, color=IVORY, maxw=940):
    if alpha <= 0 or not text:
        return
    lines = balanced_wrap(text, "sans_m", size, maxw)
    lh = size * 1.42
    y0 = y - (len(lines) - 1) * lh / 2 + size * 0.36
    for i, ln in enumerate(lines):
        draw_text(c, ln, W / 2, y0 + i * lh, "sans_m", size, color, alpha, align="center", shadow=6)

def quote_card(c, de, zh, cx, cy, alpha=1.0, de_size=40, zh_size=34, maxw=900, de_color=GOLD_HI,
               zh_color=IVORY, italic=True):
    """German/Latin line in serif, plain Chinese right under it."""
    if alpha <= 0:
        return
    fname = "garamond_i" if italic else "garamond"
    lines = wrap_cjk(de, fname, de_size, maxw)
    lh = de_size * 1.3
    y = cy
    for ln in lines:
        draw_text(c, ln, cx, y, fname, de_size, de_color, alpha, align="center")
        y += lh
    y += zh_size * 0.35
    zl = wrap_cjk(zh, "serif", zh_size, maxw)
    for ln in zl:
        draw_text(c, ln, cx, y + zh_size * 0.2, "serif", zh_size, zh_color, alpha * 0.95, align="center")
        y += zh_size * 1.45
    return y

def new_surface():
    info = skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    return skia.Surface.MakeRaster(info)

def surface_to_rgb(surf):
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    return arr[..., :3]

def footnote(c, text, alpha=1.0, y=1515):
    if alpha <= 0 or not text:
        return
    lines = balanced_wrap(text, "sans", 22, 900)
    for i, ln in enumerate(lines):
        draw_text(c, ln, W / 2, y + i * 32, "sans", 22, MUTED, alpha * 0.75, align="center")

def smooth_noise(h, w, cells, seed):
    import PIL.Image as PI
    rng = np.random.default_rng(seed)
    small = rng.random((max(2, h // cells), max(2, w // cells))).astype(np.float32)
    im = PI.fromarray((small * 255).astype(np.uint8)).resize((w, h), PI.BICUBIC)
    return np.asarray(im, np.float32) / 255.0

def fbm(h, w, seed, octaves=5, base=400):
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        acc += amp * smooth_noise(h, w, max(4, base >> o), seed + o * 17)
        tot += amp; amp *= 0.5
    return acc / tot

@functools.lru_cache(None)
def marble_image(w=W, h=H, seed=5, base_col=(17, 44, 37), vein_col=(170, 186, 168), dark=0.0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = fbm(h, w, seed, 6, 700)
    t3 = fbm(h, w, seed + 7, 5, 300)
    phase = (xx * 0.0016 + yy * 0.0024) * 2 * np.pi + t * 11.0 + t3 * 3.0
    v = np.abs(np.sin(phase))
    veins = np.clip(1 - v / 0.035, 0, 1) ** 1.4 * 0.9 + np.clip(1 - v / 0.22, 0, 1) ** 2 * 0.25
    # break veins up so they fade in and out
    mask = np.clip((fbm(h, w, seed + 3, 4, 500) - 0.38) * 3.0, 0, 1)
    veins *= mask
    t2 = fbm(h, w, seed + 99, 6, 400)
    base = np.array(base_col, np.float32)[None, None, :] * (0.70 + 0.6 * t2[..., None])
    img = base * (1 - veins[..., None] * 0.5) + np.array(vein_col, np.float32)[None, None, :] * veins[..., None] * 0.42
    img *= (1 - dark)
    rng = np.random.default_rng(seed)
    img += rng.normal(0, 2.5, (h, w))[..., None]
    out = np.dstack([np.clip(img, 0, 255).astype(np.uint8), np.full((h, w), 255, np.uint8)])
    return to_image(out)

def vignette(c, cx=W / 2, cy=800, r=1150, strength=170):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(center=(cx, cy), radius=r,
                colors=[C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, strength)], positions=[0.0, 0.45, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)

def dash_trim(on, off, frac):
    d = skia.DashPathEffect.Make([on, off], 0)
    if frac >= 0.999:
        return d
    t = skia.TrimPathEffect.Make(0, max(0.0005, clamp(frac)))
    return skia.PathEffect.MakeCompose(d, t)

def split_sub(text, maxlen=17):
    """Split a narration line into subtitle chunks at punctuation; strip trailing ，。"""
    import re
    parts = re.split(r"(?<=[。！？；])", text)
    chunks = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= maxlen:
            chunks.append(p); continue
        sub = re.split(r"(?<=[，、：——])", p)
        cur = ""
        for q in sub:
            if not q:
                continue
            if len(cur) + len(q) <= maxlen or not cur:
                cur += q
            else:
                chunks.append(cur); cur = q
        if cur:
            chunks.append(cur)
    # merge very short tails
    out = []
    for ch in chunks:
        if out and len(ch) <= 4 and len(out[-1]) + len(ch) <= maxlen + 4:
            out[-1] += ch
        else:
            out.append(ch)
    return [o.rstrip("，。；、") if not o.endswith("……") else o for o in out]
