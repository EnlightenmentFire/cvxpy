# -*- coding: utf-8 -*-
"""lines.json -> tts_in.json (per-line speed);  --trim: vo_raw/*.wav -> vo/*.wav (trim silence, 48k not needed)"""
import json, os, sys
import numpy as np, soundfile as sf
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf8"))
SPEED = dict(p=1.12, q=0.98, slow=0.92, key=1.04)
def spd(l): return SPEED["slow" if l.get("slow") else "key" if l.get("key") else l["kind"]]
if "--trim" in sys.argv:
    os.makedirs(os.path.join(ROOT, "audio", "vo"), exist_ok=True)
    for l in lines:
        f = os.path.join(ROOT, "audio", "vo_raw2", l["id"] + ".wav")
        if not os.path.exists(f): continue
        x, sr = sf.read(f); e = np.abs(x); k = int(.02 * sr); env = np.convolve(e, np.ones(k) / k, "same"); idx = np.where(env > .012)[0]
        if len(idx) == 0: continue
        a, b = max(0, idx[0] - int(.05 * sr)), min(len(x), idx[-1] + int(.12 * sr)); y = x[a:b].copy()
        n = int(.02 * sr); y[:n] *= np.linspace(0, 1, n); y[-n:] *= np.linspace(1, 0, n)
        sf.write(os.path.join(ROOT, "audio", "vo", l["id"] + ".wav"), y, sr)
    print("trimmed")
else:
    out = [dict(id=l["id"], text=l["tts"], speed=spd(l)) for l in lines]
    sel = sys.argv[1:]
    if sel: out = [o for o in out if o["id"] in sel]
    json.dump(out, open(os.path.join(ROOT, "audio", "tts_in.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(len(out), "lines")
