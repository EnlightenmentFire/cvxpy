"""ASR read-back of processed lines (faster-whisper large-v3-turbo); compare toneless pinyin with the script.
usage: python asr_check.py [id prefixes...]  -> /tmp/claude-0/work/tts/asr_report.json
"""
import sys, os, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin

PROC = "/tmp/claude-0/work/tts/proc"
NUM = dict(zip("0123456789", "零一二三四五六七八九"))
_m = None


def norm(s):
    s = "".join(NUM.get(c, c) for c in s)
    return re.sub(r"[^一-鿿]", "", s)


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]; dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
    return dp[-1]


def model():
    global _m
    if _m is None:
        _m = WhisperModel("/tmp/claude-0/models/fw-large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    return _m


def check(path, expected):
    x, sr = sf.read(path)
    x = resample_poly(x, 1, 3).astype(np.float32) if sr == 48000 else x.astype(np.float32)
    segs, _ = model().transcribe(x, language="zh", beam_size=5, vad_filter=False,
                                 initial_prompt="以下是普通话的句子。正念认知疗法，西格尔，蒂斯代尔，凯肯，戈亚尔，范达姆，杂阿含经。")
    hyp = "".join(s.text for s in segs)
    a, b = lazy_pinyin(norm(expected)), lazy_pinyin(norm(hyp))
    return hyp, edit(a, b) / max(1, len(a))


if __name__ == "__main__":
    pre = sys.argv[1:] or [""]
    p = "/tmp/claude-0/work/tts/asr_report.json"
    rep = json.load(open(p)) if os.path.exists(p) else {}
    for d in all_lines():
        if any(d["id"].startswith(x) for x in pre) and os.path.exists(f"{PROC}/{d['id']}.wav"):
            hyp, per = check(f"{PROC}/{d['id']}.wav", d["say"])
            ok = per <= 0.08
            rep[d["id"]] = dict(hyp=hyp, per=round(per, 3), ok=ok, text=d["say"])
            print(f"{'OK ' if ok else 'BAD'} {d['id']} PER={per:.2f}" + ("" if ok else f"\n   want {norm(d['say'])}\n   got  {norm(hyp)}"), flush=True)
    json.dump(rep, open(p, "w"), ensure_ascii=False, indent=1)
    print("BAD:", " ".join(k for k, v in rep.items() if not v["ok"]))
