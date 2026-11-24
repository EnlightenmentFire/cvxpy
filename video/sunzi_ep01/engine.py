# -*- coding: utf-8 -*-
"""渲染引擎：Skia 画布工具、时间轴、字幕、底纹/暗角/颗粒。

画布 1080x1920，30fps。视频号安全区：顶部 ~230px、底部 ~440px 不放关键信息；
字幕基线在 y≈1350–1460。
"""
import json, math, pathlib, functools
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
ROOT = pathlib.Path(__file__).resolve().parent

# ---------- 色板（与系列统一：暗调、骨白、玄黑、暖红、旧金） ----------
PAL = {
    "bg": "#0b0c0f", "bg2": "#16171c", "ink": "#23252c", "ink2": "#33363f",
    "bone": "#e9e2d0", "dim": "#8d8778", "dim2": "#5d594f",
    "gold": "#d6b068", "gold2": "#8c7340",
    "red": "#c24a33", "red2": "#7a2c1f", "ember": "#e8834a",
    "black": "#060607", "water": "#2c3a44", "water2": "#3d5361",
    "bamboo": "#2b2418", "bamboo2": "#3a3122", "bamboo3": "#4a3f2c",
}


def C(name, a=1.0):
    h = PAL.get(name, name).lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))


def mix(c1, c2, t):
    h1 = PAL.get(c1, c1).lstrip("#"); h2 = PAL.get(c2, c2).lstrip("#")
    t = max(0.0, min(1.0, t))
    v = [round(int(h1[i:i + 2], 16) * (1 - t) + int(h2[i:i + 2], 16) * t) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(v)


# ---------- 数学 ----------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def ramp(t, a, b):
    """t 从 a 到 b 线性 0→1（夹紧）。"""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def ease(x):  # smoothstep
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eout(x):  # ease-out cubic
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ein(x):
    x = clamp(x)
    return x ** 3


def pulse(t, a, b, fi=0.4, fo=0.4):
    """在 [a,b] 内为 1，带淡入淡出。"""
    return min(ease(ramp(t, a, a + fi)), 1 - ease(ramp(t, b - fo, b)))


# ---------- 字体 ----------
_fm = skia.FontMgr()


@functools.lru_cache(maxsize=None)
def _tf(kind, weight):
    fam = "Noto Serif CJK SC" if kind == "serif" else "Noto Sans CJK SC"
    tf = _fm.matchFamilyStyle(fam, skia.FontStyle(weight, 5, skia.FontStyle.kUpright_Slant))
    assert tf is not None, fam
    return tf


@functools.lru_cache(maxsize=None)
def font(kind="serif", weight=700, size=48):
    f = skia.Font(_tf(kind, weight), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def tw(s, f, track=0.0):
    return f.measureText(s) + track * max(0, len(s) - 1)


def text(c, s, x, y, f, col="bone", a=1.0, align="l", glow=0.0, track=0.0, glow_col=None, glow_a=0.6):
    """横排文字；y 为基线。align: l/c/r。"""
    if a <= 0.003 or not s:
        return
    w = tw(s, f, track)
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    def draw(paint):
        if track:
            xx = x
            for ch in s:
                c.drawString(ch, xx, y, f, paint)
                xx += f.measureText(ch) + track
        else:
            c.drawString(s, x, y, f, paint)
    if glow > 0:
        p = skia.Paint(AntiAlias=True, Color=C(glow_col or col, a * glow_a))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        draw(p)
    draw(skia.Paint(AntiAlias=True, Color=C(col, a)))


def vtext(c, s, x, y, f, col="bone", a=1.0, step=None, alphas=None, cols=None, glow=0.0):
    """竖排：x 为列中心，y 为首字基线。alphas/cols 可逐字给。"""
    step = step or f.getSize() * 1.12
    for i, ch in enumerate(s):
        ai = a * (alphas[i] if alphas else 1.0)
        ci = cols[i] if cols else col
        text(c, ch, x, y + i * step, f, ci, ai, align="c", glow=glow if ai > 0.5 else 0)


def wrap(s, f, maxw):
    """按宽度折行（中文逐字，标点不置行首）。"""
    lines, cur = [], ""
    for ch in s:
        if tw(cur + ch, f) > maxw and cur and ch not in "，。；：、？！」』》）":
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def para(c, s, x, y, f, col="bone", a=1.0, maxw=800, lh=1.5, align="l"):
    ls = wrap(s, f, maxw)
    for i, l in enumerate(ls):
        text(c, l, x, y + i * f.getSize() * lh, f, col, a, align=align)
    return len(ls)


# ---------- 图形 ----------
def P(col="bone", a=1.0, w=None, cap=True, blur=0.0, dash=None, trim=None, wobble=None):
    p = skia.Paint(AntiAlias=True, Color=C(col, a))
    if w is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        if cap:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    eff = None
    if trim is not None:
        a0, a1 = trim
        if a1 - a0 < 0.9999:
            eff = skia.TrimPathEffect.Make(clamp(a0), clamp(a1))
    if dash is not None:
        d = skia.DashPathEffect.Make(list(dash[:2]), dash[2] if len(dash) > 2 else 0)
        eff = d if eff is None else skia.PathEffect.MakeCompose(d, eff)
    if wobble is not None:
        d = skia.DiscretePathEffect.Make(wobble[0], wobble[1], int(wobble[2]) if len(wobble) > 2 else 1)
        eff = d if eff is None else skia.PathEffect.MakeCompose(d, eff)
    if eff is not None:
        p.setPathEffect(eff)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def spline(pts, closed=False):
    """过点的 Catmull-Rom 平滑曲线。"""
    path = skia.Path()
    n = len(pts)
    if n < 2:
        return path
    path.moveTo(*pts[0])
    if n == 2:
        path.lineTo(*pts[1]); return path
    def g(i):
        if closed:
            return pts[i % n]
        return pts[max(0, min(n - 1, i))]
    last = n if closed else n - 1
    for i in range(last):
        p0, p1, p2, p3 = g(i - 1), g(i), g(i + 1), g(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        path.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        path.close()
    return path


def poly(pts, closed=False):
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    if closed:
        path.close()
    return path


def path_point(path, frac):
    pm = skia.PathMeasure(path, False)
    L = pm.getLength()
    pos, tan = pm.getPosTan(clamp(frac) * L)
    return (pos.x(), pos.y()), (tan.x(), tan.y())


def arrow(c, pts, col="red", w=8, prog=1.0, a=1.0, head=None, dash=None, smooth=True, glow=0.0):
    """沿折线/曲线生长的箭头。prog 0→1。"""
    if prog <= 0.001 or a <= 0.003:
        return
    path = spline(pts) if smooth and len(pts) > 2 else poly(pts)
    head = head or w * 2.6
    if glow > 0:
        c.drawPath(path, P(col, a * 0.5, w * 1.6, blur=glow, trim=(0, prog)))
    c.drawPath(path, P(col, a, w, dash=dash, trim=(0, prog)))
    (x, y), (tx, ty) = path_point(path, prog)
    n = math.hypot(tx, ty) or 1
    tx, ty = tx / n, ty / n
    nx, ny = -ty, tx
    tip = (x + tx * head * 0.9, y + ty * head * 0.9)
    hp = poly([tip, (x - tx * head * 0.25 + nx * head * 0.62, y - ty * head * 0.25 + ny * head * 0.62),
               (x - tx * head * 0.25 - nx * head * 0.62, y - ty * head * 0.25 - ny * head * 0.62)], True)
    c.drawPath(hp, P(col, a))


def rrect(c, x, y, w, h, r, col, a=1.0, sw=None, blur=0.0, dash=None):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, P(col, a, sw, blur=blur, dash=dash))


def circle(c, x, y, r, col, a=1.0, sw=None, blur=0.0, dash=None):
    if a <= 0.003 or r <= 0:
        return
    c.drawCircle(x, y, r, P(col, a, sw, blur=blur, dash=dash))


def glow_dot(c, x, y, r, col, a=1.0, spread=3.0):
    if a <= 0.003:
        return
    circle(c, x, y, r * spread, col, a * 0.35, blur=r * spread * 0.6)
    circle(c, x, y, r, col, a)


def block(c, x, y, w, h, side="han", a=1.0, r=3, lit=1.0):
    """兵力方块。han/qin=玄黑（骨白描边）；enemy=暖红。x,y 为中心。"""
    if a <= 0.003:
        return
    rect = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    if side in ("han", "qin"):
        c.drawRoundRect(skia.Rect.MakeXYWH(x - w / 2 - 3, y - h / 2 - 3, w + 6, h + 6), r + 2, r + 2, P("bone", a * 0.22 * lit, blur=6))
        c.drawRoundRect(rect, r, r, P("black", a))
        c.drawRoundRect(rect, r, r, P("bone", a * (0.4 + 0.6 * lit), max(2.2, min(w, h) * 0.13)))
        k = min(w, h) * 0.2
        c.drawRect(skia.Rect.MakeXYWH(x - k / 2, y - k / 2, k, k), P("bone", a * 0.55 * lit))
    elif side == "gray":
        c.drawRoundRect(rect, r, r, P("ink2", a))
        c.drawRoundRect(rect, r, r, P("dim", a * 0.7, 1.5))
    else:
        c.drawRoundRect(rect, r, r, P(mix("red2", "red", lit), a))


def stamp(c, s, x, y, size=44, col="red", a=1.0, rot=-4):
    """小印章式标注（横排 1–4 字）。"""
    if a <= 0.003:
        return
    f = font("serif", 900, size)
    w = tw(s, f) + size * 0.7
    h = size * 1.5
    c.save(); c.translate(x, y); c.rotate(rot)
    rrect(c, -w / 2, -h / 2, w, h, 6, col, a * 0.92, sw=3.5)
    text(c, s, 0, size * 0.36, f, col, a, align="c")
    c.restore()


def tag(c, s, x, y, size=30, col="dim", a=1.0, align="l", weight=500, kind="sans", plate=False):
    """小标注文字。plate=True 时垫半透明底，保证压在线条上可读。"""
    if a <= 0.003:
        return
    f = font(kind, weight, size)
    if plate:
        w = tw(s, f)
        x0 = x - (w / 2 if align == "c" else w if align == "r" else 0)
        rrect(c, x0 - 10, y - size * 0.95, w + 20, size * 1.32, 6, "bg", a * 0.78)
    text(c, s, x, y, f, col, a, align=align)


# ---------- 时间轴 ----------
class Timeline:
    def __init__(self, path=None):
        d = json.load(open(path or ROOT / "build" / "timeline.json", encoding="utf-8"))
        self.d = d
        self.total = d["total"]
        self.lines = {l["id"]: l for l in d["lines"]}
        self.order = [l["id"] for l in d["lines"]]
        self.segs = d["segs"]
        self.chunks = d["chunks"]  # [{text, start, end, kind}]

    def L(self, lid):
        l = self.lines[lid]
        return l["start"], l["end"]

    def S(self, sid):
        s = self.segs[sid]
        return s["start"], s["end"]


class Ctx:
    """一帧的上下文：t 为全片绝对秒。"""
    def __init__(self, tl, t):
        self.tl, self.t = tl, t

    def st(self, lid):
        return self.tl.lines[lid]["start"]

    def en(self, lid):
        return self.tl.lines[lid]["end"]

    def since(self, lid, off=0.0):
        return self.t - self.tl.lines[lid]["start"] - off

    def after(self, lid, off=0.0):
        """距该行结束的秒数。"""
        return self.t - self.tl.lines[lid]["end"] - off

    def prog(self, lid, lead=0.0, tail=0.0):
        s, e = self.tl.L(lid)
        return ramp(self.t, s + lead, e - tail)

    def fin(self, lid, dur=0.5, off=0.0):
        """该行开始后淡入 0→1。"""
        return ease(ramp(self.t, self.st(lid) + off, self.st(lid) + off + dur))

    def span(self, a, b, fi=0.5, fo=0.5, pre=0.0, post=0.0):
        """从行 a 开始到行 b 结束为 1，带淡入淡出。"""
        return pulse(self.t, self.st(a) - pre, self.en(b) + post, fi, fo)


# ---------- 底纹 / 暗角 / 颗粒（预计算） ----------
_cache = {}


def _noise_img(seed, w, h, scale):
    rng = np.random.default_rng(seed)
    n = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    return n


def _bg_image():
    if "bg" in _cache:
        return _cache["bg"]
    # 低频云状墨色底纹：多层模糊噪声
    rng = np.random.default_rng(7)
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(C("bg"))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C("#101116"), C("#0b0c0f"), C("#08080a")], [0, 0.55, 1])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    for i in range(46):
        x, y = rng.random() * W, rng.random() * H
        r = 180 + rng.random() * 420
        col = "#1b1d24" if rng.random() > 0.35 else "#050506"
        circle(c, x, y, r, col, 0.10 + 0.10 * rng.random(), blur=r * 0.55)
    # 细纸纹：横向极淡的纤维
    for i in range(260):
        y = rng.random() * H
        x = rng.random() * W
        l = 60 + rng.random() * 260
        c.drawLine(x, y, x + l, y + rng.normal() * 3, P("#ffffff", 0.012 + 0.01 * rng.random(), 1.0))
    _cache["bg"] = s.makeImageSnapshot()
    return _cache["bg"]


def _vignette_image():
    if "vig" in _cache:
        return _cache["vig"]
    s = skia.Surface(W, H)
    c = s.getCanvas()
    c.clear(skia.Color(0, 0, 0, 0))
    sh = skia.GradientShader.MakeRadial((W / 2, H * 0.47), H * 0.72,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 150), skia.Color(0, 0, 0, 235)],
                                        [0, 0.52, 0.86, 1.0])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    _cache["vig"] = s.makeImageSnapshot()
    return _cache["vig"]


def _grain_images():
    if "grain" in _cache:
        return _cache["grain"]
    imgs = []
    for k in range(6):
        rng = np.random.default_rng(100 + k)
        n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        a = np.clip(np.abs(n) * 26, 0, 255).astype(np.uint8)
        v = np.where(n > 0, 255, 0).astype(np.uint8)
        arr = np.dstack([v, v, v, a])
        imgs.append(skia.Image.fromarray(np.ascontiguousarray(arr)))
    _cache["grain"] = imgs
    return imgs


def background(c, t):
    img = _bg_image()
    # 极慢的漂移，避免死板
    dx = math.sin(t * 0.05) * 14
    dy = math.cos(t * 0.04) * 10
    c.save()
    c.translate(W / 2 + dx, H / 2 + dy); c.scale(1.05, 1.05); c.translate(-W / 2, -H / 2)
    c.drawImage(img, 0, 0)
    c.restore()


def finish(c, t, frame):
    c.drawImage(_vignette_image(), 0, 0)
    g = _grain_images()[(frame // 2) % 6]
    c.drawImageRect(g, skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=0.16))


# ---------- 字幕 ----------
SUB_Y = 1392          # 单行基线
SUB_MAXW = 900


def subtitles(c, ctx):
    t = ctx.t
    for ch in ctx.tl.chunks:
        if ch["start"] - 0.05 <= t < ch["end"] + 0.12:
            a = min(ease(ramp(t, ch["start"] - 0.05, ch["start"] + 0.10)), 1 - ease(ramp(t, ch["end"], ch["end"] + 0.12)))
            q = ch["kind"] == "q"
            f = font("serif", 700, 56) if q else font("sans", 700, 50)
            col = "gold" if q else "bone"
            lines = ch["lines"]
            lh = 74
            y0 = SUB_Y - (len(lines) - 1) * lh / 2
            # 半透明底板
            wmax = max(tw(l, f) for l in lines)
            ph = lh * len(lines) + 30
            rrect(c, W / 2 - wmax / 2 - 34, y0 - 60, wmax + 68, ph, 14, "#000000", a * 0.46, blur=10)
            for i, l in enumerate(lines):
                y = y0 + i * lh
                # 描边阴影保证可读
                sp = skia.Paint(AntiAlias=True, Color=C("#000000", a * 0.85), Style=skia.Paint.kStroke_Style, StrokeWidth=7)
                sp.setStrokeJoin(skia.Paint.kRound_Join)
                x = W / 2 - tw(l, f) / 2
                c.drawString(l, x, y, f, sp)
                c.drawString(l, x, y, f, skia.Paint(AntiAlias=True, Color=C(col, a)))
            break


def new_surface():
    return skia.Surface(W, H)
