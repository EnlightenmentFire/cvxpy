# -*- coding: utf-8 -*-
"""各场景绘制函数。每个函数签名 draw_xxx(c, S)，S 为状态字典：
  t   全片时间        ts  场景内时间      tb  当前 beat 内时间    bd  当前 beat 时长
  beat 当前 beat      seen 本场景已出现过的 beats（含当前）       sec_title 段落标题
"""
import math
import random

import numpy as np
import skia

from render_lib import (C, W, H, SIDE, SAFE_TOP, SUB_Y, rgb, rgba, font, paint, draw_text, draw_lines, wrap, rrect,
                        line, path_from, smooth_path, vignette, bg_night, grid_bg, quote_card, gpws_text, ease,
                        ease_out, ease_in, clamp, lerp, fade_io, plane_side, plane_top, overlay_grain, section_tag,
                        text_w)

# ════════════════════════════════════════════════════════════════════
# 801 飞行剖面数据（NTSB AAR-00/01 第 1.1 节；u=离 6L 跑道入口海里数，alt=海拔英尺）
# ════════════════════════════════════════════════════════════════════
def hms(s):
    h, m, x = [float(v) for v in s.split(":")]
    return h * 3600 + m * 60 + x


TRACK = [("01:39:40", 10.3, 2660), ("01:40:13", 9.0, 2640), ("01:40:33", 8.3, 2400), ("01:40:37", 8.05, 2360),
         ("01:40:57", 6.8, 2000), ("01:41:14", 6.2, 1800), ("01:41:22", 5.95, 1700), ("01:41:42", 5.3, 1400),
         ("01:41:59", 4.6, 1100), ("01:42:14", 4.0, 840), ("01:42:19", 3.8, 730), ("01:42:22", 3.65, 680),
         ("01:42:24", 3.5, 670), ("01:42:26", 3.3, 660)]
TRACK = [(hms(a), u, al) for a, u, al in TRACK]
T_IMPACT = hms("01:42:26")
VOR_U = 3.3      # 测距台/VOR（尼米兹山）离跑道入口
GUQQY_U = 4.9    # 外指点标（DME 1.6）
MAP_U = 0.5      # 复飞点（DME 2.8）
# 地形（示意；由报告中的离地高度与海拔推算）
TERRAIN = [(11.0, -10), (7.6, -10), (7.1, 0), (6.6, 90), (6.0, 220), (5.3, 400), (4.9, 560), (4.55, 640),
           (4.2, 590), (3.8, 535), (3.55, 590), (3.3, 665), (3.05, 710), (2.6, 640), (2.0, 480), (1.4, 360),
           (0.8, 300), (0.0, 256), (-1.6, 256)]
STAIRS = [(10.3, 2000), (GUQQY_U, 2000), (GUQQY_U, 1440), (VOR_U, 1440), (VOR_U, 560), (MAP_U, 560)]


def track_at(tsec):
    if tsec <= TRACK[0][0]:
        return TRACK[0][1], TRACK[0][2]
    for (t0, u0, a0), (t1, u1, a1) in zip(TRACK, TRACK[1:]):
        if t0 <= tsec <= t1:
            k = (tsec - t0) / (t1 - t0)
            return lerp(u0, u1, k), lerp(a0, a1, k)
    return TRACK[-1][1], TRACK[-1][2]


def terrain_at(u):
    for (u0, a0), (u1, a1) in zip(TERRAIN, TERRAIN[1:]):
        if u1 <= u <= u0:
            k = (u0 - u) / (u0 - u1)
            return lerp(a0, a1, ease(k) * 0.3 + k * 0.7)
    return 0.0


def min_alt_at(u):
    if u > GUQQY_U:
        return 2000
    if u > VOR_U:
        return 1440
    if u > MAP_U:
        return 560
    return 256


# ════════════════════════════════════════════════════════════════════
# 0 冷启动 / 片头
# ════════════════════════════════════════════════════════════════════
def draw_cold(c, S):
    c.clear(rgb("#000000"))
    show = S["beat"]["ev"].get("show", 4)
    tb = S["tb"]
    out = 1.0 - ease(tb / max(S["bd"] * 0.8, 0.1)) if show >= 5 else 1.0   # 最后只剩红字
    f_t = font(30, "mono", 700)
    f_who = font(30, "sans", 700)
    f_en = font(78, "mono", 700)
    y1, y2, y3 = 610, 860, 1090
    # 第 1 句
    if show >= 1:
        a = 1.0 if show > 1 else ease(tb / 0.5)
        k = 1.0 if show > 1 else clamp(tb / 0.9)
        a *= out
        draw_text(c, "01:41:59", SIDE + 20, y1 - 96, f_t, C["amber"], a * 0.9)
        draw_text(c, "副驾驶", SIDE + 196, y1 - 96, f_who, C["text2"], a * 0.9)
        s = "not in sight?"
        draw_text(c, s[:max(1, int(len(s) * k))] if k < 1 else s, SIDE + 20, y1, f_en, "#FFFFFF", a)
    if show >= 2:
        a = 1.0 if show > 2 else ease(tb / 0.25)
        dim = 1.0 if show != 4 else 0.85
        draw_text(c, "01:42:00", SIDE + 20, y2 - 110, f_t, C["red"], a * 0.9 * dim)
        draw_text(c, "近地警告", SIDE + 196, y2 - 110, f_who, C["red"], a * 0.8 * dim)
        gpws_text(c, "five hundred", SIDE + 20, y2, size=92, alpha=a * dim, align="left")
    if show >= 3:
        a = 1.0 if show > 3 else ease(tb / 0.4)
        dim = (1.0 if show < 4 else 0.55) * out
        draw_text(c, "01:42:02", SIDE + 20, y3 - 96, f_t, C["amber"], a * 0.9 * dim)
        draw_text(c, "飞行工程师", SIDE + 196, y3 - 96, f_who, C["text2"], a * 0.9 * dim)
        draw_text(c, "eh?", SIDE + 20, y3, f_en, "#FFFFFF", a * dim)
        draw_text(c, "[报告原注：惊讶的语气]", SIDE + 210, y3 - 4, font(30, "sans", 400), C["text3"], a * dim)
    if show >= 4:
        # 三秒的刻度
        a = (ease(S["ts_beat_group"] / 0.8) if "ts_beat_group" in S else 1.0) * out
        x0 = W - SIDE - 30
        line(c, x0, y1 - 40, x0, y3 - 20, C["text3"], a * 0.8, 2)
        for yy in (y1 - 40, y3 - 20):
            line(c, x0 - 14, yy, x0 + 14, yy, C["text3"], a * 0.8, 2)
        draw_text(c, "3 秒", x0 - 24, (y1 + y3) / 2 - 20, font(34, "sans", 700), C["text2"], a, "right")


def draw_title(c, S):
    ts = S["tb"]
    bg_night(c, glow=0.5)
    rain_streaks(c, S["t"], 70, alpha=0.35)
    a = fade_io(ts, S["bd"], 0.8, 0.6)
    draw_text(c, "组织里的权力", W / 2, 700, font(40, "sans", 700), C["amber"], a, "center")
    line(c, W / 2 - 150, 735, W / 2 + 150, 735, C["amber"], a * 0.6, 2)
    f = font(112, "sans", 900)
    draw_text(c, "不敢说的", W / 2, 900, f, C["text"], a, "center", glow="#FFFFFF", glow_alpha=0.12)
    draw_text(c, "那句话", W / 2, 1040, f, C["text"], a, "center", glow="#FFFFFF", glow_alpha=0.12)
    draw_text(c, "大韩航空 801 号班机 · 1997 年 8 月 6 日 · 关岛", W / 2, 1150, font(32, "sans", 400), C["text2"], a,
              "center")
    draw_text(c, "本片配音为 AI 合成 · 黑匣子原话依据 NTSB 调查报告", W / 2, 1430, font(24, "sans", 400), C["text3"],
              a * 0.9, "center")
    vignette(c, 0.7)


# ════════════════════════════════════════════════════════════════════
# 雨 / 夜空
# ════════════════════════════════════════════════════════════════════
_RAIN = None


def _rain_seed(n):
    global _RAIN
    if _RAIN is None or len(_RAIN) < n:
        rng = random.Random(801)
        _RAIN = [(rng.random(), rng.random(), 0.5 + rng.random(), rng.random()) for _ in range(400)]
    return _RAIN[:n]


def rain_streaks(c, t, n=80, alpha=0.4, y0=0, y1=H, angle=0.18):
    p = paint("#9FB6D6", alpha * 0.55, stroke=1.6, cap="round")
    span = y1 - y0
    for (rx, ry, sp, ph) in _rain_seed(n):
        L = 30 + 50 * sp
        y = y0 + ((ry * span + t * 900 * sp) % (span + L)) - L
        x = rx * (W + 200) - 100 + (y - y0) * angle
        c.drawLine(x, y, x + L * angle, y + L, p)


def windshield_drops(c, t, rect, n=46, alpha=0.8, wiper_t=None):
    x0, y0, w, h = rect
    rng = random.Random(7)
    for i in range(n):
        bx, by = rng.random(), rng.random()
        born = rng.random() * 6
        life = (t - born) % 6.0
        if wiper_t is not None:
            pass
        r = 2 + rng.random() * 5
        a = alpha * clamp(life / 0.4) * 0.7
        cx, cy = x0 + bx * w, y0 + by * h + life * 6
        c.drawCircle(cx, cy, r, paint("#BFD3EE", a * 0.35))
        c.drawCircle(cx - r * 0.3, cy - r * 0.3, r * 0.35, paint("#FFFFFF", a * 0.5))


# ════════════════════════════════════════════════════════════════════
# 1 那一夜：夜航 + 驾驶舱（背后视角剪影）
# ════════════════════════════════════════════════════════════════════
def draw_night(c, S):
    t, ts = S["t"], S["ts"]
    bg_night(c)
    # 远处城市灯（首尔金浦）→ 黑夜云层
    k = clamp(ts / 12)
    for i in range(70):
        rng = random.Random(i)
        x = rng.random() * W
        y = 1180 + rng.random() * 120
        tw = 0.5 + 0.5 * math.sin(t * 2 + i)
        c.drawCircle(x, y + ts * 6, 1.6 + rng.random() * 1.8, paint(C["amber"], (1 - k) * 0.5 * tw))
    # 云层
    for j in range(5):
        y = 520 + j * 140
        shader = skia.GradientShader.MakeLinear([skia.Point(0, y), skia.Point(0, y + 160)],
                                                [rgba("#1A2740", 0.0), rgba("#1A2740", 0.35), rgba("#1A2740", 0.0)],
                                                [0, 0.5, 1])
        c.save()
        c.translate(-((t * (12 + j * 5)) % 400), 0)
        c.drawRect(skia.Rect.MakeXYWH(0, y, W + 400, 160), skia.Paint(Shader=shader))
        c.restore()
    # 747 剪影穿过
    px = lerp(-120, W + 140, clamp(ts / 16))
    plane_side(c, px, 780 - ts * 4, 2.2, "#C9D6EA", 0.85, pitch=-2)
    c.drawCircle(px - 98, 780 - ts * 4 - 30, 3, paint(C["red"], 0.9 * (0.5 + 0.5 * math.sin(t * 6))))
    rain_streaks(c, t, 60, 0.25)
    draw_text(c, "首尔金浦 → 关岛", W / 2, 470, font(36, "sans", 700), C["text2"], ease(ts / 1.2), "center")
    draw_text(c, "KE801 · B747-300 · 254 人", W / 2, 525, font(30, "mono", 700), C["amber"], ease(ts / 1.6), "center")
    vignette(c, 0.7)



def seat_silhouette(c, cx, head_y, s, body_col, alpha=1.0, rim=0.0, turn=0.0):
    """背后视角：座椅 + 头肩剪影。head_y 为头部中心。rim>0 时加琥珀色轮廓光。"""
    c.save()
    c.translate(cx, head_y)
    c.scale(s, s)
    # 座椅靠背
    rrect(c, -105, 40, 210, 330, 40, "#0B1220", alpha)
    rrect(c, -105, 40, 210, 330, 40, "#22314C", alpha * 0.9, stroke=2)
    # 肩膀 + 躯干
    sh = smooth_path([(-130, 190), (-112, 108), (-62, 70), (62, 70), (112, 108), (130, 190)])
    sh.lineTo(130, 260)
    sh.lineTo(-130, 260)
    sh.close()
    c.drawPath(sh, paint(body_col, alpha))
    # 头
    c.save()
    c.translate(turn * 8, 0)
    c.drawOval(skia.Rect.MakeXYWH(-46, -54, 92, 112), paint(body_col, alpha))
    c.drawArc(skia.Rect.MakeXYWH(-54, -64, 108, 104), 195, 150, False, paint("#33435F", alpha, stroke=8))  # 耳机
    c.restore()
    if rim > 0:
        c.drawOval(skia.Rect.MakeXYWH(-46, -54, 92, 112), paint(C["amber"], rim * 0.9, stroke=3))
        c.drawPath(smooth_path([(-130, 190), (-112, 108), (-62, 70), (62, 70), (112, 108), (130, 190)]),
                   paint(C["amber"], rim * 0.8, stroke=3))
    c.restore()


def label_pill(c, x, y, name, age, alpha=1.0, align="center"):
    f1, f2 = font(36, "sans", 900), font(30, "sans", 700)
    w = f1.measureText(name) + f2.measureText(age) + 64
    x0 = x - w / 2 if align == "center" else x
    rrect(c, x0, y - 44, w, 62, 31, "#050A14", 0.85 * alpha)
    rrect(c, x0, y - 44, w, 62, 31, C["amber"], 0.55 * alpha, stroke=2)
    wn = draw_text(c, name, x0 + 24, y, f1, C["text"], alpha)
    draw_text(c, age, x0 + 24 + wn + 16, y, f2, C["amber"], alpha)


def draw_cockpit(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    ev = S["beat"]["ev"]
    hi = ev.get("hi")
    c.clear(rgb("#03060C"))
    # 风挡：夜 + 雨
    ws = path_from([(96, 340), (984, 340), (948, 700), (132, 700)], True)
    c.save()
    c.clipPath(ws, doAntiAlias=True)
    shader = skia.GradientShader.MakeLinear([skia.Point(0, 340), skia.Point(0, 700)],
                                            [rgb("#0A1630"), rgb("#0F1D38"), rgb("#16223A")], [0, 0.6, 1])
    c.drawRect(skia.Rect.MakeXYWH(0, 340, W, 360), skia.Paint(Shader=shader))
    rain_streaks(c, t, 80, 0.5, 340, 700, angle=0.05)
    windshield_drops(c, t, (120, 350, 840, 340), 55, 0.9)
    c.restore()
    c.drawPath(ws, paint("#18233A", 1, stroke=16))
    line(c, 540, 340, 540, 700, "#18233A", 1, 20, cap="butt")
    # 遮光板 + 仪表板
    gl = smooth_path([(40, 712), (300, 690), (780, 690), (1040, 712)])
    gl.lineTo(1040, 760)
    gl.lineTo(40, 760)
    gl.close()
    c.drawPath(gl, paint("#0A101C", 1))
    rrect(c, 40, 748, 1000, 150, 8, "#08101C", 1)
    rng = random.Random(3)
    for i in range(30):
        x = 70 + (i % 15) * 64
        y = 768 + (i // 15) * 62
        col = [C["amber"], C["green"], C["cyan2"]][rng.randrange(3)]
        a = 0.35 + 0.2 * math.sin(t * 0.6 + i)
        c.drawCircle(x + 22, y + 22, 17, paint(col, 0.06 + 0.04 * a, blur=6))
        c.drawCircle(x + 22, y + 22, 15, paint(col, 0.32 + 0.12 * a, stroke=2))
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, 820), 600,
                                        [rgba(C["amber"], 0.12), rgba(C["amber"], 0.0)], [0, 1])
    c.drawRect(skia.Rect.MakeXYWH(0, 600, W, 700), skia.Paint(Shader=sh))
    # 飞行工程师的侧面面板（右侧）
    rrect(c, 985, 720, 120, 560, 10, "#08101C", 1)
    for i in range(16):
        x = 1000 + (i % 2) * 42
        y = 745 + (i // 2) * 64
        c.drawCircle(x + 14, y + 14, 12, paint(C["amber"] if i % 3 else C["green"], 0.35, stroke=2))
    # 三个人（机长左、副驾驶右、工程师在后侧，面向右侧面板）
    dim = lambda k: 1.0 if hi in (None, k) else 0.55
    seat_silhouette(c, 330, 800, 1.0, "#1A2640", 1.0, rim=(0.9 if hi == "cap" else 0))
    seat_silhouette(c, 750, 800, 1.0, "#1A2640", 1.0, rim=(0.9 if hi == "fo" else 0))
    seat_silhouette(c, 860, 990, 1.12, "#1E2B47", 1.0, rim=(0.9 if hi == "fe" else 0), turn=1.0)
    if hi in ("cap", "fo", "fe"):
        cx, cy = {"cap": (330, 800), "fo": (750, 800), "fe": (860, 990)}[hi]
        g = skia.GradientShader.MakeRadial(skia.Point(cx, cy), 300,
                                           [rgba(C["amber"], 0.16), rgba(C["amber"], 0.0)], [0, 1])
        c.drawRect(skia.Rect.MakeXYWH(cx - 320, cy - 320, 640, 640), skia.Paint(Shader=g))
    # 标签
    label_pill(c, 330, 676, "机长", "42 岁", dim("cap"))
    label_pill(c, 750, 676, "副驾驶", "40 岁", dim("fo"))
    label_pill(c, 520, 1010, "飞行工程师", "57 岁", dim("fe"))
    line(c, 662, 990, 790, 990, C["amber"], 0.5 * dim("fe"), 2)
    # 年纪 vs 地位
    if ev.get("rank"):
        a = ease(tb / 0.8)
        bx, by, bw, bh = 150, 352, 780, 236
        rrect(c, bx, by, bw, bh, 16, "#03070F", a * 0.92)
        rrect(c, bx, by, bw, bh, 16, C["steel"], a, stroke=2)
        draw_text(c, "年纪", bx + 250, by + 50, font(28, "sans", 700), C["text2"], a, "center")
        draw_text(c, "驾驶舱里的地位", bx + 610, by + 50, font(28, "sans", 700), C["text2"], a, "center")
        rows = [("机械师", 57, 1), ("机长", 42, 3), ("副驾驶", 40, 2)]
        for i, (n, age, rank) in enumerate(rows):
            y = by + 100 + i * 48
            col = C["amber"] if n == "机械师" else C["text"]
            draw_text(c, n, bx + 30, y, font(30, "sans", 900), col, a)
            rrect(c, bx + 150, y - 24, age * 3.2 * ease(tb / 1.0), 26, 5, C["amber"], a * 0.9)
            draw_text(c, str(age), bx + 160 + age * 3.2, y, font(26, "mono", 700), C["amber"], a)
            for r in range(3):
                rrect(c, bx + 520 + r * 62, y - 24, 52, 26, 5, C["cyan"] if r < rank else "#1C2A44", a)
    vignette(c, 0.55)


# ════════════════════════════════════════════════════════════════════
# 2 关岛的陷阱：俯视地图（进近航向竖直向上）
# ════════════════════════════════════════════════════════════════════

MAP_X = 560                # 6L 航向线附近的 x
MAP_Y0 = 520               # 跑道入口 y（u=0）
MAP_S = 118                # 像素/海里
MAP_CLIP = (0, 330, W, 940)


def mxy(u, v):
    """u=离跑道入口海里（沿进近航向，向下为正），v=横向海里（右为正）。"""
    return MAP_X + v * MAP_S, MAP_Y0 + u * MAP_S


LAND = [(-2.5, 5.6), (-2.5, -4.8), (-0.6, -3.6), (0.9, -3.1), (2.3, -2.9), (3.6, -2.4), (4.7, -1.8),
        (5.5, -1.0), (6.05, 0.0), (6.3, 1.4), (6.6, 2.9), (7.0, 4.4), (7.4, 5.6)]


def bracket(c, x, ya, yb, col, a, w=4, tick=14):
    line(c, x, ya, x, yb, col, a, w)
    for yy in (ya, yb):
        line(c, x - tick, yy, x + tick, yy, col, a, w)


def draw_map(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    stage = S["beat"]["ev"].get("stage", "island")
    order = ["island", "ils", "gs_off", "steps", "dme", "two_lines", "rain", "layers"]
    si = order.index(stage) if stage in order else 0
    tst = S.get("ts_stage", {})
    c.clear(rgb("#03060C"))
    x0, y0, w0, h0 = MAP_CLIP
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x0, y0, w0, h0))
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w0, h0), paint("#081A33", 1))       # 海
    grid_bg(c, 0.22, 59, y0, y0 + h0)
    land = smooth_path([mxy(u, v) for u, v in LAND], close=True)
    c.drawPath(land, paint("#14202F", 1))
    c.drawPath(land, paint("#30486B", 1, stroke=3))
    # 尼米兹山（等高线）
    hx, hy = mxy(VOR_U, 0.3)
    for i, r in enumerate([170, 125, 84, 46]):
        c.drawOval(skia.Rect.MakeXYWH(hx - r * 1.3, hy - r * 0.95, r * 2.6, r * 1.9), paint("#7A5F3E", 0.4 + i * 0.12, stroke=2))
    c.drawOval(skia.Rect.MakeXYWH(hx - 50, hy - 36, 100, 72), paint("#4A3A27", 0.8))
    draw_text(c, "尼米兹山", hx + 150, hy + 96, font(36, "sans", 900), "#E2C08F", 1)
    # 跑道 6L / 6R
    for dv in (-0.24, 0.24):
        xa, ya = mxy(0, dv)
        xb, yb = mxy(-1.7, dv)
        line(c, xa, ya, xb, yb, "#C8D2E0", 1, 18, cap="butt")
        line(c, xa, ya, xb, yb, "#0B1220", 1, 2, dash=[16, 14], cap="butt")
    rx, ry = mxy(0.0, 0.24)
    draw_text(c, "跑道 6L", rx + 40, ry - 40, font(36, "sans", 900), C["text"], 1)
    draw_text(c, "关岛机场", rx + 40, ry - 84, font(28, "sans", 700), C["text2"], 1)
    ax, ay = mxy(0, -0.24)
    bx_, by_ = mxy(8.0, -0.24)
    # ILS 航向道
    if si >= 1:
        a = ease(tst.get("ils", 9) / 0.8)
        wedge = path_from([mxy(0, -0.24), mxy(8.0, -0.9), mxy(8.0, 0.42)], True)
        c.drawPath(wedge, paint(C["green"], 0.10 * a))
        line(c, ax, ay, bx_, by_, C["green"], 0.85 * a, 3, dash=[18, 12])
        draw_text(c, "航向道：管左右", ax - 40, y0 + h0 - 30, font(30, "sans", 900), C["green"], a, "right")
    # 测距台
    vx, vy = mxy(VOR_U, -0.24)
    if si >= 4:
        for i in range(3):
            ph = ((t * 0.8 + i / 3) % 1.0)
            c.drawCircle(vx, vy, 18 + ph * 80, paint(C["cyan"], (1 - ph) * 0.55, stroke=3))
        c.drawCircle(vx, vy, 13, paint(C["cyan"], 1))
        draw_text(c, "测距台 DME", vx - 34, vy - 30, font(34, "sans", 900), C["cyan"], 1, "right")
        if si == 4:
            draw_text(c, "（在山上，不在机场）", vx - 34, vy + 12, font(26, "sans", 700), C["cyan"], 0.9, "right")
    if si == 4:
        a = ease(tst.get("dme", 9) / 0.8)
        xb = mxy(0, 1.35)[0]
        bracket(c, xb, mxy(0, 0)[1], vy, C["text"], a)
        draw_text(c, "3.3 海里", xb + 26, (vy + mxy(0, 0)[1]) / 2 + 14, font(36, "sans", 900), C["text"], a)
    # 两条距离线
    if si >= 5:
        k = ease(tst.get("two_lines", 9) / 1.0)
        pu = VOR_U + 1.0
        px, py = mxy(pu, -0.24)
        plane_top(c, px, py, 1.3, "#FFFFFF", 1, 0)
        xa = mxy(0, -1.05)[0]
        bracket(c, xa, vy, py, C["cyan"], k)
        draw_text(c, "仪表显示：1.0 海里", xa - 26, (vy + py) / 2 - 6, font(32, "sans", 900), C["cyan"], k, "right")
        draw_text(c, "= 离山上的测距台", xa - 26, (vy + py) / 2 + 36, font(28, "sans", 700), C["cyan"], k, "right")
        xb = mxy(0, 3.05)[0]
        thy = mxy(0, 0)[1]
        bracket(c, xb, thy, py, C["text"], k)
        draw_text(c, "离跑道", xb - 24, (thy + py) / 2 - 18, font(30, "sans", 700), C["text"], k, "right")
        draw_text(c, "4.3 海里", xb - 24, (thy + py) / 2 + 26, font(38, "sans", 900), C["text"], k, "right")
        k2 = ease((tst.get("two_lines", 9) - 2.0) / 1.0)
        gx, gy = mxy(VOR_U, -0.24)
        glen = 1.4 * MAP_S
        rrect(c, gx - 13, gy - glen, 26, glen, 4, C["red"], 0.22 * k2)
        rrect(c, gx - 13, gy - glen, 26, glen, 4, C["red"], k2, stroke=3)
        tx = gx - 40
        draw_text(c, "当成“离跑道 1 海里”：", tx, gy - glen + 10, font(28, "sans", 700), C["red"], k2, "right")
        draw_text(c, "以为跑道在这儿", tx, gy - glen + 54, font(36, "sans", 900), C["red"], k2, "right")
        draw_text(c, "——其实是山", tx, gy - glen + 96, font(30, "sans", 900), C["red"], k2, "right")
    if si >= 6:
        rain_streaks(c, t, 110, 0.5, y0, y0 + h0)
    c.restore()
    rrect(c, x0 + 2, y0, w0 - 4, h0, 0, C["steel"], 0.8, stroke=2)
    draw_text(c, "关岛 · 示意图，非比例", W - 40, y0 + 140, font(22, "sans", 400), C["text3"], 1, "right")
    # 罗盘
    cx_, cy_ = W - 110, y0 + 70
    c.drawCircle(cx_, cy_, 32, paint("#03060C", 0.7))
    c.drawCircle(cx_, cy_, 32, paint(C["text3"], 0.9, stroke=2))
    c.save()
    c.translate(cx_, cy_)
    c.rotate(-63)
    c.drawPath(path_from([(0, -28), (8, 4), (-8, 4)], True), paint(C["text2"], 0.95))
    draw_text(c, "N", 0, -36, font(22, "sans", 700), C["text2"], 0.95, "center")
    c.restore()
    # 侧视小窗：下滑道 / 台阶
    if 1 <= si <= 3:
        ix, iy, iw, ih = SIDE, y0 + 20, 430, 230
        rrect(c, ix, iy, iw, ih, 14, "#03070F", 0.94)
        rrect(c, ix, iy, iw, ih, 14, C["steel"], 1, stroke=2)
        draw_text(c, "从侧面看", ix + 20, iy + 40, font(26, "sans", 700), C["text2"], 1)
        gx0, gy0, gx1, gy1 = ix + 30, iy + ih - 28, ix + iw - 28, iy + 70
        line(c, gx0 - 6, gy0, gx1 + 6, gy0, "#3A4C6B", 1, 3)
        rrect(c, gx1 - 64, gy0 - 5, 70, 8, 3, "#C8D2E0", 1)
        if si < 3:
            col = C["amber"] if si == 1 else C["text3"]
            line(c, gx0, gy1, gx1 - 34, gy0 - 4, col, 1, 4, dash=None if si == 1 else [10, 10])
            draw_text(c, "下滑道：管高低", gx0 + 150, gy1 + 10, font(28, "sans", 900), col, 1)
            if si == 2:
                k = ease(tst.get("gs_off", 9) / 0.6)
                line(c, gx0 + 110, gy1 + 30, gx0 + 230, gy0 - 30, C["red"], k, 7)
                line(c, gx0 + 230, gy1 + 30, gx0 + 110, gy0 - 30, C["red"], k, 7)
                draw_text(c, "停用", gx0 + 250, gy0 - 40, font(44, "sans", 900), C["red"], k)
        else:
            steps = [(0.0, 0.0), (0.24, 0.0), (0.24, 0.32), (0.52, 0.32), (0.52, 0.64), (0.8, 0.64), (0.8, 0.92)]
            pts = [(lerp(gx0, gx1 - 40, a_), lerp(gy1, gy0 - 8, b_)) for a_, b_ in steps]
            c.drawPath(path_from(pts), paint(C["amber"], 1, stroke=4))
            draw_text(c, "非精密进近：下台阶", gx0 + 120, gy1 + 6, font(28, "sans", 900), C["amber"], 1)
    if si >= 7:
        a = ease(tb / 0.8)
        items = ["累了的机长", "坏了的滑梯", "不在机场的信标", "看不透的雨"]
        ix, iy = SIDE, y0 + 20
        rrect(c, ix, iy, 430, 330, 14, "#03070F", 0.94 * a)
        draw_text(c, "保险，一层层变薄", ix + 20, iy + 44, font(28, "sans", 900), C["amber"], a)
        for i, s in enumerate(items):
            y = iy + 76 + i * 62
            wbar = 390 * (1 - 0.2 * (i + 1) * ease((tb - 0.3 * i) / 0.8))
            rrect(c, ix + 20, y, 390, 48, 8, "#0E1729", a)
            rrect(c, ix + 20, y, wbar, 48, 8, C["amber"], a * 0.25)
            draw_text(c, s, ix + 36, y + 35, font(28, "sans", 700), C["text"], a)


# ════════════════════════════════════════════════════════════════════
# 3 最后的二十分钟：时间轴 + 侧视剖面
# ════════════════════════════════════════════════════════════════════
def draw_timeline(c, S):
    t, ts = S["t"], S["ts"]
    at = S["beat"]["ev"].get("at", 0)
    bg_night(c)
    grid_bg(c, 0.18, 60, 330, 1300)
    # 竖直时间轴：01:21 → 01:42:26
    x = 250
    y0, y1 = 400, 1230
    T0, T1 = hms("01:21:00"), T_IMPACT

    def ty(tt):
        return y0 + (tt - T0) / (T1 - T0) * (y1 - y0)
    line(c, x, y0, x, y1, C["text3"], 1, 4)
    for m in range(21, 43, 3):
        yy = ty(hms(f"01:{m:02d}:00"))
        line(c, x - 14, yy, x, yy, C["text3"], 1, 2)
        draw_text(c, f"01:{m:02d}", x - 26, yy + 10, font(26, "mono", 700), C["text3"], 1, "right")
    # 最后两分钟（红）
    yr = ty(hms("01:40:37"))
    rrect(c, x - 10, yr, 20, y1 - yr, 6, C["red"], 0.9)
    draw_text(c, "机长报出错误高度 → 撞山：不到 2 分钟", x + 40, y1 + 8, font(28, "sans", 700), C["red"], 0.95)
    # 已出现的话
    pts = [("01:21:59", "关岛天气不好", 1), ("01:24:02", "你不觉得雨更大吗？", 2)]
    for tt, s, idx in pts:
        if at >= idx:
            yy = ty(hms(tt))
            a = 1.0
            c.drawCircle(x, yy, 12, paint(C["amber"], a))
            line(c, x + 14, yy, x + 70, yy, C["amber"], a, 2)
            draw_text(c, s, x + 84, yy + 12, font(34, "sans", 700), C["text"], a)
    # 当前卡片
    q = S["beat"].get("q")
    if q:
        a = fade_io(S["tb"], S["bd"], 0.35, 0.3)
        quote_card(c, q, x + 60, ty(hms(q["t"])) + 50, W - x - 60 - SIDE, a, t_type=clamp(S["tb"] / 1.2))
    if at == 0:
        a = ease(S["tb"] / 0.8)
        draw_text(c, "20 分钟", x + 80, (y0 + yr) / 2, font(64, "sans", 900), C["text2"], a)
    vignette(c, 0.55)


# 剖面坐标
PX0, PX1 = 70, 1010          # u=10.6 → u=-0.6
PU0, PU1 = 10.6, -0.6
PY_BASE = 1108               # 海平面
PY_SCALE = 0.182             # 像素/英尺
# 假如 01:42:14 复飞（NTSB：可越过地形约 450 英尺）——示意航迹
GHOST = [(4.0, 840), (3.88, 815), (3.72, 860), (3.52, 975), (3.3, 1120), (3.0, 1320), (2.5, 1630), (1.9, 1980),
         (1.3, 2320)]


def pxy(u, alt):
    return PX0 + (PU0 - u) / (PU0 - PU1) * (PX1 - PX0), PY_BASE - alt * PY_SCALE


def draw_profile(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    ev = S["beat"]["ev"]
    tclock = S.get("tclock", hms(ev.get("t", "01:39:44")))
    bg_night(c)
    # 网格
    for alt in range(0, 2501, 500):
        y = pxy(PU0, alt)[1]
        line(c, PX0, y, PX1, y, C["grid"], 0.9, 1)
        draw_text(c, f"{alt}", PX0 + 6, y - 8, font(22, "mono", 400), C["text3"], 0.9)
    draw_text(c, "海拔（英尺）", PX0 + 6, pxy(0, 2800)[1], font(24, "sans", 400), C["text3"], 0.9)
    # 地形
    terr = [pxy(u, max(a, 0)) for u, a in TERRAIN]
    tp = smooth_path(terr)
    tp.lineTo(PX1 + 60, PY_BASE + 14)
    tp.lineTo(PX0 - 60, PY_BASE + 14)
    tp.close()
    c.drawPath(tp, paint("#1E1913", 1))
    c.drawPath(smooth_path(terr), paint("#7A6040", 1, stroke=3))
    sx = pxy(7.1, 0)[0]
    rrect(c, PX0 - 60, PY_BASE - 3, sx - PX0 + 60, 8, 2, "#24477A", 0.95)
    draw_text(c, "海", PX0 + 60, PY_BASE - 16, font(24, "sans", 700), "#4F79B0", 0.9)
    for u in range(0, 11):
        x = pxy(u, 0)[0]
        line(c, x, PY_BASE + 16, x, PY_BASE + 26, C["text3"], 0.8, 2)
        if u % 2 == 0:
            draw_text(c, f"{u}", x, PY_BASE + 52, font(22, "mono", 400), C["text3"], 0.9, "center")
    draw_text(c, "离跑道（海里）", PX1, PY_BASE + 52, font(22, "sans", 400), C["text3"], 0.9, "right")
    # 山、测距台、跑道
    hx, hy = pxy(3.05, 330)
    draw_text(c, "尼米兹山", hx, hy, font(30, "sans", 900), "#E2C08F", 0.95, "center")
    vx, vy = pxy(VOR_U, 685)
    c.drawCircle(vx, vy, 7, paint(C["cyan"], 0.95))
    draw_text(c, "测距台", vx, vy + 40, font(22, "sans", 700), C["cyan"], 0.85, "center")
    rx, ry = pxy(0, 256)
    rrect(c, rx - 4, ry - 4, pxy(-0.6, 0)[0] - rx + 4, 8, 2, "#C8D2E0", 1)
    draw_text(c, "跑道", rx - 6, ry - 18, font(26, "sans", 700), C["text"], 0.95)
    # 程序规定的最低高度（台阶）
    pst = paint(C["amber"], 0.85, stroke=3)
    pst.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
    c.drawPath(path_from([pxy(u, a) for u, a in STAIRS]), pst)
    lx, ly = pxy(9.55, 2000)
    draw_text(c, "程序规定的最低高度", lx, ly + 34, font(24, "sans", 700), C["amber"], 0.95)
    if ev.get("show_fix") or tclock > hms("01:40:39"):
        fx, fy = pxy(GUQQY_U, 1440)
        line(c, fx, fy - 130, fx, PY_BASE, C["amber"], 0.45, 2, dash=[6, 8])
        draw_text(c, "外指点标", fx, fy - 140, font(24, "sans", 700), C["amber"], 0.95, "center")
        draw_text(c, "1440", pxy(4.1, 1440)[0], pxy(4.1, 1440)[1] - 12, font(24, "mono", 700), C["amber"], 0.95,
                  "center")
    # 实际航迹：低于规定高度的部分标红
    n = 180
    pts, reds = [], []
    for i in range(n + 1):
        tt = lerp(TRACK[0][0], tclock, i / n)
        u, a = track_at(tt)
        pts.append(pxy(u, a))
        reds.append(a < min_alt_at(u) - 5)
    c.drawPath(path_from(pts), paint(C["cyan"], 0.22, stroke=10, blur=6))
    for i in range(n):
        line(c, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], C["red"] if reds[i] else C["cyan"], 1, 4)
    if any(reds) and tclock > hms("01:41:20"):
        u, a = track_at(hms("01:41:20"))
        x, y = pxy(u, a)
        draw_text(c, "低于规定高度", x + 22, y + 4, font(24, "sans", 900), C["red"], 0.95)
    # 假如 01:42:14 复飞
    if ev.get("ghost") or S.get("ghost"):
        k = ease(tb / 1.8) if ev.get("ghost") else 1.0
        gp = [pxy(u, a) for u, a in GHOST]
        m = max(2, int(round(len(gp) * k)))
        pg = paint(C["green"], 0.95, stroke=4)
        pg.setPathEffect(skia.DashPathEffect.Make([12, 10], 0))
        c.drawPath(smooth_path(gp[:m]), pg)
        if k > 0.55:
            a2 = ease((k - 0.55) / 0.45)
            gx, gy = pxy(VOR_U, 1120)
            hx2, hy2 = pxy(VOR_U, 700)
            line(c, gx, gy + 8, hx2, hy2 - 10, C["green"], a2 * 0.8, 2, dash=[4, 6])
            tx, ty2 = pxy(2.35, 1080)
            draw_text(c, "如果这一秒复飞：", tx, ty2, font(28, "sans", 700), C["green"], a2)
            draw_text(c, "比山高出约 450 英尺", tx, ty2 + 42, font(32, "sans", 900), C["green"], a2)
    # 话语标记
    for (mt, lab, col) in S.get("marks", []):
        if hms(mt) <= tclock + 0.01:
            u, a = track_at(hms(mt))
            x, y = pxy(u, a)
            c.drawCircle(x, y, 6, paint(col, 1))
            c.drawCircle(x, y, 10, paint(col, 0.55, stroke=2))
    # 飞机
    u, a = track_at(tclock)
    x, y = pxy(u, a)
    if tclock < T_IMPACT - 0.05:
        plane_side(c, x, y, 0.72, "#FFFFFF", 1, pitch=3)
    gap = a - terrain_at(u)
    if ev.get("show_gap"):
        k = ease(tb / 0.8)
        tx, ty_ = pxy(u, terrain_at(u))
        line(c, x, y + 10, tx, ty_, C["red"], k, 3)
        for yy in (y + 10, ty_):
            line(c, x - 10, yy, x + 10, yy, C["red"], k, 3)
        draw_text(c, "离地 500", x - 18, (y + ty_) / 2 + 10, font(28, "sans", 900), C["red"], k, "right")
    # 读数条
    bx, by = SIDE, 1176
    rrect(c, bx, by, W - 2 * SIDE, 108, 14, "#050B16", 0.92)
    hh, mm, ss = int(tclock // 3600), int(tclock % 3600 // 60), int(tclock % 60)
    draw_text(c, "关岛当地时间", bx + 24, by + 34, font(22, "sans", 400), C["text3"], 1)
    draw_text(c, f"{hh:02d}:{mm:02d}:{ss:02d}", bx + 24, by + 88, font(48, "mono", 700), C["text"], 1)
    draw_text(c, "海拔", bx + 380, by + 34, font(22, "sans", 400), C["text3"], 1)
    draw_text(c, f"{int(round(a, -1)):>4d}", bx + 380, by + 88, font(48, "mono", 700), C["cyan"], 1)
    draw_text(c, "英尺", bx + 520, by + 88, font(22, "sans", 400), C["text3"], 1)
    draw_text(c, "离地", bx + 640, by + 34, font(22, "sans", 400), C["text3"], 1)
    gcol = C["red"] if gap < 800 else C["text"]
    draw_text(c, f"{max(0, int(round(gap, -1))):>4d}", bx + 640, by + 88, font(48, "mono", 700), gcol, 1)
    draw_text(c, "英尺", bx + 780, by + 88, font(22, "sans", 400), C["text3"], 1)
    # 近地警告
    g = S["beat"].get("gpws")
    if g:
        k = fade_io(tb, max(S["bd"], 0.8), 0.05, 0.25)
        draw_text(c, "近地警告 GPWS", W / 2, 452, font(26, "sans", 700), C["red"], k * 0.9, "center")
        gpws_text(c, g.replace(".", ""), W / 2, 535, size=60 if len(g) < 16 else 42, alpha=k)
    q = S["beat"].get("q")
    if q:
        a = fade_io(tb, S["bd"], 0.3, 0.25)
        accent = C["red"] if q["t"] >= "01:42:19" else (C["cyan"] if q["who"] == "管制员" else C["amber"])
        quote_card(c, q, SIDE, 334, W - 2 * SIDE, a, accent=accent, t_type=clamp(tb / 1.0))
    if ev.get("silence"):
        k = fade_io(tb, S["bd"], 0.3, 0.3)
        draw_text(c, "（没有人回答）", W / 2, 480, font(44, "sans", 900), C["text2"], k, "center")
    vignette(c, 0.5)


def draw_impact(c, S):
    tb = S["tb"]
    c.clear(rgb("#000000"))
    if tb < 0.14:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(C["red"], 0.32 * (1 - tb / 0.14)))


def draw_memorial(c, S):
    ts = S["ts"]
    c.clear(rgb("#000000"))
    a = ease(ts / 1.5)
    draw_text(c, "1997.8.6  01:42:26", W / 2, 760, font(40, "mono", 700), C["text3"], a, "center")
    draw_text(c, "机上 254 人", W / 2, 880, font(56, "sans", 700), C["text2"], a, "center")
    draw_text(c, "228 人遇难", W / 2, 970, font(64, "sans", 900), C["text"], a, "center")


# ════════════════════════════════════════════════════════════════════
# 4 报告 / 瑞士奶酪
# ════════════════════════════════════════════════════════════════════
def draw_report(c, S):
    tb, ts = S["tb"], S["ts"]
    hl = S["beat"]["ev"].get("hl")
    bg_night(c)
    x, y, w = SIDE + 10, 340, W - 2 * SIDE - 20
    rrect(c, x, y, w, 900, 12, "#0D1626", 1)
    rrect(c, x, y, w, 900, 12, "#2B3E60", 1, stroke=2)
    draw_text(c, "调查报告摘要（中译）", x + 36, y + 66, font(36, "sans", 900), C["text"], 1)
    draw_text(c, "NTSB/AAR-00/01 · 2000 年 1 月", x + 36, y + 112, font(26, "mono", 400), C["text3"], 1)
    line(c, x + 36, y + 140, x + w - 36, y + 140, C["steel"], 1, 2)
    blocks = [
        ("cause", "可能原因", ["机长没有把这次非精密进近", "交代好、飞好；", "副驾驶和飞行工程师没能有效", "监控、核对机长的操作。"]),
        ("contrib", "促成因素", ["机长疲劳；", "大韩航空机组训练不足；"]),
        ("msaw", "促成因素（地面）", ["美国联邦航空局故意关闭关岛的", "最低安全高度警告（MSAW），", "且管理不善。"]),
    ]
    yy = y + 200
    order = ["cause", "contrib", "msaw", "none"]
    cur = order.index(hl) if hl in order else 0
    for i, (key, head, lines) in enumerate(blocks):
        on = (key == hl)
        a = 1.0 if i <= cur else 0.25
        if on:
            rrect(c, x + 20, yy - 46, w - 40, 60 + 52 * len(lines), 10, C["amber"], 0.10)
            line(c, x + 22, yy - 36, x + 22, yy + 4 + 52 * len(lines), C["amber"], 1, 5)
        draw_text(c, head, x + 44, yy, font(30, "sans", 900), C["amber"] if on else C["text2"], a)
        for j, s in enumerate(lines):
            draw_text(c, s, x + 44, yy + 50 + j * 50, font(34, "sans", 700), C["text"], a)
        yy += 90 + 50 * len(lines)
    if hl == "none":
        a = ease(tb / 0.8)
        draw_text(c, "全文没有提到“文化”", W / 2, y + 860, font(40, "sans", 900), C["text"], a, "center")
    vignette(c, 0.5)


def draw_cheese(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    ev = S["beat"]["ev"]
    bg_night(c)
    labels = ["机长的判断", "副驾驶的监控", "机械师的监控", "排班和休息", "地面报警"]
    if ev.get("align"):
        align = ease((S.get("first_align_tb", tb)) / 2.2)
    else:
        align = 0.0
    n = len(labels)
    cy = 790
    hole_y = cy + 10
    for i in range(n):
        x = 175 + i * 182
        th = 26
        front = path_from([(x - 52, cy - 290), (x + 40, cy - 250), (x + 40, cy + 270), (x - 52, cy + 310)], True)
        side = path_from([(x + 40, cy - 250), (x + 40 + th, cy - 256), (x + 40 + th, cy + 264), (x + 40, cy + 270)], True)
        c.drawPath(side, paint("#B8892E", 0.85))
        c.drawPath(front, paint("#F2C14E", 0.92))
        rng = random.Random(i * 17 + 3)
        holes = [(rng.uniform(-0.55, 0.45), rng.uniform(-0.8, 0.8), rng.uniform(12, 22)) for _ in range(4)]
        k0 = rng.uniform(-0.75, 0.75)
        ky = lerp(k0, (hole_y - cy) / 280, align)
        holes.append((-0.05, ky, 30))
        for hx, hy, r in holes:
            yy = cy + hy * 280 + (hx * 40) * 0.4
            c.drawOval(skia.Rect.MakeXYWH(x - 6 + hx * 80 - r * 0.62, yy - r, r * 1.24, r * 2), paint("#060A12", 0.96))
        c.drawPath(front, paint("#8F6A22", 1, stroke=2))
        a = 1.0 if (ev.get("labels") or ev.get("align")) else ease((tb - i * 0.3) / 0.5)
        draw_text(c, labels[i], x, cy + 360 + (i % 2) * 50, font(28, "sans", 700), C["text"], a, "center")
    if ev.get("beam"):
        k = ease(tb / 1.2)
        xe = lerp(40, W - 30, k)
        line(c, 40, hole_y, xe, hole_y, C["red"], 0.45, 22, blur=12)
        line(c, 40, hole_y, xe, hole_y, C["red"], 1, 6)
    draw_text(c, "“瑞士奶酪”：航空安全里常用的比喻", W / 2, 420, font(30, "sans", 700), C["text2"], 1, "center")
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 5 1978 波特兰（暖黄胶片）
# ════════════════════════════════════════════════════════════════════
def draw_ua173(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    stage = S["beat"]["ev"].get("stage", "intro")
    c.clear(rgb(C["sepia_bg"]))
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, 820), 900, [rgba("#3A2814", 1.0), rgba(C["sepia_bg"], 1.0)], [0, 1])
    c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    draw_text(c, "1978 · 波特兰", W - SIDE, SAFE_TOP + 46, font(32, "sans", 900), C["sepia"], 0.95, "right")
    focus = {"intro": 0.0, "gear": 0.15, "focus": 0.6, "focus2": 0.85, "flameout": 0.95, "dark": 1.0, "report": 0.5}[stage]
    # 起落架指示面板（注意力越集中，越大）
    s = lerp(1.0, 1.45, focus)
    cx, cy = W / 2, 820
    pw, ph = 500 * s, 300 * s
    rrect(c, cx - pw / 2, cy - ph / 2, pw, ph, 18 * s, "#2A2016", 1)
    rrect(c, cx - pw / 2, cy - ph / 2, pw, ph, 18 * s, C["sepia2"], 1, stroke=3)
    draw_text(c, "GEAR", cx, cy - ph / 2 + 50 * s, font(28 * s, "mono", 700), C["sepia"], 0.95, "center")
    for i, nm in enumerate(["LEFT", "NOSE", "RIGHT"]):
        lx, ly = cx + (i - 1) * 140 * s, cy + 16 * s
        c.drawCircle(lx, ly, 46 * s, paint("#14100B", 1))
        if nm == "NOSE":
            blink = 0.75 + 0.25 * math.sin(t * 5)
            c.drawCircle(lx, ly, 40 * s, paint(C["sepia_green"], 0.95 * blink))
            c.drawCircle(lx, ly, 72 * s, paint(C["sepia_green"], 0.3 * blink, blur=24))
        else:
            c.drawCircle(lx, ly, 40 * s, paint("#3B3226", 1))
        c.drawCircle(lx, ly, 46 * s, paint(C["sepia2"], 1, stroke=3))
        draw_text(c, nm, lx, ly + 90 * s, font(22 * s, "mono", 700), C["sepia"], 0.85, "center")
    # 油量表：被挤到角落
    fs = lerp(1.0, 0.45, focus)
    fx, fy = lerp(W / 2, W - 120, focus), lerp(1150, 1215, focus)
    r = 105 * fs
    c.drawCircle(fx, fy, r, paint("#241B12", 1))
    c.drawCircle(fx, fy, r, paint(C["sepia2"], 1, stroke=3))
    for k in range(11):
        ang = math.radians(220 - k * 26)
        line(c, fx + math.cos(ang) * r * 0.78, fy - math.sin(ang) * r * 0.78, fx + math.cos(ang) * r * 0.92,
             fy - math.sin(ang) * r * 0.92, C["sepia"], 0.9, max(1.2, 2 * fs))
    fuel = {"intro": 0.72, "gear": 0.62, "focus": 0.42, "focus2": 0.26, "flameout": 0.04, "dark": 0.0, "report": 0.0}[stage]
    ang = math.radians(220 - fuel * 260)
    line(c, fx, fy, fx + math.cos(ang) * r * 0.85, fy - math.sin(ang) * r * 0.85, C["red"] if fuel < 0.3 else C["sepia"],
         1, max(2, 5 * fs))
    draw_text(c, "FUEL", fx, fy + r * 0.6, font(max(16, 28 * fs), "mono", 700), C["sepia"], 0.9, "center")
    q = S["beat"].get("q")
    if q:
        a = fade_io(tb, S["bd"], 0.3, 0.25)
        quote_card(c, q, SIDE, 334, W - 2 * SIDE, a, accent=C["sepia"], t_type=clamp(tb / 1.2))
    if stage == "dark":
        c.drawRect(skia.Rect.MakeWH(W, H), paint("#000000", 0.7 * ease(tb / 1.0)))
    overlay_grain(c, int(t * 12), 9, 0.2, warm=True)
    vignette(c, 0.75, "#0A0603")


def draw_stat(c, S):
    tb, ts = S["tb"], S["ts"]
    ev = S["beat"]["ev"]
    bg_night(c)
    draw_text(c, "美国大航空公司 · 机组相关重大事故", W / 2, 420, font(34, "sans", 700), C["text2"], 1, "center")
    draw_text(c, "1978–1990（NTSB 回顾研究）", W / 2, 470, font(28, "sans", 400), C["text3"], 1, "center")
    k = ease((ts - 1.0) / 1.5) if ev.get("bar") or ts > 1.0 else 0
    rows = [("机长亲自驾驶", "副驾驶负责盯着", 0.82, C["red"], "八成以上"), ("副驾驶驾驶", "机长负责盯着", 0.18, C["cyan2"], "约两成")]
    for i, (a1, a2, v, col, lab) in enumerate(rows):
        y = 640 + i * 250
        draw_text(c, a1, SIDE, y, font(38, "sans", 900), C["text"], 1)
        draw_text(c, a2, SIDE, y + 46, font(28, "sans", 400), C["text2"], 1)
        rrect(c, SIDE, y + 80, (W - 2 * SIDE) * v * k, 60, 10, col, 0.9)
        draw_text(c, lab, SIDE + (W - 2 * SIDE) * v * k + 18 if v < 0.5 else SIDE + 20, y + 124, font(36, "sans", 900),
                  C["text"], k)
    if ev.get("quote"):
        a = ease(S["tb"] / 0.8)
        rrect(c, SIDE, 1080, W - 2 * SIDE, 170, 14, "#0A1120", a * 0.9)
        draw_lines(c, ["“副驾驶可能担心，对一个决定提出质疑，", "会被看成直接挑战机长的权威。”"], SIDE + 30, 1150,
                   font(34, "sans", 700), 52, C["text"], a)
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 6 NASA / 模拟器
# ════════════════════════════════════════════════════════════════════
def draw_nasa(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    stage = S["beat"]["ev"].get("stage", "conf")
    bg_night(c)
    draw_text(c, "1979 · 旧金山", W / 2, 420, font(36, "mono", 700), C["amber"], 1, "center")
    draw_text(c, "NASA 研讨会", W / 2, 480, font(34, "sans", 700), C["text2"], 1, "center")
    draw_text(c, "“驾驶舱里的资源管理”", W / 2, 560, font(48, "sans", 900), C["text"], 1, "center")
    # 三个人 + 连线
    pos = [(300, 900), (780, 900), (540, 1130)]
    k = ease(ts / 2.0) if stage == "crm" else 0.25
    for i in range(3):
        for j in range(i + 1, 3):
            line(c, *pos[i], *pos[j], C["cyan"], 0.25 + 0.6 * k, 3)
    for (x, y), nm in zip(pos, ["机长", "副驾驶", "机械师"]):
        c.drawCircle(x, y, 70, paint("#13213A", 1))
        c.drawCircle(x, y, 70, paint(C["cyan"], 0.5 + 0.5 * k, stroke=3))
        # 眼睛 + 嘴
        c.drawCircle(x - 22, y - 10, 7, paint(C["text"], 0.9))
        c.drawCircle(x + 22, y - 10, 7, paint(C["text"], 0.9))
        c.drawArc(skia.Rect.MakeXYWH(x - 22, y + 4, 44, 26), 20, 140, False, paint(C["text"], 0.9, stroke=4))
        draw_text(c, nm, x, y + 120, font(32, "sans", 700), C["text2"], 1, "center")
    if stage == "crm":
        a = ease(tb / 0.6) if S["beat"]["id"].endswith("06") else 1
        draw_text(c, "CRM", W / 2, 1320 - 30, font(96, "sans", 900), C["amber"], a, "center", glow=C["amber"], glow_alpha=0.3)
    vignette(c, 0.5)


def draw_sim(c, S):
    tb, ts = S["tb"], S["ts"]
    stage = S["beat"]["ev"].get("stage", "chaos")
    bg_night(c)
    draw_text(c, "747 模拟器实验 · 20 个航线机组", W / 2, 420, font(34, "sans", 700), C["text2"], 1, "center")
    cols = [("机长主动安排", 4, C["green"]), ("机长不管不问", 26, C["red"])]
    for i, (nm, nerr, col) in enumerate(cols):
        x = SIDE + 20 + i * 490
        a = 1.0 if (stage in ("good", "bad") and (i == 0 or stage == "bad")) else 0.3
        rrect(c, x, 500, 440, 700, 16, "#0A1120", 0.9)
        rrect(c, x, 500, 440, 700, 16, col, 0.6 * a, stroke=2)
        draw_text(c, nm, x + 220, 570, font(36, "sans", 900), C["text"], a, "center")
        draw_text(c, "错误", x + 220, 620, font(26, "sans", 400), C["text3"], a, "center")
        rng = random.Random(i)
        shown = nerr if a > 0.5 else 0
        k = ease(tb / 1.4)
        for j in range(int(shown * k)):
            px, py = x + 50 + rng.random() * 340, 680 + rng.random() * 460
            c.drawCircle(px, py, 13, paint(C["red"], 0.85))
        if i == 1 and stage == "bad" and tb > 1.6:
            a2 = ease((tb - 1.6) / 0.6)
            rrect(c, x + 30, 1060, 380, 110, 12, "#000000", 0.8 * a2)
            draw_text(c, "算错重量", x + 220, 1100, font(28, "sans", 700), C["text"], a2, "center")
            draw_text(c, "差 10 万磅", x + 220, 1150, font(40, "sans", 900), C["red"], a2, "center")
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 7 梯子 / 规矩
# ════════════════════════════════════════════════════════════════════
RUNGS = [("暗示", "“前面 25 海里那片回波，看着挺凶。”"), ("表达偏好", "“我觉得往左或往右绕，可能比较明智。”"),
         ("询问", "“你想往哪边绕？”"), ("建议", "“我们绕过这片天气吧。”"), ("机组义务", "“我觉得我们现在需要往右绕了。”"),
         ("命令", "“右转 30 度。”")]
# (出现顺序, 梯级, 原话, 时间/说话人, 距撞山)
LADDER_CARDS = [(1, 0, "captain, Guam condition is no good.", "01:21:59 副驾驶", "距撞山 20 分钟"),
                (2, 2, "don't you think it rains more?", "01:24:02 副驾驶", "距撞山 18 分钟"),
                (3, 3, "let's make a missed approach.", "01:42:19 副驾驶", "距撞山 7 秒"),
                (4, 5, "go around.", "01:42:22 机械师 → 01:42:23 机长", "距撞山 4 秒")]


def fit_font(s, maxw, size, kind="mono", weight=700, min_size=18):
    while size > min_size:
        f = font(size, kind, weight)
        if f.measureText(s) <= maxw:
            return f
        size -= 1
    return font(min_size, kind, weight)


def draw_ladder(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    ev = S["beat"]["ev"]
    build = ev.get("build", 0)
    cards = ev.get("cards", -1)
    bg_night(c)
    lx0, lx1 = SIDE + 20, SIDE + 120
    yb, yt = 1250, 380
    step = (yb - yt) / 6
    line(c, lx0, yt - 20, lx0, yb + 20, C["steel"], 1, 8)
    line(c, lx1, yt - 20, lx1, yb + 20, C["steel"], 1, 8)
    for i, (nm, ex) in enumerate(RUNGS):
        y = yb - (i + 0.5) * step
        on = build > i
        just = (build == i + 1)
        a = 1.0 if on else 0.16
        col = C["red"] if i == 5 else (C["amber"] if i >= 3 else C["cyan"])
        line(c, lx0, y, lx1, y, col if on else C["steel"], a, 7)
        k = ease(tb / 0.5) if just else 1.0
        draw_text(c, nm, lx1 + 30, y + 13, font(40, "sans", 900), col, a * k)
        if cards < 0:
            draw_text(c, ex, lx1 + 30, y + 56, font(27, "sans", 400), C["text2"], a * k * 0.95)
    draw_text(c, "硬", lx0 - 32, yt, font(30, "sans", 900), C["red"], 1, "center")
    draw_text(c, "软", lx0 - 32, yb + 10, font(30, "sans", 900), C["cyan"], 1, "center")
    if S["beat"]["id"] == "s7_09":
        a = ease(tb / 0.8)
        draw_text(c, "机长 → 多用命令", W - SIDE, yt + 40, font(32, "sans", 900), C["red"], a, "right")
        draw_text(c, "副驾驶 → 多用暗示", W - SIDE, yb - 10, font(32, "sans", 900), C["cyan"], a, "right")
    if cards >= 0:
        cx0, cw = lx1 + 190, 566
        for (ci, rung, en, who, ttl) in LADDER_CARDS:
            if cards >= ci:
                y = yb - (rung + 0.5) * step
                just = (cards == ci)
                k = ease(tb / 0.6) if just else 1.0
                col = C["red"] if rung == 5 else (C["amber"] if rung >= 3 else C["cyan"])
                rrect(c, cx0, y - 50, cw, 96, 12, "#0A1120", 0.94 * k)
                rrect(c, cx0, y - 50, cw, 96, 12, col, 0.85 * k, stroke=2)
                draw_text(c, who, cx0 + 16, y - 18, font(21, "sans", 700), col, k)
                draw_text(c, ttl, cx0 + cw - 16, y - 18, font(21, "sans", 700), C["text2"], k, "right")
                draw_text(c, en, cx0 + 16, y + 24, fit_font(en, cw - 32, 30), C["text"], k)
        # 高度表（离地）
        ax, ay0, ay1 = W - SIDE - 8, yt, yb
        rrect(c, ax - 14, ay0, 28, ay1 - ay0, 8, "#0A1120", 1)
        rrect(c, ax - 14, ay0, 28, ay1 - ay0, 8, C["steel"], 1, stroke=2)
        level = {0: 1.0, 1: 1.0, 2: 1.0, 3: 200 / 2600, 4: 90 / 2600}[min(cards, 4)]
        fill_h = (ay1 - ay0) * level
        rrect(c, ax - 10, ay1 - fill_h, 20, fill_h, 6, C["red"] if level < 0.2 else C["cyan2"], 0.95)
        draw_text(c, "离地", ax, ay0 - 16, font(22, "sans", 700), C["text3"], 1, "center")
    vignette(c, 0.5)


def draw_rules(c, S):
    tb, ts = S["tb"], S["ts"]
    rule = S["beat"]["ev"].get("rule", 0)
    bg_night(c)
    cards = [
        ("①", "提醒两次，没有正常回应", ["当成对方可能已经“失能”", "说“我来操纵”，直接接手"]),
        ("②", "三级用词，说到第三级全员停", ["我担心 → 我不舒服 → 这是安全问题"]),
        ("③", "机长先开门", ["出发前先说：", "“看到不对，随时说出来。”"]),
    ]
    for i, (num, head, body) in enumerate(cards):
        y = 380 + i * 300
        on = rule >= i + 1
        just = rule == i + 1
        a = (ease(tb / 0.6) if just else 1.0) if on else 0.15
        rrect(c, SIDE, y, W - 2 * SIDE, 250, 16, "#0A1120", 0.92)
        rrect(c, SIDE, y, W - 2 * SIDE, 250, 16, C["amber"], 0.6 * a, stroke=2)
        draw_text(c, num, SIDE + 30, y + 72, font(52, "sans", 900), C["amber"], a)
        draw_text(c, head, SIDE + 110, y + 70, font(38, "sans", 900), C["text"], a)
        if i == 1 and on:
            xs = [SIDE + 40, SIDE + 330, SIDE + 640]
            words = [("我担心", C["amber"]), ("我不舒服", "#FF8A3D"), ("这是安全问题", C["red"])]
            for j, (wd, col) in enumerate(words):
                kk = ease((tb - j * 0.5) / 0.5) if just else 1.0
                rrect(c, xs[j], y + 120, 270 if j < 2 else 320, 84, 12, col, 0.18 * a * kk)
                rrect(c, xs[j], y + 120, 270 if j < 2 else 320, 84, 12, col, a * kk, stroke=3)
                draw_text(c, wd, xs[j] + (135 if j < 2 else 160), y + 176, font(36, "sans", 900), col, a * kk, "center")
        else:
            for j, s in enumerate(body):
                draw_text(c, s, SIDE + 110, y + 140 + j * 52, font(34, "sans", 700), C["text2"], a)
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 8 权力距离
# ════════════════════════════════════════════════════════════════════
PDI = [("奥地利", 11), ("丹麦", 18), ("美国", 40), ("日本", 54), ("韩国", 60), ("法国", 68), ("马来西亚", 104)]


def draw_pdi(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    stage = S["beat"]["ev"].get("stage", "title")
    order = ["title", "survey", "question", "defn", "ruler"]
    si = order.index(stage)
    bg_night(c)
    draw_text(c, "权力距离", W / 2, 440, font(86, "sans", 900), C["text"], 1, "center")
    draw_text(c, "Power Distance", W / 2, 500, font(32, "mono", 700), C["amber"], 0.9, "center")
    if si >= 1 and si < 4:
        draw_text(c, "霍夫斯泰德 · IBM 员工调查 · 1967–1973", W / 2, 570, font(30, "sans", 700), C["text2"], 1, "center")
        draw_text(c, "11.6 万份问卷", W / 2, 620, font(30, "sans", 700), C["text2"], 1, "center")
    if si in (2, 3):
        a = ease(S["ts_stage"].get("question", 0) / 1.0) if "ts_stage" in S else 1
        x, y, w, h = SIDE + 20, 700, W - 2 * SIDE - 40, 360
        rrect(c, x + 8, y + 12, w, h, 6, "#000000", 0.4 * a, blur=12)
        rrect(c, x, y, w, h, 6, C["paper"], 0.95 * a)
        draw_text(c, "问卷中的一题（大意）", x + 36, y + 60, font(26, "serif", 700), "#6B6152", a)
        draw_lines(c, ["在你的经验里，“员工害怕向", "上级表达不同意见”，这种情况", "有多常见？"], x + 36, y + 130,
                   font(42, "serif", 900), 62, C["ink"], a)
        for j, opt in enumerate(["非常常见", "经常", "有时", "很少", "非常少"]):
            ox = x + 36 + j * 176
            c.drawRect(skia.Rect.MakeXYWH(ox, y + 300, 22, 22), paint(C["ink"], a * 0.8, stroke=2))
            draw_text(c, opt, ox + 32, y + 320, font(24, "serif", 400), C["ink"], a * 0.85)
    if si == 3:
        a = ease(S["tb"] / 0.8)
        rrect(c, SIDE, 1100, W - 2 * SIDE, 190, 14, "#0A1120", 0.92 * a)
        draw_lines(c, ["没有权力的人，在多大程度上", "预期、并且接受权力分配不平等"], W / 2, 1170, font(36, "sans", 900), 54,
                   C["text"], a, "center")
    if si == 4:
        a = ease(S["ts_stage"].get("ruler", 0) / 1.0) if "ts_stage" in S else 1
        y = 900
        x0, x1 = SIDE + 20, W - SIDE - 20
        line(c, x0, y, x1, y, C["text2"], a, 4)
        for v in range(0, 111, 10):
            xx = lerp(x0, x1, v / 110)
            line(c, xx, y - (16 if v % 50 == 0 else 9), xx, y, C["text2"], a, 2)
            if v % 50 == 0:
                draw_text(c, str(v), xx, y + 44, font(26, "mono", 700), C["text3"], a, "center")
        for i, (nm, v) in enumerate(PDI):
            k = ease((S["ts_stage"].get("ruler", 0) - 0.3 - i * 0.35) / 0.6) if "ts_stage" in S else 1
            xx = lerp(x0, x1, v / 110)
            up = (i % 2 == 0)
            yy = y - 70 if up else y + 110
            col = C["amber"] if nm == "韩国" else (C["cyan"] if nm == "美国" else C["text"])
            c.drawCircle(xx, y, 11, paint(col, k))
            line(c, xx, y, xx, yy + (20 if up else -40), col, 0.6 * k, 2)
            draw_text(c, nm, xx, yy, font(32, "sans", 900), col, k, "center")
            draw_text(c, str(v), xx, yy + (-44 if up else 44), font(28, "mono", 700), col, k, "center")
        draw_text(c, "权力距离指数（IBM 原始数据，节选）", W / 2, 700, font(30, "sans", 700), C["text2"], a, "center")
        draw_text(c, "分数是倾向，不是“谁会出事”的名单", W / 2, 1180, font(32, "sans", 700), C["text2"], a, "center")
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 9 争议：分屏
# ════════════════════════════════════════════════════════════════════
def draw_debate(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    side = S["beat"]["ev"].get("side", "L")
    bg_night(c)
    mid = W / 2
    show_split = side in ("L", "R", "L2", "both")
    if show_split or side == "check":
        a_split = 1.0 if side != "check" else 0.25
        line(c, mid, 380, mid, 1260, C["steel"], a_split, 2)
        aL = 1.0 if side in ("L", "L2", "both") else 0.35
        aR = 1.0 if side in ("R", "both") else 0.35
        aL *= a_split
        aR *= a_split
        draw_text(c, "一种说法", mid / 2, 420, font(40, "sans", 900), C["amber"], aL, "center")
        draw_text(c, "格拉德威尔《异类》", mid / 2, 470, font(26, "sans", 400), C["text2"], aL, "center")
        Ltxt = ["高权力距离", "+ 细密的敬语", "→ 副手只敢", "  绕着弯说", "→ 深层原因"]
        if side == "L2":
            Ltxt = ["回应：", "语言不推动文化，", "只是反映文化；", "下属不敢挑战机长，", "是航空界自己", "提出的问题。"]
        draw_lines(c, Ltxt, 60, 560, font(36, "sans", 700), 58, C["text"], aL)
        draw_text(c, "反驳", mid + mid / 2, 420, font(40, "sans", 900), C["cyan"], aR, "center")
        draw_text(c, "一位韩裔博主（2013）", mid + mid / 2, 470, font(26, "sans", 400), C["text2"], aR, "center")
        Rtxt = ["“天气不好”", "已经说得很直接；", "官方报告", "没归到文化上；", "“录音九成是英语”"]
        draw_lines(c, Rtxt, mid + 40, 560, font(36, "sans", 700), 58, C["text"], aR)
        q = S["beat"].get("q")
        if q:
            a = fade_io(tb, S["bd"], 0.3, 0.25)
            quote_card(c, q, SIDE, 900, W - 2 * SIDE, a, accent=C["amber"], t_type=clamp(tb / 1.2), scale=0.9)
    if side == "check":
        a = ease(S["ts_stage"].get("check", 0) / 0.8) if "ts_stage" in S else 1
        x, y, w = SIDE, 520, W - 2 * SIDE
        rrect(c, x, y, w, 720, 14, "#0A1120", 0.95 * a)
        rrect(c, x, y, w, 720, 14, C["cyan"], 0.6 * a, stroke=2)
        draw_text(c, "核对 NTSB 录音附录", x + 30, y + 60, font(36, "sans", 900), C["cyan"], a)
        rows = [("天气不好", "괌이 안좋네요. 기장님.", "韩"), ("保持 1440", "...천사백사십을 지켜야...", "韩"),
                ("看不见吧？", "안보이잖아?", "韩"), ("我们复飞吧", "missed approach 합시다.", "韩英"),
                ("复飞", "go around.", "英"), ("检查单 / 标准喊话", "flaps thirty …", "英")]
        f_ko = skia.Font(skia.FontMgr().matchFamilyStyle("Noto Sans CJK KR", skia.FontStyle(700, 5, skia.FontStyle.kUpright_Slant)), 30)
        for i, (zh, orig, lang) in enumerate(rows):
            yy = y + 140 + i * 92
            draw_text(c, zh, x + 30, yy, font(34, "sans", 700), C["text"], a)
            draw_text(c, orig, x + 330, yy, f_ko, C["text2"], a)
            col = C["amber"] if "韩" in lang else C["green"]
            rrect(c, x + w - 120, yy - 34, 92, 46, 10, col, 0.2 * a)
            draw_text(c, lang, x + w - 74, yy, font(28, "sans", 900), col, a, "center")
    if side == "rule":
        a = ease(S["ts_stage"].get("rule", 0) / 0.8) if "ts_stage" in S else 1
        x, y, w, h = SIDE + 40, 600, W - 2 * SIDE - 80, 460
        rrect(c, x, y, w, h, 18, "#0A1120", 0.95 * a)
        rrect(c, x, y, w, h, 18, C["amber"], a, stroke=3)
        draw_text(c, "驾驶舱规矩", W / 2, y + 80, font(44, "sans", 900), C["amber"], a, "center")
        for j, s in enumerate(["谁可以喊停", "怎么喊停", "喊了以后必须怎样"]):
            draw_text(c, s, W / 2, y + 190 + j * 80, font(42, "sans", 900), C["text"], a, "center")
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 10 后来：安全记录时间线
# ════════════════════════════════════════════════════════════════════
def draw_after(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    stage = S["beat"]["ev"].get("stage", "red")
    tst = S.get("ts_stage", {})
    bg_night(c)
    x0, x1 = SIDE + 20, W - SIDE - 20
    y = 860
    Y0, Y1 = 1996, 2027

    def X(yr):
        return lerp(x0, x1, (yr - Y0) / (Y1 - Y0))
    draw_text(c, "大韩航空 · 有人遇难的事故", W / 2, 420, font(40, "sans", 900), C["text"], 1, "center")
    line(c, x0, y, x1, y, C["steel"], 1, 4)
    for yr in (2000, 2005, 2010, 2015, 2020, 2025):
        line(c, X(yr), y - 10, X(yr), y + 10, C["text3"], 1, 2)
        draw_text(c, str(yr), X(yr), y + 48, font(24, "mono", 700), C["text3"], 1, "center")
    evs = [(1997.6, "1997 关岛 801（客机）"), (1999.3, "1999.4 上海（货机）"), (1999.97, "1999.12 伦敦（货机）")]
    for i, (yr, lab) in enumerate(evs):
        xx = X(yr)
        c.drawCircle(xx, y, 15, paint(C["red"], 1))
        c.drawCircle(xx, y, 28, paint(C["red"], 0.28, blur=10))
        yy = y - 260 + i * 78
        line(c, xx, y - 18, xx, yy + 12, C["red"], 0.6, 2)
        draw_text(c, lab, xx + 14, yy, font(30, "sans", 700), C["text"], 1)
    notes = [(1999.3, "1999 合作伙伴暂停代码共享"), (2001.6, "2001 韩国民航安全评级下调，数月后恢复")]
    for i, (yr, s) in enumerate(notes):
        draw_text(c, s, X(2001.2), y + 120 + i * 52, font(28, "sans", 700), C["amber"], 0.95)
    if stage in ("turn", "green"):
        a = ease(tst.get("turn", 9) / 0.8)
        xx = X(2000.05)
        line(c, xx, y - 40, xx, y + 300, C["cyan"], a * 0.8, 3, dash=[10, 8])
        draw_text(c, "2000 起：改训练 · CRM · 英语", xx + 16, y + 290, font(30, "sans", 900), C["cyan"], a)
    if stage == "green":
        k = ease(tst.get("green", 9) / 2.0)
        xe = lerp(X(2000.1), X(2026.9), k)
        line(c, X(2000.1), y, xe, y, C["green"], 0.4, 22, blur=10)
        line(c, X(2000.1), y, xe, y, C["green"], 1, 8)
        draw_text(c, "此后没有再发生有人遇难的事故", W / 2, 1250, font(36, "sans", 900), C["green"], k, "center")
    vignette(c, 0.5)


# ════════════════════════════════════════════════════════════════════
# 11 收尾 / 12 片尾
# ════════════════════════════════════════════════════════════════════
def draw_end(c, S):
    t, ts, tb = S["t"], S["ts"], S["tb"]
    ln = S["beat"]["ev"].get("line", 1)
    c.clear(rgb("#000000"))
    lines = [("飞机上最危险的，", "常常不是坏天气。"), ("是看见了问题的人，", "说不出那个词。"),
             ("一个组织安不安全，", "不看最聪明的人有多聪明，"), ("看的是最没有地位的那个人，", "敢不敢喊“停”。")]
    i = ln - 1
    a = fade_io(tb, S["bd"], 0.6, 0.5) if ln < 4 else ease(tb / 0.8)
    f = font(58, "sans", 900)
    y = 860
    l1, l2 = lines[i]
    draw_text(c, l1, W / 2, y, f, C["text"], a, "center")
    if ln == 4:
        w2 = f.measureText(l2)
        xs = W / 2 - w2 / 2
        pre = "敢不敢喊“"
        draw_text(c, pre, xs, y + 96, f, C["text"], a)
        xs += f.measureText(pre)
        draw_text(c, "停", xs, y + 96, f, C["red"], a, glow=C["red"], glow_alpha=0.6)
        xs += f.measureText("停")
        draw_text(c, "”。", xs, y + 96, f, C["text"], a)
    else:
        draw_text(c, l2, W / 2, y + 96, f, C["text"], a, "center")


NEXT_EP = "下期预告：挑战者号——工程师说了“不”"


def draw_credits(c, S, sources=()):
    ts = S["ts"]
    c.clear(rgb("#000000"))
    a = ease(ts / 1.0)
    draw_text(c, "组织里的权力", W / 2, 470, font(40, "sans", 700), C["amber"], a, "center")
    draw_text(c, NEXT_EP, W / 2, 540, font(36, "sans", 900), C["text"], a, "center")
    draw_text(c, "谨以此片纪念大韩航空 801 号班机", W / 2, 680, font(30, "sans", 700), C["text2"], a, "center")
    draw_text(c, "与联合航空 173 号班机的遇难者", W / 2, 724, font(30, "sans", 700), C["text2"], a, "center")
    y = 830
    draw_text(c, "主要资料", SIDE, y, font(26, "sans", 700), C["text3"], a)
    f = font(21, "sans", 400)
    y += 44
    for s in sources:
        for ln in wrap(s, f, W - 2 * SIDE):
            draw_text(c, ln, SIDE, y, f, C["text3"], a)
            y += 31
        y += 6
    draw_text(c, "配音：AI 合成（Qwen3-TTS，Apache-2.0）· 画面与音效：程序生成", SIDE, y + 30, f, C["text3"], a)
    draw_text(c, "人物均为剪影示意，不使用任何真实机组或遇难者影像", SIDE, y + 62, f, C["text3"], a)


SCENES = dict(cold=draw_cold, title=draw_title, night=draw_night, cockpit=draw_cockpit, map=draw_map,
              timeline=draw_timeline, profile=draw_profile, impact=draw_impact, memorial=draw_memorial,
              report=draw_report, cheese=draw_cheese, ua173=draw_ua173, stat=draw_stat, nasa=draw_nasa, sim=draw_sim,
              ladder=draw_ladder, rules=draw_rules, pdi=draw_pdi, debate=draw_debate, after=draw_after, end=draw_end,
              credits=draw_credits)
