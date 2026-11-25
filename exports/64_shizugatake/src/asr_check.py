# -*- coding: utf-8 -*-
"""ASR read-back (faster-whisper small, int8) of processed narration lines; compares toneless pinyin.
usage: python asr_check.py [id prefixes...]  -> work/tts/asr.json, prints lines with PER > 0.12"""
import sys, os, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WK = "/tmp/claude-0/work"
OUT = f"{WK}/tts/asr.json"
_m = None


def model():
    global _m
    if _m is None:
        _m = WhisperModel(f"{WK}/models/fw-small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 2)))
    return _m


D = "零一二三四五六七八九"


def num_cn(n):
    if n < 10:
        return D[n]
    if n < 100:
        return ("" if n // 10 == 1 else D[n // 10]) + "十" + (D[n % 10] if n % 10 else "")
    if n < 1000:
        r = n % 100
        return D[n // 100] + "百" + ("" if r == 0 else ("零" + D[r] if r < 10 else ("一" + num_cn(r) if r < 20 else num_cn(r))))
    if n < 10000:
        r = n % 1000
        return D[n // 1000] + "千" + ("" if r == 0 else ("零" + num_cn(r) if r < 100 else num_cn(r)))
    return "".join(D[int(c)] for c in str(n))


def digits(s):
    s = re.sub(r"(\d+)\.(\d+)", lambda m: num_cn(int(m.group(1))) + "点" + "".join(D[int(c)] for c in m.group(2)), s)
    s = re.sub(r"\d{4}(?=年)", lambda m: "".join(D[int(c)] for c in m.group(0)), s)
    return re.sub(r"\d+", lambda m: num_cn(int(m.group(0))), s)


def norm(s):
    return re.sub(r"[^一-鿿A-Za-z]", "", digits(s))


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]


def check(path, ref, prompt=None):
    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(1)
    x = resample_poly(x, 1, sr // 16000).astype(np.float32) if sr != 16000 else x.astype(np.float32)
    segs, _ = model().transcribe(x, language="zh", beam_size=5, initial_prompt=prompt or "以下是普通话的句子。")
    hyp = "".join(s.text for s in segs)
    a, b = lazy_pinyin(norm(ref)), lazy_pinyin(norm(hyp))
    return hyp, ed(a, b) / max(1, len(a))


if __name__ == "__main__":
    pre = sys.argv[1:] or [""]
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for d in all_lines():
        if not any(d["id"].startswith(p) for p in pre):
            continue
        p = f"{WK}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        hyp, per = check(p, d["say"], "日本战国，丰臣秀吉，柴田胜家，佐久间盛政，贱岳，余吴湖，木之本。")
        res[d["id"]] = dict(per=round(per, 3), hyp=hyp, ref=d["say"])
        if per > 0.12:
            print(f"BAD {d['id']} per={per:.2f}\n  ref {d['say']}\n  hyp {hyp}", flush=True)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    v = [r["per"] for r in res.values()]
    print(f"{len(v)} lines, mean PER {np.mean(v):.3f}, >0.12: {sum(x > 0.12 for x in v)}")
