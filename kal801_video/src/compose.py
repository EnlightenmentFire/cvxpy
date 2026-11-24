# -*- coding: utf-8 -*-
"""时间线 + 帧合成：把 beats（及配音时长）排成时间线，按时间 t 画出整帧。"""
import json
import os

import skia

import scenes as SC
from render_lib import (C, W, H, SIDE, SAFE_TOP, rgb, font, draw_text, line, ease, clamp, fade_io, subtitle,
                        split_subtitle, section_tag, vignette)
from script_data import B, SECTION_TITLES, SOURCES

CHAPTER_DUR = 1.5
GPWS_DUR = {"five hundred": 1.05, "one thousand": 1.05, "minimums. minimums.": 1.55, "sink rate.": 0.95,
            "one hundred. fifty. forty. thirty. twenty.": 2.1}
NO_TAG = {"cold", "title", "impact", "memorial", "end", "credits", "chapter"}
XFADE = 0.45


def est_dur(x):
    if x["say"]:
        n = len(x["say"].replace(" ", ""))
        return n / (4.6 if x["tempo"] == "quote" else 5.0)
    if x["gpws"]:
        return GPWS_DUR.get(x["gpws"], 1.2)
    if x["q"]:
        return 1.4
    return 0.0


def build_timeline(manifest=None, gpws_manifest=None):
    manifest = manifest or {}
    gpws_manifest = gpws_manifest or {}
    tl = []
    t = 0.0
    cur_sec = None
    for x in B:
        if x["sec"] != cur_sec and x["sec"] in SECTION_TITLES:
            tl.append(dict(id=f"ch{x['sec']}", sec=x["sec"], scene="chapter", say=None, sub=None, q=None, gpws=None,
                           gap=0, tempo="narr", key=False, ev={}, start=t, dur=CHAPTER_DUR, adur=0))
            t += CHAPTER_DUR
        cur_sec = x["sec"]
        if x["say"] and x["id"] in manifest:
            ad = manifest[x["id"]]["dur"]
        elif x["gpws"] and x["gpws"] in gpws_manifest:
            ad = gpws_manifest[x["gpws"]]["dur"]
        else:
            ad = est_dur(x)
        lead = 0.0
        if x["q"] and x["say"]:
            lead = 0.35          # 卡片先出现，再开口
        d = lead + ad + x["gap"]
        e = dict(x)
        e.update(start=t, dur=d, adur=ad, lead=lead)
        tl.append(e)
        t += d
    # 场景分段 & 舞台起点
    run_start, run_scene = 0.0, None
    stage_start = {}
    first_align = None
    for e in tl:
        if e["scene"] != run_scene:
            run_scene, run_start = e["scene"], e["start"]
            stage_start = {}
            first_align = None
        e["scene_start"] = run_start
        st = e["ev"].get("stage") or e["ev"].get("side") or e["ev"].get("at")
        if st is not None and st not in stage_start:
            stage_start[st] = e["start"]
        e["stage_start"] = dict(stage_start)
        if e["ev"].get("align") and first_align is None:
            first_align = e["start"]
        e["first_align"] = first_align
    return tl, t


def find(tl, t):
    lo, hi = 0, len(tl) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if tl[mid]["start"] <= t:
            lo = mid
        else:
            hi = mid - 1
    return lo


def profile_clock(tl, i, t):
    """剖面场景：钟表时间在相邻 beat 的 ev.t 之间线性推进。"""
    e = tl[i]
    t0 = SC.hms(e["ev"].get("t", "01:39:44"))
    nxt = None
    for j in range(i + 1, len(tl)):
        if tl[j]["scene"] != "profile":
            break
        if tl[j]["ev"].get("t"):
            nxt = SC.hms(tl[j]["ev"]["t"])
            break
    if nxt is None:
        nxt = SC.T_IMPACT
    k = clamp((t - e["start"]) / max(e["dur"], 0.01))
    if nxt < t0:
        nxt = t0
    return t0 + (nxt - t0) * k


def profile_marks(tl, i):
    marks = []
    for j in range(i, -1, -1):
        e = tl[j]
        if e["scene"] != "profile":
            break
        if e["q"]:
            col = C["red"] if e["q"]["t"] >= "01:42:19" else (C["cyan"] if e["q"]["who"] == "管制员" else C["amber"])
            marks.append((e["q"]["t"], e["q"]["t"], col))
    return marks


def state_for(tl, i, t):
    e = tl[i]
    S = dict(t=t, ts=t - e["scene_start"], tb=t - e["start"], bd=e["dur"], beat=e)
    S["ts_stage"] = {k: t - v for k, v in e["stage_start"].items()}
    if e["scene"] == "profile":
        S["tclock"] = profile_clock(tl, i, t)
        S["marks"] = profile_marks(tl, i)
        if any(tl[j]["ev"].get("ghost") for j in range(i - 3, i) if 0 <= j and tl[j]["scene"] == "profile"):
            S["ghost"] = True
    if e["scene"] == "cold":
        s4 = next((x for x in tl if x["id"] == "s0_04"), None)
        if s4:
            S["ts_beat_group"] = t - s4["start"]
    if e["scene"] == "cheese" and e["first_align"] is not None:
        S["first_align_tb"] = t - e["first_align"]
    return S


def draw_chapter(c, S):
    e = S["beat"]
    c.clear(rgb("#03060C"))
    a = fade_io(S["tb"], S["bd"], 0.35, 0.35)
    sec = e["sec"]
    draw_text(c, f"{sec:02d}", W / 2, 860, font(120, "mono", 700), C["amber"], a * 0.9, "center")
    line(c, W / 2 - 60, 905, W / 2 + 60, 905, C["amber"], a * 0.7, 3)
    draw_text(c, SECTION_TITLES[sec], W / 2, 1000, font(76, "sans", 900), C["text"], a, "center")


def draw_scene(c, S, zoom=True):
    e = S["beat"]
    sc = e["scene"]
    c.save()
    if zoom and sc not in ("cold", "impact", "memorial", "end", "credits", "chapter"):
        z = 1.0 + 0.035 * clamp(S["ts"] / 40.0)
        c.translate(W / 2, H * 0.45)
        c.scale(z, z)
        c.translate(-W / 2, -H * 0.45)
    if sc == "chapter":
        draw_chapter(c, S)
    elif sc == "credits":
        SC.draw_credits(c, S, SOURCES)
    else:
        SC.SCENES[sc](c, S)
    c.restore()


def draw_overlays(c, S):
    e = S["beat"]
    sc = e["scene"]
    if sc not in NO_TAG and e["sec"] in SECTION_TITLES:
        section_tag(c, e["sec"], SECTION_TITLES[e["sec"]], 1.0)
    text = e.get("sub") or e.get("say")
    if text and sc not in ("end",):
        pages = split_subtitle(text)
        ad = max(e["adur"], 0.1)
        tt = S["tb"] - e.get("lead", 0)
        lens = [sum(len(s) for s in p) for p in pages]
        tot = sum(lens)
        acc, idx = 0.0, len(pages) - 1
        for k, n in enumerate(lens):
            acc += n / tot * ad
            if tt < acc:
                idx = k
                break
        a = clamp((tt + 0.15) / 0.18) * clamp((e["dur"] - S["tb"]) / 0.18)
        if e.get("wordpages"):
            idx = e["wordpages"](tt)
        subtitle(c, pages[idx], a, key=e["key"])


def render(tl, t, surface=None, surface2=None):
    surface = surface or skia.Surface(W, H)
    c = surface.getCanvas()
    i = find(tl, t)
    S = state_for(tl, i, t)
    draw_scene(c, S)
    # 场景切换交叉淡化
    e = tl[i]
    if i > 0 and e["scene"] != tl[i - 1]["scene"] and (t - e["start"]) < XFADE and e["scene"] not in ("impact",) \
            and tl[i - 1]["scene"] not in ("impact",):
        surface2 = surface2 or skia.Surface(W, H)
        c2 = surface2.getCanvas()
        Sp = state_for(tl, i - 1, t)
        draw_scene(c2, Sp)
        img = surface2.makeImageSnapshot()
        p = skia.Paint()
        p.setAlphaf(1 - ease((t - e["start"]) / XFADE))
        c.drawImage(img, 0, 0, skia.SamplingOptions(), p)
    draw_overlays(c, S)
    return surface


def load_manifests(work):
    m, g = {}, {}
    p = os.path.join(work, "manifest.json")
    if os.path.exists(p):
        m = json.load(open(p, encoding="utf-8"))
    p = os.path.join(work, "gpws_manifest.json")
    if os.path.exists(p):
        g = json.load(open(p, encoding="utf-8"))
    return m, g
