# -*- coding: utf-8 -*-
"""lines.json (+ wav durations if present) -> timeline.json / timeline.js / subtitles.srt"""
import json, os, re, sys, wave
sys.path.insert(0, os.path.dirname(__file__))
from script import L, SEGS, tts_text

ROOT = os.path.join(os.path.dirname(__file__), "..")
WAVDIR = os.path.join(ROOT, "audio", "vo")
LEAD = 4.4          # 开场：夜、鸡鸣，再开口
TITLE_HOLD = 0.0    # 标题卡含在 s01 末句 gap 里
cnt = lambda s: len(re.sub(r"[^一-鿿]", "", s))

def dur(l):
    f = os.path.join(WAVDIR, l["id"] + ".wav")
    if os.path.exists(f):
        with wave.open(f) as w:
            return w.getnframes() / w.getframerate(), True
    return cnt(l["text"]) / (3.6 if l.get("slow") else 4.4) + 0.25, False

t = LEAD; lines = []; real = 0
for l in L:
    d, ok = dur(l); real += ok
    lines.append(dict(id=l["id"], seg=l["seg"], kind=l["kind"], text=l.get("disp") or l["text"], src=l.get("src", ""),
                      show=l.get("show", ""), show_src=l.get("show_src", ""), slow=bool(l.get("slow")),
                      s=round(t, 3), e=round(t + d, 3), gap=l["gap"]))
    l["gap"] = round(l["gap"] * (0.66 if l["gap"] < 3 else 0.85), 3); lines[-1]["gap"] = l["gap"]
    t += d + l["gap"]
total = t + 1.0
segs = []
for sid, name in SEGS:
    ls = [x for x in lines if x["seg"] == sid]
    segs.append(dict(id=sid, name=name, s=ls[0]["s"], e=ls[-1]["e"] + ls[-1]["gap"]))
segs[0]["s"] = 0.0
for a, b in zip(segs, segs[1:]):
    b["s"] = round(b["s"] - 0.45, 3); a["e"] = b["s"]
segs[-1]["e"] = total
tl = dict(total=round(total, 3), fps=30, lines=lines, segs=segs)
json.dump(tl, open(os.path.join(ROOT, "audio", "timeline.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, "src", "timeline.js"), "w", encoding="utf8").write("window.TL=" + json.dumps(tl, ensure_ascii=False) + ";")

# ── SRT（按标点切小句，按字数比例分配时间）──
def chunks(text, maxlen=15):
    parts = re.findall(r"[^，。；：？！、]+[，。；：？！、”]*", text)
    out, cur = [], ""
    for p_ in parts:
        if cur and (cnt(cur) + cnt(p_) > maxlen or cur.rstrip("”")[-1] in "。？！；"):
            out.append(cur); cur = p_
        else:
            cur += p_
    if cur: out.append(cur)
    return out
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return "%02d:%02d:%06.3f" % (h, m, s)
srt = []; k = 1
for l in lines:
    cs = chunks(l["text"], 13 if l["kind"] == "p" else 99)
    w = [cnt(c) + 1.2 * len(re.findall(r"[，。；：？！]", c)) for c in cs]; W_ = sum(w); a = l["s"]
    l["chunks"] = []
    for c, wi in zip(cs, w):
        b = a + (l["e"] - l["s"]) * wi / W_
        txt = c.strip("，。；：、 ") if l["kind"] == "p" else c
        if l["kind"] == "q": txt = "「" + txt + "」"
        l["chunks"].append(dict(t=txt, s=round(a, 3), e=round(b, 3)))
        srt.append("%d\n%s --> %s\n%s\n" % (k, ts(a).replace(".", ","), ts(b).replace(".", ","), txt)); k += 1
        a = b
open(os.path.join(ROOT, "out", "liukun.srt"), "w", encoding="utf8").write("\n".join(srt))
json.dump(tl, open(os.path.join(ROOT, "audio", "timeline.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, "src", "timeline.js"), "w", encoding="utf8").write("window.TL=" + json.dumps(tl, ensure_ascii=False) + ";")
print("total %.1fs (%d:%02d)  real wavs %d/%d" % (total, total // 60, total % 60, real, len(L)))
for s in segs: print(s["id"], s["name"], "%.1f-%.1f (%.1fs)" % (s["s"], s["e"], s["e"] - s["s"]))
