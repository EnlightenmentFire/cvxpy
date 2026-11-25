"""ASR read-back: faster-whisper on each processed line; compare toneless pinyin to the script (say text).
usage: python asr_check.py [ids...]  -> WORK/asr_lines.json (+ prints failures)"""
import sys, os, json, re
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import difflib
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{WORK}/tts/proc"


def py(s):
    s = re.sub(r"[^一-鿿0-9A-Za-z]", "", s)
    return lazy_pinyin(s)


def per(ref, hyp):
    sm = difflib.SequenceMatcher(None, ref, hyp)
    match = sum(b.size for b in sm.get_matching_blocks())
    return 1 - match / max(1, len(ref))


def main():
    pre = sys.argv[1:]
    out_p = f"{WORK}/asr_lines.json"
    res = json.load(open(out_p)) if os.path.exists(out_p) else {}
    m = WhisperModel("/tmp/claude-0/models/faster-whisper-small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("THREADS", 2)))
    for d in all_lines():
        if pre and not any(d["id"].startswith(p) for p in pre):
            continue
        f = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(f):
            continue
        x, sr = sf.read(f)
        x = resample_poly(x, 1, sr // 16000).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子，关于北宋王安石变法。")
        hyp = "".join(s.text for s in segs)
        e = per(py(d["say"]), py(hyp))
        res[d["id"]] = dict(ref=d["say"], hyp=hyp, per=round(e, 3))
        flag = "  <-- CHECK" if e > 0.12 else ""
        print(f"{d['id']} {e:.3f} {hyp}{flag}", flush=True)
    json.dump(res, open(out_p, "w"), ensure_ascii=False, indent=1)
    errs = [v["per"] for v in res.values()]
    print("lines", len(errs), "mean pinyin err %.3f" % (sum(errs) / max(1, len(errs))), "flagged", sum(e > 0.12 for e in errs))


if __name__ == "__main__":
    main()
