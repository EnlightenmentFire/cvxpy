"""场景（上）：钩子、笛卡尔剧场、全局工作空间。"""
from prims import *

FIELD = None
def field():
    global FIELD
    if FIELD is None:
        FIELD = NeuralField(1500, seed=7)
    return FIELD
GRAPH = None
def graph():
    global GRAPH
    if GRAPH is None:
        GRAPH = FeatureGraph()
    return GRAPH

class Cue:
    def __init__(self, sc):
        self.t0, self.t1, self.key = sc["t0"], sc["t1"], sc["key"]
        self.L = {l["id"]: l for l in sc["lines"]}
        self.ids = [l["id"] for l in sc["lines"]]
    def s(self, i): return self.L[i]["start"]
    def e(self, i): return self.L[i]["end"]
    def at(self, t, i, d=0.6, off=0.0):
        return ease((t - self.s(i) - off) / d)
    def frac(self, t, i):
        return clamp((t - self.s(i)) / max(0.1, self.e(i) - self.s(i)))
    def lt(self, t): return t - self.t0
    def p(self, t): return clamp((t - self.t0) / max(0.1, self.t1 - self.t0))
    def fin(self, t, d=0.6): return fade(t, self.t0, self.t1, d)

# ======================= HOOK =======================
def hook(fr, t, c):
    fr.img[:] = nebula(1, (10, 30, 70), (40, 15, 70), 1.0)
    lt = c.lt(t)
    camz = lt * 6.0 + 2.0
    field().draw(fr, t, camz=camz, bright=1.25, dim_center=min(1, lt / 3) * 0.9)
    fr.finish_glow(1.0)
    a = 1.0
    reticle(fr, W / 2, H * 0.46, 120 + 10 * math.sin(lt * 3), lt, CYAN, a)
    st = "正在定位：意识中心……" if lt < c.e("a01") - c.t0 - 0.8 else "中心：未找到"
    col = CYAN if st.startswith("正") else RED
    text(fr.img, st, W / 2, H * 0.46 + 200, 36, "sansb", col, "mm", 1.0, 2)
    text(fr.img, f"扫描深度 {lt * 61.7:06.1f} μm", W / 2, H * 0.46 + 250, 26, "sans", GREY, "mm", 0.8)

def hook2(fr, t, c):
    fr.img[:] = grid_bg(3)
    lt = c.lt(t)
    # feature activation map
    rng = np.random.default_rng(11)
    cols, rows = 12, 16
    x0, y0, cw = 120, 560, 70
    base = rng.random((rows, cols))
    for r in range(rows):
        for q in range(cols):
            v = 0.5 + 0.5 * math.sin(t * 2.1 + base[r, q] * 9 + r * 0.4)
            v = v ** 3 * base[r, q]
            col = mix(BLUE, AMBER, v) if v > 0.35 else mix((20, 30, 60), BLUE, v * 2)
            x, y = x0 + q * cw, y0 + r * cw * 0.72
            cv2.rectangle(fr.img, (x + 3, int(y) + 3), (x + cw - 4, int(y + cw * 0.72) - 4), scale(col, 0.25 + 0.75 * v), -1)
            if v > 0.45:
                gdot(fr, (x + cw / 2, y + cw * 0.36), 22, col, v * 0.6)
    fr.finish_glow(0.9)
    reticle(fr, W / 2, 560 + 16 * cw * 0.36, 140, lt, RED, 1.0)
    text(fr.img, "大模型内部特征图（示意）", W / 2, 500, 34, "sans5", GREY, "mm")
    text(fr.img, "中心：未找到", W / 2, 1420, 40, "sansb", RED, "mm", 1.0, 2)

def self_scene(fr, t, c):
    fr.img[:] = nebula(2, (30, 20, 50), (10, 30, 60), 0.9)
    lt = c.lt(t)
    P = head_profile(fr, W / 2 - 20, H * 0.47, 380, AMBER, 1.0)
    # the "I" dot inside the head, flickering, then dispersing into a network
    k = c.at(t, "a04", 1.5)
    cx, cy = W / 2 - 40, H * 0.47 - 100
    rng = np.random.default_rng(4)
    pts = rng.normal(0, 1, (60, 2)) * (60 + 170 * k)
    for i, (dx, dy) in enumerate(pts):
        a = 0.4 + 0.4 * math.sin(t * 3 + i)
        gdot(fr, (cx + dx * k, cy + dy * k * 0.8), 6, CYAN if k > 0.3 else AMBER, a * (0.3 + k))
    if k > 0.2:
        for i in range(0, 59):
            j = (i * 7 + 3) % 60
            gline(fr, (cx + pts[i][0] * k, cy + pts[i][1] * k * 0.8), (cx + pts[j][0] * k, cy + pts[j][1] * k * 0.8), CYAN, 0.15 * k)
    gdot(fr, (cx, cy), 40 * (1 - k) + 6, AMBER, (1 - k) * (0.8 + 0.2 * math.sin(t * 6)))
    fr.finish_glow()
    text(fr.img, "我", cx, cy, 64, "serifb", AMBER, "mm", 1 - k, 2)
    if k > 0.4:
        text(fr.img, "「我」住在哪儿？", W / 2, H * 0.47 + 480, 52, "serifb", WHITE, "mm", ease((k - 0.4) * 3), 2)

# ---- teasers ----
def tease_split(fr, t, c):
    fr.img[:] = nebula(5, (30, 15, 40), (10, 25, 60), 0.9)
    k = c.at(t, "a05", 1.0)
    cut = c.at(t, "a05", 0.8, 1.2)
    brain_top(fr, W / 2, 820, 360, CYAN, 1.0, gap=10 + 40 * cut, lcol=CYAN, rcol=VIOLET)
    if cut > 0:
        for y in range(470, 1170, 30):
            gdot(fr, (W / 2 + 8 * math.sin(y * 0.1 + t * 5), y), 5, RED, 0.6 * cut)
    fr.finish_glow()
    text(fr.img, "左右脑被切断联系", W / 2, 400, 46, "sansb", RED, "mm", cut, 2)
    # left hand picks shovel
    a2 = c.at(t, "a05", 0.6, 3.5)
    tag(fr.img, "左手 → 拿起铲子", W / 2, 1290, CYAN, a2, 38)
    b = c.at(t, "a06", 0.6)
    if b > 0:
        card_box(fr.img, 140, 1360, W - 140, 1470, b, AMBER)
        text(fr.img, "“理由很简单……”", W / 2, 1405, 44, "serifb", WHITE, "mm", b)
        text(fr.img, "说得头头是道——但是错的", W / 2, 1452, 28, "sans5", AMBER, "mm", c.at(t, "a06", 0.6, 1.8))
    text(fr.img, "示意", W - 60, 1170, 26, "sans", GREY, "rm", 0.8)

def tease_poem(fr, t, c):
    fr.img[:] = grid_bg(3)
    g = graph()
    plan = c.at(t, "a08", 0.8, 1.0)
    hot = {len(g.nodes) - 3: plan, len(g.nodes) - 9: plan * 0.6}
    g.draw(fr, t, 0.55, hot=hot)
    fr.finish_glow()
    l1 = "He saw a carrot and had to grab it,"
    text(fr.img, l1, W / 2, 400, 44, "serif", WHITE, "mm", c.at(t, "a07", 0.6, 1.0))
    if plan > 0:
        x, y = g.nodes[len(g.nodes) - 3][:2]
        tag(fr.img, "规划：rabbit", x, y - 60, AMBER, plan, 34)
    l2 = "His hunger was like a starving rabbit"
    wr = c.frac(t, "a09") if t > c.s("a09") else 0
    n = int(len(l2) * wr)
    text(fr.img, l2[:n], W / 2 - text_size(l2, 44, "serif")[0] / 2, 470, 44, "serif", AMBER, "lm", 1.0 if n else 0)
    tag(fr.img, "“规划模块”：不存在", W / 2, 1400, RED, c.at(t, "a09", 0.6, 1.0), 38)
    text(fr.img, "大模型内部（示意）", W / 2, 1330, 28, "sans", GREY, "mm", 0.8)

def step_ramp_pts(x0, y0, x1, y1, m, n=60):
    pts = []
    for i in range(n):
        u = i / (n - 1)
        if m <= 0:
            v = 0.02 if u < 0.7 else 0.95
            v = 0.02 + 0.93 * ease((u - 0.68) / 0.06)
        smooth = 0.03 + 0.92 * u ** 1.6
        stepv = 0.02 + 0.93 * ease((u - 0.68) / 0.06)
        v = lerp(stepv, smooth, m)
        pts.append((x0 + (x1 - x0) * u, y1 - (y1 - y0) * v))
    return pts

def tease_step(fr, t, c):
    fr.img[:] = grid_bg(3)
    x0, y0, x1, y1 = 160, 620, 940, 1260
    chart_axes(fr, x0, y0, x1, y1, 1.0)
    m = c.at(t, "a10", 1.6, 2.0)
    curve(fr, step_ramp_pts(x0, y0, x1, y1, m), mix(AMBER, CYAN, m), 1.0, ease(c.lt(t) / 1.2))
    fr.finish_glow()
    text(fr.img, "突然开窍？" if m < 0.5 else "还是尺子造成的台阶？", W / 2, 470, 56, "serifb", mix(AMBER, CYAN, m), "mm", 1.0, 2)

def twin(fr, t, c):
    fr.img[:] = nebula(1, (10, 30, 70), (40, 15, 70), 0.9)
    lt = c.lt(t)
    field().draw(fr, t, camz=lt * 2, cy=640, f=600, bright=1.0, ylim=(300, 930))
    g = graph()
    g2 = FeatureGraph(layers=(5, 8, 10, 8, 5), x0=120, x1=960, y0=1000, y1=1330, seed=9, horizontal=True) if not hasattr(twin, "g2") else twin.g2
    twin.g2 = g2
    g2.draw(fr, t, 0.8)
    fr.finish_glow()
    rect_alpha(fr.img, 0, 950, W, 975, BG, 0.9)
    text(fr.img, "大脑：约 860 亿个神经元", W / 2, 330, 40, "sansb", CYAN, "mm", c.at(t, "a11", 0.5), 2)
    text(fr.img, "大模型：千亿级参数，海量运算", W / 2, 1380, 40, "sansb", VIOLET, "mm", c.at(t, "a11", 0.5, 1.6), 2)
    k = c.at(t, "a12", 0.6)
    tag(fr.img, "指挥官：无", W / 2, 962, RED, k, 40)

# ======================= 笛卡尔剧场 =======================
def theater_draw(fr, t, cx, cy, s, spot=1.0, seat_k=1.0, viewer=0.0, dissolve=0.0):
    img = fr.img
    # stage
    sw = s * 0.9
    stage = np.array([(cx - sw, cy - s * 0.1), (cx + sw, cy - s * 0.1), (cx + sw * 1.1, cy + s * 0.05), (cx - sw * 1.1, cy + s * 0.05)], np.int32)
    cv2.fillPoly(img, [stage], (22, 26, 40), cv2.LINE_AA)
    cv2.polylines(img, [stage], True, scale(GREY, 0.7), 2, cv2.LINE_AA)
    # curtains
    for side in (-1, 1):
        cur = np.array([(cx + side * sw, cy - s * 0.75), (cx + side * sw * 1.15, cy - s * 0.75), (cx + side * sw * 1.15, cy - s * 0.1), (cx + side * sw * 0.86, cy - s * 0.1)], np.int32)
        cv2.fillPoly(img, [cur], (70, 18, 30), cv2.LINE_AA)
    line(img, (cx - sw * 1.15, cy - s * 0.75), (cx + sw * 1.15, cy - s * 0.75), (90, 30, 40), 6)
    # spotlight cone
    if spot > 0:
        cone = np.array([(cx - 20, cy - s * 0.75), (cx + 20, cy - s * 0.75), (cx + s * 0.32, cy - s * 0.05), (cx - s * 0.32, cy - s * 0.05)], np.int32) // 2
        cv2.fillPoly(fr.g, [cone], gcol(WHITE, 0.10 * spot), cv2.LINE_AA)
        cv2.ellipse(fr.g, (int(cx / 2), int((cy - s * 0.05) / 2)), (int(s * 0.16), int(s * 0.03)), 0, 0, 360, gcol(WHITE, 0.35 * spot), -1, cv2.LINE_AA)
    # seats rows
    rng = np.random.default_rng(3)
    for r in range(6):
        yy = cy + s * 0.22 + r * s * 0.13
        n = 9 + r * 2
        for q in range(n):
            u = (q + 0.5) / n - 0.5
            x = cx + u * s * (1.5 + r * 0.25)
            y = yy + abs(u) ** 2 * s * 0.25
            if dissolve > 0:
                jr = rng.normal(0, 1, 2) * dissolve * 160
                x, y = x + jr[0], y + jr[1] - dissolve * 120 * rng.random()
            a = seat_k * (1 - dissolve * 0.9)
            cv2.rectangle(img, (int(x - 16), int(y - 14)), (int(x + 16), int(y + 14)), scale((60, 70, 95), a), -1)
            cv2.rectangle(img, (int(x - 16), int(y - 24)), (int(x + 16), int(y - 12)), scale((80, 90, 120), a), -1)
    if viewer > 0:
        vx, vy = cx, cy + s * 0.22 + 3 * s * 0.13 - 40
        cv2.circle(img, (int(vx), int(vy - 42)), 22, scale(AMBER, viewer), -1, cv2.LINE_AA)
        cv2.ellipse(img, (int(vx), int(vy)), (36, 26), 0, 180, 360, scale(AMBER, viewer), -1, cv2.LINE_AA)
        gdot(fr, (vx, vy - 30), 60, AMBER, 0.4 * viewer)

def theater(fr, t, c):
    fr.img[:] = nebula(6, (25, 20, 40), (40, 20, 30), 0.8)
    a1 = c.at(t, "b01", 1.0)
    # sensory streams flowing to the theater
    for i in range(14):
        u = ((t * 0.35 + i / 14) % 1)
        side = -1 if i % 2 else 1
        x = W / 2 + side * (520 - 480 * u)
        y = 420 + 380 * u + 30 * math.sin(i)
        gdot(fr, (x, y), 10, CYAN if side < 0 else VIOLET, 0.7 * a1 * (1 - u))
    text(fr.img, "眼睛", 130, 420, 34, "sans5", CYAN, "mm", a1)
    text(fr.img, "耳朵", W - 130, 420, 34, "sans5", VIOLET, "mm", a1)
    theater_draw(fr, t, W / 2, 960, 560, spot=1.0, viewer=c.at(t, "b02", 1.0))
    fr.finish_glow()
    if c.at(t, "b02", 0.5) > 0:
        text(fr.img, "“我”在这里看着一切？", W / 2, 1330, 40, "serifb", AMBER, "mm", c.at(t, "b02", 0.6, 1.0), 2)
    k = c.at(t, "b03", 0.7)
    text(fr.img, "笛卡尔剧场", W / 2, 300, 76, "serifh", WHITE, "mm", k, 3)
    text(fr.img, "Cartesian Theater", W / 2, 380, 36, "serif", GREY, "mm", k)

def dennett(fr, t, c):
    fr.img[:] = nebula(6, (25, 20, 40), (40, 20, 30), 0.7)
    theater_draw(fr, t, W / 2, 1180, 420, spot=0.5)
    fr.finish_glow(0.8)
    rect_alpha(fr.img, 0, 0, W, H, BG, 0.35)
    book_card(fr.img, 360, "《意识的解释》", "Daniel C. Dennett, Consciousness Explained", "Little, Brown · 1991", c.at(t, "b04", 0.8),
              "第 5 章：Multiple Drafts Versus the Cartesian Theater")

def pineal(fr, t, c):
    fr.img[:] = nebula(7, (15, 25, 55), (30, 15, 50), 0.8)
    brain_side(fr, W / 2, 840, 400, CYAN, 1.0)
    k = c.at(t, "b06", 1.5, 2.5)
    # pineal gland dot -> wanders to other areas
    spots = [(W / 2 - 30, 860), (W / 2 + 230, 700), (W / 2 - 150, 640), (W / 2 + 60, 560)]
    if k <= 0:
        p = spots[0]
    else:
        seg = min(2.999, k * 3)
        i = int(seg); f = ease(seg - i)
        p = (lerp(spots[i][0], spots[i + 1][0], f), lerp(spots[i][1], spots[i + 1][1], f))
    gdot(fr, p, 34, AMBER, 0.9 + 0.1 * math.sin(t * 5))
    fr.finish_glow()
    circle(fr.img, p, 12, AMBER)
    a = c.at(t, "b05", 0.6)
    text(fr.img, "松果体", spots[0][0] + 10, spots[0][1] + 70, 38, "sansb", AMBER, "mm", a * (1 - k), 2)
    text(fr.img, "笛卡尔：心灵与身体在此交会", W / 2, 1220, 40, "serifb", WHITE, "mm", a * (1 - k))
    text(fr.img, "换一个脑区……剧场还在", W / 2, 1220, 44, "serifb", AMBER, "mm", k, 2)
    text(fr.img, "示意", W - 60, 1120, 26, "sans", GREY, "rm", 0.8)

def homunculus(fr, t, c):
    fr.img[:] = nebula(8, (30, 20, 45), (15, 25, 55), 0.8)
    lt = c.lt(t)
    z = (lt * 0.25) % 1.0
    for n in range(6):
        s = 520 * (0.42 ** (n - z * 1.0))
        if s < 6 or s > 2000:
            continue
        a = clamp(1.2 - n * 0.18)
        head_profile(fr, W / 2 + s * 0.05, 860 + s * 0.05, s, mix(AMBER, CYAN, n / 5), a)
    fr.finish_glow()
    k = c.at(t, "b08", 0.8)
    text(fr.img, "小人里面，还有小人……", W / 2, 340, 50, "serifb", WHITE, "mm", c.at(t, "b07", 0.7), 2)
    k2 = c.at(t, "b09", 0.6)
    text(fr.img, "小人谬误", W / 2, 1380, 72, "serifh", AMBER, "mm", k2, 3)
    text(fr.img, "homunculus fallacy", W / 2, 1450, 34, "serif", GREY, "mm", k2)

class Drafts:
    def __init__(self, n=26, seed=12):
        rng = np.random.default_rng(seed)
        self.p = rng.uniform((80, 520), (W - 220, 1250), (n, 2))
        self.v = rng.normal(0, 14, (n, 2))
        self.lab = [["看", "听", "记忆", "预测", "语言", "情绪"][i % 6] for i in range(n)]
        self.rot = rng.uniform(-8, 8, n)
        self.seed = rng.integers(0, 1000, n)
DR = Drafts()

def drafts_draw(fr, t, a=1.0, winner_k=0.0, dissolve=0.0, win=7):
    img = fr.img
    for i, (p, v) in enumerate(zip(DR.p, DR.v)):
        x, y = p + v * math.sin(t * 0.3 + i)
        x, y = x, y - dissolve * 50
        w_, h_ = 150, 190
        win_i = (i == win)
        col = AMBER if win_i and winner_k > 0 else (200, 210, 230)
        aa = a * (0.55 if not win_i else 0.55 + 0.45 * winner_k)
        if win_i and winner_k > 0:
            gdot(fr, (x + w_ / 2, y + h_ / 2), 120, AMBER, 0.35 * winner_k)
        rect_alpha(img, x, y, x + w_, y + h_, (16, 22, 36), 0.85 * aa)
        rounded(img, x, y, x + w_, y + h_, 6, scale(col, aa), 2)
        text(img, DR.lab[i], x + 14, y + 26, 26, "sansb", scale(col, aa), "lm", 1)
        rng = np.random.default_rng(DR.seed[i] + int(t * 1.5))   # rewritten 1.5×/s
        for r in range(5):
            L = rng.uniform(0.3, 1.0) * (w_ - 30)
            yy = y + 60 + r * 24
            line(img, (x + 14, yy), (x + 14 + L, yy), scale(col, 0.6 * aa), 3)
            if rng.random() < 0.3:
                line(img, (x + 14, yy - 6), (x + 14 + L * 0.6, yy + 6), scale(RED, 0.7 * aa), 2)

def drafts(fr, t, c):
    fr.img[:] = nebula(9, (20, 25, 50), (35, 20, 45), 0.8)
    wk = c.at(t, "b13", 0.8)
    drafts_draw(fr, t, 1.0, wk)
    fr.finish_glow()
    k = c.at(t, "b10", 0.7)
    text(fr.img, "多重草稿模型", W / 2, 330, 70, "serifh", WHITE, "mm", k, 3)
    text(fr.img, "Multiple Drafts Model", W / 2, 405, 34, "serif", GREY, "mm", k)
    if wk > 0:
        x, y = DR.p[7]
        text(fr.img, "此刻占了上风的一稿", W / 2, 1330, 40, "sansb", AMBER, "mm", wk * (1 - c.at(t, "b14", 0.5)), 2)
    k3 = c.at(t, "b14", 0.6)
    tag(fr.img, "比方：一家没有总编的报社", W / 2, 1330, CYAN, k3, 38)

def label_phil(fr, t, c):
    fr.img[:] = nebula(6, (25, 20, 40), (40, 20, 30), 0.7)
    d = c.at(t, "b17", 2.5)
    theater_draw(fr, t, W / 2, 1060, 480, spot=0.6 * (1 - d), dissolve=d)
    fr.finish_glow()
    tag(fr.img, "哲学理论 · 影响大，批评也多", W / 2, 360, AMBER, c.at(t, "b15", 0.5), 40)
    k = c.at(t, "b16", 0.6)
    if k > 0:
        text(fr.img, "Consciousness Explained", W / 2, 470, 44, "serif", WHITE, "mm", k * (1 - c.at(t, "b17", 0.6)))
        text(fr.img, "“…Explained Away”", W / 2, 540, 44, "serif", RED, "mm", c.at(t, "b16", 0.5, 1.6) * (1 - c.at(t, "b17", 0.6)))
    text(fr.img, "没有最终的观众席", W / 2, 500, 58, "serifb", WHITE, "mm", c.at(t, "b17", 0.8, 0.8) * (1 - c.at(t, "b18", 0.5)), 2)
    text(fr.img, "那统一感从哪来？", W / 2, 500, 62, "serifb", CYAN, "mm", c.at(t, "b18", 0.6, 1.2), 3)

# ======================= 全局工作空间 =======================
SPECS = ["人脸", "语法", "距离", "颜色", "记忆", "声音", "运动", "数字", "气味", "情绪", "位置", "词义", "节奏", "边缘", "触觉", "预测"]
class Specs:
    def __init__(self, seed=21):
        rng = np.random.default_rng(seed)
        n = len(SPECS)
        ang = np.linspace(0, 2 * np.pi, n, endpoint=False) + rng.normal(0, 0.1, n)
        rr = rng.uniform(300, 420, n)
        self.p = np.stack([W / 2 + np.cos(ang) * rr, 900 + np.sin(ang) * rr * 1.05], 1)
        self.ph = rng.uniform(0, 6, n)
SP = Specs()

def gw_scene(fr, t, c, mode):
    fr.img[:] = nebula(10, (15, 20, 45), (30, 15, 45), 0.8)
    img = fr.img
    cx, cy = W / 2, 900
    if mode == "stage":
        spot = c.at(t, "c02", 1.0)
        comp = 0; win = 0; bc = 0
    else:
        spot = 1.0
        comp = c.at(t, "c03", 1.0)
        win = c.at(t, "c04", 1.0, 1.4)
        bc = c.at(t, "c04", 0.3, 3.0)
    # spotlight in centre
    cone = np.array([(cx - 30, 300), (cx + 30, 300), (cx + 170, cy + 60), (cx - 170, cy + 60)], np.int32) // 2
    cv2.fillPoly(fr.g, [cone], gcol(WHITE, 0.08 * spot), cv2.LINE_AA)
    cv2.ellipse(fr.g, (int(cx / 2), int((cy + 60) / 2)), (90, 18), 0, 0, 360, gcol(WHITE, 0.3 * spot), -1, cv2.LINE_AA)
    wi = 0
    for i, (p, ph) in enumerate(zip(SP.p, SP.ph)):
        act = 0.25 + 0.25 * math.sin(t * 2.5 + ph) if comp else 0.12
        pos = p
        if i == wi and win > 0:
            pos = (lerp(p[0], cx, win), lerp(p[1], cy, win))
        col = AMBER if (i == wi and win > 0) else CYAN
        gdot(fr, pos, 26 + (30 * win if i == wi else 0), col, act + (0.7 * win if i == wi else 0))
        circle(img, pos, 10 + (8 * win if i == wi else 0), scale(col, 0.5 + act))
        text(img, SPECS[i], pos[0], pos[1] + 44, 28, "sans5", scale(col, 0.7 + act), "mm", max(comp, 0.25) if mode != "stage" else 0.25)
    if bc > 0:
        for k in range(3):
            r = ((t * 260 + k * 220) % 660)
            gring(fr, (cx, cy), r, AMBER, 0.6 * bc * (1 - r / 660), 3)
        for i, p in enumerate(SP.p):
            if i != wi:
                gline(fr, (cx, cy), p, AMBER, 0.18 * bc)
                gdot(fr, p, 30, AMBER, 0.35 * bc)
    fr.finish_glow()
    if mode == "stage":
        k = c.at(t, "c01", 0.8)
        text(img, "全局工作空间理论", W / 2, 340, 66, "serifh", WHITE, "mm", k, 3)
        text(img, "Bernard J. Baars · A Cognitive Theory of Consciousness", W / 2, 410, 28, "serif", GREY, "mm", k)
        text(img, "Cambridge University Press · 1988", W / 2, 452, 28, "serif", GREY, "mm", k)
        text(img, "台下：没有观众", W / 2, 1330, 44, "serifb", AMBER, "mm", c.at(t, "c02", 0.6, 2.0), 2)
    else:
        text(img, "专门处理器在暗处竞争", W / 2, 340, 46, "serifb", WHITE, "mm", comp * (1 - c.at(t, "c04", 0.5, 1.0)), 2)
        text(img, "赢家被放大，广播全脑", W / 2, 340, 46, "serifb", AMBER, "mm", c.at(t, "c04", 0.6, 1.2) * (1 - c.at(t, "c05b", 0.5)), 2)
        text(img, "= 你“意识到”了", W / 2, 1400, 44, "serifb", AMBER, "mm", c.at(t, "c05", 0.6) * (1 - c.at(t, "c05b", 0.5)), 2)
        tag(img, "比方：开放办公室里的大喇叭", W / 2, 340, CYAN, c.at(t, "c05b", 0.6), 38)

def gw_stage(fr, t, c): gw_scene(fr, t, c, "stage")
def gw_compete(fr, t, c): gw_scene(fr, t, c, "compete")

def mask(fr, t, c):
    fr.img[:] = nebula(11, (15, 20, 40), (25, 15, 40), 0.6)
    img = fr.img
    k = c.at(t, "c06", 0.7)
    text(img, "全局神经工作空间", W / 2, 320, 62, "serifh", WHITE, "mm", k, 3)
    text(img, "Stanislas Dehaene · Consciousness and the Brain · Viking 2014", W / 2, 392, 26, "serif", GREY, "mm", k)
    # screen with flashing word
    sx0, sy0, sx1, sy1 = 190, 520, 890, 960
    a = c.at(t, "c07", 0.6)
    card_box(img, sx0, sy0, sx1, sy1, a, GREY, fill=(10, 12, 18), fa=0.95)
    cyc = (t - c.s("c07")) % 2.4 if t > c.s("c07") else -1
    long_ = t > c.s("c08") + 1.6
    if a > 0 and cyc >= 0:
        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        if cyc < 0.6:
            text(img, "+", cx, cy, 70, "sans5", WHITE, "mm", a)
        elif cyc < (0.64 if not long_ else 0.80):
            text(img, "海洋", cx, cy, 110, "sansh", WHITE, "mm", a)
        elif cyc < 1.4:
            text(img, "#&%@#", cx, cy, 110, "sansh", scale(GREY, 0.8), "mm", a)
    # timeline bar
    b = c.at(t, "c07", 0.6, 1.5)
    y = 1060
    line(img, (190, y), (890, y), scale(GREY, b), 3)
    segs = [(190, 330, "注视点", GREY), (330, 380 if not long_ else 440, "词 33ms" if not long_ else "词 更久", AMBER), (380 if not long_ else 440, 640, "遮挡图案", VIOLET)]
    for x0, x1, lab, col in segs:
        cv2.rectangle(img, (x0, y - 18), (x1, y + 18), scale(col, 0.7 * b), -1)
        text(img, lab, (x0 + x1) / 2, y + 52, 28, "sans5", col, "mm", b)
    r = c.at(t, "c08", 0.5)
    text(img, "没看见" if not long_ else "看见了！", W / 2, 1220, 58, "serifb", RED if not long_ else GREEN, "mm", r, 2)
    fr.finish_glow()

def ignite(fr, t, c):
    fr.img[:] = nebula(12, (15, 20, 45), (40, 15, 40), 0.8)
    img = fr.img
    conscious = t > c.s("c10")
    bx, by, bs = W / 2, 690, 320
    brain_side(fr, bx, by, bs, GREY, 0.8)
    vis = (bx - 0.8 * bs, by + 0.05 * bs)
    front = [(bx + 0.6 * bs, by - 0.2 * bs), (bx + 0.35 * bs, by - 0.45 * bs)]
    par = [(bx - 0.2 * bs, by - 0.55 * bs), (bx - 0.5 * bs, by - 0.35 * bs)]
    # activity over a 0.8s loop
    u = ((t - c.t0) % 2.6) / 2.6
    vis_a = math.exp(-((u - 0.15) / 0.08) ** 2) if not conscious else min(1, u / 0.12) * (1 if u < 0.9 else 0.5)
    gdot(fr, vis, 50, CYAN, 0.6 * vis_a)
    if conscious:
        ig = ease((u - 0.38) / 0.08) * (1 if u < 0.92 else 0.4)
        for p in front + par:
            gdot(fr, p, 46, AMBER, 0.55 * ig)
        for i, p in enumerate(front + par):
            for q in (front + par)[i + 1:]:
                gline(fr, p, q, AMBER, 0.5 * ig, 2)
            gline(fr, vis, p, AMBER, 0.4 * ig, 2)
    # plot
    x0, y0, x1, y1 = 170, 1060, 930, 1300
    line(img, (x0, y1), (x1, y1), GREY, 2); line(img, (x0, y1), (x0, y0), GREY, 2)
    tx = x0 + (x1 - x0) * 0.375
    cv2.line(img, (int(tx), y0), (int(tx), y1), scale(AMBER, 0.6), 2)
    text(img, "≈300 毫秒", tx + 10, y0 + 6, 28, "sans5", AMBER, "lm")
    text(img, "时间 →", x1, y1 + 36, 28, "sans", GREY, "rm")
    def tr(fn, col):
        pts = [(x0 + (x1 - x0) * v, y1 - (y1 - y0) * fn(v)) for v in np.linspace(0, 1, 80)]
        cv2.polylines(img, [np.array(pts, np.int32)], False, col, 4, cv2.LINE_AA)
        cv2.polylines(fr.g, [(np.array(pts) / 2).astype(np.int32)], False, gcol(col, 0.5), 3, cv2.LINE_AA)
    tr(lambda v: 0.35 * math.exp(-((v - 0.2) / 0.08) ** 2), CYAN)
    if conscious:
        tr(lambda v: 0.35 * math.exp(-((v - 0.2) / 0.08) ** 2) + 0.85 * ease((v - 0.36) / 0.08) * (1 - 0.4 * ease((v - 0.8) / 0.2)), AMBER)
    fr.finish_glow()
    text(img, "没看见：视觉区一闪，很快衰减", W / 2, 330, 40, "sansb", CYAN, "mm", c.at(t, "c09", 0.5) * (1 - c.at(t, "c10", 0.4)), 2)
    text(img, "看见：额叶与顶叶一起点亮", W / 2, 330, 40, "sansb", AMBER, "mm", c.at(t, "c10", 0.5) * (1 - c.at(t, "c11", 0.4)), 2)
    text(img, "全局点火", W / 2, 320, 76, "serifh", AMBER, "mm", c.at(t, "c11", 0.6), 3)
    text(img, "global ignition", W / 2, 395, 32, "serif", GREY, "mm", c.at(t, "c11", 0.6))
    if c.at(t, "c12", 0.5) > 0:
        tag(img, "没有小人，只有广播", W / 2, 1420, CYAN, c.at(t, "c12", 0.6), 40)
    text(img, "示意", W - 60, 1000, 26, "sans", GREY, "rm", 0.8)

def cogitate(fr, t, c):
    fr.img[:] = nebula(13, (20, 20, 45), (35, 15, 40), 0.7)
    img = fr.img
    a = c.at(t, "c13", 0.6)
    tag(img, "领先理论之一 · 仍有争议", W / 2, 320, AMBER, a, 40)
    k = c.at(t, "c14", 0.7)
    for i, (nm, en, d, col) in enumerate((("全局神经工作空间", "GNWT", "前额叶 · 广播", CYAN), ("整合信息理论", "IIT", "后部皮层 · 整合", VIOLET))):
        x0 = 80 + i * 470
        card_box(img, x0, 430, x0 + 450, 690, k if i else max(a, k), col)
        text(img, en, x0 + 225, 495, 56, "sansh", col, "mm", k if i else max(a, k))
        text(img, nm, x0 + 225, 570, 34, "sansb", WHITE, "mm", k if i else max(a, k))
        text(img, d, x0 + 225, 630, 30, "sans", GREY, "mm", k if i else max(a, k))
    p = c.at(t, "c15", 0.8)
    if p > 0:
        text(img, "对抗性合作", W / 2, 770, 54, "serifh", WHITE, "mm", p, 2)
        text(img, "预先登记各自预测 → 多个实验室同一方案检验", W / 2, 840, 32, "sans5", GREY, "mm", p)
        for j in range(5):
            x = 170 + j * 185
            gdot(fr, (x, 940), 26, GREEN, 0.5 * p * (0.6 + 0.4 * math.sin(t * 3 + j)))
            circle(img, (x, 940), 12, scale(GREEN, p))
    q = c.at(t, "c16", 0.6)
    if q > 0:
        text(img, "Cogitate Consortium · bioRxiv 2023 → Nature, 2025年4月", W / 2, 1020, 30, "sans5", AMBER, "mm", q)
    r = c.at(t, "c17", 0.6)
    if r > 0:
        for i, col in enumerate((CYAN, VIOLET)):
            x = 305 + i * 470
            text(img, "√ 部分预测得到支持", x, 1120, 32, "sansb", GREEN, "mm", r)
            text(img, "× 关键主张受严重挑战", x, 1175, 32, "sansb", RED, "mm", c.at(t, "c17", 0.6, 1.2))
    text(img, "意识从哪来：尚无定论", W / 2, 1300, 50, "serifb", WHITE, "mm", c.at(t, "c18", 0.6), 2)
    fr.finish_glow()
