"""「三十秒一问」02 幸存者偏差 —— 单画面矢量场景渲染（cairo 画矢量，PIL 叠字幕）。"""
import math, json, random
import numpy as np
import cairo
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT_BLACK = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc", 2)
FONT_BOLD = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 2)
FONT_MED = ("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 2)
YELLOW = (255, 212, 0)
WHITE = (255, 255, 255)
RED = (0.93, 0.20, 0.17)
BG_TOP = (0x1C / 255, 0x26 / 255, 0x33 / 255)
BG_BOT = (0x10 / 255, 0x16 / 255, 0x1F / 255)
PLANE_CX, PLANE_CY = 540, 1000

_fonts = {}


def font(spec, size):
    k = (spec, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(spec[0], size, index=spec[1])
    return _fonts[k]


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back_out(x, s=1.7):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ramp(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)


# ---------------------------------------------------------------- plane geometry (plane units, nose up)
def mirror(pts):
    return pts + [(-x, y) for x, y in reversed(pts)]


FUSE_R = [(0, -405), (16, -400), (30, -385), (40, -360), (46, -325), (49, -280), (50, -200),
          (50, -60), (48, 60), (43, 170), (34, 270), (24, 340), (15, 380), (6, 398)]
FUSELAGE = mirror(FUSE_R)


def wing_le(x):  # leading edge y at |x|
    return -98 + 62 * (abs(x) - 45) / 400


def wing_te(x):
    return 74 - 48 * (abs(x) - 45) / 400


TIP = 445
WING_R = [(45, wing_le(45)), (TIP, wing_le(TIP)), (TIP + 9, wing_le(TIP) + 8), (TIP + 13, -4),
          (TIP + 10, wing_te(TIP) - 4), (TIP, wing_te(TIP)), (45, wing_te(45))]
WING_L = [(-x, y) for x, y in WING_R]
STAB_R = [(12, 286), (170, 314), (179, 321), (184, 340), (180, 354), (168, 360), (12, 376)]
STAB_L = [(-x, y) for x, y in STAB_R]

ENGINES = []  # (cx, front_y, back_y, halfwidth)
for ex, hw, back in [(135, 25, 100), (272, 22, 62)]:
    for s in (-1, 1):
        ENGINES.append((s * ex, wing_le(ex) - 62, back, hw))
COCKPIT = (0, -305, 40, 62)  # cx, cy, rx, ry  —— 驾驶舱「空白区」


def in_poly(x, y, poly):
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


def near_engine(x, y, m):
    for cx, fy, by, hw in ENGINES:
        if cx - hw - m < x < cx + hw + m and fy - m < y < by + m:
            return True
    return False


def near_cockpit(x, y, m):
    cx, cy, rx, ry = COCKPIT
    return ((x - cx) / (rx + m)) ** 2 + ((y - cy) / (ry + m)) ** 2 < 1


def inside_plane(x, y):
    return in_poly(x, y, FUSELAGE) or in_poly(x, y, WING_R) or in_poly(x, y, WING_L) or \
        in_poly(x, y, STAB_R) or in_poly(x, y, STAB_L)


def poisson(rng, accept, n_target, rmin, box, tries=60000):
    pts = []
    x0, y0, x1, y1 = box
    for _ in range(tries):
        if len(pts) >= n_target:
            break
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if not accept(x, y):
            continue
        if all((x - a) ** 2 + (y - b) ** 2 > rmin * rmin for a, b, *_ in pts):
            pts.append((x, y))
    return pts


def make_dots(seed=7):
    rng = random.Random(seed)

    def ok_red(x, y):
        if near_engine(x, y, 16) or near_cockpit(x, y, 26):
            return False
        if y < -250:  # 机头/驾驶舱前段稀
            return False
        # 内侧机翼（油箱附近）稀：只留一部分
        if 55 < abs(x) < 108 and -100 < y < 75 and rng.random() < 0.7:
            return False
        if abs(x) < 9:  # 机身中线留给垂尾线
            return False
        # 点不要压在轮廓线上
        return inside_plane(x, y) and inside_plane(x + 9, y) and inside_plane(x - 9, y) and \
            inside_plane(x, y + 9) and inside_plane(x, y - 9)

    red = poisson(rng, ok_red, 165, 22, (-470, -260, 470, 385))
    rng.shuffle(red)
    red = [(x, y, rng.uniform(0.85, 1.15)) for x, y in red]

    def ok_gray(x, y):
        if near_cockpit(x, y, -6) and inside_plane(x, y):
            return True
        return near_engine(x, y, -10) and y > -170
    gray = poisson(rng, ok_gray, 30, 18, (-320, -380, 320, 110))
    rng.shuffle(gray)
    gray = [(x, y, rng.uniform(0.85, 1.1)) for x, y in gray]
    return red, gray


RED_DOTS, GRAY_DOTS = make_dots()
N_INITIAL = 80  # 第一帧已有的红点


# armor plates: wing panels between x1..x2, plus fuselage block
def wing_panel(x1, x2, pad=7):
    s = 1 if x1 > 0 else -1
    a, b = sorted([abs(x1), abs(x2)])
    pts = [(a, wing_le(a) - pad), (b, wing_le(b) - pad), (b, wing_te(b) + pad), (a, wing_te(a) + pad)]
    return [(s * x, y) for x, y in pts]


ARMOR = [
    wing_panel(300, 448), wing_panel(-300, -448),
    wing_panel(160, 250), wing_panel(-160, -250),
    [(-56, -190), (56, -190), (52, 230), (-52, 230)],
    [(-176, 290), (176, 314), (176, 362), (-176, 362)],
]
ARMOR[5] = [(-180, 300), (180, 300), (180, 362), (-180, 362)]


# ---------------------------------------------------------------- default timeline
DEFAULT_TL = {
    "s1": [0.00, 2.95], "s2": [3.10, 8.70], "s3a": [8.85, 10.95], "s3b": [11.10, 14.30],
    "s4": [14.45, 15.10], "s5a": [15.85, 19.20], "s5b": [19.40, 22.30], "end": 24.4,
    "hits": None,
}


def default_hits(tl):
    """3–9 秒段：红点一颗颗打上来（若有配乐节拍则对齐节拍）。"""
    t0, t1 = tl["s2"][0] + 0.15, tl["s3a"][0] - 0.2
    n = len(RED_DOTS) - N_INITIAL
    beats = tl.get("beats")
    times = []
    if beats:
        bs = [b for b in beats if t0 <= b <= t1]
        # 每拍一簇，越往后越密
        k = len(bs)
        weights = [1 + 2.2 * i / max(1, k - 1) for i in range(k)]
        tot = sum(weights)
        counts = [max(1, round(n * w / tot)) for w in weights]
        while sum(counts) > n:
            counts[counts.index(max(counts))] -= 1
        while sum(counts) < n:
            counts[-1] += 1
        for b, c in zip(bs, counts):
            for j in range(c):
                times.append(b + j * 0.045)
    else:
        for i in range(n):
            u = (i + 0.5) / n
            times.append(t0 + (t1 - t0) * (u ** 0.75))
    return times


# ---------------------------------------------------------------- drawing helpers
def path_poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def path_smooth(ctx, pts):
    """Catmull-Rom closed smooth path."""
    n = len(pts)
    ctx.move_to(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(*c1, *c2, *p2)
    ctx.close_path()


def engine_path(ctx, e):
    cx, fy, by, hw = e
    r = hw
    ctx.new_sub_path()
    ctx.arc(cx, fy + r, r, math.pi, 2 * math.pi)
    ctx.line_to(cx + hw * 0.92, by - 10)
    ctx.curve_to(cx + hw * 0.7, by, cx - hw * 0.7, by, cx - hw * 0.92, by - 10)
    ctx.close_path()


def draw_plane_shape(ctx, fill=None, stroke=None, lw=3.2, detail=True):
    """整架飞机外形：机翼/平尾/发动机/机身。fill=(r,g,b,a) 用于剪影。"""
    shapes = []
    for poly in (WING_R, WING_L, STAB_R, STAB_L):
        shapes.append(("poly", poly))
    if fill is not None:
        ctx.set_source_rgba(*fill)
        for _, poly in shapes:
            path_smooth(ctx, poly) if False else path_poly(ctx, poly)
            ctx.fill()
        for e in ENGINES:
            engine_path(ctx, e)
            ctx.fill()
        path_smooth(ctx, FUSELAGE)
        ctx.fill()
        return
    # 线稿：先用底色填充（遮住重叠线），再描边
    bg = (0.105, 0.14, 0.19, 1)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _, poly in shapes:
        path_poly(ctx, poly)
        ctx.set_source_rgba(*bg)
        ctx.fill_preserve()
        ctx.set_source_rgba(*stroke)
        ctx.set_line_width(lw)
        ctx.stroke()
    if detail:
        # 副翼/襟翼分割线
        ctx.set_line_width(lw * 0.45)
        ctx.set_source_rgba(stroke[0], stroke[1], stroke[2], stroke[3] * 0.45)
        for s in (-1, 1):
            for x1, x2 in [(300, 438), (60, 290)]:
                ctx.move_to(s * x1, wing_te(x1) - 16)
                ctx.line_to(s * x2, wing_te(x2) - 16)
                ctx.stroke()
            ctx.move_to(s * 20, 358)
            ctx.line_to(s * 168, 346)
            ctx.stroke()
    for e in ENGINES:
        engine_path(ctx, e)
        ctx.set_source_rgba(*bg)
        ctx.fill_preserve()
        ctx.set_source_rgba(*stroke)
        ctx.set_line_width(lw)
        ctx.stroke()
        cx, fy, by, hw = e
        # 螺旋桨：俯视为一条细线 + 桨毂
        ctx.set_line_width(lw * 0.55)
        ctx.set_source_rgba(stroke[0], stroke[1], stroke[2], stroke[3] * 0.55)
        ctx.move_to(cx - 56, fy - 5)
        ctx.line_to(cx + 56, fy - 5)
        ctx.stroke()
        ctx.arc(cx, fy - 4, 5.5, 0, 2 * math.pi)
        ctx.set_source_rgba(*stroke)
        ctx.fill()
        if detail:  # 发动机罩环线
            ctx.set_line_width(lw * 0.45)
            ctx.set_source_rgba(stroke[0], stroke[1], stroke[2], stroke[3] * 0.4)
            ctx.move_to(cx - hw * 0.95, fy + hw + 22)
            ctx.line_to(cx + hw * 0.95, fy + hw + 22)
            ctx.stroke()
    path_smooth(ctx, FUSELAGE)
    ctx.set_source_rgba(*bg)
    ctx.fill_preserve()
    ctx.set_source_rgba(*stroke)
    ctx.set_line_width(lw)
    ctx.stroke()
    if detail:
        ctx.set_line_width(lw * 0.5)
        ctx.set_source_rgba(stroke[0], stroke[1], stroke[2], stroke[3] * 0.6)
        # 机头玻璃
        ctx.move_to(-30, -372)
        ctx.curve_to(-14, -360, 14, -360, 30, -372)
        ctx.stroke()
        # 驾驶舱风挡
        ctx.move_to(-38, -318)
        ctx.curve_to(-20, -338, 20, -338, 38, -318)
        ctx.line_to(36, -290)
        ctx.curve_to(16, -300, -16, -300, -36, -290)
        ctx.close_path()
        ctx.stroke()
        ctx.move_to(0, -333)
        ctx.line_to(0, -297)
        ctx.stroke()
        # 背部炮塔
        ctx.arc(0, -235, 15, 0, 2 * math.pi)
        ctx.stroke()
        # 垂尾（俯视为中线）
        ctx.set_line_width(lw * 0.8)
        ctx.set_source_rgba(*stroke)
        ctx.move_to(0, 262)
        ctx.line_to(0, 398)
        ctx.stroke()


def draw_dot(ctx, x, y, r, color, alpha, ring=False):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*color, alpha)
    ctx.fill()
    if ring:
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.35, 0.05, 0.04, alpha * 0.8)
        ctx.set_line_width(1.6)
        ctx.stroke()


def draw_flash(ctx, x, y, k):
    """落点闪光：k 0→1。"""
    if k <= 0 or k >= 1:
        return
    a = (1 - k) ** 1.5
    rr = 6 + 26 * ease_out(k)
    ctx.arc(x, y, rr, 0, 2 * math.pi)
    ctx.set_source_rgba(1, 0.85, 0.55, 0.85 * a)
    ctx.set_line_width(3 * (1 - k) + 0.5)
    ctx.stroke()
    for i in range(6):
        ang = i * math.pi / 3 + 0.4
        r1, r2 = rr * 0.55, rr * 0.95
        ctx.move_to(x + r1 * math.cos(ang), y + r1 * math.sin(ang))
        ctx.line_to(x + r2 * math.cos(ang), y + r2 * math.sin(ang))
    ctx.set_source_rgba(1, 0.95, 0.8, 0.9 * a)
    ctx.set_line_width(2.2)
    ctx.stroke()
    if k < 0.35:
        ctx.arc(x, y, 12 * (1 - k / 0.35), 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 0.9, 0.9 * (1 - k / 0.35))
        ctx.fill()


# ---------------------------------------------------------------- text
def text_line(draw, segs, cx, y, size, spec=FONT_BLACK, stroke=None, alpha=1.0, scale=1.0, img=None):
    """segs: [(text, color)]，居中画一行，黑描边。"""
    f = font(spec, max(8, int(size * scale)))
    sw = stroke if stroke is not None else max(3, int(size * scale * 0.11))
    total = sum(f.getlength(t) for t, _ in segs)
    x = cx - total / 2
    for t, col in segs:
        draw.text((x, y), t, font=f, fill=col + (int(255 * alpha),), stroke_width=sw,
                  stroke_fill=(0, 0, 0, int(255 * alpha)), anchor="ls")
        x += f.getlength(t)
    return total


def parse(s, base=WHITE):
    """'满身弹孔的地方，为什么[不用加固]？' → segs，[] 内亮黄。"""
    segs, cur, hi = [], "", False
    for ch in s:
        if ch == "[":
            if cur:
                segs.append((cur, base))
            cur, hi = "", True
        elif ch == "]":
            if cur:
                segs.append((cur, YELLOW))
            cur, hi = "", False
        else:
            cur += ch
    if cur:
        segs.append((cur, YELLOW if hi else base))
    return segs


# ---------------------------------------------------------------- frame
class Scene:
    def __init__(self, tl=None):
        self.tl = dict(DEFAULT_TL)
        if tl:
            self.tl.update(tl)
        self.hits = self.tl.get("hits") or default_hits(self.tl)
        rng = random.Random(3)
        # 下坠剪影
        self.fallers = []
        for i in range(4):
            self.fallers.append(dict(
                x=rng.choice([-1, 1]) * rng.uniform(200, 420) + 540, y0=rng.uniform(480, 700),
                dx=rng.uniform(-90, 90), t0=i * 0.55, rot0=rng.uniform(-0.4, 0.4),
                rot=rng.choice([-1, 1]) * rng.uniform(0.6, 1.3), sc=rng.uniform(0.15, 0.22)))
        self.fallers[0]["x"], self.fallers[1]["x"] = 230, 860
        self.fallers[2]["x"], self.fallers[3]["x"] = 820, 300

    # camera: slow push-in; zoom toward blanks during s4
    def camera(self, t):
        tl = self.tl
        z = 0.95 + 0.0042 * t
        oy = 0
        k = ease(ramp(t, tl["s4"][0] - 0.2, 1.4))
        z += 0.07 * k
        oy += 70 * k  # 把发动机/驾驶舱往画面中间推
        k2 = ease(ramp(t, tl["s5a"][0] + 0.2, 2.5))
        z -= 0.035 * k2
        oy -= 40 * k2
        return z, oy

    def render(self, t):
        tl = self.tl
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surf)
        # background gradient
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, *BG_TOP)
        g.add_color_stop_rgb(1, *BG_BOT)
        ctx.set_source(g)
        ctx.paint()
        # faint blueprint grid
        z, oy = self.camera(t)
        ctx.set_line_width(1)
        ctx.set_source_rgba(1, 1, 1, 0.035)
        step = 60 * z
        offx = (PLANE_CX) % step
        offy = (PLANE_CY + oy) % step
        x = offx
        while x < W:
            ctx.move_to(x, 0); ctx.line_to(x, H); x += step
        y = offy
        while y < H:
            ctx.move_to(0, y); ctx.line_to(W, y); y += step
        ctx.stroke()

        # falling silhouettes (background)
        fa = ramp(t, tl["s5a"][0] + 0.3, 0.01)
        if fa > 0:
            tt = t - (tl["s5a"][0] + 0.3)
            for f in self.fallers:
                u = (tt - f["t0"]) / 2.6
                if 0 < u < 1:
                    a = math.sin(math.pi * u) ** 1.2 * 0.38
                    ctx.save()
                    px = f["x"] + f["dx"] * u
                    py = f["y0"] + 900 * (u ** 1.6)
                    ctx.translate(px, py)
                    ctx.rotate(math.pi + f["rot0"] + f["rot"] * u)
                    ctx.scale(f["sc"], f["sc"])
                    # 下坠轨迹（淡灰细线，无火光）
                    draw_plane_shape(ctx, fill=(0.50, 0.56, 0.63, a))
                    ctx.restore()
                    ctx.move_to(px - f["dx"] * 0.25, py - 230)
                    ctx.line_to(px, py - 50)
                    ctx.set_source_rgba(0.6, 0.65, 0.72, a * 0.35)
                    ctx.set_line_width(2)
                    ctx.stroke()

        # plane transform
        ctx.save()
        ctx.translate(PLANE_CX, PLANE_CY + oy)
        ctx.scale(z, z)
        # soft shadow
        ctx.save()
        ctx.translate(14, 22)
        draw_plane_shape(ctx, fill=(0, 0, 0, 0.22))
        ctx.restore()
        draw_plane_shape(ctx, stroke=(0.95, 0.97, 1.0, 0.95), lw=3.4 / z ** 0.3)

        # blanks flash (s4): engines & cockpit glow
        if tl["s4"][0] - 0.1 <= t <= tl["s5a"][0] + 0.6:
            tt = t - (tl["s4"][0] - 0.1)
            pulse = 0
            for p0 in (0.15, 0.85):
                u = (tt - p0) / 0.55
                if 0 < u < 1:
                    pulse = max(pulse, math.sin(math.pi * u))
            if pulse > 0:
                for e in ENGINES:
                    engine_path(ctx, e)
                    ctx.set_source_rgba(1, 0.83, 0, 0.18 * pulse)
                    ctx.fill_preserve()
                    ctx.set_source_rgba(1, 0.83, 0, 0.95 * pulse)
                    ctx.set_line_width(4.5)
                    ctx.stroke()
                cx, cy, rx, ry = COCKPIT
                ctx.save(); ctx.translate(cx, cy); ctx.scale(rx, ry)
                ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
                ctx.set_source_rgba(1, 0.83, 0, 0.16 * pulse)
                ctx.fill_preserve()
                ctx.set_source_rgba(1, 0.83, 0, 0.9 * pulse)
                ctx.set_line_width(4)
                ctx.set_dash([10, 7])
                ctx.stroke()
                ctx.set_dash([])

        # red dots
        for i, (x, y, s) in enumerate(RED_DOTS):
            if i < N_INITIAL:
                ta = -10
            else:
                ta = self.hits[i - N_INITIAL]
            if t < ta:
                continue
            k = (t - ta)
            sc = 1 + 0.7 * (1 - ease_out(k / 0.14)) if k < 0.14 else 1
            draw_dot(ctx, x, y, 8.2 * s * sc, RED, 1.0, ring=True)
        for i, (x, y, s) in enumerate(RED_DOTS[N_INITIAL:]):
            draw_flash(ctx, x, y, (t - self.hits[i]) / 0.32)

        # gray "invisible" holes
        g0 = tl["s5a"][0] + 0.15
        for i, (x, y, s) in enumerate(GRAY_DOTS):
            ta = g0 + i * 0.07
            if t < ta:
                continue
            k = ease_out((t - ta) / 0.45)
            r = 8.2 * s * (0.4 + 0.6 * back_out(min(1, (t - ta) / 0.45)))
            draw_dot(ctx, x, y, r, (0.66, 0.70, 0.76), 0.55 * k)
            ctx.arc(x, y, r + 4, 0, 2 * math.pi)
            ctx.set_source_rgba(0.80, 0.84, 0.90, 0.55 * k)
            ctx.set_line_width(1.6)
            ctx.set_dash([3.5, 3])
            ctx.stroke()
            ctx.set_dash([])
            # 浮现时一圈扩散
            u = (t - ta) / 0.6
            if u < 1:
                ctx.arc(x, y, r + 4 + 20 * ease_out(u), 0, 2 * math.pi)
                ctx.set_source_rgba(0.85, 0.88, 0.93, 0.5 * (1 - u))
                ctx.set_line_width(1.8)
                ctx.stroke()

        # armor plates (s3)
        a0 = tl["s3a"][0] + 0.1
        stop = tl["s3b"][0] + 0.2
        fade = tl["s4"][0] - 0.25
        if a0 <= t < fade + 0.45:
            for i, poly in enumerate(ARMOR):
                ts = a0 + i * 0.16
                if t < ts:
                    continue
                # 从上方飞入 → 悬停接近 → 在 stop 时刻停住（不再下落）
                tm = min(t, stop)
                k = ease_out((tm - ts) / 0.55)
                hover = 46 * (1 - k) + 14 * (1 - ease((tm - ts - 0.55) / max(0.1, stop - ts - 0.55)))
                drop = -hover - 70 * (1 - k)
                alpha = clamp((t - ts) / 0.25) * (1 - ease(ramp(t, fade, 0.4)))
                jolt = 0
                if t >= stop:  # 停住的一下：轻微回弹
                    u = (t - stop) / 0.35
                    jolt = -6 * math.sin(math.pi * clamp(u)) if u < 1 else 0
                sc = 1.06 - 0.04 * k
                ctx.save()
                cx = sum(p[0] for p in poly) / len(poly)
                cy = sum(p[1] for p in poly) / len(poly)
                ctx.translate(cx, cy + drop + jolt - 6)
                ctx.scale(sc, sc)
                pts = [(p[0] - cx, p[1] - cy) for p in poly]
                # 投影
                ctx.save(); ctx.translate(8, 14)
                path_poly(ctx, pts); ctx.set_source_rgba(0, 0, 0, 0.25 * alpha); ctx.fill()
                ctx.restore()
                path_poly(ctx, pts)
                gr = cairo.LinearGradient(0, -60, 0, 60)
                gr.add_color_stop_rgba(0, 0.62, 0.72, 0.84, 0.62 * alpha)
                gr.add_color_stop_rgba(1, 0.42, 0.52, 0.64, 0.55 * alpha)
                ctx.set_source(gr)
                ctx.fill_preserve()
                ctx.set_source_rgba(0.85, 0.92, 1.0, 0.9 * alpha)
                ctx.set_line_width(2.4)
                ctx.stroke()
                # 铆钉
                for p in pts:
                    ix, iy = p[0] * 0.82, p[1] * 0.7
                    ctx.arc(ix, iy, 2.6, 0, 2 * math.pi)
                    ctx.set_source_rgba(0.9, 0.95, 1.0, 0.7 * alpha)
                    ctx.fill()
                ctx.restore()
        ctx.restore()

        # vignette
        rg = cairo.RadialGradient(W / 2, H * 0.52, 300, W / 2, H * 0.52, 1250)
        rg.add_color_stop_rgba(0, 0, 0, 0, 0)
        rg.add_color_stop_rgba(1, 0, 0, 0, 0.55)
        ctx.set_source(rg)
        ctx.paint()
        # 答案帧：文字区压暗一点
        ka = ease(ramp(t, tl["s5a"][0], 0.4))
        if ka > 0:
            lg = cairo.LinearGradient(0, 0, 0, 640)
            lg.add_color_stop_rgba(0, 0.03, 0.05, 0.08, 0.0)
            lg.add_color_stop_rgba(0.45, 0.03, 0.05, 0.08, 0.5 * ka)
            lg.add_color_stop_rgba(1, 0.03, 0.05, 0.08, 0)
            ctx.set_source(lg)
            ctx.rectangle(0, 0, W, 640)
            ctx.fill()

        buf = surf.get_data()
        arr = np.ndarray((H, W, 4), np.uint8, buf).copy()
        img = Image.fromarray(arr[:, :, [2, 1, 0, 3]], "RGBA")
        self.overlay_text(img, t)
        return img.convert("RGB")

    def overlay_text(self, img, t):
        tl = self.tl
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        def pop(t0):
            u = clamp((t - t0) / 0.16)
            return ease_out(u), 0.9 + 0.1 * back_out(u)

        # 「示意图」右下角
        d.text((1010, 1452), "示意图", font=font(FONT_MED, 34), fill=(225, 232, 240, 170),
               anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0, 120))

        Y1 = 330  # 字幕基线区（顶部 10% 安全区以下）
        s2, s3a, s3b, s4, s5a, s5b = (tl[k][0] for k in ("s2", "s3a", "s3b", "s4", "s5a", "s5b"))
        if t < s2:
            a, sc = (1.0, 1.0)
            text_line(d, parse("满身弹孔的地方，"), 540, Y1, 92, alpha=a)
            text_line(d, parse("为什么[不用加固]？"), 540, Y1 + 122, 92, alpha=a)
        elif t < s3a:
            a, sc = pop(s2)
            text_line(d, parse("二战 · 军方统计飞回来的轰炸机"), 540, Y1 - 20, 46, spec=FONT_BOLD,
                      alpha=a * 0.95, scale=sc)
            text_line(d, parse("哪儿弹孔多，"), 540, Y1 + 100, 92, alpha=a, scale=sc)
            text_line(d, parse("就在哪儿[加装甲]"), 540, Y1 + 222, 92, alpha=a, scale=sc)
        elif t < s3b:
            a, sc = pop(s3a)
            text_line(d, parse("装甲很重，"), 540, Y1 + 30, 92, alpha=a, scale=sc)
            text_line(d, parse("[不能哪儿都加]"), 540, Y1 + 152, 92, alpha=a, scale=sc)
        elif t < s4:
            a, sc = pop(s3b)
            text_line(d, parse("统计学家沃尔德："), 540, Y1 + 30, 84, alpha=a, scale=sc)
            text_line(d, parse("[正好反过来]"), 540, Y1 + 160, 108, alpha=a, scale=sc)
        elif t < s5a:
            a, sc = pop(s4)
            text_line(d, parse("为什么？"), 540, Y1 + 120, 140, alpha=a, scale=sc)
        else:
            a, sc = pop(s5a)
            text_line(d, parse("这些地方中弹的，[大多没回来]"), 540, Y1 + 10, 70, alpha=a, scale=sc)
            if t >= s5b:
                a2, sc2 = pop(s5b)
                text_line(d, parse("该加固的，是[没弹孔]的地方"), 540, Y1 + 118, 70, alpha=a2, scale=sc2)
            kf = ease(ramp(t, tl["s5b"][1] - 0.1, 0.5))
            if kf > 0:
                text_line(d, parse("这就叫：幸存者偏差"), 540, 1520, 50, spec=FONT_BOLD, alpha=kf)
        img.alpha_composite(layer)


if __name__ == "__main__":
    import sys
    sc = Scene()
    for t in map(float, sys.argv[1:]):
        sc.render(t).save(f"frame_{t:05.2f}.png")
