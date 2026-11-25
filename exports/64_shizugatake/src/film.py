# -*- coding: utf-8 -*-
"""All scenes. Each scene fn(c, t, S) draws the full frame content for local time t.
S: dict with L (line start offsets), E (line end offsets), dur."""
import math, json, os
import numpy as np
import skia
from gfx import *
from geo import PLACES

RB = Basemap("region")
LB = Basemap("local")
_bg = {}


def bgimg(name):
    if name not in _bg:
        _bg[name] = skia.Image.open(f"/tmp/claude-0/work/base/{name}.png").makeRasterImage()
    return _bg[name]


def ink_bg(c, t, tint=(30, 26, 22), a_map=0.55):
    c.clear(col(INK))
    im = bgimg("bg_blur")
    sc = 1.08 + 0.02 * math.sin(t * 0.1)
    c.save(); c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-im.width() / 2, -im.height() / 2)
    p = skia.Paint(); p.setAlphaf(a_map)
    c.drawImage(im, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), paint(tint, 0.55))


# ---------- map helpers ----------
def RP(cam, n):
    return cam(*RB.geo.p(n)) if isinstance(n, str) else cam(*RB.geo(*n))


def LP(cam, n):
    return cam(*LB.geo.p(n)) if isinstance(n, str) else cam(*LB.geo(*n))


def rcam(names, pad=1.3, sy=820, **k):
    return fit_cam(RB, names, pad, sy, **k)


def lcam(names, pad=1.3, sy=820, **k):
    return fit_cam(LB, names, pad, sy, **k)


def campath(t, keys):
    """keys: list of (time, cam); eased between"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, c0), (t1, c1) in zip(keys, keys[1:]):
        if t <= t1:
            return Cam.blend(c0, c1, ease((t - t0) / max(1e-6, t1 - t0)))
    return keys[-1][1]


def drift(cam, t, amt=0.015):
    return Cam(cam.cx, cam.cy, cam.z * (1 + amt * t / 10), cam.sy)


def region_labels(c, cam, names, a=1.0, lsize=36, pos=None):
    pos = pos or {}
    for n in names:
        x, y = RP(cam, n); city(c, x, y, n, a, lsize=lsize, lpos=pos.get(n, "r"))


def lake_label(c, cam, a=0.8, P=LP, size=32):
    x, y = P(cam, "余吴湖"); text(c, "余吴湖", x, y + 10, size, "semi", (150, 190, 210), a, stroke=5)


def biwa_label(c, cam, P, pt, a=0.7, size=40):
    x, y = P(cam, pt); text(c, "琵 琶 湖", x, y, size, "semi", (120, 160, 185), a, stroke=5)


ROUTE = [(136.6161, 35.3620), (136.527, 35.372), (136.467, 35.368), (136.41, 35.392), (136.372, 35.414),
         (136.30, 35.445), (136.262, 35.470), (136.2223, 35.5023)]
RIDGE_B = ["内中尾山", "别所山", "行市山"]
RIDGE_R = ["神明山", "堂木山", "岩崎山", "大岩山", "贱岳", "田上山"]
FIELD = ["内中尾山", "行市山", "田上山", "木之本", "贱岳", "神明山"]


def torches_route(c, cam, t, prog, P=RP, n=70, a=1.0, s=1.0):
    pts = catmull([P(cam, p) for p in ROUTE], 10)
    for i in range(n):
        f = i / (n - 1)
        if f > prog:
            break
        k = clamp((prog - f) * 25)
        p, _ = at(pts, f)
        torch(c, p[0] + math.sin(i * 7.7) * 10, p[1] + math.cos(i * 3.1) * 10, t, a * k, seed=i, s=s)


# ======================= HOOK =======================
def s_firedragon(c, t, S):
    c.clear(col(INK))
    k1 = rcam(["大垣", "木之本", "长浜", "关原"], 1.15, sy=860)
    k2 = rcam(["大垣", "木之本", "余吴湖"], 1.05, sy=860)
    cam = campath(t, [(0, k1), (S["dur"], k2)])
    draw_map(c, RB, cam, "night")
    biwa_label(c, cam, RP, (136.12, 35.30), 0.6)
    prog = clamp(0.22 + t / (S["dur"] * 0.9) * 0.78)
    torches_route(c, cam, t, prog, n=90, s=1.25)
    p, ang = at(catmull([RP(cam, q) for q in ROUTE], 10), prog)
    radial(c, p[0], p[1], 160, (255, 120, 40), 0.55)
    region_labels(c, cam, ["大垣", "木之本", "长浜"], 0.95, 40, {"木之本": "l", "长浜": "l"})
    x, y = RP(cam, "余吴湖"); text(c, "余吴湖", x - 20, y - 30, 34, "semi", (150, 190, 210), 0.8, stroke=5)
    embers(c, t, 50, 11, 0.6)
    vignette(c, 0.8)
    a = 1 - ev(t, S["dur"] - 1.2, 1.0)
    text(c, "五个小时", W / 2, 330, 120, "brush", (255, 210, 150), a, stroke=12, shadow=18)
    text(c, "五十二公里", W / 2, 470, 120, "brush", (255, 160, 90), a, stroke=12, shadow=18)
    hh = 14 + 5 * prog
    text(c, f"{int(hh):02d}:{int((hh % 1) * 60):02d}", W - 70, 1330, 64, "heavy", GOLD, 0.9, "r", stroke=8)
    text(c, "1583 · 北近江", 70, 1330, 44, "serif", PAPER, 0.85, "l", stroke=6)


def field_cam(pad=1.12, sy=800):
    return lcam(FIELD, pad, sy)


def forts(c, cam, t, which, a=1.0, t0=0.0, step=0.25, lsize=32, labels=True, skip=(), states=None, pos=None):
    pos = pos or {}
    states = states or {}
    for i, n in enumerate(which):
        if n in skip:
            continue
        x, y = LP(cam, n)
        k = ev(t, t0 + i * step, 0.4)
        colr = BLUE if n in RIDGE_B or n in ("茂山",) else RED
        if n == "茂山":
            colr = LBLUE
        st = states.get(n, colr)
        fort(c, x, y, st, a * k, 32, n if labels else None, lsize + 6, pos.get(n, "r"))


def s_ridges(c, t, S):
    cam = drift(field_cam(), t, 0.03)
    draw_map(c, LB, cam, "day")
    fog(c, t, 0.55, 2, 300, 1300)
    # ridgelines
    a = ev(t, 0.3, 1.0)
    dashed(c, [LP(cam, n) for n in ["内中尾山", "别所山", "行市山", "茂山"]], ev(t, 0.3, 2.0), 7, BLUE, a, smooth=True)
    dashed(c, [LP(cam, n) for n in ["神明山", "堂木山", "岩崎山", "大岩山", "贱岳"]], ev(t, 0.9, 2.0), 7, RED, a, smooth=True)
    forts(c, cam, t, RIDGE_B + ["茂山"], 1, 0.3, 0.3, labels=False)
    forts(c, cam, t, RIDGE_R, 1, 0.9, 0.25, labels=False)
    lake_label(c, cam)
    tag(c, "柴田军", *LP(cam, (136.150, 35.585)), 40, BLUE, ev(t, 1.2))
    tag(c, "羽柴军", *LP(cam, (136.245, 35.540)), 40, RED, ev(t, 1.6))
    vignette(c, 0.7)
    k = ev(t, S["L"][1] + 1.6, 0.6)
    text(c, "谁先动 · 谁吃亏", W / 2, 330, 96, "brush", WHITE, k, stroke=10, shadow=16)


def s_leave(c, t, S):
    cam = drift(rcam(["大垣", "木之本", "岐阜", "长浜"], 1.25, sy=820), t, 0.03)
    draw_map(c, RB, cam, "day")
    region_labels(c, cam, ["大垣", "岐阜", "长浜"], 1, 38, {"长浜": "l"})
    x, y = RP(cam, "余吴湖")
    fort(c, x, y + 20, RED, 1 - 0.6 * ev(t, S["L"][1] + 2.5, 1.0), 26)
    fort(c, x - 30, y - 50, BLUE, 1, 26)
    p = ev(t, S["L"][0] + 0.3, 3.5)
    arrow(c, [RP(cam, q) for q in ROUTE[::-1]], p, 34, RED, hi=RED_HI)
    tag(c, "秀吉主力", *RP(cam, (136.50, 35.46)), 38, RED, ev(t, 1.5))
    tag(c, "美浓", *RP(cam, (136.70, 35.40)), 36, (80, 70, 60), ev(t, 1.0))
    k = ev(t, S["L"][1] + 2.4, 0.5)
    pulse = (t * 0.8) % 1.0
    c.drawCircle(x, y, 60 + 120 * pulse, paint((255, 230, 150), k * (1 - pulse), stroke=6))
    tag(c, "破绽", x + 140, y - 10, 48, (200, 150, 40), k, INK)
    vignette(c, 0.65)


RAID_PATH = [(136.1694, 35.5684), (136.179, 35.552), (136.184, 35.534), (136.189, 35.517), (136.1985, 35.5135), (136.2037, 35.5153)]


def s_raid(c, t, S):
    k1 = lcam(["行市山", "大岩山", "贱岳", "茂山"], 1.25, sy=800)
    cam = drift(k1, t, 0.04)
    draw_map(c, LB, cam, "night", mode2="day", k2=0.4 + 0.3 * ev(t, 0, S["dur"]))
    fog(c, t, 0.45, 5, 400, 1400)
    lake_label(c, cam)
    hit = S["L"][1] + 0.8
    forts(c, cam, t, ["行市山"], 1, 0, labels=True)
    forts(c, cam, t, ["岩崎山", "贱岳"], 1, 0, labels=True, pos={"贱岳": "b"})
    x, y = LP(cam, "大岩山")
    fort(c, x, y, mix(RED, (60, 60, 60), ev(t, hit + 1.0, 0.8)), 1, 30, "大岩山", 34, "b")
    arrow(c, [LP(cam, p) for p in RAID_PATH], ev(t, 0.3, S["L"][1] + 0.6, eout), 40, BLUE, hi=BLUE_HI)
    flashes(c, t, [(x + dx, y + dy) for dx, dy in ((-40, -20), (-60, 30), (-20, 40), (-70, -5), (10, -40))], fio(t, hit - 0.8, hit + 3.5), 9, 7)
    smoke(c, t, x - 30, y, fio(t, hit - 0.6, S["dur"] + 1), 12, 8, 90)
    xmark(c, x, y, 36, ev(t, hit + 1.0, 0.3))
    tag(c, "中川清秀 战死", x + 10, y - 120, 40, (60, 50, 45), ev(t, hit + 1.2, 0.4))
    tag(c, "佐久间盛政", *LP(cam, (136.160, 35.552)), 38, BLUE, ev(t, 0.8))
    vignette(c, 0.75)


def s_orders(c, t, S):
    cam = drift(lcam(["内中尾山", "大岩山", "行市山", "木之本"], 1.2, sy=820), t, 0.03)
    draw_map(c, LB, cam, "day")
    lake_label(c, cam)
    fort(c, *LP(cam, "内中尾山"), BLUE, 1, 30, "胜家本阵", 34)
    x, y = LP(cam, "大岩山")
    unit(c, x, y, BLUE, 1, 110, 50, "盛政", 34)
    forts(c, cam, t, ["贱岳", "岩崎山", "田上山"], 0.9, 0, labels=False)
    src = LP(cam, "内中尾山")
    for i, t0 in enumerate([S["L"][0] + 1.6, S["L"][1] + 0.2, S["L"][1] + 1.6]):
        pr = ev(t, t0, 1.3, eout)
        a = fio(t, t0, t0 + 2.4, 0.3)
        dashed(c, [src, ((src[0] + x) / 2 - 80 + i * 40, (src[1] + y) / 2), (x, y - 40)], pr, 6, BLUE_HI, a)
        if pr > 0.95:
            stamp(c, "撤！", x + 120 - i * 30, y - 120 - i * 70, 56, (90, 150, 255), a, -6 + i * 6)
    k = ev(t, S["L"][1] + 2.6, 0.5)
    text(c, "不 走", x, y + 160, 88, "brush", (255, 230, 200), k, stroke=10, shadow=14)
    vignette(c, 0.7)


def s_ogaki(c, t, S):
    cam = drift(rcam(["大垣", "木之本", "关原"], 1.35, sy=820), t, 0.03)
    draw_map(c, RB, cam, "day", mode2="night", k2=ev(t, 0, S["dur"]))
    region_labels(c, cam, ["大垣", "木之本"], 1, 40, {"木之本": "l"})
    x, y = RP(cam, "大垣")
    pulse = (t * 0.9) % 1
    c.drawCircle(x, y, 40 + 140 * pulse, paint(RED_HI, 1 - pulse, stroke=7))
    arrow(c, [RP(cam, q) for q in ROUTE], ev(t, S["L"][0] + 1.5, S["dur"] - 2, eout), 40, RED, hi=RED_HI)
    text(c, "14:00", x, y + 110, 72, "heavy", GOLD, ev(t, S["L"][0] + 1.2), stroke=9)
    k = ev(t, S["L"][1], 0.4)
    text(c, "5 小时", W / 2, 330, 110, "heavy", WHITE, k, stroke=12, shadow=16)
    text(c, "52 公里", W / 2, 470, 110, "heavy", (255, 170, 110), ev(t, S["L"][1] + 0.7, 0.4), stroke=12, shadow=16)
    vignette(c, 0.7)


def s_question(c, t, S):
    ink_bg(c, t, (20, 16, 14), 0.5)
    embers(c, t, 70, 21, 0.8)
    k = ev(t, 0.1, 0.8)
    text(c, "从无名小卒到天下人", W / 2, 520, 44, "serif", GOLD, k, spacing=0.25)
    sz = 230
    for i, ch in enumerate("贱岳之战"):
        kk = ev(t, 0.3 + i * 0.18, 0.5, eout)
        text(c, ch, W / 2 + (i - 1.5) * sz * 0.98, 820 - (1 - kk) * 40, sz, "brush", WHITE, kk, stroke=14, shadow=28)
    c.drawLine(W / 2 - 300, 900, W / 2 + 300, 900, paint(RED, ev(t, 1.0, 0.8), stroke=5))
    q1 = ev(t, S["L"][0], 0.5)
    for j, ln in enumerate(["先赢了一仗的人，", "为什么最后全线崩溃？"]):
        text(c, ln, W / 2, 1040 + j * 80, 58, "serif", WHITE, q1, stroke=6)
    q2 = ev(t, S["L"][1], 0.5)
    for j, ln in enumerate(["被调离前线的人，", "怎样把对手钓出来吃掉？"]):
        text(c, ln, W / 2, 1240 + j * 80, 58, "serif", (255, 190, 150), q2, stroke=6)
    vignette(c, 0.6)


# ======================= BACKGROUND =======================
def node(c, x, y, s, label, colr, a, sub=None, r=None, size=52):
    if a <= 0.003:
        return
    w = r or (measure(label, size) + 70)
    rrect(c, x - w / 2 + 6, y - 50 + 8, w, 100, 14, INK, a * 0.6, blur=8)
    rrect(c, x - w / 2, y - 50, w, 100, 14, colr, a * 0.95)
    rrect(c, x - w / 2, y - 50, w, 100, 14, mix(colr, WHITE, 0.5), a * 0.8, stroke=3)
    text(c, label, x, y + size * 0.36, size, "serif", WHITE, a)
    if sub:
        text(c, sub, x, y + 100, 36, "serif", PAPER, a * 0.9, stroke=5)


def s_kiyosu(c, t, S):
    ink_bg(c, t)
    L = S["L"]
    a0 = ev(t, 0.2)
    node(c, W / 2, 360, 1, "织田信长", (70, 60, 50), a0, "1582 本能寺之变")
    xmark(c, W / 2 + 190, 330, 22, ev(t, 1.2, 0.3) * a0, (200, 60, 50))
    # Hideyoshi rise
    k = fio(t, L[1], L[2] + 0.3)
    tag(c, "山崎之战 · 为主君复仇", W / 2, 560, 40, RED, k)
    kb = ev(t, L[2])
    c.drawLine(W / 2, 450, W / 2, 620, paint(PAPER, kb * 0.6, stroke=4))
    c.drawLine(270, 620, 810, 620, paint(PAPER, kb * 0.6, stroke=4))
    for x in (270, 810):
        c.drawLine(x, 620, x, 700, paint(PAPER, kb * 0.6, stroke=4))
    node(c, 270, 760, 1, "三子 信孝", BLUE, kb, r=360)
    node(c, 810, 760, 1, "嫡孙 三法师", RED, ev(t, L[2] + 1.6), r=380)
    text(c, "3 岁", 810, 880, 46, "heavy", GOLD, ev(t, L[2] + 2.6), stroke=6)
    text(c, "柴田胜家 推", 270, 920, 42, "serif", BLUE_HI, ev(t, L[2] + 0.6), stroke=5)
    text(c, "羽柴秀吉 推", 810, 940, 42, "serif", RED_HI, ev(t, L[2] + 2.0), stroke=5)
    # Niwa & Ikeda move
    for i, nm in enumerate(["丹羽长秀", "池田恒兴"]):
        m = ev(t, L[3] + 0.4 + i * 0.5, 1.2)
        x = lerp(W / 2, 810, m) + (i - 0.5) * 0
        y = 1080 + i * 120
        tag(c, nm, lerp(W / 2, 760, m), y, 44, mix((90, 80, 70), RED, m), ev(t, L[3], 0.4))
    k = ev(t, L[4], 0.6)
    rrect(c, 120, 1260, 840, 160, 18, INK, k * 0.7)
    text(c, "谁替孩子说话", W / 2, 1325, 54, "serif", WHITE, k)
    text(c, "谁就握住织田家", W / 2, 1395, 54, "serif", GOLD, ev(t, L[4] + 1.2, 0.6))
    vignette(c, 0.6)


def s_winter(c, t, S):
    L = S["L"]
    k1 = rcam(["北之庄", "长浜", "木之本"], 1.25, sy=820)
    cam = drift(k1, t, 0.03)
    draw_map(c, RB, cam, "day")
    x, y = RP(cam, "北之庄")
    # snow cover over Echizen
    radial(c, x + 120, y - 60, 520, (235, 240, 250), 0.42)
    snow(c, t, 0.9, 160, 9, (0, 0, W, 1000))
    city(c, x, y, "北之庄", 1, lsize=40)
    tag(c, "越前 · 大雪封山", x, y - 120, 44, (60, 90, 130), ev(t, 0.6))
    region_labels(c, cam, ["长浜"], 1, 38, {"长浜": "l"})
    k = ev(t, L[1], 0.5)
    p0 = (x, y); p1 = RP(cam, (136.30, 35.42))
    dashed(c, [p0, (lerp(p0[0], p1[0], .5) + 70, lerp(p0[1], p1[1], .5)), p1], ev(t, L[1] + 0.3, 2.5), 7, LBLUE, k)
    tag(c, "前田利家等 · 议和", (p0[0] + p1[0]) / 2 + 140, (p0[1] + p1[1]) / 2, 38, (70, 120, 150), ev(t, L[1] + 1.0))
    stamp(c, "缓兵之计", W / 2 + 160, 1240, 76, (220, 70, 50), ev(t, L[1] + 4.0, 0.3), -6)
    kk = ev(t, L[2] + 0.5, 0.8)
    if kk > 0:
        q = RP(cam, (136.40, 35.62))
        c.drawLine(p1[0], p1[1], q[0], q[1], paint(RED_HI, kk * 0.8, stroke=3))
        text(c, "？", q[0] + 20, q[1], 80, "heavy", RED_HI, kk, stroke=8)
    vignette(c, 0.65)


def s_winterwar(c, t, S):
    L = S["L"]
    cam = drift(rcam(["北之庄", "长浜", "岐阜", "大垣"], 1.2, sy=820), t, 0.03)
    melt = ev(t, L[2], 2.0)
    draw_map(c, RB, cam, "day")
    x, y = RP(cam, "北之庄")
    radial(c, x + 120, y - 60, 520, (235, 240, 250), 0.42 * (1 - melt))
    snow(c, t, 0.9 * (1 - melt), 120, 9, (0, 0, W, 900))
    city(c, x, y, "北之庄", 1, lsize=38)
    for i, (n, t0) in enumerate([("长浜", L[1] + 0.3), ("岐阜", L[1] + 2.2)]):
        px, py = RP(cam, n)
        f = ev(t, t0, 0.5)
        fort(c, px, py, mix(BLUE, RED, f), 1, 28, n, 38, "l" if n == "长浜" else "r", pulse=(t * 0.9 % 1) * fio(t, t0, t0 + 2))
    q = RP(cam, (136.78, 35.78))
    k = ev(t, L[1] + 4.0, 0.6)
    tag(c, "结好越后上杉景胜", q[0] - 100, q[1] + 70, 38, RED, k)
    dashed(c, [RP(cam, "长浜"), q], ev(t, L[1] + 4.2, 1.2), 5, RED_HI, k)
    # pincer arrows on Echizen
    arrow(c, [q, (x + 120, y - 20)], ev(t, L[1] + 5.0, 1.0), 22, RED, 0.8 * k)
    text(c, "雪一化 · 出山决战", W / 2, 1320, 80, "brush", WHITE, ev(t, L[2] + 0.5), stroke=10, shadow=14)
    vignette(c, 0.65)


# ======================= STANDOFF =======================
def s_deploy(c, t, S):
    L = S["L"]
    k0 = lcam(["柳濑", "内中尾山", "行市山", "木之本", "贱岳", "神明山"], 1.12, sy=820)
    cam = drift(k0, t, 0.02)
    draw_map(c, LB, cam, "day")
    lake_label(c, cam)
    # Shibata arrive from north
    arrow(c, [LP(cam, (136.185, 35.64)), LP(cam, "柳濑"), LP(cam, "内中尾山")], ev(t, 0.5, 2.5), 34, BLUE, hi=BLUE_HI)
    tag(c, "柴田 约3万", *LP(cam, (136.225, 35.598)), 40, BLUE, ev(t, 1.2))
    forts(c, cam, t, ["内中尾山", "别所山", "行市山"], 1, L[1] - 0.2, 0.6, pos={"行市山": "l", "内中尾山": "l", "别所山": "l"})
    tag(c, "胜家本阵", *LP(cam, (136.205, 35.600)), 32, (40, 60, 110), ev(t, L[1] + 0.3))
    tag(c, "盛政", *LP(cam, (136.145, 35.560)), 32, (40, 60, 110), ev(t, L[1] + 2.0))
    fort(c, *LP(cam, "茂山"), LBLUE, ev(t, L[1] + 2.6), 24, "茂山", 30, "l")
    # Hashiba arrive from south
    arrow(c, [LP(cam, (136.25, 35.44)), LP(cam, (136.235, 35.47)), LP(cam, "木之本")], ev(t, L[2] + 0.2, 2.0), 34, RED, hi=RED_HI)
    tag(c, "羽柴 约5万", *LP(cam, (136.205, 35.470)), 40, RED, ev(t, L[2] + 0.8))
    city(c, *LP(cam, "木之本"), "木之本", ev(t, L[2] + 1.0), lpos="b", lsize=34)
    # probe of Shinmeiyama
    k = fio(t, L[3], L[4] + 0.5)
    arrow(c, [LP(cam, (136.195, 35.570)), LP(cam, (136.212, 35.560))], ev(t, L[3] + 0.3, 1.0), 20, BLUE, k)
    flashes(c, t, [LP(cam, "神明山")], k, 3, 5)
    # fort chain
    order = ["堂木山", "神明山", "大岩山", "岩崎山", "贱岳"]
    for i, n in enumerate(order):
        tt = L[4] + 3.2 + i * 1.1
        fort(c, *LP(cam, n), RED, ev(t, tt, 0.4), 24, n, 30, {"贱岳": "b", "大岩山": "b", "神明山": "r", "堂木山": "r", "岩崎山": "r"}[n], pulse=(t % 1) * fio(t, tt, tt + 1.2))
    fort(c, *LP(cam, "田上山"), RED, ev(t, L[4] + 8.6), 24, "田上山", 30)
    dashed(c, [LP(cam, n) for n in ["神明山", "堂木山", "岩崎山", "大岩山", "贱岳"]], ev(t, L[4] + 8.0, 2.0), 6, RED, 0.8)
    vignette(c, 0.6)


def s_fortcut(c, t, S):
    """cross-section of a fortified hilltop vs a column on the path"""
    L = S["L"]
    ink_bg(c, t, (24, 22, 20), 0.35)
    gy = 1180
    # hill profile
    hill = skia.Path(); hill.moveTo(0, gy)
    pts = [(0, gy), (180, gy - 10), (360, gy - 120), (520, gy - 330), (640, gy - 470), (700, gy - 520), (860, gy - 530), (1080, gy - 520), (1080, H), (0, H)]
    hill.moveTo(*pts[0])
    for p in pts[1:]:
        hill.lineTo(*p)
    hill.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([(0, gy - 530), (0, gy + 200)], [col((92, 82, 60)), col((40, 36, 28))]))
    c.drawPath(hill, p)
    c.drawPath(hill, paint((150, 130, 95), 0.8, stroke=4))
    k1 = ev(t, L[1], 0.5)
    # moat
    mo = skia.Path(); mo.moveTo(580, gy - 400); mo.lineTo(610, gy - 360); mo.lineTo(650, gy - 370); mo.lineTo(670, gy - 450)
    c.drawPath(mo, paint((20, 18, 16), k1, stroke=14))
    lab = [("壕沟", 560, gy - 300, L[1] + 0.2), ("削陡的斜坡", 380, gy - 160, L[1] + 0.9), ("栅栏", 690, gy - 640, L[1] + 1.6), ("射击位", 900, gy - 690, L[1] + 2.4)]
    for s_, x, y, t0 in lab:
        tag(c, s_, x, y, 38, (70, 60, 48), ev(t, t0, 0.4))
    # palisade
    kp = ev(t, L[1] + 1.4, 0.5)
    for i in range(10):
        x = 700 + i * 34
        c.drawLine(x, gy - 520, x, gy - 600, paint((120, 90, 60), kp, stroke=10))
        c.drawLine(x, gy - 600, x - 5, gy - 612, paint((120, 90, 60), kp, stroke=6))
    # defenders
    kd = ev(t, L[1] + 2.2, 0.5)
    for i in range(6):
        x = 760 + i * 50
        c.drawCircle(x, gy - 548, 14, paint(RED, kd))
    # column on path
    kc = ev(t, L[0] + 2.0, 0.6)
    march = (t * 18) % 60
    for i in range(16):
        x = -40 + i * 42 + march
        if x > 470:
            continue
        yy = gy - 8 - max(0, (x - 180)) * 0.6
        c.drawCircle(x, yy - 16, 12, paint(BLUE, kc))
        c.drawLine(x, yy - 4, x, yy + 10, paint(BLUE, kc, stroke=6))
    # fire lines
    kf = fio(t, L[2], S["dur"] + 1, 0.4)
    for i in range(5):
        ph = (t * 1.4 + i * 0.37) % 1
        x0, y0 = 770 + i * 50, gy - 548
        x1, y1 = 120 + i * 70, gy - 40
        xx, yy = lerp(x0, x1, ph), lerp(y0, y1, ph)
        c.drawLine(xx, yy, xx + (x1 - x0) * 0.05, yy + (y1 - y0) * 0.05, paint((255, 210, 120), kf * (1 - ph), stroke=4))
    flashes(c, t, [(770 + i * 50, gy - 560) for i in range(5)], kf, 31, 2.5)
    text(c, "以一当数", 820, 360, 96, "brush", RED_HI, ev(t, L[2] + 0.3), stroke=10, shadow=12)
    text(c, "走出工事，只是一条长队", W / 2, 1330, 54, "serif", BLUE_HI, ev(t, L[2] + 3.0), stroke=6)
    vignette(c, 0.55)


def s_patience(c, t, S):
    L = S["L"]
    swap = L[4] - 0.4
    if t < swap:
        cam = drift(field_cam(1.1), t, 0.025)
        draw_map(c, LB, cam, "day")
        fog(c, t, 0.35 + 0.35 * fio(t, L[3] - 0.3, swap), 7, 300, 1400)
        forts(c, cam, t, RIDGE_B + ["茂山"], 1, 0, 0, labels=False)
        forts(c, cam, t, RIDGE_R, 1, 0, 0, labels=False)
        lake_label(c, cam)
        # ghost sortie: blue leaves, flank glows
        k = fio(t, L[1], L[2] + 1.5)
        gp = [LP(cam, "行市山"), LP(cam, (136.190, 35.535)), LP(cam, (136.200, 35.518))]
        arrow(c, gp, ev(t, L[1] + 0.3, 2.5), 30, BLUE, k * 0.75, dash=[30, 16])
        for i, n in enumerate(["贱岳", "岩崎山", "田上山"]):
            arrow(c, [LP(cam, n), LP(cam, (136.197, 35.528))], ev(t, L[1] + 2.4 + i * 0.3, 1.0), 18, RED, k)
        tag(c, "侧面暴露", *LP(cam, (136.215, 35.535)), 38, (170, 40, 30), ev(t, L[1] + 3.2) * k)
        text(c, "谁先动 · 谁吃亏", W / 2, 330, 96, "brush", WHITE, fio(t, 0.3, L[1] + 0.2), stroke=10, shadow=14)
        text(c, "耐心本身就是武器", W / 2, 330, 90, "brush", GOLD, fio(t, L[2] + 0.3, swap), stroke=10, shadow=14)
    else:
        cam = drift(rcam(["北之庄", "长浜", "岐阜", (136.45, 34.88)], 1.15, sy=830), t - swap, 0.03)
        draw_map(c, RB, cam, "day")
        k = ev(t, swap, 0.5)
        x, y = RP(cam, "余吴湖")
        fort(c, x, y, RED, k, 24); fort(c, x - 24, y - 50, BLUE, k, 24)
        # supply lines
        k2 = fio(t, L[4], L[5] - 0.2)
        dashed(c, [RP(cam, "北之庄"), RP(cam, (136.26, 35.80)), RP(cam, (136.19, 35.62))], ev(t, L[4] + 0.3, 2.0), 8, BLUE_HI, k2)
        tag(c, "胜家粮道 · 翻越山口", *RP(cam, (136.40, 35.86)), 36, BLUE, ev(t, L[4] + 1.5) * k2)
        dashed(c, [RP(cam, "长浜"), RP(cam, "木之本")], ev(t, L[4] + 3.0, 1.0), 8, RED_HI, k2)
        tag(c, "秀吉后方 · 近江平原", *RP(cam, (136.38, 35.34)), 36, RED, ev(t, L[4] + 3.5) * k2)
        k3 = ev(t, L[5], 0.5)
        for n, p_, lab_, t0 in [("岐阜", RB.geo.p("岐阜"), "岐阜 织田信孝", L[5] + 2.0), ("伊势", RB.geo(136.45, 34.88), "伊势 泷川一益", L[5] + 1.2)]:
            xx, yy = cam(*p_)
            kk = ev(t, t0, 0.4)
            pulse = (t * 0.8) % 1
            c.drawCircle(xx, yy, 30 + 90 * pulse, paint(BLUE_HI, kk * (1 - pulse), stroke=5))
            fort(c, xx, yy, BLUE, kk, 26)
            tag(c, lab_, xx, yy + 90, 38, BLUE, kk)
    vignette(c, 0.6)


# ======================= OPENING =======================
def s_tomino(c, t, S):
    L = S["L"]
    cam = drift(rcam(["余吴湖", "大垣", "岐阜", "长浜"], 1.25, sy=830), t, 0.03)
    draw_map(c, RB, cam, "day", mode2="night", k2=0.35 * ev(t, L[2], 1.5))
    region_labels(c, cam, ["大垣", "岐阜", "长浜"], 1, 38, {"长浜": "l"})
    gx, gy = RP(cam, "岐阜")
    kk = ev(t, L[0] + 0.3, 0.4)
    pulse = (t * 0.9) % 1
    c.drawCircle(gx, gy, 30 + 100 * pulse, paint(BLUE_HI, kk * (1 - pulse), stroke=6))
    tag(c, "信孝再起", gx, gy - 70, 38, BLUE, kk)
    x, y = RP(cam, "余吴湖")
    fort(c, x, y + 20, RED, 1, 24); fort(c, x - 24, y - 40, BLUE, 1, 24)
    tag(c, "秀长 留守", x + 150, y + 30, 34, (120, 50, 40), ev(t, L[1]))
    arrow(c, [RP(cam, q) for q in ROUTE[::-1]], ev(t, L[1] + 0.8, 3.0, eout), 34, RED, hi=RED_HI)
    # flood band between Ogaki and Gifu
    kf = ev(t, L[2] + 0.6, 1.0)
    if kf > 0:
        a_, b_ = RP(cam, (136.655, 35.55)), RP(cam, (136.640, 35.20))
        pth = skia.Path(); pth.moveTo(*a_)
        for i in range(1, 21):
            f = i / 20
            pth.lineTo(lerp(a_[0], b_[0], f) + 10 * math.sin(f * 20 + t * 3), lerp(a_[1], b_[1], f))
        c.drawPath(pth, paint((80, 150, 220), kf * 0.5, stroke=60, blur=20))
        c.drawPath(pth, paint((140, 200, 240), kf * 0.8, stroke=10))
        tag(c, "揖斐川泛滥", (a_[0] + b_[0]) / 2 + 170, (a_[1] + b_[1]) / 2 - 40, 38, (40, 90, 140), kf)
    rain(c, t, ev(t, L[2], 0.8) * 0.9)
    k = ev(t, L[3] + 0.2, 0.5)
    text(c, "主帅不在 · 主力不在", W / 2, 330, 84, "brush", WHITE, k, stroke=10, shadow=14)
    if k > 0:
        c.drawCircle(x, y, 90 + 10 * math.sin(t * 4), paint((255, 220, 120), k * 0.9, stroke=5))
    vignette(c, 0.65)


def s_raidmap(c, t, S):
    L = S["L"]
    k0 = lcam(["行市山", "大岩山", "贱岳", "神明山", "木之本"], 1.15, sy=810)
    cam = drift(k0, t, 0.03)
    dawn = ev(t, L[4] - 1.0, 3.0)
    draw_map(c, LB, cam, "night", mode2="day", k2=0.2 + 0.8 * dawn)
    fog(c, t, 0.4 * (1 - dawn), 12, 300, 1400)
    lake_label(c, cam)
    hit = L[3] + 0.3
    falls = ev(t, L[3] + 1.0, 0.8)
    forts(c, cam, t, ["行市山", "别所山", "茂山"], 1, 0, 0, labels=False)
    forts(c, cam, t, ["神明山", "堂木山", "贱岳", "田上山"], 1, 0, 0, labels=True, lsize=28, pos={"贱岳": "b"})
    # defector
    kd = fio(t, L[1], L[2] + 0.4)
    dashed(c, [LP(cam, "堂木山"), LP(cam, (136.19, 35.565)), LP(cam, "行市山")], ev(t, L[1] + 0.3, 1.6), 6, (200, 200, 200), kd)
    tag(c, "倒戈者送来情报", *LP(cam, (136.205, 35.575)), 34, (80, 80, 80), ev(t, L[1] + 1.0) * kd)
    ax, ay = LP(cam, "大岩山")
    bx, by = LP(cam, "岩崎山")
    fort(c, ax, ay, mix(RED, BLUE, falls), 1, 28, "大岩山", 30, "b")
    fort(c, bx, by, mix(RED, BLUE, ev(t, L[3] + 3.0, 0.8)), 1, 26, "岩崎山", 30, "r")
    arrow(c, [LP(cam, p) for p in RAID_PATH], ev(t, L[2] + 0.5, max(1.5, hit - L[2] - 0.5), eout), 42, BLUE, hi=BLUE_HI)
    tag(c, "4月20日 凌晨", W / 2, 300, 44, (40, 60, 110), fio(t, L[2], L[3] + 2))
    flashes(c, t, [(ax + dx, ay + dy) for dx, dy in ((-40, -20), (-60, 30), (-20, 40), (-70, -5), (10, -40), (30, 20))], fio(t, hit - 0.8, L[4]), 9, 7)
    smoke(c, t, ax - 20, ay, fio(t, hit - 0.6, S["dur"] + 1), 12, 8, 100)
    xmark(c, ax + 50, ay - 50, 26, ev(t, L[3] + 1.4, 0.3))
    tag(c, "中川清秀 战死", ax + 20, ay - 130, 36, (60, 50, 45), ev(t, L[3] + 1.6, 0.4))
    arrow(c, [(bx, by), LP(cam, "木之本")], ev(t, L[3] + 3.2, 1.0), 18, RED, 0.8, dash=[20, 12])
    tag(c, "高山右近 弃砦", bx + 30, by + 90, 32, (120, 50, 40), ev(t, L[3] + 3.6))
    city(c, *LP(cam, "木之本"), "木之本", 1, lpos="b", lsize=30)
    k = ev(t, L[4] + 2.0, 0.6)
    text(c, "开战以来最漂亮的一仗", W / 2, 360, 70, "brush", BLUE_HI, k, stroke=10, shadow=14)
    vignette(c, 0.7)


def s_stay(c, t, S):
    L = S["L"]
    cam = drift(lcam(["内中尾山", "行市山", "大岩山", "贱岳", "田上山", "木之本"], 1.15, sy=830), t, 0.025)
    draw_map(c, LB, cam, "day")
    lake_label(c, cam)
    ax, ay = LP(cam, "大岩山")
    forts(c, cam, t, ["内中尾山", "行市山", "茂山"], 1, 0, 0, labels=True, lsize=28, pos={"行市山": "l", "内中尾山": "l"})
    forts(c, cam, t, ["贱岳", "田上山", "神明山", "堂木山"], 1, 0, 0, labels=True, lsize=28, pos={"贱岳": "b"})
    city(c, *LP(cam, "木之本"), "木之本", 1, lpos="b", lsize=30)
    unit(c, ax, ay, BLUE, 1, 120, 52, "盛政", 32)
    k = ev(t, L[1], 0.6)
    # encirclement
    for n in ["贱岳", "田上山", "木之本", "岩崎山"]:
        dashed(c, [LP(cam, n), (ax, ay)], ev(t, L[1] + 0.4, 1.2), 5, RED_HI, k * 0.9, on=12, off=10)
    pulse = (t * 0.7) % 1
    c.drawCircle(ax, ay, 90 + 140 * pulse, paint(RED_HI, k * (1 - pulse) * 0.8, stroke=5))
    # distance to HQ
    hq = LP(cam, "内中尾山")
    dashed(c, [hq, (ax, ay)], ev(t, L[1] + 1.5, 1.5), 4, BLUE_HI, k * 0.8, on=8, off=10)
    tag(c, "离本阵约 10 公里", (hq[0] + ax) / 2 + 150, (hq[1] + ay) / 2, 34, (40, 60, 110), ev(t, L[1] + 2.5) * fio(t, L[1], L[3]))
    kk = fio(t, L[2], L[3] + 0.5)
    text(c, "打完就回来", W / 2, 330, 84, "brush", BLUE_HI, kk, stroke=10, shadow=14)
    text(c, "就地停下", W / 2, 460, 84, "brush", WHITE, ev(t, L[2] + 2.2) * kk, stroke=10, shadow=14)
    # explanations
    ke = fio(t, L[3], S["dur"] + 1)
    if ke > 0:
        rrect(c, 70, 230, 940, 420, 22, INK, ke * 0.78)
        text(c, "为什么不撤？各书不一", W / 2, 310, 56, "heavy", GOLD, ke)
        tag(c, "贪功说", 290, 420, 46, (90, 70, 50), ev(t, L[4]) * ke)
        text(c, "等援军上来再打一仗", 290, 500, 36, "serif", PAPER, ev(t, L[4] + 0.4) * ke)
        tag(c, "时机说", 790, 420, 46, (90, 70, 50), ev(t, L[4] + 2.6) * ke)
        text(c, "算准秀吉一时回不来", 790, 500, 36, "serif", PAPER, ev(t, L[4] + 3.0) * ke)
        k5 = ev(t, L[5], 0.5) * ke
        text(c, "后世军记：使者五六次", W / 2, 600, 40, "serif", (210, 200, 180), k5)
        stamp(c, "存疑", 880, 600, 56, (220, 70, 50), ev(t, L[5] + 4.0, 0.3), -10)
    vignette(c, 0.6)


def s_agency(c, t, S):
    L = S["L"]
    ink_bg(c, t, (22, 22, 26), 0.3)
    text(c, "委托代理问题", W / 2, 300, 92, "heavy", WHITE, ev(t, L[1] + 0.5), stroke=8, shadow=12)
    text(c, "Jensen & Meckling (1976)", W / 2, 375, 38, "sansm", GOLD, ev(t, L[1] + 1.2))
    k2 = ev(t, L[2], 0.5)
    node(c, 270, 560, 1, "委托人", (60, 70, 100), k2, "主帅 · 柴田胜家", r=330)
    node(c, 810, 560, 1, "代理人", BLUE, ev(t, L[2] + 0.8), "前线 · 佐久间盛政", r=330)
    if k2 > 0:
        arrow(c, [(450, 545), (630, 545)], ev(t, L[2] + 1.0, 0.6), 12, PAPER, k2 * 0.9, glow=False, smooth=False)
        text(c, "授权", 540, 510, 32, "serif", PAPER, k2)
    k3 = ev(t, L[3], 0.5)
    for i, s_ in enumerate(["保住战果", "不让部队暴露"]):
        tag(c, s_, 270, 790 + i * 80, 40, (50, 60, 90), ev(t, L[3] + 0.3 + i * 0.4))
    for i, s_ in enumerate(["眼前战果", "个人功名"]):
        tag(c, s_, 810, 790 + i * 80, 40, (40, 80, 160), ev(t, L[3] + 2.2 + i * 0.4))
    text(c, "≠", W / 2, 860, 120, "heavy", RED_HI, ev(t, L[4] - 0.4), stroke=8)
    k4 = ev(t, L[4] + 0.2, 0.5)
    # info fog over agent
    if k4 > 0:
        fog(c, t, 0.9 * k4, 41, 470, 700, (170, 170, 180))
        text(c, "信息只在前线", 810, 1060, 40, "serif", PAPER, k4, stroke=5)
        ph = ((t - L[4]) * 0.35) % 1
        mx = lerp(300, 780, ph)
        c.drawCircle(mx, 1150, 14, paint(BLUE_HI, k4))
        dashed(c, [(300, 1150), (780, 1150)], 1, 4, PAPER, k4 * 0.5, on=10, off=10, smooth=False)
        text(c, "命令在路上", 540, 1120, 36, "serif", PAPER, k4)
    k5 = ev(t, L[5], 0.6)
    rrect(c, 90, 1240, 900, 170, 20, INK, k5 * 0.75)
    text(c, "一线团队：赢了一单，还想再赢一单", W / 2, 1310, 44, "serif", WHITE, k5)
    text(c, "却忘了后方要的是什么", W / 2, 1375, 44, "serif", GOLD, ev(t, L[5] + 2.5, 0.6))
    vignette(c, 0.55)


def s_trap(c, t, S):
    L = S["L"]
    swap = L[3] - 0.3
    if t < swap:
        ink_bg(c, t, (26, 20, 18), 0.3)
        text(c, "胜利的陷阱", W / 2, 300, 100, "brush", RED_HI, ev(t, 0.2), stroke=10, shadow=14)
        x0, y0, x1, y1 = 140, 1250, 960, 520
        k = ev(t, L[0] + 1.0, 0.6)
        c.drawLine(x0, y0, x1, y0, paint(PAPER, k, stroke=4)); c.drawLine(x0, y0, x0, y1, paint(PAPER, k, stroke=4))
        text(c, "赢下一仗之后的时间 →", x1, y0 + 60, 36, "serif", PAPER, k, "r")
        n = 80
        pr = ev(t, L[1], 4.0)
        gain = [(lerp(x0, x1, i / n), y0 - 520 * (1 - math.exp(-i / n * 4)) * 0.75) for i in range(n + 1)]
        risk = [(lerp(x0, x1, i / n), y0 - 640 * (i / n) ** 2.2) for i in range(n + 1)]
        def pl(pts, colr, a):
            pth = skia.Path(); pth.moveTo(*pts[0])
            for p in pts[1:]:
                pth.lineTo(*p)
            c.drawPath(pth, paint(colr, a, stroke=8))
        if pr > 0:
            pl(cut(gain, pr), BLUE_HI, k)
            text(c, "以为还能多赢的", 940, gain[-1][1] + 60, 38, "serif", BLUE_HI, ev(t, L[1] + 3.5), "r")
        pr2 = ev(t, L[2], 4.0)
        if pr2 > 0:
            pl(cut(risk, pr2), RED_HI, k)
            text(c, "暴露带来的风险", 900, 560, 38, "serif", RED_HI, ev(t, L[2] + 3.5), "r")
        kk = ev(t, L[2] + 4.0, 0.6)
        if kk > 0:
            xs = lerp(x0, x1, 0.62)
            r = skia.Rect.MakeLTRB(xs, y1, x1, y0)
            c.drawRect(r, paint((200, 50, 40), kk * 0.18))
            text(c, "舍不得收手的几个小时", (xs + x1) / 2, y0 - 40, 34, "serif", WHITE, kk)
    else:
        cam = drift(lcam(["行市山", "大岩山", "贱岳", "田上山", "神明山"], 1.15, sy=830), t - swap, 0.03)
        draw_map(c, LB, cam, "day")
        lake_label(c, cam)
        ax, ay = LP(cam, "大岩山")
        forts(c, cam, t, ["贱岳", "田上山", "神明山", "堂木山", "岩崎山"], 1, 0, 0, labels=False)
        forts(c, cam, t, ["行市山", "茂山"], 1, 0, 0, labels=False)
        unit(c, ax, ay, BLUE, 1, 120, 52, "盛政", 32)
        dashed(c, [LP(cam, p) for p in RAID_PATH[::-1]], 1, 5, BLUE_HI, 0.7)
        k = ev(t, swap + 1.0, 0.8)
        g = (math.sin(t * 5) + 1) / 2
        c.drawCircle(ax - 10, ay + 10, 100, paint((255, 60, 40), k * (0.4 + 0.3 * g), stroke=14, blur=8))
        tag(c, "整个柴田军的侧面", ax, ay + 150, 40, (170, 40, 30), k)
        text(c, "时间站在谁那边？", W / 2, 330, 84, "brush", WHITE, ev(t, swap + 0.3), stroke=10, shadow=14)
    vignette(c, 0.6)


# ======================= RETURN & BATTLE =======================
NIWA = [(136.03, 35.43), (136.0615, 35.4617), (136.10, 35.485), (136.150, 35.505), (136.1745, 35.5035), (136.1927, 35.5061)]


def s_niwa(c, t, S):
    L = S["L"]
    cam = drift(lcam(["海津", "贱岳", "大岩山", (136.03, 35.43), "行市山"], 1.12, sy=860), t, 0.02)
    draw_map(c, LB, cam, "day")
    biwa_label(c, cam, LP, (136.07, 35.415), 0.7)
    lake_label(c, cam, 0.7, size=26)
    city(c, *LP(cam, "海津"), "海津", 1, lpos="l", lsize=32)
    # boats
    kb = ev(t, 0.3, 0.5)
    for i in range(7):
        f = clamp(ev(t, 0.4 + i * 0.15, L[1] + 0.6, eout))
        p, ang = at([LP(cam, NIWA[0]), LP(cam, NIWA[1])], max(0.001, f))
        bx, by = p[0] - 30 + (i % 3) * 30, p[1] + (i // 3) * 28 - 30
        c.drawOval(skia.Rect.MakeXYWH(bx - 18, by - 6, 36, 12), paint(RED, kb))
    arrow(c, [LP(cam, p) for p in NIWA[1:]], ev(t, L[1] + 0.8, 3.0, eout), 32, RED, hi=RED_HI)
    tag(c, "丹羽长秀 渡湖", *LP(cam, (136.06, 35.50)), 38, RED, ev(t, 0.8))
    sx, sy = LP(cam, "贱岳")
    flick = 0.5 + 0.5 * math.sin(t * 14) if t < L[1] + 3.5 else 1
    fort(c, sx, sy, RED, (0.5 + 0.5 * flick) if t < L[1] + 3.8 else 1, 30, "贱岳", 34, "b", pulse=(t % 1) * fio(t, L[1] + 3.8, L[2] + 1))
    tag(c, "桑山重晴 欲弃砦", sx, sy - 120, 32, (120, 50, 40), fio(t, L[1] + 1.0, L[1] + 4.2))
    tag(c, "守住！", sx, sy - 120, 44, RED, ev(t, L[1] + 4.2, 0.3))
    ax, ay = LP(cam, "大岩山")
    unit(c, ax, ay, BLUE, 1, 100, 46, "盛政", 30)
    k = ev(t, L[2] + 0.3, 0.4)
    if k > 0:
        c.drawLine(sx + 20, sy - 10, ax - 50, ay + 5, paint(RED_HI, k * 0.9, stroke=5))
        text(c, "一颗钉子", W / 2, 330, 90, "brush", WHITE, k, stroke=10, shadow=14)
    vignette(c, 0.6)


def s_decide(c, t, S):
    L = S["L"]
    cam = drift(rcam(["大垣", "木之本", "余吴湖", "关原"], 1.3, sy=830), t, 0.03)
    draw_map(c, RB, cam, "day")
    region_labels(c, cam, ["大垣", "木之本"], 1, 40, {"木之本": "l"})
    x, y = RP(cam, "大垣")
    pulse = (t * 0.9) % 1
    c.drawCircle(x, y, 40 + 140 * pulse, paint(RED_HI, 1 - pulse, stroke=7))
    ax, ay = RP(cam, (136.2037, 35.5153))
    unit(c, ax + 40, ay - 10, BLUE, 1, 70, 32)
    k = ev(t, L[1], 0.5)
    c.drawCircle(ax + 40, ay - 10, 70, paint((255, 220, 120), k, stroke=5))
    tag(c, "离开了工事", ax + 40, ay - 110, 38, (40, 60, 110), k)
    text(c, "不是败局", W / 2, 320, 90, "brush", WHITE, ev(t, L[0] + 1.5), stroke=10, shadow=14)
    text(c, "是机会", W / 2, 450, 110, "brush", RED_HI, ev(t, L[0] + 2.4), stroke=10, shadow=14)
    kk = ev(t, L[1] + 2.5, 0.5)
    rrect(c, 130, 1180, 820, 130, 18, INK, kk * 0.75)
    text(c, "在他撤回去之前赶到", W / 2, 1265, 58, "serif", GOLD, kk)
    vignette(c, 0.65)


def s_march(c, t, S):
    L = S["L"]
    swap = L[5] - 0.3
    if t < swap:
        k1 = rcam(["大垣", "关原"], 2.2, sy=860)
        k2 = rcam(["大垣", "木之本", "关原", "长浜"], 1.15, sy=860)
        k3 = rcam(["木之本", "余吴湖", (136.30, 35.45)], 1.8, sy=860)
        cam = campath(t, [(0, k1), (L[2], k2), (L[4], k2), (swap, k3)])
        draw_map(c, RB, cam, "night")
        prog = ev(t, L[0], swap - L[0] - 0.5, lambda x: x)
        torches_route(c, cam, t, prog, n=110, s=1.1)
        pts = catmull([RP(cam, q) for q in ROUTE], 10)
        p, ang = at(pts, max(prog, 0.002))
        radial(c, p[0], p[1], 180, (255, 130, 50), 0.5)
        arrow(c, [RP(cam, q) for q in ROUTE], prog, 26, RED, 0.55, glow=True)
        region_labels(c, cam, ["大垣", "木之本", "长浜", "关原"], 1, 38, {"木之本": "l", "长浜": "l"})
        # villages torches (legend)
        kv = fio(t, L[2], L[3] + 1)
        for i in range(12):
            f = i / 11
            q, _ = at(pts, f)
            torch(c, q[0] + 50 * math.sin(i * 2.3), q[1] + 40 * math.cos(i * 1.7) - 50, t, kv * 0.9, seed=100 + i, s=0.9)
        tag(c, "传说", W - 150, 300, 40, (120, 90, 40), kv)
        hh = 14 + 5 * prog
        text(c, f"{int(hh):02d}:{int((hh % 1) * 60):02d}", W - 70, 1330, 70, "heavy", GOLD, 0.95, "r", stroke=8)
        text(c, f"{52 * prog:4.1f} 公里", 70, 1330, 60, "heavy", WHITE, 0.95, "l", stroke=8)
        k = fio(t, L[4], swap)
        text(c, "十三里 ≈ 五十二公里", W / 2, 330, 72, "brush", WHITE, k, stroke=10, shadow=14)
        text(c, "通说 · 五个小时", W / 2, 440, 66, "brush", (255, 170, 110), ev(t, L[4] + 2.0) * k, stroke=10, shadow=14)
        k0 = fio(t, L[1] - 0.5, L[3] + 0.5)
        text(c, "以迂为直", W / 2, 330, 90, "brush", (255, 210, 150), 0, stroke=10)
        kk = fio(t, L[1], L[2])
        text(c, "沿路：备火把 · 备饭食", W / 2, 330, 64, "brush", WHITE, kk, stroke=10, shadow=14)
        embers(c, t, 40, 51, 0.5)
    else:
        cam = drift(lcam(["行市山", "大岩山", "木之本", "贱岳", "田上山"], 1.1, sy=820), t - swap, 0.03)
        draw_map(c, LB, cam, "night")
        lake_label(c, cam, 0.6)
        kx, ky = LP(cam, "木之本")
        R_ = Rng(77)
        for i in range(90):
            xx = kx + R_(-260, 220); yy = ky + R_(-60, 260)
            torch(c, xx, yy, t, ev(t, swap + R_(0, 2.5), 0.3), seed=i, s=0.8)
        ax, ay = LP(cam, "大岩山")
        unit(c, ax, ay, BLUE, 1, 110, 48, "盛政", 30)
        k = ev(t, L[5] + 2.2, 0.6)
        text(c, "秀吉，已经回来了", W / 2, 340, 88, "brush", (255, 200, 140), k, stroke=10, shadow=16)
    vignette(c, 0.75)


def s_doubt(c, t, S):
    L = S["L"]
    ink_bg(c, t, (22, 22, 26), 0.35)
    text(c, "史料存疑", W / 2, 290, 84, "heavy", GOLD, ev(t, 0.2), stroke=8)
    k = ev(t, L[1], 0.5)
    text(c, "52 公里 ÷ 5 小时", W / 2, 430, 70, "heavy", WHITE, k, stroke=8)
    text(c, "≈ 10.4 公里 / 小时", W / 2, 520, 70, "heavy", RED_HI, ev(t, L[1] + 1.2), stroke=8)
    kb = ev(t, L[1] + 2.0, 0.6)
    x0 = 180
    for i, (lab, v, cl) in enumerate([("通说要求", 10.4, RED), ("披甲步行（一般）", 4.5, (120, 120, 120))]):
        y = 640 + i * 110
        text(c, lab, 110, y + 45, 36, "serif", PAPER, kb, "l")
        w = 340 * v / 10.4 * ev(t, L[1] + 2.2 + i * 0.4, 0.8)
        rrect(c, 470, y + 10, w, 50, 8, cl, kb)
        text(c, f"{v} km/h", 485 + w, y + 48, 34, "sansm", PAPER, kb, "l")
    text(c, "（示意）", 900, 880, 30, "serif", (170, 160, 150), kb)
    # split column
    k3 = ev(t, L[2], 0.5)
    if k3 > 0:
        y = 1040
        c.drawLine(120, y, 960, y, paint(PAPER, k3 * 0.4, stroke=3))
        text(c, "大垣", 120, y + 60, 34, "serif", PAPER, k3, "l"); text(c, "木之本", 960, y + 60, 34, "serif", PAPER, k3, "r")
        pr = ev(t, L[2] + 0.3, 6.0, lambda x: x)
        c.drawCircle(lerp(120, 960, pr), y - 30, 18, paint(RED_HI, k3))
        text(c, "骑马先头", lerp(120, 960, pr), y - 70, 30, "serif", RED_HI, k3)
        for i in range(24):
            f = pr * (0.82 - i * 0.025)
            if f > 0:
                c.drawCircle(lerp(120, 960, f), y + 10, 9, paint(RED, k3 * 0.85))
        text(c, "后队连夜陆续赶上", W / 2, y + 140, 40, "serif", WHITE, ev(t, L[2] + 3.5), stroke=5)
    k4 = ev(t, L[3], 0.5)
    tag(c, "出发：正午？", 330, 1300, 40, (70, 70, 80), k4 * fio(t, L[3], L[4] + 0.2))
    tag(c, "午后两点？", 750, 1300, 40, (70, 70, 80), ev(t, L[3] + 1.0) * fio(t, L[3], L[4] + 0.2))
    k5 = ev(t, L[4], 0.5)
    text(c, "他算：秀吉明天也回不来", W / 2, 1290, 48, "serif", BLUE_HI, k5, stroke=5)
    text(c, "实际：秀吉当晚就到了", W / 2, 1370, 48, "serif", RED_HI, ev(t, L[4] + 2.2), stroke=5)
    vignette(c, 0.55)


def quote_card(c, t, S, orig, src, plain, bg="lake"):
    ink_bg(c, t, (16, 18, 22), 0.45)
    embers(c, t, 30, 61, 0.35, color=(255, 200, 140))
    size = 96
    parts = [p for p in orig.replace("。", "").split("，") if p]
    cols = parts
    xs = [W / 2 + 95, W / 2 - 95] if len(cols) == 2 else [W / 2]
    y0 = 220
    for j, colstr in enumerate(cols):
        for i, ch in enumerate(colstr):
            k = ev(t, 0.3 + (j * len(cols[0]) + i) * 0.12, 0.5)
            text(c, ch, xs[j], y0 + size * 1.02 * (i + 0.88), size, "heavy", WHITE, k, stroke=8, shadow=16)
    by = y0 + size * 1.02 * max(len(x) for x in cols) + 50
    k2 = ev(t, 1.6, 0.6)
    # seal-like source
    text(c, src, W / 2, by + 30, 46, "serif", GOLD, k2)
    c.drawLine(W / 2 - 200, by + 70, W / 2 + 200, by + 70, paint(RED, k2, stroke=3))
    k3 = ev(t, S["E"][0] - 0.5 if S["E"] else 2.5, 0.6)
    for i, ln in enumerate(wrap(plain, 50, 900)):
        text(c, ln, W / 2, by + 145 + i * 70, 50, "serif", WHITE, k3, stroke=5)
    vignette(c, 0.6)


def s_quote_yu(c, t, S):
    quote_card(c, t, S, "以迂為直，以患為利。", "——《孫子·軍爭》", "把绕远变成近路，把不利变成有利。")
    k = ev(t, S["L"][1], 0.5)
    if k > 0:
        rrect(c, 80, 1300, 920, 150, 18, INK, k * 0.8)
        text(c, "大水挡路 = 绕远", W / 2, 1360, 44, "serif", PAPER, k)
        text(c, "盛政奇袭 = 祸患 → 秀吉的筹码", W / 2, 1424, 44, "serif", GOLD, ev(t, S["L"][1] + 2.0), stroke=4)


BATTLE_CAM_PTS = ["行市山", "大岩山", "贱岳", "茂山", "木之本", "田上山"]
SHOMASA = (136.1835, 35.5115)


def s_retreat(c, t, S):
    L = S["L"]
    cam = drift(lcam(BATTLE_CAM_PTS, 1.12, sy=820), t, 0.04)
    dawn = ev(t, L[1], 6.0)
    draw_map(c, LB, cam, "night", mode2="day", k2=0.15 + 0.7 * dawn)
    lake_label(c, cam, 0.7)
    forts(c, cam, t, ["行市山", "别所山"], 1, 0, 0, labels=True, lsize=28, pos={"行市山": "l", "别所山": "l"})
    fort(c, *LP(cam, "茂山"), LBLUE, 1, 24, "茂山 · 前田", 28, "r")
    forts(c, cam, t, ["田上山", "神明山", "堂木山"], 1, 0, 0, labels=False)
    city(c, *LP(cam, "木之本"), "木之本", 1, lpos="b", lsize=30)
    sx, sy_ = LP(cam, "贱岳")
    hq = ev(t, L[2] - 0.3, 0.6)
    fort(c, sx, sy_, RED, 1, 30 + 8 * hq, "贱岳" + (" · 秀吉本阵" if hq > 0.5 else ""), 30, "b", pulse=(t % 1) * fio(t, L[2], L[3]))
    # Morimasa retreats
    rp = ev(t, L[0] + 0.5, 6.0, eout)
    path = [LP(cam, p) for p in [(136.2037, 35.5153), (136.192, 35.525), (136.186, 35.540), (136.178, 35.555)]]
    q, _ = at(catmull(path), rp * 0.75)
    unit(c, q[0], q[1], BLUE, 1, 100, 44, "盛政", 30)
    arrow(c, path, rp, 26, BLUE, 0.85, dash=[26, 14])
    gx, gy = LP(cam, SHOMASA)
    unit(c, gx, gy, BLUE, 1 - ev(t, L[4] + 2.0, 1.0), 96, 44, "胜政 断后", 30)
    # red waves
    kk = ev(t, L[1], 0.4)
    for i, src in enumerate([(136.215, 35.505), (136.205, 35.498), (136.2223, 35.5023)]):
        arrow(c, [LP(cam, src), LP(cam, (136.200, 35.508 + i * 0.002)), (gx + 30, gy + 10 * i)], ev(t, L[1] + 0.3 + i * 0.4, 2.5, eout), 30, RED, kk, hi=RED_HI)
    arrow(c, [(sx, sy_), (gx + 20, gy - 10)], ev(t, L[3] + 0.2, 1.0), 34, RED, ev(t, L[3]), hi=RED_HI)
    kb = fio(t, L[3] + 0.2, S["dur"] + 1)
    flashes(c, t, [(gx + dx, gy + dy) for dx, dy in ((-50, -30), (40, 30), (-20, 50), (60, -20), (0, -50), (70, 40), (-70, 20))], kb, 14, 8, size=9)
    smoke(c, t, gx, gy, kb, 16, 15, 120, size=50)
    xmark(c, gx, gy, 30, ev(t, L[5] + 1.6, 0.3))
    tag(c, "4月21日 凌晨", W / 2, 300, 44, (120, 40, 30), fio(t, L[1], L[3]))
    text(c, "退，比进难得多", W / 2, 330, 84, "brush", WHITE, fio(t, L[0] + 1.0, L[1]), stroke=10, shadow=14)
    embers(c, t, 50, 71, kb * 0.8)
    vignette(c, 0.7)


def s_maeda(c, t, S):
    L = S["L"]
    cam = drift(lcam(["内中尾山", "行市山", "大岩山", "贱岳", "木之本", "神明山"], 1.1, sy=820), t, 0.03)
    draw_map(c, LB, cam, "day")
    lake_label(c, cam, 0.7)
    leave = L[0] + 1.6
    collapse = L[5] + 0.3
    kc = ev(t, collapse, 3.0)
    forts(c, cam, t, ["田上山", "神明山", "堂木山", "岩崎山", "大岩山"], 1, 0, 0, labels=False)
    fort(c, *LP(cam, "贱岳"), RED, 1, 34, "秀吉本阵", 28, "b")
    fort(c, *LP(cam, "内中尾山"), mix(BLUE, (80, 80, 90), kc), 1, 28, "胜家本阵", 28, "l")
    mx, my = LP(cam, "茂山")
    mp = ev(t, leave, 4.0, ein)
    tx, ty = LP(cam, (136.222, 35.582))
    ux, uy = lerp(mx, tx, mp), lerp(my, ty, mp)
    if mp > 0:
        arrow(c, [(mx, my), (lerp(mx, tx, .5) + 40, lerp(my, ty, .5)), (tx, ty)], mp, 26, LBLUE, 0.9)
    unit(c, ux, uy, LBLUE, 1, 110, 48, "前田利家", 32)
    if t < leave + 0.3:
        c.drawCircle(mx, my, 90 + 8 * math.sin(t * 6), paint((255, 230, 150), ev(t, L[0] + 0.4, 0.4), stroke=6))
    # hinge
    kh = fio(t, L[2], L[4] + 0.5)
    gx, gy = LP(cam, (136.178, 35.553))
    hx, hy = LP(cam, "内中尾山")
    if kh > 0:
        c.drawLine(gx, gy, mx, my, paint(GOLD, kh, stroke=6)); c.drawLine(mx, my, hx, hy, paint(GOLD, kh, stroke=6))
        c.drawCircle(mx, my, 26, paint(GOLD, kh, stroke=6))
        tag(c, "铰链", mx + 110, my + 10, 40, (150, 110, 30), kh)
    kgap = ev(t, L[3] + 0.5, 0.6) * (1 - kc)
    if kgap > 0:
        c.drawLine(gx, gy, hx, hy, paint((255, 60, 40), kgap * (0.6 + 0.4 * math.sin(t * 8)), stroke=10, blur=4))
        text(c, "退路可能被切断", W / 2, 340, 72, "brush", RED_HI, kgap, stroke=10, shadow=14)
    unit(c, gx, gy, BLUE, 1 - kc * 0.8, 100, 44, "盛政", 30)
    # other units leave
    for i, (nm, p0) in enumerate([("不破", (136.165, 35.585)), ("金森", (136.160, 35.575))]):
        k = ev(t, L[4] + 1.6 + i * 0.5, 2.5, ein)
        a0, b0 = LP(cam, p0), LP(cam, (p0[0] - 0.01, p0[1] + 0.03))
        unit(c, lerp(a0[0], b0[0], k), lerp(a0[1], b0[1], k), BLUE, ev(t, L[4], 0.5) * (1 - k * 0.7), 80, 36, nm, 28)
    # collapse: blue particles flowing north
    if kc > 0:
        R_ = Rng(91)
        for i in range(160):
            sx0, sy0 = R_(gx - 200, gx + 260), R_(gy - 80, gy + 300)
            sp = R_(0.5, 1.4)
            f = ((t - collapse) * 0.18 * sp + R_(0, 1)) % 1
            c.drawCircle(sx0 + f * 30, sy0 - f * 520, 6, paint(BLUE_HI, kc * (1 - f) * 0.9))
        for i in range(4):
            arrow(c, [LP(cam, (136.205 + i * 0.006, 35.508)), LP(cam, (136.185 + i * 0.008, 35.560 + i * 0.006))], ev(t, collapse + 0.3 + i * 0.3, 2.5), 30, RED, kc, hi=RED_HI)
        text(c, "全线崩溃", W / 2, 340, 110, "brush", WHITE, kc, stroke=12, shadow=18)
    # music stop beat flash
    kf = fio(t, leave - 0.1, leave + 0.9, 0.15)
    if kf > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(INK, kf * 0.35))
        text(c, "转身走了", W / 2, 340, 100, "brush", LBLUE, kf, stroke=10, shadow=16)
    text(c, "转身走了", W / 2, 340, 100, "brush", LBLUE, fio(t, leave + 0.9, L[2], 0.2), stroke=10, shadow=16)
    vignette(c, 0.65)


def s_threshold(c, t, S):
    L = S["L"]
    ink_bg(c, t, (20, 22, 26), 0.3)
    text(c, "阈值模型", W / 2, 290, 92, "heavy", WHITE, ev(t, L[1]), stroke=8)
    text(c, "Granovetter (1978)", W / 2, 360, 38, "sansm", GOLD, ev(t, L[1] + 0.8))
    gx0, gy0, sp = 180, 470, 80
    # phases
    p_full = (L[3], L[4] - 0.3)      # full cascade 0..99
    p_break = (L[4], L[5] - 0.3)     # replaced 1 -> stop
    p_block = (L[6], S["dur"])        # block leaves
    kgrid = ev(t, L[2], 0.6)
    for i in range(100):
        r, cidx = divmod(i, 10)
        x, y = gx0 + cidx * sp, gy0 + r * sp
        thr = i
        ran = False
        if p_full[0] <= t < p_full[1]:
            ran = (t - p_full[0] - 0.8) * 9 >= thr
        elif p_break[0] <= t < p_break[1]:
            ran = thr == 0 and t > p_break[0] + 1.0
            if i == 1:
                thr = 2
        elif t >= p_block[0]:
            tb = t - p_block[0]
            # 20 visible at once (block), then cascade from 20
            ran = (i < 20 and tb > 1.0) or (tb > 2.0 and (tb - 2.0) * 10 >= thr - 20)
        ccol = RED_HI if ran else (90, 100, 120)
        kk = kgrid
        if i == 1 and p_break[0] <= t < p_break[1]:
            c.drawCircle(x, y, 32, paint(GOLD, kk, stroke=4))
        c.drawCircle(x, y + (-10 if ran else 0), 26, paint(ccol, kk))
        if ev(t, L[2] + 1.0) > 0:
            text(c, str(thr), x, y + 10 + (-10 if ran else 0), 26, "sans", INK if ran else WHITE, kk)
    if p_full[0] <= t < p_full[1]:
        text(c, "门槛 0 的人先动 → 一个带一个", W / 2, 1330, 46, "serif", WHITE, 1, stroke=5)
    if p_break[0] <= t < p_break[1]:
        text(c, "换掉门槛为 1 的那个人", W / 2, 1330, 46, "serif", GOLD, 1, stroke=5)
        text(c, "→ 什么都不会发生", W / 2, 1400, 46, "serif", WHITE, ev(t, p_break[0] + 2.0), stroke=5)
    if L[5] <= t < L[6]:
        text(c, "关键在链条最前面那几环", W / 2, 1360, 50, "serif", GOLD, ev(t, L[5]), stroke=5)
    if t >= p_block[0]:
        tb = t - p_block[0]
        if tb > 0.8:
            c.drawRect(skia.Rect.MakeXYWH(gx0 - 45, gy0 - 45, 10 * sp + 10, 2 * sp + 10), paint(LBLUE, 1, stroke=6))
            tag(c, "一支友军整建制撤离", W / 2, 420 + 0 * gy0, 38, (50, 110, 140), ev(t, p_block[0] + 0.8))
        txt = "只要每个人都相信：别人要跑了"
        if t >= L[8] if len(L) > 8 else False:
            text(c, txt, W / 2, 1360, 50, "serif", GOLD, ev(t, L[8]), stroke=5)
    vignette(c, 0.5)


def s_why_maeda(c, t, S):
    L = S["L"]
    ink_bg(c, t, (20, 24, 30), 0.35)
    text(c, "前田利家为什么撤？", W / 2, 300, 76, "heavy", LBLUE, ev(t, 0.2), stroke=8)
    stamp(c, "无定论", 850, 400, 52, (220, 70, 50), ev(t, L[0] + 1.6, 0.3), -8)
    items = [("说法一", "去年冬天当使者时，已与秀吉有约", L[1]),
             ("说法二", "秀吉旧交 · 胜家部下 · 夹缝中自保", L[2]),
             ("前田家记录", "为防备北边的上杉", L[2] + 6.0)]
    for i, (h, b, t0) in enumerate(items):
        k = ev(t, t0, 0.5)
        y = 560 + i * 230
        rrect(c, 90, y - 70, 900, 180, 18, INK, k * 0.75)
        rrect(c, 90, y - 70, 900, 180, 18, LBLUE, k * 0.5, stroke=3)
        text(c, h, 140, y, 44, "heavy", LBLUE, k, "l")
        for j, ln in enumerate(wrap(b, 42, 820)):
            text(c, ln, 140, y + 62 + j * 52, 42, "serif", WHITE, k, "l")
    k = ev(t, L[3], 0.5)
    text(c, "结果一样：战后成为秀吉麾下大名", W / 2, 1330, 50, "serif", GOLD, k, stroke=5)
    vignette(c, 0.55)


def s_kitanosho(c, t, S):
    L = S["L"]
    cam = drift(rcam(["北之庄", "木之本", "长浜"], 1.3, sy=820), t, 0.03)
    draw_map(c, RB, cam, "day")
    region_labels(c, cam, ["木之本"], 1, 38, {"木之本": "l"})
    x, y = RP(cam, "北之庄")
    arrow(c, [RP(cam, (136.17, 35.60)), RP(cam, (136.08, 35.80)), (x - 30, y + 30)], ev(t, 0.2, 2.5), 26, BLUE, 0.85)
    arrow(c, [RP(cam, "木之本"), RP(cam, (136.20, 35.75)), (x + 20, y + 60)], ev(t, 1.2, 3.0), 38, RED, hi=RED_HI)
    city(c, x, y, "北之庄", 1, lsize=40)
    kf = ev(t, L[0] + 3.5, 1.0)
    if kf > 0:
        radial(c, x, y, 220, (255, 110, 40), kf * 0.6)
        smoke(c, t, x, y - 60, kf, 14, 23, 90, (110, 100, 95), 50, 40)
        embers(c, t, 50, 25, kf, (x - 150, y - 300, x + 150, y + 40))
    tag(c, "4月24日 城破", x, y + 110, 40, (120, 40, 30), ev(t, L[0] + 3.0))
    vignette(c, 0.65)


SEVEN = ["福岛正则", "加藤清正", "加藤嘉明", "平野长泰", "胁坂安治", "糟屋武则", "片桐且元"]


def s_seven(c, t, S):
    L = S["L"]
    ink_bg(c, t, (26, 20, 16), 0.35)
    k0 = ev(t, L[1] + 3.5, 0.6)
    text(c, "贱岳七本枪", W / 2, 300, 104, "brush", GOLD, k0, stroke=10, shadow=16)
    for i, nm in enumerate(SEVEN):
        k = ev(t, L[1] + i * 0.45, 0.4)
        x = W / 2 + (3 - i) * 125
        vtext(c, nm, x, 380, 70, "brush", WHITE, k, stroke=6, shadow=10)
    k2 = ev(t, L[3], 0.5)
    for i, nm in enumerate(["樱井佐吉", "石川兵助"]):
        x = W / 2 + (0.5 - i) * 250
        vtext(c, nm, x, 820, 60, "brush", (200, 190, 170), ev(t, L[3] + 0.5 + i * 0.5), stroke=6)
    if k2 > 0:
        tag(c, "同样得到感状重赏", W / 2, 1150, 38, (90, 70, 50), k2)
    k1 = ev(t, L[2], 0.5)
    rrect(c, 80, 1230, 920, 180, 18, INK, k1 * 0.8)
    text(c, "称号初见：甫庵《太阁记》（江户初年）", W / 2, 1300, 42, "serif", PAPER, k1)
    text(c, "同时代《柴田合战记》：记了九人", W / 2, 1370, 42, "serif", GOLD, ev(t, L[3] + 3.0))
    stamp(c, "七 · 为了顺口", 800, 760, 50, (220, 70, 50), ev(t, L[4], 0.3), -10)
    vignette(c, 0.55)


def s_newrule(c, t, S):
    L = S["L"]
    ink_bg(c, t, (24, 20, 18), 0.35)
    text(c, "一条新规矩", W / 2, 300, 96, "brush", WHITE, ev(t, 0.3), stroke=10, shadow=14)
    steps = [("出身不高", 1150), ("战功", 930), ("地位", 710)]
    for i, (s_, y) in enumerate(steps):
        k = ev(t, L[1] + 0.5 + i * 1.6, 0.5)
        x = 110 + i * 240
        rrect(c, x, y, 380, 110, 10, mix((80, 60, 40), RED, i / 2), k)
        text(c, s_, x + 190, y + 75, 52, "serif", WHITE, k)
        if i:
            arrow(c, [(x - 20, y + 200), (x + 60, y + 120)], k, 12, GOLD, k, glow=False, smooth=False)
    k = ev(t, L[2], 0.6)
    rrect(c, 80, 1300, 920, 120, 18, INK, k * 0.8)
    text(c, "织田老臣里，再无人能与秀吉争", W / 2, 1380, 48, "serif", GOLD, k)
    vignette(c, 0.55)


def s_lake(c, t, S):
    L = S["L"]
    swap = L[1] - 0.3
    if t < swap or t > L[2] + 1.5:
        cam = lcam(["余吴湖", "贱岳", "大岩山"], 1.6, sy=820)
        cam = Cam(cam.cx, cam.cy, cam.z * (1 + 0.04 * t / 10), cam.sy)
        draw_map(c, LB, cam, "day")
        x, y = LP(cam, "余吴湖")
        for i in range(5):
            ph = (t * 0.15 + i / 5) % 1
            c.drawOval(skia.Rect.MakeXYWH(x - 40 - 160 * ph, y - 20 - 60 * ph, 80 + 320 * ph, 40 + 120 * ph), paint((180, 210, 230), 0.3 * (1 - ph), stroke=2))
        lake_label(c, cam, 0.85, size=40)
        fog(c, t, 0.3, 81, 300, 1300)
        text(c, "让对手先动", W / 2, 340, 100, "brush", WHITE, ev(t, L[0] + 2.5) * (1 - ev(t, swap - 0.3, 0.3)), stroke=10, shadow=14)
        if t > L[2] + 1.5:
            text(c, "备好回来的路", W / 2, 340, 100, "brush", GOLD, ev(t, L[2] + 1.6), stroke=10, shadow=14)
    else:
        cam = drift(rcam(["大垣", "木之本", "关原", "长浜"], 1.15, sy=830), t - swap, 0.02)
        draw_map(c, RB, cam, "day")
        pts = catmull([RP(cam, q) for q in ROUTE], 10)
        for i in range(9):
            q, _ = at(pts, i / 8)
            k = ev(t, swap + 0.6 + i * 0.25, 0.4)
            c.drawCircle(q[0], q[1], 16, paint(GOLD, k)); c.drawCircle(q[0], q[1], 30, paint(GOLD, k * 0.5, stroke=3))
        dashed(c, pts, ev(t, swap + 0.6, 2.2), 6, GOLD, 0.9, smooth=False)
        region_labels(c, cam, ["大垣", "木之本", "长浜"], 1, 38, {"木之本": "l", "长浜": "l"})
        tag(c, "联络与补给预先布好（一说）", W / 2, 1300, 40, (110, 85, 40), ev(t, swap + 1.5))
    vignette(c, 0.6)


def s_quote_zhi(c, t, S):
    quote_card(c, t, S, "善戰者，致人而不致於人。", "——《孫子·虛實》", "会打仗的人调动敌人，而不被敌人调动。")
    k = ev(t, S["L"][1], 0.5)
    if k > 0:
        rrect(c, 80, 1300, 920, 150, 18, INK, k * 0.8)
        text(c, "盛政：被一场小胜调动", W / 2, 1360, 44, "serif", BLUE_HI, k)
        text(c, "秀吉：被大雨调动，却备好了回来的路", W / 2, 1424, 42, "serif", RED_HI, ev(t, S["L"][1] + 2.5))


def s_takeaway(c, t, S):
    L = S["L"]
    ink_bg(c, t, (18, 16, 14), 0.4)
    embers(c, t, 40, 91, 0.5)
    lines1 = ["对手最大的破绽，", "常常是他刚赢下一小仗之后，", "舍不得收手的那几个小时。"]
    for i, ln in enumerate(lines1):
        text(c, ln, W / 2, 520 + i * 100, 62, "serif", WHITE if i < 2 else GOLD, ev(t, 0.3 + i * 0.8, 0.6), stroke=6, shadow=10)
    k = ev(t, L[1], 0.6)
    c.drawLine(W / 2 - 220, 880, W / 2 + 220, 880, paint(RED, k, stroke=4))
    for i, ln in enumerate(["你刚赢一小仗的时候，", "也正是你最危险的时候。"]):
        text(c, ln, W / 2, 1000 + i * 96, 58, "serif", RED_HI if i else WHITE, ev(t, L[1] + 0.8 + i * 1.2, 0.6), stroke=6)
    vignette(c, 0.55)


def s_next(c, t, S):
    L = S["L"]
    ink_bg(c, t, (14, 14, 18), 0.3)
    k = ev(t, 0.3, 0.8)
    text(c, "拿下北陆之后", W / 2, 520, 56, "serif", PAPER, k)
    text(c, "第一次遇上一个怎么也打不赢的人", W / 2, 610, 56, "serif", PAPER, ev(t, 1.2, 0.8))
    k2 = ev(t, L[1] - 0.2, 0.8)
    text(c, "下一集", W / 2, 800, 50, "serif", GOLD, k2)
    for i, ch in enumerate("德川家康"):
        kk = ev(t, L[1] + 0.2 + i * 0.2, 0.6, eout)
        text(c, ch, W / 2 + (i - 1.5) * 210, 1060, 210, "brush", WHITE, kk, stroke=14, shadow=24)
    text(c, "从无名小卒到天下人", W / 2, 1300, 40, "serif", GOLD, ev(t, L[1] + 1.5), spacing=0.25)
    vignette(c, 0.6)


SCENE_FN = {k[2:]: v for k, v in globals().items() if k.startswith("s_") and callable(v)}


def cover(c, t=3.0):
    c.clear(col(INK))
    cam = rcam(["大垣", "木之本", "余吴湖", "关原"], 1.2, sy=1000)
    draw_map(c, RB, cam, "night")
    torches_route(c, cam, t, 1.0, n=120, s=1.35)
    for i in range(0, 9):
        p, _ = at(catmull([RP(cam, q) for q in ROUTE], 10), i / 8)
        radial(c, p[0], p[1], 150, (255, 120, 40), 0.25)
    region_labels(c, cam, ["大垣", "木之本"], 1, 44, {"木之本": "l"})
    embers(c, t, 80, 11, 0.7)
    vignette(c, 0.85)
    vgrad(c, 0, 760, INK, 0.85, INK, 0.0)
    vgrad(c, 1350, H, INK, 0.0, INK, 0.9)
    text(c, "从无名小卒到天下人", W / 2, 150, 44, "serif", GOLD, 1, spacing=0.25)
    text(c, "贱岳之战", W / 2, 400, 230, "brush", WHITE, 1, stroke=14, shadow=30)
    c.drawLine(W / 2 - 320, 470, W / 2 + 320, 470, paint(RED, 1, stroke=6))
    text(c, "打赢了还不撤", W / 2, 600, 92, "heavy", (255, 200, 150), 1, stroke=10, shadow=16)
    text(c, "五个小时 · 五十二公里", W / 2, 1450, 84, "heavy", WHITE, 1, stroke=10, shadow=16)
    text(c, "秀吉怎样把对手钓出来吃掉", W / 2, 1580, 58, "serif", GOLD, 1, stroke=8)
