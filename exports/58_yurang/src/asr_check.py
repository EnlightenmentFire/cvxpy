"""faster-whisper 逐句回读：按无调拼音比对脚本（错误率 PER），并输出逐字时间（字幕对时用）。
usage: python asr_check.py [id 前缀 ...]   -> tts/asr.json, tts/align.json
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import opencc
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

WK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WK}/tts/proc"
_cc = opencc.OpenCC("t2s")
NUM = dict(zip("0123456789", "零一二三四五六七八九"))


def norm(s):
    s = _cc.convert(s)
    s = "".join(NUM.get(c, c) for c in s)
    return re.sub(r"[^一-鿿]", "", s)


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[-1]


def main():
    pre = sys.argv[1:] or [""]
    m = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=4)
    res = json.load(open(f"{WK}/tts/asr.json")) if os.path.exists(f"{WK}/tts/asr.json") else {}
    al = json.load(open(f"{WK}/tts/align.json")) if os.path.exists(f"{WK}/tts/align.json") else {}
    bad = []
    for d in all_lines():
        if not any(d["id"].startswith(p) for p in pre):
            continue
        x, sr = sf.read(f"{PROC}/{d['id']}.wav")
        x = resample_poly(x.astype(np.float32), 1, sr // 16000).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5, word_timestamps=True,
                               initial_prompt="以下是普通话的句子。", vad_filter=False)
        chars = []
        hyp = ""
        for s in segs:
            hyp += s.text
            for w in s.words or []:
                cs = norm(w.word)
                for k, ch in enumerate(cs):
                    a = w.start + (w.end - w.start) * k / len(cs)
                    b = w.start + (w.end - w.start) * (k + 1) / len(cs)
                    chars.append((round(a, 3), round(b, 3)))
        want, got = lazy_pinyin(norm(d["say"])), lazy_pinyin(norm(hyp))
        per = edit(want, got) / max(1, len(want))
        res[d["id"]] = dict(per=round(per, 3), hyp=norm(hyp), want=norm(d["say"]))
        n = len(want)
        if chars:
            al[d["id"]] = [chars[min(len(chars) - 1, int(i * len(chars) / n))] for i in range(n)]
        flag = "OK " if per <= 0.08 else "BAD"
        if per > 0.08:
            bad.append(d["id"])
        print(f"{flag} {d['id']} per={per:.2f}" + ("" if per <= 0.08 else f"\n   want {norm(d['say'])}\n   got  {norm(hyp)}"), flush=True)
    json.dump(res, open(f"{WK}/tts/asr.json", "w"), ensure_ascii=False, indent=1)
    json.dump(al, open(f"{WK}/tts/align.json", "w"))
    print("BAD:", " ".join(bad))


if __name__ == "__main__":
    main()
