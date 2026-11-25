# -*- coding: utf-8 -*-
"""ASR read-back (faster-whisper) of every processed line, compared in toneless pinyin.
usage: python asr_check.py [model] -> WORK/asr_report.json, prints lines with pinyin error rate > 0.12"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def norm(s):
    return re.sub(r"[^一-鿿0-9a-zA-Z]", "", s)


CN = "零一二三四五六七八九"


def num2cn(m):
    t = m.group(0)
    if len(t) == 4 and t.startswith(("17", "18", "19", "20")):
        return "".join(CN[int(c)] for c in t)
    n = int(t)
    if n < 10:
        return CN[n]
    if n < 100:
        return (CN[n // 10] if n >= 20 else "") + "十" + (CN[n % 10] if n % 10 else "")
    return "".join(CN[int(c)] for c in t)


def py(s):
    s = re.sub(r"\d+", num2cn, s)
    return lazy_pinyin(norm(s))


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]


if __name__ == "__main__":
    m = WhisperModel(sys.argv[1] if len(sys.argv) > 1 else "small", device="cpu", compute_type="int8", cpu_threads=2)
    rep, E, N = [], 0, 0
    only = sys.argv[2:] if len(sys.argv) > 2 else None
    for d in all_lines():
        if only and not any(d["id"].startswith(o) for o in only):
            continue
        fn = f"{WORK}/tts/proc/{d['id']}.wav"
        if not os.path.exists(fn):
            continue
        import soundfile as sf
        from scipy.signal import resample_poly
        x, sr = sf.read(fn); x = resample_poly(x, 1, sr // 16000).astype("float32")
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。羽柴秀吉，高松城，清水宗治，毛利，足守川，备中。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        e = ed(a, b); E += e; N += len(a)
        rep.append(dict(id=d["id"], ref=d["say"], hyp=hyp, per=round(e / max(len(a), 1), 3)))
        if e / max(len(a), 1) > 0.12:
            print(f"{d['id']} PER={e / len(a):.2f}\n  REF {d['say']}\n  HYP {hyp}", flush=True)
    json.dump(rep, open(f"{WORK}/asr_report.json", "w"), ensure_ascii=False, indent=1)
    print(f"overall pinyin error rate {E / max(N, 1):.3f} over {len(rep)} lines")
