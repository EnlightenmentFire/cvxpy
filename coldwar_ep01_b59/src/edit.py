"""Edit decision list: shots driven by narration timing -> timeline.json, voice track, score + SFX, final mix.

Run in the qwen312 venv (needs voiceqc deps + scipy).
  python edit.py voice    # process QC'd lines -> 48 kHz processed wavs + durations
  python edit.py build    # timeline.json + voice.wav + music.wav + mix.wav
"""
import json
import math
import os
import re
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import voiceqc as Q  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
QC = os.path.join(SCR, "tts/full_clone/qc.json")
PROC = os.path.join(SCR, "voice_proc")
OUT = os.path.join(SCR, "edit")
SR = 48000
FPS = 30
TEMPO_N, TEMPO_Q = 1.30, 1.16

SHOTS = [
    dict(id="cold", fn="cold_open", fixed=3.2, hypo=True),
    dict(id="open_text", lines=["a01", "a02"], pre=0.6, post=0.8),
    dict(id="title", fixed=3.0),
    dict(id="u2", lines=["b01", "b02"], pre=0.3),
    dict(id="globe_range", lines=["b03"]),
    dict(id="blockade", lines=["b04"]),
    dict(id="defcon", lines=["b05"]),
    dict(id="rooms", lines=["b06"]),
    dict(id="subs", lines=["b07", "b08"], post=0.5),
    dict(id="timeline", lines=["c01"], pre=0.3),
    dict(id="ev_cuba", lines=["c02", "c03"]),
    dict(id="ev_arctic", lines=["c04"], post=0.3),
    dict(id="dive", lines=["c05", "c06"], pre=1.5, post=0.4),
    dict(id="section", lines=["d01", "d02", "d03"]),
    dict(id="knock", lines=["d04", "d05", "d06"]),
    dict(id="sonar", lines=["d07", "d08"], post=2.0),
    dict(id="quote_sav", lines=["d09", "d10", "d11", "d12", "d13"], suppress=["d10", "d12"]),
    dict(id="orders", lines=["d14", "d15", "d16", "d17"], suppress=["d15"], post=0.6),
    dict(id="hypo_launch", fixed=2.2, hypo=True),
    dict(id="hypo_burst", lines=["e01", "e02"], pre=1.8, post=0.5, hypo=True),
    dict(id="hypo_globe", lines=["e03", "e04"], post=1.2, hypo=True),
    dict(id="hypo_out", lines=["e05"], pre=1.4, post=0.6, suppress=["e05"]),
    dict(id="surfacing", lines=["f01", "f02"], pre=0.3),
    dict(id="topdown", lines=["f03", "f04", "f05"]),
    dict(id="tower", lines=["f06", "f07", "f08", "f09"]),
    dict(id="photo", fixed=2.2),
    dict(id="arkhipov", lines=["f10"]),
    dict(id="checklist", lines=["f11"], post=0.8, suppress=["f11"]),
    dict(id="vote", lines=["g01", "g02"]),
    dict(id="headline", lines=["g03", "g04", "g05"], suppress=["g04"]),
    dict(id="split", lines=["h01", "h02"]),
    dict(id="gitmo", lines=["h03"]),
    dict(id="hotline", lines=["h04", "h05"], post=0.8),
    dict(id="ending", lines=["i01", "i02", "i03", "i04", "i05"], suppress=["i02"], post=3.0),
    dict(id="credits", fixed=4.5),
]


def gap_after(text, nxt_kind):
    if text.endswith("：") and nxt_kind == "Q":
        return 0.22
    if text.endswith(("。", "！", "？", "”")):
        return 0.34
    return 0.2


# ----------------------------------------------------------------------------
def process_voice():
    from voice_post import process_line
    os.makedirs(PROC, exist_ok=True)
    lines = json.load(open(os.path.join(ROOT, "audio/full/lines.json")))
    qc = json.load(open(QC))
    durs = {}
    rows = []
    for ln in lines:
        rec = qc[ln["id"]]
        x, sr = sf.read(rec["path"], dtype="float32")
        y = process_line(x, sr, ln["kind"], TEMPO_N, TEMPO_Q)
        p = os.path.join(PROC, ln["id"] + ".wav")
        sf.write(p, y, SR)
        durs[ln["id"]] = len(y) / SR
        rows.append({"id": ln["id"], "kind": ln["kind"], "dur": round(len(y) / SR, 2),
                     "f0": round(float(Q.f0_median(y, SR)), 1), "rate": round(float(Q.speech_rate(ln["tts"], y, SR)), 2),
                     "longest_pause": round(float(Q.longest_pause(y, SR)), 2), "tries": rec["tries"], "ser": rec["ser"],
                     "tone_warn": Q.tone_warnings(ln["tts"], rec["asr"]), "asr": rec["asr"]})
        print(rows[-1], flush=True)
    json.dump({"durs": durs, "rows": rows}, open(os.path.join(PROC, "durs.json"), "w"), ensure_ascii=False, indent=1)


# ----------------------------------------------------------------------------
def _w(s):
    return sum(0.55 if (c.isascii() and c.isalnum()) or c in "-·. " else 1.0 for c in s)


def _tokens(seg):
    try:
        import jieba
        jieba.setLogLevel(60)
        for w_ in ("萨夫兰斯卡娅", "阿尔希波夫", "萨维茨基", "奥尔洛夫", "凯托夫", "罗伯特·肯尼迪", "赫鲁晓夫", "关塔那摩",
                   "伦道夫号", "比尔号", "科尼号", "马尾藻海", "克里姆林宫", "20多公里", "300多发", "3400人", "核鱼雷",
                   "训练深弹", "值更军官", "参谋长", "柴电潜艇", "萨姆导弹", "木星导弹", "核空空导弹", "战术核武器"):
            jieba.add_word(w_, freq=200000)
        return list(jieba.cut(seg))
    except Exception:
        return list(seg)


def _hard_split(seg, max_w):
    rows, cur = [], ""
    for tok in _tokens(seg):
        if _w(cur + tok) <= max_w or not cur:
            cur += tok
        else:
            rows.append(cur)
            cur = tok
    if cur:
        rows.append(cur)
    return rows


def split_subs(text, max_w=16.0):
    """Split a line into subtitle cards (<=2 rows, width-aware, word boundaries via jieba)."""
    t = text.replace("——", "，")
    parts = [p for p in re.split(r"(?<=[。！？；])", t) if p.strip()]
    merged = []
    for p in parts:  # attach a lone closing quote to the previous sentence
        if merged and re.fullmatch(r"[”’」』）)\s]+", p.strip()):
            merged[-1] += p.strip()
        else:
            merged.append(p)
    cards = []
    for p in merged:
        p = p.strip()
        rows = []
        cur = ""
        for seg in re.split(r"(?<=[，：、])", p):
            if _w(cur + seg.rstrip("，：、")) <= max_w:
                cur += seg
            else:
                if cur:
                    rows.append(cur)
                    cur = ""
                if _w(seg.rstrip("，：、")) > max_w:
                    pieces = _hard_split(seg, max_w)
                    rows += pieces[:-1]
                    cur = pieces[-1]
                else:
                    cur = seg
        if cur:
            rows.append(cur)
        rows = [r.lstrip("，、：；。").rstrip("，、：；。") for r in rows]
        rows = [r for r in rows if r]
        # no orphans: fold a tiny last row back if it nearly fits
        if len(rows) >= 2 and _w(rows[-1]) <= 3 and _w(rows[-2] + rows[-1]) <= max_w + 2.5:
            rows[-2] += rows[-1]
            rows.pop()
        for i in range(0, len(rows), 2):
            cards.append("\n".join(rows[i:i + 2]))
    return cards


def build():
    os.makedirs(OUT, exist_ok=True)
    lines = {ln["id"]: ln for ln in json.load(open(os.path.join(ROOT, "audio/full/lines.json")))}
    durs = json.load(open(os.path.join(PROC, "durs.json")))["durs"]
    t = 0.0
    shots = []
    placements = []
    subs = []
    for sh in SHOTS:
        start = t
        cues = {}
        if "fixed" in sh:
            t += sh["fixed"]
        else:
            t += sh.get("pre", 0.15)
            ids = sh["lines"]
            for i, lid in enumerate(ids):
                d = durs[lid]
                cues[lid] = (round(t - start, 3), round(t - start + d, 3))
                placements.append((lid, t))
                # subtitles for this line
                if lid not in sh.get("suppress", []):
                    cards = split_subs(lines[lid]["text"])
                    w = np.array([max(1, len(re.sub(r"\s", "", c))) for c in cards], np.float64)
                    edges = t + np.concatenate([[0], np.cumsum(w / w.sum() * d)])
                    for c, a, b in zip(cards, edges[:-1], edges[1:]):
                        subs.append({"start": round(float(a), 3), "end": round(float(b) + 0.08, 3), "text": c,
                                     "line": lid})
                t += d
                if i + 1 < len(ids):
                    t += gap_after(lines[lid]["text"], lines[ids[i + 1]]["kind"])
            t += sh.get("post", 0.15)
        # snap shot boundary to frame grid
        t = round(t * FPS) / FPS
        shots.append({"id": sh["id"], "fn": sh.get("fn", sh["id"]), "start": round(start, 4), "end": round(t, 4),
                      "cues": cues, "hypo": sh.get("hypo", False)})
    total = t
    # subtitles must not overlap: trim each to next start
    subs.sort(key=lambda s: s["start"])
    for a, b in zip(subs[:-1], subs[1:]):
        a["end"] = min(a["end"], b["start"] - 0.02)
    tl = {"fps": FPS, "duration": round(total, 3), "frames": int(round(total * FPS)), "shots": shots, "subs": subs,
          "placements": placements}
    json.dump(tl, open(os.path.join(OUT, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print(f"total {total:.1f}s = {total / 60:.2f} min, {len(shots)} shots, {len(subs)} subtitle cards")
    # voice track
    n = int(math.ceil(total * SR)) + SR
    voice = np.zeros(n, np.float32)
    for lid, at in placements:
        y, _ = sf.read(os.path.join(PROC, lid + ".wav"), dtype="float32")
        i = int(at * SR)
        voice[i:i + len(y)] += y
    sf.write(os.path.join(OUT, "voice.wav"), voice, SR)
    import score
    music = score.build(tl, voice, SR)
    sf.write(os.path.join(OUT, "music.wav"), music, SR)
    mix = voice + music
    pk = np.max(np.abs(mix))
    if pk > 0.89:
        mix = np.tanh(mix / 0.89) * 0.89
    sf.write(os.path.join(OUT, "mix.wav"), mix.astype(np.float32), SR)
    print("voice active rms", round(float(Q.active_rms_db(voice, SR)), 1), "dBFS; music rms",
          round(float(20 * np.log10(np.sqrt(np.mean(music ** 2)) + 1e-12)), 1), "dBFS; mix peak",
          round(float(20 * np.log10(np.max(np.abs(mix)) + 1e-12)), 1))


if __name__ == "__main__":
    {"voice": process_voice, "build": build}[sys.argv[1]]()
