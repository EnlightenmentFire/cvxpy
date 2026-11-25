# -*- coding: utf-8 -*-
"""faster-whisper read-back per processed line; compare toneless pinyin (homophones ok). usage: asr_check.py [ids]"""
import sys, os, re, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(__file__))
from script import all_lines

W = "/tmp/claude-0/w73"
NUM = {"一五五": "一五五"}


def py(s):
    s = re.sub(r"[^一-鿿0-9]", "", s)
    s = re.sub(r"\d+", lambda m: "".join("零一二三四五六七八九"[int(c)] for c in m.group()), s)
    return lazy_pinyin(s)


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]


if __name__ == "__main__":
    ids = sys.argv[1:]
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 4)))
    res = []
    for d in all_lines():
        if ids and d["id"] not in ids: continue
        p = f"{W}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p): continue
        x, sr = sf.read(p, dtype="float32"); x = resample_poly(x, 1, 3).astype(np.float32)
        seg, _ = m.transcribe(x, language="zh", initial_prompt="以下是普通话的句子，关于三国曹操。", beam_size=5)
        hyp = "".join(s.text for s in seg)
        a, b = py(d["say"]), py(hyp)
        e = ed(a, b) / max(1, len(a))
        res.append(dict(id=d["id"], err=round(e, 3), ref=d["sub"], hyp=hyp))
        flag = "  <<<" if e > 0.12 else ""
        print(f"{d['id']} {e:.2f} {hyp}{flag}", flush=True)
    json.dump(res, open(f"{W}/out/asr_report.json", "w"), ensure_ascii=False, indent=1)
    tot = sum(r["err"] * len(py(r["ref"])) for r in res) / max(1, sum(len(py(r["ref"])) for r in res))
    print(f"overall pinyin error {tot:.3f}; flagged {sum(r['err'] > 0.12 for r in res)}")
