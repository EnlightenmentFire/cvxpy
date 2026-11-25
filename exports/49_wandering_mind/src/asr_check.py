# -*- coding: utf-8 -*-
"""ASR read-back (faster-whisper) of processed TTS lines; compare by toneless pinyin.
usage: python asr_check.py [ids...]  -> WORK/asr_report.json
"""
import os, sys, json, re
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from tts_clone import tts_text

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
DIG = dict(zip("0123456789", "零一二三四五六七八九"))


def norm(s):
    s = s.replace("%", "").replace("％", "")
    s = "".join(DIG.get(c, c) for c in s)
    s = re.sub(r"[^一-鿿]", "", s)
    return lazy_pinyin(s)


def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[len(b)]


def main():
    ids = sys.argv[1:]
    m = WhisperModel("medium", device="cpu", compute_type="int8", download_root=f"{WORK}/models/whisper",
                     cpu_threads=int(os.environ.get("THREADS", 4)))
    rep_p = f"{WORK}/asr_report.json"
    rep = json.load(open(rep_p)) if os.path.exists(rep_p) else {}
    for d in all_lines():
        if ids and d["id"] not in ids:
            continue
        p = f"{WORK}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        import soundfile as sf
        from scipy.signal import resample_poly
        x, sr = sf.read(p, dtype="float32")
        x = resample_poly(x, 1, 3).astype("float32") if sr == 48000 else x
        segs, _ = m.transcribe(x, language="zh", beam_size=5, vad_filter=False,
                               initial_prompt="以下是普通话的句子，使用简体中文。")
        hyp = "".join(s.text for s in segs)
        ref = tts_text(d["say"])
        a, b = norm(ref), norm(hyp)
        e = ed(a, b) / max(1, len(a))
        rep[d["id"]] = dict(ref=d["say"], hyp=hyp, per=round(e, 3))
        print(f"{d['id']} per={e:.3f} | {hyp}", flush=True)
        json.dump(rep, open(rep_p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
