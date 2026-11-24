"""Drawing primitives on a skia canvas."""
import math
import numpy as np
import skia
from theme import *  # noqa: F401,F403

# ---------------------------------------------------------------- paints
def fill(color, a=1.0, shader=None):
    p = skia.Paint(AntiAlias=True, Color=col(color, a))
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(a)
    return p


def stroke(color, w=3.0, a=1.0, cap="round", dash=None, blur=0.0):
    p = skia.Paint(AntiAlias=True, Color=col(color, a), Style=skia.Paint.kStroke_Style, StrokeWidth=w)
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(list(dash), 0))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ---------------------------------------------------------------- text
_PUNCT_NO_START = set("，。、；：？！”’）》」』…—,.;:?!)%")


def text_w(s, fname, size, spacing=0.0):
    f = font(fname, size)
    if spacing == 0:
        return f.measureText(s)
    return sum(f.measureText(ch) for ch in s) + spacing * max(0, len(s) - 1)


def text(c, s, x, y, fname, size, color, a=1.0, align="l", spacing=0.0, glow=0.0, glow_a=0.45):
    """Draw text with baseline y. align: l / c / r. Returns width."""
    if not s or a <= 0:
        return 0.0
    f = font(fname, size)
    w = text_w(s, fname, size, spacing)
    x0 = x - (w / 2 if align == "c" else w if align == "r" else 0)
    paints = []
    if glow > 0:
        gp = fill(color, a * glow_a)
        gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
        paints.append(gp)
    paints.append(fill(color, a))
    for p in paints:
        if spacing == 0:
            c.drawString(s, x0, y, f, p)
        else:
            xx = x0
            for ch in s:
                c.drawString(ch, xx, y, f, p)
                xx += f.measureText(ch) + spacing
    return w


def shadow_text(c, s, x, y, fname, size, color, a=1.0, align="c", spacing=0.0, sh=(0, 0, 0), sh_a=0.75, sh_blur=6):
    f = font(fname, size)
    w = text_w(s, fname, size, spacing)
    x0 = x - (w / 2 if align == "c" else w if align == "r" else 0)
    sp = fill(sh, a * sh_a)
    sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sh_blur))
    for p, dy in ((sp, 3), (fill(color, a), 0)):
        xx = x0
        if spacing == 0:
            c.drawString(s, x0, y + dy, f, p)
        else:
            for ch in s:
                c.drawString(ch, xx, y + dy, f, p)
                xx += f.measureText(ch) + spacing
    return w


def wrap(s, fname, size, maxw):
    """Greedy CJK-aware wrap; keeps closing punctuation off line starts."""
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if text_w(cur + ch, fname, size) <= maxw or not cur:
            cur += ch
        else:
            if ch in _PUNCT_NO_START:
                cur += ch
            else:
                # don't break inside a latin word / number
                j = len(cur)
                while j > 0 and (cur[j - 1].isascii() and cur[j - 1].isalnum()) and ch.isascii() and ch.isalnum():
                    j -= 1
                if 0 < j < len(cur):
                    lines.append(cur[:j])
                    cur = cur[j:] + ch
                else:
                    lines.append(cur)
                    cur = ch
    if cur:
        lines.append(cur)
    return lines


_JIEBA = None


def _word_bounds(s):
    global _JIEBA
    if _JIEBA is None:
        import jieba
        jieba.setLogLevel(60)
        _JIEBA = jieba
    pos, out = 0, set()
    for w in _JIEBA.cut(s):
        pos += len(w)
        out.add(pos)
    return out


def balanced_wrap(s, fname, size, maxw):
    """Wrap into the fewest lines; break after punctuation if possible, else at a
    word boundary, never inside a word; keep closing punctuation off line starts."""
    lines = wrap(s, fname, size, maxw)
    if len(lines) < 2:
        return lines
    n = len(lines)
    if n > 3:
        return lines
    bounds = _word_bounds(s)
    total = text_w(s, fname, size)

    def ok_break(i):  # break before index i
        return 0 < i < len(s) and s[i] not in _PUNCT_NO_START

    def score_split(cuts):
        segs = [s[a:b] for a, b in zip([0] + cuts, cuts + [len(s)])]
        ws = [text_w(x, fname, size) for x in segs]
        if max(ws) > maxw:
            return None
        pen = 0.0
        for c_ in cuts:
            if s[c_ - 1] in "，。；：、？！":
                pen += 0
            elif c_ in bounds:
                pen += 0.18 * total
            else:
                pen += 10 * total
        return (max(ws) - min(ws)) + pen

    best = None
    if n == 2:
        for i in range(1, len(s)):
            if ok_break(i):
                sc = score_split([i])
                if sc is not None and (best is None or sc < best[0]):
                    best = (sc, [i])
    else:
        for i in range(1, len(s)):
            if not ok_break(i):
                continue
            for j in range(i + 1, len(s)):
                if ok_break(j):
                    sc = score_split([i, j])
                    if sc is not None and (best is None or sc < best[0]):
                        best = (sc, [i, j])
    if best is None:
        return lines
    cuts = best[1]
    return [s[a:b] for a, b in zip([0] + cuts, cuts + [len(s)])]


def typewriter(c, s, n, x, y, fname, size, color, a=1.0, cursor_t=None, spacing=0.0, glow=0.0):
    """Draw first n characters of s (n may be fractional)."""
    k = int(max(0, min(len(s), math.floor(n))))
    w = text(c, s[:k], x, y, fname, size, color, a, "l", spacing, glow)
    if cursor_t is not None and (k < len(s) or (cursor_t % 0.9) < 0.5):
        f = font(fname, size)
        m = f.getMetrics()
        cw = max(6.0, size * 0.42)
        c.drawRect(skia.Rect.MakeXYWH(x + w + (spacing if k else 0) + 3, y + m.fAscent * 0.78, cw, -m.fAscent * 0.95), fill(color, a * 0.85))
    return w


def _runs(s):
    runs, cur, cur_ascii = [], "", None
    for ch in s:
        isa = ch.isascii() and ch not in "“”"
        if cur and isa != cur_ascii:
            runs.append((cur, cur_ascii))
            cur = ""
        cur += ch
        cur_ascii = isa
    if cur:
        runs.append((cur, cur_ascii))
    return runs


def mtext_w(s, size, cjk="bold", mono="mono", mono_scale=0.96):
    return sum(text_w(r, mono if a else cjk, size * (mono_scale if a else 1.0)) for r, a in _runs(s))


def mtext(c, s, x, y, size, color, a=1.0, align="l", cjk="bold", mono="mono", mono_scale=0.96, glow=0.0):
    """Mixed text: ASCII runs in the mono font, everything else in a CJK font."""
    w = mtext_w(s, size, cjk, mono, mono_scale)
    xx = x - (w / 2 if align == "c" else w if align == "r" else 0)
    for r, isa in _runs(s):
        fn = mono if isa else cjk
        sz = size * (mono_scale if isa else 1.0)
        xx += text(c, r, xx, y, fn, sz, color, a, "l", 0.0, glow)
    return w


# ---------------------------------------------------------------- shapes
def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


def badge(c, s, x, y, color=GOLD, a=1.0, size=27, align="r"):
    """Small outlined tag, e.g. 示意. (x, y) = top-right (align r) or top-left."""
    w = text_w(s, "medium", size) + 30
    h = size + 20
    x0 = x - w if align == "r" else x
    c.drawRRect(rrect(x0, y, w, h, 9), fill(BG_LO, 0.55 * a))
    c.drawRRect(rrect(x0, y, w, h, 9), stroke(color, 2, a * 0.9))
    text(c, s, x0 + w / 2, y + h / 2 + size * 0.36, "medium", size, color, a, "c")
    return w, h


def glow_path(c, path, color, w=4.0, a=1.0, glow=10.0, glow_a=0.5, dash=None):
    if a <= 0:
        return
    if glow > 0:
        c.drawPath(path, stroke(color, w * 2.6, a * glow_a, dash=dash, blur=glow))
    c.drawPath(path, stroke(color, w, a, dash=dash))


def polyline(pts):
    p = skia.Path()
    if len(pts) == 0:
        return p
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p


def panel(c, x, y, w, h, a=1.0, title=None, border=PHOS_DIM, scan=True, grid=60):
    """Retro terminal panel."""
    c.drawRRect(rrect(x, y, w, h, 18), fill(BG_LO, 0.92 * a))
    c.save()
    c.clipRRect(rrect(x, y, w, h, 18), doAntiAlias=True)
    if grid:
        gp = stroke(GRID, 1.2, 0.55 * a)
        gx = x + (w % grid) / 2
        while gx < x + w:
            c.drawLine(gx, y, gx, y + h, gp)
            gx += grid
        gy = y + (h % grid) / 2
        while gy < y + h:
            c.drawLine(x, gy, x + w, gy, gp)
            gy += grid
    if scan:
        sp = stroke((0, 0, 0), 1.0, 0.16 * a)
        for yy in range(int(y), int(y + h), 4):
            c.drawLine(x, yy, x + w, yy, sp)
    c.restore()
    c.drawRRect(rrect(x, y, w, h, 18), stroke(border, 2.0, 0.9 * a))
    if title:
        text(c, title, x + 26, y + 46, "mono", 26, PHOS, 0.85 * a)


# ---------------------------------------------------------------- turtle
def _turtle_shell_paths():
    shell = skia.Path()
    shell.addOval(skia.Rect.MakeLTRB(-100, -128, 100, 128))
    inner = skia.Path()
    inner.addOval(skia.Rect.MakeLTRB(-74, -100, 74, 100))
    ys = np.linspace(-92, 92, 6)
    b = [10, 17, 19, 19, 17, 10]
    w = [25, 31, 33, 31, 25]
    hexes = skia.Path()
    ribs = skia.Path()
    for k in range(5):
        y0, y1 = ys[k], ys[k + 1]
        ym = (y0 + y1) / 2
        hexes.addPoly([(-b[k], y0), (b[k], y0), (w[k], ym), (b[k + 1], y1), (-b[k + 1], y1), (-w[k], ym)], True)
        xe = 74 * math.sqrt(max(0.0, 1 - (ym / 100.0) ** 2))
        for s in (-1, 1):
            ribs.moveTo(s * w[k], ym)
            ribs.lineTo(s * xe * 0.985, ym + (8 if ym > 0 else -8) * abs(ym) / 100)
    rim = skia.Path()
    for k in range(22):
        ang = 2 * math.pi * k / 22 + 0.07
        ca, sa = math.cos(ang), math.sin(ang)
        rim.moveTo(74 * ca, 100 * sa)
        rim.lineTo(100 * ca, 128 * sa)
    return shell, inner, hexes, ribs, rim


_SHELL = None


def turtle(c, x, y, scale=1.0, rot=0.0, phase=0.0, color=GOLD, a=1.0, w=3.2, fill_bg=BG, glow=0.0):
    """Line-drawn sea turtle, facing up at rot=0. phase drives flipper strokes."""
    global _SHELL
    if _SHELL is None:
        _SHELL = _turtle_shell_paths()
    shell, inner, hexes, ribs, rim = _SHELL
    if a <= 0:
        return
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    sw = w / scale
    p = stroke(color, sw, a)
    gp = stroke(color, sw * 3, a * 0.35, blur=glow / scale) if glow > 0 else None
    sweep = math.sin(phase * 2 * math.pi)
    for s in (-1, 1):
        # front flipper
        c.save()
        c.translate(s * 78, -62)
        c.rotate(s * (10 * sweep - 4))
        f = skia.Path()
        f.moveTo(0, 0)
        f.cubicTo(s * 52, -50, s * 112, -10, s * 128, 70)
        f.cubicTo(s * 94, 52, s * 44, 40, s * 10, 34)
        f.close()
        c.drawPath(f, fill(fill_bg, a))
        if gp:
            c.drawPath(f, gp)
        c.drawPath(f, p)
        c.restore()
        # rear flipper
        c.save()
        c.translate(s * 50, 104)
        c.rotate(s * (-8 * sweep))
        r = skia.Path()
        r.moveTo(0, -6)
        r.cubicTo(s * 30, 2, s * 56, 22, s * 60, 52)
        r.cubicTo(s * 38, 46, s * 14, 32, -s * 6, 14)
        r.close()
        c.drawPath(r, fill(fill_bg, a))
        if gp:
            c.drawPath(r, gp)
        c.drawPath(r, p)
        c.restore()
    # tail
    t = skia.Path()
    t.moveTo(-9, 124)
    t.lineTo(0, 150)
    t.lineTo(9, 124)
    c.drawPath(t, p)
    # head + neck
    head = skia.Path()
    head.moveTo(-17, -122)
    head.cubicTo(-22, -140, -28, -160, -14, -176)
    head.cubicTo(-6, -184, 6, -184, 14, -176)
    head.cubicTo(28, -160, 22, -140, 17, -122)
    head.close()
    c.drawPath(head, fill(fill_bg, a))
    if gp:
        c.drawPath(head, gp)
    c.drawPath(head, p)
    c.drawCircle(-9, -163, 3.0 / scale ** 0.3, fill(color, a))
    c.drawCircle(9, -163, 3.0 / scale ** 0.3, fill(color, a))
    # shell
    c.drawPath(shell, fill(fill_bg, a))
    if gp:
        c.drawPath(shell, gp)
    c.drawPath(shell, p)
    thin = stroke(color, sw * 0.72, a * 0.9)
    c.drawPath(inner, thin)
    c.drawPath(hexes, thin)
    c.drawPath(ribs, thin)
    c.drawPath(rim, stroke(color, sw * 0.6, a * 0.75))
    c.restore()


# ---------------------------------------------------------------- people
def bust(c, x, y, s=1.0, color=SILH, a=1.0, rim=GOLD, rim_a=0.55, mirror=False):
    """Front-facing head-and-shoulders silhouette; (x, y) = bottom centre."""
    c.save()
    c.translate(x, y)
    c.scale(-s if mirror else s, s)
    body = skia.Path()
    body.moveTo(-104, 0)
    body.lineTo(-104, -70)
    body.cubicTo(-104, -122, -70, -140, -30, -148)
    body.lineTo(-20, -170)
    body.lineTo(20, -170)
    body.lineTo(30, -148)
    body.cubicTo(70, -140, 104, -122, 104, -70)
    body.lineTo(104, 0)
    body.close()
    head = skia.Path()
    head.addOval(skia.Rect.MakeLTRB(-40, -262, 40, -160))
    for pth in (body, head):
        c.drawPath(pth, fill(color, a))
        if rim_a > 0:
            c.drawPath(pth, stroke(rim, 2.2 / s, a * rim_a))
    c.restore()


def walker(c, x, y, s=1.0, phase=0.0, color=SILH, a=1.0, rim=GOLD, rim_a=0.45, walking=True):
    """Simple full-body pictogram; (x, y) = feet."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    sw = math.sin(phase * 2 * math.pi) if walking else 0.0
    parts = []
    for side, ang in ((-1, 20 * sw), (1, -20 * sw)):
        leg = skia.Path()
        leg.addRRect(rrect(-8, 0, 16, 66, 8))
        parts.append(("leg", side, ang, leg))
    for side, ang in ((-1, -16 * sw), (1, 16 * sw)):
        arm = skia.Path()
        arm.addRRect(rrect(-6.5, 0, 13, 56, 6.5))
        parts.append(("arm", side, ang, arm))
    p_fill = fill(color, a)
    p_rim = stroke(rim, 1.8 / s, a * rim_a)
    for kind, side, ang, pth in parts:
        c.save()
        if kind == "leg":
            c.translate(side * 10, -68)
        else:
            c.translate(side * 25, -128)
        c.rotate(ang)
        c.drawPath(pth, p_fill)
        c.drawPath(pth, p_rim)
        c.restore()
    torso = skia.Path()
    torso.addRRect(rrect(-24, -134, 48, 72, 13))
    head = skia.Path()
    head.addCircle(0, -158, 19)
    for pth in (torso, head):
        c.drawPath(pth, p_fill)
        c.drawPath(pth, p_rim)
    c.restore()


# ---------------------------------------------------------------- icons (line, ~52px box)
def icon(c, kind, x, y, s=1.0, color=GOLD, a=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    p = stroke(color, 2.6 / s, a)
    pf = fill(color, a)
    if kind == "keyboard":
        c.drawRRect(rrect(-27, -15, 54, 30, 5), p)
        for r in range(3):
            for k in range(6 - (r == 2) * 2):
                c.drawRect(skia.Rect.MakeXYWH(-21 + k * 7.6 + (r == 2) * 7.6, -9 + r * 7.5, 4.2, 3.6), pf)
        c.drawRect(skia.Rect.MakeXYWH(-10, 9.5, 20, 2.6), pf)
    elif kind == "abacus":
        c.drawRRect(rrect(-25, -20, 50, 40, 3), p)
        for r, beads in ((-9, (-15, -8, 9)), (1, (-15, 3, 10, 17)), (11, (-8, -1, 15))):
            c.drawLine(-25, r, 25, r, stroke(color, 1.6 / s, a))
            for bx in beads:
                c.drawCircle(bx, r, 3.4, pf)
        c.drawLine(-25, -15, 25, -15, stroke(color, 1.6 / s, a * 0.0))
    elif kind == "cards":
        for ang, dx in ((-14, -7), (10, 7)):
            c.save()
            c.translate(dx, 2)
            c.rotate(ang)
            c.drawRRect(rrect(-13, -19, 26, 38, 4), fill(BG, a))
            c.drawRRect(rrect(-13, -19, 26, 38, 4), p)
            c.restore()
        text(c, "A", 7, 9, "mono", 20, color, a, "c")
    elif kind == "dice":
        c.save()
        c.rotate(12)
        c.drawRRect(rrect(-17, -17, 34, 34, 7), p)
        for px, py in ((-8, -8), (8, -8), (0, 0), (-8, 8), (8, 8)):
            c.drawCircle(px, py, 3.0, pf)
        c.restore()
    elif kind == "shield":
        sh = skia.Path()
        sh.moveTo(0, -22)
        sh.lineTo(20, -14)
        sh.cubicTo(20, 6, 12, 16, 0, 23)
        sh.cubicTo(-12, 16, -20, 6, -20, -14)
        sh.close()
        c.drawPath(sh, p)
        st = skia.Path()
        st.moveTo(-8, 0)
        st.lineTo(-2, 7)
        st.lineTo(9, -6)
        c.drawPath(st, p)
    elif kind == "ledger":
        c.drawRRect(rrect(-24, -18, 48, 36, 3), p)
        c.drawLine(0, -18, 0, 18, p)
        for r in (-9, -2, 5, 12):
            c.drawLine(-19, r, -5, r, stroke(color, 1.4 / s, a))
            c.drawLine(5, r, 19, r, stroke(color, 1.4 / s, a))
    elif kind == "mask":
        m = skia.Path()
        m.moveTo(-20, -16)
        m.cubicTo(-8, -20, 8, -20, 20, -16)
        m.cubicTo(22, 6, 12, 20, 0, 21)
        m.cubicTo(-12, 20, -22, 6, -20, -16)
        m.close()
        c.drawPath(m, p)
        c.drawOval(skia.Rect.MakeXYWH(-12, -8, 8, 5), pf)
        c.drawOval(skia.Rect.MakeXYWH(4, -8, 8, 5), pf)
        sm = skia.Path()
        sm.moveTo(-8, 8)
        sm.quadTo(0, 14, 8, 8)
        c.drawPath(sm, p)
    elif kind == "chart":
        c.drawLine(-24, 18, 24, 18, p)
        c.drawLine(-24, 18, -24, -20, p)
        c.drawPath(polyline([(-18, 10), (-8, 2), (0, 8), (10, -6), (20, -14)]), p)
    elif kind == "book":
        c.drawRRect(rrect(-20, -22, 40, 44, 3), p)
        c.drawLine(-12, -22, -12, 22, p)
    elif kind == "question":
        text(c, "?", 0, 14, "mono", 40, color, a, "c")
    c.restore()


def coin(c, x, y, r, ang, color=GOLD, a=1.0):
    """Coin flipping about its horizontal axis; ang in radians."""
    ry = r * abs(math.cos(ang))
    thick = 7 * abs(math.sin(ang))
    face = mix(color, GOLD_HI, 0.25) if math.cos(ang) >= 0 else mix(color, GOLD_DIM, 0.35)
    if thick > 0.5:
        c.drawOval(skia.Rect.MakeLTRB(x - r, y - ry + thick, x + r, y + ry + thick), fill(GOLD_DIM, a))
    c.drawOval(skia.Rect.MakeLTRB(x - r, y - max(ry, 1.2), x + r, y + max(ry, 1.2)), fill(face, a))
    c.drawOval(skia.Rect.MakeLTRB(x - r * 0.78, y - max(ry * 0.78, 0.8), x + r * 0.78, y + max(ry * 0.78, 0.8)), stroke(GOLD_DIM, 2.2, a * 0.8))


# ---------------------------------------------------------------- post textures
def make_grain(n=6, seed=7, amp=46):
    rng = np.random.default_rng(seed)
    imgs = []
    for _ in range(n):
        g = rng.normal(128, amp, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)
        rgba = np.dstack([g, g, g, np.full_like(g, 255)])
        imgs.append(skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType))
    return imgs


def vignette_paint(strength=0.62):
    sh = skia.GradientShader.MakeRadial(
        center=(W / 2, H * 0.46), radius=H * 0.72,
        colors=[col((0, 0, 0), 0.0), col((0, 0, 0), 0.0), col((0, 0, 0), strength * 0.55), col((0, 0, 0), strength)],
        positions=[0.0, 0.42, 0.78, 1.0])
    p = skia.Paint(AntiAlias=True)
    p.setShader(sh)
    return p
