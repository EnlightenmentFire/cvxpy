# -*- coding: utf-8 -*-
"""逍遥津 竖屏渲染器（skia 矢量绘制，逐帧输出 BGRA 给 ffmpeg）。

用法：
  python3 render.py timeline <audio_dir>            生成 timeline.json
  python3 render.py frame <t> <out.png>             渲染单帧（检查用）
  python3 render.py chunk <k> <n> <out.mp4>         渲染第 k/n 段
"""
import json, math, os, random, re, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script_data import S

W, H, FPS = 1080, 1920, 25
CX, CY = 540, 760          # 舞台中心
LEAD = 0.45                # 片头留白（秒）

# ───────────────────────── 字体 ─────────────────────────
FD = '/usr/share/fonts/opentype/noto/'
TF = {
    'serif_black': skia.Typeface.MakeFromFile(FD + 'NotoSerifCJK-Black.ttc', 2),
    'serif_bold': skia.Typeface.MakeFromFile(FD + 'NotoSerifCJK-Bold.ttc', 2),
    'serif': skia.Typeface.MakeFromFile(FD + 'NotoSerifCJK-SemiBold.ttc', 2),
    'sans_bold': skia.Typeface.MakeFromFile(FD + 'NotoSansCJK-Bold.ttc', 2),
    'sans_black': skia.Typeface.MakeFromFile(FD + 'NotoSansCJK-Black.ttc', 2),
    'sans': skia.Typeface.MakeFromFile(FD + 'NotoSansCJK-Medium.ttc', 2),
}
_fc = {}


def F(name, size):
    k = (name, round(size, 1))
    if k not in _fc:
        f = skia.Font(TF[name], size)
        f.setSubpixel(True)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        _fc[k] = f
    return _fc[k]


# ───────────────────────── 颜色 ─────────────────────────
def hexc(h, a=1.0):
    h = h.lstrip('#')
    return skia.ColorSetARGB(int(255 * max(0, min(1, a))), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


C = dict(bg0='#081630', bg1='#0B2D45', ink='#F7F3EA', gold='#F6C35B', red='#FF5A3C', cyan='#38C6F4',
         mint='#4FD8A8', lilac='#B795FF', dim='#8FA3B8', card='#FBF7EF', cardink='#1B2433', vermil='#D9412B',
         water='#1E6F8F', land='#12324A')
PERSON = {'张辽': ('辽', C['red']), '李典': ('典', C['mint']), '乐进': ('进', C['lilac']), '薛悌': ('悌', C['gold']),
          '孙盛': ('盛', C['gold'])}


def P(col, a=1.0, stroke=0, blur=0, cap_round=True):
    p = skia.Paint(AntiAlias=True, Color=hexc(col, a) if isinstance(col, str) else col)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        if cap_round:
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ───────────────────────── 缓动 ─────────────────────────
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def sm(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def eo(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def seg01(x, a, b):
    return clamp((x - a) / (b - a)) if b > a else (1.0 if x >= b else 0.0)


# ───────────────────────── 绘图工具 ─────────────────────────
def text(c, s, x, y, font, col, a=1.0, align='c', shadow=0, stroke=0, stroke_col='#06101E', blur=0):
    w = font.measureText(s)
    if align == 'c':
        x -= w / 2
    elif align == 'r':
        x -= w
    if shadow:
        c.drawString(s, x, y + shadow * 0.4, font, P('#000000', 0.45 * a, blur=shadow))
    if stroke:
        sp = P(stroke_col, 0.9 * a, stroke=stroke)
        sp.setStrokeJoin(skia.Paint.kRound_Join)
        c.drawString(s, x, y, font, sp)
    c.drawString(s, x, y, font, P(col, a, blur=blur))
    return w


def text_hl(c, s, hl, x, y, font, col, hlcol, a=1.0, align='c', stroke=0, shadow=0):
    """一行文字，其中 hl 子串换色。"""
    w = font.measureText(s)
    if align == 'c':
        x0 = x - w / 2
    elif align == 'r':
        x0 = x - w
    else:
        x0 = x
    parts = []
    if hl and hl in s:
        i = s.index(hl)
        parts = [(s[:i], col), (hl, hlcol), (s[i + len(hl):], col)]
    else:
        parts = [(s, col)]
    xx = x0
    for t, cc in parts:
        if not t:
            continue
        text(c, t, xx, y, font, cc, a, align='l', stroke=stroke, shadow=shadow)
        xx += font.measureText(t)
    return w


def vtext(c, s, x, y, font, col, a=1.0, gap=1.08, reveal=1.0, blur=0):
    """竖排文字，x 为列中心，y 为首字顶部。"""
    sz = font.getSize()
    n = len(s)
    for i, ch in enumerate(s):
        r = clamp(reveal * n - i)
        if r <= 0:
            break
        yy = y + (i + 0.88) * sz * gap
        text(c, ch, x, yy - (1 - r) * 12, font, col, a * r, blur=blur)


def rrect(c, x, y, w, h, r, paint):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint)


def pill(c, s, x, y, font, fg, bg, a=1.0, pad=22, align='c', dot=None):
    w = font.measureText(s)
    sz = font.getSize()
    extra = (sz * 0.9) if dot else 0
    tw = w + pad * 2 + extra
    if align == 'c':
        x0 = x - tw / 2
    elif align == 'r':
        x0 = x - tw
    else:
        x0 = x
    h = sz * 1.75
    rrect(c, x0, y - h / 2, tw, h, h / 2, P(bg, a))
    if dot:
        c.drawCircle(x0 + pad + sz * 0.25, y, sz * 0.22, P(dot, a))
    text(c, s, x0 + pad + extra, y + sz * 0.36, font, fg, a, align='l')
    return tw


def polyline(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p


def smooth_path(pts):
    """Catmull-Rom 平滑折线。"""
    p = skia.Path()
    p.moveTo(*pts[0])
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    return p


def partial_path(path, frac):
    if frac >= 0.999:
        return path
    if frac <= 0:
        return skia.Path()
    meas = skia.PathMeasure(path, False)
    L = meas.getLength()
    out = skia.Path()
    meas.getSegment(0, L * frac, out, True)
    return out


def path_point(path, frac):
    meas = skia.PathMeasure(path, False)
    L = meas.getLength()
    r = meas.getPosTan(L * clamp(frac)) if L > 0 else None
    if not r:
        return None
    pos, tan = r
    return (pos.fX, pos.fY), (tan.fX, tan.fY)


def arrow(c, pts, col, a=1.0, width=10, frac=1.0, head=30, dash=None, glow=True, smooth=True):
    path = smooth_path(pts) if smooth and len(pts) > 2 else polyline(pts)
    sub = partial_path(path, frac)
    if glow:
        c.drawPath(sub, P(col, 0.35 * a, stroke=width * 2.4, blur=8))
    pp = P(col, a, stroke=width)
    if dash:
        pp.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    c.drawPath(sub, pp)
    if frac > 0.05 and head:
        pt = path_point(path, frac)
        if pt is None:
            return
        (x, y), (tx, ty) = pt
        ang = math.atan2(ty, tx)
        hp = skia.Path()
        hp.moveTo(x + math.cos(ang) * head * 0.6, y + math.sin(ang) * head * 0.6)
        hp.lineTo(x + math.cos(ang + 2.5) * head, y + math.sin(ang + 2.5) * head)
        hp.lineTo(x + math.cos(ang - 2.5) * head, y + math.sin(ang - 2.5) * head)
        hp.close()
        c.drawPath(hp, P(col, a))


def glow_dot(c, x, y, r, col, a=1.0, g=2.6):
    c.drawCircle(x, y, r * g, P(col, 0.18 * a, blur=r * 1.2))
    c.drawCircle(x, y, r, P(col, a))


def flag(c, x, y, col, label, a=1.0, s=1.0, wave=0.0):
    c.drawLine(x, y, x, y - 90 * s, P('#E8E2D0', a, stroke=4 * s))
    p = skia.Path()
    p.moveTo(x, y - 90 * s)
    p.cubicTo(x + 25 * s, y - (98 - 8 * wave) * s, x + 45 * s, y - (82 + 8 * wave) * s, x + 70 * s, y - 88 * s)
    p.lineTo(x + 70 * s, y - 48 * s)
    p.cubicTo(x + 45 * s, y - (42 + 8 * wave) * s, x + 25 * s, y - (58 - 8 * wave) * s, x, y - 50 * s)
    p.close()
    c.drawPath(p, P(col, a))
    text(c, label, x + 34 * s, y - 56 * s, F('serif_black', 30 * s), '#08162B', a)


def wall_box(c, x, y, w, h, col, a=1.0, label=None, lsize=40):
    rrect(c, x - w / 2, y - h / 2, w, h, 10, P(col, 0.12 * a))
    rrect(c, x - w / 2, y - h / 2, w, h, 10, P(col, a, stroke=6))
    # 垛口
    n = int(w / 34)
    for i in range(n):
        xx = x - w / 2 + 17 + i * (w - 34) / max(1, n - 1)
        c.drawRect(skia.Rect.MakeXYWH(xx - 6, y - h / 2 - 12, 12, 12), P(col, a))
    if label:
        text(c, label, x, y + lsize * 0.36, F('serif_black', lsize), col, a)


# ───────────────────────── 背景 ─────────────────────────
rng0 = random.Random(7)
PARTS = [(rng0.random() * W, rng0.random() * H, rng0.uniform(1.5, 3.5), rng0.uniform(8, 26), rng0.random() * 6.28)
         for _ in range(36)]


def background(c, t, sky='night', dim=0.0):
    top, bot = {'night': ('#071329', '#0C2B44'), 'dawn': ('#0E1E3C', '#2B3E5C'), 'noon': ('#0D2A4A', '#1F5B72'),
                'dark': ('#04080F', '#0A1726'), 'paper': ('#0B1D36', '#123A52')}.get(sky, ('#071329', '#0C2B44'))
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, H)], [hexc(top), hexc(bot)])
    p = skia.Paint(Shader=sh)
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # 光斑
    glows = [(C['gold'], 260 + 80 * math.sin(t * 0.21), 380 + 60 * math.cos(t * 0.17), 520, 0.16),
             (C['cyan'], 860 + 70 * math.cos(t * 0.13), 1050 + 90 * math.sin(t * 0.19), 600, 0.13),
             ('#FF7A59', 700 + 60 * math.sin(t * 0.11), 300, 380, 0.08)]
    if sky == 'dawn':
        glows.append(('#FF9A5A', 540, 1500, 900, 0.32))
    if sky == 'noon':
        glows.append(('#FFE7A0', 540, 200, 800, 0.22))
    if sky == 'dark':
        glows = [(C['cyan'], 540, 900, 600, 0.07)]
    for col, x, y, r, a in glows:
        sh = skia.GradientShader.MakeRadial((x, y), r, [hexc(col, a * (1 - dim)), hexc(col, 0)])
        c.drawCircle(x, y, r, skia.Paint(Shader=sh))
    # 漂浮微粒
    for (x, y, r, sp, ph) in PARTS:
        yy = (y - t * sp) % H
        xx = x + 12 * math.sin(t * 0.5 + ph)
        c.drawCircle(xx, yy, r, P('#CFE8FF', 0.22 * (0.6 + 0.4 * math.sin(t + ph)) * (1 - dim)))


# ───────────────────────── 时间线 ─────────────────────────
def build_timeline(audio_dir):
    man = json.load(open(os.path.join(audio_dir, 'manifest.json')))
    t = LEAD
    segs = []
    for m in man:
        s = S[m['i']]
        if m.get('chap'):
            d = s['dur']
            segs.append(dict(i=m['i'], start=t, speech=0, dur=d, chap=s['chap']))
        else:
            d = m['dur'] + m['gap']
            segs.append(dict(i=m['i'], start=t, speech=m['dur'], dur=d, file=m['file']))
        t += d
    total = t + 0.6
    # 子镜头切分：单幅不超过约 4 秒
    for sg in segs:
        d = sg['dur']
        n = max(1, int(math.ceil(d / 3.6))) if not sg.get('chap') else 1
        sg['shots'] = n
        sg['subs'] = [] if sg.get('chap') else split_subs(S[sg['i']]['t'], sg['speech'])
    tl = dict(total=total, segs=segs)
    json.dump(tl, open(os.path.join(HERE, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
    print('total', total, 'segments', len(segs))
    return tl


def split_subs(t, speech):
    """把旁白切成单行字幕（≤16 字），按字数分配时间。"""
    pieces = re.findall(r'[^，。：；？！]+[，。：；？！]?', t)
    lines = []
    cur = ''
    for pc in pieces:
        if len(cur) + len(pc.rstrip('，。：；')) <= 15 and cur:
            cur += pc
        else:
            if cur:
                lines.append(cur)
            cur = pc
    if cur:
        lines.append(cur)
    out = []
    for ln in lines:
        while len(ln) > 17:
            cut = 14
            out.append(ln[:cut])
            ln = ln[cut:]
        out.append(ln)
    weights = [len(re.sub(r'[，。：；？！“”、…（）·\s]', '', x)) + 1.2 * len(re.findall(r'[，。：；？！]', x)) for x in out]
    tot = sum(weights)
    res = []
    acc = 0
    for ln, w in zip(out, weights):
        d = speech * w / tot
        disp = ln.rstrip('，。：；')
        disp = disp.replace('，', ' ').replace('。', ' ').replace('：', '：')
        res.append((acc, acc + d, disp.strip()))
        acc += d
    return res


# ───────────────────────── 场景 ─────────────────────────
class Ctx:
    pass


def scene_dispatch(c, name, prm, x):
    fn = SCENES.get(name)
    if fn:
        fn(c, prm, x)


# ---------- 信（函） ----------
def draw_case(c, x, y, s, a=1.0, glow=1.0, label=True, t=0.0, label_reveal=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if glow > 0:
        c.drawRoundRect(skia.Rect.MakeXYWH(-200, -330, 400, 660), 30, 30, P(C['gold'], 0.22 * glow * a, blur=60))
    # 漆木函
    sh = skia.GradientShader.MakeLinear([(-170, -300), (170, 300)], [hexc('#E4523A', a), hexc('#A82A22', a)])
    c.drawRoundRect(skia.Rect.MakeXYWH(-170, -300, 340, 600), 22, 22, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawRoundRect(skia.Rect.MakeXYWH(-170, -300, 340, 600), 22, 22, P(C['gold'], a, stroke=6))
    c.drawRoundRect(skia.Rect.MakeXYWH(-150, -280, 300, 560), 14, 14, P('#FFD98A', 0.55 * a, stroke=2))
    # 绳与封泥
    c.drawRect(skia.Rect.MakeXYWH(-170, -16, 340, 32), P('#F3D9A0', 0.9 * a))
    c.drawRoundRect(skia.Rect.MakeXYWH(-46, -52, 92, 104), 10, 10, P('#3A2A22', a))
    c.drawRoundRect(skia.Rect.MakeXYWH(-46, -52, 92, 104), 10, 10, P(C['gold'], 0.6 * a, stroke=3))
    text(c, '封', 0, 22, F('serif_black', 60), '#F2C98A', a)
    # 函边题字条
    if label:
        c.drawRoundRect(skia.Rect.MakeXYWH(92, -270, 58, 250), 8, 8, P('#FBF3E2', a))
        vtext(c, '贼至乃发', 121, -268, F('serif_black', 50), '#1A1A1A', a, gap=0.98, reveal=label_reveal)
    c.restore()


JIAO_COLS = [('若孙权至者', C['cardink']), ('张李将军出战', C['vermil']), ('乐将军守护军', '#6B4FD8'), ('勿得与战', '#6B4FD8')]


def draw_slips(c, x, y, s, reveal=1.0, a=1.0, hl=None, blur=0, extra_blank=0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    ncol = 4 + extra_blank
    sw = 118
    tot = ncol * sw
    x0 = tot / 2
    # 竹简底
    c.drawRoundRect(skia.Rect.MakeXYWH(-x0 - 30, -400, tot + 60, 800), 18, 18, P('#000000', 0.35 * a, blur=30))
    for k in range(ncol):
        xx = x0 - (k + 0.5) * sw
        sh = skia.GradientShader.MakeLinear([(xx - sw / 2, 0), (xx + sw / 2, 0)], [hexc('#F7E7C3', a), hexc('#EDD6A6', a)])
        c.drawRoundRect(skia.Rect.MakeXYWH(xx - sw / 2 + 5, -380, sw - 10, 760), 12, 12, skia.Paint(AntiAlias=True, Shader=sh))
        c.drawLine(xx - sw / 2 + 5, -300, xx + sw / 2 - 5, -300, P('#B88A4A', 0.6 * a, stroke=3))
        c.drawLine(xx - sw / 2 + 5, 300, xx + sw / 2 - 5, 300, P('#B88A4A', 0.6 * a, stroke=3))
    for k, (s_, col) in enumerate(JIAO_COLS):
        xx = x0 - (k + 0.5) * sw
        r = clamp(reveal * 4 - k)
        if r <= 0:
            continue
        aa = a
        if hl is not None:
            aa = a * (1.0 if k in hl else 0.28)
            if k in hl:
                c.drawRoundRect(skia.Rect.MakeXYWH(xx - sw / 2 + 2, -385, sw - 4, 770), 14, 14, P(C['gold'], 0.9 * a, stroke=6))
        fs = 74 if len(s_) <= 5 else 66
        vtext(c, s_, xx, -360 + (6 - len(s_)) * 20, F('serif_black', fs), col, aa, gap=1.06, reveal=r, blur=blur)
    for k in range(4, ncol):
        xx = x0 - (k + 0.5) * sw
        rr = skia.Rect.MakeXYWH(xx - sw / 2 + 14, -360, sw - 28, 720)
        pp = P(C['vermil'], 0.8 * a, stroke=4)
        pp.setPathEffect(skia.DashPathEffect.Make([18, 12], 0))
        c.drawRoundRect(rr, 10, 10, pp)
        text(c, '？', xx, 30, F('serif_black', 90), C['vermil'], a)
    c.restore()


def sc_letter(c, prm, x):
    mode = prm.get('mode', 'closed')
    lt, d, j = x.lt, x.d, x.j
    u = lt / max(d, 0.1)
    fl = math.sin(x.t * 1.3)
    if mode == 'closed':
        s = 1.0 + 0.05 * u + (0.12 if j % 2 else 0)
        draw_case(c, CX + (j % 2) * 20, CY - 60 + 10 * fl, s, glow=0.7 + 0.3 * math.sin(x.t * 2), t=x.t,
                  label_reveal=eo(lt / 1.2) if x.first else 1)
        if prm.get('cap'):
            a = eo((lt - 0.4) / 0.6)
            text(c, prm['cap'], CX, 1180, F('serif_black', 74), C['gold'], a, stroke=6, shadow=12)
    elif mode == 'edge':
        s = 2.3 + 0.15 * u
        c.save()
        c.translate(CX, CY)
        c.rotate(-4 + 2 * u)
        draw_case(c, -270 * s / 2.3, 210, s, glow=0.4, label_reveal=eo(lt / 1.6))
        c.restore()
        if prm.get('cap'):
            a = eo((lt - 0.3) / 0.6)
            text(c, prm['cap'], CX, 1190, F('serif_black', 74), C['gold'], a, stroke=6, shadow=12)
    elif mode in ('open', 'blank'):
        draw_case(c, 210, 420, 0.42, a=0.9, glow=0.3)
        rev = 1.0 if (mode == 'blank' or prm.get('hlseq') or not x.first_seg_shot) else eo(lt / max(1.0, d * 0.75))
        hl = None
        if prm.get('hlseq'):
            hl = [1] if u < 0.5 else [2, 3]
        s = 1.0 + 0.04 * u
        if j % 2 == 1 and mode != 'blank':
            s = 1.22
        draw_slips(c, CX + 40, CY + 60, s * (0.86 if mode == 'blank' else 1.0), reveal=rev, hl=hl,
                   blur=8 if prm.get('blur') else 0, extra_blank=2 if mode == 'blank' else 0)
        if mode == 'blank':
            a = eo((lt - 0.5) / 0.5)
            text(c, '带多少人？怎么打？', CX, 1215, F('serif_black', 62), C['gold'], a, stroke=6)
    elif mode == 'fake':
        # 蒋济伪书
        c.save()
        c.translate(CX, CY)
        c.rotate(-3 + 2 * math.sin(x.t * 0.7))
        sc = 1.0 + 0.04 * u + (0.15 if j % 2 else 0)
        c.scale(sc, sc)
        rrect(c, -230, -380, 460, 760, 16, P('#000000', 0.4, blur=30))
        rrect(c, -230, -380, 460, 760, 16, P('#F4EAD5'))
        rrect(c, -210, -360, 420, 720, 10, P('#B88A4A', 0.6, stroke=3))
        vtext(c, '步骑四万', 90, -330, F('serif_black', 84), C['cardink'], 1, reveal=eo(lt / 1.0))
        vtext(c, '已到雩娄', -50, -330, F('serif_black', 84), C['cardink'], 1, reveal=eo((lt - 0.4) / 1.0))
        a = eo((lt - 1.4) / 0.4)
        if a > 0:
            c.save()
            c.translate(120, 250)
            c.rotate(-12)
            sc2 = 1.6 - 0.6 * a
            c.scale(sc2, sc2)
            rrect(c, -95, -95, 190, 190, 14, P(C['vermil'], 0.92 * a, stroke=10))
            text(c, '伪', 0, 50, F('serif_black', 140), C['vermil'], 0.92 * a)
            c.restore()
        c.restore()
        if prm.get('cap'):
            a = eo((lt - 0.4) / 0.6)
            text(c, prm['cap'], CX, 1200, F('serif_black', 70), C['gold'], a, stroke=6, shadow=10)
    elif mode == 'final':
        s = 1.12 + 0.08 * u
        draw_case(c, CX, CY - 40, s, glow=0.8 + 0.2 * math.sin(x.t * 1.5))
        a = eo((lt - 1.0) / 1.0)
        text(c, '贼 至 乃 发', CX, 1210, F('serif_black', 96), C['gold'], a, stroke=6, shadow=14)


# ---------- 城 / 围城 ----------
rngs = random.Random(3)
SIEGE_DOTS = []
for k in range(520):
    ang = rngs.uniform(0, 2 * math.pi)
    rad = rngs.uniform(230, 400)
    SIEGE_DOTS.append(dict(tx=math.cos(ang) * rad, ty=math.sin(ang) * rad * 0.9,
                           sx=rngs.uniform(-500, 500), sy=rngs.uniform(700, 1000), dl=rngs.uniform(0, 0.45)))


def sc_siege(c, prm, x):
    p0, p1 = prm.get('p', (0, 1))
    p = lerp(p0, p1, sm(x.lt / max(0.1, x.d * 0.9)))
    cx, cy = CX, CY - 20
    zoom = 1.0 + 0.05 * x.lt / max(1, x.d) + (0.18 if x.j % 2 else 0)
    c.save()
    c.translate(cx, cy)
    c.scale(zoom, zoom)
    # 城
    wall_box(c, 0, 0, 230, 190, C['red'], label='合肥', lsize=56)
    for dct in SIEGE_DOTS:
        q = clamp((p - dct['dl']) / (1 - dct['dl'] + 1e-6))
        q = eo(q)
        xx = lerp(dct['sx'], dct['tx'], q) + 3 * math.sin(x.t * 2 + dct['tx'])
        yy = lerp(dct['sy'], dct['ty'], q)
        c.drawCircle(xx, yy, 6, P(C['cyan'], 0.85))
    if prm.get('days'):
        n = int(clamp(x.lt / max(0.5, x.d * 0.85)) * 10) + 1
        for k in range(n):
            ang = -math.pi / 2 + k * 0.42
            c.drawCircle(math.cos(ang) * 175, math.sin(ang) * 155, 9, P(C['gold'], 0.95))
        txt = f'第{["一","二","三","四","五","六","七","八","九","十","十余"][min(n-1,10)]}天'
        text(c, txt, 0, -330, F('serif_black', 80), C['gold'], 1, stroke=6)
        # 攻城受挫
        for k in range(4):
            ph = (x.t * 0.8 + k * 0.25) % 1
            ang = k * 1.57 + 0.6
            r0 = lerp(330, 150, ph if ph < 0.6 else 0.6) + (0 if ph < 0.6 else (ph - 0.6) * 300)
            c.drawCircle(math.cos(ang) * r0, math.sin(ang) * r0, 10, P(C['cyan'], 0.9 * (1 - ph)))
    c.restore()
    a = eo((p - 0.6) / 0.3)
    if not prm.get('days'):
        text(c, '号称十万', CX, 1210, F('serif_black', 92), C['cyan'], a, stroke=6, shadow=10)


# ---------- 城门 ----------
def sc_gate(c, prm, x):
    mode = prm.get('mode')
    lt, d = x.lt, x.d
    night = mode == 'night'
    zoom = 1.0 + 0.04 * lt / max(1, d) + (0.12 if x.j % 2 else 0)
    c.save()
    c.translate(CX, CY - 150)
    c.scale(zoom, zoom)
    wc = '#2A4A66' if not night else '#1A2B40'
    rrect(c, -540, -60, 1080, 420, 0, P(wc))
    for i in range(16):
        c.drawRect(skia.Rect.MakeXYWH(-540 + i * 70, -100, 44, 44), P(wc))
    c.drawLine(-540, -60, 540, -60, P(C['gold'], 0.5, stroke=3))
    # 门洞
    rrect(c, -150, 60, 300, 300, 0, P('#06101E'))
    arch = skia.Path()
    arch.addArc(skia.Rect.MakeXYWH(-150, -90, 300, 300), 180, 180)
    c.drawPath(arch, P('#06101E'))
    if mode == 'close':
        o = 1 - eo(lt / 1.4)
    elif mode in ('out', 'two'):
        o = eo(lt / 1.0)
    else:
        o = 0.0
    dw = 150 * (1 - o)
    door = P('#8A3B22')
    c.drawRect(skia.Rect.MakeXYWH(-150, 60, dw, 300), door)
    c.drawRect(skia.Rect.MakeXYWH(150 - dw, 60, dw, 300), door)
    for k in range(4):
        for m in range(4):
            if dw > 30:
                c.drawCircle(-150 + dw * (0.2 + 0.2 * m), 100 + k * 70, 7, P(C['gold'], 0.8))
                c.drawCircle(150 - dw * (0.2 + 0.2 * m), 100 + k * 70, 7, P(C['gold'], 0.8))
    if mode == 'close':
        b = eo((lt - 1.3) / 0.4)
        if b > 0:
            c.drawRect(skia.Rect.MakeXYWH(-180, 180 - 200 * (1 - b), 360, 30), P(C['gold'], b))
        text(c, '关门死守？', 0, -260, F('serif_black', 90), C['ink'], eo((lt - 0.6) / 0.5), stroke=6)
    if mode == 'out':
        f = eo((lt - 0.5) / 1.2)
        arrow(c, [(0, 250), (0, 420), (0, 560)], C['red'], frac=f, width=26, head=70)
        text(c, '出去打', 0, -260, F('serif_black', 110), C['red'], eo((lt - 0.9) / 0.4), stroke=6)
    if mode == 'two':
        f = eo((lt - 0.4) / 1.6)
        for dx, nm in [(-70, '张辽'), (70, '李典')]:
            ch, col = PERSON[nm]
            yy = lerp(230, 470, f)
            glow_dot(c, dx * (1 + f), yy, 46, col)
            text(c, ch, dx * (1 + f), yy + 18, F('serif_black', 50), '#08162B')
            text(c, nm, dx * (1 + f) * 1.15, yy + 120, F('sans_bold', 40), col, f)
    if night:
        c.drawCircle(330, -330, 55, P('#FFF1C9', 0.95))
        c.drawCircle(330, -330, 130, P('#FFF1C9', 0.12, blur=40))
        for tx in (-300, 300):
            fl = 0.7 + 0.3 * math.sin(x.t * 9 + tx)
            c.drawCircle(tx, -10, 26 * fl, P('#FFB347', 0.9, blur=6))
            c.drawCircle(tx, -10, 90, P('#FFB347', 0.18 * fl, blur=40))
        # 招募榜
        a = eo((lt - 0.3) / 0.6)
        rrect(c, -170, -420, 340, 290, 14, P('#F3E2BE', a))
        rrect(c, -170, -420, 340, 290, 14, P(C['vermil'], a, stroke=6))
        text(c, '募', 0, -285, F('serif_black', 120), C['vermil'], a)
        text(c, '敢从之士', 0, -180, F('serif_black', 50), C['cardink'], a)
        for k in range(int(eo((lt - 0.8) / 2.0) * 24)):
            rr = random.Random(k)
            c.drawCircle(rr.uniform(-480, 480), rr.uniform(420, 560), 9, P(C['red'], 0.9))
    c.restore()


# ---------- 大字 ----------
def sc_bigtext(c, prm, x):
    lines = prm['lines']
    hl = prm.get('hl')
    lt, d, j = x.lt, x.d, x.j
    size = prm.get('size', 140)
    if prm.get('wm'):
        c.save()
        c.translate(CX + 120, CY - 40)
        c.rotate(-8 + 3 * math.sin(x.t * 0.3))
        text(c, prm['wm'], 0, 300, F('serif_black', 820), C['gold'], 0.06)
        c.restore()
    fsz = []
    for ln in lines:
        f = F('serif_black', size)
        w = f.measureText(ln)
        fsz.append(min(size, size * 940 / max(w, 1)))
    gap = 1.28
    tot = sum(fsz) * gap
    y0 = CY - tot / 2 + fsz[0] * 0.95
    zoom = 1.0 + 0.035 * lt / max(1, d)
    if j % 2 == 1:
        zoom *= 1.12
        rrect(c, 40, CY - tot / 2 - 50, 1000, tot + 100, 30, P(C['gold'], 0.10))
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    y = y0
    nl = len(lines)
    for k, ln in enumerate(lines):
        if prm.get('stagger'):
            st = k * (d * 0.8 / nl) if x.first_seg_shot else 0
            if j > 0:
                st = 0
        else:
            st = k * 0.18 if x.first_seg_shot else 0
        a = eo((lt - st) / 0.45)
        yy = y + (1 - a) * 40
        text_hl(c, ln, hl, CX, yy, F('serif_black', fsz[k]), C['ink'], C['gold'], a, stroke=5, shadow=12)
        y += fsz[k] * gap
    c.restore()
    if prm.get('src'):
        text(c, '——' + prm['src'], CX, y0 + tot + 10, F('sans', 34), C['dim'], eo((lt - 0.4) / 0.5))


# ---------- 原文卡 ----------
def wrap_cn(s, font, maxw):
    lines, cur = [], ''
    for ch in s:
        if font.measureText(cur + ch) > maxw and cur:
            if ch in '，。；：！？、”）':
                cur += ch
                lines.append(cur)
                cur = ''
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def sc_quote(c, prm, x):
    q = prm['q']
    hl = prm.get('hl', '')
    lt, d, j = x.lt, x.d, x.j
    big = prm.get('big')
    if j % 2 == 1 and (big or hl):
        # 大字强调
        phrase = big or hl
        f = F('serif_black', 200)
        w = f.measureText(phrase)
        sz = min(200, 200 * 960 / max(w, 1))
        a = eo(lt / 0.35)
        sc = 1.08 - 0.08 * eo(lt / 0.5) + 0.03 * lt / max(1, d)
        c.save()
        c.translate(CX, CY)
        c.scale(sc, sc)
        text(c, phrase, 0, sz * 0.35, F('serif_black', sz), C['gold'], a, stroke=6, shadow=18)
        c.restore()
        text(c, '——' + prm.get('src', ''), CX, CY + sz * 0.35 + 110, F('sans', 34), C['dim'], a)
        return
    f = F('serif_bold', 62 if len(q) < 40 else 56)
    lines = wrap_cn(q, f, 820)
    lh = f.getSize() * 1.6
    ch = len(lines) * lh + 170
    y0 = CY - ch / 2
    zoom = 1.0 + 0.04 * lt / max(1, d)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    ain = eo(lt / 0.3) if x.first_seg_shot else 1
    rrect(c, 70, y0 + 16, 940, ch, 26, P('#000000', 0.35 * ain, blur=28))
    rrect(c, 70, y0, 940, ch, 26, P(C['card'], ain))
    rrect(c, 70, y0, 12, ch, 6, P(C['vermil'], ain))
    pill(c, '原文', 120, y0 + 2, F('sans_bold', 28), '#FFFFFF', C['vermil'], ain, align='l')
    total_chars = len(q)
    rev = clamp(lt / max(0.8, min(2.2, d * 0.5))) if x.first_seg_shot else 1.0
    shown = int(rev * total_chars + 0.999)
    # 高亮位置
    hs = q.find(hl) if hl else -1
    he = hs + len(hl) if hs >= 0 else -1
    idx = 0
    y = y0 + 85 + f.getSize()
    for ln in lines:
        xx = 130
        for chh in ln:
            if idx >= shown:
                break
            col = C['cardink']
            if hs <= idx < he:
                col = C['vermil']
                wch = f.measureText(chh)
                hla = eo((lt - 0.2 - rev * 0.0) / 0.4) if x.first_seg_shot else 1
                c.drawRect(skia.Rect.MakeXYWH(xx - 2, y + 12, wch + 4, 8), P(C['gold'], 0.9 * hla))
            text(c, chh, xx, y, f, col, 1.0, align='l')
            xx += f.measureText(chh)
            idx += 1
        y += lh
    text(c, '——' + prm.get('src', ''), 970, y0 + ch - 36, F('sans', 32), '#6A7380', ain, align='r')
    c.restore()


# ---------- 人物 ----------
def medal(c, x, y, r, name, a=1.0, hl=True, role=None, note=None, t=0.0):
    ch, col = PERSON[name]
    aa = a if hl else a * 0.35
    c.drawCircle(x, y, r * 1.35, P(col, 0.16 * aa, blur=r * 0.5))
    c.drawCircle(x, y, r, P('#0C1E36', aa))
    c.drawCircle(x, y, r, P(col, aa, stroke=r * 0.07))
    c.drawCircle(x, y, r * 0.84, P(col, 0.5 * aa, stroke=2))
    text(c, ch, x, y + r * 0.36, F('serif_black', r * 1.02), col, aa)
    text(c, name, x, y + r + 66, F('sans_black', r * 0.42), C['ink'], aa)
    if role:
        rc = {'出战': C['red'], '守城': C['lilac'], '持教': C['gold']}.get(role, C['gold'])
        pill(c, role, x, y + r + 125, F('sans_bold', 40), '#08162B', rc, a=aa)
    if note:
        text(c, note, x, y + r + 140, F('sans_bold', 38), C['gold'], aa)


def jagged(c, x0, y0, x1, y1, t, a=1.0):
    n = 9
    pts = []
    rr = random.Random(int(t * 8))
    for k in range(n + 1):
        u = k / n
        px, py = lerp(x0, x1, u), lerp(y0, y1, u)
        if 0 < k < n:
            dx, dy = -(y1 - y0), (x1 - x0)
            L = math.hypot(dx, dy) + 1e-6
            off = rr.uniform(-18, 18)
            px += dx / L * off
            py += dy / L * off
        pts.append((px, py))
    c.drawPath(polyline(pts), P(C['red'], 0.35 * a, stroke=14, blur=6))
    c.drawPath(polyline(pts), P('#FF8A6A', a, stroke=4))


def sc_roster(c, prm, x):
    who = prm['who']
    lt, d, j = x.lt, x.d, x.j
    n = len(who)
    if n == 1:
        pos = [(CX, CY - 80)]
        r = 190
    elif n == 2:
        pos = [(CX - 230, CY - 40), (CX + 230, CY - 40)]
        r = 140
    elif n == 3:
        pos = [(CX, CY - 260), (CX - 260, CY + 150), (CX + 260, CY + 150)]
        r = 120
    else:
        pos = [(CX - 240, CY - 230), (CX + 240, CY - 230), (CX - 240, CY + 220), (CX + 240, CY + 220)]
        r = 110
    zoom = 1.0 + 0.04 * lt / max(1, d)
    if j % 2 == 1:
        zoom *= 1.1
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    if prm.get('letter'):
        draw_case(c, CX, 330, 0.28, glow=0.6)
        for (px, py) in pos:
            f = eo((lt - 0.3) / 0.8)
            arrow(c, [(CX, 430), (lerp(CX, px, f), lerp(430, py - r - 10, f))], C['gold'], 0.8, width=5, head=0, dash=[14, 10])
    if prm.get('feud') and n >= 2:
        a = eo((lt - 0.4) / 0.5)
        for i1 in range(n):
            for i2 in range(i1 + 1, n):
                (xa, ya), (xb, yb) = pos[i1], pos[i2]
                L = math.hypot(xb - xa, yb - ya)
                ux, uy = (xb - xa) / L, (yb - ya) / L
                jagged(c, xa + ux * (r + 20), ya + uy * (r + 20), xb - ux * (r + 20), yb - uy * (r + 20), x.t, a)
        text(c, '素不睦', CX, CY + (420 if n == 3 else 300), F('serif_black', 84), C['red'], a, stroke=6)
    roles = {'张辽': '出战', '李典': '出战', '乐进': '守城', '薛悌': '持教'}
    for k, (nm, (px, py)) in enumerate(zip(who, pos)):
        st = k * 0.15 if x.first_seg_shot else 0
        a = eo((lt - st) / 0.4)
        hl = (prm.get('hl') in (None, nm))
        role = None
        if prm.get('roles') or (prm.get('hl') == '薛悌' and nm == '薛悌'):
            ra = eo((lt - 0.5 - k * 0.3) / 0.4)
            role = roles.get(nm) if ra > 0.05 else None
        medal(c, px, py + (1 - a) * 30, r, nm, a, hl=hl, role=role, note=prm.get('note') if n == 1 else None, t=x.t)
    c.restore()


# ---------- 时间轴 ----------
def sc_timeline(c, prm, x):
    lt, d = x.lt, x.d
    anim = prm.get('anim')
    y = CY
    x0, x1 = 90, 990
    yr0, yr1 = 200, 222

    def X(yr):
        return lerp(x0, x1, (yr - yr0) / (yr1 - yr0))
    f = eo(lt / 0.8) if anim == 'in' else 1
    c.drawLine(x0, y, lerp(x0, x1, f), y, P(C['ink'], 0.8, stroke=5))
    for yr in range(yr0, yr1 + 1):
        if X(yr) > lerp(x0, x1, f):
            break
        h = 26 if yr % 5 == 0 else 12
        c.drawLine(X(yr), y - h, X(yr), y + h, P(C['ink'], 0.7, stroke=3))
        if yr % 5 == 0:
            text(c, f'{yr}', X(yr), y + 75, F('sans_bold', 34), C['dim'])
    zoom = 1.0 + (0.1 if x.j % 2 else 0)
    a208 = 1 if anim != 'in' else eo((lt - 0.8) / 0.5)
    ac = 1.0 if anim != 'to215' else 0.45
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    glow_dot(c, X(208), y, 20, C['cyan'], a208 * ac)
    text(c, '208', X(208), y - 230, F('serif_black', 100), C['cyan'], a208 * ac, stroke=5)
    text(c, '赤壁之年', X(208), y - 150, F('sans_bold', 42), C['ink'], a208 * ac)
    text(c, '第一次围合肥', X(208), y - 95, F('sans_bold', 38), C['dim'], a208 * ac)
    if anim == 'to215':
        f2 = eo((lt - 0.2) / 1.2)
        xx = lerp(X(208), X(215), f2)
        arrow(c, [(X(208), y + 150), (xx, y + 150)], C['gold'], width=8, head=26)
        text(c, '七年后', (X(208) + X(215)) / 2, y + 230, F('serif_black', 60), C['gold'], f2)
        a = eo((lt - 1.2) / 0.5)
        glow_dot(c, X(215), y, 26, C['red'], a)
        text(c, '215', X(215), y - 230, F('serif_black', 130), C['red'], a, stroke=5)
        text(c, '逍遥津', X(215), y - 140, F('sans_black', 48), C['ink'], a)
    if anim == 'mark208':
        a = eo((lt - 0.3) / 0.5)
        c.drawCircle(X(208), y, 60 + 30 * math.sin(x.t * 4), P(C['cyan'], 0.6 * a, stroke=4))
    c.restore()


# ---------- 全国示意图 ----------
def LL(lon, lat):
    return (540 + (lon - 112.5) * 72, 770 - (lat - 32.5) * 85)


RIV = {
    '长江': [(104.6, 28.8), (106.5, 29.6), (108.4, 30.8), (110.0, 31.0), (111.3, 30.7), (112.2, 30.3), (112.9, 29.8), (113.1, 29.4),
           (114.3, 30.6), (115.0, 30.2), (116.0, 29.7), (117.0, 30.5), (117.9, 31.0), (118.4, 31.3), (118.8, 32.1), (119.4, 32.2),
           (120.3, 31.9), (121.5, 31.4)],
    '汉水': [(106.5, 33.1), (107.0, 33.1), (108.0, 32.9), (109.0, 32.7), (110.8, 32.6), (111.7, 32.4), (112.1, 32.0), (112.6, 31.2),
           (113.3, 30.7), (114.3, 30.6)],
    '淮河': [(113.4, 32.4), (114.1, 32.3), (115.4, 32.4), (116.4, 32.5), (116.8, 32.6), (117.4, 32.9), (118.5, 33.1), (119.2, 33.6),
           (120.3, 34.2)],
    '黄河': [(110.3, 34.6), (111.5, 34.8), (112.4, 34.9), (113.6, 34.9), (114.3, 35.0), (115.0, 35.7), (115.9, 36.5), (116.6, 37.3),
           (117.6, 37.7), (118.5, 37.8)],
    '渭水': [(106.5, 34.4), (107.6, 34.35), (108.9, 34.3), (110.3, 34.6)],
    '湘水': [(113.0, 29.2), (112.9, 28.2), (112.9, 27.8), (112.6, 26.9), (111.6, 26.4)],
}
PLACE = {'汉中': (107.0, 33.1), '合肥': (117.3, 31.8), '陆口': (113.9, 29.85), '邺': (114.3, 36.3), '许': (113.8, 34.0),
         '长安': (108.9, 34.3), '建业': (118.8, 32.05)}


def draw_cnmap(c, t, reveal=1.0, a=1.0):
    for nm, pts in RIV.items():
        path = smooth_path([LL(*p) for p in pts])
        w = 9 if nm in ('长江', '黄河') else 6
        c.drawPath(partial_path(path, reveal), P('#4FB3E0', 0.25 * a, stroke=w * 2.6, blur=6))
        c.drawPath(partial_path(path, reveal), P('#7FD3F5', 0.85 * a, stroke=w))
    # 湖
    for (lon, lat, rx, ry) in [(112.6, 29.1, 55, 30), (117.6, 31.6, 30, 18)]:
        x, y = LL(lon, lat)
        c.drawOval(skia.Rect.MakeXYWH(x - rx, y - ry, rx * 2, ry * 2), P('#7FD3F5', 0.6 * a * reveal))
    lab = [('长江', 111.2, 30.1), ('淮河', 115.4, 32.75), ('汉水', 109.6, 33.15), ('黄河', 113.0, 35.35)]
    for nm, lon, lat in lab:
        x, y = LL(lon, lat)
        text(c, nm, x, y, F('sans_bold', 30), '#9EDCF7', 0.8 * a * reveal)


def place(c, nm, col, a=1.0, size=38, dy=-26, r=12, t=0.0, pulse=False):
    x, y = LL(*PLACE[nm])
    if pulse:
        c.drawCircle(x, y, r * (2 + (t * 1.5 % 1) * 3), P(col, 0.6 * (1 - t * 1.5 % 1) * a, stroke=3))
    glow_dot(c, x, y, r, col, a)
    text(c, nm, x, y + dy, F('sans_black', size), C['ink'], a, stroke=4)


def sc_cnmap(c, prm, x):
    show = prm.get('show')
    lt, d, j = x.lt, x.d, x.j
    u = lt / max(1, d)
    # 镜头
    focus = {'base': (112.5, 32.5, 1.0), 'cao_west': (110.5, 34.0, 1.08), 'split': (112.8, 29.3, 1.45),
             'sun_north': (115.8, 31.0, 1.25), 'dist': (112.2, 32.5, 1.0), 'dist2': (112.2, 32.5, 1.0)}[show]
    fx, fy = LL(focus[0], focus[1])
    z = focus[2] * (1 + 0.05 * u) * (1.15 if j % 2 else 1.0)
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-fx, -fy)
    rev = eo(lt / 1.6) if show == 'base' and x.first_seg_shot else 1
    draw_cnmap(c, x.t, rev)
    for nm in ('许', '建业'):
        place(c, nm, C['dim'], 0.8 * rev, size=30, r=8)
    place(c, '合肥', C['red'], rev, size=44, pulse=True, t=x.t)
    place(c, '汉中', C['gold'], rev, size=40)
    if show == 'cao_west':
        place(c, '邺', C['red'], 1, size=34, r=9)
        pts = [LL(114.3, 36.3), LL(112.4, 34.8), LL(108.9, 34.4), LL(107.3, 34.0), LL(107.0, 33.3)]
        arrow(c, pts, C['red'], frac=eo(lt / 2.2), width=12, head=36)
        text(c, '曹操 西征张鲁', LL(110.6, 35.6)[0], LL(110.6, 35.6)[1], F('serif_black', 54), C['red'], eo((lt - 0.8) / 0.5), stroke=5)
    if show == 'split':
        place(c, '陆口', C['cyan'], 1, size=34, r=9)
        pts = [LL(*p) for p in RIV['湘水']]
        pp = P(C['gold'], 0.95, stroke=7)
        pp.setPathEffect(skia.DashPathEffect.Make([20, 12], -x.t * 40))
        c.drawPath(partial_path(smooth_path(pts), eo(lt / 1.2)), pp)
        a = eo((lt - 0.8) / 0.5)
        text(c, '刘', LL(111.6, 27.8)[0], LL(111.6, 27.8)[1], F('serif_black', 80), '#F2A65A', a, stroke=5)
        text(c, '孙', LL(114.0, 27.8)[0], LL(114.0, 27.8)[1], F('serif_black', 80), C['cyan'], a, stroke=5)
        text(c, '以湘水为界', LL(112.8, 26.7)[0], LL(112.8, 26.7)[1], F('sans_bold', 38), C['gold'], a, stroke=4)
    if show == 'sun_north':
        place(c, '陆口', C['cyan'], 1, size=34, r=9)
        pts = [LL(113.9, 29.85), LL(115.0, 30.3), LL(116.3, 29.9), LL(117.2, 30.6), LL(117.9, 31.2), LL(117.6, 31.5), LL(117.35, 31.75)]
        arrow(c, pts, C['cyan'], frac=eo(lt / 2.4), width=12, head=36)
        text(c, '孙权', LL(116.0, 29.3)[0], LL(116.0, 29.3)[1], F('serif_black', 50), C['cyan'], eo((lt - 0.6) / 0.5), stroke=5)
    if show in ('dist', 'dist2'):
        a1, b1 = LL(*PLACE['汉中']), LL(*PLACE['合肥'])
        pp = P(C['gold'], 0.95, stroke=6)
        pp.setPathEffect(skia.DashPathEffect.Make([22, 14], -x.t * 30))
        f = eo(lt / 1.3) if show == 'dist' else 1
        c.drawLine(a1[0], a1[1], lerp(a1[0], b1[0], f), lerp(a1[1], b1[1], f), pp)
        mx, my = (a1[0] + b1[0]) / 2, (a1[1] + b1[1]) / 2
        text(c, '直线约一千公里', mx, my - 40, F('serif_black', 52), C['gold'], eo((lt - 0.8) / 0.5), stroke=5)
        if show == 'dist2':
            prog = 0.08 + 0.1 * u
            px, py = lerp(a1[0], b1[0], prog), lerp(a1[1], b1[1], prog)
            glow_dot(c, px, py, 14, C['red'])
            text(c, '救兵', px, py + 60, F('sans_black', 40), C['red'], 1, stroke=4)
            text(c, '来不及', b1[0] - 40, b1[1] + 90, F('serif_black', 60), C['red'], eo((lt - 0.8) / 0.5), stroke=5)
    c.restore()


# ---------- 合肥区域示意图 ----------
HF = dict(city=(470, 560), chao=(600, 880), wan=(240, 1080), ruxu=(800, 1130), jin=(560, 640))
HF_JIANG = [(-60, 1180), (200, 1150), (420, 1160), (640, 1150), (860, 1120), (1140, 1050)]
HF_HUAI = [(-60, 300), (250, 280), (500, 300), (760, 270), (1140, 230)]
HF_SHI = [(260, 420), (380, 500), (470, 600), (560, 650), (600, 760), (610, 840)]
HF_RUXU = [(700, 930), (760, 1010), (800, 1130)]


def draw_hfmap(c, t, a=1.0, reveal=1.0):
    for pts, w in [(HF_JIANG, 26), (HF_HUAI, 14), (HF_SHI, 9), (HF_RUXU, 9)]:
        path = partial_path(smooth_path(pts), reveal)
        c.drawPath(path, P('#4FB3E0', 0.25 * a, stroke=w * 2.4, blur=8))
        c.drawPath(path, P('#7FD3F5', 0.9 * a, stroke=w))
    x, y = HF['chao']
    c.drawOval(skia.Rect.MakeXYWH(x - 150, y - 80, 300, 160), P('#7FD3F5', 0.75 * a * reveal))
    text(c, '巢湖', x, y + 14, F('sans_black', 40), '#0B2D45', a * reveal)
    text(c, '长江', 300, 1230, F('sans_black', 40), '#9EDCF7', a * reveal)
    text(c, '淮河', 880, 230, F('sans_black', 40), '#9EDCF7', a * reveal)


def sc_hfmap(c, prm, x):
    show = prm.get('show')
    lt, d, j = x.lt, x.d, x.j
    u = lt / max(1, d)
    z = (1 + 0.05 * u) * (1.15 if j % 2 else 1.0)
    fx, fy = CX, CY
    if show == 'jin':
        z = 1.9 * (1 + 0.05 * u) * (1.12 if j % 2 else 1)
        fx, fy = HF['jin']
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-fx, -fy)
    rev = eo(lt / 1.4) if show == 'geo' and x.first_seg_shot else 1
    draw_hfmap(c, x.t, 1, rev)
    cx, cy = HF['city']
    wall_box(c, cx, cy, 110, 90, C['red'], label='合肥', lsize=34)
    if show in ('door', 'geo'):
        pass
    if show == 'door':
        arrow(c, [HF['ruxu'], (760, 1010), (650, 880), (560, 720), (500, 620)], C['cyan'], frac=eo(lt / 1.8), width=12, head=34)
        arrow(c, [(470, 500), (480, 330)], C['cyan'], 0.5, frac=eo((lt - 1.4) / 0.8), width=8, head=26, dash=[14, 10])
        a = eo((lt - 1.0) / 0.5)
        text(c, '北上必经', cx + 230, cy - 20, F('serif_black', 56), C['gold'], a, stroke=5)
    if show == 'empty':
        rr = random.Random(5)
        for k in range(60):
            sx, sy = rr.uniform(150, 900), rr.uniform(650, 1080)
            f = eo(clamp((lt - rr.uniform(0, 1.2)) / 1.8))
            yy = lerp(sy, 1280, f)
            c.drawCircle(sx, yy, 7, P('#E8E2D0', 0.8 * (1 - f * 0.8)))
        wall_box(c, *HF['wan'], 90, 70, C['red'], label='皖城', lsize=28)
        text(c, '江西遂虚', 560, 1020 - 0, F('serif_black', 60), C['gold'], eo((lt - 1.2) / 0.5), stroke=5)
    if show == 'wancheng':
        f = eo((lt - 0.3) / 0.6)
        wall_box(c, *HF['wan'], 90, 70, C['cyan'] if f > 0.5 else C['red'], label='皖城', lsize=28)
        flag(c, HF['wan'][0] + 30, HF['wan'][1] - 40, C['cyan'], '孙', f, 0.8, math.sin(x.t * 3))
        pr = (x.t * 0.8) % 1
        c.drawCircle(cx, cy, 80 + 120 * pr, P(C['red'], 0.7 * (1 - pr), stroke=4))
        text(c, '孤城', cx, cy - 110, F('serif_black', 70), C['red'], eo((lt - 0.9) / 0.5), stroke=5)
    if show == 'jin':
        jx, jy = HF['jin']
        pr = (x.t * 0.9) % 1
        c.drawCircle(jx + 10, jy + 15, 20 + 50 * pr, P(C['gold'], 0.8 * (1 - pr), stroke=3))
        # 桥
        c.drawLine(jx - 10, jy - 20, jx + 30, jy + 50, P('#E8D9B5', 1, stroke=8))
        a = eo((lt - 0.4) / 0.5)
        text(c, '逍遥津', jx + 120, jy + 10, F('serif_black', 40), C['gold'], a, stroke=4)
        text(c, '津 = 渡口', jx + 110, jy + 60, F('sans_bold', 24), C['ink'], a, stroke=3)
    c.restore()


# ---------- 兵力点阵 ----------
def sc_dots(c, prm, x):
    mode = prm['mode']
    lt, d, j = x.lt, x.d, x.j
    zoom = (1 + 0.04 * lt / max(1, d)) * (1.1 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    if mode in ('7000', '800'):
        bx, by = CX - 230, CY - 200
        for k in range(70):
            gx, gy = k % 10, k // 10
            px, py = bx + gx * 51, by + gy * 60
            a = eo((lt - k * 0.012) / 0.3) if (mode == '7000' and x.first_seg_shot) else 1
            col = C['red']
            r = 13
            if mode == '800' and k in (32, 33, 34, 35, 36, 37, 42, 43):
                f = eo((lt - 0.4) / 1.0)
                py -= 0
                px += 0
                col = C['gold']
                r = 13 + 4 * f
                c.drawCircle(px, py, r * 2.4, P(C['gold'], 0.25 * f, blur=10))
            elif mode == '800':
                col = C['red']
                a *= 0.45
            c.drawCircle(px, py, r, P(col, a))
        wall_box(c, CX, CY - 20, 640, 520, C['ink'], a=0.35)
        lab = '七千余人' if mode == '7000' else '八百'
        text(c, lab, CX, CY + 380, F('serif_black', 110), C['gold'] if mode == '800' else C['red'], eo((lt - 0.5) / 0.5), stroke=6)
        text(c, '每点 ≈ 100 人', CX, CY + 450, F('sans', 32), C['dim'], 0.8)
    else:
        # 七千 vs 十万
        for k in range(70):
            gx, gy = k % 7, k // 7
            c.drawCircle(110 + gx * 22, 520 + gy * 24, 8, P(C['red']))
        text(c, '七千余', 175, 830, F('serif_black', 64), C['red'], 1, stroke=5)
        n = int(1000 * (eo(lt / 1.6) if x.first_seg_shot else 1))
        for k in range(n):
            gx, gy = k % 32, k // 32
            c.drawCircle(318 + gx * 22, 420 + gy * 21, 7, P(C['cyan'], 0.9))
        text(c, '号称十万', 660, 1180, F('serif_black', 72), C['cyan'], eo((lt - 0.8) / 0.5), stroke=5)
        if mode == 'vs2':
            text(c, '换成你？', CX, 330, F('serif_black', 96), C['gold'], eo((lt - 0.6) / 0.4), stroke=6)
    c.restore()


# ---------- 推演链 ----------
CHAIN = ['趁敌未合', '出城逆击', '折其盛势', '以安众心', '然后可守']


def sc_chain(c, prm, x):
    a0, a1 = prm['upto']
    lt, d, j = x.lt, x.d, x.j
    check = prm.get('check')
    n = len(CHAIN)
    zoom = (1 + 0.03 * lt / max(1, d)) * (1.08 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    y0 = CY - 400
    step = 200
    if check or not x.first_seg_shot:
        shown = n
    else:
        shown = a0 + (a1 - a0) * clamp(lt / max(1.0, d * 0.8)) + 0.999
    for k, s_ in enumerate(CHAIN):
        a = clamp(shown - k)
        if a <= 0:
            continue
        a = eo(a)
        y = y0 + k * step
        col = C['red'] if k in (1, 2) else (C['lilac'] if k == 4 else C['gold'])
        rrect(c, CX - 300, y - 60, 600, 120, 60, P(col, 0.14 * a))
        rrect(c, CX - 300, y - 60, 600, 120, 60, P(col, a, stroke=5))
        text(c, s_, CX, y + 26, F('serif_black', 72), C['ink'], a)
        if k < n - 1 and shown > k + 1:
            arrow(c, [(CX, y + 66), (CX, y + step - 66)], C['ink'], 0.7, width=5, head=18, glow=False)
        if check:
            f = eo((lt - 0.3 - k * 0.25) / 0.3)
            if f > 0:
                pth = polyline([(CX + 330, y), (CX + 355, y + 25), (CX + 400, y - 30)])
                c.drawPath(partial_path(pth, f), P(C['mint'], 1, stroke=12))
    c.restore()


# ---------- 孙盛评 ----------
def sc_sunsheng(c, prm, x):
    mode = prm['mode']
    lt, d, j = x.lt, x.d, x.j
    u = lt / max(1, d)
    zoom = (1 + 0.04 * u) * (1.1 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    if mode == 'intro':
        medal(c, 0, -120, 190, '孙盛', 1)
        text(c, '东晋史学家', 0, 250, F('sans_bold', 48), C['ink'], eo((lt - 0.3) / 0.4))
        text(c, '为曹操的密教写过一段评', 0, 330, F('sans_bold', 44), C['dim'], eo((lt - 0.6) / 0.4))
    elif mode == 'scale':
        tilt = 10 * math.sin(x.t * 1.6)
        c.drawLine(0, -40, 0, 360, P(C['ink'], 0.8, stroke=10))
        c.drawPath(polyline([(-90, 360), (90, 360), (0, 300)]), P(C['ink'], 0.8))
        c.save()
        c.translate(0, -40)
        c.rotate(tilt)
        c.drawLine(-380, 0, 380, 0, P(C['gold'], 1, stroke=10))
        for sx, lab1, lab2, col in [(-1, '专任勇者', '好战生患', C['red']), (1, '专任怯者', '惧心难保', C['lilac'])]:
            px = sx * 330
            c.save()
            c.translate(px, 0)
            c.rotate(-tilt)
            c.drawLine(-80, 160, 0, 0, P(C['gold'], 0.8, stroke=3))
            c.drawLine(80, 160, 0, 0, P(C['gold'], 0.8, stroke=3))
            rrect(c, -150, 160, 300, 170, 24, P(col, 0.18))
            rrect(c, -150, 160, 300, 170, 24, P(col, 1, stroke=5))
            text(c, lab1, 0, 230, F('serif_black', 50), C['ink'])
            text(c, lab2, 0, 300, F('serif_black', 46), col, eo((lt - 0.6) / 0.4))
            c.restore()
        c.restore()
        text(c, '都不行', 0, -260, F('serif_black', 92), C['gold'], eo((lt - 1.4) / 0.4), stroke=6)
    elif mode == 'fangyuan':
        f = eo(lt / 1.0)
        sx = lerp(-330, -150, f)
        rrect(c, sx - 110, -230, 220, 220, 16, P(C['red'], 0.9))
        text(c, '方', sx, -85, F('serif_black', 130), '#08162B')
        cx2 = lerp(330, 150, f)
        c.drawCircle(cx2, -120, 112, P(C['mint'], 0.9))
        text(c, '圆', cx2, -75, F('serif_black', 130), '#08162B')
        a = eo((lt - 0.8) / 0.5)
        text(c, '推选方员', 0, 170, F('serif_black', 96), C['gold'], a, stroke=6)
        text(c, '参以同异', 0, 300, F('serif_black', 96), C['gold'], eo((lt - 1.2) / 0.5), stroke=6)
    elif mode == 'fuqi':
        f = eo(lt / 1.6)
        for side in (-1, 1):
            off = lerp(220, 0, f) * side
            c.save()
            c.translate(off, -60)
            p = skia.Path()
            if side < 0:
                p.moveTo(0, -200)
                p.lineTo(-150, -200)
                p.quadTo(-230, -200, -230, -110)
                p.lineTo(-230, 110)
                p.quadTo(-230, 200, -150, 200)
                p.lineTo(0, 200)
            else:
                p.moveTo(0, -200)
                p.lineTo(150, -200)
                p.quadTo(230, -200, 230, -110)
                p.lineTo(230, 110)
                p.quadTo(230, 200, 150, 200)
                p.lineTo(0, 200)
            for k in range(8):
                yy = 200 - k * 50
                p.lineTo(side * (-20 if k % 2 == 0 else 0) * -1 + (20 if k % 2 == 0 else 0) * 0, yy - 25)
                p.lineTo(0, yy - 50)
            p.close()
            col = C['gold']
            c.drawPath(p, P(col, 0.25))
            c.drawPath(p, P(col, 1, stroke=6))
            text(c, '符' if side < 0 else '契', side * 115, 40, F('serif_black', 120), col)
            c.restore()
        if f > 0.97:
            c.drawCircle(0, -60, 300, P(C['gold'], 0.25 * (0.5 + 0.5 * math.sin(x.t * 5)), blur=40))
        text(c, '若合符契', 0, 320, F('serif_black', 100), C['gold'], eo((lt - 1.4) / 0.5), stroke=6)
    c.restore()


# ---------- 断句对照 ----------
def sc_twocut(c, prm, x):
    lt, d, j = x.lt, x.d, x.j
    zoom = (1 + 0.03 * lt / max(1, d)) * (1.08 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    rows = [('《张辽传》', ['乐将军', '守护军', '，勿得与战']), ('《资治通鉴》', ['乐将军', '守', '，护军勿得与战'])]
    for k, (src, parts) in enumerate(rows):
        y = CY - 220 + k * 380
        a = eo((lt - k * 0.8) / 0.5)
        text(c, src, CX, y - 90, F('sans_black', 46), C['dim'], a)
        f = F('serif_black', 76)
        tot = sum(f.measureText(p) for p in parts) + 30 * (len(parts) - 1)
        xx = CX - tot / 2
        for m, p in enumerate(parts):
            w = f.measureText(p)
            col = C['ink']
            if m == 0 or (k == 1 and m == 1) or (k == 0 and m == 1):
                col = C['lilac'] if m < 2 else C['ink']
            rrect(c, xx - 10, y - 70, w + 20, 100, 16, P(col, 0.15 * a))
            text(c, p, xx, y, f, col, a, align='l')
            xx += w + 30
        hl = eo((lt - 2.2) / 0.5)
        if hl > 0:
            text(c, '乐进：守', CX, CY + 470, F('serif_black', 90), C['gold'], hl, stroke=6)
    c.restore()


# ---------- 战斗（出城逆击） ----------
rb = random.Random(11)
BLUE = [(rb.uniform(80, 1000), rb.uniform(330, 980)) for _ in range(560)]
BLUE = [(bx, by) for (bx, by) in BLUE if not (440 < bx < 640 and by > 900)]
RED_OFF = []
for k in range(80):
    row = int((math.sqrt(8 * k + 1) - 1) / 2)
    col = k - row * (row + 1) // 2
    RED_OFF.append(((col - row / 2) * 22, row * 20))
GATE = (540, 1110)
BANNER0 = (560, 600)
HILL = (640, 470)


def battle_state(p):
    """返回红队中心、孙权位置等。"""
    if p < 1:
        rc = (GATE[0], GATE[1] + 40 * (1 - p))
    elif p < 2:
        q = sm(p - 1)
        rc = (lerp(GATE[0], BANNER0[0], q), lerp(GATE[1] - 20, BANNER0[1] + 70, q))
    elif p < 4:
        rc = (BANNER0[0], BANNER0[1] + 70)
    elif p < 5:
        rc = (BANNER0[0], BANNER0[1] + 70)
    elif p < 6:
        rc = (BANNER0[0], BANNER0[1] + 70 + 200 * sm((p - 5.5) / 0.5))
    else:
        rc = (lerp(BANNER0[0], GATE[0], sm(p - 6)), lerp(BANNER0[1] + 270, GATE[1] - 40, sm(p - 6)))
    if p < 2:
        sq = (BANNER0[0], BANNER0[1])
    else:
        q = sm((p - 2) / 0.8)
        sq = (lerp(BANNER0[0], HILL[0], q), lerp(BANNER0[1], HILL[1], q))
    return rc, sq


def sc_battle(c, prm, x):
    p0, p1 = prm['p']
    lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.92)))
    rc, sq = battle_state(p)
    # 镜头
    if prm.get('zoomout'):
        z = lerp(1.5, 0.95, eo(lt / 1.6))
        fx, fy = lerp(rc[0], CX, eo(lt / 1.6)), lerp(rc[1], CY, eo(lt / 1.6))
    else:
        z = 1.0 + 0.05 * lt / max(1, d)
        fx, fy = CX, CY
        if j % 2 == 1:
            z = 1.45
            fx, fy = rc[0], rc[1] - 60
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-fx, -fy - 75)
    # 地面
    rrect(c, 40, 300, 1000, 900, 40, P('#0F2C3F', 0.6))
    # 高冢
    for k in range(4):
        c.drawOval(skia.Rect.MakeXYWH(HILL[0] - 150 + k * 30, HILL[1] - 80 + k * 18, 300 - k * 60, 170 - k * 36),
                   P('#C9A46A', 0.18 + 0.08 * k))
    hl = eo((p - 2.1) / 0.4)
    if hl > 0:
        text(c, '高冢', HILL[0] + 150, HILL[1] - 70, F('serif_black', 44), '#E8C98A', hl, stroke=4)
    # 城墙
    c.drawRect(skia.Rect.MakeXYWH(40, 1120, 1000, 70), P('#2A4A66'))
    for i in range(14):
        c.drawRect(skia.Rect.MakeXYWH(50 + i * 72, 1098, 40, 24), P('#2A4A66'))
    go = eo(clamp((p - 0.3) / 0.6))
    c.drawRect(skia.Rect.MakeXYWH(GATE[0] - 70, 1120, 140, 70), P('#06101E'))
    c.drawRect(skia.Rect.MakeXYWH(GATE[0] - 70, 1120, 70 * (1 - go), 70), P('#8A3B22'))
    c.drawRect(skia.Rect.MakeXYWH(GATE[0] + 70 - 70 * (1 - go), 1120, 70 * (1 - go), 70), P('#8A3B22'))
    text(c, '合肥城', 200, 1170, F('sans_black', 36), C['ink'], 0.8)
    # 吴军
    ring_a = eo(clamp(p - 3))
    ring_open = eo(clamp((p - 5.5) / 0.5)) * (1 - eo(clamp(p - 6.3)))
    recoil = eo(clamp(p - 6))
    for k, (bx, by) in enumerate(BLUE):
        xx, yy = bx, by
        # 被冲开
        dx, dy = xx - rc[0], yy - rc[1]
        dist = math.hypot(dx, dy) + 1e-3
        if 1 <= p < 3 and dist < 130:
            push = (130 - dist) * 0.9
            xx += dx / dist * push
            yy += dy / dist * push
        if 2 <= p < 3.2 and k % 3 == 0:
            xx += 14 * math.sin(x.t * 7 + k)
            yy += 14 * math.cos(x.t * 6 + k)
        # 包围
        if k % 2 == 0 and ring_a > 0:
            ang = k * 0.137
            rad = 115 + (k % 5) * 22
            tx, ty = rc[0] + math.cos(ang) * rad, rc[1] + math.sin(ang) * rad
            if ring_open > 0 and math.sin(ang) > 0.3:
                tx += math.cos(ang) * 160 * ring_open
                ty += 60 * ring_open
            xx, yy = lerp(xx, tx, ring_a), lerp(yy, ty, ring_a)
        if recoil > 0:
            yy -= 260 * recoil * (0.5 + 0.5 * ((k * 37) % 10) / 10)
        c.drawCircle(xx, yy, 6.5, P(C['cyan'], 0.85 * (1 - 0.4 * recoil)))
    # 孙权
    flag(c, sq[0], sq[1], C['cyan'], '孙', 1, 0.9, math.sin(x.t * 3))
    # 红队
    out = eo(clamp(p - 4))
    back = eo(clamp(p - 5))
    vis = eo(clamp((p - 0.6) / 0.4))
    for k, (ox, oy) in enumerate(RED_OFF):
        xx, yy = rc[0] + ox, rc[1] + oy * (1 if p < 2 else 0.8)
        if 3 <= p < 6:
            ang = k * 0.61
            xx, yy = rc[0] + math.cos(ang) * (8 + k * 0.9), rc[1] + math.sin(ang) * (8 + k * 0.9)
        if k < 14 and 4 <= p < 5.6:
            xx += 0
            yy += 230 * out * (1 - back)
        if p < 1:
            yy = max(yy, 0) + 30 * (1 - vis)
        c.drawCircle(xx, yy, 7.5, P(C['red'], vis))
    # 张辽
    lx, ly = rc[0], rc[1] - 22
    if 4 <= p < 5.6:
        ly += 230 * out * (1 - back)
    if vis > 0:
        glow_dot(c, lx, ly, 13, '#FFD0A0', vis)
        text(c, '张辽', lx + 70, ly - 20, F('sans_black', 34), C['red'], vis, stroke=4)
    if 1 <= p < 2.05:
        arrow(c, [(GATE[0], GATE[1] - 20), (lerp(GATE[0], rc[0], 0.5), lerp(GATE[1], rc[1], 0.5) + 10), (rc[0], rc[1] + 40)],
              C['red'], 0.55, width=9, head=0)
    c.restore()
    # 太阳
    if prm.get('sky') == 'noon' or p > 6:
        sp = clamp(lt / max(1, d))
        sx, sy = lerp(980, 830, sp), lerp(380, 260, sp)
        c.drawCircle(sx, sy, 46, P('#FFE7A0', 0.95))
        c.drawCircle(sx, sy, 130, P('#FFE7A0', 0.15, blur=40))
        text(c, '天亮 → 日中', CX, 330, F('serif_black', 64), C['gold'], eo(lt / 0.6), stroke=5)
    if prm.get('word'):
        a = eo((lt - 0.25) / 0.35)
        sc = 1.25 - 0.25 * a
        c.save()
        c.translate(CX, 1225)
        c.scale(sc, sc)
        text(c, prm['word'], 0, 0, F('serif_black', 88), C['gold'], a, stroke=7, shadow=14)
        c.restore()


# ---------- 撤军 ----------
ROAD = [(470, 600), (520, 640), (560, 700), (600, 790), (620, 860), (640, 960), (700, 1080), (780, 1200), (900, 1330)]
RIVER_Y = 820
BRIDGE_X = 615
rr_ = random.Random(21)
COL = [rr_.random() for _ in range(420)]


def sc_retreat(c, prm, x):
    p0, p1 = prm['p']
    lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.92)))
    z = 1.0 + 0.05 * lt / max(1, d)
    fx, fy = CX, CY
    if (j % 2 == 1 or p > 3.5) and not prm.get('wall'):
        z = 1.5
        fx, fy = BRIDGE_X, RIVER_Y - 60
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-fx, -fy)
    # 地
    rrect(c, 20, 280, 1040, 980, 40, P('#0F2C3F', 0.55))
    # 河
    rp = smooth_path([(0, 760), (250, 790), (BRIDGE_X, RIVER_Y), (850, 840), (1080, 880)])
    c.drawPath(rp, P('#4FB3E0', 0.3, stroke=110, blur=10))
    c.drawPath(rp, P('#2B8CC0', 0.95, stroke=70))
    for k in range(6):
        ph = (x.t * 0.15 + k / 6) % 1
        px = ph * 1080
        c.drawLine(px, 772 + px * 0.1, px + 40, 776 + px * 0.1, P('#BFE9FF', 0.5, stroke=3))
    text(c, '津北', 300, 700, F('sans_black', 38), C['ink'], 0.8, stroke=3)
    text(c, '津南', 300, 930, F('sans_black', 38), C['ink'], 0.8, stroke=3)
    # 桥
    c.drawRect(skia.Rect.MakeXYWH(BRIDGE_X - 22, RIVER_Y - 70, 44, 140), P('#C9A46A'))
    gap = eo(clamp((p - 3.6) / 0.4))
    if gap > 0:
        c.drawRect(skia.Rect.MakeXYWH(BRIDGE_X - 22, RIVER_Y + 10, 44, 60 * gap), P('#2B8CC0'))
        pp = P(C['gold'], gap, stroke=3)
        pp.setPathEffect(skia.DashPathEffect.Make([8, 6], 0))
        c.drawRect(skia.Rect.MakeXYWH(BRIDGE_X - 22, RIVER_Y + 10, 44, 60), pp)
        text(c, '丈余无版', BRIDGE_X + 150, RIVER_Y + 60, F('serif_black', 40), C['gold'], gap, stroke=4)
    text(c, '逍遥津', BRIDGE_X + 150, RIVER_Y - 10, F('serif_black', 40), '#BFE9FF', 0.9, stroke=4)
    # 合肥
    wall_box(c, 330, 470, 210, 170, C['red'], label='合肥', lsize=46)
    # 吴军：p<1 围城环 → 长列
    roadp = smooth_path(ROAD)
    form = eo(clamp(p))
    adv = 0.25 + 0.6 * clamp(p / 2)
    for k, r in enumerate(COL):
        ang = r * 6.283
        ringx, ringy = 330 + math.cos(ang) * 190, 470 + math.sin(ang) * 160
        rear = k < 36
        if rear:
            s_ = 0.12 + 0.03 * (k % 6)
        else:
            s_ = clamp(0.2 + r * 0.8 * adv + adv * 0.4)
        (lx, ly), _ = path_point(roadp, s_)
        lx += ((k * 7) % 9 - 4) * 5
        xx, yy = lerp(ringx, lx, form), lerp(ringy, ly, form)
        if rear and p > 2.6:
            # 被冲散/挤向桥
            xx = lerp(xx, BRIDGE_X + ((k * 13) % 11 - 5) * 10, eo(clamp((p - 2.6) / 1.2)) * 0.5)
        c.drawCircle(xx, yy, 6.5, P(C['cyan'], 0.9))
    # 墙→线
    if prm.get('wall'):
        a = eo(lt / 0.5)
        pp = P(C['cyan'], 0.5 * a, stroke=4)
        pp.setPathEffect(skia.DashPathEffect.Make([10, 10], 0))
        c.drawOval(skia.Rect.MakeXYWH(140, 310, 380, 320), pp)
        text(c, '墙', 150, 300, F('serif_black', 70), C['cyan'], a, stroke=5)
        text(c, '线', 830, 1080, F('serif_black', 70), C['cyan'], eo((lt - 1.0) / 0.5), stroke=5)
    # 孙权位置
    if p < 3.8:
        sq = path_point(roadp, 0.15)[0]
    elif p < 4.5:
        q = sm((p - 3.8) / 0.7)
        sq = (BRIDGE_X, lerp(RIVER_Y - 90, RIVER_Y + 120, q))
    else:
        sq = (BRIDGE_X, RIVER_Y + 120)
    jump = 0
    if 3.8 <= p < 4.5:
        q = (p - 3.8) / 0.7
        jump = math.sin(math.pi * clamp((q - 0.35) / 0.4)) * 40 if 0.35 < q < 0.75 else 0
    flag(c, sq[0] - 10, sq[1] - jump, C['cyan'], '孙', 1, 0.8, math.sin(x.t * 3))
    if p >= 2.0 and p < 4.2:
        text(c, '孙权', sq[0] - 90, sq[1] + 10, F('sans_black', 30), C['cyan'], 1, stroke=3)
    # 张辽突袭
    if p > 2.0:
        f = eo(clamp(p - 2.0))
        tx, ty = sq[0] - 40, sq[1] - 40
        arrow(c, [(390, 560), (460, 620), (lerp(430, tx, f), lerp(600, ty, f))], C['red'], 0.9, width=11, head=30)
        for k in range(50):
            ang = k * 0.9
            rad = 40 + (k % 5) * 16
            cx2, cy2 = lerp(400, tx - 60, f), lerp(580, ty - 30, f)
            c.drawCircle(cx2 + math.cos(ang) * rad, cy2 + math.sin(ang) * rad * 0.6, 6.5, P(C['red'], 0.95))
        pass
    # 凌统
    if 2.9 < p < 4.2:
        a = eo(clamp((p - 2.9) / 0.3))
        lx, ly = sq[0] - 70, sq[1] - 50
        glow_dot(c, lx, ly, 12, C['cyan'], a)
        text(c, '凌统 三百人', lx - 20, ly - 30, F('sans_black', 28), C['cyan'], a, stroke=3, align='r')
    # 贺齐
    if p > 4.2:
        a = eo(clamp((p - 4.2) / 0.4))
        for k in range(40):
            c.drawCircle(BRIDGE_X - 120 + (k % 10) * 26, RIVER_Y + 170 + (k // 10) * 24, 6.5, P('#7FE0FF', a))
        text(c, '贺齐 三千人', BRIDGE_X + 230, RIVER_Y + 230, F('sans_black', 36), '#7FE0FF', a, stroke=3)
    c.restore()
    if 2.05 < p < 3.0:
        text(c, '奄至', CX, 1225, F('serif_black', 90), C['red'], eo(clamp((p - 2.1) / 0.3)), stroke=7, shadow=12)
    if p < 0.9 and prm.get('p')[0] < 0.1:
        text(c, '撤军', CX, 1215, F('serif_black', 88), C['cyan'], eo((lt - 0.4) / 0.4), stroke=6)


# ---------- 桥（侧视） ----------
def sc_bridge(c, prm, x):
    p0, p1 = prm['p']
    lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d * 0.9)))
    dark = prm.get('dark')
    z = (1 + 0.05 * lt / max(1, d)) * (1.18 if j % 2 else 1)
    fx = 600 if j % 2 else CX
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-fx, -CY)
    # 水
    for k in range(7):
        y = 930 + k * 45
        pts = [(xx, y + 8 * math.sin(xx * 0.02 + x.t * 1.6 + k)) for xx in range(-40, 1130, 40)]
        c.drawPath(smooth_path(pts), P('#4FB3E0', (0.55 - k * 0.05) * (0.5 if dark else 1), stroke=4))
    # 桥墩
    for bx in (220, 480, 700, 900):
        c.drawRect(skia.Rect.MakeXYWH(bx - 18, 790, 36, 220), P('#6B4A2A', 0.9 if not dark else 0.5))
    # 桥面
    gap0, gap1 = 700, 840
    broken = prm.get('broken')
    for k in range(40):
        x0 = 80 + k * 22
        if x0 > 960:
            break
        if gap0 <= x0 < gap1:
            continue
        if broken and 560 <= x0 < 700 and k % 3:
            continue
        c.drawRect(skia.Rect.MakeXYWH(x0, 770, 19, 26), P('#D8B47A', 0.95 if not dark else 0.45))
    c.drawLine(80, 770, gap0, 770, P('#E8D9B5', 0.6, stroke=3))
    c.drawLine(gap1, 770, 960, 770, P('#E8D9B5', 0.6, stroke=3))
    # 缺口
    ga = 0.6 + 0.4 * math.sin(x.t * 4)
    c.drawRect(skia.Rect.MakeXYWH(gap0, 760, gap1 - gap0, 50), P(C['gold'], 0.18 * ga, blur=10))
    pp = P(C['gold'], 0.9, stroke=3)
    pp.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
    c.drawRect(skia.Rect.MakeXYWH(gap0, 770, gap1 - gap0, 26), pp)
    text(c, '津北', 130, 720, F('sans_black', 40), C['ink'], 0.8)
    text(c, '津南', 950, 720, F('sans_black', 40), C['ink'], 0.8)
    if prm.get('measure'):
        a = eo(lt / 0.5)
        c.drawLine(gap0, 860, gap1, 860, P(C['gold'], a, stroke=4))
        c.drawLine(gap0, 840, gap0, 880, P(C['gold'], a, stroke=4))
        c.drawLine(gap1, 840, gap1, 880, P(C['gold'], a, stroke=4))
        text(c, '一丈 ≈ 2.3 米', (gap0 + gap1) / 2, 930, F('serif_black', 50), C['gold'], a, stroke=5)
    # 孙权（骑马标记）
    if not broken:
        if p < 0.55:
            q = p / 0.55
            bx = lerp(120, gap0 - 30, sm(q))
            by = 740
        elif p < 0.6:
            bx, by = gap0 - 30, 740
        else:
            q = sm((p - 0.6) / 0.4)
            bx = lerp(gap0 - 30, gap1 + 60, q)
            by = 740 - math.sin(math.pi * q) * 150
        if dark and p0 >= 0.7:
            pass
        aa = 0.55 if dark else 1
        # 拖尾
        for k in range(6):
            c.drawCircle(bx - 18 * k, by + (6 * k if p > 0.6 else 0), 16 - 2 * k, P(C['cyan'], 0.15 * aa))
        glow_dot(c, bx, by, 18, C['cyan'], aa)
        flag(c, bx - 4, by - 10, C['cyan'], '孙', aa, 0.7, math.sin(x.t * 4))
        if p > 0.5 and not dark:
            gx = bx - 70 if p < 0.6 else gap0 - 110
            glow_dot(c, gx, 742, 11, '#7FE0FF', 1)
            text(c, '谷利', gx - 10, 700, F('sans_black', 30), '#7FE0FF', 1, stroke=3)
            if 0.58 < p < 0.7:
                c.drawLine(gx + 10, 730, bx - 20, by - 5, P(C['gold'], 1, stroke=4))
    else:
        text(c, '桥败路绝', CX, 640, F('serif_black', 80), C['gold'], eo(lt / 0.6), stroke=6)
        # 潜行的凌统
        q = clamp(lt / max(1, d))
        glow_dot(c, lerp(500, 820, q), 905 + 4 * math.sin(x.t * 3), 11, C['cyan'], 0.9)
        text(c, '凌统', lerp(500, 820, q), 980, F('sans_black', 32), C['cyan'], 0.9, stroke=3)
    c.restore()
    if prm.get('word'):
        a = eo((lt - 0.3) / 0.35)
        text(c, prm['word'], CX, 1225, F('serif_black', 90), C['gold'], a, stroke=7, shadow=14)
    if dark and not broken and p0 < 0.5:
        text(c, '十几天后', CX, 470, F('serif_black', 80), C['ink'], eo((lt - 0.8) / 0.6) * 0.9, stroke=5)


# ---------- 文献层 ----------
LAYERS = [('魏略', '鱼豢 · 三国魏', 'ghost'), ('三国志 正文', '陈寿 · 西晋', 'zw'), ('裴松之注', '南朝宋 · 429年', 'pz'),
          ('蒙求', '唐', 'mq'), ('太平御览', '北宋 · 983年', 'yl'), ('资治通鉴', '北宋 · 1084年', 'tj'), ('三国演义', '元末明初', 'yy')]


def sc_layers(c, prm, x):
    mode = prm['mode']
    lt, d, j = x.lt, x.d, x.j
    zoom = (1 + 0.03 * lt / max(1, d)) * (1.08 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    c.translate(-CX, -CY)
    n = len(LAYERS)
    bh = 118
    y_bot = CY + 430
    marks = {}
    hl = set()
    if mode == 'jbz':
        hl = {'pz'}
    elif mode == 'none3':
        marks = {'zw': '✕', 'tj': '✕'}
        hl = {'zw', 'tj'}
    elif mode == 'yulan':
        marks = {'zw': '✕', 'tj': '✕', 'yl': '✓'}
        hl = {'yl'}
    elif mode == 'weilue':
        hl = {'ghost', 'yl'}
        marks = {'yl': '✓'}
    elif mode == 'rise':
        hl = {'ghost', 'mq', 'yy'}
    for k, (nm, sub, key) in enumerate(LAYERS):
        y = y_bot - k * (bh + 14)
        a = eo((lt - k * 0.08) / 0.4) if x.first_seg_shot else 1
        on = key in hl
        col = C['gold'] if on else C['dim']
        if key == 'ghost':
            pp = P(col, a * (1 if on else 0.6), stroke=4)
            pp.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
            rrect(c, 120, y - bh / 2, 840, bh, 20, pp)
            text(c, '已佚', 900, y + 14, F('sans_bold', 34), C['red'], a, align='r')
        else:
            rrect(c, 120, y - bh / 2, 840, bh, 20, P(col, (0.22 if on else 0.08) * a))
            rrect(c, 120, y - bh / 2, 840, bh, 20, P(col, a * (1 if on else 0.4), stroke=3))
        text(c, nm, 160, y + 16, F('serif_black', 54), C['ink'] if on else '#9DB0C4', a, align='l')
        text(c, sub, 600, y + 12, F('sans', 32), C['ink'] if on else C['dim'], a * 0.9, align='l')
        if key in marks:
            mk = marks[key]
            ma = eo((lt - 0.6 - k * 0.15) / 0.3)
            text(c, mk, 930, y + 22, F('sans_black', 70), C['red'] if mk == '✕' else C['mint'], ma, align='r')
        if mode == 'jbz' and key == 'pz':
            pill(c, '引《江表传》：故事性较强', CX, 300, F('sans_black', 36), '#08162B', C['gold'], eo((lt - 0.5) / 0.4))
        if mode == 'yulan' and key == 'yl':
            pill(c, '卷四百八十八 · 人事部 · 泣', CX, 300, F('sans_black', 36), '#08162B', C['gold'], eo((lt - 0.5) / 0.4))
    ys = {key: y_bot - k * (bh + 14) for k, (_, _, key) in enumerate(LAYERS)}
    if mode == 'weilue':
        f = eo((lt - 0.5) / 1.2)
        arrow(c, [(1000, ys['ghost']), (1040, (ys['ghost'] + ys['yl']) / 2), (1000, ys['yl'])], C['gold'], frac=f, width=7, head=24)
        text(c, '转引', 1010, (ys['ghost'] + ys['yl']) / 2 + 60, F('sans_bold', 34), C['gold'], f, align='r')
    if mode == 'rise':
        f = eo((lt - 0.3) / max(1, d * 0.7))
        arrow(c, [(80, ys['ghost']), (60, ys['mq']), (80, ys['yy'])], C['gold'], frac=f, width=8, head=26)
        for key, lab, at in [('ghost', '风声', 0.0), ('mq', '典故', 0.45), ('yy', '小说', 0.9)]:
            a = eo((f - at) / 0.1)
            pill(c, lab, 960, ys[key] - 60, F('sans_black', 34), '#08162B', C['gold'], a, align='r')
    c.restore()


# ---------- 两国记载 ----------
def sc_split(c, prm, x):
    mode = prm['mode']
    lt, d, j = x.lt, x.d, x.j
    f = eo(lt / 0.6)
    merge = eo((lt - 0.3) / 1.2) if mode == 'merge' else 0
    zoom = (1 + 0.03 * lt / max(1, d)) * (1.08 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(zoom, zoom)
    off = lerp(260, 241, merge)
    for side, col, t1, t2, t3 in [(-1, C['red'], '魏', '《张辽传》', '出城那一冲'), (1, C['cyan'], '吴', '《吴主传》等', '撤退差点被擒')]:
        cx = side * (off if mode != 'intro' else lerp(540, 260, f))
        rrect(c, cx - 240, -400, 480, 800, 30, P(col, 0.13))
        rrect(c, cx - 240, -400, 480, 800, 30, P(col, 0.9, stroke=5))
        text(c, t1, cx, -170, F('serif_black', 200), col, 1)
        text(c, t2, cx, -10, F('sans_black', 50), C['ink'], 1)
        if mode in ('both', 'merge'):
            a = eo((lt - 0.4 - (0.5 if side > 0 else 0)) / 0.4)
            text(c, t3, cx, 120, F('serif_black', 56), C['gold'], a, stroke=4)
            if side < 0:
                arrow(c, [(cx, 330), (cx, 200)], C['red'], a, width=12, head=30)
            else:
                c.drawLine(cx - 120, 260, cx + 120, 260, P('#D8B47A', a, stroke=16))
                c.drawRect(skia.Rect.MakeXYWH(cx + 30, 248, 50, 24), P('#0B2D45', a))
    if mode == 'merge':
        text(c, '各记一半', 0, -470, F('serif_black', 90), C['gold'], eo((lt - 1.2) / 0.5), stroke=6)
    c.restore()


# ---------- 大船 ----------
def sc_boat(c, prm, x):
    lt, d, j = x.lt, x.d, x.j
    z = (1 + 0.05 * lt / max(1, d)) * (1.15 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    bob = 8 * math.sin(x.t * 1.4)
    hull = skia.Path()
    hull.moveTo(-380, 60 + bob)
    hull.lineTo(380, 60 + bob)
    hull.quadTo(330, 200 + bob, 220, 210 + bob)
    hull.lineTo(-220, 210 + bob)
    hull.quadTo(-330, 200 + bob, -380, 60 + bob)
    c.drawPath(hull, P('#1D4E6B'))
    c.drawPath(hull, P(C['cyan'], 0.9, stroke=5))
    rrect(c, -220, -110 + bob, 440, 170, 14, P('#173E57'))
    rrect(c, -220, -110 + bob, 440, 170, 14, P(C['cyan'], 0.8, stroke=4))
    for k in range(4):
        lx = -160 + k * 107
        fl = 0.7 + 0.3 * math.sin(x.t * 5 + k)
        c.drawCircle(lx, -40 + bob, 18 * fl, P('#FFC56B', 0.95, blur=3))
        c.drawCircle(lx, -40 + bob, 60, P('#FFC56B', 0.18 * fl, blur=30))
    for k in range(6):
        y = 250 + k * 40
        pts = [(xx, y + 7 * math.sin(xx * 0.02 + x.t * 1.5 + k)) for xx in range(-560, 580, 40)]
        c.drawPath(smooth_path(pts), P('#4FB3E0', 0.5 - k * 0.06, stroke=4))
    text(c, '入大船宴饮', 0, -260, F('serif_black', 80), C['gold'], eo((lt - 0.3) / 0.5), stroke=6)
    c.restore()


# ---------- 尾声：循行 ----------
def sc_walk(c, prm, x):
    p0, p1 = prm['p']
    lt, d, j = x.lt, x.d, x.j
    p = lerp(p0, p1, clamp(lt / max(0.1, d)))
    z = (1.25 + 0.06 * p) * (1.12 if j % 2 else 1)
    c.save()
    c.translate(CX, CY)
    c.scale(z, z)
    c.translate(-470, -640)
    draw_hfmap(c, x.t, 0.6)
    wall_box(c, 470, 560, 110, 90, C['red'], label='合肥', lsize=34)
    path = smooth_path([(400, 640), (460, 700), (540, 690), (600, 740), (560, 800), (480, 780), (420, 720)])
    pp = P(C['gold'], 0.8, stroke=5)
    pp.setPathEffect(skia.DashPathEffect.Make([6, 12], 0))
    c.drawPath(partial_path(path, p), pp)
    (mx, my), _ = path_point(path, p)
    glow_dot(c, mx, my, 12, C['gold'])
    text(c, '曹操', mx, my - 30, F('sans_black', 30), C['gold'], 1, stroke=3)
    text(c, '辽战处', 640, 690, F('serif_black', 34), C['ink'], 0.7, stroke=3)
    c.restore()
    if p > 0.5:
        text(c, '叹息者良久', CX, 1210, F('serif_black', 80), C['gold'], eo((p - 0.55) / 0.2), stroke=6)
    elif p0 < 0.25:
        text(c, '建安二十一年', CX, 1210, F('serif_black', 70), C['gold'], eo((lt - 0.4) / 0.5), stroke=6)


# ---------- 章节卡 / 标题 ----------
def sc_chapter(c, prm, x):
    lt, d = x.lt, x.d
    a = eo(lt / 0.35)
    sweep = (lt / d) * 1.6 - 0.3
    sh = skia.GradientShader.MakeLinear([(0, 0), (W, 0)], [hexc(C['gold'], 0), hexc(C['gold'], 0.35), hexc(C['gold'], 0)],
                                        [clamp(sweep - 0.2), clamp(sweep), clamp(sweep + 0.2)])
    c.drawRect(skia.Rect.MakeXYWH(0, CY - 260, W, 520), skia.Paint(Shader=sh))
    c.drawLine(lerp(CX, 140, a), CY - 160, lerp(CX, 940, a), CY - 160, P(C['gold'], 0.8, stroke=3))
    c.drawLine(lerp(CX, 140, a), CY + 200, lerp(CX, 940, a), CY + 200, P(C['gold'], 0.8, stroke=3))
    text(c, prm['n'], CX, CY - 60, F('sans_black', 60), C['gold'], a)
    sc = 1.12 - 0.12 * eo(lt / 0.5)
    c.save()
    c.translate(CX, CY + 110)
    c.scale(sc, sc)
    f = F('serif_black', 130)
    w = f.measureText(prm['title'])
    fs = min(130, 130 * 900 / w)
    text(c, prm['title'], 0, 0, F('serif_black', fs), C['ink'], eo((lt - 0.1) / 0.4), shadow=16)
    c.restore()


def sc_title(c, prm, x):
    lt, d = x.lt, x.d
    sweep = (lt / max(d, 1)) * 1.4 - 0.2
    sh = skia.GradientShader.MakeLinear([(0, 0), (W, 0)], [hexc(C['gold'], 0), hexc(C['gold'], 0.3), hexc(C['gold'], 0)],
                                        [clamp(sweep - 0.25), clamp(sweep), clamp(sweep + 0.25)])
    c.drawRect(skia.Rect.MakeXYWH(0, CY - 420, W, 840), skia.Paint(Shader=sh))
    draw_case(c, CX, CY - 350, 0.34, glow=0.8)
    a = eo(lt / 0.4)
    pill(c, '历史的关键一局', CX, CY - 120, F('sans_black', 40), '#08162B', C['gold'], a)
    sc = 1.08 - 0.08 * eo(lt / 0.6)
    c.save()
    c.translate(CX, CY)
    c.scale(sc, sc)
    text_hl(c, '八百人冲阵之前', '那封信', 0, 70, F('serif_black', 118), C['ink'], C['gold'], a, stroke=6, shadow=14)
    text_hl(c, '那封信写了什么？', '那封信', 0, 220, F('serif_black', 118), C['ink'], C['gold'], eo((lt - 0.2) / 0.4), stroke=6, shadow=14)
    c.restore()
    text(c, '逍遥津 · 公元215年 · 合肥', CX, CY + 340, F('sans_bold', 44), C['dim'], eo((lt - 0.5) / 0.5))


def draw_cover(c, cw=1080, ch=1440):
    sh = skia.GradientShader.MakeLinear([(0, 0), (0, ch)], [hexc('#071329'), hexc('#123552')])
    c.drawRect(skia.Rect.MakeWH(cw, ch), skia.Paint(Shader=sh))
    for col, x, y, r, a in [(C['gold'], 540, 820, 560, 0.30), ('#FF9A5A', 540, 1440, 700, 0.35), (C['cyan'], 950, 300, 420, 0.12)]:
        g = skia.GradientShader.MakeRadial((x, y), r, [hexc(col, a), hexc(col, 0)])
        c.drawCircle(x, y, r, skia.Paint(Shader=g))
    # 城门夜募
    wy = 1130
    c.drawRect(skia.Rect.MakeXYWH(0, wy, cw, 320), P('#1C3550'))
    for i in range(17):
        c.drawRect(skia.Rect.MakeXYWH(i * 66, wy - 34, 40, 36), P('#1C3550'))
    arch = skia.Path()
    arch.addArc(skia.Rect.MakeXYWH(420, wy + 40, 240, 240), 180, 180)
    c.drawPath(arch, P('#FFB347', 0.85))
    c.drawRect(skia.Rect.MakeXYWH(420, wy + 160, 240, 160), P('#FFB347', 0.85))
    for tx in (300, 780):
        c.drawCircle(tx, wy + 70, 22, P('#FFC56B', 1, blur=5))
        c.drawCircle(tx, wy + 70, 90, P('#FFB347', 0.25, blur=40))
    rr = random.Random(9)
    for k in range(70):
        x = rr.uniform(60, 1020)
        y = rr.uniform(wy + 210, 1420)
        c.drawCircle(x, y, rr.uniform(7, 11), P(C['red'], 0.95))
    # 函
    draw_case(c, 540, 790, 0.9, glow=1.0)
    # 标题
    text_hl(c, '八百人冲阵之前', '', 540, 250, F('serif_black', 122), C['ink'], C['gold'], 1, stroke=8, shadow=16)
    text_hl(c, '那封信写了什么？', '那封信', 540, 400, F('serif_black', 122), C['ink'], C['gold'], 1, stroke=8, shadow=16)
    pill(c, '历史的关键一局', 40, 60, F('sans_black', 40), '#08162B', C['gold'], 1, align='l')


SCENES = dict(letter=sc_letter, siege=sc_siege, gate=sc_gate, bigtext=sc_bigtext, quote=sc_quote, roster=sc_roster,
              timeline=sc_timeline, cnmap=sc_cnmap, hfmap=sc_hfmap, dots=sc_dots, chain=sc_chain, sunsheng=sc_sunsheng,
              twocut=sc_twocut, battle=sc_battle, retreat=sc_retreat, bridge=sc_bridge, layers=sc_layers, split=sc_split,
              boat=sc_boat, walk=sc_walk, chapter=sc_chapter, title=sc_title)

SKY = {'battle': None, 'bridge': None}


# ───────────────────────── 叠加层 ─────────────────────────
def overlays(c, t, tl, sg, x):
    total = tl['total']
    s = S[sg['i']]
    # 顶部系列名
    pill(c, '历史的关键一局', 60, 150, F('sans_black', 32), '#08162B', C['gold'], 0.95, align='l')
    # 章节名
    chap = x.chapname
    if chap:
        text(c, chap, 1020, 162, F('sans_bold', 32), C['ink'], 0.85, align='r')
    if t < 7:
        text(c, 'AI配音 · 地图为示意', 1020, 210, F('sans', 26), C['dim'], 0.8 * (1 - seg01(t, 6, 7)), align='r')
    # 标签
    tag = s.get('tag')
    if tag and not sg.get('chap'):
        a = eo((t - sg['start']) / 0.3)
        col = C['gold']
        if tag.startswith('本集解读'):
            col = C['mint']
        elif tag.startswith('古人评'):
            col = C['lilac']
        elif tag.startswith(('传说', '小说', '典故')):
            col = '#FF9A7A'
        elif tag.startswith(('示意', '说明')):
            col = C['dim']
        pill(c, tag, CX, 1290, F('sans_bold', 28), C['ink'], '#0A1A30', 0.85 * a, dot=col)
    # 字幕
    if not sg.get('chap'):
        lt = t - sg['start']
        for (a0, a1, ln) in sg['subs']:
            if a0 <= lt < a1 + (0.25 if ln is sg['subs'][-1][2] else 0) or (lt >= a1 and ln is sg['subs'][-1][2] and lt < sg['dur']):
                f = F('sans_black', 62)
                w = f.measureText(ln)
                if w > 980:
                    f = F('sans_black', 62 * 980 / w)
                text(c, ln, CX, 1408, f, '#FFFFFF', 1, stroke=10, stroke_col='#06101E', shadow=8)
                break
    # 章节进度
    y = 1478
    c.drawLine(80, y, 1000, y, P(C['ink'], 0.15, stroke=4))
    c.drawLine(80, y, lerp(80, 1000, t / total), y, P(C['gold'], 0.75, stroke=4))
    for cs in tl['chap_starts']:
        xx = lerp(80, 1000, cs / total)
        c.drawCircle(xx, y, 6, P(C['gold'] if t >= cs else C['ink'], 0.8 if t >= cs else 0.3))


# ───────────────────────── 帧渲染 ─────────────────────────
def prepare(tl):
    segs = tl['segs']
    tl['chap_starts'] = [sg['start'] for sg in segs if sg.get('chap')]
    chapname = ''
    for sg in segs:
        if sg.get('chap'):
            chapname = f"{sg['chap'][0]} · {sg['chap'][1]}"
        sg['chapname'] = chapname if S[sg['i']].get('v', ('',))[0] != 'title' else ''
    return tl


def find_seg(tl, t):
    segs = tl['segs']
    lo, hi = 0, len(segs) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if segs[mid]['start'] <= t:
            lo = mid
        else:
            hi = mid - 1
    return segs[lo]


def render_frame(c, t, tl):
    sg = find_seg(tl, t)
    s = S[sg['i']]
    name, prm = s['v']
    x = Ctx()
    x.t = t
    lt_seg = max(0.0, t - sg['start'])
    n = sg['shots']
    sd = sg['dur'] / n
    j = min(n - 1, int(lt_seg / sd))
    # 场景整体若与上一段相同，则延续变体编号使画面有变化
    x.j = j + sg.get('jofs', 0)
    x.lt = lt_seg - j * sd if name in ('quote', 'bigtext', 'letter', 'roster', 'dots', 'chain', 'sunsheng',
                                         'twocut', 'split', 'layers', 'gate', 'boat', 'timeline', 'hfmap', 'cnmap') and j > 0 and name not in ('timeline', 'cnmap', 'hfmap', 'letter') else lt_seg
    if name in ('quote',) and j > 0:
        x.lt = lt_seg - j * sd
    x.d = sg['dur'] if x.lt == lt_seg else sd
    x.first = True
    x.first_seg_shot = (j == 0) or name in ('battle', 'retreat', 'bridge', 'walk', 'siege', 'cnmap', 'hfmap', 'timeline', 'letter', 'chain', 'dots', 'layers')
    x.chapname = sg['chapname']
    sky = prm.get('sky') or ('dark' if prm.get('dark') else 'night')
    if name == 'chapter':
        sky = 'night'
    background(c, t, sky)
    # 片段切入动效：前 0.18 秒轻微缩放淡入
    cut_in = clamp((t - sg['start'] - j * sd) / 0.18)
    c.save()
    c.clipRect(skia.Rect.MakeLTRB(0, 208, W, 1338))
    if cut_in < 1:
        s_ = 1.03 - 0.03 * eo(cut_in)
        c.translate(CX, CY)
        c.scale(s_, s_)
        c.translate(-CX, -CY)
    scene_dispatch(c, name, prm, x)
    c.restore()
    if cut_in < 1:
        c.drawRect(skia.Rect.MakeWH(W, H), P('#FFFFFF', 0.10 * (1 - cut_in)))
    # 底部压暗，保证字幕可读
    sh = skia.GradientShader.MakeLinear([(0, 1150), (0, 1338)], [hexc('#040B16', 0), hexc('#040B16', 0.7)])
    c.drawRect(skia.Rect.MakeXYWH(0, 1150, W, 188), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect.MakeXYWH(0, 1338, W, H - 1338), P('#040B16', 0.7))
    overlays(c, t, tl, sg, x)
    # 片尾淡出
    if t > tl['total'] - 0.5:
        c.drawRect(skia.Rect.MakeWH(W, H), P('#000000', clamp((t - (tl['total'] - 0.5)) / 0.5)))


def load_tl():
    tl = json.load(open(os.path.join(HERE, 'timeline.json')))
    # 相邻同场景：延续变体，避免连续两段都从同一构图开始
    prev = None
    for sg in tl['segs']:
        name = S[sg['i']]['v'][0]
        sg['jofs'] = 0
        if prev and prev[0] == name:
            sg['jofs'] = (prev[1] + prev[2]) % 2
        prev = (name, sg['jofs'], sg['shots'])
    return prepare(tl)


def main():
    cmd = sys.argv[1]
    if cmd == 'timeline':
        build_timeline(sys.argv[2])
        return
    tl = load_tl()
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    if cmd == 'frame':
        t = float(sys.argv[2])
        render_frame(c, t, tl)
        surf.makeImageSnapshot().save(sys.argv[3], skia.kPNG)
        return
    if cmd == 'cover':
        cs = skia.Surface(1080, 1440)
        draw_cover(cs.getCanvas())
        cs.makeImageSnapshot().save(sys.argv[2], skia.kPNG)
        return
    if cmd == 'frames':  # 多帧检查：t1,t2,... out_prefix
        for tt in sys.argv[2].split(','):
            c.clear(skia.ColorBLACK)
            render_frame(c, float(tt), tl)
            surf.makeImageSnapshot().save(f"{sys.argv[3]}_{float(tt):07.2f}.png", skia.kPNG)
        return
    if cmd == 'chunk':
        k, n, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        nf = int(math.ceil(tl['total'] * FPS))
        f0, f1 = nf * k // n, nf * (k + 1) // n
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                               '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12',
                               '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(f0, f1):
            render_frame(c, fi / FPS, tl)
            ff.stdin.write(surf.makeImageSnapshot().tobytes())
            if fi % 500 == 0:
                print(k, fi, f1, flush=True)
        ff.stdin.close()
        ff.wait()


if __name__ == '__main__':
    main()
