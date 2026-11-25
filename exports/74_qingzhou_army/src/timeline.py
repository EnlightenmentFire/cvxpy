# -*- coding: utf-8 -*-
"""时间线：每句起止（秒）。有处理后的配音就用真实时长，否则按 4.3 字/秒估算。"""
import os, re, json
import soundfile as sf
from script import all_lines

PROC = "/tmp/claude-0/w74/tts/proc"
LEAD = 0.45          # 开场声音钩子先响
GAP = 0.50           # 句间停顿
SCENE_GAP = 0.55     # 换段额外停顿


def nchar(s):
    return len(re.sub(r"[，。？！：；、“”《》「」\s·…]", "", s))


def build():
    out = []
    t = LEAD
    prev_scene = None
    for d in all_lines():
        if prev_scene and d["scene"] != prev_scene:
            t += SCENE_GAP
        p = f"{PROC}/{d['id']}.wav"
        if os.path.exists(p):
            dur = sf.info(p).duration
        else:
            dur = nchar(d["say"]) / 4.3
        d = dict(d, start=t, dur=dur, end=t + dur)
        out.append(d)
        t += dur + (d["pause"] if d["pause"] else GAP)
        prev_scene = d["scene"]
    total = t + 1.0
    return out, total


if __name__ == "__main__":
    L, T = build()
    print(len(L), "lines, total %.1fs = %d:%02d" % (T, T // 60, T % 60))
    cur = None
    for d in L:
        if d["scene"] != cur:
            cur = d["scene"]; print("%6.1f  %s" % (d["start"], cur))
