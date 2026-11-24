"""~1 minute voice + picture sample: cold open (S0) + the Qin 'harsh law' beat (S2_19/20/22)."""
import copy
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from timeline import Timeline
import audio_synth
import render

BUILD = "/home/user/wude_build"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{BUILD}/sample"
os.makedirs(OUT, exist_ok=True)

segs = json.load(open(f"{BUILD}/script.json", encoding="utf-8"))
by_id = {l["id"]: l for s in segs for l in s["lines"]}
s0 = copy.deepcopy(segs[0])
s2 = copy.deepcopy(segs[2])
s2["lines"] = [copy.deepcopy(by_id[i]) for i in ("S2_19", "S2_20", "S2_22")]
s2["lines"][0]["cues"] = [
    {"cmd": "stage", "_args": ["qin_law"]},
    {"cmd": "wheel", "go": "水", "label": "秦"},
    {"cmd": "pause", "s": "3.2"},
    {"cmd": "sfx", "_args": ["drum_stop"]},
    {"cmd": "pause", "s": "0.6"},
]
segs_sample = [s0, s2]
durs = json.load(open(f"{BUILD}/voice_post/durations.json"))
tl = Timeline(segs_sample, durs)
print(f"sample length {tl.total:.1f}s")
wav = audio_synth.mix(tl, f"{BUILD}/voice_post", f"{OUT}/sample_mix.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "aac", "-b:a", "192k",
                f"{OUT}/样音_五德终始.m4a"], check=True)
if "--video" in sys.argv:
    render.export_video(tl, f"{OUT}/样片_五德终始_1分钟.mp4", 0.0, tl.total, audio=wav, crf=21)
print("done")
