"""按逐句旁白时长排时间线：句间 0.50 s；换幕 +0.8 s；引文句前后各 +0.5 s；片头 0.6 s 声音钩子先行。
字幕：每句按标点切成 ≤16 字的块，按字数比例分配时长。输出 WORK/timeline.json 和 narration.srt。
"""
import os, sys, json, re
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, SCENES

W = "/tmp/claude-0/work"
GAP, SCENE_GAP, QUOTE_PAD, LEAD, TAIL = 0.50, 0.8, 0.5, 0.6, 4.0
QUOTES = {"B05c", "E15", "F05", "G06"}
EXTRA = {"A02": 0.3, "A06": 0.4, "D10": 0.6, "D11": 0.5, "C13": 0.2, "G04": 0.6, "G08": 0.4, "A13": 0.3, "D01": 0.4}
NOSPACE = re.compile(r"[，。？！：；、“”《》〈〉·\s]")


def dur_of(d):
    p = f"{W}/tts/proc/{d['id']}.wav"
    if os.path.exists(p):
        return sf.info(p).duration, True
    return len(NOSPACE.sub("", d["say"])) / 4.6, False


def chunks(s, maxc=16):
    parts = re.findall(r"[^，。？！：；]+[，。？！：；]?", s)
    out = []
    for p in parts:
        core = p.rstrip("，。？！：；")
        while len(core) > maxc:
            k = len(core) // 2 if len(core) <= 2 * maxc else maxc
            out.append(core[:k]); core = core[k:]
        out.append(core + (p[len(p.rstrip("，。？！：；")):] if p.endswith(("？", "！")) else ""))
    # 合并过短的块
    merged = []
    for c in out:
        if merged and len(merged[-1]) + len(c) <= 11 and len(c) <= 5:
            merged[-1] = merged[-1] + "，" + c
        else:
            merged.append(c)
    return [m for m in merged if m]


def build():
    L = all_lines()
    t = LEAD
    lines, missing, prev_scene = [], 0, None
    for d in L:
        if prev_scene and d["scene"] != prev_scene:
            t += SCENE_GAP
        if d["id"] in QUOTES:
            t += QUOTE_PAD
        du, ok = dur_of(d)
        missing += (not ok)
        lines.append(dict(id=d["id"], scene=d["scene"], start=round(t, 3), end=round(t + du, 3), say=d["say"], sub=d["sub"]))
        t += du + GAP + EXTRA.get(d["id"], 0) + (QUOTE_PAD if d["id"] in QUOTES else 0)
        prev_scene = d["scene"]
    total = t + TAIL
    subs = []
    for ln in lines:
        cs = chunks(ln["sub"])
        n = sum(len(NOSPACE.sub("", c)) or 1 for c in cs)
        a = ln["start"]
        for c in cs:
            k = (len(NOSPACE.sub("", c)) or 1) / n
            b = a + (ln["end"] - ln["start"]) * k
            subs.append(dict(id=ln["id"], text=c, start=round(a, 3), end=round(b, 3)))
            a = b
    tl = dict(total=round(total, 3), lines=lines, subs=subs, missing=missing)
    json.dump(tl, open(f"{W}/timeline.json", "w"), ensure_ascii=False, indent=1)

    def ts(x):
        h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
    with open(f"{W}/narration.srt", "w") as f:
        for i, s in enumerate(subs, 1):
            f.write(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n")
    return tl


if __name__ == "__main__":
    tl = build()
    nch = sum(len(NOSPACE.sub("", l["say"])) for l in tl["lines"])
    print(f"total {tl['total']:.1f}s ({tl['total']/60:.2f} min), missing {tl['missing']}, {nch/(tl['total']/60):.0f} chars/min")
