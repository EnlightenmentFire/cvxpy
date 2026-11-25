# -*- coding: utf-8 -*-
"""单独重做一句里的第一个片段（引文），拼回原句并平移逐字时间。
python fix_segment.py NARR_DIR LINE_ID "TTS写法1|TTS写法2" seeds"""
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qtts  # noqa: E402
import qnarr  # noqa: E402

GOOD_CHEN = set("嗔瞋臣陈晨沉尘辰琛抻宸谌")


def main(narr, lid, variants, seeds):
    rep = json.load(open(os.path.join(narr, "report.json")))
    meta = {m["id"]: m for m in json.load(open(os.path.join(narr, "meta.json")))}
    seg0 = rep[lid][0]
    display = seg0["text"]
    tempo = seg0["tempo"]
    old_dur = seg0["dur"]
    best = None
    for v in variants:
        for s in seeds:
            w = qtts.trim_and_cap(qtts.gen(v, s), cap=0.4)
            f0 = qtts.median_f0(w)
            c = qnarr.check(display, w)
            hit = sum(ch in GOOD_CHEN for ch in (c["whisper"] + c["paraformer"])[:12])
            score = (qtts.F0_LO <= f0 <= qtts.F0_HI, hit, c["sim"])
            print(f"  [{v}] seed {s}: f0={f0:.1f} sim={c['sim']:.3f} chen_hits={hit} W:{c['whisper']} P:{c['paraformer']}", flush=True)
            if best is None or score > best[0]:
                best = (score, w, c, v, s, f0)
    _, w, c, v, s, f0 = best
    w2 = qtts.trim_and_cap(qtts.stretch(w, tempo), cap=0.4)
    line, sr = sf.read(os.path.join(narr, lid + ".wav"), dtype="float32")
    cut = int(old_dur * sr)
    new_line = np.concatenate([w2, line[cut:]]).astype(np.float32)
    sf.write(os.path.join(narr, lid + ".wav"), new_line, sr)
    shift = len(w2) / sr - old_dur
    m = meta[lid]
    nq = len(re.findall(r"[一-鿿0-9]", display))
    words = m["words"]
    newq = qnarr.char_times(display, [(x, a / tempo, b / tempo) for x, a, b in c["words"]], len(w2) / sr, 0.0)
    m["words"] = [[ch, a, b, True] for ch, a, b in newq] + [[x, a + shift, b + shift, q] for x, a, b, q in words[nq:]]
    m["dur"] = len(new_line) / sr
    m["f0"] = round(qtts.median_f0(new_line), 1)
    json.dump(list(meta.values()), open(os.path.join(narr, "meta.json"), "w"), ensure_ascii=False, indent=1)
    seg0.update(seed=s, f0=round(f0, 1), whisper=c["whisper"], paraformer=c["paraformer"], sim=c["sim"],
                sim_w=c["sim_w"], sim_p=c["sim_p"], bad_keys=c["bad_keys"],
                ok=bool(qtts.F0_LO <= f0 <= qtts.F0_HI and c["sim"] >= qtts.ASR_OK and not c["bad_keys"]),
                tts_text=v, dur=round(len(w2) / sr, 2), fixed=True)
    json.dump(rep, open(os.path.join(narr, "report.json"), "w"), ensure_ascii=False, indent=1)
    print("chosen", v, s, "f0", round(f0, 1), "line f0", m["f0"], "shift", round(shift, 2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3].split("|"), [int(x) for x in sys.argv[4].split(",")])
