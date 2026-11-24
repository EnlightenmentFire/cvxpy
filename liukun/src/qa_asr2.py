# -*- coding: utf-8 -*-
"""第二个 ASR（whisper large-v3）复核全部句子；与 medium 的结果并排，输出两者都偏差大的句子"""
import json, os, re, sys
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf8"))
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
han = lambda s: re.sub(r"[^一-鿿]", "", s)
NUM = {"零": "0", "一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
out = []
for l in lines:
    f = os.path.join(ROOT, "audio", "vo", l["id"] + ".wav")
    segs, _ = m.transcribe(f, language="zh", beam_size=5, condition_on_previous_text=False)
    hyp = "".join(s.text for s in segs)
    a, b = lazy_pinyin(han(l["tts"])), lazy_pinyin(han(hyp)); r = ed(a, b) / max(1, len(a))
    out.append(dict(id=l["id"], kind=l["kind"], err=round(r, 3), ref=l["tts"], hyp=hyp))
    print(("!! " if r > .1 else "   ") + l["id"], l["kind"], "%.2f" % r, "|", han(l["tts"]), "|", hyp, flush=True)
json.dump(out, open(os.path.join(ROOT, "audio", "qa_asr_large.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
