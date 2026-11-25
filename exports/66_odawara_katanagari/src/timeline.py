"""Build the timeline from processed narration durations (or estimates)."""
import json, os, re, sys
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import S, all_lines, SUBS
WORK = "/tmp/claude-0/work"
PROC = f"{WORK}/tts/proc"
SCENE_GAP = 1.2
LEAD = 1.8
TAIL = 3.5

def dur(l):
    p = f"{PROC}/{l['id']}.wav"
    if os.path.exists(p):
        i = sf.info(p); return i.frames / i.samplerate, True
    n = len(re.sub(r"[，。？！：；、“”《》\s]", "", l["say"]))
    return n * 0.235, False

DIG = dict(zip("零一二三四五六七八九", "0123456789"))
def yeardig(s):
    import re as _re
    s = _re.sub(r"([零一二三四五六七八九]{4})(年)", lambda m: "".join(DIG[ch] for ch in m.group(1)) + m.group(2), s)
    return s.replace("一九一九", "1919")

def chunks(sub, d):
    """split a subtitle line into display chunks (<=2 rows of 16), timed by char count"""
    parts = re.split(r"(?<=[，。？！；：])", sub)
    parts = [p for p in parts if p.strip()]
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) <= 30: cur += p
        else:
            if cur: out.append(cur)
            cur = p
    if cur: out.append(cur)
    tot = sum(len(o) for o in out); t = 0; res = []
    for o in out:
        dd = d * len(o) / tot; res.append((t, t + dd, o.rstrip("，。；：、"))); t += dd
    return res

def build():
    t = LEAD; lines = []; real = 0
    for si, s in enumerate(S):
        if si > 0: t += SCENE_GAP if si > 1 else 0.3
        for l in s["lines"]:
            d, ok = dur(l); real += ok
            sub = l["sub"]
            if sub is None:
                sub = l["say"]
                for a, b in SUBS.items(): sub = sub.replace(a, b)
            if l["k"] == "n": sub = yeardig(sub)
            lines.append(dict(id=l["id"], scene=s["id"], k=l["k"], v=l["v"], t0=round(t, 3), t1=round(t + d, 3), sub=sub,
                              chunks=[(round(t + a, 3), round(t + b, 3), c) for a, b, c in chunks(l["say"] if l["k"] == "q" else sub, d)]))
            t += d + l["gap"]
    total = lines[-1]["t1"] + TAIL
    beats = []
    for l in lines:
        if beats and beats[-1]["v"] == l["v"] and beats[-1]["scene"] == l["scene"]:
            beats[-1]["lines"].append(l["id"])
        else:
            beats.append(dict(v=l["v"], scene=l["scene"], start=l["t0"], lines=[l["id"]]))
    beats[0]["start"] = 0.0
    for i, b in enumerate(beats):
        b["end"] = beats[i + 1]["start"] if i + 1 < len(beats) else total
    # beats start a little before their first line when following a scene gap
    titles = {s["id"]: s["title"] for s in S}
    tl = dict(total=round(total, 3), lines=lines, beats=beats, titles=titles,
              scenes=[dict(id=s["id"], start=min(l["t0"] for l in lines if l["scene"] == s["id"]),
                           end=max(l["t1"] for l in lines if l["scene"] == s["id"])) for s in S])
    json.dump(tl, open(f"{WORK}/timeline.json", "w"), ensure_ascii=False, indent=1)
    print(f"total {total:.1f}s ({total/60:.2f} min), {len(lines)} lines ({real} real durations), {len(beats)} beats")
    return tl

if __name__ == "__main__":
    build()
