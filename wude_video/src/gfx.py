"""Drawing primitives, fonts, palettes and textures (skia)."""
import math
import functools
import numpy as np
import skia

W, H = 1080, 1920
FPS = 30

# ---------------------------------------------------------------- fonts
NOTO = "/usr/share/fonts/opentype/noto"
SC, TC = 2, 3


@functools.lru_cache(maxsize=None)
def typeface(kind="serif", weight="Bold", script=SC):
    fam = "NotoSerifCJK" if kind == "serif" else "NotoSansCJK"
    return skia.Typeface.MakeFromFile(f"{NOTO}/{fam}-{weight}.ttc", script)


@functools.lru_cache(maxsize=None)
def font(kind="serif", weight="Bold", size=48, script=SC):
    f = skia.Font(typeface(kind, weight, script), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


# ---------------------------------------------------------------- colours
def hexc(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255, g / 255, b / 255, a)


def c4(c, a=None):
    r, g, b, aa = c
    return skia.Color4f(r, g, b, aa if a is None else a)


def mix(c1, c2, t):
    return tuple(c1[i] * (1 - t) + c2[i] * t for i in range(4))


def with_alpha(c, a):
    return (c[0], c[1], c[2], c[3] * a)


# 五德五色
DE_COLOR = {
    "土": hexc("#C99A2E"),
    "木": hexc("#2E7A68"),
    "金": hexc("#DCD5C6"),
    "火": hexc("#B5302A"),
    "水": hexc("#17181D"),
}
DE_INK = {  # glyph colour on top of each sector
    "土": hexc("#2A1C08"), "木": hexc("#F2EAD8"), "金": hexc("#2A241C"),
    "火": hexc("#FBEFD9"), "水": hexc("#E9DFC9"),
}
BRONZE = hexc("#A9834C")
CINNABAR = hexc("#B23A26")
INK = hexc("#1E1A15")
SILK = hexc("#EBDFC4")

THEMES = {
    #           top        bottom     paper  text(sub)   quote      accent     dark?
    "void":       ("#0B0A09", "#16120E", 0.25, "#EFE6D2", "#D8B677", "#B08D57", True),
    "silk":       ("#ECE0C6", "#D8C59E", 1.00, "#1F1A14", "#7A2E1E", "#9A3A26", False),
    "qin":        ("#0D0E11", "#1C1812", 0.22, "#F1E8D6", "#CDA86C", "#A9834C", True),
    "hanchu":     ("#130C0B", "#2B100D", 0.22, "#F4E8D8", "#E2A472", "#C0392B", True),
    "taichu_pre": ("#1A140B", "#30230F", 0.25, "#F3E9D6", "#E3BE6A", "#C99A2E", True),
    "taichu":     ("#DDB865", "#B98C36", 0.85, "#22170A", "#5E2410", "#7A3B10", False),
    "xihan":      ("#962E1F", "#661A12", 0.40, "#FBF1E0", "#FFD79A", "#F2C46A", True),
    "donghan":    ("#A8341F", "#7A2214", 0.40, "#FBF1E0", "#FFD79A", "#F2C46A", True),
    "ending":     ("#0F0F0F", "#1B1713", 0.25, "#EFE6D2", "#D8B677", "#B08D57", True),
}


def theme(name):
    t = THEMES[name]
    return dict(name=name, top=hexc(t[0]), bottom=hexc(t[1]), paper=t[2], sub=hexc(t[3]),
                quote=hexc(t[4]), accent=hexc(t[5]), dark=t[6])


def blend_theme(a, b, k):
    if k <= 0:
        return a
    if k >= 1:
        return b
    out = dict(a)
    for key in ("top", "bottom", "sub", "quote", "accent"):
        out[key] = mix(a[key], b[key], k)
    out["paper"] = a["paper"] * (1 - k) + b["paper"] * k
    out["dark"] = a["dark"] if k < 0.5 else b["dark"]
    out["name"] = a["name"] if k < 0.5 else b["name"]
    return out


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def ramp(t, t0, dur):
    return clamp((t - t0) / dur) if dur > 0 else (1.0 if t >= t0 else 0.0)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- paint helpers
def paint(color, style="fill", width=1.0, alpha=None, blur=0.0, cap="round", join="round", blend=None):
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setColor4f(c4(color, alpha if alpha is None else color[3] * alpha))
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin({"round": skia.Paint.kRound_Join, "miter": skia.Paint.kMiter_Join,
                         "bevel": skia.Paint.kBevel_Join}[join])
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend:
        p.setBlendMode(getattr(skia.BlendMode, blend))
    return p


def text_width(s, f):
    return f.measureText(s)


def draw_text(cv, s, x, y, f, color, align="left", alpha=1.0, shadow=None, spacing=0.0):
    """Draw single-line text. y is the baseline. spacing = extra px between chars."""
    if alpha <= 0.002 or not s:
        return
    if spacing:
        widths = [f.measureText(ch) for ch in s]
        total = sum(widths) + spacing * (len(s) - 1)
    else:
        total = f.measureText(s)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    if shadow:
        sc, sb, (dx, dy) = shadow
        sp = paint(sc, alpha=alpha, blur=sb)
        _draw_str(cv, s, x + dx, y + dy, f, sp, spacing)
    _draw_str(cv, s, x, y, f, paint(color, alpha=alpha), spacing)


def _draw_str(cv, s, x, y, f, p, spacing):
    if not spacing:
        cv.drawString(s, x, y, f, p)
        return
    for ch in s:
        cv.drawString(ch, x, y, f, p)
        x += f.measureText(ch) + spacing


def draw_vtext(cv, s, x, y, f, color, step=None, alpha=1.0, reveal=None, glow=None):
    """Vertical text; (x, y) = centre-x and top. reveal = number of chars (float)."""
    size = f.getSize()
    step = step or size * 1.12
    n = len(s)
    for i, ch in enumerate(s):
        a = alpha
        sc = 1.0
        if reveal is not None:
            k = clamp(reveal - i)
            if k <= 0:
                continue
            a = alpha * ease(k)
            sc = 1.0 + 0.18 * (1 - ease_out(k))
        w = f.measureText(ch)
        cy = y + i * step + size * 0.88
        cv.save()
        cv.translate(x, cy - size * 0.38)
        cv.scale(sc, sc)
        if glow:
            cv.drawString(ch, -w / 2, size * 0.38, f, paint(glow, alpha=a * 0.8, blur=size * 0.12))
        cv.drawString(ch, -w / 2, size * 0.38, f, paint(color, alpha=a))
        cv.restore()


def wrap_cjk(s, max_chars):
    """Break CJK text into rows (prefer breaking after punctuation)."""
    rows, cur = [], ""
    punct = "，。；：？！、,.;:?!」”）)"
    for ch in s:
        cur += ch
        if len(cur) >= max_chars:
            # try to break at the last punctuation within the row
            cut = -1
            for i in range(len(cur) - 1, max(0, len(cur) - 7), -1):
                if cur[i] in punct:
                    cut = i
                    break
            if cut >= 0 and cut < len(cur) - 1:
                rows.append(cur[:cut + 1])
                cur = cur[cut + 1:]
            else:
                rows.append(cur)
                cur = ""
    if cur:
        rows.append(cur)
    # avoid a row that starts with punctuation
    for i in range(1, len(rows)):
        while rows[i] and rows[i][0] in punct:
            rows[i - 1] += rows[i][0]
            rows[i] = rows[i][1:]
    return [r for r in rows if r]


# ---------------------------------------------------------------- svg-ish path parser
def path_from(d, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    """Tiny SVG path parser: M L H V C Q Z (absolute & relative)."""
    import re
    toks = re.findall(r"[MLHVCQZmlhvcqz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    p = skia.Path()
    i, cmd = 0, None
    x = y = 0.0
    sx0 = sy0 = 0.0

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def T(px, py):
        return px * sx + ox, py * sy + oy

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in "Zz":
                p.close(); x, y = sx0, sy0
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            nx, ny = num(), num()
            if rel: nx += x; ny += y
            x, y = nx, ny; sx0, sy0 = x, y
            p.moveTo(*T(x, y)); cmd = "l" if rel else "L"
        elif c == "L":
            nx, ny = num(), num()
            if rel: nx += x; ny += y
            x, y = nx, ny; p.lineTo(*T(x, y))
        elif c == "H":
            nx = num(); x = x + nx if rel else nx; p.lineTo(*T(x, y))
        elif c == "V":
            ny = num(); y = y + ny if rel else ny; p.lineTo(*T(x, y))
        elif c == "C":
            a = [num() for _ in range(6)]
            if rel: a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y, a[4] + x, a[5] + y]
            p.cubicTo(*T(a[0], a[1]), *T(a[2], a[3]), *T(a[4], a[5])); x, y = a[4], a[5]
        elif c == "Q":
            a = [num() for _ in range(4)]
            if rel: a = [a[0] + x, a[1] + y, a[2] + x, a[3] + y]
            p.quadTo(*T(a[0], a[1]), *T(a[2], a[3])); x, y = a[2], a[3]
    return p


def partial_path(path, frac):
    """Return the first `frac` of a path's length (all contours)."""
    if frac >= 0.999:
        return path
    out = skia.Path()
    if frac <= 0:
        return out
    pm = skia.PathMeasure(path, False)
    lens = []
    while True:
        lens.append(pm.getLength())
        if not pm.nextContour():
            break
    total = sum(lens)
    target = total * frac
    pm = skia.PathMeasure(path, False)
    acc = 0.0
    for L in lens:
        if acc + L <= target:
            pm.getSegment(0, L, out, True)
        else:
            pm.getSegment(0, max(0.0, target - acc), out, True)
            break
        acc += L
        if not pm.nextContour():
            break
    return out


# ---------------------------------------------------------------- textures
def _value_noise(h, w, cell, rng):
    gh, gw = h // cell + 3, w // cell + 3
    g = rng.random((gh, gw)).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) / cell
    xs = np.arange(w, dtype=np.float32) / cell
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = ys - y0; fx = xs - x0
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    top = a * (1 - fx) + b * fx
    bot = c * (1 - fx) + d * fx
    return top * (1 - fy[:, None]) + bot * fy[:, None]


def fbm(h, w, base_cell=256, octaves=5, seed=1):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, cell = 1.0, 0.0, base_cell
    for _ in range(octaves):
        out += amp * _value_noise(h, w, max(2, int(cell)), rng)
        tot += amp
        amp *= 0.5
        cell /= 2
    return out / tot


@functools.lru_cache(maxsize=None)
def paper_texture(seed=7):
    """Grayscale multiplier around 1.0 (H x W float32): mottling + fibres + specks."""
    rng = np.random.default_rng(seed)
    n = fbm(H, W, 420, 6, seed) - 0.5
    fine = fbm(H, W, 18, 2, seed + 1) - 0.5
    tex = 1.0 + 0.10 * n + 0.035 * fine
    # fibres: draw with skia onto a gray surface
    s = skia.Surface(W, H)
    cv = s.getCanvas()
    cv.clear(skia.Color4f(0.5, 0.5, 0.5, 1))
    for _ in range(900):
        x, y = rng.random() * W, rng.random() * H
        L = 20 + rng.random() * 120
        ang = rng.normal(0, 0.9)
        p = skia.Path()
        p.moveTo(x, y)
        p.quadTo(x + L * 0.5 * math.cos(ang) + rng.normal(0, 8), y + L * 0.5 * math.sin(ang) + rng.normal(0, 8),
                 x + L * math.cos(ang), y + L * math.sin(ang))
        v = 0.5 + (0.08 if rng.random() < 0.5 else -0.07)
        cv.drawPath(p, paint((v, v, v, 0.55), "stroke", 0.6 + rng.random() * 1.0))
    for _ in range(2500):
        x, y = rng.random() * W, rng.random() * H
        v = 0.5 - 0.15 * rng.random()
        cv.drawCircle(x, y, 0.4 + rng.random() * 1.1, paint((v, v, v, 0.5)))
    fib = s.makeImageSnapshot().toarray()[..., 0].astype(np.float32) / 255.0 - 0.5
    tex += fib * 0.6
    return np.clip(tex, 0.75, 1.25).astype(np.float32)


@functools.lru_cache(maxsize=None)
def vignette(strength=0.55):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx - W / 2) / (W * 0.62)
    dy = (yy - H * 0.47) / (H * 0.62)
    r = np.sqrt(dx * dx + dy * dy)
    return np.clip(1.0 - strength * np.clip(r - 0.35, 0, None) ** 1.6, 0.25, 1.0).astype(np.float32)


@functools.lru_cache(maxsize=8)
def background_image(theme_key):
    """theme_key: tuple(top, bottom, paper, dark) -> skia.Image"""
    top, bottom, paper_amt, dark = theme_key
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.array(top[:3], np.float32)[None, None, :]
    bottom = np.array(bottom[:3], np.float32)[None, None, :]
    base = top * (1 - yy) + bottom * yy
    tex = paper_texture()
    m = 1.0 + (tex - 1.0) * paper_amt
    img = base * m[..., None]
    v = vignette(0.65 if dark else 0.42)
    img = img * v[..., None]
    rgba = np.empty((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(img * 255, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)


def theme_key(th):
    q = lambda c: tuple(round(v, 3) for v in c)
    return (q(th["top"]), q(th["bottom"]), round(th["paper"], 3), th["dark"])


@functools.lru_cache(maxsize=None)
def erosion_mask(w, h, seed=3, amount=0.5):
    n = fbm(h, w, 6, 3, seed)
    n2 = fbm(h, w, 40, 3, seed + 5)
    m = np.clip((n * 0.7 + n2 * 0.3 - (0.18 + 0.2 * amount)) * 6, 0, 1)
    return m.astype(np.float32)


@functools.lru_cache(maxsize=256)
def stone_text_image(s, kind, weight, size, color, seed=3, amount=0.5, script=SC, vertical=False):
    """Text rendered with a worn 'stone/rubbing' edge, returned as skia.Image + offsets."""
    f = font(kind, weight, size, script)
    if vertical:
        wpx = int(size * 1.4)
        hpx = int(size * 1.12 * len(s) + size * 0.6)
    else:
        wpx = int(f.measureText(s) + size * 0.6)
        hpx = int(size * 1.5)
    surf = skia.Surface(wpx, hpx)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(0, 0, 0, 0))
    if vertical:
        draw_vtext(cv, s, wpx / 2, size * 0.1, f, (1, 1, 1, 1))
    else:
        cv.drawString(s, size * 0.3, size * 1.12, f, paint((1, 1, 1, 1)))
    a = surf.makeImageSnapshot().toarray()[..., 3].astype(np.float32) / 255.0
    em = erosion_mask(wpx, hpx, seed, amount)
    # erode mostly near edges: blur alpha to find interior
    from scipy.ndimage import gaussian_filter
    inner = gaussian_filter(a, size * 0.035)
    keep = np.clip(em + (inner - 0.55) * 2.2, 0, 1)
    alpha = a * np.clip(keep * 1.4, 0, 1)
    rgba = np.zeros((hpx, wpx, 4), np.uint8)
    rgba[..., 0] = int(color[0] * 255); rgba[..., 1] = int(color[1] * 255); rgba[..., 2] = int(color[2] * 255)
    rgba[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType,
                               alphaType=skia.kUnpremul_AlphaType)
    return img


def draw_image(cv, img, x, y, alpha=1.0, scale=1.0, center=False):
    p = skia.Paint()
    p.setAlphaf(clamp(alpha))
    p.setAntiAlias(True)
    w, h = img.width() * scale, img.height() * scale
    if center:
        x -= w / 2
        y -= h / 2
    cv.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear), p)


# ---------------------------------------------------------------- common objects
def bamboo_slip(cv, x, y, w, h, alpha=1.0, seed=0, tint=None, cords=True):
    """Bamboo slip with top-left at (x, y)."""
    rng = np.random.default_rng(seed)
    base1 = tint[0] if tint else hexc("#D0AC6E")
    base2 = tint[1] if tint else hexc("#AF8A50")
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), w * 0.08, w * 0.08)
    # shadow
    cv.drawRRect(r.makeOffset(6, 10) if hasattr(r, "makeOffset") else r,
                 paint((0, 0, 0, 0.45), alpha=alpha, blur=10))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(x, y), skia.Point(x + w, y)],
        [c4(base2, alpha), c4(base1, alpha), c4(base1, alpha), c4(base2, alpha)],
        [0.0, 0.35, 0.7, 1.0]))
    cv.drawRRect(r, p)
    cv.save()
    cv.clipRRect(r, doAntiAlias=True)
    for i in range(int(w / 5)):
        fx = x + rng.random() * w
        a = 0.06 + 0.08 * rng.random()
        cv.drawLine(fx, y, fx + rng.normal(0, 1.5), y + h, paint((0.35, 0.22, 0.08, a), "stroke", 1.0, alpha=alpha))
    # bamboo node
    for k in range(2):
        ny = y + h * (0.18 + 0.62 * k) + rng.normal(0, 8)
        cv.drawLine(x, ny, x + w, ny + 2, paint((0.3, 0.18, 0.06, 0.25), "stroke", 3, alpha=alpha))
    cv.restore()
    if cords:
        for k in (0.25, 0.75):
            cy = y + h * k
            cv.drawRect(skia.Rect.MakeXYWH(x - 4, cy - 5, w + 8, 10), paint(hexc("#3B2A1A"), alpha=alpha * 0.9))
            cv.drawLine(x - 4, cy - 1, x + w + 4, cy + 1, paint(hexc("#6B5236"), "stroke", 1.5, alpha=alpha * 0.8))


def seal(cv, cx, cy, size, text, color=CINNABAR, alpha=1.0, rot=0.0, text_color=(0.98, 0.94, 0.86, 1),
         seed=1, vertical=True, square=True):
    """Square vermilion seal with text (white, vertical columns right-to-left)."""
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(rot)
    r = skia.Rect.MakeXYWH(-size / 2, -size / 2, size, size)
    rr = skia.RRect.MakeRectXY(r, size * 0.06, size * 0.06)
    cv.drawRRect(rr, paint(color, alpha=alpha))
    cv.drawRRect(rr, paint(text_color, "stroke", max(2, size * 0.035), alpha=alpha * 0.85))
    n = len(text)
    if n:
        if n <= 2:
            fs = size * (0.62 if n == 1 else 0.42)
            f = font("serif", "Black", fs)
            if n == 1:
                draw_text(cv, text, 0, fs * 0.36, f, text_color, "center", alpha)
            else:
                draw_vtext(cv, text, 0, -size * 0.43, f, text_color, step=fs * 1.02, alpha=alpha)
        else:
            cols = 2
            per = math.ceil(n / cols)
            fs = size * 0.36 if per <= 2 else size * 0.27
            f = font("serif", "Black", fs)
            for ci in range(cols):
                chunk = text[ci * per:(ci + 1) * per]
                xx = size * 0.22 - ci * size * 0.44
                draw_vtext(cv, chunk, xx, -size * 0.45, f, text_color, step=fs * 1.05, alpha=alpha)
    cv.restore()


def ink_splat(cv, cx, cy, r, color, alpha, seed=0, k=1.0):
    rng = np.random.default_rng(seed)
    for i in range(24):
        ang = rng.random() * math.tau
        d = r * (0.2 + 1.2 * rng.random()) * k
        rr = r * (0.05 + 0.15 * rng.random()) * (1.2 - 0.4 * k)
        cv.drawCircle(cx + d * math.cos(ang), cy + d * math.sin(ang), rr,
                      paint(color, alpha=alpha * (1 - 0.5 * k)))


def cloud_swirl(cv, cx, cy, s, color, alpha=1.0, width=3.0, flip=False, frac=1.0):
    """Han-style 云气纹 curl."""
    p = skia.Path()
    n = 60
    pts = []
    for i in range(n + 1):
        t = i / n
        ang = t * math.pi * 2.6
        rad = s * (0.12 + 0.88 * (1 - t) ** 1.2) * 0.5
        x = cx + (rad * math.cos(ang)) * (-1 if flip else 1)
        y = cy - rad * math.sin(ang)
        pts.append((x, y))
    tail = [(cx + (s * 0.5 + s * 1.1 * u) * (-1 if flip else 1), cy - s * 0.02 + s * 0.25 * math.sin(u * 3)) for u in np.linspace(0, 1, 20)]
    allp = tail[::-1] + pts
    p.moveTo(*allp[0])
    for q in allp[1:]:
        p.lineTo(*q)
    pp = partial_path(p, frac)
    cv.drawPath(pp, paint(color, "stroke", width, alpha=alpha))


def han_figure(cv, x, y, h, color, alpha=1.0, pose="stand", facing=1):
    """汉画像石风格剪影. (x, y) = feet centre, h = height."""
    s = h / 400.0
    cv.save()
    cv.translate(x, y)
    cv.scale(s * facing, s)
    cv.translate(0, -400)
    p = paint(color, alpha=alpha)
    # robe: bell shape
    robe = path_from("M -18 120 C -40 170 -60 300 -78 392 L 70 392 C 62 300 40 170 26 120 Z")
    cv.drawPath(robe, p)
    # head + cap
    cv.drawCircle(4, 92, 26, p)
    if pose in ("stand", "scholar", "bow_broom"):
        cap = path_from("M -14 72 L 6 18 L 22 24 L 14 70 Z")  # 进贤冠 slanted
        cv.drawPath(cap, p)
    if pose == "king":
        cap = path_from("M -22 68 L -26 50 L 34 46 L 30 66 Z M -40 50 L 48 44 L 48 52 L -40 58 Z")
        cv.drawPath(cap, p)
    # neck/shoulders
    cv.drawPath(path_from("M -20 110 C -10 122 18 122 30 110 L 32 132 L -24 134 Z"), p)
    if pose in ("stand", "scholar", "king"):
        # large sleeve hanging in front
        cv.drawPath(path_from("M 10 135 C 60 150 74 210 64 260 C 50 268 30 262 22 250 C 30 210 20 170 4 150 Z"), p)
    elif pose == "bow_broom":
        # leaning forward, arms extended holding a broom
        cv.drawPath(path_from("M 10 135 C 50 150 80 170 104 196 L 96 210 C 70 192 40 176 8 166 Z"), p)
        broom = paint(color, "stroke", 7, alpha=alpha)
        cv.drawLine(70, 150, 190, 370, broom)
        for k in range(-4, 5):
            cv.drawLine(186, 362, 186 + k * 9, 400, paint(color, "stroke", 3.5, alpha=alpha))
    elif pose == "kneel":
        pass
    cv.restore()


def kneeling_figure(cv, x, y, h, color, alpha=1.0, facing=1):
    s = h / 260.0
    cv.save()
    cv.translate(x, y)
    cv.scale(s * facing, s)
    cv.translate(0, -260)
    p = paint(color, alpha=alpha)
    cv.drawPath(path_from("M -60 258 C -66 200 -40 140 -10 112 L 30 112 C 52 150 70 210 80 258 Z"), p)
    cv.drawCircle(18, 84, 24, p)  # head bowed forward
    cv.drawPath(path_from("M 0 64 C 20 40 46 52 44 70 Z"), p)  # hair bun
    cv.drawPath(path_from("M 26 120 C 60 140 70 170 52 196 C 40 190 34 170 20 150 Z"), p)  # sleeve to face
    cv.restore()


def horse(cv, x, y, s, color, alpha=1.0):
    """Stylised galloping Han horse; (x,y) = hoof line centre."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s / 100.0, s / 100.0)
    p = paint(color, alpha=alpha)
    body = path_from(
        "M -40 -46 C -20 -58 22 -58 38 -48 C 46 -60 54 -78 66 -84 C 74 -86 80 -82 82 -76 "
        "L 70 -66 C 66 -58 62 -48 58 -40 C 56 -30 50 -26 44 -24 L 58 -4 L 52 0 L 34 -22 "
        "L 12 -22 L -6 -2 L -12 -4 L 0 -24 C -14 -26 -24 -28 -32 -30 L -52 -8 L -58 -12 "
        "L -44 -34 C -54 -36 -64 -46 -70 -60 C -62 -56 -52 -50 -40 -46 Z")
    cv.drawPath(body, p)
    cv.restore()
