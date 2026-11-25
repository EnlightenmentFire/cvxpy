"""ASR read-back of every processed line (faster-whisper small, CPU int8), compared as toneless pinyin.
python asr_check.py [ids...] -> WORK/asr_lines.json; prints lines below threshold."""
import os, sys, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def py(s):
    s = re.sub(r"[^一-鿿]", "", s)
    return lazy_pinyin(s)


def main():
    ids = sys.argv[1:]
    m = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=4)
    out = {}
    p = f"{WORK}/asr_lines.json"
    if os.path.exists(p):
        out = json.load(open(p))
    for d in all_lines():
        if ids and not any(d["id"].startswith(i) for i in ids):
            continue
        if not os.path.exists(f"{WORK}/tts/proc/{d['id']}.wav"):
            continue
        x, sr = sf.read(f"{WORK}/tts/proc/{d['id']}.wav")
        x = resample_poly(x, 1, sr // 16000).astype(np.float32)
        segs, _ = m.transcribe(x, language="zh", beam_size=5,
                               initial_prompt="以下是普通话的句子，关于佛经故事目连救母。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        r = SequenceMatcher(None, a, b).ratio()
        out[d["id"]] = dict(ref=d["say"], hyp=hyp, ratio=round(r, 3))
        flag = "  <-- CHECK" if r < 0.85 else ""
        print(f"{d['id']} {r:.2f} {hyp}{flag}", flush=True)
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
