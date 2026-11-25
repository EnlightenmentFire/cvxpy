# -*- coding: utf-8 -*-
"""Write narration.srt (subtitle chunks as shown on screen) and sentences.json / sentences.txt from timeline.json.
usage: python export.py <out_dir>"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import split_sub, sub_display

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(out):
    tl = json.load(open(f"{WORK}/timeline.json"))
    os.makedirs(out, exist_ok=True)
    srt, sents, k = [], [], 1
    for s in tl["scenes"]:
        for L in s["lines"]:
            sents.append(dict(id=L["id"], scene=s["id"], text=L["say"], subtitle=L.get("sub", L["say"]),
                              start=L["start"], end=L["end"]))
            ch = split_sub(L.get("sub", L["say"]))
            n = sum(len(c) for c in ch)
            t = L["start"]
            for c in ch:
                d = (L["end"] - L["start"]) * len(c) / n
                srt.append(f"{k}\n{ts(t)} --> {ts(t + d)}\n{sub_display(c)}\n")
                k += 1; t += d
    open(f"{out}/narration.srt", "w").write("\n".join(srt))
    json.dump(dict(voice="Qwen3-TTS-12Hz-1.7B-Base ICL, 托克维尔设计音色参考 A0b (18 s)", tempo=1.15, total=tl["total"],
                   sentences=sents), open(f"{out}/sentences.json", "w"), ensure_ascii=False, indent=1)
    open(f"{out}/sentences.txt", "w").write("\n".join(x["text"] for x in sents) + "\n")
    print(len(sents), "sentences,", k - 1, "subtitle chunks")


if __name__ == "__main__":
    main(sys.argv[1])
