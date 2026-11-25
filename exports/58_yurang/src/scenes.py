# -*- coding: utf-8 -*-
"""各镜头画面。每个镜头函数签名 f(t, T, c) -> float 图 (H,W,3)：
t 镜头内时间，T 镜头时长，c 上下文（marks: 镜头内每句开始时刻；ends: 每句结束时刻；gt: 全片时间）。"""
import math
from functools import lru_cache
import numpy as np
from gfx import *
from art import *

import gfx as _g
import opencc as _oc
_T2S = _oc.OpenCC("t2s")
# 只有史书原文保留繁体；其余说明文字一律转简体
QUOTES = {"眾人遇我", "國士遇我", "且吾所爲者", "極難耳", "三躍而擊之", "漆其頭以爲飲器", "入宮塗廁", "中挾匕首", "心動", "欲爲智伯報仇！", "卒醳去之", "行乞於市　其妻不識",
          "滅鬚去眉 · 吞炭變音", "懷二心", "極難", "愧天下後世", "懷二心以事其君者", "馬驚", "此必是豫讓也", "無所知名", "甚尊寵之",
          "喟然嘆息而泣", "寡人不復釋子", "襄子大義之", "吾可以下報智伯矣", "趙國志士", "皆爲涕泣", "衣盡出血襄子回車車輪未周而亡",
          "太史公曰", "其義或成或不成", "然其立意較然", "不欺其志", "名垂後世", "豈妄也哉", "國士", "國士遇我　國士報之", "漆身",
          "吞炭", "妻不識也", "爲何獨爲智伯報仇之深？", "襄子立三十三年卒 ——《趙世家》", "傳說", "知己", "士"}


def _loc(lines, fnt):
    if isinstance(lines, str):
        lines = [lines]
    if getattr(fnt, "index", SC) == TC and "".join(lines) not in QUOTES:
        lines = [_T2S.convert(x) for x in lines]
        fnt = _g.font(fnt.path.split("-")[-1].split(".")[0], fnt.size, SC)
    return lines, fnt


def put_text(img, lines, fnt, *a, **kw):
    lines, fnt = _loc(lines, fnt)
    return _g.put_text(img, lines, fnt, *a, **kw)


TCF = lambda w, s: font(w, s, TC)
SCF = lambda w, s: font(w, s, SC)


def mk(c, i, default=None):
    m = c["marks"]
    if i < len(m):
        return m[i]
    return default if default is not None else 1e9


def ktext(img, lines, t, t0, fnt, xy, col=(1, 1, 1), dur_in=0.45, t_out=None, dur_out=0.35, rise=18, glow_col=None,
          glow_k=0.5, shadow=10, **kw):
    if isinstance(lines, str):
        lines = [lines]
    a = ramp(t, t0, t0 + dur_in)
    if t_out is not None:
        a *= 1 - ramp(t, t_out, t_out + dur_out)
    if a <= 0.002:
        return img
    y = xy[1] + rise * (1 - ease_out((t - t0) / dur_in if dur_in > 0 else 1))
    return put_text(img, lines, fnt, col, (xy[0], int(y)), alpha=a, glow_col=glow_col, glow_k=glow_k, shadow=shadow, **kw)


def panel(img, box, a=0.6, col="#05070b", border=GOLD_D, bk=0.8):
    x0, y0, x1, y1 = [int(v) for v in box]
    img = img.copy()
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + hexc(col) * a
    if bk > 0:
        for yy in (y0, y1 - 2):
            img[yy:yy + 2, x0:x1] = img[yy:yy + 2, x0:x1] * (1 - bk) + border * bk
    return img


def hline(img, x0, x1, y, col=GOLD, k=0.8, th=2):
    img = img.copy()
    img[y:y + th, int(x0):int(x1)] = img[y:y + th, int(x0):int(x1)] * (1 - k) + col * k
    return img


# ================================================================= 夜桥底图
@lru_cache(maxsize=4)
def bridge_static(variant="night"):
    if variant == "dawn":
        img = vgrad(H, W, hexc("#2b3447"), hexc("#c9b79a"), 1.3)
        img += radial(H, W, 820, 760, 900, 2.0)[:, :, None] * hexc("#f0c98a") * 0.45
        mrgb, mal = mountains(5, 4, 860, 1220, col_far="#8a8f9c", col_near="#3a3f4a", amp=380, mist="#d8cdb8")
    else:
        img = night_sky(1).copy()
        mrgb, mal = mountains(3, 4, 880, 1230, amp=420)
    img = over(img, mrgb, mal)
    b, ba, _ = bridge_layer(lit="#e8d2a8" if variant == "dawn" else "#9fb3d1")
    if variant == "dawn":
        b = b * 1.1 + 0.04
    img = over(img, b, ba)
    return img.astype(np.float32)


def bridge_scene(t, variant="night", mist_k=0.25, wl=1330):
    img = bridge_static(variant)
    img = water_reflect(img, wl, t, k=0.5 if variant == "night" else 0.6)
    if variant == "dawn":
        img = img + mist_layer(t, 7, y=1180, height=380, k=0.55, col="#e9e0cf")
        img = img + mist_layer(t * 0.6, 9, y=1500, height=300, k=0.35, col="#e9e0cf")
    else:
        img = img + mist_layer(t, 5, y=1250, height=360, k=mist_k)
    return img


ROBE_CUTS = [((330, 470), (760, 900)), ((770, 450), (310, 960)), ((260, 720), (840, 700))]


def robe_on(img, t, cuts_done, sep, cx=540, cy=720, sc=0.72, sway=1.0, glow_cut=None):
    rr, ra = robe_layer(cx, 720, sc)
    oy0 = cy - 720
    # 只在包围盒内运算（锦袍按 cy=720 生成，再整体平移 oy0）
    y0, y1, x0, x1 = 360, 1180, 160, 920
    sub_r, sub_a = rr[y0:y1, x0:x1], ra[y0:y1, x0:x1]
    if cuts_done:
        cuts = [((a[0] - x0, a[1] - y0), (b[0] - x0, b[1] - y0)) for a, b in ROBE_CUTS]
        sub_r, sub_a = _robe_cut_crop(sub_r, sub_a, cuts, cuts_done, sep)
    dx = int(6 * sway * math.sin(t * 1.3))
    dy = int(4 * sway * math.sin(t * 0.9 + 1)) + int(oy0)
    out = img.copy()
    ty0, ty1 = y0 + dy, y1 + dy
    cy0, cy1 = max(0, ty0), min(H, ty1)
    if cy1 <= cy0:
        return out
    sr_, sa_ = sub_r[cy0 - ty0:cy1 - ty0], sub_a[cy0 - ty0:cy1 - ty0]
    reg = out[cy0:cy1, x0 + dx:x1 + dx]
    sh = blur(sa_, 18)
    reg = reg * (1 - 0.45 * sh[:, :, None])
    reg = reg * (1 - sa_[:, :, None]) + sr_ * sa_[:, :, None]
    out[cy0:cy1, x0 + dx:x1 + dx] = reg
    return out


def _robe_cut_crop(rgb, al, cuts, n_done, sep):
    h, w = al.shape
    yy, xx = np.mgrid[:h, :w]
    label = np.zeros((h, w), np.int32)
    disp = []
    for i, (p0, p1) in enumerate(cuts[:n_done]):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        side = ((xx - p0[0]) * dy - (yy - p0[1]) * dx) > 0
        label |= (side.astype(np.int32) << i)
        L = math.hypot(dx, dy)
        disp.append((-dy / L, dx / L))
    out_rgb = np.zeros_like(rgb); out_a = np.zeros_like(al)
    for lab in range(2 ** n_done):
        mk_ = label == lab
        if not mk_.any():
            continue
        ox = oy = 0.0
        for i in range(n_done):
            s = -1 if (lab >> i) & 1 else 1
            k = sep[i]
            ox += s * disp[i][0] * k * 0.5
            oy += s * disp[i][1] * k * 0.5 + (k * 0.35 if s * disp[i][1] > 0 else 0)
        ox, oy = int(round(ox)), int(round(oy))
        a = np.roll(np.roll(np.where(mk_, al, 0), ox, 1), oy, 0)
        r = np.roll(np.roll(rgb * mk_[:, :, None], ox, 1), oy, 0)
        out_rgb += r; out_a += a
    return out_rgb / np.maximum(out_a, 1)[:, :, None], np.clip(out_a, 0, 1)


# ================================================================= s0 开场
HOOK_STRIKES = [0.42, 0.92, 1.42]   # 三声劈斩（与音效同步）


def v_hook(t, T, c):
    img = bridge_scene(t)
    # 推镜
    n = sum(1 for s in HOOK_STRIKES if t >= s + 0.12)
    sep = [min(1, (t - s - 0.12) / 0.5) * 20 if t >= s + 0.12 else 0 for s in HOOK_STRIKES]
    img = robe_on(img, t, n, sep)
    for i, s in enumerate(HOOK_STRIKES):
        if s <= t < s + 0.5:
            p0, p1 = ROBE_CUTS[i]
            ext = ((p0[0] - (p1[0] - p0[0]) * 0.25, p0[1] - (p1[1] - p0[1]) * 0.25),
                   (p1[0] + (p1[0] - p0[0]) * 0.25, p1[1] + (p1[1] - p0[1]) * 0.25))
            pr = min(1, (t - s) / 0.12)
            k = 1 - ramp(t, s + 0.12, s + 0.5)
            img = sword_flash(img, ext[0], ext[1], pr, width=9, k=k)
            img = img + (0.35 * k) * (t - s < 0.06)
    # 第三句再闪三下（「连砍三下」）
    m3 = mk(c, 2)
    e3 = c["ends"][2] if len(c["ends"]) > 2 else 1e9
    for i, s in enumerate([e3 - 1.3, e3 - 0.85, e3 - 0.4]):
        if s <= t < s + 0.4:
            p0, p1 = ROBE_CUTS[i]
            k = 1 - ramp(t, s + 0.1, s + 0.4)
            img = sword_flash(img, p0, p1, min(1, (t - s) / 0.1), width=6, k=k * 0.8)
    img = Particles(160, 3, (0, 200, W, 1300), (8, -20, 12), 6, (0.6, 1.6), hexc("#cfe0ff"), 10).draw(img, t, 0.6)
    img = kenburns_img(img, t, T, 1.0, 1.06)
    # 五个大字
    a = 1 - ramp(t, 2.6, 3.4)
    if a > 0:
        img = put_text(img, ["三躍而擊之"], TCF("Black", 150), GOLD, (W // 2, 300), alpha=a, glow_col=FIRE, glow_r=30,
                       glow_k=0.5, shadow=14, stroke=2, stroke_fill=(0.05, 0.03, 0.02))
        img = put_text(img, ["《史記·刺客列傳》"], SCF("Medium", 34), (0.85, 0.8, 0.7), (W // 2, 420), alpha=a)
    return img


def kenburns_img(img, t, T, z0, z1, cx=0.5, cy=0.45):
    z = z0 + (z1 - z0) * ease(t / max(T, 1e-3))
    if abs(z - 1) < 1e-3:
        return img
    M = np.float32([[z, 0, (1 - z) * W * cx], [0, z, (1 - z) * H * cy]])
    return cv2.warpAffine(np.ascontiguousarray(img, dtype=np.float32), M, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REFLECT)


def v_names(t, T, c):
    img = vgrad(H, W, hexc("#06080d"), hexc("#151b27"))
    img += radial(H, W, 280, 900, 600, 2)[:, :, None] * hexc("#3a2a1a") * 0.6
    img += radial(H, W, 800, 900, 600, 2)[:, :, None] * hexc("#1b2a44") * 0.8
    a1 = ramp(t, 0.1, 0.8)
    a2 = ramp(t, mk(c, 0) + 2.4, mk(c, 0) + 3.2)
    fm = figure_layer("walk", 300 - 30 * ease(t / T), 1300, 520)
    img = over(img, hexc("#030405"), fm * a1) + rim_light(fm, -5, 2, "#ffb46a", 0.8) * a1
    fz = figure_layer("stand", 790, 1300, 600, flip=True)
    img = over(img, hexc("#030405"), fz * a2) + rim_light(fz, 5, 2, "#9fb3d1", 0.9) * a2
    img = ktext(img, "豫讓", t, 0.2, TCF("Black", 140), (290, 520), GOLD, glow_col=FIRE)
    img = ktext(img, "刺客 · 晉國人", t, 0.5, SCF("Medium", 38), (290, 630), (0.85, 0.8, 0.7))
    img = ktext(img, "趙襄子", t, mk(c, 0) + 2.5, TCF("Black", 120), (790, 520), MOON, glow_col=BLUE)
    img = ktext(img, "趙氏宗主", t, mk(c, 0) + 2.8, SCF("Medium", 38), (790, 630), (0.75, 0.8, 0.9))
    if t > mk(c, 0) + 2.5:
        img = ktext(img, "VS", t, mk(c, 0) + 2.7, font("Black", 70, sans=True), (W // 2, 560), RED)
    return img


def charcoal_img(t, heat_k=1.0, zoom=1.0):
    base, heat = ember_bed()
    sh = int(t * 6) % 40
    hm = np.roll(heat, sh, 0) * (0.75 + 0.25 * math.sin(t * 2.3)) * heat_k
    img = base + heat_color(hm) * 1.1 + blur(heat_color(hm), 25) * 0.6
    img = img + smoke(t, 12, 0.35)
    img = Particles(220, 9, (0, 600, W, H), (0, -90, 30), 4, (0.8, 2.2), FIRE, 25, -2).draw(img, t, 1.0)
    return img


def v_charcoal_flash(t, T, c):
    img = charcoal_img(t)
    img = kenburns_img(img, t, T, 1.12, 1.0)
    # 背影剪影（不做毁容特写）
    fm = figure_layer("stand", 540, 2150, 1300)
    img = over(img, hexc("#020203"), fm * 0.92) + rim_light(fm, 0, 4, "#ff8a3a", 1.0)
    img = ktext(img, "漆身", t, 0.3, TCF("Black", 170), (300, 420), GOLD, glow_col=FIRE)
    img = ktext(img, "吞炭", t, mk(c, 0) + 3.2, TCF("Black", 170), (780, 420), GOLD, glow_col=FIRE)
    img = ktext(img, "妻不識也", t, mk(c, 0) + 5.4, TCF("Bold", 60), (W // 2, 640), (0.95, 0.9, 0.85))
    return img


def palace_img(t, n_strokes, fig=True, dagger=0.0, lantern=True):
    img = palace_wall().copy()
    m = plaster_strokes(t, n_strokes)
    img = over(img, hexc("#b9ad98"), m * 0.55)
    if lantern:
        img = torch_glow(img, [(900, 640)], t, 0.9, r=260, seed=1)
    if fig:
        fm = figure_layer("stand", 360, 1560, 820)
        img = over(img, hexc("#030305"), fm) + rim_light(fm, 5, 3, "#ffb46a", 0.7)
        # 泥刀
        tx = 520 + 60 * math.sin(t * 2.2)
        tm = mask_from_poly([[(tx, 980), (tx + 70, 960), (tx + 76, 975), (tx + 6, 996)]])
        img = over(img, hexc("#8d8a84"), tm)
        if dagger > 0:
            img = sword_flash(img, (300, 1080), (380, 1150), 1.0, width=4, k=dagger)
    return img


def v_palace_flash(t, T, c):
    img = palace_img(t, 3 + t * 2.5, dagger=0.6 + 0.4 * math.sin(t * 6) if t > 2 else 0)
    img = kenburns_img(img, t, T, 1.0, 1.08, 0.4, 0.55)
    img = ktext(img, "入宮塗廁", t, 0.3, TCF("Black", 130), (W // 2, 330), GOLD, glow_col=FIRE)
    img = ktext(img, "中挾匕首", t, 2.2, TCF("Black", 100), (W // 2, 480), (0.95, 0.92, 0.88), glow_col=RED)
    return img


def vessel_img(t, k=1.0):
    img = vgrad(H, W, hexc("#040305"), hexc("#120a08"))
    img += radial(H, W, 540, 900, 700, 2)[:, :, None] * hexc("#3a140c") * 0.7
    cand = [(220, 1180), (860, 1160)]
    img = torch_glow(img, cand, t, 0.7, r=220, seed=3)
    vm = mask_from_poly(vessel_polys(540, 820, 230), blur_r=1.0)
    # 漆面：黑里透红，一道高光，只做暗影
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    sheen = np.exp(-((xx - 470) / 40) ** 2 - ((yy - 860) / 160) ** 2) * 0.6
    col = hexc("#1a0503") + hexc("#5a120a") * radial(H, W, 600, 900, 300, 1.5)[:, :, None] + sheen[:, :, None] * hexc("#ff8a5a")
    img = over(img, col, vm * k)
    img = img + rim_light(vm, 3, -3, "#ff7a3a", 0.8) * k
    img = img + smoke(t, 14, 0.25, "#4a3a36")
    return img


def v_vessel(t, T, c):
    img = vessel_img(t)
    img = kenburns_img(img, t, T, 1.0, 1.1, 0.5, 0.48)
    img = ktext(img, "漆其頭以爲飲器", t, 0.6, TCF("Bold", 72), (W // 2, 360), (0.92, 0.85, 0.78), glow_col=RED,
                glow_k=0.4)
    return img


def v_question(t, T, c):
    img = vgrad(H, W, hexc("#05070b"), hexc("#10141d"))
    img = img + smoke(t, 15, 0.18, "#3a4152")
    m1 = mk(c, 1)
    y = 420
    img = ktext(img, "沒有人逼他", t, 0.2, TCF("Bold", 84), (W // 2, y), (0.92, 0.9, 0.86), t_out=m1 - 0.3)
    img = ktext(img, "事成也沒有賞賜", t, 1.3, TCF("Bold", 84), (W // 2, y + 140), (0.92, 0.9, 0.86), t_out=m1 - 0.3)
    img = ktext(img, "他圖什麼？", t, 2.6, TCF("Black", 150), (W // 2, y + 360), GOLD, glow_col=FIRE, t_out=m1 - 0.3)
    img = ktext(img, "趙襄子", t, m1 + 0.1, TCF("Black", 110), (W // 2, 360), MOON, glow_col=BLUE)
    img = ktext(img, "第一次：放了", t, m1 + 1.6, TCF("Bold", 80), (W // 2, 580), (0.92, 0.9, 0.86))
    img = ktext(img, "最後一次：給了衣服", t, m1 + 3.4, TCF("Bold", 80), (W // 2, 720), RED, glow_col=RED, glow_k=0.3)
    return img


def v_guoshi_title(t, T, c):
    img = charcoal_img(t, 0.45)
    img = img * 0.55
    img = ktext(img, ["國士"], t, 0.3, TCF("Black", 330), (W // 2, 800), GOLD, dur_in=0.7, glow_col=FIRE, glow_k=0.9,
                vertical=True, spacing=1.0, rise=0)
    img = ktext(img, "國士遇我　國士報之", t, 1.4, TCF("Bold", 56), (W // 2, 1250), (0.95, 0.9, 0.82))
    return img


# ================================================================= s1 地图
MAP_POS = dict(晋阳=(600, 630), 智=(300, 880), 韩=(560, 1130), 魏=(300, 1240), 赵=(780, 520))
COL = dict(智=RED, 韩=hexc("#d89a3a"), 魏=hexc("#9b6bd0"), 赵=BLUE)


@lru_cache(maxsize=1)
def map_base():
    img = vgrad(H, W, hexc("#0c0f0d"), hexc("#151a16"))
    hgt = fbm(W // 2, H // 2, 41, 7, 4, 0.55)
    hgt = np.asarray(Image.fromarray(hgt, "F").resize((W, H), Image.BICUBIC))
    gy, gx = np.gradient(hgt)
    shade = np.clip(0.5 + (gx - gy) * 120, 0, 1)
    img = img * (0.6 + 0.8 * shade[:, :, None]) + hexc("#2b3a28") * hgt[:, :, None] * 0.6
    # 太行山脉（右侧）
    yy, xx = np.mgrid[:H, :W].astype(np.float32)
    band = np.exp(-((xx - 900 - 40 * np.sin(yy / 200)) / 90) ** 2) * ((yy > 300) & (yy < 1300))
    img = img + band[:, :, None] * hexc("#4a4636") * 0.6 * shade[:, :, None]
    # 黄河、汾水
    yr = path([(140, 250), (190, 600), (120, 950), (220, 1300)], [(220, 1300), (500, 1360), (800, 1290), (1100, 1330)])
    fr = path([(640, 300), (560, 600), (560, 750), (430, 980)], [(430, 980), (330, 1150), (250, 1290)])
    rm = mask_from_poly([("line", yr, 16), ("line", fr, 8)], blur_r=1)
    img = over(img, hexc("#4c6f8f"), rm * 0.85)
    img = put_text(img, ["黄河"], SCF("Medium", 30), (0.6, 0.75, 0.88), (90, 700), vertical=True, alpha=0.8, spacing=1.0)
    img = put_text(img, ["汾水"], SCF("Medium", 30), (0.6, 0.75, 0.88), (520, 800), alpha=0.8)
    img = put_text(img, ["太行山"], SCF("Medium", 30), (0.75, 0.72, 0.6), (980, 800), vertical=True, alpha=0.7, spacing=1.0)
    img = img * vignette(0.5)
    return img.astype(np.float32)


def arrow_poly(ctrl, prog, w0=46, w1=30, head=70):
    pts = np.array(bezier(ctrl, 60), np.float32)
    n = max(2, int(len(pts) * min(1, max(prog, 0.02))))
    p = pts[:n]
    if len(p) < 2:
        return None
    d = np.gradient(p, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    wv = np.linspace(w0, w1, len(pts))[:n][:, None] / 2
    # 缩短给箭头留位置
    left = p + nrm * wv
    right = p - nrm * wv
    tip = p[-1] + d[-1] * head
    hb = p[-1] + nrm[-1] * (w1 * 1.2)
    hb2 = p[-1] - nrm[-1] * (w1 * 1.2)
    poly = [tuple(q) for q in left] + [tuple(hb), tuple(tip), tuple(hb2)] + [tuple(q) for q in right[::-1]]
    return poly


def draw_arrow(img, ctrl, prog, col, w0=46, w1=30, head=70, k=1.0):
    if prog <= 0:
        return img
    poly = arrow_poly(ctrl, prog, w0, w1, head)
    if poly is None:
        return img
    m = mask_from_poly([poly])
    img = img * (1 - blur(m, 10)[:, :, None] * 0.6 * k)
    img = over(img, col * 1.05, m * 0.92 * k)
    img = img + rim_light(m, 0, 4, col * 1.6, 0.6 * k)
    return img


def territory(name, k, shatter=0.0, t=0.0):
    cx, cy = MAP_POS[name]
    rng = np.random.default_rng(hash(name) % 1000)
    ang = np.linspace(0, 2 * math.pi, 36, endpoint=False)
    r = 150 + 40 * rng.random(36)
    r = np.convolve(np.r_[r[-2:], r, r[:2]], np.ones(5) / 5, "valid")
    pts = [(cx + rr * math.cos(a) * 1.1, cy + rr * math.sin(a) * 0.8) for rr, a in zip(r, ang)]
    return pts


def v_map(t, T, c):
    img = map_base().copy()
    m = c["marks"]
    gm = lambda i: mk(c, i)
    # 标题
    img = ktext(img, "晉陽之戰", t, 0.2, TCF("Black", 96), (W // 2, 250), GOLD, glow_col=FIRE, glow_k=0.3, t_out=gm(4) - 0.4)
    img = ktext(img, "公元前453年 · 三家滅智", t, 0.5, SCF("Medium", 36), (W // 2, 345), (0.85, 0.82, 0.72), t_out=gm(4) - 0.4)
    img = put_text(img, ["地图为示意"], SCF("Regular", 26), (0.7, 0.7, 0.65), (110, 1395), alpha=0.8)
    # 势力范围
    shat = ramp(t, gm(6) + 1.2, gm(6) + 2.6)
    for nm in ["智", "韩", "魏", "赵"]:
        a = ramp(t, gm(1) + {"智": 0.3, "韩": 1.2, "赵": 1.7, "魏": 2.2}[nm], gm(1) + 2.6)
        if a <= 0:
            continue
        pts = territory(nm, a)
        tm = mask_from_poly([pts], blur_r=6)
        kk = a * (1 - shat if nm == "智" else 1)
        img = over(img, COL[nm] * 0.55, tm * 0.32 * kk)
        img = img + rim_light(tm, 0, 3, COL[nm], 0.5 * kk)
        if nm == "智" and shat > 0:
            # 智氏碎裂：分给三家
            for j, (q, cc) in enumerate([(-1, COL["韩"]), (0, COL["赵"]), (1, COL["魏"])]):
                piece = [(x + q * 40 * shat, y + (j - 1) * 30 * shat) for x, y in pts]
                pm = mask_from_poly([piece], blur_r=3) * mask_from_poly([[(MAP_POS["智"][0] + (j - 1.5) * 110 + 10, 500),
                                                                           (MAP_POS["智"][0] + (j - 0.5) * 110, 500),
                                                                           (MAP_POS["智"][0] + (j - 0.5) * 110, 1100),
                                                                           (MAP_POS["智"][0] + (j - 1.5) * 110 + 10, 1100)]])
                img = over(img, cc * 0.6, pm * 0.5 * shat)
    # 晋阳城
    jx, jy = MAP_POS["晋阳"]
    cm = mask_from_poly([[(jx - 34, jy - 34), (jx + 34, jy - 34), (jx + 34, jy + 34), (jx - 34, jy + 34)]])
    cmi = mask_from_poly([[(jx - 24, jy - 24), (jx + 24, jy - 24), (jx + 24, jy + 24), (jx - 24, jy + 24)]])
    img = over(img, hexc("#e8dcc0"), np.clip(cm - cmi, 0, 1))
    img = put_text(img, ["晉陽"], TCF("Bold", 44), (0.95, 0.92, 0.85), (jx + 100, jy - 10), alpha=1.0)
    # 势力字
    for nm in ["智", "韩", "魏", "赵"]:
        a = ramp(t, gm(1) + {"智": 0.3, "韩": 1.2, "赵": 1.7, "魏": 2.2}[nm], gm(1) + 2.6)
        lab = {"智": "智", "韩": "韓", "魏": "魏", "赵": "趙"}[nm]
        sz = 120 if nm == "智" else 96
        if nm == "智":
            a *= 1 - shat
        img = put_text(img, [lab], TCF("Black", sz), COL[nm] * 1.3, MAP_POS[nm], alpha=a, glow_col=COL[nm], glow_k=0.5)
    # 索地
    for nm, ok in [("韩", True), ("魏", True), ("赵", False)]:
        t0 = gm(2) + {"韩": 0.2, "魏": 1.0, "赵": 2.0}[nm]
        a = ramp(t, t0, t0 + 0.6) * (1 - ramp(t, gm(3) - 0.4, gm(3)))
        if a > 0:
            x0, y0 = MAP_POS["智"]; x1, y1 = MAP_POS[nm]
            img = draw_arrow(img, [(x0, y0), ((x0 + x1) / 2, min(y0, y1) - 80), (x1 - (x1 - x0) * 0.25, y1 - (y1 - y0) * 0.25)],
                             ramp(t, t0, t0 + 0.6), COL["智"] * 0.8, 14, 10, 30, a)
            img = put_text(img, ["√" if ok else "×"], font("Black", 70, sans=True), (0.5, 0.9, 0.5) if ok else (1, 0.3, 0.25),
                           (x1 + 70, y1 - 70), alpha=ramp(t, t0 + 0.6, t0 + 0.9) * a)
    # 三家合围（粗箭头）
    p = lambda i0: ramp(t, gm(3) + i0, gm(3) + i0 + 1.4) * (1 - ramp(t, gm(6) - 0.2, gm(6) + 0.4))
    img = draw_arrow(img, [MAP_POS["智"], (380, 620), (jx - 80, jy + 20)], p(0.2), COL["智"])
    img = draw_arrow(img, [MAP_POS["韩"], (640, 860), (jx + 10, jy + 90)], p(0.6), COL["韩"])
    img = draw_arrow(img, [MAP_POS["魏"], (420, 900), (jx - 60, jy + 80)], p(1.0), COL["魏"])
    # 引水灌城
    fl = ramp(t, gm(3) + 2.4, gm(4) + 3.0) * (1 - ramp(t, gm(6) + 0.5, gm(6) + 2))
    if fl > 0:
        wm = radial(H, W, jx, jy + 20, 60 + 170 * fl, 0.8)
        wtex = 0.8 + 0.2 * np.sin(np.arange(W)[None, :] / 9 + t * 4)
        img = img + (wm * wtex)[:, :, None] * hexc("#3d7fc0") * 0.7 * fl
    # 密使
    if gm(5) < 1e8:
        a = ramp(t, gm(5) + 0.3, gm(5) + 0.8) * (1 - ramp(t, gm(6) + 0.5, gm(6) + 1.2))
        for dest in ["韩", "魏"]:
            pr = ramp(t, gm(5) + 0.5, gm(5) + 3.0)
            ctrl = [(jx, jy), ((jx + MAP_POS[dest][0]) / 2 + 120, (jy + MAP_POS[dest][1]) / 2), MAP_POS[dest]]
            pts = bezier(ctrl, 40)
            n = int(len(pts) * pr)
            dots = [("ellipse", (x - 6, y - 6, x + 6, y + 6)) for i, (x, y) in enumerate(pts[:n]) if i % 3 == 0]
            if dots:
                img = img + mask_from_poly(dots, blur_r=1)[:, :, None] * hexc("#ffe2a0") * a
    # 倒戈
    rv = lambda i0: ramp(t, gm(6) + i0, gm(6) + i0 + 1.2) * (1 - ramp(t, T - 0.8, T))
    zx, zy = MAP_POS["智"]
    img = draw_arrow(img, [MAP_POS["韩"], (450, 1000), (zx + 60, zy + 70)], rv(0.0), COL["韩"])
    img = draw_arrow(img, [MAP_POS["魏"], (230, 1050), (zx - 30, zy + 90)], rv(0.2), COL["魏"])
    img = draw_arrow(img, [(jx, jy), (450, 600), (zx + 60, zy - 60)], rv(0.4), COL["赵"])
    img = ktext(img, "三分其地", t, gm(6) + 1.8, TCF("Black", 90), (W // 2, 300), GOLD, glow_col=FIRE)
    return img


def v_vessel2(t, T, c):
    img = vessel_img(t, 1.0)
    img = kenburns_img(img, t, T, 1.05, 1.15, 0.5, 0.45)
    return img


def mountain_img(t, fig_x=None):
    img = vgrad(H, W, hexc("#0e1420"), hexc("#3d4a60"), 0.8)
    img += radial(H, W, 300, 500, 700, 2)[:, :, None] * hexc("#7d8aa3") * 0.35
    mrgb, mal = mountains(17, 6, 620, 1650, col_far="#5c6a82", col_near="#0b0e14", amp=620, mist="#a7b3c8")
    img = over(img, mrgb, mal)
    img = img + mist_layer(t, 19, y=1000, height=260, k=0.45, col="#b8c3d6", speed=10)
    img = img + mist_layer(t, 23, y=1450, height=200, k=0.35, col="#b8c3d6", speed=14)
    if fig_x is not None:
        fm = figure_layer("walk", fig_x, 1520, 220)
        img = over(img, hexc("#05070a"), fm)
    return img


def v_mountain(t, T, c):
    img = mountain_img(t, 380 + 40 * t / T)
    img = kenburns_img(img, t, T, 1.0, 1.08, 0.4, 0.7)
    return img


# ================================================================= 引文大字
def v_quote_big(t, T, c):
    q = c["quote"]
    style = c.get("qstyle", "fire")
    if style == "fire":
        img = charcoal_img(t, 0.35) * 0.35
    elif style == "dark":
        img = vgrad(H, W, hexc("#030304"), hexc("#0b0b10"))
        img += radial(H, W, 540, 700, 900, 2)[:, :, None] * hexc("#2a3550") * 0.5
        img = Particles(120, 5, (0, 0, W, H), (0, -12, 6), 8, (0.6, 1.4), hexc("#cfd8ff"), 6).draw(img, t, 0.5)
    else:
        img = mountain_img(t) * 0.45
    txt, src = q
    # 断句成行
    parts = [p for p in txt.replace("；", "；|").replace("。", "。|").replace("，", "，|").replace("！", "！|").split("|") if p]
    lines, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= 9:
            cur += p
        else:
            if cur:
                lines.append(cur)
            cur = p
    if cur:
        lines.append(cur)
    for ln in lines:
        QUOTES.add(ln)
    fs = 96 if max(len(x) for x in lines) <= 9 else 84
    n = len(lines)
    lh = fs * 1.45
    y0 = 860 - lh * (n - 1) / 2
    e = c["ends"][0] if c["ends"] else T
    for i, ln in enumerate(lines):
        t0 = 0.2 + (e - 0.6) * i / max(n, 1)
        img = ktext(img, ln, t, t0, TCF("Black", fs), (W // 2, int(y0 + i * lh)), GOLD, dur_in=0.6, glow_col=FIRE,
                    glow_k=0.55, rise=10)
    img = ktext(img, "—— " + src, t, 0.8, SCF("Medium", 34), (W // 2, int(y0 + n * lh + 30)), (0.85, 0.8, 0.7))
    return img


# ================================================================= s2 宫中
def v_palace(t, T, c):
    m = c["marks"]
    n = 1 + t * 1.2
    img = palace_img(t, n, dagger=(0.5 + 0.5 * math.sin(t * 5)) * ramp(t, mk(c, 2), mk(c, 2) + 0.5))
    img = kenburns_img(img, t, T, 1.0, 1.1, 0.35, 0.6)
    return img


def v_heart(t, T, c):
    img = vgrad(H, W, hexc("#050506"), hexc("#140808"))
    beat = (t % 1.0)
    pulse = math.exp(-beat * 9) + 0.6 * math.exp(-max(0, beat - 0.22) * 9) * (beat > 0.22)
    img += radial(H, W, 540, 1000, 900, 1.6)[:, :, None] * RED_D * (0.4 + 0.8 * pulse)
    fm = figure_layer("stand", 540, 2300, 1500)
    img = over(img, hexc("#020203"), fm) + rim_light(fm, 6, 2, "#ff6a4a", 0.8 + 0.6 * pulse)
    img = kenburns_img(img, t, T, 1.0 + 0.015 * pulse, 1.06 + 0.015 * pulse)
    img = ktext(img, ["心動"], t, mk(c, 0) + 1.8, TCF("Black", 240), (W // 2, 1000), (1, 0.92, 0.88), dur_in=0.25,
                glow_col=RED, glow_k=0.9, vertical=True, spacing=1.0, rise=0)
    return img


def guards_img(t, center=(540, 1300), n=7, r=360, close=0.0, kneel=True, torches=True):
    img = palace_wall().copy() * 0.7
    pts = []
    figs = []
    for i in range(n):
        a = math.pi * (0.1 + 0.8 * i / (n - 1))
        rr = r * (1 - 0.35 * close)
        x = center[0] + rr * math.cos(a) * 1.25
        y = center[1] - 90 + rr * math.sin(a) * -0.18 + (i % 2) * 20
        figs += figure_polys("stand", x, y + 160, 330, flip=x > center[0])
        figs.append(("line", [(x + (20 if x < center[0] else -20), y - 220), (x + (60 if x < center[0] else -60), y - 360)], 5))
        pts.append((x + (28 if x < center[0] else -28), y - 90))
    if torches:
        img = torch_glow(img, pts[::2], t, 0.9, r=200, seed=4)
    fm = mask_from_poly(figs, blur_r=0.8)
    img = over(img, hexc("#040405"), fm) + rim_light(fm, 0, -3, "#ff9a5a", 0.6)
    if kneel:
        km = figure_layer("kneel", center[0], center[1] + 120, 300)
        img = over(img, hexc("#020203"), km) + rim_light(km, 0, -4, "#ffb47a", 0.9)
    return img


def v_arrest(t, T, c):
    img = guards_img(t, close=ease(t / T))
    img = shake(img, t, 6 * (1 - ramp(t, 0, 0.8)))
    img = kenburns_img(img, t, T, 1.0, 1.08, 0.5, 0.65)
    img = ktext(img, "欲爲智伯報仇！", t, mk(c, 1) + 0.2, TCF("Black", 92), (W // 2, 380), (1, 0.9, 0.85), glow_col=RED)
    return img


def v_release(t, T, c):
    img = palace_wall().copy() * 0.6
    gate = radial(H, W, 900, 1250, 500, 1.4)
    img += gate[:, :, None] * hexc("#d9c9a8") * 0.6 * ramp(t, mk(c, 3) - 0.5, mk(c, 3) + 1)
    fz = figure_layer("stand", 300, 1560, 760)
    img = over(img, hexc("#030305"), fz) + rim_light(fz, 5, 2, "#c7d3e6", 0.8)
    # 豫让离去
    wx = 640 + 260 * ramp(t, mk(c, 3), T)
    fy = figure_layer("walk", wx, 1450, 380, flip=False)
    img = over(img, hexc("#030305"), fy * (1 - 0.5 * ramp(t, T - 2, T))) + rim_light(fy, -4, 2, "#ffd39a", 0.6)
    img = kenburns_img(img, t, T, 1.0, 1.05, 0.45, 0.6)
    img = ktext(img, "卒醳去之", t, mk(c, 3) + 0.1, TCF("Black", 110), (W // 2, 380), GOLD, glow_col=FIRE)
    img = ktext(img, "第一回合", t, mk(c, 4, T - 3), SCF("Medium", 40), (W // 2, 500), (0.8, 0.8, 0.8))
    return img


def card_box(img, x, y, w, h, title, items, t, t0, col, tcol=GOLD, a_max=0.85):
    a = ramp(t, t0, t0 + 0.5)
    if a <= 0:
        return img
    img = panel(img, (x, y, x + w, y + h), 0.55 * a, border=col, bk=0.9 * a)
    img = put_text(img, [title], TCF("Black", 100), tcol, (x + w // 2, y + 95), alpha=a, glow_col=col, glow_k=0.4)
    for i, (it, ti) in enumerate(items):
        img = ktext(img, it, t, ti, SCF("Bold", 44), (x + w // 2, y + 230 + i * 90), (0.93, 0.9, 0.85))
    return img


def v_mech_release(t, T, c):
    img = palace_wall().copy() * 0.25
    img = img + smoke(t, 33, 0.12, "#556070")
    img = ktext(img, "可以這樣理解", t, 0.2, TCF("Black", 84), (W // 2, 240), GOLD)
    img = ktext(img, "（今人解讀，非史書原意）", t, 0.6, SCF("Regular", 34), (W // 2, 330), (0.75, 0.75, 0.75))
    # 观众：一排眼睛
    m1 = mk(c, 1)
    a = ramp(t, m1, m1 + 0.6)
    if a > 0:
        for i in range(7):
            x = 150 + i * 130
            em = mask_from_poly([("ellipse", (x - 34, 470, x + 34, 500))], blur_r=1)
            pm = mask_from_poly([("ellipse", (x - 10, 474, x + 10, 496))])
            img = over(img, hexc("#d8d2c2"), em * a)
            img = over(img, hexc("#0a0a0a"), pm * a)
        img = put_text(img, ["智氏舊部 · 晉國士人　都在看"], SCF("Medium", 40), (0.85, 0.85, 0.85), (W // 2, 570), alpha=a)
    img = card_box(img, 70, 680, 440, 560, "殺", [("坐實仇家", mk(c, 2) + 0.8), ("寒了人心", mk(c, 2) + 2.2)], t, mk(c, 2),
                   RED, tcol=hexc("#ff7a66"))
    img = card_box(img, 570, 680, 440, 560, "放", [("敬重義士", mk(c, 3) + 0.8), ("名聲更值錢", mk(c, 3) + 2.2)], t,
                   mk(c, 3), GOLD)
    if t > mk(c, 3) + 3:
        img = ktext(img, "√", t, mk(c, 3) + 3, font("Black", 90, sans=True), (790, 1180), (0.6, 0.95, 0.6))
    img = ktext(img, "難題，拋回給了豫讓", t, mk(c, 4) + 2.5, TCF("Bold", 60), (W // 2, 1340), (0.95, 0.9, 0.85))
    return img


# ================================================================= s3 漆身吞炭
def v_charcoal(t, T, c):
    img = charcoal_img(t)
    img = kenburns_img(img, t, T, 1.15, 1.0)
    fm = figure_layer("stand", 540 + 30 * math.sin(t * 0.3), 2200, 1350)
    img = over(img, hexc("#020203"), fm * 0.9 * ramp(t, mk(c, 2) - 0.5, mk(c, 2) + 0.5)) + \
        rim_light(fm, 0, 4, "#ff8a3a", 1.0) * ramp(t, mk(c, 2) - 0.5, mk(c, 2) + 0.5)
    return img


def street_img(t, beggar=True, crowd=True, lantern_k=1.0):
    img = vgrad(H, W, hexc("#07080c"), hexc("#1a1712"))
    # 街两侧屋檐
    for side in (0, 1):
        x0 = 0 if side == 0 else W
        poly = [(x0, 300), (x0 + (360 if side == 0 else -360), 380), (x0 + (330 if side == 0 else -330), 1500), (x0, 1600)]
        img = over(img, hexc("#0b0c10"), mask_from_poly([poly]))
    img = torch_glow(img, [(250, 620), (830, 600), (540, 520)], t, 0.6 * lantern_k, r=200, seed=7)
    if crowd:
        figs = []
        for i in range(5):
            x = (130 + i * 230 + t * 40 * (1 if i % 2 else -1)) % (W + 200) - 100
            figs += figure_polys("walk", x, 1500 - (i % 2) * 40, 420 + (i % 2) * 40, flip=bool(i % 2))
        fm = mask_from_poly(figs, blur_r=1.5)
        img = over(img, hexc("#0e0d0f"), fm * 0.85)
    if beggar:
        bm = figure_layer("kneel", 230, 1620, 300)
        img = over(img, hexc("#030303"), bm) + rim_light(bm, 3, -3, "#ffb46a", 0.6)
    return img


def v_market(t, T, c):
    img = street_img(t)
    # 妻子走过（亮一点的轮廓）
    wx = 1000 - 700 * ramp(t, 0.3, mk(c, 1, T) if mk(c, 1, T) < 1e8 else T)
    wm = figure_layer("walk", wx, 1560, 470, flip=True)
    img = over(img, hexc("#0a090b"), wm) + rim_light(wm, -4, 0, "#ffcf9a", 0.9)
    img = kenburns_img(img, t, T, 1.0, 1.06, 0.4, 0.65)
    img = ktext(img, "行乞於市　其妻不識", t, 0.4, TCF("Bold", 66), (W // 2, 300), GOLD, glow_col=FIRE, glow_k=0.3,
                t_out=mk(c, 1) - 0.3 if len(c["marks"]) > 1 else None)
    img = ktext(img, "滅鬚去眉 · 吞炭變音", t, mk(c, 1) + 0.6, TCF("Bold", 60), (W // 2, 960), (0.95, 0.9, 0.85))
    img = ktext(img, "《戰國策》記載更細", t, mk(c, 1) + 0.2, SCF("Medium", 34), (W // 2, 1050), (0.8, 0.8, 0.75))
    return img


def v_friend(t, T, c):
    img = street_img(t, beggar=False, crowd=False, lantern_k=0.8)
    f1 = figure_layer("stand", 330, 1600, 620)
    f2 = figure_layer("kneel", 760, 1600, 520, flip=True)
    img = over(img, hexc("#030305"), f1) + rim_light(f1, 5, 0, "#ffd39a", 0.7)
    img = over(img, hexc("#030305"), f2) + rim_light(f2, -5, 0, "#ffd39a", 0.7)
    m = lambda i, d=None: mk(c, i, d)
    # 朋友的「捷径」
    steps = ["投靠襄子", "近身受寵", "再下手：易"]
    for i, s in enumerate(steps):
        img = ktext(img, s, t, m(1) + 0.6 + i * 1.6, TCF("Bold", 64), (W // 2, 340 + i * 120), (0.92, 0.92, 0.9),
                    t_out=m(3) + 0.2)
        if i < 2:
            img = ktext(img, "↓", t, m(1) + 1.3 + i * 1.6, font("Bold", 50, sans=True), (W // 2, 400 + i * 120), GOLD,
                        t_out=m(3) + 0.2)
    img = ktext(img, "懷二心", t, m(3) + 0.8, TCF("Black", 180), (W // 2, 500), RED, glow_col=RED, glow_k=0.7, dur_in=0.2,
                rise=0)
    if t > m(4) + 1.0:
        img = ktext(img, "＝ 高明的騙子", t, m(4) + 1.0, TCF("Bold", 60), (W // 2, 700), (0.95, 0.9, 0.85))
    return img


def v_hard_path(t, T, c):
    img = mountain_img(t) * 0.55
    # 两条路
    easy = path([(540, 1700), (420, 1400), (300, 1100)])
    hard = path([(540, 1700), (650, 1450), (720, 1250), (820, 1000), (900, 700)])
    a = ramp(t, 0.2, 1.0)
    em = mask_from_poly([("line", easy, 26)], blur_r=2)
    hm = mask_from_poly([("line", hard, 30)], blur_r=2)
    img = over(img, hexc("#8a8a8a"), em * 0.6 * a)
    img = over(img, GOLD, hm * a * ramp(t, 0.6, 1.4))
    img = img + blur(hm, 20)[:, :, None] * FIRE * 0.6 * ramp(t, 0.6, 1.4)
    img = ktext(img, "易：委质近身", t, 0.5, SCF("Bold", 46), (290, 1040), (0.75, 0.75, 0.75))
    img = ktext(img, "难：漆身吞炭", t, 1.0, SCF("Bold", 46), (850, 1000), GOLD)
    if t > 1.6:
        img = ktext(img, "×", t, 1.6, font("Black", 100, sans=True), (330, 1180), (1, 0.3, 0.25))
    to = mk(c, 1) - 0.2 if len(c["marks"]) > 1 else None
    img = ktext(img, "且吾所爲者", t, 0.4, TCF("Bold", 70), (W // 2, 260), (0.95, 0.92, 0.88), t_out=to)
    img = ktext(img, ["極難耳"], t, 1.0, TCF("Black", 200), (W // 2, 580), (1, 0.93, 0.85), glow_col=FIRE, glow_k=0.6,
                vertical=True, spacing=1.0, rise=0, t_out=to, dur_in=0.3)
    img = ktext(img, "《史記·刺客列傳》", t, 1.2, SCF("Medium", 32), (W // 2, 890), (0.8, 0.76, 0.68), t_out=to)
    return img


def peacock(img, t, cx, cy, k, scale=1.0):
    if k <= 0:
        return img
    polys_eye, polys_rach = [], []
    for i in range(23):
        a = math.pi * (0.08 + 0.84 * i / 22)
        L = (460 + 40 * math.sin(i * 1.7)) * scale * (0.3 + 0.7 * k)
        ex, ey = cx - L * math.cos(a), cy - L * math.sin(a) * 0.95
        polys_rach.append(("line", [(cx, cy), (ex, ey)], 3))
        r = 28 * scale
        polys_eye.append(("ellipse", (ex - r, ey - r * 1.3, ex + r, ey + r * 1.3)))
    rm = mask_from_poly(polys_rach, blur_r=1)
    em = mask_from_poly(polys_eye, blur_r=1)
    img = img + rm[:, :, None] * GOLD_D * 0.8 * k
    img = over(img, hexc("#1f6f66"), em * 0.8 * k)
    img = img + blur(em, 10)[:, :, None] * hexc("#2fb5a0") * 0.5 * k
    img = img + rim_light(em, 0, 2, GOLD, 0.8 * k)
    body = mask_from_poly([("ellipse", (cx - 40 * scale, cy - 80 * scale, cx + 40 * scale, cy + 70 * scale))])
    img = over(img, hexc("#14305a"), body * k)
    return img


def v_mech_signal(t, T, c):
    img = vgrad(H, W, hexc("#06080c"), hexc("#121823"))
    m = lambda i, d=None: mk(c, i, d)
    # 阶段：0-1 引子；2 不利条件原理图；3 孔雀；4 斯彭斯；5-6 回到豫让
    ph_chart = ramp(t, m(2), m(2) + 0.6) * (1 - ramp(t, m(3) - 0.3, m(3) + 0.2))
    ph_pea = ramp(t, m(3), m(3) + 0.6) * (1 - ramp(t, m(4) - 0.3, m(4) + 0.2))
    ph_sp = ramp(t, m(4), m(4) + 0.6) * (1 - ramp(t, m(5) - 0.3, m(5) + 0.2))
    ph_end = ramp(t, m(5), m(5) + 0.6)
    ph_intro = 1 - ramp(t, m(2) - 0.3, m(2) + 0.2)
    if ph_intro > 0:
        img = ktext(img, "朋友的辦法 → 更容易成功", t, 0.3, TCF("Bold", 60), (W // 2, 520), (0.8, 0.8, 0.8), t_out=m(2) - 0.3)
        img = ktext(img, "豫讓要的：", t, m(1), TCF("Bold", 70), (W // 2, 760), GOLD, t_out=m(2) - 0.3)
        img = ktext(img, "不可能被誤會", t, m(1) + 0.8, TCF("Black", 120), (W // 2, 920), (1, 0.95, 0.9), glow_col=FIRE,
                    t_out=m(2) - 0.3)
    if ph_chart > 0:
        k = ph_chart
        ox, oy, w, h = 170, 1330, 760, 620
        img = hline(img, ox, ox + w, oy, MOON, 0.8 * k, 3)
        img[oy - h:oy, ox:ox + 3] = img[oy - h:oy, ox:ox + 3] * (1 - 0.8 * k) + MOON * 0.8 * k
        img = put_text(img, ["信號的代價 →"], SCF("Medium", 38), MOON, (ox + w - 150, oy + 50), alpha=k)
        img = put_text(img, ["可信度"], SCF("Medium", 38), MOON, (ox + 70, oy - h - 30), alpha=k)
        pr = ramp(t, m(2) + 0.4, m(2) + 3)
        curve = [(ox + w * u, oy - h * (u ** 0.6) * 0.95) for u in np.linspace(0, pr, 40)]
        if len(curve) > 1:
            img = img + mask_from_poly([("line", curve, 8)], blur_r=1)[:, :, None] * GOLD * k
        pts = [("一句忠心話", 0.08), ("投靠後刺殺", 0.45), ("漆身吞炭", 0.95)]
        for i, (lab, u) in enumerate(pts):
            ta = m(2) + 1.5 + i * 1.6
            a = ramp(t, ta, ta + 0.4) * k
            x, y = ox + w * u, oy - h * (u ** 0.6) * 0.95
            img = over(img, FIRE if i == 2 else MOON, mask_from_poly([("ellipse", (x - 16, y - 16, x + 16, y + 16))]) * a)
            img = put_text(img, [lab], SCF("Bold", 42), FIRE if i == 2 else (0.85, 0.85, 0.85),
                           (min(x + 20, 880), y - 50 if i < 2 else y + 60), alpha=a, align="center")
    if ph_pea > 0:
        img = peacock(img, t, 540, 1250, ph_pea * ramp(t, m(3), m(3) + 1.5), 1.1)
        img = ktext(img, "我扛得起這個負擔", t, m(3) + 1.8, TCF("Black", 80), (W // 2, 420), GOLD, glow_col=FIRE,
                    t_out=m(4) - 0.3)
    if ph_sp > 0:
        img = ktext(img, "便宜的話　誰都會說", t, m(4) + 0.3, TCF("Bold", 70), (W // 2, 640), (0.8, 0.8, 0.8), t_out=m(5) - 0.3)
        img = ktext(img, "昂貴的付出　分開真假", t, m(4) + 2.5, TCF("Black", 76), (W // 2, 820), GOLD, glow_col=FIRE,
                    t_out=m(5) - 0.3)
        img = ktext(img, "Spence, 1973, 求職市場信號", t, m(4) + 0.6, SCF("Regular", 32), (W // 2, 1000), (0.7, 0.7, 0.7),
                    t_out=m(5) - 0.3)
    if ph_end > 0:
        for i, s in enumerate(["臉", "聲音", "家"]):
            ti = m(5) + 0.6 + i * 0.9
            img = ktext(img, s, t, ti, TCF("Black", 120), (230 + i * 310, 640), (0.95, 0.92, 0.88), t_out=m(7, T) - 0.4)
            if t > ti + 0.5:
                y = 640
                img = img + mask_from_poly([("line", [(130 + i * 310, y + 10), (330 + i * 310, y - 10)], 8)])[:, :, None] * RED * ramp(t, ti + 0.5, ti + 0.7) * (1 - ramp(t, m(7, T) - 0.4, m(7, T)))
        img = ktext(img, "代價越大　越不圖好處", t, m(5) + 3.5, TCF("Bold", 64), (W // 2, 860), GOLD, t_out=m(7, T) - 0.4)
        img = ktext(img, "難，本身就是他要說的話", t, m(7, T) + 0.2, TCF("Black", 76), (W // 2, 760), (1, 0.93, 0.85),
                    glow_col=FIRE, glow_k=0.6)
    return img


# ================================================================= s4 桥下
def v_bridge_ambush(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = bridge_scene(t, mist_k=0.3)
    # 桥下暗影里的人
    hm = figure_layer("kneel", 560, 1325, 200)
    img = over(img, hexc("#020203"), hm * 0.95) + rim_light(hm, 2, -2, "#6f86aa", 0.6)
    # 马与骑者
    rear = 1.0 - ramp(t, m(1), m(1) + 0.5) * (1 - ramp(t, m(1) + 2.5, m(1) + 3.5)) * 1.0
    hx = 260 + 120 * ramp(t, 0, m(1))
    hsm = horse_layer(int(hx), 1050, 440, rear=round(0.35 + 0.65 * rear, 2))
    img = over(img, hexc("#030304"), hsm) + rim_light(hsm, 3, -3, "#ffb46a", 0.7)
    tor = [(hx - 120, 900), (hx - 220, 930), (hx + 260, 920)]
    close = ramp(t, m(3), m(3) + 2.5)
    tor += [(560 - 200 + 60 * close, 1180 + 60 * close), (560 + 220 - 60 * close, 1180 + 60 * close)] if close > 0 else []
    img = torch_glow(img, tor, t, 0.9, r=190, seed=8)
    img = shake(img, t - m(1), 10 * (1 - ramp(t, m(1), m(1) + 0.8)) * (t > m(1)))
    z1 = 1.18 if t > m(2) else 1.04
    img = kenburns_img(img, t, T, 1.0, z1, 0.5, 0.62)
    img = ktext(img, "馬驚", t, m(1) + 0.1, TCF("Black", 150), (W // 2, 360), (1, 0.92, 0.85), dur_in=0.15, rise=0,
                glow_col=RED, t_out=m(2) - 0.2)
    return img


def lords_row(img, t, t0, k=1.0):
    xs = [220, 540, 860]
    names = ["范氏", "中行氏", "智伯"]
    for i, (x, nm) in enumerate(zip(xs, names)):
        a = ramp(t, t0 + i * 0.3, t0 + i * 0.3 + 0.4) * k
        img = panel(img, (x - 130, 560, x + 130, 760), 0.6 * a, border=GOLD_D, bk=0.8 * a)
        img = put_text(img, [nm], TCF("Black", 64), GOLD if i == 2 else (0.9, 0.88, 0.85), (x, 660), alpha=a)
    return img


def v_interrogation(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = guards_img(t, center=(700, 1320), n=5, r=300, close=0.6, kneel=True)
    fz = figure_layer("stand", 230, 1650, 820, flip=False)
    img = over(img, hexc("#030305"), fz) + rim_light(fz, 5, 0, "#c7d3e6", 0.8)
    img = kenburns_img(img, t, T, 1.0, 1.05, 0.4, 0.6)
    img = img * (1 - 0.45 * ramp(t, m(1) - 0.3, m(1) + 0.3))
    if t > m(1) - 0.3:
        img = lords_row(img, t, m(1))
        # 智伯灭范、中行
        for i, x in enumerate([220, 540]):
            ti = m(1) + 2.0 + i * 0.5
            if t > ti:
                a = ramp(t, ti, ti + 0.3)
                img = img + mask_from_poly([("line", [(x - 100, 590), (x + 100, 730)], 10), ("line", [(x + 100, 590), (x - 100, 730)], 10)])[:, :, None] * RED * a
        img = ktext(img, "不報仇", t, m(1) + 3.6, TCF("Bold", 56), (380, 840), (0.9, 0.85, 0.8))
        img = ktext(img, "反而投靠 →", t, m(1) + 4.6, TCF("Bold", 56), (760, 840), GOLD)
        img = ktext(img, "爲何獨爲智伯報仇之深？", t, m(2) + 0.3, TCF("Black", 72), (W // 2, 1000), (1, 0.93, 0.88),
                    glow_col=RED, glow_k=0.4)
        img = ktext(img, "如果只是「忠」……", t, m(3) + 1.8, TCF("Bold", 60), (W // 2, 1140), (0.8, 0.8, 0.8))
    return img


def crowd_seen(img, t, spot, dim_k=1.0):
    figs = []
    for row in range(4):
        for i in range(7):
            x = 90 + i * 150 + (row % 2) * 70
            y = 1000 + row * 160
            if row == 2 and i == 3:
                continue
            figs += figure_polys("stand", x, y, 220 + row * 25)
    fm = mask_from_poly(figs, blur_r=1)
    img = over(img, hexc("#2a2d33") * dim_k, fm * 0.9)
    # 中间那个人
    x, y = 90 + 3 * 150, 1000 + 2 * 160
    one = figure_layer("stand", x, y, 270)
    if spot > 0:
        beam = mask_from_poly([[(x - 40, 0), (x + 40, 0), (x + 200, y + 20), (x - 200, y + 20)]], blur_r=30)
        img = img + beam[:, :, None] * hexc("#ffe2a8") * 0.35 * spot
    img = over(img, hexc("#2a2d33") * (1 - spot) + hexc("#0a0806") * spot, one)
    img = img + rim_light(one, 0, 4, "#ffd690", 1.2 * spot)
    return img


def v_seen(t, T, c):
    """marks: 0 白话 1 战国策注 2 无所知名(卡) 3 甚尊宠之 4 被看见 5 士阶层"""
    m = lambda i, d=None: mk(c, i, d)
    img = vgrad(H, W, hexc("#06070a"), hexc("#14161c"))
    spot = ramp(t, m(3), m(3) + 1.0)
    img = crowd_seen(img, t, spot)
    img = ktext(img, "眾人遇我", t, 0.4, TCF("Bold", 72), (300, 640), (0.75, 0.75, 0.75), t_out=m(3) - 0.2)
    img = ktext(img, "國士遇我", t, 1.6, TCF("Black", 80), (780, 640), GOLD, glow_col=FIRE, t_out=m(2) - 0.2)
    img = ktext(img, "甚尊寵之", t, m(3) + 0.3, TCF("Black", 120), (W // 2, 660), GOLD, glow_col=FIRE, t_out=m(4) + 0.2)
    img = ktext(img, "不只是俸禄，是被看见", t, m(4) + 0.8, TCF("Black", 72), (W // 2, 660), (1, 0.94, 0.86), glow_col=FIRE,
                glow_k=0.4, t_out=m(5, T) - 0.2)
    if len(c["marks"]) > 5:
        img = ktext(img, "士", t, m(5) + 0.2, TCF("Black", 190), (W // 2, 400), GOLD, glow_col=FIRE)
        img = ktext(img, "有才，无世袭地位", t, m(5) + 1.6, TCF("Bold", 56), (W // 2, 600), (0.92, 0.9, 0.86))
        img = ktext(img, "谁肯赏识，为谁效力", t, m(5) + 4.4, TCF("Bold", 56), (W // 2, 700), (0.92, 0.9, 0.86))
        img = ktext(img, "知己", t, m(5) + 7.5, TCF("Black", 110), (W // 2, 850), RED, glow_col=RED, glow_k=0.5)
    return img


def scale_draw(img, t, tilt, lk, rk, ll, rl, a=1.0):
    cx, cy = 540, 900
    img = img + mask_from_poly([[(cx - 8, cy), (cx + 8, cy), (cx + 30, cy + 520), (cx - 30, cy + 520)]])[:, :, None] * GOLD_D * a
    ang = tilt
    L = 380
    lx, ly = cx - L * math.cos(ang), cy - L * math.sin(ang)
    rx, ry = cx + L * math.cos(ang), cy + L * math.sin(ang)
    img = img + mask_from_poly([("line", [(lx, ly), (rx, ry)], 10)])[:, :, None] * GOLD * a
    for (x, y, k, lab) in [(lx, ly, lk, ll), (rx, ry, rk, rl)]:
        img = img + mask_from_poly([("line", [(x, y), (x - 90, y + 200)], 3), ("line", [(x, y), (x + 90, y + 200)], 3)])[:, :, None] * GOLD_D * a
        pan = mask_from_poly([[(x - 130, y + 200), (x + 130, y + 200), (x + 90, y + 240), (x - 90, y + 240)]])
        img = over(img, GOLD_D, pan * a)
        wsz = 30 + 60 * k
        wm = mask_from_poly([[(x - wsz, y + 200), (x + wsz, y + 200), (x + wsz * 0.7, y + 200 - wsz * 1.3), (x - wsz * 0.7, y + 200 - wsz * 1.3)]])
        img = over(img, FIRE if k > 0.7 else MOON * 0.7, wm * a)
        img = put_text(img, [lab], TCF("Bold", 50), (0.95, 0.92, 0.88), (x, y + 310), alpha=a)
    return img


def v_mech_recip(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = vgrad(H, W, hexc("#06080c"), hexc("#11151e"))
    st = ramp(t, m(2), m(2) + 1.5)  # 从众人到国士
    k = 0.15 + 0.85 * st
    a = ramp(t, m(1) - 0.2, m(1) + 0.5)
    img = scale_draw(img, t, 0.0 + 0.02 * math.sin(t * 1.5), k, k, "給你的待遇", "還你的分量", a)
    lab = "眾人 ⇄ 眾人" if st < 0.5 else "國士 ⇄ 國士"
    img = ktext(img, lab, t, m(1) + 0.6 if st < 0.5 else m(2) + 0.6, TCF("Black", 84), (W // 2, 680),
                (0.85, 0.85, 0.85) if st < 0.5 else GOLD, glow_col=None if st < 0.5 else FIRE,
                t_out=m(2) if st < 0.5 else None)
    img = ktext(img, "不是無條件的忠，是對等的回報", t, m(3) + 0.5, TCF("Bold", 54), (W // 2, 1300), (0.95, 0.9, 0.85))
    return img


def v_org(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = vgrad(H, W, hexc("#070a10"), hexc("#141b28"))
    img = ktext(img, "放到今天的組織裏", t, 0.2, TCF("Bold", 64), (W // 2, 260), (0.9, 0.9, 0.9), t_out=m(1) - 0.3)
    base = 1300
    for i, (lab, col) in enumerate([("A", MOON), ("B", GOLD)]):
        x = 330 + i * 420
        # 薪水（一样）
        a = ramp(t, 0.8, 1.4)
        h1 = 260 * a
        img = over(img, hexc("#3b4a63"), mask_from_poly([[(x - 150, base - h1), (x - 20, base - h1), (x - 20, base), (x - 150, base)]]))
        # 投入
        eff = ramp(t, m(0) + 2.5, m(0) + 4.0) * (260 if i == 0 else 760)
        img = over(img, col, mask_from_poly([[(x + 20, base - eff), (x + 150, base - eff), (x + 150, base), (x + 20, base)]]))
        img = put_text(img, ["薪水"], SCF("Medium", 36), (0.75, 0.8, 0.9), (x - 85, base + 50), alpha=a)
        img = put_text(img, ["投入"], SCF("Medium", 36), col, (x + 85, base + 50), alpha=a)
    img = ktext(img, "只交差", t, m(0) + 4.0, TCF("Bold", 56), (330, 980), MOON)
    img = ktext(img, "拼了命", t, m(0) + 4.4, TCF("Black", 64), (750, 480), GOLD, glow_col=FIRE, t_out=m(2, T) + 2.0)
    img = ktext(img, "差別不在錢", t, m(1) + 0.2, TCF("Black", 76), (W // 2, 250), (1, 0.94, 0.88))
    img = ktext(img, "而在有沒有被當成一個人物", t, m(1) + 1.5, TCF("Bold", 54), (W // 2, 360), GOLD)
    if len(c["marks"]) > 2:
        img = ktext(img, "螺絲釘", t, m(2) + 0.3, TCF("Bold", 50), (330, 1060), (0.7, 0.7, 0.7))
        img = ktext(img, "人物", t, m(2) + 2.4, TCF("Black", 64), (750, 480), FIRE, glow_col=FIRE)
    return img


def v_zhibo(t, T, c):
    img = vgrad(H, W, hexc("#050506"), hexc("#120d0a"))
    fm = figure_layer("stand", 540, 1700, 1000)
    dis = ramp(t, 1.5, 4.5)
    img = over(img, hexc("#1a1410"), fm * (1 - dis * 0.8)) + rim_light(fm, 4, 0, "#c79a5a", 0.6 * (1 - dis))
    img = Particles(400, 21, (300, 700, 780, 1700), (30, -60, 25), 5, (0.6, 1.8), hexc("#c79a5a"), 20).draw(img, t, dis)
    img = ktext(img, "智伯", t, 0.2, TCF("Black", 120), (W // 2, 330), (0.85, 0.75, 0.6))
    img = ktext(img, "貪婪 · 傲慢 · 身死族滅", t, 0.8, TCF("Bold", 56), (W // 2, 460), (0.8, 0.75, 0.7))
    img = ktext(img, "但他看見了這個人", t, max(3.5, T - 3.2), TCF("Black", 84), (W // 2, 620), GOLD, glow_col=FIRE)
    return img


# ================================================================= s5 高潮
def bridge_ring(t, close=0.5, figs=("kneel",), zhao=True, n_t=8):
    img = bridge_scene(t, mist_k=0.2)
    # 火把圈
    pts = []
    for i in range(n_t):
        a = 2 * math.pi * i / n_t + 0.2
        r = 420 - 140 * close
        pts.append((540 + r * math.cos(a), 1010 + 0.18 * r * math.sin(a) - 60))
    img = torch_glow(img, pts, t, 1.0, r=170, seed=9)
    gp = []
    for (x, y) in pts:
        gp += figure_polys("stand", x, y + 130, 230)
    gm_ = mask_from_poly(gp, blur_r=1)
    img = over(img, hexc("#050506"), gm_ * 0.9)
    if "kneel" in figs:
        km = figure_layer("kneel", 560, 1080, 230)
        img = over(img, hexc("#020203"), km) + rim_light(km, 0, -3, "#ffbf80", 1.0)
    if zhao:
        zm = figure_layer("stand", 250, 1110, 330)
        img = over(img, hexc("#030304"), zm) + rim_light(zm, 3, -2, "#c7d3e6", 0.8)
    return img


def v_surround(t, T, c):
    img = bridge_ring(t, close=ramp(t, mk(c, 2) - 0.5, T))
    img = kenburns_img(img, t, T, 1.0, 1.12, 0.45, 0.55)
    img = ktext(img, "寡人不復釋子", t, mk(c, 1) + 3.0, TCF("Black", 100), (W // 2, 330), (1, 0.9, 0.85), glow_col=RED)
    return img


def v_request(t, T, c):
    img = bridge_ring(t, close=1.0)
    img = kenburns_img(img, t, T, 1.12, 1.3, 0.5, 0.56)
    img = img * 0.85
    return img


def v_robe_given(t, T, c):
    img = bridge_ring(t, close=1.0, figs=())
    drop = ease_out(t / min(T, 4.0))
    img = robe_on(img, t, 0, [0, 0, 0], cy=int(720 - 500 * (1 - drop)))
    km = figure_layer("stand", 560, 1080, 260)
    img = over(img, hexc("#020203"), km) + rim_light(km, 0, -3, "#ffbf80", 1.0)
    img = kenburns_img(img, t, T, 1.0, 1.06, 0.5, 0.5)
    img = ktext(img, "襄子大義之", t, 0.3, TCF("Black", 110), (W // 2, 260), GOLD, glow_col=FIRE)
    return img


def v_strike(t, T, c):
    """慢镜头三击。c['strikes'] 为三击在镜头内的时刻。"""
    st = c["strikes"]
    img = bridge_ring(t, close=1.0, figs=(), zhao=False)
    n = sum(1 for s in st if t >= s + 0.15)
    sep = [min(1, (t - s - 0.15) / 0.7) * 30 if t >= s + 0.15 else 0 for s in st]
    img = robe_on(img, t, n, sep, sway=0.4)
    # 跃起
    jump = 0
    for s in st:
        if s - 0.35 <= t < s + 0.4:
            jump = max(jump, math.sin(math.pi * (t - s + 0.35) / 0.75))
    x = 300 + 40 * math.sin(t * 2.0)
    fm = figure_layer("strike", x, 1090 - 120 * jump, 420)
    img = over(img, hexc("#020203"), fm) + rim_light(fm, 4, -3, "#ffd39a", 1.2)
    for i, s in enumerate(st):
        if s <= t < s + 0.9:
            p0, p1 = ROBE_CUTS[i]
            ext = ((p0[0] - (p1[0] - p0[0]) * 0.3, p0[1] - (p1[1] - p0[1]) * 0.3),
                   (p1[0] + (p1[0] - p0[0]) * 0.3, p1[1] + (p1[1] - p0[1]) * 0.3))
            k = 1 - ramp(t, s + 0.2, s + 0.9)
            img = sword_flash(img, ext[0], ext[1], min(1, (t - s) / 0.2), width=12, k=k * 1.2)
            if t - s < 0.08:
                img = img + 0.5
    # 碎布、火星粒子
    if n:
        img = Particles(260, 31, (250, 450, 830, 1000), (0, 30, 60), 3, (0.8, 2.0), hexc("#ffcf8a"), 40, 20).draw(img, t, ramp(t, st[0], st[0] + 0.3))
    img = kenburns_img(img, t, T, 1.05, 1.22, 0.5, 0.5)
    img = shake(img, t, 7 * max((1 - ramp(t, s, s + 0.35)) if t >= s else 0 for s in st))
    return img


def v_final_words(t, T, c):
    img = np.zeros((H, W, 3), np.float32) + hexc("#030304")
    img += radial(H, W, 540, 300, 1300, 1.6)[:, :, None] * hexc("#2a3550") * 0.5 * ramp(t, 0, 1)
    img = Particles(80, 41, (0, 0, W, H), (0, -10, 4), 10, (0.5, 1.2), hexc("#ffe0a0"), 4).draw(img, t, 0.5)
    img = ktext(img, ["吾可以下報智伯矣"], t, 0.15, TCF("Black", 132), (W // 2, 860), GOLD,
                dur_in=1.0, glow_col=FIRE, glow_k=0.7, vertical=True, spacing=1.0, rise=0, tracking=6)
    img = ktext(img, "《史記·刺客列傳》", t, 1.2, SCF("Medium", 34), (W // 2, 1520), (0.8, 0.76, 0.68))
    return img


def v_fallen(t, T, c):
    img = bridge_scene(t, mist_k=0.4) * 0.8
    # 剑横在桥面，碎袍落地；不出现身体
    sm = mask_from_poly([[(380, 1028), (760, 1016), (762, 1022), (382, 1036)]])
    img = img + sm[:, :, None] * hexc("#dfe8f5") * 0.9 + blur(sm, 12)[:, :, None] * hexc("#9fb8e0") * 0.6
    cloth = mask_from_poly([[(600, 1040), (720, 1030), (760, 1050), (640, 1062)], [(470, 1045), (560, 1040), (540, 1060)]], blur_r=1)
    img = over(img, hexc("#4a100c"), cloth)
    img = kenburns_img(img, t, T, 1.15, 1.25, 0.52, 0.53)
    return img


def v_tears(t, T, c):
    img = vgrad(H, W, hexc("#04060a"), hexc("#10141c"))
    # 远处城郭剪影
    city = [(0, 1250), (120, 1250), (120, 1180), (300, 1180), (300, 1230), (520, 1230), (520, 1150), (560, 1120), (600, 1150),
            (600, 1230), (820, 1230), (820, 1190), (1080, 1190), (1080, 1920), (0, 1920)]
    img = over(img, hexc("#05070a"), mask_from_poly([city]))
    img = Particles(160, 51, (0, 1000, W, 1600), (0, -26, 5), 14, (0.8, 2.0), hexc("#ffcf8a"), 12).draw(img, t, 0.9)
    img = Particles(300, 52, (0, 0, W, H), (-3, 140, 10), 6, (0.3, 0.8), hexc("#8fa3c4"), 0).draw(img, t, 0.5, flick=False)
    img = ktext(img, "趙國志士", t, 0.4, TCF("Black", 110), (W // 2, 360), (0.9, 0.92, 1))
    img = ktext(img, "皆爲涕泣", t, 1.4, TCF("Black", 110), (W // 2, 500), (0.9, 0.92, 1), glow_col=BLUE, glow_k=0.4)
    img = ktext(img, "《史記·刺客列傳》", t, 2.0, SCF("Medium", 32), (W // 2, 610), (0.75, 0.78, 0.85))
    return img


def v_legend(t, T, c):
    img = vgrad(H, W, hexc("#0b0a09"), hexc("#191512"))
    p = paper_tex()
    box = (170, 230, 910, 1080)
    a = ramp(t, 0.2, 0.9)
    pm = mask_from_poly([[(box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]], blur_r=2)
    img = over(img, p * 0.9, pm * a)
    cols = ["衣盡出血", "襄子回車", "車輪未周而亡"]
    img = put_text(img, cols, TCF("Bold", 70), (0.12, 0.1, 0.09), (540, 640), alpha=a * 0.95, vertical=True, spacing=1.4,
                   shadow=1, shadow_k=0.0)
    img = put_text(img, ["司馬貞《史記索隱》引《戰國策》"], SCF("Medium", 32), (0.25, 0.22, 0.2), (540, 1030), alpha=a, shadow=1,
                   shadow_k=0)
    # 红印「传说」
    sa = ramp(t, 3.0, 3.3)
    if sa > 0:
        s0 = 1.0 + 0.4 * (1 - sa)
        sm = mask_from_poly([[(760 - 60 * s0, 340 - 70 * s0), (760 + 60 * s0, 340 - 70 * s0), (760 + 60 * s0, 340 + 70 * s0),
                              (760 - 60 * s0, 340 + 70 * s0)]])
        img = over(img, hexc("#a8261c"), sm * 0.85 * sa)
        img = put_text(img, ["傳說"], TCF("Black", 52), (0.97, 0.9, 0.85), (760, 340), alpha=sa, vertical=True,
                       spacing=1.0, shadow=1, shadow_k=0)
    m1 = mk(c, 1)
    img = ktext(img, "今本《戰國策》無此文", t, m1 + 0.4, TCF("Bold", 58), (W // 2, 1170), (0.95, 0.9, 0.85))
    img = ktext(img, "《史記》未載", t, m1 + 2.0, TCF("Bold", 58), (W // 2, 1260), (0.95, 0.9, 0.85))
    img = ktext(img, "襄子立三十三年卒 ——《趙世家》", t, m1 + 4.0, SCF("Medium", 38), (W // 2, 1350), (0.8, 0.78, 0.72))
    return img


# ================================================================= s6 收束
def v_dawn(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = bridge_scene(t, "dawn")
    img = kenburns_img(img, t, T, 1.12, 1.0, 0.5, 0.55)
    img = img * (1 - 0.35 * ramp(t, m(1) - 0.3, m(1) + 0.3))
    band = np.exp(-((np.arange(H, dtype=np.float32) - 400) / 260) ** 2)[:, None, None]
    img = img * (1 - 0.55 * band)
    img = ktext(img, "沒人逼　沒回報", t, 0.4, TCF("Bold", 66), (W // 2, 300), (0.95, 0.92, 0.86),
                t_out=m(1) - 0.3)
    img = ktext(img, "爲何拼命？", t, 1.8, TCF("Black", 110), (W // 2, 440), GOLD, glow_col=FIRE, t_out=m(1) - 0.3)
    img = ktext(img, "一筆「被看見」的債", t, m(1) + 0.5, TCF("Black", 92), (W // 2, 330), (1, 0.95, 0.85), glow_col=FIRE,
                glow_k=0.3, t_out=m(2) - 0.3)
    img = ktext(img, "不走捷徑　不懷二心", t, m(1) + 5.0, TCF("Bold", 64), (W // 2, 470), (1, 0.95, 0.88), t_out=m(2) - 0.3)
    img = ktext(img, "敬重義士", t, m(2) + 2.5, TCF("Black", 96), (W // 2, 330), (1, 0.95, 0.85), glow_col=FIRE, glow_k=0.3,
                t_out=m(3, T) - 0.3)
    img = ktext(img, "＝ 告訴天下：我值得追隨", t, m(2) + 4.5, TCF("Bold", 60), (W // 2, 470), (1, 0.95, 0.88),
                t_out=m(3, T) - 0.3)
    if len(c["marks"]) > 3:
        img = ktext(img, "同一套規矩　互相成全", t, m(3) + 1.5, TCF("Black", 80), (W // 2, 380), (1, 0.95, 0.85),
                    glow_col=FIRE, glow_k=0.3)
    return img


def v_takeaway(t, T, c):
    img = bridge_scene(t, "dawn") * 0.45
    lines = ["一個人願意爲你拼到什麼程度", "往往取決於", "你當初把他當成什麼人"]
    for i, ln in enumerate(lines):
        img = ktext(img, ln, t, 0.3 + i * 1.3, TCF("Black", 72 if i != 1 else 56), (W // 2, 700 + i * 140),
                    GOLD if i == 2 else (1, 0.96, 0.9), glow_col=FIRE if i == 2 else None, glow_k=0.5)
    return img


def v_taishigong(t, T, c):
    m = lambda i, d=None: mk(c, i, d)
    img = bridge_scene(t, "dawn")
    img = kenburns_img(img, t, T, 1.0, 1.08, 0.5, 0.6)
    img = img * 0.42
    cols = ["太史公曰", "其義或成或不成", "然其立意較然", "不欺其志", "名垂後世", "豈妄也哉"]
    n = len(cols)
    fs = 74
    colw = int(fs * 1.55)
    x0 = W // 2 + (n - 1) * colw // 2
    t_start = m(1) - 0.3
    for i, cl in enumerate(cols):
        ti = (m(0) + 0.5) if i == 0 else t_start + (i - 1) * (max(m(2) - t_start, 6) / (n - 1))
        col = GOLD if i == 0 else (0.96, 0.92, 0.84)
        img = ktext(img, [cl], t, ti, TCF("Black", fs if i else 60), (x0 - i * colw, 300 + (len(cl) * (fs + 4)) // 2),
                    col, dur_in=0.9, vertical=True, spacing=1.0, rise=0, shadow=8, shadow_k=0.7,
                    glow_col=None, tracking=4)
    img = ktext(img, "《史記·刺客列傳》", t, m(1) + 1.0, SCF("Medium", 34), (W // 2, 1000), (0.85, 0.8, 0.7))
    if len(c["marks"]) > 3:
        a = ramp(t, m(3) + 0.3, m(3) + 1.2)
        img = img * (1 - 0.5 * a)
        img = ktext(img, "不欺其志", t, m(3) + 3.5, TCF("Black", 150), (W // 2, 1250), GOLD, glow_col=FIRE, glow_k=0.6)
    return img


VIS = dict(hook=v_hook, names=v_names, charcoal_flash=v_charcoal_flash, palace_flash=v_palace_flash, vessel=v_vessel,
           question=v_question, guoshi_title=v_guoshi_title, map=v_map, vessel2=v_vessel2, mountain=v_mountain,
           quote_big=v_quote_big, palace=v_palace, heart=v_heart, arrest=v_arrest, release=v_release,
           mech_release=v_mech_release, charcoal=v_charcoal, market=v_market, friend=v_friend, hard_path=v_hard_path,
           mech_signal=v_mech_signal, bridge_ambush=v_bridge_ambush, interrogation=v_interrogation, seen=v_seen,
           mech_recip=v_mech_recip, org=v_org, zhibo=v_zhibo, surround=v_surround, request=v_request,
           robe_given=v_robe_given, strike=v_strike, final_words=v_final_words, fallen=v_fallen, tears=v_tears,
           legend=v_legend, dawn=v_dawn, takeaway=v_takeaway, taishigong=v_taishigong)

# 每句用哪个画面（相邻同名合并为一个镜头）
LINE_VIS = {
    "s0_01": "hook", "s0_02": "hook", "s0_03": "hook", "s0_04": "names", "s0_05": "charcoal_flash",
    "s0_06": "palace_flash", "s0_07": "vessel", "s0_08": "question", "s0_09": "question", "s0_10": "guoshi_title",
    **{f"s1_{i:02d}": "map" for i in range(1, 8)}, "s1_08": "vessel2", "s1_09": "vessel2", "s1_10": "mountain",
    "s1_11": "quote_big", "s1_12": "mountain2", "s1_13": "mountain2",
    "s2_01": "palace", "s2_02": "palace", "s2_03": "palace", "s2_04": "heart", "s2_04b": "heart", "s2_05": "arrest",
    "s2_06": "arrest", "s2_07": "release", "s2_08": "release", "s2_09": "release", "s2_10": "release", "s2_10b": "release",
    **{k: "mech_release" for k in ["s2_11", "s2_12", "s2_13", "s2_14", "s2_15"]},
    "s3_01": "charcoal", "s3_02": "charcoal", "s3_03": "charcoal", "s3_04": "market", "s3_05": "market",
    **{k: "friend" for k in ["s3_06", "s3_07", "s3_08", "s3_09", "s3_09b"]}, "s3_10": "hard_path", "s3_11": "hard_path",
    **{k: "mech_signal" for k in ["s3_12", "s3_13", "s3_14", "s3_15", "s3_15b", "s3_16", "s3_16b", "s3_17"]},
    **{k: "bridge_ambush" for k in ["s4_01", "s4_02", "s4_02b", "s4_03", "s4_04"]},
    **{k: "interrogation" for k in ["s4_05", "s4_06", "s4_07", "s4_08", "s4_09"]}, "s4_10": "quote_big2",
    **{k: "seen" for k in ["s4_11", "s4_12", "s4_13", "s4_14", "s4_15", "s4_15b"]},
    **{k: "mech_recip" for k in ["s4_16", "s4_17", "s4_17b", "s4_18"]},
    **{k: "org" for k in ["s4_19", "s4_20", "s4_20b"]}, "s4_21": "zhibo",
    **{k: "surround" for k in ["s5_01", "s5_02", "s5_03", "s5_03b"]},
    **{k: "request" for k in ["s5_04", "s5_05", "s5_06", "s5_07"]}, "s5_08": "robe_given", "s5_09": "robe_given",
    "s5_10": "strike", "s5_11": "final_words", "s5_12": "final_words", "s5_13": "fallen", "s5_14": "tears",
    "s5_15": "legend", "s5_16": "legend",
    **{k: "dawn" for k in ["s6_01", "s6_02", "s6_03", "s6_03b"]}, "s6_04": "takeaway",
    **{k: "taishigong" for k in ["s6_05", "s6_06", "s6_07", "s6_08"]},
}
ALIAS = {"mountain2": "mountain", "quote_big2": "quote_big"}
# 这些镜头本身就展示原文，不再叠原文卡
NO_CARD = {"quote_big", "quote_big2", "final_words", "legend", "taishigong", "vessel", "tears"}
NO_CARD_LINES = {"s3_10"}
