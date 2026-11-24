# -*- coding: utf-8 -*-
"""ASR 回听校验：逐句转写 TTS 音频，与目标文本按拼音（带声调）比对，列出可疑句。"""
import json, os, re, sys
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin, Style
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = json.load(open(os.path.join(ROOT, "audio", "lines.json"), encoding="utf8"))
only = set(sys.argv[1:])
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
han = lambda s: re.sub(r"[^一-鿿]", "", s)
def py(s, tone=False): return lazy_pinyin(han(s), style=Style.TONE3 if tone else Style.NORMAL)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p = d[:]; d[0] = i
        for j, y in enumerate(b, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (x != y))
    return d[-1]
res = []
for l in lines:
    if only and l["id"] not in only: continue
    f = os.path.join(ROOT, "audio", "vo_raw", l["id"] + ".wav")
    if not os.path.exists(f): continue
    segs, _ = m.transcribe(f, language="zh", beam_size=5, initial_prompt="以下是普通话的句子，讲西晋刘琨、祖逖、石勒、刘聪、段匹磾的历史。", condition_on_previous_text=False)
    hyp = "".join(s.text for s in segs)
    a, b = py(l["tts"]), py(hyp); e = ed(a, b); r = e / max(1, len(a))
    res.append(dict(id=l["id"], kind=l["kind"], err=round(r, 3), ref=l["tts"], hyp=hyp))
    print(("!! " if r > .12 else "   ") + l["id"], l["kind"], "%.2f" % r, "|", han(l["tts"]), "|", han(hyp), flush=True)
json.dump(res, open(os.path.join(ROOT, "audio", "qa_asr.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
