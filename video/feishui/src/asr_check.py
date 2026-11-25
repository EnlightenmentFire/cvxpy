# -*- coding: utf-8 -*-
"""faster-whisper 回读每句旁白，按无调拼音比对；输出 WORK/tts/asr.json 并列出可疑句。
usage: python asr_check.py [proc|raw] [id_prefix ...]"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
from faster_whisper import WhisperModel
import numpy as _np, soundfile as _sf
from scipy.signal import resample_poly as _rp
def load16(path):
    x, sr = _sf.read(path, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    g = _np.gcd(sr, 16000)
    return _rp(x, 16000 // g, sr // g).astype(_np.float32)
from pypinyin import lazy_pinyin
import difflib

W = os.environ.get("WORK", "/tmp/claude-0/work")
kind = sys.argv[1] if len(sys.argv) > 1 else "proc"
pre = sys.argv[2:]
model = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=4)
CLEAN = r"[，。？！：；、“”《》（）·\s,.?!:;'\"]"


def py(s):
    return lazy_pinyin(re.sub(CLEAN, "", s))


res, bad = [], []
for d in all_lines():
    if pre and not any(d["id"].startswith(p) for p in pre):
        continue
    p = f"{W}/tts/{kind}/{d['id']}.wav"
    if not os.path.exists(p):
        continue
    segs, _ = model.transcribe(load16(p), language="zh", beam_size=5, initial_prompt="以下是普通话的句子，关于淝水之战、苻坚、谢安。")
    hyp = "".join(s.text for s in segs)
    a, b = py(d["say"]), py(hyp)
    sm = difflib.SequenceMatcher(a=a, b=b)
    err = 1 - sm.ratio()
    diffs = [(" ".join(a[i1:i2]), " ".join(b[j1:j2])) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    r = dict(id=d["id"], ref=d["say"], hyp=hyp, err=round(err, 3), diffs=diffs)
    res.append(r)
    if err > 0.08:
        bad.append(r)
    print(f"{d['id']} err={err:.3f} {hyp}", flush=True)
json.dump(res, open(f"{W}/tts/asr_{kind}.json", "w"), ensure_ascii=False, indent=1)
tot = sum(len(py(r["ref"])) for r in res)
werr = sum(r["err"] * len(py(r["ref"])) for r in res) / max(1, tot)
print(f"\nlines={len(res)} weighted pinyin error={werr:.3f}  suspicious={len(bad)}")
for r in bad:
    print(" !", r["id"], r["err"], r["diffs"][:6])
