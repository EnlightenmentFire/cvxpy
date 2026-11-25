"""各场景。scene(t, D, ev) -> RGB 图（W×H）。t=场景内时间，D=场景时长，ev={句id: (相对起点, 时长)}。"""
import math, json, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from base import *

GEO = json.load(open("/tmp/claude-0/geo/china_geo.json"))


def at(ev, k, default=0.0):
    return ev[k][0] if k in ev else default


def tag(img, s, x=W - 40, y=232, anchor="rm"):
    """右上角标识：示意图 / 情景演绎。"""
    return draw_text(img, (x, y), s, font("sans", 30, "Medium"), fill=(200, 190, 170), anchor=anchor, shadow=3, alpha=0.85)


# ══════════ 客店夜景（钩子） ══════════
@functools.lru_cache(None)
def inn_static(variant=0):
    S = 1.18
    w, h = int(W * S), int(H * S)
    img = vgrad((6, 9, 20), (26, 24, 30), w, h, 0.9).copy().convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    for _ in range(260):
        x, y = rng.uniform(0, w), rng.uniform(0, h * 0.45)
        r = rng.uniform(0.6, 1.8); a = int(rng.uniform(60, 200))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 225, 240, a))
    # 月晕
    rgb = img.convert("RGB"); glow(rgb, w * 0.78, h * 0.14, 260, (60, 70, 96), 0.9)
    d2 = ImageDraw.Draw(rgb); d2.ellipse([w * 0.78 - 46, h * 0.14 - 46, w * 0.78 + 46, h * 0.14 + 46], fill=(214, 212, 196))
    img = rgb.convert("RGBA")
    img.alpha_composite(mountains(w, h, h * 0.50, h * 0.16, 5, (26, 30, 44, 255), rough=0.72, n=22))
    img.alpha_composite(mountains(w, h, h * 0.57, h * 0.12, 9, (15, 17, 26, 255), rough=0.7, n=22))
    d = ImageDraw.Draw(img)
    gc = (8, 8, 11, 255)
    # 关城：城墙 + 关楼（左侧）
    wy = h * 0.60
    d.rectangle([-10, wy, w * 0.52, h], fill=gc)
    for i in range(0, int(w * 0.52), 46):
        d.rectangle([i, wy - 26, i + 26, wy], fill=gc)
    tx = w * 0.22
    d.rectangle([tx - 150, wy - 190, tx + 150, wy], fill=gc)
    poly(d, [(tx - 230, wy - 190), (tx + 230, wy - 190), (tx + 160, wy - 270), (tx - 160, wy - 270)], gc)
    poly(d, [(tx - 260, wy - 186), (tx - 200, wy - 206), (tx - 160, wy - 196)], gc)
    poly(d, [(tx + 260, wy - 186), (tx + 200, wy - 206), (tx + 160, wy - 196)], gc)
    d.rectangle([tx - 110, wy - 330, tx + 110, wy - 270], fill=gc)
    poly(d, [(tx - 170, wy - 330), (tx + 170, wy - 330), (tx + 100, wy - 390), (tx - 100, wy - 390)], gc)
    # 城门洞
    d.rounded_rectangle([tx - 70, wy + 80, tx + 70, wy + 330], radius=70, fill=(20, 18, 16, 255))
    # 客舍（右侧）
    ix = w * 0.70; iy = h * 0.74
    d.rectangle([ix - 260, iy - 230, ix + 300, iy + 260], fill=(12, 11, 12, 255))
    poly(d, [(ix - 330, iy - 220), (ix + 370, iy - 220), (ix + 250, iy - 330), (ix - 210, iy - 330)], (9, 9, 10, 255))
    # 门与窗（暖光）
    d.rectangle([ix - 30, iy - 40, ix + 120, iy + 260], fill=(120, 70, 28, 255))
    d.rectangle([ix - 200, iy - 150, ix - 90, iy - 60], fill=(150, 92, 36, 255))
    for k in range(4):
        d.line([(ix - 200 + 27 * k + 14, iy - 150), (ix - 200 + 27 * k + 14, iy - 60)], fill=(30, 20, 12, 255), width=4)
    # 墙上的木牍法令
    bx, by = ix + 180, iy - 120
    d.rectangle([bx, by, bx + 92, by + 210], fill=(88, 66, 38, 255))
    f = font("serif", 30, "Bold", tc=True)
    for i, ch in enumerate("商君之法"):
        d.text((bx + 46, by + 26 + i * 40), ch, font=f, fill=(28, 18, 10, 255), anchor="mm")
    # 地面
    d.rectangle([w * 0.45, iy + 260, w, h], fill=(10, 9, 9, 255))
    rgb = img.convert("RGB")
    glow(rgb, ix + 45, iy + 110, 560, (150, 84, 26), 1.0)
    glow(rgb, ix - 145, iy - 105, 300, (140, 76, 22), 0.8)
    glow(rgb, ix - 60, iy + 420, 520, (70, 40, 14), 0.8)
    return rgb


def scene_inn(t, D, ev, variant=0):
    S = 1.18
    base = inn_static(0).copy()
    w, h = base.size
    d = ImageDraw.Draw(base, "RGBA")
    ix = w * 0.70; iy = h * 0.74
    # 灯笼摇曳
    sw = math.sin(t * 1.6) * 0.12
    lx, ly = ix + 45 + 110 * math.sin(sw), iy - 210
    d.line([(ix + 45, iy - 330), (lx, ly - 40)], fill=(10, 10, 10, 255), width=3)
    flick = 0.85 + 0.15 * math.sin(t * 9.0) * math.sin(t * 3.3)
    if variant == 3:
        flick *= 1 - ramp(t, D - 3.0, 2.0)
    d.ellipse([lx - 34, ly - 44, lx + 34, ly + 44], fill=(int(220 * flick), int(110 * flick), 30, 255))
    if flick > 0.05:
        glow(base, lx, ly, 200, (int(150 * flick), int(80 * flick), 20), 0.9)
    # 车马（关门外）
    hx, hy = w * 0.30, h * 0.90
    horse(d, hx, hy - 120, 210, (6, 6, 8, 255), 0, 0.3 + 0.05 * math.sin(t))
    d.rectangle([hx - 420, hy - 200, hx - 150, hy - 120], fill=(6, 6, 8, 255))
    d.ellipse([hx - 380, hy - 160, hx - 250, hy - 30], outline=(6, 6, 8, 255), width=12)
    d.line([(hx - 150, hy - 150), (hx - 60, hy - 140)], fill=(6, 6, 8, 255), width=10)
    # 人物背影（商鞅）与店主
    figure(d, ix - 150, iy + 300, 450, (4, 4, 6, 255))
    if variant in (0, 3):
        sh = 0.5 + 0.5 * math.sin(t * 2.2)
        figure(d, ix + 50, iy + 255, 300, (36, 22, 12, 255))
    d = None
    base = dust(base, t, n=70, seed=4, color=(200, 205, 220), speed=22, size=2.4, alpha=90)
    if variant == 2:
        img = kenburns(base, t, D, 1.12, 1.30, 0.66, 0.62, 0.72, 0.66)
    elif variant == 3:
        img = kenburns(base, t, D, 1.0, 1.06, 0.55, 0.55, 0.6, 0.6)
        k = 0.35 * ramp(t, 0, D)
        g = img.convert("L").convert("RGB")
        img = Image.blend(img, g, k)
    else:
        img = kenburns(base, t, D, 1.0, 1.10, 0.52, 0.56, 0.62, 0.62)
    img = tag(img, "情景演绎")
    if variant == 2:
        # 法令特写：墙上木牍「舍人無驗者坐之」
        f = font("serif", 46, "Bold", tc=True)
        a = ramp(t, 0.2, 0.8)
        im = slip_card(["舍人無驗者坐之", "商君之法"], f, w_slip=92, h=470, seed=21)
        paste_center(img, im, W * 0.5, 1070, alpha=a * 0.96)
    return img


# ══════════ 人亡法存 ══════════
def scene_death(t, D, ev):
    img = vgrad((18, 6, 6), (4, 3, 3)).copy()
    glow(img, W / 2, 880, 700, (70, 16, 10), 0.8)
    d = ImageDraw.Draw(img, "RGBA")
    k_dis = ramp(t, 0.5, 4.5)
    # 左：人物剪影化为灰烬
    fx, fy = W * 0.30, 1320
    rng = np.random.default_rng(3)
    if k_dis < 1:
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        figure(ImageDraw.Draw(tmp), fx, fy, 560, (30, 24, 22, 255))
        a = tmp.getchannel("A").point(lambda v: int(v * (1 - k_dis)))
        tmp.putalpha(a); img.paste(tmp, (0, 0), tmp)
    for i in range(240):
        px = fx + rng.uniform(-110, 110); py = fy - rng.uniform(0, 560)
        dt = k_dis * rng.uniform(0.4, 1.0)
        x = px + dt * rng.uniform(40, 260); y = py - dt * rng.uniform(80, 420)
        a = int(200 * clamp(k_dis * 3) * (1 - dt))
        r = rng.uniform(1.5, 4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(220, 120, 60, max(0, a)))
    # 右：竹简（法）愈来愈亮
    k = ramp(t, 1.0, 4.0)
    f = font("serif", 50, "Bold", tc=True)
    sc = slip_card(["什伍連坐", "軍功受爵", "耕織復身", "集鄉為縣"], f, w_slip=96, h=600, seed=31)
    paste_center(img, sc, W * 0.70, 1000, alpha=0.6 + 0.4 * k, scale=0.82)
    glow(img, W * 0.70, 1000, 380, (90, 60, 20), 0.5 * k)
    if t > at(ev, "a06", 99) + 0.3:
        a = ramp(t, at(ev, "a06") + 0.3, 0.8)
        img = draw_text(img, (W * 0.30, 640), "人亡", font("serif", 110, "Black"), fill=(170, 160, 150), alpha=a)
        img = draw_text(img, (W * 0.70, 560), "法存", font("serif", 110, "Black"), fill=GOLD2, alpha=a)
    img = draw_text(img, (W / 2, 330), "公元前338年", font("serif", 60, "Bold"), fill=(220, 190, 170), alpha=ramp(t, 0.1, 0.6))
    return img


# ══════════ 时间轴 ══════════
TL = [(-361, "秦孝公即位"), (-356, "第一次变法"), (-350, "第二次变法"), (-338, "商鞅被杀  法令未废"), (-221, "秦统一六国")]


def scene_timeline(t, D, ev, mode="full"):
    img = vgrad((12, 10, 10), (22, 16, 12)).copy()
    glow(img, W / 2, 1000, 800, (40, 28, 14), 0.7)
    d = ImageDraw.Draw(img, "RGBA")
    y0, y1 = 420, 1340
    order = [yr for yr, _ in TL]
    def Y(yr): return y0 + order.index(yr) / (len(order) - 1) * (y1 - y0)
    x = 300
    k = ramp(t, 0.2, max(2.0, D * 0.55))
    d.line([(x, y0), (x, lerp(y0, y1, k))], fill=GOLD + (230,), width=6)
    for i, (yr, lab) in enumerate(TL):
        yy = Y(yr)
        if yy > lerp(y0, y1, k) + 2:
            continue
        a = clamp((lerp(y0, y1, k) - yy) / 60)
        c = RED2 if yr == -338 else GOLD2
        d.ellipse([x - 16, yy - 16, x + 16, yy + 16], fill=c + (int(255 * a),))
        img = draw_text(img, (x - 40, yy), f"前{-yr}", font("serif", 46, "Bold"), fill=c, anchor="rm", alpha=a)
        img = draw_text(img, (x + 50, yy), lab, font("serif", 50, "Bold"), fill=PAPER, anchor="lm", alpha=a)
        d = ImageDraw.Draw(img, "RGBA")
    if k > 0.95:
        a = ramp(t, 0.2 + max(2.0, D * 0.55), 0.8)
        ya, yb = Y(-338), Y(-221)
        d.line([(x + 30, ya + 30), (x + 30, yb - 30)], fill=RED2 + (int(200 * a),), width=4)
        img = draw_text(img, (x + 420, (ya + yb) / 2 + 10), "117年", font("serif", 120, "Black"), fill=RED2, alpha=a)
    return img


# ══════════ 机器 / 三根杠杆 ══════════
def gear(d, cx, cy, r, teeth, ang, color, width=0):
    pts = []
    for i in range(teeth * 2):
        a = ang + i * math.pi / teeth
        rr = r if i % 2 == 0 else r * 0.86
        a2 = a + math.pi / teeth
        pts += [(cx + rr * math.cos(a), cy + rr * math.sin(a)), (cx + rr * math.cos(a2 - 0.02), cy + rr * math.sin(a2 - 0.02))]
    d.polygon(pts, fill=color)
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.55, cy + r * 0.55], fill=(14, 12, 10, 255))
    d.ellipse([cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18], fill=color)


GEARS = [(540, 860, 230, 18, "军功爵"), (250, 1120, 150, 12, "耕织"), (830, 1130, 160, 12, "什伍"), (560, 1370, 120, 10, "县制")]


def scene_machine(t, D, ev, labels=True, ghost=True):
    img = vgrad((14, 12, 10), (24, 18, 12)).copy()
    glow(img, W / 2, 1000, 760, (60, 40, 16), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    sp = 0.35
    for i, (x, y, r, n, lab) in enumerate(GEARS):
        dirn = 1 if i % 2 == 0 else -1
        ang = dirn * t * sp * (230 / r)
        gear(d, x, y, r, n, ang, (150, 108, 58, 255))
        d.ellipse([x - r * 0.55, y - r * 0.55, x + r * 0.55, y + r * 0.55], outline=(200, 160, 90, 120), width=3)
        if labels:
            img = draw_text(img, (x, y), lab, font("serif", int(r * 0.26), "Bold"), fill=GOLD2, shadow=4)
            d = ImageDraw.Draw(img, "RGBA")
    if ghost:
        # 机器中央曾经站着的人：虚线轮廓，逐渐淡去
        a = 1 - ramp(t, 0.5, D * 0.8)
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        figure(ImageDraw.Draw(tmp), 540, 640, 380, (230, 220, 200, 255))
        edge = tmp.filter(ImageFilter.FIND_EDGES)
        al = edge.getchannel("A").point(lambda v: int(min(255, v * 2) * 0.7 * a))
        edge.putalpha(al)
        img.paste(edge, (0, 0), edge)
    return img


@functools.lru_cache(None)
def city_static():
    """咸阳城俯瞰（示意）：城墙、街坊、宫城、渭水、灯火。"""
    img = vgrad((20, 18, 14), (10, 9, 7)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, 1020
    R = 380
    rng = np.random.default_rng(5)
    # 城外田野
    for i in range(-12, 13):
        for j in range(-14, 15):
            x, y = cx + i * 70, cy + j * 70
            if abs(i * 70) > R + 30 or abs(j * 70) > R + 30:
                c = int(rng.uniform(14, 22))
                d.rectangle([x - 32, y - 32, x + 32, y + 32], fill=(c + 3, c + 4, c - 3, 255))
    d.rectangle([cx - R, cy - R, cx + R, cy + R], fill=(28, 24, 18, 255))
    # 坊：大小不一的屋顶块
    for _ in range(900):
        x = rng.uniform(cx - R + 20, cx + R - 20); y = rng.uniform(cy - R + 20, cy + R - 20)
        if abs(x - cx) < 26 or abs(y - cy) < 26 or (abs(x - cx) < 150 and cy - 330 < y < cy - 90):
            continue
        w2, h2 = rng.uniform(8, 22), rng.uniform(6, 16)
        c = int(rng.uniform(46, 86))
        d.rectangle([x - w2, y - h2, x + w2, y + h2], fill=(c + 12, c, c - 14, 255))
    # 主街（十字）
    d.rectangle([cx - 16, cy - R, cx + 16, cy + R], fill=(86, 70, 46, 255))
    d.rectangle([cx - R, cy - 16, cx + R, cy + 16], fill=(86, 70, 46, 255))
    # 宫城与冀阙
    d.rectangle([cx - 140, cy - 330, cx + 140, cy - 90], fill=(70, 48, 28, 255), outline=(200, 160, 90, 255), width=5)
    d.rectangle([cx - 90, cy - 280, cx + 90, cy - 170], fill=(120, 80, 40, 255))
    d.line([(cx - 90, cy - 225), (cx + 90, cy - 225)], fill=(60, 36, 18, 255), width=4)
    for sx in (-1, 1):
        d.rectangle([cx + sx * 60 - 18, cy - 110, cx + sx * 60 + 18, cy - 70], fill=(150, 100, 50, 255))
    # 城墙与城门
    d.rectangle([cx - R, cy - R, cx + R, cy + R], outline=(160, 128, 76, 255), width=16)
    for (gx, gy) in [(cx, cy - R), (cx, cy + R), (cx - R, cy), (cx + R, cy)]:
        d.rectangle([gx - 34, gy - 34, gx + 34, gy + 34], fill=(120, 90, 50, 255))
    # 渭水
    pts = [(-20, cy + R + 150), (300, cy + R + 110), (600, cy + R + 170), (1100, cy + R + 100)]
    d.line(pts, fill=(56, 76, 98, 255), width=46, joint="curve")
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    for _ in range(70):
        x = rng.uniform(cx - R + 30, cx + R - 30); y = rng.uniform(cy - R + 30, cy + R - 30)
        glow(img, x, y, 22, (120, 70, 20), 0.8)
    glow(img, cx, cy - 210, 260, (90, 56, 18), 0.6)
    return img


def lever_icon(img, kind, x, y, a):
    d = ImageDraw.Draw(img, "RGBA")
    c = GOLD2 + (int(255 * a),)
    if kind == 0:  # 木柱
        d.rectangle([x - 12, y - 90, x + 12, y + 90], fill=c)
    elif kind == 1:  # 阶梯
        for i in range(5):
            d.rectangle([x - 90 + i * 36, y + 60 - i * 34, x - 90 + (i + 1) * 36, y + 80], fill=c)
    else:  # 网格
        for i in range(-2, 3):
            d.line([(x - 90, y + i * 36), (x + 90, y + i * 36)], fill=c, width=5)
            d.line([(x + i * 36, y - 90), (x + i * 36, y + 90)], fill=c, width=5)


def scene_levers(t, D, ev):
    base = city_static().copy()
    img = kenburns(base, t, D, 1.0, 1.06)
    img = tag(img, "示意")
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, 1020
    T0 = at(ev, "a12", 0.0)
    pos = [(190, 420, "信用", "信"), (540, 340, "激励", "赏"), (890, 420, "信息", "察")]
    for i, (x, y, lab, ch) in enumerate(pos):
        k = ramp(t, T0 + 1.4 + i * 0.9, 0.8)
        if k <= 0:
            continue
        # 光线
        for wdt, al in [(26, 40), (12, 90), (4, 230)]:
            d.line([(cx, cy - 120), (lerp(cx, x, k), lerp(cy - 120, y + 120, k))], fill=GOLD2 + (int(al * k),), width=wdt)
        lever_icon(img, i, x, y, k)
        img = draw_text(img, (x, y - 150), lab, font("serif", 64, "Black"), fill=GOLD2, alpha=k)
        d = ImageDraw.Draw(img, "RGBA")
    if t < T0 + 0.2:
        img = draw_text(img, (W / 2, 470), "咸阳", font("serif", 60, "Bold"), fill=(200, 180, 140), alpha=0.6)
    return img


# ══════════ 地图（示意） ══════════
MAPB = (104.0, 29.6, 121.2, 41.2)
MAPBOX = (30, 300, 1050, 1380)


def proj(lon, lat, box=MAPBOX, b=MAPB):
    x0, y0, x1, y1 = box
    kx = (x1 - x0) / ((b[2] - b[0]) * math.cos(math.radians(35)))
    ky = (y1 - y0) / (b[3] - b[1])
    k = min(kx, ky)
    cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    cl, ca = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return cxp + (lon - cl) * math.cos(math.radians(35)) * k, cyp - (lat - ca) * k


PLACES = {"秦": (107.6, 34.6), "魏": (113.6, 35.4), "韩": (113.0, 34.0), "赵": (114.0, 37.4), "齐": (118.2, 36.4),
          "楚": (113.5, 31.4), "燕": (116.0, 39.9)}
CITIES = {"咸阳": (108.7, 34.33), "安邑": (111.0, 35.1), "大梁": (114.35, 34.8), "商": (110.0, 33.85), "雍": (107.4, 34.5)}


@functools.lru_cache(None)
def map_static(box=MAPBOX):
    img = vgrad((16, 15, 12), (10, 9, 8)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    # 底纹：经纬淡线
    for lon in range(104, 122, 2):
        d.line([proj(lon, MAPB[1], box), proj(lon, MAPB[3], box)], fill=(255, 240, 200, 10), width=1)
    for lat in range(30, 42, 2):
        d.line([proj(MAPB[0], lat, box), proj(MAPB[2], lat, box)], fill=(255, 240, 200, 10), width=1)
    for seg in GEO["coast"]:
        pts = [proj(*p, box) for p in seg]
        if len(pts) > 1:
            d.line(pts, fill=(120, 110, 90, 200), width=3)
    for r in GEO["rivers"]:
        if r["n"] in ("Yellow", "Wei", "Yangtze", "Han", "Huai", "Fen", "Luo", "Jing"):
            pts = [proj(*p, box) for p in r["pts"]]
            wdt = 7 if r["n"] in ("Yellow", "Yangtze") else 4
            d.line(pts, fill=(70, 100, 128, 230), width=wdt, joint="curve")
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    for nm, (lon, lat) in [("黄河", (111.2, 38.6)), ("渭水", (106.6, 34.75)), ("长江", (116.5, 30.3))]:
        img = draw_text(img, proj(lon, lat, box), nm, font("serif", 30, "Medium"), fill=(110, 140, 170), shadow=0)
    return img


def hexi_poly(box=MAPBOX):
    pts = [(110.45, 36.6), (110.55, 35.3), (110.2, 34.6), (109.5, 34.75), (109.6, 35.6), (109.9, 36.5)]
    return [proj(*p, box) for p in pts]


def draw_states(img, a=1.0, qin_k=0.0, box=MAPBOX):
    for nm, (lon, lat) in PLACES.items():
        x, y = proj(lon, lat, box)
        c = RED2 if nm == "秦" else (190, 170, 130)
        if nm == "秦":
            glow(img, x, y, int(lerp(170, 260, qin_k)), (90, 22, 14), 0.9 * a)
        img = draw_text(img, (x, y), nm, font("serif", 78 if nm == "秦" else 60, "Black", tc=True), fill=c, alpha=a)
    return img


def scene_map(t, D, ev, mode=1):
    img = kenburns(map_static(), t, D, 1.0, 1.08, 0.5, 0.5, 0.44, 0.48)
    img = img.copy()
    img = draw_states(img, 1.0, ramp(t, 0, D))
    d = ImageDraw.Draw(img, "RGBA")
    img = tag(img, "战国形势示意  约前361年")
    if mode == 1:
        k = ramp(t, at(ev, "b02", 0) + 1.0, 1.0)
        hp = hexi_poly()
        d.polygon(hp, fill=(160, 150, 130, int(110 * k)), outline=(220, 200, 150, int(255 * k)))
        hx = sum(p[0] for p in hp) / len(hp); hy = sum(p[1] for p in hp) / len(hp)
        img = draw_text(img, (hx + 10, hy - 140), "河西之地", font("serif", 46, "Bold"), fill=PAPER, alpha=k)
        img = draw_text(img, (hx + 10, hy - 88), "（为魏所占）", font("serif", 34, "Medium"), fill=(200, 190, 170), alpha=k)
        d = ImageDraw.Draw(img, "RGBA")
        k2 = ramp(t, at(ev, "b03", 99) + 0.8, 1.6)
        if k2 > 0:
            arrow(d, proj(108.4, 34.4), proj(110.3, 35.6), RED2 + (240,), 16, 50, k2)
    else:
        k = ramp(t, 0.6, D * 0.6)
        path = [proj(*p) for p in [(111.0, 35.1), (110.3, 34.75), (109.3, 34.5), (108.7, 34.33)]]
        path_arrow(d, path, GOLD2 + (255,), 12, 44, k)
        x, y = proj(111.0, 35.1)
        img = draw_text(img, (x + 20, y - 60), "魏", font("serif", 40, "Bold"), fill=GOLD2)
        img = draw_text(img, (W / 2, 1300), "卫鞅西行入秦", font("serif", 56, "Bold"), fill=GOLD2, alpha=ramp(t, 0.8, 0.8))
    return img


# ══════════ 四见孝公 ══════════
@functools.lru_cache(None)
def palace_static():
    img = vgrad((26, 16, 10), (10, 7, 5)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    for x in (120, 960):
        d.rectangle([x - 46, 260, x + 46, 1500], fill=(46, 22, 12, 255))
        d.rectangle([x - 60, 1480, x + 60, 1520], fill=(40, 20, 10, 255))
    d.rectangle([0, 230, W, 300], fill=(36, 18, 10, 255))
    d.rectangle([0, 1500, W, H], fill=(20, 12, 8, 255))
    for i in range(0, W, 90):
        d.line([(i, 1500), (W / 2 + (i - W / 2) * 2.4, H)], fill=(40, 24, 14, 255), width=2)
    glow(img, W / 2, 700, 600, (90, 50, 18), 0.6)
    return img


def scene_audience(t, D, ev):
    img = palace_static().copy()
    d = ImageDraw.Draw(img, "RGBA")
    labs = [("帝道", "b05", 0.0), ("王道", "b06", 0.0), ("霸道", "b06", 0.5), ("强国之术", "b07", 0.0)]
    f = font("serif", 50, "Bold")
    for i, (lab, k_id, frac) in enumerate(labs):
        st = at(ev, k_id, 99) + frac * ev.get(k_id, (0, 4))[1] + (1.6 if i == 0 else 0)
        a = ramp(t, st, 0.6)
        if a <= 0:
            continue
        x = 180 + i * 240
        is_last = i == 3
        sl = slip(110, 520, seed=40 + i)
        paste_center(img, sl, x, 720, alpha=a)
        vtext(img, x, 520, lab, f, fill=(40, 24, 12) if not is_last else (120, 20, 10), alpha=a)
        d = ImageDraw.Draw(img, "RGBA")
        mark = ["困", "未入", "善之", "大悦"][i]
        img = draw_text(img, (x, 1030), mark, font("serif", 44, "Bold"), fill=(RED2 if is_last else (170, 160, 150)), alpha=a)
        if is_last:
            glow(img, x, 720, 260, (110, 60, 20), 0.7 * a)
    # 孝公剪影（前倾）
    lean = ramp(t, at(ev, "b07", 99) + 1.5, 2.0)
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    figure(ImageDraw.Draw(tmp), 0, 0 + 0, 1, (0, 0, 0, 0))
    td = ImageDraw.Draw(img, "RGBA")
    td.rectangle([300, 1330, 780, 1380], fill=(30, 16, 8, 255))
    figure(td, 540 + 40 * lean, 1340, 300, (8, 5, 4, 255), kind="crown")
    if t > at(ev, "b08", 99):
        a = ramp(t, at(ev, "b08", 99) + 0.5, 0.7)
        img = draw_text(img, (W / 2, 1180), "帝王之道：数十百年", font("serif", 48, "Bold"), fill=(170, 160, 150), alpha=a)
        img = draw_text(img, (W / 2, 1250), "强国之术：立见其效", font("serif", 48, "Bold"), fill=GOLD2, alpha=ramp(t, at(ev, "b08", 99) + 1.5, 0.7))
    return img


# ══════════ 廷辩：大殿俯拍 + 竹简对撞 ══════════
@functools.lru_cache(None)
def hall_static():
    img = vgrad((22, 16, 12), (14, 10, 8)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(-10, 12):
        for j in range(-2, 22):
            x, y = 540 + i * 110 + (j % 2) * 55, 200 + j * 90
            d.rectangle([x - 50, y - 40, x + 50, y + 40], fill=(34 + (i + j) % 3 * 4, 26, 20, 255))
    for side in (-1, 1):
        for j in range(5):
            x, y = 540 + side * 400, 420 + j * 280
            d.ellipse([x - 40, y - 40, x + 40, y + 40], fill=(70, 30, 18, 255), outline=(120, 70, 30, 255), width=4)
        for j in range(6):
            x, y = 540 + side * 250, 520 + j * 150
            d.ellipse([x - 28, y - 28, x + 28, y + 28], fill=(30, 24, 30, 255) if side < 0 else (40, 20, 14, 255))
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(10, 8, 8, 255))
    d.rectangle([340, 230, 740, 330], fill=(60, 30, 16, 255), outline=(160, 110, 50, 255), width=4)
    glow(img, 540, 280, 260, (100, 60, 20), 0.6)
    return img


def scene_debate(t, D, ev):
    img = kenburns(hall_static(), t, D, 1.04, 1.12, 0.5, 0.5, 0.5, 0.46).copy()
    f = font("serif", 52, "Bold", tc=True)
    tL = at(ev, "b11", 0.5); tR = at(ev, "b13", D * 0.6)
    kL = ease_out((t - tL) / 1.2)
    kR = ease_out((t - tR) / 1.0)
    left = slip_card(["法古無過", "循禮無邪"], f, w_slip=100, h=480, seed=50, fill=(30, 36, 50))
    right = slip_card(["治世不一道", "便國不法古"], f, w_slip=100, h=560, seed=60, fill=(120, 20, 10))
    y = 920
    hit = t - (tR + 1.0)
    shake = 10 * math.exp(-max(0, hit) * 6) * math.sin(hit * 60) if hit > 0 else 0
    if kL > 0:
        paste_center(img, left, lerp(-200, 330, kL) + (shake if hit > 0 else 0), y, alpha=clamp(kL * 2))
        img = draw_text(img, (lerp(-200, 330, kL), y - 330), "甘龙 · 杜挚", font("serif", 40, "Bold"), fill=(150, 170, 200), alpha=clamp(kL * 2))
    if kR > 0:
        paste_center(img, right, lerp(W + 200, 760, kR) - shake, y, alpha=clamp(kR * 2))
        img = draw_text(img, (lerp(W + 200, 760, kR), y - 370), "卫鞅", font("serif", 44, "Bold"), fill=GOLD2, alpha=clamp(kR * 2))
    if 0 < hit < 1.2:
        glow(img, 545, y, int(300 + 200 * hit), (200, 140, 60), 1.2 * (1 - hit / 1.2))
    return img


def scene_debate2(t, D, ev):
    img = vgrad((16, 12, 10), (8, 6, 6)).copy()
    glow(img, W / 2, 900, 700, (50, 30, 14), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    f = font("serif", 64, "Black")
    # 两种标准
    tb = at(ev, "b16", 0)
    k = ramp(t, tb + 0.8, 2.0)
    img = draw_text(img, (W * 0.28, 640), "合不合古", f, fill=mix((220, 210, 190), (90, 86, 80), k))
    img = draw_text(img, (W * 0.72, 640), "利不利国", f, fill=mix((120, 110, 90), GOLD2, k))
    img = draw_text(img, (W * 0.28, 730), "懂古礼的老臣", font("serif", 40, "Medium"), fill=(150, 140, 130))
    img = draw_text(img, (W * 0.72, 730), "拿出结果的人", font("serif", 40, "Medium"), fill=(200, 170, 120))
    img = draw_text(img, (W / 2, 470), "谁有资格解释什么是对的？", font("serif", 52, "Bold"), fill=PAPER, alpha=ramp(t, 0.6, 0.8))
    # 解释权之印 从左移到右
    s = seal("解釋之權", 200)
    x = lerp(W * 0.28, W * 0.72, k)
    paste_center(img, s, x, 940, alpha=0.95)
    # 变法之令
    t19 = at(ev, "b19", 99)
    if t > t19:
        a = ramp(t, t19 + 0.6, 0.5)
        sc = 1.6 - 0.6 * ease_out((t - t19 - 0.6) / 0.35)
        paste_center(img, seal("變法之令", 240), W / 2, 1180, alpha=a, scale=sc)
    t20 = at(ev, "b20", 99)
    if t > t20:
        img = draw_text(img, (W / 2, 1390), "前356 第一次变法  ·  前350 第二次变法", font("serif", 40, "Bold"), fill=GOLD2, alpha=ramp(t, t20 + 0.5, 0.7))
    return img


# ══════════ 徙木立信 ══════════
@functools.lru_cache(None)
def pole_static():
    img = vgrad((30, 22, 14), (12, 9, 7)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    # 透视大道：南门（下）→ 北门（上）
    d.polygon([(470, 470), (610, 470), (1000, 1700), (80, 1700)], fill=(60, 46, 30, 255))
    for k in range(18):
        y = 470 + (1700 - 470) * (k / 18) ** 1.4
        d.line([(540 - (k + 1) * 26, y), (540 + (k + 1) * 26, y)], fill=(70, 54, 36, 255), width=2)
    # 北门（远）
    def gate(cx, cy, s, c):
        d.rectangle([cx - 160 * s, cy - 110 * s, cx + 160 * s, cy], fill=c)
        d.polygon([(cx - 210 * s, cy - 110 * s), (cx + 210 * s, cy - 110 * s), (cx + 140 * s, cy - 170 * s), (cx - 140 * s, cy - 170 * s)], fill=c)
        d.rounded_rectangle([cx - 50 * s, cy - 80 * s, cx + 50 * s, cy], radius=int(40 * s), fill=(90, 60, 30, 255))
        d.rectangle([0 if cx < 600 else cx, cy - 60 * s, cx - 160 * s, cy], fill=c) if False else None
    gate(540, 470, 0.7, (20, 14, 10, 255))
    d.rectangle([0, 1640, W, H], fill=(16, 11, 8, 255))
    gate(540, 1700, 1.6, (14, 10, 8, 255))
    img = draw_text(img, (540, 340), "北门", font("serif", 44, "Bold"), fill=(190, 170, 130))
    img = draw_text(img, (540, 1810), "南门", font("serif", 44, "Bold"), fill=(190, 170, 130))
    glow(img, 540, 1000, 520, (70, 46, 20), 0.5)
    return img


def scene_pole(t, D, ev):
    img = pole_static().copy()
    d = ImageDraw.Draw(img, "RGBA")
    t5 = at(ev, "c05", 99)
    carry = ramp(t, t5 + 2.2, 3.5) if t5 < 99 else 0
    # 木头位置沿大道上移，并随透视变小
    y = lerp(1450, 560, carry)
    s = lerp(1.0, 0.35, carry)
    if carry > 0:
        figure(d, 540 + 20 * s, y + 10, 210 * s, (10, 7, 5, 255))
        d.line([(540 - 170 * s, y - 180 * s), (540 + 210 * s, y - 120 * s)], fill=(120, 80, 40, 255), width=int(26 * s) + 2)
    else:
        d.rectangle([528, 1450 - 520, 552, 1450], fill=(120, 80, 40, 255))
        d.rectangle([500, 1440, 580, 1460], fill=(60, 40, 20, 255))
        rng = np.random.default_rng(9)
        for i in range(14):
            x = 540 + rng.uniform(-380, 380); yy = 1500 + rng.uniform(-40, 120)
            figure(d, x, yy, 160, (18, 12, 9, 255))
    # 赏金
    t4 = at(ev, "c04", 0)
    if t > t4 + 2.0:
        reward = "十金" if t < t5 + 1.0 else "五十金"
        k = ramp(t, t4 + 2.0, 0.5)
        pop = 1 + 0.25 * math.exp(-max(0, t - t5 - 1.0) * 5) if t > t5 + 1.0 else 1
        img = draw_text(img, (850, 820), reward, font("serif", int(86 * pop), "Black"), fill=GOLD2, alpha=k)
    if t5 < 99 and t > t5 + 6.0:
        paste_center(img, seal("以明不欺", 220), 230, 820, alpha=ramp(t, t5 + 6.0, 0.4), scale=1.3 - 0.3 * ease_out((t - t5 - 6.0) / 0.3))
    return img


def scene_pole2(t, D, ev):
    """昂贵的信号：成本条 vs 可信度条。"""
    img = vgrad((18, 14, 10), (8, 7, 6)).copy()
    glow(img, W / 2, 900, 650, (60, 40, 16), 0.6)
    d = ImageDraw.Draw(img, "RGBA")
    t6 = at(ev, "c06", 0)
    k = ramp(t, t6 + 1.0, 3.0)
    bars = [("承诺的成本", k, GOLD), ("别人的信任", ramp(t, t6 + 2.5, 3.5), RED2)]
    for i, (lab, v, c) in enumerate(bars):
        y = 780 + i * 220
        d.rounded_rectangle([200, y - 40, 900, y + 40], radius=40, outline=(120, 100, 70, 255), width=3)
        d.rounded_rectangle([200, y - 40, 200 + 700 * max(0.06, v), y + 40], radius=40, fill=c + (230,))
        img = draw_text(img, (200, y - 90), lab, font("serif", 46, "Bold"), fill=PAPER, anchor="lm")
        d = ImageDraw.Draw(img, "RGBA")
    t7 = at(ev, "c07", 99)
    if t > t7:
        img = draw_text(img, (W / 2, 1250), "昂贵的信号", font("serif", 88, "Black"), fill=GOLD2, alpha=ramp(t, t7 + 0.3, 0.6))
        img = draw_text(img, (W / 2, 1345), "costly signal", font("serif", 40, "Medium"), fill=(170, 160, 140), alpha=ramp(t, t7 + 0.6, 0.6))
    return img


# ══════════ 太子犯法 ══════════
def scene_prince(t, D, ev):
    img = palace_static().copy()
    d = ImageDraw.Draw(img, "RGBA")
    t11 = at(ev, "c11", 99)
    xs = [(270, "公子虔", "太子之傅"), (540, "太子", "储君"), (810, "公孙贾", "太子之师")]
    for i, (x, nm, role) in enumerate(xs):
        col = (10, 6, 5, 255)
        figure(d, x, 1260, 420 if i == 1 else 380, col, kind="crown" if i == 1 else "robe")
        if i == 1:
            glow(img, x, 1000, 250, (110, 80, 30), 0.5)
        img = draw_text(img, (x, 1320), nm, font("serif", 48, "Bold"), fill=(RED2 if (i == 0 and t > t11) else PAPER))
        img = draw_text(img, (x, 1380), role, font("serif", 34, "Medium"), fill=(170, 160, 140))
        d = ImageDraw.Draw(img, "RGBA")
    if t > t11 + 1.2:
        a = ramp(t, t11 + 1.2, 0.4)
        img = draw_text(img, (270, 780), "刑", font("serif", 120, "Black"), fill=RED2, alpha=a)
    if t > t11 + 3.0:
        a = ramp(t, t11 + 3.0, 0.4)
        img = draw_text(img, (810, 780), "黥", font("serif", 120, "Black", tc=True), fill=RED2, alpha=a)
    if t > t11 - 4 and t11 < 99:
        a = ramp(t, at(ev, "c09", 0) + 0.3, 0.5)
        img = draw_text(img, (540, 690), "太子犯法", font("serif", 70, "Black"), fill=GOLD2, alpha=a * (1 - ramp(t, t11 + 1.0, 0.5)))
    t12 = at(ev, "c12", 99)
    if t > t12:
        img = draw_text(img, (W / 2, 580), "明日，秦人皆趨令", font("serif", 54, "Bold", tc=True), fill=GOLD2, alpha=ramp(t, t12 + 0.2, 0.6))
    return img


def scene_prince2(t, D, ev):
    img = vgrad((16, 12, 10), (8, 6, 5)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    k1 = ramp(t, 0.6, 0.6); k2 = ramp(t, 2.6, 0.6)
    d.rectangle([258, 620, 282, 1040], fill=(140, 92, 46, int(255 * k1)))
    img = draw_text(img, (270, 1100), "赏是真的", font("serif", 50, "Bold"), fill=GOLD2, alpha=k1)
    d = ImageDraw.Draw(img, "RGBA")
    figure(d, 810, 1040, 400, (60, 20, 14, int(255 * k2)))
    img = draw_text(img, (810, 1100), "罚也是真的", font("serif", 50, "Bold"), fill=RED2, alpha=k2)
    d = ImageDraw.Draw(img, "RGBA")
    kf = ramp(t, 4.6, 1.5)
    d.rounded_rectangle([240, 1210, 840, 1270], radius=30, outline=(160, 130, 80, 255), width=3)
    d.rounded_rectangle([240, 1210, 240 + 600 * max(0.05, kf), 1270], radius=30, fill=GOLD + (230,))
    img = draw_text(img, (540, 1160), "信用", font("serif", 52, "Black"), fill=PAPER)
    t14 = at(ev, "c14", 99)
    if t > t14:
        a = ramp(t, t14 + 0.6, 0.6)
        img = draw_text(img, (W / 2, 1390), "公子虔 —— 怨", font("serif", 66, "Black"), fill=RED2, alpha=a)
    return img


# ══════════ 激励：爵位阶梯 ══════════
def scene_ladder(t, D, ev, mode=1):
    img = vgrad((18, 12, 8), (6, 5, 4)).copy()
    glow(img, W / 2, 500, 700, (90, 60, 20), 0.5)
    d = ImageDraw.Draw(img, "RGBA")
    n = 12
    k = ramp(t, 0.3, 3.0)
    for i in range(n):
        if i / n > k:
            break
        x0 = 120 + i * 62; y = 1480 - i * 82
        c = mix((80, 60, 36), GOLD2, i / n)
        d.rectangle([x0, y, x0 + 62, 1480 + 60], fill=c + (255,))
        d.line([(x0, y), (x0 + 62, y)], fill=(255, 230, 170, 200), width=3)
    # 攀登者
    for j in range(5):
        p = (t * 0.06 + j * 0.19) % 1.0
        i = p * (n - 1) * k
        x = 150 + i * 62; y = 1480 - int(i) * 82
        figure(d, x, y, 120, (12, 8, 5, 255))
    img = draw_text(img, (250, 560), "军功", font("serif", 80, "Black"), fill=RED2, alpha=ramp(t, 1.0, 0.6))
    img = draw_text(img, (250, 660), "↓", font("sans", 60, "Bold"), fill=PAPER, alpha=ramp(t, 1.4, 0.6))
    img = draw_text(img, (250, 760), "爵位", font("serif", 80, "Black"), fill=GOLD2, alpha=ramp(t, 1.8, 0.6))
    if mode == 1:
        t4 = at(ev, "d04", 99)
        if t > t4:
            a = ramp(t, t4 + 0.4, 0.6)
            dd = ImageDraw.Draw(img, "RGBA")
            figure(dd, 760, 1390, 220, (120, 92, 52, int(255 * a)), kind="crown")
            img = draw_text(img, (760, 1060), "宗室无军功", font("serif", 46, "Bold"), fill=(200, 180, 150), alpha=a)
            img = draw_text(img, (760, 1120), "不得为属籍", font("serif", 46, "Bold"), fill=RED2, alpha=a)
        t5 = at(ev, "d05", 99)
        if t > t5:
            a = ramp(t, t5 + 0.5, 0.6)
            img = draw_text(img, (W / 2, 330), "出身  →  功劳", font("serif", 72, "Black"), fill=GOLD2, alpha=a)
    else:
        items = ["田", "宅", "臣妾", "衣服"]
        for i, it in enumerate(items):
            a = ramp(t, 1.0 + i * 0.5, 0.5)
            x = 170 + (i % 2) * 200; yy = 900 + (i // 2) * 200
            dd = ImageDraw.Draw(img, "RGBA")
            dd.ellipse([x - 80, yy - 80, x + 80, yy + 80], fill=(20, 14, 8, int(220 * a)), outline=GOLD2 + (int(255 * a),), width=4)
            img = draw_text(img, (x, yy), it, font("serif", 56 if len(it) == 1 else 44, "Black", tc=True), fill=GOLD2, alpha=a)
    return img


# ══════════ 阡陌 / 分家 ══════════
@functools.lru_cache(None)
def fields_static():
    S = 1.15
    w, h = int(W * S), int(H * S)
    img = Image.new("RGB", (w, h), (30, 28, 18))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(12)
    cell = 120
    for i in range(-1, w // cell + 2):
        for j in range(-1, h // cell + 2):
            g = rng.uniform(0.6, 1.0)
            c = (int(58 * g), int(66 * g), int(34 * g)) if rng.random() > 0.25 else (int(86 * g), int(72 * g), int(36 * g))
            x, y = i * cell, j * cell
            d.rectangle([x + 6, y + 6, x + cell - 6, y + cell - 6], fill=c)
            for k in range(6, cell - 6, 12):
                d.line([(x + 6, y + k), (x + cell - 6, y + k)], fill=tuple(int(v * 0.85) for v in c), width=2)
    for i in range(0, w, cell * 4):
        d.line([(i, 0), (i, h)], fill=(120, 100, 70), width=12)
    for j in range(0, h, cell * 4):
        d.line([(0, j), (w, j)], fill=(120, 100, 70), width=12)
    return img


def house(d, x, y, s, c):
    d.rectangle([x - 40 * s, y - 26 * s, x + 40 * s, y + 26 * s], fill=c)
    d.polygon([(x - 52 * s, y - 22 * s), (x, y - 58 * s), (x + 52 * s, y - 22 * s)], fill=tuple(int(v * 0.8) for v in c[:3]) + (c[3],))


def scene_fields(t, D, ev, mode=1):
    img = kenburns(fields_static(), t, D, 1.0, 1.08, 0.5, 0.5, 0.52, 0.46).copy()
    dk = Image.new("RGB", img.size, (0, 0, 0))
    img = Image.blend(img, dk, 0.35)
    d = ImageDraw.Draw(img, "RGBA")
    img = tag(img, "阡陌俯瞰  示意")
    if mode == 1:
        t8 = at(ev, "d08", 0); t9 = at(ev, "d09", 99); t11 = at(ev, "d11", 99)
        if t < t9:
            img = draw_text(img, (300, 700), "耕织多", font("serif", 60, "Black"), fill=GOLD2, alpha=ramp(t, t8 + 1, 0.6))
            img = draw_text(img, (300, 790), "免徭役", font("serif", 52, "Bold"), fill=PAPER, alpha=ramp(t, t8 + 1.5, 0.6))
            img = draw_text(img, (780, 1100), "怠而贫", font("serif", 60, "Black"), fill=(170, 160, 150), alpha=ramp(t, t8 + 4, 0.6))
            img = draw_text(img, (780, 1190), "没为官奴", font("serif", 52, "Bold"), fill=RED2, alpha=ramp(t, t8 + 4.5, 0.6))
        else:
            k = ramp(t, t9 + 3.0, 2.5)
            cx, cy = W / 2, 1050
            if k < 0.5:
                d.rectangle([cx - 220, cy - 140, cx + 220, cy + 140], outline=(220, 190, 130, 255), width=6)
                for i in range(6):
                    house(d, cx - 150 + (i % 3) * 150, cy - 60 + (i // 3) * 120, 1.0, (130, 96, 60, 255))
                img = draw_text(img, (cx, cy - 210), "大家族", font("serif", 56, "Black"), fill=PAPER)
            else:
                kk = (k - 0.5) * 2
                pos = [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1.6), (0, 1.6)]
                for i, (px, py) in enumerate(pos):
                    x = cx + px * lerp(150, 320, kk); y = cy + py * lerp(110, 260, kk)
                    house(d, x, y, 1.0, (150, 110, 64, 255))
                    if t > t11:
                        a = ramp(t, t11 + 0.3 + i * 0.2, 0.4)
                        d.line([(x, y - 40), (cx, 420)], fill=GOLD2 + (int(200 * a),), width=4)
                if t > t11:
                    img = draw_text(img, (cx, 380), "国", font("serif", 110, "Black"), fill=GOLD2, alpha=ramp(t, t11, 0.6))
                img = draw_text(img, (cx, cy + 420), "二男以上不分异者，倍其赋", font("serif", 44, "Bold"), fill=PAPER, alpha=kk)
    else:
        t12 = at(ev, "d12", 0); t13 = at(ev, "d13", 99)
        if t < t13:
            for i, (lab, x) in enumerate([("耕", 330), ("战", 750)]):
                a = ramp(t, t12 + 1 + i * 0.6, 0.6)
                d.ellipse([x - 120, 1000 - 120, x + 120, 1000 + 120], fill=(30, 20, 12, int(220 * a)), outline=GOLD2 + (int(255 * a),), width=6)
                img = draw_text(img, (x, 1000), lab, font("serif", 120, "Black"), fill=GOLD2, alpha=a)
                d = ImageDraw.Draw(img, "RGBA")
                arrow(d, (540, 560), (x, 860), RED2 + (int(230 * a),), 10, 36, a)
            img = draw_text(img, (540, 500), "国家想要的", font("serif", 54, "Bold"), fill=PAPER, alpha=ramp(t, t12 + 0.5, 0.6))
            img = draw_text(img, (540, 1300), "上升通道接在这里", font("serif", 54, "Bold"), fill=GOLD2, alpha=ramp(t, t12 + 3, 0.6))
        else:
            k = ramp(t, t13 + 0.5, 1.5)
            img = draw_text(img, (540, 520), "委托人", font("serif", 46, "Bold"), fill=GOLD2, alpha=k)
            dd = ImageDraw.Draw(img, "RGBA")
            dd.ellipse([490, 570, 590, 670], fill=GOLD2 + (int(255 * k),))
            rng = np.random.default_rng(4)
            align = ramp(t, t13 + 5.0, 3.0)
            for i in range(90):
                x = 140 + (i % 15) * 57; y = 800 + (i // 15) * 70
                a0 = rng.uniform(0, 6.28); a1 = -math.pi / 2
                a = lerp(a0, a1, align)
                dd.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(200, 190, 170, int(230 * k)))
                dd.line([(x, y), (x + 26 * math.cos(a), y + 26 * math.sin(a))], fill=(RED2 if align > 0.5 else (170, 160, 150)) + (int(230 * k),), width=4)
            img = draw_text(img, (540, 1300), "代理人：几百万百姓", font("serif", 46, "Bold"), fill=PAPER, alpha=k)
            img = draw_text(img, (540, 1380), "规则让私利与国家同向", font("serif", 46, "Bold"), fill=GOLD2, alpha=align)
    return img


# ══════════ 受益阶层守护新法 ══════════
def scene_class(t, D, ev):
    img = vgrad((14, 10, 8), (6, 5, 4)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, 960
    k = ramp(t, 0.5, D * 0.6)
    rng = np.random.default_rng(8)
    N = int(420 * k)
    for i in range(N):
        r = rng.uniform(220, 430); a = rng.uniform(0, 6.28)
        rr = r * (1 - 0.06 * math.sin(t * 0.8 + i))
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        c = GOLD2 if i % 3 else RED2
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=c + (200,))
    glow(img, cx, cy, 300, (110, 70, 20), 0.6 + 0.4 * k)
    sl = slip_card(["新法"], font("serif", 70, "Black", tc=True), w_slip=130, h=360, seed=70)
    paste_center(img, sl, cx, cy, alpha=1.0)
    img = draw_text(img, (W / 2, 330), "军功新贵  ·  耕织之户", font("serif", 52, "Bold"), fill=GOLD2, alpha=ramp(t, 1.0, 0.8))
    t16 = at(ev, "d16", 99)
    if t > t16:
        img = draw_text(img, (W / 2, 1380), "改革的守护者", font("serif", 72, "Black"), fill=PAPER, alpha=ramp(t, t16 + 0.4, 0.7))
    return img


# ══════════ 县制 ══════════
def scene_county(t, D, ev):
    box = (-500, -400, 1700, 2100)
    img = map_static().copy()
    img = kenburns(img, t, D, 1.0, 1.6, 0.5, 0.5, 0.37, 0.53).copy()
    dk = Image.new("RGB", img.size, (0, 0, 0)); img = Image.blend(img, dk, 0.25)
    d = ImageDraw.Draw(img, "RGBA")
    img = tag(img, "关中  示意")
    cx, cy = 400, 1010
    t4 = at(ev, "e04", 0)
    k = ramp(t, t4 + 3.5, 3.0)
    rng = np.random.default_rng(17)
    nodes = [(cx + rng.uniform(-330, 560), cy + rng.uniform(-330, 340)) for _ in range(12)]
    for i, (nx, ny) in enumerate(nodes):
        for j in range(6):
            a = rng.uniform(0, 6.28); r = rng.uniform(30, 90)
            x = lerp(nx + r * math.cos(a), nx, k); y = lerp(ny + r * math.sin(a), ny, k)
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(200, 190, 160, 210))
        if k > 0.6:
            a2 = ramp(k, 0.6, 0.4)
            d.rectangle([nx - 16, ny - 16, nx + 16, ny + 16], fill=GOLD2 + (int(255 * a2),))
            d.line([(nx, ny), (cx, cy)], fill=GOLD + (int(150 * a2),), width=3)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=RED2 + (255,))
    img = draw_text(img, (cx, cy - 60), "咸阳", font("serif", 52, "Black"), fill=RED2)
    if k > 0.7:
        img = draw_text(img, (720, 520), "县 · 令 · 丞", font("serif", 62, "Black"), fill=GOLD2, alpha=ramp(k, 0.7, 0.3))
    t5 = at(ev, "e05", 99)
    if t > t5:
        items = ["开阡陌", "平斗桶", "平权衡", "平丈尺"]
        for i, it in enumerate(items):
            a = ramp(t, t5 + 0.5 + i * 0.9, 0.5)
            img = draw_text(img, (170 + i * 248, 1390), it, font("serif", 50, "Bold"), fill=PAPER, alpha=a)
    return img


# ══════════ 商鞅方升 ══════════
@functools.lru_cache(None)
def sheng_img():
    w, h = 900, 620
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    br = (104, 92, 66, 255); br2 = (70, 64, 46, 255); br3 = (132, 118, 84, 255)
    # 3/4 视角长方体 + 柄
    fx, fy, fw, fh, dx, dy = 140, 210, 420, 300, 150, -110
    d.polygon([(fx, fy), (fx + fw, fy), (fx + fw + dx, fy + dy), (fx + dx, fy + dy)], fill=br3)
    d.polygon([(fx + 26, fy - 6), (fx + fw - 18, fy - 6), (fx + fw + dx - 30, fy + dy + 14), (fx + dx + 14, fy + dy + 14)], fill=(28, 24, 18, 255))
    d.rectangle([fx, fy, fx + fw, fy + fh], fill=br)
    d.polygon([(fx + fw, fy), (fx + fw + dx, fy + dy), (fx + fw + dx, fy + dy + fh), (fx + fw, fy + fh)], fill=br2)
    d.polygon([(fx - 130, fy + 110), (fx, fy + 100), (fx, fy + 150), (fx - 130, fy + 160)], fill=br)
    d.rounded_rectangle([fx - 160, fy + 96, fx - 110, fy + 174], radius=12, fill=br2)
    # 铭文刻痕
    f = font("serif", 26, "Medium", tc=True)
    txt = ["十八年齊遣卿", "大夫眾來聘冬", "十二月乙酉大", "良造鞅爰積十", "六尊五分尊壹", "為升"]
    for i, col in enumerate(txt):
        for j, ch in enumerate(col):
            d.text((fx + fw - 40 - i * 58, fy + 30 + j * 40), ch, font=f, fill=(58, 50, 34, 255), anchor="mm")
    rng = np.random.default_rng(3)
    a = np.array(im).astype(np.float32)
    mask = a[..., 3] > 0
    patina = rng.normal(0, 10, a.shape[:2])
    for c, k in zip(range(3), (0.6, 1.2, 0.9)):
        a[..., c][mask] += patina[mask] * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def scene_sheng(t, D, ev):
    img = vgrad((18, 16, 14), (6, 6, 6)).copy()
    glow(img, W / 2, 960, 600, (60, 50, 36), 0.7)
    sc = 1.0 + 0.04 * ease(t / D)
    paste_center(img, sheng_img(), W / 2 + 40, 900, alpha=ramp(t, 0, 0.6), scale=sc)
    img = tag(img, "示意绘制  原器藏上海博物馆")
    img = draw_text(img, (W / 2, 1270), "商鞅方升", font("serif", 80, "Black"), fill=GOLD2)
    img = draw_text(img, (W / 2, 1360), "秦孝公十八年（前344）  容积 202.15 毫升", font("serif", 38, "Medium"), fill=(200, 190, 170))
    t7 = at(ev, "e07", 99)
    if t > t7:
        a = ramp(t, t7 + 1.5, 0.8)
        im = slip_card(["廿六年皇帝盡并兼", "天下諸侯黔首大安", "立號為皇帝乃詔丞", "相狀綰法度量則不", "壹歉疑者皆明壹之"],
                       font("serif", 34, "Bold", tc=True), w_slip=72, h=400, seed=80)
        paste_center(img, im, W / 2, 1100 - 60 * a, alpha=a * 0.97, scale=0.8)
        img = draw_text(img, (W / 2, 320), "底部加刻：秦始皇二十六年诏书", font("serif", 46, "Bold"), fill=RED2, alpha=a)
    return img


def scene_sheng2(t, D, ev):
    """清晰化：杂乱的线条被整理成网格。"""
    img = vgrad((14, 12, 10), (6, 6, 5)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    k = ramp(t, 1.0, D * 0.5)
    rng = np.random.default_rng(21)
    for i in range(90):
        x0, y0 = rng.uniform(150, 930), rng.uniform(560, 1220)
        a = rng.uniform(0, 6.28); L = rng.uniform(40, 140)
        gx = round((x0 - 150) / 78) * 78 + 150; gy = round((y0 - 600) / 75) * 75 + 600
        horiz = i % 2 == 0
        x0k, y0k = lerp(x0, gx, k), lerp(y0, gy, k)
        ak = lerp(a, 0 if horiz else math.pi / 2, k)
        Lk = lerp(L, 78, k)
        d.line([(x0k, y0k), (x0k + Lk * math.cos(ak), y0k + Lk * math.sin(ak))], fill=mix((150, 140, 120), GOLD2, k) + (220,), width=4)
    img = draw_text(img, (W / 2, 430), "清晰化", font("serif", 110, "Black"), fill=GOLD2, alpha=ramp(t, 0.5, 0.6))
    img = draw_text(img, (W / 2, 1310), "Legibility —— James C. Scott", font("serif", 40, "Medium"), fill=(190, 180, 160), alpha=ramp(t, 1.0, 0.6))
    img = draw_text(img, (W / 2, 1380), "《国家的视角》", font("serif", 44, "Bold"), fill=PAPER, alpha=ramp(t, 1.2, 0.6))
    return img


# ══════════ 什伍连坐：村落俯拍 ══════════
VIL = None


def village():
    global VIL
    if VIL is None:
        rng = np.random.default_rng(33)
        pts = []
        for gi in range(4):
            for gj in range(5):
                cx, cy = 210 + gi * 220 + rng.uniform(-20, 20), 520 + gj * 168 + rng.uniform(-20, 20)
                for k in range(5):
                    a = k / 5 * 6.28 + rng.uniform(-0.3, 0.3)
                    pts.append((cx + 62 * math.cos(a), cy + 56 * math.sin(a), gi, gj, k))
        VIL = pts
    return VIL


@functools.lru_cache(None)
def village_static():
    img = vgrad((14, 14, 12), (6, 6, 6)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(2)
    for i in range(400):
        x, y = rng.uniform(0, W), rng.uniform(380, 1600)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(40, 46, 30, 200))
    return img


def scene_grid(t, D, ev, mode=1):
    img = village_static().copy()
    d = ImageDraw.Draw(img, "RGBA")
    pts = village()
    t10 = at(ev, "e10", 0); t12 = at(ev, "e12", 99); t13b = at(ev, "e13b", 99)
    k5 = ramp(t, t10 + 1.0, 1.5)       # 五家为伍
    k10 = ramp(t, t10 + 3.5, 1.5)      # 十家为什
    knet = ramp(t, t12 + 1.0, 3.0) if mode == 1 else 1.0
    kup = ramp(t, t12 + 4.0, 2.0) if mode == 1 else 1.0
    # 灯火熄灭（grid2）
    off = set()
    if mode == 2:
        t15 = at(ev, "e15", 0)
        kk = ramp(t, t15 + 1.0, max(1.0, D - t15 - 2.0))
        rng = np.random.default_rng(5)
        order = rng.permutation(len(pts))
        off = set(order[: int(len(pts) * kk * 0.92)].tolist())
    for i, (x, y, gi, gj, k) in enumerate(pts):
        lit = i not in off
        house(d, x, y, 0.42, (70, 58, 40, 255))
        if lit:
            fl = 0.8 + 0.2 * math.sin(t * 5 + i)
            d.ellipse([x - 7, y - 4, x + 7, y + 8], fill=(255, 190, 90, int(230 * fl)))
    lc = RED2
    for i, (x, y, gi, gj, k) in enumerate(pts):
        j = i - k + (k + 1) % 5
        x2, y2 = pts[j][0], pts[j][1]
        if k5 > 0:
            d.line([(x, y), (lerp(x, x2, k5), lerp(y, y2, k5))], fill=lc + (int(200 * k5),), width=3)
    if k10 > 0:
        for gi in range(4):
            for gj in range(0, 5, 2):
                if gj + 1 < 5:
                    a = pts[(gi * 5 + gj) * 5][:2]; b = pts[(gi * 5 + gj + 1) * 5][:2]
                    d.line([a, (lerp(a[0], b[0], k10), lerp(a[1], b[1], k10))], fill=GOLD2 + (int(220 * k10),), width=5)
    if knet > 0:
        for gi in range(4):
            for gj in range(5):
                a = pts[(gi * 5 + gj) * 5 + 2][:2]
                for (ni, nj) in [(gi + 1, gj), (gi, gj + 1)]:
                    if ni < 4 and nj < 5:
                        b = pts[(ni * 5 + nj) * 5 + 2][:2]
                        d.line([a, (lerp(a[0], b[0], knet), lerp(a[1], b[1], knet))], fill=RED + (int(170 * knet),), width=3)
    if mode == 1:
        if kup > 0:
            d.rectangle([440, 300, 640, 400], fill=(40, 26, 14, int(230 * kup)), outline=GOLD2 + (int(255 * kup),), width=4)
            img = draw_text(img, (540, 350), "县", font("serif", 64, "Black"), fill=GOLD2, alpha=kup)
            d = ImageDraw.Draw(img, "RGBA")
            for i, xx in enumerate((260, 540, 820)):
                ph = ((t * 0.6 + i * 0.33) % 1.0)
                y = lerp(1300, 420, ph)
                d.polygon([(xx, y - 26), (xx - 18, y), (xx + 18, y)], fill=GOLD2 + (int(220 * kup * (1 - ph)),))
        if t < t12:
            img = draw_text(img, (540, 360), "五家为伍  十家为什", font("serif", 58, "Black"), fill=PAPER, alpha=k5)
        if t > t13b:
            a = ramp(t, t13b + 0.5, 0.6)
            img = draw_text(img, (W / 2, 1330), "告奸 ＝ 斩首", font("serif", 72, "Black"), fill=RED2, alpha=a)
            img = draw_text(img, (W / 2, 1405), "杠杆二 ⟷ 杠杆三", font("serif", 46, "Bold"), fill=GOLD2, alpha=ramp(t, t13b + 3.0, 0.6))
    else:
        img = draw_text(img, (W / 2, 1390), "信任被抽走", font("serif", 64, "Black"), fill=(200, 190, 170), alpha=ramp(t, at(ev, "e15", 0) + 2.0, 0.8))
    img = tag(img, "示意")
    return img


# ══════════ 连称赞者也赶走 ══════════
def crowd(d, t, n, xs, y, colors, s=120):
    for i in range(n):
        figure(d, xs[i], y, s, colors[i])


def scene_praise(t, D, ev, mode=1):
    img = vgrad((14, 12, 10), (8, 6, 5)).copy()
    d = ImageDraw.Draw(img, "RGBA")
    if mode == 1:
        t17 = at(ev, "e17", 0); t18 = at(ev, "e18", 99)
        n = 21
        rng = np.random.default_rng(6)
        for i in range(n):
            row = i // 7; col = i % 7
            x0 = 160 + col * 128 + (row % 2) * 40; y0 = 960 + row * 150
            praise = i % 3 == 0
            k = ramp(t, t17 + 4.0, 1.0)
            c = mix((110, 104, 96), GOLD2, k if praise else 0)
            # 被迁往边城
            mv = ramp(t, t18 + 3.0 + (i % 5) * 0.15, 2.0) if praise else 0
            x = lerp(x0, W + 200, mv); y = lerp(y0, 640, mv)
            figure(d, x, y, 150, c + (255,))
        img = draw_text(img, (W / 2, 520), "言令不便者 以千数", font("serif", 50, "Bold"), fill=(170, 160, 150), alpha=ramp(t, 0.3, 0.6) * (1 - ramp(t, t17 + 3.5, 0.5)))
        img = draw_text(img, (W / 2, 520), "来言令便者", font("serif", 56, "Black"), fill=GOLD2, alpha=ramp(t, t17 + 4.0, 0.6) * (1 - ramp(t, t18 + 2.5, 0.5)))
        if t > t18 + 2.5:
            img = draw_text(img, (W - 160, 520), "边城 →", font("serif", 56, "Black"), fill=RED2, alpha=ramp(t, t18 + 2.5, 0.6))
        if t > t18 + 6.0:
            img = draw_text(img, (W / 2, 1380), "民莫敢议令", font("serif", 78, "Black"), fill=PAPER, alpha=ramp(t, t18 + 6.0, 0.7))
    else:
        # 反馈回路：系统 → 输出 → 反馈（负/正）→ 系统，两条反馈都被切断
        cx, cy = W / 2, 980
        d.rounded_rectangle([cx - 170, cy - 110, cx + 170, cy + 110], radius=24, outline=GOLD2 + (255,), width=6)
        img = draw_text(img, (cx, cy), "秦法", font("serif", 80, "Black", tc=True), fill=GOLD2)
        d = ImageDraw.Draw(img, "RGBA")
        for i, (lab, side) in enumerate([("批评", -1), ("称赞", 1)]):
            x = cx + side * 200
            d.arc([x - 200, cy - 260, x + 200, cy + 260], -90 if side > 0 else 90, 90 if side > 0 else 270, fill=(170, 160, 140, 255), width=6)
            arrow(d, (x + side * 20, cy + 260), (x - side * 40, cy + 255), (170, 160, 140, 255), 6, 26)
            img = draw_text(img, (x + side * 60, cy - 320), lab, font("serif", 50, "Bold"), fill=PAPER)
            d = ImageDraw.Draw(img, "RGBA")
            k = ramp(t, 1.0 + i * 1.6, 0.4)
            xx = x + side * 200
            s = 60 * k
            d.line([(xx - s, cy - s), (xx + s, cy + s)], fill=RED2 + (255,), width=14)
            d.line([(xx - s, cy + s), (xx + s, cy - s)], fill=RED2 + (255,), width=14)
        t20 = at(ev, "e20", 99)
        if t > t20:
            img = draw_text(img, (W / 2, 1360), "听不到自己出错的声音", font("serif", 58, "Black"), fill=GOLD2, alpha=ramp(t, t20 + 2.5, 0.8))
        img = draw_text(img, (W / 2, 460), "反馈回路", font("serif", 60, "Black"), fill=(190, 180, 160), alpha=ramp(t, 0.3, 0.6))
    return img


# ══════════ 富强 / 赵良 ══════════
def scene_rise(t, D, ev):
    img = kenburns(map_static(), t, D, 1.0, 1.12, 0.5, 0.5, 0.4, 0.52).copy()
    img = draw_states(img, 1.0, 1.0)
    d = ImageDraw.Draw(img, "RGBA")
    img = tag(img, "示意")
    t2 = at(ev, "f02", 99)
    k = ramp(t, t2 + 3.0, 1.5)
    hp = hexi_poly()
    d.polygon(hp, fill=mix((160, 150, 130), RED2, k) + (int(lerp(110, 190, k)),), outline=(230, 200, 150, 255))
    if t > t2:
        x, y = proj(111.0, 35.1)
        arrow(d, proj(108.9, 34.6), (x - 10, y + 10), RED2 + (240,), 14, 46, ramp(t, t2 + 0.5, 1.5))
    img = draw_text(img, (W / 2, 1390), "天子致胙  诸侯毕贺", font("serif", 56, "Black", tc=False), fill=GOLD2, alpha=ramp(t, 0.6, 0.8) * (1 - ramp(t, t2, 0.5)))
    if t > t2 + 6:
        x, y = proj(*CITIES["商"])
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=GOLD2 + (255,))
        img = draw_text(img, (x + 30, y + 40), "商  十五邑", font("serif", 46, "Bold"), fill=GOLD2, anchor="lm", alpha=ramp(t, t2 + 6, 0.6))
        img = draw_text(img, (W / 2, 1390), "号为商君", font("serif", 70, "Black"), fill=PAPER, alpha=ramp(t, t2 + 7, 0.6))
    return img


def scene_zhaoliang(t, D, ev, mode=1):
    img = palace_static().copy()
    d = ImageDraw.Draw(img, "RGBA")
    if mode == 1:
        figure(d, 330, 1300, 420, (10, 6, 5, 255))
        figure(d, 750, 1300, 400, (30, 16, 10, 255))
        img = draw_text(img, (330, 1360), "商君", font("serif", 48, "Bold"), fill=PAPER)
        img = draw_text(img, (750, 1360), "赵良", font("serif", 48, "Bold"), fill=GOLD2)
        t5 = at(ev, "f05", 99)
        if t > t5 + 0.5:
            # 千人诺诺：一片灰点头；一士谔谔：一个红色站立者
            ka = ramp(t, t5 + 0.5, 0.8)
            img = Image.blend(img, Image.new("RGB", img.size, (8, 6, 5)), 0.75 * ka)
            dd = ImageDraw.Draw(img, "RGBA")
            for i in range(75):
                x = 110 + (i % 15) * 61; y = 860 + (i // 15) * 90
                if abs(x - 540) < 50 and 1000 < y < 1300:
                    continue
                nod = 7 * math.sin(t * 4 + i)
                dd.ellipse([x - 16, y - 16 + nod, x + 16, y + 16 + nod], fill=(110, 104, 96, int(230 * ka)))
                dd.rectangle([x - 18, y + 20 + nod, x + 18, y + 50], fill=(80, 76, 70, int(230 * ka)))
            figure(dd, 540, 1330, 300, RED2 + (int(255 * ka),))
            img = draw_text(img, (300, 1390), "诺诺", font("serif", 50, "Bold"), fill=(170, 160, 150), alpha=ka)
            img = draw_text(img, (780, 1390), "谔谔", font("serif", 50, "Bold"), fill=RED2, alpha=ka)
    else:
        # 朝露：叶上的露珠在晨光中缩小
        img = vgrad((40, 30, 24), (12, 10, 9)).copy()
        k = ramp(t, 1.0, D * 0.8)
        glow(img, 820, 420, 500, (150, 110, 60), 0.4 + 0.6 * k)
        d = ImageDraw.Draw(img, "RGBA")
        d.polygon([(100, 1250), (500, 980), (980, 1040), (560, 1250)], fill=(40, 60, 34, 255))
        d.line([(100, 1250), (980, 1040)], fill=(70, 96, 56, 255), width=6)
        r = lerp(70, 6, k)
        d.ellipse([540 - r, 1100 - 2 * r, 540 + r, 1100], fill=(200, 220, 230, int(200 * (1 - k * 0.7))))
        d.ellipse([540 - r * 0.4, 1100 - 1.6 * r, 540 - r * 0.05, 1100 - 1.2 * r], fill=(255, 255, 255, int(220 * (1 - k))))
        img = draw_text(img, (W / 2, 1290), "朝露", font("serif", 120, "Black"), fill=PAPER, alpha=ramp(t, 0.5, 0.8))
        t7 = at(ev, "f07", 99)
        if t > t7:
            img = draw_text(img, (W / 2, 1400), "商君弗从", font("serif", 64, "Black", tc=True), fill=RED2, alpha=ramp(t, t7 + 1.5, 0.6))
    return img


# ══════════ 出逃（地图） ══════════
def scene_fall(t, D, ev, mode=1):
    img = kenburns(map_static(), t, D, 1.15, 1.25, 0.42, 0.52, 0.44, 0.5).copy()
    dk = Image.new("RGB", img.size, (0, 0, 0)); img = Image.blend(img, dk, 0.2)
    d = ImageDraw.Draw(img, "RGBA")
    img = tag(img, "出逃路线  示意")
    # 坐标已在 kenburns 内变换：用近似方式在全图坐标上画，再统一推拉 → 简化：直接在推拉后的画面上画固定位置
    if mode == 1:
        t8 = at(ev, "f08", 0); t9 = at(ev, "f09", 99)
        img = draw_text(img, (W / 2, 420), "前338年  秦孝公卒", font("serif", 62, "Black"), fill=PAPER, alpha=ramp(t, t8 + 0.3, 0.6))
        if t > t9:
            img = draw_text(img, (W / 2, 520), "公子虔之徒告商君欲反", font("serif", 50, "Bold", tc=False), fill=RED2, alpha=ramp(t, t9 + 2.0, 0.6))
    pts = {"咸阳": (430, 1010), "关": (560, 1000), "魏": (720, 900), "商": (520, 1140), "郑": (480, 1070)}
    for nm, (x, y) in pts.items():
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(230, 210, 170, 255))
        img = draw_text(img, (x, y - 40), nm, font("serif", 40, "Bold"), fill=PAPER)
        d = ImageDraw.Draw(img, "RGBA")
    if mode == 1:
        t10 = at(ev, "f10", 99)
        k = ramp(t, t10, 2.0)
        path_arrow(d, [pts["咸阳"], pts["关"]], RED2 + (255,), 10, 34, k)
    else:
        t11 = at(ev, "f11", 0); t12 = at(ev, "f12", 99)
        path_arrow(d, [pts["咸阳"], pts["关"]], RED2 + (150,), 10, 34, 1.0)
        path_arrow(d, [pts["关"], pts["魏"]], RED2 + (255,), 10, 34, ramp(t, t11 + 0.5, 1.5))
        if t > t11 + 3:
            a = ramp(t, t11 + 3, 0.4)
            x, y = pts["魏"]
            d.line([(x - 30, y - 30), (x + 30, y + 30)], fill=(240, 240, 240, int(255 * a)), width=10)
            d.line([(x - 30, y + 30), (x + 30, y - 30)], fill=(240, 240, 240, int(255 * a)), width=10)
            img = draw_text(img, (x + 20, y + 70), "弗受", font("serif", 44, "Bold", tc=True), fill=PAPER, alpha=a)
            d = ImageDraw.Draw(img, "RGBA")
        path_arrow(d, [pts["魏"], (640, 1100), pts["商"]], RED2 + (255,), 10, 34, ramp(t, t11 + 4.5, 1.5))
        if t > t12:
            path_arrow(d, [pts["商"], pts["郑"]], RED2 + (255,), 10, 34, ramp(t, t12 + 0.5, 1.0))
            a = ramp(t, t12 + 1.8, 0.4)
            x, y = pts["郑"]
            glow(img, x, y, 120, (160, 20, 10), a)
            img = draw_text(img, (x - 30, y + 80), "兵败被杀", font("serif", 50, "Black"), fill=RED2, anchor="mm", alpha=a)
    return img


# ══════════ 车裂：五马剪影向五方散开 → 黑屏（不写实） ══════════
def scene_horses(t, D, ev):
    img = vgrad((26, 8, 6), (6, 2, 2)).copy()
    k = ramp(t, 0.6, 3.0)
    glow(img, W / 2, 960, 600, (90, 14, 8), 0.8 * (1 - k))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = W / 2, 960
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        r = lerp(120, 900, ease(k))
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        horse(d, x, y, 260, (0, 0, 0, 255), a, t * 9 + i)
        d.line([(cx, cy), (x, y)], fill=(0, 0, 0, int(160 * (1 - k))), width=3)
    fade = ramp(t, 3.2, 1.2)
    if fade > 0:
        img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), fade)
    if t > 4.0:
        img = draw_text(img, (W / 2, 900), "莫如商鞅反者", font("serif", 84, "Black", tc=True), fill=(200, 60, 40), alpha=ramp(t, 4.2, 0.8) * (1 - ramp(t, D - 0.8, 0.6)))
    return img


# ══════════ 睡虎地秦简 ══════════
def scene_slips(t, D, ev):
    img = vgrad((18, 14, 10), (6, 5, 4)).copy()
    glow(img, W / 2, 900, 650, (80, 56, 24), 0.6)
    txt = ["雨為澍及誘粟", "輒以書言澍稼", "誘粟……頃數", "田律"]
    im = slip_card(txt, font("serif", 52, "Bold", tc=True), w_slip=104, h=760, seed=90)
    t19 = at(ev, "f19", 99)
    yy = lerp(1060, 830, ramp(t, t19 - 0.3, 1.0))
    paste_center(img, im, W / 2, yy, alpha=ramp(t, 0, 0.8), scale=0.72 + 0.03 * ease(t / D))
    img = tag(img, "睡虎地秦简  摹写示意")
    t19 = at(ev, "f19", 99); t20 = at(ev, "f20", 99)
    if t > t19 and t < t20:
        a = ramp(t, t19 + 0.3, 0.6)
        img = draw_text(img, (W / 2, 1300), "命令随人而去", font("serif", 60, "Black"), fill=(180, 170, 160), alpha=a)
        img = draw_text(img, (W / 2, 1390), "制度随受益者而存", font("serif", 60, "Black"), fill=GOLD2, alpha=ramp(t, t19 + 2.0, 0.6))
    if t > t20:
        a = ramp(t, t20 + 0.3, 0.6)
        img = draw_text(img, (W / 2, 1300), "前338 → 前221", font("serif", 64, "Black"), fill=PAPER, alpha=a)
        img = draw_text(img, (W / 2, 1395), "117 年", font("serif", 80, "Black"), fill=RED2, alpha=ramp(t, t20 + 2.5, 0.6))
    return img


# ══════════ 结尾：两句评语并置，中间秦律竹简 ══════════
def scene_verdict(t, D, ev, mode=1):
    img = vgrad((16, 12, 10), (6, 5, 4)).copy()
    glow(img, W / 2, 960, 600, (70, 46, 18), 0.6)
    f = font("serif", 44, "Bold", tc=True)
    a0 = ramp(t, 0.2, 0.8)
    mid = slip_card(["秦律"], font("serif", 60, "Black", tc=True), w_slip=120, h=640, seed=99)
    paste_center(img, mid, W / 2, 1000, alpha=a0)
    tg2 = at(ev, "g02", 0 if mode == 2 else 99); tg3 = at(ev, "g03", 0 if mode == 2 else 99)
    la = ramp(t, tg2 + 1.0, 0.8) if mode == 1 else 1.0
    ra = ramp(t, tg3 + 1.0, 0.8) if mode == 1 else 1.0
    if la > 0:
        sl = slip_card(["商君其天資", "刻薄人也"], f, w_slip=80, h=520, seed=101)
        paste_center(img, sl, 220, 1000, alpha=la)
        img = draw_text(img, (220, 1330), "司马迁", font("serif", 40, "Bold"), fill=(200, 190, 170), alpha=la)
    if ra > 0:
        sl = slip_card(["千人之諾諾", "不如一士之", "諤諤"], f, w_slip=80, h=520, seed=111, fill=(120, 20, 10))
        paste_center(img, sl, 860, 1000, alpha=ra)
        img = draw_text(img, (860, 1330), "赵良", font("serif", 40, "Bold"), fill=GOLD2, alpha=ra)
    if mode == 2:
        t4 = at(ev, "g04", 0)
        img = draw_text(img, (220, 540), "这个人", font("serif", 54, "Black"), fill=(200, 190, 170), alpha=ramp(t, t4 + 0.8, 0.5))
        img = draw_text(img, (860, 540), "这台机器缺了什么", font("serif", 44, "Black"), fill=GOLD2, alpha=ramp(t, t4 + 2.2, 0.5))
    return img


def scene_end(t, D, ev, mode=1):
    if mode == 1:
        img = kenburns(city_static(), t, D, 1.05, 1.15).copy()
        img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.45)
        k = ramp(t, 0.5, 1.0)
        img = draw_text(img, (W / 2, 560), "改革能否活过改革者", font("serif", 64, "Black"), fill=GOLD2, alpha=k)
        img = draw_text(img, (W / 2, 660), "看它造出了多少离不开它的人", font("serif", 50, "Bold"), fill=PAPER, alpha=ramp(t, 1.5, 0.8))
        t9 = at(ev, "g09", 99)
        if t > t9:
            img = draw_text(img, (W / 2, 1290), "把称赞者也赶走", font("serif", 56, "Black"), fill=(200, 190, 170), alpha=ramp(t, t9 + 0.5, 0.6))
            img = draw_text(img, (W / 2, 1380), "迟早没人敢说真话", font("serif", 56, "Black"), fill=RED2, alpha=ramp(t, t9 + 1.8, 0.6))
        return img
    img = vgrad((10, 8, 7), (2, 2, 2)).copy()
    glow(img, W / 2, 900, 500, (70, 40, 14), 0.6 * (1 - ramp(t, D - 1.5, 1.4)))
    f = font("serif", 66, "Black", tc=True)
    a = ramp(t, 0.2, 1.0) * (1 - ramp(t, D - 1.2, 1.0))
    img = draw_text(img, (W / 2, 760), "千人之諾諾", f, fill=PAPER, alpha=a)
    img = draw_text(img, (W / 2, 880), "不如一士之諤諤", f, fill=GOLD2, alpha=a)
    img = draw_text(img, (W / 2, 1000), "——《史記·商君列傳》", font("serif", 40, "Medium", tc=True), fill=(190, 180, 160), alpha=a)
    return img


SCENES = {
    "inn": lambda t, D, ev: scene_inn(t, D, ev, 0),
    "inn2": lambda t, D, ev: scene_inn(t, D, ev, 2),
    "inn3": lambda t, D, ev: scene_inn(t, D, ev, 3),
    "death": scene_death,
    "timeline": scene_timeline,
    "levers0": lambda t, D, ev: scene_machine(t, D, ev, labels=False, ghost=True),
    "levers": scene_levers,
    "map": lambda t, D, ev: scene_map(t, D, ev, 1),
    "map2": lambda t, D, ev: scene_map(t, D, ev, 2),
    "audience": scene_audience,
    "debate": scene_debate,
    "debate2": scene_debate2,
    "pole": scene_pole,
    "pole2": scene_pole2,
    "prince": scene_prince,
    "prince2": scene_prince2,
    "ladder": lambda t, D, ev: scene_ladder(t, D, ev, 1),
    "ladder2": lambda t, D, ev: scene_ladder(t, D, ev, 2),
    "fields": lambda t, D, ev: scene_fields(t, D, ev, 1),
    "fields2": lambda t, D, ev: scene_fields(t, D, ev, 2),
    "class": scene_class,
    "county": scene_county,
    "sheng": scene_sheng,
    "sheng2": scene_sheng2,
    "grid": lambda t, D, ev: scene_grid(t, D, ev, 1),
    "grid2": lambda t, D, ev: scene_grid(t, D, ev, 2),
    "praise": lambda t, D, ev: scene_praise(t, D, ev, 1),
    "praise2": lambda t, D, ev: scene_praise(t, D, ev, 2),
    "rise": scene_rise,
    "zhaoliang": lambda t, D, ev: scene_zhaoliang(t, D, ev, 1),
    "zhaoliang2": lambda t, D, ev: scene_zhaoliang(t, D, ev, 2),
    "fall": lambda t, D, ev: scene_fall(t, D, ev, 1),
    "fall2": lambda t, D, ev: scene_fall(t, D, ev, 2),
    "horses": scene_horses,
    "machine": lambda t, D, ev: scene_machine(t, D, ev, labels=True, ghost=False),
    "machine2": lambda t, D, ev: scene_machine(t, D, ev, labels=True, ghost=False),
    "slips": scene_slips,
    "verdict": lambda t, D, ev: scene_verdict(t, D, ev, 1),
    "verdict2": lambda t, D, ev: scene_verdict(t, D, ev, 2),
    "end": lambda t, D, ev: scene_end(t, D, ev, 1),
    "end2": lambda t, D, ev: scene_end(t, D, ev, 2),
}
