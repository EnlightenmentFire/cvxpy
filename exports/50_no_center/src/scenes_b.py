"""场景（下）：解释器、心智社会、涌现之争、打开黑箱、收束。"""
from scenes_a import *

# ---------- icons (line art) ----------
def icon_claw(img, cx, cy, s, col, a=1.0):
    c = scale(col, a)
    line(img, (cx, cy + s * 0.5), (cx, cy - s * 0.05), c, 6)
    for dx in (-0.45, 0, 0.45):
        line(img, (cx, cy - s * 0.05), (cx + dx * s, cy - s * 0.55), c, 6)
    line(img, (cx, cy - s * 0.05), (cx - s * 0.1, cy + s * 0.15), c, 5)
def icon_snow(img, cx, cy, s, col, a=1.0, t=0):
    c = scale(col, a)
    pts = np.array([(cx - s * 0.6, cy + s * 0.5), (cx - s * 0.15, cy - s * 0.05), (cx + s * 0.15, cy + s * 0.2), (cx + s * 0.6, cy - s * 0.2), (cx + s * 0.6, cy + s * 0.5)], np.int32)
    cv2.polylines(img, [pts], True, c, 4, cv2.LINE_AA)
    cv2.rectangle(img, (int(cx - s * 0.05), int(cy + s * 0.18)), (int(cx + s * 0.28), int(cy + s * 0.5)), c, 3, cv2.LINE_AA)
    cv2.line(img, (int(cx - s * 0.1), int(cy + s * 0.2)), (int(cx + s * 0.12), int(cy + s * 0.0)), c, 3, cv2.LINE_AA)
    cv2.line(img, (int(cx + s * 0.12), int(cy)), (int(cx + s * 0.33), int(cy + s * 0.2)), c, 3, cv2.LINE_AA)
    rng = np.random.default_rng(1)
    for i in range(14):
        x = cx + rng.uniform(-0.6, 0.6) * s
        y = cy - s * 0.6 + ((rng.uniform(0, 1) + t * 0.15) % 1) * s * 0.75
        circle(img, (x, y), 4, c)
def icon_chicken(img, cx, cy, s, col, a=1.0):
    c = scale(col, a)
    cv2.ellipse(img, (int(cx), int(cy + s * 0.1)), (int(s * 0.42), int(s * 0.3)), 0, 0, 360, c, 4, cv2.LINE_AA)
    circle(img, (cx + s * 0.35, cy - s * 0.25), s * 0.16, c, 4)
    pts = np.array([(cx + s * 0.5, cy - s * 0.28), (cx + s * 0.66, cy - s * 0.22), (cx + s * 0.5, cy - s * 0.17)], np.int32)
    cv2.polylines(img, [pts], True, c, 3, cv2.LINE_AA)
    line(img, (cx - s * 0.1, cy + s * 0.38), (cx - s * 0.1, cy + s * 0.58), c, 4)
    line(img, (cx + s * 0.1, cy + s * 0.38), (cx + s * 0.1, cy + s * 0.58), c, 4)
def icon_shovel(img, cx, cy, s, col, a=1.0):
    c = scale(col, a)
    line(img, (cx, cy - s * 0.55), (cx, cy + s * 0.15), c, 6)
    line(img, (cx - s * 0.15, cy - s * 0.55), (cx + s * 0.15, cy - s * 0.55), c, 6)
    pts = np.array([(cx - s * 0.22, cy + s * 0.15), (cx + s * 0.22, cy + s * 0.15), (cx + s * 0.18, cy + s * 0.5), (cx, cy + s * 0.6), (cx - s * 0.18, cy + s * 0.5)], np.int32)
    cv2.polylines(img, [pts], True, c, 4, cv2.LINE_AA)

def split_intro(fr, t, c):
    fr.img[:] = nebula(14, (15, 20, 45), (40, 15, 40), 0.8)
    cut = c.at(t, "d03", 0.8, 2.6)
    brain_top(fr, W / 2, 860, 380, CYAN, 1.0, gap=8 + 34 * cut, lcol=CYAN, rcol=VIOLET)
    # corpus callosum fibres
    for j in range(9):
        y = 760 + j * 22
        k = 1 - cut
        gline(fr, (W / 2 - 60, y), (W / 2 + 60, y), AMBER, 0.6 * k + 0.05, 2)
    if cut > 0:
        for y in range(470, 1250, 26):
            gdot(fr, (W / 2 + 6 * math.sin(y * 0.1 + t * 5), y), 5, RED, 0.5 * cut)
    fr.finish_glow()
    text(fr.img, "割裂脑", W / 2, 320, 76, "serifh", WHITE, "mm", c.at(t, "d02", 0.6), 3)
    text(fr.img, "胼胝体", W / 2, 1300, 44, "sansb", AMBER, "mm", c.at(t, "d03", 0.6, 1.0) * (1 - cut), 2)
    text(fr.img, "胼胝体切断术（治疗严重癫痫）", W / 2, 1300, 40, "sansb", RED, "mm", cut, 2)
    text(fr.img, "左脑", W / 2 - 230, 860, 40, "sansb", CYAN, "mm", 0.9)
    text(fr.img, "右脑", W / 2 + 230, 860, 40, "sansb", VIOLET, "mm", 0.9)
    text(fr.img, "俯视示意", W - 60, 1220, 26, "sans", GREY, "rm", 0.8)

def split_rule(fr, t, c):
    fr.img[:] = nebula(14, (15, 20, 45), (40, 15, 40), 0.7)
    img = fr.img
    brain_top(fr, W / 2, 820, 330, CYAN, 0.9, gap=50, lcol=CYAN, rcol=VIOLET)
    k = c.at(t, "d05", 0.6)
    k2 = c.at(t, "d05", 0.6, 2.4)
    fr.finish_glow()
    text(img, "左脑", W / 2 - 200, 820, 40, "sansb", CYAN, "mm")
    text(img, "右脑", W / 2 + 200, 820, 40, "sansb", VIOLET, "mm")
    a = c.at(t, "d04", 0.6, 1.5)
    text(img, "实验里：只让一侧大脑看到图片", W / 2, 340, 42, "serifb", WHITE, "mm", a, 2)
    tag(img, "语言：多数人主要在左脑", W / 2 - 170, 1230, CYAN, k, 34)
    if k2 > 0:
        arrow(img, (W / 2 + 200, 1000), (W / 2 - 300, 1360), VIOLET, 5, k2, 0.06)
        tag(img, "左手 ← 右脑控制", W / 2 + 120, 1400, VIOLET, k2, 34)

def split_exp(fr, t, c):
    fr.img[:] = nebula(15, (12, 18, 40), (30, 15, 40), 0.6)
    img = fr.img
    # screen with fixation, two halves
    a = c.at(t, "d06", 0.6)
    card_box(img, 100, 300, W - 100, 760, a, GREY, fill=(10, 12, 20), fa=0.95)
    text(img, "+", W / 2, 530, 60, "sans5", WHITE, "mm", a)
    show = c.at(t, "d07", 0.6, 0.6)
    icon_snow(img, 300, 530, 240, VIOLET, show, t)
    icon_claw(img, W - 300, 530, 220, AMBER, show)
    text(img, "→ 右脑看到：雪景", 300, 710, 30, "sansb", VIOLET, "mm", show)
    text(img, "→ 左脑看到：鸡爪", W - 300, 710, 30, "sansb", AMBER, "mm", show)
    # choice cards
    ch = c.at(t, "d07", 0.6, 3.0)
    opts = [("鸡", icon_chicken), ("铲子", icon_shovel), ("苹果", None), ("锤子", None)]
    xs = [180, 420, 660, 900]
    pick_r = c.at(t, "d08", 0.6, 0.3)
    pick_l = c.at(t, "d08", 0.6, 2.8)
    for (nm, fn), x in zip(opts, xs):
        y = 980
        hl = (nm == "鸡" and pick_r > 0) or (nm == "铲子" and pick_l > 0)
        col = (AMBER if nm == "鸡" else VIOLET) if hl else GREY
        card_box(img, x - 100, y - 120, x + 100, y + 120, ch, col, fa=0.9)
        if fn:
            fn(img, x, y - 20, 150, col, ch)
        else:
            text(img, nm, x, y - 20, 52, "sansb", col, "mm", ch * 0.7)
        text(img, nm, x, y + 90, 30, "sans5", col, "mm", ch)
        if hl:
            gring(fr, (x, y), 150, col, 0.5, 3)
    fr.finish_glow()
    tag(img, "右手 → 鸡（左脑回应鸡爪）", W / 2, 1200, AMBER, pick_r, 34)
    tag(img, "左手 → 铲子（右脑回应雪景）", W / 2, 1280, VIOLET, pick_l, 34)
    text(img, "Gazzaniga & LeDoux 实验示意（非真实病人画面）", W / 2, 1360, 26, "sans", GREY, "mm", ch)

def split_ask(fr, t, c):
    fr.img[:] = nebula(15, (12, 18, 40), (30, 15, 40), 0.6)
    img = fr.img
    brain_top(fr, W / 2, 1060, 230, CYAN, 0.8, gap=40, lcol=CYAN, rcol=VIOLET, rk=0.35)
    fr.finish_glow()
    text(img, "“你为什么选铲子？”", W / 2, 330, 52, "serifb", WHITE, "mm", c.at(t, "d09", 0.6), 2)
    k = c.at(t, "d10", 0.6)
    tag(img, "会说话的左脑：没看到雪景", W / 2, 440, RED, k, 36)
    q = c.at(t, "d11", 0.7)
    if q > 0:
        quote_card(img, 520, "“这很简单。鸡爪配鸡，而清理鸡舍，需要一把铲子。”",
                   "病人 P.S. 的回答，据 Gazzaniga & LeDoux（1978）；英文原话见 Volz & Gazzaniga, Brain 2017",
                   "“Oh, that's simple. The chicken claw goes with the chicken, and you need a shovel to clean out the chicken shed.”",
                   q, AMBER, 46)
    text(img, "左", W / 2 - 130, 1060, 34, "sansb", CYAN, "mm")
    text(img, "右", W / 2 + 130, 1060, 34, "sansb", VIOLET, "mm", 0.5)

def interpreter(fr, t, c):
    fr.img[:] = nebula(16, (20, 20, 45), (35, 15, 40), 0.8)
    img = fr.img
    cx, cy = W / 2 - 120, 860
    brain_top(fr, W / 2, cy, 360, CYAN, 0.8, gap=40, lcol=AMBER, rcol=VIOLET, rk=0.4)
    k = c.at(t, "d13", 0.8)
    st = c.at(t, "d14", 3.0)
    frags = ["左手动了", "铲子", "鸡爪", "一阵情绪", "一个念头", "雪？"]
    rng = np.random.default_rng(5)
    pos = []
    for i, f in enumerate(frags):
        ang = i / len(frags) * 6.28 + t * 0.2
        x0, y0 = W / 2 + math.cos(ang) * 400, cy + 40 + math.sin(ang) * 430
        x, y = lerp(x0, cx, st * 0.0), lerp(y0, 1380 - 0, 0)
        pos.append((x0, y0))
        gdot(fr, (x0, y0), 30, VIOLET, 0.3)
    if st > 0:
        n = int(len(pos) * st) + 1
        for i in range(min(n, len(pos) - 1)):
            gline(fr, pos[i], pos[i + 1], AMBER, 0.7, 3)
    gdot(fr, (cx, cy), 90, AMBER, 0.6 * k * (0.8 + 0.2 * math.sin(t * 4)))
    fr.finish_glow()
    for (x, y), f in zip(pos, frags):
        text(img, f, x, y, 32, "sans5", WHITE, "mm", 0.85)
    text(img, "解释器", W / 2, 320, 80, "serifh", AMBER, "mm", k, 3)
    text(img, "the interpreter · Gazzaniga", W / 2, 400, 32, "serif", GREY, "mm", k)
    if st > 0:
        tag(img, "事后串成一个说得通的故事", W / 2, 1460, AMBER, st, 38)
    q = c.at(t, "d15b", 0.6)
    if q > 0:
        rect_alpha(img, 0, 0, W, H, BG, 0.55 * q)
        text(img, "先做了，", W / 2, 820, 64, "serifb", WHITE, "mm", q, 2)
        text(img, "再找理由——而且深信不疑。", W / 2, 920, 56, "serifb", AMBER, "mm", c.at(t, "d15b", 0.6, 1.5), 2)

def face(img, cx, cy, s, col, a, seed):
    rng = np.random.default_rng(seed)
    cv2.ellipse(img, (int(cx), int(cy)), (int(s * 0.36), int(s * 0.48)), 0, 0, 360, scale(col, a), 4, cv2.LINE_AA)
    hair = rng.uniform(0.2, 0.5)
    cv2.ellipse(img, (int(cx), int(cy - s * 0.15)), (int(s * 0.4), int(s * (0.38 + hair * 0.2))), 0, 190, 350, scale(col, a), 6, cv2.LINE_AA)
    for dx in (-0.13, 0.13):
        circle(img, (cx + dx * s, cy - s * 0.05), s * 0.035, scale(col, a))
    cv2.ellipse(img, (int(cx), int(cy + s * 0.2)), (int(s * 0.1), int(s * 0.04 + rng.uniform(0, 8))), 0, 0, 180, scale(col, a), 3, cv2.LINE_AA)

def choice(fr, t, c):
    fr.img[:] = nebula(17, (20, 20, 45), (35, 15, 40), 0.7)
    img = fr.img
    a = c.at(t, "d16", 0.6)
    sw = c.at(t, "d17", 0.9, 0.3)
    pick = c.at(t, "d16", 0.5, 3.2)
    # two cards; chosen = left; after swap the left card slides to the right and vice versa
    xl, xr = 300, 780
    xa = lerp(xl, xr, sw); xb = lerp(xr, xl, sw)
    for x, seed, col, nm in ((xa, 1, AMBER if pick else GREY, "A"), (xb, 2, GREY, "B")):
        card_box(img, x - 180, 560, x + 180, 1040, a, col, fa=0.92)
        face(img, x, 790, 300, col, a, seed)
    if sw > 0.9:
        text(img, "递回来的，是没被选中的那张", W / 2, 1120, 36, "sansb", RED, "mm", c.at(t, "d17", 0.5, 1.6))
        text(img, "“我选它，是因为她的笑容……”", W / 2, 1210, 40, "serifb", AMBER, "mm", c.at(t, "d17", 0.5, 3.2), 2)
    text(img, "选择盲视实验", W / 2, 330, 62, "serifh", WHITE, "mm", a, 3)
    text(img, "Johansson, Hall 等, Science, 2005 · 实证", W / 2, 405, 30, "sans5", GREY, "mm", a)
    text(img, "示意", W - 60, 1060, 26, "sans", GREY, "rm", 0.8 * a)

def split_debate(fr, t, c):
    fr.img[:] = nebula(14, (15, 20, 45), (40, 15, 40), 0.6)
    img = fr.img
    brain_top(fr, W / 2, 900, 300, CYAN, 0.7, gap=40, lcol=CYAN, rcol=VIOLET)
    m = c.at(t, "d19", 1.2)
    gring(fr, (W / 2, 900), 380, WHITE, 0.3 * m, 3)
    fr.finish_glow()
    tag(img, "争议 · 小样本（n = 2）", W / 2, 320, RED, c.at(t, "d18", 0.5), 40)
    text(img, "Pinto 等, Brain, 2017", W / 2, 400, 32, "sans5", GREY, "mm", c.at(t, "d18", 0.5))
    text(img, "知觉被分开 ≠ 意识被一分为二", W / 2, 1340, 46, "serifb", WHITE, "mm", m, 2)
    tag(img, "“解释器”现象：被反复观察到", W / 2, 1400, AMBER, c.at(t, "d20", 0.6, 2.5), 36)

# ======================= 心智社会 =======================
class Agents:
    def __init__(self, n=140, seed=31):
        rng = np.random.default_rng(seed)
        self.p0 = rng.uniform((80, 430), (W - 80, 1080), (n, 2))
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
        # target: a big "brain-ish" ring structure of agents
        r = 300 + 40 * np.sin(ang * 5)
        self.p1 = np.stack([W / 2 + np.cos(ang) * r, 720 + np.sin(ang) * r * 1.1], 1)
        self.ph = rng.uniform(0, 6, n)
AG = Agents()

def agents_draw(fr, t, k, col=CYAN):
    P = AG.p0 * (1 - k) + AG.p1 * k
    for i, (p, ph) in enumerate(zip(P, AG.ph)):
        x, y = p[0] + 6 * math.sin(t * 1.3 + ph), p[1] + 6 * math.cos(t * 1.1 + ph)
        cv2.rectangle(fr.img, (int(x - 7), int(y - 7)), (int(x + 7), int(y + 7)), scale(col, 0.75), 2, cv2.LINE_AA)
        circle(fr.img, (x, y), 2, WHITE)
        if k > 0.5 and i % 2 == 0:
            q = P[(i + 1) % len(P)]
            gline(fr, (x, y), q, col, 0.35 * (k - 0.5) * 2)
        gdot(fr, (x, y), 12, col, 0.2)

def society(fr, t, c):
    fr.img[:] = nebula(18, (15, 25, 50), (30, 20, 45), 0.8)
    k = c.at(t, "e02", 3.0, 1.0)
    agents_draw(fr, t, k)
    fr.finish_glow()
    a = c.at(t, "e01", 0.6)
    text(fr.img, "聪明，从哪里来？", W / 2, 330, 58, "serifb", WHITE, "mm", a * (1 - c.at(t, "e02", 0.5)), 2)
    b = c.at(t, "e02", 0.7)
    book_card(fr.img, 1150, "《心智社会》", "Marvin Minsky, The Society of Mind", "Simon & Schuster · 1986", b * 0.97)

def minsky_q(fr, t, c):
    fr.img[:] = nebula(18, (15, 25, 50), (30, 20, 45), 0.6)
    agents_draw(fr, t, 1.0, scale(CYAN, 0.6))
    fr.finish_glow(0.6)
    rect_alpha(fr.img, 0, 0, W, H, BG, 0.45)
    a = c.at(t, "e03", 0.8)
    quote_card(fr.img, 430,
               "Each mental agent by itself can only do some simple thing that needs no mind or thought at all. Yet when we join these agents in societies — in certain very special ways — this leads to true intelligence.",
               "Marvin Minsky, The Society of Mind, Prologue（1986）",
               "每个心智智能体单独只能做一点简单的事，不需要心智或思考；但以特殊方式组成社会，就产生真正的智能。",
               a, CYAN, 40, "serif")

def society2(fr, t, c):
    fr.img[:] = nebula(19, (25, 20, 40), (20, 25, 50), 0.8)
    img = fr.img
    # ant colony: ants walking along tunnels forming a nest
    rng = np.random.default_rng(8)
    nest_k = c.at(t, "e05b", 4.0)
    for j in range(5):
        y = 900 + j * 90
        L = 120 + (j + 1) * 120 * min(1, nest_k * 1.3 + 0.15)
        line(img, (W / 2 - L, y), (W / 2 + L, y), scale(AMBER, 0.35), 18)
        if j < 4:
            line(img, (W / 2 + (-1) ** j * L * 0.6, y), (W / 2 + (-1) ** j * L * 0.4, y + 90), scale(AMBER, 0.35), 18)
    for i in range(70):
        j = i % 5
        y = 900 + j * 90
        L = 120 + (j + 1) * 120 * min(1, nest_k * 1.3 + 0.15)
        u = (rng.random() + t * rng.uniform(0.05, 0.15) * (1 if i % 2 else -1)) % 1
        x = W / 2 - L + 2 * L * u
        circle(img, (x, y), 6, (230, 200, 160))
        gdot(fr, (x, y), 10, AMBER, 0.25)
    fr.finish_glow()
    text(img, "智能在组织方式里", W / 2, 330, 62, "serifh", WHITE, "mm", c.at(t, "e05", 0.6) * (1 - c.at(t, "e06", 0.5)), 3)
    text(img, "没有哪只蚂蚁知道蚁巢的图纸", W / 2, 470, 38, "sans5", AMBER, "mm", c.at(t, "e05b", 0.6) * (1 - c.at(t, "e06", 0.5)))
    q = c.at(t, "e06", 0.7)
    if q > 0:
        rect_alpha(img, 0, 0, W, H, BG, 0.5 * q)
        quote_card(img, 380, "What magical trick makes us intelligent? The trick is that there is no trick.",
                   "Marvin Minsky, The Society of Mind, §30.8", "让我们聪明的魔法是什么？诀窍就是，没有诀窍。", q, AMBER, 46, "serif")

def skandha(fr, t, c):
    fr.img[:] = nebula(20, (25, 22, 35), (35, 28, 30), 0.7)
    img = fr.img
    k = c.at(t, "e08", 2.5, 1.0)
    names = ["色", "受", "想", "行", "识"]
    cx, cy = W / 2, 900
    for i, nm in enumerate(names):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        r0 = 380; r1 = 170
        r = lerp(r0, r1, k)
        x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        gdot(fr, (x, y), 90, (220, 200, 160), 0.12)
        circle(img, (x, y), 62, (14, 12, 16), -1)
        circle(img, (x, y), 62, (225, 205, 160), 2)
        text(img, nm, x, y, 56, "serifb", (240, 225, 190), "mm", c.at(t, "e08", 0.5, 0.8 + i * 0.25))
    # dashed empty "I"
    if k > 0.5:
        for a0 in range(0, 360, 20):
            cv2.ellipse(img, (int(cx), int(cy)), (95, 95), 0, a0, a0 + 10, scale((240, 225, 190), (k - 0.5) * 2), 3, cv2.LINE_AA)
        text(img, "我？", cx, cy, 48, "serifb", (240, 225, 190), "mm", (k - 0.5) * 2 * 0.8)
    fr.finish_glow(0.8)
    text(img, "五蕴和合", W / 2, 320, 76, "serifh", (240, 225, 190), "mm", c.at(t, "e07", 0.7), 3)
    tag(img, "类比 · 印照", W / 2, 420, AMBER, c.at(t, "e07", 0.6, 0.8), 36)
    text(img, "因缘聚合，找不到独立不变的主宰", W / 2, 1420, 40, "serifb", WHITE, "mm", c.at(t, "e08", 0.6, 4.0), 2)

def huayan(fr, t, c):
    fr.img[:] = nebula(20, (25, 22, 35), (35, 28, 30), 0.5)
    img = fr.img
    a = c.at(t, "e09", 0.9)
    gdot(fr, (W / 2, 760), 420, (200, 170, 120), 0.02)
    fr.finish_glow()
    quote_card(img, 420, "心如工畫師，畫種種五陰。",
               "《大方廣佛華嚴經》卷十〈夜摩天宮菩薩說偈品〉，東晉佛馱跋陀羅譯（六十卷本）",
               "心像一位画师，画出种种身心现象。", a, (225, 200, 150), 64, "serifh")
    k = c.at(t, "e10", 0.7)
    text(img, "解释器编出的“我”，也许就是这样一幅画", W / 2, 1180, 40, "serifb", AMBER, "mm", k, 2)

def yinzhao(fr, t, c):
    fr.img[:] = nebula(20, (25, 22, 35), (35, 28, 30), 0.5)
    img = fr.img
    a = c.at(t, "e11", 0.7)
    for i, (h, s, col) in enumerate((("修行中的观察", "佛学 · 五蕴", (225, 205, 160)), ("计算的设想", "明斯基 · 心智社会", CYAN))):
        x0 = 90 + i * 470
        card_box(img, x0, 600, x0 + 430, 860, a, col)
        text(img, h, x0 + 215, 690, 42, "serifb", col, "mm", a)
        text(img, s, x0 + 215, 770, 30, "sans", GREY, "mm", a)
    text(img, "≠", W / 2, 730, 70, "sansb", WHITE, "mm", a)
    text(img, "不是同一个命题", W / 2, 470, 48, "serifb", WHITE, "mm", a, 2)
    k = c.at(t, "e12", 0.8)
    text(img, "是印照，", W / 2, 1060, 80, "serifh", (240, 225, 190), "mm", c.at(t, "e12", 0.6, 2.5), 3)
    text(img, "不是证明。", W / 2, 1180, 80, "serifh", AMBER, "mm", c.at(t, "e12", 0.6, 3.6), 3)

# ======================= 涌现之争 =======================
TOK = "大 模 型 只 是 在 海 量 文 字 上 一 遍 遍 预 测 下 一 个 词 ……".split()
def llm_train(fr, t, c):
    fr.img[:] = grid_bg(3)
    g = graph()
    g.draw(fr, t, 0.7)
    lt = c.lt(t)
    for i in range(14):
        u = (lt * 0.25 + i / 14) % 1
        x = 120 + 840 * ((i * 37) % 14) / 14
        y = 1420 - u * 1000
        text(fr.img, TOK[i % len(TOK)], x, y, 34, "sans5", CYAN, "mm", 0.6 * (1 - u))
    fr.finish_glow()
    text(fr.img, "把目光转向机器", W / 2, 340, 58, "serifb", WHITE, "mm", c.at(t, "f01", 0.6) * (1 - c.at(t, "f02", 0.5)), 2)
    tag(fr.img, "“推理模块”：没人写过", W / 2, 340, RED, c.at(t, "f02", 0.6), 40)
    tag(fr.img, "训练目标：预测下一个词", W / 2, 1460, CYAN, c.at(t, "f02", 0.6, 2.5), 36)
    text(fr.img, "规模越来越大之后……", W / 2, 440, 44, "serifb", AMBER, "mm", c.at(t, "f03", 0.6), 2)

def wei(fr, t, c):
    fr.img[:] = grid_bg(3)
    a = c.at(t, "f04", 0.7)
    book_card(fr.img, 330, "《大语言模型的涌现能力》", "Wei et al., Emergent Abilities of Large Language Models", "Transactions on Machine Learning Research · 2022", a)
    q = c.at(t, "f05", 0.7)
    quote_card(fr.img, 780, "We consider an ability to be emergent if it is not present in smaller models but is present in larger models.",
               "Wei et al. 2022, Abstract", "小模型身上没有、大模型身上才出现的能力，叫“涌现”。", q, CYAN, 40, "serif")

def step_curve(fr, t, c):
    fr.img[:] = grid_bg(3)
    x0, y0, x1, y1 = 160, 560, 940, 1240
    chart_axes(fr, x0, y0, x1, y1, 1.0, "模型规模（对数）→", "正确率")
    up = c.at(t, "f06", 4.0, 1.0)
    curve(fr, step_ramp_pts(x0, y0, x1, y1, 0.0), AMBER, 1.0, up)
    fr.finish_glow()
    text(fr.img, "多位数加法（示意）", W / 2, 380, 46, "serifb", WHITE, "mm", c.at(t, "f06", 0.6), 2)
    if up > 0.75:
        tag(fr.img, "一道台阶？", W / 2 + 180, 760, AMBER, ease((up - 0.75) * 4), 40)
    text(fr.img, "继续放大，新能力会自己蹦出来？", W / 2, 1400, 42, "serifb", AMBER, "mm", c.at(t, "f07", 0.6), 2)

def mirage(fr, t, c):
    fr.img[:] = grid_bg(3)
    a = c.at(t, "f08", 0.7)
    # heat shimmer
    y = book_card(fr.img, 360, "《涌现能力，是海市蜃楼吗？》", "Schaeffer, Miranda & Koyejo, Are Emergent Abilities of Large Language Models a Mirage?",
                  "斯坦福大学 · NeurIPS 2023", a, None, AMBER)
    if a > 0.5:
        band = fr.img[600:1300].copy()
        for yy in range(0, band.shape[0], 4):
            sh = int(5 * math.sin(yy * 0.05 + t * 6))
            band[yy:yy + 4] = np.roll(band[yy:yy + 4], sh, axis=1)
        fr.img[600:1300] = band
    tag(fr.img, "NeurIPS 2023 优秀论文奖（Outstanding Main Track Paper）", W / 2, 1100, AMBER, c.at(t, "f09", 0.6), 30)

def metric(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    k = c.at(t, "f10", 0.6)
    text(img, "问题可能出在：打分方式", W / 2, 320, 54, "serifb", WHITE, "mm", k, 2)
    text(img, "12345 + 67890 = 80235", W / 2, 450, 56, "sansb", CYAN, "mm", c.at(t, "f11", 0.6))
    tag(img, "规则：全对才算对，错一位 = 0 分", W / 2, 540, RED, c.at(t, "f11", 0.6, 1.5), 34)
    rows = [("80935", 1), ("80135", 1), ("81235", 1), ("80235", 0)]
    answers = [("83975", 3), ("80975", 2), ("80295", 1), ("80235", 0)]
    p = c.at(t, "f12", 4.5)
    for i, (ans, nerr) in enumerate(answers):
        a = clamp(p * 4 - i)
        if a <= 0:
            continue
        y = 680 + i * 150
        text(img, ["小模型", "中模型", "大一些", "更大"][i], 160, y, 34, "sans5", GREY, "lm", a)
        x = 420
        for j, ch in enumerate(ans):
            wrong = ch != "80235"[j]
            text(img, ch, x + j * 56, y, 56, "sansb", RED if wrong else GREEN, "mm", a)
        sc = 1.0 if nerr == 0 else 0.0
        text(img, f"{int(sc)} 分", 900, y, 52, "sansh", GREEN if sc else RED, "mm", a, 2)
        text(img, f"错 {nerr} 位", 740, y, 30, "sans5", GREY, "mm", a)
    fr.finish_glow()

def smooth(fr, t, c):
    fr.img[:] = grid_bg(3)
    x0, y0, x1, y1 = 160, 520, 940, 1120
    chart_axes(fr, x0, y0, x1, y1, 1.0, "模型规模（对数）→", "得分")
    m = c.at(t, "f13", 2.2, 2.0)
    curve(fr, step_ramp_pts(x0, y0, x1, y1, 0.0), AMBER, 1 - 0.7 * m, 1.0)
    if m > 0:
        curve(fr, step_ramp_pts(x0, y0, x1, y1, 1.0), CYAN, m, 1.0)
    fr.finish_glow()
    text(fr.img, "全对 / 全错", 700, 600, 34, "sansb", AMBER, "mm", 1 - 0.6 * m)
    text(fr.img, "连续指标：每位对了多少", 560, 860, 34, "sansb", CYAN, "mm", m)
    text(fr.img, "同一批模型，换一把尺子", W / 2, 360, 50, "serifb", WHITE, "mm", c.at(t, "f13", 0.6), 2)
    q = c.at(t, "f14", 0.7)
    if q > 0:
        rect_alpha(fr.img, 0, 1180, W, 1660, BG, 0.0)
        quote_card(fr.img, 1190, "…emergent abilities appear due the researcher's choice of metric rather than due to fundamental changes in model behavior with scale.",
                   "Schaeffer, Miranda & Koyejo, NeurIPS 2023, Abstract", None, q, CYAN, 32, "serif")

def both(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    a = c.at(t, "f15", 0.6)
    text(img, "那，涌现是错觉吗？", W / 2, 320, 56, "serifb", WHITE, "mm", a * (1 - c.at(t, "f16", 0.5)), 2)
    tag(img, "争论尚未完全结束", W / 2, 420, AMBER, c.at(t, "f15", 0.6, 1.5) * (1 - c.at(t, "f16", 0.5)), 36)
    k = c.at(t, "f16", 0.8)
    bar = c.at(t, "f18b", 0.6)
    if k > 0 and bar <= 0.01:
        x0, x1 = 160, 920
        for i, (lab, col, fn, y) in enumerate((("模型内部：平滑增长", CYAN, lambda u: u ** 1.4, 820), ("用户感受：突然开窍", AMBER, lambda u: ease((u - 0.75) / 0.05), 1180))):
            yb = y + 120
            pts = [(x0 + (x1 - x0) * u, yb - 220 * fn(u)) for u in np.linspace(0, 1, 60)]
            curve(fr, pts, col, k, 1.0, dots=False)
            text(img, lab, W / 2, y - 140, 40, "sansb", col, "mm", k, 2)
        text(img, "可以同时成立", W / 2, 1420, 52, "serifh", WHITE, "mm", c.at(t, "f16", 0.6, 2.5), 3)
        text(img, "错一位 = 全错 = 不能用", W / 2, 360, 44, "serifb", RED, "mm", c.at(t, "f17", 0.6) * (1 - c.at(t, "f18", 0.5)), 2)
        text(img, "里面一点点进步，外面像突然开窍", W / 2, 360, 42, "serifb", AMBER, "mm", c.at(t, "f18", 0.6), 2)
    if bar > 0:
        p = clamp((t - c.s("f18b")) / max(1, c.e("f18b") - c.s("f18b")))
        text(img, "比方：背单词", W / 2, 340, 58, "serifh", WHITE, "mm", bar, 3)
        text(img, "每天的进步", 160, 700, 38, "sansb", CYAN, "lm", bar)
        cv2.rectangle(img, (160, 750), (920, 800), scale(GREY, 0.5 * bar), 2)
        cv2.rectangle(img, (162, 752), (162 + int(756 * p), 798), scale(CYAN, bar), -1)
        text(img, "考试：一字不差默写整段", 160, 950, 38, "sansb", AMBER, "lm", bar)
        months = ["一月", "二月", "三月", "四月"]
        for i, mth in enumerate(months):
            sc = "100" if (i == 3 and p > 0.85) else "0"
            text(img, mth, 230 + i * 210, 1040, 32, "sans5", GREY, "mm", bar * clamp(p * 5 - i))
            text(img, sc, 230 + i * 210, 1120, 64, "sansh", GREEN if sc == "100" else RED, "mm", bar * clamp(p * 5 - i), 2)
    fr.finish_glow()

# ======================= 打开黑箱 =======================
def cube(fr, cx, cy, s, t, open_k=0.0, crack=0.0):
    img = fr.img
    a = 0.6 + 0.4 * math.sin(t)
    pts = np.array([(cx - s, cy - s * 0.4), (cx, cy - s * 0.85), (cx + s, cy - s * 0.4), (cx + s, cy + s * 0.6), (cx, cy + s * 1.05), (cx - s, cy + s * 0.6)], np.int32)
    cv2.fillPoly(img, [pts], (8, 10, 16), cv2.LINE_AA)
    cv2.polylines(img, [pts], True, scale(GREY, 0.7), 3, cv2.LINE_AA)
    line(img, (cx - s, cy - s * 0.4), (cx, cy + s * 0.05), scale(GREY, 0.6), 3)
    line(img, (cx + s, cy - s * 0.4), (cx, cy + s * 0.05), scale(GREY, 0.6), 3)
    line(img, (cx, cy + s * 0.05), (cx, cy + s * 1.05), scale(GREY, 0.6), 3)
    if crack > 0:
        rng = np.random.default_rng(3)
        for i in range(7):
            p = (cx + rng.uniform(-0.6, 0.6) * s, cy + rng.uniform(-0.2, 0.7) * s)
            q = (p[0] + rng.normal(0, 60), p[1] + rng.normal(0, 60))
            gline(fr, p, q, CYAN, crack * 0.9, 3)
        gdot(fr, (cx, cy + s * 0.05), s * 0.35 * crack, CYAN, 0.15 * crack)

def blackbox(fr, t, c):
    fr.img[:] = grid_bg(3)
    cr = c.at(t, "g01", 1.2, 1.5)
    cube(fr, W / 2, 900, 300, t, crack=cr)
    fr.finish_glow()
    text(fr.img, "打开黑箱", W / 2, 330, 80, "serifh", WHITE, "mm", c.at(t, "g01", 0.6), 3)
    b = c.at(t, "g02", 0.6)
    if b > 0:
        book_card(fr.img, 1300, "《大语言模型的生物学》", "On the Biology of a Large Language Model", "Anthropic · 2025-03-27 · transformer-circuits.pub", b)

class Features:
    def __init__(self, n=900, seed=41):
        rng = np.random.default_rng(seed)
        self.p = rng.uniform((70, 480), (W - 70, 1280), (n, 2))
        self.ph = rng.uniform(0, 6, n)
        self.c = rng.integers(0, 3, n)
FE = Features()

def features(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    a = c.at(t, "g04", 1.0)
    for i, (p, ph) in enumerate(zip(FE.p, FE.ph)):
        v = 0.5 + 0.5 * math.sin(t * 1.4 + ph)
        if v ** 4 < 0.2:
            circle(img, p, 2, scale(GREY, 0.4 * a))
        else:
            col = (CYAN, VIOLET, AMBER)[FE.c[i]]
            gdot(fr, p, 7, col, 0.45 * a * v ** 4)
    gk = c.at(t, "g06", 0.8, 1.5)
    if gk > 0:
        graph().draw(fr, t, gk)
    fr.finish_glow()
    text(img, "替代模型 → 约 3000 万个特征", W / 2, 340, 48, "serifb", WHITE, "mm", c.at(t, "g04", 0.6), 2)
    text(img, "研究对象：Claude 3.5 Haiku（轻量级模型）", W / 2, 420, 30, "sans5", GREY, "mm", c.at(t, "g03", 0.6))
    lab = c.at(t, "g05", 0.6)
    for i, (s, col, x, y) in enumerate((("概念：“兔子”", CYAN, 300, 640), ("语法：句尾", VIOLET, 760, 840), ("打算：押韵", AMBER, 420, 1080))):
        if lab > 0 and gk < 0.5:
            tag(img, s, x, y, col, clamp(lab * 3 - i) * (1 - gk * 2), 32)
    tag(img, "归因图 attribution graph", W / 2, 1400, AMBER, gk, 38)

def dallas(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    q = c.at(t, "g07", 0.6)
    text(img, "Fact: the capital of the state containing Dallas is", W / 2, 330, 32, "serif", WHITE, "mm", q)
    text(img, "（达拉斯所在州的首府是？）", W / 2, 385, 32, "sans", GREY, "mm", q)
    nodes = [((W / 2, 1300), "Dallas 达拉斯", CYAN), ((W / 2 - 180, 960), "Texas 得克萨斯", VIOLET), ((W / 2, 620), "Austin 奥斯汀", AMBER)]
    s1 = c.at(t, "g08", 0.8, 0.8)
    s2 = c.at(t, "g08", 0.8, 3.0)
    sc = c.at(t, "g09", 0.8, 4.5)
    ks = [q, s1, s2]
    for i in range(2):
        p, q2 = nodes[i][0], nodes[i + 1][0]
        k = ks[i + 1]
        if k > 0:
            e = (lerp(p[0], q2[0], k), lerp(p[1], q2[1], k))
            gline(fr, p, e, AMBER, 0.9, 4)
            line(img, p, e, AMBER, 4)
    if sc > 0:
        for u in np.linspace(0, 1, 16)[::2]:
            p0 = (lerp(nodes[0][0][0], nodes[2][0][0], u) + 160 * math.sin(u * math.pi), lerp(nodes[0][0][1], nodes[2][0][1], u))
            u2 = u + 1 / 30
            p1 = (lerp(nodes[0][0][0], nodes[2][0][0], u2) + 160 * math.sin(u2 * math.pi), lerp(nodes[0][0][1], nodes[2][0][1], u2))
            line(img, p0, p1, scale(GREY, sc), 3)
        text(img, "也有“抄近路”的直接连线", W / 2 + 290, 960, 30, "sans5", GREY, "mm", sc)
    for (p, lab, col), k in zip(nodes, ks):
        gdot(fr, p, 70, col, 0.6 * k)
    fr.finish_glow()
    for (p, lab, col), k in zip(nodes, ks):
        if k > 0:
            card_box(img, p[0] - 170, p[1] - 45, p[0] + 170, p[1] + 45, k, col, fa=0.9)
            text(img, lab, p[0], p[1], 36, "sansb", col, "mm", k)
    tag(img, "在内部走了两步", W / 2, 1450, AMBER, c.at(t, "g09", 0.6), 40)
    text(img, "归因图示意（据 Anthropic, 2025）", W / 2, 1520, 26, "sans", GREY, "mm", q)

def poem(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    g = graph()
    rab = c.at(t, "g12", 0.8, 1.5)
    sup = c.at(t, "g13", 0.5, 0.2)
    grn = c.at(t, "g13", 0.5, 4.5)
    hot = {len(g.nodes) - 3: rab * (1 - sup), len(g.nodes) - 5: sup * (1 - grn), len(g.nodes) - 1: grn}
    g.draw(fr, t, 0.5, hot=hot)
    fr.finish_glow()
    a = c.at(t, "g10", 0.6)
    text(img, "He saw a carrot and had to grab it,", W / 2, 330, 44, "serif", WHITE, "mm", a)
    l2 = "His hunger was like a starving rabbit"
    if t > c.s("g11"):
        wr = clamp((t - c.s("g11")) / 2.5)
        if t > c.s("g12"):
            wr = clamp((t - c.s("g12") - 1.8) / max(1, c.e("g12") - c.s("g12") - 2))
        n = int(len(l2) * wr)
        x0 = W / 2 - text_size(l2, 44, "serif")[0] / 2
        text(img, l2[:n], x0, 400, 44, "serif", AMBER, "lm", 1.0 if n else 0)
        if sup > 0:
            rect_alpha(img, 0, 370, W, 430, BG, sup)
            alt = "…like a starving habit?" if grn < 0.5 else "…ending with “green”"
            text(img, alt, W / 2, 400, 44, "serif", RED if grn < 0.5 else GREEN, "mm", sup)
    tag(img, "grab it ↔ rabbit 押韵", W / 2, 1330, CYAN, c.at(t, "g11", 0.6, 2.0) * (1 - sup), 32)
    for idx, lab, col, k in ((len(g.nodes) - 3, "规划：rabbit", AMBER, rab * (1 - sup)), (len(g.nodes) - 5, "改押：habit", RED, sup * (1 - grn)), (len(g.nodes) - 1, "注入：green", GREEN, grn)):
        if k > 0.02:
            x, y = g.nodes[idx][:2]
            tag(img, lab, min(W - 180, max(180, x)), y - 70, col, k, 34)
    tag(img, "它在规划——却没有“规划模块”", W / 2, 1420, AMBER, c.at(t, "g14", 0.6), 38)

def limits(fr, t, c):
    fr.img[:] = grid_bg(3)
    img = fr.img
    a = c.at(t, "g15", 0.6)
    cx, cy, r = W / 2, 760, 230
    if a > 0 and c.at(t, "g17", 0.5) < 1:
        k = 1 - c.at(t, "g17", 0.5)
        cv2.circle(img, (int(cx), int(cy)), r, scale(GREY, 0.3 * a * k), -1, cv2.LINE_AA)
        cv2.ellipse(img, (int(cx), int(cy)), (r, r), -90, 0, 90 * ease(c.at(t, "g15", 1.2, 1.0)), scale(AMBER, a * k), -1, cv2.LINE_AA)
        text(img, "≈ 1/4", cx + 120, cy - 120, 48, "sansh", WHITE, "mm", a * k, 2)
        text(img, "的提示给出令人满意的洞察（作者自述）", W / 2, cy + r + 70, 36, "sansb", AMBER, "mm", a * k)
        text(img, "研究的是替代模型，不是原模型", W / 2, cy + r + 150, 36, "sansb", RED, "mm", c.at(t, "g16", 0.6) * k)
    g = c.at(t, "g17", 0.8, 0.5)
    if g > 0:
        graph().draw(fr, t, g, flow=1.5, base=0.55)
        text(img, "没有推理中枢，只有特征之间的协作", W / 2, 1420, 42, "serifb", WHITE, "mm", c.at(t, "g17", 0.6, 2.5), 2)
    s = c.at(t, "g18", 0.8)
    if s > 0:
        rect_alpha(img, 0, 0, W, H, BG, 0.6 * s)
        field().draw(fr, t, camz=t, cy=680, f=500, bright=0.8 * s, ylim=(430, 930))
        text(img, "≈", W / 2, 980, 80, "sansb", WHITE, "mm", s)
        text(img, "这和大脑，惊人地相似", W / 2, 1420, 46, "serifb", AMBER, "mm", s, 2)
    fr.finish_glow()
    tag(img, "局限，如实说", W / 2, 320, RED, a, 40)

# ======================= 收束 =======================
def finale(fr, t, c):
    fr.img[:] = nebula(1, (10, 30, 70), (40, 15, 70), 1.0)
    lt = c.lt(t)
    z = ease(lt / 8)
    field().draw(fr, t, camz=-lt * 2, f=900 - 500 * z, bright=1.1)
    fr.finish_glow()
    text(fr.img, "大脑与模型，说着同一件事", W / 2, 360, 46, "serifb", GREY, "mm", c.at(t, "h01", 0.6), 2)
    k = c.at(t, "h02", 1.0)
    text(fr.img, "智慧，", W / 2, 820, 88, "serifh", WHITE, "mm", k, 3)
    text(fr.img, "可以从没有中心的协作里", W / 2, 950, 64, "serifh", WHITE, "mm", c.at(t, "h02", 1.0, 0.6), 3)
    text(fr.img, "长出来", W / 2, 1070, 88, "serifh", AMBER, "mm", c.at(t, "h02", 1.0, 1.8), 3)

def finale2(fr, t, c):
    fr.img[:] = nebula(2, (30, 20, 50), (10, 30, 60), 0.8)
    a = c.at(t, "h03", 0.6)
    k = c.at(t, "h04", 0.8)
    if k < 1:
        graph().draw(fr, t, (1 - k) * 0.9, flow=1.2)
    if k > 0:
        drafts_draw(fr, t, k, winner_k=c.at(t, "h04", 0.8, 2.5))
    fr.finish_glow()
    text(fr.img, "与其相信里面有个可靠的小人，", W / 2, 330, 42, "serifb", WHITE, "mm", a * (1 - k), 2)
    text(fr.img, "不如老老实实看线路", W / 2, 400, 48, "serifb", CYAN, "mm", c.at(t, "h03", 0.6, 3.0) * (1 - k), 2)
    text(fr.img, "对自己，少一点执着", W / 2, 360, 56, "serifh", AMBER, "mm", k, 3)
    text(fr.img, "“我”：众多草稿里，声音最大的一份", W / 2, 1420, 40, "serifb", WHITE, "mm", c.at(t, "h04", 0.6, 2.5), 2)

def takeaway(fr, t, c):
    fr.img[:] = nebula(2, (30, 20, 50), (10, 30, 60), 0.6)
    a = c.at(t, "h05", 0.7)
    card_box(fr.img, 90, 560, W - 90, 1220, a, AMBER)
    text(fr.img, "带一句话回去", W / 2, 650, 44, "sansb", AMBER, "mm", a)
    paragraph(fr.img, "好结果，常常来自没有中心的协作；", W / 2, 760, 50, "serifb", WHITE, 820, 1.5, "m", a)
    paragraph(fr.img, "遇到“突然开窍”，先看看是不是打分的尺子造成的台阶。", W / 2, 920, 46, "serif", WHITE, 820, 1.5, "m", c.at(t, "h05", 0.7, 2.5))

STARS = None
def sutra(fr, t, c):
    fr.img[:] = nebula(4, (12, 16, 30), (22, 18, 30), 0.6)
    lt = c.lt(t)
    field().draw(fr, t, camz=-30 - lt * 0.5, cy=600, f=380, bright=0.6, ylim=(0, 1250), pulses=False, sharp=False, cols=((200, 200, 230), (160, 180, 230), (220, 200, 170)))
    seated_figure(fr, W / 2, 1520, 150, WHITE, 0.9)
    fr.finish_glow(0.9)
    a = c.at(t, "h06", 1.0)
    quote_card(fr.img, 330, "凡所有相，皆是虛妄；若見諸相非相，則見如來。", "《金剛般若波羅蜜經》，姚秦鳩摩羅什譯",
               "一切显现的相，都不是固定实有的；看清相不是固定的，才见到真实。", a, (225, 200, 150), 54, "serifh")
    tag(fr.img, "印照，不是证明", W / 2, 1100, (225, 200, 150), c.at(t, "h07", 0.6, 1.0), 34)

def sutra2(fr, t, c):
    fr.img[:] = nebula(4, (12, 16, 30), (22, 18, 30), 0.6)
    lt = c.lt(t)
    field().draw(fr, t, camz=-30 - lt * 0.5, cy=600, f=380 - 60 * ease(lt / 12), bright=0.7, ylim=(0, 1350), pulses=False, sharp=False, cols=((200, 200, 230), (160, 180, 230), (220, 200, 170)))
    seated_figure(fr, W / 2, 1520, 150, WHITE, 0.9)
    fr.finish_glow(0.9)
    text(fr.img, "大脑里，没有那个小人", W / 2, 520, 50, "serifb", WHITE, "mm", c.at(t, "h08", 0.8), 2)
    text(fr.img, "机器里，也没有", W / 2, 610, 50, "serifb", WHITE, "mm", c.at(t, "h08", 0.8, 2.0), 2)
    text(fr.img, "也许，本来就不需要一个。", W / 2, 840, 60, "serifh", (240, 225, 190), "mm", c.at(t, "h09", 1.2), 3)

RENDERERS = dict(
    hook=hook, hook2=hook2, self=self_scene, tease_split=tease_split, tease_poem=tease_poem, tease_step=tease_step, twin=twin,
    theater=theater, dennett=dennett, pineal=pineal, homunculus=homunculus, drafts=drafts, label_phil=label_phil,
    gw_stage=gw_stage, gw_compete=gw_compete, mask=mask, ignite=ignite, cogitate=cogitate,
    split_intro=split_intro, split_rule=split_rule, split_exp=split_exp, split_ask=split_ask, interpreter=interpreter,
    choice=choice, split_debate=split_debate, society=society, minsky_q=minsky_q, society2=society2, skandha=skandha,
    huayan=huayan, yinzhao=yinzhao, llm_train=llm_train, wei=wei, step_curve=step_curve, mirage=mirage, metric=metric,
    smooth=smooth, both=both, blackbox=blackbox, features=features, dallas=dallas, poem=poem, limits=limits,
    finale=finale, finale2=finale2, takeaway=takeaway, sutra=sutra, sutra2=sutra2,
)
