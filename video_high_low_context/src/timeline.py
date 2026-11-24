# -*- coding: utf-8 -*-
"""Turn the structured script + clip durations into an absolute timeline."""
import re

GAP_N = 0.26        # between narration lines
GAP_EN = 0.32       # after an English clip
SEG_TAIL = 0.75     # end of a segment
CHAPTER_IN = 1.35   # chapter card before first line
TRANS = 0.85        # "翻译中…" duration


def est_dur(text, cps=5.4):
    """Rough duration estimate for a Chinese line (used before audio exists)."""
    n = len(re.sub(r"[\s，。、：；！？“”…—]", "", text))
    p = len(re.findall(r"[，。、：；！？…]", text))
    return n / cps + p * 0.12 + 0.2


def est_en(text):
    return 0.45 + len(text.split()) * 0.30


def build(segments, dur=None):
    """dur: dict clip_id -> seconds (missing -> estimate)."""
    dur = dur or {}

    def D(cid, fallback):
        return dur.get(cid, fallback)

    tl = dict(segs=[], narr=[], clips=[], cards=[], takeaways=[], sfx=[], total=0)
    t = 0.0
    for si, seg in enumerate(segments):
        S = dict(id=seg["id"], chapter=seg.get("chapter", ""), idx=si, t0=t, scenes=[],
                 trig={}, shiyi=seg.get("shiyi", False), history=seg.get("history", False))
        S["scenes"].append((t, seg["scene"]))
        if seg.get("chapter"):
            S["chapter_t"] = t
            tl["sfx"].append((t + 0.1, "whoosh"))
            t += CHAPTER_IN
        open_card = None
        quick = []

        def close_card(at):
            nonlocal open_card
            if open_card is not None and open_card.get("t_end") is None:
                open_card["t_end"] = at
            open_card = None

        for ii, it in enumerate(seg["items"]):
            cid = f"{seg['id']}_{ii:02d}"
            k = it["kind"]
            if it.get("scene"):
                close_card(t)
                S["scenes"].append((t, it["scene"]))
            if it.get("show"):
                S["trig"][it["show"]] = t
            if it.get("vignette"):
                close_card(t)
                S["trig"].setdefault("vignettes", []).append((t, it["vignette"]))
            if k in ("N", "Q"):
                d = D(cid, est_dur(it["text"]) * (1.12 if k == "Q" else 1.0))
                line = dict(t0=t, t1=t + d, text=it["text"], kind=k, cid=cid, seg=seg["id"],
                            takeaway=it.get("takeaway", False))
                if it.get("over_quick") and quick:
                    n = len(quick)
                    for qi, qc in enumerate(quick):
                        qc["t_zh"] = t + qi * d / (n + 0.4)
                        qc["t_lit"] = qc["t_zh"] + 0.25
                        qc["t_real"] = qc["t_zh"] + 0.9
                        qc["t_trans"] = qc["t_zh"] + 0.3
                    quick = []
                if it.get("reveal") == "real" and open_card is not None:
                    open_card["t_real"] = t
                    tl["sfx"].append((t, "ding"))
                if it.get("reveal") == "why" and open_card is not None:
                    open_card["t_why"] = t + 0.3
                if it.get("beat"):
                    S["trig"][it["beat"]] = t
                if line["takeaway"]:
                    close_card(t)
                    tl["takeaways"].append(line)
                tl["narr"].append(line)
                tl["clips"].append(dict(t=t, cid=cid, kind="narr" if k == "N" else "quote"))
                t += d + GAP_N
            elif k == "E":
                close_card(t)
                de = D(cid + "_en", est_en(it["en"]))
                card = dict(kind="E", seg=seg["id"], spk=it["spk"], en=it["en"], lit=it["lit"],
                            real=it["real"], why=it["why"], t0=t, t_end=None)
                tl["clips"].append(dict(t=t, cid=cid + "_en", kind="en", spk=it["spk"]))
                tl["sfx"].append((t - 0.05, "pop"))
                t += de + GAP_EN
                card["t_lit"] = t - GAP_EN + 0.08
                if it.get("say_lit"):
                    d = D(cid + "_lit", est_dur(it["say_lit"]))
                    tl["narr"].append(dict(t0=t, t1=t + d, text=it["say_lit"], kind="N",
                                           cid=cid + "_lit", seg=seg["id"]))
                    tl["clips"].append(dict(t=t, cid=cid + "_lit", kind="narr"))
                    t += d + GAP_N
                card["t_trans"] = t
                tl["sfx"].append((t, "type"))
                if it.get("hold_real"):
                    card["t_real"] = None
                    card["t_why"] = None
                else:
                    t += TRANS
                    card["t_real"] = t
                    tl["sfx"].append((t, "ding"))
                    if it.get("say_real"):
                        d = D(cid + "_real", est_dur(it["say_real"]))
                        tl["narr"].append(dict(t0=t, t1=t + d, text=it["say_real"], kind="N",
                                               cid=cid + "_real", seg=seg["id"]))
                        tl["clips"].append(dict(t=t, cid=cid + "_real", kind="narr"))
                        card["t_why"] = t + min(d * 0.5, 2.2) if it["why"] else None
                        t += d + GAP_N + 0.15
                    else:
                        card["t_why"] = t + 0.9 if it["why"] else None
                        t += 2.4 + (0.9 if it["why"] else 0)
                tl["cards"].append(card)
                open_card = card
            elif k == "C":
                if it.get("quick"):
                    card = dict(kind="CQ", seg=seg["id"], zh=it["zh"], lit=it["lit"], real=it["real"],
                                why=it.get("why", ""), slot=len(quick), t_end=None)
                    quick.append(card)
                    tl["cards"].append(card)
                    continue
                close_card(t)
                card = dict(kind="C", seg=seg["id"], zh=it["zh"], lit=it["lit"], real=it["real"],
                            why=it["why"], t0=t, t_end=None)
                if it.get("quote"):
                    d = D(cid + "_q", est_dur(it["zh"]) * 1.12)
                    tl["narr"].append(dict(t0=t, t1=t + d, text="“" + it["zh"] + "”", kind="Q",
                                           cid=cid + "_q", seg=seg["id"], hide_caption=True))
                    tl["clips"].append(dict(t=t, cid=cid + "_q", kind="quote"))
                    tl["sfx"].append((t - 0.05, "pop"))
                    t += d + GAP_EN
                card["t_lit"] = t - 0.1
                card["t_trans"] = t + 0.5
                tl["sfx"].append((t + 0.5, "type"))
                t += 0.5 + TRANS
                card["t_real"] = t
                tl["sfx"].append((t, "ding"))
                if it.get("say"):
                    d = D(cid + "_say", est_dur(it["say"]))
                    tl["narr"].append(dict(t0=t, t1=t + d, text=it["say"], kind="N",
                                           cid=cid + "_say", seg=seg["id"]))
                    tl["clips"].append(dict(t=t, cid=cid + "_say", kind="narr"))
                    card["t_why"] = t + d * 0.5 if it["why"] else None
                    t += d + GAP_N
                else:
                    card["t_why"] = t + 1.3 if it["why"] else None
                    t += 3.2 + (1.4 if it["why"] else 0)
                tl["cards"].append(card)
                open_card = card
            elif k == "J":
                d = D(cid + "_jp", 1.3)
                tl["clips"].append(dict(t=t, cid=cid + "_jp", kind="jp"))
                S["trig"]["jp"] = t
                S["trig"]["jp_end"] = t + d
                tl["narr"].append(dict(t0=t, t1=t + d, text=f"{it['text']}（{it['display']}）", kind="J",
                                       cid=cid + "_jp", seg=seg["id"], hide_caption=False))
                t += d + 0.45
            elif k == "BEAT":
                S["trig"][it.get("tag") or f"beat{ii}"] = t
                t += it["sec"]
        close_card(t + SEG_TAIL * 0.6)
        t += SEG_TAIL
        S["t1"] = t
        tl["segs"].append(S)
    # close any card still open at its segment end
    for c in tl["cards"]:
        if c.get("t_end") is None:
            seg = next(s for s in tl["segs"] if s["id"] == c["seg"])
            c["t_end"] = seg["t1"] - 0.3
        if c["kind"] == "CQ":
            seg = next(s for s in tl["segs"] if s["id"] == c["seg"])
            c["t0"] = c.get("t_zh", seg["t0"])
            nxt = [ts for ts, _ in seg["scenes"] if ts > c["t0"] + 0.01]
            c["t_end"] = min(nxt) if nxt else seg["t1"] - 0.3
    tl["total"] = t + 1.0
    return tl


def seg_at(tl, t):
    for s in tl["segs"]:
        if s["t0"] <= t < s["t1"]:
            return s
    return tl["segs"][-1]


def scene_at(seg, t):
    cur = seg["scenes"][0]
    for sc in seg["scenes"]:
        if sc[0] <= t:
            cur = sc
    return cur
