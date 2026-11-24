# -*- coding: utf-8 -*-
"""旁白读音复核：逐行 wav → faster-whisper 识别 → 与稿子比无声调拼音，列出差异大的行。"""
import sys, json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import script as S
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import difflib
import soundfile as sf, numpy as np


def load16k(p):
    w, sr = sf.read(str(p), dtype="float32")
    n = int(len(w) * 16000 / sr)
    return np.interp(np.linspace(0, len(w) - 1, n), np.arange(len(w)), w).astype("float32")


vo = pathlib.Path(sys.argv[1])
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small", device="cpu", compute_type="int8", cpu_threads=4)
han = lambda s: "".join(re.findall(r"[一-鿿]", s))
bad = 0
for seg, lid, kind, sub, opt in S.iter_lines():
    segs, _ = m.transcribe(load16k(vo / f"{lid}.wav"), language="zh", beam_size=3, initial_prompt="以下是普通话的句子，讲周亚夫、章邯、项羽、赵高、司马欣。")
    hyp = han("".join(s.text for s in segs))
    ref = han(sub)
    a, b = lazy_pinyin(ref), lazy_pinyin(hyp)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    if r < 0.86:
        bad += 1
        print(f"{lid} {r:.2f}\n   稿: {ref}\n   识: {hyp}", flush=True)
print("lines flagged:", bad)
