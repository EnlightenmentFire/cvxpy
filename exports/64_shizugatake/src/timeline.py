# -*- coding: utf-8 -*-
"""Build timeline.json: per line start/end, per scene start/dur, subtitle chunks; uses processed audio
durations when available (else estimates at 4.4 chars/s)."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import SCENES, all_lines

PROC = "/tmp/claude-0/work/tts/proc/durs.json"
OUT = "/tmp/claude-0/work/timeline.json"
GAP = 0.45          # between sentences
SCENE_GAP = 0.35    # extra between scenes
LEAD = 0.60         # first line starts here
CHAPTERS = {"b1": ("壹", "清洲之后"), "s1": ("贰", "山中对峙"), "t1": ("叁", "破绽与诱惑"),
            "r1": ("肆", "美浓大返还"), "e1": ("伍", "结局"), "c1": ("陆", "致人而不致于人")}
CHAPTER_PAD = 1.4   # extra lead-in at chapter starts
QUOTE_HOLD = 1.6    # extra hold after a quote line
EXTRA = {"h6": 1.2, "r7": 0.0, "c4": 2.5, "h0": 0.0}  # extra seconds at scene end

PUNCT = "，。？！：；、"
MAXC = 16


def nchars(s):
    return len(re.sub(r"[，。？！：；、“”《》\s·]", "", s))


def chunks(s):
    parts, cur = [], ""
    for ch in s:
        cur += ch
        if ch in PUNCT:
            parts.append(cur); cur = ""
    if cur:
        parts.append(cur)
    out, buf = [], ""
    for p in parts:
        if buf and buf[-1] in "。？！":
            out.append(buf); buf = ""
        if nchars(buf + p) <= MAXC:
            buf += p
        else:
            if buf:
                out.append(buf)
            buf = p
    if buf:
        out.append(buf)
    res = []
    for o in out:
        if nchars(o) > MAXC + 2:
            n = (nchars(o) + MAXC - 1) // MAXC
            L = len(o); k = (L + n - 1) // n
            res += [o[i:i + k] for i in range(0, L, k)]
        else:
            res.append(o)
    # strip trailing punctuation for display (keep ？！)
    return [r.rstrip("，。；：、") for r in res]


def build():
    durs = json.load(open(PROC))["durs"] if os.path.exists(PROC) else {}
    t = LEAD
    lines, scenes = [], []
    for s in SCENES:
        if s["id"] in CHAPTERS:
            t += CHAPTER_PAD
        s0 = t - (CHAPTER_PAD if s["id"] in CHAPTERS else 0) - (LEAD if not scenes else 0)
        Ls = []
        for d in [x for x in all_lines() if x["scene"] == s["id"]]:
            dur = durs.get(d["id"], nchars(d["say"]) / 4.4 + 0.3)
            cs = chunks(d["text"])
            tot = sum(max(1, nchars(c)) for c in cs)
            sub, u = [], t
            for cpart in cs:
                du = dur * max(1, nchars(cpart)) / tot
                sub.append(dict(s=round(u, 3), e=round(u + du, 3), text=cpart)); u += du
            L = dict(id=d["id"], scene=s["id"], start=round(t, 3), end=round(t + dur, 3), text=d["text"], q=d["q"], sub=sub)
            lines.append(L); Ls.append(L)
            t += dur + GAP + d["gap"] + (QUOTE_HOLD if d["q"] else 0)
        t += SCENE_GAP + EXTRA.get(s["id"], 0)
        scenes.append(dict(id=s["id"], vis=s["vis"], start=round(s0, 3), end=round(t, 3),
                           L=[round(x["start"] - s0, 3) for x in Ls], E=[round(x["end"] - s0, 3) for x in Ls],
                           chapter=CHAPTERS.get(s["id"])))
    for i in range(len(scenes) - 1):
        scenes[i]["end"] = scenes[i + 1]["start"]
    tl = dict(total=round(t + 0.5, 3), scenes=scenes, lines=lines, est=not bool(durs))
    json.dump(tl, open(OUT, "w"), ensure_ascii=False, indent=1)
    return tl


if __name__ == "__main__":
    tl = build()
    print(f"total {tl['total']:.1f}s ({tl['total']/60:.2f} min), est={tl['est']}")
    for s in tl["scenes"]:
        print(f"{s['id']:4s} {s['vis']:11s} {s['start']:7.1f} {s['end']-s['start']:5.1f}")
