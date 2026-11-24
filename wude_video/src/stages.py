"""Stage illustrations (the middle band of the frame, y ~ 430..1270)."""
import math
import numpy as np
import skia
from gfx import (W, H, SC, TC, DE_COLOR, DE_INK, BRONZE, CINNABAR, INK, hexc, mix, with_alpha, paint, font,
                 draw_text, draw_vtext, clamp, ease, ease_out, ease_in, ramp, lerp, bamboo_slip, seal,
                 path_from, partial_path, cloud_swirl, han_figure, kneeling_figure, horse, ink_splat,
                 stone_text_image, draw_image, wrap_cjk)

SY0, SY1 = 440, 1268
SCX, SCY = 540, 850
SLIP_INK = hexc("#1B140C")
GOLD = hexc("#E2B85C")


class Ctx:
    def __init__(self, tl, t, ts, th, alpha, wheel):
        self.tl, self.t, self.ts, self.th, self.alpha, self.wheel = tl, t, ts, th, alpha, wheel
        self.lt = t - ts

    def fx(self, name):
        tf = self.tl.fx_time(name, self.t, since=self.ts)
        return None if tf is None else self.t - tf

    def fxp(self, name, key, default=None):
        return self.tl.fx_param(name, self.t, key, default)

    def line(self, line_id):
        for ln in self.tl.lines:
            if ln["id"] == line_id:
                return ln
        return None

    def lp(self, line_id):
        """progress (0..1) through a given line, <0 before / >1 after."""
        ln = self.line(line_id)
        if not ln:
            return 0.0
        return (self.t - ln["t0"]) / max(ln["dur"], 0.01)

    def kw_time(self, line_id, key):
        ln = self.line(line_id)
        if not ln:
            return 1e9
        i = ln["text"].find(key)
        if i < 0:
            return ln["t0"]
        return ln["t0"] + ln["dur"] * (i / max(1, len(ln["text"])))

    @property
    def text(self):
        return self.th["sub"]

    @property
    def dark(self):
        return self.th["dark"]


def caption(cv, c, s, y=1215, size=34, alpha=1.0, color=None):
    f = font("serif", "Bold", size)
    col = color or with_alpha(c.text, 0.85)
    draw_text(cv, s, SCX, y, f, col, "center", alpha * c.alpha,
              shadow=((0, 0, 0, 0.55), 4, (0, 2)) if c.dark else None)


def tag(cv, c, s, x, y, alpha=1.0, size=28):
    """small boxed tag such as 示意 / 史书记载"""
    f = font("sans", "Medium", size)
    w = f.measureText(s) + size * 0.9
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y - size * 1.05, w, size * 1.45), 6, 6)
    col = hexc("#E9D9B4") if c.dark else hexc("#5B3A22")
    cv.drawRRect(r, paint(col, "stroke", 2, alpha=alpha * c.alpha * 0.8))
    draw_text(cv, s, x + size * 0.45, y, f, col, "left", alpha * c.alpha * 0.9)


def rubbing_panel(cv, x, y, w, h, alpha, seed=0):
    """汉画像石拓片 style dark panel."""
    rng = np.random.default_rng(seed)
    p = skia.Path()
    n = 40
    pts = []
    for i in range(n):
        pts.append((x + w * i / n, y + rng.normal(0, 2.5)))
    for i in range(n):
        pts.append((x + w + rng.normal(0, 2.5), y + h * i / n))
    for i in range(n):
        pts.append((x + w - w * i / n, y + h + rng.normal(0, 2.5)))
    for i in range(n):
        pts.append((x + rng.normal(0, 2.5), y + h - h * i / n))
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    cv.drawPath(p, paint((0, 0, 0, 0.5), alpha=alpha, blur=12))
    cv.drawPath(p, paint(hexc("#16130F"), alpha=alpha))
    # mottled ink
    cv.save()
    cv.clipPath(p, doAntiAlias=True)
    for _ in range(140):
        cx, cy = x + rng.random() * w, y + rng.random() * h
        cv.drawCircle(cx, cy, 6 + rng.random() * 40, paint(hexc("#2A251E"), alpha=alpha * 0.18 * rng.random()))
    cv.restore()
    inset = 18
    cv.drawRect(skia.Rect.MakeXYWH(x + inset, y + inset, w - 2 * inset, h - 2 * inset),
                paint(hexc("#CFC2A6"), "stroke", 3, alpha=alpha * 0.55))


FIG = hexc("#DCCFB2")


# ------------------------------------------------------------------ S0
def st_slip_open(cv, c):
    a = c.alpha * ease(c.lt / 1.0)
    bt = c.fx("banner")
    shift = -200 * ease(bt / 1.3) if bt is not None else 0.0
    rise = (1 - ease_out(c.lt / 1.6)) * 90
    w, h = 150, 800
    x0, y0 = SCX - w / 2 + shift, 450 + rise
    # glow behind the slip
    cv.drawCircle(SCX + shift, y0 + h / 2, 330, paint(hexc("#5A4630"), alpha=a * 0.35, blur=120))
    bamboo_slip(cv, x0, y0, w, h, alpha=a, seed=3)
    f = font("serif", "Black", 92, TC)
    draw_vtext(cv, "代火者必將水", SCX + shift, y0 + 64, f, SLIP_INK, step=106, alpha=a,
               reveal=(c.lt - 0.7) / 0.30)
    fs = font("serif", "Bold", 30, TC)
    draw_vtext(cv, "呂氏春秋·應同", x0 - 34, y0 + 30, fs, with_alpha(CINNABAR, 0.95), step=34,
               alpha=a * ease((c.lt - 2.2) / 0.8))
    if bt is not None:
        draw_banner(cv, 650 + 60, 470, bt, c.alpha)


def draw_banner(cv, px, py, lt, alpha):
    a = alpha * ease(lt / 0.6)
    # pole
    cv.drawRect(skia.Rect.MakeXYWH(px - 7, py, 14, 790), paint(hexc("#3A2A18"), alpha=a))
    cv.drawCircle(px, py - 6, 14, paint(hexc("#A9834C"), alpha=a))
    unf = ease_out(lt / 1.4)
    fw, fh = 300 * unf, 420
    if fw < 2:
        return
    p = skia.Path()
    ph = lt * 2.2
    n = 30
    top = [(px + fw * i / n, py + 20 + 10 * math.sin(ph + i * 0.35) * (i / n)) for i in range(n + 1)]
    bot = [(px + fw * i / n, py + 20 + fh + 12 * math.sin(ph + 0.8 + i * 0.35) * (i / n)) for i in range(n + 1)]
    p.moveTo(*top[0])
    for q in top[1:]:
        p.lineTo(*q)
    for q in reversed(bot):
        p.lineTo(*q)
    p.close()
    cv.drawPath(p, paint((0, 0, 0, 0.6), alpha=a, blur=14))
    cv.drawPath(p, paint(hexc("#0A0A0C"), alpha=a))
    cv.drawPath(p, paint(hexc("#8E6E3E"), "stroke", 3, alpha=a * 0.8))
    # folds
    for i in range(3, n, 6):
        x = top[i][0]
        cv.drawLine(x, top[i][1] + 6, bot[i][0], bot[i][1] - 6, paint(hexc("#2B2B33"), "stroke", 6, alpha=a * 0.5))


def st_title_card(cv, c):
    a = c.alpha * ease(c.lt / 1.2)
    img = stone_text_image("五德终始", "serif", "Black", 168, (0.93, 0.86, 0.70, 1.0), 11, 0.55)
    draw_image(cv, img, SCX, 800, alpha=a, center=True)
    f = font("serif", "Bold", 40)
    draw_text(cv, "命理与正统 · 第一期", SCX, 640, f, hexc("#C8A56A"), "center", a, spacing=4)
    # five colour seals
    for i, el in enumerate(["土", "木", "金", "火", "水"]):
        x = SCX + (i - 2) * 110
        k = ease((c.lt - 0.8 - i * 0.15) / 0.5)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 40, 940 - 40, 80, 80), 8, 8)
        cv.drawRRect(r, paint(DE_COLOR[el], alpha=a * k))
        cv.drawRRect(r, paint(hexc("#E8D9B5"), "stroke", 2, alpha=a * k * 0.6))
        draw_text(cv, el, x, 940 + 18, font("serif", "Black", 50), DE_INK[el], "center", a * k)
    draw_text(cv, "不算命 · 讲学问", SCX, 1090, font("sans", "Medium", 34), hexc("#BFAE8E"), "center",
              a * ease((c.lt - 1.6) / 0.6), spacing=6)


# ------------------------------------------------------------------ S1
def lonlat(lon, lat):
    return 40 + (lon - 104.0) / 21.0 * 1000, 470 + (42.6 - lat) / 13.0 * 760


COAST = [(124.6, 40.1), (123.2, 40.6), (122.3, 40.5), (121.7, 39.6), (121.2, 38.9), (121.9, 39.2),
         (122.2, 40.2), (121.2, 40.9), (120.2, 40.3), (119.5, 39.9), (118.6, 39.3), (117.8, 38.9),
         (117.6, 38.4), (118.3, 37.9), (118.9, 37.4), (119.4, 37.1), (120.2, 37.5), (120.8, 37.8),
         (121.7, 37.5), (122.5, 37.3), (122.0, 36.9), (121.2, 36.6), (120.4, 36.1), (119.6, 35.6),
         (119.2, 34.9), (119.8, 34.4), (120.4, 33.6), (120.9, 32.6), (121.5, 32.0), (121.9, 31.4),
         (121.6, 30.8), (121.0, 30.5), (121.9, 30.0), (122.0, 29.4)]
RIVER = [(104.8, 35.9), (105.9, 37.4), (106.6, 38.9), (107.6, 40.3), (109.5, 40.6), (111.1, 40.3),
         (111.3, 39.0), (110.6, 37.6), (110.5, 36.0), (110.3, 34.7), (111.8, 34.8), (113.4, 34.9),
         (114.4, 35.4), (115.2, 36.3), (116.0, 37.3), (116.8, 38.1), (117.6, 38.6)]
STATES = {"秦": (107.8, 35.2), "赵": (114.2, 37.9), "魏": (113.2, 35.6), "韩": (112.6, 34.3),
          "楚": (113.2, 31.6), "燕": (116.4, 40.2), "齐": (118.4, 36.3)}


def map_paths():
    sea = skia.Path()
    pts = [lonlat(*p) for p in COAST]
    sea.moveTo(*pts[0])
    for q in pts[1:]:
        sea.lineTo(*q)
    sea.lineTo(1100, 1300)
    sea.lineTo(1100, 400)
    sea.lineTo(pts[0][0], 400)
    sea.close()
    coast = skia.Path()
    coast.moveTo(*pts[0])
    for q in pts[1:]:
        coast.lineTo(*q)
    river = skia.Path()
    rp = [lonlat(*p) for p in RIVER]
    river.moveTo(*rp[0])
    for i in range(1, len(rp) - 1):
        mx, my = (rp[i][0] + rp[i + 1][0]) / 2, (rp[i][1] + rp[i + 1][1]) / 2
        river.quadTo(rp[i][0], rp[i][1], mx, my)
    river.lineTo(*rp[-1])
    return sea, coast, river


def draw_map(cv, c, a, ink, sea_col, draw_k=1.0, labels_k=1.0, highlight=None, hl_col=None,
             qin_k=0.0):
    sea, coast, river = map_paths()
    cv.save()
    cv.clipRect(skia.Rect.MakeLTRB(30, SY0, 1050, SY1 - 40))
    cv.drawPath(sea, paint(sea_col, alpha=a * 0.55))
    # sea ripples
    for i in range(9):
        y = 560 + i * 70
        x0 = lonlat(122.8, 0)[0] + (i % 2) * 30
        p = skia.Path()
        p.moveTo(x0, y)
        for k in range(6):
            p.quadTo(x0 + k * 30 + 15, y - 8, x0 + k * 30 + 30, y)
        cv.drawPath(p, paint(ink, "stroke", 1.5, alpha=a * 0.18))
    if qin_k > 0:
        # Qin black spreading east from the west
        sx, sy = lonlat(*STATES["秦"])
        rad = 1300 * ease(qin_k)
        land = skia.Path()
        land.addCircle(sx, sy, rad)
        cv.save()
        cv.clipPath(sea, skia.ClipOp.kDifference, True)
        cv.drawPath(land, paint(hexc("#0B0B0E"), alpha=a * 0.85))
        cv.restore()
    cv.drawPath(partial_path(coast, draw_k), paint(ink, "stroke", 3.5, alpha=a * 0.9))
    cv.drawPath(partial_path(river, draw_k), paint(hexc("#C9A46A") if c.dark else hexc("#6E5634"), "stroke", 4,
                                                   alpha=a * 0.8))
    if highlight:
        for name in highlight:
            hx, hy = lonlat(*STATES[name])
            pulse = 0.75 + 0.25 * math.sin(c.lt * 3)
            cv.drawCircle(hx, hy, 90, paint(hl_col or CINNABAR, alpha=a * 0.33 * pulse, blur=30))
    f = font("serif", "Black", 54)
    for name, (lo, la) in STATES.items():
        x, y = lonlat(lo, la)
        hl = highlight and name in highlight
        col = (hl_col or CINNABAR) if hl else with_alpha(ink, 0.62)
        if qin_k > 0 and name != "秦":
            col = with_alpha(hexc("#8C7A5E"), 0.9)
        draw_text(cv, name, x, y + 18, f if hl else font("serif", "Bold", 44), col, "center", a * labels_k)
    cv.restore()


def st_map_qi(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    ink = hexc("#2B2117")
    draw_map(cv, c, a, ink, hexc("#9DB0A9"), draw_k=ease(c.lt / 1.6), labels_k=ease((c.lt - 1.0) / 0.8),
             highlight=["齐"])
    tag(cv, c, "示意", 70, 520, a)
    pt = c.fx("slips_pile")
    if pt is not None:
        k = ease(pt / 0.8)
        for i in range(5):
            bx = 640 + i * 62 - 20 * (i % 2)
            by = 1015 - (i % 3) * 22
            draw_slip_bundle(cv, bx, by, 150, 70, a * k, seed=i)
        draw_text(cv, "《终始》《大圣》 十余万言", 830, 1165, font("serif", "Bold", 36), hexc("#5A2A18"),
                  "center", a * k)


def draw_slip_bundle(cv, x, y, w, h, alpha, seed=0):
    """A rolled bundle of slips seen from the side (cylinder)."""
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), h / 2, h / 2)
    cv.drawRRect(r, paint((0, 0, 0, 0.35), alpha=alpha, blur=8))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)],
                [skia.Color4f(0.82, 0.66, 0.40, alpha), skia.Color4f(0.62, 0.46, 0.24, alpha)]))
    cv.drawRRect(r, p)
    for k in range(1, 9):
        yy = y + h * k / 9
        cv.drawLine(x + 8, yy, x + w - 8, yy, paint((0.3, 0.2, 0.1, 0.35), "stroke", 1.2, alpha=alpha))
    cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.3, y - 2, 10, h + 4), paint(hexc("#3B2A1A"), alpha=alpha))
    cv.drawRect(skia.Rect.MakeXYWH(x + w * 0.65, y - 2, 10, h + 4), paint(hexc("#3B2A1A"), alpha=alpha))


def st_wheel_stage(cv, c):
    a = c.alpha
    col = with_alpha(c.th["accent"], 0.25)
    for k in range(3):
        cv.drawCircle(540, 800, 400 + k * 46, paint(col, "stroke", 1.5, alpha=a * (0.6 - k * 0.15)))
    for i, (x, y, s, fl) in enumerate([(150, 560, 110, False), (930, 1110, 120, True), (170, 1120, 90, False),
                                       (920, 540, 90, True)]):
        cloud_swirl(cv, x, y, s, c.th["accent"], alpha=a * 0.35, width=3, flip=fl)
    ot = c.fx("omen_flash")
    if ot is not None and ot < 9:
        k = ease(ot / 0.6) * (1 - ease((ot - 7.5) / 1.0))
        seal(cv, 540, 800, 120, "瑞", color=hexc("#B8862A"), alpha=a * k, rot=-4)
        caption(cv, c, "符瑞：天降的预兆", y=1245, size=38, alpha=k)
    # caption about the rule (only where the rule is being explained)
    st = c.wheel
    seg = c.tl.seg_at(c.t)["id"]
    if st and st.big > 0.6 and (ot is None or ot >= 9) and seg in ("S1", "S6"):
        if st.order[0] == "土" and st.arrows:
            caption(cv, c, "相胜（相克）：后一个打败前一个", y=1245, size=38,
                    alpha=max(aa for *_, aa in st.arrows))
        elif st.order[0] == "木" and st.flip is None:
            if st.run_slot > 0.05:
                caption(cv, c, "闰位：插在缝里、不算数的一格", y=1245, size=38, alpha=st.run_slot)
            elif st.arrows:
                caption(cv, c, "相生：前一个生出后一个", y=1245, size=38,
                        alpha=max(aa for *_, aa in st.arrows))
    if st and st.flip is not None:
        p = st.flip
        k = math.sin(math.pi * p)
        cv.drawCircle(540, 800, 380, paint(hexc("#FFE9B8"), alpha=a * 0.65 * k, blur=100))
        # rays
        for i in range(16):
            ang = i / 16 * math.tau + p * 0.6
            x1, y1 = 540 + 330 * math.cos(ang), 800 + 330 * math.sin(ang)
            x2, y2 = 540 + (420 + 120 * k) * math.cos(ang), 800 + (420 + 120 * k) * math.sin(ang)
            cv.drawLine(x1, y1, x2, y2, paint(hexc("#FFF1CC"), "stroke", 4, alpha=a * 0.5 * k))
        f = font("serif", "Black", 84)
        if p < 0.5:
            kk = 1 - ease(p / 0.5)
            draw_text(cv, "相克", 540, 1230, f, c.text, "center", a * (0.35 + 0.65 * kk))
            if p > 0.2:
                w = f.measureText("相克")
                cv.drawLine(540 - w / 2 - 10, 1200, 540 - w / 2 - 10 + (w + 20) * ease((p - 0.2) / 0.3), 1200,
                            paint(CINNABAR, "stroke", 8, alpha=a))
        else:
            kk = ease((p - 0.5) / 0.4)
            w = f.measureText("相生")
            op = paint(hexc("#FFF3D6"), "stroke", 10, alpha=a * kk)
            cv.drawString("相生", 540 - w / 2, 1230, f, op)
            draw_text(cv, "相生", 540, 1230, f, hexc("#8E1B12"), "center", a * kk)


def st_lscq_book(cv, c):
    a = c.alpha * ease(c.lt / 0.7)
    n = 11
    w, gap, h = 66, 10, 640
    total = n * w + (n - 1) * gap
    x0 = SCX - total / 2
    y0 = 480
    for i in range(n):
        k = ease((c.lt - (n - 1 - i) * 0.07) / 0.5)
        x = x0 + i * (w + gap)
        bamboo_slip(cv, x, y0 + (1 - k) * 30, w, h, alpha=a * k, seed=10 + i, cords=True)
    f = font("serif", "Black", 50, TC)
    draw_vtext(cv, "呂氏春秋", x0 + (n - 1) * (w + gap) + w / 2, y0 + 40, f, SLIP_INK, step=60, alpha=a)
    hl = ease((c.lt - 1.2) / 0.6)
    xi = x0 + (n - 3) * (w + gap) + w / 2
    cv.drawRect(skia.Rect.MakeXYWH(xi - w / 2 - 4, y0 + 20, w + 8, 170), paint(CINNABAR, alpha=a * hl * 0.25))
    draw_vtext(cv, "應同", xi, y0 + 40, f, CINNABAR, step=60, alpha=a * hl)
    ft = font("serif", "Medium", 34, TC)
    txt = "凡帝王者之將興也天必先見祥乎下民"
    for i in range(n - 4):
        x = x0 + (n - 5 - i) * (w + gap) + w / 2
        seg = txt[i * 2:(i * 2) + 2]
        draw_vtext(cv, seg, x, y0 + 60, ft, with_alpha(SLIP_INK, 0.75), step=40, alpha=a * ease((c.lt - 1.5 - i * 0.1) / 0.5))
    caption(cv, c, "成书于秦统一以前 · 吕不韦门客编", y=1205, size=34, alpha=ease((c.lt - 0.8) / 0.6))


def st_slip_prophecy(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    # darkening from below = 水 is coming
    dk = ease(c.lt / 6.0)
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, SY0), skia.Point(0, SY1)],
                [skia.Color4f(0, 0, 0, 0), skia.Color4f(0.03, 0.03, 0.05, 0.55 * dk * a)]))
    cv.drawRect(skia.Rect.MakeLTRB(0, SY0, W, SY1), p)
    slips = [("天且先見水氣勝", 760), ("代火者必將水", 540), ("水氣勝故其色尚黑", 320)]
    q = c.line("S1_19")
    for i, (txt, x) in enumerate(slips):
        start = (q["t0"] - c.ts) + i * 1.6 if q else i * 1.6
        k = ease((c.lt - start + 0.4) / 0.6)
        h = 760
        bamboo_slip(cv, x - 62, 470, 124, h, alpha=a * k, seed=40 + i)
        fs = 70 if len(txt) <= 7 else 62
        f = font("serif", "Black", fs, TC)
        draw_vtext(cv, txt, x, 520, f, SLIP_INK, step=fs * 1.12, alpha=a * k,
                   reveal=(c.lt - start) / 0.18)
    # highlight 尚黑
    kh = ease((c.lt - ((q["t0"] - c.ts) + 5.0 if q else 6)) / 0.6)
    if kh > 0:
        f = font("serif", "Black", 62, TC)
        y = 520 + 62 * 1.12 * 6
        cv.drawCircle(320, y + 34, 58, paint(CINNABAR, "stroke", 4, alpha=a * kh))


def st_broom(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    rubbing_panel(cv, 70, 470, 940, 700, a, seed=5)
    # palace outline (碣石宫)
    roof = path_from("M 600 640 L 680 590 L 900 590 L 980 640 Z")
    cv.drawPath(roof, paint(FIG, alpha=a * 0.55))
    for x in (640, 720, 800, 880, 940):
        cv.drawRect(skia.Rect.MakeXYWH(x, 640, 12, 150), paint(FIG, alpha=a * 0.45))
    cv.drawRect(skia.Rect.MakeXYWH(610, 790, 360, 14), paint(FIG, alpha=a * 0.5))
    draw_text(cv, "碣石宫", 790, 572, font("serif", "Bold", 32), with_alpha(FIG, 0.8), "center", a)
    walk = 18 * math.sin(c.lt * 1.2)
    han_figure(cv, 520 + walk * 0.3, 1120, 330, FIG, a, pose="bow_broom", facing=1)
    han_figure(cv, 270 + walk * 0.3, 1120, 400, FIG, a, pose="scholar", facing=1)
    draw_text(cv, "燕昭王", 560, 1155, font("serif", "Bold", 30), with_alpha(FIG, 0.85), "center", a)
    draw_text(cv, "邹衍", 270, 1155, font("serif", "Bold", 30), with_alpha(FIG, 0.85), "center", a)
    caption(cv, c, "拥彗先驱 —— 拿着扫帚在前面开路", y=1228, size=34)
    tag(cv, c, "示意", 900, 520, a)


def st_zouyan_scroll(cv, c, final=False):
    a = c.alpha * ease(c.lt / 0.8)
    unroll = 1.0 if final else ease_out(c.lt / 1.2)
    x0, y0, w, h = 110, 500, 860, 620
    sw = w * unroll
    r = skia.Rect.MakeXYWH(SCX - sw / 2, y0, sw, h)
    cv.drawRect(r.makeOffset(6, 10), paint((0, 0, 0, 0.4), alpha=a, blur=12))
    sp = skia.Paint(AntiAlias=True)
    sp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, y0), skia.Point(0, y0 + h)],
                 [skia.Color4f(0.95, 0.91, 0.82, a), skia.Color4f(0.88, 0.82, 0.69, a)]))
    cv.drawRect(r, sp)
    for xr in (SCX - sw / 2, SCX + sw / 2):
        cv.drawRect(skia.Rect.MakeXYWH(xr - 12, y0 - 20, 24, h + 40), paint(hexc("#5A3A20"), alpha=a))
    if unroll < 0.6:
        return
    k = ease((unroll - 0.6) / 0.4)
    ink = hexc("#22190F")
    draw_text(cv, "然要其归", SCX, 600, font("serif", "Bold", 44), with_alpha(ink, 0.7), "center", a * k)
    draw_text(cv, "必止乎仁义节俭", SCX, 700, font("serif", "Black", 80), ink, "center", a * k)
    draw_text(cv, "君臣上下六亲之施", SCX, 780, font("serif", "Bold", 44), with_alpha(ink, 0.7), "center", a * k)
    t2 = 0.0 if final else ((c.line("S1_34")["t0"] - c.ts) if c.line("S1_34") else 3.0)
    k2 = 1.0 if final else ease((c.lt - t2) / 0.6)
    draw_text(cv, "惧然顾化", 290, 960, font("serif", "Black", 62), hexc("#3A2A18"), "center", a * k2)
    draw_text(cv, "→", 485, 955, font("serif", "Black", 54), hexc("#3A2A18"), "center", a * k2)
    draw_text(cv, "其后不能行之", 750, 960, font("serif", "Black", 62), CINNABAR, "center", a * k2)
    draw_text(cv, "吓了一跳", 290, 1030, font("sans", "Medium", 34), with_alpha(ink, 0.7), "center", a * k2)
    draw_text(cv, "然后做不到", 750, 1030, font("sans", "Medium", 34), with_alpha(ink, 0.7), "center", a * k2)
    mt = c.fx("mark_line")
    mk = 1.0 if final else (ease(mt / 0.8) if mt is not None else 0.0)
    if mk > 0:
        p = skia.Path()
        p.moveTo(570, 990)
        p.cubicTo(650, 1000, 820, 984, 940, 996)
        cv.drawPath(partial_path(p, mk), paint(CINNABAR, "stroke", 9, alpha=a * 0.9))
        seal(cv, 930, 1080, 70, "记", alpha=a * mk, rot=6)


def st_zouyan_scroll2(cv, c):
    st_zouyan_scroll(cv, c, final=True)


# ------------------------------------------------------------------ S2 秦
def st_qin_unify(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    draw_map(cv, c, a, hexc("#C9B48C"), hexc("#1E2A2E"), draw_k=1.0, labels_k=1.0,
             highlight=["秦"], hl_col=hexc("#C9A46A"), qin_k=ease((c.lt - 0.6) / 2.2))
    k = ease((c.lt - 1.5) / 0.8)
    img = stone_text_image("公元前221年", "serif", "Black", 64, (0.85, 0.72, 0.48, 1), 4, 0.4)
    draw_image(cv, img, SCX, 1170, alpha=a * k, center=True)
    tag(cv, c, "示意", 70, 520, a)


def st_qin_list(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    x0, y0, w, h = 70, 462, 940, 790
    r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y0, w, h), 18, 18)
    cv.drawRRect(r, paint((0, 0, 0, 0.6), alpha=a, blur=18))
    cv.drawRRect(r, paint(hexc("#0B0B0D"), alpha=a))
    cv.drawRRect(r, paint(BRONZE, "stroke", 3, alpha=a * 0.8))
    inner = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + 12, y0 + 12, w - 24, h - 24), 12, 12)
    cv.drawRRect(inner, paint(BRONZE, "stroke", 1.2, alpha=a * 0.45))
    rows = [("正朔", "十月为岁首"), ("服色", "尚黑"), ("数", "以六为纪 · 六寸 六尺 六马"),
            ("更名", "河 → 德水"), ("或曰", "秦文公获黑龙（有人说）")]
    fx_t = [None] * 5
    for (tf, n, p) in c.tl.fx:
        if n == "list" and c.ts - 0.3 <= tf <= c.t:
            i = int(p.get("i", 0))
            fx_t[i] = c.t - tf
    for i, (k1, k2) in enumerate(rows):
        lt = fx_t[i]
        if lt is None:
            continue
        k = ease(lt / 0.5)
        y = y0 + 40 + i * 150
        cy = y + 62
        # icon box
        ix = x0 + 60
        draw_list_icon(cv, i, ix + 70, cy, lt, a * k)
        draw_text(cv, k1, x0 + 250, cy - 4, font("serif", "Black", 52), hexc("#D8B677"), "left", a * k)
        f2 = font("sans", "Bold", 44 if len(k2) < 12 else 36)
        draw_text(cv, k2, x0 + 250, cy + 52, f2, hexc("#EEE3CC"), "left", a * k)
        if i < 4:
            cv.drawLine(x0 + 40, y + 140, x0 + w - 40, y + 140, paint(BRONZE, "stroke", 1, alpha=a * k * 0.4))


def draw_list_icon(cv, i, cx, cy, lt, a):
    if i == 0:  # calendar slip 十月
        bamboo_slip(cv, cx - 28, cy - 64, 56, 128, alpha=a, seed=70, cords=False)
        draw_vtext(cv, "十月", cx, cy - 52, font("serif", "Black", 40), SLIP_INK, step=46, alpha=a)
    elif i == 1:  # cloth dyed black
        k = ease(lt / 1.2)
        r = skia.Rect.MakeXYWH(cx - 60, cy - 55, 120, 110)
        cv.drawRect(r, paint(hexc("#D8CBB0"), alpha=a))
        cv.save()
        cv.clipRect(r)
        cv.drawRect(skia.Rect.MakeXYWH(cx - 60, cy - 55, 120, 110 * k), paint(hexc("#0E0E10"), alpha=a))
        cv.restore()
        cv.drawRect(r, paint(BRONZE, "stroke", 2, alpha=a))
    elif i == 2:  # ruler + horses
        cv.drawRect(skia.Rect.MakeXYWH(cx - 70, cy - 66, 140, 22), paint(hexc("#B58C4E"), alpha=a))
        for k in range(7):
            x = cx - 70 + k * 140 / 6
            cv.drawLine(x, cy - 66, x, cy - 52, paint(hexc("#2A1C0C"), "stroke", 2, alpha=a))
        for k in range(6):
            kk = ease((lt - 0.15 * k) / 0.3)
            horse(cv, cx - 62 + k * 25, cy + 50, 30, hexc("#D8B677"), alpha=a * kk)
    elif i == 3:  # river renamed
        p = skia.Path()
        p.moveTo(cx - 70, cy + 10)
        for k in range(4):
            p.quadTo(cx - 70 + k * 35 + 17, cy - 12, cx - 70 + k * 35 + 35, cy + 10)
        cv.drawPath(p, paint(hexc("#6E8FA3"), "stroke", 6, alpha=a))
        k = ease((lt - 0.6) / 0.5)
        draw_text(cv, "河", cx - 30, cy - 26, font("serif", "Black", 40), hexc("#BBBBBB"), "center", a * (1 - 0.6 * k))
        if k > 0:
            cv.drawLine(cx - 52, cy - 38, cx - 8, cy - 38, paint(CINNABAR, "stroke", 4, alpha=a * k))
            draw_text(cv, "德水", cx + 30, cy + 62, font("serif", "Black", 36), hexc("#D8B677"), "center", a * k)
    elif i == 4:  # black dragon (outline)
        draw_dragon(cv, cx + 6, cy + 4, 0.16, hexc("#B9A27A"), a, reveal=ease(lt / 1.2), glow=False,
                    fill=hexc("#050506"))


def st_qin_law(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    rng = np.random.default_rng(9)
    # falling decree slips (slow)
    chars = "事皆決於法急法久者不赦剛毅戾深刻削毋仁恩和義"
    for i in range(14):
        x = 50 + i * 75 + rng.normal(0, 6)
        speed = 22 + rng.random() * 18
        y = SY0 - 300 + ((c.lt * speed + rng.random() * 900) % 1100)
        al = a * (0.18 + 0.12 * rng.random())
        bamboo_slip(cv, x, y, 46, 260, alpha=al, seed=100 + i, cords=False,
                    tint=(hexc("#8A93A0"), hexc("#5E6672")))
        s = "".join(chars[(i * 3 + k) % len(chars)] for k in range(5))
        draw_vtext(cv, s, x + 23, y + 16, font("serif", "Bold", 34, TC), hexc("#111318"), step=46, alpha=al * 2.4)
    # vignette band behind text
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 620), skia.Point(0, 1120)],
                [skia.Color4f(0, 0, 0, 0), skia.Color4f(0, 0, 0, 0.75 * a), skia.Color4f(0, 0, 0, 0)],
                [0, 0.5, 1]))
    cv.drawRect(skia.Rect.MakeLTRB(0, 620, W, 1120), p)
    q = c.line("S2_19")
    qs = (q["t0"] - c.ts) if q else 1.0
    k1 = ease((c.lt - qs - 0.6) / 0.8)
    img = stone_text_image("刻削毋仁恩和义", "serif", "Black", 104, (0.90, 0.92, 0.95, 1), 21, 0.6)
    draw_image(cv, img, SCX, 800, alpha=a * k1, center=True)
    kw = c.kw_time("S2_19", "然后")
    k2 = ease((c.t - kw) / 0.7)
    img2 = stone_text_image("然后合五德之数", "serif", "Black", 76, (0.83, 0.66, 0.40, 1), 22, 0.5)
    draw_image(cv, img2, SCX, 950, alpha=a * k2, center=True)
    rt = c.fx("recall_zouyan")
    if rt is not None:
        k = ease(rt / 0.8)
        fade = ease((rt - 2.5) / 2.5)
        # left: 仁义节俭 crumbling; right: 急法 不赦
        cv.drawRect(skia.Rect.MakeXYWH(90, 1080, 400, 140), paint(hexc("#E9DDC1"), alpha=a * k * (1 - 0.7 * fade)))
        draw_text(cv, "仁义节俭", 290, 1172, font("serif", "Black", 62), hexc("#3A2A18"), "center",
                  a * k * (1 - 0.8 * fade))
        cv.drawRect(skia.Rect.MakeXYWH(590, 1080, 400, 140), paint(hexc("#0A0A0C"), alpha=a * k))
        cv.drawRect(skia.Rect.MakeXYWH(590, 1080, 400, 140), paint(BRONZE, "stroke", 2, alpha=a * k))
        draw_text(cv, "急法 · 不赦", 790, 1172, font("serif", "Black", 58), hexc("#D8B677"), "center", a * k)
        if fade > 0:
            ink_splat(cv, 290, 1150, 90, hexc("#141210"), a * fade * 0.6, seed=4, k=fade)


# ------------------------------------------------------------------ S3 汉初
def robe_path(cx, top, s):
    return path_from("M -40 0 L 40 0 L 150 60 L 170 150 L 110 160 L 70 110 L 80 420 L -80 420 "
                     "L -70 110 L -110 160 L -170 150 L -150 60 Z", s, s, cx, top)


def st_han_question(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    red = ease(c.lt / 3.0)
    cv.drawCircle(820, 820, 420, paint(hexc("#B5302A"), alpha=a * 0.45 * red, blur=160))
    # stand
    cv.drawRect(skia.Rect.MakeXYWH(SCX - 210, 560, 420, 12), paint(hexc("#5A3A20"), alpha=a))
    cv.drawRect(skia.Rect.MakeXYWH(SCX - 6, 560, 12, 640), paint(hexc("#5A3A20"), alpha=a))
    rp = robe_path(SCX, 575, 1.05)
    cv.drawPath(rp, paint((0, 0, 0, 0.6), alpha=a, blur=14))
    cv.drawPath(rp, paint(hexc("#0D0D10"), alpha=a))
    cv.drawPath(rp, paint(hexc("#7A5A30"), "stroke", 3, alpha=a * 0.8))
    draw_text(cv, "秦的衣服", SCX, 1250 - 20, font("serif", "Bold", 40), c.text, "center", a)
    k = ease((c.lt - 2.0) / 0.6)
    draw_text(cv, "？", 850, 760, font("serif", "Black", 150), hexc("#E98C6A"), "center", a * k)


def snake_path(cut=0.0):
    p = skia.Path()
    pts = []
    for i in range(80):
        u = i / 79
        x = 110 + u * 860
        y = 860 + 70 * math.sin(u * 9.0) * (0.6 + 0.4 * u)
        if u > 0.5:
            x += cut * 40
            y += cut * 20
        else:
            x -= cut * 40
        pts.append((x, y))
    p.moveTo(*pts[0])
    for q in pts[1:40]:
        p.lineTo(*q)
    p.moveTo(*pts[40])
    for q in pts[41:]:
        p.lineTo(*q)
    return p, pts


def st_snake(cv, c, red=False):
    a = c.alpha * ease(c.lt / 0.8)
    ct = c.fx("snake_cut")
    cut = ease(ct / 0.5) if ct is not None else 0.0
    if red:
        cut = 1.0
    # ground line
    cv.drawLine(60, 1010, 1020, 1010, paint(hexc("#5A4A3A"), "stroke", 2, alpha=a * 0.6))
    p, pts = snake_path(cut)
    cv.drawPath(p, paint((1, 1, 1, 0.35), "stroke", 46, alpha=a, blur=10))
    cv.drawPath(p, paint(hexc("#EDEBE4"), "stroke", 36, alpha=a))
    for i in range(3, 78, 3):
        x, y = pts[i]
        cv.drawCircle(x, y, 4, paint(hexc("#B8B4A8"), alpha=a))
    # head
    hx, hy = pts[-1]
    cv.drawCircle(hx + 14, hy, 26, paint(hexc("#EDEBE4"), alpha=a))
    cv.drawCircle(hx + 22, hy - 8, 4, paint(hexc("#220000"), alpha=a))
    if ct is not None or red:
        k = ease((ct or 9) / 0.25)
        fade = 1 - ease(((ct or 9) - 0.25) / 0.8)
        mx, my = pts[40]
        cv.drawLine(mx + 140, my - 220, mx - 120, my + 200, paint(hexc("#FFF6E0"), "stroke", 8, alpha=a * k * fade))
        cv.drawLine(mx + 140, my - 220, mx - 120, my + 200, paint(hexc("#FFF6E0"), "stroke", 30, alpha=a * k * fade * 0.4, blur=12))
        ink_splat(cv, mx, my, 80, hexc("#1A1714"), a * 0.8, seed=8, k=clamp((ct or 9) / 1.2))
    # weeping old woman, after the cut
    wk = ease(((ct or -1) - 1.5) / 1.0) if not red else 1.0
    if wk > 0:
        kneeling_figure(cv, 880, 1008, 200, hexc("#CFC6B6"), a * wk * 0.85, facing=-1)
    ft = c.fx("red_flag")
    if ft is not None or red:
        k = ease((ft if ft is not None else 9) / 0.8)
        for i, x in enumerate((120, 230, 340)):
            yk = ease(((ft if ft is not None else 9) - i * 0.2) / 0.8)
            ytop = 520 + (1 - yk) * 200
            cv.drawRect(skia.Rect.MakeXYWH(x, ytop, 8, 470), paint(hexc("#3A2618"), alpha=a * yk))
            fl = path_from("M 0 0 L 120 12 L 110 60 L 124 120 L 0 110 Z", 1, 1, x + 8, ytop + 10)
            cv.drawPath(fl, paint(hexc("#C0302A"), alpha=a * yk))
    if red:
        seal(cv, 820, 620, 150, "赤帝之符", alpha=a * ease(c.lt / 0.8), rot=-5)


def st_snake_red(cv, c):
    st_snake(cv, c, red=True)
    caption(cv, c, "汉承尧运 · 协于火德", y=1220, size=40, alpha=ease((c.lt - 1.0) / 0.8))


def tablet(cv, cx, cy, w, h, color, text, alpha, text_col=None, edge=None):
    p = path_from(f"M {-w/2} {h/2} L {-w/2} {-h/2 + w/2} Q {-w/2} {-h/2} 0 {-h/2} Q {w/2} {-h/2} {w/2} {-h/2 + w/2} "
                  f"L {w/2} {h/2} Z", 1, 1, cx, cy)
    cv.drawPath(p, paint((0, 0, 0, 0.5), alpha=alpha, blur=10))
    cv.drawPath(p, paint(color, alpha=alpha))
    cv.drawPath(p, paint(edge or hexc("#E8D9B5"), "stroke", 3, alpha=alpha * 0.7))
    f = font("serif", "Black", int(w * 0.5))
    draw_vtext(cv, text, cx, cy - h * 0.28, f, text_col or hexc("#1A140C"), step=w * 0.58, alpha=alpha)


def st_shrine(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    vt = c.fx("versus")
    vk = ease(vt / 0.8) if vt is not None else 0.0
    plates = [("白帝", DE_COLOR["金"], hexc("#2A241C")), ("青帝", DE_COLOR["木"], hexc("#F2EAD8")),
              ("黄帝", DE_COLOR["土"], hexc("#2A1C08")), ("赤帝", DE_COLOR["火"], hexc("#FBEFD9"))]
    st = c.fx("shrine_black")
    n_show = 4 + (1 if st is not None else 0)
    for i, (txt, col, tc) in enumerate(plates):
        x = SCX + (i - (n_show - 1) / 2) * 180
        k = ease((c.lt - i * 0.25) / 0.5)
        tablet(cv, x, 820, 120, 330, col, txt, a * k * (1 - vk), tc)
    if st is not None:
        k = ease(st / 0.6)
        x = SCX + (4 - (n_show - 1) / 2) * 180
        y = 820 - (1 - k) * 200
        cv.drawCircle(x, 820, 160, paint(hexc("#7A8AA0"), alpha=a * 0.25 * k * (1 - vk), blur=50))
        tablet(cv, x, y, 120, 330, hexc("#0B0B0E"), "黑帝", a * k * (1 - vk), hexc("#E8DCC4"), edge=BRONZE)
        draw_text(cv, "北畤", x, 1060, font("serif", "Black", 44), c.text, "center", a * k * (1 - vk))
        draw_text(cv, "秦祭四帝", SCX - 90, 1060, font("serif", "Bold", 36), with_alpha(c.text, 0.7), "center",
                  a * k * (1 - vk))
    if vk > 0:
        # red flag vs black tablet
        for i, x in enumerate((250,)):
            cv.drawRect(skia.Rect.MakeXYWH(x - 120, 560, 8, 520), paint(hexc("#3A2618"), alpha=a * vk))
            fl = path_from("M 0 0 L 200 18 L 186 90 L 206 190 L 0 170 Z", 1, 1, x - 112, 570)
            cv.drawPath(fl, paint(hexc("#C0302A"), alpha=a * vk))
        draw_text(cv, "自称赤帝子", 250, 1160, font("serif", "Black", 48), hexc("#F08070"), "center", a * vk)
        tablet(cv, 830, 800, 140, 380, hexc("#0B0B0E"), "黑帝", a * vk, hexc("#E8DCC4"), edge=BRONZE)
        draw_text(cv, "却立黑帝祠", 830, 1160, font("serif", "Black", 48), hexc("#D8D0C0"), "center", a * vk)
        qk = ease((vt - 0.6) / 0.5)
        draw_text(cv, "？", SCX, 900, font("serif", "Black", 170), hexc("#F0C080"), "center", a * qk)


def st_zhangcang(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    han_figure(cv, 250, 1180, 420, hexc("#CDBB98"), a * 0.9, pose="scholar", facing=1)
    draw_text(cv, "张苍", 250, 1225, font("serif", "Bold", 36), c.text, "center", a)
    # calendar wheel
    cx, cy, r = 700, 820, 230
    cv.drawCircle(cx, cy, r, paint(hexc("#1A1512"), alpha=a))
    cv.drawCircle(cx, cy, r, paint(BRONZE, "stroke", 3, alpha=a))
    months = ["十月", "十一", "十二", "正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月"]
    for i, m in enumerate(months):
        ang = math.radians(-90 + i * 30)
        x, y = cx + r * 0.78 * math.cos(ang), cy + r * 0.78 * math.sin(ang)
        hl = i == 0
        draw_text(cv, m, x, y + 12, font("serif", "Black" if hl else "Bold", 34 if hl else 26),
                  hexc("#F0C27A") if hl else hexc("#9C8C70"), "center", a)
    draw_text(cv, "岁首", cx, cy - 10, font("serif", "Black", 50), hexc("#E8DCC4"), "center", a)
    draw_text(cv, "十月", cx, cy + 50, font("serif", "Black", 50), hexc("#F0C27A"), "center", a)
    k = ease((c.lt - 2.0) / 0.4)
    if k > 0:
        seal(cv, cx + 160, cy + 200, 120, "照旧", alpha=a * k, rot=8 * (1 - k) + 6)


# ------------------------------------------------------------------ S4 黄龙
def memorial_slips(cv, x, y, n, w, h, texts, alpha, seed=0, ink=None):
    for i in range(n):
        bamboo_slip(cv, x + i * (w + 6), y, w, h, alpha=alpha, seed=seed + i, cords=True)
    f = font("serif", "Black", int(w * 0.62), TC)
    for i, t in enumerate(texts):
        xi = x + (n - 1 - i) * (w + 6) + w / 2
        draw_vtext(cv, t, xi, y + 26, f, ink or SLIP_INK, step=w * 0.72, alpha=alpha)


def st_memorial(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    k1 = ease(c.lt / 1.0)
    m2 = c.fx("memorial2")
    shift = -140 * ease(m2 / 0.8) if m2 is not None else 0
    memorial_slips(cv, 160, 500 + shift, 8, 82, 420, ["色尚黃", "數用五", "定官名", "悉更秦之法"], a * k1 *
                   (1 - 0.5 * (ease(m2 / 0.8) if m2 is not None else 0)), seed=200)
    draw_text(cv, "贾谊的方案", 520, 960 + shift, font("serif", "Bold", 36), c.text, "center",
              a * k1 * (1 - (ease(m2 / 0.8) if m2 is not None else 0)))
    if m2 is not None:
        k = ease(m2 / 0.8)
        memorial_slips(cv, 230, 640 + (1 - k) * 200, 6, 90, 470, ["漢當土德", "黃龍見", "色上黃"], a * k, seed=300)
        draw_text(cv, "公孙臣上书", 540, 1170, font("serif", "Bold", 38), c.text, "center", a * k)
    sr = c.fx("seal_reject")
    if sr is not None:
        k = ease(sr / 0.25)
        sc = 1.6 - 0.6 * k
        shake = math.sin(sr * 60) * 6 * (1 - clamp(sr / 0.4))
        cv.save()
        cv.translate(760 + shake, 900)
        cv.scale(sc, sc)
        seal(cv, 0, 0, 170, "驳", alpha=a * k, rot=-8)
        cv.restore()
    tag(cv, c, "示意", 900, 520, a)


def _smooth(u, a, b):
    k = clamp((u - a) / (b - a))
    return k * k * (3 - 2 * k)


def dragon_geom(cx, cy, s, n=220):
    """Spine points (tail -> head) and half-widths of a sinuous Han-style dragon facing right."""
    pts, wid = [], []
    for i in range(n):
        u = i / (n - 1)
        x = cx + s * (-430 + 800 * u)
        amp = 105 * (0.35 + 0.65 * math.sin(math.pi * min(1.0, u * 1.05)))
        y = cy + s * (amp * math.sin(2 * math.pi * 1.35 * u + 0.9) - 95 * _smooth(u, 0.78, 1.0) + 20)
        pts.append((x, y))
        w = 3 + 33 * (math.sin(math.pi * min(1.0, u / 0.92)) ** 0.7)
        w = w * (1 - 0.35 * _smooth(u, 0.80, 0.97))
        wid.append(s * w)
    return pts, wid


def _edges(pts, wid, m):
    left, right, nrm = [], [], []
    n = len(pts)
    for i in range(m):
        x, y = pts[i]
        x2, y2 = pts[min(i + 1, n - 1)]
        x1, y1 = pts[max(i - 1, 0)]
        tx, ty = x2 - x1, y2 - y1
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        if ny > 0:  # make 'left' the upper side
            nx, ny = -nx, -ny
        nrm.append((nx, ny, tx / L, ty / L))
        left.append((x + nx * wid[i], y + ny * wid[i]))
        right.append((x - nx * wid[i], y - ny * wid[i]))
    return left, right, nrm


def _poly(points, close=True):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def _leg(cv, x, y, s, dirx, gold, line, alpha, lw, phase=0.0):
    """bent leg with three claws; (x, y) = hip on the belly edge."""
    kx, ky = x + 26 * s * dirx, y + 52 * s
    fx, fy = kx - 6 * s * dirx + 30 * s, ky + 34 * s
    thigh = [(x - 12 * s, y), (x + 14 * s, y), (kx + 7 * s, ky), (kx - 7 * s, ky)]
    shin = [(kx - 6 * s, ky), (kx + 6 * s, ky), (fx + 4 * s, fy), (fx - 4 * s, fy)]
    for poly in (thigh, shin):
        p = _poly(poly)
        cv.drawPath(p, paint(gold, alpha=alpha))
        cv.drawPath(p, paint(line, "stroke", lw * 0.8, alpha=alpha))
    for k, ang in enumerate((-0.5, 0.0, 0.5)):
        cl = skia.Path()
        cl.moveTo(fx, fy)
        ex, ey = fx + 22 * s * math.cos(ang), fy + 22 * s * math.sin(ang) + 4 * s
        cl.quadTo(fx + 14 * s * math.cos(ang), fy + 14 * s * math.sin(ang) - 6 * s, ex, ey)
        cv.drawPath(cl, paint(line, "stroke", lw * 1.1, alpha=alpha))
    # elbow flame
    fl = skia.Path()
    fl.moveTo(kx, ky - 4 * s)
    fl.quadTo(kx - 26 * s * dirx, ky - 6 * s, kx - 34 * s * dirx, ky - 26 * s)
    cv.drawPath(fl, paint(line, "stroke", lw * 0.8, alpha=alpha))


def draw_dragon(cv, cx, cy, s, color, alpha, reveal=1.0, glow=True, fill=None):
    """color = outline/highlight colour; fill = body colour (defaults to a gold ramp)."""
    pts, wid = dragon_geom(cx, cy, s)
    n = len(pts)
    m = max(3, int(n * clamp(reveal)))
    left, right, nrm = _edges(pts, wid, m)
    body = _poly(left + right[::-1])
    line = hexc("#5E3F12") if fill is None else color
    gold = fill if fill is not None else hexc("#E2B556")
    lw = max(1.2, 3.2 * s)
    if glow:
        cv.drawPath(body, paint(hexc("#F6D27A"), alpha=alpha * 0.45, blur=26 * s + 2))
    cv.drawPath(body, paint(gold, alpha=alpha))
    # belly band (lighter) on the lower side
    belly = _poly([(pts[i][0] - nrm[i][0] * wid[i] * 0.35, pts[i][1] - nrm[i][1] * wid[i] * 0.35) for i in range(m)]
                  + right[::-1])
    cv.drawPath(belly, paint(hexc("#F5DFA0") if fill is None else mix(fill, color, 0.25), alpha=alpha * 0.9))
    for i in range(4, m - 2, 4):
        bx0 = pts[i][0] - nrm[i][0] * wid[i] * 0.35
        by0 = pts[i][1] - nrm[i][1] * wid[i] * 0.35
        cv.drawLine(bx0, by0, right[i][0], right[i][1], paint(line, "stroke", lw * 0.45, alpha=alpha * 0.6))
    # scales: small arcs pointing to the tail
    for i in range(8, m - 6, 6):
        for k in (-0.05, 0.35, 0.7):
            px = pts[i][0] + nrm[i][0] * wid[i] * k
            py = pts[i][1] + nrm[i][1] * wid[i] * k
            r = wid[i] * 0.28
            if r < 2:
                continue
            ang = math.degrees(math.atan2(nrm[i][3], nrm[i][2]))
            arc = skia.Path()
            arc.arcTo(skia.Rect.MakeLTRB(px - r, py - r, px + r, py + r), ang - 90, 180, True)
            cv.drawPath(arc, paint(line, "stroke", lw * 0.45, alpha=alpha * 0.55))
    # dorsal spikes
    for i in range(10, m - 8, 7):
        x0, y0 = left[i]
        x1, y1 = left[min(i + 5, m - 1)]
        nx, ny = nrm[i][0], nrm[i][1]
        h = (10 + 10 * math.sin(i * 0.7) ** 2) * s
        sp = _poly([(x0, y0), ((x0 + x1) / 2 + nx * h - nrm[i][2] * 4 * s, (y0 + y1) / 2 + ny * h - nrm[i][3] * 4 * s), (x1, y1)])
        cv.drawPath(sp, paint(gold, alpha=alpha))
        cv.drawPath(sp, paint(line, "stroke", lw * 0.6, alpha=alpha))
    # legs (hind near the tail, fore near the neck)
    for u, dirx in ((0.30, -1), (0.38, -1), (0.70, 1), (0.77, 1)):
        i = int(u * (n - 1))
        if i < m:
            _leg(cv, right[i][0], right[i][1], s, dirx, gold, line, alpha, lw)
    cv.drawPath(body, paint(line, "stroke", lw, alpha=alpha))
    # tail tuft
    if m > 4:
        tx, ty = pts[0]
        for k, (dx, dy) in enumerate(((-40, -30), (-52, 2), (-38, 30))):
            tf = skia.Path()
            tf.moveTo(tx, ty)
            tf.quadTo(tx + dx * 0.4 * s, ty + dy * 0.9 * s, tx + dx * s, ty + dy * s)
            cv.drawPath(tf, paint(line if fill is None else color, "stroke", lw, alpha=alpha))
    # head
    if m >= n - 2:
        hx, hy = pts[-1]
        tx, ty = nrm[-1][2], nrm[-1][3]
        ang = math.degrees(math.atan2(ty, tx))
        cv.save()
        cv.translate(hx, hy)
        cv.rotate(ang * 0.4)
        cv.scale(s * 1.3, s * 1.3)
        mane = [path_from("M -6 -18 C -40 -40 -70 -30 -92 -54"), path_from("M -4 -6 C -44 -14 -76 4 -104 -10"),
                path_from("M -2 8 C -36 18 -60 36 -90 30")]
        for mp in mane:
            cv.drawPath(mp, paint(line if fill is None else color, "stroke", 4.0, alpha=alpha))
        upper = path_from("M -10 -22 C 20 -40 58 -36 88 -26 C 100 -22 108 -16 104 -8 L 60 -2 C 40 0 10 2 -10 6 Z")
        lower = path_from("M -6 8 C 20 14 46 18 74 26 C 80 30 76 36 68 36 C 40 34 10 28 -8 20 Z")
        for hp in (upper, lower):
            cv.drawPath(hp, paint(gold, alpha=alpha))
            cv.drawPath(hp, paint(line, "stroke", 3.2, alpha=alpha))
        for k in range(4):  # teeth
            x = 30 + k * 14
            cv.drawPath(_poly([(x, -1), (x + 5, 9), (x + 10, -1)]), paint(hexc("#FFF7E0"), alpha=alpha))
        cv.drawPath(path_from("M 22 -26 C 30 -34 44 -34 50 -26"), paint(line, "stroke", 3, alpha=alpha))
        cv.drawOval(skia.Rect.MakeLTRB(28, -25, 44, -16), paint(hexc("#FFFFFF"), alpha=alpha))
        cv.drawCircle(37, -20.5, 3.2, paint(hexc("#2A1A08"), alpha=alpha))
        antler = path_from("M 4 -30 C -6 -62 -30 -80 -58 -86 M -18 -64 C -12 -82 -18 -94 -10 -104 "
                           "M 14 -32 C 10 -58 -2 -72 -20 -84")
        cv.drawPath(antler, paint(line if fill is None else color, "stroke", 5, alpha=alpha))
        whisker = path_from("M 100 -14 C 136 -20 150 -56 132 -78 C 124 -88 110 -84 112 -72")
        cv.drawPath(whisker, paint(line if fill is None else color, "stroke", 2.6, alpha=alpha))
        cv.restore()


def st_dragon(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    clouds = [(160, 560, 120, False), (880, 600, 140, True), (300, 1120, 130, False), (820, 1140, 110, True),
              (540, 520, 80, False)]
    for (x, y, s, fl) in clouds:
        cloud_swirl(cv, x + 6 * math.sin(c.lt * 0.4 + x), y, s, hexc("#8E7440"), alpha=a * 0.5, width=3, flip=fl)
    dt = c.fx("dragon")
    if dt is not None:
        rv = ease_out(dt / 2.6)
        bob = 6 * math.sin(dt * 0.9)
        cv.drawCircle(SCX, 850, 380, paint(hexc("#E8B850"), alpha=a * 0.18 * rv, blur=140))
        draw_dragon(cv, SCX - 10, 860 + bob, 0.98, GOLD, a, reveal=rv, glow=True)
        k = ease((dt - 2.4) / 0.6)
        tag(cv, c, "史书记载", 80, 520, a * k)
        draw_text(cv, "黄龙见成纪", SCX, 1205, font("serif", "Black", 56), GOLD, "center", a * k,
                  shadow=((0, 0, 0, 0.7), 6, (0, 2)))


def st_zhangcang_exit(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    k = ease((c.lt - 1.0) / 3.5)
    han_figure(cv, 420 + 380 * k, 1150, 420, hexc("#CDBB98"), a * (1 - 0.85 * k), pose="scholar", facing=1)
    # empty mat
    cv.drawRect(skia.Rect.MakeXYWH(250, 1150, 300, 18), paint(hexc("#6B5236"), alpha=a))
    draw_text(cv, "张丞相由此自绌，谢病称老", SCX, 640, font("serif", "Black", 52), c.text, "center", a)


def st_smoke(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    bt = c.fx("smoke_blow")
    blow = ease(bt / 1.6) if bt is not None else 0.0
    cols = [DE_COLOR["火"], DE_COLOR["土"], hexc("#7FB0A0"), hexc("#E0DACA"), hexc("#6C7A92")]
    rng = np.random.default_rng(3)
    # censer
    cv.drawPath(path_from("M -60 0 L 60 0 L 40 60 L -40 60 Z", 1, 1, SCX, 1130), paint(BRONZE, alpha=a * (1 - blow)))
    for i in range(26):
        u = i / 25
        x = SCX + 80 * math.sin(u * 6 + c.lt * 0.5) * u + blow * (300 + 400 * u) * (0.6 + rng.random())
        y = 1110 - u * 560 - blow * 60 * rng.random()
        r = 40 + 70 * u
        cv.drawCircle(x, y, r * (1 + blow), paint(cols[i % 5], alpha=a * 0.22 * (1 - blow), blur=r * 0.5))
    tag(cv, c, "望气（示意）", 80, 520, a * (1 - blow))
    if bt is not None:
        k = ease((bt - 1.0) / 0.8)
        draw_text(cv, "诈", SCX, 860, font("serif", "Black", 200), CINNABAR, "center", a * k * 0.9)


# ------------------------------------------------------------------ S5 太初
def hall(cv, cx, y, w, color, alpha):
    roof = path_from(f"M {-w/2-60} 70 Q {-w/2} 40 {-w/2+40} 0 L {w/2-40} 0 Q {w/2} 40 {w/2+60} 70 Z", 1, 1, cx, y)
    cv.drawPath(roof, paint(color, alpha=alpha))
    for k in range(6):
        x = cx - w / 2 + 30 + k * (w - 60) / 5
        cv.drawRect(skia.Rect.MakeXYWH(x - 8, y + 70, 16, 150), paint(color, alpha=alpha * 0.8))
    cv.drawRect(skia.Rect.MakeXYWH(cx - w / 2 - 30, y + 220, w + 60, 20), paint(color, alpha=alpha))
    cv.drawRect(skia.Rect.MakeXYWH(cx - w / 2 - 60, y + 240, w + 120, 22), paint(color, alpha=alpha * 0.8))


def st_court(cv, c):
    a = c.alpha * ease(c.lt / 0.8)
    hall(cv, SCX, 480, 560, hexc("#C8A56A") if c.dark else hexc("#3A2A18"), a * 0.85)
    q1 = c.line("S5_03")
    q2 = c.line("S5_05")
    if q1 and c.t >= q1["t0"] - 0.2:
        k = ease((c.t - q1["t0"]) / 0.6) * (1 - ease((c.t - (q2["t0"] if q2 else 1e9) + 0.3) / 0.5))
        draw_text(cv, "今宜何以为正朔？", SCX, 900, font("serif", "Black", 70), c.text, "center", a * k)
        draw_text(cv, "服色何上？", SCX, 1010, font("serif", "Black", 70), c.text, "center", a * k)
    if q2 and c.t >= q2["t0"] - 0.2:
        k = ease((c.t - q2["t0"]) / 0.6)
        f = font("serif", "Black", 60)
        draw_text(cv, "帝王必改正朔，易服色，", SCX, 880, f, c.text, "center", a * k)
        s2 = "所以明受命于天也"
        draw_text(cv, s2, SCX, 990, f, c.text, "center", a * k)
        kt = c.kw_time("S5_07", "明")
        mk = ease((c.t - kt) / 0.5)
        if mk > 0:
            wbefore = f.measureText("所以")
            total = f.measureText(s2)
            x = SCX - total / 2 + wbefore + f.measureText("明") / 2
            cv.drawCircle(x, 970, 52, paint(CINNABAR, "stroke", 6, alpha=a * mk))


def seal_glyphs(cv, cx, cy, size, color, alpha, seed=5):
    """five abstract seal-script-like glyph blocks (示意, not real text)."""
    rng = np.random.default_rng(seed)
    cells = [(0.25, -0.33, 0.42, 0.28), (0.25, 0.0, 0.42, 0.28), (0.25, 0.33, 0.42, 0.28),
             (-0.25, -0.2, 0.42, 0.45), (-0.25, 0.25, 0.42, 0.40)]
    for ci, (ux, uy, uw, uh) in enumerate(cells):
        x0, y0 = cx + (ux - uw / 2) * size, cy + (uy - uh / 2) * size
        w, h = uw * size, uh * size
        p = paint(color, "stroke", size * 0.026, alpha=alpha, cap="square", join="miter")
        kind = ci % 5
        X = lambda u: x0 + w * u
        Y = lambda v: y0 + h * v
        if kind == 0:   # 口 with inner stroke + cap
            cv.drawRect(skia.Rect.MakeLTRB(X(0.2), Y(0.35), X(0.8), Y(0.85)), p)
            cv.drawLine(X(0.1), Y(0.18), X(0.9), Y(0.18), p)
            cv.drawLine(X(0.5), Y(0.05), X(0.5), Y(0.35), p)
        elif kind == 1:  # 冂 with two inner verticals
            cv.drawPath(_poly([(X(0.12), Y(0.9)), (X(0.12), Y(0.12)), (X(0.88), Y(0.12)), (X(0.88), Y(0.9))], False), p)
            cv.drawLine(X(0.38), Y(0.3), X(0.38), Y(0.75), p)
            cv.drawLine(X(0.62), Y(0.3), X(0.62), Y(0.75), p)
            cv.drawLine(X(0.3), Y(0.52), X(0.7), Y(0.52), p)
        elif kind == 2:  # three horizontals + hook
            for v in (0.15, 0.45, 0.75):
                cv.drawLine(X(0.12), Y(v), X(0.88), Y(v), p)
            cv.drawPath(_poly([(X(0.5), Y(0.15)), (X(0.5), Y(0.92)), (X(0.3), Y(0.92))], False), p)
        elif kind == 3:  # tall: 尸-like frame + inner zigzag
            cv.drawPath(_poly([(X(0.88), Y(0.08)), (X(0.12), Y(0.08)), (X(0.12), Y(0.94))], False), p)
            cv.drawLine(X(0.12), Y(0.3), X(0.88), Y(0.3), p)
            cv.drawPath(_poly([(X(0.35), Y(0.45)), (X(0.8), Y(0.45)), (X(0.35), Y(0.7)), (X(0.8), Y(0.7)),
                               (X(0.8), Y(0.92))], False), p)
        else:  # 章-like: cap + 曰 + long vertical
            cv.drawLine(X(0.15), Y(0.1), X(0.85), Y(0.1), p)
            cv.drawRect(skia.Rect.MakeLTRB(X(0.25), Y(0.22), X(0.75), Y(0.52)), p)
            cv.drawLine(X(0.25), Y(0.37), X(0.75), Y(0.37), p)
            cv.drawLine(X(0.1), Y(0.64), X(0.9), Y(0.64), p)
            cv.drawLine(X(0.5), Y(0.52), X(0.5), Y(0.95), p)


def st_seal_five(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    st = c.fx("seal_stamp")
    k = ease(st / 0.3) if st is not None else 0.0
    # calendar strip on the left: 正月 → 岁首
    bamboo_slip(cv, 140, 520, 90, 560, alpha=a, seed=500, cords=False)
    draw_vtext(cv, "正月歲首", 185, 560, font("serif", "Black", 66, TC), SLIP_INK, step=78, alpha=a)
    # seal impression
    size = 380
    cx, cy = 640, 800
    if k > 0:
        cv.save()
        sc = 1.25 - 0.25 * k
        cv.translate(cx, cy)
        cv.scale(sc, sc)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-size / 2, -size / 2, size, size), 14, 14)
        cv.drawRRect(r, paint(CINNABAR, "stroke", 14, alpha=a * k))
        seal_glyphs(cv, 0, 0, size * 0.9, CINNABAR, a * k)
        cv.restore()
    draw_text(cv, "官印五字（示意）", cx, 1080, font("serif", "Bold", 38), c.text, "center", a * k)
    draw_text(cv, "土数五", cx, 1150, font("serif", "Black", 48), CINNABAR if not c.dark else GOLD, "center", a * k)


def big_disc(cv, cx, cy, r, el, label, alpha):
    cv.drawCircle(cx, cy, r, paint((0, 0, 0, 0.45), alpha=alpha, blur=14))
    cv.drawCircle(cx, cy, r, paint(DE_COLOR[el], alpha=alpha))
    cv.drawCircle(cx, cy, r, paint(hexc("#E8D9B5"), "stroke", 3, alpha=alpha * 0.7))
    draw_text(cv, el, cx, cy + r * 0.3, font("serif", "Black", int(r * 0.9)), DE_INK[el], "center", alpha)
    draw_text(cv, label, cx, cy + r + 62, font("serif", "Black", 44), INK, "center", alpha)


def st_book_review(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    big_disc(cv, 280, 780, 150, "水", "秦", a)
    big_disc(cv, 800, 780, 150, "土", "汉 · 太初", a * ease((c.lt - 0.5) / 0.6))
    k = ease((c.lt - 1.2) / 0.6)
    p = skia.Path()
    p.moveTo(640, 780)
    p.lineTo(450, 780)
    cv.drawPath(partial_path(p, k), paint(CINNABAR, "stroke", 12, alpha=a))
    if k > 0.95:
        cv.drawPath(path_from("M 0 0 L 40 -26 L 40 26 Z", 1, 1, 430, 780), paint(CINNABAR, alpha=a))
    draw_text(cv, "土克水", SCX, 740, font("serif", "Black", 54), CINNABAR, "center", a * k)
    draw_text(cv, "遂顺黄德", SCX, 1150, font("serif", "Black", 64), hexc("#3A2410"), "center", a * k)


def st_simaqian(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    kneeling_figure(cv, 300, 1130, 330, hexc("#3A2A18") if not c.dark else FIG, a, facing=1)
    bamboo_slip(cv, 400, 900, 260, 46, alpha=a, seed=600, cords=False)
    draw_text(cv, "司马迁", 300, 1190, font("serif", "Bold", 36), c.text, "center", a)
    q = c.line("S5_15")
    if q:
        k = ease((c.t - (q["t0"] + q["dur"] * 0.85)) / 0.5)
        draw_text(cv, "何哉？", 760, 760, font("serif", "Black", 150), CINNABAR, "center", a * k)


# ------------------------------------------------------------------ S6 相生
CHAIN = [("伏羲", "木"), ("神农", "火"), ("黄帝", "土"), ("少昊", "金"),
         ("颛顼", "水"), ("帝喾", "木"), ("尧", "火"), ("舜", "土"),
         ("禹", "金"), ("汤", "水"), ("周", "木"), ("汉", "火")]


def chain_pos(i):
    row = i // 4
    col = i % 4
    if row == 1:
        col = 3 - col
    x = 170 + col * 247
    y = 560 + row * 270
    return x, y


def st_chain(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    ln = c.line("S6_04")
    prog = (c.t - ln["t0"]) / ln["dur"] if ln else 1.0
    lit = clamp(prog) * 12.5 if prog < 1.2 else 12.5
    if c.t > (ln["t1"] if ln else 0):
        lit = 12.5
    gap_t = c.fx("chain_gap")
    # connectors
    for i in range(11):
        x0, y0 = chain_pos(i)
        x1, y1 = chain_pos(i + 1)
        k = clamp(lit - i - 0.5)
        col = with_alpha(c.text, 0.55)
        cv.drawLine(x0, y0, x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, paint(col, "stroke", 4, alpha=a))
        if k > 0.9 and y0 == y1:
            draw_text(cv, "生", (x0 + x1) / 2, y0 - 22, font("serif", "Bold", 30), col, "center", a)
    for i, (name, el) in enumerate(CHAIN):
        x, y = chain_pos(i)
        k = ease(clamp(lit - i))
        s = 150
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - s / 2, y - s / 2, s, s), 12, 12)
        cv.drawRRect(r, paint(DE_COLOR[el], alpha=a * (0.25 + 0.75 * k)))
        cv.drawRRect(r, paint(hexc("#F5E8C8"), "stroke", 3, alpha=a * (0.4 + 0.6 * k)))
        draw_text(cv, el, x, y - 8, font("serif", "Black", 64), DE_INK[el], "center", a * (0.3 + 0.7 * k))
        draw_text(cv, name, x, y + 52, font("serif", "Bold", 34), DE_INK[el], "center", a * (0.3 + 0.7 * k))
    # 闰 slots
    if gap_t is not None:
        k = ease(gap_t / 0.8)
        for (i0, i1, who) in ((0, 1, "共工"), (10, 11, "秦")):
            x0, y0 = chain_pos(i0)
            x1, y1 = chain_pos(i1)
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(mx - 18, my - 60, 36, 120), 6, 6)
            cv.drawRRect(r, paint(hexc("#8C8A86"), alpha=a * k))
            cv.drawRRect(r, paint(hexc("#2A2622"), "stroke", 2, alpha=a * k))
            draw_text(cv, who, mx, my + 100, font("serif", "Black", 36), hexc("#D8D4CC"), "center", a * k)
            draw_text(cv, "闰", mx, my + 14, font("serif", "Black", 30), hexc("#1E1C1A"), "center", a * k)


def st_run_slot(cv, c):
    st_wheel_stage(cv, c)


def st_ke_vs_sheng(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    # left: 相克
    cx1, cx2, cy = 290, 790, 800
    draw_text(cv, "相克", cx1, 590, font("serif", "Black", 76), c.text, "center", a)
    draw_text(cv, "相生", cx2, 590, font("serif", "Black", 76), c.text, "center", a)
    cv.drawCircle(cx1 - 70, cy, 70, paint(DE_COLOR["水"], alpha=a))
    cv.drawCircle(cx1 - 70, cy, 70, paint(hexc("#E8D9B5"), "stroke", 3, alpha=a))
    cv.drawCircle(cx1 + 80, cy, 70, paint(DE_COLOR["土"], alpha=a))
    # strike
    cv.drawPath(path_from("M 0 -40 L -60 0 L 0 40 Z", 1, 1, cx1 + 4, cy), paint(CINNABAR, alpha=a))
    draw_text(cv, "打下来的天下", cx1, 960, font("serif", "Bold", 44), c.text, "center", a)
    draw_text(cv, "后一个打败前一个", cx1, 1020, font("sans", "Medium", 32), with_alpha(c.text, 0.8), "center", a)
    # right: 相生 mother -> child
    cv.drawCircle(cx2 - 50, cy, 85, paint(DE_COLOR["火"], alpha=a))
    cv.drawCircle(cx2 + 80, cy + 20, 55, paint(DE_COLOR["土"], alpha=a))
    p = skia.Path()
    p.moveTo(cx2 - 50 + 60, cy - 60)
    p.quadTo(cx2 + 40, cy - 110, cx2 + 80, cy - 40)
    cv.drawPath(p, paint(c.text, "stroke", 4, alpha=a))
    draw_text(cv, "传下来的天下", cx2, 960, font("serif", "Bold", 44), c.text, "center", a)
    draw_text(cv, "前一个生出后一个", cx2, 1020, font("sans", "Medium", 32), with_alpha(c.text, 0.8), "center", a)
    cv.drawLine(SCX, 620, SCX, 1080, paint(with_alpha(c.text, 0.4), "stroke", 2, alpha=a))


def st_suihong(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    ln = c.line("S6_22")
    dk = ease((c.t - c.kw_time("S6_22", "他因此")) / 1.0) if ln else 0.0
    tint = (hexc("#D0AC6E"), hexc("#AF8A50"))
    grey = (hexc("#8A877F"), hexc("#6E6B64"))
    for i, txt in enumerate(["漢家堯後", "有傳國之運"]):
        x = 640 - i * 190
        bamboo_slip(cv, x - 70, 500, 140, 680, alpha=a, seed=700 + i, tint=grey if dk > 0.5 else tint, cords=True)
        draw_vtext(cv, txt, x, 540, font("serif", "Black", 92, TC), SLIP_INK, step=110, alpha=a * (1 - 0.5 * dk))
    draw_text(cv, "汉昭帝时 · 眭弘上书", 870, 1150, font("serif", "Bold", 34), c.text, "center", a)
    tag(cv, c, "示意", 820, 520, a)


def st_wangmang(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    rows = [(("尧", "火"), ("舜", "土"), "让"), (("汉", "火"), ("新", "土"), "受禅")]
    for r, ((n0, e0), (n1, e1), verb) in enumerate(rows):
        y = 620 + r * 230
        k = ease((c.lt - r * 1.2) / 0.6)
        for j, (n, e) in enumerate(((n0, e0), (n1, e1))):
            x = 300 + j * 480
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 85, y - 85, 170, 170), 14, 14)
            cv.drawRRect(rr, paint(DE_COLOR[e], alpha=a * k))
            cv.drawRRect(rr, paint(hexc("#F5E8C8"), "stroke", 3, alpha=a * k))
            draw_text(cv, n, x, y + 30, font("serif", "Black", 92), DE_INK[e], "center", a * k)
            draw_text(cv, e + "德", x, y + 130, font("serif", "Bold", 34), c.text, "center", a * k)
        p = skia.Path()
        p.moveTo(400, y)
        p.lineTo(670, y)
        cv.drawPath(p, paint(c.text, "stroke", 5, alpha=a * k))
        cv.drawPath(path_from("M 0 -18 L 30 0 L 0 18 Z", 1, 1, 670, y), paint(c.text, alpha=a * k))
        draw_text(cv, verb, 535, y - 22, font("serif", "Black", 40), hexc("#FFD79A"), "center", a * k)
    q = c.line("S6_24")
    if q:
        k = ease((c.t - q["t0"]) / 0.6)
        draw_text(cv, "火德销尽 · 土德当代", SCX, 1175, font("serif", "Black", 58), hexc("#FFD79A"), "center", a * k,
                  shadow=((0, 0, 0, 0.6), 5, (0, 2)))


# ------------------------------------------------------------------ S7
def st_altar(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    at = c.fx("altar_red")
    rk = ease(at / 1.6) if at is not None else 0.0
    cx, base = SCX, 1080
    for k, (rx, ry, hgt) in enumerate(((380, 90, 60), (280, 66, 60), (180, 44, 60))):
        y = base - k * 70
        col = mix(hexc("#D9CDB4"), hexc("#C0392B"), rk)
        side = skia.Path()
        side.addOval(skia.Rect.MakeLTRB(cx - rx, y - ry, cx + rx, y + ry))
        cv.drawRect(skia.Rect.MakeLTRB(cx - rx, y - hgt, cx + rx, y), paint(mix(col, hexc("#000000"), 0.35), alpha=a))
        cv.drawOval(skia.Rect.MakeLTRB(cx - rx, y - ry, cx + rx, y + ry), paint(mix(col, hexc("#000000"), 0.35), alpha=a))
        cv.drawOval(skia.Rect.MakeLTRB(cx - rx, y - hgt - ry, cx + rx, y - hgt + ry), paint(col, alpha=a))
        cv.drawOval(skia.Rect.MakeLTRB(cx - rx, y - hgt - ry, cx + rx, y - hgt + ry),
                    paint(hexc("#3A2418"), "stroke", 2, alpha=a * 0.6))
    draw_text(cv, "洛阳城南 · 郊兆", SCX, 1205, font("serif", "Bold", 38), c.text, "center", a)
    tag(cv, c, "示意", 80, 520, a)
    if rk > 0:
        img = stone_text_image("始正火德", "serif", "Black", 96, (1.0, 0.86, 0.6, 1), 9, 0.4)
        draw_image(cv, img, SCX, 640, alpha=a * rk, center=True)


def st_three_virtues(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    items = [("水", "汉初", "张苍定"), ("土", "太初", "公元前104年"), ("火", "建武", "公元26年")]
    for i, (el, era, when) in enumerate(items):
        x = 210 + i * 330
        kt = c.kw_time("S7_04", el + "德")
        k = ease((c.t - kt + 0.2) / 0.5)
        r = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 110, 700, 220, 220), 16, 16)
        cv.drawRRect(r, paint((0, 0, 0, 0.4), alpha=a * k, blur=12))
        cv.drawRRect(r, paint(DE_COLOR[el], alpha=a * k))
        cv.drawRRect(r, paint(hexc("#F5E8C8"), "stroke", 3, alpha=a * k))
        draw_text(cv, el, x, 850, font("serif", "Black", 130), DE_INK[el], "center", a * k)
        draw_text(cv, era, x, 990, font("serif", "Black", 46), c.text, "center", a * k)
        draw_text(cv, when, x, 1045, font("sans", "Medium", 30), with_alpha(c.text, 0.8), "center", a * k)
    draw_text(cv, "同一个汉朝", SCX, 620, font("serif", "Black", 56), c.text, "center", a)


# ------------------------------------------------------------------ S8 / S9
def st_slip_wanshi(cv, c):
    a = c.alpha * ease(c.lt / 0.6)
    for i, (txt, x) in enumerate((("二世三世至于萬世", 640), ("傳之無窮", 450))):
        k = ease((c.lt - i * 0.8) / 0.6)
        bamboo_slip(cv, x - 64, 470, 128, 760, alpha=a * k, seed=800 + i)
        draw_vtext(cv, txt, x, 500, font("serif", "Black", 76, TC), SLIP_INK, step=88, alpha=a * k,
                   reveal=(c.lt - i * 0.8) / 0.15)
    kt = c.kw_time("S8_05", "终")
    k = ease((c.t - kt) / 0.6)
    if k > 0:
        img = stone_text_image("終始", "serif", "Black", 150, (0.95, 0.88, 0.72, 1), 31, 0.5, TC, True)
        draw_image(cv, img, 870, 850, alpha=a * k, center=True)
        cv.drawCircle(870, 760, 98, paint(CINNABAR, "stroke", 7, alpha=a * k))


def st_end_card(cv, c):
    a = c.alpha * ease(c.lt / 1.0)
    img = stone_text_image("五德终始", "serif", "Black", 140, (0.93, 0.86, 0.70, 1.0), 11, 0.55)
    draw_image(cv, img, SCX, 640, alpha=a, center=True)
    draw_text(cv, "命理与正统 · 第一期", SCX, 520, font("serif", "Bold", 38), hexc("#C8A56A"), "center", a, spacing=4)
    lines = ["主要史料", "《史记》秦始皇本纪 · 封禅书 · 孟子荀卿列传", "张丞相列传 · 屈原贾生列传 · 高祖本纪 · 孝文本纪",
             "《汉书》郊祀志 · 律历志 · 高帝纪 · 王莽传 · 眭弘传", "《吕氏春秋·应同》 · 《后汉书·光武帝纪》",
             "参考：顾颉刚《五德终始说下的政治和历史》（1930）", "引文据通行点校本，简体转写"]
    for i, s in enumerate(lines):
        f = font("serif", "Bold", 36) if i == 0 else font("sans", "Regular", 28)
        draw_text(cv, s, SCX, 820 + i * 56 + (10 if i else 0), f, hexc("#E3D6B8") if i else hexc("#C8A56A"),
                  "center", a * ease((c.lt - 0.8 - i * 0.12) / 0.6))


STAGES = {
    "slip_open": st_slip_open, "title_card": st_title_card, "map_qi": st_map_qi, "wheel_stage": st_wheel_stage,
    "lscq_book": st_lscq_book, "slip_prophecy": st_slip_prophecy, "broom": st_broom,
    "zouyan_scroll": st_zouyan_scroll, "zouyan_scroll2": st_zouyan_scroll2, "qin_unify": st_qin_unify,
    "qin_list": st_qin_list, "qin_law": st_qin_law, "han_question": st_han_question, "snake": st_snake,
    "snake_red": st_snake_red, "shrine": st_shrine, "zhangcang": st_zhangcang, "memorial": st_memorial,
    "dragon": st_dragon, "zhangcang_exit": st_zhangcang_exit, "smoke": st_smoke, "court": st_court,
    "seal_five": st_seal_five, "book_review": st_book_review, "simaqian": st_simaqian, "chain": st_chain,
    "run_slot": st_run_slot, "ke_vs_sheng": st_ke_vs_sheng, "suihong": st_suihong, "wangmang": st_wangmang,
    "altar": st_altar, "three_virtues": st_three_virtues, "slip_wanshi": st_slip_wanshi, "end_card": st_end_card,
}
