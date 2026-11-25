"""faster-whisper large-v3-turbo 回读每句旁白，按无调拼音比对，错误率 > 8% 标 BAD。
python asr_check.py [id前缀...]   → WORK/tts/asr.json
python asr_check.py --mix WAV t0 t1 ...  → 抽查成片某几处（各 12 秒）
"""
import sys, os, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import opencc

W = "/tmp/claude-0/work"
_cc = opencc.OpenCC("t2s")
NUM = dict(zip("0123456789", "零一二三四五六七八九"))
PROMPT = "以下是普通话的句子。墨俣，洲股，信长公记，太田牛一，小濑甫庵，太阁记，武功夜话，川并众，蜂须贺小六，斋藤龙兴，稻叶山，佐久间信盛，柴田胜家，弗洛伊斯，顾颉刚，巴特利特。"
_m = None


def model():
    global _m
    if _m is None:
        _m = WhisperModel("/tmp/claude-0/models/fw-large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    return _m


def norm(s):
    s = _cc.convert(s)
    s = "".join(NUM.get(c, c) for c in s)
    return re.sub(r"[^一-鿿]", "", s)


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]; dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
    return dp[-1]


def load16k(x, sr):
    if x.ndim > 1:
        x = x.mean(1)
    g = np.gcd(int(sr), 16000)
    return resample_poly(x, 16000 // g, int(sr) // g).astype(np.float32)


def transcribe(x16):
    segs, _ = model().transcribe(x16, language="zh", beam_size=5, vad_filter=False, initial_prompt=PROMPT)
    return "".join(s.text for s in segs)


def per(exp, hyp):
    a, b = lazy_pinyin(norm(exp)), lazy_pinyin(norm(hyp))
    return edit(a, b) / max(1, len(a))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--mix"]:
        x, sr = sf.read(sys.argv[2])
        tl = json.load(open(f"{W}/timeline.json"))
        for t0 in map(float, sys.argv[3:]):
            seg = x[int(t0 * sr):int((t0 + 12) * sr)]
            hyp = transcribe(load16k(seg, sr))
            exp = "".join(l["say"] for l in tl["lines"] if l["end"] > t0 and l["start"] < t0 + 12)
            print(f"@{t0:.0f}s  PER≈{per(exp, hyp):.2f}\n  want: {norm(exp)}\n  got : {norm(hyp)}")
        sys.exit()
    pre = sys.argv[1:] or [""]
    out = f"{W}/tts/asr.json"
    rep = json.load(open(out)) if os.path.exists(out) else {}
    bad = []
    for d in all_lines():
        p = f"{W}/tts/proc/{d['id']}.wav"
        if not any(d["id"].startswith(q) for q in pre) or not os.path.exists(p):
            continue
        x, sr = sf.read(p)
        hyp = transcribe(load16k(x, sr))
        e = per(d["say"], hyp)
        rep[d["id"]] = dict(per=round(e, 3), hyp=hyp)
        flag = "OK " if e <= 0.08 else "BAD"
        if e > 0.08:
            bad.append(d["id"])
        print(f"{flag} {d['id']} {e:.2f}" + ("" if e <= 0.08 else f"\n   want {norm(d['say'])}\n   got  {norm(hyp)}"), flush=True)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1)
    print("BAD:", " ".join(bad))
