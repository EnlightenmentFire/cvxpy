# -*- coding: utf-8 -*-
"""由逐句 wav 时长生成 build/timeline.json / timeline.js，并拼出旁白干声 build/narration.wav"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, soundfile as sf
from script_data import segments, SCENES
VOICE = sys.argv[1] if len(sys.argv) > 1 else "zm_029"
ROOT = os.path.join(os.path.dirname(__file__), ".."); SR = 24000
LEAD = 1.2          # 片头留白
MAXLEN = 17         # 单行字幕最多字数

def chunks(text):
    """按标点切字幕行；尽量合并到 MAXLEN 以内。返回 [(显示文本, 权重)]"""
    parts = re.findall(r"[^，。；：？！、—…]+[，。；：？！、—…]*", text)
    out = []; cur = ""
    for p in parts:
        body = lambda s: re.sub(r"[，。；：？！、—…「」《》]", "", s)
        if cur and len(body(cur + p)) > MAXLEN:
            out.append(cur); cur = p
        else:
            cur += p
    if cur: out.append(cur)
    res = []
    for c in out:
        w = len(re.findall(r"[一-鿿]", c)) + 1.2*len(re.findall(r"[，；：、]", c)) + 2.0*len(re.findall(r"[。？！—…]", c))
        disp = re.sub(r"[，。；：、]+$", "", c).replace("——", "")
        disp = re.sub(r"[，；]", " ", disp) if False else disp
        res.append((disp, max(w, 1)))
    return res

segs = segments(); t = LEAD; tl = []; audio = []
for s in segs:
    wp = os.path.join(ROOT, "build", "tts", VOICE, s["id"] + ".wav")
    if os.path.exists(wp):
        w, sr = sf.read(wp, dtype="float32"); assert sr == SR
    else:                                   # 尚未合成：按字数估时长（仅供排版预览）
        n = len(re.findall(r"[\u4e00-\u9fff]", s["text"])); w = np.zeros(int(SR * (n / (4.1 if s["kind"] == "q" else 5.0) + 0.3)), dtype=np.float32)
    d = len(w) / SR
    cs = chunks(s["text"]); tot = sum(c[1] for c in cs); subs = []; a = t
    for disp, wt in cs:
        b = a + d * wt / tot; subs.append(dict(text=disp, s=round(a, 3), e=round(b, 3))); a = b
    tl.append(dict(id=s["id"], scene=s["scene"], kind=s["kind"], text=s["text"], s=round(t, 3), e=round(t + d, 3), subs=subs))
    audio.append((t, w)); t += d + s["gap"]
total = round(t + 0.5, 2)
scenes = []
for sid, title, lines in SCENES:
    ss = [x for x in tl if x["scene"] == sid]
    scenes.append(dict(id=sid, title=title, s=ss[0]["s"], e=ss[-1]["e"]))
for i, sc in enumerate(scenes):            # 场景边界取相邻两段中点
    sc["cut_out"] = round((sc["e"] + scenes[i+1]["s"]) / 2, 3) if i + 1 < len(scenes) else total
    sc["cut_in"] = scenes[i-1]["cut_out"] if i else 0.0
TL = dict(total=total, fps=30, voice=VOICE, segs=tl, scenes=scenes)
os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
json.dump(TL, open(os.path.join(ROOT, "build", "timeline.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, "build", "timeline.js"), "w").write("window.TL=" + json.dumps(TL, ensure_ascii=False) + ";")
buf = np.zeros(int(total * SR) + SR, dtype=np.float32)
for st, w in audio:
    i = int(st * SR); buf[i:i+len(w)] += w
sf.write(os.path.join(ROOT, "build", "narration.wav"), buf, SR)
print("total %.1fs = %d:%04.1f" % (total, total // 60, total % 60))
for sc in scenes: print("  %-7s %-10s %6.1f → %6.1f (%.1fs)" % (sc["id"], sc["title"], sc["cut_in"], sc["cut_out"], sc["cut_out"] - sc["cut_in"]))
