"""Visual beats for ep.66, part 2 (s3 Ishigakiyama climax, s4 katanagari & kenchi, s5 close)."""
from scenes import *

# =================================================================== s3 Ishigakiyama
@mapbeat
def v_ishi_site(c, x):
    cam = cam_lerp("odawara", (139.145, 35.248, 0.5), (139.14, 35.244, 0.62), clamp(x.t / max(x.T, 1)))
    mapframe(c, cam, x)
    Xo, Yo = cam.city("小田原城"); Xi, Yi = cam.city("石垣山城")
    ring = paint(RED, 0.8, stroke=6); ring.setPathEffect(skia.DashPathEffect.Make([20, 12], x.t * 30))
    c.drawCircle(Xo, Yo, 150, ring)
    city_marker(c, Xo, Yo, "小田原城", "lit", 1, x.t, 1.3, "r", 42)
    k = eout(x.t / 1.5)
    red_marker(c, Xi, Yi, k, x.t, 1.4, None)
    flash(c, Xi, Yi, (x.t - 0.3) / 1.2, RED, 160)
    # distance line
    u = eout(clamp((x.t - 1.0) / 1.2))
    p = paint(WHITE, 0.9 * u, stroke=4); p.setPathEffect(skia.DashPathEffect.Make([14, 10], 0))
    c.drawLine(Xi, Yi, lerp(Xi, Xo, u), lerp(Yi, Yo, u), p)
    text(c, "约 3 公里（示意）", (Xi + Xo) / 2 + 30, (Yi + Yo) / 2 + 70, 40, "sansm", WHITE, u, "c", stroke=6)
    if x.on("d02"):
        b = x.p("d02", 0.5)
        text(c, "笠悬山", Xi - 40, Yi - 70, 42, "sans", (200, 190, 170), b * (1 - x.p("d02", 0.5, 1.6)), "c", stroke=6)
        text(c, "石垣山", Xi - 40, Yi - 70, 50, "serifbk", RED, x.p("d02", 0.5, 1.6), "c", stroke=7)
    text(c, "围城的同时 · 筑城", W / 2, 470, 70, "serifbk", WHITE, 1, "c", shadow=10)

def build_scene(c, x, prog, night=1.0, workers=True):
    t = x.t
    sky3(c, (6, 8, 16), (18, 22, 36), (46, 40, 48), 1100)
    stars(c, t, 0.6 * night)
    ridge(c, 31, 1000, 50, (20, 24, 30), 1.0)
    gy = 1250
    ridge(c, 32, gy - 30, 22, (28, 26, 26), 1.0, rough=0.1)
    # castle grows: stone base -> walls -> keep levels
    cx = W / 2
    bw = 520
    hb = 220 * clamp(prog / 0.45)
    if hb > 2:
        ishigaki(c, cx - bw / 2, cx + bw / 2, gy - hb, gy, 1.0, (150, 130, 110), (60, 50, 44), seed=9)
    if prog > 0.45:
        lv = clamp((prog - 0.45) / 0.55)
        c.save(); c.clipRect(skia.Rect(0, gy - hb - 520 * lv, W, gy - hb + 2))
        tenshu(c, cx, gy - hb, 1.25, a=1.0, lit=0.45, windows=0.25)
        c.restore()
        # scaffold
        for k in range(7):
            xx = cx - 170 + k * 56
            c.drawLine(xx, gy - hb, xx, gy - hb - 480 * lv, paint((70, 52, 36), 0.7, stroke=4))
        for k in range(6):
            yy = gy - hb - k * 80 * lv
            c.drawLine(cx - 180, yy, cx + 180, yy, paint((70, 52, 36), 0.6, stroke=3))
    # crane / hoist
    c.drawLine(cx + 330, gy, cx + 330, gy - 560, paint((40, 30, 22), 1, stroke=10))
    c.drawLine(cx + 330, gy - 540, cx + 90, gy - 480, paint((40, 30, 22), 1, stroke=7))
    sy = gy - 480 + 200 * (0.5 + 0.5 * math.sin(t * 0.8))
    c.drawLine(cx + 110, gy - 485, cx + 110, sy, paint((60, 50, 40), 1, stroke=2))
    c.drawRect(skia.Rect(cx + 80, sy, cx + 140, sy + 44), paint((130, 116, 100), 1))
    # bonfires
    for i, fx in enumerate([110, 260, 820, 980]):
        fire(c, fx, gy + 40, 1.2, t, 1.0, i)
    # workers hauling a stone on a sledge
    if workers:
        off = (t * 40) % 240
        c.drawRect(skia.Rect(80 + off, gy + 140, 300 + off, gy + 230), paint((110, 100, 88), 1))
        for k in range(9):
            person(c, 330 + off + k * 60, gy + 240, 1.6, (12, 10, 10), 1.0, arm=0.2)
        c.drawLine(300 + off, gy + 170, 330 + off + 8 * 60 + 20, gy + 140, paint((70, 56, 40), 1, stroke=3))
    c.drawRect(skia.Rect(0, gy + 250, W, H), paint((10, 9, 9)))

@scenic
def v_ishi_build(c, x):
    prog = clamp(0.1 + 0.9 * x.t / max(x.T, 1))
    build_scene(c, x, prog)
    a = clamp(x.t / 0.5)
    counter(c, 80 * eout(x.t / 3), W / 2, 470, 130, a, GOLD, " 天")
    text(c, "三四万人 · 四月 → 六月下旬", W / 2, 545, 44, "sansm", WHITE, a, "c", stroke=6)
    seal(c, 70, 640, "据《小田原北条记》· 江户时代军记", a, 30)
    if x.on("d04"):
        chip(c, "关东最早的总石垣城", W / 2, 1440, x.p("d04", 0.5), GOLD, 44)

@scenic
def v_ishi_legend(c, x):
    prog = clamp(x.t / max(x.T * 0.8, 1))
    dawn_scene(c, x, prog, defenders=True)
    seal(c, 70, 640, "逸话", 1.0, 40)
    text(c, "树林后施工 · 一夜砍倒", W / 2, 470, 60, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=10)

@scenic
def v_ishi_look(c, x):
    # day/night cycles while the far castle grows; foreground Odawara wall with a watcher
    t = x.t
    cyc = (t / 2.2) % 1.0
    day = 0.5 + 0.5 * math.cos(cyc * 2 * math.pi)
    top = tuple(int(lerp(a, b, day)) for a, b in zip((8, 10, 20), (60, 84, 118)))
    hor = tuple(int(lerp(a, b, day)) for a, b in zip((36, 34, 44), (200, 186, 156)))
    sky3(c, top, tuple((a + b) // 2 for a, b in zip(top, hor)), hor, 1050)
    stars(c, t, 0.6 * (1 - day))
    ridge(c, 12, 1020, 55, (44, 52, 56), 1.0, rough=0.25)
    cx = 600; gy = ridge_y(12, 1020, 55, cx, rough=0.25) + 6
    prog = clamp(t / max(x.T * 0.85, 1))
    c.save(); c.translate(cx, gy); c.scale(0.6, 0.6); c.translate(-cx, -gy)
    bw = 320; hb = 120 * clamp(prog / 0.4)
    if hb > 1: ishigaki(c, cx - bw / 2, cx + bw / 2, gy - hb, gy, 1.0, (160, 150, 132), (60, 56, 50))
    if prog > 0.4:
        lv = clamp((prog - 0.4) / 0.6)
        c.save(); c.clipRect(skia.Rect(0, gy - hb - 360 * lv, W, gy - hb + 1)); tenshu(c, cx, gy - hb, 1.0, lit=0.5 + 0.5 * day, windows=0.6 * (1 - day)); c.restore()
    c.restore()
    if day < 0.4:
        for i, fx in enumerate([cx - 140, cx + 150]): fire(c, fx, gy - 4, 0.5, t, 1 - day, i)
    fy = 1500
    c.drawRect(skia.Rect(0, fy, W, H), paint((12, 12, 14)))
    for i in range(0, W + 60, 60): c.drawRect(skia.Rect(i, fy - 40, i + 34, fy), paint((12, 12, 14)))
    ashigaru(c, 860, fy + 10, 1.7, (8, 8, 10), 1.0)
    text(c, "一天天 · 一层层", W / 2, 470, 66, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
    if x.on("d06"):
        seal(c, 70, 640, "很可能是故意让对方看的", x.p("d06", 0.5, 2.0), 30)
    if x.on("d07"):
        b = x.p("d07", 0.4)
        card(c, 70, 700, W - 140, 170, b, fa=0.85)
        text(c, "围城里，为什么要修永久的石头城？", W / 2, 805, 48, "serifbk", GOLD, b, "c")

def tent_icon(c, cx, cy, s, a, color=(190, 170, 140)):
    c.drawPath(P((cx - 110 * s, cy), (cx + 110 * s, cy), (cx, cy - 120 * s)), paint(color, a))
    c.drawPath(P((cx - 22 * s, cy), (cx + 22 * s, cy), (cx, cy - 50 * s)), paint(INK, a))

def v_signal(c, x):
    paper_bg(c, dark=0.4)
    a = clamp(x.t / 0.4)
    mech_tag(c, "二", "昂贵的信号", a)
    if x.on("d09"):
        b = x.p("d09", 0.5)
        card(c, 80, 520, W - 160, 230, b, fa=0.85, border=GOLD)
        text(c, "谢林《冲突的战略》（1960）", W / 2, 600, 40, "sansm", GOLD, b, "c")
        text(c, "威胁，怎样才能让对手相信？", W / 2, 690, 54, "serifbk", WHITE, b, "c")
    if x.on("d10"):
        b = x.p("d10", 0.5)
        # cheap talk vs costly commitment bars
        text(c, "嘴上说说", 300, 870, 44, "serifbk", (200, 190, 170), b, "c")
        text(c, "代价高 · 收不回", 780, 870, 44, "serifbk", GOLD, b, "c")
        c.drawRect(skia.Rect(240, 1260 - 40, 360, 1260), paint((150, 140, 120), b))
        hh = 40 + 320 * eout(x.p("d10", 1.5))
        c.drawRect(skia.Rect(720, 1260 - hh, 840, 1260), paint(RED, b))
        text(c, "可信度", W / 2, 1320, 36, "sans", WHITE, b, "c")
        text(c, "×", 300, 1150, 90, "serifbk", (200, 120, 100), x.p("d10", 0.5, 1.5), "c")
        text(c, "√", 780, 1260 - hh - 30, 90, "serifbk", GOLD, x.p("d10", 0.5, 1.5), "c")

def v_signal2(c, x):
    paper_bg(c, dark=0.45)
    a = clamp(x.t / 0.4)
    card(c, 60, 480, 460, 860, a, fa=0.7, border=(150, 140, 120))
    tent_icon(c, 290, 950, 1.4, a)
    text(c, "临时营寨", 290, 1060, 50, "serifbk", (210, 200, 180), a, "c")
    text(c, "「我在这里」", 290, 1200, 50, "serifbk", (210, 200, 180), a, "c", shadow=10)
    b = x.p("d11", 0.5, 2.2)
    card(c, 560, 480, 460, 860, b, fa=0.78, border=GOLD)
    c.save(); c.translate(790, 1000); c.scale(0.62, 0.62); castle(c, 0, 0, 1.0, b, 0.9, walls=False); c.restore()
    text(c, "石墙 + 天守", 790, 1060, 50, "serifbk", GOLD, b, "c")
    text(c, "「我不走了」", 790, 1200, 52, "serifbk", RED, b, "c", shadow=10)

@scenic
def v_tea(c, x):
    bg_grad(c, (40, 30, 20), (10, 8, 6))
    t = x.t
    # tatami floor
    c.drawRect(skia.Rect(0, 1240, W, H), paint((70, 64, 40)))
    for k in range(6): c.drawLine(0, 1240 + k * 60, W, 1240 + k * 60, paint((40, 34, 22), 0.6, stroke=2))
    # shoji
    for k in range(5):
        c.drawRect(skia.Rect(80 + k * 190, 520, 250 + k * 190, 1180), paint((220, 200, 160), 0.18))
        for j in range(5): c.drawLine(80 + k * 190, 520 + j * 132, 250 + k * 190, 520 + j * 132, paint((60, 50, 36), 0.5, stroke=3))
    # seated figures
    for (sx, flip) in ((330, 1), (760, -1)):
        c.save(); c.translate(sx, 1240); c.scale(flip * 1.6, 1.6)
        c.drawPath(P((-60, 0), (60, 0), (40, -70), (-30, -80)), paint((14, 10, 8)))
        c.drawPath(P((-26, -76), (26, -72), (20, -150), (-20, -150)), paint((14, 10, 8)))
        c.drawCircle(0, -168, 20, paint((14, 10, 8)))
        c.restore()
    # kettle + steam + bowl
    c.drawCircle(545, 1200, 40, paint((30, 26, 22)))
    for k in range(4):
        ph = t * 0.8 + k * 0.7
        c.drawCircle(545 + 20 * math.sin(ph * 2), 1130 - (ph % 3) * 90, 26 + k * 6, paint((230, 220, 200), 0.10, blur=16))
    c.drawPath(P((600, 1230), (660, 1230), (650, 1250), (610, 1250)), paint((150, 110, 70)))
    text(c, "阵中茶会", W / 2, 420, 80, "serifbk", PAPERL, clamp(t / 0.5), "c", shadow=10, spacing=12)
    text(c, "千利休 · 侧室茶茶", W / 2, 495, 42, "sansm", GOLD, clamp(t / 0.5), "c", stroke=6)

@scenic
def v_standoff(c, x):
    t = x.t
    sky3(c, (18, 18, 30), (60, 50, 60), (170, 112, 74), 1080)
    ridge(c, 41, 960, 70, (46, 44, 54), 1.0)
    # far: Ishigakiyama castle on left ridge (vermilion-lit)
    gy = ridge_y(41, 960, 70, 260) + 8
    c.save(); c.translate(260, gy); c.scale(0.45, 0.45); c.translate(-260, -gy)
    castle(c, 260, gy, 1.0, 1.0, 0.8, walls=False)
    c.restore()
    c.drawCircle(260, gy - 80, 160, paint(RED, 0.18, blur=50))
    # near: Odawara castle right, big
    c.save(); c.translate(760, 1420); c.scale(0.95, 0.95); c.translate(-760, -1420)
    castle(c, 760, 1420, 1.0, 1.0, 0.55, windows=0.5)
    c.restore()
    c.drawRect(skia.Rect(0, 1420, W, H), paint((14, 12, 12)))
    # eye line
    u = eout(clamp(t / 2.0))
    p = paint(WHITE, 0.5 * u, stroke=2); p.setPathEffect(skia.DashPathEffect.Make([10, 12], -t * 20))
    c.drawLine(700, 860, lerp(700, 280, u), lerp(860, gy - 120, u), p)
    text(c, "城里的人每天抬头", W / 2, 420, 60, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
    text(c, "一个打算在这里过日子的对手", W / 2, 520, 50, "serifbk", RED, clamp((t - 2.0) / 0.6), "c", stroke=7)

def gauge(c, cx, cy, r, val, label, a, color=CYAN):
    p = paint((60, 56, 50), a, stroke=18); p.setStrokeCap(skia.Paint.kButt_Cap)
    c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), 180, 180, False, p)
    q = paint(color, a, stroke=18); q.setStrokeCap(skia.Paint.kButt_Cap)
    c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), 180, 180 * clamp(val), False, q)
    ang = math.pi * (1 + clamp(val))
    c.drawLine(cx, cy, cx + math.cos(ang) * r * 0.85, cy + math.sin(ang) * r * 0.85, paint(WHITE, a, stroke=6))
    c.drawCircle(cx, cy, 12, paint(WHITE, a))
    text(c, label, cx, cy + 70, 44, "serifbk", WHITE, a, "c")

def v_expect(c, x):
    dark_bg(c, x, "odawara", 139.15, 35.25, 0.5, 0.75)
    a = clamp(x.t / 0.4)
    mech_tag(c, "三", "预期的崩塌", a)
    v1 = 0.75 - 0.6 * eout(x.p("d15", 4.0)) if x.on("d15") else 0.75
    v2 = 0.65 - 0.55 * eout(x.p("d15", 5.0, 1.0)) if x.on("d15") else 0.65
    gauge(c, 300, 900, 180, v1, "援军会来？", a)
    gauge(c, 780, 900, 180, v2, "对方会撤？", a)
    if x.on("d15"):
        text(c, "坚守的意义 = 对未来的预期", W / 2, 1220, 52, "serifbk", GOLD, x.p("d15", 0.5), "c", stroke=7)

@mapbeat
def v_date(c, x):
    cam = cam_lerp("japan", (139.3, 36.3, 0.75), (139.4, 36.0, 0.8), x.t / max(x.T, 1))
    mapframe(c, cam, x)
    territory(c, cam, HOJO, CYAN, 1, 0.16)
    k = eout(x.t / 2.5)
    route(c, cam, [(139.93, 37.49), (139.75, 36.9), (139.4, 35.9), (139.17, 35.27)], k, 30, GOLD, flow_t=x.t)
    X, Y = cam.city("会津"); city_marker(c, X, Y, "会津 · 伊达政宗", "gold", 1, x.t, 1.1, "r", 40)
    X, Y = cam.city("小田原城"); city_marker(c, X, Y, "小田原", "siege", 1, x.t, 1.1, "l", 40)
    text(c, "6 月初 · 伊达政宗参阵", W / 2, 470, 64, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "最后的外援，向秀吉低头", W / 2, 1380, 54, "serifbk", GOLD, clamp((x.t - 2.5) / 0.6), "c", stroke=7)

@mapbeat
def v_expect2(c, x):
    cam = Cam("kanto", 139.3, 35.6, 0.55)
    mapframe(c, cam, x, dim=0.1)
    st = {nm: "fallen" for nm in HOJO_CASTLES[1:]}; st["忍城"] = "lit"
    kanto_net(c, cam, x, st, 0.3)
    X0, Y0 = cam.city("小田原城")
    for nm in ("八王子城", "钵形城", "韭山城", "玉绳城"):
        X, Y = cam.city(nm)
        for j in range(3):
            u = ((x.t * 0.4 + j / 3 + hash(nm) % 7 / 7) % 1.0)
            c.drawCircle(lerp(X, X0, u), lerp(Y, Y0, u), 9, paint(RED, 0.9 * (1 - u * 0.5)))
    flash(c, X0, Y0, (x.t % 1.6) / 1.6, RED, 160)
    text(c, "坏消息 · 一个接一个", W / 2, 470, 64, "serifbk", WHITE, 1, "c", shadow=10)
    text(c, "八王子城的惨状 · 被刻意展示", W / 2, 1380, 50, "serifbk", RED, clamp((x.t - 1) / 0.6), "c", stroke=7)

@scenic
def v_hyojo(c, x):
    bg_grad(c, (30, 24, 18), (8, 6, 5))
    t = x.t
    c.drawRect(skia.Rect(0, 1180, W, H), paint((48, 40, 28)))
    # two rows of seated retainers facing each other
    for side in (-1, 1):
        for k in range(4):
            sx = W / 2 + side * (150 + k * 95); sy = 1180 + k * 60
            hl = 0.5 + 0.5 * math.sin(t * 2.2 + (0 if side < 0 else math.pi))
            colr = tuple(int(v * (0.6 + 0.4 * hl)) for v in ((150, 70, 50) if side < 0 else (80, 120, 170)))
            c.save(); c.translate(sx, sy); c.scale(1.2, 1.2)
            c.drawPath(P((-50, 0), (50, 0), (34, -60), (-30, -66)), paint((14, 10, 8)))
            c.drawPath(P((-22, -62), (22, -60), (18, -126), (-18, -126)), paint((14, 10, 8)))
            c.drawCircle(0, -142, 17, paint((14, 10, 8)))
            c.restore()
            c.drawCircle(sx, sy - 250, 30 * hl, paint(colr, 0.35 * hl, blur=14))
    text(c, "主战", 220, 900, 64, "serifbk", (220, 110, 90), 1, "c", shadow=8)
    text(c, "主和", 860, 900, 64, "serifbk", (130, 170, 220), 1, "c", shadow=8)
    text(c, "争执不下", W / 2, 470, 72, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
    if x.on("d19"):
        b = x.p("d19", 0.5)
        card(c, 80, 540, W - 160, 240, b, fa=0.85, border=GOLD)
        text(c, "「小田原评定」", W / 2, 640, 58, "serifbk", GOLD, b, "c")
        text(c, "＝ 议而不决 · 江户以后才流行的用法", W / 2, 720, 38, "sans", WHITE, b, "c")

@mapbeat
def v_encircle(c, x):
    cam = cam_lerp("odawara", (139.145, 35.248, 0.5), (139.15, 35.25, 0.72), clamp(x.t / max(x.T, 1)))
    mapframe(c, cam, x, dim=0.1)
    X, Y = cam.city("小田原城"); Xi, Yi = cam.city("石垣山城")
    k = eout(clamp(x.t / max(x.T - 0.5, 1)))
    R = 520 - 300 * k
    # red camps ring
    for i in range(40):
        ang = i / 40 * 2 * math.pi + 0.05 * math.sin(x.t + i)
        rr = R + 30 * math.sin(i * 1.7)
        c.drawCircle(X + math.cos(ang) * rr, Y + math.sin(ang) * rr * 0.9, 12, paint(RED, 0.95))
    rp = paint(RED, 0.6, stroke=10, blur=6); c.drawCircle(X, Y, R, rp)
    red_marker(c, Xi, Yi, 1, x.t, 1.4, "石垣山", "l", 40)
    city_marker(c, X, Y, "小田原", "lit", 1 - 0.4 * k, x.t, 1.4, "u", 44)
    big_title(c, "所有出路 · 一一堵死", 470, 66, WHITE, 1)

@scenic
def v_surrender(c, x):
    t = x.t
    bg_grad(c, (20, 18, 20), (6, 6, 8))
    # big gate front view
    gx0, gx1, gy0, gy1 = 190, 890, 640, 1480
    c.drawRect(skia.Rect(80, gy0 - 120, W - 80, gy1), paint((34, 30, 28)))
    roof(c, W / 2, gy0 - 100, 980, 120, (20, 20, 24))
    op = eout(clamp((t - 0.8) / 5.0))
    light = paint((255, 226, 170), 0.9 * op)
    c.drawRect(skia.Rect(W / 2 - 350 * op, gy0, W / 2 + 350 * op, gy1), light)
    c.drawRect(skia.Rect(W / 2 - 350 * op, gy0, W / 2 + 350 * op, gy1), paint((255, 210, 150), 0.5 * op, blur=60))
    for side in (-1, 1):
        dx0 = W / 2 + side * 350 * op; dx1 = W / 2 + side * (350 + 350 * (1 - op) * 0 + 0) if False else None
        lx = W / 2 - 350 if side < 0 else W / 2 + 350 * op
        rx = W / 2 - 350 * op if side < 0 else W / 2 + 350
        c.drawRect(skia.Rect(min(lx, rx), gy0, max(lx, rx), gy1), paint((60, 44, 32)))
        for j in range(6):
            yy = gy0 + 60 + j * 130
            c.drawCircle((lx + rx) / 2, yy, 10, paint((140, 120, 80)))
    c.drawRect(skia.Rect(0, gy1, W, H), paint((14, 12, 10)))
    if op > 0.2:
        person(c, W / 2, gy1 - 4, 2.4, (12, 10, 10), clamp((op - 0.2) * 3))
    text(c, "7 月 5 日", W / 2, 420, 84, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=12)
    text(c, "开城", W / 2, 540, 110, "serifbk", PAPERL, clamp((t - 1.0) / 0.6), "c", shadow=14, spacing=30)
    if x.on("d22"):
        seal(c, 70, 680, "氏直免死 · 氏政等人被令切腹", x.p("d22", 0.5), 32)

@mapbeat
def v_surrender2(c, x):
    cam = Cam("odawara", 139.15, 35.25, 0.62)
    mapframe(c, cam, x, dim=0.15)
    X, Y = cam.city("小田原城")
    k = eout(x.t / 1.5)
    city_marker(c, X, Y, "小田原", "fallen", 1, x.t, 1.6, "u", 46)
    c.drawCircle(X, Y, 90 + 260 * k, paint((160, 160, 160), 0.25 * (1 - k), stroke=6))
    big_title(c, "围城三个月", 640, 86, WHITE, clamp(x.t / 0.5))
    big_title(c, "几乎没有大规模攻城", 780, 70, GOLD, clamp((x.t - 0.8) / 0.5))

# =================================================================== s4 katanagari & kenchi
def village_bg(c, x):
    sky3(c, (60, 70, 80), (150, 150, 130), (210, 190, 150), 1000)
    ridge(c, 51, 920, 60, (90, 100, 90), 1.0)
    ridge(c, 52, 1000, 30, (70, 82, 64), 1.0, rough=0.2)
    # paddies
    for k in range(5):
        y = 1040 + k * 70
        c.drawRect(skia.Rect(0, y, W, y + 66), paint((96 - k * 6, 116 - k * 8, 70 - k * 4)))
        c.drawLine(0, y, W, y, paint((60, 64, 40), 0.7, stroke=3))
    # farmhouses
    for hx in (180, 860):
        c.drawRect(skia.Rect(hx - 90, 940, hx + 90, 1030), paint((60, 50, 40)))
        c.drawPath(P((hx - 130, 950), (hx + 130, 950), (hx + 40, 860), (hx - 40, 860)), paint((120, 104, 70)))

def farmer(c, x0, y0, s, sword=True, a=1.0, color=(20, 16, 12), tool=None):
    ashigaru(c, x0, y0, s, color, a, spear=False)
    if sword:
        c.save(); c.translate(x0, y0); c.scale(s, s)
        c.drawLine(-20, -58, 42, -36, paint(color, a, stroke=6)); c.restore()
    if tool == "spear":
        c.drawLine(x0 + 16 * s, y0 - 70 * s, x0 + 26 * s, y0 - 240 * s, paint(color, a, stroke=4 * s))
    if tool == "gun":
        c.drawLine(x0 - 10 * s, y0 - 80 * s, x0 + 60 * s, y0 - 150 * s, paint(color, a, stroke=5 * s))

@scenic
def v_village(c, x):
    village_bg(c, x)
    for i, (fx, s, tool) in enumerate([(150, 1.6, "spear"), (330, 1.5, None), (540, 1.7, "gun"), (740, 1.5, "spear"), (920, 1.6, None)]):
        farmer(c, fx, 1500 + (i % 2) * 30, s, True, 1.0, (18, 14, 10), tool)
    c.drawRect(skia.Rect(0, 1530, W, H), paint((24, 20, 14)))
    text(c, "战国的村子", W / 2, 420, 80, "serifbk", WHITE, clamp(x.t / 0.5), "c", shadow=12, spacing=10)
    if x.on("e03"):
        chip(c, "争水 · 争山林 · 一揆", W / 2, 540, x.p("e03", 0.5), GOLD, 44)
    if x.on("e04"):
        b = x.p("e04", 0.5)
        card(c, 80, 600, W - 160, 200, b, fa=0.85)
        text(c, "农民手里的刀", W / 2, 680, 50, "serifbk", WHITE, b, "c")
        text(c, "能造就天下人 · 也能掀翻天下人", W / 2, 760, 44, "serifbk", GOLD, b, "c")

def decree_doc(c, x, a, title="刀狩令", date="天正十六年七月八日 · 1588", lines_=None):
    scroll_doc(c, 140, 430, 800, 900, a)
    vcol(c, title, 860, 480, 96, a, (40, 28, 20))
    vcol(c, "天正十六年七月八日", 760, 500, 44, a, (90, 60, 40), "tc")
    for i, ln in enumerate(lines_ or ["諸国百姓、刀・脇指・弓・やり・てつはう", "取をかるへき刀・脇指、大仏御建立釘かすかひ", "百姓ハ農具さへもち、耕作を専に仕候へハ"]):
        vcol(c, ln[:16], 640 - i * 150, 500, 50, a * 0.85, (50, 36, 26), "tc")
    c.drawRect(skia.Rect(200, 1180, 300, 1280), paint((180, 40, 30), 0.85 * a))

def v_decree(c, x):
    paper_bg(c, dark=0.35)
    a = clamp(x.t / 0.5)
    decree_doc(c, x, a)
    text(c, "1588 · 7 月", W / 2, 1420, 56, "serifbk", WHITE, a * (1 - x.p("e07b", 0.4)) if x.on("e07b") else a, "c", stroke=7)
    if x.on("e07b"):
        b = x.p("e07b", 0.5)
        card(c, 70, 1080, W - 140, 300, b, fa=0.9, border=GOLD)
        text(c, "同日 · 海贼停止令", W / 2, 1160, 48, "serifbk", WHITE, b, "c")
        text(c, "私斗 · 海盗 · 百姓持刀 → 收归中央", W / 2, 1240, 40, "sans", GOLD, b, "c")
        text(c, "藤木久志：「丰臣平和令」", W / 2, 1320, 40, "sansm", PAPER, b, "c")

def v_decree1(c, x):
    paper_bg(c, dark=0.4)
    a = clamp(x.t / 0.4)
    text(c, "第一条", W / 2, 450, 72, "serifbk", GOLD, a, "c", shadow=10)
    items = ["刀", "胁差", "弓", "长枪", "铁炮"]
    for i, it in enumerate(items):
        b = clamp((x.t - 0.4 - i * 0.35) / 0.4)
        yy = 580 + i * 140
        card(c, 240, yy, 600, 120, b, fa=0.8, border=(150, 130, 100))
        text(c, it, W / 2, yy + 82, 60, "serifbk", WHITE, b, "c")
        if x.t > 2.8 + i * 0.2:
            u = clamp((x.t - 2.8 - i * 0.2) / 0.3)
            c.drawLine(260, yy + 60, 260 + 560 * u, yy + 60, paint(RED, 0.95, stroke=8))
    text(c, "百姓 · 禁止持有", W / 2, 1380, 56, "serifbk", RED, clamp((x.t - 2.5) / 0.5), "c", stroke=7)

@scenic
def v_daibutsu(c, x):
    t = x.t
    bg_grad(c, (24, 16, 12), (6, 4, 4))
    # faint great Buddha outline (schematic)
    # temple roof silhouette (schematic) behind the forge glow
    roof(c, W / 2, 900, 900, 160, (40, 30, 24), 0.9)
    c.drawRect(skia.Rect(W / 2 - 380, 900, W / 2 + 380, 1180), paint((30, 22, 18), 0.9))
    for k in range(6): c.drawRect(skia.Rect(W / 2 - 340 + k * 132, 900, W / 2 - 320 + k * 132, 1180), paint((60, 44, 30), 0.9))
    # pile of swords with heat glow, melting into nails
    m = eout(clamp((t - 0.8) / 3.0))
    rng = np.random.default_rng(2)
    for i in range(16):
        ang = rng.uniform(-30, 30); xx = 280 + rng.uniform(0, 520); yy = 1320 + rng.uniform(-60, 40)
        katana(c, xx, yy, 300, ang, 1 - m, glow=0.7 * m)
    c.drawCircle(W / 2, 1360, 300, paint((255, 120, 40), 0.35 * m, blur=80))
    for i in range(int(18 * m)):
        nx = 250 + (i % 9) * 70; ny = 1260 + (i // 9) * 120
        c.drawRect(skia.Rect(nx - 6, ny, nx + 6, ny + 90), paint((150, 140, 130), 0.95))
        c.drawRect(skia.Rect(nx - 16, ny - 8, nx + 16, ny + 4), paint((150, 140, 130), 0.95))
    text(c, "第二条", W / 2, 420, 64, "serifbk", GOLD, clamp(t / 0.5), "c", shadow=10)
    text(c, "刀 → 方广寺大佛的钉子", W / 2, 510, 54, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
    if x.on("e07"):
        text(c, "献出刀 · 今生来世都能得救", W / 2, 590, 44, "sansm", PAPER, x.p("e07", 0.5, 3.0), "c", stroke=6)

def v_decree3(c, x):
    paper_bg(c, dark=0.3)
    q0, q1 = x.L("e09")
    if x.t < q0:
        text(c, "第三条 · 原文", W / 2, 760, 72, "serifbk", GOLD, clamp(x.t / 0.4), "c", shadow=10)
    else:
        a = clamp((x.t - q0 + 0.2) / 0.5)
        quote_vertical(c, "百姓ハ農具さへもち、耕作を専に仕候へハ、子々孫々まて長久に候", "刀狩令第三条（島津家文書本）", a,
                       size=66, top=380, reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.2), maxcol=12, srcsize=34)

def v_hoe(c, x):
    bg_grad(c, (40, 34, 24), (10, 8, 6))
    t = x.t
    m = eout(clamp((t - 0.6) / 1.6))
    katana(c, 220, 1100, 640, -40, 1 - m)
    hoe(c, 640, 1460, 1.5, m, -8)
    text(c, "刀", 300, 520, 140, "serifbk", WHITE, 1 - m, "c", shadow=12)
    text(c, "→", W / 2, 520, 110, "serifbk", GOLD, 1, "c")
    text(c, "锄", 780, 520, 140, "serifbk", GOLD, m, "c", shadow=12)
    text(c, "一个身份 · 换成另一个身份", W / 2, 680, 48, "serifbk", WHITE, clamp((t - 2) / 0.6), "c", stroke=7)

ISSUED = [(130.9, 32.6, "九州"), (135.6, 34.8, "近畿"), (134.8, 34.3, "淡路等")]

@mapbeat
def v_myth(c, x):
    cam = Cam("japan", 135.0, 34.5, 0.5 + 0.01 * x.t)
    mapframe(c, cam, x, dim=0.2)
    a = clamp(x.t / 0.4)
    card(c, 90, 400, W - 180, 160, a, fa=0.85, border=(150, 140, 120))
    text(c, "课本：收光全国农民的刀", W / 2, 500, 52, "serifbk", WHITE, a, "c")
    if x.t > 1.5:
        u = clamp((x.t - 1.5) / 0.4)
        c.drawLine(140, 480, 140 + (W - 280) * u, 480, paint(RED, 0.95, stroke=8))
    if x.on("e12"):
        b = x.p("e12", 0.5)
        for (lon, lat, nm) in ISSUED:
            X, Y = cam.P(lon, lat)
            c.drawCircle(X, Y, 120, paint(GOLD, 0.25 * b, blur=40))
            text(c, nm, X, Y + 16, 50, "serifbk", GOLD, b, "c", stroke=7)
        text(c, "实际发给：九州诸侯 · 近畿 · 部分大名", W / 2, 1380, 46, "serifbk", WHITE, b * (1 - x.p("e12b", 0.3)) if x.on("e12b") else b, "c", stroke=7)
    if x.on("e12b"):
        b = x.p("e12b", 0.5)
        card(c, 70, 1100, W - 140, 300, b, fa=0.92, border=GOLD)
        seal(c, 110, 1170, "史料冲突", b, 32)
        text(c, "1590 朱印状：「全国已禁、已没收」", W / 2, 1260, 44, "serifbk", WHITE, b, "c")
        text(c, "政权自己的说法 ≠ 各地实际执行", W / 2, 1340, 42, "sansm", GOLD, b, "c")

def v_fujiki(c, x):
    village_bg(c, x)
    c.drawRect(skia.Rect(0, 0, W, H), paint(INK, 0.45))
    a = clamp(x.t / 0.4)
    card(c, 90, 400, W - 180, 230, a, fa=0.88, border=GOLD)
    text(c, "藤木久志《刀狩》", W / 2, 490, 60, "serifbk", WHITE, a, "c")
    text(c, "岩波新书 · 2005", W / 2, 570, 38, "sansm", GOLD, a, "c")
    b = x.p("e13", 0.5, 2.5) if x.on("e13") else 0
    for i, (lab, yy) in enumerate([("打猎的铁炮", 800), ("祭祀的武具", 920)]):
        bb = clamp(b * 2 - i * 0.5)
        chip(c, lab + " · 留在村里", W / 2, yy, bb, CYAN, 48)
    if x.on("e14"):
        u = eout(x.p("e14", 1.5))
        text(c, "江户时代 · 有的藩清点结果（示意）", W / 2, 1060, 38, "sans", WHITE, x.p("e14", 0.5), "c", stroke=6)
        c.drawRect(skia.Rect(260, 1400 - 180 * u, 420, 1400), paint(GOLD, 0.95))
        c.drawRect(skia.Rect(660, 1400 - 300 * u, 820, 1400), paint(CYAN, 0.95))
        text(c, "武士的铁炮", 340, 1460, 38, "sansm", GOLD, u, "c")
        text(c, "百姓的铁炮", 740, 1460, 38, "sansm", CYAN, u, "c")

def v_fujiki2(c, x):
    paper_bg(c, dark=0.35)
    t = x.t
    a = clamp(t / 0.4)
    big_title(c, "收走的不是武器", 450, 66, WHITE, a)
    big_title(c, "而是带刀的权利", 560, 80, GOLD, clamp((t - 0.8) / 0.5))
    m = eout(x.p("e16", 1.5, 1.5)) if x.on("e16") else 0
    farmer(c, 330, 1300, 2.6, sword=(m < 0.5), a=1.0, color=(30, 24, 18))
    text(c, "百姓", 330, 1400, 52, "serifbk", CYAN, a, "c")
    ashigaru(c, 760, 1300, 2.6, (30, 24, 18), 1.0, spear=False)
    c.save(); c.translate(760, 1300); c.scale(2.6, 2.6); c.drawLine(-22, -58, 46, -34, paint((30, 24, 18), 1, stroke=6)); c.drawLine(-18, -50, 40, -30, paint((30, 24, 18), 1, stroke=5)); c.restore()
    text(c, "武士", 760, 1400, 52, "serifbk", RED, a, "c")
    if x.on("e17"):
        b = x.p("e17", 0.5)
        chip(c, "1587 · 禁止村与村私斗", W / 2, 700, b, GOLD, 40)

def v_line(c, x):
    bg_grad(c, (30, 26, 22), (10, 8, 6))
    t = x.t
    u = eout(clamp(t / 1.5))
    c.drawLine(W / 2, 360, W / 2, 360 + 1200 * u, paint(GOLD, 1, stroke=6))
    c.drawLine(W / 2, 360, W / 2, 360 + 1200 * u, paint(GOLD, 0.4, stroke=24, blur=10))
    a = clamp((t - 0.8) / 0.5)
    text(c, "武士", 270, 520, 90, "serifbk", RED, a, "c", shadow=10)
    for i, s in enumerate(["佩刀", "打仗", "领俸禄"]): chip(c, s, 270, 680 + i * 120, clamp((t - 1.2 - i * 0.3) / 0.4), RED, 46)
    b = clamp((t - 2.0) / 0.5)
    text(c, "百姓", 810, 520, 90, "serifbk", CYAN, b, "c", shadow=10)
    for i, s in enumerate(["种地", "纳贡", "不再佩刀"]): chip(c, s, 810, 680 + i * 120, clamp((t - 2.4 - i * 0.3) / 0.4), CYAN, 46)
    katana(c, 140, 1250, 260, -20, a)
    hoe(c, 820, 1440, 0.9, b, -6)
    big_title(c, "兵农分离", 1370, 92, GOLD, x.p("e18", 0.6, 5.0) if x.on("e18") else 0, spacing=20)

@scenic
def v_kenchi(c, x):
    t = x.t
    bg_grad(c, (40, 46, 34), (12, 14, 10))
    a = clamp(t / 0.4)
    text(c, "太阁检地", W / 2, 430, 86, "serifbk", WHITE, a, "c", shadow=12, spacing=14)
    text(c, "1582 起 · 丈量田地", W / 2, 505, 42, "sansm", GOLD, a, "c", stroke=6)
    prog = eout(clamp((t - 0.5) / 4.0))
    grid_field(c, 140, 640, 6, 5, 133, 120, 1.0, (110, 140, 80), prog=prog)
    # measuring pole sweep
    px = 140 + 800 * ((t * 0.25) % 1.0)
    c.drawLine(px, 600, px, 1260, paint((210, 180, 120), 1, stroke=10))
    for k in range(10): c.drawLine(px - 10, 620 + k * 64, px + 10, 620 + k * 64, paint((60, 40, 20), 1, stroke=4))
    person(c, px + 40, 1300, 2.0, (14, 12, 10), 1)
    if x.on("e21"):
        b = x.p("e21", 0.5)
        card(c, 70, 1250, W - 140, 190, b, fa=0.9, border=GOLD)
        text(c, "1 间 = 6 尺 3 寸   1 段 = 300 步", W / 2, 1330, 44, "serifbk", WHITE, b, "c")
        text(c, "产量 → 折成米 → 石高", W / 2, 1405, 44, "serifbk", GOLD, b, "c")

def v_kenchi2(c, x):
    bg_grad(c, (40, 46, 34), (12, 14, 10))
    t = x.t
    grid_field(c, 140, 640, 4, 3, 200, 160, 1.0, (110, 140, 80))
    names = ["作人 甲", "作人 乙", "作人 丙", "作人 丁", "作人 戊", "作人 己", "作人 庚", "作人 辛", "作人 壬", "作人 癸", "作人 子", "作人 丑"]
    for i in range(12):
        b = clamp((t - 0.3 - i * 0.12) / 0.3)
        xx = 140 + (i % 4) * 200 + 100; yy = 640 + (i // 4) * 160 + 90
        chip(c, names[i], xx, yy, b, PAPER, 30)
    text(c, "一地 · 一作人", W / 2, 470, 82, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=12, spacing=10)
    if x.on("e23"):
        b = x.p("e23", 0.5)
        layers = ["庄园领主", "地方豪族", "层层中间人"]
        for i, s in enumerate(layers):
            u = clamp((x.t - x.L("e23")[0] - 2.5 - i * 0.4) / 0.6)
            yy = 1260 + i * 80 - 300 * eout(u)
            chip(c, s, W / 2, yy, b * (1 - u), (190, 160, 120), 42)
        text(c, "中间层 · 切掉", W / 2, 1400, 50, "serifbk", GOLD, clamp((x.t - x.L("e23")[0] - 3.5) / 0.5), "c", stroke=7)

def v_ledger2(c, x):
    paper_bg(c, dark=0.3)
    t = x.t
    a = clamp(t / 0.4)
    scroll_doc(c, 120, 420, 840, 980, a)
    text(c, "同一本账", W / 2, 520, 70, "serifbk", (40, 28, 20), a, "c")
    rows = [("土地", "×× 村 · 田 3 段"), ("产量", "石高 4.5 石"), ("赋税", "年贡"), ("兵役", "按石高出兵")]
    for i, (k_, v_) in enumerate(rows):
        b = clamp((t - 0.6 - i * 0.6) / 0.4)
        yy = 650 + i * 170
        c.drawLine(180, yy + 40, 900, yy + 40, paint((90, 70, 50), b, stroke=2))
        text(c, k_, 260, yy, 52, "serifbk", (120, 40, 30), b, "c")
        text(c, v_, 640, yy, 46, "serif", (40, 28, 20), b, "c")
    text(c, "（示意）", W / 2, 1360, 32, "sans", (90, 70, 50), a, "c")

def v_weber(c, x):
    paper_bg(c, dark=0.5)
    q0, q1 = x.L("e26")
    a = clamp(x.t / 0.4)
    text(c, "马克斯·韦伯", W / 2, 470, 76, "serifbk", WHITE, a, "c", shadow=10)
    text(c, "《以政治为业》· 1919", W / 2, 545, 42, "sansm", GOLD, a, "c")
    if x.on("e26"):
        b = clamp((x.t - q0 + 0.2) / 0.5)
        card(c, 70, 620, W - 140, 760, b, fa=0.88, border=GOLD)
        de = ["Staat ist diejenige menschliche", "Gemeinschaft, welche innerhalb", "eines bestimmten Gebietes …", "das Monopol legitimer", "physischer Gewaltsamkeit für sich", "(mit Erfolg) beansprucht."]
        for i, ln in enumerate(de):
            text(c, ln, W / 2, 720 + i * 58, 38, "serif", (210, 200, 180) if i not in (3, 4) else GOLD, b, "c")
        text(c, "垄断 · 正当的 · 武力", W / 2, 1210, 60, "serifbk", GOLD, b * clamp((x.t - q0 - 1.0) / 0.6), "c")

def v_weber2(c, x):
    paper_bg(c, dark=0.45)
    t = x.t
    big_title(c, "关键在「正当」", 460, 80, GOLD, clamp(t / 0.5))
    # many swords, one license
    for i in range(12):
        xx = 160 + (i % 6) * 152; yy = 800 + (i // 6) * 200
        katana(c, xx - 60, yy, 150, -30, 0.6)
    u = eout(clamp((t - 2.0) / 1.0))
    card(c, 200, 1180, 680, 170, u, fa=0.92, border=RED)
    text(c, "谁有资格 · 合法地动刀", W / 2, 1290, 56, "serifbk", RED, u, "c")
    text(c, "不必收光每一把刀", W / 2, 640, 50, "serif", WHITE, clamp((t - 0.8) / 0.5), "c")

def v_twonets(c, x):
    bg_grad(c, (24, 22, 18), (6, 6, 5))
    t = x.t
    k1 = eout(clamp(t / 1.5)); k2 = eout(clamp((t - 1.2) / 1.5))
    for i in range(9):
        c.drawLine(180 + i * 90, 600, 180 + i * 90, 600 + 720 * k1, paint(RED, 0.8, stroke=4))
        c.drawLine(180, 600 + i * 90, 180 + 720 * k2, 600 + i * 90, paint(GOLD, 0.8, stroke=4))
    for i in range(9):
        for j in range(9):
            if k1 > 0.99 and k2 > 0.99:
                c.drawCircle(180 + i * 90, 600 + j * 90, 7, paint(WHITE, 0.8))
    text(c, "刀狩：谁能拿刀（人）", W / 2, 440, 50, "serifbk", RED, k1, "c", stroke=6)
    text(c, "检地：谁该交粮（地）", W / 2, 520, 50, "serifbk", GOLD, k2, "c", stroke=6)
    if x.on("e29"):
        big_title(c, "这条路，被制度堵上了", 1410, 60, WHITE, x.p("e29", 0.5, 2.0))

# =================================================================== s5 close
@mapbeat
def v_recap(c, x):
    cam = Cam("kanto", 139.2, 35.5, 0.55)
    mapframe(c, cam, x, dim=0.35)
    a = clamp(x.t / 0.4)
    t2 = x.L("f02")[0]
    big_title(c, "为什么几乎没打？", 460, 72, WHITE, a)
    icons = ["粮仓", "船队", "支城开城", "不拆的石头城"]
    for i, s in enumerate(icons):
        b = clamp((x.t - t2 - 1.5 - i * 1.4) / 0.4) if x.on("f02") else 0
        chip(c, s, W / 2, 680 + i * 150, b, [GOLDW, RED, CYAN, RED][i], 54)
    if x.on("f02b"):
        b = x.p("f02b", 0.5)
        card(c, 70, 1260, W - 140, 150, b, fa=0.9, border=GOLD)
        text(c, "老办法失效 · 你不会走 · 坚守失去意义", W / 2, 1352, 42, "serifbk", GOLD, b, "c")

def v_sunzi(c, x):
    paper_bg(c, dark=0.45)
    q0, q1 = x.L("f04")
    if x.t < q0:
        text(c, "两千多年前", W / 2, 700, 64, "serif", PAPER, clamp(x.t / 0.4), "c", shadow=8, spacing=10)
        text(c, "孙子", W / 2, 860, 120, "serifbk", GOLD, clamp((x.t - 0.3) / 0.4), "c", shadow=12, spacing=20)
    else:
        a = clamp((x.t - q0 + 0.3) / 0.5)
        quote_vertical(c, "不戰而屈人之兵，善之善者也。", "《孫子·謀攻》", a, size=92, top=420,
                       reveal=clamp((x.t - q0) / (q1 - q0 + 0.01) * 1.15))

def v_series(c, x):
    bg_grad(c, (28, 22, 16), (6, 5, 4))
    t = x.t
    k = eout(clamp(t / 4.0))
    # rising path from a small dot to a large castle
    pts = [(120, 1300), (330, 1220), (500, 1100), (650, 960), (820, 800), (930, 700)]
    arrow(c, pts, k, 30, GOLD, 1.0, glow=True, flow_t=t)
    c.drawCircle(120, 1300, 12, paint(WHITE, 1))
    text(c, "无名小卒", 90, 1370, 40, "sansm", WHITE, 1, "l")
    if k > 0.95:
        text(c, "天下人", 930, 640, 56, "serifbk", GOLD, clamp((t - 4) / 0.5), "c", shadow=10)
    text(c, "从无名小卒到天下人", W / 2, 430, 66, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
    text(c, "不靠一夜 · 靠把对手逼到没有选择", W / 2, 510, 42, "sansm", GOLD, clamp((t - 1.0) / 0.5), "c", stroke=6)
    if x.on("f07"):
        chip(c, "刀狩 + 检地 = 不必再打的规则", W / 2, 640, x.p("f07", 0.5), GOLD, 42)

def v_lesson(c, x):
    paper_bg(c, dark=0.55)
    a = clamp(x.t / 0.5)
    card(c, 80, 560, W - 160, 600, a, fa=0.86)
    lines = [("真正的胜利", WHITE), ("不是打赢最后一仗", WHITE), ("", WHITE), ("而是建立一套规则", GOLD), ("让下一仗不必再打", GOLD)]
    for i, (ln, colr) in enumerate(lines):
        pa = clamp((x.t - i * 0.6) / 0.5)
        text(c, ln, W / 2, 690 + i * 100, 66, "serifbk", colr, pa, "c")

def v_plain(c, x):
    c.drawRect(skia.Rect(0, 0, W, H), paint((10, 9, 9)))

@scenic
def v_osaka(c, x):
    t = x.t
    sky3(c, (4, 6, 14), (12, 16, 30), (30, 30, 46), 1150)
    stars(c, t, 0.7)
    c.drawCircle(200, 330, 46, paint((230, 226, 210), 0.85, blur=3)); c.drawCircle(200, 330, 140, paint((200, 200, 220), 0.12, blur=50))
    ridge(c, 61, 1120, 20, (16, 18, 26), 1.0, rough=0.1)
    c.save(); c.translate(W / 2, 1180); c.scale(0.9, 0.9); c.translate(-W / 2, -1180)
    castle(c, W / 2, 1180, 1.0, 1.0, 0.25, windows=0.35)
    c.restore()
    c.drawRect(skia.Rect(0, 1180, W, H), paint((6, 6, 10)))
    # leaf + dew drop
    q0, q1 = x.L("f11")
    lp = skia.Path(); lp.moveTo(80, 1440); lp.quadTo(300, 1320, 520, 1380); lp.quadTo(300, 1440, 80, 1440); lp.close()
    c.drawPath(lp, paint((30, 50, 40), 0.95))
    dd = clamp((t - q0 - 1.0) / 2.0) if t > q0 else 0
    dy = 1385 + 420 * ein(dd); da = 1 - clamp((dd - 0.9) / 0.1)
    c.drawCircle(520, dy, 14, paint((200, 220, 240), 0.9 * da)); c.drawCircle(516, dy - 4, 4, paint(WHITE, 0.9 * da))
    if t < q0:
        text(c, "1598 · 伏见城", W / 2, 470, 56, "serifbk", WHITE, clamp(t / 0.5), "c", shadow=10)
        text(c, "辞世", W / 2, 580, 90, "serifbk", PAPERL, clamp((t - 0.6) / 0.5), "c", shadow=12, spacing=30)
    else:
        a = clamp((t - q0 + 0.3) / 0.8)
        cols = ["露と落ち", "露と消えにし", "我が身かな", "浪速のことも", "夢のまた夢"]
        for i, s in enumerate(cols):
            ca = a * clamp((t - q0 - i * 1.0) / 0.8)
            vcol(c, s, 880 - i * 110, 300, 64, ca, PAPERL, "tcbk")
        text(c, "—— 丰臣秀吉 辞世", 900, 860, 34, "tc", GOLD, a, "r")
    # final fade to black
    end = clamp((t - (x.T - 2.0)) / 1.8)
    if end > 0: c.drawRect(skia.Rect(0, 0, W, H), paint((0, 0, 0), end))
