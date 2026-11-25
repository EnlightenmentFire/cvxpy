"""Drawing engine (skia) for ep.66 Odawara / katanagari (adapted from the ep.34 engine): fonts, text, map camera, arrows, markers, cards."""
import math, json, os, functools
import numpy as np, skia
from geo import View, CITY, merc
W, H = 1080, 1920
FPS = 25
WORK = "/tmp/claude-0/work"
NOTO = "/usr/share/fonts/opentype/noto/"
def _tf(f, i): return skia.Typeface.MakeFromFile(NOTO + f, i)
SANS = _tf("NotoSansCJK-Bold.ttc", 2); SANS_M = _tf("NotoSansCJK-Medium.ttc", 2); SANS_BK = _tf("NotoSansCJK-Black.ttc", 2)
SERIF = _tf("NotoSerifCJK-Bold.ttc", 2); SERIF_BK = _tf("NotoSerifCJK-Black.ttc", 2)
SERIF_TC = _tf("NotoSerifCJK-Bold.ttc", 3); SERIF_TC_BK = _tf("NotoSerifCJK-Black.ttc", 3)

GOLD = (224, 176, 70); GOLD_D = (150, 108, 30); INK = (20, 16, 12)
CYAN = (96, 164, 230); CYAN_D = (34, 80, 130); WHITE = (245, 240, 228); RED = (222, 64, 40)
PAPER = (232, 220, 192)

def col(c, a=1.0):
    return skia.Color4f(c[0] / 255, c[1] / 255, c[2] / 255, max(0.0, min(1.0, a)))
def paint(c=WHITE, a=1.0, stroke=None, blur=None, aa=True, cap=None, join=None):
    p = skia.Paint(AntiAlias=aa); p.setColor4f(col(c, a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap); p.setStrokeJoin(join or skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ein(x): x = clamp(x); return x ** 3
def lerp(a, b, t): return a + (b - a) * t
def fade(t, T, fi=0.4, fo=0.4):
    a = 1.0
    if fi > 0: a = min(a, clamp(t / fi))
    if fo > 0: a = min(a, clamp((T - t) / fo))
    return a

@functools.lru_cache(maxsize=256)
def font(tf_name, size):
    return skia.Font({"sans": SANS, "sansm": SANS_M, "sansbk": SANS_BK, "serif": SERIF, "serifbk": SERIF_BK,
                      "tc": SERIF_TC, "tcbk": SERIF_TC_BK}[tf_name], size)

def text_w(s, f): return f.measureText(s)

def text(c, s, x, y, size=48, face="sans", color=WHITE, a=1.0, align="c", stroke=0, stroke_c=INK, stroke_a=0.85,
         shadow=0, spacing=0):
    if a <= 0.003 or not s: return
    f = font(face, size)
    if spacing:
        widths = [f.measureText(ch) for ch in s]; tw = sum(widths) + spacing * (len(s) - 1)
    else:
        tw = f.measureText(s)
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
    def draw(p):
        if spacing:
            xx = x0
            for ch, wch in zip(s, widths):
                c.drawString(ch, xx, y, f, p); xx += wch + spacing
        else:
            c.drawString(s, x0, y, f, p)
    if shadow:
        draw(paint(INK, a * 0.7, blur=shadow))
    if stroke:
        draw(paint(stroke_c, a * stroke_a, stroke=stroke))
    draw(paint(color, a))
    return tw

def vtext(c, s, x, y, size, face="tc", color=WHITE, a=1.0, lh=1.08, stroke=0):
    """Vertical text, one column, top at y, centered on x."""
    f = font(face, size)
    for i, ch in enumerate(s):
        if ch in "，。、；：！？":
            text(c, ch, x + size * 0.36, y + i * size * lh + size * 0.42, size * 0.9, face, color, a, stroke=stroke)
        else:
            text(c, ch, x, y + (i + 0.88) * size * lh, size, face, color, a, stroke=stroke)

PUN = "，。、；：！？》」”）"
def wrap(s, n):
    """balanced wrap for subtitles: <=n per row, prefer breaks after punctuation, no row starts with punctuation"""
    if len(s) <= n: return [s]
    rows = math.ceil(len(s) / n)
    if rows == 2:
        mid = len(s) / 2; best, bs = None, 1e9
        for i in range(max(1, len(s) - n), min(n, len(s) - 1) + 1):
            if s[i] in PUN: continue
            sc = abs(i - mid) - (3.5 if s[i - 1] in PUN else 0)
            if sc < bs: bs, best = sc, i
        if best: return [s[:best], s[best:]]
    return _wrap_greedy(s, n)

def _wrap_greedy(s, n):
    out, cur = [], ""
    for ch in s:
        cur += ch
        if len(cur) >= n and ch not in "，。、；：！？》」”":
            out.append(cur); cur = ""
        elif len(cur) > n:
            out.append(cur); cur = ""
    if cur:
        if out and len(cur) <= 2: out[-1] += cur
        else: out.append(cur)
    return out

# ------------------------------------------------------------------ images
_IMG = {}
def image(path):
    if path not in _IMG:
        _IMG[path] = skia.Image.open(path)
    return _IMG[path]
def np_image(arr):
    arr = np.ascontiguousarray(arr)
    if arr.ndim == 2: arr = np.dstack([arr, arr, arr, np.full_like(arr, 255)])
    if arr.shape[2] == 3: arr = np.dstack([arr, np.full(arr.shape[:2], 255, np.uint8)])
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)

# ------------------------------------------------------------------ map camera
_V = {}
def view(name):
    if name not in _V: _V[name] = View(name)
    return _V[name]
CX, CY = W / 2, 880

class Cam:
    def __init__(self, vname, lon, lat, scale, rot=0.0):
        self.v = view(vname); self.lon, self.lat, self.s = lon, lat, scale
        self.cx, self.cy = self.v.px(lon, lat)
    def P(self, lon, lat):
        x, y = self.v.px(lon, lat)
        return CX + (x - self.cx) * self.s, CY + (y - self.cy) * self.s
    def city(self, name): return self.P(*CITY[name])

def cam_lerp(vname, k0, k1, t):
    """k = (lon, lat, scale); interpolate in pixel space, scale geometrically."""
    v = view(vname)
    x0, y0 = v.px(k0[0], k0[1]); x1, y1 = v.px(k1[0], k1[1])
    e = ease(t)
    s = math.exp(lerp(math.log(k0[2]), math.log(k1[2]), e))
    c = Cam(vname, k0[0], k0[1], s); c.cx = lerp(x0, x1, e); c.cy = lerp(y0, y1, e)
    return c

def draw_map(c, cam, dim=0.0, sat=1.0):
    v = cam.v; img = image(v.path)
    c.save()
    c.translate(CX, CY); c.scale(cam.s, cam.s); c.translate(-cam.cx, -cam.cy)
    p = skia.Paint(AntiAlias=True)
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
    c.restore()
    x0 = CX - cam.cx * cam.s; y0 = CY - cam.cy * cam.s; x1 = x0 + v.w * cam.s; y1 = y0 + v.h * cam.s
    F = 160
    def grad(ax, ay, bx, by, r):
        g = skia.Paint(); g.setShader(skia.GradientShader.MakeLinear([skia.Point(ax, ay), skia.Point(bx, by)], [col(INK, 1), col(INK, 0)]))
        c.drawRect(r, g)
    if y0 > -F: grad(0, y0, 0, y0 + F, skia.Rect(0, y0, W, y0 + F))
    if y1 < H + F: grad(0, y1, 0, y1 - F, skia.Rect(0, y1 - F, W, y1))
    if x0 > -F: grad(x0, 0, x0 + F, 0, skia.Rect(x0, 0, x0 + F, H))
    if x1 < W + F: grad(x1, 0, x1 - F, 0, skia.Rect(x1 - F, 0, x1, H))
    bg = paint(INK, 1)
    if y0 > 0: c.drawRect(skia.Rect(0, 0, W, y0 + 1), bg)
    if y1 < H: c.drawRect(skia.Rect(0, y1 - 1, W, H), bg)
    if x0 > 0: c.drawRect(skia.Rect(0, 0, x0 + 1, H), bg)
    if x1 < W: c.drawRect(skia.Rect(x1 - 1, 0, W, H), bg)
    if dim > 0: c.drawRect(skia.Rect(0, 0, W, H), paint(INK, dim))

# rivers (lon/lat polylines)
@functools.lru_cache(maxsize=1)
def rivers():
    d = json.load(open(f"{WORK}/geo/ne_10m_rivers_lake_centerlines.geojson"))
    want = {"Tone": 2.2, "Arakawa": 1.6, "Sagami": 1.6, "Fuji": 1.6, "Tama": 1.4, "Sakawa": 1.4, "Syr  Darya": 3.0, "Amu  Darya": 3.2, "Zarafshon": 2.0, "Indus": 3.2, "Panj": 2.4, "Naryn": 2.0,
            "Helmand": 1.8, "Harirud": 1.6, "Volga": 2.6, "Ural": 2.0, "Tigris": 2.0, "Euphrates": 2.0, "Ile": 1.6,
            "Kabul": 2.0, "Chu": 1.6, "Kura": 1.6, "Atrek": 1.4, "Kashkadarya": 1.4, "Yellow": 2.4, "Huang": 2.4,
            "Yangtze": 2.4, "Chang": 2.4, "Amur": 2.0, "Ob": 2.0, "Irtysh": 2.0, "Selenga": 1.6, "Orhon": 1.4, "Kerulen": 1.4}
    out = []
    for ft in d["features"]:
        nm = ft["properties"].get("name") or ""
        if nm in want:
            g = ft["geometry"]
            lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
            for ln in lines: out.append((nm, want[nm], np.array(ln)))
    return out

def draw_rivers(c, cam, a=1.0, width_k=1.0):
    if a <= 0: return
    v = cam.v
    for nm, wd, pts in rivers():
        # quick cull
        xs = []
        path = skia.Path(); first = True
        for lon, lat in pts[:: 1]:
            x, y = cam.P(lon, lat)
            if first: path.moveTo(x, y); first = False
            else: path.lineTo(x, y)
        b = path.getBounds()
        if b.right() < -50 or b.left() > W + 50 or b.bottom() < -50 or b.top() > H + 50: continue
        w = wd * width_k * max(0.6, min(2.2, cam.s * 1.2))
        c.drawPath(path, paint((70, 140, 170), 0.35 * a, stroke=w * 3, blur=4))
        c.drawPath(path, paint((120, 185, 205), 0.85 * a, stroke=w))

# ------------------------------------------------------------------ geometry helpers
def catmull(pts, n=16):
    pts = [np.array(p, float) for p in pts]
    if len(pts) < 3:
        a, b = pts[0], pts[-1]
        return [a + (b - a) * t for t in np.linspace(0, 1, n * 2)]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out

def partial(poly, prog):
    poly = np.array(poly); seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    L = seg.sum(); target = L * clamp(prog)
    cum = np.concatenate([[0], np.cumsum(seg)])
    k = np.searchsorted(cum, target) - 1; k = max(0, min(k, len(seg) - 1))
    r = (target - cum[k]) / (seg[k] + 1e-9)
    end = poly[k] + (poly[k + 1] - poly[k]) * r
    return np.vstack([poly[:k + 1], end]), L

def arrow(c, pts_screen, prog, w=34, color=GOLD, a=1.0, head=2.1, glow=True, flow_t=None, outline=True):
    """Fat tapered arrow along a smooth curve through screen points; prog in [0,1]."""
    if prog <= 0.001 or a <= 0: return
    poly = catmull(pts_screen, 20)
    part, L = partial(poly, prog)
    if len(part) < 2: return
    hl = min(w * head * 1.15, L * prog * 0.5)
    # trim body before head
    seg = np.linalg.norm(np.diff(part, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    tot = cum[-1]
    tip = part[-1]
    # direction at tip
    j = np.searchsorted(cum, tot - max(hl, 1)) ; j = max(0, min(j, len(part) - 2))
    base = part[j]; d = tip - base; d = d / (np.linalg.norm(d) + 1e-9); nrm = np.array([-d[1], d[0]])
    body = part[:j + 1]
    if len(body) < 2: body = np.vstack([part[0], base])
    bc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(body, axis=0), axis=1))])
    left, right = [], []
    for i, p in enumerate(body):
        if i < len(body) - 1: dd = body[i + 1] - p
        else: dd = p - body[i - 1]
        dd = dd / (np.linalg.norm(dd) + 1e-9); nn = np.array([-dd[1], dd[0]])
        u = bc[i] / (bc[-1] + 1e-9)
        ww = w * (0.38 + 0.62 * u) / 2
        left.append(p + nn * ww); right.append(p - nn * ww)
    hw = w * head / 2
    path = skia.Path(); path.moveTo(*left[0])
    for p in left[1:]: path.lineTo(*p)
    path.lineTo(*(base + nrm * hw)); path.lineTo(*tip); path.lineTo(*(base - nrm * hw))
    for p in right[::-1]: path.lineTo(*p)
    path.close()
    if glow:
        c.drawPath(path, paint(color, 0.45 * a, blur=w * 0.6))
    shader = skia.GradientShader.MakeLinear([skia.Point(*part[0]), skia.Point(*tip)],
                                           [col(tuple(int(v * 0.55) for v in color), a * 0.75), col(color, a)])
    p = skia.Paint(AntiAlias=True); p.setShader(shader); c.drawPath(path, p)
    if outline: c.drawPath(path, paint(INK, 0.75 * a, stroke=2.5))
    if flow_t is not None and len(body) > 3:
        # moving light streaks along the body
        cl = bc[-1]
        for k in range(3):
            pos = ((flow_t * 160 + k * cl / 3) % (cl + 1e-9))
            i = np.searchsorted(bc, pos); i = max(1, min(i, len(body) - 1))
            q = body[i]
            c.drawCircle(q[0], q[1], w * 0.18, paint((255, 236, 180), 0.55 * a, blur=4))
    return tip

def city_marker(c, x, y, name=None, state="lit", a=1.0, t=0.0, size=1.0, label_side="r", label_size=40, lab_a=None):
    if a <= 0: return
    r = 11 * size
    if state == "lit":
        pul = 0.5 + 0.5 * math.sin(t * 3.0)
        c.drawCircle(x, y, r * (2.6 + 0.6 * pul), paint(CYAN, 0.22 * a, blur=10))
        c.drawCircle(x, y, r, paint(CYAN, a)); c.drawCircle(x, y, r, paint(INK, 0.8 * a, stroke=2.5))
        c.drawCircle(x, y, r * 0.42, paint(WHITE, 0.9 * a))
    elif state == "siege":
        c.drawCircle(x, y, r * 2.6, paint(CYAN, 0.18 * a, blur=10))
        c.drawCircle(x, y, r, paint(CYAN, a)); c.drawCircle(x, y, r, paint(INK, 0.8 * a, stroke=2.5))
        p = paint(GOLD, 0.95 * a, stroke=4.5)
        p.setPathEffect(skia.DashPathEffect.Make([10, 9], t * 30))
        c.drawCircle(x, y, r * 2.4, p)
    elif state == "fallen":
        c.drawCircle(x, y, r * 2.0, paint((60, 40, 20), 0.35 * a, blur=10))
        c.drawCircle(x, y, r * 0.9, paint((70, 66, 60), a)); c.drawCircle(x, y, r * 0.9, paint(GOLD_D, 0.9 * a, stroke=3))
    elif state == "gold":
        c.drawCircle(x, y, r * 2.6, paint(GOLD, 0.25 * a, blur=10))
        c.drawCircle(x, y, r, paint(GOLD, a)); c.drawCircle(x, y, r, paint(INK, 0.8 * a, stroke=2.5))
    if name:
        la = a if lab_a is None else lab_a
        if label_side == "r": text(c, name, x + r + 14, y + label_size * 0.36, label_size, "sans", WHITE, la, "l", stroke=6)
        elif label_side == "l": text(c, name, x - r - 14, y + label_size * 0.36, label_size, "sans", WHITE, la, "r", stroke=6)
        elif label_side == "u": text(c, name, x, y - r - 16, label_size, "sans", WHITE, la, "c", stroke=6)
        else: text(c, name, x, y + r + label_size + 6, label_size, "sans", WHITE, la, "c", stroke=6)

def region_label(c, s, x, y, size=46, a=1.0, color=(220, 205, 170), spacing=14):
    text(c, s, x, y, size, "serif", color, a * 0.85, "c", stroke=5, stroke_a=0.6, spacing=spacing)

def flash(c, x, y, t, color=GOLD, R=120):
    """expanding ring flash, t in [0,1]"""
    if not 0 <= t <= 1: return
    c.drawCircle(x, y, R * eout(t), paint(color, 0.9 * (1 - t), stroke=6 * (1 - t) + 1))
    c.drawCircle(x, y, R * 0.5 * eout(t), paint(color, 0.35 * (1 - t), blur=14))

# ------------------------------------------------------------------ overlays
_GRAIN = None
def grain(c, fi, a=0.06):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7); _GRAIN = []
        for i in range(6):
            g = rng.normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
            _GRAIN.append(np_image(np.dstack([g, g, g, np.full_like(g, 255)])))
    p = skia.Paint(); p.setAlphaf(a); p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(_GRAIN[fi % 6], skia.Rect(0, 0, W, H), skia.SamplingOptions(), p)

def vignette(c, a=0.75):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.46), H * 0.72,
                [col(INK, 0), col(INK, 0.15 * a), col(INK, a)], [0.0, 0.55, 1.0]))
    c.drawRect(skia.Rect(0, 0, W, H), p)
    # top / bottom bands for text
    p2 = skia.Paint(); p2.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 330)], [col(INK, 0.85), col(INK, 0)]))
    c.drawRect(skia.Rect(0, 0, W, 330), p2)
    p3 = skia.Paint(); p3.setShader(skia.GradientShader.MakeLinear([skia.Point(0, H - 620), skia.Point(0, H)], [col(INK, 0), col(INK, 0.92)]))
    c.drawRect(skia.Rect(0, H - 620, W, H), p3)

def header(c, title, a=1.0, sub=None):
    text(c, "从无名小卒到天下人 · 终章", 64, 112, 34, "sansm", GOLD, a * 0.95, "l", spacing=4)
    c.drawRect(skia.Rect(64, 132, 64 + 64, 136), paint(GOLD, a * 0.9))
    if title: text(c, title, 64, 205, 58, "serifbk", WHITE, a, "l", shadow=6)
    if sub: text(c, sub, 64, 262, 34, "sansm", (200, 190, 170), a, "l")

def badges(c, mapnote=False, a=1.0):
    text(c, "AI配音", W - 52, 104, 28, "sansm", (220, 215, 200), 0.7 * a, "r")
    if mapnote: text(c, "地图示意", W - 52, 146, 28, "sansm", (220, 215, 200), 0.7 * a, "r")

def subtitle(c, s, a=1.0, y=1610, size=58):
    if not s or a <= 0: return
    lines = [ln.rstrip("，。、；：") for ln in wrap(s, 16)]
    n = len(lines)
    y0 = y - (n - 1) * size * 1.38
    for i, ln in enumerate(lines):
        text(c, ln, W / 2, y0 + i * size * 1.38, size, "sans", WHITE, a, "c", stroke=8, stroke_a=0.9, shadow=8)

def card(c, x, y, w, h, a=1.0, fill=(14, 12, 10), fa=0.72, border=GOLD, r=18):
    rr = skia.RRect.MakeRectXY(skia.Rect(x, y, x + w, y + h), r, r)
    c.drawRRect(rr, paint(INK, 0.5 * a, blur=24))
    c.drawRRect(rr, paint(fill, fa * a))
    if border: c.drawRRect(rr, paint(border, 0.75 * a, stroke=2.5))

def seal(c, x, y, s, a=1.0, size=34):
    """small red seal-like tag (e.g. 据记载 / 史料分歧)"""
    f = font("sans", size); tw = f.measureText(s)
    rr = skia.RRect.MakeRectXY(skia.Rect(x, y - size, x + tw + 28, y + size * 0.4), 6, 6)
    c.drawRRect(rr, paint((150, 40, 30), 0.9 * a)); c.drawRRect(rr, paint((235, 190, 160), 0.8 * a, stroke=2))
    text(c, s, x + 14, y, size, "sans", (250, 236, 220), a, "l")
