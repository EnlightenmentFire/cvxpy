"""逐帧渲染画面（1080×1920，25 fps，恒定帧率），按 timeline.json 对时。

全部画面由代码生成：物理示意（双缝、Kim 等 1999 实验光路、符合计数分组）、经文卡片、禅堂灯、云月、书法。
物理图样按真实公式抽样：
  D0 总图 ∝ sinc²(πax)；R01 ∝ sinc²·cos²(πdx)；R02 ∝ sinc²·sin²(πdx)；R03/R04 ∝ sinc²（无条纹）
usage: python render.py <part> <nparts>      -> video/part_<k>.mp4（无声）
       python render.py still <t> [out.png]  -> 单帧预览
"""
import os, sys, json, math, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
W, H, FPS = 1080, 1920, 25
TL = json.load(open(os.environ.get("TIMELINE", f"{WORK}/timeline.json")))
TOTAL = TL["total"]

# ───────────────────────── 字体 ─────────────────────────
NOTO = "/usr/share/fonts/opentype/noto/"
_fc = {}


def font(kind, size):
    key = (kind, size)
    if key not in _fc:
        path, idx = {
            "serif": (NOTO + "NotoSerifCJK-Regular.ttc", 2), "serif_b": (NOTO + "NotoSerifCJK-SemiBold.ttc", 2),
            "serif_bk": (NOTO + "NotoSerifCJK-Black.ttc", 2), "tc": (NOTO + "NotoSerifCJK-Regular.ttc", 3),
            "tc_b": (NOTO + "NotoSerifCJK-SemiBold.ttc", 3), "sans": (NOTO + "NotoSansCJK-Medium.ttc", 2),
            "sans_r": (NOTO + "NotoSansCJK-Regular.ttc", 2), "kai": ("/usr/share/fonts/truetype/arphic/ukai.ttc", 0),
        }[kind]
        _fc[key] = ImageFont.truetype(path, size, index=idx)
    return _fc[key]


# ───────────────────────── 颜色 ─────────────────────────
def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


CREAM = hexc("e9e4d8")
ICE = hexc("8fd3ff")
VIOLET = hexc("9b7bff")
RED = hexc("ff6a5a")
GOLD = hexc("d9b25f")
SEAL = hexc("b23a2e")
GREY = hexc("8a94a6")
DCOL = {1: hexc("f5c451"), 2: hexc("4fd1c5"), 3: hexc("8a94a6"), 4: hexc("b39ddb")}


def lerp(a, b, u):
    return a + (b - a) * u


def clamp(u, a=0.0, b=1.0):
    return max(a, min(b, u))


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def fade(t, t0, d=0.5):
    return ease((t - t0) / d)


def withalpha(c, a):
    return (c[0], c[1], c[2], int(clamp(a) * c[3]))


# ───────────────────────── 背景 ─────────────────────────
_bg = {}
rng0 = np.random.default_rng(7)


def bg(kind):
    if kind in _bg:
        return _bg[kind]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    vign = np.clip(1 - 1.3 * r ** 2, 0, 1)[..., None]
    if kind == "phys":
        top, bot = np.array([10, 16, 30]), np.array([4, 7, 14])
    elif kind == "budd":
        top, bot = np.array([26, 21, 17]), np.array([9, 8, 7])
    elif kind == "night":
        top, bot = np.array([8, 12, 24]), np.array([16, 16, 22])
    else:
        top, bot = np.array([12, 12, 14]), np.array([5, 5, 6])
    g = (yy / H)[..., None]
    img = (top * (1 - g) + bot * g) * (0.55 + 0.45 * vign)
    noise = rng0.normal(0, 1.2, (H, W, 1))
    img = np.clip(img + noise, 0, 255).astype(np.float32)
    if kind == "phys":  # 极淡的网格（实验室感）
        grid = ((xx % 90 < 1) | (yy % 90 < 1)).astype(np.float32)[..., None] * 5
        img += grid * vign
    _bg[kind] = img
    return img


# ───────────────────────── 光点 / 发光 ─────────────────────────
def add_glow(cv, x, y, color, radius, gain):
    """在 float canvas 上叠加一个高斯光斑"""
    r = int(radius * 3)
    x0, y0 = int(x) - r, int(y) - r
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(W, x0 + 2 * r + 1), min(H, y0 + 2 * r + 1)
    if xs1 <= xs0 or ys1 <= ys0:
        return
    yy, xx = np.mgrid[ys0:ys1, xs0:xs1]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radius ** 2))[..., None] * gain
    cv[ys0:ys1, xs0:xs1] += g * np.array(color[:3], np.float32)


def dot_field(cv, rect, xs, ys, cols, alpha, sigma=1.4, gain=1.0, flash=None):
    """把一批点（xs∈[-1,1], ys∈[0,1]）画到 rect 内；cols: Nx3 颜色；flash: 每点额外亮度（新落点）"""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    if len(xs) == 0:
        return
    px = np.clip(((xs + 1) / 2 * (w - 1)).astype(int), 0, w - 1)
    py = np.clip((ys * (h - 1)).astype(int), 0, h - 1)
    den = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        np.add.at(den[..., c], (py, px), cols[:, c] * alpha)
    den = gaussian_filter(den, (sigma, sigma, 0)) * (2 * math.pi * sigma ** 2) * 0.55 * gain * 255
    if flash is not None and (flash > 0).any():
        m = flash > 0
        fl = np.zeros((h, w, 3), np.float32)
        for c in range(3):
            np.add.at(fl[..., c], (py[m], px[m]), cols[m, c] * flash[m])
        fl = gaussian_filter(fl, (6, 6, 0)) * (2 * math.pi * 36) * 0.12 * 255
        den += fl
    cv[y0:y1, x0:x1] += den


# ───────────────────────── 物理分布与抽样 ─────────────────────────
A_ENV, D_FR = 1.05, 3.2


def p_env(x):
    return np.sinc(A_ENV * x) ** 2


def p_group(x, g):
    e = p_env(x)
    if g == 1:
        return e * np.cos(np.pi * D_FR * x) ** 2
    if g == 2:
        return e * np.sin(np.pi * D_FR * x) ** 2
    if g == 3:
        return np.sinc(A_ENV * (x + 0.04)) ** 2 * 0.5 + 0.0 * x
    return np.sinc(A_ENV * (x - 0.04)) ** 2 * 0.5


def sample(pf, n, rng):
    out = []
    while len(out) < n:
        x = rng.uniform(-1, 1, n * 3)
        u = rng.uniform(0, 1, n * 3)
        out.extend(x[u < pf(x)].tolist())
    return np.array(out[:n])


R = np.random.default_rng(1999)
N_KIM = 2600
KIM_G = R.integers(1, 5, N_KIM)                 # 孪生光子落在 D1..D4，各 1/4
KIM_X = np.array([sample(lambda x, g=g: p_group(x, g), 1, R)[0] for g in KIM_G])
KIM_Y = R.uniform(0.06, 0.94, N_KIM)
KIM_T = np.sqrt(np.arange(N_KIM) / N_KIM)       # 0..1 累积进度（先慢后快）
N_SL = 2200
SL_FR_X = sample(lambda x: p_env(x) * np.cos(np.pi * D_FR * x) ** 2, N_SL, R)
SL_BL_X = sample(lambda x: 0.5 * (np.sinc(A_ENV * (x - 0.05)) ** 2 + np.sinc(A_ENV * (x + 0.05)) ** 2), N_SL, R)
SL_TAG = R.integers(0, 2, N_SL)
SL_Y = R.uniform(0.06, 0.94, N_SL)
SL_T = np.sqrt(np.arange(N_SL) / N_SL)


def hist_curve(xs, bins=90, smooth=1.2):
    h, e = np.histogram(xs, bins=bins, range=(-1, 1))
    h = gaussian_filter(h.astype(float), smooth)
    return (e[:-1] + e[1:]) / 2, h


# ───────────────────────── 文字工具 ─────────────────────────
def text(dr, xy, s, f, fill, anchor="mm", stroke=0, sfill=(0, 0, 0, 200), spacing=10):
    dr.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill, spacing=spacing)


def wrap(s, f, maxw):
    if re.match(r"^[\x00-\x7f]+$", s):  # 英文按词换行
        lines, cur = [], ""
        for w_ in s.split(" "):
            if cur and f.getlength(cur + " " + w_) > maxw:
                lines.append(cur); cur = w_
            else:
                cur = (cur + " " + w_).strip()
        return lines + ([cur] if cur else [])
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if f.getlength(cur + ch) > maxw and cur:
            if ch in "，。、；：！？」』”）…":
                cur += ch; lines.append(cur); cur = ""; continue
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def para(dr, cx, y, s, f, fill, maxw, lh=None, anchor_center=True, reveal=1.0):
    """多行居中文本，返回结束 y；reveal 控制逐字显现比例"""
    ls = wrap(s, f, maxw)
    lh = lh or int(f.size * 1.55)
    n_all = sum(len(l) for l in ls)
    shown = reveal * n_all
    k = 0
    for i, l in enumerate(ls):
        yy = y + i * lh
        if anchor_center:
            x0 = cx - f.getlength(l) / 2
        else:
            x0 = cx
        xx = x0
        for ch in l:
            a = clamp(shown - k)
            if reveal < 1.0:
                a = 0.22 + 0.78 * a
            if a > 0:
                dr.text((xx, yy), ch, font=f, fill=withalpha(fill, a), anchor="lm")
            xx += f.getlength(ch)
            k += 1
    return y + len(ls) * lh


# ───────────────────────── 时间线索引 ─────────────────────────
LINES = TL["lines"]
GROUP = {
    "laser": "lab", "no": "lab", "erase_tease": "lab", "whichpath": "lab",
    "tease_groups": "tease", "no_signal": "tease", "halves": "halves", "halves2": "halves", "disclaimer": "disc",
    "slit_setup": "slit", "slit_dots": "slit", "slit_fringe": "slit", "slit_tag": "slit", "slit_blob": "slit",
    "slit_entangle": "slit", "carroll1": "slit", "question": "slit",
    "history": "hist", "paper": "hist",
    "kim_crystal": "kim", "kim_pair": "kim", "kim_signal": "kim", "kim_idler": "kim", "kim_split": "kim",
    "kim_d34": "kim", "kim_d12": "kim", "abstract": "kim", "abstract_note": "kim", "kim_claim": "kim",
    "f1": "facts", "f1_blob": "facts", "f2": "facts", "f2_color": "facts", "f2_r1": "facts", "f2_r2": "facts",
    "f2_sum": "facts", "f2_r34": "facts", "f2_analogy": "analogy", "f3": "time", "f3_no": "time", "f3_order": "time",
    "f4": "f4", "carroll2": "f4",
    "sum1": "sum", "sum2": "sum", "sum3": "sum", "to_stars": "stars",
    "hall": "hall", "q_hy": "hall", "q_hy_note": "hall", "q_hy2": "hall", "q_tj0": "hall", "q_tj1": "hall",
    "q_tj2": "hall", "q_tj3": "hall", "q_tj3_note": "hall", "penit_end": "hall",
    "q_fj": "moon", "q_pali": "moon", "moon_cloud": "moon",
    "compare": "close", "compare_l": "close", "compare_r": "close", "analogy": "close2", "small": "small",
    "final1": "final", "final2": "final", "brush": "brush",
}
# 镜头：相邻同组合并
SHOTS = []
for i, e in enumerate(LINES):
    g = GROUP[e["cue"]]
    st = 0.0 if i == 0 else e["start"] - 0.25
    if SHOTS and SHOTS[-1]["g"] == g:
        continue
    if SHOTS:
        SHOTS[-1]["end"] = st
    SHOTS.append(dict(g=g, start=st, end=TOTAL))
CUE_T = {}
for e in LINES:
    CUE_T.setdefault(e["cue"], e["start"])
LINE_BY_CUE = {}
for e in LINES:
    LINE_BY_CUE.setdefault(e["cue"], []).append(e)


def since(cue, t):
    return t - CUE_T[cue] if cue in CUE_T else -1e9


def cue_span(cue):
    ls = LINE_BY_CUE[cue]
    return ls[0]["start"], ls[-1]["end"]


def line_prog(cue, t, idx=0):
    """该 cue 第 idx 句朗读进度 0..1"""
    e = LINE_BY_CUE[cue][idx]
    return clamp((t - e["start"]) / max(0.1, e["end"] - e["start"]))


def cur_line(t):
    for e in LINES:
        if e["start"] - 0.05 <= t < e["end"] + 0.05:
            return e
    return None


# ───────────────────────── 通用版式 ─────────────────────────
PART = {"open": "", "slit": "第一部分 · 物理", "kim": "第一部分 · 物理", "facts": "第一部分 · 物理", "sum": "第一部分 · 物理",
        "penit": "第二部分 · 忏悔", "moon": "第二部分 · 忏悔", "close": "印照"}


def head(dr, s, t, t0, y=250, size=66, col=CREAM, kind="serif_b"):
    a = fade(t, t0, 0.5)
    if a > 0:
        text(dr, (W // 2, y), s, font(kind, size), withalpha(col, a), stroke=3, sfill=(0, 0, 0, int(160 * a)))


def badge(dr, s, xy, col=GREY, size=26):
    f = font("sans_r", size)
    x, y = xy
    w = f.getlength(s) + 24
    dr.rounded_rectangle((x - w, y - 20, x, y + 20), 8, outline=withalpha(col, 0.8), width=2)
    text(dr, (x - w / 2, y), s, f, withalpha(col, 0.9))


def card(dr, box, fill=(12, 16, 26, 215), outline=(143, 211, 255, 90)):
    dr.rounded_rectangle(box, 22, fill=fill, outline=outline, width=2)


# ───────────────────────── 场景：开场实验室 ─────────────────────────
LAB_SCREEN = (120, 1080, 960, 1300)
CRYS = (540, 640)


def draw_beam(dr, p0, p1, col, width, a=1.0):
    for w_, aa in [(width * 7, 0.07), (width * 3, 0.18), (width, 0.95)]:
        dr.line([p0, p1], fill=withalpha(col, aa * a), width=int(w_))


def lab_layer(dr, t, a=1.0, split=True):
    # 泵浦（紫外，画成紫色）自上而下照到晶体
    draw_beam(dr, (540, 330), (540, 615), VIOLET, 6, a)
    # 晶体
    cx, cy = CRYS
    dr.polygon([(cx - 70, cy - 26), (cx + 70, cy - 26), (cx + 82, cy + 26), (cx - 58, cy + 26)], fill=(120, 170, 220, int(70 * a)), outline=withalpha(ICE, 0.8 * a))
    if split:
        draw_beam(dr, (cx - 15, cy + 20), (330, LAB_SCREEN[1] - 10), RED, 4, a)
        draw_beam(dr, (cx + 15, cy + 20), (960, 860), RED, 4, a * 0.7)


def scene_lab(cv, dr, t):
    tg = t
    lab_layer(dr, t)
    # 屏幕
    x0, y0, x1, y1 = LAB_SCREEN
    dr.rectangle((x0, y0, x1, y1), outline=(143, 211, 255, 70), width=2)
    T0 = 24.0
    prog = clamp(0.28 + tg / T0)
    n = int(np.searchsorted(KIM_T, prog))
    tt = (KIM_T[:n] - 0.28) * T0
    age = tg - tt
    flash = np.clip(1 - age / 0.4, 0, 1) * 3
    cols = np.tile(np.array([[255, 236, 220]], np.float32) / 255, (n, 1))
    dot_field(cv, (x0, y0, x1, y1), KIM_X[:n], KIM_Y[:n], cols, 1.0, flash=flash)
    # 光子沿光束飞行
    k = int(tg / 0.35)
    for j in range(max(0, k - 2), k + 1):
        u = (tg - j * 0.35) / 0.7
        if 0 <= u <= 1:
            add_glow(cv, lerp(525, 330, u), lerp(660, LAB_SCREEN[1] - 10, u), RED, 7, 1.6)
            add_glow(cv, lerp(555, 960, u), lerp(660, 860, u), RED, 7, 1.2)
    add_glow(cv, CRYS[0], CRYS[1], VIOLET, 28, 0.5 + 0.1 * math.sin(t * 7))
    text(dr, (x1, y1 + 36), "D0 屏幕（示意）", font("sans_r", 26), withalpha(GREY, 0.9), anchor="rm")
    text(dr, (300, 900), "信号光子", font("sans_r", 28), withalpha(RED, 0.9), anchor="rm")
    text(dr, (900, 790), "孪生光子", font("sans_r", 28), withalpha(RED, 0.9), anchor="rm")
    head(dr, "未来的选择，能改变过去？", t, -1, y=230, size=68)
    if since("no", t) > 0:
        a = fade(t, CUE_T["no"], 0.25)
        f = font("serif_bk", 150)
        text(dr, (W // 2, 860), "不是", f, withalpha(hexc("ff8a7a"), a), stroke=6, sfill=(0, 0, 0, int(200 * a)))
        if since("erase_tease", t) > 0:
            pass
    if since("erase_tease", t) > 0:
        a = fade(t, CUE_T["erase_tease"], 0.4)
        dr.rounded_rectangle((60, 720, W - 60, 990), 20, fill=(4, 7, 14, int(205 * a)))
        text(dr, (W // 2, 790), "但确实有一样东西，被擦掉了", font("serif_b", 58), withalpha(CREAM, a))
    if since("whichpath", t) > 0:
        a = fade(t, CUE_T["whichpath"], 0.4)
        e = 1 - fade(t, CUE_T["whichpath"] + 3.5, 1.2)
        text(dr, (W // 2, 890), "“这个光子，走的是哪条路”", font("serif", 50), withalpha(ICE, a * (0.35 + 0.65 * e)))
        # 擦除：一道横线扫过
        u = ease((t - CUE_T["whichpath"] - 3.0) / 1.5)
        if u > 0:
            wline = font("serif", 50).getlength("“这个光子，走的是哪条路”")
            dr.line([(W / 2 - wline / 2, 892), (W / 2 - wline / 2 + wline * u, 892)], fill=withalpha(RED, 0.9), width=4)
            text(dr, (W // 2, 950), "擦掉的：路径信息   不是：已经发生的事", font("sans", 34), withalpha(CREAM, u))


# ───────────────────────── 预告：总图不变，条纹在分组里 ─────────────────────────
def draw_panel(cv, dr, rect, mask, t_shown=1.0, color_mode="white", label=None, curve=True, curve_col=None, a=1.0, flash=None, hist_scale=None):
    x0, y0, x1, y1 = rect
    dr.rectangle(rect, outline=(143, 211, 255, int(70 * a)), width=2)
    idx = np.where(mask)[0]
    idx = idx[KIM_T[idx] <= t_shown]
    if color_mode == "white":
        cols = np.tile(np.array([[1.0, 0.93, 0.86]], np.float32), (len(idx), 1))
    else:
        cols = np.array([np.array(DCOL[g][:3], np.float32) / 255 for g in KIM_G[idx]]).reshape(-1, 3)
    dot_field(cv, rect, KIM_X[idx], KIM_Y[idx], cols, a, flash=None if flash is None else flash[idx])
    if curve and len(idx) > 30:
        xc, hc = hist_curve(KIM_X[idx])
        sc = hist_scale or hc.max()
        pts = [(x0 + (xc[i] + 1) / 2 * (x1 - x0), y1 + 6 + 70 - 70 * hc[i] / sc) for i in range(len(xc))]
        pts = [(px, py + 0) for px, py in pts]
        cc = curve_col or ICE
        dr.line(pts, fill=withalpha(cc, 0.9 * a), width=3)
    if label:
        text(dr, (x0 + 8, y0 - 26), label, font("sans", 30), withalpha(CREAM, a), anchor="lm")


def scene_tease(cv, dr, t):
    t0 = CUE_T["tease_groups"]
    u = fade(t, t0 + 1.2, 1.4)
    top = (120, 420, 960, 600)
    draw_panel(cv, dr, top, KIM_G > 0, label="D0 上的全部光点：一团，无条纹", hist_scale=None)
    if u > 0:
        g1 = (120, 820, 520, 980)
        g2 = (560, 820, 960, 980)
        draw_panel(cv, dr, g1, KIM_G == 1, color_mode="col", label="事后分组 ①", curve_col=DCOL[1], a=u)
        draw_panel(cv, dr, g2, KIM_G == 2, color_mode="col", label="事后分组 ②", curve_col=DCOL[2], a=u)
        text(dr, (W // 2, 1180), "条纹只出现在事后的分组里", font("serif_b", 50), withalpha(CREAM, u))
    head(dr, "屏上的点，一个都没有动", t, t0, y=250, size=62)
    if since("no_signal", t) > 0:
        a = fade(t, CUE_T["no_signal"], 0.4)
        dr.rectangle((0, 1240, W, 1420), fill=(4, 7, 14, int(225 * a)))
        f = font("serif_b", 50)
        text(dr, (W // 2, 1290), "× 没有改写过去", f, withalpha(hexc("ff8a7a"), a))
        text(dr, (W // 2, 1370), "× 不能向过去发信号", f, withalpha(hexc("ff8a7a"), a))


# ───────────────────────── 两半 / 声明 ─────────────────────────
_cloud = {}


def cloud_sprite(seed, w=760, h=230):
    if seed not in _cloud:
        rs = np.random.default_rng(seed)
        im = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(im)
        for _ in range(26):
            cx, cy = rs.uniform(0.12, 0.88) * w, rs.uniform(0.35, 0.65) * h
            rx, ry = rs.uniform(0.08, 0.2) * w, rs.uniform(0.15, 0.3) * h
            d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=int(rs.uniform(120, 230)))
        im = im.filter(ImageFilter.GaussianBlur(22))
        a = np.asarray(im, np.float32) / 255
        tex = gaussian_filter(rs.normal(0, 1, (h, w)), 6)
        a = np.clip(a * (0.85 + 0.6 * tex / (tex.std() + 1e-6) * 0.25), 0, 1)
        wx = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (0.22 * w), 0, 1)
        wy = np.clip(np.minimum(np.arange(h), h - 1 - np.arange(h)) / (0.3 * h), 0, 1)
        a = a * (wy[:, None] ** 1.5) * (wx[None, :] ** 1.5)
        _cloud[seed] = a
    return _cloud[seed]


def blend_sprite(cv, alpha, x, y, col, op, rect):
    h, w = alpha.shape
    x0, y0 = int(x - w / 2), int(y - h / 2)
    rx0, ry0, rx1, ry1 = rect
    a0, b0 = max(x0, rx0, 0), max(y0, ry0, 0)
    a1, b1 = min(x0 + w, rx1, W), min(y0 + h, ry1, H)
    if a1 <= a0 or b1 <= b0:
        return
    al = alpha[b0 - y0:b1 - y0, a0 - x0:a1 - x0][..., None] * op
    reg = cv[b0:b1, a0:a1]
    reg[:] = reg * (1 - al) + np.array(col, np.float32) * al


def moon_sky(cv, dr, rect, t, cloud_u, moon_r=90, mx=None, my=None, a=1.0):
    """夜空 + 月 + 云；cloud_u：0=云遮月 1=云散"""
    x0, y0, x1, y1 = rect
    mx = mx if mx is not None else (x0 + x1) / 2
    my = my if my is not None else (y0 + y1) / 2
    rs = np.random.default_rng(3)
    for i in range(70):
        sx, sy = rs.uniform(x0, x1), rs.uniform(y0, y1)
        tw = 0.6 + 0.4 * math.sin(t * rs.uniform(0.5, 2) + i)
        add_glow(cv, sx, sy, (220, 225, 255), rs.uniform(0.8, 1.6), 0.5 * tw * a)
    add_glow(cv, mx, my, (255, 240, 205), moon_r * 1.7, (0.2 + 0.4 * cloud_u) * a)
    # 月轮（抗锯齿圆盘，画进 canvas，云才能盖住它）
    r = int(moon_r + 3)
    ys, xs = np.mgrid[int(my) - r:int(my) + r, int(mx) - r:int(mx) + r]
    dd = np.sqrt((xs - mx) ** 2 + (ys - my) ** 2)
    m = np.clip(moon_r - dd + 0.5, 0, 1)[..., None] * a
    ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
    if ok.all():
        reg = cv[int(my) - r:int(my) + r, int(mx) - r:int(mx) + r]
        shade = 1 - 0.06 * np.clip((xs - mx + ys - my) / moon_r, -1, 1)[..., None]
        reg[:] = reg * (1 - m) + np.array([250, 240, 214], np.float32) * shade * m
    occl = 1 - cloud_u
    s = moon_r / 110
    for k, (dy, sp, seed) in enumerate([(-30, 1.0, 1), (25, -0.85, 2), (70, 0.6, 3), (-80, -0.5, 4)]):
        off = (cloud_u * 560 * s + 14 * math.sin(t * 0.25 + k)) * (1 if sp > 0 else -1)
        spr = cloud_sprite(seed)
        if s < 0.95:
            key = (seed, round(s, 2))
            if key not in _cloud:
                im = Image.fromarray((spr * 255).astype(np.uint8)).resize((int(spr.shape[1] * s), int(spr.shape[0] * s)))
                _cloud[key] = np.asarray(im, np.float32) / 255
            spr = _cloud[key]
        blend_sprite(cv, spr, mx + off + sp * 30 * s, my + dy * s, (40, 44, 58), (0.55 + 0.4 * occl) * a, rect)


def scene_halves(cv, dr, t):
    t0 = CUE_T["halves"]
    a1 = fade(t, t0, 0.4)
    # 上：物理
    draw_panel(cv, dr, (160, 470, 920, 640), KIM_G > 0, a=a1, curve=False)
    text(dr, (W // 2, 380), "前一半 · 物理", font("serif_b", 56), withalpha(ICE, a1))
    text(dr, (W // 2, 700), "物理事实优先，宁可慢一点", font("sans_r", 34), withalpha(CREAM, a1 * 0.85))
    a2 = fade(t, CUE_T["halves2"], 0.5)
    if a2 > 0:
        moon_sky(cv, dr, (160, 860, 920, 1240), t, 0.55, moon_r=70, a=a2)
        text(dr, (W // 2, 800), "后一半 · 忏悔", font("serif_b", 56), withalpha(GOLD, a2))
        text(dr, (W // 2, 1300), "做过的事擦不掉，忏悔还有什么用？", font("serif", 42), withalpha(CREAM, a2))


def scene_disc(cv, dr, t):
    t0 = CUE_T["disclaimer"]
    a = fade(t, t0, 0.5)
    card(dr, (110, 640, 970, 1160), fill=(10, 12, 18, 230), outline=(217, 178, 95, 120))
    text(dr, (W // 2, 760), "先说清楚", font("sans", 36), withalpha(GOLD, a))
    text(dr, (W // 2, 880), "这是类比，不是证明", font("serif_b", 64), withalpha(CREAM, a))
    text(dr, (W // 2, 1000), "物理学没有证明佛法", font("serif_b", 64), withalpha(CREAM, fade(t, t0 + 2.5, 0.6)))


# ───────────────────────── 双缝 ─────────────────────────
SL_SCREEN = (110, 1040, 970, 1260)
SL_BAR_Y = 640


def scene_slit(cv, dr, t):
    s0 = CUE_T["slit_setup"]
    tag_t = CUE_T["slit_tag"]
    blob_t = CUE_T["slit_blob"]
    ent_t = CUE_T["slit_entangle"]
    # 光源
    add_glow(cv, 540, 450, RED, 16, 1.2)
    text(dr, (640, 450), "光源", font("sans_r", 28), withalpha(GREY, 0.9))
    # 挡板与两条缝
    dr.rectangle((110, SL_BAR_Y - 10, 470, SL_BAR_Y + 10), fill=(110, 125, 150, 255))
    dr.rectangle((500, SL_BAR_Y - 10, 580, SL_BAR_Y + 10), fill=(110, 125, 150, 255))
    dr.rectangle((610, SL_BAR_Y - 10, 970, SL_BAR_Y + 10), fill=(110, 125, 150, 255))
    tagged = t >= tag_t
    if tagged:
        a = fade(t, tag_t, 0.5)
        dr.rectangle((470, SL_BAR_Y - 26, 500, SL_BAR_Y + 26), fill=withalpha(DCOL[1], a))
        dr.rectangle((580, SL_BAR_Y - 26, 610, SL_BAR_Y + 26), fill=withalpha(DCOL[2], a))
        text(dr, (485, SL_BAR_Y - 52), "左", font("sans", 30), withalpha(DCOL[1], a))
        text(dr, (595, SL_BAR_Y - 52), "右", font("sans", 30), withalpha(DCOL[2], a))
    dr.rectangle(SL_SCREEN, outline=(143, 211, 255, 70), width=2)
    text(dr, (SL_SCREEN[2], SL_SCREEN[3] + 34), "屏幕（示意）", font("sans_r", 26), withalpha(GREY, 0.9), anchor="rm")
    # 光点：分两个阶段（干涉 / 有路径信息）
    bt = tag_t + 1.6  # 标记后立即开始累积无条纹分布
    if t < bt:
        T = max(8.0, CUE_T["slit_fringe"] - CUE_T["slit_dots"] + 6)
        prog = clamp((t - CUE_T["slit_dots"]) / T)
        n = int(np.searchsorted(SL_T, prog))
        xs, ys = SL_FR_X[:n], SL_Y[:n]
        if tagged:
            # 标记阶段：既有条纹淡出
            fa = 1 - fade(t, tag_t + 1.0, 1.0)
        else:
            fa = 1
        tt = CUE_T["slit_dots"] + SL_T[:n] * T
        flash = np.clip(1 - (t - tt) / 0.4, 0, 1) * 3
        cols = np.tile(np.array([[1.0, 0.93, 0.86]], np.float32), (n, 1))
        dot_field(cv, SL_SCREEN, xs, ys, cols, fa, flash=flash)
        if n > 200 and fa > 0.02:
            xc, hc = hist_curve(xs)
            x0, y0, x1, y1 = SL_SCREEN
            pts = [(x0 + (xc[i] + 1) / 2 * (x1 - x0), y1 + 100 - 80 * hc[i] / hc.max()) for i in range(len(xc))]
            dr.line(pts, fill=withalpha(ICE, 0.9 * fa), width=3)
        # 飞行中的光子
        if t > CUE_T["slit_dots"] and not tagged:
            u = ((t - CUE_T["slit_dots"]) % 0.9) / 0.9
            xs_ = 540 + (rng0.uniform(-1, 1) * 0)
            yy = lerp(450, SL_SCREEN[1], u)
            add_glow(cv, 540, yy, RED, 7, 1.5)
            if u > 0.25:
                for xo in (485, 595):
                    add_glow(cv, lerp(xo, 540, 0), yy, RED, 10, 0.25)
        if tagged:
            u = ((t - tag_t) % 0.8) / 0.8
            side = int((t - tag_t) / 0.8) % 2
            xo = 485 if side == 0 else 595
            col = DCOL[1] if side == 0 else DCOL[2]
            yy = lerp(450, SL_SCREEN[1], u)
            xx = lerp(540, xo, clamp(u * 2.5)) if yy < SL_BAR_Y else lerp(xo, xo + (rng0.uniform(-200, 200)), 0)
            add_glow(cv, xx, yy, col, 8, 1.6)
    else:
        T = 12.0
        prog = clamp((t - bt) / T)
        n = int(np.searchsorted(SL_T, prog))
        xs, ys = SL_BL_X[:n], SL_Y[:n]
        cols = np.array([np.array(DCOL[1 + g][:3], np.float32) / 255 for g in SL_TAG[:n]]).reshape(-1, 3)
        tt = bt + SL_T[:n] * T
        flash = np.clip(1 - (t - tt) / 0.4, 0, 1) * 3
        dot_field(cv, SL_SCREEN, xs, ys, cols, 1.0, flash=flash)
        if n > 200:
            xc, hc = hist_curve(xs)
            x0, y0, x1, y1 = SL_SCREEN
            pts = [(x0 + (xc[i] + 1) / 2 * (x1 - x0), y1 + 100 - 80 * hc[i] / hc.max()) for i in range(len(xc))]
            dr.line(pts, fill=withalpha(ICE, 0.9), width=3)
    # 标题与注释
    if t < tag_t:
        head(dr, "双缝：一颗一颗地发射", t, s0, size=60)
        if t > CUE_T["slit_fringe"]:
            text(dr, (W // 2, 340), "累积出明暗相间的干涉条纹", font("sans", 36), withalpha(ICE, fade(t, CUE_T["slit_fringe"])))
    elif t < blob_t:
        head(dr, "给每个光子做标记：路径信息", t, tag_t, size=58)
    elif t < ent_t:
        head(dr, "有了路径信息，条纹消失", t, blob_t, size=60)
        if t > LINE_BY_CUE["slit_blob"][1]["start"]:
            text(dr, (W // 2, 340), "不必有人去看 · 只要原则上可取得", font("sans", 36), withalpha(ICE, fade(t, LINE_BY_CUE["slit_blob"][1]["start"])))
    else:
        head(dr, "“测量” = 与别的东西发生纠缠", t, ent_t, size=56)
        a = fade(t, ent_t, 0.6)
        # 光子与环境的纠缠连线
        px, py = 760, 820
        ex, ey = 930, 900
        add_glow(cv, px, py, RED, 10, 1.4 * a)
        add_glow(cv, ex, ey, ICE, 10, 1.4 * a)
        pts = [(lerp(px, ex, i / 40), lerp(py, ey, i / 40) + 10 * math.sin(i / 3 + t * 4)) for i in range(41)]
        dr.line(pts, fill=withalpha(ICE, 0.7 * a), width=2)
        text(dr, (ex, ey + 40), "环境", font("sans_r", 26), withalpha(ICE, a))
        text(dr, (px - 20, py - 34), "光子", font("sans_r", 26), withalpha(RED, a))
        text(dr, (W // 2, 340), "不是意识在看，路径痕迹留在了别处", font("sans", 36), withalpha(CREAM, a))
    if since("carroll1", t) > 0:
        a = fade(t, CUE_T["carroll1"], 0.5)
        card(dr, (80, 700, 1000, 1010), fill=(8, 12, 22, int(235 * a)), outline=(143, 211, 255, int(110 * a)))
        f = font("serif", 44)
        para(dr, W // 2, 770, "任何形式的纠缠，只要让两条路径变得可以区分，就会破坏干涉。", f, withalpha(CREAM, a), 820)
        text(dr, (940, 960), "—— 肖恩·卡罗尔（Sean Carroll）大意", font("sans_r", 28), withalpha(ICE, a), anchor="rm")
    if since("question", t) > 0:
        a = fade(t, CUE_T["question"], 0.5)
        dr.rectangle((0, 680, W, 1030), fill=(4, 7, 14, int(225 * a)))
        f = font("serif_b", 54)
        para(dr, W // 2, 760, "光子已经落在屏上，\n事后再擦掉路径信息，\n条纹会回来吗？", f, withalpha(CREAM, a), 900, lh=84)


# ───────────────────────── 历史 / 论文 ─────────────────────────
def scene_hist(cv, dr, t):
    t0 = CUE_T["history"]
    head(dr, "从思想实验到实验室", t, t0, size=60)
    items = [
        ("思想源头", "惠勒：延迟选择思想实验", t0 + 0.2),
        ("1982", "斯库利 & 德吕尔 提出量子擦除方案\nPhys. Rev. A 25, 2208", LINE_BY_CUE["history"][1]["start"]),
        ("1999.3", "实验论文提交 arXiv\nquant-ph/9903047", CUE_T["paper"]),
        ("2000.1.3", "发表于《物理评论快报》\nPhys. Rev. Lett. 84, 1", CUE_T["paper"] + 3.0),
    ]
    x = 220
    dr.line([(x, 420), (x, 1300)], fill=(143, 211, 255, 90), width=3)
    for i, (yr, s, ts) in enumerate(items):
        a = fade(t, ts, 0.6)
        y = 480 + i * 220
        add_glow(cv, x, y, ICE, 8, 1.2 * a)
        text(dr, (x - 30, y), yr, font("sans", 34), withalpha(ICE, a), anchor="rm")
        para(dr, x + 40, y - 20, s, font("serif", 40), withalpha(CREAM, a), 720, lh=58, anchor_center=False)
    if since("paper", t) > 0:
        a = fade(t, CUE_T["paper"] + 1.5, 0.6)
        text(dr, (W // 2, 1390), "Y.-H. Kim, R. Yu, S. P. Kulik, Y. Shih, M. O. Scully", font("sans_r", 28), withalpha(GREY, a))
        text(dr, (W // 2, 1435), "“A Delayed Choice Quantum Eraser”", font("serif", 32), withalpha(CREAM, a))


# ───────────────────────── Kim 实验光路（俯视示意） ─────────────────────────
P = dict(src=(60, 760), slit=(240, 760), A=(495, 760), B=(585, 760), LS=(540, 640), D0=(540, 575),
         BSA=(495, 930), BSB=(585, 930), D3=(150, 930), D4=(930, 930), MA=(380, 1110), MB=(700, 1110),
         BS=(540, 1270), D1=(360, 1390), D2=(720, 1390))
D0_PANEL = (150, 340, 930, 500)
IDLER_PATHS = {
    3: lambda o: [P[o], P["BSA"], P["D3"]],
    4: lambda o: [P[o], P["BSB"], P["D4"]],
    1: lambda o: [P[o], P["BSA" if o == "A" else "BSB"], P["MA" if o == "A" else "MB"], P["BS"], P["D1"]],
    2: lambda o: [P[o], P["BSA" if o == "A" else "BSB"], P["MA" if o == "A" else "MB"], P["BS"], P["D2"]],
}


def along(pts, u):
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = sum(seg) * clamp(u)
    for i, s in enumerate(seg):
        if L <= s:
            v = L / s if s else 0
            return (lerp(pts[i][0], pts[i + 1][0], v), lerp(pts[i][1], pts[i + 1][1], v))
        L -= s
    return pts[-1]


def detector(dr, xy, name, col, lit=0.0, a=1.0):
    x, y = xy
    dr.rounded_rectangle((x - 34, y - 24, x + 34, y + 24), 8, fill=(18, 24, 38, int(255 * a)), outline=withalpha(col, a), width=3)
    if lit > 0:
        dr.rounded_rectangle((x - 34, y - 24, x + 34, y + 24), 8, fill=withalpha(col, 0.55 * lit * a))
    text(dr, (x, y), name, font("sans", 26), withalpha(CREAM, a))


def splitter(dr, xy, a=1.0, ang=45):
    x, y = xy
    d = 26
    if ang == 45:
        dr.line([(x - d, y + d), (x + d, y - d)], fill=withalpha(ICE, a), width=5)
    else:
        dr.line([(x - d, y - d), (x + d, y + d)], fill=withalpha(ICE, a), width=5)


def kim_static(cv, dr, t, a=1.0, hl=None):
    """光路图。hl: 高亮 'd34' / 'd12' / None"""
    # 泵浦 + 双缝
    draw_beam(dr, P["src"], (P["A"][0] - 60, 760), VIOLET, 5, a)
    dr.rectangle((P["slit"][0] - 8, 690, P["slit"][0] + 8, 742), fill=(110, 125, 150, int(255 * a)))
    dr.rectangle((P["slit"][0] - 8, 778, P["slit"][0] + 8, 830), fill=(110, 125, 150, int(255 * a)))
    # 晶体
    dr.rectangle((440, 720, 640, 800), fill=(120, 170, 220, int(60 * a)), outline=withalpha(ICE, 0.8 * a), width=2)
    text(dr, (660, 812), "晶体", font("sans_r", 24), withalpha(GREY, a), anchor="lm")
    text(dr, (P["A"][0], 742), "A", font("sans", 26), withalpha(CREAM, a))
    text(dr, (P["B"][0], 742), "B", font("sans", 26), withalpha(CREAM, a))
    # 信号光路
    for o in ("A", "B"):
        dr.line([P[o], P["LS"]], fill=withalpha(RED, 0.35 * a), width=2)
    dr.line([P["LS"], P["D0"]], fill=withalpha(RED, 0.35 * a), width=2)
    dr.ellipse((P["LS"][0] - 60, P["LS"][1] - 10, P["LS"][0] + 60, P["LS"][1] + 10), outline=withalpha(ICE, 0.8 * a), width=2)
    text(dr, (P["LS"][0] + 74, P["LS"][1]), "透镜", font("sans_r", 22), withalpha(GREY, a), anchor="lm")
    # 孪生光路
    ca = {None: 0.35, "d34": 0.2, "d12": 0.2}[hl]
    for o, bs, m in (("A", "BSA", "MA"), ("B", "BSB", "MB")):
        dr.line([P[o], P[bs]], fill=withalpha(RED, 0.35 * a), width=2)
        c34 = 0.9 if hl == "d34" else ca
        c12 = 0.9 if hl == "d12" else ca
        dr.line([P[bs], P["D3" if o == "A" else "D4"]], fill=withalpha(RED, c34 * a), width=3 if hl == "d34" else 2)
        dr.line([P[bs], P[m], P["BS"]], fill=withalpha(RED, c12 * a), width=3 if hl == "d12" else 2)
    for d in (1, 2):
        dr.line([P["BS"], P[f"D{d}"]], fill=withalpha(RED, (0.9 if hl == "d12" else ca) * a), width=3 if hl == "d12" else 2)
    splitter(dr, P["BSA"], a, 45)
    splitter(dr, P["BSB"], a, -45)
    splitter(dr, P["BS"], a, 45)
    for m in ("MA", "MB"):
        x, y = P[m]
        dr.line([(x - 22, y - 22), (x + 22, y + 22)] if m == "MA" else [(x - 22, y + 22), (x + 22, y - 22)], fill=withalpha(GREY, a), width=6)
    text(dr, (P["BSA"][0] - 20, P["BSA"][1] + 46), "分束器", font("sans_r", 22), withalpha(GREY, a))
    text(dr, (P["BS"][0], P["BS"][1] + 50), "分束器（合路）", font("sans_r", 22), withalpha(GREY, a))
    badge(dr, "示意", (1040, 1450), GREY, 24)


def kim_pairs(cv, dr, t, t_from, period=0.75, a=1.0, lit_cb=None):
    """周期性发射光子对：信号光子短路到 D0，孪生光子长路随机到 D1–D4"""
    lit = {1: 0, 2: 0, 3: 0, 4: 0, 0: 0}
    if t < t_from:
        return lit
    k = int((t - t_from) / period)
    for j in range(max(0, k - 4), k + 1):
        te = t_from + j * period
        dt = t - te
        rr = np.random.default_rng(j + 11)
        o = "A" if rr.random() < 0.5 else "B"
        g = (3 if o == "A" else 4) if rr.random() < 0.5 else (1 if rr.random() < 0.5 else 2)
        ts, ti = 0.45, 1.6
        if 0 <= dt <= ts:
            add_glow(cv, *along([P[o], P["LS"], P["D0"]], dt / ts), RED, 7, 1.6 * a)
        if ts < dt < ts + 0.5:
            lit[0] = max(lit[0], 1 - (dt - ts) / 0.5)
        if 0 <= dt <= ti:
            add_glow(cv, *along(IDLER_PATHS[g](o), dt / ti), hexc("ff9a7a"), 7, 1.6 * a)
        if ti < dt < ti + 0.6:
            lit[g] = max(lit[g], 1 - (dt - ti) / 0.6)
    return lit


def scene_kim(cv, dr, t):
    t0 = CUE_T["kim_crystal"]
    hl = None
    if CUE_T["kim_d34"] <= t < CUE_T["kim_d12"]:
        hl = "d34"
    elif CUE_T["kim_d12"] <= t < CUE_T["abstract"]:
        hl = "d12"
    dim = 1 - 0.75 * fade(t, CUE_T["abstract"], 0.6) + 0.5 * fade(t, CUE_T["kim_claim"], 0.6)
    dim = clamp(dim, 0.25, 1)
    kim_static(cv, dr, t, dim, hl)
    lit = kim_pairs(cv, dr, t, CUE_T["kim_pair"], a=dim)
    add_glow(cv, (P["A"][0] + P["B"][0]) / 2, 760, VIOLET, 30, 0.5 * dim)
    # D0：左右扫描
    scan = 0
    if t > CUE_T["kim_signal"]:
        scan = 200 * math.sin((t - CUE_T["kim_signal"]) * 0.8)
    show_det = lambda key, ts: fade(t, ts, 0.5) * dim
    detector(dr, (P["D0"][0] + scan * 0.6, P["D0"][1]), "D0", RED, lit[0], show_det("D0", CUE_T["kim_signal"]))
    for d, ts in ((3, CUE_T["kim_split"]), (4, CUE_T["kim_split"]), (1, CUE_T["kim_split"]), (2, CUE_T["kim_split"])):
        a = show_det(d, ts)
        if hl == "d34" and d in (1, 2) or hl == "d12" and d in (3, 4):
            a *= 0.45
        detector(dr, P[f"D{d}"], f"D{d}", DCOL[d], lit[d], a)
    # D0 记录屏（总图）
    a = fade(t, CUE_T["kim_signal"], 0.6) * dim
    if a > 0:
        prog = clamp((t - CUE_T["kim_signal"]) / 60)
        draw_panel(cv, dr, D0_PANEL, KIM_G > 0, t_shown=prog, a=a, label="D0 的记录（总图）", curve=False)
    # 标题
    if t < CUE_T["kim_signal"]:
        head(dr, "延迟选择量子擦除", t, t0, y=250, size=64)
    elif t < CUE_T["kim_idler"]:
        pass
    # 注释
    notes = [("kim_idler", "孪生光子多走约 2.5 米 · 晚到至少 8 纳秒", ICE),
             ("kim_split", "分束器随机：反射或透过，各一半", ICE),
             ("kim_d34", "D3 / D4：路径信息保留", DCOL[3]),
             ("kim_d12", "D1 / D2：两路合一，路径信息被擦掉", DCOL[1])]
    cur = None
    for c, s, col in notes:
        if since(c, t) >= 0:
            cur = (c, s, col)
    if cur and t < CUE_T["abstract"]:
        a = fade(t, CUE_T[cur[0]], 0.4)
        f = font("sans", 36)
        wbox = f.getlength(cur[1]) + 60
        dr.rounded_rectangle((W / 2 - wbox / 2, 200, W / 2 + wbox / 2, 270), 14, fill=(8, 12, 22, int(225 * a)))
        text(dr, (W // 2, 235), cur[1], f, withalpha(cur[2], a))
    # 摘要卡
    if CUE_T["abstract"] <= t < CUE_T["kim_claim"]:
        a = fade(t, CUE_T["abstract"], 0.6)
        card(dr, (70, 560, 1010, 1240), fill=(8, 12, 22, int(240 * a)), outline=(143, 211, 255, int(120 * a)))
        text(dr, (W // 2, 620), "论文摘要原句", font("sans", 32), withalpha(ICE, a))
        en = ("The which-path or both-path information of a quantum can be erased or marked by its "
              "entangled twin even after the registration of the quantum.")
        para(dr, W // 2, 690, en, font("serif", 34), withalpha(CREAM, a), 840, lh=50)
        zh = "光子被记录之后，“走哪条路”的信息，仍可经由纠缠的孪生光子被擦除或标记。"
        para(dr, W // 2, 900, zh, font("serif", 40), withalpha(CREAM, a * fade(t, CUE_T["abstract"] + 1.0, 0.8)), 840, lh=60)
        text(dr, (W // 2, 1190), "Kim et al., arXiv:quant-ph/9903047 / PRL 84, 1 (2000)", font("sans_r", 26), withalpha(GREY, a))
        if since("abstract_note", t) > 0:
            u = fade(t, CUE_T["abstract_note"], 0.5)
            f = font("serif_b", 48)
            dr.rounded_rectangle((120, 1290, 960, 1420), 16, fill=(30, 22, 10, int(235 * u)), outline=withalpha(GOLD, u), width=2)
            text(dr, (W // 2, 1355), "被擦除的是信息，不是记录", f, withalpha(GOLD, u))
    if since("kim_claim", t) > 0:
        a = fade(t, CUE_T["kim_claim"], 0.5)
        dr.rectangle((0, 120, W, 330), fill=(4, 7, 14, int(200 * a)))
        text(dr, (W // 2, 200), "网上说：后来的擦除", font("serif_b", 54), withalpha(CREAM, a))
        text(dr, (W // 2, 280), "改变了过去光子的行为？", font("serif_b", 54), withalpha(hexc("ff8a7a"), a))


# ───────────────────────── 四个关键事实（分组画面） ─────────────────────────
F_TOP = (120, 400, 960, 570)
F_SUB = {1: (120, 740, 520, 870), 2: (560, 740, 960, 870), 3: (120, 1090, 520, 1220), 4: (560, 1090, 960, 1220)}


def scene_facts(cv, dr, t):
    t1 = CUE_T["f1"]
    tc = CUE_T["f2_color"]
    t_r1, t_r2, t_sum, t_34 = CUE_T["f2_r1"], CUE_T["f2_r2"], CUE_T["f2_sum"], CUE_T["f2_r34"]
    colored = t >= tc + 1.0
    # 标号
    if t < CUE_T["f2"]:
        head(dr, "① D0 上的全部光点", t, t1, size=60)
    else:
        head(dr, "② 条纹出现在分组之后", t, CUE_T["f2"], size=60)
    # 顶部总图（始终不变）
    cm = "col" if colored else "white"
    a_top = 1.0
    draw_panel(cv, dr, F_TOP, KIM_G > 0, color_mode=cm, label="D0 总图", curve=True)
    if t < CUE_T["f2"]:
        u = fade(t, CUE_T["f1_blob"], 0.5)
        text(dr, (W // 2, 800), "始终是一团，没有条纹", font("serif_b", 56), withalpha(CREAM, u))
        if t > LINE_BY_CUE["f1_blob"][1]["start"]:
            u2 = fade(t, LINE_BY_CUE["f1_blob"][1]["start"], 0.5)
            text(dr, (W // 2, 920), "从头到尾，一个点都没有改变", font("serif", 46), withalpha(GOLD, u2))
        return
    if t < tc + 1.0:
        text(dr, (W // 2, 680), "符合计数：按孪生光子落在哪个探测器分组", font("sans", 36), withalpha(ICE, fade(t, tc, 0.5)))
    # 分组面板：点从总图飞到各组
    fly = ease((t - tc - 1.8) / 2.0)
    if fly > 0:
        for g in (1, 2, 3, 4):
            rect = F_SUB[g]
            a = fly
            focus = 1.0
            if t >= t_r1 and t < t_34:
                focus = 1.0 if (g == 1 and t < t_r2) or (g in (1, 2) and t >= t_r2) else 0.3
            if t >= t_34:
                focus = 1.0 if g in (3, 4) or t >= t_34 + 3 else 0.35
            if t >= t_sum and t < t_34 and g in (1, 2):
                # 叠回：两组滑到中间合并
                mv = ease((t - t_sum - 0.5) / 2.0)
                cxm = (120 + 960) / 2
                w_ = 400
                xa = lerp(rect[0], cxm - w_ / 2, mv)
                rect = (int(xa), rect[1], int(xa + w_), rect[3])
            draw_panel(cv, dr, rect, KIM_G == g, color_mode="col", label=f"与 D{g} 配对" if not (t >= t_sum and t < t_34 and g == 2) else None,
                       curve=True, curve_col=DCOL[g], a=a * focus)
        if t_sum <= t < t_34:
            mv = ease((t - t_sum - 0.5) / 2.0)
            if mv > 0.95:
                u = fade(t, t_sum + 2.6, 0.5)
                # 合并后的包络
                x0, x1 = 340, 740
                idx = (KIM_G == 1) | (KIM_G == 2)
                xc, hc = hist_curve(KIM_X[idx])
                pts = [(x0 + (xc[i] + 1) / 2 * (x1 - x0), F_SUB[1][3] + 6 + 70 - 70 * hc[i] / hc.max()) for i in range(len(xc))]
                dr.line(pts, fill=withalpha(CREAM, u), width=4)
                text(dr, (W // 2, 1000), "条纹 + 反条纹 = 一团", font("serif_b", 50), withalpha(CREAM, u))
    # 说明字
    if t_r1 <= t < t_r2:
        text(dr, (W // 2, 1000), "D1 组：干涉条纹", font("serif_b", 48), withalpha(DCOL[1], fade(t, t_r1)))
    elif t_r2 <= t < t_sum:
        text(dr, (W // 2, 1000), "D2 组：反条纹（错开半个周期）", font("serif_b", 46), withalpha(DCOL[2], fade(t, t_r2)))
    elif t >= t_34:
        text(dr, (W // 2, 1000), "D3、D4 组：没有条纹", font("serif_b", 48), withalpha(DCOL[3], fade(t, t_34)))
        if t > LINE_BY_CUE["f2_r34"][1]["start"]:
            u = fade(t, LINE_BY_CUE["f2_r34"][1]["start"])
            dr.rounded_rectangle((80, 1330, 1000, 1440), 14, fill=(8, 12, 22, int(220 * u)))
            text(dr, (W // 2, 1362), "D1/D2：两路合一，可能性重新叠加", font("sans", 32), withalpha(DCOL[1], u))
            text(dr, (W // 2, 1408), "D3/D4：路径已写明，无可叠加", font("sans", 32), withalpha(DCOL[3], u))


def scene_analogy(cv, dr, t):
    t0 = CUE_T["f2_analogy"]
    head(dr, "打个比方：一张成绩单", t, t0, size=60)
    rs = np.random.default_rng(5)
    scores = rs.integers(58, 99, 40)
    sex = rs.integers(0, 2, 40)
    split = ease((t - t0 - 2.5) / 1.0) * (1 - ease((t - t0 - 7.5) / 1.0))
    f = font("sans", 34)
    ia = ib = 0
    for i in range(40):
        r_, c_ = divmod(i, 5)
        x0 = 200 + c_ * 140
        y0 = 450 + r_ * 80
        if sex[i] == 0:
            xs, ys = 120 + (ia % 3) * 120, 450 + (ia // 3) * 80
            ia += 1
        else:
            xs, ys = 600 + (ib % 3) * 120, 450 + (ib // 3) * 80
            ib += 1
        x = lerp(x0, xs, split)
        y = lerp(y0, ys, split)
        col = DCOL[1] if sex[i] == 0 else DCOL[2]
        cc = withalpha(col, 0.35 + 0.65 * split) if split > 0.01 else CREAM
        dr.rounded_rectangle((x, y, x + 100, y + 60), 10, outline=withalpha(cc, 0.8), width=2)
        text(dr, (x + 50, y + 30), str(scores[i]), f, cc)
    if split > 0.5:
        text(dr, (300, 400), "男生", font("sans", 34), withalpha(DCOL[1], split))
        text(dr, (780, 400), "女生", font("sans", 34), withalpha(DCOL[2], split))
    u = fade(t, t0 + 8.5, 0.6)
    text(dr, (W // 2, 1180), "分组，没有改动任何一个分数", font("serif_b", 52), withalpha(GOLD, u))
    if len(LINE_BY_CUE["f2_analogy"]) > 1 and t > LINE_BY_CUE["f2_analogy"][1]["start"]:
        u = fade(t, LINE_BY_CUE["f2_analogy"][1]["start"], 0.6)
        dr.rectangle((0, 1240, W, 1420), fill=(4, 7, 14, int(230 * u)))
        text(dr, (W // 2, 1300), "条纹本来就藏在两个光子的关联里", font("serif", 44), withalpha(CREAM, u))
        text(dr, (W // 2, 1370), "对上号，才看得出来", font("serif", 44), withalpha(CREAM, u))


def scene_time(cv, dr, t):
    t0 = CUE_T["f3"]
    head(dr, "③ 不能向过去发信号", t, t0, size=60)
    order = since("f3_order", t) > 0
    y = 640
    x0, x1 = 140, 940
    dr.line([(x0, y), (x1, y)], fill=withalpha(CREAM, 0.6), width=3)
    dr.polygon([(x1, y - 10), (x1 + 20, y), (x1, y + 10)], fill=withalpha(CREAM, 0.6))
    text(dr, (x1, y + 40), "时间", font("sans_r", 26), withalpha(GREY, 1), anchor="rm")
    sw = ease((t - CUE_T.get("f3_order", 1e9) - 1.0) / 1.5) if order else 0
    xa = lerp(250, 560, sw)
    xb = lerp(560, 250, sw)
    for xx, lab, col in ((xa, "信号光子到 D0", RED), (xb, "孪生光子到 D1–D4", DCOL[1])):
        add_glow(cv, xx, y, col, 9, 1.5)
        text(dr, (xx, y - 50), lab, font("sans", 30), withalpha(col, 1))
    a = fade(t, t0 + 1.5, 0.5)
    text(dr, (560 if not order else 250, y + 50), "+8 纳秒" if not order else "", font("sans_r", 26), withalpha(GREY, a))
    # 经典通信
    u = fade(t, LINE_BY_CUE["f3"][1]["start"], 0.6)
    if u > 0:
        xc = 820
        dr.line([(xb, y + 110), (xc, y + 110)], fill=withalpha(ICE, u), width=3)
        text(dr, (xc + 10, y + 110), "电缆传来\n≤ 光速", font("sans", 28), withalpha(ICE, u), anchor="lm")
        text(dr, (W // 2, y + 190), "→ 才能分组", font("serif", 40), withalpha(CREAM, u))
    # 只看 D0
    if since("f3_no", t) > 0:
        u = fade(t, CUE_T["f3_no"], 0.5) * (1 - (fade(t, CUE_T["f3_order"] + 2.0, 0.5) if order else 0))
        draw_panel(cv, dr, (160, 990, 920, 1130), KIM_G > 0, a=u, label="只看 D0：读不出任何东西", curve=False)
        text(dr, (W // 2, 1230), "× 不能向过去发信号", font("serif_b", 52), withalpha(hexc("ff8a7a"), u))
    if order:
        u = fade(t, CUE_T["f3_order"] + 2.5, 0.6)
        dr.rectangle((0, 960, W, 1300), fill=(4, 7, 14, int(235 * u)))
        text(dr, (W // 2, 1060), "先后次序对调", font("serif_b", 50), withalpha(CREAM, u))
        text(dr, (W // 2, 1150), "分组后的统计结果：一模一样", font("serif_b", 50), withalpha(GOLD, u))
        text(dr, (W // 2, 1230), "（按量子力学计算）", font("sans_r", 30), withalpha(GREY, u))


def scene_f4(cv, dr, t):
    t0 = CUE_T["f4"]
    head(dr, "④ 擦掉的到底是什么", t, t0, size=60)
    a = fade(t, t0 + 0.5, 0.6)
    card(dr, (90, 430, 990, 820), fill=(8, 12, 22, int(225 * a)))
    text(dr, (150, 520), "擦掉的", font("sans", 36), withalpha(ICE, a), anchor="lm")
    para(dr, 330, 520, "“走哪条路”的信息，还能不能被取得", font("serif_b", 42), withalpha(CREAM, a), 600, lh=60, anchor_center=False)
    dr.line([(140, 640), (940, 640)], fill=withalpha(GREY, 0.4 * a), width=2)
    b = fade(t, t0 + 3.0, 0.6)
    text(dr, (150, 720), "没擦掉", font("sans", 36), withalpha(hexc("ff8a7a"), b), anchor="lm")
    text(dr, (330, 720), "已经发生、已经记录的事", font("serif_b", 42), withalpha(CREAM, b), anchor="lm")
    if since("carroll2", t) > 0:
        u = fade(t, CUE_T["carroll2"], 0.6)
        card(dr, (70, 900, 1010, 1390), fill=(8, 12, 22, int(240 * u)), outline=(143, 211, 255, int(110 * u)))
        para(dr, W // 2, 980, "延迟的测量，只是在选择我们去看纠缠态的哪一部分；屏幕上的总体分布，从来没有变过。", font("serif", 44), withalpha(CREAM, u), 840, lh=70)
        text(dr, (960, 1290), "—— 肖恩·卡罗尔 大意", font("sans_r", 28), withalpha(ICE, u), anchor="rm")
        text(dr, (960, 1335), "“The Notorious Delayed-Choice Quantum Eraser”, 2019", font("sans_r", 24), withalpha(GREY, u), anchor="rm")


def scene_sum(cv, dr, t):
    t0 = CUE_T["sum1"]
    draw_panel(cv, dr, (160, 560, 920, 760), KIM_G > 0, label=None, curve=False, a=1 - fade(t, CUE_T["sum3"], 0.6) * 0.97)
    a = fade(t, t0, 0.5)
    text(dr, (W // 2, 400), "过去的记录，一个点都没动", font("serif_b", 62), withalpha(CREAM, a * (1 - fade(t, CUE_T["sum3"], 0.5))))
    b = fade(t, CUE_T["sum2"], 0.5) * (1 - fade(t, CUE_T["sum3"], 0.5))
    text(dr, (W // 2, 920), "变的，是我们怎样分组、怎样理解", font("serif_b", 54), withalpha(GOLD, b))
    if since("sum3", t) > 0:
        u = fade(t, CUE_T["sum3"], 0.5)
        f = font("serif_b", 46)
        for i, s in enumerate(["× 未来改变了过去", "× 意识让光子“变卦”", "× 穿越时间的电话"]):
            uu = fade(t, CUE_T["sum3"] + 1.5 + i * 2.2, 0.5)
            text(dr, (W // 2, 420 + i * 100), s, f, withalpha(hexc("ff8a7a"), uu))
        if len(LINE_BY_CUE["sum3"]) > 1 and t > LINE_BY_CUE["sum3"][1]["start"]:
            v = fade(t, LINE_BY_CUE["sum3"][1]["start"], 0.6)
            # 两个相距很远的光子，纠缠连线
            ax, bx, yy = 200, 880, 1000
            add_glow(cv, ax, yy, RED, 10, 1.5 * v)
            add_glow(cv, bx, yy, hexc("ff9a7a"), 10, 1.5 * v)
            pts = [(lerp(ax, bx, i / 80), yy + 14 * math.sin(i / 5 + t * 3)) for i in range(81)]
            dr.line(pts, fill=withalpha(ICE, 0.6 * v), width=2)
            text(dr, (W // 2, 1120), "真正的奇妙：相隔很远的精确关联", font("serif_b", 48), withalpha(GOLD, v))


def scene_stars(cv, dr, t):
    t0 = CUE_T["to_stars"]
    u = ease((t - t0) / (cue_span("to_stars")[1] - t0 + 1.4))
    # 光点上升，化作星
    idx = np.arange(0, N_KIM, 3)
    x0, y0, x1, y1 = (160, 560, 920, 760)
    px = x0 + (KIM_X[idx] + 1) / 2 * (x1 - x0)
    py = y0 + KIM_Y[idx] * (y1 - y0)
    rs = np.random.default_rng(9)
    tx = rs.uniform(40, W - 40, len(idx))
    ty = rs.uniform(150, 1100, len(idx))
    for i in range(0, len(idx), 2):
        xx, yy = lerp(px[i], tx[i], u), lerp(py[i], ty[i], u)
        add_glow(cv, xx, yy, (255, 236, 220), 1.4 + 0.4 * u, 0.9)
    a = fade(t, t0, 0.5) * (1 - fade(t, t0 + 2.6, 0.6))
    text(dr, (W // 2, 1300), "记住这句话", font("serif", 48), withalpha(CREAM, a))


# ───────────────────────── 佛法：禅堂、灯、经文卡 ─────────────────────────
def lamp(cv, dr, x, y, t, a=1.0, s=1.0):
    fl = 1 + 0.08 * math.sin(t * 9.1) + 0.05 * math.sin(t * 13.7 + 1)
    add_glow(cv, x, y - 30 * s, (255, 190, 110), 140 * s * fl, 0.22 * a)
    add_glow(cv, x, y - 26 * s, (255, 210, 140), 30 * s * fl, 0.9 * a)
    dr.ellipse((x - 9 * s, y - 52 * s * fl, x + 9 * s, y - 14 * s), fill=(255, 235, 190, int(240 * a)))
    dr.polygon([(x - 46 * s, y - 10 * s), (x + 46 * s, y - 10 * s), (x + 30 * s, y + 14 * s), (x - 30 * s, y + 14 * s)], fill=(70, 55, 40, int(255 * a)))
    dr.rectangle((x - 6 * s, y + 14 * s, x + 6 * s, y + 90 * s), fill=(60, 48, 36, int(255 * a)))
    dr.ellipse((x - 40 * s, y + 84 * s, x + 40 * s, y + 100 * s), fill=(60, 48, 36, int(255 * a)))


def hall_bg(cv, dr, t, a=1.0):
    # 月洞窗 + 窗棂 + 晨雾
    cx, cy, r = 540, 760, 330
    add_glow(cv, cx, cy, (150, 160, 190), 260, 0.18 * a)
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(120, 100, 80, int(200 * a)), width=10)
    for k in range(-2, 3):
        dr.line([(cx + k * 110, cy - r + 30), (cx + k * 110, cy + r - 30)], fill=(90, 75, 60, int(120 * a)), width=4)
        dr.line([(cx - r + 30, cy + k * 110), (cx + r - 30, cy + k * 110)], fill=(90, 75, 60, int(120 * a)), width=4)
    # 地面
    dr.rectangle((0, 1180, W, 1260), fill=(30, 24, 19, int(255 * a)))
    lamp(cv, dr, 540, 1150, t, a)


def quote_card(cv, dr, t, ts, body, src, plain=None, plain_t=None, read=None, y0=360, size=54):
    a = fade(t, ts, 0.6)
    if a <= 0:
        return
    f = font("tc", size)
    ls = wrap(body, f, 820)
    lh = int(size * 1.7)
    h_body = len(ls) * lh
    h = 140 + h_body + (170 if plain else 40)
    box = (70, y0, 1010, y0 + h)
    dr.rounded_rectangle(box, 18, fill=(236, 226, 204, int(238 * a)), outline=(160, 130, 90, int(200 * a)), width=2)
    ink = (42, 34, 28, 255)
    rv = 1.0 if read is None else read
    para(dr, W // 2, y0 + 80, body, f, withalpha(ink, a), 820, lh=lh, reveal=min(0.999, clamp(rv * 1.08)) if (read is not None and rv < 0.93) else 1.0)
    # 出处（朱红）
    fs = font("tc", 30)
    sy = y0 + 80 + h_body + 10
    text(dr, (960, sy), src, fs, withalpha(SEAL, a), anchor="rm")
    if plain:
        pa = a * (fade(t, plain_t, 0.6) if plain_t else 1)
        dr.line([(130, sy + 40), (950, sy + 40)], fill=(160, 130, 90, int(120 * pa)), width=2)
        para(dr, W // 2, sy + 90, plain, font("serif", 36), withalpha((70, 60, 50, 255), pa), 820, lh=54)
    return box


def scene_hall(cv, dr, t):
    t0 = CUE_T["hall"]
    hall_bg(cv, dr, t, 1.0)
    # 标题
    if t < CUE_T["q_hy"]:
        head(dr, "忏悔，是删除记录吗？", t, t0, y=250, size=64, col=CREAM)
        if t > LINE_BY_CUE["hall"][-1]["start"]:
            u = fade(t, LINE_BY_CUE["hall"][-1]["start"], 0.6)
            text(dr, (W // 2, 340), "佛教讲因果：造下的业，不会凭空消失", font("sans", 36), withalpha(GOLD, u))
    # 华严 忏悔偈
    def lp(cue, i=0):
        return line_prog(cue, t, i)
    if CUE_T["q_hy"] <= t < CUE_T["q_hy2"]:
        ql = LINE_BY_CUE["q_hy"]
        quote_card(cv, dr, t, ql[0]["start"], "我昔所造諸惡業，皆由無始貪恚癡，\n從身語意之所生，一切我今皆懺悔。",
                   "《華嚴經·普賢行願品》（唐·般若譯，卷四十）",
                   plain="我过去造的种种恶业，都从贪嗔痴来，从身口意生起；这一切，我今天都忏悔。", plain_t=ql[2]["start"],
                   read=lp("q_hy", 1), y0=330)
        if since("q_hy_note", t) > 0:
            u = fade(t, CUE_T["q_hy_note"], 0.5)
            text(dr, (W // 2, 1080), "是我做的，我认。", font("serif_b", 64), withalpha(GOLD, u), stroke=3, sfill=(0, 0, 0, 180))
    elif CUE_T["q_hy2"] <= t < CUE_T["q_tj0"]:
        ql = LINE_BY_CUE["q_hy2"]
        quote_card(cv, dr, t, ql[0]["start"], "誠心懺悔，後不復造。", "《華嚴經·普賢行願品》（唐·般若譯，卷四十）", read=lp("q_hy2", 1), y0=420, size=64)
        if t > ql[2]["start"]:
            u = fade(t, ql[2]["start"], 0.5)
            text(dr, (W // 2, 820), "一半对着过去，一半对着以后", font("serif_b", 52), withalpha(GOLD, u), stroke=3, sfill=(0, 0, 0, 180))
    elif CUE_T["q_tj0"] <= t < CUE_T["q_tj1"]:
        ql = LINE_BY_CUE["q_tj0"]
        quote_card(cv, dr, t, ql[0]["start"], "此事須從自事中起，於一切時，念念自淨其心。", "《六祖壇經·懺悔品》（宗寶本，CBETA T2008）",
                   plain="这件事，要从自己身上的事做起，时时刻刻，清理自己的心。", plain_t=ql[2]["start"], read=lp("q_tj0", 1), y0=360, size=54)
    elif CUE_T["q_tj1"] <= t < CUE_T["q_tj2"]:
        ql = LINE_BY_CUE["q_tj1"]
        quote_card(cv, dr, t, ql[0]["start"], "懺者，懺其前愆，從前所有惡業，愚迷憍誑嫉妬等罪，悉皆盡懺，永不復起，是名為懺。",
                   "《六祖壇經·懺悔品》", plain="忏：对过去——把以前的过错看清、认尽，让它不再生起。", plain_t=ql[2]["start"], read=lp("q_tj1", 1), y0=300)
    elif CUE_T["q_tj2"] <= t < CUE_T["q_tj3"]:
        ql = LINE_BY_CUE["q_tj2"]
        quote_card(cv, dr, t, ql[0]["start"], "悔者，悔其後過，從今以後，所有惡業……今已覺悟，悉皆永斷，更不復作，是名為悔。",
                   "《六祖壇經·懺悔品》", plain="悔：对以后——觉悟了，从此不再做。", plain_t=ql[1]["start"], read=lp("q_tj2", 0), y0=300)
    elif CUE_T["q_tj3"] <= t < CUE_T["q_tj3_note"]:
        ql = LINE_BY_CUE["q_tj3"]
        quote_card(cv, dr, t, ql[0]["start"], "凡夫愚迷，只知懺其前愆，不知悔其後過。以不悔故，前愆不滅，後過又生。",
                   "《六祖壇經·懺悔品》", plain="只对过去懊恼、不改变以后：旧的没有了结，新的又来了。", plain_t=ql[2]["start"], read=lp("q_tj3", 1), y0=300)
    elif CUE_T["q_tj3_note"] <= t < CUE_T["penit_end"]:
        u = fade(t, CUE_T["q_tj3_note"], 0.6)
        dr.rectangle((0, 330, W, 760), fill=(14, 11, 9, int(215 * u)))
        text(dr, (W // 2, 420), "真正悔了，前愆可以灭", font("serif_b", 56), withalpha(CREAM, u))
        v = fade(t, LINE_BY_CUE["q_tj3_note"][1]["start"], 0.6)
        text(dr, (W // 2, 550), "灭的不是“那件事发生过”", font("serif", 46), withalpha(GREY, v))
        text(dr, (W // 2, 640), "而是推着人再犯的那股习气", font("serif_b", 50), withalpha(GOLD, v))
    elif t >= CUE_T["penit_end"]:
        u = fade(t, CUE_T["penit_end"], 0.6)
        text(dr, (W // 2, 420), "忏悔的重心", font("serif", 48), withalpha(CREAM, u))
        text(dr, (W // 2, 520), "不在涂改过去，而在往后的因果", font("serif_b", 58), withalpha(GOLD, u), stroke=3, sfill=(0, 0, 0, 180))


def scene_moon(cv, dr, t):
    t0 = CUE_T["q_fj"]
    t1 = cue_span("moon_cloud")[1]
    cu = ease((t - t0) / (t1 - t0 + 1.5))
    moon_sky(cv, dr, (0, 120, W, 1400), t, cu, moon_r=110, mx=540, my=1000)
    if t < CUE_T["q_pali"]:
        ql = LINE_BY_CUE["q_fj"]
        quote_card(cv, dr, t, ql[0]["start"], "人前為惡，後止不犯，\n是炤世間，如月雲消。", "漢譯《法句經·放逸品》（吳·維祇難等譯，CBETA T210）",
                   plain="以前做过恶，后来止住不再犯，就照亮世间，像月亮从云里出来。", plain_t=ql[2]["start"], read=line_prog("q_fj", t, 1), y0=260, size=58)
    elif t < CUE_T["moon_cloud"]:
        a = fade(t, CUE_T["q_pali"], 0.6)
        card(dr, (90, 280, 990, 640), fill=(236, 226, 204, int(232 * a)), outline=(160, 130, 90, int(200 * a)))
        text(dr, (W // 2, 360), "若作惡業已，覆之以善者，", font("tc", 50), withalpha((42, 34, 28, 255), a))
        text(dr, (W // 2, 450), "彼照耀此世，如月出雲翳。", font("tc", 50), withalpha((42, 34, 28, 255), a))
        text(dr, (950, 570), "南傳巴利《法句經》第一七三偈 · 葉均譯", font("tc", 30), withalpha(SEAL, a), anchor="rm")
    else:
        a = fade(t, CUE_T["moon_cloud"], 0.6)
        lc = LINE_BY_CUE["moon_cloud"]
        text(dr, (W // 2, 330), "“放逸”：心散了，放纵了", font("serif", 44), withalpha(CREAM, a * (1 - fade(t, lc[1]["start"], 0.5))))
        if t > lc[1]["start"]:
            u = fade(t, lc[1]["start"], 0.6)
            text(dr, (W // 2, 330), "月亮出来，并没有否认云来过", font("serif_b", 54), withalpha(CREAM, u), stroke=3, sfill=(0, 0, 0, 160))
        if len(lc) > 2 and t > lc[2]["start"]:
            u = fade(t, lc[2]["start"], 0.6)
            text(dr, (W // 2, 430), "云来过，是记录；月出来，是后来的因缘", font("serif", 44), withalpha(GOLD, u))


def scene_close(cv, dr, t):
    t0 = CUE_T["compare"]
    a = fade(t, t0, 0.5)
    text(dr, (W // 2, 250), "把两件事放在一起", font("serif_b", 60), withalpha(CREAM, a))
    # 上：物理
    draw_panel(cv, dr, (160, 420, 920, 600), KIM_G > 0, a=a, curve=False, label=None)
    ul = fade(t, CUE_T["compare_l"], 0.5)
    text(dr, (W // 2, 660), "量子擦除：擦的是路径信息能否取得", font("sans", 36), withalpha(ICE, ul))
    text(dr, (W // 2, 710), "屏上已经留下的点，一个没动", font("sans", 36), withalpha(ICE, ul))
    # 下：月
    ur = fade(t, CUE_T["compare_r"], 0.5)
    if ur > 0:
        moon_sky(cv, dr, (160, 800, 920, 1150), t, 0.85, moon_r=60, a=ur)
        text(dr, (W // 2, 1200), "忏悔：改的是与过去的关系", font("sans", 36), withalpha(GOLD, ur))
        text(dr, (W // 2, 1250), "以及接下来要种下的因", font("sans", 36), withalpha(GOLD, ur))
    lc = LINE_BY_CUE["compare"]
    if len(lc) > 1 and t > lc[1]["start"]:
        u = fade(t, lc[1]["start"], 0.5)
        dr.rectangle((0, 1290, W, 1420), fill=(6, 6, 8, int(220 * u)))
        text(dr, (W // 2, 1330), "物理：可重复，可检验", font("serif", 40), withalpha(CREAM, u))
        text(dr, (W // 2, 1385), "修行：此生、此心", font("serif", 40), withalpha(CREAM, u))
    if len(lc) > 2 and t > lc[2]["start"]:
        u = fade(t, lc[2]["start"], 0.5)
        dr.rectangle((0, 1290, W, 1420), fill=(6, 6, 8, int(245 * u)))
        text(dr, (W // 2, 1355), "检验忏悔：下一次，还会不会再犯", font("serif_b", 44), withalpha(GOLD, u))


def scene_close2(cv, dr, t):
    t0 = CUE_T["analogy"]
    a = fade(t, t0, 0.5)
    card(dr, (90, 520, 990, 1250), fill=(14, 12, 10, int(235 * a)), outline=(217, 178, 95, int(140 * a)))
    text(dr, (W // 2, 640), "两者不是同一件事", font("serif_b", 58), withalpha(CREAM, a))
    text(dr, (W // 2, 740), "这是类比 · 物理学没有证明佛法", font("serif", 46), withalpha(CREAM, a))
    b = fade(t, LINE_BY_CUE["analogy"][1]["start"], 0.6)
    dr.line([(200, 820), (880, 820)], fill=withalpha(GOLD, 0.5 * b), width=2)
    text(dr, (W // 2, 910), "过去的记录不变，理解和以后可以改变", font("serif", 42), withalpha(CREAM, b))
    text(dr, (W // 2, 1040), "或许佛学的讲法也有它的道理", font("serif_b", 50), withalpha(GOLD, b))
    text(dr, (W // 2, 1130), "算是一种印照", font("serif_b", 58), withalpha(GOLD, b))


def scene_small(cv, dr, t):
    t0 = CUE_T["small"]
    hall_bg(cv, dr, t, 0.55)
    a = fade(t, t0, 0.5)
    text(dr, (W // 2, 250), "不必想得太高", font("serif_b", 60), withalpha(CREAM, a))
    lc = LINE_BY_CUE["small"]
    text(dr, (W // 2, 360), "一句迟到的道歉 · 一个准备改掉的习惯", font("serif", 42), withalpha(GOLD, fade(t, t0 + 2.0, 0.6)))
    if len(lc) > 1 and t > lc[1]["start"]:
        u = fade(t, lc[1]["start"], 0.6)
        dr.rectangle((0, 1290, W, 1440), fill=(10, 8, 7, int(220 * u)))
        text(dr, (W // 2, 1340), "话已出口，收不回来", font("serif", 44), withalpha(CREAM, u))
        v = fade(t, lc[1]["start"] + 3.0, 0.6)
        text(dr, (W // 2, 1400), "可以道歉，可以从此换一种说法", font("serif", 44), withalpha(CREAM, v))
    if len(lc) > 2 and t > lc[2]["start"]:
        u = fade(t, lc[2]["start"], 0.6)
        text(dr, (W // 2, 470), "那句话还在；它的意思，已经不一样了", font("serif_b", 46), withalpha(CREAM, u), stroke=3, sfill=(0, 0, 0, 180))


def scene_final(cv, dr, t):
    t0 = CUE_T["final1"]
    moon_sky(cv, dr, (0, 120, W, 1400), t, 0.75, moon_r=80, mx=540, my=1050, a=0.8)
    draw_panel(cv, dr, (160, 480, 920, 660), KIM_G > 0, a=fade(t, t0, 0.6), curve=False)
    a = fade(t, t0, 0.5)
    text(dr, (W // 2, 330), "过去的记录，一个点都不会变", font("serif_b", 58), withalpha(CREAM, a), stroke=3, sfill=(0, 0, 0, 160))
    b = fade(t, CUE_T["final2"], 0.6)
    text(dr, (W // 2, 760), "能变的，是怎样理解它", font("serif_b", 54), withalpha(GOLD, b), stroke=3, sfill=(0, 0, 0, 160))
    text(dr, (W // 2, 850), "以及从今以后，种下什么因", font("serif_b", 54), withalpha(GOLD, fade(t, CUE_T["final2"] + 2.5, 0.6)), stroke=3, sfill=(0, 0, 0, 160))


_paper = None


def scene_brush(cv, dr, t):
    global _paper
    t0 = CUE_T["brush"]
    s0, s1 = cue_span("brush")
    if _paper is None:
        rs = np.random.default_rng(4)
        tex = gaussian_filter(rs.normal(0, 1, (H, W)), 2) * 3 + gaussian_filter(rs.normal(0, 1, (H, W)), 30) * 25
        _paper = (np.array([232, 222, 200], np.float32) + tex[..., None]).astype(np.float32)
    a = fade(t, t0 - 0.2, 0.8)
    cv[:] = cv * (1 - a) + _paper * a
    # 书法「從今以後」竖写，逐字自上而下擦出（念到这四个字时开始）
    f = font("kai", 250)
    wstart = s0 + 0.62 * (s1 - s0)
    for i, ch in enumerate("從今以後"):
        u = clamp((t - (wstart + i * 0.7)) / 0.65)
        if u <= 0:
            continue
        cy = 400 + i * 270
        layer = Image.new("L", (300, 300), 0)
        ImageDraw.Draw(layer).text((150, 150), ch, font=f, fill=255, anchor="mm")
        yy = np.arange(300)[:, None]
        mask = np.clip((300 * u * 1.15 - yy) / 40, 0, 1)
        arr = np.asarray(layer, np.float32) / 255 * mask * a
        ys, xs = cy - 150, 540 - 150 - 60
        reg = cv[ys:ys + 300, xs:xs + 300]
        reg[:] = reg * (1 - arr[..., None]) + np.array([30, 26, 22], np.float32) * arr[..., None]
    night_t = s1 + 3.4
    v = fade(t, night_t, 1.6)
    u = fade(t, wstart + 3.2, 0.8) * (1 - v)
    if u > 0:
        dr.rectangle((760, 470, 840, 1030), outline=withalpha(SEAL, u), width=4)
        for i, ch in enumerate("六祖壇經·懺悔品"):
            text(dr, (800, 510 + i * 64), ch, font("tc_b", 44), withalpha(SEAL, u))
    if v > 0:
        night = bg("night")
        cv[:] = cv * (1 - v) + night * v
        moon_sky(cv, dr, (0, 200, W, 1500), t, ease((t - night_t - 0.6) / 4.0), moon_r=120, mx=540, my=760, a=ease((v - 0.4) / 0.6))
        text(dr, (W // 2, 1250), "從今以後", font("kai", 110), withalpha(CREAM, fade(t, night_t + 1.2, 1.0)))
        text(dr, (W // 2, 1350), "《六祖壇經·懺悔品》", font("tc", 34), withalpha(GOLD, fade(t, night_t + 1.8, 1.0)))


SCENE_FN = {"lab": scene_lab, "tease": scene_tease, "halves": scene_halves, "disc": scene_disc, "slit": scene_slit,
            "hist": scene_hist, "kim": scene_kim, "facts": scene_facts, "analogy": scene_analogy, "time": scene_time,
            "f4": scene_f4, "sum": scene_sum, "stars": scene_stars, "hall": scene_hall, "moon": scene_moon,
            "close": scene_close, "close2": scene_close2, "small": scene_small, "final": scene_final, "brush": scene_brush}
BGK = {"hall": "budd", "small": "budd", "moon": "night", "close": "night", "close2": "budd", "final": "night", "brush": "night", "stars": "phys"}


# ───────────────────────── 字幕 ─────────────────────────
SUBS = []
for e in LINES:
    if e.get("nosub"):
        continue
    for s in e["subs"]:
        SUBS.append(s)


def draw_sub(dr, t):
    for s in SUBS:
        if s["start"] - 0.02 <= t < s["end"] + 0.12:
            f = font("sans", 50)
            tx = s["text"]
            w = f.getlength(tx)
            y = 1530
            dr.rounded_rectangle((W / 2 - w / 2 - 28, y - 44, W / 2 + w / 2 + 28, y + 44), 14, fill=(0, 0, 0, 120))
            text(dr, (W // 2, y), tx, f, (255, 255, 255, 255), stroke=3, sfill=(0, 0, 0, 230))
            return


def frame_scene(g, t):
    cv = bg(BGK.get(g, "phys")).copy()
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    SCENE_FN[g](cv, dr, t)
    base = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8), "RGB")
    base.paste(ov, (0, 0), ov)
    return np.asarray(base, np.float32)


XF = 0.5


def frame(t):
    i = 0
    for k, s in enumerate(SHOTS):
        if s["start"] <= t < s["end"] or k == len(SHOTS) - 1:
            i = k
            break
    s = SHOTS[i]
    img = frame_scene(s["g"], t)
    if i > 0 and t - s["start"] < XF:
        u = ease((t - s["start"]) / XF)
        prev = frame_scene(SHOTS[i - 1]["g"], t)
        img = prev * (1 - u) + img * u
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    # 角标
    f = font("sans_r", 24)
    dr.rounded_rectangle((W - 150, 50, W - 40, 92), 10, fill=(0, 0, 0, 90))
    text(dr, (W - 95, 71), "AI 配音", f, (230, 230, 230, 200))
    sc = None
    for x in TL["scenes"]:
        if x["start"] - 0.3 <= t:
            sc = x["id"]
    tag = PART.get(sc, "")
    if tag:
        text(dr, (60, 71), tag, f, (200, 200, 200, 150), anchor="lm")
    draw_sub(dr, t)
    out.alpha_composite(ov)
    return out.convert("RGB")


def render_part(k, n):
    nf = int(round(TOTAL * FPS))
    a, b = nf * k // n, nf * (k + 1) // n
    os.makedirs(f"{WORK}/video", exist_ok=True)
    out = f"{WORK}/video/part_{k:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                         stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for fi in range(a, b):
        im = frame(fi / FPS)
        p.stdin.write(im.tobytes())
        if (fi - a) % 250 == 0:
            print(f"part {k}: {fi - a}/{b - a} frames, {time.time() - t0:.0f}s", flush=True)
    p.stdin.close()
    p.wait()
    print(f"part {k} done {b - a} frames in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "still":
        t = float(sys.argv[2])
        frame(t).save(sys.argv[3] if len(sys.argv) > 3 else f"{WORK}/still_{t:.1f}.png")
    else:
        render_part(int(sys.argv[1]), int(sys.argv[2]))
