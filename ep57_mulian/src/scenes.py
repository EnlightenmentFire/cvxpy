"""All shots. A shot gets its duration and the relative timings of its lines, and draws frames.
Style: night ink-wash + Dunhuang mineral palette; figures only as silhouettes; ghosts only as shadow & firelight."""
import math, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from art import *

GROUND = 1160


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return ease((t - a) / max(b - a, 1e-6))


class Shot:
    zoom = (1.0, 1.06)
    focus = (W / 2, H / 2)
    focus2 = None
    seed = 0

    def __init__(self, dur, lines):
        self.dur, self.lines = dur, lines
        self._bg = None

    def L(self, i):
        return self.lines[min(i, len(self.lines) - 1)]

    def line_by(self, lid):
        for d in self.lines:
            if d["id"] == lid:
                return d
        return self.lines[0]

    def bg(self):
        if self._bg is None:
            self._bg = self.build().astype(np.float32)
        return self._bg

    def build(self):
        return vgrad(H, W, NIGHT_TOP, NIGHT_BOT)

    def dyn(self, img, t):
        pass

    def cam(self, t):
        u = ease(t / max(self.dur, 1e-3))
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * u
        f2 = self.focus2 or self.focus
        return z, self.focus[0] + (f2[0] - self.focus[0]) * u, self.focus[1] + (f2[1] - self.focus[1]) * u

    def over(self, pil, t):
        pass

    def has_subs(self):
        return True


# ---------------------------------------------------------------- shared painters
def night_bg(seed, mountains=True, moon=None, horizon=1150, warm=0.0):
    img = vgrad(H, W, NIGHT_TOP, (0.09 + warm * 0.08, 0.085 + warm * 0.04, 0.13))
    r = rng(seed)
    st = r.random((H, W)) > 0.9993

    ys, xs = np.nonzero(st[:900])
    for y, x in zip(ys, xs):
        img[y, x] += 0.25 + 0.4 * r.random()
    if moon:
        mx, my, mr = moon
        add_glow(img, mx, my, mr * 9, (0.55, 0.55, 0.6), 0.35)
        mm = radial(H, W, mx, my, mr, 0.15)
        img[:] = img * (1 - mm[..., None]) + np.array((0.93, 0.9, 0.8), np.float32) * mm[..., None]
    if mountains:
        ink_mountains(img, [(horizon - 330, 120, 0.45), (horizon - 200, 110, 0.65), (horizon - 60, 90, 0.85)],
                      seed=seed, cols=[(0.13, 0.14, 0.2), (0.08, 0.09, 0.13), (0.04, 0.045, 0.07)])
    m = mist_layer(H, W, seed + 7)
    yy = np.arange(H, dtype=np.float32)[:, None]
    band = np.exp(-((yy - horizon + 80) / 260) ** 2)
    img += (m * band * 0.16)[..., None] * np.array((0.6, 0.65, 0.8), np.float32)
    img[horizon:] = img[horizon:] * 0.55 + np.array((0.02, 0.02, 0.03), np.float32) * 0.45
    return img


def mural_bg(seed, tone=OCHRE):
    img = paper(H, W, tone, seed, dark=0.28)
    n = fbm(H, W, 90, 4, seed + 3)
    img *= (0.82 + 0.18 * n)[..., None]
    # worn malachite / lapis patches like old murals
    for col, s2 in ((MALACHITE, 11), (LAPIS, 17)):
        p = np.clip((fbm(H, W, 300, 3, seed + s2) - 0.62) * 5, 0, 1)
        img = img * (1 - 0.35 * p[..., None]) + np.array(col, np.float32) * 0.35 * p[..., None]
    return img


def embers(img, t, t0, sx, sy, n=60, spread=60, life=2.6, rate=1.0, seed=5, size=14, rise=260):
    if t < t0:
        return
    r = rng(seed)
    births = t0 + r.random(n) * 6.0 / rate
    for i in range(n):
        a = t - births[i]
        if a < 0 or a > life:
            continue
        u = a / life
        x = sx + (r.random() - 0.5) * spread + math.sin(a * 2 + i) * 18 * u
        y = sy - rise * u * (0.7 + 0.6 * ((i * 37) % 10) / 10)
        fl = (1 - u) * (0.6 + 0.4 * math.sin(a * 17 + i))
        add_glow(img, x, y, size * (1 - 0.4 * u), (1.0, 0.55, 0.18), 1.4 * fl)
    # note: consume rng deterministically


def fire_glow(img, x, y, k, size=420):
    add_glow(img, x, y, size, (1.0, 0.42, 0.12), 0.55 * k)
    add_glow(img, x, y, size * 0.35, (1.0, 0.75, 0.4), 0.9 * k)


def rim(img, mask, color, dx, dy, amount=1.0, blur=2):
    e = rim_light(mask, dx, dy, blur)
    img += e[..., None] * np.array(color, np.float32) * amount


# ---------------------------------------------------------------- A. hook
class Hook(Shot):
    """kneeling monk offers the bowl; at the fire cue the rice becomes embers"""
    seed = 11
    BX = None

    def build(self):
        img = night_bg(self.seed, horizon=GROUND)
        m = Mask()
        self.bx, self.by = monk_kneel_offer(m, 360, GROUND + 10, 520, f=1, arm=1.0)
        monk = m.get(0.8)
        m2 = Mask(); hunched(m2, 800, GROUND + 6, 470, f=-1, reach=1.0); gh = m2.get(1.5)
        self.monk, self.ghost = monk, gh
        comp(img, gh, (0.015, 0.012, 0.02), 0.92)
        comp(img, monk, (0.02, 0.022, 0.03))
        rim(img, monk, (0.35, 0.4, 0.55), -3, -2, 0.18, 3)
        mb = Mask(); bowl(mb, self.bx, self.by, 46); self.bmask = mb.get(0.6)
        comp(img, self.bmask, (0.05, 0.04, 0.03))
        return img

    def fire_t(self):
        d = self.line_by("a02") if any(x["id"] == "a02" for x in self.lines) else None
        if d is None:
            return 0.8
        return d["t0"] + 0.66 * (d["t1"] - d["t0"])

    def dyn(self, img, t):
        tf = self.fire_t() if not getattr(self, "aftermath", False) else -10
        bx, by = self.bx, self.by - 12
        if t < tf:
            k = 0.85 + 0.15 * math.sin(t * 3)
            add_glow(img, bx, by, 360, (1.0, 0.85, 0.55), 0.35 * k)
            add_glow(img, bx, by - 6, 90, (1.0, 0.95, 0.8), 0.9 * k)
        else:
            a = t - tf
            flash = math.exp(-a * 2.2)
            fire_glow(img, bx, by, 0.55 + 0.9 * flash + 0.12 * math.sin(a * 11), 520)

            img += (self.ghost_rim() * (0.5 + flash))[..., None] * np.array((1.0, 0.35, 0.1), np.float32)
            embers(img, t, tf, bx, by, n=90, spread=70, life=2.8, seed=7, rise=420)
            # charcoal lumps
            for i in range(7):
                x = bx - 30 + i * 10; y = by - 4 - (i % 3) * 4
                add_glow(img, x, y, 22, (1.0, 0.3, 0.05), 0.8 * (0.6 + 0.4 * math.sin(a * 5 + i)))

    @functools.lru_cache(maxsize=1)
    def ghost_rim(self):
        return rim_light(self.ghost, 6, 0, 3)

    def cam(self, t):
        u = ease(min(t / 6.5, 1))
        z = 1.85 - 0.8 * u
        return z, self.bx + (W / 2 - self.bx) * u, self.by + (H * 0.52 - self.by) * u


class HookReturn(Hook):
    aftermath = True
    seed = 11

    def build(self):
        img = super().build()
        g = img.mean(2, keepdims=True)
        return img * 0.6 + g * 0.4

    def dyn(self, img, t):
        bx, by = self.bx, self.by - 12
        fire_glow(img, bx, by, 0.45 + 0.08 * math.sin(t * 5), 480)
        img += (self.ghost_rim() * 0.4)[..., None] * np.array((1.0, 0.35, 0.1), np.float32)
        embers(img, t, -2.0, bx, by, n=120, spread=60, life=3.2, seed=8, rise=380, rate=0.25)

    def cam(self, t):
        u = ease(t / self.dur)
        return 1.0 + 0.25 * u, W / 2 + (self.bx - W / 2) * u * 0.6, H * 0.52 + (self.by - H * 0.52) * u * 0.6


# ---------------------------------------------------------------- title & text cards
class TextCard(Shot):
    """dark paper with gold dust; subclasses set items: list of (pil_img, x_center, y_center, t_in)"""
    zoom = (1.0, 1.04)
    tone = (0.09, 0.085, 0.08)
    seed = 21

    def build(self):
        img = paper(H, W, self.tone, self.seed, dark=0.35)
        img = img * 0.9 + vgrad(H, W, (0.0, 0.0, 0.0), (0.05, 0.04, 0.03)) * 0.1
        return img

    def dyn(self, img, t):
        r = rng(self.seed)
        for i in range(40):
            x = r.random() * W; y0 = r.random() * H; sp = 8 + r.random() * 20
            y = (y0 - t * sp) % H
            add_glow(img, x, y, 10 + r.random() * 10, GOLD, 0.25 * (0.5 + 0.5 * math.sin(t + i)))

    def items(self):
        return []

    def over(self, pil, t):
        if not hasattr(self, "_items"):
            self._items = self.items()
        for it in self._items:
            im, cx, cy, tin = it[:4]
            a = ramp(t, tin, tin + 0.6)
            paste(pil, im, cx - im.width / 2, cy - im.height / 2 + (1 - a) * 20, a)


class SutraTitle(TextCard):
    def items(self):
        return [(vtext_img(["佛說盂蘭盆經"], font("kai", 120), fill=(240, 214, 160))[0], W / 2, 760, 0.0),
                (text_img("目连救母", font("brush", 96), fill=(235, 225, 205)), W / 2, 1270, 0.4),
                (text_img("经题：西晋月氏三藏竺法护译", font("serif", 36), fill=(190, 180, 160)), W / 2, 1380, 0.8),
                (seal("盂兰", 96), W / 2 + 170, 1110, 1.0)]


class StoryFrame(TextCard):
    def items(self):
        return [(text_img("当故事听", font("brush", 120), fill=(235, 225, 205)), W / 2, 640, 0.0),
                (text_img("↓", font("serif", 80), fill=(200, 170, 120)), W / 2, 820, 0.8),
                (text_img("看清寓意", font("brush", 120), fill=(240, 205, 140)), W / 2, 1000, 1.2),
                (text_img("饿鬼、神通是经中的故事元素\n不作为事实陈述", font("serif", 38), fill=(180, 170, 150)), W / 2, 1230, 2.0)]


QUOTES = {
    "q_feiru": (["非汝一人", "力所奈何。"], "《佛說盂蘭盆經》", "不是你一个人的力量能做到的"),
    "q_rubu": (["欲度父母，", "報乳哺之恩。"], "《佛說盂蘭盆經》", "想度化父母，报答哺乳养育之恩"),
    "q_huotan": (["母得鉢飯，", "便以左手障鉢，", "右手摶飯，", "食未入口，", "化成火炭，", "遂不得食。"], "《佛說盂蘭盆經》", "饭还没入口，就化成了火炭"),
    "q_zuigen": (["汝母罪根深結，", "非汝一人", "力所奈何。"], "《佛說盂蘭盆經》", "你母亲罪根太深，不是你一人之力能救"),
    "q_xiaoshun": (["汝雖孝順，", "聲動天地，", "︙", "亦不能奈何。"], "《佛說盂蘭盆經》", "孝心感天动地，一个人也做不到"),
    "q_shifang": (["當須十方眾僧", "威神之力，", "乃得解脫。"], "《佛說盂蘭盆經》", "要靠十方僧众合力，才能解脱"),
    "q_zizi": (["七月十五日，", "僧自恣時。"], "《佛說盂蘭盆經》", "七月十五日，僧众自恣之时"),
    "q_pen": (["具飯、百味五果，", "︙以著盆中，", "供養十方", "大德眾僧。"], "《佛說盂蘭盆經》", "备好饭食果品放在盆中，供养十方僧众"),
    "q_qishi": (["是佛弟子修孝順者，", "應念念中常憶父母，", "供養乃至七世父母。"], "《佛說盂蘭盆經》", "学佛行孝，念念不忘父母，乃至七世父母"),
}


class QuoteCard(TextCard):
    """vertical quote revealed char by char across the quote line; source + plain-language line"""
    key = None
    zoom = (1.0, 1.035)

    def build(self):
        img = paper(H, W, (0.10, 0.09, 0.085), self.seed + hash(self.key) % 97, dark=0.4)
        add_glow(img, W / 2, 820, 1300, (0.45, 0.32, 0.18), 0.18)
        return img

    def prep(self):
        cols, src, bh = QUOTES[self.key]
        n = max(len(c) for c in cols)
        size = min(118, int(1000 / (n * 1.12)), int(880 / (len(cols) * 1.45)))
        self.vt, self.boxes = vtext_img(cols, font("kai", size), fill=(242, 228, 200))
        self.src = text_img("——" + src, font("serif_sb", 40), fill=(214, 180, 120))
        self.bh = text_img(bh, font("serif", 40), fill=(205, 198, 182))
        self.seal = seal("經", 84)
        q = [d for d in self.lines if d["k"] == "q"]
        self.qt0 = q[0]["t0"] if q else 0.0
        self.qt1 = q[0]["t1"] if q else 1.5
        nq = [d for d in self.lines if d["k"] != "q"]
        self.bt = nq[0]["t0"] if nq else self.qt1 + 0.2
        self.full = self.vt
        # per-char reveal masks are produced by cropping boxes
        self.x0 = W / 2 - self.vt.width / 2
        self.y0 = 780 - self.vt.height / 2

    def over(self, pil, t):
        if not hasattr(self, "vt"):
            self.prep()
        nchar = len(self.boxes)
        span = max(self.qt1 - self.qt0, 0.5)
        prog = (t - self.qt0 + 0.25) / span * nchar
        if prog >= nchar:
            paste(pil, self.vt, self.x0, self.y0, 1.0)
        else:
            for i, (bx0, by0, bx1, by1, ch) in enumerate(self.boxes):
                a = min(max(prog - i, 0), 1)
                if a <= 0:
                    break
                tile = self.vt.crop((bx0 - 14, by0 - 14, bx1 + 30, by1 + 4))
                paste(pil, tile, self.x0 + bx0 - 14, self.y0 + by0 - 14, a)
        a = ramp(t, self.qt0 + 0.3, self.qt0 + 1.0)
        paste(pil, self.src, W / 2 - self.src.width / 2, self.y0 + self.vt.height + 10, a)
        paste(pil, self.seal, self.x0 - 40, self.y0 + self.vt.height - 120, a)
        b = ramp(t, self.bt, self.bt + 0.6)
        paste(pil, self.bh, W / 2 - self.bh.width / 2, self.y0 + self.vt.height + 80, b)


def make_quote(key):
    return type("Q_" + key, (QuoteCard,), {"key": key})


class FinalQuote(QuoteCard):
    key = "q_feiru"
    zoom = (1.0, 1.08)

    def build(self):
        img = night_bg(5, mountains=False, moon=(W / 2, 520, 120), horizon=1500)
        return img

    def prep(self):
        self.vt, self.boxes = vtext_img(["非汝一人", "力所奈何"], font("brush", 190), fill=(246, 236, 214))
        self.src = text_img("——《佛說盂蘭盆經》", font("serif_sb", 42), fill=(214, 180, 120))
        self.bh = text_img("一个人的力量，总有尽头", font("serif", 42), fill=(220, 212, 196))
        self.seal = seal("盂蘭", 96)
        q = [d for d in self.lines if d["k"] == "q"]
        self.qt0, self.qt1 = (q[0]["t0"], q[0]["t1"]) if q else (0, 2)
        self.bt = self.qt1 + 0.4
        self.x0 = W / 2 - self.vt.width / 2
        self.y0 = 900 - self.vt.height / 2


# ---------------------------------------------------------------- concept shots
class LanternTease(Shot):
    seed = 31
    zoom = (1.08, 1.0)

    def build(self):
        img = night_bg(self.seed, moon=(800, 420, 60), horizon=950)
        w = water(H, W, 4, top_y=950)
        img[950:] = img[950:] * 0.35 + w[950:] * 0.65
        return img

    def dyn(self, img, t):
        r = rng(3)
        for i in range(14):
            x = (r.random() * W * 1.3 + t * (18 + 10 * r.random())) % (W * 1.3) - 100
            y = 1050 + r.random() * 700
            s = 10 + (y - 1000) / 26
            lantern(img, x, y, s, 0.8 + 0.2 * math.sin(t * 3 + i))

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = [text_img(s, font("kai", 58), fill=(240, 220, 180)) for s in ("盂兰盆会", "七月十五", "中元节")]
        for i, im in enumerate(self.lab):
            a = ramp(t, 0.5 + i * 1.2, 1.1 + i * 1.2)
            paste(pil, im, 150 + i * 280 - im.width / 2 + 120, 520 + (i % 2) * 90, a * 0.95)


class OneLamp(Shot):
    seed = 41
    zoom = (1.0, 1.12)
    focus = (W / 2, 1000)

    def build(self):
        img = vgrad(H, W, (0.01, 0.012, 0.02), (0.04, 0.04, 0.06))
        m = Mask(); monk_seated(m, W / 2 - 150, 1180, 300); self.m = m.get(1)
        comp(img, self.m, (0.0, 0.0, 0.0))
        return img

    def dyn(self, img, t):
        k = 0.85 + 0.15 * math.sin(t * 7) * math.sin(t * 2.3)
        add_glow(img, W / 2 + 60, 1130, 700, WARM, 0.45 * k)
        add_glow(img, W / 2 + 60, 1130, 60, (1, 0.9, 0.7), 1.0 * k)
        img += (rim_light(self.m, -6, 0, 2) * 0.0)[..., None]

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("一盏灯 · 一个人", font("kai", 60), fill=(230, 210, 170))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 520, ramp(t, 0.6, 1.4) * 0.9)


class TwoDisciples(Shot):
    seed = 51
    zoom = (1.0, 1.07)

    def build(self):
        img = mural_bg(self.seed)
        for cx in (W / 2 - 200, W / 2 + 200):
            halo(img, cx, 690, 120, (0.95, 0.75, 0.35), rays=False, amount=0.35)
        m = Mask(); monk_standing(m, W / 2 - 200, 1240, 640, 0.0); monk_standing(m, W / 2 + 200, 1240, 640, 0.0)
        ms = m.get(1)
        comp(img, ms, (0.34, 0.16, 0.10), 0.92)
        tex = fbm(H, W, 40, 3, 9)
        img -= (ms * (tex - 0.5) * 0.12)[..., None]
        # niche frame
        f = Mask(); f.rect(90, 330, W - 90, 1330); f.rect(120, 360, W - 120, 1300, fill=0)
        comp(img, f.get(1), (0.30, 0.20, 0.12), 0.6)
        return img

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = [text_img("舍利弗\n智慧第一", font("kai", 52), fill=(60, 30, 18), shadow=False),
                        text_img("目犍连\n神通第一", font("kai", 52), fill=(130, 30, 20), shadow=False)]
        for i, im in enumerate(self.lab):
            paste(pil, im, W / 2 + (i * 2 - 1) * 200 - im.width / 2, 1250, ramp(t, 0.5 + i * 0.6, 1.1 + i * 0.6))


class SixPowers(Shot):
    seed = 61
    zoom = (1.0, 1.05)
    NAMES = ["天眼", "天耳", "他心", "宿命", "神足", "漏尽"]

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1500)
        m = Mask(); monk_seated(m, W / 2, 1150, 420); self.m = m.get(1)
        halo(img, W / 2, 800, 150, GOLD, rays=True, amount=0.4)
        comp(img, self.m, (0.03, 0.03, 0.04))
        return img

    def pos(self, i):
        a = -math.pi / 2 + (i - 2.5) * 0.52
        return W / 2 + math.cos(a) * 400, 860 + math.sin(a) * 400 + 120

    def tl(self, i):
        d = self.line_by("b03b")
        if d["id"] != "b03b":
            return 0.5 + i * 0.4
        return d["t0"] + (0.12 + i * 0.13) * (d["t1"] - d["t0"])

    def dyn(self, img, t):
        for i in range(6):
            x, y = self.pos(i)
            k = ramp(t, self.tl(i), self.tl(i) + 0.5)
            add_glow(img, x, y, 240, GOLD, 0.15 + 0.45 * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = [text_img(n, font("kai", 54), fill=(250, 232, 190)) for n in self.NAMES]
            self.title = text_img("六通", font("brush", 110), fill=(240, 210, 150))
        paste(pil, self.title, W / 2 - self.title.width / 2, 300, ramp(t, 0.3, 1.0))
        for i, im in enumerate(self.lab):
            x, y = self.pos(i)
            paste(pil, im, x - im.width / 2, y - im.height / 2, 0.25 + 0.75 * ramp(t, self.tl(i), self.tl(i) + 0.4))


class DaoEye(Shot):
    seed = 71
    zoom = (1.0, 1.3)
    focus = (W / 2, 900)

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1700)
        cl = fbm(H, W, 220, 5, 4)
        img += (np.clip(cl - 0.45, 0, 1) * 0.35)[..., None] * np.array((0.6, 0.62, 0.75), np.float32)
        y, x = np.ogrid[:H, :W]
        e = ((x - W / 2) / 380) ** 2 + ((y - 900) / 170) ** 2 * (1 + 0.0)
        eye = np.clip((1 - e) * 4, 0, 1)
        self.eye = eye
        inner = vgrad(H, W, (0.08, 0.02, 0.02), (0.25, 0.06, 0.03))
        img = img * (1 - eye[..., None]) + inner * eye[..., None]
        img += (np.exp(-((np.sqrt(e) - 1) / 0.05) ** 2) * 0.6)[..., None] * np.array(GOLD, np.float32)
        return img

    def dyn(self, img, t):
        add_glow(img, W / 2, 960, 300, (1.0, 0.3, 0.1), 0.25 + 0.05 * math.sin(t * 2))


class GhostShadow(Shot):
    seed = 81
    zoom = (1.12, 1.0)
    focus = (W / 2, 1050)

    def build(self):
        img = night_bg(self.seed, horizon=GROUND)
        img *= np.array((1.0, 0.85, 0.85), np.float32)
        m = Mask(); hunched(m, W / 2 + 40, GROUND + 4, 560, f=-1, reach=0.2); self.g = m.get(2.0)
        comp(img, self.g, (0.0, 0.0, 0.0), 0.95)
        return img

    def dyn(self, img, t):
        add_glow(img, W / 2 + 260, GROUND - 120, 700, (0.8, 0.22, 0.08), 0.22 + 0.04 * math.sin(t * 1.7))
        img += (rim_light(self.g, 6, 0, 2) * 0.0)[..., None]

    def over(self, pil, t):
        if not hasattr(self, "q"):
            self.q, _ = vtext_img(["不見飲食，", "皮骨連立。"], font("kai", 62), fill=(225, 200, 170))
        paste(pil, self.q, 90, 330, ramp(t, 0.8, 1.6) * 0.9)


class BowlGo(Shot):
    seed = 91

    def build(self):
        return night_bg(self.seed, horizon=GROUND)

    def dyn(self, img, t):
        x = 140 + t * 55
        m = Mask(); bx, by = monk_walk(m, x, GROUND + 4, 500, t * 3.2, f=1)
        mm = m.get(0.8)
        comp(img, mm, (0.02, 0.02, 0.03))
        add_glow(img, bx, by - 10, 260, (1.0, 0.85, 0.55), 0.3)
        add_glow(img, bx, by - 14, 50, (1.0, 0.95, 0.8), 0.7)

    def cam(self, t):
        return 1.05, min(max(140 + t * 55 + 120, W / 2 - 30), W / 2 + 30), H / 2


class BowlFire(Shot):
    """close-up: rice -> fire -> charcoal"""
    seed = 101
    zoom = (1.0, 1.08)

    def build(self):
        img = vgrad(H, W, (0.02, 0.015, 0.02), (0.06, 0.04, 0.04))
        m = Mask(); bowl(m, W / 2, 1000, 300); self.bm = m.get(1)
        comp(img, self.bm, (0.06, 0.045, 0.035))
        img += (rim_light(self.bm, 0, -5, 2) * 0.25)[..., None] * np.array(GOLD, np.float32)
        return img

    def dyn(self, img, t):
        tf = 1.2 if self.lines[0]["id"] != "b10" else self.lines[0]["t0"] + 0.62 * (self.lines[0]["t1"] - self.lines[0]["t0"])
        if t < tf:
            add_glow(img, W / 2, 960, 700, (1, 0.9, 0.6), 0.35)
            for i in range(26):
                add_glow(img, W / 2 - 220 + (i * 53) % 440, 950 + (i * 31) % 50, 36, (1, 0.96, 0.85), 0.5)
        else:
            a = t - tf
            fl = math.exp(-a * 1.8)
            fire_glow(img, W / 2, 940, 0.6 + 1.0 * fl + 0.1 * math.sin(a * 13), 900)
            for i in range(26):
                x = W / 2 - 220 + (i * 53) % 440; y = 950 + (i * 31) % 50
                add_glow(img, x, y, 46, (1, 0.3, 0.05), 0.9 * (0.5 + 0.5 * math.sin(a * 4 + i)))
            embers(img, t, tf, W / 2, 930, n=140, spread=420, life=3.0, seed=9, rise=650, size=20)


class HandGuard(BowlFire):
    """the guarding left hand: an ink arc wrapping the bowl"""
    seed = 103

    def build(self):
        img = super().build()
        m = Mask(); m.line(bez((W / 2 - 360, 1150), (W / 2 - 520, 860), (W / 2 - 160, 720), 30), 46)
        self.arc = m.get(1.2)
        return img

    def dyn(self, img, t):
        fire_glow(img, W / 2, 940, 0.45 + 0.06 * math.sin(t * 9), 820)
        k = ramp(t, 0.3, 1.6)
        comp(img, self.arc * k, (0.01, 0.01, 0.01), 0.95)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("左手障钵", font("brush", 96), fill=(240, 205, 150))
            self.lab2 = text_img("护住一口饭 · 也护住一颗只顾自己的心", font("kai", 46), fill=(225, 215, 195))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 400, ramp(t, 0.5, 1.2))
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 1260, ramp(t, 2.5, 3.2))


class Grasp(Shot):
    """grains in a tightening ring spill outwards"""
    seed = 111

    def build(self):
        return vgrad(H, W, (0.02, 0.02, 0.03), (0.05, 0.04, 0.05))

    def dyn(self, img, t):
        r = rng(5)
        u = ease(t / self.dur)
        R = 330 * (1 - 0.55 * u)
        for i in range(160):
            a = r.random() * 2 * math.pi
            rr = math.sqrt(r.random()) * 330
            esc = r.random() < u * 0.9
            if esc:
                d = rr + (t * 90 * (0.5 + r.random()))
                y = 900 + math.sin(a) * d + (t ** 2) * 25
            else:
                d = rr * R / 330
                y = 900 + math.sin(a) * d
            x = W / 2 + math.cos(a) * d
            add_glow(img, x, y, 22, (1, 0.9, 0.65) if not esc else (0.7, 0.55, 0.4), 0.7 if not esc else 0.35)
        ring = Mask(); ring.d.ellipse([(W / 2 - R - 30) * 2, (900 - R - 30) * 2, (W / 2 + R + 30) * 2, (900 + R + 30) * 2],
                                      outline=255, width=int(18 * 2))
        comp(img, ring.get(2), (0.55, 0.12, 0.08), 0.8)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("越抓得紧 · 越吃不到", font("kai", 64), fill=(235, 220, 190))
            self.lab2 = text_img("苦，往往不在外面缺什么，\n而在心里放不下", font("kai", 52), fill=(240, 205, 150))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 380, ramp(t, 0.5, 1.2))
        d = self.line_by("b14")
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 1290, ramp(t, d["t0"], d["t0"] + 0.6) if d["id"] == "b14" else 0)


class RunBack(Shot):
    seed = 121

    def build(self):
        img = night_bg(self.seed, horizon=GROUND)
        halo(img, W - 200, GROUND - 120, 90, GOLD, rays=True, amount=0.5)
        return img

    def dyn(self, img, t):
        x = 120 + t * 70
        m = Mask(); monk_walk(m, x, GROUND + 4, 330, t * 7.5, f=1)
        comp(img, m.get(0.8), (0.02, 0.02, 0.03))

    def cam(self, t):
        return 1.0 + 0.04 * t / self.dur, W / 2, H / 2


class BuddhaLight(Shot):
    """aniconic: empty lotus seat in a great halo"""
    seed = 131
    zoom = (1.15, 1.0)
    focus = (W / 2, 880)

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1600, warm=0.4)
        halo(img, W / 2, 800, 300, GOLD, rays=True, amount=0.75)
        m = Mask(); lotus_mask(m, W / 2, 1120, 420, 11); lm = m.get(1)
        comp(img, lm, (0.55, 0.32, 0.18), 0.9)
        img += (rim_light(lm, 0, 6, 2) * 0.6)[..., None] * np.array(GOLD, np.float32)
        return img

    def dyn(self, img, t):
        add_glow(img, W / 2, 800, 900, (1, 0.85, 0.5), 0.12 + 0.03 * math.sin(t))


class OneVsMany(Shot):
    seed = 141
    zoom = (1.0, 1.0)

    def build(self):
        return vgrad(H, W, (0.01, 0.012, 0.02), (0.04, 0.04, 0.06))

    def dyn(self, img, t):
        u = t / self.dur
        k = 0.7 + 0.1 * math.sin(t * 6)
        cx, cy = W / 2, 900
        add_glow(img, cx, cy, 380, WARM, 0.5 * k * (1 - 0.3 * u))
        add_glow(img, cx, cy, 50, (1, 0.9, 0.7), k)
        n = int(ramp(t, self.dur * 0.55, self.dur * 0.95) * 36)
        for i in range(n):
            a = i * 2.39996
            rr = 120 + 18 * math.sqrt(i) * 10
            add_glow(img, cx + math.cos(a) * rr * 0.9, cy + math.sin(a) * rr * 0.9, 150, WARM, 0.35)
            add_glow(img, cx + math.cos(a) * rr * 0.9, cy + math.sin(a) * rr * 0.9, 26, (1, 0.9, 0.7), 0.8)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("一个人的力量，再大也有尽头", font("kai", 56), fill=(235, 220, 190))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 400, ramp(t, 0.8, 1.6))


class ManyLamps(Shot):
    """assembly of monks with lamps: 僧伽 = 众"""
    seed = 151
    zoom = (1.08, 1.0)
    focus = (W / 2, 1050)

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1500, warm=0.3)
        m = Mask()
        self.lamps = []
        for row in range(5):
            s = 120 + row * 38
            y = 760 + row * 120
            n = 9 - row
            for j in range(n):
                x = W / 2 + (j - (n - 1) / 2) * (W / (n + 0.5))
                monk_seated(m, x, y, s)
                self.lamps.append((x + s * 0.35, y - s * 0.12, s))
        self.mm = m.get(1)
        comp(img, self.mm, (0.025, 0.022, 0.03))
        return img

    def dyn(self, img, t):
        for i, (x, y, s) in enumerate(self.lamps):
            k = ramp(t, 0.2 + i * 0.05, 0.8 + i * 0.05) * (0.85 + 0.15 * math.sin(t * 5 + i))
            add_glow(img, x, y, s * 1.6, WARM, 0.35 * k)
            add_glow(img, x, y, s * 0.18, (1, 0.9, 0.7), 0.9 * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("僧伽 saṅgha", font("kai", 66), fill=(240, 210, 150))
            self.lab2 = text_img("＝ 众 · 和合的一群人", font("kai", 56), fill=(230, 220, 200))
        a = ramp(t, 1.0, 1.7) if any(d["id"] == "c11b" for d in self.lines) else 0
        d = self.line_by("c11b")
        if d["id"] == "c11b":
            a = ramp(t, d["t0"], d["t0"] + 0.6)
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 340, a)
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 450, a)


class OpenHand(Shot):
    """one bowl's grains flowing out to a ring of bowls"""
    seed = 161
    final = False

    def build(self):
        img = vgrad(H, W, (0.02, 0.02, 0.03), (0.06, 0.05, 0.05))
        m = Mask(); bowl(m, W / 2, 900, 110)
        self.ring = []
        for i in range(10):
            a = i / 10 * 2 * math.pi - math.pi / 2
            x, y = W / 2 + math.cos(a) * 380, 900 + math.sin(a) * 380
            bowl(m, x, y, 48); self.ring.append((x, y))
        self.bm = m.get(1)
        comp(img, self.bm, (0.10, 0.075, 0.055))
        img += (rim_light(self.bm, 0, -4, 2) * 0.4)[..., None] * np.array(GOLD, np.float32)
        return img

    def dyn(self, img, t):
        u = 1.0 if self.final else ramp(t, self.dur * 0.35, self.dur)
        add_glow(img, W / 2, 880, 260, WARM, 0.5)
        for i, (x, y) in enumerate(self.ring):
            for k in range(5):
                p = ((t * 0.45 + k / 5 + i * 0.13) % 1.0)
                if u <= 0:
                    break
                px, py = W / 2 + (x - W / 2) * p, 880 + (y - 880) * p - math.sin(p * math.pi) * 60
                add_glow(img, px, py, 20, (1, 0.9, 0.65), 0.7 * u)
            add_glow(img, x, y - 14, 120, WARM, 0.45 * u)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("把抓紧的手，换成打开的手", font("kai", 56), fill=(240, 220, 185))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 1360 - 60, ramp(t, 1.0, 1.8))


class ShareBowl(OpenHand):
    final = True

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("苦，起于护钵；\n解脱，在于分饭", font("brush", 84), fill=(240, 210, 150))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 300, ramp(t, 0.6, 1.4))


class MoonRise(Shot):
    seed = 171
    zoom = (1.0, 1.05)

    def build(self):
        return night_bg(self.seed, horizon=1250)

    def dyn(self, img, t):
        y = 900 - 260 * ease(t / self.dur)
        add_glow(img, W / 2, y, 900, (0.6, 0.62, 0.7), 0.3)
        add_glow(img, W / 2, y, 220, (1.0, 0.97, 0.88), 1.1)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("七月十五", font("brush", 130), fill=(240, 225, 195))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 1300, ramp(t, 0.4, 1.2))


class RainRetreat(Shot):
    seed = 181
    zoom = (1.0, 1.06)

    def build(self):
        img = night_bg(self.seed, horizon=1250)
        img = img * 0.8 + 0.06
        m = Mask(); hall(m, W / 2, 1250, 900, 420, tiers=1)
        hm = m.get(1)
        comp(img, hm, (0.04, 0.045, 0.06))
        m2 = Mask()
        for j in range(5):
            monk_seated(m2, W / 2 - 300 + j * 150, 1235, 150)
        self.mm = m2.get(1)
        add_glow(img, W / 2, 1150, 900, WARM, 0.18)
        comp(img, self.mm, (0.01, 0.01, 0.015))
        return img

    def dyn(self, img, t):
        r = rng(2)
        for i in range(260):
            x = r.random() * W; sp = 1400 + 500 * r.random(); y = (r.random() * H + t * sp) % H
            y0, y1 = int(y), int(min(H, y + 34))
            xi = int(x)
            if 0 <= xi < W:
                img[y0:y1, xi] += 0.10

    def over(self, pil, t):
        if not hasattr(self, "bar"):
            self.bar = text_img("四月十五 结夏  ━━━━━━  七月十五 解夏", font("kai", 46), fill=(230, 215, 185))
            self.lab = text_img("雨安居", font("brush", 110), fill=(235, 215, 175))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 300, ramp(t, 0.4, 1.0))
        d = self.line_by("d04b")
        if d["id"] == "d04b":
            paste(pil, self.bar, W / 2 - self.bar.width / 2, 1330, ramp(t, d["t0"], d["t0"] + 0.6))


class MoonCircle(Shot):
    """monks in a circle under the full moon, lamp in the centre"""
    seed = 191
    zoom = (1.0, 1.07)
    focus = (W / 2, 1000)
    label = ("自恣", "pavāraṇā · 邀请")
    progressive = False

    def build(self):
        img = night_bg(self.seed, mountains=True, moon=(W / 2, 420, 110), horizon=1000)
        m = Mask()
        self.pos = []
        for i in range(14):
            a = i / 14 * 2 * math.pi
            x = W / 2 + math.cos(a) * 380; y = 1150 + math.sin(a) * 150
            s = 150 + (y - 1000) * 0.35
            self.pos.append((x, y, s, a))
        for x, y, s, a in sorted(self.pos, key=lambda p: p[1]):
            monk_seated(m, x, y, s)
        self.mm = m.get(1)
        comp(img, self.mm, (0.02, 0.02, 0.03))
        img += (rim_light(self.mm, 0, 6, 2) * 0.35)[..., None] * np.array((0.7, 0.72, 0.85), np.float32)
        return img

    def dyn(self, img, t):
        add_glow(img, W / 2, 1130, 520, WARM, 0.35 + 0.04 * math.sin(t * 4))
        add_glow(img, W / 2, 1130, 50, (1, 0.9, 0.7), 1.0)
        if self.progressive:
            for i, (x, y, s, a) in enumerate(self.pos):
                k = ramp(t, 0.5 + i * 0.35, 1.0 + i * 0.35)
                add_glow(img, x, y - s * 0.9, s * 1.4, GOLD, 0.35 * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img(self.label[0], font("brush", 120), fill=(240, 220, 180))
            self.lab2 = text_img(self.label[1], font("kai", 54), fill=(225, 210, 180))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 610, ramp(t, 0.4, 1.1))
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 760, ramp(t, 1.0, 1.7))


class MoonCircle2(MoonCircle):
    progressive = True
    label = ("先清净", "再合力")


class Basin(Shot):
    seed = 201
    zoom = (1.0, 1.08)

    def build(self):
        img = mural_bg(self.seed, (0.55, 0.40, 0.25)) * 0.55
        m = Mask()
        m.poly(bez((W / 2 - 330, 950), (W / 2, 1320), (W / 2 + 330, 950), 24)); m.ell(W / 2, 950, 330, 60)
        bm = m.get(1)
        comp(img, bm, (0.36, 0.17, 0.10))
        f = Mask()
        cols = [CINNABAR, (0.85, 0.6, 0.2), MALACHITE, (0.75, 0.3, 0.35), (0.9, 0.75, 0.3)]
        for i in range(5):
            mm = Mask(); mm.ell(W / 2 - 200 + i * 100, 900 - (i % 2) * 40, 62, 58)
            comp(img, mm.get(1), cols[i], 0.95)
        img += (rim_light(bm, 0, -5, 2) * 0.5)[..., None] * np.array(GOLD, np.float32)
        return img

    def dyn(self, img, t):
        for i in range(6):
            p = (t * 0.25 + i / 6) % 1
            add_glow(img, W / 2 - 150 + i * 60 + math.sin(t + i) * 20, 840 - p * 380, 120, (0.9, 0.85, 0.8), 0.12 * math.sin(p * math.pi))

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("百味五果 · 以著盆中", font("kai", 62), fill=(245, 225, 190))
            self.lab2 = text_img("为七世父母及现在父母", font("kai", 50), fill=(235, 220, 195))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 380, ramp(t, 0.5, 1.2))
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 1300, ramp(t, 1.5, 2.2))


class MotherFreed(GhostShadow):
    seed = 81
    zoom = (1.0, 1.05)

    def build(self):
        img = super().build()
        return img

    def dyn(self, img, t):
        u = ease(t / self.dur)
        add_glow(img, W / 2 + 40, GROUND - 300, 900, (1, 0.85, 0.55), 0.35 * u)
        r = rng(3)
        ys, xs = np.nonzero(self.g[::12, ::12] > 0.5)
        for i in range(0, len(ys), 2):
            p = (u * 1.2 - r.random() * 0.5)
            if p <= 0:
                continue
            x = xs[i] * 12 + math.sin(t + i) * 30 * p
            y = ys[i] * 12 - p * 600
            add_glow(img, x, y, 26, (1, 0.9, 0.65), 0.7 * max(0, 1 - p))
        img[:] = img + (self.g * u * 0.0)[..., None]

    def over(self, pil, t):
        pass


class SevenGen(Shot):
    seed = 211
    zoom = (1.0, 1.06)

    def build(self):
        img = night_bg(self.seed, horizon=1000)
        return img

    def dyn(self, img, t):
        for i in range(8):
            k = ramp(t, 0.3 + i * 0.35, 0.8 + i * 0.35)
            y = 1500 - i * 90 - i * i * 4
            x = W / 2 + math.sin(i * 0.9) * (180 - i * 18)
            s = 46 - i * 4.5
            add_glow(img, x, y, s * 8, WARM, 0.35 * k)
            add_glow(img, x, y, s, (1, 0.92, 0.75), 1.0 * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("现在父母 → 七世父母", font("kai", 58), fill=(240, 220, 185))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 400, ramp(t, 1.0, 1.7))


class Critique(TextCard):
    seed = 221

    def items(self):
        q, _ = vtext_img(["身體髮膚，", "受之父母，", "不敢毀傷，", "孝之始也。"], font("kai", 86), fill=(238, 224, 196))
        it = [(q, W / 2 + 140, 760, 0.3),
              (text_img("——《孝經·開宗明義章》", font("serif_sb", 38), fill=(214, 180, 120)), W / 2 + 120, 1230, 0.8)]
        m = Mask(); monk_standing(m, 0, 0, 1, 0)
        d = self.line_by("e06")
        tt = d["t0"] if d["id"] == "e06" else 3.0
        it.append((text_img("出家人也讲孝\n孝及七世父母", font("brush", 70), fill=(240, 205, 150)), W / 2 - 260, 760, tt))
        return it


class Bianwen(Shot):
    """yellowed Dunhuang manuscript (schematic), title only legible"""
    seed = 231
    zoom = (1.0, 1.08)

    def build(self):
        img = vgrad(H, W, (0.04, 0.035, 0.03), (0.08, 0.06, 0.05))
        sc = paper(H, W, (0.78, 0.66, 0.45), self.seed, dark=0.35)
        m = Mask(); m.rect(120, 330, W - 120, 1330); mm = m.get(3)
        img = img * (1 - mm[..., None]) + sc * mm[..., None]
        r = rng(4)
        L = Mask()
        for c in range(13):
            x = W - 230 - c * 62
            y = 420 + r.random() * 30
            while y < 1250:
                h = 14 + r.random() * 22
                L.rect(x - 7 + r.random() * 4, y, x + 7, y + h)
                y += h + 10 + r.random() * 12
        comp(img, L.get(0.8) * mm, (0.20, 0.13, 0.08), 0.55)
        # worn edges
        n = fbm(H, W, 70, 3, 8)
        img *= (1 - 0.25 * np.clip((n - 0.6) * 4, 0, 1) * mm)[..., None]
        return img

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.t1, _ = vtext_img(["大目乾連冥間救母變文"], font("kai", 66), fill=(70, 30, 15), shadow=False)
            self.lab = text_img("敦煌写本 · 示意", font("serif", 36), fill=(200, 185, 160))
            self.lab2 = text_img("青提夫人", font("brush", 96), fill=(240, 210, 160))
        paste(pil, self.t1, W - 200 - self.t1.width / 2 + 20, 360, ramp(t, 0.3, 1.0))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 1350, ramp(t, 0.5, 1.2))
        d = self.line_by("e08b")
        if d["id"] == "e08b":
            paste(pil, self.lab2, 170, 1150, ramp(t, d["t0"] + 0.8, d["t0"] + 1.4))


class SongStage(Shot):
    seed = 241
    zoom = (1.06, 1.0)
    focus = (W / 2, 1000)

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1400, warm=0.5)
        m = Mask()
        m.rect(160, 900, W - 160, 1000)                       # stage floor
        m.rect(170, 560, 200, 900); m.rect(W - 200, 560, W - 170, 900)
        roof(m, W / 2, 580, 860, 170, 0.25)
        for i in range(22):
            m.ell(80 + i * 45 + (i % 2) * 20, 1230 + (i % 3) * 40, 26, 32)
            m.ell(80 + i * 45 + (i % 2) * 20, 1300 + (i % 3) * 40, 40, 50)
        sm = m.get(1)
        add_glow(img, W / 2, 800, 900, WARM, 0.35)
        comp(img, sm, (0.02, 0.018, 0.02))
        f = Mask(); monk_standing(f, W / 2 - 120, 900, 300, 0.05); hunched(f, W / 2 + 150, 900, 260, f=-1, reach=0.5)
        comp(img, f.get(1), (0.05, 0.03, 0.03))
        self.lamps = [(260, 640), (W - 260, 640), (W / 2, 610)]
        return img

    def dyn(self, img, t):
        for i, (x, y) in enumerate(self.lamps):
            k = 0.85 + 0.15 * math.sin(t * 5 + i)
            add_glow(img, x, y, 160, (1, 0.5, 0.2), 0.6 * k)
            add_glow(img, x, y, 36, (1, 0.85, 0.6), 1.0 * k)

    def over(self, pil, t):
        if not hasattr(self, "q"):
            self.q = text_img("構肆樂人，自過七夕，\n便般目連救母雜劇……觀者增倍。", font("kai", 50), fill=(240, 226, 200), spacing=18)
            self.src = text_img("——孟元老《東京夢華錄》卷八", font("serif_sb", 36), fill=(214, 180, 120))
        paste(pil, self.q, W / 2 - self.q.width / 2, 170, ramp(t, 0.6, 1.3))
        paste(pil, self.src, W / 2 - self.src.width / 2, 170 + self.q.height - 10, ramp(t, 1.0, 1.6))


class Bonds(Shot):
    seed = 251

    def build(self):
        return vgrad(H, W, (0.02, 0.025, 0.04), (0.05, 0.05, 0.07))

    def dyn(self, img, t):
        u = ease(t / self.dur)
        a = (W / 2 - 250, 960); b = (W / 2 + 250, 900)
        add_glow(img, *a, 300, WARM, 0.55)
        add_glow(img, *a, 50, (1, 0.9, 0.7), 1.0)
        kb = 1 - 0.65 * u
        add_glow(img, *b, 300, (0.7, 0.75, 1.0), 0.45 * kb)
        add_glow(img, *b, 46, (0.9, 0.92, 1.0), 0.9 * kb)
        for i in range(60):
            p = i / 59
            x = a[0] + (b[0] - a[0]) * p; y = a[1] + (b[1] - a[1]) * p - math.sin(p * math.pi) * 70
            add_glow(img, x, y, 16, (1, 0.85, 0.6), 0.35 + 0.15 * math.sin(t * 2 - p * 8))

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("持续联结\nContinuing Bonds", font("kai", 62), fill=(240, 220, 185))
            self.lab2 = text_img("Klass, Silverman & Nickman 编，1996", font("serif", 34), fill=(190, 182, 168))
            self.tag = text_img("类比 · 印照 · 不是证明", font("serif_sb", 44), fill=(250, 200, 120))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 340, ramp(t, 0.5, 1.2))
        paste(pil, self.lab2, W / 2 - self.lab2.width / 2, 560, ramp(t, 1.2, 1.8))
        d = self.line_by("e11")
        if d["id"] == "e11":
            paste(pil, self.tag, W / 2 - self.tag.width / 2, 1240, ramp(t, d["t0"] + 1.0, d["t0"] + 1.6))


class MapRoute(Shot):
    """schematic route, no borders"""
    seed = 261
    zoom = (1.0, 1.04)
    NODES = [("天竺", 230, 1250), ("西域", 360, 760), ("长安", 680, 820), ("建康", 900, 1080)]

    def build(self):
        img = paper(H, W, (0.70, 0.60, 0.44), self.seed, dark=0.35) * 0.85
        return img

    def dyn(self, img, t):
        u = ramp(t, 0.3, self.dur * 0.85)
        pts = []
        for (n0, x0, y0), (n1, x1, y1) in zip(self.NODES, self.NODES[1:]):
            for k in range(30):
                p = k / 30
                pts.append((x0 + (x1 - x0) * p, y0 + (y1 - y0) * p - math.sin(p * math.pi) * 60))
        npts = int(len(pts) * u)
        for i, (x, y) in enumerate(pts[:npts]):
            if i % 3 == 0:
                add_glow(img, x, y, 22, (-0.5, -0.35, -0.25), 0.9)
        for i, (nm, x, y) in enumerate(self.NODES):
            add_glow(img, x, y, 70, (-0.4, -0.5, -0.5), 0.9 * ramp(u, i / 4, i / 4 + 0.1))

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = [text_img(n, font("kai", 54), fill=(80, 30, 15), shadow=False) for n, _, _ in self.NODES]
            self.tag = text_img("示意图 · 不表示疆界", font("serif", 34), fill=(90, 60, 40), shadow=False)
            self.ttl = text_img("佛法东传  盂兰盆入华", font("brush", 76), fill=(90, 30, 15), shadow=False)
        u = ramp(t, 0.3, self.dur * 0.85)
        for i, (im, (nm, x, y)) in enumerate(zip(self.lab, self.NODES)):
            paste(pil, im, x - im.width / 2, y + 30, ramp(u, i / 4, i / 4 + 0.1))
        paste(pil, self.tag, W - self.tag.width - 60, 1420, 1.0)
        paste(pil, self.ttl, W / 2 - self.ttl.width / 2, 380, ramp(t, 0.2, 0.9))


class TempleSouth(Shot):
    seed = 271
    zoom = (1.12, 1.0)
    focus = (W / 2, 900)

    def build(self):
        img = night_bg(self.seed, horizon=1200, warm=0.1)
        img = img * 0.7 + np.array((0.12, 0.13, 0.16), np.float32) * 0.3
        m = Mask(); pagoda(m, W / 2 + 170, 1220, 360, 860, 7); hall(m, W / 2 - 230, 1230, 460, 260)
        pm = m.get(1)
        comp(img, pm, (0.05, 0.055, 0.07))
        mist = mist_layer(H, W, 9, 300)
        yy = np.arange(H, dtype=np.float32)[:, None]
        img += (mist * np.exp(-((yy - 1150) / 200) ** 2) * 0.25)[..., None]
        return img

    def dyn(self, img, t):
        for x, y in ((W / 2 - 300, 1150), (W / 2 - 160, 1150)):
            add_glow(img, x, y, 90, WARM, 0.6)
        r = rng(6)
        for i in range(160):
            x = r.random() * W; y = (r.random() * H + t * (900 + 300 * r.random())) % H
            xi, y0 = int(x), int(y)
            img[y0:y0 + 26, xi] += 0.07

    def over(self, pil, t):
        if not hasattr(self, "q"):
            self.q, _ = vtext_img(["帝幸同泰寺", "設盂蘭盆齋"], font("kai", 72), fill=(240, 226, 200))
            self.src = text_img("——志磐《佛祖統紀》卷三十七（南宋）", font("serif_sb", 36), fill=(214, 180, 120))
            self.yr = text_img("梁武帝 大同四年 · 公元538年", font("kai", 52), fill=(235, 220, 190))
            self.note = text_img("七百多年后的追记", font("serif", 38), fill=(200, 190, 170))
        paste(pil, self.q, 110, 300, ramp(t, 0.4, 1.0))
        paste(pil, self.yr, W / 2 - self.yr.width / 2, 1290, ramp(t, 1.0, 1.6))
        paste(pil, self.src, W / 2 - self.src.width / 2, 1380, ramp(t, 1.4, 2.0))
        d = self.line_by("f03")
        if d["id"] == "f03":
            paste(pil, self.note, W / 2 - self.note.width / 2, 1450 - 20, 0)


class Jingchu(TextCard):
    seed = 281

    def items(self):
        q, _ = vtext_img(["七月十五日，", "僧尼道俗", "悉營盆供。"], font("kai", 100), fill=(238, 224, 196))
        return [(q, W / 2, 780, 0.2),
                (text_img("——宗懍《荊楚歲時記》（南朝梁）", font("serif_sb", 38), fill=(214, 180, 120)), W / 2, 1260, 0.8),
                (text_img("出家人、在家人，都备盆供养", font("serif", 40), fill=(205, 198, 182)), W / 2, 1340, 1.4)]


class TangPalace(Shot):
    seed = 291
    zoom = (1.0, 1.07)

    def build(self):
        img = night_bg(self.seed, horizon=1250, warm=0.5)
        m = Mask(); hall(m, W / 2, 1250, 1000, 380, tiers=2); hall(m, 140, 1260, 360, 200); hall(m, W - 140, 1260, 360, 200)
        comp(img, m.get(1), (0.04, 0.03, 0.035))
        add_glow(img, W / 2, 1000, 1200, (1, 0.6, 0.3), 0.18)
        return img

    def dyn(self, img, t):
        r = rng(8)
        for i in range(30):
            x = 120 + i * 29 + r.random() * 10; y = 1080 + (i % 3) * 30
            k = 0.8 + 0.2 * math.sin(t * 4 + i)
            add_glow(img, x, y, 60, (1, 0.45, 0.15), 0.6 * k)
            add_glow(img, x, y, 16, (1, 0.85, 0.5), 0.9 * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = text_img("唐  宫廷与民间", font("brush", 96), fill=(240, 210, 160))
        paste(pil, self.lab, W / 2 - self.lab.width / 2, 380, ramp(t, 0.3, 1.0))


class Sanyuan(Shot):
    seed = 301
    zoom = (1.0, 1.04)
    ITEMS = [("上元", "正月十五", "天官"), ("中元", "七月十五", "地官"), ("下元", "十月十五", "水官")]

    def build(self):
        img = night_bg(self.seed, mountains=True, horizon=1500)
        return img

    def dyn(self, img, t):
        d8 = self.line_by("f08")
        hi = ramp(t, d8["t0"] + 2.0, d8["t0"] + 3.0) if d8["id"] == "f08" else 0
        for i in range(3):
            x = W / 2 + (i - 1) * 310; y = 860
            k = ramp(t, 0.3 + i * 0.5, 0.9 + i * 0.5)
            col = (0.85, 0.88, 1.0) if i != 1 else (1, 0.9, 0.7)
            add_glow(img, x, y, 360, col, (0.22 + (0.35 * hi if i == 1 else -0.1 * hi)) * k)
            add_glow(img, x, y, 120, col, (0.7 + (0.3 * hi if i == 1 else -0.3 * hi)) * k)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.lab = [text_img(f"{a}\n{b}", font("kai", 50), fill=(240, 226, 200)) for a, b, c in self.ITEMS]
            self.off = [text_img(c, font("brush", 76), fill=(240, 205, 150)) for a, b, c in self.ITEMS]
            self.say = text_img("天官赐福 · 地官赦罪 · 水官解厄", font("kai", 50), fill=(235, 215, 180))
            self.src = text_img("晚出的定型说法（明《续道藏》所收三元经）", font("serif", 32), fill=(190, 180, 160))
            self.ttl = text_img("三元", font("brush", 120), fill=(240, 220, 180))
        paste(pil, self.ttl, W / 2 - self.ttl.width / 2, 330, ramp(t, 0.2, 0.8))
        for i in range(3):
            x = W / 2 + (i - 1) * 310
            paste(pil, self.lab[i], x - self.lab[i].width / 2, 1010, ramp(t, 0.3 + i * 0.5, 0.9 + i * 0.5))
        d7 = self.line_by("f07")
        if d7["id"] == "f07":
            for i in range(3):
                x = W / 2 + (i - 1) * 310
                paste(pil, self.off[i], x - self.off[i].width / 2, 600, ramp(t, d7["t0"] + 3.5 + i * 0.3, d7["t0"] + 4.1 + i * 0.3))
        d8 = self.line_by("f08")
        if d8["id"] == "f08":
            a = ramp(t, d8["t0"], d8["t0"] + 0.6)
            paste(pil, self.say, W / 2 - self.say.width / 2, 1190, a)
            paste(pil, self.src, W / 2 - self.src.width / 2, 1270, a)


class Merge(Shot):
    """two streams of light merging: 佛 盂兰盆 (gold) + 道 中元 (blue)"""
    seed = 311

    def build(self):
        return night_bg(self.seed, horizon=1700)

    def dyn(self, img, t):
        for i in range(70):
            p = ((t * 0.12 + i / 70) % 1.0)
            for side, col in ((-1, (1, 0.8, 0.45)), (1, (0.55, 0.7, 1.0))):
                if p < 0.5:
                    x = W / 2 + side * 380 * (1 - p * 2) ** 1.2 + math.sin(i + t) * 10
                else:
                    x = W / 2 + math.sin(i * 1.3 + t) * 60
                    col = (0.9, 0.82, 0.65)
                y = 400 + p * 1100
                add_glow(img, x, y, 70, col, 0.35)
        u = ramp(t, self.dur * 0.4, self.dur)
        r = rng(4)
        for i in range(int(u * 18)):
            x = W / 2 + (r.random() - 0.5) * 160; y = 1050 + ((r.random() * 500 + t * 40) % 500)
            lantern(img, x, y, 12, 0.9, refl=False)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.a = text_img("佛教 · 盂兰盆", font("kai", 54), fill=(250, 220, 160))
            self.b = text_img("道教 · 中元", font("kai", 54), fill=(190, 210, 250))
            self.c = text_img("七月半", font("brush", 110), fill=(240, 225, 200))
            self.lab = 1
        paste(pil, self.a, 70, 300, ramp(t, 0.3, 0.9))
        paste(pil, self.b, W - 70 - self.b.width, 300, ramp(t, 0.6, 1.2))
        paste(pil, self.c, W / 2 - self.c.width / 2, 1330, ramp(t, self.dur * 0.55, self.dur * 0.55 + 0.7))


class BookCard(TextCard):
    seed = 321

    def items(self):
        d12 = self.line_by("f12")
        t12 = d12["t0"] if d12["id"] == "f12" else 1.0
        d13 = self.line_by("f13")
        t13 = d13["t0"] if d13["id"] == "f13" else 3.0
        return [(text_img("经题：西晋竺法护译", font("kai", 60), fill=(240, 226, 200)), W / 2, 420, 0.0),
                (text_img("《出三藏記集》卷四：列为“失译”", font("kai", 50), fill=(225, 210, 180)), W / 2, 540, t12 + 2.5),
                (text_img("译自印度原典？\n还是在中国编成？", font("brush", 92), fill=(240, 205, 150)), W / 2, 790, t12 + 5.0),
                (text_img("学界至今仍有争论", font("serif_sb", 44), fill=(214, 180, 120)), W / 2, 1000, t12 + 6.0),
                (text_img("Stephen F. Teiser\nThe Ghost Festival in Medieval China\nPrinceton University Press, 1988",
                          font("serif", 40), fill=(225, 220, 205)), W / 2, 1210, t13 + 0.5),
                (text_img("太史文《中国中世纪的鬼节》", font("kai", 46), fill=(214, 180, 120)), W / 2, 1370, t13 + 1.0)]


class TeiserBridge(Shot):
    seed = 331
    zoom = (1.0, 1.04)

    def build(self):
        img = night_bg(self.seed, mountains=False, horizon=1600, warm=0.2)
        m = Mask(); hall(m, 260, 1100, 340, 250); pagoda(m, W - 260, 1110, 230, 560, 5)
        comp(img, m.get(1), (0.03, 0.03, 0.04))
        return img

    def dyn(self, img, t):
        add_glow(img, 260, 1020, 300, WARM, 0.35)
        add_glow(img, W - 260, 900, 300, GOLD, 0.35)
        for i in range(14):
            p = (t * 0.25 + i / 14) % 1
            x = 360 + (W - 720) * p; y = 820 - math.sin(p * math.pi) * 120
            add_glow(img, x, y, 26, (1, 0.9, 0.6), 0.7)
            x2 = W - 360 - (W - 720) * p; y2 = 1180 + math.sin(p * math.pi) * 120
            add_glow(img, x2, y2, 26, (0.8, 0.85, 1.0), 0.7)

    def over(self, pil, t):
        if not hasattr(self, "lab"):
            self.l1 = text_img("家 · 孝道", font("kai", 56), fill=(240, 220, 185))
            self.l2 = text_img("僧团 · 出家", font("kai", 56), fill=(240, 220, 185))
            self.a1 = text_img("供养 →", font("kai", 50), fill=(250, 220, 160))
            self.a2 = text_img("← 回向功德", font("kai", 50), fill=(200, 215, 250))
            self.c = text_img("七月十五  握手", font("brush", 96), fill=(240, 205, 150))
            self.lab = 1
        paste(pil, self.l1, 260 - self.l1.width / 2, 1150, ramp(t, 0.3, 0.9))
        paste(pil, self.l2, W - 260 - self.l2.width / 2, 1150, ramp(t, 0.6, 1.2))
        d = self.line_by("f13c")
        tt = d["t0"] if d["id"] == "f13c" else 1.5
        paste(pil, self.a1, W / 2 - self.a1.width / 2, 640, ramp(t, tt + 1.5, tt + 2.1))
        paste(pil, self.a2, W / 2 - self.a2.width / 2, 1300, ramp(t, tt + 3.5, tt + 4.1))
        d = self.line_by("f13d")
        if d["id"] == "f13d":
            paste(pil, self.c, W / 2 - self.c.width / 2, 340, ramp(t, d["t0"], d["t0"] + 0.7))


class Etymology(TextCard):
    seed = 341

    def items(self):
        d = self.line_by("f14b")
        tb = d["t0"] if d["id"] == "f14b" else 6
        return [(text_img("盂兰盆", font("brush", 170), fill=(240, 215, 160)), W / 2, 420, 0.0),
                (text_img("旧释：梵语“倒悬” → 救倒悬\n（唐 玄应《一切經音義》、宗密《盂蘭盆經疏》）", font("kai", 44), fill=(230, 218, 196)), W / 2, 680, 1.0),
                (text_img("对应梵文词 ullambana：并无实证", font("serif", 42), fill=(205, 195, 178)), W / 2, 860, 4.5),
                (text_img("新说（辛嶋静志）：本义或为“盛饭之钵”", font("kai", 50), fill=(250, 205, 140)), W / 2, 980, 7.0),
                (seal("钵", 110), W / 2, 1200, tb)]

    def dyn(self, img, t):
        super().dyn(img, t)
        d = self.line_by("f14b")
        if d["id"] == "f14b":
            k = ramp(t, d["t0"], d["t0"] + 1.0)
            add_glow(img, W / 2, 1200, 400, WARM, 0.3 * k)


class River(Shot):
    """ending: lanterns accumulate, the river brightens"""
    seed = 351
    people = False

    def build(self):
        img = night_bg(self.seed, moon=(W - 260, 360, 70), horizon=820)
        w = water(H, W, 7, top_y=820)
        img[820:] = img[820:] * 0.3 + w[820:] * 0.7
        if self.people:
            m = Mask()
            for i, (x, s) in enumerate(((200, 330), (330, 250), (760, 300), (880, 220))):
                monk_standing(m, x, 1880, s, 0.02 * (i % 2)) if i % 2 == 0 else monk_seated(m, x, 1880, s * 0.8)
            m.rect(0, 1840, W, H)
            self.pm = m.get(1)
            comp(img, self.pm, (0.01, 0.01, 0.015))
        return img

    def n_lamps(self, t):
        base = getattr(self, "base_lamps", 6)
        return int(base + (90 - base) * ease(t / max(self.dur, 1)))

    def dyn(self, img, t):
        r = rng(11)
        n = self.n_lamps(t)
        u = ease(t / max(self.dur, 1))
        img[820:] += (np.float32(0.05 * u) * np.array((1.0, 0.7, 0.4), np.float32))
        for i in range(n):
            y = 860 + (r.random() ** 0.8) * 1000
            sp = 10 + 14 * r.random()
            x = (r.random() * (W + 300) + t * sp) % (W + 300) - 150
            s = 5 + (y - 840) / 30
            lantern(img, x, y, s, 0.8 + 0.2 * math.sin(t * 3 + i))

    def cam(self, t):
        return 1.0 + 0.05 * t / max(self.dur, 1), W / 2, H / 2 + 60 * t / max(self.dur, 1)


class RiverPeople(River):
    people = True
    seed = 352
    base_lamps = 10

    def n_lamps(self, t):
        return int(10 + 25 * ease(t / max(self.dur, 1)))


# ---------------------------------------------------------------- registry
SHOTS = {
    "hook": Hook, "hook_return": HookReturn, "sutra_title": SutraTitle, "lantern_tease": LanternTease,
    "story_frame": StoryFrame, "one_lamp": OneLamp, "two_disciples": TwoDisciples, "six_powers": SixPowers,
    "dao_eye": DaoEye, "ghost_shadow": GhostShadow, "bowl_go": BowlGo, "bowl_fire": BowlFire,
    "hand_guard": HandGuard, "grasp": Grasp, "run_back": RunBack, "buddha_light": BuddhaLight,
    "one_vs_many": OneVsMany, "many_lamps": ManyLamps, "open_hand": OpenHand, "share_bowl": ShareBowl,
    "moon_rise": MoonRise, "rain_retreat": RainRetreat, "moon_circle": MoonCircle, "moon_circle2": MoonCircle2,
    "basin": Basin, "mother_freed": MotherFreed, "seven_gen": SevenGen, "critique": Critique,
    "bianwen": Bianwen, "song_stage": SongStage, "bonds": Bonds, "map_route": MapRoute,
    "temple_south": TempleSouth, "jingchu": Jingchu, "tang_palace": TangPalace, "sanyuan": Sanyuan,
    "merge": Merge, "book_card": BookCard, "teiser_bridge": TeiserBridge, "etymology": Etymology,
    "final_quote": FinalQuote, "river": River, "river_people": RiverPeople,
}
for k in QUOTES:
    SHOTS[k] = make_quote(k)

SECTIONS = [("a", "开篇"), ("b", "壹 · 一碗饭"), ("c", "贰 · 一句话"), ("d", "叁 · 一个日子"),
            ("e", "肆 · 一份孝"), ("f", "伍 · 一个节日"), ("g", "陆 · 一条河")]
