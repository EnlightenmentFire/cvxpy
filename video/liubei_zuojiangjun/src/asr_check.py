# -*- coding: utf-8 -*-
"""ASR 回读：faster-whisper（small）逐句识别处理后的旁白，按无调拼音与稿子（tts 文本）比对，输出错误率。
用法：python asr_check.py [id 前缀 ...]   结果写 $WORK/tts/asr.json，打印超过阈值的句子。
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
NUM = {"196": "一九六", "199": "一九九", "219": "二一九"}


def norm(s):
    for k, v in NUM.items():
        s = s.replace(k, v)
    s = re.sub(r"[^一-鿿0-9]", "", s)
    return lazy_pinyin(s)


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]


def main():
    pre = sys.argv[1:] or [""]
    m = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=4)
    res = {}
    bad = []
    tot_e = tot_n = 0
    for d in all_lines():
        if not any(d["id"].startswith(p) for p in pre):
            continue
        p = f"{WORK}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        import soundfile as sf, numpy as np
        from scipy.signal import resample_poly
        x, sr = sf.read(p, dtype="float32")
        if x.ndim > 1: x = x.mean(1)
        x = resample_poly(x, 16000, sr).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话历史纪录片旁白。")
        hyp = "".join(s.text for s in segs)
        a, b = norm(d["tts"]), norm(hyp)
        e = ed(a, b); r = e / max(1, len(a))
        tot_e += e; tot_n += len(a)
        res[d["id"]] = dict(ref=d["tts"], hyp=hyp, err=round(r, 3))
        if r > 0.12:
            bad.append(d["id"])
            print(f"!! {d['id']} {r:.2f}\n   稿: {d['tts']}\n   听: {hyp}", flush=True)
    json.dump(res, open(f"{WORK}/tts/asr.json", "w"), ensure_ascii=False, indent=1)
    print(f"total pinyin error {tot_e}/{tot_n} = {tot_e / max(1, tot_n):.3f}; flagged {len(bad)}: {' '.join(bad)}")


if __name__ == "__main__":
    main()
