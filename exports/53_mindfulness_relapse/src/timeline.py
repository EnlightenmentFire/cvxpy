# -*- coding: utf-8 -*-
"""Build the timeline from processed line durations (estimates for missing lines).
Writes /tmp/claude-0/work/timeline.json."""
import os, sys, json, re
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines, SCENES

PROC = "/tmp/claude-0/work/tts/proc"
GAP = 0.50            # between sentences (VOICE_SPEC)
SCENE_PAD = 0.45      # extra breath at a scene change
LEAD = 0.30           # voice starts right after the opening bell strike
TAIL = 4.0            # final card hold
EXTRA = {"s04_arrow_tease": 0.4, "s05_disclaimer": 0.3, "s17_arrow_05": 0.6, "s19_verse_02": 0.5, "s19_verse_06": 0.8,
         "s12_kuyken": 0.3, "s16b_ledger": 0.3, "s20_yinzhao": 0.6, "s21_end_03": 0.7}


def build():
    lines = all_lines()
    t = LEAD
    out, scenes = [], []
    cur = None
    for d in lines:
        if d["scene"] != cur:
            if cur is not None:
                scenes[-1]["end"] = t - GAP + SCENE_PAD / 2 + EXTRA.get(cur, 0) / 2
                t += SCENE_PAD + EXTRA.get(cur, 0)
            cur = d["scene"]
            scenes.append(dict(id=cur, start=(0.0 if not scenes else None)))
        p = f"{PROC}/{d['id']}.wav"
        if os.path.exists(p):
            dur = sf.info(p).duration; est = False
        else:
            dur = len(re.sub(r"[^一-鿿]", "", d["say"])) / (4.9 if d["k"] == "n" else 3.6); est = True
        out.append(dict(id=d["id"], scene=d["scene"], k=d["k"], start=round(t, 3), end=round(t + dur, 3), sub=d["sub"], est=est))
        t += dur + GAP + EXTRA.get(d["id"], 0)
    total = t - GAP + TAIL
    scenes[-1]["end"] = total
    for i in range(1, len(scenes)):
        scenes[i]["start"] = scenes[i - 1]["end"]
    tl = dict(lines=out, scenes=scenes, total=round(total, 3))
    json.dump(tl, open("/tmp/claude-0/work/timeline.json", "w"), ensure_ascii=False, indent=1)
    n = sum(len(re.sub(r"[^一-鿿]", "", d["say"])) for d in lines)
    print(f"total {total:.1f}s = {total/60:.2f} min; {n} hanzi -> {n/(total/60):.0f} /min; estimated lines: {sum(o['est'] for o in out)}")
    return tl


if __name__ == "__main__":
    build()
