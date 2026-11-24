# -*- coding: utf-8 -*-
"""Roman scenes: coin chain of the 'five good emperors' + Commodus; Caesar -> Kaiser/Tsar."""
import math
import skia
from engine import *
from shapes import profile_path, beard_path, laurel

GOLD_COIN = ((250, 226, 150), (196, 150, 64), (120, 86, 30))
RUST = ((150, 110, 90), (96, 66, 52), (52, 36, 30))

def coin(c, cx, cy, r, legend, beard=False, rust=0.0, crack=0.0, alpha=1.0, flip=False, seed=0):
    hi = mix(GOLD_COIN[0], RUST[0], rust)
    mid = mix(GOLD_COIN[1], RUST[1], rust)
    lo = mix(GOLD_COIN[2], RUST[2], rust)
    # shadow
    c.drawCircle(cx + 6, cy + 10, r, paint((0, 0, 0), 0.45 * alpha, blur=12))
    # disc
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(center=(cx - r * 0.35, cy - r * 0.4), radius=r * 1.7,
                colors=[C(*hi, 255 * alpha), C(*mid, 255 * alpha), C(*lo, 255 * alpha)],
                positions=[0.0, 0.55, 1.0]))
    # slightly irregular flan
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        rr = r * (1 + 0.018 * math.sin(3 * a + seed) + 0.012 * math.sin(7 * a + seed * 2))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    flan = path_from(pts, closed=True, smooth=True)
    c.drawPath(flan, p)
    # rim
    c.drawCircle(cx, cy, r * 0.90, paint(lo, 0.55 * alpha, stroke=r * 0.025))
    c.drawCircle(cx - 1, cy - 1, r * 0.90, paint(hi, 0.35 * alpha, stroke=r * 0.012))
    # beads
    for k in range(64):
        a = 2 * math.pi * k / 64
        c.drawCircle(cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a), r * 0.014, paint(lo, 0.5 * alpha))
    # legend around
    f = font("cinzel", max(9, r * 0.13))
    txt = legend
    total = sum(f.measureText(ch) + r * 0.012 for ch in txt)
    circ = 2 * math.pi * r * 0.78
    start = math.radians(140) + (circ * 0.82 - total) / (r * 0.78) * 0  # start lower-left
    ang = start
    for ch in txt:
        w = f.measureText(ch) + r * 0.012
        a_mid = ang + w / 2 / (r * 0.78)
        x = cx + r * 0.78 * math.cos(a_mid)
        y = cy + r * 0.78 * math.sin(a_mid)
        c.save(); c.translate(x, y); c.rotate(math.degrees(a_mid) + 90)
        c.drawString(ch, -w / 2, r * 0.045, f, paint(lo, 0.85 * alpha))
        c.drawString(ch, -w / 2 - 1, r * 0.045 - 1, f, paint(hi, 0.35 * alpha))
        c.restore()
        ang += w / (r * 0.78)
    # relief bust: shadow, highlight, body
    s = r * 0.62
    bx, by = cx - r * 0.02, cy + r * 0.06
    prof = profile_path(bx, by, s, flip)
    c.save()
    c.clipPath(path_from([(cx + r * 0.70 * math.cos(a), cy + r * 0.70 * math.sin(a))
                          for a in [2 * math.pi * k / 40 for k in range(40)]], closed=True), doAntiAlias=True)
    c.save(); c.translate(r * 0.025, r * 0.03); c.drawPath(prof, paint(lo, 0.85 * alpha, blur=r * 0.01)); c.restore()
    c.save(); c.translate(-r * 0.018, -r * 0.022); c.drawPath(prof, paint(hi, 0.9 * alpha)); c.restore()
    c.drawPath(prof, paint(mid, alpha))
    if beard:
        bp = beard_path(bx, by, s, flip)
        c.drawPath(bp, paint(mid, alpha))
        for k in range(14):
            xx = bx + (0.05 + 0.032 * k) * s * (-1 if flip else 1)
            yy = by + (0.08 + 0.05 * math.sin(k * 1.7)) * s
            c.drawCircle(xx, yy, s * 0.025, paint(lo, 0.5 * alpha, stroke=1.0))
    # hair curls
    for k in range(10):
        a = math.radians(200 + k * 15)
        xx = bx + (math.cos(a) * 0.42 - 0.05) * s * (-1 if flip else 1)
        yy = by + math.sin(a) * 0.42 * s - 0.38 * s
        c.drawCircle(xx, yy, s * 0.05, paint(lo, 0.45 * alpha, stroke=1.2))
    laurel(c, bx, by, s, paint(mix(lo, mid, 0.4), 0.9 * alpha), flip)
    # drapery folds
    for k in range(3):
        pa = path_from([(bx - 0.4 * s + k * 0.25 * s, by + 0.62 * s), (bx - 0.25 * s + k * 0.25 * s, by + 0.72 * s),
                        (bx - 0.1 * s + k * 0.25 * s, by + 0.79 * s)], smooth=True)
        c.drawPath(pa, paint(lo, 0.5 * alpha, stroke=1.4))
    c.restore()
    # wear / patina
    c.drawCircle(cx, cy, r, paint((0, 0, 0), 0.0))
    # crack
    if crack > 0:
        rng = [(0.05, -0.98), (0.10, -0.62), (-0.04, -0.35), (0.12, -0.05), (0.02, 0.22), (0.16, 0.55), (0.08, 0.99)]
        pts = [(cx + a * r, cy + b * r) for a, b in rng]
        pa = path_from(pts)
        pr = paint((20, 12, 8), alpha, stroke=r * 0.035)
        draw_path_progress(c, pa, pr, crack)
        draw_path_progress(c, pa, paint(hi, 0.4 * alpha, stroke=r * 0.012), crack)
        if crack > 0.5:
            br = path_from([(cx - 0.04 * r, cy - 0.35 * r), (cx - 0.35 * r, cy - 0.22 * r), (cx - 0.62 * r, cy - 0.30 * r)])
            draw_path_progress(c, br, pr, (crack - 0.5) * 2)
            br2 = path_from([(cx + 0.02 * r, cy + 0.22 * r), (cx + 0.40 * r, cy + 0.30 * r), (cx + 0.70 * r, cy + 0.18 * r)])
            draw_path_progress(c, br2, pr, (crack - 0.6) * 2.5)

EMPERORS = [
    dict(zh="涅尔瓦", years="96–98", legend="IMP NERVA CAES AVG", beard=False),
    dict(zh="图拉真", years="98–117", legend="IMP CAES NERVA TRAIAN AVG", beard=False),
    dict(zh="哈德良", years="117–138", legend="HADRIANVS AVGVSTVS", beard=True),
    dict(zh="安敦宁·毕尤", years="138–161", legend="ANTONINVS AVG PIVS", beard=True),
    dict(zh="马可·奥勒留", years="161–180", legend="M AVREL ANTONINVS AVG", beard=True),
    dict(zh="康茂德", years="180–192", legend="M COMMODVS ANTONINVS AVG", beard=True),
]
LINKS = ["收养", "收养", "收养", "收养", "亲生"]

def coin_pos(i):
    x = 300 if i % 2 == 0 else 780
    y = 418 + i * 152
    return x, y

def draw_coins(c, appear=1.0, links=1.0, final_link=1.0, crack=0.0, rust=0.0, focus=None, dim=0.0):
    c.drawImage(marble_image(), 0, 0)
    # darken edges for focus
    vignette(c, W / 2, 800, 1150, 175)
    r = 92
    # links
    for i in range(5):
        a = clamp(links * 5 - i) if i < 4 else final_link
        if a <= 0:
            continue
        (x0, y0), (x1, y1) = coin_pos(i), coin_pos(i + 1)
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        sx, sy = x0 + ux * (r + 8), y0 + uy * (r + 8)
        ex, ey = x1 - ux * (r + 8), y1 - uy * (r + 8)
        pa = path_from([(sx, sy), (ex, ey)])
        if i < 4:
            p = paint(GOLD_HI, 0.9, stroke=3.2)
            p.setPathEffect(dash_trim(12, 10, a))
            c.drawPath(pa, p)
            col = GOLD_HI
        else:
            draw_path_progress(c, pa, paint(RED, 1.0, stroke=5), a)
            col = RED
        if a > 0.6:
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            la = clamp((a - 0.6) / 0.4)
            w = 92
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(mx - w / 2, my - 22, w, 44), 22, 22)
            c.drawRRect(rr, paint(INK, 0.9 * la))
            c.drawRRect(rr, paint(col, la, stroke=2))
            draw_text(c, LINKS[i], mx, my + 10, "serif_sb", 28, col, la, align="center")
    # coins
    for i, e in enumerate(EMPERORS):
        a = clamp(appear * 6 - i)
        if a <= 0:
            continue
        x, y = coin_pos(i)
        y += (1 - ease_out(a)) * 30
        d = dim if (focus is not None and focus != i) else 0.0
        is_last = i == 5
        coin(c, x, y, r, e["legend"], e["beard"], rust=rust if is_last else 0.0,
             crack=crack if is_last else 0.0, alpha=a * (1 - 0.55 * d), flip=False, seed=i)
        # labels on the outer side
        if i % 2 == 0:
            lx, al = x - r - 22, "right"
        else:
            lx, al = x + r + 22, "left"
        zh = e["zh"]
        size = 34 if len(zh) <= 3 else 30
        col = RED if (is_last and final_link > 0.5) else IVORY
        draw_text(c, zh, lx, y - 4, "serif_sb", size, col, a * (1 - 0.6 * d), align=al)
        draw_text(c, e["years"], lx, y + 32, "garamond", 28, GOLD, a * 0.9 * (1 - 0.6 * d), align=al)

# ---------------------------------------------------------------- Caesar -> Kaiser / Tsar
def draw_caesar(c, coin_a=1.0, name_a=1.0, morph=0.0, extra=0.0):
    c.drawImage(marble_image(), 0, 0)
    vignette(c, W / 2, 760, 1100, 185)
    coin(c, 540, 560, 170, "IMP CAESAR DIVI F", False, alpha=coin_a, seed=9)
    # CAESAR word
    y = 900
    draw_text(c, "CAESAR", 540, y, "cinzel", 120, GOLD_HI, name_a * (1 - 0.4 * morph), align="center",
              tracking=0.08, glow=10 * name_a, glow_color=GOLD)
    draw_text(c, "恺撒 · 一个人的名字", 540, y + 62, "serif", 32, IVORY, name_a * (1 - 0.4 * morph), align="center")
    if morph > 0:
        for k, (word, fnm, zh) in enumerate([("KAISER", "cinzel", "德语 · 皇帝"), ("ЦАРЬ", "garamond", "俄语 · 沙皇")]):
            a = clamp(morph * 2 - k * 0.6)
            x = 300 if k == 0 else 780
            yy = 1100
            pa = path_from([(540, y + 90), (x, yy - 90)])
            draw_path_progress(c, pa, paint(GOLD, 0.8, stroke=2.4), a)
            draw_text(c, word, x, yy, fnm, 76, GOLD_HI, a, align="center", tracking=0.06)
            draw_text(c, zh, x, yy + 48, "serif", 28, IVORY, a * 0.9, align="center")
