"""Builds the global timeline (line times, cards, sound events) and subtitle units."""
import json
import os
import re

from script_data import LINES, SECTIONS, spoken_chars

CARD_DUR = 2.0        # chapter card
TITLE_DUR = 3.0       # title card after cold open
COLD_LEAD = 2.2       # machines running before the first word
STOP_GAP = 0.85       # clack + half-second silence before "一台机器，停了"
TAIL = 2.0            # hold after last line
TEASER_DUR = 4.0
SOURCES_DUR = 5.0
EST_RATE = {"Chinese": 4.6, "English": 2.6, "French": 2.6}  # chars/s (en/fr: words/s)


def est_duration(line):
    if line["tts"] is None:
        return 0.0
    if line["lang"] == "Chinese":
        return spoken_chars(line["tts"]) / EST_RATE["Chinese"] + 0.25
    words = len(line["tts"].split())
    return words / EST_RATE["English"] + 0.4


def load_durations(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def build(durations=None):
    """Returns dict with: lines{id: (start, end)}, sections{sec: (start, end)}, cards[], events[], total."""
    durations = durations or {}
    t = 0.0
    lines = {}
    sections = {}
    cards = []
    events = []
    for sec, label in SECTIONS:
        s0 = t
        if label is not None:
            cards.append(dict(sec=sec, num=label[0], title=label[1], start=t, end=t + CARD_DUR))
            events.append((t, "card", sec))
            t += CARD_DUR
        if sec == "cold":
            events.append((0.0, "beat_on", None))
            t += COLD_LEAD
        if sec == "intro":
            cards.append(dict(sec="title", num=None, title=None, start=t, end=t + TITLE_DUR))
            events.append((t, "title", None))
            t += TITLE_DUR
        for ln in [d for d in LINES if d["sec"] == sec]:
            if ln["id"] == "c03":
                events.append((t, "stop", "c03"))
                t += STOP_GAP
            d = durations.get(ln["id"], est_duration(ln))
            lines[ln["id"]] = (t, t + d)
            t += d
            if d > 0:
                t += ln["gap"]
            if ln["id"] == "s2_01":
                events.append((t - ln["gap"] + 0.1, "stop", "s2_01"))
                t += 0.6
        sections[sec] = (s0, t)
    end_main = t
    t += TAIL
    teaser = (t, t + TEASER_DUR)
    t += TEASER_DUR
    sources = (t, t + SOURCES_DUR)
    t += SOURCES_DUR
    sections["end"] = (sections["end"][0], t)
    return dict(lines=lines, sections=sections, cards=cards, events=sorted(events, key=lambda e: e[0]),
                teaser=teaser, sources=sources, total=t, end_main=end_main)


# ------------------------------------------------------------------ subtitles
PUNCT_SPLIT = re.compile(r"([，。；：？！、,.;:?!])")
MAXLINE = 16


def _units_for(text):
    """Split a Chinese line into display units (each ≤ 2 lines × MAXLINE chars)."""
    parts = PUNCT_SPLIT.split(text)
    phrases = []
    for i in range(0, len(parts), 2):
        body = parts[i]
        p = parts[i + 1] if i + 1 < len(parts) else ""
        if body.strip() or p:
            phrases.append((body.strip(), p))
    # glue very short phrases (“不过”、“一”、“那么”) to the following phrase
    glued = []
    carry = ""
    for body, p in phrases:
        if carry:
            body = carry + " " + body
            carry = ""
        if len(body) <= 2 and p not in "。？！" and body:
            carry = body
            continue
        glued.append((body, p))
    if carry:
        glued.append((carry, ""))
    phrases = glued
    units = []
    cur = []
    cur_len = 0
    for body, p in phrases:
        n = len(body)
        if cur and (cur_len + n > MAXLINE * 2 - 2 or (cur_len >= MAXLINE and n > 4)):
            units.append(cur)
            cur, cur_len = [], 0
        cur.append((body, p))
        cur_len += n + 1
        if p in "。？！":
            units.append(cur)
            cur, cur_len = [], 0
    if cur:
        units.append(cur)
    out = []
    for u in units:
        # display text: interior commas -> space, keep ？！ and quotes
        segs = []
        for body, p in u:
            if not body:
                continue
            keep = p if p in "？！?!" else ""
            segs.append(body + keep)
        disp = "　".join(segs)
        weight = sum(len(b) for b, _ in u) + 0.8 * sum(1 for _, p in u if p)
        out.append((disp, weight))
    return [o for o in out if o[0]]


def _wrap(disp):
    """Break a unit into ≤2 lines, preferring the full-width space."""
    if len(disp) <= MAXLINE:
        return [disp]
    # candidate split points: ideographic spaces
    best = None
    for i, ch in enumerate(disp):
        if ch == "　" and i >= 4 and len(disp) - i - 1 >= 4:
            score = abs(i - len(disp) / 2)
            if i <= MAXLINE + 1 and len(disp) - i - 1 <= MAXLINE + 1 and (best is None or score < best[0]):
                best = (score, i)
    if best:
        i = best[1]
        return [disp[:i], disp[i + 1:]]
    mid = (len(disp) + 1) // 2
    # prefer breaking right after a function word near the middle
    for d in range(0, 5):
        for j in (mid + d, mid - d):
            if 3 < j < len(disp) - 3 and disp[j - 1] in "的了是和把就也都在着过" and disp[j] not in "”」？！》，":
                if len(disp) - j <= MAXLINE + 1 and j <= MAXLINE + 1:
                    return [disp[:j], disp[j:]]
    # avoid splitting inside “quotes” / before closing punctuation
    for d in range(0, 4):
        for j in (mid + d, mid - d):
            if 0 < j < len(disp) and disp[j] not in "”」？！》" and disp[j - 1] not in "“「《":
                return [disp[:j], disp[j:]]
    return [disp[:mid], disp[mid:]]


def subtitles(tl):
    """List of dict(start, end, lines[], kind, lang)."""
    subs = []
    for ln in LINES:
        if ln["id"] not in tl["lines"]:
            continue
        s, e = tl["lines"][ln["id"]]
        if e - s <= 0.01:
            continue
        if ln["lang"] != "Chinese" and not ln.get("sub"):
            subs.append(dict(start=s, end=e + min(ln["gap"], 0.3), lines=[ln["text"]], lang=ln["lang"], id=ln["id"]))
            continue
        units = _units_for(ln.get("sub") or ln["text"])
        tot = sum(w for _, w in units) or 1
        t = s
        for k, (disp, w) in enumerate(units):
            d = (e - s) * w / tot
            end = t + d if k < len(units) - 1 else e + min(ln["gap"], 0.3)
            subs.append(dict(start=t, end=end, lines=_wrap(disp), lang="Chinese", id=ln["id"]))
            t += d
    return subs


if __name__ == "__main__":
    tl = build()
    print("total %.1f s (%.1f min)" % (tl["total"], tl["total"] / 60))
    for sec, (a, b) in tl["sections"].items():
        print(f"{sec:6s} {a:7.1f} {b:7.1f}")
    subs = subtitles(tl)
    for s in subs[:40]:
        print(f"{s['start']:6.1f} {s['end']:6.1f} {' / '.join(s['lines'])}")
    print(max(len(l) for s in subs if s['lang'] == 'Chinese' for l in s['lines']))
