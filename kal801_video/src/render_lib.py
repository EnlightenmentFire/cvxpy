# -*- coding: utf-8 -*-
"""画面公共库：画布、配色、字体、文字排版、字幕、字幕卡、缓动。skia-python 绘制。"""
import math
import random

import numpy as np
import skia

W, H = 1080, 1920
FPS = 30

# 视频号安全区（顶部状态栏/标题、底部点赞评论区会遮挡）
SAFE_TOP = 240
SAFE_BOTTOM = 1500           # 正文与字幕不低于此线
SUB_Y = 1300                 # 字幕区上沿
SIDE = 64                    # 左右边距


def rgb(h, a=255):
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def rgba(h, alpha):
    return rgb(h, max(0, min(255, int(alpha * 255))))


# ── 配色：夜航驾驶舱 ──
C = dict(
    bg="#060A12", bg2="#0B1322", navy="#12203A", navy2="#1A2C4C", steel="#2B3E60", grid="#16243C",
    text="#E9EEF5", text2="#9AABC2", text3="#5E708C",
    amber="#F2A93B", amber2="#C9822A", green="#58D68D", cyan="#86D4FF", cyan2="#4FA9DD",
    red="#FF3B30", red2="#B3261E",
    sepia_bg="#1B130B", sepia="#E7C27D", sepia2="#9C7A47", sepia_green="#9BC46A",
    paper="#E9E2D0", ink="#2A2520",
)

# ── 字体 ──
_FM = skia.FontMgr()
_TF = {}


def tf(kind="sans", weight=700):
    key = (kind, weight)
    if key not in _TF:
        fam = {"sans": "Noto Sans CJK SC", "serif": "Noto Serif CJK SC", "mono": "Liberation Mono",
               "monocjk": "Noto Sans Mono CJK SC"}[kind]
        _TF[key] = _FM.matchFamilyStyle(fam, skia.FontStyle(weight, 5, skia.FontStyle.kUpright_Slant))
    return _TF[key]


def font(size, kind="sans", weight=700):
    f = skia.Font(tf(kind, weight), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def paint(color, alpha=1.0, stroke=None, aa=True, blur=None, cap=None):
    p = skia.Paint(AntiAlias=aa)
    if isinstance(color, str):
        p.setColor(rgba(color, alpha))
    else:
        p.setColor(color)
        p.setAlphaf(p.getAlphaf() * alpha)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
    if cap == "round":
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ── 缓动 ──
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def fade_io(t, dur, fin=0.35, fout=0.35):
    """在 [0,dur] 内淡入淡出的透明度。"""
    if dur <= 0:
        return 0.0
    a = clamp(t / fin) if fin > 0 else 1.0
    b = clamp((dur - t) / fout) if fout > 0 else 1.0
    return ease(min(a, b))


# ── 文字排版 ──
NO_START = set("，。、；：？！）」』”’》〉…—,.;:?!)]}%·")
NO_END = set("（「『“‘《〈([{")


def wrap(text, f, maxw):
    """中英混排断行：中文按字，英文按词；避头尾标点。"""
    tokens = []
    buf = ""
    for ch in text:
        if ch.isascii() and not ch.isspace() and ch not in ",.;:?!)]}([{":
            buf += ch
        else:
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
    if buf:
        tokens.append(buf)
    lines, cur = [], ""
    for tk in tokens:
        if tk == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + tk
        if f.measureText(trial) <= maxw or not cur.strip():
            cur = trial
        else:
            # 避头：标点不放行首
            if tk[0] in NO_START:
                cur = trial
                continue
            # 避尾：行尾的开引号挪到下一行
            carry = ""
            while cur and cur[-1] in NO_END:
                carry = cur[-1] + carry
                cur = cur[:-1]
            lines.append(cur.rstrip())
            cur = (carry + tk).lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def text_w(s, f):
    return f.measureText(s)


def _has_cjk(s):
    return any(ord(ch) > 0x2E7F for ch in s)


_LATIN_MONO = {"Liberation Mono", "DejaVu Sans Mono"}


def draw_text(c, s, x, y, f, color="#FFFFFF", alpha=1.0, align="left", glow=None, glow_alpha=0.6, shadow=False):
    if alpha <= 0.003:
        return 0
    if _has_cjk(s) and f.getTypeface().getFamilyName() in _LATIN_MONO:
        f = font(f.getSize(), "monocjk", 700)
    w = f.measureText(s)
    if align == "center":
        x = x - w / 2
    elif align == "right":
        x = x - w
    if shadow:
        c.drawString(s, x + 2, y + 3, f, paint("#000000", alpha * 0.55, blur=4))
    if glow:
        c.drawString(s, x, y, f, paint(glow, alpha * glow_alpha, blur=10))
    c.drawString(s, x, y, f, paint(color, alpha))
    return w


def draw_lines(c, lines, x, y, f, lh, color="#FFFFFF", alpha=1.0, align="left", **kw):
    for i, ln in enumerate(lines):
        draw_text(c, ln, x, y + i * lh, f, color, alpha, align, **kw)
    return y + len(lines) * lh


def rrect(c, x, y, w, h, r, color, alpha=1.0, stroke=None, blur=None):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint(color, alpha, stroke=stroke, blur=blur))


def line(c, x0, y0, x1, y1, color, alpha=1.0, width=2, dash=None, cap="round", blur=None):
    p = paint(color, alpha, stroke=width, cap=cap, blur=blur)
    if dash:
        p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    c.drawLine(x0, y0, x1, y1, p)


def path_from(pts, close=False):
    pa = skia.Path()
    pa.moveTo(*pts[0])
    for p in pts[1:]:
        pa.lineTo(*p)
    if close:
        pa.close()
    return pa


def smooth_path(pts, close=False):
    """Catmull-Rom 转贝塞尔，用于地形/海岸线。"""
    pa = skia.Path()
    n = len(pts)
    if n < 3:
        return path_from(pts, close)
    P = pts + pts[:3] if close else [pts[0]] + pts + [pts[-1]]
    pa.moveTo(*P[1])
    rng = range(1, n + 1) if close else range(1, n)
    for i in rng:
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        pa.cubicTo(*c1, *c2, *p2)
    if close:
        pa.close()
    return pa


# ── 背景 ──
_VIG = {}


def vignette(c, strength=0.65, color="#000000"):
    key = (strength, color)
    if key not in _VIG:
        shader = skia.GradientShader.MakeRadial(
            skia.Point(W / 2, H * 0.45), H * 0.78,
            [rgba(color, 0.0), rgba(color, 0.0), rgba(color, strength)], [0.0, 0.55, 1.0])
        p = skia.Paint(Shader=shader)
        _VIG[key] = p
    c.drawRect(skia.Rect.MakeWH(W, H), _VIG[key])


def bg_night(c, glow=0.0):
    c.clear(rgb(C["bg"]))
    shader = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                            [rgb("#0A1222"), rgb(C["bg"]), rgb("#05080F")], [0.0, 0.55, 1.0])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=shader))
    if glow > 0:
        sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, 1180), 700,
                                            [rgba(C["amber"], 0.10 * glow), rgba(C["amber"], 0.0)], [0.0, 1.0])
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


def grid_bg(c, alpha=0.35, step=60, y0=0, y1=H):
    p = paint(C["grid"], alpha, stroke=1)
    for x in range(0, W + 1, step):
        c.drawLine(x, y0, x, y1, p)
    for y in range(int(y0), int(y1) + 1, step):
        c.drawLine(0, y, W, y, p)


# ── 段落标签（安全区内左上） ──
def section_tag(c, sec, title, alpha=1.0, color=None):
    if alpha <= 0 or not sec:
        return
    col = color or C["amber"]
    f1 = font(30, "mono", 700)
    f2 = font(34, "sans", 700)
    y = SAFE_TOP + 46
    draw_text(c, f"{sec:02d}", SIDE, y, f1, col, alpha)
    line(c, SIDE + 56, y - 11, SIDE + 92, y - 11, col, alpha * 0.8, 2)
    draw_text(c, title, SIDE + 104, y, f2, C["text"], alpha * 0.92)


# ── 旁白字幕 ──
def subtitle(c, lines, alpha=1.0, key=False, y=SUB_Y, size=46):
    if alpha <= 0.003 or not lines:
        return
    f = font(size, "sans", 700)
    lh = size * 1.42
    widths = [f.measureText(s) for s in lines]
    bw = max(widths) + 56
    bh = lh * len(lines) + 30
    bx = (W - bw) / 2
    rrect(c, bx, y, bw, bh, 18, "#03060C", alpha * 0.62)
    if key:
        line(c, bx + 18, y + 18, bx + 18, y + bh - 18, C["amber"], alpha, 5)
    col = "#FFD58A" if key else C["text"]
    for i, s in enumerate(lines):
        draw_text(c, s, W / 2, y + 15 + size * 1.02 + i * lh, f, col, alpha, "center", shadow=True)


def split_subtitle(text, maxw=W - 2 * SIDE - 70, size=46, max_lines=2):
    """把一句字幕切成若干屏（每屏 ≤ max_lines 行）：先按小句（，、：；——）装行，必要时才按字断。"""
    import re as _re
    f = font(size, "sans", 700)
    sents, cur = [], ""
    for ch in text:
        cur += ch
        if ch in "。；！？":
            sents.append(cur)
            cur = ""
    if cur:
        sents.append(cur)
    pages, page_lines = [], []
    for snt in sents:
        clauses = [c for c in _re.split(r"(?<=[，、：；”])|(?<=——)", snt.strip()) if c]
        lines, cur = [], ""
        for cl in clauses:
            if f.measureText(cur + cl) <= maxw:
                cur += cl
            else:
                if cur:
                    lines.append(cur)
                if f.measureText(cl) <= maxw:
                    cur = cl
                else:
                    sub = wrap(cl, f, maxw)
                    lines += sub[:-1]
                    cur = sub[-1]
        if cur:
            lines.append(cur)
        if page_lines and len(page_lines) + len(lines) > max_lines:
            pages.append(page_lines)
            page_lines = []
        while len(lines) > max_lines:
            pages.append(lines[:max_lines])
            lines = lines[max_lines:]
        page_lines += lines
    if page_lines:
        pages.append(page_lines)
    return [_balance(p, f, maxw) for p in pages]


def _balance(lines, f, maxw):
    """两行字幕：第二行太短时，在中间附近（优先标点后）重新断行。"""
    if len(lines) != 2:
        return lines
    a, b = lines
    if f.measureText(b) >= 0.45 * f.measureText(a):
        return lines
    txt = a + b
    n = len(txt)
    best, best_score = None, 1e9
    for i in range(max(1, n // 2 - n // 3), min(n - 1, n // 2 + n // 3) + 1):
        l1, l2 = txt[:i], txt[i:]
        if l2[:1] in NO_START or l1[-1:] in NO_END:
            continue
        if f.measureText(l1) > maxw or f.measureText(l2) > maxw:
            continue
        score = abs(f.measureText(l1) - f.measureText(l2))
        if l1[-1:] in "，、：；—":
            score -= f.measureText("中") * 2.5
        if l1[-1:].isascii() and l1[-1:].isalnum() and l2[:1].isascii() and l2[:1].isalnum():
            score += 1e6          # 不在英文单词/数字中间断开
        if score < best_score:
            best, best_score = (l1, l2), score
    return list(best) if best else lines


# ── 黑匣子字幕卡 ──
LANG_TAG = {"ko": "原话为韩语 · NTSB 英译", "mix": "韩英混说 · NTSB 英译", "en": "原话即英语"}


def quote_card(c, q, x, y, w, alpha=1.0, accent=None, big=False, t_type=None, scale=1.0):
    """返回卡片高度。t_type: 打字机进度 0-1（None=全部显示）。"""
    if alpha <= 0.003:
        return 0
    accent = accent or C["amber"]
    fs = (46 if big else 38) * scale
    fen = font(fs, "mono", 700)
    pad = 26 * scale
    lines = wrap(q["en"], fen, w - 2 * pad)
    lh = fs * 1.32
    fh = font(26 * scale, "mono", 700)
    fwho = font(28 * scale, "sans", 700)
    ftag = font(22 * scale, "sans", 400)
    note = q.get("note")
    fnote = font(24 * scale, "sans", 400)
    note_lines = wrap(note, fnote, w - 2 * pad) if note else []
    h = pad + 34 * scale + 14 * scale + lh * len(lines) + 12 * scale + 30 * scale + (len(note_lines) * 32 * scale) + pad * 0.7
    rrect(c, x + 6, y + 10, w, h, 16 * scale, "#000000", alpha * 0.45, blur=14)
    rrect(c, x, y, w, h, 16 * scale, "#0A1120", alpha * 0.92)
    rrect(c, x, y, w, h, 16 * scale, accent, alpha * 0.55, stroke=2)
    line(c, x + 2, y + 18 * scale, x + 2, y + h - 18 * scale, accent, alpha, 5 * scale, cap="butt")
    ty = y + pad + 24 * scale
    tw = draw_text(c, q["t"], x + pad, ty, fh, accent, alpha)
    draw_text(c, q["who"], x + pad + tw + 20 * scale, ty + 1, fwho, C["text"], alpha)
    ty += 14 * scale + lh * 0.95
    total = sum(len(s) for s in lines)
    shown = total if t_type is None else int(round(total * clamp(t_type)))
    k = 0
    for s in lines:
        n = clamp(shown - k, 0, len(s))
        if n > 0:
            draw_text(c, s[:int(n)], x + pad, ty, fen, "#FFFFFF", alpha)
        k += len(s)
        ty += lh
    if t_type is not None and t_type < 1.0 and (int(t_type * 60) % 2 == 0):
        pass
    ty += 4 * scale
    draw_text(c, LANG_TAG.get(q.get("lang"), ""), x + pad, ty, ftag, C["text3"], alpha)
    ty += 34 * scale
    for s in note_lines:
        draw_text(c, s, x + pad, ty, fnote, C["text2"], alpha)
        ty += 32 * scale
    return h


def gpws_text(c, s, x, y, size=64, alpha=1.0, align="center"):
    f = font(size, "mono", 700)
    draw_text(c, s.upper(), x, y, f, C["red"], alpha, align, glow=C["red"], glow_alpha=0.9)


# ── 简单噪点纹理（静态，减少码率） ──
_GRAIN = {}


def grain_image(seed=0, amp=10, warm=False):
    key = (seed, amp, warm)
    if key not in _GRAIN:
        rng = np.random.default_rng(seed)
        small = rng.normal(0, amp, (H // 3, W // 3)).astype(np.float32)
        big = np.kron(small, np.ones((3, 3), np.float32))[:H, :W]
        a = np.clip(np.abs(big) * 2.2, 0, 255).astype(np.uint8)
        base = np.where(big[..., None] > 0, np.array([255, 245, 225] if warm else [255, 255, 255], np.uint8),
                        np.array([0, 0, 0], np.uint8))
        arr = np.dstack([base.astype(np.uint8), a])
        _GRAIN[key] = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
    return _GRAIN[key]


def overlay_grain(c, seed=0, amp=10, alpha=0.25, warm=False):
    img = grain_image(seed % 4, amp, warm)
    p = skia.Paint()
    p.setAlphaf(alpha)
    c.drawImage(img, 0, 0, skia.SamplingOptions(), p)


# ── 小图标 ──
def plane_side(c, x, y, s=1.0, color="#FFFFFF", alpha=1.0, pitch=0.0):
    """侧视大型客机剪影（朝右）。"""
    c.save()
    c.translate(x, y)
    c.rotate(-pitch)
    c.scale(s, s)
    pts = [(-46, -3), (-40, -7), (30, -7), (40, -5), (47, -1), (48, 1), (44, 4), (-36, 5), (-44, 3)]
    c.drawPath(smooth_path(pts, close=True), paint(color, alpha))
    c.drawPath(path_from([(-40, -6), (-50, -22), (-42, -22), (-28, -6)], True), paint(color, alpha))  # 垂尾
    c.drawPath(path_from([(-6, 1), (-20, 12), (-12, 12), (8, 2)], True), paint(color, alpha * 0.85))  # 机翼
    c.drawPath(smooth_path([(26, -7), (30, -12), (36, -11), (40, -6)], False), paint(color, alpha))  # 747 驼峰
    c.restore()


def plane_top(c, x, y, s=1.0, color="#FFFFFF", alpha=1.0, heading=0.0):
    """俯视客机剪影（heading=0 朝上）。"""
    c.save()
    c.translate(x, y)
    c.rotate(heading)
    c.scale(s, s)
    body = path_from([(0, -30), (3, -26), (3, 20), (0, 28), (-3, 20), (-3, -26)], True)
    wing = path_from([(0, -6), (26, 6), (26, 10), (0, 4), (-26, 10), (-26, 6)], True)
    tail = path_from([(0, 18), (9, 25), (9, 27), (0, 24), (-9, 27), (-9, 25)], True)
    p = paint(color, alpha)
    c.drawPath(body, p)
    c.drawPath(wing, p)
    c.drawPath(tail, p)
    c.restore()


def to_array(surface):
    return surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]
