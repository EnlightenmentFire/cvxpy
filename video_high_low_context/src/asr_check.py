# -*- coding: utf-8 -*-
"""ASR read-back of processed clips (or a full mix). usage: asr_check.py clips.json proc_dir [cid_prefixes]"""
import json, os, re, sys
import numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("TTS_THREADS", "4")
from tts_qwen import Checker
clips = json.load(open(sys.argv[1]))
proc = sys.argv[2]
pre = tuple(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
chk = Checker()
bad = 0
for c in clips:
    if pre and not c["cid"].startswith(pre):
        continue
    p = os.path.join(proc, c["cid"] + ".wav")
    if not os.path.exists(p):
        continue
    a, sr = sf.read(p, dtype="float32")
    lang = {"en": "en", "jp": "ja"}.get(c["kind"], "zh")
    hyp = chk.asr(a, sr, lang)
    err = chk.score(c["tts"], hyp, lang) if lang != "en" else (0.0 if re.sub(r"[^a-z]", "", hyp.lower()) == re.sub(r"[^a-z]", "", c["tts"].lower()) else 1.0)
    flag = "OK " if err <= 0.06 else "BAD"
    bad += flag == "BAD"
    print(flag, c["cid"], round(err, 3), "|", c["tts"], "|", hyp, flush=True)
print("bad", bad)
