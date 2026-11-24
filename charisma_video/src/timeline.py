# -*- coding: utf-8 -*-
"""Process narration clips and lay out the global timeline (timeline.json + voice.wav)."""
import os, sys, json
import numpy as np, soundfile as sf
from audio import SR, ffmpeg_proc, compress_pauses, normalize_voice, load, place, undb
import script
from engine import split_sub

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "voice", "lines")
FIN = os.path.join(HERE, "voice", "final"); os.makedirs(FIN, exist_ok=True)

TEMPO = {"n": 1.06, "q": 1.0, "en": 0.80}
START = 1.6
GAP = 0.35
SEG_GAP = 1.3
STORY_SEGS = {"lot", "designate", "elect", "blood", "office"}   # line 0 is spoken over the map

def clip(key, kind):
    raw = os.path.join(HERE, "voice", "en_5.wav") if kind == "en" else os.path.join(RAW, key + ".wav")
    out = os.path.join(FIN, key + ".wav")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(raw):
        tmp = out + ".tmp.wav"
        ffmpeg_proc(raw, tmp, TEMPO[kind])
        y = compress_pauses(load(tmp))
        y = normalize_voice(y, -18.0)
        if kind == "en":
            y *= undb(-1.5)
        sf.write(out, y.astype(np.float32), SR)
        os.remove(tmp)
    return out

def build(allow_missing=False):
    segs = []
    t = START
    for si, seg in enumerate(script.SEGMENTS):
        sid = seg["id"]
        s = dict(id=sid, scene=seg["scene"], tag=seg.get("tag", ""), road=seg.get("road"), lines=[])
        if sid == "title":
            t += 1.2            # title card breathes before narration
        s["t0"] = t
        for i, ln in enumerate(seg["lines"]):
            kind = ln.get("k", "n")
            key = f"{sid}_{i:02d}"
            raw = os.path.join(HERE, "voice", "en_5.wav") if kind == "en" else os.path.join(RAW, key + ".wav")
            if not os.path.exists(raw):
                if allow_missing:
                    dur = max(1.5, len(ln["t"]) / 5.0)
                    path = None
                else:
                    raise FileNotFoundError(raw)
            else:
                path = clip(key, kind)
                dur = sf.info(path).duration
            text = ln["t"]
            chunks = [] if kind == "en" else split_sub(text)
            # distribute chunk times by character count
            weights = [max(1, sum(1 for ch in c if ch.strip() and ch not in "，。、：；？！“”")) for c in chunks]
            tot = sum(weights) or 1
            ct, ch_out = t, []
            for c, wgt in zip(chunks, weights):
                d = dur * wgt / tot
                ch_out.append([round(ct, 3), round(ct + d, 3), c])
                ct += d
            s["lines"].append(dict(key=key, k=kind, text=text, cue=ln.get("cue"), t0=round(t, 3), t1=round(t + dur, 3),
                                   path=path, chunks=ch_out, sub2=ln.get("sub2")))
            gap = GAP
            if text.startswith("这说明什么"):
                gap = 0.75
            if kind == "en":
                gap = 1.1
            if key == "cold_04":
                gap = 0.7
            if sid in STORY_SEGS and i == 0:
                gap = 1.3        # travel to the end of the road, then into the story
            if i + 1 < len(seg["lines"]) and seg["lines"][i + 1]["t"].startswith("这说明什么"):
                gap = max(gap, 0.6)
            t += dur + gap
        t -= gap
        s["t1"] = round(t, 3)
        segs.append(s)
        t += SEG_GAP if sid != "cold" else 1.0
    end = t + 1.5
    tl = dict(segments=segs, end_card=[round(t, 3), round(end + 3.0, 3)], total=round(end + 3.0, 3))
    return tl

def voice_track(tl, out):
    N = int(tl["total"] * SR) + SR
    buf = np.zeros(N, np.float32)
    for s in tl["segments"]:
        for ln in s["lines"]:
            if ln["path"]:
                place(buf, load(ln["path"]), ln["t0"])
    sf.write(out, buf, SR)
    return buf

if __name__ == "__main__":
    allow = "--allow-missing" in sys.argv
    tl = build(allow)
    json.dump(tl, open(os.path.join(HERE, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("total", tl["total"], "s =", round(tl["total"] / 60, 2), "min")
    if not allow:
        voice_track(tl, os.path.join(HERE, "voice", "voice_track.wav"))
