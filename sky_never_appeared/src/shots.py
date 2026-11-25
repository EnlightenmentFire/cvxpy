"""Per-section shot logic: maps absolute time -> rendered frame (float RGB)."""
import math
import numpy as np
import cv2
from common import *
import fx
import scene_sky as SKY
import scenes2d as S2
import scenes_more as SM
import script_data as SD
from scenes2d import BLUE, AMBER, RED, WHITE, GREY, DIM

TL = None
SEC = {}
CUE = {}
SUBS_BY = []
FREEZE_AT = 12.70          # sky time at which the cold open freezes
XFADE = 0.45
_cache = {}


def setup(tl):
    global TL, SEC, CUE
    TL = tl
    SEC = {s['sec']: s for s in tl['sections']}
    CUE = tl['cues']
    build_shots()


def section_at(t):
    for s in TL['sections']:
        if s['start'] - SM_GAP <= t < s['end']:
            return s
    return TL['sections'][-1]


SM_GAP = 0.0


def subs_at(t):
    return [s for s in TL['subs'] if s['start'] - 0.05 <= t < s['end'] + 0.05]


def sub_time(prefix):
    """start time of the first subtitle chunk that begins with prefix."""
    for s in TL['subs']:
        if s['text'].startswith(prefix):
            return s['start']
    return None


def draw_subtitles(img, t):
    for s in subs_at(t):
        a = min(1.0, (t - s['start'] + 0.05) / 0.12, (s['end'] + 0.05 - t) / 0.12)
        if s.get('en'):
            fx.subtitle(img, s['text'], alpha=clamp(a), color=(0.98, 0.93, 0.80))
        else:
            fx.subtitle(img, s['text'], alpha=clamp(a))


# ------------------------------------------------------------------ cold open
def _frozen():
    if 'frozen' not in _cache:
        c, e, cam = SKY.draw_sky(FREEZE_AT)
        _cache['frozen'] = (c + e + bloom(e, 0.95) + bloom(c.clip(0.6, 5) - 0.6, 0.25))
    return _cache['frozen']


def zoom(img, z, cx=W / 2, cy=H * 0.45):
    M = np.array([[z, 0, cx * (1 - z)], [0, z, cy * (1 - z)]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def render_open(t, fi):
    title_t = CUE.get('TITLE_START', 40.0)
    if t < FREEZE_AT:
        c, e, cam = SKY.draw_sky(t)
        k_in = smooth(remap(t, 0.0, 1.6))
        img = SKY.finish(c * k_in, e * k_in, fi, hypo=1.0)
        fx.hypo_overlay(img, alpha=smooth(remap(t, 0.4, 1.2)))
        return img
    if t < title_t:
        base = _frozen()
        k = remap(t, FREEZE_AT, title_t)
        img = zoom(base, 1.0 + 0.07 * smooth(k))
        d = smooth(remap(t, FREEZE_AT, FREEZE_AT + 0.6))
        lum = img.mean(axis=2, keepdims=True)
        img = img * (1 - 0.25 * d) + lum * 0.25 * d
        img = img * (1 - 0.18 * smooth(k))
        img = grade_hypo(img, 1.0)
        img = vignette(tonemap(img), 0.55)
        img = grain(img, fi, 0.016)
        fx.hypo_overlay(img)
        draw_subtitles(img, t)
        if t > title_t - 2.0 / FPS:
            img = img + 1.6
        return img
    tt = t - title_t
    c, e = S2.title_card(tt + 0.3)
    img = S2.finish(c, e, fi)
    if tt < 2.0 / FPS:
        img = img + 1.2
    return img


# ------------------------------------------------------------------ generic shots
class Shot:
    def __init__(self, start, fn, hypo=False, name=''):
        self.start, self.fn, self.hypo, self.name = start, fn, hypo, name
        self.end = None


SHOTS = []


def cue(lid):
    return CUE[lid]


def build_shots():
    SHOTS.clear()
    S = SHOTS
    tw = lambda f: f  # noqa

    def add(lid_or_t, fn, hypo=False, name=''):
        t0 = cue(lid_or_t) if isinstance(lid_or_t, str) else lid_or_t
        S.append(Shot(t0 - 0.25, fn, hypo, name))

    # chapter cards between sections are drawn by render(); shots start at the first line
    # ---- 02 terror
    add('t1', lambda t: S2.balance(t, 'level'), name='balance')
    add('t7', lambda t: SM.treaty(t), name='treaty')
    add('t10', lambda t: SM.takeaway(t, ['冷战的和平', '靠的是同归于尽']), name='take')
    # ---- 03 reagan
    add('r1', lambda t: SM.speech_card(t), name='speech0')
    en1 = CUE['EN1_end'] - 16.95
    add(en1, lambda t: SM.speech_card(t, 'en1', SD.EN_CLIPS['EN1']['en']), name='EN1')
    add('r2', lambda t: SM.plain_meaning(t), name='meaning')
    add('r4', lambda t: SM.speech_card(t, 'en2' if t > (CUE['EN2_end'] - 5.9 - CUE['r4']) else None,
                                       '…I call upon the scientific community in our country, those who gave us nuclear weapons…',
                                       'impotent and obsolete'), name='EN2')
    add('r5', lambda t: SM.shield_vs_spear(t), name='shield')
    add('r7', lambda t: SM.concept_art(t), name='art')
    add('r8', lambda t: SM.star_wars_name(t), name='starwars')
    add('r10', lambda t: S2.balance(t, 'shield'), name='balance2')
    add('r12', lambda t: SM.reagan_admits(t), name='admits')
    add('r13', lambda t: SM.takeaway(t, ['想逃出恐怖平衡的那一步', '恰恰最让对方害怕'], size=60), name='take')
    # ---- 04 excalibur
    add('x1', lambda t: SM.boost_decoy(t, 'boost'), hypo=True, name='boost')
    add('x3', lambda t: SM.boost_decoy(t + 4.2, 'decoy'), hypo=True, name='decoy')
    add('x4', lambda t: SM.quote_card(t, '“氢弹之父”泰勒 · 利弗莫尔实验室', '神剑\nX 射线激光', '1980 年代初的设想', col=WHITE), name='excal')
    add('x6', lambda t: SM.xray_schematic(t), hypo=True, name='xray')
    add('x8', lambda t: SM.submarine(t), hypo=True, name='sub')
    add('x9', lambda t: nevada_with_cards(t), name='nevada')
    add('x12', lambda t: S2.letter(t), name='letter')
    add('x13', lambda t: SM.unsent(t), name='unsent')
    add('x15', lambda t: SM.glow_mirror(t), name='mirror')
    add('x18', lambda t: SM.two_versions(t, '伍德拉夫辞职：两种说法',
                                         ('1985 年 · 他自己说', '与《科学》杂志的质疑\n“完全没有关系”', '《洛杉矶时报》1985-11-03'),
                                         ('1988 年 ·《洛杉矶时报》', '“给星球大战\n吹哨的人”', 'Los Angeles Times 1988-07-17')), name='woodruff')
    add('x20', lambda t: SM.takeaway(t, ['华盛顿：快造好了', '实验室：有没有', '都还说不清'], size=60), name='take')
    # ---- 05 HOE
    h2 = cue('h2') - cue('h1')
    add('h1', lambda t: S2.hoe(t, card=0.0, hit_t=h2 + 3.5), name='hit')
    strike = (sub_time('但这个计划在第三次试验前') or cue('h6') + 5) - cue('h5')
    add('h5', lambda t: S2.hoe(t + 2.0, card=smooth(remap(t, 0, 0.6)), hit_t=0.5, strike_t=strike), name='plan')
    add('h8', lambda t: SM.target_heat(t), name='target')
    add('h9', lambda t: SM.two_versions(t, '“试验造假”？',
                                        ('1993 ·《纽约时报》', '报道：试验\n被“操纵”', 'New York Times 1993-08-18'),
                                        ('1994 · 国会审计署', '作假计划存在，\n但没用在成功那次', 'GAO/NSIAD-94-219')), name='nyt')
    add('h11', lambda t: SM.takeaway(t, ['这场演示的一部分观众', '从一开始就在莫斯科'], size=60), name='take')
    # ---- 06 physics
    add('p2', lambda t: SM.orders(t * 0.9), name='orders')
    add('p6', lambda t: SM.pebbles(t), name='pebbles')
    add('p8', lambda t: SM.takeaway(t, ['天上的那面盾', '一块也没有部署']), name='take')
    # ---- 07 reykjavik
    add('k1', lambda t: SM.house(t), name='house')
    add('k4', lambda t: SM.table_cards(t), name='table')
    add('k7', lambda t: SM.party(t), name='party')
    add('k10', lambda t: SM.quote_card(t, '戈尔巴乔夫 · 10 月 11 日', '“你们连石油设备、\n牛奶厂的设备都不肯给，\n分享星球大战？”', '美苏双方会谈记录都有'), name='milk')
    add('k11', lambda t: SM.quote_card(t, '里根复述苏方的顾虑', '先打第一击，\n再用防御挡住报复', '据会谈记录', col=AMBER), name='firststrike')
    add('k12', lambda t: S2.reykjavik_lab(t), name='lab')
    add('k13', lambda t: SM.lab_quotes(t), name='labq')
    add('k15', lambda t: SM.memoir_vs_record(t), name='memoir')
    add('k16', lambda t: SM.memoir_lines(t * 0.8), name='memoir2')
    add('k20', lambda t: SM.two_views(t), name='views')
    add('k22', lambda t: SM.takeaway(t, ['一个还不存在的东西', '挡住了一个', '差点存在的世界']), name='take')
    # ---- 08 polyus
    add('s1', lambda t: SM.soviet_station(t), hypo=True, name='su_station')
    add('s3', lambda t: SM.energia_launch(t), name='launch')
    add('s4', lambda t: SM.polyus_specs(t), name='specs')
    add('s6', lambda t: SM.restrictions(t), name='restrict')
    add('s7', lambda t: S2.polyus_diagram(t * 0.6), name='tumble')
    add('s9', lambda t: SM.ocean_fall(t), name='fall')
    add('s10', lambda t: SM.takeaway(t, ['两边都在造一片天空', '两边都没有造出来']), name='take')
    # ---- 09 myth
    add('m1', lambda t: SM.inf_card(t), name='inf')
    add('m3', lambda t: SM.takeaway(t, ['真正的裁军', '是在把那片天空', '放到一边之后谈成的'], size=58), name='take')
    add('m4', lambda t: SM.quote_card(t, '流传很广的说法', '“星球大战\n拖垮了苏联”？', '', col=WHITE), name='myth')
    add('m6', lambda t: SM.soviet_projects(t), name='projects')
    add('m8', lambda t: SM.quote_card(t, '波德维格 2017', '“不太可能造成任何\n可测量的经济压力”', 'Science & Global Security 25:1'), name='podvig')
    add('m9', lambda t: SM.quote_card(t, '波德维格还发现', '星球大战给苏联国内\n主张对抗的人壮了胆', 'Podvig 2017'), name='embolden')
    add('m10', lambda t: SM.verdict(t), name='verdict')
    add('m11', lambda t: SM.takeaway(t, ['改变历史的', '不是它拖垮了谁', '而是双方的猜测'], size=60), name='take')
    # ---- 10 end
    add('e1', lambda t: ending(t), hypo=True, name='ending')
    S.sort(key=lambda s: s.start)
    for a, b in zip(S[:-1], S[1:]):
        a.end = b.start
    S[-1].end = TL['total']


def nevada_with_cards(t):
    c, e = SM.nevada(t)
    t10 = cue('x10') - cue('x9') - 0.25
    tdec = (sub_time('同年12月') or (cue('x10') + 5)) - cue('x9') - 0.25
    SM.date_card(c, '1983 年 3 月 26 日', '里根讲话后第三天 · 传感器故障', 1180, smooth(remap(t, t10, t10 + 0.5)) * (1 - smooth(remap(t, tdec - 0.3, tdec))))
    SM.date_card(c, '1983 年 12 月 16 日', '终于显示出了激光', 1180, smooth(remap(t, tdec, tdec + 0.5)), col=AMBER)
    return c, e


def ending(t):
    """replay of the imagined sky: beams go out, stations turn to wireframe and vanish."""
    end_total = TL['total'] - cue('e1')
    sky_t = 8.0 + min(t, 14.0) * 0.25
    fade = smooth(remap(t, 1.0, 9.0))
    diss = smooth(remap(t, 5.0, 16.0))
    c, e, cam = SKY.draw_sky(sky_t, mode='end', fade_beams=fade, dissolve=diss, show_missiles=t < 12.0)
    return c, e


def chapter_card(t, sec):
    c = S2.bg_reality('plain')
    e = np.zeros_like(c)
    k = smooth(remap(t, 0.0, 0.5))
    text(c, f"{sec['index']:02d}", W / 2, 760, 'type', 60, PAL['grey'], k, tracking=6)
    text(c, sec['chapter'], W / 2, 860, 'black', 96, PAL['white'], k, tracking=6)
    draw_polyline(e, [(W / 2 - 140 * k, 950), (W / 2 + 140 * k, 950)], PAL['us'] * 0.8, 2, k, add=True)
    return c, e


def finish_frame(c, e, fi, hypo):
    if hypo:
        img = c + e + bloom(e, 0.95) + bloom(c.clip(0.6, 5) - 0.6, 0.2)
        img = grade_hypo(img, 1.0)
        img = vignette(tonemap(img), 0.5)
        img = grain(img, fi, 0.016)
        fx.hypo_overlay(img)
        return img
    return S2.finish(c, e, fi)


def shot_at(t):
    for s in SHOTS:
        if s.start <= t < s.end:
            return s
    return None


def render_shot(s, t, fi):
    c, e = s.fn(t - s.start)
    return finish_frame(c, e, fi, s.hypo)


def render(t, fi):
    open_end = SEC['open']['end']
    if t < open_end:
        return render_open(t, fi)
    # chapter cards in the gap before each section's first line
    for sec in TL['sections'][1:]:
        first = cue([ln for ln in TL['lines'] if ln['sec'] == sec['sec']][0]['id'])
        if sec['chapter'] and first - 1.5 <= t < first - 0.25:
            c, e = chapter_card(t - (first - 1.5), sec)
            return S2.finish(c, e, fi)
    s = shot_at(t)
    if s is None:
        c, e = chapter_card(0.5, TL['sections'][1])
        return S2.finish(c, e, fi)
    img = render_shot(s, t, fi)
    # cross-fade from previous shot (no fade across hypo<->reality: those cut with a white flash)
    idx = SHOTS.index(s)
    if idx > 0 and t - s.start < XFADE:
        p = SHOTS[idx - 1]
        if p.hypo == s.hypo and p.end > p.start + XFADE:
            a = smooth((t - s.start) / XFADE)
            img = img * a + render_shot(p, t, fi) * (1 - a)
        elif p.hypo and not s.hypo and t - s.start < 2.0 / FPS:
            img = img + 1.4
    # chapter tag + subtitles
    sec = section_at(t)
    if sec['chapter'] and sec['sec'] not in ('open', 'end') and not s.hypo:
        fx.chapter_label(img, sec['index'], sec['chapter'])
    draw_subtitles(img, t)
    if sec['sec'] == 'end':
        end_card(img, t)
    return img


def end_card(img, t):
    t_last = TL['lines'][-1]['start'] + TL['lines'][-1]['dur'] + 1.0
    k = smooth(remap(t, t_last, t_last + 1.2))
    if k <= 0:
        return
    img *= (1 - 0.75 * k)
    text(img, '冷战核按钮 · 第二期', W / 2, 640, 'medium', 40, PAL['grey'], k, tracking=8)
    text(img, '一片没有出现的天空', W / 2, 740, 'black', 80, PAL['white'], k)
    refs = ['主要参考资料',
            '里根图书馆 · 1983-03-23 讲话讲稿与录音',
            '美国国会审计署 GAO/NSIAD-94-219（1994）等',
            '美国物理学会 定向能武器研究报告（1987）',
            '美国外交关系文件 FRUS 1981–88；美国国家安全档案馆',
            '舒尔茨《Turmoil and Triumph》（1993）',
            'Podvig, Science & Global Security 25:1（2017）',
            'Day & Kennedy, Air & Space（2010）；Lantratov（2005）',
            '《洛杉矶时报》1985、1988 年相关报道']
    for i, r in enumerate(refs):
        text(img, r, W / 2, 900 + i * 52, 'bold' if i == 0 else 'regular', 32 if i == 0 else 28,
             PAL['grey'] if i else PAL['white'], k)
