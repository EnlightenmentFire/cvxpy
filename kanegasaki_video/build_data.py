"""Build timeline (per line t0/t1 + subtitle chunks) from processed voice wavs, write render/data.js.
Durations: processed wav if present, else raw wav * TEMPO, else char estimate.
"""
import os, re, json, sys
import soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import S

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = "/tmp/claude-0/work/tts/proc"
RAW = "/tmp/claude-0/work/tts/raw"
TEMPO = float(os.environ.get("TEMPO", "1.0"))
START = 1.5          # voice enters after horn, hooves, volley and first taiko hit
SCENE_GAP = 1.1       # breathing room between chapters
TITLE_HOLD = 1.4      # chapter card before first line of s1..s6
QUOTE_EXTRA = 0.7     # extra hold after a quoted line
TAIL = 4.0
CH = r"[，。？！：；、“”《》「」\s]"

def dur(d):
    for p, k in ((f"{PROC}/{d['id']}.wav", 1.0), (f"{RAW}/{d['id']}.wav", 1.0 / TEMPO)):
        if os.path.exists(p):
            i = sf.info(p); return i.frames / i.samplerate * k, True
    return len(re.sub(CH, "", d["say"])) / 3.9, False

def chunks(sub, t0, t1, maxc=30):
    # split subtitle into display chunks (<= 2 lines of ~16 chars), timed by char share
    parts = re.findall(r"[^，。？！：；]*[，。？！：；]?", sub)
    parts = [p for p in parts if p.strip()]
    out, cur = [], ""
    for p in parts:
        if len(re.sub(CH, "", cur + p)) > maxc and cur:
            out.append(cur); cur = p
        else:
            cur += p
    if cur: out.append(cur)
    n = [max(1, len(re.sub(CH, "", c))) for c in out]; tot = sum(n)
    res, t = [], t0
    for c, k in zip(out, n):
        dt = (t1 - t0) * k / tot
        res.append(dict(t0=round(t, 3), t1=round(t + dt, 3), text=c.rstrip("，、；：")))
        t += dt
    return res

def build():
    t = START; lines = {}; scenes = []; real = 0
    for si, s in enumerate(S):
        st = t if si == 0 else t
        if si > 0:
            t += TITLE_HOLD
        for d in s["lines"]:
            dd, ok = dur(d); real += ok
            t0, t1 = t, t + dd
            lines[d["id"]] = dict(t0=round(t0, 3), t1=round(t1, 3), sub=chunks(d["sub"], t0, t1))
            t = t1 + d.get("gap", 0.5) + (QUOTE_EXTRA if d.get("q") else 0)
        scenes.append(dict(id=s["id"], title=s["title"], t0=round(st, 3), t1=round(t, 3)))
        t += SCENE_GAP if si < len(S) - 1 else 0
    total = t + TAIL
    scenes[-1]["t1"] = round(total, 3)
    for a, b in zip(scenes, scenes[1:]):
        a["t1"] = b["t0"]
    tl = dict(total=round(total, 3), scenes=scenes, lines=lines)
    maps = json.load(open(f"{HERE}/assets/maps/maps.json"))
    os.makedirs(f"{HERE}/render", exist_ok=True)
    with open(f"{HERE}/render/data.js", "w") as f:
        f.write("window.DATA=" + json.dumps(dict(script=S, tl=tl, maps=maps), ensure_ascii=False) + ";\n")
    json.dump(tl, open("/tmp/claude-0/work/timeline.json", "w"), ensure_ascii=False, indent=1)
    # subtitles + sentence sheets
    def ts(x):
        h, r = divmod(x, 3600); m, r = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int(round((r - int(r)) * 1000)) % 1000:03d}"
    srt, k = [], 1
    for s_ in S:
        for d in s_["lines"]:
            for c in lines[d["id"]]["sub"]:
                srt.append(f"{k}\n{ts(c['t0'])} --> {ts(c['t1'])}\n{c['text']}\n"); k += 1
    open("/tmp/claude-0/work/narration.srt", "w").write("\n".join(srt))
    sent = [dict(id=d["id"], scene=s_["id"], say=d["say"], sub=d["sub"], t0=lines[d["id"]]["t0"], t1=lines[d["id"]]["t1"]) for s_ in S for d in s_["lines"]]
    json.dump(sent, open("/tmp/claude-0/work/sentences.json", "w"), ensure_ascii=False, indent=1)
    open("/tmp/claude-0/work/sentences.txt", "w").write("\n".join(x["say"] for x in sent) + "\n")
    print(f"total {total:.1f}s = {total/60:.2f} min; real durations {real}/{len(lines)}")
    for s in scenes: print(s["id"], s["t0"], s["t1"])

if __name__ == "__main__":
    build()
