"""ASR 回读：faster-whisper 逐句识别，按无调拼音和原稿比对，输出错误率，标出可疑句子。
usage: python asr_check.py [ids...] [--model small] [--wav path --text ...]"""
import os, sys, json, re
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
PROC = os.environ.get("PROC", "/tmp/claude-0/work/tts/proc")

def py(s):
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return [p.lower() for p in lazy_pinyin(s)]

def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return d[-1]

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("ASR_T", 2)))
    res = []; E = N = 0
    for d in all_lines():
        if args and not any(d["id"].startswith(a) for a in args):
            continue
        p = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p); x = resample_poly(x, 1, sr // 16000).astype(np.float32)
        segs, _ = model.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        e = ed(a, b); E += e; N += len(a)
        r = e / max(1, len(a))
        res.append(dict(id=d["id"], err=round(r, 3), ref=d["say"], hyp=hyp))
        print(f"{d['id']} {r:.2f} {'!!' if r > 0.12 else ''} {hyp}", flush=True)
    print(f"TOTAL pinyin error {E}/{N} = {E / max(1, N):.3f}")
    json.dump(res, open(os.environ.get("ASR_OUT", "/tmp/claude-0/work/asr.json"), "w"), ensure_ascii=False, indent=1)
