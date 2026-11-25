# -*- coding: utf-8 -*-
"""每层 2–3 个候选里挑一个：不能有人声；2–4 kHz 越少越好（不抢人声）；
铺底/回落/尾声要平稳（突跳小），高潮要有起伏。
python choose_layers.py ACE_DIR OUT.json"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from music_qc import qc  # noqa: E402


HALLU = ["独播剧场", "Television", "点赞", "订阅", "字幕", "Subtitles", "感谢观看", "Thank you", "明镜", "栏目"]


def has_vocals(r):
    """Whisper 在纯音乐上常幻听出固定的片头/字幕语句；这类不算人声。只有识别出成句内容且 no_speech 低才算"""
    t = r.get("asr_text", "")
    for h in HALLU:
        t = t.replace(h, "")
    t = re.sub(r"[¶♪♫\s.。,，!！?？…\-—a-zA-Z]", "", t)
    return len(t) >= 8 and r.get("no_speech", 1.0) < 0.5


def score(layer, r):
    s = -r["band_2_4k"] * 8.0
    if layer in ("base", "after", "coda"):
        s -= r["max_jump_db"] / 3.0 + max(0, r["st_p95_minus_p50"] - 8) / 2.0
    elif layer == "push":
        s -= r["max_jump_db"] / 4.0
    elif layer == "climax":
        s += min(r["st_p95_minus_p50"], 14) / 2.0
    return s


def main(ace_dir, out):
    from faster_whisper import WhisperModel
    wm = WhisperModel("/home/user/work/models/whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8", cpu_threads=4)
    rep, pick = {}, {}
    for layer in ("base", "push", "climax", "after", "coda"):
        cands = []
        for d in sorted(glob.glob(os.path.join(ace_dir, f"{layer}_*"))):
            for f in glob.glob(os.path.join(d, "*.wav")):
                r = qc(f, wm)
                r["vocals"] = has_vocals(r)
                r["score"] = round(score(layer, r), 2)
                cands.append(r)
        ok = [c for c in cands if not c["vocals"]] or cands
        best = max(ok, key=lambda c: c["score"])
        pick[layer] = best["file"]
        rep[layer] = cands
        print(layer, "→", os.path.basename(os.path.dirname(best["file"])), json.dumps(best, ensure_ascii=False))
    json.dump(pick, open(out, "w"), ensure_ascii=False, indent=1)
    json.dump(rep, open(out.replace(".json", "_qc.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
