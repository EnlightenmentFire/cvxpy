# -*- coding: utf-8 -*-
"""Scene compositions for episode 53."""
import numpy as np, cv2
from engine import (W, H, FPS, SERIF_SC, SERIF_TC, SANS_SC, BRUSH, INK, PAPER, CINNABAR, GOLD, MIST,
                    text_sprite, vtext_sprite, blit, rgb, clamp, ease, ease_out, paper_texture, scale_sprite)
from scenes import (Base, ScrollScene, T, chip, seal, fade, ink_night, draw_scroll, ink_layer, arrow_strokes,
                    brush_path, WHITE, DIM, INKG, TEAL, SC_X0, SC_X1, SC_Y0, SC_Y1)
from rain import RainWindow
from water import Water

CX = W / 2
SRC = (120, 112, 100)          # source line colour on paper
GREEN = (60, 104, 84)


def src(img, s, y=1385, a=1.0):
    T(img, s, CX, y, 26, SRC, SANS_SC, a, weight=400, maxw=860)


# ============================================================ rain-window scenes (shared timeline)
class RainSeg(Base):
    """A window into a shared RainWindow timeline (offset = this scene's start within the rain block)."""

    def __init__(self, dur, lt, rw, offset, overlay=None):
        super().__init__(dur, lt)
        self.rw, self.offset, self.overlay = rw, offset, overlay

    def render(self, t):
        img = self.rw.render(self.offset + t)
        if self.overlay:
            self.overlay(self, img, t)
        return img


def ov_hook(sc, img, t):
    # title on the dark glass from frame 0
    a = 1.0 - fade(t, sc.dur - 0.8, 0.8)
    T(img, "抑郁好了以后，", CX, 250, 76, WHITE, SERIF_SC, a, weight=700, shadow=6)
    T(img, "为什么还会回来？", CX, 360, 76, WHITE, SERIF_SC, a, weight=700, shadow=6)
    T(img, "静坐的科学 · 二", CX, 120, 32, GOLD, SERIF_SC, a * 0.9, weight=500, tracking=8)


def ov_headline(sc, img, t):
    # darken the upper glass a touch for legibility
    k = fade(t, 0.0, 0.5)
    img[:900] *= (1 - 0.35 * k)
    T(img, "9", 300, 300, 190, GOLD, SERIF_SC, fade(t, 0.1), weight=700, shadow=6)
    T(img, "项随机试验", 300, 430, 44, WHITE, SERIF_SC, fade(t, 0.3), weight=500, shadow=4)
    T(img, "1,258", 760, 300, 150, GOLD, SERIF_SC, fade(t, sc.L(0) + 1.4), weight=700, shadow=6)
    T(img, "名患者", 760, 430, 44, WHITE, SERIF_SC, fade(t, sc.L(0) + 1.6), weight=500, shadow=4)
    a2 = fade(t, sc.L(1) + 0.3)
    T(img, "复发风险", CX, 600, 52, WHITE, SERIF_SC, a2, weight=500, shadow=4)
    T(img, "↓ 约三成", CX, 720, 110, (240, 200, 140), SERIF_SC, fade(t, sc.L(1) + 1.6), weight=700, shadow=6)
    T(img, "Kuyken et al., JAMA Psychiatry, 2016 · 已缓解的复发性抑郁患者 · 60 周随访", CX, 830, 25, (200, 200, 200),
      SANS_SC, fade(t, sc.L(1) + 2.2), weight=400, maxw=1000)


def ov_thesis(sc, img, t):
    k = fade(t, 0.0, 0.5)
    img[:1000] *= (1 - 0.3 * k)
    T(img, "不是不再难过", CX, 330, 100, WHITE, BRUSH, fade(t, 0.1, 0.8), shadow=8, maxw=1040)
    T(img, "而是不再被难过拖走", CX, 500, 100, (244, 214, 160), BRUSH, fade(t, sc.L(1) + 0.9, 0.8), shadow=8, maxw=1040)


def ov_yinzhao(sc, img, t):
    T(img, "经文讲修行　研究讲复发率", CX, 300, 50, WHITE, SERIF_SC, fade(t, 0.2) * (1 - fade(t, sc.L(1), 0.5)), weight=500, shadow=5)
    a = fade(t, sc.L(1) + 0.2)
    T(img, "印照，不是证明", CX, 300, 78, (244, 214, 160), SERIF_SC, a, weight=700, shadow=6)
    T(img, "此生 · 此心", CX, 450, 64, WHITE, BRUSH, fade(t, sc.L(2) + 1.6, 1.0), shadow=6)


def ov_end(sc, img, t):
    T(img, "雨总会停。", CX, 260, 70, (60, 46, 36), BRUSH, fade(t, 0.2, 0.8) * (1 - fade(t, sc.L(1), 0.6)))
    a = fade(t, sc.L(1) + 0.1, 0.8)
    T(img, "难过来了，可以让它只是难过；", CX, 250, 54, (52, 40, 32), SERIF_SC, a * (1 - fade(t, sc.L(3), 0.6)), weight=600)
    T(img, "看见念头只是念头，就少中一支箭。", CX, 340, 54, (52, 40, 32), SERIF_SC,
      fade(t, sc.L(2) + 0.1, 0.8) * (1 - fade(t, sc.L(3), 0.6)), weight=600)
    a3 = fade(t, sc.L(3) - 0.1, 1.0)
    T(img, "不被第二毒箭", CX, 320, 120, (40, 30, 24), BRUSH, a3)
    T(img, "——《杂阿含经》卷十七 · 第 470 经", CX, 560, 34, (70, 56, 44), SERIF_SC, fade(t, sc.L(3) + 0.8), weight=500)
    T(img, "本片不构成医疗建议　如有困扰，请寻求专业帮助", CX, 1800, 32, (226, 220, 210), SANS_SC, fade(t, sc.L(3) + 1.4), weight=500)


# ============================================================ ink-on-paper scenes
class PaperScene(Base):
    seed = 2

    def bg(self, t):
        p = paper_texture().copy()
        f = np.clip((np.arange(H, dtype=np.float32) - 1440) / 100, 0, 1)[:, None, None]
        return p * (1 - f) + ink_night() * f


class ArrowTease(PaperScene):
    def __init__(self, dur, lt):
        super().__init__(dur, lt)
        self.a1 = arrow_strokes(170, 560, 900, 470, w=10, seed=1)
        self.a2 = arrow_strokes(170, 800, 900, 730, w=10, seed=7)

    def render(self, t):
        img = self.bg(t)
        s1 = [(st, 0.15 + 0.12 * i, 0.9 + 0.12 * i) for i, st in enumerate(self.a1)]
        a = ink_layer((W, H), s1, t, seed=1)
        img = img * (1 - a[..., None] * 0.92) + rgb(INK) * a[..., None] * 0.92
        T(img, "第一支箭", 540, 400, 46, INK, SERIF_SC, fade(t, 0.6), weight=600)
        t2 = self.L(0) + 2.2
        s2 = [(st, t2 + 0.12 * i, t2 + 0.75 + 0.12 * i) for i, st in enumerate(self.a2)]
        b = ink_layer((W, H), s2, t, seed=7)
        dis = fade(t, t2 + 1.6, 1.4)          # second arrow fades to a ghost
        k = 0.85 * (1 - 0.75 * dis)
        img = img * (1 - b[..., None] * k) + rgb((120, 40, 30)) * b[..., None] * k
        T(img, "第二支箭", 540, 650, 46, (120, 40, 30), SERIF_SC, fade(t, t2 + 0.4) * (1 - 0.6 * dis), weight=600)
        if dis > 0:
            cv2.line(img, (300, 600), (780, 900), rgb(CINNABAR).tolist(), int(10 * dis) + 1, cv2.LINE_AA)
            cv2.line(img, (780, 600), (300, 900), rgb(CINNABAR).tolist(), int(10 * dis) + 1, cv2.LINE_AA)
        T(img, "中了一箭，别再中第二箭", CX, 1060, 60, INK, SERIF_SC, fade(t, self.L(0) + 3.6), weight=600)
        seal(img, "印照", 360, 1240, 56, fade(t, self.L(2) + 0.3, 0.4))
        T(img, "不是证明", 600, 1240, 58, CINNABAR, SERIF_SC, fade(t, self.L(2) + 0.7), weight=700)
        return img


class Disclaimer(Base):
    def render(self, t):
        img = ink_night().copy()
        T(img, "先说一句", CX, 420, 44, GOLD, SERIF_SC, fade(t, 0.1), weight=500, tracking=6)
        T(img, "本片只讲研究\n不构成医疗建议", CX, 620, 70, WHITE, SERIF_SC, fade(t, 0.3), weight=700, spacing=1.5)
        T(img, "正在服药或治疗\n任何调整，请先和医生商量", CX, 930, 50, (210, 206, 198), SERIF_SC, fade(t, self.L(1) + 0.2),
          weight=500, spacing=1.5)
        return img


class Path(PaperScene):
    """A footpath trodden deeper with each episode; old thoughts wake along it."""

    def __init__(self, dur, lt):
        super().__init__(dur, lt)
        xs = np.linspace(120, 960, 40)
        self.pts = [(x, 1000 - 260 * np.sin((x - 120) / 840 * np.pi * 1.1) * 0.6 - (x - 120) * 0.35) for x in xs]

    def render(self, t):
        img = self.bg(t)
        T(img, "每一次发作，都像在心里踩出一条小路", CX, 230, 44, INK, SERIF_SC, fade(t, self.L(3) - 0.2), weight=600)
        times = [self.L(1) + 0.2, self.L(1) + 1.6, self.L(1) + 3.0, self.L(3) + 0.4]
        widths = [2.5, 5, 8, 11]
        for i, (ti, wv) in enumerate(zip(times, widths)):
            st = brush_path(self.pts, wv, wv * 0.8, seed=i, n=300)
            a = ink_layer((W, H), [(st, ti, ti + 1.6)], t, seed=i)
            kk = 0.35 + 0.15 * i
            img = img * (1 - a[..., None] * kk) + rgb(INK) * a[..., None] * kk
        for i, lab in enumerate(["第一次", "第二次", "第三次"]):
            T(img, lab, 200 + 300 * i, 1160 - 120 * i, 34, INKG, SERIF_SC, fade(t, times[i] + 0.4), weight=500)
        # path stays after recovery
        T(img, "病好了，路还在", CX, 1300, 44, INKG, SERIF_SC, fade(t, self.L(4)) * (1 - fade(t, self.L(5), 0.5)), weight=600)
        # a grey day wakes the old thoughts along the path
        th = [("我又不行了", 300, 820), ("什么都不会好", 600, 650), ("都是我的错", 820, 520)]
        for i, (s, x, y) in enumerate(th):
            a = fade(t, self.L(6) + 1.6 + 1.0 * i, 0.5)
            T(img, s, x, y, 50, (130, 36, 28), SERIF_SC, a, weight=700)
        T(img, "一点小小的低落 → 整套旧想法被唤醒", CX, 1300, 40, INK, SERIF_SC, fade(t, self.L(5) + 0.2), weight=500)
        return img


class Reactivity(ScrollScene):
    label = "认知反应性 · 一项实验"

    def content(self, img, t):
        T(img, "Segal 等, 2006", CX, 240, 40, INKG, SERIF_SC, fade(t, 0.6), weight=500)
        T(img, "99 位已康复的抑郁症患者", CX, 320, 54, INK, SERIF_SC, fade(t, self.L(1)), weight=700)
        # mood dip -> belief rise schematic
        x0, x1, ybase = 160, 920, 640
        p = clamp((t - self.L(1) - 1.5) / 2.0)
        n = int(80 * p)
        xs = np.linspace(x0, x1, 80)
        mood = ybase - 40 + 70 * np.exp(-((xs - 400) / 90) ** 2)
        pts = np.stack([xs, mood], 1).astype(np.int32)[:max(2, n)]
        if n > 1:
            cv2.polylines(img, [pts], False, rgb(TEAL).tolist(), 5, cv2.LINE_AA)
        T(img, "情绪被短暂调低", 330, 520, 34, TEAL, SERIF_SC, fade(t, self.L(1) + 2.0), weight=500)
        q = clamp((t - self.L(2)) / 1.6)
        bars = [(560, 90, "勾起少"), (720, 230, "勾起多")]
        for i, (bx, hgt, lab) in enumerate(bars):
            hh = int(hgt * ease(q))
            cv2.rectangle(img, (bx, 900 - hh), (bx + 90, 900), rgb((150, 60, 46) if i else (120, 110, 100)).tolist(), -1)
            T(img, lab, bx + 45, 940, 32, INK, SERIF_SC, fade(t, self.L(2) + 0.4), weight=500)
        T(img, "消极信念", 640, 600, 36, INK, SERIF_SC, fade(t, self.L(2) + 0.2), weight=600)
        T(img, "勾起越多 → 18 个月内复发越早", CX, 1060, 46, (150, 40, 30), SERIF_SC, fade(t, self.L(3) + 0.3), weight=700)
        chip(img, "实证 · 单项研究 · 小样本（99人）", CX, 1190, fade(t, self.L(4) + 0.2), CINNABAR, 32)
        src(img, "Segal ZV et al. Arch Gen Psychiatry 2006;63(7):749-755", a=fade(t, 0.8))


class Rumination(Base):
    def __init__(self, dur, lt, mode="ruminate"):
        super().__init__(dur, lt)
        self.w = Water(dur + 1, mode, center=(540, 760), moon=(560, 560))

    def render(self, t):
        img = self.w.render(t)
        words = ["为什么", "怎么办", "又是我", "为什么", "我不行", "怎么办", "又搞砸了", "为什么"]
        for i, s in enumerate(words):
            t0 = 0.6 + i * 1.3
            a = t - t0
            if a < 0 or a > 6:
                continue
            ang = i * 2.4
            r = 60 + 80 * a
            x, y = 540 + r * np.cos(ang), 760 + r * np.sin(ang) * 0.9
            al = clamp(a / 0.6) * clamp((6 - a) / 2) * 0.85
            T(img, s, x, y, 40 + int(4 * a), (200, 214, 230), SERIF_SC, al, weight=500, shadow=3)
        T(img, "反刍", CX, 1220, 96, (230, 232, 236), BRUSH, fade(t, self.L(1) + 0.1, 0.8), shadow=6)
        T(img, "像在解决问题，其实在原地打转", CX, 1350, 42, (200, 206, 214), SERIF_SC, fade(t, self.L(2) + 0.6), weight=500, shadow=4)
        return img


class Origin(ScrollScene):
    label = "MBCT 的来历 · 1990 年代"

    def content(self, img, t):
        names = [("辛德尔·西格尔", "Zindel Segal"), ("马克·威廉斯", "Mark Williams"), ("约翰·蒂斯代尔", "John Teasdale")]
        for i, (zh, en) in enumerate(names):
            a = fade(t, self.L(1) + 0.4 * i)
            y = 260 + 110 * i
            T(img, zh, CX, y, 46, INK, SERIF_SC, a, weight=700)
            T(img, en, CX, y + 46, 26, INKG, SANS_SC, a, weight=400)
        T(img, "起初：想做「维持版」认知疗法", CX, 610, 40, INKG, SERIF_SC, fade(t, self.L(2)) * (1 - 0.5 * fade(t, self.L(3))), weight=500)
        T(img, "后来：不是把想法改对，\n而是换一种方式和想法相处", CX, 720, 38, INK, SERIF_SC, fade(t, self.L(3) + 0.5), weight=600, maxw=860)
        # equation
        a = fade(t, self.L(4))
        cv2.rectangle(img, (110, 820), (500, 1010), rgb((226, 216, 196)).tolist(), -1) if a > 0.5 else None
        T(img, "正念减压", 300, 870, 46, INK, SERIF_SC, a, weight=700)
        T(img, "卡巴金 · 麻省大学医学院", 300, 930, 26, INKG, SANS_SC, a, weight=400)
        T(img, "取法东方禅修传统", 300, 975, 26, INKG, SANS_SC, fade(t, self.L(5)), weight=400)
        T(img, "＋", CX, 915, 60, INK, SERIF_SC, fade(t, self.L(6)), weight=400)
        T(img, "认知疗法", 780, 900, 46, INK, SERIF_SC, fade(t, self.L(6) + 0.3), weight=700)
        T(img, "CBT", 780, 955, 28, INKG, SANS_SC, fade(t, self.L(6) + 0.3), weight=400)
        T(img, "↓", CX, 1060, 60, INK, SERIF_SC, fade(t, self.L(6) + 1.6), weight=400)
        T(img, "正念认知疗法 MBCT", CX, 1170, 66, (150, 40, 30), SERIF_SC, fade(t, self.L(6) + 2.2), weight=700)
        src(img, "Segal, Williams & Teasdale, Mindfulness-Based Cognitive Therapy for Depression (Guilford, 2002; 2nd ed. 2013)", a=fade(t, self.L(6) + 2.4))


class Design(ScrollScene):
    label = "专为「防复发」而设计"

    def content(self, img, t):
        T(img, "对象", 230, 270, 40, INKG, SERIF_SC, fade(t, 0.5), weight=500)
        T(img, "曾多次抑郁、现已缓解的人", 590, 270, 44, INK, SERIF_SC, fade(t, 0.7), weight=700, maxw=620)
        T(img, "目标", 230, 370, 40, INKG, SERIF_SC, fade(t, self.L(1)), weight=500)
        T(img, "防住下一次", 590, 370, 44, (150, 40, 30), SERIF_SC, fade(t, self.L(1) + 0.3), weight=700)
        # 8 weeks
        for i in range(8):
            a = fade(t, self.L(2) + 0.25 * i, 0.3)
            x = 170 + i * 105
            cv2.circle(img, (int(x), 520), 36, rgb(INK).tolist(), 3, cv2.LINE_AA) if a > 0.05 else None
            if a > 0.5:
                cv2.circle(img, (int(x), 520), 26, rgb(TEAL).tolist(), -1, cv2.LINE_AA)
            T(img, str(i + 1), x, 520, 28, (250, 244, 232), SANS_SC, a, weight=600)
        T(img, "8 周 · 每周一次小组课 · 每天在家练习", CX, 600, 36, INK, SERIF_SC, fade(t, self.L(2) + 1.0), weight=500)
        T(img, "呼吸　身体扫描　日常觉察", CX, 690, 40, INKG, SERIF_SC, fade(t, self.L(3) + 0.3), weight=600, tracking=4)
        # three-minute breathing space: three arcs of a circle
        T(img, "三分钟呼吸空间", CX, 800, 50, INK, SERIF_SC, fade(t, self.L(4)), weight=700)
        cx, cy, R = 540, 1060, 150
        segs = [(self.L(5), "觉察：念头·感受·身体"), (self.L(6), "收拢：呼吸"), (self.L(6) + 2.6, "扩展：全身")]
        cols = [TEAL, (150, 110, 60), (150, 40, 30)]
        for i, (ti, lab) in enumerate(segs):
            p = clamp((t - ti) / 1.8)
            if p > 0:
                cv2.ellipse(img, (cx, cy), (R, R), -90, 120 * i, 120 * i + 118 * ease(p), rgb(cols[i]).tolist(), 16, cv2.LINE_AA)
            ang = np.deg2rad(-90 + 120 * i + 60)
            lx, ly = [(cx + 300, cy - 110), (cx, cy + R + 60), (cx - 300, cy - 110)][i]
            T(img, lab, lx, ly, 30, cols[i], SERIF_SC, fade(t, ti + 0.6), weight=600, maxw=260)
            T(img, f"第{'一二三'[i]}分钟", cx, cy - 20 + 0 * i, 34, cols[i], SERIF_SC,
              fade(t, ti) * (1 - fade(t, segs[i + 1][0] if i < 2 else 1e9, 0.4)), weight=600)


class Decenter(PaperScene):
    def render(self, t):
        img = self.bg(t)
        # head outline in ink (profile facing right)
        cx, cy = 400, 700
        hp = clamp(t / 1.5)
        pts = []
        for a in np.linspace(0, 2 * np.pi * 0.9 * hp, 120):
            r = 230 + 8 * np.sin(2 * a)
            pts.append((cx + r * np.cos(a + 2.2), cy + r * np.sin(a + 2.2)))
        if len(pts) > 1 and hp > 0.02:
            st = brush_path(pts, 18, 4, seed=3, n=220)
            a = ink_layer((W, H), [(st, 0, 0.01)], 1, seed=3)
            img = img * (1 - a[..., None] * 0.8) + rgb(INK) * a[..., None] * 0.8
        T(img, "看见它　承认它　不必相信它", CX, 250, 46, INK, SERIF_SC, fade(t, 0.8), weight=700)
        # the thought moves out of the head into a cloud
        t_out = self.L(2) + 2.2
        k = ease(clamp((t - t_out) / 2.0))
        tx, ty = cx + (760 - cx) * k, cy + (520 - cy) * k
        if k > 0.02:
            for j in range(7):
                ang = j / 7 * 2 * np.pi
                cv2.ellipse(img, (int(tx + 120 * np.cos(ang)), int(ty + 55 * np.sin(ang))), (85, 60), 0, 0, 360,
                            (rgb((200, 192, 176)) * (1 - 0.0)).tolist(), -1, cv2.LINE_AA) if k > 0.6 else None
        T(img, "「我真没用」", tx, ty, 56, (140, 36, 28), SERIF_SC, fade(t, self.L(2)), weight=700)
        T(img, "心中飘过的念头", 640, 400, 44, TEAL, SERIF_SC, fade(t, t_out + 1.8), weight=700)
        T(img, "✓", 860, 400, 44, TEAL, SANS_SC, fade(t, t_out + 1.8), weight=700)
        T(img, "事实", 760, 980, 44, INKG, SERIF_SC, fade(t, t_out + 2.4), weight=700)
        if t > t_out + 2.6:
            cv2.line(img, (700, 980), (820, 980), rgb(CINNABAR).tolist(), 5, cv2.LINE_AA)
        T(img, "去中心化", CX, 1190, 76, INK, BRUSH, fade(t, self.L(1) + 0.2, 0.8))
        chip(img, "机制假说 · 理论＋部分实证", CX, 1320, fade(t, self.L(3) + 0.2), CINNABAR, 34)
        return img


class Teasdale(ScrollScene):
    label = "第一项随机试验 · 2000"

    def content(self, img, t):
        T(img, "145 名已康复患者 · 随访 60 周", CX, 260, 46, INK, SERIF_SC, fade(t, self.L(1)), weight=700)
        # two groups of dots
        rng = np.random.default_rng(4)
        for g, (gx, lab) in enumerate([(300, "照常治疗"), (780, "照常治疗 ＋ MBCT")]):
            a = fade(t, self.L(1) + 1.5 + 0.6 * g)
            if a > 0.05:
                for i in range(72):
                    x = gx - 150 + (i % 12) * 27; y = 370 + (i // 12) * 27
                    c = TEAL if g else (120, 110, 100)
                    cv2.circle(img, (x, y), 9, (rgb(c) * a + rgb(PAPER) * (1 - a)).tolist(), -1, cv2.LINE_AA)
            T(img, lab, gx, 560, 34, INK, SERIF_SC, a, weight=600)
        y0 = 700
        T(img, "发作过 3 次以上", 300, y0, 44, INK, SERIF_SC, fade(t, self.L(3) + 0.2), weight=700)
        T(img, "复发风险明显下降", 740, y0, 44, GREEN, SERIF_SC, fade(t, self.L(3) + 1.2), weight=700)
        T(img, "只发作过 2 次", 300, y0 + 120, 44, INK, SERIF_SC, fade(t, self.L(3) + 3.0), weight=700)
        T(img, "看不出差别", 740, y0 + 120, 44, INKG, SERIF_SC, fade(t, self.L(3) + 4.0), weight=700)
        T(img, "它针对的，可能正是那条被反复踩过的旧路", CX, 1010, 40, (150, 40, 30), SERIF_SC, fade(t, self.L(4) + 0.4), weight=600)
        chip(img, "实证 · 单项随机试验", CX, 1150, fade(t, self.L(3) + 1.0), CINNABAR, 32)
        src(img, "Teasdale JD et al. J Consult Clin Psychol 2000;68(4):615-623", a=fade(t, 0.8))


class Kuyken(ScrollScene):
    label = "最有分量的证据 · 2016"

    def content(self, img, t):
        T(img, "JAMA Psychiatry", CX, 240, 44, INK, SERIF_SC, fade(t, self.L(1) + 0.5), weight=700)
        T(img, "《美国医学会精神病学杂志》", CX, 300, 34, INKG, SERIF_SC, fade(t, self.L(1) + 0.8), weight=500)
        T(img, "Kuyken 等 · 牛津大学", CX, 370, 36, INK, SERIF_SC, fade(t, self.L(2)), weight=600)
        # 9 trial blocks merging into one
        m = ease(clamp((t - self.L(3) - 2.0) / 2.0))
        for i in range(9):
            a = fade(t, self.L(3) + 0.15 * i, 0.3)
            if a < 0.05:
                continue
            x0 = 130 + i * 92; y0 = 460
            xm = 330 + (i % 3) * 140; ym = 450 + (i // 3) * 40
            x = x0 + (xm - x0) * m; y = y0 + (ym - y0) * m
            cv2.rectangle(img, (int(x), int(y)), (int(x + 70), int(y + 30)), (rgb(TEAL) * a + rgb(PAPER) * (1 - a)).tolist(), -1)
            T(img, f"试验{i + 1}", x + 35, y + 15, 18, (250, 244, 232), SANS_SC, a * (1 - m), weight=500)
        T(img, "每位患者的原始数据 → 重新合算", CX, 640, 38, INK, SERIF_SC, fade(t, self.L(3) + 3.0), weight=600)
        T(img, "个体数据元分析（IPD meta-analysis）", CX, 720, 40, (150, 40, 30), SERIF_SC, fade(t, self.L(4)), weight=700)
        # 1,258 dots
        a = clamp((t - self.L(5)) / 2.5)
        n = int(1258 * a)
        if n > 0:
            idx = np.arange(n)
            xs = 150 + (idx % 52) * 15.3; ys = 800 + (idx // 52) * 15.3
            fem = (idx % 4) != 3
            for x, y, f in zip(xs, ys, fem):
                cv2.circle(img, (int(x), int(y)), 5, rgb(TEAL if f else (150, 110, 60)).tolist(), -1, cv2.LINE_AA)
        T(img, "1,258 人 · 平均 47 岁 · 女性 75%", CX, 1210, 42, INK, SERIF_SC, fade(t, self.L(5) + 1.0), weight=700)
        src(img, "Kuyken W et al. JAMA Psychiatry 2016;73(6):565-574", a=fade(t, self.L(1) + 1.0))


class Forest(ScrollScene):
    label = "复发风险比（60 周）"

    def content(self, img, t):
        x_of = lambda v: 200 + (v - 0.4) / (1.2 - 0.4) * 700
        y_axis = 1000
        a = fade(t, 0.5)
        if a > 0.05:
            cv2.line(img, (int(x_of(0.4)), y_axis), (int(x_of(1.2)), y_axis), rgb(INK).tolist(), 2, cv2.LINE_AA)
            for v in [0.4, 0.6, 0.8, 1.0, 1.2]:
                cv2.line(img, (int(x_of(v)), y_axis), (int(x_of(v)), y_axis + 12), rgb(INK).tolist(), 2, cv2.LINE_AA)
                T(img, f"{v:.1f}", x_of(v), y_axis + 42, 28, INK, SANS_SC, a, weight=400)
            for yy in range(330, y_axis, 24):
                cv2.line(img, (int(x_of(1.0)), yy), (int(x_of(1.0)), yy + 12), rgb(INKG).tolist(), 2, cv2.LINE_AA)
            T(img, "1 = 没有差别", x_of(1.0), 300, 28, INKG, SANS_SC, a, weight=400)
            T(img, "← 复发风险更低", x_of(0.62), y_axis + 100, 32, GREEN, SERIF_SC, a, weight=600)
        rows = [(self.L(0) + 1.0, 0.69, 0.58, 0.82, "对比：未接受 MBCT", 500),
                (self.L(1) + 1.0, 0.79, 0.64, 0.97, "对比：其他积极治疗（含抗抑郁药）", 740)]
        for (ti, hr, lo, hi, lab, y) in rows:
            p = ease(clamp((t - ti) / 1.2))
            if p <= 0:
                continue
            T(img, lab, CX, y - 90, 36, INK, SERIF_SC, fade(t, ti - 0.4), weight=600)
            xl, xh, xc = x_of(lo), x_of(hi), x_of(hr)
            cv2.line(img, (int(xc - (xc - xl) * p), y), (int(xc + (xh - xc) * p), y), rgb(INK).tolist(), 4, cv2.LINE_AA)
            s = int(18 * p)
            cv2.rectangle(img, (int(xc - s), y - s), (int(xc + s), y + s), rgb((150, 40, 30)).tolist(), -1)
            T(img, f"{hr:.2f}", xc, y + 56, 40, (150, 40, 30), SANS_SC, fade(t, ti + 0.6), weight=700)
            T(img, f"95% CI {lo:.2f}–{hi:.2f}", xc, y + 95, 26, INKG, SANS_SC, fade(t, ti + 1.0), weight=400)
        T(img, "约低三成", 240, 500, 34, GREEN, SERIF_SC, fade(t, self.L(0) + 3.5), weight=700)
        T(img, "约低两成", 240, 740, 34, GREEN, SERIF_SC, fade(t, self.L(1) + 3.5), weight=700)
        if t > self.L(2) + 0.5:
            r = int(24 + 6 * np.sin(t * 4))
            cv2.circle(img, (int(x_of(0.97)), 740), r, rgb(CINNABAR).tolist(), 3, cv2.LINE_AA)
            T(img, "上限接近 1：优势不大", x_of(0.97) - 20, 900, 30, CINNABAR, SERIF_SC, fade(t, self.L(2) + 0.6), weight=600)
        T(img, "残余症状越重，获益可能越大（有一些证据提示）", CX, 1230, 34, INK, SERIF_SC, fade(t, self.L(3) + 0.5), weight=600, maxw=860)
        chip(img, "实证 · 证据较强", CX, 1310, fade(t, 1.0), CINNABAR, 32)
        src(img, "Kuyken W et al. JAMA Psychiatry 2016;73(6):565-574 · HR, 95% CI", a=fade(t, 1.0))


class Caveat(ScrollScene):
    label = "两点必须说清楚"

    def content(self, img, t):
        a1 = fade(t, self.L(1))
        T(img, "①", 160, 290, 56, (150, 40, 30), SERIF_SC, a1, weight=700)
        T(img, "对象：复发性抑郁、目前已缓解的人", 570, 270, 40, INK, SERIF_SC, a1, weight=700, maxw=720)
        T(img, "不是急性发作期，更不是所有人", 570, 330, 34, INKG, SERIF_SC, fade(t, self.L(1) + 2.5), weight=500, maxw=720)
        a2 = fade(t, self.L(2))
        T(img, "②", 160, 460, 56, (150, 40, 30), SERIF_SC, a2, weight=700)
        T(img, "不是替代治疗", 570, 440, 48, INK, SERIF_SC, a2, weight=700, maxw=720)
        T(img, "「打坐可以代替吃药」？读反了", 570, 510, 36, CINNABAR, SERIF_SC, fade(t, self.L(2) + 2.0), weight=600, maxw=720)
        a3 = fade(t, self.L(3))
        if a3 > 0.02:
            cv2.rectangle(img, (130, 640), (950, 1180), (rgb((226, 216, 196)) * a3 + rgb(PAPER) * (1 - a3)).tolist(), -1)
        T(img, "英国 NICE 成人抑郁指南（NG222, 2022）", CX, 700, 38, INK, SERIF_SC, a3, weight=700, maxw=800)
        T(img, "团体正念认知疗法：预防复发的可选方案之一", CX, 800, 38, INK, SERIF_SC, fade(t, self.L(3) + 2.0), weight=600, maxw=780)
        T(img, "与继续服药等方案并列", CX, 900, 38, INK, SERIF_SC, fade(t, self.L(4)), weight=600, maxw=780)
        T(img, "由受过专门训练的人带领", CX, 980, 38, INK, SERIF_SC, fade(t, self.L(4) + 1.6), weight=600, maxw=780)
        T(img, "是否用药、如何调整，请遵医嘱", CX, 1090, 34, CINNABAR, SERIF_SC, fade(t, self.L(4) + 2.6), weight=600, maxw=780)
        src(img, "NICE guideline NG222: Depression in adults: treatment and management (June 2022)", a=a3)


class Goyal(ScrollScene):
    label = "焦虑与抑郁情绪 · 2014"

    def content(self, img, t):
        T(img, "JAMA Internal Medicine · 约翰斯·霍普金斯大学", CX, 230, 32, INKG, SERIF_SC, fade(t, self.L(1)), weight=500, maxw=880)
        # funnel
        steps = [(self.L(2) + 0.2, "18,753", "篇文献", 760), (self.L(2) + 1.8, "47", "项随机试验", 520), (self.L(2) + 3.2, "3,515", "人 · 均有积极对照", 360)]
        for i, (ti, num, lab, wv) in enumerate(steps):
            a = fade(t, ti)
            y = 320 + i * 100
            if a > 0.02:
                cv2.rectangle(img, (int(CX - wv / 2), y), (int(CX + wv / 2), y + 80), (rgb((214, 204, 184)) * a + rgb(PAPER) * (1 - a)).tolist(), -1)
            T(img, num + " " + lab, CX, y + 40, 38, INK, SERIF_SC, a, weight=700)
        # effect-size ruler
        x_of = lambda v: 160 + v / 0.9 * 760
        y = 900
        a = fade(t, self.L(3))
        if a > 0.02:
            cv2.line(img, (int(x_of(0)), y), (int(x_of(0.9)), y), rgb(INK).tolist(), 2, cv2.LINE_AA)
            for v, lab in [(0.2, "小"), (0.5, "中"), (0.8, "大")]:
                cv2.line(img, (int(x_of(v)), y - 10), (int(x_of(v)), y + 10), rgb(INK).tolist(), 2, cv2.LINE_AA)
                T(img, f"{v}\n{lab}", x_of(v), y + 60, 26, INKG, SANS_SC, a, weight=400, spacing=1.2)
        for i, (v, lab, ti) in enumerate([(0.38, "焦虑 0.38", self.L(3) + 2.0), (0.30, "抑郁 0.30", self.L(3) + 3.0)]):
            p = ease(clamp((t - ti) / 1.0))
            yy = 760 + i * 60
            if p > 0:
                cv2.rectangle(img, (int(x_of(0)), yy - 18), (int(x_of(0) + (x_of(v) - x_of(0)) * p), yy + 18), rgb(TEAL if i == 0 else (150, 110, 60)).tolist(), -1)
            T(img, lab, x_of(v) + 110, yy, 32, INK, SANS_SC, fade(t, ti + 0.6), weight=600)
        T(img, "效应量（8 周）", x_of(0) + 120, 700, 30, INKG, SERIF_SC, a, weight=500)
        T(img, "小到中等：看得出来，但不是奇迹", CX, 1060, 40, INK, SERIF_SC, fade(t, self.L(4)), weight=700)
        T(img, "不优于药物、运动、其他行为疗法", CX, 1150, 40, CINNABAR, SERIF_SC, fade(t, self.L(5) + 0.4), weight=700)
        chip(img, "实证 · 系统综述 · 中等强度证据", CX, 1260, fade(t, self.L(3) + 1.0), CINNABAR, 32)
        src(img, "Goyal M et al. JAMA Intern Med 2014;174(3):357-368", a=fade(t, self.L(1)))


class Limits(ScrollScene):
    label = "泼一点冷水"

    def content(self, img, t):
        a = fade(t, self.L(1))
        T(img, "Mind the Hype", CX, 250, 56, INK, SERIF_SC, a, weight=700)
        T(img, "《警惕炒作》 · Van Dam 等 15 位学者 · 2018", CX, 320, 30, INKG, SERIF_SC, a, weight=500, maxw=880)
        items = [(self.L(2), "定义不一"), (self.L(2) + 2.4, "样本小 · 对照弱"), (self.L(3), "难以盲法 · 期待效应")]
        for i, (ti, s) in enumerate(items):
            T(img, "·  " + s, CX, 410 + i * 70, 40, INK, SERIF_SC, fade(t, ti), weight=600)
        chip(img, "争议与局限", CX, 640, fade(t, self.L(2)), (120, 110, 100), 30)
        # 100-dot matrix, ~8 marked
        a2 = fade(t, self.L(5))
        if a2 > 0.02:
            for i in range(100):
                x = 300 + (i % 10) * 52; y = 760 + (i // 10) * 42
                bad = i in (7, 18, 33, 41, 56, 64, 79, 92)
                c = (150, 40, 30) if bad and t > self.L(6) else (150, 144, 134)
                cv2.circle(img, (x, y), 13, (rgb(c) * a2 + rgb(PAPER) * (1 - a2)).tolist(), -1, cv2.LINE_AA)
        T(img, "83 项研究 · 6,703 名练习者", CX, 710, 34, INK, SERIF_SC, a2, weight=600)
        T(img, "约 8% 报告过不良反应（焦虑、情绪低落最常见）", CX, 1210, 34, (150, 40, 30), SERIF_SC, fade(t, self.L(6) + 0.3), weight=700, maxw=900)
        T(img, "严重抑郁或创伤：请在合格指导下练习", CX, 1290, 38, INK, SERIF_SC, fade(t, self.L(7) + 0.2), weight=700)
        src(img, "Van Dam NT et al. Perspect Psychol Sci 2018;13(1):36-61 · Farias M et al. Acta Psychiatr Scand 2020;142(5):374-393", y=1385, a=a)


class Ledger(ScrollScene):
    label = "证据捋一捋"

    def content(self, img, t):
        rows = [("预防复发", "实证 · 较强", "仅限已缓解的复发性抑郁", GREEN),
                ("焦虑与抑郁情绪", "实证 · 小到中等", "不优于其他积极疗法", TEAL),
                ("去中心化机制", "理论＋部分实证", "仍在研究", (150, 110, 60)),
                ("与佛经相通", "类比 · 印照", "不是实证", CINNABAR)]
        for i, (a_, b_, c_, col) in enumerate(rows):
            a = fade(t, self.L(i + 1))
            y = 300 + i * 260
            if a > 0.02:
                cv2.line(img, (130, y + 120), (950, y + 120), (rgb(INKG) * a + rgb(PAPER) * (1 - a)).tolist(), 1, cv2.LINE_AA)
            T(img, a_, 300, y, 46, INK, SERIF_SC, a, weight=700)
            chip(img, b_, 740, y, a, col, 34, fill=True)
            T(img, c_, CX, y + 70, 32, INKG, SERIF_SC, a, weight=500)


class SutraQuote(PaperScene):
    """Vertical classical quote, source, then the plain reading."""

    def __init__(self, dur, lt, quote, source, qline, arrows=False, size=74, col_len=10):
        super().__init__(dur, lt)
        self.quote, self.source, self.qline, self.size, self.col_len = quote, source, qline, size, col_len
        self.arrows = arrows

    def render(self, t):
        img = self.bg(t)
        tq = self.L(self.qline)
        spr = vtext_sprite(self.quote, SERIF_TC, self.size, INK, 600, col_len=self.col_len)
        a = fade(t, tq - 0.3, 1.2)
        blit(img, spr, CX + 40, 720, a)
        # source on the left, small vertical, plus seal
        s2 = vtext_sprite(self.source, SERIF_TC, 34, INKG, 500, col_len=20)
        blit(img, s2, 130, 720, fade(t, tq + 0.8))
        seal(img, "阿含", 130, 1230, 34, fade(t, tq + 1.2))
        if self.qline > 0:
            T(img, "两千多年前的比喻", CX, 300, 44, INKG, SERIF_SC, fade(t, 0.2) * (1 - fade(t, tq - 0.6, 0.4)), weight=600)
            T(img, "凡夫：身受 ＋ 心受　如中两箭", CX, 420, 40, INK, SERIF_SC, fade(t, self.L(min(2, self.qline - 1)) + 0.5) * (1 - fade(t, tq - 0.6, 0.4)), weight=600)
        return img


class Settle(Base):
    """Water ripple from a single stone settles to a mirror; first vs second arrow."""

    def __init__(self, dur, lt):
        super().__init__(dur, lt)
        self.w = Water(dur + 1, "settle", center=(540, 760), moon=(540, 600))

    def render(self, t):
        img = self.w.render(t)
        T(img, "第一支箭", CX, 250, 56, (230, 232, 236), SERIF_SC, fade(t, 0.2), weight=700, shadow=4)
        T(img, "病痛　失去　挫折", CX, 340, 42, (200, 206, 214), SERIF_SC, fade(t, 1.2), weight=500, shadow=4)
        a2 = fade(t, self.L(1))
        T(img, "第二支箭", CX, 1150, 56, (236, 190, 170), SERIF_SC, a2, weight=700, shadow=4)
        T(img, "「为什么又是我」「我永远好不了」", CX, 1240, 40, (220, 196, 186), SERIF_SC, a2, weight=500, shadow=4)
        T(img, "一句批评 → 一整晚回放", CX, 1320, 38, (200, 206, 214), SERIF_SC, fade(t, self.L(2) + 0.5) * (1 - fade(t, self.L(4), 0.5)), weight=500, shadow=4)
        T(img, "难过，就是难过；念头，只是念头", CX, 1320, 42, (230, 232, 236), SERIF_SC, fade(t, self.L(5) + 0.3), weight=600, shadow=4)
        T(img, "相通之处 · 类比", CX, 1420, 30, GOLD, SERIF_SC, fade(t, self.L(4) + 0.2), weight=500, shadow=3)
        return img


class Verse(PaperScene):
    def render(self, t):
        img = self.bg(t)
        tq1, tq2 = self.L(1), self.L(5)
        out1 = fade(t, self.L(4) - 0.2, 0.6)
        spr = vtext_sprite("苦樂二俱捨\n不順亦不違", SERIF_TC, 96, INK, 600, col_len=6, col_gap=1.7)
        blit(img, spr, CX + 40, 650, fade(t, tq1 - 0.3, 1.0) * (1 - out1))
        T(img, "《雜阿含經》卷十七 · 第 470 經 · 偈頌", CX, 1120, 32, INKG, SERIF_TC, fade(t, tq1 + 0.8) * (1 - out1), weight=500)
        T(img, "不顺着它走，也不跟它对抗", CX, 1220, 44, (150, 40, 30), SERIF_SC, fade(t, self.L(2) + 0.2) * (1 - out1), weight=700)
        T(img, "看着它来　看着它走", CX, 1300, 44, INK, SERIF_SC, fade(t, self.L(3) + 2.0) * (1 - out1), weight=600)
        spr2 = vtext_sprite("一切有為法\n如夢幻泡影\n如露亦如電\n應作如是觀", SERIF_TC, 86, INK, 600, col_len=6, col_gap=1.6)
        blit(img, spr2, CX + 30, 640, fade(t, tq2 - 0.3, 1.0))
        T(img, "《金剛般若波羅蜜經》 · 鳩摩羅什 譯", CX, 1130, 32, INKG, SERIF_TC, fade(t, tq2 + 0.8), weight=500)
        T(img, "念头：生起，停留，消散", CX, 1230, 46, (150, 40, 30), SERIF_SC, fade(t, self.L(6) + 0.2), weight=700)
        return img
