# -*- coding: utf-8 -*-
"""分段画面编排。所有时间点都从旁白时间轴（逐字时间）取。"""
import math

import numpy as np

import assets
import script
from assets import MapView, PLACES, MODERN
from engine import (W, H, C, clamp, prog, ease_out, ease_in, ease_io, ease_back, smooth, lerp, fade,
                    draw_text, text_size, set_col, rect, rrect_path, line, circle, polyline, point_along, arrow,
                    arrow_head, draw_seal, paper_texture, paint_surface, new_frame, postprocess, smooth_path)
from timeline import TITLE_CARD
from widgets import (draw_subtitles, chapter_tag, chapter_card, vquote, Dots, tag, card, name_tile, strike, cross,
                     big_number, takeaway, icon_house, icon_flag, icon_tree, icon_boat, icon_crown, icon_gate,
                     icon_granary, icon_coins, icon_dice, icon_person, icon_robe, icon_fire, wind_arrows, TOP_Y)

TITLES = {k: v for k, v in script.SECTIONS}
ORDER = [k for k, _ in script.SECTIONS]


class Film:
    def __init__(self, T):
        self.T = T
        self.subs = T.subtitles()
        # 兵点
        self.d_red_small = Dots(110, 3)
        self.d_red_1700 = Dots(1700, 5)
        self.d_red_170 = Dots(170, 7)
        self.d_blue_2000 = Dots(2000, 9)
        self.d_blue_300 = Dots(300, 11)
        self.d_blue_60 = Dots(60, 13)
        self.d_gray_300 = Dots(300, 15)
        self.d_gray_80 = Dots(80, 17)
        self.d_red_30 = Dots(30, 19)
        self.d_ppl = Dots(2000, 21)
        self.d_lao = Dots(120, 23)
        self.d_crowd = Dots(160, 25)
        rng = np.random.default_rng(77)
        self.beifu_mask = rng.random(2000) < 0.68     # 北府人
        self.flags = rng.random((48, 3))

    # ── 总入口 ────────────────────────────────────────────
    def frame(self, t, fi=0, post=True):
        surf, ctx = new_frame()
        T = self.T
        sec = self.section_at(t)
        getattr(self, "draw_" + sec)(ctx, t)
        # 章节卡与顶部标签
        for i, k in enumerate(ORDER):
            if TITLES[k] and k in T.sec_start:
                t0, t1 = T.sec_start[k], T.sec_end[k]
                chapter_tag(ctx, t, i, TITLES[k], t0 + 1.2, t1 - 0.3)
                chapter_card(ctx, t, i, TITLES[k], t0 - 0.25, 1.75)
        if T.title_start <= t < T.title_start + TITLE_CARD:
            self.title_card(ctx, t)
        draw_subtitles(ctx, t, self.subs)
        if t >= T.end_card:
            self.end_card(ctx, t)
        # 片头/片尾黑场
        rect(ctx, 0, 0, W, H, "#000000", 1 - ease_io(prog(t, 0, 1.4)))
        rect(ctx, 0, 0, W, H, "#000000", ease_io(prog(t, T.total - 1.2, 1.2)))
        if post:
            postprocess(surf, fi)
        return surf

    def section_at(self, t):
        T = self.T
        cur = "S0"
        for k in ORDER:
            if t >= T.sec_start[k] - 0.0:
                cur = k
        # 章节卡最暗时切换场景
        for k in ORDER[1:]:
            if T.sec_start[k] - 0.25 <= t < T.sec_start[k] + 0.25:
                return k if t >= T.sec_start[k] + 0.0 else ORDER[ORDER.index(k) - 1]
        return cur

    def bg(self, ctx, alpha=1.0):
        paint_surface(ctx, paper_texture(1), alpha=alpha)

    # ── 片名卡 ────────────────────────────────────────────
    def title_card(self, ctx, t):
        t0 = self.T.title_start
        a = fade(t, t0, t0 + TITLE_CARD - 0.4, 0.45, 0.4)
        rect(ctx, 0, 0, W, H, "#0a0806", 0.62 * a)
        sc = 1.0 + 0.03 * ease_out(prog(t, t0, TITLE_CARD))
        draw_text(ctx, "京口起兵", W / 2, 700, family="serif", weight="Black", size=150, color=C["ink"], alpha=a,
                  anchor="cm", tracking=0.18, shadow=10, scale=sc)
        line(ctx, W / 2 - 300 * ease_out(prog(t, t0 + 0.2, 0.8)), 820, W / 2 + 300 * ease_out(prog(t, t0 + 0.2, 0.8)), 820,
             C["gold"], 1.6, a * 0.8)
        a2 = fade(t, t0 + 0.4, t0 + TITLE_CARD - 0.4, 0.45, 0.4)
        draw_text(ctx, "一个还不上债的人", W / 2, 885, family="sans", weight="Medium", size=42, color=C["ink"],
                  alpha=a2, anchor="cm", tracking=0.08)
        draw_text(ctx, "怎么用一千多人推翻了皇帝", W / 2, 945, family="sans", weight="Medium", size=42, color=C["ink"],
                  alpha=a2, anchor="cm", tracking=0.08)
        draw_seal(ctx, "寄奴", W / 2 + 330, 640, size=96, alpha=ease_out(prog(t, t0 + 0.9, 0.3)) * a, rot=0.05,
                  scale=1 + 0.3 * (1 - ease_back(prog(t, t0 + 0.9, 0.35))))

    # ── 片尾卡 ────────────────────────────────────────────
    def end_card(self, ctx, t):
        t0 = self.T.end_card
        a = ease_out(prog(t, t0, 0.8))
        rect(ctx, 0, 0, W, H, "#0a0806", 0.88 * a)
        draw_text(ctx, "京口起兵", W / 2, 520, family="serif", weight="Black", size=96, color=C["ink"], alpha=a,
                  anchor="cm", tracking=0.18)
        line(ctx, W / 2 - 200, 600, W / 2 + 200, 600, C["gold"], 1.4, a * 0.7)
        rows = ["主要史料", "《宋书》卷一、卷四十七　《南史》卷一", "《魏书》卷九十七　《晋书》卷六十九、卷七十五",
                "《资治通鉴》卷一百一十二、一百一十三", "赵翼《廿二史札记》卷八、卷十二"]
        for i, r in enumerate(rows):
            draw_text(ctx, r, W / 2, 680 + i * 56, family="serif" if i else "sans", weight="SemiBold" if i else "Bold",
                      size=32 if i else 30, color=C["gold"] if i == 0 else C["ink"], alpha=a * (1 if i else 0.9),
                      anchor="cm")
        cr = ["地图为示意，海岸线取今形　旁白为 AI 合成（Kokoro，Apache-2.0）",
              "地图数据 Natural Earth　字体 Noto Serif/Sans SC（OFL）"]
        for i, r in enumerate(cr):
            draw_text(ctx, r, W / 2, 1040 + i * 44, family="sans", weight="Regular", size=24, color=C["dim"],
                      alpha=a * 0.9, anchor="cm")

    # ══ S0 冷启动 ═════════════════════════════════════════
    def draw_S0(self, ctx, t):
        T = self.T
        te = T.title_start + TITLE_CARD
        assets.draw_woodcut(ctx, clamp(t / te), push=(1.0, 1.12), focus=(650, 980), t_abs=t)
        ts = T.title_start
        # 信息槽：依次替换
        a = fade(t, T.start("s0a") - 0.1, T.start("s0c") - 0.2, 0.6, 0.4)
        draw_text(ctx, "东晋 · 京口", 86, 330, family="serif", weight="Bold", size=50, color=C["ink"], alpha=a,
                  tracking=0.2, shadow=6)
        draw_text(ctx, "今江苏镇江 · 长江南岸", 90, 395, family="sans", weight="Regular", size=30, color=C["dim"],
                  alpha=a, shadow=4)
        tc = T.word("s0c", "刘裕")
        a = fade(t, tc - 0.2, T.start("s0d") - 0.1, 0.4, 0.35)
        draw_text(ctx, "刘裕", 82, 300, family="serif", weight="Black", size=132, color=C["ink"], alpha=a, shadow=8)
        draw_text(ctx, "后来的宋武帝（363—422）", 90, 470, family="sans", weight="Medium", size=32, color=C["gold"],
                  alpha=a, shadow=4)
        # 三无
        t404 = T.word("s0d", "公元")
        x = 86
        for lab, key in (("家世", "没家世"), ("钱", "没钱"), ("名声", "名声也差")):
            tk = T.word("s0d", key)
            a = fade(t, tk - 0.15, t404 - 0.4, 0.3, 0.25)
            w, _ = text_size(lab, "serif", "Black", 76)
            draw_text(ctx, lab, x, 330, family="serif", weight="Black", size=76, color=C["ink"], alpha=a, shadow=6)
            strike(ctx, x - 8, 378, x + w + 8, ease_out(prog(t, tk + 0.25, 0.25)), a, width=7)
            x += w + 56
        # 404 一千多人 → 桓玄
        a = fade(t, t404 - 0.08, T.start("s0e") - 0.1, 0.35, 0.3)
        draw_text(ctx, "404", 82, 300, family="serif", weight="Black", size=132, color=C["red2"], alpha=a, shadow=8)
        draw_text(ctx, "年", 330, 352, family="serif", weight="Black", size=60, color=C["red2"], alpha=a, shadow=6)
        a2 = fade(t, T.word("s0d", "一千多人") - 0.1, T.start("s0e") - 0.1, 0.3, 0.3)
        draw_text(ctx, "一千多人起兵", 90, 480, family="serif", weight="Black", size=58, color=C["ink"], alpha=a2, shadow=6)
        a3 = fade(t, T.word("s0d", "打垮") - 0.1, T.start("s0e") - 0.1, 0.3, 0.3)
        draw_text(ctx, "→ 打垮已称帝的桓玄", 90, 560, family="serif", weight="Black", size=58, color=C["blue2"],
                  alpha=a3, shadow=6)
        # 凭什么？
        te_ = T.start("s0e")
        a = fade(t, te_ - 0.05, ts + 0.2, 0.25, 0.4)
        rect(ctx, 0, 0, W, H, "#080605", 0.45 * a)
        draw_text(ctx, "凭什么？", W / 2, 560, family="serif", weight="Black", size=140, color=C["ink"], alpha=a,
                  anchor="cm", shadow=10, scale=1 + 0.06 * (1 - ease_out(prog(t, te_, 0.6))))

    # ══ S1 寄奴 ═══════════════════════════════════════════
    def draw_S1(self, ctx, t):
        T = self.T
        self.bg(ctx)
        t_books = T.start("s1c") - 0.2
        # 家谱图（s1a–s1b）
        a = fade(t, T.sec_start["S1"] + 0.6, t_books, 0.5, 0.5)
        if a > 0:
            ym = 470
            # 母
            am = ease_out(prog(t, T.word("s1a", "母亲") - 0.2, 0.4)) * a
            name_tile(ctx, 230, ym - 120, "母", "生下他就死了", alpha=am * 0.75, col=C["dim"], w=230)
            # 父
            af = ease_out(prog(t, T.word("s1a", "家里穷") - 0.2, 0.4)) * a
            name_tile(ctx, 520, ym - 120, "父", "家贫 · 请不起奶妈", alpha=af, w=260)
            # 刘裕（婴儿）
            ay = ease_out(prog(t, T.start("s1a") + 0.3, 0.5)) * a
            name_tile(ctx, 375, ym + 140, "刘裕", "刚出生", alpha=ay, col=C["red2"], w=230)
            line(ctx, 230, ym - 20, 375, ym + 140, C["dim"], 2, am * 0.6)
            line(ctx, 520, ym - 20, 375, ym + 140, C["dim"], 2, af * 0.6)
            # 姨母与怀敬
            ai = ease_out(prog(t, T.start("s1b") - 0.1, 0.4)) * a
            name_tile(ctx, 830, ym - 120, "姨母", "刘裕之从母", alpha=ai, col=C["gold2"], w=220)
            ak = ease_out(prog(t, T.word("s1b", "不满一岁") - 0.2, 0.4)) * a
            name_tile(ctx, 830, ym + 140, "刘怀敬", "未满一岁", alpha=ak, w=230)
            # 乳：从怀敬转给刘裕
            t_cut = T.word("s1b", "断了奶")
            line(ctx, 830, ym - 20, 830, ym + 140, C["gold2"], 4, ai * (1 - ease_out(prog(t, t_cut, 0.4))) * 0.9)
            cross(ctx, 830, ym + 62, 22, prog(t, t_cut, 0.3), ai * (1 - prog(t, t_books - 0.6, 0.4)))
            pts = smooth_path([(780, ym - 10), (640, ym + 40), (500, ym + 150)], 10)
            arrow(ctx, pts, C["gold2"], 5, ai, frac=ease_out(prog(t, T.word("s1b", "喂活") - 0.3, 0.6)), head=18)
            draw_text(ctx, "乳", 640, ym + 10, family="serif", weight="Black", size=44, color=C["gold2"],
                      alpha=ai * ease_out(prog(t, T.word("s1b", "喂活") - 0.1, 0.4)), anchor="cm")
            # 寄奴
            aj = ease_out(prog(t, T.word("s1b", "寄奴") - 0.2, 0.4)) * a
            draw_text(ctx, "小名 · 寄奴", 375, ym + 330, family="serif", weight="Black", size=58, color=C["ink"],
                      alpha=aj, anchor="cm", shadow=6)
            draw_text(ctx, "“寄”＝寄养（一般认为）", 375, ym + 400, family="sans", weight="Regular", size=28,
                      color=C["dim"], alpha=aj, anchor="cm")
        # 原文卡
        vquote(ctx, t, T, "s1a", W / 2, 1000, size=62, t_out=T.start("s1b") - 0.1)
        vquote(ctx, t, T, "s1b", 820, 960, size=54, t_out=T.word("s1b", "小名") - 0.1)
        # 两部史书（s1c–s1f）
        a = fade(t, t_books, T.sec_end["S1"], 0.5, 0.3)
        if a > 0:
            for side, (x0, line_id, book, who, col) in enumerate(((70, "s1c", "《宋书》", "南朝 · 沈约撰", C["gold"]),
                                                                    (560, "s1d", "《魏书》", "北齐 · 魏收撰", C["blue"]))):
                ap = ease_out(prog(t, T.start(line_id) - 0.2, 0.5)) * a
                if ap <= 0:
                    continue
                card(ctx, x0, 330, 450, 760, ap, edge=col, edge_alpha=0.8)
                draw_text(ctx, book, x0 + 225, 395, family="serif", weight="Black", size=56, color=col, alpha=ap, anchor="cm")
                draw_text(ctx, who, x0 + 225, 455, family="sans", weight="Regular", size=26, color=C["dim"], alpha=ap, anchor="cm")
                vquote(ctx, t, T, line_id, x0 + 225, 720, size=54, t_out=T.sec_end["S1"], frame=False, src=False, alpha=a)
            # 魏书立场
            ab = ease_out(prog(t, T.word("s1d", "北朝敌国") - 0.1, 0.4)) * a
            draw_seal(ctx, "敌国", 940, 1040, size=92, alpha=ab, rot=0.08, scale=1 + 0.3 * (1 - ease_back(prog(t, T.word("s1d", "北朝敌国"), 0.35))))
            draw_text(ctx, "列传标题：島夷劉裕", 785, 1135, family="serif", weight="SemiBold", size=30, color=C["blue2"],
                      alpha=ab, anchor="cm")
            # 樗蒲
            ad = fade(t, T.word("s1d", "樗蒲是") - 0.1, T.start("s1f") + 0.3, 0.4, 0.4) * a
            icon_dice(ctx, 300, 1170, 70, C["gold"], ad)
            draw_text(ctx, "樗蒲：掷五枚木子的博戏", 300, 1225, family="sans", weight="Regular", size=26, color=C["dim"],
                      alpha=ad, anchor="cm")
        # 结论
        takeaway(ctx, t, T.start("s1f"), T.sec_end["S1"] + 0.3, ["两边立场相反", "都承认：出身最底层"], y=620)

    # ══ S2 马桩 ═══════════════════════════════════════════
    def draw_S2(self, ctx, t):
        T = self.T
        t0 = T.sec_start["S2"]
        # 开头回到马桩（特写）
        aw = 1 - ease_in(prog(t, T.word("s2a", "欠的") - 0.2, 0.6))
        if aw > 0:
            assets.draw_woodcut(ctx, 0.2 + 0.2 * prog(t, t0, 4), push=(1.55, 1.6), focus=(690, 980), t_abs=t)
        self.bg(ctx, alpha=1 - aw)
        # 两种说法
        tA, tB = T.word("s2a", "欠的"), T.start("s2c") - 0.2
        a = fade(t, tA, tB, 0.5, 0.45)
        if a > 0:
            aL = ease_out(prog(t, T.word("s2a", "宋书") - 0.2, 0.4)) * a
            card(ctx, 70, 330, 450, 850, aL, edge=C["gold"])
            draw_text(ctx, "《宋书》", 295, 390, family="serif", weight="Black", size=50, color=C["gold"], alpha=aL, anchor="cm")
            draw_text(ctx, "社钱三万", 295, 470, family="serif", weight="Black", size=62, color=C["ink"], alpha=aL, anchor="cm")
            draw_text(ctx, "乡里祭土地神的公款", 295, 530, family="sans", weight="Regular", size=26, color=C["dim"], alpha=aL, anchor="cm")
            icon_coins(ctx, 295, 640, 56, C["gold"], aL * 0.9)
            vquote(ctx, t, T, "s2a", 295, 900, size=40, frame=False, src=False, t_out=tB, alpha=a)
            aR = ease_out(prog(t, T.start("s2b") - 0.2, 0.4)) * a
            card(ctx, 560, 330, 450, 850, aR, edge=C["red"])
            draw_text(ctx, "《资治通鉴》", 785, 390, family="serif", weight="Black", size=50, color=C["red2"], alpha=aR, anchor="cm")
            draw_text(ctx, "樗蒲赌债", 785, 470, family="serif", weight="Black", size=62, color=C["ink"], alpha=aR, anchor="cm")
            draw_text(ctx, "输了不给钱", 785, 530, family="sans", weight="Regular", size=26, color=C["dim"], alpha=aR, anchor="cm")
            icon_dice(ctx, 785, 640, 60, C["red2"], aR * 0.9)
            vquote(ctx, t, T, "s2b", 785, 850, size=50, frame=False, src=False, t_out=tB, alpha=a)
            ao = ease_out(prog(t, T.word("s2b", "马桩这个") - 0.2, 0.4)) * a
            tag(ctx, "捆在马桩：仅见《通鉴》", 600, 1090, alpha=ao, col=C["red2"], size=28)
            draw_text(ctx, "胡三省注：枊，系马柱也", 785, 1140, family="sans", weight="Regular", size=24,
                      color=C["dim"], alpha=ao * 0.9, anchor="cm")
        # 刁家（s2c）
        tC, tD = T.start("s2c") - 0.2, T.start("s2d") - 0.1
        a = fade(t, tC, tD, 0.5, 0.4)
        if a > 0:
            draw_text(ctx, "刁氏", 90, 360, family="serif", weight="Black", size=84, color=C["ink"], alpha=a, shadow=6)
            draw_text(ctx, "京口豪强", 280, 385, family="serif", weight="Bold", size=44, color=C["gold"], alpha=a)
            # 田：10×10 方格
            af = ease_out(prog(t, T.word("s2c", "有田") - 0.2, 0.6)) * a
            for i in range(100):
                gx, gy = 90 + (i % 10) * 40, 500 + (i // 10) * 40
                ai = clamp(af * 3 - (i / 100) * 2)
                rect(ctx, gx, gy, 34, 34, "#7a6236", ai * 0.85)
            draw_text(ctx, "田 万顷", 290, 930, family="serif", weight="Black", size=44, color=C["ink"], alpha=af, anchor="cm")
            draw_text(ctx, "（一顷＝一百亩）", 290, 980, family="sans", weight="Regular", size=24, color=C["dim"], alpha=af, anchor="cm")
            # 奴婢：点
            ap = ease_out(prog(t, T.word("s2c", "奴婢") - 0.2, 0.6)) * a
            P = self.d_ppl.blob(780, 690, 210, 190)
            self.d_ppl.draw(ctx, P, C["dim"], r=2.6, alpha=ap * 0.85, count=2000 * ap)
            draw_text(ctx, "奴婢 数千人", 780, 930, family="serif", weight="Black", size=44, color=C["ink"], alpha=ap, anchor="cm")
            ah = ease_out(prog(t, T.word("s2c", "豪强") - 0.2, 0.4)) * a
            tag(ctx, "豪强：有地 · 有钱 · 有人，横行一方", 90, 1080, alpha=ah, col=C["gold2"], size=32)
        vquote(ctx, t, T, "s2c", 0, 0, size=1, alpha=0)  # 占位（文字已在信息图中）
        # 门阀 vs 豪强（s2d）
        tE = T.start("s2e") - 0.1
        a = fade(t, tD, tE + 0.3, 0.5, 0.4)
        if a > 0:
            for k, (x, head, tiles, note, col) in enumerate(((290, "豪强", ["刁"], "靠地、钱、私家人马", C["gold"]),
                                                              (790, "门阀", ["王", "谢"], "几百年的世家\n做官靠出身", C["ink"]))):
                ak = ease_out(prog(t, tD + k * 0.5, 0.5)) * a
                draw_text(ctx, head, x, 420, family="serif", weight="Black", size=72, color=col, alpha=ak, anchor="cm")
                for j, tt in enumerate(tiles):
                    xx = x + (j - (len(tiles) - 1) / 2) * 170
                    card(ctx, xx - 70, 520, 140, 140, ak, edge=col)
                    draw_text(ctx, tt, xx, 590, family="serif", weight="Black", size=88, color=col, alpha=ak, anchor="cm")
                for j, nl in enumerate(note.split("\n")):
                    draw_text(ctx, nl, x, 730 + j * 48, family="sans", weight="Medium", size=34, color=C["dim"], alpha=ak, anchor="cm")
            line(ctx, W / 2, 380, W / 2, 860, C["faint"], 1.5, a * 0.6)
        # 王谧（s2e–s2f）
        a = fade(t, tE, T.start("s2g"), 0.5, 0.4)
        if a > 0:
            name_tile(ctx, W / 2, 320, "王谧", "琅邪王氏 · 王导之孙", alpha=a, col=C["gold2"], w=380)
            vquote(ctx, t, T, "s2e", W / 2, 760, size=62, t_out=T.word("s2e", "这回") - 0.4)
            ah = fade(t, T.word("s2e", "这回") + 0.15, T.word("s2e", "从此") - 0.2, 0.4, 0.3)
            draw_text(ctx, "责逵 · 释之 · 代之还直", W / 2, 760, family="serif", weight="Black", size=58, color=C["ink"],
                      alpha=ah, anchor="cm", shadow=6)
            draw_text(ctx, "——《通鉴》卷一百一十三", W / 2, 840, family="serif", weight="SemiBold", size=28, color=C["gold"],
                      alpha=ah, anchor="cm")
            tf = T.start("s2f")
            an = ease_out(prog(t, tf - 0.1, 0.4)) * a
            tag(ctx, "《宋书》：王谧「密以钱代还」", 90, 545, alpha=an, col=C["gold"], size=32)
            # 恨 / 德
            tq = T.word("s2e", "从此")
            ar = ease_out(prog(t, tq, 0.5)) * a
            name_tile(ctx, W / 2, 700, "刘裕", None, alpha=ar, col=C["red2"], w=200)
            name_tile(ctx, 230, 960, "刁逵", None, alpha=ar, col=C["dim"], w=200)
            name_tile(ctx, 850, 960, "王谧", None, alpha=ar, col=C["gold2"], w=200)
            arrow(ctx, [(480, 790), (300, 950)], C["red"], 5, ar, frac=ease_out(prog(t, T.word("s2e", "恨透"), 0.5)))
            draw_text(ctx, "憾", 360, 850, family="serif", weight="Black", size=56, color=C["red2"],
                      alpha=ar * ease_out(prog(t, T.word("s2e", "恨透"), 0.4)), anchor="cm")
            arrow(ctx, [(600, 790), (780, 950)], C["gold2"], 5, ar, frac=ease_out(prog(t, T.word("s2e", "记住"), 0.5)))
            draw_text(ctx, "德", 720, 850, family="serif", weight="Black", size=56, color=C["gold2"],
                      alpha=ar * ease_out(prog(t, T.word("s2e", "记住"), 0.4)), anchor="cm")
            draw_text(ctx, "《通鉴》：裕深憾逵而德谧", W / 2, 1110, family="serif", weight="SemiBold", size=30, color=C["gold"],
                      alpha=ar * ease_out(prog(t, T.word("s2e", "记住"), 0.4)), anchor="cm")
        takeaway(ctx, t, T.start("s2g"), T.sec_end["S2"] + 0.3, ["底层人往上走", "得有人看得上他"], y=620)

    # ══ S3 北府 ═══════════════════════════════════════════
    V3 = MapView(120.1, 31.0, 290, W / 2, 900)

    def map_label(self, ctx, view, name, alpha, side="r", col=None, size=34, modern=True, dx=0, dy=0, dot=7):
        x, y = view.place(name)
        circle(ctx, x, y, dot, col or C["ink"], alpha)
        circle(ctx, x, y, dot + 6, col or C["ink"], alpha * 0.4, stroke=True, width=1.5)
        sgn = 1 if side == "r" else -1
        anc = "lm" if side == "r" else "rm"
        draw_text(ctx, name, x + sgn * (dot + 12) + dx, y + dy, family="sans", weight="Bold", size=size,
                  color=col or C["ink"], alpha=alpha, anchor=anc, shadow=4)
        if modern and name in MODERN:
            draw_text(ctx, MODERN[name], x + sgn * (dot + 12) + dx, y + dy + size * 0.95, family="sans", weight="Regular",
                      size=int(size * 0.68), color=C["dim"], alpha=alpha, anchor=anc, shadow=3)

    def draw_S3(self, ctx, t):
        T = self.T
        t0 = T.sec_start["S3"]
        # 镜头：总览 → 吴 → 海盐 → 总览
        Vall = self.V3
        Vwu = MapView(120.55, 31.2, 520, W / 2, 760)
        Vhy = MapView(120.93, 30.5, 900, W / 2, 760)
        tc, td, te = T.start("s3c") - 0.4, T.start("s3d") - 0.2, T.start("s3e") - 0.4
        if t < tc:
            v = Vall
        elif t < td:
            v = MapView.blend(Vall, Vwu, ease_io(prog(t, tc, 1.4)))
        elif t < te:
            v = MapView.blend(Vwu, Vall, ease_io(prog(t, td, 1.0)))
        else:
            v = MapView.blend(Vall, Vhy, ease_io(prog(t, te, 1.4)))
        assets.draw_map(ctx, v)
        am = 1.0
        # 地名
        for n, side in (("建康", "l"), ("京口", "r"), ("吴", "r"), ("海盐", "r"), ("山阴", "l"), ("句章", "l")):
            self.map_label(ctx, v, n, am * 0.95, side=side, size=34 if n in ("京口", "建康") else 30)
        # 京口高亮
        kx, ky = v.place("京口")
        pa = fade(t, t0 + 0.8, T.start("s3c"), 0.6, 0.6)
        for k in range(3):
            ph = ((t - t0) * 0.6 + k / 3) % 1
            circle(ctx, kx, ky, 12 + ph * 60, C["red2"], pa * (1 - ph) * 0.8, stroke=True, width=3)
        # 北府兵说明卡
        a = fade(t, T.start("s3a") + 0.6, T.start("s3c") - 0.2, 0.5, 0.4)
        if a > 0:
            card(ctx, 70, 300, 940, 210, a, edge=C["red"])
            draw_text(ctx, "北府兵", 110, 360, family="serif", weight="Black", size=60, color=C["red2"], alpha=a, anchor="lm")
            draw_text(ctx, "京口招募的北方流民", 330, 345, family="sans", weight="Medium", size=34, color=C["ink"], alpha=a, anchor="lm")
            ab = ease_out(prog(t, T.word("s3a", "淝水"), 0.4)) * a
            draw_text(ctx, "淝水之战（383）的主力", 330, 400, family="sans", weight="Medium", size=34, color=C["gold2"], alpha=ab, anchor="lm")
            ab2 = ease_out(prog(t, T.start("s3b"), 0.4)) * a
            draw_text(ctx, "京口距都城建康很近", 330, 455, family="sans", weight="Medium", size=34, color=C["ink"], alpha=ab2, anchor="lm")
        # 京口—建康 括线
        ab = fade(t, T.start("s3b"), T.start("s3c") - 0.2, 0.5, 0.4)
        if ab > 0:
            x1, y1 = v.place("建康"); x2, y2 = v.place("京口")
            line(ctx, x1, y1 - 40, x2, y2 - 40, C["gold2"], 3, ab, dash=[10, 8])
        # 399：吴附近 侦察
        a = fade(t, T.start("s3c"), T.start("s3d") - 0.1, 0.5, 0.4)
        if a > 0:
            wx, wy = v.place("吴")
            cx, cy = wx - 130, wy - 140
            Pg = self.d_gray_300.blob(cx + 40, cy - 30, 120, 90)
            Pr = self.d_red_30.blob(cx - 140, cy + 80, 22, 22)
            tm = T.word("s3c", "撞上")
            Pg2 = self.d_gray_300.lerp(Pg + np.array([200, -120]), Pg, t, tm - 0.6, 1.0, spread=0.3)
            self.d_gray_300.draw(ctx, Pg2, C["gray"], r=3.4, alpha=a)
            self.d_red_30.draw(ctx, Pr, C["red2"], r=4.2, alpha=a)
            draw_text(ctx, "孙恩军 数千", cx + 40, cy - 160, family="sans", weight="Bold", size=32, color=C["ink"], alpha=a, anchor="cm", shadow=4)
            draw_text(ctx, "刘裕 数十人", cx - 140, cy + 140, family="sans", weight="Bold", size=32, color=C["red2"], alpha=a, anchor="cm", shadow=4)
            draw_text(ctx, "399", 90, 360, family="serif", weight="Black", size=96, color=C["ink"], alpha=a, shadow=6)
            vquote(ctx, t, T, "s3c", 860, 980, size=50)
        # 军纪对比（s3d）
        a = fade(t, T.start("s3d") - 0.1, T.start("s3e") - 0.3, 0.5, 0.4)
        if a > 0:
            rect(ctx, 0, 0, W, H, "#0b0806", 0.7 * a)
            for k, (x0, title, col) in enumerate(((70, "官军：纵兵抢掠", C["gray"]), (560, "刘裕：法令明整", C["red2"]))):
                card(ctx, x0, 340, 450, 470, a, edge=col)
                draw_text(ctx, title, x0 + 225, 395, family="sans", weight="Bold", size=36, color=col, alpha=a, anchor="cm")
                if k == 0:
                    for j in range(4):
                        icon_house(ctx, x0 + 80 + j * 100, 720, 30, "#3b3328", a)
                    P0 = self.d_gray_80.grid(x0 + 225, 560, 10, 22)
                    P1 = self.d_gray_80.ring(x0 + 225, 690, 40, 190)
                    P = self.d_gray_80.lerp(P0, P1, t, T.start("s3d") + 0.3, 1.2, spread=0.6)
                    self.d_gray_80.draw(ctx, P, C["gray"], r=4, alpha=a)
                else:
                    P = self.d_gray_80.grid(x0 + 225, 600, 10, 22)
                    self.d_gray_80.draw(ctx, P, C["red2"], r=4, alpha=a)
            vquote(ctx, t, T, "s3d", W / 2, 1040, size=50)
        # 海盐（s3e）
        a = fade(t, T.start("s3e") + 0.2, T.start("s3f") + 0.2, 0.5, 0.4)
        if a > 0:
            hx, hy = v.place("海盐")
            fx, fy = hx - 30, hy - 230
            # 小城
            set_col(ctx, "#5b4a35", a); ctx.rectangle(fx - 110, fy - 80, 220, 160); ctx.fill()
            set_col(ctx, "#1a140f", a); ctx.rectangle(fx - 90, fy - 60, 180, 120); ctx.fill()
            tl = T.word("s3e", "几个病弱")
            for k in range(3):
                icon_person(ctx, fx - 40 + k * 40, fy - 80, 14, C["dim"], a * ease_out(prog(t, tl + k * 0.1, 0.3)))
            # 旗子倒下
            fl = ease_out(prog(t, T.word("s3e", "藏起"), 0.6))
            for k in range(4):
                ang = -math.pi / 2 + fl * 1.35
                bx, by = fx - 100 + k * 66, fy - 80
                set_col(ctx, C["red"], a)
                ctx.set_line_width(3); ctx.move_to(bx, by); ctx.line_to(bx + math.cos(ang) * 40, by + math.sin(ang) * 40); ctx.stroke()
            # 敌军涌来，随后被反击打散
            tg = T.word("s3e", "一松懈")
            tb = T.word("s3e", "打垮")
            P0 = self.d_gray_300.blob(fx + 330, fy + 140, 120, 90)
            P1 = self.d_gray_300.blob(fx + 150, fy + 40, 80, 60)
            P = self.d_gray_300.lerp(P0, P1, t, tg - 0.8, 1.0, spread=0.3)
            P = self.d_gray_300.lerp(P, self.d_gray_300.scatter_from(P1, fx, fy, 380), t, tb - 0.1, 1.2, spread=0.4)
            self.d_gray_300.draw(ctx, P, C["gray"], r=3.4, alpha=a * (1 - 0.6 * prog(t, tb + 0.4, 1.0)))
            Pr0 = self.d_red_30.blob(fx, fy, 50, 40)
            Pr1 = self.d_red_30.blob(fx + 130, fy + 40, 60, 50)
            Pr = self.d_red_30.lerp(Pr0, Pr1, t, tb - 0.2, 0.5, spread=0.2)
            self.d_red_30.draw(ctx, Pr, C["red2"], r=4.4, alpha=a)
            tag(ctx, "偃旗匿众 · 羸疾登城（《宋书》）", 90, 360, alpha=a, col=C["gold2"], size=32)
        takeaway(ctx, t, T.start("s3f"), T.sec_end["S3"] + 0.3, ["带头冲 · 不扰民 · 有脑子", "这是他唯一的本钱"], y=620, size=54)

    # ══ S4 等 ═════════════════════════════════════════════
    def draw_S4(self, ctx, t):
        T = self.T
        t0 = T.sec_start["S4"]
        tb = T.start("s4b") - 0.2
        # 桓玄东下（宽地图）
        a = fade(t, t0, tb + 0.3, 0.5, 0.5)
        if a > 0:
            v = MapView(115.5, 30.9, 118, W / 2, 800)
            assets.draw_map(ctx, v, alpha=a)
            pts = smooth_path([v(*p) for p in assets.YANGTZE_PATH], 8)
            polyline(ctx, pts, C["river"], 5, a * 0.9)
            arrow(ctx, pts, C["blue2"], 8, a, frac=ease_io(prog(t, T.start("s4a") + 0.4, 2.6)), head=24)
            for n, lab, side in (("江陵", "江陵（荆州）", "r"), ("建康", "建康", "l")):
                x, y = v.place(n)
                circle(ctx, x, y, 8, C["ink"], a)
                draw_text(ctx, lab, x + (18 if side == "r" else -18), y - 30, family="sans", weight="Bold", size=34,
                          color=C["ink"], alpha=a, anchor="lm" if side == "r" else "rm", shadow=4)
            draw_text(ctx, "402", 90, 360, family="serif", weight="Black", size=96, color=C["blue2"], alpha=a, shadow=6)
            ah = ease_out(prog(t, T.word("s4a", "桓温"), 0.4)) * a
            name_tile(ctx, W / 2, 1000, "桓玄", "桓温之子 · 门第高", alpha=ah, col=C["blue2"], w=360)
        self.bg(ctx, alpha=ease_out(prog(t, tb, 0.5)))
        # 刘牢之：一人三反
        a = fade(t, tb, T.start("s4c") - 0.1, 0.5, 0.4)
        if a > 0:
            name_tile(ctx, W / 2, 330, "刘牢之", "北府主帅", alpha=a, col=C["ink"], w=330)
            items = [("398", "反王恭"), ("402", "反司马元显"), ("402", "又想反桓玄")]
            keys = [T.word("s4b", "投降") - 0.6, T.word("s4b", "投降"), T.word("s4b", "又想反")]
            for k, ((yr, txt), tk) in enumerate(zip(items, keys)):
                ak = ease_out(prog(t, tk, 0.4)) * a
                y = 520 + k * 86
                draw_text(ctx, yr, 300, y, family="serif", weight="Black", size=44, color=C["gold"], alpha=ak, anchor="rm")
                pts = [(330, y), (420, y)]
                arrow(ctx, pts, C["dim"], 4, ak, frac=1, head=12)
                draw_text(ctx, txt, 440, y, family="sans", weight="Bold", size=40, color=C["ink"], alpha=ak, anchor="lm")
            vquote(ctx, t, T, "s4b", W / 2, 1010, size=56, t_out=T.word("s4b", "众人散去"))
            # 众叛亲离
            ts_ = T.word("s4b", "众人散去")
            P0 = self.d_crowd.blob(W / 2, 960, 230, 120)
            P = self.d_crowd.lerp(P0, self.d_crowd.scatter_from(P0, W / 2, 960, 600), t, ts_, 1.6, spread=0.5)
            ad = ease_out(prog(t, ts_ - 0.4, 0.4)) * (1 - prog(t, ts_ + 0.8, 1.2)) * a
            self.d_crowd.draw(ctx, P, C["ink"], r=4, alpha=ad)
            ae = ease_out(prog(t, T.word("s4b", "上吊"), 0.4)) * a
            draw_text(ctx, "自缢于新洲", W / 2, 1080, family="serif", weight="Black", size=52, color=C["dim"], alpha=ae, anchor="cm")
        # 刘裕与何无忌
        a = fade(t, T.start("s4c") - 0.1, T.start("s4e") - 0.1, 0.5, 0.4)
        if a > 0:
            name_tile(ctx, 300, 330, "刘裕", None, alpha=a, col=C["red2"], w=200)
            name_tile(ctx, 780, 330, "何无忌", "刘牢之外甥", alpha=a, w=260)
            line(ctx, 400, 375, 650, 375, C["dim"], 2, a, dash=[8, 8])
            vquote(ctx, t, T, "s4c", W / 2, 800, size=56, t_out=T.start("s4d") - 0.1)
            # 桓玄评语（只上屏，不朗读）
            ad = fade(t, T.start("s4d") - 0.1, T.start("s4e") - 0.1, 0.4, 0.4)
            if ad > 0:
                vquote(ctx, t, T, "s4d", W / 2, 820, size=64)
                tag(ctx, "桓玄评刘裕（对王谧语）", 260, 1120, alpha=ad, col=C["blue2"], size=30)
        # 兵与心
        a = fade(t, T.start("s4e") - 0.1, T.sec_end["S4"] + 0.2, 0.5, 0.3)
        if a > 0:
            name_tile(ctx, 230, 330, "桓玄", None, alpha=a, col=C["blue2"], w=200)
            name_tile(ctx, 850, 330, "刘裕", None, alpha=a, col=C["red2"], w=200)
            P0 = self.d_crowd.blob(W / 2, 720, 170, 130)
            P1 = self.d_crowd.blob(250, 720, 150, 120)
            tk = T.word("s4e", "接手")
            P = self.d_crowd.lerp(P0, P1, t, tk, 1.2, spread=0.4)
            self.d_crowd.draw(ctx, P, C["blue2"], r=4.5, alpha=a)
            # 心：红线连回刘裕
            ah = ease_out(prog(t, T.word("s4e", "心没拿到") - 0.2, 0.6)) * a
            for k in range(0, 160, 9):
                x0, y0 = P[k]
                polyline(ctx, smooth_path([(x0, y0), ((x0 + 850) / 2, y0 - 120), (850, 430)], 6), C["red"], 1.2, ah * 0.55)
            draw_text(ctx, "兵", 250, 920, family="serif", weight="Black", size=64, color=C["blue2"], alpha=a, anchor="cm")
            draw_text(ctx, "心", 850, 560, family="serif", weight="Black", size=64, color=C["red2"], alpha=ah, anchor="cm")
            # 北府老将被杀
            ak = ease_out(prog(t, T.word("s4e", "老将") - 0.3, 0.4)) * a
            names = ["高素", "竺谦之", "竺朗之", "刘袭", "刘季武"]
            for j, nm in enumerate(names):
                x = 130 + j * 205
                draw_text(ctx, nm, x, 1040, family="serif", weight="Bold", size=34, color=C["dim"], alpha=ak, anchor="cm")
                w_, _ = text_size(nm, "serif", "Bold", 34)
                strike(ctx, x - w_ / 2 - 6, 1040, x + w_ / 2 + 6, prog(t, T.word("s4e", "老将") + j * 0.08, 0.25), ak, width=4)
            draw_text(ctx, "桓玄所杀北府旧将（《通鉴》卷一一二）", W / 2, 1110, family="sans", weight="Regular", size=26,
                      color=C["dim"], alpha=ak * 0.9, anchor="cm")
            aw = fade(t, T.word("s4e", "不急着") - 0.2, T.sec_end["S4"] + 0.2, 0.4, 0.3)
            draw_text(ctx, "等", 850, 760, family="serif", weight="Black", size=150, color=C["ink"], alpha=aw, anchor="cm", shadow=8)

    # ══ S5 起兵 ═══════════════════════════════════════════
    def draw_S5(self, ctx, t):
        T = self.T
        self.bg(ctx)
        t0 = T.sec_start["S5"]
        # 时间线
        a = fade(t, T.start("s5a") - 0.1, T.start("s5b") - 0.1, 0.5, 0.4)
        if a > 0:
            line(ctx, 120, 640, 960, 640, C["faint"], 3, a)
            for k, (x, yr, mon, txt, col, key) in enumerate(((260, "403", "十二月", "桓玄称帝", C["blue2"], "篡位"),
                                                             (800, "404", "二月", "刘裕起兵", C["red2"], "第二年"))):
                ak = ease_out(prog(t, T.word("s5a", key) - 0.2, 0.4)) * a
                circle(ctx, x, 640, 12, col, ak)
                draw_text(ctx, yr, x, 520, family="serif", weight="Black", size=84, color=col, alpha=ak, anchor="cm")
                draw_text(ctx, mon, x, 590, family="sans", weight="Medium", size=32, color=C["dim"], alpha=ak, anchor="cm")
                draw_text(ctx, txt, x, 715, family="serif", weight="Black", size=50, color=C["ink"], alpha=ak, anchor="cm")
                if k == 0:
                    icon_crown(ctx, x, 800, 60, C["blue2"], ak)
        # 27 → 100余
        tb, tc_, td = T.start("s5b"), T.start("s5c"), T.start("s5d")
        a = fade(t, tb - 0.15, td - 0.1, 0.4, 0.4)
        if a > 0:
            n27 = ease_out(prog(t, tb + 0.2, 0.6))
            num = "27" if t < tc_ + 0.4 else "100余"
            sc = 1 + 0.15 * (1 - ease_back(prog(t, tc_ + 0.4, 0.4))) if t >= tc_ + 0.4 else 1.0
            big_number(ctx, num, W / 2, 480, size=200, alpha=a, scale=sc)
            draw_text(ctx, "同谋" if t < tc_ + 0.4 else "愿从者", W / 2, 640, family="sans", weight="Bold", size=40,
                      color=C["ink"], alpha=a, anchor="cm")
            P = self.d_red_small.blob(W / 2, 890, 170, 150)
            cnt = 27 * n27 + 83 * ease_out(prog(t, tc_ + 0.3, 0.9))
            self.d_red_small.draw(ctx, P, C["red2"], r=7, alpha=a, count=cnt)
            tag(ctx, "《宋书》卷一", W / 2, 1120, alpha=a * 0.9, col=C["gold"], size=28, anchor="cm")
        # 城门
        te = T.start("s5e") - 0.1
        a = fade(t, td - 0.15, te, 0.4, 0.4)
        if a > 0:
            op = ease_io(prog(t, T.start("s5d") + 0.1, 0.9))
            icon_gate(ctx, W / 2, 1000, 520, 380, "#4a3d2e", a, open_=op)
            draw_text(ctx, "京口", W / 2, 520, family="serif", weight="Black", size=56, color=C["ink"], alpha=a, anchor="cm")
            draw_text(ctx, "天一亮 · 城门开", W / 2, 400, family="sans", weight="Medium", size=34, color=C["dim"], alpha=a, anchor="cm")
            tw = T.word("s5d", "冲进城")
            P0 = self.d_red_small.blob(W / 2, 1150, 260, 60)
            P1 = self.d_red_small.blob(W / 2, 880, 60, 60)
            P = self.d_red_small.lerp(P0, P1, t, tw - 0.3, 0.9, spread=0.5)
            self.d_red_small.draw(ctx, P, C["red2"], r=6, alpha=a * (1 - prog(t, tw + 0.9, 0.5)))
            ah = ease_out(prog(t, T.word("s5d", "何无忌") - 0.1, 0.4)) * a
            tag(ctx, "何无忌：穿传诏服，假称奉诏", 90, 1210, alpha=ah, col=C["gold2"], size=30)
            ax = ease_out(prog(t, T.word("s5d", "桓修") - 0.1, 0.3)) * a
            name_tile(ctx, 860, 560, "桓修", "守将", alpha=ax, col=C["blue2"], w=180)
            cross(ctx, 860, 610, 50, prog(t, T.word("s5d", "桓修") + 0.1, 0.3), ax)
        # 周氏
        tf = T.start("s5f")
        a = fade(t, te, T.start("s5g") - 0.1, 0.4, 0.4)
        if a > 0:
            name_tile(ctx, W / 2, 330, "周氏", "孟昶之妻 · 倾家财", alpha=a, col=C["gold2"], w=380)
            vquote(ctx, t, T, "s5e", W / 2, 780, size=64, t_out=tf + 0.1)
            # 红布 → 军袍
            ar = fade(t, tf - 0.1, T.start("s5g") - 0.1, 0.4, 0.3)
            if ar > 0:
                rng = np.random.default_rng(5)
                tr = T.word("s5f", "红布")
                for k in range(24):
                    gx, gy = 170 + (k % 8) * 105, 620 + (k // 8) * 170
                    sx, sy = rng.uniform(-200, W + 200), rng.uniform(300, 600)
                    p = ease_io(prog(t, tr - 0.8 + k * 0.03, 1.1))
                    x, y = lerp(sx, gx, p), lerp(sy, gy, p)
                    if p < 0.98:
                        ctx.save(); ctx.translate(x, y); ctx.rotate((1 - p) * (k % 5 - 2))
                        rect(ctx, -26, -18, 52, 36, C["red"], ar * 0.9); ctx.restore()
                    else:
                        icon_robe(ctx, gx, gy, 46, C["red"], ar)
                draw_text(ctx, "家中绛色之物 → 军士袍", W / 2, 1150, family="serif", weight="Black", size=44,
                          color=C["red2"], alpha=ar * ease_out(prog(t, T.word("s5f", "全缝成"), 0.4)), anchor="cm")
        # 人数阶梯
        tg = T.start("s5g")
        a = fade(t, tg - 0.1, T.sec_end["S5"] + 0.2, 0.4, 0.3)
        if a > 0:
            steps = [("1000余", "《宋书》：百姓愿从", T.word("s5g", "一千多人"), 1000),
                     ("1700", "《通鉴》：带出京口", T.word("s5g", "一千七百人"), 1700),
                     ("1848", "请功名单", T.word("s5g", "一千八百四十八人"), 1700)]
            cur = 0
            for k, (num, src, tk, n) in enumerate(steps):
                ak = ease_out(prog(t, tk - 0.2, 0.4)) * a
                y = 360 + k * 112
                col = C["red2"] if k < 2 else C["gold2"]
                draw_text(ctx, num, 120, y, family="serif", weight="Black", size=84, color=col, alpha=ak, anchor="lm")
                draw_text(ctx, src, 450, y + 6, family="sans", weight="Medium", size=34, color=C["ink"], alpha=ak, anchor="lm")
                if t >= tk:
                    cur = n
            P = self.d_red_1700.grid(W / 2, 960, 50, 10.5)
            prev = 0 if t < steps[0][2] else (1000 if t < steps[1][2] else 1700)
            tk_ = steps[0][2] if t < steps[1][2] else steps[1][2]
            base = 0 if t < steps[1][2] else 1000
            cnt = base + (prev - base) * ease_out(prog(t, tk_ - 0.1, 0.8))
            self.d_red_1700.draw(ctx, P, C["red2"], r=3.4, alpha=a, count=cnt)
            draw_text(ctx, "每点 1 人", 900, 1170, family="sans", weight="Regular", size=24, color=C["dim"], alpha=a, anchor="rm")
            ah = fade(t, T.start("s5h") + 0.6, T.sec_end["S5"] + 0.2, 0.4, 0.3)
            if ah > 0:
                rect(ctx, 0, 0, W, H, "#0b0806", 0.55 * ah)
                draw_text(ctx, "全部家当", 300, 620, family="serif", weight="Black", size=72, color=C["red2"], alpha=ah, anchor="cm", shadow=6)
                draw_text(ctx, "对", W / 2, 620, family="serif", weight="Bold", size=48, color=C["dim"], alpha=ah, anchor="cm")
                icon_crown(ctx, 790, 560, 70, C["blue2"], ah)
                draw_text(ctx, "皇帝桓玄", 790, 680, family="serif", weight="Black", size=60, color=C["blue2"], alpha=ah, anchor="cm", shadow=6)

    # ══ S6 胜负手 ═════════════════════════════════════════
    V6 = MapView(119.13, 32.12, 1050, W / 2, 720)

    def draw_S6(self, ctx, t):
        T = self.T
        t0 = T.sec_start["S6"]
        V = self.V6
        Vfz = MapView(118.86, 32.08, 2600, W / 2, 760)    # 覆舟山特写
        tb, tc, te, tf, tg, th = (T.start(k) for k in ("s6b", "s6c", "s6e", "s6f", "s6g", "s6h"))
        t_ring = T.word("s6b", "罗落桥") - 0.3
        # 地图视图
        if t < te - 0.3:
            v = V
        else:
            v = MapView.blend(V, Vfz, ease_io(prog(t, te - 0.3, 1.6)))
        assets.draw_map(ctx, v)
        for n, side, dy in (("建康", "l", 30), ("京口", "r", 0), ("江乘", "r", -40), ("罗落桥", "r", 34), ("竹里", "r", 40),
                            ("覆舟山", "r", -36), ("石头城", "l", -10)):
            x, y = v.place(n)
            al = 0.95 if n in ("建康", "京口") else fade(t, T.start("s6b") - 0.2 if n in ("江乘", "竹里", "罗落桥") else te, None)
            circle(ctx, x, y, 6, C["ink"], al)
            draw_text(ctx, n, x + (14 if side == "r" else -14), y + dy, family="sans", weight="Bold", size=30,
                      color=C["ink"], alpha=al, anchor="lm" if side == "r" else "rm", shadow=4)
        # 桓玄两万（每点≈10人）
        fzx, fzy = v.place("东陵")
        Pb = self.d_blue_2000.blob(fzx - 10, fzy + 8, 0.12 * v.k, 0.1 * v.k)
        ab = fade(t, T.word("s6e", "两万人") - 0.3, None, 0.6)
        disperse = ease_in(prog(t, T.word("s6g", "两万人") - 0.6, 2.2))
        alphas = None
        col_core = None
        if t >= tf - 0.2:
            # 北府人：亮起红芯，随后“散开”而不是倒下
            Pd = self.d_blue_2000.scatter_from(Pb, fzx + 0.03 * v.k, fzy - 0.02 * v.k, 0.11 * v.k)
            Pb = self.d_blue_2000.lerp(Pb, Pd, t, T.word("s6g", "两万人") - 0.7, 2.4, spread=1.0)
            alphas = 1 - 0.85 * np.clip((t - T.word("s6g", "两万人") - self.d_blue_2000.r[:, 2] * 1.0) / 1.6, 0, 1)
        self.d_blue_2000.draw(ctx, Pb, C["blue"], r=max(1.6, min(3.6, v.k / 520)), alpha=ab, alphas=alphas)
        if t >= tf:
            ar = ease_out(prog(t, T.word("s6f", "北府人") - 0.2, 0.6)) * (1 - disperse)
            rr = max(1.0, min(2.0, v.k / 1000))
            set_col(ctx, C["red2"], ar * 0.95)
            for i in np.nonzero(self.beifu_mask)[0]:
                ctx.move_to(Pb[i, 0] + rr, Pb[i, 1]); ctx.arc(Pb[i, 0], Pb[i, 1], rr, 0, 2 * math.pi)
            ctx.fill()
        bx, by = v.place("覆舟山")
        lab_a = fade(t, T.word("s6e", "两万人") - 0.3, tf + 0.2, 0.4, 0.4)
        draw_text(ctx, "桓玄军 约两万", fzx - 0.02 * v.k, fzy + 0.17 * v.k, family="sans", weight="Bold", size=34,
                  color=C["blue2"], alpha=lab_a, anchor="cm", shadow=4)
        draw_text(ctx, "（每点约十人）", fzx - 0.02 * v.k, fzy + 0.17 * v.k + 44, family="sans", weight="Regular",
                  size=24, color=C["dim"], alpha=lab_a, anchor="cm", shadow=3)
        # 刘裕军：沿路线推进
        route = [PLACES["京口"], PLACES["竹里"], PLACES["江乘"], PLACES["罗落桥"], (118.86, 32.08)]
        rp = [v(*p) for p in route]
        rp_s = smooth_path(rp, 8)
        fr = 0.0
        if t >= tb:
            fr = 0.45 * ease_io(prog(t, tb + 0.2, 2.2))      # 京口 → 江乘
            fr += 0.30 * ease_io(prog(t, t_ring - 0.5, 1.2))   # → 罗落桥
            fr += 0.25 * ease_io(prog(t, te - 0.2, 1.6))       # → 覆舟山东
        if t >= tb:
            arrow(ctx, rp_s, C["red2"], 6, 0.9, frac=fr, head=18)
        rx, ry, _ = point_along(rp_s, fr)
        Pr = self.d_red_170.blob(rx, ry, 0.03 * v.k, 0.03 * v.k)
        charge = ease_in(prog(t, tg - 0.1, 1.4))
        if t >= tg - 0.1:
            Pr = Pr + np.array([-0.06 * v.k * charge, 0.01 * v.k * charge])
        self.d_red_170.draw(ctx, Pr, C["red2"], r=max(2.0, min(4.0, v.k / 450)), alpha=fade(t, T.start("s6a") + 0.4, None))
        draw_text(ctx, "刘裕 约1700", rx + 0.04 * v.k, ry - 0.05 * v.k, family="sans", weight="Bold", size=32,
                  color=C["red2"], alpha=fade(t, T.start("s6a") + 0.4, tb + 0.6) * 0.95, anchor="lm", shadow=4)
        # 日期标签
        a = fade(t, tb - 0.1, te - 0.4, 0.4, 0.3) * (1 - fade(t, t_ring + 0.3, te - 0.2, 0.3, 0.4))
        draw_text(ctx, "三月初一", 90, 360, family="serif", weight="Black", size=72, color=C["ink"], alpha=a, shadow=6)
        a = fade(t, te - 0.1, None, 0.4)
        draw_text(ctx, "三月初二", 90, 360, family="serif", weight="Black", size=72, color=C["ink"], alpha=a * (1 - prog(t, th - 0.2, 0.3)), shadow=6)
        # 江乘：吴甫之
        jx, jy = v.place("江乘")
        tj = T.word("s6b", "斩了")
        P0 = self.d_blue_60.blob(jx - 30, jy + 10, 40, 30)
        P = self.d_blue_60.lerp(P0, self.d_blue_60.scatter_from(P0, jx, jy, 160), t, tj, 1.2, spread=0.4)
        aj = fade(t, tb + 0.4, tj + 1.4, 0.4, 0.5)
        self.d_blue_60.draw(ctx, P, C["blue"], r=3.2, alpha=aj)
        draw_text(ctx, "斩吴甫之", jx + 20, jy - 70, family="serif", weight="Black", size=40, color=C["red2"],
                  alpha=aj * ease_out(prog(t, tj, 0.3)), anchor="lm", shadow=5)
        # 罗落桥：被围（特写图解）
        a = fade(t, t_ring + 0.3, te - 0.2, 0.5, 0.4)
        if a > 0:
            rect(ctx, 0, 0, W, H, "#0b0806", 0.84 * a)
            cx, cy = W / 2 - 40, 900
            icon_tree(ctx, cx, cy + 40, 90, "#3d3024", a)
            Pc = self.d_red_30.blob(cx, cy, 26, 22)
            self.d_red_30.draw(ctx, Pc, C["red2"], r=5, alpha=a)
            ring = self.d_blue_300.ring(cx, cy, 120, 230)
            t_bi = T.word("s6d", "辟易")
            back = ease_out(prog(t, t_bi - 0.1, 0.5))
            ring2 = self.d_blue_300.ring(cx, cy, 200, 330)
            Pring = ring + (ring2 - ring) * back
            t_arrow = T.word("s6d", "一箭正中")
            Psc = self.d_blue_300.scatter_from(ring2, cx, cy, 420)
            Pring = self.d_blue_300.lerp(Pring, Psc, t, t_arrow + 0.4, 1.4, spread=0.5)
            self.d_blue_300.draw(ctx, Pring, C["blue"], r=4, alpha=a * (1 - 0.7 * prog(t, t_arrow + 0.8, 1.0)))
            draw_text(ctx, "罗落桥", 86, 470, family="serif", weight="Black", size=58, color=C["ink"], alpha=a, shadow=5)
            draw_text(ctx, "皇甫敷围之数重", 90, 545, family="sans", weight="Bold", size=34, color=C["blue2"], alpha=a, shadow=4)
            at = ease_out(prog(t, T.word("s6b", "背靠大树") - 0.2, 0.4)) * a
            tag(ctx, "倚大树挺战", 86, 615, alpha=at, col=C["red2"], size=32)
            draw_text(ctx, "胡三省注：挺身独战也", 90, 668, family="sans", weight="Regular", size=24, color=C["dim"], alpha=at)
            # 一箭
            pa = prog(t, t_arrow - 0.2, 0.5)
            if 0 < pa < 1:
                x = lerp(120, cx + 200, ease_in(pa)); y = lerp(1250, cy - 140, ease_in(pa))
                arrow(ctx, [(x - 60, y + 50), (x, y)], C["gold2"], 4, a, head=14)
            vquote(ctx, t, T, "s6c", 850, 470, size=48, t_out=T.start("s6d") - 0.05, src=False)
            vquote(ctx, t, T, "s6d", 850, 470, size=48, src=False, t_out=te - 0.3, maxcol=5)
        # 覆舟山：疑兵
        a = fade(t, te + 0.4, tf + 0.6, 0.4, 0.5)
        if a > 0:
            hx, hy = v.place("覆舟山")
            set_col(ctx, "#4b3d2c", a)
            ctx.move_to(hx - 160, hy + 50); ctx.curve_to(hx - 90, hy - 60, hx + 60, hy - 70, hx + 170, hy + 50); ctx.close_path(); ctx.fill()
            tfl = T.word("s6e", "遍插旗帜")
            for k in range(48):
                fx = hx + 60 + (self.flags[k, 0] - 0.2) * 520
                fy = hy - 40 + (self.flags[k, 1] - 0.3) * 380
                ak = ease_out(prog(t, tfl - 0.3 + self.flags[k, 2] * 1.4, 0.3)) * a
                icon_flag(ctx, fx, fy, 22, C["red"], ak, wave=t * 3 + k)
            ag = ease_out(prog(t, T.word("s6e", "扔掉余粮") - 0.2, 0.4)) * a
            tag(ctx, "食毕，悉弃余粮", 90, 470, alpha=ag, col=C["gold2"], size=32)
            aq = ease_out(prog(t, T.word("s6e", "不知有多少"), 0.4)) * a
            draw_text(ctx, "“裕军四塞，不知多少”", 90, 540, family="serif", weight="Bold", size=38, color=C["blue2"],
                      alpha=aq, shadow=4)
        # 起兵前桓玄的一问
        vquote(ctx, t, T, "s6a", W / 2, 760, size=60, t_out=T.start("s6b") - 0.2)
        # 关键一句
        vquote(ctx, t, T, "s6f", 790, 520, size=50, t_out=tg + 0.2, maxcol=5)
        if t >= tf:
            al = fade(t, T.word("s6f", "北府人") + 0.2, tg + 0.2, 0.4, 0.4)
            circle(ctx, 120, 1170, 9, C["blue"], al)
            circle(ctx, 120, 1170, 4, C["red2"], al)
            draw_text(ctx, "红芯：北府出身的兵", 145, 1170, family="sans", weight="Medium", size=30, color=C["ink"], alpha=al, anchor="lm", shadow=4)
        # 东北风、火、桓玄跑路
        a = fade(t, tg - 0.1, th + 0.4, 0.4, 0.6)
        if a > 0:
            fzx, fzy = v.place("东陵")
            tw = T.word("s6g", "东北风")
            wind_arrows(ctx, t, fzx + 520, fzy - 420, fzx - 120, fzy + 220, 5, C["ink"], a * ease_out(prog(t, tw - 0.1, 0.4)) * 0.7, tw)
            tfi = T.word("s6g", "顺风放火")
            rng = np.random.default_rng(3)
            for k in range(26):
                p = prog(t, tfi + k * 0.05, 0.6)
                if p <= 0:
                    continue
                fx = fzx + 120 - k * 14 + rng.uniform(-40, 40)
                fy = fzy - 60 + rng.uniform(-90, 90)
                icon_fire(ctx, fx, fy, 30 + rng.uniform(0, 26), a * ease_out(p) * (1 - 0.5 * prog(t, th, 0.5)), phase=t + k)
            tag(ctx, "时东北风急，因纵火", 90, 470, alpha=a * ease_out(prog(t, tw, 0.4)), col=C["gold2"], size=32)
            # 桓玄
            tr = T.word("s6g", "石头城")
            sx, sy = v.place("石头城")
            pb = ease_io(prog(t, tr + 0.2, 2.2))
            ab_ = fade(t, tr - 0.2, th + 0.4, 0.4, 0.5)
            icon_boat(ctx, sx - 30 - pb * 150, sy + 30 + pb * 90, 28, C["blue2"], ab_)
            draw_text(ctx, "桓玄 · 弃城而走", 86, sy + 190, family="serif", weight="Black", size=40, color=C["blue2"],
                      alpha=ab_, anchor="lm", shadow=5)
        # 结论：对比表
        a = fade(t, th - 0.1, T.sec_end["S6"] + 0.2, 0.5, 0.3)
        if a > 0:
            rect(ctx, 0, 0, W, H, "#0b0806", 0.8 * a)
            draw_text(ctx, "这说明什么", W / 2, 330, family="serif", weight="Bold", size=34, color=C["gold"], alpha=a, anchor="cm", tracking=0.4)
            rows = [("朝廷", "有", "—", "朝廷"), ("门第", "高", "寒门", "门第"), ("兵力", "约两万", "约一千七", "兵多出十倍"),
                    ("北府军心", "无", "有", "北府兵认的是刘裕")]
            draw_text(ctx, "桓玄", 560, 420, family="serif", weight="Black", size=54, color=C["blue2"], alpha=a, anchor="cm")
            draw_text(ctx, "刘裕", 850, 420, family="serif", weight="Black", size=54, color=C["red2"], alpha=a, anchor="cm")
            for k, (lab, v1, v2, key) in enumerate(rows):
                ak = ease_out(prog(t, T.word("s6h", key) - 0.2, 0.4)) * a
                y = 530 + k * 110
                line(ctx, 90, y - 52, 990, y - 52, C["faint"], 1, ak * 0.6)
                draw_text(ctx, lab, 110, y, family="sans", weight="Bold", size=40, color=C["ink"], alpha=ak, anchor="lm")
                hl = k == 3
                draw_text(ctx, v1, 560, y, family="serif", weight="Black", size=44, color=C["dim"] if hl else C["blue2"], alpha=ak, anchor="cm")
                draw_text(ctx, v2, 850, y, family="serif", weight="Black", size=44 if not hl else 52,
                          color=C["red2"] if hl else C["dim"], alpha=ak, anchor="cm")
            af = ease_out(prog(t, T.word("s6h", "仗还没打") - 0.2, 0.5)) * a
            draw_text(ctx, "仗还没打，对面先散了", W / 2, 1040, family="serif", weight="Black", size=60, color=C["ink"],
                      alpha=af, anchor="cm", shadow=8)

    # ══ S7 恩怨 ═══════════════════════════════════════════
    def draw_S7(self, ctx, t):
        T = self.T
        self.bg(ctx)
        a = fade(t, T.start("s7a") - 0.1, T.start("s7b") - 0.1, 0.4, 0.4)
        if a > 0:
            name_tile(ctx, W / 2, 520, "桓玄", "404年五月 · 西逃途中被杀", alpha=a, col=C["blue2"], w=440)
            cross(ctx, W / 2, 575, 60, prog(t, T.word("s7a", "被杀"), 0.3), a)
            ab = ease_out(prog(t, T.word("s7a", "报恩"), 0.4)) * a
            draw_text(ctx, "报恩", 330, 860, family="serif", weight="Black", size=96, color=C["gold2"], alpha=ab, anchor="cm", shadow=6)
            draw_text(ctx, "报仇", 750, 860, family="serif", weight="Black", size=96, color=C["red2"],
                      alpha=ease_out(prog(t, T.word("s7a", "报仇"), 0.4)) * a, anchor="cm", shadow=6)
        # 刁逵
        a = fade(t, T.start("s7b") - 0.1, T.start("s7c") - 0.1, 0.4, 0.4)
        if a > 0:
            name_tile(ctx, W / 2, 400, "刁逵", "桓玄所任豫州刺史", alpha=a, col=C["ink"], w=420)
            ak = ease_out(prog(t, T.word("s7b", "同谋") - 0.2, 0.4)) * a
            tag(ctx, "曾执送刘裕同谋诸葛长民", 220, 620, alpha=ak, col=C["dim"], size=32)
            ts = T.word("s7b", "灭族")
            draw_seal(ctx, "灭族", W / 2, 860, size=180, alpha=ease_out(prog(t, ts - 0.1, 0.25)) * a, rot=-0.08,
                      scale=1 + 0.5 * (1 - ease_back(prog(t, ts - 0.1, 0.35))))
            ak2 = ease_out(prog(t, T.word("s7b", "子侄") - 0.2, 0.4)) * a
            draw_text(ctx, "子侄无少长皆死（《通鉴》）", W / 2, 1060, family="serif", weight="SemiBold", size=32,
                      color=C["gold"], alpha=ak2, anchor="cm")
        # 散财
        a = fade(t, T.start("s7c") - 0.1, T.start("s7d") - 0.1, 0.4, 0.4)
        if a > 0:
            gx, gy = W / 2, 1060
            op = ease_io(prog(t, T.word("s7c", "散给") - 0.2, 0.9))
            # 太阳走一整天
            ps = prog(t, T.word("s7c", "弥日"), 4.5)
            sxx = lerp(120, 960, ps); syy = 640 - math.sin(ps * math.pi) * 140
            circle(ctx, sxx, syy, 26, "#e0a35e", a * 0.9 * ease_out(prog(t, T.word("s7c", "弥日") - 0.3, 0.4)))
            icon_granary(ctx, gx, gy, 360, 300, "#5b4a35", a, open_=op)
            circle(ctx, gx, gy - 232, 34, "#2a2119", a)
            draw_text(ctx, "刁", gx, gy - 232, family="serif", weight="Black", size=44, color=C["gold2"], alpha=a, anchor="cm")
            # 人流：左进右出
            n = 160
            P = np.zeros((n, 2))
            rr = self.d_crowd.r
            for i in range(n):
                ph = ((t - T.word("s7c", "散给")) * 0.22 + rr[i, 0]) % 1.0
                if ph < 0.5:
                    x = lerp(40, gx - 40, ph * 2); y = gy + 60 + rr[i, 1] * 70
                else:
                    x = lerp(gx + 40, W - 40, (ph - 0.5) * 2); y = gy + 60 + rr[i, 1] * 70
                P[i] = (x, y)
            vis = ease_out(prog(t, T.word("s7c", "散给") + 0.4, 0.6)) * a
            for i in range(n):
                carrying = P[i, 0] > gx
                circle(ctx, P[i, 0], P[i, 1], 5, C["ink"] if not carrying else C["gold2"], vis * 0.9)
                if carrying:
                    rect(ctx, P[i, 0] - 5, P[i, 1] - 15, 10, 8, "#a07a3c", vis)
            vquote(ctx, t, T, "s7c", W / 2, 480, size=52, t_out=T.start("s7d") - 0.15, src=True, maxcol=4)
            af = ease_out(prog(t, T.word("s7c", "饥荒") - 0.2, 0.4)) * a
            tag(ctx, "时州郡饥弊，民赖之以济", 90, 1200, alpha=af, col=C["gold2"], size=30)
        # 王谧
        a = fade(t, T.start("s7d") - 0.1, T.start("s7e") - 0.1, 0.4, 0.4)
        if a > 0:
            steps = [("被捆时", "替刘裕还钱"), ("桓玄篡位", "亲手解下玉玺"), ("刘裕得势", "力保不杀"), ("司徒", "位列三公")]
            keys = ["王谧", "玉玺", "保他", "三公"]
            for k, ((h1, h2), key) in enumerate(zip(steps, keys)):
                ak = ease_out(prog(t, T.word("s7d", key) - 0.2, 0.4)) * a
                y = 1030 - k * 175
                x = 220 + k * 160
                card(ctx, x - 150, y - 60, 300, 120, ak, edge=C["gold2"] if k == 3 else C["faint"])
                draw_text(ctx, h1, x, y - 18, family="serif", weight="Black", size=36, color=C["gold2"] if k == 3 else C["ink"], alpha=ak, anchor="cm")
                draw_text(ctx, h2, x, y + 28, family="sans", weight="Regular", size=26, color=C["dim"], alpha=ak, anchor="cm")
            name_tile(ctx, 820, 330, "王谧", "琅邪王氏", alpha=a, col=C["gold2"], w=260)
            ag = ease_out(prog(t, T.word("s7d", "三公") + 0.2, 0.4)) * a
            draw_text(ctx, "《魏书》：裕以其偿钱之惠，固请免之", W / 2, 1180, family="serif", weight="SemiBold", size=30,
                      color=C["gold"], alpha=ag, anchor="cm")
        # 萧方等
        a = fade(t, T.start("s7e") - 0.1, T.start("s7f") - 0.1, 0.4, 0.4)
        if a > 0:
            vquote(ctx, t, T, "s7e", W / 2, 560, size=52, t_out=T.start("s7f") - 0.15)
            # 天平
            tilt = 0.22 * ease_io(prog(t, T.word("s7e", "一个封公") - 0.2, 0.8))
            cx, cy = W / 2, 1000
            line(ctx, cx, cy, cx, cy + 160, C["dim"], 5, a)
            lx, ly = cx - 280 * math.cos(tilt), cy - 280 * math.sin(tilt)
            rx_, ry_ = cx + 280 * math.cos(tilt), cy + 280 * math.sin(tilt)
            line(ctx, lx, ly, rx_, ry_, C["dim"], 6, a)
            for (px, py, txt, col) in ((lx, ly, "王谧为公", C["gold2"]), (rx_, ry_, "刁逵亡族", C["red2"])):
                line(ctx, px, py, px, py + 70, C["dim"], 2, a)
                draw_text(ctx, txt, px, py + 110, family="serif", weight="Black", size=44, color=col, alpha=a, anchor="cm")
        # 王愉父子
        a = fade(t, T.start("s7f") - 0.1, T.sec_end["S7"] + 0.2, 0.4, 0.3)
        if a > 0:
            name_tile(ctx, 330, 480, "王愉", "太原王氏 · 江左冠族", alpha=a, w=380)
            name_tile(ctx, 750, 480, "王绥", "王愉之子", alpha=a, w=300)
            ak = ease_out(prog(t, T.word("s7f", "看不起") - 0.2, 0.4)) * a
            draw_text(ctx, "以高祖起自布衣，甚相凌忽", W / 2, 720, family="serif", weight="Black", size=44, color=C["ink"], alpha=ak, anchor="cm")
            draw_text(ctx, "——《宋书》卷一", W / 2, 785, family="serif", weight="SemiBold", size=28, color=C["gold"], alpha=ak, anchor="cm")
            ts = T.word("s7f", "全族被杀")
            draw_seal(ctx, "族诛", W / 2, 960, size=150, alpha=ease_out(prog(t, ts - 0.1, 0.25)) * a, rot=0.06,
                      scale=1 + 0.5 * (1 - ease_back(prog(t, ts - 0.1, 0.35))))
            am = ease_out(prog(t, T.word("s7f", "谋反") - 0.2, 0.4)) * a
            draw_text(ctx, "《通鉴》《晋书》：谋袭刘裕，事泄", W / 2, 1110, family="sans", weight="Regular", size=28,
                      color=C["dim"], alpha=am, anchor="cm")

    # ══ S8 寒人 ═══════════════════════════════════════════
    def draw_S8(self, ctx, t):
        T = self.T
        self.bg(ctx)
        a = fade(t, T.start("s8a") - 0.1, T.start("s8b") - 0.1, 0.4, 0.4)
        if a > 0:
            draw_text(ctx, "门阀", 110, 400, family="serif", weight="Black", size=60, color=C["dim"], alpha=a, anchor="lm")
            for k, (nm, ok) in enumerate((("王谧", True), ("王愉", False))):
                x = 420 + k * 300
                name_tile(ctx, x, 345, nm, "用" if ok else "杀", alpha=a, col=C["gold2"] if ok else C["dim"], w=220)
                if not ok:
                    cross(ctx, x, 395, 40, prog(t, T.word("s8a", "杀掉"), 0.3), a)
            line(ctx, 90, 560, 990, 560, C["faint"], 1.5, a * 0.6)
            draw_text(ctx, "京口寒人", 110, 680, family="serif", weight="Black", size=60, color=C["red2"], alpha=a, anchor="lm")
            names = ["刘裕", "刘毅", "何无忌", "孟昶", "檀道济", "刘道规"]
            for k, nm in enumerate(names):
                ak = ease_out(prog(t, T.word("s8a", "京口") - 0.2 + k * 0.08, 0.4)) * a
                x = 190 + (k % 3) * 300
                y = 780 + (k // 3) * 150
                name_tile(ctx, x, y, nm, None, alpha=ak, col=C["red2"] if k == 0 else C["ink"], w=230, size=44)
            # 兵权落下
            tp = T.word("s8a", "掌兵")
            p = ease_io(prog(t, tp - 0.2, 0.9))
            draw_seal(ctx, "兵權", lerp(900, 900, p), lerp(380, 700, p), size=120, alpha=ease_out(prog(t, tp - 0.4, 0.3)) * a, rot=0.05)
            tag(ctx, "寒人：没有门第的普通人", 90, 1150, alpha=ease_out(prog(t, T.word("s8a", "没有门第") - 0.2, 0.4)) * a,
                col=C["gold2"], size=32)
        a = fade(t, T.start("s8b") - 0.1, T.start("s8c") - 0.1, 0.4, 0.4)
        if a > 0:
            vquote(ctx, t, T, "s8b", W / 2, 470, size=48, t_out=T.start("s8c") - 0.15)
            emps = [("宋", "刘裕"), ("齐", "萧道成"), ("梁", "萧衍"), ("陈", "陈霸先")]
            for k, (dyn, nm) in enumerate(emps):
                ak = ease_out(prog(t, T.word("s8b", "南朝四朝") - 0.2 + k * 0.15, 0.4)) * a
                x = 150 + k * 260
                card(ctx, x - 110, 800, 220, 230, ak, edge=C["red"] if k == 0 else C["faint"])
                draw_text(ctx, dyn, x, 860, family="serif", weight="Black", size=64, color=C["red2"] if k == 0 else C["ink"], alpha=ak, anchor="cm")
                draw_text(ctx, nm, x, 940, family="serif", weight="Bold", size=34, color=C["ink"], alpha=ak, anchor="cm")
                draw_text(ctx, "非高门", x, 990, family="sans", weight="Regular", size=24, color=C["dim"], alpha=ak, anchor="cm")
            ac = ease_out(prog(t, T.word("s8b", "欠债被抓") - 0.3, 0.4)) * a
            tag(ctx, "赵翼举证：宋武“尝负刁逵社钱被执，其寒贱可知也”", 70, 1110, alpha=ac, col=C["gold2"], size=27)
        a = fade(t, T.start("s8c") - 0.1, T.sec_end["S8"] + 0.3, 0.4, 0.4)
        if a > 0:
            draw_text(ctx, "刀把子", 300, 700, family="serif", weight="Black", size=110, color=C["red2"], alpha=a, anchor="cm", shadow=8)
            draw_text(ctx, "＞", W / 2, 700, family="serif", weight="Black", size=90, color=C["ink"],
                      alpha=ease_out(prog(t, T.word("s8c", "压过") - 0.2, 0.3)) * a, anchor="cm")
            draw_text(ctx, "门第", 800, 700, family="serif", weight="Black", size=110, color=C["dim"],
                      alpha=ease_out(prog(t, T.word("s8c", "门第") - 0.3, 0.3)) * a, anchor="cm", shadow=8)
            draw_text(ctx, "从京口这一千多人开始", W / 2, 520, family="sans", weight="Medium", size=38, color=C["gold2"], alpha=a, anchor="cm")

    # ══ S9 收尾 ═══════════════════════════════════════════
    def draw_S9(self, ctx, t):
        T = self.T
        t0 = T.sec_start["S9"]
        tn = clamp((t - t0) / (T.total - t0))
        assets.draw_woodcut(ctx, tn, mood="dusk", figure=False, push=(1.04, 1.12), focus=(700, 1000), t_abs=t)
        rect(ctx, 0, 0, W, H, "#0a0806", 0.25)
        for k, (lid, txt, col) in enumerate((("s9a", "他欠下三万钱，被捆在马桩上。", C["ink"]),
                                             ("s9b", "他攒下的，是一支军队的信任。", C["gold2"]),
                                             ("s9c", "一千七百人能赢，", C["red2"]))):
            a = fade(t, T.start(lid) - 0.1, T.end_card - 0.2, 0.6, 0.5)
            draw_text(ctx, txt, 86, 330 + k * 92, family="serif", weight="Black", size=54, color=col, alpha=a, shadow=6)
        a = fade(t, T.word("s9c", "是因为") - 0.1, T.end_card - 0.2, 0.6, 0.5)
        draw_text(ctx, "是因为对面的兵，本来就是他的。", 86, 330 + 3 * 92, family="serif", weight="Black", size=54,
                  color=C["red2"], alpha=a, shadow=6)
