"""Build the global timeline from the script and the processed narration durations,
and split subtitles into on-screen chunks aligned to the pauses in each take."""
import json
import os
import re
import sys
from dataclasses import dataclass, field

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from script_data import SEGMENTS  # noqa: E402

GAP = 0.18           # between sentences
POINT_GAP = 0.7      # after a "这说明什么" sentence
SEG_LEAD = {"coldopen": 0.5}
SEG_LEAD_DEFAULT = 0.8   # chapter transition
SEG_TAIL_DEFAULT = 0.3
HOLD_AFTER = {"c0_robot": 1.25, "c0_5": 0.15, "c0_9": 3.2, "c4_8": 1.0, "c10_14": 2.0, "c11_3": 6.5}


@dataclass
class Ev:
    id: str
    seg: str
    start: float
    end: float
    say: str
    sub: str
    kind: str
    style: str
    en: str = ""
    chunks: list = field(default_factory=list)   # [(t0, t1, text)]


@dataclass
class Seg:
    key: str
    title: str
    start: float
    end: float
    events: list


def split_phrases(text):
    """Split at sentence/clause punctuation, keeping the punctuation with the phrase."""
    parts = re.split(r"(?<=[，。；：？！…、])", text)
    return [p for p in parts if p.strip()]


def clean_sub(s):
    s = s.strip()
    s = re.sub(r"[。，、；：]+$", "", s)
    s = s.replace("。", "　").replace("……", "…")
    return s.strip()


def detect_pauses(wav, sr, min_len=0.12, thresh_db=-40):
    win = int(0.01 * sr)
    k = len(wav) // win
    if k == 0:
        return []
    fr = wav[: k * win].reshape(k, win)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    quiet = db < thresh_db
    pauses, i = [], 0
    while i < k:
        if quiet[i]:
            j = i
            while j < k and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= min_len and i > 0 and j < k:
                pauses.append(((i + j) / 2) * 0.01)
            i = j
        else:
            i += 1
    return pauses


def chunk_subtitle(sub, say, start, end, wav=None, sr=None, max_chars=28):
    """Group phrases into screen-sized chunks; time each chunk by aligning phrase breaks to pauses."""
    sub_ph = split_phrases(sub)
    say_ph = split_phrases(say)
    dur = end - start
    # phrase boundary times
    times = None
    if wav is not None and len(sub_ph) == len(say_ph) and len(sub_ph) > 1:
        pauses = detect_pauses(wav, sr)
        need = len(say_ph) - 1
        if len(pauses) >= need:
            # choose the `need` pauses closest to proportional positions
            lens = np.array([len(p) for p in say_ph], float)
            prop = np.cumsum(lens)[:-1] / lens.sum() * dur
            chosen, used = [], set()
            for p in prop:
                cands = [(abs(q - p), q) for q in pauses if q not in used]
                if not cands:
                    break
                q = min(cands)[1]
                used.add(q)
                chosen.append(q)
            if len(chosen) == need and all(np.diff(chosen) > 0):
                times = [0.0] + chosen + [dur]
    if times is None:
        lens = np.array([max(1, len(re.sub(r"\s", "", p))) for p in sub_ph], float)
        times = [0.0] + list(np.cumsum(lens) / lens.sum() * dur)
    # group phrases into chunks
    chunks, cur, c0 = [], "", 0.0
    for i, ph in enumerate(sub_ph):
        if cur and len(cur) + len(ph) > max_chars:
            chunks.append((start + c0, start + times[i], clean_sub(cur)))
            cur, c0 = "", times[i]
        cur += ph
    if cur:
        chunks.append((start + c0, end, clean_sub(cur)))
    return chunks


def build(voice_dir, robot_wav=None, seg_keys=None, allow_missing=False):
    rep = json.load(open(os.path.join(voice_dir, "proc_report.json")))
    t = 0.0
    segs = []
    for key, title, lines in SEGMENTS:
        if seg_keys and key not in seg_keys:
            continue
        s0 = t
        t += SEG_LEAD.get(key, SEG_LEAD_DEFAULT)
        evs = []
        for ln in lines:
            kind = ln.get("kind", "narr")
            style = ln.get("style", "")
            if kind == "robot":
                if robot_wav is None:
                    continue
                w, sr = sf.read(robot_wav, dtype="float32")
                path = robot_wav
            else:
                if ln["id"] not in rep:
                    if not allow_missing:
                        raise KeyError(f"missing processed audio for {ln['id']}")
                    sr = 24000
                    w = np.zeros(int(sr * len(re.sub(r"[^\u4e00-\u9fff]", "", ln["say"])) / 4.9), np.float32)
                    path = None
                else:
                    path = os.path.join(voice_dir, "proc", f"{ln['id']}.wav")
                    w, sr = sf.read(path, dtype="float32")
            d = len(w) / sr
            ev = Ev(ln["id"], key, t, t + d, ln["say"], ln.get("sub", ln["say"]), kind, style, ln.get("en", ""))
            ev.audio = path
            ev.chunks = chunk_subtitle(ev.sub, ev.say, ev.start, ev.end, w, sr)
            evs.append(ev)
            t += d
            t += HOLD_AFTER.get(ln["id"], POINT_GAP if style == "point" else GAP)
        t += SEG_TAIL_DEFAULT
        segs.append(Seg(key, title, s0, t, evs))
    return segs, t


def ev_by_id(segs):
    return {e.id: e for s in segs for e in s.events}


if __name__ == "__main__":
    segs, total = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, allow_missing=True,
                        seg_keys=sys.argv[3].split(",") if len(sys.argv) > 3 else None)
    for s in segs:
        print(f"{s.key:10s} {s.start:7.2f} - {s.end:7.2f}")
        for e in s.events:
            print(f"   {e.id:9s} {e.start:7.2f} {e.end:7.2f}  " + " | ".join(f"{c[0]:.1f}:{c[2]}" for c in e.chunks))
    print("total", round(total, 2))
