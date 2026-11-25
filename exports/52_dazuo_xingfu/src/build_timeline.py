"""timeline.json from processed line wavs (tts/proc/Lxxx.wav) or estimates."""
import json, os, sys, re
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
D = os.path.dirname(os.path.abspath(__file__))
LEAD = 0.35  # voice starts 0.35 s after first frame (bell strike at 0)
t = LEAD; out = []
for d in all_lines():
    p = f"{D}/tts/proc/{d['id']}.wav"
    if os.path.exists(p):
        dur = sf.info(p).duration; est = False
    else:
        dur = len(re.sub(r"[^一-鿿]", "", d["say"])) * 60 / 285 + 0.3; est = True
    out.append(dict(id=d["id"], scene=d["scene"], sub=d["sub"], say=d["say"], kind=d["kind"], start=round(t, 3), dur=round(dur, 3), est=est))
    t += dur + d["pause"]
total = round(t + 1.5, 3)
json.dump(dict(lines=out, total=total), open(f"{D}/timeline.json", "w"), ensure_ascii=False, indent=1)
print("total", total, "s =", total / 60, "min; estimated lines:", sum(l["est"] for l in out))
