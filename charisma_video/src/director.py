# -*- coding: utf-8 -*-
"""Maps the global timeline to drawn frames: per-segment animation, overlays, transitions."""
import json, math, os
import skia
from engine import *
import routemap as rm
import scene_open as so, scene_rome as sr, scene_medieval as sme, scene_east as se, scene_modern as smo, scene_saul as ss

HERE = os.path.dirname(os.path.abspath(__file__))

LABELS = {
    "cold": ("上世纪七十年代 · 迪士尼", "情景示意"),
    "title": (None, None),
    "weber": ("人为什么服从？", None),
    "routine": ("他走了以后", None),
    "lot": ("b) 抽签·神谕", "韦伯原文提到的例子"),
    "designate": ("c) 前任指定 · 罗马", "对照例子（韦伯原文在这一条举的是古罗马官职的任命）"),
    "elect": ("d) 推选＋认可 · 维泰博 1268–1271", "教皇的产生是韦伯原文的例子；维泰博是对照例子"),
    "blood": ("e) 血统 · 汉初", "对照例子"),
    "ottoman": ("e) 血统 · 奥斯曼", "韦伯原文提到的例子"),
    "office": ("f) 职位 · 罗马", "对照例子"),
    "donatist": ("f) 职位 · 北非教会", "韦伯原文提到的例子"),
    "disney": ("回到公司 · 迪士尼", "对照例子"),
    "apple": ("回到公司 · 苹果", "对照例子"),
    "end": ("他走了以后", None),
}
FOOT = {
    "cold": "画面为情景示意，人物为剪影。“What would Walt do?”的说法见《好莱坞报道者》2011、卡特穆尔《创新公司》2014 等",
    "weber": "韦伯《以政治为业》：1919 年 1 月 28 日慕尼黑演讲，同年出版（印行本有扩写）",
    "routine": "韦伯《经济与社会》（1922）第一部分第三章 §11“魅力的日常化”",
    "lot": "《撒母耳记上》10:17–27（和合本）；韦伯 §11 b)：Das alte Kriegsorakel bezeichnete angeblich Saul.",
    "designate": "前几位多因没有存活的亲生儿子而收养；“五贤帝”之说可追溯到马基雅维利《论李维》I.10",
    "elect": "据枢机主教们 1270 年 6 月的信（落款 in discooperto palatio）及枢机主教霍斯蒂恩西斯的记述；敕令 Ubi periculum（1274）",
    "blood": "《史记·吕太后本纪》。王陵之争在前 187 年；诛诸吕、迎立文帝在前 180 年",
    "ottoman": "法典条文仅存 17 世纪抄本，真伪有争议；1595 年事据 TDV《伊斯兰百科》“穆罕默德三世”条",
    "office": "Kaiser 源自拉丁文 Caesar；俄语 царь（沙皇）经哥特语、希腊语辗转而来",
    "donatist": "韦伯 §11 f)：character indelebilis 引发的争论“从多纳图派开始”",
    "disney": "《好莱坞报道者》2011；拉塞特语见美联社 2008；《纽约时报》1979-09-20",
    "apple": "《纽约时报》2014-08-10（Brian X. Chen）；库克：2011-10-19 追思会、2012 年 D10 大会。黑板上的公牛为本片自绘",
}

class Seg:
    def __init__(self, d):
        self.d = d
        self.t0, self.t1 = d["t0"], d["t1"]
        self.cues = {}
        self.lines = d["lines"]
        for i, ln in enumerate(d["lines"]):
            if ln.get("cue") and ln["cue"] not in self.cues:
                self.cues[ln["cue"]] = ln["t0"] - self.t0
            self.cues[f"L{i}"] = ln["t0"] - self.t0
            self.cues[f"E{i}"] = ln["t1"] - self.t0
        self.dur = self.t1 - self.t0

    def cue(self, name, default=1e9):
        return self.cues.get(name, default)

    def P(self, t, name, dur=1.0, delay=0.0):
        return ease(prog(t, self.cue(name) + delay, dur))

# ---------------------------------------------------------------- overlays
def quote_panel(c, de, zh, alpha, y=420, de_size=40, zh_size=32, italic=True):
    if alpha <= 0:
        return
    lines = wrap_cjk(de, "garamond_i" if italic else "garamond", de_size, 900)
    zl = wrap_cjk(zh, "serif", zh_size, 900)
    h = len(lines) * de_size * 1.3 + len(zl) * zh_size * 1.45 + 70
    rect = skia.Rect.MakeXYWH(60, y - 30, 960, h)
    c.drawRRect(skia.RRect.MakeRectXY(rect, 16, 16), paint(INK, 0.82 * alpha))
    c.drawRRect(skia.RRect.MakeRectXY(rect, 16, 16), paint(GOLD_DIM, alpha, stroke=1.6))
    quote_card(c, de, zh, 540, y + de_size * 0.9, alpha, de_size, zh_size, 900, italic=italic)

def big_line(c, text, y, alpha, size=60, color=IVORY, font_name="serif_b"):
    if alpha > 0:
        draw_paragraph(c, text, 540, y, font_name, size, color, 940, alpha, line_h=1.35, glow=6 * alpha, glow_color=GOLD)

def fade_win(t, a, b, fin=0.6, fout=0.6):
    return min(ease(prog(t, a, fin)), 1 - ease(prog(t, b - fout, fout)))

# ---------------------------------------------------------------- map state helper
ROAD_OF = {"lot": 1, "designate": 2, "elect": 3, "blood": 4, "ottoman": 4, "office": 5, "donatist": 5}
STORY_ORDER = ["lot", "designate", "elect", "blood", "office"]

def costs_before(sid, extra=0.0):
    """roads whose story has been told before segment sid; road 0 always shows '(not expanded)'."""
    done = [1.0] + [0.0] * 5
    for s in STORY_ORDER:
        if s == sid:
            break
        done[ROAD_OF[s]] = 1.0
    return done

def map_interlude(c, sid, t, seg, now_cost_from=None):
    """line-0 of a story: map with active road and a travelling light."""
    i = ROAD_OF[sid]
    costs = costs_before(sid)
    # previous road's cost stamps in as we arrive
    prev = STORY_ORDER.index(sid) - 1
    if prev >= 0:
        pr = ROAD_OF[STORY_ORDER[prev]]
        costs[pr] = ease(prog(t, 0.0, 1.0))
    draw_bg(c)
    tr = ease(prog(t, 0.3, seg.cue("E0") + 0.9 - 0.3))
    rm.draw_map(c, glow=0, extinguish=1, split=1, icons=1, labels=[1] * 6, costs=costs, show_center_label=1,
                active=i, travel=tr, dim_others=0.55)

def story_mix(c, seg, t, draw_story, sid):
    """Draw map for line 0, crossfade into the story scene."""
    switch = seg.cue("E0") + 0.4
    a = ease(prog(t, switch, 0.9))
    if a < 1:
        c.save()
        z = 1 + 0.25 * ease_in(prog(t, switch - 0.3, 1.2))
        (ex, ey), _, _ = path_point(rm.paths()[ROAD_OF[sid]], 1.0)
        c.translate(ex, ey); c.scale(z, z); c.translate(-ex, -ey)
        map_interlude(c, sid, t, seg)
        c.restore()
    if a > 0:
        c.saveLayerAlpha(None, int(255 * a))
        draw_story(c, t)
        c.restore()

# ---------------------------------------------------------------- segment drivers
def d_cold(c, seg, t):
    look = seg.P(t, "look_up", 1.4)
    line_a = seg.P(t, "walt_line", 0.8) * (1 - seg.P(t, "L5", 0.8))
    zh_a = seg.P(t, "walt_line", 0.8, 0.7) * (1 - seg.P(t, "L5", 0.8))
    glow = 0.45 + 0.5 * look
    c.save(); z = 1 + 0.04 * clamp(t / seg.dur); c.translate(540, 700); c.scale(z, z); c.translate(-540, -700)
    so.draw_meeting(c, look_up=look, line_a=line_a, zh_a=zh_a, portrait_glow=glow)
    c.restore()

def d_title(c, seg, t):
    a = ease(prog(t, -1.2, 1.4))
    so.draw_title(c, a=a, sub_a=ease(prog(t, -0.4, 1.4)), glow=0.55 + 0.1 * math.sin(t * 1.3))

def d_weber(c, seg, t):
    draw_bg(c)
    lec_a = ease(prog(t, 0, 1.2)) * (1 - seg.P(t, "charisma", 1.0))
    so.draw_lecture(c, lec_a)
    if seg.cue("three") < 1e8:
        ap = (seg.P(t, "r1", 0.8), seg.P(t, "r2", 0.8), seg.P(t, "r3", 0.8))
        hl = seg.P(t, "r2", 1.0, 0.3)
        out = seg.P(t, "so", 1.0, 0.5)
        if max(ap) > 0 and out < 1:
            c.saveLayerAlpha(None, int(255 * (1 - out)))
            so.draw_cards(c, ap, hl)
            c.restore()
    # definition panel (top area) after "charisma"
    da = seg.P(t, "charisma", 1.0, 0.3) * (1 - seg.P(t, "so", 1.0, 0.5))
    if da > 0:
        draw_text(c, "Charisma", 540, 450, "garamond_i", 96, GOLD_HI, da, align="center", glow=10, glow_color=GOLD)
        draw_text(c, "卡里斯玛", 540, 530, "serif_b", 52, IVORY, da, align="center", tracking=0.2)
        d2 = seg.P(t, "L9", 1.0) * da
        draw_paragraph(c, "大家相信，这个人身上有一种天生的、非同一般的东西", 540, 610, "serif", 34, IVORY, 900, d2)
        d3 = seg.P(t, "L10", 1.0) * da
        draw_text(c, "Gnadengabe · 天赐的恩典 → 今译“魅力”", 540, 700, "serif_sb", 32, GOLD, d3, align="center")
    nr = seg.P(t, "no_rules", 0.8) * (1 - seg.P(t, "so", 0.8))
    if nr > 0:
        quote_panel(c, "Es gibt keine „Hierarchie“ … keinen „Gehalt“ … kein Reglement",
                    "没有“等级”……没有“薪水”……没有章程", nr, y=820)
    # the glowing circle that becomes the map's centre
    ca = seg.P(t, "so", 1.4, 0.3)
    if ca > 0:
        c.saveLayerAlpha(None, int(255 * ca))
        rm.draw_map(c, glow=1.0, split=0, icons=0, show_center_label=0)
        c.restore()
        fr = seg.P(t, "L14", 1.0)
        draw_text(c, "最有力量", 540, 1110, "serif_b", 46, GOLD_HI, ca * (1 - fr), align="center")
        draw_text(c, "也最脆弱", 540, 1110, "serif_b", 46, RED, fr, align="center")

def ring(c, cx, cy, r, n, col, alpha, size=1.0, phase=0.0, label=None):
    for k in range(n):
        a = 2 * math.pi * k / n + phase
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        c.drawCircle(x, y - 14 * size, 9 * size, paint(col, alpha))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 11 * size, y - 4 * size, 22 * size, 24 * size),
                                          9 * size, 9 * size), paint(col, alpha))

def d_routine(c, seg, t):
    draw_bg(c)
    ext = seg.P(t, "extinguish", 1.6)
    split = ease(prog(t, seg.cue("split") + 0.2, 2.6))
    icons = ease(prog(t, seg.cue("split") + 1.2, 2.0))
    labels = [seg.P(t, f"road{i + 1}", 0.7) for i in range(6)]
    costs = [seg.P(t, "road1", 0.7, 1.2)] + [0] * 5
    active = None; tr = 0
    for i in range(6):
        if seg.cue(f"road{i + 1}") <= t < seg.cue(f"road{i + 2}" if i < 5 else "all"):
            active = i
            tr = ease(prog(t, seg.cue(f"road{i + 1}"), 1.6))
    flick = 0.0
    if seg.cue("L8") <= t < seg.cue("extinguish"):
        flick = 0.15 * (0.5 + 0.5 * math.sin(t * 9) * math.sin(t * 3.1))
    rm.draw_map(c, glow=1.0 - flick, extinguish=ext, split=split, icons=icons, labels=labels, costs=costs,
                show_center_label=ease(prog(t, seg.cue("extinguish") + 0.8, 1.2)),
                active=active, travel=tr, dim_others=0.45 if active is not None else 0.0)
    # followers and staff rings before the light goes out
    fa = seg.P(t, "followers", 1.0) * (1 - seg.P(t, "extinguish", 0.8))
    sa = seg.P(t, "staff", 1.0) * (1 - seg.P(t, "extinguish", 0.8))
    if fa > 0:
        ring(c, rm.O[0], rm.O[1], 300, 16, IVORY, fa * 0.8, 1.0, t * 0.05)
        draw_text(c, "追随者：希望恩典别走", 540, rm.O[1] + 380, "serif_sb", 32, IVORY, fa, align="center")
    if sa > 0:
        ring(c, rm.O[0], rm.O[1], 175, 7, GOLD, sa, 1.2, -t * 0.08)
        draw_text(c, "班底：要位置、收入、养家", 540, rm.O[1] - 360, "serif_sb", 32, GOLD_HI, sa, align="center")
    # quotes
    qa = fade_win(t, seg.cue("title_card"), seg.cue("L2"))
    if qa > 0:
        quote_panel(c, "Die Veralltäglichung des Charisma", "魅力的日常化：把不一般的东西，变成能天天用、能传下去的东西", qa, y=372)
    na = fade_win(t, seg.cue("nascendi"), seg.cue("L3") + 0.3)
    if na > 0:
        quote_panel(c, "in statu nascendi", "拉丁文：“在诞生的状态中”", na, y=372)
    ca = fade_win(t, seg.cue("L9"), seg.cue("extinguish"))
    if ca > 0:
        draw_text(c, "不按规矩来  ×  装进规矩", 540, 380, "serif_b", 44, RED, ca, align="center")

def d_lot(c, seg, t):
    def story(c, t):
        ss.draw_saul(c, tribes=seg.P(t, "tribes", 2.0), pick=seg.P(t, "narrow", 1.0),
                     clans=seg.P(t, "narrow", 1.0, 2.2), pick2=seg.P(t, "narrow", 0.8, 3.4),
                     men=seg.P(t, "narrow", 1.0, 4.4), pick3=seg.P(t, "narrow", 0.8, 5.2),
                     hide=seg.P(t, "hide", 1.0, 0.8), tall=seg.P(t, "tall", 1.2), doubt=seg.P(t, "doubt", 1.0, 0.4))
        wa = fade_win(t, seg.cue("weber_note"), seg.cue("tribes"))
        if wa > 0:
            quote_panel(c, "Das alte Kriegsorakel bezeichnete angeblich Saul.", "韦伯 §11 b)：古老的战争神谕，据说选中了扫罗。", wa, y=420)
    story_mix(c, seg, t, story, "lot")

def d_designate(c, seg, t):
    def story(c, t):
        sr.draw_coins(c, appear=ease(prog(t, seg.cue("coins_in"), 3.0)), links=ease(prog(t, seg.cue("chain"), 4.0)),
                      final_link=seg.P(t, "solid", 1.0), crack=seg.P(t, "crack", 1.6), rust=seg.P(t, "crack", 2.4, 0.4),
                      focus=5 if t >= seg.cue("commodus") else None, dim=seg.P(t, "commodus", 1.0) * 0.6)
        ca = fade_win(t, seg.cue("caveat"), seg.cue("commodus"))
        if ca > 0:
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(90, 1040, 900, 120), 16, 16)
            c.drawRRect(rr, paint(INK, 0.85 * ca)); c.drawRRect(rr, paint(GOLD_DIM, ca, stroke=1.6))
            draw_text(c, "不是有意设计", 540, 1090, "serif_b", 38, GOLD_HI, ca, align="center")
            draw_text(c, "前几位要么没有儿子，要么儿子没能活下来", 540, 1138, "serif", 30, IVORY, ca, align="center")
        da = seg.P(t, "dio", 0.8) * (1 - seg.P(t, "so", 0.8, 0.5))
        if da > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.45 * da))
            quote_panel(c, "“…from a kingdom of gold to one of iron and rust.”",
                        "从黄金的王国，跌进铁锈的王国——卡西乌斯·狄奥《罗马史》72.36.4", da, y=560)
    story_mix(c, seg, t, story, "designate")

def d_elect(c, seg, t):
    def story(c, t):
        roof = ease(prog(t, seg.cue("roof"), 5.0)) * 0.75 + ease(prog(t, seg.cue("rule"), 3.0)) * 0.25
        bread = 4 - int(3 * clamp((t - seg.cue("roof")) / 6.0)) if t >= seg.cue("roof") else 4
        key = ease(prog(t, seg.cue("key"), 1.8)) * (1 - seg.P(t, "so", 1.0, 1.0))
        inner = seg.P(t, "palace", 1.2) if seg.cue("palace") < 1e8 else 1
        c.saveLayerAlpha(None, int(255 * max(0.0, inner)))
        sme.draw_viterbo(c, roof_off=roof, bread=bread, key=key, letter=fade_win(t, seg.cue("letter"), seg.cue("L7") + 0.5))
        c.restore()
        wa = fade_win(t, seg.cue("weber_note"), seg.cue("L2") + 0.4)
        if wa > 0:
            draw_bg(c)
            quote_panel(c, "Durch Nachfolgerdesignation seitens des charismatisch qualifizierten Verwaltungsstabs und Anerkennung durch die Gemeinde.",
                        "韦伯 §11 d)：由有魅力资格的班底指定，再由众人认可", wa, y=640)
        # year counter
        ya = fade_win(t, seg.cue("months"), seg.cue("rule"))
        if ya > 0:
            span = max(1.0, seg.cue("L7") - seg.cue("months"))
            yr = 1268 + int(3.75 * clamp((t - seg.cue("months")) / span) * 1.0)
            yr = min(yr, 1271)
            draw_text(c, str(yr), 160, 1240, "cinzel", 64, GOLD_HI, ya, align="left")
            if t >= seg.cue("L7"):
                draw_text(c, "1271.9.1  格里高利十世", 920, 1240, "serif_sb", 34, GOLD_HI, seg.P(t, "L7", 0.8), align="right")
        ra = fade_win(t, seg.cue("rule"), seg.cue("key"))
        if ra > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.5 * ra))
            quote_panel(c, "ita claudatur undique, ut nullus illud intrare valeat vel exire",
                        "四面封闭，任何人不得进出——敕令 Ubi periculum，1274", ra, y=400, de_size=34)
            rows = [("关门选举", 0.0), ("三天选不出 → 每顿一道菜", 0.25), ("再过五天 → 面包、水、酒", 0.5)]
            for k, (txt, dl) in enumerate(rows):
                a = ease(prog(t, seg.cue("rule") + 0.8 + dl * (seg.cue("key") - seg.cue("rule") - 1.5), 0.6)) * ra
                draw_text(c, txt, 540, 760 + k * 90, "serif_b", 46, IVORY if k == 0 else GOLD_HI, a, align="center")
        la = seg.P(t, "L12", 1.0)
        if la > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.6 * la))
            for k, (yr_, txt, col) in enumerate([("1274", "订立", GOLD_HI), ("1276", "暂停、撤销", RED), ("1294", "恢复", GOLD_HI)]):
                a = ease(prog(t, seg.cue("L12") + 0.6 + k * 1.2, 0.6)) * la
                x = 220 + k * 320
                draw_text(c, yr_, x, 760, "cinzel", 70, col, a, align="center")
                draw_text(c, txt, x, 830, "serif_sb", 36, IVORY, a, align="center")
                if k < 2:
                    c.drawLine(x + 100, 740, x + 220, 740, paint(GOLD_DIM, a, stroke=2))
    story_mix(c, seg, t, story, "elect")

def d_blood(c, seg, t):
    def story(c, t):
        ta = fade_win(t, seg.cue("term"), seg.cue("horse") - 0.2)
        if t < seg.cue("horse"):
            draw_bg(c, tint=se.HAN_BG)
            quote_panel(c, "Erbcharisma", "世袭魅力：认为那种不一般的东西在血里，跟着血统往下传", ta, y=640, de_size=72)
            q2 = seg.P(t, "L2", 0.8)
            draw_text(c, "谁，算这个血统？", 540, 1000, "serif_b", 56, RED, q2 * ta, align="center")
            return
        horse = seg.P(t, "horse", 1.4)
        slips = ease(prog(t, seg.cue("oath"), 2.5))
        se.draw_han(c, horse_a=horse, slips_a=slips, red_a=seg.P(t, "slips", 1.2), seal_a=seg.P(t, "slips", 0.8, 1.0))
        wa = fade_win(t, seg.cue("wendi"), seg.cue("so") + 0.4)
        if wa > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * wa))
            draw_text(c, "前 180 年", 540, 560, "cinzel", 60, GOLD_HI, wa, align="center")
            draw_text(c, "吕后去世 · 诸吕被除 · 迎立代王刘恒（汉文帝）", 540, 640, "serif_sb", 36, IVORY, wa, align="center")
        sa = seg.P(t, "so", 1.0)
        if sa > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.72 * sa))
            draw_text(c, "先说清：谁算这个血统", 540, 760, "serif_b", 60, RED, sa, align="center", glow=6)
    story_mix(c, seg, t, story, "blood")

def lamp_schedule(seg):
    t0 = seg.cue("lamps") + 1.5
    dur = max(4.0, seg.cue("weber_quote") - t0 - 0.3)
    return t0, dur

def d_ottoman(c, seg, t):
    lamps_t0, lamps_dur = lamp_schedule(seg)
    k = clamp((t - lamps_t0) / lamps_dur) * 19
    n_out = int(k); frac = k - n_out
    if n_out >= 19:
        lamps_on, fading = -1, 0.0
    else:
        lamps_on, fading = 18 - n_out, frac
    if t < lamps_t0:
        lamps_on, fading = 19, 0.0
    se.draw_ottoman(c, lamps_on=lamps_on, fading=fading, arches_a=seg.P(t, "L0", 1.5))
    # count
    if t >= lamps_t0:
        n_out = min(19, int(k))
        draw_text(c, f"{n_out} / 19", 540, 1300 - 40, "cinzel", 44, GOLD, fade_win(t, lamps_t0, seg.cue("weber_quote") + 0.8), align="center")
    ca = fade_win(t, seg.cue("code"), seg.cue("lamps"))
    if ca > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * ca))
        quote_panel(c, "“…for the good order of the world.”",
                    "“为了世界的秩序”，继位者处死兄弟“是适宜的”——据传出自穆罕默德二世法典，仅存后世抄本", ca, y=620)
    wa = fade_win(t, seg.cue("weber_quote"), seg.cue("cage"))
    if wa > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * wa))
        quote_panel(c, "die „Pflicht“ der Ausrottung aller sonst denkbaren Anwärter im Hause Osmans",
                    "韦伯 §11：奥斯曼王室“除掉其他所有可能的继承人”的“义务”", wa, y=620)
    ga = fade_win(t, seg.cue("cage"), seg.cue("so") + 0.3)
    if ga > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((4, 8, 20), 0.6 * ga))
        # lattice (kafes)
        x0, y0, w, h = 300, 560, 480, 560
        for kx in range(0, 9):
            c.drawLine(x0 + kx * w / 8, y0, x0 + kx * w / 8, y0 + h, paint(se.OT_GOLD, ga, stroke=5))
        for ky in range(0, 10):
            c.drawLine(x0, y0 + ky * h / 9, x0 + w, y0 + ky * h / 9, paint(se.OT_GOLD, ga, stroke=5))
        se.lamp(c, 540, 850, 0.6, alpha=ga)
        draw_text(c, "Kafes · “笼子”（1603 年起）", 540, 500, "serif_sb", 38, IVORY, ga, align="center")
    pa = seg.P(t, "primo", 1.0)
    if pa > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.6 * pa))
        quote_panel(c, "Nur im mittelalterlichen Okzident und in Japan, sonst nur vereinzelt, ist das eindeutige Prinzip des Primogeniturerbrechts … durchgedrungen",
                    "韦伯 §11：只有在中世纪西方和日本，长子继承这条清楚的原则才真正贯彻（别处只是零星）", pa, y=520, de_size=34)

def d_office(c, seg, t):
    def story(c, t):
        if t < seg.cue("name"):
            draw_bg(c)
            ta = fade_win(t, seg.cue("term"), seg.cue("name") + 0.2)
            quote_panel(c, "Amtscharisma", "职位魅力：认为那种不一般的东西在位子上，谁坐上去，谁就有", ta, y=640, de_size=72)
            return
        sr.draw_caesar(c, coin_a=seg.P(t, "name", 1.2), name_a=seg.P(t, "name", 1.0, 1.0), morph=seg.P(t, "kaiser", 2.0))
        ma = fade_win(t, seg.cue("L3"), seg.cue("kaiser"))
        if ma > 0:
            draw_text(c, "屋大维 · 18 岁 · 以“恺撒”之名起家", 540, 1160, "serif_sb", 34, IVORY, ma * (1 - seg.P(t, "L4", 0.6)), align="center")
            draw_text(c, "奥古斯都 · 前 27 年 · 自称“第一公民”(princeps)", 540, 1160, "serif_sb", 32, IVORY, seg.P(t, "L4", 0.6) * ma, align="center")
    story_mix(c, seg, t, story, "office")

def d_donatist(c, seg, t):
    seat = seg.P(t, "glow_seat", 1.5)
    fig = 1.0
    sme.draw_window(c, seat_glow=0.25 + 0.75 * seat, figure=fig, text_a=seg.P(t, "indelebilis", 1.0))
    ba = fade_win(t, seg.cue("books"), seg.cue("augustine"))
    if ba > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.55 * ba))
        draw_text(c, "公元 303–305 年 · 戴克里先迫害", 540, 600, "serif_sb", 38, IVORY, ba, align="center")
        draw_text(c, "traditores · “交出经书的人”", 540, 680, "garamond_i", 44, GOLD_HI, ba, align="center")
        da = seg.P(t, "L2", 0.8) * ba
        draw_text(c, "多纳图派：他们主持的圣礼，统统不算数", 540, 790, "serif_b", 40, RED, da, align="center")
    aa = fade_win(t, seg.cue("augustine"), seg.cue("glow_seat") + 0.2)
    if aa > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 0.5 * aa))
        draw_text(c, "奥古斯丁（354–430）", 540, 640, "serif_sb", 42, GOLD_HI, aa, align="center")
        draw_text(c, "北非希波的主教", 540, 700, "serif", 32, IVORY, aa, align="center")
    wa = fade_win(t, seg.cue("indelebilis"), seg.cue("so") + 0.3)
    if wa > 0:
        quote_panel(c, "Der character indelebilis bedeutet die Loslösung der amtscharismatischen Fähigkeiten von den Qualitäten der Person des Priesters.",
                    "“不可磨灭的印记”，意味着职位的能力，与神父本人的品格分开", wa, y=372, de_size=32, zh_size=30)

def d_disney(c, seg, t):
    draw_bg(c, tint=((8, 22, 24), (16, 40, 44)))
    ice = seg.P(t, "ice", 3.0) * (1 - 0.6 * seg.P(t, "thaw", 3.0))
    c.save(); z = 1.5; c.translate(540, 640); c.scale(z, z); c.translate(-540, -640)
    smo.frozen_portrait(c, 540, 620, 240, 290, ice, ease(prog(t, 0, 1.0)))
    c.restore()
    qa = fade_win(t, seg.cue("L1"), seg.cue("leave"))
    draw_text(c, "“What would Walt do?”", 540, 1010, "garamond_i", 56, ICE_C, qa, align="center")
    la = fade_win(t, seg.cue("leave"), seg.cue("thaw") + 0.4)
    if la > 0:
        for k in range(11):
            p = clamp((t - seg.cue("leave") - k * 0.25) / 4.0)
            x = 150 + k * 40 + ease(p) * 700
            smo_fig(c, x, 1180, la * (1 - 0.7 * p))
        draw_text(c, "1979.9.13 · 11 人 · 超过动画部门的 15%", 540, 1010, "serif_sb", 36, IVORY, la, align="center")
    ta = seg.P(t, "thaw", 1.0) * (1 - seg.P(t, "so", 0.8))
    if ta > 0:
        draw_text(c, "1984 · 艾斯纳、威尔斯接手", 540, 1010, "serif_sb", 38, IVORY, ta, align="center")
    sa = seg.P(t, "so", 1.0)
    if sa > 0:
        draw_text(c, "不是传承，是冻结", 540, 1060, "serif_b", 60, ICE_C, sa, align="center", glow=8, glow_color=(120, 180, 220))

ICE_C = (176, 214, 232)

def smo_fig(c, x, y, a):
    c.drawCircle(x, y - 70, 14, paint((200, 210, 210), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 16, y - 54, 32, 54), 12, 12), paint((200, 210, 210), a))

def d_apple(c, seg, t):
    draw_bg(c, tint=((8, 22, 24), (16, 40, 44)))
    end_cmp = seg.cue("so")
    if t < end_cmp:
        stage = 0 if t < seg.cue("bulls") else 4 * clamp((t - seg.cue("bulls")) / max(3.0, seg.cue("L4") - seg.cue("bulls") + 1.0))
        stage = max(stage, 0.0)
        a = ease(prog(t, seg.cue("class"), 1.2)) * (1 - seg.P(t, "cook", 0.8))
        c.save(); c.translate(0, -240)
        smo.classroom(c, 772, max(stage, 0.001) if stage > 0 else 0, a)
        c.restore()
        if stage <= 0 and a > 0:
            draw_text(c, "Apple University · 2008", 540, 1120, "garamond_i", 44, GOLD_HI, a, align="center")
        ua = seg.P(t, "class", 1.0) * (1 - seg.P(t, "cook", 0.8))
        draw_text(c, "用自己的历史当案例", 540, 1120 if stage > 0 else 1180, "serif_sb", 36, IVORY, ua * (1 if stage > 0 else 0.0), align="center")
        ka = seg.P(t, "cook", 1.0)
        if ka > 0:
            draw_text(c, "2011 年 8 月", 540, 560, "cinzel", 64, GOLD_HI, ka, align="center")
            draw_text(c, "乔布斯请库克接任首席执行官", 540, 640, "serif_sb", 38, IVORY, ka, align="center")
            draw_text(c, "几个星期后，乔布斯去世", 540, 700, "serif", 32, MUTED, ka * seg.P(t, "cook", 0.8, 2.0), align="center")
            ma = seg.P(t, "L6", 1.0) * (1 - seg.P(t, "never_ask", 0.6))
            draw_text(c, "“what would Walt have done?”", 540, 860, "garamond_i", 46, ICE_C, ma, align="center")
            draw_text(c, "沃尔特走后，大家开会琢磨：沃尔特会怎么做？", 540, 920, "serif", 30, IVORY, ma, align="center")
            na = seg.P(t, "never_ask", 1.0)
            if na > 0:
                draw_text(c, "“never ask what he would do.", 540, 860, "garamond_i", 52, GOLD_HI, na, align="center")
                draw_text(c, "Just do what’s right.”", 540, 930, "garamond_i", 52, GOLD_HI, na, align="center")
                draw_text(c, "永远别问我会怎么做，做对的事就行", 540, 1010, "serif_b", 40, IVORY, na, align="center")
                draw_text(c, "——库克转述乔布斯（2011 年追思会；2012 年 D10 大会）", 540, 1070, "serif", 26, MUTED, na, align="center")
    else:
        smo.draw_companies(c, ice=0.85, stage=4, top_a=seg.P(t, "so", 1.0), bot_a=seg.P(t, "so", 1.0, 0.6))

def d_end(c, seg, t):
    draw_bg(c)
    dim = seg.P(t, "l1", 1.2)
    c.saveLayerAlpha(None, int(255 * (1 - 0.86 * dim)))
    rm.draw_map(c, glow=0.25 * seg.P(t, "l3", 2.0), extinguish=1 - 0.35 * seg.P(t, "l3", 2.0), split=1, icons=1,
                labels=[1] * 6, costs=[1] * 6, show_center_label=1)
    c.restore()
    big_line(c, "一个组织靠一个人撑起来，不稀奇。", 470, seg.P(t, "l1", 1.0), 52)
    big_line(c, "稀奇的是，那个人走了以后，还能接着走。", 620, seg.P(t, "l2", 1.0), 52, GOLD_HI)
    big_line(c, "能活下来的，都是把“他”变成了“规矩”的那一些。", 800, seg.P(t, "l3", 1.0), 50)
    big_line(c, "别问“他会怎么做”。", 1060, seg.P(t, "l4", 1.2, 2.0), 64, GOLD_HI)

DRIVERS = dict(cold=d_cold, title=d_title, weber=d_weber, routine=d_routine, lot=d_lot, designate=d_designate,
               elect=d_elect, blood=d_blood, ottoman=d_ottoman, office=d_office, donatist=d_donatist,
               disney=d_disney, apple=d_apple, end=d_end)

def end_card(c, t, dur, teaser=None):
    draw_bg(c)
    a = ease(prog(t, 0, 1.2))
    draw_text(c, "他走了以后", 540, 860, "serif_b", 80, GOLD_HI, a, align="center", tracking=0.08)
    draw_text(c, "魅力的日常化 · Max Weber", 540, 940, "serif", 34, IVORY, a * 0.9, align="center")
    if teaser:
        draw_text(c, teaser, 540, 1120, "serif", 30, MUTED, a, align="center")

# ---------------------------------------------------------------- frame composition
class Director:
    def __init__(self, tl_path, teaser=None):
        self.tl = json.load(open(tl_path))
        self.segs = [Seg(s) for s in self.tl["segments"]]
        self.teaser = teaser

    def active(self, T):
        """return list of (seg, alpha) to draw"""
        segs = self.segs
        for i, s in enumerate(segs):
            nxt = segs[i + 1] if i + 1 < len(segs) else None
            end = nxt.t0 if nxt else self.tl["end_card"][0]
            if s.t0 - (1.6 if i == 0 else 0) <= T < end:
                # crossfade in the gap: last 0.9 s before next segment
                if nxt and T > end - 0.9:
                    a = ease((T - (end - 0.9)) / 0.9)
                    return [(s, 1.0), (nxt, a)]
                return [(s, 1.0)]
        return []

    def frame(self, c, T):
        draw_bg(c)
        items = self.active(T)
        if not items:
            ec0 = self.tl["end_card"][0]
            if T >= ec0 - 0.01:
                # fade from last segment into end card
                end_card(c, T - ec0, self.tl["total"] - ec0, self.teaser)
            return
        for seg, a in items:
            if a < 1:
                c.saveLayerAlpha(None, int(255 * a))
            DRIVERS[seg.d["id"]](c, seg, T - seg.t0)
            lab, badge = LABELS[seg.d["id"]]
            la = 1.0
            if lab:
                chapter_label(c, lab, la)
            if badge:
                tag_badge(c, badge, la)
            if seg.d["id"] in FOOT:
                footnote(c, FOOT[seg.d["id"]], 0.9)
            if a < 1:
                c.restore()
        # subtitles from the most recent segment
        for seg, a in items:
            for ln in seg.lines:
                if seg.d["id"] == "end" and ln.get("cue") in ("l1", "l2", "l3"):
                    continue
                for (c0, c1, txt) in ln["chunks"]:
                    if c0 - 0.05 <= T < c1 + 0.15:
                        sa = min(1.0, (T - c0 + 0.05) / 0.12, (c1 + 0.15 - T) / 0.12)
                        subtitle(c, txt, clamp(sa))
        # global fade in at start, fade to black at very end
        if T < 1.0:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), 1 - ease(T / 1.0)))
        if T > self.tl["total"] - 1.2:
            c.drawRect(skia.Rect.MakeWH(W, H), paint((0, 0, 0), ease((T - (self.tl["total"] - 1.2)) / 1.2)))
