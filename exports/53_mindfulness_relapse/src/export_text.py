# -*- coding: utf-8 -*-
"""Write sentences.json / sentences.txt (for re-voicing on the box), narration.srt (final timeline)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
tl = json.load(open("/tmp/claude-0/work/timeline.json"))
tmap = {l["id"]: l for l in tl["lines"]}
L = all_lines()
js = [dict(id=d["id"], scene=d["scene"], kind=("quote" if d["k"] == "q" else "narration"), tts_text=d["say"],
           subtitle=d["sub"], start=tmap[d["id"]]["start"], end=tmap[d["id"]]["end"]) for d in L]
json.dump(dict(voice="Tocqueville (Qwen3-TTS-12Hz-1.7B-Base ICL clone of voice_design_reference)",
               tempo={"narration": 1.16, "quote": 1.0}, gap_s=0.5, lines=js),
          open(f"{OUT}/sentences.json", "w"), ensure_ascii=False, indent=1)
with open(f"{OUT}/sentences.txt", "w") as f:
    for d in L:
        f.write(d["say"] + "\n")


def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


with open(f"{OUT}/narration.srt", "w") as f:
    for i, d in enumerate(js):
        f.write(f"{i + 1}\n{ts(d['start'])} --> {ts(d['end'])}\n{d['subtitle']}\n\n")
print("text exports ->", OUT)
