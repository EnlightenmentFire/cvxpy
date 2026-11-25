# -*- coding: utf-8 -*-
"""Scene drawing functions. Each: f(ctx, T, sc, fi) with T seconds since scene start.
sc.cue(i) -> seconds since line i started (negative before); sc.ld(i) line duration; sc.dur."""
import math
import numpy as np
import cairo
from lib import *
from widgets import *

VIS_T, VIS_B = 240, 1370


def appear(sc, i, d=0.5, off=0.0):
    return ramp(sc.cue(i), off, d)


def between(sc, i, j, d=0.45):
    """visible from line i start until line j start (fades)."""
    return min(appear(sc, i, d), 1 - ramp(sc.cue(j), -d, d)) if j is not None else appear(sc, i, d)


def kelvin(ctx, x, y, ang, L, a):
    bx, by = -math.cos(ang), -math.sin(ang)
    nx, ny = -by, bx
    for sgn in (-1, 1):
        ctx.move_to(x + bx * 50, y + by * 50)
        ctx.line_to(x + bx * L + sgn * nx * L * 0.36, y + by * L + sgn * ny * L * 0.36)
        rgba(ctx, (0.9, 0.95, 1), 0.45 * a); ctx.set_line_width(5); ctx.stroke()
    g = cairo.LinearGradient(x, y, x + bx * L, y + by * L)
    g.add_color_stop_rgba(0, 0.9, 0.95, 1, 0.55 * a); g.add_color_stop_rgba(1, 0.9, 0.95, 1, 0)
    ctx.move_to(x + bx * 40 + nx * 10, y + by * 40 + ny * 10); ctx.line_to(x + bx * L + nx * 60, y + by * L + ny * 60)
    ctx.line_to(x + bx * L - nx * 60, y + by * L - ny * 60); ctx.line_to(x + bx * 40 - nx * 10, y + by * 40 - ny * 10); ctx.close_path()
    ctx.set_source(g); ctx.fill()


# ============================================================ s00 hook
def s00(ctx, T, sc, fi):
    # descending view: sea + carriers, clouds parting, bombers diving (shrinking)
    z = 1.0 + 0.35 * ease(T / 12)
    ctx.save(); ctx.translate(W / 2, 820); ctx.scale(z, z); ctx.translate(-W / 2, -820)
    paint_surface(ctx, sea_tex(), -110, -120, 1.0)
    rgba(ctx, (0.02, 0.05, 0.09), 0.25); ctx.paint()
    # carriers
    hit = [ramp(sc.cue(2), 0.3 + k * 0.9, 0.4) for k in range(3)]
    flash = sum(max(0, 1 - abs(sc.cue(2) - (0.3 + k * 0.9)) / 0.18) for k in range(3))
    for k, (x, y, ang) in enumerate(((300, 560, -2.2), (770, 660, -2.25), (520, 840, -2.2))):
        kelvin(ctx, x, y, ang, 300, 1.0)
        for j in (-1, 1):  # escorts
            ex, ey = x + j * 150 * math.sin(ang) + 60 * math.cos(ang), y - j * 150 * math.cos(ang) + 60 * math.sin(ang)
            kelvin(ctx, ex, ey, ang, 140, 0.6)
            ctx.save(); ctx.translate(ex, ey); ctx.rotate(ang); ctx.scale(1.4, 0.35); ctx.arc(0, 0, 22, 0, 6.29); ctx.restore()
            rgba(ctx, (0.35, 0.33, 0.33), 0.9); ctx.fill()
        carrier_top(ctx, x, y, ang, 1.9, JP, 1.0, fire=hit[k], t=T + k)
    ctx.restore()
    # bombers diving from viewer toward targets
    for k, (tx, ty, d0) in enumerate(((300, 560, 0.0), (770, 660, 0.6), (520, 840, 1.2))):
        u = clamp((T - d0) / (sc.lines[2]["s0"] + 0.3 + k * 0.9 - d0))
        if u < 1:
            sx, sy = W / 2 + (k - 1) * 380, 300 + k * 60
            px, py = lerp(sx, tx, ease_in(u) * 0.9 + 0.1 * u), lerp(sy, ty, ease_in(u) * 0.9 + 0.1 * u)
            s = lerp(9.0, 0.6, ease_in(u))
            plane_top(ctx, px, py, math.atan2(ty - sy, tx - sx), s, (0.55, 0.62, 0.70), 0.95 * (1 - ease_in(clamp((u - 0.85) / 0.15))))
    # clouds near the viewer, parting outwards
    for k, (cx, cy, seed) in enumerate(((-200, -300, 11), (380, -200, 12), (-350, 900, 13), (450, 1000, 14))):
        dx = (cx + 600 - W / 2) * (0.5 * ease(T / 8)); dy = (cy + 600 - 900) * 0.4 * ease(T / 8)
        sca = 1.6 + 0.5 * ease(T / 8)
        paint_surface(ctx, cloud_tex(seed), cx + dx - 300, cy + dy - 300, sca, 0.95 - 0.45 * ease(T / 10))
    if flash > 0:
        rgba(ctx, (1, 0.95, 0.85), 0.55 * clamp(flash)); ctx.paint()
    vignette(ctx, 0.7)
    # overlays
    if getattr(sc, "cover", False):
        return
    a0 = 1 - ramp(sc.cue(3), -0.3, 0.4)
    text(ctx, "「命运的五分钟」", W / 2, 1010, 96, GOLD, a0, SERIF, True, stroke=8, glow=16)
    text(ctx, "可能根本不存在？", W / 2, 1110, 64, WHITE, a0, SERIF, True, stroke=7)
    text(ctx, "1942 · 6 · 4  上午 10:20 前后", W / 2, 1215, 40, (0.85, 0.88, 0.92), a0, SERIF, True, stroke=6)
    # five minutes countdown
    a1 = appear(sc, 3, 0.4)
    if a1 > 0:
        rgba(ctx, (0, 0, 0), 0.65 * a1); ctx.paint()
        secs = 300 - int(clamp((sc.cue(4)) / max(1, sc.ld(4))) * 300 * 0.35) if sc.cue(4) > 0 else 300
        text(ctx, "只差", W / 2, 560, 64, WHITE, a1, SERIF, True, stroke=6)
        text(ctx, "五分钟？", W / 2, 720, 150, GOLD, a1, SERIF, True, stroke=8, glow=16)
        text(ctx, f"{secs // 60:02d}:{secs % 60:02d}", W / 2, 900, 110, (1, 0.9, 0.7), a1 * appear(sc, 4, 0.4), SANS, True, glow=12)
        strike(ctx, 200, 670, 880, ramp(sc.cue(5), 0.6, 0.5), a1, RED, 16)
        stamp(ctx, "可能是编出来的", W / 2, 1100, 64, appear(sc, 5, 0.3, 0.9), RED, -0.08, 1 + 0.4 * (1 - ramp(sc.cue(5), 0.9, 0.25)))


# ============================================================ s01 Fuchida's book
QUOTE_EN = ["At 1020 Admiral Nagumo gave the order", "to launch when ready. ...", "Within five minutes, all her planes", "would be launched. Five minutes!", "Who would have dreamed that the tide", "of battle would shift completely", "in that interval of time?"]


def s01(ctx, T, sc, fi):
    bg(ctx, T)
    # 0-1: Fuchida card
    a = between(sc, 0, 2)
    if a > 0:
        card(ctx, 90, 420, W - 180, 620, None, a)
        text(ctx, "渊田美津雄", W / 2, 560, 96, WHITE, a, SERIF, True, glow=10)
        text(ctx, "Fuchida Mitsuo", W / 2, 630, 40, GREY, a, "DejaVu Serif", False)
        ctx.move_to(240, 690); ctx.line_to(W - 240, 690); rgba(ctx, GOLD, 0.5 * a); ctx.set_line_width(2); ctx.stroke()
        text(ctx, "1941 · 空袭珍珠港 空中总指挥", W / 2, 780, 42, GOLD, a, SANS, True)
        text(ctx, "1942 · 中途岛 · 在旗舰赤城号上", W / 2, 870, 42, (1, 0.8, 0.75), a * appear(sc, 1, 0.4), SANS, True)
        text(ctx, "人物不出肖像 · 文字卡示意", W / 2, 990, 26, GREY, 0.7 * a, SANS, False)
    # 2-4: book page + translation
    a = between(sc, 2, 5)
    if a > 0:
        hl = (3, ramp(sc.cue(3), 2.0, 1.2))
        doc_page(ctx, 110, 330, W - 220, 600, a, "Midway: The Battle That Doomed Japan", QUOTE_EN, 32, hl, -0.015)
        text(ctx, "Fuchida & Okumiya, 美国海军学会 1955 · 经 Parshall (NWCR 2010) 转引", W / 2, 980, 25, GREY, a, SANS, False)
        aq = appear(sc, 3, 0.5)
        card(ctx, 70, 1020, W - 140, 250, None, aq, alpha=0.9)
        para(ctx, "「五分钟内，飞机就能全部起飞。五分钟！谁能想到，战局会在这段时间里完全翻转？」", W / 2, 1090, W - 220, 40, GOLD, aq, SERIF, True)
        if sc.cue(4) > 0:
            u = appear(sc, 4, 0.4)
            stamp(ctx, "惨败 → 运气不好", W / 2, 700, 70, u, RED, -0.1)
    # 5-6: Shattered Sword + records
    a = between(sc, 5, 7)
    if a > 0:
        card(ctx, 90, 330, W - 180, 230, None, a, edge=US)
        text(ctx, "Shattered Sword", W / 2, 420, 64, WHITE, a, "DejaVu Serif", True)
        text(ctx, "Parshall & Tully · 2005", W / 2, 490, 36, US, a, "DejaVu Serif", False)
        text(ctx, "依据：日方航空队行动记录（行動調書）", W / 2, 540, 30, GREY, a, SANS, False)
        u = appear(sc, 6, 0.5)
        if u > 0:
            text(ctx, "10:20 前后 · 赤城号飞行甲板（示意）", W / 2, 650, 34, GOLD, u, SANS, True)
            ctx.rectangle(100, 690, W - 200, 210); rgba(ctx, (0.45, 0.37, 0.27), u); ctx.fill()
            ctx.rectangle(100, 690, W - 200, 210); rgba(ctx, (1, 1, 1), 0.3 * u); ctx.set_line_width(2); ctx.stroke()
            for k in range(14):  # ghost: what the legend claims
                x = 170 + (k % 7) * 120; y = 750 + (k // 7) * 95
                plane_top(ctx, x, y, -math.pi / 2, 2.0, (1, 1, 1), 0.18 * u * (1 - ramp(sc.cue(6), 1.5, 1.0)))
            for k, x in enumerate((300, 640)):
                plane_top(ctx, x + 60 * math.sin(T + k), 795, math.pi, 2.4, (0.9, 0.9, 0.85), u)
            text(ctx, "传说：排满待飞的攻击机", W / 2, 950, 34, GREY, u * (1 - ramp(sc.cue(6), 1.5, 1.0)), SANS, False)
            text(ctx, "记录：只有起降的零式战斗机", W / 2, 950, 38, WHITE, u * ramp(sc.cue(6), 1.8, 0.8), SANS, True)
    # 7: four carriers + question
    a = between(sc, 7, 8)
    if a > 0:
        for k, n in enumerate(JP_CARRIERS):
            x = 175 + k * 243
            carrier_top(ctx, x, 620, -math.pi / 2, 1.5, JP, a, fire=0.7 * ramp(sc.cue(7), 1 + k * 0.5, 0.6), t=T + k)
            text(ctx, n, x, 760, 46, WHITE, a, SERIF, True)
        text(ctx, "？", W / 2, 1010, 200, GOLD, a * appear(sc, 7, 0.5, 2.0), SERIF, True, glow=20)
        text(ctx, "一天之内 · 四艘航母", W / 2, 1180, 52, WHITE, a, SERIF, True)
    a = appear(sc, 8, 0.5)
    if a > 0:
        text(ctx, "不讲运气", W / 2, 640, 120, GREY, a, SERIF, True)
        strike(ctx, 270, 600, 810, ramp(sc.cue(8), 0.6, 0.4), a, RED, 12)
        text(ctx, "讲机制", W / 2, 900, 160, GOLD, a * appear(sc, 8, 0.5, 0.9), SERIF, True, glow=18)


# ============================================================ s02 intel
def code_grid(ctx, T, a, af=0.0, top=360):
    rng = np.random.default_rng(42)
    for r in range(11):
        for c in range(5):
            g = "".join(str(d) for d in rng.integers(0, 10, 5))
            x = 140 + c * 200; y = top + r * 64
            col = (0.5, 0.75, 0.6)
            aa = a * (0.35 + 0.25 * math.sin(T * 2 + r * 1.3 + c))
            if (r, c) in ((3, 2), (6, 1), (8, 3)):
                text(ctx, "AF", x, y, 44, GOLD, a * (0.4 + 0.6 * af), SANS, True, glow=10 * af)
            else:
                text(ctx, g, x, y, 34, col, aa, "DejaVu Sans Mono", False)


def s02(ctx, T, sc, fi):
    bg(ctx, T)
    # map phases: lines 1-6 ; then 16
    am = max(between(sc, 1, 7), between(sc, 16, 17))
    if am > 0:
        cam = CAM_PAC
        draw_map(ctx, cam, am, top=VIS_T, bottom=VIS_B, t=T)
        jp_home = cam.p(*HASHIRA)
        if between(sc, 1, 7) > 0:
            u = ramp(sc.cue(2), 0.3, 2.2)
            arrow(ctx, bezier_pts(cam.p(136, 32), cam.p(160, 26), cam.p(*MIDWAY)), u, JP, 40, am)
            arrow(ctx, bezier_pts(cam.p(143, 41), cam.p(165, 52), cam.p(184, 51.5)), ramp(sc.cue(4), 0.2, 2.0), JP, 32, am)
            pin(ctx, *cam.p(*MIDWAY), "中途岛", am * appear(sc, 2, 0.4, 1.8), GOLD, 38, -20, 48, "r")
            pin(ctx, *cam.p(*PEARL), "珍珠港", am * appear(sc, 3, 0.4), US, 36, -18, 52, "r")
            text(ctx, "日本", *cam.p(137.5, 38.5), 40, (1, 0.85, 0.8), am, SERIF, True, stroke=6)
            text(ctx, "阿留申群岛", *cam.p(181, 55.5), 34, WHITE, am * appear(sc, 4, 0.4), SERIF, True, stroke=6)
            text(ctx, "联合舰队", *cam.p(152, 27.5), 34, (1, 0.8, 0.75), am * appear(sc, 2, 0.4, 1.0), SANS, True, stroke=6)
            u3 = appear(sc, 3, 0.5)
            if u3 > 0:
                pts = [cam.p(*MIDWAY), cam.p(*PEARL)]
                dashed_line(ctx, pts, WHITE, 0.8 * u3, 3, prog=ramp(sc.cue(3), 0.2, 1.2))
                mx, my = (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2
                text(ctx, "两千多公里", mx + 10, my - 18, 32, WHITE, u3, SANS, True, stroke=5)
            u5 = appear(sc, 5, 0.5)
            if u5 > 0:
                fleet_us(ctx, cam, (PEARL[0] - 4, PEARL[1] + 5.5), u5, ["企业号", "大黄蜂号", "约克城号"], s=0.55)
                text(ctx, "约克城号：珊瑚海受伤", *cam.p(PEARL[0] - 4, PEARL[1] + 9.8), 28, GOLD, u5 * appear(sc, 5, 0.4, 3.0), SANS, True, stroke=5)
            u6 = appear(sc, 6, 0.5)
            if u6 > 0:
                panel(ctx, 140, 1100, W - 280, 150, u6)
                text(ctx, "美方多出来的唯一一张牌：密码", W / 2, 1192, 44, GOLD, u6, SERIF, True)
        else:
            u = appear(sc, 16, 0.5)
            pin(ctx, *cam.p(*MIDWAY), "中途岛", am, GOLD, 38, -20, 48, "r")
            pin(ctx, *cam.p(*PEARL), "珍珠港", am, US, 36, -18, 52, "r")
            arrow(ctx, bezier_pts(cam.p(PEARL[0] - 1, PEARL[1] + 1.5), cam.p(196, 31), cam.p(*POINT_LUCK)), ramp(sc.cue(16), 0.3, 2.5), US, 38, am)
            fleet_us(ctx, cam, POINT_LUCK, am * ramp(sc.cue(16), 2.4, 0.6), ["", "", ""], s=0.4)
            text(ctx, "提前埋伏：中途岛东北", *cam.p(POINT_LUCK[0] + 1, POINT_LUCK[1] + 3.5), 34, US, am * ramp(sc.cue(16), 2.6, 0.6), SANS, True, stroke=6)
        map_frame(ctx, VIS_T, VIS_B, am)
    # code room 7-12
    a = between(sc, 7, 13)
    if a > 0:
        code_grid(ctx, T, a, ramp(sc.cue(9), 0.3, 0.6))
        panel(ctx, 90, 1080, W - 180, 190, a)
        text(ctx, "「海波」破译站 Station HYPO", W / 2, 1150, 44, GOLD, a, SERIF, True)
        text(ctx, "珍珠港 · 地下室 · 负责人 罗什福尔", W / 2, 1220, 34, WHITE, a, SANS, False)
        u = between(sc, 10, 11)
        if u > 0:
            rgba(ctx, (0, 0, 0), 0.6 * u); ctx.paint()
            text(ctx, "AF = ？", W / 2, 600, 140, GOLD, u, SANS, True, glow=16)
            for k, s in enumerate(("中途岛？", "阿留申？", "夏威夷？")):
                text(ctx, s, 200 + k * 340, 820, 52, WHITE, u * appear(sc, 10, 0.3, 0.6 + 0.5 * k), SERIF, True)
        u = between(sc, 11, 13)
        if u > 0:
            rgba(ctx, (0, 0, 0), 0.7 * u); ctx.paint()
            card(ctx, 110, 380, W - 220, 300, "中途岛 → 明码电报", u, edge=US)
            para(ctx, "岛上的淡水设备坏了。", W / 2, 520, W - 300, 54, WHITE, u, SERIF, True)
            text(ctx, "（故意让日军听见）", W / 2, 640, 32, GREY, u, SANS, False)
            u2 = appear(sc, 12, 0.5)
            card(ctx, 110, 740, W - 220, 300, "截获的日军情报", u2, edge=JP)
            text(ctx, "「AF 缺水」", W / 2, 900, 80, (1, 0.85, 0.8), u2, SERIF, True, glow=8)
            stamp(ctx, "AF = 中途岛", W / 2, 1150, 64, appear(sc, 12, 0.3, 1.8), GOLD, -0.06)
    # 13-15: funnel
    a = between(sc, 13, 16)
    if a > 0:
        text(ctx, "情报不是知道一切", W / 2, 420, 58, WHITE, a, SERIF, True)
        strike(ctx, 300, 400, 780, ramp(sc.cue(14), 0.2, 0.4), a, RED, 8)
        opts = ["西海岸", "夏威夷", "阿留申", "澳洲方向", "中途岛"]
        u = ramp(sc.cue(15), 0.2, 2.0)
        for k, s in enumerate(opts):
            x0 = 150 + k * 195; y0 = 560
            fin = k == 4
            x = lerp(x0, W / 2, u) if fin else x0
            y = lerp(y0, 1060, u) if fin else lerp(y0, 760, u)
            aa = a * (1 if fin else 1 - u * 0.85)
            text(ctx, s, x, y, 40 if not fin else lerp(40, 80, u), GOLD if fin else GREY, aa, SERIF, True)
        ctx.move_to(130, 620); ctx.line_to(W / 2 - 90, 960); ctx.move_to(W - 130, 620); ctx.line_to(W / 2 + 90, 960)
        rgba(ctx, GOLD, 0.5 * a * appear(sc, 15, 0.4)); ctx.set_line_width(3); ctx.stroke()
        text(ctx, "把对手的选项，缩小到够用", W / 2, 1220, 50, WHITE, a * appear(sc, 15, 0.5, 1.2), SERIF, True)
    # 17-19: Sunzi
    a = between(sc, 17, 20)
    if a > 0:
        quote_card(ctx, ["多算勝，少算不勝，", "而況於無算乎？"], "——《孫子·始計》", 440, a * appear(sc, 18, 0.6), 72,
                   plain="算得多的赢，算得少的输，更何况根本不算的。" if sc.cue(19) > 0 else None, h=560)
        text(ctx, "孙子", W / 2, 400, 60, GOLD, a * (1 - appear(sc, 18, 0.4)), SERIF, True)
    # 20-23: Nimitz
    a = appear(sc, 20, 0.5)
    if a > 0:
        card(ctx, 70, 340, W - 140, 330, None, a, edge=US)
        text(ctx, "尼米兹 → 弗莱彻、斯普鲁恩斯", W / 2, 420, 42, US, a, SERIF, True)
        text(ctx, "作战指令 · 1942 年 5 月 28 日", W / 2, 480, 32, GREY, a, SANS, False)
        text(ctx, "「经过计算的风险」", W / 2, 600, 72, WHITE, a * appear(sc, 21, 0.5), SERIF, True, glow=10)
        u = appear(sc, 21, 0.5, 0.8)
        doc_page(ctx, 90, 720, W - 180, 330, u, None,
                 ["...you will be governed by the principle", "of calculated risk, which you shall interpret", "to mean the avoidance of exposure of your", "force to attack by superior enemy forces", "without good prospect of inflicting ... greater", "damage on the enemy."], 27, (1, ramp(sc.cue(21), 1.5, 1.2)), 0.0)
        u = appear(sc, 22, 0.5)
        para(ctx, "没把握让敌人吃更大的亏，就别把航母暴露给更强的敌人。", W / 2, 1120, W - 200, 40, GOLD, u, SERIF, True)
        text(ctx, "可以赌，但每一注都要先算过", W / 2, 1255, 46, WHITE, appear(sc, 23, 0.5), SERIF, True)


def s02b(ctx, T, sc, fi):
    bg(ctx, T)
    cam = Cam(188.5, 29, 36)
    draw_map(ctx, cam, 1, top=VIS_T, bottom=VIS_B, t=T)
    pin(ctx, *cam.p(*MIDWAY), "中途岛", 1, GOLD, 38, 0, 52, "c")
    pin(ctx, *cam.p(*PEARL), "珍珠港", 1, US, 36, 0, 52, "c")
    u1 = appear(sc, 1, 0.5)
    # Japanese assumption: US carriers at Pearl, arriving late
    if u1 > 0:
        px, py = cam.p(PEARL[0] - 1.5, PEARL[1] + 2.0)
        for k in range(3):
            carrier_top(ctx, px + (k - 1) * 70, py, math.pi * 0.85, 0.45, US, u1 * 0.5)
        dashed_line(ctx, bezier_pts(cam.p(PEARL[0] - 2, PEARL[1] + 2.5), cam.p(192, 28), cam.p(MIDWAY[0] + 1, MIDWAY[1] + 0.5)), US, 0.7 * u1, 4, prog=ramp(sc.cue(1), 0.4, 2.0))
        text(ctx, "日军设想：美航母事后才从珍珠港赶来", W / 2, 360, 38, (1, 0.85, 0.8), u1, SANS, True, stroke=6)
    u2 = appear(sc, 2, 0.5)
    if u2 > 0:
        arrow(ctx, bezier_pts(cam.p(177, 32.5), cam.p(179.5, 31), cam.p(MIDWAY[0] - 0.4, MIDWAY[1] + 0.4)), ramp(sc.cue(2), 0.2, 1.5), JP, 34, u2)
        text(ctx, "先拔掉岛上的飞机", *cam.p(176.5, 34), 32, (1, 0.85, 0.8), u2, SANS, True, stroke=6)
        text(ctx, "再回头收拾美舰", *cam.p(176.5, 33.2 - 0.9), 32, (1, 0.85, 0.8), u2 * appear(sc, 2, 0.4, 2.0), SANS, True, stroke=6)
    u3 = appear(sc, 3, 0.5)
    if u3 > 0:
        panel(ctx, 110, 1090, W - 220, 160, u3, edge=JP)
        text(ctx, "前提：美国人不知道日本人要来", W / 2, 1185, 44, WHITE, u3, SERIF, True)
        strike(ctx, 150, 1172, W - 150, ramp(sc.cue(4), 0.8, 0.5), u3, RED, 10)
    u4 = appear(sc, 4, 0.5)
    if u4 > 0:
        fleet_us(ctx, cam, POINT_LUCK, u4, ["", "", ""], s=0.45)
        text(ctx, "实际：已在东北埋伏", *cam.p(POINT_LUCK[0], POINT_LUCK[1] + 2.4), 34, US, u4, SANS, True, stroke=6)
        xmark(ctx, *cam.p(PEARL[0] - 1.5, PEARL[1] + 2.0), 60, u4, RED, 9)
    map_frame(ctx, VIS_T, VIS_B, 1)


# ============================================================ s03 morning
def ops_base(ctx, T, cam, a=1.0, midway=True):
    draw_map(ctx, cam, a, top=VIS_T, bottom=VIS_B, t=T)
    if midway:
        pin(ctx, *cam.p(*MIDWAY), "中途岛", a, GOLD, 38, 0, 56, "c", r=9)


def s03(ctx, T, sc, fi):
    bg(ctx, T)
    map_on = max(between(sc, 0, 6), between(sc, 7, 10), between(sc, 17, 22))
    cam = CAM_OPS
    if map_on > 0:
        ops_base(ctx, T, cam, map_on)
        fleet_jp(ctx, cam, KIDO_0430, T, map_on, names=True, s=0.62)
        text(ctx, "日军机动部队", *cam.p(KIDO_0430[0], KIDO_0430[1] + 1.15), 40, (1, 0.8, 0.75), map_on, SANS, True, stroke=6)
        if between(sc, 0, 6) > 0:
            arrow(ctx, bezier_pts(cam.p(KIDO_0430[0] + 0.3, KIDO_0430[1] - 0.4), cam.p(182.2, 29.6), cam.p(MIDWAY[0] - 0.1, MIDWAY[1] + 0.25)), ramp(sc.cue(0), 1.5, 2.5), JP, 44, map_on)
            text(ctx, "108 架 空袭中途岛", *cam.p(182.9, 29.3), 32, (1, 0.85, 0.8), map_on * appear(sc, 0, 0.4, 3.0), SANS, True, stroke=6, align="l")
            u = appear(sc, 1, 0.4)
            if u > 0:
                panel(ctx, 70, 1170, 520, 170, u * map_on, edge=JP)
                text(ctx, "南云忠一 中将", 330, 1330, 44, WHITE, u * map_on, SERIF, True)
                text(ctx, "机动部队指挥官", 330, 1300, 30, GREY, u * map_on, SANS, False)
            u = between(sc, 2, 6)
            if u > 0:
                panel(ctx, 610, 1170, 400, 170, u * map_on, edge=GOLD)
                text(ctx, "预备队", 810, 1320, 40, GOLD, u * map_on, SERIF, True)
                torpedo(ctx, 740, 1290, 1.6, u * map_on); bomb(ctx, 880, 1290, 1.6, u * map_on)
                text(ctx, "对舰", 810, 1330, 26, GREY, u * map_on, SANS, False)
            u = appear(sc, 3, 0.4)
            if u > 0:
                panel(ctx, 560, 420, 450, 120, u * map_on * (1 - appear(sc, 5, 0.4)), edge=JP)
                text(ctx, "空袭队：需再炸一次", 785, 495, 38, WHITE, u * map_on * (1 - appear(sc, 5, 0.4)), SANS, True)
            u = appear(sc, 4, 0.4)
            for k in range(3):
                arrow(ctx, bezier_pts(cam.p(MIDWAY[0] + 0.2 - k * 0.3, MIDWAY[1] + 0.3), cam.p(181.5 + k * 0.4, 29.5), cam.p(KIDO_0430[0] + 0.25 - k * 0.2, KIDO_0430[1] - 0.3)), ramp(sc.cue(4), 0.3 + k * 0.4, 1.6), US, 22, map_on * u)
        if between(sc, 7, 10) > 0:
            # Tone scout
            u = ramp(sc.cue(7), 0.2, 2.5)
            p0 = cam.p(KIDO_0430[0] + 0.4, KIDO_0430[1] + 0.3); p2 = cam.p(TF16[0] - 0.4, TF16[1] + 0.2)
            pts = bezier_pts(p0, ((p0[0] + p2[0]) / 2, p0[1] - 120), p2)
            dashed_line(ctx, pts, (1, 0.8, 0.7), map_on, 3, prog=u)
            q = pts[min(len(pts) - 1, int(u * (len(pts) - 1)))]
            plane_top(ctx, q[0], q[1], -0.2, 1.4, (1, 0.8, 0.75), map_on)
            fleet_us(ctx, cam, TF16, map_on * ramp(sc.cue(7), 2.2, 0.5), ["", ""], s=0.5)
            fleet_us(ctx, cam, TF17, map_on * ramp(sc.cue(7), 2.2, 0.5), [""], s=0.5)
            uu = appear(sc, 7, 0.4, 2.6)
            panel(ctx, 90, 1150, W - 180, 200, uu * map_on, edge=JP)
            text(ctx, "利根号 4 号机：发现敌水面舰艇约 10 艘", W / 2, 1230, 38, WHITE, uu * map_on, SANS, True)
            text(ctx, "07:28 发出 → 约 08:00 送到南云 · 没提航母", W / 2, 1300, 32, GOLD, map_on * appear(sc, 8, 0.4), SANS, True)
        if between(sc, 17, 22) > 0:
            # returning Midway strike + Yamaguchi vs Nagumo
            for k in range(3):
                arrow(ctx, bezier_pts(cam.p(MIDWAY[0] - 0.2 + k * 0.2, MIDWAY[1] + 0.5), cam.p(181.6 - 0.2 * k, 29.7), cam.p(KIDO_0430[0] + 0.1 * k, KIDO_0430[1] - 0.35)), ramp(sc.cue(17), 0.2 + 0.3 * k, 2.0), (1, 0.6, 0.5), 22, map_on)
            text(ctx, "空袭队返航 · 油快烧完", *cam.p(182.2, 29.0), 32, (1, 0.85, 0.8), map_on * appear(sc, 17, 0.4, 1.5), SANS, True, stroke=6, align="l")
            u = appear(sc, 18, 0.4)
            if u > 0:
                panel(ctx, 70, 1130, 450, 220, u * map_on, edge=JP)
                text(ctx, "山口多闻（飞龙）", 295, 1290, 36, (1, 0.85, 0.8), u * map_on, SERIF, True)
                text(ctx, "立刻出击！", 295, 1290, 56, WHITE, u * map_on, SERIF, True)
                u2 = appear(sc, 19, 0.4)
                panel(ctx, 560, 1130, 450, 220, u2 * map_on, edge=GOLD)
                text(ctx, "南云忠一", 785, 1290, 36, GOLD, u2 * map_on, SERIF, True)
                text(ctx, "先回收 再出击", 785, 1290, 50, WHITE, u2 * map_on, SERIF, True)
            u = appear(sc, 20, 0.4)
            if u > 0:
                panel(ctx, 160, 420, W - 320, 120, u * map_on)
                text(ctx, "无护航攻击机 ≈ 送死", W / 2, 498, 44, WHITE, u * map_on, SANS, True)
        clock_t = [(0, 270, 270), (3, 420, 420), (5, 435, 435), (7, 448, 448), (8, 480, 480), (17, 510, 510)]
        cur = "04:30"
        for i, m0, m1 in clock_t:
            if sc.cue(i) >= 0:
                cur = f"{m0 // 60:02d}:{m0 % 60:02d}"
        if sc.cue(7) >= 0 and sc.cue(8) < 0:
            cur = "07:28"
        clock(ctx, cur, a=map_on if between(sc, 17, 22) <= 0 else 0, y=420 if between(sc, 3, 6) <= 0 else 640)
        map_frame(ctx, VIS_T, VIS_B, map_on)
    # 5-6, 9-10: hangar swap
    a = max(between(sc, 5, 7) * (1 if sc.cue(6) >= -0.3 or True else 0), between(sc, 9, 12))
    if a > 0 and map_on < 0.99:
        aa = a * (1 - map_on)
        swap = sc.cue(9) < 0
        if swap:
            u = clamp(sc.cue(6) / max(1, sc.ld(6)))
            planes = ["B" if k < int(u * 6) else ("x" if k == int(u * 6) else "T") for k in range(6)]
            title, tm = "07:15 换装：鱼雷 → 对地炸弹", "07:15"
            piles = int(u * 6)
        else:
            planes = ["B", "B", "B", "x", "T", "T"]
            title, tm = "07:45 改令：鱼雷先别卸", "07:45"
            piles = 8
        text(ctx, title, W / 2, 400, 50, GOLD, aa, SERIF, True, stroke=5)
        hangar_view(ctx, 110, 760, W - 220, T, aa, planes, piles, deck_planes=None, fuel=0.0 if swap else 0.6)
        if not swap:
            for k in range(4):
                x = 200 + k * 220 + 40 * math.sin(T * 1.5 + k)
                plane_top(ctx, x, 520 + 20 * math.cos(T * 2 + k), 0.3 * math.sin(T + k), 1.3, (0.8, 0.8, 0.75), aa * appear(sc, 10, 0.4))
            text(ctx, "头顶：空战", W / 2, 600, 32, GREY, aa * appear(sc, 10, 0.4), SANS, True)
            text(ctx, "卸下的弹药堆在机库", W / 2, 1220, 40, FIRE, aa * appear(sc, 10, 0.4, 1.5), SANS, True)
        else:
            text(ctx, "一枚鱼雷 八百多公斤 · 小车一架一架卸、一枚一枚挂", W / 2, 1220, 34, WHITE, aa * appear(sc, 6, 0.4), SANS, True)
        clock(ctx, tm, a=aa, y=560 if swap else 560, size=60)
    # 11: mechanism 1
    a = between(sc, 11, 12)
    if a > 0:
        text(ctx, "机制一", W / 2, 520, 60, GOLD, a, SERIF, True)
        text(ctx, "两个任务", W / 2, 700, 110, WHITE, a, SERIF, True, glow=12)
        text(ctx, "抢同一批飞机", W / 2, 860, 70, (1, 0.85, 0.8), a * appear(sc, 11, 0.4, 1.2), SERIF, True)
        text(ctx, "抢同一块甲板", W / 2, 980, 70, (1, 0.85, 0.8), a * appear(sc, 11, 0.4, 2.0), SERIF, True)
        u = appear(sc, 11, 0.4, 0.6)
        arrow(ctx, bezier_pts((140, 1150), (300, 1080), (500, 1150)), u, JP, 30, a)
        arrow(ctx, bezier_pts((940, 1150), (780, 1080), (580, 1150)), u, (0.8, 0.5, 0.2), 30, a)
        text(ctx, "炸中途岛", 160, 1230, 34, WHITE, a * u, SANS, True)
        text(ctx, "打美舰队", 920, 1230, 34, WHITE, a * u, SANS, True)
    # 12-14: deck as one-lane road, elevator, spotting time
    a = between(sc, 12, 15)
    if a > 0:
        text(ctx, "飞行甲板 = 单行道", W / 2, 400, 60, WHITE, a, SERIF, True)
        lift = clamp((sc.cue(13)) / max(1, sc.ld(13)) * 1.2) if sc.cue(13) > 0 else 0
        hangar_view(ctx, 110, 760, W - 220, T, a, ["T", "T", "-", "T", "T"], 0, deck_planes=[0.4, 0.55] if sc.cue(13) < 0 else None, elevator=(0.22, lift) if sc.cue(13) > 0 else None)
        if sc.cue(13) < 0:
            u = appear(sc, 12, 0.4, 0.8)
            arrow(ctx, poly_pts([(150, 560), (930, 560)], 60), u, US, 30, a)
            text(ctx, "放飞", 300, 520, 34, US, a * u, SANS, True)
            arrow(ctx, poly_pts([(930, 640), (150, 640)], 60), u, JP, 30, a * 0.5)
            text(ctx, "回收", 780, 700, 34, (1, 0.8, 0.75), a * u, SANS, True)
            xmark(ctx, W / 2, 600, 40, a * appear(sc, 12, 0.3, 1.8), RED, 8)
            text(ctx, "不能同时进行", W / 2, 1220, 42, WHITE, a * appear(sc, 12, 0.3, 1.8), SANS, True)
        u = appear(sc, 14, 0.4)
        if u > 0:
            rgba(ctx, (0, 0, 0), 0.65 * u); ctx.paint()
            text(ctx, "排一次大规模出击", W / 2, 600, 56, WHITE, u, SERIF, True)
            pr = ramp(sc.cue(14), 0.4, 2.2)
            rrect(ctx, 120, 700, W - 240, 70, 10); rgba(ctx, GREY, 0.4 * u); ctx.set_line_width(2); ctx.stroke()
            rrect(ctx, 124, 704, (W - 248) * pr, 62, 8); rgba(ctx, GOLD, 0.85 * u); ctx.fill()
            text(ctx, f"约 {int(pr * 45)} 分钟", W / 2, 900, 90, GOLD, u, SANS, True, glow=10)
            text(ctx, "提升 · 排列 · 暖机（40–45 分钟）", W / 2, 1000, 36, GREY, u, SANS, False)
    # 15-16 doctrine: merge into big formation
    a = between(sc, 15, 17)
    if a > 0:
        text(ctx, "日军习惯：几艘航母同时放飞，空中合成大机群", W / 2, 400, 36, WHITE, a, SANS, True)
        for k in range(4):
            cx = 170 + k * 247
            carrier_top(ctx, cx, 1130, -math.pi / 2, 1.1, JP, a)
            text(ctx, JP_CARRIERS[k], cx, 1250, 34, WHITE, a, SERIF, True)
            u = ramp(sc.cue(15), 0.5, 3.0)
            for j in range(5):
                sx, sy = cx + (j - 2) * 18, 1060
                ex, ey = W / 2 + (k - 1.5) * 60 + (j - 2) * 20, 560 + j * 14
                px, py = lerp(sx, ex, ease(u)), lerp(sy, ey, ease(u))
                plane_top(ctx, px, py, math.atan2(ey - sy, ex - sx), 1.2, (1, 0.75, 0.7), a)
        u = appear(sc, 16, 0.4)
        text(ctx, "威力大 · 但慢 · 也死板", W / 2, 490, 48, GOLD, a * u, SERIF, True)
        text(ctx, "要等所有飞机都准备好", W / 2, 820, 40, WHITE, a * appear(sc, 16, 0.4, 1.5), SANS, True)
    # 21: foreshadow torpedo planes
    a = appear(sc, 21, 0.5)
    if a > 0:
        rgba(ctx, (0, 0, 0), 0.75 * a); ctx.paint()
        for k in range(6):
            plane_side(ctx, 220 + k * 130, 760 + 20 * math.sin(T * 2 + k), 2.2, US, a)
        text(ctx, "几个小时后 · 美军鱼雷机", W / 2, 620, 52, US, a, SERIF, True)


# ============================================================ s04 nine waves
WAVES = [  # (from lon,lat), label   — schematic origins
    ((182.4, 28.6), "1"), ((182.6, 28.9), "2"), ((182.2, 28.7), "3"), ((182.9, 29.2), "4"), ((182.0, 28.5), "5"),
    ((184.0, 31.4), "6"), ((184.2, 31.0), "7"), ((184.5, 31.6), "8"), ((184.7, 31.9), "9")]


def s04(ctx, T, sc, fi):
    bg(ctx, T)
    cam = Cam(182.0, 30.4, 150)
    on = max(between(sc, 0, 4), between(sc, 8, 11))
    if on > 0:
        ops_base(ctx, T, cam, on)
        zig = 1.0 if sc.cue(8) > -0.5 else 0.25
        fleet_jp(ctx, cam, KIDO_1020, T, on, names=True, zig=zig, s=0.5)
        if between(sc, 0, 4) > 0:
            span = sc.lines[3]["s1"] - sc.lines[1]["s0"]
            cnt = 0
            for k, (o, lab) in enumerate(WAVES):
                t0 = sc.lines[1]["s0"] + k * span / 9
                u = ramp(T, t0, 1.4)
                if u <= 0:
                    continue
                cnt = k + 1
                tgt = cam.p(KIDO_1020[0] + 0.2 * math.sin(k * 2), KIDO_1020[1] + 0.15 * math.cos(k * 3))
                src = cam.p(*o)
                mid = ((src[0] + tgt[0]) / 2 + 80 * math.sin(k), (src[1] + tgt[1]) / 2 - 60)
                fade = 1 - ramp(T, t0 + 2.2, 1.0)
                arrow(ctx, bezier_pts(src, mid, tgt), u, US, 30, on * max(0.25, fade))
                if fade > 0.3:
                    text(ctx, lab, src[0], src[1] - 20, 40, WHITE, on * fade, SANS, True, stroke=6)
                xmark(ctx, tgt[0] + 40, tgt[1] - 40, 16, on * ramp(T, t0 + 1.4, 0.3) * fade, (1, 0.9, 0.9), 5)
            panel(ctx, 70, 1090, 460, 170, on)
            text(ctx, f"第 {max(cnt, 1)} 批", 300, 1170, 64, US, on, SANS, True)
            text(ctx, "07:00 – 10:00", 300, 1235, 30, GREY, on, SANS, False)
            panel(ctx, 560, 1090, 450, 170, on)
            text(ctx, "命中：0", 785, 1185, 64, WHITE, on * appear(sc, 3, 0.4), SANS, True)
            u = between(sc, 2, 3)
            if u > 0:
                for k, s in enumerate(("鱼雷机", "陆军轰炸机", "陆战队俯冲轰炸机", "B-17 空中堡垒")):
                    text(ctx, s, 80, 430 + k * 56, 36, US, on * u * appear(sc, 2, 0.3, k * 0.8), SANS, True, "l", stroke=5)
            text(ctx, "至少五次攻击 · 九批飞机（据 Parshall）", W / 2, 360, 34, GOLD, on * appear(sc, 1, 0.4), SANS, True, stroke=5)
        else:
            u = appear(sc, 8, 0.4)
            text(ctx, "全速转向规避 · 航迹拧成蛇形", W / 2, 400, 44, WHITE, on * u, SERIF, True, stroke=6)
            for k in range(3):
                ph = (T * 0.6 + k / 3) % 1
                x0, y0 = cam.p(*KIDO_1020)
                plane_top(ctx, x0 - 300 + 600 * ph, y0 - 180 - 60 * k, 0, 1.3, US, on * u * (1 - ph))
            u = appear(sc, 9, 0.4)
            if u > 0:
                panel(ctx, 110, 1040, W - 220, 220, on * u)
                labels = ["升空拦截", "打光子弹", "降落加油", "再起飞"]
                for k, s in enumerate(labels):
                    x = 210 + k * 220
                    hl = int(T * 1.2) % 4 == k
                    text(ctx, s, x, 1160, 38, GOLD if hl else WHITE, on * u, SANS, True)
                    if k < 3:
                        text(ctx, "→", x + 110, 1160, 36, GREY, on * u, "DejaVu Sans", True)
                text(ctx, "↺ 零战循环", W / 2, 1225, 30, GREY, on * u, SANS, False)
            u = appear(sc, 10, 0.4)
            if u > 0:
                rgba(ctx, (0, 0, 0), 0.0);
        map_frame(ctx, VIS_T, VIS_B, on)
    # 4-5: torpedo plane statistics
    a = between(sc, 4, 8)
    if a > 0:
        text(ctx, "航母鱼雷机「毁灭者」", W / 2, 400, 52, US, a, SERIF, True)
        stat_grid(ctx, 150, 500, 41, 11, 6, a, T, cell=78, lost_u=ramp(sc.cue(4), 1.0, 3.0))
        text(ctx, "41 架出击 · 回来 6 架", W / 2, 880, 56, WHITE, a * appear(sc, 4, 0.4, 3.0), SERIF, True)
        u = appear(sc, 5, 0.4)
        if u > 0:
            panel(ctx, 90, 950, W - 180, 260, a * u, edge=US)
            text(ctx, "大黄蜂号 第八鱼雷中队", W / 2, 1020, 42, US, a * u, SERIF, True)
            text(ctx, "15 架全部被击落 · 30 人只活 1 人", W / 2, 1095, 42, WHITE, a * u, SANS, True)
            text(ctx, "乔治·盖伊 少尉", W / 2, 1170, 40, GOLD, a * appear(sc, 5, 0.4, 2.5), SERIF, True)
        u = appear(sc, 6, 0.4)
        if u > 0:
            rgba(ctx, (0, 0, 0), 0.6 * u * a); ctx.paint()
            text(ctx, "毫无意义的牺牲？", W / 2, 720, 80, WHITE, a * u, SERIF, True, glow=10)
            text(ctx, "战争不只看命中率", W / 2, 900, 64, GOLD, a * appear(sc, 7, 0.4), SERIF, True)
    # 10-11: deck locked by fighters + mechanism 2
    a = between(sc, 10, 12, 0.4)
    if a > 0:
        rgba(ctx, BG0, a); ctx.paint()
        text(ctx, "甲板一直被战斗机占着", W / 2, 420, 54, WHITE, a, SERIF, True)
        lp = (T * 0.5) % 1
        hangar_view(ctx, 110, 720, W - 220, T, a, ["T", "B", "T", "B", "T"], 0, deck_planes=[0.35 + 0.1 * math.sin(T), 0.55], elevator=None)
        plane_side(ctx, lerp(1000, 200, lp), 640 - 60 * math.sin(lp * 3.14), 1.5, (0.85, 0.85, 0.8), a, flip=True)
        text(ctx, "机库里的攻击机：排不上去", W / 2, 1220, 44, (1, 0.8, 0.75), a, SANS, True)
        xmark(ctx, 250, 650, 30, a * appear(sc, 10, 0.3, 1.0), RED, 7)
    a = between(sc, 11, 12)
    if a > 0:
        rgba(ctx, (0, 0, 0), 0.8 * a); ctx.paint()
        text(ctx, "机制二", W / 2, 560, 60, GOLD, a, SERIF, True)
        text(ctx, "对手不用打中你", W / 2, 760, 84, WHITE, a, SERIF, True, glow=10)
        text(ctx, "只要让你一直忙", W / 2, 920, 84, GOLD, a * appear(sc, 11, 0.4, 1.4), SERIF, True, glow=10)
    # 12-13 Nautilus / Arashi
    a = between(sc, 12, 14)
    if a > 0:
        cam2 = Cam(181.3, 30.8, 330)
        ops_base(ctx, T, cam2, a, midway=False)
        fleet_jp(ctx, cam2, (KIDO_1020[0] + 0.25, KIDO_1020[1] + 0.2), T, a, names=False, s=0.55, zig=0.6)
        sx, sy = cam2.p(180.6, 30.3)
        ctx.save(); ctx.translate(sx, sy)
        rrect(ctx, -50, -9, 100, 18, 9); rgba(ctx, US, a); ctx.fill(); ctx.rectangle(-8, -16, 18, 8); ctx.fill(); ctx.restore()
        text(ctx, "鹦鹉螺号（潜艇）", sx, sy + 190, 34, US, a, SERIF, True, stroke=5)
        # Arashi circles the sub, drops depth charges, lags behind
        u = ramp(sc.cue(12), 1.5, 4.0)
        ang = u * 5
        dx, dy = sx + 170 * math.cos(ang), sy - 120 * math.sin(ang)
        hist = [(sx + 170 * math.cos(ang - k * 0.08), sy - 120 * math.sin(ang - k * 0.08)) for k in range(30, 0, -1)]
        wake(ctx, hist + [(dx, dy)], a, 8)
        carrier_top(ctx, dx, dy, -ang - math.pi / 2, 0.45, (0.85, 0.35, 0.3), a)
        text(ctx, "驱逐舰 岚号", dx, dy - 40, 36, (1, 0.85, 0.8), a, SERIF, True, stroke=5)
        for k in range(4):
            ph = (T * 0.8 + k * 0.25) % 1
            r = 10 + 50 * ph
            ctx.arc(sx + 40 * math.cos(k * 1.7), sy + 30 * math.sin(k * 2.3), r, 0, 6.29); rgba(ctx, (1, 1, 1), a * (1 - ph) * 0.7 * u); ctx.set_line_width(3); ctx.stroke()
        text(ctx, "深水炸弹", sx + 230, sy + 60, 30, WHITE, a * u, SANS, True, stroke=5)
        u = appear(sc, 13, 0.4)
        if u > 0:
            panel(ctx, 110, 1090, W - 220, 160, a * u, edge=GOLD)
            text(ctx, "岚号掉了队 —— 记住它", W / 2, 1185, 48, GOLD, a * u, SERIF, True)
        map_frame(ctx, VIS_T, VIS_B, a)
    # 14: no radar
    a = between(sc, 14, 15)
    if a > 0:
        rgba(ctx, BG0, a); ctx.paint()
        for k, (s, c) in enumerate((("雷达：没有", RED), ("空中巡逻：靠瞭望哨的眼睛", WHITE), ("零战之间：几乎没法用无线电协调", WHITE))):
            text(ctx, s, W / 2, 560 + k * 170, 50, c, a * appear(sc, 14, 0.4, k * 1.2), SERIF, True)
    # 15-16 altitude diagram
    a = appear(sc, 15, 0.5)
    if a > 0:
        rgba(ctx, BG0, a); ctx.paint()
        g = cairo.LinearGradient(0, 330, 0, 1270)
        g.add_color_stop_rgba(0, 0.12, 0.2, 0.32, a); g.add_color_stop_rgba(1, 0.05, 0.12, 0.18, a)
        ctx.set_source(g); ctx.rectangle(60, 330, W - 120, 940); ctx.fill()
        ctx.rectangle(60, 1160, W - 120, 110); rgba(ctx, (0.05, 0.15, 0.25), a); ctx.fill()
        text(ctx, "高空", 90, 400, 36, GREY, a, SANS, True, "l"); text(ctx, "低空（贴海面）", 90, 1140, 36, GREY, a, SANS, True, "l")
        for k in range(4):
            carrier_top(ctx, 260 + k * 190, 1200, 0, 0.8, JP, a)
        # torpedo planes low from right
        u = ramp(sc.cue(15), 0.0, 3.0)
        for k in range(5):
            plane_side(ctx, lerp(1150, 650, u) + k * 70, 1100 - k * 6, 1.4, US, a, flip=True)
        # zeros diving down to low
        z = ramp(sc.cue(15), 1.2, 2.5)
        for k in range(6):
            x = 200 + k * 110
            y = lerp(560 + (k % 2) * 60, 1030 + (k % 3) * 20, ease(z))
            plane_side(ctx, x, y, 1.3, (0.85, 0.85, 0.8), a, pitch=0.6 * (1 - abs(2 * z - 1)))
        text(ctx, "零战一窝蜂扑到低空", W / 2, 940, 40, WHITE, a * ramp(sc.cue(15), 2.5, 0.5), SANS, True, stroke=5)
        u = appear(sc, 16, 0.5)
        if u > 0:
            rrect(ctx, 120, 360, W - 240, 300, 16); rgba(ctx, GOLD, 0.6 * a * u); ctx.set_dash([16, 10]); ctx.set_line_width(4); ctx.stroke(); ctx.set_dash([])
            text(ctx, "高空，空了出来", W / 2, 540, 72, GOLD, a * u, SERIF, True, glow=12)


# ============================================================ s05 10:20
def s05(ctx, T, sc, fi):
    bg(ctx, T)
    cam = Cam(182.6, 31.0, 140)
    on = max(between(sc, 0, 7), 0)
    if on > 0:
        ops_base(ctx, T, cam, on, midway=False)
        burn = [ramp(sc.cue(5), d, 0.4) for d in (0.3, 99, 99, 99)]
        # order: 赤城 加贺 苍龙 飞龙 ; hits: 加贺 10:22, 苍龙 10:25, 赤城 10:26
        c5 = sc.cue(5); L5 = max(3.0, sc.ld(5))
        fires = (ramp(c5, L5 * 0.85, 0.4), ramp(c5, L5 * 0.05, 0.4), ramp(c5, L5 * 0.5, 0.4), 0)
        fleet_jp(ctx, cam, KIDO_1020, T, on, names=True, fires=fires, zig=0.5, s=0.5)
        fleet_us(ctx, cam, TF16, on, ["企业号", "大黄蜂号"], s=0.38)
        fleet_us(ctx, cam, (TF17[0] + 0.5, TF17[1] + 0.6), on, ["约克城号"], s=0.38)
        kx, ky = cam.p(*KIDO_1020)
        # Enterprise path: SW search, turn, follow Arashi
        e0 = cam.p(*TF16)
        pts_e = poly_pts([e0, cam.p(181.2, 29.6), cam.p(180.5, 29.9), cam.p(180.9, 30.5), (kx - 20, ky - 30)], 160)
        u = ramp(sc.cue(1), 0.0, max(2.0, sc.ld(1) + sc.ld(2) + sc.ld(3) - 0.5)) if sc.cue(1) > 0 else 0
        arrow(ctx, pts_e, u, US, 34, on)
        if sc.cue(2) > 0:
            ax, ay = cam.p(180.35, 29.75)
            wake(ctx, [(ax - 6 * k, ay + 9 * k) for k in range(30, 0, -1)] + [(ax, ay)], on, 8)
            carrier_top(ctx, ax, ay, -1.0, 0.35, (0.85, 0.35, 0.3), on)
            text(ctx, "岚号", ax - 50, ay + 10, 32, (1, 0.85, 0.8), on, SERIF, True, stroke=5, align="r")
        text(ctx, "麦克拉斯基 · 企业号俯冲轰炸机", *cam.p(181.6, 29.25), 30, US, on * appear(sc, 1, 0.4), SANS, True, stroke=5)
        y0 = cam.p(TF17[0] + 0.5, TF17[1] + 0.6)
        u2 = ramp(sc.cue(3), 0.2, 2.5)
        arrow(ctx, bezier_pts(y0, ((y0[0] + kx) / 2, y0[1] - 150), (kx + 30, ky - 40)), u2, (0.55, 0.85, 1.0), 34, on)
        text(ctx, "约克城号俯冲轰炸机（起飞更晚）", *cam.p(183.1, 32.25), 30, (0.6, 0.85, 1), on * appear(sc, 3, 0.4), SANS, True, stroke=5)
        u = appear(sc, 4, 0.4)
        if u > 0:
            panel(ctx, 140, 1100, W - 280, 150, on * u * (1 - appear(sc, 5, 0.3)))
            text(ctx, "不是精心协同 · 很大程度是巧合", W / 2, 1192, 44, WHITE, on * u * (1 - appear(sc, 5, 0.3)), SERIF, True)
        cl = "10:20"
        if c5 > L5 * 0.05: cl = "10:22"
        if c5 > L5 * 0.5: cl = "10:25"
        if c5 > L5 * 0.85: cl = "10:26"
        clock(ctx, cl, a=on, y=420, color=RED if c5 > 0 else GOLD)
        u = appear(sc, 5, 0.3)
        if u > 0:
            panel(ctx, 70, 1090, W - 140, 170, on * u, edge=RED)
            for k, (tm, nm, d) in enumerate((("10:22", "加贺", 0.05), ("10:25", "苍龙", 0.5), ("10:26", "赤城", 0.85))):
                aa = on * ramp(c5, L5 * d, 0.3)
                text(ctx, tm, 220 + k * 320, 1160, 46, RED, aa, SANS, True)
                text(ctx, nm, 220 + k * 320, 1225, 40, WHITE, aa, SERIF, True)
        # dive flashes
        for d, idx in ((0.05, 1), (0.5, 2), (0.85, 0)):
            fl = max(0, 1 - abs(c5 - L5 * d) / 0.25)
            if fl > 0:
                rgba(ctx, (1, 0.95, 0.85), 0.35 * fl * on); ctx.paint()
        map_frame(ctx, VIS_T, VIS_B, on)
    # 6-7: one bomb
    a = between(sc, 6, 8)
    if a > 0:
        rgba(ctx, BG0, 0.96 * a); ctx.paint()
        text(ctx, "赤城号", W / 2, 520, 60, WHITE, a, SERIF, True)
        text(ctx, "1", W / 2, 860, 300, RED, a, SERIF, True, glow=24)
        text(ctx, "颗直接命中的炸弹", W / 2, 1000, 56, WHITE, a, SERIF, True)
        text(ctx, "为什么一颗就够？", W / 2, 1180, 56, GOLD, a * appear(sc, 7, 0.4), SERIF, True)
    # 8-12: hangar chain reaction
    a = between(sc, 8, 13)
    if a > 0:
        rgba(ctx, BG0, a); ctx.paint()
        c8 = sc.cue(8)
        drop = ramp(sc.cue(11), 0.0, 0.8) if sc.cue(11) > 0 else None
        boom = clamp(sc.cue(11) / max(1, sc.ld(11))) if sc.cue(11) > 0.6 else None
        fire = ramp(sc.cue(11), 0.8, 1.5)
        hangar_view(ctx, 110, 720, W - 220, T, a, ["B", "T", "B", "x", "T", "B"], 10, fuel=appear(sc, 9, 0.4), fire=fire, boom=boom, bomb_drop=drop)
        notes = [(8, "卸下的鱼雷、炸弹堆在机库", 420), (9, "飞机加满油 · 输油管还连着", 490), (10, "机库封闭：爆炸能量散不出去", 560)]
        for i, s, y in notes:
            text(ctx, s, W / 2, y, 40, WHITE, a * appear(sc, i, 0.4), SANS, True, stroke=5)
        u = appear(sc, 11, 0.3)
        if u > 0:
            chain = ["炸弹", "飞机", "弹药", "更多弹药"]
            for k, s in enumerate(chain):
                aa = a * appear(sc, 11, 0.3, 0.8 + k * 0.7)
                text(ctx, s, 150 + k * 260, 1200, 40, FIRE if k else WHITE, aa, SERIF, True, stroke=5)
                if k < 3:
                    text(ctx, "→", 280 + k * 260, 1200, 36, FIRE, aa, "DejaVu Sans", True)
    a = appear(sc, 12, 0.5)
    if a > 0:
        rgba(ctx, (0, 0, 0), 0.8 * a); ctx.paint()
        text(ctx, "真正致命的", W / 2, 540, 56, GREY, a, SERIF, True)
        text(ctx, "不是那几颗炸弹", W / 2, 690, 74, WHITE, a, SERIF, True)
        text(ctx, "是机库里早就堆好的", W / 2, 860, 56, WHITE, a * appear(sc, 12, 0.4, 1.0), SERIF, True)
        text(ctx, "燃料和弹药", W / 2, 1000, 96, FIRE, a * appear(sc, 12, 0.4, 1.6), SERIF, True, glow=16)
        text(ctx, "因为同一批飞机，被派了两个任务", W / 2, 1200, 42, GOLD, a * appear(sc, 13, 0.4), SERIF, True)


def s05b(ctx, T, sc, fi):
    bg(ctx, T)
    nodes = ["情报：美航母提前埋伏", "两个任务：换弹又换回", "九批来袭：甲板被锁死", "鱼雷机：零战拖到低空", "俯冲轰炸机：高空进来", "机库弹药燃料：放大毁伤"]
    text(ctx, "一个上午 · 一条链", W / 2, 370, 56, GOLD, appear(sc, 0, 0.4), SERIF, True)
    for k, s in enumerate(nodes):
        lit = appear(sc, min(k + 1, 6), 0.4)
        y = 420 + k * 135
        chain_node(ctx, 170, y, W - 340, 100, s, max(0.35, lit), lit, RED if k == 5 else GOLD, 38)
        if k < 5:
            text(ctx, "↓", W / 2, y + 128, 34, GOLD, lit, "DejaVu Sans", True)
    u = appear(sc, 6, 0.5)
    if u > 0:
        text(ctx, "单看每一环都不致命 · 连起来就输掉一支舰队", W / 2, 1265, 36, WHITE, u, SANS, True)


# ============================================================ s06 sources
def s06(ctx, T, sc, fi):
    bg(ctx, T)
    a = between(sc, 0, 3)
    if a > 0:
        doc_page(ctx, 130, 340, W - 260, 470, a, "Midway (1955)", QUOTE_EN[2:], 32, (1, 1.0), 0.02)
        u = appear(sc, 1, 0.4)
        panel(ctx, 90, 870, W - 180, 170, a * u, edge=GREY)
        text(ctx, "渊田：阑尾炎术后，不能上天", W / 2, 940, 42, WHITE, a * u, SANS, True)
        text(ctx, "在赤城号上目击", W / 2, 1005, 34, GREY, a * u, SANS, False)
        u = appear(sc, 2, 0.4)
        text(ctx, "后来的书、电影 → 沿用这个场景", W / 2, 1180, 40, GOLD, a * u, SANS, True)
    a = between(sc, 3, 4)
    if a > 0:
        text(ctx, "三项检查", W / 2, 560, 110, WHITE, a, SERIF, True, glow=12)
        for k, s in enumerate(("① 对一手记录", "② 算时间", "③ 看讲述者")):
            text(ctx, s, W / 2, 760 + k * 110, 54, GOLD, a * appear(sc, 3, 0.3, 0.4 + 0.3 * k), SERIF, True)
    a = between(sc, 4, 7)
    if a > 0:
        text(ctx, "① 对一手记录", 70, 380, 50, GOLD, a, SERIF, True, "l")
        doc_page(ctx, 90, 420, W - 180, 330, a * appear(sc, 5, 0.4), "戦史叢書 43 · ミッドウェー海戦", [], 34, None, 0.0, SERIF)
        u = appear(sc, 5, 0.4)
        text(ctx, "防卫厅防卫研修所战史室 · 1971", W / 2, 590, 30, INK, u * a, SANS, False)
        text(ctx, "遭攻击时：甲板上没有攻击机", W / 2, 660, 38, (0.55, 0.08, 0.05), u * a * appear(sc, 5, 0.4, 2.5), SANS, True)
        text(ctx, "只有空中巡逻的战斗机", W / 2, 715, 38, (0.55, 0.08, 0.05), u * a * appear(sc, 5, 0.4, 3.5), SANS, True)
        record_table(ctx, 90, 800, W - 180, [("10:10", "回收零战 ×3（第 9 次空中巡逻）"), ("10:24", "零战起飞（空中巡逻）"), ("10:26", "被炸弹命中")], a * appear(sc, 6, 0.4), reveal=ramp(sc.cue(6), 0.3, 2.0), hi=0, size=34)
        text(ctx, "据 Parshall 引赤城号行动调书 · 时间为当地时间", W / 2, 1265, 26, GREY, a * appear(sc, 6, 0.4), SANS, False)
    a = between(sc, 7, 9)
    if a > 0:
        text(ctx, "② 算时间", 70, 380, 50, GOLD, a, SERIF, True, "l")
        x0, x1 = 120, W - 120
        def X(m): return lerp(x0, x1, (m - 600) / 60)  # 10:00..11:00
        ctx.move_to(x0, 760); ctx.line_to(x1, 760); rgba(ctx, GREY, a); ctx.set_line_width(3); ctx.stroke()
        for m, lab in ((600, "10:00"), (610, "10:10"), (625, "10:25"), (640, "10:40"), (660, "11:00")):
            ctx.move_to(X(m), 750); ctx.line_to(X(m), 770); ctx.stroke()
            text(ctx, lab, X(m), 810, 28, GREY, a, SANS, False)
        u = appear(sc, 8, 0.3)
        # available window 10:10 -> 10:25
        rrect(ctx, X(610), 640, X(625) - X(610), 70, 8); rgba(ctx, US, 0.8 * a * u); ctx.fill()
        text(ctx, "实际：15 分钟", (X(610) + X(625)) / 2, 620, 34, US, a * u, SANS, True)
        pr = ramp(sc.cue(8), 0.8, 2.5)
        need = X(610) + (X(650) - X(610)) * pr
        rrect(ctx, X(610), 880, need - X(610), 70, 8); rgba(ctx, GOLD, 0.85 * a * u); ctx.fill()
        text(ctx, "排一次出击：40 分钟以上", (X(610) + X(650)) / 2, 1000, 36, GOLD, a * u, SANS, True)
        ctx.move_to(X(625), 600); ctx.line_to(X(625), 980); rgba(ctx, RED, a * u); ctx.set_line_width(5); ctx.stroke()
        text(ctx, "炸弹落下", X(625) + 10, 1050, 34, RED, a * u, SANS, True, "l")
        stamp(ctx, "对不上", W / 2, 1200, 80, a * appear(sc, 8, 0.3, 3.0), RED, -0.08)
    a = between(sc, 9, 11)
    if a > 0:
        text(ctx, "③ 看讲述者", 70, 380, 50, GOLD, a, SERIF, True, "l")
        doc_page(ctx, 110, 450, W - 220, 420, a * appear(sc, 10, 0.4), "Naval War College Review · 2010",
                 ["Jonathan Parshall", "", "\"Reflecting on Fuchida,", "or 'A Tale of Three Whoppers'\""], 38, (2, ramp(sc.cue(10), 2.0, 1.0)), -0.02)
        text(ctx, "「三个弥天大谎」", W / 2, 1000, 70, RED, a * appear(sc, 10, 0.4, 2.5), SERIF, True, glow=8)
        text(ctx, "渊田的回忆 · 多处和记录对不上", W / 2, 1120, 40, WHITE, a * appear(sc, 9, 0.4, 0.5), SANS, True)
    a = between(sc, 11, 16)
    if a > 0:
        text(ctx, "争论没有结束", W / 2, 400, 56, WHITE, a, SERIF, True)
        u = appear(sc, 12, 0.4)
        card(ctx, 70, 470, W - 140, 330, None, a * u, edge=GREY)
        text(ctx, "Martin Bennett · NWCR 2013", W / 2, 540, 34, GREY, a * u, "DejaVu Serif", False)
        text(ctx, "\"Parshall's 'Whoppers' Examined\"", W / 2, 600, 34, WHITE, a * u, "DejaVu Serif", True)
        text(ctx, "引源田实 1948 年证词：", W / 2, 680, 36, WHITE, a * u * appear(sc, 12, 0.4, 2.5), SANS, True)
        text(ctx, "「离出击还差十五分钟」", W / 2, 760, 50, GOLD, a * u * appear(sc, 12, 0.4, 3.5), SERIF, True)
        u = appear(sc, 13, 0.4)
        text(ctx, "日方记录有缺漏，不能全信", W / 2, 870, 38, GREY, a * u, SANS, True)
        u = appear(sc, 14, 0.4)
        if u > 0:
            text(ctx, "15", 330, 1080, 160, GOLD, a * u, SANS, True, glow=10)
            text(ctx, "≠", W / 2, 1060, 120, WHITE, a * u, "DejaVu Sans", True)
            text(ctx, "5", 750, 1080, 160, GREY, a * u, SANS, True)
            text(ctx, "攻击机队并没有准备好", W / 2, 1220, 40, WHITE, a * appear(sc, 14, 0.4, 2.0), SANS, True)
        u = appear(sc, 15, 0.4)
        if u > 0:
            rgba(ctx, BG0, 0.85 * u * a); ctx.paint()
            text(ctx, "多数研究者：接受 Parshall 的结论", W / 2, 720, 46, WHITE, a * u, SERIF, True)
            text(ctx, "但争论仍在", W / 2, 860, 56, GOLD, a * u, SERIF, True)
    a = appear(sc, 16, 0.5)
    if a > 0:
        text(ctx, "为什么「五分钟」这么动人？", W / 2, 440, 52, WHITE, a * (1 - appear(sc, 17, 0.4) * 0.5), SERIF, True)
        u = appear(sc, 17, 0.4)
        text(ctx, "组织问题", W / 2, 660, 100, WHITE, a * u, SERIF, True)
        strike(ctx, 280, 630, 800, ramp(sc.cue(17), 1.5, 0.4), a * u, RED, 10)
        text(ctx, "↓", W / 2, 780, 70, GOLD, a * appear(sc, 17, 0.4, 1.2), "DejaVu Sans", True)
        text(ctx, "运气问题", W / 2, 920, 100, GOLD, a * appear(sc, 17, 0.4, 1.6), SERIF, True, glow=12)
        u = appear(sc, 18, 0.4)
        text(ctx, "情报 · 决策 · 甲板流程 → 无人负责", W / 2, 1100, 40, GREY, a * u, SANS, True)
        text(ctx, "只能怪天意", W / 2, 1200, 52, WHITE, a * appear(sc, 18, 0.4, 3.0), SERIF, True)


# ============================================================ s07 ending
def s07(ctx, T, sc, fi):
    bg(ctx, T)
    on = between(sc, 0, 4)
    cam = Cam(183.2, 31.3, 150)
    if on > 0:
        ops_base(ctx, T, cam, on, midway=False)
        fires = (1, 1, 1, ramp(sc.cue(2), 0.8, 0.6))
        fleet_jp(ctx, cam, KIDO_1020, T, on, names=True, fires=fires, s=0.48, dim=(0.5, 0.5, 0.5, 0.5 * ramp(sc.cue(2), 0.8, 0.6)))
        yk = (TF17[0] + 0.5, TF17[1] + 0.6)
        yf = ramp(sc.cue(1), 1.2, 0.6)
        fleet_us(ctx, cam, yk, on * (1 - 0.6 * ramp(sc.cue(3), 1.0, 1.5)), ["约克城号"], s=0.4, fire=[yf * (1 - ramp(sc.cue(3), 1.0, 1.5))], t=T)
        fleet_us(ctx, cam, TF16, on, ["企业号", "大黄蜂号"], s=0.4)
        hx, hy = cam.p(KIDO_1020[0] + 0.15, KIDO_1020[1] + 0.12)
        ykx, yky = cam.p(*yk)
        arrow(ctx, bezier_pts((hx + 40, hy - 20), ((hx + ykx) / 2, hy - 160), (ykx - 30, yky + 10)), ramp(sc.cue(1), 0.0, 1.5), JP, 32, on)
        text(ctx, "飞龙号两次反击", (hx + ykx) / 2, hy - 120, 34, (1, 0.85, 0.8), on * appear(sc, 1, 0.4), SANS, True, stroke=5)
        ex, ey = cam.p(*TF16)
        arrow(ctx, bezier_pts((ex - 30, ey), ((hx + ex) / 2, ey + 120), (hx + 40, hy + 20)), ramp(sc.cue(2), 0.0, 1.0), US, 32, on)
        clock(ctx, "17:00" if sc.cue(2) > 0 else "12:00", a=on * (1 - appear(sc, 3, 0.3)), y=420)
        clock(ctx, "07:01", a=on * appear(sc, 3, 0.3), y=420, date="6月7日")
        u = appear(sc, 0, 0.4)
        text(ctx, "只有飞龙号躲过了上午的俯冲轰炸", W / 2, 1210, 38, WHITE, on * u * (1 - appear(sc, 2, 0.3)), SANS, True)
        text(ctx, "飞龙号：起火，次日沉没", W / 2, 1210, 40, WHITE, on * appear(sc, 2, 0.3) * (1 - appear(sc, 3, 0.3)), SANS, True)
        text(ctx, "约克城号：被潜艇鱼雷击中，6 月 7 日沉没", W / 2, 1210, 38, US, on * appear(sc, 3, 0.3), SANS, True)
        map_frame(ctx, VIS_T, VIS_B, on)
    a = between(sc, 4, 6)
    if a > 0:
        for k, n in enumerate(JP_CARRIERS):
            x = 175 + k * 243
            off = ramp(sc.cue(4), 0.6 + k * 0.7, 0.6)
            carrier_top(ctx, x, 620, -math.pi / 2, 1.5, JP, a * (1 - 0.75 * off), dim=off)
            text(ctx, n, x, 760, 46, WHITE, a * (1 - 0.6 * off), SERIF, True)
        text(ctx, "四艘航母 · 三千多人阵亡", W / 2, 930, 54, WHITE, a * appear(sc, 4, 0.4, 3.2), SERIF, True)
        text(ctx, "大批熟练机械师与地勤，很难再补", W / 2, 1020, 38, GREY, a * appear(sc, 4, 0.4, 4.0), SANS, True)
        text(ctx, "太平洋上的主动权，开始转向", W / 2, 1180, 50, GOLD, a * appear(sc, 5, 0.4), SERIF, True)
    a = between(sc, 6, 12)
    if a > 0:
        paint_surface(ctx, sea_tex(), -110, -120 + (T * 4) % 40, 1.0, a * 0.8)
        rgba(ctx, BG0, 0.5 * a); ctx.paint()
        text(ctx, "五分钟", W / 2, 560, 140, WHITE, a, SERIF, True, glow=14)
        text(ctx, "悬念 · 遗憾 · 命运", W / 2, 690, 46, GREY, a * appear(sc, 7, 0.4), SERIF, True)
        text(ctx, "太好听 → 最该先查", W / 2, 800, 50, GOLD, a * appear(sc, 8, 0.4), SERIF, True)
        u = appear(sc, 9, 0.4)
        if u > 0:
            panel(ctx, 140, 870, W - 280, 140, a * u)
            text(ctx, "时间对得上吗？", W / 2, 965, 64, WHITE, a * u, SERIF, True)
        text(ctx, "「只差一点点」→ 先摊开时间表", W / 2, 1110, 42, WHITE, a * appear(sc, 10, 0.4), SANS, True)
        text(ctx, "差的，往往是一整套流程", W / 2, 1210, 48, GOLD, a * appear(sc, 11, 0.4), SERIF, True)
    a = between(sc, 12, 14)
    if a > 0:
        quote_card(ctx, ["盡信《書》，", "則不如無《書》。"], "——《孟子·盡心下》", 450, a, 76,
                   plain="全信书上写的，还不如没有这本书。" if sc.cue(13) > 0 else None, h=560)
    a = appear(sc, 14, 0.6)
    if a > 0:
        paint_surface(ctx, sea_tex(), -110, -120 + (T * 4) % 40, 1.0, a)
        rgba(ctx, BG0, 0.35 * a); ctx.paint()
        for k, n in enumerate(JP_CARRIERS):
            x = 175 + k * 243
            off = ramp(sc.cue(15), 0.5 + k * 1.2, 0.8)
            ctx.arc(x, 1120, 14, 0, 6.29); rgba(ctx, JP, a * (1 - off)); ctx.fill()
            ctx.arc(x, 1120, 30, 0, 6.29); rgba(ctx, JP, 0.25 * a * (1 - off)); ctx.fill()
            text(ctx, n, x, 1190, 32, GREY, a * (1 - 0.7 * off), SERIF, True)
        text(ctx, "胜负手", W / 2, 470, 60, GOLD, a, SERIF, True)
        text(ctx, "五分钟", W / 2, 640, 130, WHITE, a, SERIF, True)
        strike(ctx, 300, 600, 780, ramp(sc.cue(14), 0.8, 0.5), a, RED, 14)
        u = appear(sc, 15, 0.4)
        for k, s in enumerate(("情报先算了一步", "攻击锁住了甲板", "机库堆满改过两次的命令")):
            text(ctx, s, W / 2, 790 + k * 80, 44, WHITE, a * appear(sc, 15, 0.4, 0.5 + 1.6 * k), SERIF, True)


def s_end(ctx, T, sc, fi):
    bg(ctx, T)
    a = ramp(T, 0, 0.6)
    text(ctx, "主要参考", W / 2, 420, 48, GOLD, a, SERIF, True)
    refs = ["Parshall & Tully, Shattered Sword (2005)", "Parshall, NWCR 63(2), 2010", "Bennett, NWCR 66(1), 2013",
            "Isom, Midway Inquest (2007)", "Symonds, The Battle of Midway (2011)", "防卫厅战史室《戦史叢書·ミッドウェー海戦》1971",
            "Fuchida & Okumiya, Midway (1955)", "NHHC / NSA 中途岛史料", "《孙子·始计》《孟子·尽心下》"]
    for k, r in enumerate(refs):
        text(ctx, r, W / 2, 520 + k * 66, 30, WHITE, a, SANS if any(ord(ch) > 0x3000 for ch in r) else "DejaVu Sans", False)
    text(ctx, "地图与动画为示意 · 配音为 AI 生成", W / 2, 1180, 32, GREY, a, SANS, False)


SCENES = dict(s00=s00, s01=s01, s02=s02, s02b=s02b, s03=s03, s04=s04, s05=s05, s05b=s05b, s06=s06, s07=s07, end=s_end)
TITLES = dict(s00="命运的五分钟？", s01="一个流传半个世纪的故事", s02="情报：缩小选项", s02b="对手的盘算", s03="清晨：两个任务",
              s04="九批来袭", s05="十点二十分", s05b="机制回放", s06="史料对质", s07="收束", end="")
