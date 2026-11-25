"""ASR 回读：faster-whisper（medium）逐句识别，按无调拼音比对，算拼音错误率（PER）。
python asr_check.py [id 前缀...]  -> $WORK/asr.json，打印超阈值的句子
"""
import os, sys, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WK = os.environ.get("WORK", "/tmp/claude-0/work")
_M = None


def norm(s):
    return re.sub(r"[^一-鿿0-9a-zA-Z]", "", s)


CN = "零一二三四五六七八九"


def num2cn(n):
    n = int(n)
    if n == 0:
        return "零"
    out, units = "", ["", "十", "百", "千"]
    ds = str(n)
    for i, ch in enumerate(ds):
        k = len(ds) - i - 1
        if ch == "0":
            if not out.endswith("零"):
                out += "零"
        else:
            out += CN[int(ch)] + units[k]
    out = out.rstrip("零")
    return out[1:] if out.startswith("一十") else out


def digits_variants(s):
    a = re.sub(r"\d+", lambda m: num2cn(m.group()), s)
    b = re.sub(r"\d", lambda m: CN[int(m.group())], s)
    return [a, b]


def py(s):
    return lazy_pinyin(norm(s))


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]


def model():
    global _M
    if _M is None:
        _M = WhisperModel("/tmp/claude-0/models/fw-medium", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 2)))
    return _M


def transcribe(x, sr, prompt=None):
    if x.ndim > 1:
        x = x.mean(1)
    a = resample_poly(x, 16000 // np.gcd(sr, 16000), sr // np.gcd(sr, 16000)).astype(np.float32)
    segs, _ = model().transcribe(a, language="zh", beam_size=5, initial_prompt=prompt or "以下是普通话的句子。")
    return "".join(s.text for s in segs)


def check(path, ref):
    x, sr = sf.read(path)
    hyp = transcribe(x, sr)
    r = py(ref)
    per = min(ed(r, py(v)) / max(1, len(r)) for v in digits_variants(hyp))
    return hyp, per


if __name__ == "__main__":
    pre = sys.argv[1:] or [""]
    res = json.load(open(f"{WK}/asr.json")) if os.path.exists(f"{WK}/asr.json") else {}
    bad = []
    for d in all_lines():
        if not any(d["id"].startswith(p) for p in pre):
            continue
        p = f"{WK}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        hyp, per = check(p, d["say"])
        res[d["id"]] = dict(per=round(per, 3), hyp=hyp, ref=d["say"])
        flag = per > 0.10
        print(("BAD " if flag else "ok  ") + f"{d['id']} {per:.2f}" + (f"\n   want {norm(d['say'])}\n   got  {norm(hyp)}" if flag else ""), flush=True)
        if flag:
            bad.append(d["id"])
    json.dump(res, open(f"{WK}/asr.json", "w"), ensure_ascii=False, indent=1)
    allp = [v["per"] for v in res.values()]
    print("mean PER", round(float(np.mean(allp)), 3), "FAILED:", " ".join(bad))
