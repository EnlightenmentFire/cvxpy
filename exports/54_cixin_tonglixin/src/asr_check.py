# -*- coding: utf-8 -*-
"""ASR 回读：faster-whisper medium 逐句识别，按无调拼音比对脚本。
python asr_check.py [proc|raw] [ids...]   -> /tmp/claude-0/work/asr_report.json
"""
import sys, os, json, re
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WK = "/tmp/claude-0/work"


DIG = dict(zip("0123456789", "零一二三四五六七八九"))


def py(s):
    s = "".join(DIG.get(c, c) for c in s)
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return lazy_pinyin(s)


def ed(a, b):
    m, n = len(a), len(b)
    D = list(range(n + 1))
    for i in range(1, m + 1):
        prev, D[0] = D[0], i
        for j in range(1, n + 1):
            cur = D[j]
            D[j] = min(D[j] + 1, D[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return D[n]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "proc"
    ids = sys.argv[2:]
    m = WhisperModel("/tmp/claude-0/models/fw-medium", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 4)))
    rep = []
    tot_e = tot_n = 0
    for d in all_lines():
        if ids and d["id"] not in ids: continue
        p = f"{WK}/tts/{src}/{d['id']}.wav"
        if not os.path.exists(p): continue
        import soundfile as sf, numpy as np
        from scipy.signal import resample_poly
        x, sr = sf.read(p); x = x.mean(1) if x.ndim > 1 else x
        g = np.gcd(sr, 16000); x = resample_poly(x, 16000 // g, sr // g).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        e = ed(a, b)
        tot_e += e; tot_n += len(a)
        r = dict(id=d["id"], ref=d["say"], hyp=hyp, err=e, n=len(a), rate=round(e / max(1, len(a)), 3))
        rep.append(r)
        flag = "  <<<" if r["rate"] > 0.08 else ""
        print(f"{d['id']} {r['rate']:.2f} | {hyp}{flag}", flush=True)
    print(f"TOTAL pinyin error rate {tot_e}/{tot_n} = {tot_e / max(1, tot_n):.3%}")
    json.dump(rep, open(f"{WK}/asr_report_{src}.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
