"""ASR read-back of processed lines with faster-whisper; compare toneless pinyin to the script.
usage: python asr_check.py <id prefixes...>   (or --file some.wav "expected text")
"""
import sys, os, json, re
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import opencc

PROC = "/tmp/claude-0/work/tts/proc"
_cc = opencc.OpenCC("t2s")
NUM = {"0": "零", "1": "一", "2": "二", "3": "三", "4": "四", "5": "五", "6": "六", "7": "七", "8": "八", "9": "九"}


def norm(s):
    s = _cc.convert(s)
    s = "".join(NUM.get(c, c) for c in s)
    return re.sub(r"[^一-鿿]", "", s)


def py(s):
    return lazy_pinyin(norm(s))


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[-1]


_model = None


def model():
    global _model
    if _model is None:
        _model = WhisperModel("/tmp/claude-0/models/fw-large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    return _model


def load16k(path):
    import soundfile as sf
    from scipy.signal import resample_poly
    x, sr = sf.read(path)
    if x.ndim > 1:
        x = x.mean(1)
    g = np.gcd(int(sr), 16000)
    return resample_poly(x, 16000 // g, int(sr) // g).astype(np.float32)


def transcribe(path):
    segs, _ = model().transcribe(load16k(path), language="zh", beam_size=5, vad_filter=False,
                                 initial_prompt="以下是普通话的句子。托克维尔，博蒙，乔克托人，孟菲斯，新英格兰。")
    return "".join(s.text for s in segs)


def check(path, expected):
    hyp = transcribe(path)
    a, b = py(expected), py(hyp)
    per = edit(a, b) / max(1, len(a))
    return hyp, per


if __name__ == "__main__":
    pre = sys.argv[1:]
    report = {}
    for d in all_lines():
        if any(d["id"].startswith(p) for p in pre) and os.path.exists(f"{PROC}/{d['id']}.wav"):
            hyp, per = check(f"{PROC}/{d['id']}.wav", d["say"])
            flag = "OK " if per <= 0.08 else "BAD"
            print(f"{flag} {d['id']} PER={per:.2f}\n   want: {norm(d['say'])}\n   got : {norm(hyp)}", flush=True)
            report[d["id"]] = dict(hyp=hyp, per=per)
    os.makedirs("/tmp/claude-0/work/tts", exist_ok=True)
    p = "/tmp/claude-0/work/tts/asr_report.json"
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(report)
    json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)
