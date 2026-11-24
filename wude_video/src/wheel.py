"""五德轮盘 — the always-on wheel (mini HUD in the top-right, big on stage)."""
import math
import skia
from gfx import (DE_COLOR, DE_INK, BRONZE, CINNABAR, hexc, mix, paint, font, draw_text, clamp,
                 ease, with_alpha)

ORDER_KE = ["土", "木", "金", "火", "水"]      # 相胜(相克): 后一个克前一个
ORDER_SHENG = ["木", "火", "土", "金", "水"]   # 相生: 前一个生后一个
KE_TEXT = {("土", "木"): "木克土", ("木", "金"): "金克木", ("金", "火"): "火克金",
           ("火", "水"): "水克火", ("水", "土"): "土克水"}
SHENG_TEXT = {("木", "火"): "木生火", ("火", "土"): "火生土", ("土", "金"): "土生金",
              ("金", "水"): "金生水", ("水", "木"): "水生木"}

MINI = (912.0, 300.0, 104.0)
BIG = (540.0, 800.0, 285.0)


def sector_angle(i):
    return -90.0 + 72.0 * i


class WheelState:
    def __init__(self):
        self.alpha = 0.0
        self.big = 0.0                 # 0 = mini, 1 = big
        self.order = list(ORDER_KE)
        self.flip = None               # progress 0..1 while flipping
        self.next_order = None
        self.angle = sector_angle(3)   # pointer angle (deg), starts at 火
        self.labels = {}
        self.active = "火"
        self.arrows = []               # (from_el, to_el, text, alpha)
        self.ghost = None              # (el, alpha)
        self.question = 0.0
        self.run_slot = 0.0
        self.spin = 0.0
        self.center_text = 0.0
        self.pulse = 0.0               # flash when the pointer arrives


def _arc_path(cx, cy, r0, r1, a0, a1):
    p = skia.Path()
    outer = skia.Rect.MakeLTRB(cx - r1, cy - r1, cx + r1, cy + r1)
    inner = skia.Rect.MakeLTRB(cx - r0, cy - r0, cx + r0, cy + r0)
    p.arcTo(outer, a0, a1 - a0, True)
    p.arcTo(inner, a1, -(a1 - a0), False)
    p.close()
    return p


def draw_wheel(cv, st: WheelState, th):
    if st.alpha <= 0.01:
        return
    k = ease(st.big)
    cx = MINI[0] + (BIG[0] - MINI[0]) * k
    cy = MINI[1] + (BIG[1] - MINI[1]) * k
    r = MINI[2] + (BIG[2] - MINI[2]) * k
    A = st.alpha
    text_col = th["sub"]
    dark = th["dark"]

    cv.save()
    cv.translate(cx, cy)
    sx = 1.0
    order = st.order
    if st.flip is not None:
        p = st.flip
        sx = abs(math.cos(math.pi * p))
        if p >= 0.5 and st.next_order:
            order = st.next_order
        sx = max(sx, 0.02)
    if st.flip is not None:
        zoom = 1.0 + 0.12 * math.sin(math.pi * st.flip)
        cv.scale(zoom, zoom)
        # wheel thickness seen edge-on
        if sx < 0.35:
            k = 1 - sx / 0.35
            edge = skia.Rect.MakeLTRB(-10 * k, -r, 10 * k, r)
            cv.drawRect(edge, paint(hexc("#7A5A2E"), alpha=A * k))
            cv.drawRect(edge, paint(hexc("#E8C987"), "stroke", 2, alpha=A * k))
    cv.scale(sx, 1.0)
    if st.spin:
        cv.rotate(st.spin)

    # soft halo
    cv.drawCircle(0, 0, r * 1.06, paint((0, 0, 0, 0.55 if dark else 0.25), alpha=A, blur=r * 0.08))
    rim = hexc("#E8D9B5") if dark else hexc("#3A2C1C")
    r_in, r_out = r * 0.50, r

    for i, el in enumerate(order):
        a_c = sector_angle(i)
        a0, a1 = a_c - 34.0, a_c + 34.0
        if st.run_slot > 0 and order == ORDER_SHENG:
            if el == "木":
                a1 -= 4.5 * st.run_slot
            if el == "火":
                a0 += 4.5 * st.run_slot
        is_act = (el == st.active)
        pop = 1.0 + (0.045 + 0.03 * st.pulse) * (1 if is_act else 0)
        col = DE_COLOR[el]
        if not is_act:
            base = hexc("#2A2622") if dark else hexc("#CBBE9F")
            col = mix(col, base, 0.42)
        path = _arc_path(0, 0, r_in, r_out * pop, a0, a1)
        if is_act:
            glow = DE_COLOR[el] if el != "水" else hexc("#8FA3B8")
            cv.drawPath(path, paint(glow, alpha=A * (0.55 + 0.4 * st.pulse), blur=r * 0.07))
        cv.drawPath(path, paint(col, alpha=A))
        cv.drawPath(path, paint(rim, "stroke", max(1.2, r * 0.012), alpha=A * (0.75 if is_act else 0.35)))
        # glyph
        gr = (r_in + r_out * pop) / 2
        gx = gr * math.cos(math.radians(a_c))
        gy = gr * math.sin(math.radians(a_c))
        fs = r * (0.25 if st.big < 0.5 else 0.21)
        f = font("serif", "Black", round(fs))
        ink = DE_INK[el] if is_act else with_alpha(DE_INK[el], 0.75)
        cv.save()
        cv.translate(gx, gy)
        if st.spin:
            cv.rotate(-st.spin)
        draw_text(cv, el, 0, fs * 0.36, f, ink, "center", A)
        cv.restore()
        # ghost (dashed outline: "空着，等人来坐")
        if st.ghost and st.ghost[0] == el and st.ghost[1] > 0.01:
            gp = paint(hexc("#F3E7C9") if dark else hexc("#2A1C10"), "stroke", max(2, r * 0.02), alpha=A * st.ghost[1])
            gp.setPathEffect(skia.DashPathEffect.Make([r * 0.06, r * 0.04], 0))
            cv.drawPath(_arc_path(0, 0, r_in * 0.97, r_out * 1.09, a0 - 2, a1 + 2), gp)

    # 闰位 sliver between 木 and 火 (相生 order only)
    if st.run_slot > 0.01 and order == ORDER_SHENG:
        a_m = (sector_angle(0) + sector_angle(1)) / 2
        sp = _arc_path(0, 0, r_in * 0.92, r_out * 1.02, a_m - 3.6 * st.run_slot, a_m + 3.6 * st.run_slot)
        cv.drawPath(sp, paint(hexc("#8C8A86"), alpha=A * st.run_slot))
        cv.drawPath(sp, paint(rim, "stroke", 1.5, alpha=A * st.run_slot * 0.8))
        if st.big > 0.5:
            lr = r_out * 1.17
            lx, ly = lr * math.cos(math.radians(a_m)), lr * math.sin(math.radians(a_m))
            f = font("serif", "Black", round(r * 0.11))
            draw_text(cv, "闰 · 秦", lx, ly, f, hexc("#B9B5AE"), "center", A * st.run_slot)

    # jade bi disc in the middle
    jade = skia.Paint(AntiAlias=True)
    jade.setShader(skia.GradientShader.MakeRadial(
        skia.Point(-r_in * 0.25, -r_in * 0.3), r_in * 1.2,
        [skia.Color4f(0.62, 0.72, 0.62, A), skia.Color4f(0.30, 0.42, 0.36, A), skia.Color4f(0.17, 0.25, 0.22, A)],
        [0.0, 0.6, 1.0]))
    cv.drawCircle(0, 0, r_in * 0.93, jade)
    dot = paint((0.85, 0.9, 0.82, 0.22), alpha=A)
    for ring in (0.55, 0.75):
        n = int(14 * ring * (2 if st.big > 0.5 else 1))
        for j in range(n):
            ang = j / n * math.tau
            cv.drawCircle(r_in * ring * math.cos(ang), r_in * ring * math.sin(ang), r_in * 0.035, dot)
    cv.drawCircle(0, 0, r_in * 0.93, paint(hexc("#D9E4D2"), "stroke", max(1, r * 0.008), alpha=A * 0.5))

    # pointer
    ang = math.radians(st.angle - (st.spin or 0))
    L = r_out * 0.97
    needle = skia.Path()
    w = r * 0.045
    needle.moveTo(L, 0)
    needle.lineTo(r_in * 0.2, -w)
    needle.lineTo(-r_in * 0.42, -w * 0.6)
    needle.lineTo(-r_in * 0.5, 0)
    needle.lineTo(-r_in * 0.42, w * 0.6)
    needle.lineTo(r_in * 0.2, w)
    needle.close()
    PA = A * (1 - st.center_text)
    cv.save()
    cv.rotate(math.degrees(ang))
    cv.drawPath(needle, paint((0, 0, 0, 0.5), alpha=PA, blur=r * 0.02))
    np_ = skia.Paint(AntiAlias=True)
    np_.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(0, -w), skia.Point(0, w)],
        [skia.Color4f(0.93, 0.80, 0.55, PA), skia.Color4f(0.55, 0.40, 0.20, PA)]))
    cv.drawPath(needle, np_)
    cv.restore()
    cv.drawCircle(0, 0, r * 0.075, paint(hexc("#C9A465"), alpha=PA))
    cv.drawCircle(0, 0, r * 0.035, paint(hexc("#5A4020"), alpha=PA))

    # centre text 终始
    if st.center_text > 0.01:
        f = font("serif", "Black", round(r_in * 0.42))
        draw_text(cv, "终始", 0, r_in * 0.15, f, hexc("#F6EBD0"), "center", A * st.center_text,
                  shadow=((0, 0, 0, 0.6), r_in * 0.04, (0, 2)))

    # arrows (克 / 生) outside the ring
    for (e0, e1, txt, aa) in st.arrows:
        if aa <= 0.01 or e0 not in order or e1 not in order:
            continue
        i0, i1 = order.index(e0), order.index(e1)
        a0 = sector_angle(i0) + 10
        a1 = sector_angle(i1) - 10
        if a1 < a0:
            a1 += 360
        rr = r_out * 1.12
        ap = skia.Path()
        ap.arcTo(skia.Rect.MakeLTRB(-rr, -rr, rr, rr), a0, a1 - a0, True)
        col = hexc("#F1E2BE") if dark else hexc("#3B2A18")
        cv.drawPath(ap, paint(col, "stroke", max(2, r * 0.014), alpha=A * aa))
        # arrow head
        ae = math.radians(a1)
        hx, hy = rr * math.cos(ae), rr * math.sin(ae)
        tx, ty = -math.sin(ae), math.cos(ae)  # tangent (clockwise)
        nx, ny = math.cos(ae), math.sin(ae)
        hs = r * 0.05
        head = skia.Path()
        head.moveTo(hx + tx * hs, hy + ty * hs)
        head.lineTo(hx - tx * hs * 0.2 + nx * hs * 0.6, hy - ty * hs * 0.2 + ny * hs * 0.6)
        head.lineTo(hx - tx * hs * 0.2 - nx * hs * 0.6, hy - ty * hs * 0.2 - ny * hs * 0.6)
        head.close()
        cv.drawPath(head, paint(col, alpha=A * aa))
        if st.big > 0.5:
            am = math.radians((a0 + a1) / 2)
            lr = r_out * 1.27
            f = font("sans", "Bold", round(r * 0.095))
            draw_text(cv, txt, lr * math.cos(am), lr * math.sin(am) + r * 0.035, f,
                      hexc("#FFE6B0") if dark else CINNABAR, "center", A * aa)

    cv.restore()

    # labels (outside, not scaled by flip so they stay legible)
    if st.flip is None and st.big > 0.4 and not st.arrows_hide_labels():
        f = font("serif", "Bold", round(r * 0.085))
        la = A * clamp((st.big - 0.4) / 0.6)
        for i, el in enumerate(order):
            lab = st.labels.get(el)
            if not lab:
                continue
            a_c = math.radians(sector_angle(i) + (st.spin or 0))
            lr = r * 1.34
            lx, ly = cx + lr * math.cos(a_c), cy + lr * math.sin(a_c)
            is_act = el == st.active
            draw_text(cv, lab, lx, ly + r * 0.03, f, text_col if is_act else with_alpha(text_col, 0.6),
                      "center", la)
    # mini caption under the wheel
    if st.big < 0.5 and st.flip is None:
        lab = st.labels.get(st.active, "")
        cap = f"{lab} · {st.active}德" if lab else f"{st.active}德"
        f = font("serif", "Bold", 30)
        draw_text(cv, cap, cx, cy + r + 42, f, text_col, "center", A * (1 - st.big * 2),
                  shadow=((0, 0, 0, 0.5 if dark else 0.0), 3, (0, 1)))
    # question mark
    if st.question > 0.01:
        f = font("serif", "Black", round(r * (0.55 if st.big < 0.5 else 0.3)))
        qx = cx - r * 1.25 if st.big < 0.5 else cx + r * 0.0
        qy = cy + r * 0.2 if st.big < 0.5 else cy - r * 1.15
        draw_text(cv, "？", qx, qy, f, CINNABAR if not dark else hexc("#F0B07A"), "center", A * st.question)


def _hide(self):
    return False


WheelState.arrows_hide_labels = _hide
